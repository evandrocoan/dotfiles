"""Monitor contracts through the standalone CLI and its real private state."""

import json
import os
from pathlib import Path
import subprocess
import sys
import datetime as dt
import copy
import runpy
import sqlite3
import types
import io
import tomllib
import tempfile
import shutil
import socket
import struct
from urllib.parse import urlsplit, parse_qs
from email.utils import format_datetime

import pytest


CLI = Path(os.environ.get("CODEX_MONITOR_TEST_CLI", Path(__file__).resolve().parents[2] / ".local/bin/codex-session-stats"))


# A JSONL SDK/native fixture over real Unix sockets. This exercises processes, peer
# credentials, leases, stdio and cancellation, not real WebSocket framing or Codex.
RELAY_SDK = '''
import asyncio,json
class Connection:
    def __init__(self,path,**kwargs): self.path=path
    async def __aenter__(self):
        self.reader,self.writer=await asyncio.open_unix_connection(self.path,limit=128*1024*1024)
        self.transport=self.writer.transport
        return self
    def __await__(self): return self.__aenter__().__await__()
    async def __aexit__(self,*args): await self.close()
    async def send(self,raw):
        self.writer.write((raw+'\\n').encode()); await self.writer.drain()
    async def recv(self):
        raw=await self.reader.readline()
        if not raw: raise EOFError('native fixture closed')
        return raw.decode().rstrip('\\n')
    def __aiter__(self): return self
    async def __anext__(self):
        try: return await self.recv()
        except EOFError: raise StopAsyncIteration
    async def close(self):
        self.writer.close(); await self.writer.wait_closed()
unix_connect=Connection
'''

RELAY_NATIVE = '''
import json,os,pathlib,socket,sys,threading
root=pathlib.Path(__file__).parent
if '--listen' not in sys.argv:
    with (root/'delegated.jsonl').open('a') as log:
        log.write(json.dumps({'argv':sys.argv[1:],'cli':os.environ.get('CODEX_CLI_PATH')})+'\\n')
    print('delegated'); raise SystemExit
(root/'native-argv.json').write_text(json.dumps(sys.argv[1:]))
(root/'native-pid').write_text(str(os.getpid()))
home=pathlib.Path(os.environ['CODEX_HOME']); home.mkdir(exist_ok=True)
alias=home/'app-server-control/app-server-control.sock'; alias.parent.mkdir(exist_ok=True)
endpoint=root/'native.sock'
server=socket.socket(socket.AF_UNIX); server.bind(str(endpoint)); server.listen()
alias.symlink_to(endpoint)
def client(connection):
    with connection,connection.makefile('rb') as stream:
        original=None
        while raw:=stream.readline():
            message=json.loads(raw)
            method=message.get('method')
            with (root/'requests.jsonl').open('a') as log: log.write(json.dumps(message)+'\\n')
            if method=='initialize':
                if 'fixture.silent_initialize=true' in sys.argv: continue
                if (root/'revoke-on-monitor-initialize').exists() and message.get('params',{}).get('clientInfo',{}).get('name')=='codex_stats_gitlab_monitor':
                    ready=next((root/'runtime/codex-session-stats').glob('shared-*/ready.json'))
                    receipt=json.loads(ready.read_text()); receipt['proxy']['birth']='stale'; ready.write_text(json.dumps(receipt))
                if 'fixture.fail_initialize=true' in sys.argv:
                    response={'id':message['id'],'error':{'code':-1}}
                else: response={'id':message['id'],'result':{'fixture':True}}
            elif method=='server/request':
                original=message['id']
                response={'id':'approval','method':'item/commandExecution/requestApproval','params':{'fixture':True}}
            elif message.get('id')=='approval':
                response={'id':original,'result':message['result']}
            elif 'id' in message: response={'id':message['id'],'result':message.get('params',{})}
            else: continue
            connection.sendall((json.dumps(response)+'\\n').encode())
while True:
    connection,_=server.accept(); threading.Thread(target=client,args=(connection,),daemon=True).start()
'''

RELAY_GUI = '''
import json,os,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).parent
scenario=sys.argv[1]
env=dict(os.environ); env['CODEX_INTERNAL_ORIGINATOR_OVERRIDE']='Codex Desktop'
wrapper=env['CODEX_CLI_PATH']
helper=subprocess.run([wrapper,'--version'],env=env,capture_output=True,text=True,check=True)
assert helper.stdout.strip()=='delegated'
args=['-c','features.code_mode_host=true','-c','plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled=true',
      '-c','plugins.code-review@openai-bundled.mcp_servers.code-review.enabled=false']
if scenario=='reordered': args=['app-server',*args,'--analytics-default-enabled']
else: args += ['app-server','--analytics-default-enabled']
if scenario=='failed': args += ['-c','fixture.fail_initialize=true']
if scenario=='silent': args += ['-c','fixture.silent_initialize=true']
for helper_args,origin in [(args,'codex_latex_preview'),
        (['-c','features.code_mode_host=true','app-server','--analytics-default-enabled'],'Codex Desktop')]:
    helper_env={**env,'CODEX_INTERNAL_ORIGINATOR_OVERRIDE':origin}
    helper=subprocess.run([wrapper,*helper_args],env=helper_env,capture_output=True,text=True,check=True)
    assert helper.stdout.strip()=='delegated'
child=subprocess.Popen([wrapper,*args],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def send(message):
    child.stdin.write((json.dumps(message)+'\\n').encode()); child.stdin.flush()
def receive():
    raw=child.stdout.readline()
    assert raw,'relay ended before response'
    return json.loads(raw)
try:
    send({'id':'__codex_initialize__','method':'initialize','params':{'clientInfo':{'name':'Codex Desktop','version':'1'}}})
    if scenario=='silent':
        assert child.stdout.readline()==b''
        initialized={}
    else: initialized=receive()
    if scenario=='silent': pass
    elif scenario=='failed':
        assert 'error' in initialized
    elif scenario=='oversize':
        try: send({'id':3,'method':'echo','params':{'large':'x'*(65*1024*1024)}})
        except BrokenPipeError: pass
    elif scenario=='backpressure':
        import array,fcntl,termios
        send({'id':3,'method':'echo','params':{'large':'x'*(9*1024*1024)}})
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            pending=array.array('i',[0]); fcntl.ioctl(child.stdout.fileno(),termios.FIONREAD,pending,True)
            if pending[0]>=fcntl.fcntl(child.stdout.fileno(),fcntl.F_GETPIPE_SZ): break
            time.sleep(.01)
        else: raise AssertionError('GUI output pipe never filled')
        child.stdin.close()
    else:
        send({'id':3,'method':'config/read','params':{'fixture':True}})
        assert receive()=={'id':3,'result':{'fixture':True}}
        duplicate=subprocess.run([wrapper,*args],env=env,input=b'',capture_output=True)
        assert duplicate.returncode==1
        send({'id':4,'method':'server/request','params':{}})
        assert receive()['method']=='item/commandExecution/requestApproval'
        send({'id':'approval','result':{'decision':'fixture-response'}})
        assert receive()=={'id':4,'result':{'decision':'fixture-response'}}
        large='x'*(9*1024*1024)
        send({'id':5,'method':'echo','params':{'large':large}})
        assert receive()['result']['large']==large
    print(json.dumps({'ready':True,'env':{key:os.environ.get(key) for key in (
        'GITLAB_TOKEN','GITLAB_PAT','CODEX_APP_SERVER_WS_URL','CODEX_APP_SERVER_USE_LOCAL_DAEMON')},'pid':os.getpid()}),flush=True)
    sys.stdin.readline()
finally:
    if not child.stdin.closed:
        try: child.stdin.close()
        except BrokenPipeError: pass
    child.wait(timeout=10)
    child.stdout.close()
print(json.dumps({'relay_exit':child.returncode}),flush=True)
'''


@pytest.fixture
def shared_app():
    import venv
    # Short paths also keep AF_UNIX endpoints below Linux's length limit.
    with tempfile.TemporaryDirectory(prefix="csm-") as directory:
        root = Path(directory)
        venv.EnvBuilder(with_pip=False, symlinks=True).create(root / "venv")
        python = root / "venv/bin/python"
        site = next((root / "venv/lib").glob("python*/site-packages"))
        package = site / "websockets"
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "client.py").write_text(RELAY_SDK)
        (package / "exceptions.py").write_text("class WebSocketException(Exception): pass\n")
        gui = root / "gui"
        shutil.copyfile(Path(sys.executable).resolve(), gui)
        gui.chmod(0o700)
        (root / "gui.py").write_text(RELAY_GUI)
        native = root / "native"
        native.write_text(f"#!{python}\n" + RELAY_NATIVE)
        native.chmod(0o700)
        (root / "home").mkdir()
        (root / "home/.codex").mkdir()
        (root / "runtime").mkdir(mode=0o700)
        environment = {**os.environ, "HOME": str(root / "home"), "XDG_RUNTIME_DIR": str(root / "runtime"),
                       "CODEX_HOME": str(root / "home/.codex"), "GITLAB_TOKEN": "DO_NOT_FORWARD",
                       "GITLAB_PAT": "DO_NOT_FORWARD", "CODEX_APP_SERVER_WS_URL": "ws://do-not-forward",
                       "CODEX_APP_SERVER_USE_LOCAL_DAEMON": "1"}
        config_path = root / "monitor.json"
        base = [str(python), str(CLI), "monitor-gitlab", "--config", str(config_path)]
        created = subprocess.run([*base, "configure", "--project-url", "https://gitlab.example.test/team/project",
                                  "--project-id", "42"], env=environment, capture_output=True, text=True)
        assert created.returncode == 0, created.stderr
        children, errors = [], []

        def start(scenario="normal"):
            log = (root / f"stderr-{len(children)}").open("w+")
            process = subprocess.Popen([*base, "launch-app", "--app", str(gui), "--codex", str(native),
                "--", str(root / "gui.py"), scenario], env=environment, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=log, text=True)
            children.append(process)
            errors.append(log)
            # No fixed sleeps: communicate startup through an explicit ready record.
            import selectors
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=20), "shared GUI fixture did not become ready"
            line = process.stdout.readline()
            log.flush(); log.seek(0)
            assert line, log.read()
            return process, json.loads(line)

        yield root, environment, base, start
        for process in children:
            if process.poll() is None:
                process.stdin.write("stop\n"); process.stdin.flush()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
                pytest.fail("shared GUI fixture did not stop its owned relay")
            process.stdin.close(); process.stdout.close()
        for log in errors:
            log.close()


