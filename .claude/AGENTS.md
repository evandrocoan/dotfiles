# Global agent instructions

Never redirect standard error to `/dev/null` (`2>/dev/null`). Hidden errors make
failures impossible to diagnose.

## Startup and workspace scope

At the start of work in each workspace root, before running project commands or
editing files, locate and read its root `AGENTS.md` if present. Use `CLAUDE.md`
only as a compatibility fallback when `AGENTS.md` is absent, and follow an
`@AGENTS.md` import by reading the target directly. Commands used only to locate
or read instruction files are permitted before this step. Read each file once
unless it changes or a new workspace root is added.

Project instructions may refine global workflow assumptions, but must not relax
global safety, authorization, workspace-scope, or destructive-action boundaries.

## Question-only turns

- Treat a user message whose last non-whitespace character is `?` or `w` as a
  question. A trailing `w` may be an accidental result of typing `?` with AltGr.
- For such a message, only answer the question. Read-only inspection of files,
  diffs, logs, or state, including through tools or commands, is allowed when it
  is necessary to answer accurately.
- Do not edit anything, run tests, implement changes, create or execute a plan,
  resume pending work, or perform any action that changes local or remote state.
- A question about missing or incomplete work, or about what something means, is
  not authorization to perform that work. Wait for a later, explicit instruction
  that does not end as a question before acting.

### Missing repositories and workspace scope

Treat `workspace_roots` as the complete authorized local repository discovery
scope unless the user explicitly says otherwise. When a task requires local
file work in a repository that is not listed there:

1. Stop before searching sibling directories, parent directories, the home
   directory, editor metadata, or any other location outside the workspace.
2. Tell the user exactly which repository or checkout is missing.
3. Ask the user either to add the checkout to the workspace or to explicitly
   authorize a search outside it.
4. Search outside only after receiving that authorization, and limit the search
   to the smallest plausible location.
5. If an authorized checkout is outside the writable roots, request filesystem
   access before editing it. Never use a remote file or commit API to modify
   repository contents in place of the authorized local working tree. Read-only
   remote inspection remains allowed when the task calls for it.
6. Prefer the authorized local working tree for file work. Read its root
   `AGENTS.md`, or its `CLAUDE.md` compatibility fallback when no `AGENTS.md`
   exists, inspect its current branch and status, and preserve all existing
   changes.
7. Treat remote repository tools as read-only unless the user explicitly
   requests the corresponding remote mutation.

## General safeguards

- When web browsing reaches bot verification, wait for the user to complete it.
  Never bypass or automate the verification.
- Preserve the existing code formatting style when making focused changes.
- If a required assumption proves false, stop before changing implementation
  strategy. Report the concrete evidence and ask the user how to proceed. Do
  not invent a workaround, substitute another branch or repository layout, or
  copy files across branches. Never silently choose a standard-library-only or
  custom implementation merely to avoid adding or installing a dependency. If
  a purpose-built dependency is a reasonable option, load
  `dependency-decisions`, compare it explicitly, and obtain the user's choice
  before implementation.
- Never create another Git worktree, rebase, merge, rewrite history,
  force-push, or cherry-pick unless the user asks for that operation.
- When asked to write code, do not add documentation or README files unless the
  user explicitly requests them. Do not add unrelated tests; add or modify only
  tests needed to verify the requested behavior, and load `test-quality` before
  doing so.
- Name alternative Dockerfiles with the environment before `.Dockerfile`, such
  as `dev.Dockerfile`; never use a suffix such as `Dockerfile.dev`.

## Language and portable files

Write AI-facing instruction files in English. Preserve literal strings an agent
must emit and instructions that pin generated output to another language.

For every other existing file, match the language of the surrounding content.
If a file already mixes languages, preserve the local convention during focused
edits. Ask which language to use only when adding substantial new content whose
intended language cannot be inferred, or when normalization is requested.

Architecture artifacts are an explicit exception. Architecture indexes, plans,
ADRs, and decision records must always be written in English according to the
`architecture-records` skill. When an affected architecture artifact is not in
English or mixes languages, translate the entire artifact and its coupled index in
the same change instead of preserving mixed-language prose.

Use relative paths for files, configuration, and symbolic links intended to be
shared across users or machines. Never store user-specific or machine-specific
absolute paths in shared artifacts.

Expose every shared Claude, Codex, and Copilot skill at
`~/.claude/skills/<skill-name>`. Keep locally owned skill packages canonical
there. When a repository owns a shared skill, preserve that repository as the
source and use a relative symbolic link at the same `~/.claude/skills` path;
never copy it into a second maintained package. Expose every shared entry through
`~/.agents/skills/<skill-name>` with the relative target
`../../.claude/skills/<skill-name>`. Leave Codex system skills under
`~/.codex/skills/.system` untouched.

