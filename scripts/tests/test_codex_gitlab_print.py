"""Finite print execution through the real consumer; service/native transport is simulated."""
import copy
import hashlib
import json
from pathlib import Path
import uuid

import pytest

from test_codex_gitlab_queue import flow, module, domain, rendered
from test_codex_gitlab_periodic import enqueue, quiet_scan


def launch(f):
    job=enqueue(f)
    assert f.m['mq_step'](f.config,f.q)
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
    def forbidden(*args):raise AssertionError('retired completion authority')
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
    assert not f.m['mq_step'](f.config,f.q)
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
    assert f.launched==['claude','codex'] and saved['state']=='completed'


def test_lost_launch_acknowledgment_reconciles_same_invocation_once(flow,monkeypatch):
    f=flow;original=f.m['mq_service_command']
    def command(c,args):
        result=original(c,args)
        if args[0]=='systemd-run':raise RuntimeError('lost acknowledgment after service accepted')
        return result
    monkeypatch.setitem(f.m,'mq_service_command',command)
    job=enqueue(f);f.m['mq_step'](f.config,f.q)
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
    f.m['mq_step'](f.config,f.q)
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
    first=values[1];second=copy.deepcopy(first);second['uuid']=str(uuid.uuid4());second['parentUuid']=first['uuid']
    # The installed CLI result envelope carries only the last text block.
    first['message']['content']=[{'type':'text','text':'Review result:'}]
    values.insert(2,second);values[3]['parentUuid']=second['uuid']
    later_user={'type':'user','uuid':str(uuid.uuid4()),'sessionId':stage['session'],
                'parentUuid':second['uuid'],'message':{'content':'A later human input'}}
    later=copy.deepcopy(second);later.update(uuid=str(uuid.uuid4()),parentUuid=later_user['uuid'])
    later['message']['id']='later';values.extend([later_user,later]);save_records(path,values)
    events[0]['message']=first['message']
    events.insert(1,{'type':'assistant','uuid':second['uuid'],'session_id':stage['session'],
                     'parent_tool_use_id':None,'message':second['message']})
    child=copy.deepcopy(events[1]);child['uuid']=str(uuid.uuid4());child['parent_tool_use_id']='tool-child'
    events.insert(2,child);rewrite_output(f,stage,events)
    f.m['mq_step'](f.config,f.q)
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
