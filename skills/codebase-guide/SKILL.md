---
name: codebase-guide
description: The master map for building a feature end to end on this Django 5.2 / DRF 3.16 + Next.js stack — the model to serializer to ViewSet to urls/router to tests pipeline, every step tenant-scoped by the entreprise FK and gated by {resource}_{action} RBAC. Use when starting a new feature, adding an endpoint or app, onboarding to the conventions, asking "how is a feature built here" or "where does this go", or reviewing that a change follows house rules. Points to specialist skills for depth. Not for the deep mechanics of one layer — see multi-tenancy, drf-api, rbac-permissions, migrations, or write-tests for that.
---

# Codebase guide (how a feature is built end to end)

## When to use
Starting any new feature, endpoint, or app, or checking that a change follows the
house conventions. This is the map; the specialist skills are the terrain. Read it
first, then dive into the layer you are touching.

## Pattern
Every business feature flows through the same five files, in order:
`models.py` (tenant FK) → `serializers.py` (field shape) → `views.py`/ViewSet
(scope + RBAC) → `urls.py`/router (route name) → `tests.py` (isolation test).

Two invariants ride along every step and are non-negotiable on a new endpoint:

1. **Tenant scope** — the row is filtered/stamped by the current `entreprise`
   (fail-closed), never trusted from the client (see `multi-tenancy`).
2. **RBAC gate** — access is gated by a `{resource}_{action}` permission
   (see `rbac-permissions`).

A worked example, one file per step (migration follows the model — see `migrations`):

```python
# invoices/models.py
class Invoice(models.Model):
    entreprise = models.ForeignKey(               # rename to your tenant FK
        "tenants.Entreprise", on_delete=models.CASCADE,
        null=False, related_name="invoices")
    number = models.CharField(max_length=32)
    class Meta:
        indexes = [models.Index(fields=["entreprise"])]  # every filter hits it

# invoices/serializers.py  (see drf-api)
class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "number", "entreprise"]
        read_only_fields = ["entreprise"]         # server stamps it, not the client

# invoices/views.py  — both invariants enforced here
class InvoiceViewSet(TenantScopedViewSet):        # get_queryset filters by tenant
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.all()
    permission_classes = [HasResourcePermission]  # gates by invoice_{action}
    perm_base = "invoice"                         # matches rbac-permissions -> invoice_read/create/...

# invoices/urls.py  — basename gives reversible route names; mount under /api/
router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")

# invoices/tests.py  — the mandatory tenant-isolation test (see write-tests)
def test_tenant_isolation(self):
    self.client.cookies = self.user_a_cookies     # user A must NOT see B's invoice
    resp = self.client.get(f"/api/invoices/{self.invoice_b.id}/")
    assert resp.status_code == 404                # scoped queryset -> 404, not 403
```

Conventions on every change:
- New endpoint ⇒ tenant filter **and** RBAC permission, both. A filter with no gate
  leaks within the tenant; a gate with no filter leaks across tenants.
- One app per bounded resource; keep `models / serializers / views / urls / tests`
  split as above rather than one mega-file.
- Server owns the tenant: `read_only_fields` on the FK, stamped in `perform_create`.
  Stamp the audit trail in the same override — `perform_create` sets `created_by`
  (and `updated_by`) alongside the tenant, `perform_update` sets `updated_by` — from
  the request user, never the client. Newcomers wire the tenant and forget the who.
- Tests include the isolation case for every scoped resource — it is the one test
  reviewers block a PR for missing.

## Adapt to your repo
Rename `Entreprise`/`entreprise` and the accessor (`user.entreprise_id`) to your
tenant model. Adjust the `resource` string and permission class to your RBAC helper's
names. Confirm your project `urls.py` mounts app routers under a stable prefix
(`/api/`). Frontend features mirror this on the Next.js side — see `nextjs-module`.

## Gotchas
- Skipping the router basename breaks `reverse()` and DRF's `HyperlinkedIdentityField`.
- `Model.objects.get(pk=...)` inside a view bypasses tenant scoping — always go
  through the scoped `get_queryset()` / `get_object()`.
- Custom `@action` methods do not inherit the RBAC check automatically — gate each one.
- A migration that adds a `null=False` tenant FK to a populated table needs a default
  or a data migration (see `migrations`).
- Business rows are **soft-deleted**, not hard-`DELETE`d. Override `destroy()` to set a
  flag (`archived_at` / `is_deleted`) instead of removing the row, and exclude flagged
  rows from the default `get_queryset()` so they drop out of lists and 404 on detail
  while staying recoverable. A real `DELETE` loses the audit trail and breaks FKs.

## See also
- `multi-tenancy`
- `drf-api`
- `rbac-permissions`
- `migrations`
- `write-tests`
