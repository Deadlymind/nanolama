# Third-party notices & attribution

nanolama is original work, but its **structure and conventions** were informed by
studying reputable public skill/plugin repositories during the research phase. We
adapt patterns to our stack and quality bar — we do **not** copy code or text verbatim.
Where a specific skill's shape is adapted from a source, that skill's `SKILL.md` carries
a trailing comment pointing back here.

With gratitude to:

## obra/superpowers — MIT
<https://github.com/obra/superpowers>

- The `Use when …` description convention and the flat `skills/` namespace with
  name-based cross-references.
- The discipline-skill rhetoric (a non-negotiable rule + "red flags" + a
  rationalization table). The [`verify`](skills/verify/SKILL.md) skill's completion
  gate is adapted from *verification-before-completion*.

## anthropics/skills — Apache-2.0
<https://github.com/anthropics/skills>

- The two-field (`name` + `description`) SKILL.md frontmatter contract and the
  progressive-disclosure model (SKILL.md body + on-demand reference files).
- The `template/` starter-skill idea and this `THIRD_PARTY_NOTICES.md` pattern. The
  [`skill-authoring`](skills/skill-authoring/SKILL.md) skill is informed by
  *skill-creator*.

> Note: the document-conversion skills in that repo (docx/pdf/pptx/xlsx) are
> source-available, **not** open source — nothing from them is used here.

## wshobson/agents — MIT
<https://github.com/wshobson/agents>

- Keeping catalog metadata in a single source of truth and generating the human-facing
  README from it, plus running real schema/lint validation in CI
  (`scripts/validate_skills.py`, `scripts/generate_readme.py`, `.github/workflows/ci.yml`).

## anthropics/knowledge-work-plugins
<https://github.com/anthropics/knowledge-work-plugins>

- The multi-dimension review lens behind [`code-review`](skills/code-review/SKILL.md),
  the reproduce→isolate→diagnose→fix shape in [`debug`](skills/debug/SKILL.md), and the
  confidence-gated finding shape in [`security-review`](skills/security-review/SKILL.md).
  Structure only — reviewed against the repo's license before reuse; no text copied.

## awesome-claude-code / awesome-claude-skills (curated lists)
<https://github.com/hesreallyhim/awesome-claude-code>

- The README skeleton (badge row, install snippet, category table) and the
  generate-the-catalog-from-a-data-file convention. Pattern reference only.

## kodustech/awesome-agent-skills — no license declared
<https://github.com/kodustech/awesome-agent-skills> (fronted by <https://ai-skills.io>)

- Surveyed as a **capability directory** to find gaps in this library. The repo
  declares **no license**, so **no text or code was copied** — only engineering
  *principles* were noted and rewritten from scratch for our stack. Skills whose
  gap was surfaced this way (e.g. [`observability`](skills/observability/SKILL.md),
  [`audit-logging`](skills/audit-logging/SKILL.md),
  [`accessibility`](skills/accessibility/SKILL.md),
  [`frontend-perf`](skills/frontend-perf/SKILL.md),
  [`production-readiness`](skills/production-readiness/SKILL.md)) are original work.
  Individual skills linked from that directory carry their own upstream licenses; we
  did not vendor any of them.

---

All third-party names and trademarks belong to their respective owners. If you believe
an attribution is missing or incorrect, please open an issue.
