# GitLab monitor simple queue

**Status:** Implemented. Supersedes [work ownership](gitlab-monitor-work-ownership.md).
The fresh consumer is installed; predecessor state and chats remain untouched and outside its intake.

## Decision and scope

The monitor owns one durable FIFO and one supervised consumer. Admitted reviewers receive the
MR link and frozen workspace, obtain context on demand, investigate and publish during native
execution through scoped tools. The monitor owns admission, public-operation journaling,
authenticated read-back and recovery; it does not judge semantic duplicates or choose between
reviewers. No final JSON review report or all-reviewer publication barrier is required.

Preserve repository identity, human requests and holds admitted by this consumer, actual reviewed
progress and publication provenance. The original fresh-queue cutover left predecessor state and
chats untouched. Subsequent tool adoption retains this consumer's queue and original sources.
New chats receive current instructions; never rewrite loaded historical instructions. The optional
official MCP SDK supplies a client-launched stdio transport, not another queue, scanning service or
credential route. Codex and Claude use the same round-bound tools with per-launch approvals.

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
context. A cold native read may omit live environments: only an exact notLoaded/null response
uses the protected native rollout's authenticated session metadata and latest persisted turn
context. The native home must remain private/owned; native rollout file modes are preserved,
with bounded no-symlink reads of an owned regular file. Missing latest turn context is rejected. Changed or malformed latest context never falls back to older matching roots. Loaded
ambiguous context remains rejected; verification never resumes the chat for inspection.
This registry neither adopts predecessor sessions nor updates loaded instructions.
Claude retains its existing native session history. One consumer still owns all public effects.

## One queue and one consumer

Jobs have three states: pending, running and completed, ordered by one global sequence across
all repositories. Pending jobs can carry a wait reason and retry time. Settle superseded unsent code revisions without model work; preserve independent human requests and scope. Commits arriving during work
remain pending. One dedicated singleton process lock protects the consumer. The consumer lock also excludes operator recovery/cutover; short SQLite transactions protect state
boundaries, while inventory HTTP runs outside SQLite transactions within the bounded cycle. Producers enqueue
transactionally and cannot interrupt the consumer. There is no competing reservation machine.
Selective reviewer retries move the same job's scheduling sequence to the tail, retaining its
original sequence and immutable admission/source. New arrivals follow that position. Repeated
requeue is transactional and idempotent; a pending retry is not enqueued again.

Unstarted automatic code/discussion events for the same authenticated repository and MR share
one pending representative at the oldest FIFO position, targeting the latest admitted head and
current discussions. Preserve every original source/key and admission kind/head. Retain absorbed
event records with an explicit administrative outcome and link to their representative; this is
neither completed review nor publication. Repeated original admission remains idempotent.

Enqueue and reservation coalesce in one write transaction. Flatten all contributing admissions
when selecting the target; only an actual code event for that head can authorize a code checkpoint
after completed review. A discussion at another head cannot fabricate code provenance. Models
receive one current review context and a real contributing source, without notification history.
Unfinished human/noneligible work and incompatible reviewer policies divide chronological segments
of outstanding same-MR work; completed historical requests are retained outside those segments.
Prior execution/history, results, waits, effects and held jobs cannot be absorbed. Reservation
freezes membership durably; later arrivals form subsequent work even if the current round retries.
Existing pending events are consolidated through normal consumer controls, without migration.

Each job binds authenticated repository ID, MR IID, mapped chat, immutable source, requested work,
internal epoch and exact native execution attempt. Persist exact automatic input before native
start and prove its acknowledgment or reconcile that exact delivery. Acceptance is not review.
Unknown native execution retains the running slot; elapsed time is not evidence of termination.

Reviewers use task-sized read, finding, reply and resolve operations. The helper derives job,
stage, epoch, source and public-operation identities; models supply only domain arguments.
Authenticate each call through the native client's private MCP metadata, exact registered native
input and current running stage. Codex checks session/turn/user input; Claude checks exact tool
call arguments, original-input ancestry and live service invocation. A copied identifier alone
never grants authority. Former agent administration commands remain rejected.

A short work lock serializes consumer transitions and tool calls without holding SQLite writes
across network operations. The cycle lock remains separate, so native tools can run after the
periodic consumer exits. A busy helper returns a retry indication before any send.

