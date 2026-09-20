# Implementation plan: close the decision-to-architecture gaps in the shared skills

**Status:** Planned
**Mode:** Plan only. The user instructed the recording of the decisions below; executing them needs
a later explicit instruction.

Three independent plan reviews ran. The first returned "not ready", and the second and the third
"ready after the blocking findings are fixed". Their findings are applied below, including the user
decisions they required, D10 to D12. The corrections made after the third review change no
decision, scope, or step order; what remains before execution is recorded under **Plan review**.

## Outcome

The shared skills `discussion-briefs`, `architecture-records`, and `plan-implementation` define,
without contradicting each other, how a decision the user takes in a discussion brief reaches an
approved architecture record: who records it, in what order, how the record shows a rule that the
code does not follow yet, and how nobody is left believing a decision is recorded when its owner has
not received it. The work ends when every obligation in the closure audit is verified, the touched
packages validate, the forward-test of D6 has met its pass criteria, and the high-risk closure audit
has passed.

## Scope

### In scope

- `.claude/skills/discussion-briefs/SKILL.md` and its template (D1, D5, D8, D9).
- `.claude/skills/architecture-records/SKILL.md` (D2 with the D10 criterion, the record side of D3
  and D4, and the D11 sentence).
- `.claude/skills/plan-implementation/SKILL.md` (D3 with the D12 fallback, D4, D7, and the consumer
  of D1 in its per-phase brief check).
- An inspection of the other consumers of the changed rules, with an edit only when the inspection
  shows it is needed: `.claude/skills/codex-claude-loop/SKILL.md`,
  `.claude/skills/documentation/SKILL.md`, `implementation-plans/README.md`, the opening statement
  of `plan-implementation` that durable design authority stays in architecture records, the full
  and compact plan templates, the architecture record and index templates, and the registry entries
  and frontmatter descriptions of the three skills.
- Throwaway forward-test fixtures under the session scratchpad (D6).
- The brief that feeds this plan: its pointers, state, links when this plan moves, and corrections
  of explanatory text that a review shows to be wrong, without changing a decision line.

### Out of scope

- The global instructions in `.codex/AGENTS.md`, including the question-only gate and the Git and
  review authorization sections, beyond a registry entry that a changed description requires.
- Any Git staging, commit, or push.
- An architecture record or an `architecture/` directory for this flow: under D11 none is created.
- Renumbering existing briefs under D8, and retrospective edits to completed plans.
- The repository of the other conversation that exposed the problem; nothing there is read or
  changed.

## Governing decisions and invariants

The user took these decisions in
[the brief](../briefs/decision-to-architecture-flow.md) and then instructed their recording.

