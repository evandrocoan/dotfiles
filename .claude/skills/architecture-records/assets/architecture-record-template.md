# Record title

**Status:** proposed; implementation has not started.

State what this record owns and make clear whether it describes intended, current, or
superseded behavior.

## Context

Describe the problem, affected boundaries, and why the decision requires a durable
cross-component record.

## Goals

- State the outcomes the architecture must produce.

## Non-goals

- State nearby behavior intentionally excluded from this decision.

## Current state

Point to the authoritative code, configuration, tests, and documentation. Describe
only the current boundaries needed to understand the change.

## Architecture

Describe ownership, data flow, state transitions, and recovery behavior. Use the
smallest useful diagram when relationships would otherwise be hard to follow.

## Failure semantics

Define bounded failure, partial-progress, retry, recovery, and terminal meanings for
every affected architectural boundary. State which owner may classify each failure
and which authenticated state must survive it.

## Invariants

1. Record the conditions that every implementation and future change must preserve.

## Implementation order

Describe the dependency order and architectural acceptance criteria. Keep
task-specific delivery tracking in the issue or merge request.

## Validation and acceptance

- Define evidence that proves the architecture is implemented completely.
- Include failure, recovery, migration, and compatibility paths where relevant.

## Traceability and conformance

Map every load-bearing invariant to its authoritative runtime owner, all affected
consumers, and proportional executable protection. Keep execution status and detailed
run evidence in the implementation plan or owning test, replay, CI, issue, or merge
request artifact.

| Invariant | Authoritative owner | Affected consumers | Tests | Recorded replay |
| --- | --- | --- | --- | --- |
| <invariant identifier> | <code or configuration owner> | <all consumers> | <focused protection> | <full, partial with boundary, unavailable, or not applicable> |

Before changing this record to `Implemented`, require the corresponding implementation
plan's completed closure audit to verify the architecture-to-implementation and
implementation-to-authority traces. A missing, pending, or unresolved applicable row
blocks the lifecycle transition.

## Rejected alternatives

| Alternative | Reason rejected |
| --- | --- |
| <plausible competing design> | <durable tradeoff or violated invariant> |

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Describe a material architectural risk | Describe the corresponding control |

## Authoritative sources

- Link to the code, configuration, tests, and user documentation that own executable
  behavior and current values.
