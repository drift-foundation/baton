"""Independent finite-fragment review, budget10s. No suite/runtime operations."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]

def module(path):
    spec = importlib.util.spec_from_file_location("tests.manager.review_inventory", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

candidate = HERE / "correction-116178/candidate.py"
prior = HERE / "candidate.py"
live = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
assert live.read_bytes() == candidate.read_bytes()
facts = {"hashes":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, prior, live)}}
branch = '''
def _view(row):
    return row["claim_generation"]
def public(connection, condition):
    if condition:
        row = connection.execute("SELECT * FROM offers").fetchone()
    else:
        row = None
    if row is not None:
        return _view(row)
'''
branch_reversed = '''
def _view(row):
    return row["claim_generation"]
def public(connection, condition):
    if not condition:
        row = None
    else:
        row = connection.execute("SELECT * FROM offers").fetchone()
    if row is not None:
        return _view(row)
'''
shadow = '''
from .producer import row as read
def _view(row):
    return row["claim_generation"]
def public(connection, read):
    return _view(read(connection))
'''
producer = '''
def row(connection):
    return connection.execute("SELECT * FROM offers").fetchone()
'''
reassign = '''
def _record(*, envelope):
    return envelope["record"]
def public(row):
    row = _record(envelope=row)
    return row["identity"]
'''
nested_import = '''
from .producer import row as read
def _view(row):
    return row["claim_generation"]
def public(connection):
    def unused():
        from .unrelated import row as read
        return read
    return _view(read(connection))
'''

for name, path in (("prior",prior),("candidate",candidate)):
    b = module(path)
    result = {}
    for label, source in (("branch",branch),("equivalent_reversed_branch",branch_reversed),("shadow",shadow),("nested_import",nested_import)):
        fragments = [(Path("producer.py"),ast.parse(producer)),(Path("sample.py"),ast.parse(source))]
        if label == "nested_import":
            fragments.append((Path("unrelated.py"),ast.parse(producer.replace("FROM offers", "FROM unrelated_offers"))))
        returns = b._returned_origins(fragments)
        tree = fragments[1][1]
        site = "sample.py:public"
        node = dict(b._functions(tree,"sample.py"))[site]
        origins = b._origins(node,site,returns)
        entries = sorted(b._through_helpers({},site,node,origins,b._helpers(tree,"sample.py"),returns=returns))
        result[label] = {"origins":origins,"entries":entries}
    if name == "candidate":
        result["reassignment_return"] = b._returned_origins([(Path("sample.py"),ast.parse(reassign))])["sample.py:public"][0]
    facts[name] = result

classes = lambda path: {n.name:ast.dump(n) for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef)}
old, new = classes(HERE / "before.py"), classes(candidate)
facts["changed_original_classes"] = [n for n,v in old.items() if new.get(n)!=v]
facts["original_class_count"] = len(old)
(HERE / "review-116214.json").write_text(json.dumps(facts,indent=2,sort_keys=True)+"\n")
print(json.dumps(facts,indent=2,sort_keys=True))
