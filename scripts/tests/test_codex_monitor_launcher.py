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
    assert 'Sem --gui, abre a CLI no terminal' in capsys.readouterr().out


def test_cli_exec_keeps_cwd_exit_and_arguments_without_restarting_native(launcher, monkeypatch, tmp_path):
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
        function({'codex_home': str(tmp_path)}, native, native, ['-C', 'relative', 'hello world'])
    assert result.value.code == 41
    binary, args, env, cwd = calls[0]
    assert binary == native
    assert args == [str(native), '--remote', 'unix:///fixture/native.sock', '-C', 'relative', 'hello world']
    assert env['CODEX_HOME'] == str(tmp_path)
    assert 'CODEX_CLI_PATH' not in env and 'CODEX_STATS_APP_LAUNCH' not in env
    assert cwd == Path.cwd()
    for arguments in (['--remote', 'unix:///other'], ['--remote=unix:///other']):
        with pytest.raises(RuntimeError, match='remova a opção --remote'):
            function({'codex_home': str(tmp_path)}, native, native, arguments)
    assert len(calls) == 1


@pytest.fixture
def independent(launcher, monkeypatch):
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
        namespace = launcher['native_owner'].__globals__
        monkeypatch.setitem(namespace, 'installed_native', lambda config: Path(sys.executable).resolve())
        script = ('import socket,sys; s=socket.socket(socket.AF_UNIX); s.bind(sys.argv[1]); '
                  's.listen(); print("ready",flush=True); '\
                  '\nwhile True:\n c,_=s.accept(); c.close()\n')
        process = subprocess.Popen([sys.executable, '-c', script, str(endpoint), 'app-server'],
            env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            assert process.stdout.readline() == 'ready\n'
            alias.symlink_to(endpoint)
            owner = launcher['native_owner'](config)
            runtime_path = launcher['support']()['monitor_shared_runtime'](config, create=True)
            launcher['monitor_runtime_write'](runtime_path/'ready.json', owner)
            yield config, owner, process, runtime_path, home
        finally:
            process.terminate(); process.wait(timeout=5)
            process.stdin.close(); process.stdout.close(); process.stderr.close()
            endpoint.unlink(missing_ok=True)
            tools.rmdir()


def test_independent_owner_uses_native_identity_without_gui_and_rejects_stale_receipt(launcher, independent):
    config, owner, process, runtime, home = independent
    assert launcher['monitor_shared_owner'](config) == owner
    assert set(owner) == {'version','codex_home','socket','native','native_executable','socket_identity'}
    assert owner['native']['pid'] == process.pid
    changed = json.loads((runtime/'ready.json').read_text()); changed['native']['birth']='stale'
    (runtime/'ready.json').write_text(json.dumps(changed))
    with pytest.raises(RuntimeError, match='registro do servidor mudou'):
        launcher['monitor_shared_owner'](config)
    assert process.poll() is None
    launcher['monitor_runtime_write'](runtime/'ready.json', owner)
    (home/'config.toml').write_text((home/'config.toml').read_text()+'\n# external edit\n')
    assert launcher['monitor_shared_owner'](config) == owner
    (home/'config.toml').write_text((home/'config.toml').read_text().replace('code_mode_host=true','code_mode_host=false'))
    with pytest.raises(RuntimeError, match='não habilitou as ferramentas'):
        launcher['monitor_shared_owner'](config)
    assert process.poll() is None


def test_independent_owner_rejects_other_connected_peer(launcher, independent):
    config, owner, process, runtime, home = independent
    left, right = socket.socketpair()
    try:
        transport = types.SimpleNamespace(get_extra_info=lambda name: left)
        with pytest.raises(RuntimeError, match='outro servidor nativo'):
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
    with pytest.raises(RuntimeError, match='registro do servidor mudou'):
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
    with pytest.raises(RuntimeError, match='Outra camada.*features.code_mode_host'):
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
    (subprocess.TimeoutExpired(['native','app-server','daemon','start'], 1), 'pode ter iniciado'),
    (subprocess.CalledProcessError(1, ['wmctrl','-ia','0x123']), 'trabalhos foram preservados'),
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


def singleton_gui(tmp_path, lock_owner, socket_cookie='42'):
    """Make this test process a GUI whose Chromium child names a profile with a singleton socket."""
    profile, sockets = tmp_path/'profile', tmp_path/'s'
    profile.mkdir(); sockets.mkdir()
    (profile/'SingletonLock').symlink_to(f'{socket.gethostname()}-{lock_owner}')
    (profile/'SingletonCookie').symlink_to('42')
    (sockets/'SingletonCookie').symlink_to(socket_cookie)
    (profile/'SingletonSocket').symlink_to(sockets/'SingletonSocket')
    # Chromium rewrites a child's arguments into one space-joined process title; reproduce that shape.
    title = f'{APP} --type=zygote --enable-crash-reporter=, --user-data-dir={profile} --change-stack-guard-on-fork=enable'
    child = subprocess.Popen(['bash', '-c', 'exec -a "$0" sleep 60', title])
    return profile, sockets/'SingletonSocket', child


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
    ('foreign-lock', 'não foi possível confirmar sua instância'),
    ('cookie-mismatch', 'não foi possível confirmar sua instância'),
    ('shutting-down', 'não aceitou o pedido'),
    ('silent', 'não respondeu ao pedido'),
    ('no-window', 'janela ainda não está disponível'),
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
        with pytest.raises(RuntimeError, match='não foi possível confirmar sua instância'):
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
    acquisitions = {}; launches = []; results = {}; errors = {}
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
    finally:
        second_started.set(); second_done.set()
        first.join(timeout=10)
        if second.ident is not None:second.join(timeout=10)
        directory = launcher['monitor_app_tools_directory'](config)
        directory.rmdir()


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
    namespace = launcher['existing_gui'].__globals__
    original_path = Path
    monkeypatch.setitem(namespace, 'Path', lambda value: types.SimpleNamespace(iterdir=lambda: iter(entries))
                        if str(value) == '/proc' else original_path(value))
    authenticated = []
    gui = {'pid': 5, 'birth': 'fixture', 'exe': str(app), 'parent': 9}
    def process(pid):
        authenticated.append(pid); assert pid == 5; return gui
    monkeypatch.setitem(namespace, 'monitor_process', process)
    monkeypatch.setitem(namespace, 'process_environment', lambda pid: {'HOME': str(home.parent), 'CODEX_HOME': str(home)})
    assert list(launcher['existing_gui']({'codex_home': str(home)}, app)) == [gui]
    assert authenticated == [5]
    import pwd
    monkeypatch.setattr(pwd, 'getpwuid', lambda uid: types.SimpleNamespace(pw_dir=str(tmp_path)))
    monkeypatch.setitem(namespace, 'process_environment', lambda pid: {})
    assert list(launcher['existing_gui']({'codex_home': str(tmp_path/'.codex')}, app)) == [gui]
    def unreadable(pid):raise PermissionError('actual GUI environment unreadable')
    monkeypatch.setitem(namespace, 'process_environment', unreadable)
    with pytest.raises(RuntimeError, match='configuração do Codex já aberto'):
        list(launcher['existing_gui']({'codex_home': str(home)}, app))
