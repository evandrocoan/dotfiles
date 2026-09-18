# Implementation plan: apply the reviewed corrections to the discussion-briefs skill

**Status:** Complete
**Mode:** Plan and execute
**Risk:** Non-trivial local and reversible

The changes are wording edits in shared skills plus one `.gitignore` allowlist rule. No edit relaxes
an authorization, safety, review, or closure gate: the Git sentences replaced under D7 and D5.10
repeat the always-loaded global Git authorization section, which stays the governing rule for
Claude, Codex, and Copilot, and D4.1 and D5.7 only tighten the new skill.

## Outcome and scope

- Outcome: every decision the user recorded in
  [the brief](../briefs/discussion-briefs-review.md) is applied to its owning file, the four touched
  skill packages validate, and the forward-test under D6 has run with its observations recorded.
- In scope: `.claude/skills/discussion-briefs/` (`SKILL.md` and the template), the registry entry
  for `discussion-briefs` in `.codex/AGENTS.md`, three narrow insertions in
  `.claude/skills/plan-implementation/SKILL.md`, one sentence each in
  `.claude/skills/architecture-records/SKILL.md` and `.claude/skills/codex-claude-loop/SKILL.md`,
  two allowlist rules in `.gitignore`, and the brief itself.
- Out of scope: any Git staging, commit, or push; every other sentence of the three sibling
  skills; the global question-only gate; the plan templates; new skills.
- Authority: the user's decisions below, stated in chat and noted in the brief; the global
  instructions in `.codex/AGENTS.md`; `skill-creator` and `documentation` for skill text.

## Governing decisions absorbed from the brief

| Brief item | Decision |
| --- | --- |
| D1 | Create a brief unprompted only for points waiting on the user: a decision, an authorization, or an external dependency. Explanation-only requests stay in chat, subagents and reviewers never create a brief, and an explicit user request always creates one. Update the frontmatter and the registry entry to match. |
| D2 | `plan-implementation` shows `briefs/` in its root layout, reads a same-subject brief before planning and absorbs its decided items, and fixes brief links when a plan moves. `discussion-briefs` tells the user in chat when it edits the plan root's README. |
| D3 | Allowlist `implementation-plans/briefs/` in this repository's `.gitignore`. |
| D4.1 | Promotion means recording a decision in the plan, architecture record, or issue, never in code or configuration, and never implementing it. It follows the owner's skill, including any plan, review, or user instruction required. Until recorded, the item stays `decidido` with the marker `registro pendente`. A plan under `completed/` counts as no owner. |
| D4.2 | When a brief is warranted in a question-only turn, do not create it; answer with a short self-contained summary and offer the brief for a later turn. |
| D4.3 | Apply pending rewrites only at the next non-question instruction about the brief or its subject, and list every item with an unapplied rewrite in each question-only reply. |
| D4.4 | Add the state `resolvido` for dependency items and accept it in the closing condition. |
| D4.5 | Only the formatting rules of `documentation` apply to a brief: no table of contents and no commit-pinned links. Remove the item count from the template summary. |
| D4.6 | Number items sequentially only; cite plan or record identifiers inside the item text and define them in the glossary; the brief's own item numbers need no glossary entry. |
| D5.1 | Rename the closing section to "Decididos e descartados" and keep a dropped item there in one line. |
| D5.2 | Remove the state `em discussão` from items. |
| D5.3 | Show the `Decisão` line only when a decision exists. |
| D5.4 | Separate the template header fields with blank lines. |
| D5.5 | State in the template preamble that nothing in the brief authorizes work. |
| D5.6 | Rename the heading "Decisões suas" to "Decisões que dependem de você". |
| D5.7 | The brief ranks below every authority layer and is never an authority. A user decision noted there draws its authority from the user's statement and stays marked pending until its owner records it; in every other disagreement, correct the brief. |
| D5.8 | With another plan location, `briefs/` sits beside the lifecycle directories; without a plan directory, use the default root; never place a brief inside an architecture directory. |
| D5.9 | Let `Alimenta` list several targets, and show `não verificado` and a verification date in the template. |
| D5.10 | Replace the stage-or-commit sentence with the wording `plan-implementation` uses for plans. |
| D7 | Replace the copied Git sentence in `architecture-records` and in `codex-claude-loop` with the same pattern: name the artifact-specific temptation, then defer to the user's requested Git outcome and the repository convention. |
| D8 | A decision changes only the brief: the item becomes `decidido` with `registro pendente`, and no plan, architecture record, issue, or code changes in that turn. Promotion happens only on the user's instruction, and the chat reply says how many decisions still carry `registro pendente`. As mitigation, `plan-implementation` checks a same-subject brief for such items before each phase. Raised by forward-test case C; the user chose option 1 and then instructed its recording and application. |
| D9 | Define the routing boundary in the registry entry, the frontmatter description, and the skill body: a question whose answer would list several points waiting on the user is not an explanation-only request, so `discussion-briefs` loads before the answer. This refines the D1 sentence without undoing it. Then repeat case B more than once. Raised by the case B re-test; the user chose option 1 and instructed its application. |
| D6 | After the corrections, forward-test the skill with independent agents, starting with three cases: work ending with several pending points, a status question with no brief, and a decision whose owner is an approved architecture record. |