@pytest.mark.parametrize("scenario", ["normal", "reordered"])
def test_shared_relay_preserves_protocol_large_messages_and_exact_live_owner(shared_app, monkeypatch, scenario):
    root, environment, base, start = shared_app
    process, report = start(scenario)
    assert all(value is None for value in report["env"].values())
    monkeypatch.setenv("XDG_RUNTIME_DIR", environment["XDG_RUNTIME_DIR"])
    module = runpy.run_path(str(CLI))
    config = module["monitor_config"](root / "monitor.json")
    receipt = module["monitor_shared_owner"](config)
    assert receipt["gui"]["pid"] == process.pid == report["pid"]
    peer = socket.socket(socket.AF_UNIX)
    try:
        peer.connect(config["socket"])
        transport = types.SimpleNamespace(get_extra_info=lambda name: peer)
        module["monitor_shared_peer"](config, types.SimpleNamespace(transport=transport))
        assert struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[0] == receipt["native"]["pid"]
    finally:
        peer.close()
    delegated = [json.loads(line) for line in (root / "delegated.jsonl").read_text().splitlines()]
    assert len(delegated) == 3
    assert delegated[0] == {"argv": ["--version"], "cli": str(root / "native")}
    assert all(item["cli"] == str(root / "native") for item in delegated)
    assert delegated[1]["argv"].count("--analytics-default-enabled") == 1
    assert delegated[2]["argv"] == ["-c", "features.code_mode_host=true", "app-server", "--analytics-default-enabled"]
    argv = json.loads((root / "native-argv.json").read_text())
    assert argv[-2:] == ["--listen", "unix://"]
    assert "plugins.code-review@openai-bundled.mcp_servers.code-review.enabled=false" in argv
    # An independently connected monitor client reaches the same process after GUI initialization.
    script = "import runpy,json,sys; m=runpy.run_path(sys.argv[1]); c=m['monitor_config'](__import__('pathlib').Path(sys.argv[2])); print(json.dumps(m['monitor_native'](c,'config/read',{'second_client':True})))"
    response = subprocess.run([base[0], "-c", script, str(CLI), str(root / "monitor.json")],
                              env=environment, capture_output=True, text=True, timeout=10)
    assert response.returncode == 0, response.stderr
    assert json.loads(response.stdout) == {"second_client": True}
    process.stdin.write("stop\n"); process.stdin.flush()
    assert json.loads(process.stdout.readline())["relay_exit"] == 0
    process.wait(timeout=10)
    with pytest.raises(RuntimeError, match="unavailable or unverified"):
        module["monitor_shared_owner"](config)
    with pytest.raises((FileNotFoundError, ProcessLookupError, RuntimeError)):
        module["monitor_process"](receipt["native"]["pid"])


@pytest.mark.parametrize("scenario,exit_code", [("failed", 0), ("silent", 1), ("oversize", 1), ("backpressure", 0)])
def test_relay_failure_and_eof_revoke_readiness_and_reap_owned_native(shared_app, monkeypatch, scenario, exit_code):
    root, environment, _, start = shared_app
    if scenario == "silent":
        path = root / "monitor.json"
        settings = json.loads(path.read_text())
        settings["native_timeout"] = 1
        path.write_text(json.dumps(settings))
    process, _ = start(scenario)
    monkeypatch.setenv("XDG_RUNTIME_DIR", environment["XDG_RUNTIME_DIR"])
    module = runpy.run_path(str(CLI))
    config = module["monitor_config"](root / "monitor.json")
    if scenario in {"failed", "silent"}:
        with pytest.raises(RuntimeError, match="unavailable or unverified"):
            module["monitor_shared_owner"](config)
    process.stdin.write("stop\n"); process.stdin.flush()
    assert json.loads(process.stdout.readline())["relay_exit"] == exit_code
    process.wait(timeout=10)
    assert not (module["monitor_shared_runtime"](config) / "ready.json").exists()
    with pytest.raises((FileNotFoundError, ProcessLookupError, RuntimeError)):
        module["monitor_process"](int((root / "native-pid").read_text()))


def test_shared_owner_rejects_stale_receipt_lease_and_wrong_connected_peer(shared_app, monkeypatch):
    root, environment, base, start = shared_app
    process, _ = start()
    monkeypatch.setenv("XDG_RUNTIME_DIR", environment["XDG_RUNTIME_DIR"])
    module = runpy.run_path(str(CLI))
    config = module["monitor_config"](root / "monitor.json")
    runtime = module["monitor_shared_runtime"](config)
    path = runtime / "ready.json"
    original = path.read_text()
    receipt = json.loads(original)
    for role in ("gui", "proxy", "native"):
        changed = copy.deepcopy(receipt)
        changed[role]["birth"] = "invalid"
        path.write_text(json.dumps(changed))
        with pytest.raises(RuntimeError, match="unavailable or unverified"):
            module["monitor_shared_owner"](config)
        path.write_text(original)
    (runtime / "lease").rename(runtime / "old-lease")
    (runtime / "lease").touch(mode=0o600)
    with pytest.raises(RuntimeError, match="unavailable or unverified"):
        module["monitor_shared_owner"](config)
    (runtime / "lease").unlink()
    (runtime / "old-lease").rename(runtime / "lease")
    left, right = socket.socketpair()
    try:
        transport = types.SimpleNamespace(get_extra_info=lambda name: left)
        with pytest.raises(RuntimeError, match="not the GUI's shared server"):
            module["monitor_shared_peer"](config, types.SimpleNamespace(transport=transport))
    finally:
        left.close(); right.close()
    # Refuse another launch while the exact GUI is live, without disturbing it.
    duplicate = subprocess.run([*base, "launch-app", "--app", str(root / "gui"), "--codex", str(root / "native")],
                               env=environment, capture_output=True, text=True, timeout=10)
    assert duplicate.returncode == 1 and "already running" in duplicate.stderr
    assert process.poll() is None


def test_poll_without_shared_gui_leaves_no_state_http_or_optional_import(tmp_path, monkeypatch):
    config = configure(tmp_path)
    module = runpy.run_path(str(CLI))
    code = module["monitor_poll"].__globals__
    monkeypatch.setitem(code, "monitor_is_open", lambda config: True)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "absent-runtime"))
    assert module["monitor_poll"](config, tmp_path / "monitor.json") == {
        "skipped": "shared_app_unavailable", "mutated": False}
    assert not Path(config["state_file"]).exists()


def test_native_revalidates_gui_lease_after_initialization_before_protected_request(shared_app):
    root, environment, base, start = shared_app
    start()
    (root / "revoke-on-monitor-initialize").touch()
    script = "import runpy,sys; m=runpy.run_path(sys.argv[1]); c=m['monitor_config'](__import__('pathlib').Path(sys.argv[2])); m['monitor_native'](c,'config/read',{'must_not_send':True})"
    response = subprocess.run([base[0], "-c", script, str(CLI), str(root / "monitor.json")],
                              env=environment, capture_output=True, text=True, timeout=10)
    assert response.returncode != 0 and "unavailable or unverified" in response.stderr
    requests = [json.loads(line) for line in (root / "requests.jsonl").read_text().splitlines()]
    assert not any(request.get("params", {}).get("must_not_send") for request in requests)


def test_shared_runtime_rejects_agent_writable_location_before_creating_files(tmp_path, monkeypatch):
    config = configure(tmp_path)
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    config["state_file"] = str(runtime / "state.sqlite3")
    module = runpy.run_path(str(CLI))
    with pytest.raises(RuntimeError, match="outside the monitor's writable"):
        module["monitor_shared_runtime"](config, create=True)
    assert list(runtime.iterdir()) == []


def test_offline_status_retains_historical_endpoint_without_allowing_writable_rebind(tmp_path):
    config = configure(tmp_path)
    module = runpy.run_path(str(CLI))
    config["socket"] = str(tmp_path / "old.sock")
    state = module["MonitorState"](config)
    state.db.close()
    before = Path(config["state_file"]).read_bytes()
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["endpoint_verified"] is False
    assert Path(config["state_file"]).read_bytes() == before
    live = module["monitor_config"](tmp_path / "monitor.json")
    with pytest.raises(RuntimeError, match="another project, endpoint or schema"):
        module["MonitorState"](live)


