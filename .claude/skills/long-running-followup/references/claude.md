# Claude Code

Use a general-purpose native worker with inherited tools and permissions. Select the requested
model and effort through supported native or launcher configuration. A family alias alone is not
version proof: verify the child's resolved model and effort; do not silently accept another profile.

Distinguish a command's completion notification to its worker from the worker's handback to its
parent. A worker final that says it is waiting can notify the parent before its command finishes.
Prefer finite foreground commands inside a background worker, with a supported tool timeout.
For detached commands, use a native wait or an existing deterministic wait tied to the original
operation, keeping the same worker without an interim handback. If neither route is available,
report quiet delivery as unsupported; do not promise that wording suppresses host notifications.
Preserve already-started work and its verified completion route. Do not restart it, add model-driven
polling or add another monitoring worker. Check tools, permissions and lifetime before using a route.

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
