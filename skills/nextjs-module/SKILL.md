---
name: nextjs-module
description: Structures a Next.js 16 App Router frontend feature as layered modules (lib/api typed fetchers, query-keys, TanStack Query hooks, React 19 pages) fed by one shared fetch client that sends the auth cookie with credentials include, attaches the tenant header, and normalizes errors. Use when scaffolding a new frontend feature or module, building a fetch/apiClient wrapper, wiring cookie-JWT calls to the DRF backend, deciding where fetchers vs hooks vs pages live, or fixing a feature whose data layer is tangled. Not for query cache config and useMutation invalidation depth (see react-query) or form state and validation (see zod-forms).
---

# Next.js module (layered feature + shared fetch client)

## When to use
Starting or reorganizing a frontend feature that talks to the DRF backend, or
building the fetch client every feature shares. Keep each feature a thin stack of
layers so pages stay declarative and the auth/tenant/error concerns live in one place.

## Pattern
One feature = four layers, each depending only on the one below it:

```
app/(pages)  ->  hooks (useQuery/useMutation)  ->  query-keys  ->  lib/api (typed fetchers)
                                                                        |
                                                        shared fetch client (cookie + tenant + errors)
```

- **`lib/api/<feature>.ts`** — typed async fetchers, the only place a URL/verb appears.
- **query-keys** — one factory per feature so hooks and invalidation agree on keys.
- **hooks** — `useQuery`/`useMutation` wrapping the fetchers; components import these.
- **pages** — App Router Server/Client Components render hook state, no `fetch` inline.

Every fetcher goes through **one shared client** that sends the HttpOnly auth cookie
(`credentials: "include"`), attaches the tenant header, and throws a normalized error.
One vertical slice, top of stack unchanged from the client up:

```tsx
// lib/api/client.ts — one shared client: cookie-JWT, tenant header, normalized errors
export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) { super(`HTTP ${status}`); }
}
export async function apiClient<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    credentials: "include",               // HttpOnly cookie rides along; never read the token in JS
    headers: { "Content-Type": "application/json", "X-Entreprise": getTenantId(), ...init.headers },
  });
  if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => null));
  return res.status === 204 ? (undefined as T) : res.json();   // empty body on 204/DELETE
}

// lib/api/invoices.ts — typed fetchers are the only place a URL/verb appears
export const getInvoices = () => apiClient<Invoice[]>("/api/invoices/");

// query-keys — one factory so hooks and invalidation agree on keys
export const invoiceKeys = { all: ["invoices"] as const, list: () => [...invoiceKeys.all, "list"] as const };

// hooks — components import these, never the fetchers
export const useInvoices = () =>
  useQuery({ queryKey: invoiceKeys.list(), queryFn: getInvoices });

// app/invoices/page.tsx — declarative page reads hook state
"use client";
export default function InvoicesPage() {
  const { data, isPending, error } = useInvoices();   // TanStack v5: isPending, not isLoading
  if (isPending) return <Spinner />;
  if (error) return <ErrorState error={error} />;      // ApiError carries .status
  return <InvoiceTable rows={data} />;
}
```

## Adapt to your repo
Rename the tenant header (`X-Entreprise`) and `getTenantId()` to match your backend
and where the id lives (often a Zustand store — see the state pattern). Set
`NEXT_PUBLIC_API_URL` per environment. Pick your folder convention (`app/` vs a
`features/` directory) and hold it repo-wide. If you server-fetch in a Server
Component, forward the incoming `cookie` header explicitly — `credentials: "include"`
only applies to browser fetches.

## Gotchas
- Never read the JWT in JS or put it in `localStorage`; it is an HttpOnly cookie, so
  `credentials: "include"` is the whole auth story client-side.
- Cross-origin cookies need the backend CORS to allow credentials and the cookie to be
  `SameSite=None; Secure` — a silent 401 in prod is usually this, not your code.
- Don't call `fetch` inside components or pages; that scatters auth/tenant/error logic
  the client exists to centralize.
- Return `undefined` for `204 No Content` before calling `res.json()`, or a DELETE
  mutation throws on an empty body.
- Render loading, empty, AND error as three distinct states, not just success. A
  successfully-fetched empty list (`data.length === 0`) is not an error and not still
  loading — it needs its own empty-state UI (a message plus a call to action, e.g. a
  "Create your first invoice" button), never an infinite spinner or a blank table. So
  the page reads: `isPending` -> spinner, `error` -> error state, empty -> empty state,
  else -> the list.
- Validate response shapes at the fetcher boundary with Zod when the payload is
  untrusted or drifts (see `drf-zod-contract`).

## See also
- `react-query`
- `zod-forms`
- `drf-zod-contract`
- `i18n-rtl`
