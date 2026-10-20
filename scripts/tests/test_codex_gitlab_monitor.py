"""Native relay and public configuration contracts retained across queue replacement."""
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
    config = module["mq_config"](root / "monitor.json")
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
    script = "import runpy,json,sys; m=runpy.run_path(sys.argv[1]); c=m['mq_config'](__import__('pathlib').Path(sys.argv[2])); print(json.dumps(m['monitor_native'](c,'config/read',{'second_client':True})))"
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
    config = module["mq_config"](root / "monitor.json")
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
    config = module["mq_config"](root / "monitor.json")
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


def test_native_revalidates_gui_lease_after_initialization_before_protected_request(shared_app):
    root, environment, base, start = shared_app
    start()
    (root / "revoke-on-monitor-initialize").touch()
    script = "import runpy,sys; m=runpy.run_path(sys.argv[1]); c=m['mq_config'](__import__('pathlib').Path(sys.argv[2])); m['monitor_native'](c,'config/read',{'must_not_send':True})"
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
    return runpy.run_path(str(CLI))["mq_config"](tmp_path / "monitor.json")


def test_mq_configure_is_private_and_status_does_not_initialize_state(tmp_path):
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


def test_mq_configure_never_overwrites_existing_configuration(tmp_path):
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
