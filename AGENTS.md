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
