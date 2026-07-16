---
name: architecture-decisions
description: Records an architecture decision as a numbered, immutable ADR under docs/adr — Status, Date, Context, Decision, Consequences, and the alternatives that lost — so the reasoning outlives the people who held it. Use when a choice is expensive to reverse or cross-cutting (Celery versus a cron, cookie JWT versus bearer tokens, one shared DB with a tenant FK versus schema-per-tenant), when a settled trade-off is being re-litigated in review, when superseding an earlier ADR, or when a PR needs a link to the reasoning behind it. Not for the commit message that carries the change (see commit-message) or the user-facing release notes (see changelog).
---

# Architecture decisions (ADRs that outlive the team)

## When to use
A choice is on the table that someone will question in six months, and the answer
lives in one engineer's head or in a Slack thread that will be gone. Write the ADR
*while the arguments are still fresh* — reconstructed reasoning is fiction.

Three tests. Any one earns an ADR:

- **Expensive to reverse.** Unwinding it means a data migration, a re-auth of every
  client, or a rewrite — schema-per-tenant versus a shared DB with a tenant FK.
- **Cross-cutting.** It constrains code nobody has written yet — cookie JWT versus
  bearer tokens changes every frontend fetch and every CSRF decision.
- **A trade-off future-you will re-litigate.** Celery versus a cron, Zustand versus
  server state, one queue versus several. If the losing option is *reasonable*, the
  ADR is what stops the argument from restarting annually.

Not everything is an ADR. Reversible, local choices — a helper's name, a library
swap behind one module — are just commits. An ADR file per PR is noise, and noise
is how the trail stops being read.

## Pattern
An ADR is a **dated, numbered, immutable** record of one decision. Five parts:

1. **Status** — Proposed, Accepted, Superseded by ADR-0012, Deprecated.
2. **Date** — when it was decided, not when it was typed up.
3. **Context** — the forces, *honestly*, including the constraint you disliked.
   "We had four weeks and one backend engineer" is context. Leave it out and the
   next reader assumes you were wrong instead of constrained.
4. **Decision** — active voice, future tense, what we **will** do. "We will scope
   every business queryset by a tenant FK," not "it was felt that scoping is good."
5. **Consequences** — what this makes easy **and** what it makes hard. An ADR with
   no downside is marketing, and the reader will trust none of it.

Plus **Alternatives considered** and, for each, *why it lost* — that is the section
that actually gets read, because the person reopening the question is usually
holding the alternative.

The immutability is the whole point. A decided ADR is **never edited**; when the
decision changes, write a new one that links back and flip the old Status to
*Superseded*. You are keeping a trail, not a current-state document.

## Idioms — the file

```markdown
<!-- docs/adr/0007-cookie-jwt-over-bearer-tokens.md -->
# ADR-0007 — Cookie JWT over bearer tokens

Status: Accepted            <!-- becomes "Superseded by ADR-0015" — never deleted -->
Date: 2025-03-11

## Context
The SPA must call the DRF API from the browser. Tokens in localStorage are
readable by any XSS on the page, and we ship third-party analytics we do not
control. We dislike that cookies force us to own CSRF — noted, not hidden.

## Decision
We will issue JWTs in HttpOnly + Secure + SameSite cookies, and enforce CSRF on
every unsafe method. No token ever reaches JavaScript.

## Consequences
Easy: XSS cannot exfiltrate a session; logout is a server-side cookie clear.
Hard: CSRF tokens on every mutation; cross-origin needs explicit CORS + credentials;
native clients later will need a separate path. We accept that cost.

## Alternatives considered
- **Bearer token in localStorage.** Trivial for the SPA, no CSRF. Lost: one XSS
  is a full account takeover, and we cannot audit the analytics bundle.
- **Server sessions only.** Lost: our Channels workers already verify JWTs.
```

Numbered `0001`, `0002`, … so they sort and so "ADR-0007" is an unambiguous thing
to say in a review. Zero-padded, kebab-case slug after the number.

## Link it from the PR
An ADR nobody finds is a diary. Two links, both cheap:

- **The PR that implements it references the ADR** ("Implements ADR-0007"), so the
  diff and the reasoning are one click apart forever (see `git-workflow`).
- **The ADR lands in the same PR as the change**, or immediately before it. An ADR
  merged three weeks later documents a decision that was actually made in review
  comments — the trail is already broken.

In review, "why not X?" answered by a link to an ADR is a *closed* thread. The same
question answered from memory reopens next quarter (see `code-review`).

## Adapt to your repo
`docs/adr/` is a convention, not a law — `docs/decisions/` is equally fine, but pick
one and never move it, because links from old PRs are the asset. Decide who can
accept an ADR (author plus one reviewer, or a tech lead) and write that rule into
the repo's contributing guide, not into each ADR. If your project pre-dates its
ADRs, do not backfill the archive — write ADR-0001 for the next real decision and
let the trail start there. Keep the Status vocabulary short and fixed; three values
people use beat eight nobody remembers.

## Gotchas
- **Editing a decided ADR destroys the trail.** Fixing a typo is fine; changing the
  Decision or the Context is rewriting history. Supersede instead.
- **A Context that only lists reasons you were right is unusable.** The constraint
  you resented — the deadline, the one senior engineer, the client's fixed API — is
  exactly what a reader needs to judge whether the decision still holds now that the
  constraint is gone.
- **Consequences are not a benefits list.** If you cannot name the thing this makes
  harder, you have not finished thinking, and reviewers can tell.
- **"Superseded" is not "wrong".** ADR-0007 was right in 2025 and ADR-0015 is right
  now. Both stay. Deleting the loser deletes the reason the winner exists.
- **Do not pin tool versions in an ADR** unless the version *is* the decision — the
  file is immutable and will be stale within a year (see `version-check`).
- An ADR is not a design doc. One decision, one page. If it needs diagrams and a
  rollout plan, that is a separate document the ADR can link to.

## See also
- `git-workflow`
- `code-review`
- `production-readiness`
