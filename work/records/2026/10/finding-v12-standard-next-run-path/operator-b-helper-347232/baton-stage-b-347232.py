#!/usr/bin/python3 -I -B
"""Run selected W339626 Stage B once; never install or start a provider."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
CHECK = 'import os,stat,json,hashlib,pwd\nfrom pathlib import Path\nassert os.geteuid()==0\nroot=Path("/opt/baton-next-run")\ndef custody(p,uid=0,private=False):\n s=p.lstat()\n assert not stat.S_ISLNK(s.st_mode) and s.st_uid==uid and not s.st_mode & (0o077 if private else 0o022), str(p)\n return s\nraw=(root/"installation.json").read_bytes()\nassert hashlib.sha256(raw).hexdigest()=="342587c532c9a6aa03ca65d2a664bb79b815812b43619a5a907e0a65a9b0c4ac"\nc=json.loads(raw)\nassert json.loads((root/"READY").read_bytes())=={"installation_sha256":hashlib.sha256(raw).hexdigest()}\npaths=[root,root/"installation.json",root/"READY",root/"state",root/"runs",Path(c["storage"])]\npaths += [root/x for x in c["files"]]\npaths += list(Path("/opt/baton-next-run-source-345599").rglob("*"))\nfor p in paths:\n for a in [*p.parents,p]: custody(a)\nfor rel,digest in c["files"].items():\n assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel\nassert {str(x.relative_to(root)) for x in (root/"code").rglob("*") if x.is_file()}=={x for x in c["files"] if x.startswith("code/")}\nrule=b"#1000 ALL=(root) NOPASSWD: /opt/baton-next-run/entry.py request\\n"\nfor p in [root/"admission.sudoers",Path("/etc/sudoers.d/baton-next-run")]:\n custody(p);assert p.read_bytes()==rule\nfor a in c["accounts"]:\n assert pwd.getpwuid(a["uid"]).pw_gid==a["gid"]\n assert pwd.getpwuid(a["uid"]).pw_shell=="/usr/sbin/nologin"\n d=Path(a["credentials"]).parent\n custody(d,a["uid"],True)\n for f in d.iterdir():\n  s=custody(f,a["uid"],True);assert stat.S_ISREG(s.st_mode) and s.st_gid==a["gid"]\nprint(json.dumps({"state":"installation-custody-pass","files":len(c["files"]),"capacity":c["capacity"],"credential_contents_read":False,"writes":0}))\n'
RUN = 'w339626-live-345599'
CLIENT = '/opt/baton-next-run/client.py'
def main():
    if os.getuid() != 1000:
        raise RuntimeError('Run as sl, without sudo; individual checks request sudo themselves.')
    os.umask(0o077)
    logs = Path(tempfile.mkdtemp(prefix='baton-stage-b-347232-'))
    print('Receipts: ' + str(logs), flush=True)
    sequence = 0
    def step(label, argv, data=None, expected_refusal=False):
        nonlocal sequence
        sequence += 1
        print('\n' + label, flush=True)
        result = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        prefix = logs / (str(sequence).zfill(2) + '-' + label)
        Path(str(prefix)+'.stdout').write_bytes(result.stdout)
        Path(str(prefix)+'.stderr').write_bytes(result.stderr)
        Path(str(prefix)+'.status').write_text(str(result.returncode)+'\n')
        sys.stdout.buffer.write(result.stdout); sys.stdout.buffer.flush()
        sys.stderr.buffer.write(result.stderr); sys.stderr.buffer.flush()
        if expected_refusal:
            if result.returncode != 2 or b'managed next-run refused: Refusal: unsupported action or request operands' not in result.stderr:
                raise RuntimeError('Expected application refusal was not established; stopping.')
        elif result.returncode:
            raise RuntimeError(label + ' failed; stopping. Preserve receipts; do not retry preparation.')
        return result.stdout
    def require(value, key, expected):
        if value.get(key) != expected:
            raise RuntimeError('Unexpected '+key+': '+repr(value.get(key))+'; stopping.')
    custody = json.loads(step('installation-custody', ['/usr/bin/sudo','/usr/bin/python3','-I','-B','-c',CHECK]))
    require(custody,'state','installation-custody-pass')
    step('sudo-admission',['/usr/bin/sudo','-n','-l','/opt/baton-next-run/entry.py','request'])
    step('malformed-request',['/usr/bin/sudo','-n','/opt/baton-next-run/entry.py','request'],json.dumps({'action':'status','run':RUN,'extra':True}).encode(),True)
    # Exclusive marker prevents this helper from attempting preparation twice.
    marker=Path('/tmp/baton-stage-b-347232-prepare-attempted')
    with marker.open('x') as f:
        f.write(str(logs)+'\n')
    task=Path('/opt/baton-next-run-source-345599/validation-task.json').read_bytes()
    receipt=json.loads(step('prepare',[CLIENT,'prepare'],task))
    require(receipt,'run_id',RUN)
    if receipt.get('continuation_of') is not None:
        raise RuntimeError('Continuation returned; preserve receipt for review.')
    checked=json.loads(step('check',[CLIENT,'check',RUN]))
    require(checked,'state','checked'); require(checked,'run_id',RUN)
    status=json.loads(step('status',[CLIENT,'status',RUN]))
    require(status,'run_id',RUN); require(status,'state','prepared')
    isolation=json.loads(step('negative-isolation',['/usr/bin/sudo','/usr/bin/python3','-I','-B','/opt/baton-next-run-source-345599/operator-isolation.py']))
    require(isolation,'state','negative-access-checks-pass')
    print('\nStage B checks passed. No provider started. Receipts: '+str(logs),flush=True)
if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print('\nSTOP: '+str(error),file=sys.stderr)
        sys.exit(1)
