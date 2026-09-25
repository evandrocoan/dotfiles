---
name: test-quality
description: >-
  Create, modify, run, review, debug, or improve automated tests that must fail for the right
  reason. Use for unit, integration, end-to-end, regression, smoke, live, paid, async, mocked,
  recorded-replay, or data-backed tests; complete test-suite execution; continuous replay
  recording, retention, rotation, promotion, and CI fixture design; test-related code review;
  false-positive audits; flaky-test investigation; assertion design; and any code change that
  adds, modifies, or executes tests.
---

# Test quality

Make every test prove one deterministic behavior through an observable result. Treat a passing
test as evidence only when the same test would fail after the behavior under test is broken.

## Establish the contract

1. Read the repository instructions and authoritative CI configuration.
2. Identify the system under test, the behavior being claimed, and the observable result controlled
   by that behavior.
3. Define one exact expected outcome for each test case before writing assertions.
4. Parameterize genuinely different scenarios. Never branch inside one test to accept multiple
   outcomes.

## Build deterministic arrangements

- Seed every required record, relationship, file, clock value, identity, and scope explicitly.
- Fail fixture setup when required data is absent. Never make an assertion conditional on whatever
  data happens to exist.
- Do not select an arbitrary production-like record when the expected properties matter. Create a
  record with those exact properties and remove it during teardown.
- Keep randomness, time, network responses, model output, and database state controlled or
  represented by explicit fixtures.
- Assert an exact fixture value when the fixture defines it. Use membership assertions only when
  the closed domain itself is the behavior under test.

## Exercise real behavior

- Call the real system under test. Mock only external, nondeterministic, slow, or failure-injection
  boundaries.
- Never mock the system under test or the business rule being verified.
- Do not use a configured mock return value as the sole evidence. Also assert the real
  transformation, routing decision, persisted state, emitted request, or other behavior performed
  by the system under test.
- If a test returns a fixed mock payload and compares the response with that payload, count it as
  evidence only for independently asserted behavior in the real code, such as parameter mapping or
  serialization. Name that narrower boundary; the comparison does not prove the mocked query,
  authorization decision, or persistence.
- Verify both the expected boundary interaction and the resulting state when orchestration is the
  behavior under test.
- Exercise orchestration through the production entry point or a production function actually used
  by it. Never reconstruct its decisions, transaction sequence, or writes in a test helper and
  treat that helper's success as evidence for the application's flow.

## Preserve integration fidelity

- State the tested boundary. Real queries against a real database prove query integration; direct
  handler calls prove component integration. Neither proves application startup, route wiring,
  middleware, or HTTP parsing. When the claimed behavior depends on that complete boundary, start
  the application through its supported entry point and send requests through the real transport.
  Keep focused component tests alongside that coverage; not every query test needs a running app.
- Build disposable integration databases with the application's authoritative schema setup,
  normally its real migration chain, including required schemas, types, constraints, and triggers.
  Do not handcraft, copy, or simplify application tables in test code, helpers, or SQL files as a
  substitute. Running a real database engine does not make an invented schema faithful.
- Fixture helpers prepare explicit scenario data in that schema. Raw SQL for seeding, assertions,
  or synchronization is acceptable; relocating copied DDL does not repair schema divergence. For a
  migration test, establish the prior schema through the authoritative migration history before
  exercising the target migration; applying only that migration to invented predecessor tables
  does not prove upgrade compatibility.
- A deliberately permissive schema is allowed only for a focused defensive test whose subject is
  handling an invalid state that the real schema prevents. Explain the exact departure and its
  purpose, keep it isolated, and do not count it as production-schema integration coverage. Retain
  faithful coverage for valid application behavior.
- If authoritative schema setup fails or is unavailable, report that failure or coverage gap.
  Never replace it with a reduced schema, disable integrity rules, or skip a required integration
  test to make the suite pass.

## Verify authorization decisions

- Pair permitted scenarios with separate denials for each independent gate, such as operation
  permission, privileged role, and tenant or organization scope. Keep the other gates satisfied so
  each case fails for its intended reason.
- Assert the exact denial and absence of protected reads, writes, or external effects. Checking that
  a permission helper was called does not prove its negative result was enforced. A test for a gate
  must fail if production ignores that gate while still calling the helper.

## Replay recorded failures when possible

