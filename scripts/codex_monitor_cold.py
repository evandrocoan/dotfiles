"""Shared cold native ownership and configuration-reading primitives.

Importing this module does not load optional monitor packages or touch runtime state.
The existing standalone monitor remains the owner of generic identity helpers.
"""
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import runpy


@lru_cache(maxsize=1)
def _monitor_support():
    return runpy.run_path(str(Path(__file__).resolve().parent.parent / ".local/bin/codex-session-stats"))


class MonitorColdStart:
    """The shared backend's cold-start slice; never adopts or stops a server."""

    def __init__(self, config, native_paths):
        import stat
        support = _monitor_support()
        self.private = support["monitor_private"]
        self.process = support["monitor_process"]
        self.shared_runtime = support["monitor_shared_runtime"]
        self.config = config
        self.home = Path(config['codex_home'])
        if (not self.home.is_absolute() or self.home.resolve(strict=True) != self.home
                or self.home != Path(os.path.normpath(str(self.home)))):
            raise RuntimeError('cold start requires the canonical selected Codex home')
        self.private(self.home, directory=True)
        self.native = {}
        for path in native_paths:
            path = Path(path).resolve(strict=True)
            meta = path.stat()
            regular_file = stat.S_ISREG(meta.st_mode)
            trusted_owner = meta.st_uid in {0, os.getuid()}
            executable = os.access(path, os.X_OK)
            writable_bits = meta.st_mode & 0o022
            if not regular_file or not trusted_owner or not executable or writable_bits:
                raise RuntimeError('untrusted native executable for cold-start classification: '
                    f'path={str(path)!r}, uid={meta.st_uid}, current_uid={os.getuid()}, '
                    f'mode={stat.S_IMODE(meta.st_mode):#06o}, regular_file={regular_file}, '
                    f'trusted_owner={trusted_owner}, executable={executable}, '
                    f'writable_bits={writable_bits:#05o}')
            self.native[str(path)] = self.file_identity(meta)
        if not self.native:
            raise RuntimeError('cold start requires exact native executable identities')
        self.runtime = None
        self.coordinator = None
        self.native_locks = []
        self.descriptors = []
        self.control_directories = {}

    @staticmethod
    def file_identity(meta):
        return (meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid,
                meta.st_mode, meta.st_nlink, meta.st_size, meta.st_mtime_ns)

    def lock_file(self, path, *, private):
        import fcntl
        import stat
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            meta = os.fstat(descriptor)
            if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_nlink != 1
                    or private and meta.st_mode & 0o077
                    or self.file_identity(meta) != self.file_identity(path.lstat())):
                raise RuntimeError('cold-start lock must be an unchanged owned regular file')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.descriptors.append((path, descriptor, self.file_identity(meta)))
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def __enter__(self):
        try:
            self.runtime = self.shared_runtime(self.config, create=True)
            self.coordinator = self.lock_file(self.runtime / 'launch.lock', private=True)
            self.acquire_native_exclusion()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def acquire_native_exclusion(self):
        """Classify cold state without releasing the already held launch coordinator."""
        import stat
        if self.coordinator is None or self.native_locks:
            raise RuntimeError('native exclusion requires a held coordinator and no native locks')
        self.verify_coordinator()
        for relative in ('app-server-daemon', 'app-server-control'):
            directory = self.home / relative
            directory.mkdir(mode=0o700, exist_ok=True)
            meta = directory.lstat()
            # Native files can inherit a broader mode inside the private home. Never chmod
            # native-owned files or interpret a mode alone as proof of an active owner.
            if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != os.getuid():
                raise RuntimeError('native control directory must be owned and without symlinks')
            self.control_directories[directory] = (meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid, meta.st_mode)
        for path in (self.home / 'app-server-daemon/daemon.lock',
                     self.home / 'app-server-control/app-server-startup.lock'):
            self.native_locks.append(self.lock_file(path, private=False))
        self.verify()

    def __exit__(self, *_):
        for _, descriptor, _ in reversed(self.descriptors):
            os.close(descriptor)
        self.descriptors.clear()
        self.native_locks.clear()
        self.coordinator = None

    def read_record(self, path, *, private=False):
        import stat
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor, 'rb') as stream:
            meta = os.fstat(stream.fileno())
            if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_nlink != 1
                    or private and meta.st_mode & 0o077):
                raise RuntimeError('unsafe cold-start process record')
            value = stream.read(65537)
            if len(value) > 65536:
                raise RuntimeError('cold-start process record exceeds 64 KiB')
            if self.file_identity(meta) != self.file_identity(path.lstat()):
                raise RuntimeError('cold-start process record changed while reading')
        result = json.loads(value)
        if not isinstance(result, dict):
            raise RuntimeError('invalid cold-start process record')
        return result

    def live_process(self, pid):
        if type(pid) is not int or pid <= 0:
            raise RuntimeError('invalid cold-start process identity')
        try:
            root = Path('/proc') / str(pid)
            fields = (root / 'stat').read_text().rsplit(')', 1)[1].split()
            if fields[0] in {'Z', 'X'}:
                return None
            return self.process(pid)
        except (FileNotFoundError, ProcessLookupError):
            return None

    def verify_coordinator(self):
        if self.coordinator is None:
            raise RuntimeError('cold-start exclusion is not held')
        self.private(self.home, directory=True)
        for path, identity in self.control_directories.items():
            meta = path.lstat()
            if (meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid, meta.st_mode) != identity:
                raise RuntimeError('native control directory identity changed')
        for path, descriptor, identity in self.descriptors:
            if (self.file_identity(os.fstat(descriptor)) != identity
                    or self.file_identity(path.lstat()) != identity):
                raise RuntimeError('cold-start lock identity changed')
        for path, identity in self.native.items():
            if self.file_identity(Path(path).stat()) != identity:
                raise RuntimeError('native executable changed during cold-start preparation')

    def verify(self):
        import stat
        if len(self.native_locks) != 2:
            raise RuntimeError('cold-start exclusion is not held')
        self.verify_coordinator()
        alias = Path(self.config['_socket_alias'])
        expected = self.home / 'app-server-control/app-server-control.sock'
        if alias != expected:
            raise RuntimeError('managed cold start requires its ordinary native control alias')
        try:
            meta = alias.lstat()
        except FileNotFoundError:
            meta = None
        if meta is not None:
            if not stat.S_ISLNK(meta.st_mode) or meta.st_uid != os.getuid():
                raise RuntimeError('native endpoint exists or its alias is unverified')
            endpoint = alias.resolve(strict=False)
            native_directory = Path('/tmp') / ('codex-daemon-' + str(os.getuid()))
            if (endpoint.parent != native_directory
                    or not re.fullmatch(r'[a-f0-9]{64}', endpoint.name)):
                raise RuntimeError('native alias has an unexpected destination')
            try:
                self.private(native_directory, directory=True)
            except FileNotFoundError:
                # Reboot can remove the native temporary directory while leaving
                # its persistent alias. Remaining owner checks still apply.
                pass
            if endpoint.exists() or endpoint.is_symlink():
                raise RuntimeError('native endpoint already exists; cold preparation denied')
        if Path(self.config['socket']).exists():
            raise RuntimeError('configured native endpoint already exists; cold preparation denied')
        for name in ('daemon.pid', 'app-server.pid'):
            record = self.read_record(self.home / 'app-server-daemon' / name)
            if record is not None and self.live_process(record.get('pid')) is not None:
                raise RuntimeError('native PID record refers to a live or uncertain owner')
        for name in ('launch.json', 'ready.json'):
            record = self.read_record(self.runtime / name, private=True)
            if record is None:
                continue
            if record.get('codex_home') != str(self.home):
                raise RuntimeError('shared launch record has another home or is incomplete')
            identities = [record[role] for role in ('gui', 'proxy', 'native') if role in record]
            if not identities:
                raise RuntimeError('shared launch record lacks process identities')
            for identity in identities:
                if not isinstance(identity, dict) or not isinstance(identity.get('birth'), str):
                    raise RuntimeError('shared launch record has an invalid process identity')
                current = self.live_process(identity.get('pid'))
                if current is not None and current['birth'] == identity['birth']:
                    raise RuntimeError('a shared GUI/native launch is still live or pending')
        owners = self.native_owners()
        if owners:
            kind = 'installed native' if owners[0]['exe'] in self.native else 'unknown'
            raise RuntimeError('an ' + kind + ' app-server start is live or pending '
                               f'(PID {owners[0]["pid"]})')

    def native_owners(self):
        owners = []
        # A possible app-server using this home blocks effects before its endpoint/PID
        # appears. An unknown executable is a denial too, never an adoption by name.
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                # The installed CLI's server contract includes this exact argv word.
                # Unrelated nondumpable same-UID processes (for example systemd) need
                # not expose their executable or environment to this classifier.
                arguments = (entry / 'cmdline').read_bytes().split(b'\0')
                if b'app-server' not in arguments:
                    continue
                current = self.live_process(int(entry.name))
                if current is None:
                    continue
                executable = str((entry / 'exe').resolve(strict=True))
                raw_environment = (entry / 'environ').read_bytes()
                environment = dict(value.split(b'=', 1) for value in
                    raw_environment.split(b'\0') if b'=' in value)
                selected = os.fsdecode(environment.get(b'CODEX_HOME',
                    environment.get(b'HOME', b'') + b'/.codex'))
                selected = Path(selected)
                if not selected.is_absolute():
                    selected = (entry / 'cwd').resolve(strict=True) / selected
                if selected.resolve(strict=False) == self.home:
                    if current['exe'] != executable:
                        raise RuntimeError('native process changed during classification')
                    # The installed updater survives daemon stop. Its server
                    # restarts are serialized by the native operation lock.
                    expected = self.native.get(executable)
                    if (arguments[1:] == [b'app-server', b'daemon', b'pid-update-loop', b'']
                            and self.file_identity((entry / 'exe').stat()) == expected):
                        if ((entry / 'cmdline').read_bytes().split(b'\0') != arguments
                                or (entry / 'environ').read_bytes() != raw_environment
                                or self.live_process(current['pid']) != current
                                or self.file_identity((entry / 'exe').stat()) != expected):
                            raise RuntimeError('native updater identity changed during classification')
                        continue
                    owners.append(current)
            except (FileNotFoundError, ProcessLookupError):
                continue
            except PermissionError as error:
                raise RuntimeError('native cold-start process classification is unreadable') from error
        return owners

    def process_family(self, leader):
        """Observe this private native session and descendants without signaling them."""
        records = {}
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
                if fields[0] not in {'Z', 'X'}:
                    records[int(entry.name)] = (int(fields[1]), int(fields[3]), fields[19])
            except (FileNotFoundError, ProcessLookupError):
                continue
        if leader['pid'] in records and records[leader['pid']][2] != leader['birth']:
            raise RuntimeError('temporary reader PID was reused; ownership is unknown')
        members = {leader['pid']}
        while True:
            added = {pid for pid, (parent, session, _) in records.items()
                     if parent in members or session == leader['pid']}
            if added <= members:
                break
            members.update(added)
        result = []
        for pid in sorted(members & records.keys()):
            current = self.live_process(pid)
            if current is not None:
                if current['birth'] != records[pid][2]:
                    raise RuntimeError('temporary reader family changed during observation')
                result.append(current)
        return result

    def before_native_start(self):
        """Release native locks before native management reacquires them; retain our authority."""
        self.verify()
        retained = []
        for record in self.descriptors:
            if record[1] in self.native_locks:
                os.close(record[1])
            else:
                retained.append(record)
        self.descriptors = retained
        self.native_locks.clear()

    def after_native_stop(self):
        """Restore full exclusion; this never stops or adopts a native process."""
        import stat
        self.verify_coordinator()
        if self.native_locks:
            raise RuntimeError('native exclusion is already held')
        baseline = len(self.descriptors)
        try:
            for relative in ('app-server-daemon', 'app-server-control'):
                meta = (self.home / relative).lstat()
                if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != os.getuid():
                    raise RuntimeError('native control directory must be owned and without symlinks')
            for path in (self.home / 'app-server-daemon/daemon.lock',
                         self.home / 'app-server-control/app-server-startup.lock'):
                self.native_locks.append(self.lock_file(path, private=False))
            self.verify()
        except BaseException:
            for _, descriptor, _ in reversed(self.descriptors[baseline:]):
                os.close(descriptor)
            del self.descriptors[baseline:]
            self.native_locks.clear()
            raise


