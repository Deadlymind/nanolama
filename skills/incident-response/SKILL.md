---
name: incident-response
description: Runs the response when something is live-broken or a secret is exposed — report first, contain the blast radius, fix the root cause through a reviewed change, then a blameless post-mortem that hardens the lesson into a standing rule. Use when a production endpoint is down or misbehaving, a key/token/credential may have leaked, an account or session looks compromised, a bad deploy is degrading users, or someone asks how to handle an ongoing incident. Not for pre-ship risk auditing (see security-review) or root-causing a failure in isolation (see debug).
---

# Incident response (report, contain, fix, prevent)

## When to use
Something is broken in production right now, or a secret may have escaped — a
leaked key, an endpoint exhausting a shared resource, a bad deploy degrading
users. This is the live-fire path, distinct from reviewing code before it ships.

## Pattern
Four moves, in order, and the order matters:

1. **Report first.** Announce the incident before you touch anything. Quiet fixing
   hides the blast radius — visibility lets others help, stop dependent work, and
   catch what you can't see. A wrong-but-loud call beats a right-but-silent one.
2. **Contain.** Stop the bleeding before you understand it fully: revoke the
   key/session, disable or feature-flag the broken endpoint, take the risky feature
   offline. Reducing exposure is not the fix — it buys time to fix safely.
3. **Fix the root cause** through a normal reviewed change, not a panicked hotfix
   straight to production. The pressure to skip review is exactly when review
   catches the second bug you'd introduce.
4. **Prevent** with a short blameless post-mortem that turns the lesson into a
   durable standing rule, so the whole *class* of bug cannot recur.

## Adapt to your repo
Define these once so the sequence runs the same every time: where incidents are
announced, who can revoke a credential or flip a feature flag, how to roll back or
disable a deploy, and where post-mortems live. Wire "assume compromised → rotate"
into whatever secret store you use (env, secrets manager, KMS). Keep the loop fast
and low-ceremony — a heavy process just tempts people to skip step 1.

## Secrets are assumed compromised
Any credential that *may* have leaked is treated as leaked — rotate it immediately,
don't wait for proof it was used. A key printed to a log, pushed to a repo, or
pasted anywhere shared is burned. Rotate the value, invalidate old sessions/tokens
minted with it, and confirm the new one is live before you call it contained.
Redacting the leak after the fact does not un-leak it.

## Codify the fix as a rule
A post-mortem that ends at "we fixed it" invites the same bug in a new costume.
End it at a rule that makes the whole class impossible. Concretely: if an endpoint
polled on an interval overloaded a shared resource, the standing rule is *any
endpoint polled on an interval must be bounded (page size / row cap) and cached
(short server-side TTL)* — so no future polled endpoint can exhaust that resource.
Write the rule where it will be enforced (a lint check, a review checklist, a
skill), not in a doc no one reopens.

```text
# Incident timeline — the shape to reach for
T+0   REPORT    "Payments 500ing since 14:02, investigating" (before touching prod)
T+2   CONTAIN   revoke leaked key + rotate; feature-flag the failing endpoint off
T+15  FIX       reviewed PR for the root cause → deploy through the normal pipeline
T+1d  PREVENT   blameless post-mortem → new standing rule that kills the class
```

## Gotchas
- Fixing before reporting is the classic mistake — it shrinks the responder pool to
  just you and hides scope from everyone who could help.
- Containment is temporary relief, not resolution — a disabled feature still owes a
  real fix and a re-enable.
- "It probably wasn't exposed long enough to matter" is not a rotation decision —
  assume compromised and rotate anyway.
- A panicked direct-to-prod hotfix routinely ships a second incident; route the fix
  through review even under pressure (see `deploy-aws` for safe rollout/rollback).
- Blame in the post-mortem buys silence next time — keep it about the system, so the
  next person reports fast instead of hiding.

## See also
- `security-review`
- `debug`
- `deploy-aws`
