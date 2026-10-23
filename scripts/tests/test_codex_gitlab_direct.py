"""Direct publication uses native tools; queue/results retain their actual identities."""
import copy
import json
from pathlib import Path

import pytest
from test_codex_gitlab_queue import module, flow, domain, human_turn, assessment


def automatic(f,reviewers=None):
    return f.q.enqueue(11,82,source_key='direct-code',kind='code',head='a'*40,
        source={'origin':'automatic','head':'a'*40},context=copy.deepcopy(f.context),reviewers=reviewers)


@pytest.mark.parametrize('version',['v1','v2'])
@pytest.mark.parametrize('mutation',[None,'text','context','version'])
def test_captured_original_message_stays_on_its_original_reader(flow,mutation,version):
    stage=json.loads((Path(__file__).parent/('fixtures/gitlab-message-'+version+'.json')).read_text())
    if mutation=='text':stage['input']+=' forged'
    if mutation=='context':stage['input_context']['head']='b'*40
    if mutation=='version':stage['input_format']='message-v99'
    if mutation:
        with pytest.raises(RuntimeError,match='immutable reviewer input'):flow.m['mq_input_context'](flow.q,stage)
    else:
        assert flow.m['mq_input_context'](flow.q,stage)==stage['input_context']
        assert stage['input_format']=='message-'+version


@pytest.mark.parametrize('text',[
    '```text\nEstado da revisão: concluída\nCommit revisado: '+'a'*40,
    '~~~\nEstado da revisão: concluída\nCommit revisado: '+'a'*40,
    '````\nEstado da revisão: concluída\nCommit revisado: '+'a'*40+'\n```',
    'No status', '> Estado da revisão: concluída\nCommit revisado: '+'a'*40,
    '```text\nEstado da revisão: concluída\nCommit revisado: '+'a'*40+'\n```',
    'Estado da revisão: concluída\nEstado da revisão: concluída\nCommit revisado: '+'a'*40,
    'Estado da revisão: concluída', 'Estado da revisão: aguardando resposta\n',
])
def test_native_final_requires_unquoted_unambiguous_status_and_code_head(flow,text):
    job=automatic(flow)
    with pytest.raises(RuntimeError):
        flow.m['mq_direct_result'](job,{}, {'text':text,'anchor':'actual-final'})


def test_different_reviewed_head_never_advances_admitted_checkpoint(flow):
    job=automatic(flow)
    flow.results.update(claude=domain(),codex=domain())
    flow.results['codex']['head']='b'*40
    flow.drain()
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.q.mr(11,82)['reviewed_head'] is None
    assert not flow.q.effects()


@pytest.mark.parametrize('context_change',['head','closed','merged'])
def test_operational_context_change_settles_without_a_human_question(flow,context_change):
    job=automatic(flow,reviewers=['codex']);flow.step()
    if context_change=='head':flow.context['head']='b'*40
    else:flow.context['mr']['state']=context_change
    flow.drain()
    assert flow.q.job(job['id'])['state']=='completed'
    assert flow.q.mr(11,82)['hold'] is None
    assert flow.q.mr(11,82)['reviewed_head'] is None


def test_new_stage_uses_normal_gitlab_without_private_server(flow):
    job=automatic(flow);flow.step();saved=flow.q.job(job['id']);stage=saved['stages'][0]
    c=flow.m['mq_workspace_config'](flow.config,saved)
    selection=flow.m['mq_native_selection'](c)['config']
    assert stage['protocol']=='direct' and stage['input_format']=='message-v3'
    assert 'gitlab_review' not in stage['input'] and 'Exact admitted head:' not in stage['input']
    assert 'mcp_servers.gitlab_review' not in selection
    server=selection['mcp_servers.gitlab']
    assert set(flow.m['MQ_GITLAB_WRITES'])<=set(server['enabled_tools'])
    assert all(server['tools'][n]['approval_mode']=='approve' for n in flow.m['MQ_GITLAB_WRITES'])
    assert 'merge_merge_request' not in server['enabled_tools']
    readonly=flow.m['mq_native_selection']({**c,'_workspace_write':False})['config']['mcp_servers.gitlab']
    assert not set(flow.m['MQ_GITLAB_WRITES']) & set(readonly['enabled_tools'])
    command=next(c for c in flow.service.commands if c[0]=='systemd-run')
    assert 'fixture-only' not in ' '.join(command)
    private=Path(command[command.index('--mcp-config')+1])
    assert private.stat().st_mode & 0o777==0o600
    assert json.loads(private.read_text())['mcpServers']['gitlab']['headers']['Private-Token']=='fixture-only'


def test_shared_instructions_require_peer_and_whole_thread_review(module):
    text=module['mq_instructions']()
    for requirement in ('other reviewer','every note','explain','no valid concern','different defects',
                        'uncertain sends','closed','same concern'):
        assert requirement in text
    assert 'call finish_review' not in text and 'gitlab_review' not in text


def test_question_scope_includes_thread_created_by_previous_reviewer(flow):
    flow.results['claude']=domain(actions=[{'kind':'finding','body':'First concern','key':'one'}])
    flow.results['codex']=domain(outcome='question',question='Qual regra deve valer nesta discussão?')
    job=automatic(flow);flow.drain()
    hold=flow.q.mr(11,82)['hold'];thread=flow.context['threads'][0]['id']
    assert thread in hold['scope']['discussions']
    saved=flow.q.job(job['id']);assert saved['stages'][-1]['question_context']['threads'][0]['id']==thread
    reopened=flow.m['MonitorQueue'](flow.config)
    try:assert reopened.mr(11,82)['hold']==hold
    finally:reopened.close()