def monitor_read_cold_native(authority, native, contexts, *, environment, evidence, timeout=30):
    """Query an exclusively owned native child; restore exclusion before returning."""
    import selectors
    import subprocess
    import time

    if not isinstance(authority, MonitorColdStart):
        raise RuntimeError('native reader requires the real cold-start owner')
    authority.verify()
    native = Path(native).resolve(strict=True)
    if str(native) not in authority.native:
        raise RuntimeError('native reader executable is not sealed by the cold owner')
    contexts = [Path(path) for path in contexts]
    if (not contexts or any(not path.is_absolute() or path.resolve(strict=True) != path
                            or not path.is_dir() for path in contexts)):
        raise RuntimeError('native reader requires canonical existing contexts')
    if environment.get('CODEX_HOME') != str(authority.home):
        raise RuntimeError('native reader environment selects another home')
    evidence = Path(evidence)
    authority.private(evidence, directory=True)
    if any(evidence.iterdir()):
        raise RuntimeError('native reader requires a fresh private evidence directory')

    def private_file(name, binary=False):
        descriptor = os.open(evidence / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600)
        return os.fdopen(descriptor, 'wb' if binary else 'w')

    process = None
    identity = None
    failure = None
    result = {'native_started': False, 'native_terminated': False, 'locks_reacquired': False}
    messages = []
    selector = selectors.DefaultSelector()
    buffer = bytearray()
    deadline = time.monotonic() + timeout
    counter = 0
    descendants = {}

    def endpoint_state():
        import stat
        states = []
        for name in ('socket', '_socket_alias'):
            path = Path(authority.config[name])
            try:
                meta = path.lstat()
            except FileNotFoundError:
                states.append(None)
                continue
            states.append((authority.file_identity(meta), meta.st_ctime_ns,
                           os.readlink(path) if stat.S_ISLNK(meta.st_mode) else None))
        return states

    endpoints = endpoint_state()

    def verify_endpoints():
        if endpoint_state() != endpoints:
            raise RuntimeError('temporary native reader changed a shared endpoint identity')

    def owner():
        authority.verify_coordinator()
        if process.poll() is not None or authority.process(process.pid) != identity:
            raise RuntimeError('temporary native reader identity is no longer live')
        owners = authority.native_owners()
        if owners != [identity]:
            raise RuntimeError('temporary native reader is not the sole native owner')
        verify_endpoints()
        for name in ('socket', '_socket_alias'):
            if Path(authority.config[name]).exists():
                raise RuntimeError('temporary native reader exposed a shared native endpoint')
        for member in authority.process_family(identity):
            if member['pid'] != identity['pid']:
                descendants[(member['pid'], member['birth'])] = member

    def send(value):
        process.stdin.write(json.dumps(value).encode() + b'\n')
        process.stdin.flush()

    def receive():
        while b'\n' not in buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise TimeoutError('temporary native reader response timed out')
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('temporary native reader closed before its response')
            buffer.extend(chunk)
            if len(buffer) > 64 * 1024 * 1024:
                raise RuntimeError('temporary native reader response exceeds 64 MiB')
        line, _, rest = buffer.partition(b'\n')
        buffer[:] = rest
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError('temporary native reader emitted a non-object message')
        messages.append(value)
        if len(messages) > 10000:
            raise RuntimeError('temporary native reader exceeded its message bound')
        return value

    def rpc(method, params):
        nonlocal counter
        owner()
        counter += 1
        send({'id': counter, 'method': method, 'params': params})
        while True:
            value = receive()
            if value.get('id') == counter and 'method' not in value:
                owner()
                if 'error' in value:
                    raise RuntimeError('temporary native ' + method + ' rejected (code '
                                       + str(value['error'].get('code')) + ')')
                if not isinstance(value.get('result'), dict):
                    raise RuntimeError('temporary native reader response is invalid')
                return value['result']
            if 'id' in value:
                raise RuntimeError('unexpected request or response during configuration-only read')

    try:
        with private_file('native.stderr', binary=True) as errors:
            authority.before_native_start()
            process = subprocess.Popen([str(native), 'app-server', '--stdio'],
                cwd=contexts[0], env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=errors, start_new_session=True)
            result['native_started'] = True
            identity = authority.process(process.pid)
            result['process'] = identity
            if identity['exe'] != str(native) or identity['parent'] != os.getpid():
                raise RuntimeError('temporary native reader is not the exact owned child')
            selector.register(process.stdout, selectors.EVENT_READ)
            initialized = rpc('initialize', {
                'clientInfo': {'name': 'codex_permission_config_reader', 'version': '1'},
                'capabilities': {'experimentalApi': True}})
            if initialized.get('codexHome') != str(authority.home):
                raise RuntimeError('temporary native reader initialized another home')
            send({'method': 'initialized', 'params': {}})
            result['initialization'] = initialized
            result['reports'] = [rpc('config/read', {'cwd': str(path), 'includeLayers': True})
                                 for path in contexts]
            result['requirements'] = rpc('configRequirements/read', {})
            owner()
    except BaseException as error:
        failure = error
    finally:
        selector.close()
        if process is not None:
            # EOF is the ordinary shutdown of this exact child's private stdin.
            try:
                process.stdin.close()
            except OSError as error:
                if failure is None:
                    failure = error
            try:
                result['exit_code'] = process.wait(timeout=timeout)
                result['leader_terminated'] = True
                alive = authority.process_family(identity) if identity is not None else []
                for member in descendants.values():
                    current = authority.live_process(member['pid'])
                    if current is not None and current['birth'] == member['birth'] and current not in alive:
                        alive.append(current)
                result['surviving_descendants'] = alive
                result['native_terminated'] = not alive
                if alive:
                    failure = RuntimeError('temporary native reader has surviving descendants; publication denied')
                verify_endpoints()
            except subprocess.TimeoutExpired:
                failure = RuntimeError('temporary native reader has not terminated; publication denied')
                result['exit_code'] = None
            except BaseException as error:
                result['native_terminated'] = False
                if failure is None:
                    failure = error
            finally:
                process.stdout.close()
        try:
            if authority.native_locks:
                authority.verify()
            else:
                authority.after_native_stop()
            result['locks_reacquired'] = True
        except BaseException as error:
            if failure is None:
                failure = error
        result['message_count'] = len(messages)
        try:
            with private_file('native.messages.json') as stream:
                json.dump(messages, stream)
            with private_file('reader.result.json') as stream:
                json.dump(result, stream)
        except BaseException as error:
            if failure is None:
                failure = error
    if failure is not None:
        failure.reader_state = result
        raise failure
    if result.get('exit_code') != 0:
        error = RuntimeError('temporary native reader exited unsuccessfully; publication denied')
        error.reader_state = result
        raise error
    authority.verify()
    return result


