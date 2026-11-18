#!/usr/bin/python3
import json,os,subprocess,sys,uuid
from pathlib import Path
args=sys.argv[1:];cidfile=None
engine=os.environ.get('W384944_REAL_DOCKER','/usr/bin/docker')
if args and args[0]=='exec':
 with open(os.environ['ENGINE_LOG'],'a') as f:f.write(json.dumps({'command':'exec','streaming_passthrough':True})+'\n')
 os.execv(engine,[engine,*args])
if args and args[0] in ['build','pull']:
 with open(os.environ['ENGINE_LOG'],'a') as f:f.write(json.dumps({'forbidden_command':args})+'\n')
 sys.exit(125)
if args and args[0]=='run':
 cidfile=Path(os.environ['TMPDIR'])/('cid-'+uuid.uuid4().hex)
 args[1:1]=['--pull=never','--label',os.environ['TASK_LABEL'],'--cidfile',str(cidfile)]
r=subprocess.run([engine,*args],capture_output=True)
record={'command':args[0] if args else '', 'status':r.returncode}
if cidfile and cidfile.exists():
 cid=cidfile.read_text().strip();record['id']=cid;cidfile.unlink()
 info=subprocess.run([engine,'inspect',cid],capture_output=True)
 if info.returncode==0:
  d=json.loads(info.stdout)[0];record['inspect']={k:d[k] for k in ['Id','Image','State','Mounts']};record['labels']=d['Config']['Labels']
if args and args[0] in ['run','logs','wait','rm']:record.update(stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'))
with open(os.environ['ENGINE_LOG'],'a') as f:f.write(json.dumps(record)+'\n')
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)
