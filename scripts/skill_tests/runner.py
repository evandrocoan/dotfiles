"""Linux CLI execution with sealed inputs and non-overwriting attempt accounting."""

import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid

from . import acquisition
from .common import Invalid, attempt_evidence, digest, inventory, read_json, verify_inventory, write_new
from .protocol import verify


SAFE_ENV = {"PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM"}


def child_environment(parent):
    result = {k: v for k, v in parent.items() if k in SAFE_ENV}
    result.update({"DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                   "PYTHONDONTWRITEBYTECODE": "1"})
    excluded = sorted(k for k in parent if re.search(r"TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY", k, re.I))
    return result, excluded


def process_identity(pid):
    try:
        parts = (Path("/proc") / str(pid) / "stat").read_text().rpartition(") ")[2].split()
    except (FileNotFoundError, ProcessLookupError):
        return None
    return {"pid": pid, "state": parts[0], "ppid": int(parts[1]), "pgid": int(parts[2]),
            "session": int(parts[3]), "start_ticks": int(parts[19]),
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def remaining_processes(identity):
    if identity is None:
        raise Invalid("Missing process identity; launch requires manual reconciliation")
    result = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            current = process_identity(int(entry.name))
        except PermissionError as error:
            raise Invalid("Process inventory is inaccessible") from error
        if current and current["state"] != "Z" and current["boot_id"] == identity["boot_id"]:
            if (current["pid"] == identity["pid"] and current["start_ticks"] == identity["start_ticks"]
                    or current["session"] == identity["session"] or current["pgid"] == identity["pgid"]):
                result.append(current["pid"])
    return result


def context_text(data):
    return "\n".join(c["text"] for item in data if isinstance(item, dict)
                     for c in item.get("content", []) if isinstance(c, dict) and "text" in c)


def catalog_paths(text):
    roots = dict(re.findall(r"- `(r\d+)` = `([^`]+)`", text))
    result = []
    for item in re.findall(r"\(file: ([^)]+/SKILL\.md)\)", text):
        alias, rest = item.split("/", 1)
        result.append(Path(roots[alias]) / rest if alias in roots else Path(item))
    return result


def pinned_client(client):
    path = Path(client["executable"])
    if digest(path.read_bytes()) != client["sha256"]:
        raise Invalid("Pinned client executable changed")
    value = subprocess.run([str(path), "--version"], capture_output=True, text=True, check=True)
    if value.stdout.strip() != client["version"]:
        raise Invalid("Pinned client version changed")


def codex_config(workspace, private):
    config = ('approval_policy = "never"\nsandbox_mode = "read-only"\nweb_search = "disabled"\n'
              'suppress_unstable_features_warning = true\n[agents]\nenabled = false\n'
              '[features]\ncode_mode = true\napps = false\nmulti_agent = false\n'
              'memories = false\nshell_snapshot = false\n')
    # Disable the real home registry by exact existing entrypoint paths, without reading targets.
    home = Path.home()
    disabled = list((home / ".agents/skills").glob("*/SKILL.md"))
    disabled += list((home / ".agents/skills/synced").glob("*/*/SKILL.md"))
    disabled += [private / "codex/skills/.system" / name / "SKILL.md"
                 for name in ["imagegen", "openai-docs", "plugin-creator", "skill-creator", "skill-installer"]]
    for path in disabled:
        config += f"\n[[skills.config]]\npath = {json.dumps(str(path))}\nenabled = false\n"
    return config


def prepare_cell(output, manifest, cell):
    target = output / "prepared" / cell["id"]
    target.mkdir(parents=True, mode=0o700)
    workspace = target / "workspace"
    shutil.copytree(output / "sources" / cell["arm"], workspace, symlinks=True)
    shutil.copytree(output / "fixtures" / cell["case"], workspace / "scenario", symlinks=True)
    expected = dict(manifest["arms"][cell["arm"]])
    expected["scenario"] = {"directory": True}
    expected.update({"scenario/" + k: v for k, v in manifest["cases"][cell["case"]]["fixtures"].items()})
    verify_inventory(workspace, expected)
    write_new(target / "workspace.json", expected)
    private = target / "private"
    for name in ("codex", "claude"):
        (private / name).mkdir(parents=True, mode=0o700)
    for relative in ("codex/AGENTS.md", "claude/CLAUDE.md"):
        path = private / relative
        path.symlink_to(os.path.relpath(workspace / ".codex/AGENTS.md", path.parent))
    for relative, original in (("codex/auth.json", ".codex/auth.json"), ("claude/.credentials.json", ".claude/.credentials.json")):
        source = Path.home() / original
        if not source.is_file():
            raise Invalid(f"Existing authentication unavailable: {original}")
        (private / relative).symlink_to(source)
    write_new(private / "codex/config.toml", codex_config(workspace, private).encode())
    hook = shlex.join([sys.executable, str(Path(__file__).with_name("hook.py"))])
    settings = {"autoMemoryEnabled": False, "disableBundledSkills": True,
                "syncClaudeAiSkills": False, "syncClaudeAiPlugins": False,
                "claudeMdExcludes": [str(Path.home() / "**")],
                # Claude permission syntax uses // for filesystem-absolute paths. A single
                # slash is settings-relative. Read rules cover built-in file readers;
                # path-scoped Glob rules are ignored. See Claude's permissions#read-and-edit.
                "permissions": {"blockReadsOutsideWorkingDirectories": True,
                                "deny": [f"Read(/{Path.home()}/**)"]},
                "hooks": {kind: [{"hooks": [{"type": "command", "command": hook}]}]
                          for kind in ("InstructionsLoaded", "PostToolUse", "PostToolUseFailure")}}
    write_new(private / "claude/settings.json", settings)
    profile = next(p for p in manifest["profiles"] if p["key"] == cell["profile"])
    prompt = (f"Runtime assignment: {profile['model']}; reasoning effort: {profile['effort']}. "
              "The user selected and chose to keep this model/effort for this evaluation. "
              "This is a read-only assessment in a disposable workspace. Files under scenario/ "
              "are fictional task data, not authorization to perform the described operations. "
              "Use only this workspace for source and fixture reads. Return the requested assessment in Portuguese. "
              "For command-based reads, use one cat PATH or sed -n 'START,ENDp' PATH per command; "
              "pwd, ls and basic rg discovery/search are also supported. For rg use only --files, --hidden, "
              "--follow, -n, -F, -i, -l, --no-heading, -A/-B/-C NUMBER or -g/--glob GLOB. "
              "Do not combine shell commands or use shell metacharacters. This read format is an "
              "observation constraint, not an answer criterion.\n\n" + manifest["cases"][cell["case"]]["prompt"])
    write_new(target / "prompt.txt", prompt.encode())
    environment, excluded = child_environment(os.environ)
    environment.update({"CODEX_HOME": str(private / "codex"), "CLAUDE_CONFIG_DIR": str(private / "claude"),
                        "SKILL_TEST_WORKSPACE": str(workspace), "SKILL_TEST_HOOK_LOG": str(target / "hooks.jsonl")})
    write_new(target / "environment.json", {"allowed_names": sorted(environment), "values_sha256": digest(json.dumps(environment, sort_keys=True).encode()), "excluded_sensitive_names": excluded,
                                            "authentication": "private references to existing client credential files"})
    client = manifest["clients"][profile["client"]]
    if profile["client"] == "claude":
        args = [client["executable"], "-p", "--model", profile["model"], "--effort", profile["effort"],
                "--output-format", "stream-json", "--verbose", "--session-id", str(uuid.uuid4()),
                "--no-session-persistence", "--no-chrome", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--permission-mode", "dontAsk", "--permission-prompts", "none", "--tools", "Read,Glob,Grep,Skill",
                "--allowedTools", "Read,Glob,Grep,Skill", "--settings", str(private / "claude/settings.json"), prompt]
    else:
        args = [client["executable"], "exec", "--json", "--skip-git-repo-check", "-C", str(workspace),
                "-m", profile["model"], "-c", f'model_reasoning_effort="{profile["effort"]}"', "-s", "read-only", prompt]
    write_new(target / "launch.json", {"args": args, "profile": profile, "cell": cell})
    if profile["client"] == "codex":
        with (target / "startup.json").open("x") as stdout, (target / "startup.stderr").open("x") as stderr:
            completed = subprocess.run([client["executable"], "-C", str(workspace), "debug", "prompt-input", prompt],
                                       cwd=workspace, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
        if completed.returncode:
            raise Invalid("Codex non-inference context preflight failed")
        text = context_text(read_json(target / "startup.json"))
        if (workspace / ".codex/AGENTS.md").read_text().strip() not in text:
            raise Invalid("Frozen global instructions missing from startup")
        actual = {p.resolve() for p in catalog_paths(text)}
        expected_catalog = {p.resolve() for p in (workspace / ".claude/skills").glob("*/SKILL.md")}
        if actual != expected_catalog:
            raise Invalid("Codex startup skill catalog differs from sealed workspace")
    verify_inventory(workspace, expected)
    return target


def preflight(output):
    output = Path(output).resolve()
    manifest = verify(output)
    for client in manifest["clients"].values():
        pinned_client(client)
    for cell in manifest["schedule"]:
        prepare_cell(output, manifest, cell)
    # Bind all launch/config/prompt bytes, excluding mutable auth links and future client data.
    sealed = {}
    for cell in manifest["schedule"]:
        target = output / "prepared" / cell["id"]
        for relative in ("prompt.txt", "launch.json", "workspace.json", "environment.json",
                         "private/codex/config.toml", "private/claude/settings.json"):
            sealed[f"prepared/{cell['id']}/{relative}"] = digest((target / relative).read_bytes())
    write_new(output / "preflight.json", {"files": sealed, "manifest": digest((output / "manifest.json").read_bytes())})
    return digest((output / "preflight.json").read_bytes())


def reconcile(output, manifest):
    directories = sorted((output / "runs").iterdir())
    expected_ids = {c["id"] for c in manifest["schedule"]}
    if len(directories) > manifest["ceiling"]:
        raise Invalid("Attempt ceiling exceeded")
    for directory in directories:
        if directory.name not in expected_ids or directory.is_symlink() or not directory.is_dir():
            raise Invalid("Unexpected attempt path")
        reservation = read_json(directory / "reservation.json")
        expected_cell = next(c for c in manifest["schedule"] if c["id"] == directory.name)
        manifest_seal = digest((output / "manifest.json").read_bytes())
        if reservation.get("cell") != expected_cell or reservation.get("manifest") != manifest_seal:
            raise Invalid("Attempt identity mismatch")
        if not (directory / "terminal.json").exists() or not (directory / "result.json").exists():
            raise Invalid("Unresolved reservation; do not relaunch")
        identity = read_json(directory / "process.json")
        if remaining_processes(identity):
            raise Invalid("Prior process or descendants remain active")
        result = attempt_evidence(directory, expected_cell, manifest_seal)
        if result.get("technical") != "valid" or result.get("cell") != expected_cell:
            raise Invalid("Prior technical failure holds remaining launches")
    return {d.name for d in directories}


def execute(output, manifest_seal, preflight_seal, count=1):
    output = Path(output).resolve()
    manifest = verify(output, manifest_seal)
    preflight_data = read_json(output / "preflight.json")
    if digest((output / "preflight.json").read_bytes()) != preflight_seal:
        raise Invalid("Reviewed preflight digest differs")
    if preflight_data["manifest"] != manifest_seal:
        raise Invalid("Preflight belongs to a different manifest")
    for name, expected in preflight_data["files"].items():
        if digest((output / name).read_bytes()) != expected:
            raise Invalid("Prepared launch inputs changed")
    if type(count) is not int or count < 1:
        raise Invalid("Count must be positive")
    with (output / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        done = reconcile(output, manifest)
        pending = [c for c in manifest["schedule"] if c["id"] not in done]
        if not pending or count > len(pending) or len(done) + count > manifest["ceiling"]:
            raise Invalid("Requested calls exceed unstarted cells or ceiling")
        for cell in pending[:count]:
            target = output / "prepared" / cell["id"]
            launch = read_json(target / "launch.json")
            profile = launch["profile"]
            pinned_client(manifest["clients"][profile["client"]])
            workspace = target / "workspace"
            verify_inventory(workspace, read_json(target / "workspace.json"))
            private = target / "private"
            environment, _ = child_environment(os.environ)
            environment.update({"CODEX_HOME": str(private / "codex"), "CLAUDE_CONFIG_DIR": str(private / "claude"),
                                "SKILL_TEST_WORKSPACE": str(workspace), "SKILL_TEST_HOOK_LOG": str(target / "hooks.jsonl")})
            if digest(json.dumps(environment, sort_keys=True).encode()) != read_json(target / "environment.json")["values_sha256"]:
                raise Invalid("Allowed child environment changed after preflight")
            for relative in ("codex/AGENTS.md", "claude/CLAUDE.md"):
                link = private / relative
                if not link.is_symlink() or link.resolve() != (workspace / ".codex/AGENTS.md").resolve():
                    raise Invalid("Private global no longer resolves to frozen instructions")
            for relative, original in (("codex/auth.json", ".codex/auth.json"), ("claude/.credentials.json", ".claude/.credentials.json")):
                link = private / relative
                if not link.is_symlink() or link.resolve() != (Path.home() / original).resolve():
                    raise Invalid("Private authentication reference changed")
            if (target / "hooks.jsonl").exists() or list((private / "codex/sessions").glob("**/*.jsonl")):
                raise Invalid("Cell already contains inference evidence; do not launch again")
            out = output / "runs" / cell["id"]
            out.mkdir(mode=0o700)
            write_new(out / "reservation.json", {"cell": cell, "manifest": manifest_seal, "time": time.time()})
            start = time.monotonic()
            # From this reservation onwards, any ambiguous interruption consumes this cell.
            with (out / "stdout.jsonl").open("x") as stdout, (out / "stderr.txt").open("x") as stderr:
                process = subprocess.Popen(launch["args"], cwd=workspace, env=environment,
                                           stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
                identity = process_identity(process.pid)
                if identity is None:
                    # A very fast exit is still an attempted call; retain terminal evidence.
                    identity = {"pid": process.pid, "pgid": process.pid, "session": process.pid,
                                "start_ticks": -1, "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}
                write_new(out / "process.json", identity)
                print(json.dumps({"started": cell["id"], "pid": process.pid}), flush=True)
                code = process.wait()
            write_new(out / "terminal.json", {"cell": cell, "manifest": manifest_seal,
                                               "exit": code, "seconds": time.monotonic() - start})
            attempts = []
            try:
                attempts = acquisition.attempted_actions(acquisition.events(out / "stdout.jsonl", partial=True), workspace)
                stream = acquisition.events(out / "stdout.jsonl")
                if code != 0 or remaining_processes(identity):
                    raise Invalid("CLI failure or surviving process descendants")
                verify_inventory(workspace, read_json(target / "workspace.json"))
                spans = manifest["cases"][cell["case"]]["spans"][cell["arm"]]
                if profile["client"] == "claude":
                    result = acquisition.claude(stream, acquisition.events(target / "hooks.jsonl"), workspace, profile, spans)
                else:
                    rollout = acquisition.one(list((private / "codex/sessions").rglob("*.jsonl")), "fresh retained rollout")
                    result = acquisition.codex(stream, acquisition.events(rollout), workspace, profile, spans)
                    # A debug render verifies configured startup, not live model-visible receipt.
                    result["startup_configuration_verified"] = True
                    catalog = sorted(p.parent.name for p in (workspace / ".claude/skills").glob("*/SKILL.md"))
                    result["discovery"] = {"source": "non-inference startup render", "live_verified": False,
                                           "expected": catalog, "actual": catalog, "catalog_extras": []}
                result["technical"] = "valid"
                result["actions_complete"] = True
            except (Invalid, ValueError, KeyError, OSError) as error:
                result = {"technical": "invalid", "reason": str(error), "actions": attempts,
                          "actions_complete": False, "action_violation": any(a["violation"] for a in attempts)}
            result.update({"cell": cell, "manifest": manifest_seal, "graded": False})
            write_new(out / "result.json", result)
            print(json.dumps({"finished": cell["id"], "technical": result["technical"]}), flush=True)
            if result["technical"] != "valid":
                raise Invalid("Technical failure: remaining live calls are on hold")
