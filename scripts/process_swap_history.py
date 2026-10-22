#!/usr/bin/python3
"""Record bounded per-process swap-in wait history and query saved intervals."""
import argparse
from contextlib import closing
import errno
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import sqlite3
import sys
import time
from urllib.parse import quote

DEFAULT_DATABASE = Path('/var/lib/process-swap-monitor/history.sqlite3')
MIB = 1024 * 1024


class KernelReader:
    """Use the installed iotop transport/decoder, with TGID aggregation by the kernel."""
    def __init__(self):
        from iotop.data import TaskStatsNetlink, Stats
        from iotop.genetlink import GeNlMessage
        from iotop.netlink import U32Attr, NLM_F_REQUEST
        self.client = TaskStatsNetlink(None)
        self.client.connection.descriptor.settimeout(.2)
        self.message, self.attribute, self.flags, self.stats = GeNlMessage, U32Attr, NLM_F_REQUEST, Stats

    def get(self, pid):
        # TASKSTATS_CMD_ATTR_TGID=2; TYPE_AGGR_TGID=5; TYPE_STATS=3 (linux/taskstats.h).
        request = self.message(self.client.family_id, cmd=1,
                               attrs=[self.attribute(2, pid)], flags=self.flags)
        try:
            request.send(self.client.connection)
            response = self.message.recv(self.client.connection)
            if response.family != self.client.family_id:
                raise ValueError('unexpected taskstats family')
            aggregate = response.attrs[5].nested()
            if aggregate[2].u32() != pid:
                raise ValueError('taskstats response belongs to a different process')
            raw = aggregate[3].data
            if len(raw) < 272:
                raise ValueError('short taskstats response')
            return self.stats(raw).swapin_delay_total
        except (OSError, ValueError, KeyError, AssertionError) as error:
            if isinstance(error, OSError) and error.errno == errno.ESRCH:
                raise ProcessLookupError('process exited during taskstats query') from error
            if isinstance(error, OSError) and error.errno in (errno.EPERM, errno.EACCES):
                raise PermissionError('TASKSTATS access denied') from error
            # Never associate a delayed response from a timed-out socket with another PID.
            self.close()
            self.__init__()
            raise

    def close(self):
        self.client.connection.descriptor.close()


def metadata(directory, memory_details=True):
    raw = (directory / 'stat').read_text()
    close = raw.rindex(')')
    fields = raw[close + 2:].split()
    memory = {}
    for line in ((directory / 'status').read_text().splitlines() if memory_details else ()):
        key, _, value = line.partition(':')
        if key in ('VmRSS', 'VmSwap'):
            memory[key] = int(value.split()[0]) * 1024
    if min(memory.values(), default=0) < 0:
        raise ValueError('negative process memory')
    return {'pid': int(directory.name), 'start': int(fields[19]),
            'name': raw[raw.index('(') + 1:close][:64],
            'rss': memory.get('VmRSS', 0), 'swap': memory.get('VmSwap', 0)}


