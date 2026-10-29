# Research sources

Background checked on 2026-10-29; not required for normal monitoring.

- [Codex scheduling](https://learn.chatgpt.com/docs/automations#schedule-a-task-inside-a-chat)
  distinguishes chat heartbeats from standalone recurring work. Current runtime schemas own
  their exact capabilities and authorization requirements.
- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) describes an API
  optimization, not this app's cache policy or free model turns.
- [Claude background subagents](https://code.claude.com/docs/en/sub-agents) document completion
  notifications; availability still depends on the current runtime.
- [OpenClaw delivery](https://docs.openclaw.ai/tools/subagents/announce) separates execution from
  delivery and suppresses duplicates. Its private machinery is not portable.
- [OpenCode background agents](https://opencode-claude-code-plugin.dev/guides/background-subagents/)
  use push completion; this does not authorize installing the plugin.
- [Compact CI monitor](https://github.com/ll7/robot_sf_ll7/pull/2683) illustrates compact evidence
  tied to the expected revision, not measured savings in this environment.
- [Reported polling waste](https://github.com/anthropics/claude-code/issues/90443) motivates fewer
  activations; its token figures are not an independently verified benchmark.

Any savings comparison must count parent/child activations, input/output tokens, retries,
delivery calls and latency. Prepared scenarios alone prove neither wakeup nor savings.
