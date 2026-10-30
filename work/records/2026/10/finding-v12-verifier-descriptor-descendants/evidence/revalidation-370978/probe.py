"""Inert mechanism discrimination only: no engine/provider/product mutation."""
import ast,hashlib,json,os,pathlib,subprocess,sys,tempfile,time
R=pathlib.Path('/home/sl/src/baton');P=pathlib.Path(__file__).resolve().parent
raw=(R/'v12/worker/claude_agent.py').read_bytes();tree=ast.parse(raw)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ClaudeAgent')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_checked_directory');method.decorator_list=[]
class TaskRefusal(Exception):pass
ns={'os':os,'TaskRefusal':TaskRefusal};exec(compile(ast.Module(body=[method],type_ignores=[]),'<exact current _checked_directory>','exec'),ns)
started=time.monotonic();out={}
with tempfile.TemporaryDirectory(prefix='w325695-mechanism-') as temp:
 root=pathlib.Path(temp)/'root';root.mkdir(mode=0o700);child=root/'nested';child.mkdir(mode=0o700);leaf=child/'home';leaf.mkdir(mode=0o700)
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  self_alias=f'/proc/self/fd/{fd}';holder_alias=f'/proc/{os.getpid()}/fd/{fd}'
  check='import os,json;print(json.dumps({"exists":os.path.isdir(os.environ["TMPDIR"]),"resolved":os.path.realpath(os.environ["TMPDIR"])}))'
  # Parent -> child -> ordinary grandchild (no pass_fds for grandchild).
  launch='import subprocess,sys,os,json; r=subprocess.run([sys.executable,"-c",'+repr(check)+'],env=os.environ.copy(),capture_output=True,text=True,check=True);print(json.dumps({"immediate":os.path.isdir(os.environ["TMPDIR"]),"grandchild":json.loads(r.stdout)}))'
  for name,alias in [('self_fd',self_alias),('holder_fd',holder_alias)]:
   env={'PATH':'/usr/bin:/bin','TMPDIR':alias}
   r=subprocess.run([sys.executable,'-c',launch],env=env,pass_fds=(fd,),capture_output=True,text=True,timeout=10,check=True)
   out[name]=json.loads(r.stdout)
   try:ns['_checked_directory'](alias+'/nested',alias+'/nested/home');nested={'accepted':True}
   except TaskRefusal as e:nested={'accepted':False,'reason':str(e)}
   out[name]['exact_nested_adapter']=nested
  # Resolve once, then adversarial replacement after that resolution.
  ordinary=os.path.realpath(holder_alias);renamed=pathlib.Path(temp)/'held';root.rename(renamed)
  redirect=pathlib.Path(temp)/'candidate-surrogate';redirect.mkdir(mode=0o700);root.symlink_to(redirect,target_is_directory=True)
  (pathlib.Path(ordinary)/'plain-write').write_text('inert marker')
  (pathlib.Path(holder_alias)/'held-write').write_text('inert marker')
  out['replacement']={'resolved_path_redirects':(redirect/'plain-write').exists(),'holder_alias_stays_on_object':(renamed/'held-write').exists(),'holder_did_not_write_candidate':not (redirect/'held-write').exists()}
 finally:os.close(fd)
 out['holder_close']={'exists_after_close':os.path.exists(holder_alias)}
assert out['self_fd']['immediate'] and not out['self_fd']['grandchild']['exists']
assert out['holder_fd']['grandchild']['exists'] and not out['holder_fd']['exact_nested_adapter']['accepted']
assert all(out['replacement'].values()) and not out['holder_close']['exists_after_close']
result={'scope':'Inert OS operations and exact AST-extracted existing path validator; no product correction implemented','worker_sha256':hashlib.sha256(raw).hexdigest(),'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'observations':out,'seconds':time.monotonic()-started,'limits':'Rejects these specific incomplete compositions. Does not establish impossibility of every adapter-local solution; no engine namespace or credential isolation claim. All children awaited; temporary marker tree cleaned.'}
(P/'MECHANISM-CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