## Evidence and assumptions

- Verified: the working tree was clean at `e2fcf6a` before this plan; none of the five skill files
  changed since they were read in this session; `git check-ignore` reports the brief as ignored by
  the `*` rule; the Claude, Codex, and Copilot instruction files all resolve to `.codex/AGENTS.md`.
- Open assumption: None.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| completed | Obtain the plan review. | Advisor findings recorded below. |
| completed | Apply D3 in `.gitignore`. | `git status` lists `implementation-plans/briefs/` as untracked; the control `scripts/.env` still matches `/scripts/.env*`. |
| completed | Rewrite the `discussion-briefs` `SKILL.md` and template and update its registry entry (D1, D2, D4, D5). | Both files rewritten whole; `quick_validate.py` passes on the package and on its `.agents/skills/` symlink. |
| completed | Edit `plan-implementation` (D2), `architecture-records`, and `codex-claude-loop` (D7). | `git diff` shows only the planned sentences; `quick_validate.py` passes on each package. |
| completed | Validate the whole change. | Width scan clean, `git diff --check` clean, seven tracked files changed and all in scope. |
| completed | Run the D6 forward-test in an isolated scratch workspace. | Three sequential Sonnet agents, one throwaway fixture repository each; observations under Completion. |
| completed | Record in the brief where each decision now lives and collapse its decided items. | Decided items collapsed with links to this plan and the changed files; D8 is the only open item. |
| completed | Follow-up for D8: obtain the follow-up review, rewrite the promotion rule and the chat projection in `discussion-briefs`, and add the per-phase brief check to `plan-implementation`. | Advisor findings recorded below; validator passes on both packages; diff limited to those passages. |
| completed | Repeat forward-test case B and case C on fresh fixtures. | Case C passed; case B failed again for a different reason. Observations under Completion. |
| completed | Follow-up for D9: define the boundary in the registry entry, the frontmatter, and the skill body. | Validator passes on the package and its symlink; diff limited to those three passages. |
| completed | Repeat forward-test case B three times on a fresh fixture. | Three of three runs passed; observations under Completion. |
| completed | Close: collapse D9 in the brief, fix the brief's links, move this plan to `completed/`. | The brief is `concluído`, links to this plan under `completed/`, and has no open item and no `registro pendente` marker. |
| pending | Close with a focused author pass. | Verdict recorded below. |

## Review and replan

- Review mechanism: Advisor.
- Applied findings: use `registro pendente` as the single pending marker in the skill, the
  template, and the brief; D5.2 removes `em discussão` from items only, not from the document
  header; D2 adds no README requirement to `plan-implementation`, because `discussion-briefs` owns
  that sentence; rewrite the `discussion-briefs` files whole instead of stacking edits; run each
  D6 case in its own throwaway fixture repository under the scratchpad so that no test agent
  writes to a real plan root, sequentially, judged from the fixture's files and not only from the
  agent's report.
- Follow-up review for D8 (advisor): the follow-up stays non-trivial local and reversible, because
  it adds a stop and a read-only check and relaxes nothing. Applied: the per-phase brief check is
  a clause of the existing phase-inspection rule in `plan-implementation`, and it reports pending
  decisions instead of absorbing them, so the report triggers the user's recording instruction;
  the promotion section states that a decision changes only the brief, that promotion needs the
  user's explicit instruction, and that a contradiction with an approved record is reported, not
  promoted; the chat projection counts items with `registro pendente`.
- Follow-up review for D9: the advisor's closing review of the D8 follow-up already covered this
  route and was applied: option 1 must define the boundary with D1 instead of only adding
  questions as a trigger, because the registry said the skill is not for explanation-only
  requests and a status question can be read as one.
- Rejected findings: None.
- Replan if: an edit would relax a global gate or change another skill beyond the planned
  sentences; the forward-test shows a defect that needs a user decision; the user's files changed
  underneath the edit.

