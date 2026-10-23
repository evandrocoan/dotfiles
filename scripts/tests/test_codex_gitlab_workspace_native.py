"""Opt-in installed-client probes. All providers and Git repositories are disposable."""
import gzip
import http.server
import json
import os
from pathlib import Path
import queue
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid

import pytest

from test_codex_gitlab_queue import module, flow, domain, rendered

pytestmark = pytest.mark.skipif(os.environ.get('CODEX_MONITOR_NATIVE_PROBES') != '1',
    reason='requires explicitly selected installed Codex/Claude client probes')


def toml_tables(data, prefix=()):
    text='['+'.'.join(json.dumps(k) for k in prefix)+']\n' if prefix else ''
    for key,value in data.items():
        if not isinstance(value,dict):text+=json.dumps(key)+'='+json.dumps(value)+'\n'
    for key,value in data.items():
        if isinstance(value,dict):text+=toml_tables(value,(*prefix,key))
    return text


@pytest.fixture
def native_workspace(module,tmp_path):
    m=module['mq_step'].__globals__
    roots=[tmp_path/('root '+str(i)) for i in range(5)]
    main=tmp_path/'main checkout'
    subprocess.run(['git','init','-q',str(main)],check=True)
    subprocess.run(['git','-C',str(main),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
        'commit','-q','--allow-empty','-m','Fixture'],check=True)
    subprocess.run(['git','-C',str(main),'worktree','add','--detach',str(roots[0]),'HEAD'],
        check=True,capture_output=True,text=True)
    for root in roots[1:]:
        subprocess.run(['git','init','-q',str(root)],check=True)
    for directory in ('codex','claude','queue','old'):
        (tmp_path/directory).mkdir(mode=0o700)
    listener=socket.socket(socket.AF_UNIX)
    endpoint=tmp_path/'codex'/'control.sock';listener.bind(str(endpoint));listener.listen()
    (roots[0]/'escape').symlink_to(main,target_is_directory=True)
    config=m['monitor_default_config']('https://gitlab.example.test/team/repo',11,'gitlab')
    config.update(cwd=str(roots[0]),codex_home=str(tmp_path/'codex'),claude_home=str(tmp_path/'claude'),
        state_file=str(tmp_path/'old'/'state.sqlite3'),queue_file=str(tmp_path/'queue'/'queue.sqlite3'),
        socket=str(endpoint),_config_path=str(tmp_path/'connection.json'))
    (tmp_path/'connection.json').write_text('{}')
    (tmp_path/'queue'/'input.json').write_text('{"fixture":"immutable"}')
    (tmp_path/'codex'/'config.toml').write_text('')
    config['_workspace']={'project_id':None,'project_name':None,'cwd':str(roots[0]),
        'roots':[str(r) for r in roots],'git_metadata':m['mq_git_metadata']([str(r) for r in roots])}
    config['_workspace_write']=True
    code='''import json,pathlib,socket,subprocess
out={}
for root in ROOTS:
    pathlib.Path(root,"written").write_text("fixture")
    subprocess.run(["git","symbolic-ref","HEAD","refs/heads/native-probe"],cwd=root,check=True,capture_output=True)
    out[root]="ok"
for key,target in DENIALS.items():
    try:pathlib.Path(target).write_text("forbidden");out[key]="WRITTEN"
    except OSError as e:out[key]="denied"
peer=None
try:
    peer=socket.socket(socket.AF_UNIX)
    peer.connect(ENDPOINT);out["socket"]="CONNECTED"
except OSError:out["socket"]="denied"
finally:
    if peer is not None:peer.close()
print(json.dumps(out))
'''.replace('ROOTS',repr(config['_workspace']['roots'])).replace('DENIALS',repr({
        'main-source':str(main/'bad'),'symlink':str(roots[0]/'escape'/'bad-link'),
        'queue':str(tmp_path/'queue'/'bad'),'native':str(tmp_path/'codex'/'bad')})).replace('ENDPOINT',repr(str(endpoint)))
    script=roots[0]/'probe.py';script.write_text(code)
    expected={**{str(r):'ok' for r in roots},**{k:'denied' for k in ('main-source','symlink','queue','native','socket')}}
    yield m,config,roots,main,script,expected
    listener.close()


