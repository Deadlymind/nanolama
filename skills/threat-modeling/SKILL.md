---
name: threat-modeling
description: Runs design-time STRIDE threat modelling on a feature before the code exists — names the trust boundaries this stack actually has (the tenant boundary, RBAC roles inside a tenant, the auth cookie and CSRF edge, file-upload ingestion, inbound webhooks and third-party payloads, and the AI tool surface where a model-supplied argument is attacker-influenced input), walks spoofing, tampering, repudiation, information disclosure, denial of service and elevation of privilege against only the boundaries the feature crosses, then emits a short threat-to-mitigation-to-owning-skill table of work items. Use when designing a new endpoint or background job, introducing a new trust boundary or a new class of data, planning anything that touches money, PII or auth, writing an RFC or ADR, or asked "what could go wrong with this design". Not for auditing an existing diff (see security-review) or reacting after a breach or outage (see incident-response).
---

# Threat modeling (STRIDE per feature, at design time)

## When to use
Before the code exists. Four triggers earn a model on this stack:

- **A new endpoint** or a new background job/consumer that reaches business data.
- **A new trust boundary** — a first webhook, a first outbound fetch, a first AI tool.
- **A new class of data** — PII, credentials, documents, anything you would have to
  disclose if it leaked.
- **Anything touching money or auth** — balances, invoices, sessions, tokens, roles.

A CRUD field on a model you already scope correctly does not need one. Modelling
everything is how teams learn to skip modelling anything.

## Pattern
Enumerate the trust boundaries the feature **actually crosses**, walk STRIDE across
each one, and stop at a table of work items — not a document. Threat modelling is
proactive and design-time: it changes the design while changing it is still free.
`security-review` is the retrospective twin that audits the diff once written; the
model you build here is what that review is checked against.

Two rules keep it honest:

1. **Skip boundaries the feature does not cross.** A read-only internal report that
   never accepts an upload gets no upload row. Padding is what makes these ignored.
2. **Every threat ends in an owner or it is not a threat.** A row with no mitigation
   and no skill that implements it is a decision you have not made yet.

## Trust boundaries on this stack
Data crossing these lines changes from attacker-controlled to trusted. Name the ones
your feature crosses, then only STRIDE those.

| Boundary | What crosses it | Attacker's position |
| --- | --- | --- |
| **Tenant** | Every business row, every FK id in a body | A legitimate user of *another* tenant |
| **RBAC inside a tenant** | Endpoints, `@action`s, field visibility | A legitimate low-privilege colleague |
| **Auth cookie / CSRF edge** | Session cookie, CSRF token, login and refresh | Any origin the browser will talk to |
| **File-upload ingestion** | Filename, content-type, bytes, size | Anyone who can reach the upload |
| **Webhook / third-party payload** | Provider POSTs, callback URLs, ids | Anyone who can guess the URL |
| **AI tool surface** | Model-supplied tool arguments, retrieved text | Anyone whose text reaches the prompt |

The last one is the one teams miss. A model-supplied argument is **attacker-influenced
input**, not internal input — a document, an email body, or a webhook payload that
lands in the context window can steer the tool call that follows. Treat every tool
argument exactly like a request body: validate it, and re-scope every id through the
caller's tenant server-side. The model never carries authority.

## STRIDE, boundary by boundary
For each boundary the feature crosses, ask the six questions. Concretely, here:

- **Spoofing** — can a caller claim an identity? A tenant id read from the body or an
  `X-Tenant` header, an unsigned webhook, a login that leaks which emails exist.
- **Tampering** — can input change what it should not? A client-set `entreprise` on
  create, an FK pointing at another tenant's row, a webhook amount trusted as sent.
- **Repudiation** — could you reconstruct who did this? Money moves, role changes and
  exports need an audit record written in the same transaction as the effect.
- **Information disclosure** — what does the response, the log, the error, the export
  and the WebSocket group say that this role should not see?
