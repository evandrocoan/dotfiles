# Repair test signals and restore the desktop

**Status:** Completed; source/test and runtime conformance passed independently
**Mode:** Plan and execute

## Outcome and scope

Prevent the incident-capture tests from signaling the user's session and restore the custom XFCE
desktop and usable TeamViewer, including the explicitly authorized replacement of the broken
graphical login. Preserve existing work and Git state.
Source owners are `scripts/performance-monitoring/incident_capture.py` and its test module.
Runtime recovery used fresh process identities, bus ownership and saved desktop configuration,
with the verified recovery actions recorded below.
Do not reboot, restart LightDM/Xorg services, kill broad process groups, install dependencies,
deploy the monitoring service, or change unrelated files. Back up any restored panel configuration.
The user subsequently explicitly authorized terminating the broken c208 graphical session and
performed the new login. Revalidate its exact ID/leader/type immediately before logind
termination; preserve the SSH session and live user manager. Do not bypass authentication.

## Governing invariants and evidence

- High risk: live desktop recovery and correcting an actual broad process-termination defect.
- The September 23 suite stopped at the mocked-Popen cancellation test at 12:26:16, coincident
  with widespread SIGTERM and graphical logout. The real cleanup uses `os.killpg(child.pid, ...)`.
- Pending lightweight-mode tests were added by another chat while production still always calls
  collectors. The user explicitly chose to finish lightweight capture. Implement automatic
  pressure observation without children; retain detailed manual capture and current report fields.
- The user manager was inactive after the broad termination. Starting this stopped manager is
  within desktop recovery; inspect its unit and defaults first, then verify the real bus and
  re-read graphical ownership before starting missing components. Never restart a healthy manager.
- Replace forbidden process creation with a raising stub, never a fabricated process object.
- Before any group signal, require an actual integer PID greater than one and an isolated group
  owned by the spawned child. Cover TERM and KILL. Test invalid identities with signaling mocked.
- Use waitid with WNOWAIT for exit detection to keep the child unreaped as a stable ownership
  anchor until cleanup. Reject ChildProcessError and group/session mismatches, and record cleanup
  failures. Cover natural leader exit with descendants and TERM-ignoring escalation.
- Real collector tests use only disposable Python children in new sessions; retain cleanup proof.
- Initial host session c208 had Xorg, xfce4-session and TeamViewer, but desktop components were
  absent. The agent's inherited bus address was stale; recovery used the real session environment.
- Recover only missing components or exact verified failed GUI identities; preserve live apps.
- Do not dismiss the stalled xfce4-session dialog. Its manager may remain disconnected from the
  replacement bus; verify actual ownership separately and report an unresolved session issue
  if it cannot recover without logout. No silent replacement of the user's session is allowed.
- The visible error and absent session-manager owner confirmed that c208 cannot complete its
  startup. User-authorized recovery now includes ending only c208, waiting for the greeter, and
  verifying fresh session ownership and saved panel after the user's login.
- Relevant root AGENTS.md and skills govern this plan. No same-subject brief exists.

## Execution steps

| Status | Step and owner | Material premise | Validation |
| --- | --- | --- | --- |
| completed | Independent plan review | High-risk boundary | repair_plan_review approved after ownership and session-health findings |
| completed | Make test fixtures and collector signaling safe | No test reaches a real unsafe signal | Closure finding repaired; real orchestration and negative control prove descendant cleanup |
| completed | Restore current graphical components | Fresh session, bus and X authority verified | Fresh c212 has session-manager ownership and saved custom panel; user confirms image/control |
| completed | Reconcile unfinished lightweight tests | Explicit user choice received | Final gate 44 monitoring plus 54 other tests and syntax checks pass |
| completed | Independent closure | Stable session and validated code | repair_closure_review passed source/test; repair_runtime_closure passed final runtime read-back |

## Plan review

