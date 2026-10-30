"""Actual health export and independent notification state; no live provider or desktop effects."""
import copy
import json
import os
from pathlib import Path
import runpy
import sys

import pytest

from test_codex_gitlab_queue import module, flow, domain


ALERT = Path(os.environ.get('CODEX_MONITOR_ALERT_SCRIPT',
                           Path(__file__).resolve().parents[1] / 'codex_monitor_alert.py'))


@pytest.fixture
def alert():
    return runpy.run_path(str(ALERT), run_name='alert_test')


@pytest.fixture
def health_flow(flow, monkeypatch):
    # The shared flow normally drives the worker directly. These cases use its real tick too,
    # so its external GitLab fixture also needs an explicit empty inventory page.
    def pages(self, route, **kwargs):
        yield [], True
    monkeypatch.setattr(flow.m['MonitorGitLab'], 'pages', pages, raising=False)
    return flow


@pytest.fixture
def clock():
    return {'boot': 'test-boot', 'mono': 5000., 'wall': 10000., 'suspend': 0.}


@pytest.fixture
def state(clock):
    return {'version': 1, 'boot': clock['boot'], 'grace_until': 0.,
            'suspend': 0., 'incidents': {}, 'queue_id': None}


def document(clock, checks=None, **values):
    return {'version': 1, 'boot_id': clock['boot'], 'cycle_id': 'cycle-one', 'queue_id': 'queue-one',
            'invocation_id': 'one',
            'phase': 'finished', 'sampled': clock['mono'], 'wall_time': clock['wall'],
            'interval_seconds': 900, 'checks': checks or {},
            'summary': {'pending': 2, 'running': 0, 'holds': 0}, **values}


def issue(*, status='failed', episode='one', failures=1, threshold=1):
    return {'status': status, 'episode': episode, 'kind': 'Conexão do Codex',
            'message': 'Use Codex Monitor.', 'failures': failures, 'threshold': threshold,
            'first_seen': 10., 'last_seen': 20.}


def write(path, value):
    path.write_text(json.dumps(value)); path.chmod(0o600)
    return path


def healthy_units():
    return {
        'codex-gitlab-monitor.timer': {'Id': 'codex-gitlab-monitor.timer', 'LoadState': 'loaded',
            'ActiveState': 'active', 'SubState': 'waiting', 'UnitFileState': 'enabled'},
        'codex-gitlab-monitor.service': {'Id': 'codex-gitlab-monitor.service', 'LoadState': 'loaded',
            'ActiveState': 'inactive', 'SubState': 'dead', 'Result': 'success',
            'ExecMainStartTimestampMonotonic': '1000000', 'ExecMainExitTimestampMonotonic': '2000000',
            'ExecMainCode': '1', 'ExecMainStatus': '0', 'InvocationID': 'one'}}


def test_original_caught_shared_app_failure_exports_failure_despite_success_exit(health_flow, monkeypatch):
    f = health_flow
    raw = dict(f.raw)
    for key in ('cwd', 'model', 'effort'):
        raw.pop(key)
    raw['analysis_config'] = 'analysis.toml'
    raw['codex_project_binding'] = {'id': '01234567-89ab-4cde-8fab-0123456789ab',
        'name': 'fixture project', 'roots': [f.config['cwd']], 'existing_threads': {}}
    analysis = f.config_path.with_name('analysis.toml')
    analysis.write_text('codex_model="gpt-6.1-sol"\ncodex_effort="xhigh"\n'
                        'codex_project_name="fixture project"\n')
    analysis.chmod(0o600)
    f.config_path.write_text(json.dumps(raw))
    f.config.clear(); f.config.update(f.m['mq_config'](f.config_path))
    job = f.q.enqueue(11, 82, source_key='health-regression', kind='code', head=f.context['head'],
        source={'origin': 'automatic', 'head': f.context['head']}, context=copy.deepcopy(f.context))
    native = f.m['monitor_native']
    # External native provider boundary fails its real local ownership proof at workspace lookup.
    def missing(c, method, params, **kwargs):
        f.m['monitor_shared_owner'](c)
        return native(c, method, params, **kwargs)
    monkeypatch.setitem(f.m, 'monitor_native', missing)
    result = f.tick()
    assert result['cycle'] == 'checked'
    snapshot = Path(f.config['queue_file']).with_name('health.json')
    assert snapshot.is_file(), 'caught native failure must be exported despite successful cycle exit'
    health = json.loads(snapshot.read_text())
    assert health['checks']['native:shared']['status'] == 'failed'
    assert health['checks']['native:shared']['threshold'] == 1
    assert len([key for key in health['checks'] if key.startswith('native:shared')]) == 1
    assert f.q.job(job['id'])['state'] == 'pending'
    assert f.q.mr(11, 82)['reviewed_head'] is None
    assert not f.sends and not f.launched


