---
name: debug
description: A root-cause debugging method for the Django/DRF + Celery + Channels + Next.js stack — reproduce, isolate, hypothesize, fix the cause not the symptom, verify, add a regression test. Use when tracking down a bug, a 500, a flaky test, missing data, a stale UI, or an N+1 query, when asked to "debug", "why is this broken", "figure out why", or "find the root cause", and when deciding where to read logs (Django, Celery, Daphne, browser console/network). Not for proving a finished change works end to end (see verify) or optimizing already-correct code (see perf-review).
---

# Debug (find the root cause, not the symptom)

## When to use
Something is wrong — a 500, a wrong number, a UI that won't update, a query storm,
a test that fails one run in ten — and you need to find *why*, not paper over it.
The goal is a fix at the cause, backed by a test that would have caught it.

## Pattern
Five steps, in order — skipping one is how band-aids happen:

1. **Reproduce.** A reliable repro (command, click-path, failing test) before any fix.
   Can't reproduce it → you can't confirm you fixed it.
2. **Isolate.** Bisect the surface — narrow which layer, request, or line owns the
   failure. Read the logs at that layer (below), don't guess.
3. **Hypothesize.** State a specific, falsifiable cause ("stale cache because the
   mutation never invalidates the list key"), then test *that*.
4. **Fix the root cause.** Change the thing that is actually wrong, not the symptom.
   A `try/except` that swallows the error, a hard-coded retry, a `refetchInterval`
   masking a missing invalidation — those are band-aids. Resist them.
5. **Verify + regression test.** Reproduce the original failure, show it gone (see
   `verify`), and add a test that fails on the old code (see `write-tests`).

## Where the logs live
| Layer | Where to look |
| --- | --- |
| Django request/500 | dev server stdout; set `DEBUG=True` locally for the traceback |
| Celery task | worker stdout (`celery -A myproject worker -l info`), not the web log |
| Channels/websocket | Daphne stdout (`daphne myproject.asgi:application`) — the dev ASGI server |
| Frontend | browser **Console** (errors) + **Network** tab (status, payload, timing) |

## Playbook: N+1 query (symptom = slow list, log full of near-identical SELECTs)
Spot it: one query per row instead of one for the set. Fix at the queryset, not by caching.

```python
# BEFORE — 1 query for invoices + 1 per invoice for .client + N for .lines  (N+1)
qs = Invoice.objects.filter(entreprise=request.user.entreprise)
# AFTER — FK followed in the join; reverse/M2M batched into one extra query
qs = (Invoice.objects
      .filter(entreprise=request.user.entreprise)
      .select_related("client")        # forward FK / OneToOne → SQL JOIN
      .prefetch_related("lines"))       # reverse FK / M2M → one batched IN query
# Confirm the count dropped: assertNumQueries, or django-debug-toolbar.
```

## Playbook: React Query stale data (symptom = UI shows old value until refresh)
Root cause is usually a mutation that changes the server but never invalidates the
cache — not a caching bug to mask with `refetchInterval`. In the mutation's
`onSuccess`, call `queryClient.invalidateQueries` for the exact keys the mutation
touches (the list key *and* the affected detail key), so both refetch. See
`react-query` for the key-factory pattern.

## Adapt to your repo
Rename `Entreprise`/`entreprise`, `myproject.asgi`, and the query keys/routes to
match your project. Confirm your actual log locations and the command that starts
each process (worker, Daphne/ASGI). Match query keys to your app's real key factory.

## Gotchas
- Fixing the symptom (swallow the exception, add a retry, poll on an interval) leaves
  the cause live — it resurfaces elsewhere. Name the cause before you touch code.
- No repro = no fix. If it's intermittent, find the ordering/timing/data that triggers it.
- `select_related` is for forward FK/OneToOne (a JOIN); `prefetch_related` is for
  reverse FK/M2M (a second batched query). Swapping them silently does nothing.
- A 500 with `DEBUG=False` hides the traceback — read the server log, don't guess.
- Close the loop: a fix without a failing-then-passing regression test isn't done.

## See also
- `verify`
- `perf-review`
- `react-query`
