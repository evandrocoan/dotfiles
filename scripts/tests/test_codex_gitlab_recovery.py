"""Real queue/tick recovery and recorded native artifacts; external providers are simulated."""
import copy
import json
from pathlib import Path
import uuid

import pytest

from test_codex_gitlab_queue import historical_hold, assessment, domain, flow, module, rendered, compact
from test_codex_gitlab_workspace import project
from test_codex_gitlab_periodic import quiet_scan


FIXTURES = Path(__file__).parent/'fixtures'


def captured_claude(m, tmp_path, monkeypatch, *, records=None, state='running',
                    artifact_name='gitlab-claude-tool-transcript.json'):
    artifact=json.loads((FIXTURES/artifact_name).read_text())
    rows=copy.deepcopy(artifact['records'] if records is None else records)
    session=rows[0]['sessionId'];source=next(r for r in rows if r.get('uuid')==artifact['registered_source_uuid'])
    config={'claude_home':str(tmp_path/'claude'),'cwd':str(tmp_path),'max_response_bytes':2**20}
    stage={'reviewer':'claude','session':session,'background_id':session[:8],'name':'captured !5',
        'input':source['message']['content']}
    for row in rows:row['cwd']=config['cwd']
    root=Path(config['claude_home'])/'projects'/'fixture';root.mkdir(parents=True,exist_ok=True)
    target=root/(session+'.jsonl')
    target.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    monkeypatch.setitem(m,'mq_claude_command',lambda *a:json.dumps([{'kind':'background',
        'id':stage['background_id'],'sessionId':session,'name':stage['name'],'cwd':config['cwd'],'state':state}]))
    return config,stage,rows,target


def test_recorded_tool_chain_and_split_final_are_collected_without_stopping_remote_control(module,tmp_path,monkeypatch):
    m=module['mq_step'].__globals__;config,stage,rows,path=captured_claude(m,tmp_path,monkeypatch)
    actual=m['mq_claude_observe'](config,stage)
    assert actual['terminal'] is True and actual['text']=='Captured final review text.'
    assert actual['anchor']=='37ff9ce3-a30c-4a6d-9c8d-172b00d0b78f'
    assert actual['source_id']=='cce5519b-9edd-4c9a-bcfe-263acbdd9c50'
    assert 'remote_url' not in actual
    assert path.read_text()==''.join(json.dumps(row)+'\n' for row in rows)


@pytest.mark.parametrize('change',['thinking_only','unsealed_text','mixed_user','wrong_tool','reused_tool',
    'distinct_final','sibling_seal','early_seal','block_after_seal'])
def test_partial_or_unauthenticated_claude_final_cannot_complete(module,tmp_path,monkeypatch,change):
    m=module['mq_step'].__globals__
    artifact=json.loads((FIXTURES/'gitlab-claude-tool-transcript.json').read_text());rows=artifact['records']
    if change=='thinking_only':
        index=next(i for i,r in enumerate(rows) if r.get('uuid')=='cbfb4d71-6861-4eb7-92ba-ff69b0079bc5');rows=rows[:index+1]
    elif change=='unsealed_text':rows=[r for r in rows if r.get('subtype')!='turn_duration']
    elif change in {'mixed_user','wrong_tool','reused_tool'}:
        tool=next(r for r in rows if r.get('type')=='user' and isinstance(r.get('message',{}).get('content'),list))
        if change=='mixed_user':tool['message']['content'].append({'type':'text','text':'responda de outro modo'})
        elif change=='wrong_tool':tool['message']['content'][0]['tool_use_id']='foreign-call'
        else:tool['message']['content'].append(copy.deepcopy(tool['message']['content'][0]))
    elif change=='distinct_final':
        row=next(r for r in rows if r.get('uuid')=='37ff9ce3-a30c-4a6d-9c8d-172b00d0b78f')
        row['message']['id']='different-native-message'
    elif change in {'sibling_seal','early_seal'}:
        seal=next(r for r in rows if r.get('subtype')=='turn_duration')
        seal['parentUuid']=artifact['registered_source_uuid']
        if change=='early_seal':rows.remove(seal);rows.insert(1,seal)
    else:
        block=copy.deepcopy(next(r for r in rows if r.get('uuid')=='37ff9ce3-a30c-4a6d-9c8d-172b00d0b78f'))
        block.update(uuid=str(uuid.uuid4()),parentUuid=next(r['uuid'] for r in rows if r.get('subtype')=='turn_duration'))
        rows.append(block)
    config,stage,_,_=captured_claude(m,tmp_path,monkeypatch,records=rows)
    if change in {'distinct_final','block_after_seal'}:
        expected='ambiguous Claude terminal result' if change=='distinct_final' else 'blocks after completion'
        with pytest.raises(RuntimeError,match=expected):m['mq_claude_observe'](config,stage)
    else:assert m['mq_claude_observe'](config,stage)['terminal'] is False


