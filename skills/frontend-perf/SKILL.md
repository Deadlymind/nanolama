---
name: frontend-perf
description: Optimizes Core Web Vitals for the Next.js/React app — LCP (largest contentful paint), INP (interaction to next paint, which replaced FID), and CLS (layout shift) — by measuring bundle weight and field data before changing anything, keeping client JS lean with Server Components and dynamic imports, using the framework image and font primitives, and tuning the data layer with staleTime and Suspense streaming. Use when a page loads slowly, an interaction feels janky, content jumps on load, the JS bundle is too heavy, or a Web Vitals/Lighthouse score needs raising. Not for backend N+1 or SQL query tuning (see perf-review).
---

# Frontend performance (Core Web Vitals on the client)

## When to use
A page on the Next.js/React app is slow, an interaction lags, or the layout
jumps while loading. This skill owns the **client**: what the browser downloads,
parses, renders, and reacts to. If the slowness is a slow API response or an N+1
query, that is server-side work — hand it to `perf-review`.

## Pattern
Optimize the three Core Web Vitals, and **measure before you touch anything**:

1. **LCP** — how fast the largest above-the-fold element paints. Hurt by heavy
   images, render-blocking resources, and slow data.
2. **INP** — how responsive interactions feel (it replaced FID as the responsiveness
   metric). Hurt by too much client JS running on the main thread.
3. **CLS** — how much content jumps after first paint. Hurt by images/fonts/ads
   that arrive without reserved space.

The invariant: **profile first, optimize second.** Guessing wastes effort and
often makes the bundle worse. Get one bundle-weight number and one real-user
number before editing.

## Measure first
Two lenses, both required:

- **Bundle weight (lab).** Run a bundle analyzer on a production build to see
  which chunks and dependencies dominate JS. A single fat dependency in a shared
  chunk usually explains a bad INP. Treat the analyzer as the map of where the
  weight actually is.
- **Field + lab data (real vs synthetic).** Field data is what real users
  experience (the browser's Web Vitals reporting, sent to your analytics);
  lab data is a synthetic run (Lighthouse / a CI Vitals check). Field tells you
  *whether* there's a problem and for whom; lab tells you *why*, reproducibly.
  Optimize what the field flags, verify with the lab, ship, re-check the field.

Only after you have those numbers do you change code.

## Keep client JS lean
Every kilobyte of client JS is main-thread cost that shows up as INP.

- **Default to Server Components; add `"use client"` only at interactive leaves.**
  A component that just renders data has no reason to ship to the browser. Push
  the client boundary as far down the tree as it goes — one small interactive
  button becomes a client leaf, its container stays a Server Component.
- **Code-split heavy client-only pieces with dynamic import.** A charting library,
  a rich editor, or a map that only some users open should not sit in the initial
  bundle. Load it on demand.
- **Use the framework image and font primitives.** The image primitive serves
  sized, lazy, modern-format images and reserves space (protects LCP and CLS);
  the font primitive self-hosts and preloads fonts so text doesn't block or shift
  (protects CLS). Hand-rolled `<img>`/`@font-face` is where layout shift creeps in.

## Tune the data layer
- **Set a sensible `staleTime`** so the app stops refetching data that hasn't
  changed. Chatty refetch-on-every-focus is wasted main-thread and network work;
  pick the window per resource (ties into `react-query`).
- **Stream slow content with Suspense.** Wrap a slow section in a boundary with a
  skeleton so the fast shell paints immediately (good LCP) while the slow part
  streams in — instead of one blank page blocked on the slowest query.

## Example — dynamic-import a heavy client-only widget
```tsx
// Chart pulls in a large plotting lib. Keep it out of the initial bundle:
// load it on demand, only in the browser, with a reserved-height fallback.
import dynamic from "next/dynamic";

const RevenueChart = dynamic(() => import("./RevenueChart"), {
  ssr: false,                              // client-only lib; skip SSR
  loading: () => <div className="h-80" />, // reserve height → no CLS
});

// RevenueChart's code now ships in its own chunk, fetched when this renders —
// not added to the page's initial JS. Rename per widget in your repo.
export function Dashboard() {
  return <RevenueChart />;
}
```

## Adapt to your repo
Confirm your framework's exact image, font, and dynamic-import primitives and
their current option names before copying — APIs drift across major versions;
use `version-check` to pin what your installed version actually supports. Wire the
bundle analyzer into your build the way your toolchain expects, and route field
Web Vitals to whatever analytics you already run. Rename `RevenueChart` and the
`staleTime` windows to your resources.

## Gotchas
- **Don't optimize without a measurement.** A "faster" refactor with no before/after
  number is a guess — and often adds bundle weight instead of removing it.
- **`ssr: false` means the widget is absent until JS runs.** Fine for a below-fold
  chart; wrong for LCP content, which should render on the server.
- **A `dynamic` import with no `loading` fallback height reintroduces CLS** — the
  swap from nothing to a tall widget is exactly the jump you were avoiding.
- **`"use client"` is contagious downward** — everything imported by a client
  component is also client. A stray `"use client"` near the tree root drags the
  whole subtree into the bundle. Keep it at the leaves.
- **A tiny `staleTime` looks correct but refetches constantly** — background
  refetches still cost main-thread time and hurt INP on data-dense screens.
- **Third-party scripts (analytics, chat, ads) are common INP/LCP culprits** and
  won't show in *your* bundle analyzer — audit them separately; defer or lazy-load.

## See also
- `perf-review`
- `nextjs-module`
- `react-query`