def test_health_counts_distinct_cycles_and_requires_matching_success(module, tmp_path):
    m = module
    c = {'_health': {'checks': {}, 'cycle_id': 'one'}}
    signal = m['mq_health_signal']
    signal(c, 'read:one', error=RuntimeError('a'), threshold=2)
    signal(c, 'read:one', error=RuntimeError('b'), threshold=2)
    before = copy.deepcopy(c['_health']['checks']['read:one'])
    assert before['failures'] == 1
    signal(c, 'read:two')
    assert c['_health']['checks']['read:one'] == before
    c['_health']['cycle_id'] = 'two'
    signal(c, 'read:one', error=RuntimeError('again'), threshold=2)
    assert c['_health']['checks']['read:one']['failures'] == 2
    assert c['_health']['checks']['read:one']['episode'] == before['episode']
    signal(c, 'read:one')
    assert c['_health']['checks']['read:one']['status'] == 'ok'
    signal(c, 'read:one', error=True)
    assert c['_health']['checks']['read:one']['episode'] != before['episode']


def test_old_database_diagnostic_is_not_a_current_incident(health_flow):
    f = health_flow
    with f.q.atomic():
        f.q.set_meta('consumer_error', {'at': 1, 'error': 'historical failure'})
    f.tick()
    health = json.loads(Path(f.config['queue_file']).with_name('health.json').read_text())
    assert health['checks'] == {}
    assert f.q.meta('consumer_error')['at'] == 1


def test_export_failure_does_not_fail_or_mutate_idle_queue(health_flow, monkeypatch, capsys):
    f = health_flow
    original = f.q.jobs()
    def denied(*args, **kwargs):
        raise PermissionError('fixture denial')
    monkeypatch.setitem(f.m, 'mq_service_write', denied)
    assert f.tick()['cycle'] == 'checked'
    assert f.q.jobs() == original
    assert 'health export failed' in capsys.readouterr().err


def test_effective_native_continuation_controls_reviewer_health(flow):
    f = flow
    job = f.q.enqueue(11, 82, source_key='health-effective', kind='code', head=f.context['head'],
        source={'origin': 'automatic', 'head': f.context['head']}, context=copy.deepcopy(f.context))
    job = f.q.reserve({11})
    stage = f.q.stage_start(job, 'claude', 'input')
    f.q.stage_end(job, stage['id'], error={'message': 'provider failure'}, terminal=True)
    f.m['mq_health_begin'](f.config, f.q)
    f.m['mq_health_publish'](f.config, f.q, 'finished')
    key = 'reviewer:' + job['id'] + ':claude'
    assert f.config['_health']['checks'][key]['status'] == 'failed'
    saved = f.q.job(job['id'])
    saved['stages'][0]['continuations'] = [{'outcome': {'state': 'succeeded', 'result': domain()}}]
    f.q.save(saved)
    f.m['mq_health_publish'](f.config, f.q, 'finished')
    assert f.config['_health']['checks'][key]['status'] == 'ok'
    assert f.q.mr(11, 82)['reviewed_head'] is None


