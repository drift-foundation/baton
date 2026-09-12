"""Recheck actual run7 rendered inputs; no host prepare/provision/model operation.

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
PREPARED = REC / 'prepared-149053'
sys.dont_write_bytecode = True
sys.path[:0] = [str(PREPARED), str(REPO / 'v12/python/src'), str(REPO / 'v12/python')]
import deployment


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


EVIDENCE = REC / 'evidence/run7-freeze-149249'


def check_images():
    """Bind owner-generated static reports; current direct reads are independent metadata."""
    build = json.loads((PREPARED / 'image-build/result.json').read_text())
    images = json.loads((PREPARED / 'candidate-images.json').read_text())
    expected_images = {'provider': 'sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13',
                       'integration': 'sha256:d739fefe6bf885db8ad79122611316f3fbe8b393fa4c821933388e8cd15e2533'}
    assert images == build['images'] == expected_images
    assert build['complete'] is True and build['selected'] is False
    assert build['base'] == deployment.PROVIDER_BASE
    context = json.loads((PREPARED / 'image-context-manifest.json').read_text())
    installation = json.loads((PREPARED / 'provider-installation.json').read_text())
    base = json.loads((PREPARED / 'image-build/base.inspect.json').read_text())
    assert base['Id'] == deployment.PROVIDER_BASE
    current = {row['Id']: row for row in json.loads((EVIDENCE / 'current-images.json').read_text())}
    containers = {row['Id']: row for row in map(json.loads, (EVIDENCE / 'current-containers.jsonl').read_text().splitlines())}
    expected_commands = [['docker', 'image', 'inspect', deployment.PROVIDER_BASE]]
    result = {}
    for kind in ('provider', 'integration'):
        image = images[kind]
        recipe = PREPARED / 'image-context' / ('Dockerfile.provider' if kind == 'provider' else 'worker/Dockerfile.integration')
        command = ['docker', 'build', '--pull=false', '--no-cache', '--network', 'none', '--platform', 'linux/amd64', '--iidfile', str(PREPARED / 'image-build' / (kind + '.iid')), '--tag', 'baton-w71879-' + kind + ':candidate-149053', '--file', str(recipe)]
        if kind == 'integration': command += ['--build-arg', 'PROVIDER_BASE=' + deployment.PROVIDER_BASE]
        command += [str(PREPARED / 'image-context')]
        expected_commands += [command, ['docker', 'image', 'inspect', image], ['docker', 'create', '--name', 'w71879-check-' + kind + '-149053', '--network', 'none', '--read-only', '--entrypoint', '/bin/true', image]]
        assert (PREPARED / 'image-build' / (kind + '.iid')).read_text().strip() == image
        facts = json.loads((PREPARED / 'image-build' / (kind + '.inspect.json')).read_text())
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
            expected[target] = dict(record, mode=stat.S_IMODE((PREPARED / 'image-context' / name).stat().st_mode))
        expected.update({path: {key: record[key] for key in ('sha256', 'bytes', 'mode')} for path, record in installation['files'].items()})
        expected['/usr/local/bin/claude'] = {'linkname': '../lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe', 'target': '/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe'}
        assert build['content_checks'][kind] == expected
        container = build['inspection_containers'][kind]
        for target in expected: expected_commands.append(['docker', 'cp', container + ':' + target, '-'])
        expected_commands.append(['docker', 'inspect', container])
        held = json.loads((PREPARED / 'image-build' / (kind + '.container.inspect.json')).read_text())
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
    retained = Path(tempfile.mkdtemp(prefix='w71879-149249-documents-'))
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
    source_manifest = json.loads((REC / 'prepared-146897/evidence/provenance.json').read_text())
    for relative, expected_manifest in (
        ('evidence/image-preparation-149053/candidate-manifest.json', 'sha256:fa2f9526995166f66c195704b71bfb4504c3713d6820362565641b88246c9037'),
        ('evidence/diagnostic-148870/candidate-manifest.json', 'sha256:0c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f'),
        ('prepared-147109/candidate-manifest.json', 'sha256:94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2'),
        ('evidence/run6-freeze-146988/candidate-manifest.json', 'sha256:87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9')):
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
    return {'work': 'W71879', 'claim': 149249, 'retained_reconstruction': str(retained),
            'scope': 'Actual host output comparison and read-only baseline/provenance. Not host UID/GID posture, model execution or terminal proof.',
            'actual_documents': matched, 'prior_manifests_verified': verified,
            'provider_entries_verified': len(source_manifest['provider_chain']), 'source_requirements_verified': len(source_manifest['source_requirements']),
            'observation_sources_verified': len(source_manifest['current_observation_sources']),
            'image_checks': image_checks, 'baseline': baseline, 'integration_workspace_bare': True, 'run7_unprovisioned_names_absent': list(absent),
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
