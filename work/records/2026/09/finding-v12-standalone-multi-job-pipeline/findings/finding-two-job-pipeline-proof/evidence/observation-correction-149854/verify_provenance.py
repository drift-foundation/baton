"""Bounded static custody checks; accepted source changes compare to retained bases."""
import ast
import hashlib
import json
from pathlib import Path
import stat
import time
import tempfile

REPO = Path('/home/sl/src/baton')
REC = REPO / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
EVIDENCE = REC / 'evidence/observation-correction-149854'
PREPARED = REC / 'prepared-149854'
PRIOR = REC / 'prepared-149488'
CHANGED = ('v12/python/tools/stage_execution.py', 'v12/python/tests/tools/test_stage_execution.py')


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def methods(path):
    tree = ast.parse(path.read_text())
    return {c.name + '.' + f.name: ast.dump(f, include_attributes=False)
            for c in tree.body if isinstance(c, ast.ClassDef)
            for f in c.body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))}


def verify():
    started = time.monotonic()
    manifest = REC / 'evidence/run8-freeze-149637/candidate-manifest.json'
    assert sha(manifest) == 'sha256:81747c62cd9863f9c0899e1292d80fc82b1757501caa7628e6286b933ba1dd81'
    given = json.loads(manifest.read_text())
    changed_manifest_paths = []
    for name, record in given['files'].items():
        path = REPO / name
        assert path.is_file() and not path.is_symlink(), name
        assert oct(stat.S_IMODE(path.stat().st_mode)) == record['mode'], name
        if name in CHANGED:
            assert sha(EVIDENCE / ('base-' + path.name)) == record['sha256'], name
            changed_manifest_paths.append(name)
        else:
            assert sha(path) == record['sha256'] and path.stat().st_size == record['bytes'], name
    markers = {n: sha(PRIOR / n) for n in ('selected-images.json', 'execution-review.json')}
    assert markers == {'selected-images.json': 'sha256:d0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f',
                       'execution-review.json': 'sha256:dc3f225a30c91e30ca50a30659bc840287992708d385f36b4721e0d0f0e297c3'}
    prior = json.loads((REC / 'prepared-146897/evidence/provenance.json').read_text())
    bindings = {}
    for group in ('provider_chain', 'source_requirements', 'current_observation_sources'):
        checked = []
        for name, record in prior[group].items():
            expected = record.get('sha256') if isinstance(record, dict) else record
            path = REPO / name
            if expected:
                if name in CHANGED:
                    assert sha(EVIDENCE / ('base-' + path.name)).removeprefix('sha256:') == expected.removeprefix('sha256:'), name
                    checked.append({'path': name, 'accepted_base': expected, 'current': sha(path), 'authority': 'owner149847'})
                else:
                    assert sha(path).removeprefix('sha256:') == expected.removeprefix('sha256:'), name
                    checked.append(name)
            else:
                assert not path.exists(), name
                checked.append(name)
        bindings[group] = checked
    old = methods(EVIDENCE / 'base-test_stage_execution.py')
    new = methods(REPO / CHANGED[1])
    for name, body in old.items():
        assert new[name] == body, name
    added = sorted(set(new) - set(old))
    assert added == ['TwoBoundJobsTraverseServingAndCorrection.test_readonly_integration_observation_keeps_the_bound_job']
    changes = []
    for path in PREPARED.rglob('*'):
        relative = path.relative_to(PREPARED)
        before = PRIOR / relative
        if path.is_file() and before.exists() and path.read_bytes() != before.read_bytes():
            changes.append(str(relative))
    assert set(changes) <= {'README.md', 'run.py', 'runner-helpers.json', 'test_run8_preparation.py'}, changes
    helpers = json.loads((PREPARED / 'runner-helpers.json').read_text())
    assert set(helpers) == {'run.py', 'deployment.py', 'failure_observation.py', 'target_posture.py'}
    for name, digest in helpers.items():
        assert sha(PREPARED / name) == digest
    return {'old_manifest': sha(manifest), 'manifest_bindings_checked': len(given['files']),
            'authorized_changed_manifest_paths': changed_manifest_paths, 'old_run8_markers': markers,
            'source_bindings': bindings, 'unchanged_product_test_methods': len(old), 'added_product_test_methods': added,
            'successor_changes': changes, 'four_helpers': helpers, 'source_and_test': {n: sha(REPO / n) for n in CHANGED},
            'verification_seconds': time.monotonic() - started}


if __name__ == '__main__':
    result = verify()
    retained = Path(tempfile.mkdtemp(prefix='w71879-149854-provenance-'))
    (retained / 'provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'retained': str(retained), 'seconds': result['verification_seconds']}, indent=2))
