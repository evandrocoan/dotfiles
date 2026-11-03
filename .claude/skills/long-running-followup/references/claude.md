# Claude Code

Use a native monitoring worker with inherited tools and permissions. Select the requested model
and effort through supported configuration; a family alias alone does not prove the resolved model.
The worker observes the existing execution; it does not launch or perform the underlying work.

Distinguish a command's completion notification to its owner from the observer's handback to its
parent. A native final saying "waiting" can notify the parent before completion. Keep wait-only
commands foreground with a supported tool timeout when possible. A timeout on the wait does not
authorize ending monitoring or cancelling the original execution.

Use native delivery or an existing deterministic wait tied to the execution. If neither route is
available, report the gap while preserving the original execution and its completion route. Do not
invent a bridge, add model-driven polling or add another monitoring worker for the same wait.

A foreground subagent's final stops its background commands, including unfinished wait commands.
Keep the launcher alive for any background observer until actual terminal delivery. Its lifetime
must not be assumed from a one-shot `claude -p` or Agent SDK result. See
[background-command lifetime](https://code.claude.com/docs/en/tools-reference#when-a-background-command-stops).
