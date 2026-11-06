"""Observational launcher diagnostics: no locks, publication, health or queue writes."""
from pathlib import Path
import runpy


def launcher():
    return runpy.run_path(str(Path(__file__).with_name('codex_monitor_launcher.py')))


def monitor_status(config, *, app=None, codex=None, check=False):
    m = launcher()
    errors, blockers = [], []
    result = {'codex_home': config['codex_home'], 'server': {'state': 'unknown'},
              'gui': {'state': 'not_verified', 'tools': 'not_verified'},
              'updater': {'auto_update_enabled': None},
              'cold_start': {'blockers': blockers, 'errors': errors,
                             'requires_closing_monitor': False},
              'check': {'ready': False, 'protocol': 'not_probed'},
              'observation': 'Sampled state only; no startup capacity is reserved.'}
    try:
        native = m['installed_native'](config)
        paths = [native] + ([codex] if codex is not None else [])
        authority = m['cold']()['MonitorColdStart'](config, paths)
    except (OSError, ValueError, RuntimeError) as error:
        errors.append(str(error))
        return result

    owner = None
    try:
        owner = m['native_owner'](config)
        result['server'] = {'state': 'authenticated', 'process': owner['native'],
                            'registration': 'not_verified', 'effective_config': 'not_probed'}
        result['cold_start']['requires_closing_monitor'] = True
        if check:
            try:
                m['verify_effective'](config, owner)
                result['server']['effective_config'] = 'verified'
                result['check']['protocol'] = 'verified'
            except Exception as error:
                # Optional transport failures are observations, never a reason to
                # refresh, restart or publish a replacement from a diagnostic command.
                result['check']['protocol'] = 'failed'
                result['server']['error'] = type(error).__name__ + ': ' + str(error)
    except (OSError, ValueError, RuntimeError, TimeoutError) as error:
        result['server']['error'] = str(error)
        if owner is None:
            result['server']['state'] = 'unavailable'

    runtime = None
    try:
        runtime = m['support']()['monitor_shared_runtime'](config)
        saved = authority.read_record(runtime / 'ready.json', private=True)
        if owner is not None:
            result['server']['registration'] = 'matching' if saved == owner else 'stale_or_missing'
    except FileNotFoundError:
        pass
    except (OSError, ValueError, RuntimeError) as error:
        errors.append('Runtime evidence: ' + str(error))

    known = [owner['native']] if owner is not None else []
    try:
        if app is not None:
            guis = list(m['gui_processes'](Path(app).resolve(strict=True)))
            for gui in guis:
                registered = m['gui_registration'](gui)
                if registered['home'] != config['codex_home']:
                    continue
                known.append(registered['proxy'])
                result['cold_start']['requires_closing_monitor'] = True
                result['gui'] = {'state': 'registered_live', 'process': gui,
                                 'tools': 'not_verified'}
                if runtime is not None:
                    ready = authority.read_record(runtime / 'gui-ready.json', private=True)
                    directory = m['monitor_app_tools_directory'](config)
                    binding = authority.read_record(directory / 'binding.json', private=True)
                    meta = (directory / 'host.sock').lstat()
                    if (ready and owner and ready.get('native') == owner['native']
                            and ready.get('gui') == gui and ready.get('proxy') == registered['proxy']
                            and ready.get('binding') == binding and binding
                            and binding.get('socket_identity') == [meta.st_dev, meta.st_ino]):
                        result['gui']['tools'] = 'last_validated'
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        errors.append('GUI evidence: ' + str(error))

    try:
        owners = authority.native_owners()
        for process in owners:
            if any(all(process[k] == expected[k] for k in ('pid', 'birth', 'exe')) for expected in known):
                continue
            blockers.append({'process': process, 'client': m['cold']()['describe_native_process'](process),
                             'action': 'Finish this client normally before a cold recovery.'})
    except (OSError, ValueError, RuntimeError) as error:
        errors.append('Process inventory: ' + str(error))

    try:
        path = Path(config['codex_home']) / 'app-server-daemon/settings.json'
        settings = authority.read_record(path)
        enabled = (settings or {}).get('updater', {}).get('autoUpdateEnabled', True)
        if type(enabled) is not bool:
            raise ValueError('autoUpdateEnabled must be a boolean')
        result['updater']['auto_update_enabled'] = enabled
    except (OSError, ValueError, AttributeError, RuntimeError) as error:
        errors.append('Updater settings: ' + str(error))

    # A cold recovery always needs the current Monitor clients to finish normally.
    # Additional clients are reported even while the current server can be reused.
    reusable = owner is not None and result['server'].get('registration') == 'matching'
    result['check']['ready'] = not blockers and not errors and (
        reusable and (not check or result['check']['protocol'] == 'verified'))
    return result
