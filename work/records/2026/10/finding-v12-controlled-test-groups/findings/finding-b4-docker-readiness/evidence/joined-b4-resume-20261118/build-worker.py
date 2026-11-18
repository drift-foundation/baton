"""One selected offline build, after immutable source and base verification."""
from pathlib import Path
import hashlib,json,subprocess,time,uuid
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'AGENTS.md').is_file())
m=json.loads((HERE/'source-manifest.json').read_text());s=REPO/m['snapshot']
for p,entry in m['files'].items():assert hashlib.sha256((s/p).read_bytes()).hexdigest()==entry['sha256'],p
pre=json.loads((HERE/'preflight.json').read_text());assert subprocess.check_output(['docker','image','inspect',pre['base'],'--format','{{.Id}}'],text=True).strip()==pre['base_id']
tag='baton-w384944-joined:'+uuid.uuid4().hex[:12]
argv=['docker','build','--pull=false','--network=none','-f',str(s/'v12/worker/Dockerfile'),'-t',tag,str(s/'v12/worker')]
plan=dict(argv=argv,tag=tag,base=pre['base'],base_id=pre['base_id'],preexisting_images=subprocess.check_output(['docker','image','ls','-q','--no-trunc'],text=True).splitlines())
(HERE/'build-plan.json').write_text(json.dumps(plan,indent=2)+'\n');start=time.monotonic()
with (HERE/'build.log').open('x') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
result=dict(status=r.returncode,seconds=time.monotonic()-start);assert r.returncode==0
result['image']=subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip();(HERE/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
