"""Exercise client selection and native runtime metadata through the real CLI."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


CLI = Path(os.environ.get('CODEX_SESSION_STATS_TEST_CLI',
                         Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats'))


@pytest.fixture
def runtime_homes(tmp_path):
    homes = {name: tmp_path / name for name in ('codex', 'claude', 'copilot')}
    for home in homes.values():
        home.mkdir()
    rollout = homes['codex'] / 'rollout.jsonl'
    rollout.write_text('\n'.join(json.dumps(row) for row in (
        {'type': 'session_meta', 'payload': {'id': 'codex-child'}},
        {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': 'codex-turn'}},
        {'type': 'turn_context', 'payload': {
            'turn_id': 'codex-turn', 'model': 'gpt-6.1-sol', 'effort': 'high'}},
    )) + '\n')
    with sqlite3.connect(homes['codex'] / 'state_5.sqlite') as database:
        database.execute('create table threads (id text primary key, rollout_path text)')
        database.execute('insert into threads values (?, ?)', ('codex-child', str(rollout)))
    write_claude(homes['claude'], [claude_call()])
    write_copilot(homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'medium'}),
        ('assistant.turn_start', {'turnId': 'copilot-turn', 'model': 'gpt-6-sol'}),
    ])
    return homes


def claude_call(message_id='claude-turn', *, model='claude-opus-5-5', effort='xhigh',
                agent_id=None):
    row = {
        'type': 'assistant', 'sessionId': 'claude-child', 'uuid': message_id,
        'requestId': message_id, 'isSidechain': agent_id is not None,
        'perTurnEffort': effort,
        'message': {'id': message_id, 'model': model, 'stop_reason': 'tool_use',
                    'content': [{'type': 'tool_use', 'id': 'tool-' + message_id,
                                 'name': 'Bash', 'input': {'command': 'codex-session-stats current'}}]},
    }
    if agent_id is not None:
        row['agentId'] = agent_id
    return row


def write_claude(home, rows, *, agent_id=None):
    parent = home / 'projects/project'
    if agent_id is None:
        path = parent / 'claude-child.jsonl'
    else:
        path = parent / 'claude-child/subagents' / f'agent-{agent_id}.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
    return path


def write_copilot(home, events, *, session_id='copilot-child'):
    path = home / 'session-state' / session_id / 'events.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, event in enumerate(events):
        kind, data, *agent = event
        row = {'id': f'event-{index}', 'parentId': f'event-{index-1}' if index else None,
               'timestamp': '2026-10-12T03:00:00Z', 'type': kind, 'data': data}
        if agent:
            row['agentId'] = agent[0]
        rows.append(row)
    path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
    return path


def invoke(homes, *arguments, environment=None, input_text=None):
    env = os.environ.copy()
    for key in ('CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CLAUDE_CODE_SESSION_ID', 'CLAUDE_EFFORT'):
        env.pop(key, None)
    env.update(environment or {})
    return subprocess.run(
        [sys.executable, str(CLI), 'current', '--format', 'json',
         '--codex-home', str(homes['codex']), '--claude-home', str(homes['claude']),
         '--copilot-home', str(homes['copilot']), *arguments],
        env=env, input=input_text, capture_output=True, text=True, check=False,
    )


@pytest.mark.parametrize(('client', 'model'), (
    ('codex', 'gpt-6.1-sol'), ('claude', 'claude-opus-5-5'),
))
def test_explicit_client_ignores_inherited_other_client_identity(runtime_homes, client, model):
    result = invoke(runtime_homes, '--client', client, environment={
        'CODEX_THREAD_ID': 'codex-child', 'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['client'] == client
    assert data['session_id'] == f'{client}-child'
    assert data['model'] == model
    assert data['reasoning_effort_status'] == 'known'


def test_auto_rejects_two_inherited_identities(runtime_homes):
    result = invoke(runtime_homes, environment={
        'CODEX_THREAD_ID': 'codex-child', 'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'ambiguous' in result.stderr.lower()


def test_explicit_client_never_falls_back_to_another_client(runtime_homes):
    result = invoke(runtime_homes, '--client', 'claude', environment={'CODEX_THREAD_ID': 'codex-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'CLAUDE_CODE_SESSION_ID' in result.stderr


def test_auto_uses_one_visible_native_identity(runtime_homes):
    result = invoke(runtime_homes, environment={'CODEX_THREAD_ID': 'codex-child'})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['client'] == 'codex'


@pytest.mark.parametrize('client', ('codex', 'claude'))
def test_explicit_session_id_cannot_override_runtime_identity(runtime_homes, client):
    result = invoke(runtime_homes, '--client', client, '--session-id', 'other', environment={
        'CODEX_THREAD_ID': 'codex-child', 'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'does not match' in result.stderr


def test_copilot_identity_cannot_escape_session_directory(runtime_homes):
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', '../copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'invalid session identity' in result.stderr


def test_claude_model_change_uses_latest_pending_call(runtime_homes):
    old = claude_call('old', model='claude-sonnet-4-6', effort='medium')
    result_row = {'type': 'user', 'sessionId': 'claude-child', 'message': {
        'content': [{'type': 'tool_result', 'tool_use_id': 'tool-old'}]}}
    write_claude(runtime_homes['claude'], [old, result_row, claude_call()])
    result = invoke(runtime_homes, '--client', 'claude',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['model'] == 'claude-opus-5-5'
    assert data['reasoning_effort'] == 'xhigh'
    assert data['turn_id'] == 'claude-turn'


@pytest.mark.parametrize('tail', (
    {'type': 'user', 'sessionId': 'claude-child', 'message': {'content': [
        {'type': 'tool_result', 'tool_use_id': 'tool-claude-turn'}]}},
    {'type': 'user', 'sessionId': 'claude-child', 'message': {'content': 'new prompt'}},
    {'type': 'assistant', 'sessionId': 'claude-child', 'message': {
        'id': 'finished', 'model': 'claude-opus-5-5', 'stop_reason': 'end_turn', 'content': []}},
))
def test_claude_never_reuses_a_completed_or_previous_call(runtime_homes, tail):
    write_claude(runtime_homes['claude'], [claude_call(), tail])
    result = invoke(runtime_homes, '--client', 'claude',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'active' in result.stderr.lower()


def test_claude_subagent_uses_own_transcript(runtime_homes):
    write_claude(runtime_homes['claude'], [claude_call(model='claude-sonnet-4-6',
                 effort='high', agent_id='worker')], agent_id='worker')
    result = invoke(runtime_homes, '--client', 'claude', '--agent-id', 'worker',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['agent_id'] == 'worker'
    assert data['model'] == 'claude-sonnet-4-6'
    assert data['reasoning_effort'] == 'high'


def test_missing_subagent_never_returns_parent(runtime_homes):
    result = invoke(runtime_homes, '--client', 'claude', '--agent-id', 'missing',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'missing' in result.stderr


def test_claude_missing_effort_does_not_infer_unsupported(runtime_homes):
    row = claude_call()
    row.pop('perTurnEffort')
    write_claude(runtime_homes['claude'], [row])
    result = invoke(runtime_homes, '--client', 'claude',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'effort' in result.stderr.lower()


def test_claude_environment_effort_alone_cannot_identify_the_child_effort(runtime_homes):
    row = claude_call()
    row.pop('perTurnEffort')
    write_claude(runtime_homes['claude'], [row])
    result = invoke(runtime_homes, '--client', 'claude', environment={
        'CLAUDE_CODE_SESSION_ID': 'claude-child', 'CLAUDE_EFFORT': 'high'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'effort' in result.stderr


def test_claude_rejects_conflicting_effective_effort(runtime_homes):
    result = invoke(runtime_homes, '--client', 'claude', environment={
        'CLAUDE_CODE_SESSION_ID': 'claude-child', 'CLAUDE_EFFORT': 'medium'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'conflicting effort' in result.stderr


def test_claude_late_fragment_cannot_reopen_a_completed_tool(runtime_homes):
    result_row = {'type': 'user', 'sessionId': 'claude-child', 'message': {'content': [
        {'type': 'tool_result', 'tool_use_id': 'tool-claude-turn'}]}}
    write_claude(runtime_homes['claude'], [claude_call(), result_row, claude_call()])
    result = invoke(runtime_homes, '--client', 'claude',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'active' in result.stderr


@pytest.mark.parametrize('client', ('claude', 'copilot'))
def test_malformed_native_record_produces_no_settings(runtime_homes, client):
    path = (runtime_homes['claude'] / 'projects/project/claude-child.jsonl' if client == 'claude'
            else runtime_homes['copilot'] / 'session-state/copilot-child/events.jsonl')
    with path.open('a') as handle:
        handle.write('{"broken":\n')
    result = invoke(runtime_homes, '--client', client, '--session-id', f'{client}-child',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'malformed runtime record' in result.stderr


def test_documented_claude_statusline_can_report_unsupported_effort(runtime_homes):
    snapshot = {'session_id': 'claude-child', 'prompt_id': 'prompt-1',
                'model': {'id': 'claude-haiku-4-5'}, 'thinking': {'enabled': False}}
    result = invoke(runtime_homes, '--client', 'claude', '--claude-statusline',
                    environment={'CLAUDE_CODE_SESSION_ID': 'claude-child'},
                    input_text=json.dumps(snapshot))
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['model'] == 'claude-haiku-4-5'
    assert data['reasoning_effort'] is None
    assert data['reasoning_effort_status'] == 'unsupported'
    assert data['source'] == 'claude_statusline'


@pytest.mark.parametrize(('payload_id', 'argument_id', 'environment_id', 'error'), (
    ('other', None, 'claude-child', 'identity mismatch'),
    ('other', 'other', 'claude-child', 'does not match'),
    ('claude-child', None, None, 'caller identity'),
))
def test_statusline_input_requires_matching_caller_identity(
    runtime_homes, payload_id, argument_id, environment_id, error
):
    snapshot = {'session_id': payload_id, 'prompt_id': 'prompt', 'model': {'id': 'claude-opus-5-5'},
                'effort': {'level': 'high'}}
    arguments = ['--client', 'claude', '--claude-statusline']
    if argument_id is not None:
        arguments.extend(['--session-id', argument_id])
    environment = {'CLAUDE_CODE_SESSION_ID': environment_id} if environment_id else {}
    result = invoke(runtime_homes, *arguments, environment=environment, input_text=json.dumps(snapshot))
    assert result.returncode == 1
    assert result.stdout == ''
    assert error in result.stderr


def test_copilot_explicit_identity_and_current_turn(runtime_homes):
    before = {path: path.read_bytes() for path in runtime_homes['copilot'].rglob('*') if path.is_file()}
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child',
                    environment={'CODEX_THREAD_ID': 'codex-child', 'CLAUDE_CODE_SESSION_ID': 'claude-child'})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        'client': 'copilot', 'session_id': 'copilot-child', 'agent_id': None,
        'turn_id': 'copilot-turn', 'model': 'gpt-6-sol', 'reasoning_effort': 'medium',
        'reasoning_effort_status': 'known', 'source': 'copilot_events',
    }
    assert {path: path.read_bytes() for path in before} == before


def test_copilot_model_and_effort_change(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'medium'}),
        ('assistant.turn_start', {'turnId': 'old', 'model': 'gpt-6-sol'}),
        ('assistant.turn_end', {'turnId': 'old'}),
        ('session.model_change', {'newModel': 'claude-sonnet-4-6', 'reasoningEffort': 'high'}),
        ('assistant.turn_start', {'turnId': 'new', 'model': 'claude-sonnet-4-6'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert (data['turn_id'], data['model'], data['reasoning_effort']) == ('new', 'claude-sonnet-4-6', 'high')


def test_copilot_pending_model_change_does_not_relabel_active_turn(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'medium'}),
        ('assistant.turn_start', {'turnId': 'current', 'model': 'gpt-6-sol'}),
        ('session.model_change', {'newModel': 'claude-sonnet-4-6', 'reasoningEffort': 'high'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert (data['model'], data['reasoning_effort']) == ('gpt-6-sol', 'medium')


def test_copilot_resume_replaces_previous_session_effort(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'low'}),
        ('assistant.turn_start', {'turnId': 'old', 'model': 'gpt-6-sol'}),
        ('assistant.turn_end', {'turnId': 'old'}),
        ('session.resume', {'eventCount': 3, 'resumeTime': '2026-10-12T03:00:00Z',
                            'reasoningEffort': 'high'}),
        ('assistant.turn_start', {'turnId': 'new', 'model': 'gpt-6-sol'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['reasoning_effort'] == 'high'


def test_copilot_resume_missing_effort_cannot_reuse_previous_value(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'low'}),
        ('assistant.turn_start', {'turnId': 'old', 'model': 'gpt-6-sol'}),
        ('assistant.turn_end', {'turnId': 'old'}),
        ('session.resume', {'eventCount': 3, 'resumeTime': '2026-10-12T03:00:00Z'}),
        ('assistant.turn_start', {'turnId': 'new', 'model': 'gpt-6-sol'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'effort' in result.stderr


def test_copilot_resume_cannot_reopen_abandoned_work(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'low'}),
        ('assistant.turn_start', {'turnId': 'old', 'model': 'gpt-6-sol'}),
        ('session.resume', {'eventCount': 2, 'resumeTime': '2026-10-12T03:00:00Z',
                            'continuePendingWork': False, 'reasoningEffort': 'high'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'active' in result.stderr


def test_copilot_resume_preserves_pending_inference_settings(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'low'}),
        ('assistant.turn_start', {'turnId': 'old', 'model': 'gpt-6-sol'}),
        ('session.resume', {'eventCount': 2, 'resumeTime': '2026-10-12T03:00:00Z',
                            'continuePendingWork': True, 'reasoningEffort': 'high'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['reasoning_effort'] == 'low'


def test_copilot_model_deselection_preserves_independent_effort(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'high'}),
        ('session.model_deselected', {'previousModel': 'gpt-6-sol'}),
        ('assistant.turn_start', {'turnId': 'current', 'model': 'gpt-6-astra'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['reasoning_effort'] == 'high'


def test_copilot_retry_uses_its_own_resolved_model(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'high'}),
        ('assistant.turn_start', {'turnId': 'current', 'model': 'gpt-6-sol'}),
        ('assistant.turn_retry', {'turnId': 'current', 'reason': 'retry', 'model': 'gpt-6-astra'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['model'] == 'gpt-6-astra'


def test_copilot_retry_missing_model_cannot_reuse_previous_attempt(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'high'}),
        ('assistant.turn_start', {'turnId': 'current', 'model': 'gpt-6-sol'}),
        ('assistant.turn_retry', {'turnId': 'current', 'reason': 'retry'}),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'model' in result.stderr


@pytest.mark.parametrize('kind', ('assistant.turn_start', 'assistant.turn_retry'))
def test_copilot_model_bound_effort_cannot_identify_another_model(runtime_homes, kind):
    events = [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'high',
                           'reasoningEffortManaged': True, 'reasoningEffortModel': 'gpt-6-sol'}),
    ]
    if kind == 'assistant.turn_retry':
        events.append(('assistant.turn_start', {'turnId': 'current', 'model': 'gpt-6-sol'}))
    events.append((kind, {'turnId': 'current', 'model': 'gpt-6-astra'}))
    write_copilot(runtime_homes['copilot'], events)
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'effort' in result.stderr


def test_copilot_subagent_never_inherits_root_effort(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'medium'}),
        ('assistant.turn_start', {'turnId': 'root', 'model': 'gpt-6-sol'}),
        ('assistant.turn_start', {'turnId': 'child', 'model': 'claude-sonnet-4-6'}, 'worker'),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child',
                    '--agent-id', 'worker')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'effort' in result.stderr


def test_copilot_subagent_uses_its_explicit_runtime_settings(runtime_homes):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'medium'}),
        ('assistant.turn_start', {'turnId': 'root', 'model': 'gpt-6-sol'}),
        ('session.model_change', {'newModel': 'claude-sonnet-4-6', 'reasoningEffort': 'high'}, 'worker'),
        ('assistant.turn_start', {'turnId': 'child', 'model': 'claude-sonnet-4-6'}, 'worker'),
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child',
                    '--agent-id', 'worker')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert (data['agent_id'], data['model'], data['reasoning_effort']) == ('worker', 'claude-sonnet-4-6', 'high')


@pytest.mark.parametrize('tail', (
    ('assistant.turn_end', {'turnId': 'copilot-turn'}),
    ('abort', {'reason': 'cancelled'}),
    ('session.shutdown', {}),
))
def test_copilot_rejects_finished_turn(runtime_homes, tail):
    write_copilot(runtime_homes['copilot'], [
        ('session.start', {'sessionId': 'copilot-child', 'reasoningEffort': 'medium'}),
        ('assistant.turn_start', {'turnId': 'copilot-turn', 'model': 'gpt-6-sol'}), tail,
    ])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert 'active' in result.stderr.lower()


@pytest.mark.parametrize(('start', 'turn', 'error'), (
    ({'sessionId': 'other', 'reasoningEffort': 'medium'}, {'turnId': 'turn', 'model': 'gpt-6-sol'}, 'identity'),
    ({'sessionId': 'copilot-child'}, {'turnId': 'turn', 'model': 'gpt-6-sol'}, 'effort'),
    ({'sessionId': 'copilot-child', 'reasoningEffort': 'high'}, {'turnId': 'turn'}, 'model'),
    ({'sessionId': 'copilot-child', 'reasoningEffort': 'high'}, {'turnId': 'turn', 'model': 'auto'}, 'model'),
))
def test_copilot_requires_effective_runtime_evidence(runtime_homes, start, turn, error):
    write_copilot(runtime_homes['copilot'], [('session.start', start), ('assistant.turn_start', turn)])
    result = invoke(runtime_homes, '--client', 'copilot', '--session-id', 'copilot-child')
    assert result.returncode == 1
    assert result.stdout == ''
    assert error in result.stderr.lower()


def test_copilot_session_context_hook_emits_native_identity_without_writes(tmp_path):
    payload = {'sessionId': 'copilot-child', 'cwd': str(tmp_path), 'source': 'startup', 'timestamp': 0}
    result = subprocess.run([sys.executable, str(CLI), 'session-context', '--client', 'copilot'],
                            input=json.dumps(payload), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)['additionalContext']
    assert 'current --client copilot --session-id copilot-child --format json' in context
    assert 'subagent' in context
    assert list(tmp_path.iterdir()) == []
