"""Exercise current-session settings through the installed CLI entry point."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


CLI = Path(
    os.environ.get(
        "CODEX_SESSION_STATS_TEST_CLI",
        Path(__file__).resolve().parents[2] / ".local/bin/codex-session-stats",
    )
)


def record(kind, payload):
    return {"type": kind, "payload": payload}


def started(turn_id):
    return record("event_msg", {"type": "task_started", "turn_id": turn_id})


def finished(turn_id):
    return record("event_msg", {"type": "task_complete", "turn_id": turn_id})


def aborted(turn_id):
    return record("event_msg", {"type": "turn_aborted", "turn_id": turn_id})


def context(turn_id, model="gpt-6-sol", effort="xhigh"):
    return record("turn_context", {"turn_id": turn_id, "model": model, "effort": effort})


@pytest.fixture
def codex_home(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    with sqlite3.connect(home / "state_5.sqlite") as database:
        database.execute("create table threads (id text primary key, rollout_path text)")
    return home


def add_thread(home, thread_id, events, *, metadata_id=None, raw_line=None):
    rollout = home / "sessions" / f"{thread_id}.jsonl"
    rollout.parent.mkdir(exist_ok=True)
    entries = [record("session_meta", {"id": metadata_id or thread_id}), *events]
    lines = [json.dumps(entry) for entry in entries]
    if raw_line is not None:
        lines.append(raw_line)
    rollout.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with sqlite3.connect(home / "state_5.sqlite") as database:
        database.execute(
            "insert into threads (id, rollout_path) values (?, ?)",
            (thread_id, str(rollout)),
        )
    return rollout


def run_current(home, *, thread_id=None, session_id=None):
    environment = os.environ.copy()
    environment.pop("CODEX_THREAD_ID", None)
    environment.pop("CODEX_SESSION_ID", None)
    if thread_id is not None:
        environment["CODEX_THREAD_ID"] = thread_id
    if session_id is not None:
        environment["CODEX_SESSION_ID"] = session_id
    return subprocess.run(
        [sys.executable, str(CLI), "current", "--client", "codex", "--format", "json", "--codex-home", str(home)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def test_current_uses_acting_child_thread_and_does_not_modify_state(codex_home):
    parent = add_thread(codex_home, "parent", [started("parent-turn"), context("parent-turn")])
    child = add_thread(
        codex_home,
        "child",
        [started("child-turn"), context("child-turn", "gpt-6-astra", "high")],
    )
    before = {path: path.read_bytes() for path in (codex_home / "state_5.sqlite", parent, child)}

    result = run_current(codex_home, thread_id="child", session_id="parent")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "client": "codex",
        "session_id": "child",
        "agent_id": None,
        "thread_id": "child",
        "turn_id": "child-turn",
        "model": "gpt-6-astra",
        "reasoning_effort": "high",
        "reasoning_effort_status": "known",
        "source": "turn_context",
    }
    assert result.stderr == ""
    assert {path: path.read_bytes() for path in before} == before


def test_current_never_falls_back_to_parent(codex_home):
    add_thread(codex_home, "parent", [started("parent-turn"), context("parent-turn")])

    result = run_current(codex_home, thread_id="missing-child", session_id="parent")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "missing-child" in result.stderr


def test_current_uses_latest_started_turn_after_model_change(codex_home):
    add_thread(
        codex_home,
        "acting",
        [
            started("old"),
            context("old", "gpt-6-sol", "medium"),
            finished("old"),
            started("new"),
            context("new", "gpt-6-astra", "xhigh"),
        ],
    )

    result = run_current(codex_home, thread_id="acting")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "client": "codex",
        "session_id": "acting",
        "agent_id": None,
        "thread_id": "acting",
        "turn_id": "new",
        "model": "gpt-6-astra",
        "reasoning_effort": "xhigh",
        "reasoning_effort_status": "known",
        "source": "turn_context",
    }


def test_current_rejects_older_unfinished_turn_after_newer_turn_ends(codex_home):
    add_thread(
        codex_home,
        "acting",
        [
            started("abandoned"),
            context("abandoned"),
            started("latest"),
            context("latest", "gpt-6-astra", "high"),
            finished("latest"),
        ],
    )

    result = run_current(codex_home, thread_id="acting")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "latest" in result.stderr


def test_current_rejects_interrupted_latest_turn(codex_home):
    add_thread(
        codex_home,
        "acting",
        [started("turn"), context("turn"), aborted("turn")],
    )

    result = run_current(codex_home, thread_id="acting")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "no longer active" in result.stderr


def test_current_rejects_context_without_a_matching_start(codex_home):
    add_thread(
        codex_home,
        "acting",
        [started("old"), context("old"), context("new", "gpt-6-astra", "high")],
    )

    result = run_current(codex_home, thread_id="acting")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "new" in result.stderr
    assert "start" in result.stderr


@pytest.mark.parametrize(
    ("events", "metadata_id", "raw_line", "error_text"),
    [
        ([started("turn"), context("turn")], "other", None, "identity"),
        ([started("turn")], None, None, "context"),
        ([started("turn"), context("turn", model=None)], None, None, "model"),
        ([started("turn"), context("turn", effort=None)], None, None, "effort"),
        ([started("turn"), context("turn")], None, '{"type":"event_msg",', "malformed"),
    ],
)
def test_current_rejects_untrustworthy_rollout(
    codex_home, events, metadata_id, raw_line, error_text
):
    add_thread(codex_home, "acting", events, metadata_id=metadata_id, raw_line=raw_line)

    result = run_current(codex_home, thread_id="acting")

    assert result.returncode == 1
    assert result.stdout == ""
    assert error_text in result.stderr.lower()


def test_current_requires_acting_thread_identity(codex_home):
    add_thread(codex_home, "parent", [started("turn"), context("turn")])

    result = run_current(codex_home, session_id="parent")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "CODEX_THREAD_ID" in result.stderr
