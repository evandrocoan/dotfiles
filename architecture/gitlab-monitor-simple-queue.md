# GitLab monitor simple queue

**Status:** Implemented. Supersedes [work ownership](gitlab-monitor-work-ownership.md).
The fresh consumer is installed; predecessor state and chats remain untouched and outside its intake.

## Decision and scope

The monitor owns one durable FIFO and one supervised consumer. Agents review and return domain
results; the script handles admission, publication, read-back and recovery. Preserve existing
repository identity, human requests and holds admitted by this consumer, actual reviewed progress
and publication provenance. Start with fresh monitor state and newly created MR chats. Leave
predecessor chats and state untouched: no import, adoption, relocation or instruction update.
No additional queue/MCP server, dependency or credential route.

**Workspace execution amendment:** Reviewers may execute commands, edit files, change
branches and run tests in the configured workspace folders and their necessary shared Git
metadata, without per-command approval. The monitor supplies the same durable workspace snapshot
to every reviewer in a round; the model chooses the repository, checkout and commands. Refresh
the named Codex project's folders only for a new round. Preserve original chat contexts and human
sources across fresh-chat creation when folders or shared instructions change. Consumer intake
remains read-only; direct manual app turns follow
the shared semantic instructions and are outside the consumer's launch serialization. Reviewers
do not receive the consumer's native control socket or state-write capability. Global defaults,
publication ownership, queue capacity and provenance protections remain unchanged.

Persist canonical ordered roots, primary directory, native project identity and actual Git
metadata paths before the first launch/input. A restart or later reviewer uses that same snapshot.
An archived round retains its original snapshot; only its successor resolves the live project
again. A same-name replacement project does not inherit authorization. Historical saved folder
lists do not prevent reading the current live list or authenticate a source against changed roots.

Codex selects a distinct thread-local permissions profile at creation, resume and turn start;
resume explicitly supplies the round's roots. Claude receives the same primary/additional
directories, scoped native Edit/Write rules and command sandbox settings without inherited hooks
or unrelated writable directories. Preserve intended model/effort and subscription credentials.
No unsandboxed retry is enabled. The immutable input remains readable without adding the queue
directory as a writable workspace. Necessary linked-worktree Git metadata may be outside the
configured roots; this exception does not include the main checkout's source directory.

Register original contexts for every Codex session created by this consumer, retaining older
sessions after chat rotation. Source authentication and pre-publication checks use that original
context. This registry neither adopts predecessor sessions nor updates loaded instructions.
Claude retains its existing native session history. One consumer still owns all public effects.

## One queue and one consumer

Jobs have three states: pending, running and completed, ordered by one global sequence across
all repositories. Pending jobs can carry a wait reason and retry time. Settle superseded unsent code revisions without model work; preserve independent human requests and scope. Commits arriving during work
remain pending. One dedicated singleton process lock protects the consumer. The consumer lock also excludes operator recovery/cutover; short SQLite transactions protect state
boundaries, while inventory HTTP runs outside that lock. Producers enqueue
transactionally and cannot interrupt the consumer. There is no competing reservation machine.

Each job binds authenticated repository ID, MR IID, mapped chat, immutable source, requested work,
internal epoch and exact native execution attempt. Persist exact automatic input before native
start and prove its acknowledgment or reconcile that exact delivery. Acceptance is not review.
Unknown native execution retains the running slot; elapsed time is not evidence of termination.

The agent returns a versioned domain result in the actual native final message: proposed comments,
replies or resolutions with evidence, actual reviewed head, concerns, a question or an outcome.
It never selects generations, events, reservation identifiers, execution tokens or receipts.
All former agent mutating CLI payloads fail safely; no delayed command can obtain another turn's
authority. Read-only snapshot/status remain available. Bind collection to the exact job/attempt/
native turn and re-read native source, context, epoch and job authority before accepting results.
A stale result cannot settle a successor. Persist the validated batch before its first send;
publication keys are stable domain identities, never action-list positions. Preserve prior results
and receipts in every continuation. The agent's final must not claim publication before read-back.
A question result cannot also contain public effects.

Native terminal status plus a valid result starts application of the saved domain batch. Keep
the job running and the global slot occupied until all intended public effects are confirmed or
explicitly settled and the outcome is recorded. Only then complete the job and progress immediately.
Unknown public delivery moves the unfinished job to pending with an inspection wait only when
the native execution is proven terminal; do not mark that job completed or advance its checkpoint.
Its MR remains blocked, while other MRs may proceed. Preserve
only the head actually reviewed by completed code-event work; human work never fabricates a code
event or advances the automatic code checkpoint.

## Ordered reviewer stages

An admitted job snapshots its ordered nonempty unique list of enabled reviewers. Every configured
reviewer runs once in that order, including after an earlier success or failure. One reviewer is
valid. There is no fallback mode, quota classifier or success-based skipping. Record each result
or failure honestly and continue to the next reviewer after the preceding execution is terminal.
A failed stage never contributes reviewed coverage. At least one complete valid review of the
exact target head is required before applying results or advancing a code checkpoint.