class Native:
    def __init__(self, binary, config, *, environment=None):
        self.events=queue.Queue();self.counter=0;self.pending=[]
        self.errors=(Path(config['codex_home'])/'server.stderr').open('a')
        env={k:v for k,v in os.environ.items() if not k.startswith(('OPENAI_','CODEX_'))}
        env.update(CODEX_HOME=config['codex_home'],HTTP_PROXY='http://127.0.0.1:9',
            HTTPS_PROXY='http://127.0.0.1:9',NO_PROXY='127.0.0.1,localhost')
        env.update(environment or {})
        self.child=subprocess.Popen([binary,'app-server','--stdio'],cwd=config['cwd'],env=env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.errors,text=True)
        def read():
            for line in self.child.stdout:self.events.put(json.loads(line))
            self.events.put({'closed':True})
        threading.Thread(target=read,daemon=True).start()
        self.rpc('initialize',{'clientInfo':{'name':'workspace-native-fixture','version':'1'},
            'capabilities':{'experimentalApi':True}})
        self.send({'method':'initialized','params':{}})
    def send(self,data):
        self.child.stdin.write(json.dumps(data)+'\n');self.child.stdin.flush()
    def rpc(self,method,params):
        self.counter+=1;identifier=self.counter
        self.send({'id':identifier,'method':method,'params':params})
        while True:
            event=self.events.get(timeout=35)
            assert 'closed' not in event,event
            if event.get('id')==identifier:
                assert 'error' not in event,(method,event)
                return event['result']
            assert 'id' not in event,('unexpected approval request',event)
            self.pending.append(event)
    def close(self):
        self.child.stdin.close()
        try:self.child.wait(timeout=10)
        except subprocess.TimeoutExpired:self.child.terminate();self.child.wait(timeout=10)
        self.child.stdout.close();self.errors.close()

    def turn(self,thread,permissions,text="Disposable local fixture"):
        params={'threadId':thread,'input':[{'type':'text','text':text}],'approvalPolicy':'never'}
        if permissions is not None:params['permissions']=permissions
        result=self.rpc('turn/start',params)
        identifier=result['turn']['id']
        while True:
            for event in self.pending:
                if event.get('method')=='turn/completed' and event['params']['turn']['id']==identifier:
                    assert event['params']['turn']['status']=='completed',event
                    return
            event=self.events.get(timeout=35)
            assert 'id' not in event and 'closed' not in event,('unexpected native request',event)
            self.pending.append(event)


@pytest.mark.parametrize('legacy',[False,True])
def test_native_codex_intake_command_denials(native_workspace,legacy):
    m,c,roots,main,script,expected=native_workspace
    c['_workspace_write']=False
    targets={**{str(root):str(root/'forbidden') for root in roots},
        'git-metadata':str(main/'.git'/'forbidden'),
        'main-source':str(main/'forbidden'),
        'queue':str(Path(c['queue_file']).parent/'forbidden'),
        'native':str(Path(c['codex_home'])/'forbidden')}
    script.write_text('''import json,pathlib,socket
out={'source_read':pathlib.Path(__file__).read_text().startswith('import json,pathlib,socket')}
for label,target in TARGETS.items():
    try:pathlib.Path(target).write_text('forbidden');out[label]='WRITTEN'
    except OSError:out[label]='denied'
peer=None
try:
    peer=socket.socket(socket.AF_UNIX)
    peer.connect(ENDPOINT);out['socket']='CONNECTED'
except OSError:out['socket']='denied'
finally:
    if peer is not None:peer.close()
print(json.dumps(out))
'''.replace('TARGETS',repr(targets)).replace('ENDPOINT',repr(c['socket'])))
    binary=os.environ.get('CODEX_MONITOR_NATIVE_CODEX') or shutil.which('codex')
    assert binary,'Codex CLI must be installed for the selected native probe'
    data={'model':'gpt-6.1-sol','analytics':{'enabled':False},
          'features':{'network_proxy':True},'permissions':{m['MQ_PERMISSION_PROFILE']:m['mq_permission_profile'](c)}}
    if legacy:data['sandbox_mode']='workspace-write'
    (Path(c['codex_home'])/'config.toml').write_text(toml_tables(data))
    native=Native(binary,c)
    try:
        result=native.rpc('command/exec',{'command':[sys.executable,str(script)],'cwd':c['cwd'],
            'permissionProfile':m['MQ_PERMISSION_PROFILE'],'timeoutMs':20000})
        assert result['exitCode']==0,result
        assert json.loads(result['stdout'])=={
            'source_read':True,**{label:'denied' for label in targets},'socket':'denied'}
        assert all(not Path(target).exists() for target in targets.values())
    finally:native.close()


