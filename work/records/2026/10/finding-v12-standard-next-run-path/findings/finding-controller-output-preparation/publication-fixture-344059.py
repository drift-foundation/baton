"""Unprivileged preparation fixture; never touches installed policy/credentials.
Uses the proposed shell stage/hash/publish sequence with current-uid ownership.
Root custody and actual visudo acceptance remain operator-only observations.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import time

here = Path(__file__).parent
started = time.monotonic()
root = Path(tempfile.mkdtemp(prefix='baton-publication-344059-'))
cases = []

def shell(body, folder, wanted):
    return subprocess.run(['bash', '-eu', '-c', body, 'fixture', str(folder), wanted], text=True, capture_output=True)

stage = '''
cd "$1"
test ! -e stage
test ! -L stage
install -m 400 source stage
printf '%s  %s\\n' "$2" stage | sha256sum -c -
'''
publish = '''
cd "$1"
test ! -e live
test ! -L live
printf '%s  %s\\n' "$2" stage | sha256sum -c -
install -m "$3" stage live
printf '%s  %s\\n' "$2" live | sha256sum -c -
'''
for filename, mode in [('sudoers-v3', 0o440), ('credential-sources-v3.json', 0o400)]:
    original = (here / filename).read_bytes()
    wanted = hashlib.sha256(original).hexdigest()
    for scenario in ('replacement-after-stage', 'mismatch', 'stage-collision', 'live-collision', 'live-symlink'):
        folder = root / (filename + '-' + scenario)
        folder.mkdir(mode=0o700)
        (folder / 'source').write_bytes(original if scenario != 'mismatch' else b'changed source\n')
        if scenario == 'stage-collision': (folder / 'stage').write_bytes(b'prior stage\n')
        result = shell(stage, folder, wanted)
        if scenario in ('mismatch', 'stage-collision'):
            assert result.returncode != 0 and not (folder / 'live').exists()
            if scenario == 'stage-collision': assert (folder / 'stage').read_bytes() == b'prior stage\n'
        else:
            assert result.returncode == 0, result.stderr
            # The mutable original is replaced after the approved snapshot.
            (folder / 'source').write_bytes(b'unreviewed replacement\n')
            if scenario == 'live-collision': (folder / 'live').write_bytes(b'prior live\n')
            if scenario == 'live-symlink': (folder / 'live').symlink_to('absent-canary')
            result = subprocess.run(['bash', '-eu', '-c', publish, 'fixture', str(folder), wanted, format(mode, 'o')], text=True, capture_output=True)
            if scenario == 'replacement-after-stage':
                assert result.returncode == 0, result.stderr
                final = (folder / 'live').lstat()
                assert (folder / 'live').read_bytes() == original
                assert stat.S_IMODE(final.st_mode) == mode and final.st_uid == os.getuid() and final.st_nlink == 1
            else:
                assert result.returncode != 0
                if scenario == 'live-collision': assert (folder / 'live').read_bytes() == b'prior live\n'
                else: assert (folder / 'live').is_symlink() and not (folder / 'absent-canary').exists()
        cases.append({'configuration': filename, 'scenario': scenario, 'passed': True})

procedure = (here / 'OPERATOR-344059.md').read_text()
blocks = re.findall(r'```sh\n(.*?)\n```', procedure, re.S)
for block in blocks:
    result = subprocess.run(['bash', '-n'], input=block, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
assert 'visudo -cf /home/sl/' not in procedure
for line in procedure.splitlines():
    if line.startswith('install ') and ('/etc/sudoers.d/' in line or '/etc/baton-managed-entry/w339626-v3-credential-sources.json' in line):
        assert '/root/baton-output-preparation-344059/' in line
result = {'scope': 'unprivileged preparation shell fixture, not product or installed acceptance', 'cases': cases, 'shell_blocks_bash_n': len(blocks), 'retained_fixture': str(root), 'elapsed_seconds': time.monotonic() - started, 'limitations': ['root ownership/custody not simulated as proven', 'visudo not executed', 'no real sudoers or credential files read or written', 'no bearer material', 'live publication collision guards rely on trusted parent and exclusive operator interval'], 'bundle_rebuilt': False}
(here / 'VALIDATION-344059.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
