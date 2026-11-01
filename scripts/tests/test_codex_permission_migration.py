"""Exact migration mapping and real source/absence/consumer boundaries."""
import copy
import errno
import importlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
import stat
import subprocess
import sys
import tomllib

import pytest


@pytest.fixture
def migration(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    return importlib.import_module('codex_permission_migration')


SOURCE = b'''# user preference
sandbox_mode = "workspace-write" # old mode
approval_policy = { granular = { sandbox_approval = true, rules = true, request_permissions = true, mcp_elicitations = true, skill_approval = true } }
secret = "SENTINEL-DO-NOT-PRINT"
[features]
code_mode_host = true
# legacy CLI compatibility
[sandbox_workspace_write]
network_access = true # direct network
[permissions.existing]
extends = ":read-only"
[permissions.existing.filesystem]
"/example" = "write"
'''


@pytest.mark.parametrize('layout', ['table', 'inline', 'dotted'])
def test_exact_transform_preserves_existing_profiles_approvals_and_comments(migration, layout):
    source = SOURCE
    network = (b'# legacy CLI compatibility\n[sandbox_workspace_write]\n'
               b'network_access = true # direct network\n')
    if layout != 'table':
        declarations = {
            'inline': b'sandbox_workspace_write = { network_access = true } # direct network\n',
            'dotted': b'sandbox_workspace_write.network_access = true # direct network\n',
        }
        source = source.replace(network, b'').replace(
            b'[features]\n', b'# legacy CLI compatibility\n' + declarations[layout] + b'[features]\n')
    output = migration.transform(source)
    old, new = tomllib.loads(source.decode()), tomllib.loads(output.decode())
    assert new['default_permissions'] == 'local-workspace'
    assert new['permissions']['local-workspace'] == {'extends': ':workspace', 'network': {'enabled': True}}
    assert new['sandbox_workspace_write'] == {'network_access': True}
    del new['default_permissions'], new['permissions']['local-workspace']
    del old['sandbox_mode']
    assert new == old
    assert b'# user preference' in output
    assert b'# legacy CLI compatibility' in output
    assert b'# direct network' in output
    assert b'network_proxy' not in output
    assert b'SENTINEL-DO-NOT-PRINT' in output


@pytest.mark.parametrize('network', [
    b'network_access = false',
    b'network_access = 1',
    b'network_access = true\nexclude_tmpdir_env_var = true',
])
def test_unreviewed_legacy_network_shape_is_refused(migration, network):
    source = SOURCE.replace(b'network_access = true # direct network', network)
    with pytest.raises(RuntimeError, match='formato aprovado'):
        migration.transform(source)


@pytest.mark.parametrize('change', [
    b'sandbox_mode = "read-only"',
    b'sandbox_mode = "workspace-write"\ndefault_permissions = "other"',
    b'sandbox_mode = "workspace-write"\n[permissions.local-workspace]\nextends = ":workspace"',
    b'sandbox_mode = "workspace-write"\n[profiles.other]\nmodel = "other"',
])
def test_unreviewed_source_shape_is_refused(migration, change):
    with pytest.raises(RuntimeError, match='formato aprovado'):
        migration.transform(change + b'\n[sandbox_workspace_write]\nnetwork_access = true\n')


@pytest.fixture
def shape(tmp_path):
    home = tmp_path / 'codex'
    home.mkdir(mode=0o700)
    work = tmp_path / 'work'
    work.mkdir(mode=0o700)
    target = home / 'config.toml'
    target.write_bytes(SOURCE)
    target.chmod(0o600)
    name = {'type': 'user', 'file': str(target), 'profile': None}
    user = {'name': name, 'version': 'sha256:test', 'config': tomllib.loads(SOURCE.decode())}
    system = {'name': {'type': 'system', 'file': '/etc/codex/config.toml'},
              'version': 'sha256:empty', 'config': {}}
    report = {'layers': [user, system], 'origins': {'sandbox_mode': {'name': name}}}
    return home, work, target, report


def test_inventory_rechecks_real_absent_and_present_sources(migration, shape):
    home, work, target, report = shape
    original = migration.inventory(home, [work], [report], {'requirements': None})
    migration.revalidate_inventory(original, home, [work], [report], {'requirements': None})
    # Both the previously missing directory and a new project policy invalidate the seal.
    (work / '.codex').mkdir(mode=0o700)
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate(original['sources'])
    (work / '.codex/config.toml').write_text('sandbox_mode = "read-only"\n')
    (work / '.codex/config.toml').chmod(0o600)
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate(original['sources'])
    assert target.read_bytes() == SOURCE


def test_same_bytes_with_new_file_identity_invalidate_inventory(migration, shape):
    home, work, target, report = shape
    original = migration.inventory(home, [work], [report], {'requirements': None})
    replacement = home / 'other'
    replacement.write_bytes(SOURCE)
    replacement.chmod(0o600)
    replacement.replace(target)
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate(original['sources'])


@pytest.mark.parametrize('kind', ['enterpriseManaged', 'mdm', 'packagedDefaults', 'future'])
def test_unknown_and_unbound_managed_layers_refuse_inventory(migration, shape, kind):
    home, work, _, report = shape
    report['layers'].insert(0, {'name': {'type': kind}, 'version': 'new', 'config': {}})
    with pytest.raises(RuntimeError, match='desconhecida ou não vinculável'):
        migration.inventory(home, [work], [report], {'requirements': None})


def test_changed_requirements_and_session_policy_cannot_be_hidden(migration, shape):
    home, work, _, report = shape
    with pytest.raises(RuntimeError, match='requisitos gerenciados'):
        migration.inventory(home, [work], [report], {'requirements': {}})
    report['layers'].insert(0, {'name': {'type': 'sessionFlags'}, 'version': 'flags',
                               'config': {'sandbox_mode': 'danger-full-access'}})
    with pytest.raises(RuntimeError, match='opções de sessão'):
        migration.inventory(home, [work], [report], {'requirements': None})


def test_source_changed_since_native_read_is_refused(migration, shape):
    home, work, target, report = shape
    target.write_bytes(SOURCE.replace(b'workspace-write', b'read-only'))
    with pytest.raises(RuntimeError, match='não corresponde'):
        migration.inventory(home, [work], [report], {'requirements': None})


@pytest.mark.parametrize('source_value, native_value', [(30, 30.0), (30.0, 30), (0, -0.0)])
def test_inventory_accepts_equal_native_numbers(migration, shape, source_value, native_value):
    home, work, target, report = shape
    source = SOURCE + ('\n[mcp_servers.fixture]\nstartup_timeout_sec = '
                       + json.dumps(source_value) + '\n').encode()
    target.write_bytes(source)
    report['layers'][0]['config'] = tomllib.loads(source.decode())
    report['layers'][0]['config']['mcp_servers']['fixture']['startup_timeout_sec'] = native_value
    before = target.read_bytes(), target.stat()
    inventory = migration.inventory(home, [work], [report], {'requirements': None})
    migration.revalidate_inventory(inventory, home, [work], [report], {'requirements': None})
    assert (target.read_bytes(), target.stat()) == before
    # The independent exact-transform/source seals must stay representation-sensitive.
    assert migration.semantic(tomllib.loads(source.decode())) != migration.semantic(report['layers'][0]['config'])


@pytest.mark.parametrize('source_value, native_value', [
    (30, 30.5), (2 ** 53 + 1, float(2 ** 53 + 1)), (1, True), (0, False), ('30', 30.0),
])
def test_inventory_refuses_different_native_numbers_and_types(migration, shape, source_value, native_value):
    home, work, target, report = shape
    source = SOURCE + ('\n[mcp_servers.fixture]\nstartup_timeout_sec = '
                       + json.dumps(source_value) + '\n').encode()
    target.write_bytes(source)
    report['layers'][0]['config'] = tomllib.loads(source.decode())
    report['layers'][0]['config']['mcp_servers']['fixture']['startup_timeout_sec'] = native_value
    with pytest.raises(RuntimeError, match='não corresponde'):
        migration.inventory(home, [work], [report], {'requirements': None})
    assert target.read_bytes() == source


@pytest.fixture
def native_paths_shape(shape):
    home, work, target, report = shape
    source = SOURCE + b'''\n[skills]
config = [{ path = "skills/fixture/SKILL.md", enabled = false }]
description = "skills/fixture/SKILL.md"
'''
    target.write_bytes(source)
    report['layers'][0]['config'] = tomllib.loads(source.decode())
    report['layers'][0]['config']['skills']['config'][0]['path'] = str(home / 'skills/fixture/SKILL.md')
    return shape


def test_inventory_resolves_skill_paths_from_declaring_config(migration, native_paths_shape):
    home, work, target, report = native_paths_shape
    before = target.read_bytes(), target.stat(), copy.deepcopy(report)
    inventory = migration.inventory(home, [work], [report], {'requirements': None})
    migration.revalidate_inventory(inventory, home, [work], [report], {'requirements': None})
    assert (target.read_bytes(), target.stat(), report) == before
    assert inventory['reports'][0]['layers'][0]['config']['skills']['config'][0]['path'] == str(
        home / 'skills/fixture/SKILL.md')


@pytest.mark.parametrize('changed', ['cwd_base', 'different_path', 'untyped_string', 'enabled_type'])
def test_inventory_refuses_other_skill_changes(migration, native_paths_shape, changed):
    home, work, target, report = native_paths_shape
    skills = report['layers'][0]['config']['skills']
    if changed == 'cwd_base':
        skills['config'][0]['path'] = str(work / 'skills/fixture/SKILL.md')
    elif changed == 'different_path':
        skills['config'][0]['path'] = str(home / 'skills/other/SKILL.md')
    elif changed == 'untyped_string':
        skills['description'] = str(home / 'skills/fixture/SKILL.md')
    else:
        skills['config'][0]['enabled'] = 0
    before = target.read_bytes()
    with pytest.raises(RuntimeError, match='não corresponde'):
        migration.inventory(home, [work], [report], {'requirements': None})
    assert target.read_bytes() == before


@pytest.mark.parametrize('unsafe, expected_error', [('symlink', OSError), ('hardlink', RuntimeError)])
def test_unsafe_source_witness_refused(migration, tmp_path, unsafe, expected_error):
    target = tmp_path / 'source'
    target.write_text('secret')
    target.chmod(0o600)
    if unsafe == 'symlink':
        alias = tmp_path / 'alias'
        alias.symlink_to(target)
        target = alias
    else:
        os.link(target, tmp_path / 'alias')
    with pytest.raises(expected_error) as caught:
        migration.witness(target)
    if unsafe == 'symlink':
        assert caught.value.errno == errno.ELOOP
    else:
        assert str(caught.value) == 'origem insegura de configuração'


@pytest.mark.parametrize('directory_mode, file_mode', [
    (0o755, 0o664), (0o755, 0o666), (0o775, 0o600), (0o777, 0o600),
])
def test_source_witness_accepts_existing_modes(migration, tmp_path, directory_mode, file_mode):
    directory = tmp_path / 'shared'
    directory.mkdir()
    directory.chmod(directory_mode)
    target = directory / 'source'
    target.write_bytes(b'original source')
    target.chmod(file_mode)

    recorded = migration.witness(target)
    migration.revalidate([recorded])

    assert recorded['file']['sha256'] == migration.digest(b'original source')
    assert target.read_bytes() == b'original source'
    assert stat.S_IMODE(directory.stat().st_mode) == directory_mode
    assert stat.S_IMODE(target.stat().st_mode) == file_mode


@pytest.mark.parametrize('changed', ['content', 'replacement', 'mode'])
def test_writable_source_changes_still_invalidate_witness(migration, tmp_path, changed):
    directory = tmp_path / 'shared'
    directory.mkdir()
    directory.chmod(0o777)
    target = directory / 'source'
    target.write_bytes(b'original source')
    target.chmod(0o666)
    recorded = migration.witness(target)
    original_inode = target.stat().st_ino
    if changed == 'content':
        target.write_bytes(b'changed source')
    elif changed == 'replacement':
        replacement = directory / 'replacement'
        replacement.write_bytes(b'original source')
        replacement.chmod(0o666)
        replacement.replace(target)
        assert target.stat().st_ino != original_inode
    else:
        target.chmod(0o664)
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate([recorded])


@pytest.fixture
def shared_inputs(migration, shape):
    home, work, target, report = shape
    settings = home.parent / 'settings'
    settings.mkdir()
    settings.chmod(0o777)
    work.chmod(0o775)
    marker = work / '.git'
    marker.write_bytes(b'gitdir: ../shared-git-metadata\n')
    marker.chmod(0o664)
    alias = home / 'app-server-control/app-server-control.sock'
    support = migration._monitor_support()
    raw = support['monitor_default_config']('https://gitlab.example.invalid/team/project', 1, 'gitlab')
    raw.update(codex_home=str(home), socket=str(alias), cwd=str(work),
               queue_file=str(home.parent / 'queue.sqlite3'),
               state_file=str(home.parent / 'state/state.sqlite3'))
    monitor = settings / 'monitor.json'
    monitor_bytes = json.dumps(raw).encode()
    monitor.write_bytes(monitor_bytes)
    monitor.chmod(0o600)
    config = support['mq_config'](monitor)
    config.pop('_health', None)
    return {'config': config, 'work': work, 'target': target, 'report': report, 'monitor': monitor,
            'artifact': home.parent / 'artifact', 'directories': {settings: 0o777, work: 0o775},
            'sources': {target: (SOURCE, 0o600), monitor: (monitor_bytes, 0o600),
                        marker: (b'gitdir: ../shared-git-metadata\n', 0o664)}}


def prepare_shared_artifact(migration, inputs):
    manifest = migration.prepare_artifact(inputs['config'], [inputs['work']], [inputs['report']],
        {'requirements': None}, native_paths=[sys.executable],
        client_executables=['/usr/bin/true'], artifact=inputs['artifact'])
    seal = migration.digest((inputs['artifact'] / 'manifest.json').read_bytes())
    return manifest, seal


def test_prepare_accepts_existing_source_modes_without_chmod(migration, shared_inputs):
    manifest, seal = prepare_shared_artifact(migration, shared_inputs)
    artifact = shared_inputs['artifact']
    migration.artifact_inputs(artifact, seal)
    migration.static_revalidate(manifest)
    migration.revalidate(manifest['inventory']['sources'])
    for path, (expected_bytes, expected_mode) in shared_inputs['sources'].items():
        assert path.read_bytes() == expected_bytes
        assert stat.S_IMODE(path.stat().st_mode) == expected_mode
    for path, expected_mode in shared_inputs['directories'].items():
        assert stat.S_IMODE(path.stat().st_mode) == expected_mode
    candidate = tomllib.loads((artifact / 'proposed.toml').read_text())
    assert 'sandbox_mode' not in candidate
    assert candidate['default_permissions'] == 'local-workspace'
    assert candidate['permissions']['local-workspace'] == {
        'extends': ':workspace', 'network': {'enabled': True}}
    assert candidate['sandbox_workspace_write'] == {'network_access': True}
    assert stat.S_IMODE(artifact.stat().st_mode) == 0o700
    for name in ('manifest.json', 'proposed.toml'):
        assert stat.S_IMODE((artifact / name).stat().st_mode) == 0o600


def test_prepare_preserves_source_bytes_with_native_normalization(migration, shared_inputs):
    target, report = shared_inputs['target'], shared_inputs['report']
    source = SOURCE + b'''\n[mcp_servers.fixture]
startup_timeout_sec = 30
tool_timeout_sec = 300
[mcp_servers.node_repl]
startup_timeout_sec = 120
[skills]
config = [{ path = "skills/fixture/SKILL.md", enabled = false }]
'''
    target.write_bytes(source)
    report['layers'][0]['config'] = tomllib.loads(source.decode())
    native = report['layers'][0]['config']
    native['mcp_servers']['fixture'].update(startup_timeout_sec=30.0, tool_timeout_sec=300.0)
    native['mcp_servers']['node_repl']['startup_timeout_sec'] = 120.0
    native['skills']['config'][0]['path'] = str(target.parent / 'skills/fixture/SKILL.md')
    before = target.read_bytes(), target.stat()
    manifest, seal = prepare_shared_artifact(migration, shared_inputs)
    migration.artifact_inputs(shared_inputs['artifact'], seal)
    migration.static_revalidate(manifest)
    migration.revalidate_inventory(manifest['inventory'], target.parent,
                                  [shared_inputs['work']], [report], {'requirements': None})
    assert manifest['source_sha256'] == migration.digest(source)
    assert (target.read_bytes(), target.stat()) == before
    candidate_bytes = (shared_inputs['artifact'] / 'proposed.toml').read_bytes()
    candidate = tomllib.loads(candidate_bytes.decode())
    assert candidate_bytes == migration.transform(source)
    assert candidate['default_permissions'] == 'local-workspace'
    assert candidate['mcp_servers'] == tomllib.loads(source.decode())['mcp_servers']
    assert candidate['skills'] == tomllib.loads(source.decode())['skills']


@pytest.mark.parametrize('changed', ['content', 'replacement'])
def test_prepared_shared_monitor_source_changes_are_refused(migration, shared_inputs, changed):
    manifest, _ = prepare_shared_artifact(migration, shared_inputs)
    monitor = shared_inputs['monitor']
    original_bytes = monitor.read_bytes()
    original_inode = monitor.stat().st_ino
    if changed == 'content':
        monitor.write_bytes(original_bytes + b'\n')
    else:
        replacement = monitor.with_suffix('.replacement')
        replacement.write_bytes(original_bytes)
        replacement.chmod(0o600)
        replacement.replace(monitor)
        assert monitor.stat().st_ino != original_inode
        assert monitor.read_bytes() == original_bytes
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.static_revalidate(manifest)
    assert shared_inputs['target'].read_bytes() == SOURCE


@pytest.mark.parametrize('name', ['manifest.json', 'proposed.toml'])
def test_shared_sources_do_not_allow_nonprivate_artifacts(migration, shared_inputs, name):
    _, seal = prepare_shared_artifact(migration, shared_inputs)
    artifact = shared_inputs['artifact']
    (artifact / name).chmod(0o644)
    with pytest.raises(RuntimeError, match='must be private'):
        migration.artifact_inputs(artifact, seal)
    assert shared_inputs['target'].read_bytes() == SOURCE


def test_executable_rewrite_with_restored_bytes_and_mtime_changes_pin(migration, tmp_path):
    executable = tmp_path / 'native'
    executable.write_bytes(b'fixture executable bytes')
    executable.chmod(0o700)
    before = executable.stat()
    original = migration.executable_pin(executable)
    executable.write_bytes(b'fixture executable bytes')
    os.utime(executable, ns=(before.st_atime_ns, before.st_mtime_ns))
    changed = migration.executable_pin(executable)
    assert changed['sha256'] == original['sha256']
    assert changed['identity'][:-1] == original['identity'][:-1]
    assert changed['identity'][-1] != original['identity'][-1]
    assert changed != original


def test_real_client_process_denies_quiescence_even_without_native_records(migration, shape, monkeypatch):
    home, work, target, _ = shape
    runtime = home.parent / 'run'
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(runtime))
    alias = home / 'app-server-control/app-server-control.sock'
    config = {'codex_home': str(home), '_socket_alias': str(alias), 'socket': str(alias),
              'queue_file': str(home.parent / 'queue.sqlite3'),
              'state_file': str(home.parent / 'state/state.sqlite3')}
    with migration.MonitorColdStart(config, [sys.executable]) as owner:
        process = subprocess.Popen([sys.executable, '-u', '-c',
            'import time;print("ready",flush=True);time.sleep(30)'],
            env={**os.environ, 'CODEX_HOME': str(home)}, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        try:
            assert process.stdout.readline() == 'ready\n'
            with pytest.raises(RuntimeError, match='ainda está ativo'):
                migration.quiescent(owner, client_executables=[sys.executable], consumer_scripts=[])
            assert target.read_bytes() == SOURCE
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
        migration.quiescent(owner, client_executables=[sys.executable], consumer_scripts=[])


def test_new_git_root_marker_and_auth_change_invalidate_seal(migration, shape):
    home, work, _, report = shape
    sealed = migration.inventory(home, [work], [report], {'requirements': None})
    (work / '.git').mkdir(mode=0o700)
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate(sealed['sources'])
    sealed = migration.inventory(home, [work], [report], {'requirements': None})
    (home / 'auth.json').write_text('{}')
    (home / 'auth.json').chmod(0o600)
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate(sealed['sources'])


def test_running_automatic_obligation_denies_without_queue_writes(migration, shape, monkeypatch):
    home, _, target, _ = shape
    runtime = home.parent / 'run'
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(runtime))
    alias = home / 'app-server-control/app-server-control.sock'
    config = {'codex_home': str(home), '_socket_alias': str(alias), 'socket': str(alias),
              'queue_file': str(home.parent / 'queue.sqlite3'),
              'state_file': str(home.parent / 'state/state.sqlite3'),
              'gitlab_url': 'https://gitlab.example.invalid'}
    support = migration._monitor_support()
    queue = support['MonitorQueue'](config)
    queue.db.execute('INSERT INTO jobs(id,source_key,repository,iid,state,value) VALUES(?,?,?,?,?,?)',
                     ('held', 'fixture', 1, 1, 'running', json.dumps({'id': 'held'})))
    queue.close()
    before = Path(config['queue_file']).read_bytes()
    with migration.MonitorColdStart(config, [sys.executable]) as owner:
        with pytest.raises(RuntimeError, match='trabalho automático'):
            migration.quiescent(owner, client_executables=[], consumer_scripts=[])
    assert Path(config['queue_file']).read_bytes() == before
    assert target.read_bytes() == SOURCE