def test_question_snapshot_failure_preserves_final_and_blocks_only_same_mr(flow,monkeypatch):
    flow.results['codex']=domain(outcome='question',question='Qual regra vale?')
    job=automatic(flow,reviewers=['codex']);flow.step()
    original=flow.m['mq_context']
    monkeypatch.setitem(flow.m,'mq_context',lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('read failed')))
    with pytest.raises(RuntimeError,match='read failed'):flow.step()
    saved=flow.q.job(job['id'])
    assert saved['wait_reason']=='question_scope' and saved['question_scope_pending']
    assert saved['stages'][0]['result']['question']=='Qual regra vale?'
    assert flow.q.mr(11,82)['hold'] is None
    later=flow.q.enqueue(11,82,source_key='later',kind='human',head='a'*40,source={'origin':'human'},context={})
    other=flow.q.enqueue(11,83,source_key='other',kind='discussion',head='a'*40,source={'origin':'automatic'},context={})
    reserved=flow.q.reserve({11});assert reserved['id']==other['id']
    flow.q.finish(reserved,'fixture other settled')
    with flow.q.atomic():saved['retry_at']=0;flow.q.save(saved)
    monkeypatch.setitem(flow.m,'mq_context',original);flow.drain()
    assert flow.q.mr(11,82)['hold']['question']=='Qual regra vale?'
    assert flow.q.job(later['id'])['state']=='pending'


def test_old_preparation_retirement_preserves_success_and_retry_boundary(flow):
    job=automatic(flow);job=flow.q.reserve({11})
    old=flow.q.stage_start(job,'claude','first');flow.q.stage_end(job,old['id'],result=domain(),terminal=True)
    stage=flow.q.stage_start(job,'codex','old unused');stage['protocol']='tools'
    with flow.q.atomic():flow.q.save(job)
    flow.q.retire_preparation(job,stage)
    assert flow.q.next_reviewer(job)=='codex' and job['stages']==[old]
    assert job['retired_preparations'][0]['id']==stage['id']
    assert stage['id'] in {s['id'] for s in flow.m['mq_all_stages'](flow.q)}
    with pytest.raises(RuntimeError):flow.q.retire_preparation(job,stage)


@pytest.mark.parametrize('delivery',['sending','accepted'])
def test_unknown_old_delivery_cannot_be_retired(flow,delivery):
    job=automatic(flow);job=flow.q.reserve({11});stage=flow.q.stage_start(job,'claude','old')
    stage.update(protocol='tools',delivery=delivery)
    with flow.q.atomic():flow.q.save(job)
    before=copy.deepcopy(job)
    with pytest.raises(RuntimeError,match='non-issue'):flow.q.retire_preparation(job,stage)
    assert flow.q.job(job['id'])==before


def test_legacy_completion_still_requires_its_original_signal(flow):
    job=automatic(flow);stage={'protocol':'tools'}
    observed={'text':'Original readable summary','anchor':'final','turn_id':'original','source_id':'source'}
    assert flow.m['mq_tool_result'](flow.q,job,stage,observed)[0] is None
    stage['finish_intent']={'identity':{'turn_id':'original','source_id':'source','call_id':'call'}}
    assert flow.m['mq_tool_result'](flow.q,job,stage,observed)[0]['outcome']=='complete'
    observed['turn_id']='foreign'
    assert flow.m['mq_tool_result'](flow.q,job,stage,observed)[0] is None


def test_inventory_race_retires_only_proved_self_activity(flow,monkeypatch):
    f=flow
    class API:
        def __init__(self,*a):pass
        def project(self):return {'id':11}
        def pages(self,*a,**kw):yield [{'iid':82}],True
    monkeypatch.setitem(f.m,'MonitorGitLab',API)
    with f.q.atomic():
        record=f.q.mr(11,82);record.update(observed_head='a'*40,observed_notes=f.m['monitor_digest']([]),
            observed_note_versions=[]);f.q.put_mr(record)
    f.results['codex']=domain(actions=[{'kind':'finding','key':'one','body':'Real fixture concern'}])
    job=automatic(f,reviewers=['codex']);f.step() # Send is visible; result collection has not happened.
    f.m['mq_inventory'](f.config,f.q)
    pending=next(j for j in f.q.jobs('pending') if j['kind']=='discussion')
    active=f.q.job(job['id']);stage=active['stages'][0]
    f.m['mq_observe_outputs'](f.m['mq_workspace_config'](f.config,active),f.q,active,stage)
    assert f.q.job(pending['id'])['outcome']=='self-only discussion activity; not reviewed'
    f.m['mq_inventory'](f.config,f.q)
    assert len(f.q.jobs())==2
    # A human edit under the same account remains eligible and never inherits tool provenance.
    note=f.context['threads'][0]['notes'][0]
    note.update(body='Human edit by the same account',updated_at='2026-10-20T00:00:00Z')
    f.m['mq_inventory'](f.config,f.q)
    assert len(f.q.jobs('pending'))==1
    assert f.q.jobs('pending')[0]['kind']=='discussion'
    assert f.q.mr(11,82)['reviewed_head'] is None


