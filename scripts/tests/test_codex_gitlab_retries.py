"""Selective reviewer retries through the real FIFO/worker; external providers are fixtures."""
import copy
import json
from pathlib import Path

import pytest

from test_codex_gitlab_queue import module, queue, flow, enqueue, domain, human_turn, assessment, compact, resolution_fixture


def automatic(f, **values):
    return f.q.enqueue(11,82,source_key='retry-case',kind='code',head=f.context['head'],
        source={'origin':'automatic','head':f.context['head']},context=copy.deepcopy(f.context),**values)


@pytest.mark.parametrize('reviewers',[['claude','codex'],['codex','claude'],['claude'],['codex']])
@pytest.mark.parametrize('failed_index',[0,-1])
def test_retry_runs_only_missing_reviewer_and_retains_native_history(flow,monkeypatch,reviewers,failed_index):
    f=flow;failed=reviewers[failed_index];f.results[failed]=RuntimeError('arbitrary terminal failure')
    original=automatic(f,reviewers=reviewers);f.drain()
    saved=f.q.job(original['id']);stages=copy.deepcopy(saved['stages'])
    assert f.launched==reviewers and saved['wait_reason']=='reviewer_retry'
    assert saved['review_attempt']=={'start':len(reviewers),'reviewers':[failed]}
    assert saved['original_sequence']==original['sequence'] and saved['sequence']>original['sequence']
    assert saved['source']==original['source'] and saved['head']==original['head']
    assert not f.step() and f.launched==reviewers
    monkeypatch.setitem(f.m,'mq_stamp',lambda:saved['retry_at']+1)
    f.results[failed]=domain();f.drain()
    finished=f.q.job(original['id'])
    assert finished['state']=='completed' and finished['outcome']=='reviewed'
    assert f.launched==reviewers+[failed] and len(f.q.jobs())==1
    assert finished['stages'][:len(stages)]==stages and finished['workspace']==saved['workspace']
    assert f.q.mr(11,82)['reviewed_head']=='a'*40 and not f.sends


def test_repeated_failure_requeues_with_interval_and_no_completed_reviewer_replay(flow,monkeypatch):
    f=flow;f.results['claude']=RuntimeError('network unavailable')
    job=automatic(f);f.drain();first=f.q.job(job['id'])
    monkeypatch.setitem(f.m,'mq_stamp',lambda:first['retry_at']+1)
    f.drain();second=f.q.job(job['id'])
    assert f.launched==['claude','codex','claude']
    assert second['sequence']>first['sequence'] and second['retry_at']>first['retry_at']
    assert second['review_attempt']=={'start':3,'reviewers':['claude']}
    assert second['stages'][1]==first['stages'][1] and len(f.q.jobs())==1
    assert not f.step() and f.launched==['claude','codex','claude']
    monkeypatch.setitem(f.m,'mq_stamp',lambda:second['retry_at']+1)
    f.results['claude']=domain();f.drain()
    assert f.launched==['claude','codex','claude','claude']
    assert f.q.job(job['id'])['state']=='completed'


def test_both_fail_then_each_success_removes_only_its_own_retry(flow,monkeypatch):
    f=flow;f.results.update(claude=RuntimeError('capacity'),codex=RuntimeError('network'))
    original=automatic(f);f.drain();first=f.q.job(original['id'])
    assert first['review_attempt']['reviewers']==['claude','codex']
    assert f.q.mr(11,82)['reviewed_head'] is None
    monkeypatch.setitem(f.m,'mq_stamp',lambda:first['retry_at']+1)
    f.results['claude']=domain();f.drain();second=f.q.job(original['id'])
    assert f.launched==['claude','codex','claude','codex']
    assert second['review_attempt']['reviewers']==['codex']
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    monkeypatch.setitem(f.m,'mq_stamp',lambda:second['retry_at']+1)
    f.results['codex']=domain();f.drain()
    assert f.launched==['claude','codex','claude','codex','codex']
    assert f.q.job(original['id'])['state']=='completed'


