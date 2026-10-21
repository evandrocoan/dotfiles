"""Component contracts of the real fresh queue; no native or GitLab effects."""
import copy
import os
from pathlib import Path
import runpy

import pytest

CLI = Path(os.environ.get('CODEX_MONITOR_TEST_CLI', Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats'))


@pytest.fixture
def module():
    return runpy.run_path(str(CLI), run_name='queue_contract_test')


@pytest.fixture
def queue(module, tmp_path):
    root = tmp_path / 'private'
    root.mkdir(mode=0o700)
    config = {'queue_file': str(root / 'queue.sqlite3'), 'gitlab_url': 'https://gitlab.example.test',
              'codex_home': str(tmp_path / 'codex'), 'reviewers': ['claude', 'codex']}
    q = module['MonitorQueue'](config)
    yield q
    q.close()


def enqueue(q, repository=11, iid=82, *, kind='code', marker='one'):
    return q.enqueue(repository, iid, source_key=f'{repository}:{iid}:{kind}:{marker}', kind=kind,
        head='a' * 40, source={'native_input': marker}, context={'head': 'a' * 40})


@pytest.mark.parametrize('reviewers', [['claude', 'codex'], ['codex', 'claude']])
@pytest.mark.parametrize('outcomes', [(True, True), (True, False), (False, True), (False, False)])
def test_every_enabled_reviewer_runs_after_success_or_any_failure(queue, reviewers, outcomes):
    queue.config['reviewers'] = reviewers
    enqueue(queue)
    job = queue.reserve({11})
    actual = []
    for reviewer, succeeds in zip(reviewers, outcomes):
        assert queue.next_reviewer(job) == reviewer
        stage = queue.stage_start(job, reviewer, 'registered input ' + reviewer)
        actual.append(reviewer)
        with pytest.raises(RuntimeError, match='every enabled reviewer'):
            queue.review_result(job)
        if succeeds:
            queue.stage_end(job, stage['id'], result={'head': 'a'*40, 'outcome':'complete', 'from': reviewer}, terminal=True)
        else:
            queue.stage_end(job, stage['id'], error={'message': 'arbitrary failure'}, terminal=True)
    assert actual == reviewers
    assert queue.next_reviewer(job) is None
    expected = next((reviewer for reviewer, success in reversed(list(zip(reviewers, outcomes))) if success), None)
    result = queue.review_result(job)
    assert result == ({'head': 'a'*40, 'outcome':'complete', 'from': expected} if expected else None)
    assert [s['state'] for s in queue.job(job['id'])['stages']] == [
        'succeeded' if success else 'failed' for success in outcomes]
    assert queue.mr(11, 82)['reviewed_head'] is None


@pytest.mark.parametrize('error', ['credits exhausted', 'authentication failed', 'network failed',
                                 'invalid output', 'refusal', 'any other terminal failure'])
def test_error_cause_never_controls_continuation(queue, error):
    enqueue(queue)
    job = queue.reserve({11})
    first = queue.stage_start(job, 'claude', 'first')
    queue.stage_end(job, first['id'], error={'message': error}, terminal=True)
    assert queue.next_reviewer(job) == 'codex'
    second = queue.stage_start(job, 'codex', 'second')
    assert second['reviewer'] == 'codex'
    assert queue.job(job['id'])['stages'][0]['error'] == {'message': error}
    assert queue.effects() == []


@pytest.mark.parametrize('reviewer', ['claude', 'codex'])
def test_one_enabled_reviewer_runs_once(queue, reviewer):
    queue.config['reviewers'] = [reviewer]
    enqueue(queue)
    job = queue.reserve({11})
    stage = queue.stage_start(job, reviewer, 'input')
    queue.stage_end(job, stage['id'], result={'head': 'a'*40, 'outcome':'complete'}, terminal=True)
    assert queue.next_reviewer(job) is None
    queue.finish(job, 'reviewed', reviewed=True)
    assert queue.job(job['id'])['state'] == 'completed'
    assert queue.mr(11, 82)['reviewed_head'] == 'a'*40


def test_unknown_execution_cannot_start_next_or_release_capacity(queue):
    enqueue(queue)
    later = enqueue(queue, repository=22)
    job = queue.reserve({11, 22})
    stage = queue.stage_start(job, 'claude', 'input')
    with pytest.raises(RuntimeError, match='terminal identity is unproven'):
        queue.stage_end(job, stage['id'], error={'message':'connection lost'}, terminal=False)
    with pytest.raises(RuntimeError, match='previous reviewer execution'):
        queue.stage_start(job, 'codex', 'second')
    with pytest.raises(RuntimeError, match='native execution is unknown'):
        queue.park(job, 'retry')
    assert queue.reserve({11, 22})['id'] == job['id']
    assert queue.job(later['id'])['state'] == 'pending'
    assert queue.effects() == []


def test_fifo_shared_across_repositories_and_same_iids(queue):
    a = enqueue(queue, repository=22)
    b = enqueue(queue, repository=11)
    assert queue.reserve({11, 22})['id'] == a['id']
    queue.finish(queue.job(a['id']), 'superseded')
    assert queue.reserve({11, 22})['id'] == b['id']
    assert queue.mr(11, 82)['chats'] == {}
    assert queue.mr(22, 82)['chats'] == {}


def test_hold_blocks_same_mr_but_other_repository_progresses(queue):
    a = enqueue(queue)
    enqueue(queue, marker='later')
    c = enqueue(queue, repository=22)
    job = queue.reserve({11,22})
    record = queue.mr(11,82)
    with queue.atomic():
        record['hold'] = {'job_id': a['id'], 'question': 'Explain the intended behavior.'}
        queue.put_mr(record)
    queue.park(job, 'human')
    assert queue.reserve({11,22})['id'] == c['id']
    assert queue.job(a['id'])['wait_reason'] == 'human'
    assert queue.mr(11,82)['hold'] == record['hold']


def test_repeat_and_restart_preserve_sources_and_policy(queue, module):
    original = enqueue(queue)
    queue.config['reviewers'] = ['codex']
    repeated = enqueue(queue)
    assert repeated['id'] == original['id']
    assert repeated['reviewers'] == ['claude', 'codex']
    reopened = module['MonitorQueue'](queue.config)
    try:
        assert reopened.jobs() == queue.jobs()
        assert reopened.epoch == queue.epoch
    finally:
        reopened.close()
    with pytest.raises(RuntimeError, match='repeated source identity changed'):
        queue.enqueue(22,82,source_key='11:82:code:one',kind='code',head='a'*40,
            source={'native_input':'one'},context={})
    assert len(queue.jobs()) == 1


def test_human_completion_cannot_advance_code_checkpoint(queue):
    queue.config['reviewers'] = ['codex']
    enqueue(queue, kind='human')
    job = queue.reserve({11})
    stage = queue.stage_start(job, 'codex', 'human input')
    queue.stage_end(job, stage['id'], result={'head':'a'*40, 'outcome':'complete'}, terminal=True)
    with pytest.raises(RuntimeError, match='only actual completed code review'):
        queue.finish(job, 'reviewed', reviewed=True)
    queue.finish(job, 'human request completed')
    assert queue.mr(11,82)['reviewed_head'] is None
    assert queue.job(job['id'])['state'] == 'completed'


def test_all_failed_cannot_advance_checkpoint(queue):
    enqueue(queue)
    job = queue.reserve({11})
    for reviewer in ['claude','codex']:
        stage = queue.stage_start(job, reviewer, reviewer)
        queue.stage_end(job, stage['id'], error={'message':'failed'}, terminal=True)
    with pytest.raises(RuntimeError, match='only actual completed code review'):
        queue.finish(job, 'reviewed', reviewed=True)
    queue.park(job, 'all reviewers failed', retry_at=12345)
    assert queue.job(job['id'])['state'] == 'pending'
    assert queue.job(job['id'])['retry_at'] == 12345
    assert queue.mr(11,82)['reviewed_head'] is None
    assert queue.effects() == []


def test_stale_result_cannot_settle_current_attempt(queue):
    enqueue(queue)
    job = queue.reserve({11})
    stale = copy.deepcopy(job)
    stage = queue.stage_start(job, 'claude', 'source A')
    with pytest.raises(RuntimeError, match='stale or mismatched running job'):
        queue.stage_end(stale, stage['id'], result={'head':'a'*40, 'outcome':'complete'}, terminal=True)
    with pytest.raises(RuntimeError, match='terminal identity is unproven'):
        queue.stage_end(job, 'another-stage', result={'head':'a'*40, 'outcome':'complete'}, terminal=True)
    assert queue.job(job['id'])['stages'][0]['state'] == 'running'
    assert queue.effects() == []


def test_foreign_database_is_rejected_without_modification(queue, module, tmp_path):
    import hashlib
    import sqlite3
    target = tmp_path / 'foreign.sqlite3'
    connection = sqlite3.connect(target)
    connection.execute('CREATE TABLE predecessor(value TEXT)')
    connection.execute("INSERT INTO predecessor VALUES('do not migrate')")
    connection.commit()
    connection.close()
    target.chmod(0o600)
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match='predecessor databases are never imported'):
        module['MonitorQueue']({**queue.config, 'queue_file': str(target)})
    assert hashlib.sha256(target.read_bytes()).hexdigest() == before
    connection = sqlite3.connect(target)
    try:
        assert connection.execute('SELECT value FROM predecessor').fetchall() == [('do not migrate',)]
        assert connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [('predecessor',)]
    finally:
        connection.close()


def domain(iid=82, *, outcome='complete', actions=None, assessment=None, question=None):
    return {'version':1,'repository_id':11,'iid':iid,'head':'a'*40,'outcome':outcome,
            'question':question,'assessment':assessment,'actions':actions or [],'concerns':[],'dispositions':[]}


def rendered(value):
    import json
    return ((value.get('question') or '')+'\n```csm-review\n'+json.dumps(value)+'\n```\nProposta preparada.')


def compact(value):
    import json
    assessment=value['assessment']
    return '```csm-assessment\n'+json.dumps({'kind':assessment['kind'],'summary':assessment['summary'],
        **assessment['scope'],'question_anchor':assessment.get('question_anchor')})+'\n```'


@pytest.fixture
def flow(module,tmp_path,monkeypatch):
    """Actual worker/SQLite with external native/GitLab providers and explicit model steps."""
    import json
    import uuid
    import sys
    from gitlab_print_service_fixture import PrintService
    m = module['mq_step'].__globals__
    config_path = tmp_path/'config.json'
    raw = m['monitor_default_config']('https://gitlab.example.test/team/repo',11,'gitlab')
    raw.update(cwd=str(tmp_path),codex_home=str(tmp_path/'codex'),state_file=str(tmp_path/'old'/'old.sqlite3'),
               claude_bin=sys.executable,claude_home=str(tmp_path/'claude'),queue_file=str(tmp_path/'queue'/'queue.sqlite3'),reviewers=['claude','codex'])
    config_path.write_text(json.dumps(raw)); config_path.chmod(0o600)
    config = m['mq_config'](config_path)
    Path(config['codex_home']).mkdir()
    (Path(config['codex_home'])/'config.toml').write_text('')
    context = {'repository_id':11,'iid':82,'head':'a'*40,'actor_id':7,
        'mr':{'iid':82,'project_id':11,'state':'opened','sha':'a'*40,'title':'MR',
              'diff_refs':{'head_sha':'a'*40,'base_sha':'b'*40,'start_sha':'c'*40}},
        'threads':[],'diff':{'head_commit_sha':'a'*40,'base_commit_sha':'b'*40,'start_commit_sha':'c'*40,
            'diffs':[{'old_path':'x.py','new_path':'x.py','diff':'@@ -1 +1 @@\n-old\n+new'}]}}
    turns,items,chats,claude_agents = {},{},{},[]
    launched,sends,results = [],[],{'claude':domain(),'codex':domain()}
    class API:
        def __init__(self,c,guard=None): self.config=c
        def project(self): return {'id':11}
        def get(self,route):
            if route.startswith('/users/'): return {'id':int(route.rsplit('/',1)[1]),'bot':True}
            raise AssertionError(route)
    def native(c,method,params,**kwargs):
        if kwargs.get('followup'):
            import asyncio
            result=native(c,method,params)
            async def request(name,arguments):return m['monitor_native'](c,name,arguments)
            return asyncio.run(kwargs['followup'](request,result))
        if method=='thread/start':
            identity=str(uuid.uuid4()); chats[identity]={'id':identity,'cwd':c['cwd'],
                'projectId':params.get('projectId'),'status':{'type':'idle'},
                'environments':[{'environmentId':'local','cwd':c['cwd'],
                                 'runtimeWorkspaceRoots':params.get('runtimeWorkspaceRoots',[c['cwd']])}]}
            turns[identity]=[]
            return {'thread':chats[identity], 'activePermissionProfile':{'id':m['MQ_PERMISSION_PROFILE'],'extends':':read-only'}}
        if method in {'thread/resume','thread/read'}: return {'thread':chats[params['threadId']],
            'activePermissionProfile':{'id':m['MQ_PERMISSION_PROFILE'],'extends':':read-only'}}
        if method=='thread/name/set': return {}
        if method=='turn/start':
            launched.append('codex'); t=str(uuid.uuid4()); result=results['codex']
            row={'id':t,'status':'failed' if isinstance(result,Exception) else 'completed','error':str(result)}
            turns[params['threadId']].insert(0,row)
            items[t]=[{'type':'userMessage','id':'source-'+t,'clientId':params['clientUserMessageId'],'content':params['input']}]
            if not isinstance(result,Exception):
                items[t].append({'type':'agentMessage','id':'final-'+t,'phase':'final_answer','text':rendered(result)})
            return {'turn':row}
        if method=='thread/turns/list': return {'data':turns[params['threadId']],'nextCursor':None}
        if method=='thread/items/list': return {'data':[{'turnId':params['turnId'],'item':i} for i in items[params['turnId']]],'nextCursor':None}
        raise AssertionError(method)
    def claude(c,args):
        if args[:2]==['agents','--json']: return json.dumps(claude_agents)
        assert args[0] in {'--bg','--print'}
        launched.append('claude'); session=args[args.index('--session-id')+1] if args[0]=='--print' else str(uuid.uuid4()); src=str(uuid.uuid4()); final=str(uuid.uuid4())
        name=args[args.index('--name')+1]
        claude_agents.append({'id':session[:8],'sessionId':session,'name':name,'cwd':c['cwd'],'kind':'background','state':'running'})
        result=results['claude']
        rows=[{'type':'user','uuid':src,'sessionId':session,'cwd':c['cwd'],'message':{'content':c.get('_test_stdin',args[-1]) if args[0]=='--print' else args[1]}}]
        rows.append({'type':'assistant','uuid':final,'parentUuid':src,'sessionId':session,
            'isApiErrorMessage':isinstance(result,Exception),'error':str(result),
            'message':{'id':'message-'+final,'stop_reason':'end_turn','content':[{'type':'text','text':str(result) if isinstance(result,Exception) else rendered(result)}]}})
        rows.append({'type':'system','subtype':'turn_duration','uuid':str(uuid.uuid4()),
            'parentUuid':final,'sessionId':session})
        root=Path(c['claude_home'])/'projects'/'fixture';root.mkdir(parents=True,exist_ok=True)
        (root/(session+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        return '{}'
    def send(api,method,route,payload):
        sends.append((method,route,payload))
        identity='d'+str(len(sends))
        note={'id':100+len(sends),'body':payload['body'],'author':{'id':7},'system':False,
            'created_at':'2026-10-19T00:00:00Z','resolvable':True,'resolved':False,'position':payload.get('position')}
        if '/notes' in route:
            thread=next(t for t in context['threads'] if t['id']==route.rsplit('/',2)[1]);thread['notes'].append(note)
        else:
            context['threads'].append({'id':identity,'notes':[note]})
        return note
    monkeypatch.setitem(m,'MonitorGitLab',API)
    monkeypatch.setitem(m,'mq_context',lambda *a,**kw:copy.deepcopy(context))
    monkeypatch.setitem(m,'monitor_native',native)
    monkeypatch.setitem(m,'mq_claude_command',claude)
    service=PrintService(config,lambda c,args:m['mq_claude_command'](c,args))
    monkeypatch.setitem(m,'mq_service_command',service.command)
    monkeypatch.setitem(m,'mq_service_identity',lambda c:service.identity.copy())
    monkeypatch.setitem(m,'mq_cgroup_empty',lambda group:not service.populated)
    monkeypatch.setitem(m,'mq_send',send)
    q=m['MonitorQueue'](config)
    class Flow:
        pass
    f=Flow(); f.m=m;f.q=q;f.config=config;f.context=context;f.results=results
    f.service=service
    f.launched=launched;f.sends=sends;f.chats=chats;f.turns=turns;f.items=items;f.raw=raw;f.config_path=config_path
    f.model_calls=[];f.model_errors=[];f.processed=set()
    def model_step():
        active=q.jobs('running')
        if not active or not active[0]['stages']:return
        job=active[0];stage=job['stages'][-1]
        if stage['state']!='running' or stage.get('protocol')!='tools' or stage['id'] in f.processed:return
        if not stage.get('session'):return
        result=results[stage['reviewer']]
        if isinstance(result,Exception):return
        native_path=None;records=None
        if stage['reviewer']=='codex':
            if not stage.get('session') or not turns.get(stage['session']):return
            stage=copy.deepcopy(stage)
            if not stage.get('turn_id'):stage['turn_id']=turns[stage['session']][0]['id']
            turn=next(t for t in turns[stage['session']] if t['id']==stage['turn_id'])
            turn['status']='inProgress'
            final=items[stage['turn_id']].pop()
            source_id=items[stage['turn_id']][0]['id']
        else:
            native_path=Path(config['claude_home'])/'projects'/'fixture'/(stage['session']+'.jsonl')
            if not native_path.exists():return # This injected provider never accepted execution.
            records=[json.loads(line) for line in native_path.read_text().splitlines()]
            source_id=records[0]['uuid'];final=records[1];records=records[:1]
            state=service.units[stage['unit']];original_state=state.copy()
            state.update(ActiveState='active',SubState='running',ControlGroup=stage['service_identity']['root']+'/app.slice/'+stage['unit'])
            service.populated=True
        f.processed.add(stage['id'])
        def call(name,args):
            current=q.job(job['id']);current_stage=current['stages'][-1];call_id='tool-'+str(uuid.uuid4())
            if stage['reviewer']=='codex':
                meta={'threadId':stage['session'],'sessionId':stage['session'],'callId':call_id,
                    'x-codex-turn-metadata':{'thread_id':stage['session'],'session_id':stage['session'],'turn_id':stage['turn_id']}}
            else:
                records.append({'uuid':str(uuid.uuid4()),'parentUuid':records[-1]['uuid'],'type':'assistant',
                    'sessionId':stage['session'],'cwd':config['cwd'],'message':{'id':'message-'+call_id,
                    'content':[{'type':'tool_use','id':call_id,'name':'mcp__gitlab_review__'+name,'input':args}]}})
                native_path.write_text(''.join(json.dumps(r)+'\n' for r in records))
                meta={'claudecode/toolUseId':call_id}
            f.model_calls.append((stage['reviewer'],name,args))
            value=m['mq_tool_execute'](m['mq_workspace_config'](config,current),q,current,current_stage,meta,name,args)
            if records is not None:
                records.append({'uuid':str(uuid.uuid4()),'parentUuid':records[-1]['uuid'],'type':'user',
                    'sessionId':stage['session'],'cwd':config['cwd'],
                    'message':{'content':[{'type':'tool_result','tool_use_id':call_id,'content':json.dumps(value)}]}})
            return value
        text=result.get('question') or 'Revisão concluída com análise estática; testes não executados.'
        try:
            if job['kind']=='intake':
                a=result.get('assessment') or {'kind':'explanation','summary':'No explicit action',
                    'scope':{'effects':[],'discussions':[]},'question_anchor':None}
                text='```csm-assessment\n'+json.dumps({'kind':a['kind'],'summary':a['summary'],
                    **a['scope'],'question_anchor':a.get('question_anchor')})+'\n```'
            elif stage.get('purpose')=='question':
                text=job['pending_question']['question'];call('ask_human',{'question':text})
            elif result['outcome']=='question':call('ask_human',{'question':text})
            elif result['outcome']=='complete':
                call('read_mr',{})
                for action in result['actions']:
                    if action['kind']=='finding':
                        p=action['position'];side='new' if p.get('new_line') else 'old'
                        call('publish_finding',{'body':action['body'],'path':p[side+'_path'],'line':p[side+'_line'],'side':side})
                    elif action['kind']=='reply':call('reply',{'discussion':action['discussion'],'body':action['body']})
                    else:
                        call('read_discussion',{'discussion':action['discussion']})
                        notes=[{'note':n['id'],'status':n['concerns'][0]['disposition'] if n.get('concerns') else 'no_concern',
                            'evidence':n['concerns'][0]['evidence'] if n.get('concerns') else n['no_concern_reason']}
                            for n in action['assessment']['notes']]
                        call('resolve',{'discussion':action['discussion'],'explanation':action['body'],
                            'basis':action['basis'],'notes':notes})
                call('finish_review',{})
        except (OSError,RuntimeError,ValueError) as error:
            f.model_errors.append(error);text='Não concluí: '+str(error)
        finally:
            if stage['reviewer']=='codex':
                turn['status']='completed';final['text']=text;items[stage['turn_id']].append(final)
            else:
                service.populated=False;state.clear();state.update(original_state)
                final['parentUuid']=records[-1]['uuid'];final['message']['content']=[{'type':'text','text':text}]
                records.append(final);records.append({'uuid':str(uuid.uuid4()),'parentUuid':final['uuid'],
                    'sessionId':stage['session'],'type':'system','subtype':'turn_duration'})
                native_path.write_text(''.join(json.dumps(r)+'\n' for r in records))
                directory=Path(config['queue_file']).parent/'executions'/stage['id']
                stream=[{'type':'assistant','session_id':stage['session'],'uuid':final['uuid'],
                    'parent_tool_use_id':None,'message':final['message']},
                    {'type':'result','session_id':stage['session'],'is_error':False,'subtype':'success','result':text}]
                (directory/'stdout').write_text(''.join(json.dumps(r)+'\n' for r in stream))
                receipt=json.loads((directory/'receipt.json').read_text())
                import hashlib
                receipt['stdout_digest']=hashlib.sha256((directory/'stdout').read_bytes()).hexdigest()
                (directory/'receipt.json').write_text(json.dumps(receipt))
    def step(connection=None):
        value=m['mq_step'](config,connection or q);model_step();return value
    def tick():
        value=m['mq_tick'](config_path);model_step();return value
    def drain(limit=20):
        for _ in range(limit):
            if not step():return
        raise AssertionError('worker failed to reach idle/hold')
    f.model_step=model_step;f.step=step;f.tick=tick;f.drain=drain
    yield f
    q.close()


@pytest.mark.parametrize('first_failure',[False,True])
@pytest.mark.parametrize('second_failure',[False,True])
def test_worker_runs_both_and_settles_actual_coverage(flow,first_failure,second_failure):
    for reviewer,fails in [('claude',first_failure),('codex',second_failure)]:
        if fails: flow.results[reviewer]=RuntimeError('arbitrary terminal provider failure')
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic','head':'a'*40},context=copy.deepcopy(flow.context))
    flow.drain()
    assert flow.launched==['claude','codex']
    saved=flow.q.job(job['id'])
    assert [s['state'] for s in saved['stages']]==['failed' if f else 'succeeded' for f in [first_failure,second_failure]]
    assert saved['state']==('pending' if first_failure or second_failure else 'completed')
    assert flow.q.mr(11,82)['reviewed_head']==(None if first_failure and second_failure else 'a'*40)
    assert flow.sends==[]


def test_worker_preserves_native_receipts_after_restart_and_does_not_resend(flow):
    action={'key':'subtraction','kind':'finding','body':'[P2] Subtraia o desconto.',
        'position':{'position_type':'text','base_sha':'b'*40,'start_sha':'c'*40,'head_sha':'a'*40,
                    'old_path':'x.py','new_path':'x.py','new_line':1}}
    flow.results['codex']=domain(actions=[action])
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    # Every advancement rereads the database like an interrupted/restarted consumer.
    for _ in range(10):
        flow.step()
        if flow.q.job(job['id'])['state']=='completed': break
    assert flow.launched==['claude','codex']
    assert len(flow.sends)==1 and flow.sends[0][0]=='POST'
    assert flow.q.effects()[0]['state']=='confirmed'
    flow.step()
    assert len(flow.sends)==1
    assert flow.q.job(job['id'])['state']=='completed'


def human_turn(flow,text,*,mixed=False,automatic=False):
    import uuid
    record=flow.q.mr(11,82);session=record['chats'].get('codex')
    if not session:
        session=str(uuid.uuid4());record['chats']['codex']=session
        record['codex_context']={'cwd':flow.config['cwd'],'project_id':None,'roots':[flow.config['cwd']]}
        flow.chats[session]={'id':session,'cwd':flow.config['cwd'],'projectId':None,'status':{'type':'idle'}}
        flow.turns[session]=[]
        with flow.q.atomic(): flow.q.put_mr(record)
    turn=str(uuid.uuid4());source='source-'+turn
    flow.turns[session].insert(0,{'id':turn,'status':'completed'})
    flow.items[turn]=[{'type':'userMessage','id':source,'content':[{'type':'text','text':text}]}]
    if mixed: flow.items[turn].append({'type':'functionCallOutput','name':'gitlab_monitor_event'})
    if automatic:
        flow.items[turn][0]['clientId']=next(iter(flow.m['mq_all_stages'](flow.q)))['id']
    return {'origin':'human','provider':'codex','session':session,'turn_id':turn,'source_id':source,
        'texts':[text],'cwd':flow.config['cwd'],'project_id':None,'mixed':mixed,'automated':automatic}


def assessment(text,*,kind='action',anchor=None):
    return {'kind':kind,'text_basis':[text],'summary':'Responda e resolva o apontamento solicitado.',
            'scope':{'effects':['reply','resolve'],'discussions':['csp']},'question_anchor':anchor}


@pytest.mark.parametrize('render',[rendered,compact])
def test_real_human_after_completed_round_gets_new_fifo_job_without_code_checkpoint(flow,monkeypatch,render):
    previous=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    flow.drain();assert flow.q.job(previous['id'])['state']=='completed'
    text='responda na thread que a CSP foi corrigida e que o apontamento de memoização não procede, e marque como resolvida'
    source=human_turn(flow,text)
    if render is rendered:
        with flow.q.atomic():
            record=flow.q.mr(11,82);record['instruction_versions'][source['session']]=2;flow.q.put_mr(record)
    action=resolution_fixture(flow)
    result=domain(assessment=assessment(text),actions=[action])
    original_send=flow.m['mq_send']
    def send(api,method,route,payload):
        if method=='PUT':
            flow.sends.append((method,route,payload))
            for note in flow.context['threads'][0]['notes']:
                note.update(resolved=True,resolved_by={'id':7})
            return {}
        return original_send(api,method,route,payload)
    monkeypatch.setitem(flow.m,'mq_send',send)
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'human-final','phase':'final_answer','text':render(result)})
    flow.results.update(claude=result,codex=result)
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    jobs=flow.q.jobs();assert len(jobs)==2 and jobs[1]['kind']=='human' and jobs[1]['source']==source
    flow.drain()
    assert flow.launched==['claude','codex','claude','codex']
    assert flow.q.job(jobs[1]['id'])['state']=='completed'
    assert flow.q.mr(11,82)['reviewed_head']=='a'*40
    assert flow.q.job(previous['id'])['stages']==jobs[0]['stages']
    assert [method for method,_,_ in flow.sends]==['POST','PUT']
    assert all(e['state']=='confirmed' for e in flow.q.effects())
    assert flow.context['threads'][0]['notes'][0]['resolved']
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    assert len(flow.q.jobs())==2 and len(flow.sends)==2


@pytest.mark.parametrize('text,mixed',[('responda na thread?',False),('responda na thread w',False),('responda na thread',True)])
def test_native_questions_trailing_w_and_mixed_input_grant_no_job(flow,text,mixed):
    source=human_turn(flow,text,mixed=mixed)
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'a','phase':'final_answer','text':rendered(domain(assessment=assessment(text)))})
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    assert flow.q.jobs()==[] and flow.sends==[]