def test_mr78_partial_native_artifact_no_longer_requires_a_private_reader(flow):
    artifact=json.loads((Path(__file__).parent/'fixtures/gitlab-direct-mr78.json').read_text())
    assert artifact['capture_kind']=='partial-authenticated-native-artifact'
    assert artifact['read_error']=='Error executing tool read_mr: MR head changed or MR is closed/merged'
    assert 'read_mr' in artifact['final_question'] and 'gitlab_review' in artifact['old_task_prefix']
    # Replay only the captured terminal-signal boundary, then exercise the new route synthetically.
    original={'repository_id':11,'iid':78,'head':artifact['head'],'kind':'code'}
    observed={'text':artifact['final_question'],'anchor':artifact['final_id'],
        'turn_id':artifact['turn_id'],'source_id':artifact['registered_source_id']}
    stage={'question_intent':artifact['native_signal']}
    result,error=flow.m['mq_tool_result'](flow.q,original,stage,observed)
    assert error is None and result['question']==artifact['final_question']
    assert flow.m['mq_tool_result'](flow.q,original,stage,{**observed,'turn_id':'foreign'})[0] is None
    job=automatic(flow,reviewers=['codex']);flow.step()
    stage=flow.q.job(job['id'])['stages'][0]
    assert 'read_mr' not in stage['input'] and 'admitted head' not in stage['input']
    assert 'Head changes, closed MRs and transport failures are not human decisions' in flow.m['mq_instructions']()
    flow.context['head']='c'*40;flow.drain()
    assert flow.q.mr(11,82)['hold'] is None and flow.q.mr(11,82)['reviewed_head'] is None


@pytest.mark.parametrize('change',['source','server','repository','mr','error','missing_result'])
def test_own_output_filter_requires_exact_native_target_and_success(flow,change):
    f=flow;f.results['codex']=domain(actions=[{'kind':'finding','key':'one','body':'A real fixture issue'}])
    job=automatic(f,reviewers=['codex']);f.step();active=f.q.job(job['id']);stage=active['stages'][0]
    item=next(i for i in f.items[stage['turn_id']] if i.get('tool')=='create_merge_request_thread')
    if change=='source':f.items[stage['turn_id']][0]['clientId']='foreign'
    if change=='server':item['server']='different'
    if change=='repository':item['arguments']['project_id']='99'
    if change=='mr':item['arguments']['merge_request_iid']='99'
    if change=='error':item['error']={'message':'uncertain response'}
    if change=='missing_result':item['result']=None
    if change=='source':
        with pytest.raises(RuntimeError,match='native input changed'):
            f.m['mq_observe_outputs'](f.config,f.q,active,stage)
    else:f.m['mq_observe_outputs'](f.config,f.q,active,stage)
    assert not f.q.mr(11,82).get('own_outputs')
    assert len(f.context['threads'])==1 # A real fixture send exists, but is not presumed own activity.


def test_mixed_self_external_event_and_issued_work_survive_late_observation(flow):
    f=flow;own={'id':1,'discussion':'one','revision':'own','author_id':7,'resolved':False,
        'updated_at':'2026-10-22T00:00:00Z','resolved_at':None}
    external={**own,'id':2,'revision':'external'}
    record=f.q.mr(11,82);record['own_outputs']={f.m['monitor_digest'](own):None}
    def event(marker,rows):
        return f.q.enqueue(11,82,source_key=marker,kind='discussion',head='a'*40,
            source={'origin':'automatic','notes':marker,'note_delta':{'before':[],'after':rows}},context=f.context)
    mixed=event('mixed',[own,external])
    with f.q.atomic():f.q.put_mr(record);f.m['mq_retire_self_activity'](f.q,record)
    assert f.q.job(mixed['id'])['state']=='pending'
    running=f.q.reserve({11});f.q.finish(running,'fixture settled mixed')
    issued=event('own',[own]);issued=f.q.reserve({11});stage=f.q.stage_start(issued,'claude','registered')
    with f.q.atomic():f.m['mq_retire_self_activity'](f.q,record)
    assert f.q.job(issued['id'])['stages'][0]['id']==stage['id']
    assert f.q.job(issued['id'])['state']=='running'


def test_own_resolution_delta_is_filtered_but_later_external_edit_is_not(flow):
    before={'id':1,'discussion':'one','revision':'same','author_id':7,'resolved':False,
        'updated_at':'2026-10-22T00:00:00Z','resolved_at':None}
    after={**before,'resolved':True,'resolved_at':'2026-10-22T00:01:00Z'}
    own={flow.m['monitor_digest'](after):before}
    assert flow.m['mq_normalize_notes']([before],own)==flow.m['mq_normalize_notes']([after],own)
    edited={**after,'revision':'human edit','updated_at':'2026-10-22T00:02:00Z'}
    assert flow.m['mq_normalize_notes']([before],own)!=flow.m['mq_normalize_notes']([edited],own)


