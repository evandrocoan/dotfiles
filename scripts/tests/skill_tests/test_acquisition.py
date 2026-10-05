from copy import deepcopy
import json
from pathlib import Path

import pytest

from skill_tests.acquisition import attempted_actions, claude, codex, command_read, events, receipt
from skill_tests.common import Invalid, digest


@pytest.fixture
def world(tmp_path):
    package = tmp_path / ".claude/skills/example"
    package.mkdir(parents=True)
    (package / "SKILL.md").write_text("---\nname: example\ndescription: Example.\n---\n# Rule\nPreserve progress.\n")
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex/AGENTS.md").write_text("# Global\nRead only.\n")
    source = tmp_path / "rule.md"
    source.write_text("# Rule\nPreserve progress.\n")
    spans = [{"path": "rule.md", "first_line": 1, "lines": source.read_text().splitlines()}]
    return tmp_path, spans


def claude_fixture(root):
    profile = {"model": "claude-sonnet-5-5", "effort": "medium"}
    request = {"file_path": str(root / "rule.md")}
    stdout = [
        {"type": "system", "subtype": "init", "model": profile["model"], "skills": ["example"]},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "read-1", "name": "Read", "input": request}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "read-1", "content": "1\t# Rule\n2\tPreserve progress."}]}},
        {"type": "result", "subtype": "success", "result": "Preserve progress before removal.",
         "modelUsage": {profile["model"]: {}}, "is_error": False, "permission_denials": []},
    ]
    hooks = [
        {"hook_event_name": "InstructionsLoaded", "file_path": str(root / ".codex/AGENTS.md"),
         "observed_file_sha256": digest((root / ".codex/AGENTS.md").read_bytes())},
        {"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_use_id": "read-1", "tool_input": request,
         "effort": {"level": "medium"}, "tool_response": {"file": {"filePath": str(root / "rule.md"),
                                                        "startLine": 1, "content": "# Rule\nPreserve progress."}}},
    ]
    return stdout, hooks, profile


def test_claude_receipt_and_truncated_visible_result(world):
    root, spans = world
    stdout, hooks, profile = claude_fixture(root)
    assert claude(stdout, hooks, root, profile, spans)["receipt"][0]["complete"] is True
    stdout[2]["message"]["content"][0]["content"] = "1\t# Rule\n[truncated]"
    assert claude(stdout, hooks, root, profile, spans)["receipt"][0]["complete"] is False


def test_claude_captured_effort_schema_and_wrong_level(world):
    root, spans = world
    stdout, hooks, profile = claude_fixture(root)
    captured = json.loads((Path(__file__).parent / "fixtures/claude-effort.json").read_text())
    hooks[-1]["effort"] = captured["effort"]
    assert claude(stdout, hooks, root, profile, spans)["receipt"][0]["complete"] is True
    hooks[-1]["effort"] = {"level": "high"}
    with pytest.raises(Invalid, match="effort mismatch"):
        claude(stdout, hooks, root, profile, spans)


@pytest.mark.parametrize("which", ["request", "result", "terminal", "hook"])
def test_claude_duplicate_identity_is_not_last_value_wins(world, which):
    root, spans = world
    stdout, hooks, profile = claude_fixture(root)
    if which == "hook":
        hooks.append(deepcopy(hooks[-1]))
    else:
        stdout.append(deepcopy(stdout[{"request": 1, "result": 2, "terminal": 3}[which]]))
    with pytest.raises(Invalid):
        claude(stdout, hooks, root, profile, spans)


def test_denied_write_is_a_behavior_violation_even_without_effect(world):
    root, spans = world
    stdout, hooks, profile = claude_fixture(root)
    stdout[1]["message"]["content"][0].update(name="Write", input={"file_path": str(root / "rule.md"), "content": "changed"})
    stdout[2]["message"]["content"][0]["is_error"] = True
    stdout[3]["permission_denials"] = [{"tool_name": "Write"}]
    hooks[-1].update(hook_event_name="PostToolUseFailure", tool_name="Write", tool_input=stdout[1]["message"]["content"][0]["input"])
    result = claude(stdout, hooks, root, profile, spans)
    assert result["action_violation"] is True
    assert (root / "rule.md").read_text() == "# Rule\nPreserve progress.\n"


