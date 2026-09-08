"""Independent local-list alias fragments; budget10s, no suite/runtime calls."""
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
candidate = HERE / "correction-116609/candidate.py"
live = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
assert candidate.read_bytes() == live.read_bytes()
spec = importlib.util.spec_from_file_location("tests.manager.review_inventory", candidate)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
prefix = '''
def _view(mount):
    return mount["source"], mount["target"], mount["writable"]
def public(adapter, other, condition):
    landing = []
    for mount in getattr(adapter, "mounts", None):
        landing.append(mount)
'''
cases = {
    "definite_clear": "    alias = landing\n    alias.clear()\n",
    "external_or_local_clear": "    alias = landing\n    if condition:\n        alias = other\n    alias.clear()\n",
    "reversed_external_or_local_clear": "    alias = other\n    if condition:\n        alias = landing\n    alias.clear()\n",
    "two_local_lists_clear": "    alias = landing\n    if condition:\n        alias = []\n    alias.clear()\n",
    "external_clear": "    alias = other\n    alias.clear()\n",
}
expected_mounts = sorted(("caller","sample.py:public",f"adapter.mounts.{member}") for member in ("source","target","writable"))
facts = {"hashes":{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (candidate,live,HERE / "before.py")},"cases":{}}
start = time.monotonic()
for name, middle in cases.items():
    source = prefix + middle + "    _view(landing[0])\n"
    tree = ast.parse(source)
    returned = b._returned_origins([(Path("sample.py"),tree)])
    node = dict(b._functions(tree,"sample.py"))["sample.py:public"]
    origins = b._origins(node,"sample.py:public",returned)
    observed = sorted(b._through_helpers({},"sample.py:public",node,origins,b._helpers(tree,"sample.py"),returns=returned))
    expected = [] if name == "definite_clear" else expected_mounts
    facts["cases"][name] = {"source":source,"observed":observed,"expected":expected,"matches":observed==expected}
classes = lambda path: {n.name:ast.dump(n) for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef)}
old,new = classes(HERE / "before.py"),classes(candidate)
facts["baseline_class_count"] = len(old)
facts["changed_baseline_classes"] = [name for name,value in old.items() if new.get(name)!=value]
assert all(case["matches"] for case in facts["cases"].values()), facts["cases"]
assert not facts["changed_baseline_classes"]
facts["all_retained_cases_pass"] = True
facts["elapsed_seconds"] = time.monotonic()-start
(HERE / "review-116630.json").write_text(json.dumps(facts,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:value for key,value in facts.items() if key!="cases"},indent=2))
print(json.dumps({name:{key:value for key,value in data.items() if key!="source"} for name,data in facts["cases"].items()},indent=2))