def run_monitor(tmp_path, *arguments, input_text=None, extra_env=None):
    environment = os.environ.copy()
    environment.update({"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config"),
                        "XDG_STATE_HOME": str(tmp_path / "state"), "PYTHONDONTWRITEBYTECODE": "1"})
    environment.pop("CODEX_HOME", None)
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CLI), "monitor-gitlab", "--config",
         str(tmp_path / "monitor.json"), *arguments],
        input=input_text, capture_output=True, text=True, env=environment, check=False,
    )


def configure(tmp_path):
    result = run_monitor(tmp_path, "configure", "--project-url",
                         "https://gitlab.example.test/engineering/project", "--project-id", "42")
    assert result.returncode == 0, result.stderr
    return json.loads((tmp_path / "monitor.json").read_text())


def test_monitor_configure_is_private_and_status_does_not_initialize_state(tmp_path):
    config = configure(tmp_path)
    assert config["project_id"] == 42
    assert config["project_path"] == "engineering/project"
    assert config["weekdays"] == [0, 1, 2, 3, 4, 5]
    assert config["open_hour"] == 7
    assert config["close_hour"] == 22
    assert config["interval_minutes"] == 15
    assert (tmp_path / "monitor.json").stat().st_mode & 0o777 == 0o600
    before = (tmp_path / "monitor.json").read_bytes()
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["initialized"] is False
    assert not Path(config["state_file"]).exists()
    assert (tmp_path / "monitor.json").read_bytes() == before


def test_monitor_configure_never_overwrites_existing_configuration(tmp_path):
    configure(tmp_path)
    before = (tmp_path / "monitor.json").read_bytes()
    result = run_monitor(tmp_path, "configure", "--project-url",
                         "https://other.example.test/team/other", "--project-id", "99")
    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert (tmp_path / "monitor.json").read_bytes() == before


@pytest.mark.parametrize("url", ["http://gitlab.example.test/group/project",
    "https://user:password@gitlab.example.test/group/project",
    "https://gitlab.example.test/group/project?token=secret",
    "https://gitlab.example.test/group/../project"])
def test_monitor_rejects_unsafe_project_urls_without_creating_config(tmp_path, url):
    result = run_monitor(tmp_path, "configure", "--project-url", url, "--project-id", "42")
    assert result.returncode == 1
    assert not (tmp_path / "monitor.json").exists()
    assert not (tmp_path / "state").exists()


def test_optional_websocket_import_is_absent_from_help_and_offline_status(tmp_path):
    configure(tmp_path)
    poison = tmp_path / "poison"
    poison.mkdir()
    (poison / "websockets.py").write_text("raise RuntimeError('unexpected optional import')\n")
    for arguments in (("--help",), ("status",)):
        result = run_monitor(tmp_path, *arguments, extra_env={"PYTHONPATH": str(poison)})
        assert result.returncode == 0, result.stderr
        assert "unexpected optional import" not in result.stderr


class Boundary:
    """Only external HTTP/WebSocket/runtime fixtures; production orchestration stays real."""

    def __init__(self, tmp_path, monkeypatch):
        self.config = configure(tmp_path)
        self.path = tmp_path / "monitor.json"
        self.module = runpy.run_path(str(CLI))
        self.code = self.module["monitor_poll"].__globals__
        # Consumer policy fixtures replace only the external GUI/process boundary.
        # Live lease, process and connected-peer checks have separate OS-level tests below.
        monkeypatch.setitem(self.code, "monitor_shared_owner", lambda config: {})
        monkeypatch.setitem(self.code, "monitor_shared_peer", lambda config, connection: None)
        self.now = dt.datetime(2026, 10, 17, 13, tzinfo=dt.timezone.utc)
        monkeypatch.setitem(self.code, "monitor_now", lambda: self.now)
        self.monkeypatch = monkeypatch
        self.http, self.native, self.threads, self.turns, self.items = [], [], {}, {}, {}
        self.mrs, self.discussions, self.users = {}, {}, {7: {"id": 7, "bot": False}}
        self.fail_page = None
        self.after_http = None
        self.on_start = None
        self.lost_ack = False
        self.cross_origin = False
        self.token = "FIXTURE_PRIVATE_TOKEN_DO_NOT_FORWARD"
        home = Path(self.config["codex_home"])
        home.mkdir(parents=True)
        (home / "config.toml").write_text('[mcp_servers.gitlab.env]\nGITLAB_API_URL = "https://gitlab.example.test/api/v4"\nGITLAB_PERSONAL_ACCESS_TOKEN = "' + self.token + '"\n')
        self.codex_settings = tomllib.loads((home / "config.toml").read_text())
        self.config_version = "fixture-user-1"
        self.extra_config_layers = []
        self.on_config_write = None
        self.clock = lambda: format_datetime(self.now, usegmt=True)
        monkeypatch.setattr("urllib.request.OpenerDirector.open", self.open)

        boundary = self

        class Socket:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def send(self, raw):
                request = json.loads(raw)
                boundary.native.append(request)
                if request.get("id") == 1:
                    self.response = {"id": 1, "result": {}}
                elif request.get("id") == 2:
                    result = boundary.respond(request["method"], request["params"])
                    self.response = {"id": 2, "result": result}

            async def recv(self):
                return json.dumps(self.response)

        package = types.ModuleType("websockets")
        client = types.ModuleType("websockets.client")
        exceptions = types.ModuleType("websockets.exceptions")
        exceptions.WebSocketException = type("WebSocketException", (Exception,), {})
        client.unix_connect = lambda endpoint, **kwargs: Socket()
        monkeypatch.setitem(sys.modules, "websockets", package)
        monkeypatch.setitem(sys.modules, "websockets.client", client)
        monkeypatch.setitem(sys.modules, "websockets.exceptions", exceptions)

    def call(self, name, *args, **kwargs):
        return self.module["monitor_" + name](*args, **kwargs)

    def state(self):
        return self.module["MonitorState"](self.config)

    def api(self):
        return self.module["MonitorGitLab"](self.config)

    def mr(self, iid=1, sha="a" * 40, created="2020-01-01T00:00:00Z"):
        mr = {"iid": iid, "project_id": 42, "web_url": f"https://gitlab.example.test/engineering/project/-/merge_requests/{iid}",
              "title": "Hostile $(do-not-execute) `text`", "sha": sha, "state": "opened", "created_at": created,
              "diff_refs": {"base_sha": "0" * 40, "start_sha": "0" * 40, "head_sha": sha}}
        self.mrs[iid] = mr
        self.discussions.setdefault(iid, [])
        return mr

    def note(self, iid=1, note_id=11, body="A concern", author=7, created=None, system=False):
        note = {"id": note_id, "body": body, "author": {"id": author},
                "created_at": created or self.now.isoformat(), "system": system,
                "resolvable": True, "resolved": False}
        self.discussions[iid].append({"id": f"discussion{note_id}", "notes": [note]})
        return note

    def open(self, request, timeout=None):
        self.http.append(request)
        assert request.headers["Private-token"] == self.token
        url = urlsplit(request.full_url)
        assert url.netloc == "gitlab.example.test"
        route, query = url.path.removeprefix("/api/v4"), parse_qs(url.query)
        headers = {"Date": self.clock(), "X-Next-Page": ""}
        if route == "/projects/42":
            data = {"id": 42, "path_with_namespace": "engineering/project", "web_url": "https://gitlab.example.test/engineering/project"}
        elif route == "/user":
            data = {"id": 7, "username": "reviewer"}
        elif route.startswith("/users/"):
            data = self.users[int(route.split("/")[-1])]
        elif route == "/projects/42/merge_requests":
            assert query.get("order_by") == ["created_at"]
            data = [m for m in self.mrs.values() if m["state"] == "opened"]
        elif route.endswith("/discussions"):
            iid, page = int(route.split("/")[-2]), int(query.get("page", ["1"])[0])
            if self.fail_page == page:
                raise RuntimeError("fixture page failure")
            data = self.discussions[iid][page - 1:page]
            if page < len(self.discussions[iid]):
                headers["X-Next-Page"] = str(page + 1)
            if self.cross_origin:
                headers["Link"] = '<https://evil.example/api/v4/next?page=2>; rel="next"'
        else:
            data = self.mrs[int(route.split("/")[-1])]
        if self.after_http:
            self.after_http(route)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, size):
                return json.dumps(data).encode()[:size]

        response = Response()
        response.headers = headers
        return response

    def respond(self, method, params):
        if method == "config/read":
            assert params == {"cwd": self.config["cwd"], "includeLayers": True}
            return {"config": {}, "origins": {}, "layers": [
                {"name": {"type": "user", "file": str(Path(self.config["codex_home"]) / "config.toml"),
                          "profile": None}, "version": self.config_version,
                 "config": copy.deepcopy(self.codex_settings)}, *copy.deepcopy(self.extra_config_layers)]}
        if method == "config/batchWrite":
            if self.on_config_write:
                self.on_config_write(params)
            if params["expectedVersion"] != self.config_version:
                raise RuntimeError("fixture configuration version conflict")
            assert params["filePath"] == str(Path(self.config["codex_home"]) / "config.toml")
            assert params["reloadUserConfig"] is False
            assert len(params["edits"]) == 1
            edit = params["edits"][0]
            assert edit["keyPath"] == "permissions.codex-session-stats-gitlab-monitor"
            assert edit["mergeStrategy"] == "upsert"
            self.codex_settings.setdefault("permissions", {}).setdefault(
                "codex-session-stats-gitlab-monitor", {}).update(copy.deepcopy(edit["value"]))
            self.config_version += "-next"
            return {"status": "ok", "version": self.config_version, "filePath": params["filePath"]}
        if method == "thread/start":
            tid = f"00000000-0000-0000-0000-{len(self.threads) + 1:012d}"
            thread = {"id": tid, "cwd": self.config["cwd"], "status": {"type": "idle"}}
            self.threads[tid] = thread
            self.turns[tid] = []
            return {"thread": thread, "activePermissionProfile": {
                "id": params.get("permissions"), "extends": ":read-only"}}
        if method in {"thread/read", "thread/resume"}:
            return {"thread": self.threads[params["threadId"]], "activePermissionProfile": {
                "id": params.get("permissions"), "extends": ":read-only"}}
        if method == "thread/list":
            return {"data": [t for t in self.threads.values() if not t.get("archived")], "nextCursor": None}
        if method == "thread/name/set":
            return {}
        if method == "thread/turns/list":
            return {"data": self.turns[params["threadId"]], "nextCursor": None}
        if method == "thread/items/list":
            return {"data": [{"item": i} for i in self.items[params["turnId"]]], "nextCursor": None}
        if method == "mcpServer/tool/call":
            assert params["server"] == "gitlab" and params["tool"] == "whoami"
            return {"content": [{"type": "text", "text": json.dumps({"id": "7", "web_url": "https://gitlab.example.test/reviewer"})}]}
        if method == "turn/start":
            tid = params["threadId"]
            turn = {"id": f"turn-{len(self.items) + 1}", "status": "inProgress", "startedAt": int(self.now.timestamp())}
            self.turns[tid].insert(0, turn)
            self.threads[tid]["status"] = {"type": "active"}
            self.items[turn["id"]] = ([{"type": "userMessage", "content": params["input"]}]
                if params["input"] else [{"type": "functionCallOutput", **params["toolOutput"]}])
            if self.on_start:
                self.on_start(tid, turn["id"])
            if self.lost_ack:
                raise TimeoutError("fixture lost acknowledgement")
            return {"turn": turn}
        raise AssertionError(method)

    def runtime(self, thread, turn):
        home = Path(self.config["codex_home"])
        rollout = home / "fixture-rollout.jsonl"
        rollout.write_text("\n".join(json.dumps(x) for x in [
            {"type": "session_meta", "payload": {"id": thread}},
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": turn}},
            {"type": "turn_context", "payload": {"turn_id": turn, "model": "gpt-6.1-sol", "effort": "xhigh"}},
        ]) + "\n")
        with sqlite3.connect(home / "state_5.sqlite") as db:
            db.execute("CREATE TABLE IF NOT EXISTS threads (id TEXT PRIMARY KEY, rollout_path TEXT)")
            db.execute("INSERT OR REPLACE INTO threads VALUES (?,?)", (thread, str(rollout)))
        self.monkeypatch.setenv("CODEX_THREAD_ID", thread)

    def finish(self, tid, turn):
        next(t for t in self.turns[tid] if t["id"] == turn)["status"] = "completed"
        self.threads[tid]["status"] = {"type": "idle"}

    def poll(self, **kwargs):
        return self.call("poll", self.config, self.path, **kwargs)

    def active_claim(self):
        state = self.state()
        attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch" and a["state"] == "accepted")
        self.runtime(attempt["thread_id"], attempt["turn_id"])
        work = self.call("claim", self.config, state, attempt["iid"],
                         {"attempt_id": attempt["id"], "event_id": attempt["event_id"]})
        return state, attempt, work


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    return Boundary(tmp_path, monkeypatch)


