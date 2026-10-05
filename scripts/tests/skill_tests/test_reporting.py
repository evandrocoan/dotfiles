from copy import deepcopy
import importlib.metadata
from pathlib import Path

import pytest

from skill_tests.common import Invalid, digest, json_bytes, read_json, write_new
from skill_tests.protocol import code_fingerprint
from skill_tests.reporting import export, grade, report, sensitive


@pytest.fixture
def round_data(tmp_path):
    (tmp_path / "runs").mkdir()
    cells = [{"id": "run-001", "case": "case", "profile": "model", "arm": "current", "repeat": 1},
             {"id": "run-002", "case": "case", "profile": "model", "arm": "current", "repeat": 2}]
    manifest = {"schema": 1, "code": code_fingerprint(), "dependencies": {}, "arms": {},
                "profiles": [{"key": "model", "model": "test-model", "effort": "medium"}], "cases": {}, "schedule": cells, "corpus": {"case": {"kind": "application", "selected": True}}, "ceiling": 2}
    (tmp_path / "fixtures/case").mkdir(parents=True)
    manifest["cases"]["case"] = {"fixtures": {}, "criteria": {"A1": "Preserve progress."}, "spans": {"current": []}}
    write_new(tmp_path / "manifest.json", manifest)
    write_new(tmp_path / "manifest.sha256", (digest(json_bytes(manifest)) + "\n").encode())
    for cell in cells:
        target = tmp_path / "runs" / cell["id"]
        target.mkdir()
        write_new(target / "reservation.json", {"cell": cell, "manifest": digest(json_bytes(manifest))})
        write_new(target / "terminal.json", {"cell": cell, "manifest": digest(json_bytes(manifest)), "exit": 0})
        write_new(target / "process.json", {"pid": -1, "start_ticks": -1, "pgid": -1, "session": -1, "boot_id": "fixture"})
        write_new(target / "result.json", {"cell": cell, "manifest": digest(json_bytes(manifest)), "technical": "valid", "answer": "Keep progress.",
                                          "model": "test-model", "effort_requested": "medium", "effort_evidence": "fixture",
                                          "receipt": [], "permission_denials": [], "discovery": {}, "actions_complete": True,
                                          "action_violation": False, "private_reasoning": "MUST NOT EXPORT",
                                          "usage": {"input_tokens": 20, "private_reasoning": "MUST NOT EXPORT"},
                                          "actions": [{"id": "read", "name": "Read", "violation": False, "assessed": True, "evidence": "stdout:2", "private_reasoning": "MUST NOT EXPORT"}]})
    return tmp_path


def good_grade():
    return {"A1": {"verdict": "pass", "quote": "Keep progress.", "answer_offset": 0, "action_refs": [], "reason": "Explicitly preserves the invariant."}}


def test_missing_grade_is_not_all_pass_and_all_cells_remain(round_data):
    assert report(round_data)["status"] == "incomplete"
    grade(round_data, "run-001", good_grade())
    assert report(round_data)["status"] == "incomplete"
    grade(round_data, "run-002", good_grade())
    value = report(round_data)
    assert value["status"] == "behavior-passed"
    assert value["scheduled"] == value["started"] == 2
    assert "MUST NOT EXPORT" not in json_bytes(value).decode()


@pytest.mark.parametrize("change", ["missing", "quote", "verdict"])
def test_grade_rejects_incomplete_or_unsupported_evidence(round_data, change):
    value = good_grade()
    if change == "missing": value.clear()
    elif change == "quote": value["A1"]["quote"] = "Fabricated evidence"
    else: value["A1"]["verdict"] = "probably"
    with pytest.raises(Invalid):
        grade(round_data, "run-001", value)


def test_grade_is_not_overwritten_and_failures_are_preserved(round_data):
    value = good_grade()
    value["A1"]["verdict"] = "fail"
    grade(round_data, "run-001", value)
    with pytest.raises(FileExistsError):
        grade(round_data, "run-001", good_grade())
    grade(round_data, "run-002", good_grade())
    assert report(round_data)["status"] == "behavior-failed"


def test_tampered_answer_invalidates_grade(round_data):
    grade(round_data, "run-001", good_grade())
    target = round_data / "runs/run-001/result.json"
    value = read_json(target)
    value["answer"] = "Changed after grading."
    target.write_bytes(json_bytes(value))
    with pytest.raises(Invalid, match="Grade evidence changed"):
        report(round_data)


def test_export_requires_exact_review_and_blocks_sensitive_answer(round_data, tmp_path_factory):
    destination = tmp_path_factory.mktemp("export") / "report.json"
    candidate = report(round_data)
    with pytest.raises(Invalid, match="exact private candidate"):
        export(round_data, destination, "wrong")
    assert export(round_data, destination, digest(json_bytes(candidate))) == 2
    assert read_json(destination)["status"] == "incomplete"
    target = round_data / "runs/run-001/result.json"
    value = read_json(target)
    value["answer"] = "access_token=synthetic-secret-value"
    target.write_bytes(json_bytes(value))
    candidate = report(round_data)
    with pytest.raises(Invalid, match="Sensitive-looking"):
        export(round_data, destination.parent / "blocked.json", digest(json_bytes(candidate)))


@pytest.mark.parametrize("file,field,value", [
    ("reservation.json", "manifest", "another-round"),
    ("result.json", "manifest", "another-round"),
    ("terminal.json", "manifest", "another-round"),
    ("terminal.json", "exit", 1),
])
def test_cross_round_or_contradictory_terminal_cannot_be_graded_or_reported(round_data, file, field, value):
    path = round_data / "runs/run-001" / file
    data = read_json(path)
    data[field] = value
    path.write_bytes(json_bytes(data))
    for operation in [lambda: report(round_data), lambda: grade(round_data, "run-001", good_grade())]:
        with pytest.raises(Invalid):
            operation()


@pytest.mark.parametrize("change", ["offset", "action", "missing_action"])
def test_grade_and_report_require_exact_pointers_and_complete_actions(round_data, change):
    value = good_grade()
    if change == "offset":
        value["A1"]["answer_offset"] = 1
    elif change == "action":
        value["A1"]["action_refs"] = ["stdout:999"]
    else:
        path = round_data / "runs/run-001/result.json"
        data = read_json(path)
        del data["action_violation"]
        path.write_bytes(json_bytes(data))
        with pytest.raises(Invalid, match="Incomplete valid-result"):
            report(round_data)
    with pytest.raises(Invalid):
        grade(round_data, "run-001", value)


def test_repeated_quote_is_tied_to_selected_occurrence(round_data):
    path = round_data / "runs/run-001/result.json"
    data = read_json(path)
    data["answer"] = "Keep progress. Then: Keep progress."
    path.write_bytes(json_bytes(data))
    value = good_grade()
    value["A1"]["answer_offset"] = data["answer"].rindex("Keep progress.")
    value["A1"]["action_refs"] = ["stdout:2"]
    grade(round_data, "run-001", value)
    assert read_json(path.with_name("grades.json"))["grades"]["A1"]["answer_offset"] == 21