def test_source_change_and_foreign_chat_are_rejected(flow):
    source=human_turn(flow,'responda na thread')
    flow.m['mq_verify_source'](flow.config,flow.q,source,11,82)
    flow.items[source['turn_id']][0]['content'][0]['text']='different'
    with pytest.raises(RuntimeError,match='source changed'):
        flow.m['mq_verify_source'](flow.config,flow.q,source,11,82)
    with pytest.raises(RuntimeError,match='owned by this MR'):
        flow.m['mq_verify_source'](flow.config,flow.q,source,22,82)


def test_occupied_queue_preserves_new_human_source(flow):
    source=human_turn(flow,'responda na thread')
    first=flow.q.enqueue(11,90,source_key='busy',kind='code',head='a'*40,source={'origin':'automatic'},context={})
    flow.q.reserve({11})
    result=domain(assessment=assessment(source['texts'][0]))
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'a','phase':'final_answer','text':rendered(result)})
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    waiting=flow.q.jobs()[1]
    assert waiting['state']=='pending' and waiting['source']==source
    assert flow.q.reserve({11})['id']==first['id']
    assert flow.sends==[]


def test_singleton_lock_does_not_block_wake_enqueue(flow):
    descriptor=flow.m['mq_lock'](flow.config,'consumer')
    try:
        with pytest.raises(BlockingIOError): flow.m['mq_lock'](flow.config,'consumer')
        with flow.q.atomic(): flow.q.set_meta('wake',123)
        assert flow.q.meta('wake')==123
    finally:
        os.close(descriptor)


