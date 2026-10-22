# GitLab monitor simple queue

**Status:** Implemented. Supersedes [work ownership](gitlab-monitor-work-ownership.md).
The fresh consumer is installed; predecessor state and chats remain untouched and outside its intake.

## Decision and scope

### Direct GitLab publication ownership

The operator selected direct use of the existing ordinary GitLab HTTP MCP for newly prepared
review stages. This amendment supersedes private `gitlab_review` publication ownership for new stages;
the older operation contract remains only for original issued evidence and
read-back recovery. The FIFO, native identities, sufficient-answer holds, reviewer order and
actual code checkpoints remain unchanged. Historical input formats retain their exact readers.

New native clients publish findings, replies and explained resolutions themselves. The monitor
does not authorize individual sends, generate body markers, journal intentions or confirm receipts
for these stages. Per-launch permissions expose reads and the three review writes; intake exposes
reads only. Both reviewers read complete current discussions, including their peer's findings,
and preserve unresolved concerns. Current head/open-state checks and whole-discussion judgment
at publication are agent responsibilities, not equivalent deterministic monitor gates.

Exact native terminal finals supply a readable completion/question status. Only an actual completed
review of the admitted code head contributes its checkpoint. Automatic questions receive a saved
authenticated discussion snapshot before their anchored hold is established; snapshot failure
blocks that MR until recovery without occupying capacity after proven termination. Human scope
never expands from that snapshot.

Passive collection of authenticated ordinary native tool results records self-created note
revisions and proven resolution deltas solely for inventory filtering. Normalize raw before/after
observations against the same evidence. Retire only never-issued automatic discussion events
proved entirely self-generated, retaining their original admissions. The installed service returns text-only resolution success, so those unproved deltas stay
eligible for an extra ordinary pass. Unknown output stays eligible;
same-account human activity must not be ignored. This is not a durable send journal or an
exactly-once guarantee. Existing uncertain historical effects remain read-back-only fences.

Retire proven-unissued old preparations transactionally outside executed attempts. Preserve
successes, selective-retry bounds, original source lookup, questions and original collectors for
issued terminal results. Never relaunch ambiguous delivery. New stages use fresh instructions and
the normal shared service's initial `core,merge_requests` catalog, without rewriting old chats.

The monitor owns one durable FIFO and one supervised consumer. Admitted reviewers receive the
MR link and frozen workspace, obtain context on demand, investigate and publish during native
execution through the ordinary GitLab MCP. The monitor owns admission and native execution
recovery; new direct publications belong to the native reviewers, while old journals retain read-back; it does not judge semantic duplicates or choose between
reviewers. No final JSON review report or all-reviewer publication barrier is required.

Preserve repository identity, human requests and holds admitted by this consumer, actual reviewed
progress and publication provenance. The original fresh-queue cutover left predecessor state and
chats untouched. Subsequent tool adoption retains this consumer's queue and original sources.
New chats receive current instructions; never rewrite loaded historical instructions. Codex and Claude use the existing shared HTTP GitLab service and its initial `core,merge_requests`
catalog, with per-launch review tool permissions and the same validated credential source.

**Workspace execution amendment:** Reviewers may execute commands, edit files, change
branches and run tests in the configured workspace folders and their necessary shared Git
metadata, without per-command approval. The monitor supplies the same durable workspace snapshot
to every reviewer in a round; the model chooses the repository, checkout and commands. Refresh
the named Codex project's folders only for a new round. Preserve original chat contexts and human
sources across fresh-chat creation when folders or shared instructions change. Consumer intake
remains read-only; direct manual app turns follow
the shared semantic instructions and are outside the consumer's launch serialization. Reviewers
do not receive the consumer's native control socket or state-write capability. Global defaults,
queue capacity and native-source protections remain unchanged; direct publication has the
explicit limits in the amendment above.

Persist canonical ordered roots, primary directory, native project identity and actual Git
metadata paths before the first launch/input. A restart or later reviewer uses that same snapshot.
An archived round retains its original snapshot; only its successor resolves the live project
again. A same-name replacement project does not inherit authorization. Historical saved folder
lists do not prevent reading the current live list or authenticate a source against changed roots.

Codex selects a distinct thread-local permissions profile at creation, resume and turn start;
resume explicitly supplies the round's roots. Claude receives the same primary/additional
directories, scoped native Edit/Write rules and command sandbox settings without inherited hooks
or unrelated writable directories. Preserve intended model/effort and subscription credentials.
No unsandboxed retry is enabled. The complete saved request is sent directly to the native chat
without adding the queue directory as a writable workspace. Necessary linked-worktree Git metadata may be outside the
configured roots; this exception does not include the main checkout's source directory.

