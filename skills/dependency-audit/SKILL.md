---
name: dependency-audit
description: Audits a project's Python and JavaScript dependencies for known CVEs and version drift — pip-audit for the backend, pnpm audit for the frontend, plus lockfile and pinning hygiene. Use when checking dependencies for vulnerabilities, adding or upgrading a package, reviewing a Dependabot or renovate PR, wiring a supply-chain gate into CI, or triaging an audit finding. Not for reviewing application code changes (see security-review) or general CI pipeline setup (see ci-cd).
---

# Dependency audit (supply-chain hygiene)

## When to use
Before adding or bumping a dependency, when a vulnerability scanner or bot flags one,
and on a schedule in CI. A CVE in a transitive package is as real as a bug in your own
code — treat the dependency tree as attack surface.

## Pattern
Scan **both** ecosystems against advisory databases, from the **committed lockfiles**
(so you audit exactly what ships), triage each finding (upgrade, or consciously accept
with a recorded reason), and run the scan as a CI gate so new CVEs surface on their own.

## Steps / idioms
1. Commit and audit from lockfiles — `uv.lock`/`poetry.lock`/pinned `requirements.txt`
   and `pnpm-lock.yaml`. Pin production deps; never audit a floating range.
2. Run both scanners; fail the build on the severity you care about:

   ```bash
   # Python — pip-audit reads installed pkgs or a requirements file (OSV/PyPI advisories)
   pip-audit -r requirements.txt --strict            # non-zero exit on any known CVE
   #   pip-audit --fix                                # auto-bump where a safe version exists

   # JavaScript — audit the pnpm workspace
   pnpm audit --prod --audit-level=high              # non-zero exit at >= high
   #   pnpm audit --fix                              # apply compatible upgrades

   # Triage a finding you cannot fix yet: upgrade, or record an explicit, expiring waiver
   #   (e.g. a pip-audit --ignore-vuln GHSA-xxxx with a comment + review date).
   ```

3. Automate the bumps: enable Dependabot or renovate, and review those PRs against this
   same checklist rather than merging blindly.
4. Vet **new** dependencies before adding: real project, active maintenance, sane
   transitive footprint, and the exact package name (guard against typosquats).

## Adapt to your repo
Swap the tools for your package managers (`npm audit`/`yarn npm audit`, `poetry`, `uv`,
`osv-scanner`, or `safety` as an alternative to pip-audit). Choose the `--audit-level`
threshold your team enforces, and point the commands at your real lockfile paths.

## Gotchas
- Auditing installed packages instead of the lockfile hides what actually deploys — scan the lock.
- `--audit-level=high` still lets moderate CVEs through; pick the threshold deliberately.
- A "fix" that jumps a major version can break you — read the changelog, don't just take `--fix`.
- Dev-only advisories still matter for your build/CI machines; scan dev deps too, separately.
- Accepting a finding without an expiry turns into a permanent silent risk — set a review date.

## See also
- `security-review`
- `ci-cd`