@pytest.mark.parametrize('render',[rendered,compact])
def test_question_hold_sufficient_answer_releases_only_its_original_anchor(flow,render):
    # Claude fails, Codex emits a real native question S; after the full barrier it holds.
    flow.results['claude']=RuntimeError('terminal error')
    flow.results['codex']=domain(outcome='question',question='Qual comportamento devo considerar na CSP?')
    original=flow.q.enqueue(11,82,source_key='code:held',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    flow.drain()
    held=flow.q.mr(11,82)['hold'];assert held and flow.launched==['claude','codex']
    assert flow.q.job(original['id'])['wait_reason']=='human'
    source=human_turn(flow,'considere a CSP atual e continue')
    if render is rendered:
        with flow.q.atomic():
            record=flow.q.mr(11,82);record['instruction_versions'][source['session']]=2;flow.q.put_mr(record)
    answer=domain(assessment=assessment(source['texts'][0],kind='answer',anchor='wrong question'))
    with pytest.raises(RuntimeError,match='exact sufficient-answer'):
        flow.m['mq_accept_answer'](flow.config,flow.q,flow.q.mr(11,82),source,answer)
    assert flow.q.mr(11,82)['hold']==held
    # Hold's automatic scope has no existing threads in this fixture; use finding-only bounded scope.
    answer['assessment']['question_anchor']=held['anchor']
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':render(answer)})
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    assert flow.q.mr(11,82)['hold']==held  # Registration alone never clears a hold.
    flow.results.update(claude=domain(),codex=domain())
    flow.drain()
    assert flow.q.mr(11,82)['hold'] is None
    assert flow.q.mr(11,82)['hold_history'][0]['answer']==source
    assert flow.q.job(original['id'])['state']=='completed'
    assert flow.launched==['claude','codex','claude','codex']


def test_question_first_reviewer_preserves_second_behind_human_hold(flow):
    flow.results['claude']=domain(outcome='question',question='Qual regra usar?')
    flow.q.enqueue(11,82,source_key='code:question',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    flow.drain()
    assert flow.launched==['claude']
    record=flow.q.mr(11,82)
    assert record['hold']['provider']=='claude'
    assert flow.q.jobs()[0]['state']=='pending'
    assert flow.q.effects()==[]


def test_automatic_copy_is_not_a_human_answer_and_cannot_clear_hold(flow):
    flow.results['codex']=domain(outcome='question',question='Qual regra usar?')
    flow.q.enqueue(11,82,source_key='code:q',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    held=flow.q.mr(11,82)['hold']
    source=human_turn(flow,'continue',automatic=True)
    result=domain(assessment=assessment('continue',kind='answer',anchor=held['anchor']))
    with pytest.raises(RuntimeError,match='automatic/mixed'):
        flow.m['mq_accept_answer'](flow.config,flow.q,flow.q.mr(11,82),source,result)
    assert flow.q.mr(11,82)['hold']==held and flow.sends==[]


def test_changed_head_invalidates_old_result_before_any_send(flow):
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    for _ in range(4): flow.step()
    assert flow.launched==['claude','codex']
    flow.context['head']='d'*40;flow.context['mr']['sha']='d'*40
    flow.step()
    assert flow.sends==[] and flow.q.mr(11,82)['reviewed_head'] is None
    flow.drain()
    assert flow.q.job(job['id'])['outcome']=='context changed; completed publications preserved'


@pytest.mark.parametrize('state',['closed','merged'])
def test_closed_or_merged_mr_never_starts_or_publishes(flow,state):
    flow.context['mr']['state']=state
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    flow.drain()
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.launched==[] and flow.sends==[] and flow.q.mr(11,82)['reviewed_head'] is None




def resolution_fixture(flow, *, bot=True):
    note={'id':5,'body':'CSP incorreta e memoização inválida','author':{'id':9},'system':False,
          'created_at':'2026-10-18T00:00:00Z','resolvable':True,'resolved':False}
    flow.context['threads']=[{'id':'csp','notes':[note]}]
    action={'key':'csp-fix','kind':'resolve','body':'A CSP foi corrigida; a memoização é um falso positivo.',
            'discussion':'csp','basis':'bot_false_positive','assessment':{'complete':True,'notes':[
                {'id':5,'revision':flow.m['monitor_digest'](note['body']),
                 'concerns':[{'disposition':'invalid','evidence':'O código usa o cache existente.'}]}]}}
    return action


def test_compound_reply_then_resolve_requires_exact_confirmed_explanation(flow,monkeypatch):
    action=resolution_fixture(flow)
    flow.results['codex']=domain(actions=[action])
    original_send=flow.m['mq_send']
    def send(api,method,route,payload):
        if method=='PUT':
            assert len(flow.sends)==1
            assert next(e for e in flow.q.effects() if e['kind']=='reply')['state']=='confirmed'
            flow.sends.append((method,route,payload))
            for note in flow.context['threads'][0]['notes']:
                note.update(resolved=True,resolved_by={'id':7})
            return {}
        return original_send(api,method,route,payload)
    monkeypatch.setitem(flow.m,'mq_send',send)
    flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    assert [method for method,_,_ in flow.sends]==['POST','PUT']
    assert all(e['state']=='confirmed' for e in flow.q.effects())
    assert flow.q.jobs()[0]['state']=='completed'


def test_new_concern_after_explanation_prevents_resolve(flow,monkeypatch):
    flow.results['codex']=domain(actions=[resolution_fixture(flow)])
    original_send=flow.m['mq_send']
    def send(api,method,route,payload):
        assert method=='POST','concurrent concern must veto resolution'
        result=original_send(api,method,route,payload)
        flow.context['threads'][0]['notes'].append({'id':999,'body':'Outra preocupação não analisada.',
            'author':{'id':10},'created_at':'2026-10-19T00:00:01Z','system':False,'resolvable':True,'resolved':False})
        return result
    monkeypatch.setitem(flow.m,'mq_send',send)
    flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    # Stop at the actual race; a subsequent pass would correctly require a new assessment.
    for _ in range(5): flow.step()
    assert [method for method,_,_ in flow.sends]==['POST']
    assert all(not n['resolved'] for n in flow.context['threads'][0]['notes'])
    assert flow.q.mr(11,82)['reviewed_head']=='a'*40 # First reviewer completed actual code review.
    assert flow.q.jobs()[0]['stages'][-1]['state']=='failed'
    assert 'context changed' in str(flow.model_errors[-1])


def test_unknown_public_delivery_readback_recovers_without_second_send(flow,monkeypatch):
    flow.results['codex']=domain(actions=[{'key':'answer','kind':'reply','body':'A CSP foi corrigida.','discussion':'csp'}])
    resolution_fixture(flow)
    original_send=flow.m['mq_send']
    def lost(api,method,route,payload):
        original_send(api,method,route,payload)
        raise TimeoutError('lost response after commit')
    monkeypatch.setitem(flow.m,'mq_send',lost)
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    assert flow.q.job(job['id'])['wait_reason']=='effect_unknown'
    assert len(flow.sends)==1 and flow.q.mr(11,82)['reviewed_head'] is None
    result=flow.m['mq_recover'](flow.config,job['id'])
    assert result['reconciled'] and len(flow.sends)==1
    flow.drain()
    saved=flow.q.job(job['id'])
    assert saved['wait_reason']=='reviewer_retry' and len(flow.sends)==1
    assert saved['review_attempt']['reviewers']==['codex']


def test_missing_public_readback_never_authorizes_resend(flow,monkeypatch):
    resolution_fixture(flow)
    flow.results['codex']=domain(actions=[{'key':'answer','kind':'reply','body':'CSP corrigida.','discussion':'csp'}])
    def uncertain(*args): raise TimeoutError('cannot know if remote committed')
    monkeypatch.setitem(flow.m,'mq_send',uncertain)
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    with pytest.raises(RuntimeError,match='remains unconfirmed'):
        flow.m['mq_recover'](flow.config,job['id'])
    assert flow.q.job(job['id'])['wait_reason']=='effect_unknown'
    assert flow.q.mr(11,82)['reviewed_head'] is None


def test_real_gitlab_http_transport_is_local_and_rejects_redirects(module,tmp_path,monkeypatch):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    m=module['mq_send'].__globals__;calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            calls.append((self.path,self.headers.get('PRIVATE-TOKEN'),json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            self.send_response(200);self.end_headers();self.wfile.write(b'{"id":10}')
        def do_GET(self):
            self.send_response(302);self.send_header('Location','http://unreachable.invalid/');self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    monkeypatch.setitem(m,'monitor_credential',lambda config:(f'http://127.0.0.1:{server.server_port}/api/v4','fixture-token'))
    api=m['MonitorGitLab']({'http_timeout':2,'max_response_bytes':1024})
    try:
        assert m['mq_send'](api,'POST','/projects/11/merge_requests/82/discussions',{'body':'fixture'})=={'id':10}
        assert calls==[('/api/v4/projects/11/merge_requests/82/discussions','fixture-token',{'body':'fixture'})]
        with pytest.raises(RuntimeError,match='HTTP 302'):
            api.get('/user')
        assert len(calls)==1
    finally:
        server.shutdown();server.server_close();worker.join(2)


def test_lost_native_ack_is_reconciled_without_second_codex_turn(flow,monkeypatch):
    original=flow.m['monitor_native'];lost=[True]
    def native(c,method,params,**kwargs):
        result=original(c,method,params,**kwargs)
        if method=='turn/start' and lost.pop():
            raise RuntimeError('lost acknowledgement after actual accepted input')
        return result
    monkeypatch.setitem(flow.m,'monitor_native',native)
    flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    assert flow.launched==['claude','codex']
    assert flow.q.jobs()[0]['state']=='completed'
    assert len(flow.turns[flow.q.mr(11,82)['chats']['codex']])==1


def test_interrupted_answer_is_interpreted_read_only_while_hold_remains(flow):
    flow.results['claude']=RuntimeError('failed')
    flow.results['codex']=domain(outcome='question',question='Qual regra usar?')
    original=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    hold=flow.q.mr(11,82)['hold']
    source=human_turn(flow,'use a regra atual e continue')
    # No native final: the interruption cannot silently lose this exact answer.
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    intake=flow.q.jobs()[1];assert intake['kind']=='intake'
    result=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
    result['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.results.update(claude=result,codex=result)
    for _ in range(5): flow.step()
    assert flow.q.job(intake['id'])['state']=='completed'
    assert flow.q.mr(11,82)['hold']==hold  # Registered sufficient answer is not an implicit release.
    assert flow.q.job(original['id'])['wait_reason']=='answer_ready'
    flow.results.update(claude=domain(),codex=domain())
    flow.drain()
    assert flow.q.mr(11,82)['hold'] is None
    assert flow.q.job(original['id'])['state']=='completed'
    assert flow.sends==[]


def test_cli_initialize_tick_and_status_leave_predecessor_untouched(flow):
    import json
    import subprocess
    import sys
    legacy=Path(flow.raw['state_file']);legacy.parent.mkdir(mode=0o700)
    legacy.write_bytes(b'untouched predecessor bytes')
    def cli(*args):
        process=subprocess.run([sys.executable,str(CLI),'monitor-gitlab','--config',str(flow.config_path),*args],
            text=True,capture_output=True,timeout=10)
        assert process.returncode==0,process.stderr
        return json.loads(process.stdout)
    assert cli('initialize')['initialized']
    assert cli('status')['parallel']==1
    assert legacy.read_bytes()==b'untouched predecessor bytes'
    descriptor=flow.m['mq_lock'](flow.config,'consumer')
    try:
        denied=subprocess.run([sys.executable,str(CLI),'monitor-gitlab','--config',str(flow.config_path),'serve','--once'],
            text=True,capture_output=True,timeout=10)
        assert denied.returncode==2 and 'invalid choice' in denied.stderr
        assert cli('tick')=={'cycle':'busy','writes_performed':False}
        assert cli('status')['parallel']==1
    finally:
        os.close(descriptor)


def test_unrelated_discussion_change_after_explanation_also_blocks_resolve(flow,monkeypatch):
    flow.results['codex']=domain(actions=[resolution_fixture(flow)])
    other={'id':44,'body':'Outro comentário original.','author':{'id':10},'created_at':'2026-10-19T00:00:00Z',
           'system':False,'resolvable':True,'resolved':False}
    flow.context['threads'].append({'id':'other','notes':[other]})
    original_send=flow.m['mq_send']
    def send(api,method,route,payload):
        assert method=='POST','a changed unrelated discussion also requires reassessment'
        result=original_send(api,method,route,payload)
        other['body']='Comentário editado durante a publicação.'
        return result
    monkeypatch.setitem(flow.m,'mq_send',send)
    flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    for _ in range(5): flow.step()
    assert len(flow.sends)==1 and flow.q.effects()[0]['state']=='confirmed'
    assert flow.q.jobs()[0]['stages'][-1]['state']=='failed'
    assert 'context changed' in str(flow.model_errors[-1])
    assert not flow.context['threads'][0]['notes'][0]['resolved']


def test_crash_after_native_question_result_recovers_same_hold_before_next_stage(flow,monkeypatch):
    question='Qual política de CSP devo usar?'
    flow.results['claude']=domain(outcome='question',question=question)
    flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    original=flow.m['mq_question']
    def crash(*args): raise InterruptedError('crash after terminal result commit')
    monkeypatch.setitem(flow.m,'mq_question',crash)
    flow.step()
    with pytest.raises(InterruptedError): flow.step()
    saved=flow.q.jobs()[0]
    assert saved['stages'][0]['result']['question']==question and flow.q.mr(11,82)['hold'] is None
    monkeypatch.setitem(flow.m,'mq_question',original)
    flow.drain()
    assert flow.q.mr(11,82)['hold']['question']==question
    assert flow.launched==['claude'] and flow.sends==[]


def test_crash_after_sufficient_answer_keeps_required_new_round(flow,monkeypatch):
    flow.results['codex']=domain(outcome='question',question='Qual regra usar?')
    job=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    hold=flow.q.mr(11,82)['hold'];source=human_turn(flow,'use a regra atual e continue')
    answer=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    flow.m['mq_accept_answer'](flow.config,flow.q,flow.q.mr(11,82),source,answer)
    original=flow.m['mq_reset_round']
    def crash(*args): raise InterruptedError('crash between answer and new execution')
    monkeypatch.setitem(flow.m,'mq_reset_round',crash)
    with pytest.raises(InterruptedError): flow.step()
    assert flow.q.job(job['id'])['needs_round_reset'] and flow.q.mr(11,82)['hold'] is None
    assert flow.q.mr(11,82)['reviewed_head'] is None
    monkeypatch.setitem(flow.m,'mq_reset_round',original)
    flow.results.update(claude=domain(),codex=domain());flow.drain()
    assert flow.launched==['claude','codex','claude','codex']
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.q.job(job['id'])['answers']==[source]




def test_readonly_answer_intake_cannot_bypass_uncertain_public_effect(flow):
    job=flow.q.enqueue(11,82,source_key='uncertain',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context))
    held=flow.q.reserve({11});flow.q.park(held,'effect_unknown')
    flow.q.enqueue(11,82,source_key='human',kind='intake',head='a'*40,
        source={'origin':'human','texts':['continue']},context=copy.deepcopy(flow.context))
    assert flow.q.reserve({11}) is None
    assert flow.q.job(job['id'])['wait_reason']=='effect_unknown'
    assert flow.launched==[] and flow.sends==[]


def test_terminal_consumer_io_failure_releases_slot_with_preserved_retry(flow,monkeypatch):
    first=flow.q.enqueue(11,82,source_key='one',kind='code',head='a'*40,source={'origin':'automatic'},context={})
    second=flow.q.enqueue(11,90,source_key='two',kind='code',head='b'*40,source={'origin':'automatic'},context={})
    flow.q.reserve({11})
    def failed(*args): raise RuntimeError('repository temporarily unavailable')
    monkeypatch.setitem(flow.m,'mq_step',failed)
    assert flow.m['mq_consume'](flow.config,flow.q) is True
    saved=flow.q.job(first['id'])
    assert saved['state']=='pending' and saved['wait_reason']=='retry' and saved['retry_at']>0
    assert flow.q.reserve({11})['id']==second['id']
    assert flow.sends==[]


def test_consumer_observation_failure_never_releases_unknown_native(flow,monkeypatch):
    first=flow.q.enqueue(11,82,source_key='one',kind='code',head='a'*40,source={'origin':'automatic'},context={})
    flow.q.enqueue(11,90,source_key='two',kind='code',head='b'*40,source={'origin':'automatic'},context={})
    active=flow.q.reserve({11});flow.q.stage_start(active,'claude','immutable original')
    def failed(*args): raise RuntimeError('cannot yet observe native execution')
    monkeypatch.setitem(flow.m,'mq_step',failed)
    assert flow.m['mq_consume'](flow.config,flow.q) is False
    assert flow.q.reserve({11})['id']==first['id']
    assert flow.q.job(first['id'])['state']=='running' and flow.sends==[]


def test_original_claude_question_session_can_answer_after_fresh_execution(flow):
    import json
    import uuid
    flow.results['claude']=domain(outcome='question',question='Qual regra de CSP devo usar?')
    original=flow.q.enqueue(11,82,source_key='code:a',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(flow.context));flow.drain()
    hold=flow.q.mr(11,82)['hold'];session_s=hold['session']
    # Another actual native input needs read-only interpretation. It creates fresh Claude T.
    source_b=human_turn(flow,'preciso explicar melhor a CSP')
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    flow.results.update(claude=domain(outcome='noop'),codex=domain(outcome='noop'))
    flow.drain()
    record=flow.q.mr(11,82)
    assert record['hold']==hold and session_s in record['claude_history']
    assert record['chats']['claude']!=session_s
    # The user answers in the original S, after T has been registered and completed.
    text='use a regra atual da CSP e continue';source_id=str(uuid.uuid4());anchor=str(uuid.uuid4())
    answer=domain(assessment=assessment(text,kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    target=next((Path(flow.config['claude_home'])/'projects').glob('*/'+session_s+'.jsonl'))
    rows=[{'type':'user','uuid':source_id,'parentUuid':hold['native_anchor'],'sessionId':session_s,
           'cwd':flow.config['cwd'],'message':{'content':text}},
          {'type':'assistant','uuid':anchor,'parentUuid':source_id,'sessionId':session_s,
           'message':{'id':'message-'+anchor,'stop_reason':'end_turn','content':[{'type':'text','text':compact(answer)}]}},
          {'type':'system','subtype':'turn_duration','uuid':str(uuid.uuid4()),'parentUuid':anchor,'sessionId':hold['session']}]
    with target.open('a') as stream:
        for row in rows: stream.write(json.dumps(row)+'\n')
    flow.m['mq_intake'](flow.config,flow.q,record)
    assert flow.q.mr(11,82)['hold']==hold
    assert flow.q.job(original['id'])['wait_reason']=='answer_ready'
    flow.results.update(claude=domain(),codex=domain());flow.drain()
    record=flow.q.mr(11,82)
    assert record['hold'] is None
    assert record['hold_history'][0]['answer']['session']==session_s
    assert record['hold_history'][0]['answer']['source_id']==source_id
    assert flow.q.job(original['id'])['state']=='completed' and flow.sends==[]
