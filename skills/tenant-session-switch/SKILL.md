---
name: tenant-session-switch
description: Switches the active tenant (entreprise) in a multi-tenant Next.js SPA without leaking the previous tenant's cached data — the ordered switch sequence (set the store, cancelQueries, remove the old tenant's cache entries, resubscribe websockets, let observers refetch), the tenant-in-the-query-key invariant, and tenant-aware persistence that stores only the tenant id. Use when building or reviewing an entreprise/workspace switcher, debugging one tenant's rows showing under another after a switch, deciding what to purge on switch, fixing a socket still delivering the old tenant's events, or auditing what a store persists across tenants. Not for the server-side tenant isolation that is the actual boundary (see multi-tenancy) or generic query-key factories and cache tuning (see react-query).
---

# Tenant session switch (change tenant without leaking the old one)

## When to use
The frontend lets a user act inside more than one `entreprise` — an agency over
client sub-accounts, a consultant with several memberships, an internal operator —
and a switcher changes which tenant every subsequent request belongs to. Also use
when a tenant switch leaves stale rows, counts, or realtime events on screen.

> **Defence in depth, not the boundary.** The server still enforces isolation on
> every queryset (see `multi-tenancy`); nothing here replaces it. But a client
> cache leak is a **real, user-visible breach** the backend never sees — it serves
> tenant A's rows from memory to a session now claiming tenant B, with no request
> to audit and no log line. Treat it as a security bug, not a refresh glitch.

## Pattern
**The tenant belongs IN the query key, not only in the request header.** A key of
`['invoices', 'list', filters]` describes the same cache entry for every tenant,
so the header decides what gets *written* into it and the key decides what gets
*read* out — and after a switch those disagree. Scope every key under
`['tenant', tenantId, ...]` and two tenants can never collide in one entry.

Given that, the switch itself is **an ordered sequence, and the order is the whole
safety property**.

## The ordered sequence
1. **Set the new tenant in the store.** The store is the single source of truth the
   API client reads to stamp the tenant header, and the value every query key is
   built from (see `zustand-state`). It goes first so everything after it — new
   keys, new requests, new socket groups — is already on the new tenant.
2. **`cancelQueries()`.** In-flight requests were issued *before* the switch, so
   they already carry the **old** tenant's header. Left alone they resolve after
   the switch and write old-tenant rows into the cache under whatever key their
   observer holds. Cancel before touching the cache, and `await` it.
3. **Remove the old tenant's entries — do not merely invalidate.**
   `invalidateQueries` marks data stale but **keeps it**, and a stale entry is still
   served instantly to a mounted observer while the refetch is in flight. That
   render is the leak. `removeQueries` deletes the entries outright.
4. **Resubscribe websockets to the new tenant's groups.** Sockets joined
   `entreprise_<old>_...` groups at connect time and keep pushing that tenant's
   events — and pushed events get written straight into the cache. Leave the old
   group, join the new one (see `websockets-channels`).
5. **Let active observers refetch.** Do not orchestrate this. Mounted `useQuery`
   observers now subscribe to new keys with no data, so Query refetches them for
   you against the new tenant.

```ts
// features/tenant/switch.ts — order matters at every line
export async function switchTenant(qc: QueryClient, nextId: string) {
  const prevId = useUI.getState().activeEntrepriseId;
  if (prevId === nextId) return;

  // 1. Store first: the header's source of truth AND the root of every query key.
  useUI.getState().setEntreprise(nextId);

  // 2. In-flight requests still carry the OLD tenant header — kill them before
  //    they can resolve into the new tenant's view.
  await qc.cancelQueries();

  // 3. Remove, don't invalidate: invalidated data is still SERVED while refetching.
  qc.removeQueries({ queryKey: ['tenant', prevId] });   // prefix-match: whole subtree

  // 4. Sockets joined entreprise_<prevId>_* groups and would keep pushing that
  //    tenant's events into the cache.
  resubscribeSockets(nextId);

  // 5. No refetch call here on purpose: mounted observers are now on
  //    ['tenant', nextId, ...] keys with no data, so Query fetches them itself.
}
```

## Tenant-aware persistence
Persistence outlives the switch *and the session*, so it is the leak that survives
a reload. **Persist the tenant id; never another tenant's fetched rows.**

- `partialize` the store down to `activeEntrepriseId` plus UI prefs — a persisted
  list of tenant A's invoices is readable next login under tenant B (see
  `zustand-state`).
- Do not add a persister to the Query cache on a multi-tenant app unless it is
  keyed per tenant and cleared on logout. A whole-cache persister writes every
  tenant's rows to `localStorage`, where nothing scopes them.
- On logout, clear both — `qc.clear()` and the persisted store — or the next user
  on that browser hydrates into the previous one's data.
- Rehydrating a persisted `activeEntrepriseId` is a *hint*, not an entitlement:
  the server must re-validate that membership on every request. If it now 403s,
  fall back to the switcher rather than retrying.

## Adapt to your repo
Rename `entreprise`/`activeEntrepriseId`, the store (`useUI`), and the socket group
prefix (`entreprise_<id>_notifs`) to your project's terms. Confirm where the tenant
header is stamped — one shared API client, not per-`queryFn` `fetch` calls — and
that it reads the same store field the keys are built from; two sources of truth
here *is* the bug. If the tenant lives in an HttpOnly cookie or the session rather
than a header, the switch is a server round-trip first, then steps 2-5 unchanged
(see `cookie-auth-csrf`). Pin nothing to a Query version — check the installed one
before copying an API name (see `version-check`).

## Gotchas
- **`invalidateQueries` is not `removeQueries`.** Invalidated data stays in the
  cache and is rendered to the new tenant during the refetch. Remove it.
- **Not awaiting `cancelQueries()`** lets a settling old-tenant response land after
  your removal and repopulate the cache. Await, then remove.
- **`qc.clear()` is the blunt version** and is safe — it just also drops tenant-
  independent entries (reference data, the session itself), causing a refetch
  stampede. Prefer removing the `['tenant', prevId]` subtree.
- **A key that forgot the tenant prefix** silently opts out of all of this: it is
  neither removed by the prefix match nor distinct per tenant. One un-prefixed key
  factory reintroduces the leak everywhere it is used.
- **Sockets are a second write path into the cache.** A switch that only touches
  Query still leaks if the consumer stays in the old group.
- **The switcher's own list of tenants is not per-tenant data** — key it under the
  user, or it gets removed on every switch and refetched for nothing.
- **Test the switch, don't eyeball it**: mount tenant A's list, switch, assert the
  DOM never renders an A row (see `write-tests`, `browser-e2e-testing`).

## See also
- `react-query`
- `multi-tenancy`
- `websockets-channels`
- `zustand-state`