@pytest.fixture
def isolated_migration(tmp_path, monkeypatch):
    source_root = Path(__file__).resolve().parents[2]
    fixture_root = tmp_path / 'source'
    for relative in ('scripts/codex_permission_migration.py', 'scripts/codex_monitor_cold.py',
                     'scripts/pyproject.toml', 'scripts/poetry.lock',
                     '.local/bin/codex-session-stats', '.local/bin/codex-monitor'):
        original, copied = source_root / relative, fixture_root / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, copied)
        assert copied.read_bytes() == original.read_bytes()
    # The real module paths select fixture consumers, keeping unrelated live
    # monitor processes outside this operator's source/home context.
    for name in ('codex_monitor_cold', 'codex_permission_migration'):
        spec = importlib.util.spec_from_file_location(name, fixture_root / 'scripts' / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
    return module


@pytest.fixture
def operator(isolated_migration, shape, monkeypatch, request):
    migration = isolated_migration
    home, work, target, report = shape
    if getattr(request, 'param', False):
        source = SOURCE + b'''\n[mcp_servers.fixture]
startup_timeout_sec = 30
[skills]
config = [{ path = "skills/fixture/SKILL.md", enabled = false }]
'''
        target.write_bytes(source)
        report['layers'][0]['config'] = tomllib.loads(source.decode())
        native = report['layers'][0]['config']
        native['mcp_servers']['fixture']['startup_timeout_sec'] = 30.0
        native['skills']['config'][0]['path'] = str(home / 'skills/fixture/SKILL.md')
    root = home.parent
    for name in ('run', 'user', 'config', 'data', 'cache', 'state', 'bin'):
        (root / name).mkdir(mode=0o700)
    for key, name in (('HOME', 'user'), ('CODEX_HOME', 'codex'), ('XDG_RUNTIME_DIR', 'run'),
                      ('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                      ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')):
        monkeypatch.setenv(key, str(root / name))
    fake = root / 'bin/systemctl'
    fake.write_text('#!/usr/bin/python3\nimport os\nprint(os.environ.get("FIXTURE_UNIT_STATE", "inactive"))\n')
    fake.chmod(0o700)
    monkeypatch.setenv('PATH', str(fake.parent) + ':' + os.environ['PATH'])
    # Protocol fixture at the native executable boundary. No guard, source reader,
    # inventory comparison, lock, backup or publisher logic is replaced.
    (work / 'app-server').write_text('''import json,os,pathlib,sys,tomllib
home=pathlib.Path(os.environ['CODEX_HOME'])
for line in sys.stdin:
    row=json.loads(line)
    if 'id' not in row:continue
    method=row['method']
    if method=='initialize':value={'codexHome':str(home)}
    elif method=='configRequirements/read':value={'requirements':None}
    elif method=='config/read':
        source=tomllib.loads((home/'config.toml').read_text())
        for server in source.get('mcp_servers',{}).values():
            for key in ('startup_timeout_sec','tool_timeout_sec'):
                if key in server:server[key]=float(server[key])
        for skill in source.get('skills',{}).get('config',[]):
            skill['path']=str(home/skill['path'])
        user={'type':'user','file':str(home/'config.toml'),'profile':None}
        value={'layers':[{'name':user,'version':'sha256:test','config':source},
            {'name':{'type':'system','file':'/etc/codex/config.toml'},'version':'sha256:empty','config':{}}],
            'origins':{'sandbox_mode':{'name':user}}}
    else:raise AssertionError(method)
    print(json.dumps({'id':row['id'],'result':value}),flush=True)
''')
    alias = home / 'app-server-control/app-server-control.sock'
    config = {'codex_home': str(home), '_socket_alias': str(alias), 'socket': str(alias),
              'queue_file': str(root / 'queue.sqlite3'), 'state_file': str(root / 'state/state.sqlite3'),
              'gitlab_url': 'https://gitlab.example.invalid'}
    support = migration._monitor_support()
    monitor_path = root / 'monitor.json'
    raw = support['monitor_default_config']('https://gitlab.example.invalid/team/project', 1, 'gitlab')
    raw.update({key: value for key, value in config.items() if not key.startswith('_')})
    raw['cwd'] = str(work)
    monitor_path.write_text(json.dumps(raw))
    monitor_path.chmod(0o600)
    config = support['mq_config'](monitor_path)
    artifact = root / 'artifact'
    migration.prepare_artifact(config, [work], [report], {'requirements': None},
        native_paths=[sys.executable], client_executables=['/usr/bin/true'], artifact=artifact)
    manifest_sha256 = migration.digest((artifact / 'manifest.json').read_bytes())
    return migration, target, artifact, manifest_sha256


@pytest.mark.parametrize('operator', [False, True], indirect=True, ids=['exact', 'native-normalized'])
def test_operator_uses_real_transition_backup_repeat_and_guarded_recovery(operator):
    migration, target, artifact, seal = operator
    previous = target.read_bytes()
    result = migration.apply_artifact(artifact, manifest_sha256=seal)
    assert result['published'] and result['native_started'] and result['native_terminated']
    assert result['locks_reacquired'] and result['backup_complete']
    assert result['activation_verified'] is False
    assert Path(result['backup']).read_bytes() == previous
    candidate = target.read_bytes()
    unchanged = migration.apply_artifact(artifact, manifest_sha256=seal)
    assert unchanged['unchanged'] and not unchanged['native_started']
    assert target.read_bytes() == candidate
    restored = migration.apply_artifact(artifact, manifest_sha256=seal, recover=True)
    assert restored['published'] and target.read_bytes() == previous
    assert Path(restored['backup']).read_bytes() == candidate


def test_operator_refuses_its_active_consumer_before_reader_or_backup(operator):
    migration, target, artifact, seal = operator
    source_root = Path(migration.__file__).resolve().parents[1]
    consumer = str(source_root / '.local/bin/codex-session-stats')
    assert json.loads((artifact / 'manifest.json').read_text())['consumers'] == [
        consumer, str(source_root / '.local/bin/codex-monitor')]
    # A different native home isolates this assertion from native/client gates.
    # The exact configured script argument identifies the automatic consumer.
    process = subprocess.Popen([sys.executable, '-u', '-c',
        'import time;print("ready",flush=True);time.sleep(30)', consumer],
        env={**os.environ, 'CODEX_HOME': str(target.parent.parent / 'another-home')},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline() == 'ready\n'
        with pytest.raises(RuntimeError, match='consumidor automático ainda está ativo'):
            migration.apply_artifact(artifact, manifest_sha256=seal)
        assert target.read_bytes() == SOURCE
        assert not list(artifact.glob('reader-*'))
        assert not list(target.parent.glob('config.toml.before-monitor-*.bak'))
    finally:
        process.terminate()
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


@pytest.mark.parametrize('already_applied', [False, True])
def test_changed_monitor_queue_refuses_before_reader_or_backup(operator, already_applied):
    migration, target, artifact, seal = operator
    if already_applied:
        migration.apply_artifact(artifact, manifest_sha256=seal)
    monitor_path = target.parent.parent / 'monitor.json'
    raw = json.loads(monitor_path.read_text())
    raw['queue_file'] = str(target.parent.parent / 'another-queue.sqlite3')
    monitor_path.write_text(json.dumps(raw))
    changed = migration._monitor_support()['mq_config'](monitor_path)
    queue = migration._monitor_support()['MonitorQueue'](changed)
    queue.db.execute('INSERT INTO jobs(id,source_key,repository,iid,state,value) VALUES(?,?,?,?,?,?)',
        ('detached', 'fixture-detached', 1, 1, 'running', json.dumps({'id': 'detached'})))
    queue.close()
    previous = target.read_bytes(), target.stat().st_mtime_ns
    readers = set(artifact.glob('reader-*'))
    backups = set(target.parent.glob('config.toml.before-monitor-*.bak'))
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.apply_artifact(artifact, manifest_sha256=seal)
    assert (target.read_bytes(), target.stat().st_mtime_ns) == previous
    assert set(artifact.glob('reader-*')) == readers
    assert set(target.parent.glob('config.toml.before-monitor-*.bak')) == backups


def test_monitor_sources_refuse_stale_derived_queue_selection(operator):
    migration, target, _, _ = operator
    path = target.parent.parent / 'monitor.json'
    config = migration._monitor_support()['mq_config'](path)
    raw = json.loads(path.read_text())
    raw['queue_file'] = str(target.parent.parent / 'another-queue.sqlite3')
    path.write_text(json.dumps(raw))
    with pytest.raises(RuntimeError, match='seleção da configuração do monitor mudou'):
        migration.monitor_sources(config)


def test_linked_monitor_analysis_source_is_revalidated(operator):
    migration, target, _, _ = operator
    import tomlkit
    support = migration._monitor_support()
    path = target.parent.parent / 'monitor.json'
    raw = json.loads(path.read_text())
    settings = {key: raw.pop(key) for key in support['MONITOR_TOML_OPTIONS'] if key in raw}
    for key in ('model', 'effort'):
        settings['codex_' + key] = raw.pop(key)
    settings['workspace'] = raw.pop('cwd')
    analysis = path.with_suffix('.toml')
    analysis.write_text(tomlkit.dumps(settings))
    analysis.chmod(0o600)
    raw['analysis_config'] = str(analysis)
    path.write_text(json.dumps(raw))
    config = support['mq_config'](path)
    sources = migration.monitor_sources(config)
    assert [item['path'] for item in sources] == [str(path), str(analysis)]
    analysis.write_text(analysis.read_text() + '\n# external edit\n')
    with pytest.raises(RuntimeError, match='origem presente ou ausente mudou'):
        migration.revalidate(sources)


@pytest.mark.parametrize('changed', ['manifest', 'candidate', 'candidate_metadata', 'config', 'project', 'unit'])
def test_operator_initial_refusals_never_start_reader_or_backup(operator, monkeypatch, changed):
    migration, target, artifact, seal = operator
    if changed == 'manifest':
        with (artifact / 'manifest.json').open('ab') as stream:
            stream.write(b' ')
    elif changed == 'candidate':
        with (artifact / 'proposed.toml').open('ab') as stream:
            stream.write(b'# changed\n')
    elif changed == 'candidate_metadata':
        meta = (artifact / 'proposed.toml').stat()
        os.utime(artifact / 'proposed.toml', ns=(meta.st_atime_ns, meta.st_mtime_ns + 1))
    elif changed == 'config':
        target.write_bytes(target.read_bytes() + b'# external edit\n')
    elif changed == 'project':
        work = target.parent.parent / 'work'
        (work / '.codex').mkdir(mode=0o700)
    else:
        monkeypatch.setenv('FIXTURE_UNIT_STATE', 'active')
    current = target.read_bytes(), target.stat().st_mtime_ns
    with pytest.raises((RuntimeError, OSError)):
        migration.apply_artifact(artifact, manifest_sha256=seal)
    assert (target.read_bytes(), target.stat().st_mtime_ns) == current
    assert not list(artifact.glob('reader-*'))
    assert not list(target.parent.glob('config.toml.before-monitor-*.bak'))


@pytest.mark.parametrize('changed', ['user', 'project'])
def test_edit_after_native_shutdown_refuses_backup_and_reports_reader_activity(operator, monkeypatch, changed):
    migration, target, artifact, seal = operator
    import codex_monitor_cold
    real_reader = codex_monitor_cold.monitor_read_cold_native
    def after_shutdown(*args, **kwargs):
        value = real_reader(*args, **kwargs)
        assert value['native_terminated'] and value['locks_reacquired']
        if changed == 'user':
            target.write_bytes(target.read_bytes() + b'# later edit\n')
        else:
            (target.parent.parent / 'work/.codex').mkdir(mode=0o700)
        return value
    monkeypatch.setattr(codex_monitor_cold, 'monitor_read_cold_native', after_shutdown)
    previous = target.read_bytes()
    with pytest.raises(RuntimeError, match='mudaram') as caught:
        migration.apply_artifact(artifact, manifest_sha256=seal)
    state = caught.value.migration_state
    assert state['native_started'] and state['native_terminated'] and not state['published']
    assert target.read_bytes() == previous + (b'# later edit\n' if changed == 'user' else b'')
    assert not list(target.parent.glob('config.toml.before-monitor-*.bak'))


@pytest.mark.parametrize('changed', ['target', 'backup'])
def test_guarded_recovery_refuses_later_edits(operator, changed):
    migration, target, artifact, seal = operator
    result = migration.apply_artifact(artifact, manifest_sha256=seal)
    path = target if changed == 'target' else Path(result['backup'])
    path.write_bytes(path.read_bytes() + b'# later edit\n')
    before = target.read_bytes(), target.stat().st_mtime_ns
    with pytest.raises(RuntimeError, match='recuperação recusada'):
        migration.apply_artifact(artifact, manifest_sha256=seal, recover=True)
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
