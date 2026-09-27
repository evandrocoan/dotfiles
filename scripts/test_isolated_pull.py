"""Regression tests for scripts/isolated_pull.sh.

The script relocates a repository's .git directory, so every test asserts an
observable outcome of that relocation: where .git ends up, which state it
carries, and that the repository root work tree is never written. Fixtures build
their environment from scratch so no inherited GIT_* variable, host
configuration or default branch name can decide a result. HOME is pinned to the
fixture repository root, reproducing the real topology in which Git resolves the
tracked global configuration through HOME.
"""

import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/isolated_pull.sh'
README = SCRIPT.parents[1] / 'README.md'
BLOCKING_SLEEP_SECONDS = 20
MOVE_DEADLINE_SECONDS = 15


class IsolatedPullTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / 'origin.git'
        self.repository = self.root / 'home'
        self.base = self.root / 'base'
        self.base.mkdir()
        self.env = {
            'PATH': os.environ['PATH'],
            'HOME': str(self.repository),
            'LANG': 'C',
            'LC_ALL': 'C',
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_TERMINAL_PROMPT': '0',
        }
        self.git('init', '--bare', '-b', 'master', str(self.origin), cwd=self.root)
        self.git('init', '-b', 'master', str(self.repository), cwd=self.root)
        self.write('.gitconfig', '[user]\n\tname = Fixture\n\temail = fixture@example.invalid\n')
        self.write('live.conf', 'live configuration version 1\n')
        self.write('shared.txt', 'shared line\n')
        self.write('flagged_changed.conf', 'flagged original\n')
        self.write('flagged_intact.conf', 'flagged original\n')
        self.git('add', '-A', cwd=self.repository)
        self.git('commit', '-m', 'Seed', cwd=self.repository)
        self.git('remote', 'add', 'origin', str(self.origin), cwd=self.repository)
        self.git('push', '-u', 'origin', 'master', cwd=self.repository)

    def git(self, *args, cwd, check=True):
        result = subprocess.run(['git', *args], cwd=str(cwd), env=self.env,
                                capture_output=True, text=True)
        if check:
            self.assertEqual(result.returncode, 0, f'git {args}: {result.stderr}')
        return result

    def write(self, relative_path, content):
        path = self.repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def push_upstream_change(self, changes, message='Upstream change'):
        """Publish changes to origin through a separate clone."""
        upstream = self.root / f'upstream-{message.replace(" ", "-")}'
        self.git('clone', str(self.origin), str(upstream), cwd=self.root)
        for relative_path, content in changes.items():
            target = upstream / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        self.git('add', '-A', cwd=upstream)
        self.git('commit', '-m', message, cwd=upstream)
        self.git('push', cwd=upstream)
        return self.git('rev-parse', 'HEAD', cwd=upstream).stdout.strip()

    def run_script(self, *args, expect=0, script=None, env=None, timeout=120):
        command = ['bash', str(script or SCRIPT),
                   '--repository', str(self.repository),
                   '--base', str(self.base), *args]
        result = subprocess.run(command, env=env or self.env, capture_output=True,
                                text=True, timeout=timeout)
        self.assertEqual(result.returncode, expect,
                         f'unexpected status\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}')
        return result

    def start_blocked_script(self, *args, script=None, descendant_lock=False,
                             resistant_descendant=False):
        """Start a run whose fetch blocks, so signals arrive mid-pull."""
        fake_ssh = self.root / 'fake_ssh.sh'
        self.transport_marker = self.root / 'transport-started'
        if descendant_lock:
            self.descendant_marker = self.root / 'descendant-pid'
            ignored_term = "trap '' TERM\n" if resistant_descendant else ''
            child_wait = (f'exec sleep {BLOCKING_SLEEP_SECONDS}\n' if resistant_descendant else
                          f'trap \'rm -f -- "${{git_directory}}/index.lock"; exit 0\' TERM\n'
                          f'sleep {BLOCKING_SLEEP_SECONDS}\n')
            fake_ssh.write_text(
                '#!/usr/bin/env bash\nset -euo pipefail\n'
                '(\n'
                f'    {ignored_term}'
                '    found_git_directory=0\n'
                f'    for git_directory in {shlex.quote(str(self.base))}/run-*/.git; do\n'
                '        if [[ -d "${git_directory}" ]]; then\n'
                '            : > "${git_directory}/index.lock"\n'
                '            found_git_directory=1\n'
                '            break\n'
                '        fi\n'
                '    done\n'
                '    [[ "${found_git_directory}" == 1 ]] || exit 1\n'
                f'    printf "%s\\n" "${{BASHPID}}" > {shlex.quote(str(self.descendant_marker))}\n'
                f'    {child_wait}'
                f') > {shlex.quote(str(self.root / "descendant-stdout"))} '
                f'2> {shlex.quote(str(self.root / "descendant-stderr"))} &\n'
                f'while [[ ! -s {shlex.quote(str(self.descendant_marker))} ]]; do sleep 0.05; done\n'
                f': > {shlex.quote(str(self.transport_marker))}\n'
                f'sleep {BLOCKING_SLEEP_SECONDS}\n')
        else:
            fake_ssh.write_text(f'#!/usr/bin/env bash\n: > "{self.transport_marker}"\n'
                                f'sleep {BLOCKING_SLEEP_SECONDS}\n')
        fake_ssh.chmod(0o755)
        self.git('remote', 'set-url', 'origin', 'ssh://fixture.invalid/repository',
                 cwd=self.repository)
        env = dict(self.env, GIT_SSH_COMMAND=str(fake_ssh))
        # Transport descendants can outlive the pull leader and inherit output;
        # files let tests wait for the script rather than pipe EOF.
        self.blocked_stdout = self.root / 'blocked-stdout.txt'
        self.blocked_stderr = self.root / 'blocked-stderr.txt'
        stdout_stream = self.blocked_stdout.open('w')
        stderr_stream = self.blocked_stderr.open('w')
        self.addCleanup(stdout_stream.close)
        self.addCleanup(stderr_stream.close)
        process = subprocess.Popen(
            ['bash', str(script or SCRIPT), '--repository', str(self.repository),
             '--base', str(self.base), *args],
            env=env, stdout=stdout_stream, stderr=stderr_stream, text=True)
        self.addCleanup(self.terminate_process, process)
        deadline = time.monotonic() + MOVE_DEADLINE_SECONDS
        while time.monotonic() < deadline:
            if self.transport_marker.exists():
                return process
            if process.poll() is not None:
                break
            time.sleep(0.05)
        self.fail('the run never reached the blocked transport\n'
                  f'stdout:\n{self.blocked_stdout.read_text()}\n'
                  f'stderr:\n{self.blocked_stderr.read_text()}')

    def process_is_running_now(self, pid):
        stat_path = Path(f'/proc/{pid}/stat')
        if not stat_path.exists():
            return False
        try:
            state = stat_path.read_text().rsplit(') ', 1)[1].split(' ', 1)[0]
        except FileNotFoundError:
            return False
        return state not in {'Z', 'X'}

    def process_is_alive(self, pid):
        deadline = time.monotonic() + MOVE_DEADLINE_SECONDS
        while time.monotonic() < deadline:
            if not self.process_is_running_now(pid):
                return False
            time.sleep(0.05)
        return True

    def process_start_time(self, pid):
        try:
            fields = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
        except FileNotFoundError:
            return None
        return fields[19]

    def kill_descendant(self, pid, start_time):
        if self.process_start_time(pid) != start_time:
            return
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def signal_after_move(self, *, returning=False):
        """Signal the real script after mv renamed .git but before its next statement."""
        bin_directory = self.root / 'signal-bin'
        bin_directory.mkdir()
        marker = self.root / 'move-signalled'
        condition = (f'[[ "${{4}}" == {shlex.quote(str(self.repository / ".git"))} ]]'
                     if returning else
                     f'[[ "${{3}}" == {shlex.quote(str(self.repository / ".git"))} ]]')
        wrapper = bin_directory / 'mv'
        wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
                           f'{shlex.quote(shutil.which("mv"))} "$@"\n'
                           f'if {condition}; then\n'
                           f'    : > {shlex.quote(str(marker))}\n'
                           '    kill -TERM "${PPID}"\n'
                           'fi\n')
        wrapper.chmod(0o755)
        env = dict(self.env, PATH=f'{bin_directory}{os.pathsep}{self.env["PATH"]}')
        result = self.run_script(expect=143, env=env)
        self.assertTrue(marker.exists(), 'the signal never reached the move boundary')
        return result

    def fail_isolated_abort(self, *, after_real_abort=False):
        bin_directory = self.root / 'abort-bin'
        bin_directory.mkdir()
        wrapper = bin_directory / 'git'
        real_git = shlex.quote(shutil.which('git'))
        real_abort = f'    {real_git} "$@"\n' if after_real_abort else ''
        wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
                           'if [[ " $* " == *" rebase --abort "* ]]; then\n'
                           f'{real_abort}'
                           '    printf "injected abort failure\\n" >&2\n'
                           '    exit 73\n'
                           'fi\n'
                           f'exec {real_git} "$@"\n')
        wrapper.chmod(0o755)
        return dict(self.env, PATH=f'{bin_directory}{os.pathsep}{self.env["PATH"]}')

    def readme_recovery_command(self):
        section = README.read_text().split('#### Recover an interrupted isolated pull\n', 1)[1]
        return section.split('```bash\n', 1)[1].split('\n```', 1)[0]

    def direct_children(self, parent_pid):
        """Return (pid, command name) for every direct child of parent_pid."""
        children = []
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                fields = (entry / 'stat').read_text().rsplit(') ', 1)
                command = fields[0].split(' (', 1)[1]
                if int(fields[1].split(' ')[1]) == parent_pid:
                    children.append((int(entry.name), command))
            except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
                continue
        return children

    def terminate_process(self, process):
        if process.poll() is None:
            process.kill()
            process.wait(timeout=MOVE_DEADLINE_SECONDS)

    def isolated_trees(self):
        return sorted(path for path in self.base.iterdir() if path.is_dir())

    def assume_unchanged(self, cwd=None):
        listing = self.git('ls-files', '-v', cwd=cwd or self.repository).stdout
        return {line[2:] for line in listing.splitlines() if line.startswith('h ')}

    def snapshot(self, *relative_paths):
        return {path: (self.repository / path).read_bytes() for path in relative_paths}

    def assert_git_returned(self):
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file(),
                        'the Git directory did not return to the repository root')
        self.assertFalse((self.repository / '.git' / '.git').exists(),
                         'the Git directory was nested instead of returned')
        for tree in self.isolated_trees():
            self.assertFalse((tree / '.git').exists(),
                             f'a Git directory was left behind in {tree}')

    def assert_no_pending_state(self):
        for marker in ('rebase-merge', 'rebase-apply', 'MERGE_HEAD', 'index.lock'):
            self.assertFalse((self.repository / '.git' / marker).exists(),
                             f'.git/{marker} came back with the repository')

    def test_fast_forward_returns_git_and_preserves_root_work(self):
        self.write('live.conf', 'live configuration version 1 WITH MY EDIT\n')
        self.write('untracked.txt', 'my untracked work\n')
        before = self.snapshot('live.conf', 'untracked.txt', 'shared.txt')
        upstream_commit = self.push_upstream_change({'shared.txt': 'upstream rewrote this\n'})

        result = self.run_script()

        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         upstream_commit)
        self.assertEqual(self.snapshot('live.conf', 'untracked.txt', 'shared.txt'), before,
                         'the repository work tree was written')
        tree = self.isolated_trees()[0]
        self.assertEqual((tree / 'shared.txt').read_text(), 'upstream rewrote this\n')
        self.assertIn('Returned the Git directory', result.stdout)

    def test_tracked_global_configuration_is_untouched_while_history_moves(self):
        """Invariant 4: Git reads global configuration from HOME, not from the isolated tree."""
        before = self.snapshot('.gitconfig')
        self.push_upstream_change({
            '.gitconfig': '[user]\n\tname = Upstream\n\temail = upstream@example.invalid\n'})

        self.run_script()

        self.assertEqual(self.snapshot('.gitconfig'), before,
                         'the tracked global configuration in the root was rewritten')
        tree = self.isolated_trees()[0]
        self.assertIn('Upstream', (tree / '.gitconfig').read_text())
        origin = self.git('config', '--show-origin', 'user.name',
                          cwd=self.repository).stdout
        self.assertIn(str(self.repository / '.gitconfig'), origin)

    def test_failed_pull_returns_git_directory(self):
        self.write('live.conf', 'live configuration WITH MY EDIT\n')
        before = self.snapshot('live.conf')
        self.origin.rename(self.root / 'origin.git.away')

        result = self.run_script(expect=1)

        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertIn('git pull --rebase" failed', result.stderr)
        self.assertEqual(self.snapshot('live.conf'), before)

    def test_failed_pull_with_remaining_index_lock_stays_isolated(self):
        fake_ssh = self.root / 'lock_then_fail_ssh.sh'
        fake_ssh.write_text(
            '#!/usr/bin/env bash\nset -euo pipefail\n'
            f'for git_directory in {shlex.quote(str(self.base))}/run-*/.git; do\n'
            '    if [[ -d "${git_directory}" ]]; then\n'
            '        : > "${git_directory}/index.lock"\n'
            '        exit 1\n'
            '    fi\n'
            'done\n'
            'exit 2\n')
        fake_ssh.chmod(0o755)
        self.git('remote', 'set-url', 'origin', 'ssh://fixture.invalid/repository',
                 cwd=self.repository)
        env = dict(self.env, GIT_SSH_COMMAND=str(fake_ssh))

        result = self.run_script(expect=1, env=env)

        self.assertFalse((self.repository / '.git').exists())
        tree = self.isolated_trees()[0]
        lock = tree / '.git' / 'index.lock'
        self.assertTrue(lock.is_file())
        self.assertIn(str(lock), result.stderr)
        self.assertIn(str(tree), result.stderr)

    def test_negative_control_without_trap_leaves_git_displaced(self):
        """Proves the restore assertion above detects a missing exit handler."""
        without_trap = self.root / 'isolated_pull_without_trap.sh'
        source = SCRIPT.read_text()
        self.assertIn('trap onexit EXIT\n', source)
        without_trap.write_text(source.replace('trap onexit EXIT\n', ''))
        self.origin.rename(self.root / 'origin.git.away')

        self.run_script(expect=1, script=without_trap)

        self.assertFalse((self.repository / '.git').exists(),
                         'without the exit handler the Git directory should stay displaced')
        self.assertTrue((self.isolated_trees()[0] / '.git' / 'HEAD').is_file())

    def test_conflicting_rebase_returns_git_without_rebase_state(self):
        self.write('shared.txt', 'my local commit line\n')
        self.git('add', 'shared.txt', cwd=self.repository)
        self.git('commit', '-m', 'Local commit', cwd=self.repository)
        local_tip = self.git('rev-parse', 'master', cwd=self.repository).stdout.strip()
        self.write('live.conf', 'live configuration WITH MY EDIT\n')
        before = self.snapshot('live.conf')
        self.push_upstream_change({'shared.txt': 'upstream rewrote the same line\n'})

        result = self.run_script(expect=1)

        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         local_tip, 'the local commit was not preserved at its original tip')
        self.assertEqual(self.git('rev-parse', '--abbrev-ref', 'HEAD',
                                  cwd=self.repository).stdout.strip(), 'master')
        self.assertEqual(self.snapshot('live.conf'), before)
        self.assertIn('failed', result.stderr)

    def test_termination_signal_returns_git_directory(self):
        """A TERM arriving while the pull blocks must not move a busy database."""
        process = self.start_blocked_script()

        pull_pid = self.direct_children(process.pid)[0][0]

        process.terminate()
        status = process.wait(timeout=MOVE_DEADLINE_SECONDS)

        self.assertNotEqual(status, 0, self.blocked_stderr.read_text())
        self.assertFalse(self.process_is_alive(pull_pid),
                         'the pull still held the database after the script exited')
        self.assert_git_returned()
        self.assert_no_pending_state()

    def test_termination_stops_lock_holding_descendant_before_return(self):
        process = self.start_blocked_script(descendant_lock=True)
        descendant_pid = int(self.descendant_marker.read_text())
        self.addCleanup(self.kill_descendant, descendant_pid,
                        self.process_start_time(descendant_pid))
        self.assertTrue((self.isolated_trees()[0] / '.git' / 'index.lock').is_file())

        process.terminate()
        status = process.wait(timeout=MOVE_DEADLINE_SECONDS)

        self.assertNotEqual(status, 0)
        self.assertFalse(self.process_is_alive(descendant_pid),
                         'a descendant still held the Git directory after restoration')
        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertFalse((self.isolated_trees()[0] / 'pull-process-group').exists())

    def test_unstoppable_descendant_keeps_git_isolated(self):
        self.write('live.conf', 'my live edit\n')
        self.write('untracked.txt', 'my untracked work\n')
        before = self.snapshot('live.conf', 'untracked.txt')
        process = self.start_blocked_script(descendant_lock=True,
                                            resistant_descendant=True)
        descendant_pid = int(self.descendant_marker.read_text())
        self.addCleanup(self.kill_descendant, descendant_pid,
                        self.process_start_time(descendant_pid))
        self.assertTrue((self.isolated_trees()[0] / '.git' / 'index.lock').is_file())

        process.terminate()
        status = process.wait(timeout=MOVE_DEADLINE_SECONDS)

        self.assertNotEqual(status, 0)
        self.assertTrue(self.process_is_running_now(descendant_pid),
                        'the fixture descendant must resist TERM')
        self.assertFalse((self.repository / '.git').exists(),
                         'the database returned while its descendant could still use it')
        tree = self.isolated_trees()[0]
        self.assertTrue((tree / '.git' / 'HEAD').is_file())
        self.assertTrue((tree / 'pull-process-group').is_file())
        self.assertIn(str(tree), self.blocked_stderr.read_text())
        self.assertEqual(self.snapshot('live.conf', 'untracked.txt'), before)

    def test_pull_leader_exits_before_live_descendant_keeps_git_isolated(self):
        self.write('live.conf', 'my live edit\n')
        before = self.snapshot('live.conf')
        bin_directory = self.root / 'early-pull-exit-bin'
        bin_directory.mkdir()
        marker = self.root / 'early-pull-descendant-pid'
        wrapper = bin_directory / 'git'
        wrapper.write_text(
            '#!/usr/bin/env bash\nset -euo pipefail\n'
            'if [[ " $* " == *" pull --rebase "* ]]; then\n'
            '    git_directory=""\n'
            '    for argument in "$@"; do\n'
            '        if [[ "${argument}" == --git-dir=* ]]; then\n'
            '            git_directory="${argument#--git-dir=}"\n'
            '        fi\n'
            '    done\n'
            '    [[ -n "${git_directory}" ]] || exit 2\n'
            '    (\n'
            "        trap '' TERM\n"
            '        : > "${git_directory}/descendant-active"\n'
            f'        printf "%s\\n" "${{BASHPID}}" > {shlex.quote(str(marker))}\n'
            f'        exec sleep {BLOCKING_SLEEP_SECONDS}\n'
            f'    ) > {shlex.quote(str(self.root / "early-descendant-stdout"))} '
            f'2> {shlex.quote(str(self.root / "early-descendant-stderr"))} &\n'
            f'    while [[ ! -s {shlex.quote(str(marker))} ]]; do sleep 0.05; done\n'
            '    exit 0\n'
            'fi\n'
            f'exec {shlex.quote(shutil.which("git"))} "$@"\n')
        wrapper.chmod(0o755)
        env = dict(self.env, PATH=f'{bin_directory}{os.pathsep}{self.env["PATH"]}')

        result = self.run_script(expect=1, env=env)

        self.assertTrue(marker.is_file(), result.stderr)
        descendant_pid = int(marker.read_text())
        self.addCleanup(self.kill_descendant, descendant_pid,
                        self.process_start_time(descendant_pid))
        self.assertTrue(self.process_is_running_now(descendant_pid),
                        'the descendant must remain after its pull leader exits')
        tree = self.isolated_trees()[0]
        self.assertFalse((self.repository / '.git').exists())
        self.assertTrue((tree / '.git' / 'descendant-active').is_file())
        self.assertTrue((tree / 'pull-process-group').is_file())
        self.assertIn('pull process group', result.stderr)
        self.assertNotIn('still has a lock', result.stderr)
        self.assertIn(str(tree), result.stderr)
        self.assertEqual(self.snapshot('live.conf'), before)

    def test_unstoppable_pull_leader_exits_script_without_returning_git(self):
        bin_directory = self.root / 'resistant-pull-bin'
        bin_directory.mkdir()
        marker = self.root / 'resistant-pull-pid'
        wrapper = bin_directory / 'git'
        wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
                           'if [[ " $* " == *" pull --rebase "* ]]; then\n'
                           "    trap '' TERM\n"
                           f'    printf "%s\\n" "${{BASHPID}}" > {shlex.quote(str(marker))}\n'
                           f'    exec sleep {BLOCKING_SLEEP_SECONDS}\n'
                           'fi\n'
                           f'exec {shlex.quote(shutil.which("git"))} "$@"\n')
        wrapper.chmod(0o755)
        env = dict(self.env, PATH=f'{bin_directory}{os.pathsep}{self.env["PATH"]}')
        stdout_path = self.root / 'resistant-pull-stdout'
        stderr_path = self.root / 'resistant-pull-stderr'
        with stdout_path.open('w') as stdout_stream, stderr_path.open('w') as stderr_stream:
            process = subprocess.Popen(
                ['bash', str(SCRIPT), '--repository', str(self.repository),
                 '--base', str(self.base)], env=env, stdout=stdout_stream,
                stderr=stderr_stream)
            self.addCleanup(self.terminate_process, process)
            deadline = time.monotonic() + MOVE_DEADLINE_SECONDS
            while not marker.exists() and time.monotonic() < deadline:
                self.assertIsNone(process.poll(), stderr_path.read_text())
                time.sleep(0.05)
            self.assertTrue(marker.exists(), stderr_path.read_text())
            leader_pid = int(marker.read_text())
            self.addCleanup(self.kill_descendant, leader_pid,
                            self.process_start_time(leader_pid))

            process.terminate()
            status = process.wait(timeout=MOVE_DEADLINE_SECONDS)

        self.assertNotEqual(status, 0)
        self.assertTrue(self.process_is_running_now(leader_pid),
                        'the fixture pull leader must resist TERM')
        self.assertFalse((self.repository / '.git').exists())
        tree = self.isolated_trees()[0]
        self.assertTrue((tree / '.git' / 'HEAD').is_file())
        self.assertTrue((tree / 'pull-process-group').is_file())
        self.assertIn(str(tree), stderr_path.read_text())

    def test_signal_after_first_rename_restores_git(self):
        before = self.snapshot('live.conf', 'shared.txt')

        self.signal_after_move()

        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)

    def test_signal_after_return_rename_recognizes_completed_restore(self):
        before = self.snapshot('live.conf', 'shared.txt')
        upstream_commit = self.push_upstream_change({'shared.txt': 'upstream rewrote this\n'})

        result = self.signal_after_move(returning=True)

        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         upstream_commit)
        self.assertNotIn('reappeared', result.stderr)

    def test_failed_abort_keeps_pending_database_isolated(self):
        self.write('shared.txt', 'my local commit line\n')
        self.git('commit', '-am', 'Local commit', cwd=self.repository)
        local_tip = self.git('rev-parse', 'master', cwd=self.repository).stdout.strip()
        self.write('live.conf', 'my live edit\n')
        before = self.snapshot('live.conf', 'shared.txt')
        self.push_upstream_change({'shared.txt': 'upstream rewrote the same line\n'})

        result = self.run_script(expect=1, env=self.fail_isolated_abort())

        self.assertFalse((self.repository / '.git').exists())
        tree = self.isolated_trees()[0]
        self.assertTrue((tree / '.git' / 'rebase-merge').is_dir())
        self.assertEqual(self.git('--git-dir', str(tree / '.git'),
                                  'rev-parse', 'refs/heads/master', cwd=self.root).stdout.strip(),
                         local_tip)
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        self.assertIn(str(tree), result.stderr)
        self.assertIn('README.md', result.stderr)

    def test_failed_abort_status_keeps_database_isolated_even_without_marker(self):
        self.write('shared.txt', 'my local commit line\n')
        self.git('commit', '-am', 'Local commit', cwd=self.repository)
        local_tip = self.git('rev-parse', 'master', cwd=self.repository).stdout.strip()
        self.write('live.conf', 'my live edit\n')
        before = self.snapshot('live.conf', 'shared.txt')
        self.push_upstream_change({'shared.txt': 'upstream rewrote the same line\n'})

        result = self.run_script(expect=1,
                                 env=self.fail_isolated_abort(after_real_abort=True))

        self.assertFalse((self.repository / '.git').exists())
        tree = self.isolated_trees()[0]
        self.assertTrue((tree / '.git' / 'HEAD').is_file())
        self.assertFalse((tree / '.git' / 'rebase-merge').exists())
        self.assertEqual(self.git('--git-dir', str(tree / '.git'),
                                  'rev-parse', 'refs/heads/master', cwd=self.root).stdout.strip(),
                         local_tip)
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        self.assertIn(str(tree), result.stderr)

    def test_readme_recovery_aborts_isolated_rebase_before_return(self):
        self.base = self.repository / '.local' / 'state' / 'isolated-pull'
        self.base.mkdir(parents=True)
        self.write('shared.txt', 'my local commit line\n')
        self.git('commit', '-am', 'Local commit', cwd=self.repository)
        local_tip = self.git('rev-parse', 'master', cwd=self.repository).stdout.strip()
        self.write('live.conf', 'my live edit\n')
        before = self.snapshot('live.conf', 'shared.txt')
        self.push_upstream_change({'shared.txt': 'upstream rewrote the same line\n'})
        self.run_script(expect=1, env=self.fail_isolated_abort())

        result = subprocess.run(['bash', '-c', self.readme_recovery_command()],
                                env=self.env, capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_git_returned()
        self.assert_no_pending_state()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         local_tip)
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)

    def test_readme_recovery_refuses_live_pull_group(self):
        self.base = self.repository / '.local' / 'state' / 'isolated-pull'
        self.base.mkdir(parents=True)
        process = self.start_blocked_script(descendant_lock=True,
                                            resistant_descendant=True)
        descendant_pid = int(self.descendant_marker.read_text())
        self.addCleanup(self.kill_descendant, descendant_pid,
                        self.process_start_time(descendant_pid))
        self.assertTrue((self.isolated_trees()[0] / '.git' / 'index.lock').is_file())
        process.terminate()
        self.assertNotEqual(process.wait(timeout=MOVE_DEADLINE_SECONDS), 0)

        result = subprocess.run(['bash', '-c', self.readme_recovery_command()],
                                env=self.env, capture_output=True, text=True)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('Pull processes still run', result.stderr)
        self.assertFalse((self.repository / '.git').exists())
        self.assertTrue((self.isolated_trees()[0] / '.git' / 'HEAD').is_file())

    def test_readme_recovery_refuses_remaining_rebase_marker(self):
        self.base = self.repository / '.local' / 'state' / 'isolated-pull'
        self.base.mkdir(parents=True)
        self.write('shared.txt', 'my local commit line\n')
        self.git('commit', '-am', 'Local commit', cwd=self.repository)
        self.push_upstream_change({'shared.txt': 'upstream rewrote the same line\n'})
        self.run_script(expect=1, env=self.fail_isolated_abort())
        tree = self.isolated_trees()[0]

        bin_directory = self.root / 'noop-abort-bin'
        bin_directory.mkdir()
        wrapper = bin_directory / 'git'
        wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
                           'if [[ " $* " == *" rebase --abort "* ]]; then exit 0; fi\n'
                           f'exec {shlex.quote(shutil.which("git"))} "$@"\n')
        wrapper.chmod(0o755)
        env = dict(self.env, PATH=f'{bin_directory}{os.pathsep}{self.env["PATH"]}')

        result = subprocess.run(['bash', '-c', self.readme_recovery_command()],
                                env=env, capture_output=True, text=True)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('Unfinished Git operation remains', result.stderr)
        self.assertFalse((self.repository / '.git').exists())
        self.assertTrue((tree / '.git' / 'rebase-merge').is_dir())

    def test_return_collision_is_refused_instead_of_nested(self):
        process = self.start_blocked_script()
        (self.repository / '.git').mkdir()

        process.terminate()
        status = process.wait(timeout=MOVE_DEADLINE_SECONDS)
        stderr = self.blocked_stderr.read_text()

        self.assertNotEqual(status, 0)
        self.assertIn('reappeared', stderr)
        self.assertIn('resolve the collision', stderr)
        self.assertFalse((self.repository / '.git' / '.git').exists(),
                         'the database was nested inside the stray directory')
        self.assertTrue((self.isolated_trees()[0] / '.git' / 'HEAD').is_file(),
                        'the database must stay isolated when the destination is occupied')

    def test_refuses_staged_changes_then_succeeds_after_clearing(self):
        self.write('shared.txt', 'staged content\n')
        self.git('add', 'shared.txt', cwd=self.repository)
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('staged changes', result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

        self.git('restore', '--staged', 'shared.txt', cwd=self.repository)
        self.run_script()
        self.assert_git_returned()

    def test_refuses_active_lock_then_succeeds_after_clearing(self):
        lock = self.repository / '.git' / 'index.lock'
        lock.write_text('')
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('Another Git process is active', result.stderr)
        self.assertEqual(self.isolated_trees(), [])

        lock.unlink()
        self.run_script()
        self.assert_git_returned()

    def test_refuses_pack_directory_lock(self):
        lock = self.repository / '.git' / 'objects' / 'pack' / 'multi-pack-index.lock'
        lock.write_text('')

        result = self.run_script(expect=1)

        self.assertIn(str(lock), result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

    def test_refuses_secondary_worktree(self):
        """A linked worktree's gitdir pointer would break while .git is displaced."""
        self.git('worktree', 'add', '--detach', str(self.root / 'linked'), cwd=self.repository)

        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('registered worktrees', result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

        self.git('worktree', 'remove', str(self.root / 'linked'), cwd=self.repository)
        self.run_script()
        self.assert_git_returned()

    def test_refuses_pending_rebase_then_succeeds_after_aborting(self):
        """The refusal must react to a real conflicted rebase, not only to a marker."""
        self.git('checkout', '-b', 'side', cwd=self.repository)
        self.write('shared.txt', 'side branch line\n')
        self.git('commit', '-am', 'Side commit', cwd=self.repository)
        self.git('checkout', 'master', cwd=self.repository)
        self.write('shared.txt', 'master line\n')
        self.git('commit', '-am', 'Master commit', cwd=self.repository)
        conflicted = self.git('rebase', 'side', cwd=self.repository, check=False)
        self.assertNotEqual(conflicted.returncode, 0, 'the fixture rebase must conflict')
        self.assertTrue((self.repository / '.git' / 'rebase-merge').is_dir())
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('already in progress', result.stderr)
        self.assertEqual(self.isolated_trees(), [])

        self.git('rebase', '--abort', cwd=self.repository)
        self.run_script()
        self.assert_git_returned()

    def test_refuses_branch_without_upstream_then_succeeds_on_a_tracked_branch(self):
        self.git('checkout', '-b', 'local-only', cwd=self.repository)
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('no upstream', result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

        self.git('checkout', 'master', cwd=self.repository)
        self.run_script()
        self.assert_git_returned()

    def test_reports_dropped_assume_unchanged_flag(self):
        self.git('update-index', '--assume-unchanged', 'flagged_changed.conf',
                 'flagged_intact.conf', cwd=self.repository)
        self.write('flagged_changed.conf', 'my hidden drift\n')
        before = self.snapshot('flagged_changed.conf')
        self.assertEqual(self.assume_unchanged(),
                         {'flagged_changed.conf', 'flagged_intact.conf'})
        self.push_upstream_change({'flagged_changed.conf': 'upstream rewrote the flagged file\n'})

        result = self.run_script()

        self.assertEqual(self.assume_unchanged(), {'flagged_intact.conf'},
                         'only the upstream-changed path should lose its flag')
        self.assertIn('flagged_changed.conf', result.stdout)
        self.assertIn('update-index --assume-unchanged', result.stdout)
        self.assertEqual(self.snapshot('flagged_changed.conf'), before,
                         'the hidden local drift was overwritten')

    def test_reports_when_no_flag_was_dropped(self):
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script()

        self.assertIn('No assume-unchanged flag was dropped', result.stdout)

    def test_clean_rebase_resolves_identity_through_home(self):
        """A local commit is replayed inside the isolated tree while the upstream
        version of the tracked .gitconfig carries no identity. It can only succeed
        because Git reads the configuration from HOME, which is the repository root
        the method never writes."""
        self.write('live.conf', 'live configuration WITH MY EDIT\n')
        before = self.snapshot('live.conf')
        self.write('local_only.txt', 'my local commit content\n')
        self.git('add', 'local_only.txt', cwd=self.repository)
        self.git('commit', '-m', 'Local commit', cwd=self.repository)
        local_subject = 'Local commit'
        upstream_commit = self.push_upstream_change({
            '.gitconfig': '[core]\n\tquotePath = false\n',
            'shared.txt': 'upstream rewrote this\n'})

        self.run_script()

        self.assert_git_returned()
        self.assert_no_pending_state()
        log = self.git('log', '--format=%s %ae %ce', '-2', 'master', cwd=self.repository).stdout
        # The committer is resolved while the rebase runs, so it is the field that
        # shows which configuration was read; the author is merely carried over.
        self.assertIn(f'{local_subject} fixture@example.invalid fixture@example.invalid', log,
                      'the replayed commit must take its committer identity from HOME')
        parents = self.git('rev-parse', 'master^', cwd=self.repository).stdout.strip()
        self.assertEqual(parents, upstream_commit,
                         'the local commit must be replayed on top of the upstream commit')
        self.assertEqual(self.snapshot('live.conf'), before)

    def test_refuses_base_on_another_mount_point(self):
        candidate = Path('/dev/shm')
        if not candidate.is_dir():
            self.skipTest('/dev/shm is absent, so no second mount point is available')
        mounts = {path: subprocess.run(['stat', '-c', '%m', str(path)], capture_output=True,
                                       text=True).stdout.strip()
                  for path in (candidate, self.repository)}
        if mounts[candidate] == mounts[self.repository]:
            self.skipTest(f'/dev/shm shares the fixture mount point {mounts[candidate]}, '
                          'so a cross-mount base cannot be built here')
        base = candidate / f'isolated-pull-fixture-{os.getpid()}'
        self.addCleanup(lambda: base.exists() and base.rmdir())

        result = subprocess.run(['bash', str(SCRIPT), '--repository', str(self.repository),
                                 '--base', str(base)], env=self.env, capture_output=True,
                                text=True)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('device and mount point', result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())

    def test_refuses_base_inside_the_database(self):
        inside = self.repository / '.git' / 'isolated'

        result = subprocess.run(['bash', str(SCRIPT), '--repository', str(self.repository),
                                 '--base', str(inside)], env=self.env, capture_output=True,
                                text=True)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('inside the repository database', result.stderr)
        self.assertFalse(inside.exists(), 'a refused base must not be created')

    def test_two_consecutive_runs_succeed(self):
        self.push_upstream_change({'shared.txt': 'first upstream change\n'}, message='First')
        self.run_script()
        second_commit = self.push_upstream_change({'shared.txt': 'second upstream change\n'},
                                                  message='Second')

        self.run_script()

        self.assert_git_returned()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         second_commit)
        self.assertEqual(len(self.isolated_trees()), 2,
                         'each run must materialize into its own directory')

    def test_clean_removes_the_isolated_tree(self):
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script('--clean')

        self.assert_git_returned()
        self.assertEqual(self.isolated_trees(), [])
        self.assertIn('Removed the isolated tree', result.stdout)

    def test_dry_run_prints_plan_and_moves_nothing(self):
        result = self.run_script('--dry-run')

        self.assertIn(str(self.base), result.stdout)
        self.assertIn('git reset --hard inside the isolated tree', result.stdout)
        self.assertIn('git pull --rebase inside the isolated tree', result.stdout)
        self.assertIn('Dry run: nothing was moved.', result.stdout)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

    def test_help_exits_zero_and_describes_the_options(self):
        result = subprocess.run(['bash', str(SCRIPT), '--help'], env=self.env,
                                capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        for option in ('--repository', '--base', '--dry-run', '--clean'):
            self.assertIn(option, result.stdout)

    def test_rejects_unknown_option(self):
        result = subprocess.run(['bash', str(SCRIPT), '--nope'], env=self.env,
                                capture_output=True, text=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn('Unknown parameter', result.stderr)


if __name__ == '__main__':
    unittest.main()
