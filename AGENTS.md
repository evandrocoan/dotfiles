# Dotfiles Repository

This is the user's home directory tracked as a git repository (Linux Mint
XFCE / Ubuntu). Only explicitly allowlisted files are tracked — the
`.gitignore` starts with `*` (ignore everything) and then uses `!` rules to
opt specific files and directories back in.

## Repository structure

```
~/
├── .bashrc / .bash_logout / .inputrc  # shell config
├── .vimrc                             # Vim config
├── .gitconfig                         # global git config
├── .ssh/config                        # SSH host aliases
├── .config/
│   ├── smartgit/22.1/                 # SmartGit preferences & tools
│   ├── copyq/copyq.conf               # CopyQ clipboard manager config
│   ├── terminator/config              # Terminator terminal emulator
│   ├── remmina/remmina.pref           # Remmina RDP/VNC client prefs
│   ├── xfce4/                         # XFCE4 panel, window manager, keybinds
│   ├── Thunar/                        # Thunar file manager config
│   ├── gtk-3.0/                       # GTK3 theme/settings
│   ├── autokey/                       # AutoKey keyboard automation
│   ├── k9s/                           # k9s Kubernetes TUI config
│   └── okularpartrc                   # Okular PDF viewer config
├── .local/
│   ├── bin/                           # custom scripts and wrappers
│   ├── share/applications/            # custom .desktop entries
│   ├── share/nemo/actions/            # Nemo right-click actions
│   ├── share/xfce4/helpers/           # XFCE4 preferred app helpers
│   └── share/themes/border-only/      # custom XFCE4 window theme
└── scripts/                           # automation scripts (see below)
```

## scripts/ directory

Python environment is managed with **Poetry**. The virtualenv lives at
`~/scripts/.venv/` (in-project). Scripts in `~/.local/bin/` that use Python
point their shebang directly to `~/scripts/.venv/bin/python`.

To set up after a fresh clone:
```bash
cd ~/scripts
poetry config virtualenvs.in-project true --local
poetry install
```

Key scripts:

| File | Purpose |
|---|---|
| `check_ci` | Bash: polls a list of IPs on port 22, sends desktop notification on failure |
| `smartgit_create_mr.py` | Python: SmartGit external tool — commits with `oco` (OpenCommit), creates branch, pushes, opens MR on GitLab. Reads `GITLAB_TOKEN`/`GITLAB_PAT` and `GITLAB_URL` from env / `.env` |
| `check_clock_punches_playwright.py` | Python/Playwright: checks clock-punch records |
| `hypervisor_clock_punches_playwright.py` | Python: supervises the playwright clock checker |
| `on_unlock_screen.py` | Triggered on screen unlock events |
| `build_xfce4.sh` | Builds XFCE4 panel and plugins from source into `~/.local/` |
| `restore_xfce_shortcuts.sh` | Restores XFCE4 keyboard shortcuts |
| `create-remmina-desktops.sh` | Generates `.desktop` icons from saved Remmina connections |
| `upload_to_s3_glacier_deep.sh` | Uploads files to S3 Glacier Deep Archive |

### Standalone CLI dependencies

For standalone multi-command scripts such as `.local/bin/codex-session-stats`, import
command-specific optional dependencies only inside the function or subcommand that uses them.
Keep shared startup, unrelated commands and help independent of those packages. A missing
optional package must fail only the operation that needs it, with an actionable diagnostic.
Apply the same isolation to future command-specific dependencies so adding one feature does not
break the rest of the standalone CLI.

### GitLab monitor work ownership

Preserve the [simple queue contract](architecture/gitlab-monitor-simple-queue.md). One durable
FIFO and one consumer own all repositories, keyed by authenticated GitLab repository ID plus MR
IID. Coalesce unstarted automatic work per MR at its oldest FIFO position, preserving original
event lineage and freezing membership at reservation. Previously admitted human work and issued work
remain separate. Every configured reviewer runs in order after success or any terminal failure; no quota
classifier or fallback mode. Agents investigate the MR link and publish directly through the existing ordinary GitLab MCP.
Both reviewers read complete current threads, including their peer's findings, explain verified
fixes/invalid concerns before resolving and preserve remaining concerns. Different defects on the
same line remain separate. No private review MCP, per-send monitor journal or final JSON review
report is used for new stages. Normal tool permissions bound operations; current head/open-state,
human scope and whole-discussion checks at publication belong to the reviewer and are not equivalent
to the retired runtime gates. Already admitted historical intake remains read-only.

