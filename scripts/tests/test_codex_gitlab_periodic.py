"""Periodic consumer and native-Claude recovery regressions; no external services."""
import copy
import http.server
import json
from pathlib import Path
import subprocess
import threading
import time
import uuid

import pytest

from test_codex_gitlab_queue import assessment, domain, flow, human_turn, module, rendered


def enqueue(f, iid=82):
    return f.q.enqueue(11,iid,source_key='periodic:'+str(iid),kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context))


def quiet_scan(f, monkeypatch):
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)


def test_interactive_inventory_does_not_invalidate_background(module,monkeypatch):
    m=module['mq_step'].__globals__
    background={'kind':'background','id':'worker','sessionId':'session','cwd':'/fixture',
        'name':'owned','state':'running'}
    interactive={'kind':'interactive','pid':42,'sessionId':'other','cwd':'/other',
        'name':'manual','status':'idle'}
    monkeypatch.setitem(m,'mq_claude_command',lambda *a:json.dumps([interactive,background]))
    assert m['mq_claude_agents']({})==[background]


@pytest.mark.parametrize('custom',[False,True])
def test_native_default_and_custom_preferences_environment(module,tmp_path,monkeypatch,custom):
    m=module['mq_step'].__globals__;captured={}
    home=tmp_path/'custom' if custom else Path.home()/'.claude'
    monkeypatch.setenv('CLAUDE_CONFIG_DIR','/inherited/unwanted')
    def run(argv,**kw):
        captured.update(kw['env']);kw['stdout'].write('[]')
        return subprocess.CompletedProcess(argv,0)
    monkeypatch.setattr(subprocess,'run',run)
    config={'claude_home':str(home.resolve()),'claude_bin':'fixture','cwd':str(tmp_path),'native_timeout':2}
    assert m['mq_claude_command'](config,['agents','--json','--all'])=='[]'
    assert captured.get('CLAUDE_CONFIG_DIR')==(str(home.resolve()) if custom else None)


def test_post_launch_missing_inventory_never_releases_serial_capacity(flow,monkeypatch):
    original=flow.m['mq_claude_command']
    def command(c,args):
        if args[0]=='agents':raise FileNotFoundError('inventory disappeared after accepted launch')
        return original(c,args)
    monkeypatch.setitem(flow.m,'mq_claude_command',command)
    job=enqueue(flow)
    flow.m['mq_step'](flow.config,flow.q)
    saved=flow.q.job(job['id'])
    assert saved['stages'][0]['state']=='running'
    assert saved['stages'][0]['delivery']=='sending'
    assert flow.launched==['claude']


@pytest.mark.parametrize('first_failure',[False,True])
def test_successive_ticks_resume_same_stage_then_advance_and_exit(flow,monkeypatch,first_failure):
    quiet_scan(flow,monkeypatch);job=enqueue(flow)
    if first_failure:flow.results['claude']=RuntimeError('terminal provider failure')
    for expected in (['claude'],['claude','codex'],['claude','codex']):
        result=flow.m['mq_tick'](flow.config_path)
        assert result['cycle']=='checked'
        assert flow.launched==expected
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.q.mr(11,82)['reviewed_head']=='a'*40


def test_ticks_with_active_reviewer_do_not_wait_or_start_another(flow,monkeypatch):
    quiet_scan(flow,monkeypatch);job=enqueue(flow)
    flow.m['mq_tick'](flow.config_path)
    original=flow.m['mq_claude_records']
    monkeypatch.setitem(flow.m,'mq_claude_records',lambda *a:[])
    flow.m['mq_tick'](flow.config_path)
    flow.m['mq_tick'](flow.config_path)
    assert flow.launched==['claude']
    assert flow.q.job(job['id'])['stages'][0]['state']=='running'
    monkeypatch.setitem(flow.m,'mq_claude_records',original)
    flow.m['mq_tick'](flow.config_path)
    assert flow.launched==['claude','codex']


