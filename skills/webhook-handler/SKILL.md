---
name: webhook-handler
description: Safely receives inbound third-party webhooks and provider callbacks by holding a four-step contract — verify authenticity with a constant-time HMAC or verify token before parsing, resolve the owning tenant from the verified payload before persisting anything, dedupe idempotently by the provider event id, then ACK 200 fast and do the real work in a background task. Use when adding or reviewing a webhook or callback endpoint, wiring signature verification, handling retried or duplicate deliveries, guarding against SSRF from payload URLs, or asking how inbound provider events are processed here. Not for calling out to a provider's API (see ai-integration) or the background worker mechanics themselves (see celery-tasks).
---

# Webhook handler (verify, resolve, dedupe, ack)

## When to use
Adding or reviewing any endpoint a third party POSTs to — payment events, chat
platform callbacks, delivery receipts, provider status updates. Treat the whole
request body as a form submitted by a stranger: nothing in it is trusted until you
have proven where it came from.

## Pattern
Four steps, always in this order. Skipping or reordering any one is a security or
reliability bug, not a style nit:

1. **Verify authenticity first.** Compute the provider's HMAC over the raw body and
   compare with a constant-time equality check, or match the provider's verify
   token. Do this *before* JSON-parsing or trusting a single field. Reject with 401
   on mismatch.
2. **Resolve the owning tenant explicitly** from the verified payload, so the event
   lands in the right account and can never leak across tenants (see `multi-tenancy`).
   No tenant resolved → reject, never fall through to a default account. Do this
   *before* you persist: a dedupe row written for an event you then reject makes the
   provider's retry a no-op, losing the event permanently.
3. **Dedupe idempotently** by the event's external id. Providers retry and
   re-deliver the same event; a unique constraint or `get_or_create` makes reprocessing
   a no-op instead of a double charge or duplicate row. Dedupe on *handled*, not
   merely *seen* — a row still `pending` must be re-enqueued, not swallowed.
4. **ACK 200 fast, then work in the background.** Persist the row and enqueue the task
   in one `atomic()` block, with the enqueue on `transaction.on_commit` so it can never
   fire for a row that rolled back. Then return 200 and let the task do the real work —
   slow handlers make the provider time out and retry, multiplying load.

## Steps / idioms
Verify → resolve tenant → dedupe → enqueue on commit → 200, in one thin view. The
tenant is resolved *before* the dedupe row exists, so a rejected event leaves no row
for the provider's retry to collide with:

```python
@csrf_exempt
def provider_webhook(request):
    raw = request.body                                   # raw bytes, not parsed
    sig = request.headers.get("X-Provider-Signature", "")
    expected = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):           # 1. constant-time verify
        return HttpResponse(status=401)                  #    before trusting body

    event = json.loads(raw)

    tenant = resolve_tenant(event)                       # 2. tenant BEFORE we persist
    if tenant is None:
        return HttpResponse(status=400)                  #    no owner → reject, no row

    with transaction.atomic():
        obj, created = WebhookEvent.objects.get_or_create(  # 3. idempotent dedupe
            provider="provider", external_id=event["id"],   #    (unique together)
            defaults={"payload": event, "entreprise": tenant, "status": "pending"},
        )
        if not created and obj.status != "pending":
            return HttpResponse(status=200)              #    already handled → no-op
        # only enqueue once the row is durably committed
        transaction.on_commit(lambda: process_webhook_event.delay(obj.id))

    return HttpResponse(status=200)                      # 4. ack now, work later
```

## Adapt to your repo
Rename the signature header, secret key, and provider name to match each integration.
Confirm you hash the **raw** request body — re-serializing parsed JSON changes bytes and
breaks the HMAC. Set the unique constraint on `(provider, external_id)`. Give
`WebhookEvent` a `status` field (`pending`/`done`/`failed`); the task must flip it to
`done` on success, so a re-delivery of a still-`pending` event is re-enqueued rather
than swallowed. Point the background call at your task runner (see `celery-tasks`),
and resolve the tenant through whatever your project treats as the account owner.

## Gotchas
- Verifying against parsed-then-re-dumped JSON fails intermittently — always sign the
  raw bytes exactly as received.
- Use a constant-time compare (`hmac.compare_digest`), never `==`, for signatures.
- **SSRF:** never fetch, redirect to, or enqueue a URL taken from the payload without a
  strict host allowlist — an attacker-controlled callback can hit internal services.
- Some providers send an unsigned verification handshake on setup; handle it explicitly
  rather than weakening signature checks for real events.
- Do the heavy work (API calls, emails, DB writes) in the background task, not in the
  request — but persist enough in the view that a retry after a crash is still idempotent.
- Return 200 only after the event is durably stored **and** marked for processing — a
  dedupe row written before the tenant is resolved or before the task is enqueued turns
  the provider's retry into a silent 200 and loses the event for good.
- **Bound the body before you hash it.** `request.body` is capped by
  `DATA_UPLOAD_MAX_MEMORY_SIZE` (2.5 MB default) — set it to your provider's real
  maximum rather than inheriting the default, and return 413 above it.
- **Parse defensively after verifying.** Wrap `json.loads(raw)` and the `event["id"]`
  lookup in `try/except (ValueError, KeyError): return HttpResponse(status=400)` — a
  signed-but-malformed body should be a 400 you can see, not a 500 the provider
  silently retries forever.
- **Check the signature timestamp.** If the provider signs a timestamp
  (`t=...,v1=...`), include it in the HMAC input and reject deliveries outside a short
  window (±5 min). Dedupe by event id blunts replay but does not stop a captured
  request being replayed before the original lands.
- **Support two secrets during rotation.** Verify against
  `[SECRET_CURRENT, SECRET_PREVIOUS]` with `any(hmac.compare_digest(sig, ...))` so a
  rotation does not 401 in-flight deliveries; drop the old secret once the provider
  has cut over.

## See also
- `celery-tasks`
- `security-review`
- `multi-tenancy`
