"""Run the Bash entry point with real dotenv parsing and isolated SSH/notification tools."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "check_ci"
REAL_TIMEOUT = shutil.which("timeout")
REAL_BASH = shutil.which("bash")


def executable(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body), encoding="utf-8")
    path.chmod(0o755)


@pytest.fixture
def monitor(tmp_path):
    directory = tmp_path / "scripts with spaces"
    directory.mkdir()
    source = Path(os.environ.get("CHECK_CI_TEST_SOURCE", SOURCE))
    script = directory / "check_ci"
    shutil.copyfile(source, script)
    config = directory / ".env"
    config.write_text('CHECK_CI_HOSTS="first second"\n', encoding="utf-8")
    python = directory / ".venv/bin/python"
    executable(python, """
        import os
        import sys
        os.execv(sys.executable, [sys.executable, *sys.argv[1:]])
    """)

    tools = tmp_path / "bin"
    record = """
import json
import os
from pathlib import Path
import sys
with Path(os.environ['CHECK_CI_CALLS']).open('a') as stream:
    stream.write(json.dumps([Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')
"""
    executable(tools / "ssh", record + """
import time
mode = json.loads(os.environ.get('CHECK_CI_SSH_RESULTS', '{}')).get(sys.argv[-2], 'success')
if mode == 'reset':
    print('kex_exchange_identification: read: Connection reset by peer', file=sys.stderr)
    sys.exit(255)
if mode == 'hang':
    time.sleep(30)
if mode == 'auth':
    print('Permission denied (publickey).', file=sys.stderr)
    sys.exit(255)
""")
    executable(tools / "notify-send", record + """
if os.environ.get('CHECK_CI_NOTIFY_FAIL'):
    print('Notification bus unavailable', file=sys.stderr)
    sys.exit(1)
""")
    executable(tools / "timeout", record + """
args = sys.argv[1:]
if args[2] == 'ssh' and os.environ.get('CHECK_CI_SHORT_TIMEOUT'):
    args[1] = '0.2s'
os.execv(os.environ['CHECK_CI_REAL_TIMEOUT'], ['timeout', *args])
""")
    # The legacy port probe succeeds, reproducing the reported false positive.
    executable(tools / "nc", record)
    calls = tmp_path / "calls.jsonl"
    env = {
        **os.environ,
        "PATH": f"{tools}{os.pathsep}{os.defpath}",
        "CHECK_CI_CALLS": str(calls),
        "CHECK_CI_REAL_TIMEOUT": REAL_TIMEOUT,
    }
    cwd = tmp_path / "another directory"
    cwd.mkdir()

    def run(results=None, **overrides):
        return subprocess.run(
            [REAL_BASH, str(script)],
            cwd=cwd,
            env={**env, "CHECK_CI_SSH_RESULTS": json.dumps(results or {}), **overrides},
            capture_output=True,
            text=True,
            timeout=10,
        )

    def invocations(name):
        records = [json.loads(line) for line in calls.read_text().splitlines()]
        return [record[1:] for record in records if record[0] == name]

    return run, invocations, config, python


def test_loads_adjacent_dotenv_and_checks_authenticated_ssh(monitor):
    run, calls, config, _ = monitor
    config.write_text('export CHECK_CI_HOSTS="first user@second 192.0.2.3" # hosts\n')

    result = run(CHECK_CI_HOSTS="ignored-inherited-value")

    assert result.returncode == 0, result.stderr
    assert [args[-2:] for args in calls("ssh")] == [
        ["first", "true"], ["user@second", "true"], ["192.0.2.3", "true"]
    ]
    assert calls("nc") == []
    assert calls("notify-send") == []
    for args in calls("ssh"):
        assert args == [
            "-nT", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "ConnectionAttempts=1", "-o", "StrictHostKeyChecking=yes",
            "-o", "UpdateHostKeys=no", "-o", "ControlMaster=no",
            "-o", "ControlPath=none", "-o", "ClearAllForwardings=yes",
            "-o", "ForwardAgent=no", "-o", "ForwardX11=no", "--", args[-2], "true",
        ]
    assert [args[:3] for args in calls("timeout")] == [
        ["--kill-after=2s", "15s", "ssh"]
    ] * 3
    assert "SSH check succeeded for first." in result.stdout


@pytest.mark.parametrize("mode,diagnostic", [
    ("reset", "Connection reset by peer"),
    ("auth", "Permission denied (publickey)."),
])
def test_ssh_failure_notifies_and_continues_to_remaining_hosts(monitor, mode, diagnostic):
    run, calls, _, _ = monitor

    result = run({"first": mode})

    assert result.returncode == 1
    assert [args[-2] for args in calls("ssh")] == ["first", "second"]
    assert diagnostic in result.stderr
    assert "SSH check succeeded for second." in result.stdout
    notifications = calls("notify-send")
    assert len(notifications) == 1
    assert notifications[0][:2] == ["--", "check_ci"]
    assert "SSH check failed for first (exit 255)" in notifications[0][2]
    assert diagnostic in notifications[0][2]


def test_real_timeout_terminates_stalled_ssh_and_continues(monitor):
    run, calls, _, _ = monitor

    result = run({"first": "hang"}, CHECK_CI_SHORT_TIMEOUT="1")

    assert result.returncode == 1
    assert "SSH check failed for first (exit 124)" in result.stderr
    assert "SSH check succeeded for second." in result.stdout
    assert [args[-2] for args in calls("ssh")] == ["first", "second"]
    assert len(calls("notify-send")) == 1


def test_notification_failure_is_visible_and_does_not_stop_other_checks(monitor):
    run, calls, _, _ = monitor

    result = run({"first": "reset", "second": "auth"}, CHECK_CI_NOTIFY_FAIL="1")

    assert result.returncode == 1
    assert [args[-2] for args in calls("ssh")] == ["first", "second"]
    assert len(calls("notify-send")) == 2
    assert result.stderr.count("could not deliver the check_ci notification") == 2
    assert "Notification bus unavailable" in result.stderr


@pytest.mark.parametrize("contents", [
    "OTHER=value\n",
    "CHECK_CI_HOSTS=\n",
    'CHECK_CI_HOSTS="  "\n',
    'CHECK_CI_HOSTS="-oProxyCommand=bad"\n',
    'CHECK_CI_HOSTS="first;bad"\n',
    'CHECK_CI_HOSTS="${INHERITED_HOST}"\n',
])
def test_invalid_configuration_notifies_without_running_ssh(monitor, contents):
    run, calls, config, _ = monitor
    config.write_text(contents)

    result = run(INHERITED_HOST="first")

    assert result.returncode == 2
    assert "Error:" in result.stderr
    assert calls("ssh") == []
    assert len(calls("notify-send")) == 1
    assert "Invalid configuration" in calls("notify-send")[0][2]


def test_missing_dotenv_notifies_without_running_ssh(monitor):
    run, calls, config, _ = monitor
    config.unlink()

    result = run()

    assert result.returncode == 2
    assert "configuration file not found" in result.stderr
    assert calls("ssh") == []
    assert len(calls("notify-send")) == 1


def test_missing_python_environment_has_actionable_diagnostic(monitor):
    run, calls, _, python = monitor
    python.unlink()

    result = run()

    assert result.returncode == 2
    assert "run poetry install" in result.stderr
    assert calls("ssh") == []
    assert len(calls("notify-send")) == 1


def test_dotenv_is_data_and_duplicate_destinations_are_checked_once(monitor, tmp_path):
    run, calls, config, _ = monitor
    sentinel = tmp_path / "must-not-exist"
    config.write_text(
        f'OTHER="$(touch {sentinel})"\n'
        'CHECK_CI_HOSTS="first\nsecond first"\n'
    )

    result = run()

    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    assert [args[-2] for args in calls("ssh")] == ["first", "second"]
