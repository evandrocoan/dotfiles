"""Individual review coverage through the real worker and SQLite; providers are fixtures."""
import copy
import json
from pathlib import Path

import pytest
from test_codex_gitlab_queue import module, flow, domain


BASIS = {'target_project_id': 11, 'target_branch': 'main', 'base_sha': 'b' * 40, 'start_sha': 'c' * 40}


def setup_basis(f):
    f.context['mr'].update(target_project_id=11, target_branch='main')


def admit(f, head, marker, reviewers=None):
    f.context['head'] = f.context['mr']['sha'] = f.context['mr']['diff_refs']['head_sha'] = head
    f.context['diff']['head_commit_sha'] = head
    f.results.update(claude={**domain(), 'head':head}, codex={**domain(), 'head':head})
    return f.q.enqueue(11,82,source_key=marker,kind='code',head=head,
        source={'origin':'automatic','head':head},context=copy.deepcopy(f.context),reviewers=reviewers)


def scope(stage):
    return stage['input_context']['code_review_scope']


def test_first_complete_then_each_reviewer_uses_own_frozen_baseline(flow):
    f=flow;setup_basis(f)
    first=admit(f,'a'*40,'a');f.drain()
    saved=f.q.job(first['id']);coverage=f.q.mr(11,82)['reviewed_code_by_reviewer']
    assert set(coverage)=={'claude','codex'}
    for stage in saved['stages']:
        assert scope(stage)=={'mode':'complete','reason':'no_coverage','baseline':None,'head':'a'*40,'basis':BASIS}
        assert coverage[stage['reviewer']]=={'head':'a'*40,'basis':BASIS,'job_id':first['id'],'stage_id':stage['id']}
    second=admit(f,'d'*40,'d');f.drain()
    for stage in f.q.job(second['id'])['stages']:
        assert scope(stage)=={'mode':'incremental','reason':'eligible','baseline':'a'*40,'head':'d'*40,'basis':BASIS}
        assert 'ancestor' in stage['input'] and 'complete review' in stage['input']
        assert f.q.mr(11,82)['reviewed_code_by_reviewer'][stage['reviewer']]['head']=='d'*40


@pytest.mark.parametrize('failed',['claude','codex'])
def test_partial_success_never_credits_peer_and_next_round_uses_different_baselines(flow,failed):
    f=flow;setup_basis(f)
    admit(f,'a'*40,'a');f.drain()
    second=admit(f,'d'*40,'d');f.results[failed]=RuntimeError('provider failed');f.drain()
    saved=f.q.job(second['id']);peer=next(r for r in ('claude','codex') if r!=failed)
    coverage=f.q.mr(11,82)['reviewed_code_by_reviewer']
    assert coverage[peer]['head']=='d'*40 and coverage[failed]['head']=='a'*40
    assert saved['review_attempt']['reviewers']==[failed]
    third=admit(f,'e'*40,'e');f.drain()
    stages={s['reviewer']:s for s in f.q.job(third['id'])['stages']}
    assert scope(stages[peer])['baseline']=='d'*40
    assert scope(stages[failed])['baseline']=='a'*40
    assert all(scope(s)['head']=='e'*40 for s in stages.values())


def test_old_v3_fixture_keeps_exact_reader_and_digest(flow):
    f=flow
    stage=json.loads((Path(__file__).parent/'fixtures/gitlab-message-v3.json').read_text())
    assert f.m['mq_input_context'](f.q,stage)==stage['input_context']
    changed=copy.deepcopy(stage);changed['input_context']['head']='f'*40
    with pytest.raises(RuntimeError,match='immutable reviewer input'):f.m['mq_verify_input'](f.q,changed)


@pytest.mark.parametrize('field',['target_project_id','target_branch','base_sha','start_sha','head_sha'])
def test_missing_basis_forces_full_and_does_not_credit(flow,field):
    f=flow;setup_basis(f)
    refs=f.context['mr']['diff_refs']
    if field in refs:refs.pop(field)
    else:f.context['mr'].pop(field)
    job=admit(f,'a'*40,'missing')
    if field=='head_sha':f.context['mr']['diff_refs'].pop('head_sha')
    f.drain()
    assert all(scope(s)['mode']=='complete' and scope(s)['reason']=='missing_basis'
               for s in f.q.job(job['id'])['stages'])
    assert not f.q.mr(11,82).get('reviewed_code_by_reviewer')
    assert f.q.mr(11,82)['reviewed_head']=='a'*40