| Brief item | Decision |
| --- | --- |
| D1 | When recording decisions, the agent names the owner of each one: a durable design decision belongs to the architecture record, and the execution sequence belongs to the plan. While an owner has not received the decision, the brief item keeps `registro pendente` for that owner, the brief cannot be concluded, and the chat reply says what was left out and why. |
| D2 | A deliberate user decision that changes an implemented record enters in one of two forms. A small change enters as a block labelled "Approved amendment, in implementation" directly under the rule it changes; the current rule stays unmarked and the block says that the rule above is still in force. At most one pending block per rule; no dates, plan links, or progress inside it; the closure pass removes it when the rule is rewritten. A large change uses a new record in the Proposed state plus a one-line notice at the top of the old record, which becomes Superseded only when the new record is Implemented. D10 defines how the agent chooses between the two forms. |
| D3 | When the plan itself proposes the design change, the order is: user decision, record amendment, plan derived from the amended record, independent review of both, then code. |
| D4 | The session that conducted the discussion and wrote the plan amends the architecture record before handing the work over. The implementing session is told that the records are already amended and implements against them. |
| D5 | Replace the sentence in `discussion-briefs` that tells the agent to "let the record's own skill decide how the record changes" with a pointer to the concrete procedure created by D2, D3, and D4, in the same pass as the other changes. |
| D6 | After the changes, forward-test the case that failed in practice: the user sends "registre as decisões" and one decision belongs to an approved architecture record. Start with the small-change variant, two runs. |
| D7 | Before a plan moves to `completed/`, `plan-implementation` checks the same-subject brief. A decision still marked `registro pendente` blocks the closure. An item that is merely open is reported to the user in the closing message, noted in the plan, and does not block. |
| D8 | In new briefs each section has its own prefix and sequence, starting at 1: `D` for decisions between options, `T` for work the agent can do, and another prefix for external dependencies. An item number never changes; an item that changes nature is recreated in the right section and the old one stays `descartado`, pointing at the new one. |
| D9 | The template's work item gains the same depth as a decision item: the question for the user, a concrete example, what happens under each answer, and a recommendation. |
| D10 | The purpose decides between the amendment block and a new record: avoid noise in the record when writing a new one would be easier. The block is the default. A new record is used when amending the old one would leave more noise than writing a new one. To judge, the agent lists the places in the record that the decision forces to change: rules, flow sections, diagrams, and tables. A short list of rules only gives the block; a long list, or one that includes a flow section, diagram, or table, gives the new record. The agent shows that list in chat with the form it chose, and asks before writing when in doubt. There is no fixed count of rules. The choice is reversible text made before any code, and the plan review also judges the form. The existing guard stays: a record is created or superseded only when the design actually changes; when much changes without changing the design, the agent uses blocks and asks first. The nature of the change sets the rigor, not the form. The skill carries two short examples, one for each side. |
| D11 | The skills are the durable authority for this flow, and no architecture record is created for it. Each new rule carries its reason in a sentence inside the skill; the rejected alternatives stay in this plan, once completed, and in the brief. `architecture-records` gains a sentence saying that the workflow rules of shared skills, and their reasons, live in the skills themselves. D1 to D4 and D7 therefore do not regain `registro pendente`: the plan owns the sequence, and the skills receive the rules when the plan is executed. |
| D12 | When editing the record would require a change outside the bounds of the D3 exception, such as translating a record that is not in English or removing a manual table of contents, the exception does not apply. The agent says so in chat, the brief item keeps `registro pendente` for the record, and the maintenance and the amendment become plan steps after the independent plan review. The per-phase brief check in `plan-implementation` gains the clause "except the step that records the decision in that owner", so that it does not block the step that resolves the pending marker. That clause is delimited under the invariants below. |

Alternatives the user rejected, kept here because D11 makes this plan and the brief their home; the
brief holds the full reasoning in Portuguese:

- D1: leaving the agent to choose where to record and when the brief closes.
- D2: always using a new Proposed record, and marking the whole record "In implementation".
- D3: plan review first, with the record amended only after it.
- D4: the implementing session amends the record, or the discussion session by default with a
  stated exception.
- D7: a passive chat reminder of open briefs, separate folders for open and concluded briefs, and no
  check at all.
- D8: one sequence with the `D` prefix plus an explanation, and one neutral prefix for every item.
- D10: choosing the form by the nature of the change, by a count of rules, or by both together.
- D11: an `architecture/` record in this repository, and a `references/` file inside one skill.
- D12: doing the maintenance first as separate work and then amending before the review, and asking
  the user case by case.
- D5, D6, and D9 were answers of do, do not, or defer; the user chose to do each one.

Invariants and bounds that the changes must preserve:

- A record never presents proposed behavior as current, and no two texts are authoritative for the
  same scope and phase. The coexistence rule below splits authority by scope; it does not create
  concurrent authorities.
- A record carries no execution diary: no timestamps, plan links, or progress narration.
- A decision changes only the brief; promotion needs the user's explicit instruction and never
  includes implementing the decision. Decision, promotion, and execution stay three separate
  operations.
- D3 is a deliberate exception, chosen by the user, to the rule that the plan review precedes any
  implementation step. It is not a reading of the current text. Its bounds: before the plan review,
  the only permitted change is the D2-labelled block under the rule it changes, or the new Proposed
  record plus the one-line notice on the old one and the index entry that `architecture-records`
  requires for every current record. No other record text, no code or configuration, and no
  repository instruction file changes. The exception waives no other obligation of
  `architecture-records`: when editing the record would also require a change outside these bounds,
  such as translating a record that is not in English or removing a manual table of contents, the
  exception does not apply, the agent says so, and the amendment follows the ordinary order, after
  the plan review. The user chose that fallback under D12. Synchronizing the instruction file, which
  `architecture-records` requires when behavior changes, waits for the implementation because it
  would present proposed behavior as current. Every other implementation step still waits for the
  plan review. The review examines the amendment together with the plan, and a finding against the
  amendment is corrected in the block or the Proposed record.
