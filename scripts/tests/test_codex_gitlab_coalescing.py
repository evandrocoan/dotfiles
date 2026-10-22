"""Automatic-event coalescing through real queue transactions and worker adapters."""
import copy
import json
from pathlib import Path
import threading

import pytest

from test_codex_gitlab_queue import domain, flow, module, queue


def automatic(q, key, *, kind='code', head='a'*40, repository=11, iid=82, context=None, reviewers=None):
    source={'origin':'automatic',**({'head':head} if kind=='code' else {'notes':key})}
    return q.enqueue(repository,iid,source_key=key,kind=kind,head=head,source=source,
        context=copy.deepcopy(context or {'head':head}),reviewers=reviewers)


@pytest.mark.parametrize('first_kind',['code','discussion'])
def test_pending_events_use_oldest_slot_latest_target_and_original_identities(queue,module,first_kind):
    first=automatic(queue,'first',kind=first_kind)
    other=automatic(queue,'other',iid=90)
    code=automatic(queue,'new-code',head='b'*40)
    last=automatic(queue,'latest-comments',kind='discussion',head='b'*40)
    saved=queue.job(first['id'])
    assert [j['id'] for j in queue.jobs('pending')]==[first['id'],other['id']]
    assert (saved['kind'],saved['head'])==('code','b'*40)
    assert saved['source']==first['source']
    assert saved['admission']=={'kind':first_kind,'head':'a'*40,'source':first['source']}
    assert saved['coalesced_jobs']==[code['id'],last['id']]
    assert saved['target_event']==code['id']
    for original in [code,last]:
        row=queue.job(original['id'])
        assert row['coalesced_into']==first['id'] and row['outcome']=='coalesced; not reviewed'
        assert row['stages']==[] and row['source']==original['source']
        assert row['completed_at']==original['completed_at']
    assert queue.mr(11,82)['reviewed_head'] is None
    reopened=module['MonitorQueue'](queue.config)
    try:
        for key,kind,head,original in [('first',first_kind,'a'*40,first),('new-code','code','b'*40,code),
                ('latest-comments','discussion','b'*40,last)]:
            repeated=automatic(reopened,key,kind=kind,head=head)
            assert repeated['id']==original['id']
        assert len(reopened.jobs())==4
        active=reopened.reserve({11});assert active['id']==first['id']
        reopened.finish(active,'fixture administrative finish')
        assert reopened.reserve({11})['id']==other['id']
    finally:reopened.close()


def test_same_discussion_source_with_changed_head_is_not_a_repeat(queue):
    automatic(queue,'discussion',kind='discussion')
    automatic(queue,'code',head='b'*40)
    with pytest.raises(RuntimeError,match='repeated source identity changed'):
        automatic(queue,'discussion',kind='discussion',head='b'*40)


def test_discussion_at_new_head_does_not_invent_code_provenance(queue):
    first=automatic(queue,'old-code')
    latest=automatic(queue,'new-discussion',kind='discussion',head='b'*40)
    active=queue.reserve({11})
    assert (active['id'],active['kind'],active['head'],active['target_event'])==(first['id'],'discussion','b'*40,latest['id'])
    for reviewer in active['reviewers']:
        stage=queue.stage_start(active,reviewer,'fixture')
        queue.stage_end(active,stage['id'],result={'head':'b'*40,'outcome':'complete'},terminal=True)
    with pytest.raises(RuntimeError,match='only actual completed code review'):
        queue.finish(active,'not code',reviewed=True)
    assert queue.mr(11,82)['reviewed_head'] is None


