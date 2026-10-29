# Claude Code

Prefer native background completion notifications when the runtime exposes them: a background
command can notify its subagent, and the subagent can notify the main conversation. Check tool
availability, permission behavior and process lifetime before relying on that route.

Do not poll while reliable completion delivery is pending. Treat the notification as execution
evidence, not a new human instruction. Keep an existing delegation owner when another skill
governs execution.