def test_corrupt_own_coverage_does_not_inherit_valid_peer(flow):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    record=f.q.mr(11,82);record['reviewed_code_by_reviewer']['claude']={'head':'bad'}
    with f.q.atomic():f.q.put_mr(record)
    job=admit(f,'d'*40,'d');f.drain()
    stages={s['reviewer']:s for s in f.q.job(job['id'])['stages']}
    assert scope(stages['claude'])['mode']=='complete' and scope(stages['claude'])['baseline'] is None
    assert scope(stages['codex'])['mode']=='incremental' and scope(stages['codex'])['baseline']=='a'*40


def test_target_basis_change_forces_complete_review_for_both(flow):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    f.context['mr']['target_branch']='release'
    job=admit(f,'d'*40,'d');f.drain()
    assert all(scope(s)['mode']=='complete' and scope(s)['baseline'] is None
               for s in f.q.job(job['id'])['stages'])
    assert all(v['basis']['target_branch']=='release' for v in
               f.q.mr(11,82)['reviewed_code_by_reviewer'].values())


def test_scope_bytes_remain_frozen_after_coverage_changes_and_tampering_rejected(flow):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    job=admit(f,'d'*40,'d');assert f.step()
    stage=copy.deepcopy(f.q.job(job['id'])['stages'][0]);record=f.q.mr(11,82)
    record['reviewed_code_by_reviewer']['claude']['head']='f'*40
    with f.q.atomic():f.q.put_mr(record)
    assert f.m['mq_input_context'](f.q,stage)==stage['input_context']
    assert scope(stage)['baseline']=='a'*40
    changed=copy.deepcopy(stage);scope(changed)['baseline']='f'*40
    with pytest.raises(RuntimeError,match='immutable reviewer input'):f.m['mq_verify_input'](f.q,changed)


def test_settlement_transaction_rolls_back_individual_coverage_and_job(flow,monkeypatch):
    f=flow;setup_basis(f);job=admit(f,'a'*40,'a')
    for _ in range(4):assert f.step()
    before_job=copy.deepcopy(f.q.job(job['id']));before_mr=copy.deepcopy(f.q.mr(11,82))
    save=f.q.save
    def interrupted(value):raise OSError('interrupted settlement')
    monkeypatch.setattr(f.q,'save',interrupted)
    with pytest.raises(OSError,match='interrupted settlement'):f.step()
    assert f.q.job(job['id'])==before_job and f.q.mr(11,82)==before_mr
    monkeypatch.setattr(f.q,'save',save);f.drain()
    assert f.q.job(job['id'])['state']=='completed'
    assert set(f.q.mr(11,82)['reviewed_code_by_reviewer'])=={'claude','codex'}
    assert len(f.launched)==2 and not f.sends


@pytest.mark.parametrize('reviewer',['claude','codex'])
def test_single_reviewer_establishes_only_its_own_coverage(flow,reviewer):
    f=flow;setup_basis(f);job=admit(f,'a'*40,'single',reviewers=[reviewer]);f.drain()
    assert set(f.q.mr(11,82)['reviewed_code_by_reviewer'])=={reviewer}
    assert f.q.job(job['id'])['state']=='completed' and f.launched==[reviewer]


def test_basis_changes_during_review_preserve_aggregate_but_not_individual_credit(flow):
    f=flow;setup_basis(f);job=admit(f,'a'*40,'basis-change')
    for _ in range(4):assert f.step()
    f.context['mr']['target_branch']='release';f.drain()
    assert f.q.job(job['id'])['outcome']=='reviewed'
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    assert not f.q.mr(11,82).get('reviewed_code_by_reviewer')


