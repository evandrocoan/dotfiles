"""Installed-client MCP transport probes with disposable local model providers."""
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import uuid
import ssl
import selectors
import tempfile

import pytest

from test_codex_gitlab_queue import module
from test_codex_gitlab_workspace_native import Native, Provider, native_workspace, toml_tables

pytestmark = pytest.mark.skipif(os.environ.get('CODEX_MONITOR_NATIVE_PROBES') != '1',
    reason='requires explicitly selected installed Codex/Claude client probes')


@pytest.fixture
def probe_server(tmp_path):
    source = tmp_path/'probe.py'
    capture = tmp_path/'capture.json'
    source.write_text('''import json,os,sys,time
from pathlib import Path
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
server=MCPServer("monitor_probe")
@server.tool()
def probe(message:str,ctx:Context)->dict:
    context=ctx.request_context
    data={"message":message,"request_id":context.request_id,
          "meta":dict(context.meta) if context.meta else None,
          "params":dict(context.params or {}),
          "environment":{k:v for k,v in os.environ.items() if k in
              ("CODEX_THREAD_ID","CODEX_SESSION_ID","CLAUDE_SESSION_ID")}}
    Path(sys.argv[1]).write_text(json.dumps(data))
    deadline=time.monotonic()+30
    while not Path(sys.argv[1]+".release").exists():
        if time.monotonic()>deadline:raise RuntimeError("fixture release missing")
        time.sleep(.01)
    return {"received":message}
server.run()
''')
    return {'command':sys.executable,'args':[str(source),str(capture)]},capture


def captured_call(capture):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if capture.exists():
            try:return json.loads(capture.read_text())
            except json.JSONDecodeError:pass
        time.sleep(.01)
    raise AssertionError('native client did not invoke the MCP fixture')


class ToolResponses(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        import gzip
        assert self.path=='/v1/responses',self.path
        raw=self.rfile.read(int(self.headers['Content-Length']))
        if self.headers.get('Content-Encoding')=='gzip':raw=gzip.decompress(raw)
        data=json.loads(raw);self.server.requests.append(data)
        steps=getattr(self.server,'steps',None)
        if steps is not None:
            outputs=[i for i in data['input'] if i.get('type')=='custom_tool_call_output']
            retry=outputs and '"retry": true' in json.dumps(outputs[-1]).replace('\\"','"')
            if not hasattr(self.server,'cursor'):self.server.cursor=0
            elif not retry:self.server.cursor+=1
            if self.server.cursor==1 and hasattr(self.server,'before_publish'):self.server.before_publish()
            assert len(self.server.requests)<=10,'fixture tool never became available'
            if self.server.cursor<len(steps):
                name,args=steps[self.server.cursor]
                item={'type':'custom_tool_call','id':'call-'+str(len(self.server.requests)),
                    'call_id':'call-'+str(len(self.server.requests)),'namespace':'functions','name':'exec',
                    'input':'const t=ALL_TOOLS.find(t=>t.name.includes("gitlab_review")&&t.name.endsWith("__'+name+'")); '
                        'if(!t)throw new Error(JSON.stringify(ALL_TOOLS)); text(await tools[t.name]('+json.dumps(args)+'));'}
            else:
                item={'id':'msg-final','type':'message','role':'assistant','status':'completed',
                    'phase':'final_answer','content':[{'type':'output_text','text':'Revisão concluída no cenário local.','annotations':[]}]}
        elif len(self.server.requests)==1:
            item={'type':'custom_tool_call','id':'probe-call','call_id':'probe-call',
                'namespace':'functions','name':'exec',
                'input':getattr(self.server,'probe_code','const t=ALL_TOOLS.find(t=>t.name.includes("monitor_probe")); '
                    'if(!t)throw new Error(JSON.stringify(ALL_TOOLS)); '
                    'text(await tools[t.name]({message:"fixture"}));')}
        else:
            item={'id':'msg-final','type':'message','role':'assistant','status':'completed',
                'phase':'final_answer','content':[{'type':'output_text','text':'fixture complete','annotations':[]}]}
        response={'id':'resp-'+str(len(self.server.requests)),'object':'response','status':'completed',
            'model':data['model'],'output':[item],'usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2}}
        events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}},
            {'type':'response.output_item.added','output_index':0,'item':item},
            {'type':'response.output_item.done','output_index':0,'item':item},
            {'type':'response.completed','response':response}]
        body=''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
        self.send_response(200);self.send_header('Content-Type','text/event-stream')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        if item['type']=='message' and hasattr(self.server,'finished'):self.server.finished.set()


