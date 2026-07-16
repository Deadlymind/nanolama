---
name: production-readiness
description: Orchestrates the go-live gates before a launch or major release on a Django/DRF plus Next.js stack — chains the owning skills into one pre-launch checklist covering health and readiness endpoints, env and secrets, reversible migrations, wired monitoring and alerts, a rehearsed rollback, a load and perf pass, tested backups, a security review, and explicit human sign-off. Use when preparing a launch, cutting a major release, running a go/no-go review, writing a release runbook, or asked "are we ready to ship this to prod". This skill decides readiness only; deploy, DNS cutover, and data migration stay behind explicit human approval. Not for the mechanics of one deploy (see deploy-aws) or proving a single change works (see verify).
---

# Production readiness (go-live gate orchestrator)

## When to use
Preparing a launch or a major release and you need a single, auditable go/no-go
pass over every gate — not a new gate, but the checklist that confirms each
owning skill's gate is actually green before anyone ships.

## Pattern
Readiness is a **conjunction of gates you do not duplicate**. Each item below
delegates to the skill that owns it; this skill only verifies the gate passed and
records who signed off. A single red gate is a no-go — readiness is all-or-nothing,
not a score you average. Crucially, **deciding ready is separate from shipping**:
this skill produces a go/no-go, and every side-effectful launch action (deploy, DNS
cutover, data migration, flag flip) waits for an explicit human "go".

## The checklist
Run top to bottom on the **target** environment. Each line names its owning skill.

1. **Health and readiness endpoints green** on the target env — liveness returns
   200 and readiness reports its dependencies (DB, cache, broker) reachable, not
   just "process up" (see `deploy-aws`).
2. **Env and secrets present and non-default.** Every required key is set for the
   target env, no placeholder or dev default leaked through, and **nothing secret
   is committed** — config comes from the environment (see `security-review`).
3. **Migrations reviewed as reversible.** Schema changes follow expand-contract so
   the old code keeps running against the new schema, and each has a tested
   backward step — no destructive drop shipped in the same release as the code that
   stops using the column (see `migrations`).
4. **Monitoring, dashboards, and alerts wired and firing.** Confirm alerts actually
   page (fire a synthetic one), dashboards read live data, and error and latency
   signals are visible — a dashboard nobody is paged from is not monitoring
   (see `observability`).
5. **Rollback plan rehearsed.** A written, *practiced* path back to the last good
   release — not "we'll redeploy the old tag if it breaks". Know the rollback time
   and whether it is safe once the new migration has run (see `deploy-aws`).
6. **Load and perf sanity pass.** A representative load run against the target env
   with no regression in the key latency and error budgets — catch the N+1 or the
   missing index before users do (see `perf-review`).
7. **Backups taken and a restore tested.** A fresh backup exists **and** you have
   restored it somewhere and confirmed the data is intact — an untested backup is a
   hope, not a recovery plan (see `aws-services`).
8. **Security review completed.** The launch diff passed a review of tenant
   isolation, RBAC, PII, uploads, and secrets, with findings resolved or explicitly
   accepted (see `security-review`).
9. **Explicit human sign-off and error-budget check.** A named owner records the
   go/no-go, confirms the service is within its error budget (not mid-incident), and
   authorizes each side-effectful launch step by hand.

## The checklist, copyable

```text
# Go-live checklist — <release / launch name>, target env: <staging|prod>
[ ] Health + readiness endpoints green on target env        -> deploy-aws
[ ] Env + secrets set, non-default, nothing committed       -> security-review
[ ] Migrations reversible / expand-contract, back step run  -> migrations
[ ] Dashboards live + at least one alert fired end-to-end   -> observability
[ ] Rollback plan written AND rehearsed; rollback time known-> deploy-aws
[ ] Load/perf pass on target env, budgets held              -> perf-review
[ ] Backup taken AND restore tested                         -> aws-services
[ ] Security review done, findings resolved/accepted        -> security-review
[ ] Human sign-off: <name> — error budget OK, GO / NO-GO
# NO side-effectful launch step (deploy, DNS, data migration) runs before GO.
```

## Adapt to your repo
Rename the environments (`staging`/`prod`) and the owning team to match your setup,
and point each line at your real endpoints — the health/readiness URLs, the alert
that must fire, the dashboard that must read live. Fix the exact latency and error
budgets your service commits to; this skill states the shape, not your numbers.
Do not pin tool versions (Sentry, OpenTelemetry, Playwright, k6, etc.) — confirm the
current version of any tool you reach for with `version-check`. Decide up front which
gates are hard blockers versus "accepted with an owner's note".

## Gotchas
- Absence is the failure mode: a gate that was never wired reads as "green" because
  nothing complains. Verify each gate *actively* — fire the alert, run the restore,
  exercise the rollback — don't tick it from memory (see `verify`).
- This skill decides readiness; it does not release. If you find yourself about to
  run the deploy or flip DNS, stop — that needs an explicit human "go" per the sign-off.
- "Backup exists" is not "restore works". Only a completed test restore counts.
- A staging pass is not a prod pass: run the health, load, and monitoring checks
  against the environment you are actually launching.
- Skipping a gate under deadline pressure is a decision an owner records and accepts
  by name — never a silent omission.

## See also
- `verify`
- `deploy-aws`
- `observability`
- `security-review`
- `migrations`