def test_supplied_constraints_are_preserved_when_generated_head_line_is_removed(module):
    data=json.loads((Path(__file__).parent/'fixtures/gitlab-message-v1.json').read_text())['input_context']
    constraint='Exact admitted head: '+'b'*40+'\nFor a review call finish_review is quoted context here.'
    data['original_source']={'origin':'human','texts':[constraint]}
    data['answers']=[{'texts':[constraint]}]
    data['hold']={'question':constraint,'scope':{'effects':['finding'],'discussions':[]}}
    data['prior_reviewers']=[{'reviewer':'claude','summary':constraint}]
    old=module['mq_render_input_v1'](data).split('--- BEGIN SUPPLIED CONTEXT ---',1)[1]
    new=module['mq_render_input'](data)
    assert new.split('--- BEGIN SUPPLIED CONTEXT ---',1)[1]==old
    assert new.count(constraint)==4
    assert ('Exact admitted head: '+'a'*40) not in new.split('--- BEGIN SUPPLIED CONTEXT ---',1)[0]


def test_fenced_question_keeps_exact_native_anchor_and_accepts_answer_after_restart(flow):
    from test_codex_gitlab_queue import compact
    f=flow;question='Aprova a regra abaixo?\n```diff\n-old\n+new\n```\nResponda sim ou não.'
    f.results['codex']=domain(outcome='question',question=question)
    job=automatic(f,reviewers=['codex']);f.drain();hold=f.q.mr(11,82)['hold']
    assert hold['question']==question
    source=human_turn(f,'Use a regra nova e continue')
    result=domain(assessment={'kind':'answer','summary':'Use the new rule',
        'text_basis':source['texts'],'scope':{'effects':['finding'],'discussions':[]},'question_anchor':hold['anchor']})
    f.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':'Estado da revisão: concluída\nCommit revisado: '+'a'*40})
    reopened=f.m['MonitorQueue'](f.config)
    try:f.m['mq_intake'](f.config,reopened,reopened.mr(11,82))
    finally:reopened.close()
    f.results['codex']=domain();f.drain()
    assert f.q.mr(11,82)['hold'] is None
    assert f.q.mr(11,82)['hold_history'][0]['question']==question
    assert f.q.job(job['id'])['state']=='completed'


@pytest.mark.parametrize('value',['01','7.0',' 7','-1','1e0',True,None])
def test_only_canonical_mcp_numeric_ids_are_normalized(module,value):
    note={'id':'12','body':'Actual note','author':{'id':'7'},'created_at':'2026-10-22T00:00:00Z',
          'updated_at':'2026-10-22T00:00:00Z','system':False,'resolved':False}
    assert module['mq_mcp_note_versions']([{'id':'d','notes':[note]}])[0]['author_id']==7
    with pytest.raises(RuntimeError):module['monitor_note'](note,'d') # REST reader stays unchanged.
    note['id']=value
    with pytest.raises(RuntimeError):module['mq_mcp_note_versions']([{'id':'d','notes':[note]}])


def test_text_only_resolution_has_no_invented_revision_receipt(flow):
    from test_codex_gitlab_queue import resolution_fixture
    f=flow;f.results['codex']=domain(actions=[resolution_fixture(f)])
    job=automatic(f,reviewers=['codex']);f.drain()
    assert all(n.get('resolved') for n in f.context['threads'][0]['notes'])
    saved=f.q.job(job['id']);own=f.q.mr(11,82)['own_outputs']
    assert own and all(value is None for value in own.values()) # reply only, no guessed resolution delta
    resolve=next(i for i in f.items[saved['stages'][0]['turn_id']] if i.get('tool')=='resolve_merge_request_thread')
    assert f.m['mq_tool_payload'](resolve['result']) is None
    assert f.q.effects()==[]


def native_hold(f,reviewers=None):
    f.results['codex']=domain(outcome='question',question='Qual regra devo usar?')
    job=automatic(f,reviewers=reviewers or ['codex']);f.drain()
    return job,f.q.mr(11,82)['hold']


def native_answer(f,text='Use a regra atual e continue',final=None,**options):
    source=human_turn(f,text,**options)
    f.items[source['turn_id']].append({'type':'agentMessage','id':'final-'+source['turn_id'],
        'phase':'final_answer','text':final or 'Revisei o código e as discussões.\nEstado da revisão: concluída\nCommit revisado: '+'a'*40})
    return source


@pytest.mark.parametrize('text,options',[
    ('responda na thread que a CSP foi corrigida e que o apontamento de memoização não procede, e marque como resolvida',{}),
    ('explique a CSP',{}),('prefiro a regra atual',{}),('publique?',{}),('publiquew',{}),
    ('publique',{'mixed':True}),('publique',{'automatic':True})])
def test_normal_post_review_messages_are_never_queued_or_classified(flow,monkeypatch,text,options):
    f=flow;job=automatic(f);f.drain()
    f.context['head']='b'*40
    source=native_answer(f,text,final='Estado da revisão: concluída\nCommit revisado: '+'b'*40,**options)
    before=copy.deepcopy(f.q.jobs());launches=f.launched.copy()
    def forbidden(*a,**kw):raise AssertionError('ordinary chat was read/classified')
    monkeypatch.setitem(f.m,'mq_human_candidates',forbidden)
    monkeypatch.setitem(f.m,'mq_session_candidates',forbidden)
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'monitor_is_open',lambda *a:False)
    import time
    f.config['_cycle_deadline']=time.monotonic()+10
    f.m['mq_scan'](f.config,f.q)
    assert f.q.jobs()==before and f.launched==launches and f.sends==[]
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert source['turn_id'] not in {s['turn_id'] for s in f.q.job(job['id'])['stages']}


