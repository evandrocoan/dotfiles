# Implementation plan: isolated pull recovery corrections

**Status:** Completed
**Mode:** Plan and execute

## Outcome

`scripts/isolated_pull.sh` preserves the home repository's work tree and Git state when interrupted
at either directory move, when aborting an isolated rebase fails, and when the pull's supervised
process group has live members. Preconditions reject relevant Git locks, including those under
`.git/objects/pack`. Regression tests exercise each failure through the real script in disposable
repositories; the repository gate passes. The helper
is never run against the home repository during validation.

## Scope

### In scope

- Correct the recovery and active-process handling in `scripts/isolated_pull.sh`.
- Add focused regressions to `scripts/test_isolated_pull.py` and align the existing README recovery
  instructions with the changed failure contract.

### Out of scope

- Running the helper against the home repository, changing its branch, rewriting existing history,
  or changing remote state.
- Changing the chosen `git pull --rebase` update method or deciding how ordinary conflicts should
  be resolved manually.
- Editing unrelated user work already present in the home directory.

## Governing decisions and invariants

- The user's correction request covers the defects identified in the review of
  `eca198fbd3369708b1c893788d947852c7afa331`.
- The user's follow-up clarifies that this helper is new; documentation must not imply an
  installed earlier version or retain a hypothetical legacy recovery procedure.
- `AGENTS.md` and the existing `README.md` runbook require the root work tree to remain untouched
  and manual review after the isolated pull. This plan corrects recovery guarantees without
  changing the original pull method.
- On an observable failure, restore `.git` only after Git operations using it have stopped and an
  unfinished rebase or merge has been aborted. If those conditions cannot be established, leave
  `.git` in the isolated tree and provide a precise recovery path.
- Reconcile both directory moves from actual source and destination presence; the moved flag alone
  cannot establish location after a signal. A completed return move must not be reported as a
  collision when a signal arrives before its flag assignment.
- Any nonzero abort status leaves recovery unverified, even if a marker disappears. Do not move the
  database back until the abort succeeds and pending-state checks pass.
- A pull leader's exit alone does not prove that Git descendants are done. Check the separate pull
  process group before restoration, leave `.git` isolated if a live member remains, and disable
  automatic detached Git maintenance during the pull.
- The precondition lock check cannot rule out another Git process starting afterward; neither code
  nor documentation may claim it does.
- The full repository test route is `bash scripts/run_repository_tests.sh`, which runs the Python
  tests and Bash syntax checks. Validation uses disposable fixture repositories, never `$HOME`.
- High risk: moving the live Git database has a credible interruption and data-loss hazard.

## Current evidence and assumptions

### Verified original-commit evidence

- `movegitdirectory` sets its moved flag after the external `mv`; Bash may run a pending signal
  trap between them, and `onexit` then skips restoration.
- `abortpendingoperation` ignores abort errors; `restoregitdirectory` returns `.git` to the root
  even while a rebase or merge marker remains.
- `checknolocks` prunes `.git/objects`, omitting locks in that tree.
- `stoppullchild` waits only for the direct `git pull` PID. The existing blocked-transport test
  states that its transport outlives the script and observes only the direct child.
- The work tree contains unrelated pre-existing changes; this correction must leave them intact.

### Open assumptions

- None. A blocked transport can leave a lock-holding descendant after the pull leader exits;
  a separate process group permits controlled termination and observation. A test-only `mv`
  wrapper injects signals after the real rename without a production hook.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Obtain high-risk plan review | Recovery behavior must be reviewed before implementation | Fresh-context reviewer findings recorded below |
| completed | Authenticate both move-boundary signal windows, abort failure, pack lock, and Git descendant cases in disposable fixtures | The fixture exercises the real script and can observe location, pending state, and process lifetime | Six focused cases failed on the original code for the intended reasons |
| completed | Correct `scripts/isolated_pull.sh` recovery and supervision | The authenticated failure mechanisms support the selected route | Focused cases pass; safety failures retain `.git` in isolation |
| completed | Synchronize README recovery steps and remove obsolete implementation-specific test assertions | Failed aborts and live descendants can leave `.git` isolated | Recovery selects the `run-*` tree containing `.git` and checks the saved process group and locks |
| completed | Run focused tests, repository gate, and closure audit | All code and test edits are final | Original correction passed: 44 and 174 tests; independent second pass passed |
| completed | Remove hypothetical prior-version recovery from README, its test, and coupled claims | User clarified the helper is new and no legacy recovery is needed | Only the current `run-*` recovery remains; three focused README tests and the repository gate passed |

## Plan review

