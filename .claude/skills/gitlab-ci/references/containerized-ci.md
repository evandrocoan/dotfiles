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

Audit mount shadowing before trusting that image. A checkout, project-directory, or home-directory bind mount can hide
an environment, package-manager configuration, or cache created during the build. Place reusable environments and
non-authoritative caches outside mounted paths, or configure their locations through explicit environment variables.
When the image intentionally prewarms downloads and recreates a project environment at runtime, bind its tag to every
relevant lockfile and make a cache miss affect speed rather than correctness.

Use one base Compose model plus a focused CI override when CI must remove production-only mounts or ports, change
commands, or move nonessential default services behind profiles. Validate the exact merged file set. Do not copy the
stack into a second CI-only model or let an override silently retain an incompatible base field.

## Isolate every Compose stack

Assign every job a unique, bounded `COMPOSE_PROJECT_NAME`, normally derived from trusted pipeline and job identifiers.
This prevents concurrent jobs from sharing container, network, or volume names.

For each job:

1. select the exact Compose files and profiles;
2. validate the merged model with `docker compose config --quiet`;
3. keep registry transfer progress out of ordinary job logs by using `--quiet-pull` on every
   Compose `up` and `run`, and `--quiet` on an explicit Compose `pull`; preserve pull errors and
   do not silence the complete Compose command;
4. wait for dependency health rather than a fixed sleep or an unmanaged background process;
5. propagate the terminal service status with an invocation that matches every selected
   service's lifecycle;
6. clean only that job's project in `after_script` with `docker compose down --remove-orphans`;
7. add `--volumes` only when every named volume in that isolated project is disposable.

Choose the Compose lifecycle from the services that may exit:

- Use `--abort-on-container-exit` with `--exit-code-from <terminal-service>` only when
  that terminal service is the only service expected to exit. A successful setup, seed, or
  migration would otherwise abort the stack before the terminal test finishes.
- Use `--abort-on-container-failure` only when any nonzero service exit must stop an
  attached stack and another explicit condition owns successful completion. It ignores
  successful exits, so it cannot finish a CI test after a terminal service returns `0`.
  Do not add `--exit-code-from` as a workaround because that option implies
  `--abort-on-container-exit`.
- When expected one-shots are dependencies of a terminal test, model their success with
  `depends_on` and `condition: service_completed_successfully`, then use the terminal
  service as the lifecycle boundary:

```bash
docker compose up -d --quiet-pull <terminal-service>
docker compose logs --follow --no-color <terminal-service> &
docker compose wait --down-project <terminal-service>
```

The first command starts the dependency graph and fails if a required setup service fails. The
log follower exposes the terminal service's output without becoming the result authority. The
Compose wait returns the named terminal service's exit status and tears down that isolated project.
Keep `after_script` cleanup as a fallback for cancellation or startup failure. Do not use detached
`up` followed only by `wait`: `wait` does not stream container output, and `--down-project` can
remove the container before later log collection.

If Compose has `wait` but lacks `wait --down-project`, preserve both the terminal and cleanup
results explicitly:

```bash
set -euo pipefail
docker compose up -d --quiet-pull <terminal-service>
docker compose logs --follow --no-color <terminal-service> &
set +e
docker compose wait <terminal-service>
TERMINAL_STATUS="$?"
docker compose down --remove-orphans
CLEANUP_STATUS="$?"
set -e
if [[ "${TERMINAL_STATUS}" -ne 0 ]]; then
    exit "${TERMINAL_STATUS}"
fi
exit "${CLEANUP_STATUS}"
```

If Compose lacks `wait` entirely, use a repository-owned wrapper that waits for the exact terminal
container, reads its recorded exit status, tears down only the isolated Compose project, and
returns the terminal status. Do not replace that lifecycle with sleeps, log matching, or an
unbounded polling loop.

If a dependency cannot be modeled as a Compose service, use a bounded, strict readiness helper: refuse to execute the
payload after timeout, preserve the readiness exit status, and `exec` the payload after success. When a CI shell block
must start a local helper in the background, capture its PID, install a cleanup trap, wait for readiness, preserve the
test status, and terminate the helper. Prefer a Compose service and healthcheck whenever practical.

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