@pytest.mark.parametrize('stop_confirmed',[False,True])
def test_expired_owned_reviewer_only_progresses_after_stop_confirmation(flow,monkeypatch,stop_confirmed):
    quiet_scan(flow,monkeypatch);job=enqueue(flow)
    flow.m['mq_tick'](flow.config_path)
    job=flow.q.job(job['id']);stage=job['stages'][0]
    flow.m['mq_update_stage'](flow.q,job,stage['id'],review_deadline=1)
    monkeypatch.setitem(flow.m,'mq_claude_records',lambda *a:[])
    stopped=[]
    def stop(c,native):
        stopped.append(native['sessionId']);return stop_confirmed
    monkeypatch.setitem(flow.m,'mq_claude_stop',stop)
    flow.m['mq_tick'](flow.config_path)
    saved=flow.q.job(job['id'])
    assert stopped==[stage['session']]
    assert bool(saved['stages'][0]['cancel_requested_at'])
    assert saved['stages'][0]['state']==('failed' if stop_confirmed else 'running')
    assert flow.launched==(['claude','codex'] if stop_confirmed else ['claude'])


def test_expired_unacknowledged_attempt_retains_intent_and_capacity(flow,monkeypatch):
    quiet_scan(flow,monkeypatch)
    def lost(c,args):raise RuntimeError('lost launch acknowledgment')
    monkeypatch.setitem(flow.m,'mq_claude_command',lost)
    job=enqueue(flow);flow.m['mq_tick'](flow.config_path)
    job=flow.q.job(job['id']);stage=job['stages'][0]
    flow.m['mq_update_stage'](flow.q,job,stage['id'],review_deadline=1)
    monkeypatch.setitem(flow.m,'mq_claude_agents',lambda *a:[])
    flow.m['mq_tick'](flow.config_path)
    saved=flow.q.job(job['id'])
    assert saved['state']=='running' and saved['stages'][0]['cancel_requested_at']
    assert saved['stages'][0]['review_deadline']==1
    assert flow.launched==[]
    assert 'unacknowledged' in flow.q.meta('consumer_error')['error']


def test_acceptance_and_mr_ownership_commit_together(flow,monkeypatch):
    original=flow.m['mq_claude_accept']
    monkeypatch.setitem(flow.m,'mq_claude_accept',lambda *a:None)
    job=enqueue(flow);flow.m['mq_step'](flow.config,flow.q)
    job=flow.q.job(job['id']);stage=job['stages'][0]
    assert stage['session'] is None
    monkeypatch.setitem(flow.m,'mq_claude_accept',original)
    put=flow.q.put_mr
    monkeypatch.setattr(flow.q,'put_mr',lambda r:(_ for _ in ()).throw(InterruptedError('registration crash')))
    with pytest.raises(InterruptedError):original(flow.config,flow.q,job,stage)
    saved=flow.q.job(job['id'])
    assert saved['stages'][0]['session'] is None
    assert flow.q.mr(11,82)['chats']=={}
    monkeypatch.setattr(flow.q,'put_mr',put)
    original(flow.config,flow.q,saved,saved['stages'][0])
    session=flow.q.job(job['id'])['stages'][0]['session']
    assert flow.q.mr(11,82)['chats']['claude']==session
    assert flow.q.mr(11,82)['claude_contexts'][session]==flow.config['cwd']


def test_existing_accepted_registration_is_repaired_idempotently(flow,monkeypatch):
    job=enqueue(flow);flow.m['mq_step'](flow.config,flow.q)
    # Model the old version's interruption between its separate acknowledgment and mapping commits.
    with flow.q.atomic():flow.q.put_mr({'repository_id':11,'iid':82,'chats':{},'hold':None})
    flow.m['mq_step'](flow.config,flow.q)
    saved=flow.q.job(job['id']);session=saved['stages'][0]['session']
    assert flow.q.mr(11,82)['chats']['claude']==session
    assert flow.q.mr(11,82).get('claude_history',[])==[]


def test_budget_before_launch_preserves_prepared_attempt(flow,monkeypatch):
    quiet_scan(flow,monkeypatch);job=enqueue(flow)
    original=flow.m['mq_claude_command']
    def yield_before(c,args):raise flow.m['MonitorCycleYield']('before spawn')
    monkeypatch.setitem(flow.m,'mq_claude_command',yield_before)
    result=flow.m['mq_tick'](flow.config_path)
    saved=flow.q.job(job['id']);attempt=saved['stages'][0]['id']
    assert result['yielded'] and saved['stages'][0]['delivery']=='prepared'
    assert saved['stages'][0]['state']=='running' and flow.launched==[]
    monkeypatch.setitem(flow.m,'mq_claude_command',original)
    flow.m['mq_tick'](flow.config_path)
    assert flow.q.job(job['id'])['stages'][0]['id']==attempt
    assert flow.launched==['claude']


