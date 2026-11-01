"""The actual cold-start editor preserves unrelated TOML and refuses uncertain writes."""
import builtins
import copy
import math
import os
from pathlib import Path
import runpy
import stat
import subprocess
import sys
import tempfile
import tomllib

import pytest

CLI = Path(os.environ.get('CODEX_MONITOR_TEST_CLI',
    Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats'))
FALSE = '''# User comment stays here.
model = "fixture-model" # Leave this model alone.
unrelated = { enabled = false, retries = 3 }
empty = {}
[features] # Keep the feature heading.
code_mode_host = false # Only this value changes.
other_feature = false
[plugins."codex-app-tools@openai-bundled".mcp_servers.codex_app]
enabled = false # Preserve app comment.
[plugins."code-review@openai-bundled".mcp_servers.code-review]
enabled = false
[mcp_servers.external]
command = 'unchanged-tool'
args = [ "one", 'two' ]
'''
TRUE = FALSE.replace('code_mode_host = false', 'code_mode_host = true').replace(
    'enabled = false # Preserve app comment.', 'enabled = true # Preserve app comment.').replace(
    '[plugins."code-review@openai-bundled".mcp_servers.code-review]\nenabled = false',
    '[plugins."code-review@openai-bundled".mcp_servers.code-review]\nenabled = true')


@pytest.fixture
def editor(monkeypatch):
    module = runpy.run_path(str(CLI))['monitor_launcher']()
    with tempfile.TemporaryDirectory(prefix='cm-bootstrap-') as name:
        root = Path(name)
        home, runtime = root/'codex', root/'run'
        home.mkdir(mode=0o700); runtime.mkdir(mode=0o700)
        monkeypatch.setenv('XDG_RUNTIME_DIR', str(runtime))
        alias = home/'app-server-control/app-server-control.sock'
        config = {'codex_home':str(home), '_socket_alias':str(alias), 'socket':str(alias),
                  'state_file':str(root/'monitor/state.sqlite3')}
        target = home/'config.toml'
        target.write_text(FALSE); target.chmod(0o640)
        factory = lambda: module['cold']()['MonitorColdStart'](config, [sys.executable])
        yield module, root, target, factory


def prepared(module, original):
    expected = copy.deepcopy(original)
    for path in module['MONITOR_BOOTSTRAP_OPTIONS']:
        table = expected
        for name in path[:-1]:
            table = table.setdefault(name, {})
        table[path[-1]] = True
    return expected


def outputs(target):
    return sorted(path.name for path in target.parent.iterdir() if path.name.startswith(
        ('config.toml.before-monitor-', '.config.toml.codex-monitor-')))


def test_false_flags_only_changes_values_preserves_format_and_exact_private_backup(editor):
    module, _, target, factory = editor
    before = target.read_bytes()
    group = target.stat().st_gid
    with factory() as authority:
        result = module['monitor_prepare_bootstrap'](authority)
        assert result['changed'] is True
        assert target.read_text() == TRUE
        assert tomllib.loads(target.read_text()) == prepared(module, tomllib.loads(FALSE))
        backup = Path(result['backup'])
        assert backup.read_bytes() == before
        assert stat.S_IMODE(backup.stat().st_mode) == 0o600
        assert backup.stat().st_nlink == 1
        assert stat.S_IMODE(target.stat().st_mode) == 0o640
        assert target.stat().st_gid == group
        assert outputs(target) == [backup.name]
        identity = target.stat(), target.read_bytes()
        assert module['monitor_prepare_bootstrap'](authority) == {'changed':False, 'backup':None}
        assert (target.stat(), target.read_bytes()) == identity
        assert outputs(target) == [backup.name]


@pytest.mark.parametrize('contents', [b'# Preserve header\r\nmodel = "fixture"\r\n',
                                     b'features = { other = false }\n',
                                     b'[empty]\n', b''])
def test_missing_options_are_added_without_losing_existing_tables(editor, contents):
    module, _, target, factory = editor
    target.write_bytes(contents)
    with factory() as authority:
        result = module['monitor_prepare_bootstrap'](authority)
    assert Path(result['backup']).read_bytes() == contents
    assert tomllib.loads(target.read_text()) == prepared(module, tomllib.loads(contents.decode()))
    if contents.startswith(b'# Preserve'):
        assert target.read_bytes().startswith(contents)


def test_missing_file_is_created_private_without_fabricating_backup(editor):
    module, _, target, factory = editor
    target.unlink()
    with factory() as authority:
        assert module['monitor_prepare_bootstrap'](authority) == {'changed':True, 'backup':None}
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert tomllib.loads(target.read_text()) == prepared(module, {})
    assert outputs(target) == []


def test_noop_and_unrelated_cli_help_do_not_import_optional_editor(editor, monkeypatch):
    module, _, target, factory = editor
    target.write_text(TRUE)
    before = target.read_bytes(), target.stat()
    original = builtins.__import__
    def unavailable(name, *args, **kwargs):
        if name == 'tomlkit':
            raise AssertionError('no-op imported the optional editor')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', unavailable)
    with factory() as authority:
        assert module['monitor_prepare_bootstrap'](authority) == {'changed':False, 'backup':None}
    assert (target.read_bytes(), target.stat()) == before
    assert outputs(target) == []
    monkeypatch.setattr(sys, 'argv', [str(CLI), '--help'])
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(CLI), run_name='__main__')
    assert result.value.code == 0


def test_missing_optional_editor_is_actionable_without_touching_config(editor, monkeypatch):
    module, _, target, factory = editor
    before = target.read_bytes(), target.stat()
    original = builtins.__import__
    def unavailable(name, *args, **kwargs):
        if name == 'tomlkit':
            raise ImportError('controlled absent dependency')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', unavailable)
    with factory() as authority:
        with pytest.raises(RuntimeError, match='poetry install --with monitor-tools'):
            module['monitor_prepare_bootstrap'](authority)
    assert (target.read_bytes(), target.stat()) == before
    assert outputs(target) == []


@pytest.mark.parametrize('contents', ['invalid = [', '[features]\ncode_mode_host = "false"\n',
                                    'features = false\n', 'plugins = []\n'])
def test_invalid_toml_or_option_types_refuse_without_writes(editor, contents):
    module, _, target, factory = editor
    target.write_text(contents)
    before = target.read_bytes(), target.stat()
    with factory() as authority:
        with pytest.raises((ValueError, RuntimeError)):
            module['monitor_prepare_bootstrap'](authority)
    assert (target.read_bytes(), target.stat()) == before
    assert outputs(target) == []


@pytest.mark.parametrize('unsafe', ['symlink', 'hardlink', 'writable'])
def test_unsafe_file_refuses_and_preserves_target(editor, unsafe):
    module, root, target, factory = editor
    other = root/'original'
    if unsafe in {'symlink', 'hardlink'}:
        target.rename(other)
        if unsafe == 'symlink':target.symlink_to(other)
        else:os.link(other, target)
    else:target.chmod(0o660)
    def image():
        contents = target.read_bytes()
        metadata = target.lstat()
        # Following a symbolic link can update its access time without a write.
        return contents, tuple(getattr(metadata, field) for field in (
            'st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    before = image()
    with factory() as authority:
        with pytest.raises((OSError, RuntimeError)):
            module['monitor_prepare_bootstrap'](authority)
    assert image() == before
    assert outputs(target) == []


def test_editor_cannot_replace_real_authority_with_a_callback(editor):
    module, _, target, factory = editor
    before = target.read_bytes(), target.stat()
    with pytest.raises(RuntimeError, match='requires the shared cold-start authority'):
        module['monitor_prepare_bootstrap'](lambda: True)
    with factory() as authority:
        authority.before_native_start()
        with pytest.raises(RuntimeError, match='exclusion is not held'):
            module['monitor_prepare_bootstrap'](authority)
    assert (target.read_bytes(), target.stat()) == before


def test_observed_concurrent_edit_is_preserved_before_backup_or_publication(editor, monkeypatch):
    import tomlkit
    module, _, target, factory = editor
    original = tomlkit.dumps
    external = b'# Concurrent owner edit\nmodel = "other-owner"\n'
    def concurrent(document):
        result = original(document)
        target.write_bytes(external)
        return result
    monkeypatch.setattr(tomlkit, 'dumps', concurrent)
    with factory() as authority:
        with pytest.raises(RuntimeError, match='changed concurrently'):
            module['monitor_prepare_bootstrap'](authority)
    assert target.read_bytes() == external
    assert outputs(target) == []


def test_semantic_roundtrip_rejects_unrelated_data_change(editor, monkeypatch):
    import tomlkit
    module, _, target, factory = editor
    before = target.read_bytes(), target.stat()
    original = tomlkit.dumps
    monkeypatch.setattr(tomlkit, 'dumps', lambda doc: original(doc).replace('fixture-model', 'altered-model'))
    with factory() as authority:
        with pytest.raises(RuntimeError, match='beyond the three approved'):
            module['monitor_prepare_bootstrap'](authority)
    assert (target.read_bytes(), target.stat()) == before
    assert outputs(target) == []


def test_edit_after_backup_is_preserved_and_backup_keeps_original(editor, monkeypatch):
    module, _, target, factory = editor
    original_bytes = target.read_bytes()
    external = b'# Later concurrent edit\nmodel = "later-owner"\n'
    original_fsync = os.fsync
    changed = False
    def concurrent(descriptor):
        nonlocal changed
        original_fsync(descriptor)
        path = Path('/proc/self/fd')/str(descriptor)
        if path.resolve().name.startswith('config.toml.before-monitor-'):
            target.write_bytes(external)
            changed = True
    monkeypatch.setattr(os, 'fsync', concurrent)
    with factory() as authority:
        with pytest.raises(RuntimeError, match='changed concurrently'):
            module['monitor_prepare_bootstrap'](authority)
    assert changed
    assert target.read_bytes() == external
    names = outputs(target)
    assert len(names) == 1 and names[0].startswith('config.toml.before-monitor-')
    assert (target.parent/names[0]).read_bytes() == original_bytes


def test_new_native_start_during_formatting_prevents_publication(editor, monkeypatch):
    import tomlkit
    module, _, target, factory = editor
    before = target.read_bytes(), target.stat()
    original = tomlkit.dumps
    child = None
    def concurrent(document):
        nonlocal child
        child = subprocess.Popen([sys.executable, '-u', '-c',
            'import time;print("ready",flush=True);time.sleep(20)', 'app-server'],
            env={**os.environ, 'CODEX_HOME':str(target.parent)},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert child.stdout.readline() == 'ready\n'
        return original(document)
    monkeypatch.setattr(tomlkit, 'dumps', concurrent)
    try:
        with factory() as authority:
            with pytest.raises(RuntimeError, match='app-server start is live or pending'):
                module['monitor_prepare_bootstrap'](authority)
        assert (target.read_bytes(), target.stat()) == before
        assert outputs(target) == []
    finally:
        if child is not None:
            child.terminate(); child.wait(timeout=5)
            child.stdout.close(); child.stderr.close()


def test_atomic_replace_failure_keeps_original_and_backup_and_removes_temporary(editor, monkeypatch):
    module, _, target, factory = editor
    before = target.read_bytes(), target.stat()
    original = os.replace
    def fail(source, destination):
        if Path(destination) == target:
            raise OSError('controlled failed publication')
        return original(source, destination)
    monkeypatch.setattr(os, 'replace', fail)
    with factory() as authority:
        with pytest.raises(OSError, match='controlled failed publication'):
            module['monitor_prepare_bootstrap'](authority)
    assert (target.read_bytes(), target.stat()) == before
    names = outputs(target)
    assert len(names) == 1 and names[0].startswith('config.toml.before-monitor-')
    assert (target.parent/names[0]).read_bytes() == before[0]


def test_unrelated_nan_and_dates_survive_semantic_comparison(editor):
    module, _, target, factory = editor
    target.write_text(FALSE + '\n[unrelated_values]\nnan_value = nan\ndate = 2026-10-31\n')
    with factory() as authority:
        module['monitor_prepare_bootstrap'](authority)
    values = tomllib.loads(target.read_text())['unrelated_values']
    assert math.isnan(values['nan_value'])
    assert str(values['date']) == '2026-10-31'