@pytest.mark.parametrize('value', ['idle', 'busy', 'backoff', 'human', 'active'])
def test_expected_queue_conditions_do_not_create_alerts(alert, state, clock, tmp_path, value):
    path = write(tmp_path / 'health.json', document(clock,
        summary={'pending': 1 if value in {'backoff', 'human'} else 0,
                 'running': 1 if value == 'active' else 0, 'holds': 1 if value == 'human' else 0}))
    checks = alert['collect'](path, healthy_units(), state, clock)
    sent = []
    result = alert['deliver'](checks, state, tmp_path / 'state.json', Path('/fixture'), clock,
                            sender=lambda *args: sent.append(args))
    assert result == (0, [])
    assert sent == []
    assert state['incidents'] == {}


def test_duplicate_failure_recovery_and_new_episode_survive_restart(alert, state, clock, tmp_path):
    path = tmp_path / 'state.json'; sent = []
    sender = lambda *args: sent.append(args)
    deliver = alert['deliver']
    deliver({'monitor:shared': issue()}, state, path, Path('/fixture'), clock, sender=sender)
    restarted = alert['load_state'](path, clock)
    deliver({'monitor:shared': issue(failures=9)}, restarted, path, Path('/fixture'), clock, sender=sender)
    assert len(sent) == 1
    deliver({'monitor:other': issue(status='ok')}, restarted, path, Path('/fixture'), clock, sender=sender)
    assert len(sent) == 1
    deliver({'monitor:shared': issue(status='ok')}, restarted, path, Path('/fixture'), clock, sender=sender)
    assert len(sent) == 2 and 'recuperação' in sent[-1][1]
    deliver({'monitor:shared': issue(episode='new')}, restarted, path, Path('/fixture'), clock, sender=sender)
    assert len(sent) == 3


def test_failed_delivery_retries_current_state_and_no_stale_recovery_popup(alert, state, clock, tmp_path):
    path = tmp_path / 'state.json'
    def fail(*args):
        raise RuntimeError('desktop offline')
    sent, errors = alert['deliver']({'monitor:shared': issue()}, state, path, Path('/fixture'), clock, sender=fail)
    assert sent == 0 and errors == ['desktop offline']
    assert alert['read_private'](path)['incidents']['monitor:shared']['notified'] is False
    calls = []
    result = alert['deliver']({'monitor:shared': issue(status='ok')}, state, path, Path('/fixture'), clock,
                             sender=lambda *args: calls.append(args))
    assert result == (0, []) and calls == []
    assert state['incidents'] == {}


def test_failed_recovery_notice_is_retried_and_scope_retirement_is_silent(alert, state, clock, tmp_path):
    path = tmp_path / 'state.json'; sender = lambda *args: None
    alert['deliver']({'monitor:shared': issue()}, state, path, Path('/fixture'), clock, sender=sender)
    def fail(*args):raise TimeoutError('timeout')
    assert alert['deliver']({'monitor:shared': issue(status='ok')}, state, path, Path('/fixture'), clock,
                            sender=fail) == (0, ['timeout'])
    assert state['incidents']['monitor:shared']['notified'] is True
    assert alert['deliver']({'monitor:shared': issue(status='retired')}, state, path, Path('/fixture'), clock,
                            sender=sender) == (0, [])
    assert state['incidents'] == {}


@pytest.mark.parametrize('fault', ['missing', 'json', 'version', 'mode', 'symlink', 'stale', 'old-boot', 'future'])
def test_unknown_health_never_resolves_existing_failure(alert, state, clock, tmp_path, fault):
    path = tmp_path / 'health.json'
    value = document(clock)
    if fault == 'version':value['version'] = 99
    if fault == 'stale':value['sampled'] = clock['mono'] - 2101
    if fault == 'old-boot':value['boot_id'] = 'old-boot'
    if fault == 'future':value['sampled'] = clock['mono'] + 99
    if fault != 'missing':write(path, value)
    if fault == 'json':path.write_text('not json')
    if fault == 'mode':path.chmod(0o644)
    if fault == 'symlink':
        other = path.with_name('target.json'); path.rename(other); path.symlink_to(other.name)
    state['incidents']['monitor:shared'] = {'episode': 'one', 'notified': True, 'first_seen': 1}
    checks = alert['collect'](path, healthy_units(), state, clock)
    assert checks['observer:health']['status'] == 'failed'
    assert 'monitor:shared' not in checks
    assert state['incidents']['monitor:shared']['notified'] is True


