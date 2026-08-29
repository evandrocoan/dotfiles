# Pipeline design

## Start with a source matrix

Write down the expected pipeline and job behavior for every source the project actually uses. At minimum, consider
merge requests, branch pushes, tags, schedules, manual/API runs, and child or multi-project triggers. Add protected
and fork contexts whenever credentials or privileged runners exist.

Evaluate admission in this order:

1. `workflow:rules` decides whether the pipeline exists.
2. Each job's first matching `rules` entry decides whether and how the job exists.
3. `needs`, stages, manual gates, and environments decide when an admitted job can run.

Do not diagnose a missing job until confirming that the pipeline itself was admitted. Do not add a broad final
`when: always` rule without proving which additional sources it admits.

## Avoid duplicate branch and merge request pipelines

For repositories that switch from branch pipelines to merge request pipelines after an MR opens, start from this
shape and adapt it to the source matrix:

```yaml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS && $CI_PIPELINE_SOURCE == "push"'
      when: never
    - if: '$CI_COMMIT_BRANCH'
```

The explicit `push` condition matters when triggered pipelines also carry a branch variable. Add tag, schedule, web,
or downstream rules only when the project intends those sources. A configuration that requires successful MR
pipelines must not use workflow rules that prevent every MR pipeline from being created.

Pair `rules:changes` with an `if` condition that limits the applicable pipeline sources. Changes can have surprising
truth values when a source has no ordinary push comparison. Use `compare_to` when the desired baseline is explicit.

Authoritative reference: [GitLab workflow](https://docs.gitlab.com/ci/yaml/workflow/).

## Model the DAG explicitly

- Use stages as broad lifecycle and policy boundaries.
- Use `needs` when a job depends on specific producers and can start before the entire prior stage finishes.
- Use `needs: []` only when the job is intentionally independent at pipeline creation.
- Mark a need optional only when its producer is legitimately absent in some validated rule scenarios.
- Keep artifact transfer explicit on each need. Scheduling dependency and artifact dependency are related but distinct.
- Detect cycles and jobs whose needs can never coexist under their respective rules.
- Use parallel matrices for genuine variants, not copy-pasted jobs with drifting policy.

Do not serialize unrelated work merely because it belongs to the same stage. Do not create a DAG that bypasses a
required quality, approval, or deployment gate.

Authoritative reference: [GitLab DAG and needs](https://docs.gitlab.com/ci/yaml/needs/).

## Make special job behavior explicit

- For manual jobs, set both `when` and `allow_failure` deliberately. Verify whether the pipeline must wait for the job.
- Use `resource_group` to serialize mutations of one environment or other exclusive resource.
- Use `interruptible` and workflow auto-cancel only for work that is safe to abandon when superseded.
- Retry only classified transient failures. Never retry deterministic test, policy, or syntax failures to obtain green.
- Set timeouts around external tools and services, and preserve their useful diagnostic output.
- Keep packaging independent from tests only when artifact generation itself is useful. Require the intended test and
  security jobs before promotion, release, or deployment.
- Use environments and protected deployment controls for deployment authorization; a job name is not a gate.

## Design downstream pipelines as contracts

Choose child pipelines for configuration decomposed within one project and multi-project pipelines for separately
owned pipelines. Define:

- the exact inputs and metadata sent downstream;
- which variables are intentionally inherited or forwarded;
- how the downstream authenticates the caller and accesses upstream data;
- which pipeline and commit own every artifact;
- how cancellation and status propagate;
- what the upstream reports if the downstream cannot start or finish.

Use `strategy: mirror` when the trigger job must mirror the downstream status. Treat `strategy: depend` as legacy
behavior to retain only when the target GitLab instance or a verified report integration requires it.

Do not forward masked variables across a multi-project boundary. Prefer typed `trigger:inputs` for configuration and
an explicit `trigger:forward` or `inherit:variables` policy for the remaining variables.

Authoritative reference: [GitLab downstream pipelines](https://docs.gitlab.com/ci/pipelines/downstream_pipelines/).