def test_actual_held_continuation_credits_original_stage_only(flow):
    from test_codex_gitlab_direct import native_answer
    f=flow;setup_basis(f);job=admit(f,'a'*40,'held',reviewers=['codex'])
    f.results['codex']=domain(outcome='question',question='Qual regra devo usar?');f.drain()
    held=copy.deepcopy(f.q.job(job['id'])['stages'][0])
    assert not f.q.mr(11,82).get('reviewed_code_by_reviewer')
    native_answer(f);f.m['mq_intake'](f.config,f.q,f.q.mr(11,82));f.drain()
    saved=f.q.job(job['id'])
    assert {k:v for k,v in saved['stages'][0].items() if k!='continuations'}==held
    assert saved['stages'][0]['continuations'][0]['outcome']['result']['outcome']=='complete'
    assert f.q.mr(11,82)['reviewed_code_by_reviewer']['codex']['stage_id']==held['id']
    assert set(f.q.mr(11,82)['reviewed_code_by_reviewer'])=={'codex'}


@pytest.mark.parametrize('operator',['held','mr'])
def test_operator_restart_forces_full_scope_through_failed_reviewer_retry(flow,monkeypatch,operator):
    from test_codex_gitlab_visible_requests import restart as restart_held
    from test_codex_gitlab_restart_mr import restart as restart_mr
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    job=admit(f,'d'*40,'d')
    if operator=='held':
        f.results['codex']=domain(outcome='question',question='Qual regra devo usar?')
        f.drain();hold=f.q.mr(11,82)['hold'];restart_held(f,f.q.job(job['id']),hold)
    else:
        f.results.update(claude=RuntimeError('failure'),codex=RuntimeError('failure'));f.drain()
        restart_mr(f,f.q.job(job['id']))
    f.results.update(claude=RuntimeError('retry failure'),codex={**domain(),'head':'d'*40});f.drain()
    pending=f.q.job(job['id'])
    assert pending['review_attempt']['reviewers']==['claude']
    assert all(scope(s)['mode']=='complete' and scope(s)['reason']=='operator_restart' for s in pending['stages'])
    assert f.q.mr(11,82)['reviewed_code_by_reviewer']['claude']['head']=='a'*40
    monkeypatch.setitem(f.m,'mq_stamp',lambda:pending['retry_at']+1)
    f.results['claude']={**domain(),'head':'d'*40};f.drain()
    done=f.q.job(job['id']);assert done['state']=='completed'
    assert [s['reviewer'] for s in done['stages']]==['claude','codex','claude']
    assert scope(done['stages'][-1])['reason']=='operator_restart'
    assert scope(done['stages'][-1])['mode']=='complete'


def test_aggregate_only_and_legacy_stage_do_not_supply_individual_coverage(flow):
    f=flow;setup_basis(f)
    record=f.q.mr(11,82);record['reviewed_head']='a'*40
    with f.q.atomic():f.q.put_mr(record)
    job=admit(f,'d'*40,'legacy',reviewers=['codex']);assert f.step()
    saved=f.q.job(job['id']);stage=saved['stages'][0]
    assert scope(stage)['mode']=='complete' and scope(stage)['baseline'] is None
    data=copy.deepcopy(stage['input_context']);data.pop('code_review_scope')
    with f.q.atomic():
        stage.update(input=f.m['mq_render_input'](data),input_context=data,input_format='message-v3',
                     input_digest=f.m['monitor_digest'](data))
        f.q.save(saved)
    # Keep the fixture native input consistent with the historical saved stage.
    f.items[stage['turn_id']][0]['content'][0]['text']=stage['input']
    f.drain()
    assert f.q.job(job['id'])['outcome']=='reviewed'
    assert f.q.mr(11,82)['reviewed_head']=='d'*40
    assert not f.q.mr(11,82).get('reviewed_code_by_reviewer')


def test_discussion_work_never_advances_individual_coverage(flow):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    before=copy.deepcopy(f.q.mr(11,82)['reviewed_code_by_reviewer'])
    job=f.q.enqueue(11,82,source_key='discussion',kind='discussion',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context))
    f.drain()
    assert f.q.job(job['id'])['outcome']=='reviewed'
    assert f.q.mr(11,82)['reviewed_code_by_reviewer']==before


