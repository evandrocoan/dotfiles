"""Passive evidence must neither suppress unknown activity nor block native recovery."""
import copy
import json
from pathlib import Path
import socket
import sqlite3
import time

import pytest

from test_codex_gitlab_queue import module, flow
from test_codex_gitlab_direct import automatic


def launched(f):
    job=automatic(f,reviewers=['codex']);f.step()
    active=f.q.job(job['id'])
    return active,active['stages'][0]


def publication(f,stage,tool='create_merge_request_thread'):
    note={'id':'123','body':'Actual created note','author':{'id':'7'},'system':False,
          'resolvable':True,'resolved':False,'created_at':'2026-10-22T00:00:00Z',
          'updated_at':'2026-10-22T00:00:00Z'}
    args={'project_id':'11','merge_request_iid':'82','body':note['body']}
    payload={'id':'actual-discussion','notes':[note]}
    if tool=='create_merge_request_discussion_note':
        args['discussion_id']='actual-discussion';payload=note
    item={'type':'mcpToolCall','id':'publication','server':'gitlab','tool':tool,
          'arguments':args,'status':'completed','error':None,
          'result':{'content':[{'type':'text','text':json.dumps(payload)}]}}
    f.items[stage['turn_id']].insert(-1,item)
    return item,payload,note


def wire(item,payload):
    item['result']={'content':[{'type':'text','text':json.dumps(payload)}]}


def pending_delta(f,stage,note):
    row=f.m['mq_mcp_note_versions']([{'id':'actual-discussion','notes':[note]}])[0]
    return f.q.enqueue(11,82,source_key='observed-note',kind='discussion',head='a'*40,
        source={'origin':'automatic','note_delta':{'before':[],'after':[row]}},context=f.context)


def test_recorded_mr7_projected_read_allows_terminal_retry_and_next_mr(flow,monkeypatch):
    f=flow
    artifact=json.loads((Path(__file__).parent/'fixtures/gitlab-passive-output-mr7.json').read_text())
    assert artifact['capture_kind']=='partial-authenticated-native-artifact'
    monkeypatch.setattr(socket.socket,'connect',lambda *a:pytest.fail('unrecorded network access'))
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)
    job,stage=launched(f)
    original=f.items[stage['turn_id']]
    calls=[{'type':'mcpToolCall','server':'gitlab','status':'completed',**c} for c in artifact['calls']]
    projected=next(c for c in calls if c['tool']=='mr_discussions')
    projected_rows=f.m['mq_tool_payload'](projected['result'])
    assert projected['arguments']['jmespath'] and 'id' not in projected_rows[0]
    final={**original[-1],'text':artifact['observed']['text']}
    f.items[stage['turn_id']]=[original[0],*calls,final]
    other=f.q.enqueue(11,83,source_key='other-mr',kind='code',head='a'*40,
        source={'origin':'automatic'},context=f.context,reviewers=['claude'])
    assert f.tick()['cycle']=='checked'
    saved=f.q.job(job['id'])
    assert saved['state']=='pending' and saved['wait_reason']=='reviewer_retry'
    assert saved['stages'][0]['state']=='failed'
    assert saved['stages'][0]['summary']==artifact['observed']['text']
    assert saved['stages'][0]['error']['message']==artifact['observed']['text']
    assert f.q.mr(11,82)['reviewed_head'] is None
    assert f.q.job(other['id'])['stages'][0]['reviewer']=='claude'
    assert f.launched==['codex','claude'] and f.sends==[]
    own=f.q.mr(11,82)['own_outputs'];assert len(own)==1
    before=copy.deepcopy(own)
    f.m['mq_observe_direct_stages'](f.config,f.q)
    assert f.q.mr(11,82)['own_outputs']==before


@pytest.mark.parametrize('tool',['create_merge_request_thread','create_merge_request_discussion_note'])
@pytest.mark.parametrize('envelope',['text','nested','structured'])
def test_exact_created_revision_is_idempotent_across_reopen(flow,tool,envelope):
    f=flow;job,stage=launched(f);item,payload,note=publication(f,stage,tool)
    if envelope=='nested':
        item['result']={'content':[{'type':'text','text':json.dumps(item['result'])}]}
    elif envelope=='structured':item['result']={'structuredContent':payload,'content':[]}
    pending=pending_delta(f,stage,note)
    assert f.m['mq_observe_outputs'](f.config,f.q,job,stage) is True
    assert f.q.job(pending['id'])['outcome']=='self-only discussion activity; not reviewed'
    row=f.m['mq_mcp_note_versions']([{'id':'actual-discussion','notes':[note]}])[0]
    assert f.q.mr(11,82)['own_outputs']=={f.m['monitor_digest'](row):None}
    reopened=f.m['MonitorQueue'](f.config)
    try:
        saved=reopened.job(job['id'])
        f.m['mq_observe_outputs'](f.config,reopened,saved,saved['stages'][0])
        assert reopened.job(job['id'])==saved
        assert reopened.mr(11,82)['own_outputs']=={f.m['monitor_digest'](row):None}
    finally:reopened.close()