def test_native_codex_scoped_mcp_call(native_workspace,probe_server):
    m,c,roots,main,script,expected=native_workspace
    tool,capture=probe_server
    binary=os.environ.get('CODEX_MONITOR_NATIVE_CODEX') or shutil.which('codex');assert binary
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),ToolResponses)
    server.requests=[];server.error=None
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    config={'model':'gpt-6.1-sol','model_provider':'fixture','analytics':{'enabled':False},
        'mcp_servers':{'gitlab':{'command':'fixture-mcp-must-never-run','enabled':False}},
        'model_providers':{'fixture':{'name':'Disposable fixture',
            'base_url':f'http://127.0.0.1:{server.server_port}/v1','wire_api':'responses',
            'requires_openai_auth':False,'supports_websockets':False}}}
    (Path(c['codex_home'])/'config.toml').write_text(toml_tables(config))
    native=Native(binary,c)
    try:
        selection=m['mq_native_selection'](c)
        selection['config']['mcp_servers.monitor_probe']={**tool,'enabled':True,
            'tools':{'probe':{'approval_mode':'approve'}}}
        created=native.rpc('thread/start',{'cwd':c['cwd'],'ephemeral':False,
            'runtimeWorkspaceRoots':c['_workspace']['roots'],'approvalPolicy':'never',**selection})
        identifier=created['thread']['id']
        started=native.rpc('turn/start',{'threadId':identifier,
            'clientUserMessageId':'fixture-native-input',
            'input':[{'type':'text','text':'Disposable local fixture'}],
            'approvalPolicy':'never','permissions':m['MQ_PERMISSION_PROFILE']})
        captured=captured_call(capture)
        meta=captured['meta'];turn=started['turn']['id']
        assert meta['threadId']==identifier
        assert meta['x-codex-turn-metadata']['turn_id']==turn
        page=native.rpc('thread/items/list',{'threadId':identifier,'turnId':turn,'limit':100})
        items=[r['item'] for r in page['data']]
        live=native.rpc('thread/read',{'threadId':identifier,'includeTurns':True})
        assert [t['status'] for t in live['thread']['turns'] if t['id']==turn]==['inProgress']
        inputs=[i for i in items if i.get('type')=='userMessage']
        assert len(inputs)==1 and inputs[0]['clientId']=='fixture-native-input'
        assert inputs[0]['content'][0]['text']=='Disposable local fixture'
        # The native client supplies call metadata over its private stdio connection.
        # Codex persists tool items only on completion; original input is already readable.
        calls=[e['params']['item'] for e in native.pending if e.get('method')=='item/started'
            and e['params']['item'].get('id')==meta['callId']]
        assert len(calls)==1 and calls[0]['arguments']=={'message':'fixture'}
        Path(str(capture)+'.release').touch()
        while not any(e.get('method')=='turn/completed' for e in native.pending):
            event=native.events.get(timeout=35)
            assert 'id' not in event and 'closed' not in event,event
            native.pending.append(event)
        assert server.error is None,server.error
        assert capture.exists(),native.pending
        captured=json.loads(capture.read_text())
        assert captured['message']=='fixture'
        # Keep the actual transport evidence in pytest's disposable directory for diagnosis.
        (capture.parent/'codex-events.json').write_text(json.dumps(native.pending))
        assert len(server.requests)==2
        outputs=[i for i in server.requests[-1]['input'] if i.get('type')=='custom_tool_call_output']
        assert len(outputs)==1 and outputs[0]['call_id']=='probe-call'
        assert 'fixture' in str(outputs[0]['output'])
    finally:
        Path(str(capture)+'.release').touch()
        (capture.parent/'codex-events.json').write_text(json.dumps(native.pending))
        (capture.parent/'provider-requests.json').write_text(json.dumps(server.requests))
        native.close();server.shutdown();server.server_close();worker.join(5)


