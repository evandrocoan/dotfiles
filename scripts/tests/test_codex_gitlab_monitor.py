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


def restricted_monitor_metadata(monkeypatch, *, ancestor=None, endpoint=None):
    original_lstat, original_stat = Path.lstat, Path.stat
    def lstat(path, *args, **kwargs):
        metadata = original_lstat(path, *args, **kwargs)
        if path == ancestor:
            fields = list(metadata)
            fields[4] = os.getuid() + 1
            return os.stat_result(fields)
        return metadata
    def stat(path, *args, **kwargs):
        if path == endpoint:
            raise PermissionError(13, "sandbox endpoint inspection denied", str(path))
        return original_stat(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(Path, "stat", stat)


@pytest.mark.parametrize("fault", ["ancestor", "endpoint", "both"])
@pytest.mark.parametrize("initialized", [False, True])
def test_offline_status_reads_held_state_under_restricted_metadata(
        tmp_path, monkeypatch, capsys, fault, initialized):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    module = runpy.run_path(str(CLI))
    loaded = module["monitor_config"](tmp_path / "monitor.json")
    mr = {"iid": 42, "generation": 7, "owner": None, "case_id": "held",
          "human_continuation_verified": False}
    case = {"id": "held", "iid": 42, "state": "awaiting_user"}
    state_file = Path(config["state_file"])
    if initialized:
        historical = {**loaded, "socket": str(tmp_path / "historical.sock")}
        state = module["MonitorState"](historical)
        state.put("mrs", "42", mr)
        state.put("cases", "held", case)
        state.db.close()
    paths = [target, tmp_path / "monitor.json"] + ([state_file] if initialized else [])
    before = {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in paths}
    restricted_monitor_metadata(monkeypatch,
        ancestor=tmp_path if fault in {"ancestor", "both"} else None,
        endpoint=Path(loaded["socket"]) if fault in {"endpoint", "both"} else None)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "absent-runtime"))
    def forbidden(*args, **kwargs):
        pytest.fail("offline status must not connect, read credentials or provision permissions")
    code = module["monitor_main"].__globals__
    for name in ("monitor_native", "monitor_credential", "monitor_ensure_permissions", "MonitorGitLab"):
        assert name in code
        monkeypatch.setitem(code, name, forbidden)
    monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config",
                                     str(tmp_path / "monitor.json"), "status"])
    assert module["monitor_main"]() == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert captured.err == ""
    assert result["configured"] is True
    assert result["initialized"] is initialized
    assert result["endpoint_verified"] is False
    assert result["control_rule"]["state"] == "missing"
    assert result["control_rule"]["load_state"] == "not_verified"
    assert result["mrs"] == ([mr] if initialized else [])
    if initialized:
        assert result["cases"] == [case]
        for readonly in (False, True):
            with pytest.raises(RuntimeError, match="another project, endpoint or schema"):
                module["MonitorState"](loaded, readonly=readonly)
    assert {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in paths} == before
    assert state_file.exists() is initialized
    assert not (Path(config["codex_home"]) / "rules").exists()


@pytest.mark.parametrize("arguments", [
    ["preflight", "--check-only"], ["resume", "--mr", "42"], ["poll", "--dry-run"],
])
def test_nonstatus_commands_keep_analysis_ancestor_ownership_checks(
        tmp_path, monkeypatch, capsys, arguments):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    module = runpy.run_path(str(CLI))
    before = (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())
    restricted_monitor_metadata(monkeypatch, ancestor=tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("invalid configuration must fail before native or credential access")
    code = module["monitor_main"].__globals__
    for name in ("monitor_shared_owner", "monitor_native", "monitor_credential", "MonitorGitLab"):
        monkeypatch.setitem(code, name, forbidden)
    monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config",
                                     str(tmp_path / "monitor.json"), *arguments])
    assert module["monitor_main"]() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "trusted configuration directory must be owned" in captured.err
    with pytest.raises(RuntimeError, match="trusted configuration directory must be owned"):
        module["monitor_config"](tmp_path / "monitor.json")
    assert (target.read_bytes(), (tmp_path / "monitor.json").read_bytes()) == before
    assert not Path(config["state_file"]).exists()


@pytest.mark.parametrize("field", ["schema", "project_id", "gitlab_url", "cwd"])
def test_offline_denied_endpoint_does_not_hide_other_binding_mismatches(
        tmp_path, monkeypatch, capsys, field):
    config = configure(tmp_path)
    module = runpy.run_path(str(CLI))
    state = module["MonitorState"]({**config, "socket": str(tmp_path / "historical.sock")})
    identity = state.get("meta", "identity")
    if field == "schema":
        identity["schema"] = 2
    else:
        identity["binding"][field] = 99 if field == "project_id" else "other"
    state.put("meta", "identity", identity)
    state.db.close()
    before = Path(config["state_file"]).read_bytes()
    restricted_monitor_metadata(monkeypatch, endpoint=Path(config["socket"]))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "absent-runtime"))
    monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config",
                                     str(tmp_path / "monitor.json"), "status"])
    assert module["monitor_main"]() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "another project, endpoint or schema" in captured.err
    assert Path(config["state_file"]).read_bytes() == before


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


def analysis_config(tmp_path, config):
    root = tmp_path / "analysis"
    root.mkdir(mode=0o700)
    (root / "workspace").mkdir(mode=0o700)
    target = root / "config.toml"
    target.write_text('model = "gpt-6.1-sol"\nmodel_reasoning_effort = "high"\n')
    target.chmod(0o600)
    data = {k: v for k, v in config.items() if k not in {"cwd", "model", "effort"}}
    data["analysis_config"] = "analysis/config.toml"
    (tmp_path / "monitor.json").write_text(json.dumps(data))
    return target, data


def test_analysis_toml_is_the_single_source_and_status_stays_offline(tmp_path):
    config = configure(tmp_path)
    target, data = analysis_config(tmp_path, config)
    module = runpy.run_path(str(CLI))
    loaded = module["monitor_config"](tmp_path / "monitor.json")
    assert loaded["cwd"] == str(target.parent / "workspace")
    assert (loaded["model"], loaded["effort"]) == ("gpt-6.1-sol", "high")
    before = (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["initialized"] is False
    assert (target.read_bytes(), (tmp_path / "monitor.json").read_bytes()) == before
    assert not Path(config["state_file"]).exists()


@pytest.mark.parametrize("kind", ["relative", "absolute", "home"])
def test_analysis_toml_resolves_configurable_workspace_from_its_own_directory(tmp_path, monkeypatch, kind):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    workspace = tmp_path / "work trees" / "selected"
    workspace.mkdir(parents=True)
    choices = {"relative": "../work trees/selected", "absolute": str(workspace),
               "home": "~/work trees/selected"}
    monkeypatch.setenv("HOME", str(tmp_path))
    target.write_text(target.read_text() + f"workspace = {json.dumps(choices[kind])}\n")
    module = runpy.run_path(str(CLI))
    loaded = module["monitor_config"](tmp_path / "monitor.json")
    assert loaded["cwd"] == str(workspace)
    assert (loaded["model"], loaded["effort"]) == ("gpt-6.1-sol", "high")


@pytest.mark.parametrize("value", ['""', '12', '[]', '{}'])
def test_analysis_toml_rejects_invalid_workspace_value(tmp_path, value):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    target.write_text(target.read_text() + f"workspace = {value}\n")
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 1
    assert "invalid workspace" in result.stderr
    assert not Path(config["state_file"]).exists()


@pytest.mark.parametrize("kind", ["missing", "file", "state", "state_symlink"])
def test_analysis_toml_keeps_configured_workspace_directory_boundary(tmp_path, kind):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    state_dir = Path(config["state_file"]).parent
    state_dir.mkdir(parents=True, mode=0o700)
    workspace = target.parent / "selected"
    if kind == "file": workspace.touch()
    if kind == "state": workspace = state_dir
    if kind == "state_symlink": workspace.symlink_to(state_dir, target_is_directory=True)
    target.write_text(target.read_text() + f"workspace = {json.dumps(str(workspace))}\n")
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 1
    assert "analysis configuration" in result.stderr
    assert not Path(config["state_file"]).exists()


@pytest.mark.parametrize("key", ["cwd", "model", "effort"])
def test_analysis_toml_rejects_duplicate_json_authority(tmp_path, key):
    config = configure(tmp_path)
    target, data = analysis_config(tmp_path, config)
    data[key] = config[key]
    (tmp_path / "monitor.json").write_text(json.dumps(data))
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 1
    assert "duplicate analysis settings" in result.stderr


@pytest.mark.parametrize("content", [
    'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "high"\napproval_policy = "never"\n',
    'model = "gpt-6.1-sol"\n',
    'model = 12\nmodel_reasoning_effort = "high"\n',
    'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "invalid"\n',
    'not valid toml',
])
def test_analysis_toml_rejects_invalid_settings(tmp_path, content):
    config = configure(tmp_path)
    target, data = analysis_config(tmp_path, config)
    target.write_text(content)
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 1
    assert "analysis configuration" in result.stderr


@pytest.mark.parametrize("kind", ["public", "symlink", "ancestor_symlink", "inside_state", "oversized"])
def test_analysis_toml_keeps_trusted_source_boundary(tmp_path, kind):
    config = configure(tmp_path)
    target, data = analysis_config(tmp_path, config)
    if kind == "public":
        target.chmod(0o644)
    elif kind == "symlink":
        other = target.with_name("real.toml")
        target.rename(other)
        target.symlink_to(other.name)
    elif kind == "ancestor_symlink":
        other = target.parent.with_name("real-analysis")
        target.parent.rename(other)
        target.parent.symlink_to(other.name, target_is_directory=True)
    elif kind == "inside_state":
        directory = Path(config["state_file"]).parent
        directory.mkdir(parents=True, mode=0o700)
        other = directory / "config.toml"
        other.write_bytes(target.read_bytes())
        other.chmod(0o600)
        data["analysis_config"] = str(other)
        (tmp_path / "monitor.json").write_text(json.dumps(data))
    else:
        target.write_text("#" + "x" * 65536)
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 1
    assert "analysis configuration" in result.stderr


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
        # Model an installed trusted executable with safe ownership/mode. The live
        # home script may intentionally have different permissions; never chmod it.
        self.cli = tmp_path / "bin/codex-session-stats"
        self.cli.parent.mkdir(mode=0o700)
        self.cli.write_bytes(CLI.read_bytes())
        self.cli.chmod(0o700)
        self.module = runpy.run_path(str(self.cli))
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
        home.mkdir(parents=True, mode=0o700)
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
            thread = {"id": tid, "cwd": params.get("cwd", self.config["cwd"]), "status": {"type": "idle"},
                      "preview": "", "ephemeral": False, "source": "vscode", "modelProvider": "openai"}
            self.threads[tid] = thread
            self.turns[tid] = []
            return {"thread": thread, "activePermissionProfile": {
                "id": params.get("permissions"), "extends": ":read-only"}}
        if method in {"thread/read", "thread/resume"}:
            return {"thread": self.threads[params["threadId"]], "activePermissionProfile": {
                "id": params.get("permissions"), "extends": ":read-only"}}
        if method == "thread/list":
            archived = params.get("archived", False)
            sources = params.get("sourceKinds") or ["cli", "vscode"]
            providers = params.get("modelProviders")
            return {"data": [t for t in self.threads.values()
                if bool(t.get("archived")) == archived and (archived or t.get("preview", ""))
                and (not params.get("cwd") or t["cwd"] == params["cwd"])
                and t["source"] in sources and (not providers or t["modelProvider"] in providers)],
                "nextCursor": None}
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
            if params["input"] and not self.threads[tid]["preview"]:
                self.threads[tid]["preview"] = params["input"][0]["text"][:128]
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


def test_poll_registers_scoped_control_rule_and_preserves_matching_file(boundary):
    import ast
    b = boundary
    b.poll()
    target = Path(b.config["codex_home"]) / "rules/codex-session-stats-gitlab-monitor.rules"
    content = target.read_text()
    expression = ast.parse(content).body[0].value
    assert expression.func.id == "prefix_rule"
    fields = {k.arg: ast.literal_eval(k.value) for k in expression.keywords}
    assert fields["decision"] == "allow"
    assert fields["pattern"][:4] == [str(b.cli.resolve()), "monitor-gitlab", "--config", str(b.path)]
    assert set(fields["pattern"][4]) == {"claim", "pause", "resume", "reanchor", "snapshot",
        "effect-intent", "effect-receipt", "complete"}
    assert fields["pattern"][5:] == ["--mr"]
    assert target.stat().st_mode & 0o777 == 0o600
    before = (target.read_bytes(), target.stat().st_mtime_ns)
    assert list(target.parent.iterdir()) == [target]
    b.poll()
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    assert not b.threads


def test_offline_status_checks_installed_rule_under_remapped_ancestor(boundary, monkeypatch, capsys):
    b = boundary
    settings, _ = analysis_config(b.path.parent, b.config)
    b.config = b.call("config", b.path)
    rule = b.call("control_rule", b.config, b.path, install=True)
    target = Path(rule["file"])
    state = b.state()
    mr = {"iid": 42, "generation": 7, "owner": None, "case_id": "held"}
    case = {"id": "held", "iid": 42, "state": "awaiting_user"}
    state.put("mrs", "42", mr)
    state.put("cases", "held", case)
    state.db.close()
    paths = [b.cli, b.path, settings, Path(b.config["state_file"]), target]
    before = {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in paths}
    restricted_monitor_metadata(monkeypatch, ancestor=b.path.parent)
    def forbidden(*args, **kwargs):
        pytest.fail("offline rule inspection must not connect, read credentials or provision permissions")
    for name in ("monitor_native", "monitor_credential", "monitor_ensure_permissions", "MonitorGitLab"):
        monkeypatch.setitem(b.code, name, forbidden)
    code, captured = monitor_cli(b, capsys, "status")
    assert code == 0, captured.err
    result = json.loads(captured.out)
    assert result["control_rule"] == {**rule, "changed": False}
    assert result["control_rule"]["state"] == "configured_on_disk"
    assert result["control_rule"]["load_state"] == "not_verified"
    assert result["mrs"] == [mr] and result["cases"] == [case]
    assert {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in paths} == before
    assert not b.http and not b.native


@pytest.mark.parametrize("fault,diagnostic", [
    ("bytes", "control rule conflicts or is unsafe"),
    ("rule_mode", "control rule conflicts or is unsafe"),
    ("rule_link", "control rule is unavailable or unsafe"),
    ("directory_link", "control rule is unavailable or unsafe"),
    ("directory_owner", "control rule directory must be owned"),
    ("config_mode", "trusted configuration"),
    ("script_mode", "trusted script"),
])
def test_rule_diagnostic_keeps_leaf_and_directory_guards(boundary, monkeypatch, fault, diagnostic):
    b = boundary
    target = Path(b.call("control_rule", b.config, b.path, install=True)["file"])
    if fault == "bytes":
        target.write_text(target.read_text().replace('"claim"', '"merge"'))
    elif fault == "rule_mode":
        target.chmod(0o644)
    elif fault == "rule_link":
        other = target.with_name("other.rules")
        target.rename(other)
        target.symlink_to(other.name)
    elif fault == "directory_link":
        directory = target.parent
        other = directory.with_name("actual-rules")
        directory.rename(other)
        directory.symlink_to(other.name, target_is_directory=True)
    elif fault == "directory_owner":
        original_fstat = os.fstat
        directory = target.parent.stat()
        def fstat(descriptor):
            metadata = original_fstat(descriptor)
            if (metadata.st_dev, metadata.st_ino) == (directory.st_dev, directory.st_ino):
                fields = list(metadata)
                fields[4] = os.getuid() + 1
                return os.stat_result(fields)
            return metadata
        monkeypatch.setattr(os, "fstat", fstat)
    elif fault == "config_mode":
        b.path.chmod(0o640)
    else:
        b.cli.chmod(0o600)
    paths = [b.cli, b.path, target]
    before = {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in paths}
    restricted_monitor_metadata(monkeypatch, ancestor=b.path.parent)
    result = b.call("control_rule_status", b.config, b.path)
    assert result["state"] == "conflict_or_unreadable"
    assert diagnostic in result["diagnostic"]
    assert result["load_state"] == "not_verified"
    assert {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in paths} == before
    assert not b.http and not b.native


@pytest.mark.parametrize("install", [False, True])
def test_control_rule_keeps_strict_ancestor_checks(boundary, monkeypatch, install):
    b = boundary
    before = (b.cli.read_bytes(), b.path.read_bytes())
    restricted_monitor_metadata(monkeypatch, ancestor=b.path.parent)
    with pytest.raises(RuntimeError, match="trusted script directory must be owned"):
        b.call("control_rule", b.config, b.path, install=install)
    assert (b.cli.read_bytes(), b.path.read_bytes()) == before
    assert not (Path(b.config["codex_home"]) / "rules").exists()
    assert not b.http and not b.native


def test_diagnostic_rule_installation_fails_before_definition_access(boundary, monkeypatch):
    b = boundary
    def forbidden(*args, **kwargs):
        pytest.fail("diagnostic installation must fail before definition or filesystem access")
    monkeypatch.setitem(b.code, "monitor_control_rule_definition", forbidden)
    with pytest.raises(RuntimeError, match="diagnostic.*install"):
        b.call("control_rule", b.config, b.path, diagnostic=True, install=True)
    assert not (Path(b.config["codex_home"]) / "rules").exists()
    assert not b.http and not b.native


@pytest.mark.parametrize("location", ["script", "script_parent", "config_parent", "codex_home", "rules_directory"])
@pytest.mark.parametrize("mode", [0o775, 0o777])
def test_control_rule_accepts_existing_writable_modes_without_chmod(boundary, location, mode):
    b = boundary
    home = Path(b.config["codex_home"])
    directory = home / "rules"
    directory.mkdir(mode=0o700)
    paths = {"script": b.cli, "script_parent": b.cli.parent, "config_parent": b.path.parent,
             "codex_home": home, "rules_directory": directory}
    paths[location].chmod(mode)
    before_modes = {name: path.stat().st_mode & 0o777 for name, path in paths.items()}
    first = b.poll()
    target = directory / "codex-session-stats-gitlab-monitor.rules"
    assert first["control_rule"]["state"] == "configured_on_disk"
    assert first["control_rule"]["changed"] is True
    assert target.read_text() == b.call("control_rule_definition", b.config, b.path)
    assert target.stat().st_mode & 0o777 == 0o600
    before = (target.read_bytes(), target.stat().st_mtime_ns)
    second = b.poll()
    assert second["control_rule"]["changed"] is False
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    assert {name: path.stat().st_mode & 0o777 for name, path in paths.items()} == before_modes
    assert not b.threads


@pytest.mark.parametrize("kind", ["conflict", "same_size_conflict", "symlink", "directory_link"])
def test_control_rule_conflict_never_overwrites_or_provisions_profile(boundary, kind):
    b = boundary
    directory = Path(b.config["codex_home"]) / "rules"
    other = b.path.parent / "other-rule"
    other.write_text('prefix_rule(pattern=["bash"],decision="allow")\n')
    other.chmod(0o600)
    if kind == "directory_link":
        directory.symlink_to(b.path.parent, target_is_directory=True)
    else:
        directory.mkdir(mode=0o700)
        target = directory / "codex-session-stats-gitlab-monitor.rules"
        if kind == "symlink":
            target.symlink_to(other)
        else:
            content = (b.call("control_rule_definition", b.config, b.path).replace('"claim"', '"merge"')
                       if kind == "same_size_conflict" else other.read_text())
            target.write_text(content)
            target.chmod(0o600)
    before = other.read_bytes()
    with pytest.raises(RuntimeError, match="control rule"):
        b.poll()
    assert other.read_bytes() == before
    assert "permissions" not in b.codex_settings
    assert not b.http and not b.native


@pytest.mark.parametrize("mode", [0o644, 0o660])
def test_control_rule_still_rejects_nonprivate_exact_rule_without_overwriting(boundary, mode):
    b = boundary
    directory = Path(b.config["codex_home"]) / "rules"
    directory.mkdir(mode=0o700)
    target = directory / "codex-session-stats-gitlab-monitor.rules"
    target.write_text(b.call("control_rule_definition", b.config, b.path))
    target.chmod(mode)
    before = (target.read_bytes(), target.stat().st_mtime_ns, target.stat().st_mode)
    with pytest.raises(RuntimeError, match="control rule conflicts or is unsafe"):
        b.poll()
    assert (target.read_bytes(), target.stat().st_mtime_ns, target.stat().st_mode) == before
    assert "permissions" not in b.codex_settings
    assert not b.http and not b.native


@pytest.mark.parametrize("mode", [0o640, 0o660])
def test_control_rule_still_rejects_nonprivate_configuration(boundary, mode):
    b = boundary
    b.cli.chmod(0o775)
    b.cli.parent.chmod(0o775)
    b.path.chmod(mode)
    with pytest.raises(RuntimeError, match="trusted configuration"):
        b.poll()
    assert b.path.stat().st_mode & 0o777 == mode
    assert "permissions" not in b.codex_settings
    assert not (Path(b.config["codex_home"]) / "rules").exists()
    assert not b.http and not b.native


def test_control_rule_still_requires_an_executable_script(boundary):
    b = boundary
    b.cli.chmod(0o660)
    with pytest.raises(RuntimeError, match="trusted script"):
        b.poll()
    assert b.cli.stat().st_mode & 0o777 == 0o660
    assert "permissions" not in b.codex_settings
    assert not (Path(b.config["codex_home"]) / "rules").exists()
    assert not b.http and not b.native


@pytest.mark.parametrize("kind", ["writable_config", "writable_script"])
def test_control_rule_trusted_paths_cannot_be_replaced_from_state(boundary, kind):
    b = boundary
    state_dir = Path(b.config["state_file"]).parent
    state_dir.parent.mkdir(parents=True, mode=0o700)
    state_dir.mkdir(mode=0o700)
    if kind == "writable_config":
        b.path = state_dir / "monitor.json"
        b.path.write_text(json.dumps(b.config))
        b.path.chmod(0o600)
    else:
        source = state_dir / "trusted-control"
        source.write_text(CLI.read_text())
        source.chmod(0o700)
        b.monkeypatch.setitem(b.code, "__file__", str(source))
    with pytest.raises(RuntimeError, match="trusted.*(state|script|configuration)"):
        b.poll()
    assert "permissions" not in b.codex_settings
    assert not (Path(b.config["codex_home"]) / "rules").exists()
    assert not b.http and not b.native


def concurrent_control_rule_file(boundary, monkeypatch, *, conflicting):
    b = boundary
    directory = Path(b.config["codex_home"]) / "rules"
    name = "codex-session-stats-gitlab-monitor.rules"
    original = os.link
    winning = []
    def race(source, target, **kwargs):
        descriptor = os.open(source, os.O_RDONLY, dir_fd=kwargs["src_dir_fd"])
        with os.fdopen(descriptor, "rb") as stream:
            content = stream.read()
        content = b"another rule\n" if conflicting else content
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600,
                             dir_fd=kwargs["dst_dir_fd"])
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        winning.append(content)
        return original(source, target, **kwargs)
    monkeypatch.setattr(os, "link", race)
    return directory, name, winning


