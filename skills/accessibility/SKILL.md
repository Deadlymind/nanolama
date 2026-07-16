---
name: accessibility
description: Builds WCAG 2.2 AA accessible React UI on shadcn/Radix primitives — keyboard operability with a visible focus ring, dialog focus trap and restore, labelled form fields wired to aria-describedby errors, token-based color contrast, and Arabic RTL mirroring. Use when adding or reviewing an interactive component, an icon-only button, a dialog or menu, a form field's error wiring, or a keyboard/focus/contrast/screen-reader fix, and when making a screen work in RTL. Not for translation plumbing or bidi text setup (see i18n-rtl) or design-token definition (see tailwind-shadcn).
---

# Accessibility (WCAG 2.2 AA on React + Radix)

## When to use
Building or reviewing any interactive UI on this stack — a button, dialog, menu,
form field, or a whole screen — that a keyboard or screen-reader user must be able
to operate. Treat a control that only works with a mouse as a bug, not a polish
item. Target **WCAG 2.2 AA** as the bar.

## Pattern
Reach for an accessible **primitive** before you hand-build behavior. A Radix/shadcn
`Button`, `Dialog`, `DropdownMenu`, or `Tabs` ships the correct role, focus
management, and keyboard handling for free; a `<div onClick>` ships none of it and
you will re-implement them wrong. The invariant: everything is operable by keyboard
with a **visible focus ring**, every control has an **accessible name**, and state
(errors, expansion, selection) is exposed to assistive tech, not just painted.

## Idioms
1. **Never `div`-with-onClick for a control.** A clickable div has no role, is not
   in the tab order, and ignores Enter/Space. Use the primitive (`Button`, a Radix
   trigger) so screen readers announce it and keyboards reach it.
2. **Keyboard first, visibly.** Every action reachable by Tab; never remove the
   focus outline without replacing it. Style `:focus-visible` (not `:focus`) so a
   mouse click does not flash a ring but a Tab does.
3. **Trap and restore focus in overlays.** A dialog/menu keeps Tab inside it while
   open, closes on Escape, and returns focus to the element that opened it. Radix
   `Dialog` does this — do not fight it with manual `focus()` calls.
4. **Name every control.** Icon-only buttons need an `aria-label` (or visually
   hidden text); an unlabelled icon button is silence to a screen reader.
5. **Wire form errors.** Associate each field with its `<label>`, and point
   `aria-describedby` at the error node with `aria-invalid` on the input, so the
   error is announced when focus lands (ties `zod-forms`).
6. **Contrast from tokens.** Meet 4.5:1 body / 3:1 large-text and UI contrast using
   semantic design tokens, not ad-hoc hex — one accessible palette, applied
   everywhere (ties `tailwind-shadcn`).

## Example
```tsx
// Icon-only button: a screen reader announces "Delete invoice", not "button".
<Button variant="ghost" size="icon" aria-label="Delete invoice">
  <TrashIcon aria-hidden="true" />   {/* decorative: hidden from AT */}
</Button>

// Dialog: Radix traps focus while open, restores it to the trigger on close,
// and closes on Escape. Title/description are wired to the dialog by id.
<Dialog>
  <DialogTrigger asChild>
    <Button>Delete</Button>
  </DialogTrigger>
  <DialogContent>            {/* focus moves in; Tab is trapped here */}
    <DialogTitle>Delete this invoice?</DialogTitle>
    <DialogDescription>This cannot be undone.</DialogDescription>
    <DialogClose asChild><Button variant="outline">Cancel</Button></DialogClose>
  </DialogContent>
</Dialog>
```

## RTL
For Arabic, the whole layout mirrors. Use CSS **logical properties**
(`margin-inline-start`, `padding-inline-end`, `inset-inline`) instead of
left/right so spacing flips automatically, and let icons/arrows that imply
direction mirror too. Reading order and focus/Tab order must follow the visual
order in both directions — set `dir="rtl"` on the container and verify Tab walks
the mirrored layout sensibly (ties `i18n-rtl`).

## Verify
Automated checkers catch only part of the picture — roughly what is machine-testable
(missing labels, contrast ratios, bad ARIA), not whether focus order makes sense or
a flow is usable. Flow- and layout-level WCAG 2.2 criteria (target size, focus not
obscured, redundant entry, consistent help, dragging alternatives) are baked in at
design time by `product-ux-design` and `visual-ui-design`; this audit verifies they
survived implementation. Run all three passes:
- an **axe-style** automated scan in CI on rendered pages,
- a **keyboard-only** pass (unplug the mouse: Tab, Enter, Space, Escape, arrows),
- a **screen-reader** pass (VoiceOver/NVDA) on the primary flow.

## Adapt to your repo
Confirm which primitive library you actually use (Radix under shadcn here; Headless
UI and others give the same guarantees differently) and that its focus-trap default
is on. Point contrast checks at your own token names. Version-pin nothing from this
skill — confirm the current release of any axe-style checker or testing library
through `version-check`.

## Gotchas
- `aria-label` on a `<div>` does nothing useful without a role — that is why the
  primitive matters; do not paper over a wrong element with ARIA.
- Removing the focus outline for looks is a WCAG failure; replace it, never delete it.
- `placeholder` is not a label — it vanishes on input and is often skipped by AT.
- `display:none` and `aria-hidden` remove content from the accessibility tree;
  a "visually hidden" utility (clipped, not hidden) is what keeps label text for AT.
- RTL breaks when you hard-code `left`/`right` or `margin-left`; logical properties
  are what let one component serve both directions.
- A passing axe scan is a floor, not a pass — it cannot judge focus order or whether
  a custom widget is actually operable.

## See also
- `zod-forms`
- `tailwind-shadcn`
- `i18n-rtl`
- `nextjs-module`