def test_job_rotation_preserves_mr_coverage_and_whole_retirement_clears_it(flow):
    import time
    f=flow;setup_basis(f);job=admit(f,'a'*40,'a');f.drain()
    before=copy.deepcopy(f.q.mr(11,82)['reviewed_code_by_reviewer'])
    f.m['mq_observe_direct_stages'](f.config,f.q)
    f.m['mq_rotate_jobs'](f.q,0)
    assert f.q.job(job['id']) is None and f.q.mr(11,82)['reviewed_code_by_reviewer']==before
    f.config['_cycle_deadline']=time.monotonic()+10
    f.m['mq_notify_unread'](f.config,f.q)
    closed=f.q.mr(11,82);closed['mr_state']='closed'
    other=f.q.mr(11,83);other['mr_state']='opened'
    with f.q.atomic():f.q.put_mr(closed);f.q.put_mr(other)
    config={'project_id':11,'project_path':'team/project','projects':[{'id':11,'path':'team/project'}],
        'history_limit':1,'_checked_mr_states':{(11,82):'closed'}}
    f.m['mq_rotate_mrs'](f.q,config,1)
    assert not f.q.mr(11,82).get('reviewed_code_by_reviewer')
    fresh=admit(f,'d'*40,'fresh');f.drain()
    assert all(scope(s)['mode']=='complete' for s in f.q.job(fresh['id'])['stages'])


def test_prepared_input_survives_reopen_and_coverage_change_before_dispatch(flow,monkeypatch):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    job=admit(f,'d'*40,'prepared',reviewers=['claude'])
    dispatch=f.m['mq_claude_dispatch']
    def interrupt(*args):raise f.m['MonitorCycleYield']('before native dispatch')
    monkeypatch.setitem(f.m,'mq_claude_dispatch',interrupt)
    with pytest.raises(f.m['MonitorCycleYield'],match='before native dispatch'):f.step()
    prepared=copy.deepcopy(f.q.job(job['id'])['stages'][0])
    assert prepared['delivery']=='prepared' and scope(prepared)['baseline']=='a'*40
    record=f.q.mr(11,82);record['reviewed_code_by_reviewer']['claude']['head']='f'*40
    with f.q.atomic():f.q.put_mr(record)
    monkeypatch.setitem(f.m,'mq_claude_dispatch',dispatch)
    reopened=f.m['MonitorQueue'](f.config)
    try:
        assert f.step(reopened)
        issued=reopened.job(job['id'])['stages'][0]
        assert [issued[k] for k in ('input','input_context','input_digest')]==[
            prepared[k] for k in ('input','input_context','input_digest')]
        assert scope(issued)['baseline']=='a'*40
        f.drain()
        native=f.m['mq_claude_records'](f.config,issued['session'])
        assert native[0]['message']['content']==prepared['input']
        assert reopened.job(job['id'])['state']=='completed'
    finally:reopened.close()


def test_coalesced_code_targets_latest_admitted_head_without_losing_baseline(flow):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    earlier=admit(f,'d'*40,'earlier');later=admit(f,'e'*40,'later')
    discussion=f.q.enqueue(11,82,source_key='same-head-discussion',kind='discussion',head='e'*40,
        source={'origin':'automatic','event':'discussion'},context=copy.deepcopy(f.context))
    f.drain();saved=f.q.job(earlier['id'])
    assert saved['head']=='e'*40 and saved['kind']=='code' and saved['target_event']==later['id']
    assert set(saved['coalesced_jobs'])=={later['id'],discussion['id']}
    assert all(scope(s)['baseline']=='a'*40 and scope(s)['head']=='e'*40 for s in saved['stages'])
    assert all(v['head']=='e'*40 for v in f.q.mr(11,82)['reviewed_code_by_reviewer'].values())


def test_newer_discussion_cannot_fabricate_code_coverage(flow):
    f=flow;setup_basis(f);admit(f,'a'*40,'a');f.drain()
    before=copy.deepcopy(f.q.mr(11,82)['reviewed_code_by_reviewer'])
    earlier=admit(f,'d'*40,'earlier')
    f.context['head']=f.context['mr']['sha']=f.context['mr']['diff_refs']['head_sha']='e'*40
    discussion=f.q.enqueue(11,82,source_key='later-discussion',kind='discussion',head='e'*40,
        source={'origin':'automatic','event':'discussion'},context=copy.deepcopy(f.context))
    f.results.update(claude={**domain(),'head':'e'*40},codex={**domain(),'head':'e'*40})
    f.drain();saved=f.q.job(earlier['id'])
    assert saved['kind']=='discussion' and saved['head']=='e'*40 and saved['target_event']==discussion['id']
    assert f.q.mr(11,82)['reviewed_code_by_reviewer']==before
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
