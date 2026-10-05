"""Drive preparation and execution through a real local stub of the external CLI."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from skill_tests.common import Invalid, digest, read_json
from skill_tests import protocol, runner


CLIENT = r'''
import hashlib, json, os, sys
from pathlib import Path

if '--version' in sys.argv:
    print('fixture-cli 1.0')
    raise SystemExit(0)
workspace = Path.cwd()
skills = list((workspace / '.claude/skills').glob('*/SKILL.md'))
global_file = workspace / '.codex/AGENTS.md'
if 'debug' in sys.argv:
    text = global_file.read_text() + '\n' + '\n'.join('(file: ' + str(p) + ')' for p in skills)
    print(json.dumps([{'content': [{'text': text}]}]))
elif '-p' in sys.argv:
    model = sys.argv[sys.argv.index('--model') + 1]
    hook = {'hook_event_name':'InstructionsLoaded', 'file_path': str(global_file),
            'observed_file_sha256': hashlib.sha256(global_file.read_bytes()).hexdigest()}
    Path(os.environ['SKILL_TEST_HOOK_LOG']).write_text(json.dumps(hook) + '\n')
    print(json.dumps({'type':'system', 'subtype':'init', 'model':model, 'skills':[p.parent.name for p in skills]}))
    print(json.dumps({'type':'result', 'subtype':'success', 'is_error':False, 'result':'Keep progress.',
                      'modelUsage':{model:{}}, 'permission_denials':[]}))
else:
    model = sys.argv[sys.argv.index('-m') + 1]
    directory = Path(os.environ['CODEX_HOME']) / 'sessions'
    directory.mkdir()
    (directory / 'fixture.jsonl').write_text(json.dumps({'type':'turn_context','payload':{'model':model,'effort':'medium'}}) + '\n')
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Keep progress.'}}))
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':1}}))
'''


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    package = repo / ".claude/skills/example"
    package.mkdir(parents=True)
    (package / "SKILL.md").write_text("---\nname: example\ndescription: Example.\n---\n# Rule\nPreserve progress.\n")
    (repo / ".codex").mkdir()
    (repo / ".codex/AGENTS.md").write_text("# Global\nRead only.\n")
    (repo / "AGENTS.md").write_text("# Fixture repo\nRead only.\n")
    (repo / "README.md").write_text("# Fixture\n")
    corpus = tmp_path / "corpus"
    fixture = corpus / "case/scenario"
    fixture.mkdir(parents=True)
    (fixture / "input.md").write_text("# Scenario\nAssess progress.\n")
    (fixture.parent / "case.yaml").write_text(
        "id: case\nkind: application\ninitial_live: true\nprompt: Assess progress.\n"
        "criteria:\n  A1: Preserve progress.\nreceipt:\n"
        "  - path: .codex/AGENTS.md\n    heading: '# Global'\n")
    fake_home = tmp_path / "home"
    (fake_home / ".codex").mkdir(parents=True)
    (fake_home / ".claude").mkdir()
    (fake_home / ".codex/auth.json").write_text('{"synthetic":true}')
    (fake_home / ".claude/.credentials.json").write_text('{"synthetic":true}')
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    client = tmp_path / "client"
    client.write_text(f"#!{sys.executable}\n" + CLIENT)
    client.chmod(0o700)
    which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: str(client) if name in {"claude", "codex"} else which(name))
    output = tmp_path / "round"
    seal = protocol.prepare(repo, output, corpus=corpus, repeats=1, ceiling=2)
    preflight_seal = runner.preflight(output)
    return output, seal, preflight_seal


def test_real_runner_boundary_preserves_attempts_and_resumes_only_unstarted(prepared):
    output, seal, preflight_seal = prepared
    runner.execute(output, seal, preflight_seal, 1)
    original = (output / "runs/run-001/stdout.jsonl").read_bytes()
    runner.execute(output, seal, preflight_seal, 1)
    assert (output / "runs/run-001/stdout.jsonl").read_bytes() == original
    second = read_json(output / "runs/run-002/result.json")
    assert second["technical"] == "valid"
    assert second["startup_configuration_verified"] is True
    assert second["receipt"][0]["complete"] is False
    with pytest.raises(Invalid, match="exceed unstarted"):
        runner.execute(output, seal, preflight_seal, 1)
    assert len(list((output / "runs").iterdir())) == 2
    for path in (output / "prepared").glob("*/workspace"):
        assert not (path / "case.yaml").exists()
        assert not (path / "manifest.json").exists()
        assert not (path / "grades.json").exists()


def test_claude_read_rule_has_filesystem_absolute_anchor(prepared):
    output, _, _ = prepared
    settings = read_json(output / "prepared/run-001/private/claude/settings.json")
    expected = f"Read(/{Path.home()}/**)"
    assert expected.startswith("Read(//")
    assert settings["permissions"]["deny"] == [expected]
    assert f"Read({Path.home()}/**)" not in settings["permissions"]["deny"]


def test_interruption_at_launch_consumes_reservation_and_cannot_auto_retry(prepared, monkeypatch):
    output, seal, preflight_seal = prepared
    original = subprocess.Popen
    def interrupted(args, **kwargs):
        if "--version" not in args:
            raise OSError("simulated launch interruption")
        return original(args, **kwargs)
    monkeypatch.setattr(subprocess, "Popen", interrupted)
    with pytest.raises(OSError, match="simulated"):
        runner.execute(output, seal, preflight_seal)
    assert (output / "runs/run-001/reservation.json").is_file()
    monkeypatch.setattr(subprocess, "Popen", original)
    with pytest.raises(Invalid, match="Unresolved reservation"):
        runner.execute(output, seal, preflight_seal)
    assert not (output / "runs/run-002").exists()


def test_concurrent_invocation_cannot_reserve_a_second_attempt(prepared):
    import fcntl
    output, seal, preflight_seal = prepared
    with (output / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            runner.execute(output, seal, preflight_seal)
    assert list((output / "runs").iterdir()) == []


@pytest.mark.parametrize("mutation", ["source", "hidden", "launch", "model", "environment"])
def test_mutated_input_is_held_before_any_inference(prepared, mutation, monkeypatch):
    output, seal, preflight_seal = prepared
    if mutation == "source":
        (output / "sources/current/AGENTS.md").write_text("changed")
    elif mutation == "hidden":
        (output / "prepared/run-001/workspace/.oracle").write_text("answer")
    elif mutation == "launch":
        (output / "prepared/run-001/launch.json").write_text("{}")
    elif mutation == "environment":
        monkeypatch.setenv("LANG", "changed.UTF-8")
    else:
        (output / "manifest.json").write_text((output / "manifest.json").read_text().replace("medium", "high"))
    with pytest.raises(Invalid):
        runner.execute(output, seal, preflight_seal)
    assert list((output / "runs").iterdir()) == []


@pytest.mark.parametrize("file", ["reservation.json", "terminal.json", "result.json"])
def test_resume_refuses_foreign_round_evidence(prepared, file):
    from skill_tests.common import json_bytes
    output, seal, preflight_seal = prepared
    runner.execute(output, seal, preflight_seal, 1)
    path = output / "runs/run-001" / file
    data = read_json(path)
    data["manifest"] = "foreign-round"
    path.write_bytes(json_bytes(data))
    with pytest.raises(Invalid, match="identity mismatch"):
        runner.execute(output, seal, preflight_seal, 1)
    assert not (output / "runs/run-002").exists()


def test_runner_retains_attempted_actions_after_adapter_failure(prepared, monkeypatch):
    output, seal, preflight_seal = prepared
    real_events = runner.acquisition.events
    def with_attempt(path, **kwargs):
        data = real_events(path, **kwargs)
        if path.name == "stdout.jsonl":
            data.insert(1, {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "attempt", "name": "Write", "input": {"file_path": "rule.md"}}]}})
        return data
    monkeypatch.setattr(runner.acquisition, "events", with_attempt)
    with pytest.raises(Invalid, match="Technical failure"):
        runner.execute(output, seal, preflight_seal, 1)
    result = read_json(output / "runs/run-001/result.json")
    assert result["technical"] == "invalid"
    assert result["actions_complete"] is False
    assert result["actions"][0]["name"] == "Write"
    assert result["action_violation"] is True
    assert not (output / "runs/run-002").exists()