def test_native_completion_preserves_original_final_and_progresses_after_restart(flow):
    f=flow;job,hold=native_hold(f);original=copy.deepcopy(f.q.job(job['id'])['stages'][0])
    source=native_answer(f)
    reopened=f.m['MonitorQueue'](f.config)
    try:f.m['mq_intake'](f.config,reopened,reopened.mr(11,82))
    finally:reopened.close()
    saved=f.q.job(job['id']);stage=saved['stages'][0]
    assert {k:v for k,v in stage.items() if k!='continuations'}==original
    assert len(stage['continuations'])==1 and stage['continuations'][0]['source']==source
    assert f.q.mr(11,82)['hold'] is None and f.q.mr(11,82)['reviewed_head'] is None
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert f.launched==['codex'] and len(f.q.jobs())==1 and f.sends==[]
    assert f.q.job(job['id'])['state']=='completed' and f.q.mr(11,82)['reviewed_head']=='a'*40
    status=f.m['mq_job_status'](f.q.job(job['id']))['stages'][0]
    assert status['result']['outcome']=='complete' and status['original_result']['outcome']=='question'


@pytest.mark.parametrize('case',['generic','insufficient','malformed','interrupted','failed','running','mixed','automatic','question','w','ambiguous','foreign-context','changed-question'])
def test_native_question_rejects_non_review_or_unproven_continuations(flow,case):
    f=flow;job,hold=native_hold(f)
    source=native_answer(f,'Use a regra atual?' if case=='question' else 'Continuew' if case=='w' else 'Continue',
        final='Explicação sem conclusão de revisão.' if case in {'generic','insufficient'} else
              'Estado da revisão: concluída' if case=='malformed' else None,
        mixed=case=='mixed',automatic=case=='automatic')
    if case in {'interrupted','failed','running'}:
        f.turns[source['session']][0]['status']='inProgress' if case=='running' else case
    if case=='ambiguous':f.items[source['turn_id']].append(copy.deepcopy(f.items[source['turn_id']][-1]))
    if case=='foreign-context':f.chats[source['session']]['cwd']='/foreign'
    if case=='changed-question':
        with f.q.atomic():
            r=f.q.mr(11,82);r['hold']['question']='changed';f.q.put_mr(r)
    before=f.q.job(job['id'])
    if case in {'foreign-context','changed-question'}:
        with pytest.raises(RuntimeError):f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    else:f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.job(job['id'])==before and f.q.mr(11,82)['hold'] is not None
    assert f.q.mr(11,82)['reviewed_head'] is None and f.sends==[] and f.launched==['codex']


@pytest.mark.parametrize('reuse_anchor',[False,True])
def test_followup_questions_are_consumed_in_native_causal_order(flow,reuse_anchor):
    f=flow;job,hold=native_hold(f)
    first=native_answer(f,final='Estado da revisão: aguardando resposta\nQual opção complementar usar?')
    second=native_answer(f,'Use a segunda opção e continue')
    if reuse_anchor:f.items[second['turn_id']][-1]['id']=f.items[first['turn_id']][-1]['id']
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    next_hold=f.q.mr(11,82)['hold']
    assert next_hold['turn_id']==first['turn_id'] and next_hold['question']=='Qual opção complementar usar?'
    assert f.q.mr(11,82)['hold_history'][0]['native_anchor']==hold['native_anchor']
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert f.q.mr(11,82)['hold'] is None and f.q.job(job['id'])['state']=='completed'
    assert [o['source']['turn_id'] for o in f.q.job(job['id'])['stages'][0]['continuations']]==[first['turn_id'],second['turn_id']]
    assert f.launched==['codex']


def test_answer_observation_does_not_steal_occupied_automatic_slot(flow):
    f=flow;job,hold=native_hold(f,reviewers=['codex','claude'])
    other=f.q.enqueue(11,90,source_key='busy-mr',kind='code',head='a'*40,source={'origin':'automatic'},context=f.context)
    busy=f.q.reserve({11});assert busy['id']==other['id']
    native_answer(f);f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.reserve({11})['id']==busy['id'] and f.launched==['codex']
    f.q.finish(busy,'fixture terminal');f.drain()
    assert f.launched==['codex','claude'] and f.q.job(job['id'])['state']=='completed'
    assert 'Revisei o código' in f.q.job(job['id'])['stages'][1]['input']


def test_resumed_review_failure_runs_remaining_reviewer_and_retries_only_failure(flow):
    f=flow;job,hold=native_hold(f,reviewers=['codex','claude'])
    native_answer(f,final='Falha no teste.\nEstado da revisão: não concluída')
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    saved=f.q.job(job['id'])
    assert f.q.mr(11,82)['hold'] is None and saved['wait_reason']=='reviewer_retry'
    assert saved['review_attempt']['reviewers']==['codex'] and f.launched==['codex','claude']
    assert f.m['mq_effective_stage'](saved['stages'][0])['state']=='failed'
    assert saved['stages'][0]['result']['outcome']=='question' and f.sends==[]


