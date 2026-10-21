"""Visible requests and explicit operator restart through real worker/queue/native boundaries."""
import copy
import errno
import hashlib
import json
from pathlib import Path
import uuid

import pytest
from test_codex_gitlab_queue import module, flow, domain


def automatic(f):
    return f.q.enqueue(11,82,source_key='real-admission',kind='code',head='a'*40,
        source={'origin':'automatic','head':'a'*40},context=copy.deepcopy(f.context))


def held(f):
    f.results['codex']=domain(outcome='question',question='Qual é a divergência específica entre revisores?')
    job=automatic(f)
    with f.q.atomic():
        job['scope']={'effects':['finding'],'discussions':[]};f.q.save(job)
    f.drain()
    job=f.q.job(job['id'])
    assert job['wait_reason']=='human'
    return job,f.q.mr(11,82)['hold']


def human(f,hold,text='continuar',result=None):
    session=hold['session'];turn=str(uuid.uuid4());source='human-'+turn
    f.turns[session].insert(0,{'id':turn,'status':'completed'})
    f.items[turn]=[{'type':'userMessage','id':source,'content':[{'type':'text','text':text}]}]
    if result:
        f.items[turn].append({'type':'agentMessage','id':'answer-'+turn,'phase':'final_answer','text':result})
    return turn


def answer(hold):
    return '```csm-assessment\n'+json.dumps({'kind':'answer','summary':'continue the held work',
        **hold['scope'],'question_anchor':hold['anchor']})+'\n```'


def restart(f,job,hold,reason='Discard misleading question and review afresh'):
    return f.m['mq_restart_review'](f.config,job['id'],hold['stage_id'],reason)


def test_readable_native_requests_and_no_external_input_json(flow):
    f=flow;job=automatic(f)
    with f.q.atomic():
        job['validation_error']='unresolved reviewer disagreement requires a human decision';f.q.save(job)
    f.drain();saved=f.q.job(job['id'])
    assert f.launched==['claude','codex'] and saved['outcome']=='reviewed' and not f.model_errors
    for stage in saved['stages']:
        assert stage.get('input_format')=='message-v1'
        assert 'https://gitlab.example.test/team/repo/-/merge_requests/82' in stage['input']
        assert 'Exact admitted head: '+'a'*40 in stage['input']
        assert f.config['cwd'] in stage['input']
        assert 'Read the immutable input file' not in stage['input']
        assert 'unresolved reviewer disagreement' not in stage['input']
        assert f.m['mq_input_context'](f.q,stage)['head']=='a'*40
    assert not (f.q.path.parent/'inputs').exists()
    first=saved['stages'][0]
    rows=f.m['mq_claude_records'](f.config,first['session'])
    assert rows[0]['message']['content']==first['input']
    second=saved['stages'][1]
    assert f.items[second['turn_id']][0]['content']==[{'type':'text','text':second['input']}]
    command=next(c for c in f.service.commands if c[0]=='systemd-run')
    assert first['input'] not in command
    assert any(c.startswith('--property=StandardInput=file:') for c in command)


@pytest.mark.parametrize('change',['text','context','version','stage'])
def test_input_tampering_is_rejected(flow,change):
    f=flow;job=automatic(f);f.step();stage=copy.deepcopy(f.q.job(job['id'])['stages'][0])
    if change=='text':stage['input']+=' changed'
    elif change=='context':stage['input_context']['head']='d'*40
    elif change=='version':stage['input_format']='message-v99'
    else:stage['id']=str(uuid.uuid4())
    with pytest.raises(RuntimeError,match='immutable reviewer input changed'):f.m['mq_verify_input'](f.q,stage)


def test_historical_input_keeps_its_file_reader(flow):
    f=flow;raw=b'{"hold":null,"head":"original"}'
    stage={'id':str(uuid.uuid4()),'reviewer':'codex'}
    root=f.q.path.parent/'inputs';root.mkdir(mode=0o700)
    path=root/(stage['id']+'.json');path.write_bytes(raw);path.chmod(0o600)
    stage['input']='Old pointer (SHA-256 '+hashlib.sha256(raw).hexdigest()+')'
    assert f.m['mq_input_context'](f.q,stage)==json.loads(raw)
    path.write_bytes(raw+b' ')
    with pytest.raises(RuntimeError):f.m['mq_verify_input'](f.q,stage)


