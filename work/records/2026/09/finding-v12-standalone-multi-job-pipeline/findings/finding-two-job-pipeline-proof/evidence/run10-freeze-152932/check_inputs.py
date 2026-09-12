"""Actual run10 reconstruction and custody; no store, model, host mutation or repair."""
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import time
REPO = Path('/home/sl/src/baton')
REC = REPO / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PREPARED = REC / 'prepared-152826'
IMAGE_PREPARED = REC / 'prepared-149053'
EVIDENCE = REC / 'evidence/run10-freeze-152932'
sys.dont_write_bytecode = True
sys.path[:0] = [str(PREPARED), str(REPO / 'v12/python/src'), str(REPO / 'v12/python')]
import deployment

def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

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
    assert set(helpers) == {'run.py', 'deployment.py', 'target_posture.py', 'failure_observation.py', 'accounting.py'}
    for name, expected in helpers.items(): assert sha(PREPARED / name) == expected
    result['five_helpers'] = helpers
    return result


def check():
    started = time.monotonic()
    retained = Path(tempfile.mkdtemp(prefix='w71879-152932-documents-'))
    (retained / 'OFFLINE-ONLY.txt').write_text('Deterministic reconstruction with actual source nomination; not actual frozen inputs or execution.\n')
    validation = json.loads((PREPARED / 'validation.json').read_text())
    facts = validation['public_authority_facts']
    assert facts['authority_uuid'] == deployment.UUID == 'c71879b4000000000000000000000001'
    assert facts['policy_generation'] == 24
    assert facts['principals'] == {n: 'principal:w71879-run10-' + n for n in deployment.ACTORS}
    images = json.loads((PREPARED / 'candidate-images.json').read_text())
    destination = retained / 'documents'
    deployment.documents(destination, images, facts)
    actual = PREPARED / 'frozen-config'
    assert not actual.is_symlink()
    for q in actual.rglob('*'): assert not q.is_symlink(), q
    names = sorted(str(q.relative_to(actual)) for q in actual.rglob('*') if q.is_file())
    assert len(names) == 33
    assert names == sorted(str(q.relative_to(destination)) for q in destination.rglob('*') if q.is_file())
    matched = {}
    for name in names:
        q = actual / name
        expected = (destination / name).read_bytes().replace(str(destination).encode(), str(actual).encode())
        assert q.read_bytes() == expected, name
        matched[name] = sha(q)
    assert matched['stage-execution.json'] == 'sha256:401f13768132ab7d47650f9afe8bec59068d31d017298c8ace0faf84dcace84e'
    assert matched['submission.json'] == 'sha256:c9ef35157bf768aa09c481cda2fe6aa4b5aaf773ace34154e4db4301907d6e7d'
    assert matched['integration-instructions.txt'] == 'sha256:4b3160e825f6d4f166fc5fc8477f8d85f3190420ba402dcfb780f01df7be9f76'
    assert json.loads((actual / 'authority-provisioning.json').read_text()) == facts
    temporary_validation = Path(validation['temporary_path_retained'])
    for key, name in (('configuration', 'stage-execution.json'), ('submission', 'submission.json')):
        assert sha(temporary_validation / name) == validation['documents'][key]
    config = json.loads((actual / 'stage-execution.json').read_text())
    workers = [w['deployment'] for w in config['workers']] + [w['deployment'] for w in config['result_judgment_workers']['job-b'].values()]
    assert len(workers) == 8
    assert len({w['credential_home'] for w in workers}) == 8
    for worker in workers:
        assert worker['credential_sources'] == deployment.REGISTRY
        assert worker['credential_profile'] == {'claude': deployment.CREDENTIAL}
        assert worker['credential_slots'] == ['claude']
        assert worker['authority_uuid'] == deployment.UUID
        assert worker['workspace_group'] == 1001
    prior = {}
    journals = {REC / n for n in ('FINDING.md', 'PLAN.md', 'PROGRESS.md')}
    for name in ('run10-preparation-152826', 'accounting-152750', 'accounting-152563', 'accounting-150501', 'run9-freeze-150125', 'run9-budget-150384'):
        manifest = REC / 'evidence' / name / 'candidate-manifest.json'
        entries = json.loads(manifest.read_text())['files']; count = 0
        for file, expected in entries.items():
            q = REPO / file
            if q in journals: continue
            assert q.is_file() and not q.is_symlink(), file
            assert sha(q) == expected['sha256'] and q.stat().st_size == expected['bytes'], file
            if 'mode' in expected: assert oct(stat.S_IMODE(q.stat().st_mode)) == expected['mode'], file
            count += 1
        prior[name] = {'non_journal_files': count, 'manifest': sha(manifest)}
    image_checks = check_images()
    baseline = {}
    for name in ('source', 'target'):
        root = deployment.RUN / name
        identity = deployment.git_read(root, 'show', '--no-patch', '--format=%H %T', 'HEAD')
        status = deployment.git_read(root, 'status', '--porcelain')
        branch = deployment.git_read(root, 'symbolic-ref', '--short', 'HEAD')
        assert identity == deployment.BASE + ' ' + deployment.TREE and status == '' and branch == 'main'
        count = 0
        for original in (REC / 'prepared-141510/baseline').rglob('*'):
            if original.is_file():
                q = root / original.relative_to(REC / 'prepared-141510/baseline')
                assert not q.is_symlink() and q.read_bytes() == original.read_bytes()
                count += 1
        assert count == 10
        baseline[name] = {'identity': identity, 'branch': branch, 'status': status, 'payloads': count}
    assert deployment.git_read(deployment.RUN / 'integration-workspace', 'rev-parse', '--is-bare-repository') == 'true'
    posture = {}
    for rel in ('', 'demo', 'tests', 'demo/greeting.py', 'demo/units.py', 'tests/test_greeting.py'):
        q = deployment.RUN / 'target' / rel; held = q.stat()
        mode = stat.S_IMODE(held.st_mode)
        assert mode == (0o2775 if q.is_dir() else 0o644), (rel, oct(mode))
        posture[rel or '.'] = {'mode': oct(mode), 'observed_uid': held.st_uid, 'observed_gid': held.st_gid}
    absent = ('authority.sqlite3', 'integration.sqlite3', 'jobs.sqlite3', 'control.sqlite3', 'state', 'storage', 'launch', 'credentials', 'evidence')
    for name in absent: assert not (deployment.RUN / name).exists() and not (deployment.RUN / name).is_symlink(), name
    for name in ('selected-images.json', 'execution-review.json'): assert not (PREPARED / name).exists() and not (PREPARED / name).is_symlink(), name
    return {'work': 'W71879', 'claim': 152932, 'retained_reconstruction': str(retained), 'actual_documents': matched,
            'scope': 'Physical actual input equality, public schema, read-only source/image/custody. No store/model/credential payload or host mutation.',
            'prior_custody': prior, 'image_checks': image_checks, 'baseline': baseline, 'target_posture': posture,
            'posture_qualification': 'Observed managed IDs are not actual host ownership proof; owner152925 reports reviewed host preparation succeeded.',
            'integration_workspace_bare': True, 'unprovisioned_absent': list(absent), 'fresh_markers_absent': True,
            'validation_file': sha(PREPARED / 'validation.json'), 'host_validation_seconds': validation['wall_seconds'],
            'runtime_profile_digest': deployment.digest(json.loads((actual / 'runtime-profile.json').read_text())),
            'verification_seconds': time.monotonic() - started}

if __name__ == '__main__':
    answer = check()
    with (EVIDENCE / 'post-render.json').open('x') as f: json.dump(answer, f, indent=2); f.write('\n')
    print(json.dumps({k: answer[k] for k in ('retained_reconstruction','verification_seconds','host_validation_seconds','runtime_profile_digest')}, indent=2))
    print('33 actual documents match; six prior manifests and five helpers verify; source/target clean; no provisioning or execution')
