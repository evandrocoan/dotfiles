# GitLab monitor simple queue

**Status:** Implemented. Supersedes [work ownership](gitlab-monitor-work-ownership.md).
The fresh consumer is installed; predecessor state and chats remain untouched and outside its intake.

## Decision and scope

### Per-group history rotation

`history_limit` defaults to 2,000 and applies independently to each durable queue-history group
(`jobs`, `effects`, `mrs`, `metadata`, and compact `retired_jobs` markers). It is a row-count limit,
not one combined total or a byte limit. Lowering it takes effect on the next successful tick.

Ticks remove the oldest eligible rows after the evidence needed for that group is available. A group
may exceed its limit while rows protect active work, retry/output obligations, human holds, unread
notices, unsettled effects, checkpoints, source/session provenance, inventory comparison, or operator
receipts. Completed job details are replaced with non-executable identity markers in the same SQLite
transaction. A retained native session keeps its markers needed to distinguish agent-authored
messages; expiring that old session removes it from monitor intake and answer recognition. This
changes monitor handling only; ordinary manual GitLab MCP use in that chat remains available.

Settled finding/reply receipts remain while their matching comments are present in the latest
successful discussion read; resolution identities stay with the MR inventory baseline. An
operator-restart receipt also retains referenced effects and prevents retirement of its MR group.
A closed MR does not by itself retire this identity: it may reopen. When the MR group needs
trimming, its full baseline, terminal jobs, settled effects and markers can be removed together
only after a current identity-validated closed/merged response, or after its project is removed
from configuration, and no remaining work, receipt, output or question dependencies. Failed or
unknown state reads keep a configured project's record. Reopened or rediscovered MRs after full
retirement start as fresh admissions.

Metadata rotation discards only explicitly recognized diagnostics; unknown keys remain protected.
Active cursors, proofs and identities remain. The
limit does not cap large values or nested history inside a row and does not shrink the SQLite file
physically. It adds no parallel queue and does not change reviewer order or publication protocols.

### Direct GitLab publication ownership

The operator selected direct use of the existing ordinary GitLab HTTP MCP for newly prepared
review stages. This amendment supersedes private `gitlab_review` publication ownership for new stages;
the older operation contract remains only for original issued evidence and
read-back recovery. The FIFO, native identities, sufficient-answer holds, reviewer order and
actual code checkpoints remain unchanged. Historical input formats retain their exact readers. Freeze the actual dispatched instruction
policy independently of input format, including an old preparation sent unchanged in a fresh chat.

New native clients publish findings, replies and explained resolutions themselves. The monitor
does not authorize individual sends, generate body markers, journal intentions or confirm receipts
for these stages. Per-launch permissions expose reads and the three review writes; intake exposes
reads only for already admitted historical work; no new intake jobs are produced.
Both reviewers read complete current discussions, including their peer's findings,
and preserve unresolved concerns. Current head/open-state checks and whole-discussion judgment
at publication are agent responsibilities, not equivalent deterministic monitor gates.

Exact native terminal finals supply a readable completion/question status. Only an actual completed
review of the admitted code head contributes its checkpoint. Automatic questions receive a saved
authenticated discussion snapshot before their anchored hold is established; snapshot failure
blocks that MR until recovery without occupying capacity after proven termination. Human scope
never expands from that snapshot.

Passive collection of authenticated ordinary native tool results records self-created note revisions
and proven resolution deltas solely for inventory filtering. Normalize raw before/after observations
against the same evidence. Retire only never-issued automatic discussion events proved entirely
self-generated, retaining their original admissions. The installed service returns text-only
resolution success, so those unproved deltas stay eligible for an extra ordinary pass. Unknown
output stays eligible; same-account human activity must not be ignored. This is not a durable send
journal or an exactly-once guarantee. Normal recovery keeps uncertain historical effects as read-
back-only fences; explicit operator MR abandonment is the scoped exception defined below.

Retire proven-unissued old preparations transactionally outside executed attempts. Preserve
successes, selective-retry bounds, original source lookup, questions and original collectors for
issued terminal results. Never relaunch ambiguous delivery. New stages use fresh instructions and
the normal shared service's initial MR and CI-read catalog, without rewriting old chats.