def test_e2big_is_proven_non_launch_and_next_reviewer_runs(flow,monkeypatch):
    f=flow;job=automatic(f);original=f.m['mq_service_command']
    def command(config,args):
        if args[0]=='systemd-run':raise OSError(errno.E2BIG,'argument list too long')
        return original(config,args)
    monkeypatch.setitem(f.m,'mq_service_command',command)
    f.drain();saved=f.q.job(job['id'])
    assert f.launched==['codex'] and not f.service.units
    assert saved['stages'][0]['state']=='failed' and saved['wait_reason']=='reviewer_retry'
    assert not f.q.jobs('running') and saved['stages'][1]['state']=='succeeded'


def test_restart_full_round_once_preserves_history_and_creates_fresh_chat(flow):
    f=flow;job,hold=held(f);old=copy.deepcopy(job);old_record=copy.deepcopy(f.q.mr(11,82))
    receipt=restart(f,job,hold);saved=f.q.job(job['id'])
    assert saved['source']==old['source'] and f.q.admission(saved)==f.q.admission(old)
    assert saved['stages']==[] and saved['workspace'] is None
    assert saved['rounds'][-1]['stages']==old['stages']
    assert saved['sequence']>old['sequence'] and not f.q.mr(11,82)['hold']
    assert f.q.mr(11,82)['reviewed_head']==old_record['reviewed_head']
    assert restart(f,job,hold)==receipt and f.q.job(job['id'])==saved
    f.results['codex']=domain();f.drain();finished=f.q.job(job['id'])
    assert f.launched==['claude','codex','claude','codex']
    assert finished['stages'][1]['session']!=hold['session']
    assert hold['session'] in f.q.mr(11,82)['codex_contexts']
    assert finished['outcome']=='reviewed' and len(finished['stages'])==2
    assert all(t['id'] not in {s['id'] for s in old['stages']} for t in finished['stages'])
    assert not f.sends


@pytest.mark.parametrize('denial',['stage','head','closed','merged','pending_answer','source','anchor','unknown','running','removed'])
def test_restart_denials_leave_protected_state_unchanged(flow,denial):
    f=flow;job,hold=held(f)
    if denial in {'head','closed','merged'}:
        if denial=='head':f.context['head']='d'*40
        else:f.context['mr']['state']=denial
    if denial in {'pending_answer','anchor'}:
        with f.q.atomic():
            r=f.q.mr(11,82)
            if denial=='pending_answer':r['pending_answers']=[{'source':'already registered'}]
            else:r['hold']['native_anchor']='wrong'
            f.q.put_mr(r)
    if denial=='source':f.items[hold['turn_id']][0]['content']=[{'type':'text','text':'changed input'}]
    if denial=='running':f.turns[hold['session']][0]['status']='inProgress'
    if denial=='removed':f.config['projects']=[{'id':99,'path':'other/repo'}]
    if denial=='unknown':
        with f.q.atomic():f.q.put_effect({'key':'uncertain','repository_id':11,'iid':82,'state':'unknown','job_id':job['id']})
    before=(f.q.jobs(),f.q.mrs(),f.q.effects())
    with pytest.raises((RuntimeError,KeyError)):
        f.m['mq_restart_review'](f.config,job['id'],'wrong' if denial=='stage' else hold['stage_id'],'discard')
    assert (f.q.jobs(),f.q.mrs(),f.q.effects())==before and not f.sends


@pytest.mark.parametrize('moment',['before','between','after_check'])
def test_native_answer_races_restart(flow,monkeypatch,moment):
    f=flow;job,hold=held(f);frontier=f.m['mq_restart_frontier'];calls=[]
    if moment=='before':human(f,hold,result=answer(hold))
    def read(*args):
        value=frontier(*args);calls.append(value)
        if (moment=='between' and len(calls)==1) or (moment=='after_check' and len(calls)==2):
            human(f,hold,result=answer(hold))
        return value
    monkeypatch.setitem(f.m,'mq_restart_frontier',read)
    if moment!='after_check':
        with pytest.raises(RuntimeError,match='unprocessed native human'):restart(f,job,hold)
        assert f.q.mr(11,82)['hold']==hold
    else:
        restart(f,job,hold)
        f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
        dispositions=[json.loads(r['value']) for r in f.q.db.execute("SELECT value FROM metadata WHERE key LIKE 'human:%'")]
        assert any(d and d.get('disposition')=='retired_question_answer' for d in dispositions)
        assert len(f.q.jobs())==1 and not f.q.mr(11,82)['hold']
    assert not f.sends