When designing or modifying an always-on recording system, replay storage,
retention and rotation, fixture promotion, replay sidecars, or replay CI gates,
read [references/recorded-replay-lifecycle.md](references/recorded-replay-lifecycle.md)
completely before acting. Keep repository-specific commands, directories,
schemas, environment variables, and defaults in that repository's authoritative
code and documentation.

Classify recorded regressions by the boundary they reproduce:

- **Recorded-artifact replay:** Feed a sanitized payload captured from a real failure into the
  narrowest production boundary that mishandled it, such as a parser, canonicalizer, validator, or
  state transition. Use this when the artifact is sufficient for the local defect but the complete
  session is unavailable. Preserve the malformed or provider-specific shape that triggered the
  defect and label the test as an artifact replay, not a session or end-to-end replay.
- **Recorded-session replay:** Replay the ordered inputs, provider responses, tool calls and
  results, state transitions, and terminal observation through the same public orchestration
  boundary used in production. Add this level whenever the recorded transcript is sufficient to
  reach the failing boundary without live network access.

Apply these rules to both levels:

- Add focused unit coverage for the repaired rule even when a replay exists. When a complete
  session exists, keep both the focused regression and the session replay because they diagnose
  different failure scopes.
- Treat a recording as sufficient only for the level whose required inputs and observations it
  contains. If session data is incomplete, state what is missing and create the strongest
  recorded-artifact replay available instead; do not claim a complete replay.
- Preserve behaviorally relevant envelope shapes, ordering, tool calls, usage fields, malformed
  outputs, and terminal data. Remove credentials and unrelated content without normalizing away
  the defect.
- Stub only mutable external effects. Keep every production control-flow layer inside the declared
  replay boundary real.
- Assert the observable outcome and the critical state transition that previously failed. Include
  a negative control or equivalent sensitivity proof showing that the replay fails when the repair
  is absent.
- Reuse and extend an existing fixture when it already represents the same artifact or session.
  Use the repository's replay marker or suite convention when one exists, and keep deterministic
  replays in the normal CI gate. Reserve live provider tests for separate smoke coverage.
- Fail on every unexpected, duplicated, or unconsumed recorded interaction. Preserve strict order
  across causal dependencies and any sequence whose order is part of the contract. Match causally
  independent concurrent interactions by authenticated identity and multiplicity rather than
  completion order, and consume each recorded response and tool result exactly once.
- Block live network access during deterministic replay and fail if code attempts to fall back to
  an unrecorded provider, repository, clock, or other external service.

## Control paid and live validation

- Treat a request to run a named test, all tests, the full test suite, CI-equivalent tests, or
  equivalent wording as authorization for every repository-defined test selected by that request.
  This includes live or provider-paid tests and documented test-owned setup and teardown that
  creates, resets, recreates, or deletes disposable test resources such as a test tenant.
- Never require the user to mention provider cost, disposable resource recreation, or other
  documented test effects separately. The request to execute the test already authorizes effects
  that are part of that test's authoritative contract.
- Do not omit a repository-defined test because it costs money, uses a live service, or mutates its
  documented disposable fixture. Report its measured cost and effects after execution when they
  are observable.
- This authorization does not include deployment, release, promotion, production mutation, or
  another CI job that is not a test. Ask before an operation that is outside the documented test
  contract or targets a shared, non-disposable, or production resource.
- Run paid validation scenarios sequentially: wait for one scenario to reach a terminal outcome
  before starting the next. This rule does not reduce normal production concurrency.

## Test concurrency and resilience

- Cover idempotency, bounded retries, timeouts, cancellation, duplicate delivery, and partial
  failure whenever the production path implements those behaviors.
- Coordinate concurrent tests with barriers, events, fake clocks, or controllable executors. Do not
  use arbitrary sleeps as proof of ordering or race safety.
- Drive competing operations through the production flow. Keep its lock acquisition, revalidation,
  transaction, and writes real. Mock invocation order alone does not prove completion order: verify
  that a dependent read or write cannot proceed until the awaited lock or operation completes.
- Assert both the terminal result and durable side effects. Verify that duplicate or retried work
  does not publish, persist, charge, or mutate more than the contract permits.
- Force each recoverable and terminal failure at its real boundary. Assert retry count, backoff
  scheduling when observable, state preservation, and the absence of retry after a deterministic
  rejection.

## Use property tests for invariants

- Use property-based or deterministically generated cases when parsers, canonicalizers, validators,
  serializers, or state machines must preserve an invariant across many input shapes.
