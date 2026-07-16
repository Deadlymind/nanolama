---
name: websockets-channels
description: Real-time events on this stack with Django Channels 4.2+ on ASGI — an AsyncJsonWebsocketConsumer, JWT-cookie auth middleware that rejects anonymous sockets, tenant-scoped group names per entreprise, and channel_layer.group_send fired from transaction.on_commit over a Redis channel layer. Use when adding a WebSocket endpoint, building a consumer, pushing live notifications, wiring the ASGI application, fixing a socket that receives no events or leaks across tenants, or asking how real-time works here. Not for background jobs or fan-out compute (see celery-tasks), tenant filtering of REST querysets (see multi-tenancy), or the production ASGI/Procfile setup (see deploy-aws).
---

# WebSockets (Django Channels on ASGI)

## When to use
Pushing server-initiated events to the browser — live notifications, presence,
progress bars, collaborative updates. If the client just polls or the work is a
one-off background job with no live push, you want `celery-tasks`, not a socket.

## Pattern
Four invariants, held together:

1. **Async consumer** — `AsyncJsonWebsocketConsumer`, one per logical channel.
2. **Auth from the JWT cookie in `scope`** via ASGI middleware — a `BaseMiddleware`
   subclass reads the HttpOnly cookie from `scope["cookies"]`, resolves the user with
   `AccessToken(token)["user_id"]` wrapped in `database_sync_to_async`, and sets
   `scope["user"]`. Anonymous sockets are `close()`d, never left open — it mirrors the
   REST cookie auth.
3. **Group names are tenant-scoped** (`entreprise_<id>_...`) so `group_send` can
   never fan out across tenants — the same fail-closed rule as REST scoping.
4. **Events fire after the DB commit**, inside `transaction.on_commit`, so clients
   never see a row that a rollback erased. A Redis channel layer carries the fan-out.

The consumer rejects anonymous sockets and joins a tenant group; a plain function
emits into that group only after the row commits:

```python
# realtime/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]                       # set by JWT-cookie middleware
        if not user.is_authenticated:
            return await self.close(code=4401)          # reject anonymous, fail closed
        self.group = f"entreprise_{user.entreprise_id}_notifs"   # tenant-scoped name
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notify(self, event):                      # handler for {"type": "notify"}
        await self.send_json(event["payload"])

# call from a view, signal, or Celery task — only after the row is committed
def emit_notification(invoice):
    group = f"entreprise_{invoice.entreprise_id}_notifs"
    payload = {"type": "notify", "payload": {"id": invoice.id, "kind": "invoice"}}
    transaction.on_commit(
        lambda: async_to_sync(get_channel_layer().group_send)(group, payload)
    )
```

Wire it in `asgi.py`: call `get_asgi_application()` first so apps load before routes are
imported, then build a `ProtocolTypeRouter` with `"http"` mapped to that app and
`"websocket"` mapped to your `JWTCookieMiddleware(URLRouter([...]))` routing
`path("ws/notifications/", NotificationConsumer.as_asgi())`. Set `CHANNEL_LAYERS["default"]`
to `channels_redis.core.RedisChannelLayer` with a `hosts` entry pointing at Redis.

## Dev vs production
- **Dev server is Daphne**, not Uvicorn — add `"daphne"` above `"django.contrib.staticfiles"`
  in `INSTALLED_APPS` and `runserver` speaks ASGI automatically.
- **Under Uvicorn (production)** run `uvicorn myproject.asgi:application` against the same
  ASGI app. Uvicorn is a fine ASGI server but is not bundled with Channels; the Procfile
  lives in `deploy-aws`.

## Client side
The backend is only half of it — the browser has to hold the socket open and react
to events sanely.
- **One connection per session**, shared across the app, not one per component.
  **Auto-reconnect with backoff** (grow the delay, cap it) when it drops.
- **Keepalive ping on an interval *below* your proxy/load-balancer idle timeout.** An
  LB drops an idle socket after its quiet-timeout window; with no traffic under it the
  connection dies and events silently stop arriving — the classic "socket works, then
  goes dead after a minute of quiet." Keep the interval a relative rule (comfortably
  below whatever your proxy timeout is), not a hard-coded number.
- **Fall back to polling** when websockets are unavailable (blocked network, proxy
  strips the upgrade) so the UI still updates, just slower.
- **On each event, invalidate/refetch the affected query — don't hand-patch UI state
  from the payload.** The socket signals *what* changed; the refetch fetches the
  authoritative value. Patching state from the payload drifts from the server and
  races other writers. With `react-query`, an event maps to
  `queryClient.invalidateQueries({ queryKey: [...] })`.

## Adapt to your repo
Rename `Entreprise`/`entreprise` and the tenant accessor (`user.entreprise_id` vs
`user.profile.entreprise_id`), the cookie name (`access_token`), the app label
(`realtime`), and the group prefix to match your project. Point `CHANNEL_LAYERS`
at your ElastiCache Redis in production, and keep the socket cookie in sync with
your `simplejwt`/`dj-rest-auth` cookie name.

## Gotchas
- **No `transaction.on_commit` = race**: sending inside the transaction can reach the
  client before commit (or after a rollback) — always defer the send.
- **Never build a group name from client input** — derive it from `scope["user"]`,
  same fail-closed rule as REST tenant scoping (see `multi-tenancy`).
- The **in-memory channel layer** works only in one process; multi-worker or multi-dyno
  fan-out needs the Redis layer, or events silently vanish.
- **Blocking ORM calls** in an async consumer freeze the event loop — wrap them in
  `database_sync_to_async` (or `@sync_to_async`).
- `AccessToken(token)` **raises on expired/invalid** — catch it and fall back to
  `AnonymousUser`, or the socket 500s on connect.

## See also
- `multi-tenancy`
- `celery-tasks`
- `deploy-aws`
- `react-query`
