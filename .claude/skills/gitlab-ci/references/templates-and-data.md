# Templates and pipeline data

## Treat shared configuration as versioned executable code

Prefer a CI/CD component with typed inputs for a reusable, product-like unit. Use project or local includes when the
repository layout or GitLab instance does not support a component cleanly.

- Pin external components and project includes to a protected release tag. Do not consume `main`, `master`, or another
  moving ref in production pipelines.
- Review the included source and its transitive includes before granting it secrets or a privileged runner.
- Use semantic release tags and an intentional update process. Test the release tag before moving consumers to it.
- Use `spec:inputs` for typed, validated, compile-time configuration. Give defaults to inputs used by automatically
  created pipelines; otherwise pipeline creation can fail before any job exists.
- Keep runtime secrets and values that must be changed during execution in CI/CD variables or an external secret
  provider, not in inputs.
- Give reusable jobs collision-resistant names or configurable prefixes. Included configuration merges into the
  consumer's configuration and can overwrite or be overwritten.
- Assign one explicit owner for global keys such as `workflow`, `stages`, `default`, and top-level variables. An
  included template that defines them changes the whole consumer pipeline, not only its own jobs.
- Do not require every consumer to rediscover and duplicate an undocumented stage list. Expose configurable stage
  names through typed inputs where supported, or version and validate the exact consumer contract.

Authoritative references: [CI/CD components](https://docs.gitlab.com/ci/components/) and
[CI/CD inputs](https://docs.gitlab.com/ci/inputs/).

## Reuse YAML without hiding ownership

- Prefer `extends` for reusable job maps and components or inputs for public template contracts.
- Use YAML anchors only inside one file; anchors do not cross include boundaries.
- Remember that maps can merge while arrays such as `script`, `rules`, and `tags` are commonly replaced. Inspect the
  merged configuration instead of assuming a deep merge.
- Use `!reference` sparingly for selected sections. Prefer component inputs when the consumer should configure the
  template through a supported interface.
- Keep hidden jobs focused. A hidden job that mixes runner selection, credentials, checkout, rules, and scripts makes
  inheritance order difficult to audit.

Authoritative reference: [GitLab YAML optimization](https://docs.gitlab.com/ci/yaml/yaml_optimization/).

## Separate artifacts, reports, and caches

Use artifacts for outputs produced by one job and consumed or presented as results of that pipeline. Use cache for
reusable downloads or generated dependency state whose correctness does not depend on one exact producer execution.

For artifacts:

- bind consumers to the intended producer with `needs:artifacts`, `dependencies`, or the appropriate cross-pipeline
  mechanism;
- when using `needs`, select artifacts on that edge and do not also configure `dependencies` in the consumer;
- set retention and access to the minimum operational need;
- expose machine-readable outputs through the applicable `artifacts:reports` contract;
- treat expiration, download failure, or malformed content as missing evidence, not an empty result;
- avoid downloading all prior-stage artifacts when a job needs only one producer.

For caches:

- derive keys from lockfiles, platform, runtime, and other inputs that affect compatibility;
- separate protected and unprotected cache writers;
- use pull-only consumers when one controlled job owns publication;
- never place credentials, security reports, release artifacts, or uniquely authoritative results in cache;
- make a cache miss slower, not semantically incorrect.

Authoritative references: [GitLab cache](https://docs.gitlab.com/ci/caching/) and
[job artifacts](https://docs.gitlab.com/ci/jobs/job_artifacts/).

## Preserve identity across projects and merge requests

A downstream consumer must identify the exact upstream project, pipeline, job, commit, and merge request context it
uses. For merge request pipelines, the ordinary branch ref can select the wrong artifact; use the MR pipeline ref or
an exact pipeline/job identity supported by the chosen transfer mechanism.

Use native cross-pipeline artifact support and job-token allowlists when available. If an API download is necessary,
authenticate the expected caller, paginate list endpoints, select the job unambiguously, verify its status, and reject
multiple or missing matches. Never choose an artifact merely by the latest branch pipeline.

## Prefer Runner checkout controls

Use GitLab Runner's checkout model before implementing a custom clone:

- select `GIT_STRATEGY` according to whether the job needs a working tree;
- control main repository and submodule depth independently;
- use the built-in recursive submodule strategy when required;
- synchronize submodule URLs and credentials through supported controls;
- use `GIT_STRATEGY: none` only for jobs that truly consume no repository content.

Custom clone logic is exceptional. If evidence requires it, keep retries bounded, fetch the exact commit, isolate the
workspace, avoid shell tracing and credential output, and never broadly delete a persistent runner directory. Do not
disable host networking features or fork the runner as a routine clone workaround.

Authoritative reference: [GitLab submodules](https://docs.gitlab.com/ci/runners/git_submodules/).
