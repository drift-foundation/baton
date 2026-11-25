"""Exact-byte host import of the accepted W385830 N4a join candidate e9e9c84f.

Whole-path-set preflight first; any refusal leaves every target untouched.
Filesystem only: no staging, no commit, no other Git mutation. The five
W386057 isolation paths present in the tree are a separate, unreviewed-here
candidate: they must be disjoint and are never written."""
from pathlib import Path
import hashlib, json, os, stat, subprocess, tarfile
ROOT = Path('/home/sl/src/baton')
D = ROOT/'work/records/2026/11/finding-v12-native-provider-selection'
P = D/'evidence/import-e9e9c84f'
C = D/'evidence/n4a-join-386051'
REVIEW = D/'review-2026-11-24T23-40-10Z.md'
ISOLATION = json.loads((ROOT/'work/records/2026/11/finding-v12-git-fixture-isolation/evidence/candidate-manifest.json').read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
git = lambda *a: subprocess.run(['git', *a], cwd=ROOT, capture_output=True, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
m = json.loads((C/'candidate-manifest.json').read_text())
assert m['candidate'] == 'sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f'
assert 'sha256:'+sha(json.dumps({k: m[k] for k in ('base', 'files')}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == m['candidate']
assert m['base'] == 'ac034bc1c9fae525b94a1a5f21d9721c677dc39e'
assert sha(REVIEW.read_bytes()) == 'd38fa34d330765cd093bb0381e88a699b9dc89f8ed570b514b92086b1454230d', 'accepting review changed'
assert m['candidate'][7:] in REVIEW.read_text(), 'review does not name this candidate'
head = git('rev-parse', 'HEAD').stdout.decode().strip()
assert head == m['base'], 'HEAD is not the reviewed base'
assert not git('diff', '--cached', '--name-only').stdout.strip(), 'index has staged content'
assert sha((C/'candidate-files.tar.gz').read_bytes()) == '713112419c0e76c48788308ceefdc94c3146043bbf130468e7a6ae22254822f0'
isolation = {f['path'] for f in ISOLATION['files']}
with tarfile.open(C/'candidate-files.tar.gz') as t:
    members = t.getmembers(); assert len(members) == len(m['files']) == 17
    assert {x.name for x in members} == {x['path'] for x in m['files']}
    assert not ({x.name for x in members} & isolation), 'overlap with the isolation candidate'
    data = {}
    for x in members:
        assert x.isfile() and not Path(x.name).is_absolute() and '..' not in Path(x.name).parts and x.name.startswith('v12/')
        f = next(f for f in m['files'] if f['path'] == x.name)
        b = t.extractfile(x).read(); assert sha(b) == f['sha256'] and len(b) == f['bytes']
        data[x.name] = (b, f)
dirty = git('status', '--porcelain', '--', *sorted(data)).stdout.decode()
assert not dirty.strip(), 'target drift against HEAD:\n' + dirty
checks = []
for name, (b, f) in sorted(data.items()):
    path = ROOT/name
    for parent in path.parents:
        if parent == ROOT: break
        assert not parent.is_symlink(), str(parent)
        if parent.exists(): assert parent.is_dir(), str(parent)
    if f['base_sha256'] is not None:
        s = path.lstat(); assert stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_mode & stat.S_IWUSR, name
        assert sha(path.read_bytes()) == f['base_sha256'], 'target drift '+name
        mode = stat.S_IMODE(s.st_mode)
    else:
        assert not os.path.lexists(path), 'new target exists '+name
        mode = 0o644
    assert not mode & 0o111 and not int(f['mode'], 8) & 0o111, 'unexpected executable bit '+name
    checks.append({'path': name, 'existing': f['base_sha256'] is not None, 'base_sha256': f['base_sha256'],
                   'target_mode': oct(mode), 'manifest_mode': f['mode'], 'sha256': sha(b)})
before = {p: sha((ROOT/p).read_bytes()) for p in sorted(isolation)}
(P/'preflight.json').write_text(json.dumps({'candidate': m['candidate'], 'base': m['base'], 'head': head, 'index_empty': True,
    'accepting_review': REVIEW.name, 'drift_check': 'git status --porcelain over the 17 paths empty; existing targets equal manifest base_sha256; new targets absent',
    'checked': checks, 'refusals': 0, 'isolation_candidate': ISOLATION['candidate'], 'isolation_paths_before': before}, indent=2)+'\n')
for f in checks:
    path = ROOT/f['path']; path.parent.mkdir(parents=True, exist_ok=True)
    if f['existing']: path.write_bytes(data[f['path']][0])
    else:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as out: out.write(data[f['path']][0])
    assert sha(path.read_bytes()) == f['sha256'] and oct(stat.S_IMODE(path.stat().st_mode)) == f['target_mode'], f['path']
after = {p: sha((ROOT/p).read_bytes()) for p in sorted(isolation)}
assert after == before, 'isolation paths changed during import'
changed = sorted(l[3:] for l in git('status', '--porcelain', '--untracked-files=all', '--', 'v12').stdout.decode().splitlines())
unexpected = sorted(set(changed) - set(data) - isolation - {'v12/DESIGN.md'})
(P/'postflight.json').write_text(json.dumps({'candidate': m['candidate'], 'verified': checks, 'exact_bytes': True, 'existing_modes_preserved': True,
    'new_file_mode': '0o644 (Git records only the executable bit; none is executable)', 'isolation_paths_unchanged': True,
    'v12_status_paths_after': changed, 'unexpected_v12_paths': unexpected}, indent=2)+'\n')
print(json.dumps({'imported': len(checks), 'new': [f['path'] for f in checks if not f['existing']], 'unexpected_v12_paths': unexpected}))
