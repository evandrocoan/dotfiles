"""Unread notifications through the real periodic consumer; only native/app I/O is fake."""
import copy
import json
from contextlib import nullcontext

import pytest

from test_codex_gitlab_queue import domain, flow, human_turn, module


@pytest.fixture
def notifications(flow,monkeypatch):
    monkeypatch.setitem(flow.m,'mq_inventory',lambda *args:True)
    return flow


def enqueue(f,key='first'):
    return f.q.enqueue(11,82,source_key=key,kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context))


def complete(f):
    for _ in range(4):
        f.tick()
        if not f.q.jobs('running') and not any(j['wait_reason'] is None for j in f.q.jobs('pending')):
            return
    pytest.fail('fixture review did not finish or hold')


def test_new_result_marks_once_across_ticks_and_a_later_result_marks_again(notifications):
    f=notifications;first=enqueue(f);complete(f)
    session=f.q.mr(11,82)['chats']['codex']
    assert f.q.job(first['id'])['state']=='completed'
    assert f.unread_calls==[session] and f.app_read[session] is False
    f.app_read[session]=True # The person opens the chat after the acknowledged notification.
    f.tick();f.tick()
    assert f.unread_calls==[session] and f.app_read[session] is True
    enqueue(f,'second');complete(f)
    assert f.q.mr(11,82)['chats']['codex']==session
    assert f.unread_calls==[session,session] and f.app_read[session] is False
    assert f.sends==[]


def test_question_and_its_actual_native_completion_each_notify_once(notifications):
    f=notifications;f.results['codex']=domain(outcome='question',question='Qual regra usar?')
    job=enqueue(f);complete(f)
    hold=f.q.mr(11,82)['hold'];session=hold['session']
    assert f.unread_calls==[session]
    original=copy.deepcopy(f.q.job(job['id'])['stages'][-1])
    f.app_read[session]=True
    source=human_turn(f,'use a regra atual e continue')
    f.items[source['turn_id']].append({'type':'agentMessage','id':'human-completion',
        'phase':'final_answer','text':'Commit revisado: '+'a'*40+'\nEstado da revisão: concluída'})
    f.tick();f.tick()
    saved=f.q.job(job['id'])
    assert f.q.mr(11,82)['hold'] is None and saved['state']=='completed'
    assert saved['stages'][-1]['anchor']==original['anchor']
    assert f.unread_calls==[session,session] and f.app_read[session] is False