def test_startup_resume_and_wall_clock_change_do_not_manufacture_missed_cycles(alert, clock, tmp_path):
    path = tmp_path / 'state.json'
    state = alert['load_state'](path, clock)
    checks = alert['collect'](tmp_path / 'missing', healthy_units(), state, clock)
    assert 'observer:health' not in checks
    state['grace_until'] = 0
    alert['atomic_write'](path, state)
    resumed = {**clock, 'suspend': 100, 'wall': clock['wall'] + 100000}
    state = alert['load_state'](path, resumed)
    assert state['grace_until'] == clock['mono'] + 1200
    assert 'observer:health' not in alert['collect'](tmp_path / 'missing', healthy_units(), state, resumed)


@pytest.mark.parametrize('field,value', [('ActiveState', 'inactive'), ('LoadState', 'not-found'),
                                        ('UnitFileState', 'disabled')])
def test_timer_failure_detected_without_producer(alert, state, clock, tmp_path, field, value):
    units = healthy_units(); units['codex-gitlab-monitor.timer'][field] = value
    checks = alert['collect'](tmp_path / 'missing', units, state, clock)
    assert checks['systemd:timer']['status'] == 'failed'


def test_service_failure_independent_of_health_and_cli_import(alert, state, clock, tmp_path):
    units = healthy_units()
    units['codex-gitlab-monitor.service'].update(ActiveState='failed', Result='exit-code')
    checks = alert['collect'](tmp_path / 'missing', units, state, clock)
    assert checks['systemd:service']['status'] == 'failed'
    source = ALERT.read_text()
    assert 'run_path' not in source and 'codex-session-stats monitor' not in source


def test_notification_request_escapes_markup_and_has_no_shell(alert, monkeypatch):
    calls = []
    monkeypatch.setitem(alert['notify'].__globals__, 'run_bounded', lambda args, **kw: calls.append(args))
    alert['notify'](Path('/fixture/notify'), '<title>', '<body>&')
    assert calls[0][-2:] == ['&lt;title&gt;', '&lt;body&gt;&amp;']
    assert calls[0][-3] == '--'