Finish and ask-human signals are provisional. Finish requires a compatible successful native
final and no uncertainty or question before it contributes actual reviewed coverage. An
interrupted or timed-out finish cannot advance a checkpoint. Ask-human fences mutable calls
immediately; only its readable native final establishes the anchored hold. Persist an interrupted
question for a read-only presentation after exact native termination. Recover intent/result/hold
handoffs before another reviewer or protocol cutover. Never invent an anchor or sufficient answer.

Unknown public delivery fences that MR while active native execution retains global capacity.
After exact termination, park the job without completing it; other MRs may proceed. Subsequent
cycles and explicit recovery perform read-back only. Confirmation resumes the remaining reviewer
sequence without replaying completed stages. Only completed actual code-event review advances a
code checkpoint; human and discussion work cannot fabricate one.

## Ordered reviewer stages

An admitted job snapshots its ordered nonempty unique list of enabled reviewers. Every configured
reviewer runs in the first attempt in that order, including after an earlier success or failure. One reviewer is
valid. There is no fallback mode, quota classifier or success-based skipping. Record each result
or failure honestly and continue to the next reviewer after the preceding execution is terminal.
A failed stage never contributes reviewed coverage. At least one complete valid review of the
exact target head is required before advancing a code checkpoint. Publication during an active
review does not depend on that reviewer or a later reviewer ultimately succeeding.

After all reviewers in an attempt terminate, only reviewers whose latest review failed return to
the tail of the same FIFO, eligible after the configured interval. Successful reviewers are not
rerun. A subsequent failed attempt follows the same rule. Keep the same job, exact head, frozen
workspace, all stage IDs/results and public-operation identities. Each attempt records its reviewer
subset and stage boundary. A sufficient-answer or protocol full reset clears those attempt bounds
together with the stages; selective retry never performs that reset.

Authentication, network, credits, invalid output and other terminal failures all follow the same
continuation rule. Preserve partial evidence and confirmed receipts, but do not call a failed
stage a successful review. A failed review remains pending for a later attempt with a visible
reason, even if another reviewer succeeded. Unknown execution is still running rather than a proven failure: reconcile or
interrupt that exact execution and prove termination before starting another, preserving serial
capacity. Human questions retain their sufficient-answer hold; they are not authorization to
publish. Reviewer stages are fields of one job, not another queue or capacity authority.

The consumer also re-admits its previously completed partial-success review jobs once through this
same transition. Administrative, explanation, superseded and closed outcomes do not reopen.
Retain existing checkpoints and completion history. A valid successful review can advance the
normal code checkpoint before requeue; interrupted settlement is recovered through the same
completed-job check. Revalidate repository admission, native human scope, current head and open
state before launching the retry. Original human holds and uncertain sends remain authoritative.

New Claude stages use a finite signed-in CLI process in print stream-JSON mode, owned by a
transient user systemd service. Preserve native session history and an explicit session UUID for
later CLI resume; no Remote Control, browser accompaniment or idle-chat supervisor is required.
The monitor persists launch identity and immutable input before issuing the service. An atomic
service receipt binds the invocation and captured output; terminal unit evidence and an empty
exact execution cgroup, including descendants, establish termination. Receipt appearance alone
cannot release capacity. Retained receipt/cgroup evidence survives successful-unit collection;
unit absence alone never proves non-launch or completion. Reconcile lost acknowledgments without
issuing another execution. A reboot proves interruption of unfinished execution, preserving a
previously recorded valid result. Failure and timeout continue the configured reviewer sequence.

The official output stream identifies the final main message and all its split blocks by native
UUID. Authenticate the original native input and those exact blocks during completion/question collection;
the terminal envelope's text identifies its trailing text block, not the complete split response.
Later human turns cannot replace the captured final. Results and readable questions remain in
native history and monitor status, which supplies a command to resume the original CLI context.
Desktop import is not part of this contract. Historical Codex chats remain outside the consumer.

Already issued background stages retain their original collection/cancellation and result
revalidation until settled; new launches cannot select that transport. Human intake retains the
shared native ancestry collector: only tool results with matching ancestral call identities can
continue an input, human/mixed input cuts that ancestry, and split final blocks belong to one
completed native message. Register fresh Claude executions when needed, preserving original
source/question identities and sufficient-answer routing. Do not edit or migrate native history,
or run an extra Codex model solely for presentation.
When the monitor configuration omits `claude_model`, use `claude-opus-5-5`; an explicit value
takes precedence. Omitted effort retains Claude's own effort settings. No new credential route.

