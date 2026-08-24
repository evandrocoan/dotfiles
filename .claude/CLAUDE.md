# Global Claude Instructions

Never redirect stderr to /dev/null (2>/dev/null) in any command, because it hides errors and makes failures impossible to diagnose.

## Reading CLAUDE.md before acting

Before running any command or making any file edit, read the CLAUDE.md of
every working directory in the session — both the primary directory and all
additional working directories listed in the session context. Each project
may have its own environment constraints, tool execution rules, and
architectural decisions that override default behavior. Skipping any of them
causes incorrect actions that cannot be undone safely.

## General

When browsing the web, if bot verification begins, wait for the user to complete
the verification and then continue the task. Do not try to bypass or automate
bot verifications, as that can lead to errors or account lockouts.

Do not change my code formatting style when fixing it.

AI-facing instruction files must always be written in English, regardless of
the surrounding codebase language. This covers any file whose primary purpose
is to instruct an AI agent — not just CLAUDE.md, but also skill and slash
command definitions (`.claude/commands/*.md`, `.claude/skills/**`), `AGENTS.md`,
`.github/copilot-instructions.md`, and equivalents. English gives the model a
small but real edge in instruction-following, and keeps these files consistent
with each other.

Two things inside an English instruction file stay in their original language:
- Literal strings the agent must emit verbatim — commit messages, menu/button
  labels, output templates, example values.
