---
name: security-review
description: Audits a diff for this stack's top risks — tenant isolation on every business queryset (fail-closed, no client-supplied tenant id trusted), RBAC on every custom endpoint and @action, PII leakage in list endpoints/logs/exports, file-upload validation (content-type, size, extension, private storage), and secrets not committed. Use when reviewing a Django/DRF change before merge, auditing a new ViewSet or upload handler, checking a PR for security issues, or asked "is this safe to ship". Findings are confidence-gated. Run only on TRUSTED diffs — not hardened against prompt injection. Not for generic correctness/quality review (see code-review) or proving behavior works (see verify).
---

# Security review (audit changes for top risks)

## When to use
Reviewing a diff before merge on this stack, especially one that touches a
ViewSet, a custom `@action`, a serializer, an upload handler, an export, or
logging. Focus on the handful of risks that actually bite this architecture,
not a generic OWASP recital.

> **CAUTION — trusted diffs only.** This skill reads code and follows its intent.
> It is *not* hardened against prompt injection. Do not run it on untrusted or
> attacker-controlled diffs; a hostile comment or string could steer the review.

## Pattern
Walk the diff against a fixed checklist, and gate every finding by confidence:
report **Confirmed** (you can point at the vulnerable line and the exploit),
**Likely** (pattern is present but the sink is one hop away), or **Question**
(needs the author to confirm). Never pad the report with speculative low-signal
noise — a fail-closed tenant leak outranks a style nit by orders of magnitude.

## The checklist
1. **Tenant isolation.** Every business queryset scoped by the tenant FK
   (`entreprise`) and **fail-closed** — no tenant resolves to `.none()`, never all
   rows. The tenant comes from `request.user`, never from a body/query param. Flag
   any raw `Model.objects.get/filter(...)` in a view that bypasses the scoped
   queryset, and any `@action` that re-queries without scoping (see `multi-tenancy`).
2. **RBAC.** Every custom endpoint and every `@action` carries an explicit
   permission — no endpoint relies on "logged in" alone. A new action without a
   `{resource}_{action}` gate is a finding (see `rbac-permissions`).
3. **PII leakage.** List/export serializers must not spill emails, phones, tokens,
   or internal ids beyond what the screen needs; logs and error payloads must not
   echo request bodies or secrets.
4. **File uploads.** Validate content-type **and** extension **and** size; store to
   **private** storage (never a public-read S3 ACL); never trust the client filename.
5. **Secrets.** No keys, tokens, or `.env` values in the diff — config comes from
   the environment. Watch AI/search keys especially (see `ai-integration`).
6. **Money & counters.** Flag any balance/counter that reads a value into app code
   and writes it back. A read-modify-write without `select_for_update()` inside
   `transaction.atomic()` is a race. **Confirmed** example: two concurrent requests
   both read `100`, both subtract, one write is lost. Require an atomic `F()`-style
   expression, a decimal type for money, and validation **inside** the locked block —
   an "insufficient funds" check outside the lock still oversells (see `money-decimal`,
   `db-concurrency`).
7. **Object-level authz / BOLA.** Validate **every** foreign-key id in the body or
   params against the caller's tenant, not just the object being fetched. An
   unvalidated FK lets a user reference or attach another tenant's row even when the
   top-level queryset looks correctly scoped — e.g. posting a `category_id` that
   belongs to a different tenant. Re-scope each FK through the caller's queryset.
8. **Auth & tokens.** Tokens live in `HttpOnly`/`Secure`/`SameSite` cookies, never
   `localStorage`. Never log a token, cookie, or `Authorization` header. No
   hand-rolled auth/session flow — lean on the framework. External credentials
   (third-party API keys, OAuth secrets) encrypted at rest, not stored plaintext.

## Idioms — what a real finding looks like
```python
# CONFIRMED — cross-tenant leak plus an unsafe upload, both attacker-reachable.
@action(detail=False, methods=["post"])
def bulk_send(self, request):
    ids = request.data["invoice_ids"]
    qs = Invoice.objects.filter(id__in=ids)                 # BUG: not tenant-scoped
    # fix: qs = self.get_queryset().filter(id__in=ids)      # reuse fail-closed scope

    f = request.FILES["doc"]
    if f.content_type == "application/pdf":                 # BUG: spoofable header only
        default_storage.save(f.name, f)                     # public bucket + raw name
    # fix: check f.size, whitelist the extension, sniff magic bytes, private storage
    ...
```

## OWASP quick-map
The generic OWASP list only earns its keep when pinned to a real sink. Three that
bite this stack, confidence-gated like everything else:
- **SSRF (server-side request forgery).** Any *server-side* URL fetch in the AI /
  OCR / RAG or webhook paths must validate the target against an **egress
  allowlist** — never fetch a user- or model-supplied URL blindly. A model that
  returns a link, or a webhook payload carrying a callback URL, is attacker
  reachable; a blind `requests.get(url)` there can hit `169.254.169.254` or an
  internal service. **Confirmed** when the fetched URL flows from request/model
  data with no host check (see `webhook-handler`, `ai-integration`).
- **Injection escape hatches.** The ORM parameterizes for you, so a plain
  `.filter(...)` is safe — flag the code that *leaves* it: `.raw()`, `.extra()`,
  `RawSQL(...)`, `cursor.execute(f"... {x}")`, or any string-built query. An id or
  name interpolated into that string is SQL injection even though the surrounding
  code "uses the ORM."
- **Security headers.** Confirm Django `SECURE_*` settings — HSTS
  (`SECURE_HSTS_SECONDS`), `SECURE_SSL_REDIRECT`, and `Secure`/`HttpOnly`/`SameSite`
  session and CSRF cookies — plus a **Content-Security-Policy** on the frontend.
  Missing HSTS or a permissive CSP is **Likely**, not Confirmed, unless you can show
  the header is actually absent in a response.

## Adapt to your repo
Rename `entreprise`/`Entreprise` and the tenant accessor (`user.entreprise_id` vs
`user.profile.entreprise_id`) to match your project. Confirm where "logged in" is
enforced globally so you can spot endpoints that *only* have that and nothing more.
Know your storage default (public vs private bucket) before judging upload code.

## Gotchas
- Absence is the bug: a missing tenant filter or missing permission won't appear as
  a red line — you must notice what *isn't* there. Diff-only review misses it; open
  the whole changed view.
- A 200 that returns another tenant's row is worse than a 500 — verify the fix
  actually fails closed, don't just eyeball the filter (see `verify`).
- Client-supplied `entreprise`/`tenant` ids, filenames, and content-types are all
  attacker-controlled — never trusted, even when "the frontend sets it".
- Rank by blast radius, not count. One confirmed cross-tenant leak beats ten nits.

## See also
- `multi-tenancy`
- `rbac-permissions`
- `ai-integration`
- `webhook-handler`
- `money-decimal`
- `db-concurrency`