def monitor_config_snapshot(authority):
    """Read the selected config without following links; retain exact bytes/ctime."""
    import stat
    target = authority.home / 'config.toml'
    try:
        descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None, b''
    with os.fdopen(descriptor, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid()
                or meta.st_nlink != 1 or meta.st_mode & 0o022):
            raise RuntimeError('Codex config must be an owned single regular file without group/world writes')
        contents = stream.read(8 * 1024 * 1024 + 1)
        if len(contents) > 8 * 1024 * 1024:
            raise RuntimeError('Codex config exceeds the 8 MiB preparation limit')
        identity = authority.file_identity(meta) + (meta.st_ctime_ns,)
        for current in (os.fstat(stream.fileno()), target.lstat()):
            if authority.file_identity(current) + (current.st_ctime_ns,) != identity:
                raise RuntimeError('Codex config changed while reading; preparation refused')
    return identity, contents


def monitor_publish_config(authority, original, prepared, *, recheck=lambda: None):
    """Publish reviewed config bytes under real cold exclusion, never auto-rollback."""
    import stat
    import tempfile
    import uuid

    if not isinstance(authority, MonitorColdStart):
        raise RuntimeError('config publication requires the real cold-start authority')
    authority.verify()
    target = authority.home / 'config.toml'
    original_identity, contents = original
    state = {'changed': False, 'published': False, 'backup': None, 'backup_complete': False}

    def revalidate():
        authority.verify()
        recheck()
        if monitor_config_snapshot(authority) != original:
            raise RuntimeError('Codex config changed concurrently; preparation refused')

    revalidate()
    if contents == prepared:
        return state
    temporary = None
    directory = os.open(authority.home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        descriptor, name = tempfile.mkstemp(prefix='.config.toml.codex-monitor-', dir=authority.home)
        temporary = Path(name)
        with os.fdopen(descriptor, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            if original_identity is not None:
                os.fchown(stream.fileno(), -1, original_identity[3])
                os.fchmod(stream.fileno(), stat.S_IMODE(original_identity[4]))
            stream.write(prepared)
            stream.flush()
            os.fsync(stream.fileno())
            prepared_group = os.fstat(stream.fileno()).st_gid
        revalidate()
        if original_identity is not None:
            backup = authority.home / ('config.toml.before-monitor-' + uuid.uuid4().hex + '.bak')
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            state['backup'] = str(backup)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(directory)
            state['backup_complete'] = True
        revalidate()
        os.replace(temporary, target)
        state.update(changed=True, published=True)
        temporary = None
        os.fsync(directory)
        actual_identity, actual = monitor_config_snapshot(authority)
        expected_mode = stat.S_IMODE(original_identity[4]) if original_identity else 0o600
        if (actual != prepared or actual_identity is None
                or stat.S_IMODE(actual_identity[4]) != expected_mode
                or actual_identity[3] != prepared_group):
            raise RuntimeError('Codex config differs after publication; refusing another overwrite')
        return state
    except BaseException as error:
        error.publication_state = state
        if state['published']:
            failure = RuntimeError('The Codex configuration was written, but verification failed. '
                                   'Check the backup before trying again.')
            failure.publication_state = state
            raise failure from error
        raise
    finally:
        os.close(directory)
        if temporary is not None:
            temporary.unlink(missing_ok=True)
