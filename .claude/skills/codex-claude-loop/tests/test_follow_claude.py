"""Process-boundary tests for the host-owned Claude supervisor."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock
import importlib.util


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "follow_claude.py"

FAKE_CODEX = '''#!/usr/bin/env python3
import json
import os
import sys
import uuid
from pathlib import Path

state = Path(os.environ["FAKE_STATE_DIR"])
args = sys.argv[1:]
assert args[:3] == ["exec", "resume", "--json"]
assert args[-1] == "-"
output = Path(args[args.index("-o") + 1])
prompt = sys.stdin.read()
calls = state / "codex-calls.jsonl"
existing = calls.read_text().splitlines() if calls.exists() else []
number = len(existing)
with calls.open("a") as stream:
    stream.write(json.dumps({"turn": number, "prompt": prompt}) + "\\n")
scenario = os.environ["FAKE_SCENARIO"]
if number and not (scenario == "question" and number == 1):
    assert '"exit_code": 37' in prompt or '"exit_code": 0' in prompt
    assert ("FINAL" in prompt or scenario == "error_only") and "DIAG" in prompt
if scenario == "question" and number == 0:
    decision = {"action": "needs_user", "claude_prompt": "", "message": "Choose the fixture"}
elif number == 0 or (scenario == "continue" and number == 1) or (
        scenario == "question" and number == 1):
    if scenario == "question" and number == 1:
        assert "Use fixture A" in prompt
    decision = {"action": "run_claude", "claude_prompt": f"Implement round {number}",
                "message": ""}
else:
    decision = {"action": "done", "claude_prompt": "", "message": "verified"}
output.write_text(json.dumps(decision))
thread_id = str(uuid.uuid4()) if scenario == "wrong_codex_session" else args[-2]
print(json.dumps({"type": "thread.started", "thread_id": thread_id}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1,
                                                   "output_tokens": 1}}))
'''

FAKE_CLAUDE = '''#!/usr/bin/env python3
import json
import os
import sys
import time
import subprocess
from pathlib import Path

state = Path(os.environ["FAKE_STATE_DIR"])
args = sys.argv[1:]
calls = state / "claude-calls.jsonl"
existing = calls.read_text().splitlines() if calls.exists() else []
number = len(existing)
flag = "--session-id" if number == 0 else "--resume"
assert flag in args
session_id = args[args.index(flag) + 1]
with calls.open("a") as stream:
    stream.write(json.dumps({"round": number, "session_id": session_id,
                             "flag": flag, "prompt": sys.stdin.read()}) + "\\n")
(state / f"ready-{number}").touch()
while not (state / f"release-{number}").exists():
    time.sleep(0.05)
if os.environ["FAKE_SCENARIO"] == "descendant":
    subprocess.Popen([sys.executable, str(state / "fake-child.py")],
                     stdin=subprocess.DEVNULL, close_fds=True)
init = {"type": "system", "subtype": "init", "session_id": session_id}
if os.environ["FAKE_SCENARIO"] == "mcp_failure":
    init["mcp_servers"] = [{"name": "fixture", "status": "failed"}]
print(json.dumps(init))
if os.environ["FAKE_SCENARIO"] == "permission_denied":
    print(json.dumps({"type": "permission_denied", "message": "Bash was denied"}))
observed_session = "wrong-session" if os.environ["FAKE_SCENARIO"] == "wrong_claude_session" else session_id
if os.environ["FAKE_SCENARIO"] == "error_only":
    print(json.dumps({"type": "result", "session_id": observed_session,
                      "result": None, "is_error": True,
                      "subtype": "error_during_execution", "errors": ["provider failure"],
                      "terminal_reason": "classifier"}))
else:
    print(json.dumps({"type": "result", "session_id": observed_session,
                  "result": f"FINAL {number}", "is_error": False,
                  "permission_denials": (["Bash"] if os.environ["FAKE_SCENARIO"] == "permission_denied" else []),
                  "modelUsage": {"fake-opus": {}}}))
print(f"ERROR DIAG {number}", file=sys.stderr)
if os.environ["FAKE_SCENARIO"] == "stderr_early":
    print("ordinary output " * 700, file=sys.stderr)
sys.exit(37 if number == 0 and os.environ["FAKE_SCENARIO"] != "mcp_failure" else 0)
'''

FAKE_CHILD = '''#!/usr/bin/env python3
import os
import time
from pathlib import Path
state = Path(os.environ["FAKE_STATE_DIR"])
(state / "child-ready").touch()
while not (state / "release-child").exists():
    time.sleep(0.05)
'''


class FollowClaudeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="follow-claude-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        self.state = self.root / "state"
        self.state.mkdir()
        self.codex = self.root / "fake-codex"
        self.claude = self.root / "fake-claude"
        for path, source in ((self.codex, FAKE_CODEX), (self.claude, FAKE_CLAUDE)):
            path.write_text(source)
            path.chmod(0o700)
        (self.state / "fake-child.py").write_text(FAKE_CHILD)
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({
            "checkout": str(self.checkout),
            "codex": {"bin": str(self.codex), "args": ["--skip-git-repo-check"]},
            "claude": {"bin": str(self.claude), "args": [
                "--model", "fake-opus", "--permission-mode", "bypassPermissions"
            ]},
        }))
        self.start_prompt = self.root / "start.txt"
        self.start_prompt.write_text("Complete the fixture task.")
        self.session_id = str(uuid.uuid4())
        self.processes: list[subprocess.Popen[str]] = []
        self.addCleanup(self.release_and_reap)

    def release_and_reap(self) -> None:
        for number in range(3):
            (self.state / f"release-{number}").touch()
        (self.state / "release-child").touch()
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            process.communicate()

    def launch(self, scenario: str, answer_file: Path | None = None) -> subprocess.Popen[str]:
        environment = os.environ.copy()
        environment.update(FAKE_STATE_DIR=str(self.state), FAKE_SCENARIO=scenario)
        command = [
            sys.executable, str(SCRIPT), "follow", "--config", str(self.config),
            "--state-dir", str(self.state), "--codex-session", self.session_id,
            "--start-prompt", str(self.start_prompt),
        ]
        if answer_file is not None:
            command.extend(("--answer-file", str(answer_file)))
        process = subprocess.Popen(command, cwd=self.checkout, env=environment, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        self.processes.append(process)
        return process

    def await_condition(self, condition, description: str) -> None:
        deadline = time.monotonic() + 10
        while not condition():
            process = self.processes[-1]
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.fail(f"Supervisor exited before {description}: "
                          f"{process.returncode}, {stdout!r}, {stderr!r}")
            if time.monotonic() > deadline:
                self.fail(f"Timed out waiting for {description}")
            time.sleep(0.02)

    def calls(self, name: str) -> list[dict]:
        path = self.state / f"{name}-calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def test_quiet_wait_keeps_codex_idle_and_delivers_exit_and_diagnostic(self) -> None:
        process = self.launch("basic")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        self.await_condition(
            lambda: json.loads((self.state / "state.json").read_text())["phase"] == "claude_running",
            "running state publication",
        )
        state = json.loads((self.state / "state.json").read_text())
        self.assertEqual(state["phase"], "claude_running")
        self.assertEqual(len(self.calls("codex")), 1)
        self.assertFalse((self.state / "codex" / "turn-0001").exists())
        (self.state / "release-0").touch()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual((process.returncode, stdout, stderr), (0, "verified\n", ""))
        terminal = json.loads((self.state / "runs" / "run-0000" / "terminal.json").read_text())
        self.assertEqual(terminal["exit_code"], 37)
        self.assertEqual(terminal["final_answer"], "FINAL 0")
        self.assertEqual(terminal["stderr_diagnostics"], ["ERROR DIAG 0"])
        self.assertEqual(len(self.calls("codex")), 2)
        self.assertEqual(len(self.calls("claude")), 1)

    def test_restart_reattaches_to_same_worker_without_second_implementation(self) -> None:
        first = self.launch("basic")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        self.assertEqual(len(self.calls("codex")), 1)
        first.terminate()
        first.wait(timeout=10)
        first.communicate()
        identity = json.loads((self.state / "runs" / "run-0000" / "worker.json").read_text())
        self.assertTrue(Path(f"/proc/{identity['pid']}/stat").exists())
        second = self.launch("basic")
        self.assertEqual(len(self.calls("codex")), 1)
        (self.state / "release-0").touch()
        stdout, stderr = second.communicate(timeout=10)
        self.assertEqual((second.returncode, stdout, stderr), (0, "verified\n", ""))
        self.assertEqual(len(self.calls("codex")), 2)
        self.assertEqual(len(self.calls("claude")), 1)

    def test_codex_can_request_another_round_after_first_result(self) -> None:
        process = self.launch("continue")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "first Claude run")
        (self.state / "release-0").touch()
        self.await_condition(lambda: (self.state / "ready-1").exists(), "second Claude run")
        self.assertEqual(len(self.calls("codex")), 2)
        (self.state / "release-1").touch()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual((process.returncode, stdout, stderr), (0, "verified\n", ""))
        self.assertEqual(len(self.calls("codex")), 3)
        claude_calls = self.calls("claude")
        self.assertEqual([call["flag"] for call in claude_calls], ["--session-id", "--resume"])
        self.assertEqual(claude_calls[0]["session_id"], claude_calls[1]["session_id"])

    def test_concurrent_supervisor_cannot_start_second_worker(self) -> None:
        first = self.launch("basic")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        second = self.launch("basic")
        stdout, stderr = second.communicate(timeout=10)
        self.assertEqual(second.returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Another supervisor holds this state directory", stderr)
        self.assertEqual(len(self.calls("codex")), 1)
        self.assertEqual(len(self.calls("claude")), 1)
        (self.state / "release-0").touch()
        self.assertEqual(first.communicate(timeout=10), ("verified\n", ""))

    def test_dead_worker_does_not_trigger_a_codex_resume_or_relaunch(self) -> None:
        first = self.launch("basic")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        worker = json.loads((self.state / "runs" / "run-0000" / "worker.json").read_text())
        os.kill(worker["pid"], signal.SIGTERM)
        (self.state / "release-0").touch()
        stdout, stderr = first.communicate(timeout=10)
        self.assertEqual(first.returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Worker exited", stderr)
        second = self.launch("basic")
        stdout, stderr = second.communicate(timeout=10)
        self.assertEqual(second.returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Worker disappeared without a result", stderr)
        self.assertEqual(len(self.calls("codex")), 1)
        self.assertEqual(len(self.calls("claude")), 1)

    def test_user_question_waits_for_explicit_answer_before_launch(self) -> None:
        first = self.launch("question")
        stdout, stderr = first.communicate(timeout=10)
        self.assertEqual((first.returncode, stdout, stderr), (2, "Choose the fixture\n", ""))
        self.assertEqual(len(self.calls("codex")), 1)
        self.assertFalse((self.state / "claude-calls.jsonl").exists())
        answer = self.root / "answer.txt"
        answer.write_text("Use fixture A")
        second = self.launch("question", answer)
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude after answer")
        (self.state / "release-0").touch()
        stdout, stderr = second.communicate(timeout=10)
        self.assertEqual((second.returncode, stdout, stderr), (0, "verified\n", ""))
        self.assertEqual(len(self.calls("codex")), 3)
        self.assertEqual(len(self.calls("claude")), 1)

    def test_changed_codex_session_blocks_claude_launch(self) -> None:
        process = self.launch("wrong_codex_session")
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Codex session ID changed", stderr)
        self.assertFalse((self.state / "claude-calls.jsonl").exists())

    def test_changed_claude_session_blocks_next_codex_turn(self) -> None:
        process = self.launch("wrong_claude_session")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        (self.state / "release-0").touch()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Claude session ID changed", stderr)
        self.assertEqual(len(self.calls("codex")), 1)

    def test_startup_failure_is_reported_even_with_zero_claude_exit(self) -> None:
        process = self.launch("mcp_failure")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        (self.state / "release-0").touch()
        process.communicate(timeout=10)
        terminal = json.loads((self.state / "runs" / "run-0000" / "terminal.json").read_text())
        self.assertEqual(terminal["startup_and_event_alerts"], ["MCP startup: fixture: failed"])
        self.assertIn("MCP startup: fixture: failed", self.calls("codex")[1]["prompt"])

    def test_permission_denial_is_distinct_in_compact_result(self) -> None:
        process = self.launch("permission_denied")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        (self.state / "release-0").touch()
        process.communicate(timeout=10)
        terminal = json.loads((self.state / "runs" / "run-0000" / "terminal.json").read_text())
        self.assertEqual(terminal["permission_denials"], ["Bash"])
        self.assertEqual(terminal["startup_and_event_alerts"], ["Permission denied: Bash was denied"])

    def test_surviving_descendant_holds_next_codex_turn(self) -> None:
        process = self.launch("descendant")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        (self.state / "release-0").touch()
        self.await_condition(lambda: (self.state / "child-ready").exists(), "descendant readiness")
        root = json.loads((self.state / "runs" / "run-0000" / "claude_process.json").read_text())
        self.await_condition(lambda: not Path(f"/proc/{root['pid']}").exists(),
                             "Claude root exit")
        self.await_condition(
            lambda: (self.state / "runs" / "run-0000" / "group_waiting.json").exists(),
            "verified descendant wait",
        )
        self.assertIsNone(process.poll())
        self.assertEqual(len(self.calls("codex")), 1)
        self.assertFalse((self.state / "codex" / "turn-0001").exists())
        (self.state / "release-child").touch()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual((process.returncode, stdout, stderr), (0, "verified\n", ""))
        self.assertEqual(len(self.calls("codex")), 2)

    def test_error_only_result_preserves_cause(self) -> None:
        process = self.launch("error_only")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        (self.state / "release-0").touch()
        process.communicate(timeout=10)
        terminal = json.loads((self.state / "runs" / "run-0000" / "terminal.json").read_text())
        self.assertEqual(terminal["result_subtype"], "error_during_execution")
        self.assertEqual(terminal["result_errors"], ["provider failure"])
        self.assertEqual(terminal["termination_reason"], "classifier")
        self.assertIn("provider failure", self.calls("codex")[1]["prompt"])

    def test_early_stderr_diagnostic_survives_later_noise(self) -> None:
        process = self.launch("stderr_early")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        (self.state / "release-0").touch()
        process.communicate(timeout=10)
        terminal = json.loads((self.state / "runs" / "run-0000" / "terminal.json").read_text())
        self.assertEqual(terminal["stderr_diagnostics"], ["ERROR DIAG 0"])
        self.assertNotIn("ordinary output", self.calls("codex")[1]["prompt"])

    def test_changed_worker_identity_blocks_reattach(self) -> None:
        first = self.launch("basic")
        self.await_condition(lambda: (self.state / "ready-0").exists(), "Claude readiness")
        first.terminate()
        first.communicate(timeout=10)
        identity_path = self.state / "runs" / "run-0000" / "worker.json"
        identity = json.loads(identity_path.read_text())
        identity["start_time"] = "wrong-start-time"
        identity_path.write_text(json.dumps(identity))
        second = self.launch("basic")
        stdout, stderr = second.communicate(timeout=10)
        self.assertEqual(second.returncode, 1)
        self.assertIn("Worker identity changed", stderr)
        self.assertEqual(len(self.calls("codex")), 1)
        (self.state / "release-0").touch()
        deadline = time.monotonic() + 10
        while not (self.state / "runs" / "run-0000" / "terminal.json").exists():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.02)

    def test_empty_group_scan_with_existing_group_is_not_quiescent(self) -> None:
        specification = importlib.util.spec_from_file_location("follow_claude", SCRIPT)
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        with mock.patch.object(module, "live_process_group_members", return_value=[]):
            with mock.patch.object(module.os, "killpg", return_value=None):
                with self.assertRaisesRegex(module.SupervisorError, "still present"):
                    module.wait_for_process_group(12345, self.state)

    def test_post_launch_supervision_error_never_writes_terminal(self) -> None:
        specification = importlib.util.spec_from_file_location("follow_claude", SCRIPT)
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        run_dir = self.state / "runs" / "run-0000"
        run_dir.mkdir(parents=True)
        (run_dir / "prompt.txt").write_text("Fixture prompt")
        (run_dir / "run.json").write_text(json.dumps({"first": True}))
        (self.state / "session.json").write_text(json.dumps({
            "config": json.loads(self.config.read_text()),
            "claude_session_id": str(uuid.uuid4()),
        }))
        environment = os.environ.copy()
        environment.update(FAKE_STATE_DIR=str(self.state), FAKE_SCENARIO="basic")
        with mock.patch.dict(os.environ, environment):
            with mock.patch.object(module, "wait_for_process_group",
                                   side_effect=OSError("process inspection failed")):
                (self.state / "release-0").touch()
                with self.assertRaisesRegex(OSError, "process inspection failed"):
                    module.worker(self.state, "run-0000")
        self.assertFalse((run_dir / "terminal.json").exists())


if __name__ == "__main__":
    unittest.main()
