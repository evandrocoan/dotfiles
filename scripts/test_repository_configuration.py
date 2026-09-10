"""Repository-level configuration invariants that are safe on hosted runners."""

import configparser
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def tracked(pattern):
    output = subprocess.check_output(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            pattern,
        ],
        cwd=ROOT,
    ).decode()
    return [ROOT / name for name in output.split("\0") if name]


def load_json_files(paths):
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def systemd_sections(path):
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.optionxform = str
    with path.open(encoding="utf-8") as stream:
        parser.read_file(stream)
    return set(parser.sections())


class RepositoryConfigurationTests(unittest.TestCase):
    def test_all_tracked_json_is_parseable(self):
        paths = tracked("*.json")
        self.assertGreater(len(paths), 0)
        self.assertEqual(len(load_json_files(paths)), len(paths))

    def test_json_validator_rejects_a_malformed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"missing":', encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_json_files([path])

    def test_systemd_sources_have_sections_required_by_their_unit_type(self):
        paths = tracked("scripts/systemd/system/**") + tracked(
            "scripts/install/systemd/user/**"
        )
        units = [path for path in paths if path.suffix in (".service", ".timer", ".conf")]
        self.assertGreater(len(units), 0)
        for path in units:
            with self.subTest(path=path.relative_to(ROOT)):
                sections = systemd_sections(path)
                self.assertTrue(sections)
                if path.suffix == ".service":
                    self.assertTrue({"Unit", "Service"}.issubset(sections))
                elif path.suffix == ".timer":
                    self.assertTrue({"Unit", "Timer"}.issubset(sections))

    def test_systemd_validator_rejects_content_outside_a_section(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.service"
            path.write_text("ExecStart=/bin/false\n", encoding="utf-8")
            with self.assertRaises(configparser.MissingSectionHeaderError):
                systemd_sections(path)

    def test_agent_instruction_compatibility_paths_are_canonical(self):
        self.assertEqual((ROOT / "CLAUDE.md").read_text(encoding="utf-8"), "@AGENTS.md\n")
        copilot = ROOT / ".github/copilot-instructions.md"
        self.assertTrue(copilot.is_symlink())
        self.assertEqual(copilot.readlink(), Path("../AGENTS.md"))
        self.assertEqual(copilot.resolve(), ROOT / "AGENTS.md")

    def test_ci_and_test_sources_are_allowlisted_while_secrets_remain_ignored(self):
        visible = [
            ".github/workflows/tests.yml",
            "scripts/test_repository_configuration.py",
            "scripts/test_redmine_time_send.py",
            "scripts/test_smartgit_create_mr.py",
            "scripts/test_fix_windows_zip_paths.py",
            "scripts/run_repository_tests.sh",
        ]
        for path in visible:
            with self.subTest(path=path):
                result = subprocess.run(
                    ["git", "check-ignore", "-q", path], cwd=ROOT, check=False
                )
                self.assertEqual(result.returncode, 1)
        for path in ("scripts/.env", ".cache/private-data"):
            with self.subTest(path=path):
                result = subprocess.run(
                    ["git", "check-ignore", "-q", path], cwd=ROOT, check=False
                )
                self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
