---
name: verify
description: Drives a change end to end and observes real behavior — exercising the actual flow through the API, UI, or logs, not just tests or typecheck — before it is called done. Use when about to claim a task is finished, working, or fixed, when the user asks to verify or confirm a change, or before opening a PR. Enforces a gate — no completion claim without a fresh proving-command run and its pasted output. Not for writing the tests themselves (see write-tests) or root-causing a failure (see debug).
---

# Verify (prove it actually works)

## When to use
Right before you say "done", "fixed", or "it works" — and before opening a PR.
A change is not verified because it compiles, typechecks, or has tests; it is
verified when you have watched the real behavior it was supposed to produce.

## Pattern
**The gate:** no completion claim without a fresh run of a proving command and its
actual output pasted in. Decide up front what observable behavior would prove the
change, produce that observation on the real system, then report it. If you cannot
run the proving command, say so plainly instead of implying success.

## Steps / idioms
1. **Name the proving behavior.** What should a user (or caller) now see that they
   couldn't before? Turn it into a concrete command or click-path.
2. **Run it fresh, end to end**, against a running system — not a dry run:
   - API: hit the endpoint with a real auth cookie and inspect the status + body.

     ```bash
     # cookie-JWT flow: prove the endpoint returns the tenant's data, not a 500
     curl -sS -b cookies.txt http://localhost:8000/api/invoices/ | head -c 400
     ```
   - UI: drive the actual page/flow and watch the result (see `run` if available).
   - Async/websocket: trigger it and tail the worker/consumer logs for the effect.
3. **Read the evidence, don't assume it.** A 200 with the wrong body is still a fail.
4. **Paste the observed output** into your report, then state the claim.
5. If a regression is possible, add a test that would have caught it (see `write-tests`).

## The claim → requires → not-sufficient table
| Claim | Requires | Not sufficient |
| --- | --- | --- |
| "Endpoint works" | fresh request + observed 2xx + correct body | typecheck / unit test passing |
| "Bug fixed" | reproduce the original failure, then show it gone | "the code looks right" |
| "Tenant-scoped" | user B gets 404/empty for user A's row | filter present in the diff |
| "Deploys" | health check green on the target env | build succeeded locally |

## Adapt to your repo
Define your proving commands: the dev-server start command, the login/cookie step,
the health-check URL, where worker and websocket logs live. Capture them once (a
project `verify` note or Makefile target) so every change is proven the same way.

## Gotchas
- Green CI/typecheck is necessary, not sufficient — it proves shape, not behavior.
- Mocked tests passing says nothing about the real integration; exercise the seam.
- "Should work" is a hypothesis, not a result — never report it as done.
- Verify on data that resembles production (multiple tenants, empty states, RTL text).

## See also
- `write-tests`
- `debug`
- `code-review`
- `security-review`

<!-- Discipline adapted from obra/superpowers "verification-before-completion" (MIT).
     See THIRD_PARTY_NOTICES.md. -->