def test_ready_progression_precedes_inventory_that_uses_its_budget(flow,monkeypatch):
    quiet_scan(flow,monkeypatch);job=enqueue(flow)
    flow.m['mq_tick'](flow.config_path)
    def slow(*args):
        assert flow.launched==['claude','codex']
        raise flow.m['MonitorCycleYield']('slow inventory')
    monkeypatch.setitem(flow.m,'mq_inventory',slow)
    flow.m['mq_tick'](flow.config_path)
    assert flow.launched==['claude','codex']


@pytest.mark.parametrize('after_send',[False,True,'interrupted_send'])
def test_budget_yield_around_send_retains_batch_and_does_not_repeat_review(flow,monkeypatch,after_send):
    quiet_scan(flow,monkeypatch)
    action={'key':'finding','kind':'finding','body':'[P2] Subtraia o desconto.',
        'position':{'position_type':'text','base_sha':'b'*40,'start_sha':'c'*40,'head_sha':'a'*40,
            'old_path':'x.py','new_path':'x.py','new_line':1}}
    flow.results['codex']=domain(actions=[action]);job=enqueue(flow)
    flow.m['mq_tick'](flow.config_path);flow.m['mq_tick'](flow.config_path)
    original_send=flow.m['mq_send'];original_context=flow.m['mq_context'];sent=[False]
    def send(*args):
        if not after_send:raise flow.m['MonitorCycleYield']('before send')
        result=original_send(*args);sent[0]=True
        if after_send=='interrupted_send':raise flow.m['MonitorCycleYield']('during possible send',issued=True)
        return result
    def context(*args,**kw):
        if sent[0] and after_send is True:raise flow.m['MonitorCycleYield']('after send')
        return original_context(*args,**kw)
    monkeypatch.setitem(flow.m,'mq_send',send);monkeypatch.setitem(flow.m,'mq_context',context)
    flow.m['mq_tick'](flow.config_path)
    saved=flow.q.job(job['id']);batch=copy.deepcopy(saved['batch'])
    assert saved['state']=='running' and saved['outcome'] is None
    assert len(flow.sends)==int(bool(after_send))
    monkeypatch.setitem(flow.m,'mq_send',original_send);monkeypatch.setitem(flow.m,'mq_context',original_context)
    flow.m['mq_tick'](flow.config_path)
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.q.job(job['id'])['batch']==batch
    assert len(flow.sends)==1 and flow.launched==['claude','codex']


@pytest.mark.parametrize('changed',[None,'version','binary','message','session'])
def test_original_launch_only_trust_rejection_requires_unchanged_identity(flow,tmp_path,monkeypatch,changed):
    binary=tmp_path/'claude-fixture';binary.write_text('fixture');binary.chmod(0o700)
    flow.config['claude_bin']=str(binary)
    def lost(c,args):raise RuntimeError('legacy original launch failed')
    monkeypatch.setitem(flow.m,'mq_claude_command',lost)
    job=enqueue(flow);flow.m['mq_step'](flow.config,flow.q)
    job=flow.q.job(job['id']);stage=job['stages'][0]
    message=f"Claude CLI failed: Workspace not trusted. Run `claude` in {flow.config['cwd']} once and accept the trust prompt, then retry."
    flow.m['mq_update_stage'](flow.q,job,stage['id'],error={'message':message})
    monkeypatch.setitem(flow.m,'mq_claude_agents',lambda *a:[])
    monkeypatch.setitem(flow.m,'mq_claude_command',lambda *a:'new version' if changed=='version' else '2.1.289 (Claude Code)\n')
    if changed=='message':flow.m['mq_update_stage'](flow.q,job,stage['id'],error={'message':message+' other operation'})
    if changed=='session':flow.m['mq_update_stage'](flow.q,job,stage['id'],session='already-issued-session')
    if changed=='binary':flow.m['mq_update_stage'](flow.q,job,stage['id'],started_at=0)
    flow.m['mq_step'](flow.config,flow.q)
    saved=flow.q.job(job['id'])
    assert saved['stages'][0]['state']==('failed' if changed is None else 'running')
    if changed is None:
        assert saved['stages'][0]['error']['not_started']
        assert saved['stages'][0]['error']['evidence']['version']=='2.1.289'
        assert flow.q.mr(11,82)['reviewed_head'] is None