def test_actual_subprocess_output_and_time_bounds(alert):
    assert alert['run_bounded']([sys.executable, '-c', 'print("unit")']) == 'unit\n'
    with pytest.raises(ValueError, match='output exceeds bound'):
        alert['run_bounded']([sys.executable, '-c', 'print("x" * 20000)'], limit=100)
    with pytest.raises(TimeoutError, match='timed out'):
        alert['run_bounded']([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=.05)


def test_send_attempts_are_bounded_per_checker_run(alert, state, clock, tmp_path):
    calls = []
    checks = {'monitor:' + str(i): issue() for i in range(8)}
    sent, failures = alert['deliver'](checks, state, tmp_path / 'state.json', Path('/fixture'), clock,
                                     sender=lambda *args: calls.append(args))
    assert sent == len(calls) == 5 and failures == []
    assert sum(v['notified'] for v in state['incidents'].values()) == 5


def test_partial_export_is_not_recovery_and_finished_service_reports_incomplete_health(alert, state, clock, tmp_path):
    path = write(tmp_path / 'health.json', document(clock, phase='running'))
    units = healthy_units()
    state['incidents']['observer:health'] = {'episode': 'local', 'notified': True, 'first_seen': 1}
    checks = alert['collect'](path, units, state, clock)
    assert checks['observer:health']['status'] == 'failed'
    units['codex-gitlab-monitor.service']['ActiveState'] = 'activating'
    checks = alert['collect'](path, units, state, clock)
    assert 'observer:health' not in checks
    assert state['incidents']['observer:health']['notified'] is True


def test_inventory_interval_does_not_hide_missing_service_cycles(alert, state, clock, tmp_path):
    path = write(tmp_path / 'health.json', document(clock, interval_seconds=7200,
                                                   sampled=clock['mono'] - 2101))
    checks = alert['collect'](path, healthy_units(), state, clock)
    assert checks['observer:health']['status'] == 'failed'


def test_main_with_real_local_fixture_commands_preserves_snapshot_and_suppresses_repeat(alert, tmp_path):
    import subprocess
    clock = alert['now']()
    snapshot = write(tmp_path / 'health.json', document(clock, {'shared': issue()}))
    evidence = snapshot.read_bytes()
    state_dir = tmp_path / 'private'; state_dir.mkdir(mode=0o700)
    units = tmp_path / 'systemctl'
    wire = '\n\n'.join('\n'.join(key+'='+value for key,value in row.items()) for row in healthy_units().values())
    units.write_text('#!'+sys.executable+'\nprint('+repr(wire)+')\n'); units.chmod(0o700)
    calls = tmp_path / 'calls'
    sender = tmp_path / 'notify'
    sender.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\n'
                      'with Path('+repr(str(calls))+').open("a") as f: f.write(repr(sys.argv[1:])+"\\n")\n')
    sender.chmod(0o700)
    argv = [sys.executable, str(ALERT), '--snapshot', str(snapshot), '--state', str(state_dir / 'state.json'),
            '--systemctl', str(units), '--notify-command', str(sender)]
    first = subprocess.run(argv, capture_output=True, text=True, timeout=15, check=True)
    second = subprocess.run(argv, capture_output=True, text=True, timeout=15, check=True)
    assert json.loads(first.stdout)['sent'] == 1
    assert json.loads(second.stdout)['sent'] == 0
    assert len(calls.read_text().splitlines()) == 1
    assert snapshot.read_bytes() == evidence


def test_concurrent_checker_respects_existing_lock(alert, tmp_path):
    import argparse
    import fcntl
    root = tmp_path / 'state'; root.mkdir(mode=0o700)
    target = root / 'state.json'
    lock = target.with_suffix('.lock')
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        args = argparse.Namespace(state=target, snapshot=tmp_path / 'missing',
                                  systemctl=Path('/not-executed'), notify_command=Path('/not-executed'),
                                  cycle_seconds=900)
        assert alert['check'](args) == {'status': 'busy', 'sent': 0}
        assert not target.exists()
    finally:
        os.close(descriptor)


def test_reset_failed_without_new_successful_invocation_is_not_recovery(alert, state, clock, tmp_path):
    units = healthy_units()
    service = units['codex-gitlab-monitor.service']
    service.update(ActiveState='failed', Result='exit-code', ExecMainStatus='1')
    path = write(tmp_path / 'health.json', document(clock))
    calls = []
    sender = lambda *args: calls.append(args)
    status_path = tmp_path / 'state.json'
    alert['deliver'](alert['collect'](path, units, state, clock), state, status_path,
                     Path('/fixture'), clock, sender=sender)
    assert len(calls) == 1
    service.update(ActiveState='inactive', Result='success', ExecMainStatus='0')
    alert['deliver'](alert['collect'](path, units, state, clock), state, status_path,
                     Path('/fixture'), clock, sender=sender)
    assert len(calls) == 1 and state['incidents']['systemd:service']['notified'] is True
    service.update(InvocationID='two', ExecMainStartTimestampMonotonic='3000000')
    alert['deliver'](alert['collect'](path, units, state, clock), state, status_path,
                     Path('/fixture'), clock, sender=sender)
    assert len(calls) == 2 and 'systemd:service' not in state['incidents']