- State the invariant explicitly, such as round-trip equivalence, idempotence, monotonic state
  progress, stable identity, or rejection without mutation. Do not treat random execution without
  an invariant as meaningful coverage.
- Keep generation reproducible and retain the smallest failing example reported by the framework
  as a regression fixture when it represents a distinct production risk.
- Exercise valid, malformed, boundary, and composition cases. Combine property tests with concrete
  examples that document important known failures.
- Follow the repository's dependency policy before introducing a property-testing library. Prefer
  an already supported framework; otherwise use deterministic parameter generation until a
  dependency choice is approved.

## Distinguish telemetry from behavior

- Treat log, metric, and trace assertions as evidence only of the telemetry emitted. A queue name,
  route, identifier, or outcome recorded in telemetry does not prove that the system used that
  value or performed that behavior.
- When the claim concerns application behavior, assert the real boundary interaction, state
  transition, return value, or failure contract. If observability also matters, assert the
  telemetry separately.
- Use telemetry as the sole subject only when its structured fields or message are an explicit
  operational, audit, or compliance contract. Prefer stable structured fields over exact prose
  unless a consumer depends on the text.

## Remove obsolete tests with obsolete code

- Treat tests as evidence of an authoritative product contract, not as an independent reason to
  preserve production code.
- Never retain a retired implementation, fallback, compatibility branch, transport, parser, or
  adapter solely because an existing test exercises it.
- When an architecture or behavior is intentionally replaced, identify the observable contract
  that remains. Rewrite tests against the replacement contract and delete tests that only freeze
  the retired implementation.
- Remove obsolete production paths and their implementation-specific tests in the same change.
  Preserve shared primitives only when active production code still consumes them.
- Require an explicit product, protocol, migration, or compatibility requirement before keeping a
  legacy path. Test existence alone does not establish such a requirement.
- If an old test fails because an intentional replacement removed its subject, do not weaken the
  new design or add a dormant adapter to make the test pass. Correct or remove the stale test.

## Write assertions that can fail meaningfully

- Require at least one explicit behavior or state assertion, `raises` expectation, or equivalent
  framework matcher in every test.
- Reject tautologies such as `assert True`, self-comparisons, truthy literals, and assertions that
  merely prove an exception variable exists inside its own handler.
- Reject conditional expectations such as `if result: assert A; else: assert B`, `assert A or B`,
  or a broad set of accepted values when the arrangement determines one value.
- For a successful no-op or validator, assert its exact return contract and a relevant unchanged
  boundary or state. Pair it with rejection tests for invalid input.
- Assert complete response envelopes when downstream code depends on them. Do not accept several
  incompatible shapes through adaptive parsing.
- Prefer precise values and state transitions over only checking type, truthiness, non-emptiness,
  or lack of an exception.

## Handle exceptions explicitly

- Use the framework's exception matcher with the narrowest expected exception type and, when
  stable, the meaningful message or error code.
- Never use broad `Exception` or `BaseException` expectations for a specific failure contract.
- Never catch and ignore unexpected exceptions in a test. If an exception is incidental to driving
  another behavior, catch only the documented expected type.
- Ensure the test fails when an expected exception is not raised.

## Validate async behavior

- Await every coroutine or return the promise according to the framework contract.
- Assert the resolved value or resulting state, never the coroutine or promise object's truthiness.
- Treat un-awaited-coroutine warnings, pending tasks, and background exceptions as failures.
- Await async mocks and assert their awaited arguments when the boundary interaction matters.

## Control skips and flaky tests

- Require every skip or expected failure to name the unavailable capability or known defect through
  a precise, reviewable condition. Never skip because setup failed or because the result was
  inconvenient.
- Use strict expected failures so an unexpected pass fails the suite. Remove the marker when its
  condition is resolved.
- Do not add test-level retries for deterministic product behavior. Permit retry only for a
  confirmed external infrastructure failure, keep it visible in the result, and retain a
  non-retried deterministic test for the product contract.
- Treat intermittent failures as defects to reproduce and fix. If temporary quarantine is
  unavoidable, keep the test visible, state the removal condition, and do not count it as passing
  coverage.
- Report skips, expected failures, retries, and quarantined tests separately from passes.
  Investigate any unexpected change in those outcomes.

## Audit for false positives

For a project-wide false-positive audit, search all test roots. For a focused test change, inspect
the affected tests and the production path they claim to cover. Review candidates for:

