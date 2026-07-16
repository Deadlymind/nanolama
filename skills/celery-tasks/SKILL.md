---
name: celery-tasks
description: Hardens Celery 5.6.3 background jobs on Redis broker/result backend — @shared_task with soft/hard time limits, autoretry_for + retry_backoff + max_retries, pass IDs not ORM objects (re-fetch tenant-scoped inside the task), idempotency guards against double-delivery, and beat schedules that carry explicit entreprise_id. Use when writing or reviewing a Celery task, wiring autoretry or time limits, fixing a task that mutated a stale object or ran twice, adding a periodic beat job, or asking how background jobs stay tenant-scoped here. Not for real-time push over a consumer (see websockets-channels), row-locking inside a task (see db-concurrency), or worker deployment on Elastic Beanstalk (see deploy-aws).
---

# Celery tasks (hardened, tenant-scoped background jobs)

## When to use
Moving work off the request cycle — OCR extraction, emails, report builds, third-party
calls — with Celery 5.6.3 workers on a Redis broker and Redis result backend. A task
runs in a different process, later, and possibly twice; treat every task as if the
message could be redelivered and the objects it touches could have changed.

## Pattern
Four rules, held on every task:

1. **Pass IDs, never ORM objects.** Serializing a model pickles a stale snapshot. Pass
   the pk plus `entreprise_id`, then re-fetch tenant-scoped inside the task.
2. **Bound every task** with `soft_time_limit` (raises `SoftTimeLimitExceeded` you can
   catch) and a hard `time_limit` that kills the worker as a backstop.
3. **Retry transient failures only** with `autoretry_for` + `retry_backoff` + a finite
   `max_retries`; never blanket-retry a bug.
4. **Make it idempotent.** At-least-once delivery means the body must be safe to run
   twice — *claim* the work atomically (`select_for_update` plus a conditional state
   transition, a conditional `UPDATE ... WHERE not_yet_done`, or a `unique` execution row)
   before the side effect. A bare read-then-check status flag is not a guard: two workers
   both read "not sent" and both deliver. For external calls, also pass a provider
   idempotency key — a DB rollback cannot un-send an HTTP request.

## Steps / idioms
```python
# billing/tasks.py
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.utils import timezone
from billing.models import Invoice

@shared_task(
    bind=True,
    autoretry_for=(ConnectionError,),   # transient only — not ValueError/DoesNotExist
    retry_backoff=True,                 # 1s, 2s, 4s… exponential
    retry_backoff_max=300,
    retry_jitter=True,                  # randomize the delay — no lockstep herd
    max_retries=5,
    soft_time_limit=25,                 # SoftTimeLimitExceeded fires here
    time_limit=30,                      # SIGKILL backstop
    acks_late=True,                     # re-queue if the worker dies mid-run
)
def send_invoice(self, invoice_id, entreprise_id):
    # Atomically CLAIM the work: lock the row, re-check the state under the lock, and
    # transition it. A read-then-act `if invoice.sent_at` is NOT idempotency — two
    # workers both read "not sent" and both deliver.
    with transaction.atomic():
        invoice = (
            Invoice.objects.select_for_update()      # re-fetch tenant-scoped + locked
            .get(pk=invoice_id, entreprise_id=entreprise_id)
        )
        if invoice.sent_at:                          # someone else claimed it
            return "already-sent"
        invoice.sent_at = timezone.now()             # conditional transition = the claim
        invoice.save(update_fields=["sent_at"])
    try:
        # Provider idempotency key: a DB rollback cannot un-send a completed HTTP call,
        # so the *provider* must dedupe on a stable key derived from the row.
        invoice.deliver(idempotency_key=f"invoice-{invoice_id}-send")
    except SoftTimeLimitExceeded:
        invoice.mark_stalled()          # clean up before the hard kill
        raise
    except ConnectionError:
        Invoice.objects.filter(pk=invoice_id, entreprise_id=entreprise_id).update(
            sent_at=None                # release the claim; the retry re-claims it
        )
        raise

# Enqueue with plain IDs, resolving the tenant server-side:
# send_invoice.delay(invoice.pk, request.user.entreprise_id)

# settings.py — beat still passes the tenant explicitly (fan out per tenant,
# never query "all rows globally" inside one task):
CELERY_BEAT_SCHEDULE = {
    "sweep-overdue": {
        "task": "billing.tasks.sweep_overdue",
        "schedule": 3600.0,             # every hour; or a crontab(...) object
        "kwargs": {"entreprise_id": 1},
    },
}
```

