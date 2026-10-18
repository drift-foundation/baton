"""For the separately selected non-provider engine proof ONLY."""
import ast,errno,json,os,pathlib,stat,subprocess,sys,tempfile,time
roots={name:'/run/baton-verifier/'+leaf for name,leaf in [('HOME','home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('PYTHONPYCACHEPREFIX','pycache')]}
parent=pathlib.Path('/run/baton-verifier');s=parent.stat();assert s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o755 and not os.access(parent,os.W_OK)
for name,root in roots.items():
 s=os.lstat(root);assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
 assert os.path.realpath(root)==root
 assert os.path.ismount(root)
 before=(s.st_dev,s.st_ino)
 for op in ('rename','remove'):
  try:
   if op=='rename':os.rename(root,root+'-replaced')
   else:os.rmdir(root)
  except OSError as e:assert e.errno in (errno.EBUSY,errno.EROFS,errno.EACCES,errno.EPERM)
  else:raise AssertionError('mount root replaced')
 try:os.symlink('/tmp',root)
 except FileExistsError:pass
 else:raise AssertionError('mount replaced by link')
 assert (os.stat(root).st_dev,os.stat(root).st_ino)==before
# Ordinary children/grandchildren, default close_fds, with a closed private env.
env={'PATH':'/usr/local/bin:/usr/bin:/bin',**roots}
leaf="import os,pathlib; [pathlib.Path(os.environ[k],'child-marker').write_text('inert') for k in ['HOME','TMPDIR','XDG_CACHE_HOME','PYTHONPYCACHEPREFIX']]"
child='import subprocess,sys;subprocess.run([sys.executable,"-c",'+repr(leaf)+'],check=True)'
subprocess.run([sys.executable,'-c',child],env=env,check=True,timeout=10)
raw=pathlib.Path('/opt/baton/claude_agent.py').read_bytes();tree=ast.parse(raw);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ClaudeAgent');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_checked_directory');fn.decorator_list=[]
class TaskRefusal(Exception):pass
ns={'os':os,'TaskRefusal':TaskRefusal};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<candidate validator>','exec'),ns)
with tempfile.TemporaryDirectory(dir=roots['TMPDIR']) as scratch:
 home=pathlib.Path(scratch)/'home';home.mkdir(mode=0o700);assert ns['_checked_directory'](scratch,str(home))==str(home)
# Detached verifier-like descendant remains until exact container teardown.
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)'],env=env,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'mount_binding':'passed','ordinary_grandchild':'passed','nested_validator':'passed','descendant_started':p.pid,'cleanup':'not-yet-observed'}),flush=True)
time.sleep(120)