The monitor owns one durable FIFO and one supervised consumer. Admitted reviewers receive the
MR link and frozen workspace, obtain context on demand, investigate and publish during native
execution through the ordinary GitLab MCP. The monitor owns admission and native execution
recovery; new direct publications belong to the native reviewers, while old journals retain read-back; it does not judge semantic duplicates or choose between
reviewers. No final JSON review report or all-reviewer publication barrier is required.

Preserve repository identity, independently admitted human requests, actual reviewed progress and
publication provenance. Automatic questions and holds remain authoritative unless explicitly retired
by the operator. The original fresh-queue cutover left predecessor state and chats untouched.
Subsequent tool adoption retains this consumer's queue and original sources. New chats receive
current instructions; never rewrite loaded historical instructions. Codex and Claude use the
existing shared HTTP GitLab service and its initial MR and CI-read catalog, with per-launch review
tool permissions and the same validated credential source. The shared Compose configuration
individually enables required CI readers; it does not activate pipeline mutations. Native clients
need these reads in the initial catalog, without relying on mid-turn discovery.

**Workspace execution amendment:** Reviewers may execute commands, edit files, change
branches and run tests in the configured workspace folders and their necessary shared Git
metadata, without per-command approval. The monitor supplies the same durable workspace snapshot
to every reviewer in a round; the model chooses the repository, checkout and commands. Refresh
the named Codex project's folders only for a new round. Preserve original chat contexts and human
sources across fresh-chat creation when folders or shared instructions change. Consumer intake
remains read-only; direct manual app turns follow the shared semantic instructions and are outside
the consumer's launch serialization. Mutable Codex reviews select the native full-access
profile with no command approval and direct networking. Mutable Claude reviews run Bash with the
operator's host access and no shell sandbox. These trusted processes can reach monitor/native
files and the control socket; Codex file tools also have full local access. Claude file tools
retain workspace rules, which do not constrain Bash. Workspace remains task scope rather than
an OS boundary. Queue and source validators remain application checks, not security guarantees
against these processes. Intake explicitly reselects its read-only sandbox, network proxy and
read-only MCP grants. Manual Codex continuations may inherit the latest native chat permissions;
there is no automatic post-turn restoration. Global defaults, queue capacity and native-source
validation remain unchanged; direct publication has the explicit limits in the amendment above.

Persist canonical ordered roots, primary directory, native project identity and actual Git
metadata paths before the first launch/input. A restart or later reviewer uses that same snapshot.
An archived round retains its original snapshot; only its successor resolves the live project
again. A same-name replacement project does not inherit authorization. Historical saved folder
lists do not prevent reading the current live list or authenticate a source against changed roots.

Codex selects and verifies the purpose-specific thread-local permissions profile at creation,
resume and turn start; resume explicitly supplies the round's roots. Claude receives the same
primary/additional directories and scoped native Edit/Write rules, without inherited hooks.
Review shells use the trusted host route; intake retains its fail-closed sandbox and does not
retry unsandboxed. Preserve intended model/effort and subscription credentials. Select the proven
SSH agent in the monitor unit and forward it through Codex's launch-local shell environment.
The complete saved request is sent directly to the native chat without adding the queue directory
to the workspace. Necessary linked-worktree Git metadata may be outside the configured roots;
that file-tool allowance does not include the main checkout's source directory. Mutable host
access is broader, as specified above, without changing source authentication or intake permissions.

Register original contexts for every Codex session created by this consumer, retaining older
sessions after chat rotation. Source authentication uses that original
context. A cold native read may omit live environments: only an exact notLoaded/null response
uses the native rollout's authenticated session metadata and latest persisted turn
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
Normal automatic coalescence cannot absorb prior execution/history, results, waits, effects or held
jobs. Explicit operator MR abandonment is a separate transition. Reservation
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
mandatory independently of that status. Already admitted historical intake keeps its explicit
initial compact assessment task; that contract never applies to later ordinary human messages.

