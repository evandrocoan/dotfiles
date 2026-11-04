from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

import pytest

from skill_tests.common import Invalid, digest, json_bytes, read_json, write_new
from skill_tests.protocol import CORPUS, PROFILES, cases, prepare, schedule, select_span
from skill_tests.runner import child_environment, process_identity, reconcile, remaining_processes


def test_all_cases_valid_and_live_budget_exact():
    corpus = cases()
    assert set(corpus) == {
        "architecture", "authorization", "references", "held-out", "natural-trigger", "near-miss",
        "llm-replay-quality", "agentic-causal-diagnosis", "agentic-native-layer",
        "llm-outcome-trigger", "llm-outcome-near-miss", "llm-outcome-held-out",
        "followup-native-trigger", "followup-scheduled-worker", "followup-uncertain-return",
        "followup-limits", "followup-near-miss", "followup-database-near-miss",
        "followup-unchanged-check", "followup-stale-reference",
        "followup-monitor-model", "followup-simple-wait",
        "followup-worker-reuse", "followup-independent-workers",
        "followup-worker-lifetime", "followup-command-contract", "followup-evidence-only",
        "followup-executor-model",
        "followup-parent-takeover", "followup-task-continuation", "followup-quiet-batch",
        "followup-parent-wait",
        "followup-pipeline-notifications",
    }
    selected = [key for key, case in corpus.items() if case["initial_live"]]
    assert selected == ["architecture", "authorization", "references"]
    cells = schedule(selected, PROFILES, ["current"], 2)
    assert len(cells) == 12
    assert len({c["id"] for c in cells}) == 12
    for name in selected:
        for model in ["sonnet", "luna"]:
            assert {c["repeat"] for c in cells if c["case"] == name and c["profile"] == model} == {1, 2}
    assert [c["profile"] for c in cells[:4]] == ["sonnet", "luna", "luna", "sonnet"]


def test_case_receipts_resolve_in_authoritative_sources():
    repo = Path(__file__).resolve().parents[3]
    for key, case in cases().items():
        for selector in case["receipt"]:
            name = selector["path"]
            source = (CORPUS / key / name) if name.startswith("scenario/") else repo / name
            span = select_span(source.read_text(), selector["heading"])
            assert span["lines"][0] == selector["heading"]


def test_comparison_arms_are_counterbalanced():
    cells = schedule(["a"], PROFILES, ["baseline", "candidate"], 2)
    assert [(c["profile"], c["arm"]) for c in cells[:4]] == [
        ("sonnet", "baseline"), ("sonnet", "candidate"),
        ("luna", "candidate"), ("luna", "baseline")]


def test_span_requires_unique_real_heading():
    text = "# Intro\n## Owner\nrule\n### Detail\nextra\n## Next\nother"
    assert select_span(text, "## Owner") == {"first_line": 2, "lines": ["## Owner", "rule", "### Detail", "extra"]}
    with pytest.raises(Invalid, match="unique"):
        select_span(text + "\n## Owner", "## Owner")


def test_empty_corpus_does_not_look_valid(tmp_path):
    with pytest.raises(Invalid, match="Empty corpus"):
        cases(tmp_path)


@pytest.mark.parametrize("case_id", [
    "followup-monitor-model", "followup-simple-wait",
    "followup-unchanged-check", "followup-stale-reference",
    "followup-worker-reuse", "followup-independent-workers",
    "followup-worker-lifetime", "followup-command-contract", "followup-evidence-only",
    "followup-executor-model",
    "followup-parent-takeover", "followup-task-continuation", "followup-quiet-batch",
    "followup-database-near-miss",
    "followup-parent-wait",
    "followup-pipeline-notifications",
])
def test_native_case_rejected_before_cli_discovery_or_output(tmp_path, monkeypatch, case_id):
    def unexpected_client_lookup(name):
        pytest.fail(f"Native case reached CLI lookup: {name}")
    monkeypatch.setattr("skill_tests.protocol.shutil.which", unexpected_client_lookup)
    output = tmp_path / "round"
    with pytest.raises(Invalid, match=f"require native tools.*{case_id}"):
        prepare(tmp_path, output, case_ids=[case_id], profile_keys=["luna"])
    assert not output.exists()