def test_native_codex_host_only_tool(native_workspace,probe_server):
    m,c,roots,main,script,expected=native_workspace
    tool,capture=probe_server
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),ToolResponses)
    server.requests=[];server.probe_code='const t=ALL_TOOLS.find(t=>t.name.includes("monitor_probe")); text(await tools[t.name]({message:"agent"}));'
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    config={'model':'gpt-6.1-sol','model_provider':'fixture','analytics':{'enabled':False},
        'model_providers':{'fixture':{'name':'Fixture','base_url':f'http://127.0.0.1:{server.server_port}/v1',
            'wire_api':'responses','requires_openai_auth':False,'supports_websockets':False}}}
    (Path(c['codex_home'])/'config.toml').write_text(toml_tables(config))
    native=Native(shutil.which('codex'),c)
    try:
        created=native.rpc('thread/start',{'cwd':c['cwd'],'approvalPolicy':'never',
            'config':{'mcp_servers.monitor_probe':{**tool,'enabled':True,'tools':{'probe':{'approval_mode':'prompt'}}}}})
        identifier=created['thread']['id']
        Path(str(capture)+'.release').touch()
        result=native.rpc('mcpServer/tool/call',{'threadId':identifier,'server':'monitor_probe',
            'tool':'probe','arguments':{'message':'fixture'}})
        assert result.get('isError') is not True and capture.exists(),result
        native.turn(identifier,':read-only')
        outputs=[i for i in server.requests[-1]['input'] if i.get('type')=='custom_tool_call_output']
        assert len(outputs)==1 and 'requires approval, but approval policy is never' in str(outputs[0]['output']),outputs
        assert json.loads(capture.read_text())['message']=='fixture'
    finally:
        native.close();server.shutdown();server.server_close();worker.join(5)