## Publication during ordered reviews

Each reviewer reads actual current discussions and earlier readable summaries. It can publish
findings, supplement a concern or resolve an evidenced fix while reviewing. Confirmed effects
survive later failure. Repetition of an identical operation reuses its receipt; different defects
on one line remain separate. Semantic duplication and disagreement are model judgments over
actual discussions, not line grouping or mandatory concern/disposition inventories.

Every configured reviewer must reach proven termination before job completion, except that a
human question or uncertain effect preserves its hold before the next mutable stage. A successful
first stage never skips the second. Failed reviewers wait for a selective retry; no failed
stage contributes coverage. The monitor neither regenerates a final consolidated batch nor
publishes historical saved proposals on behalf of a new round.

## Human input and questions

Observe actual native human turns in mapped MR chats. Authenticate exact source text and its
terminal assessment; do not infer source from the latest runtime turn. A compact fenced
`csm-assessment` classifies action, sufficient answer or explanation, with bounded effects and
actual discussion IDs. The reader binds the exact original text internally, rather than asking
the model to reproduce administrative identity or a complete proposed publication batch.
An explicit post-completion action enters the same FIFO as new human work. Read-only intake can
recover a missing assessment; its automatic continuation is never itself human authorization.
Before mutable dispatch, preserve the original source, assessment and scope. The old assessment
reader remains available only for original historical sources. Human work never becomes an
automatic code event or a new permission grant.

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

GitLab authenticates repository/MR identity, current refs and changed-file metadata. Missing diff
bodies remain visible and do not block admission. The reviewer chooses a checkout and investigates
exact objects. For inline validation, the helper can read only the selected file from existing
Git objects at the authenticated base/start/head within frozen workspace roots. It does not fetch,
change refs/index/branches or maintain checkout mappings. Disable external diff/textconv and
validate exact paths, commit objects and patch coordinates. Missing or unprovable objects reject
that inline operation; never substitute working-tree content. This on-demand rule replaces the
previous pending proposal to acquire every complete diff before dispatch.

Resolve is a compound domain operation: first explain, confirm the exact explanation, then
revalidate and resolve. The comparison may account only for that exact confirmed explanation
created by this operation, whose no-concern disposition is recorded. Every other note, revision,
author, concern and head must remain unchanged. Never relax the whole fingerprint to accommodate
our reply. Require a verified fix or authenticated bot false positive and disposition of every
concern from every author. Human disagreement alone cannot resolve a discussion. Read-back with changed context remains visibly unsettled; ordinary recovery cannot discard the
context mismatch. Never re-resolve or reopen automatically.

A possibly delivered send requires exact marker/body/actor/context reconciliation. Missing
read-back is not proof of non-delivery and cannot authorize a blind retry. Park ambiguity for read-back without discarding it. Selective reviewer retries and failed terminal
consumer operations use the configured interval before retrying, without a quota classifier.
Retries preserve completed stages, immutable inputs, workspace and confirmed receipts. Proven
unsent prepared effects may be cancelled with a reason; they never become fabricated receipts.
Possibly issued effects prevent reset until reconciled. Parking terminal work counts as progress,
so persistent failures cannot starve other MRs. A native reviewer is failed only when no input was
issued or exact termination is proven.

## Instructions and scheduling

One concise common instruction producer initializes newly created chats. Preserve original chat
IDs and source bytes when later rounds require fresh chats. Do not update loaded historical chats or depend on
runtime instruction replacement. Verify creation and cold-resume model input with the installed
binary and a local fixture provider. Saved settings alone do not prove instruction inclusion.
No production model turns or artificial public writes are validation evidence.

For monitor-dispatched stages the configured model and effort, including intentionally inherited
client settings, are already the operator's sufficient selection. Shared instructions and exact
stage input carry this delegation; native launch uses that stage's selection. Do not introduce
model-choice holds before admitted work. Existing native holds still require their real sufficient
answers; manual chats and domain-question policy are unchanged. New instruction versions must not
change how older compact human assessments are authenticated and read.

