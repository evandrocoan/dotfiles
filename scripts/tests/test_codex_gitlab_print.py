"""Finite print execution through the real consumer; service/native transport is simulated."""
import copy
import hashlib
import json
from pathlib import Path
import uuid

import pytest

from test_codex_gitlab_queue import flow, module, domain, rendered
from test_codex_gitlab_periodic import enqueue, quiet_scan


@pytest.mark.parametrize('reviewer',['claude','codex'])
def test_monitor_allocates_passes_and_removes_registered_stage_scratch(flow,reviewer):
    f=flow;job=enqueue(f)
    with f.q.atomic():job['reviewers']=[reviewer];f.q.save(job)
    f.step();stage=f.q.job(job['id'])['stages'][0];path=Path(stage['scratch']['path'])
    assert path.is_dir() and path.stat().st_mode & 0o777==0o700
    assert f.m['mq_input_context'](f.q,stage)['scratch_path']==str(path)
    assert 'Temporary directory for review-only files: '+str(path) in stage['input']
    (path/'snapshot').mkdir();(path/'snapshot'/'output.log').write_text('disposable result')
    outside=path.parent/'unregistered';outside.mkdir();(outside/'keep').write_text('user data')
    (path/'user-link').symlink_to(outside,target_is_directory=True)
    f.drain();saved=f.q.job(job['id'])
    assert saved['state']=='completed' and saved['stages'][0]['state']=='succeeded'
    assert saved['stages'][0]['scratch']['state']=='removed' and not path.exists()
    assert (outside/'keep').read_text()=='user data'
    if reviewer=='claude':
        command=next(c for c in f.service.commands if c[0]=='systemd-run')
        assert str(path) in ' '.join(command) and 'Write(/'+str(path)+'/**)' in command
        assert command[command.index('--permission-mode')+1]=='dontAsk'


def test_cleanup_failure_is_separate_and_retried_without_new_review(flow,monkeypatch):
    f=flow
    def busy(config,path):raise RuntimeError('container still references scratch')
    monkeypatch.setitem(f.m,'mq_scratch_resources',busy)
    job=enqueue(f);f.drain();saved=f.q.job(job['id'])
    assert saved['state']=='completed' and f.launched==['claude','codex']
    assert all(s['state']=='succeeded' and s['scratch']['state']=='pending' for s in saved['stages'])
    assert all('container' in s['scratch']['reason'] for s in saved['stages'])
    paths=[Path(s['scratch']['path']) for s in saved['stages']]
    assert all(p.is_dir() for p in paths)
    status=f.m['mq_job_status'](saved,f.config)
    assert status['stages'][0]['error'] is None
    assert status['stages'][0]['scratch']['state']=='pending'
    f.m['mq_rotate_jobs'](f.q,0)
    assert f.q.job(job['id']) is not None
    monkeypatch.setitem(f.m,'mq_scratch_resources',lambda c,p:None)
    reopened=f.m['MonitorQueue'](f.config)
    try:assert not f.m['mq_step'](f.config,reopened)
    finally:reopened.close()
    assert all(not p.exists() for p in paths)
    assert f.launched==['claude','codex']
    assert all(s['scratch']['state']=='removed' for s in f.q.job(job['id'])['stages'])


@pytest.mark.parametrize('change',['resume','image-only','empty','mixed-tool-result',
                                   'missing','duplicate','invalid-id','partial'])
def test_claude_cleanup_authenticates_native_frontier_outside_holds(flow,monkeypatch,change):
    f=flow
    def unavailable(c,p):raise RuntimeError('Docker inventory unavailable')
    monkeypatch.setitem(f.m,'mq_scratch_resources',unavailable)
    job=enqueue(f)
    with f.q.atomic():job['reviewers']=['claude'];f.q.save(job)
    f.drain();saved=f.q.job(job['id']);stage=saved['stages'][0]
    path=Path(stage['scratch']['path']);native,values=records(f,stage)
    assert saved['state']=='completed' and not stage.get('continuations') and not f.q.mr(11,82).get('hold')
    if change in {'resume','image-only','empty','mixed-tool-result'}:
        user=copy.deepcopy(values[0]);user['uuid']=str(uuid.uuid4())
        content='Run another command in the temporary directory.'
        if change=='image-only':content=[{'type':'image','source':{'type':'base64','data':'fixture'}}]
        elif change=='empty':content=[]
        elif change=='mixed-tool-result':content=[{'type':'tool_result','content':'done'},{'type':'image'}]
        user['message']['content']=content;values.append(user)
    elif change=='missing':values=values[1:]
    elif change=='duplicate':values.append(copy.deepcopy(values[0]))
    elif change=='invalid-id':values[0]['uuid']='not-a-native-uuid'
    save_records(native,values)
    if change=='partial':
        with native.open('a') as stream:stream.write('{"type":"user"')
    monkeypatch.setitem(f.m,'mq_scratch_resources',lambda c,p:None)
    f.m['mq_cleanup_scratch'](f.config,f.q)
    saved=f.q.job(job['id'])
    assert path.is_dir() and saved['stages'][0]['scratch']['state']=='pending'
    assert saved['stages'][0]['scratch']['reason'] and saved['state']=='completed'
    assert f.launched==['claude']