def test_late_answer_cannot_clear_identical_new_question(flow):
    f=flow;job,hold=held(f);restart(f,job,hold);f.drain()
    new=f.q.mr(11,82)['hold'];assert new['question']==hold['question'] and new['native_anchor']!=hold['native_anchor']
    human(f,hold,result=answer(hold));f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert f.q.mr(11,82)['hold']==new and len(f.q.jobs())==1 and not f.sends


def test_late_answer_without_assessment_uses_readonly_intake(flow):
    f=flow;job,hold=held(f);restart(f,job,hold)
    human(f,hold);f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    intake=next(j for j in f.q.jobs() if j['kind']=='intake')
    assert intake['retired_question']==hold
    # Keep the full review pending while the actual old-chat reply is assessed.
    with f.q.atomic():
        original=f.q.job(job['id']);original['retry_at']=f.m['mq_stamp']()+999;f.q.save(original)
    assessed=domain();assessed['assessment']={'kind':'answer','summary':'continue',
        'text_basis':['continuar'],'scope':hold['scope'],'question_anchor':hold['anchor']}
    f.results['codex']=assessed;f.results['claude']=assessed
    f.drain()
    assert f.q.job(intake['id'])['outcome']=='answer to an operator-retired question; no mutable work'
    assert not f.sends and not f.q.mr(11,82)['hold']


def test_restart_cli_and_transaction_rollback(flow,monkeypatch,capsys):
    f=flow;job,hold=held(f);saved=f.q.jobs();record=f.q.mrs()
    cls=f.m['MonitorQueue'];save=cls.save
    def interrupted(self,value):
        save(self,value)
        if value.get('operator_restarts'):raise RuntimeError('interrupted before commit')
    monkeypatch.setattr(cls,'save',interrupted)
    with pytest.raises(RuntimeError,match='before commit'):restart(f,job,hold)
    assert f.q.jobs()==saved and f.q.mrs()==record
    monkeypatch.setattr(cls,'save',save)
    monkeypatch.setattr('sys.argv',['codex-session-stats','monitor-gitlab','--config',str(f.config_path),
        'restart-review',job['id'],'--stage',hold['stage_id'],'--reason','explicit restart'])
    assert f.m['mq_main']()==0
    result=json.loads(capsys.readouterr().out)
    assert result['restarted'] and result['stage']==hold['stage_id']
    assert f.q.job(job['id'])['stages']==[] and not f.sends


def test_restart_respects_consumer_lock_and_other_running_mr(flow):
    import os
    f=flow;job,hold=held(f)
    lock=f.m['mq_lock'](f.config,'consumer')
    try:
        with pytest.raises(BlockingIOError):restart(f,job,hold)
    finally:os.close(lock)
    other=f.q.enqueue(11,83,source_key='other',kind='code',head='a'*40,
        source={'origin':'automatic'},context=f.context)
    reserved=f.q.reserve({11})
    assert reserved['id']==other['id']
    restart(f,job,hold)
    assert f.q.jobs('running')==[reserved]
    assert f.q.reserve({11})['id']==other['id'] and not f.sends


def test_unrelated_action_in_old_chat_remains_human_work(flow):
    f=flow;job,hold=held(f);restart(f,job,hold)
    text='Publique um achado sobre a validação de login'
    assessment={'kind':'action','summary':text,'effects':['finding'],'discussions':[],'question_anchor':None}
    human(f,hold,text=text,result='```csm-assessment\n'+json.dumps(assessment)+'\n```')
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    request=next(j for j in f.q.jobs() if j['kind']=='human')
    assert request['source']['texts']==[text] and not request.get('retired_question') and not f.sends


@pytest.mark.parametrize('text',['continuar?','continuarw'])
def test_retired_question_does_not_override_question_only_gate(flow,text):
    f=flow;job,hold=held(f);restart(f,job,hold)
    human(f,hold,text=text,result=answer(hold));f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert len(f.q.jobs())==1 and not f.sends


def test_reset_archives_diagnostics_without_reissuing_them(flow):
    f=flow;job=automatic(f);f.drain()
    # Use the real running transition for a fresh round after a genuine hold answer/reset.
    other=f.q.enqueue(11,83,source_key='fresh-reset',kind='discussion',head='a'*40,
        source={'origin':'automatic'},context=f.context)
    running=f.q.reserve({11})
    with f.q.atomic():
        running['validation_error']='old disagreement';running['last_error']={'message':'old failure'};f.q.save(running)
    f.m['mq_reset_round'](f.q,running,'new review')
    saved=f.q.job(other['id'])
    assert saved['rounds'][-1]['diagnostics']['validation_error']=='old disagreement'
    assert not saved.get('validation_error') and not saved.get('last_error')