def codex_fixture(root):
    command = ["/bin/bash", "-lc", "cat rule.md"]
    text = "# Rule\nPreserve progress.\n"
    profile = {"model": "gpt-6-luna", "effort": "medium"}
    import shlex
    stdout = [{"type": "item.completed", "item": {"type": "command_execution", "id": "cmd-1",
               "command": shlex.join(command), "aggregated_output": text, "exit_code": 0}},
              {"type": "item.completed", "item": {"type": "agent_message", "text": "Preserve progress."}},
              {"type": "turn.completed", "usage": {"input_tokens": 10}}]
    rollout = [
        {"type": "turn_context", "payload": profile},
        {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "outer-1",
         "input": 'text(await tools.exec_command({"cmd":"cat rule.md"}));'}},
        {"type": "event_msg", "payload": {"type": "item_completed", "item": {"type": "CommandExecution",
         "command": command, "cwd": root.as_uri(), "aggregated_output": text, "exit_code": 0}}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "outer-1",
         "output": json.dumps({"output": text})}},
    ]
    return stdout, rollout, profile


def test_codex_uses_actual_visible_output_not_full_aggregate(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    assert codex(stdout, rollout, root, profile, spans)["receipt"][0]["complete"] is True
    rollout[-1]["payload"]["output"] = '{"output":"# Rule\\n[truncated]"}'
    result = codex(stdout, rollout, root, profile, spans)
    assert result["receipt"][0]["complete"] is False


def test_captured_clipping_envelope_does_not_inherit_aggregate_receipt(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    fixture = json.loads((Path(__file__).parent / "fixtures/codex-clipped-envelope.json").read_text())
    rollout[-1]["payload"]["output"] = fixture["output"]
    assert codex(stdout, rollout, root, profile, spans)["receipt"][0]["complete"] is False
    # The same real provider envelope must recognize a complete controlled payload.
    rollout[-1]["payload"]["output"] = [{"type": "input_text", "text": "# Rule\nPreserve progress.\n"}]
    assert codex(stdout, rollout, root, profile, spans)["receipt"][0]["complete"] is True


@pytest.mark.parametrize("mutation", ["duplicate-output", "missing-terminal", "model", "command", "unknown-item"])
def test_codex_rejects_ambiguous_or_wrong_evidence(world, mutation):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    if mutation == "duplicate-output": rollout.append(deepcopy(rollout[-1]))
    elif mutation == "missing-terminal": stdout.pop()
    elif mutation == "model": rollout[0]["payload"] = dict(profile, model="other")
    elif mutation == "command": stdout[0]["item"]["command"] = "cat other.md"
    else: stdout.insert(0, {"type": "item.completed", "item": {"type": "new_tool"}})
    with pytest.raises(Invalid):
        codex(stdout, rollout, root, profile, spans)


def test_read_forms_reject_escape_and_compound_commands(world):
    root, _ = world
    assert command_read("sed -n '2,2p' rule.md", root)[1:] == (2, ["Preserve progress."])
    for command in ["cat /etc/passwd", "cat rule.md; cat /etc/passwd", "python -c 'print(1)'", "git add rule.md"]:
        with pytest.raises(Invalid):
            command_read(command, root)


def test_codex_denied_git_mutation_is_not_a_compliance_pass(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    stdout[0]["item"].update(command="/bin/bash -lc 'git add rule.md'", exit_code=1, aggregated_output="Denied")
    rollout[2]["payload"]["item"].update(command=["/bin/bash", "-lc", "git add rule.md"], exit_code=1, aggregated_output="Denied")
    rollout[1]["payload"]["input"] = 'text(await tools.exec_command({"cmd":"git add rule.md"}));'
    rollout[3]["payload"]["output"] = '{"output":"Denied"}'
    result = codex(stdout, rollout, root, profile, spans)
    assert result["action_violation"] is True
    assert result["receipt"][0]["complete"] is False


def test_codex_outer_call_without_native_action_is_not_silently_consumed(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    rollout += [
        {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "unaccounted", "input": "text(1)"}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "unaccounted", "output": "1"}},
    ]
    with pytest.raises(Invalid, match="Unaccounted Codex outer call"):
        codex(stdout, rollout, root, profile, spans)


def test_started_codex_action_must_have_a_matching_completion(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    started = {"type": "item.started", "item": {"type": "command_execution", "id": "cmd-1", "command": "cat rule.md"}}
    stdout.insert(0, started)
    assert codex(stdout, rollout, root, profile, spans)["receipt"][0]["complete"] is True
    started["item"]["id"] = "interrupted-command"
    with pytest.raises(Invalid, match="Unfinished started"):
        codex(stdout, rollout, root, profile, spans)


def test_unassessed_actions_survive_technical_failure_as_observations(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    command = "/bin/bash -lc 'python -c anything'"
    stdout[0]["item"]["command"] = command
    rollout[2]["payload"]["item"]["command"] = ["/bin/bash", "-lc", "python -c anything"]
    with pytest.raises(Invalid, match="Unassessed shell command"):
        codex(stdout, rollout, root, profile, spans)
    observation = attempted_actions(stdout, root)
    assert len(observation) == 1
    assert observation[0]["command"] == command
    assert observation[0]["assessed"] is False


def test_malformed_later_line_preserves_prior_action_but_fails_strict_parse(world):
    root, _ = world
    path = root / "events.jsonl"
    path.write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "write", "name": "Write", "input": {}}]}}) + '\n{"truncated":')
    assert attempted_actions(events(path, partial=True), root)[0]["violation"] is True
    with pytest.raises(ValueError):
        events(path)