class Responses(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        assert self.path=='/v1/responses',self.path
        raw=self.rfile.read(int(self.headers['Content-Length']))
        if self.headers.get('Content-Encoding')=='gzip':raw=gzip.decompress(raw)
        data=json.loads(raw);self.server.requests.append(data)
        index=len(self.server.requests)-1
        if index==0 and getattr(self.server,'command',None):
            code=('let r=await tools.exec_command('+json.dumps({'cmd':self.server.command,
                'yield_time_ms':1000,'max_output_tokens':5000})+');text(r);'
                'while(r.session_id){r=await tools.write_stdin({session_id:r.session_id,chars:"",yield_time_ms:1000,max_output_tokens:5000});text(r);}')
            item={'type':'custom_tool_call','id':'host-probe','call_id':'host-probe',
                'namespace':'functions','name':'exec','input':code}
        elif index<len(self.server.targets):
            item={'type':'custom_tool_call','id':'patch-'+str(index),'call_id':'patch-'+str(index),'name':'apply_patch',
                  'input':'*** Begin Patch\n*** Add File: '+str(self.server.targets[index])+'\n+native edit\n*** End Patch'}
        else:
            item={'id':'msg-'+str(len(self.server.requests)),'type':'message','role':'assistant',
                'status':'completed','phase':'final_answer',
                'content':[{'type':'output_text','text':'fixture complete','annotations':[]}]}
        response={'id':'resp-'+str(len(self.server.requests)),'object':'response','status':'completed',
            'model':data['model'],'output':[item],'usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2}}
        events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}},
            {'type':'response.output_item.added','output_index':0,'item':item},
            {'type':'response.output_item.done','output_index':0,'item':item},
            {'type':'response.completed','response':response}]
        body=''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
        self.send_response(200);self.send_header('Content-Type','text/event-stream')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)


