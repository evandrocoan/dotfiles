"""Operator MR abandonment through the real SQLite/worker controls; no public effects."""
import copy
import json
import os

import pytest
from test_codex_gitlab_queue import module, flow, domain
from test_codex_gitlab_visible_requests import automatic, held, human


def restart(f,job,reason='Abandon legacy chats and review the current MR again'):
    return f.m['mq_restart_mr'](f.config,job['id'],reason)


def effect(f,job,key='uncertain',state='unknown'):
    value={'key':key,'repository_id':11,'iid':82,'head':job['head'],'kind':'finding',
        'body':'historical finding','actor_id':7,'discussion':None,'job_id':job['id'],'state':state}
    with f.q.atomic():f.q.put_effect(value)
    return value


def snapshot(f):
    return copy.deepcopy((f.q.jobs(),f.q.mrs(),f.q.effects()))


def head(f,value):
    f.context['head']=value
    f.context['mr']['sha']=value
    f.context['mr']['diff_refs']['head_sha']=value
    f.context['diff']['head_commit_sha']=value


def test_mr78_multiple_issued_and_grouped_jobs_become_one_fresh_full_round(flow):
    f=flow;f.results['claude']=RuntimeError('provider failed')
    first=automatic(f);f.drain()
    assert f.q.job(first['id'])['wait_reason']=='reviewer_retry'
    f.results['codex']=domain(outcome='question',question='Old operational question?')
    root=f.q.enqueue(11,82,source_key='discussion',kind='discussion',head='a'*40,
        source={'origin':'automatic','notes':'old'},context=copy.deepcopy(f.context))
    f.drain();root=f.q.job(root['id']);old_hold=copy.deepcopy(f.q.mr(11,82)['hold'])
    retry=f.q.enqueue(11,82,source_key='unissued-retry',kind='code',head='d'*40,
        source={'origin':'automatic','head':'d'*40},context=copy.deepcopy(f.context))
    with f.q.atomic():
        retry.update(wait_reason='retry',retry_at=10**12);f.q.save(retry)
    latest=f.q.enqueue(11,82,source_key='latest-code',kind='code',head='f'*40,
        source={'origin':'automatic','head':'f'*40},context=copy.deepcopy(f.context))
    child=f.q.enqueue(11,82,source_key='latest-discussion',kind='discussion',head='f'*40,
        source={'origin':'automatic','notes':'latest'},context=copy.deepcopy(f.context))
    assert f.q.job(child['id'])['coalesced_into']==latest['id']
    old_jobs=copy.deepcopy(f.q.jobs());old_checkpoint=f.q.mr(11,82)['reviewed_head']
    old_effect=effect(f,root)
    with f.q.atomic():
        value=f.q.job(root['id'])
        value.update(scope={'effects':['reply'],'discussions':['old']},answers=[{'origin':'human','texts':['old answer']}],
            validation_error='old diagnostic',review_attempt={'start':0,'reviewers':['codex']})
        f.q.save(value)
    head(f,'f'*40)
    receipt=restart(f,root);saved=f.q.job(root['id']);record=f.q.mr(11,82)
    assert len(f.q.jobs('pending'))==1 and saved['sequence']==receipt['sequence']
    assert set(receipt['retired_jobs'])=={first['id'],root['id'],retry['id'],latest['id']}
    assert receipt['head']=='f'*40 and saved['head']=='f'*40 and saved['kind']=='code'
    assert f.q.admission(saved)==f.q.admission(root) and f.q.admission(saved)['kind']=='discussion'
    assert not any(saved.get(k) for k in ('scope','answers','review_attempt','target_event','coalesced_jobs','stages','workspace'))
    assert record['hold'] is None and record['chats']=={} and record['reviewed_head']==old_checkpoint
    assert record['retired_questions'][-1]['question']==old_hold
    assert f.q.job(child['id'])['coalesced_into']==latest['id']
    for previous in old_jobs:
        if previous['state']!='pending':continue
        archived=f.q.job(previous['id'])['rounds'][-1]
        assert archived['stages']==previous['stages']
        assert f.q.admission(archived)==f.q.admission(previous)
    abandoned=f.q.effect('uncertain')
    assert abandoned=={**old_effect,'state':'abandoned','abandoned_from':'unknown','operator_abandonment':receipt}
    assert receipt['effect_states']=={'uncertain':'unknown'} and not f.m['mq_tool_uncertain'](f.q,saved)
    f.results.update(claude={**domain(),'head':'f'*40},codex={**domain(),'head':'f'*40});f.drain()
    done=f.q.job(root['id'])
    assert done['outcome']=='reviewed' and f.q.mr(11,82)['reviewed_head']=='f'*40
    assert f.launched==['claude','codex','claude','codex','claude','codex']
    assert done['stages'][1]['session']!=old_hold['session']
    for stage in done['stages']:
        context=f.m['mq_input_context'](f.q,stage)
        assert context['original_source']['origin']=='operator' and context['head']=='f'*40
        assert context['answers']==[] and context['hold'] is None and not context['scope']
        assert stage['instructions_version']==f.m['MQ_INSTRUCTIONS_VERSION']
        assert stage['id'] not in {s['id'] for j in old_jobs for s in j['stages']}
    assert not f.sends


