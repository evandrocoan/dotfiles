# Validation and troubleshooting

Use the smallest sequence that proves the changed contract. Prefer
repository-documented services and flags over the generic commands below.

## Contents

- [Check capabilities first](#check-capabilities-first)
- [Validate configuration before building](#validate-configuration-before-building)
- [Build the narrowest target](#build-the-narrowest-target)
- [Exercise the runtime contract](#exercise-the-runtime-contract)
- [Inspect the built artifact](#inspect-the-built-artifact)
- [Diagnose failures in order](#diagnose-failures-in-order)
- [Avoid destructive diagnostics](#avoid-destructive-diagnostics)
- [Consult current primary documentation](#consult-current-primary-documentation)

## Check capabilities first

Inspect Docker and Compose availability without changing daemon state:

```text
docker version
docker compose version
docker buildx version
docker buildx inspect
```

Do not create or switch builders merely to make a check pass. If the installed
version lacks a documented option, report the limitation and use a
repository-approved alternative.

## Validate configuration before building

Validate the exact Compose file set, profiles, project directory, and environment
source used by the scenario:

```text
docker compose -f compose.yaml -f compose.override.yaml config --quiet
```

Use the repository's actual filenames. Avoid rendering the full model when
interpolation may include secrets. When a profile matters, activate it exactly as
the documented invocation does.

Run Dockerfile build checks without building when supported:

```text
docker build --check -f path/to/Dockerfile path/to/context
```

Treat build-check warnings as findings to assess, not automatic permission to
rewrite working platform-specific logic. Do not enable experimental checks or add
skip directives without a concrete reason.

## Build the narrowest target

Prefer the service or stage affected by the change:

```text
docker compose build service-name
docker buildx build --load --target target-name -f path/to/Dockerfile -t local-test:temporary path/to/context
```

Use `--load` only for a single-platform local validation. Do not push as part of
validation unless explicitly authorized. Preserve normal cache behavior first;
use a clean build only when testing reproducibility or diagnosing a cache-specific
failure. Remember that `--no-cache` does not refresh a cached base image; use
`--pull` only when network access and image refresh are intended.

For multi-platform behavior, validate the intended platform matrix in the
existing CI or builder workflow. Do not register emulators, create remote
builders, or run privileged setup without authorization.

## Exercise the runtime contract

Start only the required service set and wait for declared healthchecks when supported:

```text
docker compose up --detach --wait service-name
docker compose ps --all
docker compose logs --tail 200 service-name
```

Use a bounded wait. For a one-shot task, use the repository's official invocation, commonly:

```text
docker compose run --rm service-name
```

Verify the task's exit code, not merely that its container was created. For a
stack test, prefer an attached terminal service with exit-code propagation and
automatic stop of dependencies.

## Inspect the built artifact

Use image inspection and a minimal smoke run to verify the properties the change claims:

- Confirm the configured runtime user is non-root when required.
- Confirm `Entrypoint` and `Cmd` preserve argument and signal behavior.
- Confirm expected OCI labels contain CI-supplied metadata and no sensitive values.
- Confirm the final filesystem contains only runtime artifacts, not test suites,
  credentials, package caches, or build tools that the runtime does not need.
- Confirm mounted paths are writable or read-only exactly as intended.
- Confirm the application binds the expected container interface and the
  healthcheck tests useful readiness.
- Stop the smoke container normally and verify graceful shutdown within the configured grace period.

Never inspect for secrets by printing all environment values or exporting the
image filesystem into an uncontrolled location. Use targeted metadata and path
checks.

## Diagnose failures in order

### Compose model

Run `docker compose config --quiet`. Check the selected files, project directory,
active profiles, required variables, relative paths, merge behavior, and mutual
exclusivity before touching the daemon.

### Build

Read the first failing build step. Check whether `.dockerignore` removed a
required input, whether the context path is correct, whether the base and source
stages support the target platform, whether lockfile installation is frozen, and
whether secret or cache mounts are declared on the exact `RUN` instruction that
needs them.

### Container creation

Inspect the daemon error and the rendered service model. Check mount source
existence and type, network existence, port conflicts, device availability,
resource constraints, and security policy. Do not respond by broadening
privileges unless the error proves the specific missing permission.

### Startup and health

Use `docker compose ps --all` and bounded logs. Distinguish an exited entrypoint,
a running but unready application, and a faulty healthcheck. Check command
overrides, file ownership, executable bits, PID 1 behavior, dependency conditions,
listening address, and probe availability.

### Connectivity

Test from the same network boundary as the failing consumer. Check service DNS,
internal port, published host port, bind address, proxy settings, and
external-network membership. Do not assume host `localhost` refers to the host
from inside a container.

### Storage and resources

Check the exact mount, UID and GID, read-only state, available space, memory limit,
shared memory, and ulimits. Preserve named volumes unless the user explicitly
authorizes deleting state.

### Shutdown and restart

Observe the real process, stop signal, grace period, exit code, and restart policy.
Check for shell wrappers that fail to `exec`, unreaped children, non-idempotent
startup work, and state that needs more time to flush.

## Avoid destructive diagnostics

Do not use `docker system prune`, `docker builder prune`, `docker volume prune`,
`docker compose down --volumes`, `docker compose up --renew-anon-volumes`, forced
orphan removal, or broad image deletion as routine troubleshooting. Inspect exact
resources first and obtain explicit authorization for any material cleanup.

## Consult current primary documentation

- [Dockerfile best practices](https://docs.docker.com/build/building/best-practices/)
- [Docker build checks](https://docs.docker.com/build/checks/)
- [Build secrets](https://docs.docker.com/build/building/secrets/)
- [Multi-platform builds](https://docs.docker.com/build/building/multi-platform/)
- [Compose configuration rendering](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Compose profiles](https://docs.docker.com/compose/how-tos/profiles/)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)