def test_human_intake_uses_same_recorded_tool_ancestry(flow,tmp_path,monkeypatch):
    config,stage,rows,path=captured_claude(flow.m,tmp_path,monkeypatch)
    record=flow.q.mr(11,82);record['chats']['claude']=stage['session']
    candidates=list(flow.m['mq_session_candidates'](config,flow.q,record,'claude',stage['session']))
    assert len(candidates)==1
    _,source,text=candidates[0]
    assert source['source_id']=='cce5519b-9edd-4c9a-bcfe-263acbdd9c50'
    assert source['mixed'] is False and text=='Captured final review text.'


def test_sufficient_human_answer_with_tool_results_releases_only_original_hold(flow):
    flow.results['claude']=domain(outcome='question',question='Qual regra usar?')
    job=enqueue(flow);flow.drain();hold=copy.deepcopy(flow.q.mr(11,82)['hold'])
    historical_hold(flow)
    artifact=json.loads((FIXTURES/'gitlab-claude-tool-transcript.json').read_text())
    rows=artifact['records'];text='use a regra atual e continue'
    answer=domain(assessment=assessment(text,kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    for row in rows:
        row.update(sessionId=hold['session'],cwd=flow.config['cwd'])
        if row['uuid']==artifact['registered_source_uuid']:
            row['message']['content']=text;row['parentUuid']=hold['native_anchor']
        if row.get('uuid')=='37ff9ce3-a30c-4a6d-9c8d-172b00d0b78f':
            row['message']['content']=[{'type':'text','text':compact(answer)}]
    path=next((Path(flow.config['claude_home'])/'projects').glob('*/'+hold['session']+'.jsonl'))
    with path.open('a') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')
    flow.m['mq_intake'](flow.config,flow.q,flow.q.mr(11,82))
    record=flow.q.mr(11,82)
    assert record['hold']==hold
    assert record['pending_answers'][0]['source']['source_id']==artifact['registered_source_uuid']
    assert flow.q.job(job['id'])['wait_reason']=='answer_ready' and flow.sends==[]
    flow.results['claude']=domain();flow.drain()
    assert flow.q.mr(11,82)['hold'] is None
    assert flow.q.mr(11,82)['hold_history'][0]['answer']['source_id']==artifact['registered_source_uuid']


def cold_context(m,tmp_path):
    artifact=json.loads((FIXTURES/'gitlab-codex-cold-context.json').read_text())
    thread=artifact['thread'];records=artifact['rollout']
    home=tmp_path/'codex';folder=home/'sessions'/'fixture';folder.mkdir(parents=True);home.chmod(artifact['native_home_mode'])
    path=folder/(thread['id']+'.jsonl');path.write_text(''.join(json.dumps(r)+'\n' for r in records));path.chmod(artifact['native_rollout_mode'])
    thread['path']=str(path)
    roots=records[0]['payload']['runtime_workspace_roots']
    record={'codex_contexts':{thread['id']:{'cwd':thread['cwd'],'project_id':thread['projectId'],'roots':roots}}}
    return {'codex_home':str(home),'max_response_bytes':2**20},thread,record,records,path


def test_recorded_cold_context_uses_latest_protected_native_metadata(module,tmp_path):
    m=module['mq_step'].__globals__;config,thread,record,rows,path=cold_context(m,tmp_path)
    before=path.read_bytes()
    assert m['mq_verify_codex_context'](config,record,thread,thread['id']) is None
    assert path.read_bytes()==before and thread['environments'] is None


@pytest.mark.parametrize('change',['latest_roots','latest_missing_roots','latest_absent','latest_cwd',
    'session','project','loaded','ambiguous','foreign_path','symlink','oversize','public_home'])
def test_cold_context_rejects_changed_or_unavailable_evidence(module,tmp_path,change):
    m=module['mq_step'].__globals__;config,thread,record,rows,path=cold_context(m,tmp_path)
    if change=='latest_roots':rows[-1]['payload']['workspace_roots']=['/different']
    elif change=='latest_missing_roots':rows[-1]['payload'].pop('workspace_roots')
    elif change=='latest_absent':rows.pop()
    elif change=='latest_cwd':rows[-1]['payload']['cwd']='/different'
    elif change=='session':rows[0]['payload']['id']=str(uuid.uuid4())
    elif change=='project':thread['projectId']='different-project'
    elif change=='loaded':thread['status']={'type':'idle'}
    elif change=='ambiguous':thread['environments']=[{},{}]
    elif change=='foreign_path':thread['path']=str(tmp_path/'outside.jsonl')
    elif change=='symlink':
        link=path.with_name('link.jsonl');link.symlink_to(path);thread['path']=str(link)
    elif change=='oversize':config['max_response_bytes']=10
    elif change=='public_home':Path(config['codex_home']).chmod(0o755)
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    expected={'latest_roots':'project/workspace context mismatch','latest_missing_roots':'cold workspace roots',
        'latest_cwd':'cold workspace roots','session':'cold context identity mismatch','project':'workspace/project changed',
        'loaded':'workspace environment is unavailable','ambiguous':'workspace environment is unavailable',
        'foreign_path':'outside protected history','symlink':'outside protected history','oversize':'exceeds configured bound',
        'latest_absent':'latest native cold context is missing','public_home':'runtime must be private'}
    with pytest.raises(RuntimeError,match=expected[change]):
        m['mq_verify_codex_context'](config,record,thread,thread['id'])


def enqueue(f,key='one',iid=82):
    return f.q.enqueue(11,iid,source_key=key,kind='code',head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context))


def completed_stages(f):
    for _ in range(4):assert f.step()
    job=f.q.jobs('running')[0]
    assert [s['state'] for s in job['stages']]==['succeeded','succeeded']
    return copy.deepcopy(job)


def test_operation_retry_and_restart_preserve_completed_reviews(flow,monkeypatch):
    job=enqueue(flow);before=completed_stages(flow)
    original=flow.m['mq_context']
    def fail(*a,**kw):raise RuntimeError('temporary provider read failure')
    monkeypatch.setitem(flow.m,'mq_context',fail)
    progressed=flow.m['mq_consume'](flow.config,flow.q)
    saved=flow.q.job(job['id'])
    assert saved['stages']==before['stages'] and saved['workspace']==before['workspace']
    assert saved['state']=='pending' and saved['wait_reason']=='retry' and progressed is True
    assert saved['last_error']['error']=='temporary provider read failure'
    assert flow.q.mr(11,82)['reviewed_head'] is None and flow.sends==[]
    monkeypatch.setitem(flow.m,'mq_context',original)
    monkeypatch.setitem(flow.m,'mq_stamp',lambda:saved['retry_at']+1)
    reopened=flow.m['MonitorQueue'](flow.config)
    try:
        assert flow.m['mq_consume'](flow.config,reopened)
        assert reopened.job(job['id'])['outcome']=='reviewed'
        assert reopened.job(job['id'])['stages']==before['stages']
    finally:reopened.close()
    assert flow.launched==['claude','codex'] and flow.sends==[]


def test_two_persistent_context_failures_do_not_starve_third_job_in_one_tick(flow,monkeypatch):
    quiet_scan(flow,monkeypatch)
    first=enqueue(flow,'first',81);second=enqueue(flow,'second',83);third=enqueue(flow,'third')
    original=flow.m['mq_context']
    def context(c,iid,**kw):
        if iid in (81,83):raise flow.m['MonitorDeferred']('current diff is incomplete')
        return original(c,iid,**kw)
    monkeypatch.setitem(flow.m,'mq_context',context)
    flow.tick()
    assert flow.q.job(third['id'])['stages'] and flow.launched==['claude']
    for job in (first,second):
        saved=flow.q.job(job['id'])
        assert saved['wait_reason']=='retry' and saved['stages']==[]
        assert saved['last_error']['error']=='current diff is incomplete'
    assert flow.q.job(third['id'])['stages'][0]['delivery']=='accepted'
    assert flow.launched==['claude'] and flow.sends==[]


def test_cold_read_after_real_dispatch_does_not_repeat_review(project,monkeypatch):
    f=project;job=enqueue(f);before=completed_stages(f)
    stage=before['stages'][-1];native=f.chats[stage['session']]
    folder=Path(f.config['codex_home'])/'sessions';folder.mkdir()
    path=folder/(stage['session']+'.jsonl')
    rows=[{'type':'session_meta','payload':{'id':stage['session'],'cwd':native['cwd'],
        'runtime_workspace_roots':before['workspace']['roots']}},
        {'type':'turn_context','payload':{'cwd':native['cwd'],'workspace_roots':before['workspace']['roots']}}]
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows));path.chmod(0o600)
    Path(f.config['codex_home']).chmod(0o700)
    native.update(status={'type':'notLoaded'},environments=None,path=str(path))
    calls=len(f.wire)
    assert f.m['mq_consume'](f.config,f.q)
    assert f.q.job(job['id'])['outcome']=='reviewed' and f.launched==['claude','codex']
    assert not any(method=='thread/resume' for method,_ in f.wire[calls:])


