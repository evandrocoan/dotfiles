"""Native relay and public configuration contracts retained across queue replacement."""
import json


import os


from pathlib import Path


import subprocess


import sys


import datetime as dt


import copy


import runpy


import sqlite3


import types


import io


import tomllib


import tempfile


import shutil


import socket


import struct


from urllib.parse import urlsplit, parse_qs


from email.utils import format_datetime


import pytest


CLI = Path(os.environ.get("CODEX_MONITOR_TEST_CLI", Path(__file__).resolve().parents[2] / ".local/bin/codex-session-stats"))


def test_shared_runtime_rejects_agent_writable_location_before_creating_files(tmp_path, monkeypatch):
    config = configure(tmp_path)
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    config["state_file"] = str(runtime / "state.sqlite3")
    module = runpy.run_path(str(CLI))
    with pytest.raises(RuntimeError, match="outside the monitor's writable"):
        module["monitor_shared_runtime"](config, create=True)
    assert list(runtime.iterdir()) == []


def run_monitor(tmp_path, *arguments, input_text=None, extra_env=None):
    environment = os.environ.copy()
    environment.update({"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config"),
                        "XDG_STATE_HOME": str(tmp_path / "state"), "PYTHONDONTWRITEBYTECODE": "1"})
    environment.pop("CODEX_HOME", None)
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), "monitor-gitlab", "--config",
         str(tmp_path / "monitor.json"), *arguments],
        input=input_text, capture_output=True, text=True, env=environment, check=False,
    )


def configure(tmp_path):
    result = run_monitor(tmp_path, "configure", "--project-url",
                         "https://gitlab.example.test/engineering/project", "--project-id", "42")
    assert result.returncode == 0, result.stderr
    return runpy.run_path(str(CLI))["mq_config"](tmp_path / "monitor.json")


def test_mq_configure_is_private_and_status_does_not_initialize_state(tmp_path):
    config = configure(tmp_path)
    analysis = tomllib.loads((tmp_path / "analysis.toml").read_text())
    assert analysis["codex_model"] == config["model"] == "gpt-6.1-sol"
    assert analysis["codex_effort"] == config["effort"] == "xhigh"
    assert not {"model", "model_reasoning_effort"} & analysis.keys()
    assert config["project_id"] == 42
    assert config["project_path"] == "engineering/project"
    assert config["weekdays"] == [0, 1, 2, 3, 4, 5]
    assert config["open_hour"] == 7
    assert config["close_hour"] == 22
    assert config["interval_minutes"] == 15
    assert analysis["history_limit"] == config["history_limit"] == 2000
    assert (tmp_path / "monitor.json").stat().st_mode & 0o777 == 0o600
    before = (tmp_path / "monitor.json").read_bytes()
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["initialized"] is False
    assert not Path(config["state_file"]).exists()
    assert (tmp_path / "monitor.json").read_bytes() == before


def test_existing_analysis_toml_without_history_limit_uses_default(tmp_path):
    config=configure(tmp_path)
    analysis=tmp_path/'analysis.toml'
    analysis.write_text('\n'.join(line for line in analysis.read_text().splitlines()
                                  if not line.startswith('history_limit ='))+'\n')
    loaded=runpy.run_path(str(CLI))['mq_config'](tmp_path/'monitor.json')
    assert loaded['history_limit']==2000
    assert not Path(loaded['queue_file']).exists()


@pytest.mark.parametrize("original,replacement,error", [
    ('codex_model = "gpt-6.1-sol"', 'model = "gpt-6.1-sol"', "unknown or missing TOML settings"),
    ('codex_effort = "xhigh"', 'model_reasoning_effort = "xhigh"', "unknown or missing TOML settings"),
    ('codex_model = "gpt-6.1-sol"', '', "unknown or missing TOML settings"),
    ('codex_effort = "xhigh"', '', "unknown or missing TOML settings"),
    ('codex_model = "gpt-6.1-sol"', 'codex_model = ""', "invalid codex_model"),
    ('codex_effort = "xhigh"', 'codex_effort = "invalid"', "invalid codex_effort"),
    ('history_limit = 2000', 'history_limit = 0', "history_limit must be a positive integer"),
    ('history_limit = 2000', 'history_limit = true', "history_limit must be a positive integer"),
])
def test_invalid_codex_toml_settings_fail_before_queue_creation(tmp_path, original, replacement, error):
    config = configure(tmp_path)
    analysis = tmp_path / "analysis.toml"
    text = analysis.read_text()
    assert text.count(original) == 1
    analysis.write_text(text.replace(original, replacement))
    result = run_monitor(tmp_path, "initialize")
    assert result.returncode == 1
    assert error in result.stderr
    assert not Path(config["queue_file"]).exists()


def test_mq_configure_never_overwrites_existing_configuration(tmp_path):
    configure(tmp_path)
    before = (tmp_path / "monitor.json").read_bytes()
    result = run_monitor(tmp_path, "configure", "--project-url",
                         "https://other.example.test/team/other", "--project-id", "99")
    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert (tmp_path / "monitor.json").read_bytes() == before


@pytest.mark.parametrize("url", ["http://gitlab.example.test/group/project",
    "https://user:password@gitlab.example.test/group/project",
    "https://gitlab.example.test/group/project?token=secret",
    "https://gitlab.example.test/group/../project"])
def test_monitor_rejects_unsafe_project_urls_without_creating_config(tmp_path, url):
    result = run_monitor(tmp_path, "configure", "--project-url", url, "--project-id", "42")
    assert result.returncode == 1
    assert not (tmp_path / "monitor.json").exists()
    assert not (tmp_path / "state").exists()


def test_optional_websocket_import_is_absent_from_help_and_offline_status(tmp_path):
    configure(tmp_path)
    poison = tmp_path / "poison"
    poison.mkdir()
    (poison / "websockets.py").write_text("raise RuntimeError('unexpected optional import')\n")
    for arguments in (("--help",), ("status",)):
        result = run_monitor(tmp_path, *arguments, extra_env={"PYTHONPATH": str(poison)})
        assert result.returncode == 0, result.stderr
        assert "unexpected optional import" not in result.stderr
