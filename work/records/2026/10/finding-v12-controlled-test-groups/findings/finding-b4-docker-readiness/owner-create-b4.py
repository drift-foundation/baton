"""Owner-run creation: atomically create, bind and attach the B4 child. No service or tests started."""
import json, subprocess
from pathlib import Path
BASE=['/home/sl/opt/baton/v11/0650c61/bin/baton','--config','/home/sl/baton-v11.14aecfb/baton.json','--participant','baton.slaw']
record='work/records/2026/10/finding-v12-controlled-test-groups/findings/finding-b4-docker-readiness'
result=subprocess.run(BASE+['create','team=baton','kind=codx','title=V12 B4: Docker and environment readiness for W384870','origin=decomposition','classification=confirmed-defect','parent=W384870','binding=baton:'+record,'body=Owner authorizes codexpc alongside K. Participant baton.codxpc, role impl. Read '+record+'/FINDING.md and parent T384870 introductions. First checkpoint: read-only B4 test/prerequisite inventory, exact operator commands and proposed file/resource ownership. No product edits/builds/engine runs yet. Claim this child only; K retains Stage C. baton.prompt coordinates and independently reviews; Slawomir alone owns Git. Return first checkpoint by passing to baton.decide.','op-id=w384870-b4-owner-create-20261031'],text=True,capture_output=True)
print(result.stdout,end='');print(result.stderr,end='')
result.check_returncode()
subprocess.run(BASE+['children','work=W384870'],check=True)