- Authority while both texts coexist: the current rule stays in force for every consumer except the
  work this kind of plan authorizes, and the amendment or the Proposed record prescribes only that
  work. The block states which rule is in force, not the state of the code. Partial progress lives
  in the plan, never in the record. The closure pass rewrites the rule and removes the block or the
  notice whether or not the record's lifecycle state changes.
- Authority and owner are different things here. The authority is the text that governs agent
  behavior; the owner is the document where a decision is recorded when it is promoted. Under D11
  the skills become the authority for this flow when the plan is executed, and the plan is the
  owner until then.
- An owner, for D1 and for the per-phase brief check, is a document that records decisions: the
  plan, an architecture record, or an issue. The code or skill text that a plan will change is the
  target of the work, never an owner that must carry the decision before a phase starts. Under D11
  the decisions of this plan have one owner, the plan.
- The D12 exemption in the per-phase brief check is narrow. After the plan review that D12
  requires, the promotion unit may start although the record does not carry the decision yet. That
  unit is the amendment of the record together with the maintenance that `architecture-records`
  makes mandatory for that edit. The exemption waives only the pending marker that this unit
  resolves. The user's instruction to record stays required, and every other pending decision and
  all work that depends on the amendment stay subject to the check. The session named by D4
  performs the unit, before the handoff.
- D7 adds a check and relaxes no existing completion gate. An open brief item that stands for a
  required validation, authorization, or access still blocks closure through the existing gates;
  "does not block" means that the brief check alone does not.
- A subagent or reviewer never creates or edits a brief, and nothing in a brief authorizes work.

High-risk trigger: D3 is an exception to the order of a mandatory review and D7 adds a closure gate
in `plan-implementation`; D2 changes lifecycle rules of `architecture-records`, whose imperatives
are delivery gates; and D11 narrows when that skill requires a record.

## Current evidence and assumptions

### Verified evidence

- `architecture-records` has lifecycle states for the whole record only, and no procedure for an
  amendment block. It does not say when the old record becomes Superseded relative to the new one
  being Implemented.
- Its criterion for amending versus creating or superseding a record sits in the incident-diagnosis
  section and looks at the nature of the change: amend when the durable contract was incomplete;
  create or supersede only when the ownership model, authority boundary, stage order, failure
  meaning, or recovery policy actually changes. It does not count rules, so it is not the size
  criterion the brief first described under D2. "Only when" states a necessary condition for a new
  record, which the D10 guard keeps.
- It mentions a deliberate decision twice, without a procedure: the classification section says to
  change the record first only when a deliberate architecture decision changes the approved design,
  and the source-of-truth section says an approved record governs until a deliberate decision
  supersedes or amends it.
- `plan-implementation` requires the risk-appropriate plan review before any implementation step
  starts, and classifies changes to mandatory review and closure gates in skills as high risk. It
  also requires amending or superseding the record first when a durable invariant must change. It
  does not say whether amending the record is an implementation step.
- Its per-phase check on a same-subject brief holds a phase "until the user instructs its recording
  and the plan carries it". That check looks only at the plan and does not check any other owner
  of the decision, so D1 must reach it.
- `discussion-briefs` tells the agent to report a contradiction with an approved record and let the
  record's own skill decide how the record changes, and subordinates promotion to any plan or review
  the owner's skill requires.
- In the first run of forward-test case C, recorded in
  [the completed plan](../completed/discussion-briefs-review.md), an agent superseded an approved
  record immediately and changed no code. Whether the fixture's code followed the old record was not
  verified.
- This repository has no `architecture/` directory, and earlier gate changes to the shared skills
  were kept in the skills and in a completed plan. By their letter, `architecture-records`, which
  classifies a long-lived decision with its rationale and rejected alternatives as a record, and
  `documentation`, which sends a changed stage order or ownership boundary to that skill, point to a
  record for D1 to D4 and D7. The user decided otherwise under D11; the new sentence in
  `architecture-records` states that exception.
- In `codex-claude-loop` the planner session owns plan changes after a decision, and the skill does
  not say who amends a record. It also says that the planner "does not edit the implementation in
  this workflow". Whether the D4 amendment, which D3 treats as an exception to the order of
  implementation steps, stays on the planner's side of that line is unresolved; the consumer
  analysis must settle it.
