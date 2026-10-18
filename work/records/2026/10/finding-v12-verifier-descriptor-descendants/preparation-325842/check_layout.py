"""Reference proposal composition; does not implement or exercise product correction."""
import copy,json,pathlib,time
P=pathlib.Path(__file__).resolve().parent;d=json.loads((P/'LAYOUT.json').read_text());t=time.monotonic()
def compose(v,uid,gid,compatible=True):
 if not compatible:raise ValueError('image/layout mismatch')
 if type(uid) is not int or uid<=0 or type(gid) is not int or gid<=0:raise ValueError('identity')
 if v['parent']!='/run/baton-verifier' or v['parent_writable'] or v['root_mode']!='0700':raise ValueError('parent/mode')
 names={'HOME':'home','TMPDIR':'tmp','XDG_CACHE_HOME':'cache','PYTHONPYCACHEPREFIX':'pycache'}
 if set(v['roots'])!=set(names):raise ValueError('root set')
 roots=[]
 for name,leaf in names.items():
  r=v['roots'][name]
  if r['target']!=v['parent']+'/'+leaf or type(r['bytes']) is not int or r['bytes']<=0:raise ValueError('target/size')
  roots.append(r)
 total=v['tmp_bytes']+v['shm_bytes']+sum(r['bytes'] for r in roots)
 if total!=80*1024**2 or total!=v['scratch_total_bytes'] or v['workspace_min_bytes']<=total:raise ValueError('scratch/floor')
 if total+v['legacy_decoy_bytes']!=v['all_tmpfs_total_bytes'] or v['all_tmpfs_total_bytes']>=v['memory_limit_bytes']:raise ValueError('memory')
 return [r['target']+':rw,noexec,nosuid,nodev,size='+str(r['bytes'])+',mode=0700,uid='+str(uid)+',gid='+str(gid) for r in roots]
positive=compose(d,1000,1000);cases=[]
for name,edit in [('writable-parent',lambda v:v.update(parent_writable=True)),('wrong-mode',lambda v:v.update(root_mode='0777')),('escaping-target',lambda v:v['roots']['HOME'].update(target='/tmp/home')),('duplicate-target',lambda v:v['roots']['HOME'].update(target=v['roots']['TMPDIR']['target'])),('growth-unaccounted',lambda v:v['roots']['HOME'].update(bytes=8*1024**2)),('floor-too-small',lambda v:v.update(workspace_min_bytes=80*1024**2)),('decoy-omitted',lambda v:v.update(all_tmpfs_total_bytes=80*1024**2))]:
 v=copy.deepcopy(d);edit(v)
 try:compose(v,1000,1000);raise AssertionError(name)
 except ValueError as e:cases.append({'case':name,'refused':str(e)})
for name,uid,gid,compatible in [('root-uid',0,1000,True),('invalid-gid',1000,False,True),('old-image',1000,1000,False)]:
 try:compose(d,uid,gid,compatible);raise AssertionError(name)
 except ValueError as e:cases.append({'case':name,'refused':str(e)})
out={'kind':'reference design arithmetic/composition/refusal, not product or kernel proof','positive':positive,'negative':cases,'scratch_bytes':d['scratch_total_bytes'],'including_decoy_bytes':d['all_tmpfs_total_bytes'],'seconds':time.monotonic()-t}
(P/'LAYOUT-CHECK.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