def test_scratch_deletion_yields_between_entries_and_resumes_same_inode(flow,monkeypatch):
    f=flow;job=enqueue(f);job=f.q.reserve({11});f.m['mq_workspace'](f.config,f.q,job)
    stage=f.q.stage_start(job,'claude','');f.m['mq_allocate_scratch'](f.q,job,stage)
    path=Path(stage['scratch']['path']);identity=stage['scratch']['identity']
    f.q.stage_end(job,stage['id'],error={'message':'fixture unissued','not_started':True},terminal=True)
    for i in range(10):(path/str(i)).write_text('temporary output')
    calls=0;remove=f.m['mq_remove_scratch'];budget=f.m['mq_budget']
    def bounded(c,s):return remove({**c,'_deletion_probe':True},s)
    def expire(c):
        nonlocal calls
        if c.get('_deletion_probe'):
            calls+=1
            if calls==3:raise f.m['MonitorCycleYield']('fixture deletion deadline')
        return budget(c)
    with monkeypatch.context() as patch:
        patch.setitem(f.m,'mq_remove_scratch',bounded);patch.setitem(f.m,'mq_budget',expire)
        f.m['mq_cleanup_scratch'](f.config,f.q)
    saved=f.q.job(job['id'])['stages'][0]
    assert saved['scratch']['state']=='pending' and 'deferred' in saved['scratch']['reason']
    assert len(list(path.iterdir()))==8 and saved['scratch']['identity']==identity
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert not path.exists() and f.q.job(job['id'])['stages'][0]['scratch']['state']=='removed'
    assert f.launched==[]


@pytest.mark.parametrize('failure',['rejected','lost-ack'])
def test_codex_rejected_dispatch_cleanup_distinguishes_unknown_delivery(flow,monkeypatch,failure):
    f=flow;native=f.m['monitor_native']
    def failing(c,method,params,**kwargs):
        if method=='turn/start':
            if failure=='rejected':raise f.m['MonitorNativeRejected']('turn/start rejected')
            native(c,method,params,**kwargs)
            raise RuntimeError('turn/start acknowledgment lost')
        return native(c,method,params,**kwargs)
    monkeypatch.setitem(f.m,'monitor_native',failing)
    job=enqueue(f)
    with f.q.atomic():job['reviewers']=['codex'];f.q.save(job)
    f.step();stage=f.q.job(job['id'])['stages'][0];path=Path(stage['scratch']['path'])
    f.m['mq_cleanup_scratch'](f.config,f.q);saved=f.q.job(job['id'])['stages'][0]
    assert saved['delivery']=='sending' and not saved.get('turn_id')
    if failure=='rejected':
        assert saved['state']=='failed' and saved['error']['not_started'] is True
        assert saved['scratch']['state']=='removed' and not path.exists() and f.launched==[]
    else:
        assert saved['state']=='running' and not saved['error'].get('not_started')
        assert path.is_dir() and saved['scratch']['state']=='ready' and f.launched==['codex']