For a new automatic question, persist an authenticated current discussion snapshot with the final
before establishing its anchored hold. A failed scope read leaves that exact question pending and
blocks the MR; proven termination lets other MRs proceed. Preserve an existing human grant instead
of enlarging it from the snapshot. Recover this handoff before another reviewer or human intake.

Historical uncertain public delivery fences that MR until read-back recovery or explicit operator
abandonment. After exact native termination, subsequent
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
same transition. Administrative, explanation, superseded and closed outcomes do not reopen. Retain
existing checkpoints and completion history. A valid successful review can advance the normal code
checkpoint before requeue; interrupted settlement is recovered through the same completed-job check.
Revalidate repository admission, native human scope, current head and open state before launching
the retry. Original human holds and uncertain sends remain authoritative outside explicit operator
abandonment.

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
revalidation until settled; new launches cannot select that transport. Historical answer intake retains the
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

Newly prepared review chats handle human followups as normal native conversations. The agent
interprets and executes the actual request there, without assessment JSON, classification calls
or admission of new human/intake jobs. Manual work is outside automatic FIFO serialization.
Question-only input, preferences, explanations and mixed/automatic input grant no new mutable
authority; native agents apply normal authorization and the applicable question-only rule.
Ordinary messages cannot advance code checkpoints. Their real GitLab inventory deltas remain
eligible for ordinary automatic work, including same-account human comments.

The monitor observes only outstanding automatic-review questions. A question has the original
stage/session, exact native final anchor, readable question and bounded scope. After proven
termination the job waits pending; later work for that MR is blocked while other MRs proceed.
Recover an interrupted question/result handoff before another reviewer. Partial output never
creates a question or consent.

For a new-chat held task, the native model judges whether the actual answer is sufficient and
continues that review in the same chat. Only actual continuation/completion of that held task
uses the readable review status. Unrelated replies require no queue signal. Native metadata
proves identity and order, not semantic sufficiency. Require the original native input/final,
unchanged original context, a real nonautomatic unmixed human source and its exact completed
final. Codex requires a completed turn; Claude requires parent ancestry through the held final
and a native completion marker bound to that final branch. A generic, malformed or interrupted
reply leaves the hold intact. Follow further questions in native causal order.

Append immutable native continuation observations under the original held stage, keeping its
captured question/final intact. One effective-stage accessor feeds settlement, failed-reviewer
selection, prior summaries/status and actual code credit. No extra counted stage, automatic
attempt or event is fabricated for manually executed work. A resumed operational failure releases
the answered domain hold, runs remaining reviewers and receives ordinary failure-only retry.
A real newer-head review settles the original work without credit for its admitted head.
Uncertain historical-publication fences remain independent of every answer. Only explicit operator
MR abandonment can retire such a fence without confirming delivery.

Loaded historical chats retain their original instructions and readers. Consume an already
produced original assessment only for its existing held question or already admitted work;
never launch a repair classifier or produce new post-completion human work. Select that reader
from the original held stage's frozen protocol/input, not its latest chat mapping. Missing
historical assessments remain visibly held until an actual sufficient native response or supported
operator recovery. Their sufficient-answer reset retains its original source/scope checks and
crash recovery. Earlier consumer sessions remain original question sources; predecessor chats
are not adopted. Native user-channel clients are trusted locally, not proof of physical typing.

An explicit local operator request through `restart-review JOB --stage STAGE --reason TEXT` may discard one exactly selected pending round
and return that same admitted work to the FIFO tail for a fresh complete review and new chats.
Revalidate job/stage/epoch, original native input/question, exact termination, repository/open MR,
admitted head, current native-answer frontier, absence of pending answers and settled public
effects. Archive the old round, diagnostic, held question and operator reason distinctly from
sufficient answers. Preserve original admission/source, original contexts, public identities and
actual code checkpoint. Reset active stages/attempt/workspace; every configured reviewer runs in
the replacement round. This explicit full restart is separate from failed-reviewer selective retry.
Repetition cannot repeat the transition; no fake automatic event or human answer is created.
Changed native/head context or unresolved active uncertainty rejects without dispatch. Genuine holds outside the selected round
remain authoritative; models cannot request this administration through their review tools.

