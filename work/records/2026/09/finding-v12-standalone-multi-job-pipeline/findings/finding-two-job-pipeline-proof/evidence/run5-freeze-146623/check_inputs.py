"""Recheck actual run5 rendered inputs; no host prepare/provision/model operation.

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
PREPARED = REC / 'prepared-146538'
sys.dont_write_bytecode = True
sys.path[:0] = [str(PREPARED), str(REPO / 'v12/python/src'), str(REPO / 'v12/python')]
import deployment


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    started = time.monotonic()
    retained = Path(tempfile.mkdtemp(prefix='w71879-146623-documents-'))
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
    assert matched['integration-instructions.txt'] == 'sha256:599b5612c1d3c1062f9184f233ec2f58cccd4fd2f728b1c176727513700f6379'
    assert json.loads((actual / 'authority-provisioning.json').read_text()) == facts
    held_validation = Path(validation['temporary_path_retained'])
    for key, name in (('configuration', 'stage-execution.json'), ('submission', 'submission.json')):
        assert sha(held_validation / name) == validation['documents'][key]
    verified = []
    source_manifest = None
    for manifest in (PREPARED / 'candidate-manifest.json', REC / 'prepared-145615/candidate-manifest.json', REC / 'evidence/run4-freeze-145461/candidate-manifest.json'):
        given = json.loads(manifest.read_text())
        for name, info in given['files'].items():
            path = REPO / name
            assert path.is_file() and not path.is_symlink(), name
            assert sha(path) == info['sha256'] and path.stat().st_size == info['bytes'], name
            assert oct(stat.S_IMODE(path.stat().st_mode)) == info['mode'], name
        verified.append({'path': str(manifest.relative_to(REPO)), 'sha256': sha(manifest), 'files': len(given['files'])})
        if source_manifest is None:
            source_manifest = given
    for name, info in source_manifest['provider_chain'].items():
        path = REPO / name
        if 'sha256' in info:
            assert sha(path).removeprefix('sha256:') == info['sha256'], name
        else:
            assert not path.exists(), name
    for name, info in source_manifest['source_requirements'].items():
        expected = info['sha256'] if isinstance(info, dict) else info
        assert sha(REPO / name).removeprefix('sha256:') == expected.removeprefix('sha256:'), name
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
    return {'work': 'W71879', 'claim': 146623, 'retained_reconstruction': str(retained),
            'scope': 'Actual host output comparison and read-only baseline/provenance. Not host UID/GID posture, model execution or terminal proof.',
            'actual_documents': matched, 'prior_manifests_verified': verified,
            'provider_entries_verified': len(source_manifest['provider_chain']), 'source_requirements_verified': len(source_manifest['source_requirements']),
            'baseline': baseline, 'integration_workspace_bare': True, 'run5_unprovisioned_names_absent': list(absent),
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