def test_control_rule_publication_preserves_a_matching_concurrent_file(boundary, monkeypatch):
    b = boundary
    directory, name, winning = concurrent_control_rule_file(b, monkeypatch, conflicting=False)
    result = b.call("control_rule", b.config, b.path, install=True)
    assert result["state"] == "configured_on_disk"
    assert result["changed"] is False
    assert len(winning) == 1
    assert (directory / name).read_bytes() == winning[0]
    assert list(directory.iterdir()) == [directory / name]
    assert not b.http and not b.native


def test_control_rule_publication_refuses_a_conflicting_concurrent_file(boundary, monkeypatch):
    b = boundary
    directory, name, winning = concurrent_control_rule_file(b, monkeypatch, conflicting=True)
    with pytest.raises(RuntimeError, match="control rule conflicts"):
        b.call("control_rule", b.config, b.path, install=True)
    assert len(winning) == 1
    assert (directory / name).read_bytes() == winning[0]
    assert list(directory.iterdir()) == [directory / name]
    assert not b.http and not b.native


def test_snapshot_rejects_unmapped_runtime_before_credentials_or_api(boundary, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    b.runtime("00000000-0000-0000-0000-999999999999", "unrelated-turn")
    b.http.clear()
    b.native.clear()
    before = Path(b.config["state_file"]).read_bytes()
    credentials = []
    original = b.code["monitor_credential"]
    def credential(config):
        credentials.append(True)
        return original(config)
    b.monkeypatch.setitem(b.code, "monitor_credential", credential)
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "snapshot", "--mr", "1"])
    assert b.call("main") == 1
    assert "mapped native conversation" in capsys.readouterr().err
    assert not credentials and not b.http and not b.native
    assert Path(b.config["state_file"]).read_bytes() == before
    state.db.close()


def test_snapshot_accepts_mapped_active_runtime_without_state_write(boundary, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    before = Path(b.config["state_file"]).read_bytes()
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "snapshot", "--mr", "1"])
    assert b.call("main") == 0
    assert json.loads(capsys.readouterr().out)["head"] == "a" * 40
    assert Path(b.config["state_file"]).read_bytes() == before
    state.db.close()


def test_private_payload_file_claim_uses_existing_native_provenance(boundary, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    payload = Path(b.config["state_file"]).parent / "claim.json"
    payload.write_text(json.dumps({"attempt_id": attempt["id"], "event_id": attempt["event_id"]}))
    payload.chmod(0o600)
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "claim", "--mr", "1", "--payload-file", str(payload)])
    b.monkeypatch.setattr(sys, "stdin", io.StringIO("not JSON; file must be the selected source"))
    assert b.call("main") == 0
    result = json.loads(capsys.readouterr().out)
    assert result["generation"] == 1
    assert result["owner"]["turn_id"] == attempt["turn_id"]
    assert state.get("mrs", "1")["owner"]["turn_id"] == attempt["turn_id"]
    state.db.close()


@pytest.mark.parametrize("kind", ["outside", "symlink", "insecure", "fifo", "oversize", "multibyte", "hardlink"])
def test_payload_file_rejects_unsafe_input_before_claim(boundary, capsys, kind):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    directory = Path(b.config["state_file"]).parent
    payload = directory / "claim.json"
    data = json.dumps({"attempt_id": attempt["id"], "event_id": attempt["event_id"]})
    if kind == "outside":
        # A same-named valid file inside state makes the parent-path gate
        # independently observable even though the reader uses an anchored dir fd.
        payload.write_text(data)
        payload.chmod(0o600)
        payload = b.path.parent / "claim.json"
    if kind == "fifo":
        os.mkfifo(payload, 0o600)
    elif kind in {"symlink", "hardlink"}:
        target = directory / "target.json"
        target.write_text(data)
        target.chmod(0o600)
        if kind == "symlink":
            payload.symlink_to(target)
        else:
            os.link(target, payload)
    else:
        payload.write_text(" " * 65537 if kind == "oversize" else
            json.dumps({"text": "á" * 40000}, ensure_ascii=False) if kind == "multibyte" else data)
        payload.chmod(0o644 if kind == "insecure" else 0o600)
    before = Path(b.config["state_file"]).read_bytes()
    b.native.clear()
    b.http.clear()
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "claim", "--mr", "1", "--payload-file", str(payload)])
    assert b.call("main") == 1
    assert "payload" in capsys.readouterr().err
    assert state.get("mrs", "1")["owner"] is None
    assert Path(b.config["state_file"]).read_bytes() == before
    assert not b.http and not b.native
    state.db.close()


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


def test_check_only_preflight_does_not_reinstall_a_missing_control_rule(boundary, capsys):
    b = boundary
    b.poll()
    target = Path(b.config["codex_home"]) / "rules/codex-session-stats-gitlab-monitor.rules"
    target.unlink()
    b.native.clear()
    b.http.clear()
    before = copy.deepcopy(b.codex_settings)
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "preflight", "--check-only"])
    assert b.call("main") == 1
    assert "control rule is missing" in capsys.readouterr().err
    assert not target.exists()
    assert b.codex_settings == before
    assert not b.http and not b.native


def test_native_claim_callback_does_not_repair_a_missing_profile(boundary, capsys):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    del b.codex_settings["permissions"]["codex-session-stats-gitlab-monitor"]
    rule = Path(b.config["codex_home"]) / "rules/codex-session-stats-gitlab-monitor.rules"
    rule.unlink()
    before = copy.deepcopy(b.codex_settings)
    b.native.clear()
    b.monkeypatch.setattr(sys, "argv", [str(CLI), "monitor-gitlab", "--config", str(b.path),
        "claim", "--mr", "1"])
    b.monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({
        "attempt_id": attempt["id"], "event_id": attempt["event_id"]})))
    assert b.call("main") == 0
    assert json.loads(capsys.readouterr().out)["generation"] == state.get("mrs", "1")["generation"]
    assert b.codex_settings == before
    assert not rule.exists()
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
    # The question turn must finish before another MR can occupy its slot.
    b.finish(attempt["thread_id"], attempt["turn_id"])
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


def monitor_cli(b, capsys, *arguments):
    b.monkeypatch.setattr(sys, "argv", [str(b.cli), "monitor-gitlab", "--config", str(b.path), *arguments])
    code = b.module["main"]()
    return code, capsys.readouterr()


def test_first_poll_bootstraps_unlisted_empty_chat_in_configured_workspace_once(boundary):
    b = boundary
    target, _ = analysis_config(b.path.parent, b.config)
    workspace = target.parent / "selected workspace"
    workspace.mkdir()
    target.write_text(target.read_text() + 'workspace = "selected workspace"\n')
    b.config = b.call("config", b.path)
    b.mr(created=b.now.isoformat())
    result = b.poll()
    assert result["errors"] == {}
    assert result["dispatch"] == {"1": "submitted"}
    state = b.state()
    record = state.get("mrs", "1")
    starts = [r["params"] for r in b.native if r.get("method") == "thread/start"]
    turns = [r["params"] for r in b.native if r.get("method") == "turn/start"]
    assert len(starts) == len(turns) == 1
    assert starts[0]["cwd"] == str(workspace)
    assert turns[0]["threadId"] == record["thread_id"]
    assert (turns[0]["model"], turns[0]["effort"]) == ("gpt-6.1-sol", "high")
    assert turns[0]["permissions"] == "codex-session-stats-gitlab-monitor"
    assert turns[0]["input"][0]["text"].startswith("Standing task explicitly approved")
    assert "toolOutput" not in turns[0]
    assert state.get("attempts", record["creation_attempt"])["state"] == "accepted"
    assert len([a for a in state.all("attempts") if a["kind"] == "dispatch"]) == 1
    b.poll()
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == 1
    assert len(b.threads) == 1
    inventories = [r["params"] for r in b.native if r.get("method") == "thread/list"]
    # Dispatch and its admission-readiness check both verify the empty-chat exception.
    assert [p["archived"] for p in inventories] == [False, True, False, True]
    assert all(p["modelProviders"] == [] and "appServer" in p["sourceKinds"] for p in inventories)
    state.db.close()


@pytest.mark.parametrize("flag, result_key", [("--hold-check", "hold_check"), ("--verify", "verification_turn_id")])
def test_first_pilot_input_accepts_unlisted_empty_chat(boundary, capsys, flag, result_key):
    b = boundary
    b.mr()
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", flag)
    assert code == 0, output.err
    assert json.loads(output.out)[result_key]
    assert len([r for r in b.native if r.get("method") == "thread/start"]) == 1
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == 1


def empty_dispatch_candidate(b):
    mr = b.mr()
    state = b.state()
    tid = b.call("ensure_thread", b.config, state, mr)
    with state.atomic():
        record = state.get("mrs", "1")
        b.call("add_event", state, record, to_head=record["head"], reason="head")
    return state, tid


@pytest.mark.parametrize("obstacle", ["archived", "ephemeral", "missing_ephemeral", "missing_preview", "nonempty_unlisted",
    "history", "creation_id", "creation_kind", "creation_iid", "creation_thread", "creation_state", "bootstrap"])
def test_empty_dispatch_exception_requires_current_creation_and_unused_nonarchived_metadata(boundary, obstacle):
    b = boundary
    state, tid = empty_dispatch_candidate(b)
    if obstacle == "archived":
        b.threads[tid].update(archived=True, source="appServer", modelProvider="other-provider")
    if obstacle == "ephemeral": b.threads[tid]["ephemeral"] = True
    if obstacle in {"missing_ephemeral", "missing_preview"}:
        field = obstacle.removeprefix("missing_")
        external = b.respond
        def incomplete(method, params):
            response = external(method, params)
            if method == "thread/read":
                response = copy.deepcopy(response)
                response["thread"].pop(field)
            return response
        b.respond = incomplete
    if obstacle == "nonempty_unlisted":
        b.threads[tid]["preview"] = "previous input"
        external = b.respond
        def hidden(method, params):
            if method == "thread/list" and not params["archived"]:
                return {"data": [], "nextCursor": None}
            return external(method, params)
        b.respond = hidden
    if obstacle == "history": b.turns[tid] = [{"id": "used-turn", "status": "completed"}]
    with state.atomic():
        record = state.get("mrs", "1")
        attempt = state.get("attempts", record["creation_attempt"])
        if obstacle == "creation_id": attempt["id"] = b.call("id")
        if obstacle == "creation_kind": attempt["kind"] = "dispatch"
        if obstacle == "creation_iid": attempt["iid"] = 2
        if obstacle == "creation_thread": attempt["thread_id"] = b.call("id")
        if obstacle == "creation_state": attempt["state"] = "uncertain"
        if obstacle == "bootstrap": record["bootstrap_verified"] = True
        state.put("attempts", record["creation_attempt"], attempt)
        state.put("mrs", "1", record)
    before = {bucket: state.all(bucket) for bucket in state.BUCKETS}
    native_before = len(b.native)
    with pytest.raises(RuntimeError, match="archived or absent"):
        b.call("dispatch", b.config, b.path, state, b.api(), 1, b.module["MonitorGate"](b.config))
    assert {bucket: state.all(bucket) for bucket in state.BUCKETS} == before
    assert not [r for r in b.native[native_before:] if r.get("method") in {"thread/start", "thread/resume", "turn/start"}]
    state.db.close()


def test_default_inventory_validation_does_not_accept_empty_metadata_alone(boundary):
    b = boundary
    state, tid = empty_dispatch_candidate(b)
    with pytest.raises(RuntimeError, match="archived or absent"):
        b.call("thread", b.config, tid, active_inventory=True)
    assert not [r for r in b.native if r.get("method") == "turn/start"]
    state.db.close()


@pytest.mark.parametrize("failure, message", [
    ("active_cursor", "invalid native inventory"), ("active_bad_cursor", "invalid native inventory"),
    ("active_cap", "inventory exceeds"), ("archived_cursor", "invalid native inventory"),
    ("archived_cap", "inventory exceeds"), ("history_cap", "history exceeds"),
    ("archived_later_match", "archived or absent"), ("history_cursor", "invalid native history"),
    ("history_data", "invalid native history"),
])
def test_empty_dispatch_requires_complete_native_history_and_both_inventories(boundary, failure, message):
    b = boundary
    state, tid = empty_dispatch_candidate(b)
    b.config["max_history_pages"] = 2
    external = b.respond
    def damaged(method, params):
        if method == "thread/list":
            if not params["archived"]:
                if failure == "active_cursor": return {"data": []}
                if failure == "active_bad_cursor": return {"data": [], "nextCursor": []}
                if failure == "active_cap": return {"data": [], "nextCursor": "more"}
            else:
                if failure == "archived_cursor": return {"data": []}
                if failure == "archived_cap": return {"data": [], "nextCursor": "more-archives"}
                if failure == "archived_later_match":
                    if not params.get("cursor"): return {"data": [], "nextCursor": "next-archive"}
                    return {"data": [b.threads[tid]], "nextCursor": None}
        if method == "thread/turns/list":
            if failure == "history_cursor": return {"data": []}
            if failure == "history_data": return {"data": {}, "nextCursor": None}
            if failure == "history_cap": return {"data": [], "nextCursor": "more-history"}
        return external(method, params)
    b.respond = damaged
    before = {bucket: state.all(bucket) for bucket in state.BUCKETS}
    native_before = len(b.native)
    with pytest.raises(RuntimeError, match=message):
        b.call("dispatch", b.config, b.path, state, b.api(), 1, b.module["MonitorGate"](b.config))
    assert {bucket: state.all(bucket) for bucket in state.BUCKETS} == before
    assert not [r for r in b.native[native_before:] if r.get("method") in {"thread/start", "turn/start"}]
    state.db.close()