@pytest.mark.parametrize('context_change',['newhead','closed','merged'])
def test_genuine_held_completion_settles_changed_context_without_old_checkpoint(flow,context_change):
    f=flow;job,hold=native_hold(f)
    head='b'*40 if context_change=='newhead' else 'a'*40
    native_answer(f,final='Estado da revisão: concluída\nCommit revisado: '+head)
    if context_change=='newhead':f.context.update(head=head);f.context['mr']['sha']=head
    else:f.context['mr']['state']=context_change
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert f.q.mr(11,82)['hold'] is None and f.q.mr(11,82)['reviewed_head'] is None
    assert f.q.job(job['id'])['outcome']=='context changed; completed publications preserved' and f.sends==[]


def claude_answer(f,hold,*,parent=None,sealed=True,text=None):
    import uuid
    target=next((Path(f.config['claude_home'])/'projects').glob('*/'+hold['session']+'.jsonl'))
    source,final=str(uuid.uuid4()),str(uuid.uuid4())
    rows=[{'type':'user','uuid':source,'parentUuid':parent or hold['native_anchor'],'sessionId':hold['session'],
        'cwd':f.config['cwd'],'message':{'content':'Use a regra atual e continue'}},
        {'type':'assistant','uuid':final,'parentUuid':source,'sessionId':hold['session'],
         'message':{'id':'msg-'+final,'stop_reason':'end_turn','content':[{'type':'text','text':text or
              'Estado da revisão: concluída\nCommit revisado: '+'a'*40}]}}]
    if sealed:rows.append({'type':'system','subtype':'turn_duration','uuid':str(uuid.uuid4()),'parentUuid':final,'sessionId':hold['session']})
    with target.open('a') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')
    return source,final


@pytest.mark.parametrize('case',['actual','sibling','unsealed'])
def test_claude_held_continuation_requires_sealed_actual_ancestry(flow,case):
    f=flow;f.results['claude']=domain(outcome='question',question='Qual regra devo usar?')
    job=automatic(f);f.drain();hold=f.q.mr(11,82)['hold']
    original=f.q.job(job['id'])['stages'][0]
    source,final=claude_answer(f,hold,parent=original['source_id'] if case=='sibling' else None,sealed=case!='unsealed')
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    if case=='actual':
        assert f.q.mr(11,82)['hold'] is None
        f.drain();saved=f.q.job(job['id'])
        assert saved['state']=='completed' and f.launched==['claude','codex']
        assert saved['stages'][0]['continuations'][0]['source']['source_id']==source
    else:
        assert f.q.mr(11,82)['hold']==hold and f.q.job(job['id'])['stages'][0]==original
        assert f.launched==['claude']
    assert f.sends==[]


@pytest.mark.parametrize('protocol',['tools','direct'])
def test_historical_question_uses_original_assessment_and_preserves_uncertain_fence(flow,protocol):
    from test_codex_gitlab_queue import historical_hold, compact
    f=flow;job,hold=native_hold(f);historical_hold(f,protocol)
    saved=f.q.job(job['id'])
    with f.q.atomic():
        saved.update(wait_reason='effect_unknown');f.q.save(saved)
        f.q.put_effect({'key':'historical-uncertain','repository_id':11,'iid':82,'job_id':job['id'],
            'stage_id':hold['stage_id'],'state':'unknown','kind':'reply'})
    source=human_turn(f,'Use a regra atual e continue')
    answer=domain(assessment={'kind':'answer','summary':'continue','text_basis':source['texts'],
        'scope':{'effects':['finding'],'discussions':[]},'question_anchor':hold['anchor']})
    f.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':compact(answer)})
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert f.q.job(job['id'])['wait_reason']=='effect_unknown' and f.q.mr(11,82)['hold']==hold
    assert f.q.mr(11,82)['pending_answers'][0]['source']==source
    assert f.q.effect('historical-uncertain')['state']=='unknown' and f.launched==['codex'] and f.sends==[]


@pytest.mark.parametrize('case',['original-input','original-final','foreign-chat'])
def test_new_question_requires_unchanged_original_native_identity(flow,case):
    f=flow;job,hold=native_hold(f)
    if case=='original-input':f.items[hold['turn_id']][0]['content'][0]['text']='tampered input'
    elif case=='original-final':f.items[hold['turn_id']][-1]['text']+=' changed final'
    else:
        import uuid
        other=str(uuid.uuid4());f.chats[other]={'id':other,'cwd':f.config['cwd'],'projectId':None}
        f.turns[other]=[]
        with f.q.atomic():
            r=f.q.mr(11,82);r['chats']['codex']=other;f.q.put_mr(r)
    native_answer(f)
    before=f.q.job(job['id'])
    if case=='foreign-chat':f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    else:
        with pytest.raises(RuntimeError,match='original held native'):f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.job(job['id'])==before and f.q.mr(11,82)['hold']==hold and f.sends==[]


def test_question_continuation_transaction_rolls_back_and_recovers_without_duplicate(flow,monkeypatch):
    f=flow;job,hold=native_hold(f);native_answer(f)
    save=type(f.q).save
    def interrupted(self,value):
        save(self,value)
        if value['id']==job['id'] and value['stages'][0].get('continuations'):
            raise OSError('crash before observation commit')
    before=(f.q.jobs(),f.q.mrs())
    monkeypatch.setattr(type(f.q),'save',interrupted)
    with pytest.raises(OSError,match='observation commit'):f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert (f.q.jobs(),f.q.mrs())==before
    monkeypatch.setattr(type(f.q),'save',save)
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert len(f.q.job(job['id'])['stages'][0]['continuations'])==1 and f.q.mr(11,82)['hold'] is None
    assert f.launched==['codex'] and f.sends==[]


