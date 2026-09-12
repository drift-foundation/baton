"""Independent custody/limited-delta verification, no execution of production helpers."""
import ast, hashlib, json, pathlib, stat, time
start = time.monotonic()
ROOT = pathlib.Path('/home/sl/src/baton')
PROOF = ROOT / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
OUT = pathlib.Path(__file__).resolve().parent
NEW = PROOF / 'prepared-145615'
OLD = PROOF / 'prepared-145397'
def read(p): return json.loads(p.read_text())
def sha(p): return 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()
def files(m):
    for name, row in m['files'].items():
        p = ROOT / name
        s = p.lstat()
        assert stat.S_ISREG(s.st_mode), name
        assert sha(p) == row['sha256'], name
        assert s.st_size == row['bytes'], name
        assert oct(stat.S_IMODE(s.st_mode)) == row['mode'], name
    return len(m['files'])
manifest_path = NEW / 'candidate-manifest.json'
assert sha(manifest_path) == 'sha256:601f57182dd6b19922b5ce5e0f7b58abde24f74533a3720af07d75f3bd13bbdd'
m = read(manifest_path)
counts = {'candidate_files': files(m)}
provenance = read(NEW / 'evidence/provenance.json')
for key in ('prior_candidate_manifest', 'preserved_run4_freeze'):
    ref = provenance[key]
    path = ROOT / ref['path']
    assert sha(path) == ref['sha256'], key
    counts[key] = files(read(path))
unchanged = provenance['unchanged_dependencies']
for name in unchanged:
    assert (NEW/name).read_bytes() == (OLD/name).read_bytes(), name
for name, value in m['provider_chain'].items():
    p = ROOT/name
    if 'sha256' in value:
        assert sha(p).removeprefix('sha256:') == value['sha256'], name
    else:
        assert not p.exists() and not p.is_symlink(), name
for name, value in m['source_requirements'].items():
    assert sha(ROOT/name) == value, name
old = ast.parse((OLD/'deployment.py').read_text())
new = ast.parse((NEW/'deployment.py').read_text())
function = next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='documents')
additions = [n for n in function.body if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='instructions']
assert len(additions)==1
addition = additions[0]
assert isinstance(addition.op,ast.Add) and isinstance(addition.value,ast.Constant) and isinstance(addition.value.value,str)
function.body.remove(addition)
assert ast.dump(new,include_attributes=False)==ast.dump(old,include_attributes=False)
test_root=pathlib.Path('/tmp/w71879-145615-offline-verification-fuyiczch')
verification=read(test_root/'verification.json')
assert verification['tests']==26 and verification['failures']==verification['errors']==0
for name in ('verification.json','verification.txt'):
    (OUT/name).write_bytes((test_root/name).read_bytes())
actual=pathlib.Path('/tmp/w71879-145615-report-fixtures-366r8o9y/constructor/integration-instructions.txt')
assert actual.read_bytes()==(NEW/'evidence/generated-integration-instructions.txt').read_bytes()
result={'verdict':'accepted bounded instruction correction; not executable inputs or timeout proof',
        'manifest':sha(manifest_path),'counts':counts,'unchanged_dependencies':unchanged,
        'provider_entries':len(m['provider_chain']),'source_requirements':len(m['source_requirements']),
        'only_helper_change':'one literal instructions += statement in documents()',
        'emitted_instructions':sha(actual),'tests':verification,
        'verification_seconds':verification['seconds'],
        'custody_check_seconds':time.monotonic()-start,
        'no_new_run_or_marker':True}
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