@pytest.mark.parametrize('malformed',['malformed\n','null\n','{"type":"user","sessionId":"11111111-1111-4111-8111-111111111111","message":null}\n'])
def test_status_uses_cli_resume_without_reading_historical_web_metadata(flow,tmp_path,monkeypatch,malformed):
    config,stage,rows,path=captured_claude(flow.m,tmp_path,monkeypatch)
    config.update(flow.config);config['claude_home']=str(tmp_path/'claude')
    job=enqueue(flow);active=flow.q.reserve({11})
    active['rounds']=[{'reason':'old terminal error','stages':[stage]}]
    with flow.q.atomic():flow.q.save(active)
    before=copy.deepcopy(flow.q.job(job['id']));raw=path.read_bytes()
    status=flow.m['mq_status'](config)
    assert stage['session'] in status['jobs'][0]['rounds'][0]['stages'][0]['resume_command']
    assert flow.q.job(job['id'])==before and path.read_bytes()==raw
    path.write_text(malformed)
    status=flow.m['mq_status'](config)
    assert 'remote_url' not in status['jobs'][0]['rounds'][0]['stages'][0]
    assert stage['session'] in status['jobs'][0]['rounds'][0]['stages'][0]['resume_command']
    assert flow.q.job(job['id'])==before


def finding(key):
    return {'key':key,'kind':'finding','body':'[P2] '+key,
        'position':{'position_type':'text','base_sha':'b'*40,'start_sha':'c'*40,'head_sha':'a'*40,
            'old_path':'x.py','new_path':'x.py','new_line':1}}




