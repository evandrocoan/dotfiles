"""Narrow permission migration preparation; no production activation on import."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tomllib

from codex_monitor_cold import MonitorColdStart, _monitor_support


PROFILE = 'local-workspace'
POLICY_KEYS = {'sandbox_mode', 'sandbox_workspace_write', 'default_permissions',
               'permissions', 'approval_policy', 'approvals_reviewer', 'profiles', 'profile'}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def semantic(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode())


def native_user_semantic(value, home):
    """Compare loaded user values without changing exact file/transform seals."""
    def numbers(item):
        if isinstance(item, dict):
            return {key: numbers(child) for key, child in item.items()}
        if isinstance(item, list):
            return [numbers(child) for child in item]
        # Do not coerce booleans, strings or large integers through float: that
        # would hide type differences or a rounded native numeric value.
        if type(item) is float and item.is_integer():
            return int(item)
        return item

    config = numbers(value)
    skills = config.get('skills')
    if isinstance(skills, dict) and isinstance(skills.get('config'), list):
        for skill in skills['config']:
            if isinstance(skill, dict) and isinstance(skill.get('path'), str):
                # Installed native versions resolve this typed path relative to
                # the declaring config.toml. Keep other strings untouched.
                skill['path'] = os.path.normpath(os.path.join(home, skill['path']))
    return semantic(config)


def transform(source):
    """Return only the reviewed mapping, preserving TOML trivia and unrelated values."""
    import copy
    import tomlkit

    before = tomllib.loads(source.decode('utf-8'))
    if (before.get('sandbox_mode') != 'workspace-write'
            or before.get('sandbox_workspace_write') != {'network_access': True}
            or type(before['sandbox_workspace_write']['network_access']) is not bool
            or 'default_permissions' in before
            or before.get('profiles') or before.get('profile')
            or not isinstance(before.get('permissions', {}), dict)
            or PROFILE in before.get('permissions', {})):
        raise RuntimeError('configuração fora do formato aprovado para migração')
    document = tomlkit.parse(source.decode('utf-8'))
    del document['sandbox_mode']
    # The current interactive CLI explicitly selects the legacy workspace mode.
    # Retain its existing network setting alongside the named server default.
    document['default_permissions'] = PROFILE
    if 'permissions' not in document:
        document['permissions'] = tomlkit.table()
    document['permissions'][PROFILE] = {
        'extends': ':workspace', 'network': {'enabled': True}}
    result = tomlkit.dumps(document).encode('utf-8')
    expected = copy.deepcopy(before)
    del expected['sandbox_mode']
    expected['default_permissions'] = PROFILE
    expected.setdefault('permissions', {})[PROFILE] = {
        'extends': ':workspace', 'network': {'enabled': True}}
    # Independent parser enforces the exact edit boundary. Reject special NaN values
    # rather than treating unequal values as proof that unrelated content survived.
    if semantic(tomllib.loads(result.decode('utf-8'))) != semantic(expected):
        raise RuntimeError('a transformação alterou valores fora do escopo aprovado')
    return result


def directory_identity(meta):
    return [meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid, meta.st_mode]


def witness(path, *, allow_directory=False):
    """Bind a regular source or its absence and every existing ancestor identity."""
    path = Path(path)
    if not path.is_absolute() or path != Path(os.path.normpath(str(path))):
        raise RuntimeError('a origem precisa ter caminho absoluto normalizado')
    parents = []
    missing = None
    for parent in reversed(path.parents):
        if missing is not None:
            continue
        try:
            meta = parent.lstat()
        except FileNotFoundError:
            missing = str(parent)
            continue
        if not stat.S_ISDIR(meta.st_mode) or meta.st_uid not in {0, os.getuid()}:
            raise RuntimeError('ancestral inseguro da origem de configuração')
        parents.append([str(parent), directory_identity(meta)])
    result = {'path': str(path), 'parents': parents, 'missing_ancestor': missing,
              'allow_directory': allow_directory}
    if missing is not None:
        result['file'] = None
        return result
    if allow_directory:
        try:
            meta = path.lstat()
        except FileNotFoundError:
            meta = None
        if meta is not None and stat.S_ISDIR(meta.st_mode):
            if meta.st_uid not in {0, os.getuid()}:
                raise RuntimeError('marcador de projeto não confiável')
            result.update(file=None, directory=directory_identity(meta))
            return result
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        result['file'] = None
        return result
    with os.fdopen(descriptor, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        if (not stat.S_ISREG(meta.st_mode) or meta.st_uid not in {0, os.getuid()}
                or meta.st_nlink != 1):
            raise RuntimeError('origem insegura de configuração')
        data = stream.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024:
            raise RuntimeError('origem de configuração excede 8 MiB')
        identity = list(MonitorColdStart.file_identity(meta)) + [meta.st_ctime_ns]
        current, named = os.fstat(stream.fileno()), path.lstat()
        if (identity != list(MonitorColdStart.file_identity(current)) + [current.st_ctime_ns]
                or identity != list(MonitorColdStart.file_identity(named)) + [named.st_ctime_ns]):
            raise RuntimeError('origem mudou durante a leitura')
    result['file'] = {'identity': identity, 'sha256': digest(data)}
    return result


def revalidate(witnesses):
    for original in witnesses:
        if witness(original['path'], allow_directory=original.get('allow_directory', False)) != original:
            raise RuntimeError('origem presente ou ausente mudou; prepare novamente')


def inventory(home, contexts, reports, requirements):
    """Seal native layer provenance and supported local absence witnesses.

    This deliberately supports the inspected base-user/null-requirements shape.
    Native managed, preset, packaged and non-file sources require a separate decision.
    It never attempts to reproduce the native configuration loader.
    """
    home = Path(home)
    if not contexts or len(contexts) != len(reports):
        raise RuntimeError('inventário sem todos os contextos de cliente')
    if requirements.get('requirements', object()) is not None:
        raise RuntimeError('requisitos gerenciados não vinculáveis; migração recusada')
    paths = {home / 'config.toml', home / 'auth.json', Path('/etc/codex/config.toml'),
             Path('/etc/codex/requirements.toml'), Path('/etc/codex/managed_config.toml'),
             home / 'managed_config.toml', home / 'requirements.toml'}
    markers = set()
    signatures = []
    for context, report in zip(contexts, reports):
        context = Path(context)
        if context.resolve(strict=True) != context or not context.is_dir():
            raise RuntimeError('contexto de cliente não canônico')
        # Watch the whole finite ancestry, including absent project files. Native
        # root markers/trust decide activation; additions still invalidate this seal.
        for parent in (context, *context.parents):
            paths.add(parent / '.codex/config.toml')
            markers.add(parent / '.git')
        layers = report.get('layers')
        if not isinstance(layers, list) or not layers:
            raise RuntimeError('resposta nativa sem proveniência completa de camadas')
        active = []
        user = []
        for layer in layers:
            name = layer.get('name', {})
            kind = name.get('type')
            if kind == 'sessionFlags':
                # Current GUI supplies plugin paths, never migration policy. Their
                # raw identity is sealed separately; the cold reader has no flags.
                if set(layer.get('config', {})) != {'plugins'} or layer.get('disabledReason'):
                    raise RuntimeError('opções de sessão fora do escopo inspecionado')
                continue
            if kind == 'user':
                if name != {'type': 'user', 'file': str(home / 'config.toml'), 'profile': None}:
                    raise RuntimeError('perfil ou origem de usuário inesperado')
                user.append(layer)
            elif kind == 'system':
                if name != {'type': 'system', 'file': '/etc/codex/config.toml'} or layer.get('config'):
                    raise RuntimeError('configuração de sistema fora do escopo inspecionado')
            elif kind == 'project':
                folder = Path(name.get('dotCodexFolder', ''))
                if not folder.is_absolute() or folder / 'config.toml' not in paths:
                    raise RuntimeError('camada de projeto fora dos contextos selados')
                paths.add(folder / 'config.toml')
                if (any(key in layer.get('config', {}) for key in POLICY_KEYS)
                        or 'network_proxy' in layer.get('config', {}).get('features', {})):
                    raise RuntimeError('política de projeto conflita com a migração global')
            else:
                raise RuntimeError('origem nativa desconhecida ou não vinculável')
            if not isinstance(layer.get('version'), str) or not isinstance(layer.get('config'), dict):
                raise RuntimeError('identidade de camada nativa incompleta')
            active.append(layer)
        if len(user) != 1:
            raise RuntimeError('camada base de usuário ausente ou ambígua')
        source = tomllib.loads((home / 'config.toml').read_text())
        if native_user_semantic(user[0]['config'], home) != native_user_semantic(source, home):
            raise RuntimeError('camada nativa não corresponde ao arquivo de usuário')
        # Reject origins that cannot be accounted for by actual returned layers.
        names = [item['name'] for item in layers]
        for key, origin in report.get('origins', {}).items():
            if origin.get('name') not in names:
                raise RuntimeError('origem efetiva sem camada correspondente')
            if key.split('.')[0] in POLICY_KEYS and origin.get('name') != user[0]['name']:
                raise RuntimeError('política efetiva selecionada por outra origem')
        signatures.append({'context': str(context), 'layers': active})
    result = {'reports': signatures, 'requirements': requirements,
              'sources': [witness(path) for path in sorted(paths)]
                         + [witness(path, allow_directory=True) for path in sorted(markers)]}
    for item in result['sources']:
        if item['file'] and item['path'] in {
                '/etc/codex/requirements.toml', '/etc/codex/managed_config.toml',
                str(home / 'managed_config.toml'), str(home / 'requirements.toml')}:
            raise RuntimeError('fonte gerenciada presente fora do escopo inspecionado')
    revalidate(result['sources'])
    return result


def revalidate_inventory(original, home, contexts, reports, requirements):
    revalidate(original['sources'])
    if inventory(home, contexts, reports, requirements) != original:
        raise RuntimeError('inventário nativo mudou; prepare novamente')


def quiescent(authority, *, client_executables, consumer_scripts, allowed_reader=None):
    """Refuse relevant user processes and any running automatic queue obligation."""
    authority.verify_coordinator() if allowed_reader else authority.verify()
    executable_paths = {str(Path(path).resolve(strict=True)) for path in client_executables}
    script_paths = {str(Path(path).resolve(strict=True)) for path in consumer_scripts}
    support = _monitor_support()
    queue_path = Path(authority.config['queue_file'])
    if queue_path.exists():
        queue = support['MonitorQueue'](authority.config, readonly=True)
        try:
            if any(job['state'] == 'running' for job in queue.jobs()):
                raise RuntimeError('há trabalho automático em execução ou aguardando reconciliação')
        finally:
            queue.close()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            arguments = [os.fsdecode(value) for value in (entry / 'cmdline').read_bytes().split(b'\0') if value]
            # Executable basenames alone never identify a client. Resolve the actual
            # executable, with a command-line prefilter for unreadable identities.
            possible = (any(value in script_paths for value in arguments)
                        or any(Path(value).name in {Path(p).name for p in executable_paths}
                               for value in arguments[:1]))
            try:
                executable = str((entry / 'exe').resolve(strict=True))
            except PermissionError:
                if possible:
                    raise
                continue
            if executable not in executable_paths and not any(value in script_paths for value in arguments):
                continue
            current = authority.live_process(int(entry.name))
            if current is None or current == allowed_reader:
                continue
            if current['exe'] not in executable_paths and not any(value in script_paths for value in arguments):
                continue
            if any(value in script_paths for value in arguments):
                raise RuntimeError('consumidor automático ainda está ativo')
            environment = dict(value.split(b'=', 1) for value in
                (entry / 'environ').read_bytes().split(b'\0') if b'=' in value)
            selected = environment.get(b'CODEX_HOME')
            if selected is None:
                selected = environment.get(b'HOME', b'') + b'/.codex'
            if not Path(os.fsdecode(selected)).is_absolute():
                raise RuntimeError('cliente com origem de configuração não vinculável')
            if Path(os.fsdecode(selected)).resolve(strict=False) == authority.home:
                raise RuntimeError('cliente gráfico, CLI ou consumidor ainda está ativo')
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as error:
            raise RuntimeError('identidade de possível consumidor não pôde ser lida') from error


ENVIRONMENT_KEYS = {'HOME', 'CODEX_HOME', 'PATH', 'TMPDIR', 'XDG_RUNTIME_DIR',
                    'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME',
                    'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
                    'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy',
                    'SSL_CERT_FILE', 'SSL_CERT_DIR'}
UNITS = ('codex-gitlab-monitor.timer', 'codex-gitlab-monitor.service',
         'codex-monitor-alert.timer', 'codex-monitor-alert.service')


def environment_seal():
    # Keep secrets out of the manifest's environment map and terminal messages.
    return {key: digest(os.environ[key].encode()) if key in os.environ else None
            for key in sorted(ENVIRONMENT_KEYS)}


def executable_pin(path):
    """Bind selection symlinks, trusted ancestry and the actual executable bytes."""
    path = Path(path).absolute()
    links = []
    for part in (*reversed(path.parents), path):
        meta = part.lstat()
        if stat.S_ISLNK(meta.st_mode):
            if meta.st_uid not in {0, os.getuid()}:
                raise RuntimeError('seleção de executável não confiável')
            links.append([str(part), list(MonitorColdStart.file_identity(meta)), os.readlink(part)])
        elif part != path and (not stat.S_ISDIR(meta.st_mode)
                or meta.st_uid not in {0, os.getuid()}
                or meta.st_mode & 0o002 and not meta.st_mode & stat.S_ISVTX
                or meta.st_mode & 0o020 and not meta.st_mode & stat.S_ISVTX
                and not (meta.st_uid == os.getuid() and meta.st_gid == os.getgid())):
            raise RuntimeError('ancestral inseguro do executável')
    actual = path.resolve(strict=True)
    with actual.open('rb') as stream:
        meta = os.fstat(stream.fileno())
        if (not stat.S_ISREG(meta.st_mode) or meta.st_uid not in {0, os.getuid()}
                or meta.st_mode & 0o022 or not os.access(actual, os.X_OK)):
            raise RuntimeError('executável não confiável')
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
        identity = list(MonitorColdStart.file_identity(meta)) + [meta.st_ctime_ns]
        current, named = os.fstat(stream.fileno()), actual.stat()
        if (identity != list(MonitorColdStart.file_identity(current)) + [current.st_ctime_ns]
                or identity != list(MonitorColdStart.file_identity(named)) + [named.st_ctime_ns]):
            raise RuntimeError('executável mudou durante a leitura')
    return {'path': str(path), 'actual': str(actual), 'links': links,
            'identity': identity, 'sha256': value}


def code_sources():
    import sys
    import tomlkit
    import websockets
    root = Path(__file__).resolve().parent.parent
    return [witness(path) for path in (
        Path(__file__).resolve(), root / 'scripts/codex_monitor_cold.py',
        root / '.local/bin/codex-session-stats', root / 'scripts/pyproject.toml',
        root / 'scripts/poetry.lock', Path(tomlkit.__file__).resolve(),
        Path(websockets.__file__).resolve(), Path(sys.prefix) / 'pyvenv.cfg')]


def private_write(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def private_read(path):
    _monitor_support()['monitor_private'](path)
    record = witness(path)
    if record['file']['identity'][2] != os.getuid() or record['file']['identity'][4] & 0o077:
        raise RuntimeError('artefato precisa ser um arquivo privado do usuário')
    value = Path(path).read_bytes()
    if digest(value) != record['file']['sha256'] or witness(path) != record:
        raise RuntimeError('artefato mudou durante a leitura')
    return value


def monitor_sources(config):
    """Bind automatic-work selection to the actual monitor configuration sources."""
    if not config.get('_config_path'):
        raise RuntimeError('origem da configuração do monitor ausente')
    path = Path(config['_config_path'])
    sources = [witness(path)]
    current = _monitor_support()['mq_config'](path)
    if current.get('analysis_config'):
        sources.append(witness(Path(current['analysis_config'])))
        # Read again after witnessing the referenced analysis file, so a source
        # replacement during the first load cannot bind stale derived values.
        current = _monitor_support()['mq_config'](path)
    for key in ('codex_home', 'queue_file', 'state_file', 'gitlab_url',
                '_socket_alias', 'analysis_config'):
        if current.get(key) != config.get(key):
            raise RuntimeError('seleção da configuração do monitor mudou; prepare novamente')
    revalidate(sources)
    return sources


def prepare_artifact(config, contexts, reports, requirements, *, native_paths,
                     client_executables, artifact):
    """Seal already authenticated read-only native reports; never start a real reader here."""
    from codex_monitor_cold import monitor_config_snapshot
    import sys

    monitor_inputs = monitor_sources(config)
    alias = str(Path(config['_socket_alias']))
    cold_config = {key: config[key] for key in ('codex_home', 'queue_file', 'state_file', 'gitlab_url')}
    cold_config.update(socket=alias, _socket_alias=alias)
    authority = MonitorColdStart(cold_config, native_paths)
    original = monitor_config_snapshot(authority)
    if original[0] is None:
        raise RuntimeError('arquivo de configuração inspecionado ausente')
    prepared = transform(original[1])
    sources = inventory(authority.home, contexts, reports, requirements)
    native = [executable_pin(path) for path in native_paths]
    clients = [executable_pin(path) for path in dict.fromkeys([*client_executables, *native_paths])]
    source_root = Path(__file__).resolve().parent.parent
    consumers = [str(source_root / '.local/bin/codex-session-stats'),
                 str(source_root / '.local/bin/codex-monitor')]
    artifact = Path(artifact).absolute()
    if artifact.resolve(strict=False) != artifact or artifact.is_relative_to(authority.home):
        raise RuntimeError('artefato deve ficar fora do armazenamento nativo, sem links')
    artifact.mkdir(mode=0o700)
    _monitor_support()['monitor_private'](artifact, directory=True)
    manifest = {'version': 1, 'config': cold_config, 'contexts': [str(path) for path in contexts],
                'inventory': sources, 'native': native, 'clients': clients, 'consumers': consumers,
                'source_sha256': digest(original[1]), 'candidate_sha256': digest(prepared),
                'source_identity': list(original[0]), 'environment': environment_seal(),
                'monitor_sources': monitor_inputs,
                'code': code_sources(), 'python': executable_pin(sys.executable),
                'systemctl': executable_pin(__import__('shutil').which('systemctl'))}
    if monitor_config_snapshot(authority) != original:
        raise RuntimeError('arquivo de usuário mudou durante a preparação')
    revalidate(sources['sources'])
    revalidate(monitor_inputs)
    private_write(artifact / 'proposed.toml', prepared)
    manifest['candidate_witness'] = witness(artifact / 'proposed.toml')
    private_write(artifact / 'manifest.json', json.dumps(manifest, sort_keys=True).encode())
    return manifest


def systemd_quiescent(executable):
    import subprocess
    for unit in UNITS:
        result = subprocess.run([executable, '--user', 'show', unit, '--property=ActiveState', '--value'],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15)
        if result.returncode != 0 or result.stdout.strip() != 'inactive':
            raise RuntimeError('agendamento ou serviço ativo/não verificável: ' + unit)


def artifact_inputs(artifact, manifest_sha256):
    artifact = Path(artifact).absolute()
    if artifact.resolve(strict=True) != artifact:
        raise RuntimeError('diretório de artefatos não canônico')
    _monitor_support()['monitor_private'](artifact, directory=True)
    encoded = private_read(artifact / 'manifest.json')
    if digest(encoded) != manifest_sha256:
        raise RuntimeError('manifesto mudou depois da revisão; prepare novamente')
    manifest = json.loads(encoded)
    if manifest.get('version') != 1:
        raise RuntimeError('versão de artefato não suportada')
    prepared = private_read(artifact / 'proposed.toml')
    if (digest(prepared) != manifest['candidate_sha256']
            or witness(artifact / 'proposed.toml') != manifest['candidate_witness']):
        raise RuntimeError('prévia mudou depois da preparação')
    return artifact, manifest, prepared


def static_revalidate(manifest):
    if environment_seal() != manifest['environment']:
        raise RuntimeError('ambiente de execução mudou; prepare novamente')
    revalidate(manifest['code'])
    revalidate(manifest['monitor_sources'])
    for item in (*manifest['native'], *manifest['clients'], manifest['python'], manifest['systemctl']):
        if executable_pin(item['path']) != item:
            raise RuntimeError('código, pacote ou executável mudou; prepare novamente')


def apply_artifact(artifact, *, manifest_sha256, recover=False):
    """External operator phase only. The CLI additionally requires normal-close acknowledgment."""
    from codex_monitor_cold import monitor_config_snapshot, monitor_publish_config, monitor_read_cold_native
    import uuid

    artifact, manifest, prepared = artifact_inputs(artifact, manifest_sha256)
    static_revalidate(manifest)
    systemd_quiescent(manifest['systemctl']['actual'])
    authority = MonitorColdStart(manifest['config'], [item['actual'] for item in manifest['native']])
    state = {'native_started': False, 'native_terminated': False, 'published': False, 'backup': None}
    receipt = None
    if recover:
        receipt = json.loads(private_read(artifact / 'application.json'))
        backup = Path(receipt['backup'])
        if (backup.parent != authority.home
                or not __import__('re').fullmatch(r'config\.toml\.before-monitor-[a-f0-9]{32}\.bak', backup.name)):
            raise RuntimeError('backup fora do local conhecido')
        restored = private_read(backup)
        if digest(restored) != manifest['source_sha256'] or witness(backup) != receipt['backup_witness']:
            raise RuntimeError('backup original mudou; recuperação recusada')
    try:
        with authority:
            def consumers():
                quiescent(authority, client_executables=[item['actual'] for item in manifest['clients']],
                          consumer_scripts=manifest['consumers'])
                systemd_quiescent(manifest['systemctl']['actual'])

            consumers()
            original = monitor_config_snapshot(authority)
            if not recover and original[1] == prepared:
                revalidate([item for item in manifest['inventory']['sources']
                            if item['path'] != str(authority.home / 'config.toml')])
                return {**state, 'unchanged': True, 'activation_verified': False}
            if recover:
                if witness(authority.home / 'config.toml') != receipt['target_witness'] or original[1] != prepared:
                    raise RuntimeError('configuração mudou após a aplicação; recuperação recusada')
            elif (list(original[0] or ()) != manifest['source_identity']
                  or digest(original[1]) != manifest['source_sha256']
                  or transform(original[1]) != prepared):
                raise RuntimeError('configuração mudou; prepare novamente')
            # Other sources must remain byte/identity-exact. The restored user image
            # is the sole permitted inventory difference for a recovery read.
            watched = [item for item in manifest['inventory']['sources']
                       if not recover or item['path'] != str(authority.home / 'config.toml')]
            revalidate(watched)
            evidence = artifact / ('reader-' + uuid.uuid4().hex)
            evidence.mkdir(mode=0o700)
            environment = dict(os.environ, CODEX_HOME=str(authority.home))
            try:
                reader = monitor_read_cold_native(authority, manifest['native'][0]['actual'],
                    [Path(path) for path in manifest['contexts']], environment=environment, evidence=evidence)
            except BaseException as error:
                state.update({key: value for key, value in getattr(error, 'reader_state', {}).items()
                              if key in ('native_started', 'native_terminated', 'locks_reacquired')})
                raise
            state.update({key: reader[key] for key in ('native_started', 'native_terminated', 'locks_reacquired')})
            actual = inventory(authority.home, [Path(path) for path in manifest['contexts']],
                               reader['reports'], reader['requirements'])
            expected = __import__('copy').deepcopy(manifest['inventory'])
            if recover:
                expected['sources'] = actual['sources']
                for old, new in zip(expected['reports'], actual['reports']):
                    for old_layer, new_layer in zip(old['layers'], new['layers']):
                        if old_layer['name']['type'] == 'user':
                            old_layer['version'] = new_layer['version']
                            if (native_user_semantic(new_layer['config'], authority.home)
                                    != native_user_semantic(tomllib.loads(prepared.decode()), authority.home)):
                                raise RuntimeError('camada nativa não corresponde à prévia de recuperação')
                            old_layer['config'] = new_layer['config']
            if actual != expected:
                raise RuntimeError('camadas ou requisitos nativos mudaram; gravação recusada')
            observed = witness(authority.home / 'config.toml')

            def recheck():
                artifact_inputs(artifact, manifest_sha256)
                static_revalidate(manifest)
                revalidate(watched)
                consumers()
                revalidate(actual['sources'])
                if witness(authority.home / 'config.toml') != observed:
                    raise RuntimeError('configuração mudou após o leitor; gravação recusada')
                if recover and witness(backup) != receipt['backup_witness']:
                    raise RuntimeError('backup mudou antes da recuperação')

            result = monitor_publish_config(authority, original, restored if recover else prepared, recheck=recheck)
            state.update(result)
            if result['changed']:
                result.update(target_witness=witness(authority.home / 'config.toml'),
                              backup_witness=witness(result['backup']))
                private_write(artifact / ('recovery.json' if recover else 'application.json'),
                              json.dumps(result, sort_keys=True).encode())
            return {**state, 'unchanged': not result['changed'], 'activation_verified': False}
    except BaseException as error:
        state.update(getattr(error, 'publication_state', {}))
        error.migration_state = state
        raise


def main(argv=None):
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Preparar e aplicar a migração revisada de permissões do Codex.')
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare', help='preparar prévia privada usando a conexão autenticada atual')
    prepare.add_argument('--monitor-config', type=Path, required=True)
    prepare.add_argument('--native', type=Path, action='append', required=True)
    prepare.add_argument('--context', type=Path, action='append', required=True)
    prepare.add_argument('--artifact', type=Path, required=True)
    for operation in ('apply', 'recover'):
        command = commands.add_parser(operation, help='fase externa após fechamento normal do aplicativo')
        command.add_argument('--artifact', type=Path, required=True)
        command.add_argument('--after-normal-close', action='store_true', required=True)
        command.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args(argv)
    state = {}
    try:
        if args.command == 'prepare':
            support = _monitor_support()
            config = support['mq_config'](args.monitor_config.expanduser().absolute())
            config.pop('_health', None)
            owner = support['monitor_shared_owner'](config)
            if str(args.native[0].resolve(strict=True)) != owner['native']['exe']:
                raise RuntimeError('o primeiro executável deve ser o nativo da conexão autenticada atual')
            contexts = [path.expanduser().resolve(strict=True) for path in args.context]
            reports = [support['monitor_native'](config, 'config/read', {'cwd': str(path), 'includeLayers': True})
                       for path in contexts]
            requirements = support['monitor_native'](config, 'configRequirements/read', {})
            prepare_artifact(config, contexts, reports, requirements, native_paths=args.native,
                             client_executables=[owner['gui']['exe']], artifact=args.artifact)
            print('Prévia preparada. Sua configuração continua sem alterações. Artefatos: ' + str(args.artifact))
            print('SHA-256 do manifesto: ' + digest(private_read(args.artifact / 'manifest.json')))
            return 0
        state = apply_artifact(args.artifact, manifest_sha256=args.manifest_sha256,
                               recover=args.command == 'recover')
        if state['unchanged']:
            print('A configuração já contém os bytes preparados; nenhum arquivo foi alterado. '
                  'A ativação nos clientes ainda precisa ser verificada.')
        else:
            print(('Configuração anterior restaurada.' if args.command == 'recover' else 'Configuração migrada.')
                  + ' Backup privado: ' + str(state['backup'])
                  + ' Reabra o aplicativo e verifique as permissões; a ativação ainda não foi confirmada.')
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        state = getattr(error, 'migration_state', state)
        print('Migração recusada: ' + str(error), file=sys.stderr)
        if state.get('published'):
            print('A gravação ocorreu, mas a confirmação falhou. Não houve reversão automática. '
                  'Backup: ' + str(state.get('backup')), file=sys.stderr)
        elif state.get('native_started'):
            print('O leitor nativo foi iniciado. Encerramento confirmado: '
                  + ('sim' if state.get('native_terminated') else 'não')
                  + '. A configuração não foi substituída.', file=sys.stderr)
        else:
            print('Nenhum leitor nativo foi iniciado e a configuração não foi substituída.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