def test_native_codex_project_cold_resume_and_edit(native_workspace):
    m,c,roots,main,script,expected=native_workspace
    binary=os.environ.get('CODEX_MONITOR_NATIVE_CODEX') or shutil.which('codex');assert binary
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Responses)
    server.requests=[]
    server.targets=[roots[-1]/'native-edit',main/'native-outside',roots[0]/'escape'/'native-symlink',
                    Path(c['queue_file']).parent/'native-mutate']
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    config={'model':'gpt-6.1-sol','model_provider':'fixture','analytics':{'enabled':False},
        'mcp_servers':{'gitlab':{'command':'fixture-mcp-must-never-run','enabled':False}},
        'model_providers':{'fixture':{'name':'Disposable fixture','base_url':f'http://127.0.0.1:{server.server_port}/v1',
            'wire_api':'responses','requires_openai_auth':False,'supports_websockets':False}}}
    (Path(c['codex_home'])/'config.toml').write_text(toml_tables(config))
    native=Native(binary,c)
    try:
        project=native.rpc('project/create',{'idempotencyKey':str(uuid.uuid4()),'name':'Disposable workspace',
            'roots':[{'path':str(p)} for p in roots]})['project']
        selected=m['mq_native_selection'](c)
        created=native.rpc('thread/start',{'cwd':c['cwd'],'ephemeral':False,'projectId':project['id'],
            'runtimeWorkspaceRoots':c['_workspace']['roots'],'approvalPolicy':'never',
            'developerInstructions':m['mq_instructions'](),**selected})
        m['mq_verify_permission_selection'](c,created)
        thread=created['thread'];identifier=thread['id']
        assert thread['projectId']==project['id']
        assert m['monitor_thread_source_roots'](c,thread)==c['_workspace']['roots']
        visible=m['mq_render_input']({'stage':str(uuid.uuid4()),'kind':'code',
            'url':'https://gitlab.example.test/team/repo/-/merge_requests/82','head':'a'*40,
            'workspace':c['_workspace'],'model_selection':{'model':'gpt-6.1-sol','effort':'xhigh'},
            'original_source':{'origin':'automatic'},'prior_reviewers':[]})
        native.turn(identifier,m['mq_codex_permissions'](c),visible)
        history=native.rpc('thread/turns/list',{'threadId':identifier,'itemsView':'notLoaded'})
        turn=history['data'][0]['id']
        wire=native.rpc('thread/items/list',{'threadId':identifier,'turnId':turn})
        users=[r['item'] for r in wire['data'] if r['item']['type']=='userMessage']
        assert len(users)==1 and len(users[0]['content'])==1
        assert users[0]['content'][0]['type']=='text' and users[0]['content'][0]['text']==visible
        assert server.targets[0].read_text()=='native edit\n'
        assert all(p.read_text()=='native edit\n' for p in server.targets[1:])
        outputs=[i for i in server.requests[-1]['input'] if i.get('type')=='custom_tool_call_output']
        assert {i['call_id'] for i in outputs}=={'patch-'+str(i) for i in range(4)}
        assert not any('rejected' in str(item['output']).lower() for item in outputs)
        extra=main.parent/'new folder';extra.mkdir()
        native.rpc('project/update',{'projectId':project['id'],
            'roots':[{'path':str(p)} for p in [*roots,extra]]})
        native.close();native=Native(binary,c)
        resumed=native.rpc('thread/resume',{'threadId':identifier,'excludeTurns':True,
            'runtimeWorkspaceRoots':c['_workspace']['roots'],'approvalPolicy':'never',**selected})
        m['mq_verify_permission_selection'](c,resumed)
        assert resumed['thread']['projectId']==project['id']
        assert m['monitor_thread_source_roots'](c,resumed['thread'])==c['_workspace']['roots']
        native.turn(identifier,m['mq_codex_permissions'](c))
        assert len(server.requests)==6
        assert json.dumps(m['mq_instructions']())[1:-1] in json.dumps(server.requests[-1])
        for writable in (False,True):
            c['_workspace_write']=writable
            target=main/('role-'+str(writable))
            server.targets += [main/'unused']*(len(server.requests)-len(server.targets))
            server.targets.append(target)
            native.close();native=Native(binary,c)
            selected=m['mq_native_selection'](c)
            resumed=native.rpc('thread/resume',{'threadId':identifier,'excludeTurns':True,
                'runtimeWorkspaceRoots':c['_workspace']['roots'],'approvalPolicy':'never',**selected})
            expected_profile={'id':':danger-full-access','extends':None} if writable else {
                'id':m['MQ_PERMISSION_PROFILE'],'extends':':read-only'}
            assert resumed['activePermissionProfile']==expected_profile
            native.turn(identifier,m['mq_codex_permissions'](c))
            assert target.exists()==writable
        # Full access is retained by a later manual turn with no override.
        target=main/'manual-continuation'
        server.targets += [main/'unused']*(len(server.requests)-len(server.targets))
        server.targets.append(target)
        native.turn(identifier,None)
        assert target.read_text()=='native edit\n'
    finally:
        native.close();server.shutdown();server.server_close();worker.join(5)


@pytest.mark.skipif(os.environ.get('CODEX_MONITOR_HOST_PROBES')!='1',
    reason='requires explicitly selected host Docker, GCR and read-only GitLab SSH probes')