def test_captured_claude_cleanup_denial_cannot_block_executor_cleanup(flow):
    """Artifact-level regression of the observed dontAsk denial, not a model/session replay."""
    f=flow;job=enqueue(f);f.step();stage=f.q.job(job['id'])['stages'][0]
    root=directory(f,stage);events=[json.loads(line) for line in (root/'stdout').read_text().splitlines()]
    result=next(event for event in events if event['type']=='result')
    result['permission_denials']=[{'tool_name':'Bash','tool_use_id':'captured-cleanup-call',
        'tool_input':{'command':'rm -rf '+stage['scratch']['path'],
            'description':"Remove this review's scratch directory"}}]
    rewrite_output(f,stage,events)
    f.drain();saved=f.q.job(job['id'])
    assert saved['stages'][0]['state']=='succeeded'
    assert saved['stages'][0]['scratch']['state']=='removed'
    assert not Path(stage['scratch']['path']).exists()
    assert f.launched==['claude','codex'] and saved['state']=='completed'


@pytest.mark.parametrize('reviewer',['claude','codex'])
def test_question_preserves_scratch_before_snapshot_hold_exists(flow,monkeypatch,reviewer):
    f=flow;f.results[reviewer]=domain(outcome='question',question='Qual regra usar?')
    job=enqueue(f)
    with f.q.atomic():job['reviewers']=[reviewer];f.q.save(job)
    f.step();f.step()
    saved=f.q.job(job['id']);stage=saved['stages'][0];path=Path(stage['scratch']['path'])
    # Simulate interruption between saving the native question and establishing its hold.
    record=f.q.mr(11,82);record['hold']=None
    with f.q.atomic():f.q.put_mr(record)
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert path.is_dir() and f.q.job(job['id'])['stages'][0]['scratch']['state']=='held'


@pytest.mark.parametrize('replacement',['symlink','directory','base'])
def test_registered_scratch_replacement_is_preserved(flow,monkeypatch,replacement):
    f=flow
    monkeypatch.setitem(f.m,'mq_scratch_resources',lambda c,p:(_ for _ in ()).throw(RuntimeError('busy')))
    job=enqueue(f);f.drain();saved=f.q.job(job['id']);stage=saved['stages'][0]
    path=Path(stage['scratch']['path']);old=path.with_name(path.name+'-original')
    if replacement=='base':
        base=path.parent;base.rename(base.with_name(base.name+'-original'));base.mkdir(mode=0o700)
        path.mkdir(mode=0o700)
    else:
        path.rename(old)
        if replacement=='symlink':path.symlink_to(old,target_is_directory=True)
        else:path.mkdir(mode=0o700)
    (path/'keep').write_text('replacement data')
    monkeypatch.setitem(f.m,'mq_scratch_resources',lambda c,p:None)
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert (path/'keep').read_text()=='replacement data'
    assert f.q.job(job['id'])['stages'][0]['scratch']['state']=='pending'


def test_delete_before_state_commit_recovers_without_relaunch(flow,monkeypatch):
    f=flow;job=enqueue(f);f.step();f.step()
    stage=f.q.job(job['id'])['stages'][0];path=Path(stage['scratch']['path'])
    original=f.q.save
    def interrupted(value):
        if value['stages'][0]['scratch']['state']=='removed':raise RuntimeError('crash before commit')
        original(value)
    with monkeypatch.context() as patch:
        patch.setattr(f.q,'save',interrupted)
        with pytest.raises(RuntimeError,match='crash before commit'):f.m['mq_cleanup_scratch'](f.config,f.q)
    assert not path.exists() and f.q.job(job['id'])['stages'][0]['scratch']['state']=='ready'
    f.drain()
    assert f.q.job(job['id'])['stages'][0]['scratch']['state']=='removed'
    assert f.launched==['claude','codex']


def test_allocation_interruption_does_not_adopt_directory_or_launch_it(flow,monkeypatch):
    f=flow;original=f.m['mq_update_stage']
    def interrupted(queue,job,identifier,**changes):
        if (changes.get('scratch') or {}).get('identity'):raise RuntimeError('allocation commit interrupted')
        return original(queue,job,identifier,**changes)
    with monkeypatch.context() as patch:
        patch.setitem(f.m,'mq_update_stage',interrupted)
        job=enqueue(f);f.step()
    saved=f.q.job(job['id']);stage=saved['stages'][0];path=Path(stage['scratch']['path'])
    assert stage['state']=='failed' and stage['scratch']['identity'] is None and path.is_dir()
    assert f.launched==[]
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert path.exists() and 'ownership is incomplete' in f.q.job(job['id'])['stages'][0]['scratch']['reason']