@pytest.mark.parametrize('barrier',['human','policy','prepared','history','hold','effect','retry'])
def test_same_mr_boundaries_preserve_independent_work(queue,barrier):
    first=automatic(queue,'first')
    if barrier=='human':
        middle=queue.enqueue(11,82,source_key='human',kind='human',head='a'*40,
            source={'origin':'human','texts':['reply to this thread']},context={})
    elif barrier=='policy':middle=automatic(queue,'different-policy',reviewers=['codex'])
    else:
        active=queue.reserve({11});queue.finish(active,'setup separates the first segment')
        middle=automatic(queue,'protected')
        with queue.atomic():
            if barrier=='prepared':middle['prepared']={'outcome':'complete'}
            if barrier=='history':middle['rounds']=[{'stages':[]}]
            if barrier=='retry':middle.update(wait_reason='retry',retry_at=9999999999)
            if barrier=='hold':
                record=queue.mr(11,82);record['hold']={'job_id':middle['id'],'question':'original'};queue.put_mr(record)
            if barrier=='effect':queue.put_effect({'key':'fixture-effect','job_id':middle['id'],
                'repository_id':11,'iid':82,'head':'a'*40,'body':'fixture','kind':'reply',
                'target_discussion':'d','position':None,'state':'sending'})
            queue.save(middle)
    before=copy.deepcopy(queue.job(middle['id']))
    last=automatic(queue,'after-boundary')
    assert queue.job(middle['id'])==before
    assert queue.job(last['id'])['state']=='pending'
    assert not queue.job(last['id']).get('coalesced_into')
    assert not queue.job(first['id']).get('coalesced_jobs')


def test_repository_identity_is_part_of_group_key(queue):
    one=automatic(queue,'one',repository=11)
    two=automatic(queue,'two',repository=22)
    automatic(queue,'more-one',repository=11,kind='discussion')
    assert [j['id'] for j in queue.jobs('pending')]==[one['id'],two['id']]
    assert queue.job(two['id'])['source']==two['source']


def test_reservation_stays_frozen_after_return_to_pending(queue):
    first=automatic(queue,'first');active=queue.reserve({11})
    queue.park(active,None)
    later=automatic(queue,'later',kind='discussion')
    assert queue.job(first['id'])['coalescing_frozen'] is True
    assert queue.job(first['id'])['head']=='a'*40 and not queue.job(first['id']).get('coalesced_jobs')
    assert queue.job(later['id'])['state']=='pending' and not queue.job(later['id']).get('coalesced_into')


def test_recorded_queue_artifact_is_normalized_by_reservation(queue,module):
    capture=json.loads((Path(__file__).parent/'fixtures'/'gitlab-pending-events.json').read_text())
    assert capture['capture_kind']=='recorded-artifact'
    originals=[]
    # Seed pre-upgrade event data in MonitorQueue's actual schema; no grouping decision is copied.
    for event in capture['events']:
        row=queue.enqueue(capture['repository_id'],capture['iid'],source_key=event['source_key'],
            kind=event['kind'],head=event['head'],source={'origin':'fixture-seed'},context={'head':event['head']})
        originals.append(row)
    with queue.atomic():
        for row,event in zip(originals,capture['events']):
            row['source']=event['source'];queue.save(row)
    assert len(queue.jobs('pending'))==3
    active=queue.reserve({capture['repository_id']})
    assert active['id']==originals[0]['id'] and active['kind']=='code'
    assert active['coalesced_jobs']==[j['id'] for j in originals[1:]]
    assert len(queue.jobs())==3 and queue.jobs('pending')==[]
    status=module['mq_job_status'](active)
    assert status['admission']['head']==capture['events'][0]['head']
    assert status['coalesced_jobs']==active['coalesced_jobs']
    assert module['mq_job_status'](queue.job(originals[1]['id']))['coalesced_into']==active['id']


def test_failed_coalescing_transaction_leaves_original_queue_intact(queue,monkeypatch):
    automatic(queue,'original');before=queue.jobs();save=queue.save
    def interrupted(job):
        if job.get('coalesced_into'):raise InterruptedError('injected before administrative write')
        return save(job)
    monkeypatch.setattr(queue,'save',interrupted)
    with pytest.raises(InterruptedError,match='injected before administrative write'):
        automatic(queue,'second',kind='discussion')
    assert queue.jobs()==before and queue.effects()==[]