def test_mr13_saved_artifact_does_not_become_current_decision(flow):
    f=flow;artifact=json.loads((Path(__file__).parent/'fixtures'/'mr13-stale-input.json').read_text())
    assert artifact['hold'] is None and artifact['pending_question'] is None
    job=automatic(f)
    with f.q.atomic():
        job['validation_error']=artifact['validation_error'];f.q.save(job)
    f.step();saved=f.q.job(job['id'])
    assert artifact['validation_error'] not in saved['stages'][0]['input']
    f.drain();assert f.q.job(job['id'])['outcome']=='reviewed' and not f.q.mr(11,82)['hold']


@pytest.mark.parametrize('change',['stdin','transport'])
def test_claude_saved_transport_tampering_rejects_collection(flow,change):
    f=flow;job=automatic(f);f.step();stage=f.q.job(job['id'])['stages'][0]
    root=f.q.path.parent/'executions'/stage['id']
    if change=='stdin':(root/'stdin').write_bytes(b'changed')
    else:
        manifest=json.loads((root/'manifest.json').read_text());manifest['input_transport']='unknown'
        (root/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError):f.m['mq_print_observe'](f.config,stage)
    assert not f.sends and f.q.job(job['id'])['stages'][0]['state']=='running'


def test_historical_prepared_argv_manifest_still_dispatches_exact_input(flow,monkeypatch):
    f=flow;job=automatic(f);original=f.m['mq_service_command']
    def before_issue(c,args):
        if args[0]=='systemd-run':raise f.m['MonitorCycleYield']('before issue')
        return original(c,args)
    monkeypatch.setitem(f.m,'mq_service_command',before_issue)
    with pytest.raises(f.m['MonitorCycleYield']):f.step()
    stage=f.q.job(job['id'])['stages'][0];root=f.q.path.parent/'executions'/stage['id']
    manifest=json.loads((root/'manifest.json').read_text());manifest.pop('input_transport')
    # Authentic historical file input and matching original launch receipt, not a downgrade
    # of a new persisted manifest under its original digest.
    data=stage['input_context'];raw=json.dumps(data).encode()
    inputs=f.q.path.parent/'inputs';inputs.mkdir(mode=0o700)
    path=inputs/(stage['id']+'.json');path.write_bytes(raw);path.chmod(0o600)
    with f.q.atomic():
        current=f.q.job(job['id']);stage=current['stages'][0]
        stage['input']='Old pointer (SHA-256 '+hashlib.sha256(raw).hexdigest()+')'
        for key in ('input_format','input_context','input_digest'):stage.pop(key)
        manifest['input_digest']=f.m['monitor_digest'](stage['input'])
        (root/'manifest.json').write_text(json.dumps(manifest))
        stage['manifest_digest']=f.m['monitor_digest']((root/'manifest.json').read_text())
        f.q.save(current)
    (root/'stdin').unlink()
    monkeypatch.setitem(f.m,'mq_service_command',original)
    f.drain();assert f.q.job(job['id'])['outcome']=='reviewed'
    launch=next(c for c in f.service.commands if c[0]=='systemd-run')
    assert launch[-1]==stage['input'] and not any('StandardInput=' in c for c in launch)


def test_restart_rechecks_original_question_after_first_native_frontier(flow,monkeypatch):
    f=flow;job,hold=held(f);frontier=f.m['mq_restart_frontier']
    def vanished(*args):
        f.items[hold['turn_id']][-1]['text']='The original question disappeared'
        return frontier(*args)
    monkeypatch.setitem(f.m,'mq_restart_frontier',vanished)
    before=(f.q.jobs(),f.q.mrs())
    with pytest.raises(RuntimeError,match='question identity'):restart(f,job,hold)
    assert (f.q.jobs(),f.q.mrs())==before and not f.sends