Authentication, network, credits, invalid output and other terminal failures all follow the same
continuation rule. Preserve partial evidence and confirmed receipts, but do not call a failed
stage a successful review. If every reviewer fails, retain unfinished work for bounded retry with
a visible reason. Unknown execution is still running rather than a proven failure: reconcile or
interrupt that exact execution and prove termination before starting another, preserving serial
capacity. Human questions retain their sufficient-answer hold; they are not authorization to
publish. Reviewer stages are fields of one job, not another queue or capacity authority.

Claude execution uses the existing signed-in background CLI with Remote Control. Preserve its
native session identity and authenticated original input/results; no fabricated Codex turn stands
in for Claude review. Historical Codex chats remain outside the new consumer. Results/questions stay in the reviewer's own
native app: Claude Remote Control or the Codex MR chat. Register fresh Claude sessions per review
when needed, preserving their source history and sufficient-answer routing with distinct original
source and execution identities; do not run an extra Codex model solely for presentation.
When the monitor configuration omits `claude_model`, use `claude-opus-5-5`; an explicit value
takes precedence. Omitted effort retains Claude's own effort settings. No new credential route.

## Stage barrier and consolidated publication

A successful stage is not job completion. Every configured reviewer must have run to a terminal
result or failure before publication or completion. Earlier success never skips a later reviewer;
earlier failure never cancels one. With at least one valid successful review, use actual successful
coverage and record every failure. If none succeeds, no publication or checkpoint advance occurs.
An unresolved human question, unsafe public operation or unknown native execution still prevents
settlement; these safety boundaries do not classify a failed reviewer as successful.

Pass earlier complete/partial findings and prior receipts to the next reviewer. The last successful
reviewer returns one consolidated batch, explicitly disposing of each earlier proposed concern
as retained, duplicate or rejected with evidence, or uncertain. Use semantic concern keys rather
than array positions. Duplicate concerns publish once. An unresolved conflict/uncertain concern
holds the affected work for a human decision; a later evidenced outstanding concern vetoes an
earlier resolution. The monitor verifies disposition coverage and retains the evidence/history;
it never chooses an LLM winner or unions conflicting resolve proposals mechanically. When a later
reviewer fails, use the last complete successful consolidated result after every enabled reviewer
has run, and label the actual coverage and failures. Persist the chosen consolidated
batch before the first send. No reviewer-stage success alone grants public effects.

## Human input and questions

Observe actual native human turns in mapped MR chats. Authenticate exact source text and its
terminal final result; do not infer source from the latest runtime turn. A human domain request
must contain an explicit semantic action assessment, exact text basis and bounded effect/
discussion scope. Register it to that original source and enqueue it. The consumer can apply its
prepared domain result only when still current and within scope; otherwise continue that same
registered request after capacity is available: in the same Codex chat or an explicitly registered
fresh Claude execution. Keep its original native source/question identity and record the
source-to-execution relationship before dispatch; copied history never grants human authority. Its continuation is human work,
not an automatic code event and not a new permission grant.

Question marks, trailing-w, explanations, preferences, registered automation and mixed input do
not admit mutable human work. Plain answers/explanations produce no job. Native user-channel
clients remain trusted locally; this is not proof of physical typing. An interrupted human intake
without a valid final assessment is preserved visibly as read-only recovery in this same jobs
queue. Before dispatching continuation B, persist its relationship to original human source A.
B's registered automation text is never human authorization. Recovery may interpret A but cannot
publish or clear a hold before a valid action or sufficient-answer assessment against A. Do not automatically re-run already answered plain questions.

A domain question is persisted with its actual final native anchor and must appear as a readable
plain-language final question, not solely inside structured metadata. After that turn terminates,
its job waits pending and other MRs may proceed. Every later job for the same MR remains blocked.
Resume only on a later sufficient native human answer to the completed anchor, preserving scope,
source, concerns and the prior hold history. Only an actual terminal native final can establish a question. If interruption occurs after saving
that result and before saving its hold, reconstruct the same anchored hold before another stage
or effect. Persist a required new-round reset with the sufficient answer, so a crash cannot apply
the pre-answer result. Partial native output is not an invented completed question or consent. This preserves holds within the new consumer; predecessor chats are not intake. Earlier sessions
created by this consumer remain valid human sources for their original requests and questions,
even when a later execution uses a different Claude session.

## Publications

The consumer validates repository, job authority, immutable reviewed head, current discussion,
semantic assessment and real diff coordinates before journaling a send. Invalid unsent anchors
leave no outstanding send intent. It owns the operation identity, body marker, provider send and
authenticated read-back. Publication identity is independent of retries/execution epochs; reuse
confirmed effects after repeated results, restart and partial batches. Recheck admission and
context at send boundaries; no new effects on closed/merged MRs.

