"""Active reviewer tools: real queue, source authentication, journal and worker controls.

Only native transport and GitLab I/O are disposable providers. No production inference/writes.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import uuid

import pytest

from test_codex_gitlab_queue import module, flow, human_turn, resolution_fixture, compact, domain, assessment


@pytest.fixture
def active(flow):
    f=flow;f.legacy=False
    job=f.q.enqueue(11,82,source_key='tools',kind='code',head=f.context['head'],
        source={'origin':'automatic','head':f.context['head']},context=copy.deepcopy(f.context),reviewers=['codex','claude'])
    f.m['mq_step'](f.config,f.q)
    f.job=job['id'];stage=f.q.job(f.job)['stages'][-1]
    f.turns[stage['session']][0]['status']='inProgress'
    f.items[stage['turn_id']]=[i for i in f.items[stage['turn_id']] if i['type']=='userMessage']
    def call(name,**arguments):
        job=f.q.job(f.job);stage=job['stages'][-1]
        config=f.m['mq_workspace_config'](f.config,job)
        meta={'threadId':stage['session'],'sessionId':stage['session'],'callId':'call-'+str(uuid.uuid4()),
            'x-codex-turn-metadata':{'thread_id':stage['session'],'session_id':stage['session'],'turn_id':stage['turn_id']}}
        return f.m['mq_tool_execute'](config,f.q,job,stage,meta,name,arguments)
    f.call=call
    def terminal(*,error=None,text='Revisão concluída; validação estática. Não executei testes.'):
        stage=f.q.job(f.job)['stages'][-1]
        f.turns[stage['session']][0].update(status='failed' if error else 'completed',error=error)
        f.items[stage['turn_id']].append({'type':'agentMessage','id':'final-'+stage['turn_id'],
            'phase':'final_answer','text':text})
        return f.m['mq_step'](f.config,f.q)
    f.terminal=terminal
    return f


def test_inline_is_confirmed_before_second_reviewer_and_readable_final(active):
    f=active;f.call('read_mr')
    result=f.call('publish_finding',body='[P2] Subtraia o desconto.',path='x.py',line=1)
    assert result['state']=='confirmed' and len(f.sends)==1
    assert f.launched==['codex'] and f.q.job(f.job)['stages'][0]['state']=='running'
    assert f.q.mr(11,82)['reviewed_head'] is None
    f.call('finish_review');f.terminal()
    assert f.q.job(f.job)['stages'][0]['state']=='succeeded'
    f.m['mq_step'](f.config,f.q)
    assert f.launched==['codex','claude'] and f.context['threads'][0]['notes'][0]['body'].startswith('[P2]')
    assert '```csm-review' not in f.m['mq_instructions']()


def test_same_line_different_defects_and_exact_retry(active):
    f=active;f.call('read_mr')
    first=f.call('publish_finding',body='Sinal incorreto.',path='x.py',line=1)
    assert f.call('publish_finding',body='Sinal incorreto.',path='x.py',line=1)['key']==first['key']
    second=f.call('publish_finding',body='Limite incorreto.',path='x.py',line=1)
    assert len(f.sends)==2 and first['discussion']!=second['discussion']
    assert len(f.q.effects())==2


@pytest.mark.parametrize('change',['input','mixed','question','foreign_turn','closed','merged','head','discussion'])
def test_active_source_and_context_changes_block_publication(active,change):
    f=active;f.call('read_mr');stage=f.q.job(f.job)['stages'][-1]
    if change=='input':f.items[stage['turn_id']][0]['content'][0]['text']='substituted'
    elif change=='mixed':f.items[stage['turn_id']].append({'type':'userMessage','id':'extra','content':[{'type':'text','text':'continue'}]})
    elif change=='question':
        f.items[stage['turn_id']][0]['content'][0]['text']='Pode revisar?'
    elif change=='foreign_turn':f.turns[stage['session']][0]['id']='foreign'
    elif change in {'closed','merged'}:f.context['mr']['state']=change
    elif change=='head':f.context['head']='d'*40
    else:f.context['mr']['description']='changed description'
    with pytest.raises(RuntimeError):f.call('publish_finding',body='Defeito.',path='x.py',line=1)
    assert not f.sends and not f.q.effects()


@pytest.mark.parametrize('change',['session','epoch','state','hold','intake','automatic_as_human'])
def test_ownership_holds_and_human_scope_are_not_bypassed(active,change):
    f=active;f.call('read_mr');job=f.q.job(f.job)
    with f.q.atomic():
        if change=='session':job['stages'][-1]['session']='foreign'
        elif change=='state':job['stages'][-1]['state']='failed'
        elif change=='epoch':job['stages'][-1]['protocol']='stale'
        elif change=='hold':
            record=f.q.mr(11,82);record['hold']={'job_id':f.job,'anchor':'original'};f.q.put_mr(record)
        elif change=='intake':job['kind']='intake'
        else:
            job['source']={'origin':'human','provider':'codex','session':job['stages'][0]['session'],
                'turn_id':job['stages'][0]['turn_id'],'texts':[job['stages'][0]['input']],
                'source_id':'source-'+job['stages'][0]['turn_id'],'cwd':f.config['cwd'],'project_id':None}
            if change=='scope':job['scope']={'effects':['reply'],'discussions':['other']}
        f.q.save(job)
    with pytest.raises((RuntimeError,KeyError)):f.call('publish_finding',body='Defeito.',path='x.py',line=1)
    assert not f.sends


@pytest.mark.parametrize('outside',['operation','discussion'])
def test_authenticated_human_scope_denies_another_operation(active,outside):
    f=active;f.context['threads']=[{'id':'csp','notes':[]},{'id':'other','notes':[]}]
    f.call('read_mr');source=human_turn(f,'responda somente na thread CSP')
    f.m['mq_verify_source'](f.config,f.q,source,11,82)
    with f.q.atomic():
        job=f.q.job(f.job);job['source']=source;job['scope']={'effects':['reply'],'discussions':['csp']};f.q.save(job)
    with pytest.raises(RuntimeError,match='exceeds admitted human request scope'):
        if outside=='operation':f.call('publish_finding',body='Defeito.',path='x.py',line=1)
        else:f.call('reply',discussion='other',body='Fora do pedido.')
    assert not f.sends and not f.q.effects()
    assert f.call('reply',discussion='csp',body='Informação solicitada.')['state']=='confirmed'
    assert len(f.sends)==1


def test_finish_is_provisional_and_interruption_runs_next_without_checkpoint(active):
    f=active;f.call('read_mr');f.call('finish_review')
    assert f.q.mr(11,82)['reviewed_head'] is None
    f.terminal(error='interrupted')
    assert f.q.job(f.job)['stages'][0]['state']=='failed'
    f.m['mq_step'](f.config,f.q)
    assert f.launched==['codex','claude'] and f.q.mr(11,82)['reviewed_head'] is None


def test_question_fences_now_and_requires_actual_native_anchor(active):
    f=active;question='Qual comportamento devo considerar na CSP?'
    f.call('read_mr');f.call('ask_human',question=question)
    with pytest.raises(RuntimeError,match='fences'):f.call('publish_finding',body='Defeito.',path='x.py',line=1)
    assert f.q.mr(11,82)['hold'] is None
    f.terminal(text=question)
    hold=f.q.mr(11,82)['hold']
    assert hold['question']==question and hold['native_anchor'].startswith('final-')
    f.m['mq_step'](f.config,f.q)
    assert f.q.job(f.job)['wait_reason']=='human' and f.launched==['codex']


def test_interrupted_question_preserves_fence_and_uses_readonly_continuation(active):
    f=active;f.call('ask_human',question='Qual regra usar?');f.terminal(error='interrupted')
    pending=f.q.job(f.job)['pending_question'];assert pending['question']=='Qual regra usar?'
    assert f.q.mr(11,82)['hold'] is None
    f.m['mq_step'](f.config,f.q)
    job=f.q.job(f.job);stage=job['stages'][-1]
    assert stage['purpose']=='question' and f.m['mq_workspace_config'](f.config,job)['_workspace_write'] is False
    assert f.q.next_reviewer(job) is None # native presentation still running, retains capacity
    assert len(job['stages'])==2 and f.launched==['codex','codex']


def test_crash_after_question_failure_recovers_fence_once(active,monkeypatch):
    f=active;f.call('ask_human',question='Qual regra usar?')
    restore=f.m['mq_restore_question']
    def crash(*args):raise OSError('crash before question handoff')
    monkeypatch.setitem(f.m,'mq_restore_question',crash)
    with pytest.raises(OSError,match='handoff'):f.terminal(error='interrupted')
    assert f.q.job(f.job)['stages'][0]['state']=='failed'
    assert not f.q.job(f.job).get('pending_question')
    monkeypatch.setitem(f.m,'mq_restore_question',restore)
    reopened=f.m['MonitorQueue'](f.config)
    try:
        f.m['mq_step'](f.config,reopened)
        assert reopened.job(f.job)['pending_question']['question']=='Qual regra usar?'
        f.step(reopened);f.step(reopened)
        assert reopened.mr(11,82)['hold']['question']=='Qual regra usar?'
        assert not reopened.job(f.job).get('pending_question')
        f.step(reopened)
        assert reopened.job(f.job)['wait_reason']=='human' and f.launched==['codex','codex']
    finally:reopened.close()


def test_legacy_completed_proposals_are_archived_never_replayed(flow):
    f=flow
    job=f.q.enqueue(11,82,source_key='legacy',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context),reviewers=['codex'])
    job=f.q.reserve({11});stage=f.q.stage_start(job,'codex','old issued input')
    result={'outcome':'complete','head':'a'*40,'actions':[{'kind':'finding','body':'old unverified proposal'}]}
    f.q.stage_end(job,stage['id'],result=result,terminal=True)
    f.m['mq_step'](f.config,f.q)
    saved=f.q.job(job['id'])
    assert saved['protocol']=='tools' and saved['rounds'][0]['stages'][0]['result']==result
    assert saved['stages'][0]['protocol']=='tools' and f.launched==['codex']
    assert not f.sends and f.q.mr(11,82)['reviewed_head'] is None


def test_recorded_mr13_uncertainty_is_history_and_new_question_gets_native_anchor(flow):
    f=flow;artifact=json.loads((Path(__file__).parent/'fixtures/gitlab-agent-tools-cutover.json').read_text())
    assert artifact['uncertainty']['last_error']=='unresolved reviewer disagreement requires a human decision'
    job=f.q.enqueue(11,82,source_key='recorded-uncertainty',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context),reviewers=['codex'])
    job=f.q.reserve({11});stage=f.q.stage_start(job,'codex','old issued input')
    f.q.stage_end(job,stage['id'],result={'outcome':'complete','head':'a'*40,
        'dispositions':artifact['uncertainty']['dispositions']},terminal=True)
    f.results['codex']={'outcome':'question','question':'Qual fluxo de autenticação é o esperado?'}
    f.drain();saved=f.q.job(job['id'])
    assert saved['rounds'][0]['stages'][0]['result']['dispositions']==artifact['uncertainty']['dispositions']
    assert saved['wait_reason']=='human' and not f.sends
    hold=f.q.mr(11,82)['hold']
    assert hold['question']==f.results['codex']['question'] and hold['native_anchor'].startswith('final-')


def test_recorded_mr18_unknown_send_blocks_cutover_without_confirmation(flow):
    f=flow;artifact=json.loads((Path(__file__).parent/'fixtures/gitlab-agent-tools-cutover.json').read_text())
    job=f.q.enqueue(11,82,source_key='recorded-unknown',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context),reviewers=['codex'])
    job=f.q.reserve({11});effect={**artifact['unknown_effect'],'job_id':job['id']}
    with f.q.atomic():f.q.put_effect(effect)
    f.m['mq_step'](f.config,f.q)
    assert f.q.job(job['id'])['wait_reason']=='effect_unknown' and not f.launched
    assert f.m['mq_reconcile_effects'](f.config,f.q,f.q.job(job['id'])) is False
    assert f.q.effect(effect['key'])==effect and not f.sends


def test_legacy_question_is_restored_before_cutover_or_next_reviewer(active,monkeypatch):
    f=active;f.call('ask_human',question='Qual regra usar?')
    restore=f.m['mq_restore_question']
    monkeypatch.setitem(f.m,'mq_restore_question',lambda *args:None)
    f.terminal(text='Qual regra usar?')
    with f.q.atomic():
        job=f.q.job(f.job);job.pop('protocol');job['stages'][0].pop('protocol');f.q.save(job)
    monkeypatch.setitem(f.m,'mq_restore_question',restore)
    f.m['mq_step'](f.config,f.q)
    assert f.q.mr(11,82)['hold']['question']=='Qual regra usar?'
    f.m['mq_step'](f.config,f.q)
    assert f.q.job(f.job)['wait_reason']=='human' and f.launched==['codex']


@pytest.mark.parametrize('delivered',[False,True])
def test_unknown_send_keeps_capacity_then_parks_and_readback_never_resends(active,monkeypatch,delivered):
    f=active;f.call('read_mr');send=f.m['mq_send']
    def lost(*args):
        if delivered:send(*args)
        raise OSError('lost response')
    monkeypatch.setitem(f.m,'mq_send',lost)
    with pytest.raises(OSError):f.call('publish_finding',body='Defeito.',path='x.py',line=1)
    assert f.q.job(f.job)['state']=='running' and f.q.effects()[0]['state']=='unknown'
    with pytest.raises(RuntimeError,match='fences'):f.call('publish_finding',body='Defeito.',path='x.py',line=1)
    f.terminal();f.m['mq_step'](f.config,f.q)
    assert f.q.job(f.job)['wait_reason']=='effect_unknown' and f.launched==['codex']
    later=f.q.enqueue(11,83,source_key='later',kind='code',head='a'*40,source={'origin':'automatic'},context=f.context)
    assert f.q.reserve({11})['id']==later['id']
    context=f.m['mq_context']
    def mr_context(config,iid,**kwargs):
        value=context(config,iid,**kwargs)
        if iid==83:
            value=copy.deepcopy(value);value['iid']=83;value['mr']['iid']=83
        return value
    monkeypatch.setitem(f.m,'mq_context',mr_context)
    f.drain()
    assert f.q.job(later['id'])['state']=='completed'
    job=f.q.job(f.job)
    assert f.m['mq_reconcile_effects'](f.config,f.q,job) is delivered
    assert len(f.sends)==int(delivered)
    assert f.q.job(f.job)['stages'][0]['state']=='failed'
    if delivered:
        assert f.q.job(f.job)['wait_reason'] is None
        assert f.q.next_reviewer(f.q.job(f.job))=='claude'
        f.drain()
        assert f.q.job(f.job)['wait_reason']=='reviewer_retry'
        assert f.q.job(f.job)['review_attempt']['reviewers']==['codex']
        assert f.launched==['codex','claude','codex','claude'] and len(f.sends)==1


@pytest.mark.parametrize('answer_first',[False,True])
def test_uncertain_send_question_and_sufficient_answer_resume_after_readback(active,monkeypatch,answer_first):
    f=active;f.call('read_mr');send=f.m['mq_send']
    def lost(*args):send(*args);raise OSError('lost acknowledgment')
    monkeypatch.setitem(f.m,'mq_send',lost)
    with pytest.raises(OSError):f.call('publish_finding',body='Defeito.',path='x.py',line=1)
    f.call('ask_human',question='Qual regra usar?');f.terminal(text='Qual regra usar?')
    f.m['mq_step'](f.config,f.q)
    assert f.q.job(f.job)['wait_reason']=='effect_unknown'
    hold=f.q.mr(11,82)['hold']
    def answer():
        source=human_turn(f,'use a regra atual e continue')
        result=domain(assessment=assessment(source['texts'][0],kind='answer',anchor=hold['anchor']))
        result['assessment']['scope']={'effects':['finding'],'discussions':[]}
        f.items[source['turn_id']].append({'type':'agentMessage','id':'answer','phase':'final_answer','text':compact(result)})
        f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    if answer_first:answer()
    assert f.m['mq_reconcile_effects'](f.config,f.q,f.q.job(f.job))
    assert f.q.job(f.job)['wait_reason']==('answer_ready' if answer_first else 'human')
    if not answer_first:answer()
    monkeypatch.setitem(f.m,'mq_send',send)
    f.drain()
    assert f.q.mr(11,82)['hold'] is None and f.q.job(f.job)['state']=='completed'
    assert f.launched==['codex','codex','claude'] and len(f.sends)==1


def test_resolution_requires_complete_read_and_explains_before_resolving(active,monkeypatch):
    f=active;resolution_fixture(f)
    send=f.m['mq_send']
    def publish(api,method,route,payload):
        if method!='PUT':return send(api,method,route,payload)
        assert len(f.sends)==1 and f.q.effects()[0]['state']=='confirmed'
        f.sends.append((method,route,payload))
        for n in f.context['threads'][0]['notes']:n.update(resolved=True,resolved_by={'id':7})
    monkeypatch.setitem(f.m,'mq_send',publish)
    f.call('read_mr')
    args={'discussion':'csp','explanation':'A CSP foi corrigida no head analisado.',
        'basis':'verified_fix','notes':[{'note':1,'status':'fixed','evidence':'A diretiva agora permite a origem correta.'}]}
    with pytest.raises(RuntimeError,match='complete current discussion'):f.call('resolve',**args)
    discussion=f.call('read_discussion',discussion='csp')
    args['notes'][0]['note']=discussion['notes'][0]['id']
    result=f.call('resolve',**args)
    assert result['resolved'] is True and [s[0] for s in f.sends]==['POST','PUT']
    assert f.call('resolve',**args)['resolved'] is True and len(f.sends)==2


def test_extra_human_concern_after_explanation_blocks_resolution(active,monkeypatch):
    f=active;resolution_fixture(f);discussion=f.call('read_discussion',discussion='csp')
    send=f.m['mq_send']
    def race(*args):
        assert args[1]=='POST';result=send(*args)
        f.context['threads'][0]['notes'].append({'id':999,'body':'Outra preocupação.',
            'author':{'id':10},'created_at':'2026-10-19T00:00:01Z','system':False,'resolvable':True,'resolved':False})
        return result
    monkeypatch.setitem(f.m,'mq_send',race)
    with pytest.raises(RuntimeError,match='context changed'):
        f.call('resolve',discussion='csp',explanation='Correção verificada.',basis='verified_fix',
            notes=[{'note':discussion['notes'][0]['id'],'status':'fixed','evidence':'Código corrigido.'}])
    assert len(f.sends)==1 and f.q.effects()[0]['state']=='confirmed'


def test_human_assessment_is_small_and_original_text_is_bound(active):
    f=active;source=human_turn(f,'responda na thread que a CSP foi corrigida e que o apontamento de memoização não procede, e marque como resolvida')
    value={'kind':'action','summary':'Responder e resolver CSP/memoização.',
        'effects':['reply','resolve'],'discussions':['csp','memo'],'question_anchor':None}
    result=f.m['mq_parse_assessment']('```csm-assessment\n'+json.dumps(value)+'\n```',f.q.job(f.job),source)
    assert f.m['mq_human_assessment'](result,source)=={'effects':['reply','resolve'],'discussions':['csp','memo']}
    for text in ('Pode responder?','responda w'):
        changed={**source,'texts':[text]}
        with pytest.raises(RuntimeError):f.m['mq_human_assessment'](result,changed)


@pytest.mark.parametrize('legacy',[False,True])
def test_new_chat_rejects_legacy_assessment_but_compact_assessment_admits(flow,legacy):
    from test_codex_gitlab_queue import rendered
    f=flow
    first=f.q.enqueue(11,82,source_key='first',kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context))
    f.drain();assert f.q.job(first['id'])['state']=='completed'
    source=human_turn(f,'responda na thread CSP')
    result=domain(assessment=assessment(source['texts'][0]))
    f.items[source['turn_id']].append({'type':'agentMessage','id':'response','phase':'final_answer',
        'text':(rendered if legacy else compact)(result)})
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.jobs()[-1]['kind']==('intake' if legacy else 'human')
    assert f.q.jobs()[-1]['prepared']==(None if legacy else f.m['mq_parse_assessment'](compact(result),f.context,source))
    assert not f.sends


def test_tick_lock_does_not_block_tools_but_work_lock_does(active):
    f=active;lock=f.m['mq_lock'](f.config,'consumer')
    try:assert f.call('read_mr')['head']=='a'*40
    finally:os.close(lock)
    lock=f.m['mq_lock'](f.config,'work')
    try:
        assert f.m['mq_consume'](f.config,f.q) is False
        with pytest.raises(BlockingIOError):f.m['mq_lock'](f.config,'work')
    finally:os.close(lock)


@pytest.mark.parametrize('filename',['x.py','[slug].py'])
def test_omitted_diff_uses_exact_local_objects_without_checkout(active,tmp_path,filename):
    f=active;root=Path(f.config['cwd'])/'repository';root.mkdir()
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    git('init','-q');git('config','user.email','fixture@example.invalid');git('config','user.name','Fixture')
    (root/filename).write_text('old\n');(root/'s.py').write_text('old decoy\n')
    git('add','.');git('commit','-qm','base');base=git('rev-parse','HEAD')
    (root/filename).write_text('new\n');(root/'s.py').write_text('decoy\nsecond\n')
    git('commit','-qam','head');head=git('rev-parse','HEAD')
    context=copy.deepcopy(f.context);context['head']=head
    context['mr']['diff_refs']={'base_sha':base,'start_sha':base,'head_sha':head}
    context['diff'].update(base_commit_sha=base,start_commit_sha=base,head_commit_sha=head)
    context['diff']['diffs'][0].update(diff='',collapsed=True,old_path=filename,new_path=filename)
    config=f.m['mq_workspace_config'](f.config,f.q.job(f.job))
    position=f.m['mq_tool_position'](config,context,filename,1,'new',str(root))
    assert position['head_sha']==head and position['base_sha']==base and position['new_line']==1
    with pytest.raises(RuntimeError,match='outside the authenticated diff'):
        f.m['mq_tool_position'](config,context,filename,2,'new',str(root))
    assert git('rev-parse','HEAD')==head and git('status','--porcelain')==''
    context['mr']['diff_refs']['base_sha']='f'*40
    with pytest.raises(RuntimeError,match='authenticated MR refs'):
        f.m['mq_tool_position'](config,context,filename,1,'new',str(root))


def test_real_stdio_sdk_registers_only_review_tools_and_rejects_stale_binding(active):
    import asyncio
    import sys
    from mcp import ClientSession, StdioServerParameters, stdio_client
    f=active;job=f.q.job(f.job);stage=job['stages'][-1]
    async def probe():
        params=StdioServerParameters(command=sys.executable,args=[f.m['__file__'],'monitor-gitlab',
            '--config',str(f.config_path),'tools','--job',f.job,'--stage',stage['id'],'--epoch','foreign'])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=(await session.list_tools()).tools
                assert {t.name for t in tools}==set(f.m['MQ_TOOLS'])
                assert all('ctx' not in t.input_schema.get('properties',{}) for t in tools)
                result=await session.call_tool('finish_review',{})
                assert result.is_error and 'stale tool launch binding' in str(result.content)
    asyncio.run(probe())
    assert f.q.job(f.job)['stages'][0].get('finish_intent') is None and not f.sends
