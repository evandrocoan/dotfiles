# Implementation plan: Repository test coverage

**Status:** Completed
**Mode:** Plan and execute

## Outcome

GitHub Actions runs every deterministic, repository-owned test plus syntax and configuration
checks, while host-specific eBPF validation remains an explicit local check. Existing scripts that
rename files or create remote changes gain hermetic regression protection, and Redmine dry-run
performs no network access.

## Scope

### In scope

- Move the embedded Redmine parser tests into a discoverable `unittest` module, strengthen their
  assertions, and protect dry-run from HTTP calls.
- Extend TeamViewer watchdog coverage through its replay, CLI parsing, and dispatch boundaries.
- Test SmartGit remote parsing, API request construction, and main orchestration with Git, HTTP,
  input, and browser effects replaced by exact fakes.
- Refactor the Windows ZIP path repair script behind an import-safe function and test renames,
  unchanged paths, and collision preservation in disposable directories.
- Add deterministic Python, Bash, JSON, and repository configuration checks to the workflow and
  synchronize the README commands.

### Out of scope

- Running netatop/eBPF checks on GitHub-hosted runners or installing a self-hosted runner.
- Running or changing test suites owned by the tmux submodules.
- Exercising live GitLab, Redmine, Pushover, browser, desktop, or systemd service effects.
- Committing or pushing the changes.

## Governing decisions and invariants

- `AGENTS.md` owns the allowlist, documentation placement, and systemd source layout rules.
- The user approved all recommendations from the repository test audit.
- CI additions use Python's standard library and existing runner commands; manifests, lockfiles,
  and the machine's installed packages remain unchanged.
- Tests use disposable paths and explicit fakes for external effects. No test may send data,
  rename user files, restart services, open a browser, or depend on credentials.
- `.github/workflows/tests.yml` remains read-only and host-specific validation remains documented
  as local.

## Initial evidence and assumptions

### Initially verified evidence

- The workflow currently runs 31 performance-monitoring and 12 TeamViewer tests.
- Fifteen embedded Redmine pytest tests pass, but `test_basic_load` has no assertion and pytest is
  not a direct project dependency.
- All tracked Bash files pass `bash -n`; all tracked Python files compile, with an invalid-escape
  `SyntaxWarning` in `.local/bin/movescreen.py`.
- Two netatop tests require `/run/netatop-bpf-socket`; tmux tests belong to Git submodules.

### Planning assumptions

- GitHub's Ubuntu runner provides Bash and Python 3.12 as configured by the existing workflow.
- Systemd semantic verification may be unsuitable for the hosted runner when units reference
  host-installed executables; repository-owned configuration checks will cover deterministic
  invariants without pretending to prove live activation.

## Execution steps

| Status | Step | Affected owner and consumers | Validation |
| --- | --- | --- | --- |
| completed | Extract and strengthen Redmine tests; make dry-run local-only. | `.local/bin/redmine_time_send.py`, `scripts/test_redmine_time_send.py` | Nine focused `unittest` cases cover the legacy scenarios, exact parser output, title caching, no-boundary dry-run, confirmations, and POST payload. |
| completed | Add deterministic tests around TeamViewer, SmartGit, and path repair boundaries. | Runtime scripts and `scripts/test_*.py` consumers | Focused suites cover replay/CLI dispatch, exact Git/API calls, import safety, encoded renames, collision preservation, and traversal rejection. |
| completed | Add static and configuration checks to CI and correct the Python warning. | Workflow, tracked Python/Bash/JSON/configuration files | Exact workflow commands pass; warning-as-error catches the original escape; malformed fixture sensitivity checks fail. |
| completed | Synchronize the README and run the full repository CI-equivalent gate. | README test runbook and all deterministic test suites | The README and workflow invoke `scripts/run_repository_tests.sh`; 31 monitoring and 40 general tests plus Python and Bash syntax checks pass with no skips. |
| completed | Audit and deliver. | Complete diff, plan, instructions, consumers, and validation evidence | Bidirectional closure matrix and independent conformance review passed; this plan is stored in `completed/`. |

## Replan conditions

- A proposed test requires a new dependency, credentials, network, root, desktop state, or a
  non-disposable resource.
- Refactoring reveals a runtime compatibility contract that cannot be preserved without a broader
  design choice.
- Hosted-runner systemd checking cannot distinguish source errors from intentionally absent host
  executables.
- Concurrent user changes overlap any affected file.

## Completion evidence

- `bash scripts/run_repository_tests.sh` passes 31 performance-monitoring and 40 general tests,
  followed by warning-as-error Python compilation and Bash syntax checking.
- Negative controls prove the new tests reject missing Redmine parser output, an altered SmartGit
  API payload, the original destructive path-repair import, and the original invalid Python escape.
- The false-positive audit finds assertion signals in all 71 test methods, and the central runner
  rejects unexpected arguments with exit status 2.
- Path-repair tests also prove that regular and dangling-symlink collisions preserve every source,
  a non-directory parent cannot cause a partial batch, and symlink parents cannot redirect a write.