def test_slow_human_intake_rotates_to_later_mr_on_next_cycle(flow,monkeypatch):
    with flow.q.atomic():
        flow.q.put_mr({'repository_id':11,'iid':1,'chats':{},'hold':None})
        flow.q.put_mr({'repository_id':11,'iid':2,'chats':{},'hold':{'question':'original'}})
    seen=[]
    def intake(c,q,r):
        seen.append(r['iid'])
        if r['iid']==1:raise flow.m['MonitorCycleYield']('slow first MR')
    monkeypatch.setitem(flow.m,'mq_intake',intake)
    monkeypatch.setitem(flow.m,'mq_inventory',lambda *a:True)
    flow.m['mq_tick'](flow.config_path)
    assert seen==[1]
    flow.m['mq_tick'](flow.config_path)
    assert seen[:2]==[1,2]
    assert flow.q.mr(11,2)['hold']=={'question':'original'}


def test_partial_inventory_continues_after_slow_mr_without_restarting_page(flow,monkeypatch):
    pages=[];seen=[]
    class API:
        def __init__(self,*a,**kw):pass
        def project(self):return {'id':11}
        def pages(self,route,*,start_page=1):
            pages.append(start_page)
            yield [{'iid':1},{'iid':2}],True
    def context(c,iid,**kw):
        seen.append(iid)
        if iid==1:raise flow.m['MonitorCycleYield']('slow first MR')
        result=copy.deepcopy(flow.context);result['iid']=iid;result['mr']['iid']=iid
        return result
    monkeypatch.setitem(flow.m,'MonitorGitLab',API)
    monkeypatch.setitem(flow.m,'mq_context',context)
    with pytest.raises(flow.m['MonitorCycleYield']):flow.m['mq_inventory'](flow.config,flow.q)
    assert seen==[1] and pages==[1]
    assert flow.m['mq_inventory'](flow.config,flow.q)
    assert seen==[1,2] and pages==[1]
    assert flow.q.jobs('pending')[0]['iid']==2


@pytest.mark.parametrize('bad',[{}, {'kind':'background','id':'worker'}, {'kind':'unknown'}])
def test_malformed_inventory_cannot_authorize_execution(module,monkeypatch,bad):
    m=module['mq_step'].__globals__
    monkeypatch.setitem(m,'mq_claude_command',lambda *a:json.dumps([bad]))
    with pytest.raises(RuntimeError):m['mq_claude_agents']({})


@pytest.mark.parametrize('trusted',[False,True])
def test_preflight_uses_same_native_preferences_as_launch(module,tmp_path,monkeypatch,trusted):
    m=module['mq_step'].__globals__;home=tmp_path/'client';home.mkdir()
    config={'cwd':str(tmp_path/'workspace'),'claude_home':str(home)}
    (home/'.claude.json').write_text(json.dumps({'projects':{config['cwd']:{'hasTrustDialogAccepted':trusted}}}))
    operations=[]
    def command(c,args):
        operations.append(args[0]);return json.dumps({'loggedIn':True}) if args[0]=='auth' else '[]'
    monkeypatch.setitem(m,'mq_claude_command',command)
    if trusted:
        m['mq_claude_preflight'](config)
        assert operations==['auth','agents']
    else:
        with pytest.raises(RuntimeError,match='not trusted'):m['mq_claude_preflight'](config)
        assert operations==['auth']


@pytest.mark.parametrize('operation,issued',[('--bg',True),('agents',False),('stop',True)])
def test_command_timeout_at_cycle_deadline_yields_with_delivery_evidence(module,tmp_path,monkeypatch,operation,issued):
    m=module['mq_step'].__globals__
    def timeout(argv,**kw):raise subprocess.TimeoutExpired(argv,kw['timeout'])
    monkeypatch.setattr(subprocess,'run',timeout)
    monkeypatch.setitem(m,'mq_expired',lambda c:True)
    config={'claude_home':str(tmp_path),'claude_bin':'fixture','cwd':str(tmp_path),'native_timeout':1}
    with pytest.raises(m['MonitorCycleYield']) as yielded:m['mq_claude_command'](config,[operation,'fixture'])
    assert yielded.value.issued is issued