def test_claude_unrelated_leaf_marker_does_not_seal_an_unfinished_answer(flow):
    f=flow;f.results['claude']=domain(outcome='question',question='Qual regra devo usar?')
    job=automatic(f);f.drain();hold=f.q.mr(11,82)['hold']
    claude_answer(f,hold,sealed=False)
    path=next((Path(f.config['claude_home'])/'projects').glob('*/'+hold['session']+'.jsonl'))
    with path.open('a') as stream:
        stream.write(json.dumps({'type':'last-prompt','sessionId':hold['session'],
            'leafUuid':hold['native_anchor'],'lastPrompt':'Use a regra atual e continue'})+'\n')
    before=f.q.job(job['id']);f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.job(job['id'])==before and f.q.mr(11,82)['hold']==hold and f.sends==[]


@pytest.mark.parametrize('reviewer',['codex','claude'])
def test_unissued_frozen_v2_uses_actual_new_chat_instruction_policy(flow,monkeypatch,reviewer):
    f=flow;f.results[reviewer]=domain(outcome='question',question='Qual regra devo usar?')
    job=automatic(f,reviewers=[reviewer])
    external=f.m['monitor_native'] if reviewer=='codex' else f.m['mq_service_command']
    def before_issue(c,operation,*args,**kwargs):
        if operation=='thread/start' or isinstance(operation,list) and operation[0]=='systemd-run':
            raise f.m['MonitorCycleYield']('no native execution issued',issued=False)
        return external(c,operation,*args,**kwargs)
    key='monitor_native' if reviewer=='codex' else 'mq_service_command'
    monkeypatch.setitem(f.m,key,before_issue)
    with pytest.raises(f.m['MonitorCycleYield']):f.step()
    saved=f.q.job(job['id']);stage=saved['stages'][0]
    assert stage['delivery']=='prepared' and not f.launched
    # A previously frozen input remains on v2; only this disposable preparation is seeded.
    data=stage['input_context'];original=f.m['mq_render_input_v2'](data)
    with f.q.atomic():
        stage.update(input=original,input_format='message-v2');stage.pop('instructions_version',None);f.q.save(saved)
    if reviewer=='claude':
        # A real old preparation's manifest/stdin carry the same old bytes, before any send.
        path=f.q.path.parent/'executions'/stage['id']/'manifest.json'
        import hashlib
        manifest=json.loads(path.read_text());manifest['input_digest']=f.m['monitor_digest'](original)
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        stage['manifest_digest']=f.m['monitor_digest'](path.read_text())
        path.with_name('stdin').write_text(original)
        with f.q.atomic():f.q.save(saved)
    monkeypatch.setitem(f.m,key,external);f.drain()
    held=f.q.mr(11,82)['hold'];issued=f.q.job(job['id'])['stages'][0]
    assert issued['input']==original and issued['input_format']=='message-v2'
    assert issued['instructions_version']==7
    assert f.m['mq_input_context'](f.q,issued)==data
    if reviewer=='codex':native_answer(f)
    else:claude_answer(f,held)
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert f.q.mr(11,82)['hold'] is None and f.q.job(job['id'])['state']=='completed'
    assert f.launched==[reviewer] and len(f.q.jobs())==1 and f.sends==[]


@pytest.mark.parametrize('limit',['pages','earlier-replies'])
def test_native_hold_observation_keeps_causal_progress_across_bounded_cycles(flow,monkeypatch,limit):
    f=flow;job,hold=native_hold(f)
    first=native_answer(f,'explique a regra',final='Explicação sem conclusão de revisão.')
    second=native_answer(f,'prefiro esta regra',final='Preferência anotada.')
    sufficient=native_answer(f)
    original=f.m['monitor_native'];calls=[];allow=[2];spent=[0]
    ordered=copy.deepcopy(f.turns[hold['session']])
    def bounded(c,method,params,**kw):
        if limit=='pages' and method=='thread/turns/list':
            if spent[0]>=allow[0]:raise f.m['MonitorCycleYield']('page share exhausted')
            spent[0]+=1;index=int(params.get('cursor','0'));calls.append(index)
            return {'data':[ordered[index]],'nextCursor':str(index+1) if index+1<len(ordered) else None}
        if limit=='earlier-replies' and method=='thread/items/list' and params['turnId'] in {first['turn_id'],second['turn_id']}:
            if spent[0]>=1:raise f.m['MonitorCycleYield']('reply share exhausted')
            spent[0]+=1;calls.append(params['turnId'])
        return original(c,method,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',bounded)
    with pytest.raises(f.m['MonitorCycleYield']):f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.mr(11,82)['hold']==hold and f.launched==['codex']
    reopened=f.m['MonitorQueue'](f.config);spent[0]=0
    try:f.m['mq_intake'](f.config,reopened,reopened.mr(11,82))
    finally:reopened.close()
    assert f.q.mr(11,82)['hold'] is None
    expected=[0,1,2,3] if limit=='pages' else [first['turn_id'],second['turn_id']]
    assert calls==expected
    f.drain();saved=f.q.job(job['id'])
    assert saved['state']=='completed' and saved['stages'][0]['continuations'][0]['source']==sufficient
    assert f.launched==['codex'] and f.sends==[]


@pytest.mark.parametrize('provider',['codex','claude'])
def test_explicit_restart_uses_current_native_question_and_ignores_earlier_manual_context(flow,provider):
    f=flow
    f.results[provider]=domain(outcome='question',question='Qual regra devo usar?')
    job=automatic(f,reviewers=[provider]);f.drain();hold=f.q.mr(11,82)['hold']
    if provider=='codex':
        native_answer(f,'explique a regra',final='Explicação sem conclusão de revisão.')
        native_answer(f,final='Estado da revisão: aguardando resposta\nQual opção complementar usar?')
    else:
        claude_answer(f,hold,text='Explicação sem conclusão de revisão.')
        claude_answer(f,hold,text='Estado da revisão: aguardando resposta\nQual opção complementar usar?')
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));current=f.q.mr(11,82)['hold']
    assert current['question']=='Qual opção complementar usar?'
    original=f.q.job(job['id']);assert original['stages'][0]['result']['question']==hold['question']
    result=f.m['mq_restart_review'](f.config,job['id'],hold['stage_id'],'explicit new review')
    assert result['restarted'] and f.q.mr(11,82)['hold'] is None
    saved=f.q.job(job['id'])
    assert saved['stages']==[] and saved['rounds'][-1]['stages']==original['stages']
    assert saved['rounds'][-1]['retirement']['question']==current and f.sends==[]
    assert f.m['mq_restart_review'](f.config,job['id'],hold['stage_id'],'explicit new review')==result


