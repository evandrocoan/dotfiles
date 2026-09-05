# Docker Compose design

Use this reference for Compose models, service lifecycle, storage, networks,
resources, and container-backed local or CI workflows.

## Contents

- [Treat the rendered model as authoritative](#treat-the-rendered-model-as-authoritative)
- [Model service lifecycles](#model-service-lifecycles)
- [Express readiness, not creation order](#express-readiness-not-creation-order)
- [Classify storage by intent](#classify-storage-by-intent)
- [Design connectivity deliberately](#design-connectivity-deliberately)
- [Bound resources and special hardware](#bound-resources-and-special-hardware)
- [Align development and CI](#align-development-and-ci)

## Treat the rendered model as authoritative

- Use the Compose v2 command form, `docker compose`, unless the repository
  explicitly supports another interface.
- Inspect every file, include, override, profile, environment source, and CLI
  `-f` selection that contributes to the target scenario.
- Use `docker compose ... config --quiet` to validate the merged model without
  printing interpolated secrets. Render the full model only when its values are
  safe to expose.
- Use includes and overrides to express genuine layering. Use reset semantics
  when merge behavior would retain an invalid inherited value; never depend on a
  surprising implicit merge.
- Centralize repeated structure with extensions or anchors when it improves
  coherence. Do not repeat large service blocks that should evolve together.
- Centralize repeated non-secret configuration with `env_file` and
  interpolation. Use safe defaults for optional values and required-value syntax
  for inputs that must fail before startup; never put usable credentials in
  shared defaults.
- Keep mutually exclusive backends explicit. Validate that an invocation cannot
  accidentally activate incompatible alternatives.

## Model service lifecycles

- Keep core runtime services enabled by default. Put optional tools, CLI tasks,
  tests, GPU paths, and alternative backends behind capability-oriented profiles.
- Represent migrations, setup, seed, documentation, CLI, and tests as explicit
  one-shot services. Use `restart: "no"` for work that must not repeat
  automatically.
- Make setup operations idempotent and bounded. Prefer a healthcheck or
  protocol-level retry with a deadline over a fixed sleep or an unbounded wait
  loop.
- Set restart policy according to lifecycle. Use a long-lived policy only for
  services that can safely restart; do not restart a task whose repeated side
  effects may corrupt state.
- Set shutdown grace periods from observed application behavior, especially for
  databases and stateful workers.
- Avoid `container_name` for stacks that may run in parallel. Let the Compose
  project name scope containers, networks, and default resource names.

## Express readiness, not creation order

- Give each long-lived dependency a healthcheck that probes the minimum
  capability its consumer needs.
- Bind consumers to `service_healthy` when they require readiness and to
  `service_completed_successfully` when they require a successful one-shot
  prerequisite.
- Do not use `service_started`, fixed sleeps, or shared sentinel files as a
  substitute for application readiness.
- Keep healthchecks fast, bounded, and independent of optional upstream
  services. Ensure required probe binaries are actually present in the image.

## Classify storage by intent

- Mount source, fixtures, and immutable configuration read-only.
- Store durable service state in named volumes.
- Use a writable bind mount only for an artifact the user intentionally wants on the host.
- Use `tmpfs` for scratch data and pair it with a read-only root filesystem when
  the application supports that model.
- Separate shared read-only state from each service's private writable cache.
- Avoid broad mounts such as an entire home directory, `/root`, the Docker data
  root, or host timezone files unless a specific trusted local workflow proves
  the need.
- For trusted local development bind mounts, preserve the checkout's absolute
  host path inside the container by default instead of using a generic target
  such as `/workspace`. When Compose is invoked from the checkout being mounted,
  use:

  ```yaml
  working_dir: $PWD
  volumes:
    - "$PWD:$PWD"
  ```

  This keeps paths emitted by debuggers, test tools, caches, and editor
  integrations valid on both sides. Resolve `$PWD` from the actual Compose
  invocation boundary: when an integrated Compose command runs from a monorepo
  root, mount that root at the same path and set a product service's
  `working_dir` to its subdirectory under `$PWD`. Use a different target only
  for a demonstrated image or portability constraint, and document that
  constraint.
- Use workspace-derived project or volume names for parallel test scenarios.
  Normalize and delimit the value so two workspaces cannot collide.

## Design connectivity deliberately

- Use named bridge networks and service DNS for ordinary service-to-service communication.
- Use an external network only when independently managed stacks must
  interoperate; validate that it exists before starting the scenario.
- Publish only ports that host clients need. Avoid fixed host ports in parallel
  test stacks when an ephemeral mapping or internal-only access suffices.
- Use host networking only for a concrete, documented reachability or
  performance requirement. Treat the reduced isolation and portability as part
  of the decision.
- Use `host.docker.internal` with `host-gateway` only when a container must reach
  a host service and the platform requires the mapping. Do not encode a host IP.

## Bound resources and special hardware

- Set memory, swap, CPU, shared memory, and ulimits from observed workload needs
  and failure behavior. Do not copy a generic resource table into every service.
- Declare GPU access as an explicit device reservation and isolate it behind a
  GPU capability or profile. Provide a clear diagnostic when the runtime lacks
  the device.
- Force a non-native platform only when no native image exists and emulation is
  an accepted tradeoff.
- Configure bounded log rotation for long-lived local or production services so
  the Docker log driver cannot consume storage indefinitely.
- Keep browser-specific seccomp configuration versioned and tested with the
  browser image. Pair it with appropriate init and shared-memory settings; do
  not disable the sandbox as a shortcut.

## Align development and CI

- Mount the checkout for hot reload when rebuilding would impede development.
  Keep dependency environments outside a path hidden by that mount.
- Use a focused override to switch a development container between host
  networking and the stack bridge. Reset inherited network or port fields that
  do not apply in the selected mode instead of accumulating both models.
- Use a `post_start` hook only for adjustment that truly depends on a runtime
  mount, such as ownership of a newly mounted directory. Prefer compatible UID
  and GID values so the hook is unnecessary.
- Build dependencies into the development image instead of downloading them
  every time the environment opens.
- Treat a host Docker socket mounted into a development container as host-level
  control. Allow it only for a trusted local environment and prefer a restricted
  broker or isolated Docker-in-Docker service when practical.
- Build a reusable test-environment image, mount source and tests read-only, and
  write only explicit results or scratch data. Use a temporary filesystem when a
  formatter or test tool must mutate a copy.
- Reuse the same one-shot Compose service locally and in CI. Propagate the
  terminal service's exit code and make all required dependencies healthy first.
- Use `pull_policy: never` only when the workflow guarantees the exact local
  image was built before use and validates its identity.
- Combine an immutable dependency image with mounted local code only as an
  explicit development strategy. Detect an incompatible code-to-dependency
  contract instead of silently running it.
