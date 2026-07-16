---
name: rbac-permissions
description: Gates access inside a tenant with a {resource}_{action} role system on Django/DRF — a deny-by-default permission class that maps the ViewSet action to a codename and checks has_permission/has_object_permission, plus explicit guards on every custom @action. Use when adding or reviewing a DRF permission class, wiring permission_classes on a ViewSet, deciding who may list/create/update/delete a resource, guarding a custom @action, or fixing an unguarded endpoint. Not for tenant row-scoping in get_queryset (see multi-tenancy) or generic serializer/router setup (see drf-api).
---

# RBAC permissions ({resource}_{action}, deny-by-default)

## When to use
Deciding *who inside a tenant* may perform an action on a resource. Tenant scoping
(`multi-tenancy`) answers "which rows exist for this user"; RBAC answers "may this
user list/create/update/delete them, or fire this custom action". Keep the two
separate — a queryset filter is not an authorization check.

## Pattern
Roles grant named permissions of the form `{resource}_{action}` (e.g.
`invoice_create`, `invoice_delete`). One DRF permission class:

1. **Deny by default.** Return `False` unless the user's roles grant the required
   codename. No codename resolved → deny; anonymous → deny.
2. **Map the DRF action to the codename.** `create`/`list`/`retrieve`/`update`/
   `partial_update`/`destroy` and every custom `@action` map to one
   `{resource}_{action}` string. `has_object_permission` re-checks per object.
3. **Guard every custom `@action` explicitly.** A custom action gets no codename for
   free; an unmapped action must fail closed, never fall through to allow.

One reusable class carries all three rules; the ViewSet declares its `perm_base` and
maps each custom `@action` to its codename half in `perm_action_map`, so the class-level
check resolves the codename *before* the handler body runs (DRF checks permissions in
`initial()`, ahead of your action code):

```python
# accounts/permissions.py — one deny-by-default class + its wiring
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission

_ACTION_MAP = {  # DRF action -> {action} half of the codename
    "list": "read", "retrieve": "read", "create": "create",
    "update": "update", "partial_update": "update", "destroy": "delete",
}

class HasResourcePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        base = getattr(view, "perm_base", None)             # e.g. "invoice"
        # custom @actions declare their half in perm_action_map; else map the DRF action
        act = getattr(view, "perm_action_map", {}).get(view.action) or _ACTION_MAP.get(view.action)
        if not base or not act:
            return False                                    # unmapped -> deny closed
        return request.user.has_perm(f"{base}_{act}")       # your role lookup

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)           # re-check per object

class InvoiceViewSet(TenantScopedViewSet):                  # scoping from multi-tenancy
    permission_classes = [HasResourcePermission]
    perm_base = "invoice"
    perm_action_map = {"approve": "approve"}               # custom @action -> codename half

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        invoice = self.get_object()                        # runs has_object_permission -> invoice_approve
        ...                                                # class-level check already passed in initial()
```

## Adapt to your repo
Replace `has_perm` with your actual role lookup (a `roles`/`permissions` M2M,
a cached set on the user, a claim in the JWT — resolve it server-side, never from
the request body). Rename `perm_base` values to your resources and settle the
codename verbs (`read`/`create`/`update`/`delete`, or `view`/`add`/`change`).
Confirm the tenant FK is still named `entreprise` (rename to your tenant) and that
scoping lives in `get_queryset`, not here.

## Gotchas
- Row-scoping is not authorization. `get_queryset` filtering by `entreprise` hides
  other tenants' rows; it does not stop an in-tenant user without the role. Keep both.
- Custom `@action`s bypass the default action map — map each one in `perm_action_map`
  (resolved at check time, not in the handler body) so an unmapped action denies, and
  fetch detail objects via `get_object()` so the per-object check runs.
- `has_object_permission` runs only on single-object lookups fetched via
  `get_object()`; list endpoints are gated by `has_permission` alone.
- Never trust a role/permission name sent in the request — resolve it from
  `request.user` server-side (see `security-review`).
- Order matters — an empty or missing `perm_base`/action must fail closed, so guard
  the `None` case before building the codename string.

## See also
- `multi-tenancy`
- `drf-api`
- `security-review`
