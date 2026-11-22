import hashlib,json,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/sl/src/baton')
e=root/'work/records/2026/11/finding-v12-retained-recovery-admission/evidence'
src=e/'output-limit-recovery-20261122'; out=e/'recovery-assessment-385690'
scratch=root/'work/scratch/w385624-recovery-385690'; scratch.mkdir(exist_ok=False)
start=time.monotonic()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
manifest=json.loads((src/'manifest.json').read_text())
for p,h in manifest.items():assert sha(src/p)==h,p
repo=scratch/'objects.git'
log=(out/'git-reconstruction.log').open('w')
def git(*args):
 p=subprocess.run(['git',*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
 log.write(p.stdout.decode());log.flush();return p.stdout
base='ce6e1b2bf12519a84a3792f06562b7727dfe3021'; head='5bc260b6dcbe970c8729424fa826b88dbc1a9d0f'
git('init','--bare',repo)
git('-C',repo,'fetch','--depth=1',root.as_uri(),base)
git('-C',repo,'bundle','verify',src/'proposal/objects.bundle')
git('-C',repo,'fetch',src/'proposal/objects.bundle','HEAD')
assert git('-C',repo,'rev-parse','FETCH_HEAD').decode().strip()==head
assert git('-C',repo,'rev-parse',head+'^').decode().strip()==base
paths=git('-C',repo,'diff','--name-only',base,head).decode().splitlines()
assert paths==json.loads((src/'proposal/result.json').read_text())['changed_paths']
def tar_inventory(stream, mode):
 d={}
 with tarfile.open(fileobj=stream,mode=mode) as t:
  for m in t:
   if m.isdir():continue
   assert not m.name.startswith('/') and '..' not in pathlib.PurePosixPath(m.name).parts
   assert m.name not in d
   if m.isfile(): h=hashlib.sha256(t.extractfile(m).read()).hexdigest()
   elif m.issym():h=m.linkname
   else:raise ValueError(m.name)
   d[m.name]=[m.type.decode(),m.mode,m.size,h]
 return d
with (src/'candidate.tar').open('rb') as f: retained=tar_inventory(f,'r|')
p=subprocess.Popen(['git','-C',str(repo),'archive',head],stdout=subprocess.PIPE)
actual=tar_inventory(p.stdout,'r|');assert p.wait()==0
assert retained==actual, sorted(set(retained)^set(actual))[:10]
with (out/'candidate-tree.json').open('w') as f:json.dump(actual,f,sort_keys=True,indent=2);f.write('\n')
# Extract validated archive only into confined scratch for subsequent review.
checkout=scratch/'candidate';checkout.mkdir()
with tarfile.open(src/'candidate.tar') as t:t.extractall(checkout,filter='data')
result={'candidate':head,'base':base,'manifest_files_verified':len(manifest),'tree_entries_verified':len(actual),'changed_paths':paths,'candidate_tree_manifest_sha256':sha(out/'candidate-tree.json'),'scratch':str(scratch),'elapsed_seconds':round(time.monotonic()-start,3),'tests_run':0,'main_git_mutations':False}
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
