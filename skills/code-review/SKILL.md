---
name: code-review
description: Reviews the current git diff across four lenses (correctness, simplification, reuse, efficiency) and emits findings ranked by severity with file—line and a concrete failure scenario, plus nanolama-specific gates a generic reviewer misses (missing entreprise tenant filter, fail-closed regression, resource_action RBAC gap on a custom @action, DRF N+1, TanStack Query cache-key/invalidation bugs). Use when reviewing a diff or PR, doing a self-review before pushing, or asked to "review my changes" or "look over this diff". Not for exploit-focused auth/injection review (see security-review), query-plan/load profiling (see perf-review), or proving the change runs (see verify).
---

# Code review (4-lens, severity-ranked, stack-aware)

## When to use
Reviewing the working diff or a PR — self-review before you push, or a teammate's
change. Goal is a short, ranked list of real findings, most severe first, each with
`file:line` and a concrete failure scenario — not a wall of style nits.

## Pattern
Read only what changed (`git diff` / the PR range), then pass it through four lenses
in this order, because a correctness bug outranks any cleanup:

1. **Correctness** — does it do the wrong thing? Off-by-one, null/empty case, wrong
   branch, broken invariant, race, unhandled error.
2. **Simplification** — same behavior, less code? Dead branches, redundant state.
3. **Reuse** — does a helper/mixin/hook already exist for this?
4. **Efficiency** — N+1, needless re-render, work in a loop that belongs outside it.

Every finding needs a **severity** (blocker / major / minor), a **`file:line`**, and a
**failure scenario** ("when user B opens A's invoice, they see A's rows"). No scenario,
no finding.

## nanolama gates a generic reviewer misses
Check these explicitly on every relevant diff — they are the house invariants:

- **Missing `entreprise` tenant filter / fail-closed regression.** A new ViewSet,
  `get_queryset`, or raw `Model.objects.get(pk=...)` that isn't scoped by the current
  tenant, or an empty/anonymous path that returns all rows instead of `.none()`. Blocker.
- **`{resource}_{action}` RBAC gap on a custom `@action`.** The default CRUD verbs are
  gated but a hand-written `@action` (export, approve, bulk) ships with no permission
  class — a role that shouldn't reach it now can.
- **DRF N+1.** A serializer traverses a FK/reverse relation with no `select_related` /
  `prefetch_related` on the queryset — one query per row under a tenant's real volume.
- **TanStack Query cache correctness.** A mutation that doesn't invalidate the exact
  query key it changed (stale list after create), or a key missing a variable it
  depends on (two filters share one cache entry).

## Steps / idioms
```python
# BLOCKER — correctness + tenancy, invoices/views.py:42
# Custom @action bypasses the fail-closed queryset AND has no RBAC gate.
class InvoiceViewSet(TenantScopedViewSet):
    @action(detail=False, methods=["get"])            # no permission_classes here
    def export(self, request):
        rows = Invoice.objects.all()                  # BUG: unscoped -> cross-tenant leak
        return Response(serialize(rows))
# Failure: user in entreprise B calls /invoices/export/ and downloads A's invoices.
# Fix: rows = self.get_queryset(); gate with the invoice_export permission.
```

Report each finding as one ranked bullet: `**[BLOCKER]** file:line — what's wrong;
failure scenario; one-line fix.` Order the whole list by severity, blockers first.

## Adapt to your repo
Rename `entreprise` and the `{resource}_{action}` permission convention to yours.
Confirm what "the diff" is (`git diff main...HEAD`, staged, or a PR range) and which
lint/type checks already run in CI so you don't re-report what a linter catches.
Deep exploit hunting and query-plan profiling are out of scope here — hand those to
the sibling skills below.

## Gotchas
- Rank by severity, not by reading order — a blocker on line 300 comes before a nit
  on line 5.
- Don't report what the linter/type checker already flags; spend the review on logic.
- A missing tenant filter is a blocker even when "tests pass" — tests rarely have two
  tenants (see `verify`).
- Review the diff's blast radius, not just the changed lines: a renamed field can
  break a caller outside the diff.
- Skip praise and speculation — every finding must be actionable with a `file:line`.

## See also
- `security-review`
- `perf-review`
- `verify`