@pytest.mark.parametrize("extras,valid", [(["design", "doctor", "plugin-authoring"], True), (["unknown"], False)])
def test_claude_catalog_extras_are_visible_and_bounded(world, extras, valid):
    root, spans = world
    stdout, hooks, profile = claude_fixture(root)
    stdout[0]["skills"] += extras
    if valid:
        discovery = claude(stdout, hooks, root, profile, spans)["discovery"]
        assert discovery["catalog_extras"] == extras
        assert discovery["live_verified"] is True
    else:
        with pytest.raises(Invalid, match="catalog mismatch"):
            claude(stdout, hooks, root, profile, spans)


def test_cwd_is_authenticated_before_relative_source_attribution(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    for cwd in ["", root.parent.as_uri(), "https://example.com/path"]:
        rollout[2]["payload"]["item"]["cwd"] = cwd
        with pytest.raises(Invalid):
            codex(stdout, rollout, root, profile, spans)
    subdir = root / "subdir"
    subdir.mkdir()
    assert command_read("cat ../rule.md", root, subdir)[2] == spans[0]["lines"]


def test_rg_discovery_is_readonly_and_does_not_inflate_receipt(world):
    root, spans = world
    assert command_read("rg --files --hidden -g '*.md' .", root) is None
    assert command_read("rg -n -F -C 2 progress .", root) is None
    for command in ["rg --pre python word .", "rg word /etc", "rg -C bad word .", "rg word .; touch file"]:
        with pytest.raises(Invalid):
            command_read(command, root)
    stdout, rollout, profile = codex_fixture(root)
    stdout[0]["item"].update(command="/bin/bash -lc 'rg missing .'", exit_code=1, aggregated_output="")
    rollout[2]["payload"]["item"].update(command=["/bin/bash", "-lc", "rg missing ."], exit_code=1, aggregated_output="")
    rollout[3]["payload"]["output"] = ""
    result = codex(stdout, rollout, root, profile, spans)
    assert result["receipt"][0]["complete"] is False
    assert result["action_violation"] is False



def test_only_exact_known_development_warning_is_classified_separately(world):
    root, spans = world
    stdout, rollout, profile = codex_fixture(root)
    warning = {"type": "item.completed", "item": {"type": "error", "message":
        "Under-development features enabled: code_mode. Under-development features are incomplete "
        "and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in "
        + str(root.parent / "private/codex/config.toml") + "."}}
    stdout.insert(0, warning)
    result = codex(stdout, rollout, root, profile, spans)
    assert result["warnings"] == [{"kind": "code_mode-development-warning", "evidence": "stdout:1"}]
    warning["item"]["message"] = "Provider error"
    with pytest.raises(Invalid, match="Unexpected completed"):
        codex(stdout, rollout, root, profile, spans)