@pytest.mark.parametrize('reviewer',['codex','claude'])
def test_native_review_host_commands(native_workspace,monkeypatch,reviewer):
    m,c,roots,main,script,expected=native_workspace
    agent=Path(os.environ['XDG_RUNTIME_DIR'])/'gcr/ssh'
    assert agent.is_socket() and agent.stat().st_uid==os.getuid()
    monkeypatch.setenv('SSH_AUTH_SOCK',str(agent))
    target='git@'+os.environ['CODEX_MONITOR_HOST_GITLAB']
    reference=subprocess.run(['ssh-add','-l'],capture_output=True,text=True,check=True).stdout
    result_file=roots[0]/'host-result.json'
    script=roots[0]/'host-probe.py'
    script.write_text('''import json,os,subprocess,socket,urllib.request,urllib.error
from pathlib import Path
out={'agent':os.environ.get('SSH_AUTH_SOCK')}
for name,command in COMMANDS.items():
    r=subprocess.run(command,capture_output=True,text=True,timeout=12)
    out[name]={'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
for url in ['https://pypi.org','https://registry.npmjs.org','https://api.osv.dev']:
    try:
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=8) as response:out[url]=response.status
    except urllib.error.HTTPError as error:out[url]=error.code
with socket.socket() as server:server.bind(('127.0.0.1',0));out['binding']=True
Path(RESULT).write_text(json.dumps(out))
'''.replace('COMMANDS',repr({'docker':['docker','version','--format','{{json .Server.Version}}'],
        'keys':['ssh-add','-l'],'ssh':['ssh','-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes',
        '-oConnectTimeout=8',target]})).replace('RESULT',repr(str(result_file))))
    command=shlex.join([sys.executable,str(script)])
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Responses if reviewer=='codex' else Provider)
    server.requests=[];server.targets=[];server.command=command
    server.steps=[('Bash',{'command':command,'description':'Read-only host capability check'})]
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    native=None
    try:
        if reviewer=='codex':
            data={'model':'gpt-6.1-sol','model_provider':'fixture','analytics':{'enabled':False},
                'mcp_servers':{'gitlab':{'command':'fixture-must-not-run','enabled':False}},
                'model_providers':{'fixture':{'name':'Local fixture','base_url':f'http://127.0.0.1:{server.server_port}/v1',
                    'wire_api':'responses','requires_openai_auth':False,'supports_websockets':False}}}
            (Path(c['codex_home'])/'config.toml').write_text(toml_tables(data))
            native=Native(os.environ.get('CODEX_MONITOR_NATIVE_CODEX') or shutil.which('codex'),c,
                environment={'SSH_AUTH_SOCK':'/tmp/fixture-no-agent','HTTP_PROXY':'','HTTPS_PROXY':'','ALL_PROXY':'','NO_PROXY':'*'})
            selected=m['mq_native_selection'](c)
            created=native.rpc('thread/start',{'cwd':c['cwd'],'approvalPolicy':'never',**selected})
            m['mq_verify_permission_selection'](c,created)
            native.turn(created['thread']['id'],m['mq_codex_permissions'](c))
        else:
            home=Path(c['claude_home'])
            (home/'.claude.json').write_text(json.dumps({'projects':{c['cwd']:{'hasTrustDialogAccepted':True}}}))
            environment={k:v for k,v in m['mq_claude_environment'](c).items()
                if not k.startswith(('ANTHROPIC_','CODEX_','OPENAI_'))}
            environment.update(ANTHROPIC_API_KEY='fixture-only',ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',
                CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_AUTOUPDATER='1',HTTP_PROXY='',HTTPS_PROXY='',ALL_PROXY='',NO_PROXY='*')
            result=subprocess.run([shutil.which('claude'),*m['mq_claude_arguments'](c,'Run the read-only fixture.','capability fixture')],
                cwd=c['cwd'],env=environment,capture_output=True,text=True,timeout=60)
            assert result.returncode==0,result.stderr
        assert result_file.is_file(),'native command never completed'
        result=json.loads(result_file.read_text())
        assert result['agent']==str(agent)
        assert result['keys']['code']==0 and result['keys']['stdout']==reference
        assert result['docker']['code']==0,result
        assert result['ssh']['code']==0 and 'Welcome to GitLab' in result['ssh']['stdout'],result
        assert result['binding'] is True and result['https://pypi.org']==200 and result['https://registry.npmjs.org']==200
        assert result['https://api.osv.dev'] in {200,404}
    finally:
        if native:native.close()
        server.shutdown();server.server_close();thread.join(5)


class Provider(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if '/count_tokens' in self.path:
            self.reply(b'{"input_tokens":1}','application/json');return
        assert self.path.split('?')[0]=='/v1/messages',self.path
        self.server.requests.append(data)
        index=len(self.server.requests)-1
        if index==0 and hasattr(self.server,'release'):
            self.server.entered.set()
            assert self.server.release.wait(35),'fixture provider was never released'
        step_index=0 if getattr(self.server,'retry_on_busy',False) and 'monitor is checking this stage; retry this tool' in json.dumps(data['messages'][-1]) else index
        tool=step_index<len(self.server.steps)
        if tool:
            name,value=self.server.steps[step_index]
            block={'type':'tool_use','id':'tool-'+str(index),'name':name,'input':{}}
            delta={'type':'input_json_delta','partial_json':json.dumps(value)}
        else:
            block={'type':'text','text':''};delta={'type':'text_delta','text':getattr(self.server,'final_text','native fixture complete')}
        message={'id':'msg-'+str(index),'type':'message','role':'assistant','model':data['model'],
            'content':[],'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':1,'output_tokens':0}}
        events=[('message_start',{'type':'message_start','message':message}),
            ('content_block_start',{'type':'content_block_start','index':0,'content_block':block}),
            ('content_block_delta',{'type':'content_block_delta','index':0,'delta':delta}),
            ('content_block_stop',{'type':'content_block_stop','index':0}),
            ('message_delta',{'type':'message_delta','delta':{'stop_reason':'tool_use' if tool else 'end_turn',
                'stop_sequence':None},'usage':{'output_tokens':1}}),('message_stop',{'type':'message_stop'})]
        self.reply(''.join('event: '+kind+'\ndata: '+json.dumps(value)+'\n\n' for kind,value in events).encode(),'text/event-stream')
    def reply(self,raw,kind):
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)


