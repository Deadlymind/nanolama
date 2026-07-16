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

## Design-guidance sources for the four design skills

The `product-ux-design`, `visual-ui-design`, `dashboard-data-design` and `design-system`
skills were written after consulting primary design sources. All guidance was restated
in original wording — no text, code, layouts, or visual identity was copied — but two
sources carry licenses that ask for attribution even of adaptations, and honesty asks
for the rest to be named:

- **GOV.UK Design System** — <https://design-system.service.gov.uk>, Crown copyright,
  Open Government Licence v3.0. Form/error/review-page/task-list pattern thinking and
  the evidence-gated contribution model informed `product-ux-design` and
  `design-system`. Contains public sector information licensed under the Open
  Government Licence v3.0.
- **Material Design 3** — <https://m3.material.io>, Google, documentation text CC BY 4.0.
  The token-tier concept, semantic color-role grammar, state and density guidance
  informed `design-system` and `visual-ui-design` (adapted, not copied).
- **W3C WCAG 2.2** and **WAI-ARIA Authoring Practices Guide** — cited as standards by
  SC number and pattern name; no normative text reproduced.
- **Apple Human Interface Guidelines** and **Microsoft Fluent 2** — consulted as
  informative references for hierarchy, spacing, and density principles; restated, no
  text copied (neither site's guidance text is openly licensed).
- **Radix UI**, **shadcn/ui**, **Tailwind CSS**, **Next.js**, **React** documentation —
  factual API and convention behavior restated for implementation-awareness; these
  projects' docs are MIT/CC-BY-licensed and their conventions are already credited to
  the implementation skills that own them.

---

All third-party names and trademarks belong to their respective owners. If you believe
an attribution is missing or incorrect, please open an issue.
