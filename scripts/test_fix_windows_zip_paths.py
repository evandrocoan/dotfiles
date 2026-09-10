"""Disposable-filesystem tests for the Windows ZIP path repair tool."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_script():
    spec = importlib.util.spec_from_file_location(
        "fix_windows_zip_paths", ROOT / ".local/bin/fix_windows_zip_paths.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


repair = load_script()


class PathRepairTests(unittest.TestCase):
    def test_import_does_not_rename_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "nested\\file.txt"
            source.write_text("content", encoding="utf-8")

            previous = Path.cwd()
            try:
                os.chdir(directory)
                load_script()
            finally:
                os.chdir(previous)

            self.assertTrue(source.exists())
            self.assertFalse((Path(directory) / "nested/file.txt").exists())

    def test_repairs_backslash_and_private_separator_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backslash = root / "one\\file.txt"
            private = root / "two\uf05cfile.txt"
            ordinary = root / "ordinary.txt"
            backslash.write_text("backslash", encoding="utf-8")
            private.write_text("private", encoding="utf-8")
            ordinary.write_text("ordinary", encoding="utf-8")

            moved = repair.repair_paths(root)

            self.assertEqual(
                {(source.name, target.relative_to(root).as_posix()) for source, target in moved},
                {
                    ("one\\file.txt", "one/file.txt"),
                    ("two\uf05cfile.txt", "two/file.txt"),
                },
            )
            self.assertEqual((root / "one/file.txt").read_text(), "backslash")
            self.assertEqual((root / "two/file.txt").read_text(), "private")
            self.assertEqual(ordinary.read_text(), "ordinary")

    def test_collision_preserves_both_source_and_existing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other_source = root / "other\\file.txt"
            source = root / "nested\\file.txt"
            target = root / "nested/file.txt"
            target.parent.mkdir()
            other_source.write_text("other", encoding="utf-8")
            source.write_text("source", encoding="utf-8")
            target.write_text("target", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                repair.repair_paths(root)

            self.assertEqual(other_source.read_text(), "other")
            self.assertFalse((root / "other/file.txt").exists())
            self.assertEqual(source.read_text(), "source")
            self.assertEqual(target.read_text(), "target")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "nested\\file.txt"
            target = root / "nested/file.txt"
            target.parent.mkdir()
            source.write_text("source", encoding="utf-8")
            target.symlink_to("missing-target")

            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                repair.repair_paths(root)

            self.assertEqual(source.read_text(), "source")
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.readlink(), Path("missing-target"))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other_source = root / "other\\file.txt"
            blocked_source = root / "blocked\\file.txt"
            blocked_parent = root / "blocked"
            other_source.write_text("other", encoding="utf-8")
            blocked_source.write_text("blocked-source", encoding="utf-8")
            blocked_parent.write_text("blocking-file", encoding="utf-8")

            with self.assertRaisesRegex(
                NotADirectoryError, "refusing target beneath non-directory path"
            ):
                repair.repair_paths(root)

            self.assertEqual(other_source.read_text(), "other")
            self.assertFalse((root / "other/file.txt").exists())
            self.assertEqual(blocked_source.read_text(), "blocked-source")
            self.assertEqual(blocked_parent.read_text(), "blocking-file")

    def test_rejects_lexical_and_symlink_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / f"outside-{root.name}.txt"
            self.assertFalse(outside.exists())
            source = root / f"..\\{outside.name}"
            source.write_text("source", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unsafe encoded path"):
                repair.repair_paths(root)

            self.assertEqual(source.read_text(), "source")
            self.assertFalse(outside.exists())

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "nested").symlink_to(outside, target_is_directory=True)
            source = root / "nested\\file.txt"
            source.write_text("source", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unsafe symlink in target path"):
                repair.repair_paths(root)

            self.assertEqual(source.read_text(), "source")
            self.assertFalse((outside / "file.txt").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
