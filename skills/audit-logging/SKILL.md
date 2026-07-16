---
name: audit-logging
description: Records an append-only, tenant-scoped audit trail of security-relevant actions in an AuditLog model — actor, action, target, timestamp, ip/user-agent, and a REDACTED before/after diff — written in the same transaction as the action and made append-only at the DB by revoking UPDATE/DELETE. Use when logging auth events (login/logout/failed-login), RBAC role or permission changes, tenant-data exports, or destructive admin actions, adding an AuditLog model, enforcing retention or immutability, or asked how to prove who did what to which row. Not for ops telemetry, metrics, or traces — that is observability — and not for role gating itself (see rbac-permissions).
---

# Audit logging (append-only security record)

## When to use
You need a durable, queryable answer to "who did what, to which row, when, from
where" — for compliance, incident forensics, or a customer trust review. Reach
for this whenever a change touches authentication, RBAC, a tenant-data export, or
a destructive admin action. It is a security **record**, not application logging.

## Pattern
An audit log is an **append-only, tenant-scoped table of facts** about
security-relevant actions. Three invariants make it trustworthy:

1. **Immutable.** No update or delete path exists in app code, and the DB itself
   forbids it (revoke `UPDATE`/`DELETE`, or a rejecting trigger). A trail an admin
   can quietly rewrite proves nothing.
2. **Atomic with the action.** The audit row is written in the **same transaction**
   as the change it describes. If the action rolls back, so does its record.
3. **Redacted at write time.** Passwords, tokens, secrets, and full PII are stripped
   *before* the diff is persisted. The log records that a field changed, not its
   secret value.

## What to capture
Log the events an auditor or responder actually asks about — not every request:

- **Authentication** — login, logout, and **failed** login (failed auth is the
  signal that matters most in an incident).
- **Authorization changes** — RBAC role grants/revokes, permission edits, ownership
  transfers (see `rbac-permissions`).
- **Tenant-data exports** — any bulk read that leaves the system (CSV/report/API dump).
- **Destructive or admin actions** — deletes, config changes, impersonation, resets.

Each row carries: `entreprise` FK (tenant scope), `actor` (the acting user, nullable
for anonymous failed logins), `action` (a stable verb like `role.granted`), the
**target** as a generic content-type + object id, `timestamp`, request `ip` and
`user_agent`, and a redacted `changes` before/after diff.

## Model + helper

```python
# audit/models.py
class AuditLog(models.Model):
    entreprise = models.ForeignKey("tenants.Entreprise", null=True, blank=True,
                                   on_delete=models.PROTECT,
                                   related_name="audit_logs")   # null: pre-auth event
    actor      = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, # null: failed login
                                   on_delete=models.SET_NULL)
    action     = models.CharField(max_length=64)                        # "auth.login_failed"
    target_ct  = models.ForeignKey("contenttypes.ContentType", null=True,
                                   on_delete=models.SET_NULL)           # generic target
    target_id  = models.CharField(max_length=64, blank=True)
    ip         = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=256, blank=True)
    changes    = models.JSONField(default=dict)                         # REDACTED diff
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["entreprise", "action", "created_at"])]

    def save(self, *a, **kw):
        if self.pk:                              # app-level guard; DB is the real gate
            raise ValueError("AuditLog rows are append-only")
        super().save(*a, **kw)

SECRET_KEYS = {"password", "token", "secret", "authorization", "ssn"}

def record(*, request, action, actor=None, entreprise=None, target=None,
           before=None, after=None):
    def _redact(d):  # never persist secret values
        return {k: ("***" if k.lower() in SECRET_KEYS else v) for k, v in (d or {}).items()}
    user = getattr(request, "user", None)
    if actor is None and user is not None and user.is_authenticated:
        actor = user                      # anonymous (failed login) stays None
    if entreprise is None:
        entreprise = getattr(actor, "entreprise", None)  # may stay None: pre-auth event
    # runs inside the caller's transaction.atomic() — commits/rolls back with the action
    AuditLog.objects.create(
        entreprise=entreprise, actor=actor,
        action=action,
        target_ct=ContentType.objects.get_for_model(target) if target else None,
        target_id=str(getattr(target, "pk", "")),
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:256],
        changes={"before": _redact(before), "after": _redact(after)},
    )
```

Call `record(...)` from inside the same `transaction.atomic()` block as the action
(e.g. right after `serializer.save()` in `perform_update`). For failed logins there
is no authenticated user — `record()` leaves `actor` None for an `AnonymousUser`.
Pass `entreprise=` explicitly if you can resolve the tenant from the submitted
identifier; otherwise the row is written unscoped-but-logged (hence the nullable
tenant FK).

## Enforcing append-only at the DB
The `save()` guard stops honest bugs; a real audit trail also needs the database to
refuse rewrites, so a compromised app account cannot alter history. In a migration,
run raw SQL to `REVOKE UPDATE, DELETE ON audit_auditlog FROM <app_role>`, or install
a `BEFORE UPDATE OR DELETE` trigger that raises. Pair this with a **retention
policy**: keep rows for your compliance window (often 1–7 years), then archive to
cold storage rather than deleting live — deletes are what you just forbade.

## Adapt to your repo
Rename `Entreprise`/`entreprise` and the tenant accessor (`request.user.entreprise`
vs `request.user.profile.entreprise`) to match your project. Set `SECRET_KEYS` to
your actual sensitive field names, and confirm the DB role your app connects as is
the one you revoke write grants from (the migration role often differs). Pick a
retention window from your compliance obligations, not a default. This is a portable
pattern — no exact table or role names are assumed.

## Gotchas
- **Audit is not observability.** This table is a queryable compliance record,
  tenant-scoped and retained for years; ops telemetry (metrics, traces, request
  logs) is high-volume, short-lived, and lives in your APM. Do not conflate them or
  route audit rows into log shipping where they can be dropped or mutated.
- **Append-only is not tamper-evident.** Revoking `UPDATE`/`DELETE` stops the *app
  role* from rewriting history; it does not detect a privileged role inserting,
  backdating, or reloading rows, nor an altered backup. If you must *prove* the trail
  is unaltered, chain each row (`prev_hash`, `row_hash = sha256(prev_hash || canonical(row))`)
  and/or ship rows to an append-only external sink — a WORM bucket with object lock,
  or a signed periodic checkpoint. Optional hardening; claim only what you enforce.
- **Write it in the transaction, not after the response.** A fire-and-forget log
  after commit can silently fail and desync the trail. Prefer the same `atomic()`
  block: a failed audit write then rolls the action back too. `transaction.on_commit`
  is a *weaker* fallback — it correctly never fires for a rolled-back action, but it
  runs in a new transaction after COMMIT, so if that insert fails the action is
  already committed and the trail silently drifts. Use it only where the audit write
  must not be able to abort the action, and alert on callback failures.
- **Redact before persisting, not on read.** Once a secret is in the row, it has
  leaked; masking at display time is too late (see `security-review`).
- **`on_delete=PROTECT`/`SET_NULL`, never `CASCADE`.** Deleting a user or tenant
  must not erase their audit history — that is exactly the record you need after
  an incident (see `incident-response`).
- **Log the failure too.** Failed logins and denied-permission attempts are the
  highest-signal rows; capturing only successes hides the attack.

## See also
- `rbac-permissions`
- `multi-tenancy`
- `security-review`
- `incident-response`
