"""Independent fragment projections; budget10s; no suite/runtime/store calls."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]

def module(path):
    spec = importlib.util.spec_from_file_location("tests.manager.review_inventory", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def serial(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(type(value).__name__)

# Read original reviewer fragments as literal AST assignments, without executing
# the earlier evidence writer or changing any prior evidence.
old_fragments = {}
for node in ast.parse((HERE / "review-116214.py").read_text()).body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        old_fragments[node.targets[0].id] = node.value.value

view = '''
def _view(row):
    return row["identity"]
'''
choose = '''
def _choose(connection, condition):
    if condition:
        return connection.execute("SELECT * FROM first").fetchone()
    return _later(connection)
'''
later = '''
def _later(connection):
    return connection.execute("SELECT * FROM second").fetchone()
'''
public = '''
def public(connection, condition):
    return _view(_choose(connection, condition))
'''
handler = view + '''
def public(connection):
    try:
        row = connection.execute("SELECT * FROM offers").fetchone()
        raise RuntimeError("inspect the adopted row")
    except RuntimeError:
        return _view(row)
'''
loop_break = view + '''
def public(connection, condition):
    row = None
    while condition:
        row = connection.execute("SELECT * FROM offers").fetchone()
        break
    return _view(row)
'''
loop_for = loop_break.replace("while condition:", "for item in condition:")
finally_unhandled = view + '''
def public(connection):
    row = connection.execute("SELECT * FROM first").fetchone()
    try:
        pass
    except RuntimeError:
        row = None
    else:
        raise ValueError("leave the else clause")
        row = connection.execute("SELECT * FROM second").fetchone()
    finally:
        _view(row)
'''
finally_else_call = view + '''
def public(connection):
    row = connection.execute("SELECT * FROM first").fetchone()
    try:
        pass
    except RuntimeError:
        row = None
    else:
        row = connection.execute("SELECT * FROM second").fetchone()
    finally:
        _view(row)
'''
exit_destinations = view + '''
def public(connection, supplied, condition):
    row = None
    for item in supplied:
        try:
            row = connection.execute("SELECT * FROM first").fetchone()
            if condition:
                break
            row = connection.execute("SELECT * FROM second").fetchone()
            return None
        finally:
            pass
    return _view(row)
'''
return_fallthrough = view + '''
def public(connection, condition):
    row = None
    try:
        if condition:
            row = connection.execute("SELECT * FROM first").fetchone()
            return None
        row = connection.execute("SELECT * FROM second").fetchone()
    finally:
        pass
    return _view(row)
'''
candidate = HERE / "correction-116443/candidate.py"
prior = HERE / "correction-116389/candidate.py"
live = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
assert candidate.read_bytes() == live.read_bytes()
facts = {"hashes":{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (candidate,prior,live)}}
start = time.monotonic()
for label, path in (("candidate",candidate),("prior",prior)):
    b = module(path)
    result = {}
    examples = {"late_return":view+choose+later+public, "reordered_definitions":view+later+choose+public, "exception_handler":handler, "finally_exit_destinations":exit_destinations, "finally_return_fallthrough":return_fallthrough, "while_break":loop_break, "for_break":loop_for, "finally_explicit_else_raise":finally_unhandled, "finally_implicit_else_exception":finally_else_call}
    if label == "candidate":
        examples.update({key:old_fragments[key] for key in ("branch","branch_reversed","shadow","nested_import","reassign")})
    for name, source in examples.items():
        fragments = [(Path("sample.py"),ast.parse(source))]
        if name in ("shadow","nested_import"):
            fragments.append((Path("producer.py"),ast.parse(old_fragments["producer"])))
        if name == "nested_import":
            fragments.append((Path("unrelated.py"),ast.parse(old_fragments["producer"].replace("FROM offers","FROM unrelated_offers"))))
        returned = b._returned_origins(fragments)
        tree = fragments[0][1]
        site = "sample.py:public"
        node = dict(b._functions(tree,"sample.py"))[site]
        origins = b._origins(node,site,returned)
        entries = sorted(b._through_helpers({},site,node,origins,b._helpers(tree,"sample.py"),returns=returned))
        result[name] = {"entries":entries,"return":returned.get(site),"choose_return":returned.get("sample.py:_choose")}
    facts[label] = result

classes = lambda path: {n.name:ast.dump(n) for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef)}
old, new = classes(HERE / "before.py"),classes(candidate)
facts["changed_original_classes"] = [name for name,value in old.items() if new.get(name)!=value]
facts["original_class_count"] = len(old)
expected = {
    "branch": [("adopted","sample.py:public","offers.claim_generation")],
    "branch_reversed": [("adopted","sample.py:public","offers.claim_generation")],
    "shadow": [],
    "nested_import": [("adopted","producer.py:row","offers.claim_generation")],
    "exception_handler": [("adopted","sample.py:public","offers.identity")],
    "while_break": [("adopted","sample.py:public","offers.identity")],
    "for_break": [("adopted","sample.py:public","offers.identity")],
    "late_return": [("adopted","sample.py:_choose","first.identity"),("adopted","sample.py:_later","second.identity")],
    "reordered_definitions": [("adopted","sample.py:_choose","first.identity"),("adopted","sample.py:_later","second.identity")],
    "finally_explicit_else_raise": [("adopted","sample.py:public","first.identity")],
    "finally_implicit_else_exception": [("adopted","sample.py:public","first.identity"),("adopted","sample.py:public","second.identity")],
    "finally_exit_destinations": [("adopted","sample.py:public","first.identity")],
    "finally_return_fallthrough": [("adopted","sample.py:public","second.identity")],
}
for name, entries in expected.items():
    assert facts["candidate"][name]["entries"] == sorted(entries), (name,facts["candidate"][name])
assert facts["candidate"]["reassign"]["return"][0] == "caller:row[record][identity]"
assert not facts["changed_original_classes"]
facts["all_retained_counterexamples_pass"] = True
facts["asserted_projection_cases"] = len(expected)
facts["elapsed_seconds"] = time.monotonic()-start
(HERE / "review-116481.json").write_text(json.dumps(facts,indent=2,sort_keys=True,default=serial)+"\n")
print(json.dumps(facts,indent=2,sort_keys=True,default=serial))
