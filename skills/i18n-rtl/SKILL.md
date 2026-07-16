---
name: i18n-rtl
description: Internationalizes a Next.js 16 App Router app with next-intl for fr/en/ar — every user string via t() and present in all three message files, locale routing, and Arabic RTL that mirrors via dir="rtl" plus logical Tailwind classes (ms-/me-, ps-/pe-, text-start) instead of physical left/right. Use when adding a translated string, wiring next-intl routing/middleware, fixing hardcoded text, making a layout mirror for Arabic, or converting ml-/mr-/text-left to logical properties. Not for Zod form schemas and field messages (see zod-forms) or the Tailwind theme and shadcn setup itself (see tailwind-shadcn).
---

# i18n and Arabic RTL (next-intl, logical CSS)

## When to use
Adding or reviewing any user-facing string, wiring locale routing, or making a
layout mirror correctly for Arabic. On this stack every visible string is
translated in **all three** locales (fr, en, ar) and every direction-sensitive
style is written in **logical** properties so `dir="rtl"` flips it for free.

## Pattern
Two invariants, held everywhere:

1. **No hardcoded user text.** Every visible string comes from `t()` and exists as
   a key in `messages/fr.json`, `messages/en.json`, and `messages/ar.json`. A key
   present in one file but missing in another is a bug (blank UI or a raw key leak).
2. **Direction is data, not layout.** Set `dir` from the locale on `<html>`; write
   spacing/alignment with logical classes (`ms-`, `me-`, `ps-`, `pe-`, `text-start`,
   `text-end`) so the same markup mirrors for `ar` without RTL-specific CSS.

Route by locale, set `dir` once in the root layout, and read every string via `t()`:

```tsx
// app/[locale]/layout.tsx — route by locale, set dir once, provide messages
import { NextIntlClientProvider, hasLocale } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';

export default async function LocaleLayout(
  { children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> },
) {
  const { locale } = await params;                 // Next 16 params are async
  if (!hasLocale(routing.locales, locale)) notFound();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';     // direction is data, not layout
  const messages = await getMessages();
  return (
    <html lang={locale} dir={dir}>
      <body>
        <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}

// In components: strings via t(), spacing via LOGICAL classes so ar mirrors for free.
// const t = useTranslations('invoices');   // key must exist in fr.json, en.json, ar.json
// <span className="ms-2 me-4 text-start ps-3">{t('label')}</span>   // not ml-/mr-/text-left
```

## Adapt to your repo
Rename the `invoices` namespace and message keys to your domain. Confirm your locale
set (`routing.locales` in `i18n/routing.ts`) and `defaultLocale`, and that the
`[locale]` segment plus the next-intl `middleware.ts` matcher are wired. Add a
CI/lint step that diffs the key sets of `fr/en/ar.json` so a missing translation
fails the build rather than shipping a blank string.

## Gotchas
- A key in `fr.json` but missing in `ar.json` renders the raw key or empty text —
  keep the three files in lockstep; don't let one drift.
- `ml-`/`mr-`/`left-`/`right-`/`text-left` do **not** flip under `dir="rtl"`; use the
  logical `ms-`/`me-`/`ps-`/`pe-`/`text-start`/`text-end` (Tailwind v4 maps these to
  CSS logical properties). See `tailwind-shadcn`.
- Set `dir` on `<html>` from the locale, not per-component; icons/chevrons that must
  point a fixed way get an explicit `rtl:rotate-180` or a physical override.
- Translate the tenant label too — "Entreprise" is the portable example; rename it and
  its message keys to your own tenant noun.
- `useTranslations` runs in client components; use `getTranslations` in server
  components/route handlers — don't mix them up.

## See also
- `tailwind-shadcn`
- `zod-forms`
- `nextjs-module`