def test_poll_registers_only_its_named_profile_and_repeated_poll_does_not_write(boundary):
    b = boundary
    before = copy.deepcopy(b.codex_settings)
    b.poll()
    writes = [r["params"] for r in b.native if r.get("method") == "config/batchWrite"]
    assert len(writes) == 1
    assert writes[0]["expectedVersion"] == "fixture-user-1"
    profile = b.codex_settings["permissions"]["codex-session-stats-gitlab-monitor"]
    assert profile["extends"] == ":read-only"
    assert profile["filesystem"] == {str(Path(b.config["state_file"]).parent): "write"}
    assert profile["network"] == {"enabled": True, "allow_local_binding": True,
        "domains": {"gitlab.example.test": "allow"}, "unix_sockets": {b.config["socket"]: "allow"}}
    assert {k: v for k, v in b.codex_settings.items() if k != "permissions"} == before
    assert b.token not in json.dumps(writes)
    b.native.clear()
    expected = copy.deepcopy(b.codex_settings)
    b.poll()
    assert not [r for r in b.native if r.get("method") == "config/batchWrite"]
    assert b.codex_settings == expected
    assert not b.threads


def test_partial_profile_adds_missing_rules_without_replacing_other_settings(boundary):
    b = boundary
    b.codex_settings.update({"sandbox_mode": "workspace-write", "approval_policy": "on-request",
        "features": {"network_proxy": False}, "permissions": {
            "another-tool": {"extends": ":workspace"},
            "codex-session-stats-gitlab-monitor": {"extends": ":read-only", "network": {"enabled": True}}}})
    before = copy.deepcopy(b.codex_settings)
    b.poll()
    assert b.codex_settings["permissions"]["codex-session-stats-gitlab-monitor"]["network"]["enabled"] is True
    assert b.codex_settings["permissions"]["another-tool"] == before["permissions"]["another-tool"]
    assert {k: v for k, v in b.codex_settings.items() if k != "permissions"} == {
        k: v for k, v in before.items() if k != "permissions"}
    assert len([r for r in b.native if r.get("method") == "config/batchWrite"]) == 1


@pytest.mark.parametrize("conflict", [{"extends": ":workspace"},
    {"network": {"dangerously_allow_all_unix_sockets": True}}, {"network": {"enabled": 1}},
    {"network": None}])
def test_existing_conflicting_profile_is_not_overwritten_or_dispatched(boundary, conflict):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.codex_settings["permissions"] = {"codex-session-stats-gitlab-monitor": conflict}
    before = copy.deepcopy(b.codex_settings)
    with pytest.raises(RuntimeError, match="profile.*(conflict|invalid)"):
        b.poll()
    assert b.codex_settings == before
    assert not [r for r in b.native if r.get("method") in {"config/batchWrite", "thread/start", "turn/start"}]


def test_profile_override_in_another_active_layer_blocks_registration(boundary):
    b = boundary
    b.extra_config_layers = [{"name": {"type": "project", "dotCodexFolder": b.config["cwd"]},
        "version": "project-version", "config": {"permissions": {
            "codex-session-stats-gitlab-monitor": {"extends": ":workspace"}}}}]
    with pytest.raises(RuntimeError, match="profile.*layer"):
        b.poll()
    assert not [r for r in b.native if r.get("method") == "config/batchWrite"]


def test_duplicate_base_user_layer_cannot_redirect_profile_registration(boundary):
    b = boundary
    b.extra_config_layers = [{"name": {"type": "user", "file": str(Path(b.config["cwd"]) / "other.toml"),
        "profile": None}, "version": "wrong-version", "config": {}}]
    with pytest.raises(RuntimeError, match="user.*layer"):
        b.poll()
    assert not [r for r in b.native if r.get("method") == "config/batchWrite"]


def test_concurrent_codex_edit_is_not_overwritten_or_retried_with_old_version(boundary):
    b = boundary
    def concurrent_edit(params):
        b.codex_settings["user_edit"] = "preserve me"
        b.config_version = "concurrent-version"
    b.on_config_write = concurrent_edit
    with pytest.raises(RuntimeError, match="configuration|profile"):
        b.poll()
    assert b.codex_settings["user_edit"] == "preserve me"
    assert "permissions" not in b.codex_settings
    assert len([r for r in b.native if r.get("method") == "config/batchWrite"]) == 1


def test_lost_profile_write_response_is_reconciled_without_a_second_write(boundary):
    b = boundary
    original = b.respond
    def lost_response(method, params):
        result = original(method, params)
        if method == "config/batchWrite":
            raise TimeoutError("fixture acknowledgement lost after configuration write")
        return result
    b.respond = lost_response
    b.poll()
    assert b.codex_settings["permissions"]["codex-session-stats-gitlab-monitor"]["extends"] == ":read-only"
    assert len([r for r in b.native if r.get("method") == "config/batchWrite"]) == 1


def test_profile_never_grants_write_to_workspace_as_state_parent(boundary):
    b = boundary
    b.config["state_file"] = str(Path(b.config["cwd"]) / "monitor.sqlite3")
    with pytest.raises(RuntimeError, match="state directory"):
        b.poll()
    assert not [r for r in b.native if r.get("method") == "config/batchWrite"]


