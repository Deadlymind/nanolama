---
name: drf-zod-contract
description: Keeps a DRF serializer and its frontend Zod 4 schema and TanStack Query hook in sync across the full-stack type seam — DRF serializer is the source of truth, a typed fetcher runs schema.parse(data), and a contract test fails when they drift. Use when adding or changing a serialized field, wiring a typed fetcher, deriving Zod/TS types from a drf-spectacular OpenAPI schema, mapping DateField or DecimalField to Zod, or debugging a shape mismatch between backend response and frontend parse. Not for building the ViewSet/serializer itself (see drf-api), form-only validation and RHF wiring (see zod-forms), or query caching and invalidation (see react-query).
---

# DRF ↔ Zod contract (the full-stack type seam)

## When to use
Any time a value crosses the API boundary — a serializer emits a field the
frontend parses. The seam drifts silently: someone renames a field, changes
`DecimalField` to a string, or adds a nullable, and the frontend keeps compiling
against a stale shape until it explodes at runtime. Treat the serializer as the
single source of truth and make drift a failing test, not a production surprise.

## Pattern
One direction of truth, one place that parses, one test that guards the seam:

1. **The DRF serializer defines the contract.** The frontend never guesses the
   shape — it mirrors the serializer.
2. **Every response is parsed once, at the fetch boundary**, with `schema.parse(data)`.
   Nothing downstream trusts raw JSON; the Zod schema is the runtime gate and the
   `z.infer` type is what the app sees.
3. **A contract test fails when the two diverge** — either generated from the
   serializer's OpenAPI schema, or a hand-mirror guarded by a paired snapshot test.

## Keeping them in sync — two options
- **Generate (preferred for large surfaces).** Emit an OpenAPI schema with
  `drf-spectacular` (`manage.py spectacular --file schema.yml`), then derive TS/Zod
  from it in CI. The generator is the mirror; a stale checked-in schema fails the build.
- **Hand-mirror (fine for a few endpoints).** Write the Zod schema by hand and add a
  contract test that asserts the serializer's field names equal the schema's keys, so
  adding a serializer field without touching Zod turns CI red.

## Field-by-field mapping
The seam breaks on types, not just names. DRF serializes some fields as strings:

| DRF field | JSON on the wire | Zod 4 |
| --- | --- | --- |
| `CharField` / `TextField` | string | `z.string()` |
| `IntegerField` | number | `z.number().int()` |
| `DecimalField` | **string** ("19.90") | `z.string()` then `z.coerce.number()` to use it |
| `DateField` | "2026-07-16" | `z.iso.date()` |
| `DateTimeField` | ISO 8601 | `z.iso.datetime({ offset: true })` |
| `BooleanField` | boolean | `z.boolean()` |
| nullable / `required=False` | may be `null` / absent | `.nullable()` / `.optional()` |
| `entreprise` (tenant FK) | number (pk) | `z.number().int()` |

## Pattern in code
```ts
// lib/invoice.ts — mirror of InvoiceSerializer; rename `entreprise` to your tenant field
import { z } from 'zod'; // resolves Zod 4

export const InvoiceSchema = z.object({
  id: z.number().int(),
  entreprise: z.number().int(),            // tenant FK, serialized as pk
  reference: z.string(),
  amount: z.string(),                       // DecimalField -> string on the wire
  issued_on: z.iso.date(),                  // DateField
  created_at: z.iso.datetime({ offset: true }), // DateTimeField
  paid: z.boolean(),
  note: z.string().nullable(),              // null=True / required=False
});
export type Invoice = z.infer<typeof InvoiceSchema>;
export const amountOf = (i: Invoice) => z.coerce.number().parse(i.amount);

// typed fetcher — parse once, at the boundary; raw JSON never leaks past here
export async function getInvoice(id: number): Promise<Invoice> {
  const res = await fetch(`/api/invoices/${id}/`, { credentials: 'include' });
  if (!res.ok) throw new Error(`invoice ${id}: ${res.status}`);
  return InvoiceSchema.parse(await res.json()); // throws on drift, not silently wrong
}
```

Feed `getInvoice` straight into a `useQuery` hook (see `react-query`); the hook's
data is typed `Invoice` with zero manual annotation.

## The contract test (hand-mirror guard)
For a hand-mirror, add a Python test that imports the serializer and asserts its field
names equal the Zod schema's keys — e.g. `set(InvoiceSerializer().fields) == set(zod_keys)`,
where `zod_keys` is read from a small `invoice.keys.json` file that a frontend test dumps
from the Zod object's keys, so both sides feed the same list. Adding `discount` to the
serializer then fails CI until the Zod schema gains it too.

## Adapt to your repo
Rename `Invoice`/`InvoiceSerializer`, the `/api/invoices/` path, and the tenant field
(`entreprise` here — rename to yours). Pick one sync strategy per surface: generate
from `drf-spectacular` for broad APIs, hand-mirror for a handful of endpoints — don't
run both for the same type. Confirm your DRF `COERCE_DECIMAL_TO_STRING` setting (default
`True`) so `DecimalField` really is a string; if you set it `False`, use `z.number()`.

## Gotchas
- `DecimalField` is a **string** by default — `z.number()` on it throws. Keep it
  `z.string()` and coerce only where you compute, to preserve precision.
- `z.coerce.number()` turns `""`/`null` into `0`/`NaN` silently — validate the raw
  string first; don't coerce nullable money fields blindly.
- A hand-mirror with no contract test is worse than none — it looks maintained but
  drifts. The failing test is the whole point.
- Zod 4 moved the ISO string-format checks to top-level helpers — use `z.iso.date()` /
  `z.iso.datetime()` (and `z.email()`, `z.url()`), not the now-deprecated
  `z.string().date()` / `z.string().datetime()` method forms carried over from v3.
- Parse at the fetch boundary only. Re-parsing the same object deeper in the tree is
  wasted work and a second place to drift.

## See also
- `drf-api`
- `zod-forms`
- `react-query`
