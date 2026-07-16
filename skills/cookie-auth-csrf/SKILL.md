---
name: cookie-auth-csrf
description: Wires the cookie-JWT plus CSRF auth seam end to end — DRF issuing the access token into an HttpOnly/Secure/SameSite cookie via simplejwt and dj-rest-auth, the Next.js client echoing the csrftoken cookie back as an X-CSRFToken header on every unsafe method, credentialed CORS pinned to an explicit origin allowlist, and refresh rotation with blacklist-on-logout. Use when setting up or debugging cookie auth, choosing SameSite Lax vs None, fixing a 403 on POST/PUT/PATCH/DELETE, chasing a silent 401 on cross-origin requests, revoking tokens at logout, or asking why cookie auth needs CSRF when header auth does not. Not for the generic feature/fetch-client layering (see nextjs-module) or role gating (see rbac-permissions).
---

# Cookie auth + CSRF (the auth seam, end to end)

## When to use
Standing up or debugging the seam where DRF issues a JWT into a cookie and the
Next.js frontend consumes it. Symptoms that land here: a 403 on every write, a
401 that only happens in production, a logout that does not actually log anyone
out, or a "just put the token in localStorage" suggestion.

## Pattern
**The token lives in an HttpOnly cookie, so JS can never read it. That closes XSS
token theft and opens CSRF — so every unsafe method must carry proof of intent.**

Why the trade is real, in one line each:

- **Header auth (`Authorization: Bearer ...`) is not CSRF-exposed** because the
  attacker's page cannot make your JS attach the header. Sending it *is* the proof
  of intent. But the token must be readable by JS, so any XSS exfiltrates it.
- **Cookie auth is CSRF-exposed** because the browser attaches the cookie to a
  cross-site request *automatically*. A form on `evil.com` posting to your API sends
  the session cookie without the user ever intending it — **possession of the cookie
  is not proof of intent**. The token is unreadable by JS, but the browser is now a
  confused deputy.

So you keep HttpOnly and buy back intent with a second, **deliberately readable**
token: the `csrftoken` cookie. JS reads it and echoes it as the `X-CSRFToken`
header on POST/PUT/PATCH/DELETE. The attacker's site can *force* the request but
cannot *read* your cookie (same-origin policy) — so it cannot produce the header.
The echo is the intent proof. SameSite narrows the window; the CSRF token closes it.

## Cookie flags, set deliberately

| Flag | Value | Why |
| --- | --- | --- |
| `HttpOnly` | `True` on the JWT cookie, **`False` on `csrftoken`** | JS must not read the token; JS *must* read the CSRF value to echo it |
| `Secure` | `True` everywhere but local HTTP | plaintext cookie on the wire is a stolen session |
| `SameSite` | `Lax` same-site, `None` cross-site | `None` **requires** `Secure`, and re-opens CSRF fully — the header is then your only defence |

Same-site (frontend and API share a registrable domain) is the safer default: prefer
`Lax` and a shared parent domain over `None` whenever the deployment allows it.

## Issuing and consuming

```python
# settings.py — DRF reads the JWT from a cookie; dj-rest-auth/simplejwt set it on login.
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "app-access",
    "JWT_AUTH_REFRESH_COOKIE": "app-refresh",
    "JWT_AUTH_HTTPONLY": True,        # JS cannot read the token; XSS cannot exfiltrate it
    "JWT_AUTH_SECURE": not DEBUG,     # HTTPS only outside local dev
    "JWT_AUTH_SAMESITE": "Lax",       # "None" ONLY if cross-site — and then Secure is mandatory
}
SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,    # each refresh mints a new refresh token
    "BLACKLIST_AFTER_ROTATION": True, # ...and kills the old one, so a stolen copy dies on next use
}
INSTALLED_APPS += ["rest_framework_simplejwt.token_blacklist"]  # required for revocation

# CSRF cookie is NOT HttpOnly on purpose — the client must read it to echo the header.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = ["https://app.example.com"]   # exact scheme + host, no wildcard

# CORS: credentials REQUIRE an explicit origin allowlist. A wildcard is rejected by the
# browser when credentials are included — and would be a cross-origin read hole if it weren't.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = ["https://app.example.com"]   # never CORS_ALLOW_ALL_ORIGINS
CORS_ALLOW_HEADERS = [*default_headers, "x-csrftoken"]
```

Client side, one shared fetch client does both halves — `credentials: "include"` so
the browser attaches the auth cookie, and `X-CSRFToken` read from `document.cookie`
on unsafe methods only. That client belongs to `nextjs-module`; do not re-implement
it per feature.

## Refresh rotation, logout, revocation
- **Access short, refresh long.** The refresh endpoint reads the refresh *cookie* and
  sets a fresh access cookie — the browser never hands the token to JS.
- **Rotate on every refresh** and **blacklist after rotation**. Replay of an old
  refresh token then fails instead of minting a live session.
- **Logout must revoke, not just forget.** Deleting the cookie only clears the
  *browser's* copy — anyone who captured the refresh token still holds a valid
  credential until it expires. Logout has to blacklist the refresh token server-side
  **and** clear both cookies. A logout that only drops the cookie leaves a live token.
- The refresh endpoint is an unsafe method too, so it needs the CSRF header like any
  other write.

## Adapt to your repo
Rename the cookie names (`app-access`/`app-refresh`) and set the allowlists per
environment — `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` are exact origins,
never wildcards, and must include the scheme. Decide same-site vs cross-site *first*
(a shared parent domain lets you keep `SameSite=Lax`); everything else follows.
Confirm the blacklist app is installed and migrated, or rotation silently no-ops.
Check the package names and settings keys against the versions you actually have
(see `version-check`) — the auth libraries rename these keys between majors.

## Gotchas
- **A 403 on a write means the CSRF header is missing (or the token is stale). Never
  `@csrf_exempt` the endpoint to silence it** — that permanently removes the only
  intent proof cookie auth has, on exactly the methods that change state. Fix the
  client to send `X-CSRFToken`.
- Never put the token in `localStorage` or read it in JS — that discards the entire
  reason for the HttpOnly cookie (see `security-review`).
- `SameSite=None` without `Secure` is silently dropped by browsers. The symptom is a
  clean 401 in production and a working local dev — not an error you can see.
- A wildcard CORS origin plus `allow-credentials` does not "work anyway" — browsers
  reject the combination. Reaching for `CORS_ALLOW_ALL_ORIGINS` to fix a preflight is
  how the allowlist gets deleted.
- The `csrftoken` cookie must exist before the first write. If the client never hits a
  GET that sets it, seed it from a login/CSRF endpoint on app boot.
- `X-CSRFToken` must be in the CORS allowed headers, or the preflight fails before your
  view ever runs.
- CSRF proves *intent*, not *authority*. It says the user meant to send the request —
  not that they may perform it, and not which tenant's rows they may touch. Keep the
  permission gate (`rbac-permissions`) and the tenant filter (`multi-tenancy`).
- Never log a cookie, a token, or an `Authorization` header — that puts the credential
  in plaintext in your log pipeline.

## See also
- `nextjs-module`
- `rbac-permissions`
- `security-review`
- `multi-tenancy`
