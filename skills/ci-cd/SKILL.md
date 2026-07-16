---
name: ci-cd
description: Builds a GitHub Actions merge gate for the app stack — parallel backend/frontend jobs that run manage.py check, makemigrations --check --dry-run (fail on model drift), pytest, ruff lint, tsc typecheck, and pnpm build, with cached deps and required status checks blocking red PRs. Use when adding or fixing a workflow under .github/workflows, wiring CI for Django/DRF plus Next.js, catching migration drift or unformatted code before merge, running a dependency-audit gate, or asking how the pipeline blocks a broken branch. Not for deploying the built app to Beanstalk/Amplify (see deploy-aws) or authoring the tests themselves (see write-tests).
---

# CI/CD (GitHub Actions merge gate)

## When to use
Setting up or repairing the pipeline that must go green before any branch merges to
`main`. On this stack the gate has one job: refuse to merge a branch that fails a
static check, drifts from its migrations, breaks a test, or won't build.

## Pattern
**Fail closed at the PR boundary.** Split backend and frontend into parallel jobs,
cache their dependency stores, and make each check a distinct step so a red run points
at the exact failure. The migration-drift check (`makemigrations --check --dry-run`)
is the one people forget — it catches models edited without a migration, which passes
locally but breaks deploy. Mark every job a **required status check** in branch
protection so a red pipeline blocks merge instead of merely warning.

## Steps / idioms
1. One workflow, two jobs. Backend job (Postgres service, `manage.py check`, drift,
   pytest, ruff) and frontend job (`tsc`, `pnpm build`) run in parallel:

   ```yaml
   # .github/workflows/ci.yml
   name: CI
   on:
     pull_request: { branches: [main] }
     push: { branches: [main] }
   jobs:
     backend:
       runs-on: ubuntu-latest
       services:
         postgres:
           image: postgres:17
           env: { POSTGRES_PASSWORD: postgres, POSTGRES_DB: app }
           ports: ["5432:5432"]
           options: >-
             --health-cmd pg_isready --health-interval 10s --health-retries 5
       env:
         DATABASE_URL: postgres://postgres:postgres@localhost:5432/app
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: { python-version: "3.12", cache: pip }  # cache the wheel dir
         - run: pip install -r requirements.txt
         - run: python manage.py check                     # settings/app sanity
         - run: python manage.py makemigrations --check --dry-run  # fail on drift
         - run: ruff check .                               # lint (non-zero fails job)
         - run: pytest -q                                  # Django/DRF tests
         - run: pip-audit                                  # dependency-audit gate

     frontend:
       runs-on: ubuntu-latest
       defaults: { run: { working-directory: web } }
       steps:
         - uses: actions/checkout@v4
         - uses: pnpm/action-setup@v4
           with: { version: 9 }
         - uses: actions/setup-node@v4
           with: { node-version: "20", cache: pnpm, cache-dependency-path: web/pnpm-lock.yaml }
         - run: pnpm install --frozen-lockfile
         - run: pnpm tsc --noEmit                          # typecheck, no output
         - run: pnpm build                                 # Next.js production build
   ```

2. **Block merge on red.** In repo Settings → Branches → protect `main`: require
   the `backend` and `frontend` checks to pass and require branches be up to date.
   A green-only merge button is what actually enforces the gate; the YAML alone does not.
3. **Keep steps granular.** Separate `ruff check` from `pytest` so the summary names
   the failure. Add `ruff format --check .` if you enforce formatting.
4. **Audit dependencies in CI.** `pip-audit` (Python) and `pnpm audit --prod` (Node)
   flag known-vuln packages on every PR (see `dependency-audit`).

## Adapt to your repo
Rename the frontend dir (`web`), the Postgres image tag (16/17/18 all run Django 5.2),
and the Python/Node versions to match your project. If you use Poetry or uv, swap the
install step and its cache key. Point `cache-dependency-path` at your real lockfile.
Match the required-check names in branch protection to your actual job names, or the
gate silently passes. If a job needs secrets (RDS, S3), inject them via repository
secrets — never commit them.

## Gotchas
- `makemigrations --check --dry-run` exits non-zero **only** when a migration is
  missing — it is the drift guard; running plain `makemigrations` in CI would instead
  write files and hide the problem (see `migrations`).
- A cache alone doesn't install — you still run `pip install` / `pnpm install`; the
  cache only skips the download. `--frozen-lockfile` fails if the lockfile is stale.
- `pnpm build` needs any build-time env vars (`NEXT_PUBLIC_*`) present, or the build
  errors on missing config — set them as non-secret env in the job.
- Branch protection is per-branch and per-check-name; a renamed job silently stops
  being required until you re-add it. Verify a red PR is actually unmergeable.
- Deploy is a separate workflow triggered after this one is green — keep it here or
  see `deploy-aws`; don't couple test steps to deploy credentials.

## See also
- `deploy-aws`
- `write-tests`
- `migrations`
- `dependency-audit`
- `version-check`