- `plan-implementation` opens by keeping durable design authority in architecture records,
  `documentation` keeps the extended rationale in the architecture record, and
  `implementation-plans/README.md` says that durable cross-component decisions belong in
  architecture records. `plan-implementation` requires that README to define the boundary between
  temporary execution authority and durable architecture records. All three are consumers of the
  D11 exception.

- The authoring client keeps, in the local history of the session, a transcript file for each
  subagent run and a metadata file that names the run. The transcripts of the earlier forward-test
  runs of this session were checked and contain the tool calls of the run.

### Open assumptions

- The account of the other conversation, in which a decision was recorded only in the plan and the
  brief was concluded, comes from text the user pasted. It motivates the change but was not
  inspected. No step depends on it.
- The D6 forward-test covers only the small-change variant, so it does not exercise the D10 judgment
  between the two forms. That judgment is verified by inspection of the text only.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Advisor review and fresh-context independent review of the first version of this plan. | High risk: review order and closure gates change. | Not ready; findings under **Plan review**; plan revised. |
| completed | Carry the user's decisions on brief items D10 and D11 into this plan, on the user's recording instruction. | Both needed a user decision. | Decision rows, scope, evidence, steps, and closure rows updated; brief items linked. |
| completed | Second fresh-context independent review, of the revised plan. | A material replan inherits the high-risk review. | Ready after the blocking findings are fixed; four blocking and four non-blocking findings applied. |
| completed | Advisor review of the corrected plan. | A material replan inherits the advisor review too. | Three findings applied; see **Plan review**. |
| completed | Carry the user's decision on brief item D12 into this plan, on the user's recording instruction. | The D3 fallback needed a user decision. | Decision row, D3 bounds, the `plan-implementation` step, and the closure rows updated; brief item linked. |
| completed | Third fresh-context independent review, of the corrected plan. | A material replan inherits both high-risk reviews. | Ready after the blocking findings are fixed; three blocking and three non-blocking findings applied. |
| pending | Advisor review of the corrections made after the third review, which is done, and a confirmation from the third reviewer's session that its findings are resolved. | The corrections change no decision, scope, or step order, so a delta confirmation is proportionate; a finding that does change one of them reopens the full review. | Findings under **Plan review**. |
| pending | Authenticate the current text: reread the three skills in full and confirm each passage under **Verified evidence**. | None. | Each cited passage found or the evidence corrected. |
| pending | Consumer analysis before any edit: `codex-claude-loop`, including whether the D4 amendment is planner work under its rule that the planner does not edit the implementation; `documentation`, `implementation-plans/README.md`, and the opening statement of `plan-implementation`, for the D11 exception; the full and compact plan templates, the architecture record and index templates, the brief template, and the registry entries and frontmatter descriptions. | Compatibility is decided before dependent text is written. | Each consumer marked "changes" or "unchanged" with a reason; a contradiction triggers a replan. |
| pending | `architecture-records`: add the procedure for a deliberate decision (D2 with the D10 criterion and its two examples, and the record side of D3 and D4), the authority rule while both texts coexist, the removal of the block or notice in the closure pass and the validation list, and the D11 sentence. Qualify the lifecycle sentence that forbids two concurrently authoritative records, so that it agrees with the coexistence rule: no two texts authoritative for the same scope and phase. | The examples are generic, with no project-specific names, as `documentation` requires. The incident criterion stays as it is. | Validator passes; the new text contradicts no existing gate of the skill. |
| pending | `plan-implementation`: state the D3 exception with its bounds, the D4 owner of the amendment, the D7 closure check in both the proportional-closure section and the completion gates, covering compact plans, and change the per-phase brief check so that a phase waits until every recording owner named for the decision carries it, with the owner definition above and the D12 exemption exactly as delimited under the invariants: only the promotion unit, only the pending marker it resolves, the recording instruction still required. State the D12 fallback beside the D3 bounds, with its two examples. | D3 is a bounded exception, not a reclassification of record edits in general. | Validator passes; the executable sequence, the per-phase check, and the closure sections agree. |
| pending | `discussion-briefs`: D1, D5, D8, and D9 in `SKILL.md` and the template. Each new rule in the three skills carries its reason in a sentence (D11). | D5 points at text that exists after the two steps above. | Validator passes on the package and its symlink. |
| pending | Validate the whole change: validators, width scan, `git diff --check`, and a cross-skill reread for contradictions. | The validator checks structure only, never decisions or gates. | Clean results, a scoped diff, and the reread recorded. |
| pending | D6 forward-test, small-change variant, two sequential runs. | A weaker model follows the new text. The client stores a transcript of each subagent run in its local session history. | A fresh fixture per run; the prompt withholds the expected outcome. A run passes only when all hold. Record: a comparison of the whole record before and after shows exactly one added block and no other change; the block sits directly under the right rule, carries the "Approved amendment, in implementation" label, states the user's decision, says that the rule above is still in force, and contains no date, plan link, or progress note; the old record is not superseded. Plan and brief: the plan carries the sequence; the brief item links to both owners and keeps no pending marker. Reply: it names where each decision was recorded and says that the decision is approved while the plan review is still to come. Side effects: the before and after snapshots show no other file, no code, and no Git state changed, and the stored transcript of the run shows no edit outside the three documents and no state-changing Git command, including one that was later undone. Any miss fails the run. When the transcript is unavailable, the absence of prohibited operations is recorded as unverified and the run does not count as a pass. Before the runs, judge hand-made defective results with the same criteria and confirm that each fails: only the plan received the decision; the block has no label; the block carries a date or a plan link; a second block sits under the same rule; another rule of the record was altered. These add no agent run. |
| pending | Closure audit, independent second pass, and the D7 brief check before moving this plan; update the brief's links when it moves. | None. | Matrix complete and verdict recorded. |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

