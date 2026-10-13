"""Real CLI/log-query integration and sanitized native-log artifact replay.

The task-owned span was captured from native logs, with IDs anonymized and
unrelated payload removed. This is not a conversation or host-transport replay.
The complete upstream log migration chain is vendored from OpenAI Codex revision
12cca49c81c8aa6a37a5cc4e39964ee3b70f9458, codex-rs/state/logs_migrations.
Its SHA-384 checksums were checked against the native _sqlx_migrations records.
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from test_codex_session_stats import CLI, add_thread, codex_home, context, finished, run_current, started


FIXTURES = Path(__file__).parent / 'fixtures/codex_runtime_logs'
MIGRATIONS = {
    '0001_logs.sql': '3ac717a6db0fc2d138f485ea4e5798f1367d5c2811db87a80ddd8b7bf8526ca0',
    '0002_logs_feedback_log_body.sql': '1cdeb6c3cddcf2f4b81995fb4f227f8578c0624568d27407c2fa2bddb7f7ba77',
}


@pytest.fixture
def native_log():
    return json.loads((FIXTURES / 'turn_log.json').read_text())


def write_logs(home, rows, *, version=2):
    path = home / f'logs_{version}.sqlite'
    with sqlite3.connect(path) as database:
        for name, expected_hash in MIGRATIONS.items():
            source = (FIXTURES / name).read_bytes()
            assert hashlib.sha256(source).hexdigest() == expected_hash
            database.executescript(source.decode())
        for index, row in enumerate(rows):
            database.execute(
                'insert into logs (ts, ts_nanos, level, target, thread_id, process_uuid, feedback_log_body) '
                'values (?, ?, ?, ?, ?, ?, ?)',
                (row.get('ts', 100 + index), row.get('ts_nanos', 0), 'TRACE', row['target'],
                 row['thread_id'], row['process_uuid'], row['feedback_log_body']),
            )
    return path


def invoke(home):
    # No host metadata, extra flags, or stdin: the acting ID is sufficient.
    return run_current(home, thread_id='worker', session_id='parent')


def assert_settings(result, *, turn='live-turn', model='gpt-6.1-sol', effort='xhigh',
                    observed_at='1970-01-01T00:01:40.000000000Z'):
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        'client': 'codex', 'session_id': 'worker', 'agent_id': None,
        'thread_id': 'worker', 'turn_id': turn, 'model': model,
        'reasoning_effort': effort, 'reasoning_effort_status': 'known', 'source': 'runtime_log',
        'settings_status': 'last_logged', 'observed_at': observed_at,
    }
    assert result.stderr == ''


def assert_failure(result, error):
    assert result.returncode == 1
    assert result.stdout == ''
    assert error in result.stderr


def test_native_artifact_recovers_missing_state_record_without_writes(codex_home, native_log):
    write_logs(codex_home, [native_log])
    before = {path.name: path.read_bytes() for path in codex_home.iterdir()}
    assert_settings(invoke(codex_home))
    assert {path.name: path.read_bytes() for path in codex_home.iterdir()} == before


@pytest.mark.parametrize('state_failure', ('absent', 'corrupt', 'missing_table'))
def test_log_fallback_recovers_unavailable_state(codex_home, native_log, state_failure):
    state = codex_home / 'state_5.sqlite'
    state.unlink()
    if state_failure == 'corrupt':
        state.write_bytes(b'not a SQLite database')
    elif state_failure == 'missing_table':
        with sqlite3.connect(state) as database:
            database.execute('pragma user_version = 1')
    write_logs(codex_home, [native_log])
    before = {path.name: path.read_bytes() for path in codex_home.iterdir()}
    assert_settings(invoke(codex_home))
    assert {path.name: path.read_bytes() for path in codex_home.iterdir()} == before


def test_log_fallback_cannot_substitute_parent_rows(codex_home, native_log):
    row = copy.deepcopy(native_log)
    row['thread_id'] = 'parent'
    row['feedback_log_body'] = row['feedback_log_body'].replace('worker', 'parent')
    write_logs(codex_home, [row])
    assert_failure(invoke(codex_home), 'no authenticated native log settings')


@pytest.mark.parametrize(('old', 'replacement', 'error'), (
    ('session_loop{thread_id=worker}', 'session_loop{thread_id=parent}', 'session identity'),
    ('thread.id=worker', 'thread.id=parent', 'turn thread identity'),
    ('conversation.id=worker', 'conversation.id=parent', 'input identity'),
    ('turn.id="live-turn"', 'turn.id="wrong-turn"', 'input identity'),
    ('submission.id="live-turn"', 'submission.id="wrong-turn"', 'submission identity'),
    ('codex.op="turn_input"', 'codex.op="other"', 'submission identity'),
    ('turn.id=live-turn', 'turn.id="bad/id"', 'invalid session identity'),
    ('model=gpt-6.1-sol', 'model=gpt-6.1-sol model=gpt-6-astra', 'duplicate'),
    ('codex.turn.reasoning_effort=xhigh}', 'codex.turn.reasoning_effort=xhigh', 'malformed'),
))
def test_log_fallback_rejects_invalid_native_envelope(codex_home, native_log, old, replacement, error):
    native_log['feedback_log_body'] = native_log['feedback_log_body'].replace(old, replacement)
    write_logs(codex_home, [native_log])
    assert_failure(invoke(codex_home), error)


def test_log_fallback_uses_latest_logged_turn_after_model_change(codex_home, native_log):
    older = copy.deepcopy(native_log)
    older['feedback_log_body'] = older['feedback_log_body'].replace('live-turn', 'older-turn').replace(
        'model=gpt-6.1-sol', 'model=gpt-6-astra').replace('reasoning_effort=xhigh', 'reasoning_effort=high')
    write_logs(codex_home, [older, native_log])
    assert_settings(invoke(codex_home), observed_at='1970-01-01T00:01:41.000000000Z')


@pytest.mark.parametrize(('timestamps', 'expected_time'), (
    (((200, 0), (100, 0)), '1970-01-01T00:03:20.000000000Z'),
    (((100, 900), (100, 1)), '1970-01-01T00:01:40.000000900Z'),
    (((100, 0), (100, 0)), '1970-01-01T00:01:40.000000000Z'),
))
def test_log_order_uses_timestamp_nanoseconds_then_row_id(codex_home, native_log, timestamps, expected_time):
    older = copy.deepcopy(native_log)
    older['feedback_log_body'] = older['feedback_log_body'].replace('live-turn', 'older-turn')
    rows = [native_log, older]
    if timestamps[0] == timestamps[1]:
        rows.reverse()
    for row, (seconds, nanos) in zip(rows, timestamps):
        row['ts'], row['ts_nanos'] = seconds, nanos
    write_logs(codex_home, rows)
    assert_settings(invoke(codex_home), observed_at=expected_time)


@pytest.mark.parametrize(('old', 'replacement', 'model', 'effort'), (
    ('model=gpt-6.1-sol', 'model=gpt-6-astra', 'gpt-6-astra', 'xhigh'),
    ('reasoning_effort=xhigh', 'reasoning_effort=high', 'gpt-6.1-sol', 'high'),
))
def test_latest_record_supersedes_older_settings(codex_home, native_log, old, replacement, model, effort):
    latest = copy.deepcopy(native_log)
    latest['feedback_log_body'] = latest['feedback_log_body'].replace(old, replacement)
    latest['process_uuid'] = 'pid:101:resumed-process'
    write_logs(codex_home, [native_log, latest])
    assert_settings(invoke(codex_home), model=model, effort=effort,
                    observed_at='1970-01-01T00:01:41.000000000Z')


@pytest.mark.parametrize(('old', 'replacement', 'error'), (
    ('model=gpt-6.1-sol', '', 'model'),
    ('model=gpt-6.1-sol', 'model=default', 'resolved effective model'),
    ('reasoning_effort=xhigh', 'reasoning_effort=""', 'effort'),
    ('codex.turn.reasoning_effort=xhigh', '', 'effort'),
    ('reasoning_effort=xhigh', 'reasoning_effort=unknown', 'known reasoning effort'),
))
def test_invalid_latest_settings_do_not_fall_back_to_older_record(codex_home, native_log, old, replacement, error):
    latest = copy.deepcopy(native_log)
    latest['feedback_log_body'] = latest['feedback_log_body'].replace(old, replacement)
    write_logs(codex_home, [native_log, latest])
    assert_failure(invoke(codex_home), error)


def test_log_fallback_does_not_parse_settings_in_tool_payload(codex_home, native_log):
    native_log['feedback_log_body'] = 'session_loop{thread_id=worker}: payload ' + native_log['feedback_log_body']
    write_logs(codex_home, [native_log])
    assert_failure(invoke(codex_home), 'no authenticated native log settings')


def test_log_fallback_ignores_untrusted_payload_after_native_span(codex_home, native_log):
    native_log['feedback_log_body'] += ' payload model=wrong codex.turn.reasoning_effort=low'
    write_logs(codex_home, [native_log])
    assert_settings(invoke(codex_home))


def test_log_fallback_skips_newer_event_without_feedback_body(codex_home, native_log):
    empty = copy.deepcopy(native_log)
    empty['feedback_log_body'] = None
    write_logs(codex_home, [native_log, empty])
    assert_settings(invoke(codex_home))


@pytest.mark.parametrize(('seconds', 'nanos'), ((100, -1), (100, 1_000_000_000), (2**62, 0)))
def test_log_fallback_rejects_invalid_observation_time(codex_home, native_log, seconds, nanos):
    native_log['ts'], native_log['ts_nanos'] = seconds, nanos
    write_logs(codex_home, [native_log])
    assert_failure(invoke(codex_home), 'malformed native log timestamp')


@pytest.mark.parametrize('field', ('target', 'otel'))
def test_log_fallback_requires_native_logger_and_task_span(codex_home, native_log, field):
    if field == 'target':
        native_log['target'] = 'user_payload'
    else:
        native_log['feedback_log_body'] = native_log['feedback_log_body'].replace(
            'otel.name="session_task.turn"', 'otel.name="user_payload"')
    write_logs(codex_home, [native_log])
    assert_failure(invoke(codex_home), 'no authenticated native log settings')


@pytest.mark.parametrize('event', ('Agent loop exited', 'Shutting down Codex instance'))
def test_shutdown_does_not_claim_activity_or_hide_last_logged_settings(codex_home, native_log, event):
    shutdown = {'target': 'codex_core::session::handlers', 'thread_id': 'worker',
                'process_uuid': native_log['process_uuid'],
                'feedback_log_body': 'session_loop{thread_id=worker}: ' + event}
    write_logs(codex_home, [native_log, shutdown])
    assert_settings(invoke(codex_home))


@pytest.mark.parametrize(('events', 'metadata_id', 'error'), (
    ([started('live-turn'), context('live-turn'), finished('live-turn')], None, 'no longer active'),
    ([started('live-turn')], None, 'no context'),
    ([started('live-turn'), context('live-turn')], 'parent', 'rollout identity'),
))
def test_fallback_never_bypasses_invalid_existing_rollout(codex_home, native_log, events, metadata_id, error):
    add_thread(codex_home, 'worker', events, metadata_id=metadata_id)
    write_logs(codex_home, [native_log])
    assert_failure(invoke(codex_home), error)


def test_valid_rollout_remains_primary(codex_home, native_log):
    add_thread(codex_home, 'worker', [started('live-turn'), context('live-turn', 'gpt-6-astra', 'high')])
    write_logs(codex_home, [native_log])
    result = invoke(codex_home)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        'client': 'codex', 'session_id': 'worker', 'agent_id': None,
        'thread_id': 'worker', 'turn_id': 'live-turn', 'model': 'gpt-6-astra',
        'reasoning_effort': 'high', 'reasoning_effort_status': 'known', 'source': 'turn_context',
    }


def test_log_database_version_is_selected_numerically(codex_home, native_log):
    older = copy.deepcopy(native_log)
    older['feedback_log_body'] = older['feedback_log_body'].replace('model=gpt-6.1-sol', 'model=gpt-6-astra')
    write_logs(codex_home, [older])
    write_logs(codex_home, [native_log], version=10)
    assert_settings(invoke(codex_home))


def test_log_fallback_never_uses_older_database_when_newest_is_invalid(codex_home, native_log):
    write_logs(codex_home, [native_log])
    (codex_home / 'logs_10.sqlite').write_bytes(b'invalid log database')
    assert_failure(invoke(codex_home), 'not a database')


def test_log_failure_preserves_original_lookup_error(codex_home):
    assert_failure(invoke(codex_home), 'no state record for acting thread worker; log fallback failed: no runtime logs database')


def test_text_output_explains_last_logged_provenance(codex_home, native_log):
    write_logs(codex_home, [native_log])
    result = subprocess.run(
        [sys.executable, str(CLI), 'current', '--client', 'codex', '--codex-home', str(codex_home)],
        env={**os.environ, 'CODEX_THREAD_ID': 'worker', 'CODEX_SESSION_ID': 'parent'},
        stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        'Model: gpt-6.1-sol\nReasoning effort: xhigh\nClient: codex\nSession: worker\n'
        'Turn: live-turn\nSource: runtime_log\nSettings status: last_logged\n'
        'Observed at: 1970-01-01T00:01:40.000000000Z\n'
    )
    assert result.stderr == ''