@pytest.mark.parametrize('change',['extra_note','duplicate_note','body','missing_updated','missing_created',
    'missing_resolved','invalid_date','naive_date','backwards_date','author_type','note_type','projection',
    'error','nested_error','malformed_block','excessive_nesting','wrong_discussion','wrong_project'])
def test_unknown_publication_never_retires_discussion_work(flow,change):
    f=flow;job,stage=launched(f);item,payload,note=publication(f,stage)
    pending=pending_delta(f,stage,copy.deepcopy(note))
    if change=='extra_note':payload['notes'].append({**note,'id':'124'})
    elif change=='duplicate_note':payload['notes'].append(copy.deepcopy(note))
    elif change=='body':note['body']='Another same-account edit'
    elif change.startswith('missing_'):note.pop(change[len('missing_'):]+('_at' if change in {'missing_updated','missing_created'} else ''))
    elif change=='invalid_date':note['updated_at']='not-a-date'
    elif change=='naive_date':note['updated_at']='2026-10-22T00:00:00'
    elif change=='backwards_date':note['updated_at']='2026-10-21T00:00:00Z'
    elif change=='author_type':note['author']=[]
    elif change=='note_type':payload['notes']=[42]
    elif change=='projection':item['arguments']['jmespath']='notes[0]'
    elif change=='wrong_discussion':note['discussion_id']='foreign'
    elif change=='wrong_project':note['project_id']='99'
    wire(item,payload)
    if change=='error':item['result']['isError']=True
    elif change=='nested_error':
        item['result']={'content':[{'type':'text','text':json.dumps({**item['result'],'isError':True})}]}
    elif change=='malformed_block':item['result']={'content':[42]}
    elif change=='excessive_nesting':
        for _ in range(10):item['result']={'content':[{'type':'text','text':json.dumps(item['result'])}]}
    f.m['mq_try_observe_outputs'](f.config,f.q,job,stage)
    assert not f.q.mr(11,82).get('own_outputs')
    assert f.q.job(pending['id'])['state']=='pending'
    assert f.q.mr(11,82)['reviewed_head'] is None


@pytest.mark.parametrize('tool',['mr_discussions','get_merge_request_discussion','resolve_merge_request_thread'])
def test_unrelated_outputs_are_never_decoded(flow,monkeypatch,tool):
    f=flow;job,stage=launched(f)
    f.items[stage['turn_id']]=[f.items[stage['turn_id']][0],{
        'type':'mcpToolCall','id':'unrelated','server':'gitlab','tool':tool,'status':'completed',
        'arguments':{'project_id':'11','merge_request_iid':'82'},'result':{'arbitrary':'shape'}}]
    monkeypatch.setitem(f.m,'mq_tool_payload',lambda *a:pytest.fail('decoded unrelated tool'))
    f.m['mq_observe_outputs'](f.config,f.q,job,stage)
    assert not f.q.mr(11,82).get('own_outputs')


@pytest.mark.parametrize('failure',[KeyError('shape'),TypeError('shape'),RuntimeError('source unavailable')])
def test_optional_acquisition_errors_do_not_block_terminal_or_next_work(flow,monkeypatch,failure):
    f=flow;job,stage=launched(f)
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)
    def broken(*a):raise failure
    monkeypatch.setitem(f.m,'mq_native_gitlab_calls',broken)
    assert f.tick()['cycle']=='checked'
    assert f.q.job(job['id'])['state']=='completed'
    assert f.q.job(job['id'])['stages'][0]['state']=='succeeded'
    assert f.q.meta('output_observation:'+stage['id'])['error']==str(failure)
    assert f.q.mr(11,82)['reviewed_head']=='a'*40


