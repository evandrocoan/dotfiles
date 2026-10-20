"""Recorded native MR !7 artifact and real worker/SQLite; external transports are simulated."""
import copy
import json
from pathlib import Path
import socket
import uuid

import pytest

from test_codex_gitlab_queue import assessment, domain, flow, module, rendered
from test_codex_gitlab_recovery import FIXTURES, captured_claude, enqueue, finding


ARTIFACT='gitlab-claude-parallel-transcript.json'
SOURCE='4e226cec-0197-4435-9c00-ae4600d6296d'
FINAL='2616bc72-1336-4e8d-8c30-a0e3d553f0cf'


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args,**kwargs):raise AssertionError('unexpected live network access')
    monkeypatch.setattr(socket.socket,'connect',deny)
    monkeypatch.setattr(socket,'create_connection',deny)


def artifact():
    return json.loads((FIXTURES/ARTIFACT).read_text())


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'claude-parallel-test:'+name))


def parallel_rows(order=('a','b'),tip='b'):
    session='b425590f-cf2f-4125-9f34-8829a1fb1a61'
    source={'type':'user','uuid':SOURCE,'sessionId':session,'message':{'content':'Captured parallel input'}}
    def assistant(identity,parent,message,content,stop):
        return {'type':'assistant','uuid':identity,'parentUuid':parent,'sessionId':session,
            'message':{'id':message,'stop_reason':stop,'content':content}}
    calls={name:assistant(uid('call-'+name),SOURCE if name=='a' else uid('call-a'),
        'message-tools',[{'type':'tool_use','id':'tool-'+name,'name':'Read','input':{}}],'tool_use') for name in ('a','b')}
    returns={name:{'type':'user','uuid':uid('return-'+name),'parentUuid':calls[name]['uuid'],
        'sessionId':session,'message':{'content':[{'type':'tool_result','tool_use_id':'tool-'+name,
            'content':'Captured tool output'}]}} for name in ('a','b')}
    thinking=assistant(uid('thinking'),returns[tip]['uuid'],'message-final',[{'type':'thinking'}],'end_turn')
    final=assistant(FINAL,thinking['uuid'],'message-final',[{'type':'text','text':'Complete parallel review.'}],'end_turn')
    seal={'type':'system','subtype':'turn_duration','uuid':uid('seal'),'parentUuid':FINAL,'sessionId':session}
    rows=[source,calls['a'],calls['b'],*[returns[name] for name in order],thinking,final,seal]
    return rows,{r['uuid']:r for r in rows}


@pytest.mark.parametrize('state',['running','done'])
def test_recorded_mr7_parallel_final_is_collected(module,tmp_path,monkeypatch,state):
    m=module['mq_step'].__globals__
    config,stage,rows,path=captured_claude(m,tmp_path,monkeypatch,state=state,artifact_name=ARTIFACT)
    before=path.read_bytes();actual=m['mq_claude_observe'](config,stage)
    assert actual=={'terminal':True,'source_id':SOURCE,'anchor':FINAL,
        'text':'Captured parallel review result.'}
    assert len(rows)==294 and path.read_bytes()==before


@pytest.mark.parametrize('order',[('a','b'),('b','a')])
@pytest.mark.parametrize('tip',['a','b'])
def test_parallel_results_join_by_identity_in_either_order_and_branch(module,order,tip):
    rows,_=parallel_rows(order,tip)
    assert module['mq_claude_final'](rows,rows[0])=={
        'sealed':True,'anchor':FINAL,'text':'Complete parallel review.'}


@pytest.mark.parametrize('missing',['a','b'])
@pytest.mark.parametrize('tip',['a','b'])
def test_each_parallel_return_is_required_even_outside_continuing_ancestry(module,missing,tip):
    rows,_=parallel_rows(tip=tip)
    rows=[r for r in rows if r['uuid']!=uid('return-'+missing)]
    assert module['mq_claude_final'](rows,rows[0])=={'sealed':False}


@pytest.mark.parametrize('change',['foreign_id','foreign_batch','foreign_source','wrong_parent','mixed','duplicate_block'])
def test_invalid_sibling_result_cannot_credit_parallel_message(module,change):
    rows,lookup=parallel_rows();result=lookup[uid('return-a')]
    if change=='foreign_id':result['message']['content'][0]['tool_use_id']='foreign-tool'
    elif change=='foreign_batch':result['message']['content'].append({'type':'tool_result','tool_use_id':'foreign-tool'})
    elif change=='foreign_source':
        foreign={'type':'user','uuid':uid('foreign'),'message':{'content':'Another human request'}}
        rows.insert(3,foreign);result['parentUuid']=foreign['uuid']
    elif change=='wrong_parent':result['parentUuid']=SOURCE
    elif change=='mixed':result['message']['content'].append({'type':'text','text':'Use another request'})
    else:result['message']['content'].append(copy.deepcopy(result['message']['content'][0]))
    assert module['mq_claude_final'](rows,rows[0])=={'sealed':False}