Advisor unavailable. Independent fresh-context `repair_plan_review` approved execution after
source and host inspection. Same-model review has residual correlated-blind-spot risk.
Applied initial findings: retain unreaped process ownership through cleanup; verify session-manager
bus health separately from component startup. No rejected findings.
The bounded logout revision was approved by repair_plan_review after verifying c208, the running
user manager, and distinct SSH/TTY scopes. Applied: reconcile all five temporary recovery units
after logout because they are owned by the user manager rather than the terminated session.
Closure reviewer found that waiting/reaping a cooperative leader after TERM could leave a
TERM-resistant descendant. Applied: retain the anchor through a bounded non-reaping grace period,
send a final checked group KILL before reaping, and cover both cooperative and already-exited
leaders through the actual collector orchestration. Reopen source validation for this correction.

## Validation and replan conditions

Authenticate the incident from existing records; never rerun its unsafe form. Negative controls
must intercept signal syscalls. The user disabled the tool sandbox; establish a verified PID
namespace using installed tools before executing focused regressions and the repository gate.
Keep test processes unprivileged. A missing isolation capability blocks test execution until a
safe route is agreed. No dependency installation is authorized.
Revalidate the active session before runtime changes. Stop for an unexpected session replacement,
missing authority or unexpected process ownership. The c208 logout is explicitly authorized.
Require a user reconnect check for remote image/control; local process health alone is insufficient.

## Completion evidence

- Both Popen fixtures now raise on unexpected calls. Group signaling rejects invalid IDs, verifies
  unreaped direct-child ownership, and requires isolated PGID/SID. Natural exit is detected without
  reaping. Both TERM and KILL pass through the same checked boundary.
- Automatic pressure captures observe host samples without subprocesses and retain process deltas,
  history and cooldown. Manual captures still use disposable collector subprocesses. Cancellation,
  incomplete snapshots and sampler failure have distinct verified terminal outcomes.
- Bwrap PID/network isolation was verified before tests; host root was read-only, with private
  `/proc`, `/dev` and temporary storage. Focused tests passed; full repository gate passed with
  44 monitoring tests and 54 other tests, no skips. Python compilation and Bash syntax passed.
- The unsafe-identity negative control intercepted signal syscalls and caused 22 expected assertion
  failures; injecting forbidden spawning caused the light test to fail without creating a child.
- Final cleanup retains the unreaped leader through TERM grace, checked group KILL and then wait.
  A real orchestration regression covers a TERM-resistant descendant under both already-exited
  and cooperative leaders. Omitting final group KILL in memory produced two expected failures
  with zero errors; its guarded fixture cleanup removed the surviving disposable descendants.
- Started the inactive user manager and imported only verified graphical variables. An automatically
  activated xfconfd had started before the environment import; verified its exact bus owner and
  executable, terminated only that process through a pidfd, and started the custom daemon with
  correct Mint config inheritance. Intermediate PID 1496287 owned the bus name before logout.
- Started missing WM 1497659, settings 1497684, desktop 1497690 and custom panel 1497693 through
  temporary user units. Saved panel XML already matched HEAD; no configuration restoration was
  needed. The recent-applications-only whiskermenu difference was preserved.
- Intermediate desktop recovery preserved c208, Xorg 1422771 and xfce4-session 1425017 and the
  user confirmed remote control. Its failed-start dialog and missing session-manager bus owner
  required the subsequent, separately authorized logout rather than declaring full recovery.
- The TeamViewer GUI subsequently exited with UserEnd; after verifying GUI/name absence, used its
  installed D-Bus activation entry to make it available again. No daemon restart was requested.
- Monitoring service installation and fatrace measurement remain outside this repair and pending
  in the original lightweight plan. The installed service still uses the previous source.
- After explicit approval and reviewed identity checks, only c208 was terminated. Greeter c211
  appeared; SSH session 7271, tty session 2981 and user manager 1488102 were preserved at that
  point. All five owned recovery units became inactive. A D-Bus-activated custom xfconfd was
  healthy with correct Mint inheritance. The later fresh login and confirmation are below.