@pytest.mark.parametrize("race", [False, True])
def test_empty_creation_recovery_cannot_bind_a_stale_creation_attempt(boundary, race):
    b = boundary
    mr = b.mr()
    state = b.state()
    tid = b.call("ensure_thread", b.config, state, mr)
    record = state.get("mrs", "1")
    attempt = state.get("attempts", record["creation_attempt"])
    replacement = b.call("id")
    with state.atomic():
        record["thread_id"] = None
        if not race: record["creation_attempt"] = replacement
        attempt["state"] = "uncertain"
        state.put("mrs", "1", record)
        state.put("attempts", attempt["id"], attempt)
    external = b.respond
    def changed(method, params):
        response = external(method, params)
        if race and method == "thread/read":
            with state.atomic():
                current = state.get("mrs", "1")
                current["creation_attempt"] = replacement
                state.put("mrs", "1", current)
        return response
    b.respond = changed
    native_before = len(b.native)
    with pytest.raises(RuntimeError, match="creation"):
        b.call("recover", b.config, state, {"attempt_id": attempt["id"], "thread_id": tid})
    assert state.get("mrs", "1")["thread_id"] is None
    assert state.get("mrs", "1")["creation_attempt"] == replacement
    assert state.get("attempts", attempt["id"])["state"] == "uncertain"
    if not race: assert len(b.native) == native_before
    state.db.close()


def workspace_candidate(b, capsys):
    b.mr()
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1")
    assert code == 0, output.err
    state = b.state()
    with state.atomic():
        record = state.get("mrs", "1")
        record.update(generation=4, bootstrap_verified=True, human_continuation_verified=True)
        state.put("mrs", "1", record)
        state.put("events", "1:old-event", {"id": "old-event", "iid": 1, "state": "reviewed",
            "reasons": ["pilot_hold"], "notes": [], "attempt_id": "old-dispatch",
            "from_head": "a" * 40, "to_head": "a" * 40})
        state.put("attempts", "old-dispatch", {"id": "old-dispatch", "iid": 1,
            "kind": "dispatch", "state": "accepted", "thread_id": record["thread_id"],
            "event_id": "old-event", "turn_id": "old-turn", "bootstrap": True,
            "bootstrap_text": "historical standing instructions"})
        state.put("cases", "old-case", {"id": "old-case", "iid": 1, "state": "answered"})
    b.turns[record["thread_id"]] = [{"id": "old-turn", "status": "completed"}]
    b.threads[record["thread_id"]]["preview"] = "historical standing instructions"
    b.items["old-turn"] = [{"type": "userMessage", "content": [
        {"type": "text", "text": "historical standing instructions"}]}]
    raw = b.path.read_bytes()
    target, _ = analysis_config(b.path.parent, b.config)
    b.path.write_bytes(raw)
    new_config = {**b.config, "cwd": str(target.parent / "workspace"), "effort": "high"}
    response = b.call("native", new_config, "thread/start", {
        "cwd": new_config["cwd"], "model": new_config["model"],
        **b.call("permission_selection", new_config)})
    return state, target, response["thread"]["id"]


def adopt_workspace(b, capsys, target, thread_id):
    return monitor_cli(b, capsys, "adopt-workspace", "--analysis-config", str(target),
                       "--mr", "1", "--thread-id", thread_id)


def test_workspace_adoption_cli_preserves_history_restarts_bootstrap_and_is_idempotent(boundary, capsys):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    old = state.get("mrs", "1")
    audit = {bucket: state.all(bucket) for bucket in ["events", "attempts", "cases", "operations", "notes"]}
    native_before = len(b.native)
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 0, output.err
    assert json.loads(output.out)["thread_id"] == tid
    data = json.loads(b.path.read_text())
    assert data["analysis_config"] == str(target)
    assert not set(data) & {"cwd", "model", "effort"}
    current = state.get("mrs", "1")
    assert (current["thread_id"], current["generation"]) == (tid, 5)
    assert current["bootstrap_verified"] is False and current["human_continuation_verified"] is False
    assert current["previous_conversations"][0]["thread_id"] == old["thread_id"]
    assert current["previous_conversations"][0]["human_continuation_verified"] is True
    for bucket in ["events", "cases", "operations", "notes"]:
        assert state.all(bucket) == audit[bucket]
    assert all(state.get("attempts", a["id"]) == a for a in audit["attempts"])
    assert len(state.all("attempts")) == len(audit["attempts"]) + 1
    assert not any(r.get("method") in {"thread/start", "turn/start", "thread/settings/update"}
                   for r in b.native[native_before:])
    with pytest.raises(RuntimeError, match="binding changed"):
        with state.atomic():
            state.put("meta", "stale_callback", True)
    b.config = b.call("config", b.path)
    fresh = b.state()
    with fresh.atomic():
        current.update(bootstrap_verified=True, human_continuation_verified=True, generation=7)
        fresh.put("mrs", "1", current)
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 0, output.err
    assert json.loads(output.out)["changed"] is False
    assert fresh.get("mrs", "1") == current
    assert fresh.get("meta", "workspace_adoption")["state"] == "completed"
    # A future head event receives the standing contract in the new chat, not
    # a tool output inherited from the old conversation's bootstrap proof.
    with fresh.atomic():
        current.update(bootstrap_verified=False, human_continuation_verified=False)
        fresh.put("mrs", "1", current)
        b.call("add_event", fresh, current, to_head=current["head"], reason="head")
    b.call("dispatch", b.config, b.path, fresh, b.api(), 1, b.module["MonitorGate"](b.config))
    request = [r["params"] for r in b.native if r.get("method") == "turn/start"][-1]
    assert request["threadId"] == tid and request["effort"] == "high"
    assert "Standing task explicitly approved" in request["input"][0]["text"]
    assert "toolOutput" not in request
    fresh.db.close()
    state.db.close()


@pytest.mark.parametrize("obstacle, message", [
    ("owner", "owner"), ("hold", "hold"), ("pending", "pending"),
    ("other_chat", "other mapped"), ("effect", "public effects"),
    ("diagnostic", "diagnostic attempts"), ("busy", "idle native"),
    ("diagnostic_accepted", "completed native diagnostic"),
    ("unproved_creation", "conversation/diagnostic attempts"),
    ("unproved_diagnostic", "conversation/diagnostic attempts"),
    ("used", "already has turns"), ("missing_inventory", "archived or absent"),
])
def test_workspace_adoption_refuses_unsafe_candidate_without_cutover(boundary, capsys, obstacle, message):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    with state.atomic():
        current = state.get("mrs", "1")
        if obstacle == "owner": current["owner"] = {"turn_id": "busy-owner"}
        if obstacle == "hold": current["case_id"] = "human-question"
        state.put("mrs", "1", current)
        if obstacle == "pending":
            event = state.get("events", "1:old-event")
            event["state"] = "pending"
            state.put("events", "1:old-event", event)
        if obstacle == "other_chat": state.put("mrs", "2", {"iid": 2, "thread_id": "another-chat"})
        if obstacle == "effect": state.put("operations", "1:uncertain", {"state": "uncertain"})
        if obstacle == "diagnostic": state.put("attempts", "uncertain", {"kind": "pilot_check", "state": "uncertain"})
        if obstacle == "diagnostic_accepted":
            state.put("attempts", "incomplete", {"kind": "pilot_check", "state": "accepted",
                "thread_id": current["thread_id"], "turn_id": "unproved-diagnostic"})
        if obstacle == "unproved_creation":
            identifier = b.call("id")
            state.put("attempts", identifier, {"id": identifier, "kind": "conversation",
                "state": "unstarted", "thread_id": current["thread_id"]})
        if obstacle == "unproved_diagnostic":
            identifier = b.call("id")
            state.put("attempts", identifier, {"id": identifier, "kind": "pilot_check", "state": "unstarted"})
    if obstacle == "busy": b.threads[tid]["status"] = {"type": "active"}
    if obstacle == "used":
        b.threads[tid]["preview"] = "existing user input"
        b.turns[tid] = [{"id": "other-turn", "status": "completed"}]
    if obstacle == "missing_inventory": b.threads[tid]["archived"] = True
    before = b.path.read_bytes(), Path(b.config["state_file"]).read_bytes()
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1 and message in output.err
    assert (b.path.read_bytes(), Path(b.config["state_file"]).read_bytes()) == before
    state.db.close()


def test_workspace_adoption_retains_definitely_deferred_historical_creation(boundary, capsys):
    b = boundary
    state = b.state()
    def defer():
        raise b.module["MonitorDeferred"]("fixture definitely unsubmitted creation")
    with pytest.raises(b.module["MonitorDeferred"]):
        b.call("ensure_thread", {**b.config, "_native_guard": defer}, state, b.mr())
    attempt = state.all("attempts")[0]
    assert attempt["kind"] == "conversation" and attempt["state"] == "unstarted"
    assert state.get("mrs", "1")["creation_attempt"] is None
    assert not b.threads
    prepared, target, tid = workspace_candidate(b, capsys)
    assert prepared.get("mrs", "1")["creation_attempt"] != attempt["id"]
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 0, output.err
    assert prepared.get("attempts", attempt["id"]) == attempt
    prepared.db.close()
    state.db.close()


def test_workspace_adoption_rejects_workspace_symlink_into_writable_state(boundary, capsys):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    workspace = target.parent / "workspace"
    workspace.rmdir()
    workspace.symlink_to(Path(b.config["state_file"]).parent, target_is_directory=True)
    b.threads[tid]["cwd"] = str(workspace.resolve())
    before = b.path.read_bytes(), Path(b.config["state_file"]).read_bytes()
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1 and "outside agent-writable state" in output.err
    assert (b.path.read_bytes(), Path(b.config["state_file"]).read_bytes()) == before
    state.db.close()


def test_workspace_adoption_retains_operator_confirmed_diagnostic_absence(boundary, capsys):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    original = b.respond
    def no_submission(method, params):
        if method == "turn/start": raise TimeoutError("fixture diagnostic not submitted")
        return original(method, params)
    b.respond = no_submission
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--verify")
    assert code == 1
    b.respond = original
    attempt = next(a for a in state.all("attempts") if a["kind"] == "pilot_check")
    assert attempt["state"] == "uncertain" and "turn_id" not in attempt
    code, output = monitor_cli(b, capsys, "recover", "--attempt", attempt["id"],
        "--confirm-no-diagnostic", "--acknowledge-duplicate-risk")
    assert code == 0, output.err
    absent = state.get("attempts", attempt["id"])
    assert absent["state"] == "unstarted" and absent["duplicate_risk_acknowledged"] is True
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 0, output.err
    assert state.get("attempts", attempt["id"]) == absent
    state.db.close()


@pytest.mark.parametrize("phase, receipt_phase", [("prepared", "prepared"), ("bound", "bound"), ("renamed", "bound")])
def test_workspace_adoption_recovers_interrupted_cutover_and_blocks_open_callbacks(boundary, capsys, phase, receipt_phase):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    original_native, original_replace = b.respond, os.replace
    def stopped_native(method, params):
        if (method == "thread/read" and params["threadId"] == tid
                and state.get("meta", "workspace_adoption") is not None):
            raise RuntimeError("fixture native outage after barrier")
        return original_native(method, params)
    def stopped_replace(source, destination):
        if Path(destination) == b.path:
            if phase == "renamed": original_replace(source, destination)
            raise OSError("fixture stopped at config rename")
        return original_replace(source, destination)
    if phase == "prepared": b.respond = stopped_native
    else: b.monkeypatch.setattr(os, "replace", stopped_replace)
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1
    assert state.get("meta", "workspace_adoption")["state"] == receipt_phase
    with pytest.raises(RuntimeError, match="adoption is pending"):
        with state.atomic(): state.put("meta", "stale_callback", True)
    with pytest.raises(RuntimeError): b.state()
    b.respond = original_native
    b.monkeypatch.setattr(os, "replace", original_replace)
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 0, output.err
    assert state.get("meta", "workspace_adoption")["state"] == "completed"
    assert state.get("mrs", "1")["generation"] == 5
    state.db.close()


def test_workspace_adoption_blocks_old_chat_observed_active_after_prepared_barrier(boundary, capsys):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    identity = state.get("meta", "identity")
    old = state.get("mrs", "1")
    raw = b.path.read_bytes()
    external = b.respond
    observed = []
    def activated(method, params):
        response = copy.deepcopy(external(method, params))
        if (method == "thread/read" and params["threadId"] == old["thread_id"]
                and state.get("meta", "workspace_adoption") is not None):
            observed.append(response["thread"]["status"]["type"])
            b.threads[old["thread_id"]]["status"] = {"type": "active"}
        return response
    b.respond = activated
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1 and "idle native" in output.err
    assert observed == ["idle", "active"]
    assert state.get("meta", "workspace_adoption")["state"] == "prepared"
    assert state.get("meta", "identity") == identity
    assert state.get("mrs", "1") == old
    assert b.path.read_bytes() == raw
    assert not [r for r in b.native if r.get("method") == "turn/start"]
    state.db.close()


@pytest.mark.parametrize("change, message", [("base", "configuration changed"),
    ("toml", "configuration changed"), ("busy", "idle native")])
def test_workspace_adoption_pending_recovery_revalidates_inputs(boundary, capsys, change, message):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    original_replace = os.replace
    def stop(source, destination):
        if Path(destination) == b.path: raise OSError("fixture interruption")
        return original_replace(source, destination)
    b.monkeypatch.setattr(os, "replace", stop)
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1
    b.monkeypatch.setattr(os, "replace", original_replace)
    if change == "base":
        data = json.loads(b.path.read_text())
        data["cycle_seconds"] += 1
        b.path.write_text(json.dumps(data))
    if change == "toml": target.write_text('model = "gpt-6.1-sol"\nmodel_reasoning_effort = "low"\n')
    if change == "busy": b.threads[tid]["status"] = {"type": "active"}
    before = b.path.read_bytes()
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1 and message in output.err
    assert b.path.read_bytes() == before
    assert state.get("meta", "workspace_adoption")["state"] == "bound"
    state.db.close()


def test_workspace_adoption_recovery_refuses_receipt_config_injection(boundary, capsys):
    b = boundary
    state, target, tid = workspace_candidate(b, capsys)
    original_replace = os.replace
    def stop(source, destination):
        if Path(destination) == b.path: raise OSError("fixture interruption")
        return original_replace(source, destination)
    b.monkeypatch.setattr(os, "replace", stop)
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1
    b.monkeypatch.setattr(os, "replace", original_replace)
    receipt = state.get("meta", "workspace_adoption")
    injected = json.loads(receipt["new_json"])
    injected["state_file"] = str(b.path.parent / "attacker.sqlite3")
    receipt["new_json"] = json.dumps(injected, ensure_ascii=False, indent=2) + "\n"
    # Simulate a corrupted agent-writable receipt, not a second production writer.
    with state.atomic(workspace_adoption=True): state.put("meta", "workspace_adoption", receipt)
    before = b.path.read_bytes()
    code, output = adopt_workspace(b, capsys, target, tid)
    assert code == 1 and "receipt was altered" in output.err
    assert b.path.read_bytes() == before
    assert state.get("meta", "workspace_adoption")["state"] == "bound"
    state.db.close()


def pilot_control(b, capsys, action, payload):
    target = Path(b.config["state_file"]).parent / "fixture-payload.json"
    target.write_text(json.dumps(payload))
    target.chmod(0o600)
    code, output = monitor_cli(b, capsys, action, "--mr", "1", "--payload-file", str(target))
    assert code == 0, output.err
    return json.loads(output.out)


def recorded_pilot(b, capsys):
    b.mr()
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 0, output.err
    assert json.loads(output.out)["hold_check"] == "submitted"
    state = b.state()
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    return state, attempt


def recover_pilot(b, capsys, attempt):
    b.finish(attempt["thread_id"], attempt["turn_id"])
    code, output = monitor_cli(b, capsys, "recover", "--attempt", attempt["id"], "--acknowledge-duplicate-risk")
    assert code == 0, output.err
    assert json.loads(output.out)["pending"] == attempt["event_id"]


@pytest.mark.parametrize("sunday", [False, True])
def test_recovered_pilot_cli_reuses_event_and_completes_only_real_human_fixture_work(boundary, capsys, sunday):
    b = boundary
    state, original = recorded_pilot(b, capsys)
    tid = original["thread_id"]
    b.runtime(tid, original["turn_id"])
    external = b.respond
    def inaccessible_callback(method, params):
        if method == "thread/read":
            raise PermissionError("fixture callback cannot reach native socket")
        return external(method, params)
    b.respond = inaccessible_callback
    with pytest.raises(RuntimeError, match="transport failed"):
        b.call("claim", b.config, state, 1,
               {"attempt_id": original["id"], "event_id": original["event_id"]})
    assert state.get("mrs", "1")["owner"] is None
    b.respond = external
    recover_pilot(b, capsys, original)
    assert state.get("mrs", "1")["bootstrap_verified"] is True
    if sunday:
        b.now = dt.datetime(2026, 10, 18, 13, tzinfo=dt.timezone.utc)
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 0, output.err
    assert json.loads(output.out)["hold_check"] == "submitted"
    retry = next(a for a in state.all("attempts") if a.get("kind") == "dispatch" and a["state"] == "accepted")
    assert retry["id"] != original["id"] and retry["thread_id"] == tid
    assert retry["event_id"] == original["event_id"] and retry["bootstrap"] is False
    assert len(b.threads) == 1 and len(state.all("events")) == 1
    assert state.get("attempts", original["id"])["state"] == "operator_retried"
    request = [r["params"] for r in b.native if r.get("method") == "turn/start"][-1]
    assert request["input"] == []
    delivered = b.items[retry["turn_id"]]
    assert [i["type"] for i in delivered] == ["functionCallOutput"]
    payload = json.loads(request["toolOutput"]["output"])
    assert payload["attempt_id"] == retry["id"] and payload["event_id"] == original["event_id"]
    instructions = payload["pilot_instructions"]
    for text in (str(b.cli), "--payload-file", str(Path(b.config["state_file"]).parent),
                 retry["id"], original["event_id"], "pause", "resume", "complete",
                 "Do not review code or publish", "0600"):
        assert text in instructions
    assert b.token not in instructions
    b.runtime(tid, retry["turn_id"])
    work = pilot_control(b, capsys, "claim", {"attempt_id": retry["id"], "event_id": retry["event_id"]})
    question = "Para concluir o teste de pausa e retomada deste MR, responda aqui: continuar."
    paused = pilot_control(b, capsys, "pause", {"generation": work["generation"], "question": question})
    b.items[retry["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": question})
    b.finish(tid, retry["turn_id"])
    # A real producer cycle while held discovers ordinary work; the diagnostic
    # human continuation must leave it pending instead of acquiring a review.
    b.now = dt.datetime(2026, 10, 19, 10, tzinfo=dt.timezone.utc)
    b.mrs[1]["sha"] = "b" * 40
    b.poll()
    normal = next(e for e in state.all("events") if e["state"] == "pending")
    assert normal["reasons"] == ["head"]
    human_turn(b, tid, "continuar")
    resumed = pilot_control(b, capsys, "resume", {"case_id": paused["case_id"],
        "expected_generation": paused["generation"], "answer_sufficient": True, "answer_summary": "continuar"})
    assert resumed["owner"]["origin"] == "human"
    assert resumed["owner"]["event_ids"] == [original["event_id"]]
    completed = pilot_control(b, capsys, "complete", {"generation": resumed["generation"],
        "event_ids": [original["event_id"]], "reviewed_head": "a" * 40})
    assert completed["pilot_only"] is True
    record = state.get("mrs", "1")
    assert record["human_continuation_verified"] is True and record["owner"] is None
    assert "reviewed_head" not in record and record["head"] == "b" * 40
    assert state.get("events", "1:" + normal["id"])["state"] == "pending"
    assert state.get("events", "1:" + original["event_id"])["state"] == "reviewed"
    assert state.all("operations") == []
    state.db.close()


