"""Deterministic tests for the Redmine time-entry parser and send boundary."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "redmine_time_send", ROOT / ".local/bin/redmine_time_send.py"
)
redmine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(redmine)


def parse(text):
    state = redmine.State()
    for line in textwrap.dedent(text).strip().splitlines():
        redmine.parse_time_line(state, line)
    redmine.parse_time_line(state, "")
    return state


class Response:
    def __init__(self, status_code=200, text="ok", subject="Task title"):
        self.status_code = status_code
        self.text = text
        self.subject = subject

    def json(self):
        return {"issue": {"subject": self.subject}}


class ParserTests(unittest.TestCase):
    def test_parses_all_entries_and_reports_the_sunday_total(self):
        state = parse(
            """
            1. Add 1.0 hours/8 (2023/04/12) #81448 first task
            1. Add 1.0 hours/8 (2023/04/12) #80661 second task
            1. Add 5.0 hours/8 (2023/04/12) #89081 third task

            1. Add 6.0 hours/8 (2023/04/15) #89081 saturday task

            1. Add 1.0 hours/8 (2023/04/16) #81352 sunday task one
            1. Add 1.0 hours/8 (2023/04/16) #81236 sunday task two
            1. Add 5.0 hours/8 (2023/04/16) #89081 sunday task three
            """
        )

        self.assertEqual(
            [entry["issue_id"] for entry in state.entries],
            [81448, 80661, 89081, 89081, 81352, 81236, 89081],
        )
        self.assertEqual(state.errors, [])
        self.assertEqual(len(state.warnings), 1)
        self.assertIn("on Sunday", state.warnings[0])
        self.assertIn("Invalid total time 7.0", state.warnings[0])

    def test_extracts_nested_comment_and_title(self):
        state = parse(
            """
            1. Add 1.0 hours/8 (2023/04/12) #80661 before (:note with (detail)) after
            """
        )

        self.assertEqual(state.errors, [])
        self.assertEqual(state.entries[0]["comments"], "note with (detail)")
        self.assertEqual(state.entries[0]["title"], "before after")

    def test_rejects_unbalanced_comments(self):
        for suffix in ("(:open (comment)", "(:closed) extra)"):
            with self.subTest(suffix=suffix):
                state = parse(
                    f"1. Add 1.0 hours/8 (2023/04/12) #80661 task {suffix}"
                )
                self.assertEqual(state.entries, [])
                self.assertEqual(len(state.errors), 1)
                self.assertIn("Unbalanced parentheses on input", state.errors[0])

    def test_rejects_invalid_fields_and_syntax(self):
        scenarios = (
            (
                "1. Add 1.0 hours/8 (2023/04/12) #invalid task",
                "Invalid data issue_id",
            ),
            (
                "1. Add 1.0 hours/7 (2023/04/12) #80661 task",
                "Invalid data activity_id",
            ),
            (
                "1. Add 1.0 hours8 (2023/04/12) #80661 task",
                "Line with invalid data",
            ),
        )
        for line, message in scenarios:
            with self.subTest(line=line):
                state = parse(line)
                self.assertEqual(state.entries, [])
                self.assertEqual(len(state.errors), 1)
                self.assertIn(message, state.errors[0])

    def test_rejects_mixed_decreasing_and_repeated_date_blocks(self):
        scenarios = (
            (
                """
                1. Add 1.0 hours/8 (2023/04/12) #80661 first
                1. Add 1.0 hours/8 (2023/04/13) #80662 mixed
                """,
                "Each line group must be from the same date",
            ),
            (
                """
                1. Add 1.0 hours/8 (2023/04/15) #80661 first

                1. Add 1.0 hours/8 (2023/04/14) #80662 earlier
                """,
                "Invalid date 2023-04-15 00:00:00",
            ),
            (
                """
                1. Add 1.0 hours/8 (2023/04/15) #80661 first

                1. Add 1.0 hours/8 (2023/04/15) #80662 repeated
                """,
                "The next block must be from higher date",
            ),
        )
        for text, message in scenarios:
            with self.subTest(message=message):
                state = parse(text)
                self.assertEqual(len(state.errors), 1)
                self.assertIn(message, state.errors[0])

    def test_applies_weekday_and_weekend_hour_rules(self):
        scenarios = (
            ("2023/04/14", [5], "Invalid total time 5.0"),
            ("2023/04/14", [7], None),
            ("2023/04/14", [6, 5], "Invalid total time 11.0"),
            ("2023/04/15", [3], None),
            ("2023/04/15", [6, 5], "Invalid total time 11.0"),
            ("2023/04/16", [2], "Invalid total time 2.0"),
        )
        for date, hours, warning in scenarios:
            with self.subTest(date=date, hours=hours):
                lines = "\n".join(
                    f"1. Add {value}.0 hours/8 ({date}) #{80000 + index} task"
                    for index, value in enumerate(hours)
                )
                state = parse(lines)
                self.assertEqual(state.errors, [])
                if warning is None:
                    self.assertEqual(state.warnings, [])
                else:
                    self.assertEqual(len(state.warnings), 1)
                    self.assertIn(warning, state.warnings[0])


class NetworkBoundaryTests(unittest.TestCase):
    def test_title_lookup_caches_issues_and_deduplicates_mismatches(self):
        calls = []

        def request_get(url, headers):
            calls.append((url, headers))
            return Response(subject="Remote title")

        entries = [
            {"issue_id": 42, "title": "Local title"},
            {"issue_id": 42, "title": "Local title"},
            {"issue_id": 42, "title": "Another title"},
            {"issue_id": 43},
        ]
        headers = {"X-Redmine-API-Key": "fixture"}

        result = redmine.verify_titles(entries, "https://redmine.test", headers, request_get)

        self.assertEqual(
            result,
            [
                (42, "Local title", "Remote title"),
                (42, "Another title", "Remote title"),
            ],
        )
        self.assertEqual(
            calls,
            [("https://redmine.test/issues/42.json", headers)],
        )

    def test_dry_run_never_reads_credentials_or_calls_external_boundaries(self):
        def forbidden(*args, **kwargs):
            raise AssertionError(f"unexpected external boundary: {args!r} {kwargs!r}")

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "entries.txt"
            input_path.write_text(
                "1. Add 7.0 hours/8 (2023/04/14) #80661 Task title\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                result = redmine.main(
                    ["--dry-run", "--file", str(input_path)],
                    credential_path=Path(directory) / "missing-credentials.json",
                    request_get=forbidden,
                    request_post=forbidden,
                    input_fn=forbidden,
                )

        self.assertEqual(result, 0)
        self.assertIn("Dry run — nenhum dado enviado.", output.getvalue())

    def test_normal_run_looks_up_title_and_posts_exact_payload_after_confirmation(self):
        gets = []
        posts = []
        prompts = []

        def request_get(url, headers):
            gets.append((url, headers))
            return Response(subject="Task title")

        def request_post(url, headers, data):
            posts.append((url, headers, json.loads(data)))
            return Response(status_code=201, text="created")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "entries.txt"
            input_path.write_text(
                "1. Add 7.0 hours/8 (2023/04/14) #80661 Task title\n",
                encoding="utf-8",
            )
            credentials = root / "credentials.json"
            credentials.write_text(
                json.dumps({"url": "https://redmine.test", "key": "secret"}),
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                result = redmine.main(
                    ["--file", str(input_path)],
                    credential_path=credentials,
                    request_get=request_get,
                    request_post=request_post,
                    input_fn=lambda prompt: prompts.append(prompt),
                )

        headers = {
            "Content-Type": "application/json",
            "X-Redmine-API-Key": "secret",
        }
        self.assertEqual(result, 0)
        self.assertEqual(gets, [("https://redmine.test/issues/80661.json", headers)])
        self.assertEqual(
            posts,
            [
                (
                    "https://redmine.test/time_entries.json",
                    headers,
                    {
                        "time_entry": {
                            "issue_id": 80661,
                            "hours": 7.0,
                            "spent_on": "2023-04-14",
                            "activity_id": "8",
                        }
                    },
                )
            ],
        )
        self.assertEqual(prompts, ["Press enter to send data..."] * 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