@pytest.mark.parametrize('gap',['stage','model_selection'])
def test_cold_resume_empty_preparation_completes_exact_stage(flow,monkeypatch,gap):
    f=flow;job=automatic(f);cls=f.m['MonitorQueue'];start=cls.stage_start;prepare=f.m['mq_input']
    def stage_start(self,*args,**kwargs):
        start(self,*args,**kwargs)
        raise f.m['MonitorCycleYield']('interrupted after stage_start')
    def input(*args):raise f.m['MonitorCycleYield']('interrupted after model selection')
    if gap=='stage':monkeypatch.setattr(cls,'stage_start',stage_start)
    else:monkeypatch.setitem(f.m,'mq_input',input)
    with pytest.raises(f.m['MonitorCycleYield']):f.step()
    saved=f.q.job(job['id']);stage=copy.deepcopy(saved['stages'][0])
    assert stage['input']=='' and stage['delivery']=='prepared' and not f.launched
    monkeypatch.setattr(cls,'stage_start',start);monkeypatch.setitem(f.m,'mq_input',prepare)
    connection=cls(f.config)
    try:
        assert f.step(connection)
        recovered=connection.job(job['id'])['stages'][0]
        assert recovered['id']==stage['id'] and recovered['input_format']=='message-v1'
        f.drain()
        assert connection.job(job['id'])['outcome']=='reviewed' and f.launched==['claude','codex']
    finally:connection.close()


def test_restart_refuses_already_queued_unassessed_native_answer(flow):
    f=flow;job,hold=held(f);human(f,hold)
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    assert any(j['kind']=='intake' for j in f.q.jobs())
    assert not f.q.mr(11,82).get('pending_answers')
    before=(f.q.jobs(),f.q.mrs(),f.q.effects())
    with pytest.raises(RuntimeError,match='unprocessed native human assessment'):restart(f,job,hold)
    assert (f.q.jobs(),f.q.mrs(),f.q.effects())==before and not f.sends


def test_restart_preserves_confirmed_publication_identity(flow):
    f=flow
    f.results['claude']=domain(actions=[{'key':'original-finding','kind':'finding','body':'[P2] Verify login groups.',
        'position':{'position_type':'text','base_sha':'b'*40,'start_sha':'c'*40,'head_sha':'a'*40,
                    'old_path':'x.py','new_path':'x.py','new_line':1}}])
    job,hold=held(f);effects=copy.deepcopy(f.q.effects())
    assert len(effects)==1 and effects[0]['state']=='confirmed' and len(f.sends)==1
    restart(f,job,hold)
    assert f.q.effects()==effects and len(f.sends)==1 and f.q.mr(11,82)['reviewed_head'] is None
    f.results['claude']=domain();f.results['codex']=domain();f.drain()
    assert f.q.effects()==effects and len(f.sends)==1
    assert f.q.mr(11,82)['reviewed_head']=='a'*40


@pytest.mark.parametrize('partial',['representation','native','historical'])
def test_empty_prepared_input_with_prior_evidence_is_not_regenerated(flow,monkeypatch,partial):
    f=flow;job=automatic(f);prepare=f.m['mq_input']
    def interrupted(*args):raise f.m['MonitorCycleYield']('before input')
    monkeypatch.setitem(f.m,'mq_input',interrupted)
    with pytest.raises(f.m['MonitorCycleYield']):f.step()
    with f.q.atomic():
        current=f.q.job(job['id']);stage=current['stages'][0]
        if partial=='representation':stage['input_format']='message-v1'
        elif partial=='native':stage['session']=str(uuid.uuid4())
        else:
            root=f.q.path.parent/'inputs';root.mkdir(mode=0o700)
            path=root/(stage['id']+'.json');path.write_text('{}');path.chmod(0o600)
        f.q.save(current)
    monkeypatch.setitem(f.m,'mq_input',prepare)
    with pytest.raises((RuntimeError,OSError)):f.step()
    assert not f.launched and f.q.job(job['id'])==current


@pytest.mark.parametrize('changed',['input_transport','session','deadline'])
def test_prepared_claude_manifest_cannot_change_before_issue(flow,monkeypatch,changed):
    f=flow;job=automatic(f);command=f.m['mq_service_command']
    def before_issue(c,args):
        if args[0]=='systemd-run':raise f.m['MonitorCycleYield']('before issue')
        return command(c,args)
    monkeypatch.setitem(f.m,'mq_service_command',before_issue)
    with pytest.raises(f.m['MonitorCycleYield']):f.step()
    stage=f.q.job(job['id'])['stages'][0];path=f.q.path.parent/'executions'/stage['id']/'manifest.json'
    saved=json.loads(path.read_text())
    if changed=='input_transport':saved.pop(changed)
    elif changed=='session':saved[changed]=str(uuid.uuid4())
    else:saved[changed]+=50
    path.write_text(json.dumps(saved))
    monkeypatch.setitem(f.m,'mq_service_command',command)
    f.step();failed=f.q.job(job['id'])['stages'][0]
    assert failed['state']=='failed' and 'manifest changed' in failed['error']['message']
    assert not f.launched and not f.service.units
    f.drain();assert f.launched==['codex'] and not f.sends
