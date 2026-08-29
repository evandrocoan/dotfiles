# Dockerfile design

Use this reference for Dockerfiles, build contexts, image targets, and BuildKit or Buildx behavior.

## Control the build context

- Create a strict `.dockerignore` for the actual context. Exclude Git metadata, local secrets, environment files,
  dependency directories, caches, coverage, test output, editor state, and build artifacts unless the build proves it
  needs a specific item.
- Prefer a narrow context over increasingly complex ignore exceptions.
- Treat `COPY . .` as unsafe until the context is small, closed, and audited. Copy dependency manifests and lockfiles
  first, then copy only the source required by the target.
- Never copy `.git` merely to calculate a version. Pass the revision from CI and record it with OCI labels when
  traceability is required.

## Make dependency layers reproducible

- Detect the package manager and use its lockfile-enforcing install operation. Do not invent or refresh a lockfile in
  the image build.
- Separate dependency resolution from source copying so source-only changes reuse the dependency layer.
- Use BuildKit cache mounts for package downloads when useful. Scope cache IDs by ecosystem and, when content differs,
  by target platform; use locked sharing for package managers whose caches cannot tolerate concurrent writers.
- Keep cache mounts disposable. Never rely on their contents for correctness or copy them into the runtime stage.
- Install system packages without recommendations when supported. Refresh the package index and install in the same
  layer, remove indexes from that layer, and avoid a general system upgrade.

## Separate stages and artifacts

- Split dependency acquisition, compilation, tests, and runtime into named stages. Copy only the runtime artifact and
  its required libraries into the final stage.
- Reuse a common base stage for related targets instead of duplicating nearly identical Dockerfiles.
- Produce the framework's minimal deploy artifact when it has an official mechanism, such as a filtered monorepo
  deployment or standalone server output.
- Keep test source outside a reusable test-environment image when the repository mounts the checkout read-only at
  execution time. Verify that the built image does not accidentally contain the suite.
- Place built development environments outside a path that a checkout bind mount will cover.
- Copy from another image or dependency stage only through an explicit version tag protected from overwrite. Keep an
  intentional update policy and authenticate offline artifact sources just as strictly as network downloads.
- Apply a build-time patch to an installed dependency only as documented debt: pin the source, assert the exact
  pre-patch content, fail closed when it differs, and exercise the patched behavior.

## Build for the intended platform

- Use BuildKit platform arguments such as `BUILDPLATFORM`, `TARGETPLATFORM`, `TARGETOS`, and `TARGETARCH` when the
  build selects or compiles architecture-specific artifacts.
- Verify checksums or signatures for downloaded artifacts after selecting the target architecture.
- Prefer native compilation or supported cross-compilation for compute-heavy builds. Use emulation deliberately and
  report that its performance and behavior remain a separate validation surface.
- Force a platform only when the desired artifact has no native variant and the user accepts emulation.

## Protect the supply chain

- Start from a trusted, minimal base that satisfies the runtime contract.
- Use exact version tags for production and for external `COPY --from` sources. Require the registry or publisher to
  prevent released tags from being overwritten, and keep a visible, reviewed process for updating tags and rebuilding
  images.
- Verify every distributed download with a pinned checksum or trusted signature before execution or extraction. Use
  remote `ADD` only with its checksum support and an immutable URL.
- Use `RUN --mount=type=secret` for build credentials and `RUN --mount=type=ssh` for SSH agent access. Never use
  `ARG` or persistent `ENV` for secrets.
- Record source revision, image source, and version metadata with standard OCI labels when the release pipeline
  supplies those values. Do not derive them by copying the repository history.
- Generate provenance, SBOMs, vulnerability results, and signatures through the project's release pipeline when they
  are part of its artifact policy; do not fabricate a parallel local policy in a Dockerfile.

## Define a predictable runtime

- Run the final process as a non-root user. Use stable UID and GID values when host-mounted ownership requires them,
  and use `COPY --chown` instead of a later recursive ownership repair.
- Permit a short privileged initialization only when it performs a necessary ownership or setup action and then
  reliably drops privileges before the application starts.
- Use exec-form `ENTRYPOINT` and `CMD`. For a tool image, put the fixed executable in `ENTRYPOINT` and replaceable
  default arguments in `CMD`.
- End a wrapper entrypoint with `exec "$@"` or an equally direct exec of the application. Keep wrapper logic small,
  deterministic, and free of secret tracing.
- Add a minimal init only when the application creates children or does not reap them correctly. Do not use init as a
  substitute for correct signal handling.
- Keep runtime configuration in runtime inputs. Use build arguments only for non-secret build choices; remember that
  public frontend values may become part of the artifact.
- Install only runtime packages in the final stage and remove compilers, package managers, shells, or debugging tools
  unless the runtime contract actually requires them.

## Choose the right source instruction

- Prefer `COPY` for files that must remain in the image.
- Prefer a bind mount on a `RUN` instruction for temporary build inputs that must not persist.
- Use cache mounts only for reusable, non-authoritative caches.
- Use secret and SSH mounts for credentials.
- Never rely on deleting a secret in a later layer; the earlier layer still contains it.

## Keep exceptional patterns bounded

- Use an inline Dockerfile in Compose only for a trivial, local image whose recipe is unlikely to grow or be reused.
  Move it to a named Dockerfile as soon as linting, caching, reuse, or review becomes material.
- Build multiple service targets from a shared base when their dependency contract is common. Keep each final target
  explicit so Compose and CI cannot silently select the wrong runtime.
- Build a tool image with a predictable interface and a harmless default command. Do not hide argument forwarding in
  shell interpolation.
