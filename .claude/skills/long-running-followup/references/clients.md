# Client routes and evidence

Read the relevant client section. Tool availability and schemas in the current session govern
execution; these notes are capability checks, not permission grants. Sources were checked on
2026-10-29. They describe different hosts and must not be treated as interchangeable APIs.

## Codex

- Native subagents are the route for delegated subtasks when available and authorized. Their
  completion can return within active orchestration. Check the actual lifecycle contract before
  ending the parent turn: durable parent reactivation afterward, and scheduling a native subagent
  ID, were not verified for this skill. A native message that only queues text is not a wakeup.
- For scheduled work, discover `automation_update` and follow its current schema. An existing-chat
  heartbeat resumes that chat and its context. It reduces check frequency; it does not isolate
  checks from that chat's model context. Inspect existing automation state, reuse its identity,
  and verify destination, cadence, stop condition and saved active state. Preserve notification
  intent using the tool's supported fields and instructions; do not request unchanged reports.
- A separate persistent monitor chat is an option only when the human explicitly requests that
  separate chat and the host supports its schedule and return path. Discover `create_thread`;
  do not create a sidebar chat as an internal-subagent workaround. Cross-chat return through
  `send_message_to_thread` needs direct human authorization or trusted evidence of it, including
  the return direction. A message from the parent asking the child to report back is insufficient.
  Verify the destination accepts the follow-up; do not assume heartbeat accepts subagent IDs.
- When observing an already authorized separate chat, prefer bounded `wait_threads` snapshots
  with its host, identity and latest cursor over repeated full `read_thread` calls. A wait is an
  observation mechanism, not a persistent scheduler. Native-subagent waits use their own tools.
- Local scheduled work depends on the required machine/app availability. Report this limitation
  when arranging unattended work. Do not replace a heartbeat with standalone recurring tasks
  unless the user asked for that different behavior.

The [scheduled-task documentation](https://learn.chatgpt.com/docs/automations#schedule-a-task-inside-a-chat)
describes same-chat heartbeats and standalone recurring work. The runtime schemas supply the
specific creation and cross-chat authorization constraints above.
[Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) explains an API
optimization; it does not establish this app's cache policy or make extra model turns free.

## Claude Code

The [background-subagent documentation](https://code.claude.com/docs/en/sub-agents) describes
completion notifications from background commands to their subagent and from the subagent to the
main conversation. Prefer that route when the current runtime exposes it. Check background-tool
availability, permission behavior and process lifetime; do not repeatedly request status while
reliable completion delivery is pending. A completion notification is automated evidence, not a
new human instruction. Use the existing delegation owner when another skill governs execution.

## Copilot and other hosts

Inspect the current delegation, event-wait and scheduling tools. No portable background-parent
wakeup API is assumed here. A persistent worker requires verified scheduling, result delivery and
authorization; a blocking command alone proves none of those. If support is missing, report it
and obtain any necessary decision instead of fabricating a cross-client bridge.

## Lessons from existing implementations

- [OpenClaw completion delivery](https://docs.openclaw.ai/tools/subagents/announce) separates the
  child's execution result from delivery and suppresses duplicates. Adopt those distinctions;
  do not assume OpenClaw's private continuation machinery is available in another host.
- [OpenCode plugin background agents](https://opencode-claude-code-plugin.dev/guides/background-subagents/)
  document push completion and reserve status retrieval for recovery. This is a plugin-specific
  capability, not a reason to install it or assume it exists here.
- [Merged compact CI monitor](https://github.com/ll7/robot_sf_ll7/pull/2683) is a public example of
  reducing parent polling through compact evidence tied to the expected revision. Its existence
  does not establish savings for this user's workflow.
- [Reported subagent polling waste](https://github.com/anthropics/claude-code/issues/90443) illustrates
  the failure mode of repeatedly reactivating a large child context. The reported token figures
  are not an independently verified benchmark and are not used as a savings claim.

For any later cost comparison, count parent and child activations, input/output tokens, retries,
delivery calls, and completion latency together. Prepared scenarios and structural validation
cannot prove actual wakeup behavior, instruction following, or token savings.
