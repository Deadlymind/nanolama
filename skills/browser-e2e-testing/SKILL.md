---
name: browser-e2e-testing
description: Drives real browser end-to-end tests (Playwright-style) over the few critical journeys on this Django/DRF plus Next.js stack — a storage-state auth fixture that logs in once and carries the HttpOnly cookie, the CSRF header on unsafe methods, per-test tenant-scoped seed data, and a negative authorization assertion that a user without the role is actually blocked. Use when adding or fixing an E2E spec, wiring the login/storage-state fixture, choosing which journeys deserve a browser test, debugging a flaky or order-dependent spec, or running the browser suite against a real server in CI. Not for unit or integration tests (see write-tests) or manually driving one change to confirm it works (see verify).
---

# Browser E2E testing (a handful of critical journeys)

## When to use
Adding, fixing, or pruning a real-browser test. E2E is the top of the pyramid and
the slowest, flakiest layer you own — spend it only where a silent break would be
catastrophic, and push every other assertion down to `write-tests`.

## Pattern
**A handful of journeys, never a mirror of the unit suite.** Budget roughly:

1. **Log in** — the auth path itself, unmocked.
2. **Create the core record** — the one object the product exists to produce.
3. **The money path** — checkout, invoice, payout: anything where a break costs cash.
4. **A tenant switch** — the user changes entreprise and the data actually changes.
5. **One negative authorization** — a user without the role is *blocked*.

If a case can be proven with an `APITestCase` or a hook test, it does not belong
here. Every extra spec is paid for in minutes of CI and in flake risk forever.

## The auth fixture is the crux
On a cookie-JWT stack the login is the expensive part, and it is the part most
people get wrong. Log in **once**, save the browser's storage state — the HttpOnly
access cookie rides inside it, because storage state is captured at the browser
level, not by JS — and reuse it across specs. Then remember the other half: the
cookie authenticates, but unsafe methods still need the **CSRF header** echoed
from the CSRF cookie, exactly as the real frontend sends it (see `cookie-auth-csrf`).

```ts
// e2e/fixtures.ts — rename the cookie/header names and routes to match your repo.
// Runs once (setup project), writes storage state; specs reuse it via `storageState`.
export async function loginAndSaveState(page, user, statePath) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  // HttpOnly access + CSRF cookies are both captured here — JS can't read them.
  await page.context().storageState({ path: statePath });
}

// Unsafe methods still need the CSRF header, cookie or no cookie.
export async function apiPost(context, url, data) {
  const csrf = (await context.cookies()).find((c) => c.name === "csrftoken");
  return context.request.post(url, { headers: { "X-CSRFToken": csrf.value }, data });
}
```

One state file **per role** (admin, viewer) and per tenant — that is what makes the
negative-authz spec a one-liner instead of a second login flow.

## Seed per test, and assert the negative path
Seed tenant-scoped data **for each test**, through a trusted setup route or a
management command hitting the real database — never by reusing whatever the last
run left behind. Give each test its own entreprise and its own records so specs can
run in parallel and in any order.

Then assert the thing that actually protects you: a viewer navigating to the admin
route gets a 403 or an empty screen, and the API call behind the button is refused
too. A green happy path proves the feature renders; only the negative path proves
the gate exists. Cross-tenant assertions live in the same place — after a tenant
switch, the previous tenant's records must be **gone from the DOM**, not merely
hidden behind a filter.

## Kill flake at the source
- **Web-first assertions, never sleeps.** `await expect(locator).toBeVisible()`
  retries until the app settles; an arbitrary `waitForTimeout` either wastes seconds
  or fails on a slow CI box. If a wait is unavoidable, wait on the *condition* — a
  response, a URL, an element state — not on the clock.
- **Deterministic data.** Seeded fixtures with known values. No `Date.now()` in an
  expected string, no random names you then assert on, no dependence on yesterday's
  row still existing.
- **No shared account, no test order.** Two specs mutating one login race each other
  the moment CI shards. Each test builds everything it reads.
- **Role locators over CSS.** `getByRole`/`getByLabel` survives a Tailwind refactor;
  a `.css-1x2y3z` selector breaks on the next build (see `tailwind-shadcn`).
- **A flaky E2E is a bug — quarantine nothing.** A spec that passes on rerun is
  telling you about a real race in the app or the fixture. Fix the cause or delete
  the spec; a permanently skipped test is a lie in your CI badge (see `write-tests`).

## Run it against a real server
The point of this layer is that nothing is mocked: a real Next.js build, a real
Django server, a real database, real cookies over the wire. In CI, boot the stack,
wait for a health endpoint, run the suite, and upload the trace/video for failures —
a trace turns "flaky on CI only" into a five-minute fix. Keep the browser job
separate from the unit job so a slow E2E never gates fast feedback (see `ci-cd`).

## Adapt to your repo
Rename the cookie names (`access`, `csrftoken` vs your `SIMPLE_JWT["AUTH_COOKIE"]`
and `CSRF_COOKIE_NAME`), the CSRF header (`X-CSRFToken`), `Entreprise`/`entreprise`,
and the login/dashboard routes. Confirm how your seed path is exposed and that it is
**disabled outside test settings**. Pin the browser runner and its browsers to one
version per repo rather than copying one from here (see `version-check`).

## Gotchas
- The HttpOnly cookie is invisible to page JS — you cannot read or set it from
  `page.evaluate`. Capture it via storage state or the browser context's cookie API.
- Storage state expires: a short-lived access token baked into a state file goes stale
  mid-suite. Regenerate it per run, and make sure the refresh flow is exercised by the
  login journey rather than assumed.
- A seed route that survives into production is a backdoor — gate it on test settings
  and confirm it 404s elsewhere (see `security-review`).
- Testing the happy path only is the default failure mode: the suite stays green while
  authorization silently disappears.
- E2E can prove a journey works; it cannot tell you *why* it broke. Reproduce the
  failure at the unit layer before fixing (see `debug`).

## See also
- `write-tests`
- `verify`
- `ci-cd`
- `cookie-auth-csrf`