@pytest.mark.parametrize("after_resend", [False, True])
def test_recovery_cli_rejects_repeated_or_stale_attempt_without_mutation(boundary, capsys, after_resend):
    b = boundary
    state, original = recorded_pilot(b, capsys)
    recover_pilot(b, capsys, original)
    if after_resend:
        b.poll()
        current = next(a for a in state.all("attempts") if a.get("kind") == "dispatch" and a["state"] == "accepted")
        b.finish(current["thread_id"], current["turn_id"])
    before = Path(b.config["state_file"]).read_bytes()
    code, output = monitor_cli(b, capsys, "recover", "--attempt", original["id"], "--acknowledge-duplicate-risk")
    assert code == 1 and output.err
    assert Path(b.config["state_file"]).read_bytes() == before
    if after_resend:
        recover_pilot(b, capsys, current)
        assert state.get("events", "1:" + original["event_id"])["state"] == "pending"
    state.db.close()


def test_recovery_revalidates_current_attempt_after_native_inspection(boundary, capsys):
    b = boundary
    state, original = recorded_pilot(b, capsys)
    b.finish(original["thread_id"], original["turn_id"])
    external = b.respond
    raced = []
    def changed_during_inspection(method, params):
        result = external(method, params)
        if method == "thread/read" and not raced:
            with state.atomic():
                event = state.get("events", "1:" + original["event_id"])
                event["attempt_id"] = "different-current-attempt"
                state.put("events", "1:" + event["id"], event)
            raced.append(True)
        return result
    b.respond = changed_during_inspection
    code, output = monitor_cli(b, capsys, "recover", "--attempt", original["id"], "--acknowledge-duplicate-risk")
    assert code == 1 and "current" in output.err and raced == [True]
    assert state.get("events", "1:" + original["event_id"])["state"] == "accepted"
    assert state.get("events", "1:" + original["event_id"])["attempt_id"] == "different-current-attempt"
    assert state.get("attempts", original["id"])["state"] == "accepted"
    assert state.get("mrs", "1")["generation"] == 0
    state.db.close()


@pytest.mark.parametrize("obstacle", ["unrecovered", "missing_ack", "wrong_event", "wrong_thread", "wrong_iid",
    "wrong_pointer", "mixed", "ordinary_pending", "uncertain_effect", "hold", "owner", "busy", "changed_head",
    "unstarted_with_turn"])
def test_pilot_cli_rejects_ineligible_retry_without_new_event_or_turn(boundary, capsys, obstacle):
    b = boundary
    state, original = recorded_pilot(b, capsys)
    b.finish(original["thread_id"], original["turn_id"])
    if obstacle != "unrecovered":
        recover_pilot(b, capsys, original)
    with state.atomic():
        record = state.get("mrs", "1")
        event = state.get("events", "1:" + original["event_id"])
        attempt = state.get("attempts", original["id"])
        if obstacle == "missing_ack": attempt.pop("duplicate_risk_acknowledged")
        if obstacle == "wrong_event": attempt["event_id"] = b.call("id")
        if obstacle == "wrong_thread": attempt["thread_id"] = "00000000-0000-0000-0000-999999999999"
        if obstacle == "wrong_iid": attempt["iid"] = 2
        if obstacle == "unstarted_with_turn": attempt["state"] = "unstarted"
        if obstacle == "wrong_pointer": event["attempt_id"] = b.call("id")
        if obstacle == "mixed": event["reasons"] = ["head", "pilot_hold"]
        if obstacle == "ordinary_pending":
            ordinary = {**copy.deepcopy(event), "id": b.call("id"), "reasons": ["head"]}
            state.put("events", "1:" + ordinary["id"], ordinary)
        if obstacle == "uncertain_effect":
            state.put("operations", "1:prior", {"id": "prior", "iid": 1, "state": "uncertain"})
        if obstacle == "hold": record["case_id"] = "held-case"
        if obstacle == "owner": record["owner"] = {"turn_id": "existing-owner"}
        state.put("mrs", "1", record)
        state.put("events", "1:" + event["id"], event)
        state.put("attempts", attempt["id"], attempt)
    if obstacle == "busy": b.threads[original["thread_id"]]["status"] = {"type": "active"}
    if obstacle == "changed_head": b.mrs[1]["sha"] = "b" * 40
    before = Path(b.config["state_file"]).read_bytes()
    turns_before = len([r for r in b.native if r.get("method") == "turn/start"])
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 1 and output.err
    assert Path(b.config["state_file"]).read_bytes() == before
    assert len([r for r in b.native if r.get("method") == "turn/start"]) == turns_before
    state.db.close()


def test_recorded_unstarted_pilot_reuses_event_without_duplicate_recovery(boundary, capsys, monkeypatch):
    import time
    b = boundary
    b.mr()
    state = b.state()
    original_clock = time.monotonic
    # Cross the real gate's deadline only after the producer commits an intent,
    # before it can submit turn/start. Keep guard/orchestration code unchanged.
    def expire_after_intent():
        return b.config["cycle_seconds"] + 1 if any(
            a.get("kind") == "dispatch" and a["state"] == "attempting"
            for a in state.all("attempts")) else 0
    monkeypatch.setattr(time, "monotonic", expire_after_intent)
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 1 and "global_cycle_budget" in output.err
    attempt = next(a for a in state.all("attempts") if a.get("kind") == "dispatch")
    assert attempt["state"] == "unstarted" and "turn_id" not in attempt
    assert not [r for r in b.native if r.get("method") == "turn/start"]
    monkeypatch.setattr(time, "monotonic", original_clock)
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 0 and json.loads(output.out)["hold_check"] == "submitted", output.err
    current = next(a for a in state.all("attempts") if a.get("kind") == "dispatch" and a["state"] == "accepted")
    assert current["id"] != attempt["id"] and current["event_id"] == attempt["event_id"]
    assert len(state.all("events")) == 1 and len(b.threads) == 1
    state.db.close()


def test_manual_pilot_sunday_preserves_automatic_window_and_unstarted_event(boundary, capsys):
    b = boundary
    b.mr()
    b.now = dt.datetime(2026, 10, 18, 13, tzinfo=dt.timezone.utc)
    calls = [0]
    def busy_after_creation(route):
        if route == "/projects/42/merge_requests/1":
            calls[0] += 1
            if calls[0] == 2:
                next(iter(b.threads.values()))["status"] = {"type": "active"}
    b.after_http = busy_after_creation
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 0, output.err
    assert json.loads(output.out)["hold_check"] == "native_busy"
    state = b.state()
    event = state.all("events")[0]
    assert event["state"] == "pending" and "attempt_id" not in event
    assert not [a for a in state.all("attempts") if a.get("kind") == "dispatch"]
    b.after_http = None
    next(iter(b.threads.values()))["status"] = {"type": "idle"}
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 0 and json.loads(output.out)["hold_check"] == "submitted", output.err
    assert [e["id"] for e in state.all("events")] == [event["id"]]
    before = Path(b.config["state_file"]).read_bytes()
    b.http.clear(); b.native.clear()
    assert b.poll() == {"skipped": "outside_window", "mutated": False}
    assert not b.http and not b.native and Path(b.config["state_file"]).read_bytes() == before
    state.db.close()


@pytest.mark.parametrize("origin", ["automatic", "human"])
def test_pilot_owner_cannot_register_public_effect(boundary, capsys, origin):
    b = boundary
    state, attempt = recorded_pilot(b, capsys)
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    work = b.call("claim", b.config, state, 1, {"attempt_id": attempt["id"], "event_id": attempt["event_id"]})
    if origin == "human":
        question = "Continuar o teste."
        paused = b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": question})
        b.items[attempt["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": question})
        b.finish(attempt["thread_id"], attempt["turn_id"])
        human_turn(b, attempt["thread_id"], "continuar")
        work = b.call("resume", b.config, state, 1, {"case_id": paused["case_id"],
            "expected_generation": paused["generation"], "answer_sufficient": True, "answer_summary": "continuar"})
    snapshot = b.call("snapshot", b.config, b.api(), 1)
    b.http.clear(); b.native.clear()
    with pytest.raises(RuntimeError, match="pilot.*public"):
        b.call("effect_intent", b.config, state, b.api(), 1,
            {"generation": work["generation"], "kind": "finding", "key": "forbidden", "body": "no publication",
             "head": snapshot["head"], "snapshot": snapshot["fingerprint"]})
    assert state.all("operations") == [] and not b.http
    assert not [r for r in b.native if r.get("method") == "mcpServer/tool/call"]
    state.db.close()


def test_pilot_budget_covers_entry_http_before_provisioning(boundary, monkeypatch, capsys):
    b = boundary
    b.mr()
    elapsed = [0]
    monkeypatch.setattr("time.monotonic", lambda: elapsed[0])
    b.after_http = lambda route: elapsed.__setitem__(0, b.config["cycle_seconds"] + 1)
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 1 and "global_cycle_budget" in output.err
    assert [urlsplit(r.full_url).path for r in b.http] == ["/api/v4/user"]
    assert not b.native and not Path(b.config["state_file"]).exists()


def test_pilot_budget_also_guards_native_provisioning(boundary, monkeypatch, capsys):
    b = boundary
    b.mr()
    elapsed = [0]
    monkeypatch.setattr("time.monotonic", lambda: elapsed[0])
    external = b.respond
    def exhaust_native_budget(method, params):
        result = external(method, params)
        if method == "config/read":
            elapsed[0] = b.config["cycle_seconds"] + 1
        return result
    b.respond = exhaust_native_budget
    code, output = monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check")
    assert code == 1 and "global_cycle_budget" in output.err
    assert [r["method"] for r in b.native if r.get("id") == 2] == ["config/read"]
    assert "permissions" not in b.codex_settings and not Path(b.config["state_file"]).exists()


def test_manual_gate_cannot_dispatch_ordinary_work_and_default_dispatch_refuses_mixed_pilot(boundary, capsys):
    b = boundary
    state, attempt = recorded_pilot(b, capsys)
    recover_pilot(b, capsys, attempt)
    b.http.clear(); b.native.clear()
    gate = b.module["MonitorGate"](b.config, manual_pilot=True)
    with pytest.raises(RuntimeError, match="manual pilot gate"):
        b.call("dispatch", b.config, b.path, state, b.api(), 1, gate)
    assert not b.http and not b.native
    with state.atomic():
        event = state.get("events", "1:" + attempt["event_id"])
        event["reasons"] = ["head", "pilot_hold"]
        state.put("events", "1:" + event["id"], event)
    with pytest.raises(RuntimeError, match="mixed pilot"):
        b.call("dispatch", b.config, b.path, state, b.api(), 1, b.module["MonitorGate"](b.config))
    assert not b.http and not b.native
    assert state.get("events", "1:" + event["id"])["state"] == "pending"
    state.db.close()


@pytest.mark.parametrize("other", ["--verify", "--diagnose-socket"])
def test_pilot_diagnostic_flags_are_exclusive_before_effects(boundary, capsys, other):
    b = boundary
    with pytest.raises(SystemExit) as error:
        monitor_cli(b, capsys, "pilot", "--mr", "1", "--hold-check", other)
    assert error.value.code == 2
    assert not b.http and not b.native and not Path(b.config["state_file"]).exists()


@pytest.mark.parametrize("queued_recovery", [False, True])
def test_resolution_context_change_can_be_disposed_only_by_exact_native_user_case(boundary, queued_recovery):
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
    if queued_recovery:
        b.mr(iid=2, created=b.now.isoformat())
        b.poll()
        competing = next(a for a in queue_attempts(b) if a["iid"] == 2)
    human = human_turn(b, attempt["thread_id"], "Aceito o encerramento observado; analise o novo contexto")
    answer = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
              "answer_sufficient": True, "answer_summary": "User accepted this observed outcome",
              "accept_observed_resolution": "wrong-operation"}
    with pytest.raises(RuntimeError, match="exact case"):
        b.call("resume", b.config, state, 1, answer)
    assert state.get("mrs", "1")["case_id"] == paused["case_id"]
    answer["accept_observed_resolution"] = op["id"]
    b.now = dt.datetime(2026, 10, 18, 2, tzinfo=dt.timezone.utc)
    resumed = b.call("resume", b.config, state, 1, answer)
    if queued_recovery:
        assert resumed["queued"] and state.get("mrs", "1")["owner"] is None
        b.finish(attempt["thread_id"], human)
        b.finish(competing["thread_id"], competing["turn_id"])
        b.now = dt.datetime(2026, 10, 19, 13, tzinfo=dt.timezone.utc)
        b.poll()
        continuation = next(a for a in queue_attempts(b) if a.get("continuation"))
        b.runtime(continuation["thread_id"], continuation["turn_id"])
        resumed = b.call("claim", b.config, state, 1, {"attempt_id": continuation["id"], "event_id": continuation["event_id"]})
        before_recovery = copy.deepcopy(resumed["operations"])
        assert {o["id"] for o in before_recovery} == {explanation["id"], op["id"]}
        decision = next(o for o in before_recovery if o["id"] == op["id"])
        assert decision["context_decision_turn"] == human
        assert decision["context_accepted_by_case"] == paused["case_id"]
        b.finish(continuation["thread_id"], continuation["turn_id"])
        b.call("operator_recovery", b.config, state, 1, {"owner_turn": continuation["turn_id"]})
        b.poll()
        retried = next(a for a in queue_attempts(b) if a.get("continuation") and a["id"] != continuation["id"])
        assert retried["continuation"] == continuation["continuation"]
        b.runtime(retried["thread_id"], retried["turn_id"])
        resumed = b.call("claim", b.config, state, 1, {"attempt_id": retried["id"], "event_id": retried["event_id"]})
        assert resumed["operations"] == before_recovery
    receipt = state.get("operations", f"1:{op['id']}")
    assert receipt["state"] == "confirmed" and receipt["context_accepted_by_case"] == paused["case_id"]
    assert receipt["snapshot"] != receipt["observed_snapshot"] or receipt["head"] != receipt["observed_head"]
    b.call("complete", b.config, state, 1, {"generation": resumed["generation"],
        "event_ids": resumed["owner"]["event_ids"], "reviewed_head": "b" * 40})
    assert state.get("mrs", "1")["reviewed_head"] == "b" * 40


# Production entrypoints and SQLite keep these tests independent of queue internals.
def test_root_toml_migration_moves_complete_groups_and_preserves_identity(tmp_path):
    config = configure(tmp_path)
    target, base = analysis_config(tmp_path, config)
    result = run_monitor(tmp_path, "migrate-config")
    assert result.returncode == 0, result.stderr
    settings = tomllib.loads(target.read_text())
    keys = {"gitlab_url", "project_path", "project_id", "timezone", "weekdays", "open_hour", "close_hour", "interval_minutes"}
    assert {k: settings[k] for k in keys} == {k: config[k] for k in keys}
    assert settings["parallel"] == 1
    remaining = json.loads((tmp_path / "monitor.json").read_text())
    assert remaining == {k: v for k, v in base.items() if k not in keys}
    assert target.stat().st_mode & 0o777 == 0o600
    loaded = runpy.run_path(str(CLI))["monitor_config"](tmp_path / "monitor.json")
    assert loaded["parallel"] == 1 and loaded["project_id"] == config["project_id"]
    before = (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())
    assert run_monitor(tmp_path, "migrate-config").returncode == 0
    assert before == (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())


@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5])
def test_root_toml_parallel_rejects_nonpositive_or_noninteger(tmp_path, value):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    with target.open("a") as stream:
        stream.write("parallel = " + json.dumps(value) + "\n")
    result = run_monitor(tmp_path, "status")
    assert result.returncode == 1 and "positive integer" in result.stderr


@pytest.mark.parametrize("kind", ["partial", "duplicate", "mismatch", "bad-hours", "symlink"])
def test_root_toml_migration_refuses_unsafe_transfer_without_writes(tmp_path, kind):
    config = configure(tmp_path)
    target, data = analysis_config(tmp_path, config)
    if kind == "partial":
        target.write_text(target.read_text() + 'project_id = 42\n')
    elif kind in {"duplicate", "mismatch"}:
        target.write_text(target.read_text() + 'gitlab_url = "https://gitlab.example.test"\nproject_path = "engineering/project"\nproject_id = ' + ("42" if kind == "duplicate" else "43") + '\n')
    elif kind == "bad-hours":
        data["close_hour"] = 1
        (tmp_path / "monitor.json").write_text(json.dumps(data))
    else:
        real = target.with_suffix(".real")
        target.rename(real)
        target.symlink_to(real)
    before = (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())
    if kind == "duplicate":
        assert run_monitor(tmp_path, "status").returncode == 1
        assert run_monitor(tmp_path, "migrate-config").returncode == 0
        return
    result = run_monitor(tmp_path, "migrate-config")
    assert result.returncode == 1, result.stdout
    assert before == (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())


