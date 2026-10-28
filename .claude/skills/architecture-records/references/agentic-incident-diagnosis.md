# Agentic incident diagnosis

Use this procedure for recurring lost results, excessive work, or disputed model failures when
deciding whether an LLM-based system needs an architectural correction. Inspect only the affected
path and its material consumers. Keep incident evidence in its existing execution or evaluation
artifact; the procedure does not require another report or architecture record.

## Locate the first demonstrated divergence

Establish the intended user-visible result and the exact revision and environment behind each
observation. Do not combine an old checkout, current source, and deployed behavior into one claim.
Reconstruct the relevant path from original structured inputs and outputs:

```text
available input -> delivered context -> model/tool decision -> validation and state -> delivery
```

At each relevant boundary, distinguish what was available, requested, returned, delivered, accepted,
and consumed. Locate the first demonstrated departure from the intended behavior; keep earlier
unknowns explicit. A source file present on disk is not proof the model received it, and an alias
mentioned in a trace is not proof another candidate was processed. Check the actual collection or
request before inferring work from an identifier or log phrase.

Separate wrong or incomplete judgment from orchestration that prevented investigation, truncated
context, rejected an otherwise supported result, or lost it during persistence or publication.
Allow mixed causes. Before blaming the model or increasing its effort, verify its actual tools,
permissions, instructions, delivered facts, and remaining resources. A successful investigation
with extra capabilities does not establish that the original model could have done the same.

## Trace unnecessary work to its cause

For a cost or latency incident, account for the affected stages, physical attempts, retries,
recovery, repeated reads, independent passes, and work discarded before delivery. Inspect context
growth and cache behavior when they explain the observed work. Distinguish necessary investigation
from repeated acquisition or bookkeeping. Exhausting a configured budget explains termination,
not why the work consumed that budget or whether it was useful.

Treat a suspected mechanism as a hypothesis until the relevant requests, state transitions, or
controlled comparison support it. A repair that was never exercised cannot explain a later good
result. When evidence disproves a diagnosis, remove its proposed correction rather than retaining
it as precautionary architecture. State what remains unknown instead of inventing a causal share
of cost or a guarantee that raising limits will recover quality.

## Choose the smallest correction that preserves the contract

First check whether the native agent, existing tool, or current consumer already owns the needed
capability. Before adding a controller, classifier, protocol field, blocking validator, or model
pass, identify the concrete missing behavior and why the existing mechanism does not supply it.
Compare fixing the faulty boundary, reusing the existing decision, and introducing a new layer.

Keep objective identity, authorization, resource accounting, and state enforcement in code.
Semantic relevance, causal reasoning, and defect judgment belong at the appropriate semantic
decision boundary. Correcting that boundary need not add another model call: remove an unsupported
lexical veto or preserve an existing judgment when that resolves the demonstrated defect. Conversely,
do not ask a model to deduplicate identical canonical IDs or repair deterministic rendering.

For each proposed requirement, connect the protected fact to its actual consumer and examine its
effect on unrelated useful results, calls, tokens, and latency. Derive application-owned IDs and
bookkeeping in code rather than making the model restate them. Invalid evidence that a conclusion
depends on must prevent that unsupported conclusion; an unused observation should not veto
independent supported work unless a real command-wide safety boundary requires it. Preserve
necessary authentication, authorization, and resource safeguards when simplifying.

## Verify the changed boundary and delivered result

Apply the entrypoint's incident classification to decide whether to fix implementation under an
existing invariant or amend the architectural contract. Do not rewrite the contract just to
legitimize the current defect. Preserve already valid independent results through the correction.

Use `test-quality` to select the regression and replay boundary. Pair a local restriction repair
with cases that distinguish valid consumed evidence, invalid consumed evidence, and irrelevant
unused evidence when that dependency is material. For claims about new model decisions, useful
outcomes, or savings, read
[LLM outcome evaluation](../../test-quality/references/llm-outcome-evaluation.md). Passing internal
checks or finding no technology-specific conditionals is insufficient evidence of product quality.