@pytest.mark.parametrize('failure',['transport','isError','json','wrong_thread','read_true'])
def test_notification_failure_never_blocks_review_and_retries_after_reopen(notifications,monkeypatch,failure):
    f=notifications;native=f.m['monitor_native'];attempts=[]
    def broken(c,method,params,**kw):
        if method=='mcpServer/tool/call':
            attempts.append(params)
            if failure=='transport':raise RuntimeError('app temporarily unavailable')
            if failure=='isError':return {'isError':True,'content':[{'type':'text','text':'app unavailable'}]}
            if failure=='json':return {'content':[{'type':'text','text':'not JSON'}]}
            ack={'threadId':params['threadId'],'hostId':'local','read':False}
            ack.update({'threadId':'another-chat'} if failure=='wrong_thread' else {'read':True})
            return {'content':[{'type':'text','text':json.dumps(ack)}]}
        return native(c,method,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',broken)
    job=enqueue(f);complete(f)
    session=f.q.mr(11,82)['chats']['codex']
    assert f.q.job(job['id'])['state']=='completed'
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert attempts and f.unread_calls==[]
    assert f.q.meta('unread_error:'+session)['error']
    monkeypatch.setitem(f.m,'monitor_native',native)
    f.tick();f.tick() # Each actual tick reopens the durable SQLite queue.
    assert f.unread_calls==[session] and f.app_read[session] is False
    assert f.q.meta('unread_error:'+session) is None
    assert f.sends==[]


def test_active_chat_defers_ui_work_until_idle_without_reloading_it(notifications,monkeypatch):
    f=notifications;job=enqueue(f);f.drain()
    session=f.q.mr(11,82)['chats']['codex'];native=f.m['monitor_native'];resumes=[]
    def wire(c,method,params,**kw):
        if method=='thread/resume':resumes.append(params)
        return native(c,method,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',wire)
    f.chats[session]['status']={'type':'active'}
    f.tick()
    assert f.unread_calls==[] and resumes==[]
    assert f.q.job(job['id'])['state']=='completed'
    f.chats[session]['status']={'type':'idle'}
    f.tick()
    assert f.unread_calls==[session]
    assert len(resumes)==1
    override=resumes[0]['config']
    assert override=={'plugins.codex-app-tools@openai-bundled.mcp_servers.codex_app.enabled':True}
    assert 'developerInstructions' not in resumes[0] and f.sends==[]


def test_prior_results_without_pending_notification_are_not_retroactively_marked(notifications):
    f=notifications;enqueue(f);f.drain()
    session=f.q.mr(11,82)['chats']['codex']
    # This is the exact persisted boundary of an older consumer, with no UI notification record.
    with f.q.atomic():f.q.set_meta('app_unread:'+session,None)
    f.app_read[session]=True
    f.tick()
    assert f.unread_calls==[] and f.app_read[session] is True


def test_notification_budget_exhaustion_preserves_pending_result_for_next_tick(notifications,monkeypatch):
    f=notifications;native=f.m['monitor_native']
    def exhausted(c,method,params,**kw):
        if method=='mcpServer/tool/call':raise f.m['MonitorCycleYield']('app exceeded its bounded time')
        return native(c,method,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',exhausted)
    job=enqueue(f);complete(f)
    session=f.q.mr(11,82)['chats']['codex']
    assert f.q.job(job['id'])['state']=='completed' and f.unread_calls==[]
    monkeypatch.setitem(f.m,'monitor_native',native)
    f.tick()
    assert f.unread_calls==[session]


def test_provider_failure_without_native_final_creates_no_unread_notice(notifications):
    f=notifications;f.results['codex']=RuntimeError('provider failed without a final')
    job=enqueue(f);complete(f)
    assert f.q.job(job['id'])['wait_reason']=='reviewer_retry'
    assert f.unread_calls==[]


@pytest.mark.parametrize('text',['A revisão parou.\nEstado da revisão: não concluída','Resultado sem status válido.'])
def test_readable_failure_final_is_a_new_result_even_when_review_needs_retry(notifications,text):
    f=notifications;job=enqueue(f)
    f.tick();f.tick()
    session=f.q.mr(11,82)['chats']['codex'];turn=f.turns[session][0]['id']
    f.items[turn][-1]['text']=text
    f.tick()
    assert f.q.job(job['id'])['wait_reason']=='reviewer_retry'
    assert f.unread_calls==[session]


@pytest.mark.parametrize('method',['thread/read','thread/resume'])
def test_mismatched_native_chat_never_marks_a_foreign_thread(notifications,monkeypatch,method):
    f=notifications;enqueue(f);f.drain();native=f.m['monitor_native']
    session=f.q.mr(11,82)['chats']['codex']
    def wrong(c,name,params,**kw):
        if name==method:
            response={'thread':{'id':'foreign','status':{'type':'idle'}}}
            if kw.get('followup'):
                import asyncio
                async def request(*args):pytest.fail('foreign chat reached the app write')
                return asyncio.run(kw['followup'](request,response))
            return response
        return native(c,name,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',wrong)
    f.tick()
    assert f.unread_calls==[]
    assert 'chat' in f.q.meta('unread_error:'+session)['error']


def test_interruption_keeps_notice_durable_for_the_next_consumer(notifications,monkeypatch):
    f=notifications;enqueue(f);f.drain();native=f.m['monitor_native']
    session=f.q.mr(11,82)['chats']['codex']
    def interrupted(c,method,params,**kw):
        if method=='mcpServer/tool/call':raise InterruptedError('consumer interrupted')
        return native(c,method,params,**kw)
    monkeypatch.setitem(f.m,'monitor_native',interrupted)
    with pytest.raises(InterruptedError,match='consumer interrupted'):f.tick()
    assert f.unread_calls==[]
    monkeypatch.setitem(f.m,'monitor_native',native)
    f.tick();f.tick()
    assert f.unread_calls==[session]


@pytest.mark.parametrize('error,expectation',[
    (RuntimeError('socket close failed'),nullcontext()),
    (InterruptedError('interrupted after ack'),pytest.raises(InterruptedError,match='interrupted after ack'))])
def test_confirmed_ack_survives_transport_cleanup_failure_without_marking_again(notifications,monkeypatch,error,expectation):
    f=notifications;enqueue(f);f.drain();native=f.m['monitor_native']
    session=f.q.mr(11,82)['chats']['codex']
    def cleanup_failure(c,method,params,**kw):
        result=native(c,method,params,**kw)
        if method=='thread/resume':raise error
        return result
    monkeypatch.setitem(f.m,'monitor_native',cleanup_failure)
    with expectation:f.tick()
    assert f.unread_calls==[session] and f.q.meta('app_unread:'+session)['pending'] is False
    f.app_read[session]=True
    monkeypatch.setitem(f.m,'monitor_native',native)
    f.tick();f.tick()
    assert f.unread_calls==[session] and f.app_read[session] is True
    assert f.q.meta('unread_error:'+session) is None
