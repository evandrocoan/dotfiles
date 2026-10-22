"""Exercise sampling with a kernel boundary fixture and the real persisted history."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

SOURCE = Path(os.environ.get('PROCESS_SWAP_SCRIPT', Path(__file__).with_name('process_swap_history.py')))
spec = importlib.util.spec_from_file_location('process_swap_history_tested', SOURCE)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def frame(stamp, activity=(), **coverage):
    return dict(boot='boot-one', bucket=stamp, start=stamp - 10, end=stamp, elapsed=10,
                activity=list(activity), coverage=dict(scanned=1, measured=1, baselines=0,
                errors=0, gone=0, truncated=0, resets=0, accounting_at_boot=True, **coverage))


def process(pid=123, start=100, name='sample-app', delay_ns=100000000, swap=1024):
    return dict(pid=pid, start=start, name=name, delay_ns=delay_ns, rss=4096, swap=swap)


class ProcessSwapHistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'history.sqlite3'
        self.proc = self.root / 'proc'
        self.proc.mkdir()
        self.reader = Mock()
        self.reader.get.return_value = 1000000
        self.sampler = monitor.Sampler(self.reader, self.proc)

    def proc_entry(self, pid=123, start=100, name='sample-app', swap=1000):
        directory = self.proc / str(pid)
        directory.mkdir(exist_ok=True)
        fields = ['S'] + ['0'] * 18 + [str(start)] + ['0'] * 30
        (directory / 'stat').write_text(f'{pid} ({name}) ' + ' '.join(fields))
        (directory / 'status').write_text(f'VmRSS:\t100 kB\nVmSwap:\t{swap} kB\n')
        return directory

    def sample(self, wall, mono=None, boot='boot-one'):
        return self.sampler.sample(wall, wall if mono is None else mono, boot, True)

    def history(self, **kwargs):
        writer = monitor.History(self.path, **kwargs)
        self.addCleanup(writer.close)
        return writer

    def test_only_measured_positive_wait_is_activity_not_occupied_swap(self):
        self.proc_entry(swap=900000)
        first = self.sample(1000)
        self.assertEqual(first['activity'], [])
        self.assertEqual(first['coverage']['baselines'], 1)
        second = self.sample(1010)
        self.assertEqual(second['activity'], [])
        self.assertEqual(second['coverage']['measured'], 1)
        self.reader.get.return_value += 200000000
        third = self.sample(1020)
        self.assertEqual([(p['pid'], p['name'], p['delay_ns']) for p in third['activity']],
                         [(123, 'sample-app', 200000000)])
        self.assertEqual(third['activity'][0]['swap'], 900000 * 1024)

    def test_pid_reuse_exec_and_counter_reset_are_new_baselines(self):
        self.proc_entry(name='odd (name)')
        self.sample(1000)
        for stamp, start, name, wait in ((1010, 200, 'odd (name)', 90000000),
                                        (1020, 200, 'new-app', 100000000),
                                        (1030, 200, 'new-app', 1)):
            self.proc_entry(start=start, name=name)
            self.reader.get.return_value = wait
            result = self.sample(stamp)
            self.assertEqual(result['activity'], [])
            self.assertEqual(result['coverage']['measured'], 0)
        self.assertEqual(result['coverage']['resets'], 1)

    def test_reboot_clock_jump_and_long_gap_do_not_invent_deltas(self):
        self.proc_entry()
        self.sample(1000)
        for stamp, mono, boot in ((1010, 1010, 'boot-two'), (1200, 1020, 'boot-two'),
                                   (1300, 1120, 'boot-two')):
            self.reader.get.return_value += 100000000
            result = self.sample(stamp, mono, boot)
            self.assertEqual(result['activity'], [])
            self.assertEqual(result['elapsed'], 0)

    def test_exit_churn_invalid_counter_and_truncation_are_explicit(self):
        directory = self.proc_entry()
        self.sample(1000)
        shutil.rmtree(directory)
        self.assertGreater(self.sample(1010)['coverage']['gone'], 0)
        self.proc_entry()
        self.reader.get.side_effect = ProcessLookupError('exited')
        self.assertGreater(self.sample(1020)['coverage']['gone'], 0)
        self.reader.get.side_effect = None
        self.reader.get.return_value = -1
        self.assertEqual(self.sample(1030)['coverage']['errors'], 1)
        self.sampler.max_processes = 0
        self.assertEqual(self.sample(1040)['coverage']['truncated'], 1)

    def test_permission_denial_is_source_failure(self):
        self.proc_entry()
        self.reader.get.side_effect = PermissionError('not authorized')
        with self.assertRaises(PermissionError):
            self.sample(1000)

    def test_process_changed_during_query_is_rejected(self):
        self.proc_entry()
        def changed(_):
            self.proc_entry(start=200)
            return 900000000
        self.sample(1000)
        self.reader.get.side_effect = changed
        result = self.sample(1010)
        self.assertEqual(result['activity'], [])
        self.assertEqual(result['coverage']['resets'] + result['coverage']['baselines'], 1)

    def test_saved_pid_query_survives_process_exit_and_writer_restart(self):
        self.proc_entry()
        first = self.sample(1000)
        writer = monitor.History(self.path)
        writer.record(first)
        self.reader.get.return_value += 250000000
        writer.record(self.sample(1010))
        writer.close()
        shutil.rmtree(self.proc)
        reader = monitor.query_history(self.path, 1010, 'boot-one', pid=123)
        self.assertEqual(reader['processes'][0]['swap_in_wait_seconds'], .25)
        self.assertEqual(reader['processes'][0]['pid'], 123)
        reopened = monitor.History(self.path)
        reopened.close()
        command = subprocess.run([sys.executable, str(SOURCE), 'query', '--database', str(self.path),
                                  '--before', '1010', '--boot-id', 'boot-one', '--pid', '123'],
                                 capture_output=True, text=True, timeout=5)
        self.assertEqual(command.returncode, 0, command.stderr)
        self.assertEqual(json.loads(command.stdout)['processes'], reader['processes'])
        self.assertEqual(monitor.query_history(self.path, 1010, 'other-boot')['status'], 'unavailable')
        self.assertEqual(monitor.query_history(self.path, 1010, 'boot-one', pid=999)['processes'], [])

    def test_complete_healthy_zero_is_distinct_from_missing_or_partial(self):
        writer = self.history()
        for stamp in range(1010, 1130, 10):
            writer.record(frame(stamp))
        result = monitor.query_history(self.path, 1120, 'boot-one')
        self.assertEqual((result['status'], result['processes'], result['frames']), ('measured', [], 12))
        for column, value in (('errors', 1), ('truncated', 1), ('measured', 0), ('accounting_at_boot', False)):
            original = frame(1010)['coverage']
            original[column] = value
            writer.db.execute('UPDATE frames SET coverage=? WHERE bucket=1010', (json.dumps(original),))
            writer.db.commit()
            self.assertEqual(monitor.query_history(self.path, 1120, 'boot-one')['status'], 'partial', column)
        writer.db.execute('DELETE FROM frames WHERE bucket=1010')
        writer.db.commit()
        self.assertEqual(monitor.query_history(self.path, 1120, 'boot-one')['status'], 'partial')
        self.assertEqual(monitor.query_history(self.root / 'missing', 1120, 'boot-one')['status'], 'unavailable')

    def test_readonly_directory_after_clean_shutdown_and_busy_reader(self):
        writer = monitor.History(self.path)
        writer.record(frame(1010, [process()]))
        writer.close()
        self.root.chmod(0o555)
        self.addCleanup(self.root.chmod, 0o700)
        result = monitor.query_history(self.path, 1010, 'boot-one')
        self.assertEqual(result['processes'][0]['pid'], 123)
        with sqlite3.connect(self.path) as blocker:
            blocker.execute('BEGIN EXCLUSIVE')
            result = monitor.query_history(self.path, 1010, 'boot-one')
            self.assertEqual(result['status'], 'unavailable')
            self.assertIn('locked', result['error'])
        self.assertEqual(monitor.query_history(self.path, 1010, 'boot-one')['processes'][0]['pid'], 123)

    def test_reader_sees_committed_history_during_pending_write(self):
        writer = self.history()
        writer.record(frame(1010, [process()]))
        writer.db.execute('BEGIN IMMEDIATE')
        writer.db.execute('DELETE FROM activity')
        result = monitor.query_history(self.path, 1010, 'boot-one')
        self.assertEqual(result['processes'][0]['pid'], 123)
        writer.db.rollback()

    def test_cross_boundary_intervals_cannot_attribute_activity_to_window(self):
        writer = self.history()
        early = frame(1010, [process(pid=77, name='before-window')])
        early.update(start=990, elapsed=20)
        writer.record(early)
        for stamp in range(1020, 1130, 10):
            writer.record(frame(stamp, [process(pid=88, name='inside-window')]))
        result = monitor.query_history(self.path, 1120, 'boot-one')
        self.assertEqual(result['frames'], 12)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['excluded_intervals'], 1)
        self.assertEqual([p['pid'] for p in result['processes']], [88])
        late = frame(1120, [process(pid=99, name='after-window')])
        late.update(end=1120.01)
        writer.record(late)
        result = monitor.query_history(self.path, 1120, 'boot-one')
        self.assertNotIn(99, [p['pid'] for p in result['processes']])

    def test_default_storage_budget_includes_peak_expiration_journal(self):
        writer = self.history()
        peak = 0
        def observe(*_):
            nonlocal peak
            peak = max(peak, sum(p.stat().st_size for p in self.root.glob('history.sqlite3*')))
            return 0
        writer.db.set_progress_handler(observe, 10000)
        writer.db.set_trace_callback(observe)
        activity = [process(pid=i+1, name='activity-' + 'x' * 32) for i in range(2000)]
        stamp = 1000
        while writer.db.execute('PRAGMA page_count').fetchone()[0] < writer.page_limit * .75:
            writer.record(frame(stamp, activity))
            stamp += 10
            self.assertLess(stamp, 10000, 'fixture did not fill its database budget')
        before = writer.db.execute('SELECT count(*) FROM activity').fetchone()[0]
        self.assertGreater(before, 100000)
        writer.record(frame(stamp + writer.retention + 10))
        observe()
        self.assertEqual(writer.db.execute('SELECT count(*) FROM activity').fetchone()[0], 0)
        self.assertLess(peak, 64 * monitor.MIB)
        self.assertLess(sum(p.stat().st_size for p in self.root.glob('history.sqlite3*')), 64 * monitor.MIB)

    def test_top_three_keep_start_identity_and_do_not_rank_by_swap_occupancy(self):
        writer = self.history()
        activity = [process(1, 100, 'a', 100000000, 100000000),
                    process(1, 200, 'b', 300000000, 1), process(2, 100, '<c&>', 400000000, 0),
                    process(3, 100, 'd', 200000000, 0)]
        writer.record(frame(1010, [activity[0]]))
        writer.record(frame(1020, activity[1:]))
        result = monitor.query_history(self.path, 1020, 'boot-one')
        self.assertEqual([(p['pid'], p['start_ticks']) for p in result['processes']],
                         [(2, 100), (1, 200), (3, 100)])

    def test_retention_cascades_and_storage_budget_stays_bounded(self):
        writer = self.history(max_bytes=8 * monitor.MIB, retention_seconds=120)
        for stamp in range(1000, 1300, 10):
            writer.record(frame(stamp, [process()]))
        self.assertGreaterEqual(writer.db.execute('SELECT min(ended) FROM frames').fetchone()[0], 1170)
        self.assertEqual(writer.db.execute('PRAGMA foreign_key_check').fetchall(), [])
        writer.retention = 30 * 86400
        activity = [process(pid=i + 1, name='x' * 64) for i in range(1000)]
        for stamp in range(1300, 2300, 10):
            writer.record(frame(stamp, activity))
        self.assertLess(sum(p.stat().st_size for p in self.root.glob('history.sqlite3*')), 8 * monitor.MIB)
        self.assertLess(writer.db.execute('SELECT count(*) FROM frames').fetchone()[0], 100)
        self.assertTrue(monitor.query_history(self.path, 2290, 'boot-one')['processes'])

    def test_unsafe_writer_path_and_unsupported_schema_fail_explicitly(self):
        self.root.chmod(0o777)
        with self.assertRaises(ValueError):
            monitor.History(self.path)
        self.root.chmod(0o700)
        self.path.symlink_to(self.root / 'elsewhere')
        with self.assertRaises(ValueError):
            monitor.History(self.path)
        self.path.unlink()
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA user_version=99')
        self.assertEqual(monitor.query_history(self.path, 1000, 'boot-one')['status'], 'unavailable')

    def test_mismatched_kernel_reply_is_not_associated_with_requested_pid(self):
        reader = monitor.KernelReader.__new__(monitor.KernelReader)
        reader.client = Mock(family_id=30)
        reader.attribute = Mock()
        reader.flags = 1
        reader.message = Mock()
        reader.message.recv.return_value.family = 30
        reader.message.recv.return_value.attrs = {5: Mock()}
        reader.message.recv.return_value.attrs[5].nested.return_value = {2: Mock()}
        reader.message.recv.return_value.attrs[5].nested.return_value[2].u32.return_value = 999
        reader.stats = Mock()
        # Reopening the external connection is the only additional substituted boundary.
        original = monitor.KernelReader.__init__
        monitor.KernelReader.__init__ = Mock()
        try:
            with self.assertRaisesRegex(ValueError, 'different process'):
                reader.get(123)
        finally:
            monitor.KernelReader.__init__ = original
        reader.stats.assert_not_called()
        reader.client.connection.descriptor.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
