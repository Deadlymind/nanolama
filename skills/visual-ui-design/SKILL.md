---
name: visual-ui-design
description: Designs how a specific screen looks and communicates — implementation-ready visual blueprints for Next.js B2B SaaS and ERP interfaces covering composition, visual hierarchy, layout, typography direction, spacing, surface treatment, responsive and mobile-web behavior, complete visual states, restrained microinteractions, and screenshot critique. Use when designing or redesigning a page, form, table view, detail screen or navigation shell, making a screen premium or easier to scan, or when an existing UI looks generic, crowded, dated, visually weak, or inconsistent with its sibling screens. Not for end-to-end workflow and information architecture (see product-ux-design), choosing KPIs, charts, or which data deserves attention (see dashboard-data-design), system-wide token and component governance (see design-system), Tailwind/shadcn implementation (see tailwind-shadcn), or formal accessibility auditing (see accessibility).
---

# Visual UI design (how the screen communicates)

## When to use
Designing or critiquing the look of a specific interface — a page, form, dense
table view, detail screen, or navigation shell — including from a screenshot.
The workflow behind the screen belongs to `product-ux-design`, deciding what
data deserves attention to `dashboard-data-design`, and turning the blueprint
into code to `tailwind-shadcn`. The deliverable here is a blueprint a developer
can implement without guessing.

## Pattern
One dominant purpose per screen, expressed through hierarchy — size, weight,
position, spacing, and restrained color — never through decoration.
Distinctiveness comes from intentional composition, meaningful density,
coherent typography, and one memorable functional detail; if a proposal could
be pasted unchanged into any unrelated SaaS product, it is too generic and gets
redone from this screen's actual job. Operational software is used for hours
daily: density is a feature, and every visual choice must survive the question
"does this help the user scan, decide, or act faster?"

## Workflow
1. **Diagnose before redesigning.** For an existing screen or screenshot, assess
   hierarchy, alignment, spacing, density, readability, action priority, status
   visibility, navigation clarity, discoverability, consistency, visual noise,
   and responsive risks. Report as a table — Priority | Observation | User
   impact | Recommended change — and separate what is visible in the screenshot
   from what is assumed about behavior behind it.
2. **Rank the screen's hierarchy.** What must be understood first, acted on most
   often, requires attention, is secondary, may stay hidden — and what could
   cause an expensive mistake, which gets friction by design.
3. **Blueprint the layout.** Regions, content order, visual weight, primary and
   secondary action placement, supporting panels, sticky and scrolling behavior,
   drawer vs dialog choices — as a text wireframe when that is clearer. Sticky
   chrome must never fully cover the keyboard-focused element (WCAG 2.2
   SC 2.4.11), so plan scroll offsets together with the sticky regions.
4. **Offer up to three visual directions** on substantial work, then recommend
   one: conservative precision (finance, accounting, audit, compliance),
   intelligent operational workspace (ERP operations, logistics, payroll, CRM),
   or bold contemporary identity (newer customer-facing SaaS). Define each via
   character, hierarchy, density, typography character, surfaces, navigation,
   signature detail, strengths, and risks.
5. **Specify the screen's visual language conceptually** — semantic color roles,
   type hierarchy, spacing rhythm, radius and border strategy, elevation
   restraint, content widths, icon direction, focus/selection/status appearance,
   light and dark behavior. Keep it to the roles this screen needs;
   system-wide token architecture belongs to `design-system`.
6. **Design every state.** Loading, background refresh, empty, no-results,
   validation error, permission denied, read-only, disabled-with-reason,
   success, failure, stale data, conflict, long-running, partial success. On
   this stack, screen regions stream in independently (Suspense boundaries), so
   design a space-reserving skeleton per region — never one whole-page spinner —
   and expect regions to arrive in any order without shifting the layout.
7. **Add microinteractions only where they communicate** — progress, cause and
   effect, state change, success, failure, error prevention. Specify trigger,
   response, duration category, interruption behavior, and the reduced-motion
   fallback. At most one signature interaction per screen.
8. **Compose for desktop, tablet, and mobile web.** Touch targets at a minimum
   24×24 CSS px (WCAG 2.2 SC 2.5.8, AA — its spacing exception lets deliberate
   gaps make dense rows conform; comfortable targets are larger), small-screen
   priorities, navigation changes, alternatives to wide tables, sticky and
   keyboard-overlap behavior, truncation rules. Where a module appears in pages,
   panes, and drawers, specify behavior per available container width rather
   than per viewport (the stack has container queries — `tailwind-shadcn`).
   Mobile *web* only — native iOS/Android/React Native design is out of scope.

## Example
```text
# Layout blueprint — invoice detail, direction "conservative precision" (desktop → mobile web)
header      breadcrumb · invoice number + status chip ··· [Record payment] [⋯ secondary]
meta strip  client · issue/due dates · amount — one scannable line, tabular numerals
main 8/12   line-item table: qty/unit/total right-aligned, totals row heavier, no zebra noise
side 4/12   activity + payment history, newest first, quiet surface
mobile web  side panel stacks below; sticky footer carries the one primary action;
            line items collapse to per-line cards (label + value pairs)
states      draft = neutral chip · overdue = warning chip + due date text · paid = success chip
            (status is never color alone — the label carries the meaning)
signature   totals recompute live during edit with a brief emphasis — cause and effect,
            180ms ease-out, none under prefers-reduced-motion
```

## Validation tests
Before hand-off the blueprint passes: the five-second test (hierarchy readable
at a glance), frequent-task efficiency (the daily action costs the fewest
clicks and least eye travel), visual noise (every element earns its place),
responsive (usable at every width, not merely shrunk), consistency (matches
sibling screens or says why not), originality (not paste-anywhere generic), and
error prevention (the expensive mistake is the hardest action to perform).

## Adapt to your repo
Match the existing product's direction before inventing one — a redesigned
screen that ignores its siblings creates the inconsistency this chain exists to
prevent (`design-system`). Confirm brand constraints, the density your users
need (data-entry clerks vs occasional approvers), and the locale set: fr/en/ar
means the design must survive long French labels and Arabic RTL mirroring
(`i18n-rtl`). Note focus and contrast intent at design time; the formal WCAG
audit stays with `accessibility`.

## Gotchas
- The generic-AI look is a checklist to reject: arbitrary gradients, glass
  effects, everything-in-a-card, stacked rounded containers, decorative charts,
  hero-sized empty sections in operational software, random shadows, neon
  status colors, and animation that demonstrates nothing.
- Oversized typography and luxurious whitespace read as "modern" in a mockup
  and cost operators hours in a tool used all day. Set density from task
  frequency, not fashion.
- Two primary actions equal none. If everything is emphasized, nothing is.
- Status carried by color alone excludes color-blind users and fails in
  grayscale print — pair color with a label or icon (design-time duty; the
  audit is `accessibility`'s).
- A microinteraction that cannot name what it communicates is decoration —
  cut it, and always specify the reduced-motion fallback.
- Wide tables do not "responsive" by shrinking. Design the mobile-web
  alternative (cards, column priority, horizontal scroll with pinned key
  column) explicitly.
- Screenshot critique that presents assumptions as observations erodes trust —
  keep the two labeled apart.
- Defining a full token set for one screen creates a shadow design system —
  name the roles you need and let `design-system` own the vocabulary.

## See also
- `product-ux-design`
- `dashboard-data-design`
- `design-system`
- `tailwind-shadcn`
- `accessibility`
- `i18n-rtl`
- `frontend-perf`
