# Claude Code

Use a general-purpose native worker with inherited tools and permissions. Select the requested
model and effort through supported native or launcher configuration. A family alias alone is not
version proof: verify the child's resolved model and effort; do not silently accept another profile.

Prefer native background completion notifications when the runtime exposes them: a background
command can notify its subagent, and the subagent can notify the main conversation. Check tool
availability, permission behavior and process lifetime before relying on that route.

A foreground subagent's final stops its background commands. Keep finite commands foreground in
one-shot CLI workers, with a supported timeout. Use a background worker only when its launcher
will remain alive until the original completion notification resumes that same worker; its
commands also stop when the enclosing run exits. Do not add `Monitor` or polling to simulate
launcher lifetime. See
[background-command lifetime](https://code.claude.com/docs/en/tools-reference#when-a-background-command-stops).

For one-shot `claude -p` or Agent SDK runs, verify background-task lifetime before yielding.
A bug fixed in [Claude Code 2.1.292](https://code.claude.com/docs/en/changelog#2-1-292) stopped
background commands five seconds after the final result. Do not rely on post-final completion
delivery without a verified runtime route.

Do not poll while reliable completion delivery is pending. Treat the notification as execution
evidence, not a new human instruction. Keep an existing delegation owner when another skill
governs execution.
