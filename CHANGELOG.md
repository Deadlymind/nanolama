# Changelog

All notable changes to nanolama are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
