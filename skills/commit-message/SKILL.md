---
name: commit-message
description: Writes a Conventional Commits message from the staged git diff — type(scope) subject in the imperative under 72 chars, a body explaining WHY, and footers for BREAKING CHANGE and issue refs. Use when asked to write a commit message, "commit this", "conventionalize", or when deriving the type (feat, fix, chore, refactor, docs, test, perf, build, ci) and scope from what the diff actually changed. Not for the release-facing CHANGELOG rollup across many commits (see changelog) or judging whether the diff is correct (see code-review).
---

# Commit message (Conventional Commits)

## When to use
Turning a staged diff into one well-formed commit message. Read the staged
changes first — the type and scope are *derived from what the diff does*, not
from what you meant to do.

## Pattern
Subject line, a blank line, a body explaining WHY, then footers. The subject is
`type(scope): description` in the imperative, lowercase start, no trailing
period, kept short (the git convention is ~50 chars for the subject, wrap the
body near 72). The body explains the problem, not the mechanics the diff already
shows. A breaking API change on a tenant-scoped endpoint, for example:

```
feat(invoices)!: scope list endpoint to the caller's entreprise

The list view returned every tenant's invoices. Filter by the
authenticated user's entreprise so cross-tenant rows never leak.

BREAKING CHANGE: /api/invoices/ now returns only the current
tenant's rows; clients relying on the global list must paginate
per entreprise.
Refs: #482
```

- **type** — derive from the diff's dominant effect:
  `feat` (new capability), `fix` (bug), `refactor` (behavior-preserving),
  `perf`, `docs`, `test`, `build` (deps/bundler), `ci` (pipeline), `chore` (rest).
- **scope** — the touched area (module, app, or package), e.g. `invoices`, `auth`.
- **subject** — imperative mood ("add", not "added"/"adds"), lowercase start, no period.
- **body** — optional but expected for non-trivial changes; explains the *why*.
- **footer** — `BREAKING CHANGE:` (a `!` after the type/scope also flags it) and
  issue refs (`Refs: #123`, `Closes #123`).

## Adapt to your repo
Inspect the staged diff, not the working tree — run `git diff --cached --stat`
to see the area (scope) and `git diff --cached` to see what actually changed
(type + why). Pick the single dominant type: if a diff both adds a feature and
reformats, the feature wins — split unrelated changes into separate commits.
Rename the example scope (`invoices`, `entreprise`) to your own modules and
tenant term. If your repo uses a different taxonomy — a fixed scope list, or
**gitmoji** (`:sparkles:` = feat, `:bug:` = fix) — follow that instead of these
types, and match existing `git log` history. Confirm the subject-line length
your linter enforces (commitlint's default `header-max-length` is 100).

## Gotchas
- The type describes the diff's effect, not your intent — a "quick fix" that adds
  a new endpoint is `feat`, not `fix`.
- Subject is imperative and unpunctuated; the body is where prose lives.
- `BREAKING CHANGE:` must be spelled exactly (uppercase, in the footer) for tools
  to detect it — a bare `!` in the header is a hint, the footer is authoritative.
- Don't restate the diff line by line in the body; Git already shows *what*. Say *why*.

## See also
- `changelog`
- `code-review`
