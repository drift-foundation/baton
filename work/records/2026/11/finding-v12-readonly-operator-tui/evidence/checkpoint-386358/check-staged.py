"""Read-only: do the STAGED bytes equal the reviewed candidate (combined patch f0cc2bd8…)?

Run from the repository root after staging and before committing. Reads the index with
`git show :path` and `git diff --cached --name-only`; changes nothing.
"""
import hashlib,json,os,subprocess,sys
from pathlib import Path
here=Path(__file__).resolve().parent
manifest=json.loads((here.parent/'correction-386357/manifest.json').read_text())
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
staged=sorted(subprocess.run(['git','diff','--cached','--name-only'],capture_output=True,text=True,check=True,env=env).stdout.split())
bad=[]
for path,digest in sorted(manifest['files'].items()):
    shown=subprocess.run(['git','show',':'+path],capture_output=True,env=env)
    got=hashlib.sha256(shown.stdout).hexdigest() if shown.returncode==0 else None
    if got!=digest:bad.append(path+(' (not in the index)' if got is None else ' (staged bytes differ from the reviewed ones)'))
extra=[path for path in staged if path not in manifest['files']]
missing=[path for path in manifest['files'] if path not in staged]
print(json.dumps(dict(reviewed_paths=len(manifest['files']),staged_paths=len(staged),not_matching=bad,staged_but_not_reviewed=extra,reviewed_but_not_staged=missing,ready=not bad and not extra and not missing),indent=1))
sys.exit(0 if not bad and not extra and not missing else 1)
