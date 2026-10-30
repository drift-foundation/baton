import os,stat,grp,pwd,json,hashlib,subprocess,ctypes
from pathlib import Path
assert os.geteuid()==0, 'operator host root required'
root=Path('/opt/baton-next-run-source-345599')
for path in [Path('/'),Path('/opt'),Path('/var'),Path('/var/lib'),root]:
 s=path.lstat(); assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022, str(path)
for name in ['/opt/baton-next-run','/var/lib/baton-next-run','/etc/sudoers.d/baton-next-run']:
 assert not os.path.lexists(name), 'preserve existing/partial installation: '+name
assert pwd.getpwnam('sl').pw_uid==1000 and grp.getgrnam('sl').gr_gid==1000 and grp.getgrnam('docker').gr_gid==119
for name in ['/usr/sbin/useradd','/usr/sbin/visudo','/usr/bin/sudo','/usr/bin/python3','/usr/bin/git','/usr/bin/docker']:
 assert os.access(name,os.X_OK), name
secret=Path('/home/sl/.claude/.credentials.json').lstat()
assert stat.S_ISREG(secret.st_mode) and secret.st_nlink==1 and secret.st_uid==1000 and not secret.st_mode & 0o077
sock=Path('/var/run/docker.sock').stat(); assert stat.S_ISSOCK(sock.st_mode) and sock.st_gid==119
for name,expected in json.loads((root/'package-content.json').read_text()).items():
 path=root/name; s=path.lstat(); assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==0 and not s.st_mode & 0o022
 assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, name
image=subprocess.check_output(['/usr/bin/docker','image','inspect','baton-v12-claude-worker:w239528-244216','--format','{{.Id}}'],text=True).strip()
assert image=='sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2'
base=subprocess.check_output(['/usr/bin/git','-c','safe.directory=/home/sl/src/baton','-C','/home/sl/src/baton','show','--format=%H','--no-patch','d3a7a41cc7347e4741706673c20f62b4a3190f65'],text=True).strip()
assert base=='d3a7a41cc7347e4741706673c20f62b4a3190f65'
libc=ctypes.CDLL(None,use_errno=True); abi=libc.syscall(444,0,0,1); assert abi>=3, ('Landlock ABI',abi,ctypes.get_errno())
print(json.dumps({'state':'operator-prerequisites-checked','base':base,'image':image,'landlock_abi':abi,'credential_contents_read':False,'destinations_absent':True}))