def test_retry_model_reads_existing_discussions_after_failed_stage(flow,monkeypatch):
    f=flow
    action={'kind':'finding','body':'A falha concreta.', 'position':{'old_path':'x.py','new_path':'x.py',
        'new_line':1,'position_type':'text','base_sha':'b'*40,'start_sha':'c'*40,'head_sha':'a'*40}}
    f.results['codex']=domain(actions=[action])
    original=automatic(f,reviewers=['codex','claude']);assert f.step()
    first=f.q.job(original['id'])['stages'][0]
    f.turns[first['session']][0].update(status='failed',error='native interruption after publication')
    f.drain();saved=f.q.job(original['id'])
    assert len(f.sends)==1 and saved['review_attempt']['reviewers']==['codex']
    monkeypatch.setitem(f.m,'mq_stamp',lambda:saved['retry_at']+1)
    f.drain()
    assert f.q.job(original['id'])['state']=='completed'
    assert f.launched==['codex','claude','codex'] and len(f.sends)==1
    assert f.q.effects()==[] and f.q.mr(11,82)['own_outputs']


def failed_round(q):
    q.config['interval_minutes']=15
    original=enqueue(q)
    job=q.reserve({11})
    stage=q.stage_start(job,'claude','original Claude input')
    q.stage_end(job,stage['id'],error={'message':'failure'},terminal=True)
    stage=q.stage_start(job,'codex','original Codex input')
    q.stage_end(job,stage['id'],result={'outcome':'complete','head':'a'*40},terminal=True)
    return original,job


def test_tail_order_new_arrivals_and_same_source_after_restart(queue,module,monkeypatch):
    original,job=failed_round(queue)
    older=enqueue(queue,repository=22,marker='older')
    assert queue.requeue_failed(job)
    retry=queue.job(job['id']);later=enqueue(queue,repository=22,marker='later')
    assert [j['id'] for j in queue.jobs()]==[older['id'],retry['id'],later['id']]
    assert enqueue(queue)['id']==original['id'] and len(queue.jobs())==3
    reopened=module['MonitorQueue'](queue.config)
    try:
        first=reopened.reserve({11,22},now=retry['retry_at']+1)
        assert first['id']==older['id'];reopened.finish(first,'test terminal')
        second=reopened.reserve({11,22},now=retry['retry_at']+1)
        assert second['id']==retry['id'] and reopened.next_reviewer(second)=='claude'
        assert second['original_sequence']==original['sequence']
        with pytest.raises(RuntimeError,match='stale retry'):
            reopened.requeue_failed(job)
        assert reopened.job(later['id'])['state']=='pending'
    finally:reopened.close()


def test_requeue_transaction_rolls_back_and_repeated_commit_is_idempotent(queue,monkeypatch):
    original,job=failed_round(queue);before=copy.deepcopy(job);save=queue.save
    def interrupted(value):raise OSError('interrupted before commit')
    monkeypatch.setattr(queue,'save',interrupted)
    with pytest.raises(OSError,match='before commit'):queue.requeue_failed(job)
    assert queue.job(original['id'])==before
    monkeypatch.setattr(queue,'save',save)
    job=queue.job(original['id']);assert queue.requeue_failed(job)
    after=queue.job(job['id'])
    assert not queue.requeue_failed(after)
    assert queue.job(job['id'])==after and len(queue.jobs())==1


@pytest.mark.parametrize('fence',['native','hold','effect','question'])
def test_retry_does_not_release_unknown_execution_or_holds(queue,fence):
    _,job=failed_round(queue)
    with queue.atomic():
        if fence=='native':job['stages'][-1]['state']='running';queue.save(job)
        elif fence=='hold':
            record=queue.mr(11,82);record['hold']={'job_id':job['id'],'anchor':'real question'};queue.put_mr(record)
        elif fence=='question':job['pending_question']={'question':'real question'};queue.save(job)
        else:queue.put_effect({'key':'unknown','repository_id':11,'iid':82,'state':'unknown'})
    before=copy.deepcopy(queue.job(job['id']))
    assert not queue.requeue_failed(before)
    assert queue.job(job['id'])==before