## Completion

- Evidence: every decision row above is applied in its owning file; `quick_validate.py` passes on
  `discussion-briefs` (package and symlink), `plan-implementation`, `architecture-records`, and
  `codex-claude-loop`; width scan and `git diff --check` are clean; `scripts/.env` stays ignored
  while the brief and this plan are now visible to Git. Nothing was staged or committed.
- Forward-test, case A (instruction that leaves ten pending points): the agent routed through the
  registry, created the brief under the fixture's `implementation-plans/briefs/`, numbered items
  sequentially, wrote the glossary, announced the README edit, and left the plan untouched. It
  also pasted a list of item titles into chat; the chat-projection rule now forbids that too.
- Forward-test, case B (status question, no brief): the agent created no file and offered the
  brief, but its chat answer was a long list full of undefined labels. The question-only summary
  rule was reworded to one plain line per point with no options or analysis. Not re-run.
- Forward-test, case C (bare decision whose owner is an approved architecture record): the agent
  recorded the decision and, in the same turn, superseded the approved record, created a new
  record, and edited the plan. No code changed. The skill's promotion rule still drives immediate
  promotion under the owner's skill. Whether a bare decision may touch anything beyond the brief
  is a user decision, recorded as D8 in the brief. One defect from this case needed no decision
  and was fixed: the authority paragraph told the agent to update the owner, contradicting the
  promotion section; it now only keeps the `registro pendente` marker and forbids overwriting the
  decision. The template's `Alimenta` example now shows a Markdown link, because the case A agent
  wrote a bare path.
- Re-test after D8, case C: passed. The before and after snapshots differ only in the fixture's
  brief; the architecture record, its index, and the plan are byte-identical. The item became
  `decidido` with `registro pendente`, and the chat reply named the decision, reported the
  contradiction with the approved record, gave the recording instruction, and counted the pending
  item.
- Re-test after the rewording, case B: failed. The agent created no file, but it loaded only
  `plan-implementation`, never loaded `discussion-briefs`, and answered with the long list full of
  undefined labels without offering a brief. The reworded rule was therefore not exercised: the
  defect is routing in question-only turns, not the rule's wording. Recorded as D9 in the brief.
- Re-test after D9, case B, three sequential runs: all passed. In every run the agent loaded
  `discussion-briefs`, left the fixture byte-identical, answered with six pending points in one
  line each, named the one that unblocks the most, and offered the brief for a later turn. Two
  replies still carried a few labels next to their explanation; the third carried none.
- Isolation: no test agent wrote outside its fixture; both real plan roots and the home
  repository status were checked after the runs.
- Delivery read-back: Not applicable.
- Focused author pass: Passed for the applied decisions: each decision row maps to a sentence in
  its owning file, the sibling-skill diffs contain only the planned sentences, and every link in
  the brief resolves. The brief's links to this plan were updated to `completed/` when the plan
  moved. The D8 follow-up diff was checked as well: the promotion section, the chat
  projection, the template's `Decisão` line, and the phase-inspection clause in
  `plan-implementation` all say that a decided item keeps `registro pendente` until the user
  instructs its recording. The D9 diff was checked too: the registry entry, the frontmatter, and
  the body all define a status question that lists pending points as in scope, and the
  explanation-only exclusion from D1 is still stated in all three.
- Unresolved limitations: skill routing stays a model judgment, so three passing runs show a
  tendency and not a guarantee; some labels may still appear beside their explanation in a
  question-only summary; the forward-test used one model, with one run for case A, two for case C,
  and five for case B across its three wordings; the over-trigger direction of the D9 boundary,
  such as an explanation-only request loading the skill, was not tested.
- Verdict: Passed.

## Follow-up after closure

- Instruction: after this plan closed, the user instructed that decided items keep their place in
  the brief so that each recorded decision can be reviewed beside its options.
- Change: `discussion-briefs` no longer collapses or moves a decided item. The item keeps its full
  text, its `Decisão` line swaps `registro pendente` for a link to the owner, a dropped item stays
  in place marked `descartado`, and the summary names the items still open. The template lost its
  closing section and gained the `descartado` state. This supersedes the D5.1 row above in part;
  its purpose, never reusing an item number, is kept.
- Scope: one paragraph in the skill's `SKILL.md` and the template. Routine, local, and reversible.
- Validation: `quick_validate.py` on the package and its symlink, width scan, `git diff --check`.
  No forward-test case covers the state after promotion, so this behavior is untested.
- Verdict for the follow-up: Passed. The original verdict above covers D1 to D9; this follow-up was
  validated separately and does not reopen it.
