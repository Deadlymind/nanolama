---
name: react-query
description: Manages server state on the Next.js 16 frontend with TanStack Query v5 — structured array query keys, staleTime/gcTime tuning, useQuery/useMutation with onSuccess invalidateQueries by key prefix, and the server-state vs client-state boundary. Use when fetching or caching API data, wiring a query-key factory, invalidating after a POST/PATCH/DELETE, fixing stale UI after a mutation, or deciding what belongs in Query vs Zustand. Not for persisted UI/client state (see zustand-state) or typing the API payload shapes (see drf-zod-contract).
---

# React Query (server state with TanStack Query v5)

## When to use
Any component that reads or writes data owned by the Django/DRF backend. Server
state is asynchronous, shared, and can go stale under you — that is Query's job.
Do **not** copy fetched rows into Zustand or `useState`; mirror-storing server
data is the top source of stale-UI bugs on this stack.

## Pattern
Three rules:

1. **Query keys are structured arrays from a factory**, never ad-hoc strings.
   A key is `['invoices', 'list', filters]` — a stable, serializable description
   of *what* the data is. Prefix-matching then powers targeted invalidation.
2. **`staleTime` sets how long data is trusted; `gcTime` how long an unused
   cache lingers.** Pick per resource — not the defaults everywhere.
3. **After a mutation, invalidate by key prefix in `onSuccess`.** Don't manually
   patch the cache for the common case; let the refetch reconcile with the server.

Centralize keys in a factory, read with `useQuery`, write with `useMutation`,
then invalidate by prefix in `onSuccess`:

```ts
// features/invoices/keys.ts — rename "invoices" per resource
export const invoiceKeys = {
  all: ['invoices'] as const,
  lists: () => [...invoiceKeys.all, 'list'] as const,
  list: (filters: InvoiceFilters) => [...invoiceKeys.lists(), filters] as const,
  detail: (id: number) => [...invoiceKeys.all, 'detail', id] as const,
};

// Read (v5 single-object signature; no-data status is `isPending`)
const { data, isPending, isError } = useQuery({
  queryKey: invoiceKeys.list(filters),
  queryFn: () => fetchInvoices(filters),   // returns a Zod-parsed payload
  staleTime: 30_000,   // 30s: trust the list before refetching
  gcTime: 5 * 60_000,  // keep unused cache 5min for fast back-nav
});

// Write, then prefix-invalidate so every matching list/detail refetches
const qc = useQueryClient();
const { mutate } = useMutation({
  mutationFn: (body: InvoiceInput) => createInvoice(body),
  onSuccess: () => qc.invalidateQueries({ queryKey: invoiceKeys.all }),
});
// mutate(values) — call from the form's submit handler
```

## The server-state vs client-state boundary
| Belongs in React Query | Belongs in Zustand / local state |
| --- | --- |
| API rows, lists, details | Sidebar open, active tab, theme |
| Anything the server owns | Draft form input before submit |
| Derived-from-fetched values | Selected row id / UI filters* |

*Filters live in client state, then feed into the query key — the key is the
one place client and server state meet. Never duplicate the fetched rows.

## Adapt to your repo
Rename `invoices`/`invoiceKeys` and the accessor (`/api/invoices/`) per resource,
and keep one keys file per feature. Tune `staleTime` to how fast the data changes
(near-real-time dashboards → low or `0`; reference lists → minutes). Wrap the app
once in a `QueryClientProvider` in a client boundary under the App Router. Make
`queryFn` return the Zod-validated shape (see `drf-zod-contract`).

## Gotchas
- v5 renamed `isLoading`→`isPending` for the no-data state, `cacheTime`→`gcTime`,
  and takes a **single object** — positional `useQuery(key, fn)` no longer exists.
- `invalidateQueries` prefix-matches, so `{ queryKey: ['invoices'] }` catches
  every list and detail; scoping too narrowly leaves stale sibling views.
- `staleTime: 0` (the default) refetches on every mount/focus — deliberate, but
  chatty for stable data. Set it up rather than leaving it implicit.
- Reading `data` off a mirrored Zustand copy defeats invalidation — the refetch
  updates the cache, not your snapshot. Read straight from `useQuery`.
- Cookie-JWT auth means the browser sends the HttpOnly cookie automatically; the
  `queryFn` fetch just needs `credentials: 'include'`, no token juggling.

## See also
- `nextjs-module`
- `zustand-state`
- `drf-zod-contract`
