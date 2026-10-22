"""Installed clients use ordinary HTTP GitLab tools; all writes/model output are local fixtures."""
import http.server
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
import time
import uuid

import pytest

from test_codex_gitlab_queue import module
from test_codex_gitlab_workspace_native import Native, Provider, native_workspace, toml_tables

pytestmark = pytest.mark.skipif(os.environ.get('CODEX_MONITOR_NATIVE_PROBES') != '1',
    reason='requires explicitly selected installed Codex/Claude client probes')

READS = ('get_merge_request', 'mr_discussions')
WRITES = ('create_merge_request_thread', 'create_merge_request_discussion_note',
          'resolve_merge_request_thread')
FINAL = 'Conferi a discussão e expliquei a correção.\nEstado da revisão: concluída\nCommit revisado: '+'a'*40


@pytest.fixture
def ordinary_gitlab():
    from mcp.server import MCPServer
    from mcp.server.mcpserver import Context
    from mcp.types import CallToolResult, TextContent, ToolAnnotations
    import uvicorn
    api = MCPServer('gitlab')
    notes = [{'id': '1', 'created_at':'2026-10-22T00:00:00Z','updated_at':'2026-10-22T00:00:00Z','body': 'Existing concern', 'author': {'id': '5'},
              'resolvable': True, 'resolved': False, 'system': False}]
    threads = [{'id': 'existing', 'notes': notes}]
    calls = []

    def result(value):
        return CallToolResult(content=[TextContent(type='text', text=json.dumps(value))])

    @api.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def get_merge_request(project_id: str, merge_request_iid: str) -> CallToolResult:
        calls.append(('get_merge_request', project_id, merge_request_iid))
        return result({'project_id': int(project_id), 'iid': int(merge_request_iid),
                       'state': 'opened', 'sha': 'a'*40})

    @api.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def mr_discussions(project_id: str, merge_request_iid: str) -> CallToolResult:
        calls.append(('mr_discussions', project_id, merge_request_iid))
        return result({'items':threads,'pagination':{'x_page':1,'x_per_page':100,'x_next_page':None}})

    @api.tool()
    def create_merge_request_thread(project_id: str, merge_request_iid: str,
                                    body: str) -> CallToolResult:
        calls.append(('create_merge_request_thread', project_id, merge_request_iid))
        thread = {'id': 'new', 'notes': [{'id': '2', 'created_at':'2026-10-22T00:00:01Z','updated_at':'2026-10-22T00:00:01Z','body': body, 'author': {'id': '7'},
                   'system': False, 'resolvable': True, 'resolved': False}]}
        threads.append(thread)
        return result(thread)

    @api.tool()
    def create_merge_request_discussion_note(project_id: str, merge_request_iid: str,
                                             discussion_id: str, body: str) -> CallToolResult:
        calls.append(('create_merge_request_discussion_note', project_id, merge_request_iid))
        assert discussion_id == 'existing'
        note = {'id': '3', 'created_at':'2026-10-22T00:00:02Z','updated_at':'2026-10-22T00:00:02Z','body': body, 'author': {'id': '7'}, 'system': False,
                'resolvable': True, 'resolved': False}
        notes.append(note)
        return result(note)

    @api.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def discover_tools(category: str, ctx: Context) -> CallToolResult:
        assert category == 'merge_requests'
        calls.append(('discover_tools', category))
        return result({'activated': category})

    @api.tool()
    def resolve_merge_request_thread(project_id: str, merge_request_iid: str,
                                     discussion_id: str, resolved: bool) -> CallToolResult:
        calls.append(('resolve_merge_request_thread', project_id, merge_request_iid))
        assert discussion_id == 'existing' and resolved is True
        for note in notes:
            note['resolved'] = True
        return CallToolResult(content=[TextContent(type='text',text='Thread resolved successfully')])

    @api.tool()
    def merge_merge_request(project_id: str, merge_request_iid: str) -> CallToolResult:
        calls.append(('merge_merge_request', project_id, merge_request_iid))
        raise AssertionError('unrelated mutation reached the fixture')

    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    # MCP Streamable HTTP uses HTTP/SSE, never WebSocket transport.
    server = uvicorn.Server(uvicorn.Config(api.streamable_http_app(), log_level='error', ws='none'))
    worker = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    worker.start()
    deadline = time.monotonic()+15
    while not server.started and worker.is_alive() and time.monotonic() < deadline:
        time.sleep(.01)
    try:
        assert server.started, 'fixture HTTP MCP did not start'
        yield {'url': f'http://127.0.0.1:{port}/mcp', 'calls': calls, 'threads': threads}
    finally:
        server.should_exit = True
        worker.join(10)
        sock.close()
        assert not worker.is_alive(), 'fixture MCP did not stop'