def test_previously_admitted_human_work_uses_native_continuation_without_code_credit(flow):
    f=flow;source=human_turn(f,'Revise esta discussão e publique a resposta')
    f.results['codex']=domain(outcome='question',question='Qual regra devo usar?')
    job=f.q.enqueue(11,82,source_key='previous-human',kind='human',head='a'*40,
        source=source,context=f.context,reviewers=['codex'])
    f.drain();assert f.q.mr(11,82)['hold']
    native_answer(f);f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    assert f.q.job(job['id'])['state']=='completed' and f.q.mr(11,82)['hold'] is None
    assert f.q.mr(11,82)['reviewed_head'] is None and len(f.q.jobs())==1 and f.launched==['codex'] and f.sends==[]


def test_already_admitted_historical_intake_keeps_its_explicit_initial_task_contract(flow):
    from test_codex_gitlab_queue import assessment
    f=flow
    previous=f.q.enqueue(11,82,source_key='earlier-discussion',kind='discussion',head='a'*40,
        source={'origin':'automatic'},context=f.context,reviewers=['codex'])
    f.drain();earlier=f.q.job(previous['id'])['stages'][0]['session']
    source=human_turn(f,'explique a regra atual')
    a=assessment(source['texts'][0],kind='explanation');a['scope']={'effects':[],'discussions':[]}
    f.results['codex']=domain(outcome='noop',assessment=a)
    job=f.q.enqueue(11,82,source_key='already-admitted-intake',kind='intake',head='a'*40,
        source=source,context=f.context,reviewers=['codex'])
    request=f.m['monitor_native'];instructions=[]
    def native(c,method,params,**kw):
        if method=='thread/start':instructions.append(params['developerInstructions'])
        return request(c,method,params,**kw)
    # Capture actual creation instructions, while keeping the real FIFO and parser.
    from unittest.mock import patch
    with patch.dict(f.m,{'monitor_native':native}):f.drain()
    assert len(instructions)==1 and 'already-admitted historical read-only assessment' in instructions[0]
    assert 'csm-assessment' in instructions[0] and 'normal later human messages' in instructions[0]
    assert f.q.job(job['id'])['state']=='completed' and len(f.q.jobs())==2
    assert f.q.mr(11,82)['reviewed_head'] is None and f.sends==[]
    assert f.q.job(job['id'])['stages'][0]['session']!=earlier
    assert 'csm-assessment' not in f.m['mq_instructions']()


def test_transient_native_revalidation_retries_same_sufficient_answer(flow,monkeypatch):
    f=flow;job,hold=native_hold(f);source=native_answer(f)
    native=f.m['monitor_native'];reads=[]
    def unavailable(c,method,params,**kw):
        if method=='thread/read':
            reads.append(params['threadId'])
            if len(reads)==2:raise RuntimeError('temporary native read failure')
        return native(c,method,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',unavailable)
    import time
    f.config['_cycle_deadline']=time.monotonic()+10
    monkeypatch.setitem(f.m,'monitor_is_open',lambda *a:False)
    f.m['mq_scan'](f.config,f.q)
    assert f.q.mr(11,82)['hold']==hold and not f.q.job(job['id'])['stages'][0].get('continuations')
    reopened=f.m['MonitorQueue'](f.config)
    try:f.m['mq_scan'](f.config,reopened)
    finally:reopened.close()
    f.drain();saved=f.q.job(job['id'])
    assert saved['state']=='completed' and saved['stages'][0]['continuations'][0]['source']==source
    assert len(saved['stages'][0]['continuations'])==1 and f.launched==['codex'] and f.sends==[]
