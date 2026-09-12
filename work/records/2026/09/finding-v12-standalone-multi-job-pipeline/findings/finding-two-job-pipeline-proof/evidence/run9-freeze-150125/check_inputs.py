"""Recheck actual run9 rendered inputs; no host prepare/provision/model operation.

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
PREPARED = REC / 'prepared-150007'
IMAGE_PREPARED = REC / 'prepared-149053'
sys.dont_write_bytecode = True
sys.path[:0] = [str(PREPARED), str(REPO / 'v12/python/src'), str(REPO / 'v12/python')]
import deployment


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


EVIDENCE = REC / 'evidence/run9-freeze-150125'


def check_images():
    """Bind owner-generated static reports; current direct reads are independent metadata."""
    build = json.loads((IMAGE_PREPARED / 'image-build/result.json').read_text())
    images = json.loads((IMAGE_PREPARED / 'candidate-images.json').read_text())
    expected_images = {'provider': 'sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13',
                       'integration': 'sha256:d739fefe6bf885db8ad79122611316f3fbe8b393fa4c821933388e8cd15e2533'}
    assert images == build['images'] == expected_images
    assert build['complete'] is True and build['selected'] is False
    assert build['base'] == deployment.PROVIDER_BASE
    context = json.loads((IMAGE_PREPARED / 'image-context-manifest.json').read_text())
    installation = json.loads((IMAGE_PREPARED / 'provider-installation.json').read_text())
    base = json.loads((IMAGE_PREPARED / 'image-build/base.inspect.json').read_text())
    assert base['Id'] == deployment.PROVIDER_BASE
    current = {row['Id']: row for row in json.loads((EVIDENCE / 'current-images.json').read_text())}
    containers = {row['Id']: row for row in map(json.loads, (EVIDENCE / 'current-containers.jsonl').read_text().splitlines())}
    expected_commands = [['docker', 'image', 'inspect', deployment.PROVIDER_BASE]]
    result = {}
    for kind in ('provider', 'integration'):
        image = images[kind]
        recipe = IMAGE_PREPARED / 'image-context' / ('Dockerfile.provider' if kind == 'provider' else 'worker/Dockerfile.integration')
        command = ['docker', 'build', '--pull=false', '--no-cache', '--network', 'none', '--platform', 'linux/amd64', '--iidfile', str(IMAGE_PREPARED / 'image-build' / (kind + '.iid')), '--tag', 'baton-w71879-' + kind + ':candidate-149053', '--file', str(recipe)]
        if kind == 'integration': command += ['--build-arg', 'PROVIDER_BASE=' + deployment.PROVIDER_BASE]
        command += [str(IMAGE_PREPARED / 'image-context')]
        expected_commands += [command, ['docker', 'image', 'inspect', image], ['docker', 'create', '--name', 'w71879-check-' + kind + '-149053', '--network', 'none', '--read-only', '--entrypoint', '/bin/true', image]]
        assert (IMAGE_PREPARED / 'image-build' / (kind + '.iid')).read_text().strip() == image
        facts = json.loads((IMAGE_PREPARED / 'image-build' / (kind + '.inspect.json')).read_text())
        for key in ('Id', 'Created', 'Architecture', 'Os', 'Config', 'RootFS', 'Size'):
            assert facts[key] == current[image][key], (kind, key)
        assert facts['Id'] == image and facts['Os'] == 'linux' and facts['Architecture'] == 'amd64'
        assert facts['Config']['User'] == '65532:65532'
        assert facts['Config']['Entrypoint'] == ['python3', '/opt/baton/' + ('dogfood_entry.py' if kind == 'provider' else 'integration_entry.py')]
        assert facts['RootFS']['Layers'][:len(base['RootFS']['Layers'])] == base['RootFS']['Layers']
        assert not any(value.startswith(('ANTHROPIC_', 'CLAUDE_CODE_OAUTH_TOKEN=')) for value in facts['Config'].get('Env', []))
        expected = {}
        for name, record in context.items():
            if name.endswith('Dockerfile.integration') or (kind == 'provider' and '/integration_' in name) or (kind == 'integration' and name.endswith('/dogfood_entry.py')): continue
            target = ('/opt/baton/source_profiles/' if '/source_profiles/' in name else '/opt/baton/') + Path(name).name
            expected[target] = dict(record, mode=stat.S_IMODE((IMAGE_PREPARED / 'image-context' / name).stat().st_mode))
        expected.update({path: {key: record[key] for key in ('sha256', 'bytes', 'mode')} for path, record in installation['files'].items()})
        expected['/usr/local/bin/claude'] = {'linkname': '../lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe', 'target': '/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe'}
        assert build['content_checks'][kind] == expected
        container = build['inspection_containers'][kind]
        for target in expected: expected_commands.append(['docker', 'cp', container + ':' + target, '-'])
        expected_commands.append(['docker', 'inspect', container])
        held = json.loads((IMAGE_PREPARED / 'image-build' / (kind + '.container.inspect.json')).read_text())
        live = containers[container]
        assert held['Id'] == live['Id'] == container and held['Image'] == live['Image'] == image
        assert held['State'] == live['State'] and live['State']['Status'] == 'created' and not live['State']['Running']
        assert live['State']['StartedAt'] == '0001-01-01T00:00:00Z' and live['State']['Pid'] == 0
        assert held['HostConfig']['ReadonlyRootfs'] is live['readonly'] is True
        assert held['HostConfig']['NetworkMode'] == live['network'] == 'none'
        assert held['Mounts'] == live['mounts'] == []
        result[kind] = {'id': image, 'static_files_and_launcher': len(expected), 'inspection_container': container, 'still_never_started': True}
    assert [row['argv'] for row in build['commands']] == expected_commands
    assert all(row['returncode'] == 0 for row in build['commands'])
    result['exact_successful_commands'] = len(expected_commands)
    result['host_build_and_static_inspection_seconds'] = build['wall_seconds']
    result['scope'] = 'Content from owner-executed accepted helper; direct current metadata independently matches. No static copy repeated, no provider execution.'
    helpers = json.loads((PREPARED / 'runner-helpers.json').read_text())
    assert set(helpers) == {'run.py', 'deployment.py', 'target_posture.py', 'failure_observation.py'}
    for name, expected in helpers.items(): assert sha(PREPARED / name) == expected
    result['four_helpers'] = helpers
    return result


def check():
    started = time.monotonic()
    retained = Path(tempfile.mkdtemp(prefix='w71879-150125-documents-'))
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
    assert matched['stage-execution.json'] == 'sha256:381654827ce6eb290e31c21694837e8cf10c56d6d4d9641e92df2467cb0fdc87'
    assert matched['submission.json'] == 'sha256:a4870e29847dcb18774e5d2136e8d4ccb606da11c32c0e5ac7fef056491e4fe9'
    assert matched['integration-instructions.txt'] == 'sha256:4b3160e825f6d4f166fc5fc8477f8d85f3190420ba402dcfb780f01df7be9f76'
    assert json.loads((actual / 'authority-provisioning.json').read_text()) == facts
    held_validation = Path(validation['temporary_path_retained'])
    for key, name in (('configuration', 'stage-execution.json'), ('submission', 'submission.json')):
        assert sha(held_validation / name) == validation['documents'][key]
    verified = []
    source_manifest = json.loads((REC / 'prepared-146897/evidence/provenance.json').read_text())
    manifest = REC / 'evidence/run9-preparation-150007/candidate-manifest.json'
    assert sha(manifest) == 'sha256:7c5ad3aeb64f845cc083ab9f25c6b857840f845f257b8591b8ac6ffb4f76f260'
    given = json.loads(manifest.read_text())
    for name, info in given['files'].items():
        path = REPO / name
        assert path.is_file() and not path.is_symlink(), name
        assert sha(path) == info['sha256'] and path.stat().st_size == info['bytes'], name
        assert oct(stat.S_IMODE(path.stat().st_mode)) == info['mode'], name
    verified.append({'path': str(manifest.relative_to(REPO)), 'sha256': sha(manifest), 'files': len(given['files'])})
    # Reuse accepted correction custody, including explicit source/test deltas
    # against the original provider bases and unchanged old989 files/markers.
    import importlib.util
    spec = importlib.util.spec_from_file_location('accepted_custody', REC / 'evidence/observation-correction-149854/verify_provenance.py')
    custody = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custody)
    previous = custody.verify()
    image_checks = check_images()
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
        assert not (PREPARED / name).exists() and not (PREPARED / name).is_symlink(), name
    return {'work': 'W71879', 'claim': 150125, 'retained_reconstruction': str(retained),
            'scope': 'Actual host output comparison and read-only baseline/provenance. Not host UID/GID posture, model execution or terminal proof.',
            'actual_documents': matched, 'prior_manifests_verified': verified, 'accepted_correction_custody': previous,
            'provider_entries_verified': len(source_manifest['provider_chain']), 'source_requirements_verified': len(source_manifest['source_requirements']),
            'observation_sources_verified': len(source_manifest['current_observation_sources']),
            'image_checks': image_checks, 'baseline': baseline, 'integration_workspace_bare': True, 'run9_unprovisioned_names_absent': list(absent),
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