## Resumable backfills / bulk jobs
A one-shot task that loads every row of a large tenant's table into memory, then dies at
80%, restarts from zero and re-does the work it already finished. Make big backfills and
imports resumable instead:

- **Chunk by a stable key range.** Walk `id` ranges (`id > last_id`, ordered, `LIMIT n`)
  rather than `OFFSET` paging — offsets drift as rows change and re-scan earlier pages.
- **Persist a checkpoint after each chunk.** Save the last processed `id` (cursor) to a
  small progress row or Redis key, so a re-run reads the checkpoint and continues from
  there, not from the start.
- **Make each chunk idempotent.** A re-run of an already-done chunk must be a no-op — guard
  each row with a status flag or `update_or_create`/`ON CONFLICT` upsert so redelivery or a
  restart skips finished work.
- **Bound memory.** Stream with `.values_list(..., flat=True)` or `.iterator(chunk_size=…)`
  instead of materializing the full queryset; process one bounded chunk per pass.
- **Record partial failure.** On a chunk error, log the failing range and re-raise so the
  task retries from the last good checkpoint — total rows done / failed makes progress
  observable and the job resumable rather than all-or-nothing.

Dispatch one chunk per task (each re-enqueues the next range) or loop chunks inside a single
long task that re-checkpoints between them. When the backfill accompanies a schema change
(new column, backfilled default), keep the data backfill *out* of the migration and run it
as this kind of resumable task — see `migrations` for the schema-change side.

## Adapt to your repo
Rename `entreprise_id`, `Invoice`, and the app label to match your project. Confirm the
task is loaded via autodiscovery (`app.autodiscover_tasks()`) so `@shared_task` registers.
Tune `soft_time_limit`/`time_limit` to the slowest legitimate run, and pick an idempotency
key that fits the work (a `unique` dedupe row or a Redis `SETNX` lock; a status column only
works when you flip it with a lock or a conditional UPDATE, not an if-check).
For multi-tenant beat jobs, iterate your `Entreprise` rows and dispatch one subtask per
tenant instead of scheduling a single global sweep.

## Gotchas
- `autoretry_for=(Exception,)` retries real bugs 5 times before failing — list only
  transient exception types (network, lock, rate-limit).
- No `soft_time_limit` means a hung external call pins a worker forever; always set both.
- `retry_backoff` alone still retries a whole failed batch in lockstep — every message
  waits the same 1s, 2s, 4s… and re-hammers the recovering dependency simultaneously.
  Add `retry_jitter=True` so each retry picks a randomized delay and the herd spreads out.
- Workers run outside the web request/response cycle, so the automatic per-request
  connection close never fires; idle DB connections pile up until the database refuses new
  ones. Connect `django.db.close_old_connections` to the `task_prerun`/`task_postrun`
  signals (and to beat startup) in your Celery config so each task cleans up its own.
- `acks_late=True` gives at-least-once delivery, so the idempotency guard is mandatory,
  not optional — without it a redelivered message double-charges or double-sends. The guard
  has to be an atomic *claim*, not a status check: `if invoice.sent_at: return` reads outside
  any lock, so two concurrent workers both see "not sent" and both send. And once the external
  call completes it cannot be undone by rolling back the transaction around it — pass a
  provider idempotency key so the far side dedupes the second attempt.
- Passing an ORM object serializes a stale copy and silently overwrites concurrent edits;
  re-fetch by id, and take a row lock if you mutate under contention (see `db-concurrency`).
- A task that skips `entreprise_id` and filters nothing can leak or mutate across tenants —
  scope the re-fetch exactly like a ViewSet would.
- Redis is the broker *and* result backend here; a huge return value bloats Redis — return
  a small id/status, not the payload.

## See also
- `migrations`
- `db-concurrency`
- `websockets-channels`
- `deploy-aws`
