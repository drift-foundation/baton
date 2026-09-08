"""Independent disposable boundary probes. Never opens the Baton ledger."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest import mock

REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.tools import test_integration_bundle as fixtures
producer, contract = fixtures.producer, fixtures.contract
from baton_v12.contracts import digest, ContractRefusal

paths = ['v12/worker/integration_contract.py', 'v12/python/tools/integration_bundle.py', 'v12/python/tests/tools/test_integration_bundle.py', 'v12/python/tools/parallel_test.py']
hashes = {}
for name in paths:
    raw = (REPO / name).read_bytes()
    hashes[name] = hashlib.sha256(raw).hexdigest()
    p = HERE / 'candidate' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)
report = {'candidate': hashes, 'probes': {}}

# Both public readers accept symlinked ancestors with unchanged valid bytes.
case = fixtures.ReadBackCase()
case.setUp()
try:
    envelope = case.build()
    original = Path(case.place) / 'evidence'
    outside = Path(case.root) / 'outside-evidence'
    original.rename(outside)
    original.symlink_to(outside, target_is_directory=True)
    result = contract.read_bundle(case.place)
    assert result['envelope'] == envelope
    blobdir = Path(case.place) / 'blobs'
    outside_blobs = Path(case.root) / 'outside-blobs'
    blobdir.rename(outside_blobs)
    blobdir.symlink_to(outside_blobs, target_is_directory=True)
    content = contract.bundle_blob(case.place, envelope['paths'][0]['candidate'])
    alias = Path(case.root) / 'bundle-alias'
    alias.symlink_to(case.place, target_is_directory=True)
    contract.read_bundle(str(alias))
    report['probes']['intermediate_links'] = {'evidence_directory_accepted': True, 'blob_directory_accepted': True, 'root_link_accepted': True, 'blob_bytes': len(content)}
finally:
    case.doCleanups()

# A real admitted owner world, with a source-directory replacement injected
# by the permitted deterministic Git runner after initial nomination.
case = fixtures.ProducerCase()
case.setUp()
try:
    line = Path(case.line['line_path'])
    before = (line.stat().st_dev, line.stat().st_ino)
    changed = False
    def replacement(argv):
        global changed
        if not changed:
            line.rename(str(line) + '-before-review-race')
            line.mkdir()
            changed = True
        return case.objects(argv)
    answer = case.compose(runner=replacement)
    after = (line.stat().st_dev, line.stat().st_ino)
    assert before != after
    contract.read_bundle(answer['root'])
    report['probes']['line_replaced_during_extraction'] = {'initial_identity': before, 'replacement_identity': after, 'published': True, 'consumer_accepted': True}
finally:
    case.doCleanups()

# Structural size fixture: seed from real accepted owners, then replace ONLY
# the accepted-evidence projection with an internally matching 252-edit table.
# This tests publication bounds, not acceptance of a genuine 252-path proposal.
# The real path-table builder, byte runner, serialization and publication run.
case = fixtures.ProducerCase()
case.setUp()
try:
    resolved = producer._accepted_evidence(case.world.manager, case.world.jobs, case.world.authority_read, line_id=case.world.line_id, proposal_id=case.world.proposal_id, checkpoint_profile=case.checkpoint)
    resolved = copy.deepcopy(resolved)
    names = [f'file-{i:03}.txt' for i in range(252)]
    evidence = resolved['checkpoint']['evidence']
    evidence['paths'] = names
    evidence['path_set_digest'] = digest(names)
    resolved['account']['path_set_digest'] = digest(names)
    resolved['documents']['checkpoint.json']['evidence'] = copy.deepcopy(evidence)
    resolved['documents']['checkpoint.json']['path_set_digest'] = digest(names)
    case.objects.tree(fixtures.BASE_TREE, {name: ('100644', f'before {i}'.encode()) for i, name in enumerate(names)})
    case.objects.tree(evidence['tree'], {name: ('100644', f'after {i}'.encode()) for i, name in enumerate(names)})
    with mock.patch.object(producer, '_accepted_evidence', return_value=resolved):
        try:
            case.compose()
        except ContractRefusal as error:
            failure = str(error)
        else:
            raise AssertionError('expected post-publication manifest bound refusal')
    published = Path(case.destination)
    files = [p for p in published.rglob('*') if p.is_file()]
    contract.read_bundle(str(published))
    assert len(files) == 513
    report['probes']['manifest_limit_after_publication'] = {'paths': 252, 'unique_blobs': 504, 'published_files': len(files), 'failure': failure, 'destination_exists': True, 'consumer_accepted': True}
finally:
    case.doCleanups()

(HERE / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
