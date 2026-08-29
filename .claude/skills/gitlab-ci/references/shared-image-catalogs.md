# Shared image catalogs

## Make the catalog explicit

Treat a repository of reusable images as a supply-chain product, not as a collection of unrelated Dockerfiles. Keep
one authoritative catalog entry for every published image and derive jobs from it when practical. Bind each entry to:

- its build context, Dockerfile, target, and `.dockerignore`;
- the published image name and protected release-tag policy;
- supported platforms and required CPU, GPU, or other runner capabilities;
- owners, consumers, validation commands, and lifecycle status;
- shared inputs whose change invalidates multiple entries.

Validate that every publishable directory has exactly one catalog entry and that every entry resolves to existing
files. Reject duplicate image names, tags, job identities, and undeclared contexts. Keep repository-specific versions,
paths, and owners in the catalog rather than duplicating them in agent instructions or large YAML blocks.

## Derive a complete change graph

Use `rules:changes` with explicit pipeline-source conditions. Match an image context recursively, including nested
configuration, lockfiles, and helper scripts. Include the catalog, shared templates, root CI configuration, common
bases, and shared build scripts in every affected image's change set.

Do not use deprecated `only:changes`, a single-directory `path/*` pattern for nested contexts, or path filtering as
proof of independence. Validate additions, deletions, renames, catalog-only changes, shared-input changes, and release
tags. Define explicit behavior for schedules and manual or API runs because their comparison base differs from merge
request and branch pipelines.

Use a generated child pipeline or `parallel:matrix` when it preserves readable ownership and exact needs. Keep hidden
build templates small and pass only typed or allowlisted values; never assemble build or push commands with `eval`.
Give CPU and GPU variants explicit capability lanes, but enforce runner trust separately from runner tags.

## Preserve one candidate through promotion

Use this lifecycle for each selected catalog entry:

1. **Validate:** lint the Dockerfile and catalog, inspect the build context, verify `.dockerignore`, and reject embedded
   credentials or unchecked executable downloads.
2. **Build:** create one uniquely tagged candidate, record CI-supplied source metadata with OCI labels, and emit a
   manifest that binds the candidate tag to its catalog entry, producer job, platform, and revision.
3. **Test:** exercise that exact candidate on its intended platform. Verify its tool interface or service smoke test,
   runtime user, entrypoint, expected files, forbidden credentials and test suites, and graceful exit where applicable.
4. **Scan:** scan the same candidate and retain the machine-readable report. Missing or malformed output is incomplete,
   never clean. Produce SBOM, provenance, or signature evidence when required by release policy.
5. **Publish:** promote the tested candidate without rebuilding. Require every validation, test, and scan gate, a
   protected source release tag, a non-overwritable image tag, and an authorized protected runner or environment.
6. **Notify:** expose the published tag and compatibility metadata to known consumers without silently mutating their
   repositories or deployments.

If a scanner requires registry access, publish first to a restricted staging namespace under a unique, non-overwritable
candidate tag. Promote that same candidate only after the gates pass. Never use `latest`, a branch name, a mutable
functional alias, stale runner contents, or a digest-only reference as the authority for the selected artifact.

## Secure registry and builder access

- Prefer the job-scoped registry credential and the full registry namespace supported by the GitLab instance.
- Send the password or token through standard input. Never place it in command arguments, repository URLs, images,
  artifacts, generated configuration, or logs.
- Pass only explicit, non-secret build arguments. Use BuildKit secret or SSH mounts for build-time credentials.
- Isolate daemon access and privileged builders on protected, ephemeral runners without unrelated secrets or jobs.
- Separate untrusted merge request validation from publication credentials and protected release runners.
- Stop publication and require credential rotation when a secret is discovered in a Dockerfile, build context, layer,
  or repository history. Removing the visible string does not make the exposed credential safe again.

## Balance freshness and cache integrity

Keep normal validation builds cacheable. Key external caches by compatible catalog entry, platform, toolchain, and
dependency inputs; never treat cache as the candidate artifact. Use an explicit scheduled or manually authorized clean
rebuild to refresh base images and detect undeclared network drift. Do not force `--no-cache` on every change merely to
obtain freshness, and do not use a cache alias as the published image identity.

Define deprecation, rebuild, and consumer-update policy for shared images. A protected tag without a controlled refresh
process becomes stale; a moving tag makes prior validation meaningless.

Authoritative references: [GitLab job rules](https://docs.gitlab.com/ci/jobs/job_rules/), [deprecated CI
keywords](https://docs.gitlab.com/ci/yaml/deprecated_keywords/), [container registry authentication](https://docs.gitlab.com/user/packages/container_registry/authenticate_with_container_registry/),
and [Docker build cache](https://docs.docker.com/build/cache/).
