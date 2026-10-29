# Codex

Tool schemas in the current session govern execution.

- Use native subagents for authorized delegated subtasks. Completion can return to active
  orchestration. Verify the lifecycle contract before ending the parent turn: durable wakeup
  afterward and scheduling of native subagent IDs are not established by this skill.
- For scheduled work, discover `automation_update`. A heartbeat resumes its target chat and
  context. Reuse the existing monitor; verify destination, cadence, stop condition and saved
  active state. Keep unchanged observations silent unless updates were requested.
- A separate persistent monitor chat requires an explicit human request. Discover `create_thread`
  rather than using sidebar chats as internal subagents. Cross-chat return through
  `send_message_to_thread` requires direct human authorization or trusted evidence of it, including
  the return direction. A parent-written handoff alone is insufficient. Verify acceptance; a
  queue-only message does not prove wakeup.
- Observe authorized separate chats with bounded `wait_threads` snapshots and current cursors,
  rather than repeated full history reads. Native subagents use their own event/wait tools.
- Local scheduled work requires machine/app availability. Preserve the requested heartbeat
  behavior; do not substitute standalone recurring tasks without authorization.

These are capability distinctions, not additional permission grants. Extra model turns consume
resources even when prompt caching applies.
