"""Read checkpoint objects and prepare exact archives; no engine capability."""
from pathlib import Path
import subprocess, tarfile, io, hashlib, json
import sys
P=Path(sys.argv[1]);BASE=sys.argv[2]
VECTOR='work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def write_tar(path, files):
 with tarfile.open(path,'w',format=tarfile.USTAR_FORMAT) as t:
  for name,(raw,mode) in sorted(files.items()):
   i=tarfile.TarInfo(name);i.size=len(raw);i.mode=mode;i.mtime=0;t.addfile(i,io.BytesIO(raw))
files={}
with tarfile.open(P/'source.tar') as t:
 for i in t:
  if i.isfile():files[i.name]=(t.extractfile(i).read(),i.mode)
write_tar(P/'source.tar',files)
context={}; image_files={}
for name,(body,mode) in files.items():
 rel=name.removeprefix('v12/')
 if rel.startswith('python/src/baton_v12/provider_policy/') or rel.startswith('python/src/baton_v12/source_profiles/'):
  context[rel]=(body,mode);image_files['/opt/baton/'+rel.split('baton_v12/',1)[1]]=sha(body)
for rel in ['python/src/baton_v12/attempt_log_format.py','python/src/baton_v12/verification_context.py','worker/baton_worker.py','worker/adapter_refusal.py','worker/claude_agent.py','worker/bounded_command.py','worker/dogfood_entry.py','worker/codex_agent.py','worker/codex_entry.py','worker/worker-control-1.0.schema.json','worker/verifier-layout-marker.json']:
 body,mode=files['v12/'+rel];context[rel]=(body,mode);image_files['/opt/baton/'+Path(rel).name]=sha(body)
source_manifest={name:{'sha256':sha(body),'mode':mode} for name,(body,mode) in sorted(files.items())}
manifest_raw=(json.dumps(source_manifest,sort_keys=True,indent=2)+'\n').encode();(P/'source-files.json').write_bytes(manifest_raw)
identity={'schema':'baton.q1-build/1','source_commit':BASE,'source_manifest_sha256':sha(manifest_raw),'packet_id':'q1-386214','image_files':image_files,'codex_binary_sha256':'b452ca20f838a8855a88a41050ee4a694033fff4ea3ecdad5633e6e0e8d13f2b','codex_binary_bytes':294277432,'cli_version':'codex-cli 0.169.0'}
body=(json.dumps(identity,sort_keys=True,indent=2)+'\n').encode();context['q1-build.json']=(body,0o644);(P/'q1-build.json').write_bytes(body)
recipe=files['v12/worker/Dockerfile.codex'][0].decode().replace('FROM node:22-trixie-slim','FROM node@sha256:f0960f8dc047f358e3fb428f36ccba21732194fa5f0cac849f401e63e62fb9e6')
recipe+='\nCOPY q1-build.json /opt/baton/q1-build.json\nLABEL org.opencontainers.image.revision="'+BASE+'" io.baton.q1.packet="q1-386214" io.baton.q1.source="'+sha(manifest_raw)+'"\n'
context['worker/Dockerfile.codex']=(recipe.encode(),0o644);(P/'Dockerfile.q1').write_text(recipe)
write_tar(P/'context.tar',context)
(P/'inputs.json').write_text(json.dumps({'source_commit':BASE,'source_tar_sha256':sha((P/'source.tar').read_bytes()),'context_tar_sha256':sha((P/'context.tar').read_bytes()),'recipe_sha256':sha(recipe.encode()),'source_manifest_sha256':sha(manifest_raw),'image_identity_sha256':sha(body),'retained_binary_evidence':'../source-provenance-386126/binary-match.json','base':'node@sha256:f0960f8dc047f358e3fb428f36ccba21732194fa5f0cac849f401e63e62fb9e6'},indent=2)+'\n')
print(json.dumps({'source_files':len(files),'context_files':len(context),'source_archive_bytes':(P/'source.tar').stat().st_size,'context_archive_bytes':(P/'context.tar').stat().st_size}))