- Instructions that pin the language of generated output (e.g. "write the note
  in Portuguese", "generate the Mattermost message in Portuguese"). The
  instruction prose is English; the output language it specifies is unchanged.

When editing or adding content to any other existing file (code, docs, issue
files, anything that is not an AI-facing instruction file), match the language
already used in that file. If the file is in English, write in English. If the
file is in Portuguese, write in Portuguese.

If a non-instruction file already mixes languages, ask the user before
proceeding:
- Continue adding content in the dominant language?
- Pick one language and apply it to the new content only?
- Correct the entire file to a single language?

When a package or import is missing, do not install it automatically. Ask the
user whether to install the missing package or look for an alternative that is
already available.

## Portable shared paths

When files, configuration, or symbolic links are intended to be shared across
users or machines, never store user-specific or machine-specific absolute
paths. Use paths relative to the containing file or symbolic link and verify
the stored target after creating it.

For skills shared between Claude and Codex, keep the canonical skill at
`~/.claude/skills/<skill-name>` and expose it through
`~/.codex/skills/<skill-name>` with the relative symbolic-link target
`../../.claude/skills/<skill-name>`. Never store an expanded home-directory
path in that link.

## Dependency choices

Before choosing dependencies for new code, ask the user which libraries or
dependency strategy they prefer. Present the reasonable options, including
appropriate third-party libraries and a standard-library-only approach when it
is genuinely viable. Explain the relevant tradeoffs — such as ergonomics,
maintenance, performance, portability, and installation cost — and recommend
the option that best fits the task before asking the user to choose.

Do not default to the standard library, avoiding dependencies, or any specific
library without this discussion. Do not announce a dependency decision before
the user has chosen. A separate question is unnecessary only when the user has
already selected the dependency strategy or the repository contains an
explicit, applicable requirement that leaves no meaningful choice; state that
constraint before proceeding.

When asked to write code, do not create documentation, readmes, or tests
unless explicitly asked to.

## Test quality

Before creating, modifying, reviewing, debugging, or running automated tests,
always load and follow the `test-quality` skill.

The development machine has an extremely slow mechanical disk. All terminal
commands take much longer than normal. Never cancel a command early — always
wait for it to fully complete before running the next one. Never run multiple
commands back-to-back without waiting for each one to finish first.

## Markdown

When writing markdown, do not use CamelCase for section titles. Use normal
sentence case instead.

When writing markdown tables, always use spaces around the dashes in the
separator row: `| --- | --- | --- |` instead of `|---|---|---|`.

## Commits

Never create a git commit unless the user explicitly asks for it.

When the user requests a commit:

1. Read each changed file to understand what was modified and why
2. Analyze the architectural impact of the changes
3. Write a professional commit message as a plain text code block

Commit message rules:
- Always written in **English**
- No conventional commit prefixes (no `feat:`, `fix:`, `chore:`, etc.)
- Title line must be concise and descriptive, max 72 characters
- Body lines must wrap at 80 columns
- Explain *why* the change matters, not just what changed
- Separate title from body with a blank line
- Never add `Co-Authored-By` trailers

## Pull Requests

Never create a pull request unless the user explicitly asks for it.

When the user requests a pull request:

1. Read each changed file to understand what was modified and why
2. Analyze the architectural impact of the changes
3. Write a professional pull request description as a plain text code block

Pull request rules:
- Always written in **Portuguese (Brazil)**
- No emojis anywhere in the title or body
- Title must be concise and descriptive
- Body must explain *why* the change matters, not just what changed
- Describe the architectural context and motivation behind the changes

### GitLab merge requests through Git push options

When GitLab CLI or an MCP server is unavailable, create a merge request by
pushing the branch with GitLab push options. Set the target branch, title, and
description explicitly along with `merge_request.create`.

Push option values cannot contain literal newlines. For a multiline merge
request description, use the literal `\\n` escape sequence; GitLab converts it
to line breaks. Never URL-encode line breaks as `%0A`, because GitLab stores
that text verbatim.

`merge_request.title` and `merge_request.description` can also update an
existing merge request when supplied with a later push. Prefer an ordinary
branch update or the GitLab API/MCP for such edits; do not rewrite history
solely to alter metadata unless explicitly necessary and safe.

## CLAUDE.md and .github/copilot-instructions.md sync

When working in a project, keep CLAUDE.md and .github/copilot-instructions.md
in sync using the following logic:

- If `.github/copilot-instructions.md` **already exists**: add
  `@.github/copilot-instructions.md` at the top of `CLAUDE.md` so Claude
  also reads those instructions.
- If `.github/copilot-instructions.md` **does not exist**: create a symlink
  pointing it to `CLAUDE.md` so Copilot reads the same instructions:
  `ln -s CLAUDE.md .github/copilot-instructions.md`

## Documentation

Before writing or editing documentation or AI-facing Markdown instructions,
use the `documentation` skill. If skill discovery is unavailable, read the same
instructions at `~/.claude/guidelines/documentation.md` and follow them.

## Architecture records

Before creating, moving, reviewing, implementing, or superseding a durable
cross-component architecture plan or decision record, use the
`architecture-records` skill together with the `documentation` skill. If skill
discovery is unavailable, read
`~/.claude/skills/architecture-records/SKILL.md` and follow it.

Keep temporary delivery checklists in the issue or merge request. Keep durable
motivation, boundaries, risks, invariants, lifecycle status, and architectural
acceptance criteria in the repository's architecture records. Never present a
proposed record as current behavior.

## Memory policy

Do not use the private memory system (`~/.claude/projects/`) to store
decisions, preferences, or context learned during sessions. Instead, persist
all relevant information directly in the project's `CLAUDE.md` or this global
`~/.claude/CLAUDE.md` so that every user, machine, and AI session has access
to the same up-to-date context via version control.

## Dockerfile naming

Alternative Dockerfiles must be named with the environment as a **prefix**
before `.Dockerfile`, not as a suffix after `Dockerfile`:

- Correct: `dev.Dockerfile`, `test.Dockerfile`
- Wrong: `Dockerfile.dev`, `Dockerfile.test`

## Shell scripts

Before writing or editing Bash scripts, read
`~/.claude/guidelines/bash-scripts.md` for the style conventions.

## ExcaliDash / Excalidraw MCP workflow

When asked to create, draw, edit, or generate a structured diagram, always use
the `excalidash-diagrams` skill before taking action. If skill discovery is
unavailable, report that the skill is not installed instead of bypassing it
with a machine-specific path or an improvised MCP workflow.
