# Changelog

All notable changes to nanolama are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-16

Six focused skills (**39 → 45**), added only after the 0.2.1 correctness patch landed —
production-safety fixes first, catalogue growth second. Each new skill takes **ownership**
of a topic that was previously buried inside a larger skill, and the former host was
trimmed to a pointer so two skills never compete for the same trigger.

### Added

- **`cookie-auth-csrf`** — the cookie-JWT + CSRF seam end to end: why cookie auth is
  CSRF-exposed and header auth is not, HttpOnly/Secure/SameSite flags, the deliberately
  JS-readable `csrftoken`, credentialed CORS with an explicit origin allowlist, refresh
  rotation and server-side logout revocation.
- **`tenant-session-switch`** — the ordered switch: set tenant → cancel in-flight (they
  carry the old header) → remove the old tenant's cache subtree (not merely invalidate) →
  resubscribe sockets → refetch. Defence in depth; the server still enforces isolation.
- **`threat-modeling`** — STRIDE per feature at design time against this stack's trust
  boundaries (tenant, RBAC, auth/CSRF edge, upload ingestion, webhook payloads, the AI tool
  surface), producing a threat → mitigation → owning-skill table, not a document.
- **`browser-e2e-testing`** — a handful of critical journeys: storage-state auth reuse,
  tenant-scoped seeding, asserting the RBAC denial path, and killing flake at the source.
- **`ai-evals`** — the deterministic hard gate that blocks CI (tool-routing, must-not-call
  cases, tenant/RBAC through the tool layer, golden values) vs the advisory LLM judge that
  never gates. Never enforce safety with a check that can flake.
- **`architecture-decisions`** — ADRs: Context / Decision / Consequences, numbered and
  immutable, superseded rather than edited.

### Changed

- De-duplicated ownership so triggers do not collide: `nextjs-module` keeps the working
  client but defers CSRF depth to `cookie-auth-csrf`; `react-query` keeps the
  tenant-in-the-key invariant but defers the switch procedure to `tenant-session-switch`;
  `write-tests` keeps unit/integration but defers browser specs to `browser-e2e-testing`;
  `ai-integration` keeps the agent loop and write-tool contract but defers evals to
  `ai-evals` — relieving a genuinely overloaded skill.
- Fills the two structural gaps flagged in review: the Full-stack category grows 1 → 3, and
  AI 1 → 2.

## [0.2.1] - 2026-07-16

**Correctness and security patch.** An external audit was adjudicated claim-by-claim
against the real files; every finding that survived is fixed below. These skills are
copy-pasted by engineers and agents, so an unsafe simplified example is a defect —
this release prioritises correcting examples over adding skills.

### Fixed

- **CSRF (high)** — the shared fetch client sent the HttpOnly auth cookie but no
  `X-CSRFToken` on unsafe methods, and `nextjs-module`/`react-query` taught that
  `credentials: "include"` was "the whole auth story". Cookie auth is CSRF-exposed;
  the client now sends `X-CSRFToken` on POST/PUT/PATCH/DELETE, and the gotcha warns
  never to `@csrf_exempt` an endpoint to silence a 403 on write.
- **Cross-tenant cache leak (high)** — TanStack Query keys were not tenant-scoped while
  the tenant travelled only as a header, so a tenant switch could serve the previous
  tenant's cached rows. Keys are now `['tenant', tenantId, ...]`, with a
  `## Switching tenants` procedure (cancel in-flight → clear → resubscribe → refetch)
  and the invariant stated in both `react-query` and `nextjs-module`.
- **WebSocket CSWSH (high)** — `websockets-channels` omitted `AllowedHostsOriginValidator`;
  cookie-authenticated sockets are cross-site reachable. Now wrapped, with a gotcha.
- **WebSocket disconnect crash (medium)** — `disconnect()` discarded `self.group`, which a
  rejected connection never sets. Now a guarded `getattr(self, "group", None)`.
- **Celery false idempotency (high)** — a read-then-check on a status field is not a
  guard; two workers both read "not sent" and both deliver. Now an atomic claim
  (`select_for_update` + conditional transition) plus a provider idempotency key, since
  a DB rollback cannot un-send a completed HTTP call.
- **Destructive migration reverse (high)** — the reverse wiped the column on every row,
  including values that predated the migration, while the skill claimed it was safe.
- **Negative debit credited the account (high)** — `db-concurrency` quantized the amount
  but never required it to be positive. Now validated inside the lock.
- **Webhook event loss (high)** — the dedupe row was created before the tenant was
  resolved and before enqueue, so a retry hit `created=False` and returned 200 while the
  event was never processed. Now transactional with `on_commit` enqueue and a status
  field; plus body-size, malformed-JSON, replay-window and secret-rotation gotchas.
