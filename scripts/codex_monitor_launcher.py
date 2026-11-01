"""One shared Codex launcher; importing it has no runtime or optional-package effects."""
import asyncio
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

MONITOR_RELAY_LIMIT = 64 * 1024 * 1024

@lru_cache(maxsize=1)
def support():
    return runpy.run_path(str(Path(__file__).resolve().parent.parent / '.local/bin/codex-session-stats'))

@lru_cache(maxsize=1)
def cold():
    return runpy.run_path(str(Path(__file__).with_name('codex_monitor_cold.py')))

def monitor_process(pid):
    return support()['monitor_process'](pid)

def monitor_private(path, **kwargs):
    return support()['monitor_private'](path, **kwargs)

def monitor_runtime_write(path, value):
    return support()['monitor_runtime_write'](path, value)

def monitor_id():
    return support()['monitor_id']()

MONITOR_BOOTSTRAP_OPTIONS = (
    ('features', 'code_mode_host'),
    ('plugins', 'codex-app-tools@openai-bundled', 'mcp_servers', 'codex_app', 'enabled'),
    ('plugins', 'code-review@openai-bundled', 'mcp_servers', 'code-review', 'enabled'),
)


def monitor_prepare_bootstrap(authority):
    """Prepare only the approved static options while real cold-start exclusion is held."""
    import copy
    import math
    import stat
    import tempfile
    import tomllib

    if not isinstance(authority, cold()['MonitorColdStart']):
        raise RuntimeError('bootstrap preparation requires the shared cold-start authority')
    authority.verify()
    target = authority.home / 'config.toml'

    snapshot = lambda: cold()['monitor_config_snapshot'](authority)

    original_identity, original = snapshot()
    parsed = tomllib.loads(original.decode('utf-8'))
    expected = copy.deepcopy(parsed)
    changed = False
    for path in MONITOR_BOOTSTRAP_OPTIONS:
        table = expected
        for name in path[:-1]:
            if name not in table:
                table[name] = {}
            if not isinstance(table[name], dict):
                raise RuntimeError('bootstrap option parent is not a TOML table: ' + '.'.join(path))
            table = table[name]
        name = path[-1]
        if name in table and type(table[name]) is not bool:
            raise RuntimeError('bootstrap option is not a boolean: ' + '.'.join(path))
        changed = changed or table.get(name) is not True
        table[name] = True

    def revalidate():
        authority.verify()
        if snapshot() != (original_identity, original):
            raise RuntimeError('Codex config changed concurrently; preparation refused')

    if not changed:
        revalidate()
        return {'changed': False, 'backup': None}
    try:
        import tomlkit
    except ImportError as error:
        raise RuntimeError('A preparação do Codex requer tomlkit. Em ~/scripts, execute '
                           'poetry install --with monitor-tools.') from error
    document = tomlkit.parse(original.decode('utf-8'))
    for path in MONITOR_BOOTSTRAP_OPTIONS:
        table = document
        for name in path[:-1]:
            if name not in table:
                table[name] = tomlkit.table()
            table = table[name]
        table[path[-1]] = True
    prepared = tomlkit.dumps(document).encode('utf-8')

    def same(left, right):
        if type(left) is not type(right):
            return False
        if isinstance(left, dict):
            return left.keys() == right.keys() and all(same(left[key], right[key]) for key in left)
        if isinstance(left, list):
            return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
        if isinstance(left, float) and math.isnan(left):
            return math.isnan(right)
        return left == right

    if not same(tomllib.loads(prepared.decode('utf-8')), expected):
        raise RuntimeError('TOML preparation changed data beyond the three approved options')

    result = cold()['monitor_publish_config'](authority, (original_identity, original), prepared)
    return {'changed': result['changed'], 'backup': result['backup']}


def monitor_app_tools_directory(config, *, create=False):
    import stat
    base = Path('/tmp').resolve(strict=True)
    meta = base.lstat()
    if (not stat.S_ISDIR(meta.st_mode) or meta.st_uid not in {0, os.getuid()}
            or (meta.st_mode & 0o022 and not meta.st_mode & stat.S_ISVTX)):
        raise RuntimeError('unsafe app-tool temporary directory')
    directory = base / ('codex-tools-' + str(os.getuid()) + '-' +
        hashlib.sha256(config['codex_home'].encode()).hexdigest()[:20])
    if len(os.fsencode(str(directory / 'host.sock'))) >= 108:
        raise RuntimeError('app-tool Unix address exceeds the supported length')
    if create:
        directory.mkdir(mode=0o700, exist_ok=True)
    monitor_private(directory, directory=True)
    return directory