## Plan review

- **Risk classification:** High risk. The change makes an exception to the order of a mandatory
  review and adds a closure gate in shared skills.
- **Mechanism:** Advisor: the advisor tool of the authoring Claude session. Independent reviewer:
  `gpt-6-astra` at `high` reasoning effort, from another provider, in a fresh Codex session that the
  user opened. It only read and reported, and its prompt withheld the intended verdict and the
  advisor's findings. Baseline: commit `87027b4`, with the brief modified and this plan untracked.
- **First independent review:** Verdict "not ready": eight blocking and three non-blocking findings.
  Fidelity of the nine decision rows to the brief was confirmed, apart from the points below.
- **Applied from the first review:**
  - The earlier justification that the D3 amendment "does not weaken the gate" was withdrawn. It had
    come from the advisor's first review and presented a deliberate reorder as gate preservation.
    D3 is now stated as a bounded exception, together with the authority rule while both texts
    coexist and the removal of the block independent of lifecycle state.
  - D7 is stated as an added check that relaxes no existing completion gate. This clarifies the
    decision and was reported to the user.
  - The per-phase brief check in `plan-implementation` entered the scope as a consumer of D1; the
    consumer analysis moved ahead of the edits and now covers the plan and record templates.
  - The D6 pass criteria, fixture isolation, withheld expected outcome, and a no-run sensitivity
    control were specified; the outcome now requires the test to pass, not only to run.
  - The closure matrix was decomposed by obligation.
  - Evidence corrected: two mentions of a deliberate decision, the unverified fixture code, and the
    narrowed exclusion of existing briefs. The D5 row regained "in the same pass".
- **Decided by the user after the review:** the criterion between the amendment block and a new
  record, which the brief had wrongly called the same as the incident criterion, is now the purpose
  test of D10; and D1 to D4 and D7 get no architecture record, because the skills are their durable
  authority (D11). The absence of a directory had not settled that.
- **Rejected from the first review:** None. The reviewer's suggested defective-result control was
  adopted as a judgment of a hand-made result instead of an extra agent run, because the user
  authorized two runs.
- **Second independent review:** `gpt-6-astra` at `high`, in a new fresh Codex session that the
  user opened, read-only, with a prompt that withheld the intended verdict. It ran at commit
  `87027b4` with the brief modified and this plan untracked; the user has since committed both.
  Verdict: "ready after the blocking findings are fixed": four blocking and four non-blocking
  findings, none needing a user decision. It confirmed the fidelity of rows D1 to D10 and found the
  D11 row incomplete.
