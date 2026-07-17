# Global Claude Instructions

## Commits

Never create a git commit unless the user explicitly asks for it.

When the user requests a commit:

1. Read each changed file to understand what was modified and why
2. Analyze the architectural impact of the changes
3. Write a professional commit message as a plain text code block

Commit message rules:
- No conventional commit prefixes (no `feat:`, `fix:`, `chore:`, etc.)
- Title line must be concise and descriptive, max 72 characters
- Body lines must wrap at 80 columns
- Explain *why* the change matters, not just what changed
- Separate title from body with a blank line

Example format:

```
Allow git read-only commands without permission prompts

Adds status, log, and diff to the allow list so routine inspection
commands do not interrupt the workflow with permission dialogs. Write
operations such as commit and push remain unaffected and will still
require explicit approval.
```