@pytest.mark.parametrize("concurrent_edit", [False, True])
def test_root_toml_migration_recovers_only_exact_interrupted_files(tmp_path, monkeypatch, concurrent_edit):
    config = configure(tmp_path)
    target, _ = analysis_config(tmp_path, config)
    module = runpy.run_path(str(CLI))
    original = os.replace
    def interrupted(source, destination):
        if Path(destination) == tmp_path / "monitor.json":
            raise OSError("fixture power failure after TOML publication")
        return original(source, destination)
    monkeypatch.setattr(os, "replace", interrupted)
    with pytest.raises(OSError, match="power failure"):
        module["monitor_migrate_config"](tmp_path / "monitor.json")
    assert "project_id" in tomllib.loads(target.read_text())
    assert run_monitor(tmp_path, "status").returncode == 1
    if concurrent_edit:
        target.write_text(target.read_text() + "# unrelated editor change\n")
    monkeypatch.setattr(os, "replace", original)
    before = (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())
    result = run_monitor(tmp_path, "migrate-config")
    assert result.returncode == (1 if concurrent_edit else 0), result.stderr
    if concurrent_edit:
        assert before == (target.read_bytes(), (tmp_path / "monitor.json").read_bytes())


def queue_attempts(b):
    return [a for a in b.state().all("attempts") if a.get("kind") == "dispatch"]


def queue_complete(b, state, attempt, work):
    b.runtime(attempt["thread_id"], attempt["turn_id"])
    return b.call("complete", b.config, state, attempt["iid"], {
        "generation": work["generation"], "event_ids": work["owner"]["event_ids"],
        "reviewed_head": max(work["events"], key=lambda e: e["last_sequence"])["to_head"]})


def test_review_queue_serializes_native_tail_and_advances_between_inventory_scans(boundary):
    b = boundary
    for iid in (1, 2, 3):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll(scheduled=True)
    assert len(queue_attempts(b)) == 1
    state, first, work = b.active_claim()
    queue_complete(b, state, first, work)
    scans = len([r for r in b.http if urlsplit(r.full_url).path.endswith("/merge_requests")])
    b.now += dt.timedelta(minutes=1)
    b.poll(scheduled=True)
    assert len(queue_attempts(b)) == 1
    b.finish(first["thread_id"], first["turn_id"])
    b.now += dt.timedelta(minutes=1)
    result = b.poll(scheduled=True)
    assert result["inventory_due"] is False
    assert len(queue_attempts(b)) == 2
    assert len([r for r in b.http if urlsplit(r.full_url).path.endswith("/merge_requests")]) == scans
    assert [a["iid"] for a in sorted(queue_attempts(b), key=lambda a: a["created_at"])] == [1, 2]
    assert sum(r["state"] == "active" for r in b.call("queue", state)) == 1


@pytest.mark.parametrize("status", ["failed", "interrupted", "completed"])
def test_review_queue_terminal_without_complete_requires_recovery_and_rejects_late_claim(boundary, status):
    b = boundary
    for iid in (1, 2):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll()
    state = b.state()
    first = queue_attempts(b)[0]
    b.finish(first["thread_id"], first["turn_id"])
    b.turns[first["thread_id"]][0]["status"] = status
    b.poll()
    assert len(queue_attempts(b)) == 2
    assert state.get("mrs", "1")["recovery_required"]
    assert state.get("events", "1:" + first["event_id"])["state"] != "reviewed"
    b.runtime(first["thread_id"], first["turn_id"])
    with pytest.raises(RuntimeError, match="stale|closed"):
        b.call("claim", b.config, state, 1, {"attempt_id": first["id"], "event_id": first["event_id"]})


def test_review_queue_missing_native_evidence_and_lowered_capacity_never_release_slots(boundary):
    b = boundary
    b.config["parallel"] = 2
    for iid in (1, 2, 3):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll()
    assert len(queue_attempts(b)) == 2
    b.config["parallel"] = 1
    first = queue_attempts(b)[0]
    b.turns[first["thread_id"]] = []
    b.poll()
    assert len(queue_attempts(b)) == 2
    assert sum(r["state"] == "active" for r in b.call("queue", b.state())) == 2


def test_review_queue_coalescing_retains_fifo_across_connections_and_skips_busy(boundary):
    b = boundary
    for iid in (1, 2, 3):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll()
    state, first, work = b.active_claim()
    before = next(r for r in b.call("queue", state) if r["iid"] == 2)
    b.mrs[2]["sha"] = "b" * 40
    b.poll()
    assert next(r for r in b.call("queue", b.state()) if r["iid"] == 2)["sequence"] == before["sequence"]
    thread = b.call("ensure_thread", b.config, state, b.mrs[2])
    b.threads[thread]["status"] = {"type": "active"}
    queue_complete(b, state, first, work)
    b.finish(first["thread_id"], first["turn_id"])
    b.poll()
    assert {a["iid"] for a in queue_attempts(b)} == {1, 3}
    assert next(r for r in b.call("queue", state) if r["iid"] == 2)["state"] == "queued"


def queue_hold(b):
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    paused = b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": "Qual comportamento esperado?"})
    b.items[attempt["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": paused["question"]})
    b.finish(attempt["thread_id"], attempt["turn_id"])
    return state, attempt, paused


def test_review_queue_queues_real_answer_and_later_claims_complete_bundle(boundary):
    b = boundary
    state, original, paused = queue_hold(b)
    b.mr(iid=2, created=b.now.isoformat())
    b.mrs[1]["sha"] = "b" * 40
    b.note()
    b.poll()
    second = next(a for a in queue_attempts(b) if a["iid"] == 2)
    human = human_turn(b, original["thread_id"], "Use o comportamento descrito")
    payload = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
               "answer_sufficient": True, "answer_summary": "Use the described behavior"}
    queued = b.call("resume", b.config, state, 1, payload)
    assert queued["queued"] is True and "End this turn" in queued["instructions"]
    assert state.get("mrs", "1")["owner"] is None
    assert b.call("resume", b.config, state, 1, payload) == queued
    with pytest.raises(RuntimeError, match="ownership"):
        b.call("complete", b.config, state, 1, {"generation": state.get("mrs", "1")["generation"]})
    b.runtime(second["thread_id"], second["turn_id"])
    second_work = b.call("claim", b.config, state, 2, {"attempt_id": second["id"], "event_id": second["event_id"]})
    queue_complete(b, state, second, second_work)
    b.finish(second["thread_id"], second["turn_id"])
    b.poll()
    assert len(queue_attempts(b)) == 2
    b.finish(original["thread_id"], human)
    b.poll()
    continuation = next(a for a in queue_attempts(b) if a.get("continuation"))
    assert continuation["bootstrap"] is False and len(continuation["event_ids"]) == 2
    assert continuation["continuation"]["answer_turn"] == human
    b.runtime(continuation["thread_id"], continuation["turn_id"])
    work = b.call("claim", b.config, state, 1, {"attempt_id": continuation["id"], "event_id": continuation["event_id"]})
    assert work["owner"]["origin"] == "automatic" and work["owner"]["case_id"] == paused["case_id"]
    assert set(work["owner"]["event_ids"]) == set(continuation["event_ids"])
    queue_complete(b, state, continuation, work)
    assert all(e["state"] == "reviewed" for e in state.all("events", "1:") if e["id"] in continuation["event_ids"])


def test_review_queue_failed_scan_consumes_cadence_and_outside_window_is_readonly(boundary):
    b = boundary
    b.mr()
    b.note()
    b.fail_page = 1
    b.poll(scheduled=True)
    scans = len([r for r in b.http if urlsplit(r.full_url).path.endswith("/merge_requests")])
    b.now += dt.timedelta(minutes=1)
    b.poll(scheduled=True)
    assert len([r for r in b.http if urlsplit(r.full_url).path.endswith("/merge_requests")]) == scans
    b.now += dt.timedelta(minutes=15)
    b.poll(scheduled=True)
    assert len([r for r in b.http if urlsplit(r.full_url).path.endswith("/merge_requests")]) == scans + 1
    b.now = b.now.replace(hour=2)
    before = Path(b.config["state_file"]).read_bytes()
    result = b.poll(scheduled=True)
    assert result["skipped"] == "outside_window"
    assert Path(b.config["state_file"]).read_bytes() == before


def test_review_queue_atomic_reservations_from_two_real_connections(boundary):
    import concurrent.futures
    import threading
    b = boundary
    state = b.state()
    for iid in (1, 2):
        mr = b.mr(iid=iid, created=b.now.isoformat())
        b.call("observe_mr", state, b.api(), mr)
    ready = b.call("queue_ready", b.config, state)
    request = b.call("queue", state)[0]
    barrier = threading.Barrier(2)
    def compete():
        connection = b.state()
        barrier.wait(timeout=5)
        with connection.atomic():
            admitted = b.call("reserve", b.config, connection, request["id"], ready,
                              thread_id="native-thread", turn_id="native-turn", generation=0)
        connection.db.close()
        return bool(admitted)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: compete(), range(2)))
    assert sorted(results) == [False, True]
    assert sum(r["state"] == "active" for r in b.call("queue", state)) == 1


def test_review_queue_revalidates_skipped_ticket_before_fifo_admission(boundary):
    b = boundary
    state = b.state()
    for iid in (1, 2):
        b.call("observe_mr", state, b.api(), b.mr(iid=iid, created=b.now.isoformat()))
    with state.atomic():
        record = state.get("mrs", "1")
        record["case_id"] = "held-fixture"
        state.put("mrs", "1", record)
    ready = b.call("queue_ready", b.config, state)
    second = b.call("queue", state)[1]
    other = b.state()
    with other.atomic():
        record = other.get("mrs", "1")
        record["case_id"] = None
        other.put("mrs", "1", record)
    with state.atomic():
        assert b.call("reserve", b.config, state, second["id"], ready, generation=0) is None
    assert not any(r["state"] == "active" for r in b.call("queue", state))


def test_review_queue_backfill_counts_active_legacy_but_not_completed_history(boundary):
    b = boundary
    for iid in (1, 2):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll()
    state, first, work = b.active_claim()
    with state.atomic():
        state.db.execute("DELETE FROM meta WHERE key LIKE 'review_request:%'")
    b.call("queue_reconcile", b.config, state)
    assert sum(r["state"] == "active" for r in b.call("queue", state)) == 1
    queue_complete(b, state, first, work)
    b.finish(first["thread_id"], first["turn_id"])
    # Model the historical paused automatic attempt after human completion.
    with state.atomic():
        attempt = state.get("attempts", first["id"])
        attempt["state"] = "claimed"
        state.put("attempts", first["id"], attempt)
        state.db.execute("DELETE FROM meta WHERE key LIKE 'review_request:%'")
    b.call("queue_reconcile", b.config, state)
    assert not any(r["state"] == "active" for r in b.call("queue", state))
    assert state.get("mrs", "1").get("recovery_required") is None


@pytest.mark.parametrize("forgery", ["question", "mixed", "changed-answer"])
def test_review_queue_never_dispatches_without_unchanged_actual_answer(boundary, forgery):
    b = boundary
    state, original, paused = queue_hold(b)
    b.mr(iid=2, created=b.now.isoformat())
    b.poll()
    human = human_turn(b, original["thread_id"], "continuar")
    if forgery == "question":
        b.items[human][0]["content"][0]["text"] = "Continuar?"
    elif forgery == "mixed":
        b.items[human].append({"type": "userMessage", "content": [{"type": "text", "text": original["bootstrap_text"]}]})
    payload = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
               "answer_sufficient": True, "answer_summary": "continuar"}
    if forgery != "changed-answer":
        with pytest.raises(RuntimeError, match="question-only|automation"):
            b.call("resume", b.config, state, 1, payload)
        assert state.get("mrs", "1")["case_id"] == paused["case_id"]
        return
    assert b.call("resume", b.config, state, 1, payload)["queued"]
    b.items[human][0]["content"][0]["text"] = "different later input"
    b.finish(original["thread_id"], human)
    second = next(a for a in queue_attempts(b) if a["iid"] == 2)
    b.finish(second["thread_id"], second["turn_id"])
    b.poll()
    assert not any(a.get("continuation") for a in queue_attempts(b))


def test_review_queue_recovery_keeps_full_answered_event_bundle(boundary):
    b = boundary
    state, original, paused = queue_hold(b)
    b.mr(iid=2, created=b.now.isoformat())
    b.mrs[1]["sha"] = "b" * 40
    b.note()
    b.poll()
    human = human_turn(b, original["thread_id"], "continuar")
    payload = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
               "answer_sufficient": True, "answer_summary": "continuar"}
    assert b.call("resume", b.config, state, 1, payload)["queued"]
    b.finish(original["thread_id"], human)
    second = next(a for a in queue_attempts(b) if a["iid"] == 2)
    b.finish(second["thread_id"], second["turn_id"])
    b.poll()
    continuation = next(a for a in queue_attempts(b) if a.get("continuation"))
    b.runtime(continuation["thread_id"], continuation["turn_id"])
    work = b.call("claim", b.config, state, 1, {"attempt_id": continuation["id"], "event_id": continuation["event_id"]})
    b.finish(continuation["thread_id"], continuation["turn_id"])
    b.call("operator_recovery", b.config, state, 1, {"owner_turn": continuation["turn_id"]})
    b.poll()
    retried = next(a for a in queue_attempts(b) if a.get("continuation") and a["id"] != continuation["id"])
    assert retried["continuation"] == continuation["continuation"]
    assert set(retried["event_ids"]) == set(work["owner"]["event_ids"])
    assert state.get("cases", paused["case_id"])["answer_turn"] == human


@pytest.mark.parametrize("unavailable", ["archived", "uncertain-creation"])
def test_review_queue_unavailable_head_does_not_block_other_mrs(boundary, unavailable):
    b = boundary
    state = b.state()
    for iid in (1, 2):
        b.call("observe_mr", state, b.api(), b.mr(iid=iid, created=b.now.isoformat()))
    if unavailable == "archived":
        tid = b.call("ensure_thread", b.config, state, b.mrs[1])
        b.threads[tid]["archived"] = True
    else:
        external = b.respond
        def lost_creation(method, params):
            result = external(method, params)
            if method == "thread/start":
                raise TimeoutError("fixture lost creation acknowledgement")
            return result
        b.respond = lost_creation
        with pytest.raises(RuntimeError, match="transport failed"):
            b.call("ensure_thread", b.config, state, b.mrs[1])
        b.respond = external
    b.poll()
    assert [a["iid"] for a in queue_attempts(b)] == [2]
    assert next(r for r in b.call("queue", state) if r["iid"] == 1)["state"] == "queued"


def test_review_queue_legacy_complete_before_first_backfill_retains_native_tail(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, first, work = b.active_claim()
    with state.atomic():
        state.db.execute("DELETE FROM meta WHERE key LIKE 'review_request:%'")
    queue_complete(b, state, first, work)
    b.mr(iid=2, created=b.now.isoformat())
    b.poll()
    assert len(queue_attempts(b)) == 1
    b.finish(first["thread_id"], first["turn_id"])
    b.poll()
    assert len(queue_attempts(b)) == 2


def test_review_queue_mixed_terminal_releases_slot_and_requeues_registered_work(boundary):
    b = boundary
    b.mr(created=b.now.isoformat())
    b.poll()
    state, first, work = b.active_claim()
    queue_complete(b, state, first, work)
    b.finish(first["thread_id"], first["turn_id"])
    b.note()
    b.poll()
    mixed = next(a for a in queue_attempts(b) if a["state"] == "accepted")
    b.items[mixed["turn_id"]].append({"type": "userMessage", "content": [{"type": "text", "text": "Human request"}]})
    b.finish(mixed["thread_id"], mixed["turn_id"])
    b.call("reconcile", b.config, state, 1)
    b.mr(iid=2, created=b.now.isoformat())
    b.poll()
    assert len(queue_attempts(b)) == 3
    assert state.get("attempts", mixed["id"])["state"] == "mixed_deferred"
    assert sum(r["state"] == "active" for r in b.call("queue", state)) == 1


def test_review_queue_continuation_survives_late_own_note_suppression(boundary):
    b = boundary
    b.mr()
    b.poll()
    b.note()
    b.poll()
    state, first, work = b.active_claim()
    assert work["events"][0]["reasons"] == ["comment"]
    snap = b.call("snapshot", b.config, b.api(), 1)
    publication = b.call("effect_intent", b.config, state, b.api(), 1, {
        "generation": work["generation"], "head": "a" * 40, "snapshot": snap["fingerprint"],
        "kind": "finding", "key": "late-receipt", "body": "Concrete finding"})
    paused = b.call("pause", b.config, state, 1, {"generation": work["generation"], "question": "Qual comportamento?"})
    b.items[first["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": paused["question"]})
    b.finish(first["thread_id"], first["turn_id"])
    b.mr(iid=2, created=b.now.isoformat())
    b.mrs[1]["sha"] = "b" * 40
    b.poll()
    human = human_turn(b, first["thread_id"], "continuar")
    assert b.call("resume", b.config, state, 1, {"case_id": paused["case_id"],
        "expected_generation": paused["generation"], "answer_sufficient": True, "answer_summary": "continuar"})["queued"]
    # Authenticated provider visibility confirms a previously uncertain own publication.
    b.discussions[1][0]["notes"][0]["body"] = publication["body"]
    b.finish(first["thread_id"], human)
    second = next(a for a in queue_attempts(b) if a["iid"] == 2)
    b.finish(second["thread_id"], second["turn_id"])
    b.poll()
    continuation = next(a for a in queue_attempts(b) if a.get("continuation"))
    b.runtime(first["thread_id"], continuation["turn_id"])
    resumed = b.call("claim", b.config, state, 1, {"attempt_id": continuation["id"], "event_id": continuation["event_id"]})
    assert len(resumed["owner"]["event_ids"]) == 2
    queue_complete(b, state, continuation, resumed)


def test_review_queue_conflicting_ack_keeps_capacity_until_exact_reconciliation(boundary):
    b = boundary
    for iid in (1, 2):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll()
    state, first, work = b.active_claim()
    other = {"id": "conflicting-turn", "status": "inProgress"}
    b.turns[first["thread_id"]].insert(0, other)
    b.items[other["id"]] = copy.deepcopy(b.items[first["turn_id"]])
    with pytest.raises(RuntimeError, match="conflicts"):
        b.call("accept", state, first["id"], other["id"])
    b.finish(first["thread_id"], first["turn_id"])
    b.threads[first["thread_id"]]["status"] = {"type": "active"}
    b.poll()
    assert len(queue_attempts(b)) == 1
    assert sum(r["state"] == "active" for r in b.call("queue", state)) == 1


@pytest.mark.parametrize("conflict", ["rule", "profile"])
def test_review_queue_intermediate_tick_preserves_preflight_refusals(boundary, conflict):
    b = boundary
    for iid in (1, 2):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll(scheduled=True)
    state, first, work = b.active_claim()
    queue_complete(b, state, first, work)
    b.finish(first["thread_id"], first["turn_id"])
    if conflict == "rule":
        rule = Path(b.config["codex_home"]) / "rules/codex-session-stats-gitlab-monitor.rules"
        rule.write_text("conflicting rule\n")
    else:
        b.codex_settings["permissions"]["codex-session-stats-gitlab-monitor"]["extends"] = ":workspace-write"
    b.now += dt.timedelta(minutes=1)
    with pytest.raises(RuntimeError, match="conflict"):
        b.poll(scheduled=True)
    assert len(queue_attempts(b)) == 1


def test_review_queue_competing_production_resumes_admit_one_native_owner(boundary):
    import concurrent.futures
    import threading
    b = boundary
    state, original, paused = queue_hold(b)
    human = human_turn(b, original["thread_id"], "continuar")
    barrier = threading.Barrier(2)
    payload = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
               "answer_sufficient": True, "answer_summary": "continuar"}
    def compete():
        connection = b.state()
        barrier.wait(timeout=5)
        try:
            return b.call("resume", b.config, connection, 1, payload)
        except RuntimeError as error:
            return str(error)
        finally:
            connection.db.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: compete(), range(2)))
    assert any(isinstance(result, dict) and result.get("owner", {}).get("turn_id") == human for result in results)
    reservations = [r for r in b.call("queue", state) if r["state"] == "active"]
    assert len(reservations) == 1 and reservations[0]["turn_id"] == human
    assert state.get("mrs", "1")["owner"]["turn_id"] == human
    assert len(queue_attempts(b)) == 1


