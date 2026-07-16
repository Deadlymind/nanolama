---
name: zustand-state
description: Client-only UI state stores with Zustand for Next.js 16 App Router and React 19 — a small typed create() store, persist middleware with partialize to save only IDs and UI prefs (never fetched server objects), and an isHydrated/skipHydration guard to avoid SSR hydration mismatches. Use when adding a Zustand store, persisting a sidebar/theme/filter/selection to localStorage, fixing a "Text content did not match" or hydration warning from a persisted store, or deciding what belongs in client state versus server cache. Not for server data fetching, caching, or mutations (see react-query) or route/layout/module wiring (see nextjs-module).
---

# Zustand state (client UI state, not server data)

## When to use
You need ephemeral, client-owned UI state that outlives a single component:
theme, sidebar open/closed, a wizard step, active filters, or the *id* of a
selected row. If the value comes from the API, it does not belong here.

## Pattern
Two rules, held everywhere:

1. **Zustand holds UI state; React Query holds server state.** Never mirror
   fetched objects into a store — cache them with `react-query` and keep only
   *references* (ids, selection, prefs) in Zustand. Duplicated server data
   goes stale and desyncs.
2. **Persist is opt-in and narrow.** Use `persist` + `partialize` to save only
   the UI prefs/ids you actually want across reloads, and guard hydration so
   the server-rendered HTML matches the first client render.

## Steps / idioms
1. A small, typed store — state plus the actions that mutate it, colocated.
   Persist narrowly with `partialize`, and note the hydration hooks used below:

   ```ts
   // stores/ui.ts
   import { create } from "zustand";
   import { persist, createJSONStorage } from "zustand/middleware";

   type UIState = {
     sidebarOpen: boolean;
     activeEntrepriseId: string | null; // an id/reference, NOT the fetched object
     toggleSidebar: () => void;
     setEntreprise: (id: string | null) => void;
   };

   // create<T>()(...) — the extra () is required for TS inference with middleware
   export const useUI = create<UIState>()(
     persist(
       (set) => ({
         sidebarOpen: true,
         activeEntrepriseId: null,
         toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
         setEntreprise: (id) => set({ activeEntrepriseId: id }),
       }),
       {
         name: "ui", // unique per store, avoids localStorage key collisions
         storage: createJSONStorage(() => localStorage),
         // persist ONLY prefs + ids; never fetched server lists/objects
         partialize: (s) => ({
           sidebarOpen: s.sidebarOpen,
           activeEntrepriseId: s.activeEntrepriseId,
         }),
       },
     ),
   );
   ```

2. Guard hydration so SSR and the first client paint agree. Track a `hydrated`
   flag with `useState`/`useEffect` — seed it from `useUI.persist.hasHydrated()`
   and subscribe via `useUI.persist.onFinishHydration(() => …)` (it returns an
   unsubscribe). Render a neutral default until `hydrated` is true, then read
   `useUI(...)`; this prevents the "Text content did not match" warning.

3. Select narrow slices (`useUI((s) => s.sidebarOpen)`), not the whole store,
   so components re-render only on the fields they read.

## Variants
- **Manual rehydration.** Set `skipHydration: true` in the persist options and
  call `useUI.persist.rehydrate()` yourself (e.g. after reading a cookie or the
  server-known tenant), instead of the automatic-on-mount default.
- **Non-persisted store.** Drop the `persist` wrapper entirely for pure
  in-memory UI state (a modal, a drag position) — no hydration guard needed.

## Adapt to your repo
Rename `activeEntrepriseId` and the store to your domain, and set a unique
`persist` `name` per store to avoid `localStorage` key collisions. Confirm the
store file is client-side (imported only from `"use client"` components).
Bump the persist `version` and add a `migrate` fn when you change persisted
shape. If you also use Zustand outside Next.js, the hydration guard is only
needed where SSR renders the component.

## Gotchas
- Persisting fetched server objects is the classic bug — they go stale and
  fight `react-query`; persist ids/prefs only via `partialize`.
- Reading persisted state during the first render without the hydration guard
  causes "Text content did not match" / hydration-mismatch warnings.
- `create<T>()(...)` needs the extra call parens (curried form) for correct
  TypeScript inference with middleware — a common copy error.
- One module-level store is shared across all users in the same tab; never put
  per-request secrets or another tenant's data in it.

## See also
- `react-query`
- `nextjs-module`