def monitor_app_tools_bind(directory, pipe, gui, proxy, generation):
    """Pin an authenticated GUI socket; never follow a reusable public pathname later."""
    import fcntl
    import socket
    import stat
    import struct
    directory, pipe = Path(directory), Path(pipe)
    monitor_private(directory, directory=True)
    descriptor = os.open(directory / 'bind.lock', os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    temporary = directory / ('pending-' + monitor_id())
    try:
        monitor_private(directory / 'bind.lock')
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        published, record_path = directory / 'host.sock', directory / 'binding.json'
        if record_path.exists():
            monitor_private(record_path)
            old = json.loads(record_path.read_text())
            meta = published.lstat()
            if (not stat.S_ISSOCK(meta.st_mode) or meta.st_uid != os.getuid()
                    or [meta.st_dev, meta.st_ino] != old['socket_identity']):
                raise RuntimeError('previous app-tool binding identity changed')
            for role, identity in (('gui', gui), ('proxy', proxy)):
                if old[role] == identity:
                    continue
                try:
                    current = monitor_process(old[role]['pid'])
                except (FileNotFoundError, ProcessLookupError):
                    current = None
                except RuntimeError:
                    # monitor_process rejects a proven zombie; no live lease is claimed here.
                    fields = Path('/proc/' + str(old[role]['pid']) + '/stat').read_text().rsplit(')', 1)[1].split()
                    if fields[0] not in {'Z', 'X'}:
                        raise
                    current = None
                if current and current['birth'] == old[role]['birth']:
                    raise RuntimeError('previous app-tool ' + role + ' is still live')
        elif published.exists() or published.is_symlink():
            raise RuntimeError('app-tool socket exists without an authenticated binding')
        original = pipe.lstat()
        if (not stat.S_ISSOCK(original.st_mode) or original.st_uid != os.getuid()
                or original.st_dev != directory.stat().st_dev):
            raise RuntimeError('app-tool host must be an owned same-filesystem Unix socket')
        os.link(pipe, temporary, follow_symlinks=False)
        identity = [original.st_dev, original.st_ino]
        def verify():
            meta = temporary.lstat()
            if (not stat.S_ISSOCK(meta.st_mode) or meta.st_uid != os.getuid()
                    or [meta.st_dev, meta.st_ino] != identity
                    or monitor_process(gui['pid']) != gui or monitor_process(proxy['pid']) != proxy):
                raise RuntimeError('app-tool private socket or process identity changed')
        verify()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(5)
            connection.connect(str(temporary))
            pid, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if pid != gui['pid'] or uid != os.getuid():
                raise RuntimeError('app-tool private socket peer is not the selected GUI')
            verify()
            receipt = {'gui': gui, 'proxy': proxy, 'generation': generation,
                       'socket_identity': identity}
            os.replace(temporary, published)
            monitor_runtime_write(record_path, receipt)
            return receipt
    finally:
        temporary.unlink(missing_ok=True)
        os.close(descriptor)


def monitor_app_tools_unbind(directory, receipt):
    import fcntl
    import stat
    directory = Path(directory)
    monitor_private(directory, directory=True)
    descriptor = os.open(directory / 'bind.lock', os.O_WRONLY | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        monitor_private(directory / 'binding.json')
        if json.loads((directory / 'binding.json').read_text()) != receipt:
            return False
        meta = (directory / 'host.sock').lstat()
        if (not stat.S_ISSOCK(meta.st_mode) or meta.st_uid != os.getuid()
                or [meta.st_dev, meta.st_ino] != receipt['socket_identity']):
            raise RuntimeError('app-tool cleanup socket identity changed')
        (directory / 'host.sock').unlink()
        (directory / 'binding.json').unlink()
        return True
    finally:
        os.close(descriptor)


async def monitor_relay_protocol(connection, reader, writer, *, verify, on_ready, timeout):
    """Normalize the main GUI handshake; observe GUI traffic before publishing readiness."""
    import asyncio
    sentinel = object()
    initialize_id = sentinel
    native_initialized = False
    initialize_delivered = False
    gui_exchange = sentinel
    gui_requests, server_requests = {}, set()
    ready = asyncio.Event()
    write_lock = asyncio.Lock()
    active = True

    def identifier(value):
        return isinstance(value, (str, int)) and not isinstance(value, bool)

    def decode(raw, source):
        if not isinstance(raw, (bytes, str)):
            raise RuntimeError(source + ' relay frame is binary or invalid')
        if len(raw if isinstance(raw, bytes) else raw.encode()) > MONITOR_RELAY_LIMIT:
            raise RuntimeError(source + ' relay message exceeds 64 MiB')
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise RuntimeError(source + ' relay message is not an object')
        return value

    async def send_native(raw):
        async with write_lock:
            await connection.send(raw)

    async def send_gui(raw):
        writer.write((raw + '\n').encode())
        await writer.drain()

    def publish_if_ready():
        if (active and not ready.is_set() and native_initialized and initialize_delivered
                and gui_exchange is not sentinel and not server_requests):
            verify()
            on_ready({'native_ack_owner': 'relay', 'gui_rpc_id': gui_exchange})
            ready.set()
            gui_requests.clear()

    async def to_native():
        nonlocal initialize_id, active
        try:
            while raw := await reader.readline():
                message = decode(raw, 'GUI')
                method = message.get('method')
                key = message.get('id')
                if method == 'initialize':
                    if initialize_id is not sentinel or not identifier(key):
                        raise RuntimeError('GUI initialization is repeated or invalid')
                    initialize_id = key
                elif method == 'initialized':
                    if (not native_initialized or 'id' in message
                            or message.get('params', {}) != {}):
                        raise RuntimeError('GUI initialized notification is premature or invalid')
                    # The relay already completed this native connection's handshake.
                    continue
                elif method is None and identifier(key) and key in server_requests:
                    if ('result' in message) == ('error' in message):
                        raise RuntimeError('invalid GUI reply to native initialization request')
                    await send_native(raw.decode().rstrip('\n'))
                    server_requests.remove(key)
                    publish_if_ready()
                    continue
                elif not native_initialized:
                    raise RuntimeError('GUI request preceded native handshake completion')
                elif not ready.is_set() and method is not None and 'id' in message:
                    if not identifier(key) or key in gui_requests or len(gui_requests) >= 256:
                        raise RuntimeError('invalid or excessive GUI startup requests')
                    gui_requests[key] = method
                await send_native(raw.decode().rstrip('\n'))
        finally:
            active = False

    async def to_gui():
        nonlocal native_initialized, initialize_delivered, gui_exchange, active
        try:
            async for raw in connection:
                if not isinstance(raw, str):
                    raise RuntimeError('native GUI relay frame is binary')
                message = decode(raw, 'native')
                method, key = message.get('method'), message.get('id')
                if (method is None and initialize_id is not sentinel
                        and key == initialize_id and not native_initialized):
                    if 'error' in message:
                        await send_gui(raw)
                        raise RuntimeError('native GUI initialization rejected')
                    if not isinstance(message.get('result'), dict):
                        raise RuntimeError('invalid native GUI initialization response')
                    verify()
                    await send_native(json.dumps({'method': 'initialized', 'params': {}}))
                    # Set before GUI bytes become readable: input can race output drain.
                    native_initialized = True
                    await send_gui(raw)
                    initialize_delivered = True
                    publish_if_ready()
                    continue
                if not ready.is_set() and method is not None and 'id' in message:
                    if not identifier(key) or key in server_requests or len(server_requests) >= 256:
                        raise RuntimeError('invalid or excessive native initialization requests')
                    server_requests.add(key)
                await send_gui(raw)
                if (native_initialized and not ready.is_set() and method is None
                        and identifier(key) and key in gui_requests):
                    gui_requests.pop(key)
                    if 'result' in message and 'error' not in message:
                        gui_exchange = key
                        publish_if_ready()
        finally:
            active = False

    async def startup_watchdog():
        await asyncio.wait_for(ready.wait(), timeout)
        await asyncio.get_running_loop().create_future()

    tasks = [asyncio.create_task(to_native()), asyncio.create_task(to_gui()),
             asyncio.create_task(startup_watchdog())]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
        if not ready.is_set():
            raise RuntimeError('GUI connection ended before readiness')
    finally:
        active = False
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def same_process(identity):
    current = monitor_process(identity['pid'])
    return all(current[key] == identity[key] for key in ('pid', 'birth', 'exe'))


def process_environment(pid):
    return dict(os.fsdecode(field).split('=', 1) for field in
                Path(f'/proc/{pid}/environ').read_bytes().split(b'\0') if b'=' in field)


def installed_native(config):
    """Use the existing native selection, without selecting or downloading a release."""
    target = (Path(config['codex_home']) / 'packages/app-server-daemon/current/codex').resolve(strict=True)
    # The ColdStart constructor verifies executable ownership, mode and type.
    cold()['MonitorColdStart'](config, [target])
    return target


def socket_identity(config):
    import stat
    alias = Path(config['_socket_alias'])
    ordinary = Path(config['codex_home']) / 'app-server-control/app-server-control.sock'
    if alias != ordinary:
        raise RuntimeError('O lançador requer o endereço padrão do servidor nativo neste CODEX_HOME.')
    endpoint = alias.resolve(strict=True)
    directory = Path('/tmp') / ('codex-daemon-' + str(os.getuid()))
    import re
    if endpoint.parent != directory or not re.fullmatch('[a-f0-9]{64}', endpoint.name):
        raise RuntimeError('O endereço do servidor nativo não corresponde ao gerenciador instalado.')
    monitor_private(directory, directory=True)
    meta = endpoint.lstat()
    if not stat.S_ISSOCK(meta.st_mode) or meta.st_uid != os.getuid():
        raise RuntimeError('O endereço nativo não é um socket Unix do usuário atual.')
    return str(endpoint), [meta.st_dev, meta.st_ino]


def native_owner(config):
    """Authenticate an independent managed native process; no GUI ancestry is required."""
    import socket
    import struct
    endpoint, identity = socket_identity(config)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(config['native_timeout'])
        connection.connect(endpoint)
        pid, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    native = monitor_process(pid)
    executable = installed_native(config)
    executable_identity = list(cold()['MonitorColdStart'].file_identity(executable.stat()))
    if list(cold()['MonitorColdStart'].file_identity(Path(f'/proc/{pid}/exe').stat())) != executable_identity:
        raise RuntimeError('O executável do servidor não corresponde à instalação atual.')
    environment = process_environment(pid)
    expected = {
        'CODEX_HOME': config['codex_home'],
        'CODEX_APP_TOOLS_PIPE_PATH': str(monitor_app_tools_directory(config) / 'host.sock'),
        'CODEX_MONITOR_LAUNCHER_PROTOCOL': '1',
    }
    if (uid != os.getuid() or native['exe'] != str(executable)
            or any(environment.get(key) != value for key, value in expected.items())
            or b'app-server' not in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')):
        raise RuntimeError('O servidor aberto usa a configuração anterior ou outra instalação. '
                           'Termine os trabalhos e feche o Codex normalmente; depois abra Codex Monitor.')
    import tomllib
    data = tomllib.loads((Path(config['codex_home']) / 'config.toml').read_text())
    for path in MONITOR_BOOTSTRAP_OPTIONS:
        value = data
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if value is not True:
            raise RuntimeError('O servidor aberto não habilitou as ferramentas necessárias à interface.')
    if socket_identity(config) != (endpoint, identity) or not same_process(native):
        raise RuntimeError('A identidade do servidor mudou durante a verificação; tente novamente.')
    return {'version': 1, 'codex_home': config['codex_home'], 'socket': endpoint,
            'native': native, 'native_executable': executable_identity, 'socket_identity': identity}


def monitor_shared_owner(config):
    try:
        receipt = native_owner(config)
        recorded = support()['monitor_shared_runtime'](config) / 'ready.json'
        monitor_private(recorded)
        saved = json.loads(recorded.read_text())
        if saved != receipt:
            raise RuntimeError('O registro do servidor mudou; abra codex-monitor para verificar a conexão.')
        support()['mq_health_signal'](config, 'native:shared',
            message='A conexão com o servidor compartilhado foi validada novamente.')
        return receipt
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        failure = RuntimeError('Servidor compartilhado indisponível: ' + str(error))
        support()['mq_health_signal'](config, 'native:shared', error=error,
            kind='Conexão do Codex indisponível', message=str(failure))
        failure.health_reported = True
        raise failure from error


def monitor_shared_peer(config, connection):
    import socket
    import struct
    receipt = monitor_shared_owner(config)
    peer = connection.transport.get_extra_info('socket')
    if peer is None:
        raise RuntimeError('A conexão nativa não expôs sua identidade Unix.')
    pid, uid, _ = struct.unpack('3i', peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if uid != os.getuid() or pid != receipt['native']['pid']:
        raise RuntimeError('A conexão pertence a outro servidor nativo.')
    return receipt


def websockets_connect():
    try:
        from websockets.client import unix_connect
        return unix_connect
    except ImportError as error:
        raise RuntimeError('A conexão compartilhada requer websockets; em ~/scripts, '
                           'execute poetry install --with monitor-tools.') from error


async def native_rpc(config, methods, *, unpublished=None):
    connect = websockets_connect()
    owner = unpublished or monitor_shared_owner(config)
    def verify(connection):
        import socket
        import struct
        current = native_owner(config) if unpublished else monitor_shared_owner(config)
        if current != owner:
            raise RuntimeError('O servidor mudou durante a comunicação.')
        peer = connection.transport.get_extra_info('socket')
        pid, uid, _ = struct.unpack('3i', peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if (pid, uid) != (owner['native']['pid'], os.getuid()):
            raise RuntimeError('A resposta veio de outro servidor nativo.')
    async with connect(owner['socket'], compression=None, open_timeout=config['native_timeout'],
                       close_timeout=3, max_size=MONITOR_RELAY_LIMIT, max_queue=4) as connection:
        verify(connection)
        async def request(key, method, params):
            verify(connection)
            await connection.send(json.dumps({'id': key, 'method': method, 'params': params}))
            while True:
                raw = await asyncio.wait_for(connection.recv(), config['native_timeout'])
                result = json.loads(raw)
                if result.get('id') == key and 'method' not in result:
                    if 'error' in result:
                        raise RuntimeError('O servidor recusou ' + method + ': ' + str(result['error'].get('message', 'erro nativo')))
                    return result['result']
                if 'method' in result and 'id' in result:
                    # This read-only client cannot answer an interactive server request.
                    raise RuntimeError('O servidor pediu uma resposta interativa ao verificador de conexão.')
        await request('init', 'initialize', {'clientInfo': {'name': 'codex-monitor-launcher',
            'version': '1'}, 'capabilities': {'experimentalApi': True}})
        await connection.send(json.dumps({'method': 'initialized', 'params': {}}))
        results = []
        for index, (method, params) in enumerate(methods):
            results.append(await request(index, method, params))
        verify(connection)
        return results


def verify_effective(config, owner):
    result, = asyncio.run(native_rpc(config, [('config/read', {'includeLayers': True})], unpublished=owner))
    for path in MONITOR_BOOTSTRAP_OPTIONS:
        value = result.get('config')
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if value is not True:
            raise RuntimeError('Outra camada da configuração desabilitou ' + '.'.join(path) +
                               '. O servidor foi preservado; confira a configuração antes de continuar.')


def ensure_server_once(config, codex):
    """Serialize attach/start using the same cold exclusion as the config writer."""
    import subprocess
    runtime = support()['monitor_shared_runtime'](config, create=True)
    # Classify attach/cold state and prepare under one uninterrupted coordinator lock.
    authority = cold()['MonitorColdStart'](config, [codex, installed_native(config)])
    try:
        authority.runtime = runtime
        authority.coordinator = authority.lock_file(runtime / 'launch.lock', private=True)
        alias = Path(config['_socket_alias'])
        if alias.exists():
            owner = native_owner(config)
            verify_effective(config, owner)
            monitor_runtime_write(runtime / 'ready.json', owner)
            return owner, False, None
        authority.acquire_native_exclusion()
        prepared = monitor_prepare_bootstrap(authority)
        tools = monitor_app_tools_directory(config, create=True)
        environment = clean_environment()
        environment.update({'CODEX_HOME': config['codex_home'],
            'CODEX_APP_TOOLS_PIPE_PATH': str(tools / 'host.sock'),
            'CODEX_MONITOR_LAUNCHER_PROTOCOL': '1',
            'CODEX_MCP_NODE_PATH': str(codex.parent / 'cua_node/bin/node'),
            'CODEX_ELECTRON_RESOURCES_PATH': str(codex.parent), 'CODEX_CLI_PATH': str(codex)})
        node = Path(environment['CODEX_MCP_NODE_PATH'])
        if not node.is_file() or not os.access(node, os.X_OK):
            raise RuntimeError('O runtime Node das ferramentas do aplicativo não foi encontrado.')
        before = installed_native(config)
        authority.before_native_start()
        started = subprocess.run([str(codex), 'app-server', 'daemon', 'start'], env=environment,
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=config['native_timeout'])
        if started.returncode:
            raise RuntimeError('O gerenciador nativo não iniciou o servidor: ' + started.stderr.strip()[-2000:])
        info = json.loads(started.stdout)
        owner = native_owner(config)
        if owner['native']['pid'] != info['pid'] or installed_native(config) != before:
            raise RuntimeError('A seleção nativa mudou durante a abertura. O servidor foi preservado; confira a instalação.')
        verify_effective(config, owner)
        # Native management now owns its control directories and may change their
        # modes. Our remaining authority is only the unchanged coordinator lock.
        monitor_private(authority.home, directory=True)
        for lock_path, descriptor, identity in authority.descriptors:
            if (authority.file_identity(os.fstat(descriptor)) != identity
                    or authority.file_identity(lock_path.lstat()) != identity):
                raise RuntimeError('A reserva de abertura mudou durante o início do servidor.')
        for executable, identity in authority.native.items():
            if authority.file_identity(Path(executable).stat()) != identity:
                raise RuntimeError('O executável nativo mudou durante a abertura.')
        monitor_runtime_write(runtime / 'ready.json', owner)
        return owner, True, prepared['backup']

    finally:
        authority.__exit__(None, None, None)


def ensure_server(config, codex):
    import time
    deadline = time.monotonic() + config['native_timeout']
    while True:
        try:
            return ensure_server_once(config, codex)
        except BlockingIOError as error:
            if time.monotonic() >= deadline:
                raise RuntimeError('Outra abertura do servidor ainda está em andamento. Tente novamente em instantes.') from error
            time.sleep(.1)


def clean_environment():
    # Preserve ordinary desktop/session context, never a caller's tools pipe or verification identity.
    names = {'PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LANGUAGE', 'TERM', 'COLORTERM',
        'DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR',
        'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME', 'XDG_CURRENT_DESKTOP',
        'XDG_SESSION_TYPE', 'XDG_SESSION_ID', 'XDG_SESSION_DESKTOP', 'DESKTOP_SESSION', 'GDK_BACKEND', 'GTK_THEME',
        'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy',
        'CODEX_ELECTRON_USER_DATA_PATH'}
    return {key: value for key, value in os.environ.items() if key in names or key.startswith('LC_')}


def message(text, *, gui=False, error=False):
    import shutil
    import subprocess
    print(('Codex Monitor: ' if not error else 'Codex Monitor — falha: ') + text, file=sys.stderr, flush=True)
    if gui:
        program = shutil.which('zenity' if error else 'notify-send')
        if program:
            arguments = ([program, '--error', '--title=Codex Monitor', '--text=' + text]
                         if error else [program, '--app-name=Codex Monitor', 'Codex Monitor', text])
            result = subprocess.run(arguments, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True)
            if result.returncode:
                print('Não foi possível mostrar a mensagem na área de trabalho: ' + result.stderr.strip(), file=sys.stderr)


def focus_gui(gui):
    import shutil
    import subprocess
    if not same_process(gui):
        raise RuntimeError('A interface registrada já terminou.')
    wmctrl = shutil.which('wmctrl')
    if not wmctrl:
        raise RuntimeError('O Codex já está aberto, mas wmctrl não está disponível para trazer sua janela à frente.')
    result = subprocess.run([wmctrl, '-lp'], capture_output=True, text=True, check=True)
    windows = [line.split()[0] for line in result.stdout.splitlines()
               if len(line.split()) >= 3 and line.split()[2] == str(gui['pid'])]
    if not windows or not same_process(gui):
        raise RuntimeError('O Codex já está aberto, mas sua janela ainda não está disponível para receber foco.')
    subprocess.run([wmctrl, '-ia', windows[0]], check=True)


def existing_gui(config, app):
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            try:
                arguments = (entry / 'cmdline').read_bytes().split(b'\0')
            except PermissionError as error:
                if (entry / 'comm').read_text().strip() != app.name:
                    continue
                raise RuntimeError('Não foi possível verificar o aplicativo Codex já aberto.') from error
            if (not arguments[0] or Path(os.fsdecode(arguments[0])).name != app.name
                    or any(word.startswith(b'--type=') for word in arguments)):
                continue
            try:
                process = monitor_process(int(entry.name))
            except RuntimeError:
                fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
                if fields[0] in {'Z', 'X'}:
                    continue
                raise
            if process['exe'] != str(app):
                continue
            try:
                environment = process_environment(process['pid'])
                import pwd
                account_home = environment.get('HOME') or pwd.getpwuid(os.getuid()).pw_dir
                selected = Path(environment.get('CODEX_HOME') or str(Path(account_home) / '.codex'))
            except (PermissionError, KeyError) as error:
                raise RuntimeError('Não foi possível verificar a configuração do Codex já aberto.') from error
            if not selected.is_absolute():
                selected = (entry / 'cwd').resolve(strict=True) / selected
            if selected.resolve() == Path(config['codex_home']):
                yield process
        except (FileNotFoundError, ProcessLookupError):
            continue


def verify_existing_gui(config, runtime, app):
    launch_path = runtime / 'launch.json'
    known = None
    if launch_path.exists():
        monitor_private(launch_path)
        launch = json.loads(launch_path.read_text())
        if launch.get('app') == str(app) and launch.get('codex_home') == config['codex_home']:
            known = launch.get('gui')
    for gui in existing_gui(config, app):
        if not known or gui['pid'] != known['pid'] or gui['birth'] != known['birth']:
            raise RuntimeError('O aplicativo já está aberto fora deste lançador. '
                               'Termine os trabalhos e feche-o normalmente antes de usar o atalho.')


def _monitor_launch_app(config, path, app, codex, app_args):
    import fcntl
    app, codex = Path(app).resolve(strict=True), Path(codex).resolve(strict=True)
    runtime = support()['monitor_shared_runtime'](config, create=True)
    verify_existing_gui(config, runtime, app)
    owner, created, backup = ensure_server(config, codex)
    descriptor = os.open(runtime / 'gui.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        monitor_private(runtime / 'gui.lock')
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Outra abertura da interface ainda está em andamento. Tente novamente em instantes.') from error
        launch_path = runtime / 'launch.json'
        if launch_path.exists():
            monitor_private(launch_path)
            old = json.loads(launch_path.read_text())
            try:
                gui = monitor_process(old['gui']['pid'])
            except (FileNotFoundError, ProcessLookupError, RuntimeError):
                gui = None
            if gui and gui['birth'] == old['gui']['birth']:
                if gui['exe'] != str(app) or old.get('codex_home') != config['codex_home']:
                    raise RuntimeError('Outra abertura do Codex ainda está em andamento.')
                focus_gui(gui)
                message('O Codex já estava aberto. A janela foi trazida à frente.', gui=True)
                return
        verify_existing_gui(config, runtime, app)
        wrapper = runtime / 'codex-proxy'
        temporary = runtime / ('wrapper-' + monitor_id())
        try:
            with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700), 'w') as stream:
                stream.write(f'#!{sys.executable}\nimport runpy\nraise SystemExit(runpy.run_path('
                             f'{str(Path(__file__).resolve())!r})["monitor_app_proxy_main"]())\n')
            os.replace(temporary, wrapper)
        finally:
            temporary.unlink(missing_ok=True)
        launch = {'gui': monitor_process(os.getpid()), 'app': str(app), 'codex': str(codex),
                  'config': str(path), 'codex_home': config['codex_home'], 'wrapper': str(wrapper)}
        monitor_runtime_write(launch_path, launch)
        environment = clean_environment()
        environment.update(CODEX_HOME=config['codex_home'], CODEX_CLI_PATH=str(wrapper),
                           CODEX_STATS_APP_LAUNCH=str(launch_path))
        if created:
            message('Servidor compartilhado iniciado. A interface está abrindo.' +
                    (' A configuração foi preparada; uma cópia anterior foi guardada em ' + str(backup) + '.' if backup else ''), gui=True)
        os.execve(app, [str(app), *app_args], environment)
    finally:
        os.close(descriptor)


def _monitor_launch_cli(config, codex, cli, arguments):
    codex, cli = Path(codex).resolve(strict=True), Path(cli).resolve(strict=True)
    # An alternate endpoint would defeat sharing. Native flags for prompts/cwd remain untouched.
    if any(word == '--remote' or word.startswith('--remote=') for word in arguments):
        raise RuntimeError('codex-monitor escolhe o servidor compartilhado; remova a opção --remote.')
    owner, created, backup = ensure_server(config, codex)
    if created:
        message('Servidor compartilhado iniciado. A CLI e a interface poderão usá-lo.')
    if backup:
        message('Configuração preparada. Cópia anterior: ' + str(backup))
    environment = dict(os.environ)
    environment['CODEX_HOME'] = config['codex_home']
    for key in ('CODEX_CLI_PATH', 'CODEX_STATS_APP_LAUNCH'):
        environment.pop(key, None)
    os.execve(cli, [str(cli), '--remote', 'unix://' + owner['socket'], *arguments], environment)


async def reload_tools(config):
    await native_rpc(config, [('config/mcpServer/reload', None), ('mcpServerStatus/list', {})])
    # Reload is asynchronous in the installed native. Observe the actual server state.
    deadline = asyncio.get_running_loop().time() + config['native_timeout']
    while True:
        result, = await native_rpc(config, [('mcpServerStatus/list', {})])
        app = next((item for item in result.get('data', []) if item.get('name') == 'codex_app'), {})
        # Native aggregate inventory omits runtimeStatus; a thread-scoped query
        # supplies it. A fresh installed-plugin catalog is available in both forms.
        if (app.get('runtimeStatus') in {None, 'connected'} and isinstance(app.get('tools'), dict)
                and app['tools'] and app.get('toolsError') is None
                and app.get('pluginId') == 'codex-app-tools@openai-bundled'):
            return
        if asyncio.get_running_loop().time() >= deadline:
            raise RuntimeError('A interface conectou, mas suas ferramentas ainda estão indisponíveis. '
                               'Feche e reabra a interface normalmente para tentar de novo. O servidor foi preservado.')
        await asyncio.sleep(1)
        if app.get('runtimeStatus') == 'failed' or app.get('toolsError') is not None:
            # The renderer may not expose its catalog at the first GUI RPC.
            # Refresh failed startup only; this never replays an app-tool call.
            await native_rpc(config, [('config/mcpServer/reload', None)])


def monitor_app_proxy_main():
    import signal
    binding, directory = None, None
    async def relay(config, launch, parent):
        nonlocal binding, directory
        owner = monitor_shared_owner(config)
        directory = monitor_app_tools_directory(config)
        binding = monitor_app_tools_bind(directory, Path(os.environ['CODEX_APP_TOOLS_PIPE_PATH']),
                                         parent, monitor_process(os.getpid()), monitor_id())
        connect = websockets_connect()
        tasks = []
        try:
            async with connect(owner['socket'], compression=None, open_timeout=config['native_timeout'],
                               close_timeout=3, max_size=MONITOR_RELAY_LIMIT, max_queue=4) as connection:
                def verify():
                    if not same_process(parent) or monitor_shared_peer(config, connection) != owner:
                        raise RuntimeError('A interface ou seu servidor mudou durante a conexão.')
                reader = asyncio.StreamReader(limit=MONITOR_RELAY_LIMIT + 1)
                loop = asyncio.get_running_loop()
                transport, _ = await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin.buffer)
                output, protocol = await loop.connect_write_pipe(lambda: asyncio.streams.FlowControlMixin(loop=loop), sys.stdout.buffer)
                writer = asyncio.StreamWriter(output, protocol, None, loop)
                handshake = loop.create_future()
                async def tools_ready():
                    receipt = await handshake
                    await reload_tools(config)
                    verify()
                    monitor_runtime_write(support()['monitor_shared_runtime'](config) / 'gui-ready.json',
                        {'gui': parent, 'proxy': monitor_process(os.getpid()), 'native': owner['native'],
                         'binding': binding, 'handshake': receipt})
                    await asyncio.to_thread(message,
                        'Interface conectada ao servidor compartilhado. Ferramentas do aplicativo disponíveis.', gui=True)
                protocol_task = asyncio.create_task(monitor_relay_protocol(connection, reader, writer,
                    verify=verify, on_ready=handshake.set_result, timeout=config['native_timeout']))
                tools_task = asyncio.create_task(tools_ready())
                tasks.extend([protocol_task, tools_task])
                try:
                    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    if tools_task in done:
                        try:
                            tools_task.result()
                        except Exception as error:
                            monitor_runtime_write(support()['monitor_shared_runtime'](config) / 'gui-error.json',
                                {'gui': parent, 'phase': 'tools', 'message': str(error)})
                            await asyncio.to_thread(message, str(error), gui=True, error=True)
                    await protocol_task
                finally:
                    transport.close()
                    writer.close()
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    try:
        launch_path = Path(os.environ['CODEX_STATS_APP_LAUNCH'])
        monitor_private(launch_path)
        launch = json.loads(launch_path.read_text())
        config = support()['mq_config'](Path(launch['config']))
        runtime = support()['monitor_shared_runtime'](config)
        if launch_path != runtime / 'launch.json':
            raise RuntimeError('O descritor de abertura não pertence a este Codex Monitor.')
        parent = monitor_process(os.getppid())
        main = (parent['pid'] == launch['gui']['pid'] and parent['birth'] == launch['gui']['birth']
            and parent['exe'] == launch['app'] and os.environ.get('CODEX_HOME') == launch['codex_home']
            and os.environ.get('CODEX_INTERNAL_ORIGINATOR_OVERRIDE') == 'Codex Desktop'
            and support()['monitor_main_bootstrap'](sys.argv[1:]))
        if 'app-server' in sys.argv[1:]:
            monitor_runtime_write(runtime / 'proxy-start.json', {'main': main, 'parent': parent,
                'reserved_gui': launch['gui'], 'home_matches': os.environ.get('CODEX_HOME') == launch['codex_home'],
                'originator_matches': os.environ.get('CODEX_INTERNAL_ORIGINATOR_OVERRIDE') == 'Codex Desktop',
                'bootstrap_matches': support()['monitor_main_bootstrap'](sys.argv[1:])})
        if not main:
            environment = dict(os.environ)
            environment.pop('CODEX_STATS_APP_LAUNCH', None)
            environment['CODEX_CLI_PATH'] = launch['codex']
            os.execve(launch['codex'], [launch['codex'], *sys.argv[1:]], environment)
        asyncio.run(relay(config, launch, parent))
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        message(str(error), gui=True, error=True)
        return 1
    finally:
        if binding is not None:
            try:
                monitor_app_tools_unbind(directory, binding)
                ready = support()['monitor_shared_runtime'](config) / 'gui-ready.json'
                if ready.exists():
                    monitor_private(ready)
                    saved = json.loads(ready.read_text())
                    if saved.get('binding') == binding:
                        ready.unlink()
            except Exception as error:
                print('Codex Monitor: falha ao remover a conexão encerrada: ' + str(error), file=sys.stderr)


def launch_operation(function, *arguments):
    import subprocess
    try:
        return function(*arguments)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('O gerenciador nativo não confirmou a abertura no prazo. '
                           'O servidor pode ter iniciado; ele foi preservado. Tente abrir novamente '
                           'para verificar a conexão antes de executar qualquer parada.') from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError('Não foi possível trazer a janela do Codex à frente. '
                           'O aplicativo e seus trabalhos foram preservados.') from error
    except (OSError, ValueError, KeyError, RuntimeError):
        raise
    except Exception as error:
        # Transport-library exceptions are command-local and must use the same user-facing channel.
        raise RuntimeError('A conexão de abertura falhou (' + type(error).__name__ + '). '
                           'O servidor e os trabalhos foram preservados; tente novamente.') from error


def monitor_launch_app(config, path, app, codex, app_args):
    return launch_operation(_monitor_launch_app, config, path, app, codex, app_args)


def monitor_launch_cli(config, codex, cli, arguments):
    return launch_operation(_monitor_launch_cli, config, codex, cli, arguments)