def test_native_claude_scoped_mcp_call(native_workspace,probe_server):
    m,c,roots,main,script,expected=native_workspace
    tool,capture=probe_server
    binary=shutil.which('claude');assert binary
    home=Path(c['claude_home'])
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
    server.requests=[];server.steps=[('mcp__monitor_probe__probe',{'message':'fixture'})]
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    args=m['mq_claude_arguments'](c,'Run the disposable MCP fixture.','fixture')
    args[args.index('--mcp-config')+1]=json.dumps({'mcpServers':{'monitor_probe':tool}})
    args.insert(args.index('--'),'mcp__monitor_probe__probe')
    session=str(uuid.uuid4());args[0:0]=['--session-id',session]
    environment={k:v for k,v in os.environ.items() if not k.startswith(('ANTHROPIC_','CLAUDE_','CODEX_'))}
    environment.update(CLAUDE_CONFIG_DIR=str(home),ANTHROPIC_API_KEY='fixture-only',
        ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_AUTOUPDATER='1',
        HTTP_PROXY='http://127.0.0.1:9',HTTPS_PROXY='http://127.0.0.1:9',NO_PROXY='127.0.0.1,localhost')
    try:
        child=subprocess.Popen([binary,*args],cwd=c['cwd'],env=environment,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        captured=captured_call(capture)
        deadline=time.monotonic()+10
        while True:
            records=m['mq_claude_records'](c,session)
            calls=[(r,b) for r in records for b in r.get('message',{}).get('content',[]) if isinstance(b,dict)
                and b.get('type')=='tool_use' and b.get('id')==captured['meta']['claudecode/toolUseId']]
            if calls or time.monotonic()>deadline:break
            time.sleep(.1)
        assert len(calls)==1,records
        assert calls[0][1]['input']=={'message':'fixture'}
        assert calls[0][0]['sessionId']==session and calls[0][0]['cwd']==c['cwd']
        Path(str(capture)+'.release').touch()
        stdout,stderr=child.communicate(timeout=45)
        (home/'probe.stdout').write_text(stdout);(home/'probe.stderr').write_text(stderr)
        assert child.returncode==0,stderr
        assert captured['message']=='fixture'
        assert len(server.requests)==2
        results=[b for message in server.requests[-1]['messages'] if message['role']=='user'
            and isinstance(message.get('content'),list) for b in message['content'] if b.get('type')=='tool_result']
        assert len(results)==1 and results[0]['tool_use_id']=='tool-0'
        assert 'fixture' in str(results[0]['content']) and not results[0].get('is_error')
    finally:
        Path(str(capture)+'.release').touch()
        if 'child' in locals() and child.poll() is None:child.communicate(timeout=45)
        server.shutdown();server.server_close();worker.join(5)


class GitLabFixture(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def answer(self,value):
        raw=json.dumps(value).encode();self.send_response(200)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
        self.send_header('X-Next-Page','');self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        assert self.headers.get('PRIVATE-TOKEN')=='fixture-only'
        path=self.path.split('?',1)[0].removeprefix('/api/v4');s=self.server
        values={'/projects/11':{'id':11,'path_with_namespace':'team/repo','web_url':s.origin+'/team/repo'},
            '/user':{'id':7},'/users/7':{'id':7,'bot':True},
            '/projects/11/merge_requests/82':{'iid':82,'project_id':11,'state':'opened','title':'Disposable MR',
                'web_url':s.origin+'/team/repo/-/merge_requests/82','sha':getattr(s,'head','a'*40),
                'diff_refs':{'head_sha':getattr(s,'head','a'*40),'base_sha':'b'*40,'start_sha':'c'*40}},
            '/projects/11/merge_requests/82/discussions':s.discussions,
            '/projects/11/merge_requests/82/versions':[{'id':1,'head_commit_sha':'a'*40}],
            '/projects/11/merge_requests/82/versions/1':{'head_commit_sha':'a'*40,'base_commit_sha':'b'*40,
                'start_commit_sha':'c'*40,'diffs':[{'old_path':'x.py','new_path':'x.py','diff':'@@ -1 +1 @@\n-old\n+new'}]}}
        assert path in values,path;self.answer(values[path])
    def do_POST(self):
        assert self.path=='/api/v4/projects/11/merge_requests/82/discussions'
        assert self.headers.get('PRIVATE-TOKEN')=='fixture-only'
        value=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.posts.append(value)
        note={'id':100,'body':value['body'],'position':value['position'],'system':False,
            'author':{'id':7},'created_at':'2026-10-21T00:00:00Z','resolvable':True,'resolved':False}
        self.server.discussions.append({'id':'finding','notes':[note]});self.answer(self.server.discussions[-1])


class ReviewClaudeProvider(Provider):
    def do_POST(self):
        if len(self.server.requests)==1 and hasattr(self.server,'before_publish'):self.server.before_publish()
        super().do_POST()
        if len(self.server.requests)>len(self.server.steps):self.server.finished.set()


@pytest.mark.parametrize('reviewer,context_change,initial_disconnect',[
    ('codex',None,False),('claude',None,False),('codex','head',False),('claude','head',False),
    ('codex',None,True),('codex','source',False)])
def test_native_full_review(module,monkeypatch,reviewer,context_change,initial_disconnect,tmp_path):
    """Installed client -> real scoped SDK -> authenticated source -> local HTTPS -> journal.

    Claude uses an actual finite user unit; Codex uses the actual launcher/lease with a disposable
    GUI protocol peer. All model responses are local fixtures, with production credentials absent.
    """
    m=module['mq_step'].__globals__
    original_native=m['monitor_native']
    disconnected=[]
    def observed_native(*args,**kwargs):
        if initial_disconnect and not disconnected and args[1]=='thread/start':
            followup=kwargs['followup']
            async def broken_connection(request,response):
                async def request_until_disconnect(method,params):
                    if method=='thread/name/set':
                        disconnected.append(response['thread']['id'])
                        raise OSError('fixture disconnected before first input')
                    return await request(method,params)
                return await followup(request_until_disconnect,response)
            kwargs['followup']=broken_connection
        try:return original_native(*args,**kwargs)
        except m['MonitorNativeRejected'] as error:
            (tmp_path/'native-error.json').write_text(json.dumps(error.native_error))
            raise
    monkeypatch.setitem(m,'monitor_native',observed_native)
    binary=shutil.which(reviewer);assert binary
    with tempfile.TemporaryDirectory(prefix='csm-tools-') as directory:
        root=Path(directory);workspace=root/'workspace';workspace.mkdir()
        for name in ('codex','claude','runtime'):(root/name).mkdir(mode=0o700)
        for key in tuple(os.environ):
            if key.startswith(('ANTHROPIC_','CLAUDE_','CODEX_','OPENAI_')):monkeypatch.delenv(key)
        cert=root/'cert.pem';key=root/'key.pem'
        certificate=subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes',
            '-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost',
            '-addext','subjectAltName=IP:127.0.0.1,DNS:localhost'],capture_output=True,text=True)
        assert certificate.returncode==0,certificate.stderr
        gl=http.server.ThreadingHTTPServer(('127.0.0.1',0),GitLabFixture)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(cert,key)
        gl.socket=tls.wrap_socket(gl.socket,server_side=True)
        gl.origin=f'https://127.0.0.1:{gl.server_port}';gl.posts=[];gl.discussions=[]
        # ToolResponses accepts explicit task-sized steps for this fixture.
        provider=http.server.ThreadingHTTPServer(('127.0.0.1',0),ToolResponses if reviewer=='codex' else ReviewClaudeProvider)
        provider.finished=threading.Event()
        provider.requests=[];provider.steps=[('read_mr',{}),('publish_finding',
            {'body':'[P2] Subtraia o desconto.','path':'x.py','line':1}),('finish_review',{})]
        if context_change=='head':provider.before_publish=lambda:setattr(gl,'head','d'*40)
        if context_change=='source':
            # Native steering is consumed between model steps. Keep that transition read-only,
            # and assert the changed input is delivered before the attempted publication.
            provider.steps.insert(1,('read_mr',{}))
            def steer():
                if getattr(provider,'steered',False):return
                current=m['MonitorQueue'](config,readonly=True)
                try:stage=current.jobs('running')[0]['stages'][-1]
                finally:current.close()
                m['monitor_native'](config,'turn/steer',{'threadId':stage['session'],'expectedTurnId':stage['turn_id'],
                    'input':[{'type':'text','text':'Explain the review only; do not publish.'}]})
                provider.steered=True
            provider.before_publish=steer
        if reviewer=='claude':provider.steps=[('mcp__gitlab_review__'+n,a) for n,a in provider.steps]
        workers=[]
        for server in (gl,provider):
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();workers.append(worker)
        settings={'SSL_CERT_FILE':str(cert),'HTTP_PROXY':'http://127.0.0.1:9','HTTPS_PROXY':'http://127.0.0.1:9',
            'NO_PROXY':'127.0.0.1,localhost','CLAUDE_CONFIG_DIR':str(root/'claude'),
            'ANTHROPIC_API_KEY':'fixture-only','ANTHROPIC_BASE_URL':f'http://127.0.0.1:{provider.server_port}',
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','DISABLE_AUTOUPDATER':'1'}
        for name,value in settings.items():monkeypatch.setenv(name,value)
        monkeypatch.setenv('XDG_RUNTIME_DIR',str(root/'runtime'))
        monkeypatch.setenv('DBUS_SESSION_BUS_ADDRESS',f'unix:path=/run/user/{os.getuid()}/bus')
        raw=m['monitor_default_config'](gl.origin+'/team/repo',11,'gitlab')
        raw.update(cwd=str(workspace),codex_home=str(root/'codex'),claude_home=str(root/'claude'),
            queue_file=str(root/'queue/queue.sqlite3'),state_file=str(root/'old/state.sqlite3'),
            model='gpt-6.1-sol',effort='low',claude_bin=shutil.which('claude'),reviewers=[reviewer],review_timeout_seconds=60)
        raw['socket']=str(root/'codex/app-server-control/app-server-control.sock')
        path=root/'connection.json';path.write_text(json.dumps(raw));path.chmod(0o600)
        native_config={'model':'gpt-6.1-sol','model_provider':'fixture','analytics':{'enabled':False},
            'mcp_servers':{'gitlab':{'command':'fixture-never-runs','enabled':False,
                'env':{'GITLAB_API_URL':gl.origin+'/api/v4','GITLAB_PERSONAL_ACCESS_TOKEN':'fixture-only'}}},
            'model_providers':{'fixture':{'name':'Local model fixture',
                'base_url':f'http://127.0.0.1:{provider.server_port}/v1','wire_api':'responses',
                'requires_openai_auth':False,'supports_websockets':False}}}
        (root/'codex/config.toml').write_text(toml_tables(native_config))
        (root/'claude/.claude.json').write_text(json.dumps({'projects':{str(workspace):{'hasTrustDialogAccepted':True}}}))
        config=m['mq_config'](path);gui=None;queue=None;errors=(root/'native.stderr').open('w+')
        try:
            if reviewer=='codex':
                app=root/'gui';shutil.copyfile(Path(sys.executable).resolve(),app);app.chmod(0o700)
                (root/'environment.json').write_text(json.dumps(settings))
                source=root/'gui.py';source.write_text('''import json,os,subprocess,sys,threading
from pathlib import Path
os.environ.update(json.loads(Path(sys.argv[1]).read_text()))
os.environ['CODEX_INTERNAL_ORIGINATOR_OVERRIDE']='Codex Desktop'
child=subprocess.Popen([os.environ['CODEX_CLI_PATH'],'-c','features.code_mode_host=true',
 '-c','plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled=false',
 '-c','plugins.code-review@openai-bundled.mcp_servers.code-review.enabled=false',
 'app-server','--analytics-default-enabled'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
child.stdin.write(json.dumps({'id':1,'method':'initialize','params':{'clientInfo':{'name':'Codex Desktop','version':'fixture'}}})+'\\n');child.stdin.flush()
line=child.stdout.readline();assert json.loads(line).get('result'),line
child.stdin.write(json.dumps({'method':'initialized','params':{}})+'\\n');child.stdin.flush()
threading.Thread(target=lambda:list(child.stdout),daemon=True).start()
print('ready',flush=True)
sys.stdin.readline();child.stdin.close();child.wait(timeout=15)
''')
                gui=subprocess.Popen([sys.executable,m['__file__'],'monitor-gitlab','--config',str(path),
                    'launch-app','--app',str(app),'--codex',binary,'--',str(source),str(root/'environment.json')],
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True)
                with selectors.DefaultSelector() as selector:
                    selector.register(gui.stdout,selectors.EVENT_READ)
                    assert selector.select(25),'disposable native GUI did not initialize'
                line=gui.stdout.readline();errors.flush();errors.seek(0)
                assert line.strip()=='ready',errors.read()
                config=m['mq_config'](path)
            queue=m['MonitorQueue'](config)
            context=m['mq_context'](config,82,with_diff=False)
            job=queue.enqueue(11,82,source_key='native-fixture',kind='code',head='a'*40,
                source={'origin':'automatic','head':'a'*40},context=context)
            assert m['mq_consume'](config,queue)
            if initial_disconnect:
                assert disconnected and not provider.requests
                failed=queue.job(job['id'])['stages'][0]
                assert failed['state']=='failed' and failed['delivery']=='prepared'
                m['mq_consume'](config,queue)
                waiting=queue.job(job['id']);assert waiting['wait_reason']=='reviewer_retry'
                stamp=m['mq_stamp']
                monkeypatch.setitem(m,'mq_stamp',lambda:waiting['retry_at']+1)
                try:assert m['mq_consume'](config,queue)
                finally:monkeypatch.setitem(m,'mq_stamp',stamp)
                record=queue.mr(11,82)
                assert record['chats']['codex']!=disconnected[0] and disconnected[0] in record['codex_contexts']
            # Advance the periodic collector only after the fixture model emitted its final.
            # This is an explicit provider barrier, not a timing assumption about native progress.
            if queue.job(job['id'])['stages'][-1]['state']=='running':provider.finished.wait(40)
            deadline=time.monotonic()+50
            while time.monotonic()<deadline and queue.job(job['id'])['state']=='running':
                m['mq_consume'](config,queue)
                if queue.job(job['id'])['state']=='running':time.sleep(.1)
            saved=queue.job(job['id'])
            if context_change:
                assert saved['state']=='pending' and saved['wait_reason']=='reviewer_retry',saved
                assert not gl.posts and not queue.effects()
                assert queue.mr(11,82)['reviewed_head'] is None
                reason='head changed' if context_change=='head' else 'native input changed or became mixed'
                assert reason in json.dumps(provider.requests[-1]),provider.requests[-1]
                if context_change=='source':
                    assert 'Explain the review only; do not publish.' in json.dumps(provider.requests[2]['input'])
                return
            assert saved['state']=='completed',(saved,queue.meta('consumer_error'),provider.requests[-1:])
            assert 'The operator already selected model/effort for this stage' in json.dumps(provider.requests)
            assert 'do not offer upgrades/downgrades' in json.dumps(provider.requests)
            assert len(gl.posts)==1 and queue.effects()[0]['state']=='confirmed'
            assert saved['stages'][-1]['state']=='succeeded' and saved['stages'][-1].get('finish_intent')
            assert queue.mr(11,82)['reviewed_head']=='a'*40
            assert 'csm-review' not in saved['stages'][-1]['summary']
        finally:
            errors.flush();errors.seek(0);(tmp_path/'native.stderr').write_text(errors.read())
            (tmp_path/'requests.json').write_text(json.dumps(provider.requests,indent=2))
            if queue is not None:(tmp_path/'jobs.json').write_text(json.dumps(queue.jobs(),indent=2))
            if (root/'queue/executions').exists():
                shutil.copytree(root/'queue/executions',tmp_path/'executions',dirs_exist_ok=True)
            if queue is not None:
                for job in queue.jobs('running'):
                    stage=job['stages'][-1]
                    if stage['reviewer']=='claude' and stage.get('unit'):
                        m['mq_service_command'](config,['systemctl','--user','stop',stage['unit']])
                queue.close()
            if gui is not None:
                if gui.poll() is None:gui.stdin.write('stop\n');gui.stdin.flush()
                gui.wait(timeout=20);gui.stdin.close();gui.stdout.close()
            errors.close()
            for server in (gl,provider):server.shutdown();server.server_close()
            for worker in workers:worker.join(5)
