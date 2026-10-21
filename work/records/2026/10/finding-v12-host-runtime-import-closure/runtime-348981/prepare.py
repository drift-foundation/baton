"""Offline archive preparation and AST audit. Never imports product code."""
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time

started = time.monotonic()
here = Path(__file__).resolve().parent
repo = here.parents[5]
old = repo / 'work/records/2026/10/finding-v12-serving-token-renewal/host-policy-347952'
sha = lambda b: hashlib.sha256(b).hexdigest()
def write(name, value):
    (here / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
binding = json.loads((old / 'HOST-POLICY.json').read_bytes())
assert sha((old / 'HOST-POLICY.json').read_bytes()) == 'eb57aa9c3ba74886e2d9856cfe3382ceab6a2bdb1799283512a4943dfeb62d52'
assert sha((old / 'manager-source.tar.gz').read_bytes()) == binding['archive']['sha256']
with tarfile.open(old / 'manager-source.tar.gz') as archive:
    files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
assert len(files) == 114
assert {p: sha(b) for p,b in files.items()} == binding['manager_files']
base = binding['acceptance']['host_base']
paths = subprocess.check_output(['git','ls-tree','-r','--name-only',base,'v12/python'], cwd=repo).decode().splitlines()
def module(path):
    path = path.removeprefix('src/').removesuffix('.py')
    return path.removesuffix('/__init__').replace('/', '.')
modules = {module(p.removeprefix('v12/python/')): p.removeprefix('v12/python/') for p in paths if p.endswith('.py') and (p.startswith('v12/python/src/') or p.startswith('v12/python/tools/'))}
added = []
def include(name):
    if name in modules:
        p = modules[name]
        if p not in files:
            data = subprocess.check_output(['git','show',base+':v12/python/'+p], cwd=repo)
            tested = Path('/tmp/baton-review-347919/v12/python') / p
            assert tested.read_bytes() == data, 'dependency differs from tested source: '+p
            files[p] = data
            added.append(p)
        parts = name.split('.')
        for i in range(1,len(parts)):
            include('.'.join(parts[:i]))
edges, dynamic, external = [], [], set()
seen = set()
while set(files) - seen:
    p = sorted(set(files) - seen)[0]
    seen.add(p)
    if not p.endswith('.py'): continue
    tree = ast.parse(files[p], filename=p)
    current = module(p)
    package = current if p.endswith('/__init__.py') else current.rpartition('.')[0]
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import): names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = node.module or ''
            if node.level:
                parent = package.split('.')
                prefix = '.'.join(parent[:len(parent)-node.level+1] + ([prefix] if prefix else []))
            names = [prefix] + [prefix+'.'+a.name for a in node.names if prefix+'.'+a.name in modules]
        for name in names:
            if name not in modules and 'tools.'+name in modules:
                name = 'tools.'+name  # Direct-script fallback for a supplied tools module.
            if name in modules:
                include(name)
                edges.append({'file':p,'line':node.lineno,'module':name,'member':modules[name]})
            elif name.split('.')[0] in ('tools','baton_v12'):
                raise AssertionError('unknown local import: '+name)
            else:
                assert name.split('.')[0] in sys.stdlib_module_names | {'jsonschema', 'rpds'}, 'external dependency: '+name
                external.add(name)
        if isinstance(node, ast.Call):
            call = ast.unparse(node.func)
            if any(s in call for s in ('__import__','import_module','spec_from','SourceFileLoader')) or call in ('exec','eval'):
                dynamic.append({'file':p,'line':node.lineno,'call':ast.unparse(node)})
assert added == ['tools/authoring_baseline.py'], added
assert sha(files[added[0]]) == '8e5987f56f8d5329c33a8e73f9df56f13213e134f2dade8180afabf80723efe9'
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w') as archive:
    for p,data in sorted(files.items()):
        m = tarfile.TarInfo(p); m.size = len(data); m.mode = 0o644; m.mtime = 0
        archive.addfile(m, io.BytesIO(data))
(here / 'manager-source.tar.gz').write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
binding['schema'] = 'baton.w348979.corrected-host-runtime-binding/1'
binding['work'] = 'W348979'; binding['claim'] = 348981
binding['supersedes'] = {'path':str(old.relative_to(repo))+'/HOST-POLICY.json','sha256':sha((old/'HOST-POLICY.json').read_bytes()),'reason':'missing deferred dependency; preserves all original 114 members'}
binding['archive']['members'] = len(files)
binding['archive']['sha256'] = sha((here/'manager-source.tar.gz').read_bytes())
binding['manager_files'] = {p:sha(b) for p,b in sorted(files.items())}
for p in added:
    binding['provenance'][p] = {'sha256':sha(files[p]),'base_sha256':sha(files[p]),'origin':'accepted-candidate-base'}
binding['acceptance']['successor_review'] = 'pending independent W348979 review; prior review binds original candidate only'
binding['closure_evidence'] = 'STATIC-CLOSURE.json'
write('HOST-POLICY.json', binding)
write('STATIC-CLOSURE.json', {'method':'AST walk of every supplied Python module, including nested functions; transitive local module and package inclusion against exact host base; no product imports', 'members':len(files),'added':added,'preserved_members':114,'edges':edges,'environment_imports':sorted(external),'dynamic_calls_requiring_manual_assessment':dynamic,'dynamic_execution':False})
write('SPENDING.json', {'preparation_static_seconds':time.monotonic()-started,'product_execution_seconds':0,'supplier_author_cumulative_seconds':135.817654632,'supplier_independent_review_seconds':4.704084767,'historical_live_seconds':[955.098994210,954.105032184],'historical_inner_costs':'unknown; preserved, not zero'})
print(json.dumps({'added':added,'members':len(files),'dynamic':dynamic,'binding_sha256':sha((here/'HOST-POLICY.json').read_bytes())},indent=2))
