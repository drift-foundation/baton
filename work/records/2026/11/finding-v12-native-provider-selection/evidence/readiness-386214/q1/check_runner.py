"""Local runner bounds and read-only preflight checks; never execute Docker."""
import importlib.util, json, os, sys, tempfile
from pathlib import Path
from unittest import mock
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('q1_owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
with mock.patch('subprocess.Popen',side_effect=AssertionError('read-only check spawned a process')):
    checked=owner.check()
assert checked['engine_calls']==0 and checked['credential_reads']==0
checks=['read-only manifest/source/context check with all subprocesses prohibited']
with tempfile.TemporaryDirectory(prefix='baton-q1-runner-check-386214-',dir='/var/tmp') as temporary:
    root=Path(temporary)
    for name in ('commands','client-home','docker-config','tmp'):(root/name).mkdir(mode=0o700)
    run=owner.Commands(root)
    answer=run([sys.executable,'-I','-c','import os; print(os.environ["HOME"])'],seconds=2)
    assert answer['status']==0 and answer['stdout'].strip()==str(root/'client-home')
    checks.append('child HOME and Docker configuration are isolated from user credentials')
    for code,seconds,cap,expected in [('print("x"*1000)',2,32,'output bound exceeded'),('import time; time.sleep(5)',.1,1024,'command bound exceeded')]:
        try:run([sys.executable,'-I','-c',code],seconds=seconds,cap=cap)
        except RuntimeError as exc:assert expected in str(exc)
        else:raise AssertionError('expected bounded refusal')
        result=json.loads((root/'commands'/f'{run.n:03d}.result.json').read_text())
        assert result['failure'] and result['stdout_bytes']+result['stderr_bytes']<=cap
        try:os.killpg(result['pgid'],0)
        except ProcessLookupError:pass
        else:raise AssertionError('process group survived bounded refusal')
        checks.append(expected+'; owned process group gone')
    with mock.patch('subprocess.Popen',side_effect=RuntimeError('forbidden engine invocation')):
        try:run(['docker','create','--name','must-not-start','image'],seconds=0)
        except AssertionError:pass
        else:raise AssertionError('zero bound did not refuse')
    checks.append('zero deadline refuses before process creation')
print(json.dumps(dict(checks=checks,passed=len(checks),failed=0,engine_operations=0,provider_calls=0,temporary_root_removed=not root.exists()),indent=2))
