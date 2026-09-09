"""Quick read-only scanner diagnosis; no tests, stores or source substitution."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.manager import test_boundary_inventory as inventory

started = time.monotonic()
crossings = inventory._crossings()
sites = {}
for source, tree in inventory._sources():
    for site, node in inventory._functions(tree, source.name):
        if site not in ("authority_port.py:AuthorityPort.satisfy_gate",
                        "intake.py:discharge_quiescence_gate"):
            continue
        origins = inventory._origins(node, site, inventory._helper_returns())
        calls = []
        for piece in ast.walk(node):
            if isinstance(piece, ast.Call) and (
                    isinstance(piece.func, ast.Name) and piece.func.id == "performing"
                    or isinstance(piece.func, ast.Attribute) and piece.func.attr == "satisfy_gate"):
                calls.append({"line": piece.lineno, "call": ast.unparse(piece.func),
                              "lexical_capability": inventory._capability_call(piece),
                              "origin": inventory._source(piece, origins, site, inventory._helper_returns())})
        sites[site] = {"calls": calls,
                       "bindings": {name: sorted(inventory._origin_values(origins.get(name)))
                                    for name in ("performing", "answer", "answered")}}
try:
    entries = inventory.receiving_entries()
    census = {"entries": len(entries)}
except AssertionError as error:
    census = {"exception": type(error).__name__, "message": str(error)}
paths = ["v12/python/tests/manager/test_boundary_inventory.py",
         "v12/python/src/baton_v12/worker_manager/authority_port.py",
         "v12/python/src/baton_v12/worker_manager/intake.py"]
report = {"work": "W120204", "claim": 120206,
          "sha256": {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths},
          "satisfy_gate_crossing": crossings.get("satisfy_gate"),
          "sites": sites, "census": census, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
