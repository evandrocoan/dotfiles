# Runners and secrets

## Classify runner trust before selecting tags

Runner tags express scheduling capabilities; they do not prove isolation. Determine:

- executor type and whether the workspace, VM, container host, or cache survives the job;
- whether the runner accepts unprotected branches, forks, or unrelated projects;
- whether it can access the host, Docker daemon, devices, internal network, or production credentials;
- whether one job can observe another job's processes, files, containers, cache, or tokens;
- whether privileged work runs on an isolated, ephemeral machine.

Keep sensitive runners locked to intended projects and protected refs. Separate trusted deployment/security work from
untrusted build and merge request work. Treat shell executors and persistent shared workspaces as high-risk.

Do not use a tag named `privileged`, `production`, or similar as the only authorization control. Protect the runner,
branch or tag, environment, and credential independently.

Authoritative reference: [GitLab Runner security](https://docs.gitlab.com/runner/security/).

## Minimize credentials

Choose the narrowest supported credential:

1. Use `CI_JOB_TOKEN` for supported API and artifact access while the job is running.
2. Add only the required project or group to the job-token allowlist.
3. Use a project, group, deploy, or service token only when its resource and API permissions are actually needed.
4. Use a personal token only when the operation genuinely requires a user identity and no service identity works.

Restrict tokens by scope, project, protected context, and lifetime. Store sensitive values outside YAML; prefer an
external secret provider or file-type variable where appropriate. Mask and hide values as defense in depth.

Never:

- run `env`, `printenv`, `export`, or equivalent full environment dumps in a job that can receive secrets;
- enable `set -x`, `CI_DEBUG_TRACE`, or verbose HTTP output around credentials;
- embed a token in a repository URL, artifact, cache, image layer, dotenv report, or generated configuration;
- forward a masked variable to a different project under the assumption that masking follows it;
- expose protected variables to fork or untrusted MR code without reviewing the exact code that will run.

Authoritative references: [CI/CD variables](https://docs.gitlab.com/ci/variables/) and
[CI job tokens](https://docs.gitlab.com/ci/jobs/ci_job_token/).

## Keep Docker concerns behind the Docker boundary

Load the `docker` skill before accepting Docker-in-Docker, a host Docker socket, privileged mode, host networking,
host mounts, additional capabilities, or image-building changes.

- Prefer a build method supported by an isolated runner and the project's security model.
- Treat a Docker socket mount as control of the host daemon, not as ordinary file access.
- Treat privileged mode as loss of the container isolation boundary.
- If privileged execution is unavoidable, use a dedicated ephemeral runner with no unrelated secrets or workloads.
- Use explicit released image tags; reject `latest`, floating ranges, and digest-only references under the tag policy.
- Keep Docker and Compose commands in the repository's approved container workflow and use `docker compose` syntax.

Authoritative reference: [Docker-in-Docker with GitLab](https://docs.gitlab.com/ci/docker/docker_in_docker/).

## Protect caches and persistent workspaces

- Do not assume `/builds` or another runner directory is clean between jobs.
- Use runner-managed cleanup and isolated build directories. Never use broad globs with recursive deletion as a
  self-repair strategy.
- Separate caches for protected and unprotected refs, architectures, runtimes, and incompatible lockfiles.
- Do not let untrusted jobs publish a cache later consumed by privileged release or deployment jobs.
- Avoid mutating shared dependency repositories in place. Make cache restoration disposable and reproducible.
- Never disable IPv6, rewrite host DNS, change firewall rules, or mutate other system-wide runner state as a generic
  pipeline fix.

## Control third-party and downloaded code

Review external includes, images, package hooks, analyzers, and downloaded scripts as executable supply-chain inputs.
Use protected release tags and the project's dependency approval process. Do not use `curl | sh`, unchecked archives,
or a mutable branch as a build tool. Ensure release tags cannot be overwritten and define an intentional update path.
