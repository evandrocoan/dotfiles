# Global Claude Instructions

Never redirect stderr to /dev/null (2>/dev/null) in any command, because it hides errors and makes failures impossible to diagnose.

## General

When browsing the web, if bot verification begins, wait for the user to complete
the verification and then continue the task. Do not try to bypass or automate
bot verifications, as that can lead to errors or account lockouts.

Do not change my code formatting style when fixing it.

When editing or adding content to an existing file, always match the language
already used in that file. If the file is in English, write in English. If the
file is in Portuguese, write in Portuguese. Never mix languages within the same
file unless the existing content already does so.

When a package or import is missing, do not install it automatically. Ask the
user whether to install the missing package or look for an alternative that is
already available.

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

Never write documentation that embeds data which becomes stale as the
code evolves. Specifically:

- No hardcoded counts ("28 tools", "3 graphs", "11 entity types") —
  omit the number or link to the authoritative source (code, CLAUDE.md
  changelog anchor) instead.
- No specific version numbers in prose unless they describe a historical
  event ("removed in v2.1") rather than current state.
- No snapshots of lists that are maintained in code (tool names, module
  names, CLI subcommands, env var names) unless the list is reproduced
  directly from the source and the file makes clear it must be kept in sync.

When describing quantities, use qualitative language ("typed, tenant-scoped
tools", "several cross-call rollup passes") so the description stays true
even as the codebase grows.

## Memory policy

Do not use the private memory system (`~/.claude/projects/`) to store
decisions, preferences, or context learned during sessions. Instead, persist
all relevant information directly in the project's `CLAUDE.md` or this global
`~/.claude/CLAUDE.md` so that every user, machine, and AI session has access
to the same up-to-date context via version control.

## Shell scripts

Ao escrever ou editar scripts bash, consulte primeiro
`~/.claude/guidelines/bash-scripts.md` para as convenções de estilo.

## ExcaliDash / Excalidraw MCP workflow

When asked to create, draw, or generate a diagram, follow this workflow using
the registered MCP tools:

1. `read_me` (excalidraw) — load the element format reference
2. `create_view` (excalidraw) — author and render the elements JSON
3. `read_checkpoint` (excalidraw) — extract elements using the returned checkpointId
4. `save_to_excalidash` (excalidash) — persist the drawing; return the URL to the user

Full tool reference: @/myfiles/Programs/ExcaliDash/mcp/README.md

## Commit message example

```
Allow git read-only commands without permission prompts

Adds status, log, and diff to the allow list so routine inspection
commands do not interrupt the workflow with permission dialogs. Write
operations such as commit and push remain unaffected and will still
require explicit approval.
```