def test_new_service_invocation_without_export_is_unknown_until_stale(alert, state, clock, tmp_path):
    units = healthy_units()
    units['codex-gitlab-monitor.service']['ExecMainStartTimestampMonotonic'] = str(int(clock['mono'] * 1000000))
    path = write(tmp_path / 'health.json', document(clock, sampled=clock['mono'] - 100))
    assert 'observer:health' not in alert['collect'](path, units, state, clock)
    clock['mono'] += 2101
    assert alert['collect'](path, units, state, clock)['observer:health']['status'] == 'failed'


def test_real_busy_tick_preserves_health_without_false_warning(health_flow, alert, tmp_path):
    f = health_flow
    f.tick()
    path = Path(f.config['queue_file']).with_name('health.json')
    original = path.read_bytes()
    lock = f.m['mq_lock'](f.config, 'consumer')
    try:
        assert f.tick() == {'cycle': 'busy', 'writes_performed': False}
    finally:
        os.close(lock)
    assert path.read_bytes() == original
    value = json.loads(original)
    clock = {'boot': value['boot_id'], 'mono': value['sampled'] + 10,
             'wall': value['wall_time'] + 10, 'suspend': 0.}
    state = {'version': 1, 'boot': clock['boot'], 'grace_until': 0., 'suspend': 0.,
             'incidents': {}, 'queue_id': None}
    units = healthy_units()
    units['codex-gitlab-monitor.service'].update(InvocationID='busy-invocation',
        ExecMainStartTimestampMonotonic=str(int((value['sampled'] + 5) * 1000000)))
    calls = []
    alert['deliver'](alert['collect'](path, units, state, clock), state, tmp_path / 'state.json',
                     Path('/fixture'), clock, sender=lambda *args: calls.append(args))
    assert calls == [] and state['incidents'] == {}
    # A manual consumer can also publish its running marker after that busy invocation.
    write(path, {**value, 'phase': 'running', 'sampled': clock['mono'], 'invocation_id': ''})
    assert 'observer:health' not in alert['collect'](path, units, state, clock)


@pytest.mark.parametrize('operation', ['intake', 'recovery'])
def test_actual_diagnostic_failure_and_success_share_key(flow, operation):
    f = flow
    job = f.q.enqueue(11, 82, source_key='health-keys', kind='code', head=f.context['head'],
        source={'origin': 'automatic', 'head': f.context['head']}, context=copy.deepcopy(f.context))
    record = f.q.mr(11, 82); record['hold'] = {'job_id': job['id']}
    f.q.put_mr(record)
    f.m['mq_health_begin'](f.config, f.q)
    key = 'intake_error:11:82' if operation == 'intake' else 'recovery_error:' + job['id']
    f.m['mq_diagnostic'](f.q, key, RuntimeError('read failed'))
    observation = f.config['_health']['checks']['diagnostic:' + key]
    assert observation['status'] == 'failed' and observation['job'] == job['id']
    f.m['mq_health_ok'](f.config, key)
    assert observation['status'] == 'ok'


