"""Exercise kernel-handler decisions and real file I/O in a disposable filesystem."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import contextlib
import errno
import importlib.util
import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


SCRIPT = Path(os.environ.get("CORE_DUMP_FILTER_SCRIPT",
                            Path(__file__).resolve().parent / "core_dump_filter.py"))
SPEC = importlib.util.spec_from_file_location("core_dump_filter", SCRIPT)
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)
ALERT_SPEC = importlib.util.spec_from_file_location(
    "core_dump_filter_alert", Path(__file__).resolve().parents[1] / "core_dump_alert.py")
alert = importlib.util.module_from_spec(ALERT_SPEC)
ALERT_SPEC.loader.exec_module(alert)


class UnreadableInput:
    def read(self, size):
        raise AssertionError("an excluded core must not be read")


class CoreDumpFilterTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.owner = (os.getuid(), os.getgid())
        self.rules = self.root / "etc/core-dump-filter/ignore.conf"
        self.rules.parent.mkdir(parents=True)
        (self.root / "etc").chmod(0o755)
        self.rules.parent.chmod(0o755)
        self.rules.write_text("# exact names\nxfce4-panel\npanel-5-pulseau\npanel-8-systray\n")
        self.rules.chmod(0o644)
        self.cores = self.root / "root/coredumps"
        self.cores.mkdir(parents=True)
        self.cores.parent.chmod(0o700)
        self.cores.chmod(0o1733)
        self.event = collector.parse_event(
            ["6", str(self.owner[0]), str(self.owner[1]), "321", "1793809787",
             str(2**64 - 1), "example"])
        self.expected = f"core-example-6-{self.owner[0]}-{self.owner[1]}-321-1793809787"
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(collector.syslog, "syslog").start()
        mock.patch.object(collector.syslog, "openlog").start()

    def collect(self, payload=b"core payload", event=None):
        return collector.collect(event or self.event, io.BytesIO(payload),
                                 root=self.root, owner=self.owner)

    def main(self, arguments, payload=b"core payload"):
        output, errors = io.StringIO(), io.StringIO()
        with (mock.patch.object(collector, "ROOT", self.root),
              mock.patch.object(collector, "OWNER", self.owner),
              mock.patch.object(collector.os, "geteuid", return_value=0),
              mock.patch.object(collector.sys, "stdin", io.TextIOWrapper(io.BytesIO(payload))),
              contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors)):
            status = collector.main(arguments)
        return status, output.getvalue(), errors.getvalue()

    def test_allowed_core_preserves_payload_identity_and_private_permissions(self):
        result = self.collect(b"\x7fELF\0private memory")
        self.assertEqual(result, {"status": "saved", "name": self.expected, "size": 19})
        path = self.cores / self.expected
        self.assertEqual(path.read_bytes(), b"\x7fELF\0private memory")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual((path.stat().st_uid, path.stat().st_gid), self.owner)
        self.assertEqual(sorted(p.name for p in self.cores.iterdir()), [self.expected])

    def test_each_requested_exclusion_does_not_read_or_create_a_file(self):
        for name in ("xfce4-panel", "panel-5-pulseau", "panel-8-systray"):
            with self.subTest(name=name):
                result = collector.collect(self.event._replace(comm=name), UnreadableInput(),
                                           root=self.root, owner=self.owner)
                self.assertEqual(result, {"status": "ignored", "name": None, "size": 0})
                self.assertEqual(list(self.cores.iterdir()), [])

    def test_names_are_exact_not_prefix_or_executable_matches(self):
        for name in ("xfce4-panel-x", "panel-6-pulseau", "panel-8-systrayx", "wrapper-2.0"):
            with self.subTest(name=name):
                result = self.collect(event=self.event._replace(comm=name))
                self.assertEqual(result["status"], "saved")
                self.assertEqual((self.cores / result["name"]).read_bytes(), b"core payload")

    def test_original_zero_limit_never_reads_input_even_with_missing_config(self):
        self.rules.unlink()
        result = collector.collect(self.event._replace(limit=0), UnreadableInput(),
                                   root=self.root, owner=self.owner)
        self.assertEqual(result, {"status": "disabled", "name": None, "size": 0})
        self.assertEqual(list(self.cores.iterdir()), [])

    def test_limit_minus_one_exact_and_plus_one(self):
        for payload, status, suffix in ((b"abcd", "saved", ""),
                                        (b"abcde", "saved", ""),
                                        (b"abcdef", "partial", ".partial")):
            with self.subTest(payload=payload):
                result = self.collect(payload, self.event._replace(limit=5))
                self.assertEqual(result["status"], status)
                self.assertEqual((self.cores / result["name"]).read_bytes(), payload[:5])
                self.assertEqual(result["size"], min(len(payload), 5))
                self.assertEqual(result["name"].endswith(".partial"), bool(suffix))

    def test_zero_blocks_and_trailing_holes_preserve_content_and_logical_size(self):
        chunk = collector.CHUNK_SIZE
        payload = b"A" * chunk + b"\0" * (2 * chunk) + b"B" * chunk + b"\0" * chunk
        result = self.collect(payload)
        path = self.cores / result["name"]
        self.assertEqual(path.read_bytes(), payload)
        self.assertEqual(path.stat().st_size, len(payload))
        self.assertLess(path.stat().st_blocks * 512, len(payload))

    def test_unsafe_comm_bytes_cannot_escape_the_directory(self):
        result = self.collect(event=self.event._replace(comm="../../x\n name"))
        self.assertEqual(result["name"],
                         f"core-..%2F..%2Fx%0A%20name-6-{self.owner[0]}-{self.owner[1]}-321-1793809787")
        self.assertEqual((self.cores / result["name"]).read_bytes(), b"core payload")
        self.assertFalse((self.root / "x\n name").exists())

    def test_existing_file_and_symlink_are_never_overwritten(self):
        target = self.root / "unrelated"
        target.write_bytes(b"keep unrelated")
        (self.cores / self.expected).symlink_to(target)
        first = self.collect(b"first")
        second = self.collect(b"second")
        self.assertNotEqual(first["name"], second["name"])
        self.assertNotEqual(first["name"], self.expected)
        self.assertEqual(target.read_bytes(), b"keep unrelated")
        self.assertTrue((self.cores / self.expected).is_symlink())
        self.assertEqual((self.cores / first["name"]).read_bytes(), b"first")
        self.assertEqual((self.cores / second["name"]).read_bytes(), b"second")

    def test_temporary_name_collision_does_not_touch_existing_data(self):
        path = self.cores / ".core-dump-filter-fixed"
        path.write_bytes(b"existing private data")
        with mock.patch.object(collector.secrets, "token_hex", return_value="fixed"):
            with self.assertRaisesRegex(collector.CaptureError, "no output file was created"):
                self.collect()
        self.assertEqual(path.read_bytes(), b"existing private data")
        self.assertEqual(list(self.cores.iterdir()), [path])

    def test_parallel_same_identity_captures_are_distinct_and_complete(self):
        barrier = threading.Barrier(2)

        class SynchronizedInput(io.BytesIO):
            def read(self, size):
                if self.tell() == 0:
                    barrier.wait(timeout=5)
                return super().read(size)

        def capture(payload):
            return collector.collect(self.event, SynchronizedInput(payload),
                                     root=self.root, owner=self.owner)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(capture, (b"first core", b"second core")))
        self.assertEqual(len({result["name"] for result in results}), 2)
        self.assertEqual(sorted(path.read_bytes() for path in self.cores.iterdir()),
                         [b"first core", b"second core"])
        self.assertEqual([result["status"] for result in results], ["saved", "saved"])

    def test_short_writes_are_completed(self):
        write = os.write
        with mock.patch.object(collector.os, "write", side_effect=lambda fd, data: write(fd, data[:3])):
            result = self.collect(b"payload requiring repeated writes")
        self.assertEqual((self.cores / result["name"]).read_bytes(), b"payload requiring repeated writes")
        self.assertEqual(result["status"], "saved")

    def test_read_failure_retains_the_written_prefix(self):
        class FailedInput(io.BytesIO):
            def read(self, size):
                if self.tell():
                    raise OSError(errno.EIO, "fixture read failed")
                return super().read(size)

        with self.assertRaisesRegex(collector.CaptureError, "fixture read failed.*retained core-"):
            collector.collect(self.event, FailedInput(b"written prefix"), root=self.root, owner=self.owner)
        self.assertEqual((self.cores / (self.expected + ".partial")).read_bytes(), b"written prefix")

    def test_failed_stream_preserves_a_trailing_sparse_hole(self):
        class FailedInput(io.BytesIO):
            def read(self, size):
                if self.tell():
                    raise OSError(errno.EIO, "fixture read failed after hole")
                return super().read(size)

        payload = b"\0" * collector.CHUNK_SIZE
        with self.assertRaisesRegex(collector.CaptureError, "fixture read failed after hole"):
            collector.collect(self.event, FailedInput(payload), root=self.root, owner=self.owner)
        self.assertEqual((self.cores / (self.expected + ".partial")).read_bytes(), payload)

    def test_write_failure_retains_only_successfully_written_bytes(self):
        write = os.write
        calls = 0

        def fail_after_prefix(fd, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                return write(fd, data[:3])
            raise OSError(errno.ENOSPC, "fixture disk full")

        with mock.patch.object(collector.os, "write", side_effect=fail_after_prefix):
            with self.assertRaisesRegex(collector.CaptureError, "fixture disk full.*retained core-"):
                self.collect(b"abcdef")
        self.assertEqual((self.cores / (self.expected + ".partial")).read_bytes(), b"abc")

    def test_fsync_failure_retains_data_as_partial(self):
        with mock.patch.object(collector.os, "fsync", side_effect=OSError(errno.EIO, "fixture fsync failed")):
            with self.assertRaisesRegex(collector.CaptureError, "fixture fsync failed.*retained core-"):
                self.collect()
        self.assertEqual((self.cores / (self.expected + ".partial")).read_bytes(), b"core payload")

    def test_publication_failure_retains_hidden_private_input(self):
        with mock.patch.object(collector.os, "link", side_effect=OSError(errno.EIO, "fixture link failed")):
            with self.assertRaisesRegex(collector.CaptureError, "retained .core-dump-filter-"):
                self.collect()
        paths = list(self.cores.iterdir())
        self.assertEqual(len(paths), 1)
        self.assertTrue(paths[0].name.startswith(".core-dump-filter-"))
        self.assertEqual(paths[0].read_bytes(), b"core payload")
        self.assertEqual(stat.S_IMODE(paths[0].stat().st_mode), 0o600)

    def test_directory_sync_failure_does_not_remove_published_core(self):
        fsync = os.fsync

        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError(errno.EIO, "fixture directory fsync failed")
            return fsync(fd)

        with mock.patch.object(collector.os, "fsync", side_effect=fail_directory):
            with self.assertRaisesRegex(collector.CaptureError, "fixture directory fsync failed.*retained core-"):
                self.collect()
        self.assertEqual((self.cores / self.expected).read_bytes(), b"core payload")

    def test_missing_invalid_oversized_and_writable_rules_preserve_capture(self):
        variants = ((None, 0o644), ("x" * 16, 0o644), ("#" * 65537, 0o644),
                    ("example\n", 0o666), (b"\xff", 0o644))
        for content, mode in variants:
            with self.subTest(content=repr(content)[:30], mode=mode):
                self.rules.unlink(missing_ok=True)
                if content is not None:
                    self.rules.write_bytes(content if isinstance(content, bytes) else content.encode())
                    self.rules.chmod(mode)
                with self.assertRaises((OSError, ValueError)):
                    collector.load_rules(root=self.root, owner=self.owner)
                result = self.collect()
                self.assertEqual(result["status"], "saved")
                self.assertEqual((self.cores / result["name"]).read_bytes(), b"core payload")

    def test_rule_file_symlink_is_rejected_without_following_it(self):
        outside = self.root / "outside-ignore"
        outside.write_text("example\n")
        self.rules.unlink()
        self.rules.symlink_to(outside)
        with self.assertRaises(OSError):
            collector.load_rules(root=self.root, owner=self.owner)
        result = self.collect()
        self.assertEqual(result["status"], "saved")
        self.assertEqual(outside.read_text(), "example\n")

    def test_fifo_configuration_is_rejected_without_waiting_for_a_writer(self):
        self.rules.unlink()
        os.mkfifo(self.rules, 0o600)
        program = (
            "import runpy; from pathlib import Path; "
            f"m=runpy.run_path({str(SCRIPT)!r}); "
            f"m['load_rules'](root=Path({str(self.root)!r}), owner={self.owner!r})")
        result = subprocess.run([sys.executable, "-I", "-c", program], capture_output=True,
                                text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trusted regular file", result.stderr)
        self.assertEqual(list(self.cores.iterdir()), [])

    def test_writable_configuration_parent_is_rejected(self):
        self.rules.parent.chmod(0o777)
        with self.assertRaisesRegex(ValueError, "must not be writable"):
            collector.load_rules(root=self.root, owner=self.owner)
        self.assertEqual(self.collect()["status"], "saved")

    def test_writable_configuration_ancestor_is_rejected(self):
        (self.root / "etc").chmod(0o777)
        with self.assertRaisesRegex(ValueError, "must not be writable"):
            collector.load_rules(root=self.root, owner=self.owner)
        self.assertEqual(self.collect()["status"], "saved")

    def test_symlink_configuration_parent_is_not_followed(self):
        original = self.rules.parent
        moved = original.with_name("moved")
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(OSError):
            collector.load_rules(root=self.root, owner=self.owner)
        self.assertEqual(self.collect()["status"], "saved")

    def test_untrusted_rule_file_owner_or_group_is_rejected(self):
        fstat = os.fstat
        inode = self.rules.stat().st_ino
        for index in (4, 5):
            with self.subTest(stat_field=index):
                def wrong_identity(fd):
                    metadata = fstat(fd)
                    if metadata.st_ino == inode:
                        values = list(metadata)
                        values[index] += 1
                        return os.stat_result(values)
                    return metadata

                with mock.patch.object(collector.os, "fstat", side_effect=wrong_identity):
                    with self.assertRaisesRegex(ValueError, "trusted regular file"):
                        collector.load_rules(root=self.root, owner=self.owner)

    def test_output_denials_do_not_create_files(self):
        for mode, diagnostic in ((0o777, "must not be writable"),
                                  (0o1755, "must not be readable")):
            with self.subTest(mode=mode):
                self.cores.chmod(mode)
                with self.assertRaisesRegex(ValueError, diagnostic):
                    self.collect()
                self.assertEqual(list(self.cores.iterdir()), [])
        self.cores.chmod(0o1733)
        self.cores.parent.chmod(0o777)
        with self.assertRaisesRegex(ValueError, "must not be writable"):
            self.collect()
        self.assertEqual(list(self.cores.iterdir()), [])

    def test_output_group_must_match_even_with_setgid(self):
        self.cores.chmod(0o3733)
        fstat = os.fstat
        inode = self.cores.stat().st_ino

        def wrong_group(fd):
            metadata = fstat(fd)
            if metadata.st_ino == inode:
                values = list(metadata)
                values[5] += 1
                return os.stat_result(values)
            return metadata

        with mock.patch.object(collector.os, "fstat", side_effect=wrong_group):
            with self.assertRaisesRegex(ValueError, "trusted uid and gid"):
                self.collect()
        self.assertEqual(list(self.cores.iterdir()), [])

    def test_output_symlink_is_rejected_and_target_is_untouched(self):
        outside = self.root / "outside"
        outside.mkdir(mode=0o700)
        self.cores.rmdir()
        self.cores.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            self.collect()
        self.assertEqual(list(outside.iterdir()), [])

    def test_main_check_does_not_read_payload_or_write_files(self):
        status, output, errors = self.main(["--check"])
        self.assertEqual(status, 0, errors)
        self.assertIn("Configuration OK", output)
        self.assertEqual(errors, "")
        self.assertEqual(list(self.cores.iterdir()), [])
        self.rules.chmod(0o666)
        status, output, errors = self.main(["--check"])
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("capture failed", errors)

    def test_kernel_template_drives_main_with_literal_comm_after_separator(self):
        template = (Path(__file__).resolve().parent / "filter.sysctl.conf").read_text()
        pattern = next(line.split("=", 1)[1] for line in template.splitlines()
                       if line.startswith("kernel.core_pattern="))
        self.assertLessEqual(len(pattern.encode()), 127)
        values = {"%s": "6", "%u": str(self.owner[0]), "%g": str(self.owner[1]),
                  "%P": "321", "%t": "1793809787", "%c": str(2**64 - 1), "%e": "--check"}
        arguments = [values.get(word, word) for word in pattern.split()[3:]]
        status, output, errors = self.main(arguments, b"kernel stream fixture")
        self.assertEqual(status, 0, errors)
        self.assertEqual(output, "")
        path = self.cores / f"core---check-6-{self.owner[0]}-{self.owner[1]}-321-1793809787"
        self.assertEqual(path.read_bytes(), b"kernel stream fixture")

    def test_logging_failure_cannot_discard_a_completed_core(self):
        class FailedStderr:
            def write(self, message):
                raise OSError(errno.EIO, "fixture stderr closed")

        arguments = [str(value) for value in self.event[:-1]] + ["--", self.event.comm]
        with (mock.patch.object(collector, "ROOT", self.root),
              mock.patch.object(collector, "OWNER", self.owner),
              mock.patch.object(collector.os, "geteuid", return_value=0),
              mock.patch.object(collector.sys, "stdin", io.TextIOWrapper(io.BytesIO(b"retained"))),
              mock.patch.object(collector.sys, "stderr", FailedStderr()),
              mock.patch.object(collector.syslog, "syslog", side_effect=OSError("fixture syslog down"))):
            self.assertEqual(collector.main(arguments), 0)
        self.assertEqual((self.cores / self.expected).read_bytes(), b"retained")

    def test_invalid_metadata_is_rejected_before_capture(self):
        original = [str(value) for value in self.event[:-1]] + [self.event.comm]
        for position, value in ((0, "-1"), (1, "../../x"), (2, str(2**32)),
                                (3, "0"), (4, "1\n2"), (5, str(2**64)), (6, "x" * 16)):
            with self.subTest(position=position, value=value):
                arguments = original.copy()
                arguments[position] = value
                with self.assertRaises(ValueError):
                    collector.parse_event(arguments)
        self.assertEqual(list(self.cores.iterdir()), [])

    def test_main_rejects_unprivileged_capture_without_reading(self):
        with (mock.patch.object(collector.os, "geteuid", return_value=1000),
              contextlib.redirect_stderr(io.StringIO()) as errors):
            self.assertEqual(collector.main(["--check"]), 1)
        self.assertIn("run the installed collector as root", errors.getvalue())
        self.assertEqual(list(self.cores.iterdir()), [])

    def test_publisher_recognizes_completed_and_partial_cores_only(self):
        self.collect(b"complete")
        self.collect(b"too large", self.event._replace(limit=3))
        (self.cores / ".core-dump-filter-interrupted").write_bytes(b"unpublished")
        boot = self.root / "boot-id"
        boot.write_text("fixture-boot")
        snapshot = self.root / "public/status.json"
        result = alert.publish(argparse.Namespace(directory=self.cores, snapshot=snapshot, boot_id=boot))
        self.assertEqual(result, {"status": "published", "count": 2})
        self.assertNotIn("complete", snapshot.read_text())
        self.assertNotIn("example", snapshot.read_text())


if __name__ == "__main__":
    unittest.main()
