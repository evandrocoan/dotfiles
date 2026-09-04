---
name: gitlab-ci
description: Design, create, edit, review, secure, validate, and troubleshoot GitLab CI/CD pipelines, shared templates, and CI/CD components. Use when Codex works with .gitlab-ci.yml, GitLab CI YAML includes, workflow or job rules, stages, needs or DAGs, artifacts, caches, inputs, variables, runners, downstream or child pipelines, monorepo change scoping, containerized CI, shared image catalogs, image or package promotion, security scanners, merge request reporting, CODEOWNERS gates, deployment gates or verification, or GitLab pipeline failures.
---

# GitLab CI/CD

Treat a pipeline as an executable trust, control-flow, and data-flow graph. Preserve
reproducibility, least privilege, snapshot identity, and an honest distinction between a successful
check, an incomplete check, and a skipped check.

## Follow the core workflow

1. Read the workspace instructions and inspect the repository's current branch and worktree before
   changing pipeline files. Preserve unrelated local changes.
2. Discover `.gitlab-ci.yml`, included YAML, component templates, scripts, Docker or Compose files,
   deployment configuration, and the project instructions that define how validation must run.
3. Build a pipeline-source matrix before editing: determine the intended behavior for merge
   requests, branches, tags, schedules, manual/API runs, and downstream or child pipelines. Include
   protected and fork contexts where relevant.
4. Inspect the fully merged configuration and all included definitions. Treat a moving include,
   inherited variable, or hidden job as executable code, not as documentation.
5. Model control flow from `workflow:rules` to job `rules`, then through `needs`, stages, manual
   gates, environments, and downstream triggers. Model data flow separately through artifacts,
   reports, caches, variables, and inputs.
6. Identify trust boundaries: who can change the pipeline, which runner executes it, which
   untrusted code it runs, which credentials it can receive, and which project or environment it
   can mutate.
7. Make the smallest coherent change across the root configuration, included templates, job
   scripts, and coupled runtime files. Do not duplicate one policy in several layers unless each
   copy has a distinct enforcement role.
8. Validate syntax, merged configuration, graph shape, and representative source scenarios. Do not
   create a pipeline, retry a job, cancel work, or mutate remote GitLab state unless the user
   explicitly authorizes that action.

## Route to the relevant reference

- Read [pipeline-design.md](references/pipeline-design.md) before changing `workflow`, `rules`,
  stages, `needs`, manual jobs, deployment gates, retries, or downstream pipeline topology.
- Read [templates-and-data.md](references/templates-and-data.md) before changing includes,
  components, inputs, `extends`, anchors, artifacts, reports, caches, checkout, or submodules.
- Read [security-pipelines.md](references/security-pipelines.md) before adding or reviewing SAST,
  security reports, central security templates, merge request comments, diff-scoped findings,
  CODEOWNERS checks, or approval gates.
- Read [runners-and-secrets.md](references/runners-and-secrets.md) whenever a task touches runners,
  executors, tags, tokens, protected resources, forks, Docker daemon access, privileged execution,
  or cross-project access.
- Read [containerized-ci.md](references/containerized-ci.md) before changing Compose-backed jobs,
  repository-owned CI wrappers, prebuilt CI images, writable container workspaces, or container
  lifecycle and cleanup.
- Read [monorepos-and-delivery.md](references/monorepos-and-delivery.md) before changing path-scoped
  monorepo jobs, sharding, build artifacts, image publication, package promotion, or diagnostics
  collected from parallel jobs.
- Read [shared-image-catalogs.md](references/shared-image-catalogs.md) before changing a repository
  that builds, validates, scans, or publishes multiple reusable container images for downstream
  projects.
- Read [deployment-verification.md](references/deployment-verification.md) before adding or
  reviewing post-deployment identity, content, rollout, health, smoke, or drift checks against a
  live environment.
- Read [validation.md](references/validation.md) before declaring a pipeline change valid or a
  failure diagnosed.