def test_cycle_timeout_after_possible_launch_preserves_sending_identity(flow,monkeypatch):
    quiet_scan(flow,monkeypatch);job=enqueue(flow)
    def uncertain(*args):raise flow.m['MonitorCycleYield']('possible accepted input',issued=True)
    monkeypatch.setitem(flow.m,'mq_claude_command',uncertain)
    flow.m['mq_tick'](flow.config_path)
    saved=flow.q.job(job['id']);stage=saved['stages'][0]
    assert stage['state']=='running' and stage['delivery']=='sending'
    assert stage['input'] and stage['name'] and stage['review_deadline']
    monkeypatch.setitem(flow.m,'mq_claude_agents',lambda *a:[])
    flow.m['mq_tick'](flow.config_path)
    assert flow.q.job(job['id'])['stages'][0]['id']==stage['id']
    assert flow.launched==[]


@pytest.mark.parametrize('method',['GET','POST'])
def test_http_deadline_bounds_trickling_response_not_only_socket_inactivity(module,monkeypatch,method):
    m=module['mq_step'].__globals__;stop=threading.Event();requests=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def respond(self):
            requests.append(self.command)
            if self.command=='POST':self.rfile.read(int(self.headers['Content-Length']))
            body=b'{"ok":true}'+b' '*30
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers()
            for byte in body:
                if stop.wait(.01):break
                try:self.wfile.write(bytes([byte]));self.wfile.flush()
                except (BrokenPipeError,ConnectionResetError):break
        do_GET=respond
        do_POST=respond
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    monkeypatch.setitem(m,'monitor_credential',lambda c:(f'http://127.0.0.1:{server.server_port}','fixture-token'))
    config={'http_timeout':.08,'max_response_bytes':1024,'_cycle_deadline':time.monotonic()+.12}
    api=m['MonitorGitLab'](config)
    started=time.monotonic()
    try:
        with pytest.raises(m['MonitorCycleYield']) as yielded:
            if method=='GET':api.get('/fixture')
            else:m['mq_send'](api,'POST','/fixture',{'body':'fixture'})
        assert time.monotonic()-started<.3
        assert yielded.value.issued is (method=='POST')
        assert requests==[method]
    finally:
        stop.set();server.shutdown();server.server_close();worker.join(2)