def test_review_queue_distinct_human_resumes_share_one_global_slot(boundary):
    import concurrent.futures
    import threading
    b = boundary
    b.config["parallel"] = 2
    for iid in (1, 2):
        b.mr(iid=iid, created=b.now.isoformat())
    b.poll()
    state = b.state()
    identities, payloads = {}, {}
    for attempt in queue_attempts(b):
        iid = attempt["iid"]
        b.runtime(attempt["thread_id"], attempt["turn_id"])
        work = b.call("claim", b.config, state, iid, {"attempt_id": attempt["id"], "event_id": attempt["event_id"]})
        paused = b.call("pause", b.config, state, iid, {"generation": work["generation"], "question": "Qual comportamento?"})
        b.items[attempt["turn_id"]].append({"type": "agentMessage", "phase": "final_answer", "text": paused["question"]})
        b.finish(attempt["thread_id"], attempt["turn_id"])
        human = human_turn(b, attempt["thread_id"], "continuar")
        identities[iid] = (attempt["thread_id"], human)
        payloads[iid] = {"case_id": paused["case_id"], "expected_generation": paused["generation"],
                         "answer_sufficient": True, "answer_summary": "continuar"}
    b.call("queue_reconcile", b.config, state)
    b.config["parallel"] = 1
    runtime = threading.local()
    b.monkeypatch.setitem(b.code, "monitor_runtime", lambda config: identities[runtime.iid])
    real_ready = b.code["monitor_queue_ready"]
    before_observation = threading.Barrier(2)
    after_observation = threading.Barrier(2)
    later_ticket_admitted = threading.Event()
    def overlapping_ready(*args, **kwargs):
        # Only scheduling is controlled: both production readiness results remain real.
        before_observation.wait(timeout=5)
        result = real_ready(*args, **kwargs)
        after_observation.wait(timeout=5)
        tickets = [r for r in b.call("queue", args[1]) if r["state"] == "queued"]
        runtime.earlier = tickets[0]["iid"] == runtime.iid
        # The later ticket is eligible while the earlier MR still awaits its answer.
        # Its transaction completes before the older answer tries to reserve capacity.
        if runtime.earlier:
            assert later_ticket_admitted.wait(timeout=5)
        return result
    b.monkeypatch.setitem(b.code, "monitor_queue_ready", overlapping_ready)
    def resume(iid):
        runtime.iid = iid
        connection = b.state()
        try:
            return b.call("resume", b.config, connection, iid, payloads[iid])
        finally:
            if not runtime.earlier:
                later_ticket_admitted.set()
            connection.db.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(resume, (1, 2)))
    assert sum(result.get("queued", False) for result in results) == 1
    assert sum(bool(record.get("owner")) for record in state.all("mrs")) == 1
    assert sum(r["state"] == "active" for r in b.call("queue", state)) == 1
    assert all(case["state"] == "answered" for case in state.all("cases"))
    assert len(queue_attempts(b)) == 2


def named_project_boundary(b):
    """Keep production selection/config/state; extend only native external replies."""
    target, _ = analysis_config(b.path.parent, b.config)
    b.config = b.call('config', b.path)
    roots = [b.path.parent / 'source-main', b.path.parent / 'source-extra']
    for root in roots:
        root.mkdir()
    project = {'id': '11111111-1111-1111-1111-111111111111', 'name': 'fixture-project',
               'roots': [{'path': str(root)} for root in roots]}
    b.project_pages = [{'data': [project], 'nextCursor': None}]
    b.app_projects = [{'projectId': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'projectKind': 'local',
                       'label': project['name'], 'path': str(roots[0]), 'hostId': 'local'}]
    b.app_assignments = {}
    b.after_app_move = None
    b.unloaded_environments = {}
    original = b.respond
    def respond(method, params):
        if method == 'thread/resume' and params['threadId'] in b.unloaded_environments:
            thread = b.threads[params['threadId']]
            thread.update(status={'type': 'idle'},
                          environments=b.unloaded_environments.pop(params['threadId']))
        if method == 'project/list':
            return copy.deepcopy(b.project_pages[int(params.get('cursor', '0'))])
        if method == 'mcpServer/tool/call' and params['server'] == 'codex_app':
            if params['tool'] == 'list_projects':
                payload = {'schemaVersion': 2, 'projects': b.app_projects}
            elif params['tool'] == 'move_thread_to_project':
                arguments = params['arguments']
                tid = arguments['threadId']
                assert b.threads[tid]['name']
                assert arguments['source'] == 'codex' and arguments['hostId'] == 'local'
                b.app_assignments[tid] = arguments['projectId']
                if b.after_app_move:
                    b.after_app_move(tid)
                payload = {'source': 'codex', 'threadId': tid, 'hostId': 'local',
                           'projectId': arguments['projectId']}
            else:
                raise AssertionError(params['tool'])
            return {'content': [{'type': 'text', 'text': json.dumps(payload)}], 'isError': False}
        result = original(method, params)
        if method == 'thread/start':
            thread = result['thread']
            thread.update(projectId=params.get('projectId'), createdAt=int(b.now.timestamp()),
                environments=[{'environmentId': 'local', 'cwd': thread['cwd'],
                    'runtimeWorkspaceRoots': params.get('runtimeWorkspaceRoots', [thread['cwd']])}])
        if method == 'thread/name/set':
            b.threads[params['threadId']]['name'] = params['name']
        return result
    b.respond = respond
    return target, project, [str(root) for root in roots]


def select_named_project(b):
    result = b.call('select_project', b.path, 'fixture-project')
    b.config = b.call('config', b.path)
    return result


def unload_named_chat(b, thread_id):
    """Replay the native cold-read shape; only resume restores the saved environment."""
    thread = b.threads[thread_id]
    b.unloaded_environments[thread_id] = copy.deepcopy(thread['environments'])
    thread.update(status={'type': 'notLoaded'}, environments=None)


def pending_cold_chat(b):
    named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    mr = b.mr(created=b.now.isoformat())
    b.call('observe_mr', state, b.api(), mr)
    thread_id = b.call('ensure_thread', b.config, state, mr)
    unload_named_chat(b, thread_id)
    b.native.clear()
    return state, thread_id


@pytest.mark.parametrize('omitted', [False, True])
def test_cold_chat_readiness_does_not_resume_or_claim_verified_roots(boundary, omitted):
    b = boundary
    state, thread_id = pending_cold_chat(b)
    if omitted:
        del b.threads[thread_id]['environments']
    before = {bucket: list(state.db.execute(f'SELECT key,value FROM {bucket} ORDER BY key'))
              for bucket in state.BUCKETS}
    ready = b.call('queue_ready', b.config, state)
    request = b.call('queue', state)[0]
    assert ready[request['id']]['eligible'] is True
    assert 'error' not in ready[request['id']]
    assert b.threads[thread_id].get('environments') is None
    assert not [r for r in b.native if r.get('method') in {'thread/resume', 'turn/start'}]
    assert {bucket: list(state.db.execute(f'SELECT key,value FROM {bucket} ORDER BY key'))
            for bucket in state.BUCKETS} == before
    with pytest.raises(RuntimeError, match='environment is unavailable'):
        b.call('thread', b.config, thread_id)


def test_cold_empty_chat_dispatch_resumes_before_first_model_input(boundary):
    b = boundary
    state, thread_id = pending_cold_chat(b)
    result = b.poll()
    assert result['errors'] == {}
    assert result['dispatch'] == {'1': 'submitted'}
    methods = [r['method'] for r in b.native if r.get('id') == 2]
    assert methods.count('thread/resume') == methods.count('turn/start') == 1
    assert methods.index('thread/resume') < methods.index('turn/start')
    assert 'thread/start' not in methods and 'thread/name/set' not in methods
    assert not [r for r in b.native if r.get('params', {}).get('server') == 'codex_app']
    attempt = queue_attempts(b)[0]
    assert attempt['thread_id'] == thread_id and attempt['state'] == 'accepted'
    start = next(r['params'] for r in b.native if r.get('method') == 'turn/start')
    assert start['input'] == [{'type': 'text', 'text': attempt['bootstrap_text']}]
    assert state.get('events', '1:' + attempt['event_id'])['state'] == 'accepted'
    assert b.call('queue', state)[0]['state'] == 'active'


@pytest.mark.parametrize('pinned', [False, True])
def test_cold_saved_chat_dispatch_preserves_original_context_and_mapping(boundary, pinned):
    b = boundary
    named_project_boundary(b)
    if not pinned:
        select_named_project(b)
    b.mr(created=b.now.isoformat())
    b.poll()
    state, first, work = b.active_claim()
    queue_complete(b, state, first, work)
    b.finish(first['thread_id'], first['turn_id'])
    b.call('queue_reconcile', b.config, state)
    thread_id = first['thread_id']
    context = copy.deepcopy(b.threads[thread_id])
    if pinned:
        select_named_project(b)
    unload_named_chat(b, thread_id)
    b.native.clear()
    b.mr(sha='b' * 40, created=b.now.isoformat())
    result = b.poll()
    assert result['errors'] == {} and result['dispatch'] == {'1': 'submitted'}
    current, attempt, claimed = b.active_claim()
    assert attempt['id'] != first['id'] and attempt['thread_id'] == thread_id
    assert attempt['bootstrap'] is False
    assert b.threads[thread_id]['cwd'] == context['cwd']
    assert b.threads[thread_id]['environments'] == context['environments']
    assert b.threads[thread_id]['projectId'] == context['projectId']
    assert len(b.threads) == 1
    assert len([r for r in b.native if r.get('method') == 'thread/resume']) == 1
    assert not [r for r in b.native if r.get('method') in {'thread/start', 'thread/name/set'}
                or r.get('params', {}).get('server') == 'codex_app']
    queue_complete(b, current, attempt, claimed)
    assert current.get('mrs', '1')['reviewed_head'] == 'b' * 40


@pytest.mark.parametrize(('fault', 'error'), [
    ('id', 'identity/workspace mismatch'), ('cwd', 'identity/workspace mismatch'),
    ('idle', 'environment is unavailable'), ('empty-environment', 'environment is unavailable'),
    ('malformed-environment', 'environment is unavailable'),
    ('archived', 'archived or absent'), ('history', 'archived or absent'),
])
def test_cold_chat_pre_resume_denials_never_load_or_dispatch(boundary, fault, error):
    b = boundary
    state, thread_id = pending_cold_chat(b)
    thread = b.threads[thread_id]
    if fault == 'id': thread['id'] = '00000000-0000-0000-0000-999999999999'
    if fault == 'cwd': thread['cwd'] = str(b.path.parent)
    if fault == 'idle': thread['status'] = {'type': 'idle'}
    if fault == 'empty-environment': thread['environments'] = []
    if fault == 'malformed-environment': thread['environments'] = [{}]
    if fault == 'archived': thread['archived'] = True
    if fault == 'history': b.turns[thread_id] = [{'id': 'unproven', 'status': 'completed'}]
    result = b.poll()
    assert error in result['errors']['1']
    assert not [r for r in b.native if r.get('method') in {'thread/resume', 'turn/start'}]
    assert queue_attempts(b) == []
    assert b.call('queue', state)[0]['state'] == 'queued'
    assert all(e['state'] == 'pending' for e in state.all('events'))


@pytest.mark.parametrize(('fault', 'error'), [
    ('id', 'another MR conversation'), ('cwd', 'context mismatch'),
    ('missing-environment', 'environment is unavailable'), ('roots', 'context mismatch'),
    ('reorder', 'context mismatch'), ('profile', 'permission profile'),
])
def test_cold_chat_resume_must_prove_identity_profile_and_all_roots(boundary, fault, error):
    b = boundary
    state, thread_id = pending_cold_chat(b)
    external = b.respond
    def invalid_resume(method, params):
        result = external(method, params)
        if method == 'thread/resume':
            thread = result['thread']
            if fault == 'id': thread['id'] = '00000000-0000-0000-0000-999999999999'
            if fault == 'cwd': thread['cwd'] = str(b.path.parent)
            if fault == 'missing-environment': thread['environments'] = None
            if fault == 'roots': thread['environments'][0]['runtimeWorkspaceRoots'].pop()
            if fault == 'reorder': thread['environments'][0]['runtimeWorkspaceRoots'].reverse()
            if fault == 'profile': result['activePermissionProfile'] = None
        return result
    b.respond = invalid_resume
    result = b.poll()
    assert error in result['errors']['1']
    assert len([r for r in b.native if r.get('method') == 'thread/resume']) == 1
    assert not [r for r in b.native if r.get('method') == 'turn/start']
    assert queue_attempts(b) == []
    assert b.call('queue', state)[0]['state'] == 'queued'
    assert all(e['state'] == 'pending' for e in state.all('events'))


@pytest.mark.parametrize('status', ['active', 'notLoaded'])
def test_cold_chat_nonidle_resume_cannot_reserve_or_start_review(boundary, status):
    b = boundary
    state, thread_id = pending_cold_chat(b)
    external = b.respond
    def nonidle_resume(method, params):
        result = external(method, params)
        if method == 'thread/resume':
            result['thread']['status'] = {'type': status}
        return result
    b.respond = nonidle_resume
    result = b.poll()
    assert result['errors'] == {} and result['dispatch'] == {'1': 'native_busy'}
    assert len([r for r in b.native if r.get('method') == 'thread/resume']) == 1
    assert not [r for r in b.native if r.get('method') == 'turn/start']
    assert queue_attempts(b) == []
    assert b.call('queue', state)[0]['state'] == 'queued'
    assert all(e['state'] == 'pending' for e in state.all('events'))


@pytest.mark.parametrize(('capacity', 'expected', 'attempt_count'), [
    (False, 'queue_fifo', 0), (True, 'queue_capacity', 1),
])
def test_cold_chat_fifo_and_capacity_do_not_resume_unselected_chats(boundary, capacity, expected, attempt_count):
    b = boundary
    state, first_id = pending_cold_chat(b)
    if capacity:
        assert b.poll()['dispatch'] == {'1': 'submitted'}
    mr = b.mr(iid=2, created=b.now.isoformat())
    b.call('observe_mr', state, b.api(), mr)
    second_id = b.call('ensure_thread', b.config, state, mr)
    unload_named_chat(b, second_id)
    b.native.clear()
    result = b.call('dispatch', b.config, b.path, state, b.api(), 2, b.module['MonitorGate'](b.config))
    assert result == expected
    assert b.threads[second_id]['environments'] is None
    assert not [r for r in b.native if r.get('method') in {'thread/resume', 'turn/start'}]
    assert len(queue_attempts(b)) == attempt_count
    assert state.get('mrs', '1')['thread_id'] == first_id
    assert state.get('mrs', '2')['thread_id'] == second_id