def test_archived_round_scratch_survives_reset_and_is_cleaned(flow,monkeypatch):
    f=flow;job=enqueue(f);f.step();f.step()
    saved=f.q.job(job['id']);path=Path(saved['stages'][0]['scratch']['path'])
    f.m['mq_reset_round'](f.q,saved,'fixture round reset')
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert not path.exists()
    assert f.q.job(job['id'])['rounds'][0]['stages'][0]['scratch']['state']=='removed'


def test_retired_unissued_preparation_keeps_visible_cleanup_obligation(flow):
    f=flow;job=enqueue(f);job=f.q.reserve({11});f.m['mq_workspace'](f.config,f.q,job)
    stage=f.q.stage_start(job,'claude','')
    f.m['mq_allocate_scratch'](f.q,job,stage);path=Path(stage['scratch']['path'])
    f.q.retire_preparation(job,stage)
    assert f.m['mq_job_status'](f.q.job(job['id']),f.config)['retired_preparations'][0]['scratch']['state']=='ready'
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert not path.exists()
    assert f.q.job(job['id'])['retired_preparations'][0]['scratch']['state']=='removed'
    assert f.launched==[]


@pytest.mark.parametrize('reviewer',['claude','codex'])
def test_held_continuation_cleans_only_after_resources_stop(flow,monkeypatch,reviewer):
    from test_codex_gitlab_direct import native_answer,claude_answer
    f=flow;f.results[reviewer]=domain(outcome='question',question='Qual regra usar?')
    job=enqueue(f)
    with f.q.atomic():job['reviewers']=[reviewer];f.q.save(job)
    f.drain();stage=f.q.job(job['id'])['stages'][0];path=Path(stage['scratch']['path'])
    hold=f.q.mr(11,82)['hold']
    if reviewer=='claude':claude_answer(f,hold)
    else:native_answer(f)
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    def busy(c,p):raise RuntimeError('continuation command still running')
    monkeypatch.setitem(f.m,'mq_scratch_resources',busy)
    f.drain();saved=f.q.job(job['id'])
    assert saved['state']=='completed' and saved['stages'][0]['scratch']['state']=='pending'
    assert path.is_dir() and len(saved['stages'][0]['continuations'])==1
    monkeypatch.setitem(f.m,'mq_scratch_resources',lambda c,p:None)
    f.m['mq_cleanup_scratch'](f.config,f.q)
    if reviewer=='claude':
        assert path.is_dir()
        assert 'manual Claude continuation' in f.q.job(job['id'])['stages'][0]['scratch']['reason']
    else:
        assert not path.exists()
    assert f.launched==[reviewer]


@pytest.mark.parametrize('case',['busy','unloaded','api-error','malformed','cursor-loop'])
def test_codex_native_resource_uncertainty_preserves_scratch(flow,monkeypatch,case):
    f=flow;job=enqueue(f)
    with f.q.atomic():job['reviewers']=['codex'];f.q.save(job)
    f.step();f.step();stage=f.q.job(job['id'])['stages'][0];path=Path(stage['scratch']['path'])
    original=f.m['monitor_native']
    def native(c,method,params,**kwargs):
        if method=='thread/read' and case=='unloaded':
            value=original(c,method,params,**kwargs);value['thread']['status']={'type':'notLoaded'};return value
        if method=='thread/backgroundTerminals/list':
            if case=='api-error':raise RuntimeError('native terminal inventory unavailable')
            if case=='busy':return {'data':[{'processId':'owned-command'}],'nextCursor':None}
            if case=='malformed':return {'data':None}
            if case=='cursor-loop':return {'data':[],'nextCursor':'repeated'}
            raise AssertionError('unloaded thread must not be queried for terminal inventory')
        return original(c,method,params,**kwargs)
    monkeypatch.setitem(f.m,'monitor_native',native)
    f.drain();saved=f.q.job(job['id'])
    assert saved['state']=='completed' and saved['stages'][0]['state']=='succeeded'
    assert path.is_dir() and saved['stages'][0]['scratch']['state']=='pending'
    assert saved['stages'][0]['scratch']['reason']
    assert f.launched==['codex']