@pytest.mark.parametrize('failure',['slow','unavailable'])
def test_old_session_cannot_hide_sufficient_answer_in_later_claude_session(flow,monkeypatch,failure):
    flow.results['claude']=domain(outcome='question',question='Qual regra de CSP considerar?')
    job=enqueue(flow);flow.drain();hold=flow.q.mr(11,82)['hold']
    assert hold['provider']=='claude'
    text='considere a regra atual e continue';source=str(uuid.uuid4());final=str(uuid.uuid4())
    answer=domain(assessment=assessment(text,kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    target=next((Path(flow.config['claude_home'])/'projects').glob('*/'+hold['session']+'.jsonl'))
    rows=[{'type':'user','uuid':source,'parentUuid':hold['native_anchor'],'sessionId':hold['session'],
        'cwd':flow.config['cwd'],'message':{'content':text}},
        {'type':'assistant','uuid':final,'parentUuid':source,'sessionId':hold['session'],
         'message':{'stop_reason':'end_turn','content':[{'type':'text','text':rendered(answer)}]}}]
    with target.open('a') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')
    old=str(uuid.uuid4());record=flow.q.mr(11,82)
    record['codex_contexts']={old:record['codex_context'],**record['codex_contexts']}
    with flow.q.atomic():flow.q.put_mr(record)
    original=flow.m['monitor_native']
    def native(c,method,params,**kw):
        if params.get('threadId')==old:
            error=flow.m['MonitorCycleYield'] if failure=='slow' else RuntimeError
            raise error('unreadable historical session')
        return original(c,method,params,**kw)
    monkeypatch.setitem(flow.m,'monitor_native',native)
    for _ in range(2):
        try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
        except (RuntimeError,flow.m['MonitorCycleYield']):pass
    record=flow.q.mr(11,82)
    assert record['hold']==hold
    assert flow.q.job(job['id'])['wait_reason']=='answer_ready'
    assert record['pending_answers'][0]['source']['session']==hold['session']
    assert record['pending_answers'][0]['source']['source_id']==source
    flow.results.update(claude=domain(),codex=domain());flow.drain()
    record=flow.q.mr(11,82)
    assert record['hold'] is None and record['hold_history'][0]['answer']['source_id']==source


def test_slow_earlier_source_in_same_session_does_not_hide_answer(flow,monkeypatch):
    flow.results.update(claude=RuntimeError('terminal'),codex=domain(outcome='question',question='Qual regra considerar?'))
    job=enqueue(flow);flow.drain();hold=flow.q.mr(11,82)['hold']
    old=human_turn(flow,'primeiro pedido antigo')
    source=human_turn(flow,'considere a regra atual e continue')
    answer=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':rendered(answer)})
    original=flow.m['mq_codex_items']
    def items(c,session,turn):
        if turn==old['turn_id']:raise flow.m['MonitorCycleYield']('slow earlier turn')
        return original(c,session,turn)
    monkeypatch.setitem(flow.m,'mq_codex_items',items)
    for _ in range(2):
        try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
        except flow.m['MonitorCycleYield']:pass
    assert flow.q.job(job['id'])['wait_reason']=='answer_ready'
    assert flow.q.mr(11,82)['pending_answers'][0]['source']==source
    assert flow.q.mr(11,82)['hold']==hold


def test_recorded_mixed_inventory_artifact_preserves_native_acceptance(flow,monkeypatch):
    capture=json.loads((Path(__file__).parent/'fixtures'/'claude-agents-mixed.json').read_text())
    assert capture['capture_kind']=='recorded-artifact'
    assert any(r['kind']=='interactive' and 'id' not in r for r in capture['response'])
    original=flow.m['mq_claude_command'];consumed=[]
    def command(c,args):
        output=original(c,args)
        if args==capture['operation'] and not consumed:
            consumed.append(args)
            return json.dumps([*capture['response'],*json.loads(output)])
        return output
    monkeypatch.setitem(flow.m,'mq_claude_command',command)
    job=enqueue(flow);flow.m['mq_step'](flow.config,flow.q)
    saved=flow.q.job(job['id']);stage=saved['stages'][0]
    assert stage['delivery']=='accepted' and stage['session']
    assert flow.q.mr(11,82)['chats']['claude']==stage['session']
    flow.drain()
    assert consumed==[capture['operation']]
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.launched==['claude','codex'] and flow.sends==[]


@pytest.mark.parametrize('question_first',[False,True])
def test_paged_history_resumes_answer_order_proof_across_cycles(flow,monkeypatch,question_first):
    flow.results.update(claude=RuntimeError('terminal'),codex=domain(outcome='question',question='Qual regra considerar?'))
    job=enqueue(flow);flow.drain();hold=flow.q.mr(11,82)['hold']
    source=human_turn(flow,'considere a regra atual e continue')
    answer=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':rendered(answer)})
    session=hold['session'];native=flow.m['monitor_native'];calls=[];clock=[0];budget=[0]
    question=next(t for t in flow.turns[session] if t['id']==hold['turn_id'])
    user=next(t for t in flow.turns[session] if t['id']==source['turn_id'])
    filler={'id':'empty-old-turn','status':'completed'};flow.items[filler['id']]=[]
    pages=[[question if question_first else user],[filler],[user if question_first else question]]
    def paged(c,method,params,**kw):
        if method=='thread/turns/list':
            page=int(params.get('cursor','0'));calls.append(page)
            # Each invocation can finish two pages; a whole-history read cannot finish.
            clock[0]+=1
            if clock[0]>budget[0]:raise flow.m['MonitorCycleYield']('history share exhausted')
            return {'data':pages[page],'nextCursor':str(page+1) if page+1<len(pages) else None}
        return native(c,method,params,**kw)
    monkeypatch.setitem(flow.m,'monitor_native',paged)
    for _ in range(12):
        budget[0]=clock[0]+2
        try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
        except (RuntimeError,flow.m['MonitorCycleYield']):pass
        if flow.q.job(job['id'])['wait_reason']=='answer_ready':break
    record=flow.q.mr(11,82)
    assert record['hold']==hold and flow.sends==[]
    if question_first:
        assert flow.q.job(job['id'])['wait_reason']=='human'
        assert not record.get('pending_answers')
    else:
        assert flow.q.job(job['id'])['wait_reason']=='answer_ready'
        assert record['pending_answers'][0]['source']==source
        # Final release reuses exact order evidence but still rereads native source/anchor.
        monkeypatch.setitem(flow.m,'monitor_native',native)
        flow.results.update(claude=domain(),codex=domain());flow.drain()
        assert flow.q.mr(11,82)['hold'] is None
        assert flow.q.mr(11,82)['hold_history'][0]['answer']==source
    assert 2 in calls


def test_paged_intake_visits_latest_source_before_reading_older_pages(flow,monkeypatch):
    enqueue(flow);flow.drain()
    source=human_turn(flow,'explique a regra atual')
    answer=domain(outcome='noop',assessment=assessment(source['texts'][0],kind='explanation'))
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'explanation','phase':'final_answer','text':rendered(answer)})
    native=flow.m['monitor_native'];calls=[]
    def paged(c,method,params,**kw):
        if method=='thread/turns/list':
            calls.append(params.get('cursor'))
            if params.get('cursor'):raise flow.m['MonitorCycleYield']('slow older page')
            return {'data':[flow.turns[source['session']][0]],'nextCursor':'older'}
        return native(c,method,params,**kw)
    monkeypatch.setitem(flow.m,'monitor_native',paged)
    try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    except flow.m['MonitorCycleYield']:pass
    assert flow.q.meta('human:'+source['session']+':'+source['turn_id'])=={'disposition':'observed'}
    assert calls==[None,'older'] and flow.sends==[]


