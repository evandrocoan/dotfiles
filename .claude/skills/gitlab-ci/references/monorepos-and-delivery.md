# Monorepos and artifact delivery

## Model the monorepo change graph

Split a large root pipeline with local includes and hidden job templates, but derive job admission from an explicit
change-impact map. For each application or package, include:

- its owned source, tests, Dockerfile, and service configuration;
- shared packages and generated interfaces it consumes;
- dependency lockfiles and workspace configuration;
- shared CI wrappers, included YAML, and tool configuration that can change the job's behavior;
- global build or release inputs whose effect spans every component.

Combine `rules:changes` with an explicit pipeline source. Verify its comparison base for merge requests, branches,
tags, schedules, and new branches; use `compare_to` where the intended baseline is otherwise ambiguous. A path filter
is a scheduling optimization, not proof that an unlisted shared file cannot affect the component.

Treat local wildcard includes as executable expansion. Check for duplicate job names and inspect the fully merged
configuration. A shared external template that owns global keys such as `workflow`, `stages`, `default`, or top-level
variables creates a consumer-wide contract. Prefer typed inputs for configurable stage or job names, or document and
validate the exact global contract.

## Build once, test, and promote the same output

The producer should create one immutable package or image candidate. Its consumers should test that exact output, and
the release job should promote it without rebuilding.

- Emit a small manifest containing the exact artifact filename, image tag, platform, and producer identity.
- Transfer artifacts through an explicit `needs` edge with artifact download enabled.
- Do not combine `needs` and `dependencies` in one job.
- Do not select a candidate with `latest`, a branch-only lookup, an unconstrained glob, or stale runner contents.
- Validate the packaged or containerized artifact itself when installation, entrypoint, permissions, or runtime
  contents are part of the contract.
- Make manual publication and deployment depend on the required tests and producer. `needs: []` starts immediately
  and is appropriate only for work that is truly independent.
- Publish from protected release tags and protected environments under the repository's tag-based policy.
- Keep convenience aliases outside the authority path; they must never decide which output is tested or deployed.

For registry publication, use standard-input authentication, an explicit build-argument allowlist, and public-only
build arguments. Never use `eval` to assemble command lines or pass secrets through Docker build arguments.

## Parallelize without losing coverage

Use `parallel`, `parallel:matrix`, or a deterministic shard index and total when suites can run independently.

- Prove that the partition is complete, stable, and non-overlapping where duplication is not intended.
- Give every shard a unique Compose project, workspace, artifact name, and diagnostic path.
- Ensure fan-in waits for every required shard and fails when any shard fails or disappears from the graph.
- Avoid same-name artifacts from parallel producers because later downloads can overwrite earlier files.
- Use runner tags for capability and workload class, then enforce trust separately through runner protection and
  isolation. Account for CPU, memory, disk, devices, and expected concurrency.

Store failure diagnostics with `artifacts:when: always` when they materially aid investigation, but use bounded
retention, narrow paths, and appropriate access. Key dependency caches by lockfile content plus runtime, platform, and
toolchain identity; a cache remains an optimization, never the promoted output.

Authoritative references: [job rules](https://docs.gitlab.com/ci/jobs/job_rules/), [YAML
optimization](https://docs.gitlab.com/ci/yaml/yaml_optimization/), [job artifacts](https://docs.gitlab.com/ci/jobs/job_artifacts/),
and the [`needs` syntax](https://docs.gitlab.com/ci/yaml/#needs).