@pytest.mark.parametrize('change',['missing','replacement'])
def test_frozen_preparation_revalidates_ready_scratch_before_launch(flow,monkeypatch,change):
    import shutil
    f=flow;job=enqueue(f);job=f.q.reserve({11});f.m['mq_workspace'](f.config,f.q,job)
    stage=f.q.stage_start(job,'claude','');f.m['mq_allocate_scratch'](f.q,job,stage)
    f.m['mq_input'](f.q,job,stage,f.context);original=stage['input'];path=Path(stage['scratch']['path'])
    path.rename(path.with_name(path.name+'-original'))
    if change=='replacement':path.mkdir(mode=0o700);(path/'keep').write_text('user replacement')
    f.step();saved=f.q.job(job['id'])['stages'][0]
    assert saved['state']=='failed' and saved['input']==original and f.launched==[]
    if change=='replacement':assert (path/'keep').read_text()=='user replacement'


def test_native_empty_inventory_accepts_omitted_optional_cursor(flow,monkeypatch):
    f=flow;original=f.m['monitor_native']
    def native(c,method,params,**kwargs):
        if method=='thread/backgroundTerminals/list':return {'data':[]}
        return original(c,method,params,**kwargs)
    monkeypatch.setitem(f.m,'monitor_native',native)
    job=enqueue(f)
    with f.q.atomic():job['reviewers']=['codex'];f.q.save(job)
    f.drain();stage=f.q.job(job['id'])['stages'][0]
    assert stage['scratch']['state']=='removed' and not Path(stage['scratch']['path']).exists()
    assert f.launched==['codex']


def test_retired_question_scratch_is_eligible_after_operator_restart(flow):
    from test_codex_gitlab_direct import native_hold
    f=flow;job,hold=native_hold(f);stage=f.q.job(job['id'])['stages'][0]
    path=Path(stage['scratch']['path'])
    f.m['mq_restart_review'](f.config,job['id'],hold['stage_id'],'discard this held review')
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert not path.exists()
    archived=f.q.job(job['id'])['rounds'][0]['stages'][0]
    assert archived['result']['outcome']=='question' and archived['scratch']['state']=='removed'


def test_failed_launch_scratch_is_cleaned_and_retry_gets_new_directory(flow,monkeypatch):
    import errno
    f=flow;original=f.m['mq_service_command']
    def failed(c,args):
        if args[0]=='systemd-run':raise OSError(errno.E2BIG,'fixture pre-exec failure')
        return original(c,args)
    with monkeypatch.context() as patch:
        patch.setitem(f.m,'mq_service_command',failed)
        job=enqueue(f);f.drain()
    saved=f.q.job(job['id']);first=saved['stages'][0];path=Path(first['scratch']['path'])
    assert not path.exists() and first['scratch']['state']=='removed'
    assert first['error']['not_started'] is True and saved['wait_reason']=='reviewer_retry'
    with f.q.atomic():saved['retry_at']=0;f.q.save(saved)
    f.drain();saved=f.q.job(job['id'])
    assert len(saved['stages'])==3
    assert saved['stages'][2]['scratch']['path']!=str(path)
    assert saved['state']=='completed' and f.launched==['codex','claude']


def test_unknown_delivery_and_live_execution_never_remove_scratch(flow,monkeypatch):
    f=flow;original=f.m['mq_service_command']
    def lost(c,args):
        result=original(c,args)
        if args[0]=='systemd-run':raise RuntimeError('lost acceptance')
        return result
    monkeypatch.setitem(f.m,'mq_service_command',lost)
    job=enqueue(f);f.step();stage=f.q.job(job['id'])['stages'][0]
    path=Path(stage['scratch']['path']);f.service.populated=True
    f.m['mq_cleanup_scratch'](f.config,f.q)
    assert path.is_dir() and stage['delivery']=='sending'
    assert f.q.job(job['id'])['stages'][0]['scratch']['state']=='ready'




@pytest.mark.parametrize('relation',['same','ancestor','descendant'])
def test_docker_mount_probe_blocks_all_local_contexts(module,tmp_path,monkeypatch,relation):
    import subprocess
    m=module['mq_step'].__globals__;path=tmp_path/'review';path.mkdir()
    source=path if relation=='same' else path.parent if relation=='ancestor' else path/'data'
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if 'context' in args:output='\n'.join(json.dumps({'DockerEndpoint':p}) for p in
            ('unix:///first.sock','unix:///second.sock'))
        elif 'ps' in args:output='a'*12 if 'unix:///second.sock' in args else ''
        else:output=json.dumps([{'Type':'bind','Source':str(source)}])
        return subprocess.CompletedProcess(args,0,output,'')
    monkeypatch.setattr('shutil.which',lambda name:'/fixture/docker')
    monkeypatch.delenv('DOCKER_HOST',raising=False)
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(RuntimeError,match='referenced by Docker'):m['mq_scratch_docker']({'native_timeout':5},path)
    assert any('unix:///second.sock' in c and 'inspect' in c for c in calls)