@pytest.mark.parametrize('change,expected',[
    ('duplicate_return','duplicate Claude tool result identity'),
    ('reused_call','reused Claude tool call identity'),
    ('message_owner','ambiguous Claude message ownership'),
    ('late_block','Claude message blocks after continuation')])
def test_ambiguous_parallel_identity_is_rejected(module,change,expected):
    rows,lookup=parallel_rows(tip='a')
    if change=='duplicate_return':
        duplicate=copy.deepcopy(lookup[uid('return-a')]);duplicate['uuid']=uid('duplicate')
        rows.insert(5,duplicate)
    elif change=='reused_call':
        lookup[uid('call-b')]['message']['id']='another-message'
        lookup[uid('call-b')]['message']['content'][0]['id']='tool-a'
    elif change=='message_owner':lookup[uid('call-b')]['parentUuid']=SOURCE
    else:
        call=lookup[uid('call-b')];rows.remove(call);rows.insert(5,call)
    with pytest.raises(RuntimeError,match=expected):module['mq_claude_final'](rows,rows[0])


def test_interleaved_call_and_return_fragments_of_one_message_are_supported(module):
    rows,lookup=parallel_rows(tip='b');rows.remove(lookup[uid('return-a')])
    rows.insert(2,lookup[uid('return-a')]);lookup[uid('call-b')]['parentUuid']=uid('return-a')
    assert module['mq_claude_final'](rows,rows[0])=={
        'sealed':True,'anchor':FINAL,'text':'Complete parallel review.'}


def test_late_return_cannot_retroactively_validate_an_earlier_final(module):
    rows,lookup=parallel_rows(tip='b');result=lookup[uid('return-a')];rows.remove(result)
    rows.insert(-1,result)
    assert module['mq_claude_final'](rows,rows[0])=={'sealed':False}


def test_return_cannot_use_group_membership_in_place_of_actual_call_ancestry(module):
    rows,lookup=parallel_rows(tip='a')
    lookup[uid('return-b')]['parentUuid']=uid('call-a')
    assert module['mq_claude_final'](rows,rows[0])=={'sealed':False}


@pytest.mark.parametrize('identity',[None,'',17])
@pytest.mark.parametrize('record,tip',[('return-a','b'),('call-b','a')])
def test_parallel_call_and_return_require_their_own_native_record_identity(module,identity,record,tip):
    rows,lookup=parallel_rows(tip=tip);lookup[uid(record)]['uuid']=identity
    with pytest.raises(RuntimeError,match='invalid Claude native record identity'):
        module['mq_claude_final'](rows,rows[0])


def test_parallel_return_cannot_reuse_another_native_record_identity(module):
    rows,lookup=parallel_rows();lookup[uid('return-a')]['uuid']=uid('call-a')
    with pytest.raises(RuntimeError,match='duplicate Claude native record identity'):
        module['mq_claude_final'](rows,rows[0])


def test_exact_terminal_inventory_can_complete_automatic_review_without_seal(module,tmp_path,monkeypatch):
    rows=[r for r in artifact()['records'] if r.get('subtype')!='turn_duration']
    m=module['mq_step'].__globals__
    config,stage,_,_=captured_claude(m,tmp_path,monkeypatch,records=rows,state='done',artifact_name=ARTIFACT)
    actual=m['mq_claude_observe'](config,stage)
    assert actual['terminal'] is True and actual['anchor']==FINAL
    assert actual['text']=='Captured parallel review result.'


@pytest.mark.parametrize('seal',['absent','sibling','early'])
def test_parallel_human_intake_requires_exact_descendant_seal(flow,tmp_path,monkeypatch,seal):
    rows=artifact()['records'];marker=next(r for r in rows if r.get('subtype')=='turn_duration')
    rows.remove(marker)
    if seal!='absent':
        marker['parentUuid']=SOURCE
        rows.insert(6 if seal=='early' else len(rows),marker)
    config,stage,_,_=captured_claude(flow.m,tmp_path,monkeypatch,records=rows,state='done',artifact_name=ARTIFACT)
    record=flow.q.mr(11,82);record['chats']['claude']=stage['session']
    assert list(flow.m['mq_session_candidates'](config,flow.q,record,'claude',stage['session']))==[]
    assert flow.q.jobs()==[] and flow.q.mr(11,82)['hold'] is None and flow.sends==[]


