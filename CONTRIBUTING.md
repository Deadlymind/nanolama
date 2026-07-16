# Contributing to nanolama

Thanks for improving the library. nanolama ships **no runtime code** — it is a
catalog of Claude Code skills. A contribution is a new or improved `SKILL.md` that
teaches a **portable, model-agnostic pattern** for the house stack.

## The SKILL.md contract

Every skill lives at `skills/<name>/SKILL.md` and is checked by
`scripts/validate_skills.py` (also run in CI). The [`skill-authoring`](skills/skill-authoring/SKILL.md)
skill walks through it interactively; the rules:

### Frontmatter — two required fields

```yaml
---
name: your-skill-name
description: <third person>. Use when <triggers>. Not for <sibling scope>.
---
```

Those two are required and are all most skills need. Optional, if a skill genuinely
needs them: `license` (defaults to the repo MIT LICENSE), `allowed-tools`,
`disallowed-tools`, `metadata`, `compatibility`, plus the Claude Code fields
(`disable-model-invocation`, `when_to_use`, `context`, …). `validate_skills.py`
rejects any field outside that set.

- **`name`** — must equal the directory name; only `[a-z0-9-]`; ≤ 64 chars; must **not**
  contain the reserved words `claude` or `anthropic`.
- **`description`** — third person; must contain the phrase **`Use when`**; ≤ 1024
  characters; **no angle brackets**; and **no colon-followed-by-space (`: `)** — YAML
  would misparse it, so use an em dash `—` or a period. Front-load what the skill does
  plus concrete keywords, and end with a `Not for …` clause that hands adjacent scope
  to a sibling skill (the description is the *only* auto-trigger signal).

### Body — the house sections

These headings must appear, in this order (add middle sections like
`## Steps / idioms` or `## Variants` freely):

1. `## When to use` — one or two lines.
2. `## Pattern` — the core invariant in 1–2 sentences.
3. `## Adapt to your repo` — what to rename/confirm (nanolama is portable).
4. `## Gotchas` — the sharp edges.
5. `## See also` — sibling skills as **backticked names** from the catalog only
   (e.g. `` `drf-api` ``). Every backticked token here must be a real skill.

Include **one** tight, correct, commented code example (< ~40 lines) — copy-adaptable,
never a full app. State versions as current-state facts, never date-relative. Keep the
body scannable and under ~180 lines; push heavy reference material into
`skills/<name>/reference/*.md` (one level deep).

## Workflow

```bash
# 1. scaffold
cp -r template skills/your-skill-name    # then rewrite it

# 2. list it in the catalog (single source of truth)
$EDITOR scripts/catalog.yaml

# 3. regenerate the README table + validate + test
python scripts/generate_readme.py
python scripts/validate_skills.py
python -m pytest -q
```

Install dev tooling once with `pip install -r requirements-dev.txt`.

`validate_skills.py` enforces the whole contract mechanically: frontmatter fields and
limits, the five house sections **in order**, unique descriptions, cross-references and
local file links that resolve, and a valid `allowed-tools`/`disallowed-tools` shape.
`tests/test_validator_negative.py` keeps those checks honest with invalid fixtures.

## Attribution

Adapt, never blind-copy. If you adapt structure or wording from another public repo,
credit it in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and respect its license.
Never paste code or commands you have not vetted.

## Quality bar

- Concrete and portable — a pattern plus an adapt note, not one codebase's paths.
- Small and single-purpose; cross-reference siblings instead of duplicating them.
- Green `validate_skills.py`, `--check` README, and `pytest` before you open a PR.
- A skill earns its place by being genuinely useful — don't add one to inflate the count.

## Before you add a skill

> **Add a skill only when the missing workflow appears repeatedly in real work and
> cannot be cleanly handled by an existing skill.**

Research establishes candidate *quality*; usage establishes product *necessity*. A skill
is not free — its `description` competes in the same trigger space as every other skill,
so each addition slightly degrades the predictability of the ones that already work.
"It would be useful" is not the bar; "this came up repeatedly and nothing owns it" is.

If it does earn a place and the topic currently lives inside a bigger skill, **take
ownership and trim the old host to a pointer** — never leave two skills teaching the same
thing, or they compete for the same prompt. See [BACKLOG.md](BACKLOG.md) for the
validated-but-not-yet-needed candidates and the evidence we would want first.
