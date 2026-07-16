---
name: changelog
description: Maintains a Keep a Changelog CHANGELOG.md with an Unreleased section, SemVer version headings, and grouped human-readable entries (Added, Changed, Fixed, Removed, Security, Deprecated) with compare-URL links. Use when adding a changelog entry, cutting a release, rolling Unreleased into a dated version, turning Conventional Commits into release notes, or asking "what changed in this version". Not for writing the git commit messages themselves (see commit-message) or the pipeline that publishes a release (see ci-cd).
---

# Changelog (Keep a Changelog + SemVer)

## When to use
Recording notable changes for humans, and cutting releases. Every user-facing
change lands in `CHANGELOG.md` under `## [Unreleased]` as you go; at release
time you promote that section to a dated, versioned heading. The changelog is
for people reading the project, not a `git log` dump.

## Pattern
Keep an always-present `## [Unreleased]` section at the top. Under it, use only
these groups, in this order, omitting empty ones: **Added, Changed, Deprecated,
Removed, Fixed, Security**. Pick the next version with SemVer — `MAJOR` for
breaking changes, `MINOR` for backward-compatible features, `PATCH` for fixes.
On release, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, open a fresh empty
`[Unreleased]`, and update the compare links at the bottom.

## Steps / idioms
1. As changes merge, add a bullet under the right group in `[Unreleased]`.
   Derive it from the Conventional Commit but **rewrite it for a reader** — drop
   the scope/type prefix, say what changed and why it matters.
2. To cut a release, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, open a
   fresh empty `[Unreleased]`, and update the compare links at the bottom so each
   version diffs against the prior one.
3. Tag the release commit `v1.4.0` so the compare URLs resolve; wire this into
   the release job (see `ci-cd`).

The single example below shows a just-cut release plus the compare links. The
`# from:` comments trace how each bullet was rewritten from its commit — they are
not part of the file:

```
## [Unreleased]

## [1.4.0] - 2026-07-16
### Added
- Bulk CSV export for invoices, scoped to your entreprise.   # from: feat(invoices): add bulk csv export
### Fixed
- Refresh token no longer 500s when the cookie is expired.   # from: fix(auth): handle expired refresh cookie
### Security
- Tenant filter now fails closed on unauthenticated reads.   # from: fix(tenants): fail closed

[Unreleased]: https://github.com/acme/repo/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/acme/repo/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/acme/repo/releases/tag/v1.3.0
```

## Adapt to your repo
Swap `github.com/acme/repo` for your remote, and the tag prefix (`v1.4.0` vs
`1.4.0`) to match your tagging convention — the compare URLs must use the same
prefix as your real tags. If you host on GitLab/Bitbucket, adjust the
`/compare/` URL shape. Keep the file at repo root as `CHANGELOG.md`. Rename the
`entreprise` reference in example entries to your tenant term.

## Gotchas
- One `[Unreleased]` always exists, even right after a release — never delete it.
- Don't paste raw commit subjects; a reader shouldn't need to know
  `feat(scope):` conventions to understand the entry.
- Dates are ISO `YYYY-MM-DD`, and version order is newest-first, top-down.
- A breaking change is `MAJOR` even if it's a one-line diff — SemVer tracks the
  contract, not the effort.
- Forgetting to update the `[Unreleased]` compare link leaves it pointing at the
  wrong base after a release; bump both links together.

## See also
- `commit-message`
- `ci-cd`