def test_completed_partial_success_is_reopened_once_with_checkpoint_unchanged(flow):
    f=flow;f.results['claude']=RuntimeError('provider capacity')
    original=automatic(f)
    for _ in range(4):assert f.step()
    job=f.q.job(original['id']);f.q.finish(job,'reviewed',reviewed=True)
    old=copy.deepcopy(job)
    assert f.step() is False  # Backfill requeues, but the interval is not yet eligible.
    retry=f.q.job(original['id'])
    assert retry['wait_reason']=='reviewer_retry' and retry['stages']==old['stages']
    assert retry['completion_history']==[{'outcome':'reviewed','completed_at':old['completed_at']}]
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert f.step() is False and f.q.job(original['id'])==retry
    assert f.launched==['claude','codex'] and len(f.q.jobs())==1


@pytest.mark.parametrize('changed',['closed','merged','head'])
def test_retry_rechecks_current_mr_before_dispatch(flow,monkeypatch,changed):
    f=flow;f.results['claude']=RuntimeError('provider failure');original=automatic(f);f.drain()
    saved=f.q.job(original['id']);monkeypatch.setitem(f.m,'mq_stamp',lambda:saved['retry_at']+1)
    if changed=='head':f.context['head']='d'*40
    else:f.context['mr']['state']=changed
    f.drain()
    assert f.q.job(original['id'])['state']=='completed'
    assert f.q.job(original['id'])['outcome']!='reviewed'
    assert f.launched==['claude','codex'] and not f.sends
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert not f.step()  # Do not resurrect the superseded/closed retry.


@pytest.mark.parametrize('kind',['human','discussion'])
def test_changed_head_never_rebinds_a_selective_retry(flow,monkeypatch,kind):
    f=flow;f.results['claude']=RuntimeError('failure')
    if kind=='human':
        source=human_turn(f,'Revise e publique os achados')
        a=assessment(source['texts'][0]);a['scope']={'effects':['finding'],'discussions':[]}
        with f.q.atomic():
            record=f.q.mr(11,82);record.setdefault('instruction_versions',{})[source['session']]=3;f.q.put_mr(record)
        f.items[source['turn_id']].append({'type':'agentMessage','id':'human-final','phase':'final_answer',
            'text':compact(domain(assessment=a))})
        f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));original=f.q.jobs()[0]
    else:
        original=f.q.enqueue(11,82,source_key='discussion',kind=kind,head='a'*40,
            source={'origin':'automatic'},context=f.context)
    f.drain();saved=f.q.job(original['id'])
    assert saved['review_attempt']['reviewers']==['claude']
    monkeypatch.setitem(f.m,'mq_stamp',lambda:saved['retry_at']+1)
    f.context['head']='d'*40;f.drain();finished=f.q.job(original['id'])
    assert finished['outcome']=='superseded by a new head' and finished['head']=='a'*40
    assert finished['stages']==saved['stages'] and finished['source']==saved['source']
    assert f.launched==['claude','codex'] and not f.sends


def test_prepared_claude_inheritance_survives_new_configuration(flow,monkeypatch):
    f=flow;original=automatic(f);command=f.m['mq_service_command']
    def interrupted(c,args):
        if args[0]=='systemd-run':raise f.m['MonitorCycleYield']('before issue')
        return command(c,args)
    monkeypatch.setitem(f.m,'mq_service_command',interrupted)
    with pytest.raises(f.m['MonitorCycleYield']):f.step()
    saved=f.q.job(original['id']);stage=saved['stages'][0]
    assert stage['delivery']=='prepared' and stage['model_selection']['effort'] is None
    encoded=copy.deepcopy(stage)
    seen=[]
    def resumed(c,args):
        if args[0]=='systemd-run':seen.extend(args)
        return command(c,args)
    monkeypatch.setitem(f.m,'mq_service_command',resumed)
    f.config['claude_effort']='max';assert f.step()
    assert '--effort' not in seen and 'max' not in seen
    assert f.q.job(original['id'])['stages'][0]['input']==encoded['input']
    assert f.q.job(original['id'])['stages'][0]['input_context']==encoded['input_context']
    assert f.q.job(original['id'])['stages'][0]['id']==stage['id'] and f.launched==['claude']






