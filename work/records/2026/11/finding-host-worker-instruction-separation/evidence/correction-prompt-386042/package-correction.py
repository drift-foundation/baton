"""Package the R1/R2 correction as a new candidate plus an exact delta from
the reviewed candidate a1d4ba20. Read-only toward the candidate repository."""
from pathlib import Path
import json, hashlib, subprocess, stat, tarfile, shutil, os, difflib
root = Path('/home/sl/src/baton'); r = root/'work/scratch/w385853-impl/repo'; e = root/'work/scratch/w385853-impl/evidence-r1r2'
d = root/'work/records/2026/11/finding-host-worker-instruction-separation'; old = d/'evidence/implementation-prompt-386030'
sha = lambda b: hashlib.sha256(b).hexdigest()
prior = json.loads((old/'candidate-manifest.json').read_text()); oldfiles = {f['path']: f for f in prior['files']}
assert prior['candidate'] == 'sha256:a1d4ba200543fed639864a9221e8bd46e6a947f236c11343e1470de17cb5ef8a'
ctx = e/'context'; ctx.mkdir(exist_ok=True)
for p in (old/'context').iterdir(): shutil.copyfile(p, ctx/p.name)
shutil.copyfile(d/'review-2026-11-24T22-30-06Z.md', ctx/'review-2026-11-24T22-30-06Z.md')
git = lambda *a: subprocess.check_output(['git', *a], cwd=r)
outside = [l for l in git('status', '--porcelain').decode().splitlines() if not l[3:].startswith('v12/')]
assert not outside, outside
paths = sorted(set(git('diff', '--name-only', '--', 'v12').decode().split()) | set(git('ls-files', '--others', '--exclude-standard', '--', 'v12').decode().split()))
files = []; delta = []; patch = []
with tarfile.open(old/'candidate-files.tar.gz') as previous:
    for name in paths:
        p = r/name; b = p.read_bytes(); mode = oct(stat.S_IMODE(p.stat().st_mode))
        files.append({'path': name, 'bytes': len(b), 'mode': mode, 'sha256': sha(b)})
        before = previous.extractfile(name).read() if name in oldfiles else git('show', 'HEAD:'+name)
        if sha(before) != sha(b):
            delta.append({'path': name, 'in_prior_candidate': name in oldfiles, 'before_sha256': sha(before), 'before_bytes': len(before),
                          'after_sha256': sha(b), 'after_bytes': len(b), 'after_mode': mode})
            patch.extend(difflib.unified_diff(before.decode().splitlines(keepends=True), b.decode().splitlines(keepends=True), fromfile='a/'+name, tofile='b/'+name))
assert not (set(oldfiles) - set(paths)), 'a prior path left the candidate'
unchanged = sorted(p for p in oldfiles if p not in {x['path'] for x in delta})
context = {p.name: sha(p.read_bytes()) for p in sorted(ctx.iterdir())}
identity = {'base': prior['base'], 'files': files, 'context': context}
candidate = 'sha256:' + sha(json.dumps(identity, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
manifest = dict(identity, candidate=candidate, prior_candidate=prior['candidate'], work='W385853', algorithm=prior['algorithm'],
                author='baton.prompt (K); owner-selected direct interactive correction of review M386040, no claim; coordination M386042',
                status='R1/R2 correction candidate for independent delta review by baton.codxpc; not imported, not built, not qualified')
(e/'candidate-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
(e/'delta-manifest.json').write_text(json.dumps({'base': prior['base'], 'from_candidate': prior['candidate'], 'to_candidate': candidate,
    'files': delta, 'prior_paths_unchanged': unchanged}, indent=2, sort_keys=True)+'\n')
(e/'delta.patch').write_text(''.join(patch))
for name, selected in (('candidate-files.tar.gz', paths), ('delta-files.tar.gz', [f['path'] for f in delta])):
    with tarfile.open(e/name, 'w:gz') as tar:
        for p in selected: tar.add(r/p, arcname=p, recursive=False)
    with tarfile.open(e/name) as tar:
        assert set(tar.getnames()) == set(selected)
        for member in tar.getmembers():
            f = next(f for f in files if f['path'] == member.name)
            assert sha(tar.extractfile(member).read()) == f['sha256'] and oct(member.mode) == f['mode']
    (e/(name+'.sha256')).write_text(sha((e/name).read_bytes())+'  '+name+'\n')
check = subprocess.run(['git', 'diff', '--check'], cwd=r, capture_output=True); assert check.returncode == 0, check.stdout
(e/'diff-check.log').write_bytes(check.stdout+check.stderr)
py = '/home/sl/.local/state/baton-v12-venv/bin/python'
result = subprocess.run([py, '-m', 'tools.source_identity', '--declared', 'v12'], cwd=r/'v12/python', env=dict(os.environ, PYTHONPATH='src'), capture_output=True); assert result.returncode == 0
(e/'final-source.json').write_bytes(result.stdout); final = json.loads(result.stdout)
tested = json.loads((e/'focused.source-after.json').read_text()); summary = json.loads((e/'focused.summary.json').read_text())
assert tested['content_digest'] == final['content_digest'] and summary['collected'] == summary['executed'] == summary['passed'] and not summary['nonpassing'] and not summary['unaccounted'] and summary['exit_status'] == 0
(e/'source-reconciliation.json').write_text(json.dumps({'tested_source': tested['content_digest'], 'final_source': final['content_digest'], 'equal': True,
    'consumed_root_documents': [c for c in final['consumed'] if c['path'] in ('AGENTS.md', 'docs/V12-WORKER-INSTRUCTIONS.md')],
    'focused': {k: summary[k] for k in ('collected', 'executed', 'passed', 'exit_status', 'duration_seconds', 'duplicates', 'unaccounted', 'nonpassing', 'source_drift')}}, indent=2, sort_keys=True)+'\n')
new_ids = sorted(set(summary['outcomes']) - set(json.loads((old/'focused.summary.json').read_text())['outcomes']) - {i for i in summary['outcomes'] if i.startswith(('tests.tools.test_parallel_runner', 'tests.tools.test_native_handoffs'))})
(e/'new-test-ids.json').write_text(json.dumps(new_ids, indent=1)+'\n')
print(json.dumps({'candidate': candidate, 'paths': len(files), 'delta_paths': [x['path'] for x in delta], 'unchanged_prior_paths': len(unchanged),
                  'archive': sha((e/'candidate-files.tar.gz').read_bytes()), 'delta_archive': sha((e/'delta-files.tar.gz').read_bytes()), 'new_ids': new_ids, 'patch_lines': len(patch)}, indent=1))
