# Stack version snapshot — verified 2026-07-16

> ⚠️ **This snapshot is dated and WILL go stale.** It is a starting point, not a
> source of truth. Re-verify every version and its support window at *your* install
> time using the method in [`../SKILL.md`](../SKILL.md) (endoflife.date, PyPI,
> npm, and the vendor release pages). Prefer an LTS / maintained line for production.

Sources were retrieved live on 2026-07-16 from the URLs in the last column.

## Backend — Python & Django

| Technology | Current stable | LTS / supported | EOL | Source |
| --- | --- | --- | --- | --- |
| Python (CPython) | 3.14.6 | No formal LTS; 3.14 & 3.13 bugfix, 3.12/3.11/3.10 security-only | 3.14: 2030-10-31 · 3.13: 2029-10-31 · 3.12: 2028-10-31 · 3.11: 2027-10-31 · 3.10: 2026-10-31 | endoflife.date/python |
| Django | 6.0.7 | **5.2 LTS** (5.2.16) current LTS; next LTS 6.2 (~Apr 2027, unreleased) | 6.0: sec ~2027-04 · 5.2 LTS: 2028-04 · 4.2 LTS: ended 2026-04-07 | djangoproject.com/download |
| Django REST Framework | 3.17.1 | Track latest; supports Python 3.10–3.14, Django 4.2–6.0 | n/a | pypi.org/project/djangorestframework |
| djangorestframework-simplejwt | 5.5.1 | Track latest; Django 4.2–5.2, DRF 3.14+ (6.0 not yet listed) | n/a | pypi.org/pypi/djangorestframework-simplejwt |
| dj-rest-auth | 7.2.0 | Track latest; Django 4.2–6.0, DRF ≥3.13, Python 3.10–3.14 | n/a | pypi.org/pypi/dj-rest-auth |

## Async & real-time

| Technology | Current stable | LTS / supported | EOL | Source |
| --- | --- | --- | --- | --- |
| Celery | 5.6.3 | Track latest; 5.x maintained (Python ≥3.9) | n/a | pypi.org/pypi/celery |
| Redis (server) | 8.8.0 | Track latest; maintained 8.8/8.6/8.4, plus 7.4 & 7.2 | 8.2: 2026-05-25 · 8.0: 2026-02-11 · 7.0: 2024-07-29 | endoflife.date/redis |
| Valkey (Redis fork, BSD-3) | 9.1.0 | Track latest; 8.1 longest-supported | 9.0: 2028-10-21 · 8.1: 2030-03-31 · 7.2: 2029-04-16 | endoflife.date/valkey |
| Django Channels | 4.3.2 | Track latest; 4.x → Django 4.2–6.0, Python 3.9+ | n/a | pypi.org/pypi/channels |
| channels-redis | 4.3.0 | Track latest; requires channels ≥4.2.2 | n/a | pypi.org/pypi/channels-redis |
| Daphne (dev ASGI server) | 4.2.2 | Track latest; Python ≥3.9 | n/a | pypi.org/pypi/daphne |
| Uvicorn (prod ASGI server) | 0.51.0 | Track latest; still 0.x, Python ≥3.10 | n/a | pypi.org/pypi/uvicorn |
| Gunicorn (WSGI server) | 26.0.0 | Track latest; 26.x current, Python ≥3.10 | n/a | pypi.org/pypi/gunicorn |

## Database & JS runtime

| Technology | Current stable | LTS / supported | EOL | Source |
| --- | --- | --- | --- | --- |
| PostgreSQL | 18.4 | No LTS (~5 yrs/major); supported 18,17,16,15,14 | 18: 2030-11-14 · 17: 2029-11-08 · 16: 2028-11-09 · 15: 2027-11-11 · 14: 2026-11-12 | endoflife.date/postgresql |
| Node.js (Current) | 26.5.0 | Becomes Active LTS 2026-10-28 | 26: 2029-04-30 (once LTS) | nodejs.org/en/about/previous-releases |
| Node.js Active LTS | 24.18.0 | **"Krypton" (v24)**; maintenance from 2026-10-20 | 2028-04-30 | nodejs.org/en/about/previous-releases |
| Node.js Maintenance LTS | 22.23.1 | "Jod" (v22) | 2027-04-30 | nodejs.org/en/about/previous-releases |
| pnpm | 11.13.1 | Track latest; 11.x current | n/a | registry.npmjs.org/pnpm |

## Frontend

