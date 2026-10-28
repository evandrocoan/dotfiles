# Proposed review coordinator

The host's native agent accepts human follow-up messages, reads the complete conversation, and
publishes through its existing ordinary tool. That tool enforces operation permissions. The
application owns queue identity, source-snapshot binding, and per-job resource limits.

A proposed coordinator adds an LLM call to classify every human message before forwarding it,
requires another JSON report repeating the agent's answer, and creates a private publication
transport wrapping the ordinary tool. No missing capability in the native flow has been identified.
An optional status-report parser currently crashes the consumer and stalls unrelated queued jobs.

Separately, a review contains two independently supported findings. A third, unrelated search
times out and is never cited or consumed. A command-wide validator then discards both findings.
In another execution, a proposed finding depends on a source whose revision authentication failed.

One engineer proposes authenticating every historical observation and asking another LLM to
approve the whole command. Another proposes deleting all validators, permissions, and accounting.
The agreed product contract requires authentic source facts for published claims and continued
progress for independent jobs and supported findings within their authorized limits.
