# Implementation plan: automatic performance incident capture

**Status:** Completed
**Mode:** Plan and execute

## Outcome

Capture bounded, timestamped incident reports automatically when sustained memory or I/O pressure
appears, and on manual request. Include independent eBPF block-I/O evidence, host/process/container
context, and explicit invalid-delay flags. Document installation, diagnosis, retention and removal
in the home README. Prepare delay accounting from the next boot without rebooting this workstation.

## Scope and invariants

- The user approved the proposed incident capture, eBPF tools, invalid-data handling and boot setup.
- Follow [AGENTS.md](../../AGENTS.md): system units use `scripts/systemd/system/`; monitoring code
  and configuration use `scripts/performance-monitoring/`; allowlist sources, never runtime data.
- Preserve the existing atop/sar/Netdata/netatop collectors and their histories. No Git commit/push,
  kernel upgrade, reboot, workload restart or change to swap/resource allocation of applications.
- Collect locally as root with private reports. Do not collect environment variables, application
  payloads or full command arguments. Bound capture duration, simultaneous captures, retry rate,
  collector output, resource use and retained storage; distinguish incomplete captures from success.
- Preserve raw counter evidence. Impossible delay-accounting values must be flagged and excluded
  from delay rankings rather than rewritten or presented as valid zeroes.
- Existing dependencies and distribution BCC tools are the initial route. Confirm compatibility
  with the active HWE kernel before relying on them; no assertion that a kernel update fixes BDELAY.

## Current evidence and assumptions

- Worktree is clean at the start of this delivery; the earlier monitoring configuration is tracked.
- Kernel 6.14.0-37, BTF, Python 3, kernel headers and passwordless sudo are available.
- Distribution `bpfcc-tools` and its two BCC Python/library dependencies are installed, without
  upgrading other packages. Both tracers work on the active kernel; a direct read was attributed
  to the exact test PID. Biosnoop prints its header before opening perf buffers, so its readiness
  boundary must be instrumented after `open_perf_buffer`, not inferred from the header.
- I/O and memory PSI are readable. `kernel.task_delayacct=1` is already set, but the boot command
  line lacks `delayacct`. GRUB has an existing distribution drop-in and supports local drop-ins.
- Earlier live `/proc/<pid>/task/<tid>/stat` readings contained block-delay totals exceeding thread
  lifetime; the report validator must use thread lifetime/identity, not a single-process time bound.
- The packaged biosnoop has intermittent attribution failure even with a corrected tracepoint
  layout and without execution restrictions; the earlier restriction-causality inference is false.
  Audit found producer-before-completion attachment and unchecked bounded-map writes, which can
  leak startup entries; exhaustion is a supported explanation, not directly recorded proof of the
  earlier failure. The `bcc_ready.py` adapter now gates producers until every hook/buffer is ready,
  asserts empty initial maps, and reports failed map writes separately from perf loss for both
  native tools. No alternate tracer implementation is retained.
- Block attribution can identify kernel workers rather than the original buffered-I/O application;
  snapshots provide complementary context. No claim of universal application attribution is made.

## Execution steps

| Status | Step | Owner and consumers | Validation |
| --- | --- | --- | --- |
| complete | Validate eBPF tools and recording boundaries on the current kernel. | BCC package, block-I/O hooks, capture subprocesses | Package scope checked; latency histograms and exact PID on a bounded direct read verified. |
| complete | Implement pressure detection, capture orchestration, report quality and retention. | Python monitor, configuration, private incident directory | Startup notification, collector gates, empty-map invariant and map-error handling pass focused checks and sensitivity controls. |
| complete | Install service and next-boot delay accounting; prove manual and automatic capture. | Root systemd service, CLI, GRUB drop-in | Repeated full live attribution with zero map failures; final-source bounded trace, generated GRUB and trigger replay pass. |
| complete | Document, independently audit and close delivery. | README, allowlist, persistent plan | README/source-live checks complete; independent audit passed with no unresolved findings. |

## Replan conditions

- BCC cannot attach correctly: select the smallest compatible eBPF route within the approved scope.
- Collector cost or output is excessive: reduce duration/volume while preserving independent I/O
  evidence; never silently claim success after collector failure or truncated evidence.
- Existing configuration or concurrent edits conflict: preserve them and adjust the integration.

## Validation and completion evidence

Use disposable files and controlled injected pressure samples instead of stressing memory/disks.
Retain a sanitized anomaly-shaped fixture and prove that removing validation makes its test fail.
Keep live evidence outside Git. Validate next-boot wiring without claiming an actual reboot test.

Live evidence stays under `/var/log/performance-incidents/`:

- `incident-20260910T022613Z-a9725dd5` and `incident-20260910T022859Z-da753628` each completed a full
  configured window and attributed exactly 32 reads to the known probe PID. Both collectors started
  with empty maps and ended with zero failed map updates. The second records 66063 biosnoop events.
- `incident-20260910T023612Z-d8029eff` validates final source hashes and exact PID attribution in a
  bounded five-second window, with zero map failures. It contains 1561 compared process identities
  and 23 invalid thread counters. Production configuration remains at the configured full duration.
