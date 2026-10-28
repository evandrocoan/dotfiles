# LLM outcome evaluation

Use this reference when the claim concerns the quality of decisions delivered by an LLM-based
system. Keep ordinary deterministic checks for its objective contracts. Select evidence for the
claim being made; a local renderer or identity fix need not trigger a new model benchmark.

## Separate the claims

Distinguish these observations in the result:

- A faithful replay verifies production orchestration against recorded external responses.
- A deterministic regression verifies an objective transformation, invariant, or failure boundary.
- A fresh outcome evaluation observes decisions made by the selected model and prompt under the
  tested tools, context, configuration, and execution path.

A passing replay with fixed model responses cannot establish improved judgment by a new prompt or
model. A fresh run that bypasses the changed path cannot validate that repair. Preserve useful
replay evidence, but leave unsupported quality claims unverified instead of expanding their scope.

## Establish independent expectations

Freeze each case's requirements, source revision, expected useful outcomes, and unacceptable
outcomes before grading answers. Base them on verified behavior, requirements, or independently
examined evidence. A previous model verdict, fixture name, author assertion, or reviewer agreement
alone is not ground truth. A behavior change becomes a defect only when its trigger and consequence
violate the intended contract; difference from the old implementation is insufficient.

Use stable semantic criteria for variable prose, rather than an exact sentence or the candidate's
own explanation as the answer key. Keep exact assertions for objective identities, effects, and
states. Do not broaden criteria after seeing results to accept incompatible conclusions. If a new
valid defect changes the answer key, retain the old evidence, document the correction in the
evaluation artifact, and regrade every affected comparison consistently.

Choose cases that can distinguish the claimed improvement from its plausible failure:

- Known defects with independently established triggers and consequences.
- Corrected variants and legitimate changes that should not retain the original accusation.
- Inputs verified to be clean for the stated scope, when claiming behavior on clean inputs.
- Partial or inaccessible scope, where an incomplete result must not become a clean verdict.
- Relevant wording, naming, or representation variants when overfitting is the concern.

Verify reported findings even in defect-containing cases. Those checks can establish whether the
observed findings are supported; without genuinely clean controls they do not establish behavior
on clean inputs or a general false-positive rate. Unless the expected defect inventory is complete
for a defined scope, report recovery of known defects rather than total recall or absence of bugs.

## Compare the actual systems

Identify the effective source revision, model and effort, prompt, tools and permissions, delivered
context, resource limits, and production entry point. Distinguish available source material from
what reached a completed model turn. A human or another agent with additional tools or source
access is not a controlled comparison of model capability.

When attributing an effect to one change, use comparable cases and control the other material
conditions. If comparing whole systems with different stages or transports, preserve those
differences and report a system comparison rather than a model-only causal claim. Reuse a recent
baseline when its conditions still answer the question; repeat it only to resolve a named
uncertainty. Keep some cases outside tuning and choose repetitions appropriate to observed
variability and the claim. One run per case is evidence about those runs, not reliability in
production or universal superiority.

Record the selected cases, order, repetitions, and stopping rule before execution. Retain failed,
incomplete, and ungraded attempts in the accounting. Do not silently retry until a favorable answer
appears. For shared-skill experiments, use the existing
[skill evaluation procedure](../../skill-creator/references/evaluation.md) for input isolation,
instruction receipt, frozen criteria, and grading; do not create a parallel evaluation workflow.

## Measure what reached the user

Track independently supported useful results through discovery, acceptance, persistence, and
delivery where those stages exist. Distinguish a defect never investigated, a wrong judgment, and
a valid result lost by a later consumer. Do not count aliases, repeated prose, or duplicate
publication as independent findings. Compare preserved, gained, and lost outcomes rather than
declaring improvement from a larger raw candidate count.

Report coverage and incomplete work alongside supported and unsupported results. Count the whole
scenario's calls, retries, recovery, independent passes, cost, and latency; distinguish measured
charges from estimates or unknown usage. Lower cost caused by skipping useful work is not evidence
of quality-preserving optimization. A verified partial result remains useful without implying
complete coverage. Cost attribution to a particular mechanism needs evidence beyond correlation.

## Choose proportionate validation

Pair an objective repair with its focused regression and an available faithful replay at the
affected boundary. If changed model behavior is the claimed improvement, use a proportionate fresh
evaluation or state that claim remains unverified. Apply
[paid and live validation](../SKILL.md#control-paid-and-live-validation) for authorization and
execution; this reference does not mandate an additional paid campaign for every change.

Report exactly what was executed, the tested revisions and conditions, sample size, outcomes,
unexecuted cases, and limitations. Prepared cases, source receipt, a successful tool call, and a
passing structural checker are different evidence from correct application or delivered quality.
