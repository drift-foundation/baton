"""No call without separate selection. One digest-pinned no-provider engine object."""
import argparse,hashlib,json,os,pathlib,re,subprocess,time
P=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--image',required=True);parser.add_argument('--execute-reviewed',action='store_true');a=parser.parse_args()
if not a.execute_reviewed or not re.fullmatch(r'sha256:[0-9a-f]{64}',a.image):parser.error('requires separately reviewed exact image digest and execution selection')
uid,gid=os.getuid(),os.getgid()
if uid==0 or gid==0:raise RuntimeError('nonroot trusted identity required')
layout=json.loads((P/'LAYOUT.json').read_text());payload=(P/'kernel-payload.py').read_text();started=time.monotonic();cid=None;record={'image':a.image,'payload_sha256':hashlib.sha256(payload.encode()).hexdigest(),'provider_invoked':False}
def run(args,timeout=10):return subprocess.run(['docker',*args],capture_output=True,text=True,timeout=timeout)
name='w325695-proof-325842'
if (P/'ENGINE-RESULT.json').exists():raise RuntimeError('proof already has a receipt; no retry')
prior=run(['inspect',name])
if prior.returncode==0 or 'No such' not in prior.stderr:raise RuntimeError('proof destination not proven absent')
try:
 argv=['create','--name',name,'--label','baton.proof=w325695-325842','--pull','never','--read-only','--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--user',f'{uid}:{gid}','--pids-limit','64','--memory','2g','--cpus','1','--entrypoint','/usr/bin/python3']
 for target,size in [('/tmp',layout['tmp_bytes']),('/dev/shm',layout['shm_bytes']),*[(v['target'],v['bytes']) for v in layout['roots'].values()]]:
  mode='0700' if target.startswith('/run/baton-verifier/') else '1777'
  argv+=['--tmpfs',f'{target}:rw,noexec,nosuid,nodev,size={size},mode={mode},uid={uid},gid={gid}']
 argv+=[a.image,'-c',payload];r=run(argv);assert r.returncode==0,r.stderr;cid=r.stdout.strip();assert re.fullmatch('[0-9a-f]{64}',cid)
 record['container_id']=cid;r=run(['start',cid]);assert r.returncode==0,r.stderr
 # Bounded poll of only this selected object for structural receipt, <=20s.
 for _ in range(40):
  r=run(['logs',cid]);lines=r.stdout.splitlines()
  if lines:
   record['payload']=json.loads(lines[0]);break
  time.sleep(.5)
 else:raise RuntimeError('no complete structural proof receipt within20s')
 assert record['payload']['mount_binding']=='passed'
 r=run(['inspect',cid]);assert r.returncode==0
 info=json.loads(r.stdout)[0];assert info['Id']==cid and info['Image']==a.image and info['State']['Running']
 record['before_cleanup_running']=True
finally:
 if cid is None:
  found=run(['inspect',name])
  if found.returncode==0:
   obj=json.loads(found.stdout)[0]
   if obj['Image']==a.image and obj['Config']['Labels'].get('baton.proof')=='w325695-325842':
    cid=obj['Id'];record['container_id']=cid;record['reconciled_create']=True
   else:record['uncertainty']='name occupied by unmatched object; no cleanup authority'
  elif 'No such' not in found.stderr:record['uncertainty']='creation outcome cannot be inspected'
 if cid:
  stopped=run(['rm','--force',cid],timeout=30);record['cleanup_status']=stopped.returncode
  absent=run(['inspect',cid]);record['exact_absence']=absent.returncode!=0 and 'No such' in absent.stderr
 record['seconds']=time.monotonic()-started
 (P/'ENGINE-RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
if not record.get('exact_absence') or record.get('cleanup_status')!=0:raise RuntimeError('exact runtime cessation unconfirmed; retain identity and escalate cleanup')