Each 15-minute systemd trigger runs one bounded queue cycle and exits, using a oneshot service
without automatic restart or a resident scan helper. The current TOML cadence/window governs
automatic inventory. A singleton cycle lock and durable running job preserve serial capacity between
processes. Ready native reconciliation, timeout handling, reviewer progression and effect reconciliation
precede bounded inventory; persisted intake continuation prevents starvation of later sources.
This continuation includes sessions, native sources and history pages within the same MR.
Alternate recent-page refresh with historical continuation and retain the exact native
question/answer order proof across cycles. HTTP has a wall-clock deadline for the entire operation,
backed by a finite unit timeout.
Normal budget exhaustion saves progress without recording reviewer failure or discarding confirmed effects.
Native reviewers outlive the bounded cycle. Claude print services independently own their
execution and runtime limit; the monitor unit retains its process-only stop policy for existing
issued reviewers. Deadline expiry alone never proves termination. Completion and human-answer observation occur on subsequent triggers,
including outside inventory hours. Immediate progression means within a ready
bounded cycle rather than continuous polling. Queue identity, holds, publication ownership and
reviewed checkpoints remain unchanged. Scheduling updates retain the current queue and chat sources;
they do not repeat the predecessor-to-fresh-consumer transition. Idle coordination uses no model.

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

The tool-route update pauses scheduling while replacing installed source. Collect already-issued
legacy native executions through their original reader; never issue another legacy report input.
Archive saved proposals as history and cancel proven-unsent prepared effects through consumer
controls. Preserve existing holds and confirmed/uncertain journals; reconcile uncertainty before
cutover. New work uses fresh instructions without moving, migrating or rewriting old chats.

| Invariant | Owner | Required evidence |
| --- | --- | --- |
| Durable FIFO and capacity | Jobs, consumer, locks | Competing processes, restart, immediate progression |
| Automatic event grouping | `MonitorQueue` enqueue/reserve coalescing and original admissions | `test_codex_gitlab_coalescing.py`: FIFO, frozen work, barriers, repeat/restart, concurrent transactions; sanitized pending-event artifact replay |
| Operation recovery | Native collectors, cold context normalization, consumer retry/status | `test_codex_gitlab_recovery.py`: sanitized native artifacts, retry/restart without relaunch, two-failure tick progress, prepared/confirmed effects, source/context denials and CLI resume commands |
| Selective reviewer retry | `MonitorQueue` attempt bounds, transactional tail move and worker settlement | `test_codex_gitlab_retries.py`: both orders, interval/FIFO/restart, partial-success backfill, native questions, reset interruption, old-call denial, receipt reuse and checkpoint guards |
| Finite Claude execution | Transient service, receipt and stream collector | `test_codex_gitlab_print.py` and installed-client fixtures: native identities, split finals, lost acknowledgment, live descendants, timeout and resume |
| Exact native/result identity | Scoped MCP authentication, result collector and dispatch journal | `test_codex_gitlab_tools_native.py`: installed clients, real SDK/stdio, local model/GitLab fixtures, first-turn connection, no real inference/publication |
| Human scope and holds | Native intake and result admission | ?/w/mixed denials, sufficient answer, interrupted intake/question |
| Safe effects and progress | Scoped tools and publication journal | `test_codex_gitlab_tools.py`: live publication, immutable receipts, source/context denials, partial sends, whole-discussion resolution, honest checkpoint |
| Scheduling and removal | Bounded tick, worker inventory and current config gates | Successive cycles, native oneshot lifetime/restart, slow HTTP/history vs sufficient answers, removal after send |
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
transports and local HTTP. `scripts/tests/test_codex_gitlab_coalescing.py` also consumes a sanitized
captured automatic-event sequence through enqueue/reservation; this is a partial artifact replay, not a recorded native
session or end-to-end replay.
The relay suite retains process/Unix peer/cancellation protection;
project tests cover normalized list identity and removal. Installed native-binary local-provider
probes established fresh Codex creation/cold-resume instructions and Claude background source/final
identity.
Fixtures do not prove production model quality or Desktop rendering. Subscription/account/project
preflight is read-only. Public effects and production model turns were excluded from validation.
Explicit inspection/recovery remains for delivery ambiguity.
