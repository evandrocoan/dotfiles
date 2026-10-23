"""Multi-repository configuration of the fresh global FIFO; no namespace migration."""
import json
import os
from pathlib import Path
import runpy
import pytest

CLI=Path(os.environ.get('CODEX_MONITOR_TEST_CLI',Path(__file__).resolve().parents[2]/'.local/bin/codex-session-stats'))

@pytest.fixture
def configured(tmp_path):
    m=runpy.run_path(str(CLI))
    raw=m['monitor_default_config']('https://gitlab.example.test/team/one',11,'gitlab')
    raw.update(state_file=str(tmp_path/'old'/'state.sqlite3'),codex_home=str(tmp_path/'codex'))
    for key in ('cwd','model','effort','project_id','project_path','gitlab_url'):
        raw.pop(key)
    raw['analysis_config']='analysis.toml'
    target=tmp_path/'config.json';target.write_text(json.dumps(raw));target.chmod(0o600)
    analysis=tmp_path/'analysis.toml'
    def write(entries):
        text='codex_model="gpt-6.1-sol"\ncodex_effort="xhigh"\nworkspace='+json.dumps(str(tmp_path))+'\ngitlab_url="https://gitlab.example.test"\nreviewers=["claude","codex"]\n'
        text+='projects = ['+','.join('{ id = '+str(e['id'])+', path = '+json.dumps(e['path'])+' }' for e in entries)+']\n'
        analysis.write_text(text);analysis.chmod(0o600)
    write([{'id':11,'path':'team/one'},{'id':22,'path':'team/two'}])
    return m,target,write


def test_list_normalizes_without_any_migration_or_old_state_read(configured):
    m,path,write=configured
    config=m['mq_config'](path)
    assert m['mq_repositories'](config)==[{'id':11,'path':'team/one'},{'id':22,'path':'team/two'}]
    q=m['MonitorQueue'](config)
    try:
        a=q.enqueue(22,82,source_key='a',kind='code',head='a'*40,source={'origin':'automatic'},context={})
        b=q.enqueue(11,82,source_key='b',kind='code',head='a'*40,source={'origin':'automatic'},context={})
        assert q.reserve({11,22})['id']==a['id']
        q.finish(q.job(a['id']),'done')
        assert q.reserve({11,22})['id']==b['id']
        assert q.mr(11,82)['chats']==q.mr(22,82)['chats']=={}
    finally:q.close()
    assert not Path(config['state_file']).exists()


@pytest.mark.parametrize('entries',[[{'id':11,'path':'team/one'},{'id':11,'path':'team/two'}],
    [{'id':11,'path':'team/one'},{'id':22,'path':'team/one'}],[]])
def test_invalid_project_list_is_rejected_before_state_creation(configured,entries):
    m,path,write=configured;write(entries)
    with pytest.raises(RuntimeError):m['mq_config'](path)
    assert not (path.parent/'old').exists()


def test_removal_rejects_cached_producer_without_losing_issued_work(configured):
    m,path,write=configured;config=m['mq_config'](path);q=m['MonitorQueue'](config)
    try:
        issued=q.enqueue(22,82,source_key='old',kind='code',head='a'*40,source={'origin':'automatic'},context={})
        write([{'id':11,'path':'team/one'}])
        with pytest.raises(RuntimeError,match='no longer enabled'):
            q.enqueue(22,82,source_key='new',kind='code',head='b'*40,source={'origin':'automatic'},context={})
        assert len(q.jobs())==1 and q.job(issued['id'])['source']=={'origin':'automatic'}
        assert q.reserve({11}) is None
    finally:q.close()