- **Applied from the second review:**
  - The D3 bounds now include the index entry for a new record and state that the exception waives
    no other obligation of `architecture-records`; when such an obligation needs a change outside
    the bounds, the amendment follows the ordinary order. That fallback was reported to the user as
    a clarification awaiting confirmation.
  - The D11 row regained the part about `registro pendente`; an owner is now defined as a document
    that records decisions, so that the per-phase check never waits for skill text the plan itself
    will write; `plan-implementation`, `documentation`, and `implementation-plans/README.md`
    entered the consumer analysis for the D11 exception.
  - The review step now includes the advisor.
  - The D6 criteria now require the label, the statement that the rule above is still in force,
    and a reply that separates the approved decision from the pending review; the limit of the
    snapshots is stated.
  - Non-blocking: the evidence about the per-phase check and about `codex-claude-loop` was made
    precise, with the planner's "does not edit the implementation" rule left to the consumer
    analysis; the closure rows for D7, D8, and D11 were tightened; the rejected alternatives of D1,
    D8, and the do-or-defer items were added; the brief no longer claims that the old fixture's
    code followed its record.
- **Rejected from the second review:** None.
- **Advisor review of the corrected plan:** the advisor tool of the authoring Claude session.
  Applied: the second independent review gained its own completed step; the D3 fallback was
  recognized as a choice among alternatives and handed to the user, who chose it as brief item
  D12, together with a clause that keeps the per-phase check from blocking the step that records
  the decision; authority and owner were distinguished in the
  invariants. Noted: the example block in the brief said that the code follows the rule above,
  while this plan has the block state which rule is in force; the brief's example was aligned with
  the plan. Confirmed: the owner definition resolves the D11 finding without changing D11, the D6
  criteria now fail an unlabelled amendment, and the D3 bounds include the index entry. Rejected:
  none.
- **Third independent review:** `gpt-6-astra` at `high`, in another fresh Codex session that the
  user opened, read-only, with a prompt that withheld the intended verdict. It ran at commit
  `8c78d2c` with this plan and the brief modified. Verdict: "ready after the blocking findings are
  fixed": three blocking and three non-blocking findings, none needing a user decision. It confirmed
  the fidelity of all twelve rows and every claim under **Verified evidence**.
- **Applied from the third review:**
  - The D12 exemption was delimited: only the promotion unit, only the pending marker it resolves,
    the recording instruction still required, dependent work still checked, the D4 session
    responsible.
  - The D6 verifier now compares the whole record, requires exactly one block without diary
    content, and judges five hand-made defective results.
  - Prohibited operations are judged from the stored transcript of each run together with the
    snapshots, and a run without that evidence does not count as a pass.
  - Non-blocking: authority is now forbidden only when concurrent for the same scope and phase; the
    matrix gained the validation row and the remaining D10 conditions; three explanatory passages
    of the brief were aligned with the decisions.
- **Rejected from the third review:** None.
- **Advisor review of the corrections after the third review:** the advisor tool of the authoring
  Claude session. It found that the corrections resolve the three blocking findings. Applied: the
  promotion unit of the D12 exemption was stated in the brief as a clarification under the user's
  decision line, and the D12 row now points to the invariant that delimits its clause; the evidence
  about stored transcripts was checked against the files before staying under **Verified
  evidence**; the `architecture-records` step now qualifies the skill's own sentence about
  concurrent authority. Rejected: none.
- **Next:** a reviewer confirmation, not a fourth independent review: the third reviewer's session
  states whether each of its findings is resolved and judges only the changed passages. The
  corrections change no decision, scope, or step order, so another full review is not planned. A
  finding that does change one of them, or a request from the user, reopens the full fresh-context
  review.

## Replan conditions

- A reviewer finds that the D3 exception weakens a review or authorization gate beyond its stated
  bounds. The first review triggered the earlier form of this condition.
- `codex-claude-loop`, a template, or another shared skill contradicts D1, D4, or D7.
- A change to the global instructions turns out to be necessary.
- The forward-test exposes a defect that needs a user decision; it then becomes a new brief item.

## Completion evidence

