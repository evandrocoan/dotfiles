---
name: docker
description: Create, edit, review, secure, build, run, and troubleshoot Dockerfiles, .dockerignore files, Docker BuildKit or Buildx workflows, and Docker Compose stacks. Use when Codex works on container image reproducibility, multi-stage or multi-platform builds, image size and cache behavior, container startup and signals, Compose services, profiles, healthchecks, volumes, networks, secrets, development containers, container-backed CI, or Docker runtime diagnostics.
---

# Docker and Docker Compose

Work from the repository's container contract instead of treating a Dockerfile or
Compose file in isolation. Preserve reproducibility, least privilege,
debuggability, and parity between local development and CI.

## Follow the core workflow

1. Read the workspace instructions before running Docker commands or editing files.
2. Discover the coupled surface with `rg --files` patterns for Dockerfiles,
   Compose files, `.dockerignore`, environment examples, entrypoints,
   healthchecks, devcontainers, and CI configuration.
3. Determine the intended environment, service, build target, platform, and
   lifecycle. Infer them from authoritative repository configuration; ask only
   when an unresolved choice would materially change the result.
4. Inspect the current configuration before editing. Prefer
   `docker compose config --quiet` when interpolation values may be sensitive;
   do not print resolved configuration merely to validate it.
5. Make the smallest coherent change across every coupled consumer. Keep
   Dockerfile targets, Compose build settings, environment examples,
   entrypoints, and CI invocations aligned.
6. Validate from static configuration through build and runtime behavior. Stop
   at the first failing boundary, diagnose it, and avoid layering workarounds
   over an earlier failure.
7. Report the exact files changed, commands run, observed results, and any
   unverified platform or external-service behavior.

## Route to the relevant reference

- Read [dockerfile.md](references/dockerfile.md) before creating, changing, or
  reviewing a Dockerfile, build context, `.dockerignore`, image target, or
  multi-platform build.
- Read [compose.md](references/compose.md) before creating, changing, or reviewing
  Compose services, profiles, dependencies, volumes, networks, resource
  controls, or container-backed development and CI flows.
- Read [security.md](references/security.md) whenever the task touches
  credentials, downloads, image provenance, users, capabilities, host access,
  daemon access, browser sandboxes, production hardening, or a security review.
- Read [validation.md](references/validation.md) before running builds, tests,
  smoke checks, or diagnostics. Select only checks proportional to the change
  and supported by the installed Docker capabilities.

## Preserve execution boundaries

- Use the repository's documented Docker or Compose entry points. If the
  repository requires container-only execution, keep the host limited to Docker,
  Compose, Git, and read-only inspection.
- Represent tests, migrations, setup, seed, documentation, and CLI tasks as
  explicit one-shot services when they need the project runtime. Do not install
  project dependencies on the host to bypass a missing container entry point.
- Reuse the same Compose services in local and CI workflows when practical. Keep
  CI orchestration thin and place the executable environment contract in the
  image and Compose model.
- Treat adding, removing, or upgrading an OS or application package as a
  dependency decision. Follow the repository's approval workflow before
  changing it.
- Preserve the existing Dockerfile and Compose naming convention. Name a new
  environment-specific Dockerfile with the environment before `.Dockerfile`,
  such as `dev.Dockerfile`.

## Apply decision gates

Resolve these questions from repository evidence before implementation:

- Is the target development, test, CI, production, or a reusable tool image?
- Is the target CPU architecture or GPU requirement explicit? Never infer GPU
  availability or force an architecture merely because the current host uses it.
- Which data must persist, which output must return to the host, and which files are scratch data?
- Which services are long-lived, one-shot, optional, or mutually exclusive?
- Which ports and host resources truly require exposure?
- Does the application support a non-root user, a read-only root filesystem,
  dropped capabilities, and graceful shutdown? Verify compatibility instead of
  silently weakening the controls.

## Enforce non-negotiable safety rules

- Never place secrets in a Dockerfile, build argument, persistent `ENV`, image
  layer, checked-in Compose value, build log, or broadly rendered configuration.
  Use BuildKit secret or SSH mounts and narrowly granted Compose secrets.
- Never execute code obtained through a direct download unless its immutable
  content is authenticated with a pinned checksum or signature. Reject
  `curl | sh`, `curl | tar`, unchecked remote `ADD`, and mutable direct remote
  inputs. A package manager may instead rely on its authenticated repository
  metadata, signature chain, and repository-approved lockfile; do not invent a
  separate manual checksum that its authoritative workflow does not support.
- Reject mutable production image references such as `latest`, floating version
  ranges, or branches unless the environment is explicitly disposable. Use
  explicit version tags for base, service, and `COPY --from` images; require
  released tags to be protected from overwrite and maintain an intentional
  update policy.
- Reject `privileged: true`, Docker socket mounts, host networking, broad host
  mounts, and extra capabilities by default. Require the concrete operation,
  trust boundary, and smallest viable permission before accepting one.
- Do not install dependencies, regenerate lockfiles, or compile application code
  during container startup.
- Do not keep a failed service alive with `tail -F` or `sleep infinity` outside
  an intentional interactive development container.
- Do not hide the useful process behind an untested shell supervisor. Use
  exec-form `ENTRYPOINT` and `CMD`, make an entrypoint end with `exec`, and add an
  init process when child reaping or signal forwarding requires it.
- Do not execute destructive cleanup such as volume removal, prune operations,
  image deletion, or orphan removal without explicit authorization and exact
  target inspection.
- Do not push images, change registry state, or modify shared remote builders
  unless the user explicitly requests the remote mutation.

## Diagnose by boundary

Classify a failure before changing configuration:

1. **Model resolution:** Compose parsing, interpolation, merge, profiles, paths,
   or missing required values.
2. **Build:** context, `.dockerignore`, base image, platform, dependency
   resolution, cache, secret mount, or artifact production.
3. **Creation:** mounts, networks, ports, devices, permissions, or daemon policy.
4. **Startup:** entrypoint, command, PID 1, signals, migrations, or dependency readiness.
5. **Runtime:** application error, healthcheck, resource exhaustion, filesystem
   ownership, or read-only violations.
6. **Connectivity:** service DNS, listening address, published port, external
   network, or host reachability.
7. **Shutdown:** stop signal, grace period, child processes, state flush, or restart policy.

Inspect the earliest failing boundary with the commands in
[validation.md](references/validation.md). Fix source files and rebuild; never
treat mutations made inside a running container as the solution.
