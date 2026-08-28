---
name: test-quality
description: Create, review, debug, or improve automated tests that must fail for the right reason. Use for unit, integration, end-to-end, regression, smoke, async, mocked, recorded-replay, or data-backed tests; test-related code review; false-positive audits; flaky-test investigation; fixture design; assertion design; and any code change that adds or modifies tests.
---

# Test quality

Make every test prove one deterministic behavior through an observable result. Treat a passing test as evidence only when the same test would fail after the behavior under test is broken.

## Establish the contract

1. Read the repository instructions and authoritative CI configuration.
2. Identify the system under test, the behavior being claimed, and the observable result controlled by that behavior.
3. Define one exact expected outcome for each test case before writing assertions.
4. Parameterize genuinely different scenarios. Never branch inside one test to accept multiple outcomes.

## Build deterministic arrangements

- Seed every required record, relationship, file, clock value, identity, and scope explicitly.
- Fail fixture setup when required data is absent. Never make an assertion conditional on whatever data happens to exist.
- Do not select an arbitrary production-like record when the expected properties matter. Create a record with those exact properties and remove it during teardown.
- Keep randomness, time, network responses, model output, and database state controlled or represented by explicit fixtures.
- Assert an exact fixture value when the fixture defines it. Use membership assertions only when the closed domain itself is the behavior under test.

## Exercise real behavior

- Call the real system under test. Mock only external, nondeterministic, slow, or failure-injection boundaries.
- Never mock the system under test or the business rule being verified.
- Do not use a configured mock return value as the sole evidence. Also assert the real transformation, routing decision, persisted state, emitted request, or other behavior performed by the system under test.
- Verify both the expected boundary interaction and the resulting state when orchestration is the behavior under test.

## Replay recorded failures when possible

Classify recorded regressions by the boundary they reproduce:

- **Recorded-artifact replay:** Feed a sanitized payload captured from a real failure into the narrowest production boundary that mishandled it, such as a parser, canonicalizer, validator, or state transition. Use this when the artifact is sufficient for the local defect but the complete session is unavailable. Preserve the malformed or provider-specific shape that triggered the defect and label the test as an artifact replay, not a session or end-to-end replay.
- **Recorded-session replay:** Replay the ordered inputs, provider responses, tool calls and results, state transitions, and terminal observation through the same public orchestration boundary used in production. Add this level whenever the recorded transcript is sufficient to reach the failing boundary without live network access.

Apply these rules to both levels:

- Add focused unit coverage for the repaired rule even when a replay exists. When a complete session exists, keep both the focused regression and the session replay because they diagnose different failure scopes.
- Treat a recording as sufficient only for the level whose required inputs and observations it contains. If session data is incomplete, state what is missing and create the strongest recorded-artifact replay available instead; do not claim a complete replay.
- Preserve behaviorally relevant envelope shapes, ordering, tool calls, usage fields, malformed outputs, and terminal data. Remove credentials and unrelated content without normalizing away the defect.
- Stub only mutable external effects. Keep every production control-flow layer inside the declared replay boundary real.
- Assert the observable outcome and the critical state transition that previously failed. Include a negative control or equivalent sensitivity proof showing that the replay fails when the repair is absent.
- Reuse and extend an existing fixture when it already represents the same artifact or session. Use the repository's replay marker or suite convention when one exists, and keep deterministic replays in the normal CI gate. Reserve live provider tests for separate smoke coverage.
- Fail on every unexpected, duplicated, reordered, or unconsumed recorded interaction. Assert that the replay exhausts its responses and tool results exactly once.
- Block live network access during deterministic replay and fail if code attempts to fall back to an unrecorded provider, repository, clock, or other external service.

## Test concurrency and resilience

- Cover idempotency, bounded retries, timeouts, cancellation, duplicate delivery, and partial failure whenever the production path implements those behaviors.
- Coordinate concurrent tests with barriers, events, fake clocks, or controllable executors. Do not use arbitrary sleeps as proof of ordering or race safety.
- Assert both the terminal result and durable side effects. Verify that duplicate or retried work does not publish, persist, charge, or mutate more than the contract permits.
- Force each recoverable and terminal failure at its real boundary. Assert retry count, backoff scheduling when observable, state preservation, and the absence of retry after a deterministic rejection.

## Use property tests for invariants

- Use property-based or deterministically generated cases when parsers, canonicalizers, validators, serializers, or state machines must preserve an invariant across many input shapes.
- State the invariant explicitly, such as round-trip equivalence, idempotence, monotonic state progress, stable identity, or rejection without mutation. Do not treat random execution without an invariant as meaningful coverage.
- Keep generation reproducible and retain the smallest failing example reported by the framework as a regression fixture when it represents a distinct production risk.
- Exercise valid, malformed, boundary, and composition cases. Combine property tests with concrete examples that document important known failures.
- Follow the repository's dependency policy before introducing a property-testing library. Prefer an already supported framework; otherwise use deterministic parameter generation until a dependency choice is approved.

## Distinguish telemetry from behavior

- Treat log, metric, and trace assertions as evidence only of the telemetry emitted. A queue name, route, identifier, or outcome recorded in telemetry does not prove that the system used that value or performed that behavior.
- When the claim concerns application behavior, assert the real boundary interaction, state transition, return value, or failure contract. If observability also matters, assert the telemetry separately.
- Use telemetry as the sole subject only when its structured fields or message are an explicit operational, audit, or compliance contract. Prefer stable structured fields over exact prose unless a consumer depends on the text.