## Preserve ownership boundaries

- GitLab CI owns pipeline admission, job scheduling, dependencies, data transfer, credentials,
  environments, and remote pipeline state.
- Load the `docker` skill for Dockerfiles, image construction, BuildKit, Docker Compose, container
  runtime behavior, Docker socket access, or privileged containers. GitLab CI decides when and
  where the job runs; Docker decides how the containerized workload is built and executed.
- Load the `bash-scripts` skill before creating, editing, reviewing, or debugging shell scripts or
  non-trivial shell blocks embedded in CI YAML.
- Load the repository's dependency-decision workflow before adding an image, package, analyzer,
  service, or CLI that is not already authorized by the project.
- Use GitLab repository and pipeline tools before shell, generic HTTP, or credential-based
  fallbacks for remote GitLab state. Infer GitLab from the remote URL. Keep read-only inspection
  separate from remote mutation.

## Enforce non-negotiable rules

- Do not print the environment, enable shell tracing around secrets, embed credentials in YAML, or
  pass masked secrets to an untrusted downstream project. Masking is a log defense, not an
  authorization boundary.
- Prefer narrowly scoped, short-lived job tokens where the required endpoint supports them.
  Constrain cross-project access with an explicit allowlist. Use a project or service token only
  when its additional permissions are required.
- Pin reusable templates, components, job images, and service images with the
  immutable mechanism required by the repository: a protected non-overwritable
  release tag, a digest, or a tag plus digest. Reject moving branches, `latest`,
  and floating version ranges. Do not reject or replace a digest-only reference
  unless an explicit repository policy requires tag-based traceability.
- Never interpret a missing, malformed, expired, or inaccessible security report as an empty
  report. Fail or expose an incomplete result according to the project's explicit policy.
- Bind cross-job and cross-project results to the intended pipeline, commit, and merge request
  snapshot. A branch name alone is not sufficient identity for an artifact or inline diff position.
- Do not rely on runner tags alone as a security boundary. Protect and isolate sensitive runners,
  environments, caches, and credentials from untrusted branch or fork pipelines.
- Reject broad workspace deletion, unbounded retry loops, system-wide network changes, and custom
  clone logic as generic CI repair techniques. Use GitLab Runner checkout and submodule controls
  unless evidence proves they cannot satisfy the repository contract.
- Do not bypass required tests merely to publish or deploy an artifact. Independent packaging may
  proceed when the project intends it, but promotion and deployment must retain their required
  gates.
- Use `needs: []` only for genuinely independent work. A manual, release, publication, or
  deployment job must still depend on every gate and exact producer whose success authorizes the
  mutation.
- Do not use `allow_failure`, manual jobs, or skipped rules to make a mandatory security or quality
  gate appear green. State optionality explicitly and verify the merge policy sees the intended
  status.

## Diagnose the earliest failing boundary

Classify a failure before editing:

1. **Creation:** invalid YAML, include resolution, inputs, workflow, permissions, or pipeline-source
   mismatch.
2. **Scheduling:** missing runner, incompatible tags, protected-runner restrictions, resource
   groups, or unmet needs.
3. **Preparation:** image pull, checkout, submodules, cache restore, artifact download, or secret
   injection.
4. **Execution:** script, dependency, scanner, test, build, timeout, signal, or service failure.
5. **Collection:** missing artifact, malformed report, expiration, access policy, or incorrect
   dependency selection.
6. **Downstream:** trigger permissions, forwarded inputs or variables, status strategy, or
   cross-project access.
7. **Publication:** stale merge request snapshot, API permissions, pagination, duplicate comments,
   or invalid diff coordinates.
8. **Enforcement:** job status, approval rule, protected branch, environment gate, or merge policy
   disagrees with the intended result.

Fix the source of the earliest failure. Do not layer retries, manual clone loops, or permissive
rules over an earlier configuration or trust-boundary error.
