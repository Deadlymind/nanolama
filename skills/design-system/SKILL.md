---
name: design-system
description: Defines and governs the reusable design language of a Next.js B2B SaaS or ERP product — design principles, semantic token roles, typography and spacing scales, color semantics, component taxonomy, anatomy, variants and states, shared UX patterns, naming, documentation, contribution rules, deprecation and migration. Use when creating or evolving one design language across modules, standardizing modules that have drifted apart, stopping duplicate buttons/cards/tables, defining component variants and status semantics, or writing component usage contracts. Not for one workflow's UX (see product-ux-design), one screen's composition (see visual-ui-design), dashboard KPI and chart decisions (see dashboard-data-design), or the Tailwind v4 @theme variables and cva code that implement the system (see tailwind-shadcn).
---

# Design system (one language, governed)

## When to use
Making the whole product consistent and reusable over time — creating or
evolving the shared design language, standardizing modules that have drifted
apart, or stopping teams from shipping a fourth button. One screen's design
belongs to `visual-ui-design`; the CSS variables and component code that
implement the system belong to `tailwind-shadcn`. This skill decides what
exists, what things mean, and how the system stays coherent as it grows.

## Pattern
A design system is semantics plus governance, not a component collection.
Every color, type style, and spacing value is a **semantic role** (`danger`,
`surface`, `page-title`) that means the same thing in every module — never a
feature-specific value (`invoice-red`) — and every shared component has a
written contract. Without contribution rules, duplicate detection, and a
deprecation path, a token file is just a prettier way to drift.

## Workflow
1. **Audit what exists.** Inventory tokens, colors, typography, spacing, radii,
   shadows, components, variants — then the duplicates, inconsistent states,
   naming conflicts, accessibility and RTL gaps, and undocumented one-offs.
   Standardization starts from evidence, not from a blank palette.
2. **Write testable principles.** "Dense but readable", "consistent meaning —
   one semantic per color role", "accessible by default", "RTL-ready",
   "composition over new components". Each principle must be checkable in
   review; a principle that cannot reject a proposal is a slogan.
3. **Define semantic token roles** — background, surface, elevated surface,
   foreground, muted foreground, border, focus ring (one role, applied
   uniformly), selection, primary action, secondary action, destructive action,
   success, warning, danger, information, disabled, chart series — each with a
   paired foreground and a value in every theme scope (a role missing its dark
   value is a bug). Roles over raw values; meanings over feature names; raw
   palette values live one tier below the roles, so a rebrand changes values
   without renaming a single role.
4. **Set the typography scale** — display, page title, section title, body,
   supporting text, labels, table values, numeric emphasis (tabular figures),
   code/reference — with weight, line height, and responsive behavior. Arabic
   typically needs more vertical room than Latin (deep descenders, stacked
   diacritics) and has no native italic convention — plan a taller line height,
   choose a non-slanting emphasis strategy (weight, color role), and verify
   every text style in both scripts, not just the Latin specimen.
5. **Set spacing and layout rules.** One base rhythm, component and page
   spacing derived from it, dense and comfortable modes for operational
   screens, content widths, and the grid. Every value earns a rationale.
6. **Organize the component taxonomy** — primitives, form controls, feedback,
   navigation, data display, overlays, page patterns, domain compositions —
   and classify each proposal as a primitive, a variant of an existing
   component, a composition, or a feature-specific component that stays local.
   Three real usages before promotion; premature abstraction is how systems rot.
7. **Write component contracts** (see Example) — purpose, anatomy, props
   concept, variants, states, content rules, accessibility and RTL
   requirements, responsive behavior, and explicit misuse examples. Use the
   WAI-ARIA APG pattern for each interactive component as the design reference
   and carry its keyboard map and state semantics as acceptance criteria — the
   Radix primitives under shadcn/ui are built to follow those practices and
   expose state as data-state/ARIA attributes, so define states in that
   vocabulary, lean on the primitive for focus trap, dismissal and arrow-key
   behavior, and verify the specific widget rather than assuming full coverage.
8. **Codify shared patterns** — page headers, filter bars, forms, tables,
   detail screens, status communication, empty states, errors, destructive
   confirmation, background jobs, permission-denied, search, navigation,
   dashboard shells — so modules assemble from patterns instead of reinventing.
9. **Govern.** Proposal and review process, ownership, naming rules, test and
   documentation requirements per component, versioning, deprecation with a
   migration path, an exceptions register, and duplicate detection in review.
10. **Hand implementation to `tailwind-shadcn`** — the @theme OKLCH variables,
    cva variants, shared component code, and their tests. Definitions live
    here; code lives there; neither duplicates the other.

## Example
```text
# Component contract — StatusBadge (shared primitive, data-display)
purpose    one consistent way to show a record's lifecycle state across all modules
anatomy    container · optional leading dot · label (text always present, never dot alone)
props      status (semantic) · size (sm | md) · optional count
variants   neutral | info | success | warning | danger   ← semantic roles, not per-feature
states     default · with-count · truncated (full text on hover/focus)
content    one or two words, from an i18n key — no free prose, no raw backend enums
a11y       meaning never carried by color alone — the label is the meaning (WCAG 1.4.1)
rtl        leading dot flips with dir via logical margins
misuse     ✗ a new InvoiceBadge/PayrollBadge per module — add a variant here instead
           ✗ danger for "important but fine" — danger means loss or blocked work
implement  tailwind-shadcn — cva variants over the semantic tokens defined above
```

## Adapt to your repo
Audit before adopting — the token roles above are a starting vocabulary, and
your product may genuinely need more chart-series or elevation roles (each
addition needs the same rationale). Confirm the primitive library (Radix under
shadcn/ui here) so contracts can lean on its keyboard and focus behavior
instead of restating it. Scale governance to team size: a solo team needs the
naming rules and duplicate check, not a committee. Keep dense mode real —
measure it on actual operational screens, not specimen pages.

## Gotchas
- A design system without governance is a component collection with a
  README. Steps 9–10 are the system.
- Duplicates are a discoverability failure, not a discipline failure — if
  finding the existing table pattern takes longer than building a new one,
  people will build. Naming and documentation are the countermeasure.
- Feature-named tokens (`invoice-red`, `payroll-green`) recreate the drift the
  system exists to end. Semantic roles only.
- Promoting a component after one usage bakes accidental requirements into a
  shared contract; wait for three real call sites.
- Deprecation without a migration path is a permanent fork — every removal
  ships with its replacement mapping and a deadline.
- An exceptions register beats silent exceptions: a team that cannot get a
  ruling will fork quietly.
- Consumer-app spacing imported into ERP screens breaks the "dense but
  readable" contract operators depend on — density modes are part of the
  system, not per-team taste.
- This skill defining CSS variables or cva code is a boundary violation —
  decide here, implement in `tailwind-shadcn`, audit accessibility in
  `accessibility`.

## See also
- `tailwind-shadcn`
- `visual-ui-design`
- `product-ux-design`
- `dashboard-data-design`
- `accessibility`
- `i18n-rtl`
