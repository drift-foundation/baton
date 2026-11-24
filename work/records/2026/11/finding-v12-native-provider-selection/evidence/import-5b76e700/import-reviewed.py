from pathlib import Path
import hashlib,json,os,stat,subprocess,tarfile
ROOT=Path('/home/sl/src/baton')
D=ROOT/'work/records/2026/11/finding-v12-native-provider-selection'
P=D/'evidence/import-5b76e700'
C=D/'evidence/correction-prompt-r1a'
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((C/'candidate-manifest.json').read_text())
assert m['candidate']=='sha256:5b76e7000b38c77b8405b92215f5ed7d82aeb20dab62bd2ccc2fe23a13ed5b62'
assert 'sha256:'+sha(json.dumps({k:m[k] for k in ('base','files','context')},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==m['candidate']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==m['base']
assert sha((ROOT/'v12/DESIGN.md').read_bytes())==m['context']['DESIGN.md'],'DESIGN drift'
with tarfile.open(C/'candidate-files.tar.gz') as t:
 members=t.getmembers(); assert len(members)==len(m['files'])
 assert {x.name for x in members}=={x['path'] for x in m['files']}
 data={}
 for x in members:
  assert x.isfile() and not Path(x.name).is_absolute() and '..' not in Path(x.name).parts
  f=next(f for f in m['files'] if f['path']==x.name)
  b=t.extractfile(x).read();assert sha(b)==f['sha256'] and len(b)==f['bytes'] and oct(x.mode)==f['mode']
  data[x.name]=b
checks=[]
for name,b in data.items():
 path=ROOT/name
 for parent in path.parents:
  if parent==ROOT:break
  assert not parent.is_symlink(),str(parent)
  if parent.exists():assert parent.is_dir(),str(parent)
 base=subprocess.run(['git','cat-file','blob',m['base']+':'+name],cwd=ROOT,capture_output=True)
 if base.returncode==0:
  s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_mode&stat.S_IWUSR,name
  assert path.read_bytes()==base.stdout,'target drift '+name
  mode=stat.S_IMODE(s.st_mode)
 else:
  assert not os.path.lexists(path),'new target exists '+name
  mode=0o644
 checks.append({'path':name,'existing':base.returncode==0,'target_mode':oct(mode),'sha256':sha(b)})
(P/'preflight.json').write_text(json.dumps({'candidate':m['candidate'],'checked':checks,'refusals':0},indent=2)+'\n')
for f in checks:
 path=ROOT/f['path'];path.parent.mkdir(parents=True,exist_ok=True)
 if f['existing']:path.write_bytes(data[f['path']])
 else:
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
  with os.fdopen(fd,'wb') as out:out.write(data[f['path']])
 assert sha(path.read_bytes())==f['sha256'] and oct(stat.S_IMODE(path.stat().st_mode))==f['target_mode'],f['path']
(P/'postflight.json').write_text(json.dumps({'candidate':m['candidate'],'verified':checks,'exact_bytes':True,'existing_modes_preserved':True},indent=2)+'\n')
print('Imported 37 exact reviewed paths; existing modes preserved, new files 0644. No Git mutation.')