- Unknown queue formatting is verified at the emitted-C/native-format boundary. The final short
  live probe's optional assertion requiring an unknown-queue event did not pass because none occurred;
  this is not claimed as live coverage of that display case. The actual capture, known PID proof,
  source hashes and map statistics passed subsequent explicit checks.
- Failed pre-gating validation artifacts are retained as `partial`, preserving raw data and explicit
  validation errors. Full gated artifacts predate the final unknown-queue display correction.

The focused monitoring suite passes 31 checks. Sensitivity controls demonstrate failures when
delay validation, automatic triggering, tracepoint adaptation, a required callback gate, checked map
writes, empty-map rejection or correct startup-notification ordering are removed. Automatic trigger
replay exercises production orchestration with disposable subprocesses and storage; no host-pressure
stress or claim of a full recorded-session replay is made.

Backups precede installation under
`/var/backups/performance-monitoring/incidents-20260910T015412Z/`. Boot generation contains `delayacct`
once on every Linux entry and passes `grub-script-check`; actual reboot activation remains untested.

## Closure audit

| Status | Requirement | Implementation evidence | Validation evidence |
| --- | --- | --- | --- |
| verified | Independent block I/O, kernel compatibility and attribution limits | `bcc_ready.py`, native tools, layout adaptation, report caveats | Repeated full live PID proofs, NVMe histograms, final-source bounded trace |
| verified | Collector readiness, map capacity errors and unknown queue display | Kernel gates, empty-map activation check, checked writes and native display sentinel | Adapter/activation tests and sensitivity controls; empty initial maps and zero errors in live traces |
| verified | Sustained I/O/memory PSI trigger | `Trigger.observe`, `Monitor.step`, JSON config | Threshold/recovery test and trigger-to-artifact replay; disabled-trigger control fails |
| verified | Manual capture, startup readiness and duplicate suppression | Type=notify after installed signal handlers, SIGUSR1 and capture lock | Immediate-signal socket test and live restart/signal; duplicate test and real flock contention |
| verified | Bounded automatic retries, persistent cooldown | Attempt state before capture; systemd restart limits | Reloaded monitor honors saved cooldown; service has no automatic restart failures |
| verified | Host/process/container context and timestamps | Host ring, snapshots, cgroups, manifest, source hashes | Complete live snapshots and final summary replay; UTC and attribution limits in README |
| verified | Invalid/negative/decreasing delay counters, reuse and exited identities | Per-thread lifetime/identity validation; raw snapshots preserved | Anomaly artifact replay, exited-thread test, multithread and PID-reuse tests; sensitivity control fails |
| verified | Duration/output/resource limits and low-space admission | Startup/window deadlines, stream/episode budgets, unit CPU/memory caps | Timeout, flood, total-budget and free-space tests; successful bounded live window |
| verified | Early failure, cancellation, final exit errors, lost events and crash recovery | Subprocess group cleanup, terminal manifest, recovery | Exit diagnostics, final-exit failure, cancellation, perf/map loss and interrupted-state tests |
| verified | Age/quota retention and whole-incident rotation | Locked prune, tombstones, KEEP/open/active protections | Disposable filesystem tests assert victims, protected data and interrupted deletion |
| verified | Root-only local reports; no environment/payload/full arguments | Whitelisted proc counters; private systemd directories/umask | Installed ownership/modes inspected; collection sources reviewed |
| verified | Persistent system unit in authorized tree | `scripts/systemd/system/performance-incident.service` | Installed bytes match; service enabled and active |
| verified | Next-boot accounting with backup; no kernel upgrade or reboot | GRUB drop-in plus existing runtime sysctl | Generated entries, idempotent fragment, boot syntax; current cmdline still unchanged |
| verified | Preserve prior monitoring, applications, swap and Git authorization | Changes confined to new collector/config/docs/allowlist | Earlier collectors active; no workload restart, commit, staging or push performed |
| verified | Operational documentation and source placement | README installation/update/diagnosis/pinning/removal; allowlist | Source destinations and instruction topology checked; monitoring suite passes |
| verified | Independent final conformance pass | Fresh `incident_final_audit` reviewer | Full final plan/AGENTS/runtime review, independent 31-test run and live artifact replays; all findings resolved |

Forward trace: approved incident diagnosis -> pressure/capture/report owners -> systemd/CLI and
retained reports -> deterministic failure checks and bounded live capture.
Reverse trace: each source, configuration and documentation change must serve the approved incident
capture or next-boot accounting outcome.

### Final conformance verdict

- **Verdict:** PASS. Approved configuration is installed and active; no required work remains.
- **Second pass:** Independent audit passed after startup, collector-map and queue-display findings
  were corrected and their regression protection verified.
- **Unresolved requirements:** None. Next-boot activation and the final live sample's absence of
  unknown-queue events are explicitly bounded validation limitations, not claims of completed tests.
- **Git state:** This completed plan and new source files are allowlisted but untracked; no staging,
  commit or push was requested or performed.
