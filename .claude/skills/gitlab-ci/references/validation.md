# Validation and diagnostics

## Validate without mutating remote state

Use this order, stopping at the first failed boundary:

1. Inspect YAML and every local or remote include that contributes to the target jobs.
2. Use the GitLab CI Lint or equivalent GitLab repository tool to validate the configuration with includes resolved.
3. Inspect merged YAML for overwritten arrays, inherited variables, hidden jobs, stages, rules, tags, and artifact
   dependencies.
4. Perform a dry-run or simulated pipeline creation for representative refs when the GitLab instance supports it.
5. Exercise repository-approved local checks for scripts and runtime configuration.
6. Trigger or retry a real pipeline only with explicit user authorization, then inspect the earliest failed job and
   preserve its diagnostics.

Use GitLab MCP or connector tools first for GitLab repository, merge request, and pipeline state. Fall back to the
GitLab API or shell only when the connector is unavailable or fails, and state the fallback. Never send CI YAML or
secrets to an unrelated public validator.

A generic YAML parser cannot validate GitLab includes, custom tags, inputs, expressions, or merged semantics. Static
parsing is useful only as an earlier syntax check.

Authoritative reference: [GitLab CI Lint API](https://docs.gitlab.com/api/lint/).

## Test the source matrix

For each relevant source, verify both pipeline existence and job membership:

- merge request with and without relevant file changes;
- branch push with and without an open merge request;
- default and protected branch;
- protected release tag;
- schedule or manual/API pipeline;
- parent or multi-project downstream trigger;
- fork or other untrusted source.

Add only scenarios the project can actually produce. For every scenario, verify required jobs, absent jobs, manual
blocking behavior, `allow_failure`, runner eligibility, needs that reference conditionally absent jobs, and whether
protected variables or environments are available.

## Validate data and security gates

For artifacts, reports, caches, and downstream data, check:

- exact producer identity and snapshot;
- retention and access restrictions;
- behavior when the producer is skipped, fails, or uploads no file;
- behavior when content is empty, malformed, truncated, expired, or inaccessible;
- cross-project job-token allowlists and caller permissions;
- cache miss and cache poisoning boundaries;
- status propagation and cancellation between upstream and downstream pipelines.

For SAST or MR publication, exercise zero findings, blocking findings, findings outside the diff, scanner failure,
missing report, stale MR head, pagination, repeated publication, partial inline failure, and API authorization failure.
Verify that only a valid zero-finding report can produce a clean result.

For CODEOWNERS or approval gates, exercise overlapping patterns, sections, optional sections, default owners, groups,
multiple required approvals, renamed files, missing files, ineligible approvers, self-approval policy, and a head change
after evaluation.

## Diagnose from observed state

Collect only the minimum safe diagnostics:

- pipeline source and protected status;
- job rule result and merged configuration;
- runner selection and executor class;
- upstream and downstream pipeline/job identifiers;
- artifact and report metadata without dumping sensitive content;
- HTTP status, endpoint class, and bounded error body with credentials removed.

Do not dump the full environment. Do not enable shell trace globally. Do not retry until the failure is classified as
transient. When the target GitLab version or tier is uncertain, verify feature support on that instance before using
newer syntax such as components, inputs, or status strategies.

## Validate coupled Docker work

When a job builds or runs containers, load the `docker` skill and validate the Dockerfile, Compose model, image tags,
runtime permissions, and container behavior separately from the GitLab pipeline graph. A valid `.gitlab-ci.yml` does
not prove that a container build is reproducible or that privileged access is safe.

For Compose-backed jobs, also verify unique project names, exact file and profile selection, dependency health,
terminal-service exit propagation, bounded cleanup, and isolation from concurrent jobs. For repository-owned CI
wrappers, compare the mandatory split jobs with the local aggregate command.

For monorepos and parallel suites, exercise application-only, shared-package, lockfile, CI-wrapper, and global-config
changes. Verify complete shard coverage, unique artifact names, fan-in over every required shard, and promotion of the
same artifact that passed testing.
