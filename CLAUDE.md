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