- Independent repair_closure_review rechecked the final source hashes, scoped diff, tests and
  recorded isolated results. Source/test conformance passed with no unresolved finding. It
  independently verified the greeter and preserved manager/SSH/TTY. After an interruption,
  fresh-context repair_runtime_closure completed the final runtime pass separately.
- Initial fresh-login verification of c212 found xfce4-session PID 1553771 owning
  org.xfce.SessionManager, custom xfconfd
  1554779, custom panel 1555280 with correct Mint inheritance, plugin path, NO_AT_BRIDGE and live
  SESSION_MANAGER, plus WM 1554439, settings 1555256 and desktop 1554609. Panel position and all
  twelve plugin IDs matched the saved layout; titleless_maximize was true.
- User explicitly confirmed after the new login: "Login feito; imagem e controle funcionando".
  The old error dialog belonged to terminated c208; the new session's manager is registered.
- Final independent read-back found c212 active on :0 with the same session manager, custom
  panel, WM/settings/desktop and TeamViewer GUI 1554035. Custom xfconfd now has PID 2319325,
  owns org.xfce.Xfconf and has correct Mint inheritance. User manager 1488102 remains healthy;
  SSH/TTY sessions are no longer registered. LightDM has remained active since June.
- All five exact recovery units are not-found/inactive/dead, with no remaining PID or persistent
  definition. Panel environment, position, plugin order and titleless_maximize were reverified.
  Preserve CopyQ additions to both known and hidden legacy-tray lists and recent-app history.
  Six workspaces differ from HEAD's nine, but the workspace XML dates to August 1, supporting
  a preexisting difference. No unauthorized configuration change was identified.
- Final source hashes match the independently reviewed and tested versions:
  incident_capture.py `2be7ae604562ae1fe469271b7b974a699036ee747f4a8d2ff932af7fc9f7420e`;
  test_incident_capture.py `91dae1dad73226b3d25aec750c5a3d3e2f0bb03c119a8605232046657de3b509`.
  The installed recorder remains unchanged; its service has run since September 9.
- The user authorized a local commit of this repair. Include its two Python owners and this
  completed plan; preserve other local work and leave the broader monitoring plan uncommitted.

## Closure audit

| Status | Requirement | Owner and evidence |
| --- | --- | --- |
| verified | Invalid/mock IDs cannot reach group signaling | collector_pid/signal_collector; invalid types, special IDs, reaped/unowned IDs and PGID/SID regressions |
| verified | Real disposable collectors terminate correctly | Orchestration tests for timeout, cancellation, partial startup, exited leader, stubborn descendants and KILL; negative control |
| verified | Incomplete test contract reconciled as authorized | User choice; pressure/manual replay, history/cooldown, cancellation, incomplete snapshot and sampler failure; 98-test final gate |
| verified | Runtime mutations stay within authorization | Only missing components, exact xfconfd pidfd and specifically approved c208 termination; SSH/user manager preserved |
| verified | Custom desktop and remote image/control recovered | Fresh c212 bus ownership, custom executables/env, saved layout and user confirmation after login |
| verified | Scope and existing edits preserved | Two source/test owners and two execution plans; preexisting changes preserved; local commit authorized separately; no monitoring install |
| verified | Independent conformance pass | repair_closure_review passed source/test; repair_runtime_closure passed final runtime conformance; historical evidence wording corrected |

Forward trace: recovery and safety request -> collector/test owners and current desktop ->
isolated regression, suite, process/configuration and remote checks.
Reverse trace: only collector/test fixes, runtime recovery, bounded panel restoration and this
execution plan are authorized.

### Final conformance verdict

Source/test and runtime conformance passed independently. The implementer's full instruction/plan
reread, source reconstruction, scoped diff/status, tests, negative controls and fresh-session checks
pass. The final runtime review found only historical evidence wording to correct; that correction
is recorded above. No requirement in this repair remains unresolved. Monitoring installation and
fatrace measurement remain outside this repair, pending in the original plan. Git delivery is local.
