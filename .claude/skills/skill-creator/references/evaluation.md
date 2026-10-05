# Evaluate a shared skill change

Use this procedure when creating, changing, or measuring a locally maintained shared skill.
Use the owning repository's [test operations](../../../../README.md#shared-skill-tests) for commands
and the [suite source](../../../../scripts/skill_tests/) for its supported clients and schemas.

## Choose evidence for the change

Identify the instruction owner and affected consumers through
[Validate coupled documentation](../../documentation/SKILL.md#validate-coupled-documentation).
Run the local structural checks for metadata, links, anchors and shared aliases. Investigate
repeated-prose alerts in context: identical text may govern different scopes, and different
wording may still contradict the same rule. The checker does not establish semantic consistency.

For a behavioral change, select focused scenarios that expose the changed decision. Include a
positive case, a plausible wrong outcome, and relevant edge cases. When changing discovery or
description text, include natural requests that should trigger the skill and near misses that
should not. Keep some scenarios outside prompt tuning and label their execution status honestly.
A wording-only correction does not by itself require a paid matrix.

Apply [test quality](../../test-quality/SKILL.md), including its live authorization, replay and
closure rules, rather than creating a second set of general testing policies here. Select any
plan and independent reviews through [plan implementation](../../plan-implementation/SKILL.md).

## Freeze the experiment

Describe the requested behavior and forbidden actions in evaluator criteria before inspecting
answers. Keep the task, fictional fixtures and skill source visible to the model; keep criteria,
other answers and grades outside its workspace. Capture the exact sources, client/model/effort,
case IDs, order, repetitions and attempt limit in the sealed protocol.

For a version comparison, preserve equivalent fixtures and criteria and counterbalance the
version order. Use fresh sessions. A current-version smoke round does not establish improvement
over an earlier version. Reuse failures as regressions without erasing the original outcomes.

Before real calls, verify the concrete client boundary, effective instruction catalog, evidence
capture and any selected review. The suite's digests prove input identity; passing them to a CLI
does not grant authorization. Its initial read-only profiles are not a full operating-system
sandbox. Unavailable observation or isolation controls leave live validation pending.

## Evaluate separate observations

Record discovery, source receipt, application, actions and technical validity separately:

- A discovered skill is not necessarily read. A command's complete output may exceed what the
  model actually received. Attribute delivered spans to their authenticated request and source.
- Receiving every rule is not proof of following it. Grade the answer against each frozen
  criterion with concrete quotations and a reason. Missing evidence remains unassessable.
- Inspect tool attempts as well as effects. A forbidden write denied by the client is still an
  attempted violation. A read-only assessment does not prove safe implementation.
- Keep authentication, schema, identity and process failures separate from behavioral failures.
  Retain missing cells and every attempted call in the denominator.

Use [recorded-artifact replay](../../test-quality/SKILL.md#replay-recorded-failures-when-possible)
to check client-output parsers offline. Synthetic controls and captured-output fixtures validate
the suite boundary; they are not new observations of model behavior.

## Deliver and maintain

Run the applicable local gate and report exact pass, failure, ungraded and unstarted results.
Keep raw traces private and export only inspected fields. Version reusable cases, criteria and
sanitized fixtures in the suite; leave run directories, authentication and private traces outside
Git. Complete selected reviews before their dependent phase.

When a model fails, first distinguish missing instructions, ambiguous guidance, wrong application,
and an invalid experiment. Change the responsible skill only within the user's authorized scope.
Freeze a new experiment before evaluating a correction; preserve prior failures and do not turn
additional calls into implicit retries. Report sample size and unexecuted coverage with the result.
