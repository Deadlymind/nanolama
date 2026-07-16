---
name: webhook-handler
description: Safely receives inbound third-party webhooks and provider callbacks by holding a four-step contract — verify authenticity with a constant-time HMAC or verify token before parsing, dedupe idempotently by the provider event id, resolve the owning tenant from the verified payload, then ACK 200 fast and do the real work in a background task. Use when adding or reviewing a webhook or callback endpoint, wiring signature verification, handling retried or duplicate deliveries, guarding against SSRF from payload URLs, or asking how inbound provider events are processed here. Not for calling out to a provider's API (see ai-integration) or the background worker mechanics themselves (see celery-tasks).
---

# Webhook handler (verify, dedupe, resolve, ack)

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
2. **Dedupe idempotently** by the event's external id. Providers retry and
   re-deliver the same event; a unique constraint or `get_or_create` makes reprocessing
   a no-op instead of a double charge or duplicate row.
3. **Resolve the owning tenant explicitly** from the verified payload, so the event
   lands in the right account and can never leak across tenants (see `multi-tenancy`).
   No tenant resolved → reject, never fall through to a default account.
4. **ACK 200 fast, then work in the background.** Return 200 as soon as the event is
   persisted, and hand the real processing to a background task. Slow handlers make
   the provider time out and retry, multiplying load.

## Steps / idioms
Verify → dedupe → resolve tenant → 200 → enqueue, in one thin view:

```python
@csrf_exempt
def provider_webhook(request):
    raw = request.body                                   # raw bytes, not parsed
    sig = request.headers.get("X-Provider-Signature", "")
    expected = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):           # 1. constant-time verify
        return HttpResponse(status=401)                  #    before trusting body

    event = json.loads(raw)
    obj, created = WebhookEvent.objects.get_or_create(   # 2. idempotent dedupe
        provider="provider", external_id=event["id"],    #    (unique together)
        defaults={"payload": event},
    )
    if not created:
        return HttpResponse(status=200)                  #    already seen → no-op

    tenant = resolve_tenant(event)                       # 3. tenant from payload
    if tenant is None:
        return HttpResponse(status=400)                  #    no owner → reject
    obj.entreprise = tenant
    obj.save(update_fields=["entreprise"])

    process_webhook_event.delay(obj.id)                  # 4. ack now, work later
    return HttpResponse(status=200)
```

## Adapt to your repo
Rename the signature header, secret key, and provider name to match each integration.
Confirm you hash the **raw** request body — re-serializing parsed JSON changes bytes and
breaks the HMAC. Set the unique constraint on `(provider, external_id)`. Point the
background call at your task runner (see `celery-tasks`), and resolve the tenant through
whatever your project treats as the account owner.

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
- Return 200 only after the event is durably stored; a premature 200 loses events the
  provider will not resend.

## See also
- `celery-tasks`
- `security-review`
- `multi-tenancy`