@pytest.mark.parametrize("execution", ["unsupported", "[native]"])
def test_invalid_execution_route_is_rejected(tmp_path, execution):
    fixture = tmp_path / "case/scenario"
    fixture.mkdir(parents=True)
    (fixture / "input.txt").write_text("Disposable scenario.\n")
    (fixture.parent / "case.yaml").write_text(
        "id: case\nkind: application\ninitial_live: false\n"
        f"execution: {execution}\nprompt: Observe once.\n"
        "criteria:\n  A1: Report the observation.\nreceipt: []\n")
    with pytest.raises(Invalid, match="Invalid case execution route"):
        cases(tmp_path)


def test_quiet_batch_fixture_requires_all_phases_in_order(tmp_path):
    script = tmp_path / 'operation.py'
    shutil.copyfile(CORPUS / 'followup-quiet-batch/scenario/operation.py', script)
    for action, state in [('prepare', 'PREPARED'), ('check', 'CHECKED'), ('finish', 'COMPLETE')]:
        result = subprocess.run([sys.executable, str(script), action, '--delay', '0'],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        value = json.loads(result.stdout.splitlines()[-1])
        assert (value['task'], value['action'], value['state'], value['exit_code']) == (
            'task-901', action, state, 0)
    events = [json.loads(line) for line in (tmp_path / 'events.jsonl').read_text().splitlines()]
    assert [row['action'] for row in events] == ['prepare', 'check', 'finish']


@pytest.mark.parametrize('prefix,action', [([], 'finish'), (['prepare'], 'prepare'),
                                         (['prepare'], 'finish')])
def test_quiet_batch_fixture_rejects_skips_and_repeats(tmp_path, prefix, action):
    script = tmp_path / 'operation.py'
    shutil.copyfile(CORPUS / 'followup-quiet-batch/scenario/operation.py', script)
    for previous in prefix:
        subprocess.run([sys.executable, str(script), previous, '--delay', '0'],
                       capture_output=True, text=True, check=True)
    events = tmp_path / 'events.jsonl'
    before = events.read_bytes() if events.exists() else None
    result = subprocess.run([sys.executable, str(script), action, '--delay', '0'],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert json.loads(result.stdout.splitlines()[-1])['state'] == 'OUT_OF_ORDER'
    assert (events.read_bytes() if events.exists() else None) == before


@pytest.mark.parametrize("both_operations", [True, False])
def test_independent_worker_fixture_requires_both_operations(tmp_path, both_operations):
    source = CORPUS / "followup-independent-workers/scenario/operation.py"
    script = tmp_path / "operation.py"
    shutil.copyfile(source, script)
    broker_timeout = "10" if both_operations else "1"
    broker = subprocess.Popen(
        [sys.executable, str(script), "--serve", "--timeout", broker_timeout],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    clients = []
    try:
        assert broker.stdout.readline().strip() == "BROKER_READY"
        names = ["op-a", "op-b"] if both_operations else ["op-a"]
        for name in names:
            clients.append(subprocess.Popen(
                [sys.executable, str(script), name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            ))
        for name, client in zip(names, clients):
            output, error = client.communicate(timeout=10)
            result = json.loads(output.splitlines()[-1])
            assert error == ""
            assert result["operation"] == name
            assert result["state"] == ("SUCCEEDED" if both_operations else "FAILED")
            assert result["exit_code"] == client.returncode == (0 if both_operations else 7)
        _, error = broker.communicate(timeout=10)
        assert error == ""
        assert broker.returncode == (0 if both_operations else 7)
        events = [json.loads(line) for line in (tmp_path / "broker-events.jsonl").read_text().splitlines()]
        assert sorted(event["operation"] for event in events if event["event"] == "connected") == names
        if both_operations:
            assert events[-1] == {"event": "released", "operations": ["op-a", "op-b"]}
        else:
            assert events[-1]["event"] == "failed"
            assert not any(event["event"] == "released" for event in events)
        assert not (tmp_path / "gate.sock").exists()
    finally:
        for process in [*clients, broker]:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=10)


@pytest.mark.parametrize("arrangement", ["valid", "missing_target", "missing_producer", "wrong_cwd"])
def test_execution_fixture_requires_prescribed_directory_and_both_schemas(tmp_path, arrangement):
    scenario = tmp_path / "scenario"
    shutil.copytree(CORPUS / "followup-command-contract/scenario", scenario)
    contract = read_json(scenario / "ci.json")
    cwd = tmp_path / contract["working_directory"]
    environment = dict(os.environ, **contract["environment"])
    if arrangement == "missing_target":
        environment.pop("TARGET_SCHEMA_PATH")
    elif arrangement == "missing_producer":
        environment.pop("PRODUCER_SCHEMA_PATH")
    actual_cwd = tmp_path if arrangement == "wrong_cwd" else cwd
    result = subprocess.run(
        [sys.executable, str(cwd / "suite.py"), "--delay", "0"],
        cwd=actual_cwd, env=environment, capture_output=True, text=True, timeout=10,
    )
    events = [json.loads(line) for line in (cwd / "run-events.jsonl").read_text().splitlines()]
    if arrangement == "valid":
        assert result.returncode == 0
        assert result.stderr == ""
        assert [event["event"] for event in events] == ["started", "terminal"]
        assert events[0]["cwd"] == str(cwd)
        assert events[0]["environment"] == contract["environment"]
        assert events[-1] == {"event": "terminal", "exit_code": 0, "tests": 1}
        assert "TERMINAL invocation-contract exit=0" in result.stdout
    else:
        assert result.returncode == 2
        assert "Prescribed working directory and both schema variables" in result.stderr
        assert len(events) == 1
        assert events[0]["event"] == "preflight_failed"
        assert events[0]["tests"] == 0
        assert events[0]["exit_code"] == 2
        assert "TERMINAL invocation-contract exit=0" not in result.stdout


@pytest.mark.parametrize("mode", ["workspace-write", "unsupported"])
def test_engineering_preview_fixture_preserves_source_and_rejects_unsupported_mode(tmp_path, mode):
    scenario = tmp_path / "scenario"
    shutil.copytree(CORPUS / "followup-executor-model/scenario", scenario)
    source = scenario / "source.json"
    source.write_text(json.dumps({"mode": mode, "network_enabled": True}) + "\n")
    original = source.read_bytes()
    result = subprocess.run(
        [sys.executable, str(scenario / "prepare.py"), "--delay", "0"],
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
    )
    assert source.read_bytes() == original
    events = [json.loads(line) for line in (scenario / "events.jsonl").read_text().splitlines()]
    if mode == "workspace-write":
        assert result.returncode == 0
        assert result.stderr == ""
        assert read_json(scenario / "preview.json") == {
            "permission_profile": "local-workspace", "network_enabled": True,
        }
        assert events == [
            {"state": "PREPARING", "source_sha256": digest(original)},
            {"state": "PREVIEW_READY", "exit_code": 0,
             "preview_sha256": digest((scenario / "preview.json").read_bytes())},
        ]
        assert "PREVIEW_READY exit=0; not applied" in result.stdout
    else:
        assert result.returncode == 2
        assert events == [{"state": "REFUSED", "exit_code": 2}]
        assert not (scenario / "preview.json").exists()
        assert "PREVIEW_READY" not in result.stdout


@pytest.mark.parametrize(("route", "actions", "codes", "states"), [
    ("assess_with_selected_executor", ["assess", "execute"], [0, 0],
     ["INSUFFICIENT_FOR_ENGINEERING", "COMPLETE"]),
    ("assess_with_selected_executor", ["execute"], [2], ["ASSESSMENT_REQUIRED"]),
    ("parent_retained", ["execute"], [0], ["COMPLETE"]),
])
def test_parent_takeover_fixture_requires_known_or_recorded_assessment(
        tmp_path, route, actions, codes, states):
    scenario = tmp_path / "scenario"
    shutil.copytree(CORPUS / "followup-parent-takeover/scenario", scenario)
    assignment = scenario / "assignment.json"
    value = read_json(assignment)
    value["route"] = route
    assignment.write_text(json.dumps(value) + "\n")
    original = assignment.read_bytes()
    results = [subprocess.run(
        [sys.executable, str(scenario / "task.py"), action, "--delay", "0"],
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
    ) for action in actions]
    assert [result.returncode for result in results] == codes
    assert all(result.stderr == "" for result in results)
    events = [json.loads(line) for line in (scenario / "events.jsonl").read_text().splitlines()]
    assert events == [dict(task="task-117", action=action, state=state, exit_code=code)
                      for action, state, code in zip(actions, states, codes)]
    assert assignment.read_bytes() == original


@pytest.mark.parametrize(("actions", "codes", "states"), [
    (["inspect", "finalize"], [0, 0], ["NEEDS_FINALIZE", "COMPLETE"]),
    (["finalize"], [2], ["OUT_OF_ORDER"]),
])
def test_continuation_fixture_requires_inspection_before_completion(tmp_path, actions, codes, states):
    scenario = tmp_path / "scenario"
    shutil.copytree(CORPUS / "followup-task-continuation/scenario", scenario)
    results = [subprocess.run(
        [sys.executable, str(scenario / "operation.py"), action, "--delay", "0"],
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
    ) for action in actions]
    assert [result.returncode for result in results] == codes
    assert all(result.stderr == "" for result in results)
    events = [json.loads(line) for line in (scenario / "events.jsonl").read_text().splitlines()]
    assert events == [dict(task="task-128", action=action, state=state, exit_code=code)
                      for action, state, code in zip(actions, states, codes)]


def test_child_environment_does_not_inherit_credentials_or_runtime_overrides():
    env, omitted = child_environment({"PATH": "/usr/bin", "HOME": "/real-home", "API_KEY": "private",
                                      "GITLAB_TOKEN": "private", "CODEX_HOME": "/old", "PYTHONPATH": "/injection"})
    assert env == {"PATH": "/usr/bin", "HOME": "/real-home", "DISABLE_AUTOUPDATER": "1",
                   "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    assert omitted == ["API_KEY", "GITLAB_TOKEN"]


@pytest.mark.parametrize(("mode", "observations", "observed_status", "pipeline_exit", "job_exit"), [
    ("success", 5, "success", 0, 0),
    ("required_failure", 4, "running", None, 7),
])
def test_pipeline_status_feed_preserves_execution_and_distinguishes_client_exit(
        tmp_path, mode, observations, observed_status, pipeline_exit, job_exit):
    scenario = tmp_path / "scenario"
    shutil.copytree(CORPUS / "followup-pipeline-notifications/scenario", scenario)
    task = read_json(scenario / "task.json")
    task["mode"] = mode
    (scenario / "task.json").write_text(json.dumps(task) + "\n")
    original = {p.name: p.read_bytes() for p in scenario.iterdir() if p.is_file()}
    broker = subprocess.Popen(
        [sys.executable, str(scenario / "producer.py"), "--interval", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert broker.stdout.readline().strip() == "BROKER_READY"
        results = []
        for sequence in range(observations):
            result = subprocess.run(
                [sys.executable, str(scenario / "status.py"), "--after", str(sequence - 1)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            assert result.stderr == ""
            value = json.loads(result.stdout)
            assert value["sequence"] == sequence
            results.append(value)
            if sequence == 0:
                # The real producer reaches terminal without more client requests.
                assert broker.stdout.readline().strip() == "PRODUCER_TERMINAL"
        assert results[-1]["status"] == observed_status
        assert results[-1]["pipeline_exit_code"] == pipeline_exit
        assert results[-1]["jobs"][-1]["exit_code"] == job_exit
        events = [json.loads(line) for line in (scenario / "events.jsonl").read_text().splitlines()]
        produced = [row["snapshot"] for row in events if row["kind"] == "produced"]
        observed = [row["sequence"] for row in events if row["kind"] == "observed"]
        assert [row["sequence"] for row in produced] == [0, 1, 2, 3, 4]
        assert observed == list(range(observations))
        assert produced[-1]["pipeline_exit_code"] == job_exit
        assert {name: (scenario / name).read_bytes() for name in original} == original
    finally:
        if broker.poll() is None:
            broker.terminate()
        _, stderr = broker.communicate(timeout=10)
        assert stderr == ""
        assert not (scenario / "feed.sock").exists()


def test_unresolved_reservation_cannot_be_reused_or_omitted(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    manifest = {"ceiling": 1, "schedule": [{"id": "run-001"}]}
    write_new(tmp_path / "manifest.json", manifest)
    assert reconcile(tmp_path, manifest) == set()
    attempt = runs / "run-001"
    attempt.mkdir()
    write_new(attempt / "reservation.json", {"cell": {"id": "run-001"}, "manifest": digest(json_bytes(manifest))})
    with pytest.raises(Invalid, match="Unresolved reservation"):
        reconcile(tmp_path, manifest)
    write_new(attempt / "terminal.json", {"exit": 0})
    with pytest.raises(Invalid, match="Unresolved reservation"):
        reconcile(tmp_path, manifest)


def test_live_process_is_not_terminal_even_with_terminal_artifact(tmp_path):
    import os
    identity = process_identity(os.getpid())
    assert os.getpid() in remaining_processes(identity)
    # A boot mismatch must not identify unrelated processes as the old run.
    assert remaining_processes(dict(identity, boot_id="different-boot")) == []
    # The same PID with another start identity and unrelated session/group is a reused PID.
    assert remaining_processes(dict(identity, start_ticks=-1, session=-1, pgid=-1)) == []
