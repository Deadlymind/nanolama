---
name: write-tests
description: Writes tests for this Django/DRF plus Next.js stack — Django TestCase with a tenant fixture factory, APIClient carrying the cookie JWT, a mandatory tenant-isolation test (user B gets 404/empty for user A's row), RBAC denial tests, and vitest that mocks the shared fetch-client to test hooks and Zod parsing. Use when adding tests, writing a TestCase or vitest spec, testing a ViewSet or React Query hook, covering tenant isolation or a permission denial, or asking what to test here. Not for driving a change end to end before calling it done (see verify) or wiring the CI that runs the suite (see ci-cd).
---

# Write tests (what and how to test on this stack)

## When to use
Adding or reviewing tests for a ViewSet, serializer, task, hook, or schema. Test
the seams that carry your invariants — tenant isolation, RBAC, contract parsing —
not framework internals. Every scoped resource ships with a tenant-isolation test.

## Pattern
Test **behavior at the boundary**, not implementation. On the backend that means the
DRF request/response through `APIClient` with a real auth cookie; on the frontend it
means the hook plus its Zod parse, with the **shared fetch-client mocked** — never the
raw network. Two tests are non-negotiable for any tenant-scoped endpoint: user B
cannot see user A's row (404/empty), and a user lacking the RBAC perm is denied (403).

## Steps / idioms
1. **Tenant fixture factory** — build isolated tenants once, reuse everywhere.
2. **APIClient with the cookie JWT** — authenticate the way production does (set the
   HttpOnly access cookie simple-jwt reads), not `force_authenticate`.
3. **The two required tests** — `test_tenant_isolation` (detail 404 *and* empty list)
   and `test_rbac_denied` (missing perm → 403). One Python example covers all three:

   ```python
   # tests/test_invoices.py — rename Entreprise/entreprise + perm codenames to match your repo
   def make_tenant(name, perms=()):                      # tenant fixture factory
       ent = Entreprise.objects.create(name=name)
       user = User.objects.create_user(f"{name}@t.io", "pw", entreprise=ent)
       user.user_permissions.add(*resolve_perms(perms))  # RBAC codenames, e.g. invoice_view
       return ent, user

   class InvoiceIsolationTest(APITestCase):
       def setUp(self):
           self.ent_a, self.user_a = make_tenant("a", perms=["invoice_view"])
           self.inv_a = Invoice.objects.create(entreprise=self.ent_a, total=10)

       def auth(self, user):  # set the HttpOnly access cookie simple-jwt reads
           self.client.cookies["access"] = str(AccessToken.for_user(user))

       def test_tenant_isolation(self):                  # THE required test
           _, user_b = make_tenant("b", perms=["invoice_view"])
           self.auth(user_b)
           assert self.client.get(f"/api/invoices/{self.inv_a.pk}/").status_code == 404
           assert self.client.get("/api/invoices/").json() == []   # empty, not A's row

       def test_rbac_denied(self):                       # missing perm returns 403
           _, viewer = make_tenant("c", perms=[])
           self.auth(viewer)
           assert self.client.get("/api/invoices/").status_code == 403
   ```

4. **Frontend** — `vi.mock` the shared fetch-client module (not `global.fetch` or MSW),
   then assert the hook plus its Zod parse. A `z.coerce.number()` field, for instance,
   turns the API's `"10.50"` string into `10.5` — test that coercion, not the network.

## What to skip
Framework internals (Django's ORM, DRF routing, TanStack Query's cache), trivial
getters/setters, and pure passthrough. If a test would only re-assert that Django or
Zod works, delete it. Cover *your* logic — scoping, permissions, coercion, edge cases.

## Adapt to your repo
Rename `Entreprise`/`entreprise`, the perm codenames, the cookie name (`access` vs your
`SIMPLE_JWT["AUTH_COOKIE"]`), and the fetch-client import path (`@/lib/api-client`) to
match your project. Confirm `AccessToken.for_user` matches your simple-jwt token class,
and run the suite against the same database engine as production so behavior matches.

## Gotchas
- The isolation test must assert **both** the detail 404 and the list being empty — a
  passing detail check with a leaking list is the classic miss (see `multi-tenancy`).
- Authenticate via the cookie, not `force_authenticate` — the latter skips the exact
  cookie/CSRF path production uses and hides auth-wiring bugs.
- Mock the shared client module, not `global.fetch` — you are testing your hook and
  schema, not the browser's networking.
- A green suite proves shape, not real behavior — still drive the flow (see `verify`).

## See also
- `multi-tenancy`
- `verify`
- `ci-cd`
