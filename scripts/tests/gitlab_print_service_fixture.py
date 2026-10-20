"""External systemd/CLI wire fixture; queue, dispatch, collection and publication remain real."""
import hashlib
import json
from pathlib import Path
import uuid


class PrintService:
    def __init__(self, config, claude):
        self.config=config;self.claude=claude;self.units={};self.commands=[];self.populated=False
        self.identity={'boot':'fixture-boot','manager':'123','root':'/user.slice/user-1000.slice/user@1000.service'}

    def command(self, config, arguments):
        self.commands.append(arguments[:])
        if arguments[:3]==['systemctl','--user','show']:
            if arguments[3].startswith('--property='):
                return 'ControlGroup='+self.identity['root']+'\nUserspaceTimestampMonotonic='+self.identity['manager']+'\n'
            state=self.units.get(arguments[3],{'LoadState':'not-found','ActiveState':'inactive','SubState':'dead','InvocationID':''})
            return ''.join(k+'='+str(v)+'\n' for k,v in state.items())
        if arguments[:3]==['systemctl','--user','stop']:
            state=self.units[arguments[-1]]
            state.update(ActiveState='failed',SubState='failed',Result='timeout')
            self.populated=False
            return ''
        assert arguments[0]=='systemd-run',arguments
        unit=next(a.split('=',1)[1] for a in arguments if a.startswith('--unit='))
        assert unit not in self.units,'duplicate service launch'
        start=arguments.index('--')+1
        args=arguments[start+1:]
        assert args[0]=='--print' and '--remote-control' not in args and '--bg' not in args
        self.claude(config,args)
        session=args[args.index('--session-id')+1]
        roots=list((Path(config['claude_home'])/'projects').glob('*/'+session+'.jsonl'))
        assert len(roots)==1
        records=[json.loads(l) for l in roots[0].read_text().splitlines()]
        assistant=next(r for r in records if r['type']=='assistant')
        text=assistant['message']['content'][0]['text']
        output=next(a.split('append:',1)[1] for a in arguments if a.startswith('--property=StandardOutput='))
        directory=Path(output).parent;manifest_path=directory/'manifest.json'
        manifest=json.loads(manifest_path.read_text())
        envelope={'type':'result','session_id':session,'is_error':bool(assistant['isApiErrorMessage']),
                  'subtype':'error_during_execution' if assistant['isApiErrorMessage'] else 'success','result':text}
        stream=[{'type':'assistant','session_id':session,'uuid':assistant['uuid'],
                 'parent_tool_use_id':None,'message':assistant['message']},envelope]
        Path(output).write_text(''.join(json.dumps(e)+'\n' for e in stream))
        invocation=uuid.uuid4().hex
        receipt={'manifest_digest':hashlib.sha256(json.dumps(manifest_path.read_text(),ensure_ascii=False).encode()).hexdigest(),
                 'invocation':invocation,'identity':self.identity.copy(),'cgroup':manifest['cgroup'],
                 'result':'success','exit_code':'exited','exit_status':'0'}
        for name in ('stdout','stderr'):receipt[name+'_digest']=hashlib.sha256((directory/name).read_bytes()).hexdigest()
        target=directory/'receipt.json';target.write_text(json.dumps(receipt));target.chmod(0o600)
        self.units[unit]={'LoadState':'loaded','ActiveState':'inactive','SubState':'dead',
            'InvocationID':invocation,'ControlGroup':'','Result':'success','ExecMainCode':'1','ExecMainStatus':'0'}
        return ''
