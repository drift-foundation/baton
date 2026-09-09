"""Targeted new alias-lifetime cases; exclusive evidence, no source edits."""
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.manager.test_boundary_inventory import OptionalCapabilityAliasesKeepTheirCrossing

started = time.monotonic()
case = OptionalCapabilityAliasesKeepTheirCrossing()
cases = {
    "ordinary": '''
def public(session, other):
    performing = getattr(session, "release_token", None)
    answer = performing(other)
    return answer["kind"]
''',
    "argument_rebinds_alias": '''
def public(session, other):
    performing = getattr(session, "release_token", None)
    answer = performing((performing := other))
    return answer["kind"]
''',
    "delete_attribute_keeps_callable": '''
def public(session):
    performing = getattr(session, "release_token", None)
    del performing.cached
    return performing({})["kind"]
''',
    "delete_subscript_keeps_callable": '''
def public(session, other):
    performing = getattr(session, "release_token", None)
    del other[performing]
    return performing({})["kind"]
''',
    "delete_binding_kills_callable": '''
def public(session):
    performing = getattr(session, "release_token", None)
    del performing
    return performing({})["kind"]
''',
}
results = {}
for name, source in cases.items():
    crossings, entries = case.model(source)
    results[name] = {"source": source, "crossings": crossings,
                     "injected": sorted(case.injected(entries))}
path = root / "v12/python/tests/manager/test_boundary_inventory.py"
report = {"work": "W120204", "claim": 120317,
          "candidate_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
          "question": "Does callable provenance survive argument side effects and deletion that does not rebind the callable?",
          "results": results, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