- constant assertions, self-comparisons, and exception-variable tautologies;
- test functions with no direct or delegated validation;
- branches, alternative-result assertions, adaptive response parsing, and silent skips;
- broad `try`/`except`, `try`/`catch`, `raises(Exception)`, and suppression contexts;
- mocks or monkeypatches applied to the system under test;
- handcrafted application schemas or copied orchestration inside integration fixtures and helpers;
- integration claims broader than the production boundaries actually exercised;
- authorization checks with no isolated denial case or no assertion against forbidden effects;
- assertions that only repeat a mock's configured value;
- async calls without `await` or returned promises;
- fixtures that query arbitrary existing data instead of creating exact data.

Use syntax-tree analysis when available, but review every candidate against the real implementation
before declaring it defective. Helpers may contain legitimate delegated assertions, and boundary
mocks may be correct for orchestration tests.

## Prove test sensitivity

Before trusting a new or rewritten test, identify its claim, the real production path exercised,
the mocked boundaries, an observation independent of configured mock returns, and a plausible
defect that should make the test fail. If the test only checks its mock's configured result or
cannot fail for the claimed defect, narrow its claim or strengthen the test before counting it as
protection. Record what remains unproved by its boundary.

When safe and practical, run a temporary negative control by changing the observed value,
injecting the wrong boundary result, or locally mutating the relevant behavior. Restore temporary
changes immediately and verify that the unmodified implementation passes. When a negative control
cannot run, explain why and name the specific defect the existing assertion would detect; do not
present an untested sensitivity claim as measured evidence.

Do not weaken an assertion merely to make a failing test green. Fix missing fixture data, the
implementation, or the expectation according to the contract.

## Validate completely

1. Run the narrowest relevant test while iterating.
2. Run formatting, lint, type checks, unit tests, integration tests, smoke tests, and every other
   test or required non-deployment quality check in the repository's complete CI gate after the
   final test change. When the user asks for all tests, execute every repository-defined test suite,
   including live and paid suites, under the authorization contract above. Deployment, release,
   and promotion jobs are not tests.
3. Use the repository-prescribed environment and commands; do not substitute host tools for
   containerized or locked tooling.
4. When the repository defines an official containerized test workflow, use it
   instead of treating host execution as equivalent. If host execution fails
   because of native bindings, permissions, runtime differences, or package
   mismatches, run the documented containerized suite before reporting
   verification complete.
5. Do not treat image builds, type checks, lint, or smoke checks as substitutes
   for the prescribed automated tests.
6. Report exact pass, fail, skip, and blocked results. Distinguish product failures from
   infrastructure, quota, credential, or dependency failures.

## Review test evidence before closure

For each added or materially changed test, check that its claimed behavior, exercised production
boundary, independent observation, and sensitivity evidence agree. A passing suite cannot fill a
gap between a routing test and a database, authorization, or startup claim. Report the narrower
coverage and add the missing test when that broader behavior is part of the requested contract.

Obtain a fresh-context independent review for a project-wide false-positive audit or when changed
tests are primary evidence for behavior classified as high risk by `plan-implementation`, including
authorization, destructive state changes, and data integrity. A focused routine test change needs
the author check above, not automatic delegation. Reuse an independent plan or closure review when
it examines the final tests against this section; do not duplicate a qualifying review. Honor a
user-requested reviewer and effort, such as Astra xhigh. Otherwise choose the strongest available
independent reviewer suited to the risk. If the preferred model is unavailable, use another capable
independent reviewer and disclose the substitution. If no independent reviewer is available for a
required review, keep that requirement unresolved and do not claim completion.

Give the reviewer the request, applicable instructions, tests, real implementation, relevant
fixtures, CI route, and validation and negative-control results. Withhold the intended verdict and
prior candidate classifications. For a broad audit, ask the reviewer to inspect every test root
for the patterns above and verify each candidate against the real implementation. Require file and
line, false-positive mechanism, actual behavior to observe, and corrected code for confirmed
findings; distinguish valid boundary mocks and state which categories produced no confirmed issue.
Resolve findings, rerun checks invalidated by changes, and repeat the review if the reviewed test
evidence changes materially.

## Report audit findings

For every confirmed issue, provide the file and line, the false-positive mechanism, the real
behavior that should be observed, and a corrected snippet. Separate confirmed defects from reviewed
candidates that are valid. State explicitly when no issue is confirmed in one of the audit
categories.