def steps():
    target = {'project_id': '11', 'merge_request_iid': '82'}
    return [('get_merge_request', target), ('mr_discussions', target),
            ('create_merge_request_thread', {**target, 'body': 'A distinct fixture concern'}),
            ('create_merge_request_discussion_note', {**target, 'discussion_id': 'existing',
                                                     'body': 'The exact fixture fix resolves this concern.'}),
            ('mr_discussions', target),
            ('resolve_merge_request_thread', {**target, 'discussion_id': 'existing', 'resolved': True}),
            ('merge_merge_request', target)]


class CodexProvider(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        import gzip
        assert self.path == '/v1/responses'
        raw = self.rfile.read(int(self.headers['Content-Length']))
        if self.headers.get('Content-Encoding') == 'gzip':
            raw = gzip.decompress(raw)
        data = json.loads(raw)
        index = len(self.server.requests)
        self.server.requests.append(data)
        if index < len(self.server.steps):
            name, arguments = self.server.steps[index]
            code = ('const t=ALL_TOOLS.find(t=>t.name.includes("gitlab")&&t.name.endsWith("__'+name+'"));'
                    'if(!t){text("not exposed");}else{text(await tools[t.name]('+json.dumps(arguments)+'));}')
            item = {'type': 'custom_tool_call', 'id': 'call-'+str(index), 'call_id': 'call-'+str(index),
                    'namespace': 'functions', 'name': 'exec', 'input': code}
        else:
            item = {'type': 'message', 'id': 'msg-final', 'role': 'assistant', 'status': 'completed',
                    'phase': 'final_answer', 'content': [{'type': 'output_text', 'text': FINAL,
                                                       'annotations': []}]}
        response = {'id': 'resp-'+str(index), 'object': 'response', 'status': 'completed',
                    'model': data['model'], 'output': [item],
                    'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
        events = [{'type': 'response.created', 'response': {**response, 'status': 'in_progress', 'output': []}},
                  {'type': 'response.output_item.added', 'output_index': 0, 'item': item},
                  {'type': 'response.output_item.done', 'output_index': 0, 'item': item},
                  {'type': 'response.completed', 'response': response}]
        body = ''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.mark.parametrize('reviewer', ['codex', 'claude'])
@pytest.mark.parametrize('mode', ['review', 'intake'])
def test_installed_clients_direct_http_tools(native_workspace, ordinary_gitlab, reviewer, mode, monkeypatch):
    m, c, roots, main, script, expected = native_workspace
    c['_workspace_write'] = mode == 'review'
    c['_direct_gitlab'] = True
    fixture = ordinary_gitlab
    allowed = [*READS, *(WRITES if mode == 'review' else ())]
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), CodexProvider if reviewer == 'codex' else Provider)
    server.requests = []
    server.steps = steps() if reviewer == 'codex' else [('mcp__gitlab__'+n, a) for n, a in steps()]
    server.final_text = FINAL
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    data=json.loads((Path(__file__).parent/'fixtures/gitlab-message-v1.json').read_text())['input_context']
    data.update(stage=str(uuid.uuid4()),reviewer=reviewer,kind='code' if mode=='review' else 'intake',workspace=c['_workspace'])
    task=m['mq_render_input'](data)
    stage={'id':data['stage'],'reviewer':reviewer,'input':task,'input_context':data,
        'input_format':'message-v2','input_digest':m['monitor_digest'](data)}
    native = None
    ordinary = {'gitlab': {'url': fixture['url'], 'http_headers': {'Private-Token':'fixture-only',
        'X-Gitlab-Api-Url':c['gitlab_url']+'/api/v4'}}}
    (Path(c['codex_home'])/'config.toml').write_text(toml_tables({'mcp_servers':ordinary}))
    try:
        if reviewer == 'codex':
            config = {'model': 'gpt-6.1-sol', 'model_provider': 'fixture', 'analytics': {'enabled': False},
                      'mcp_servers':ordinary,'model_providers': {'fixture': {'name': 'Fixture',
                          'base_url': f'http://127.0.0.1:{server.server_port}/v1', 'wire_api': 'responses',
                          'requires_openai_auth': False, 'supports_websockets': False}}}
            (Path(c['codex_home'])/'config.toml').write_text(toml_tables(config))
            native = Native(os.environ.get('CODEX_MONITOR_NATIVE_CODEX') or shutil.which('codex'), c)
            selection = m['mq_native_selection'](c)
            created = native.rpc('thread/start', {'cwd': c['cwd'], 'approvalPolicy': 'never',
                'runtimeWorkspaceRoots': c['_workspace']['roots'], **selection})
            session = created['thread']['id']
            native.turn(session, m['MQ_PERMISSION_PROFILE'], task)
            history = native.rpc('thread/read', {'threadId': session, 'includeTurns': True})
            turn = history['thread']['turns'][-1]['id']
            items = native.rpc('thread/items/list', {'threadId': session, 'turnId': turn, 'limit': 100})
            stage.update(session=session,turn_id=turn)
            monkeypatch.setitem(m,'monitor_native',lambda config,method,params:native.rpc(method,params))
            (Path(c['codex_home'])/'direct-history.json').write_text(json.dumps(history))
            (Path(c['codex_home'])/'direct-items.json').write_text(json.dumps(items))
            assert [r['item']['text'] for r in items['data'] if r['item'].get('type') == 'agentMessage'
                    and r['item'].get('phase') == 'final_answer'] == [FINAL]
        else:
            home = Path(c['claude_home'])
            (home/'.claude.json').write_text(json.dumps({'projects': {c['cwd']: {'hasTrustDialogAccepted': True}}}))
            private = Path(c['queue_file']).parent/'mcp.json'
            private.write_text(json.dumps({'mcpServers': {'gitlab': {'type': 'http', 'url': fixture['url']}}}))
            private.chmod(0o600)
            arguments = m['mq_claude_arguments']({**c,'_gitlab_mcp_file':str(private)}, task, 'direct fixture')
            arguments[arguments.index('--mcp-config')+1] = str(private)
            session = str(uuid.uuid4())
            environment = {k: v for k, v in os.environ.items()
                           if not k.startswith(('ANTHROPIC_', 'CLAUDE_', 'CODEX_', 'OPENAI_'))}
            environment.update(CLAUDE_CONFIG_DIR=str(home), ANTHROPIC_API_KEY='fixture-only',
                ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',
                CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1', DISABLE_AUTOUPDATER='1',
                HTTP_PROXY='http://127.0.0.1:9', HTTPS_PROXY='http://127.0.0.1:9', NO_PROXY='127.0.0.1,localhost')
            result = subprocess.run([shutil.which('claude'), '--session-id', session, *arguments],
                cwd=c['cwd'], env=environment, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
            (home/'direct-stdout').write_text(result.stdout)
            (home/'direct-stderr').write_text(result.stderr)
            assert result.returncode == 0, result.stderr
            events = [json.loads(s) for s in result.stdout.splitlines()]
            assert events[-1]['type'] == 'result' and events[-1]['result'] == FINAL
            stage.update(session=session)
            records = m['mq_claude_records'](c, session)
            (home/'direct-history.json').write_text(json.dumps(records))
        calls=m['mq_native_gitlab_calls'](c,None,stage)
        successful=[call for call in calls if not call.get('error')]
        assert {call['tool'] for call in successful}&set(WRITES)==(set(WRITES) if mode=='review' else set())
        assert all(m['mq_tool_payload'](call['result']) is not None for call in successful
                   if call['tool']!='resolve_merge_request_thread')
        resolutions=[call for call in successful if call['tool']=='resolve_merge_request_thread']
        assert all(m['mq_tool_payload'](call['result']) is None for call in resolutions)
        q=m['MonitorQueue']({'reviewers':[reviewer],**{k:c[k] for k in ('queue_file','codex_home','gitlab_url')}})
        try:
            job=q.enqueue(11,82,source_key='native-observer',kind='code',head='a'*40,
                source={'origin':'automatic'},context={'actor_id':7},reviewers=[reviewer])
            job=q.reserve({11})
            with q.atomic():job['stages']=[stage|{'state':'running','protocol':'direct'}];q.save(job)
            m['mq_observe_outputs'](c,q,job,job['stages'][0])
            own=q.mr(11,82).get('own_outputs',{})
            assert len(own)==(2 if mode=='review' else 0)
            assert all(value is None for value in own.values()) # text-only resolution has no revision receipt
        finally:q.close()
        forged={**stage,'input':task+' forged'}
        with pytest.raises(RuntimeError,match='immutable reviewer input'):
            m['mq_native_gitlab_calls'](c,None,forged)
        names = [call[0] for call in fixture['calls']]
        if mode == 'review':
            assert names == [name for name, _ in steps()[:-1]]
            assert fixture['threads'][0]['notes'][-1]['body'] == 'The exact fixture fix resolves this concern.'
            assert [n['resolved'] for n in fixture['threads'][0]['notes']] == [True, True]
            assert fixture['threads'][1]['notes'][0]['id'] == '2'
        else:
            assert names == ['get_merge_request', 'mr_discussions', 'mr_discussions']
            assert len(fixture['threads']) == 1 and len(fixture['threads'][0]['notes']) == 1
            assert fixture['threads'][0]['notes'][0]['resolved'] is False
        assert len(server.requests) == len(steps())+1
    finally:
        (Path(c[reviewer+'_home'])/'direct-provider.json').write_text(json.dumps(server.requests))
        if native:
            native.close()
        server.shutdown()
        server.server_close()
        worker.join(5)