@pytest.mark.parametrize('mode',['review','unavailable','intake'])
def test_native_claude_commands_editing_and_denials(native_workspace,mode):
    m,c,roots,main,script,expected=native_workspace
    unavailable=mode=='unavailable'
    if mode!='review':c['_workspace_write']=False
    binary=shutil.which('claude');assert binary,'Claude CLI must be installed for the selected native probe'
    home=Path(c['claude_home'])
    (home/'.claude.json').write_text(json.dumps({'projects':{c['cwd']:{'hasTrustDialogAccepted':True}}}))
    (home/'settings.json').write_text(json.dumps({'permissions':{'additionalDirectories':[str(main)]}}))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
    server.requests=[]
    server.steps=[('Bash',{'command':shlex.join([sys.executable,str(script)]),'description':'Disposable native probe'}),
        ('Write',{'file_path':str(roots[-1]/'tool-write'),'content':'initial'}),
        ('Edit',{'file_path':str(roots[-1]/'tool-write'),'old_string':'initial','new_string':'edited'}),
        ('Write',{'file_path':str(main/'tool-outside'),'content':'forbidden'}),
        ('Read',{'file_path':str(Path(c['queue_file']).parent/'input.json')})]
    if unavailable:
        # This command is allowed by intake, so the error must come from the sandbox.
        server.steps=[('Bash',{'command':'codex-session-stats current --client claude --format json',
            'description':'Allowed read-only intake command with unavailable confinement'})]
    if mode=='intake':
        server.steps=[('Bash',{'command':shlex.join([sys.executable,'-c',
            'from pathlib import Path;Path('+repr(str(root/'written'))+').write_text("forbidden")']),
            'description':'Disposable intake write attempt'}) for root in (roots[0],roots[-1])]
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    args=m['mq_claude_arguments'](c,'Run the disposable fixture.','fixture')
    environment={k:v for k,v in os.environ.items() if not k.startswith(('ANTHROPIC_','CLAUDE_','CODEX_'))}
    environment.update(CLAUDE_CONFIG_DIR=str(home),ANTHROPIC_API_KEY='fixture-only',
        ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
        DISABLE_AUTOUPDATER='1',HTTP_PROXY='http://127.0.0.1:9',HTTPS_PROXY='http://127.0.0.1:9',NO_PROXY='127.0.0.1,localhost')
    if unavailable:
        executables=home/'missing-sandbox';executables.mkdir()
        # A real installed-client launch must refuse Bash when its confinement helper fails.
        for name in ('bwrap','socat','which'):
            executable=executables/name;executable.write_text('#!/bin/sh\necho fixture-unavailable >&2\nexit 1\n')
            executable.chmod(0o700)
        environment['PATH']=str(executables)
    try:
        with (home/'stdout').open('w+') as out,(home/'stderr').open('w+') as err:
            result=subprocess.run([binary,*args],cwd=c['cwd'],env=environment,
                stdin=subprocess.DEVNULL,stdout=out,stderr=err,text=True,timeout=45)
            out.seek(0);err.seek(0)
            stdout,stderr=out.read(),err.read()
        assert result.returncode==0,(stdout,stderr)
        assert len(server.requests)==len(server.steps)+1
        results={block['tool_use_id']:block for message in server.requests[-1]['messages']
            if message['role']=='user' and isinstance(message.get('content'),list)
            for block in message['content'] if block.get('type')=='tool_result'}
        if mode!='review':
            assert not any((root/'written').exists() for root in roots)
            assert all(results['tool-'+str(i)]['is_error'] is True for i in range(len(server.steps))),results
            assert not (main/'bad').exists()
            if unavailable:
                assert 'sandbox' in str(results['tool-0']['content']).lower(),results
            return
        trusted={**{str(root):'ok' for root in roots},
            **{key:'WRITTEN' for key in ('main-source','symlink','queue','native')},'socket':'CONNECTED'}
        assert json.loads(results['tool-0']['content'])==trusted
        assert (roots[-1]/'tool-write').read_text()=='edited'
        assert results['tool-3']['is_error'] is True and not (main/'tool-outside').exists()
        assert 'immutable' in results['tool-4']['content']
    finally:
        server.shutdown();server.server_close();worker.join(5)


