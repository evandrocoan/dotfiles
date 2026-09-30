#!/usr/bin/env python3
"""Wait for Claude outside Codex turns and resume one exact Codex CLI session."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["run_claude", "done", "needs_user"]},
        "claude_prompt": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["action", "claude_prompt", "message"],
    "additionalProperties": False,
}

DECISION_INSTRUCTION = (
    "Coordinate this task in the existing Codex CLI session. Inspect the checkout and any "
    "result below before deciding. Reply only with the requested JSON schema. Choose "
    "run_claude with a complete, self-contained Claude task prompt when implementation or "
    "tests remain; choose done only after verifying completion; choose needs_user when an "
    "essential decision is missing. Do not tell Claude about later Codex work. The host "
    "supervisor will run Claude and return its compact terminal result.\n\n"
)


class SupervisorError(RuntimeError):
    """A prerequisite or process state needs explicit reconciliation."""


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise SupervisorError(f"Expected a JSON object: {path}")
    return value


def proc_start_time(pid: int) -> str | None:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    fields = stat[stat.rfind(")") + 2 :].split()
    if len(fields) < 20:
        raise SupervisorError(f"Cannot identify worker PID {pid}")
    return fields[19]


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()


def live_process_group_members(group_id: int) -> list[tuple[int, str]]:
    """Find live members of Claude's private process group, excluding zombies."""
    members: list[tuple[int, str]] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            stat = (entry / "stat").read_text(encoding="utf-8")
        except (FileNotFoundError, ProcessLookupError):
            continue
        fields = stat[stat.rfind(")") + 2 :].split()
        if len(fields) >= 20 and fields[0] not in {"Z", "X"} and fields[2] == str(group_id):
            members.append((int(entry.name), fields[19]))
    return members


def wait_for_process_group(group_id: int, run_dir: Path) -> None:
    """Wait for descendants after Claude exits, without resuming a Codex turn."""
    while True:
        members = live_process_group_members(group_id)
        if not members:
            # The process-group existence check closes a /proc scan race in which
            # a member forks and exits while the directory snapshot is traversed.
            try:
                os.killpg(group_id, 0)
            except ProcessLookupError:
                return
            raise SupervisorError(f"Claude process group {group_id} is still present but "
                                  "has no identifiable live member; reconcile it")
        pid, start_time = members[0]
        try:
            pid_fd = os.pidfd_open(pid)
        except ProcessLookupError:
            continue
        try:
            # Bind the group observation to the acquired handle before waiting.
            if (pid, start_time) not in live_process_group_members(group_id):
                continue
            waiting_path = run_dir / "group_waiting.json"
            if not waiting_path.exists():
                atomic_json(waiting_path, {"process_group": group_id,
                                           "pid": pid, "start_time": start_time})
            poller = select.poll()
            poller.register(pid_fd, select.POLLIN)
            poller.poll()
        finally:
            os.close(pid_fd)