Operator restart authenticates both the issued original final and the effective current native
question. For new native holds its answer frontier covers only that current question surface,
excluding accepted continuations and earlier manual context. Historical holds keep their original
frontier. Native answer observation is not atomic with operator retirement. Recheck the source frontier before commit
and preserve its identity in retirement history. A late answer to that exact retired question is
handled read-only with its original scope and source; it cannot become unrelated mutable work or
an answer to another hold. Retired chats produce no new monitor work.

### Explicit operator MR abandonment

`restart-mr JOB --reason TEXT` uses one original pending automatic job as the identity of an
operator request to abandon that MR's captured pending automatic code/discussion work. This is
separate from normal retry, read-back recovery and strict single-held-round restart. Those controls
cannot abandon effects themselves; their native-source, question, head and active-effect gates
remain unchanged. Effects explicitly retired here remain historical and no longer block new work.

Under the existing consumer/work locks, capture and revalidate the selected jobs, MR record and
effects. Reject independent human/intake/presentation work or pending human answers. Prove all
selected issued native executions terminal, including retained earlier rounds; a saved queue state
alone is not proof. Proven-unissued preparations need no execution. Verify original Codex context
and current idle/notLoaded chat state; original Claude execution evidence must prove termination.
Authenticate the configured repository and current open MR/head, and reject a changed head/open
state during preparation. This control does not classify answers or treat abandonment as consent
in an old chat. Unrelated running work remains untouched.

One SQLite transaction archives the captured active stages, attempts, diagnostics, workspaces,
questions, answers and scope, retaining original admissions and coalesced lineage. Keep native
sessions and contexts inspectable without rewriting their histories. Retired questions keep their
original anchors and scopes; late replies cannot revive them or release another question. Every
unsettled historical effect belonging to captured work receives an explicit administrative
abandonment with its prior state, identity and operator receipt. Unresolved public-effect delivery
remains unknown, never confirmed or resent. A shared settled-effect predicate recognizes only
abandonment backed by that durable receipt across settlement, retry, reset and recovery. Unsettled
effects outside captured work reject the operation.

Reuse one representative with a distinct operator receipt authorizing a full code review of the
authenticated current head. Preserve its immutable original admission, and retire other captured
jobs with an administrative outcome that gives no review credit. Remove stale active source-target,
coalescence, answer and scope assumptions; the operator authority supplies both native input context
and checkpoint provenance for the new round. Existing code checkpoints remain unchanged until a
new actual code review completes. Return exactly one representative to the FIFO tail, snapshot
current configured reviewers and create fresh chats. Resolve the live project's workspace once
at that round's first launch, through the existing shared snapshot owner.

Persist the authenticated inventory observation using the same note normalization as ordinary
inventory. The identical snapshot cannot create another event; real later commits/comments remain
eligible. A receipt keyed by the original job and exact reason makes repetition return the original
result without absorbing later arrivals, including after interruption or completion. A conflicting
reason rejects. Per-MR transaction rollback preserves all prior state. Status exposes the receipt,
representative, retired jobs, target head, reason and previous states of abandoned public effects.

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
read-back-only reconciliation unless explicitly abandoned by the operator control. No direct result
replays an old public action.

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
restart adds a selected round-discard transition and late-answer handling without changing normal
native human conversations.

Each 15-minute systemd trigger runs one bounded queue cycle and exits, using a oneshot service
without automatic restart or a resident scan helper. The current TOML cadence/window governs
automatic inventory. A singleton cycle lock and durable running job preserve serial capacity between
processes. Ready native reconciliation, timeout handling, reviewer progression and effect reconciliation
precede bounded inventory. Observe only held questions with a bounded share of each cycle.
New held Codex observations retain page and causal turn progress across cycles; earlier generic
replies cannot starve a later sufficient response. Historical answer readers retain their original
session/source/page progress and exact order proof; ordinary completed chats are not scanned. HTTP has a wall-clock deadline for the entire operation,
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
issued results. New inputs use `message-v3` and fresh instructions; `message-v2` retains its exact renderer. Transactionally archive only
proven-unissued old preparations outside executed attempts, preserving original lookup, successful
stages and selective retry bounds. Unknown native delivery is reconciled exactly, never relaunched.
Existing holds and confirmed/uncertain journals remain authoritative outside the explicit operator
abandonment transition. No old chat is rewritten.