New chats handle human followups directly, without assessment JSON, classification calls or human
FIFO admission. Manual work is outside automatic serialization. Observe only already held automatic
questions, preserving exact original native input/final and context. The native model owns answer
sufficiency; native identities prove source/order. Append continuations under the original stage
and use its effective result everywhere without replacing the original final or fabricating stages.
Generic/interrupted replies retain holds; resumed failures follow reviewer continuation/retry;
newer-head completion gives no old-head credit. Preserve historical question readers and uncertain
effect fences outside explicit operator abandonment, without repair classifiers. Never scan
completed chats for new human jobs.

Keep exact native input/result identity, sufficient-answer holds and actual code checkpoints.
Readable final statuses are admitted only from the exact native terminal final. Snapshot current
question scope before establishing a new automatic hold; snapshot failure blocks that MR until
recovery, without retaining capacity after proven termination. Human scope never expands.
Passively collect authenticated normal tool outputs to filter only proven self-generated inventory
deltas. Preserve external edits and same-account human notes; missing results remain eligible.
Passive inventory retires only never-issued self-only automatic discussion work, retaining its
original admissions.
New input formats must not alter historical validators. Proven-unissued old preparations may be
archived outside executed attempts; preserve successful reviewers and selective retries. Unknown
execution cannot release capacity or be relaunched. Normal recovery of historical uncertain sends
remains read-back-only. New instructions use fresh chats without rewriting old chats or native
history. Original consumer chats remain valid human and hold sources. Only actual completed code
review advances a code checkpoint. Explicit restart preserves retired questions and late answers as
read-only.

An explicit local operator MR restart may retire captured pending automatic work, questions and
unresolved historical public-effect delivery after proven native termination and a fresh open-MR/head
read. Preserve original evidence and uncertainty as abandoned, never as an acknowledgment, human
answer or review. Its durable receipt authorizes one full review of the authenticated head, at the
FIFO tail with new chats; repetition cannot consume later arrivals. Normal recovery remains
read-back-only. Strict held-round restart cannot abandon effects; explicitly retired effects no
longer block subsequent work. Independent human work and unknown execution are not discarded.

Each round snapshots the current named Codex project's ordered folders and necessary shared Git
metadata once for both reviewers and recovery. The model chooses repositories, branches and tests;
the monitor must not maintain checkout mappings or a command catalog. Admitted reviews can execute
and edit there without command approvals; intake remains read-only. Use thread/launch-local
permissions: mutable Codex reviews use native full access and Claude review shells are unsandboxed.
These trusted processes can access monitor/native state; validators are application checks, not
an OS boundary against them. Intake explicitly reselects read-only permissions. Manual Codex turns
may inherit the last review permissions. Retain original consumer chat contexts when fresh chats
are needed after folder/instruction changes. Do not update loaded historical instructions.

### Systemd user services

Installed via `cp -rv ~/scripts/install/* ~/.config/` followed by
`systemctl --user daemon-reload`. Services live under
`scripts/install/systemd/user/`:

- `check_ci.service` — runs `check_ci` on a schedule
- `check_clock_punches_playwright.service` — runs playwright clock checker
- `supervise_clock_punches_playwright.service` — supervisor for the above
- `hypervisor_clock_punches_playwright.service` — hypervisor layer
- `monitor_screen_locked.service` — monitors screen lock/unlock events

To view logs: `journalctl --user -u <service-name> -f`

### System services

Host-level units installed under `/etc/systemd/system/` live in
`scripts/systemd/system/`. Keep them outside `scripts/install/`, because that tree is copied to
`~/.config/` and is reserved for per-user configuration. Install system units explicitly as root;
document their copy, enablement, diagnostics, update, and removal commands in `README.md`.

## Documentation placement

`README.md` is the primary user-facing operations guide for this dotfiles repository. When
implementing durable automation or a system integration, update it if the change creates or changes
steps a person needs to install, enable, run, diagnose, recover, update, or remove the feature. Keep
the runbook concise and point to the authoritative source files instead of duplicating their
implementation details.

Do not add one-off investigation notes, internal implementation details, test inventories, or
behavior that is clear from a single source file. A diagnosis or review alone does not authorize a
README change. Keep reusable agent-only constraints in `AGENTS.md`; use a dedicated document only
when an operational procedure would make the main README disproportionately long.

## Investigating slowness or performance incidents