@pytest.mark.parametrize("seed", [{}, {"extends": ":read-only"}])
def test_check_only_preflight_never_repairs_missing_or_partial_profile(boundary, seed):
    b = boundary
    if seed:
        b.codex_settings["permissions"] = {"codex-session-stats-gitlab-monitor": seed}
    before = copy.deepcopy(b.codex_settings)
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "preflight", "--check-only"])
    assert b.call("main") == 1
    assert b.codex_settings == before
    assert not [r for r in b.native if r.get("method") == "config/batchWrite"]


def test_native_claim_callback_does_not_repair_a_missing_profile(boundary, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    del b.codex_settings["permissions"]["codex-session-stats-gitlab-monitor"]
    before = copy.deepcopy(b.codex_settings)
    b.native.clear()
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "claim", "--mr", "1"])
    b.monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({
        "attempt_id": attempt["id"], "event_id": attempt["event_id"]})))
    assert b.call("main") == 0
    assert json.loads(capsys.readouterr().out)["generation"] == state.get("mrs", "1")["generation"]
    assert b.codex_settings == before
    assert not [r for r in b.native if r.get("method") in {
        "config/read", "config/batchWrite", "thread/start", "thread/resume", "turn/start"}]
    assert state.get("mrs", "1")["owner"]["turn_id"] == attempt["turn_id"]
    state.db.close()


def test_profile_never_grants_write_to_a_shared_state_directory(boundary):
    b = boundary
    parent = Path(b.config["state_file"]).parent
    parent.mkdir(parents=True, mode=0o755)
    parent.chmod(0o755)
    with pytest.raises(RuntimeError, match="owned private directory"):
        b.poll()
    assert not [r for r in b.native if r.get("method") == "config/batchWrite"]