def test_changed_head_after_operation_error_does_not_publish_cached_result(flow,monkeypatch):
    job=enqueue(flow);before=completed_stages(flow);original=flow.m['mq_context']
    def fail(*a,**kw):raise RuntimeError('temporary read failure')
    monkeypatch.setitem(flow.m,'mq_context',fail);flow.m['mq_consume'](flow.config,flow.q)
    saved=flow.q.job(job['id'])
    monkeypatch.setitem(flow.m,'mq_context',original);monkeypatch.setitem(flow.m,'mq_stamp',lambda:saved['retry_at']+1)
    flow.context['head']='d'*40;flow.context['mr']['sha']='d'*40
    flow.m['mq_consume'](flow.config,flow.q);flow.m['mq_consume'](flow.config,flow.q)
    assert flow.q.job(job['id'])['outcome']=='context changed; completed publications preserved'
    assert flow.q.job(job['id'])['stages']==before['stages']
    assert flow.q.mr(11,82)['reviewed_head'] is None and flow.sends==[]








def test_earlier_sibling_marker_cannot_admit_human_answer(flow,tmp_path,monkeypatch):
    artifact=json.loads((FIXTURES/'gitlab-claude-tool-transcript.json').read_text())
    rows=artifact['records'];seal=next(r for r in rows if r.get('subtype')=='turn_duration')
    seal['parentUuid']=artifact['registered_source_uuid']
    config,stage,_,_=captured_claude(flow.m,tmp_path,monkeypatch,records=rows)
    record=flow.q.mr(11,82);record['chats']['claude']=stage['session']
    assert list(flow.m['mq_session_candidates'](config,flow.q,record,'claude',stage['session']))==[]
    assert flow.q.mr(11,82)['hold'] is None and flow.q.jobs()==[]
