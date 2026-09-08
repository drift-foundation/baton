"""Independent old/new exact-manifest import proof; no source reader or Docker."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import live_controller as old
import live_controller_setup as new

PROGRAM = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
try:
 from baton_v12.worker_manager import credentials,workspaces
 from baton_v12.worker_manager.store import ControlStore
except BaseException as e:
 print(json.dumps(dict(outcome='refused',kind='file-not-found' if type(e) is FileNotFoundError else 'other',errno=e.errno if isinstance(e,OSError) else None,missing_worker_schema=Path(getattr(e,'filename','') or '').name=='worker-control-1.0.schema.json')))
else:
 print(json.dumps(dict(outcome='imports-passed',credential_construction=False,source_read=False)))
'''
report = {}
for label, module in [('original',old),('corrected',new)]:
    manifest=json.loads(module.MANIFEST.read_text())
    with tempfile.TemporaryDirectory(prefix='w106673-review-import-') as folder:
        root=Path(folder)
        runtime=module.snapshot_runtime(root,manifest)
        result=subprocess.run(['/usr/bin/python3','-B','-s','-c',PROGRAM,str(runtime/'src')],cwd=root,env={'PATH':'/usr/bin:/bin'},capture_output=True,text=True,timeout=30)
        assert result.returncode==0 and result.stderr=='', 'unexpected child failure'
        report[label]={'manifest_sha256':hashlib.sha256(module.MANIFEST.read_bytes()).hexdigest(),'observation':json.loads(result.stdout)}
assert report['original']['observation']=={'outcome':'refused','kind':'file-not-found','errno':2,'missing_worker_schema':True}
assert report['corrected']['observation']=={'outcome':'imports-passed','credential_construction':False,'source_read':False}
print(json.dumps(report,indent=2))
