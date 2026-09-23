# Implementation plan: Agent conversation search

**Status:** Completed
**Mode:** Plan and execute
**Risk:** Non-trivial local and reversible

## Outcome and scope

- Add `codex-session-stats find` for local Codex and Claude conversation discovery, with current
  titles, client/session identity, dated excerpts, and exact source locations.
- Preserve existing statistics invocations. Add focused tests and global usage guidance in
  `.codex/AGENTS.md`, whose Claude consumer is the existing relative symlink.
- Keep all client histories and databases read-only. No remote operations, dependency changes,
  or authorization-policy changes are in scope. The user subsequently authorized a scoped local
  commit of the completed delivery; no push is authorized.

## Evidence and assumptions

- The script already uses argparse, JSON, pathlib, and read-only SQLite for Codex statistics.
- Codex stores duplicated message/event records and multiple rollouts for one session; the current
  database rollout may omit older material. Discover physical histories, not only current DB paths.
- `session_index.jsonl` carries current renamed Codex titles. Claude JSONL stores user/assistant
  content, sessionId/cwd, custom-title/ai-title records, and sidechain flags.
- Use sequential streaming with cheap byte prefilters before JSON parsing. This avoids loading
  large histories or repeatedly parsing tool results. Persistent indexing is outside this change;
  searches remain usable under the question-only read-only rule.
- Missing roots and malformed records must be visible in coverage diagnostics. An empty result
  must not be described as proof that a conversation never existed.
- No additional dependency or unresolved schema premise is required.
- Concurrent monitoring-test repair records a real group-signaling incident. Run the repository
  gate using its installed bubblewrap isolation: verified distinct PID namespace, UID 1000,
  read-only host root, private proc/dev/tmp/run and no network. Do not alter that repair's files.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| completed | Review the compact plan. | Focused author reread; no advisor tool available. |
| completed | Extend the existing script with find parsing and per-client message extraction. | Focused tests cover both formats, renamed titles, old rollouts, duplicates, MR boundaries, dates and filters. |
| completed | Document discovery procedure in global instructions and existing README operations section. | Global instructions and README explain query precision, source verification and coverage. |
| completed | Run focused tests, repository gate, real read-only searches, and closure. | 99 tests passed (44 monitoring and 55 script tests), including 15 search regressions; syntax gate passed in verified isolation. Real searches and source lines verified. |

## Review and replan

- Review mechanism: Focused author reread (advisor unavailable).
- Applied findings: Prefer full MR URLs; a matching message does not prove a code review occurred.
  Exclude tools/reasoning, subagents, and inherited transcripts by default. Make inherited context
  explicitly selectable and labelled. Group duplicate records and rollouts by client/session.
- Rejected findings: None.
- Replan if supporting observed formats requires new dependencies, client-state writes, or scope
  expansion. Preserve unrelated working-tree edits.

## Completion

- Evidence: Existing statistics CLI remains covered by an exact 60-second fixture. Both clients,
  renamed titles, original/migrated rollouts, metadata-only matches, output formats, Unicode/JSON
  escaping, repeated dates, role/project/session filters, malformed candidates, and read-only
  source bytes/mtimes passed. The missing-command regression failed before implementation; a
  quoted-query regression caught and verified the byte-prefilter correction. Final repository gate
  passed with no failures or skips; whitespace checks passed. Real full-URL search took about
  10 seconds across both clients and a Claude-only search took under one second; returned source
  lines were reopened and verified. The script remains executable, and Claude's global instruction
  symlink resolves to the updated canonical file. Final diff is scoped; unrelated edits preserved.
- Focused author pass: Passed. Corrected deduplication across distinct dates and escaped-query
  prefiltering. Reviewed parser-to-output path, source integrity, documentation and existing CLI.
- Unresolved limitations: No required work remains. Search is literal, streams JSONL on every run,
  and cannot infer whether a mention proves a review. Excluded tool/reasoning records and opt-in
  inherited/subagent context are documented. Source format extensions may need future adapters.
- Brief check: No brief on this subject.
- Verdict: Passed. The user authorized a local commit after implementation and validation.
