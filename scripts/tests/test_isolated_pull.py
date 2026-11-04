"""Integration tests for a pull that shares Git metadata but preserves live files.

All mutations, including commits and rebases, use disposable repositories.
"""

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "pull_home_git_repository.sh"


class IsolatedPullTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='isolated pull test ')
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

    def isolated_trees(self):
        return sorted(path for path in self.base.iterdir() if path.is_dir())

    def assume_unchanged(self, cwd=None):
        listing = self.git('ls-files', '-v', cwd=cwd or self.repository).stdout
        return {line[2:] for line in listing.splitlines() if line.startswith('h ')}

    def snapshot(self, *relative_paths):
        return {path: (self.repository / path).read_bytes() for path in relative_paths}

    def assert_git_stays_in_place(self):
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file(),
                        'the Git directory is missing from the repository root')
        self.assertFalse((self.repository / '.git' / 'isolated-pull.lock').exists())
        self.assertFalse((self.repository / '.git' / '.git').exists(),
                         'the Git directory was nested instead of returned')
        for tree in self.isolated_trees():
            self.assertFalse((tree / '.git').exists(),
                             f'a Git directory was left behind in {tree}')

    def assert_no_pending_state(self):
        for marker in ('rebase-merge', 'rebase-apply', 'MERGE_HEAD', 'index.lock'):
            self.assertFalse((self.repository / '.git' / marker).exists(),
                             f'.git/{marker} remains after the operation')

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

    def test_fast_forward_preserves_database_and_live_files(self):
        self.write('live.conf', 'live configuration version 1 WITH MY EDIT\n')
        self.write('untracked.txt', 'my untracked work\n')
        self.write('future.txt', 'my local file before upstream tracks this path\n')
        (self.repository / 'flagged_intact.conf').unlink()
        before = self.snapshot('live.conf', 'untracked.txt', 'shared.txt')
        upstream_commit = self.push_upstream_change({
            'shared.txt': 'upstream rewrote this\n', 'future.txt': 'new upstream file\n'})

        result = self.run_script()

        self.assert_git_stays_in_place()
        self.assert_no_pending_state()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         upstream_commit)
        self.assertEqual(self.snapshot('live.conf', 'untracked.txt', 'shared.txt'), before,
                         'the repository work tree was written')
        self.assertFalse((self.repository / 'flagged_intact.conf').exists())
        self.assertEqual((self.repository / 'future.txt').read_text(),
                         'my local file before upstream tracks this path\n')
        self.assertEqual(self.git('diff', '--cached', '--name-only',
                                  cwd=self.repository).stdout, '')
        tree = self.isolated_trees()[0]
        self.assertEqual((tree / 'shared.txt').read_text(), 'upstream rewrote this\n')
        self.assertIn('Pull completed', result.stdout)

    def test_failed_pull_preserves_database_and_live_files(self):
        self.write('live.conf', 'live configuration WITH MY EDIT\n')
        before = self.snapshot('live.conf')
        self.origin.rename(self.root / 'origin.git.away')

        result = self.run_script(expect=1)

        self.assert_git_stays_in_place()
        self.assert_no_pending_state()
        self.assertIn('git pull --rebase failed', result.stderr)
        self.assertEqual(self.snapshot('live.conf'), before)

    def test_conflicting_rebase_aborts_in_temporary_tree(self):
        self.write('shared.txt', 'my local commit line\n')
        self.git('add', 'shared.txt', cwd=self.repository)
        self.git('commit', '-m', 'Local commit', cwd=self.repository)
        local_tip = self.git('rev-parse', 'master', cwd=self.repository).stdout.strip()
        self.write('live.conf', 'live configuration WITH MY EDIT\n')
        before = self.snapshot('live.conf')
        self.push_upstream_change({'shared.txt': 'upstream rewrote the same line\n'})

        result = self.run_script(expect=1)

        self.assert_git_stays_in_place()
        self.assert_no_pending_state()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         local_tip, 'the local commit was not preserved at its original tip')
        self.assertEqual(self.git('rev-parse', '--abbrev-ref', 'HEAD',
                                  cwd=self.repository).stdout.strip(), 'master')
        self.assertEqual(self.snapshot('live.conf'), before)
        self.assertIn('failed', result.stderr)

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
        self.assert_git_stays_in_place()

    def test_refuses_active_lock_then_succeeds_after_clearing(self):
        lock = self.repository / '.git' / 'index.lock'
        lock.write_text('')
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('A Git lock exists', result.stderr)
        self.assertTrue(lock.is_file(), 'the helper must not remove another process lock')
        self.assertEqual(self.isolated_trees(), [])

        lock.unlink()
        self.run_script()
        self.assert_git_stays_in_place()

    def test_refuses_pack_directory_lock(self):
        lock = self.repository / '.git' / 'objects' / 'pack' / 'multi-pack-index.lock'
        lock.write_text('')

        result = self.run_script(expect=1)

        self.assertIn(str(lock), result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

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
        self.assert_git_stays_in_place()

    def test_refuses_branch_without_upstream_then_succeeds_on_a_tracked_branch(self):
        self.git('checkout', '-b', 'local-only', cwd=self.repository)
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script(expect=1)

        self.assertIn('no upstream', result.stderr)
        self.assertTrue((self.repository / '.git' / 'HEAD').is_file())
        self.assertEqual(self.isolated_trees(), [])

        self.git('checkout', 'master', cwd=self.repository)
        self.run_script()
        self.assert_git_stays_in_place()

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
        self.assertIn('not reapplied', result.stdout)
        self.assertEqual(self.snapshot('flagged_changed.conf'), before,
                         'the hidden local drift was overwritten')

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

        self.assert_git_stays_in_place()
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

        self.assert_git_stays_in_place()
        self.assertEqual(self.git('rev-parse', 'master', cwd=self.repository).stdout.strip(),
                         second_commit)
        self.assertEqual(len(self.isolated_trees()), 2,
                         'each run must materialize into its own directory')

    def test_clean_removes_the_isolated_tree(self):
        self.push_upstream_change({'live.conf': 'upstream live configuration\n'})

        result = self.run_script('--clean')

        self.assert_git_stays_in_place()
        self.assertEqual(self.isolated_trees(), [])
        self.assertIn('Removed the isolated tree', result.stdout)

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

    def wrap_git(self, body):
        directory = self.root / 'git-wrapper'
        directory.mkdir()
        wrapper = directory / 'git'
        wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\n' + body + '\n'
                           f'exec {shlex.quote(shutil.which("git"))} "$@"\n')
        wrapper.chmod(0o755)
        return dict(self.env, PATH=f'{directory}{os.pathsep}{self.env["PATH"]}')

    def test_database_remains_at_original_path_during_pull(self):
        observed = self.root / 'database-observed'
        env = self.wrap_git(
            'if [[ " $* " == *" pull --rebase "* ]]; then\n'
            f'    [[ -f {shlex.quote(str(self.repository / ".git/HEAD"))} ]] || {{\n'
            '        printf "Original database missing during pull\\n" >&2\n'
            '        exit 88\n'
            '    }\n'
            f'    : > {shlex.quote(str(observed))}\n'
            'fi')
        self.write('live.conf', 'my live edit\n')
        before = self.snapshot('live.conf', 'shared.txt', '.gitconfig')
        tip = self.push_upstream_change({'shared.txt': 'upstream version\n'})

        self.run_script(env=env)

        self.assertTrue(observed.exists())
        self.assertEqual(self.snapshot('live.conf', 'shared.txt', '.gitconfig'), before,
                         'the original work tree changed during pull')
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repository).stdout.strip(), tip)
        self.assert_git_stays_in_place()

    def test_failed_abort_retains_tree_and_original_database_for_recovery(self):
        self.write('shared.txt', 'local committed line\n')
        self.git('commit', '-am', 'Local commit', cwd=self.repository)
        tip = self.git('rev-parse', 'HEAD', cwd=self.repository).stdout.strip()
        self.push_upstream_change({'shared.txt': 'upstream conflicting line\n'})
        self.write('live.conf', 'live edit\n')
        before = self.snapshot('live.conf', 'shared.txt')

        result = self.run_script('--clean', expect=1, env=self.fail_isolated_abort())

        self.assert_git_stays_in_place()
        self.assertTrue((self.repository / '.git/rebase-merge').is_dir())
        self.assertIn('--work-tree=', result.stderr)
        self.assertIn('rebase --abort', result.stderr)
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        tree = self.isolated_trees()[0]
        self.run_script(expect=1)
        self.git(f'--git-dir={self.repository / ".git"}', f'--work-tree={tree}',
                 'rebase', '--abort', cwd=self.repository)
        self.assert_no_pending_state()
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repository).stdout.strip(), tip)
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)

    def test_signal_after_reset_keeps_database_and_temporary_files(self):
        before = self.snapshot('live.conf', 'shared.txt')
        env = self.wrap_git(
            'if [[ " $* " == *" reset --hard "* ]]; then\n'
            f'    {shlex.quote(shutil.which("git"))} "$@"\n'
            '    kill -TERM "$PPID"\n'
            '    exit 0\n'
            'fi')

        result = self.run_script('--clean', expect=143, env=env)

        self.assertIn('kept', result.stderr)
        self.assert_git_stays_in_place()
        self.assert_no_pending_state()
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        self.assertEqual((self.isolated_trees()[0] / 'live.conf').read_text(),
                         'live configuration version 1\n')
        self.assertFalse((self.repository / '.git/isolated-pull.lock').exists())

    def test_wrong_worktree_report_blocks_reset_without_changing_index(self):
        before = self.snapshot('live.conf', 'shared.txt')
        index_before = (self.repository / '.git/index').read_bytes()
        env = self.wrap_git(
            'if [[ " $* " == *" rev-parse --show-toplevel "* ]]; then\n'
            f'    printf "%s\\n" {shlex.quote(str(self.repository))}\n'
            '    exit 0\n'
            'fi')

        result = self.run_script(expect=1, env=env)

        self.assertIn('isolated tree', result.stderr)
        self.assertEqual((self.repository / '.git/index').read_bytes(), index_before)
        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        self.assertEqual(list(self.isolated_trees()[0].iterdir()), [])

    def test_failed_path_query_with_valid_output_blocks_reset(self):
        before = self.snapshot('live.conf', 'shared.txt')
        env = self.wrap_git(
            'if [[ " $* " == *" rev-parse --show-toplevel "* ]]; then\n'
            f'    {shlex.quote(shutil.which("git"))} "$@"\n'
            '    exit 73\n'
            'fi')

        self.run_script(expect=73, env=env)

        self.assertEqual(self.snapshot('live.conf', 'shared.txt'), before)
        self.assertEqual(list(self.isolated_trees()[0].iterdir()), [])

    def test_equivalent_native_directory_spelling_is_accepted(self):
        tip = self.push_upstream_change({'shared.txt': 'upstream content\n'})
        env = self.wrap_git(
            'if [[ " $* " == *" rev-parse --show-toplevel "* ]] || '
            '[[ " $* " == *" rev-parse --absolute-git-dir "* ]]; then\n'
            f'    REPORTED="$({shlex.quote(shutil.which("git"))} "$@")"\n'
            '    printf "%s/.\\n" "$REPORTED"\n'
            '    exit 0\n'
            'fi')

        self.run_script(env=env)

        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repository).stdout.strip(), tip)
        self.assert_git_stays_in_place()

    def test_dry_run_leaves_git_state_and_missing_base_unchanged(self):
        self.base.rmdir()
        index_before = (self.repository / '.git/index').read_bytes()

        result = self.run_script('--dry-run')

        self.assertIn('git reset --hard', result.stdout)
        self.assertIn('git pull --rebase', result.stdout)
        self.assertFalse(self.base.exists())
        self.assertEqual((self.repository / '.git/index').read_bytes(), index_before)
        self.assertFalse((self.repository / '.git/isolated-pull.lock').exists())

    def test_default_repository_uses_script_location_not_home(self):
        copied = self.repository / 'scripts/pull_home_git_repository.sh'
        copied.parent.mkdir()
        shutil.copyfile(SCRIPT, copied)
        other_home = self.root / 'different-home'
        other_home.mkdir()

        result = subprocess.run(['bash', str(copied), '--dry-run'], cwd=str(self.root),
                                env=dict(self.env, HOME=str(other_home)),
                                capture_output=True, text=True, timeout=60)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.repository), result.stdout)
        self.assertFalse((self.repository / '.local').exists())

    def test_inherited_index_override_is_refused(self):
        other_index = self.root / 'other-index'
        other_index.write_bytes(b'preserve this file')

        result = self.run_script(expect=1, env=dict(self.env, GIT_INDEX_FILE=str(other_index)))

        self.assertIn('GIT_INDEX_FILE', result.stderr)
        self.assertEqual(other_index.read_bytes(), b'preserve this file')
        self.assertEqual(self.isolated_trees(), [])

    def test_existing_helper_lock_is_not_removed(self):
        lock = self.repository / '.git/isolated-pull.lock'
        lock.mkdir()

        result = self.run_script(expect=1)

        self.assertIn('lock', result.stderr)
        self.assertTrue(lock.is_dir())
        self.assertEqual(self.isolated_trees(), [])

    def test_rebase_disables_hooks_and_does_not_update_other_branches(self):
        self.write('local.txt', 'local commit\n')
        self.git('add', 'local.txt', cwd=self.repository)
        self.git('commit', '-m', 'Local commit', cwd=self.repository)
        old_tip = self.git('rev-parse', 'HEAD', cwd=self.repository).stdout.strip()
        self.git('branch', 'untouched', cwd=self.repository)
        self.git('config', 'rebase.updateRefs', 'true', cwd=self.repository)
        self.push_upstream_change({'shared.txt': 'remote change\n'})
        hook = self.repository / '.git/hooks/pre-rebase'
        hook.write_text('#!/usr/bin/env bash\n'
                        f'printf "OVERWRITTEN\\n" > {shlex.quote(str(self.repository / "live.conf"))}\n'
                        'exit 74\n')
        hook.chmod(0o755)
        before = self.snapshot('live.conf', 'local.txt', 'shared.txt')

        self.run_script()

        self.assertEqual(self.snapshot('live.conf', 'local.txt', 'shared.txt'), before)
        self.assertEqual(self.git('rev-parse', 'untouched', cwd=self.repository).stdout.strip(),
                         old_tip)
        self.assert_no_pending_state()


if __name__ == '__main__':
    unittest.main()
