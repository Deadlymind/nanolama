---
name: observability
description: Instruments a Django/DRF plus Celery plus Channels stack so production failures are visible — structured JSON logs carrying a correlation id, tenant id (entreprise) and user id on every line, that same id propagated across the request, the task it enqueues and any consumer, plus tracing spans on state-changing work, scrubbed error tracking, and RED metrics with alerts that page a human. Use when adding logging or a logging filter, threading a correlation id through Celery or Channels, wiring an error tracker or metrics dashboard, or asking how to make one user action one traceable thread. Not for triaging a live incident (see incident-response) or auditing a diff for leaks (see security-review).
---

# Observability (tenant-correlated logs, traces, metrics)

## When to use
Adding or reviewing anything that must be debuggable in production without a
repro: a new logging config, a Celery task or Channels consumer whose failures
you can't currently trace, an error-tracker integration, or a metrics dashboard.
The goal is that one user action reads as one traceable thread across the web
request, the background task it fires, and any realtime consumer — all stamped
with *who* (user) and *which tenant* (entreprise).

## Pattern
Four signals, one correlation id tying them together:

1. **Structured logs.** Emit JSON, not free text. Every line carries a
   `correlation_id`, `entreprise_id`, and `user_id` — injected by a logging
   filter, never hand-passed. Grep-by-tenant and grep-by-request both work.
2. **Propagated correlation id.** Generate (or accept) the id at the DRF request
   edge, put it in a context var, and pass it explicitly into every Celery task
   and Channels consumer that request spawns. Background work inherits the thread.
3. **Distributed tracing.** Open a span (OpenTelemetry-style) around every
   state-changing action and every background task, so you can see the request →
   task → consumer causal chain and where the latency lives.
4. **Metrics with alerts.** Track the RED signals — request **R**ate, **E**rror
   rate, **D**uration — plus queue depth and live websocket-connection counts,
   and set thresholds that page a human, not just color a chart.

**Absolute rule:** never log a secret, token, cookie, `Authorization` header, or
raw PII. Scrub before the record leaves the process. This is a security boundary,
not a nicety (ties `security-review`).

## Steps / idioms
1. **Stamp every log line via a filter.** A `logging.Filter` reads the current
   request's context and attaches the ids to each record, so no call site has to
   remember. Point a JSON formatter at the same fields:

   ```python
   # observability/logging.py — inject correlation + tenant into every record.
   import logging
   from contextvars import ContextVar

   correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")
   entreprise_id:  ContextVar[str] = ContextVar("entreprise_id",  default="-")
   user_id:        ContextVar[str] = ContextVar("user_id",        default="-")

   class ContextFilter(logging.Filter):
       def filter(self, record: logging.LogRecord) -> bool:
           record.correlation_id = correlation_id.get()
           record.entreprise_id  = entreprise_id.get()
           record.user_id        = user_id.get()
           return True  # filter only enriches; it never drops the record
   ```

   Set the context vars in DRF middleware from `request.user` (reuse the same
   tenant accessor as `multi-tenancy`); read an inbound `X-Correlation-ID` header
   if present, else mint a UUID and echo it back on the response.

2. **Carry the id into background work.** Context vars do not cross a process, so
   pass the id as an explicit task argument (or a header) and re-set it at the top
   of the task; do the same in a Channels consumer's `connect`:

   ```python
   # Enqueue with the id; the worker re-establishes context on receipt.
   process_invoice.delay(invoice_id, correlation_id=correlation_id.get())
   ```

3. **Wrap state-changing work in a span.** Name it for the action
   (`invoice.approve`), tag it with `entreprise_id`, and let the task span link to
   the request span via the propagated id. Read-only GETs rarely need their own.
4. **Scrub before export.** Configure the error tracker's before-send hook to drop
   `Authorization`/`Cookie` headers, `password`/`token`/`secret` keys, and known
   PII fields — allowlist what may leave, don't blocklist and hope.
5. **Wire alerts, not just dashboards.** An error-rate spike, a growing Celery
   queue, or a websocket-connection cliff should page on-call (see
   `incident-response` for what happens after the page).

## Adapt to your repo
Rename `entreprise_id`/`Entreprise` and the tenant/user accessor path to match
your models. Choose your own transport for the correlation id into Celery (task
kwarg vs. message header) and Channels (scope entry). Do not pin tool versions
here — Sentry, OpenTelemetry, and your metrics backend all move; confirm the
current SDK and API surface with `version-check` before wiring. The stable facts
you can rely on are the RED signal set and the correlation-id discipline, not any
one vendor's helper names.

## Gotchas
- **Context vars are per-process, per-task.** A `.delay()` does not carry your
  `ContextVar` — pass the id explicitly and re-set it in the worker, or the task's
  logs show `correlation_id=-` and the thread breaks exactly where you need it.
- **Logging the request body re-leaks what the serializer hid.** A debug line that
  dumps `request.data` can spill a token or PII the API response never exposed —
  scrub at the logging boundary too, not only at the API edge (`security-review`).
- **Sampling hides the rare error.** Trace-sample normal traffic if you must, but
  keep error traces at 100% or the one failure you're chasing gets dropped.
- **A dashboard nobody watches is not monitoring.** If a signal has no threshold
  that pages, treat it as decoration — the outage will be found by a customer.
- **High-cardinality metric labels explode cost.** Never label a metric with
  `user_id` or a raw id; keep `entreprise_id` for logs/traces, aggregate metrics.
- **Don't rebuild an id that already exists.** If an upstream proxy or gateway
  already sets a request/trace id, adopt it instead of minting a competing one.

## See also
- `incident-response`
- `security-review`
- `celery-tasks`
- `deploy-aws`
