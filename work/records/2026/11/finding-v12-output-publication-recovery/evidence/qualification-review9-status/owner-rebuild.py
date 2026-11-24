#!/usr/bin/env python3
"""Owner-run packaging gate only. No image, container or live-provider launch."""
import hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path('/home/sl/src/baton')
DOSSIER = ROOT / 'work/records/2026/11/finding-v12-output-publication-recovery'
manifest = DOSSIER / 'evidence/qualification-review9-status/corrected-source.json'
raw = manifest.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'a86c3299f36b9d7d95509197d4bfeec26216ca90d62e94deb5b39ef3592ee1d0'
for name, want in json.loads(raw).items():
    path = ROOT / name
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != want:
        raise SystemExit('refused source drift: ' + name)
if sys.argv[1:] == ['--check']:
    print('Corrected 56-path source identity verified. No build run.')
    raise SystemExit(0)
if sys.argv[1:]:
    raise SystemExit('usage: script [--check]')
evidence = DOSSIER / 'evidence' / ('packaging-owner-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
evidence.mkdir(exist_ok=False)
(evidence / 'source.json').write_text(json.dumps({'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(), 'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'scope': 'build and packaging gate only'}, indent=2)+'\n')
scratch = tempfile.mkdtemp(prefix='baton-695-package-', dir='/var/tmp')
env = os.environ.copy()
env.update(BATON_V12_STACK_TEST_ROOT=scratch, BATON_V12_DISK_ROOT=scratch, TMPDIR=scratch)
argv = ['just', '--justfile', str(ROOT/'v12/justfile'), 'test-packaging']
print('Evidence:', evidence, flush=True)
began=time.monotonic()
with (evidence/'gate.log').open('w') as log:
    proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for line in proc.stdout:
        print(line,end='',flush=True); log.write(line); log.flush()
    rc=proc.wait()
(evidence/'result.json').write_text(json.dumps({'argv':argv,'exit_status':rc,'seconds':time.monotonic()-began,'scratch':scratch},indent=2)+'\n')
print('Packaging exit:',rc,'Evidence:',evidence,flush=True)
raise SystemExit(rc)
