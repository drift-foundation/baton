"""Successor check/run only; execution requires a later exact owner selection."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runner():
    spec = importlib.util.spec_from_file_location('successor_proof', HERE / 'engine-proof.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check():
    for name, expected in json.loads((HERE / 'PACKET-PINS.json').read_text()).items():
        if sha(HERE / name) != expected:
            raise ValueError('successor packet drift: ' + name)
    for name, expected in json.loads((HERE / 'PROVENANCE.json').read_text()).items():
        if sha(HERE.parent / name) != expected:
            raise ValueError('preserved input drift: ' + name)
    old = HERE.parent / 'preparation-376414'
    selected = json.loads((HERE / 'SELECTION.json').read_text())
    previous = json.loads((old / 'SELECTION.json').read_text())
    built = json.loads((old / 'BUILD-RECEIPT/state.json').read_text())
    if built['status'] != 'candidate-built' or built['image'] != selected['image'] or (old / 'BUILD-RECEIPT/image.id').read_text().strip() != selected['image']:
        raise ValueError('built image provenance mismatch')
    for name in ('image', 'uid', 'gid', 'layout_sha256', 'payload_sha256'):
        if selected[name] != previous[name]:
            raise ValueError('unselected diagnostic change: ' + name)
    if selected['proof_id'] != 'w325695-proof-377003':
        raise ValueError('successor identity mismatch')
    module = runner()
    module.validate(selected, (HERE / 'LAYOUT.json').read_bytes(), (HERE / 'kernel-payload.py').read_bytes(), (HERE / 'engine-proof.py').read_bytes())
    if os.path.lexists(HERE / 'ENGINE-RECEIPT'):
        raise ValueError('successor receipt already used; no retry')
    return {'packet_sha256': sha(HERE / 'PACKET-PINS.json'), 'selection_sha256': sha(HERE / 'SELECTION.json'), 'engine_invoked': False, 'receipt_unused': True}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('check', 'run'))
    parser.add_argument('--owner-selected', action='store_true')
    parser.add_argument('--selection-sha256')
    args = parser.parse_args(argv)
    result = check()
    if args.action == 'check':
        print(json.dumps(result, sort_keys=True))
        return 0
    if not args.owner_selected or args.selection_sha256 != result['selection_sha256']:
        parser.error('later exact owner selection and matching selection digest required')
    selection = json.loads((HERE / 'SELECTION.json').read_text())
    # Proof reserves the fresh receipt atomically before the first engine call.
    proof = runner().Proof(selection, json.loads((HERE / 'LAYOUT.json').read_text()), (HERE / 'kernel-payload.py').read_text(), HERE / 'ENGINE-RECEIPT')
    return 0 if proof.execute()['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
