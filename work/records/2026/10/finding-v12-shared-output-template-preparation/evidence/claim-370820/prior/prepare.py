"""W370688 successor composition; no installation, mint, or execution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'v12/justfile').exists())
PREVIOUS = ROOT / 'work/records/2026/10/finding-v12-useful-template-job-monitor'
CHILD = PREVIOUS / 'findings/finding-one-time-capacity-composition'
sys.path[:0] = [str(CHILD), str(ROOT / 'v12/python'), str(ROOT / 'v12/python/src')]
import capacity
from baton_v12.contracts import digest, check_manifest_structure


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(value):
    return json.dumps(value, indent=1, sort_keys=True).encode() + b'\n'


def compose(authority, destination):
    # These accepted inputs are consumed, never regenerated or overwritten.
    pins = {
        PREVIOUS / 'evidence/claim-370050/BINDING.json': '29375db1f141bb4b64b3be38a9429264590d3a3d2a41dd196461d7c977eaf34f',
        CHILD / 'evidence/claim-369373/BINDING.json': '92d9962a71b64b5d25142e22a3b5bd52a374093aa1a352c0c8594b2893765723',
        CHILD / 'capacity.py': '1944c97d6868c12ae19a363cb88f6e50d539adca0f33b328a9eaf4415be7fda6',
        CHILD / 'proposed_grants.py': 'f447fcb62eb665abb5e0bd445392926735c2f3763e4868cbdd8ec8fe76911857',
        CHILD / 'proposed-grants/INVENTORY.json': '6ae52f7b2b796fe1bae8323155513fb8f751e182f4a48a0dffbb577243284add',
    }
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError('historical input drift: ' + str(path.relative_to(ROOT)))
    if destination == capacity.DESTINATION:
        raise ValueError('successor must not target the historical destination')
    old = capacity.compose(authority, destination=destination, proposed_grants=True)
    document = copy.deepcopy(old['document'])
    manifest = document['workers'][0]['deployment']['input_manifest']
    proposal = manifest['outputs'][0]
    assert proposal['name'] == 'proposal' and len(manifest['outputs']) == 1
    proposal['required'] = False
    # Keep the proposal constraints exactly; bounded findings/logs follow the
    # supported shared-role contract, not an unlimited optional-output escape.
    manifest['outputs'].extend({
        'name': name, 'type': 'directory-result', 'path': name, 'required': False,
        'constraints': {'max_bytes': 1048576, 'max_entries': 100,
                        'allowed_media_types': ['application/octet-stream'],
                        'link_policy': 'forbid', 'validator_digest': None}
    } for name in ('findings', 'logs'))
    manifest['record_binding'] = {
        'root': 'baton-repository', 'path': str(HERE.relative_to(ROOT)),
        'finding_digest': 'sha256:' + sha(HERE / 'FINDING.md'),
        'plan_digest': 'sha256:' + sha(HERE / 'PLAN.md')}
    manifest.pop('manifest_digest')
    manifest['manifest_digest'] = digest(manifest)
    check_manifest_structure(manifest, 'inputManifest', what='successor shared manifest')
    for worker in document['workers']:
        worker['deployment']['input_manifest'] = copy.deepcopy(manifest)
    return {
        'schema': 'baton.preparation.shared-output-successor/1',
        'status': 'prepared; not installed or selected for execution',
        'authority_operand': 'must be read back from a separately selected fresh mint; fixture UUIDs are not receipts',
        'document': document, 'document_sha256': hashlib.sha256(render(document)).hexdigest(),
        'task_bytes': old['task_bytes'], 'task_sha256': hashlib.sha256(old['task_bytes'].encode()).hexdigest(),
        'manifest_digest': manifest['manifest_digest'],
        'predecessor_manifest_digest': old['manifest_digest'],
        'historical_pins': {str(p.relative_to(ROOT)): value for p, value in pins.items()},
        'grants': {'change': 'none; consume selected default inventory unchanged',
                   'new_owner_receipt': None, 'inventory': str((CHILD / 'proposed-grants/INVENTORY.json').relative_to(ROOT))},
        'runtime_pins': old['pins_requiring_operator_verification'],
        'source': old['source'],
        'changes': ['shared output union', 'successor record binding', 'new manifest and enclosing document digests'],
        'unchanged': ['task bytes and verification', 'seven policy artifacts and inventory', 'source base', 'image/package provenance', 'per-invocation limits', 'role principals'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authority-uuid', required=True)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    print(render(compose(args.authority_uuid, args.destination)).decode(), end='')
