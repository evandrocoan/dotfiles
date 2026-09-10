"""Hermetic tests for the SmartGit commit and merge-request helper."""

import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import call, patch


ROOT = Path(__file__).resolve().parent


class SilentLogger:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def load_script():
    dotenv = ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    loguru = ModuleType("loguru")
    loguru.logger = SilentLogger()
    spec = importlib.util.spec_from_file_location(
        "smartgit_create_mr_under_test", ROOT / "smartgit_create_mr.py"
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        os.environ, {"GITLAB_URL": "https://gitlab.com"}, clear=True
    ), patch.dict(sys.modules, {"dotenv": dotenv, "loguru": loguru}):
        spec.loader.exec_module(module)
    return module


class FakeHttpResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class SmartGitTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_script()

    def test_extracts_project_path_from_ssh_and_https_remotes(self):
        remotes = (
            ("git@gitlab.example:group/subgroup/project.git\n", "group/subgroup/project"),
            ("https://gitlab.example/group/project.git\n", "group/project"),
        )
        for remote, expected in remotes:
            with self.subTest(remote=remote), patch.object(
                self.tool, "run", return_value=SimpleNamespace(stdout=remote)
            ) as run:
                self.assertEqual(self.tool.get_remote_project_path(), expected)
                run.assert_called_once_with(["git", "remote", "get-url", "origin"])

    def test_builds_authenticated_json_request_and_decodes_response(self):
        response = FakeHttpResponse({"id": 17})
        with patch.object(
            self.tool.urllib.request, "urlopen", return_value=response
        ) as urlopen:
            result = self.tool.gitlab_request(
                "POST",
                "/projects/42/merge_requests",
                "token-value",
                {"source_branch": "feature/test"},
            )

        self.assertEqual(result, {"id": 17})
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://gitlab.com/api/v4/projects/42/merge_requests",
        )
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), {"source_branch": "feature/test"})
        self.assertEqual(request.get_header("Private-token"), "token-value")
        self.assertEqual(request.get_header("Content-type"), "application/json")

    def test_main_runs_exact_git_and_api_flow(self):
        process = SimpleNamespace(returncode=0)
        api_results = [
            {"id": 42},
            {"web_url": "https://gitlab.example/group/project/-/merge_requests/7"},
        ]
        with patch.object(self.tool, "get_current_branch", return_value="master"), patch.object(
            self.tool, "get_token", return_value="token-value"
        ), patch.object(
            self.tool, "get_remote_project_path", return_value="group/project"
        ), patch.object(
            self.tool,
            "run",
            return_value=SimpleNamespace(stdout="Describe the change\n"),
        ) as captured_run, patch.object(
            self.tool, "gitlab_request", side_effect=api_results
        ) as request, patch.object(
            self.tool.subprocess, "run", return_value=process
        ) as subprocess_run, patch(
            "builtins.input", side_effect=["feature/test", "develop", ""]
        ):
            self.tool.main()

        captured_run.assert_called_once_with(["git", "log", "-1", "--format=%s"])
        self.assertEqual(
            subprocess_run.call_args_list,
            [
                call(["git", "checkout", "-b", "feature/test"], check=True),
                call(["oco", "--yes"]),
                call(["git", "push", "-u", "origin", "feature/test"], check=True),
                call(
                    [
                        "xdg-open",
                        "https://gitlab.example/group/project/-/merge_requests/7",
                    ]
                ),
            ],
        )
        self.assertEqual(
            request.call_args_list,
            [
                call("GET", "/projects/group%2Fproject", "token-value"),
                call(
                    "POST",
                    "/projects/42/merge_requests",
                    "token-value",
                    {
                        "source_branch": "feature/test",
                        "target_branch": "develop",
                        "title": "Describe the change",
                        "remove_source_branch": True,
                    },
                ),
            ],
        )

    def test_missing_token_stops_before_local_or_remote_effects(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            self.tool, "get_current_branch"
        ) as current_branch, patch.object(
            self.tool.subprocess, "run"
        ) as subprocess_run, patch.object(
            self.tool, "gitlab_request"
        ) as request, patch(
            "builtins.input"
        ) as input_fn, self.assertRaises(SystemExit) as raised:
            self.tool.main()

        self.assertEqual(raised.exception.code, 1)
        current_branch.assert_not_called()
        subprocess_run.assert_not_called()
        request.assert_not_called()
        input_fn.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
