# Changelog

All notable changes to nanolama are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `version-check` skill — deep-research the current stable/LTS version and support
  window (at today's date) before installing, pinning, or upgrading any stack
  technology, with a dated 2026-07-16 snapshot (`reference/stack-versions-2026-07.md`)
  and the re-verify-at-install method. Cross-referenced from `dependency-audit` and `ci-cd`.
- Four skills distilled from an engineering-handbook review (general patterns only,
  no proprietary specifics): `webhook-handler` (verify → dedupe → resolve-tenant →
  ack-then-enqueue), `git-workflow` (branch/PR/rebase/safe-recovery), `money-decimal`
  (fixed-precision Decimal money + golden-fixture tests), and `incident-response`
  (report → contain → fix → blameless post-mortem → rotate). Library is now **34 skills**.

### Changed

- Enriched ~15 skills with hard-won production patterns (portable, no proprietary
  specifics): ALB idle-timeout dropping websockets, RDS backups + deletion protection,
  dependency-probing health checks, nested/indirect tenant scoping, "unseeded codename
  ⇒ 403", money/counter + BOLA + auth-token security-review items, AAA + golden +
  break-it-to-prove-it testing discipline, `retry_jitter` + worker connection hygiene,
  websocket keepalive-under-idle-timeout, leader-only migrate + migration-graph rules,
  and two-layer AI evals + prompt-injection-is-capability-limits.

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
