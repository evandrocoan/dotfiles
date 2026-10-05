---
name: windows
description: >-
  Handle Windows-specific development workflows when PowerShell argument passing,
  paths or reparse points, or portable tools and managed runtimes affect the work.
  Use for Windows setup and validation, not for ordinary cross-platform edits
  that merely happen on Windows.
---

# Windows development workflows

Use this skill for platform mechanics. The owning project defines its required tools,
versions, lockfile, and validation commands. An application's embedded interpreter is
separate from a Python interpreter used to run maintenance tools.

## Establish the execution boundary

- Identify whether the command runs in native PowerShell, `cmd`, MSYS2, WSL, or an
  application host. Use paths and executables for that host; do not assume their
  home directories or Python installations are interchangeable.
- Before editing through a junction or symbolic link, inspect its `LinkType` and
  `Target` with `Get-Item -Force`, resolve the destination, and verify the owning
  repository and worktree. A Windows `~` and an MSYS2 `~` may resolve to different
  directories even when their skill entries link to the same source.
- Keep repository-owned links relative. A cross-volume Windows exposure link may
  need an absolute, machine-local target; keep that link out of shared artifacts.

## Run native commands from PowerShell

- Invoke an executable stored in a variable with `& $executable` and pass native
  arguments separately. Do not build a command string and evaluate it to handle
  quoting. For structured arguments such as JSON, verify what the program received
  if the result is silent or unexpected.
- Use PowerShell cmdlets with `-LiteralPath` for paths that may contain wildcard
  characters. Keep discovery and filesystem mutation in the same shell. Before a
  recursive move or removal, resolve the absolute target and verify it stays
  inside the authorized directory.
- Preserve standard error and inspect any prompt before continuing a long-running
  command. A quiet process alone does not prove that it is waiting for input.

## Prepare portable tools and isolated Python

Choose the tool and installation strategy under the project's instructions and
`dependency-decisions` before acquiring it. For a portable `uv` route on Windows:

1. Select the official [release archive](https://github.com/astral-sh/uv/releases)
   for the machine architecture, verify it against that release's checksum, and
   extract it into a task-owned directory. Call `uv.exe` by its exact path; a
   portable executable does not require changing the user `PATH` or shell profile.
2. Put uv's managed Python installations, Python executable links, and cache in
   task-owned directories using process-scoped `UV_PYTHON_INSTALL_DIR`,
   `UV_PYTHON_BIN_DIR`, and `UV_CACHE_DIR`. When uv owns the project environment,
   set `UV_PROJECT_ENVIRONMENT` to a task-owned directory too. Check the installed
   uv version before using `UV_PYTHON_NO_REGISTRY=1` to prevent Windows registry
   discovery and registration. On older versions, check whether
   `uv python install --no-registry` is supported. Merely relocating `uv.exe` does
   not relocate these data stores or prevent registry registration.
3. Request the Python version required by the project with `uv python install`;
   find the installed interpreter with
   `uv python find --no-project --managed-python <required-version>` and
   invoke that executable directly when uv only supplies Python. Use `uv run`
   only when uv is meant to manage the command's environment: it can lock and
   synchronize a discovered project. For an unrelated standalone command, use
   `uv run --no-project` with dependencies already approved for that task. Add
   `--locked` for an authoritative uv lockfile when the check must not update it;
   this still permits environment synchronization. Keep the project's own test
   and formatting commands in that project, rather than baking them into this
   skill.
4. Verify the actual interpreter path and version from the environment running
   the command. Passing a maintenance-tool suite does not establish that an
   embedded application or plugin host can load the same code.

Check the executable version, checksum, resolved environment locations, command
results, and repository diff before reporting validation. State which runtime or
integration boundary was not exercised. Remove only task-owned temporary files
after verifying their resolved paths; retain them when the user needs the setup.

The [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/),
[environment variable reference](https://docs.astral.sh/uv/configuration/environment/),
and [storage reference](https://docs.astral.sh/uv/reference/storage/) own the
current uv options and defaults.