- The workflow YAML parses locally and its `unit-tests` job invokes the same central gate documented
  in `README.md`; dependency manifests remain unchanged.
- The central gate passes when invoked outside the repository with an unexpected `GITLAB_URL`; its
  trace confirms `bash -n` covers 29 discovered Bash sources, including `.bashrc`, `.bash_logout`,
  and extensionless `scripts/check_ci`.

## Closure audit

Reread this plan, `AGENTS.md`, the final implementation, and validation evidence before completing
the matrix.

| Status | Requirement source | Requirement | Implementation evidence | Validation evidence |
| --- | --- | --- | --- | --- |
| verified | Outcome | Deterministic repository tests and checks run in GitHub Actions. | `.github/workflows/tests.yml` calls `scripts/run_repository_tests.sh`, which discovers both repository suites, compiles visible Python, and syntax-checks Bash files found by suffix, shell configuration name, or shebang. | Workflow YAML parses and its `unit-tests` job contains the central command; the command exits 0 locally. |
| verified | Scope | Redmine tests are discoverable and dry-run cannot access network or credentials. | Embedded pytest cases moved to `scripts/test_redmine_time_send.py`; production boundaries are injectable and `--dry-run` returns before credential and HTTP setup. | Nine discovered tests pass; forbidden boundary fakes and a missing credential path remain untouched; missing parser output fails the exact-output negative control. |
| verified | Scope | TeamViewer replay/CLI behavior has hermetic protection. | `scripts/test_teamviewer_session_watchdog.py` covers detection order, replay, follower/limiter routing, numeric validation, and CLI dispatch with mocks. | Seventeen TeamViewer cases run inside the 40-test general suite and pass without calling the restart function. |
| verified | Scope | SmartGit Git/HTTP/orchestration behavior has exact fake-boundary protection. | `scripts/test_smartgit_create_mr.py` fixes its import environment and replaces optional imports, Git, HTTP, input, subprocesses, and the browser at their boundaries; production validates the token before local or remote effects. | Four tests pass under an unexpected inherited `GITLAB_URL`; changing `remove_source_branch` fails the exact-call assertion, and missing-token assertions prove every effect boundary remains uncalled. |
| verified | Scope | Path repair is import-safe and tested only in disposable directories. | `.local/bin/fix_windows_zip_paths.py` exposes guarded functions, validates the complete rename batch, and rejects target collisions, traversal components, symlink parents, and non-directory parents. | Four `TemporaryDirectory` tests pass for import safety, separator repair, no-partial-write preflight, and lexical/symlink traversal; the original import fails the sensitivity control. |
| verified | Invariants | CI adds no package dependency and performs no external or privileged effects. | New tests use `unittest`, `tempfile`, and exact fakes; the runner uses existing Bash, Git, and Python commands. | Dependency manifests have no diff; the full gate passes without credentials, network access, root, service changes, or user-file renames. |
| verified | Invariants | Live eBPF and submodule suites remain outside the hosted workflow. | The runner selects the hermetic performance unit suite and top-level repository tests; it does not invoke the privileged live test or submodule-owned suites. | The 31+40 test counts contain no live netatop test, and README keeps eBPF verification local. |
| verified | Documentation | README commands and limitations match the workflow. | The Repository tests section names the workflow and invokes `bash scripts/run_repository_tests.sh`. | Manual comparison confirms the same command in README and workflow, with the netatop limitation linked to its runbook. |
| verified | Validation | Focused sensitivity and complete CI-equivalent checks pass. | Test fixtures include malformed JSON/systemd, exact boundary assertions, warning-as-error compilation, and preflight preservation for every path-repair conflict type. | 71 tests, Python compilation, syntax checks of all 29 discovered Bash sources, YAML parsing, negative/sensitivity controls, hostile-environment execution, and `git diff --check` pass. |
| verified | Delivery | Final diff contains only authorized work and remains uncommitted. | Status contains the workflow, runtime fixes, tests, runner, README, and this implementation plan; generated bytecode was removed. | `git status --short` shows no unrelated generated files; no commit or push was performed. |

- Architecture to implementation: every scoped behavior maps to a runtime/test pair or the central
  runner and workflow; the README owns the reusable local command and host-only limitation.
- Implementation to authority: every changed file traces to the approved recommendations, the
  allowlist/documentation rules in `AGENTS.md`, or the plan's audit evidence.

### Final conformance verdict

- **Verdict:** PASS
- **Second pass:** PASS after resolving every finding from the first independent review.
- **Auditor and evidence:** `/root/repository_test_final_audit` independently reread the plan,
  instructions, complete diff, and new files; reran the 31+40 tests and static checks; traced all 29
  Bash syntax checks; reproduced path preflight preservation; ran the gate from `/tmp` with an
  unexpected `GITLAB_URL`; and confirmed that missing-token SmartGit execution calls no effect
  boundary. The auditor reported no remaining findings or worktree artifacts.
- **Unresolved requirements:** None.
