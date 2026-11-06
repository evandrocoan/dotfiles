"""Public routing and independent native identity, with real private Unix peers."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import tempfile
import types

import pytest

CLI = Path(os.environ.get('CODEX_MONITOR_TEST_CLI',
    Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats'))


@pytest.fixture
def launcher():
    return runpy.run_path(str(CLI))['monitor_launcher']()


@pytest.mark.parametrize('arguments,action,extra', [
    ([], 'launch-cli', []),
    (['--no-alt-screen', '-C', '/tmp/work', 'a prompt'], 'launch-cli',
     ['--no-alt-screen', '-C', '/tmp/work', 'a prompt']),
    (['--gui', '--remote-debugging-port=0'], 'launch-app', ['--remote-debugging-port=0']),
    (['--', '--help'], 'launch-cli', ['--help']),
])
def test_public_command_routes_and_preserves_arguments(monkeypatch, tmp_path, arguments, action, extra):
    module = runpy.run_path(str(CLI.with_name('codex-monitor')))
    entry = module['main'].__globals__
    app = tmp_path/'app'; app.mkdir()
    (app/'codex-launcher').touch()
    python = CLI.parents[2]/'scripts/.venv/bin/python'
    monkeypatch.setattr(Path, 'is_file', lambda self: self == python)
    monkeypatch.setattr(sys, 'argv', ['codex-monitor', *arguments])
    monkeypatch.setattr(entry['shutil'], 'which', lambda name: str(app/'codex-launcher')
                        if name == 'chatgpt' else '/installed/codex')
    calls = []
    def execute(path, args):
        calls.append((path, args)); raise SystemExit(37)
    monkeypatch.setattr(os, 'execv', execute)
    with pytest.raises(SystemExit) as result:
        module['main']()
    assert result.value.code == 37
    assert calls == [(python, [str(python), str(CLI), 'monitor-gitlab', action, '--codex', str(app/'resources/codex'),
        *(['--app', str(app/'ChatGPT')] if action == 'launch-app' else ['--cli', '/installed/codex']), '--', *extra])]


def test_help_does_not_need_installation_or_optional_packages(monkeypatch, capsys):
    module = runpy.run_path(str(CLI.with_name('codex-monitor')))
    monkeypatch.setattr(sys, 'argv', ['codex-monitor', '--help'])
    def denied(*args):
        pytest.fail('launcher help attempted application discovery')
    monkeypatch.setattr(module['main'].__globals__['shutil'], 'which', denied)
    assert module['main']() == 0
    assert 'Without --gui, opens the CLI in the terminal' in capsys.readouterr().out


@pytest.mark.parametrize('arguments', [
    ['-C', 'relative', 'hello world'],
    ['--', '--remote'],
    ['--', '--remote=example'],
])
def test_cli_exec_keeps_cwd_exit_and_arguments_without_restarting_native(
        launcher, monkeypatch, tmp_path, arguments):
    function = launcher['monitor_launch_cli']; namespace = function.__globals__
    native = Path(sys.executable).resolve(); calls = []
    monkeypatch.setitem(namespace, 'ensure_server', lambda config, codex:
                        ({'socket': '/fixture/native.sock'}, False, None))
    monkeypatch.setenv('CODEX_CLI_PATH', '/unrelated/old-wrapper')
    monkeypatch.setenv('CODEX_STATS_APP_LAUNCH', '/unrelated/receipt')
    def execute(binary, args, environment):
        calls.append((binary, args, environment, Path.cwd())); raise SystemExit(41)
    monkeypatch.setattr(os, 'execve', execute)
    with pytest.raises(SystemExit) as result:
        function({'codex_home': str(tmp_path)}, native, native, arguments)
    assert result.value.code == 41
    binary, args, env, cwd = calls[0]
    assert binary == native
    assert args == [str(native), '--remote', 'unix:///fixture/native.sock', *arguments]
    assert env['CODEX_HOME'] == str(tmp_path)
    assert 'CODEX_CLI_PATH' not in env and 'CODEX_STATS_APP_LAUNCH' not in env
    assert cwd == Path.cwd()
    for arguments in (['--remote', 'unix:///other'], ['--remote=unix:///other']):
        with pytest.raises(RuntimeError, match='remove the --remote option'):
            function({'codex_home': str(tmp_path)}, native, native, arguments)
    assert len(calls) == 1


@pytest.fixture
def independent(launcher, monkeypatch, request):
    # The real peer lives separately from its clients and reports exec-time bootstrap.
    with tempfile.TemporaryDirectory(prefix='cm-owner-') as name:
        root = Path(name); home = root/'codex'; home.mkdir(mode=0o700)
        runtime = root/'run'; runtime.mkdir(mode=0o700)
        monkeypatch.setenv('XDG_RUNTIME_DIR', str(runtime))
        alias = home/'app-server-control/app-server-control.sock'; alias.parent.mkdir()
        native_dir = Path('/tmp')/('codex-daemon-'+str(os.getuid()))
        native_dir.mkdir(mode=0o700, exist_ok=True)
        endpoint = native_dir/hashlib.sha256(str(root).encode()).hexdigest()
        config = {'codex_home': str(home), '_socket_alias': str(alias), 'socket': str(endpoint),
                  'state_file': str(root/'monitor/state.sqlite3'), 'native_timeout': 3}
        (home/'config.toml').write_text('[features]\ncode_mode_host=true\n'
            '[plugins."codex-app-tools@openai-bundled".mcp_servers.codex_app]\nenabled=true\n'
            '[plugins."code-review@openai-bundled".mcp_servers.code-review]\nenabled=true\n')
        tools = launcher['monitor_app_tools_directory'](config, create=True)
        environment = dict(os.environ, CODEX_HOME=str(home), CODEX_APP_TOOLS_PIPE_PATH=str(tools/'host.sock'),
            CODEX_MONITOR_LAUNCHER_PROTOCOL='1')
        variant = getattr(request, 'param', None)
        if variant in {'ordinary', 'missing-tools'}:
            tools.rmdir()
        if variant == 'ordinary':
            for key in ('CODEX_HOME', 'CODEX_APP_TOOLS_PIPE_PATH', 'CODEX_MONITOR_LAUNCHER_PROTOCOL'):
                environment.pop(key)
            environment['HOME'] = str(root)
        elif variant == 'wrong-tools':
            environment['CODEX_APP_TOOLS_PIPE_PATH'] = str(root / 'other.sock')
        elif variant == 'unsafe-tools':
            tools.chmod(0o777)
        namespace = launcher['native_owner'].__globals__
        monkeypatch.setitem(namespace, 'installed_native', lambda config: Path(sys.executable).resolve())
        monkeypatch.setitem(launcher, 'installed_native', lambda config: Path(sys.executable).resolve())
        script = ('import socket,sys; s=socket.socket(socket.AF_UNIX); s.bind(sys.argv[1]); '
                  's.listen(); print("ready",flush=True); '\
                  '\nwhile True:\n c,_=s.accept(); c.close()\n')
        if variant == 'rpc':
            script = '''import asyncio,json,os,sys,tomllib
from pathlib import Path
from websockets.server import unix_serve
async def handler(connection):
 async for raw in connection:
  request=json.loads(raw)
  if 'id' not in request: continue
  if request['method']=='initialize': result={'codexHome':os.environ['CODEX_HOME']}
  elif request['method']=='config/read': result={'config':tomllib.loads((Path(os.environ['CODEX_HOME'])/'config.toml').read_text())}
  else: raise AssertionError('unexpected RPC '+request['method'])
  await connection.send(json.dumps({'id':request['id'],'result':result}))
async def main():
 async with unix_serve(handler,path=sys.argv[1]):
  print('ready',flush=True)
  await asyncio.Future()
asyncio.run(main())
'''
        process = subprocess.Popen([sys.executable, '-c', script, str(endpoint), 'app-server'],
            env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            assert process.stdout.readline() == 'ready\n'
            alias.symlink_to(endpoint)
            owner = launcher['native_owner'](config) if variant in {None, 'rpc'} else None
            runtime_path = launcher['support']()['monitor_shared_runtime'](config, create=True)
            if owner is not None:
                launcher['monitor_runtime_write'](runtime_path/'ready.json', owner)
            yield config, owner, process, runtime_path, home
        finally:
            process.terminate(); process.wait(timeout=5)
            process.stdin.close(); process.stdout.close(); process.stderr.close()
            endpoint.unlink(missing_ok=True)
            if tools.exists():
                tools.rmdir()


@pytest.mark.parametrize('independent,error,message', [
    ('ordinary', RuntimeError, 'previous configuration or another installation'),
    ('wrong-tools', RuntimeError, 'previous configuration or another installation'),
    ('missing-tools', FileNotFoundError, 'codex-tools-'),
    ('unsafe-tools', RuntimeError, 'must be private'),
], indirect=['independent'])
def test_attach_rejects_incompatible_or_missing_runtime_without_effects(
        launcher, independent, monkeypatch, error, message):
    config, _, process, runtime, home = independent
    before = (home / 'config.toml').read_bytes(), (home / 'config.toml').stat().st_mtime_ns
    namespace = launcher['ensure_server_once'].__globals__
    def denied(*args, **kwargs):
        pytest.fail('rejected live attach attempted bootstrap, native start or ready publication')
    monkeypatch.setitem(namespace, 'monitor_prepare_bootstrap', denied)
    monkeypatch.setitem(namespace, 'monitor_runtime_write', denied)
    monkeypatch.setattr(subprocess, 'run', denied)
    with pytest.raises(error, match=message) as caught:
        launcher['ensure_server_once'](config, Path(sys.executable).resolve())
    if 'previous configuration' in message:
        assert 'Finish your work and close Codex normally.' in str(caught.value)
        assert launcher['server_stop_instructions'](config) in str(caught.value)
    assert process.poll() is None
    assert ((home / 'config.toml').read_bytes(), (home / 'config.toml').stat().st_mtime_ns) == before
    assert not (runtime / 'ready.json').exists()
    assert not (home / 'app-server-daemon').exists()


@pytest.mark.parametrize('previous', ['same-pid', 'live-owner', 'malformed'])
def test_every_attach_writer_preserves_conflicting_registration(launcher, independent, monkeypatch, previous):
    import fcntl
    config, owner, process, runtime, home = independent
    saved = json.loads(json.dumps(owner))
    if previous == 'same-pid':
        saved['native']['birth'] = '1'
        expected = 'same process'
    elif previous == 'live-owner':
        saved['native'] = launcher['monitor_process'](os.getpid())
        expected = 'still live'
    else:
        saved['native'] = {'pid': process.pid + 1}
        expected = 'invalid'
    launcher['monitor_runtime_write'](runtime / 'ready.json', saved)
    before = (runtime / 'ready.json').read_bytes(), (home / 'config.toml').read_bytes()
    def forbidden(*args):
        pytest.fail('a rejected registration reached protocol/config verification')
    monkeypatch.setitem(launcher['verify_effective'].__globals__, 'verify_effective', forbidden)
    with pytest.raises(RuntimeError, match=expected):
        launcher['ensure_server_once'](config, Path(sys.executable).resolve())
    assert ((runtime / 'ready.json').read_bytes(), (home / 'config.toml').read_bytes()) == before
    assert process.poll() is None
    with (runtime / 'launch.lock').open('r+') as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)


def retired_owner(launcher, owner):
    child = subprocess.Popen([sys.executable, '-c', 'import sys; print("ready",flush=True);sys.stdin.read()'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline() == 'ready\n'
        identity = launcher['monitor_process'](child.pid)
    finally:
        child.terminate(); child.wait(timeout=5)
        child.stdin.close(); child.stdout.close()
    return dict(owner, native=identity)


@pytest.mark.parametrize('independent', ['rpc'], indirect=True)
def test_new_gui_admission_replaces_terminated_native_after_real_protocol_check(launcher, independent):
    config, owner, process, runtime, home = independent
    old = retired_owner(launcher, owner)
    launcher['monitor_runtime_write'](runtime / 'ready.json', old)
    calls = []
    assert launcher['register_gui_native'](config, lambda: calls.append('gui-verified')) == owner
    assert calls == ['gui-verified']
    assert json.loads((runtime / 'ready.json').read_text()) == owner
    before = (runtime / 'ready.json').stat().st_mtime_ns
    assert launcher['register_gui_native'](config, lambda: None) == owner
    assert (runtime / 'ready.json').stat().st_mtime_ns == before
    assert process.poll() is None


@pytest.mark.parametrize('independent', ['rpc'], indirect=True)
@pytest.mark.parametrize('change', ['receipt', 'gui', 'effective-config', 'lock'])
def test_replacement_failure_preserves_registration_and_releases_lock(launcher, independent, change):
    import fcntl
    config, owner, process, runtime, home = independent
    old = retired_owner(launcher, owner)
    launcher['monitor_runtime_write'](runtime / 'ready.json', old)
    before = (runtime / 'ready.json').read_bytes()
    descriptor = None
    def revalidate():
        if change == 'gui':
            raise RuntimeError('GUI identity changed')
        if change == 'receipt':
            launcher['monitor_runtime_write'](runtime / 'ready.json', dict(old, version=2))
    if change == 'effective-config':
        target = home / 'config.toml'
        target.write_text(target.read_text().replace('code_mode_host=true', 'code_mode_host=false'))
    if change == 'lock':
        descriptor = (runtime / 'launch.lock').open('w')
        (runtime / 'launch.lock').chmod(0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        expected = {'receipt': 'registration changed', 'gui': 'GUI identity changed',
                    'effective-config': 'has not enabled', 'lock': None}[change]
        with pytest.raises(BlockingIOError if change == 'lock' else RuntimeError, match=expected):
            launcher['register_gui_native'](config, revalidate)
    finally:
        if descriptor is not None:
            descriptor.close()
    current = (runtime / 'ready.json').read_bytes()
    if change == 'receipt':
        assert json.loads(current) == dict(old, version=2)
    else:
        assert current == before
    with (runtime / 'launch.lock').open('r+') as descriptor:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert process.poll() is None


def test_gui_reconnect_never_creates_a_missing_native_registration(launcher, independent):
    config, _, process, runtime, _ = independent
    (runtime / 'ready.json').unlink()
    with pytest.raises(RuntimeError, match='registration is missing'):
        launcher['register_gui_native'](config, lambda: None)
    assert not (runtime / 'ready.json').exists()
    assert process.poll() is None


def test_native_notification_stream_cannot_extend_overall_deadline(launcher, independent, monkeypatch):
    import asyncio
    config, owner, _, _, _ = independent
    config = dict(config, native_timeout=1)
    class Connection:
        notifications = 0
        async def __aenter__(self):
            self.peer = socket.socket(socket.AF_UNIX); self.peer.connect(config['socket'])
            self.transport = types.SimpleNamespace(get_extra_info=lambda name: self.peer)
            return self
        async def __aexit__(self, *args):
            self.peer.close()
        async def send(self, raw):
            assert json.loads(raw)['method'] == 'initialize'
        async def recv(self):
            await asyncio.sleep(0)
            self.notifications += 1
            return json.dumps({'method': 'notice', 'params': {}})
    connection = Connection()
    monkeypatch.setitem(launcher['native_rpc'].__globals__, 'websockets_connect',
                        lambda: lambda *args, **kwargs: connection)
    async def scenario():
        task = asyncio.create_task(launcher['native_rpc'](config, [], unpublished=owner))
        try:
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(task), 3)
            assert task.done(), 'only the external test watchdog expired; native RPC has no overall deadline'
            assert connection.notifications > 1
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


def test_issued_monitor_request_is_not_replayed_after_connection_loss(launcher, independent, monkeypatch):
    import websockets.client
    config, owner, _, runtime, _ = independent
    core = runpy.run_path(str(CLI)); requests, connections = [], []
    monkeypatch.setitem(core['monitor_native'].__globals__, 'monitor_launcher', lambda: launcher)
    class Connection:
        async def __aenter__(self):
            connections.append(self)
            self.peer = socket.socket(socket.AF_UNIX); self.peer.connect(config['socket'])
            self.transport = types.SimpleNamespace(get_extra_info=lambda name: self.peer)
            return self
        async def __aexit__(self, *args):
            self.peer.close()
        async def send(self, raw):
            self.last = json.loads(raw); requests.append(self.last)
            if self.last.get('method') == 'thread/start':
                launcher['monitor_runtime_write'](runtime / 'ready.json',
                                                  dict(owner, native=dict(owner['native'], birth='revoked')))
        async def recv(self):
            if self.last.get('method') == 'thread/start':
                raise ConnectionResetError('connection lost after request delivery')
            return json.dumps({'id': 1, 'result': {}})
    monkeypatch.setattr(websockets.client, 'unix_connect', lambda *args, **kwargs: Connection())
    with pytest.raises(RuntimeError, match='reconcile before retry'):
        core['monitor_native'](dict(config, max_response_bytes=8192), 'thread/start', {'fixture': True})
    assert len(connections) == 1
    assert [r.get('method') for r in requests] == ['initialize', 'initialized', 'thread/start']


@pytest.mark.parametrize('missing_runtime', [False, True])
def test_passive_diagnostics_have_no_writes_or_optional_dependency(launcher, independent, monkeypatch,
                                                                  missing_runtime):
    import builtins
    import shutil
    config, owner, process, runtime, home = independent
    diagnostic = runpy.run_path(str(CLI.parents[2] / 'scripts/codex_monitor_diagnostics.py'))
    monkeypatch.setitem(diagnostic['monitor_status'].__globals__, 'launcher', lambda: launcher)
    if missing_runtime:
        shutil.rmtree(runtime.parent)
    before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in home.parent.rglob('*') if p.is_file()}
    real_open, real_import = os.open, builtins.__import__
    def read_only(path, flags, *args, **kwargs):
        assert not flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR), 'diagnostics attempted a filesystem write'
        return real_open(path, flags, *args, **kwargs)
    def no_websockets(name, *args, **kwargs):
        if name.startswith('websockets'):
            raise ImportError('optional package deliberately unavailable')
        return real_import(name, *args, **kwargs)
    with monkeypatch.context() as observation:
        observation.setattr(os, 'open', read_only)
        observation.setattr(builtins, '__import__', no_websockets)
        result = diagnostic['monitor_status'](config, codex=Path(sys.executable).resolve())
    assert result['server']['state'] == 'authenticated'
    assert result['check']['protocol'] == 'not_probed'
    assert result['gui']['tools'] == 'not_verified'
    assert result['cold_start']['errors'] == []
    assert process.poll() is None
    assert {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in home.parent.rglob('*') if p.is_file()} == before


@pytest.mark.parametrize('independent', ['rpc'], indirect=True)
def test_check_observes_protocol_without_republishing_registration(launcher, independent, monkeypatch):
    config, owner, _, runtime, home = independent
    diagnostic = runpy.run_path(str(CLI.parents[2] / 'scripts/codex_monitor_diagnostics.py'))
    monkeypatch.setitem(diagnostic['monitor_status'].__globals__, 'launcher', lambda: launcher)
    before = (runtime / 'ready.json').read_bytes(), (runtime / 'ready.json').stat().st_mtime_ns
    result = diagnostic['monitor_status'](config, codex=Path(sys.executable).resolve(), check=True)
    assert result['check'] == {'ready': True, 'protocol': 'verified'}
    assert ((runtime / 'ready.json').read_bytes(), (runtime / 'ready.json').stat().st_mtime_ns) == before


@pytest.mark.parametrize('flag', ['--status', '--check'])
def test_public_diagnostics_do_not_require_app_cli_or_venv(monkeypatch, flag):
    module = runpy.run_path(str(CLI.with_name('codex-monitor')))
    monkeypatch.setattr(sys, 'argv', ['codex-monitor', flag])
    monkeypatch.setattr(module['shutil'], 'which', lambda name: None)
    monkeypatch.setattr(Path, 'is_file', lambda path: False)
    calls = []
    def execute(binary, args):
        calls.append((str(binary), args)); raise SystemExit(37)
    monkeypatch.setattr(os, 'execv', execute)
    with pytest.raises(SystemExit) as result:
        module['main']()
    assert result.value.code == 37
    assert calls == [(sys.executable, [sys.executable, str(CLI), 'monitor-gitlab', 'launcher-status',
                                      *(['--check'] if flag == '--check' else [])])]


@pytest.mark.parametrize('independent', ['rpc'], indirect=True)
def test_incident_receipt_artifact_reconnects_only_after_old_native_termination(launcher, independent):
    config, owner, _, runtime, _ = independent
    artifact = json.loads((Path(__file__).parent / 'fixtures/codex-monitor-recovery.json').read_text())
    saved = artifact['ready']
    saved.update(codex_home=config['codex_home'], socket=owner['socket'],
                 native=retired_owner(launcher, owner)['native'])
    launcher['monitor_runtime_write'](runtime / 'ready.json', saved)
    assert launcher['register_gui_native'](config, lambda: None) == owner
    assert json.loads((runtime / 'ready.json').read_text()) == owner
    client = dict(artifact['separate_client'], pid=1)
    assert launcher['cold']()['describe_native_process'](client).startswith('VS Code Codex extension')


@pytest.mark.parametrize('independent', ['ordinary'], indirect=True)
def test_incident_missing_environment_reports_exact_launch_keys(launcher, independent):
    artifact = json.loads((Path(__file__).parent / 'fixtures/codex-monitor-recovery.json').read_text())
    config, _, process, _, _ = independent
    with pytest.raises(RuntimeError, match='Missing or incompatible launch settings') as result:
        launcher['native_owner'](config)
    for name in artifact['missing_launch_settings']:
        assert name in str(result.value)
    assert process.poll() is None


@pytest.mark.parametrize('independent', ['rpc'], indirect=True)
def test_registration_contenders_publish_one_generation_under_real_coordinator(launcher, independent):
    import threading
    config, owner, _, runtime, _ = independent
    old = retired_owner(launcher, owner)
    launcher['monitor_runtime_write'](runtime / 'ready.json', old)
    entered, release = threading.Event(), threading.Event()
    results, errors = [], []
    def hold():
        entered.set()
        assert release.wait(5), 'test did not release the held coordinator'
    def first():
        try:
            results.append(launcher['register_gui_native'](config, hold))
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=first)
    thread.start()
    try:
        assert entered.wait(5), 'first contender never reached validated admission'
        with pytest.raises(BlockingIOError):
            launcher['register_gui_native'](config, lambda: None)
        assert json.loads((runtime / 'ready.json').read_text()) == old
    finally:
        release.set(); thread.join(5)
    assert not thread.is_alive()
    assert errors == []
    assert results == [owner]
    modified = (runtime / 'ready.json').stat().st_mtime_ns
    assert launcher['register_gui_native'](config, lambda: None) == owner
    assert (runtime / 'ready.json').stat().st_mtime_ns == modified


@pytest.mark.parametrize('independent', ['rpc'], indirect=True)
def test_check_reports_separate_same_home_stdio_client_before_recovery(launcher, independent, monkeypatch):
    config, _, process, runtime, home = independent
    diagnostic = runpy.run_path(str(CLI.parents[2] / 'scripts/codex_monitor_diagnostics.py'))
    monkeypatch.setitem(diagnostic['monitor_status'].__globals__, 'launcher', lambda: launcher)
    child = subprocess.Popen([sys.executable, '-c', 'import sys;print("ready",flush=True);sys.stdin.read()',
                              'app-server'], env=dict(os.environ, CODEX_HOME=config['codex_home']),
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    before = (runtime / 'ready.json').read_bytes(), (home / 'config.toml').read_bytes()
    try:
        assert child.stdout.readline() == 'ready\n'
        result = diagnostic['monitor_status'](config, codex=Path(sys.executable).resolve(), check=True)
        assert result['server']['state'] == 'authenticated'
        assert result['check'] == {'protocol': 'verified', 'ready': False}
        assert len(result['cold_start']['blockers']) == 1
        assert result['cold_start']['blockers'][0]['process']['pid'] == child.pid
        assert result['cold_start']['blockers'][0]['client'] == 'separate stdio app-server'
        assert ((runtime / 'ready.json').read_bytes(), (home / 'config.toml').read_bytes()) == before
        assert child.poll() is None and process.poll() is None
    finally:
        child.terminate();child.wait(timeout=5)
        child.stdin.close();child.stdout.close()


def test_independent_owner_uses_native_identity_without_gui_and_rejects_stale_receipt(launcher, independent):
    config, owner, process, runtime, home = independent
    assert launcher['monitor_shared_owner'](config) == owner
    assert set(owner) == {'version','codex_home','socket','native','native_executable','socket_identity'}
    assert owner['native']['pid'] == process.pid
    changed = json.loads((runtime/'ready.json').read_text()); changed['native']['birth']='stale'
    (runtime/'ready.json').write_text(json.dumps(changed))
    with pytest.raises(RuntimeError, match='server registration changed'):
        launcher['monitor_shared_owner'](config)
    assert process.poll() is None
    launcher['monitor_runtime_write'](runtime/'ready.json', owner)
    (home/'config.toml').write_text((home/'config.toml').read_text()+'\n# external edit\n')
    assert launcher['monitor_shared_owner'](config) == owner
    (home/'config.toml').write_text((home/'config.toml').read_text().replace('code_mode_host=true','code_mode_host=false'))
    with pytest.raises(RuntimeError, match='has not enabled the tools'):
        launcher['monitor_shared_owner'](config)
    assert process.poll() is None


def test_independent_owner_rejects_other_connected_peer(launcher, independent):
    config, owner, process, runtime, home = independent
    left, right = socket.socketpair()
    try:
        transport = types.SimpleNamespace(get_extra_info=lambda name: left)
        with pytest.raises(RuntimeError, match='another native server'):
            launcher['monitor_shared_peer'](config, types.SimpleNamespace(transport=transport))
    finally:
        left.close(); right.close()
    assert process.poll() is None


def test_monitor_revalidates_after_initialize_before_protected_rpc(launcher, independent, monkeypatch):
    import websockets.client
    config, owner, process, runtime, home = independent
    core = runpy.run_path(str(CLI))
    namespace = core['monitor_native'].__globals__
    monkeypatch.setitem(namespace, 'monitor_launcher', lambda: launcher)
    requests = []
    class Connection:
        async def __aenter__(self):
            self.peer = socket.socket(socket.AF_UNIX); self.peer.connect(config['socket'])
            self.transport = types.SimpleNamespace(get_extra_info=lambda name: self.peer)
            return self
        async def __aexit__(self, *args):
            self.peer.close()
        async def send(self, raw):
            request = json.loads(raw); requests.append(request)
            if request.get('method') == 'initialized':
                stale = dict(owner, native=dict(owner['native'], birth='revoked'))
                launcher['monitor_runtime_write'](runtime/'ready.json', stale)
        async def recv(self):
            return json.dumps({'id': 1, 'result': {}})
    monkeypatch.setattr(websockets.client, 'unix_connect', lambda *args, **kwargs: Connection())
    with pytest.raises(RuntimeError, match='server registration changed'):
        core['monitor_native'](dict(config, max_response_bytes=8192), 'thread/start', {'must_not_send': True})
    assert [request.get('method') for request in requests] == ['initialize', 'initialized']
    assert process.poll() is None


def test_refresh_uses_native_reload_contract_and_waits_for_connected_catalog(launcher, monkeypatch):
    import asyncio
    namespace = launcher['reload_tools'].__globals__
    calls = []
    async def rpc(config, methods):
        calls.append(methods)
        if len(calls) == 1:
            assert methods == [('config/mcpServer/reload', None), ('mcpServerStatus/list', {})]
            return [{}, {'data': []}]
        assert methods == [('mcpServerStatus/list', {})]
        return [{'data': [{'name': 'codex_app', 'pluginId': 'codex-app-tools@openai-bundled', 'runtimeStatus': 'connected', 'tools': {'list_threads': {}}}]}]
    monkeypatch.setitem(namespace, 'native_rpc', rpc)
    asyncio.run(launcher['reload_tools']({'native_timeout': 1}))
    assert len(calls) == 2


def test_live_attach_requires_effective_flags_without_rewriting_layers(launcher, monkeypatch):
    namespace = launcher['verify_effective'].__globals__
    async def rpc(config, methods, **kwargs):
        assert methods == [('config/read', {'includeLayers': True})]
        return [{'config': {'features': {'code_mode_host': False}}}]
    monkeypatch.setitem(namespace, 'native_rpc', rpc)
    with pytest.raises(RuntimeError, match='Another configuration layer.*features.code_mode_host'):
        launcher['verify_effective']({}, {'native': {'pid': 123}})


def test_failed_catalog_startup_refreshes_after_renderer_becomes_available(launcher, monkeypatch):
    import asyncio
    namespace = launcher['reload_tools'].__globals__
    calls = []
    async def rpc(config, methods):
        calls.append(methods)
        if len(calls) == 1:
            return [{}, {'data': []}]
        if len(calls) == 2:
            return [{'data': [{'name': 'codex_app', 'pluginId': 'codex-app-tools@openai-bundled', 'runtimeStatus': 'failed', 'toolsError': 'renderer unavailable'}]}]
        if len(calls) == 3:
            assert methods == [('config/mcpServer/reload', None)]
            return [{}]
        assert methods == [('mcpServerStatus/list', {})]
        return [{'data': [{'name': 'codex_app', 'pluginId': 'codex-app-tools@openai-bundled', 'runtimeStatus': 'connected', 'tools': {'list_threads': {}}}]}]
    monkeypatch.setitem(namespace, 'native_rpc', rpc)
    asyncio.run(launcher['reload_tools']({'native_timeout': 3}))
    assert len(calls) == 4


def test_app_tools_address_does_not_depend_on_caller_temp_environment(launcher, tmp_path, monkeypatch):
    import tempfile
    # Keep both caller addresses valid AF_UNIX lengths so the old source fails
    # for switching bases, rather than unsafe permissions or an overlong address.
    with tempfile.TemporaryDirectory(prefix='ct-', dir='/tmp') as short:
        first = Path(short)/'a'; second = Path(short)/'b'
        first.mkdir(mode=0o700); second.mkdir(mode=0o700)
        config = {'codex_home': str(tmp_path/'home')}
        monkeypatch.setenv('TMPDIR', str(first))
        monkeypatch.setattr(tempfile, 'tempdir', str(first))
        address = launcher['monitor_app_tools_directory'](config, create=True)
        try:
            monkeypatch.setenv('TMPDIR', str(second))
            monkeypatch.setattr(tempfile, 'tempdir', str(second))
            assert launcher['monitor_app_tools_directory'](config) == address
            assert address.parent == Path('/tmp').resolve()
        finally:
            address.rmdir()


def private_config(core, root, monkeypatch):
    home = root/'codex'; home.mkdir(mode=0o700)
    runtime = root/'run'; runtime.mkdir(mode=0o700)
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(runtime))
    raw = core['monitor_default_config']('https://gitlab.example.invalid/team/project', 42, 'gitlab')
    raw.update(codex_home=str(home), cwd=str(root), socket=str(home/'app-server-control/app-server-control.sock'),
               state_file=str(root/'state/state.sqlite3'), queue_file=str(root/'queue/queue.sqlite3'))
    path = root/'monitor.json'; path.write_text(json.dumps(raw)); path.chmod(0o600)
    return path, core['mq_config'](path)


@pytest.mark.parametrize('arguments,origin', [
    (['--version'], 'Codex Desktop'),
    (['-c','features.code_mode_host=true','app-server','--analytics-default-enabled'], 'Codex Desktop'),
    (['-c','features.code_mode_host=true','app-server','--analytics-default-enabled',
      '-c','plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled=true',
      '-c','plugins.code-review@openai-bundled.mcp_servers.code-review.enabled=true'], 'codex_latex_preview'),
])
def test_ordinary_gui_helpers_delegate_without_starting_or_attaching_native(launcher, tmp_path, monkeypatch, arguments, origin):
    import signal
    core = launcher['support']()
    path, config = private_config(core, tmp_path, monkeypatch)
    runtime = core['monitor_shared_runtime'](config, create=True)
    gui = core['monitor_process'](os.getppid())
    native = str(Path(sys.executable).resolve())
    launch = {'gui': gui, 'app': gui['exe'], 'codex': native, 'config': str(path),
              'codex_home': config['codex_home'], 'wrapper': str(runtime/'codex-proxy')}
    core['monitor_runtime_write'](runtime/'launch.json', launch)
    monkeypatch.setenv('CODEX_STATS_APP_LAUNCH', str(runtime/'launch.json'))
    monkeypatch.setenv('CODEX_HOME', config['codex_home'])
    monkeypatch.setenv('CODEX_INTERNAL_ORIGINATOR_OVERRIDE', origin)
    monkeypatch.setenv('CODEX_CLI_PATH', launch['wrapper'])
    monkeypatch.setattr(sys, 'argv', [launch['wrapper'], *arguments])
    calls = []
    def execute(binary, words, environment):
        calls.append((binary, words, environment)); raise SystemExit(43)
    monkeypatch.setattr(os, 'execve', execute)
    previous = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGHUP)}
    try:
        with pytest.raises(SystemExit) as result:
            launcher['monitor_app_proxy_main']()
        assert result.value.code == 43
    finally:
        for number, handler in previous.items():signal.signal(number, handler)
    assert len(calls) == 1
    binary, words, env = calls[0]
    assert binary == native and words == [native, *arguments]
    assert env['CODEX_CLI_PATH'] == native and 'CODEX_STATS_APP_LAUNCH' not in env
    assert not (runtime/'ready.json').exists()
    assert not Path(config['_socket_alias']).exists()


@pytest.mark.parametrize('failure,expected', [
    (subprocess.TimeoutExpired(['native','app-server','daemon','start'], 1), 'may have started'),
    (subprocess.CalledProcessError(1, ['wmctrl','-ia','0x123']), 'your work were preserved'),
])
def test_expected_launch_failures_reach_persistent_gui_error_channel(launcher, tmp_path, monkeypatch, failure, expected):
    core = runpy.run_path(str(CLI))
    path, config = private_config(core, tmp_path, monkeypatch)
    namespace = launcher['monitor_launch_app'].__globals__
    def failed(*args):raise failure
    monkeypatch.setitem(namespace, '_monitor_launch_app', failed)
    messages = []
    monkeypatch.setitem(launcher, 'message', lambda text, **options: messages.append((text, options)))
    monkeypatch.setitem(core['mq_main'].__globals__, 'monitor_launcher', lambda: launcher)
    monkeypatch.setattr(sys, 'argv', [str(CLI), 'monitor-gitlab', '--config', str(path),
                                    'launch-app', '--app', sys.executable, '--codex', sys.executable])
    assert core['mq_main']() == 1
    assert len(messages) == 1 and expected in messages[0][0]
    assert messages[0][1] == {'gui': True, 'error': True}
    assert not Path(config['_socket_alias']).exists()


def test_focus_targets_only_verified_gui_pid_and_propagates_window_manager_failure(launcher, monkeypatch):
    import shutil
    gui = launcher['monitor_process'](os.getpid())
    calls = []
    monkeypatch.setattr(shutil, 'which', lambda name: '/fixture/wmctrl')
    def run(arguments, **kwargs):
        calls.append(arguments)
        if arguments == ['/fixture/wmctrl','-lp']:
            return types.SimpleNamespace(stdout=f'0x111 0 99999 host unrelated\n0x222 0 {gui["pid"]} host Codex\n')
        raise subprocess.CalledProcessError(1, arguments)
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(subprocess.CalledProcessError):launcher['focus_gui'](gui, Path('/fixture/app'), 1)
    assert calls == [['/fixture/wmctrl','-lp'], ['/fixture/wmctrl','-ia','0x222']]


APP = Path('/usr/lib/chatgpt/ChatGPT')


def singleton_gui(tmp_path, lock_owner, socket_cookie='42', profile_name='profile', joined=True):
    """Make this test process a GUI whose Chromium child names a profile with a singleton socket."""
    profile, sockets = tmp_path/profile_name, tmp_path/'s'
    profile.mkdir(); sockets.mkdir()
    (profile/'SingletonLock').symlink_to(f'{socket.gethostname()}-{lock_owner}')
    (profile/'SingletonCookie').symlink_to('42')
    (sockets/'SingletonCookie').symlink_to(socket_cookie)
    (profile/'SingletonSocket').symlink_to(sockets/'SingletonSocket')
    # Chromium rewrites a child's arguments into one space-joined process title; reproduce that shape.
    title = f'{APP} --type=zygote --enable-crash-reporter=, --user-data-dir={profile} --change-stack-guard-on-fork=enable'
    arguments = (['bash', '-c', 'exec -a "$0" sleep 60', title] if joined else
                 [sys.executable, '-c', 'import time; time.sleep(60)',
                  '--type=zygote', '--user-data-dir=' + str(profile)])
    child = subprocess.Popen(arguments)
    return profile, sockets/'SingletonSocket', child


@pytest.mark.parametrize('joined', [True, False], ids=['chromium-title', 'nul-argv'])
def test_profile_preserves_spaces_unicode_and_option_like_text(launcher, monkeypatch, joined):
    import threading
    with tempfile.TemporaryDirectory(prefix='cm-p-') as name:
        profile, path, child = singleton_gui(Path(name), os.getpid(),
            profile_name='perfil ação --flag=valor final', joined=joined)
        received = []
        stop = serve_singleton(path, b'ACK', received, threading.Event())
        gui = launcher['monitor_process'](os.getpid())
        fake_wmctrl(monkeypatch, gui, lambda: bool(received))
        try:
            launcher['focus_gui'](gui, APP, 5)
            assert received == [handoff(profile)]
        finally:
            stop(); child.kill(); child.wait()


def test_profile_rejects_multiple_valid_candidates_instead_of_selecting_prefix(launcher, tmp_path):
    profile, _, child = singleton_gui(tmp_path, os.getpid(), profile_name='profile --flag=long')
    prefix = tmp_path/'profile'; prefix.mkdir()
    (prefix/'SingletonLock').symlink_to(f'{socket.gethostname()}-{os.getpid()}')
    try:
        with pytest.raises(RuntimeError, match='instance could not be verified'):
            launcher['gui_profile'](launcher['monitor_process'](os.getpid()))
    finally:
        child.kill(); child.wait()


def test_profile_does_not_choose_a_valid_whitespace_prefix(launcher, tmp_path):
    profile, _, child = singleton_gui(tmp_path, os.getpid(), profile_name='profile with spaces')
    prefix = tmp_path/'profile'; prefix.mkdir()
    (prefix/'SingletonLock').symlink_to(f'{socket.gethostname()}-{os.getpid()}')
    try:
        assert launcher['gui_profile'](launcher['monitor_process'](os.getpid())) == profile
    finally:
        child.kill(); child.wait()


@pytest.mark.parametrize('stall', ['-lp', '-ia'])
def test_wmctrl_timeouts_use_remaining_budget_and_gui_error(launcher, monkeypatch, stall):
    import shutil
    import time
    gui = launcher['monitor_process'](os.getpid()); budgets = []
    clock = [10.0]
    monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(shutil, 'which', lambda name: '/fixture/wmctrl')
    def run(arguments, **kwargs):
        budgets.append(kwargs.get('timeout'))
        assert kwargs.get('timeout') is not None, 'wmctrl was called without a deadline'
        if arguments[1] == stall:
            raise subprocess.TimeoutExpired(arguments, kwargs['timeout'])
        clock[0] += .4
        return types.SimpleNamespace(stdout=f'0x222 0 {gui["pid"]} host Codex\n')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(RuntimeError, match='window.*time') as error:
        launcher['launch_operation'](launcher['focus_gui'], gui, APP, 1)
    assert 'native manager' not in str(error.value)
    assert budgets == pytest.approx([1] if stall == '-lp' else [1, .6])


def test_singleton_reads_and_later_wmctrl_share_one_deadline(launcher, monkeypatch):
    import threading
    import time
    with tempfile.TemporaryDirectory(prefix='cm-t-') as name:
        profile, path, child = singleton_gui(Path(name), os.getpid())
        received = []
        stop = serve_singleton(path, b'ACK', received, threading.Event())
        gui = launcher['monitor_process'](os.getpid())
        clock = [10.0]; socket_budgets = []; wm_budgets = []
        original_socket = socket.socket
        class Connection:
            def __init__(self, *args, **kwargs):self.connection = original_socket(*args, **kwargs)
            def __getattr__(self, key):return getattr(self.connection, key)
            def __enter__(self):return self
            def __exit__(self, *args):self.connection.close()
            def settimeout(self, value):
                socket_budgets.append(value); self.connection.settimeout(value)
            def recv(self, size):
                result = self.connection.recv(size); clock[0] += .1; return result
        monkeypatch.setattr(socket, 'socket', lambda *args, **kwargs:
                            original_socket(*args, **kwargs) if 'fileno' in kwargs else Connection(*args, **kwargs))
        monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
        import shutil
        monkeypatch.setattr(shutil, 'which', lambda name: '/fixture/wmctrl')
        def run(arguments, **kwargs):
            wm_budgets.append(kwargs.get('timeout'))
            clock[0] += .2
            return types.SimpleNamespace(stdout=f'0x333 0 {gui["pid"]} host Codex\n' if received else '')
        monkeypatch.setattr(subprocess, 'run', run)
        try:
            launcher['focus_gui'](gui, APP, 1)
            assert received == [handoff(profile)]
            assert socket_budgets == pytest.approx([.8, .8, .8, .7])
            assert wm_budgets == pytest.approx([1, .6, .4])
        finally:
            stop(); child.kill(); child.wait()


def test_window_polling_does_not_reset_the_operation_budget(launcher, monkeypatch):
    import threading
    import time
    with tempfile.TemporaryDirectory(prefix='cm-t-') as name:
        profile, path, child = singleton_gui(Path(name), os.getpid())
        received = []
        stop = serve_singleton(path, b'ACK', received, threading.Event())
        gui = launcher['monitor_process'](os.getpid()); clock = [10.0]; budgets = []
        monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
        monkeypatch.setattr(time, 'sleep', lambda seconds: clock.__setitem__(0, clock[0]+seconds))
        import shutil
        monkeypatch.setattr(shutil, 'which', lambda name: '/fixture/wmctrl')
        def run(arguments, **kwargs):
            assert arguments == ['/fixture/wmctrl', '-lp']
            budgets.append(kwargs.get('timeout')); clock[0] += .15
            return types.SimpleNamespace(stdout='')
        monkeypatch.setattr(subprocess, 'run', run)
        try:
            with pytest.raises(RuntimeError, match='window.*(time|available)'):
                launcher['focus_gui'](gui, APP, 1)
            assert received == [handoff(profile)]
            assert len(budgets) >= 3 and all(a > b > 0 for a, b in zip(budgets, budgets[1:]))
            assert clock[0] <= 11.15
        finally:
            stop(); child.kill(); child.wait()


def handoff(profile):
    return b'\0'.join([b'START', os.fsencode(os.getcwd()), os.fsencode(APP),
                        b'--no-startup-window', b'--user-data-dir=' + os.fsencode(profile)])


def serve_singleton(path, reply, received, release):
    """Answer one handoff as Chromium does: read until the client half-closes, then reply."""
    import threading
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(1)
    def answer():
        connection, _ = listener.accept()
        with connection:
            message = b''
            while chunk := connection.recv(4096):
                message += chunk
            received.append(message)
            if reply is None:
                release.wait(10)
            elif message:
                connection.sendall(reply)
    thread = threading.Thread(target=answer, daemon=True); thread.start()
    def stop():
        release.set()
        if thread.is_alive():
            # Unblock an accept() that the refused client never reached.
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as unblock:unblock.connect(str(path))
        thread.join(5)
        listener.close()
        assert not thread.is_alive()
    return stop


def fake_wmctrl(monkeypatch, gui, shown):
    import shutil
    calls = []
    monkeypatch.setattr(shutil, 'which', lambda name: '/fixture/wmctrl')
    def run(arguments, **kwargs):
        calls.append(arguments)
        if arguments == ['/fixture/wmctrl','-lp']:
            window = f'0x333 0 {gui["pid"]} host Codex\n' if shown() else ''
            return types.SimpleNamespace(stdout='0x111 0 99999 host unrelated\n' + window)
        return types.SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, 'run', run)
    return calls


def test_closed_window_is_reopened_through_registered_gui_singleton_then_focused(launcher, tmp_path, monkeypatch):
    import threading
    profile, path, child = singleton_gui(tmp_path, os.getpid())
    received = []
    stop = serve_singleton(path, b'ACK', received, threading.Event())
    gui = launcher['monitor_process'](os.getpid())
    # The GUI maps a window only after it has received the handoff.
    calls = fake_wmctrl(monkeypatch, gui, lambda: bool(received))
    try:
        launcher['focus_gui'](gui, APP, 5)
    finally:
        stop(); child.kill(); child.wait()
    assert received == [handoff(tmp_path/'profile')]
    assert calls[0] == ['/fixture/wmctrl','-lp'] and calls[-1] == ['/fixture/wmctrl','-ia','0x333']
    assert calls.count(['/fixture/wmctrl','-ia','0x333']) == 1


FOREIGN_PEER = ('import socket, sys\n'
                'listener = socket.socket(socket.AF_UNIX); listener.bind(sys.argv[1]); listener.listen(1)\n'
                'open(sys.argv[3], "w").close()\n'
                'connection, _ = listener.accept(); message = b""\n'
                'while chunk := connection.recv(4096): message += chunk\n'
                'open(sys.argv[2], "wb").write(message)\n')


@pytest.mark.parametrize('case,expected', [
    ('foreign-lock', 'instance could not be verified'),
    ('cookie-mismatch', 'instance could not be verified'),
    ('shutting-down', 'did not accept the request'),
    ('silent', 'did not respond to the request'),
    ('no-window', 'window is not yet available'),
], ids=['foreign-lock', 'cookie-mismatch', 'shutting-down', 'silent', 'no-window'])
def test_unconfirmed_reopen_is_refused_without_focusing(launcher, tmp_path, monkeypatch, case, expected):
    import threading
    profile, path, child = singleton_gui(tmp_path, 1 if case == 'foreign-lock' else os.getpid(),
                                         '43' if case == 'cookie-mismatch' else '42')
    received = []
    stop = serve_singleton(path, {'shutting-down': b'SHUTDOWN', 'silent': None}.get(case, b'ACK'),
                           received, threading.Event())
    gui = launcher['monitor_process'](os.getpid())
    calls = fake_wmctrl(monkeypatch, gui, lambda: False)
    try:
        with pytest.raises(RuntimeError, match=expected):
            launcher['focus_gui'](gui, APP, 0.5)
        sent = list(received)
    finally:
        stop(); child.kill(); child.wait()
    # A refused instance never receives the request; a reached one got exactly one.
    assert sent == ([] if case in {'foreign-lock', 'cookie-mismatch'} else [handoff(profile)])
    # Nothing is focused; only an accepted handoff waits for the window to appear.
    assert all(call == ['/fixture/wmctrl','-lp'] for call in calls)
    assert (len(calls) > 1) is (case == 'no-window')


def test_reopen_refuses_a_socket_not_served_by_the_registered_gui(launcher, tmp_path, monkeypatch):
    import time
    profile, path, child = singleton_gui(tmp_path, os.getpid())
    record, listening = tmp_path/'foreign.bin', tmp_path/'listening'
    peer = subprocess.Popen([sys.executable, '-c', FOREIGN_PEER, str(path), str(record), str(listening)])
    deadline = time.monotonic() + 10
    while not listening.exists():
        assert time.monotonic() < deadline and peer.poll() is None
        time.sleep(.05)
    gui = launcher['monitor_process'](os.getpid())
    calls = fake_wmctrl(monkeypatch, gui, lambda: False)
    try:
        with pytest.raises(RuntimeError, match='instance could not be verified'):
            launcher['focus_gui'](gui, APP, 5)
        assert peer.wait(10) == 0
    finally:
        child.kill(); child.wait()
        if peer.poll() is None:peer.kill(); peer.wait()
    assert record.read_bytes() == b''
    assert calls == [['/fixture/wmctrl','-lp']]


def test_concurrent_launchers_classify_under_one_held_coordinator(launcher, tmp_path, monkeypatch):
    import queue
    import threading
    core = launcher['support']()
    path, config = private_config(core, tmp_path, monkeypatch)
    config['native_timeout'] = 8
    agent_socket = str(tmp_path / 'agent.sock')
    monkeypatch.setenv('SSH_AUTH_SOCK', agent_socket)
    monkeypatch.setenv('CODEX_APP_TOOLS_PIPE_PATH', '/unrelated/tools.sock')
    monkeypatch.setenv('CODEX_STATS_APP_LAUNCH', '/unrelated/launch.json')
    monkeypatch.setenv('CODEX_MONITOR_LAUNCHER_PROTOCOL', 'untrusted-caller')
    resources = tmp_path/'resources'; (resources/'cua_node/bin').mkdir(parents=True)
    codex = resources/'codex'; codex.write_text('#!/usr/bin/python3\n'); codex.chmod(0o700)
    node = resources/'cua_node/bin/node'; node.write_text('#!/usr/bin/python3\n'); node.chmod(0o700)
    namespace = launcher['ensure_server_once'].__globals__
    monkeypatch.setitem(namespace, 'installed_native', lambda config: Path(sys.executable).resolve())
    alias = Path(config['_socket_alias'])
    owner = {'native': {'pid': 4321}, 'codex_home': config['codex_home'], 'socket': str(alias)}
    monkeypatch.setitem(namespace, 'native_owner', lambda config: owner)
    monkeypatch.setitem(namespace, 'verify_effective', lambda *args: None)
    cold_class = launcher['cold']()['MonitorColdStart']
    original_lock = cold_class.lock_file
    events = queue.Queue(); second_started = threading.Event(); second_done = threading.Event()
    acquisitions = {}; launches = []; environments = []; results = {}; errors = {}
    def lock_file(authority, target, **kwargs):
        name = threading.current_thread().name
        if target.name == 'launch.lock':
            acquisitions[name] = acquisitions.get(name, 0) + 1
            if name == 'first' and acquisitions[name] == 2:
                # Force the old release/reacquire race: the peer finishes in the gap.
                events.put('second-acquisition')
                assert second_done.wait(8)
            if name == 'second':second_started.set()
        return original_lock(authority, target, **kwargs)
    monkeypatch.setattr(cold_class, 'lock_file', lock_file)
    def start_native(arguments, **kwargs):
        launches.append(arguments)
        environments.append(kwargs['env'])
        if threading.current_thread().name == 'first':
            events.put('native-start')
            assert second_started.wait(8)
        alias.touch()
        return types.SimpleNamespace(returncode=0, stdout=json.dumps({'pid': 4321}), stderr='')
    monkeypatch.setattr(subprocess, 'run', start_native)
    def launch(name):
        try:results[name] = launcher['ensure_server'](config, codex)
        except BaseException as error:errors[name] = error
        finally:
            if name == 'second':second_done.set()
    first = threading.Thread(target=launch, args=('first',), name='first')
    second = threading.Thread(target=launch, args=('second',), name='second')
    first.start()
    try:
        assert events.get(timeout=8) in {'native-start','second-acquisition'}
        second.start()
        first.join(timeout=12); second.join(timeout=12)
        assert not first.is_alive() and not second.is_alive()
        assert errors == {}
        assert {name: result[0] for name, result in results.items()} == {'first': owner, 'second': owner}
        assert len(launches) == 1
        assert sum(result[1] for result in results.values()) == 1
        environment, = environments
        assert environment['SSH_AUTH_SOCK'] == agent_socket
        directory = launcher['monitor_app_tools_directory'](config)
        assert environment['CODEX_APP_TOOLS_PIPE_PATH'] == str(directory / 'host.sock')
        assert environment['CODEX_MONITOR_LAUNCHER_PROTOCOL'] == '1'
        assert 'CODEX_STATS_APP_LAUNCH' not in environment
    finally:
        second_started.set(); second_done.set()
        first.join(timeout=10)
        if second.ident is not None:second.join(timeout=10)
        try:
            directory = launcher['monitor_app_tools_directory'](config)
            directory.rmdir()
        except FileNotFoundError:
            pass


def test_aggregate_catalog_is_ready_without_thread_scoped_runtime_status(launcher, monkeypatch):
    import asyncio
    namespace = launcher['reload_tools'].__globals__
    catalog = {'data': [{'name': 'codex_app', 'pluginId': 'codex-app-tools@openai-bundled',
                        'tools': {'list_threads': {}}, 'toolsError': None}]}
    async def rpc(config, methods):
        return [{}, catalog] if len(methods) == 2 else [catalog]
    monkeypatch.setitem(namespace, 'native_rpc', rpc)
    asyncio.run(launcher['reload_tools']({'native_timeout': 1}))


def test_gui_inventory_ignores_foreign_zombie_and_unrelated_nondumpable_processes(launcher, tmp_path, monkeypatch):
    home = tmp_path/'home'; home.mkdir()
    app = Path('/installed/ChatGPT')
    class Field:
        def __init__(self, value=None, failure=None):self.value, self.failure = value, failure
        def read_bytes(self):
            if self.failure:raise self.failure
            return self.value
        def read_text(self):return self.read_bytes().decode()
    class Entry:
        def __init__(self, pid, uid, cmdline, comm='unrelated'):
            self.name, self.uid, self.cmdline, self.comm = str(pid), uid, cmdline, comm
        def stat(self):return types.SimpleNamespace(st_uid=self.uid)
        def __truediv__(self, name):
            if name == 'cmdline':return self.cmdline
            if name == 'comm':return Field(self.comm.encode())
            raise AssertionError(name)
    entries = [
        Entry(1, os.getuid()+1, Field(failure=AssertionError('foreign process must be skipped'))),
        Entry(2, os.getuid(), Field(b'')),
        Entry(3, os.getuid(), Field(failure=PermissionError('unrelated nondumpable')), 'systemd'),
        Entry(4, os.getuid(), Field(b'/installed/ChatGPT\0--type=renderer\0')),
        Entry(5, os.getuid(), Field(b'/installed/ChatGPT\0'), 'ChatGPT'),
    ]
    namespace = launcher['gui_processes'].__globals__
    original_path = Path
    monkeypatch.setitem(namespace, 'Path', lambda value: types.SimpleNamespace(iterdir=lambda: iter(entries))
                        if str(value) == '/proc' else original_path(value))
    authenticated = []
    gui = {'pid': 5, 'birth': 'fixture', 'exe': str(app), 'parent': 9}
    def process(pid):
        authenticated.append(pid); assert pid == 5; return gui
    monkeypatch.setitem(namespace, 'monitor_process', process)
    assert list(launcher['gui_processes'](app)) == [gui]
    assert authenticated == [5]


GUI_FIXTURE = '''import json, os, subprocess, sys
spec = json.loads(sys.stdin.readline())
children = []
try:
    if spec['relay']:
        children.append(subprocess.Popen([sys.executable, spec['wrapper'], *spec['bootstrap']],
            env=dict(os.environ, **spec['environment'])))
    children.append(subprocess.Popen([sys.executable, '-c', 'import signal; signal.pause()',
        '--type=zygote', '--user-data-dir=' + spec['profile']]))
    print(json.dumps([p.pid for p in children]), flush=True)
    sys.stdin.read()
finally:
    for child in children:
        child.terminate()
        child.wait(10)
'''


@pytest.fixture
def gui_instances(launcher, monkeypatch, tmp_path):
    """Real GUI/relay/Chromium-child identities; only OS GUI inventory and wmctrl are substituted."""
    import selectors
    instances = []
    base = tmp_path/'run'; base.mkdir(mode=0o700)
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(base))
    namespace = launcher['verify_existing_gui'].__globals__
    monkeypatch.setitem(namespace, 'gui_processes', lambda app: (item.gui for item in instances
                        if item.process.poll() is None))
    def create(name='default', relay=True, ready=True):
        home = tmp_path/('.codex' if name == 'default' else name); home.mkdir(mode=0o700)
        config = {'codex_home': str(home), 'state_file': str(tmp_path/'state/monitor.sqlite'), 'native_timeout': 1}
        runtime = launcher['support']()['monitor_shared_runtime'](config, create=True)
        wrapper = runtime/'codex-proxy'
        wrapper.write_text(f'#!{sys.executable}\nimport signal\nsignal.pause()\n'); wrapper.chmod(0o700)
        env = {key: value for key, value in os.environ.items() if key not in
               {'HOME', 'CODEX_HOME', 'CODEX_STATS_APP_LAUNCH', 'CODEX_INTERNAL_ORIGINATOR_OVERRIDE'}}
        process = subprocess.Popen([sys.executable, '-c', GUI_FIXTURE], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, text=True, env=env)
        gui = launcher['monitor_process'](process.pid)
        profile = tmp_path/(name+' profile'); profile.mkdir()
        (profile/'SingletonLock').symlink_to(f'{socket.gethostname()}-{process.pid}')
        launch = {'gui': dict(gui, exe='/fixture/pre-exec-python'), 'app': gui['exe'],
                  'codex': sys.executable, 'config': str(tmp_path/'monitor.json'),
                  'codex_home': str(home), 'wrapper': str(wrapper)}
        launcher['monitor_runtime_write'](runtime/'launch.json', launch)
        environment = {'CODEX_HOME': str(home), 'CODEX_STATS_APP_LAUNCH': str(runtime/'launch.json'),
                       'XDG_RUNTIME_DIR': str(base), 'CODEX_INTERNAL_ORIGINATOR_OVERRIDE': 'Codex Desktop'}
        bootstrap = ['-c', 'features.code_mode_host=true', 'app-server', '--analytics-default-enabled',
            '-c', 'plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled=true',
            '-c', 'plugins.code-review@openai-bundled.mcp_servers.code-review.enabled=true']
        process.stdin.write(json.dumps({'relay': relay, 'wrapper': str(wrapper), 'bootstrap': bootstrap,
                                       'environment': environment, 'profile': str(profile)})+'\n')
        process.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(10), 'owned GUI fixture did not start'
        children = json.loads(process.stdout.readline())
        proxy = launcher['monitor_process'](children[0]) if relay else None
        if ready and relay:
            launcher['monitor_runtime_write'](runtime/'gui-ready.json', {'gui': gui, 'proxy': proxy})
        item = types.SimpleNamespace(process=process, gui=gui, proxy=proxy, config=config, runtime=runtime,
                                     profile=profile, launch=launch, wrapper=wrapper)
        instances.append(item)
        return item
    yield create
    for item in reversed(instances):
        item.process.stdin.close()
        assert item.process.wait(10) == 0
        item.process.stdout.close()


def gui_launch_boundary(launcher, monkeypatch, item):
    effects = []
    namespace = launcher['_monitor_launch_app'].__globals__
    def ensure(config, codex):
        effects.append('ensure'); return {}, False, None
    def execute(*args):
        effects.append('exec'); raise SystemExit(43)
    monkeypatch.setitem(namespace, 'ensure_server', ensure)
    monkeypatch.setitem(namespace, 'message', lambda *args, **kwargs: effects.append('message'))
    monkeypatch.setattr(os, 'execve', execute)
    def launch():
        return launcher['_monitor_launch_app'](item.config, Path(item.launch['config']),
            Path(item.gui['exe']), Path(sys.executable), [])
    return effects, launch


@pytest.mark.parametrize('name,ready', [('default', True), ('custom home', True), ('starting', False),
                                     ('reparented', True)])
def test_reuse_authenticates_erased_gui_environment_via_actual_relay(
        launcher, monkeypatch, gui_instances, name, ready):
    item = gui_instances(name, ready=ready)
    if name == 'reparented':
        launcher['monitor_runtime_write'](item.runtime/'gui-ready.json',
            {'gui': dict(item.gui, parent=1), 'proxy': item.proxy})
    assert 'CODEX_HOME' not in launcher['process_environment'](item.gui['pid'])
    effects, launch = gui_launch_boundary(launcher, monkeypatch, item)
    calls = fake_wmctrl(monkeypatch, item.gui, lambda: True)
    before = (item.runtime/'launch.json').read_bytes()
    launch()
    assert effects == ['ensure', 'message']
    assert calls == [['/fixture/wmctrl', '-lp'], ['/fixture/wmctrl', '-ia', '0x333']]
    assert (item.runtime/'launch.json').read_bytes() == before


@pytest.mark.parametrize('damage', ['no-relay', 'home', 'birth', 'app', 'wrapper', 'ready-proxy',
                                     'unprivate', 'wrong-location', 'unrelated-child', 'dead-relay', 'profile-lock'])
def test_unconfirmed_registration_refuses_before_native_or_gui_effects(
        launcher, monkeypatch, gui_instances, damage):
    item = gui_instances(relay=damage != 'no-relay')
    launch_path = item.runtime/'launch.json'
    if damage == 'home':item.launch['codex_home'] += '-wrong'
    elif damage == 'birth':item.launch['gui']['birth'] += '-wrong'
    elif damage == 'app':item.launch['app'] = '/wrong/app'
    elif damage == 'wrapper':item.launch['wrapper'] += '-wrong'
    elif damage == 'ready-proxy':
        launcher['monitor_runtime_write'](item.runtime/'gui-ready.json', {'gui': item.gui, 'proxy': item.gui})
    elif damage == 'unrelated-child':
        # A different process's live identity in the receipt cannot authorize this child.
        launcher['monitor_runtime_write'](item.runtime/'gui-ready.json',
            {'gui': item.gui, 'proxy': launcher['monitor_process'](os.getpid())})
    elif damage == 'dead-relay':
        import signal
        os.kill(item.proxy['pid'], signal.SIGTERM)
        # Wait for our owned child to terminate; it remains a zombie until its GUI reaps it.
        import time
        deadline = time.monotonic()+5
        while Path(f'/proc/{item.proxy["pid"]}/stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z':
            assert time.monotonic() < deadline
            time.sleep(.01)
    elif damage == 'profile-lock':
        (item.profile/'SingletonLock').unlink()
        (item.profile/'SingletonLock').symlink_to(f'{socket.gethostname()}-1')
    launcher['monitor_runtime_write'](launch_path, item.launch)
    if damage == 'unprivate':launch_path.chmod(0o644)
    elif damage == 'wrong-location':
        other = item.runtime/'elsewhere.json'; launch_path.rename(other); launch_path.symlink_to(other)
    effects, launch = gui_launch_boundary(launcher, monkeypatch, item)
    calls = fake_wmctrl(monkeypatch, item.gui, lambda: True)
    with pytest.raises(RuntimeError, match='configuration and') as result:
        launch()
    assert 'daemon stop' not in str(result.value)
    assert effects == [] and calls == []


def test_existing_distinct_homes_reuse_only_the_requested_registered_gui(launcher, monkeypatch, gui_instances):
    other = gui_instances('other'); selected = gui_instances()
    effects, launch = gui_launch_boundary(launcher, monkeypatch, selected)
    calls = fake_wmctrl(monkeypatch, selected.gui, lambda: True)
    launch()
    assert other.process.poll() is None
    assert effects == ['ensure', 'message'] and calls[-1][-1] == '0x333'


def test_fresh_other_home_is_refused_even_with_initial_profile_override(launcher, monkeypatch, gui_instances):
    item = gui_instances('other')
    item.config = dict(item.config, codex_home=str(item.profile.parent/'new-home'))
    Path(item.config['codex_home']).mkdir()
    monkeypatch.setenv('CODEX_ELECTRON_USER_DATA_PATH', str(item.profile.parent/'override'))
    effects, launch = gui_launch_boundary(launcher, monkeypatch, item)
    calls = fake_wmctrl(monkeypatch, item.gui, lambda: True)
    with pytest.raises(RuntimeError, match='another configuration'):
        launch()
    assert effects == [] and calls == []


def test_profile_collision_between_existing_guis_is_refused(launcher, monkeypatch, gui_instances):
    other = gui_instances('other'); selected = gui_instances()
    (other.profile/'SingletonLock').unlink(); other.profile.rmdir()
    other.profile.symlink_to(selected.profile, target_is_directory=True)
    effects, launch = gui_launch_boundary(launcher, monkeypatch, selected)
    calls = fake_wmctrl(monkeypatch, selected.gui, lambda: True)
    with pytest.raises(RuntimeError, match='configuration and'):
        launch()
    assert effects == [] and calls == []


@pytest.mark.parametrize('reuse_pid', [False, True])
def test_terminated_reservation_allows_normal_launch(launcher, monkeypatch, gui_instances, reuse_pid):
    item = gui_instances()
    item.process.stdin.close(); assert item.process.wait(10) == 0
    # Retained historical metadata must not block a new launch, even when its PID was recycled.
    if reuse_pid:
        item.launch['gui']['pid'] = os.getpid()
        item.launch['gui']['birth'] = 'old-birth'
        launcher['monitor_runtime_write'](item.runtime/'launch.json', item.launch)
    effects, launch = gui_launch_boundary(launcher, monkeypatch, item)
    with pytest.raises(SystemExit) as result:launch()
    assert result.value.code == 43 and effects == ['ensure', 'exec']


@pytest.mark.parametrize('failure', ['registration-changed', 'wmctrl-timeout'])
def test_reuse_failure_after_inventory_releases_lock(
        launcher, monkeypatch, gui_instances, failure):
    import fcntl
    item = gui_instances()
    effects, launch = gui_launch_boundary(launcher, monkeypatch, item)
    calls = fake_wmctrl(monkeypatch, item.gui, lambda: True)
    if failure == 'registration-changed':
        # Invalidate after the second inventory, at the actual focus consumer boundary.
        original_focus = launcher['focus_gui']
        namespace = original_focus.__globals__
        def focus(*args, **kwargs):
            ready = item.runtime/'gui-ready.json'
            launcher['monitor_runtime_write'](ready, {'gui': item.gui, 'proxy': item.gui})
            return original_focus(*args, **kwargs)
        monkeypatch.setitem(namespace, 'focus_gui', focus)
        expected = 'configuration and'
    else:
        def stall(arguments, **kwargs):raise subprocess.TimeoutExpired(arguments, kwargs['timeout'])
        monkeypatch.setattr(subprocess, 'run', stall)
        expected = 'window.*time'
    with pytest.raises(RuntimeError, match=expected):launch()
    assert effects == ['ensure'] and calls == []
    with (item.runtime/'gui.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
