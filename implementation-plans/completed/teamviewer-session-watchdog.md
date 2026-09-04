# Implementation plan: TeamViewer session watchdog

**Status:** Completed
**Mode:** Plan and execute

## Outcome

Detect when TeamViewer retains a removed graphical session, restart `teamviewerd.service` with a
bounded cooldown, and leave an enabled watchdog that recovers before the next remote connection.

## Scope

### In scope

- Parse TeamViewer's daemon log as it grows and across log rotation.
- Detect a removed session that TeamViewer still considers active.
- Treat `Unable to get session` as a fallback signal.
- Restart `teamviewerd.service` at most once per cooldown window.
- Install and enable a root-owned system service and document its setup and diagnostics.

### Out of scope

- Updating or reconfiguring TeamViewer itself.
- Removing the existing daily root cron restart.
- Changing screen-lock, LightDM, or XFCE behavior.

## Governing decisions and invariants

- The authenticated incident log is the runtime authority for the failure signature.
- A removed session must never remain TeamViewer's selected active session.
- The watchdog must start at the end of the log so historical failures cannot cause a live restart.
- The privileged service must execute a root-owned installed copy, not a user-writable repository
  file.
- Detection must be covered with deterministic fixtures; live validation must not manufacture a
  broken graphical session.

## Current evidence and assumptions

### Verified evidence

- The daemon logged a LightDM session as active and then removed that same session after unlock.
- Later incoming requests repeatedly logged `Unable to get session` until the daemon was restarted.
- A restart made TeamViewer select the active user X11 session and accept the next connection.
- The host provides Python 3, systemd, and the daemon log under `/var/log/teamviewer15/`.
- A disposable systemd probe with the watchdog's restrictions successfully restarted a disposable
  target service.

### Open assumptions

- TeamViewer retains the observed log phrases across patch releases.

## Execution steps

| Status | Step | Affected owner and consumers | Validation |
| --- | --- | --- | --- |
| completed | Authenticate the stale-session transition in the incident log. | TeamViewer daemon log | Replay the observed transition without mutating the service. |
| completed | Add deterministic detection and cooldown protection. | Watchdog module and tests | Focused tests for stale, healthy, fallback, duplicate, and rotation cases. |
| completed | Add and install the hardened systemd service. | Root-installed script and unit | Verify ownership, unit security, enablement, and active state. |
| completed | Document setup, operation, and removal. | Repository README | Check commands and table-of-contents links. |
| completed | Run complete checks and closure audit. | Complete watchdog flow | Tests, compile check, replay, systemd verification, diff audit. |

## Replan conditions

- Replan if TeamViewer truncates rather than rotates the log, the live unit cannot access systemd,
  or the incident replay does not distinguish the stale transition from a healthy unlock.
- Stop before installation if root authorization is unavailable.

## Completion evidence

- Twelve deterministic tests pass for detection, rejection, cooldown, complete-line handling,
  truncation, and lossless rotation.
- A negative control that disabled removed-session recognition failed the focused regression.
- Non-mutating replay of the installed copy recognized every historical stale LightDM transition,
  including the diagnosed incident.
- The enabled service runs the root-owned installed copy and matches the repository sources.
- The hardened restart probe completed successfully; systemd rates the installed unit `2.5 OK`.
- TeamViewer's activation timestamp remained unchanged throughout installation and validation.
- The remaining compatibility limitation is that a future TeamViewer release may change private
  log messages; the fallback signature and service journal make that observable.

## Closure audit

| Status | Requirement source | Requirement | Implementation evidence | Validation evidence |
| --- | --- | --- | --- | --- |
| verified | Outcome | Recover stale TeamViewer session selection automatically. | Watchdog script and enabled systemd unit. | Historical replay, active unit, and hardened restart probe. |
| verified | Scope | Detect proactive and fallback failure signatures. | `TeamViewerSessionDetector` owns both transitions. | Focused tests and historical replay. |
| verified | Invariant | Never replay historical failures on startup. | `LogFollower` opens the initial log at EOF. | Start-at-end regression test and clean service journal. |
| verified | Invariant | Bound restart attempts with a cooldown. | `RestartLimiter` records every attempt. | Success, duplicate, and failed-attempt tests. |
| verified | Invariant | Follow complete lines without losing rotation data. | `LogFollower` drains, reopens, and handles truncation. | Complete-line, rotation, drain-before-reopen, and truncation tests. |
| verified | Invariant | Execute only a root-owned privileged copy. | Unit uses `/usr/local/sbin/teamviewer-session-watchdog`. | Root ownership, modes, source comparison, and service status. |
| verified | Out of scope | Preserve TeamViewer, cron, and lock-screen configuration. | No implementation changes those owners. | Diff audit and unchanged TeamViewer activation timestamp. |
| verified | Validation | Tests fail for the stale-session defect and pass with detection enabled. | Deterministic fixtures exercise the runtime classes. | Negative control failed; complete suite passed. |
| verified | Operations | Document installation, diagnostics, updates, and removal. | README TeamViewer recovery subsection. | Heading/link check, command review, and `git diff --check`. |

- Architecture to implementation: no architecture record governs this local watchdog; every plan
  invariant reaches the detector, follower, limiter, systemd unit, tests, and README as applicable.
- Implementation to authority: every changed runtime, test, unit, allowlist rule, plan, and README
  section is authorized by the outcome, repository tracking rules, or plan lifecycle.
- Second conformance pass: self-reviewed the complete plan, repository instructions, runtime,
  tests, unit, documentation, installed state, and final diff; no omission or unauthorized change
  remains.

### Final conformance verdict

- **Verdict:** Passed
- **Second pass:** Self-reviewed
- **Auditor and evidence:** Both self-review passes used the complete repository diff, twelve
  passing tests, negative control, historical replay, installed-source comparison, service state,
  and hardened restart probe.
- **Unresolved requirements:** None.
