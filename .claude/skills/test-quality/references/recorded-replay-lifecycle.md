# Recorded replay lifecycle

Use this design when a system must continuously capture real executions and
later reproduce selected executions as deterministic CI tests. Adapt names and
storage technology to the repository; preserve the contracts below.

## Contents

- [Design the boundary first](#design-the-boundary-first)
- [Record continuously without changing behavior](#record-continuously-without-changing-behavior)
- [Store large artifacts efficiently](#store-large-artifacts-efficiently)
- [Rotate bounded raw storage safely](#rotate-bounded-raw-storage-safely)
- [Replay through production orchestration](#replay-through-production-orchestration)
- [Promote a recording into CI](#promote-a-recording-into-ci)
- [Preserve incidents honestly](#preserve-incidents-honestly)
- [Test the recorder and lifecycle](#test-the-recorder-and-lifecycle)

## Design the boundary first

Define the public production entry point the replay must call and every mutable
boundary it must replace. A complete session normally includes inbound events,
provider reads, model requests and responses, tool calls and results, sidecar
requests, state transitions, usage, terminal decisions, and publication
effects. Do not call a replay complete when it starts after orchestration or
omits a boundary that influenced the result.

Assign one immutable execution identity to the whole session. Bind it to the
repository or tenant scope, immutable source snapshot, command, and causal
parents needed to prevent cross-execution reuse. Concurrent executions must
never share mutable event streams or sequence counters.

## Record continuously without changing behavior

- Keep recording enabled by runtime policy rather than requiring an incident to
  be reproduced manually. Recording failures must follow the repository's
  explicit availability policy and must never silently alter the analysis.
- Store one self-contained directory per execution. Include a small manifest,
  metadata, lifecycle state, ordered events, and every referenced artifact
  beneath that directory. Never require a global blob store to replay a copied
  fixture.
- Append structured events with stable schemas, monotonic sequence numbers,
  actor, kind, execution and command identities, and causal parents. Record at
  the actual boundary instead of reconstructing events from logs.
- Capture requests before invoking a boundary and record success or failure
  after it returns. Preserve malformed responses, retryable failures, usage,
  ordering, and terminal-validation outcomes exactly when they affect control
  flow.
- Keep code literals and model-owned semantic inputs byte-for-byte intact.
  Apply the repository's credential policy at capture time or through an
  explicit deterministic promotion step; never use heuristic sanitization that
  changes program meaning.
- Write active data to temporary or append-safe files. Finalize atomically only
  after writers have flushed, artifacts have been materialized, hashes have
  been computed, and terminal state has been recorded. Mark interrupted
  executions explicitly instead of presenting them as complete.

## Store large artifacts efficiently

Keep small manifests and state files directly readable. Store large response
bodies, rendered pages, extracted documents, and repeated payloads as
content-addressed artifacts within the execution directory. Events reference
those artifacts by typed relative paths and hashes; they do not duplicate large
bodies or embed binary data as base64.

Deduplicate identical artifacts within one execution so the directory remains
self-contained after copying. Compress large text artifacts and finalized event
streams with a deterministic, widely supported format. Prefer appendable
segments while recording and compact them once at finalization rather than
rewriting the complete transcript after every event.

## Rotate bounded raw storage safely

- Make the total raw-recording quota configurable and keep its default in the
  runtime configuration source of truth.
- Serialize rotation per storage root with a filesystem lock, database lease,
  or equivalent coordinator. Per-execution writers may remain concurrent.
- Measure complete execution directories, including artifacts. Rotate whole
  finalized directories in oldest-finalized order until usage is within quota.
- Never delete an active, temporary, locked, promoted, or currently replayed
  execution. Recheck lifecycle state after acquiring the rotation lock.
- Use atomic rename or tombstone-before-delete so crashes cannot leave a
  recording that still appears valid while missing files.
- Define and test the oversized-execution policy. Whether the newest complete
  execution is retained or rejected must be explicit and observable.
- Emit structured rotation results: bytes before and after, selected execution
  identities, skipped active recordings, and failures. Telemetry does not
  replace storage-state assertions in tests.

## Replay through production orchestration

Load a single directory, validate schema compatibility, relative paths, hashes,
snapshot identity, lifecycle completeness, and artifact availability, then
install recorded adapters only at mutable external boundaries. Invoke the same
public dispatcher, command handler, or service endpoint used in production.

Block live network, provider, repository, model, browser, clock, and publication
fallbacks unless the replay explicitly supplies a controlled fake for that
boundary. Match every request structurally, return the next recorded result,
and fail on an unexpected, duplicated, reordered, or unconsumed interaction.
Compare terminal output, canonical state, durable effects, usage, and failure
classification with explicit expectations.

For an external browser or research sidecar, record both its API transcript and
the provider/browser boundaries it consumed. During replay, run the real sidecar
logic against recorded search responses, navigation responses, redirects,
document bodies, and extraction inputs. Do not replace the whole sidecar with
its final returned JSON when its internal processing is part of the contract.
Isolate large sidecar fixture replays in separate processes when runtime caches
or DOM objects would otherwise accumulate across fixtures.

## Promote a recording into CI

1. Finalize the raw execution and validate its manifest and hashes.
2. Replay it successfully from its raw directory with all live external access
   blocked and exact interaction consumption enabled.
3. Copy the whole self-contained directory into the committed fixture root.
   Promotion must not rewrite semantic content or leave references outside the
   copied directory.
4. Give the fixture a stable behavior-oriented name and add machine-readable
   quality expectations for commands, terminal states, canonical outcomes,
   required evidence or effects, and bounded usage where relevant.
5. Add a focused test for the repaired rule and a sensitivity proof. Keep both
   because the focused test diagnoses the rule while the session replay protects
   orchestration.
6. Make the normal CI gate discover every promoted fixture automatically and
   fail when a fixture lacks expectations, cannot replay, accesses live
   infrastructure, or leaves an interaction unconsumed.

Keep raw rotating recordings and committed fixtures in different roots. Raw
storage is operational and disposable according to retention policy; promoted
fixtures are reviewed test data. Promotion should be equivalent to copying one
directory plus adding explicit expectations, not running a bespoke extractor.

## Preserve incidents honestly

A successful baseline fixture must reach and validate its public terminal
result. A pre-fix incident recording may intentionally diverge earlier after a
repair changes the required request or state transition. In that case, assert
the exact repaired boundary and pair it with focused post-fix coverage; do not
claim that the old transcript proves the new post-fix terminal behavior.

When a recording lacks the events needed to continue after the repaired
boundary, keep it as an incident-session regression and obtain a new complete
recording for the post-fix baseline. Never fabricate the missing model, tool,
provider, or browser response.

## Test the recorder and lifecycle

Cover event ordering, atomic finalization, interrupted sessions, schema and hash
rejection, concurrent executions, duplicate events, writer retry idempotency,
quota boundaries, active-recording protection, deterministic victim order,
rotation failure recovery, artifact deduplication, compression round trips,
promotion self-containment, network blocking, exact consumption, and sidecar
replay isolation. Use temporary storage and controllable coordination
primitives; do not prove concurrency or rotation with sleeps.
