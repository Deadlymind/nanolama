# Changelog

All notable changes to nanolama are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