class Sampler:
    def __init__(self, reader, proc=Path('/proc'), interval=10, max_processes=4096, budget=1):
        self.reader, self.proc, self.interval = reader, proc, interval
        self.max_processes, self.budget = max_processes, budget
        self.previous = {}
        self.last = None

    def sample(self, wall, monotonic, boot, accounting_at_boot):
        current, activity = {}, []
        coverage = dict(scanned=0, measured=0, baselines=0, errors=0, gone=0,
                        truncated=0, resets=0, accounting_at_boot=accounting_at_boot)
        elapsed = monotonic - self.last[1] if self.last else 0
        comparable = bool(self.last and self.last[2] == boot
                          and 0 < elapsed <= self.interval * 3
                          and abs((wall - self.last[0]) - elapsed) < 2)
        deadline = time.monotonic() + self.budget
        with os.scandir(self.proc) as entries:
            for entry in entries:
                if not entry.name.isdecimal() or not entry.is_dir(follow_symlinks=False):
                    continue
                if coverage['scanned'] >= self.max_processes or time.monotonic() >= deadline:
                    coverage['truncated'] = 1
                    break
                coverage['scanned'] += 1
                directory = Path(entry.path)
                try:
                    pid = int(entry.name)
                    wait = self.reader.get(pid)
                    if not isinstance(wait, int) or not 0 <= wait < 2 ** 64:
                        raise ValueError('invalid swap-in delay')
                    old = self.previous.get(pid)
                    # Unchanged counters cannot produce an activity record. Defer procfs
                    # metadata until change, then recheck identity around a fresh query.
                    if comparable and old is not None and wait == old['wait']:
                        current[pid] = old
                        coverage['measured'] += 1
                        continue
                    item = metadata(directory, memory_details=False)
                    wait = self.reader.get(item['pid'])
                    if not isinstance(wait, int) or not 0 <= wait < 2 ** 64:
                        raise ValueError('invalid swap-in delay')
                    item['wait'] = wait
                    current[item['pid']] = item
                    if (not comparable or old is None
                            or (old['start'], old['name']) != (item['start'], item['name'])):
                        coverage['baselines'] += 1
                        continue
                    delta = wait - old['wait']
                    # Loose kernel-wide thread ceiling rejects impossible overflow jumps.
                    if delta < 0 or delta > elapsed * 1e9 * 4194304:
                        coverage['resets'] += 1
                        continue
                    if delta:
                        after = metadata(directory)
                        if (after['start'], after['name']) != (item['start'], item['name']):
                            coverage['resets'] += 1
                            del current[item['pid']]
                            continue
                        activity.append({**after, 'delay_ns': delta})
                    coverage['measured'] += 1
                except PermissionError:
                    raise
                except (FileNotFoundError, ProcessLookupError):
                    coverage['gone'] += 1
                except (OSError, ValueError, KeyError, IndexError, AssertionError):
                    coverage['errors'] += 1
        coverage['gone'] += len(self.previous.keys() - current.keys())
        self.previous = current
        self.last = (wall, monotonic, boot)
        return {'boot': boot, 'bucket': int(wall // self.interval) * self.interval,
                'start': wall - elapsed if comparable else wall, 'end': wall,
                'elapsed': elapsed if comparable else 0, 'coverage': coverage,
                'activity': activity}


def prepare_directory(path):
    path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    parent = path.parent.stat()
    if (path.parent.is_symlink() or parent.st_uid != os.geteuid() or parent.st_mode & 0o022
            or path.is_symlink()):
        raise ValueError('history requires an owned, non-writable-by-others directory')
    if path.exists() and (path.stat().st_uid != os.geteuid() or path.stat().st_mode & 0o022):
        raise ValueError('unsafe history file owner or permissions')


class History:
    def __init__(self, path, max_bytes=64 * MIB, retention_seconds=30 * 86400):
        self.path, self.max_bytes, self.retention = path, max_bytes, retention_seconds
        if max_bytes < 8 * MIB or retention_seconds <= 0:
            raise ValueError('history budget must be >=8 MiB and retention positive')
        prepare_directory(path)
        self.db = sqlite3.connect(path, timeout=2)
        self.db.execute('PRAGMA foreign_keys=ON')
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1):
            raise ValueError('unsupported history schema')
        self.db.execute('PRAGMA auto_vacuum=INCREMENTAL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS frames(
                id INTEGER PRIMARY KEY, boot TEXT NOT NULL, bucket INTEGER NOT NULL,
                started REAL NOT NULL, ended REAL NOT NULL, elapsed REAL NOT NULL,
                coverage TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS frame_window ON frames(boot,bucket);
            CREATE INDEX IF NOT EXISTS frame_retention ON frames(ended);
            CREATE TABLE IF NOT EXISTS activity(
                frame INTEGER NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
                pid INTEGER NOT NULL, start_ticks INTEGER NOT NULL, name TEXT NOT NULL,
                delay_ns INTEGER NOT NULL CHECK(delay_ns>0), rss INTEGER NOT NULL,
                swap INTEGER NOT NULL, PRIMARY KEY(frame,pid));
            CREATE INDEX IF NOT EXISTS process_window ON activity(pid,start_ticks,frame);
            PRAGMA user_version=1;
        ''')
        if self.db.execute('PRAGMA journal_mode=DELETE').fetchone()[0] != 'delete':
            raise ValueError('history requires rollback journal mode')
        self.db.execute('PRAGMA synchronous=FULL')
        # One transaction can journal each existing page once. Disabling cache
        # spill avoids extra journal segments and bounds dirty memory by the DB.
        # https://www.sqlite.org/fileformat2.html#the_rollback_journal
        self.db.execute('PRAGMA cache_spill=OFF')
        self.page_size = self.db.execute('PRAGMA page_size').fetchone()[0]
        # Reserve a full rollback copy plus 2 MiB for record/sector headers.
        self.page_limit = (max_bytes - 2 * MIB) // (2 * self.page_size)
        actual = self.db.execute(f'PRAGMA max_page_count={self.page_limit}').fetchone()[0]
        if actual > self.page_limit:
            raise ValueError('existing history exceeds its main-file budget')
        self.db.commit()
        self.last_maintenance = 0
        self.permissions()

    def permissions(self):
        os.chmod(self.path, 0o644)

    def record(self, frame):
        if len(frame['activity']) > 4096:
            raise ValueError('too many process records')
        with self.db:
            self.db.execute('DELETE FROM frames WHERE ended < ?', (frame['end'] - self.retention,))
            used = (self.db.execute('PRAGMA page_count').fetchone()[0]
                    - self.db.execute('PRAGMA freelist_count').fetchone()[0])
            if used > self.page_limit * .8:
                count = self.db.execute('SELECT count(*) FROM frames').fetchone()[0]
                self.db.execute('DELETE FROM frames WHERE id IN (SELECT id FROM frames ORDER BY id LIMIT ?)',
                                (max(1, count // 5),))
            cursor = self.db.execute('INSERT INTO frames(boot,bucket,started,ended,elapsed,coverage) '
                                     'VALUES(?,?,?,?,?,?)',
                                     (frame['boot'], frame['bucket'], frame['start'], frame['end'],
                                      frame['elapsed'], json.dumps(frame['coverage'], separators=(',', ':'))))
            self.db.executemany('INSERT INTO activity VALUES(?,?,?,?,?,?,?)',
                                [(cursor.lastrowid, p['pid'], p['start'], p['name'], p['delay_ns'],
                                  p['rss'], p['swap']) for p in frame['activity']])
        if frame['end'] - self.last_maintenance >= 60:
            self.db.execute('PRAGMA incremental_vacuum(64)')
            self.last_maintenance = frame['end']
        self.permissions()

    def close(self):
        self.db.close()


def query_history(path, before, boot, window=120, pid=None):
    """Read saved data only; never enumerate live processes or query TASKSTATS."""
    result = {'status': 'unavailable', 'processes': []}
    try:
        uri = 'file:' + quote(str(path.absolute()), safe='/') + '?mode=ro'
        with closing(sqlite3.connect(uri, uri=True, timeout=1)) as db:
            db.execute('BEGIN')
            if db.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise ValueError('unsupported history schema')
            frames = db.execute('SELECT id,bucket,elapsed,coverage,started,ended FROM frames '
                                'WHERE boot=? AND bucket>? AND bucket<=? ORDER BY bucket,id LIMIT 1001',
                                (boot, before - window, before)).fetchall()
            if not frames:
                raise ValueError('no process history for the requested window')
            if len(frames) > 1000:
                raise ValueError('too many history frames')
            buckets = [row[1] for row in frames]
            expected = list(range(before - window + 10, before + 1, 10))
            partial = buckets != expected
            totals = dict(errors=0, gone=0, truncated=0, baselines=0, resets=0)
            at_boot = True
            valid_frames = []
            for frame_id, _, elapsed, encoded, started, ended in frames:
                coverage = json.loads(encoded)
                for key in totals:
                    totals[key] += coverage[key]
                at_boot = at_boot and coverage['accounting_at_boot']
                if (not all(isinstance(value, (float, int)) and math.isfinite(value)
                            for value in (started, ended, elapsed))
                        or elapsed <= 0 or started >= ended
                        or started < before - window or ended > before):
                    partial = True
                    continue
                valid_frames.append(frame_id)
                if coverage['measured'] < coverage['scanned']:
                    partial = True
            partial = partial or any(totals.values()) or not at_boot
            placeholders = ','.join('?' for _ in valid_frames)
            rows = db.execute(f'''SELECT a.pid,a.start_ticks,a.name,sum(a.delay_ns),
                                        max(a.rss),max(a.swap),max(f.bucket)
                                 FROM activity a JOIN frames f ON f.id=a.frame
                                 WHERE a.frame IN ({placeholders}) AND (? IS NULL OR a.pid=?)
                                 GROUP BY a.pid,a.start_ticks,a.name
                                 ORDER BY sum(a.delay_ns) DESC,a.pid LIMIT 3''',
                              [*valid_frames, pid, pid]).fetchall() if valid_frames else []
        processes = [{'pid': p, 'start_ticks': start, 'name': name,
                      'swap_in_wait_seconds': delay / 1e9, 'rss_bytes': rss,
                      'swap_bytes': swap, 'last_observed': stamp}
                     for p, start, name, delay, rss, swap, stamp in rows]
        return {'status': 'partial' if partial else 'measured', 'processes': processes,
                'after': before - window, 'before': before, 'frames': len(frames),
                'excluded_intervals': len(frames) - len(valid_frames),
                'coverage': totals, 'accounting_at_boot': at_boot}
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        return {**result, 'error': str(error)}


def collect(args):
    if os.geteuid() != 0:
        raise ValueError('collection requires root; history queries do not')
    if args.interval != 10:
        raise ValueError('collection interval must match the ten-second historical grid')
    prepare_directory(args.database)
    lock_fd = os.open(args.database.parent / '.collector.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.fchmod(lock.fileno(), 0o600)
        history = History(args.database, args.max_mib * MIB, args.retention_days * 86400)
        reader = KernelReader()
        sampler = Sampler(reader)
        stopped = False
        def stop(*_):
            nonlocal stopped
            stopped = True
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            for iteration in range(args.iterations or 2 ** 63):
                enabled = Path('/proc/sys/kernel/task_delayacct').read_text().strip() == '1'
                if not enabled:
                    raise ValueError('kernel.task_delayacct is disabled; process evidence unavailable')
                boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
                frame = sampler.sample(time.time(), time.monotonic(), boot,
                                       'delayacct' in Path('/proc/cmdline').read_text().split())
                history.record(frame)
                if not iteration or iteration % 6 == 0:
                    print(json.dumps({'status': 'collecting', 'bucket': frame['bucket'],
                                      'activity_processes': len(frame['activity']),
                                      'coverage': frame['coverage']}), flush=True)
                if stopped or (args.iterations and iteration + 1 >= args.iterations):
                    break
                target = (math.floor(time.time() / 10) + 1) * 10
                while not stopped and time.time() < target:
                    time.sleep(max(0, min(.2, target - time.time())))
                if stopped:
                    break
        finally:
            reader.close()
            history.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('collect', 'query'))
    parser.add_argument('--database', type=Path, default=DEFAULT_DATABASE)
    parser.add_argument('--before', type=int, default=None)
    parser.add_argument('--boot-id', default=None)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--interval', type=int, default=10)
    parser.add_argument('--iterations', type=int)
    parser.add_argument('--retention-days', type=int, default=30)
    parser.add_argument('--max-mib', type=int, default=64)
    args = parser.parse_args(argv)
    if args.retention_days <= 0 or args.max_mib < 8 or (args.iterations is not None and args.iterations < 1):
        parser.error('invalid iteration, retention or storage limit')
    try:
        if args.action == 'collect':
            collect(args)
        else:
            boot = args.boot_id or Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            result = query_history(args.database, args.before or int(time.time() // 10) * 10 - 10,
                                   boot, pid=args.pid)
            print(json.dumps(result, sort_keys=True))
            return 2 if result['status'] == 'unavailable' else 0
    except (OSError, ValueError, sqlite3.Error, ImportError) as error:
        print(f'Process swap history unavailable: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