@pytest.mark.parametrize('timeout',[False,True])
def test_optional_budget_exhaustion_preserves_native_completion_and_timeout(flow,monkeypatch,timeout):
    f=flow;job,stage=launched(f)
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)
    other=f.q.enqueue(11,83,source_key='budget-next',kind='code',head='a'*40,
        source={'origin':'automatic'},context=f.context,reviewers=['claude'])
    if timeout:
        f.turns[stage['session']][0]['status']='inProgress'
        f.m['mq_update_stage'](f.q,job,stage['id'],review_deadline=1)
        monkeypatch.setitem(f.m,'mq_cancel_stage',lambda c,s:True) # exact native stop boundary
    clock=[time.monotonic()]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    def slow(c,*a):
        assert c['_cycle_deadline']-clock[0]<=5
        clock[0]=c['_cycle_deadline']+.001
        c['_native_guard']()
    monkeypatch.setitem(f.m,'mq_native_gitlab_calls',slow)
    assert f.tick()['cycle']=='checked'
    saved=f.q.job(job['id'])
    assert saved['stages'][0]['state']==('failed' if timeout else 'succeeded')
    assert saved['state']==('pending' if timeout else 'completed')
    assert f.q.mr(11,82)['reviewed_head']==(None if timeout else 'a'*40)
    assert f.q.job(other['id'])['stages'][0]['reviewer']=='claude'
    assert not f.q.meta('output_observation:'+stage['id'])


@pytest.mark.parametrize('failure',[InterruptedError('interrupted'),KeyboardInterrupt(),SystemExit(),
    sqlite3.OperationalError('database failed')])
def test_nonoptional_failures_propagate_without_observation_writes(flow,monkeypatch,failure):
    f=flow;job,stage=launched(f);publication(f,stage)
    def fail(*a):raise failure
    if isinstance(failure,sqlite3.OperationalError):monkeypatch.setattr(f.q,'put_mr',fail)
    else:monkeypatch.setitem(f.m,'mq_native_gitlab_calls',fail)
    with pytest.raises(type(failure)):
        f.m['mq_try_observe_outputs'](f.config,f.q,job,stage)
    assert f.q.job(job['id'])==job
    assert not f.q.mr(11,82).get('own_outputs')
    assert not f.q.meta('output_observation:'+stage['id'])


def test_stale_stage_persistence_is_not_an_optional_source_failure(flow):
    f=flow;job,stage=launched(f);publication(f,stage)
    stale=copy.deepcopy(job)
    with f.q.atomic():job['operator_change']='new';f.q.save(job)
    with pytest.raises(RuntimeError,match='direct observation stage changed'):
        f.m['mq_try_observe_outputs'](f.config,f.q,stale,stale['stages'][0])
    assert f.q.job(job['id'])==job
    assert not f.q.mr(11,82).get('own_outputs')


def test_unrelated_cycle_yield_is_never_converted_to_optional_exhaustion(flow,monkeypatch):
    f=flow;job,stage=launched(f)
    def fail(*a):raise f.m['MonitorCycleYield']('unrelated yield')
    monkeypatch.setitem(f.m,'mq_native_gitlab_calls',fail)
    with pytest.raises(f.m['MonitorCycleYield'],match='unrelated yield'):
        f.m['mq_try_observe_outputs'](f.config,f.q,job,stage)
    assert f.q.job(job['id'])==job


def test_changed_result_never_commits_partial_observation(flow):
    f=flow;job,stage=launched(f);item,payload,note=publication(f,stage)
    f.m['mq_observe_outputs'](f.config,f.q,job,stage)
    before=f.q.mr(11,82);saved=copy.deepcopy(job)
    new=copy.deepcopy(item);new['id']='another-publication'
    f.items[stage['turn_id']].insert(1,new)
    item['arguments']['body']='Changed native result'
    assert f.m['mq_try_observe_outputs'](f.config,f.q,job,stage) is False
    assert 'observed native tool result changed' in f.q.meta('output_observation:'+stage['id'])['error']
    assert f.q.mr(11,82)==before and f.q.job(job['id'])==saved


def test_optional_failure_cannot_override_native_identity_denial(flow,monkeypatch):
    f=flow;job,stage=launched(f)
    f.items[stage['turn_id']][0]['clientId']='foreign-native-input'
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)
    f.tick()
    assert f.q.job(job['id'])['stages'][0]['state']=='running'
    assert f.q.mr(11,82)['reviewed_head'] is None
    assert f.launched==['codex']


