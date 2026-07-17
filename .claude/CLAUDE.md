# Global Claude Instructions

## General

When browsing the web, if bot verification begins, wait for the user to complete
the verification and then continue the task. Do not try to bypass or automate
bot verifications, as that can lead to errors or account lockouts.

Do not change my code formatting style when fixing it.

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

## Commit message example

```
Allow git read-only commands without permission prompts

Adds status, log, and diff to the allow list so routine inspection
commands do not interrupt the workflow with permission dialogs. Write
operations such as commit and push remain unaffected and will still
require explicit approval.
```
