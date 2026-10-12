"""Exercise CLI installation through the real Bash installer."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def installer_source(tmp_path):
    source = tmp_path / "source"
    (source / ".claude/skills/example").mkdir(parents=True)
    (source / ".claude/skills/example/SKILL.md").write_text("# Example\n")
    for relative in (
        ".claude/CLAUDE.md",
        ".codex/AGENTS.md",
        ".copilot/copilot-instructions.md",
    ):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Test instructions\n")
    cli = source / ".local/bin/codex-session-stats"
    cli.parent.mkdir(parents=True)
    shutil.copy2(ROOT / ".local/bin/codex-session-stats", cli)
    hook = source / ".copilot/hooks/current-session.json"
    hook.parent.mkdir(parents=True)
    shutil.copy2(ROOT / ".copilot/hooks/current-session.json", hook)
    shutil.copy2(ROOT / "install-ia-skills.sh", source / "install-ia-skills.sh")
    return source


def run_installer(source, destination, *options, environment=None):
    destination.mkdir(exist_ok=True)
    return subprocess.run(
        ["bash", str(source / "install-ia-skills.sh"), "--destination", str(destination), *options],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def assert_cli_help(path):
    result = subprocess.run([str(path), "current", "--help"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "reasoning effort" in result.stdout


def test_local_install_dry_run_preserves_existing_cli_and_force_replaces_it(
    installer_source, tmp_path
):
    destination = tmp_path / "destination"
    cli = destination / ".local/bin/codex-session-stats"

    preview = run_installer(installer_source, destination, "--mode", "local", "--dry-run")
    assert preview.returncode == 0, preview.stderr
    assert "Codex session CLI link" in preview.stdout
    assert not cli.exists()
    assert not (destination / ".copilot/hooks/current-session.json").exists()

    installed = run_installer(installer_source, destination, "--mode", "local")
    assert installed.returncode == 0, installed.stderr
    assert cli.is_symlink()
    assert cli.resolve() == installer_source / ".local/bin/codex-session-stats"
    assert_cli_help(cli)
    hook = destination / ".copilot/hooks/current-session.json"
    assert hook.is_symlink()
    assert hook.read_bytes() == (installer_source / ".copilot/hooks/current-session.json").read_bytes()
    hook_configuration = json.loads(hook.read_text())
    environment = os.environ.copy()
    environment["PATH"] = str(cli.parent) + os.pathsep + environment["PATH"]
    context = subprocess.run(
        ["bash", "-c", hook_configuration["hooks"]["sessionStart"][0]["bash"]],
        input=json.dumps({"sessionId": "copilot-test", "source": "startup"}),
        capture_output=True, text=True, env=environment, check=False,
    )
    assert context.returncode == 0, context.stderr
    assert "--client copilot --session-id copilot-test" in json.loads(context.stdout)["additionalContext"]
    hook.unlink()
    hook.write_text('{"user": "owned"}\n')
    unrelated_hook = hook.parent / "other.json"
    unrelated_hook.write_text('{"unrelated": true}\n')

    cli.unlink()
    cli.write_text("user-owned command\n")
    preserved = run_installer(installer_source, destination, "--mode", "local")
    assert preserved.returncode == 0, preserved.stderr
    assert cli.read_text() == "user-owned command\n"
    assert hook.read_text() == '{"user": "owned"}\n'
    assert unrelated_hook.read_text() == '{"unrelated": true}\n'

    replaced = run_installer(installer_source, destination, "--mode", "local", "--force")
    assert replaced.returncode == 0, replaced.stderr
    assert cli.is_symlink()
    assert_cli_help(cli)
    assert hook.is_symlink()
    assert unrelated_hook.read_text() == '{"unrelated": true}\n'



def test_remote_install_copies_executable_cli(installer_source, tmp_path):
    archive = tmp_path / "source.tar.gz"
    with tarfile.open(archive, "w:gz") as output:
        output.add(installer_source, arcname="dotfiles")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(
        "#!/usr/bin/env python3\n"
        "import os, shutil, sys\n"
        "arguments = sys.argv[1:]\n"
        "shutil.copyfile(os.environ['TEST_ARCHIVE'], arguments[arguments.index('--output') + 1])\n"
    )
    curl.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = str(bin_dir) + os.pathsep + environment["PATH"]
    environment["TEST_ARCHIVE"] = str(archive)
    destination = tmp_path / "destination"

    result = run_installer(installer_source, destination, "--mode", "remote", environment=environment)

    assert result.returncode == 0, result.stderr
    cli = destination / ".local/bin/codex-session-stats"
    assert cli.is_file()
    assert not cli.is_symlink()
    assert os.access(cli, os.X_OK)
    assert cli.read_bytes() == (installer_source / ".local/bin/codex-session-stats").read_bytes()
    assert_cli_help(cli)
    hook = destination / ".copilot/hooks/current-session.json"
    assert hook.is_file()
    assert not hook.is_symlink()
    assert hook.read_bytes() == (installer_source / ".copilot/hooks/current-session.json").read_bytes()


def test_missing_python_fails_before_installing_files(installer_source, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to("/bin/false")
    environment = os.environ.copy()
    environment["PATH"] = str(bin_dir) + os.pathsep + environment["PATH"]
    destination = tmp_path / "destination"

    result = run_installer(installer_source, destination, "--mode", "local", environment=environment)

    assert result.returncode == 1
    assert "sqlite3 and zoneinfo" in result.stderr
    assert not (destination / ".claude").exists()
    assert not (destination / ".local").exists()


def test_missing_cli_source_fails_before_installing_skills(installer_source, tmp_path):
    (installer_source / ".local/bin/codex-session-stats").unlink()
    destination = tmp_path / "destination"

    result = run_installer(installer_source, destination, "--mode", "local")

    assert result.returncode == 1
    assert "Codex session CLI" in result.stderr
    assert not (destination / ".claude").exists()
    assert not (destination / ".local").exists()


def test_missing_session_hook_fails_before_installing_skills(installer_source, tmp_path):
    (installer_source / ".copilot/hooks/current-session.json").unlink()
    destination = tmp_path / "destination"
    result = run_installer(installer_source, destination, "--mode", "local")
    assert result.returncode == 1
    assert "Copilot session context source" in result.stderr
    assert not (destination / ".claude").exists()
    assert not (destination / ".local").exists()