Register original contexts for every Codex session created by this consumer, retaining older
sessions after chat rotation. Source authentication uses that original
context. A cold native read may omit live environments: only an exact notLoaded/null response
uses the protected native rollout's authenticated session metadata and latest persisted turn
context. The native home must remain private/owned; native rollout file modes are preserved,
with bounded no-symlink reads of an owned regular file. Missing latest turn context is rejected. Changed or malformed latest context never falls back to older matching roots. Loaded
ambiguous context remains rejected; verification never resumes the chat for inspection.
This registry neither adopts predecessor sessions nor updates loaded instructions.
Claude retains its existing native session history. One consumer owns scheduling; native reviewers
own new direct public effects.

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

Newly prepared stages persist the complete readable task message and its frozen
context together in the existing queue stage before dispatch. Send that message directly to each
native client; do not require the reviewer to read a separate input file. Keep execution identity
and exact native-input authentication. Already prepared or issued historical inputs retain their
original bytes and original validation. Archive prior-round operational diagnostics with their
round instead of presenting them as current work or human-decision requirements. Input validation,
question-continuation authentication and interrupted delivery must use the same saved context.
Claude's finite service receives the saved message through verified UTF-8 standard input, with
versioned compatibility for already prepared argv executions. A transport artifact is not another
input authority. Proven failure before process execution cannot become unknown native capacity.

New stages use ordinary GitLab read tools and only the three review writes: create a discussion,
reply in a discussion and resolve a discussion. Intake has read tools only. The native tool server
performs these operations directly; no monitor MCP or completion callback is launched.

Only the exact native terminal final supplies the readable review status. Require one unquoted,
unfenced `Estado da revisão: concluída`, `Estado da revisão: aguardando resposta` or
`Estado da revisão: não concluída`. A completed code review includes `Commit revisado:` with its
actual full SHA. A question follows its status in readable text. Incomplete or ambiguous output
is a failed reviewer, never completed coverage. Native termination and input/final identity remain
mandatory independently of that status. Intake keeps its original compact assessment.

For a new automatic question, persist an authenticated current discussion snapshot with the final
before establishing its anchored hold. A failed scope read leaves that exact question pending and
blocks the MR; proven termination lets other MRs proceed. Preserve an existing human grant instead
of enlarging it from the snapshot. Recover this handoff before another reviewer or human intake.

Historical uncertain public delivery fences that MR. After exact native termination, subsequent
cycles perform read-back only, retaining remaining reviewers and checkpoints. New direct uncertain
sends are read back by the model before retry; the monitor has no send journal for them.

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

Both reviewers read actual current full discussions and earlier readable summaries. Each can
publish findings, supplement a concern or explain and resolve an evidenced correction. Different
defects on the same line remain separate. Semantic duplication and remaining-concern judgment
belong to the model. A terminal failure cannot undo an already published comment. Direct retries
read GitLab; they do not reuse a monitor receipt or promise exactly-once delivery.

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

An explicit local operator request through `restart-review JOB --stage STAGE --reason TEXT` may discard one exactly selected pending round
and return that same admitted work to the FIFO tail for a fresh complete review and new chats.
Revalidate job/stage/epoch, original native input/question, exact termination, repository/open MR,
admitted head, current native-answer frontier, absence of pending answers and settled public
effects. Archive the old round, diagnostic, held question and operator reason distinctly from
sufficient answers. Preserve original admission/source, original contexts, public identities and
actual code checkpoint. Reset active stages/attempt/workspace; every configured reviewer runs in
the replacement round. This explicit full restart is separate from failed-reviewer selective retry.
Repetition cannot repeat the transition; no fake automatic event or human answer is created.
Changed context or uncertainty rejects without dispatch. Genuine holds outside the selected round
remain authoritative; models cannot request this administration through their review tools.

Native intake is not atomic with operator retirement. Recheck the source frontier before commit
and preserve its identity in retirement history. A late answer to that exact retired question is
handled read-only with its original scope and source; it cannot become unrelated mutable work or
an answer to another hold. Unrelated explicit new actions in original chats remain admissible.

## Publications and passive observation

Native clients use normal GitLab arguments. Shared instructions require checking the current
open MR, refs and complete discussion immediately before mutation, explaining fixes/invalid
concerns before resolving, and keeping any remaining concern or unanswered follow-up open.
These are model responsibilities: direct tools no longer enforce the private helper's per-call
head, scope, whole-discussion fingerprint or closed-MR gates. Admission still checks repository,
human source/scope and current open state. Do not describe instructions as those removed guarantees.

