---
name: perf-review
description: Finds and fixes performance problems in a Django/DRF app — hunts N+1 and unbounded queries on hot paths, fixes them with select_related (FK) and prefetch_related (M2M/reverse), paginates every list endpoint, and caches expensive dashboard aggregates with a short TTL over a bounded query. Use when a list endpoint or dashboard is slow, when a page fires hundreds of queries, when reviewing for N+1 with django-debug-toolbar, nplusone, or QuerySet.explain(), or when someone says "this is slow" or "too many queries". Not for diagnosing a specific crash or wrong result (see debug), row-locking and race conditions (see db-concurrency), or generic ViewSet/serializer wiring (see drf-api).
---

# Perf review (find and fix slow queries)

## When to use
A list endpoint, dashboard, or serializer is slow, or a single request fires
dozens to hundreds of SQL queries. The dominant cost on this stack is almost
always the database: N+1 loops, unbounded result sets, and re-computed
aggregates. Measure first, fix the query, measure again.

## Pattern
Three rules, held on every read-heavy path:

1. **No N+1.** A loop that touches a related row per item must preload it —
   `select_related` for forward FK/one-to-one (SQL JOIN), `prefetch_related`
   for M2M and reverse FK (a second query, joined in Python).
2. **No unbounded query.** Every list is paginated and every internal fan-out
   is `LIMIT`-ed. A query whose size grows with the tenant's data is a latency
   time bomb.
3. **Cache computed aggregates, not raw rows.** Expensive dashboard rollups get
   a short TTL over an already tenant-bounded query — never cache an unbounded scan.

Measure before and after: count the queries a request makes with
`django.test.utils.CaptureQueriesContext(connection)`, or in dev use
`django-debug-toolbar`'s SQL panel or the `nplusone` middleware to name the
offending relation, and `QuerySet.explain()` to read the plan. Fix the N+1 in the
ViewSet's `get_queryset` so the whole list preloads. Bound every list globally
with DRF's `DEFAULT_PAGINATION_CLASS` (e.g. `LimitOffsetPagination` plus a
`PAGE_SIZE`) rather than per-view guesswork. Then cache expensive rollups over an
already tenant-bounded query:

```python
# views.py — fix the N+1 in one place, then cache the aggregate over a bounded query
from django.core.cache import cache
from django.db.models import Sum

class InvoiceViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return (
            super().get_queryset()                   # tenant filter stays (see multi-tenancy)
            .select_related("client", "entreprise")  # forward FK -> SQL JOIN
            .prefetch_related("line_items")          # reverse FK -> one extra query
        )

def revenue_summary(entreprise_id):
    key = f"revenue_summary:{entreprise_id}"         # namespace the key per tenant
    total = cache.get(key)
    if total is None:
        total = (Invoice.objects
                 .filter(entreprise_id=entreprise_id)  # bound first, then cache
                 .aggregate(t=Sum("amount"))["t"] or 0)
        cache.set(key, total, timeout=60)            # short TTL, staleness bounded
    return total
```

## Adapt to your repo
Rename `entreprise`, `Invoice`, and the relation names (`client`, `line_items`)
to your models. Confirm your cache backend is Redis (`django.core.cache` -> ElastiCache)
and namespace keys by tenant so one entreprise never reads another's rollup. Pick
the pagination class that fits your API (cursor for infinite scroll, limit/offset
for tables). Choose a TTL your users tolerate as stale — seconds for a live
dashboard, minutes for a report.

## Gotchas
- `select_related` on a reverse or M2M relation raises or silently does nothing —
  use `prefetch_related` there; mixing them up reintroduces the N+1.
- Calling `.count()` then slicing runs two queries; DRF pagination already does the
  right thing — don't hand-roll it.
- A `.filter()` or `.order_by()` applied *after* `prefetch_related` on the related
  manager can trigger a fresh query per row — use `Prefetch(..., queryset=...)` instead.
- Caching before bounding the query just caches an expensive scan; bound (tenant +
  `LIMIT`) first, then cache.
- Invalidate or accept staleness — a cached aggregate won't reflect a new write until
  the TTL expires; keep the TTL short or bust the key on write.
- A slow endpoint the frontend polls on an interval amplifies: each client re-fires
  the query every tick, and blind auto-retry on failure multiplies it further until
  the connection pool is exhausted and the whole app 5xxs. Fixing the query is
  necessary but not sufficient — also stop the retry storm (exponential back-off,
  disable blind auto-retry). Treat every polled endpoint as one that must be *both*
  bounded *and* cached.

## See also
- `drf-api`
- `db-concurrency`
- `debug`
