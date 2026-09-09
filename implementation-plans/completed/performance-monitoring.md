# Implementation plan: historical workstation performance monitoring

**Status:** Completed
**Mode:** Plan and execute

## Outcome

Record workstation and process activity continuously and query it by date/time. Enable atop,
process accounting, sysstat, per-process network collection and a local Netdata dashboard; document
installation, operation, update, recovery and removal in the home repository README.

## Scope and governing invariants

- User approved all recommendations, including Netdata and the netatop-bpf build dependencies.
- Follow [AGENTS.md](../../AGENTS.md): system units belong under `scripts/systemd/system/`, outside
  the user configuration installation tree. Allowlist new repository sources explicitly.
- Preserve other services, workloads, swap settings, existing history and unrelated documentation.
- Use distribution packages for atop/sysstat, the official stable Netdata APT repository, and an
  immutable upstream netatop-bpf revision. The distribution Netdata cannot rewind network procfs
  files on this kernel; stable upstream includes the verified ESPIPE/reopen fix.
- Keep Netdata bound to loopback; store metrics locally and disable cloud/anonymous telemetry.
- Preserve pre-configuration files for recovery. No reboot, Git commit or push is authorized.

## Evidence and open assumptions

- Mint/Ubuntu noble, kernel 6.14, cgroup v2, kernel BTF and task accounting support are available.
- Initially, atop, sysstat and Netdata were absent and the Git worktree was clean. Passwordless
  sudo is available.
- About 1,500 processes, Docker, memory pressure and active swap make host process history useful.
- Runtime delay accounting was initially disabled; enabling it covers subsequently created tasks only.
- Netatop-bpf revision `7c905a2a6a102167a968ab7d09645d7dafa47f21` needs a small local patch:
  current socket tracepoints expose signed `ret` plus flags, so failed/peek operations must not
  count as transferred bytes. Use lazy BPF map allocation for this memory-constrained workstation,
  bound the epoll event count to its array, and restrict the collector socket to root.
- Configure Netdata cloud and telemetry off explicitly, including after the official package update.
- All-process atop recording projected roughly 89 GiB/month in a short sample. Preserve 10 s
  detail with a storage budget and a 30-day age setting; real retention can be shorter under the
  budget. Keep sysstat monthly history and Netdata aggregates for longer-term trends.

## Execution steps

| Status | Step | Owner and consumers | Validation |
| --- | --- | --- | --- |
| completed | Inspect package/upstream configuration and prepare reproducible sources. | Monitoring configs, pinned build, system units | Reviewed vendor units, dbengine build, tracepoint ABI and pinned source; package baseline saved. |
| completed | Install and enable recording with rotation and loopback dashboard. | Root system services and `/var/log`/`/var/cache` data | Services enabled/active; stable Netdata reads nonseekable procfs; hourly 20 GiB atop budget installed. |
| completed | Prove historical CPU/memory/I/O/network and dashboard collection. | Atop replay, sar archives, Netdata API | Replay/tests passed; numerical backing filesystem and container I/O/network samples verified after narrow mount exclusions. |
| completed | Document operations and finish conformance audit. | README, allowlist, plan | README corrections verified; root and independent final conformance passes found no unresolved requirements. |

## Replan conditions

- Unsupported BPF hooks or verifier errors require a source-level fix or supported collector route;
  do not silently omit per-process network history.
- Excessive collector memory/CPU or log growth requires tuning while retaining useful history.
- Missing permissions, existing conflicting configuration or overlapping user edits require
  preserving that state and recording the actual constraint.

## Validation and completion evidence

TCP/UDP negative controls failed against unpatched upstream (3679 received bytes instead of 3328)
and both passed against the patched running service. The test sends known loopback payloads and
rejects accounting of failed receives and MSG_PEEK. Unit verification passed with unrelated legacy
PIDFile notices from pre-existing TeamViewer/AnyDesk units.

