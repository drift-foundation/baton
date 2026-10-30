"""For the separately selected non-provider engine proof ONLY."""
import ast,errno,json,os,pathlib,stat,subprocess,sys,tempfile,time
import hashlib
EXPECTED_IMAGE_FILES = {'/opt/baton/baton_worker.py': '56cdee824193834e9f1e8e974259575219a9223aa9b4f1946c99099b35c5cd34', '/opt/baton/claude_agent.py': 'cd7cee152af411e02043094ff0d6de838721209b08483960429480d9dfc90f0a', '/opt/baton/dogfood_entry.py': '8012e5d8581e43fbfbef245c60901501e588f1dbc8a0a57b9ca2cdcdae2369c2', '/opt/baton/worker-control-1.0.schema.json': '22caa60ae0aab610d93d9c676925b52c49a893352b2f8a72b03bee7a6a3301bc', '/opt/baton/verifier-layout-marker.json': '3355c11a36044111f713d37a729e51f8b781801d655be5e0df14de7fb69c9648', '/opt/baton/attempt_log_format.py': '304152a5760e0ecf1c4e5947df3a402f3f141e3ccf3ebc9306fd7fc8f749de1f', '/opt/baton/verification_context.py': 'f599072ac1202e9b759d9e7850f76c98790e23710cf6181d5a6e8907dd51650e', '/opt/baton/source_profiles/checkout.py': '037f197ad2cfc3dd9c373bcddf447adaa62160a74f7e5d1b4af0a783e73185c7', '/opt/baton/source_profiles/__init__.py': 'c16e597fa779e585cb33723d39ee648770cdd4c7b29e841cbcc2ce76ccaefdad'}
for path, expected in EXPECTED_IMAGE_FILES.items():
 assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() == expected, path
assert os.getuid() == PROOF_UID and os.getgid() == PROOF_GID
# Diagnostic selection uses the accepted topology and selected explicit UID/GID.
# It is not an installed manager-delivery receipt.
from claude_agent import ClaudeAgent
agent = ClaudeAgent.__new__(ClaudeAgent)
agent._seen = {}
marker = json.loads(pathlib.Path('/opt/baton/verifier-layout-marker.json').read_text())
selection = dict(schema=agent.LAYOUT_SCHEMA, layout_digest=marker['layout_digest'], roots=agent.LAYOUT_ROOTS,
                 filesystem=agent.LAYOUT_FILESYSTEM, options=list(agent.LAYOUT_OPTIONS), mode=agent.LAYOUT_MODE,
                 uid=PROOF_UID, gid=PROOF_GID, image_digest=PROOF_IMAGE,
                 profile_digest='sha256:'+'1'*64, policy_digest='sha256:'+'2'*64, adapter_digest='sha256:'+'3'*64)
selection_path='/tmp/kernel-diagnostic-selection.json'
pathlib.Path(selection_path).write_text(json.dumps(selection))
agent.LAYOUT_DOCUMENT=selection_path
assert agent._selected_layout() == selection
pinned, held_roots=agent._pinned_environment('/tmp', {'PATH':'/usr/local/bin:/usr/bin:/bin'})
agent._revalidated_directories(pinned, held_roots)

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
# Real bounded allocation, one private root at a time. Never grow or fall back.
capacity={"HOME":4194304,"TMPDIR":16777216,"XDG_CACHE_HOME":4194304,"PYTHONPYCACHEPREFIX":8388608}
capacity_result={}
for key, bound in capacity.items():
 root=roots[key];v=os.statvfs(root);assert v.f_blocks*v.f_frsize <= bound
 target=pathlib.Path(root)/'capacity-probe'
 written=0;failed=False
 try:
  with target.open('wb',buffering=0) as stream:
   while written <= bound+1048576:
    try:
     count=stream.write(b'x'*65536)
     if not count:raise AssertionError('zero write without ENOSPC')
     written+=count
    except OSError as err:
     assert err.errno==errno.ENOSPC;failed=True;break
  assert failed and written <= bound
  capacity_result[key]={'bytes_written':written,'errno':'ENOSPC','configured_bytes':bound}
 finally:
  target.unlink(missing_ok=True)
agent._revalidated_directories(pinned,held_roots)
for _name, fd in held_roots:os.close(fd)

# Detached verifier-like descendant remains until exact container teardown.
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)'],env=env,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'image_bytes':'passed','product_mount_checks':'passed','capacity_enospc':'passed','capacity':capacity_result,'mount_binding':'passed','ordinary_grandchild':'passed','nested_validator':'passed','descendant_started':p.pid,'cleanup':'not-yet-observed'}),flush=True)
time.sleep(120)
