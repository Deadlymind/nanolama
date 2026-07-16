---
name: ai-integration
description: Wires Anthropic Claude into a Django/DRF backend — the agentic tool-use loop (model proposes tool_use, app runs it, returns tool_result, repeat), a write-tool safety contract for data-mutating tools, an OCR/structured-extraction pipeline validated against a schema before persist, Tavily search, and a small graded eval set. Use when adding a Claude agent or tool loop, doing document OCR extraction, calling the anthropic SDK, choosing a model id, or catching AI regressions. Not for the Celery worker that runs a long call (see celery-tasks) or auditing a tool's blast radius (see security-review).
---

# AI integration (Anthropic Claude, tool-use, OCR, evals)

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
confirmation before an unrecoverable action).

**OCR / structured extraction.** Send the document as a `document`/`image` content block,
ask for JSON, then validate against a schema (e.g. `InvoiceSchema.model_validate_json(...)`)
*before* persisting — an extraction is untrusted input. Persist only the validated,
tenant-scoped result.

**Tavily search.** Expose search as one more tool in the loop — `tavily.search(query)`
returns snippets you pass back as a `tool_result`. Keep the API key server-side; never let
the model see it.

**Evals.** Keep a small graded set — inputs with expected outputs — and run it in CI before
shipping any prompt or model change, so a regression fails the build instead of shipping.

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
- Model ids and pricing change — read them from config, verify against docs, never inline.

## See also
- `security-review`
- `celery-tasks`
- `verify`