## Remove obsolete tests with obsolete code

- Treat tests as evidence of an authoritative product contract, not as an independent reason to preserve production code.
- Never retain a retired implementation, fallback, compatibility branch, transport, parser, or adapter solely because an existing test exercises it.
- When an architecture or behavior is intentionally replaced, identify the observable contract that remains. Rewrite tests against the replacement contract and delete tests that only freeze the retired implementation.
- Remove obsolete production paths and their implementation-specific tests in the same change. Preserve shared primitives only when active production code still consumes them.
- Require an explicit product, protocol, migration, or compatibility requirement before keeping a legacy path. Test existence alone does not establish such a requirement.
- If an old test fails because an intentional replacement removed its subject, do not weaken the new design or add a dormant adapter to make the test pass. Correct or remove the stale test.

## Write assertions that can fail meaningfully

- Require at least one explicit behavior or state assertion, `raises` expectation, or equivalent framework matcher in every test.
- Reject tautologies such as `assert True`, self-comparisons, truthy literals, and assertions that merely prove an exception variable exists inside its own handler.
- Reject conditional expectations such as `if result: assert A; else: assert B`, `assert A or B`, or a broad set of accepted values when the arrangement determines one value.
- For a successful no-op or validator, assert its exact return contract and a relevant unchanged boundary or state. Pair it with rejection tests for invalid input.
- Assert complete response envelopes when downstream code depends on them. Do not accept several incompatible shapes through adaptive parsing.
- Prefer precise values and state transitions over only checking type, truthiness, non-emptiness, or lack of an exception.

## Handle exceptions explicitly

- Use the framework's exception matcher with the narrowest expected exception type and, when stable, the meaningful message or error code.
- Never use broad `Exception` or `BaseException` expectations for a specific failure contract.
- Never catch and ignore unexpected exceptions in a test. If an exception is incidental to driving another behavior, catch only the documented expected type.
- Ensure the test fails when an expected exception is not raised.

## Validate async behavior

- Await every coroutine or return the promise according to the framework contract.
- Assert the resolved value or resulting state, never the coroutine or promise object's truthiness.
- Treat un-awaited-coroutine warnings, pending tasks, and background exceptions as failures.
- Await async mocks and assert their awaited arguments when the boundary interaction matters.

## Control skips and flaky tests

- Require every skip or expected failure to name the unavailable capability or known defect through a precise, reviewable condition. Never skip because setup failed or because the result was inconvenient.
- Use strict expected failures so an unexpected pass fails the suite. Remove the marker when its condition is resolved.
- Do not add test-level retries for deterministic product behavior. Permit retry only for a confirmed external infrastructure failure, keep it visible in the result, and retain a non-retried deterministic test for the product contract.
- Treat intermittent failures as defects to reproduce and fix. If temporary quarantine is unavoidable, keep the test visible, state the removal condition, and do not count it as passing coverage.
- Report skips, expected failures, retries, and quarantined tests separately from passes. Investigate any unexpected change in those outcomes.

## Audit for false positives

Search all test roots and review candidates for:

- constant assertions, self-comparisons, and exception-variable tautologies;
- test functions with no direct or delegated validation;
- branches, alternative-result assertions, adaptive response parsing, and silent skips;
- broad `try`/`except`, `try`/`catch`, `raises(Exception)`, and suppression contexts;
- mocks or monkeypatches applied to the system under test;
- assertions that only repeat a mock's configured value;
- async calls without `await` or returned promises;
- fixtures that query arbitrary existing data instead of creating exact data.

Use syntax-tree analysis when available, but review every candidate against the real implementation before declaring it defective. Helpers may contain legitimate delegated assertions, and boundary mocks may be correct for orchestration tests.

## Prove test sensitivity

Before trusting a new or rewritten test, identify a plausible defect that should make it fail. When safe and practical, run a temporary negative control by changing the observed value, injecting the wrong boundary result, or locally mutating the relevant behavior. Restore temporary changes immediately and verify that the unmodified implementation passes.

Do not weaken an assertion merely to make a failing test green. Fix missing fixture data, the implementation, or the expectation according to the contract.

## Validate completely

1. Run the narrowest relevant test while iterating.
2. Run formatting, lint, type checks, unit tests, integration tests, smoke tests, and every other job in the repository's complete CI gate after the final test change.
3. Use the repository-prescribed environment and commands; do not substitute host tools for containerized or locked tooling.
4. When the repository defines an official containerized test workflow, use it
   instead of treating host execution as equivalent. If host execution fails
   because of native bindings, permissions, runtime differences, or package
   mismatches, run the documented containerized suite before reporting
   verification complete.
5. Do not treat image builds, type checks, lint, or smoke checks as substitutes
   for the prescribed automated tests.
6. Report exact pass, fail, skip, and blocked results. Distinguish product failures from infrastructure, quota, credential, or dependency failures.

## Report audit findings

For every confirmed issue, provide the file and line, the false-positive mechanism, the real behavior that should be observed, and a corrected snippet. Separate confirmed defects from reviewed candidates that are valid. State explicitly when no issue is confirmed in one of the audit categories.
