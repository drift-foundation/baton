"""Read available preparation evidence while actual frozen inputs are absent.

Not an actual-input freeze, validator bypass, host preparation or model execution.
"""
import json
from pathlib import Path
import stat
import time

from check_inputs import REPO, REC, PREPARED, EVIDENCE, deployment, sha, check_images


def main():
    started = time.monotonic()
    report = {'work': 'W71879', 'claim': 149249, 'freeze_complete': False}
    report['images'] = check_images()
    verified = []
    for rel, expected in (
        ('evidence/image-preparation-149053/candidate-manifest.json', 'fa2f9526995166f66c195704b71bfb4504c3713d6820362565641b88246c9037'),
        ('evidence/diagnostic-148870/candidate-manifest.json', '0c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f'),
        ('prepared-147109/candidate-manifest.json', '94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2'),
        ('evidence/run6-freeze-146988/candidate-manifest.json', '87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9')):
        manifest = REC / rel
        assert sha(manifest) == 'sha256:' + expected
        entries = json.loads(manifest.read_text())['files']
        for name, info in entries.items():
            f = REPO / name; s = f.lstat()
            assert stat.S_ISREG(s.st_mode) and sha(f) == info['sha256'] and s.st_size == info['bytes'] and oct(stat.S_IMODE(s.st_mode)) == info['mode'], name
        verified.append({'path': str(manifest.relative_to(REPO)), 'sha256': sha(manifest), 'files': len(entries)})
    report['prior_manifests_verified'] = verified
    sources = json.loads((REC / 'prepared-146897/evidence/provenance.json').read_text())
    for name, info in sources['provider_chain'].items():
        if 'sha256' in info: assert sha(REPO / name) == 'sha256:' + info['sha256'], name
        else: assert not (REPO / name).exists() and not (REPO / name).is_symlink(), name
    for group in ('source_requirements', 'current_observation_sources'):
        for name, expected in sources[group].items(): assert sha(REPO / name) == expected, name
    report['provider_chain_entries_verified'] = len(sources['provider_chain'])
    report['composition_observer_bindings_verified'] = len(sources['source_requirements']) + len(sources['current_observation_sources'])
    validation = json.loads((PREPARED / 'validation.json').read_text())
    assert validation['public_authority_facts']['authority_uuid'] == deployment.UUID
    held = Path(validation['temporary_path_retained'])
    for key, name in (('configuration', 'stage-execution.json'), ('submission', 'submission.json')):
        assert sha(held / name) == validation['documents'][key]
    report['validation'] = {'sha256': sha(PREPARED / 'validation.json'), 'temporary_path_retained': str(held), 'host_seconds': validation['wall_seconds'], 'public_bootstrap_authority': deployment.UUID, 'temporary_documents_match': True, 'actual_render_equivalence_established': False}
    report['baseline'] = {}
    for name in ('source', 'target'):
        root = deployment.RUN / name
        index = root / '.git/index'
        initial_index = sha(index)
        identity = deployment.git_read(root, 'show', '--no-patch', '--format=%H %T', 'HEAD')
        status = deployment.git_read(root, 'status', '--porcelain')
        branch = deployment.git_read(root, 'symbolic-ref', '--short', 'HEAD')
        assert identity == deployment.BASE + ' ' + deployment.TREE and not status and branch == 'main'
        assert sha(index) == initial_index
        payloads = {}
        for original in (REC / 'prepared-141510/baseline').rglob('*'):
            if original.is_file():
                rel = original.relative_to(REC / 'prepared-141510/baseline'); f = root / rel
                assert not f.is_symlink() and f.read_bytes() == original.read_bytes()
                s = f.stat(); payloads[str(rel)] = {'sha256': sha(f), 'mode': oct(stat.S_IMODE(s.st_mode))}
        assert len(payloads) == 10
        for rel in ('demo/greeting.py', 'demo/units.py', 'tests/test_greeting.py'):
            assert payloads[rel]['mode'] == '0o644'
        s = root.stat()
        report['baseline'][name] = {'identity': identity, 'status': status, 'branch': branch, 'index_digest_unchanged_by_reads': initial_index, 'payloads': payloads, 'observed_root_mode': oct(stat.S_IMODE(s.st_mode)), 'projected_uid': s.st_uid, 'projected_gid': s.st_gid}
    assert deployment.git_read(deployment.RUN / 'integration-workspace', 'rev-parse', '--is-bare-repository') == 'true'
    report['integration_workspace_bare'] = True
    absent = ['authority.sqlite3', 'integration.sqlite3', 'jobs.sqlite3', 'control.sqlite3', 'state', 'storage', 'launch', 'credentials', 'evidence']
    for name in absent: assert not (deployment.RUN / name).exists() and not (deployment.RUN / name).is_symlink(), name
    for name in ('selected-images.json', 'execution-review.json'):
        assert not (PREPARED / name).exists() and not (PREPARED / name).is_symlink(), name
    report['unprovisioned_names_absent'] = absent
    frozen = PREPARED / 'frozen-config'
    assert not frozen.exists() and not frozen.is_symlink(), 'Preparation gap changed; revalidate actual state before handoff'
    report['missing_actual_rendered_root'] = str(frozen)
    report['host_posture_scope'] = 'Owner149242 attests accepted host65532:1001 helper/validation success. Managed projected IDs are observations, not independent proof of actual host UID/GID.'
    report['verification_seconds'] = time.monotonic() - started
    with (EVIDENCE / 'available-preparation.json').open('x') as out: json.dump(report, out, indent=2); out.write('\n')
    print(json.dumps({'image_commands_verified': report['images']['exact_successful_commands'], 'manifests': [v['files'] for v in verified], 'missing_actual_inputs': str(frozen), 'verification_seconds': report['verification_seconds'], 'freeze_complete': False}, indent=2))


if __name__ == '__main__':
    main()