def test_mr18_complete_old_results_and_unknown_effect_can_restart_without_a_question(flow,monkeypatch):
    f=flow;job=automatic(f);f.drain();old=f.q.job(job['id'])
    assert old['outcome']=='reviewed' and not f.q.mr(11,82)['hold']
    with f.q.atomic():
        old.update(state='pending',outcome=None,wait_reason='effect_unknown');f.q.save(old)
    effect(f,old)
    def forbidden(*args):raise AssertionError('operator reset must not read-back or resend old public effects')
    monkeypatch.setitem(f.m,'mq_readback',forbidden)
    head(f,'e'*40);restart(f,old)
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert f.q.effect('uncertain')['state']=='abandoned'
    f.results.update(claude={**domain(),'head':'e'*40},codex={**domain(),'head':'e'*40});f.drain()
    assert f.q.mr(11,82)['reviewed_head']=='e'*40 and not f.sends


def test_cli_repetition_after_reopen_does_not_consume_later_arrivals(flow,monkeypatch,capsys):
    f=flow;job,_=held(f)
    monkeypatch.setattr('sys.argv',['codex-session-stats','monitor-gitlab','--config',str(f.config_path),
        'restart-mr',job['id'],'--reason','explicit operator restart'])
    assert f.m['mq_main']()==0
    receipt=json.loads(capsys.readouterr().out)
    later=f.q.enqueue(11,82,source_key='later',kind='discussion',head='a'*40,
        source={'origin':'automatic','notes':'new arrival'},context=f.context)
    before=snapshot(f)
    assert f.m['mq_main']()==0 and json.loads(capsys.readouterr().out)==receipt
    assert snapshot(f)==before and f.q.job(later['id'])['state']=='pending'
    with pytest.raises(RuntimeError,match='differs from recorded'):restart(f,job,'different reason')
    assert snapshot(f)==before and not f.sends


@pytest.mark.parametrize('denial',['closed','merged','removed','native_active','native_unknown','chat_active',
    'claude_descendants','pending_answer','human','intake','presentation','foreign_effect','prior_round'])
def test_denials_preserve_all_protected_state(flow,denial):
    f=flow;job,hold=held(f)
    if denial in {'closed','merged'}:f.context['mr']['state']=denial
    elif denial=='removed':f.config['projects']=[{'id':99,'path':'other/repo'}]
    elif denial=='native_active':f.turns[hold['session']][0]['status']='inProgress'
    elif denial=='native_unknown':f.turns[hold['session']]=[]
    elif denial=='chat_active':f.chats[hold['session']]['status']['type']='active'
    elif denial=='claude_descendants':f.service.populated=True
    elif denial=='pending_answer':
        with f.q.atomic():
            record=f.q.mr(11,82);record['pending_answers']=[{'source':'real answer'}];f.q.put_mr(record)
    elif denial in {'human','intake','presentation'}:
        f.q.enqueue(11,82,source_key='independent-human',kind=denial,head='a'*40,
            source={'origin':'human','texts':['independent request']},context=f.context)
    elif denial=='foreign_effect':effect(f,{'id':'outside-scope','head':'a'*40})
    elif denial=='prior_round':
        with f.q.atomic():
            value=f.q.job(job['id']);value['rounds']=[{'reason':'previous','stages':value['stages'],
                'workspace':value['workspace'],'batch':value['batch']}];value['stages']=[];f.q.save(value)
        f.turns[hold['session']][0]['status']='inProgress'
    before=snapshot(f)
    with pytest.raises(RuntimeError):restart(f,job)
    assert snapshot(f)==before and f.q.meta('operator_mr_restart:'+job['id']) is None and not f.sends