@pytest.mark.parametrize('first_operation',['enqueue','reserve'])
def test_competing_connections_freeze_before_or_after_enqueue(queue,module,first_operation):
    first=automatic(queue,'first');locked=threading.Event();release=threading.Event()
    ready=threading.Barrier(3);attempted=threading.Event();results={};failures=[]
    def operation(name):
        from contextlib import contextmanager
        local=module['MonitorQueue'](queue.config)
        original=local.atomic
        @contextmanager
        def gate():
            with original():
                if name==first_operation:
                    locked.set();assert release.wait(5)
                yield
        try:
            local.atomic=gate;ready.wait(5)
            if name!=first_operation:
                assert locked.wait(5);attempted.set()
            results[name]=automatic(local,'new-code',head='b'*40) if name=='enqueue' else local.reserve({11})
        except BaseException as error:failures.append(error)
        finally:local.close()
    workers=[threading.Thread(target=operation,args=(name,)) for name in ['enqueue','reserve']]
    for worker in workers:worker.start()
    ready.wait(5)
    try:assert attempted.wait(5)
    finally:release.set()
    for worker in workers:worker.join(8);assert not worker.is_alive()
    assert failures==[]
    active=queue.job(first['id']);new=queue.job(results['enqueue']['id'])
    if first_operation=='enqueue':
        assert active['head']=='b'*40 and new['coalesced_into']==active['id']
        assert len(queue.jobs('pending'))==0
    else:
        assert active['head']=='a'*40 and new['state']=='pending'
        assert not active.get('coalesced_jobs')
    assert active['state']=='running' and results['reserve']['id']==first['id']


@pytest.mark.parametrize('first_kind',['code','discussion'])
def test_ten_events_run_each_configured_reviewer_only_once(flow,first_kind):
    old=copy.deepcopy(flow.context)
    first=automatic(flow.q,'first',kind=first_kind,context=old)
    latest=copy.deepcopy(old);latest['head']='b'*40;latest['mr']['sha']='b'*40
    latest['mr']['diff_refs']['head_sha']='b'*40;latest['diff']['head_commit_sha']='b'*40
    latest['threads']=[{'id':'current-discussion','notes':[{'id':100,'body':'latest authenticated comment',
        'author':{'id':8},'system':False,'created_at':'2026-10-20T12:00:00Z','resolvable':True,'resolved':False}]}]
    flow.context.update(latest)
    code=automatic(flow.q,'code',head='b'*40,context=latest)
    for i in range(8):automatic(flow.q,'comment-'+str(i),kind='discussion',head='b'*40,context=latest)
    for reviewer in ['claude','codex']:
        result=domain();result['head']='b'*40;flow.results[reviewer]=result
    flow.drain(limit=100)
    assert flow.launched==['claude','codex'] and flow.sends==[]
    saved=flow.q.job(first['id'])
    assert saved['outcome']=='reviewed' and len(saved['coalesced_jobs'])==9
    assert flow.q.mr(11,82)['reviewed_head']=='b'*40
    for stage in saved['stages']:
        data=stage['input_context']
        assert data['original_source']==code['source']
        assert data['head']=='b'*40 and data['kind']=='code'
        assert 'context' not in data # Context is read through tools when needed.
        assert 'coalesced_jobs' not in data


def test_arrivals_preserve_accepted_input_and_form_one_followup(flow):
    first=automatic(flow.q,'first',context=flow.context)
    flow.step()
    frozen=copy.deepcopy(flow.q.job(first['id']))
    stage=frozen['stages'][0];before=stage['input']
    later=automatic(flow.q,'later',kind='discussion',context=flow.context)
    automatic(flow.q,'more-later',kind='discussion',context=flow.context)
    assert flow.q.job(first['id'])==frozen and flow.q.job(first['id'])['stages'][0]['input']==before
    assert [j['id'] for j in flow.q.jobs('pending')]==[later['id']]
    flow.drain()
    assert flow.launched==['claude','codex','claude','codex']
    assert flow.q.job(later['id'])['state']=='completed' and flow.sends==[]


@pytest.mark.parametrize('state',['closed','merged'])
def test_grouped_review_still_blocks_closed_or_merged_mr(flow,state):
    first=automatic(flow.q,'first',context=flow.context)
    automatic(flow.q,'comments',kind='discussion',context=flow.context)
    flow.context['mr']['state']=state;flow.drain()
    assert flow.q.job(first['id'])['outcome']=='MR closed or merged'
    assert flow.launched==[] and flow.sends==[]
    assert flow.q.mr(11,82)['reviewed_head'] is None


