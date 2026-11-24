"""Package the W385853 instruction-delivery candidate. Reads the disposable
candidate repository; writes only into the scratch evidence directory."""
from pathlib import Path
import json, hashlib, subprocess, stat, tarfile, shutil, os
root = Path('/home/sl/src/baton'); r = root/'work/scratch/w385853-impl/repo'; e = root/'work/scratch/w385853-impl/evidence'
d = root/'work/records/2026/11/finding-host-worker-instruction-separation'
sha = lambda b: hashlib.sha256(b).hexdigest()
base = '317351e73c92749e201f536ba115c9fdf213077d'
ctx = e/'context'; ctx.mkdir(exist_ok=True)
for name in ('DELIVERY-CONTRACT-FINAL-2026-11-24.md', 'OWNERSHIP-N4A-DELIVERY-2026-11-24.md'):
    shutil.copyfile(d/name, ctx/name)
shutil.copyfile(root/'v12/DESIGN.md', ctx/'DESIGN.md')
git = lambda *a: subprocess.check_output(['git', *a], cwd=r)
assert git('status', '--porcelain', '--', '.').decode().strip(), 'no changes'
outside = [l for l in git('status', '--porcelain').decode().splitlines() if not l[3:].startswith('v12/')]
assert not outside, outside
paths = sorted(set(git('diff', '--name-only', '--', 'v12').decode().split()) | set(git('ls-files', '--others', '--exclude-standard', '--', 'v12').decode().split()))
tracked = set(git('ls-files', '--', 'v12').decode().split())
files = []; delta = []
for name in paths:
    p = r/name; b = p.read_bytes(); mode = oct(stat.S_IMODE(p.stat().st_mode))
    files.append({'path': name, 'bytes': len(b), 'mode': mode, 'sha256': sha(b)})
    if name in tracked:
        before = git('show', 'HEAD:'+name)
        delta.append({'path': name, 'before_sha256': sha(before), 'before_bytes': len(before), 'after_sha256': sha(b), 'after_bytes': len(b), 'after_mode': mode})
    else:
        delta.append({'path': name, 'before_sha256': None, 'before_bytes': None, 'after_sha256': sha(b), 'after_bytes': len(b), 'after_mode': mode, 'added': True})
context = {p.name: sha(p.read_bytes()) for p in sorted(ctx.iterdir())}
identity = {'base': base, 'files': files, 'context': context}
candidate = 'sha256:' + sha(json.dumps(identity, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
manifest = dict(identity, candidate=candidate, work='W385853',
                algorithm='sha256 of UTF-8 JSON of {base,files,context}; sort_keys=True, separators=(comma,colon), ensure_ascii=False; files sorted by path',
                author='baton.prompt (K); owner-selected direct interactive implementation, no claim; coordination M386030',
                base_export_commit_in_disposable_repository=git('rev-parse', 'HEAD').decode().strip(),
                status='instruction-delivery candidate for INDEPENDENT review by a participant other than the author; not imported, not built, not qualified')
(e/'candidate-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
(e/'delta-manifest.json').write_text(json.dumps({'base': base, 'candidate': candidate, 'files': delta}, indent=2, sort_keys=True)+'\n')
patch = git('diff', '--', 'v12')
for name in paths:
    if name not in tracked:  # read-only: no index change even in the disposable repository
        patch += subprocess.run(['git', 'diff', '--no-index', '--', '/dev/null', name], cwd=r, capture_output=True).stdout
(e/'delta.patch').write_bytes(patch)
with tarfile.open(e/'candidate-files.tar.gz', 'w:gz') as tar:
    for p in paths: tar.add(r/p, arcname=p, recursive=False)
with tarfile.open(e/'candidate-files.tar.gz') as tar:
    assert set(tar.getnames()) == set(paths)
    for member in tar.getmembers():
        f = next(f for f in files if f['path'] == member.name)
        assert sha(tar.extractfile(member).read()) == f['sha256'] and oct(member.mode) == f['mode']
(e/'candidate-files.tar.gz.sha256').write_text(sha((e/'candidate-files.tar.gz').read_bytes())+'  candidate-files.tar.gz\n')
check = subprocess.run(['git', 'diff', '--check'], cwd=r, capture_output=True); assert check.returncode == 0
(e/'diff-check.log').write_bytes(check.stdout+check.stderr)
py = '/home/sl/.local/state/baton-v12-venv/bin/python'
result = subprocess.run([py, '-m', 'tools.source_identity', '--declared', 'v12'], cwd=r/'v12/python', env=dict(os.environ, PYTHONPATH='src'), capture_output=True); assert result.returncode == 0
(e/'final-source.json').write_bytes(result.stdout)
final = json.loads(result.stdout); runs = {}
for run in ('focused', 'adjacent'):
    tested = json.loads((e/f'{run}.source-after.json').read_text()); summary = json.loads((e/f'{run}.summary.json').read_text())
    x = {p['path']: p['sha256'] for p in tested['changed']}; y = {p['path']: p['sha256'] for p in final['changed']}
    runs[run] = {'tested_source': tested['content_digest'], 'final_source': final['content_digest'],
                 'paths_differing_from_final': sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k)),
                 'collected': summary['collected'], 'executed': summary['executed'], 'passed': summary['passed'],
                 'nonpassing': summary['nonpassing'], 'unaccounted': summary['unaccounted'], 'duplicates': summary['duplicates'],
                 'exit_status': summary['exit_status'], 'duration_seconds': summary['duration_seconds'], 'source_drift': summary['source_drift']}
    assert not runs[run]['paths_differing_from_final'] and summary['collected'] == summary['passed'] == summary['executed'] and not summary['nonpassing'] and not summary['unaccounted'] and summary['exit_status'] == 0, run
(e/'source-reconciliation.json').write_text(json.dumps({'runs': runs, 'canonical_inputs_outside_scope': {
    'docs/V12-WORKER-INSTRUCTIONS.md': sha((r/'docs/V12-WORKER-INSTRUCTIONS.md').read_bytes()), 'AGENTS.md': sha((r/'AGENTS.md').read_bytes())}}, indent=2, sort_keys=True)+'\n')
print(json.dumps({'candidate': candidate, 'paths': len(files), 'archive': sha((e/'candidate-files.tar.gz').read_bytes()), 'runs': {k: (v['passed'], round(v['duration_seconds'], 1)) for k, v in runs.items()}}))
