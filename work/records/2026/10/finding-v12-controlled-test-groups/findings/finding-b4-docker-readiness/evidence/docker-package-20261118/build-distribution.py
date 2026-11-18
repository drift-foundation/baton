from pathlib import Path
import os,json,subprocess,time,hashlib,re
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());m=json.loads((H/'source-manifest.json').read_text());S=R/m['snapshot'];out=R/'work/scratch/w384944-package-build-20261118';out.mkdir()
py='/home/sl/.local/state/baton-v12-venv/bin/python'
locks={}
for name in ['requirements.lock','requirements.build.lock']:
 for pkg,version in re.findall(r'^([\w.-]+)==([^\s\\]+)',(S/'v12/python'/name).read_text(),re.M):locks[pkg]=version
code='import importlib.metadata,json;print(json.dumps({p:importlib.metadata.version(p) for p in '+repr(list(locks))+'}))'
installed=json.loads(subprocess.check_output([py,'-c',code],text=True));assert installed==locks,(installed,locks)
(H/'dependencies.json').write_text(json.dumps(dict(locked=locks,installed=installed,interpreter=py),indent=2)+'\n')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYINSTALLER_CONFIG_DIR=str(out/'cache'),GIT_CEILING_DIRECTORIES=str(S.parent))
argv=[py,'-m','PyInstaller','--noconfirm','--clean','--distpath',str(out/'out'),'--workpath',str(out/'work'),'packaging/stack.spec']
(H/'distribution-build-plan.json').write_text(json.dumps(dict(argv=argv,cwd=str(S/'v12/python'),timeout_seconds=1800,output=str(out),git_ceiling=str(S.parent)),indent=2)+'\n');start=time.monotonic()
with (H/'distribution-build.log').open('x') as f:r=subprocess.run(argv,cwd=S/'v12/python',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
result=dict(status=r.returncode,seconds=time.monotonic()-start,output=str(out));(H/'distribution-build-result.json').write_text(json.dumps(result,indent=2)+'\n');assert r.returncode==0
files={str(p.relative_to(out/'out/distro')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'out/distro').rglob('*')) if p.is_file()};(H/'artifact-manifest.json').write_text(json.dumps(files,indent=2)+'\n')
(H/'artifact-identity.json').write_text(subprocess.check_output([str(out/'out/distro/baton-v12-stack'),'identity'],text=True))
print(json.dumps(result))