def test_cold_chat_human_hold_is_preserved_without_resume(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    state, attempt, paused = queue_hold(b)
    unload_named_chat(b, attempt['thread_id'])
    b.mr(sha='b' * 40, created=b.now.isoformat())
    b.native.clear()
    b.poll()
    assert state.get('mrs', '1')['case_id'] == paused['case_id']
    assert state.get('cases', paused['case_id'])['state'] == 'awaiting_user'
    assert not [r for r in b.native if r.get('method') in {'thread/resume', 'turn/start'}]
    assert len(queue_attempts(b)) == 1


def test_cold_chat_busy_before_resume_stays_queued(boundary):
    b = boundary
    state, thread_id = pending_cold_chat(b)
    b.threads[thread_id].update(status={'type': 'active'},
                              preview='A human task is running',
                              environments=b.unloaded_environments.pop(thread_id))
    result = b.poll()
    assert result['errors'] == {} and result['dispatch'] == {'1': 'queue_waiting'}
    assert not [r for r in b.native if r.get('method') in {'thread/resume', 'turn/start'}]
    assert queue_attempts(b) == []
    assert b.call('queue', state)[0]['state'] == 'queued'


@pytest.mark.parametrize('flag', ['--hold-check', '--verify', '--diagnose-socket'])
def test_cold_chat_pilot_resumes_before_its_single_diagnostic_turn(boundary, capsys, flag):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    b.mr()
    code, output = monitor_cli(b, capsys, 'pilot', '--mr', '1')
    assert code == 0, output.err
    thread_id = json.loads(output.out)['thread_id']
    unload_named_chat(b, thread_id)
    b.native.clear()
    code, output = monitor_cli(b, capsys, 'pilot', '--mr', '1', flag)
    assert code == 0, output.err
    assert json.loads(output.out)['thread_id'] == thread_id
    requests = [r for r in b.native if r.get('id') == 2]
    methods = [r['method'] for r in requests]
    assert methods.count('thread/resume') == methods.count('turn/start') == 1
    assert methods.index('thread/resume') < methods.index('turn/start')
    assert 'thread/start' not in methods
    attempts = [a for a in b.state().all('attempts') if a['kind'] != 'conversation']
    assert len(attempts) == 1
    assert attempts[0]['state'] == 'accepted' and attempts[0]['thread_id'] == thread_id


@pytest.mark.parametrize('flag', ['--hold-check', '--verify', '--diagnose-socket'])
@pytest.mark.parametrize('status', ['active', 'notLoaded'])
def test_cold_chat_pilot_nonidle_resume_never_records_attempt_or_turn(boundary, capsys, flag, status):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    b.mr()
    code, output = monitor_cli(b, capsys, 'pilot', '--mr', '1')
    assert code == 0, output.err
    thread_id = json.loads(output.out)['thread_id']
    unload_named_chat(b, thread_id)
    b.native.clear()
    external = b.respond
    def nonidle_resume(method, params):
        result = external(method, params)
        if method == 'thread/resume':
            result['thread']['status'] = {'type': status}
        return result
    b.respond = nonidle_resume
    code, output = monitor_cli(b, capsys, 'pilot', '--mr', '1', flag)
    if flag == '--hold-check':
        assert code == 0 and json.loads(output.out)['hold_check'] == 'native_busy'
    else:
        assert code == 1 and 'idle resumed conversation' in output.err
    assert len([r for r in b.native if r.get('method') == 'thread/resume']) == 1
    assert not [r for r in b.native if r.get('method') == 'turn/start']
    state = b.state()
    assert [a for a in state.all('attempts') if a['kind'] != 'conversation'] == []
    assert not any(r['state'] == 'active' for r in b.call('queue', state))


def test_named_project_selection_preserves_old_chat_and_uses_two_roots_for_new_chat(boundary):
    b = boundary
    target, project, roots = named_project_boundary(b)
    state = b.state()
    old_id = b.call('ensure_thread', b.config, state, b.mr())
    old_cwd = b.config['cwd']
    with state.atomic():
        record = state.get('mrs', '1')
        record.update(generation=8, bootstrap_verified=True, human_continuation_verified=True)
        state.put('mrs', '1', record)
    before = {bucket: list(state.db.execute(f'SELECT key,value FROM {bucket} ORDER BY key'))
              for bucket in state.BUCKETS - {'meta'}}
    native_before = copy.deepcopy(b.threads[old_id])
    marker = len(b.native)
    result = select_named_project(b)
    assert result['selected'] is True
    assert 'workspace' not in tomllib.loads(target.read_text())
    assert tomllib.loads(target.read_text())['codex_project_name'] == 'fixture-project'
    assert b.config['cwd'] == roots[0]
    assert all(request.get('method') in {'initialize', 'initialized', 'project/list', 'thread/read', 'thread/list',
                                        'thread/turns/list'} for request in b.native[marker:])
    assert b.threads[old_id] == native_before
    assert {bucket: list(state.db.execute(f'SELECT key,value FROM {bucket} ORDER BY key'))
            for bucket in state.BUCKETS - {'meta'}} == before
    with pytest.raises(RuntimeError, match='binding changed'):
        with state.atomic():
            state.put('meta', 'stale', True)
    fresh = b.state()
    assert b.call('thread', b.config, old_id)['cwd'] == old_cwd
    b.call('prepare_thread', b.config, old_id)
    new_id = b.call('ensure_thread', b.config, fresh, b.mr(2))
    assert b.threads[new_id]['projectId'] == project['id']
    assert b.threads[new_id]['cwd'] == roots[0]
    assert b.threads[new_id]['environments'][0]['runtimeWorkspaceRoots'] == roots
    assert b.call('thread', b.config, new_id, active_inventory=True, allow_empty=True)['id'] == new_id
    raw = (b.path.read_bytes(), target.read_bytes())
    assert select_named_project(b)['changed'] is False
    assert (b.path.read_bytes(), target.read_bytes()) == raw


@pytest.mark.parametrize('change', ['duplicate', 'rename', 'id', 'reorder', 'secondary', 'cursor'])
def test_named_project_drift_blocks_native_creation_without_attempt(boundary, change):
    b = boundary
    _, project, roots = named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    if change == 'duplicate':
        b.project_pages[0]['nextCursor'] = '1'
        b.project_pages.append({'data': [{**project, 'id': '22222222-2222-2222-2222-222222222222'}], 'nextCursor': None})
    elif change == 'rename':
        b.project_pages[0]['data'][0]['name'] = 'renamed'
    elif change == 'id':
        b.project_pages[0]['data'][0]['id'] = '22222222-2222-2222-2222-222222222222'
    elif change == 'reorder':
        b.project_pages[0]['data'][0]['roots'].reverse()
    elif change == 'secondary':
        b.project_pages[0]['data'][0]['roots'] = [{'path': roots[0]}]
    else:
        del b.project_pages[0]['nextCursor']
    before = len(b.native)
    with pytest.raises(RuntimeError, match='project'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert not state.all('attempts')
    assert not any(r.get('method') == 'thread/start' for r in b.native[before:])


def test_named_project_secondary_root_inside_writable_state_is_rejected(boundary):
    b = boundary
    target, _, _ = named_project_boundary(b)
    forbidden = Path(b.config['state_file']).parent / 'source'
    forbidden.mkdir(parents=True)
    b.project_pages[0]['data'][0]['roots'][1]['path'] = str(forbidden)
    before = (b.path.read_bytes(), target.read_bytes())
    with pytest.raises(RuntimeError, match='state'):
        select_named_project(b)
    assert before == (b.path.read_bytes(), target.read_bytes())
    assert 'codex_project_name' not in tomllib.loads(target.read_text())


def test_named_project_status_is_offline_and_existing_thread_stays_in_original_context(boundary, monkeypatch, capsys):
    b = boundary
    target, _, roots = named_project_boundary(b)
    select_named_project(b)
    b.state().db.close()
    poison = types.ModuleType('websockets')
    monkeypatch.setitem(sys.modules, 'websockets', poison)
    def forbidden(*args, **kwargs):
        pytest.fail('offline status must not contact native server')
    monkeypatch.setitem(b.code, 'monitor_native', forbidden)
    monkeypatch.setattr(sys, 'argv', [str(b.cli), 'monitor-gitlab', '--config', str(b.path), 'status'])
    assert b.module['monitor_main']() == 0
    out = json.loads(capsys.readouterr().out)
    assert out['codex_project_name'] == 'fixture-project'
    assert out['cwd'] == roots[0]
    assert 'workspace' not in tomllib.loads(target.read_text())


@pytest.mark.parametrize('phase', ['intent', 'barrier', 'bound', 'toml', 'json'])
def test_named_project_selection_recovers_interruption_and_blocks_stale_connections(boundary, monkeypatch, phase):
    from contextlib import contextmanager
    b = boundary
    target, _, _ = named_project_boundary(b)
    old = b.state()
    atomic = b.module['MonitorState'].atomic
    replace, fsync = os.replace, b.code['monitor_fsync_directory']
    armed = True
    def interrupt():
        nonlocal armed
        if armed:
            armed = False
            raise OSError('fixture cutover interruption')
    @contextmanager
    def transaction(self, **kwargs):
        with atomic(self, **kwargs):
            yield
        receipt = self.get('meta', 'project_selection')
        if receipt and ((phase == 'barrier' and receipt['state'] == 'prepared')
                        or (phase == 'bound' and receipt['state'] == 'bound')):
            interrupt()
    def publish(source, destination):
        replace(source, destination)
        if phase == 'toml' and Path(destination) == target or phase == 'json' and Path(destination) == b.path:
            interrupt()
    def durable(directory):
        fsync(directory)
        if phase == 'intent' and b.path.with_name(b.path.name + '.project-selection').exists():
            interrupt()
    monkeypatch.setattr(b.module['MonitorState'], 'atomic', transaction)
    monkeypatch.setattr(os, 'replace', publish)
    monkeypatch.setitem(b.code, 'monitor_fsync_directory', durable)
    with pytest.raises(OSError, match='cutover interruption'):
        select_named_project(b)
    with pytest.raises(RuntimeError, match='selection|binding changed'):
        with old.atomic():
            old.put('meta', 'stale', True)
    def unavailable(*args, **kwargs):
        pytest.fail('prepared selection must recover locally with the app unavailable')
    monkeypatch.setitem(b.code, 'monitor_native', unavailable)
    assert select_named_project(b)['selected'] is True
    fresh = b.state()
    assert fresh.get('meta', 'project_selection')['state'] == 'completed'
    assert 'workspace' not in tomllib.loads(target.read_text())
    assert not b.path.with_name(b.path.name + '.project-selection').exists()


@pytest.mark.parametrize('field', ['root', 'project'])
def test_named_project_creation_records_returned_id_before_context_validation(boundary, field):
    b = boundary
    _, _, _ = named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def wrong(method, params):
        result = original(method, params)
        if method == 'thread/start':
            if field == 'root':
                result['thread']['environments'][0]['runtimeWorkspaceRoots'].pop()
            else:
                result['thread']['projectId'] = None
        return result
    b.respond = wrong
    state = b.state()
    with pytest.raises(RuntimeError, match='project|workspace'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['thread_id'] in b.threads
    assert attempt['state'] == 'uncertain'
    assert not state.get('mrs', '1').get('thread_id')
    count = len(b.threads)
    with pytest.raises(RuntimeError, match='uncertain'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert len(b.threads) == count


def test_named_project_existing_chat_continues_normal_review_with_original_context(boundary):
    b = boundary
    named_project_boundary(b)
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    queue_complete(b, state, attempt, work)
    b.finish(attempt['thread_id'], attempt['turn_id'])
    b.call('queue_reconcile', b.config, state)
    old_id, old_cwd = attempt['thread_id'], b.config['cwd']
    select_named_project(b)
    b.mr(sha='b' * 40, created=b.now.isoformat())
    b.poll()
    current, next_attempt, claimed = b.active_claim()
    assert next_attempt['id'] != attempt['id']
    assert next_attempt['thread_id'] == old_id
    queue_complete(b, current, next_attempt, claimed)
    assert current.get('mrs', '1')['reviewed_head'] == 'b' * 40
    assert b.threads[old_id]['cwd'] == old_cwd
    assert b.threads[old_id]['projectId'] is None
    assert len(b.threads) == 1


@pytest.mark.parametrize('change', ['missing-environment', 'busy', 'ambiguous-environment', 'secondary-in-state'])
def test_named_project_unavailable_existing_context_refuses_selection_without_mutation(boundary, change):
    b = boundary
    target, _, _ = named_project_boundary(b)
    state = b.state()
    old_id = b.call('ensure_thread', b.config, state, b.mr())
    if change == 'missing-environment':
        del b.threads[old_id]['environments']
    elif change == 'busy':
        b.threads[old_id]['status'] = {'type': 'active'}
    elif change == 'ambiguous-environment':
        b.threads[old_id]['environments'] *= 2
    else:
        forbidden = Path(b.config['state_file']).parent / 'source'
        forbidden.mkdir()
        b.threads[old_id]['environments'][0]['runtimeWorkspaceRoots'].append(str(forbidden))
    files = (b.path.read_bytes(), target.read_bytes())
    before = b.call('selection_snapshot', state)
    marker = len(b.native)
    with pytest.raises(RuntimeError, match='environment|idle|state'):
        select_named_project(b)
    assert (b.path.read_bytes(), target.read_bytes()) == files
    assert b.call('selection_snapshot', state) == before
    assert not b.path.with_name(b.path.name + '.project-selection').exists()
    assert not any(r.get('method') in {'thread/resume', 'thread/start', 'thread/metadata/update'}
                   for r in b.native[marker:])


@pytest.mark.parametrize('obstacle', ['owner', 'hold', 'queue-tail', 'uncertain', 'effect'])
def test_named_project_active_or_uncertain_work_blocks_selection(boundary, obstacle):
    b = boundary
    target, _, _ = named_project_boundary(b)
    state = b.state()
    old_id = b.call('ensure_thread', b.config, state, b.mr())
    with state.atomic():
        record = state.get('mrs', '1')
        if obstacle == 'owner':
            record['owner'] = {'turn_id': 'still-running'}
        elif obstacle == 'hold':
            record['case_id'] = 'case'
        elif obstacle == 'queue-tail':
            state.put('meta', 'review_request:tail', {'id': 'tail', 'iid': 1, 'state': 'active',
                'sequence': 1, 'thread_id': old_id, 'turn_id': 'still-running'})
        elif obstacle == 'uncertain':
            state.put('attempts', 'uncertain', {'id': 'uncertain', 'iid': 1, 'state': 'uncertain'})
        else:
            state.put('operations', '1:effect', {'id': 'effect', 'state': 'attempting'})
        state.put('mrs', '1', record)
    before = (b.path.read_bytes(), target.read_bytes(), b.call('selection_snapshot', state))
    with pytest.raises(RuntimeError, match='owner|hold|tails|uncertain|effects'):
        select_named_project(b)
    assert before == (b.path.read_bytes(), target.read_bytes(), b.call('selection_snapshot', state))


@pytest.mark.parametrize('kind', ['toml-conflict', 'missing-binding', 'wrong-name', 'json-name'])
def test_named_project_configuration_rejects_duplicate_or_unbound_authority(boundary, kind):
    b = boundary
    target, _, _ = named_project_boundary(b)
    select_named_project(b)
    data = json.loads(b.path.read_text())
    if kind == 'toml-conflict':
        target.write_text(target.read_text() + 'workspace = "workspace"\n')
    elif kind == 'missing-binding':
        del data['codex_project_binding']
    elif kind == 'wrong-name':
        data['codex_project_binding']['name'] = 'other'
    else:
        data['codex_project_name'] = 'fixture-project'
    b.path.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match='workspace|binding|TOML'):
        b.call('config', b.path)


@pytest.mark.parametrize('extra', ['valid-hosting', 'wrong-thread', 'wrong-date', 'arbitrary', 'reordered'])
def test_named_project_thread_checks_all_sources_and_only_its_bounded_hosting_root(boundary, extra):
    b = boundary
    _, _, roots = named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    tid = b.call('ensure_thread', b.config, state, b.mr())
    thread = b.threads[tid]
    runtime = thread['environments'][0]['runtimeWorkspaceRoots']
    if extra == 'reordered':
        runtime.reverse()
    else:
        day = b.now.date() + dt.timedelta(days=1 if extra != 'wrong-date' else 4)
        end = tid if extra != 'wrong-thread' else '22222222-2222-2222-2222-222222222222'
        path = Path(b.config['codex_home']) / 'visualizations' / day.strftime('%Y/%m/%d') / end
        if extra == 'arbitrary':
            path = b.path.parent / 'unrequested'
        path.mkdir(parents=True)
        runtime.append(str(path))
    if extra == 'valid-hosting':
        assert b.call('thread', b.config, tid)['id'] == tid
    else:
        with pytest.raises(RuntimeError, match='context mismatch'):
            b.call('thread', b.config, tid)


def test_named_project_binding_includes_secondary_root_and_identity_for_stale_connections(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    old = b.state()
    changed = copy.deepcopy(b.config)
    changed['codex_project_binding']['roots'] = changed['codex_project_binding']['roots'][:1]
    with pytest.raises(RuntimeError, match='another project'):
        b.module['MonitorState'](changed)
    changed = copy.deepcopy(b.config)
    changed['codex_project_binding']['id'] = '22222222-2222-2222-2222-222222222222'
    with pytest.raises(RuntimeError, match='another project'):
        b.module['MonitorState'](changed, readonly=True)
    assert old.get('meta', 'identity') == b.call('state_identity', b.config)


@pytest.mark.parametrize('tamper', ['receipt', 'business-state', 'toml', 'json'])
def test_named_project_interrupted_selection_refuses_changed_inputs_without_overwrite(boundary, monkeypatch, tamper):
    b = boundary
    target, _, _ = named_project_boundary(b)
    state = b.state()
    replace = os.replace
    def interrupted(source, destination):
        if Path(destination) == target:
            raise OSError('fixture stopped before file publication')
        return replace(source, destination)
    monkeypatch.setattr(os, 'replace', interrupted)
    with pytest.raises(OSError, match='stopped before'):
        select_named_project(b)
    with state.atomic(workspace_adoption=True):
        if tamper == 'receipt':
            state.put('meta', 'project_selection', {'intent': 'forged', 'state': 'bound'})
        elif tamper == 'business-state':
            state.put('events', '1:forged', {'state': 'pending'})
    if tamper == 'toml':
        target.write_text(target.read_text() + '# concurrent edit\n')
    elif tamper == 'json':
        data = json.loads(b.path.read_text()); data['parallel'] = 2
        b.path.write_text(json.dumps(data))
    before = (b.path.read_bytes(), target.read_bytes(), b.call('selection_snapshot', state))
    monkeypatch.setattr(os, 'replace', replace)
    with pytest.raises(RuntimeError, match='changed'):
        select_named_project(b)
    assert before == (b.path.read_bytes(), target.read_bytes(), b.call('selection_snapshot', state))


def test_named_project_explicit_selection_can_accept_verified_new_root_for_same_name(boundary):
    b = boundary
    _, _, roots = named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    tid = b.call('ensure_thread', b.config, state, b.mr())
    third = b.path.parent / 'new-secondary'; third.mkdir()
    b.project_pages[0]['data'][0]['roots'].append({'path': str(third)})
    assert select_named_project(b)['changed'] is True
    assert b.threads[tid]['environments'][0]['runtimeWorkspaceRoots'] == roots
    assert b.call('thread', b.config, tid)['id'] == tid
    fresh = b.state()
    new_id = b.call('ensure_thread', b.config, fresh, b.mr(2))
    assert b.threads[new_id]['environments'][0]['runtimeWorkspaceRoots'] == [*roots, str(third)]


@pytest.mark.parametrize('failure', ['write', 'fsync'])
def test_named_project_intent_publication_is_atomic_when_disk_fails(boundary, monkeypatch, failure):
    import errno
    b = boundary
    target, _, _ = named_project_boundary(b)
    state = b.state()
    before = (b.path.read_bytes(), target.read_bytes(), b.call('selection_snapshot', state))
    fdopen, fsync = os.fdopen, os.fsync
    def intent_descriptor(descriptor):
        return 'monitor-select-intent-' in os.readlink(f'/proc/self/fd/{descriptor}') or (
            os.readlink(f'/proc/self/fd/{descriptor}') == str(b.path) + '.project-selection')
    class PartialWrite:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.stream.close()
        def write(self, data):
            self.stream.write(data[:2]); self.stream.flush()
            raise OSError(errno.ENOSPC, 'fixture partial intent write')
    def open_stream(descriptor, *args, **kwargs):
        wrapped = failure == 'write' and intent_descriptor(descriptor)
        stream = fdopen(descriptor, *args, **kwargs)
        return PartialWrite(stream) if wrapped else stream
    def sync(descriptor):
        if failure == 'fsync' and intent_descriptor(descriptor):
            raise OSError(errno.ENOSPC, 'fixture intent fsync failure')
        return fsync(descriptor)
    monkeypatch.setattr(os, 'fdopen', open_stream)
    monkeypatch.setattr(os, 'fsync', sync)
    with pytest.raises(OSError, match='fixture'):
        select_named_project(b)
    assert not b.path.with_name(b.path.name + '.project-selection').exists()
    assert before == (b.path.read_bytes(), target.read_bytes(), b.call('selection_snapshot', state))
    assert b.call('config', b.path)['cwd'] == b.config['cwd']
    assert not list(b.path.parent.glob('.monitor-select-intent-*'))


def test_named_project_cached_secondary_root_must_stay_outside_writable_state(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    data = json.loads(b.path.read_text())
    forbidden = Path(b.config['state_file']).parent / 'cached-source'; forbidden.mkdir()
    data['codex_project_binding']['roots'][1] = str(forbidden)
    b.path.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match='outside agent-writable state'):
        b.call('config', b.path)


def test_named_project_creation_ack_is_enough_when_independent_grouping_is_not_persisted(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def native_response(method, params):
        result = original(method, params)
        if method == 'thread/start':
            acknowledgement = copy.deepcopy(result)
            # Actual runtime: start ACK has the requested project; a separate
            # pre-input read has no persisted sidebar metadata yet.
            b.threads[result['thread']['id']]['projectId'] = None
            return acknowledgement
        return result
    b.respond = native_response
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    queue_complete(b, state, attempt, work)
    record = state.get('mrs', '1')
    assert record['thread_id'] == attempt['thread_id']
    assert record['reviewed_head'] == 'a' * 40
    assert b.threads[record['thread_id']]['projectId'] is None
    assert sum(r.get('method') == 'thread/start' for r in b.native) == 1
    assert sum(r.get('method') == 'turn/start' for r in b.native) == 1
    assert not any(r.get('method') == 'thread/metadata/update' for r in b.native)


@pytest.mark.parametrize('project', [None, 'missing', '22222222-2222-2222-2222-222222222222'])
def test_named_project_creation_rejects_wrong_ack_even_when_later_read_has_expected_project(boundary, project):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def native_response(method, params):
        result = original(method, params)
        if method == 'thread/start':
            result = copy.deepcopy(result)
            if project == 'missing':
                result['thread'].pop('projectId')
            else:
                result['thread']['projectId'] = project
        return result
    b.respond = native_response
    state = b.state()
    with pytest.raises(RuntimeError, match='project'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['state'] == 'uncertain' and attempt['thread_id'] in b.threads
    assert not state.get('mrs', '1').get('thread_id')
    with pytest.raises(RuntimeError, match='uncertain'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert len(b.threads) == 1


def test_named_project_mr_mapping_survives_chat_rename_new_head_reply_and_missing_selector(boundary):
    b = boundary
    named_project_boundary(b)
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    queue_complete(b, state, attempt, work)
    b.finish(attempt['thread_id'], attempt['turn_id'])
    b.call('queue_reconcile', b.config, state)
    tid = attempt['thread_id']
    select_named_project(b)
    b.threads[tid]['name'] = 'User renamed this chat'
    b.config = b.call('config', b.path)
    assert b.state().get('mrs', '1')['thread_id'] == tid
    original = b.respond
    def native_response(method, params):
        assert method != 'project/list', 'existing MR must not depend on the new-chat selector'
        return original(method, params)
    b.respond = native_response
    marker = len(b.native)
    b.mr(sha='b' * 40, created=b.now.isoformat())['title'] = 'Renamed MR'
    b.poll()
    current, next_attempt, claimed = b.active_claim()
    assert next_attempt['thread_id'] == tid and next_attempt['id'] != attempt['id']
    queue_complete(b, current, next_attempt, claimed)
    b.finish(tid, next_attempt['turn_id'])
    b.call('queue_reconcile', b.config, current)
    b.note(body='Reply on an existing discussion', created=b.now.isoformat())
    b.poll()
    final, comment_attempt, comment_claim = b.active_claim()
    assert comment_attempt['thread_id'] == tid
    queue_complete(b, final, comment_attempt, comment_claim)
    assert final.get('mrs', '1')['thread_id'] == tid
    assert final.get('mrs', '1')['reviewed_head'] == 'b' * 40
    assert not any(r.get('method') in {'project/list', 'thread/start'} for r in b.native[marker:])
    assert len(b.threads) == 1


def app_requests(b, tool=None):
    return [r['params'] for r in b.native if r.get('method') == 'mcpServer/tool/call'
            and r['params']['server'] == 'codex_app'
            and (tool is None or r['params']['tool'] == tool)]


def test_new_chat_app_assignment_uses_local_name_and_app_id_before_acceptance(boundary):
    b = boundary
    _, project, roots = named_project_boundary(b)
    select_named_project(b)
    b.app_projects.extend([
        {'projectKind': 'chatgpt', 'label': 'fixture-project', 'projectId': 'cloud-id'},
        {'projectKind': 'remote', 'hostId': 'ssh:other', 'label': 'fixture-project'},
        {**b.app_projects[0], 'label': 'fixture-project-', 'projectId': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'}])
    state = b.state()
    def observe(tid):
        record = state.get('mrs', '1')
        attempt = state.get('attempts', record['creation_attempt'])
        assert record['thread_id'] is None
        assert attempt['state'] == 'attempting' and attempt['thread_id'] == tid
        assert b.turns[tid] == []
    b.after_app_move = observe
    tid = b.call('ensure_thread', b.config, state, b.mr())
    assert b.app_assignments == {tid: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
    assert b.app_assignments[tid] != project['id']
    assert b.threads[tid]['environments'][0]['runtimeWorkspaceRoots'] == roots
    assert state.get('mrs', '1')['thread_id'] == tid
    assert state.all('attempts')[0]['state'] == 'accepted'
    assert len(app_requests(b, 'list_projects')) == len(app_requests(b, 'move_thread_to_project')) == 1


def test_existing_named_chat_never_queries_or_changes_app_assignment_after_restart(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    b.mr(created=b.now.isoformat())
    b.poll()
    state, attempt, work = b.active_claim()
    tid = attempt['thread_id']
    queue_complete(b, state, attempt, work)
    b.finish(tid, attempt['turn_id'])
    b.call('queue_reconcile', b.config, state)
    b.app_assignments[tid] = 'user-selected-other-project'
    b.threads[tid]['name'] = 'User renamed chat'
    b.config = b.call('config', b.path)
    original = b.respond
    def unavailable(method, params):
        assert method != 'project/list'
        assert not (method == 'mcpServer/tool/call' and params['server'] == 'codex_app')
        return original(method, params)
    b.respond = unavailable
    b.mr(sha='b' * 40, created=b.now.isoformat())
    b.note(body='New reply', created=b.now.isoformat())
    b.poll()
    current, following, claimed = b.active_claim()
    queue_complete(b, current, following, claimed)
    assert following['thread_id'] == tid
    assert b.app_assignments[tid] == 'user-selected-other-project'
    assert b.threads[tid]['name'] == 'User renamed chat'
    assert len(b.threads) == 1


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'path', 'host', 'kind', 'id'])
def test_new_chat_app_project_refusal_retains_id_without_assignment_or_retry(boundary, change):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    if change == 'missing':
        b.app_projects.clear()
    elif change == 'duplicate':
        b.app_projects.append({**b.app_projects[0], 'projectId': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
                               'path': str(b.path.parent)})
    else:
        key, value = {'path': ('path', str(b.path.parent)), 'host': ('hostId', 'ssh:other'),
                      'kind': ('projectKind', 'chatgpt'), 'id': ('projectId', 'invalid')}[change]
        b.app_projects[0][key] = value
    state = b.state()
    with pytest.raises(RuntimeError, match='Codex app'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['state'] == 'uncertain' and attempt['thread_id'] in b.threads
    assert state.get('mrs', '1')['thread_id'] is None
    assert b.app_assignments == {} and not app_requests(b, 'move_thread_to_project')
    count = len(b.native)
    with pytest.raises(RuntimeError, match='uncertain'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert len(b.native) == count and len(b.threads) == 1


@pytest.mark.parametrize('tool', ['list_projects', 'move_thread_to_project'])
@pytest.mark.parametrize('failure', ['denied', 'envelope', 'json', 'shape'])
def test_new_chat_app_invalid_result_never_accepts_or_dispatches(boundary, tool, failure):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def response(method, params):
        result = original(method, params)
        if method == 'mcpServer/tool/call' and params['server'] == 'codex_app' and params['tool'] == tool:
            result = {'denied': {'isError': True, 'content': []},
                      'envelope': {'content': [{'type': 'image'}]},
                      'json': {'content': [{'type': 'text', 'text': 'not JSON'}]},
                      'shape': {'content': [{'type': 'text', 'text': '[]'}]}}[failure]
        return result
    b.respond = response
    state = b.state()
    with pytest.raises(RuntimeError, match='Codex app'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert state.all('attempts')[0]['state'] == 'uncertain'
    assert state.get('mrs', '1')['thread_id'] is None
    assert not any(r.get('method') == 'turn/start' for r in b.native)
    count = len(b.native)
    with pytest.raises(RuntimeError, match='uncertain'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert len(b.native) == count


@pytest.mark.parametrize('field', ['source', 'threadId', 'hostId', 'projectId'])
def test_new_chat_app_wrong_ack_keeps_known_id_and_uncertainty(boundary, field):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def response(method, params):
        result = original(method, params)
        if method == 'mcpServer/tool/call' and params['server'] == 'codex_app' and params['tool'] == 'move_thread_to_project':
            payload = json.loads(result['content'][0]['text'])
            payload[field] = 'wrong'
            result['content'][0]['text'] = json.dumps(payload)
        return result
    b.respond = response
    state = b.state()
    with pytest.raises(RuntimeError, match='Codex app'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['state'] == 'uncertain'
    assert b.app_assignments == {attempt['thread_id']: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
    assert state.get('mrs', '1')['thread_id'] is None


def test_new_chat_app_lost_ack_preserves_effect_and_never_retries_after_reload(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    def disconnect(tid):
        raise TimeoutError('fixture lost app assignment acknowledgement')
    b.after_app_move = disconnect
    state = b.state()
    with pytest.raises(RuntimeError, match=r'transport failed or timed out \(TimeoutError') as caught:
        b.call('ensure_thread', b.config, state, b.mr())
    assert isinstance(caught.value.__cause__, TimeoutError)
    attempt = state.all('attempts')[0]
    assert attempt['state'] == 'uncertain' and attempt['thread_id'] in b.app_assignments
    state.db.close()
    fresh = b.state()
    count = len(b.native)
    with pytest.raises(RuntimeError, match='uncertain'):
        b.call('ensure_thread', b.config, fresh, b.mr())
    assert len(b.native) == count and len(b.threads) == 1


def test_new_chat_app_interruption_before_local_acceptance_leaves_mapping_unset(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    def fail_local_acceptance(tid):
        state.db.execute("""CREATE TEMP TRIGGER fail_accept BEFORE UPDATE ON attempts
            WHEN json_extract(NEW.value, '$.state') = 'accepted'
            BEGIN SELECT RAISE(ABORT, 'fixture stopped before acceptance'); END""")
    b.after_app_move = fail_local_acceptance
    with pytest.raises(sqlite3.IntegrityError, match='stopped before acceptance'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['state'] == 'attempting' and attempt['thread_id'] in b.app_assignments
    assert state.get('mrs', '1')['thread_id'] is None
    state.db.close()
    count = len(b.native)
    with pytest.raises(RuntimeError, match='uncertain'):
        b.call('ensure_thread', b.config, b.state(), b.mr())
    assert len(b.native) == count


@pytest.mark.parametrize('known', ['mapping', 'attempt', 'previous', 'binding'])
def test_new_chat_app_rejects_known_ids_before_naming_or_moving(boundary, known):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    old_id = b.call('ensure_thread', b.config, state, b.mr())
    if known == 'binding':
        extra = b.path.parent / 'new-source'; extra.mkdir()
        b.project_pages[0]['data'][0]['roots'].append({'path': str(extra)})
        select_named_project(b)
        state = b.state()
    old_record = state.get('mrs', '1')
    with state.atomic():
        if known != 'mapping':
            old_record['thread_id'] = None
        if known in {'previous', 'binding'}:
            state.db.execute('DELETE FROM attempts WHERE key=?', (old_record['creation_attempt'],))
        if known == 'previous':
            old_record['previous_conversations'] = [{'thread_id': old_id}]
        state.put('mrs', '1', old_record)
    before = copy.deepcopy(b.threads[old_id])
    original = b.respond
    def duplicate(method, params):
        result = original(method, params)
        if method == 'thread/start':
            result = copy.deepcopy(result)
            result['thread']['id'] = old_id
        return result
    b.respond = duplicate
    marker = len(b.native)
    with pytest.raises(RuntimeError, match='existing monitor conversation|already mapped'):
        b.call('ensure_thread', b.config, state, b.mr(2))
    attempt = next(a for a in state.all('attempts') if a['iid'] == 2)
    assert attempt['thread_id'] == old_id and attempt['state'] == 'uncertain'
    assert b.threads[old_id] == before
    assert state.get('mrs', '2')['thread_id'] is None
    assert not any(r.get('method') == 'thread/name/set' or
                   r.get('method') == 'mcpServer/tool/call' and r['params']['server'] == 'codex_app'
                   for r in b.native[marker:])


def test_new_chat_app_rechecks_creation_authority_before_first_mutation(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    original = b.respond
    def changed(method, params):
        result = original(method, params)
        if method == 'thread/start':
            with state.atomic():
                record = state.get('mrs', '1')
                record['creation_attempt'] = 'other-attempt'
                state.put('mrs', '1', record)
        return result
    b.respond = changed
    with pytest.raises(RuntimeError, match='mapping changed'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['thread_id'] in b.threads and attempt['state'] == 'uncertain'
    assert state.get('mrs', '1')['thread_id'] is None
    assert not any(r.get('method') == 'thread/name/set' for r in b.native)
    assert not app_requests(b)


def test_new_chat_app_final_mapping_revalidates_after_move(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    state = b.state()
    def concurrent_change(tid):
        with state.atomic():
            record = state.get('mrs', '1')
            record['creation_attempt'] = 'other-attempt'
            state.put('mrs', '1', record)
    b.after_app_move = concurrent_change
    with pytest.raises(RuntimeError, match='mapping changed'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['thread_id'] in b.app_assignments
    assert state.get('mrs', '1')['thread_id'] is None


def test_uncertain_app_assignment_operator_recovery_never_moves_inspected_chat(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    def disconnect(tid):
        raise TimeoutError('fixture lost app assignment acknowledgement')
    b.after_app_move = disconnect
    state = b.state()
    with pytest.raises(RuntimeError, match=r'transport failed or timed out \(TimeoutError') as caught:
        b.call('ensure_thread', b.config, state, b.mr())
    assert isinstance(caught.value.__cause__, TimeoutError)
    attempt = state.all('attempts')[0]
    tid = attempt['thread_id']
    b.app_assignments[tid] = 'operator-corrected-project'
    marker = len(app_requests(b))
    assert b.call('recover', b.config, state, {'attempt_id': attempt['id'], 'thread_id': tid}) == {'recovered_thread': tid}
    assert len(app_requests(b)) == marker
    assert state.get('mrs', '1')['thread_id'] == tid
    assert b.app_assignments[tid] == 'operator-corrected-project'


@pytest.mark.parametrize('payload', [
    {'schemaVersion': 3, 'projects': []},
    {'schemaVersion': 2, 'projects': {}},
    {'schemaVersion': 2, 'projects': [None]},
])
def test_new_chat_app_unsupported_inventory_does_not_assign(boundary, payload):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def response(method, params):
        if method == 'mcpServer/tool/call' and params['server'] == 'codex_app' and params['tool'] == 'list_projects':
            return {'content': [{'type': 'text', 'text': json.dumps(payload)}]}
        return original(method, params)
    b.respond = response
    state = b.state()
    with pytest.raises(RuntimeError, match='Codex app project inventory'):
        b.call('ensure_thread', b.config, state, b.mr())
    assert state.all('attempts')[0]['state'] == 'uncertain'
    assert not app_requests(b, 'move_thread_to_project')
    assert state.get('mrs', '1')['thread_id'] is None


def test_new_chat_app_naming_failure_preserves_id_without_assignment(boundary):
    b = boundary
    named_project_boundary(b)
    select_named_project(b)
    original = b.respond
    def response(method, params):
        if method == 'thread/name/set':
            raise RuntimeError('fixture naming denied')
        return original(method, params)
    b.respond = response
    state = b.state()
    with pytest.raises(RuntimeError, match='fixture naming denied'):
        b.call('ensure_thread', b.config, state, b.mr())
    attempt = state.all('attempts')[0]
    assert attempt['thread_id'] in b.threads and attempt['state'] == 'uncertain'
    assert not app_requests(b)
    assert state.get('mrs', '1')['thread_id'] is None
