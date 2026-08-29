# Containerized CI

## Keep CI orchestration thin

Define each check once in a repository-owned executable contract, then invoke it from both local development and CI.
The contract can be a one-shot Compose service, a strict shell wrapper, or both.

- Let GitLab select the pipeline source, exact revision, runner, credentials, dependencies, and retention policy.
- Let the repository wrapper select the lint, unit, integration, documentation, or smoke command.
- Let Compose define services, health checks, profiles, mounts, and container exit behavior.
- Keep a local aggregate command synchronized with the union of mandatory CI jobs. A local `all` mode that omits a
  required CI check is not parity.
- Separate infrastructure-free checks from integration stacks so cheap jobs remain fast and independently schedulable.
- Put test-only services behind Compose profiles so an ordinary runtime start does not launch CI workloads.

Use a prebuilt CI environment image when dependency installation dominates runtime. Bind its protected release tag to
the relevant lockfiles, runtime, and toolchain, and document the update trigger. Never use `latest` as compatibility
authority.

## Isolate every Compose stack

Assign every job a unique, bounded `COMPOSE_PROJECT_NAME`, normally derived from trusted pipeline and job identifiers.
This prevents concurrent jobs from sharing container, network, or volume names.

For each job:

1. select the exact Compose files and profiles;
2. validate the merged model with `docker compose config --quiet`;
3. wait for dependency health rather than a fixed sleep or an unmanaged background process;
4. propagate the terminal service status with `--abort-on-container-exit` and `--exit-code-from` when appropriate;
5. clean only that job's project in `after_script` with `docker compose down --remove-orphans`;
6. add `--volumes` only when every named volume in that isolated project is disposable.

Do not begin with a broad `down`, delete shared runner directories, or ignore setup and teardown errors as routine
cleanup. Serialize jobs with `resource_group` when they mutate one shared external environment; a unique Compose name
does not isolate a shared database, GitLab project, device, or deployment target. Keep mutating verification jobs
non-interruptible unless their external effects are idempotent and safely resumable.

## Preserve container and workspace boundaries

- Prefer a read-only checkout mount for tests and builds that should not edit source.
- For formatters or hooks that require writes, copy the checkout into an isolated tmpfs or job workspace and report
  the diff explicitly. Do not loosen the source mount merely for tool convenience.
- Treat Docker-in-Docker, a Docker socket, and privileged mode as separate trust decisions. Use an isolated ephemeral
  runner and avoid unrelated secrets when daemon access is unavoidable.
- Keep generated secret files ephemeral, permission-restricted, excluded from artifacts and caches, and removed in
  teardown. Prefer file-type variables or secret providers when supported.
- Authenticate registries through standard input. Never place a password on the command line.
- Pass only explicitly allowlisted, public compile-time values as Docker build arguments. Never construct arguments
  with `eval`, and never use build arguments for secrets.

Load the `docker` skill for Dockerfile, Compose, image-build, runtime, or daemon-access decisions. Load the
`bash-scripts` skill before editing the repository wrapper or a non-trivial CI shell block.

Authoritative references: [Docker-in-Docker with GitLab](https://docs.gitlab.com/ci/docker/docker_in_docker/) and
[resource groups](https://docs.gitlab.com/ci/resource_groups/).
