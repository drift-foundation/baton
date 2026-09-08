"""Independent lexical/boundedness probes; planned cumulative budget10s.

No suite, daemon, runtime/store mutation or source edits. One child process
per scanner snapshot bounds a potentially nonterminating origin fixed point.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]

def module(path):
    spec = importlib.util.spec_from_file_location("tests.manager.review_inventory", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

if len(sys.argv) > 1:
    b = module(Path(sys.argv[1]))
    sources = [(Path("sample.py"), ast.parse('''
def _record(*, envelope):
    return envelope["record"]
def public(row):
    row = _record(envelope=row)
    return row["identity"]
'''))]
    result = b._returned_origins(sources)
    print("completed")
    raise SystemExit

candidate = HERE / "candidate.py"
before = HERE / "before.py"
live = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
facts = {"hashes": {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate,before,live)}}
assert candidate.read_bytes() == live.read_bytes()
b = module(candidate)
fragments = [
    (Path("producer.py"), ast.parse('''
def row(connection):
    return connection.execute("SELECT * FROM offers").fetchone()
''')),
    (Path("consumer.py"), ast.parse('''
from .producer import row as read
def _view(row):
    return row["claim_generation"]
def public(connection, read):
    return _view(read(connection))
'''))]
returned = b._returned_origins(fragments)
source, tree = fragments[1]
site = "consumer.py:public"
node = dict(b._functions(tree, source.name))[site]
origins = b._origins(node, site, returned)
facts["shadowed_parameter_origins"] = origins
facts["shadowed_import_projection"] = sorted(b._through_helpers({},site,node,origins,b._helpers(tree,source.name),returns=returned))
facts["expected_shadowed_adopted_entries"] = []

for name, path in (("baseline",before),("candidate",candidate)):
    start = time.monotonic()
    try:
        answer = subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),str(path.resolve())],capture_output=True,text=True,timeout=2)
        facts[name+"_member_reassignment"] = {"returncode":answer.returncode,"stdout":answer.stdout,"stderr":answer.stderr}
    except subprocess.TimeoutExpired:
        facts[name+"_member_reassignment"] = {"timed_out_seconds":2}
    facts[name+"_elapsed"] = time.monotonic()-start

old_tree, new_tree = ast.parse(before.read_text()), ast.parse(candidate.read_text())
classes = lambda tree: {n.name:ast.dump(n) for n in tree.body if isinstance(n,ast.ClassDef)}
old_classes,new_classes=classes(old_tree),classes(new_tree)
facts["changed_existing_classes"] = [n for n,v in old_classes.items() if new_classes.get(n)!=v]
facts["added_classes"] = sorted(new_classes.keys()-old_classes.keys())
facts["prior_classes"] = len(old_classes)
(HERE / "review-116112.json").write_text(json.dumps(facts,indent=2,sort_keys=True)+"\n")
print(json.dumps(facts,indent=2,sort_keys=True))
