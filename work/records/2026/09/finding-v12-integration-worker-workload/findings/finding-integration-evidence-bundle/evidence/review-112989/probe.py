"""Independent correction probes; all fixtures are disposable, no Git writes."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest import mock

REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.tools import test_integration_bundle as fixtures
producer, contract = fixtures.producer, fixtures.contract
from baton_v12.contracts import digest, ContractRefusal

old = HERE.parent / 'review-112857'
baseline = json.loads((old / 'probe.json').read_text())['candidate']
report = {'claim': 112989, 'candidate': {}, 'historical_candidates_preserved': True, 'probes': {}}
for name, expected in baseline.items():
    assert hashlib.sha256((old / 'candidate' / name).read_bytes()).hexdigest() == expected
    raw = (REPO / name).read_bytes()
    report['candidate'][name] = hashlib.sha256(raw).hexdigest()
    target = HERE / 'candidate' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)

case = fixtures.ReadBackCase()
case.setUp()
try:
    envelope = case.build()
    alias = Path(case.root) / 'alias'
    alias.symlink_to(case.place, target_is_directory=True)
    try:
        contract.read_bundle(str(alias))
    except contract.BundleRefusal:
        direct_refuses = True
    else:
        direct_refuses = False
    accepted = contract.read_bundle(str(alias) + '/.')
    assert accepted['envelope'] == envelope
    container = Path(case.root) / 'linked-parent'
    container.symlink_to(case.root, target_is_directory=True)
    accepted = contract.read_bundle(str(container / 'bundle'))
    assert accepted['envelope'] == envelope
    contract.bundle_blob(str(alias) + '/.', envelope['paths'][0]['candidate'])
    report['probes']['root_traversal'] = {'direct_root_link_refuses': direct_refuses, 'root_link_with_dot_accepted': True, 'ancestor_link_accepted': True, 'blob_root_with_dot_accepted': True}
finally:
    case.doCleanups()

# Scale only the configurable byte ceiling to8 to show the identical boundary
# at5 unique bytes referenced twice, without allocating a64MiB fixture.
with tempfile.TemporaryDirectory(prefix='w112630-shared-blob-') as temporary:
    objects = fixtures.Objects(str(Path(temporary) / 'objects-store'), temporary)
    objects.revision(fixtures.BASE, fixtures.BASE_TREE)
    objects.revision(fixtures.HEAD, fixtures.HEAD_TREE)
    objects.tree(fixtures.BASE_TREE, {})
    objects.tree(fixtures.HEAD_TREE, {'a': ('100644', b'12345'), 'b': ('100644', b'12345')})
    evidence = fixtures.evidence(paths=['a', 'b'], path_set_digest=digest(['a', 'b']))
    table = producer.reviewed_path_table(objects, temporary, evidence)
    assert table['total_bytes'] == 5 and len(table['blobs']) == 1
    with mock.patch.object(producer, 'MAX_BLOB_BYTES', 8), mock.patch.object(contract, 'MAX_BLOB_BYTES', 8):
        contract._paths(table['paths'])
        try:
            producer.reviewed_path_table(objects, temporary, evidence)
        except ContractRefusal as error:
            reason = str(error)
        else:
            raise AssertionError('expected duplicate-content budget refusal')
    report['probes']['shared_blob_budget'] = {'scaled_limit': 8, 'unique_bytes': 5, 'side_reference_bytes': 10, 'reader_accepts': True, 'producer_refuses': reason}

# Characterize the declared detection-only source boundary without alleging
# a production attack: a temporary substitution restored before revalidation.
case = fixtures.ProducerCase()
case.setUp()
try:
    line = Path(case.line['line_path'])
    before = (line.stat().st_dev, line.stat().st_ino)
    changed = False
    def transient(argv):
        global changed
        if not changed:
            parked = Path(str(line) + '-parked')
            line.rename(parked)
            line.mkdir()
            replacement = (line.stat().st_dev, line.stat().st_ino)
            assert replacement != before
            answer = case.objects(argv)
            line.rename(str(line) + '-replacement')
            parked.rename(line)
            changed = True
            return answer
        return case.objects(argv)
    answer = case.compose(runner=transient)
    assert (line.stat().st_dev, line.stat().st_ino) == before
    contract.read_bundle(answer['root'])
    report['probes']['transient_source_swap'] = {'published': True, 'same_identity_before_after': True, 'scope': 'deterministic pathname-runner seam; no real Git or incorrect content claim'}
finally:
    case.doCleanups()

def methods(raw):
    tree = ast.parse(raw)
    return {c.name + '.' + f.name: ast.dump(f, include_attributes=False) for c in tree.body if isinstance(c, ast.ClassDef) for f in c.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')}
testpath = 'v12/python/tests/tools/test_integration_bundle.py'
before = methods((old / 'candidate' / testpath).read_text())
after = methods((REPO / testpath).read_text())
report['test_methods'] = {'prior': len(before), 'current': len(after), 'removed': sorted(before.keys() - after.keys()), 'changed_existing': sorted(k for k in before.keys() & after.keys() if before[k] != after[k]), 'added': sorted(after.keys() - before.keys())}
with (HERE / 'probe.json').open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report, indent=2))
