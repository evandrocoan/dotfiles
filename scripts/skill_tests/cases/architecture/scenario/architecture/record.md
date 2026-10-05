# Record: event persistence

**Status:** Implemented

## Decision

Persist each accepted event individually. This describes the currently running path.

## Contract

An accepted event is durable before its acknowledgement. Persisted effects are idempotent under
retry. Every consumed event advances progress, including events discarded by the business filter.
A discarded event still receives acknowledgement and advances the durable consumer position;
it creates no data row.

## Flow

Receive -> classify -> persist accepted data if any -> advance progress for every consumed event
-> acknowledge. Discarded records take the progress and acknowledgement stages too.

## Recovery

Restart resumes after the durable consumer position. Retries cannot double-apply an accepted effect.

## Consequences

Per-event writes have overhead. Changing scheduling need not replace classification, progress,
acknowledgement or recovery ownership.

## Traceability

The current adapter calls persist_one, advances position, and acknowledges. The old production path
is the only executable protection of these guarantees today.
