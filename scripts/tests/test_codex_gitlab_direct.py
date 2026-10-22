"""Direct publication uses native tools; queue/results retain their actual identities."""
import copy
import json
from pathlib import Path

import pytest
from test_codex_gitlab_queue import module, flow, domain, human_turn, assessment


def automatic(f,reviewers=None):
    return f.q.enqueue(11,82,source_key='direct-code',kind='code',head='a'*40,
        source={'origin':'automatic','head':'a'*40},context=copy.deepcopy(f.context),reviewers=reviewers)


@pytest.mark.parametrize('mutation',[None,'text','context','version'])
def test_captured_original_message_stays_on_its_original_reader(flow,mutation):
    stage=json.loads((Path(__file__).parent/'fixtures/gitlab-message-v1.json').read_text())
    if mutation=='text':stage['input']+=' forged'
    if mutation=='context':stage['input_context']['head']='b'*40
    if mutation=='version':stage['input_format']='message-v99'
    if mutation:
        with pytest.raises(RuntimeError,match='immutable reviewer input'):flow.m['mq_input_context'](flow.q,stage)
    else:
        assert flow.m['mq_input_context'](flow.q,stage)==stage['input_context']
        assert 'gitlab_review' in stage['input']


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
    assert stage['protocol']=='direct' and stage['input_format']=='message-v2'
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
    f.items[source['turn_id']].append({'type':'agentMessage','id':'answer-final','phase':'final_answer','text':compact(result)})
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
