---
name: tailwind-shadcn
description: Implements the design system on a Next.js 16 frontend — Tailwind v4 CSS-first theming with @theme and OKLCH CSS variables, semantic surface/-foreground token pairs, light plus .dark sets, and shared shadcn/ui components extended via cva. Use when implementing an approved screen or component, adding or restyling a component, turning token roles into @theme CSS variables, wiring dark mode, coding a button/badge variant, or asking how theming works here. Not for deciding which tokens, component variants and patterns should exist — the system's definition and governance (see design-system), page/route structure or data fetching (see nextjs-module), or RTL and logical-property direction handling (see i18n-rtl).
---

# Tailwind + shadcn/ui (implementing the design system)

## When to use
Styling anything on the frontend: adding a component, restyling one, coding a
color or spacing token, wiring dark mode, or adding a variant. The rule of thumb —
reach for a token and a shared component before writing raw CSS or a new one-off.
Which roles, variants, and patterns should exist is decided upstream in
`design-system`; this skill turns those decisions into working code.

## Pattern
Two invariants:

1. **Colors and spacing are tokens, never raw values.** Define them once as OKLCH
   CSS variables in `@theme`, in semantic `surface` / `surface-foreground` pairs, with
   a light set on `:root` and a dark override on `.dark`. No hex, no `hsl()`, no
   `tailwind.config.js` color map — Tailwind v4 is CSS-first.
2. **Reuse the shared shadcn component; extend it with `cva`.** Add a variant to the
   existing component instead of forking a new one, so every button/badge stays in sync.

Declare tokens CSS-first in your global stylesheet — semantic names, OKLCH, each
paired with a `-foreground`; the `.dark` block overrides the same names:

```css
/* app/globals.css */
@import "tailwindcss";
@theme {
  --color-surface: oklch(1 0 0);              /* page background */
  --color-surface-foreground: oklch(0.21 0.01 285);
  --color-primary: oklch(0.62 0.19 259);      /* brand */
  --color-primary-foreground: oklch(0.98 0 0);
  --radius-lg: 0.5rem;
}
.dark {
  --color-surface: oklch(0.21 0.01 285);      /* same names, dark values */
  --color-surface-foreground: oklch(0.98 0 0);
}
```

These generate utilities automatically — `bg-surface`, `text-surface-foreground`,
`bg-primary`, `rounded-lg`. Toggle dark mode by putting `.dark` on `<html>`.

Extend the shared shadcn component with `cva` rather than forking one: define a
`cva(base, { variants, defaultVariants })` map keyed on token utilities only
(e.g. `bg-primary text-primary-foreground` for a variant, `h-8 px-3` for a size),
export its `VariantProps` as the component's prop type, and consume it in markup with
`className={button({ variant: "ghost" })}`. Never inline a hex or a magic `px` value.

## Adapt to your repo
Rename the semantic tokens to your palette (`surface`, `primary`, `accent`, `muted`,
`destructive`, `border`) and pick real OKLCH values — keep the `-foreground` pairing and
the light/`.dark` split. Confirm your `globals.css` uses `@import "tailwindcss"` and
`@theme` (v4), not a legacy `tailwind.config.js` `theme.extend.colors`. If shadcn's CLI
scaffolded HSL variables, migrate them to OKLCH once, centrally.

## Gotchas
- No hardcoded hex/`rgb`/`hsl` in components and no arbitrary `bg-[#...]` — that value
  can't follow the theme into dark mode. Only tokens flip.
- A color used without a matching `-foreground` fails contrast in one mode — always
  define and use the pair.
- Don't reintroduce `tailwind.config.js` colors alongside `@theme`; pick CSS-first and
  keep tokens in one place, or the two drift.
- Extend the shared component; a forked `MyButton` skips future token/a11y fixes.
- Use logical utilities (`ms-`, `me-`, `ps-`, `pe-`) not `ml-`/`pl-` so RTL works
  (see `i18n-rtl`).

## See also
- `design-system`
- `nextjs-module`
- `i18n-rtl`