Missing diff bodies do not block admission. The model chooses local Git and verifies exact
base/start/head objects, without monitor checkout mappings or a per-file publication proxy.

The collector passively authenticates ordinary GitLab calls/results against original native input,
server, repository/MR and stage. Persist self-created note revisions and proven resolution deltas
with an idempotent cursor, not send intentions or body markers. Inventory stores minimal raw
before/after revisions and normalizes both against the same proven outputs. Observe before inventory
and subsequent dispatch. Late evidence may retire only never-issued automatic discussion work
whose every contributing delta is self-only, preserving admissions and FIFO lineage. External edits,
same-account human activity, unknown revisions and missing results remain eligible. Observation
cannot resend or authorize a write and does not guarantee duplicate-free convergence.

Historical confirmed receipts still filter their original notes, and uncertain old effects retain
read-back-only reconciliation. No direct result replays an old public action.

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
change how older compact human assessments or frozen input formats are authenticated and read.

The same saved native message and frozen context govern dispatch, native identity, question
continuation and recovery; historical inputs remain on their original reader. Explicit operator
restart adds a selected round-discard transition and late-answer handling without changing native
human-action admission.

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
bounded cycle rather than continuous polling. Queue identity, holds and reviewed checkpoints remain unchanged. Scheduling updates retain the current queue and chat sources;
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

The direct-route update pauses scheduling until implementation, validation, selected reviews and
local commits finish. Prove issued native executions terminal before editing their runtime.
Retain original `message-v1` and older file validators and finish/question intent readers for
issued results. New inputs use `message-v2` and fresh instructions. Transactionally archive only
proven-unissued old preparations outside executed attempts, preserving original lookup, successful
stages and selective retry bounds. Unknown delivery is reconciled exactly, never relaunched.
Existing holds and confirmed/uncertain journals remain authoritative. No old chat is rewritten.

| Invariant | Owner | Required evidence |
| --- | --- | --- |
| Durable FIFO and capacity | Jobs, consumer, locks | Competing processes, restart, immediate progression |
| Automatic event grouping | `MonitorQueue` enqueue/reserve coalescing and original admissions | `test_codex_gitlab_coalescing.py`: FIFO, frozen work, barriers, repeat/restart, concurrent transactions; sanitized pending-event artifact replay |
| Operation recovery | Native collectors, cold context normalization, consumer retry/status | `test_codex_gitlab_recovery.py`: sanitized native artifacts, retry/restart without relaunch, two-failure tick progress, prepared/confirmed effects, source/context denials and CLI resume commands |
| Selective reviewer retry | `MonitorQueue` attempt bounds, transactional tail move and worker settlement | `test_codex_gitlab_retries.py`: both orders, interval/FIFO/restart, partial-success backfill, native questions, reset interruption, old-call denial, receipt reuse and checkpoint guards |
| Finite Claude execution | Transient service, receipt and stream collector | `test_codex_gitlab_print.py` and installed-client fixtures: native identities, split finals, lost acknowledgment, live descendants, timeout and resume |
| Exact native/result identity | Original native source, versioned input and terminal result collector | `test_codex_gitlab_direct_native.py`: installed clients, real HTTP MCP and local model fixtures, scoped positive/negative permissions and exact output provenance |
| Human scope and holds | Native intake and result admission | ?/w/mixed denials, sufficient answer, interrupted intake/question |
| Direct publications and observation | Native GitLab tools, passive collector and raw inventory deltas | `test_codex_gitlab_direct.py`: self-output race, human edits, version/hold/transition boundaries and honest checkpoints; legacy recovery tests retain original journals |
| Scheduling and removal | Bounded tick, worker inventory and current config gates | Successive cycles, native oneshot lifetime/restart, slow HTTP/history vs sufficient answers, removal after send |
| Fresh start and instructions | Fresh state, new-chat producer and cutover | Old state/chats untouched, no legacy intake, native creation/cold resume |
| Visible native requests  | Existing stage input, native dispatch, input validation and question continuation | Exact message/context, historical reader, large Claude stdin, pre-exec failure and native creation/cold-resume checks |
| Explicit full-round restart  | Operator control, original native question, existing queue and intake | Native-answer frontier/races, late replies, exact target, fresh complete review/chat, FIFO/history/effect preservation and rejection controls |
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
