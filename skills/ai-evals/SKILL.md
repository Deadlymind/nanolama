---
name: ai-evals
description: Regression-tests agent and LLM behaviour with two layers that are never confused — a deterministic hard gate that runs on every CI build (assert which tool the agent routes to, must-NOT-call cases for destructive paths, tenant and RBAC enforcement through the tool layer, golden exact-value extractions) and an advisory LLM-as-judge graded set that tracks quality trend but never blocks a merge. Use when changing a prompt, model id, or tool schema, adding a golden set, wiring evals into CI, catching a silent agent regression, deciding whether an eval may gate a merge, or asking how to test that the model picks the right tool. Not for the agent loop or the write-tool safety contract itself (see ai-integration) or ordinary application tests (see write-tests).
---

# AI evals (stop silent agent regressions)

## When to use
Any change to a prompt, a model id, or a tool schema. All three are untyped,
un-compiled inputs — nothing fails loudly when they break. A reworded system
prompt can quietly stop the agent from routing to `refund_tool`, and every test
still passes. Evals are how that change fails at merge time instead of in prod.

## Pattern
**Two layers, and never confuse them.**

1. **Hard gate — deterministic, blocking.** Repeatable assertions with a fixed
   expected value. Runs on every CI build, blocks the merge on red. Most of it
   makes **no model call at all**.
2. **Graded set — LLM-as-judge, advisory.** A judge model scores answer quality
   on a rubric. Stochastic: same input, different score run to run. It reports a
   **trend**, it does not gate.

The rule, stated outright: **never enforce safety with a check that can flake.**
A gate that goes red at random gets rerun until green, then ignored, then
deleted — and it takes the real signal with it. If a property matters enough to
block a merge, assert it deterministically.

## What belongs in the hard gate
- **Routing / tool selection.** Given a user turn, assert *which* tool the agent
  picks and with what arguments. Stub the model client and assert your dispatch
  layer — no API call, no key, no flake, milliseconds per case.
- **Must-NOT-call cases.** The mirror image, and the one people forget: for a
  destructive or out-of-scope request the model must **refuse the path**. Assert
  the tool was never invoked. This is the case a friendly prompt tweak breaks.
- **Tenant and RBAC through the tool layer.** Run the tool with tenant B's actor
  against tenant A's row and assert it returns nothing — the model layer must not
  become a way around the scoping the ViewSets enforce (see `multi-tenancy`).
- **Golden exact values.** Extraction and calculation have one right answer. Pin a
  hand-verified fixture and assert `==` — the invoice total is `"1250.00"`, never
  "roughly right".

```python
# tests/evals/test_routing.py — hard gate: deterministic, no live model call.
GOLDEN = json.loads((Path(__file__).parent / "golden/routing.json").read_text())

@pytest.mark.parametrize("case", GOLDEN)          # golden set lives beside the prompts
def test_routes_to_expected_tool(case):
    client = StubClient(script=case["model_reply"])   # replay a recorded tool_use block
    calls = []
    tools = {name: recorder(name, calls) for name in TOOL_IMPLS}

    run_agent(case["messages"], TOOL_SCHEMAS, tools, user=case_user(case), client=client)

    called = [c.name for c in calls]
    if case["expect_tool"] is None:
        assert called == [], f"must NOT call a tool: {case['prompt']}"   # refusal case
    else:
        assert called == [case["expect_tool"]]                           # routing case
        assert calls[0].args == case["expect_args"]                      # golden args

def test_tool_layer_is_tenant_scoped(tenant_a_invoice, user_b):
    # the model layer is not a bypass around ViewSet scoping
    assert TOOL_IMPLS["get_invoice"](user=user_b, id=tenant_a_invoice.pk) is None
```

## Running the graded set
Keep it as a separate, non-blocking CI job (or a nightly run) — it needs an API
key and costs money per run. Score each answer on a small rubric (grounded in the
retrieved context, answers the question, correct refusal), record the score, and
**watch the trend across runs**, not any single number. A drop is a prompt to go
look, not an automatic red build. Report it; never let it fail the pipeline.

## When to run them
Whenever the **prompt text, the model id, or a tool schema** changes — those are
the three inputs the type system cannot see. Wire the hard gate into the same CI
job as the unit suite so it cannot be skipped (see `ci-cd`), and re-run the graded
set before a model upgrade ships, comparing old id against new on the same set.

## Adapt to your repo
Keep the golden set **in the repo, next to the prompts it tests** — `prompts/` and
`tests/evals/golden/` move together in one commit, so a reviewer sees the prompt
diff and the expected-behaviour diff side by side. **Version the prompt** (a file
per version, or a `PROMPT_VERSION` constant recorded in each eval run) so a score
change maps to a known revision. Rename `entreprise`, the tool names, and the
actor accessor to match your project; swap `StubClient` for whatever your SDK
makes stubbable — a recorded reply object is enough, do not invent a fake API.

## Gotchas
- A live model call in the blocking gate makes the gate stochastic — and one red
  build from randomness teaches the team to rerun CI until green.
- Judge scores are not comparable across judge-model versions. Pin the judge id
  and note it with the scores, or the trend line is meaningless.
- The must-NOT-call cases are the ones that rot: nobody notices when a refusal
  quietly becomes a call. Add one for every destructive tool you expose.
- An eval set that only holds happy-path prompts passes forever. Include the
  ambiguous, the out-of-scope, and the adversarial/injected turn.
- Never fix a red gate by loosening the assertion to `in` or a fuzzy match — that
  is deleting the test with extra steps.
- Golden fixtures must be **hand-verified**, never captured from the model's own
  output — recording a wrong answer as golden freezes the bug in place.
- Evals prove the model's behaviour, not the tool's blast radius. A correctly
  routed call to an unsafe tool still ships a breach (see `ai-integration`).

## See also
- `ai-integration`
- `write-tests`
- `ci-cd`
- `verify`
