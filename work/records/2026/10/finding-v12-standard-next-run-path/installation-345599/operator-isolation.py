import os,json,sys,errno
from pathlib import Path
assert os.geteuid()==0
root=Path('/opt/baton-next-run')
config=json.loads((root/'installation.json').read_text())
record=json.loads((root/'state/w339626-live-345599.allocation.json').read_text())
assert record['uid']!=1000 and record['uid']!=0
other=next(a for a in config['accounts'] if a['uid']!=record['uid'])
assert record['groups']==[1000,119]
child=os.fork()
if child==0:
 try:
  os.setgroups(record['groups']);os.setgid(record['gid']);os.setuid(record['uid']);os.umask(0o077)
  sys.path[:0]=['/opt/baton-next-run/code/src','/opt/baton-next-run/code']
  from tools.next_run_confinement import restrict_writes
  restrict_writes(record['storage'])
  # Opening without O_TRUNC/O_CREAT performs no write. Success is a failed boundary check.
  for path,flags in [('/opt/baton-next-run/entry.py',os.O_WRONLY),('/home/sl/src/baton/v12/NEXT-RUN.md',os.O_WRONLY),('/home/sl/.claude/.credentials.json',os.O_RDONLY),(other['credentials'],os.O_RDONLY)]:
   try: fd=os.open(path,flags|os.O_NOFOLLOW)
   except PermissionError: continue
   else: os.close(fd);raise RuntimeError('isolation refusal missing for '+path)
  print(json.dumps({'state':'negative-access-checks-pass','uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),'credential_contents_read':False,'bytes_written':0}),flush=True)
  os._exit(0)
 except BaseException as e:
  print(type(e).__name__+': '+str(e),file=sys.stderr,flush=True);os._exit(1)
_,status=os.waitpid(child,0)
assert os.waitstatus_to_exitcode(status)==0, 'isolation validation failed'
