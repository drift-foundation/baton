"""Packet-only static/mocked checks; no Codex/engine subprocess or real credential."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import time
from unittest import mock
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import capture
import render_commands
import render_offline
import offline_tier_probe
import setup_offline

start = time.monotonic()
passed = []
for file in sorted(HERE.glob('*.py')):
    ast.parse(file.read_text()); passed.append('syntax:' + file.name)
s = json.loads((HERE / 'selection.template.json').read_text())
s.update(run_id='synthetic-tier-packet',execution_root='/var/tmp/synthetic-tier-packet-not-created',uid=1000,gid=1000)
for tier in (None, 'fast'):
    p = dict(s, service_tier=tier)
    render_commands.render(p, 'login-help', proposal=True)
    passed.append('renderer accepts optional tier:' + str(tier))
for tier in ('flex', 'FAST', '', 1, ['fast']):
    try:
        render_commands.render(dict(s, service_tier=tier), 'login-help', proposal=True)
    except ValueError:
        passed.append('renderer rejects:' + repr(tier))
    else:
        raise AssertionError('unsupported tier accepted')
version = HERE.parent / 'n3-execution-n3-386002-01/probe-version-01/probe-output/stdout.txt'
prefix = ['codex','exec','--dangerously-bypass-approvals-and-sandbox','--ignore-user-config','--ignore-rules','--json','--model','SYNTHETIC']
class SuppressedTurn(Exception):
    pass
for tier, tail, status_code, should_reach_turn in [
        (None, [], 1, False), ('fast', ['-c', 'service_tier="fast"'], 1, False),
        (None, [], 0, True), ('fast', ['-c', 'service_tier="fast"'], 0, True),
        (None, ['-c', 'service_tier="fast"'], 0, False), ('fast', [], 0, False),
        ('fast', ['-c', 'service_tier="flex"'], 0, False)]:
    with tempfile.TemporaryDirectory(prefix='baton-tier-packet-', dir='/var/tmp') as name:
        root=Path(name); home=root/'home';out=root/'out';home.mkdir();out.mkdir();calls=[]
        cfg=root/'synthetic-context.json'
        cfg.write_text(json.dumps(dict(authorization='SYNTHETIC-NOT-AUTHORITY',qualification_only=True,
            login_status_help_evidence='SYNTHETIC',tool_inventory_evidence='SYNTHETIC',image_tool_decision='SYNTHETIC',
            codex_home=str(home/'synthetic-home'),argv=prefix+tail+['SYNTHETIC prompt'],
            service_tier=dict(requested=tier,observed=None))))
        def bounded(argv,stem,env,seconds,limit):
            calls.append((stem,argv))
            if stem=='version':
                (out/'version.stdout').write_bytes(version.read_bytes());return 0
            if stem=='turn':
                assert argv==prefix+tail+['SYNTHETIC prompt']
                raise SuppressedTurn('no process and no fabricated successful output')
            assert stem=='local-login-status'
            return status_code
        with mock.patch.object(capture,'OUT',out),mock.patch.object(capture,'HOME',str(home)),mock.patch.object(capture.sys,'argv',['capture.py','live']),mock.patch.object(capture,'bounded',bounded),mock.patch.object(capture.shutil,'which',lambda name,**kw:'/synthetic/'+name),mock.patch.object(capture,'Path',side_effect=lambda v:cfg if v=='/packet/live-context.json' else Path(v)):
            try: capture.main()
            except (SystemExit,SuppressedTurn): pass
        assert any(stem=='turn' for stem,_ in calls)==should_reach_turn
        if tier != ('fast' if len(tail)==2 else None) or 'service_tier="flex"' in tail:
            assert calls==[]
        passed.append('capture:' + repr((tier,tail,status_code,should_reach_turn)))
for stem,argv in offline_tier_probe.PROBES:
    assert argv[0]=='codex' and argv[-1]=='--help'
    assert '--model' not in argv and not any(x in argv for x in ('login','resume','fork','review'))
    passed.append('help-only probe:'+stem)
offline=json.loads((HERE/'offline.selection.json').read_text())
commands=render_offline.render(offline)
assert commands['create'][commands['create'].index('--network')+1]=='none'
assert commands['authorization'] is None
assert len([x for x in commands['create'] if x=='--mount'])==4
passed.append('offline mounts and network isolation')
try: setup_offline.setup(offline)
except ValueError as error: assert 'not selected' in str(error)
else: raise AssertionError('unselected setup wrote paths')
passed.append('unselected setup refuses before writes')
print(json.dumps(dict(kind='packet-static-and-mocked-not-provider-evidence',passed=len(passed),cases=passed,
    elapsed_seconds=time.monotonic()-start,engine_calls=0,codex_subprocesses=0,real_credential_reads=0,successful_turn_fixtures=0),indent=2))
