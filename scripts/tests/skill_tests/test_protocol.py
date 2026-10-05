from pathlib import Path

import pytest

from skill_tests.common import Invalid, digest, json_bytes, read_json, write_new
from skill_tests.protocol import CORPUS, PROFILES, cases, schedule, select_span
from skill_tests.runner import child_environment, process_identity, reconcile, remaining_processes


def test_all_cases_valid_and_live_budget_exact():
    corpus = cases()
    assert len(corpus) == 6
    selected = [key for key, case in corpus.items() if case["initial_live"]]
    assert selected == ["architecture", "authorization", "references"]
    cells = schedule(selected, PROFILES, ["current"], 2)
    assert len(cells) == 12
    assert len({c["id"] for c in cells}) == 12
    for name in selected:
        for model in ["sonnet", "luna"]:
            assert {c["repeat"] for c in cells if c["case"] == name and c["profile"] == model} == {1, 2}
    assert [c["profile"] for c in cells[:4]] == ["sonnet", "luna", "luna", "sonnet"]


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


def test_child_environment_does_not_inherit_credentials_or_runtime_overrides():
    env, omitted = child_environment({"PATH": "/usr/bin", "HOME": "/real-home", "API_KEY": "private",
                                      "GITLAB_TOKEN": "private", "CODEX_HOME": "/old", "PYTHONPATH": "/injection"})
    assert env == {"PATH": "/usr/bin", "HOME": "/real-home", "DISABLE_AUTOUPDATER": "1",
                   "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    assert omitted == ["API_KEY", "GITLAB_TOKEN"]


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
