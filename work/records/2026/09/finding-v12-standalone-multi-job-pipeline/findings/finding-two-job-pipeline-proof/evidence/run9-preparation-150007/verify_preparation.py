"""Read-only preparation custody; fixture configuration is explicitly offline."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
REPO = Path('/home/sl/src/baton')
REC = REPO / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
EVIDENCE = REC / 'evidence/run9-preparation-150007'
PREPARED = REC / 'prepared-150007'
PRIOR = REC / 'prepared-149854'


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    began = time.monotonic()
    manifest = REC / 'evidence/observation-correction-149854/candidate-manifest.json'
    assert sha(manifest) == 'sha256:f39eedf82d8b87c238bddca481c0aceb8c32f8966d4f71d588ae54eb1d57ca21'
    bindings = json.loads(manifest.read_text())['files']
    for name, record in bindings.items():
        path = REPO / name
        assert path.is_file() and not path.is_symlink(), name
        assert sha(path) == record['sha256'] and path.stat().st_size == record['bytes'], name
        assert oct(stat.S_IMODE(path.stat().st_mode)) == record['mode'], name
    spec = importlib.util.spec_from_file_location('accepted_custody', REC / 'evidence/observation-correction-149854/verify_provenance.py')
    custody = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custody)
    previous = custody.verify()
    # The accepted correction verifier explicitly preserves old bases and current
    # accepted source/test bytes, all989 historical inputs, and genuine markers.
    images = json.loads((PREPARED / 'candidate-images.json').read_text())
    assert images == json.loads((PRIOR / 'candidate-images.json').read_text())
    observed = {row['Id']: row for row in map(json.loads, (EVIDENCE / 'current-images.jsonl').read_text().splitlines())}
    for kind, image in images.items():
        row = observed[image]
        assert row['Os'] == 'linux' and row['Architecture'] == 'amd64'
        assert row['Config']['User'] == '65532:65532'
        entry = 'dogfood_entry.py' if kind == 'provider' else 'integration_entry.py'
        assert row['Config']['Entrypoint'] == ['python3', '/opt/baton/' + entry]
    helpers = json.loads((PREPARED / 'runner-helpers.json').read_text())
    assert set(helpers) == {'run.py', 'deployment.py', 'target_posture.py', 'failure_observation.py'}
    for name, digest in helpers.items():
        assert sha(PREPARED / name) == digest
    assert (PREPARED / 'run.py').read_text() == (PRIOR / 'run.py').read_text().replace('w71879-run8', 'w71879-run9')
    for name in ('target_posture.py', 'failure_observation.py', 'test_stats_observation.py', 'test_provider_detail.py', 'test_command_errors.py', 'test_image_preparation.py'):
        assert (PREPARED / name).read_bytes() == (PRIOR / name).read_bytes()
    fixture = Path('/tmp/w71879-150007-public-bootstrap-k_dvm895/documents')
    workers = {}
    for path in (fixture / 'workers').glob('*.json'):
        document = json.loads(path.read_text())
        assert document['credential_sources'] == '/home/sl/.baton/credential-sources.json'
        assert document['credential_slots'] == ['claude']
        assert document['credential_profile'] == {'claude': {'provider': 'operator-file', 'reference': 'w64268-run1'}}
        assert Path(document['credential_home']).name == path.stem
        assert document['authority_uuid'] == 'c71879b3000000000000000000000001'
        workers[path.stem] = {key: document[key] for key in ('credential_sources', 'credential_slots', 'credential_profile', 'credential_home')}
    assert len(workers) == 8 and len({d['credential_home'] for d in workers.values()}) == 8
    source = '/home/sl/.local/state/baton/v12/w71879-run1/source'
    def git(*args):
        result = subprocess.run(['git', '--no-optional-locks', '-C', source, *args], capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip()
    assert git('show', '--no-patch', '--format=%H %T', 'HEAD') == '2fbb2d456638e5706218020aebfa47f0a82c8920 3492ba64448ab9d39bde53ee6456ce24e74ece2c'
    assert git('symbolic-ref', '--short', 'HEAD') == 'main'
    assert not git('status', '--porcelain')
    root = Path('/home/sl/.local/state/baton/v12/w71879-run9')
    assert not root.exists() and not root.is_symlink()
    for name in ('validation.json', 'frozen-config', 'selected-images.json', 'execution-review.json', 'image-build'):
        assert not (PREPARED / name).exists() and not (PREPARED / name).is_symlink(), name
    changes = [str(path.relative_to(PREPARED)) for path in PREPARED.rglob('*') if path.is_file() and (PRIOR / path.relative_to(PREPARED)).is_file() and path.read_bytes() != (PRIOR / path.relative_to(PREPARED)).read_bytes()]
    return {'accepted_candidate_files_verified': len(bindings), 'accepted_candidate_manifest': sha(manifest),
            'prior_custody': previous, 'images': images, 'four_helpers': helpers, 'changed_copies': sorted(changes),
            'offline_worker_configurations': workers, 'credential_scope': 'Synthetic generated deployment documents only; no credential payload, registry contents, delivery or authentication read/probe.',
            'original_source_clean': True, 'fresh_run9_absent': True, 'actual_inputs_and_markers_absent': True,
            'verification_seconds': time.monotonic() - began}


if __name__ == '__main__':
    result = verify()
    retained = Path(tempfile.mkdtemp(prefix='w71879-150007-provenance-'))
    (retained / 'provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'retained': str(retained), 'seconds': result['verification_seconds']}, indent=2))
