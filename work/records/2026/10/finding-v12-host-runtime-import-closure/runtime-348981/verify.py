"""Read-only archive/member and static dependency regression verification."""
import ast
import hashlib
import json
from pathlib import Path
import tarfile
import time
started = time.monotonic()
here = Path(__file__).resolve().parent
repo = here.parents[5]
sha = lambda b: hashlib.sha256(b).hexdigest()
binding = json.loads((here/'HOST-POLICY.json').read_bytes())
assert sha((here/'HOST-POLICY.json').read_bytes()) == '8309fd6ec90231c6e2d92468520bdeb075f20c4ee5f7ae7e8d34c637c10022a6'
assert sha((here/'manager-source.tar.gz').read_bytes()) == binding['archive']['sha256']
with tarfile.open(here/'manager-source.tar.gz') as archive:
    members = archive.getmembers()
    assert len(members) == len({m.name for m in members}) == 115
    assert all(m.isfile() and m.mode == 0o644 and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)
    files = {m.name:archive.extractfile(m).read() for m in members}
assert {p:sha(b) for p,b in files.items()} == binding['manager_files']
old = json.loads((repo/binding['supersedes']['path']).read_bytes())
assert all(sha(files[p]) == expected for p,expected in old['manager_files'].items())
closure = json.loads((here/'STATIC-CLOSURE.json').read_bytes())
for edge in closure['edges']:
    assert edge['member'] in files, edge
    tree = ast.parse(files[edge['file']])
    assert any(isinstance(n,(ast.Import,ast.ImportFrom)) and n.lineno == edge['line'] for n in ast.walk(tree))
# The regression is deferred inside main: the old artifact must fail this edge.
edge = next(e for e in closure['edges'] if e['file']=='tools/authoring_enforcement.py' and e['line']==554 and e['module']=='tools.authoring_baseline')
assert edge['member'] not in old['manager_files']
assert edge['member'] in files
assert binding['execution_selection'] is None and binding['stage_bootstrap_launch_authorized'] is False
print(json.dumps({'verified':True,'members':115,'preserved':114,'old_archive_missing_deferred_main_dependency':True,'static_edges':len(closure['edges']),'seconds':time.monotonic()-started,'product_executed':False},indent=2))
