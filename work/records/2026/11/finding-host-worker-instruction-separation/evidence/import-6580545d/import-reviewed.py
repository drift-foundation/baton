"""Exact-byte host import of the accepted W385853 candidate 6580545d.

Whole-path-set preflight first; any refusal leaves every target untouched.
Filesystem only: no staging, no commit, no other Git mutation."""
from pathlib import Path
import hashlib, json, os, stat, subprocess, tarfile
ROOT = Path('/home/sl/src/baton')
D = ROOT/'work/records/2026/11/finding-host-worker-instruction-separation'
P = D/'evidence/import-6580545d'
C = D/'evidence/correction-prompt-386042'
REVIEW = D/'review-2026-11-24T22-43-47Z.md'
sha = lambda b: hashlib.sha256(b).hexdigest()
git = lambda *a: subprocess.run(['git', *a], cwd=ROOT, capture_output=True, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
m = json.loads((C/'candidate-manifest.json').read_text())
assert m['candidate'] == 'sha256:6580545d6cb0c9673e9baf4dce3699b41813024654da1af5386e85dcbe59d440'
assert 'sha256:'+sha(json.dumps({k: m[k] for k in ('base', 'files', 'context')}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == m['candidate']
assert sha(REVIEW.read_bytes()) == '261ef90541b06edfb03ae3257df5d5833dd23998d2b38919c1e5a15decaff45a', 'accepting review changed'
assert m['candidate'][7:] in REVIEW.read_text(), 'review does not name this candidate'
head = git('rev-parse', 'HEAD').stdout.decode().strip()
assert head == m['base'], 'HEAD is not the reviewed base'
assert not git('diff', '--cached', '--name-only').stdout.strip(), 'index has staged content'
assert sha((C/'candidate-files.tar.gz').read_bytes()) == '5abb5d904c9e2c655823e16ebfb4e424077cbf618cdbef76ac400d19b07ad965'
with tarfile.open(C/'candidate-files.tar.gz') as t:
    members = t.getmembers(); assert len(members) == len(m['files']) == 12
    assert {x.name for x in members} == {x['path'] for x in m['files']}
    data = {}
    for x in members:
        assert x.isfile() and not Path(x.name).is_absolute() and '..' not in Path(x.name).parts and x.name.startswith('v12/')
        f = next(f for f in m['files'] if f['path'] == x.name)
        b = t.extractfile(x).read(); assert sha(b) == f['sha256'] and len(b) == f['bytes'] and oct(x.mode) == f['mode']
        data[x.name] = b
checks = []
for name, b in sorted(data.items()):
    path = ROOT/name
    for parent in path.parents:
        if parent == ROOT: break
        assert not parent.is_symlink(), str(parent)
        if parent.exists(): assert parent.is_dir(), str(parent)
    base = git('cat-file', 'blob', m['base']+':'+name)
    if base.returncode == 0:
        s = path.lstat(); assert stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_mode & stat.S_IWUSR, name
        assert path.read_bytes() == base.stdout, 'target drift '+name
        mode = stat.S_IMODE(s.st_mode)
    else:
        assert not os.path.lexists(path), 'new target exists '+name
        mode = 0o644
    checks.append({'path': name, 'existing': base.returncode == 0, 'base_sha256': sha(base.stdout) if base.returncode == 0 else None,
                   'target_mode': oct(mode), 'sha256': sha(b)})
design = {'manifest_context': m['context']['DESIGN.md'], 'working_tree': sha((ROOT/'v12/DESIGN.md').read_bytes())}
(P/'preflight.json').write_text(json.dumps({'candidate': m['candidate'], 'base': m['base'], 'head': head, 'index_empty': True,
    'accepting_review': REVIEW.name, 'checked': checks, 'refusals': 0,
    'design_context': dict(design, equal=design['manifest_context'] == design['working_tree'], note='DESIGN.md is context, not an imported path')}, indent=2)+'\n')
for f in checks:
    path = ROOT/f['path']; path.parent.mkdir(parents=True, exist_ok=True)
    if f['existing']: path.write_bytes(data[f['path']])
    else:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as out: out.write(data[f['path']])
    assert sha(path.read_bytes()) == f['sha256'] and oct(stat.S_IMODE(path.stat().st_mode)) == f['target_mode'], f['path']
changed = sorted(l[3:] for l in git('status', '--porcelain', '--', 'v12').stdout.decode().splitlines())
(P/'postflight.json').write_text(json.dumps({'candidate': m['candidate'], 'verified': checks, 'exact_bytes': True, 'existing_modes_preserved': True,
    'v12_status_paths_after': changed, 'unexpected_v12_paths': sorted(set(changed) - set(data) - {'v12/DESIGN.md'})}, indent=2)+'\n')
print(json.dumps({'imported': len(checks), 'new': [f['path'] for f in checks if not f['existing']], 'design_equal': design['manifest_context'] == design['working_tree'],
                  'unexpected_v12_paths': sorted(set(changed) - set(data) - {'v12/DESIGN.md'})}))
