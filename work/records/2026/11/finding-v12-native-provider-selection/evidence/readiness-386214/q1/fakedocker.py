"""Preparation simulation of a docker client. NOT an engine; labelled synthetic fake."""
import json,sys
from pathlib import Path
state_path=Path(sys.argv[1]);scenario=sys.argv[2];argv=sys.argv[3:]
P=Path(__file__).resolve().parent
st=json.loads(state_path.read_text()) if state_path.exists() else {'c':None,'log':[]}
st['log'].append(argv)
IMG='sha256:'+'c'*64;CID='d'*64
ident=json.loads((P/'q1-build.json').read_text())
ILAB={'org.opencontainers.image.revision':ident['source_commit'],'io.baton.q1.source':ident['source_manifest_sha256'],'io.baton.q1.packet':'q1-386214'}
out='';err='';code=0
def val(flag):return argv[argv.index(flag)+1]
c=st['c'];op=argv[0]
if op=='version':out=json.dumps({'Client':{'Version':'fake-client'},'Server':{'Version':'fake-server'}})
elif op=='build':
    if scenario=='build-fail':err='simulated build failure';code=1
    else:Path(val('--iidfile')).write_text(IMG)
elif op=='image':out=json.dumps([{'Id':IMG,'Os':'linux','Architecture':'amd64','Config':{'Entrypoint':['python3','/opt/baton/codex_entry.py'],'Labels':ILAB}}])
elif op=='run':
    assert c is None
    labels={};mounts=[]
    for i,a in enumerate(argv):
        if a=='--label':k,v=argv[i+1].split('=',1);labels[k]=v
        if a=='--mount':
            p=dict(x.split('=',1) for x in argv[i+1].split(','));mounts.append(dict(Type='bind',Source=p['source'],Destination=p['target'],RW=p['readonly']=='false'))
    st['c']=dict(name=val('--name'),labels=labels,mounts=mounts,user=val('--user'),net=val('--network'),ro='--read-only' in argv,image=argv[-1],running=True,exit=0)
    out=CID+'\n'
elif op=='ps':
    if c:
        fmt=val('--format')
        if fmt=='{{.Names}}':out=c['name']+'\n'
        elif fmt=='{{.ID}}':out=CID+'\n'
        else:out=json.dumps(dict(ID=CID,Image=c['image'],Names=c['name'],Labels=','.join(f'{k}={v}' for k,v in {**ILAB,**c['labels']}.items())))+'\n'
elif op=='inspect':
    target=argv[-1]
    if c is None or target not in (CID,c['name']):err='Error response from daemon: No such container: '+target;code=1
    else:
        doc=dict(Id=CID,Image=c['image'],Name='/'+c['name'],Path='python3',Args=['/opt/baton/codex_entry.py'],Config=dict(Labels={**ILAB,**c['labels']},User=c['user']),State=dict(Running=c['running'],StartedAt='2026-11-25T07:00:00.123456789Z',ExitCode=c['exit']),HostConfig=dict(NetworkMode=c['net'],ReadonlyRootfs=c['ro']),Mounts=c['mounts'])
        out=json.dumps(doc if '--format' in argv else [doc])
elif op=='exec':
    if scenario=='probe-fail':err='simulated probe failure';code=1
    else:out=json.dumps(dict(identity=ident,simulated=True))
elif op=='stop':c['running']=False;c['exit']=143
elif op=='rm':
    if scenario=='remove-fail':err='simulated removal failure';code=1
    else:st['c']=None
else:err='unexpected '+repr(argv);code=97
state_path.write_text(json.dumps(st))
sys.stdout.write(out);sys.stderr.write(err);sys.exit(code)
