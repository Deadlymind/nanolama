---
name: git-workflow
description: Runs the daily branch to PR to merge loop safely on any git/GitHub repo — one branch per task, confirm the branch before every commit, rebase onto latest main before review, keep PRs small with a what/why/how-to-test description, and recover cleanly with amend, revert, and reflog. Use when starting a task branch, preparing or reviewing a pull request, deciding whether to amend or revert, undoing a bad commit, or recovering work that seems lost. Not for writing the commit text itself (see commit-message) or reviewing the diff's contents (see code-review).
---

# Git workflow (branch to PR to merge)

## When to use
Any time you move a change from your working tree into the shared history — cutting
a task branch, opening or updating a PR, or digging yourself out after a bad commit.
The shared branch (`main`) is sacred: it stays green and only receives reviewed,
rebased work.

## Pattern
Two guards hold the whole loop together:

1. **Confirm your branch before every commit.** A shared checkout or a worktree can
   switch under you between commands, so never assume — check, then commit.
2. **Rebase onto latest `main` before requesting review**, so CI tests the code as it
   will actually land, not a stale merge base.

Everything else — small PRs, honest descriptions, no reviews on red CI — falls out of
protecting the shared branch.

## Steps / idioms
1. **Branch per task**, never commit straight to `main`. Name by intent
   (`feat/…`, `fix/…`):

   ```bash
   git switch -c feat/tenant-filter main    # branch off a fresh main

   # ...work, then before EACH commit, confirm where you are:
   git branch --show-current                 # must NOT be main / a shared branch
   git add -p && git commit                  # message: see commit-message

   git fetch origin
   git rebase origin/main                    # replay onto latest before review
   git push -u origin HEAD                    # (push --force-with-lease after a rebase)
   ```

2. **Keep PRs small.** One reviewable idea per PR; if it grows, split it and stack the
   branches (each PR targets the one below it) rather than shipping a 40-file wall.
3. **Write a description that answers what / why / how-to-test.** Add before/after
   screenshots for any visual change so a reviewer verifies without checking out.
4. **Don't request review on red CI.** If you want early direction, open a **Draft PR**
   and say what feedback you're after; move it to Ready only once CI is green.

## Adapt to your repo
Rename the shared branch if it isn't `main` (`master`, `develop`, a release branch).
Match your host's push protection and the branch-name convention your team uses
(prefixes, ticket ids). If PRs auto-run CI, confirm the required checks before marking
Ready; if you use stacked PRs, pick a tool or a plain base-branch chain and stay
consistent.

## Gotchas
- **Amend only before you push.** Rewriting a commit others may have pulled forces them
  into a painful reset — once it's shared, add a new commit instead.
- **Undo merged history with `git revert`, never a force-push to a shared branch.**
  Revert makes a new inverse commit that preserves history; force-pushing `main`
  rewrites everyone's base.
- **A "lost" commit usually isn't.** `git reflog` lists every HEAD you've been on;
  find the sha and `git switch -c rescue <sha>` (or `git cherry-pick` it) to recover.
- `--force-with-lease` over `--force` on your own branch — it refuses to clobber
  commits you haven't seen (e.g. a teammate's push to your PR).
- Rebasing a branch others share rewrites their base too; only rebase branches that
  are yours.

## See also
- `commit-message`
- `code-review`
- `ci-cd`
