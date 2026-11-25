"""Preparation simulation of Docker for the Q4 checks. NOT an engine; synthetic evidence only.

Several containers, keyed by name. A running container whose manager has written a command
is served once by the simulated worker for its image (sim.py). Scenario words are read from
the state file's `scenario` member.
"""
import hashlib,json,sys
from pathlib import Path
CODEX='sha256:'+'e'*64;CLAUDE='sha256:'+'c'*64
def cid(name):return hashlib.sha256(name.encode()).hexdigest()
class Fake:
    def __init__(self,state_path,packet,root):
        self.path=Path(state_path);self.packet=Path(packet);self.root=Path(root)
        self.st=json.loads(self.path.read_text()) if self.path.exists() else {}
        for key,value in (('containers',{}),('log',[]),('acted',[]),('scenario','accepted'),('removed',[])):self.st.setdefault(key,value)
    def labels(self,image):
        return dict(self.st.get('image_labels',{}).get(image,{}))
    def serve_workers(self):
        for name,c in list(self.st['containers'].items()):
            if not c['running'] or name in self.st['acted'] or self.st['scenario']=='stall':continue
            mounts={m['Destination']:m['Source'] for m in c['mounts']}
            command=mounts.get('/run/baton/exchange/command')
            if not command or not list(Path(command).glob('*.json')):continue
            self.st['acted'].append(name);self.save()
            import sim
            sim.run(self.root,mounts,json.loads(Path(mounts['/run/baton/launch.json']).read_text()),c.get('tmpfs',[]),role='implementation' if c['image']==CODEX else 'review',scenario=self.st['scenario'],packet=self.packet)
    def save(self):self.path.write_text(json.dumps(self.st))
    def __call__(self,argv):
        argv=list(argv);self.st['log'].append(argv);out='';err='';code=0;S=self.st;scenario=S['scenario']
        def val(flag):return argv[argv.index(flag)+1]
        self.serve_workers()
        op=argv[0];C=S['containers']
        def find(target):
            for name,c in C.items():
                if target in (name,cid(name)):return name,c
            return None,None
        if op=='version':out=json.dumps({'Client':{'Version':'fake-client'},'Server':{'Version':'fake-server'}})
        elif op=='build':
            if scenario=='build-fail':err='simulated build failure';code=1
            else:
                Path(val('--iidfile')).write_text(CLAUDE)
                S.setdefault('image_labels',{})[CLAUDE]=dict(x.split('=',1) for i,a in enumerate(argv) if a=='--label' for x in [argv[i+1]])
        elif op=='image':
            image=argv[-1]
            if image not in (CODEX,CLAUDE) or (image==CLAUDE and CLAUDE not in S.get('image_labels',{})):err='Error response from daemon: No such image: '+image;code=1
            else:out=json.dumps([{'Id':image,'Os':'linux','Architecture':'amd64','Config':{'User':'65532:65532' if image==CLAUDE else '','Entrypoint':['python3','/opt/baton/dogfood_entry.py' if image==CLAUDE else '/opt/baton/codex_entry.py'],'Labels':S.get('image_labels',{}).get(image,S.get('codex_labels',{}))}}])
        elif op=='run' and '--rm' in argv:
            # Offline inventory of the built image: no mounts, network none.
            assert val('--network')=='none' and '--mount' not in argv and '-v' not in argv,argv
            entry=val('--entrypoint');tail=argv[argv.index(CLAUDE)+1:]
            if entry=='claude' and tail==['--version']:out=('2.1.240' if scenario=='wrong-version' else '2.1.247')+' (Claude Code)\n'
            elif entry=='claude' and tail==['--help']:out='Usage: claude [options]\n  -p, --print\n  --output-format <format>\n  --model <model>\n  --dangerously-skip-permissions\n'
            elif entry=='python3':
                import sim
                out=json.dumps(sim.image_files(self.root,tamper=scenario=='image-drift'))
            else:err='unexpected inventory '+repr(argv);code=97
        elif op in ('run','create'):
            if scenario=='launch-fail':err='simulated launch refusal';code=1
            else:
                name=val('--name');assert name not in C
                labels={};mounts=[]
                for i,a in enumerate(argv):
                    if a=='--label':k,v=argv[i+1].split('=',1);labels[k]=v
                    if a=='--mount':
                        p=dict(x.split('=',1) for x in argv[i+1].split(','));mounts.append(dict(Type='bind',Source=p['source'],Destination=p['target'],RW=p['readonly']=='false'))
                C[name]=dict(labels=labels,mounts=mounts,tmpfs=[argv[i+1] for i,a in enumerate(argv) if a=='--tmpfs'],user=val('--user'),net=val('--network'),ro='--read-only' in argv,image=argv[-1],running=(op=='run'),exit=0)
                out=cid(name)+'\n'
        elif op=='start':
            name,c=find(argv[-1]);c['running']=True;out=cid(name)+'\n'
        elif op=='ps':
            rows=[]
            wanted=[argv[i+1] for i,a in enumerate(argv) if a=='--filter']
            for name,c in C.items():
                merged={**self.labels(c['image']),**c['labels']};keep=True
                for f in wanted:
                    kind,_,expr=f.partition('=')
                    if kind=='name':keep=keep and expr.strip('^$/')==name
                    if kind=='label':
                        k,_,v=expr.partition('=');keep=keep and merged.get(k)==v
                if not keep:continue
                fmt=val('--format') if '--format' in argv else '{{.ID}}'
                rows.append(name if fmt=='{{.Names}}' else cid(name) if fmt=='{{.ID}}' else json.dumps(dict(ID=cid(name),Image=c['image'],Names=name,Labels=','.join(f'{k}={v}' for k,v in merged.items()))))
            out=''.join(r+'\n' for r in rows)
        elif op=='inspect':
            name,c=find(argv[-1])
            if c is None:err='Error response from daemon: No such container: '+argv[-1];code=1
            else:
                doc=dict(Id=cid(name),Image=c['image'],Name='/'+name,Path='python3',Args=['/opt/baton/entry.py'],Config=dict(Labels={**self.labels(c['image']),**c['labels']},User=c['user']),State=dict(Running=c['running'],StartedAt='2026-11-25T07:00:00.123456789Z',ExitCode=c['exit']),HostConfig=dict(NetworkMode=c['net'],ReadonlyRootfs=c['ro']),Mounts=c['mounts'])
                out=json.dumps(doc if '--format' in argv else [doc])
        elif op=='stop':
            name,c=find(argv[-1])
            if c is None:err='Error response from daemon: No such container: '+argv[-1];code=1
            else:c['running']=False;c['exit']=143
        elif op=='rm':
            name,c=find(argv[-1])
            if c is None:err='Error response from daemon: No such container: '+argv[-1];code=1
            elif scenario=='remove-fail':err='simulated removal failure';code=1
            else:del C[name];S['removed'].append(name)
        else:err='unexpected '+repr(argv);code=97
        self.save()
        return code,out,err
if __name__=='__main__':
    state,packet,root=sys.argv[1:4];sys.path.insert(0,packet)
    code,out,err=Fake(state,packet,root)(sys.argv[4:])
    sys.stdout.write(out);sys.stderr.write(err);sys.exit(code)