def test_retry_remains_frozen_when_a_new_commit_is_enqueued(flow):
    f=flow;f.results['claude']=RuntimeError('failure');original=automatic(f);f.drain()
    saved=f.q.job(original['id'])
    newer=f.q.enqueue(11,82,source_key='new-head',kind='code',head='d'*40,
        source={'origin':'automatic','head':'d'*40},context={**f.context,'head':'d'*40})
    assert len(f.q.jobs())==2 and f.q.job(original['id'])==saved
    assert newer['sequence']>saved['sequence'] and newer['head']=='d'*40


@pytest.mark.parametrize('crash',[False,True])
def test_sufficient_answer_resets_retry_attempt_bounds(flow,monkeypatch,crash):
    f=flow;f.results['codex']=RuntimeError('failure');original=automatic(f);f.drain()
    saved=f.q.job(original['id']);monkeypatch.setitem(f.m,'mq_stamp',lambda:saved['retry_at']+1)
    f.results['codex']=domain(outcome='question',question='Qual regra aplicar?');f.drain()
    held=f.q.mr(11,82)['hold'];assert held and f.q.job(original['id'])['wait_reason']=='human'
    source=human_turn(f,'Use a regra já configurada e continue')
    answer=domain(outcome='noop',assessment=assessment(source['texts'][0],kind='answer',anchor=held['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    f.items[source['turn_id']].append({'type':'agentMessage','id':'answer','phase':'final_answer','text':compact(answer)})
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    reset=f.m['mq_reset_round']
    if crash:
        def interrupted(*args):raise OSError('interrupted after answer persisted')
        monkeypatch.setitem(f.m,'mq_reset_round',interrupted)
        with pytest.raises(OSError,match='after answer'):f.step()
        assert f.q.job(original['id'])['needs_round_reset']
        monkeypatch.setitem(f.m,'mq_reset_round',reset)
    f.results['codex']=domain();f.drain()
    job=f.q.job(original['id'])
    assert job['state']=='completed' and 'review_attempt' not in job
    assert f.launched==['claude','codex','codex','claude','codex']
    assert f.q.mr(11,82)['hold'] is None and len(f.q.mr(11,82)['hold_history'])==1


def test_model_choice_is_pinned_in_actual_native_input_and_version3_answers_remain_compact(flow):
    f=flow;original=automatic(f);f.drain()
    job=f.q.job(original['id'])
    for stage in job['stages']:
        data=stage['input_context']
        expected=({'model':f.config['model'],'effort':f.config['effort']} if stage['reviewer']=='codex'
                  else {'model':f.config['claude_model'],'effort':f.config.get('claude_effort')})
        assert data['model_selection']==expected==stage['model_selection']
        assert 'Proceed without asking to change model/effort' in stage['input']
    assert 'Do not offer model changes' in f.m['mq_instructions']()
    source=human_turn(f,'responda na thread')
    with f.q.atomic():
        record=f.q.mr(11,82);record['instruction_versions'][source['session']]=3;f.q.put_mr(record)
    result=domain(assessment=assessment(source['texts'][0]))
    f.items[source['turn_id']].append({'type':'agentMessage','id':'human-final','phase':'final_answer','text':compact(result)})
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert len(f.q.jobs())==2 and f.q.jobs()[-1]['kind']=='human'


def test_recorded_capacity_failure_does_not_clear_the_actual_model_question(flow):
    """Partial incident texts at the worker boundary, not a replay of native authentication."""
    captured=json.loads((Path(__file__).parent/'fixtures/gitlab-reviewer-retry-incident.json').read_text())
    f=flow;f.results['claude']=RuntimeError(captured['claude_result']['result'])
    f.results['codex']=domain(outcome='question',question=captured['codex_question'])
    original=automatic(f);f.drain();job=f.q.job(original['id'])
    assert f.launched==['claude','codex'] and job['wait_reason']=='human'
    assert job['stages'][0]['state']=='failed' and job['stages'][1]['result']['outcome']=='question'
    assert f.q.mr(11,82)['hold']['question']==captured['codex_question']
    assert 'review_attempt' not in job and not f.sends
