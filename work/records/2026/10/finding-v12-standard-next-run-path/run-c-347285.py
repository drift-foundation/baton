"""W339626 exact C operator helper. Default: read-only. No sudo wrapper."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

RUN = 'w339626-live-345599'
HERE = Path(__file__).resolve().parent
INSTALLED = Path('/opt/baton-next-run')
PINS = {'PACKET.json': '4d24ec31635de45c4bdfa72247bbedb28e673fc2985026dd6b4c825df27a2dc5', 'adapter.json': 'cbe3bb4ade990eb5411c64a40be74a10e46a79f48343c499b5f1a8453fabc9c7', 'commands.json': '6b644120fb1af05d4557b1f9d67ff15ed9dc4455f2cac841bdbe991426f0efc3', 'deployment.json': 'a54e901fb43c4aca480da64cf781464062b99fa5214c2e8f1b58cad494449a15', 'input.json': '5fc07524d1255a92d0f4b94a31317fa338013eb3997c7b70c989f19059bbd9dd', 'policy.json': '403d8de55b81f38782ba77939bf71d37d5693339b054e3b677b8d2188b8f54d1', 'runtime-profile.json': 'b6d4ea37066c22681c6509b8eff209d9b82661fa8ffdd2c33bcc8bf92f3a6fb4', 'submission.json': '724decb59781f9c17771beb8a916d21dc5260fbcd87c71888eed02e1f5449701', 'task.json': '5113b7791ee78cef5826f9d1a8dd532a989918375596168cbf67942ac079a18d'}

def check():
    for name, digest in PINS.items():
        raw = (INSTALLED / 'runs' / RUN / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise RuntimeError('generated input drift: ' + name)
    raw = (INSTALLED / 'installation.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != '342587c532c9a6aa03ca65d2a664bb79b815812b43619a5a907e0a65a9b0c4ac':
        raise RuntimeError('installation drift')
    if os.geteuid() != 1000:
        raise RuntimeError('run as caller sl/uid1000, never sudo this helper')
    print('Exact generated pins match; C selection is external, not inferred.', flush=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute-selected-run', action='store_true')
    args = ap.parse_args()
    check()
    if not args.execute_selected_run:
        return 0
    # A local once-only receipt directory supplements the installed consumption
    # fence. Never delete it or retry this helper after an uncertain dispatch.
    out = HERE / 'operator-c-receipts-347285'
    out.mkdir(mode=0o700)
    start_status = None
    status_status = None
    for action in ('start', 'status'):
        command = [str(INSTALLED / 'client.py'), action, RUN]
        before = time.monotonic()
        with (out / (action + '.stdout')).open('xb') as stdout, (out / (action + '.stderr')).open('xb') as stderr:
            result = subprocess.run(command, stdout=stdout, stderr=stderr)
        (out / (action + '.status')).write_text(str(result.returncode) + chr(10))
        (out / (action + '.json')).write_text(json.dumps({'argv':command,'exit':result.returncode,'seconds':time.monotonic()-before}) + chr(10))
        if action == 'start':
            start_status = result.returncode
        if action == 'status':
            status_status = result.returncode
        print(action + ' exit ' + str(result.returncode) + '; receipts ' + str(out), flush=True)
    print('No retry. Return receipts for independent review and operator collection of private final reports.', flush=True)
    return start_status or status_status

if __name__ == '__main__':
    sys.exit(main())
