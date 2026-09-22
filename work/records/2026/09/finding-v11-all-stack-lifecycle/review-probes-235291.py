"""Independent registry/lock/error-report probes; no service launches."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path.cwd() / 'tools'))
import infra_deployment as d
start = time.monotonic()
checks = []
with tempfile.TemporaryDirectory(prefix='w235221-review-') as temp:
    base = Path(temp)
    root = base / 'deployment'
    root.mkdir(mode=0o700)
    registry = root / d.REGISTRY
    entries = [{'name':'main','directory':'.'}, {'name':'missing','directory':'missing'}, {'name':'later','directory':'later'}]
    registry.write_text(json.dumps({'version':1,'stacks':entries}))
    (root/'infra.json').write_text(json.dumps({'version':1,'services':[{'name':'standin','command':[sys.executable,'-c','pass']}]}))
    (root/'later').mkdir(mode=0o700)
    (root/'later'/'infra.json').write_bytes((root/'infra.json').read_bytes())
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = d.run(['status', str(root)])
    result = json.loads(output.getvalue())
    assert rc == 1 and len(result['stacks']) == 3
    assert result['stacks'][1]['exit_code'] == 2
    assert result['stacks'][2]['report']['state'] == 'stopped'
    checks.append('missing member directory is reported; later stack inspected')
    victim = base/'victim'
    victim.write_bytes(b'untouched')
    victim.chmod(0o600)
    lock = root/'run'/'deployment.lock'
    lock.unlink()
    for kind in ('symlink','hardlink','fifo'):
        if kind == 'symlink': lock.symlink_to(victim)
        elif kind == 'hardlink': os.link(victim, lock)
        else: os.mkfifo(lock, 0o600)
        try:
            with patch.object(d, 'invoke', side_effect=AssertionError('lifecycle invoked')):
                try: d.run(['status', str(root)])
                except d.infra.InfraError: pass
                else: raise AssertionError('unsafe lock accepted')
            assert victim.read_bytes() == b'untouched'
            checks.append(kind+' deployment lock refuses before member invocation')
        finally: lock.unlink()
    outside = base/'outside'
    outside.mkdir()
    (root/'escape').symlink_to(outside, target_is_directory=True)
    registry.write_text(json.dumps({'version':1,'stacks':[entries[0], {'name':'escape','directory':'escape'}]}))
    try: d.members(str(root))
    except d.infra.InfraError: pass
    else: raise AssertionError('canonical escape accepted')
    checks.append('symlink member escape refuses')
    registry.write_text('{"version":1,"version":1,"stacks":[]}')
    try: d.members(str(root))
    except d.infra.InfraError: pass
    else: raise AssertionError('duplicate JSON key accepted')
    checks.append('duplicate JSON key refuses')
print(json.dumps({'checks':checks,'passed':len(checks),'elapsed_seconds':time.monotonic()-start,'live_services':False}))
