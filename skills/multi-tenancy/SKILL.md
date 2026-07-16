---
name: multi-tenancy
description: Enforces tenant isolation on a Django/DRF app where every business model carries a non-null tenant FK (entreprise) and ViewSets auto-filter fail-closed by the current tenant. Use when adding a tenant-scoped model, writing or reviewing a ViewSet or queryset, wiring a TenantScopedViewSet mixin, fixing a cross-tenant data leak, or asking how entreprise scoping works here. Not for role/permission gating (see rbac-permissions) or generic serializer/router setup (see drf-api).
---

# Multi-tenancy (fail-closed tenant isolation)

## When to use
Adding or reviewing any business model or API that must never expose one tenant's
rows to another. On this stack, tenant isolation is the single most important
invariant — treat a missing tenant filter as a security bug, not a style nit.

## Pattern
Three rules, held everywhere:

1. **Every business model carries a non-null tenant FK** (`entreprise`). No nulls,
   no "global" business rows.
2. **Reads are scoped in `get_queryset()`, fail-closed.** The tenant comes from the
   authenticated user, never from the request body/query string. No tenant → return
   `.none()`, never all rows.
3. **Writes set the tenant server-side** in `perform_create`/`perform_update`, so a
   client can never assign a row to another tenant.

Access *within* a tenant is a separate concern — gate it with `rbac-permissions`.

## Steps / idioms
1. Give the model a non-null tenant FK and a related name:

   ```python
   class Invoice(models.Model):
       entreprise = models.ForeignKey(
           "tenants.Entreprise", on_delete=models.CASCADE,
           null=False, related_name="invoices",
       )
       # ... business fields
       class Meta:
           indexes = [models.Index(fields=["entreprise"])]  # every filter hits it
   ```

2. Subclass one fail-closed mixin instead of hand-writing `get_queryset` per view:

   ```python
   # tenants/mixins.py
   class TenantScopedViewSet(viewsets.ModelViewSet):
       def get_queryset(self):
           user = self.request.user
           tenant_id = getattr(user, "entreprise_id", None)
           if not user.is_authenticated or tenant_id is None:
               return super().get_queryset().none()      # fail closed
           return super().get_queryset().filter(entreprise_id=tenant_id)

       def perform_create(self, serializer):
           serializer.save(entreprise=self.request.user.entreprise)
   ```

3. Object lookups reuse the scoped queryset, so per-object 404 is automatic —
   never `Model.objects.get(pk=...)` in a view (that bypasses scoping).
4. Add a tenant-isolation test for every scoped resource (see `write-tests`):
   user A must get 404/empty for user B's object.

## Variants
Keep the invariant; change only what "the current tenant" resolves to.

- **One entreprise = one company (default).** `user.entreprise_id` is the tenant.
- **Sub-teams / departments inside a tenant.** Tenant FK still gates isolation; add a
  second, *optional* `team`/`departement` FK and layer it as an RBAC/visibility filter
  on top of the tenant filter — never as a replacement for it.
- **Agency operating over client sub-accounts.** Model the client as the tenant and
  give agency users an explicit, audited membership across several `entreprise` rows;
  resolve "current tenant" from an `X-Tenant`-style selector **validated against that
  membership**, then filter by it. Still fail-closed: an unknown/foreign tenant → `.none()`.

## Adapt to your repo
Rename `Entreprise`/`entreprise`, the accessor path (`user.entreprise_id` vs
`user.profile.entreprise_id`), and the app label to match your project. If your tenant
is resolved from a request header (agency variant), validate it against server-side
membership before trusting it. Confirm the FK is `null=False` in the migration.

## Gotchas
- A client-supplied `entreprise`/`tenant` id in the body or query string is never
  trusted — scope from `request.user` only.
- `.none()` on the empty/anonymous case, not an unfiltered queryset — fail closed.
- Custom `@action` methods and nested/related lookups need the same scoping; the
  mixin only covers the default queryset (see `rbac-permissions` to gate actions).
- The tenant filter prevents leaks, not N+1 — add `select_related`/`prefetch_related`
  in the serializer (see `perf-review`).

## See also
- `rbac-permissions`
- `drf-api`
- `migrations`
- `security-review`
- `write-tests`