| Technology | Current stable | LTS / supported | EOL | Source |
| --- | --- | --- | --- | --- |
| Next.js | 16.2.10 | v16 current major; v15 maintained | v15: 2026-10-21 · v14: ended 2025-10-26 | endoflife.date/nextjs |
| React | 19.2.7 | Track latest; 19.x current | n/a | registry.npmjs.org/react |
| TanStack Query (@tanstack/react-query) | 5.101.2 | Track latest; v5 active (v4 legacy) | n/a | registry.npmjs.org/@tanstack/react-query |
| Zustand | 5.0.14 | Track latest; v5 current | n/a | registry.npmjs.org/zustand |
| Zod | 4.4.3 | Track latest; v4 current (v3 legacy) | n/a | registry.npmjs.org/zod |
| Tailwind CSS | 4.3.2 | Track latest; v4 (Oxide) current | n/a | registry.npmjs.org/tailwindcss |
| shadcn/ui (CLI) | 4.13.0 | Copy-in components, not a runtime dep | n/a | registry.npmjs.org/shadcn |
| next-intl | 4.13.2 | Track latest; v4 (Next 16 compatible) | n/a | registry.npmjs.org/next-intl |

## AWS managed runtimes (lag upstream)

| Technology | Current | Offered / supported | EOL | Source |
| --- | --- | --- | --- | --- |
| Elastic Beanstalk — Python (AL2023) | Python 3.14 (platform v4.13.3) | Branches: 3.14, 3.13, 3.12, 3.11, 3.9; AL2 track retiring | migrate off AL2 platforms | docs.aws.amazon.com EB platform-history-python |
| Amazon RDS for PostgreSQL | PG 18 (18.4) | Standard support: 18,17,16,15,14,13 | 13: 2026-02-28 · 14: 2027-02-28 · 15: 2028-02-29 · 16: 2029-02-28 · 17: 2030-02-28 · 18: 2031-02-28 | docs.aws.amazon.com RDS PostgreSQL release calendar |
| Amazon ElastiCache — Valkey | Valkey 9.1 | 9.1, 9.0, 8.2, 8.1, 8.0, 7.2.6 (AWS-recommended path) | none announced | docs.aws.amazon.com ElastiCache engine-versions |
| Amazon ElastiCache — Redis OSS | Redis OSS 7.1 (frozen; last BSD release) | 7.1, 7.0, 6.2, 6.0, 5.0.6, 4.0.10 | v4/v5 std ended 2026-01-31 · v6 std 2027-01-31 | docs.aws.amazon.com ElastiCache engine-versions |

## Notable flags (as of this snapshot)

- **Django LTS moved on:** 4.2 LTS reached EOL 2026-04-07. Current LTS is **5.2** (→2028-04);
  6.0.7 is the newest *non-LTS* release; next LTS 6.2 is unreleased (~Apr 2027). A pin to
  Django 4.2 LTS is now unsupported.
- **Python 3.10 EOL 2026-10-31** is imminent — target 3.12/3.13 for new work (3.14 newest).
- **PostgreSQL 13 is EOL** (community 2025-11-13; RDS standard support ended 2026-02-28 →
  paid Extended Support). PG 14 is the oldest supported major, itself EOL 2026-11-12.
- **Gunicorn jumped to 26.0.0** (Jan 2026), well past the 23.x line one might assume; needs Python ≥3.10.
- **Uvicorn is still 0.x** (0.51.0) despite heavy production use — treat "latest" as the only supported release.
- **Node 26 is newest but NOT LTS** until 2026-10-28; for production use Node 24 (Active LTS) or 22 (Maintenance). Node 25 (odd) already EOL 2026-06-01.
- **Redis licensing:** since 8.0 (May 2025) Redis Open Source ships tri-licensed (AGPLv3 OR SSPLv1 OR RSALv2), reversing the 2024 SSPL-only move. **Valkey** (BSD-3) remains the fork most distros/managed caches ship as upstream.
- **AWS ElastiCache freezes Redis OSS at 7.1** and steers new workloads to Valkey 9.1 — the managed-cache story diverges from self-hosted Redis 8.x.
- **AWS Elastic Beanstalk lags upstream** — newest Python branch is 3.14 on AL2023; AL2-based platforms are retiring.
- **simplejwt 5.5.1 (Jul 2025) predates Django 6.0** — 6.0 is not yet in its documented compatibility matrix; verify before pairing.