def test_rollback_restores_effects_questions_jobs_and_receipt(flow,monkeypatch):
    f=flow;job,_=held(f);effect(f,job);before=snapshot(f)
    cls=f.m['MonitorQueue'];save=cls.save
    def interrupted(self,value):
        save(self,value)
        if value.get('operator_restart'):raise RuntimeError('interrupted before commit')
    monkeypatch.setattr(cls,'save',interrupted)
    with pytest.raises(RuntimeError,match='before commit'):restart(f,job)
    assert snapshot(f)==before and f.q.meta('operator_mr_restart:'+job['id']) is None
    monkeypatch.setattr(cls,'save',save);receipt=restart(f,job)
    assert receipt['restarted'] and len(f.q.jobs('pending'))==1 and not f.sends


def test_existing_consumer_lock_and_other_running_mr_are_preserved(flow):
    f=flow;job,_=held(f)
    lock=f.m['mq_lock'](f.config,'consumer')
    try:
        with pytest.raises(BlockingIOError):restart(f,job)
    finally:os.close(lock)
    other=f.q.enqueue(11,83,source_key='other',kind='code',head='a'*40,
        source={'origin':'automatic'},context=f.context)
    running=f.q.reserve({11});assert running['id']==other['id']
    restart(f,job)
    assert f.q.jobs('running')==[running] and f.q.reserve({11})==running and not f.sends


def test_enqueue_during_preparation_is_not_silently_abandoned(flow,monkeypatch):
    f=flow;job,_=held(f);context=f.m['mq_context'];arrival=[]
    def read(*args,**kwargs):
        if not arrival:
            arrival.append(f.q.enqueue(11,82,source_key='racing-arrival',kind='discussion',head='a'*40,
                source={'origin':'automatic','notes':'new'},context=f.context))
        return context(*args,**kwargs)
    monkeypatch.setitem(f.m,'mq_context',read)
    with pytest.raises(RuntimeError,match='captured work changed'):restart(f,job)
    assert f.q.job(arrival[0]['id'])['state']=='pending' and f.q.job(job['id'])==job
    assert not f.q.meta('operator_mr_restart:'+job['id']) and not f.sends


def test_identical_inventory_is_quiet_and_later_real_change_is_admitted(flow,monkeypatch):
    f=flow;job,_=held(f);restart(f,job)
    class Inventory:
        def __init__(self,*args,**kwargs):pass
        def project(self):return {'id':11}
        def pages(self,route,start_page=1):yield [{'iid':82}],True
    monkeypatch.setitem(f.m,'MonitorGitLab',Inventory)
    before=f.q.jobs();f.m['mq_inventory'](f.config,f.q)
    assert f.q.jobs()==before
    f.context['threads']=[{'id':'external','notes':[{'id':91,'body':'Human changed this',
        'author':{'id':9},'system':False,'resolved':False,'resolvable':True,
        'created_at':'2026-10-22T01:00:00Z','updated_at':'2026-10-22T01:00:00Z'}]}]
    f.m['mq_inventory'](f.config,f.q)
    pending=f.q.jobs('pending')
    assert len(pending)==2 and pending[-1]['source']['note_delta']['after'][0]['id']==91
    assert pending[-1]['sequence']>pending[0]['sequence'] and not f.sends


def test_late_old_answer_does_not_restore_question_or_create_monitor_work(flow):
    f=flow;job,hold=held(f);restart(f,job)
    human(f,hold,text='continue the old task')
    before=f.q.jobs();f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.jobs()==before and f.q.mr(11,82)['hold'] is None and not f.sends


def test_unproven_abandonment_remains_a_blocking_effect(flow):
    f=flow;job,_=held(f);value=effect(f,job,state='abandoned')
    assert not f.m['mq_effect_settled'](f.q,value)
    assert f.m['mq_tool_uncertain'](f.q,job)==[value]
    with pytest.raises(RuntimeError,match='unsettled public effect'):
        f.m['mq_restart_review'](f.config,job['id'],f.q.mr(11,82)['hold']['stage_id'],'strict restart')
    assert not f.sends