def test_grouped_review_rejects_changed_head_before_publication(flow):
    first=automatic(flow.q,'first',context=flow.context)
    automatic(flow.q,'comments',kind='discussion',context=flow.context)
    for _ in range(4):flow.step()
    assert flow.launched==['claude','codex']
    flow.context['head']='d'*40;flow.context['mr']['sha']='d'*40
    flow.step()
    assert flow.sends==[] and flow.q.mr(11,82)['reviewed_head'] is None
    flow.drain()
    assert flow.q.job(first['id'])['outcome']=='context changed; completed publications preserved'


def test_failed_group_retries_without_recreating_absorbed_work(flow,monkeypatch):
    first=automatic(flow.q,'first',context=flow.context)
    automatic(flow.q,'comments',kind='discussion',context=flow.context)
    flow.results.update(claude=RuntimeError('terminal'),codex=RuntimeError('terminal'));flow.drain()
    failed=flow.q.job(first['id'])
    assert failed['wait_reason']=='reviewer_retry' and len(failed['coalesced_jobs'])==1
    assert flow.q.mr(11,82)['reviewed_head'] is None and len(flow.q.jobs('pending'))==1
    monkeypatch.setitem(flow.m,'mq_stamp',lambda:failed['retry_at']+1)
    flow.results.update(claude=domain(),codex=domain());flow.drain()
    assert flow.launched==['claude','codex','claude','codex']
    assert flow.q.job(first['id'])['outcome']=='reviewed' and len(flow.q.jobs())==2
    assert flow.q.mr(11,82)['reviewed_head']=='a'*40 and flow.sends==[]


def test_restart_keeps_grouped_input_and_publishes_once(flow):
    first=automatic(flow.q,'first',kind='discussion',context=flow.context)
    automatic(flow.q,'code',context=flow.context)
    action={'key':'subtraction','kind':'finding','body':'[P2] Subtraia o desconto.',
        'position':{'position_type':'text','base_sha':'b'*40,'start_sha':'c'*40,'head_sha':'a'*40,
            'old_path':'x.py','new_path':'x.py','new_line':1}}
    flow.results['codex']=domain(actions=[action])
    flow.step()
    accepted=copy.deepcopy(flow.q.job(first['id']))
    stage=accepted['stages'][0];before=stage['input']
    reopened=flow.m['MonitorQueue'](flow.config)
    try:
        assert reopened.job(first['id'])==accepted
        for _ in range(12):
            if not flow.step(reopened):break
        assert reopened.job(first['id'])['outcome']=='reviewed'
        assert reopened.effects()==[] and reopened.mr(11,82)['own_outputs']
        assert not flow.step(reopened)
    finally:reopened.close()
    assert flow.q.job(first['id'])['stages'][0]['input']==before and flow.launched==['claude','codex']
    assert len(flow.sends)==1


def test_flattened_prior_group_keeps_code_provenance_after_barrier_finishes(queue):
    first=automatic(queue,'old-discussion',kind='discussion')
    barrier=queue.enqueue(11,82,source_key='explanation',kind='intake',head='a'*40,
        source={'origin':'human','texts':['explain this']},context={})
    code=automatic(queue,'new-code',head='b'*40)
    tail=automatic(queue,'new-comments',kind='discussion',head='b'*40)
    with queue.atomic():
        record=queue.mr(11,82);record['hold']={'job_id':'original-held-work','question':'original question'}
        queue.put_mr(record)
    active=queue.reserve({11});assert active['id']==barrier['id']
    queue.finish(active,'fixture read-only explanation')
    assert queue.reserve({11}) is None
    grouped=queue.job(first['id'])
    assert grouped['coalesced_jobs']==[code['id'],tail['id']]
    assert (grouped['kind'],grouped['head'],grouped['target_event'])==('code','b'*40,code['id'])
    assert queue.job(code['id'])['coalesced_into']==first['id']
    assert queue.job(tail['id'])['coalesced_into']==first['id']
    assert queue.mr(11,82)['hold']==record['hold'] and queue.mr(11,82)['reviewed_head'] is None