@pytest.mark.parametrize('large',[False,True])
def test_native_claude_finite_service_consumer_and_cold_resume(flow,module,tmp_path,monkeypatch,large):
    """Real installed Claude/systemd, real FIFO consumer, local model and GitLab wire fixtures."""
    f=flow;m=f.m
    for name in ('mq_service_command','mq_service_identity','mq_cgroup_empty'):
        monkeypatch.setitem(m,name,module[name])
    binary=shutil.which('claude');assert binary
    f.raw.update(claude_bin=binary,review_timeout_seconds=30,reviewers=['codex','claude'] if large else ['claude','codex'])
    f.config_path.write_text(json.dumps(f.raw))
    f.config.clear();f.config.update(m['mq_config'](f.config_path))
    home=Path(f.config['claude_home']);home.mkdir()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
    server.requests=[];server.steps=[]
    server.final_text='Estado da revisão: aguardando resposta\nWhich fixture rule should be used?'
    server.retry_on_busy=True
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    for key in list(os.environ):
        if key.startswith(('ANTHROPIC_','CLAUDE_','CODEX_')):monkeypatch.delenv(key)
    for key,value in dict(ANTHROPIC_API_KEY='fixture-only',
        ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_AUTOUPDATER='1',
        HTTP_PROXY='http://127.0.0.1:9',HTTPS_PROXY='http://127.0.0.1:9',NO_PROXY='127.0.0.1,localhost').items():
        monkeypatch.setenv(key,value)
    stage=None
    try:
        job=f.q.enqueue(11,82,source_key='native-print',kind='code',head='a'*40,
            source={'origin':'automatic'},context=f.context)
        if large:
            f.step()
            first=f.q.job(job['id'])['stages'][0]
            f.items[first['turn_id']][-1]['text']='Earlier review context: '+('á context '*20000)+'\nEstado da revisão: concluída\nCommit revisado: '+'a'*40
            assert m['mq_consume'](f.config,f.q) # Collect the actual preceding native final.
        index=1 if large else 0
        assert m['mq_consume'](f.config,f.q)
        stage=f.q.job(job['id'])['stages'][index]
        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            m['mq_consume'](f.config,f.q)
            saved=f.q.job(job['id'])
            if saved['stages'][index]['state']!='running':break
            time.sleep(.1)
        assert saved['stages'][index]['state']=='succeeded',saved
        request=saved['stages'][index]['input']
        if large:assert len(request.encode('utf-8'))>131072
        native_records=m['mq_claude_records'](f.config,stage['session'])
        user=next(r for r in native_records if r['type']=='user')
        assert user['message']['content']==request
        assert saved['stages'][index]['result']['question']=='Which fixture rule should be used?'
        assert f.q.mr(11,82)['hold']['native_anchor']==saved['stages'][index]['anchor']
        assert m['mq_print_execution'](f.config,saved['stages'][index])['terminal'] is True
        assert m['mq_cgroup_empty'](stage['service_identity']['root']+'/app.slice/'+stage['unit'])
        f.drain()
        assert f.launched==(['codex'] if large else []) and f.sends==[]
        assert f.q.job(job['id'])['wait_reason']=='human'
        server.final_text='Cold resume fixture complete.\nEstado da revisão: concluída\nCommit revisado: '+'a'*40
        marker=Path(f.config['cwd'])/'native-human-continuation'
        server.steps=[('unused',{})]*len(server.requests)+[('Write',{'file_path':str(marker),'content':'continued'})]
        arguments=m['mq_claude_arguments'](m['mq_workspace_config'](f.config,saved),'Later fixture input','resume')
        prompt_index=arguments.index('--append-system-prompt');del arguments[prompt_index:prompt_index+2]
        arguments[-2:-2]=['--resume',stage['session']]
        output=subprocess.run([binary,*arguments],cwd=f.config['cwd'],env=m['mq_claude_environment'](f.config),
            stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=30)
        assert output.returncode==0,output.stderr
        assert marker.read_text()=='continued'
        assert any(m['mq_instructions']() in block.get('text','') for block in server.requests[-1]['system'])
        assert 'csm-assessment' not in m['mq_instructions']()
        # Revalidation still selects the captured question, never the resumed final.
        observed=m['mq_claude_observe'](f.config,saved['stages'][index])
        assert observed['anchor']==saved['stages'][index]['anchor']
        assert observed['text']=='Estado da revisão: aguardando resposta\nWhich fixture rule should be used?'
        m['mq_intake'](f.config,f.q,f.q.mr(11,82))
        assert f.q.mr(11,82)['hold'] is None
        f.drain()
        completed=f.q.job(job['id'])
        assert completed['state']=='completed' and f.q.mr(11,82)['reviewed_head']=='a'*40
        assert completed['stages'][index]['result']['outcome']=='question'
        assert completed['stages'][index]['continuations'][0]['outcome']['result']['outcome']=='complete'
        assert f.launched==['codex'] and f.sends==[] and len(f.q.jobs())==1
    finally:
        if stage and stage.get('unit'):
            state=m['mq_service_show'](f.config,stage['unit'])
            if state.get('ActiveState') not in {'inactive','failed'}:
                m['mq_service_command'](f.config,['systemctl','--user','stop',stage['unit']])
            assert m['mq_cgroup_empty'](stage['service_identity']['root']+'/app.slice/'+stage['unit'])
        server.shutdown();server.server_close();worker.join(5)


