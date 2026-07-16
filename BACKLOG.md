# Backlog — validated candidates, not a release plan

nanolama **holds at 49 skills**. The hold sat at 45 until 2026-07-16, when four frontend
design skills (`product-ux-design`, `visual-ui-design`, `dashboard-data-design`,
`design-system`) were added as an **explicit owner-authorized product-scope expansion** —
an owner decision to widen what the library covers, not an evidence-gate pass, and not a
precedent. Future skills, including every candidate below, remain subject to the existing
evidence gate. The candidates below are researched, scoped, and genuinely useful. They
are still not in the catalogue, on purpose.

> **Research establishes candidate *quality*. Usage establishes product *necessity*.**

## The gate

> **Add a skill only when the missing workflow appears repeatedly in real work and
> cannot be cleanly handled by an existing skill.**

Growth before activation evidence is the failure this library exists to avoid. A skill
is not free: its `description` competes in the same trigger space as all the others, and
that space is where discovery actually happens — so every addition slightly degrades the
predictability of the 45 that already work. "It would be useful" is not the bar.

## How the evidence gets gathered

Use the plugin on roughly **15–25 real Django/Next.js tasks**, ideally spanning what the
catalogue claims to serve: a new DRF resource · tenant isolation + RBAC · a Next.js
feature · a migration · a Celery task · authentication + CSRF · a file upload · an API
performance problem · tests and browser E2E · a deploy / production-readiness pass.

Log five fields per task — deliberately few, because a heavier form just stops getting
filled in:

```text
Task:
Expected skill:
Actually activated:
Problem:   none | missed activation | wrong activation | incomplete guidance | competing skills
Correction required:
```

What that log is looking for, and what each finding actually implies:

| Finding | What it means |
| --- | --- |
| **no skill activates** | a possible unowned gap — a new skill is on the table |
| **the wrong skill activates** | fix the `description`; the catalogue is fine |
| **guidance runs out** | **enrich the owner first** — split only if the missing workflow has its own distinct trigger, output and ownership boundary |
| **two skills always co-activate** | merge them or clarify the boundary; a new owner only when neither can cleanly own the workflow |
| **the domain barely recurs** | leave it here, however good the candidate is |

Default to fixing the 45: it is cheaper and keeps the trigger space clean. But "enrich,
never split" would be too strict — and would contradict this library's own history. The
0.3.0 carve-outs (`cookie-auth-csrf`, `tenant-session-switch`, `browser-e2e-testing`,
`ai-evals`) all came from skills that **did** activate and **were** overloaded, not from
silence. A repeatedly-incomplete workflow is real evidence; it just has to clear the
distinct-trigger / distinct-output / distinct-owner bar before it earns a skill of its own.

## Candidates, prioritised

### 1. `secure-file-ingestion` — Full-stack
Would own *building* the upload pipeline: authorization, tenant-scoped storage keys,
generated filenames (original kept only as metadata), extension allowlist + MIME +
magic-byte checks, compressed/decompressed size limits, quarantine and scanning,
async parsing, private storage with short-lived URLs, and a
`pending → scanning → accepted/rejected → processing → ready/failed` state machine —
with **no parsing before the security checks pass**.
**Why deferred:** `security-review` already *audits* upload handling; nothing yet proves
teams need a separate build-it owner. **Most likely to justify itself first.**
**Boundary if added:** ingestion (this) vs interpreting accepted data
(`bulk-import-pipeline`) vs OCR/extraction after the file is trusted (`ai-integration`)
vs auditing the result (`security-review`) vs provisioning the bucket (`aws-services`).

### 2. `postgres-query-planning` — Backend
Would own SQL-plan evidence rather than ORM shape: `pg_stat_statements`, reading plans
(seq/index/bitmap scans, join strategies, estimated-vs-actual rows, sort spills, buffers),
composite index column order (tenant-first), partial/covering/expression indexes,
duplicate and unused indexes, statistics and planner-estimate error, and production-safe
index creation.
**Why deferred:** `perf-review` covers N+1, bounding and caching — the layer most teams
actually hit. **Likely to justify itself on data-heavy or mature projects.**
**Boundary if added:** *"why does this endpoint issue 200 queries?"* → `perf-review`;
*"why is PostgreSQL ignoring this index?"* → this. Packaging the approved index change
stays with `migrations`.

### 3. `bulk-import-pipeline` — Backend
Would own the ERP import state machine: immutable source record + file hash, schema
validation, **dry-run preview before any write**, tenant resolved from the session (never
from the spreadsheet), chunked atomic batches, stable row fingerprints + checkpointed
restart, per-row error reporting, reconciliation totals, and safe cancellation only
between checkpoints. Plus spreadsheet formula injection on export (OWASP CSV Injection).
**Why deferred:** overlaps the resumable-backfill guidance already in `celery-tasks`;
the boundary is defensible but not free. **Wait for a real import implementation.**

### 4. `slo-error-budgets` — Infra & DevOps
Would own what `observability` produces telemetry *for*: user-centred SLIs, SLO targets,
error budgets, fast/slow-burn alerts, and what actually happens when the budget is spent.
**Why deferred:** more org process than coding workflow — likely a rare trigger.
**Wait until nanolama targets teams running measurable production traffic.**

### 5. `load-capacity-testing` — Quality & Security
Would own the load test `production-readiness` already demands: modelled traffic (not one
endpoint in a loop), tenant distribution, ramp/steady/spike/soak/capacity runs, thresholds
derived from SLOs, and stop conditions so a test cannot damage shared infrastructure.
**Why deferred:** same as above; also depends on `slo-error-budgets` to define the target.

## Also considered, deliberately not queued

- **`privacy-data-lifecycle`** — blocked on a named jurisdiction and a product retention
  matrix. A skill must *implement* an approved policy, never invent one.
- **`skill-supply-chain`** — nanolama *does* have a supply chain: npm (the pinned
  validator), PyPI (PyYAML, pytest, ruff), GitHub Actions, and contribution integrity.
  What it does not have is the **skill-import** surface those studies measure — it authors
  100% of its content and vendors no external skill. So the controls that genuinely apply
  are **repository** controls, and they are already in place: a pinned validator and
  SHA-pinned actions, recorded inspiration + licences, and reviewed contributions. Another
  skill description would add little on top of that — and a control that exists only as
  prose is not a control.
- **`skill-usage-audit`** — needs real session data; would start as a report script, not
  an auto-triggering skill.
- **`disaster-recovery`** — `aws-services` + `production-readiness` already cover backups,
  PITR, versioning and a tested restore. Justified only once explicit RTO/RPO, failover
  and a named business owner exist.
- Rejected outright: generic "senior backend/architect/QA" personas, Kubernetes/GitOps,
  non-AWS CI, scientific/model-training, and marketing skills — stack mismatch or trigger
  competition with most of the catalogue.

## Sources

Candidate research drew on OWASP (File Upload, CSV Injection), the PostgreSQL manual
(`pg_stat_statements`, `EXPLAIN`, `CREATE INDEX`), Google SRE (Implementing SLOs), and
the DRF throttling docs — plus two empirical studies of the skills ecosystem published on
arXiv. Both are **preprints, not peer-reviewed work**: their existence and content were
verified before being relied on, which is a weaker claim than review, so weight them
accordingly.

- *From Registry to Repository: How AI Agent Skills Are Written, Adapted, and Maintained* — <https://arxiv.org/abs/2607.00911>
- *Under the Hood of SKILL.md: Semantic Supply-chain Attacks on AI Agent Skill Registry* — <https://arxiv.org/abs/2605.11418>

No external skill was copied. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
