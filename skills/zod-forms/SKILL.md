---
name: zod-forms
description: Defines typed forms with Zod 4 where one z.object schema is the single source of both the TypeScript type and runtime validation, coercing string inputs with z.coerce.number() and resolving error messages through next-intl keys. Use when writing or reviewing a Zod schema, wiring react-hook-form or a Server Action validator, fixing a Select "all" sentinel that fails validation, coercing numeric or date inputs, translating validation messages, or migrating a schema from Zod 3 to Zod 4. Not for DRF-side field validation or the shared client/server contract (see drf-zod-contract), locale message wiring itself (see i18n-rtl), or mutation/query plumbing (see react-query).
---

# Zod forms (schema as single source of truth)

## When to use
Building or reviewing any Next.js form or Server Action input on this stack. Reach
here when you need one schema to produce both the `type` and the runtime check, when
`<input>` string values must become numbers, when a Select's "all" option breaks
validation, or when error messages must be French/English/Arabic, not hardcoded.

## Pattern
One `z.object` is the source of truth: derive the TypeScript type with
`z.infer`, validate with `.safeParse`, and never maintain a parallel `interface`.
HTML inputs are always strings — coerce at the schema edge (`z.coerce.number()`),
don't sprinkle `Number(...)` through handlers. Emit **message keys**, not English
prose, and resolve them via next-intl so the same schema serves all three locales.

## Steps / idioms
1. Import from `zod` (this resolves Zod 4) and let one schema define the type,
   coerce inputs, and model the Select sentinel; validate anywhere with
   `safeParse` and map each issue key through next-intl:

   ```ts
   import { z } from 'zod';

   // "all" is the Select's no-filter sentinel; treat it as "field omitted".
   const ALL = 'all';

   export const invoiceFilterSchema = z.object({
     // <input> gives a string; coerce to a number, keep the message a KEY.
     amountMin: z.coerce.number({ error: 'errors.amount.type' }).positive('errors.amount.positive'),
     // Select sends "all" or a real id — model the sentinel, then normalize it out.
     statusId: z.union([z.literal(ALL), z.coerce.number().int().positive()])
                .transform((v) => (v === ALL ? undefined : v))
                .optional(),
   });

   export type InvoiceFilter = z.infer<typeof invoiceFilterSchema>; // one source of truth

   // Validate anywhere (Server Action included), then localize each issue key.
   const t = useTranslations();                         // from next-intl
   const parsed = invoiceFilterSchema.safeParse(input);
   if (!parsed.success) {
     const messages = parsed.error.issues.map((i) => t(i.message)); // key -> localized string
   }
   ```

2. Wire the same schema to the resolver (`@hookform/resolvers/zod`) or a Server
   Action, then hand `parsed.data` to your mutation (see `react-query`).

## The Select "all" trap
A `<Select>` cannot hold `undefined`, so the "no filter" option needs a real string
value like `"all"`. If the field is a plain `z.coerce.number()`, `"all"` coerces to
`NaN` and validation fails on an untouched form. Model the sentinel explicitly
(`z.union([z.literal('all'), realValue])`) and `.transform()` it to `undefined`, so
downstream code sees a clean optional — never a `NaN` or the literal `"all"`.

## Zod 4 caveats (v3 -> v4)
- Error customization is one unified `error` param: `z.string({ error: 'errors.required' })`.
  The v3 `{ required_error, invalid_type_error }` pair is gone.
- Read issues from `err.issues` (use `z.treeifyError(err)` / `z.flattenError(err)`
  for nested shapes); the old `.format()` shape changed.
- `z.coerce.number()` input type is now `unknown`, so it accepts form strings without
  a cast. Prefer it over `z.preprocess(Number, ...)`.
- Email is `z.email()` (top-level); `z.string().email()` is deprecated in v4.

## Adapt to your repo
Rename `invoiceFilterSchema`/`Entreprise` domain names to yours and confirm your
message-key namespace matches your next-intl catalog (`errors.*` here). Pick your
sentinel constant (`"all"`, `""`) and keep it in one place. Verify `import { z }`
resolves v4 in `package.json` (`"zod": "^4"`), not a stale v3.

## Gotchas
- A hardcoded English string in a schema message bypasses i18n — always pass a key
  that exists in every locale catalog (fr/en/ar), then translate at the boundary.
- `z.coerce.number()` turns `""` into `0`, not an error — guard required numerics
  with `.min()`/`.positive()` or a preceding non-empty check.
- Deriving a hand-written `interface` alongside the schema lets them drift; always
  `z.infer` instead.
- Server Actions must re-validate with the same schema — client validation is UX, not
  a trust boundary (the DRF layer validates again; see `drf-zod-contract`).

## See also
- `drf-zod-contract`
- `i18n-rtl`
- `react-query`
