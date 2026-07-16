---
name: dashboard-data-design
description: Organizes complex data so users can decide and act — decision-focused dashboards and dense operational ERP screens with KPI selection and hierarchy, operational tables, chart choice, comparisons, targets and thresholds, exceptions and alerts, filters, saved views, drill-downs, totals and reconciliation, and honest data states. Use when creating or improving an executive or operational dashboard, analytics view, finance report, KPI screen, monitoring view, or table-heavy workspace, deciding which KPIs, columns, charts and exceptions deserve attention, or when data is on screen but users cannot see what matters. Not for the surrounding workflow design (see product-ux-design), visual styling and polish (see visual-ui-design), reusable component standards (see design-system), backend query performance (see perf-review), or data fetching and chart implementation (see nextjs-module and tailwind-shadcn).
---

# Dashboard & data design (decide and act, not admire)

## When to use
Designing or improving any screen whose job is understanding data — an
executive or operational dashboard, a finance report, a monitoring view, or a
dense ERP table workspace. The surrounding workflow belongs to
`product-ux-design`, the visual expression to `visual-ui-design`, and the
implementation (query hooks, chart code) to `nextjs-module` and
`tailwind-shadcn`.

## Pattern
Every element answers a question that leads to a decision that leads to an
action. Start from the decision, never from chart types: a dashboard nobody
acts on is reporting theater. Dense operational data is organized as headline
outcome → exceptions requiring attention → trends → supporting context →
detailed records — and the most important element is whatever changes the
user's next action, which is often an exception, not the biggest number.

## Workflow
1. **Define the decision.** Who uses it, what they decide, what action follows,
   how often, on what time horizon, the cost of deciding late or wrong, the
   comparison and threshold that make a value meaningful, and how fresh the
   data must be for the decision to be safe.
2. **Classify the dashboard** — strategic, tactical, operational, diagnostic,
   compliance, or exception-focused — and keep one class dominant per screen
   instead of blending them without a hierarchy.
3. **Give every KPI a contract.** Business question, calculation concept, time
   period, comparison, target or threshold, freshness, owner, and the action
   when it goes abnormal. A number with no possible action is a vanity metric —
   reject it. Never invent domain KPIs; unconfirmed ones are labeled
   assumptions for the user to validate.
4. **Choose charts to answer questions.** Change over time — line. Category
   comparison — bar. Composition — stacked bar only while comparison stays
   readable. Exact values and row-level action — table. Relationship — scatter.
   Funnel — only a true staged conversion. Avoid pies where precise comparison
   matters and gauges without a meaningful target range. No decorative charts.
   These selection rules are widely held craft knowledge (the Cleveland/Few/
   Tufte lineage), not clauses of a standard — treat them as strong defaults.
5. **Design operational tables for decisions.** Column order by decision
   importance (never database-field order), numeric columns aligned to the
   number-reading edge (right in LTR — mirror-check under RTL) with tabular
   figures, identifiers and statuses scannable, exceptions surfaced, row and
   bulk actions, sticky headers, totals and subtotals that reconcile with the
   detail, pagination or virtualization (which commits to fixed row heights and
   single-line cells — plan for it), and a mobile-web alternative. When a table
   overwhelms, shrink the data first — split it or cut columns — before
   shrinking the type.
6. **Specify filters and saved views.** Global vs local scope, defaults, date
   periods, tenant/client context, persistence and URL state, reset, sharing —
   and active filters always visible, or users will mistake a filtered view
   for the whole truth.
7. **Make aggregates drillable.** Each high-level value states whether it is
   actionable, where it drills to, which filters carry over, and the return
   path. A count with no route to its records is a dead end.
8. **Surface exceptions deliberately** — blocked work, overdue items,
   anomalies, failed operations, missing data, reconciliation differences,
   permission-limited views — and never rely on red alone to carry them.
9. **Design the data states.** Loading, background refresh, stale, delayed,
   partial, source unavailable, zero, no data, filtered-to-nothing,
   calculation error — with the last-refresh time visible. Zero is a value;
   missing is a problem; an empty filter result is neither. Zones stream in
   independently on this stack — per-zone skeleton treatment is
   `visual-ui-design`'s rule; this skill decides what each zone says while
   its data is absent, stale, or partial.

## Example
```text
# KPI contract + zones — payroll operations dashboard (accounting firm, tenant-scoped)
KPI "clients not yet validated"   question  can we close the month?
                                  calc      clients with unvalidated March payroll
                                  compare   same day last month
                                  threshold >0 two days before close
                                  fresh     minutes · owner  payroll manager
                                  abnormal  drill to the unresolved-clients list, filters kept

zones   1 headline   validated / total clients + closing countdown
        2 exceptions blocked payrolls (missing bank details, contract anomalies) — first!
        3 trend      validation progress vs previous months (line)
        4 detail     per-client table: status · anomalies · net delta vs Feb · [validate]
states  bank-feed source down → zone 2 shows "6 clients unknown — feed unavailable since 09:14"
        (stale badge + last-refresh, never a silent zero)
```

## Validation tests
Every proposal passes: the decision test (each element names its decision),
actionability (abnormal values route to action), metric definition (any two
readers compute the same number), chart-question (each chart answers one),
exception visibility (problems found in five seconds), exact values (available
where operators need them), freshness (staleness is visible), filter context
(scope always visible), and responsive (priorities hold on small screens).

## Adapt to your repo
Rename the example's domain nouns (clients, payroll validation, monthly close),
currency, and thresholds to your product — they are placeholders, not the
pattern. Confirm which metrics the backend can actually compute and how fresh
each source really is — a designed "real-time" tile over an hourly batch is a
lie in production. Respect tenant scoping in every aggregate and saved view
(`multi-tenancy` on the backend, tenant-in-the-key on the frontend via
`react-query`). Aggregation cost is real — dashboards breed unbounded queries,
so validate feasibility with `perf-review`. Number, date, and currency formats
localize per fr/en/ar (`i18n-rtl`).

## Gotchas
- Starting from "which charts?" guarantees a decorative dashboard. The decision
  inventory (step 1) is not skippable.
- Inventing plausible domain KPIs is fabrication. "Standard for payroll ops —
  confirm against your definitions" is the honest framing.
- The biggest number is rarely the most decision-relevant element; blocked and
  overdue work usually beats totals for the next action.
- Zero and missing rendered identically cause real accounting errors — "0
  revenue" and "feed down" must never look the same.
- Red as the only exception channel fails color-blind users and loses meaning
  when overused — pair with icon, label, and position.
- Hidden active filters make users read a filtered view as the whole truth —
  an expensive silent failure with no error message to catch it.
- Totals that do not reconcile with the visible detail (pagination cutoffs,
  timezone windows, filter mismatch) destroy trust in the entire product.
- A drill-down that drops filters strands the user in an unrelated list;
  carry context or do not drill.
- Design-side restraint keeps this skill honest — it decides *what* and *why*;
  query shape and caching stay with `perf-review`, fetching with `react-query`.

## See also
- `product-ux-design`
- `visual-ui-design`
- `design-system`
- `react-query`
- `perf-review`
- `nextjs-module`
- `i18n-rtl`
