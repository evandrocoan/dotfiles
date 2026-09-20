# Implementation plan: close the decision-to-architecture gaps in the shared skills

**Status:** Planned
**Mode:** Plan only. The user instructed the recording of the decisions below; executing them needs
a later explicit instruction.

The first independent plan review returned "not ready". Its findings are applied below, including
the two user decisions it required, D10 and D11. This revised plan needs a new fresh-context
independent review before any execution.

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
- `.claude/skills/plan-implementation/SKILL.md` (D3, D4, D7, and the consumer of D1 in its
  per-phase brief check).
- An inspection of the other consumers of the changed rules, with an edit only when the inspection
  shows it is needed: `.claude/skills/codex-claude-loop/SKILL.md`,
  `.claude/skills/documentation/SKILL.md`, the full and compact plan templates, the architecture
  record and index templates, and the registry entries and frontmatter descriptions of the three
  skills.
- Throwaway forward-test fixtures under the session scratchpad (D6).
- The brief that feeds this plan: its pointers, state, and links when this plan moves.

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
| D11 | The skills are the durable authority for this flow, and no architecture record is created for it. Each new rule carries its reason in a sentence inside the skill; the rejected alternatives stay in this plan, once completed, and in the brief. `architecture-records` gains a sentence saying that the workflow rules of shared skills, and their reasons, live in the skills themselves. |

Alternatives the user rejected, kept here because D11 makes this plan and the brief their home; the
brief holds the full reasoning in Portuguese:

- D2: always using a new Proposed record, and marking the whole record "In implementation".
- D3: plan review first, with the record amended only after it.
- D4: the implementing session amends the record, or the discussion session by default with a
  stated exception.
- D7: a passive chat reminder of open briefs, separate folders for open and concluded briefs, and no
  check at all.
- D10: choosing the form by the nature of the change, by a count of rules, or by both together.
- D11: an `architecture/` record in this repository, and a `references/` file inside one skill.

Invariants and bounds that the changes must preserve:

- A record never presents proposed behavior as current, and two records are never authoritative at
  the same time.
- A record carries no execution diary: no timestamps, plan links, or progress narration.
- A decision changes only the brief; promotion needs the user's explicit instruction and never
  includes implementing the decision. Decision, promotion, and execution stay three separate
  operations.
- D3 is a deliberate exception, chosen by the user, to the rule that the plan review precedes any
  implementation step. It is not a reading of the current text. Its bounds: before the plan review,
  the only permitted change is the D2-labelled block under the rule it changes, or the new Proposed
  record plus the one-line notice on the old one. No other record text, no code or configuration,
  and no repository instruction file changes; synchronizing the instruction file, which
  `architecture-records` requires when behavior changes, waits for the implementation because it
  would present proposed behavior as current. Every other implementation step still waits for the
  plan review. The review examines the amendment together with the plan, and a finding against the
  amendment is corrected in the block or the Proposed record.
- Authority while both texts coexist: the current rule stays in force for every consumer except the
  work this kind of plan authorizes, and the amendment or the Proposed record prescribes only that
  work. The block states which rule is in force, not the state of the code. Partial progress lives
  in the plan, never in the record. The closure pass rewrites the rule and removes the block or the
  notice whether or not the record's lifecycle state changes.
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
  and the plan carries it", which accepts the plan as a sufficient owner and so consumes D1.
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
- The independent reviewer reported no direct contradiction between D4 and `codex-claude-loop`: its
  planner session owns plan changes after a decision, and it does not say who amends a record.
  Reread at execution.

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
| pending | New fresh-context independent review of the revised plan. | A material replan inherits the high-risk review. | Findings under **Plan review**; verdict ready. |
| pending | Authenticate the current text: reread the three skills in full and confirm each passage under **Verified evidence**. | None. | Each cited passage found or the evidence corrected. |
| pending | Consumer analysis before any edit: `codex-claude-loop`, `documentation`, the full and compact plan templates, the architecture record and index templates, the brief template, and the registry entries and frontmatter descriptions. | Compatibility is decided before dependent text is written. | Each consumer marked "changes" or "unchanged" with a reason; a contradiction triggers a replan. |
| pending | `architecture-records`: add the procedure for a deliberate decision (D2 with the D10 criterion and its two examples, and the record side of D3 and D4), the authority rule while both texts coexist, the removal of the block or notice in the closure pass and the validation list, and the D11 sentence. | The examples are generic, with no project-specific names, as `documentation` requires. The incident criterion stays as it is. | Validator passes; the new text contradicts no existing gate of the skill. |
| pending | `plan-implementation`: state the D3 exception with its bounds, the D4 owner of the amendment, the D7 closure check in both the proportional-closure section and the completion gates, covering compact plans, and change the per-phase brief check so that a phase waits until every owner named for the decision carries it. | D3 is a bounded exception, not a reclassification of record edits in general. | Validator passes; the executable sequence, the per-phase check, and the closure sections agree. |
| pending | `discussion-briefs`: D1, D5, D8, and D9 in `SKILL.md` and the template. Each new rule in the three skills carries its reason in a sentence (D11). | D5 points at text that exists after the two steps above. | Validator passes on the package and its symlink. |
| pending | Validate the whole change: validators, width scan, `git diff --check`, and a cross-skill reread for contradictions. | The validator checks structure only, never decisions or gates. | Clean results, a scoped diff, and the reread recorded. |
| pending | D6 forward-test, small-change variant, two sequential runs. | A weaker model follows the new text. | A fresh fixture per run; the prompt withholds the expected outcome. A run passes only when all hold: the block sits under the right rule, states the user's decision, and leaves the rule above unchanged; the plan carries the sequence; the brief item links to both owners and keeps no pending marker; the reply names where each decision was recorded and that the review comes next; snapshots show no other file, no code, and no Git state changed, and the old record is not superseded. Any miss fails the run. Before the runs, judge a hand-made defective result, in which only the plan received the decision, with the same criteria and confirm that it fails; this adds no agent run. |
| pending | Closure audit, independent second pass, and the D7 brief check before moving this plan; update the brief's links when it moves. | None. | Matrix complete and verdict recorded. |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

