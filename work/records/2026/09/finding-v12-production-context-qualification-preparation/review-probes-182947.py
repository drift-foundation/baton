"""Independent bounded synthetic publication probes; no child processes."""
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
from unittest import mock

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'evidence'))
import qualification_contract as c
import qualification_worker as w

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

evidence = json.loads((R / 'EVIDENCE-182906.json').read_text())
checks = []
for row in evidence['files']:
    for p, expected in ((R / row['path'], row['candidate_sha256']), (R / row['retained_copy'], row['candidate_sha256']), (R / 'candidate-182771' / Path(row['path']).name, row['base_sha256'])):
        checks.append({'path': str(p.relative_to(R)), 'sha256': sha(p), 'matches': sha(p) == expected})
    assert oct(stat.S_IMODE((R / row['path']).stat().st_mode)) == row['mode']
assert all(x['matches'] for x in checks)
before = {row['path']: sha(R / row['path']) for row in evidence['files']}
session = '6887cfd5-e201-44ed-94eb-21d6302e13bf'
def mode(p):
    return oct(stat.S_IMODE(p.stat().st_mode))

results = []
started = time.monotonic()
cases = ('healthy', 'symlinked-projects-parent', 'hardlinked-session', 'foreign-session', 'nested-session', 'direct-credential', 'credential-in-home-cache', 'credential-in-claude-cache', 'unrelated-symlink', 'regular-project-replacement')
for case in cases:
    with tempfile.TemporaryDirectory(prefix='baton-review-182947-') as temporary:
        root = Path(temporary)
        home = root / 'home'
        projects = home / '.claude/projects'
        project = projects / 'observed'
        project.mkdir(parents=True)
        selected = project / (session + '.jsonl')
        selected.write_bytes(b'synthetic-session')
        project.chmod(0o700)
        selected.chmod(0o600)
        (home / '.claude/.credentials.json').symlink_to(c.SLOT)
        victim = selected
        real_survey = w._survey
        survey = real_survey
        swaps = []
        if case == 'symlinked-projects-parent':
            outside = root / 'outside'
            projects.rename(outside)
            projects.symlink_to(outside)
            victim = outside / 'observed' / selected.name
        elif case == 'hardlinked-session':
            victim = root / 'alias'
            os.link(selected, victim)
        elif case == 'foreign-session':
            (project / 'foreign.jsonl').write_bytes(b'foreign')
        elif case == 'nested-session':
            (project / 'nested').mkdir()
            (project / 'nested/foreign.jsonl').write_bytes(b'foreign')
        elif case == 'direct-credential':
            (home / 'oauth-token').write_bytes(b'synthetic-forbidden-name')
        elif case in ('credential-in-home-cache', 'credential-in-claude-cache'):
            cache = home / ('cache' if case == 'credential-in-home-cache' else '.claude/cache')
            cache.mkdir()
            (cache / 'oauth-token').write_bytes(b'synthetic-forbidden-name')
        elif case == 'unrelated-symlink':
            (project / 'non-session-link').symlink_to(root / 'absent')
        elif case == 'regular-project-replacement':
            decoy = root / 'decoy'
            decoy.mkdir(mode=0o700)
            victim = decoy / selected.name
            victim.write_bytes(b'uninspected-decoy')
            victim.chmod(0o600)
            (decoy / 'oauth-token').write_bytes(b'synthetic-forbidden-name')
            def survey(home_fd, selected_session):
                verified = real_survey(home_fd, selected_session)
                swaps.append('post-survey-regular-directory-replacement')
                project.rename(root / 'surveyed-original')
                decoy.rename(project)
                return verified
        initial = mode(victim)
        initial_inode = victim.stat().st_ino
        with mock.patch.object(c, 'HOME', str(home)), mock.patch.object(c, 'GROUP', os.getgid()), mock.patch.object(w, '_survey', survey):
            try:
                published = w.publish(session, 1)
                outcome = 'published'
            except BaseException as error:
                published = None
                outcome = c.failure_code(error)
        if case == 'regular-project-replacement':
            victim = selected
        try:
            c.inventory(home)
            inventory = 'accepted'
        except BaseException as error:
            inventory = c.failure_code(error)
        row = {'case': case, 'outcome': outcome, 'published': published, 'victim_before': initial, 'victim_after': mode(victim), 'same_victim_inode': victim.stat().st_ino == initial_inode, 'subsequent_inventory': inventory, 'post_survey_swaps': len(swaps)}
        if case == 'healthy':
            assert outcome == 'published' and row['victim_after'] == '0o640'
        elif case == 'regular-project-replacement':
            row['surveyed_original_mode_after'] = mode(root / 'surveyed-original' / selected.name)
            row['surveyed_original_project_mode_after'] = mode(root / 'surveyed-original')
            row['decoy_project_mode_after'] = mode(project)
            assert swaps and outcome == 'published'
            assert row['victim_after'] == '0o600' and row['same_victim_inode']
            assert row['surveyed_original_mode_after'] == '0o640'
            assert row['surveyed_original_project_mode_after'] == '0o2750' and row['decoy_project_mode_after'] == '0o700'
        else:
            assert outcome.startswith('publish-') and row['victim_after'] == '0o600', row
        results.append(row)

for number, expected in ((errno.EACCES, 'EACCES'), (errno.EIO, 'EIO'), (errno.ENOENT, 'ENOENT')):
    with tempfile.TemporaryDirectory(prefix='baton-review-182947-cause-') as temporary:
        with mock.patch.object(c.os, 'scandir', side_effect=OSError(number, 'PRIVATE-CANARY')):
            try:
                c.inventory(temporary)
            except BaseException as error:
                detail = {'step': 'source-inventory', **c.failure_detail(error)}
                assert detail['cause'] == expected and 'PRIVATE-CANARY' not in json.dumps(detail) and c.valid_failure_detail(detail)
                results.append({'case': 'coverage-' + expected, 'code': c.failure_code(error), 'detail': detail, 'cause_matches': True, 'canary_absent': True, 'valid': True})
seconds = time.monotonic() - started
assert before == {row['path']: sha(R / row['path']) for row in evidence['files']}
record = {'claim': 182947, 'candidate_manifest': evidence['manifest_sha256'], 'checks': checks, 'results': results, 'seconds': seconds, 'source_unchanged': True, 'python': sys.version, 'scope': 'synthetic same-UID trees; no real private roots, credentials, engine or model; no child processes; owned temporary directories cleaned'}
with (R / 'review-probes-182947.json').open('x') as out:
    json.dump(record, out, indent=2)
    out.write('\n')
print(json.dumps(record, indent=2))