def test_recorded_mr7_result_survives_restart_and_next_reviewer_receives_proposals(flow,monkeypatch):
    f=flow;f.results['claude']=domain(actions=[finding('parallel-concern')])
    captured=artifact()
    job=enqueue(f);assert f.m['mq_step'](f.config,f.q)
    # Previously issued background stages retain their actual transport and ancestry.
    saved=f.q.job(job['id']);stage=saved['stages'][0]
    rows=copy.deepcopy(captured['records'])
    for row in rows:
        if 'sessionId' in row:row['sessionId']=stage['session']
        row['cwd']=f.config['cwd']
        if row.get('uuid')==SOURCE:row['message']['content']=stage['input']
        if row.get('uuid')==FINAL:row['message']['content']=[{'type':'text','text':rendered(f.results['claude'])}]
    path=Path(f.config['claude_home'])/'projects'/'fixture'/(stage['session']+'.jsonl')
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with f.q.atomic():
        stage.pop('transport');stage['background_id']=stage['session'][:8]
        f.q.save(saved)
    assert f.m['mq_step'](f.config,f.q)
    saved=copy.deepcopy(f.q.job(job['id']));first=saved['stages'][0]
    assert first['state']=='succeeded' and first['result']==f.results['claude']
    assert first['anchor']==FINAL and first['source_id']==SOURCE
    assert f.launched==['claude'] and f.sends==[]
    reopened=f.m['MonitorQueue'](f.config)
    try:
        assert f.m['mq_step'](f.config,reopened)
        current=reopened.job(job['id'])
        assert current['stages'][0]==first and current['stages'][1]['reviewer']=='codex'
        assert current['stages'][1]['state']=='running' and f.launched==['claude','codex']
        immutable=json.loads((reopened.path.parent/'inputs'/(current['stages'][1]['id']+'.json')).read_text())
        assert immutable['prior_stages'][0]['result']['actions']==[finding('parallel-concern')]
        assert reopened.mr(11,82)['reviewed_head'] is None and f.sends==[]
    finally:reopened.close()


def append_answer(f,hold,*,mixed=False):
    text='use a regra atual e continue';rows=copy.deepcopy(artifact()['records'])
    answer=domain(assessment=assessment(text,kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    for row in rows:
        if 'sessionId' in row:row['sessionId']=hold['session']
        row['cwd']=f.config['cwd']
        if row.get('uuid')==SOURCE:row['message']['content']=text;row['parentUuid']=hold['native_anchor']
        if row.get('uuid')==FINAL:row['message']['content']=[{'type':'text','text':rendered(answer)}]
        if mixed and row.get('uuid')=='ef17ebbf-8412-48d6-afb5-743dcf10c901':
            row['message']['content'].append({'type':'text','text':'A different human request'})
    path=next((Path(f.config['claude_home'])/'projects').glob('*/'+hold['session']+'.jsonl'))
    with path.open('a') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')


def question(f):
    f.results['claude']=domain(outcome='question',question='Qual regra usar?')
    job=enqueue(f);f.drain()
    return job,copy.deepcopy(f.q.mr(11,82)['hold'])


def test_recorded_parallel_human_answer_preserves_then_releases_original_hold(flow):
    f=flow;job,hold=question(f);append_answer(f,hold)
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    record=f.q.mr(11,82)
    assert record['hold']==hold and record['pending_answers'][0]['source']['source_id']==SOURCE
    assert f.q.job(job['id'])['wait_reason']=='answer_ready' and f.sends==[]
    f.results['claude']=domain();f.drain()
    assert f.q.mr(11,82)['hold'] is None
    assert f.q.mr(11,82)['hold_history'][0]['answer']['source_id']==SOURCE
    assert f.sends==[]


def test_mixed_parallel_human_result_cannot_release_original_hold(flow):
    f=flow;job,hold=question(f);append_answer(f,hold,mixed=True)
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    record=f.q.mr(11,82)
    assert record['hold']==hold and record.get('pending_answers',[])==[]
    assert f.q.job(job['id'])['wait_reason']=='human' and f.sends==[]


@pytest.mark.parametrize('change,expected',[
    ('message_missing','invalid Claude assistant message identity'),
    ('message_empty','invalid Claude assistant message identity'),
    ('message_type','invalid Claude assistant message identity'),
    ('content_null','invalid Claude assistant content'),
    ('content_string','invalid Claude assistant content'),
    ('content_block','invalid Claude assistant content'),
    ('call_missing','invalid Claude tool call identity'),
    ('call_empty','invalid Claude tool call identity'),
    ('call_type','invalid Claude tool call identity'),
    ('call_duplicate','invalid Claude tool call identity')])
def test_malformed_sibling_call_cannot_silently_remove_message_obligations(module,change,expected):
    rows,lookup=parallel_rows(tip='a');message=lookup[uid('call-b')]['message']
    if change=='message_missing':message.pop('id')
    elif change=='message_empty':message['id']=''
    elif change=='message_type':message['id']=17
    elif change=='content_null':message['content']=None
    elif change=='content_string':message['content']='Invalid native content'
    elif change=='content_block':message['content']=[17]
    elif change=='call_missing':message['content'][0].pop('id')
    elif change=='call_empty':message['content'][0]['id']=''
    elif change=='call_type':message['content'][0]['id']=17
    else:message['content'].append(copy.deepcopy(message['content'][0]))
    with pytest.raises(RuntimeError,match=expected):module['mq_claude_final'](rows,rows[0])


@pytest.mark.parametrize('record,tip',[('call-b','a'),('return-a','b')])
def test_connected_parallel_node_cannot_reuse_original_source_uuid(module,record,tip):
    rows,lookup=parallel_rows(tip=tip);lookup[uid(record)]['uuid']=SOURCE
    with pytest.raises(RuntimeError,match='duplicate Claude native record identity'):
        module['mq_claude_final'](rows,rows[0])
