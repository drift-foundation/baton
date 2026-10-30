"""Read installed JSON/public projections; write proposed bytes only in this dossier."""
import copy
import json
import os
from pathlib import Path
from recover_packet import DEST, PACKET, checked_bytes, read_state, sha

state = read_state(DEST)
paths = ('deployment.json', 'generated/configuration.json', 'generated/configure-inputs.json', 'inputs.json')
changes = {}
roots = set()
for name in paths:
    data, mode = checked_bytes(DEST / name)
    original = json.loads(data)
    proposed = copy.deepcopy(original)
    for worker in proposed['workers']:
        roots.add(worker['deployment']['workspace_storage'])
        worker['deployment']['workspace_storage'] = state['workspace_root']
    # Assert that the only semantic change is workspace_storage.
    reverted = copy.deepcopy(proposed)
    for old, new in zip(original['workers'], reverted['workers']):
        new['deployment']['workspace_storage'] = old['deployment']['workspace_storage']
    assert reverted == original
    assert len({w['deployment']['launch_home'] for w in proposed['workers']}) == 2
    assert len({w['deployment']['credential_home'] for w in proposed['workers']}) == 2
    encoded = (json.dumps(proposed, indent=2, sort_keys=True) + '\n').encode()
    for folder, content in (('before', data), ('after', encoded)):
        target = PACKET / folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    changes[name] = {'before': sha(data), 'after': sha(encoded), 'mode': mode}
preserved = {}
for path in [DEST/'instance.json', DEST/'authority-identity.json', *sorted((DEST/'generated').rglob('*'))]:
    if path.is_file() and str(path.relative_to(DEST)) not in changes:
        data, mode = checked_bytes(path)
        preserved[str(path.relative_to(DEST))] = {'sha256':sha(data), 'mode':mode}
selector=json.loads((DEST/'instance.json').read_text())
stores={name:{'path':selector[name], 'device':os.stat(selector[name]).st_dev, 'inode':os.stat(selector[name]).st_ino} for name in ('job_store','control_store')}
# Authority path is named by actual emitted deployment, never opened as a raw DB.
authority=json.loads((DEST/'deployment.json').read_text())['authority_store']
stores['authority_store']={'path':authority,'device':os.stat(authority).st_dev,'inode':os.stat(authority).st_ino}
plan={'schema':'baton.w325959.workspace-recovery/1','destination':str(DEST),'state':state,'changes':changes,'preserved_files':preserved,'stores':stores,'guard_roots':sorted(roots)}
(PACKET/'CHANGE.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
print(json.dumps({'changed_files':list(changes),'committed_root':state['workspace_root'],'preserved_files':len(preserved)}))
