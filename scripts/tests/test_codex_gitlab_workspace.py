"""Workspace hand-off through the real FIFO/adapters; native wires are fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import uuid

import pytest

from test_codex_gitlab_queue import flow, module, domain, rendered, assessment


@pytest.fixture
def project(flow, monkeypatch):
    f = flow
    base = Path(f.config['cwd'])
    roots = [str(base / ('source '+str(i))) for i in range(5)]
    for root in roots:
        Path(root).mkdir()
    identifier = str(uuid.uuid4())
    raw = dict(f.raw)
    for key in ('cwd','model','effort'):
        raw.pop(key)
    raw['analysis_config'] = 'analysis.toml'
    raw['codex_project_binding'] = {'id':identifier,'name':'workspace 7','roots':roots[:],
                                    'existing_threads':{}}
    analysis = base/'analysis.toml'
    analysis.write_text('model="gpt-6.1-sol"\nmodel_reasoning_effort="xhigh"\ncodex_project_name="workspace 7"\n')
    analysis.chmod(0o600)
    f.config_path.write_text(json.dumps(raw))
    f.config.clear()
    f.config.update(f.m['mq_config'](f.config_path))
    native = f.m['monitor_native']
    claude = f.m['mq_claude_command']
    f.live = {'id':identifier,'name':'workspace 7','roots':roots}
    f.wire, f.claude_wire = [], []
    def wire(config, method, params, **kwargs):
        f.wire.append((method,copy.deepcopy(params)))
        if method == 'project/list':
            return {'data':[{**f.live,'roots':[{'path':p} for p in f.live['roots']]}], 'nextCursor':None}
        if method == 'mcpServer/tool/call':
            if params['tool'] == 'list_projects':
                result={'schemaVersion':2,'projects':[{'projectKind':'local','hostId':'local',
                    'label':'workspace 7','projectId':identifier,'path':f.live['roots'][0]}]}
            else:
                assert params['tool'] == 'move_thread_to_project'
                result=params['arguments']
            return {'content':[{'type':'text','text':json.dumps(result)}]}
        return native(config,method,params,**kwargs)
    def cli(config, args):
        if args[0] == '--print':
            f.claude_wire.append((config['cwd'],args[:]))
        return claude(config,args)
    monkeypatch.setitem(f.m,'monitor_native',wire)
    monkeypatch.setitem(f.m,'mq_claude_command',cli)
    return f


def enqueue(f, key='one', kind='code'):
    return f.q.enqueue(11,82,source_key=key,kind=kind,head='a'*40,
        source={'origin':'automatic'},context=copy.deepcopy(f.context))


def additional(args):
    start=args.index('--add-dir')+1
    end=next(i for i in range(start,len(args)) if args[i].startswith('--'))
    return args[start:end]


@pytest.mark.parametrize('model,expected',[(None,'claude-opus-5-5'),('claude-sonnet-5-5','claude-sonnet-5-5')])
def test_claude_default_and_toml_override_reach_native_cli(project,model,expected):
    f=project
    analysis=f.config_path.parent/'analysis.toml'
    if model is not None:
        with analysis.open('a') as stream:stream.write('claude_model='+json.dumps(model)+'\n')
    loaded=f.m['mq_config'](f.config_path)
    f.config.clear();f.config.update(loaded)
    enqueue(f);f.drain()
    args=f.claude_wire[0][1]
    assert args.count('--model')==1
    assert args[args.index('--model')+1]==expected
    assert f.q.jobs()[0]['state']=='completed'
    assert f.sends==[]


def test_same_five_roots_reach_both_real_dispatchers_without_global_writes(project):
    f=project
    config_before=f.config_path.read_bytes()
    native_before=(Path(f.config['codex_home'])/'config.toml').read_bytes()
    enqueue(f)
    f.drain()
    assert f.launched == ['claude','codex']
    job=f.q.jobs()[0]
    roots=f.live['roots']
    assert job['workspace']['roots'] == roots
    assert f.claude_wire[0][0] == roots[0]
    assert additional(f.claude_wire[0][1]) == roots[1:]
    args=f.claude_wire[0][1]
    assert '--setting-sources' in args and args[args.index('--setting-sources')+1] == ''
    assert str(f.q.path.parent/'inputs') not in additional(args)
    settings=json.loads(args[args.index('--settings')+1])
    assert settings['sandbox']['failIfUnavailable'] is True
    assert settings['sandbox']['allowUnsandboxedCommands'] is False
    assert 'Bash' in args and 'Read,Grep,Glob,Bash,Edit,Write' in args
    starts=[p for method,p in f.wire if method=='thread/start']
    assert starts[0]['runtimeWorkspaceRoots'] == roots
    policy=starts[0]['config']['permissions.'+f.m['MQ_PERMISSION_PROFILE']]
    assert all(policy['filesystem'][p]=='write' for p in roots)
    assert all(policy['filesystem'][str(Path(p)/'.git')]=='write' for p in roots)
    assert policy['network']['unix_sockets'] == {f.config['socket']:'deny'}
    assert policy['filesystem'][str(f.q.path.parent)] == 'read'
    for stage in job['stages']:
        data=json.loads((f.q.path.parent/'inputs'/(stage['id']+'.json')).read_text())
        assert data['workspace'] == job['workspace']
    assert f.config_path.read_bytes() == config_before
    assert (Path(f.config['codex_home'])/'config.toml').read_bytes() == native_before
    assert f.sends == []


def test_folder_addition_during_round_and_restart_only_changes_the_next_round(project):
    f=project; first=enqueue(f)
    f.m['mq_step'](f.config,f.q)
    saved=f.q.job(first['id'])['workspace']
    extra=Path(f.config['cwd']).parent/'new folder';extra.mkdir()
    f.live['roots'].append(str(extra))
    reopened=f.m['MonitorQueue'](f.config)
    try:
        for _ in range(10):
            if not f.m['mq_step'](f.config,reopened):break
        else:pytest.fail('restarted round did not terminate')
    finally:reopened.close()
    first=f.q.job(first['id'])
    assert first['workspace'] == saved
    assert f.launched == ['claude','codex']
    assert len([p for method,p in f.wire if method=='project/list']) == 1
    assert [p for method,p in f.wire if method=='thread/start'][0]['runtimeWorkspaceRoots'] == saved['roots']
    old=f.q.mr(11,82)['chats']['codex']
    enqueue(f,'two');f.drain()
    record=f.q.mr(11,82)
    assert record['chats']['codex'] != old
    assert record['codex_contexts'][old]['roots'] == saved['roots']
    assert f.q.jobs()[1]['workspace']['roots'] == f.live['roots']
    assert f.launched == ['claude','codex','claude','codex']


def native_human(f, session, text, result=None):
    turn=str(uuid.uuid4());source_id='human-'+turn
    f.turns[session].insert(0,{'id':turn,'status':'completed'})
    f.items[turn]=[{'type':'userMessage','id':source_id,'content':[{'type':'text','text':text}]}]
    if result:
        f.items[turn].append({'type':'agentMessage','id':'final-'+turn,'phase':'final_answer','text':rendered(result)})
    return {'origin':'human','provider':'codex','session':session,'turn_id':turn,
        'source_id':source_id,'texts':[text],'cwd':f.chats[session]['cwd'],
        'project_id':f.chats[session]['projectId'],'mixed':False,'automated':False}


def test_original_codex_hold_source_survives_root_change_and_readonly_intake(project):
    f=project
    f.results['codex']=domain(outcome='question',question='Qual regra devo usar?')
    original=enqueue(f);f.drain()
    hold=f.q.mr(11,82)['hold']; old=hold['session']
    extra=Path(f.config['cwd']).parent/'added';extra.mkdir();f.live['roots'].append(str(extra))
    native_human(f,old,'preciso explicar melhor a regra')
    f.m['mq_intake'](f.config,f.q,f.q.mr(11,82))
    f.results.update(claude=domain(outcome='noop'),codex=domain(outcome='noop'))
    f.drain()
    record=f.q.mr(11,82)
    assert record['chats']['codex'] != old and record['hold'] == hold
    intake=f.q.jobs()[1]
    assert intake['kind'] == 'intake' and intake['state'] == 'completed'
    starts=[p for method,p in f.wire if method=='thread/start']
    policy=starts[-1]['config']['permissions.'+f.m['MQ_PERMISSION_PROFILE']]
    assert 'write' not in policy['filesystem'].values()
    args=f.claude_wire[-1][1]
    assert 'Read,Grep,Glob,Bash' in args and 'Read,Grep,Glob,Bash,Edit,Write' not in args
    assert 'Bash' not in args
    text='use a regra atual e continue'
    answer=domain(assessment=assessment(text,kind='answer',anchor=hold['anchor']))
    answer['assessment']['scope']={'effects':['finding'],'discussions':[]}
    source=native_human(f,old,text,answer)
    f.m['mq_intake'](f.config,f.q,record)
    assert f.q.mr(11,82)['hold'] == hold
    assert f.q.job(original['id'])['wait_reason'] == 'answer_ready'
    f.results.update(claude=domain(),codex=domain());f.drain()
    record=f.q.mr(11,82)
    assert record['hold'] is None
    assert record['hold_history'][0]['answer'] == source
    assert f.q.job(original['id'])['rounds'][0]['workspace']['roots'] != f.live['roots']
    assert f.sends == []


def test_stale_missing_folder_does_not_block_current_project_read(project):
    f=project
    removed=Path(f.live['roots'].pop())
    removed.rmdir()
    fresh=f.m['mq_config'](f.config_path)
    job=enqueue(f)
    f.drain()
    assert f.q.job(job['id'])['state'] == 'completed'
    assert f.q.job(job['id'])['workspace']['roots'] == f.live['roots']
    assert fresh['codex_project_binding']['roots'][-1] == str(removed)


def test_same_name_different_project_is_not_authorized(project):
    f=project;f.live['id']=str(uuid.uuid4())
    enqueue(f)
    with pytest.raises(RuntimeError,match='native project identity changed'):
        f.m['mq_step'](f.config,f.q)
    assert f.launched == [] and f.sends == []


def test_git_metadata_grants_do_not_include_main_checkout_code(flow):
    f=flow;base=Path(f.config['cwd']); main=base/'main';work=base/'worktree'
    subprocess.run(['git','init','-q',str(main)],check=True)
    subprocess.run(['git','-C',str(main),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
        'commit','-q','--allow-empty','-m','Fixture'],check=True)
    subprocess.run(['git','-C',str(main),'worktree','add','--detach',str(work),'HEAD'],
                   check=True,capture_output=True,text=True)
    roots=[str(work)]
    metadata=f.m['mq_git_metadata'](roots)
    assert str(main/'.git') in metadata and str(main) not in metadata
    config={**f.config,'_workspace':{'roots':roots,'git_metadata':metadata},'_workspace_write':True}
    profile=f.m['mq_permission_profile'](config)
    assert profile['filesystem'][str(main/'.git')] == 'write'
    assert str(main) not in profile['filesystem']
    args=f.m['mq_claude_arguments'](config,'fixture','name')
    settings=json.loads(args[args.index('--settings')+1])
    assert settings['sandbox']['filesystem']['allowWrite'] == metadata
    assert '--add-dir' not in args


def test_claude_does_not_copy_global_extra_folders_or_hooks(flow):
    f=flow
    home=Path(f.config['claude_home']);home.mkdir()
    source={'model':'original-model','effortLevel':'high','permissions':{'additionalDirectories':['/not-workspace']},
            'hooks':{'PreToolUse':[{'command':'unexpected'}]}}
    (home/'settings.json').write_text(json.dumps(source))
    job=enqueue(f);job=f.q.reserve({11})
    config=f.m['mq_workspace'](f.config,f.q,job)
    args=f.m['mq_claude_arguments'](config,'fixture','name')
    settings=json.loads(args[args.index('--settings')+1])
    assert settings['model'] == 'original-model' and settings['effortLevel'] == 'high'
    assert '/not-workspace' not in json.dumps(settings) and 'hooks' not in settings
    assert args[args.index('--setting-sources')+1] == ''