def test_loaded_idle_mr_is_reselected_and_wrong_profile_blocks_next_turn(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    b.call("complete", b.config, state, 1, {"generation": work["generation"],
        "event_ids": [e["id"] for e in work["events"]], "reviewed_head": "a" * 40})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    b.native.clear()
    b.note(note_id=9)
    original = b.respond
    def wrong_selection(method, params):
        result = original(method, params)
        if method == "thread/resume":
            result["activePermissionProfile"] = None
        return result
    b.respond = wrong_selection
    result = b.poll()
    assert "permission profile" in result["errors"]["1"]
    resumes = [r["params"] for r in b.native if r.get("method") == "thread/resume"]
    assert len(resumes) == 1
    assert resumes[0]["threadId"] == attempt["thread_id"]
    assert resumes[0]["permissions"] == "codex-session-stats-gitlab-monitor"
    assert resumes[0]["config"]["features.network_proxy"] is True
    assert not [r for r in b.native if r.get("method") in {"thread/start", "turn/start"}]
    assert len(b.threads) == 1
    assert any(e["state"] == "pending" for e in state.all("events"))


@pytest.mark.parametrize("instant,open_window", [
    ("2026-10-17T09:59:59+00:00", False), ("2026-10-17T10:00:00+00:00", True),
    ("2026-10-18T00:59:59+00:00", True), ("2026-10-18T01:00:00+00:00", False),
    ("2026-10-18T15:00:00+00:00", False)])
def test_window_and_outside_poll_has_no_io(boundary, instant, open_window):
    b = boundary
    b.now = dt.datetime.fromisoformat(instant)
    assert b.call("is_open", b.config) is open_window
    if not open_window:
        assert b.poll()["skipped"] == "outside_window"
        assert not b.http and not b.native and not Path(b.config["state_file"]).exists()


def test_bootstrap_partial_pages_preserves_cutoff_heads_and_new_notes(boundary):
    b = boundary
    b.mr()
    b.note(note_id=10, created="2020-01-01T00:00:00Z")
    b.note(note_id=11)
    b.fail_page = 2
    b.poll()
    state = b.state()
    start = state.get("meta", "observation_start")
    assert not state.all("events")
    assert state.get("mrs", "1")["first_head"] == "a" * 40
    b.now += dt.timedelta(minutes=1)
    b.mrs[1]["sha"] = "b" * 40
    b.fail_page = None
    b.poll()
    events = [e for e in state.all("events") if e["state"] == "accepted"]
    assert len(events) == 1
    assert events[0]["from_head"] == "a" * 40 and events[0]["to_head"] == "b" * 40
    assert [n["id"] for n in events[0]["notes"]] == [11]
    assert state.get("meta", "observation_start") == start
    assert len(b.threads) == 1
    assert b.token not in json.dumps(b.native)
    assert "$(do-not-execute)" not in json.dumps(b.native)


def test_new_mr_during_bootstrap_and_late_earlier_page_note_revision(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    b.call("complete", b.config, state, 1, {"generation": work["generation"],
        "event_ids": [e["id"] for e in work["events"]], "reviewed_head": "a" * 40})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    note = b.note(note_id=9)
    b.poll()
    event = next(e for e in state.all("events") if e["state"] == "accepted")
    assert [n["id"] for n in event["notes"]] == [9]
    params = [r["params"] for r in b.native if r.get("method") == "turn/start"][-1]
    assert params["input"] == [] and "toolOutput" in params
    note["body"] = "An edited concern"
    b.poll()
    pending = [e for e in state.all("events") if e["state"] == "pending"]
    assert len(pending) == 1 and pending[0]["notes"][0]["revision"] == b.call("digest", note["body"])
    b.poll()
    assert len([e for e in state.all("events") if e["state"] == "pending"]) == 1


def test_cap_raising_recovers_and_distinguishes_global_budget(boundary, monkeypatch):
    b = boundary
    b.mr()
    b.note(note_id=1, created="2020-01-01T00:00:00Z")
    b.note(note_id=2)
    b.config["max_notes_per_mr"] = 1
    assert "per_mr_note_cap" in b.poll()["errors"]["1"]
    state = b.state()
    assert not state.all("events")
    b.config["max_notes_per_mr"] = 2
    assert b.poll()["dispatch"]["1"] == "submitted"
    assert [n["id"] for e in state.all("events") for n in e["notes"]] == [2]
    import time
    ticks = iter([0, 121, 121, 121])
    monkeypatch.setattr(time, "monotonic", lambda: next(ticks))
    with pytest.raises(RuntimeError, match="global_cycle_budget"):
        b.poll()


def test_head_occurrences_and_pending_union_do_not_collapse_accepted_return(boundary):
    b = boundary
    b.mr()
    b.poll()
    b.mrs[1]["sha"] = "b" * 40
    b.poll()
    state = b.state()
    accepted = next(e for e in state.all("events") if e["state"] == "accepted")
    b.mrs[1]["sha"] = "a" * 40
    b.note(note_id=12)
    b.poll()
    pending = next(e for e in state.all("events") if e["state"] == "pending")
    assert pending["from_head"] == "b" * 40 and pending["to_head"] == "a" * 40
    assert pending["last_sequence"] > accepted["last_sequence"]
    b.note(note_id=13)
    b.poll()
    pending = next(e for e in state.all("events") if e["state"] == "pending")
    assert {n["id"] for n in pending["notes"]} == {12, 13}


def test_ack_after_close_and_early_claim_preserves_owner_after_lost_ack(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    holder = {}

    def early(tid, turn):
        b.runtime(tid, turn)
        state = b.state()
        attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
        holder["work"] = b.call("claim", b.config, state, 1,
            {"attempt_id": attempt["id"], "event_id": attempt["event_id"]})
        b.now = dt.datetime(2026, 10, 18, 1, tzinfo=dt.timezone.utc)

    # Callback is synchronous but needs its own event loop as a separate actual agent would have.
    import concurrent.futures
    b.on_start = lambda tid, turn: concurrent.futures.ThreadPoolExecutor(1).submit(early, tid, turn).result()
    b.lost_ack = True
    result = b.poll()
    state = b.state()
    assert holder["work"]["generation"] == 1
    record = state.get("mrs", "1")
    assert record["owner"] and record["generation"] == 1
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    b.call("accept", state, attempt["id"], attempt["turn_id"])
    assert state.get("mrs", "1")["owner"] == record["owner"]
    assert "transport failed" in result["errors"]["1"]
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == 1


def test_mixed_claim_is_rejected_and_unclaimed_event_is_deferred(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    b.call("complete", b.config, state, 1, {"generation": work["generation"], "event_ids": work["owner"]["event_ids"], "reviewed_head": "a" * 40})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    b.note()
    b.poll()
    current = next(a for a in state.all("attempts") if a.get("kind") == "dispatch" and a["state"] == "accepted")
    b.items[current["turn_id"]].append({"type": "userMessage", "content": [{"type": "text", "text": "Human request"}]})
    b.runtime(current["thread_id"], current["turn_id"])
    with pytest.raises(RuntimeError, match="human input"):
        b.call("claim", b.config, state, 1, {"attempt_id": current["id"], "event_id": current["event_id"]})
    b.finish(current["thread_id"], current["turn_id"])
    b.call("reconcile", b.config, state, 1)
    assert state.get("attempts", current["id"])["state"] == "mixed_deferred"
    assert state.get("events", f"1:{current['event_id']}")["state"] == "pending"
    assert state.get("mrs", "1").get("reviewed_head") == "a" * 40


def test_pause_resume_native_answer_carries_pending_events_and_rejects_stale_owner(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    paused = b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": "Posso considerar X correto?"})
    b.mrs[1]["sha"] = "b" * 40
    b.note()
    b.poll()
    with pytest.raises(RuntimeError, match="paused"):
        b.call("complete", b.config, state, 1, {"generation": work["generation"]})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    b.items[attempt["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": paused["question"]})
    human = {"id": "human-turn", "status": "inProgress"}
    b.turns[attempt["thread_id"]].insert(0, human)
    b.items[human["id"]] = [{"type": "userMessage", "content": [{"type": "text", "text": "Por que?"}]}]
    b.runtime(attempt["thread_id"], human["id"])
    answer = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
              "answer_sufficient": True, "answer_summary": "User confirmed X"}
    with pytest.raises(RuntimeError, match="question-only"):
        b.call("resume", b.config, state, 1, answer)
    b.items[human["id"]][0]["content"][0]["text"] = "Pode considerar X correto"
    resumed = b.call("resume", b.config, state, 1, answer)
    assert resumed["generation"] > paused["generation"]
    assert len(resumed["events"]) == 2
    assert resumed["owner"]["origin"] == "human"
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == 1
    b.call("accept", state, attempt["id"], attempt["turn_id"])
    assert state.get("mrs", "1")["owner"]["turn_id"] == "human-turn"


def test_exact_registered_effect_is_reconciled_before_receipt_without_ignoring_actor(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    snap = b.call("snapshot", b.config, b.api(), 1)
    operation = b.call("effect_intent", b.config, state, b.api(), 1,
        {"generation": work["generation"], "head": "a" * 40, "snapshot": snap["fingerprint"],
         "kind": "finding", "key": "file:real-concern", "body": "Concrete source evidence"})
    b.note(note_id=10, body=operation["body"])
    b.note(note_id=11, body="A human using the same account")
    b.note(note_id=12, body=operation["body"] + " different")
    b.poll()
    assert state.get("operations", f"1:{operation['id']}")["state"] == "confirmed"
    pending = next(e for e in state.all("events") if e["state"] == "pending")
    assert {n["id"] for n in pending["notes"]} == {11, 12}
    result = b.call("effect_receipt", b.config, state, b.api(), 1, {"operation_id": operation["id"]})
    assert result["note_id"] == 10
    again = b.call("effect_intent", b.config, state, b.api(), 1,
        {"generation": work["generation"], "kind": "finding", "key": "file:real-concern"})
    assert again["write_allowed"] is False


def test_cross_origin_pagination_rejected_before_followup_and_dry_run_is_readonly(boundary):
    b = boundary
    b.mr()
    b.note()
    b.cross_origin = True
    result = b.poll(dry_run=True)
    assert result["mutated"] is False and not Path(b.config["state_file"]).exists()
    assert not b.native
    state = b.state()
    with pytest.raises(RuntimeError, match="pagination destination"):
        b.call("observe_mr", state, b.api(), b.mrs[1])
    assert all(urlsplit(r.full_url).netloc == "gitlab.example.test" for r in b.http)


@pytest.mark.parametrize("basis", ["bot_false_positive", "verified_fix"])
@pytest.mark.parametrize("disposition", ["open", "uncertain", "unassessed", "valid-unfixed"])
def test_resolution_rejects_any_outstanding_concern(boundary, disposition, basis):
    b = boundary
    b.mr(created=b.now.isoformat())
    root = b.note(author=8)
    b.users[8] = {"id": 8, "bot": True}
    b.poll()
    state, attempt, work = b.active_claim()
    discussion = b.discussions[1][0]["id"]
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    explanation = b.call("effect_intent", b.config, state, b.api(), 1,
        {"generation": work["generation"], "head": "a" * 40, "snapshot": snap["fingerprint"],
         "kind": "reply", "discussion": discussion, "key": "explain:11", "body": "Evidence why claim is wrong"})
    own = {**copy.deepcopy(root), "id": 90, "author": {"id": 7}, "body": explanation["body"]}
    b.discussions[1][0]["notes"].append(own)
    b.call("effect_receipt", b.config, state, b.api(), 1, {"operation_id": explanation["id"]})
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    payload = {"generation": work["generation"], "kind": "resolve", "key": "resolve:11", "head": "a" * 40,
        "discussion": discussion, "snapshot": snap["fingerprint"], "basis": basis,
        "explanation_operation": explanation["id"], "assessment": {"complete": True, "fix_commit": "a" * 40, "notes": [
            {"id": 11, "revision": b.call("digest", root["body"]), "concerns": [
                {"disposition": "fixed" if basis == "verified_fix" else "invalid", "evidence": "source evidence"},
                {"disposition": disposition, "evidence": "second issue"}]},
            {"id": 90, "revision": b.call("digest", own["body"]), "concerns": [], "no_concern_reason": "own explanation"}]}}
    with pytest.raises(RuntimeError, match="prohibits resolution"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)
    assert not [o for o in state.all("operations") if o["kind"] == "resolve"]
    payload["assessment"]["notes"][0]["concerns"][1]["disposition"] = "fixed" if basis == "verified_fix" else "invalid"
    accepted = b.call("effect_intent", b.config, state, b.api(), 1, payload)
    assert accepted["write_allowed"] is True
    for n in b.discussions[1][0]["notes"]:
        n["resolved"] = True
    receipt = b.call("effect_receipt", b.config, state, b.api(), 1, {"operation_id": accepted["id"]})
    assert receipt["state"] == "confirmed"


def test_resolution_rejects_missing_revision_and_human_concern_inside_bot_thread(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    root = b.note(author=8)
    b.users[8] = {"id": 8, "bot": True}
    human = dict(copy.deepcopy(root), id=12, body="Separate human concern", author={"id": 7})
    b.discussions[1][0]["notes"].append(human)
    b.poll()
    state, attempt, work = b.active_claim()
    discussion = b.discussions[1][0]["id"]
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    assessment = {"complete": True, "notes": [
        {"id": 11, "revision": b.call("digest", root["body"]), "concerns": [{"disposition": "invalid", "evidence": "code"}]},
        {"id": 12, "revision": b.call("digest", human["body"]), "concerns": [{"disposition": "invalid", "evidence": "code"}]}]}
    payload = {"generation": work["generation"], "kind": "resolve", "key": "closure", "head": "a" * 40,
               "discussion": discussion, "snapshot": snap["fingerprint"], "basis": "bot_false_positive", "assessment": assessment}
    with pytest.raises(RuntimeError, match="human disagreement"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)
    assessment["notes"].pop()
    with pytest.raises(RuntimeError, match="every current non-system note"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)
    assessment["notes"].append({"id": 12, "revision": "old", "concerns": [], "no_concern_reason": "agreement"})
    with pytest.raises(RuntimeError, match="revision changed"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)


def test_control_cli_and_restart_keep_real_human_hold(boundary, monkeypatch, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path), "claim", "--mr", "1"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"attempt_id": attempt["id"], "event_id": attempt["event_id"]})))
    assert b.module["main"]() == 0
    work = json.loads(capsys.readouterr().out)
    monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path), "pause", "--mr", "1"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"generation": work["generation"], "question": "Qual comportamento esperado?"})))
    assert b.module["main"]() == 0
    paused = json.loads(capsys.readouterr().out)
    status = run_monitor(b.path.parent, "status")
    assert status.returncode == 0, status.stderr
    assert json.loads(status.stdout)["cases"][0]["id"] == paused["case_id"]
    assert b.state().get("mrs", "1")["case_id"] == paused["case_id"]
    # Automation on another MR still proceeds; it cannot clear this hold.
    b.mr(iid=2, created=b.now.isoformat())
    b.poll()
    assert len(b.threads) == 2
    assert state.get("mrs", "1")["case_id"] == paused["case_id"]


def test_late_receipt_filters_previously_pending_own_note_and_net_empty_heads(boundary):
    b = boundary
    mr = b.mr()
    b.poll()
    state = b.state()
    thread = b.call("ensure_thread", b.config, state, mr)
    b.threads[thread]["status"] = {"type": "active"}
    b.mrs[1]["sha"] = "b" * 40
    b.poll()
    assert len([e for e in state.all("events") if e["state"] == "pending"]) == 1
    b.mrs[1]["sha"] = "a" * 40
    b.poll()
    assert not [e for e in state.all("events") if e["state"] == "pending"]
    note = b.note()
    b.poll()
    event = next(e for e in state.all("events") if e["state"] == "pending")
    with state.atomic():
        prior = state.get("notes", "1:11")
        prior["own"] = True
        state.put("notes", "1:11", prior)
    assert b.call("effective_notes", state, event) == []
    b.threads[thread]["status"] = {"type": "idle"}
    result = b.poll()
    # No marker is actually registered for this fixture note: it must remain a participant note.
    assert state.get("notes", "1:11")["own"] is False
    assert result["dispatch"]["1"] == "submitted"


