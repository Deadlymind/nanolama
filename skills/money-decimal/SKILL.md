---
name: money-decimal
description: Represents and computes money with fixed-precision Decimal on a Django/DRF app — DecimalField at the currency minor-unit precision, quantize with an explicit rounding mode at each step of a tax/fee chain, and one shared source of truth for the valid rate set and precision across model, serializer and frontend. Use when adding a money field, writing a tax/discount/withholding calculation, seeing float rounding drift in totals, defining valid rates or a currency scale, or pinning a total with a golden-fixture test. Not for row-locking concurrent money writes (see db-concurrency) or generic serializer wiring (see drf-api).
---

# Money with Decimal (fixed precision, never float)

## When to use
Any field, calculation, or serializer that carries money — line totals, taxes,
fees, discounts, withholdings. On money, a rounding bug is a correctness bug that
shows up as customer-facing cents that do not add up, so treat precision as an
invariant, not a formatting detail.

## Pattern
Two rules, held everywhere money is stored or computed:

1. **Money is `Decimal` at a fixed scale, never `float`.** Binary floats cannot
   represent decimal fractions exactly (`0.1 + 0.2 != 0.3`), so float money drifts
   by a cent under multiplication and summation. Store as `DecimalField` at the
   currency's minor-unit precision.
2. **`quantize` with an explicit rounding mode at every step of a multi-step chain**,
   not only on the final total. Rounding a tax, then rounding the fee on top of the
   already-rounded tax, gives a different answer than rounding once at the end — and
   the stepwise answer is the one on the printed document.

Concurrency (two requests writing the same balance) is a separate concern — lock the
row with `db-concurrency`. This skill is only about precision and rounding.

## Adapt to your repo
Define the currency scale as a parameter, not a magic number: most currencies use
2 decimal places, some use 0 or 3. Set `decimal_places` to your minor-unit precision
and `max_digits` to cover the largest total you expect. Declare the **valid rate set**
and the **precision** in exactly one module and import it into the model, the
serializer, and (mirrored) the frontend, so a rate added in one place cannot silently
be missing in another. Rename the example fields to your domain.

```python
# money.py — the single source of truth, imported everywhere
from decimal import Decimal, ROUND_HALF_UP

MONEY_SCALE = Decimal("0.01")            # 2 dp; use "1" for 0-dp, "0.001" for 3-dp
VALID_TAX_RATES = frozenset(map(Decimal, ["0", "0.10", "0.20"]))  # tune per jurisdiction

def money(value) -> Decimal:
    """Round any intermediate to the currency scale with an explicit mode."""
    if isinstance(value, float):
        # a float has already lost precision; quantize would only hide it.
        # Don't "fix" this with Decimal(str(value)) — that launders the error.
        raise TypeError("money() rejects float — pass Decimal, int, or str")
    return Decimal(value).quantize(MONEY_SCALE, rounding=ROUND_HALF_UP)

# stepwise chain: quantize the tax, THEN the fee — not once at the end
net  = money(unit_price * quantity)
tax  = money(net * tax_rate)                 # rate ∈ VALID_TAX_RATES
fee  = money((net + tax) * fee_rate)
total = net + tax + fee                       # already-quantized parts sum exactly
```

Model and serializer both pull from the same module:

```python
# models.py
amount = models.DecimalField(max_digits=14, decimal_places=2)  # decimal_places = scale
```

## Gotchas
- Never build a `Decimal` from a `float` literal — `Decimal(0.1)` carries the float's
  error. Pass a string or int: `Decimal("0.1")`. Enforce it at the boundary — `money()`
  raises `TypeError` on a float rather than quantizing the error away. `quantize` hides
  the drift for most values, so a laundered float is a latent cent-drift, not a loud
  failure: `money(2.675)` would give `2.67` where `money(Decimal("2.675"))` gives `2.68`.
- Pick the rounding mode deliberately and reuse it; `ROUND_HALF_UP` and
  `ROUND_HALF_EVEN` disagree on exact-half cases, and the choice is a policy, not a
  default. Whatever you pick, apply it consistently across every step.
- Validate incoming rates against the shared `VALID_TAX_RATES` set — an unlisted rate
  is a data error, not a silent computation.
- Summing a column of un-quantized intermediates then rounding once can differ from
  the document's line-by-line total; round at the boundary the document rounds at.
- The DB column's `decimal_places` and the app's `MONEY_SCALE` must match, or a
  round-trip silently re-rounds.

## Golden-fixture regression test
Pin one hand-verified worked example so any drift in the calculation fails loudly.
Compute a realistic multi-line order by hand once, assert the exact total, and also
test the boundaries — zero, each rate-bracket edge, and the min/max representable
amount (see `write-tests`).

```python
def test_order_total_golden():
    # hand-verified: net 14.97 (3 x 4.99) + tax 2.99 (20% of 14.97, half-up) + flat fee 1.50 = 19.46
    assert compute_total(unit_price=Decimal("4.99"), quantity=3,
                         tax_rate=Decimal("0.20"), fee=Decimal("1.50")) == Decimal("19.46")

def test_zero_and_bracket_edges():
    assert compute_total(Decimal("0"), 0, Decimal("0"), Decimal("0")) == Decimal("0.00")
```

## See also
- `db-concurrency`
- `write-tests`
- `drf-api`
