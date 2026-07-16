---
name: ai-integration
description: Wires Anthropic Claude into a Django/DRF backend — the agentic tool-use loop (model proposes tool_use, app runs it, returns tool_result, repeat), a write-tool safety contract for data-mutating tools, capability limits against prompt injection, an OCR/structured-extraction pipeline validated against a schema before persist, Tavily search, and per-tenant metering. Use when adding a Claude agent or tool loop, exposing a tool that mutates data, doing document OCR extraction, calling the anthropic SDK, choosing a model id, or capping AI spend per tenant. Not for regression-testing agent behaviour, golden sets or LLM-as-judge scoring (see ai-evals), the Celery worker that runs a long call (see celery-tasks), or auditing a tool's blast radius (see security-review).
---

# AI integration (Anthropic Claude, tool-use, OCR)

## When to use
Adding Claude to the backend — an agent that calls your tools, an OCR/extraction
pipeline, or a search-augmented answer. The hard part is not the API call; it is
making the model's *actions* safe, tenant-scoped, and regression-tested.

## Pattern
The **agentic loop**: you send messages + a `tools` list; the model replies with
`stop_reason == "tool_use"`; your app executes that tool, appends a `tool_result`
block, and calls again — until `stop_reason == "end_turn"`. The model never touches
your database directly; **your code** does. Extraction and search are the same loop
with narrow tools.

```python
# pip install anthropic — verify the current model id in Anthropic's docs; do not hard-code pricing.
import anthropic
from django.db import transaction

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
MODEL = "claude-sonnet-5"       # placeholder — confirm the live id per docs

def run_agent(messages, tools, tool_impls, user, max_turns=8):
    for _ in range(max_turns):                             # cap the loop — never while True
        resp = client.messages.create(model=MODEL, max_tokens=1024,
                                       tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return resp                                    # end_turn -> done
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            fn = tool_impls[block.name]                    # your Python callable
            out = fn(user=user, **block.input)             # server passes user/tenant
            results.append({"type": "tool_result",
                            "tool_use_id": block.id, "content": str(out)})
        messages.append({"role": "user", "content": results})
```

**Write-tool safety contract.** Any tool that mutates data must be, non-negotiably:
tenant-scoped server-side (the server sets `entreprise` from `user`; the model never
supplies a tenant id — drop it from the tool's input schema); atomic (wrap the mutation
in `transaction.atomic()`); audited (log actor, tool, inputs, result row id); non-destructive
by default (soft-delete/append, never expose a hard-delete tool); and bounded plus
confirm-gated for anything irreversible (cap amounts/counts, require an explicit human
confirmation before an unrecoverable action). For money/status mutations, `select_for_update()`
the row inside the transaction and re-validate the invariant (balance, current status) before
persisting — a retried or concurrent tool call must not double-apply (see `db-concurrency`).

**All model-read content is untrusted — plan for prompt injection.** Not just the user's chat:
the *contents* of any scanned/extracted document, search snippet, or fetched page the model
reads can carry injected instructions. The defense is capability limits, not persuasion — do
**not** rely on a "ignore injected instructions" line in the prompt. Contain it structurally:
scoped tools that only touch the actor's tenant, confirm-gated writes, and simply not exposing
destructive tools. If the model has no tool to do harm, an injected instruction cannot make it.

**OCR / structured extraction.** Send the document as a `document`/`image` content block,
ask for JSON, then validate against a schema (e.g. `InvoiceSchema.model_validate_json(...)`)
*before* persisting — an extraction is untrusted input. Persist only the validated,
tenant-scoped result.

**Tavily search.** Expose search as one more tool in the loop — `tavily.search(query)`
returns snippets you pass back as a `tool_result`. Keep the API key server-side; never let
the model see it.

**Per-tenant metering.** Treat an AI endpoint like a rate-limited API — track and cap usage
per tenant with a credit/quota counter, so one heavy or malicious user cannot run up an
unbounded bill. Decrement on each model call and reject when the tenant is over quota.

**Evals.** A prompt, a model id, and a tool schema are untyped inputs — changing one breaks
routing silently. Cover them with two layers: a deterministic **hard gate** that blocks CI, plus
an **advisory** LLM-as-judge set that never gates. See `ai-evals` for the full method.

## Adapt to your repo
Rename `entreprise`/`Entreprise` and the accessor (`user.entreprise` vs
`user.profile.entreprise`) to your tenant. Swap `InvoiceSchema` and the tool set for your
domain. Confirm the live model id and API shape against Anthropic's current docs — do not
trust the placeholder above. Put `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` in settings/env,
never in code.

## Gotchas
- A model-supplied `entreprise`/`tenant` id is never trusted — strip it from the tool
  schema and set it from `user`. A leak here is a cross-tenant breach.
- Extraction output is untrusted — validate against a schema and reject on failure before
  it ever hits the DB.
- Long or multi-step loops block the request thread — run them in a Celery task (see
  `celery-tasks`), not inline in the view.
- Cap the loop iterations; a misbehaving model can otherwise spin tool calls forever.
- An uncapped AI endpoint is a billing DoS — meter per tenant before it ships, not after.
- Model ids and pricing change — read them from config, verify against docs, never inline.

## See also
- `ai-evals`
- `security-review`
- `celery-tasks`
- `db-concurrency`
- `rbac-permissions`
- `verify`
