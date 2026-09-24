# Implementation plan: Disable repeated Codex VS Code first run

**Status:** Completed
**Mode:** Plan and execute
**Risk:** Non-trivial local and reversible

## Outcome and scope

- Outcome: Opening a new Codex editor tab on this machine reaches the normal chat UI without the
  repeated first-run walkthrough. A guarded local patcher can reapply the change after extension
  updates and restore the original bundle.
- In scope: The installed VS Code Codex webview first-run decision, a reusable patcher, a focused
  regression test, and its update procedure in the home dotfiles repository.
- Out of scope: History pagination, conversation files, remote Codex state, and pushing or
  publishing the dotfiles change.
- Authority: The user's request to disable the repeated walkthrough. The extension's first-run
  route guard remains the runtime owner; the installed bundle is version-specific and must be
  recognized exactly before mutation.

## Evidence and assumptions

- Verified: In the installed extension, `pcr()` reads `NUX_2025_09_15` and returns a first-run
  state when the flag is false. `hcr()` redirects any such state to `/first-run`. The first-run
  module contains the text the user reported.
- Open assumption: Reloading the VS Code window will use the modified bundle. A focused test
  can prove the route decision; visual confirmation still requires a reload in the user's window.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| completed | Review the local route guard and choose a scoped patch. | Focused author reread: patch `pcr()` only and preserve route, account, and history code. |
| completed | Add a guarded first-run patcher with backup and restore. | Exact bundle matching, syntax check, and read-back. |
| completed | Add a test that executes the real route guard with the preference unset. | Stock code redirects; patched code renders chat. Test backup, restore, and unknown-layout rejection. |
| completed | Apply locally, validate the README procedure, inspect the final diff and repository status, and close. | Installed bundle check, backup read-back, focused and repository tests, scoped diff and status. |

## Review and replan

- Review mechanism: Focused author reread; no independent reviewer is required for this local,
  reversible patch.
- Applied findings: Keep the existing preference read and other webview behavior untouched by
  changing only the first-run decision function.
- Rejected findings: None.
- Replan if: A new extension version changes the first-run function or the route guard, the bundle
  has unrelated local edits, or the patched function fails to reach the normal chat route.

## Completion

- Evidence: The installed Codex 26.917.61114 bundle matches the guarded patch exactly. The
  original backup reproduces it through the patcher. Five focused first-run tests, ten existing
  history tests, and the repository test gate passed. The README documents reapplication and
  restore; the final diff is limited to the patcher, test, allowlist, and procedure.
- Delivery read-back: Not applicable.
- Focused author pass: Passed; the route guard reaches chat when the preference is unset, the
  original redirects, and the history patch still checks at its configured limit.
- Unresolved limitations: The open VS Code window must reload to read the modified bundle; visual
  confirmation in that window has not been performed.
- Brief check: No brief on this subject.
- Verdict: Passed for the local installed patch and its reproducible route behavior.