- Pending.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| pending | D1: a decision recorded in only one of its owners keeps `registro pendente` for the other, the brief stays open, and the reply names what was left out and why. | `discussion-briefs`; the per-phase check in `plan-implementation`. | Pending. |
| pending | Decision, promotion, and execution remain three separate operations. | `discussion-briefs`. | Pending. |
| pending | D2 small variant: block placement, one per rule, no diary content, the rule above unmarked, and removal at closure even when the lifecycle state does not change. | `architecture-records` procedure, closure pass, and validation list. | Pending. |
| pending | D2 large variant: Proposed record plus notice line; the old record becomes Superseded only when the new one is Implemented; never two texts authoritative for the same scope and phase. | `architecture-records`. | Pending. |
| pending | D10: the block is the default; the agent lists the places that change, shows the list with the chosen form, and asks when in doubt; a short list of rules gives the block and a long list, or one with a flow section, diagram, or table, gives the new record; when much changes without changing the design the agent uses blocks and asks first; no fixed count; the choice is reversible; the guard that a record is created only when the design changes is kept; the incident criterion is unchanged and not contradicted; two generic examples exist. Verified by inspection, because D6 does not exercise it. | `architecture-records`. | Pending. |
| pending | The D3 exception and its bounds read the same in `plan-implementation` and `architecture-records`, including the index entry and the fallback to the ordinary order when another obligation of `architecture-records` needs a change outside the bounds; every other step still waits for the plan review; instruction-file synchronization waits for implementation. | Both skills. | Pending. |
| pending | D12: the fallback is stated beside the D3 bounds in both skills, with its two examples; under it the brief item keeps the pending marker for the record and the maintenance and the amendment are plan steps after the plan review; the per-phase exemption covers only the promotion unit and only the pending marker it resolves, keeps the recording instruction required, leaves dependent work and other pending decisions under the check, and keeps the D4 session responsible. | `plan-implementation`; `architecture-records`; `discussion-briefs`. | Pending. |
| pending | Authority while the current rule and the amendment coexist is defined by scope and phase. | `architecture-records`; `plan-implementation`. | Pending. |
| pending | D4: the amending session is named, and `codex-claude-loop` stays compatible. | `plan-implementation`; `architecture-records`; `codex-claude-loop`. | Pending. |
| pending | D5: the sentence is replaced and points at text that exists. | `discussion-briefs`. | Pending. |
| pending | D7: the check exists in the proportional closure and in the completion gates, for full and compact plans; a pending marker blocks; an open item is reported to the user and noted in the plan; no existing gate is relaxed. | `plan-implementation`. | Pending. |
| pending | D8: per-section prefixes, identifier stability, the change-of-nature rule, and the identifiers of existing briefs unchanged. | `discussion-briefs` and its template. | Pending. |
| pending | D9: every requested field exists in the template's work item. | The brief template. | Pending. |
| pending | D6: both runs met every pass criterion, including the whole-record comparison and the transcript check; each hand-made defective result failed as expected; the fixtures were isolated and fresh; any property left unverified is reported as such. | Scratchpad fixtures. | Pending. |
| pending | Every listed consumer was inspected and either changed or justified as unchanged. | Templates, `codex-claude-loop`, registry entries, frontmatter descriptions. | Pending. |
| pending | D11: `architecture-records` states that workflow rules of shared skills and their reasons live in the skills; `documentation` does not contradict it; `plan-implementation` and `implementation-plans/README.md` do not contradict it either; each new rule carries its reason in a sentence; the rejected alternatives of every decision are kept in this plan and in the brief; the per-phase check does not wait for skill text that the plan itself will write; no architecture record or directory was created. | `architecture-records`; `documentation`; `plan-implementation`; `implementation-plans/README.md`; the three skills. | Pending. |
| pending | The validation step ran in full: each touched package passed the validator, the width scan and `git diff --check` were clean, and the cross-skill reread for contradictions was done and recorded, knowing that the validator checks structure only. | The three skills, the templates, and any consumer that changed. | Pending. |
| pending | Only in-scope files changed; nothing staged or committed. | Working tree. | Pending. |
| pending | Changes made after the audit were revalidated, and the brief's links were updated when this plan moved. | This plan and the brief. | Pending. |

- Architecture to implementation: Pending.
- Implementation to authority: Pending.

### Final conformance verdict

- **Verdict:** Pending
- **Second pass:** Pending
- **Auditor and evidence:** Pending.
- **Unresolved requirements:** Pending.