Resolve is a compound domain operation: first explain, confirm the exact explanation, then
revalidate and resolve. The comparison may account only for that exact confirmed explanation
created by this batch, whose no-concern disposition is recorded. Every other note, revision,
author, concern and head must remain unchanged. Never relax the whole fingerprint to accommodate
our reply. Require a verified fix or authenticated bot false positive and disposition of every
concern from every author. Human disagreement alone cannot resolve a discussion. Read-back with changed context remains visibly unsettled; ordinary recovery cannot discard the
context mismatch. Never re-resolve or reopen automatically.

A possibly delivered send requires exact marker/body/actor/context reconciliation. Missing
read-back is not proof of non-delivery and cannot authorize a blind retry. Park ambiguity locally
for inspection. An entirely failed round or failed terminal consumer operation uses the configured interval before
retrying, without an error-cause/quota classifier. Unknown public effects require explicit read-back
recovery. Reconnect to still-running work; an unavailable reviewer is recorded as a failure only
when no input was issued or its native execution is proven terminal.

## Instructions and scheduling

One concise common instruction producer initializes newly created chats. Preserve original chat
IDs and source bytes when later rounds require fresh chats. Do not update loaded historical chats or depend on
runtime instruction replacement. Verify creation and cold-resume model input with the installed
binary and a local fixture provider. Saved settings alone do not prove instruction inclusion.
No production model turns or artificial public writes are validation evidence.

The existing systemd service runs the continuous consumer with process-failure restart. The
worker owns next_inventory_due from current TOML cadence/window; the 15-minute timer only wakes a
stopped service. Running work and recovery may finish outside the inventory window. Exactly one
bounded inventory helper owns the shared budget and its own SQLite connection, outside the
operator lock. Its results pass fresh admission checks. Slow inventory cannot block native
terminal observation, batch settlement or next-job progression. Idle coordination uses no model.

Current configuration removal denies new observation, enqueue, reservation, operation intent and
native start, including from stale cached config. Already-issued sends retain bounded receipt/
settlement access without new sends. Removal cannot erase human sources, holds or public IDs.

## Transition and traceability

Stage source before cutover. Use a separate fresh queue database; never import or modify the
predecessor database or its chat mappings. Stop its scheduled producer at cutover and verify old
native execution is terminal before starting conflicting work. Existing public GitLab discussions
remain authoritative input to the new review. The first inventory queues one review of the current
head of every open MR; it does not claim any previous reviewed checkpoint. Do not replay historical source messages as new
human authorization. Accept single-repository and list config through one normalized reader,
without a preliminary configuration migration. New Codex chats are created lazily per MR using
the configured Codex project, with fresh chats when folders or shared instructions change.
Remove superseded queue producers and their implementation-specific
tests after replacement protections pass. Never edit native databases or runtime history directly.

| Invariant | Owner | Required evidence |
| --- | --- | --- |
| Durable FIFO and capacity | Jobs, consumer, locks | Competing processes, restart, immediate progression |
| Exact native/result identity | Result collector and dispatch journal | Stale A vs B, altered input/result, no mutating legacy calls |
| Human scope and holds | Native intake and result admission | ?/w/mixed denials, sufficient answer, interrupted intake/question |
| Safe effects and progress | Batch application and publication journal | Partial batch, lost read-back, reply+resolve races, honest checkpoint |
| Scheduling and removal | Worker inventory and current config gates | Successive due inventories, slow inventory vs completion, removal after send |
| Fresh start and instructions | Fresh state, new-chat producer and cutover | Old state/chats untouched, no legacy intake, native creation/cold resume |
| Shared editable workspace | Round snapshot and native launch policy | Same roots across reviewers/restart, linked Git metadata, read-only intake, original-chat answers |

The standalone CLI owns `MonitorQueue`, the ordered worker and one shared instruction producer.

`mq_workspace` owns round snapshots; `mq_permission_profile` and `mq_claude_arguments` supply
native execution policies. `mq_codex_context` retains original source contexts. Workspace adapter
and installed-client probes are in `scripts/tests/test_codex_gitlab_workspace.py` and
`scripts/tests/test_codex_gitlab_workspace_native.py`, covering shared roots, restart, linked
metadata, actual editing/command behavior, read-only intake and original-chat hold answers.
The default fresh store is `~/.local/state/codex-session-stats-queue/queue.sqlite3`, outside the
predecessor writable directory and native state. Private immutable inputs are adjacent to it.
`scripts/tests/test_codex_gitlab_queue.py` exercises real SQLite/worker/CLI/locks with fixture native
transports and local HTTP. The relay suite retains process/Unix peer/cancellation protection;
project tests cover normalized list identity and removal. Installed native-binary local-provider
probes established fresh Codex creation/cold-resume instructions and Claude background source/final
identity.
Fixtures do not prove production model quality or Desktop rendering. Subscription/account/project
preflight is read-only. Public effects and production model turns were excluded from validation.
Explicit inspection/recovery remains for delivery ambiguity.
