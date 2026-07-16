---
name: product-ux-design
description: Designs the end-to-end user experience of a complex B2B SaaS or ERP feature — users and roles, jobs, task flows with failure and recovery branches, information architecture, navigation, screen inventory, progressive disclosure, and testable UX acceptance criteria. Use when defining or redesigning a module, business workflow, approval flow, onboarding journey, multi-step process, or navigation structure, planning UX research or usability tests, or asking how a feature should work from beginning to end. Not for visual styling and screen composition (see visual-ui-design), KPI and dashboard data organization (see dashboard-data-design), reusable component-system governance (see design-system), frontend implementation architecture (see nextjs-module), or formal accessibility auditing (see accessibility).
---

# Product UX design (how the feature works, end to end)

## When to use
Defining or redesigning how a feature works for the people who use it — an ERP
module, an approval flow, a payroll validation run, a document workflow — before
anyone draws screens or writes code. When "improve the UX" arrives without
context, ask whether the problem is workflow (here), visual expression, data
organization, or cross-module consistency before picking an owner.

## Pattern
Design the job before the screens, and the failure paths with the happy path.
Every workflow gets mapped end to end —

```text
entry → orientation → input/search → review → decision → action → confirmation → feedback → next step
```

— with the non-ideal branches (first-time use, returning user, empty data,
invalid input, permission denied, rejected approval, partial success, timeout
or system failure, cancellation, background processing, destructive action,
recovery) designed at the same time, not discovered in QA. In operational software the cost of a
workflow is `frequency × friction × consequence of error`, so daily tasks get
the deepest design and rare admin paths get the cheapest safe one.

## Workflow
1. **Frame the problem before screens.** Primary and secondary users, role and
   permissions, business objective, task frequency, trigger, definition of
   success, consequence of error, required information, dependencies, hand-offs,
   approval rules, device and context, language and RTL needs.
2. **Keep the evidence honest.** Separate confirmed facts, reasonable
   assumptions, unresolved questions, and research needs — and never invent
   interview findings, user quotations, analytics, survey numbers, or usability
   results. Plan research instead (interview questions, usability-test tasks,
   hypotheses, participant types) and synthesize only findings the user supplies.
3. **Define the job.** The user's job and desired outcome, the business outcome,
   risks, urgency, and which decisions are irreversible once made.
4. **Map the task flow** with the branches from Pattern — one flow per job, each
   branch ending in either recovery or an explicit dead end the user understands.
   In multi-step flows, never make the user re-enter what the process already
   knows (WCAG 2.2 SC 3.3.7), and put a review step with change links before any
   irreversible submission.
5. **Shape the information architecture.** Global and module placement,
   navigation and sub-navigation, breadcrumbs, page hierarchy, content grouping,
   contextual help, history and audit visibility. Help entry points sit in the
   same place on every page (WCAG 2.2 SC 3.2.6). Model the user's mental model —
   an accountant thinks "monthly closing", not "seven tables with foreign keys".
6. **Inventory every screen.** Purpose, the user question it answers, primary
   action, secondary and destructive actions, required information, entry point,
   exit point, important states. Give each screen one dominant purpose and one
   clearly dominant action where the workflow allows it; when multiple
   legitimate decisions exist (approve vs return for correction), rank and
   differentiate them rather than presenting equals.
7. **Stage disclosure.** Immediately visible → frequent → advanced → conditional
   → hidden until requested → confirmed before executing. Approval and deletion
   sit at the confirmed end; everyday entry sits at the visible end.
8. **Write acceptance criteria as behavior, not adjectives** — then hand off.

## Example
```text
# Task flow — monthly payroll validation (accountant role), failure branches designed in
entry         payroll module → "March — awaiting validation" per-client status list
orientation   totals vs last month; exceptions pinned first (hires, exits, absences)
input/search  filter to unresolved clients only
review        per-client gross→net breakdown, anomaly flags, prior-month delta
decision      validate | send back with a required reason (reason lands in the audit trail)
action        "Validate 12 remaining" — bulk, per-client failure isolation
confirmation  47 validated, 1 failed (missing bank details) — the failure names its fix
feedback      status chips update; the failed client stays in the unresolved filter
next step     export accounting entries | notify clients — offered, never automatic

branches      permission denied → read-only view; validation controls absent, not greyed mysteries
              timeout on submit → entered corrections preserved; retry offered; job continues async
              already validated by a colleague → conflict notice, no double-post
```

## Acceptance criteria and hand-off
Criteria are testable behavior: the user can always identify the next required
action; a user without the permission cannot reach the approve action; a failed
submit preserves entered data; cross-tenant context is never visible; a
long-running operation stays visible while it runs; a destructive action states
its impact and is either recoverable or explicitly confirmed. The deliverable —
objective, users and roles, facts vs assumptions, jobs, task flows, IA, screen
inventory, state and recovery model, research questions, criteria, open risks —
hands off down the chain. Data-heavy screens go to `dashboard-data-design`,
screen design to `visual-ui-design`, shared standards to `design-system`,
implementation to `nextjs-module`, journeys worth a browser test to
`browser-e2e-testing`, and flows crossing a trust boundary to `threat-modeling`.

## Adapt to your repo
Rename the roles, modules, and tenant noun to your product (the "client" above
may be an entreprise, legal entity, or employer). Confirm the real permission
codenames with the backend (`rbac-permissions`) instead of assuming roles exist.
Confirm the locale set — fr/en/ar with Arabic RTL is the house default
(`i18n-rtl`) — because flow length changes when labels double in width. Check
which states the API can actually distinguish (e.g. permission denied vs empty)
before promising them in the flow. On this stack a production server error
reaches the UI as a generic message plus a reference id, never the raw detail —
write failure copy as what-happened + reference + next step (`nextjs-module`).

## Gotchas
- Starting from screens produces database-shaped UI. Mirroring tables into pages
  is a classic ERP failure mode — frame the job first (step 1), always.
- Fabricated evidence is the one failure this skill treats as disqualifying. A
  persona, quote, or metric that was never gathered poisons every downstream
  decision with false confidence; an explicit "assumption — unvalidated" label
  is strictly more useful.
- Happy-path-only design ships the permission-denied, empty, rejected, and
  recovery paths as production surprises. Budget them into the first design.
- An approval flow without the rejected → revise → resubmit loop is half a flow;
  rejection is a normal state in finance and HR, not an error.
- "Intuitive", "seamless", "modern" are not acceptance criteria. If a criterion
  cannot fail a review, it is decoration.
- Deep-designing a quarterly admin path while the 200-times-a-day entry path
  keeps three avoidable clicks inverts the frequency rule in Pattern.
- Design workflow-level error *prevention* (defaults, constraints, confirmation
  for the irreversible), not just error messages after the fact. On failure,
  keep every field as the user entered it, and validate at the least disruptive
  moment that still prevents costly correction — immediately for impossible
  input, after field completion for useful local feedback, on submit for the
  complete business rule. Avoid noisy validation on every blur.
- Any flow operated by dragging (kanban moves, reordering, file drop) needs a
  designed single-pointer alternative (WCAG 2.2 SC 2.5.7) — a flow decision,
  not an audit retrofit.

## See also
- `visual-ui-design`
- `dashboard-data-design`
- `design-system`
- `nextjs-module`
- `rbac-permissions`
- `browser-e2e-testing`
- `threat-modeling`
- `accessibility`