@pytest.mark.parametrize('failure',['unavailable','remote','query'])
def test_docker_inventory_uncertainty_preserves_cleanup(module,tmp_path,monkeypatch,failure):
    import subprocess
    m=module['mq_step'].__globals__
    monkeypatch.setattr('shutil.which',lambda name:None if failure=='unavailable' else '/fixture/docker')
    monkeypatch.delenv('DOCKER_HOST',raising=False)
    def run(args,**kwargs):
        return subprocess.CompletedProcess(args,1 if failure=='query' else 0,
            json.dumps({'DockerEndpoint':'ssh://remote'}),'query unavailable')
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(RuntimeError,match='unavailable|complete local|inventory failed'):
        m['mq_scratch_docker']({'native_timeout':5},tmp_path)




def launch(f):
    job=enqueue(f)
    assert f.step()
    saved=f.q.job(job['id'])
    stage=saved['stages'][0]
    assert stage['delivery']=='accepted'
    return saved,stage


def directory(f, stage):
    return f.q.path.parent/'executions'/stage['id']


def rewrite_output(f,stage,events):
    root=directory(f,stage)
    (root/'stdout').write_text(''.join(json.dumps(e)+'\n' for e in events))
    receipt=json.loads((root/'receipt.json').read_text())
    receipt['stdout_digest']=hashlib.sha256((root/'stdout').read_bytes()).hexdigest()
    (root/'receipt.json').write_text(json.dumps(receipt))


def records(f,stage):
    path=next((Path(f.config['claude_home'])/'projects').glob('*/'+stage['session']+'.jsonl'))
    return path,[json.loads(l) for l in path.read_text().splitlines()]


def save_records(path,values):
    path.write_text(''.join(json.dumps(v)+'\n' for v in values))


def test_print_completion_does_not_use_tool_ancestry_or_background_inventory(flow,monkeypatch):
    f=flow;job,stage=launch(f)
    ancestry=f.m['mq_claude_final']
    def forbidden(*args,**kwargs):
        if 'tool_results' in kwargs:return ancestry(*args,**kwargs)
        raise AssertionError('retired completion authority')
    monkeypatch.setitem(f.m,'mq_claude_final',forbidden)
    monkeypatch.setitem(f.m,'mq_claude_agents',forbidden)
    f.drain()
    saved=f.q.job(job['id'])
    assert saved['state']=='completed'
    assert [s['state'] for s in saved['stages']]==['succeeded','succeeded']
    assert f.launched==['claude','codex']
    assert f.q.mr(11,82)['reviewed_head']=='a'*40
    command=next(c for c in f.service.commands if c[0]=='systemd-run')
    assert '--property=KillMode=control-group' in command
    assert '--expand-environment=no' in command
    assert not any(c[0]=='systemctl' and 'restart' in c for c in f.service.commands)
    assert '--remote-control' not in command and '--bg' not in command
    status=f.m['mq_job_status'](saved,f.config)['stages'][0]
    assert stage['session'] in status['resume_command']
    assert 'remote_url' not in status
    assert status['result']==domain()


@pytest.mark.parametrize('state,populated',[('deactivating',False),('inactive',True),('failed',True)])
def test_receipt_or_terminal_unit_with_live_execution_cannot_release_slot(flow,state,populated):
    f=flow;job,stage=launch(f)
    f.service.units[stage['unit']]['ActiveState']=state
    f.service.populated=populated
    assert not f.step()
    assert f.q.job(job['id'])['stages'][0]['state']=='running'
    assert f.launched==['claude'] and f.sends==[]


@pytest.mark.parametrize('failure',['exit-code','timeout','signal','recorder'])
def test_terminal_service_failure_always_continues_next_reviewer(flow,failure):
    f=flow;job,stage=launch(f)
    root=directory(f,stage)
    f.service.units[stage['unit']].update(ActiveState='failed',Result=failure)
    if failure=='recorder':(root/'receipt.json').unlink()
    else:
        value=json.loads((root/'receipt.json').read_text());value.update(result=failure,exit_status='7')
        (root/'receipt.json').write_text(json.dumps(value))
    f.drain()
    saved=f.q.job(job['id'])
    assert [s['state'] for s in saved['stages']]==['failed','succeeded']
    assert failure in saved['stages'][0]['error']['message']
    assert f.launched==['claude','codex'] and saved['wait_reason']=='reviewer_retry'
    assert saved['review_attempt']['reviewers']==['claude']