def validated_argv(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SupervisorError(f"{name} must be a list of argument strings")
    return value


def validate_config(config: dict[str, Any], state_dir: Path) -> None:
    checkout = config.get("checkout")
    if (not isinstance(checkout, str) or not Path(checkout).is_absolute() or
            not Path(checkout).is_dir()):
        raise SupervisorError("config.checkout must be an existing absolute directory")
    checkout_path = Path(checkout).resolve()
    if state_dir.is_relative_to(checkout_path):
        raise SupervisorError("State and raw logs must be outside the checkout")
    for name in ("codex", "claude"):
        entry = config.get(name)
        if not isinstance(entry, dict) or not isinstance(entry.get("bin"), str):
            raise SupervisorError(f"config.{name}.bin is required")
        validated_argv(entry.get("args"), f"config.{name}.args")
    claude_args = config["claude"]["args"]
    if "--model" not in claude_args or "--permission-mode" not in claude_args:
        raise SupervisorError("Claude model and permission mode must be explicit")
    managed = {"-p", "--print", "--output-format", "--verbose", "--session-id", "--resume"}
    if managed.intersection(claude_args):
        raise SupervisorError("Claude args contain supervisor-owned CLI flags")


def parse_claude_result(raw_path: Path, stderr_path: Path, exit_code: int | None,
                        launch_error: str | None) -> dict[str, Any]:
    result: dict[str, Any] | None = None
    alerts: list[str] = []
    with raw_path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                alerts.append("Malformed Claude JSONL event")
                continue
            if not isinstance(event, dict):
                alerts.append("Non-object Claude JSONL event")
                continue
            event_type = event.get("type")
            if event_type == "result":
                result = event
            elif event_type == "error":
                alerts.append(str(event.get("error", "Claude error event")))
            elif event_type == "permission_denied" or (
                    event_type == "system" and event.get("subtype") == "permission_denied"):
                alerts.append("Permission denied: " + str(event.get("message") or event))
            elif event_type == "system" and event.get("subtype") == "init":
                for key in ("errors", "warnings", "plugin_errors", "mcp_errors"):
                    if event.get(key):
                        alerts.append(f"Startup {key}: {event[key]}")
                for server in event.get("mcp_servers") or []:
                    if isinstance(server, dict) and server.get("status") in {"failed", "error"}:
                        alerts.append(f"MCP startup: {server.get('name', 'unknown')}: "
                                      f"{server.get('status')}")
            elif event_type == "system" and event.get("subtype") == "warning":
                alerts.append(str(event.get("message", "Claude warning event")))
    diagnostics: list[str] = []
    omitted_diagnostics = 0
    with stderr_path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if re.search(r"error|fail|denied|warn|exception|traceback|fatal|block|limit|permission|mcp",
                         line, re.IGNORECASE):
                if len(diagnostics) < 20:
                    diagnostics.append(line.strip()[:500])
                else:
                    omitted_diagnostics += 1
    return {
        "exit_code": exit_code,
        "launch_error": launch_error,
        "session_id": result.get("session_id") if result else None,
        "final_answer": result.get("result") if result else None,
        "is_error": result.get("is_error") if result else None,
        "result_subtype": result.get("subtype") if result else None,
        "result_errors": result.get("errors") if result else None,
        "termination_reason": (result.get("terminal_reason") or result.get("stop_reason") or
                               result.get("reason")) if result else None,
        "permission_denials": result.get("permission_denials") if result else None,
        "observed_models": list(result.get("modelUsage") or {}) if result else [],
        "startup_and_event_alerts": alerts,
        "stderr_diagnostics": diagnostics,
        "omitted_stderr_diagnostics": omitted_diagnostics,
        "result_event_present": result is not None,
    }


def worker(state_dir: Path, run_id: str) -> int:
    session = read_json(state_dir / "session.json")
    config = session["config"]
    run_dir = state_dir / "runs" / run_id
    run = read_json(run_dir / "run.json")
    atomic_json(run_dir / "worker.json", {
        "pid": os.getpid(), "start_time": proc_start_time(os.getpid()),
        "boot_id": boot_id(),
    })
    claude = config["claude"]
    session_flag = "--session-id" if run["first"] else "--resume"
    command = [claude["bin"], "-p", "--output-format", "stream-json", "--verbose",
               *claude["args"], session_flag, session["claude_session_id"]]
    exit_code: int | None = None
    launch_error: str | None = None
    group_quiescent = False
    with (run_dir / "prompt.txt").open("rb") as prompt, \
            (run_dir / "claude.stdout.jsonl").open("wb") as raw, \
            (run_dir / "claude.stderr.log").open("wb") as errors:
        try:
            process = subprocess.Popen(command, cwd=config["checkout"], stdin=prompt,
                                       stdout=raw, stderr=errors, close_fds=True,
                                       start_new_session=True)
        except OSError as exc:
            launch_error = f"{type(exc).__name__}: {exc}"
            group_quiescent = True  # No Claude process was launched.
        else:
            atomic_json(run_dir / "claude_process.json", {
                "pid": process.pid, "start_time": proc_start_time(process.pid),
                "boot_id": boot_id(), "process_group": process.pid,
            })
            exit_code = process.wait()
            wait_for_process_group(process.pid, run_dir)
            group_quiescent = True
    compact = parse_claude_result(run_dir / "claude.stdout.jsonl",
                                  run_dir / "claude.stderr.log", exit_code, launch_error)
    compact["run_id"] = run_id
    compact["expected_session_id"] = session["claude_session_id"]
    compact["claude_process_group_quiescent"] = group_quiescent
    atomic_json(run_dir / "terminal.json", compact)
    return 0


def wait_for_worker(run_dir: Path, child: subprocess.Popen[bytes] | None) -> None:
    if child is not None:
        status = child.wait()
        if status != 0:
            raise SupervisorError(f"Worker exited {status}; inspect {run_dir}")
    else:
        if (run_dir / "terminal.json").exists():
            return
        identity_path = run_dir / "worker.json"
        if not identity_path.exists():
            raise SupervisorError(f"Worker launch is ambiguous; inspect {run_dir}")
        identity = read_json(identity_path)
        pid = identity.get("pid")
        if not isinstance(pid, int) or pid < 1:
            raise SupervisorError(f"Invalid worker identity in {identity_path}")
        if identity.get("boot_id") != boot_id():
            raise SupervisorError(f"Worker belongs to another boot; inspect {run_dir}")
        try:
            pid_fd = os.pidfd_open(pid)
        except ProcessLookupError:
            pid_fd = None
        if pid_fd is not None:
            try:
                if proc_start_time(pid) != identity.get("start_time"):
                    raise SupervisorError(f"Worker identity changed; inspect {run_dir}")
                poller = select.poll()
                poller.register(pid_fd, select.POLLIN)
                poller.poll()
            finally:
                os.close(pid_fd)
        elif not (run_dir / "terminal.json").exists():
            raise SupervisorError(f"Worker disappeared without a result; inspect {run_dir}")
    if not (run_dir / "terminal.json").exists():
        raise SupervisorError(f"Worker ended without a terminal result; inspect {run_dir}")


def codex_decision(state_dir: Path, session: dict[str, Any], state: dict[str, Any],
                   start_prompt: Path) -> dict[str, Any]:
    turn = state["turn"]
    turn_dir = state_dir / "codex" / f"turn-{turn:04d}"
    turn_dir.mkdir(parents=True)
    if state["last_run"] is None:
        prompt = DECISION_INSTRUCTION + start_prompt.read_text(encoding="utf-8")
    else:
        terminal = read_json(state_dir / "runs" / state["last_run"] / "terminal.json")
        prompt = DECISION_INSTRUCTION + "Claude terminal result:\n" + json.dumps(
            terminal, ensure_ascii=False, sort_keys=True
        )
    if state.get("pending_answer") is not None:
        prompt += "\n\nUser answer to your prior question:\n" + state["pending_answer"]
    (turn_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    config = session["config"]
    command = [config["codex"]["bin"], "exec", "resume", "--json",
               "--output-schema", str(state_dir / "decision.schema.json"),
               "-o", str(turn_dir / "decision.json"), *config["codex"]["args"],
               session["codex_session_id"], "-"]
    with (turn_dir / "prompt.txt").open("rb") as input_stream, \
            (turn_dir / "events.jsonl").open("wb") as events, \
            (turn_dir / "stderr.log").open("wb") as errors:
        process = subprocess.Popen(command, cwd=config["checkout"], stdin=input_stream,
                                   stdout=events, stderr=errors, close_fds=True)
        status = process.wait()
    if status != 0:
        raise SupervisorError(f"Codex exited {status}; inspect {turn_dir}")
    completed = False
    thread_seen = False
    with (turn_dir / "events.jsonl").open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            event = json.loads(line)
            if event.get("type") == "thread.started":
                thread_seen = True
                if event.get("thread_id") != session["codex_session_id"]:
                    raise SupervisorError(f"Codex session ID changed; inspect {turn_dir}")
            elif event.get("type") == "turn.completed":
                completed = True
            elif event.get("type") in {"turn.failed", "error"}:
                raise SupervisorError(f"Codex reported an error; inspect {turn_dir}")
    if not thread_seen or not completed:
        raise SupervisorError(f"Codex has no completed turn; inspect {turn_dir}")
    decision = read_json(turn_dir / "decision.json")
    if set(decision) != {"action", "claude_prompt", "message"}:
        raise SupervisorError(f"Malformed Codex decision in {turn_dir}")
    if decision["action"] not in {"run_claude", "done", "needs_user"}:
        raise SupervisorError(f"Unknown Codex action in {turn_dir}")
    if not isinstance(decision["claude_prompt"], str) or not isinstance(decision["message"], str):
        raise SupervisorError(f"Invalid Codex decision fields in {turn_dir}")
    if decision["action"] == "run_claude" and not decision["claude_prompt"].strip():
        raise SupervisorError(f"Empty Claude prompt in {turn_dir}")
    return decision


def supervisor(config_path: Path, state_dir: Path, codex_session_id: str,
               start_prompt: Path, answer_file: Path | None) -> int:
    os.umask(0o077)
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_dir = state_dir.resolve()
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    if not isinstance(config, dict):
        raise SupervisorError("Config must be a JSON object")
    validate_config(config, state_dir)
    fingerprint = hashlib.sha256(config_bytes + b"\0" + start_prompt.read_bytes()).hexdigest()
    lock_fd = os.open(state_dir / "supervisor.lock", os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SupervisorError("Another supervisor holds this state directory") from exc
        session_path = state_dir / "session.json"
        state_path = state_dir / "state.json"
        if session_path.exists():
            session = read_json(session_path)
            if (session.get("codex_session_id") != codex_session_id or
                    session.get("fingerprint") != fingerprint):
                raise SupervisorError("Session ID or configuration changed; reconcile before reuse")
            state = read_json(state_path)
        else:
            if state_path.exists():
                raise SupervisorError("State exists without a session record")
            session = {"version": 1, "codex_session_id": codex_session_id,
                       "claude_session_id": str(uuid.uuid4()),
                       "fingerprint": fingerprint, "config": config}
            atomic_json(session_path, session)
            atomic_json(state_dir / "decision.schema.json", DECISION_SCHEMA)
            state = {"phase": "need_codex", "turn": 0, "run": None, "last_run": None,
                     "decision": None, "pending_answer": None}
            atomic_json(state_path, state)
        if answer_file is not None and state["phase"] != "needs_user":
            if state.get("pending_answer") != answer_file.read_text(encoding="utf-8").strip():
                raise SupervisorError("An answer file is valid only for the pending user question")
        while True:
            phase = state["phase"]
            if phase == "codex_inflight":
                raise SupervisorError("Codex turn was interrupted; reconcile its exact session")
            if phase == "needs_user" and answer_file is not None:
                answer = answer_file.read_text(encoding="utf-8").strip()
                if not answer:
                    raise SupervisorError("User answer file is empty")
                state["pending_answer"] = answer
                state["decision"] = None
                state["turn"] += 1
                state["phase"] = "need_codex"
                atomic_json(state_path, state)
                answer_file = None
                continue
            if phase in {"done", "needs_user"}:
                print(state["decision"]["message"])
                return 0 if phase == "done" else 2
            if phase == "need_codex":
                state["phase"] = "codex_inflight"
                atomic_json(state_path, state)
                decision = codex_decision(state_dir, session, state, start_prompt)
                state["decision"] = decision
                state["pending_answer"] = None
                state["phase"] = "decision_ready"
                atomic_json(state_path, state)
                continue
            if phase == "decision_ready":
                decision = state["decision"]
                if decision["action"] in {"done", "needs_user"}:
                    state["phase"] = decision["action"]
                    atomic_json(state_path, state)
                    continue
                run_id = f"run-{state['turn']:04d}"
                state["run"] = run_id
                state["phase"] = "claude_launching"
                atomic_json(state_path, state)
                run_dir = state_dir / "runs" / run_id
                run_dir.mkdir(parents=True)
                (run_dir / "prompt.txt").write_text(decision["claude_prompt"], encoding="utf-8")
                atomic_json(run_dir / "run.json", {"first": state["last_run"] is None})
                with (run_dir / "worker.stdout.log").open("wb") as worker_out, \
                        (run_dir / "worker.stderr.log").open("wb") as worker_err:
                    child = subprocess.Popen(
                        [sys.executable, str(Path(__file__).resolve()), "_worker",
                         str(state_dir), run_id], cwd=config["checkout"],
                        stdin=subprocess.DEVNULL, stdout=worker_out, stderr=worker_err,
                        start_new_session=True, close_fds=True,
                    )
                state["phase"] = "claude_running"
                atomic_json(state_path, state)
                wait_for_worker(run_dir, child)
            elif phase in {"claude_launching", "claude_running"}:
                run_dir = state_dir / "runs" / state["run"]
                wait_for_worker(run_dir, None)
            else:
                raise SupervisorError(f"Unknown state phase: {phase}")
            terminal = read_json(run_dir / "terminal.json")
            if terminal.get("claude_process_group_quiescent") is not True:
                raise SupervisorError(f"Claude process group is unreconciled; inspect {run_dir}")
            if (terminal.get("session_id") is not None and
                    terminal["session_id"] != session["claude_session_id"]):
                raise SupervisorError(f"Claude session ID changed; inspect {run_dir}")
            state["last_run"] = state["run"]
            state["run"] = None
            state["turn"] += 1
            state["decision"] = None
            state["phase"] = "need_codex"
            atomic_json(state_path, state)
    finally:
        os.close(lock_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    follow = subparsers.add_parser("follow", help="Run or reattach to one supervisor session")
    follow.add_argument("--config", type=Path, required=True)
    follow.add_argument("--state-dir", type=Path, required=True)
    follow.add_argument("--codex-session", required=True)
    follow.add_argument("--start-prompt", type=Path, required=True)
    follow.add_argument("--answer-file", type=Path,
                        help="Explicit user answer to a pending needs_user decision")
    internal = subparsers.add_parser("_worker", help=argparse.SUPPRESS)
    internal.add_argument("state_dir", type=Path)
    internal.add_argument("run_id")
    args = parser.parse_args()
    if args.command == "_worker":
        return worker(args.state_dir, args.run_id)
    if args.command != "follow":
        parser.print_help()
        return 2
    try:
        uuid.UUID(args.codex_session)
        return supervisor(args.config, args.state_dir, args.codex_session,
                          args.start_prompt, args.answer_file)
    except KeyboardInterrupt:
        print("follow-claude: interrupted; inspect the saved state before restarting",
              file=sys.stderr)
        return 130
    except (SupervisorError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"follow-claude: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
