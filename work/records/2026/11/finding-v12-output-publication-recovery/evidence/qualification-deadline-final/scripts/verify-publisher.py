#!/usr/bin/env python3
"""Check the captured publisher against its configured runtime identity and roots."""
import json,os,sys
from pathlib import Path
capture,instance,attempt=sys.argv[1:]
c=json.loads(Path(capture).read_text())[0]
i=json.loads(Path(instance).read_text());d=json.loads(Path(i['deployment']).read_text())
w=[w['deployment'] for w in d['workers'] if w['role']=='publication'];assert len(w)==1
w=w[0];uid=os.geteuid();gid=w['workspace_group'];assert uid>0 and gid>0
assert c['Config']['User']==f'{uid}:{gid}','runtime identity differs from manager UID/workspace group'
assert c['HostConfig']['NetworkMode']=='none','publisher network must be none'
mounts=c['Mounts'];m={x['Destination']:x for x in mounts};assert len(m)==len(mounts),'duplicate destination'
assert m['/input/source']['RW'] is False
assert not [x for x in mounts if x['Destination'].startswith('/input') and x['RW']]
storage=Path(w['workspace_storage']);launch=Path(w['launch_home'])
expected={'/output':str(storage/attempt/'workspace'),'/scratch':str(storage/attempt/'scratch'),'/run/baton/exchange/events':str(launch/attempt/'events'),'/run/baton/attempt-logs':str(launch/'logs'/attempt)}
actual={x['Destination']:x['Source'] for x in mounts if x['RW']}
assert actual==expected, f'writable roots differ: {actual!r}'
names=[v.split('=',1)[0] for v in c['Config']['Env']]
assert not [n for n in names if n.startswith(('ANTHROPIC','CLAUDE')) or 'CREDENTIAL' in n or 'TOKEN' in n]
assert not [x for x in m if 'credential' in x.lower()]
print('ok   publisher runtime identity and exact writable roots; inputs read-only; no provider credentials')