def test_answer_appended_after_cursor_stalls_is_found_on_fresh_head(flow,monkeypatch):
    flow.results.update(claude=RuntimeError('terminal'),codex=domain(outcome='question',question='Qual regra considerar?'))
    job=enqueue(flow);flow.drain();hold=flow.q.mr(11,82)['hold']
    native=flow.m['monitor_native'];calls=[]
    def paged(c,method,params,**kw):
        if method=='thread/turns/list':
            calls.append(params.get('cursor'))
            if params.get('cursor'):raise flow.m['MonitorCycleYield']('permanently slow old page')
            return {'data':flow.turns[hold['session']],'nextCursor':'older'}
        return native(c,method,params,**kw)
    monkeypatch.setitem(flow.m,'monitor_native',paged)
    try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    except flow.m['MonitorCycleYield']:pass
    assert calls==[None,'older']
    source=human_turn(flow,'considere a regra atual e continue')
    answer=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':rendered(answer)})
    try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    except flow.m['MonitorCycleYield']:pass
    assert flow.q.job(job['id'])['wait_reason']=='answer_ready'
    assert flow.q.mr(11,82)['pending_answers'][0]['source']==source
    assert flow.q.mr(11,82)['hold']==hold and flow.sends==[]


def test_slow_recent_source_does_not_starve_saved_answer_in_history(flow,monkeypatch):
    flow.results.update(claude=RuntimeError('terminal'),codex=domain(outcome='question',question='Qual regra considerar?'))
    job=enqueue(flow);flow.drain();hold=flow.q.mr(11,82)['hold']
    source=human_turn(flow,'considere a regra atual e continue')
    answer=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':rendered(answer)})
    native=flow.m['monitor_native'];initial=[True];reads=[];poison=[None]
    question=next(t for t in flow.turns[hold['session']] if t['id']==hold['turn_id'])
    user=next(t for t in flow.turns[hold['session']] if t['id']==source['turn_id'])
    def paged(c,method,params,**kw):
        if method=='thread/turns/list':
            if initial[0]:
                if reads:raise flow.m['MonitorCycleYield']('initial interrupted order proof')
                reads.append(None);return {'data':[user],'nextCursor':'older'}
            if params.get('cursor'):return {'data':[user,question],'nextCursor':None}
            return {'data':[flow.turns[hold['session']][0]],'nextCursor':'older'}
        if method=='thread/items/list' and params['turnId']==poison[0]:
            raise flow.m['MonitorCycleYield']('permanently slow recent source')
        return native(c,method,params,**kw)
    monkeypatch.setitem(flow.m,'monitor_native',paged)
    try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    except flow.m['MonitorCycleYield']:pass
    initial[0]=False;poison[0]=human_turn(flow,'outro pedido recente')['turn_id']
    for _ in range(4):
        try:flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
        except flow.m['MonitorCycleYield']:pass
        if flow.q.job(job['id'])['wait_reason']=='answer_ready':break
    assert flow.q.job(job['id'])['wait_reason']=='answer_ready'
    assert flow.q.mr(11,82)['pending_answers'][0]['source']==source
    assert flow.q.mr(11,82)['hold']==hold and flow.sends==[]
