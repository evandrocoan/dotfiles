# Docker security review

Read this reference for production changes and whenever a task touches secrets, users, downloads, image identity,
host resources, daemon access, capabilities, or sandboxing.

## Establish the trust boundary

Identify who controls the Dockerfile, build context, base images, Compose files, environment files, mounted host paths,
registry, builder, and runtime daemon. Treat content copied or mounted from a less trusted boundary as untrusted even
when the container itself is local.

## Protect credentials and sensitive data

- Keep `.env`, credentials, private certificates, package-manager auth, cloud configuration, and state directories
  outside the build context with `.dockerignore`.
- Use BuildKit secret mounts for file or environment-backed build secrets and SSH mounts for agent access. Grant only
  the instruction that needs them.
- Use Compose secrets and grant each secret only to the consuming service. Prefer file-based consumption under the
  service's secret mount over broad environment injection.
- Never store a secret in `ARG`, `ENV`, labels, image history, URLs, command-line arguments, checked-in defaults, or
  examples containing usable credentials.
- Never enable `set -x` around commands that may touch environment values or credentials.
- Avoid rendering the fully interpolated Compose model in logs. Use `docker compose config --quiet` for validation.

## Minimize privilege

- Run the application as a non-root user and verify ownership of copied and mounted files.
- Prefer `read_only: true`, explicit writable volumes, and `tmpfs` for scratch paths when application behavior permits.
- Prefer dropping all Linux capabilities and adding back only the capability proven necessary.
- Prefer `no-new-privileges` for production services unless a verified runtime requirement conflicts with it.
- Keep the default seccomp profile. Use a narrowly tailored, versioned profile only when the workload has a proven
  syscall requirement.
- Reject `privileged: true` by default. If kernel or hardware access is indispensable, document the exact capability,
  test a smaller device or capability grant first, and obtain explicit authorization.
- Allow a root initialization step only long enough to perform required setup; drop privileges before executing
  untrusted or network-facing application code.

## Protect the host

- Treat access to the Docker or container-runtime socket as effective control of the host. Do not mount it as an
  ordinary development volume.
- Prefer a restricted API broker, rootless isolated daemon, or dedicated Docker-in-Docker service when a container
  must build or launch other containers.
- Avoid host networking, host PID or IPC namespaces, broad devices, home-directory mounts, and writable source mounts.
  Require an explicit need and the narrowest viable scope.
- Do not expose stateful service ports to every interface unless remote access is intended and protected.
- Avoid stable `container_name` values and shared resource names in untrusted or parallel jobs.

## Protect the image supply chain

- Use trusted base images and exact version tags. Require released tags to be protected from overwrite when the
  artifact must be reproducible.
- Maintain an explicit refresh process for base-image tags and dependencies. A permanently stale pin is not a
  security strategy.
- Verify downloaded artifacts by pinned checksum or trusted signature before execution. Fail closed on a mismatch.
- Never execute `curl | sh`, extract an unverified stream, use an unchecked URL in `ADD`, or build from a mutable
  branch as a production input.
- Keep compilers, package managers, test suites, credentials, and caches out of the runtime stage.
- Let the release pipeline produce provenance, an SBOM, vulnerability assessment, and signature when required. Bind
  them to the same protected image tag that is promoted.
- Record a CI-supplied source revision with OCI labels instead of copying `.git` into the image.

## Review runtime resilience

- Use exec-form commands and graceful signal handling so the daemon can stop the real application.
- Set a shutdown grace period based on actual flush and cleanup behavior; do not shorten it blindly.
- Use healthchecks that prove useful capability without leaking credentials or depending on unrelated services.
- Bound local log retention and prevent secrets from entering application, entrypoint, build, or healthcheck logs.
- Keep restart policies from repeating non-idempotent setup or masking a crash loop.

## Reject common escape hatches

Reject these patterns unless the narrow exception is explicit and verified:

| Pattern | Default decision | Narrow exception |
| --- | --- | --- |
| `privileged: true` | Reject | Proven kernel or hardware operation with explicit authorization |
| Runtime socket mount | Reject | Trusted local development or a restricted broker |
| Host networking | Reject | Documented host reachability or performance requirement |
| Runtime as root | Reject | Short initialization followed by a verified privilege drop |
| `latest` or branch-based production input | Reject | Explicitly disposable exploration |
| Shell-form `CMD` or `ENTRYPOINT` | Reject | Tested wrapper that needs shell expansion and ends with `exec` |
| `tail -F` or `sleep infinity` | Reject | Clearly identified interactive development container |
| Broad writable host mount | Reject | Trusted local tool with a documented, minimized scope |
| Fixed sleep for readiness | Reject | Test synchronization where the sentinel itself is the result |
| General OS upgrade in a service image | Reject | Internally governed and tested base-image production |
