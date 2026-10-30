#!/usr/bin/env python3
"""Observe monitor health and user units; never execute or modify the review queue."""
import argparse
import fcntl
import html
import json
import math
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import tempfile
import time


MAX_BYTES = 1024 * 1024
MAX_CHECKS = 2048
UNITS = ('codex-gitlab-monitor.timer', 'codex-gitlab-monitor.service')
PROPERTIES = ('Id', 'LoadState', 'ActiveState', 'SubState', 'UnitFileState', 'Result',
              'InvocationID', 'ExecMainStartTimestampMonotonic', 'ExecMainExitTimestampMonotonic',
              'ExecMainCode', 'ExecMainStatus')


def private_directory(path):
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    value = path.lstat()
    if not stat.S_ISDIR(value.st_mode) or value.st_uid != os.getuid() or value.st_mode & 0o077:
        raise ValueError('alert directory must be private, owned and without symlinks')


def read_private(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        value = os.fstat(stream.fileno())
        if not stat.S_ISREG(value.st_mode) or value.st_uid != os.getuid() or value.st_mode & 0o077:
            raise ValueError('alert input must be a private owned regular file')
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('alert input exceeds byte bound')
    value = json.loads(raw)
    if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1:
        raise ValueError('invalid alert document version')
    return value


def atomic_write(path, value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode() + b'\n'
    if len(raw) > MAX_BYTES:
        raise ValueError('alert state exceeds byte bound')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.alert-', delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def validate_snapshot(value):
    if (not isinstance(value.get('boot_id'), str) or not value['boot_id']
            or not isinstance(value.get('cycle_id'), str) or not value['cycle_id']
            or not isinstance(value.get('queue_id'), str) or not value['queue_id']
            or value.get('phase') not in {'running', 'finished', 'yielded', 'failed'}
            or not number(value.get('sampled')) or not number(value.get('wall_time'))
            or not number(value.get('interval_seconds')) or value['interval_seconds'] < 60
            or not isinstance(value.get('checks'), dict) or len(value['checks']) > MAX_CHECKS
            or not isinstance(value.get('summary'), dict)):
        raise ValueError('invalid monitor health snapshot')
    for field in ('pending', 'running', 'holds'):
        if type(value['summary'].get(field)) is not int or value['summary'][field] < 0:
            raise ValueError('invalid monitor queue summary')
    for key, check in value['checks'].items():
        if (not isinstance(key, str) or not key or len(key) > 256
                or not isinstance(check, dict) or check.get('status') not in {'failed', 'ok', 'retired'}
                or not isinstance(check.get('episode'), str) or not check['episode']
                or not isinstance(check.get('message'), str) or len(check['message']) > 600
                or not isinstance(check.get('kind'), str) or len(check['kind']) > 80
                or not number(check.get('first_seen')) or not number(check.get('last_seen'))
                or type(check.get('failures')) is not int or check['failures'] < 0
                or type(check.get('threshold')) is not int or check['threshold'] not in (1, 2)):
            raise ValueError('invalid monitor health observation')
    return value


def run_bounded(arguments, *, timeout=10, limit=65536, allowed=(0,)):
    """Bound both pipe consumption and execution of the owned diagnostic subprocess."""
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = {process.stdout: bytearray(), process.stderr: bytearray()}
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for stream in output:
                selector.register(stream, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('alert subprocess timed out')
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fileobj.fileno(), min(8192, limit + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output[key.fileobj].extend(chunk)
                        if sum(map(len, output.values())) > limit:
                            raise ValueError('alert subprocess output exceeds bound')
        process.wait(timeout=max(.01, deadline - time.monotonic()))
        if process.returncode not in allowed:
            # Keep bounded stderr in the journal; never copy it into desktop health messages.
            diagnostic = bytes(output[process.stderr]).decode('utf-8', errors='replace')[:500].strip()
            raise RuntimeError(f'{Path(arguments[0]).name} exited with status {process.returncode}: {diagnostic}')
        return bytes(output[process.stdout]).decode('utf-8')
    except subprocess.TimeoutExpired as error:
        raise TimeoutError('alert subprocess timed out') from error
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        for stream in output:
            stream.close()


def read_units(command):
    raw = run_bounded([str(command), '--user', 'show', *UNITS,
                       '--property=' + ','.join(PROPERTIES), '--no-pager'], allowed=(0, 4))
    result = {}
    for block in raw.strip().split('\n\n'):
        fields = dict(line.split('=', 1) for line in block.splitlines() if '=' in line)
        if fields.get('Id') in result or fields.get('Id') not in UNITS:
            raise ValueError('invalid user-unit identities')
        if not {'LoadState', 'ActiveState'} <= fields.keys():
            raise ValueError('incomplete user-unit state')
        result[fields['Id']] = fields
    if set(result) != set(UNITS):
        raise ValueError('missing user-unit evidence')
    return result


def now():
    return {'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'mono': time.monotonic(), 'wall': time.time(),
            'suspend': max(0., time.clock_gettime(time.CLOCK_BOOTTIME) - time.monotonic())}


def load_state(path, clock, interval=900):
    try:
        value = read_private(path)
    except FileNotFoundError:
        value = {'version': 1, 'boot': clock['boot'], 'grace_until': clock['mono'] + interval + 300,
                 'suspend': clock['suspend'], 'incidents': {}, 'queue_id': None}
    if (not isinstance(value.get('incidents'), dict) or len(value['incidents']) > MAX_CHECKS
            or not isinstance(value.get('boot'), str) or not number(value.get('grace_until'))
            or not number(value.get('suspend'))):
        raise ValueError('invalid persisted alert state')
    for item in value['incidents'].values():
        if (not isinstance(item, dict) or not isinstance(item.get('episode'), str)
                or not number(item.get('first_seen')) or type(item.get('notified')) is not bool):
            raise ValueError('invalid persisted alert incident')
    if value['boot'] != clock['boot'] or clock['suspend'] - value['suspend'] > 5:
        value.update(boot=clock['boot'], grace_until=clock['mono'] + interval + 300)
    value['suspend'] = clock['suspend']
    return value


def observation(status, kind, message, episode='local'):
    return {'status': status, 'kind': kind, 'message': message, 'episode': episode,
            'failures': 1, 'threshold': 1, 'first_seen': 0, 'last_seen': 0}


def collect(snapshot_path, units, state, clock, interval=900):
    checks = {}
    if units is None:
        checks['observer:units'] = observation('failed', 'Verificação indisponível',
            'Não foi possível consultar o gerenciador de serviços do usuário. Consulte o journal do alerta.')
    else:
        checks['observer:units'] = observation('ok', 'Gerenciador de serviços', 'Consulta restabelecida.')
        timer, service = (units[name] for name in UNITS)
        timer_ok = (timer['LoadState'] == 'loaded' and timer['ActiveState'] == 'active'
                    and timer.get('UnitFileState') not in {'disabled', 'masked', 'masked-runtime'})
        checks['systemd:timer'] = observation('ok' if timer_ok else 'failed', 'Agendamento do monitor',
            'Timer ativo.' if timer_ok else 'O timer do monitor está ausente, desabilitado ou parado.')
        service_bad = (service['LoadState'] != 'loaded' or service['ActiveState'] == 'failed'
                       or service.get('Result', '') not in {'', 'success'})
        if service_bad:
            checks['systemd:service'] = observation('failed', 'Serviço do monitor',
                'Falha no serviço: ' + service.get('Result', service['LoadState']) + '. Consulte seu journal.')
        elif (service.get('Result') == 'success' and service['ActiveState'] == 'inactive'
              and service.get('ExecMainCode') == '1' and service.get('ExecMainStatus') == '0'
              and service.get('ExecMainExitTimestampMonotonic', '0').isdigit()
              and int(service.get('ExecMainExitTimestampMonotonic', '0')) > 0
              and service.get('ExecMainStartTimestampMonotonic', '0').isdigit()
              and int(service.get('ExecMainStartTimestampMonotonic', '0')) > 0):
            checks['systemd:service'] = observation('ok', 'Serviço do monitor',
                'Uma execução do serviço terminou com sucesso; consulte a saúde de cada operação.')
        if 'systemd:service' in checks:
            checks['systemd:service']['proof'] = service.get('InvocationID', '') + ':' + \
                service.get('ExecMainStartTimestampMonotonic', '0')
    try:
        snapshot = validate_snapshot(read_private(snapshot_path))
        if snapshot['boot_id'] != clock['boot'] or snapshot['sampled'] > clock['mono'] + 1:
            raise ValueError('health snapshot is from another boot or the future')
    except (OSError, ValueError, KeyError, TypeError):
        if clock['mono'] >= state['grace_until']:
            checks['observer:health'] = observation('failed', 'Saúde do monitor desconhecida',
                'O registro de saúde está ausente, inválido ou ilegível. Consulte o journal do monitor.')
        return checks
    if state.get('queue_id') not in {None, snapshot['queue_id']}:
        # An explicit new queue/config cannot inherit delivery claims from another source.
        state['incidents'] = {k: v for k, v in state['incidents'].items() if not k.startswith('monitor:')}
    state['queue_id'] = snapshot['queue_id']
    # Inventory cadence in TOML is distinct from the systemd cycle schedule.
    stale = clock['mono'] - snapshot['sampled'] > interval * 2 + 300
    if stale:
        if clock['mono'] >= state['grace_until']:
            checks['observer:health'] = observation('failed', 'Sem ciclos recentes',
                'O monitor não produziu saúde recente por dois intervalos mais a margem. Consulte o serviço e seu timer.')
        return checks
    if units is not None:
        service = units[UNITS[1]]
        started = service.get('ExecMainStartTimestampMonotonic', '0')
        if started.isdigit() and int(started) / 1000000 > snapshot['sampled'] + 1:
            # A lock-busy cycle legitimately exports nothing. Until the freshness bound,
            # missing per-invocation output proves neither failure nor recovery.
            return checks
    if snapshot['phase'] == 'running':
        if (units is not None and snapshot.get('invocation_id')
                and snapshot['invocation_id'] == units[UNITS[1]].get('InvocationID')
                and units[UNITS[1]]['ActiveState'] in {'inactive', 'failed'}):
            checks['observer:health'] = observation('failed', 'Registro de saúde incompleto',
                'O serviço terminou, mas não publicou o resultado de saúde do ciclo. Consulte o journal do monitor.')
        # A start marker is not successful observation of the producer's complete cycle.
        return checks
    checks['observer:health'] = observation('ok', 'Observação do monitor', 'Há um registro de saúde recente.')
    for key, value in snapshot['checks'].items():
        checks['monitor:' + key] = {**value, 'message': value['message'] +
            '\nFila: '+str(snapshot['summary']['pending'])+' pendente(s), '+
            str(snapshot['summary']['running'])+' em execução.'}
    return checks


def notify(command, title, body):
    run_bounded([str(command), '--app-name=Fila de revisões', '--urgency=normal',
                 '--icon=dialog-warning', '--expire-time=30000', '--',
                 html.escape(title), html.escape(body)], limit=8192)


def deliver(checks, state, state_path, command, clock, *, sender=notify):
    sent, failures, attempts = 0, [], 0
    for key, check in checks.items():
        previous = state['incidents'].get(key)
        if check['status'] in {'ok', 'retired'}:
            if previous is None:
                continue
            # Positive evidence for a different producer episode cannot resolve this one.
            if key.startswith('monitor:') and previous['episode'] != check['episode']:
                continue
            if key == 'systemd:service' and previous.get('proof') == check.get('proof'):
                continue
            if previous['notified'] and check['status'] == 'ok':
                if attempts >= 5:
                    continue
                attempts += 1
                try:
                    sender(command, 'Monitor: recuperação confirmada', check['kind'] + ': ' + check['message'])
                except (OSError, RuntimeError, ValueError, TimeoutError) as error:
                    failures.append(str(error))
                    continue
                sent += 1
            state['incidents'].pop(key, None)
            atomic_write(state_path, state)
            continue
        if check['failures'] < check['threshold']:
            continue
        if previous is None or previous['episode'] != check['episode']:
            previous = {'episode': check['episode'], 'notified': False, 'first_seen': clock['wall']}
            state['incidents'][key] = previous
        if key == 'systemd:service':
            previous['proof'] = check.get('proof')
        if previous['notified']:
            continue
        if attempts >= 5:
            continue
        attempts += 1
        try:
            first = time.strftime('%d/%m %H:%M', time.localtime(previous['first_seen']))
            sender(command, 'Monitor: ' + check['kind'], check['message'] + '\nObservado desde ' + first + '.')
        except (OSError, RuntimeError, ValueError, TimeoutError) as error:
            failures.append(str(error))
        else:
            previous['notified'] = True
            sent += 1
        # Failed delivery remains pending; accepted delivery survives the next checker invocation.
        atomic_write(state_path, state)
    atomic_write(state_path, state)
    return sent, failures


def check(args):
    private_directory(args.state.parent)
    descriptor = os.open(args.state.with_suffix('.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as lock:
        metadata = os.fstat(lock.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
            raise ValueError('invalid alert lock')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'busy', 'sent': 0}
        clock = now()
        state = load_state(args.state, clock, args.cycle_seconds)
        try:
            units = read_units(args.systemctl)
        except (OSError, RuntimeError, ValueError, TimeoutError) as error:
            print('codex-monitor-alert: ' + str(error), file=sys.stderr)
            units = None
        checks = collect(args.snapshot, units, state, clock, args.cycle_seconds)
        sent, failures = deliver(checks, state, args.state, args.notify_command, clock)
        if failures:
            raise RuntimeError('desktop delivery pending: ' + '; '.join(failures[:3]))
        return {'status': 'checked', 'sent': sent, 'open_incidents': len(state['incidents'])}


def main(argv=None):
    root = Path(os.environ.get('XDG_STATE_HOME', '~/.local/state')).expanduser()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=root / 'codex-session-stats-queue/health.json')
    parser.add_argument('--state', type=Path, default=root / 'codex-monitor-alert/state.json')
    parser.add_argument('--systemctl', type=Path, default=Path('/usr/bin/systemctl'))
    parser.add_argument('--notify-command', type=Path, default=Path('/usr/bin/notify-send'))
    parser.add_argument('--cycle-seconds', type=int, default=900,
                        help='expected monitor timer interval, independent of inventory cadence')
    args = parser.parse_args(argv)
    if args.cycle_seconds < 60:
        parser.error('--cycle-seconds must be at least 60')
    try:
        print(json.dumps(check(args), ensure_ascii=False))
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, TimeoutError) as error:
        print('codex-monitor-alert: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
