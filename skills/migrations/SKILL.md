---
name: migrations
description: Writes safe schema and data migrations for Django 5.2 on PostgreSQL — data backfills via RunPython with apps.get_model, reversible operations, tenant-aware per-entreprise batching, expand-contract column renames, and concurrent index creation. Use when adding or reviewing a migration, backfilling a column, renaming or dropping a field without downtime, wiring makemigrations --check into CI, or asking how to migrate safely here. Not for the model/ViewSet change that triggers the migration (see multi-tenancy) or lock/transaction concurrency at request time (see db-concurrency).
---

# Migrations (safe schema and data change on PostgreSQL)

## When to use
Any time a change produces a new migration — a new column, a data backfill, a
rename, a drop, or an index. On PostgreSQL a careless migration takes an
`ACCESS EXCLUSIVE` lock or rewrites a large table, so treat "does this block
writes in prod?" as a review question, not an afterthought.

## Pattern
Two invariants hold everywhere:

1. **Data migrations are reversible and idempotent.** Every `RunPython` gets a
   real reverse callable (or `RunPython.noop`), and re-running it is a no-op —
   never assume it runs exactly once on clean state.
2. **Schema changes that lock or rewrite are split (expand-contract).** Add the
   new shape, backfill, switch reads/writes, then drop the old shape in a later
   deploy — so no single migration takes a long exclusive lock.

Tenant data lives under `entreprise`, so backfills iterate per tenant in batches
rather than loading one giant queryset.

## Steps / idioms

1. **Never import models at module top level in a data migration.** Use the
   historical model via `apps.get_model`, give a reverse, and make it idempotent:

   ```python
   from django.db import migrations

   def backfill_slug(apps, schema_editor):
       Invoice = apps.get_model("billing", "Invoice")  # historical model, not the import
       # tenant-aware: iterate per entreprise, batch to bound memory + lock time
       for ent_id in Invoice.objects.values_list("entreprise_id", flat=True).distinct():
           qs = Invoice.objects.filter(entreprise_id=ent_id, slug="")  # idempotent: only unset rows
           for inv in qs.iterator(chunk_size=500):
               inv.slug = f"inv-{inv.pk}"
               inv.save(update_fields=["slug"])

   def unset_slug(apps, schema_editor):
       Invoice = apps.get_model("billing", "Invoice")
       Invoice.objects.update(slug="")  # real reverse, not a guess

   class Migration(migrations.Migration):
       dependencies = [("billing", "0007_invoice_slug")]
       operations = [migrations.RunPython(backfill_slug, unset_slug)]
   ```

2. **Split schema from data.** One migration adds the nullable/blank column; a
   separate `RunPython` backfills; a later migration adds `NOT NULL`/constraints.
   Mixing DDL and a long data loop in one migration holds the lock the whole time.

3. **Add indexes concurrently** on hot tables so writes are not blocked. Use
   `AddIndexConcurrently` (from `django.contrib.postgres.operations`) and set
   `atomic = False` on the `Migration` — `CREATE INDEX CONCURRENTLY` cannot run
   inside a transaction. Pass the model name, not the app label.

## Expand-contract (zero-downtime rename)
A single `RenameField` rewrites nothing but breaks any running old code mid-deploy.
Split across releases instead:

1. **Expand** — add the new column; dual-write to both old and new in app code.
2. **Backfill** — `RunPython` copies old to new per entreprise, in batches.
3. **Switch** — ship code that reads/writes only the new column.
4. **Contract** — a later migration drops the old column, once no code references it.

Each step is independently deployable and reversible. Never collapse them.

## Adapt to your repo
Rename `entreprise`/`Invoice`/`billing` and the app label to match your project.
Confirm whether your table is large enough to need `atomic = False` + concurrent
indexes (small tables are fine with a plain `AddIndex`). Pick `chunk_size` to fit
your row width. If a backfill is huge, run it as an idempotent management command
or `celery-task` and keep the migration to schema only.

## Gotchas
- Importing the app model directly (`from billing.models import Invoice`) breaks
  when the migration replays against old state — always `apps.get_model`.
- A `RunPython` with no reverse blocks `migrate` from rolling back; pass
  `RunPython.noop` when the change genuinely cannot be undone.
- `CREATE INDEX CONCURRENTLY` fails inside a transaction — it needs `atomic = False`,
  and a failed concurrent index leaves an `INVALID` index you must drop by hand.
- Adding a `NOT NULL` column with a default on a big table rewrites it under a lock;
  add nullable, backfill, then set `NOT NULL` in a follow-up.
- Run `python manage.py makemigrations --check --dry-run` in CI so a model change
  that forgot its migration fails the build (see `ci-cd`).

## See also
- `multi-tenancy`
- `db-concurrency`
- `ci-cd`
