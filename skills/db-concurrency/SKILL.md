---
name: db-concurrency
description: Keeps money and counter writes correct under concurrent access on Django 5.2 / PostgreSQL — transaction.atomic plus select_for_update to lock the row, F() expressions for read-modify-write counters, and Decimal with quantize for money. Use when writing a debit/credit or balance update, an inventory/stock decrement, a "spent count" or quota counter, a Celery task that mutates shared rows, or when fixing a lost-update, oversell, or race-condition bug. Not for schema changes and adding constraints (see migrations) or async task orchestration itself (see celery-tasks).
---

# DB concurrency (money & counters under concurrent writes)

## When to use
Any write that reads a value, computes a new one, and writes it back — balances,
stock, quotas, "used" counters — where two requests or workers can run at once.
Without a lock the second write silently overwrites the first (lost update); with
money, a float or an un-revalidated check turns that into a wrong ledger.

## Pattern
Four rules, held together:

1. **Lock the row.** Wrap the read-modify-write in `transaction.atomic()` and select
   the row with `select_for_update()` — Postgres holds a row lock until commit, so
   concurrent writers queue instead of racing.
2. **Validate inside the lock.** Re-check the invariant (sufficient balance, stock >= 0)
   *after* acquiring the lock, on the freshly-read value — a check before the lock is
   already stale.
3. **Decimal, never float, for money.** Compute in `Decimal` and `quantize()` to a fixed
   scale; float rounding corrupts ledgers.
4. **Keep the transaction short.** No network/AI/HTTP calls, no `time.sleep`, no email
   inside the lock — hold it only for the read, check, and write.

For a pure integer counter with no cross-value invariant, an `F()` expression does the
increment atomically in the database without a lock at all.

## Pattern — worked example

```python
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

def debit_account(account_id, amount: Decimal, entreprise):
    if not amount.is_finite() or amount <= 0:           # reject NaN/Inf and non-positive input:
        raise ValidationError("Amount must be a positive number")  # a negative debit CREDITS
    amount = amount.quantize(Decimal("0.01"))          # money = Decimal, fixed scale
    if amount <= 0:                                     # e.g. 0.004 rounds to 0.00
        raise ValidationError("Amount rounds to zero at the currency scale")
    with transaction.atomic():                          # one short, committed unit
        account = (
            Account.objects
            .select_for_update()                        # row lock until commit
            .get(pk=account_id, entreprise=entreprise)  # stay tenant-scoped
        )
        if account.balance < amount:                    # VALIDATE INSIDE THE LOCK
            raise ValidationError("Insufficient funds")
        account.balance -= amount                       # safe: no one else holds the row
        account.save(update_fields=["balance"])
    return account

# Lock-free counter: NO invariant to check, so let the DB do read+add atomically.
Post.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
```

Do not use `F()` when you must reject the write on a condition (e.g. balance can't go
negative) — a bare `F()` update can't fail-close on that; take the lock instead.

## Adapt to your repo
Rename `Account`/`balance`/`entreprise` to your models and tenant FK. Pick the
`quantize` scale your currency needs (`"0.01"` for 2 decimals, `"0.001"` for some).
Confirm the money column is `DecimalField(max_digits=…, decimal_places=…)`, not
`FloatField`. If you enforce non-negativity, back the lock with a DB `CheckConstraint`
(see `migrations`) so the invariant holds even for writes that skip this path.

## Gotchas
- `select_for_update()` requires being inside `atomic()` and does not work under
  autocommit — outside a transaction it raises `TransactionManagementError`.
- `.get()` after `select_for_update()` — never read the row unlocked first, then lock;
  the first read is stale by the time you lock.
- A check done *before* `select_for_update()` proves nothing; re-read and re-check after.
- Validate the *input* (amount > 0, finite) before opening the transaction, and the
  *state* invariant (sufficient balance) after locking — a negative amount turns a
  debit into a credit, and no row lock will catch it. `balance < amount` is False for
  a negative amount, so the guard passes and `balance -= amount` adds money.
- `select_for_update(skip_locked=True)` / `nowait=True` are for queue-style claiming,
  not for balances — a skipped row means the update never happened.
- Long transactions block other writers and exhaust connections — never call an
  external API or `Anthropic`/`Tavily` inside the lock; do that work, then open a short
  transaction to persist (see `celery-tasks`).
- Float creeps in via `float(...)` or JSON parsing — coerce request input to `Decimal`
  (or `str` first) before arithmetic.

## See also
- `migrations`
- `celery-tasks`
- `drf-api`
