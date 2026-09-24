# Implementation plan: Show the Codex header in an empty VS Code tab

**Status:** Complete
**Mode:** Plan and execute
**Risk:** Non-trivial local and reversible

## Outcome and scope

- Outcome: A new Codex editor tab shows its navigation header before the first message, including
  the recent-chat and settings controls. The local fix can be reapplied after extension updates
  and restored from a verified backup.
- In scope: The installed extension's `NewThreadPanelPage`, a guarded local patcher, focused
  regression protection, and update instructions in the home dotfiles repository.
- Out of scope: Conversation persistence, history pagination, the first-run walkthrough, other
  Codex surfaces, Git delivery, and remote state.
- Authority: The user's observed missing header and the installed extension's existing `Header`
  component. The patch must reject unknown bundle layouts and preserve other local patches.

## Evidence and assumptions

- Verified: `/extension/panel/new` loads `NewThreadPanelPage`. Its JSX renders the composer but
  omits `Header`. The standard home and existing-conversation views already import or render the
  same header component. The installed extension is 26.917.61114, and the history and first-run
  patches remain applied.
- Confirmed: Adding the existing header above the new-tab content renders the controls before
  the first message. The user confirmed the behavior after reloading VS Code.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| completed | Inspect the new-tab route, standard header use, and local patch state. | Exact installed JSX and route registration identified. |
| completed | Add a guarded patcher for the new-tab asset with backup and restore. | One import and JSX insertion matched; syntax and import target checked. |
| completed | Execute the real new-tab component from stock and patched assets with controlled UI dependencies. | Header absent before and present after; composer remains; drift rejected. |
| completed | Apply locally and update the reapplication procedure. | Installed asset check, 19 focused tests, and repository gate passed. |

## Review and replan

- Review mechanism: Focused author reread for a local, reversible UI patch.
- Applied findings: Reuse the extension's existing `Header` export and leave conversation and
  onboarding paths untouched.
- Rejected findings: None.
- Replan if: The new-tab asset already includes a header, the existing header cannot render in
  this route's provider context, the import graph is unsupported, or the installed bundle drifts.

## Completion

- Evidence: `--apply` and `--check` passed for Codex 26.917.61114; checks for the history
  and first-run patches also passed. The 19 focused Node tests and 55 repository tests passed.
- Delivery read-back: Not applicable.
- Focused author pass: The new import uses the existing initialized header export. The JSX
  inserts the header before the main content and leaves the composer and earlier patches intact.
- Unresolved limitations: The patcher targets the inspected extension bundle and must be
  adapted if a future extension version changes its layout.
- Brief check: No brief on this subject.
- Verdict: Complete; the user confirmed the restored header in VS Code.
