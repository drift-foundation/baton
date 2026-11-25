import hashlib,json,sys,tarfile,os,stat
from pathlib import Path
S=Path(sys.argv[1]);E=Path(sys.argv[2]);P=E/'readiness-386214'
sha=lambda b:hashlib.sha256(b).hexdigest()
out={}
m=json.loads((P/'packet-manifest.json').read_text())
out['packet_manifest_sha256']=sha((P/'packet-manifest.json').read_bytes())
out['packet_manifest_mismatches']=[f for f,d in m.items() if sha((P/f).read_bytes())!=d]
disk=sorted(str(p.relative_to(P)) for p in P.rglob('*') if p.is_file())
out['on_disk_not_in_manifest']=[f for f in disk if f not in m]
VEC='work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
mine={}
repo=S/'repo'
for p in sorted((repo/'v12').rglob('*')):
    if p.is_file() and not p.is_symlink(): mine[str(p.relative_to(repo))]=dict(sha256=sha(p.read_bytes()),mode=0o755 if p.stat().st_mode&0o111 else 0o644)
mine[VEC]=dict(sha256=sha((repo/VEC).read_bytes()),mode=0o644)
exp=json.loads((P/'expected-source.json').read_text())
out['expected_source_files']=len(exp);out['mine_files']=len(mine)
out['expected_vs_mine']=dict(only_expected=sorted(set(exp)-set(mine))[:10],only_mine=sorted(set(mine)-set(exp))[:10],differ=[k for k in exp if k in mine and exp[k]!=mine[k]][:10])
symlinks=[str(p.relative_to(repo)) for p in (repo/'v12').rglob('*') if p.is_symlink()];out['symlinks_in_v12']=symlinks
for sub in ('q1','q2'):
    seen={}
    with tarfile.open(P/sub/'source.tar') as t:
        for i in t:
            if i.isfile(): seen[i.name]=dict(sha256=sha(t.extractfile(i).read()),mode=0o755 if i.mode&0o111 else 0o644)
            elif not i.isdir(): seen[i.name]='NONFILE'
    out[sub+'_source_tar_equals_expected']=seen==exp
    out[sub+'_source_files_json_equals_expected']=(P/sub/'source-files.json').read_bytes()==(P/'expected-source.json').read_bytes()
# candidate manifest vs archive
cm=json.loads((E/'uncertainty-386214/candidate-manifest.json').read_text())
files=cm['files'];out['candidate_manifest_keys']=list(cm);out['candidate_files']=len(files)
bad=[];cand=S/'cand'
items=files.items() if isinstance(files,dict) else [(f['path'],f) for f in files]
for path,d in items:
    h=d if isinstance(d,str) else d.get('sha256')
    p=cand/path
    if not p.is_file() or sha(p.read_bytes())!=h: bad.append(path)
out['candidate_manifest_mismatches']=bad[:10]
out['archive_files_not_in_manifest']=sorted(set(str(p.relative_to(cand)) for p in cand.rglob('*') if p.is_file())-set(dict(items)))[:10]
out['product_paths']=cm['product_paths']
# archive copies of evidence equal disk
diff=[]
for path,_ in items:
    d=Path('/home/sl/src/baton')/path
    if not d.is_file() or d.read_bytes()!=(cand/path).read_bytes(): diff.append(path)
out['archive_vs_shared_tree_differences']=diff[:20];out['archive_vs_shared_tree_difference_count']=len(diff)
print(json.dumps(out,indent=1))
