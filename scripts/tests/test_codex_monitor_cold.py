"""Real per-home locks and process state guard cold config effects."""
import fcntl
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile

import pytest
import yaml

SOURCE_ROOT = Path(os.environ.get('CODEX_MONITOR_TEST_CLI',
    Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats')).parents[2]
SOURCE = SOURCE_ROOT / 'scripts/codex_monitor_cold.py'


@pytest.fixture
def cold(monkeypatch, request):
    module = runpy.run_path(str(SOURCE))
    support = module['_monitor_support']()
    module = {**support, **module}
    with tempfile.TemporaryDirectory(prefix='cm-cold-') as name:
        root = Path(name)
        home, runtime = root/'codex', root/'run'
        home.mkdir(mode=0o700);runtime.mkdir(mode=0o700)
        monkeypatch.setenv('XDG_RUNTIME_DIR',str(runtime))
        alias = home/'app-server-control/app-server-control.sock'
        config = {'codex_home':str(home),'_socket_alias':str(alias),'socket':str(alias),
                  'state_file':str(root/'monitor-state/state.sqlite3')}
        target = home/'config.toml'
        target.write_text('# keep exact bytes\n[features]\ncode_mode_host = false\n')
        target.chmod(0o600)
        if getattr(request, 'param', None):
            temporary = root / 'tmp'
            temporary.mkdir(mode=0o700)
            namespace = module['MonitorColdStart'].verify.__globals__
            monkeypatch.setitem(namespace, 'Path', lambda path: temporary if path == '/tmp' else Path(path))
            native_directory = temporary / ('codex-daemon-' + str(os.getuid()))
            if request.param == 'private-parent':
                native_directory.mkdir(mode=0o700)
            endpoint = native_directory / ('a' * 64)
            alias.parent.mkdir(mode=0o700)
            alias.symlink_to(endpoint)
            config['socket'] = str(endpoint)
        factory = lambda: module['MonitorColdStart'](config,[sys.executable])
        yield module, root, config, target, factory


@pytest.fixture
def native_helper(cold, request):
    _, root, config, _, _ = cold
    work = root / 'updater'
    work.mkdir(mode=0o700)
    (work / 'app-server').write_text('import sys\nprint("ready", flush=True)\nsys.stdin.read()\n')
    arguments = getattr(request, 'param', ['daemon', 'pid-update-loop'])
    child = subprocess.Popen([sys.executable, 'app-server', *arguments], cwd=work,
        env={**os.environ, 'CODEX_HOME': config['codex_home']},
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline() == 'ready\n'
        yield child
    finally:
        child.terminate(); child.wait(timeout=5)
        child.stdin.close(); child.stdout.close(); child.stderr.close()


def test_installed_updater_does_not_prevent_cold_start(cold, native_helper):
    _, _, _, target, factory = cold
    before = target.read_bytes(), target.stat().st_mtime_ns
    with factory() as guard:
        assert guard.native_owners() == []
        guard.verify()
        assert len(guard.descriptors) == 3
        for path, _, _ in guard.descriptors:
            with path.open('r+') as competitor:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(competitor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert native_helper.poll() is None
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


@pytest.mark.parametrize('trusted,native_helper', [
    (False, ['daemon', 'pid-update-loop']),
    (True, ['daemon', 'pid-update-loop', '--listen', 'unix://']),
    (True, ['daemon', 'start']),
], indirect=['native_helper'])
def test_only_the_exact_installed_updater_is_excluded(cold, native_helper, trusted):
    module, _, config, target, factory = cold
    if not trusted:
        factory = lambda: module['MonitorColdStart'](config, ['/usr/bin/true'])
    before = target.read_bytes(), target.stat().st_mtime_ns
    with pytest.raises(RuntimeError, match='app-server start is live or pending') as caught:
        with factory():pass
    assert f'PID {native_helper.pid}' in str(caught.value)
    assert native_helper.poll() is None
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


@pytest.mark.parametrize('changed', ['argv', 'environment', 'birth', 'executable'])
def test_changing_updater_identity_is_not_excluded(cold, native_helper, monkeypatch, changed):
    _, _, _, target, factory = cold
    before = target.read_bytes(), target.stat().st_mtime_ns
    process_root = Path('/proc') / str(native_helper.pid)
    with factory() as guard:
        reads = 0
        if changed in {'argv', 'environment'}:
            observed = process_root / ('cmdline' if changed == 'argv' else 'environ')
            original_read = Path.read_bytes
            def read_bytes(path):
                nonlocal reads
                value = original_read(path)
                if path == observed:
                    reads += 1
                    if reads == 2:
                        return value + (b'--stdio\0' if changed == 'argv' else b'CODEX_HOME=/changed\0')
                return value
            monkeypatch.setattr(Path, 'read_bytes', read_bytes)
        elif changed == 'birth':
            original_process = guard.process
            def process(pid):
                nonlocal reads
                value = original_process(pid)
                if pid == native_helper.pid:
                    reads += 1
                    if reads == 2:
                        return dict(value, birth='changed')
                return value
            monkeypatch.setattr(guard, 'process', process)
        else:
            original_stat = Path.stat
            def stat(path, *args, **kwargs):
                nonlocal reads
                value = original_stat(path, *args, **kwargs)
                if path == process_root / 'exe':
                    reads += 1
                    if reads == 2:
                        fields = list(value)
                        fields[1] += 1
                        return os.stat_result(fields)
                return value
            monkeypatch.setattr(Path, 'stat', stat)
        with pytest.raises(RuntimeError, match='updater identity changed'):
            guard.verify()
    assert reads >= 2
    assert native_helper.poll() is None
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


def test_private_reader_remains_the_only_owner_beside_installed_updater(cold, native_helper):
    module, root, config, target, factory = cold
    work = root / 'reader'
    work.mkdir(mode=0o700)
    (work / 'app-server').write_text('''import json,os,sys
for line in sys.stdin:
    row=json.loads(line)
    if 'id' not in row:continue
    value={'codexHome':os.environ['CODEX_HOME']} if row['method']=='initialize' else {}
    print(json.dumps({'id':row['id'],'result':value}),flush=True)
''')
    evidence = root / 'reader-evidence'
    evidence.mkdir(mode=0o700)
    before = target.read_bytes(), target.stat().st_mtime_ns
    with factory() as guard:
        result = module['monitor_read_cold_native'](guard, sys.executable, [work],
            environment={**os.environ, 'CODEX_HOME': config['codex_home']},
            evidence=evidence, timeout=5)
        assert result['native_started'] and result['native_terminated']
        assert result['locks_reacquired'] and result['exit_code'] == 0
        assert result['reports'] == [{}] and result['requirements'] == {}
        assert guard.native_owners() == []
    assert native_helper.poll() is None
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


def test_ci_prepares_a_private_runner_from_world_writable_python(cold, tmp_path):
    module, _, config, _, _ = cold
    prefix = tmp_path / 'provider'
    provider = prefix / 'bin/python'
    provider.parent.mkdir(parents=True)
    shutil.copyfile(Path(sys.executable).resolve(), provider)
    provider.chmod(0o777)
    for name in ('lib', 'lib64'):
        library = Path(sys.base_prefix) / name
        if library.is_dir():
            (prefix / name).symlink_to(library, target_is_directory=True)
    with pytest.raises(RuntimeError, match='untrusted native executable'):
        module['MonitorColdStart'](config, [provider])
    workflow = yaml.safe_load((SOURCE_ROOT / '.github/workflows/tests.yml').read_text())
    step, = [step for step in workflow['jobs']['unit-tests']['steps']
             if step.get('id') == 'prepare-test-python']
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    result = subprocess.run(['bash', '--noprofile', '--norc', '-c', step['run']],
        cwd=workspace, env={**os.environ, 'PATH': str(provider.parent) + os.pathsep + os.environ['PATH']},
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    runner = workspace / '.venv/bin/python'
    assert runner.resolve().is_relative_to(workspace / '.venv')
    assert runner.stat().st_mode & 0o777 == 0o755
    assert not runner.samefile(provider)
    assert provider.stat().st_mode & 0o777 == 0o777
    guard = module['MonitorColdStart'](config, [runner])
    assert set(guard.native) == {str(runner.resolve())}
    assert guard.descriptors == []


@pytest.mark.parametrize('kind,mode,regular,executable,writable_bits', [
    ('group-write', 0o770, True, True, 0o020),
    ('other-write', 0o702, True, True, 0o002),
    ('not-executable', 0o600, True, False, 0),
    ('directory', 0o700, False, True, 0),
    ('foreign-owner', 0o700, True, True, 0),
])
def test_untrusted_native_reports_rejected_file_metadata(
        cold, monkeypatch, kind, mode, regular, executable, writable_bits):
    module, root, config, target, _ = cold
    native = root / 'native'
    if kind == 'directory':
        native.mkdir(mode=mode)
    else:
        native.write_text('#!/usr/bin/python3\n')
        native.chmod(mode)
    owner = os.getuid()
    if kind == 'foreign-owner':
        owner += 1
        original_stat = Path.stat
        def file_stat(path, *args, **kwargs):
            meta = original_stat(path, *args, **kwargs)
            if path == native:
                fields = list(meta)
                fields[4] = owner
                return os.stat_result(fields)
            return meta
        monkeypatch.setattr(Path, 'stat', file_stat)
    before = target.read_bytes(), target.stat().st_mtime_ns
    with pytest.raises(RuntimeError, match='untrusted native executable') as caught:
        module['MonitorColdStart'](config, [native])
    detail = str(caught.value)
    assert f'path={str(native.resolve())!r}' in detail
    assert f'uid={owner}' in detail
    assert f'current_uid={os.getuid()}' in detail
    assert f'mode={mode:#06o}' in detail
    assert f'regular_file={regular}' in detail
    assert f'trusted_owner={kind != "foreign-owner"}' in detail
    assert f'executable={executable}' in detail
    assert f'writable_bits={writable_bits:#05o}' in detail
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    assert not (Path(config['codex_home']) / 'app-server-control').exists()


def test_trusted_native_still_constructs_without_configuration_effects(cold):
    module, root, config, target, _ = cold
    native = root / 'native'
    native.write_text('#!/usr/bin/python3\n')
    native.chmod(0o700)
    before = target.read_bytes(), target.stat().st_mtime_ns
    guard = module['MonitorColdStart'](config, [native])
    assert set(guard.native) == {str(native.resolve())}
    assert guard.descriptors == []
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


@pytest.mark.parametrize('cold', [None, 'missing-parent', 'private-parent'], indirect=True)
def test_cold_guard_holds_three_real_locks_and_changes_no_config(cold):
    _,root,config,target,factory = cold
    before = target.read_bytes(),target.stat().st_mtime_ns
    alias = Path(config['_socket_alias'])
    def alias_state():
        if not alias.is_symlink():
            return None
        meta = alias.lstat()
        # Resolving or reading the alias can update atime without changing it.
        return (meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid, meta.st_mode,
                meta.st_nlink, meta.st_size, meta.st_mtime_ns, meta.st_ctime_ns,
                alias.readlink())
    alias_before = alias_state()
    native_directory = Path(config['socket']).parent
    parent_existed = native_directory.exists()
    with factory() as guard:
        guard.verify()
        assert len(guard.descriptors)==3
        for path,_,_ in guard.descriptors:
            with path.open('r+') as competitor:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(competitor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        guard.before_native_start()
        assert len(guard.descriptors)==1
        with pytest.raises(RuntimeError,match='exclusion is not held'):
            guard.verify()
        with pytest.raises(BlockingIOError):
            with factory():pass
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before
    if alias_before is not None:
        assert alias_state() == alias_before
        assert native_directory.exists() == parent_existed
    with factory() as guard:guard.verify()


@pytest.mark.parametrize('cold', ['missing-parent'], indirect=True)
@pytest.mark.parametrize('kind,message', [
    ('public-parent', 'must be private'),
    ('file-parent', 'must be private'),
    ('dangling-parent', 'unexpected destination'),
    ('present-endpoint', 'endpoint already exists'),
])
def test_stale_alias_still_rejects_unsafe_parent_or_present_endpoint(cold, kind, message):
    _, root, config, target, factory = cold
    directory = Path(config['socket']).parent
    if kind == 'file-parent':
        directory.touch(mode=0o600)
    elif kind == 'dangling-parent':
        directory.symlink_to(root / 'missing', target_is_directory=True)
    else:
        directory.mkdir(mode=0o700)
        if kind == 'public-parent':
            directory.chmod(0o777)
        else:
            Path(config['socket']).touch(mode=0o600)
    before = target.read_bytes(), target.stat().st_mtime_ns
    with pytest.raises(RuntimeError, match=message):
        with factory():pass
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


@pytest.mark.parametrize('cold', ['missing-parent'], indirect=True)
def test_missing_native_parent_becoming_unsafe_revokes_cold_guard(cold):
    _, _, config, target, factory = cold
    before = target.read_bytes(), target.stat().st_mtime_ns
    with factory() as guard:
        directory = Path(config['socket']).parent
        directory.mkdir(mode=0o700)
        directory.chmod(0o777)
        with pytest.raises(RuntimeError, match='must be private'):
            guard.verify()
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before


@pytest.mark.parametrize('cold', [None, 'missing-parent'], indirect=True)
@pytest.mark.parametrize('relative',['app-server-daemon/daemon.lock',
                                   'app-server-control/app-server-startup.lock'])
def test_external_native_lock_denies_cold_preparation(cold,relative):
    _,root,config,target,factory = cold
    lock = Path(config['codex_home'])/relative
    lock.parent.mkdir(mode=0o700,exist_ok=True)
    before = target.read_bytes(),target.stat().st_mtime_ns
    with lock.open('w+') as competitor:
        fcntl.flock(competitor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            with factory():pass
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before
    with factory() as guard:guard.verify()


def test_reader_transition_restores_real_locks_and_keeps_coordinator(cold):
    _,_,_,target,factory=cold
    before=target.read_bytes(),target.stat().st_mtime_ns
    with factory() as guard:
        coordinator=guard.descriptors[0]
        native_paths=[path for path,_,_ in guard.descriptors[1:]]
        guard.before_native_start()
        guard.verify_coordinator()
        with pytest.raises(BlockingIOError):
            with factory():pass
        guard.after_native_stop()
        guard.verify()
        assert guard.descriptors[0]==coordinator
        assert len(guard.descriptors)==3 and len(guard.native_locks)==2
        for path in native_paths:
            with path.open('r+') as competitor:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(competitor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(RuntimeError,match='already held'):
            guard.after_native_stop()
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before


@pytest.mark.parametrize('relative',['app-server-daemon/daemon.lock',
                                   'app-server-control/app-server-startup.lock'])
def test_native_competitor_denies_reacquisition_without_losing_coordinator(cold,relative):
    _,_,config,target,factory=cold
    before=target.read_bytes(),target.stat().st_mtime_ns
    with factory() as guard:
        coordinator=guard.descriptors[0]
        guard.before_native_start()
        with (Path(config['codex_home'])/relative).open('r+') as competitor:
            fcntl.flock(competitor,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with pytest.raises(BlockingIOError):
                guard.after_native_stop()
            assert guard.descriptors==[coordinator]
            assert guard.native_locks==[]
            with pytest.raises(BlockingIOError):
                with factory():pass
        guard.after_native_stop()
        guard.verify()
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before


def test_live_unrecorded_native_denies_reacquisition(cold):
    _,_,config,target,factory=cold
    before=target.read_bytes(),target.stat().st_mtime_ns
    with factory() as guard:
        guard.before_native_start()
        child=subprocess.Popen([sys.executable,'-u','-c',
            'import time;print("ready",flush=True);time.sleep(20)','app-server'],
            env={**os.environ,'CODEX_HOME':config['codex_home']},
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            assert child.stdout.readline()=='ready\n'
            with pytest.raises(RuntimeError,match='app-server start is live or pending'):
                guard.after_native_stop()
            assert len(guard.descriptors)==1 and guard.native_locks==[]
        finally:
            child.terminate();child.wait(timeout=5)
            child.stdout.close();child.stderr.close()
        guard.after_native_stop()
        guard.verify()
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before


def test_existing_unix_endpoint_denies_before_config_effects(cold):
    _,_,config,target,factory = cold
    alias = Path(config['_socket_alias'])
    alias.parent.mkdir(mode=0o700)
    before = target.read_bytes(),target.stat().st_mtime_ns
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
        server.bind(str(alias));server.listen()
        with pytest.raises(RuntimeError,match='endpoint exists'):
            with factory():pass
        assert (target.read_bytes(),target.stat().st_mtime_ns)==before


@pytest.mark.parametrize('cold', [None, 'missing-parent'], indirect=True)
def test_live_pid_or_invalid_native_record_denies(cold):
    _,_,config,target,factory = cold
    record = Path(config['codex_home'])/'app-server-daemon/daemon.pid'
    record.parent.mkdir(mode=0o700)
    before = target.read_bytes(),target.stat().st_mtime_ns
    for value in ({'pid':os.getpid()},{'pid':'unknown'}):
        record.write_text(json.dumps(value))
        with pytest.raises(RuntimeError,match='live or uncertain|invalid cold-start process'):
            with factory():pass
        assert (target.read_bytes(),target.stat().st_mtime_ns)==before


@pytest.mark.parametrize('cold', [None, 'missing-parent'], indirect=True)
def test_live_gui_reservation_is_not_mistaken_for_a_cold_home(cold):
    module,_,config,target,factory = cold
    runtime = module['monitor_shared_runtime'](config,create=True)
    module['monitor_runtime_write'](runtime/'launch.json',{
        'codex_home':config['codex_home'],'gui':module['monitor_process'](os.getpid())})
    before = target.read_bytes(),target.stat().st_mtime_ns
    with pytest.raises(RuntimeError,match='launch is still live or pending'):
        with factory():pass
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before


@pytest.mark.parametrize('cold', [None, 'missing-parent'], indirect=True)
@pytest.mark.parametrize('known',[True,False])
def test_unrecorded_native_start_revokes_a_held_cold_guard(cold,known):
    module,_,config,target,factory = cold
    if not known:
        factory = lambda: module['MonitorColdStart'](config,['/usr/bin/true'])
    before = target.read_bytes(),target.stat().st_mtime_ns
    child = None
    with factory() as guard:
        try:
            child = subprocess.Popen([sys.executable,'-u','-c',
                'import time;print("ready",flush=True);time.sleep(20)','app-server'],
                env={**os.environ,'CODEX_HOME':config['codex_home']},
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            assert child.stdout.readline()=='ready\n'
            with pytest.raises(RuntimeError,match='app-server start is live or pending'):
                guard.verify()
            assert (target.read_bytes(),target.stat().st_mtime_ns)==before
        finally:
            if child is not None:
                child.terminate();child.wait(timeout=5)
                child.stdout.close();child.stderr.close()
    with factory() as guard:guard.verify()


def test_lock_replacement_revokes_guard(cold):
    _,_,_,target,factory = cold
    with factory() as guard:
        path = guard.descriptors[-1][0]
        path.unlink();path.touch(mode=0o600)
        with pytest.raises(RuntimeError,match='lock identity changed'):
            guard.verify()


def test_symlinked_native_control_directory_is_rejected(cold):
    _,root,config,target,factory = cold
    destination=root/'other';destination.mkdir(mode=0o700)
    (Path(config['codex_home'])/'app-server-control').symlink_to(destination,target_is_directory=True)
    before=target.read_bytes(),target.stat().st_mtime_ns
    with pytest.raises(RuntimeError,match='without symlinks'):
        with factory():pass
    assert (target.read_bytes(),target.stat().st_mtime_ns)==before
    assert list(destination.iterdir())==[]


@pytest.mark.parametrize('server_argument',[False,True])
def test_unreadable_executable_is_unknown_only_for_a_possible_native_start(cold,server_argument):
    _,_,config,target,factory=cold
    code=('import ctypes,time;'
          'assert ctypes.CDLL(None).prctl(4,0,0,0,0)==0;'
          'print("ready",flush=True);time.sleep(20)')
    child=subprocess.Popen([sys.executable,'-u','-c',code,
        'app-server' if server_argument else 'unrelated-controlled-process'],
        env={**os.environ,'CODEX_HOME':config['codex_home']},
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    before=target.read_bytes(),target.stat().st_mtime_ns
    try:
        assert child.stdout.readline()=='ready\n'
        with pytest.raises(PermissionError):
            Path('/proc').joinpath(str(child.pid),'exe').resolve(strict=True)
        if server_argument:
            with pytest.raises(RuntimeError,match='classification is unreadable'):
                with factory():pass
        else:
            with factory() as guard:guard.verify()
        assert (target.read_bytes(),target.stat().st_mtime_ns)==before
    finally:
        child.terminate();child.wait(timeout=5)
        child.stdout.close();child.stderr.close()


def test_reader_surviving_private_descendant_refuses_success(cold):
    module, root, config, target, factory = cold
    work = root / 'work'
    work.mkdir(mode=0o700)
    child_record = root / 'child.json'
    # This fixture implements only the external native transport boundary. The
    # actual owner, process discovery, private pipe and normal EOF code all run.
    script = work / 'app-server'
    script.write_text('''import json,os,subprocess,sys
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],
    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
with open(os.environ['CHILD_RECORD'],'w') as stream:json.dump({'pid':child.pid},stream)
for line in sys.stdin:
    row=json.loads(line)
    if 'id' not in row:continue
    value={'codexHome':os.environ['CODEX_HOME']} if row['method']=='initialize' else {}
    print(json.dumps({'id':row['id'],'result':value}),flush=True)
''')
    evidence = root / 'reader-evidence'
    evidence.mkdir(mode=0o700)
    before = target.read_bytes(), target.stat().st_mtime_ns
    child_pid = None
    try:
        with factory() as guard:
            with pytest.raises(RuntimeError, match='surviving descendants') as caught:
                module['monitor_read_cold_native'](guard, sys.executable, [work],
                    environment={**os.environ, 'CODEX_HOME': config['codex_home'],
                                 'CHILD_RECORD': str(child_record)}, evidence=evidence, timeout=5)
            state = caught.value.reader_state
            assert state['native_started'] and state['leader_terminated']
            assert state['native_terminated'] is False
            assert state['surviving_descendants']
            child_pid = json.loads(child_record.read_text())['pid']
            assert child_pid in [entry['pid'] for entry in state['surviving_descendants']]
            assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    finally:
        # Cleanup only this test's exact recorded child, never a production owner.
        if child_pid is None and child_record.exists():
            child_pid = json.loads(child_record.read_text())['pid']
        if child_pid is not None:
            import signal
            os.kill(child_pid, signal.SIGTERM)


def test_reader_detects_a_new_dangling_shared_endpoint_before_success(cold):
    module, root, config, target, factory = cold
    work = root / 'work'
    work.mkdir(mode=0o700)
    endpoint = root / 'shared.sock'
    config['socket'] = str(endpoint)
    script = work / 'app-server'
    script.write_text('''import json,os,pathlib,sys
for line in sys.stdin:
    row=json.loads(line)
    if 'id' not in row:continue
    value={'codexHome':os.environ['CODEX_HOME']} if row['method']=='initialize' else {}
    if row['method']=='configRequirements/read':
        pathlib.Path(os.environ['ENDPOINT']).symlink_to('missing-destination')
    print(json.dumps({'id':row['id'],'result':value}),flush=True)
''')
    evidence = root / 'reader-evidence'
    evidence.mkdir(mode=0o700)
    before = target.read_bytes(), target.stat().st_mtime_ns
    with factory() as guard:
        with pytest.raises(RuntimeError, match='changed a shared endpoint identity') as caught:
            module['monitor_read_cold_native'](guard, sys.executable, [work],
                environment={**os.environ, 'CODEX_HOME': config['codex_home'],
                             'ENDPOINT': str(endpoint)}, evidence=evidence, timeout=5)
        state = caught.value.reader_state
        assert state['native_started'] and state['leader_terminated']
        assert state['locks_reacquired'] is True
        assert endpoint.is_symlink() and not endpoint.exists()
        assert (target.read_bytes(), target.stat().st_mtime_ns) == before
        assert not list(target.parent.glob('config.toml.before-monitor-*.bak'))


def test_shared_publisher_exact_backup_mode_and_noop(cold):
    module, _, _, target, factory = cold
    target.chmod(0o640)
    previous = target.read_bytes()
    with factory() as owner:
        original = module['monitor_config_snapshot'](owner)
        before = target.stat().st_mtime_ns
        result = module['monitor_publish_config'](owner, original, previous)
        assert result['changed'] is False and result['backup'] is None
        assert target.stat().st_mtime_ns == before
        prepared = previous + b'# reviewed change\n'
        result = module['monitor_publish_config'](owner, original, prepared)
        assert result['published'] and result['backup_complete']
        backup = Path(result['backup'])
        assert backup.read_bytes() == previous and backup.stat().st_mode & 0o777 == 0o600
        assert target.read_bytes() == prepared and target.stat().st_mode & 0o777 == 0o640
        assert target.stat().st_gid == original[0][3]


@pytest.mark.parametrize('barrier', [2, 3])
def test_shared_publisher_refuses_an_editor_at_real_barriers(cold, barrier):
    module, _, _, target, factory = cold
    previous = target.read_bytes()
    calls = 0
    with factory() as owner:
        original = module['monitor_config_snapshot'](owner)
        def race():
            nonlocal calls
            calls += 1
            if calls == barrier:
                target.write_bytes(b'# external editor\n')
        with pytest.raises(RuntimeError, match='changed concurrently'):
            module['monitor_publish_config'](owner, original, previous + b'# candidate\n', recheck=race)
    assert target.read_bytes() == b'# external editor\n'
    backups = list(target.parent.glob('config.toml.before-monitor-*.bak'))
    assert len(backups) == (1 if barrier == 3 else 0)
    if backups:
        assert backups[0].read_bytes() == previous
    assert not list(target.parent.glob('.config.toml.codex-monitor-*'))


def test_shared_publisher_reports_publication_without_automatic_rollback(cold, monkeypatch):
    module, _, _, target, factory = cold
    previous = target.read_bytes()
    real_replace = os.replace
    def concurrent_after_replace(source, destination):
        real_replace(source, destination)
        Path(destination).write_bytes(b'# later edit\n')
    with factory() as owner:
        original = module['monitor_config_snapshot'](owner)
        monkeypatch.setattr(os, 'replace', concurrent_after_replace)
        with pytest.raises(RuntimeError, match='confirmação falhou') as caught:
            module['monitor_publish_config'](owner, original, previous + b'# candidate\n')
        state = caught.value.publication_state
        assert state['published'] and state['backup_complete']
        assert Path(state['backup']).read_bytes() == previous
        assert target.read_bytes() == b'# later edit\n'


def test_control_ancestry_replacement_revokes_held_owner(cold):
    _, _, config, target, factory = cold
    before = target.read_bytes(), target.stat().st_mtime_ns
    with factory() as owner:
        control = Path(config['codex_home']) / 'app-server-control'
        moved = control.with_name('moved-control')
        control.rename(moved)
        control.symlink_to(moved, target_is_directory=True)
        with pytest.raises(RuntimeError, match='directory identity changed'):
            owner.verify()
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
