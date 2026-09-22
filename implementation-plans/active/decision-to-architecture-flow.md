# Implementation plan: close the decision-to-architecture gaps in the shared skills

**Status:** In progress

Current discussion: [closure brief](../briefs/decision-to-architecture-closure.md). The
[previous brief](../briefs/decision-to-architecture-flow.md) preserves the recorded decisions.
This navigation change supplies no new execution authorization and changes no closure gate.

## Current execution: T1 corrections and T2 deferral

The user explicitly instructed recording the decisions and executing T1. This section is the
current execution contract; the completed comparisons below remain evidence. This plan is the
sole recording owner under D11. The skills are implementation targets, not additional owners.

| Decision | Recorded scope and disposition |
| --- | --- |
| [T1](../briefs/decision-to-architecture-closure.md#t1--corrigir-os-dois-defeitos-textuais-encontrados) | Do both narrow textual corrections: bind documentation's root compatibility setup to authorized instruction work, and clarify where a whole replacement carries preserved guarantees. Implement after the inherited review. |
| [T2](../briefs/decision-to-architecture-closure.md#t2--reorganizar-agora-as-skills-para-separar-as-fases-do-trabalho) | Defer broad skill reorganization. Reconsider after T1 and useful evidence about the transition failure; that condition does not automatically authorize T2. It adds no closure requirement. |

The outcome for T1 is unambiguous instruction scope and placement of preserved rules. It does
not establish that a model will perform the complete recording task or plan a safe transition.
Do not change D18/D22 acceptance, D20.2, D24, or E2. Do not create an architecture record for
shared-skill workflow rules, reorganize phases, change global instructions, repair historical
results, or mutate Git state. Preserve all pre-existing working-tree changes.

### T1 evidence, candidate, and review boundary

Risk remains high under this existing plan; the compatibility trigger also affects authorization
scope. Advisor unavailable. Obtain a fresh read-only Sol xhigh plan review before editing either
source. The review examines this bounded continuation, its candidates, affected consumers, and
inherited gates. No desired verdict is supplied. The later E2 remains the user-opened independent
review of the whole delivery, after required validation and the author audit.

Authenticated defects are R1/R2 in **Skill source review**. The current documentation paragraph
triggers setup from the mere existence of a root instruction file. The architecture template
says to carry mandatory rules "here" inside Non-goals. Current source copies and hashes, the
plan/brief baseline, and Git state are retained in T, the exclusive temporary evidence directory
`decision-to-architecture-t1-zltv4fon` under the operating system's temporary root. This storage
is not durable retention. Existing history is read-only; new evidence goes only into T.

In `.claude/skills/documentation/SKILL.md`, replace only the paragraph beginning "At a repository
root" in **Keep one source of truth for agent instructions** with:

```text
At a repository root, treat `AGENTS.md` as the only source of project-wide AI
guidance. Apply the creation, consolidation, replacement, and validation steps
below only when authorized work creates, edits, or sets up project-wide AI
guidance, including the compatibility updates necessary for that work. In that
scope, ensure `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`
exist without copying the canonical content. The presence of an instruction
file alone does not authorize setup during read-only or unrelated work.
```

The scope qualification governs the whole procedure, including its final validation. Keep
the root-only boundary, canonical authority, exact import and relative symlink, unique-guidance
preservation, conflict handling, and verification requirements unchanged. No compatibility
files are created as a side effect of editing this shared skill.

In `.claude/skills/architecture-records/assets/architecture-record-template.md`, replace only
the two Non-goals bullets with:

```text
- State nearby behavior changes intentionally excluded from this decision.
- In a whole replacement, excluding a behavior change does not exclude its existing rules.
  Carry those rules into the appropriate normative sections, such as Architecture, Failure
  semantics, and Invariants, so this record governs them once implemented. Until then, the
  current record remains in force.
```

This does not prescribe which heading must own every guarantee. The record's actual contract
determines placement; Non-goals excludes changes, not preservation. Whole replacement and
current authority remain as section 7a requires. No architecture skill rule changes.

### T1 sequence and validation

| Status | Step | Evidence and completion boundary |
| --- | --- | --- |
| completed | Record T1 and T2 in this owner and link both decisions from the current brief. | User's explicit recording and execution instruction; no skill implementation before review. |
| completed | Obtain independent readiness review of the concrete candidates and validation. | Sol xhigh returned READY with no findings requiring correction; details under Plan review. |
| completed | Apply the reviewed two-file delta and inspect affected consumers. | Exact reviewed candidate installed in both canonical files; related architecture, plan, and discussion rules need no edit. |
| completed | Validate the packages and perform the semantic walkthrough below. | Four package checks and source/format/link checks passed; eight author scenarios recorded. Extra Git index-byte preservation failed, separately qualified below; no behavioral pass is claimed. |
| completed | Record the author assessment and an independent source-conformance check of T1. | Fresh Sol xhigh returned CONFORMS for T1 with no source correction required. The metadata limitation remains recorded; this is not E2 or whole-plan closure. |

Use the installed skill-creator validator without installing dependencies. Read every scenario
against the complete affected sections, not a keyword-matching test or a fabricated gate that
implements the same prose. Record permitted actions, retained constraints, and why the old
wording failed where applicable:

| Scenario | Required reading result |
| --- | --- |
| Read-only review; root AGENTS exists and compatibility paths are missing | Presence alone does not require creation, consolidation, replacement, or all-path delivery validation. No write is authorized. |
| Unrelated README edit in the same situation | Stay within the requested documentation change; no incidental instruction setup. |
| Authorized project-wide guidance creation, edit, or compatibility setup | All three root paths and their exact topology remain required, including necessary coupled updates and validation. |
| Existing guidance differs between clients | Within authorized setup, inspect all versions, preserve unique guidance, and resolve material conflicts before replacement. |
| Global client, skill package, or scoped subdirectory | Root compatibility topology remains inapplicable there. |
| Whole replacement excludes changing a preserved behavior | Carry its existing rules into appropriate normative sections; no residual old-record authority after implementation. Before implementation the current record still governs. |
| Unchanged guarantee's runtime owner moves | Architecture section 7a and the plan's replacement-before-removal prerequisite remain intact. Template clarification alone is not proof that a model follows that prerequisite. |
| Decision recording, D3/D12 review order, and E2 closure | Their governing texts and obligations remain unchanged; T1 and deferred T2 have no pending recording owner. |

No new live model task is necessary to establish these two source corrections. A new full-flow
run would need its own recorded hypothesis, freeze, and inherited review under D24; the existing
failed attempts and unresolved full-flow requirements remain in the closure matrix. Replan if
review finds a policy choice beyond T1, source drift invalidates the baseline, or another owner
must change. Do not resolve such findings by silently expanding into deferred T2.

### T1 implementation evidence

Both installed files match the exact reviewed candidates in T `review-input.json` and
`candidate.diff`. Four validator invocations passed: documentation and architecture-records,
each through its canonical and exposed path. Changed prose formatting, new relative links and
anchors, file modes, exposed symlinks, and focused `git diff --check` passed. Source hashes confirm
the other skills, global instructions, and preserved brief were not edited by this continuation.
`validation.json` retains every individual result; `implemented.diff` is relative to the
pre-existing working tree, not HEAD, so it separates T1 from earlier uncommitted work.

The eight scenarios passed the author's semantic reading, recorded with their source hashes,
allowed actions, retained constraints, and old-text limitations in `author-walkthrough.json`.
The author finds the installed source faithful to T1; T2 is deferred in its sole owner. This is
source conformance, not automated behavioral evidence or the complete parent-plan author audit.

An extra byte-level check of `.git/index` failed and remains failed in `validation.json`.
Read-only reconciliation found the same HEAD and an empty staged diff. The readiness reviewer
reports ordinary `git status` calls without optional-lock suppression, which can refresh index
metadata; the exact cause is not established because intermediate index copies were not captured.
No index repair or Git mutation command was issued. `git-state-reading.json` records this limit;
do not claim byte-identical Git metadata or overwrite the failed observation with a green result.
The source checks above are distinct from that extra metadata check. The independent conformance
review observed another index-byte change despite optional-lock suppression; HEAD and staged
content were still unchanged. The cause remains unestablished and `validation.json` keeps its
aggregate false result.

**T1 source verdict: conforms.** Fresh reviewer `/root/t1_source_conformance` confirmed the exact
installed candidates, every hash in `postedit-review-input.json`, decision fidelity, retained
consumers/gates, and the limited validation claim. No source correction was required. This
completes T1's source task; the parent plan stays In progress with T2 deferred and its existing
full-flow, complete author-audit, and E2 obligations unresolved.

## Current continuation: skill review and model comparison

This completed continuation is retained as evidence; the T1 execution section above governs
current changes.

The user requests a review of skill quality and complementary evaluation with Terra xhigh,
Sol high or medium, and Opus high or medium. Select high for Sol and Opus within those bounds.
This authorizes review and three bounded comparative runs, not edits to the skills. Preserve
the current five modified files and HEAD `fd12a99ca5f246ac06ce6fd0056d2f05db223ec4`.
Only this plan and its brief change in the repository. Evidence is exclusive temporary storage
under S `post-audit-b1-b3-410811bdf229/live/skill-quality-comparison-01/`.

Review the four central skills and their relevant templates for correct rules, clear triggers,
scope, phase routing, dependencies, contradictory obligations and evidence requirements.
Use skill-creator's concision/progressive-disclosure criteria. Distinguish a demonstrated rule
defect, an ergonomic risk, a model's failure to follow adequate instructions, and a test/author
defect. Cite exact current sources. Do not treat line count or a model miss as proof of cause.

After the inherited independent review, run one fresh extraction task per configuration,
sequentially: `gpt-5.6-terra`/`xhigh`, `gpt-5.6-sol`/`high`, then Opus/high. Codex subjects use
`fork_turns="none"`; Claude uses the already verified interactive route with normal individual
read approvals. Resolve the `opus` alias through a metadata-only bootstrap and record its exact
model ID before the task. An unavailable requested family/effort stops that arm; do not substitute.
Keep the bootstrap task-free. Retain its complete native context and tool catalog.

Use fresh byte/mode-equivalent copies of the same original fixture and the exact previous
extraction prompt, changing only its workspace path. Keep its original semantic rubric 1–5;
generalize rubric 6's model/client identity to the requested configurations and explicitly
account for Codex's inherited client cwd versus the prompt's logical fixture boundary.
The previous Sonnet5/xhigh extraction is a reference observation with identical shared-source
hashes, not a new randomized contemporaneous arm. Keep current-source identification, retained
obligations, validation/transition, lifecycle and instruction/effect compliance separate.

Freeze sources, fixtures, prompts, rubric and existing control evidence before each task. The
three semantic controls and unchanged Claude/Codex reader controls already have recorded
assessments; inspect their applicability rather than rerunning unrelated suites. Subjects may
read only their original task files and applicable shared instructions, with no writes, Git,
fixture-code execution, parent-plan/answer/history reads, helpers or corrective follow-ups.
Preserve every terminal or interrupted result. Source drift holds later arms for assessment.

Audit native identity/context, every call/result, source delivery, final output and inventories.
If Codex encrypts the initial task, retain caller prompt/configuration and ciphertext identity,
but mark native plaintext verification UNVERIFIED; do not claim full launch verification from
configuration alone. Likewise retain mechanical-reader UNVERIFIED separately from author
classification. Unknown mandatory launch/effect evidence prevents complete-task PASS while
the observed answer can still receive its bounded content verdict. Record actual usage/time
and reported cost with their scope and limits, without comparing client timings as model speed.

Stop after these three attempts regardless of outcome. One observation per model/client can
show whether the failure repeats on this case; it cannot establish a model ranking, isolate
skill complexity from client/context differences, validate the full recording workflow, or
close D18/D22/E2. Recommendations are review findings, not authority to modify instructions.

| Status | Step | Evidence |
| --- | --- | --- |
| completed | Independently review this bounded continuation and comparison contract. | Sol xhigh delta review READY; no blocking finding. Frozen plan/rubric/prompts and input equivalence confirmed. |
| completed | Complete the source review and run the three isolated tasks sequentially. | Terra xhigh, Sol high and native claude-opus-5/high completed once each. Frozen input and rubric, terminal traces and per-criterion assessments retained. |
| completed | Synthesize skill defects versus execution failures and verify preservation. | Source findings and comparative results below. All three fixtures, 21 shared sources, 2,646 prior evidence entries and 23 decision paragraphs preserved; links/anchors and diff checks passed. No full-plan closure. |

### Skill source review

Reviewed the four central entrypoints and five relevant templates; checked the coupled loop
routing. This is not an audit of every installed skill. The four entrypoints total 1,529 lines
and 13,634 words. Size is a maintenance/context cost, not evidence of the cause of a model miss.
The independent Sol xhigh reviewer confirmed the first two findings and the adequacy of the
preservation rules. Findings remain recommendations; no skill changed in this continuation.

| Finding | Current source | Assessment and recommended correction |
| --- | --- | --- |
| R1: overbroad compatibility-file trigger | `documentation/SKILL.md`, root guidance compatibility, lines 142–165 versus scope lines 17–36 | The presence of any root instruction file triggers an obligation to create all three compatibility paths, including during unrelated/read-only review. Higher-priority scope still prohibits those writes. Limit mutation to authorized instruction-file work or a demonstrated necessary coupled change; report other missing paths. Confirmed scope defect. |
| R2: preserved rules under Non-goals | `architecture-records/assets/architecture-record-template.md`, lines 17–21 | “Carry unchanged behavior's rules here” can mean the Non-goals section or the entire replacement. Say that changing that behavior is excluded, while preserved rules belong in the appropriate normative sections. Confirmed ambiguity, not a normative contradiction. The earlier extraction Sonnet did not read this template, so it cannot explain that result. |
| R3: phase selection and duplicated rules | `architecture-records/SKILL.md`, lines 427–473; `plan-implementation/SKILL.md`, lines 301–367 and 446–565 | A shared checklist subtracts nine exception categories for planning handoff, and several entrypoints repeat phase/review rules. Prefer explicit phase routing and fewer duplicated normative passages, preserving D11 and all approved gates. Usability risk; no remaining contradiction in the central preservation contract established. |
| R4: excessive history in author documents | This active plan and brief versus `plan-implementation/SKILL.md`, lines 371–375, and `discussion-briefs/SKILL.md`, lines 17–18 and 125–133 | The active documents have accumulated investigation narration despite their current-state purpose. Condense the brief's current summary, retain historical results in the plan/evidence, and consider a separately scoped plan cleanup. Subjects could not read these parent documents; their length does not explain blind test failures. |

The central rules are adequate: architecture section 7a explicitly preserves prose/flow rules,
keeps the current record authoritative until replacement implementation, and distinguishes an
unknown responsible path from an optional guarantee. The plan skill requires locating and
validating the moved path before removal, or a safe atomic transition. A source defect and a
model's failure to follow an adequate instruction can coexist; neither establishes causality
for the other. Detailed source classification is in `source-review.final.json` under the
comparison evidence directory.

### Comparative extraction results

All three fresh attempts completed without coaching, correction or reroll. The earlier
Sonnet5/xhigh extraction is a historical same-source reference. The fixture and semantic rubric
are identical apart from workspace paths and explicit client-specific launch accounting.
All four identified the old offset commit; only the three new attempts explicitly retained
progress as mandatory when its future owner/mechanism is unknown.

| Frozen criterion | Earlier Sonnet 5/xhigh | Terra xhigh | Sol high | Opus 5/high |
| --- | --- | --- | --- | --- |
| 1. Identify the current guarantees | PASS | PASS | PASS | PASS |
| 2. Classify only authorized changes/preserved rules | PASS | PASS | PASS | FAIL: G7 expands the DLQ restriction into a universal ban on replayable storage. |
| 3. Preserve progress despite unknown implementation | FAIL | PASS | PASS | PASS |
| 4. Observable validation and safe transition | FAIL | FAIL | FAIL | FAIL |
| 5. Lifecycle and analysis scope | FAIL: authority ends at recording rather than implementation. | PASS | FAIL: same premature authority boundary in prose. | PASS |
| 6. Launch, required reads and effects | FAIL: documentation skill omitted; no prohibited effects. | UNVERIFIED native plaintext; observed reads/effects comply. | UNVERIFIED native plaintext; observed reads/effects comply. | PASS by complete author audit; mechanical unknowns retained separately. |
| Complete task | FAIL | FAIL | FAIL | FAIL |

Criterion 4 has different depth of failure. Terra and Sol propose progress, own-tenant and DLQ
checks, but do not require locating and validating the moved progress path before removing old
protection. Opus explicitly orders filter validation before removing the consumer check; its
G2 proposes lag/redelivery validation, but does not bind that progress guarantee to the same
pre-removal gate. The frozen rubric explicitly says filtering alone is insufficient. These
misses are not failed identification or lost future obligations in the three new attempts.

Opus G7 says the discard cannot reach *any replayable storage* and presents that as an unchanged
mandatory rule. The source prohibits foreign-tenant records in this DLQ because replay would
target the wrong tenant; it does not authorize the broader universal storage ban. A possible
design recommendation must not be promoted into an approved preserved obligation. No actual
document or code was changed by any subject, so all semantic risks here are prospective.

Native verification: `gpt-5.6-terra`/`xhigh`, `gpt-5.6-sol`/`high`, and
`claude-opus-5`/`high`. Codex subjects were fresh `fork_turns="none"` agents with explicit
fixture command cwd. The client still injected home cwd and global/home instructions; this is
a logical task boundary, not a sandbox. Their initial task bodies are encrypted natively.
Exact frozen caller prompts, configuration and matching parent/child ciphertext are retained,
but plaintext delivery remains UNVERIFIED. Opus had fixture-only cwd, no extra directory,
metadata-only bootstrap, exact task once, normal one-use read approvals, terminal reply and
normal exit 0. No client permission bypass or model-directed helper was used.

| Attempt | Paired calls/results | Full file delivery | Task elapsed | Task output tokens | Mechanical reader |
| --- | --- | --- | --- | --- | --- |
| Terra xhigh | 8/8 | 6, including global instructions and architecture/documentation skills | 146.936 s | 7,145, including 4,728 reported reasoning | 8 PASS / 10 UNVERIFIED |
| Sol high | 11/11 | 8, including global instructions and architecture/documentation skills | 280.075 s | 8,051, including 4,510 reported reasoning | 8 PASS / 24 UNVERIFIED |
| Opus 5/high | 16/16 | 13, including global instructions and all four central skills | 376.347 s | 13,059; task-only thinking unknown | 15 PASS / 129 UNVERIFIED |

All observed calls and paired outputs were individually classified; source slices/content
were matched exactly to files, and all fixture inventories stayed unchanged. Unsupported native
envelopes stay mechanical UNVERIFIED even when the complete author audit resolves their effects.
Claude reported US$1.3813725 for its whole session, including bootstrap and auxiliary Haiku;
this is a client estimate, not a confirmed bill. Its whole-session Opus thinking count was
6,779; do not mistake the capture helper's absent-field default zero for a measured task count.
Codex monetary cost is unknown. Timings include orchestration/approval waits and are not a
model-speed comparison. Native IDs, hashes, usage and complete per-event audits are in each
arm's `result/`; no failed artifact was overwritten.

Conclusion: the source review found a real scope defect and an ambiguous template sentence,
with further ergonomic risks. The preservation contract itself is explicit and was followed
by three different model configurations in this extraction task. This weakens an explanation
based on an unintelligible or absent rule, while neither proving the cause of Sonnet's miss
nor proving full workflow reliability. The other models also made distinct errors. One sample
per model/client cannot rank general capability or isolate the effect of skill complexity.

Recommended next change: narrowly fix R1/R2, then consider phase routing/duplication separately
without adding a scenario-specific exception or weakening existing gates. Any subsequent
experiment needs a defined purpose and reviewed frozen criteria; these three attempts are done.
This review does not authorize those edits, close D18/D22, or replace the final independent E2.

Scoped preservation checks passed: 15 unchanged entries per fixture, all 21 frozen shared
sources unchanged, all 2,646 pre-existing scratchpad entries unchanged, and all 23 original
decision paragraphs identical to the before snapshot and HEAD. Repository changes remain the
same five pre-existing paths; this continuation edits only the plan and brief, with an empty
index. Local Markdown links/anchors and `git diff --check` passed. The source review and bounded
comparison are complete; the parent implementation plan remains in progress.

<a id="current-continuation-guarantee-extraction-diagnostic"></a>

## Completed guarantee-extraction diagnostic

The user instructed `teste` after the recommendation to test explicit extraction before further
writing. Run one fresh read-only Sonnet 5/xhigh session with the current skills unchanged. This
is a new diagnostic purpose under D24: determine whether the model can enumerate and classify
the existing guarantees when that intermediate result is the entire requested output. It is
not another full recording attempt and cannot close D18/D22 or E2.

Baseline: HEAD `fd12a99ca5f246ac06ce6fd0056d2f05db223ec4`, with the five local changes from
the completed procedure-clarity experiment preserved. Only this plan and its brief change in
this continuation; skill files, global instructions, judges and historical outputs stay fixed.
Evidence uses a new exclusive directory under S
`post-audit-b1-b3-410811bdf229/live/guarantee-extraction-01/`. It is temporary storage; retain
the result and limits here. The prior pair and its stop condition remain historical facts.

### Diagnostic contract and boundaries

Use a fresh byte/mode-equivalent copy of `forward-test-d14/control-large-base.original`, outside
Git worktrees. Reuse the verified interactive CLI route and metadata-only bootstrap, with a
fresh session ID and fixture path. Confirm actual model/effort, only-fixture cwd, no extra
directories, complete native capture and normal approval access before sending the task once.
Freeze the actual common sources, original/copy inventories, prompt and diagnostic rubric.
Check their hashes before launch and after completion. Do not alter global settings or bypass
permissions. Client-owned session bookkeeping is distinct from model-directed task writes.

The task asks for a source-grounded table of current guarantees, D1's authorized changes,
remaining obligations, known or unverified future responsibilities, and observable validation.
It explicitly asks to include prose and flow and to distinguish behavior from uncertain
implementation. It does not name progress/ack, offsets, the failed criterion, expected rows,
prior outcomes or the desired verdict. The model can read original task files and applicable
shared instructions only. It may not write files, record the decision, generate the new record
or plan, execute fixture code, run Git, delegate, call another model or inspect withheld evidence.
The prompt differs materially from the realistic recording task; report that scaffolding limit.

The pre-run semantic rubric requires all source guarantees, including discarded-record
progress/ack and both DLQ restrictions, without inventing a future protocol or runtime owner.
D1's check/log/counter changes must be correct; own-tenant forwarding and failure/replay stay
preserved. Unknown implementation does not make the guarantee optional. Proposed validation
must cover the actual behavior, and moved guarantees require locating and validating their
responsible path before removing the old protection, or an explicitly safe atomic transition.
Grouping and paraphrase are accepted by meaning; exact row count or wording is not an oracle.
Score identification/classification (rubric 1–3) separately from validation/transition (rubric 4).
A validation-only miss fails the complete requested table, but does not show failed extraction.

Before launch, read three author-constructed semantic controls: a complete table, the same table
without progress, and the same table treating progress as undecided because its future owner is
unknown. Record why the latter two fail while other semantics remain equal. Use the existing
native capture/effects assessment machinery without changing the historical judge. Evaluate
all tool/results and shell commands; retain unsupported mechanical envelopes as UNVERIFIED
beside the complete hash-bound author classification. Missing mandatory evidence blocks PASS.

Stop after this one diagnostic regardless of result. A pass would establish one successful
explicit extraction; it would not prove that old failures happened only during composition,
that context complexity caused them, or that a later rewrite will preserve the table. A failure
would demonstrate a miss in this narrower task. Neither result authorizes skill changes or a
same-session conversion/correction. Preserve all outputs, costs when known, elapsed time and
usage limits. Terra and final user-opened E2 keep their separate obligations.

### Diagnostic execution steps

| Status | Step | Evidence |
| --- | --- | --- |
| completed | Independent Sol xhigh review of this bounded diagnostic plan, exact prompt and rubric. | READY; separate extraction/classification from validation-path results. No blocking findings. Exact reviewed hashes below. |
| completed | Validate semantic controls and freeze a fresh input/session. | Three author-read controls match expectations; original-equivalent input outside Git; all 21 sources unchanged. Native bootstrap confirms Sonnet5/xhigh, fixture-only cwd and zero tools. |
| completed | Submit the extraction request once and preserve terminal evidence. | Fresh native Sonnet5/xhigh, exact task once, terminal reply and normal exit 0. Nine paired calls; no coaching or corrective follow-up. |
| completed | Assess, record and check the bounded result. | FAIL on preserved-obligation classification and validation, with separate lifecycle/instruction findings. Full effects reading, preservation and local document checks recorded below. Full-plan closure stays pending. |

### Extraction result

**Overall verdict: FAIL.** The smaller task did not reliably preserve the critical obligation.
Current-source identification passed: table row 2 explicitly mentions the old consumer committing
the offset. Future preservation failed: the same row keeps only the destination restrictions,
while offset handling becomes an implementation question without a mandatory progress guarantee.
This distinction matters: the model noticed the source sentence but did not retain its obligation.

| Frozen criterion | Result and evidence in the final reply |
| --- | --- |
| 1. Current guarantees and sources | PASS: rows 1–4 and 6–9 cover the current check, discard, offset commit, log/count, own-tenant forwarding and both DLQ restrictions. Grouped coverage counts; a separate progress row was not required. |
| 2. Approved changes | PASS for the required classification: router ownership, metric name and exact log limit are present; own-tenant and DLQ behavior remain. Unnecessary questions about the input flow and a consumer fallback are additional ambiguities, not adopted architecture decisions. |
| 3. Critical preservation | FAIL: citing the old offset commit and investigating future offset management never establishes mandatory confirmation/progress after discards. No other table row supplies that obligation. |
| 4. Observable validation and transition | FAIL: no confirmation/continued-processing check and no prerequisite locating and validating that path before removing old protection. Rows 6 and 8 explicitly dispense with new validation of the own-tenant path and replayable DLQ. Row 1's statement that there must be no gap is not a validated transition prerequisite. |
| 5. Lifecycle and scope | FAIL on the explanation's lifecycle boundary: it says the old record remains in force until formal recording, instead of until the replacement is implemented. Read-only scope itself passes; no file was superseded and no concrete router implementation was invented. |
| 6. Launch, reads and effects | FAIL on complete applicable-skill loading: it deliberately skipped `documentation`, although the architecture skill's opening and global registry require it. Launch/capture, required task reads and observed read-only effects pass. |

Identification/classification (1–3): **FAIL**, specifically preservation rather than recognition.
Validation/transition (4): **FAIL**. Complete task (1–6): **FAIL**. The missing skill is a separate
instruction failure; this run does not establish that it caused the semantic miss. Likewise,
the lifecycle wording is an explanatory defect, not an observed early status mutation.

Evidence under `live/guarantee-extraction-01/result/` includes the complete native transcript,
post-exit capture, final reply, final fixture, source/inventory checks, per-criterion assessment
and hash-bound author classification of all 86 post-exit events and nine calls/results. The six
Read results reconstruct the complete bytes of the global instructions, fixture instructions,
architecture index, brief, current record and architecture skill. Three shell calls only list
fixture directories. No model-directed write, Git operation, helper, withheld read or fixture
code execution was observed. The first root listing preceded instruction-read completion;
record this order deviation without treating it as the cause of the content miss.

All 21 shared sources, the original-equivalent fixture and 2,573 historical scratchpad entries
remain unchanged. The frozen mechanical reader reports **8 PASS / 0 FAIL / 88 UNVERIFIED**;
its unsupported native envelopes remain unverified mechanically, separate from the complete
author effects classification. Native Git metadata remains unreliable; the actual preflight
confirmed that the fixture was outside a worktree. Normal client permissions are not a sandbox.

Native session: `681ee7f0-23f5-4e2c-877c-c1dba4802597`, Sonnet 5/xhigh throughout the task.
Captured trace SHA-256: `6c78ac6ba17d3a06ba75c8c17a48f82cde7dab1e62798561f200faaf21391c4f`.
Post-exit trace: `3dfb11848c73828c376faa8e922d55cc5824829c777b7dcea392d20cc02e55ef`.
The frozen task was submitted exactly once. It took 210.482 seconds including approval waits
and reported 17,764 task output tokens. Task-only thinking tokens are unknown. Post-exit client
metadata reports 12,681 Sonnet thinking tokens for the session, including bootstrap, and
USD 0.368911 total estimated session cost, including auxiliary Haiku usage. This is client
accounting, not verified billing or a model-directed helper invocation; its auxiliary purpose
is not established. Do not confuse session aggregates with task-only measurements.

The three prelaunch author-constructed controls met their expected semantic outcomes. The
positive table passed; deleting progress or making its obligation undecided failed. No language
judge was automated or changed. Local checks preserve all 23 original decision paragraphs,
links, formatting and the empty index; this continuation changes only the plan and brief.

The attempt ended without a correction, rerun, skill change or conversion into documents.
This shows a miss even with explicit table scaffolding on this input. It does not isolate the
cause of earlier failures, prove skill complexity, or establish model-wide reliability. The
bounded diagnostic is complete; D14/D16/D18/D22, final author closure and independent E2 remain
unresolved. The prior A/B pair and every earlier failure retain their original outcomes.

<a id="current-continuation-procedure-clarity-experiment"></a>

## Completed procedure-clarity experiment

The user accepted the recommendation to try an ordered recording procedure after the
read-only investigation of the interactive Sonnet failure. This authorizes the narrow
usability experiment below, without claiming a missing rule or a proved cause of failure.
It supplements D24's diagnostic purposes: an explicitly requested presentation and
clarification experiment may proceed after independent review even though the existing
whole-replacement and invariant-trace requirements are already correct. No acceptance
criterion, authorization boundary, historical verdict or closure route changes.

Baseline: HEAD `fd12a99ca5f246ac06ce6fd0056d2f05db223ec4`, clean working tree before this
planning update. All 21 common sources still match the last interactive freeze. The four
central skills contain 1,487 lines and 13,255 whitespace-delimited words. Their full contents
reached the failed Sonnet run; no denied or truncated skill read explains its misses. The
model left residual authority in the old record and omitted the plan prerequisite for a
preserved guarantee. Instruction dispersion is a hypothesis, not an established cause.

### Candidate and semantic boundaries

The concrete candidate is retained under S
`post-audit-b1-b3-410811bdf229/live/procedure-clarity-01/`, in `before/`, `candidate/`,
`candidate.diff` and `candidate-manifest.json`; the first reviewed proposal remains in
`candidate-v1/` with its own diff and manifest. These temporary artifacts supplement this
persistent contract; they are not durable retention. The reviewed candidate was applied only
after arm A reached terminal completion and its full output was preserved.

Reorganize `architecture-records` section 7a into four steps: identify the whole contract and
choose the form; check the recording boundary and record; derive the implementation plan;
cross-check before the planning handoff. Preserve the existing form selection, amendment
syntax, whole replacement, D3/D12 order, D4 handoff, current authority and closure paragraphs.
The boundary check moves before the write forms so that the exception is tested before use.

Add only these generic operational clarifications, with no fixture names or expected answers:

- Read guarantees in prose and flow as well as numbered invariants; separate approved changes
  from behavior that must remain true.
- Carry guarantees affected by an ownership/flow change into the plan's responsible path,
  execution step and validation, even when the behavior itself is unchanged. Unknown ownership
  is an investigation prerequisite, not an established implementation fact.
- Before reporting recording complete, read the resulting record and plan together. A whole
  replacement must preserve unchanged guarantees without leaving future authority in the old
  record. The written plan must carry those guarantees through transition prerequisites.
- In `plan-implementation`, beside the execution-contract requirements, make the existing
  invariant/owner/validation trace explicit before removal of a responsibility or protection,
  or within an explicitly atomic transition whose prerequisites and validation rule out gaps.
- In the architecture template's Non-goals, distinguish excluding a behavior change from
  excluding that behavior's rules from the whole replacement, keeping the old record current
  until the replacement is implemented.

This is reorganization plus explicit application of existing rules, not a pure permutation or
a reduction of total context: section 7a grows from 70 to 103 lines. No separate checklist file,
new required user artifact, registry change, global instruction change or package split is
introduced. The four-step path groups related instructions; its usability benefit remains unproved.

| Candidate element | Existing authority whose meaning must be preserved |
| --- | --- |
| Whole-contract reading and carry-over | `architecture-records` 7a already requires every unchanged rule in a whole replacement; sections 2a and 6 trace governing invariants, owners, consumers and protection. Prose does not exempt a guarantee. |
| Plan transition prerequisites | `plan-implementation` execution-contract items 3, 5 and 6 bind invariants, proved material premises and validation; its sequence establishes the authoritative path before removing obsolete paths. |
| Final cross-check | Section 7a already preserves whole authority and delegates planning-handoff checks to section 11. This operationalizes that reading without demanding completed-code evidence at promotion. |
| Non-goals clarification | The template scopes the decision's changes; section 7a requires the new record to replace the old one whole. Unchanged behavior and excluded authority are different. |
| Reordered detail | All existing amendment, purpose-test, D3/D12, handoff, coexistence and closure limits remain normative. No form or status changes early. |

The first independent review found three issues in the proposal, all accepted before any
canonical edit or live run: Step 3 needed an explicit D12 branch that plans and reviews while
the record is unchanged; the transition paragraph must preserve the permitted atomic path;
and the template must express future authority rather than suggesting a Proposed record
already governs current behavior. The candidate now states each distinction explicitly.
The same reviewer confirmed those corrections and the final formatting/closure-row fixes.

### Ordered execution and comparison

| Status | Step | Prerequisite and observable evidence |
| --- | --- | --- |
| completed | Independent read-only plan/candidate review by fresh Sol xhigh. | READY after all three semantic findings and two consistency fixes; exact reviewed hashes under Plan review. Advisor unavailable; no self-review substituted. |
| completed | Freeze and run A with current canonical instructions. | `a-02/result/`: terminal Sonnet 5/xhigh, 27 paired calls, five permitted documents changed, common source hashes unchanged. Record loses progress/ack and calls the current record superseded; plan lacks the progress prerequisite. Complete assessment follows with B. |
| completed | Apply the reviewed candidate and validate it. | Exact three candidate hashes applied after A capture/exit. Four package validations pass through both paths; focused width/diff checks and eleven author B1 scenarios pass. Source delta is exactly the reviewed proposal. |
| completed | Run B and assess both outputs. | Both terminal FAIL. B received the exact reviewed three-source delta and preserved current lifecycle authority, but omitted progress/ack and its plan prerequisite. No coaching, helpers or output repairs. |
| completed | Record results and audit this experiment. | Per-arm assessments, native captures, inventories, source accounting and complete author effects classifications retained. Local package/consumer checks pass; behavioral acceptance fails. This bounded experiment is complete; full-plan author closure and independent E2 remain pending. |

One fresh A/B pair is the bounded initial experiment. A runs even though historical failures
exist because contemporaneous access/client conditions are part of this comparison. B runs
regardless of whether A passes; do not condition its launch on obtaining a failed baseline.
Stop after that pair and report both results. An invalid launch or source drift holds the
dependent comparison for diagnosis; do not silently replace a spent attempt. A failed B stays
failed and does not trigger another wording change or reroll without a new diagnostic purpose.

Use the untouched `forward-test-d14/control-large-base.original` for both fixtures. Preserve
its bytes, modes and absent Git metadata. Reuse the previous interactive task prompt with only
the fixture path changed, the same bootstrap and client flags, and the frozen D18 criteria and
judge. Freeze all actual common sources, candidate files, fixtures, prompts, criteria and judge
before A; B's manifest must name exactly the reviewed intentional source delta. Shared-source
changes outside that delta stop the comparison. Do not restore old global settings or edit the
failed outputs. Source variants remain ephemeral evidence, not second maintained packages.

The frozen criteria judge architecture, owners, future implementation order, CHAT REPLY,
side effects, independence and launch/capture. Reread the existing positive/paraphrase,
partial-authority, missing-record-guarantee and missing-plan-prerequisite controls before
launch; unchanged judge controls need no redundant complete rerun. Re-evaluate all eleven B1
walkthrough scenarios and affected consumers after the candidate, preserving question-only,
third-owner and maintenance fallback boundaries. Validators prove structure only.

Preserve the full native trace, final outputs, inventories, prompt/source hashes, elapsed time
and observed usage for each arm. Inspect every tool/result and shell effect; mechanical
UNVERIFIED stays separate from the hash-bound complete author classification. Unclassified
effects or missing mandatory evidence prevent a pass. Monetary cost is unknown unless actual
billing evidence is available. One pair provides observations, not a success rate or proof that
complexity caused the old failures; fixed A-before-B order and backend variability remain limits.
No new Terra run is part of this comparison, and Sonnet success cannot close Terra's obligation.

### Paired result and author assessment

The pair completed on 2026-09-22: **A FAIL; B FAIL**. Both fresh sessions actually used
`claude-sonnet-5` at `xhigh`, CLI `2.1.268`, the same frozen task apart from fixture paths,
and original-equivalent input bytes/modes. All 21 shared-source hashes held within each arm;
B differed from A only in the three reviewed sources. Both ended normally, with native
`end_turn` and CLI exit 0. Neither output was repaired or rerun.

| Frozen criterion | A: previous instructions | B: reviewed candidate |
| --- | --- | --- |
| Architecture | FAIL: progress/ack absent; repeatedly calls the current record superseded. Routing and both DLQ guarantees preserved. | FAIL: progress/ack absent. Failure semantics explicitly treats offset/retry/restart as undecided instead of preserving the existing progress guarantee. Lifecycle wording and whole DLQ authority are correct. |
| Decision owners | PASS: record and plan written before brief marker removal; both linked. | PASS: same ordering and owner links; no implementation claim. |
| Future implementation order | FAIL: filtering before removal, but no progress/ack responsibility investigation and validation prerequisite. | FAIL: review, location investigation and filtering precede removal; the same progress prerequisite is missing. A conditional replan if offset ownership changes does not guarantee that investigation or validation. |
| CHAT REPLY | PASS: owners, changed places, chosen form and pending review/code are explicit. | PASS: same required information is in CHAT REPLY itself. |
| Observed effects and independence | PASS by complete author classification: 27 paired calls, five permitted documents changed. | PASS by complete author classification: 40 paired calls, five permitted documents changed; all nine mutation payloads replay to the exact final bytes. |
| Launch and capture | PASS with native Git-metadata limitation recorded separately. | PASS with the same limitation. All seven shared instruction/template reads are complete hash matches. |

The frozen mechanical reader separately returned A: 24 PASS, 0 FAIL, 169 UNVERIFIED; B:
31 PASS, 0 FAIL, 241 UNVERIFIED. Native envelope/identity, cwd, terminal and shell coverage
limitations remain UNVERIFIED in those artifacts. The complete hash-bound author reading
accounts for every tool/result, shell command and other event class; it does not relabel the
reader. No code/instruction mutation, helper, withheld-answer read or outside task write was
observed. A received all eight shared instruction/template files it requested in full; B
received all seven it requested in full, including the four central skills in each arm.

B's new record, lines 64–65, calls offset behavior an implementation prerequisite, but the
plan's execution steps 59–62 do not investigate or validate it. Its conditional replan at
78–80 is insufficient: the existing requirement to keep discarded records advancing must
survive even while the future owner/protocol is unresolved. This is the observed semantic
miss. It does not prove whether instruction volume, attention, uncertainty handling or another
model behavior caused it.

Supplementary workflow observations do not introduce new acceptance criteria. Both arms
listed the root before reading its AGENTS and ran read-only Git without loading git-delivery.
B loaded documentation after its main writes. It announced the new cross-check, but the trace
contains no full post-write read of the new record and plan together: only the old record,
brief, a short plan excerpt, index and formatting scans. B's brief retains the old Alimenta
pointer although D1 links the correct new owner. These observations prevent claiming general
procedure compliance merely because the model mentioned section 7a.

Measured task wall time, including human approval waits, was A 552.017 seconds and B 1,118.776
seconds. Native output usage was respectively 27,720 and 43,931 tokens. Native usage omits
thinking-token counts; those are unknown, not measured zero. Monetary cost is unknown. Timing
is not a model-speed comparison because approval delays differ; cached input totals are
repeated traffic, not unique context size.

Evidence is retained under the experiment directory above: `a-02/result/`, `b-02/result/`,
`paired-result.json`, `structural-validation.json`, `b1-walkthrough-current.json`, and the
before/candidate manifests. Both result directories hold the full native trace, final reply,
file snapshot, tool/result lists, source recheck, assessment and author classification.
Transcripts are SHA-256 `f8c4491243f0ea5728d82eebe205e1c5e2366701def6fe261bca57ecc9ea972e`
for A and `9157c1e661945280260a22b7747fea1b2166751d81bd31facc6c90efa8ddaf86` for B.

One unused partial fixture preparation is also preserved. Its overly strict assertion rejected
an empty pre-existing `/tmp/.git` directory; exact Git commands established that neither arm
was in a worktree. No model task ran in that partial fixture. Native `isGitRepo` is consequently
unreliable here; actual command results and inventories establish the absent-worktree premise.

The reviewed candidate remains applied as an assessed experiment, not a validated remedy.
Four package validations through canonical/exposed paths and eleven author B1 scenarios pass;
they do not turn either live failure into a pass. Stop after this pair. No additional wording
change, model reroll or Terra run followed. D14/D16/D18, Terra's separate obligation and final
E2 remain unresolved; no causal benefit, broader reliability or final closure is claimed.

<a id="current-authorization-and-next-validation-batch"></a>

## Prior D24 authorization and completed validation batch

The user's latest instruction authorizes running Sonnet, Terra and other necessary model tests,
as many as needed, and asks for the next concrete step or prompt. It supersedes the previous
single-attempt ceilings and authorizes the execution work needed to establish a current baseline.
This is recorded as D24 and resolves the baseline choice D23 in favor of preserving the current
shared instructions. No additional promotion-only turn is required for this explicit execution
instruction. Earlier decision rows and failed-run evidence remain historical facts.

The user subsequently instructed the author to call Claude in interactive mode. The author
opened the prepared `d24-manual-02` launcher through an interactive terminal, verified native
metadata, and submitted the frozen task. This changes who operates the terminal,
not the reviewed test, sources or criteria. Use the client's normal approval surface only for
the already authorized reads and fixture operations; no permission bypass or global settings
change. Final independent closure retains its separate route.

The global/Docker delta is now committed at `daa4c39fc19ccf43692a88860c55659c674c9b5f`.
Re-read the changed global instructions and inspect the exact delta before freezing this batch.
Do not restore older global files. Treat the earlier Sonnet high run as a distinct baseline and
configuration, never as an equivalent paired run or accepted D18 evidence.

The next batch consists of one fresh Terra xhigh run followed sequentially by one fresh Sonnet 5
xhigh run. Use the existing untouched Terra input and a new Sonnet copy of the original large
fixture. The content criteria under D18 are unchanged. Freeze the actual common instructions,
tested skills, original fixture content, prompts and assessment source before this batch; check
them again before each launch. A change during a batch holds its remaining launches for a
documented impact assessment and a new freeze, without rewriting the old manifest. A later
batch may intentionally use a reviewed correction and its own baseline; identical hashes are
required within a batch, not across every historical attempt.

Terra is launched here with `gpt-5.6-terra`, `xhigh`, and `fork_turns="none"`. The fresh agent's
task scope is its fixture, with absolute edit paths and explicit shell workdirs; inherited
client cwd is recorded separately and is not assumed to be the task directory. Before launch,
the observed Codex capture must support complete native events and exact agent identity. Audit
initial injected context as well as tools; parent-plan or answer exposure invalidates blindness.
This preserves the D22 logical task boundary and does not claim a filesystem sandbox.

Sonnet uses a fresh session in only its fixture directory, with model/effort and full native
capture confirmed. The user-opened route remains available; a verified local CLI route may be
used under the new execution authorization only after its exact flags, directory, permissions,
capture and authentication prerequisites are established. Never change global configuration or
bypass permissions to make it run. A preflight prompt may ask only for session metadata and
directory confirmation, with no task answer, fixture reading or coaching. Keep that bootstrap
in the transcript. All native events and effects require mechanical assessment or a hash-bound
complete author classification; unexplained effects cannot pass.

Further runs require a recorded diagnostic purpose: a new model/effort observation, a corrected
launch/capture defect, or validation after a reviewed source correction. Do not repeat unchanged
inputs merely until a favorable answer appears. Preserve every attempt and report the whole
sequence. Broad execution authorization changes neither pass criteria, Git limits, test-subject
helper prohibitions, nor the requirement for independent closure. A model miss alone does not
justify changing skills; authenticate a contradictory or missing instruction before proposing
such a correction, obtain its inherited review, and rerun invalidated controls before live work.

| Status | Next step | Required evidence |
| --- | --- | --- |
| completed | Independently review this authorization/baseline/launch delta. | Sol xhigh confirmed READY after authority contradictions and missing closure coverage were corrected. |
| completed | Freeze the current batch and launch Terra xhigh. | `live/d24-batch-01/`; Terra terminal FAIL, source freeze preserved. |
| completed | Assess Terra and prepare or launch Sonnet xhigh. | Both terminal outputs preserved. Terra FAIL; Sonnet CLI setup invalid because required global Read was denied. |
| completed | Complete and assess the interactive Sonnet attempt opened at the user's instruction. | E3 resolved. Valid Sonnet 5/xhigh launch and all four central skills read; content FAIL for partial replacement authority and missing plan prerequisite for progress/ack validation. `live/d24-manual-02/sonnet-result/` retains the complete assessment. |
| pending | Address demonstrated gaps and run further useful validation under D24. | Recorded hypothesis or reviewed correction, fresh fixtures, stable criteria and preserved failures. |
| pending | Complete author audit and obtain independent closure. | All applicable obligations resolved; reviewer independent of author and test subjects. |

The older D18/D22 descriptions below retain the original experiment and its results. Their
single-run/no-retry limits and all-history identical-source requirement are superseded only by
this section. Other boundaries and semantic acceptance criteria continue to apply. The earlier
Sonnet failure remains failed; D20.2 still excludes large-4 from closure. The final independent
closure route remains the user-opened fresh review session until explicitly changed.

**Mode:** Plan and execute. The user instructed completion after D21's independent confirmation,
authorizing resumption of the reviewed corrective implementation. That earlier execution started at HEAD
`1b79808801bb48641608aa8aecc7948913a35c69`, with a clean working tree; the previously reviewed
documents and existing skill changes are now committed. Git stays read-only in this session.
D18 originally authorized one conditional large-case run in a fresh user-opened session; D22
added one complementary Terra run. D24 now governs further execution, replacing those ceilings
and conditionally allowing local Sonnet launch. Independent closure retains its separate route.

The second closure audit failed at HEAD `50531033fdb16ef7f2c4362413c768a3a2143a09`, with four
modified in-scope files. The actual auditor was `gpt-6-astra` at `xhigh`, not the planned Sol.
That session now takes over authorship from Claude and cannot independently review its own
changes or conduct the next second pass. B1 and B2 corrections and local checks are complete. B3
remains open for the new live evidence
and independent closure. N1, N2, and N3 are
corrected in this planning continuation. The plan stays in `active/`. The Sol review received
under D19 found the replan not ready for implementation. D21 identified plan defects and residual
gaps, all corrected below, and its final verdict is **ready for implementation**. Resumption is
now authorized; the recorded execution prerequisites still apply. All taken decisions have reached
their
recording owner. The Sonnet attempt has ended with a failed assessment, at high rather than the
frozen xhigh setting and without the required fixture-only launch. That attempt remains failed.
The reviewed D24 batch has finished: Terra xhigh failed and Sonnet xhigh's CLI setup denied
the required global instruction read. Both outputs are preserved; the latter is not valid
shared-skill evidence. D23's current-source choice is resolved and its freeze held. The brief
resolves E3 through the completed interactive attempt, which also failed content criteria, and
tracks E2 for later independent closure. No decision
awaits recording. This plan remains active.
Under D20.2, large-4 remains history and
cannot close
D16. Earlier runs and logs do not prove that the reopened implementation gates passed.

## Outcome

The shared skills `discussion-briefs`, `architecture-records`, and `plan-implementation` define,
without contradicting each other, how a decision the user takes in a discussion brief reaches an
approved architecture record: who records it, in what order, how the record shows a rule that the
code does not follow yet, and how nobody is left believing a decision is recorded when its owner has
not received it. The work ends when every obligation in the closure audit is verified, the touched
packages validate, the two D6 runs are recorded per criterion with their limits, each of the three
D14 cases has met its pass criteria in an accepted run, and the high-risk closure audit has passed,
subject to the evidence disposition now recorded under D20.2:
the old D16 run cannot discharge that obligation. The D18 attempt failed; assess the new evidence
authorized by D24 against the unchanged criteria. These terminal conditions are not currently met. The reviewed corrections and B2
sensitivity are complete; the new live evidence and closure
remain outstanding. If the new run is
insufficient, keep the obligation unresolved. Further diagnostic runs follow D24 and never weaken criteria.

The recorded D22 authorization adds a separate assessment obligation for the same behavior in
Codex. Its preparation and runs under D24 remain conditional on review and the prerequisites below;
they hold neither B1/B2 nor D18. Its result cannot turn a failed Sonnet/D18 result into a pass.

## Scope

### In scope

- `.claude/skills/discussion-briefs/SKILL.md` and its template (D1, D5, D8, D9, and the D16
  sentence).
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
- Existing forward-test artifacts under the session scratchpad (D6, D14, D15, and D16), and the
  planned B2 builder/control correction and read-only rejudging. Preserve every old result,
  original, snapshot, transcript, and log; use new names for all new evidence. Rejudging launches
  no agent. Preserve the failed D18 attempt; new model runs follow D24 and its prerequisites.
- The B1/B2/B3 material replan and N1/N2/N3 evidence corrections requested after the second audit.
  Review is complete and the user's completion instruction resumes the corrective implementation.
- The D21 independent review by a fresh Sol xhigh subagent, explicitly requested by the user.
  This replaces the manual-session route for D21 only; it authorizes no test agent or nested
  delegation by the reviewer and does not change the later closure-review route.
- The D22-authorized Terra `xhigh` preparation and Codex transcript assessment, extended by D24
  to purposeful additional tests. Preparation and controls are complete; the original Sonnet
  is terminal. D23/D24 select current instructions for a newly reviewed and frozen batch.
  Terra and Sonnet remain separately assessed; one cannot erase the other's failure.
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
| D13 | The checks that `architecture-records` lists before a handoff apply at two different moments, and the skill says so in one sentence at the start of that list. When the session that conducted the discussion hands the amended record and the plan to an implementing session, only the checks about the form of the records and of the delivery apply: one explicit lifecycle status, an index that links every current record, proposed behavior not described as implemented, the form of every amendment block, no diary residue anywhere in a record, valid links, no manual table of contents, the Markdown and whitespace checks with the inspection of untracked files and diffs, the report of what changed, and the Git authorization limit. When the implementation closes, every check of the list applies, as it does today: the ones above again, and the checks about a finished implementation, which are traceability to the runtime owner with executable protection, recorded replay, no obsolete path competing with the current authority, consistent terminal states, an implemented record that describes the approved resulting architecture, the plan reread with a closure-audit matrix without pending rows, the traces in both directions, the second conformance pass, and the removal of every amendment block and replacement notice whose implementation closed. The sentence names the checks that wait for the closure, so that a check it does not name applies at both moments and is never skipped. No check is waived. |
| D14 | The user authorizes three new forward-test runs, one for each path: the small-change case again, clean; the large variant of D2; and the D12 fallback, with a record written in Portuguese. D13 enters the skill before the runs. When a run fails because of a skill defect, the defect is corrected and the run of that case starts over. |
| D15 | The user authorizes one more run of the large case, because the second one called the advisor that the prompt forbade. The prompt states that prohibition in the stronger form that the fallback run obeyed. The fixture, the judge, and the pass criteria stay as they are before the run; a judge defect that the run exposes is corrected under the rule in its step. When this run calls the advisor again, no further run is made: the evidence of the large case is then the files of the second run as they were before its advisor call, the reply of the first run, and the deviation recorded as such. |
| D16 | `discussion-briefs` gains one sentence, in the paragraph of its promotion section about a decision that changes an approved architecture record, telling the agent to put in the chat reply the list of places the decision changes and the form chosen, which `architecture-records` requires. The user then authorizes one more run of the large case, a single one. When the list still does not appear in the reply, no further run is made: the miss is recorded as a limit, and D10 stays verified by inspection of the text and only in part by the runs. The sentence stays in the skill in either case, because it only points at a rule that `architecture-records` already has; the run tests whether a weaker model follows the rule, not whether the rule is right. |
| D17 | Option 3: defer the choice about accepting large-4 as closure evidence until the Sol report in D19 arrives. This was neither acceptance nor rejection. The report has arrived, and D20 resolves the deferred choice. |
| D18 | Do: authorize one additional large-case run in an independent session opened by the user, only after review and approved corrections. Record the model, request, criteria, and limits beforehand. The test agent must not call an advisor or spawn subagents; no automatic repetition or runs of other cases are authorized. This is conditional authorization, not execution in the promotion turn. |
| D20 | Option 2: do not use large-4 as evidence to close the D16 obligation. Preserve its files and observations as history and evaluate evidence from the new D18 run when eligible. If that run is insufficient, the obligation remains open, with no automatic repetition or weakening of the criterion. |
| D21 | Follow the recommendation to obtain independent confirmation of the corrected plan and test design before preparing Sonnet. The user subsequently instructed recording and review here through a fresh `gpt-5.6-sol` `xhigh` subagent, replacing the earlier user-opened route for this review only. The reviewer reads and reports, inherits no conversation, edits nothing, runs no tests, and delegates nothing. A decision to review is not a favorable verdict. |
| D22 | Do: authorize Codex transcript-assessment preparation and one additional large-case attempt using `gpt-5.6-terra` at `xhigh`, launched by the author with fresh context after Sonnet reaches a terminal result, independent confirmation, approved corrections, and passing controls. No advisor, agents inside the test, automatic retry, model substitution, or other cases. This recorded authorization does not execute the preparation or run in the current review-only continuation. |
| D23 | Resolved by D24: preserve the current shared instructions and create a new documented baseline; do not restore the older global/Docker files or recast the earlier Sonnet high attempt as equivalent evidence. |
| D24 | Execute necessary Sonnet, Terra and other model tests without the former one-attempt ceiling. Start with a fresh Terra xhigh and Sonnet 5 xhigh batch, freeze sources and criteria, preserve every result, and permit further runs only for a recorded diagnostic purpose. Local Sonnet CLI launch is conditional on verified isolation, permissions, identity and complete capture. Criteria, Git/helper limits and independent closure remain unchanged. |

D19 is a resolved external dependency, not a design choice: the user supplied the independent
`gpt-5.6-sol` `xhigh` report, whose verdict is **not ready for implementation**. Its receipt,
findings, and the subsequent D21 confirmation are recorded under **Plan review**. D11 makes
this plan the only recording owner of D17, D18, D20, D21, D22, D23, and D24; no architecture record is
created.

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
- D13: changing only the wording of D4 so that it avoids the word handoff.
- D14: accepting the first two runs with their limits recorded, repeating the small case twice, and
  strengthening the skill for the fixture's sake before repeating it.
- D15: accepting the evidence of the large case as it stood, the files of one run and the reply of
  another, without a new run. It stays as the fallback that D15 itself names.
- D16: accepting the missing list as a limit, with no skill change and no new run. It stays as the
  fallback that D16 itself names.
- D5, D6, and D9 were answers of do, do not, or defer; the user chose to do each one.
- D17 postponed both immediate acceptance and immediate rejection until the review arrived.
- D18: refusing or postponing the single conditional run; the user chose to authorize it.
- D20: accepting large-4 as limited evidence of promotion, record form, and the list in the reply.
  The user chose history-only treatment for the D16 closure obligation instead.
- D21: the earlier user-opened confirmation route is superseded by the explicitly requested
  fresh Sol xhigh subagent for this review. The author does not replace the independent reviewer.
- D22: refusing or deferring the complementary Terra preparation and single run; the user chose
  to authorize them with the stated prerequisites and limits.

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

### Verified baseline before implementation

The following bullets describe the inspected starting point before this plan's implementation,
not the current skills. Current behavior, remaining defects, and evidence limits are in the
closure matrix and **Material replan after the second failed closure audit**. Section 7a now
exists and the per-phase check now names every owner; B1 concerns its exemptions.


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
  subagent run and a metadata file that names the run. Observed in the `subagents/` directory of
  the local Claude history of session `cd2d99b0-822e-459d-b128-52d36f0cebbc`: the file
  `agent-a3d9c0e4659886a45.jsonl`, which its metadata file describes as "Forward-test case A",
  holds the tool-call entries of that run. This is an observation about earlier runs; every D6 run
  must supply its own transcript.

### Open assumptions

- The account of the other conversation, in which a decision was recorded only in the plan and the
  brief was concluded, comes from text the user pasted. It motivates the change but was not
  inspected. No step depends on it.
- The D6 forward-test covers only the small-change variant, so it does not exercise the D10 judgment
  between the two forms. The large case of D14, with its reruns under D15 and D16, exercised that
  judgment afterwards; the parts of D10 that no run reaches stay verified by inspection.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Advisor review and fresh-context independent review of the first version of this plan. | High risk: review order and closure gates change. | Not ready; findings under **Plan review**; plan revised. |
| completed | Carry the user's decisions on brief items D10 and D11 into this plan, on the user's recording instruction. | Both needed a user decision. | Decision rows, scope, evidence, steps, and closure rows updated; brief items linked. |
| completed | Second fresh-context independent review, of the revised plan. | A material replan inherits the high-risk review. | Ready after the blocking findings are fixed; four blocking and four non-blocking findings applied. |
| completed | Advisor review of the corrected plan. | A material replan inherits the advisor review too. | Three findings applied; see **Plan review**. |
| completed | Carry the user's decision on brief item D12 into this plan, on the user's recording instruction. | The D3 fallback needed a user decision. | Decision row, D3 bounds, the `plan-implementation` step, and the closure rows updated; brief item linked. |
| completed | Third fresh-context independent review, of the corrected plan. | A material replan inherits both high-risk reviews. | Ready after the blocking findings are fixed; three blocking and three non-blocking findings applied. |
| completed | Advisor review of the corrections made after the third review, and a confirmation from the third reviewer's session that its findings are resolved. | The corrections change no decision and no step order, and widen the scope only by editorial corrections of the brief, so a delta confirmation is proportionate. | All six findings resolved; no new blocking finding; verdict ready to execute. |
| completed | Authenticate the current text: reread the three skills in full and confirm each passage under **Verified evidence**. | None. | The three skills were reread in full and every cited passage was found as described. |
| completed | B1 compatibility recheck completed; the original analysis follows. Consumer analysis before any edit: `codex-claude-loop`, including whether the D4 amendment is planner work under its rule that the planner does not edit the implementation; `documentation`, `implementation-plans/README.md`, and the opening statement of `plan-implementation`, for the D11 exception; the full and compact plan templates, the architecture record and index templates, the brief template, and the registry entries and frontmatter descriptions. | Compatibility is decided before dependent text is written. | Read in full and decided. Changes: `codex-claude-loop` gains one sentence saying that the planner amends the record during planning and that this is not the implementation the implementer owns; the opening of `plan-implementation`, `documentation`, and `implementation-plans/README.md` each gain one clause pointing at the D11 exclusion; both plan templates gain a brief-check line for D7; the architecture index template gains the rule that an implemented record stays in force until its replacement is implemented; the brief template changes under D8 and D9. Unchanged: the architecture record template, because the amendment block belongs to existing implemented records and a new record has none; the descriptions of `plan-implementation` and `discussion-briefs`. Corrected after the advisor's check of the edits: the description of `architecture-records` and its registry entry in `.codex/AGENTS.md` gained the recording of a deliberate user decision, because without it the new procedure was reachable only through the pointer in `discussion-briefs`. No contradiction found. |
| completed | `architecture-records`: add the procedure for a deliberate decision (D2 with the D10 criterion and its two examples, and the record side of D3 and D4), the authority rule while both texts coexist, the removal of the block or notice in the closure pass and the validation list, and the D11 sentence. Qualify the lifecycle sentence that forbids two concurrently authoritative records, so that it agrees with the coexistence rule: no two texts authoritative for the same scope and phase. | The examples are generic, with no project-specific names, as `documentation` requires. The incident criterion stays as it is. | Validator passes; the new text contradicts no existing gate of the skill. |
| completed | Reviewed B1 wording implemented and checked; `plan-implementation`: state the D3 exception with its bounds, the D4 owner of the amendment, the D7 closure check in both the proportional-closure section and the completion gates, covering compact plans, and change the per-phase brief check so that a phase waits until every recording owner named for the decision carries it, with the owner definition above and the D12 exemption exactly as delimited under the invariants: only the promotion unit, only the pending marker it resolves, the recording instruction still required. State the D12 fallback beside the D3 bounds, with its two examples. | D3 is a bounded exception, not a reclassification of record edits in general. | Validator passes; the executable sequence, the per-phase check, and the closure sections agree. |
| completed | `discussion-briefs`: D1, D5, D8, and D9 in `SKILL.md` and the template. Each new rule in the three skills carries its reason in a sentence (D11). | D5 points at text that exists after the two steps above. | Validator passes on the package and its symlink. |
| pending | Reopened validation after B1/B2/B3; earlier results below are historical. Validate the whole change: validators, width scan, `git diff --check`, and a cross-skill reread for contradictions. | The validator checks structure only, never decisions or gates. | Every touched package passed the validator, the width scan and `git diff --check` were clean, and the changed passages of the five skills were reread together; the reread found and fixed four wording problems, among them a closure condition that was not in D7 and a dangling reference in the per-phase exemption. |
| completed | D6 forward-test, small-change variant, two sequential runs. Pass criteria: A fresh fixture per run; the prompt withholds the expected outcome. A run passes only when all hold. Record: a comparison of the whole record before and after shows exactly one added block and no other change; the block sits directly under the right rule, carries the "Approved amendment, in implementation" label, states the user's decision, says that the rule above is still in force, and contains no date, plan link, or progress note; the old record is not superseded. Plan and brief: the plan carries the sequence; the brief item links to both owners and keeps no pending marker. Reply: it names where each decision was recorded and says that the decision is approved while the plan review is still to come. Side effects: the before and after snapshots show no other file, no code, and no Git state changed, and the stored transcript of the run shows no edit outside the three documents and no state-changing Git command, including one that was later undone. Any miss fails the run. When the transcript is unavailable, the absence of prohibited operations is recorded as unverified and the run does not count as a pass. Before the runs, judge hand-made defective results with the same criteria and confirm that each fails: only the plan received the decision; the block has no label; the block carries a date or a plan link; a second block sits under the same rule; another rule of the record was altered. These add no agent run. | A weaker model follows the new text. The client stores a transcript of each subagent run in its local session history. | Both runs met the record, brief, reply, and side-effect criteria, with two limits that the first second pass found and that the closure row for D6 describes: the first run called its advisor against the instruction to work alone, and the second run wrote the review-before-code order only in its reply. They are therefore not recorded as full passes, and D14 is the validation the user chose for those limits. Each used a fresh fixture, a Sonnet subagent, and a prompt that withheld the expected outcome. In both, the only change to the record was one labelled block under rule 3 saying that the rule stays in force; the plan's step received the user's decision; the brief item linked both owners; the reply said that the decision was recorded and that the plan review comes before any code; the snapshots, including the Git directory, showed nothing else changed; and the stored transcripts `agent-a3f534d738622cea6.jsonl` and `agent-a206a78a8920dd435.jsonl`, in the `subagents/` directory of the local history of session `cd2d99b0-822e-459d-b128-52d36f0cebbc`, showed edits to the three documents only and no state-changing Git command. Before the runs, a hand-made correct result passed the same judge and each of the five hand-made defective results failed it. Observations outside the criteria: both runs loaded `architecture-records`; the first reply showed the list of touched places with the chosen form, and the second named only the rule it changed. |
| completed | First independent second pass of the closure. | The closure of a high-risk plan needs a fresh-context second pass. | Failed; findings and corrections under **Final conformance verdict**. |
| completed | Carry the user's decisions on brief items D13 and D14 into this plan, on the user's recording instruction. | Both needed a user decision. | Decision rows, rejected alternatives, scope, the steps below, and the closure rows updated; brief items linked. |
| completed | Advisor review of this replan before its steps run. | A material replan of a high-risk plan inherits both plan reviews. The repeated second pass is a closure audit and does not replace either. | Five findings applied; see **Plan review**. |
| completed | Fresh-context independent review of this replan before its steps run. | The same inheritance: the D13 sentence changes a list of delivery gates, and the three D14 cases are new test designs. | Ready after corrections; three blocking and three non-blocking findings, all applied; see **Plan review**. |
| completed | Advisor review of those corrections, and a confirmation from the reviewer's session that its findings are resolved. | The corrections bring the plan back to what the user decided in the brief; they change no decision and no step order. | Advisor review done, four findings applied. The reviewer's session confirmed its six findings resolved and gave the verdict "ready to execute", with one non-blocking wording finding in the brief, applied. See **Plan review**. |
| completed | `architecture-records`: add the D13 sentence at the start of the validation list in section 11, naming which checks apply at the planning handoff and which at the closure of the implementation. The sentence uses exactly those two phrases and names the checks that wait for the closure, as the D13 row lists them, and section 7a changes "before handing the work to another session" to name the planning handoff, so that the two sections read as one rule. | Every check applies at the closure, as today; the checks about form and delivery apply at the planning handoff too; a check that the sentence does not name applies at both moments. The amendment bullet splits: the form of a block applies at both moments, and the removal of a closed block or notice at the closure. | Done on the user's instruction to apply. The validator passes on the package and its symlink; the width scan found only a line inside a code block that was already there, and `git diff --check` is clean. Each of the seventeen bullets of section 11 was checked against the D13 row: the sentence names the nine checks that wait for the closure, the amendment bullet splits as the premise says, and the other bullets apply at both moments. Section 7a now names the planning handoff and points at section 11. |
| completed | B2 correction and new controls completed; old artifacts preserved. Original step: build one fresh fixture and one judge for each D14 case, and judge hand-made results first. | The judges of the first D6 runs had holes: they accepted any plan change and ignored server-side tool calls. | For each case, a hand-made correct result passes and each hand-made defective result fails. Defective results: for the small case, the five of D6 plus a plan without the decided step; for the large case, the old record marked superseded at once, the old record edited beyond its one notice line, a missing index entry, an amendment block used instead of a new record, a new record with the right labels and links that still states the old rule, a new record that dropped the rules the decision does not change, and a plan that did not receive the decision; for the fallback case, the record translated, the index translated, an English block added to the untranslated record, a new record created instead, the pending marker removed, the brief concluded, and a plan without the translation and amendment steps. The plan of every fixture already has its review step before any code step. The large-case record has a flow section besides its numbered rules and names the owner of one check, so that the decision can change all three and the list of touched places can include them. In the fallback fixture the record and its index are both written in Portuguese. Every judge reads server-side tool calls, and the fallback judge requires a byte-identical record and no new file under `architecture/`. Result: `build_d14.py` and `judge_d14.py` in the session scratchpad build the three fixtures and judge them; for each case the hand-made correct result passed and the log `controls-d14.log` reports every designated defective result as FAIL. The claim that all twenty-one failed for the intended defect was wrong for large-6: its Decision paragraph preserves both supposedly dropped rules. B2 reopens this evidence. The reply of a run is judged by reading, outside the judge. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. |
| completed | `architecture-records`, section 7a, new-record form: say that the new record replaces the old one whole, carries over every rule the decision does not change, and leaves no part of the old record governing after the replacement, with the reason. | A skill defect found by the first large run, corrected under D14. It changes no decision: D2 already marks the old record `Superseded` as a whole when the new one is implemented. The small run preceded this sentence, which sits in the form that the small case does not use. | Validator passes; the width scan and `git diff --check` are clean; the second large run, before its advisor call, wrote a whole replacement. |
| completed | Historical evidence reassessed under B2 without a new agent; D18 is a separate conditional authorization. Original step: three sequential D14 runs with a Sonnet subagent, a prompt that withholds the expected outcome and forbids subagents, reviewers, and the advisor tool. | Each run used the skills available then, with D13. The small run preceded the whole-replacement sentence; the small and fallback runs preceded D16. Only large-4 ran after D16. | All cases: only the expected documents change; code and the Git directory are unchanged; the stored transcript shows no edit outside those documents, no state-changing Git command, and no advisor, reviewer, or subagent call; any miss fails the run, and a missing transcript means no pass. Small case, in a fixture whose plan already has its review step: the D6 record and brief criteria; the plan's step states what the user decided, and the plan's review step still comes before any code step; the reply names both owners, shows the list of places the decision changes with the form chosen, and says that the plan review comes before code. Large case, a decision that changes several rules, the flow section, and the owner of a check: a new record in `Proposed` says which record it will supersede and states the user's decision correctly in its rules, its flow section, and the owner of the check: every rule the decision changes is in the new wording, none of them keeps the old text, and every rule the decision does not change is carried over; the index gains its entry; the old record gains exactly one notice line, which links the new record and says that the old record stays in force, and is otherwise unchanged, still `Implemented`; no record is marked superseded; the plan's step states what the user decided, and its review step still comes before any code step; the reply shows the list of places the decision changes and the form chosen, and separates the recorded decision from the implementation; the brief item links the new record and the plan and keeps no pending marker. Fallback case, a record and an index written in Portuguese: every file under `architecture/` is byte-identical and no new record exists; the plan gains, after its review step, the translation of the record and of its index and then the amendment; the brief item links the plan and keeps `registro pendente` for the record with the reason; the brief is not concluded; the reply says that the exception does not apply, why, and what was left out. Results judged per criterion, mechanical and by reading, and recorded that way. Results, with the judge logs `run-*.judge.log` and `controls-d14.log` in the session scratchpad and the transcripts `agent-<id>.jsonl` in the `subagents/` directory of the local history of session `cd2d99b0-822e-459d-b128-52d36f0cebbc`. **Small case, run `a8e7ec69d5c6c3d77`: passed.** Every mechanical check passed, the transcript shows no advisor, reviewer, or subagent, and by reading the block states the decision, the plan's code step received it behind the review step, and the reply names both owners and says that the plan review comes before code. Limit: the reply names the one place the decision changes, rule 3, and the form, a block, as where the block went; it gives no reason for choosing the block. **Large case, first run `a7ddbb635e12f9b6a`: failed by reading, on an invariant that the case criteria did not list.** The historical assessment reported that the then-observed criteria were met, including carried-over rules; progress/ack was not assessed, so this is not full semantic conformance. The reading found that it broke the invariant of this plan that no two texts are authoritative for the same scope and phase: the new record called itself a replacement for the tenant-check ownership only and said that the DLQ rules stay governed by the old record, while also copying them, so after the supersession two texts, or none, would govern those rules. The skill stated that invariant only for the closure, where the old record becomes `Superseded` as a whole, and not for the `Proposed` record, which is a skill defect under D14. It was corrected in the step above, the criterion "the new record replaces the old record whole" was added with its check and its defective result so that the rerun would be judged on it, and the case started over. **Large case, second run `a18d5f5051c2d2c48`: the historical assessment identified the prohibited advisor call as a failing criterion, not a skill defect; progress/ack was not assessed.** After finishing its edits the agent called its advisor, which the prompt forbade, and then made five more edits. The files as they were before that call were rebuilt from the Write and Edit calls stored in the transcript (`replay_until_advisor.py`, result in `run-large-2.before-advisor`): they pass every file check, and by reading the new record says that it supersedes the old record when implemented, carries over the two unchanged rules, states the decision in its flow and rules with the router as owner of the check, and the old record gained one notice, written as two sentences wrapped over three lines, which is how "one notice line" was judged. Observation: that record added "grouped by source tenant" to the counter rule, which the decision does not say. The final reply came after the advisor call, so the reply criteria are evidenced without an advisor only by the first large run, whose reply shows the list of places, the form with its reason, and the recorded decision apart from the implementation. D14 provides no new run for this kind of miss, so the user decided it in brief item D15: one more run, in the steps below. **Fallback case, run `af41bdfd333cddd18`: passed.** The prompt of this run repeated the advisor prohibition in a separate, stronger line, after the second large run. Every file under `architecture/` is byte-identical, the plan gained one step after its review step that translates the record and its index entry and then adds the amendment, and the code step follows it; the brief item links the plan, keeps `registro pendente` for the record with the reason, and the brief is not concluded. Limit: that plan step names "its index entry" and not the whole index, whose heading is also in Portuguese; judged as met, because the step covers the index and the plan review of that plan would settle its extent; the reply says that the exception does not apply, why, and what was left out; the transcript shows no advisor, reviewer, or subagent. **Judge changes, each for a reason independent of the result it affected; no pass criterion changed, and every hand-made result was judged again after each change, ending with three designated correct results reported PASS and twenty-one designated defective results reported FAIL. B2 establishes that large-6 was not semantically defective, so the claimed sensitivity was wrong for that control.** After the small run: the Git pattern flagged the read-only `git branch -a`; corrected and tried on fourteen command shapes; the hand-made results carry no transcript, so this change does not touch them. After the first large run: the flow check tested the heading name `Flow`, while the skill's record template names that section `Architecture`; it now tests that a router step precedes the consumer step; the check and the defective result for a partial replacement, described above, were added before the second large run. Before the fallback run: the plan-link check accepts an anchor, which the small run had shown, and the decision text is read up to the next bold label. After the fallback run: the pending marker was wrapped across two lines, so the decision text is now compared with whitespace normalized, in every case; and the code step was being excluded because it mentions the amendment, so a code step is now any step naming `consumer.py`. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. |
| completed | Carry the user's decision on brief item D15 into this plan, on the user's recording instruction. | It needed a user decision, because D14 provides a new run only for a skill defect. | Decision row, rejected alternative, the step below, and the closure rows updated; brief item linked. |
| completed | Advisor review of this addition before its step runs. | The addition repeats a reviewed test with the same fixture, judge, and criteria, and changes no skill text, gate, or decision; it is not treated as a material replan, so no new independent plan review is opened. | See **Plan review**. |
| completed | D15: one more run of the large case, in a fresh fixture, with a Sonnet subagent. The prompt is the first user message of transcript `af41bdfd333cddd18`, the fallback run, with only the workspace path changed; it states the advisor prohibition in the stronger form. `judge_d14.py` and `build_d14.py` are not edited between the recording of this step and the run. A judge defect that the run itself exposes is corrected only with its reason recorded, as in the D14 runs, and with every hand-made result judged again. | The stronger wording was obeyed once, in the fallback run; that is no guarantee. | Every criterion of the large case in the runs step above, the whole-replacement criterion included, judged mechanically and by reading. When the run calls the advisor again, the fallback that D15 names applies and is recorded as such. Result, run `a3c28b56579d88953`, judge log `run-large-3.judge.log`: **the run did not call the advisor; the historical reading identified one failure.** The prompt was the stored one with only the path changed (`run-large-3.prompt.txt`). Every mechanical check passed, the transcript checks included. By reading: the new record says that it supersedes the old record once implemented, carries over rules 1 and 2 word for word, states the decision in its flow, its rules, and the owner of the check, and leaves no part of the old record governing; the old record stays `Implemented` with one notice; the index has the entry; the plan's code step states the decision behind the review step; the brief item links both owners and keeps no marker; the reply names both owners and separates the recorded decision from the implementation. The miss identified then: the chat reply names the form, a new record, but does not show the list of places the decision changes; that list appears only in the session notes, which the user would not see. Across the runs that made a recording without an advisor, the list with the form appeared in the reply of the first large run, as the single place with the form in the small run, and not in this one. The instruction to show it is in `architecture-records` section 7a, while the reply is composed under `discussion-briefs`, whose list of what the chat message gives does not mention it. Whether that is a defect to correct, and in which skill, is a choice with a duplication trade-off, so it went to the user as brief item D16 and no skill was changed in this step; the steps below carry out what the user decided. One judge change, under the freeze rule of this step, with the hashes of the judge before the run and after the correction in `d15-freeze.sha256` and `d15-after-run.sha256`: the run wrote its notice as a continuation of the status line of the old record, which is what the skill says, "add one notice line to the status", while the judge accepted only a separate inserted line. The judge now also accepts a status line kept whole and continued by the notice. Every hand-made result was judged again. The logs report three designated correct results as PASS and twenty-one designated defective results as FAIL, including the record superseded at once, which also replaces the status line. B2 invalidates the interpretation of large-6 as an intended-defect failure; every run was judged again with unchanged verdicts. `build_d14.py` is unchanged. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. |
| completed | Carry the user's decision on brief item D16 into this plan, on the user's recording instruction. | It needed a user decision: the correction is a choice between two skills with a duplication trade-off, and D15 provides no further run. | Decision row, rejected alternative, scope, the steps below, and the closure rows updated; brief item linked. |
| completed | Independently review the current D16 sentence and corrective replan while retaining the original missing-review deviation. | B3 rejected the non-material classification. A later review cannot restore the historical order retrospectively. | D19 examined the sentence and replan with an adverse verdict; D21 confirmed the corrected design. This satisfies review before future corrective implementation, not the missing original review or B3's validation obligations. D20.2 still governs evidence use. |
| completed | Existing D16 sentence reviewed under D21 and retained through B1; Original step: `discussion-briefs`: add the D16 sentence to the paragraph of **Record decisions and promote them** that starts "When the decision changes an approved architecture record". It tells the agent to put in the chat reply the list of places the decision changes and the form chosen, points at `architecture-records` for the rule, and carries its reason (D11). The list of **Keep chat a projection** is not changed, because the user chose the promotion paragraph. | The rule already exists in `architecture-records` section 7a; the sentence restates no criterion. | Done. The sentence follows the one about saying that the decision is approved and recorded. The validator passes on the package through both of its paths, the width and whitespace scan of the file is clean, and `git diff --check` is clean; the output, with the diff of the package, is `validation-d16-sentence.log` beside the other logs. |
| completed | Historical rejudging completed; D20.2 excludes it from closing D16. The separate D18 attempt has now failed; see current evidence. Original step: D16: one more run of the large case, a single one, in a fresh fixture, with a Sonnet subagent. The prompt is the stored `run-large-3.prompt.txt` with only the workspace path changed. `judge_d14.py` and `build_d14.py` are not edited between the recording of this step and the run; a judge defect that the run itself exposes is corrected only with its reason recorded and with every hand-made result judged again. | The sentence may not be the cause: the prompt asks for the reply and for session notes apart, and the notes may draw the list away from the reply. One run does not separate the two causes. | Every criterion of the large case in the D14 runs step, the whole-replacement criterion included, judged mechanically and by reading. When the reply still lacks the list, no further run is made and the limit is recorded as D16 says. D16 authorizes a single run, so any other miss is recorded as such and goes to the user. Result, run `af105416995895bca`, whose transcript is in the `subagents/` directory of the local history of session `615025e2-7500-4b3f-8854-46e79d75e0ee`, the session that made this run, and not of the session of the earlier runs; judge log `run-large-4.judge.log` and reply `run-large-4.reply.txt`, beside the other logs: **met the historically recorded file and reply criteria; D20.2 excludes it as evidence to close D16. B2 rejudging and B3 corrections remain pending. The reply shows the list with the form.** The prompt was the stored one with only the path changed (`run-large-4.prompt.txt` and `run-large-4.prompt.diff`), and the judge and the builder had the hashes of `d16-freeze.sha256`, equal to those after the D15 run, when the run was first judged. The transcript shows no advisor, reviewer, or subagent, no edit outside the fixture, and no state-changing Git command. By reading: the reply names both owners; it says that the decision changes the decision section, every step of the flow, rules 1, 3, 4, and 5, and the rejected alternatives, that rule 2 does not change, and that it therefore used a new record and not an amendment block; and it says that nothing was implemented and that the plan review comes before any code. The new record says that it supersedes the old record once implemented, puts the router before the consumer in its flow, states the decision in its rules with the router as owner of the check, keeps the DLQ rule word for word, and leaves no part of the old record governing; the old record stays `Implemented` with one notice of two sentences; the index has the entry; the plan's two code steps state the decision behind the review step; the brief item links both owners and keeps no marker. One judge change, under the freeze rule of this step, with the hashes after it in `d16-after-run.sha256` and the log of the unchanged judge kept as `run-large-4.frozen-judge.log`: the unchanged judge failed the run on the check that the unchanged rules are carried over, because it looked for the exact phrase "never reaches the DLQ", while the run wrote rule 1 as "A foreign-tenant record never reaches the order-sync consumer or the DLQ". The criterion is that the rule is carried over, so that no rule is lost when the old record is superseded; that sentence keeps the whole rule and adds what the decision implies, because the router discards the record before the consumer. The check now accepts "never reaches" and "the DLQ" within one sentence. Every hand-made result was judged again, with a log identical to the one before the change, kept as `controls-d14.before-d16-correction.log`: three designated correct results report PASS and twenty-one designated defective results report FAIL. The old large-6 does not actually drop the unchanged rules; B2 invalidates that sensitivity claim. Every earlier run was judged again with unchanged verdicts, as `verdicts-before-d16-correction.txt` and `verdicts-after-d16-correction.txt` show. `build_d14.py` is unchanged. Observations outside the criteria: the run treated rule 1 as changed by the decision and widened it instead of copying it; the brief's list of what it feeds links the new record in place of the old one, which is still in force; the brief was set to `concluído`, which its skill allows because its only item is recorded in both owners; the new record lists option 1 of the brief as a second rejected alternative; the run's plan calls the old record "the superseded record" in its evidence line, and the new record says "unchanged from the superseded record" in its Decision paragraph. These are two premature textual references; the formal status remains Implemented, not Superseded; and that plan puts the consumer step before the router step, with the router as its premise. Limits: one run does not separate the two candidate causes of the D15 miss, the missing sentence and the prompt that asks for session notes apart; D16 asked only whether the list appears in the reply, and it did. The small and the fallback runs preceded the D16 sentence, which sits in a paragraph that both cases read; D16 authorizes no run for them, and the sentence adds to the reply and changes no instruction about files. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. |
| pending | Repeat the author closure audit, obtain a fresh independent second pass, and perform the D7 brief check before any move; update links only when the plan moves. | B1/B2/B3 implementation and revalidation, independent plan review, and required user decisions must be resolved first. | The second pass failed. Historical author checks do not establish current conformance. D21 confirms the revised plan and all decisions are recorded; corrective implementation, required validation, and the independent closure pass remain pending. The author cannot provide that independent verdict. |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

## Material replan after the second failed closure audit

This high-risk corrective design was independently confirmed before the user resumed execution.
B1 source edits, B2 controls/reassessment, and the D22 reader preparation are now complete.
The approved design and historical findings below remain the authority for the continuation;
**Current corrective execution evidence** records what has actually run. The user-opened D18
attempt failed; its complete native transcript and outputs are preserved. D23/D24 resolve the
source-drift choice through the new reviewed batch. Independent closure remains outstanding.

### Findings and reopened obligations

The source is the second audit in this conversation, at the baseline named in the final verdict.
Line references below identify that audited version, not the lines after this replan is inserted.
All six findings are accepted; none is silently waived or reduced to a wording issue.

| Finding | Evidence and defect | Reopened obligation and current disposition |
| --- | --- | --- |
| B1 | `plan-implementation/SKILL.md` lines 324–336 holds affected phases until every owner records the decision, but exempts recording only after review; section 7a requires bounded D3 recording before review. D12 preparation and review lack an explicit path through the marker. | D1 consumer, D3, D12, consumer compatibility, and cross-skill validation are unresolved. The reviewed wording below is now implemented and passed the eleven author walkthroughs; independent closure is still pending. |
| B2 | `build_d14.py` lines 389–394 removes only two numbered invariants. The large-6 Decision paragraph, lines 13–15, retains both restrictions. `judge_d14.py` lines 169–173 rejects missing phrases, not missing meaning. | The claim that all twenty-one defective results failed for the intended reason was wrong for large-6. D14 and D16 sensitivity evidence, the control-building step, and affected validation are unresolved. Old files and log outcomes remain untouched. |
| B3 | D16 was classified as non-material. Its sentence entered `discussion-briefs` and `run-large-4` ran before the inherited independent plan review. The plan's former review section explicitly deferred that review to closure. | D16 review compliance and closure remain unresolved. Advisor advice and the later review do not restore the missed order. D17 deferred the evidence choice; D20.2 now excludes large-4 from closing D16, and D18 conditionally authorizes one new run. |
| N1 | The D14 matrix claimed final skill text apart from the whole-replacement sentence; small and fallback also preceded D16. | Corrected in the run premise, matrix, and completion evidence. Only large-4 followed D16; no new run follows from this wording fix. |
| N2 | The current-evidence section described the pre-implementation skills, and the brief gave stale advice about waiting for the skills to change. | Baseline evidence is now explicitly historical. The brief summary and obsolete advice are rewritten for the current state, preserving every original decision paragraph. |
| N3 | The large-4 observation mentioned premature supersession wording only in its plan. The new record's Decision paragraph also says "unchanged from the superseded record." | Both occurrences are now recorded. Formal status stayed Implemented; neither the old fixture nor its historical reply is edited. |

### B1 proposed wording and consumer checks

Replace the per-phase brief-check paragraph in `plan-implementation` with the following proposed
text after independent review. The three paths preserve the original D3/D12 bounds and explain
why the marker must not prevent its own resolution. They do not authorize any implementation in
this planning turn.

```text
When a persistent plan exists, inspect its current step, prerequisites, and relevant scope before
starting each new phase; do not reread the entire file solely because the phase changed. When a
brief on the same subject exists under briefs/, also check it for decided items still marked
registro pendente. Report them to the user and hold each affected phase until the user instructs
recording and every owner named for the decision carries it, subject only to the recording paths
below. An owner is a document that records decisions: the plan, an architecture record, or an
issue. The code or skill text the plan will change is a work target, never such an owner.

With the user's instruction to record, the marker for that decision must not block the work that
resolves it. Distinguish these paths:

- When architecture-records section 7a permits recording before plan review, allow only its amendment
  block, or Proposed record with the notice and index entry, before deriving and recording the
  plan and reviewing both. This also applies when a persistent plan already exists. No other
  record text, code, configuration, or repository instruction changes before that review.
- When section 7a requires recording after plan review, allow the read-only inspection to scope it,
  the preparation and recording of the plan, and its required review while the architecture
  record still lacks the decision. Keep the marker and its reason; change no architecture file
  during this preparation or review. Do not move the maintenance or amendment ahead of review.
- After the required review, allow the unit that records the decision in its missing document
  owner, together with only the maintenance that owner's skill makes mandatory for that edit.
  For that fallback this is the maintenance and amendment of the architecture record.

Each path waives only the pending marker for the decision it resolves, not recording authority,
other pending decisions, or any other prerequisite. Keep the marker until every named owner
carries the decision. Dependent implementation remains held until recording and all required
reviews are complete. The discussion/planning session performs the architecture recording before
handing the plan and record to an implementing session, as section 7a requires.
```

Inspect these consumers before implementation; change only a demonstrated contradiction, not
wording solely to make them alike. The review can refine this candidate before any skill edit.

| Consumer | Compatibility to establish |
| --- | --- |
| `plan-implementation`, **Inspect before planning**, paragraph beginning "When the plan carries out" | Its unconditional amendment-before-plan instruction contradicts its own D12 exception. Replace it with the two-order proposal below, covering both creation and update of a persistent plan; include it in every applicable walkthrough scenario. |
| `architecture-records`, section 7a | D3 still records before deriving/reviewing the plan; D12 leaves architecture untouched until review. Maintenance bounds, authority, and the D4 recording session stay intact. |
| `discussion-briefs`, promotion paragraph and pending-owner rule | The current "Amend it ... and then record the execution sequence" contradicts D12. Replace it with the two orders proposed below: D3 record → plan → review, and D12 plan → review → mandatory maintenance/amendment → handoff. Explicit recording authority and partial-owner markers remain required; the D16 reply must name only owners actually updated. |
| `codex-claude-loop`, planner/implementer boundary | The planner can prepare/review D12 and perform its post-review recording unit before handoff; dependent implementation remains the implementer's work. |
| Both `plan-implementation` plan templates | Prerequisites and brief checks express the revised order without relaxing closure, review, or user-authorization gates. |

Proposed replacement in `plan-implementation`, **Inspect before planning**, for the paragraph
beginning "When the plan carries out". This is a second B1 source edit, not an assumption that
the per-phase paragraph silently overrides the earlier instruction.

```text
When the plan carries out a deliberate user decision that changes an approved record, follow
the deliberate-decision procedure in architecture-records section 7a. When it permits bounded
recording before review, the discussion/planning session amends the record first, then creates
or updates the plan from that amended record and submits both to the required review. When
mandatory maintenance puts the record edit outside those bounds, create or update the plan
with the maintenance and amendment steps first, keep the decision pending for the record with
the reason, and obtain the required plan review before performing that unit. Complete the
authorized recording before the implementing-session handoff; describe which owners were
actually updated without presenting pending recording or implementation as completed. The
fallback must not be overridden by an unconditional amendment-before-plan instruction.
```

Proposed replacement in the `discussion-briefs` promotion paragraph, from "When the decision
changes" through the sentence about recording versus implementation, confirmed under D21.
Keep the following D16 list/form requirement and completed-plan rule.

```text
When the decision changes an approved architecture record, that record is one of its owners.
Follow architecture-records section 7a. When it permits bounded recording before review, amend
the record first, then derive and record the execution sequence in the plan, and submit both to
the required review. When mandatory maintenance puts the record edit outside those bounds,
record the maintenance and amendment steps in the plan first, keep the decision pending for the
record with the reason, and obtain the required plan review before performing that unit. The
discussion/planning session completes the unit before the planning handoff. In either path,
report the owners actually updated and those still pending; do not imply that partial recording
updated every owner. Say that the user approved the decision and that all required recording
and reviews precede dependent implementation. These two orders keep the fallback from requiring
an amendment before the plan that must authorize its maintenance.
```

Validation is a recorded author walkthrough of the exact rules plus the independent review, not
a new agent run. Exercise the following scenarios against all named consumers and the global
question-only and Git rules. Record the allowed next action and the still-held actions for each.

| Scenario | Required result |
| --- | --- |
| Existing persistent plan, eligible D3 decision, explicit recording instruction | The bounded amendment can occur before the plan is derived/reviewed; dependent code cannot start. |
| New plan, eligible D3 decision | The same D3 order and amendment bounds apply. |
| D12 record and index in Portuguese | Planning and required review can proceed with the marker. Translation covers the entire record and coupled index, then amendment, only after review. |
| D12 maintenance after review | Only the authorized recording unit and mandatory maintenance may resolve this marker; code remains held until every owner is updated. |
| Another pending decision or another unsatisfied prerequisite | The exception for the first decision cannot bypass the other blocker. |
| Same decision recorded in architecture and plan but still pending in a third document owner, such as an issue | The marker names the missing owner; dependent implementation remains held until all three owners carry the decision. The recording exception grants no additional remote-write permission. |
| No instruction to record | These exceptions authorize neither recording nor dependent implementation. |
| Question-only turn containing an imperative and a question mark | Read-only inspection needed to answer is allowed; no file edit, plan creation/change/execution, review initiation, recording, implementation, or resumption of pending work. |
| Question-only turn ending in the literal character w | The same complete prohibition applies even without a question mark. A later explicit non-question instruction is required to resume. |
| Proposed text coexists with an implemented record | Current behavior and status stay authoritative until implementation; no early synchronization to repository instructions. |
| Handoff or closure | D4/D13 still govern handoff; D7 and all inherited closure gates remain in force. |

After authorized implementation, run the package validator for each changed skill, the focused
Markdown/whitespace checks, and the cross-skill read. Structural checks do not establish behavior.
Old runs were made with older wording and are not forward-tests of B1. If the reviewer requires
new behavioral evidence, record that need under D18; do not launch a run or claim inspection is an
automated behavior test.

### B2 control repair, preservation, and acceptance criteria

Define the closed preservation universe before writing any output. Let S denote the scratchpad
of historical session `cd2d99b0-822e-459d-b128-52d36f0cebbc`, and H0/H1 the local history
directories of that session and `615025e2-7500-4b3f-8854-46e79d75e0ee`, respectively. Resolve
these local aliases at execution time; do not put machine-specific absolute paths in this plan.

| Protected group | Exact membership rule |
| --- | --- |
| Historical scratch artifacts | Every entry recursively present under S before output creation, including hidden files, `.git` trees, bytecode, sources, originals, controls, results, prompts, snapshots, hashes, and logs. Freeze the full path list, not a later glob expansion. Planning inventory found 805 files, 614 directories, and no symlinks; re-enumerate at execution and explain drift before proceeding. |
| D6 and D14 transcripts outside S | H0 `subagents/agent-<id>.jsonl` for IDs `a3f534d738622cea6`, `a206a78a8920dd435`, `a8e7ec69d5c6c3d77`, `a7ddbb635e12f9b6a`, `a18d5f5051c2d2c48`, `af41bdfd333cddd18`, and `a3c28b56579d88953`. All seven exact files were found during planning. |
| D16 transcript outside S | H1 `subagents/agent-af105416995895bca.jsonl`, found during planning. This external file must be in both manifests, not assumed covered by S. |

For each frozen path record its alias-relative name, type, permissions, and file SHA-256 or
symlink target. Include directory membership so deletions, additions, renames, and type changes
cannot disappear behind unchanged hashes. Do not follow a new symlink outside these roots.
At the end compare exactly the frozen paths and enumerate membership changes; only the new
exclusive output root and the two source edits below are allowed. Read-access timestamps are
not a preservation criterion. A missing or unreadable input stops the dependent step.

Preserve the current sources before any authorized edit by writing exclusive, newly named copies
of `build_d14.py` and `judge_d14.py` in a new `post-audit-b1-b3-<unused-id>` output root under S.
Verify each backup against its before hash before either source edit. Only these two historical
source paths may change after implementation is authorized; neither exception covers a control,
original, transcript, or log. Write before/after manifests, backup files, and every new result
with exclusive creation; a collision in any destination, including a manifest, aborts without
overwriting it. Do not run a destructive builder entry point or reuse an old output root.
The scratchpad is temporary, so the plan must name the new artifacts and retain concise outcomes
and limitations when they exist; it must not claim that temporary storage is durable retention.

The current builder's `build()` removes existing directories and runs `git init`, and its control
entry points call that function. Do not execute those entry points as they stand. Plan a bounded
control-only mode in `build_d14.py`: read the existing `control-*-base.original` directories,
write controls only under a new output root, reject collisions, and neither initialize Git nor
modify existing Git state. Existing baselines and historical agent runs are inputs, not targets.
Suppress import bytecode writes while running the scripts. No new dependency is required.

Correct `large-6` to isolate a real loss of an unchanged guarantee: remove the DLQ replayability
guarantee from every section, including Decision, Flow, numbered rules, and rejected alternatives.
Preserve the chosen routing decision and all other criteria. The inspected router flow already
drops foreign-tenant records before the consumer; deleting a separate DLQ prohibition may therefore
leave that prohibition implied. Do not claim that both guarantees vanished merely because two
sentences disappeared. Read the complete result and record the specific lost obligation,
replayability, and the assessment that rejects it. If any remaining wording still entails that
guarantee or an unrelated defect explains the failure, repair the control before counting it.
This refines the earlier two-omission proposal without weakening the requirement that every
unchanged rule be preserved; independent confirmation must assess this isolation as well.

Add a correct large-case control that carries both guarantees by paraphrase, with no original
sentence elsewhere that lets an exact-phrase check pass accidentally. For example: foreign-tenant
records are excluded from the dead-letter queue, and every queue entry belongs to the consumer's
own tenant and is eligible for replay. Read the complete control to establish both guarantees and
all other large-case requirements. The judge must accept this valid result; it cannot be kept as
an expected lexical failure merely because the wording differs.

The first D21 review identified another unchanged obligation in the original record's Decision
and Flow: processing must advance after a foreign-tenant record is skipped, expressed there as
committing its offset. The fixture decision moves filtering, logging, and counting to the
router; it does not authorize losing progress/ack. Preserve that observable guarantee in the
whole replacement and its flow, not only the two numbered DLQ invariants. Do not invent a
router implementation, acknowledgement protocol, or established owner. The written plan must
locate and validate the responsible path before removing the existing protection; if that
investigation exposes a genuine architecture choice, return it to the user before code.

`NEW_RECORD_TEXT` omits this guarantee. Consequently the historical large positive is not
semantically valid, and the other negatives that contain a new Proposed record share an additional
defect. Build every new
large control from a corrected positive that preserves progress/ack. All other negatives must
retain it; add one negative that omits only this obligation everywhere while retaining every
other criterion. The valid paraphrase also preserves progress/ack. Read each complete result
to establish the intended contrast; do not repair or relabel the old files as valid controls.

Change `judge_d14.py` only for demonstrated defects: the semantic contrasts above, the D18
Claude-trace sensitivity defects below, and the separately gated D22 reader. State each reason
apart from the desired outcome. If a lexical check cannot support the semantic conclusion,
label it as a lexical diagnostic and require an explicitly recorded reading verdict for meaning;
never turn an omitted semantic check into an overall PASS. The combined result must reject
the corrected large-6 for genuinely missing rules and accept the valid paraphrase. Preserve the
other criteria, including whole replacement, review-before-code, transcript restrictions, and
human reply checks.

Rejudge sequentially, with new logs, and without running agents or reconstructing old outputs:

1. All six D6 hand-made results under their unchanged D6 judge, and all twenty-four original D14
   hand-made results under the corrected D14 assessment. Reclassify old large-6 honestly as a
   misconstructed negative control, not sensitivity evidence, regardless of its lexical output.
   Record the shared progress/ack omission for each historical large control; its old positive
   designation or a negative's other defect does not establish a valid semantic control.
2. The corrected D14 control set: four valid results, including the paraphrase, and twenty-two
   genuinely defective results, including repaired large-6 and the isolated progress/ack
   omission, twenty-six in total. Record every result by criterion; another failure reason does
   not prove the intended defect was caught.
3. Both D6 agent runs under the original D6 criteria; D14 small, fallback, and large runs 1 to 4
   under their recorded criteria, using all existing originals, snapshots, and transcripts. Judge
   the existing large-2.before-advisor directory as a derived file-only state, not a clean agent
   run or a final unassisted reply. Do not rerun the reconstruction script.
4. Read the replies and changed documents for the nonmechanical criteria. Record any verdict
   change with its cause. A judge process's zero exit status is not a passing verdict: these
   scripts print their result. A lexical PASS alone is not semantic conformance.
   Explicitly reassess progress/ack in every historical large run and cite its wording or
   omission. This is an existing whole-replacement obligation previously missed, not a new
   requirement retroactively invented for those runs. Preserve the original logs; any previous
   broad conformance claim remains limited until this reassessment is recorded.
5. Compare after hashes, types, permissions, and membership with exactly the frozen universe above.
   No old artifact may change apart from the two authorized source paths with verified backups.
   A mismatch is a failed preservation check, not permission to restore or overwrite history.

This is rejudging saved outputs, not a fresh forward-test, and proves nothing about a model's
response to B1. It neither consumes nor supplies an authorization for another agent run. D14 and
D16 matrix rows remain unresolved until corrected sensitivity and the B3 evidence disposition are
established. Earlier failed agent runs remain failed for their original independent reasons.

### B3 validation disposition and user decisions

The inherited independent review was missing before the D16 sentence and run. That process fact
cannot be repaired retroactively, and the new author does not accept it on the user's behalf.
The new review evaluates the current D16 sentence as well as this replan before any further
implementation; a later second pass evaluates the result. These are two distinct reviews.

| Validation or claim | Effect of B3 and required treatment |
| --- | --- |
| D16 satisfied the inherited pre-execution review gate | Invalid. Advisor review and a later audit do not satisfy the missing independent review or its order. Keep the deviation explicit. |
| D16 and the complete plan were ready for closure | Invalid. D16 remains unresolved. D20.2 excludes the old run as closure evidence; the future D18 result still needs assessment after review and corrections. |
| The D16 sentence and its interactions are ready for further implementation | D19 found the replan not ready; after the consumer-order and assessment corrections, D21 independently confirmed the plan. Source implementation still requires resumption and validation. This does not restore D16's missed historical review order. |
| Files, transcript, reply, prompt comparison, hashes, and logged mechanical results of large-4 | Preserve and rejudge as history under B2; D20.2 prohibits using the run to close D16. It also does not prove a safe executable plan: that plan removes the consumer protection before creating or locating the router and depends on its existence although the assumption is unestablished. |
| Validators and whitespace checks already logged for earlier versions | Preserve their narrow structural meaning. Rerun those invalidated by later actual edits; no need to replay unrelated validation solely to retell the chronology. |
| D6 limitations, large-1/2/3 failures, and small/fallback historical observations | Not invalidated by B3. They do not prove the final D16 sentence or proposed B1 behavior. |
| A causal claim that D16 made the model show the list | Never established by one run; remains unsupported. D20.2 does not accept that run as evidence to close D16. |

D17 deferred acceptance until D19; that report has arrived, and the recorded D20.2 choice now
excludes large-4 as evidence to close D16. D18 authorizes one additional large-case run, in an
independent session opened by the user, after review and approved corrections, with its model,
request, criteria, and limits recorded before execution. No advisor, nested subagents, automatic
retries, or other cases are authorized. D16 itself is exhausted. Rejudging the old outputs does
not meet the new-run obligation, and a failed or insufficient new run leaves it open.

These evidence choices do not block B1/B2 corrections after their required review and the user's
later instruction to resume implementation. Only a new substantive decision raised by review
could add such a decision gate; none of Sol's five findings required one. D21 confirmation is
complete; the remaining work is live validation and closure,
not a missing D17/D18 choice.

### Test responsibilities and acceptance contract

The D18/D22 launch descriptions in this section document their original authorizations.
D24 supersedes their attempt ceilings and launch routing as stated at the top of this plan;
their content and side-effect criteria are unchanged. Use the current batch order and manifest.

The author runs deterministic scripts and reads the semantic results in this session. No GPT
subagent is needed to run those commands. The user opens the single D18 session with Sonnet as
the proposed test model; record its actual model ID and available effort setting before starting,
without assuming the historical `claude-sonnet-5` is still available. This is a planning proposal
within D18's existing manual-session route, not a new run authorization or a model substitution.
Independent plan confirmation uses the D21 Sol xhigh subagent; final conformance review remains
a separate fresh session opened by the user. Neither the author nor a test subject supplies
those verdicts. The separately authorized D22 configuration is `gpt-5.6-terra` at `xhigh`,
launched by the author with fresh task context after the defined prerequisites.

| Check | Executor and observable acceptance | What it does not prove |
| --- | --- | --- |
| Preservation and collision handling | Author: freeze the B2 universe, verify source backups, compare exact before/after inventories, and exercise collision refusal in a fresh output area containing a known sentinel. Existing content must remain byte-identical when creation is refused. | Correct workflow instructions or model behavior. |
| B1 rule walkthrough | Author, then independent reviewer: evaluate every B1 scenario against all named consumers, recording permitted actions, held actions, and the governing passage. Show why the original wording fails the D3/D12 cases and why the candidate resolves them. | An automated state machine or a model forward-test; do not create a mock gate that merely repeats the proposed rule. |
| B2 sensitivity controls | Author: six historical D6 controls, twenty-four historical D14 controls, and the corrected twenty-six-result D14 set. Valid controls preserve both DLQ guarantees and progress/ack; isolated replayability and progress/ack omissions fail for their intended reasons. Report mechanical diagnostics separately and record the common omission in historical large controls. | New model behavior or retroactive validation of large-4. |
| Historical output reassessment | Author: both D6 runs, D14 small/fallback, large 1–4, and the existing large-2 pre-advisor derivative, with frozen originals, snapshots, transcripts, and replies. Record every criterion, failure reason, and limitation. | A fresh run; the pre-advisor derivative is not an independent run, and D20.2 still excludes large-4 from closing D16. |
| D18 result and transcript assessment | Author after Sonnet stops: compare full inventories, check the complete transcript and actual model identity, and judge the record, plan, brief, and reply against the criteria below. Any missing criterion or unauditable side effect prevents a pass. | Repeatability, a causal effect of the D16 sentence, or coverage of the D12 fallback. |
| D18 Claude transcript sensitivity | Author before the live run: assess the data-only positive and negative traces below using the actual Claude schema, read destinations, call/result pairing, path boundaries, and effects. Every designated defect must be rejected for its own reason; allowed global-instruction and skill reads must pass. | A complete trace merely because a reader recognized some tool names, or Codex coverage from Claude controls. |
| D22 Codex transcript assessment and Terra run | After the recorded prerequisites: author validates a Codex event reader and its sensitivity controls, starts one Terra xhigh test subject, and evaluates it against the same content and side-effect criteria as D18. | Authorization under D18, a substitute Sonnet pass, or a comparison that isolates model quality from client/tool differences. |
| Structural validation | Author after approved edits: validate every changed skill and its exposed path, check Markdown links/formatting and whitespace, and reread affected consumers together. | Semantic correctness merely because a validator exits successfully. |

Every output assessment records the artifact ID, criterion, expected outcome, observed outcome,
evidence pointer, and pass/fail/unverified verdict. An unverified mandatory criterion blocks an
overall pass. Judge exit status alone is not the result. Run commands sequentially and retain
new logs; do not repeat already valid unrelated checks solely to increase a test count.

#### D18: one blind large-case run for Sonnet

The tested behavior is decision promotion into all owners, with a coherent future implementation
sequence and a user-visible reply, while leaving implementation untouched. Use the original
large-case input under `forward-test-d14/control-large-base.original`, not large-4's output.
The fixture has a decided brief item, an Implemented record with unchanged DLQ rules, an existing
plan with a pending review, and a consumer that still owns the tenant check. Only the consumer
source exists; no router implementation is present in this inspected input.

Preparation is author work after confirmation and implementation resumption. Create a fresh
exclusive fixture beneath the new evidence root; never reuse a historical run directory. The
original input has no `.git`; preserve that absence, verify the new directory lies outside every
Git worktree, and record this environment difference from historical initialized fixtures. Do
not initialize Git, copy Git metadata, or weaken the prohibition on Git mutations. Full inventory
comparison must detect any added Git metadata, and transcript reading must detect prohibited
commands even if their effects were later undone. This run establishes no behavior specific to
an initialized repository; the reviewer must accept that limit before launch.

Freeze the fixture, actual shared-skill files, input instruction files, prompt, assessment
criteria, and judge hashes before the run. Pin the exact model/effort, terminal conditions, and
the local transcript/output locations in the run manifest. Confirm that the Claude client can
retain a complete transcript and that the test session starts with only this fixture as its
workspace. If that capability or isolation cannot be established, do not spend the run.

The prompt keeps the realistic request `registre as decisões` and the historical limits against
Git mutation, out-of-fixture edits, advisor, reviewer, and subagents. It directs the agent to the
global instructions and applicable shared skills and asks for a chat reply and separate session
notes as before. Adapt only workspace/global-skill paths and the description "isolated workspace"
to the actual prepared environment; save the prompt diff. Do not give Sonnet this parent plan,
Sol's findings, old outputs, the judge, or the expected record form/list/order. The fixture's own
plan is the task authority it may read. No coaching or corrective follow-up after launch.

| Criterion | Required result |
| --- | --- |
| Architecture | One Proposed whole replacement states the chosen routing decision correctly in rules, flow, and ownership and preserves both unchanged DLQ guarantees and stream progress/ack by meaning, including the discarded-record flow. The old record retains its Implemented status and original content except the allowed notice. Both remain indexed; no text presents supersession as already completed. |
| Decision owners | The fixture plan records the decision; its brief links every actual owner, removes the marker only after all owners are updated, and does not claim implementation occurred. |
| Future implementation order | The plan keeps required review before code, scopes or establishes the router's currently unverified location, and requires the new filtering path and responsibility for preserved stream progress/ack to be located and validated before removing the consumer's protection. It must not invent an established owner or protocol; a genuine architecture choice returns to the user. An explicitly atomic transition is acceptable only if its prerequisites and validation rule out a protection or progress gap; an unsupported assumption that the router already exists is insufficient. |
| User-facing reply | The chat reply itself names the updated owners and shows the changed places and chosen form. It separates the recorded decision from pending review/implementation. A list present only in session notes fails this criterion. |
| Side effects and independence | Only allowed architecture, index, plan, and brief outputs change. Code, instructions, skills, and all historical artifacts remain untouched. The complete transcript shows no Git mutation, advisor, reviewer, subagent, out-of-scope edit, or reading of the withheld answers. |

Add a small D18 content-assessment control set before the paid run, separate from the twenty-six
B2 controls: one fully valid result plus six single-defect variants. The defects are (1) the list
exists only in session notes, (2) consumer protection is removed before router filtering is
established, (3) a router location is asserted without evidence or a prerequisite step, and
(4) the old record is described as already superseded while its status still says Implemented,
and (5) progress/ack after a discarded record is absent, while the plan retains the prerequisite
to locate and validate that responsibility; and (6) the record preserves progress/ack but the
plan omits locating and validating its responsible path before removing the existing protection.
These last two negatives isolate the record obligation from its implementation-plan prerequisite.
Every other variant retains both. There are seven content controls in total.
Every variant must fail its named criterion while the other criteria remain satisfied. These
are fabricated documents/replies, not extra model runs. Preserve the original criteria when
rejudging old runs; the added D18 criteria do not rewrite historical verdicts.

Before the Sonnet launch, independently validate its Claude transcript assessment. The current
reader ignores `Read`, `Glob`, and `Grep` destinations and does not establish call/result
pairing or trace completeness. Its edit-path substring and command heuristics cannot prove
these properties. Use the already authorized complete Claude transcript as a schema reference,
keeping it within the frozen B2 universe. Record an explicit inventory of recognized events and
which evidence proves terminal completion, tool results, reads, writes, execution, and delegation.
Unclassified effects, uncertain shell behavior, or missing evidence remain unverified.

Build data-only controls in that observed schema, with the relevant fixture/path inventory;
these do not run an agent. A valid complete trace must pass while reading global instructions
and applicable shared skills outside the fixture and editing only permitted outputs. Add
separate negatives for each of these risks, preserving the other properties in each control:

- an out-of-fixture edit and an out-of-fixture shell write, as separate cases;
- a state-changing Git command, including a variant with its filesystem effect later undone;
- an advisor, reviewer, or subagent call, covering each applicable entry point;
- a read of a withheld answer through `Read`, a `Glob`/`Grep` lookup, or a shell command;
- an empty trace, unknown event format, missing tool result, or missing terminal completion;
- boundary escape through a relative path, a sibling sharing the fixture name prefix, or a
  symlink. Include allowed relative-path and symlink cases whose resolved targets stay inside.

Every negative must fail or become unverified for its designated reason, never pass. A new
validator that classifies all legitimate external instruction reads as forbidden also fails its
positive control. Record criterion-level results before spending the run. These Claude controls
are required for D18 regardless of D22's readiness. Corrections to the Claude reader preserve
historical criteria; distinguish newly demonstrated assessment coverage from what old logs
actually checked. Code implementing these controls and readers waits for reviewed implementation.

This assesses the safety of the written sequence, not working router code or actual migration.
The fixture code is never executed or modified by Sonnet. A transcript parser that sees no
recognized events, an unknown event format, an incomplete transcript, or an uncertain shell
effect yields unverified, not a vacuous pass. Read the actual shell and tool events as well as
the file diff; the existing judge's edit-path and Git-command heuristics are not complete proof.

The launch package handed to the user contains the verified fixture path, exact Sonnet selection,
ready-to-send prompt, and how to preserve the transcript and final reply. Raw prompts and logs
live beside the run artifacts, not in this plan. The package is prepared only after the reviewed
skills and fixture exist. The user opens one fresh session and pastes that prompt once. The
author collects and assesses the result afterward; Sonnet does not repair or judge its own test.
Failure, interruption after model work starts, or insufficient evidence consumes the attempt;
preserve it and report the gap. No automatic retry, model substitution, or criterion weakening.

#### D22: one complementary Terra xhigh run in Codex

**Authorization status: approved and extended by D24; new batch prerequisites pending.**
D22 preparation and controls are complete, and the original Sonnet is terminal. D23/D24 resolve
the source-drift choice by retaining current instructions. The delta review and new batch freeze
precede launch. The remaining original launch description below is read under D24's supersession
of attempt ceilings, routing and all-history source equality.

Once its prerequisites are satisfied, the author may launch one `gpt-5.6-terra` agent with `xhigh`,
`fork_turns="none"`, and no inherited conversation. Verify those settings from the actual run
metadata; do not substitute another model or effort when unavailable. Fresh conversation
context does not create a filesystem sandbox: restrict the task to its separate fixture,
prohibit reading the parent plan and withheld evidence, and audit tools and file changes.
If the client cannot preserve the complete tool trace or establish that task boundary, leave
the run blocked before launch. The test subject must not spawn agents, reviewers, or an advisor.

Run after Sonnet reaches a terminal result, with no parallel model runs. Start from a separate
fresh copy of the same original fixture, never Sonnet's modified files. Freeze both input
copies and the actual shared skills before the first run so the second sees identical task
content. Use the same user request, output sections, constraints, and acceptance criteria;
record only necessary path/client bootstrap differences in the prompts. Neither test subject
receives the other one's output, score, diagnosis, or expected answers. If Sonnet exposes a
defect requiring changed skills, criteria, or inputs, stop before Terra and replan; do not
silently turn it into a coached retry. A behavioral miss alone does not authorize coaching.

The inspected `judge_d14.py` reads Claude `message.content` entries and recognizes tools such as
`Edit`, `Write`, and `Bash`. Passing a Codex transcript through that reader could produce empty
edit/command collections and an unjustified pass. Plan a separate, explicitly selected Codex
reader within the existing assessment source; keep the Claude path and historical criteria.
Its concrete schema was verified against the frozen completed D21 transcript before the
reader implementation. The inspected envelopes, tool calls/results, final reply and model
metadata are recorded in the current execution evidence. Do not launch an agent merely to obtain a
sample
or search unrelated chats. Missing access or an unknown format holds this work, not its checks.

| Codex assessment obligation | Required evidence before trusting the run |
| --- | --- |
| Parse real events | Preserve event order and tool-call/result identity, including nested calls through tool orchestration. Account for every event that can read, write, execute a command, or delegate. Empty recognized-event sets, incomplete traces, missing results, and unclassified effectful tools prevent a pass. |
| Verify paths and effects | Resolve paths against the fixture boundary, including relative paths and symlinks; a sibling whose name shares the fixture prefix is outside it. Inspect shell, patch, and nested execution effects, including a forbidden operation later undone. A final unchanged snapshot alone cannot prove compliance. |
| Preserve semantic criteria | Reuse D18's record, owner, implementation-order, reply, and side-effect requirements unchanged. Unknown wording requires a recorded semantic reading; an unknown event format requires unverified, not a fallback PASS. |
| Prove reader sensitivity | Reconstruct every effect, read, completeness, and path-boundary control required by the D18 Claude-trace list in the actually observed Codex schema. This includes external patch and shell writes, prohibited Git and helper calls, forbidden reads, empty/unknown evidence, missing results and terminal completion, relative/sibling-prefix/symlink escapes, and valid internal relative/symlink paths. In addition, isolate an out-of-fixture write inside nested tool orchestration; include a permitted nested write as a positive. Valid traces include permitted global-instruction and shared-skill reads outside the fixture. Each negative fails or becomes unverified for its designated reason; each positive passes. These are separate data-only Codex controls, not agent runs or reuse of Claude verdicts. |
| Check both readers | Existing Claude assessments retain their recorded scope and outcomes unless an independently justified defect changes them. Keep per-criterion logs, failed controls, and reviewer dispositions; do not change both readers to fit either live output. |

Apply the same exclusive artifact creation, source backups, and preservation manifests as B2.
Freeze the complete Codex sample paths before their read-only use; add them to the protected
universe explicitly. Store new reader controls and Terra outputs under new names in the new
evidence root. Preserve both live runs after completion, even when their verdicts differ.

Report one verdict per model/client and per criterion, plus observed token usage and elapsed
time when available. One run per configuration establishes observations, not success rates,
statistical superiority, or the isolated effect of reasoning effort. Terra's result does not
replace D18, rehabilitate large-4, or satisfy the independent review. A failed or interrupted
attempt is retained and not repeated automatically; unknown cost is reported as unknown.

#### Coverage deliberately left outside this run

D18 does not add live tests of a small amendment, Portuguese-record fallback, question-only turn,
or third recording owner. Those paths receive the B1 walkthrough and existing-artifact checks,
with the distinction visible in the matrix. If independent review requires new behavioral
coverage there, record a new bounded proposal for the user before running it. Running a GPT
test subagent is still another model run and cannot bypass the one-run limit or D18's route.
D22 separately authorizes one complementary large-case attempt after its own prerequisites.
The D21 reviewer only inspects evidence and is not a test subject or a source of forward-test
evidence.

### Ordered continuation and stopping points

| Status | Step and owner | Prerequisite | Evidence required |
| --- | --- | --- | --- |
| completed | Record the second audit and correct N1/N2/N3 in this plan and brief. | The user explicitly requested these document edits. | Six finding dispositions, original decision paragraphs preserved, affected steps and matrix reopened. |
| completed | Prepare this B1/B2/B3 material replan and open the brief's two choices and review dependency. | The author does not decide evidence acceptance or new runs. | Proposed B1 wording, consumer list, B2 controls/preservation criteria, and B3 invalidation boundaries above. |
| completed | Independent plan review by the fresh Sol session opened by the user. | Advisor is unavailable; this author and all subagents are excluded. | D19 received: `gpt-5.6-sol` at `xhigh`, not ready for implementation, with three blocking and two non-blocking findings recorded under **Plan review**. Receipt satisfies delivery only. |
| completed | Promote D17, D18, and D20 and record the D19 report. | The user explicitly instructed recording after deciding the three items. | Governing rows, outcome, B3 evidence disposition, steps, matrix, and brief agree. No skills, sources, controls, or runs changed in this promotion. |
| completed | Revise the plan for Sol’s findings and define the author/Sonnet test split. | The user requested planning only; no execution or skill/source edit. | B1 consumer order and full walkthrough, B2 closed preservation universe, and D18 criteria/controls and handoff are specified. No user decision changed; independent acceptance is not claimed. |
| completed | Add the proposed Terra xhigh test and Codex assessment design. | The user explicitly requested a planning update only. | D22 describes one complementary Codex run, shared criteria, separate input copy, fresh context, transcript controls, and no automatic retry. Execution is not authorized. |
| completed | Promote D21 and D22, including the user-requested D21 subagent route. | Explicit user recording and Sol xhigh review instruction. | Governing decisions, test authorization, continuation, closure obligations, and brief agree. No skill, source, fixture, or result edit. |
| completed | Receive the first D21 review and correct its three plan findings. | Read-only Sol xhigh review of the promoted baseline. | The review found the plan not ready. Added the internal B1 consumer correction, preservation and isolated controls for progress/ack, and independent Claude transcript sensitivity controls. These are plan changes only; confirmation of the delta remains outstanding. |
| completed | Obtain independent confirmation of the revised plan and test design (brief D21). | Fresh `gpt-5.6-sol` at `xhigh`, `fork_turns="none"`, read-only instructions, fixed evidence baselines, and no requested verdict. | The reviewer examined the plan and its corrective deltas and confirmed readiness after the last historical-label fix. Configuration, hashes, findings, dispositions, and limits are under **Plan review**. No skill, source, fixture, or test was changed or executed. |
| completed | Implement reviewed B1 wording and necessary consumer corrections. | D21 confirms the concrete change and the user instructed completion; recording and review gates remain intact. | Focused validators and the scenario walkthrough, with limits recorded. No agent run. |
| completed | Implement reviewed B2 source/control corrections and rejudge existing evidence. | The independent review permits the test design; exclusive destinations and source/evidence preservation are established. | New named logs and manifests, valid paraphrase accepted, corrected omission rejected for its intended reason, all historical outcomes accounted for. No agent run. |
| completed | D22 preparation: implement the explicitly selected Codex transcript reader and validate its controls. | D22 is approved and recorded and D21 confirms the design; implementation must be resumed and a complete authorized sample must be available. D22 is not a prerequisite for B1/B2 or D18. | Positive and negative controls establish event coverage and meaningful rejection; unknown or incomplete evidence cannot pass. A missing prerequisite holds this step without cancelling its recorded obligation. |
| completed | Assess the single user-opened D18 attempt under D20.2. | The attempt ran before the required launch preflight; preserve that deviation. | FAIL: actual Sonnet 5/high, unsafe consumer-before-router sequence, missing progress-path validation prerequisite, and premature supersession wording. The reply criterion passes. Attempt consumed; assessment completion does not satisfy D18/D16. No retry. See current evidence. |
| completed | D22 run: launch and assess one Terra xhigh attempt after Sonnet stops. | Recorded D22 approval, completed Codex controls, D21 confirmation, unchanged common inputs/criteria, and verified launch evidence. | Terra xhigh ran after the original Sonnet terminated and after D24 review/freeze. Assessment FAIL, with native-input readability limits separately UNVERIFIED. No coaching or source change; result below. |
| pending | Repeat the complete author audit and request the next independent closure pass. | All applicable obligations resolved and revalidated; this session remains the author. | Both traces, updated matrix and brief check, fresh external read-only audit. Keep active until conformance passes. |

## Current corrective execution evidence

The user resumed execution with `termine`. B1 is implemented in both affected paragraphs of
`plan-implementation` and the promotion paragraph of `discussion-briefs`; the D16 reply
requirement is unchanged. Eleven author walkthrough scenarios passed by reading. This is not
an automated behavior test. The architecture procedure, loop boundary and both plan templates
remain compatible without edits. Four package checks passed through canonical and exposed
paths, with focused formatting and diff checks.

New evidence is under S `post-audit-b1-b3-410811bdf229/`. This temporary storage is not durable
retention. `preservation-before.json` freezes 805 files, 614 directories and eight external
transcripts, with verified source backups. Only `build_d14.py` and `judge_d14.py` were changed
inside the historical universe. The new builder mode refuses existing destinations, preserves
a collision sentinel and uses original files without Git initialization.

| Completed local check | Result and evidence |
| --- | --- |
| B1 wording and consumers | Eleven author reading scenarios; `b1-walkthrough.json`. Exact reviewed orders implemented; no new user decision. |
| B2 controls | Six original D6 controls; 24 original D14 controls; 26 corrected D14 controls. Corrected set: four valid accepted and 22 defective rejected for their intended reasons. `b2-assessments/criterion-results.json` and per-artifact logs/readings. |
| Semantic assessment | Exact phrases are diagnostic only. Hash-bound author readings preserve meaning; the paraphrase passes, isolated replayability and progress omissions fail. No supplied reading means UNVERIFIED; a mismatched inventory is rejected. This is a combined mechanical/author assessment, not an automated language-understanding test. |
| Historical results | Eight saved runs and the existing pre-advisor derivative reassessed. `historical-dispositions.json` preserves limited D6 results, historical small/fallback observations and all large failures. No new model run or reconstruction. |
| D18 content controls | One valid and six single-defect variants read by criterion, including separate record and plan progress obligations. `d18-content-controls/author-readings.json`. |
| Claude/Codex trace controls | Fifty final data-only controls pass their sensitivity expectations: 24 Claude and 26 Codex, including unfinished execution and actual-cwd cases. `trace-controls-final/results.json`. Initial failures remain in `trace-controls-v1/`: path text falsely suggested delegation and a greedy JavaScript match rejected valid calls. Both were fixed before any live attempt; cwd and async safeguards followed author inspection. |
| D22 schema | User authorized targeted local discovery. The existing completed D21 transcript was frozen in `codex-sample-before.json`; 95 calls have paired outputs and terminal task completion. Its contexts confirm Sol/xhigh. `codex-schema.json` records envelopes and limits. |
| Live preparation | Two identical fresh copies of the original input, outside Git worktrees, plus shared-source hashes, prompt diffs and a launch manifest in `live/`. The package selected Sonnet 5/xhigh. The actual run used Sonnet 5/high; the final preparation manifest remains unchanged as the pre-run contract. |

The Codex reader explicitly selects its schema and preserves call order/identity. A single
literal awaited nested tool call can be classified; dynamic orchestration, arbitrary shell,
unknown tools/attachments, compaction effects, missing results or terminal evidence remain
unverified until separately read against the exact trace. Passing the synthetic controls does
not prove that an arbitrary future transcript is fully auditable or safe.

The new reading corrects two historical qualifications. The block-instead control has no new
record and keeps acknowledgement in its old record; it fails form rather than losing that rule.
Large-2 before the advisor explicitly commits offsets, while its final record makes the discard
mechanism undecided without preserving the progress guarantee. The derivative therefore retains
its historical file-only result and never becomes an independent successful run. Large-3 also
omits progress, and large-4 fails that obligation in addition to its D20.2 history-only status.

The final preservation comparison passed in `preservation-after.json`: all original membership,
types, permissions and hashes are unchanged except the two backed-up source contents. The eight
Claude transcripts and the newly frozen Codex sample are intact. `final-local-validation.json`
and `pre-handoff-check.json` record the structural/link checks, same-paragraph D16 requirement
and frozen inputs. `b2-assessments/semantic-reading-clarifications.json` adds source-line
citations to the B2 readings without changing verdicts. The current handoff and manifest are
`live/sonnet-handoff.final.md` and `live/launch-manifest.final.json`; earlier preparation versions
are retained. These files still mark the Sonnet session preflight as pending, accurately
preserving that it was not completed before the user launched the attempt.

### D18 Sonnet high result and Terra launch hold

The user supplied the final reply and reported using Sonnet high. Read-only local discovery
found the complete native session `8876fc0b-1f63-46eb-b03f-8818a2e274f8`, with one task input
matching the frozen prompt, 28 tool calls with 28 paired results, and a final assistant
`end_turn`. Metadata confirms `claude-sonnet-5` and `high`; this is not xhigh evidence.
The session began in the home workspace with Terminator also available, and the client injected
home project instructions and Git context. The required fixture-only preflight did not happen.
These launch deviations cannot be repaired retrospectively.

The author assessed the unchanged output against the frozen criteria. Evidence is in the new
exclusive directory S `post-audit-b1-b3-410811bdf229/live/sonnet-result/`: native transcript copy,
complete final fixture, inventory, diff, reply, frozen-reader output, and
`assessment.final.json`. Original files and the test output were not repaired.

| Criterion | Result and evidence |
| --- | --- |
| Architecture | The new Proposed whole replacement preserves both DLQ guarantees and commits offsets in its discarded-record flow. The old record changes only by its notice and both remain indexed. FAIL for premature wording in the fixture plan: it calls the still-current record "the superseded record". |
| Decision owners | PASS: the record and plan carry the decision; the brief links both and distinguishes recorded from implemented. |
| Future implementation order | FAIL: execution step 3 removes consumer protection, step 4 implements the router, and step 5 integrates it. The router's location is explicitly unknown. Normative ownership is not proof of a working path, and no prerequisite locates and validates progress/ack responsibility before removal. |
| User-facing reply | PASS: CHAT REPLY names both owners, identifies the flow and three changed invariants, chooses the new-record form, and leaves review and implementation pending. Its semantic grouping meets the frozen criterion without requiring an exhaustive heading inventory. |
| Observed operations | Author reading finds only five permitted document changes, unchanged code, 28 paired calls, read-only shell operations, and no advisor, reviewer, subagent, Git mutation, or withheld-answer tool read. The broader initial workspace remains a separate launch failure. |
| Trace assessment | Native start, tool pairing and terminal evidence are present. The frozen reader returns UNVERIFIED for actual-cwd and top-level session metadata/attachment shapes beyond its controls and for shell commands requiring reading. Author inspection does not turn that mechanical result into PASS. No reader was changed to fit the run. |

**Overall: FAIL; attempt consumed.** D14/D16/D18 remain unresolved. The test took 267.08 seconds
from task input to final reply. Native usage, deduplicated by message ID, reports 22,681 output
tokens, 38 uncached input tokens, 143,128 cache-creation input tokens and 2,100,875 cache-read
input tokens; the latter are repeated request traffic, not unique context. Monetary cost is
unknown. One run does not establish an effort comparison or a causal explanation of the misses.

Before starting Terra, the common-source check first matched the freeze, then detected concurrent
changes to `.codex/AGENTS.md` and `.claude/skills/docker/SKILL.md`. The inspected delta extends
Docker execution-routing guidance and its registry trigger. Those edits belong to other work
and are preserved. The Terra fixture, tested skills, criteria, prompts and judge remain unchanged.
`common-source-drift.json` records the exact before/observed hashes. No Terra attempt was spent.
That source change originally held Terra before launch. D23/D24 now explicitly select a new
current-source baseline with inherited review; the old manifest remains unchanged. E1 is resolved as receipt of the attempted session, not a passed
preflight or test; E2 remains the external independent closure dependency. No new skill fix,
retry, acceptance-criterion change or independent closure verdict is claimed.

### D24 batch results and interactive handoff

The Sol-reviewed batch froze the current 21 common sources, original inputs, prompts, criteria
and unchanged judge in S `post-audit-b1-b3-410811bdf229/live/d24-batch-01/`. All common
source hashes still matched after both attempts. The prior high attempt and old manifests
remain untouched. Native transcripts, final fixtures, inventories, replies, reader outputs and
per-criterion author assessments are retained under `terra-result/` and `sonnet-result/`.

| Attempt | Result | Evidence and limitation |
| --- | --- | --- |
| Terra `gpt-5.6-terra`/`xhigh` | FAIL | 186.487 seconds; 13 calls with paired results, only three architecture files changed. The plan and brief remain original; required workflow skills were not loaded. The new record omits source progress/ack. The final CHAT REPLY lacks the changed-place list shown earlier in commentary. No helper, Git mutation or out-of-scope write observed. |
| Sonnet `claude-sonnet-5`/`xhigh`, local CLI | Invalid for shared-skill evaluation | Metadata bootstrap confirmed model/effort, fixture cwd, no additional directories and native capture. During task work, the required global Read was automatically denied because no approval surface existed. No shared skill loaded; the model continued and rewrote the current architecture instead of using the required form, leaving the plan unchanged. This setup failure cannot establish Sonnet xhigh's behavior under the skills. |

Terra's native trace has complete tool events and terminal completion. Its initial task payload
is encrypted in both parent and child histories; their ciphertexts match, but exact native
plaintext comparison is unavailable. The caller's frozen prompt and launch configuration remain
retained. The frozen reader reports 8 PASS / 0 FAIL / 17 UNVERIFIED rows. Author reading
classifies all 13 calls and their effects without upgrading that mechanical verdict. Native
usage reports 572,332 input tokens (517,632 cached) and 9,352 output tokens; input totals are
request traffic, not unique context. Monetary cost is unknown.

Sonnet's native trace confirms xhigh throughout, with 15 calls and paired results, one denied
Read, two read-only shell operations, and four edits to three permitted documents. Task elapsed
time was 145.026 seconds. The CLI estimates USD 0.2850888 for task work and USD 0.029159 for
bootstrap, not verified billing. Its task output totals 15,766 tokens; bootstrap is separate.
The frozen reader remains UNVERIFIED (15 PASS / 0 FAIL / 62 UNVERIFIED rows). The native
Git metadata incorrectly reports a repository; actual Git inspection and complete inventories
show none. No Git repository was created.

The author preflight did not establish permission to read required external instructions before
sending the earlier task. This is an author setup defect, not a source-skill defect or a reason
to weaken criteria. The denied read was not retried through another tool or permission bypass.
The reviewed interactive route uses `live/d24-manual-02/`, with fresh original-equivalent input,
frozen task prompt and session configuration. The user explicitly instructed the author to
operate it. The original `open-sonnet.sh` failed before a model request because variadic
`--mcp-config` consumed the bootstrap prompt. That launcher and error are preserved; the new
`open-sonnet.interactive.sh` fixes argument order without changing flag values and passed
`bash -n`.

The interactive client required initial onboarding. The operator selected Auto theme, used the
existing subscription login route, acknowledged security notes and trusted this prepared fixture.
These are client setup effects; global runtime state is not claimed unchanged. No global
model, effort or permission defaults were edited, and no bypass was enabled. Native session
`41bcfc91-e06d-4c6f-9bbb-757e7a88c89d` confirmed Sonnet 5/xhigh, fixture cwd, no additional
directories, one metadata-only bootstrap and zero bootstrap tool calls. Its snapshot is retained
in `interactive-bootstrap.native.jsonl`; `interactive-preflight.json` records the source and
fixture checks and the unreliable native Git metadata limitation.

The frozen task was then submitted without coaching. Its native text matches the saved prompt
apart from trailing whitespace. Required global and skill reads were approved individually
through the normal interactive surface. E3 is resolved as access and launch. The task reached
native `end_turn`; the client then exited normally with code 0. No corrective follow-up was sent.

### D24 interactive Sonnet xhigh result

Evidence is retained exclusively in `live/d24-manual-02/sonnet-result/`: native transcript,
final fixture, inventories, source recheck, final reply, frozen-reader output, all tool calls
and results, and hash-bound `author-trace-reading.json` and `assessment.json`. All 21 shared
sources, criteria and judge still match the launch manifest. The original launcher failure and
both earlier Sonnet attempts remain preserved. **Overall verdict: FAIL on content.**

| Criterion | Result and evidence |
| --- | --- |
| Architecture | FAIL: correct Proposed form, old Implemented record plus notice only, both records indexed, both DLQ guarantees and discarded-record offset commit preserved. However, the new record's Non-goals says the old record continues to govern DLQ/replay; this conflicts with whole replacement when the old record is superseded. Copying the rules does not remove that residual authority. |
| Decision owners | PASS: architecture and plan updated; brief links both, removes the pending marker after recording and distinguishes proposed from implemented. |
| Future implementation order | FAIL: the plan now locates the router and validates filtering before removing consumer protection. It still lacks locating and validating responsibility for discarded-record progress/ack before removal. The record's offset-commit sentence does not establish that plan prerequisite. |
| User-facing reply | PASS for the frozen criterion: CHAT REPLY names both owners, Decision/Flow/invariants 3–5, the new-record form and pending review/implementation. Separate factual errors: it says no Git command ran, although read-only `git status` ran and failed outside Git; session notes deny external reads despite the permitted instruction/skill reads. |
| Observed effects and independence | PASS by complete author classification: 28 paired calls, comprising 18 Read, four read-only Bash commands, two Write and four Edit calls. Exactly five permitted documents changed; code/instructions, shared sources and historical artifacts are unchanged. No helpers, withheld-answer reads, Git mutation or outside writes were observed. |
| Launch/capture | PASS: fresh fixture/session, native Sonnet 5/xhigh throughout, fixture cwd with no additional directories, frozen task and normal individual read approvals. The recorded onboarding effects and unreliable native Git metadata remain limitations. |
| Frozen trace reader | UNVERIFIED: 26 PASS / 0 FAIL / 172 UNVERIFIED rows. Native envelopes, event identity, cwd/start/end and four shell effects exceed its schema. The separate hash-bound author reading accounts for the complete native trace; no mechanical verdict or reader was changed. |

Elapsed wall time from task input to final reply was 553.83 seconds, including interactive
approval delays. Deduplicated task usage: 33,186 output tokens (22,896 thinking), 38 uncached
input tokens, 85,047 cache-creation input tokens and 1,736,543 cache-read input tokens.
Bootstrap is excluded; repeated input traffic is not unique context. Monetary cost is unknown.
The filtering order improved in this output, but one run with changed client setup does not
establish a causal benefit from xhigh or a success rate.

No skill or judge was changed in response to these misses. These attempts do not close
D14/D16/D18/D22 or authorize a final conformance claim. The concrete launch defect is resolved.
Any further run requires a new recorded diagnostic purpose or a reviewed source correction;
repeating identical input merely for a favorable output remains excluded. E2 still waits for
the required evidence and author audit.

## Plan review

### T1 readiness review

Fresh read-only reviewer `/root/t1_plan_review`, launched as `gpt-5.6-sol`/`xhigh` with
`fork_turns="none"`, returned **READY for the bounded T1 source implementation**. It verified
all hashes in T `review-input.json` and the exact two-hunk candidate. No blocking or non-blocking
correction was requested; no finding was rejected. Advisor unavailable. These are caller
configuration facts; backend metadata was not independently audited.

Reviewed plan SHA-256: `fcac1f2c24cd9100ce8cf5906703ff606f4b60f27457219a8dc07bdf86622bb4`.
Reviewed brief: `0a0ab48db89ffeaa0c7b4c6926fe956b9e5a0995eca18e0efdc63d5f5dcc4d05`.
The reviewer accepted the source-only validation boundary and required the planned fresh
post-edit conformance check. Readiness supplies neither that check nor E2 or full-flow acceptance.
Subsequent status updates record the verdict without changing the candidate or its contract.

### T1 source-conformance review

Fresh read-only reviewer `/root/t1_source_conformance`, launched as `gpt-5.6-sol`/`xhigh` with
`fork_turns="none"`, returned **CONFORMS for the bounded T1 source task**. No source defect or
correction was identified. The review confirmed that T2 stays deferred and that the two-hunk
source delta plus plan/brief updates are in scope. It accepted the structural checks and author
walkthrough only for this source-text conclusion. No test was rerun by the reviewer.

The reviewer retained the failed index-byte check and independently observed its instability;
HEAD and staged content remained unchanged. This limitation is accepted as stated, not rejected
or relabelled PASS. No stronger preservation claim is made. Advisor unavailable; launch settings
are caller configuration facts, not an independent backend audit.

Reviewed plan: `f18823029810af3b2cdb07aa3045d8767d1e78b672f0990ea832a7a86fb70c37`.
Reviewed brief: `6d1b11dc3a0f2460398e6e4ea612ce192286659f22930ac51ce54c5a2be3f460`.
T `postedit-review-input.json` binds all source and evidence hashes. Subsequent edits only record
the result and synchronize completion wording. This review supplies no full-flow pass, complete
parent-plan author audit, or E2 verdict.

### Skill-review and model-comparison review

The independent Sol xhigh reviewer `/root/extraction_plan_review` confirmed **READY** for this
bounded delta, with no blocking finding. It verified the reviewed plan, rubric and all three
prompt hashes, equivalent input bytes/modes and shared sources. Advisor unavailable; this is
readiness, not E2. Reviewed plan hash:
`d231227e3ebcc835e771f8cbe5406e03f5232fc26ee36e4bb94ae7700163a2c7`.
Rubric: `6a9e1357ba680050a06e3eb96a974072919193b2e78f929ea1f8d769a8e4c214`.
Exact prompt hashes are retained in the comparison's `review-input.json`.

Accepted scoring qualification: documentation's overbroad compatibility mandate never overrides
the test's explicit no-write boundary. Do not fail an arm for leaving compatibility files
untouched. Applicable-skill loading remains assessed under the existing rubric; no new mandatory
conflict-reporting criterion is introduced. The source-quality review is separate from run scores.

### Guarantee-extraction review

Fresh `gpt-5.6-sol`/`xhigh`, `fork_turns="none"`, reviewer
`/root/extraction_plan_review`: **READY** for one bounded diagnostic. These are launch
configuration facts; no separate backend metadata audit is claimed. No blocking finding.
Applied clarification: score identification/classification separately from validation, so a
validation-only miss cannot be reported as failure to extract a guarantee. Required full reads
mean relevant task sources and applicable skills, not every unrelated file. The fixture code
stub cannot override the current architecture guarantee. No finding was rejected. Advisor
unavailable; reviewer made no edit, test/model call, Git mutation or delegation. This is not E2.

Reviewed plan: `8adcfb2053a2225cd268f18f86ae6605b251a7986e298230905757260aade0ac`.
Rubric: `58768c5e6e326e2d91888de961f65b3dc8889f913b09a44557d40fb9fdb6f59b`.
Prompt: `09a92d73a6833a05d96bded4694440ae8d3d43a16ed9093ac9c5c27502c65c8e`.
Controls: `f69754d4c5c05b829936a9824b69b2722c7c31c2f33816436f664a1b38d61a22`.
Subsequent evidence/status updates do not change the reviewed contract.

### Procedure-clarity review

Fresh `gpt-5.6-sol`/`xhigh`, `fork_turns="none"`, reviewer
`/root/procedure_clarity_review`: **READY for the bounded experiment**. It read and reported
without edits, tests, model calls, Git mutations or delegation. Advisor unavailable. The
initial three semantic findings above were all accepted. Two further fixes rewrapped new
prose and corrected the coexistence closure row to describe D12 accurately. No finding was
rejected. The review confirms candidate and experiment readiness, not a live result or E2.

Final reviewed plan SHA-256:
`218984898cc56dae57dae280b3b2ff14172eda04ea90cc298731959b292f8afa`.
Brief: `97e4bb519a20b573e5f3f6a246fe0350883dc867516d0dc9749ac1421ccaee25`.
Candidate architecture skill:
`06362d60be6172b3553ea8ce52d4a199993f17d144730ebf1f9a90fc6ac5181b`.
Candidate plan skill:
`8b11dac933f9ead42ec5cdaf30c800a31488f694e91c00e9bfdbf62f499119f4`.
Candidate template:
`49de0fac63cd2a5c5d037e54111dca2774d747529c076cbb044c494cf575fa67`.
Diff: `0b24efbb2d9a4ed0f1bbb569d73d9b3f58ed002ade76e726ebf6be8b9c268881`.
Manifest: `45b40432744e48402569fb5a63fdf6a642a80e733f7a001d1256e51d352aad6`.
The subsequent status changes record this verdict without changing the reviewed contract.

### D24 batch review

A fresh read-only `gpt-5.6-sol`/`xhigh` agent, `/root/d24_plan_review`, reviewed the
authorization, baseline and conditional launch delta without inherited conversation. Native
session `01a0c70b-d654-71a0-8b49-775c9afddb9d` confirms its model and effort. The initial
NOT READY verdict identified contradictory current-state descriptions and missing D23/D24
closure coverage. All findings were accepted. After both corrections and four residual
current-wording fixes, the reviewer confirmed **READY for batch preparation and conditional
Terra → Sonnet launches**. It did not provide a live-test or closure verdict.

Reviewed plan hash: `bbe35a60e885a810c3a158743653f4386187df4f3e90cf839ed228198a8eaecc`.
Reviewed brief hash: `05b09c6b9e695ebb85a9d811caae47787aaba67a5e09674598a987aa567292e2`.
The batch preserves its complete native review and readiness record under S
`post-audit-b1-b3-410811bdf229/live/d24-batch-01/`. Subsequent status/evidence updates do
not change that reviewed contract. No criterion or historical result was relaxed.

### Earlier reviews

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
- **Reviewer confirmation:** not a fourth independent review. The session of the third reviewer
  reread the plan and the brief at commit `8c78d2c`, with both files modified and staged by the
  user, and judged only the changed passages. It found its three blocking and three non-blocking
  findings resolved and no new blocking finding, and gave the verdict "ready to execute". The
  corrections changed no user decision and no order of the implementation steps. They widened the
  scope in one limited way: the brief's explanatory text may be corrected when a review shows it to
  be wrong, without changing a decision line. Applied from the confirmation: that statement
  replaced the earlier claim that the scope had not changed, and the evidence about stored
  transcripts now names the artifact that was observed. Rejected: none.
- **Replan after the failed second pass:** the user decided D13 and D14. Advisor review of the
  replan, by the advisor tool of the authoring Claude session. Applied: the fallback case keeps the
  Portuguese record that the user chose and gains a defective result in which an English block is
  added without translating, so that the run is judged on behavior and not through a hole in the
  judge; the review step no longer treats the repeated second pass as a plan review; the D13 step
  names the two phrases the sentence uses; the large-case record gains a flow section; D3 left the
  list of behaviors that the runs can show. Rejected: the advisor preferred a record with a manual
  table of contents for the fallback case; the Portuguese record stays because the user chose it in
  D14, and the added defective result covers the advisor's concern.
- **Independent review of the replan:** `gpt-6-astra` at `xhigh` in Codex, a model family different
  from the advisor's, as the reviewer reported from its local metadata when it confirmed the
  corrections. The user ran it from a prompt that withheld the intended verdict and that asked for
  a fresh session; the reports do not say whether the session was fresh. It read the plan and the
  brief
  at commit `6def1b0` with both files modified, and the three skills. Verdict "ready after
  corrections": three blocking and three non-blocking findings. Blocking: the D13 row and step
  turned the two moments into exclusive sets, against the brief, where every check applies at the
  closure as today, and they left the diary check, the inspection of untracked files and diffs, and
  the delivery report unclassified; the D14 criteria accepted a new record with the right labels
  and the wrong decision, a plan that never received the decision, a small case without the D10
  list, and a fallback case that did not say what happens to the coupled index; and the D6 step and
  the completion evidence still claimed two full passes that the closure row contests. Non-blocking:
  the D14 row said "not in English" where the user chose Portuguese; the D14 closure row called the
  runs evidence for whole decisions and not for the stretches they exercise; and the completion
  evidence still treated the recording of D13 and D14 as pending. Applied: all six. The D13 row now
  names the checks that wait for the closure, and an unnamed check applies at both moments.
  Rejected: none. The review confirmed that the skills give a weaker model a textual path to the
  fallback, that the step order respects the high-risk gates, and that the verdict and the pending
  rows reflect the real state.
- **Advisor review of those corrections:** Applied: the large-case criterion no longer fails a
  correct result, because a record that replaces another carries over the rules the decision does
  not change, and a defective result that drops them was added; every fixture plan has its review
  step, and the large-case record names the owner of a check; the identity of the independent
  review is recorded as pending and not assumed; the brief uses one label for its review
  clarifications. Rejected: none. The advisor confirmed that naming the checks that wait for the
  closure expresses the partition the user chose in D13 and changes no decision.
- **Reviewer confirmation of the replan:** not another independent review. The same session reread
  the changed passages of the plan and the clarification paragraphs of the brief, at commit
  `6def1b0` with both files modified. It found its three blocking and three non-blocking findings
  resolved, the two later corrections from the advisor adequate, and no new blocking finding, and
  gave the verdict "ready to execute". One new non-blocking finding: the brief said that every new
  criterion gained a hand-made defective result, which the plan does not promise; the absence of
  the D10 list in the small-case reply, for example, has none. Applied: the brief now says that the
  plan adds defective results for the cases it lists. Rejected: none.
- **Addition of the D15 run:** advisor review, by the advisor tool of the authoring Claude session.
  The addition is not treated as a material replan: it repeats a test whose fixture, judge, and
  criteria the independent review of the replan already read, with the prompt of the fallback run,
  and it changes no skill text, gate, or decision, so it inherits that review. What did change after
  that review came out of the D14 execution and is recorded in the runs step: the one sentence on
  whole replacement in `architecture-records`, the whole-replacement criterion with its defective
  result, and the five judge corrections. Their independent review is the second pass of the
  closure. Applied: the D15 step names the transcript whose first message is the prompt, so that it
  can be compared, and freezes the judge and the builder until the run. Rejected: none.
- **Addition of the D16 sentence and run, historical gap B3:** the Claude advisor reviewed the
  addition before editing. The author classified it as non-material and omitted the inherited
  independent plan review. The D16 sentence entered `discussion-briefs`, and `run-large-4` ran,
  before that required review. The second audit rejected the classification: this was a material
  behavioral continuation of a high-risk plan, not a formatting or evidence-wording correction.
  No closure review retrospectively satisfies the missing order. The sentence, prompt comparison,
  run, hashes, and earlier corrections remain preserved evidence. Their use and remaining checks
  are delimited under B3; the user subsequently decided D17, D18, and D20, now recorded above.
- **Current B1/B2/B3 replan:** high risk inherited from this plan; B1 also changes a review gate
  directly. Advisor unavailable in the current Codex session; no advisor review is claimed or
  replaced with a self-review. The user supplied the fresh independent `gpt-5.6-sol` `xhigh`
  review under D19. The report identifies HEAD `50531033fdb16ef7f2c4362413c768a3a2143a09`,
  `master` seven commits ahead, four modified files, and no staged changes. It reports read-only
  work without tests, scripts, Git mutations, browsing, or subagents. It inspected the existing
  D16 sentence, this replan, consumers, relevant scratch artifacts, and the authorized D16
  transcript; it did not inspect every scratch path. That transcript confirms `claude-sonnet-5`,
  fixture-only edits, read-only Git, and no advisor, reviewer, or subagent in the historical run.
  This review does not retroactively satisfy the missing pre-execution order.
- **Sol verdict and disposition:** **not ready for implementation**. Three blocking corrections
  and two non-blocking findings follow. None is rejected or requires a new substantive user
  decision. The three blocking corrections are now incorporated into the B1/B2 proposals only;
  independent confirmation of those changes and the detailed test design was subsequently
  obtained in D21, after the further corrections recorded below.
  The former auditor remains the author and cannot supply that
  confirmation or the later independent closure pass.

| Sol finding | Required correction and disposition |
| --- | --- |
| Blocking: D12 order in the `discussion-briefs` consumer | Its promotion paragraph says amend and then record the plan even when amendment waits for review. Applied to the plan proposal: the B1 consumer row names the contradiction, and the proposed replacement explicitly separates D3 record → plan → review from D12 plan → review → mandatory maintenance/amendment → handoff. D21 confirms the proposal; the skill remains unchanged. |
| Blocking: B1 question-only and same-decision owner coverage | Applied to the plan: separate question-mark and trailing-w cases prohibit all state changes, plan work, review initiation, and resumption. A distinct same-decision/third-owner case holds dependent work and preserves remote-write authorization. These are planned walkthrough checks, not executed model tests. |
| Blocking: B2 preservation universe | Applied to the plan: freeze all existing S entries plus eight exact external transcripts, including D16; compare the identical path universe, hashes, types, permissions, and membership. Only the two named source edits may differ after verified backups. Every new destination, including manifests, refuses collisions. No preservation run has executed. |
| Non-blocking: large-4 does not establish executable-plan correctness | Its plan prematurely calls the old record superseded, removes the consumer protection before creating or locating the router, and relies on an unestablished assumption. Recorded in B3 and the D16 matrix; D20.2 excludes the old run from closing D16. If the future run claims full plan correctness, define a criterion and negative control for that claim before execution. |
| Non-blocking: the sequence could make D17/D18 hold B1/B2 | Clarified in B3 and the ordered continuation: only a new substantive decision raised by review could add such a gate. D17/D18/D20 are recorded evidence choices; they do not hold the bounded B1/B2 corrections after required review and a later instruction to resume implementation. |

Sol found N1/N2/N3 coherent, the B1 intention faithful but incomplete, the B2 semantic contrast
appropriate but preservation insufficient, and B3's historical-gap account correct. This revision
applies the requested plan corrections and details the test design; it does not edit their
implementation or override that historical verdict. D21 subsequently supplied independent
confirmation, including the new D18 criteria and isolated-directory limitation. Skill/source
edits and rejudging still require the user's instruction to resume.

### D21 confirmation of the revised plan

The user instructed decision promotion and review by `gpt-5.6-sol` at `xhigh`, opened here as a
subagent with `fork_turns="none"`. This replaces only the prior manual-session route for D21.
The parent author is `gpt-6-astra` at `xhigh`, as identified by the user. The reviewer receives
the authoritative plan, brief, instructions, and evidence locations, with no inherited
conversation or intended verdict. It may inspect relevant files and read-only Git state, but
may not edit, execute tests, call an advisor, or delegate. Advisor remains unavailable.
The launch call specified `model="gpt-5.6-sol"`, `reasoning_effort="xhigh"`, and
`fork_turns="none"`; it returned reviewer handle `/root/d21_sol_review`. These are the
orchestration configuration facts. The reviewer had no separate interface for auditing backend
model/effort metadata and did not claim one. This review cannot close implementation or
retrospectively repair the D16 review-order breach.

First-review baseline, verified unchanged at the review's end:

- HEAD `291e0c10b5958605499b9f4a74ce1f437ad45864`, `master` eight commits ahead, four modified
  scope files, and no staged changes.
- Plan SHA-256: `375953113086162ab0d8bfce139cd9b37eafa6910c2cb37178ba8b2192b108b5`.
- Brief SHA-256: `973887d7c3e829c09d2af7afbe7937b9b086a4f99521f4c5103fd8439746d93d`.

**First verdict: not ready for implementation.** Three blocking findings follow. All are
accepted as ordinary plan corrections; none requires a new substantive user choice. They are
corrected in this plan only. The follow-up and final confirmation are recorded below.

| D21 finding | Evidence and consequence | Plan correction |
| --- | --- | --- |
| Internal B1 ordering contradiction | `plan-implementation`, **Inspect before planning**, unconditionally requires amendment before the plan, contradicting its own D12 fallback and `architecture-records` section 7a. Fixing only the per-phase gate leaves that instruction active. | Added this internal consumer and a concrete two-order replacement covering creation or update of an existing plan. The walkthrough includes this passage; no skill edit has occurred. |
| Lost stream progress/ack | The large original record's Decision and Flow require offset commit when skipping a foreign-tenant record. Its brief changes filtering/logging/counting, not that obligation. `build_d14.py` `NEW_RECORD_TEXT`, the large judge, and proposed D18 criteria omit it. The historical controls with a new Proposed record share the omission; the block-instead variant has no replacement. | Preserve the guarantee without inventing a protocol or implemented owner; require locating and validating the responsibility before removing protection. Reassess historical controls and runs; create a corrected large base and an isolated omission control. B2 now has 26 corrected controls, four valid and 22 defective; after the follow-up below, D18 has seven content controls, one valid and six defective. D22 inherits the criterion. |
| Unproved Claude transcript sensitivity | `judge_d14.py` ignores Read/Glob/Grep destinations, does not establish call/result or terminal completeness, and uses incomplete path/command heuristics. D18's content controls cannot show that these failures are detected. | Added an independent D18 data-only Claude trace set before the live run, including authorized external instruction/skill reads, forbidden effects/reads, missing evidence, and resolved-path boundary cases. Codex readiness cannot substitute for these controls. |

The reviewer accepted the closed B2 preservation design, replayability/paraphrase contrast
subject to progress/ack repair, B3 historical gap, D20.2 disposition, and D18's explicit absent-Git
limitation. It found D22's distinct scope and schema prerequisite appropriately bounded. Its
non-blocking suggestion to include global-instruction reads alongside skill reads in the Codex
positive control is applied. No finding is rejected.

The review inspected only bounded sources and evidence, without tests, builders, judges, Git
mutation, or delegation. It confirmed the scratch inventory and examined the authorized D16
transcript, observing 34 tool calls with results and 17 Reads. The current judge ignores those
reads.
It did not inspect an unauthorized Codex history. The Codex schema remains an explicit execution
prerequisite. The author independently read the original record, fixture decision, builder,
and Claude reader before accepting the findings. The final D21 confirmation below addresses
these plan corrections; source changes and model tests remain unexecuted.

**First-delta review: not ready for implementation.** The same read-only reviewer confirmed
that the three original corrections were substantively addressed, then found three residual
gaps. Its initial and final hashes were plan
`716079b5e0f1ff3441a73a1a1e8d1812bd32dc35b5ac9536b52c7611791af3e0` and brief
`46dbc9433eaccde8cce0edebf1eb5241bdc6066c84a5ba8c0c4c49a30abfce77`, with the same HEAD and
working-tree status. No files or Git state were changed by the review. All three findings are
accepted as ordinary plan corrections; none requires a new user decision.

| Residual finding | Applied plan correction confirmed in the final D21 check |
| --- | --- |
| Historical rows and matrix still asserted complete large-case conformance | Qualified all affected execution and D14/D15/D16 matrix rows as historical assessments limited to observed properties. Removed current claims of every criterion passing or exactly one defect. The original logs remain unchanged; all large runs require progress/ack reassessment under B2. D15's verified status covers its authorized attempt and recorded failure only. |
| D18 did not isolate the plan's progress/ack prerequisite | Added a sixth negative: the record preserves progress/ack, but the plan omits locating/validating its responsible path. The complementary fifth negative preserves the plan prerequisite while omitting the record guarantee. The suite and brief now specify seven content controls. |
| Codex sensitivity did not exercise every declared obligation | The Codex set now reconstructs the full D18 effect/read/completeness/path-boundary control list in its own observed schema, including shell writes, relative/sibling-prefix/symlink cases and terminal completion; it additionally covers a forbidden nested write and a permitted nested write. No Claude verdict is reused as Codex evidence. |

The next review accepted this second delta except for one remaining historical label that said
large-2 failed on exactly one criterion. The author replaced it with the reviewer's bounded
wording: the historical assessment identified the prohibited advisor call as a failing
criterion, not a skill defect, and progress/ack had not been assessed. No old log or run changed.

**Final D21 verdict: ready for implementation**, subject to the user's instruction to resume
and the existing execution prerequisites. The same independent reviewer verified the only
remaining condition through a read-only exact-text and hash check:

- Final reviewed plan SHA-256: `f740a94f8deebfa457de5dbac9ed07835b8f4cc7372a73801e8eb3c6a65374ea`.
- Reversing only that one sentence in memory recovered the preceding reviewed plan SHA-256,
  `978ef3248253c97099e29b82acc23f0bf75351de9f849340cea2efb663089e6a`.
- The reviewed brief was unchanged at
  `a5126048a0647fdab565f59a2dd70fc41b9d778fe24db446f4a283945ce21505`.
- HEAD, branch, four pre-existing modifications, and the empty index were unchanged. The
  reviewer made no file or Git mutation in any pass. Follow-ups reused the same independent
  reviewer's context and stable source evidence; they were not new implementation audits.

Subsequent edits only record this verdict and resolve the brief/plan review status. They change
no reviewed implementation requirement or test criterion. D21 is verified as plan readiness;
B1/B2 source corrections, all control execution, D18/D22 runs, and implementation closure remain
pending. No finding was rejected, and no new user decision was needed for these plan repairs.

## Replan conditions

- A reviewer finds that the D3 exception weakens a review or authorization gate beyond its stated
  bounds. The first review triggered the earlier form of this condition.
- `codex-claude-loop`, a template, or another shared skill contradicts D1, D4, or D7.
- A change to the global instructions turns out to be necessary.
- The forward-test exposes a defect that needs a user decision; it then becomes a new brief item.

## Completion evidence

- T1's exact reviewed two-file correction is installed, has focused structural and author
  semantic validation, and received an independent source-conformance verdict. T2 is recorded as
  deferred. Neither changes the unresolved full-flow or E2 obligations; the index-byte check
  remains failed with its narrow limitation recorded above.
- The four-skill source review and three requested comparative extraction attempts are complete.
  Terra xhigh, Sol high and Opus 5/high preserve the progress obligation but each fails the full
  frozen rubric for the distinct reasons above. Source defects and execution misses are separated;
  no skill was edited, no reroll made, and no full recording acceptance or E2 closure claimed.
- The single reviewed guarantee-extraction diagnostic is complete with FAIL: current-source
  identification passed, but the future progress obligation and its validation were omitted.
  Lifecycle wording and the skipped mandatory documentation skill fail separately. Full native
  evidence and effects/preservation checks are retained; skills and old evidence are unchanged.
- B1 source wording, consumer compatibility and eleven author rule scenarios are verified.
  The D16 reply sentence is retained. Structural checks do not prove future model behavior.
- B2 preservation, corrected control sensitivity and historical reassessment are complete.
  New artifacts and limitations are listed in **Current corrective execution evidence**.
  Large-4 remains history only; no old run proves the corrected B1 behavior.
- The reviewed procedure-clarity experiment is complete: canonical candidate applied,
  structural/consumer checks passed, and both fresh Sonnet xhigh arms assessed as FAIL.
  Current source hashes and full effects evidence are retained; the progress guarantee and
  its plan prerequisite remain the behavioral failure. See the paired-result assessment.
- D21 confirmed the replan before this continuation. The actual completed Codex transcript
  subsequently found for that reviewer confirms Sol/xhigh and supplies the D22 reader schema.
- D18 was assessed as FAIL at actual Sonnet 5/high, with content failures and launch deviations
  recorded separately. D24 preserved it and added Terra xhigh FAIL plus a Sonnet xhigh CLI
  setup failure: required global Read denied. The interactive Sonnet 5/xhigh attempt then
  completed with valid access/capture but failed whole-replacement and plan-progress criteria.
  Sources stayed frozen. E3 is resolved; E2 keeps the brief open, with no pending recording. Final author and
  independent closure audits remain outstanding.

## Closure audit

D22 is approved and recorded. Its assessment obligation is included below before any preparation
or run. Missing prerequisites or insufficient evidence leave it unresolved; approval is not
execution or a passing result.

D23/D24 extend the execution contract and have their own rows. Original D18/D22 run ceilings
and user-opened Sonnet routing below describe the earlier authorization; the current batch
section governs new runs. Every new attempt must be included in closure, including failures.

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | T1: implement the two textual corrections within the authorized boundary, preserving compatibility topology, whole-replacement guarantees, and all inherited gates. | This plan; documentation; architecture record template and section 7a; plan and discussion consumers. | Exact reviewed candidates installed; four package checks and eight author scenarios passed. Fresh Sol xhigh source-conformance verdict: CONFORMS, no correction required. Failed index-byte preservation remains recorded separately; no full-flow acceptance claimed. |
| verified | T2: defer broad phase reorganization without turning it into a new closure requirement. | This plan and current closure brief. | Both carry the user's deferral; T1 changes only its two authorized source hunks. Reconsideration is not execution authorization. |
| verified | Review the four central skills and assess one fresh extraction each with Terra xhigh, Sol high and Opus high. | Current continuation and frozen comparison rubric. | Source review found R1/R2 plus ergonomic risks. All three retain progress; all fail other mandatory criteria. Complete native traces, source delivery, effect audits and preservation checks retained. Verified completion of this bounded review, not approval of behavior or final closure. |
| verified | Execute and assess one read-only guarantee-extraction diagnostic with unchanged skills and pre-reviewed criteria. | This plan and brief; frozen prompt/rubric/controls; native evidence and assessments. | Sol review READY; controls behaved as expected; one Sonnet5/xhigh task completed with classification FAIL, validation FAIL and complete-task FAIL. All nine calls/results and 86 post-exit events classified; source, fixture and historical preservation verified. The separate mechanical reader retains 88 UNVERIFIED rows. Verified means this diagnostic and its assessment are complete, not behavioral acceptance or E2. |
| verified | Execute and assess the bounded procedure-clarity experiment without weakening existing rules or criteria. | This plan; architecture-records and its template; plan-implementation; native transcripts and source manifests. | Sol approved the corrected proposal before application/runs. Four package validations and eleven author scenarios pass. A FAIL and B FAIL are preserved with complete author effects classifications and separate mechanical UNVERIFIED results. Verified here means the experiment and assessment are complete; behavioral acceptance, Terra and independent E2 remain unresolved. |
| verified | D1: a decision recorded in only one of its owners keeps `registro pendente` for the other, the brief stays open, and the reply names what was left out and why. | `discussion-briefs`; the per-phase check in `plan-implementation`. | B1 corrected both recording orders and passed the eleven author scenarios; see current corrective evidence. The audit originally found that the per-phase gate could block recording itself. Historical evidence: `discussion-briefs`, **Record decisions and promote them**: owners are named in the reply, the item keeps the marker for the owner that lacks the decision, the brief is not concluded, and the reply says what was left out; **Close the brief** requires every owner. The same section now tells the agent to say in the reply that the decision is approved and recorded and that the plan review still comes before any code; that sentence was added during execution, before the D6 runs, because the D6 reply criterion depends on it. The per-phase check in `plan-implementation` now waits for every owner. |
| verified | Decision, promotion, and execution remain three separate operations. | `discussion-briefs`. | `discussion-briefs` keeps "A decision changes only the brief" unchanged, and the promotion paragraph still says that promotion never includes implementing the decision. Both D6 runs recorded without touching code. |
| verified | D2 small variant: block placement, one per rule, no diary content, the rule above unmarked, and removal at closure even when the lifecycle state does not change. | `architecture-records` procedure, closure pass, and validation list. | `architecture-records` section 7a, amendment-block bullet, for placement, label, one per rule, unmarked rule, and no diary content; the last paragraph of 7a, section 10, and the new validation bullet in section 11 for removal at closure regardless of lifecycle state. Both D6 runs exercised the creation of the block; its removal at closure was verified by inspection only. |
| verified | D2 large variant: Proposed record plus notice line; the old record becomes Superseded only when the new one is Implemented; never two texts authoritative for the same scope and phase. | `architecture-records`. | `architecture-records` section 7a, new-record bullet; the qualified `Superseded` bullet in section 4; and the lifecycle paragraph of the index template. After the first large run of D14 the bullet also says that the new record replaces the old one whole and carries over the rules the decision does not change. The form of the new record and its notice line were exercised by the D14 large case, in its own row; the supersession at the closure stays verified by inspection. |
| verified | D10: the block is the default; the agent lists the places that change, shows the list with the chosen form, and asks when in doubt; a short list of rules gives the block and a long list, or one with a flow section, diagram, or table, gives the new record; when much changes without changing the design the agent uses blocks and asks first; no fixed count; the choice is reversible; the guard that a record is created only when the design changes is kept; the incident criterion is unchanged and not contradicted; two generic examples exist. Verified by inspection, because D6 does not exercise it. | `architecture-records`. | `architecture-records` section 7a, the paragraph that starts "Choose the form by its purpose" and the two generic examples after it. Section 7 is unchanged in the diff. Verified by inspection, as planned. The D14 and D16 runs later exercised the choice between the two forms and the list shown in chat, in their own rows; the rest of this row stays verified by inspection. |
| verified | The D3 exception and its bounds read the same in `plan-implementation` and `architecture-records`, including the index entry and the fallback to the ordinary order when another obligation of `architecture-records` needs a change outside the bounds; every other step still waits for the plan review; instruction-file synchronization waits for implementation. | Both skills. | B1 now explicitly permits bounded D3 recording with existing or new plans; the author walkthrough passed. Independent closure remains pending. Historical evidence: `architecture-records` section 7a, the paragraph that starts "This recording precedes", and `plan-implementation`, the paragraph "Step 1 has one exception": the same bounds, the index entry, the fallback, and the instruction file left untouched; step 1 itself is unchanged for every other step. |
| verified | D12: the fallback is stated beside the D3 bounds in both skills, with its two examples; under it the brief item keeps the pending marker for the record and the maintenance and the amendment are plan steps after the plan review; the per-phase exemption covers only the promotion unit and only the pending marker it resolves, keeps the recording instruction required, leaves dependent work and other pending decisions under the check, and keeps the D4 session responsible. | `plan-implementation`; `architecture-records`; `discussion-briefs`. | B1 now explicitly permits D12 preparation/review with the marker and bounds the later maintenance/recording unit; the author walkthrough passed. Historical evidence: The fallback, with its two examples and its reason, closes the two paragraphs named in the row above. The exemption is in the per-phase paragraph of `plan-implementation`: only the step that records the decision in the owner that still lacks it, with its mandatory maintenance, after the plan review; the recording instruction, other pending decisions, dependent work, and the D4 session are stated there. `discussion-briefs` keeps the marker for the owner that lacks the decision. |
| verified | Authority while the current rule and the amendment coexist is defined by scope and phase. | `architecture-records`; `plan-implementation`. | `architecture-records` section 7a, the paragraph that starts "While both texts coexist", and the qualified sentence in section 4. `plan-implementation` derives the bounded-path plan from the amended record; D12 first plans and reviews while that record is unchanged, then reconciles after the authorized maintenance/amendment. Current authority is not transferred early. |
| verified | D4: the amending session is named, and `codex-claude-loop` stays compatible. | `plan-implementation`; `architecture-records`; `codex-claude-loop`. | `plan-implementation`, the paragraph added under **Inspect before planning** and the last sentence of the per-phase check; `architecture-records` section 7a, the paragraph that starts "The session that conducted the discussion", which now names the planning handoff and points at section 11; `codex-claude-loop` step 3. The collision that the first second pass found, between this handoff and the unconditional list of section 11, is resolved by D13, in its own row. |
| verified | D5: the sentence is replaced and points at text that exists. | `discussion-briefs`. | The old sentence is gone from `discussion-briefs`; the new paragraph points at the deliberate-decision procedure of `architecture-records`, which exists as section 7a and is named in that skill's description and registry entry. |
| verified | D7: the check exists in the proportional closure and in the completion gates, for full and compact plans; a pending marker blocks; an open item is reported to the user and noted in the plan; no existing gate is relaxed. | `plan-implementation`. | `plan-implementation`, first paragraph of **Close work proportionally**, and the brief check named in the compact, bounded-additive, and high-risk gates under **Completion gates**; both plan templates carry a brief-check line and condition. |
| verified | D8: per-section prefixes, identifier stability, the change-of-nature rule, and the identifiers of existing briefs unchanged. | `discussion-briefs` and its template. | `discussion-briefs`, the numbering paragraph under **Write each item for a reader outside the work**, including the change-of-nature rule and the sentence that keeps the numbering of existing briefs; the template uses `D1`, `T1`, and `E1`. No existing brief was renumbered. |
| verified | D9: every requested field exists in the template's work item. | The brief template. | The template's `T1` item has the question, the description with a concrete example, what happens under each answer, cost and risk, and the recommendation; the skill's new bullet requires the same depth. |
| verified | D6: the two runs are recorded per criterion, with their limits and not as full passes; the whole-record comparison and the transcript check were made; each hand-made defective result failed as expected; the fixtures were isolated and fresh; any property left unverified is reported as such. The validation the user chose for the limits is D14, in its own row. | Scratchpad fixtures. | Judged per criterion. Mechanical, by the judge on files, snapshots, and transcripts: both runs pass for the record, the brief, the code, the Git directory, the edited paths, and Git commands. The judge checks only that the plan changed, and it first ignored server-side tool calls; it now reads them. By reading: in both runs the block states the user's decision and the reply separates the recorded decision from the implementation and names the plan review before code. Limits: run 1 called its advisor after its edits, against the instruction to work alone, and the content of that call is encrypted; run 2 updated the plan's step but wrote the review-before-code order only in the reply, so "the plan carries the sequence" holds for it only in the reading of the user's D6 text. The hand-made correct result proves only the mechanical subset. |
| verified | D13: section 11 of `architecture-records` says which checks apply at the planning handoff and which at the closure of the implementation; every check applies at the closure, the form and delivery checks apply at the planning handoff too, every bullet is accounted for against the D13 row, and none is waived; section 7a uses the same word for that handoff. | `architecture-records`. | The sentence at the start of section 11 names the two moments with the phrases "the planning handoff" and "the closure of the implementation", applies every check at the closure, and at the planning handoff excepts by name the nine checks that presuppose a finished implementation, so that a check it does not name applies at both moments. Each of the seventeen bullets was checked against the D13 row: the nine named ones wait for the closure, the amendment bullet splits into the form of a block, at both moments, and the removal of a closed block or notice, at the closure, and the rest apply at both. Section 7a names the planning handoff and points at section 11. The validator passes. |
| unresolved | D14: each of the three cases meets every criterion in an accepted run, judged per criterion, with the large-case evidence route governed by D18/D20.2; each hand-made correct result passed and each defective one failed; the versions used by the runs are recorded, with D13 in every D14 run; the transcripts are named; any property left unverified is reported as such. The runs exercise these stretches only: the naming of the owners and the marker kept for an owner that lacks the decision (D1); the form of the amendment block and the form of the new record with its notice line (D2); the choice between the two forms, with the list shown (D10); and the stop before the amendment, with the steps planned after the review (D12). They do not exercise the unit that later amends the record under the D12 exemption, the removal of a block or notice at the closure, the supersession of the old record, the order that D3 sets between the amendment and the plan review, the D4 handoff, or the D7 check; those require inspection, with D3/D12 currently unresolved under B1; no further run is implied. | Scratchpad fixtures and judges. | Reopened by the second audit: B2 disproves large-6 sensitivity; B3 records the missed review, and D20.2 excludes large-4 from closing D16. The new D18 attempt was assessed as FAIL, as recorded under current evidence. Historical evidence: This row first read "each of the three runs met every criterion of its case" and stood pending. It was restated as "each of the three cases", because D14 starts a case over after a skill defect and the user authorized one more run of the large case in D15 and another in D16; the criteria of the cases did not change, and a failed run stays recorded as failed. The small case and the fallback case met every criterion in their first runs, the small one with the limit recorded in the runs step. The historical assessment credited the fourth large run with the then-observed criteria, as recorded in D16; D21 found missing progress/ack coverage and that broad conformance claim is not accepted. Its earlier runs are recorded as failed and are not evidence of a pass: the first failed by reading on a skill defect that was then corrected, the second met every file criterion before its advisor call but made that call, which the prompt forbade, and the third is in the D15 row. The old log verdicts remain, but large-6 did not test the claimed semantic defect, and every judge change is listed with its reason in the step of the run that exposed it. The small run preceded the whole-replacement sentence, which its case does not use. Both the small and fallback runs preceded D16; only large-4 used D16. They are not behavioral evidence for that final sentence or the proposed B1 correction. Transcripts and judge logs are named in the runs step. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. |
| verified | D15: one more run of the large case was made with the stronger advisor prohibition and the unchanged fixture, judge, and criteria; its result is recorded per criterion; a miss is recorded as a failed run and not as a pass, and a miss that D15 does not provide for went to the user; the transcript is named. | Scratchpad fixture and judge. | This row first required the run to meet every criterion or to fall back as D15 says, and it stood unresolved because neither happened. It was restated after the user decided D16, which settles what that miss leads to; the criteria of the large case did not change, and the historically credited run is in D16, subject to the later B2/B3/D21 limits. The run was made as the step describes and did not call the advisor, so the fallback of D15 does not apply. The historical assessment identified a missing list of changed places in the reply; it did not assess progress/ack, so that finding is not established as the only defect. It is recorded as a failed run. Transcript, prompt, judge log, and the one judge change are named in the step. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. Verified here means that the single authorized attempt occurred and its observed failure was recorded, not that it had only one defect or achieved full conformance. |
| unresolved | D16: `discussion-briefs` carries the sentence in the promotion paragraph the user chose, with its reason and without restating the criterion of `architecture-records`; preserve the single original D16 run, its frozen inputs, transcript, results, and limits as history. Under D20.2 it cannot close this obligation: assess the separately authorized D18 run after review and approved corrections against the applicable large-case criteria, including the list in the reply; insufficient evidence leaves the obligation unresolved. | `discussion-briefs`; `architecture-records` section 7a as the owner of the rule; scratchpad fixture and judge. | Reopened by the second audit: B2 reopens judge sensitivity. B3 records the missing inherited review; D20.2 excludes large-4 from closing this obligation, and D18 supplied a failed Sonnet high attempt; its reply meets the list criterion but its full result cannot close this obligation. Sol also found that the historical plan removes consumer protection before creating or locating the router and relies on an unestablished assumption; it does not prove executable-plan correctness. Historical evidence: `discussion-briefs`, **Record decisions and promote them**, the paragraph that starts "When the decision changes an approved architecture record": the sentence after the one about saying that the decision is approved and recorded. It points at the procedure of `architecture-records`, whose section 7a keeps the rule and its criterion, and the list of **Keep chat a projection** is unchanged, as the user chose. The historical assessment credited the then-observed file and reply criteria; the reply contains the list, form, and reason, so the specific missing-list fallback does not apply. This is not full semantic conformance: the B2 reassessment found progress/ack absent, and D20.2 excludes the run from closing D16. The run, its transcript and session, the prompt comparison, the hashes, the one judge change with its reason and the judging again of every hand-made result and every run, the observations, and the two limits are in the step. D21 qualification: the large-case observations and log verdicts above are historical and limited to the properties then assessed. All historical large controls with a new Proposed record share the progress/ack omission; the block-instead variant fails the required form without removing the old acknowledgement; every large run requires the B2 semantic reassessment before a complete verdict can be claimed. No old artifact or log is rewritten. |
| verified | D17 and D20: preserve the original deferral, then exclude large-4 as evidence to close D16 under option 2. | This plan and its brief. | Both choices are recorded on the user’s explicit promotion instruction. Historical files and observations remain intact; old-run acceptance cannot be inferred from their preservation or rejudging. |
| unresolved | D18: one additional large-case run, after review and approved corrections, in an independent session opened by the user, with model, request, criteria, and limits recorded before execution; no advisor, nested subagents, automatic retries, or other cases. | This plan, preserved Sonnet output and complete native transcript, and independent review. | Attempt consumed and assessed as FAIL: Sonnet 5/high, content defects and launch deviations. Reply criterion passes; no helper or Git mutation observed. Frozen-reader verdict UNVERIFIED. Complete assessment and limitations under current evidence; further runs follow D24 without weakening criteria. |
| verified | D21: independent confirmation of the revised replan and detailed test design before implementation. | Fresh read-only Sol xhigh subagent; this plan and its brief. | The reviewer confirmed readiness after the internal B1 consumer, progress/ack preservation, historical qualifications, seven D18 content controls, Claude/Codex transcript controls, and final historical-label correction. Exact baselines and confirmation are under **Plan review**. This verifies the plan, not implemented behavior or a live-test result. |
| unresolved | Preserve stream progress/ack throughout large-case whole replacement; establish the responsible path before removing protection, and prove both content and transcript assessment sensitivity before D18/D22. | Original record, corrected B2 controls, D18/D22 criteria and readers. | D21 reopened this missing semantic coverage and identified the shared defect in historical large controls. Corrected controls, historical reassessment and both trace readers are complete. All later live results are retained; the A/B pair still fails progress preservation and the plan prerequisite. The later extraction-only diagnostic also fails future preservation and validation despite identifying the old offset commit. Successful complete-task evidence remains absent. |
| unresolved | D22: Codex assessment preparation and one complementary Terra xhigh attempt after review, corrections, controls, and Sonnet's terminal result, with separate per-criterion evidence and no automatic retry or substitution. | Author, Codex transcript reader, isolated Terra fixture, complete trace, and independent review. | Terra xhigh completed under D24 with FAIL: architecture alone updated, plan/brief unchanged, progress guarantee omitted. Native events and outputs retained; initial task is encrypted in native caller/callee histories, so exact native plaintext remains UNVERIFIED. No successful Terra result is claimed. |
| unresolved | D23/D24: use current instructions in a newly frozen Terra→Sonnet batch; verify the conditional CLI route before task work; preserve complete native evidence and every failure; further attempts have diagnostic purpose and retain the same criteria and independent closure. | This plan, brief, batch manifests, launch metadata, full transcripts, inventories and per-criterion assessments. | Independent review confirmed readiness. Terra FAIL; noninteractive Sonnet setup invalid, an author preflight defect. Interactive Sonnet xhigh then completed with valid launch/capture and content FAIL, all evidence preserved under d24-manual-02. E3 is resolved. The subsequent reviewed procedure-clarity pair finished A FAIL/B FAIL, and the later extraction-only diagnostic finished FAIL with full evidence. It is a separate diagnostic, not another recording run. Final validation and closure remain pending. |
| verified | D19: receipt of the independent replan review. | This plan and its brief. | The user supplied the earlier fresh Sol xhigh report, not ready for implementation. Its corrections and subsequent findings were confirmed separately under D21. D19 report delivery itself is not implementation readiness or closure. |
| verified | Every listed consumer was inspected and either changed or justified as unchanged. | Templates, `codex-claude-loop`, registry entries, frontmatter descriptions. | The B1 compatibility pass is complete; both internal ordering paragraphs were corrected, with unchanged consumers justified in b1-walkthrough.json. Historical evidence: Changed: `codex-claude-loop` step 3, the opening of `plan-implementation`, `documentation`, `implementation-plans/README.md`, both plan templates, the architecture index template, the brief template, and, as a correction made after the advisor checked the edits, the description of `architecture-records` with its registry entry in `.codex/AGENTS.md`. Unchanged with a reason: the architecture record template and the descriptions of `plan-implementation` and `discussion-briefs`. |
| verified | D11: `architecture-records` states that workflow rules of shared skills and their reasons live in the skills; `documentation` does not contradict it; `plan-implementation` and `implementation-plans/README.md` do not contradict it either; each new rule carries its reason in a sentence; the rejected alternatives of every decision are kept in this plan and in the brief; the per-phase check does not wait for skill text that the plan itself will write; no architecture record or directory was created. | `architecture-records`; `documentation`; `plan-implementation`; `implementation-plans/README.md`; the three skills. | `architecture-records` section 2, new paragraph; one clause each in the opening of `plan-implementation`, in `documentation`, and in `implementation-plans/README.md`; every new rule states its reason in a sentence, the D12 fallback included; the rejected alternatives are listed in this plan and explained in the brief; the owner definition keeps the per-phase check from waiting for skill text; the repository has no `architecture/` directory. |
| unresolved | The validation step ran in full: each touched package passed the validator, the width scan and `git diff --check` were clean, and the cross-skill reread for contradictions was done and recorded, knowing that the validator checks structure only. | The three skills, the templates, and any consumer that changed. | Reopened by the second audit: The structural logs remain evidence of their own checks, but B1/B2/B3 disprove overall conformance and require focused revalidation. Historical evidence: Rerun after the second pass against commit `6def1b0`, which holds the same skill text as `cddbba8`: `quick_validate.py` on `architecture-records`, `plan-implementation`, `discussion-briefs` through both of its paths, `codex-claude-loop`, and `documentation`; a scan of every Markdown file changed since `b846769` for lines over 100 characters outside tables, headings, and code blocks, and for trailing whitespace; and `git diff --check b846769 HEAD`. All clean. The output is in `validation-after-second-pass.log` in the session scratchpad, which is temporary; the commands above reproduce it. The cross-skill reread did not find the handoff collision that the second pass found, so its claim of no contradiction was wrong. Rerun again after D13 and the D14 correction, on the working tree over commit `5053103`: the same validators on the five packages and on the two symlinked paths, the width and whitespace scan of the thirteen Markdown files of this plan's scope changed since `b846769`, and `git diff --check` for the working tree and for that range limited to the scope paths. All clean; the output is `validation-d13-d14.log` in the session scratchpad. The unrestricted scan also lists `README.md` and `.codex/config.toml`, which the user changed in unrelated commits, and two lines inside an indented code block of `plan-implementation` that predate this plan. Rerun in full after D16, on the working tree over the same commit, with this plan and the brief in their state of that moment: the validators on the five packages and on the three main skills through their symlinked paths, the width and whitespace scan of the same thirteen Markdown files, `git diff --check` for the working tree and for the range limited to the scope paths, and an empty staged diff. Clean, apart from the same two lines of that code block; the output is `validation-d16.log`, and `validation-d16-sentence.log` holds the check made right after the sentence. The cross-skill reread after D16 covered the sentence against `architecture-records` section 7a, which owns the rule and words it the same way, and against the list of **Keep chat a projection**, which it does not contradict. |
| verified | Only in-scope files changed; no Git mutation by this continuation; earlier commits remain in the baseline. | Working tree. | The changed files are the five skills named in the scope, four templates, `.codex/AGENTS.md` for the one registry entry, `implementation-plans/README.md`, this plan, and the brief; the second pass traced every changed passage to a decision row or scope item. The implementer staged and committed nothing. The user committed the changes as `cddbba8`. After D13 and the D14 correction the working tree held three modified files, all in scope: `architecture-records/SKILL.md`, this plan, and the brief. After D16 it holds a fourth, also in scope: `discussion-briefs/SKILL.md`, with the one sentence. The implementer staged and committed nothing. |
| pending | Changes made after the audit were revalidated, and the brief's links were updated when this plan moved. | This plan and the brief. | Pending. It waits for the new independent second pass: its findings may change in-scope files, and this plan moves only after it passes. |

- Architecture to implementation: each decision row D1 to D13, the D16 sentence, and each invariant
  reach skill text through the rows above, and the consumers named in the scope were inspected and
  changed or justified. D14, D15, and the run of D16 are validation decisions and reach the runs
  step and their closure rows. D17/D18/D20 reach the B3 disposition, ordered continuation, and
  evidence rows; D21/D22 reach the independent-review route, Codex assessment design, and their
  closure rows. D23/D24 reach the current batch contract, source manifest, launch/capture checks,
  attempt ledger and separate closure row. Recording these decisions does not mark validation verified.
- Implementation to authority: every changed file is named in the scope and traces to a decision
  row; the edits outside the three main skills are the one-sentence consumer changes recorded in
  the consumer-analysis step. New manifests, launch artifacts and assessments trace to D23/D24;
  any skill correction requires its own authenticated defect and inherited review, except the
  explicitly accepted presentation/clarification experiment above, which received its inherited
  review without claiming a missing rule. Its three-source delta traces to that continuation.

### Final conformance verdict

- **Verdict:** Failed. The second audit found B1/B2/B3 and N1/N2/N3. The corrective implementation
now covers B1/B2 and test preparation, but live evidence
  and independent closure remain outstanding; no replacement conformance verdict is issued.
- **Second pass:** Independent. `gpt-5.6-sol` at `xhigh`, in a fresh read-only Codex session opened
  by the user, at commit `cddbba8` with a clean tree. It differs from the advisor, which is the
  authoring Claude session's advisor tool, and from `gpt-6-astra`, which made the plan reviews.
  Verdict: Failed, with three blocking and four non-blocking findings. Blocking: the handoff that
  D4 requires collides with the unconditional "Before handoff" checks of `architecture-records`,
  which needs a user decision (brief item D13); the D6 evidence was overstated, because the judge
  checks only that the plan changed, run 2 did not write the review order in its plan, and run 1
  called its advisor, and accepting those limits or rerunning needs a user decision (brief item
  D14); and the validation had no auditable artifact, which was corrected by rerunning it with a
  saved log. Non-blocking, all corrected: the Git state sentence, the brief's summary that still
  described the work as not started, the unreported advisor call, and a matrix row that credited
  D6 with exercising the removal of the block. It confirmed the reverse trace of every changed
  passage, the fidelity of the twelve decision lines, the bounds of the D3 exception, the D12
  fallback and exemption, and the mechanical results of both runs and of the five defective
  controls.
- **Second closure audit actually performed:** `gpt-6-astra` at `xhigh`, as identified by the
  user, read-only, at HEAD `50531033fdb16ef7f2c4362413c768a3a2143a09` with four in-scope
  working-tree modifications. It was not the Sol session previously planned. It was independent
  of implementation at that time, but used the same model as the plan reviews, leaving a
  correlated-model blind-spot risk. Its report in this conversation is the source for the six
  findings recorded in the material replan. It did not rerun tests or edit artifacts.
- **Authorship transition:** that auditor now authors the continuation at the user's instruction.
  It cannot review its own replan independently or perform the next second pass. Sol xhigh
  delivered the user-opened review under D19 with a not-ready verdict. The user now authorizes
  the D21 confirmation through a fresh Sol xhigh subagent. Its initial findings were corrected;
  its final verdict confirms readiness of the plan, without claiming implemented behavior.
  The later independent closure pass remains a separate fresh session opened by the user.
- **Unresolved requirements:** D1/D3/D12 and consumer compatibility are verified by current source
reading.
  D14/D16/D18 remain unresolved after the failed Sonnet high attempt. D23/D24 authorize the new
  baseline; Terra failed and noninteractive Sonnet lacked shared-skill access. Interactive Sonnet
  xhigh subsequently failed two content criteria with valid access/capture; E3 is resolved.
  The subsequent procedure-clarity A/B pair also failed progress preservation and its plan
  prerequisite under both versions. The candidate has local structural/consumer validation,
  not behavioral acceptance. Final validation, independent
  closure and the eventual move remain pending. B1/B2 local corrections are complete; B3 keeps
  its historical breach. D20.2 still excludes large-4 from closing D16. No completion is claimed.
- **Brief check:** the original sixteen decision items retain their exact decision paragraphs and
  have no pending recording marker. D17/D18/D20/D21/D22 are recorded in their only owner, this plan;
  D19 is resolved by receipt of the report and D21 by the final readiness confirmation. The brief
  is open for E2, with zero undecided choices, one external dependency and zero pending recording
  owners. D23/D24 are recorded in this plan. E1 is resolved as receipt only. D22 retains the assessment
  obligation above. T1 and T2 from the current closure brief are recorded in this sole owner:
  T1's bounded source task is complete and T2 is deferred. Neither carries a pending marker.
  D7 does not waive implementation or required-validation gates.
