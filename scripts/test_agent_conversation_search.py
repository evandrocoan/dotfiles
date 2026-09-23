import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / '.local/bin/codex-session-stats'
STAMP = '2026-09-08T15:37:00Z'
URL = 'https://gitlab.example/ai/khomp-ai/-/merge_requests/34'


class ConversationSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.codex = self.root / 'codex'
        self.claude = self.root / 'claude'
        self.codex.mkdir()
        self.claude.mkdir()

    def write(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in records))
        return path

    def meta(self, session='codex-one', source='vscode'):
        return {'type': 'session_meta', 'payload': {
            'id': session, 'cwd': '/work/khomp-ai', 'source': source}}

    def message(self, text, role='assistant', stamp=STAMP):
        return {'timestamp': stamp, 'type': 'response_item', 'payload': {
            'type': 'message', 'role': role,
            'content': [{'type': 'output_text', 'text': text}]}}

    def find(self, *args, expect=0):
        result = subprocess.run([
            sys.executable, '-B', str(SCRIPT), 'find', *args,
            '--codex-home', str(self.codex), '--claude-home', str(self.claude),
            '--format', 'json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, expect, result.stderr)
        return json.loads(result.stdout) if expect == 0 else result

    def test_codex_old_rollouts_current_title_and_read_only_sources(self):
        path = self.write(self.codex / 'sessions/old.jsonl', [
            self.meta(), self.message('Validated ' + URL)])
        self.write(self.codex / 'sessions/new.jsonl', [self.meta(), self.message('Later task')])
        self.write(self.codex / 'session_index.jsonl', [
            {'id': 'codex-one', 'thread_name': 'Old title'},
            {'id': 'codex-one', 'thread_name': 'Current renamed chat'}])
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        output = self.find(URL, '--agent', 'codex')
        self.assertEqual(len(output['conversations']), 1)
        result = output['conversations'][0]
        self.assertEqual((result['session_id'], result['title'], result['cwd']),
                         ('codex-one', 'Current renamed chat', '/work/khomp-ai'))
        match = result['matches'][0]
        self.assertEqual((match['path'], match['line'], match['role']), (str(path), 2, 'assistant'))
        self.assertEqual(match['timestamp'], '2026-09-08 12:37:00')
        self.assertEqual(output['coverage']['files_scanned'], 2)
        self.assertEqual({p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}, before)

    def test_claude_text_blocks_and_custom_title(self):
        path = self.write(self.claude / 'projects/project/claude-one.jsonl', [
            {'type': 'user', 'sessionId': 'claude-one', 'cwd': '/work/api',
             'timestamp': STAMP, 'message': {'role': 'user', 'content': 'Look into retry policy'}},
            {'type': 'assistant', 'sessionId': 'claude-one', 'timestamp': STAMP,
             'message': {'role': 'assistant', 'content': [
                 {'type': 'thinking', 'thinking': 'secret reasoning'},
                 {'type': 'text', 'text': 'The retry policy was reviewed.'}]}},
            {'type': 'custom-title', 'sessionId': 'claude-one', 'customTitle': 'API retries'},
            {'type': 'ai-title', 'sessionId': 'claude-one', 'aiTitle': 'Generated title'}])
        result = self.find('retry policy', '--agent', 'claude')['conversations'][0]
        self.assertEqual((result['agent'], result['title'], result['session_id']),
                         ('claude', 'API retries', 'claude-one'))
        self.assertEqual({m['role'] for m in result['matches']}, {'user', 'assistant'})
        self.assertEqual({m['path'] for m in result['matches']}, {str(path)})
        self.assertEqual(self.find('secret reasoning')['conversations'], [])

    def test_mr_number_boundary_and_project_filter(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            self.message(URL + '8'), self.message('Reviewed unrelated project MR 34'),
            self.message('Reviewed ' + URL), self.message('Reviewed !34 in khomp-ai')])
        result = self.find('--mr', '34', '--project', 'khomp-ai')['conversations'][0]
        self.assertEqual(result['match_count'], 3)
        self.assertFalse(any(URL + '8' in m['excerpt'] for m in result['matches']))
        exact = self.find(URL)['conversations'][0]
        self.assertEqual(exact['match_count'], 1)

    def test_duplicate_events_and_rollouts_are_grouped(self):
        event = {'timestamp': STAMP, 'type': 'event_msg', 'payload': {
            'type': 'agent_message', 'message': 'Review marker'}}
        for name in ('one', 'two'):
            self.write(self.codex / f'sessions/{name}.jsonl', [
                self.meta(), event, self.message('Review marker')])
        result = self.find('Review marker')['conversations']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['match_count'], 1)

    def test_excludes_tools_reasoning_and_subagents(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            {'type': 'response_item', 'payload': {'type': 'function_call_output', 'output': 'tool marker'}},
            self.message('private marker', role='system'),
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant',
             'channel': 'analysis', 'content': [{'type': 'output_text', 'text': 'private marker'}]}}])
        self.write(self.codex / 'sessions/agent.jsonl', [
            self.meta('child', {'subagent': {'thread_spawn': {}}}), self.message('child marker')])
        self.assertEqual(self.find('tool marker')['conversations'], [])
        self.assertEqual(self.find('private marker')['conversations'], [])
        self.assertEqual(self.find('child marker')['conversations'], [])
        self.assertEqual(len(self.find('child marker', '--all-agents')['conversations']), 1)

    def test_event_only_and_inherited_are_distinct(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            {'timestamp': STAMP, 'type': 'event_msg', 'payload': {'type': 'item_completed',
             'item': {'type': 'AgentMessage', 'content': [{'type': 'Text', 'text': 'event marker'}]}}},
            {'timestamp': STAMP, 'type': 'compacted', 'payload': {
             'replacement_history': [self.message('inherited marker')['payload']]}}])
        self.assertEqual(self.find('event marker')['conversations'][0]['matches'][0]['origin'], 'message')
        self.assertEqual(self.find('inherited marker')['conversations'], [])
        result = self.find('inherited marker', '--include-inherited')['conversations'][0]['matches'][0]
        self.assertEqual(result['origin'], 'inherited')
        self.assertIsNone(result['timestamp'])

    def test_date_role_and_unicode_filters(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            self.message('Avaliação própria', role='user', stamp='2026-09-09T02:00:00Z'),
            self.message('AVALIAÇÃO própria', stamp='2026-09-09T04:00:00Z')])
        result = self.find('avaliação', '--role', 'user', '--since', '2026-09-08', '--until', '2026-09-08')
        self.assertEqual(result['conversations'][0]['match_count'], 1)
        self.assertEqual(result['conversations'][0]['matches'][0]['role'], 'user')
        self.assertEqual(self.find('avaliação', '--since', '2026-09-10')['conversations'], [])

    def test_repeated_messages_on_distinct_dates_survive_deduplication(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            self.message('same text', stamp='2026-09-08T15:00:00Z'),
            self.message('same text', stamp='2026-09-09T15:00:00Z')])
        self.assertEqual(self.find('same text')['conversations'][0]['match_count'], 2)
        result = self.find('same text', '--since', '2026-09-09')['conversations'][0]
        self.assertEqual(result['match_count'], 1)
        self.assertEqual(result['matches'][0]['timestamp'], '2026-09-09 12:00:00')

    def test_literal_json_escapes_and_multiline_mr_notation(self):
        path = self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            self.message('Read "quoted topic" in C:\\temp and MR\n34')])
        quoted = self.find('"quoted topic"')['conversations'][0]
        self.assertEqual(quoted['match_count'], 1)
        self.assertEqual(self.find('C:\\temp')['conversations'][0]['match_count'], 1)
        self.assertEqual(self.find('--mr', '34')['conversations'][0]['match_count'], 1)
        with path.open('a') as f:
            f.write(json.dumps(self.message(URL)).replace('/', '\\/') + '\n')
        self.assertEqual(self.find(URL)['conversations'][0]['match_count'], 1)

    def test_claude_subagents_and_compaction_are_opt_in(self):
        self.write(self.claude / 'projects/p/one.jsonl', [
            {'type': 'user', 'cwd': '/work/api', 'sessionId': 'root', 'timestamp': STAMP,
             'isCompactSummary': True, 'message': {'content': 'compaction marker'}}])
        self.write(self.claude / 'projects/p/root/subagents/child.jsonl', [
            {'type': 'assistant', 'sessionId': 'child', 'isSidechain': True,
             'message': {'content': [{'type': 'text', 'text': 'child marker'}]}}])
        self.assertEqual(self.find('compaction marker')['conversations'], [])
        self.assertEqual(self.find('compaction marker', '--include-inherited')['conversations'][0]['matches'][0]['origin'], 'inherited')
        self.assertEqual(self.find('child marker')['conversations'], [])
        self.assertEqual(self.find('child marker', '--all-agents')['conversations'][0]['session_id'], 'child')

    def test_title_search_quotes_csv_and_markdown_locations(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(), self.message('unrelated')])
        self.write(self.codex / 'session_index.jsonl', [
            {'id': 'codex-one', 'thread_name': 'Unique, renamed title', 'updated_at': STAMP}])
        result = self.find('unique, renamed')['conversations'][0]
        self.assertEqual(result['matches'][0]['origin'], 'title')
        self.assertEqual(result['matches'][0]['path'], str(self.codex / 'session_index.jsonl'))
        for fmt, expected in [('csv', '"Unique, renamed title"'), ('markdown', 'session_index.jsonl:1')]:
            with self.subTest(format=fmt):
                output = subprocess.run([sys.executable, '-B', str(SCRIPT), 'find', 'Unique, renamed',
                                         '--agent', 'codex', '--codex-home', str(self.codex), '--format', fmt],
                                        capture_output=True, text=True)
                self.assertEqual(output.returncode, 0, output.stderr)
                self.assertIn(expected, output.stdout)

    def test_both_clients_limits_and_sessions(self):
        self.write(self.codex / 'sessions/one.jsonl', [self.meta(), self.message('shared marker')])
        self.write(self.claude / 'sessions/one.jsonl', [{'type': 'user', 'sessionId': 'claude-one',
            'cwd': '/work/api', 'timestamp': STAMP, 'message': {'content': 'shared marker'}}])
        result = self.find('shared marker')
        self.assertEqual({c['agent'] for c in result['conversations']}, {'codex', 'claude'})
        limited = self.find('shared marker', '--limit', '1')
        self.assertEqual((limited['total_conversations'], len(limited['conversations'])), (2, 1))
        selected = self.find('shared marker', '--session', 'codex-one')
        self.assertEqual([c['session_id'] for c in selected['conversations']], ['codex-one'])

    def test_missing_roots_and_malformed_candidate_are_visible(self):
        path = self.write(self.codex / 'sessions/one.jsonl', [self.meta(), self.message('control')])
        with path.open('a') as f:
            f.write('{"type":"response_item", "needle": broken}\n')
        result = self.find('needle')
        self.assertEqual(result['conversations'], [])
        self.assertEqual(result['coverage']['malformed_records'], 1)
        self.assertIn(str(self.claude / 'projects'), result['coverage']['missing_roots'])
        self.assertEqual(self.find('control')['conversations'][0]['match_count'], 1)

    def test_invalid_arguments_fail(self):
        self.find(expect=2)
        self.find('word', '--since', 'bad-date', expect=1)
        self.find('word', '--since', '2026-09-09', '--until', '2026-09-08', expect=1)

    def test_original_statistics_cli_still_works(self):
        path = self.write(self.codex / 'sessions/one.jsonl', [self.meta(),
            {'timestamp': '2026-09-08T15:00:00Z', 'type': 'event_msg',
             'payload': {'type': 'task_started', 'turn_id': 'turn-one'}},
            {'timestamp': '2026-09-08T15:00:01Z', 'type': 'event_msg',
             'payload': {'type': 'user_message', 'message': 'Original request'}},
            {'timestamp': '2026-09-08T15:01:00Z', 'type': 'event_msg',
             'payload': {'type': 'task_complete', 'turn_id': 'turn-one'}}])
        with sqlite3.connect(self.codex / 'state_1.sqlite') as db:
            db.execute('create table threads(id text, rollout_path text, cwd text)')
            db.execute('insert into threads values (?,?,?)', ('codex-one', str(path), '/work/khomp-ai'))
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--codex-home', str(self.codex),
                                 '--format', 'json', '--skip-gap-analysis'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)[0]
        self.assertEqual((record['request'], record['duration_seconds']), ('Original request', 60.0))


if __name__ == '__main__':
    unittest.main()
