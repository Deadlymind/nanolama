---
name: drf-api
description: Builds DRF 3.16 REST endpoints on Django 5.2 — ModelViewSet plus DefaultRouter, a light list serializer split from a detail serializer via get_serializer_class, pagination defaults, a custom export @action, and a drf-spectacular OpenAPI schema. Use when adding or reviewing a ViewSet, serializer, router, or endpoint, splitting list vs detail payloads, wiring pagination, adding a CSV/export action, or generating the OpenAPI schema. Not for tenant queryset scoping (see multi-tenancy), role gating (see rbac-permissions), or the frontend Zod contract (see drf-zod-contract).
---

# DRF API (viewsets, serializers, routers, schema)

## When to use
Adding or reviewing a REST endpoint on this stack — a serializer, a `ModelViewSet`,
router wiring, pagination, an export action, or the OpenAPI schema. Tenant scoping and
RBAC are prerequisites here, not re-explained: your ViewSet subclasses the fail-closed
tenant mixin (`multi-tenancy`) and declares `{resource}_{action}` permissions
(`rbac-permissions`) before you add anything below.

## Pattern
One `ModelViewSet` per resource, registered on a single `DefaultRouter`. Serve a **light
list serializer** (few columns, no nested joins) for `list`, and a **fat detail
serializer** for `retrieve`/`create`/`update`, chosen in `get_serializer_class()` by
`self.action`. Pagination is a global default. Side-jobs (export, bulk ops) are custom
`@action`s, not new endpoints. The schema is generated, never hand-written.

## Steps / idioms
Split the serializers, pick one by `self.action`, register a single router, and inherit
the tenant + RBAC mixins. One consolidated example:

```python
# serializers.py — thin list row vs. fat detail payload
class InvoiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "number", "total", "status"]           # cheap list row

class InvoiceDetailSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)    # nested, costly
    class Meta:
        model = Invoice
        fields = ["id", "number", "total", "status", "lines", "notes"]

# views.py — one ViewSet; serializer chosen by action, tenant + RBAC inherited
class InvoiceViewSet(TenantScopedViewSet):        # scopes queryset fail-closed
    queryset = Invoice.objects.all()
    permission_classes = [InvoiceRBAC]            # {resource}_{action} gate

    def get_serializer_class(self):
        return InvoiceListSerializer if self.action == "list" else InvoiceDetailSerializer

    @action(detail=False, methods=["get"])        # -> /api/invoices/export/
    def export(self, request):
        rows = self.filter_queryset(self.get_queryset())   # stays tenant-scoped
        resp = HttpResponse(content_type="text/csv")
        csv.writer(resp).writerows(rows.values_list("number", "total"))
        return resp

# urls.py — one router derives the URLConf and the browsable/OpenAPI schema
router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
urlpatterns = router.urls
```

Set a global pagination default so every list is bounded: in `settings.py`, give
`REST_FRAMEWORK` a `DEFAULT_PAGINATION_CLASS` of
`rest_framework.pagination.PageNumberPagination`, a `PAGE_SIZE` (e.g. 25), and a
`DEFAULT_SCHEMA_CLASS` of `drf_spectacular.openapi.AutoSchema`. Generate the OpenAPI
schema with `python manage.py spectacular --file schema.yml`, and annotate non-obvious
actions with `@extend_schema` so the generated types stay accurate — the frontend
consumes this schema (see `drf-zod-contract`).

## Adapt to your repo
Rename `Invoice`, `InvoiceLine`, and the `entreprise` tenant FK to your models. Confirm
`TenantScopedViewSet` and your RBAC permission class exist (they are separate skills).
Pick a pagination class that fits your UI — `PageNumberPagination` for page numbers,
`CursorPagination` for infinite scroll or large offsets. Set `PAGE_SIZE` to your default.

## Gotchas
- A single fat serializer on `list` is the classic N+1 — split list vs detail and add
  `select_related`/`prefetch_related` on the detail queryset (see `perf-review`).
- Custom `@action`s bypass nothing automatically: re-run `get_queryset()` /
  `filter_queryset` so they stay tenant-scoped, and gate them under RBAC.
- No global `DEFAULT_PAGINATION_CLASS` means unbounded list responses — set it once.
- Stream large exports with `StreamingHttpResponse`; a full `HttpResponse` buffers the
  whole CSV in memory.
- `get_serializer_class` keys off `self.action` — a typo silently falls through to the
  detail serializer; assert the split in a test.

## See also
- `multi-tenancy`
- `rbac-permissions`
- `drf-zod-contract`
- `perf-review`
