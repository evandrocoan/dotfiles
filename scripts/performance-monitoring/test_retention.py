"""Deletion-policy tests use disposable directories, never the live history."""

from pathlib import Path
import tempfile
import unittest

from retain_atop_logs import open_logs, prune


class RetentionTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.days = [self.directory / ("atop_2026010" + str(n)) for n in range(1, 5)]
        for day in self.days:
            day.write_bytes(b"x" * 10)

    def test_removes_oldest_until_budget(self):
        result = prune(self.directory, 25, set(), "20260104")
        self.assertEqual(result["removed"], ["atop_20260101", "atop_20260102"])
        self.assertEqual(sorted(self.directory.iterdir()), self.days[2:])
        self.assertEqual(result["bytes_after"], 20)
        self.assertFalse(result["protected_data_exceeds_budget"])

    def test_protects_open_and_current_logs_even_over_budget(self):
        result = prune(self.directory, 0, {self.days[0]}, "20260104")
        self.assertEqual(sorted(self.directory.iterdir()), [self.days[0], self.days[3]])
        self.assertEqual(result["bytes_after"], 20)
        self.assertTrue(result["protected_data_exceeds_budget"])

    def test_leaves_unrelated_files_and_symlinks_untouched(self):
        unrelated = self.directory / "notes.txt"
        unrelated.write_bytes(b"keep")
        alias = self.directory / "atop_20251231"
        alias.symlink_to(unrelated)
        prune(self.directory, 0, set(), "20260104")
        self.assertTrue(alias.is_symlink())
        self.assertEqual(unrelated.read_bytes(), b"keep")

    def test_detects_a_real_open_reader(self):
        with self.days[0].open("rb"):
            self.assertIn(self.days[0], open_logs(self.directory))

    def test_within_budget_is_idempotent(self):
        for _ in range(2):
            result = prune(self.directory, 40, set(), "20260104")
            self.assertEqual(result["removed"], [])
            self.assertEqual(result["bytes_after"], 40)
        self.assertEqual(sorted(self.directory.iterdir()), self.days)


if __name__ == "__main__":
    unittest.main(verbosity=2)