@pytest.mark.parametrize('case',['exit-code','timeout'])
def test_native_finite_service_failure_stops_children_and_continues_codex(flow,module,tmp_path,monkeypatch,case):
    """Actual systemd lifecycle with disposable executable; no model or remote provider."""
    f=flow;m=f.m
    for name in ('mq_service_command','mq_service_identity','mq_cgroup_empty'):
        monkeypatch.setitem(m,name,module[name])
    executable=tmp_path/'finite-client'
    executable.write_text('#!'+sys.executable+'\nimport os,time\n'+
        ('raise SystemExit(7)\n' if case=='exit-code' else 'os.fork()\ntime.sleep(60)\n'))
    executable.chmod(0o700)
    f.raw.update(claude_bin=str(executable),review_timeout_seconds=2)
    f.config_path.write_text(json.dumps(f.raw));f.config.clear();f.config.update(m['mq_config'](f.config_path))
    stage=None
    try:
        job=f.q.enqueue(11,82,source_key='native-'+case,kind='code',head='a'*40,
            source={'origin':'automatic'},context=f.context)
        m['mq_step'](f.config,f.q);stage=f.q.job(job['id'])['stages'][0]
        monkeypatch.setitem(m,'mq_stamp',lambda:stage['started_at'])
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            m['mq_step'](f.config,f.q)
            saved=f.q.job(job['id'])
            if saved['stages'][0]['state']!='running':break
            time.sleep(.1)
        assert saved['stages'][0]['state']=='failed',saved
        assert case in saved['stages'][0]['error']['message']
        assert m['mq_cgroup_empty'](stage['service_identity']['root']+'/app.slice/'+stage['unit'])
        f.drain()
        assert f.q.job(job['id'])['wait_reason']=='reviewer_retry'
        assert f.q.job(job['id'])['stages'][1]['state']=='succeeded'
        assert f.launched==['codex'] and f.sends==[]
    finally:
        if stage and stage.get('unit'):
            current=m['mq_service_show'](f.config,stage['unit'])
            if current.get('ActiveState') not in {'inactive','failed'}:
                m['mq_service_command'](f.config,['systemctl','--user','stop',stage['unit']])
            assert m['mq_cgroup_empty'](stage['service_identity']['root']+'/app.slice/'+stage['unit'])
            if m['mq_service_show'](f.config,stage['unit']).get('ActiveState')=='failed':
                m['mq_service_command'](f.config,['systemctl','--user','reset-failed',stage['unit']])