- **Denial of service** — unbounded uploads, unpaginated lists, an unthrottled login,
  a webhook retry storm, an AI call with no timeout or spend ceiling.
- **Elevation of privilege** — can a user become an admin, or a tenant become another?
  A missing permission on a new `@action` is the classic path.

Fastest way to find the crossings is to sketch the feature and annotate it:

```python
# DESIGN SKETCH — annotate crossings before writing the real thing.
# Feature: "ask the assistant to email a client their invoice".
@tool  # BOUNDARY: AI tool surface — args are attacker-influenced, not internal.
def send_invoice(invoice_id: int, *, user) -> str:
    # S: identity is `user` from the session — never an id the model passes in.
    # T/E: re-scope the model-supplied id through the caller's tenant queryset.
    #      Unscoped `Invoice.objects.get(pk=invoice_id)` = cross-tenant read (-> multi-tenancy).
    invoice = scoped_invoices(user).get(pk=invoice_id)   # 404, not 403, on a foreign row

    # E: sending is a privileged verb — gate it explicitly (-> rbac-permissions).
    require_perm(user, "invoice_send")

    # I: the recipient comes from the invoice, never from the model (-> ai-integration).
    #    A prompt-injected "send to attacker@x" must have nowhere to land.
    # D: outbound send is queued with a retry cap, not called inline (-> celery-tasks).
    # R: who asked, which invoice, which recipient (-> audit-logging).
    audit(user, "invoice.sent", invoice_id=invoice.pk)
    enqueue_send(invoice.pk)
    return "queued"
```

## The output — a table, not a document
Stop here. One row per threat you are actually mitigating, and the skill that owns
the work, so the model produces tickets a reviewer can check off:

| Threat | Mitigation | Owner |
| --- | --- | --- |
| Model passes another tenant's `invoice_id` | Re-scope every id through the caller's queryset, fail closed | `multi-tenancy` |
| Any member can trigger a send | Explicit `invoice_send` permission on the tool and the endpoint | `rbac-permissions` |
| Injected text redirects the recipient | Recipient derived server-side from the row; model never supplies it | `ai-integration` |
| No record of who sent what | Audit row written in the same transaction as the effect | `audit-logging` |
| Retry storm / unbounded spend | Queue with a retry cap and a timeout | `celery-tasks` |

Then feed it forward: the table is the checklist `security-review` audits the diff
against at merge, and the open rows are release blockers for `production-readiness`
at launch. A row that survives to launch unmitigated is an accepted risk — record it
in an ADR (`architecture-decisions`) with a name against it, don't let it evaporate.

## Adapt to your repo
Rename `entreprise`/`Entreprise` and the tenant accessor to match your project, and
drop boundary rows your stack does not have — no AI surface means no AI row, and a
single-tenant app collapses the first two rows into one. Confirm what is already
enforced globally (authentication, throttling, CSRF) before modelling it as a threat;
a boundary the framework already holds is a line in the model, not a work item.

## Gotchas
- **The output is work items, not prose.** A modelling doc nobody reads has negative
  value — it buys the feeling of having done security without the mitigations.
- **Model the feature, not the whole system.** Re-modelling the login flow for the
  hundredth time is how these sessions get skipped.
- **"The frontend validates it" is not a mitigation** at any of these boundaries, and
  neither is "the model wouldn't do that" at the AI one.
- **Don't stop at the request.** Celery tasks, WebSocket consumers and webhook
  handlers cross the same tenant boundary with none of the ViewSet's scaffolding.
- **Threats without owners rot.** If no skill and no person owns a row, it is not
  mitigated — it is remembered, briefly.
- **A model is a snapshot.** Revisit it when the feature grows a new boundary, e.g.
  the day the report grows an export or the tool grows a write.

## See also
- `security-review`
- `multi-tenancy`
- `ai-integration`
- `production-readiness`