@pytest.mark.parametrize('limit', [1, 100])
def test_validated_mr_retirement_retires_diagnostic_and_real_http_scope(flow, module, limit):
    from types import SimpleNamespace
    import urllib.error
    f = flow
    for iid in (82, 83):
        f.q.put_mr(f.q.mr(11, iid))
    f.m['mq_health_begin'](f.config, f.q)
    f.m['mq_diagnostic'](f.q, 'inventory_error:11:82', RuntimeError('bad context'))
    f.m['mq_diagnostic'](f.q, 'inventory_error:11:83', RuntimeError('other MR'))
    def rejected(*args, **kwargs):
        raise urllib.error.HTTPError('https://fixture', 403, 'denied', {}, None)
    api = SimpleNamespace(config=f.config, guard=None, base='https://fixture', _token='fixture',
                          opener=SimpleNamespace(open=rejected))
    with pytest.raises(RuntimeError, match='HTTP 403'):
        module['MonitorGitLab'].get(api, '/projects/11/merge_requests/82/discussions')
    checks = f.config['_health']['checks']
    http_key = next(key for key in checks if key.startswith('gitlab:http:'))
    assert checks[http_key]['repository'] == 11 and checks[http_key]['iid'] == 82
    f.config['_checked_mr_states'] = {}
    f.m['mq_rotate_mrs'](f.q, f.config, limit)
    assert checks[http_key]['status'] == 'failed' and len(f.q.mrs()) == 2
    f.config['_checked_mr_states'] = {(11, 82): 'closed'}
    f.m['mq_rotate_mrs'](f.q, f.config, limit)
    before = copy.deepcopy(f.q.mrs())
    assert [(r['repository_id'], r['iid']) for r in before] == ([(11, 83)] if limit == 1 else [(11, 82), (11, 83)])
    f.m['mq_health_publish'](f.config, f.q, 'finished')
    assert f.q.mrs() == before
    assert checks[http_key]['status'] == 'retired'
    assert checks['diagnostic:inventory_error:11:82']['status'] == 'retired'
    assert checks['diagnostic:inventory_error:11:83']['status'] == 'failed'


def test_closed_mr_with_live_hold_keeps_operational_incident(flow):
    f = flow
    record = f.q.mr(11, 82); record['hold'] = {'job_id': 'held-job'}
    f.q.put_mr(record)
    f.config['_checked_mr_states'] = {(11, 82): 'closed'}
    f.m['mq_health_begin'](f.config, f.q)
    f.m['mq_diagnostic'](f.q, 'inventory_error:11:82', RuntimeError('read failed'))
    f.m['mq_health_publish'](f.config, f.q, 'finished')
    assert f.config['_health']['checks']['diagnostic:inventory_error:11:82']['status'] == 'failed'
    assert f.q.mr(11, 82) == record


def test_successful_terminal_retry_exports_and_delivers_matching_recovery(flow, alert, state, clock, tmp_path, monkeypatch):
    f = flow
    f.config['reviewers'] = ['claude']
    f.q.enqueue(11, 82, source_key='health-retry', kind='code', head=f.context['head'],
        source={'origin': 'automatic', 'head': f.context['head']}, context=copy.deepcopy(f.context))
    job = f.q.reserve({11})
    stage = f.q.stage_start(job, 'claude', 'first')
    f.q.stage_end(job, stage['id'], error={'message': 'failed'}, terminal=True)
    f.m['mq_health_begin'](f.config, f.q)
    f.m['mq_health_publish'](f.config, f.q, 'finished')
    key = 'reviewer:' + job['id'] + ':claude'
    calls = []
    sender = lambda *args: calls.append(args)
    alert['deliver']({'monitor:' + key: f.config['_health']['checks'][key]}, state,
        tmp_path / 'state.json', Path('/fixture'), clock, sender=sender)
    assert len(calls) == 1
    assert f.q.requeue_failed(f.q.job(job['id']))
    retry = f.q.job(job['id'])
    due = retry['retry_at'] + 1
    monkeypatch.setitem(f.m, 'mq_stamp', lambda: due)
    job = f.q.reserve({11})
    stage = f.q.stage_start(job, 'claude', 'retry')
    f.q.stage_end(job, stage['id'], result=domain(), terminal=True)
    f.q.finish(job, 'reviewed', reviewed=True)
    assert f.q.job(job['id'])['state'] == 'completed'
    f.m['mq_health_publish'](f.config, f.q, 'finished')
    assert f.config['_health']['checks'][key]['status'] == 'ok'
    alert['deliver']({'monitor:' + key: f.config['_health']['checks'][key]}, state,
        tmp_path / 'state.json', Path('/fixture'), clock, sender=sender)
    assert len(calls) == 2 and 'recuperação' in calls[-1][1]
