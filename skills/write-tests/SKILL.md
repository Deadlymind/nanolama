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

## Shape of a test
Keep **Arrange / Act / Assert** visibly separate — build state, do the one thing,
assert the outcome. Name the test after the behavior so it reads as a sentence:
`test_empty_value_is_rejected`, not `test_2`. One behavior per test — if the name
needs an "and", split it. Always cover the **unhappy path**: empty, zero, negative,
the boundary value, and the missing-permission case, not just the golden input.

## Is the test real?
Before committing, **break the code on purpose** and confirm the test goes red — a
test that passes no matter what is worse than none. Assert the one value that
encodes the behavior (`resp.json()["total"] == "12.500"`), not an exact HTML dump or
a huge JSON blob that breaks on any cosmetic change. Mock **only the boundary** — the
outbound HTTP call, the clock — and run the real logic under test through it.

## Async and UI tests
- **Celery tasks** — run them synchronously with `CELERY_TASK_ALWAYS_EAGER = True`
  so a `.delay()` executes inline and you assert its effect directly. Control time
  (freeze the clock) to assert **retry/backoff** — a failing task reschedules with a
  growing countdown — and **idempotency**: run the task twice on the same input and
  confirm the second run is a no-op (no duplicate row, no double charge). Mock
  external calls at the **boundary** (the outbound HTTP client, the payment SDK), not
  the task body, so the real task logic runs through the mock (see `celery-tasks`).
- **React components** — use a component-testing library with `user-event` (not raw
  `fireEvent`) to test **form validation and submission** — a bad value shows the
  error, a good one calls the mutation once. Cover all four TanStack Query states:
  loading (skeleton), empty (no rows), error (retry visible), success (data renders).
  Render under your locale provider to check translated strings and **RTL** direction
  (`dir="rtl"`) so a mirrored layout doesn't regress silently.
- **Top of the pyramid** — a *few* end-to-end browser tests (Playwright-style) of the
  critical **cookie-JWT + CSRF + RBAC-gated** flows: log in, obtain the HttpOnly
  cookie, send the CSRF header, and confirm a viewer is blocked where an admin passes.
  Drive these with **tenant-scoped fixtures** so each run sees only its own tenant's
  data. Keep the count small — they are slow and brittle; push detail down to the
  unit and integration layers above.

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
- For money or precise computations, assert the **exact** known value and pin a
  hand-verified golden fixture — never an approximate compare (see `money-decimal`).
- For concurrency, don't try to reproduce the race; test the **invariant** the lock
  protects — balance never negative, no duplicate numbers (see `db-concurrency`).
- Make each test self-contained: build all state in setup. No reliance on run order,
  leftover data from another test, or the machine's timezone.
- A flaky test is a bug — fix the cause, never rerun until it goes green.
- A red test is a stop sign. Never delete or skip a failing test just to merge.

## See also
- `multi-tenancy`
- `celery-tasks`
- `money-decimal`
- `db-concurrency`
- `verify`
- `ci-cd`