def test_lost_launch_acknowledgment_reconciles_same_invocation_once(flow,monkeypatch):
    f=flow;original=f.m['mq_service_command']
    def command(c,args):
        result=original(c,args)
        if args[0]=='systemd-run':raise RuntimeError('lost acknowledgment after service accepted')
        return result
    monkeypatch.setitem(f.m,'mq_service_command',command)
    job=enqueue(f);f.step()
    saved=f.q.job(job['id']);stage=saved['stages'][0]
    assert stage['delivery']=='sending'
    assert f.q.mr(11,82)['chats']=={}
    f.drain();f.drain()
    assert f.q.job(job['id'])['state']=='completed'
    assert f.launched==['claude','codex']
    assert f.q.mr(11,82)['chats']['claude']==stage['session']
    assert len([c for c in f.service.commands if c[0]=='systemd-run'])==1


@pytest.mark.parametrize('receipt',[True,False])
def test_absent_unit_requires_receipt_or_reboot_evidence(flow,receipt):
    f=flow;job,stage=launch(f)
    f.service.units.clear()
    if not receipt:(directory(f,stage)/'receipt.json').unlink()
    observed=f.m['mq_claude_observe'](f.config,stage)
    assert observed['terminal'] is receipt
    if not receipt:
        assert observed['unknown'] is True
        f.service.identity['boot']='new-boot'
        observed=f.m['mq_claude_observe'](f.config,stage)
        assert observed['terminal'] is True and 'reboot' in observed['error']['message']
    f.drain()
    assert f.launched==['claude','codex']


def test_reboot_preserves_completed_success_and_exact_public_source_validation(flow):
    f=flow;job,stage=launch(f)
    f.step()
    f.service.identity['boot']='new-boot';f.service.units.clear()
    f.drain()
    saved=f.q.job(job['id'])
    assert saved['stages'][0]['state']=='succeeded' and saved['state']=='completed'
    assert f.launched==['claude','codex']


@pytest.mark.parametrize('change',['wrong_session','missing_result','duplicate_result','wrong_uuid','changed_text','wrong_source','truncated'])
def test_invalid_output_fails_terminal_stage_without_publication(flow,change):
    f=flow;job,stage=launch(f);root=directory(f,stage)
    events=[json.loads(l) for l in (root/'stdout').read_text().splitlines()]
    if change=='wrong_session':events[0]['session_id']=str(uuid.uuid4())
    if change=='missing_result':events.pop()
    if change=='duplicate_result':events.append(events[-1])
    if change=='wrong_uuid':events[0]['uuid']=str(uuid.uuid4())
    if change=='changed_text':events[0]['message']['content'][0]['text']='changed';events[-1]['result']='changed'
    if change=='wrong_source':
        path,values=records(f,stage);values[0]['message']['content']='different input';save_records(path,values)
    rewrite_output(f,stage,events)
    if change=='truncated':
        raw=(root/'stdout').read_bytes();(root/'stdout').write_bytes(raw[:-1])
        value=json.loads((root/'receipt.json').read_text());value['stdout_digest']=hashlib.sha256(raw[:-1]).hexdigest()
        (root/'receipt.json').write_text(json.dumps(value))
    f.drain();saved=f.q.job(job['id'])
    assert [s['state'] for s in saved['stages']]==['failed','succeeded']
    assert f.launched==['claude','codex'] and f.sends==[]


@pytest.mark.parametrize('message',[
    None, 'invalid', [], {'id':None,'content':[]}, {'id':'final','content':None},
    {'id':'final','content':'invalid'}, {'id':'final','content':[None]},
    {'id':'final','content':['invalid']}, {'id':'final','content':[{'type':None}]},
    {'id':'final','content':[{'type':'text','text':None}]},
])
def test_malformed_assistant_shape_fails_and_continues_consumer(flow,message):
    f=flow;job,stage=launch(f)
    events=[json.loads(line) for line in (directory(f,stage)/'stdout').read_text().splitlines()]
    events[0]['message']=message
    rewrite_output(f,stage,events)
    f.drain();saved=f.q.job(job['id'])
    assert [s['state'] for s in saved['stages']]==['failed','succeeded']
    assert 'malformed Claude assistant' in saved['stages'][0]['error']['message']
    assert f.launched==['claude','codex'] and f.sends==[]


