"""Preparation/check by default. Build and run each require separate owner selection."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def check():
    expected = json.loads((HERE / 'PACKET-PINS.json').read_text())
    for name, wanted in expected.items():
        if sha((HERE / name).read_bytes()) != wanted:
            raise ValueError('packet drift: ' + name)
    actual_context = {str(x.relative_to(HERE)) for x in (HERE/'context').rglob('*') if x.is_file()}
    if actual_context != {name for name in expected if name.startswith('context/')} :
        raise ValueError('unlisted or missing build-context file')
    return sha((HERE / 'PACKET-PINS.json').read_bytes())

def durable_state(receipt, state):
    with (receipt / 'state.json').open('w') as output:
        output.write(json.dumps(state, indent=2)+'\n')
        output.flush()
        os.fsync(output.fileno())
    fd = os.open(receipt, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'build', 'select', 'run'])
    parser.add_argument('--owner-selected', action='store_true')
    parser.add_argument('--selection-sha256')
    args = parser.parse_args()
    pin = check()
    if args.action == 'check':
        print(json.dumps({'packet_sha256': pin, 'engine_invoked': False}))
        return
    if args.action in ('build', 'run') and not args.owner_selected:
        parser.error('this action needs its own recorded owner selection')
    if args.action == 'build':
        receipt = HERE / 'BUILD-RECEIPT'
        receipt.mkdir(mode=0o700)  # exclusive: never rerun or overwrite
        iid = receipt / 'image.id'
        argv = ['docker', 'build', '--pull=false', '--memory', '2g', '--cpu-period', '100000', '--cpu-quota', '100000', '--iidfile', str(iid),
                '-f', str(HERE / 'context/worker/Dockerfile.claude'), str(HERE / 'context')]
        state = {'packet_sha256': pin, 'argv': argv, 'timeout_seconds': 1800,
                 'status': 'intent', 'provider_invoked': False}
        durable_state(receipt, state)
        start = time.monotonic()
        try:
            with (receipt / 'build.log').open('xb') as log:
                result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
            state['exit_code'] = result.returncode
            if result.returncode:
                raise ValueError('build failed; no retry selected')
            image = iid.read_text().strip()
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
                raise ValueError('invalid image identity')
            state.update(status='candidate-built', image=image)
        except BaseException as failure:
            state.update(status='failed-or-uncertain', error=type(failure).__name__,
                         recovery='Do not retry; preserve build receipts. A timed-out daemon build may continue; owner must reconcile before another operation.')
            raise
        finally:
            state['seconds'] = time.monotonic()-start
            durable_state(receipt, state)
        print(json.dumps(state, indent=2))
    elif args.action == 'select':
        build = json.loads((HERE / 'BUILD-RECEIPT/state.json').read_text())
        if build['status'] != 'candidate-built' or build['packet_sha256'] != pin:
            raise ValueError('no matching successful build receipt')
        image = (HERE / 'BUILD-RECEIPT/image.id').read_text().strip()
        if image != build['image']:
            raise ValueError('image identity drift')
        selection = dict(schema='baton.verifier-engine-proof-selection/1', image=image,
                         uid=65532, gid=65532, proof_id='w325695-proof-376414',
                         layout_sha256=sha((HERE/'LAYOUT.json').read_bytes()),
                         payload_sha256=sha((HERE/'kernel-payload.py').read_bytes()),
                         runner_sha256=sha((HERE/'engine-proof.py').read_bytes()))
        raw=(json.dumps(selection,indent=2)+'\n').encode()
        with (HERE/'SELECTION.json').open('xb') as output: output.write(raw)
        print('Candidate selection SHA256: '+sha(raw))
        print('After owner selects this exact image/selection, run:')
        print('python3 -B '+str(HERE/'packet.py')+' run --owner-selected --selection-sha256 '+sha(raw))
    else:
        raw=(HERE/'SELECTION.json').read_bytes()
        if sha(raw) != args.selection_sha256:
            raise ValueError('exact selected digest required')
        raise SystemExit(subprocess.call([sys.executable,'-B',str(HERE/'engine-proof.py'),
                           '--selection',str(HERE/'SELECTION.json'),
                           '--selection-sha256',args.selection_sha256,'--execute-reviewed']))

if __name__ == '__main__':
    main()