This host has a historical performance-monitoring stack already installed and running
(atop/atopacctd/netatop-bpf, sysstat/sar, Netdata, and a bounded eBPF incident capture). See
[Historical performance monitoring](README.md#historical-performance-monitoring) in `README.md` for
the collectors, their retention, and the query commands.

Before running ad-hoc live diagnostics (`ps`, `top`, `free`, `vmstat`) to investigate a slowness
report about a past time window, reconstruct that window from the historical recorders first —
live tools only show the current instant, not what happened during the reported window. Live
diagnostics remain appropriate for an ongoing, currently-reproducible issue.

## .gitignore strategy

The ignore file uses an allowlist pattern:
1. Line 3 (`*`) ignores everything by default
2. Every tracked file/directory is explicitly added with `!` rules
3. Sensitive paths like `.env*` and SSH keys are excluded even when parent
   dirs are allowed

When adding new files to track, add the full path with `!` in `.gitignore`.
Parent directories must also be explicitly allowed before files within them
can be unignored.

## XFCE4 custom build

The panel (`~/.local/bin/xfce4-panel`) is built from source. After
rebuilding with `build_xfce4.sh`, sync system plugins with the loop in
README.md. Restart the panel with:
```bash
pkill xfce4-panel; sleep 1
NO_AT_BRIDGE=1 \
XFCE_PANEL_PLUGIN_PATH=$HOME/.local/lib/xfce4/panel/plugins:/usr/lib/x86_64-linux-gnu/xfce4/panel/plugins \
~/.local/bin/xfce4-panel &
```

## Claude Code config

`~/.claude/settings.json` — permission allowlist for read-only git commands
(`git *status`, `git *log`, `git *diff`) so they run without prompts.

`~/.claude/CLAUDE.md` (global, not this file) — behavioral instructions for
Claude: commit style, when to commit, etc.

## Shared skill maintenance

Follow [Update the shared skill creator](README.md#update-the-shared-skill-creator) when refreshing
the imported creator package. Its local entrypoint owns shared-client adaptations; the manifest
identifies the imported snapshot. Keep runtime system skills untouched and update imported files
only through that procedure. Policy changes belong in their existing owning skill, with coupled
consumers checked through `documentation` rather than synchronized copies.

## Gitignore allowlist

This home repository uses an allowlist strategy: `*` ignores everything by
default and files are opted in with `!` rules. When asked to commit a file
that is not tracked or is ignored, follow this procedure before staging:

1. Run `git check-ignore -v <file>` to identify the rule excluding it.
2. If the file should be tracked, add specific `!` rules to `.gitignore`.
   Explicitly allow parent directories when needed.
3. Confirm the file is no longer ignored. Also verify that associated secrets
   (for example, the real `.env` file) remain ignored with `git check-ignore
   -v <secret-file>` and `git status --short --ignored <directory>`.
4. Stage the file with ordinary `git add <file>`.
5. Before committing, inspect the staged content with `git diff --cached --
   <file>`.

Never use `git add -f` to bypass `.gitignore`. The only exception requires an
explicit user request confirming that `.gitignore` must remain unchanged.

## Updating the tracked home repository

The work tree is permanently dirty by design. It carries long-lived
uncommitted work, and every path listed by `git ls-files -v | grep '^h '` is
hidden with `assume-unchanged`, so a clean `git status` does not mean the
work tree matches `HEAD`.

Never run `git stash`, `git reset --hard`, `git checkout -- .`, `git clean`,
or `git pull` with this repository root as the work tree. Tracked files here
are live configuration read by running desktop applications, so reverting
them changes application state, and untracked files are real work. An
in-place fast-forward also aborts whenever a locally modified file was also
changed upstream, which is the condition that makes the isolated helper
necessary.

Updating from `origin` goes through `scripts/isolated_pull.sh`, which moves
`.git` out of the work tree and pulls inside an isolated tree. It returns the
database only after the supervised pull process group stops and unfinished Git operations are
aborted; otherwise it stays isolated for manual recovery.
It mutates Git state, so run it only on explicit user request. Reviewing the
resulting difference and deciding what to keep or revert is the user's manual
step; never decide it for them, and never re-apply a dropped
`assume-unchanged` flag automatically, because that hides the upstream change
still under review.

If `$HOME/.git` is missing, an isolated run did not return the database. It is
under `~/.local/state/isolated-pull`; follow [recover an interrupted isolated
pull](README.md#recover-an-interrupted-isolated-pull) instead of improvising
a repair.