## Plan review

- **Risk classification:** High risk. The change makes an exception to the order of a mandatory
  review and adds a closure gate in shared skills.
- **Mechanism:** Advisor: the advisor tool of the authoring Claude session. Independent reviewer:
  `gpt-6-astra` at `high` reasoning effort, from another provider, in a fresh Codex session that the
  user opened. It only read and reported, and its prompt withheld the intended verdict and the
  advisor's findings. Baseline: commit `87027b4`, with the brief modified and this plan untracked.
- **Independent reviewer:** Verdict "not ready": eight blocking and three non-blocking findings.
  Fidelity of the nine decision rows to the brief was confirmed, apart from the points below.
- **Applied:**
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
- **Rejected:** None. The reviewer's suggested defective-result control was adopted as a judgment of
  a hand-made result instead of an extra agent run, because the user authorized two runs.
- **Next:** a new fresh-context independent review of this revised plan.

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
| pending | D2 large variant: Proposed record plus notice line; the old record becomes Superseded only when the new one is Implemented; never two authoritative records. | `architecture-records`. | Pending. |
| pending | D10: the block is the default; the agent lists the places that change, shows the list with the chosen form, and asks when in doubt; no fixed count; the choice is reversible; the guard that a record is created only when the design changes is kept; the incident criterion is unchanged and not contradicted; two generic examples exist. Verified by inspection, because D6 does not exercise it. | `architecture-records`. | Pending. |
| pending | The D3 exception and its bounds read the same in `plan-implementation` and `architecture-records`; every other step still waits for the plan review; instruction-file synchronization waits for implementation. | Both skills. | Pending. |
| pending | Authority while the current rule and the amendment coexist is defined by scope and phase. | `architecture-records`; `plan-implementation`. | Pending. |
| pending | D4: the amending session is named, and `codex-claude-loop` stays compatible. | `plan-implementation`; `architecture-records`; `codex-claude-loop`. | Pending. |
| pending | D5: the sentence is replaced and points at text that exists. | `discussion-briefs`. | Pending. |
| pending | D7: the check exists in the proportional closure and in the completion gates, for full and compact plans; a pending marker blocks; an open item is reported; no existing gate is relaxed. | `plan-implementation`. | Pending. |
| pending | D8: per-section prefixes, identifier stability, the change-of-nature rule, and existing briefs untouched. | `discussion-briefs` and its template. | Pending. |
| pending | D9: every requested field exists in the template's work item. | The brief template. | Pending. |
| pending | D6: both runs met the pass criteria, the defective control failed as expected, and the fixtures were isolated and fresh. | Scratchpad fixtures. | Pending. |
| pending | Every listed consumer was inspected and either changed or justified as unchanged. | Templates, `codex-claude-loop`, registry entries, frontmatter descriptions. | Pending. |
| pending | D11: `architecture-records` states that workflow rules of shared skills and their reasons live in the skills; `documentation` does not contradict it; each new rule carries its reason in a sentence; no architecture record or directory was created. | `architecture-records`; `documentation`; the three skills. | Pending. |
| pending | Only in-scope files changed; nothing staged or committed. | Working tree. | Pending. |
| pending | Changes made after the audit were revalidated, and the brief's links were updated when this plan moved. | This plan and the brief. | Pending. |

- Architecture to implementation: Pending.
- Implementation to authority: Pending.

### Final conformance verdict

- **Verdict:** Pending
- **Second pass:** Pending
- **Auditor and evidence:** Pending.
- **Unresolved requirements:** Pending.