## Copyable outbound messages

Whenever drafting a complete message that the user intends to send or paste
into another service, place only the ready-to-send text inside a fenced `text`
code block. Keep explanations, alternatives, and delivery notes outside that
block. Do not format the sendable message as a Markdown blockquote or prefix
its lines with quotation markers. Use another format only when the user asks
for it or when the content is not intended for direct copying.

## Git authorization

Treat the user's requested Git outcome as authorization for its routine,
in-scope steps. Opening a pull request or merge request includes creating a
suitable source branch, committing the scoped changes, and pushing the branch.
It never includes merging, force-pushing, rewriting history, or unrelated work.

For commits, pushes, branches, pull requests, GitLab merge requests, repository
issues, reviews, or pipelines, load and follow the `git-delivery` skill.

## Shared skill registry

Treat every entry exposed under `~/.agents/skills/` as an installed shared skill.
Before acting, match the task against this complete registry and load the entire
`SKILL.md` for every applicable entry. Never skip an applicable skill because the
task appears familiar or because another skill also applies. When a skill is added,
renamed, or removed under `~/.agents/skills/`, update this registry in the same
change. If the registry and filesystem disagree, inspect the filesystem, report the
stale registry, and correct it before relying on the missing entry.

- `architecture-records`: Create, review, implement, audit, or supersede durable
  cross-component architecture records and lifecycle states. Load it together with
  `documentation`; also load `plan-implementation` before implementing or making a
  non-trivial correction governed by a record.
- `bash-scripts`: Create, edit, review, or debug Bash scripts and Bash snippets.
- `dependency-decisions`: Select, add, replace, upgrade, remove, or install any
  library, package, framework, service, or system dependency. Never install a
  missing dependency automatically.
- `docker`: Create, edit, review, build, run, or troubleshoot Dockerfiles, Compose,
  BuildKit/Buildx, container-backed CI, images, services, volumes, networks,
  healthchecks, or container runtime behavior.
- `documentation`: Create, edit, review, reorganize, or synchronize Markdown,
  README files, runbooks, changelogs, and AI-facing instruction files.
- `excalidash-diagrams`: Create or edit structured, editable Excalidraw or
  ExcaliDash diagrams. If unavailable, report that instead of improvising another
  diagram workflow.
- `git-delivery`: Create or inspect branches, commits, pushes, issues, pull requests,
  GitLab merge requests, reviews, or pipelines, while preserving authorization and
  existing work.
- `gitlab-ci`: Create, edit, review, secure, validate, or troubleshoot GitLab CI/CD
  pipelines, components, jobs, runners, variables, artifacts, caches, and deployment
  gates.
- `plan-implementation`: Plan or implement any non-trivial multi-file, multi-stage,
  cross-component, protocol, migration, replay, paid-validation, or externally
  mutating change. Use its persistent Markdown plan whenever its persistence gate
  applies, and complete its mandatory closure audit before declaring success.
- `test-quality`: Create, modify, review, debug, or run automated tests, including
  unit, integration, end-to-end, regression, smoke, property, concurrency, and
  recorded-replay tests and their recording lifecycle.

Runtime-owned Codex system skills and plugin-provided skills are discovered through
their runtime catalogs and may not be available to every AI client. Do not add them
to this shared registry unless they are deliberately exposed under
`~/.agents/skills/`.

## Machine constraints and interactive commands

The development machine has an extremely slow mechanical disk. Do not run
multiple disk-intensive terminal commands concurrently. Run dependent commands
sequentially, and inspect each result or current state before starting the next.
Long-running servers, watchers, and monitors may remain active while independent
commands run when necessary, but inspect their startup output or state first. Do
not cancel a command merely because it is slow or has stopped producing output.

Before running a command that may prompt for input, use its documented
non-interactive mode only when every required choice is unambiguous and already
authorized. Never pipe `yes` into a command or blindly accept defaults. If the
exact choice is not already explicitly authorized, ask the user before answering
a prompt concerning credentials, trust, license acceptance, overwriting files,
dependency changes, or destructive operations.

Whenever a command remains running after a tool response, inspect all newly
returned output before waiting again. Look specifically for interactive prompts,
including prompts printed without a trailing newline. If the latest output is
requesting input, treat the command as waiting rather than slow and do not
continue waiting. Respond through the existing process when the answer is
unambiguous and authorized. Otherwise, report the exact prompt and ask the user
immediately.

Silence alone is not evidence of an interactive prompt. When the output is
inconclusive, inspect the process state without cancelling it.

## Memory policy

Do not store project decisions, preferences, or session context in the private
memory system under `~/.claude/projects/`. Persist durable shared context in the
project's version-controlled instruction or architecture files. Use this global
file only for behavior that truly applies across projects.