- **`money()` accepted floats (medium)** — contradicting the skill's own "never build a
  Decimal from a float" gotcha. Now raises `TypeError` (and explains why
  `Decimal(str(value))` merely launders the error).
- **`audit-logging` overclaimed "tamper-evident" (medium)** — the implementation is
  append-only. Reworded honestly, with a note on what real tamper-evidence requires
  (hash chaining / signed checkpoints / WORM). Also made the tenant FK nullable so a
  failed login with no resolvable tenant can be logged, fixed `record()` for
  `AnonymousUser`, and corrected the same-transaction vs `on_commit` trade-off.
- **`check_versions.py` exited 0 on total failure (medium)** — every lookup could fail and
  CI would still pass. It now counts failures and exits non-zero.

### Changed

- **Validator field policy** — replaced the single "portable fields" set with
  `PORTABLE_FIELDS | CLAUDE_CODE_FIELDS`. The old rationale was self-defeating: nanolama
  ships as a Claude Code plugin, and the set already admitted three non-CC fields. This
  unblocks `disable-model-invocation`.
- **`deploy-aws` is now manual-only** (`disable-model-invocation: true`) — a deploy is
  side-effecting and prod-facing, and Claude should not decide to deploy because the code
  looks ready. Invoke it explicitly as `/nanolama:deploy-aws`.
- **The repo now obeys its own `ci-cd` skill** — least-privilege `permissions`,
  `concurrency` with cancel-in-progress, `timeout-minutes`, SHA-pinned actions (verified
  against the real v4/v5 tags), a `ruff` lint step, and the **official**
  `claude plugin validate . --strict` as a CI gate.
- `CONTRIBUTING.md` no longer says frontmatter is "exactly two fields" while the
  validator allowed seven.

## [0.2.0] - 2026-07-16

Grew the library from **29 to 39 skills** and hardened the validation harness, across
three review passes: an engineering-handbook mining pass, a validator-quality pass, and
a survey of the ai-skills.io / awesome-agent-skills catalogue for capability gaps.

### Added

- Five skills for gaps surfaced by surveying the ai-skills.io catalogue (original work,
  principles only — no third-party text copied): `observability` (tenant-correlated
  structured logging, tracing, metrics, error tracking), `audit-logging` (append-only,
  tamper-evident security trail), `accessibility` (WCAG 2.2 + Arabic RTL), `frontend-perf`
  (Core Web Vitals / RSC), and `production-readiness` (go-live gate orchestrator).
- `version-check` skill — deep-research the current stable/LTS version and support window
  before installing, pinning, or upgrading, with a dated 2026-07-16 snapshot
  (`reference/stack-versions-2026-07.md`) and a runnable `check_versions.py` checker.
- Four skills distilled from an engineering-handbook review (general patterns only):
  `webhook-handler`, `git-workflow`, `money-decimal`, and `incident-response`.
- Negative-test suite (`tests/test_validator_negative.py`): 20+ intentionally-invalid
  fixtures plus positive cases confirming modern optional frontmatter is accepted.

### Changed

- Hardened `scripts/validate_skills.py`: enforces required-section ORDER, detects
  duplicate descriptions, checks broken local file links, validates
  `allowed-tools`/`disallowed-tools` shape, and adds a minimum-description floor.
- Enriched many existing skills with portable production patterns across two passes:
  ALB idle-timeout dropping websockets, RDS backups + deletion protection,
  dependency-probing health checks, nested tenant scoping, "unseeded codename ⇒ 403",
  money/counter + BOLA + auth-token + OWASP/SSRF/CSP items in `security-review`,
  AAA/golden/break-it-to-prove-it + async/RTL/E2E testing, `retry_jitter` + worker
  connection hygiene + resumable backfills, websocket keepalive-under-idle-timeout,
  leader-only migrate + migration-graph rules, two-layer AI evals +
  prompt-injection-is-capability-limits, `ci-cd` SAST/secret-scan/workflow-hardening
  gates, and RSC do-authorization-on-the-server.

## [0.1.0] - 2026-07-16

### Added

- Initial skills library: **29 portable, model-agnostic skills** for the house stack
  (Django 5.2 / DRF 3.16 · Celery · Channels · Next.js 16 / React 19 · AWS), across
  Backend, Frontend, Full-stack, Infra, AI, Quality & Security, and Workflow & Meta.
- Claude Code plugin packaging: `.claude-plugin/plugin.json` and a self-hosting
  `.claude-plugin/marketplace.json`.
- Validation harness: `scripts/validate_skills.py` (frontmatter, naming, cross-refs,
  catalog sync), `scripts/generate_readme.py` (catalog → README table), a `pytest`
  suite, and a GitHub Actions `validate` workflow.
- Project docs: README, CONTRIBUTING, THIRD_PARTY_NOTICES, a `template/` starter skill,
  and an MIT LICENSE.