def test_ambiguous_delivery_never_blindly_retries_and_operator_recovery_is_explicit(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.lost_ack = True
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    assert attempt["state"] == "uncertain"
    b.lost_ack = False
    b.poll()
    assert state.get("attempts", attempt["id"])["state"] == "accepted"
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == 1
    b.finish(attempt["thread_id"], b.turns[attempt["thread_id"]][0]["id"])
    result = b.call("recover", b.config, state, {"attempt_id": attempt["id"]})
    assert result["pending"] == attempt["event_id"]
    b.poll()
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == 2


def test_archived_chat_and_changed_binding_fail_without_replacement(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state = b.state()
    record = state.get("mrs", "1")
    b.threads[record["thread_id"]]["archived"] = True
    with pytest.raises(RuntimeError, match="archived"):
        b.call("thread", b.config, record["thread_id"], active_inventory=True)
    changed = dict(b.config, project_id=99)
    with pytest.raises(RuntimeError, match="another project"):
        b.module["MonitorState"](changed, readonly=True)
    assert len(b.threads) == 1


def test_window_crossing_stops_new_requests_and_bounded_scan_is_fair(boundary):
    b = boundary
    b.mr()
    b.mr(iid=2)
    b.note()
    b.note(note_id=12)
    b.config["max_notes_per_mr"] = 1
    b.poll()
    assert b.state().get("mrs", "2")["notes_complete_at"]
    before = len(b.http)
    b.now = dt.datetime(2026, 10, 18, 0, 59, 59, tzinfo=dt.timezone.utc)
    b.after_http = lambda route: setattr(b, "now", dt.datetime(2026, 10, 18, 1, tzinfo=dt.timezone.utc))
    assert b.poll()["inventory_error"] == "outside_window"
    assert len(b.http) == before + 1


def test_invalid_inline_version_and_unreconciled_effect_block_new_writes(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    snap = b.call("snapshot", b.config, b.api(), 1)
    payload = {"generation": work["generation"], "head": "a" * 40, "snapshot": snap["fingerprint"],
               "kind": "finding", "key": "finding-a", "body": "Actionable evidence",
               "position": {"position_type": "text", "head_sha": "wrong", "old_path": "file", "new_path": "file", "new_line": 1}}
    with pytest.raises(RuntimeError, match="immutable diff"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)
    payload["position"] = {"position_type": "text", **b.mrs[1]["diff_refs"], "new_path": "renamed.py", "old_path": "original.py", "old_line": 2}
    operation = b.call("effect_intent", b.config, state, b.api(), 1, payload)
    assert operation["position"]["old_line"] == 2
    with pytest.raises(RuntimeError, match="missing or ambiguous"):
        b.call("effect_receipt", b.config, state, b.api(), 1, {"operation_id": operation["id"]})
    assert state.get("operations", f"1:{operation['id']}")["state"] == "uncertain"
    payload["key"] = "finding-b"
    with pytest.raises(RuntimeError, match="uncertain effects"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)


@pytest.mark.parametrize("origin", ["human", "display_bot", "missing_bot_metadata"])
def test_bot_closure_needs_authenticated_origin_not_name_or_caller_boolean(boundary, origin):
    b = boundary
    b.mr(created=b.now.isoformat())
    root = b.note()
    b.users[7] = {"id": 7, "name": "Helpful Bot", **({"bot": False} if origin != "missing_bot_metadata" else {})}
    b.poll()
    state, attempt, work = b.active_claim()
    discussion = b.discussions[1][0]["id"]
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    payload = {"generation": work["generation"], "kind": "resolve", "key": "do-not-close", "head": "a" * 40,
               "discussion": discussion, "snapshot": snap["fingerprint"], "basis": "bot_false_positive", "is_bot": True,
               "assessment": {"complete": True, "notes": [{"id": root["id"], "revision": b.call("digest", root["body"]),
                    "concerns": [{"disposition": "invalid", "evidence": "source"}]}]}}
    with pytest.raises(RuntimeError, match="root automation origin"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)
    assert not state.all("operations")


def test_consumer_contract_preserves_all_concerns_and_explicit_boundaries(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    request = next(r for r in b.native if r.get("method") == "turn/start")
    text = request["params"]["input"][0]["text"]
    for required in ["every concern", "Human", "effect-intent", "effect-receipt", "pause", "resume", "complete", "bot:true", "Unfixed, unassessed or uncertain", "No additional agents"]:
        assert required.lower() in text.lower()
    assert request["params"]["permissions"] == "codex-session-stats-gitlab-monitor"
    assert not {"approvalPolicy", "sandbox", "sandboxPolicy", "config"} & request["params"].keys()


def test_operator_effect_recovery_requires_idle_and_absent_authenticated_effect(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    snap = b.call("snapshot", b.config, b.api(), 1)
    payload = {"generation": work["generation"], "head": "a" * 40, "snapshot": snap["fingerprint"],
               "kind": "finding", "key": "test:concern", "body": "Code evidence"}
    operation = b.call("effect_intent", b.config, state, b.api(), 1, payload)
    with pytest.raises(RuntimeError, match="busy"):
        b.call("operator_recovery", b.config, state, 1, {"operation_id": operation["id"]})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    b.note(body=operation["body"])
    with pytest.raises(RuntimeError, match="matching public note exists"):
        b.call("operator_recovery", b.config, state, 1, {"operation_id": operation["id"]})
    b.discussions[1] = []
    recovered = b.call("operator_recovery", b.config, state, 1, {"operation_id": operation["id"]})
    assert recovered["abandoned_operation"] == operation["id"]
    assert state.get("operations", f"1:{operation['id']}")["state"] == "abandoned_no_effect"
    # The old marker remains reconcilable if visibility was delayed despite operator inspection.
    b.note(body=operation["body"])
    b.poll()
    assert state.get("operations", f"1:{operation['id']}")["state"] == "confirmed"


def test_finished_human_owner_recovery_preserves_receipts_and_invalidates_generation(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    with state.atomic():
        record = state.get("mrs", "1")
        record["owner"] = {"origin": "human", "turn_id": attempt["turn_id"], "event_ids": work["owner"]["event_ids"]}
        state.put("mrs", "1", record)
    b.finish(attempt["thread_id"], attempt["turn_id"])
    result = b.call("operator_recovery", b.config, state, 1, {"owner_turn": attempt["turn_id"]})
    assert result["released_owner"] == attempt["turn_id"]
    assert state.get("mrs", "1")["owner"] is None
    assert state.get("mrs", "1")["generation"] > work["generation"]
    assert next(e for e in state.all("events"))["state"] == "pending"


def test_conflicting_late_ack_holds_existing_owner_until_exact_native_reconciliation(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    with pytest.raises(RuntimeError, match="conflicts"):
        b.call("accept", state, attempt["id"], "different-turn")
    assert state.get("mrs", "1")["delivery_conflict"] == attempt["id"]
    with pytest.raises(RuntimeError, match="stale, mismatched or paused"):
        b.call("complete", b.config, state, 1, {"generation": work["generation"],
            "event_ids": work["owner"]["event_ids"], "reviewed_head": "a" * 40})
    assert state.get("mrs", "1")["owner"] == work["owner"]
    b.call("reconcile", b.config, state, 1)
    assert state.get("mrs", "1")["delivery_conflict"] is None
    assert state.get("mrs", "1")["owner"] == work["owner"]


def test_human_disagreement_cannot_be_relabelled_verified_fix(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    root = b.note()
    b.poll()
    state, attempt, work = b.active_claim()
    discussion = b.discussions[1][0]["id"]
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    payload = {"generation": work["generation"], "kind": "resolve", "key": "bad-basis", "head": "a" * 40,
        "discussion": discussion, "snapshot": snap["fingerprint"], "basis": "verified_fix",
        "assessment": {"complete": True, "fix_commit": "a" * 40, "notes": [
            {"id": root["id"], "revision": b.call("digest", root["body"]), "concerns": [
                {"disposition": "invalid", "evidence": "mere disagreement, no fix"}]}]}}
    with pytest.raises(RuntimeError, match="at least one evidenced fixed"):
        b.call("effect_intent", b.config, state, b.api(), 1, payload)


def test_later_partial_mr_gets_next_fresh_budget_without_starving_first(boundary, monkeypatch):
    import time
    b = boundary
    elapsed = [0]
    monkeypatch.setattr(time, "monotonic", lambda: elapsed[0])
    b.mr(iid=1)
    b.mr(iid=2)
    b.note(iid=1, created="2020-01-01T00:00:00Z")
    for note_id in (21, 22, 23):
        b.note(iid=2, note_id=note_id, created="2020-01-01T00:00:00Z" if note_id < 23 else None)

    def cost(route):
        if route.endswith("/1/discussions"):
            elapsed[0] += 80
        elif route.endswith("/2/discussions"):
            elapsed[0] += 30

    b.after_http = cost
    first = b.poll()
    state = b.state()
    assert first["errors"]["2"] == "global_cycle_budget"
    assert state.get("meta", "pivot") == 1
    assert state.get("notes", "2:23") is None
    b.poll()
    assert state.get("notes", "2:23") is not None
    assert state.get("mrs", "2")["notes_complete_at"]
    assert state.get("meta", "pivot") == 2


@pytest.mark.skipif(not hasattr(os, "fork"), reason="real SIGKILL-equivalent process exit tests Linux monitor recovery")
@pytest.mark.parametrize("remote_created", [False, True])
def test_creation_hard_exit_attempt_is_recoverable_without_automatic_duplicate(boundary, remote_created):
    b = boundary
    mr = b.mr()
    state = b.state()
    original = b.respond
    child = os.fork()
    if child == 0:
        def crash(method, params):
            if method == "thread/start":
                if remote_created:
                    original(method, params)
                os._exit(23)
            return original(method, params)
        b.respond = crash
        b.call("ensure_thread", b.config, b.state(), mr)
        os._exit(99)
    _, code = os.waitpid(child, 0)
    assert os.waitstatus_to_exitcode(code) == 23
    attempt = next(a for a in state.all("attempts") if a["kind"] == "conversation")
    assert attempt["state"] == "attempting"
    with pytest.raises(RuntimeError, match="uncertain"):
        b.call("ensure_thread", b.config, state, mr)
    if remote_created:
        # External server state persisted across the client's hard exit.
        existing = original("thread/start", {})["thread"]["id"]
        result = b.call("recover", b.config, state, {"attempt_id": attempt["id"], "thread_id": existing})
        assert result["recovered_thread"] == existing
        assert b.call("ensure_thread", b.config, state, mr) == existing
        assert len(b.threads) == 1
    else:
        b.call("recover", b.config, state, {"attempt_id": attempt["id"], "confirm_no_conversation": True})
        assert state.get("mrs", "1")["creation_attempt"] is None
        assert state.get("attempts", attempt["id"])["state"] == "operator_retried"
        b.call("ensure_thread", b.config, state, mr)
        assert len(b.threads) == 1


def test_retry_without_native_bootstrap_keeps_full_standing_instructions(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    original = b.respond

    def fail_before_start(method, params):
        if method == "turn/start":
            raise TimeoutError("failed before native acceptance")
        return original(method, params)

    b.respond = fail_before_start
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    assert attempt["state"] == "uncertain" and not b.items
    b.call("recover", b.config, state, {"attempt_id": attempt["id"]})
    b.respond = original
    b.poll()
    accepted = next(a for a in state.all("attempts") if a.get("kind") == "dispatch" and a["state"] == "accepted")
    assert accepted["bootstrap"] is True
    params = [r["params"] for r in b.native if r.get("method") == "turn/start"][-1]
    assert params["input"][0]["text"].startswith("Standing task explicitly approved")
    assert "toolOutput" not in params


def human_turn(b, tid, text):
    turn = {"id": f"human-{len(b.items) + 1}", "status": "inProgress"}
    b.turns[tid].insert(0, turn)
    b.items[turn["id"]] = [{"type": "userMessage", "content": [{"type": "text", "text": text}]}]
    b.runtime(tid, turn["id"])
    return turn["id"]


def test_lost_question_reanchors_only_from_human_and_keeps_hold_until_another_answer(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    paused = b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": "X está correto?"})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    tid = attempt["thread_id"]
    first_human = human_turn(b, tid, "Reapresente a pergunta")
    payload = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
               "answer_sufficient": True, "answer_summary": "X confirmed"}
    with pytest.raises(RuntimeError, match="persisted final question"):
        b.call("resume", b.config, state, 1, payload)
    anchored = b.call("reanchor", b.config, state, 1, payload)
    assert anchored["held"] and anchored["question"] == paused["question"]
    assert state.get("mrs", "1")["owner"] is None
    payload["expected_generation"] = anchored["generation"]
    with pytest.raises(RuntimeError, match="completed question anchor"):
        b.call("resume", b.config, state, 1, payload)
    b.items[first_human].append({"type": "agentMessage", "phase": "final_answer", "text": anchored["question"]})
    b.finish(tid, first_human)
    human_turn(b, tid, "X está correto, prossiga")
    resumed = b.call("resume", b.config, state, 1, payload)
    assert resumed["owner"]["origin"] == "human"
    assert resumed["owner"]["event_ids"] == work["owner"]["event_ids"]


@pytest.mark.parametrize("legacy_missing_text", [False, True])
def test_unacknowledged_diagnostic_input_never_counts_as_human_consent(boundary, legacy_missing_text):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    paused = b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": "Pode continuar?"})
    b.items[attempt["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": paused["question"]})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    diagnostic_id = b.call("id")
    text = "Integration pilot for the user-approved GitLab MR monitor. Pilot marker: " + diagnostic_id + "."
    # Historical/previously accepted producer intent with a lost acknowledgement.
    diagnostic = {"id": diagnostic_id, "kind": "pilot_check", "iid": 1,
                  "thread_id": attempt["thread_id"], "state": "uncertain"}
    if not legacy_missing_text:
        diagnostic["input_text"] = text
    with state.atomic():
        state.put("attempts", diagnostic_id, diagnostic)
    native = b.respond("turn/start", {"threadId": attempt["thread_id"], "input": [{"type": "text", "text": text}]})
    b.runtime(attempt["thread_id"], native["turn"]["id"])
    with pytest.raises(RuntimeError, match="real native human action"):
        b.call("resume", b.config, state, 1, {"case_id": paused["case_id"],
            "expected_generation": paused["generation"], "answer_sufficient": True, "answer_summary": "not a human"})
    with pytest.raises(RuntimeError, match="real native human action"):
        b.call("reanchor", b.config, state, 1, {"case_id": paused["case_id"], "expected_generation": paused["generation"]})
    assert state.get("mrs", "1")["case_id"] == paused["case_id"]


def test_pilot_cli_refuses_held_conversation_and_operator_recovery_takes_poll_lock(boundary, monkeypatch, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": "Aguarde minha decisão"})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    before = len([r for r in b.native if r.get("method") == "turn/start"])
    monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path), "pilot", "--mr", "1", "--verify"])
    assert b.module["main"]() == 1
    assert "human hold" in capsys.readouterr().err
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == before
    lock = b.call("acquire_lock", b.config)
    try:
        monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
            "recover", "--attempt", attempt["id"], "--acknowledge-duplicate-risk"])
        assert b.module["main"]() == 1
        assert "already running" in capsys.readouterr().err
    finally:
        os.close(lock)


def test_resolution_context_change_can_be_disposed_only_by_exact_native_user_case(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    root = b.note(author=8)
    b.users[8] = {"id": 8, "bot": True}
    b.poll()
    state, attempt, work = b.active_claim()
    discussion = b.discussions[1][0]["id"]
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    explanation = b.call("effect_intent", b.config, state, b.api(), 1,
        {"generation": work["generation"], "head": "a" * 40, "snapshot": snap["fingerprint"],
         "kind": "reply", "discussion": discussion, "key": "explain", "body": "Code proves the bot concern is invalid"})
    own = {**copy.deepcopy(root), "id": 90, "author": {"id": 7}, "body": explanation["body"]}
    b.discussions[1][0]["notes"].append(own)
    b.call("effect_receipt", b.config, state, b.api(), 1, {"operation_id": explanation["id"]})
    snap = b.call("snapshot", b.config, b.api(), 1, discussion)
    op = b.call("effect_intent", b.config, state, b.api(), 1,
        {"generation": work["generation"], "kind": "resolve", "key": "resolve", "head": "a" * 40,
         "discussion": discussion, "snapshot": snap["fingerprint"], "basis": "bot_false_positive",
         "explanation_operation": explanation["id"], "assessment": {"complete": True, "notes": [
            {"id": 11, "revision": b.call("digest", root["body"]), "concerns": [{"disposition": "invalid", "evidence": "code"}]},
            {"id": 90, "revision": b.call("digest", own["body"]), "concerns": [], "no_concern_reason": "own explanation"}]}})
    for n in b.discussions[1][0]["notes"]:
        n["resolved"] = True
    b.mrs[1]["sha"] = "b" * 40
    with pytest.raises(RuntimeError, match="human decision"):
        b.call("effect_receipt", b.config, state, b.api(), 1, {"operation_id": op["id"]})
    assert state.get("operations", f"1:{op['id']}")["resolution_seen"] is True
    paused = b.call("pause", b.config, state, 1, {"generation": work["generation"],
        "operation_id": op["id"], "question": "O contexto mudou; aceita o encerramento observado?"})
    b.poll()
    b.items[attempt["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": paused["question"]})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    human_turn(b, attempt["thread_id"], "Aceito o encerramento observado; analise o novo contexto")
    answer = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
              "answer_sufficient": True, "answer_summary": "User accepted this observed outcome",
              "accept_observed_resolution": "wrong-operation"}
    with pytest.raises(RuntimeError, match="exact case"):
        b.call("resume", b.config, state, 1, answer)
    assert state.get("mrs", "1")["case_id"] == paused["case_id"]
    answer["accept_observed_resolution"] = op["id"]
    b.now = dt.datetime(2026, 10, 18, 2, tzinfo=dt.timezone.utc)
    resumed = b.call("resume", b.config, state, 1, answer)
    receipt = state.get("operations", f"1:{op['id']}")
    assert receipt["state"] == "confirmed" and receipt["context_accepted_by_case"] == paused["case_id"]
    assert receipt["snapshot"] != receipt["observed_snapshot"] or receipt["head"] != receipt["observed_head"]
    b.call("complete", b.config, state, 1, {"generation": resumed["generation"],
        "event_ids": resumed["owner"]["event_ids"], "reviewed_head": "b" * 40})
    assert state.get("mrs", "1")["reviewed_head"] == "b" * 40