def test_split_final_native_ids_preserved_despite_later_human_turn(flow):
    f=flow;job,stage=launch(f);root=directory(f,stage)
    events=[json.loads(l) for l in (root/'stdout').read_text().splitlines()]
    path,values=records(f,stage)
    index=next(i for i,r in enumerate(values) if r.get('uuid')==events[0]['uuid'])
    first=values[index];second=copy.deepcopy(first);second['uuid']=str(uuid.uuid4());second['parentUuid']=first['uuid']
    # The installed CLI result envelope carries only the last text block.
    first['message']['content']=[{'type':'text','text':'Review result:'}]
    values.insert(index+1,second);values[index+2]['parentUuid']=second['uuid']
    later_user={'type':'user','uuid':str(uuid.uuid4()),'sessionId':stage['session'],
                'parentUuid':second['uuid'],'message':{'content':'A later human input'}}
    later=copy.deepcopy(second);later.update(uuid=str(uuid.uuid4()),parentUuid=later_user['uuid'])
    later['message']['id']='later';values.extend([later_user,later]);save_records(path,values)
    events[0]['message']=first['message']
    events.insert(1,{'type':'assistant','uuid':second['uuid'],'session_id':stage['session'],
                     'parent_tool_use_id':None,'message':second['message']})
    child=copy.deepcopy(events[1]);child['uuid']=str(uuid.uuid4());child['parent_tool_use_id']='tool-child'
    events.insert(2,child);rewrite_output(f,stage,events)
    f.step()
    saved=f.q.job(job['id'])['stages'][0]
    assert saved['state']=='succeeded'
    assert saved['final_ids']==[first['uuid'],second['uuid']]
    assert saved['anchor']==second['uuid'] and saved['source_id']==values[0]['uuid']
    f.drain()
    assert f.q.job(job['id'])['state']=='completed'


def test_foreign_service_invocation_never_releases_capacity(flow):
    f=flow;job,stage=launch(f)
    f.service.units[stage['unit']]['InvocationID']=uuid.uuid4().hex
    assert not f.m['mq_consume'](f.config,f.q)
    assert 'invocation changed' in f.q.meta('consumer_error')['error']
    assert f.q.job(job['id'])['stages'][0]['state']=='running'
    assert f.launched==['claude'] and f.sends==[]


def test_changed_captured_output_is_terminal_failure_not_stuck_execution(flow):
    f=flow;job,stage=launch(f)
    with (directory(f,stage)/'stdout').open('a') as stream:stream.write('corrupt\n')
    f.drain();saved=f.q.job(job['id'])
    assert saved['stages'][0]['state']=='failed'
    assert saved['stages'][0]['error']['message']=='Claude captured stdout changed'
    assert f.launched==['claude','codex'] and f.sends==[]


def test_recorder_refuses_calls_outside_registered_native_unit(flow,monkeypatch):
    f=flow;job,stage=launch(f)
    path,manifest=f.m['mq_print_manifest'](f.config,stage)
    before=path.with_name('receipt.json').read_bytes()
    monkeypatch.setenv('INVOCATION_ID',stage['invocation'])
    with pytest.raises(RuntimeError,match='not in its registered service invocation'):
        f.m['mq_print_receipt'](f.config,path,manifest)
    assert path.with_name('receipt.json').read_bytes()==before
    assert f.q.job(job['id'])==job and f.sends==[]


def test_archived_round_resume_uses_its_original_directory_and_native_home(flow):
    f=flow;job,stage=launch(f)
    previous=copy.deepcopy(job['workspace']);previous['cwd']='/original workspace'
    job['rounds']=[{'reason':'changed folders','workspace':previous,'stages':[copy.deepcopy(stage)]}]
    job['workspace']['cwd']='/current workspace'
    status=f.m['mq_job_status'](job,f.config)
    old=status['rounds'][0]['stages'][0]['resume_command']
    new=status['stages'][0]['resume_command']
    assert "cd -- '/original workspace'" in old
    assert "cd -- '/current workspace'" in new
    assert 'CLAUDE_CONFIG_DIR='+stage['native_home'] in old