Use focused live collection and replay checks; avoid memory/CPU stress on the workstation.
Check rotated-file retention behavior with disposable files only. A month of real retention cannot
be observed during installation; report configured retention separately from elapsed history.

- Five retention tests pass, including real open-reader detection and preserving current logs.
  A no-unlink negative control fails both deletion-sensitive tests.
- Vendor sysstat cleanup/compression was exercised with a disposable configuration/data directory;
  expired archives disappeared, old archives compressed losslessly, recent/unrelated files remained.
- Atop replay showed the known workload's CPU, RSS, physical read/write, UDP and terminal exit
  records at 10-second intervals. All three documented sar queries returned the expected metrics.
- Stable Netdata numerical API samples cover CPU, PSI, swap, apps, physical interface and container
  network metrics. Browser anonymous access reached the dashboard without logging into a cloud account.
- Netdata retained numeric history across its update/restarts. Narrow exclusions eliminate permission
  errors for internal Docker/root FUSE mounts while preserving `/`, `/home`, `/myfiles` and container
  I/O/network samples; see `final-diskspace-validation.json` in the local evidence directory.
- `netdatacli aclk-state` reports unclaimed/offline, telemetry opt-out exists, and the listener is
  `127.0.0.1:19999`. The kernel delay flag is enabled; existing tasks require restarting naturally.
- Source/live comparison, shell syntax, local README links, instruction symlinks, package audit and
  allowlist checks passed. Operational evidence is under
  `~/.cache/performance-monitoring-install/`; backups are root-only under
  `/var/backups/performance-monitoring/`. Raw machine history is not added to Git.

## Closure audit

| Status | Requirement | Implementation evidence | Validation evidence |
| --- | --- | --- | --- |
| verified | Continuous atop/accounting, age and disk budget | atop.default; atop/rotation drop-ins; retention service/timer/script | Active/enabled services, 10 s replay, five policy tests, live no-deletion cleanup |
| verified | Sysstat 60 s collection, 30-day retention policy and compression | sysstat.conf/default and timer drop-ins | Timers and sar archive/report checks; disposable vendor retention/compression test |
| verified | Network attribution and persistent delay accounting | Pinned BPF revision/patch/service; sysctl file | TCP/UDP negative controls and passing tests, replay network bytes, flag=1 |
| verified | Local dashboard, app/container coverage and resource/storage bounds | netdata.sources/conf/cloud/groups and service drop-in | Numeric API samples, anonymous browser flow, offline/unclaimed state, loopback listener, source/live equality; final mount exclusions preserve backing filesystem/container charts |
| verified | Observable historical process behavior and collector cost | Atop/sar/Netdata runtime consumers | history-replay.txt; sar-verified reports; final-overhead.json in the local evidence directory |
| verified | Reproducible install/update, diagnostics/recovery/removal and navigation | README monitoring section, tracked-source allowlist, root backup | Bash syntax, links, backup inventory, pinned source build, source/live comparison; journal namespace verified and approximate daily expiry documented |
| verified | Authorization and preserved surrounding system | AGENTS.md; user-approved monitoring scope | No commit/push/reboot or workload restart; changes limited to monitors, required compiler dependencies, configs, README and plan |

Forward trace: approved historical monitoring -> configuration and pinned collector -> system
services/timers -> recording/query consumers -> live replay, API and retention checks.
Reverse trace: each new source/unit/configuration and the README change supports the approved
monitoring outcome; temporary build and evidence files remain outside the Git allowlist.

### Final conformance verdict

- **Verdict:** Passed
- **Second pass:** Independent review by `monitoring_final_review`; no unresolved findings.
- **Unresolved requirements:** None.
- **Observed limits:** A full month of retention and reboot/removal were not exercised. Boot wiring
  and removal instructions were reviewed; configured retention is distinct from elapsed history.
- **Repository state:** Plan and new source files are allowlisted but untracked; no commit was made.
