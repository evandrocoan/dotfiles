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
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/isolated_pull.sh'
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

    def start_blocked_script(self, *args, script=None):
        """Start a run whose fetch blocks, so signals arrive mid-pull."""
        fake_ssh = self.root / 'fake_ssh.sh'
        self.transport_marker = self.root / 'transport-started'
        fake_ssh.write_text(f'#!/usr/bin/env bash\n: > "{self.transport_marker}"\n'
                            f'sleep {BLOCKING_SLEEP_SECONDS}\n')
        fake_ssh.chmod(0o755)
        self.git('remote', 'set-url', 'origin', 'ssh://fixture.invalid/repository',
                 cwd=self.repository)
        env = dict(self.env, GIT_SSH_COMMAND=str(fake_ssh))
        # The blocked transport outlives the script and inherits its output, so
        # files are used instead of pipes: waiting for pipe EOF would wait for
        # the sleeping transport rather than for the script's own exit.
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

    def process_is_alive(self, pid):
        deadline = time.monotonic() + MOVE_DEADLINE_SECONDS
        while time.monotonic() < deadline:
            if not Path(f'/proc/{pid}').exists():
                return False
            time.sleep(0.05)
        return True

    def command_line(self, pid):
        return Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\x00')

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

    def test_pull_runs_as_a_direct_git_child(self):
        """The exit handler can only stop the process that holds the database if
        the backgrounded pull is git itself. Backgrounding a shell function would
        make it a subshell wrapper, so terminating that wrapper would leave git
        running while .git moves."""
        process = self.start_blocked_script()

        children = self.direct_children(process.pid)

        self.assertEqual([command for _, command in children], ['git'],
                         f'the pull must be a direct git child, got {children}')
        self.assertIn('pull', self.command_line(children[0][0]),
                      'the direct git child must be the pull itself')

    def test_negative_control_subshell_wrapped_pull_is_detected(self):
        """Proves the assertion above detects the subshell form it forbids."""
        wrapped = self.root / 'isolated_pull_wrapped.sh'
        source = SCRIPT.read_text()
        marker = 'git "${ISOLATED_GIT_ARGUMENTS[@]}" pull --rebase &'
        self.assertIn(marker, source)
        wrapped.write_text(source.replace(marker, 'isolatedgit pull --rebase &'))
        process = self.start_blocked_script(script=wrapped)

        children = self.direct_children(process.pid)

        self.assertEqual([command for _, command in children], ['bash'],
                         f'the subshell form should show a shell wrapper, got {children}')

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

    def test_return_collision_is_refused_instead_of_nested(self):
        process = self.start_blocked_script()
        (self.repository / '.git').mkdir()

        process.terminate()
        status = process.wait(timeout=MOVE_DEADLINE_SECONDS)
        stderr = self.blocked_stderr.read_text()

        self.assertNotEqual(status, 0)
        self.assertIn('reappeared', stderr)
        self.assertIn('Recover with', stderr)
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