| Invariant | Owner | Required evidence |
| --- | --- | --- |
| Durable FIFO and capacity | Jobs, consumer, locks | Competing processes, restart, immediate progression |
| Automatic event grouping | `MonitorQueue` enqueue/reserve coalescing and original admissions | `test_codex_gitlab_coalescing.py`: FIFO, frozen work, barriers, repeat/restart, concurrent transactions; sanitized pending-event artifact replay |
| Operation recovery | Native collectors, cold context normalization, consumer retry/status | `test_codex_gitlab_recovery.py`: sanitized native artifacts, retry/restart without relaunch, two-failure tick progress, prepared/confirmed effects, source/context denials and CLI resume commands |
| Selective reviewer retry | `MonitorQueue` attempt bounds, transactional tail move and worker settlement | `test_codex_gitlab_retries.py`: both orders, interval/FIFO/restart, partial-success backfill, native questions, reset interruption, old-call denial, receipt reuse and checkpoint guards |
| Finite Claude execution | Transient service, receipt and stream collector | `test_codex_gitlab_print.py` and installed-client fixtures: native identities, split finals, lost acknowledgment, live descendants, timeout and resume |
| Exact native/result identity | Original native source, versioned input and terminal result collector | `test_codex_gitlab_direct_native.py`: installed clients, real HTTP MCP and local model fixtures, scoped positive/negative permissions and exact output provenance |
| Native human conversations and held reviews | Targeted `mq_intake`, original native collectors and `mq_effective_stage` | `test_codex_gitlab_direct.py`: no general producer/classifier, causal continuations, original finals, failures/retries, checkpoints, source denials and transaction recovery; installed-client cold-resume probes; historical tools holds/fences |
| Direct publications and observation | Native GitLab tools, passive collector and raw inventory deltas | `test_codex_gitlab_direct.py`: self-output race, human edits, version/hold/transition boundaries and honest checkpoints; legacy recovery tests retain original journals |
| Scheduling and removal | Bounded tick, worker inventory and current config gates | Successive cycles, native oneshot lifetime/restart, slow HTTP/history vs sufficient answers, removal after send |
| Fresh start and instructions | Fresh state, new-chat producer and cutover | Old state/chats untouched, no legacy intake, native creation/cold resume |
| Visible native requests  | Existing stage input, native dispatch, input validation and question continuation | Exact message/context, historical reader, large Claude stdin, pre-exec failure and native creation/cold-resume checks |
| Explicit full-round restart  | Operator control, original native question, existing queue and intake | Native-answer frontier/races, late replies, exact target, fresh complete review/chat, FIFO/history/effect preservation and rejection controls |
| Explicit MR abandonment | `mq_restart_mr`, durable operator authority and settled-effect predicate | `test_codex_gitlab_restart_mr.py`: multi-job/head reset, unknown delivery, native denials, rollback, concurrency, idempotence, inventory and real worker progression |
| Shared editable workspace | Round snapshot and native launch policy | Same roots across reviewers/restart, linked Git metadata, read-only intake, original-chat answers |

The standalone CLI owns `MonitorQueue`, the ordered worker and one shared instruction producer.

`mq_workspace` owns round snapshots; `mq_codex_permissions`, `mq_native_selection`,
`mq_permission_profile` and `mq_claude_arguments` supply
native execution policies. `mq_codex_context` retains original source contexts. Workspace adapter
and installed-client probes are in `scripts/tests/test_codex_gitlab_workspace.py` and
`scripts/tests/test_codex_gitlab_workspace_native.py`, covering shared roots, restart, linked
metadata, actual editing/command behavior, read-only intake and original-chat hold answers.
Installed-client probes cover Docker, authenticated SSH, dependency HTTPS, local binding and
cold-resumed purpose transitions. `test_codex_gitlab_direct_native.py` exercises initial CI reads
and tool filtering with forbidden pipeline mutations present in the initial fixture catalog.
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
