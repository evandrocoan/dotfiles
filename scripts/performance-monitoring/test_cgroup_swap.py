"""Swap collection uses kernel counters, real paths and the Netdata plugin entrypoint."""
from importlib.machinery import SourceFileLoader
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(os.environ.get("CGROUP_SWAP_SCRIPT", Path(__file__).with_name("cgroup_swap.plugin")))
loader = SourceFileLoader("cgroup_swap", str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
plugin = importlib.util.module_from_spec(spec)
loader.exec_module(plugin)


class SwapCollectorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cgroup = self.make("workload", 10, 20)
        self.collector = plugin.Collector(self.root, 10)

    def make(self, name, incoming, outgoing, populated=True):
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "memory.stat").write_text(f"anon 123\npswpin {incoming}\npswpout {outgoing}\n")
        (path / "cgroup.procs").write_text("42\n" if populated else "")
        return path

    def emit(self, now):
        stream = io.StringIO()
        self.collector.emit(now, stream)
        return stream.getvalue()

    def test_baseline_then_correct_real_page_units_both_directions(self):
        initial = self.emit(10)
        self.assertIn("DIMENSION in in absolute 1 1000", initial)
        self.assertNotIn("SET in", initial)
        self.make("workload", 1290, 660)
        with patch.object(plugin.os, "sysconf", return_value=8192):
            output = self.emit(20)
        self.assertIn("SET in = 1024000", output)  # 1280 * 8192 / 10 = 1024 KiB/s.
        self.assertIn("SET out = 512000", output)
        self.assertIn("SET measured = 1", output)

    def test_counter_reset_and_long_gap_rebaseline(self):
        self.emit(10)
        self.make("workload", 1, 1)
        output = self.emit(20)
        self.assertNotIn("SET in", output)
        # An explicit empty collection stores null. Omitting BEGIN lets Netdata interpolate.
        self.assertRegex(output, r"BEGIN hostswap_cgroup\.[a-f0-9]+\nEND")
        self.make("workload", 99999, 99999)
        self.assertNotIn("SET in", self.emit(60))
        self.assertIn("SET in = 0", self.emit(70))

    def test_reused_path_identity_rebaselines_even_with_larger_counters(self):
        self.emit(10)
        self.cgroup.rename(self.root / "old")
        self.make("workload", 999999, 999999)
        groups, values, _, _ = self.collector.sample(20)
        key = next(k for k, v in groups.items() if v["label"] == "p" + b"/workload".hex())
        self.assertNotIn(key, values)

    def test_departure_obsoletes_chart_instead_of_false_zero(self):
        self.emit(10)
        (self.cgroup / "cgroup.procs").write_text("")
        output = self.emit(20)
        self.assertIn("10 obsolete", output)
        self.assertNotIn("SET in", output)

    def test_empty_intermediates_and_symlinks_are_not_collected(self):
        self.make("parent", 0, 0, populated=False)
        self.make("parent/child", 0, 0)
        (self.root / "alias").symlink_to(self.cgroup)
        groups, _, _, coverage = self.collector.sample(10)
        self.assertEqual({os.fsdecode(bytes.fromhex(v["label"][1:])) for v in groups.values()},
                         {"/workload", "/parent/child"})
        self.assertEqual(coverage["errors"], 0)

    def test_malformed_or_missing_counters_report_partial_coverage(self):
        (self.cgroup / "memory.stat").write_text("anon 1\n")
        groups, values, _, coverage = self.collector.sample(10)
        self.assertEqual(groups, {})
        self.assertEqual(values, {})
        self.assertEqual(coverage["errors"], 1)

    def test_permission_failure_is_explicit(self):
        original = Path.open
        def boundary(path, *args, **kwargs):
            if path.name == "cgroup.procs":
                raise PermissionError("denied")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", boundary):
            self.assertEqual(self.collector.sample(10)[3]["errors"], 1)

    def test_chart_and_directory_limits_report_truncation(self):
        for i in range(8):
            self.make(f"other{i}", 0, 0)
        limited = plugin.Collector(self.root, 10, max_groups=2, max_directories=5)
        groups, _, _, coverage = limited.sample(10)
        self.assertLessEqual(len(groups), 2)
        self.assertGreater(coverage["truncated"], 0)
        self.assertLessEqual(len(limited.previous), 2)

    def test_kernel_names_cannot_inject_protocol(self):
        self.make("quote'\"\\\n, <&>", 0, 0)
        output = self.emit(10)
        self.assertNotIn("quote", output)
        self.assertEqual(sum(line.startswith("CHART") for line in output.splitlines()), 2)

    def test_actual_entrypoint_emits_coverage_and_exits(self):
        result = subprocess.run(["/usr/bin/python3", str(SOURCE), "1", "--iterations", "1",
                                 "--root", str(self.root)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CHART hostswap.coverage", result.stdout)
        self.assertIn("CLABEL cgroup_path 'p2f776f726b6c6f6164' 1", result.stdout)
        self.assertIn("SET tracked = 1", result.stdout)
        self.assertNotIn("SET in", result.stdout)


if __name__ == "__main__":
    unittest.main()