def test_optional_timeout_never_releases_unknown_native_execution(flow,monkeypatch):
    f=flow;job,stage=launched(f)
    f.turns[stage['session']][0]['status']='inProgress'
    f.m['mq_update_stage'](f.q,job,stage['id'],review_deadline=1)
    monkeypatch.setitem(f.m,'mq_cancel_stage',lambda *a:False)
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)
    def broken(*a):raise RuntimeError('optional source failure')
    monkeypatch.setitem(f.m,'mq_native_gitlab_calls',broken)
    f.q.enqueue(11,83,source_key='blocked-by-native',kind='code',head='a'*40,
        source={'origin':'automatic'},context=f.context,reviewers=['claude'])
    f.tick()
    saved=f.q.job(job['id'])
    assert saved['state']=='running' and saved['stages'][0]['state']=='running'
    assert saved['stages'][0]['cancel_requested_at']
    assert f.launched==['codex'] and f.q.mr(11,82)['reviewed_head'] is None


def test_storage_failure_after_fingerprint_write_rolls_back_memory_and_database(flow,monkeypatch):
    f=flow;job,stage=launched(f);publication(f,stage)
    before=copy.deepcopy(job);record=f.q.mr(11,82);writes=[]
    put=f.q.put_mr
    def write(value):
        put(value);writes.append(copy.deepcopy(value))
    def fail(*a):raise sqlite3.OperationalError('stage save failed after fingerprint write')
    monkeypatch.setattr(f.q,'put_mr',write)
    monkeypatch.setattr(f.q,'save',fail)
    with pytest.raises(sqlite3.OperationalError,match='stage save failed after fingerprint write'):
        f.m['mq_try_observe_outputs'](f.config,f.q,job,stage)
    assert len(writes)==1 and writes[0]['own_outputs']
    assert f.q.mr(11,82)==record and f.q.job(job['id'])==before and job==before
    assert not f.q.meta('output_observation:'+stage['id'])


def test_actual_whole_cycle_exhaustion_is_not_optional(flow,monkeypatch):
    f=flow;job,stage=launched(f);publication(f,stage)
    clock=[time.monotonic()];deadline=clock[0]+100
    config={**f.config,'_cycle_deadline':deadline}
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    def expire(c,*a):
        clock[0]=deadline+1
        c['_native_guard']()
    monkeypatch.setitem(f.m,'mq_native_gitlab_calls',expire)
    with pytest.raises(f.m['MonitorCycleYield'],match='cycle budget exhausted'):
        f.m['mq_try_observe_outputs'](config,f.q,job,stage)
    assert f.q.job(job['id'])==job and not f.q.mr(11,82).get('own_outputs')
    assert not f.q.meta('output_observation:'+stage['id'])


@pytest.mark.parametrize('cost',['acquisition','rotation','completion_commit'])
def test_observation_backlog_stops_before_next_optional_transaction(flow,monkeypatch,cost):
    f=flow
    # Real completed fixture rounds retain their authentic inputs and native results.
    for iid in (90,91,92):
        f.q.enqueue(11,iid,source_key='old:'+str(iid),kind='code',head='a'*40,
            source={'origin':'automatic'},context=f.context,reviewers=['codex'])
        f.drain()
    job,stage=launched(f)
    monkeypatch.setitem(f.m,'mq_inventory',lambda *a:True)
    monkeypatch.setitem(f.m,'mq_intake',lambda *a:None)
    clock=[time.monotonic()]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    rotations=[];set_meta=f.m['MonitorQueue'].set_meta;save=f.m['MonitorQueue'].save
    def rotate(q,key,value):
        set_meta(q,key,value)
        if key=='output_next_stage':
            rotations.append(value)
            if cost=='rotation':clock[0]+=6
    def commit(q,value):
        save(q,value)
        if cost=='completion_commit' and any(s.get('output_collected') for s in value['stages']):
            clock[0]+=6
    def acquire(c,*a):
        if cost=='acquisition':
            clock[0]=c['_cycle_deadline']+.001
            c['_native_guard']()
        return []
    monkeypatch.setattr(f.m['MonitorQueue'],'set_meta',rotate)
    monkeypatch.setattr(f.m['MonitorQueue'],'save',commit)
    monkeypatch.setitem(f.m,'mq_native_gitlab_calls',acquire)
    assert f.tick()['cycle']=='checked'
    assert len(rotations)==1
    assert f.q.meta('output_next_stage')==rotations[0]
    assert f.q.job(job['id'])['state']=='completed'
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert sum(not s.get('output_collected',False) for j in f.q.jobs() for s in j['stages'])>=3
