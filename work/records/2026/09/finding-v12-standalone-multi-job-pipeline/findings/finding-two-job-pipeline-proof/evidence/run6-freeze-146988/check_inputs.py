"""Recheck actual run6 rendered inputs; no host prepare/provision/model operation.

Only the document output destination is temporary. No mocked validators or RUN
substitution; source nomination uses the actual host-prepared source directory.
Public bootstrap facts come from the retained owner validation report. No store
is opened. Git commands are read-only. Host posture remains operator evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import time

REPO = Path('/home/sl/src/baton')
REC = REPO / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PREPARED = REC / 'prepared-146897'
sys.dont_write_bytecode = True
sys.path[:0] = [str(PREPARED), str(REPO / 'v12/python/src'), str(REPO / 'v12/python')]
import deployment


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    started = time.monotonic()
    retained = Path(tempfile.mkdtemp(prefix='w71879-146988-documents-'))
    (retained / 'OFFLINE-ONLY.txt').write_text('Deterministic reconstruction, not actual frozen host inputs or runtime results.\n')
    destination = retained / 'documents'
    validation = json.loads((PREPARED / 'validation.json').read_text())
    images = json.loads((PREPARED / 'candidate-images.json').read_text())
    facts = validation['public_authority_facts']
    assert facts['authority_uuid'] == deployment.UUID
    deployment.documents(destination, images, facts)
    actual = PREPARED / 'frozen-config'
    expected_names = sorted(str(p.relative_to(destination)) for p in destination.rglob('*') if p.is_file())
    actual_names = sorted(str(p.relative_to(actual)) for p in actual.rglob('*') if p.is_file())
    assert len(actual_names) == 33 and actual_names == expected_names
    matched = {}
    for name in actual_names:
        path = actual / name
        assert path.is_file() and not path.is_symlink(), name
        expected = (destination / name).read_bytes().replace(str(destination).encode(), str(actual).encode())
        assert expected == path.read_bytes(), name
        matched[name] = sha(path)
    assert matched['integration-instructions.txt'] == 'sha256:4b3160e825f6d4f166fc5fc8477f8d85f3190420ba402dcfb780f01df7be9f76'
    assert json.loads((actual / 'authority-provisioning.json').read_text()) == facts
    held_validation = Path(validation['temporary_path_retained'])
    for key, name in (('configuration', 'stage-execution.json'), ('submission', 'submission.json')):
        assert sha(held_validation / name) == validation['documents'][key]
    verified = []
    source_manifest = json.loads((PREPARED / 'evidence/provenance.json').read_text())
    for relative, expected_manifest in (('prepared-146897/candidate-manifest.json', 'sha256:d24b5349ed6a6e35b37fbc933eaa2550fea7233d2483123ba5ad985f3d1f7c37'), ('prepared-146797/candidate-manifest.json', 'sha256:156cb7f53d1eab4e41d1602742ddda778376250b6d1af5e7eee9e12a3c775588'), ('prepared-146538/candidate-manifest.json', 'sha256:bbb5761e087ed5bd61c8371de09346da35f9632f7cbbb203ce16b657cdc5483b'), ('evidence/run5-freeze-146623/candidate-manifest.json', 'sha256:a9ff1b8e38de58a862319c13de4bf1badccc15c28d8b88b74eb7f955d0a9f531')):
        manifest = REC / relative
        assert sha(manifest) == expected_manifest, relative
        given = json.loads(manifest.read_text())
        for name, info in given['files'].items():
            path = REPO / name
            assert path.is_file() and not path.is_symlink(), name
            assert sha(path) == info['sha256'] and path.stat().st_size == info['bytes'], name
            assert oct(stat.S_IMODE(path.stat().st_mode)) == info['mode'], name
        verified.append({'path': str(manifest.relative_to(REPO)), 'sha256': sha(manifest), 'files': len(given['files'])})
    for name, info in source_manifest['provider_chain'].items():
        path = REPO / name
        if 'sha256' in info:
            assert sha(path).removeprefix('sha256:') == info['sha256'], name
        else:
            assert not path.exists(), name
    for name, info in source_manifest['source_requirements'].items():
        expected = info['sha256'] if isinstance(info, dict) else info
        assert sha(REPO / name).removeprefix('sha256:') == expected.removeprefix('sha256:'), name
    for name, expected in source_manifest['current_observation_sources'].items():
        assert sha(REPO / name) == expected, name
    baseline = {}
    for name in ('source', 'target'):
        root = deployment.RUN / name
        identity = deployment.git_read(root, 'show', '--no-patch', '--format=%H %T', 'HEAD')
        status = deployment.git_read(root, 'status', '--porcelain')
        branch = deployment.git_read(root, 'symbolic-ref', '--short', 'HEAD')
        assert identity == deployment.BASE + ' ' + deployment.TREE and not status and branch == 'main'
        count = 0
        for original in (REC / 'prepared-141510/baseline').rglob('*'):
            if original.is_file():
                path = root / original.relative_to(REC / 'prepared-141510/baseline')
                assert not path.is_symlink() and path.read_bytes() == original.read_bytes()
                count += 1
        assert count == 10
        baseline[name] = {'identity': identity, 'branch': branch, 'status': status, 'baseline_files': count}
    assert deployment.git_read(deployment.RUN / 'integration-workspace', 'rev-parse', '--is-bare-repository') == 'true'
    absent = ('authority.sqlite3', 'integration.sqlite3', 'jobs.sqlite3', 'control.sqlite3', 'state', 'storage', 'launch', 'credentials', 'evidence')
    for name in absent:
        assert not (deployment.RUN / name).exists() and not (deployment.RUN / name).is_symlink(), name
    for name in ('execution-review.json', 'selected-images.json'):
        assert not (PREPARED / name).exists(), name
    return {'work': 'W71879', 'claim': 146988, 'retained_reconstruction': str(retained),
            'scope': 'Actual host output comparison and read-only baseline/provenance. Not host UID/GID posture, model execution or terminal proof.',
            'actual_documents': matched, 'prior_manifests_verified': verified,
            'provider_entries_verified': len(source_manifest['provider_chain']), 'source_requirements_verified': len(source_manifest['source_requirements']),
            'observation_sources_verified': len(source_manifest['current_observation_sources']),
            'baseline': baseline, 'integration_workspace_bare': True, 'run6_unprovisioned_names_absent': list(absent),
            'validation_file': sha(PREPARED / 'validation.json'), 'actual_configuration': sha(actual / 'stage-execution.json'),
            'actual_submission': sha(actual / 'submission.json'), 'runtime_profile_digest': deployment.digest(json.loads((actual / 'runtime-profile.json').read_text())),
            'host_validation_seconds': validation['wall_seconds'], 'verification_seconds': time.monotonic() - started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = check()
    output = args.output or Path(report['retained_reconstruction']) / 'verification.json'
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(output), 'documents': len(report['actual_documents']), 'configuration': report['actual_configuration'], 'submission': report['actual_submission'], 'profile': report['runtime_profile_digest'], 'seconds': report['verification_seconds'], 'retained': report['retained_reconstruction']}, indent=2))
