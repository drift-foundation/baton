"""Static joined-evidence audit. Does not import or execute product/test code."""
import hashlib
import json
from pathlib import Path
import stat
import time

R = Path(__file__).resolve().parent
ROOT = R.parents[4]
C1 = R.parent / 'finding-v12-c1-useful-correction'
C2 = R.parent / 'finding-v12-c2-counted-reopen'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def path(value):
    return ROOT / value.removeprefix('baton:')
def load(p):
    return json.loads(p.read_text())
checks = []
def check(p, expected):
    actual = sha(p)
    checks.append({'path': str(p.relative_to(ROOT)), 'expected': expected, 'actual': actual, 'matches': actual == expected})
    return actual == expected

started = time.monotonic()
specs = [
    ('A', R / 'candidate-175150.json', '9d82e0035ff756bcf7b631307482394adeb4c7ea51a1efae63ca2648babf9cf9'),
    ('B', R / 'candidate-179255.json', '010aaefde8159ef52b95ddf289b981b051a2b64041a3a1638441a158cb517c50'),
    ('C1', C1 / 'CANDIDATE-180423.json', '2e7107ecbfc133374e1811e33e99e3764924c20f90ceb22ab71683a00d834499'),
    ('C2', C2 / 'CANDIDATE-182279.json', '055b765cf539d472fda98dabc173973162214babbd51a97b758d70499086b628'),
]
latest, history, succession = {}, {}, []
for label, manifest, expected in specs:
    check(manifest, expected)
    for row in load(manifest)['files']:
        name = row['path'].removeprefix('baton:')
        snapshot = row.get('candidate_path', row.get('snapshot'))
        check(path(snapshot), row['sha256'])
        if name in latest:
            previous = latest[name]
            succession.append({'path': name, 'from': previous['slice'], 'to': label, 'accepted_predecessor_sha256': previous['sha256'], 'successor_base_sha256': row['base_sha256'], 'matches': previous['sha256'] == row['base_sha256']})
        history.setdefault(name, []).append({'slice': label, 'sha256': row['sha256'], 'snapshot': snapshot})
        latest[name] = {'path': name, 'slice': label, 'sha256': row['sha256'], 'accepted_target_mode': row['target_mode']}
for name, row in latest.items():
    p = ROOT / name
    row['current_sha256'] = sha(p)
    row['matches'] = check(p, row['sha256'])
    mode = p.lstat().st_mode
    row['current_mode'] = oct(stat.S_IMODE(mode))
    row['mode_matches_candidate'] = stat.S_IMODE(mode) == int(row['accepted_target_mode'], 8)
    row['regular_nonsymlink_owner_writable'] = stat.S_ISREG(mode) and bool(mode & stat.S_IWUSR)
    row['succession'] = history[name]

evidence_specs = [
    (R / 'REVIEW-EVIDENCE-175202.json', '95cf18411aac6322e11db06615b77150a855b17466c9b3f76c9cd77f46a07043'),
    (R / 'review-evidence-179432-3.json', '65a16e37788266b67926f0c420316c5fc3f7acf858d3788b218e40b283ba33fd'),
    (C1 / 'REVIEW-EVIDENCE-180553.json', '715d34ff5b04673dccb7971b275666ca9ef2d0a84d774ed917c58b18b46761dc'),
    (C2 / 'REVIEW-EVIDENCE-182379.json', '83dc7d5d99ee627e563713f2a29b1afc3e625e9aec1cb5fe919b50a1c52a0560'),
]
for p, expected in evidence_specs:
    check(p, expected)
for dossier, name in ((R, 'REVIEW-EVIDENCE-175202.json'), (C1, 'REVIEW-EVIDENCE-180553.json')):
    for name, expected in load(dossier / name)['artifacts'].items():
        check(dossier / name, expected)
b = load(R / 'review-evidence-179432-3.json')
check(R / 'review-run-179432-3.log', b['log_sha256'])
c2 = load(C2 / 'REVIEW-EVIDENCE-182379.json')
for run in c2['runs']:
    for key in ('receipt', 'trace', 'log'):
        check(path(run[key]['path']), run[key]['sha256'])
receipts = [('A1', load(R / 'REVIEW-EVIDENCE-175202.json')['runs'][0]), ('A2', load(R / 'REVIEW-EVIDENCE-175202.json')['runs'][1]), ('B', b)]
for label in ('positive', 'negative', 'focused'):
    receipts.append(('C1-' + label, load(C1 / ('review-run-180553-' + label + '.json'))))
for run in c2['runs']:
    receipts.append(('C2-' + run['selector'], load(path(run['receipt']['path']))))
environment = []
for label, receipt in receipts:
    environment.append({'label': label, 'python': receipt['python'], 'dependencies': receipt['dependencies'], 'status': receipt['status'], 'timeout': receipt['timeout'], 'group_gone': receipt['group_gone']})
reviews = []
for p in (R / 'review-2026-09-15T04-55-41Z.md', R / 'review-2026-09-15T16-15-23Z.md', C1 / 'review-2026-09-15T19-18-29Z.md', C2 / 'review-2026-09-16T00-49-52Z.md'):
    reviews.append({'path': str(p.relative_to(ROOT)), 'sha256': sha(p)})
lock = (ROOT / 'v12/python/requirements.lock').read_text()
pins_match = all(all(f'{name}=={version}' in lock for name, version in e['dependencies'].items()) for e in environment)
result = {'claim': 182748, 'kind': 'static joined evidence, no test or provider/engine execution', 'reviews': reviews, 'checks': checks, 'successions': succession, 'composed_paths': list(latest.values()), 'environments_from_retained_runs': environment, 'all_dependency_versions_match_current_lock': pins_match, 'lock_sha256': sha(ROOT / 'v12/python/requirements.lock'), 'pyproject_sha256': sha(ROOT / 'v12/python/pyproject.toml'), 'deployment_base_sha256': sha(ROOT / 'v12/python/DEPLOYMENT.md'), 'progress_before_sha256': sha(R / 'PROGRESS.md'), 'all_hashes_match': all(r['matches'] for r in checks), 'all_succession_bases_match': all(r['matches'] for r in succession), 'mode_differences': [r for r in latest.values() if not r['mode_matches_candidate']], 'new_test_seconds': 0, 'cumulative_reviewer_test_seconds': 117.55238462003763, 'cumulative_author_test_seconds_separate': 234.30053109725122, 'static_seconds': time.monotonic() - started}
with (R / 'JOINED-EVIDENCE-182748.json').open('x') as out:
    json.dump(result, out, indent=2)
    out.write('\n')
print(json.dumps({k: result[k] for k in ('all_hashes_match', 'all_succession_bases_match', 'all_dependency_versions_match_current_lock', 'mode_differences', 'deployment_base_sha256', 'static_seconds')}, indent=2))
print('composed_paths', len(latest), 'checks', len(checks), 'successions', len(succession))
print('evidence_sha256', sha(R / 'JOINED-EVIDENCE-182748.json'))
