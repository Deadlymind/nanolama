---
name: version-check
description: Verifies the current stable and LTS version and support window of a technology by deep research before it is installed, pinned, or upgraded — checking today's release status on official release notes, endoflife.date, PyPI, and npm rather than trusting a hardcoded number. Use when adding a dependency, choosing or bumping a version, starting a project, planning an upgrade, or asking which version or LTS to use for Django, Python, Node, PostgreSQL, Next.js, or any stack tool. Not for scanning installed dependencies for CVEs (see dependency-audit).
---

# Version check (research the current LTS before you install)

## When to use
Before adding, pinning, or upgrading **any** technology, and whenever someone asks
"which version" or "which LTS". Versions and support windows move constantly; a number
written down months ago is a guess, not a fact — this skill included.

## Pattern
**Never trust a hardcoded version — check today's date and look it up.** Before you
install or pin, find the current stable and LTS release and its support/EOL window from
the authoritative source *now*, then pin the version that stays in support across your
horizon. Prefer an LTS/maintained line for production; avoid a major whose EOL is near.

## The check — where to look, at your install time
- **Support / EOL windows** → `https://endoflife.date/<product>` (or `/api/<product>.json`):
  python, django, postgresql, nodejs, redis, valkey, nextjs.
- **Python packages** → `https://pypi.org/pypi/<pkg>/json` — read `info.version`, and
  `requires_python` / classifiers for the supported Django & Python range.
- **npm packages** → `https://registry.npmjs.org/<pkg>/latest` — the `version` field.
- **Django LTS roster** (shifts ~every 2 years) → `https://www.djangoproject.com/download/`.
- **Node LTS line + codename** → `https://nodejs.org/en/about/previous-releases`
  (even-numbered majors are LTS only after ~6 months in Current).
- **AWS managed runtimes lag upstream** — check the EB platform history, the RDS Postgres
  release calendar, and the ElastiCache engine-versions doc; then confirm per account/region.

```bash
# Confirm the CURRENT version yourself — never paste a remembered number.
curl -s https://pypi.org/pypi/django/json      | jq -r .info.version   # newest Django on PyPI
curl -s https://registry.npmjs.org/next/latest | jq -r .version        # newest Next.js on npm
curl -s https://endoflife.date/api/python.json | jq -r '.[0].cycle, .[0].eol'  # newest Python + its EOL
aws rds describe-db-engine-versions --engine postgres --default-only   # what RDS actually offers here
```

## Baseline as of 2026-07-16 (re-verify — this WILL go stale)
Highlights; the full dated table with sources is in
[`reference/stack-versions-2026-07.md`](reference/stack-versions-2026-07.md).

- **Django 5.2 LTS** is the current LTS (supported to 2028-04); 6.0 is the newest
  *non-LTS* release; **4.2 LTS ended 2026-04-07**. The house Django pin still holds.
- **Python** newest is 3.14; **3.10 reaches EOL 2026-10-31** — target ≥ 3.12.
- **DRF 3.17.x** (a 3.16 pin is now behind), **Channels 4.3.x** (`channels-redis` ≥ 4.3,
  needs `channels` ≥ 4.2.2), Celery 5.6.3, Gunicorn 26.x, Uvicorn still 0.x.
- **PostgreSQL 18** newest; **PG 14 is the oldest still-supported major** (EOL 2026-11-12).
- **Node 24 "Krypton" is the Active LTS** (26 is not LTS until 2026-10-28) — build/CI on an LTS line.
- Frontend: Next 16.2, React 19.2, TanStack Query 5.10x, Zustand 5, Zod 4.4, Tailwind 4.3, next-intl 4.13.
- AWS: EB newest Python branch is 3.14 (AL2023; AL2 platforms retiring); ElastiCache freezes
  Redis OSS at 7.1 and steers new caches to **Valkey** 9.1.

## Adapt to your repo
Pin to your **support horizon**, not just "latest" — production favors an LTS/maintained
line with a comfortable EOL runway; a leading-edge app may take the newest stable. Record
the date you last verified beside the pin. Managed platforms (AWS EB/RDS/ElastiCache) gate
what you can actually run, so check them, not only upstream.

## Gotchas
- "Latest" ≠ "LTS" ≠ "still supported" — a shiny newest release may be a short-window
  non-LTS, and an old pin may be past EOL. Check the support window, not just the number.
- endoflife.date occasionally returns a wrong date — cross-check the vendor's own release
  page for anything load-bearing (for Django dates, prefer djangoproject.com).
- AWS runtimes lag upstream and freeze forks (Redis OSS 7.1) — the version you can *deploy*
  may trail the one you can `pip install`.
- A library can lag a new framework major (e.g. simplejwt predating Django 6.0) — confirm
  the compatibility matrix before pairing a new major with an older plugin.
- Snapshots rot — this section included. Re-run the check.

## See also
- `dependency-audit`
- `ci-cd`
- `deploy-aws`
