---
name: skill-authoring
description: Authors or fixes a skill in the nanolama library — the SKILL.md frontmatter contract (directory equals name, [a-z0-9-], no reserved words), a third-person description carrying "Use when" and a "Not for" boundary with no colon-space, the five required body sections, one inline example, and backticked See-also names from the roster. Use when creating a new skill, copying template/, editing an existing SKILL.md, wiring scripts/catalog.yaml, or fixing a validate_skills.py failure. Not for authoring the domain content of a specific skill (that lives in the skill itself) or reviewing a code diff (see code-review).
---

# Skill authoring (the nanolama SKILL.md contract)

## When to use
Adding a new skill to this library, or fixing one that fails
`python scripts/validate_skills.py`. The validator is the source of truth —
every rule below is enforced, so a green run is the definition of done here.

## Pattern
A skill teaches ONE reusable pattern that is true for ANY project on the house
stack, plus an "adapt to your repo" note — never one codebase's specifics. It is
a `SKILL.md` with exactly two frontmatter fields (`name`, `description`), the five
house sections, and cross-refs that resolve to real skills. The catalog must stay
in 1:1 sync with `skills/`.

## The frontmatter contract
- **`name`** — MUST equal the directory name; only `[a-z0-9-]`; <=64 chars; MUST NOT
  contain the reserved words `claude` or `anthropic`.
- **`description`** — third person; MUST contain the literal phrase `Use when`; <=1024
  chars; NO angle brackets. CRITICAL — no colon-followed-by-space `": "` anywhere (YAML
  misparses it); use an em dash `—` or a period. Also avoid `you can`/`you should`/`I will`
  (the validator flags first/second person). Front-load what-it-does + stack keywords +
  verbatim trigger phrases; end with a `Not for ...` clause handing adjacent scope to a
  named sibling (disambiguate shared keywords — ViewSet vs consumer vs task).

```yaml
# skills/<name>/SKILL.md — copy this shape, then rewrite every value.
---
name: my-skill                 # == directory name, [a-z0-9-], no claude/anthropic
description: Does X on Django/DRF — front-loaded keywords. Use when a user
  says "trigger phrase" or edits foo.py. Not for bar (see sibling-skill).
---                            # note: no ": " colon-space, third person, <=1024 chars
```

## The body contract
These five headings MUST appear verbatim (extra middle sections like
`## Steps / idioms` or `## Variants` are welcome):
`## When to use`, `## Pattern`, `## Adapt to your repo`, `## Gotchas`, and the
See-also section. Include ONE tight, correct, COMMENTED example inline (< ~40 lines,
real APIs for the stack versions, never a full app). Keep the whole file scannable and
under ~180 lines. In the See-also section, list siblings as backticked names — every
backticked token there must resolve to a real skill in the roster, or validation fails.

## Workflow
1. `cp -r template/ skills/<name>/` and rename the folder to `<name>`.
2. Rewrite `skills/<name>/SKILL.md`: frontmatter, the five sections, one example.
3. Add an entry under `skills:` in `scripts/catalog.yaml` (name, category, blurb).
4. Run `python scripts/validate_skills.py` — fix every reported problem.
5. Run `python scripts/generate_readme.py` to re-render the README table from the catalog.

## Adapt to your repo
This meta-skill targets THIS repo's real tooling (`template/`, `scripts/catalog.yaml`,
`scripts/validate_skills.py`, `scripts/generate_readme.py`). A fork that renames those
paths or changes `REQUIRED_SECTIONS`/`ALLOWED_FIELDS` in the validator must update this
skill to match — the validator, not this prose, is authoritative.

## Gotchas
- A colon-space `": "` in the description is the most common failure — YAML reads it as
  a key/value split. Use `—` or a period instead.
- `name` must equal the directory name exactly; a mismatch (or a stray `claude`/`anthropic`
  substring) fails validation.
- Every skill dir needs a matching catalog entry and vice versa — the validator checks
  1:1 sync, so a new folder without a catalog line fails.
- Don't add extra frontmatter fields; only `name` and `description` belong on a nanolama
  skill (the validator allows a few more but the house style is exactly two).
- Prove the file before claiming done — run the validator and paste its output (see `verify`).

## See also
- `verify`
- `code-review`