def test_fresh_failure_retries_only_failed_reviewer_despite_retired_effect(flow,monkeypatch):
    f=flow;job,_=held(f);effect(f,job);restart(f,job)
    f.results.update(claude=RuntimeError('new provider failure'),codex=domain());f.drain()
    saved=f.q.job(job['id'])
    assert saved['wait_reason']=='reviewer_retry' and saved['review_attempt']['reviewers']==['claude']
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    now=saved['retry_at']+1;monkeypatch.setitem(f.m,'mq_stamp',lambda:now)
    f.results['claude']=domain();f.drain()
    assert f.launched==['claude','codex','claude','codex','claude']
    assert f.q.job(job['id'])['outcome']=='reviewed' and f.q.effect('uncertain')['state']=='abandoned'


def test_strict_restart_after_new_question_ignores_only_proven_retired_effect(flow):
    f=flow;job,_=held(f);effect(f,job);restart(f,job)
    f.drain();hold=f.q.mr(11,82)['hold']
    result=f.m['mq_restart_review'](f.config,job['id'],hold['stage_id'],'restart this new question')
    assert result['restarted'] and f.q.mr(11,82)['hold'] is None
    assert f.q.effect('uncertain')['abandoned_from']=='unknown' and not f.sends


def test_head_change_between_authenticated_reads_refuses_without_mutation(flow,monkeypatch):
    f=flow;job,_=held(f);read=f.m['mq_context'];calls=[]
    def context(*args,**kwargs):
        calls.append(1)
        if len(calls)==2:head(f,'e'*40)
        return read(*args,**kwargs)
    monkeypatch.setitem(f.m,'mq_context',context);before=snapshot(f)
    with pytest.raises(RuntimeError,match='head/open state changed'):restart(f,job)
    assert snapshot(f)==before and not f.sends


def test_changed_operator_authority_cannot_advance_checkpoint(flow):
    f=flow;job,_=held(f);restart(f,job)
    with f.q.atomic():
        value=f.q.job(job['id']);value['operator_restart']['reason']='forged authority';f.q.save(value)
    value=f.q.reserve({11})
    for reviewer in value['reviewers']:
        stage=f.q.stage_start(value,reviewer,'fixture native input')
        f.q.stage_end(value,stage['id'],result=domain(),terminal=True)
    with pytest.raises(RuntimeError,match='operator review authority changed'):
        f.q.finish(value,'reviewed',reviewed=True)
    assert f.q.mr(11,82)['reviewed_head'] is None and f.q.job(job['id'])['state']=='running'


def test_producer_waits_for_atomic_restart_and_remains_a_later_arrival(flow,monkeypatch):
    import threading
    f=flow;job,_=held(f)
    ready,start,attempted,done=(threading.Event() for _ in range(4))
    errors=[];arrivals=[];cls=f.m['MonitorQueue'];put=cls.put_mr
    def producer():
        q=None
        try:
            q=cls(f.config)
            q.db.set_trace_callback(lambda sql:attempted.set() if sql=='BEGIN IMMEDIATE' else None)
            ready.set();assert start.wait(10)
            arrivals.append(q.enqueue(11,82,source_key='concurrent-later',kind='discussion',head='a'*40,
                source={'origin':'automatic','notes':'later'},context=f.context))
        except BaseException as error:errors.append(error)
        finally:
            if q:q.close()
            done.set()
    thread=threading.Thread(target=producer);thread.start();assert ready.wait(10)
    def blocked(self,record):
        if record.get('operator_retirements'):
            start.set();assert attempted.wait(10)
            assert not done.is_set()
        return put(self,record)
    monkeypatch.setattr(cls,'put_mr',blocked)
    try:receipt=restart(f,job)
    finally:start.set();thread.join(10)
    assert done.is_set() and errors==[]
    assert len(arrivals)==1 and arrivals[0]['id'] not in receipt['retired_jobs']
    assert f.q.job(arrivals[0]['id'])['state']=='pending'
    assert f.q.job(arrivals[0]['id'])['sequence']>receipt['sequence'] and not f.sends
