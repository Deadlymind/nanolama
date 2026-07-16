---
name: deploy-aws
description: Deploy runbook for this stack's Django/DRF backend on AWS Elastic Beanstalk (Gunicorn for WSGI, Uvicorn for the Channels ASGI app via Procfile, .ebextensions, leader_only migrate) and the Next.js frontend on Amplify (amplify.yml, pinned pnpm, env vars). Use when shipping a release, writing a Procfile or amplify.yml, running eb deploy, wiring container_commands, rolling back to a prior version label, or checking GET /health after a deploy. Not for provisioning RDS/ElastiCache/S3 (see aws-services) or the GitHub Actions pipeline (see ci-cd).
---

# Deploy to AWS (Elastic Beanstalk + Amplify)

## When to use
Shipping a backend release to Elastic Beanstalk or a frontend release to Amplify,
or debugging a deploy — Procfile process wiring, migrations on deploy, env vars,
rollback, and the post-deploy health check. **Deploys are gated: never run
`eb deploy` or trigger a prod build without asking the user first.**

## Pattern
The EB instance runs two processes from one **Procfile**: Gunicorn serves the
WSGI app, Uvicorn serves the **Channels ASGI** app (websockets). Schema changes
run **once per deploy** via a `leader_only` container command, never at import
time. Secrets live in the EB/Amplify **environment**, never in git. After every
deploy, prove it with `GET /health` and roll back by redeploying the previous
version label if it is red.

## Steps / idioms
The one thing to get right is the **Procfile** (repo root): two processes, one
WSGI (Gunicorn) and one ASGI (Uvicorn pointed at the Channels application).
Daphne is the local dev server — don't ship it here:

```procfile
# --max-requests recycles each worker after N requests to cap memory growth;
# --max-requests-jitter staggers the recycles so they don't all restart at once
# (values illustrative — tune to your traffic and memory budget).
web: gunicorn myproject.wsgi:application --bind :8000 --workers 3 --max-requests 2000 --max-requests-jitter 200 --timeout 60 --graceful-timeout 30
asgi: uvicorn myproject.asgi:application --host 0.0.0.0 --port 5000 --workers 2
```

Everything else is standard EB/Amplify wiring in prose:

1. **Migrate once, on the leader only** — in `.ebextensions/01_migrate.config`,
   a `container_commands` entry running
   `source /var/app/venv/*/bin/activate && python manage.py migrate --noinput`
   with `leader_only: true` so a multi-instance fleet doesn't race on locks. Add a
   second command for `collectstatic --noinput` (no `leader_only` needed).
2. **Env vars via the EB environment**, never committed —
   `eb setenv DJANGO_SETTINGS_MODULE=myproject.settings.prod SECRET_KEY=... DATABASE_URL=... REDIS_URL=...`,
   then `eb deploy`.
3. **Amplify frontend** — `amplify.yml` with a **pinned** pnpm in `preBuild`
   (`corepack enable`, then `corepack prepare pnpm@9.12.0 --activate`, then
   `pnpm install --frozen-lockfile`) and `pnpm run build`. Never `pnpm@latest`.
   Build-time `NEXT_PUBLIC_*` vars come from the Amplify console environment.
4. **Verify, then decide** — hit the health endpoint and read the body, don't
   assume: `curl -sS -w '%{http_code}\n' https://<your-api-domain>/health`.
5. **Rollback** = redeploy the last-known-good version label with no rebuild:
   `eb appversion --list` to find the prior good label, then
   `eb deploy --version app-20260715-1`.

## Adapt to your repo
Rename `myproject` (wsgi/asgi module paths), the settings module, and the health
URL. Match the pnpm version to your `packageManager` field in `package.json`.
Confirm `.ebextensions` uses your actual venv activation path and that
`ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` include the EB and Amplify domains. If you
run websockets, ensure the load balancer forwards the `asgi` port and upgrades.

## Gotchas
- **Ask before deploying.** A deploy is a side-effecting, prod-facing action —
  confirm the target env and the release with the user first.
- Without `leader_only: true`, every instance runs `migrate` simultaneously and
  they race on locks — one leader only (see `migrations`).
- Uvicorn is a production ASGI server but is **not** bundled with Channels; wire
  the ASGI application explicitly (`uvicorn myproject.asgi:application`). Daphne is
  the dev server; don't ship it as your prod ASGI process.
- `pnpm@latest` on Amplify makes builds non-reproducible — pin the exact version
  and commit the lockfile; use `--frozen-lockfile`.
- Secrets in `.ebextensions` or `amplify.yml` land in git history — keep them in
  the environment (`eb setenv` / Amplify console) only.
- **Websockets connect then drop after ~60s?** That's the load balancer idle
  timeout, not your code. Raise the ALB idle timeout (e.g. `3600`) via an
  `.ebextensions` `option_settings` entry under `aws:elbv2:loadbalancer`, and
  confirm the LB forwards/upgrades to the ASGI port.
- **Make `/health` actually probe its dependencies** — a cheap DB query plus a
  cache/broker ping, returning non-200 if either is down. A static `200` hides
  real breakage. On EB a failing health check auto-rolls-back the deploy; that's
  an intentional gate — don't disable it (see `verify`).
- **Quiesce background workers before `migrate`.** Add a `leader_only`,
  `ignore-errors` container command that stops the workers on the leader right
  before the migrate command, so they release DB connections/locks and don't race
  the schema change. They restart with the new release (see `migrations`).
- **Backend-only commit still rebuilds the frontend?** A push-triggered build host
  (Amplify) rebuilds the whole frontend on every push, even backend-only commits.
  Suppress non-frontend commits with a commit skip marker or a path filter so you
  don't burn build minutes on changes that can't affect the frontend.
- A green build is not a green deploy — the health check is the proof (see `verify`).

## See also
- `aws-services`
- `ci-cd`
- `migrations`