- **Risk classification:** High risk because the helper relocates a live Git database.
- **Mechanism:** Independent reviewer; no advisor tool is available in this client.
- **Independent reviewer:** Fresh-context read-only deep reviewer; found four plan gaps.
- **Applied:** Added both move windows and destination reconciliation; abort failure is unverified
  regardless of marker disappearance; descendant safety requires verification before restoration;
  README must describe isolation on failed abort or live process and select the run tree containing
  `.git`; replace direct-child test assertions with observable behavior where needed; update help
  wording; distinguish safe restoration from deliberate isolation; avoid overclaiming the lock check.
- **Rejected:** A separate prior-version recovery path: the user clarified that this helper is
  new and no installed legacy procedure needs documentation.

## Replan conditions

- A deterministic regression cannot reach the move boundary or abort failure through the real
  script without altering the production contract.
- Child-process termination requires a new dependency or a different update method.
- The verified behavior contradicts an existing manual recovery guarantee.

## Completion evidence

- Original-code negative controls failed for both move windows, failed abort, pack lock, and live
  descendant cases. The updated code passes those cases and a bounded resistant-leader case.
- The real README recovery command was executed in disposable fixtures. It aborted a pending
  isolated rebase before restoration and refused recovery while the saved process group was live.
  A leader-exits-first test kept the database isolated while a live descendant without a Git lock
  remained in the supervised process group.
- The README now covers only `run-*` recovery and limits manual tree deletion to runs whose
  `.git` was returned and whose contents were reviewed. The hypothetical recovery test was removed.
- `bash scripts/run_repository_tests.sh` passed after the follow-up: 44 and 173 tests, Python
  compilation, and Bash syntax checks. Three focused README recovery tests passed.
- No test invoked the helper against the home repository. The helper, tests, README, AGENTS.md, and
  this plan are the only task-owned edits; other visible changes predate or run alongside it.
- Remaining limitation: a Git client can start after the lock precheck, and an external transport
  that deliberately leaves the supervised process group is not observable through that group.
  The README instructs keeping clients idle and checking for other processes before manual recovery.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Reconcile actual directory state after signals at both move boundaries | `restoregitdirectory`; recovery runbook | Signal wrappers call the real `mv` then signal; tests observe correct location and status at both windows |
| verified | Never return an abort failure or unresolved rebase or merge state | `abortpendingoperation`, `restoregitdirectory`; recovery runbook | Abort injection before and after the real abort leaves `.git` isolated; fixture branch tip and root files are unchanged; README recovery test succeeds after a real abort |
| verified | Stop the supervised pull process group before restoring or leave `.git` isolated | `runpull`, `stoppullchild`; process tests and README | Cooperative lock holder stops before return; resistant descendant and leader leave `.git` isolated with group marker; leader-exits-first test requires the group diagnostic without a lock; README command refuses a live group |
| verified | Reject relevant Git locks before the first move and before restoration | `findgitlock`; refusal and descendant tests | `multi-pack-index.lock` is refused; return-side `index.lock` is checked; filesystem errors return failure |
| verified | Preserve root work and unrelated local changes | Script; fixture snapshots; final diff | Dirty tracked and untracked fixture snapshots remain byte-identical; final diff is scoped to four requested artifacts and local plan |
| verified | Complete repository gate and test evidence review | Test runner; test module | 44 and 173 tests pass with syntax/config checks; assertions observe real script state rather than configured mock results |

Architecture to implementation: root work tree preservation, safe Git database return, manual
recovery, and no silent re-hiding of flags trace through this plan to the script, README, AGENTS.md,
and the focused real-script tests. No architecture record governs this correction; the original
method was introduced by the reviewed commit.

Implementation to authority: `scripts/isolated_pull.sh` implements the requested safety fixes;
`scripts/test_isolated_pull.py` protects them; `README.md` and `AGENTS.md` synchronize the changed
recovery contract under repository instructions; this plan exists under the high-risk persistence
gate.

### Final conformance verdict

- **Verdict:** Passed after the editorial follow-up.
- **Second pass:** A fresh-context read-only reviewer found no blocking issue in the final diff;
  current `run-*` recovery and its three focused tests remain intact.
- **Auditor and evidence:** The pre-edit reviewer identified the manual-deletion guard; it was
  added. The final reviewer confirmed the hypothetical path and its test are gone and found no
  divergence from the plan or repository instructions. The official gate passed 44 and 173 tests.
- **Unresolved requirements:** None within the requested scope. Known concurrency limits remain
  stated above and in the README.
- **Brief check:** No same-subject brief among the three working briefs at closure.
