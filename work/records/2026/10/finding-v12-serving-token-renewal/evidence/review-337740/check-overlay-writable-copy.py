"""Disposable byte-copy and refusal checks; no Job, Git mutation or engine."""
import hashlib,json,pathlib,subprocess,sys,tempfile,time,shutil
p=pathlib.Path('/home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/continuation-337717')
spec=json.loads((p/'PARTIAL-INPUT.json').read_text()); root=pathlib.Path(tempfile.mkdtemp(prefix='w333485-overlay-'));rows=[]
def digest(b):return hashlib.sha256(b).hexdigest()
def fresh(name):
 d=root/name;d.mkdir()
 for path,info in spec['paths'].items():
  if info['base_sha256'] is not None:
   b=subprocess.check_output(['git','show',spec['base']+':'+path],cwd='/home/sl/src/baton');assert digest(b)==info['base_sha256'];f=d/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
 return d
def snapshot(d):return {str(f.relative_to(d)):digest(f.read_bytes()) for f in d.rglob('*') if f.is_file()}
def run(label,loader,d,success):
 before=snapshot(d);t=time.monotonic();r=subprocess.run([sys.executable,'-B',str(loader),str(d)],capture_output=True,text=True,timeout=15);elapsed=time.monotonic()-t
 assert (r.returncode==0)==success,(label,r.stderr)
 if not success:assert snapshot(d)==before
 rows.append(dict(label=label,seconds=elapsed,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
a=fresh('positive');run('exact-copy',p/'restore.py',a,True)
for path,info in spec['paths'].items():assert digest((a/path).read_bytes())==info['restored_sha256']
run('reuse-refused',p/'restore.py',a,False)
b=fresh('bad-base');f=b/next(iter(spec['paths']));f.write_bytes(b'drift');run('base-refused',p/'restore.py',b,False)
c=fresh('bad-buffer-target');copy=root/'bad-input';shutil.copytree(p/'candidate-input',copy/'candidate-input',copy_function=shutil.copyfile);shutil.copyfile(p/'restore.py',copy/'restore.py');f=copy/'candidate-input'/list(spec['paths'])[-1];f.write_bytes(b'drift');run('buffer-refused-before-any-write',copy/'restore.py',c,False)
d=fresh('symlink-target');f=d/next(iter(spec['paths']));f.unlink();f.symlink_to(b/next(iter(spec['paths'])));run('symlink-refused',p/'restore.py',d,False)
print(json.dumps(dict(root=str(root),checks=rows,total_seconds=sum(r['seconds'] for r in rows)),indent=2))
