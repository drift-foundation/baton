"""W115824 diagnosis only: eight named non-engine checks.

Budget: 60 seconds; no Docker or whole-suite execution.
Question: do retained catalog/inventory diagnostics still hold?
"""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
PYTHON = ROOT / "v12/python"
sys.path[:0] = [str(PYTHON), str(PYTHON / "src")]
from tests.manager import test_boundary_inventory as b

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

started = datetime.now(timezone.utc).isoformat()

names = [
    "tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_every_v12_test_module_is_registered_exactly_once",
    "tests.authority.test_catalog.TheMigrationChecklistIsRead.test_the_suite_is_one_gate_and_not_a_pile_of_files",
    *["tests.manager.test_boundary_inventory.EveryProbeProvesItArrived." + x for x in (
        "test_every_declared_probe_reaches_its_named_boundary", "test_every_owned_entry_has_exactly_one_probe", "test_the_missing_probe_check_can_actually_fail")],
    *["tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner." + x for x in (
        "test_every_boundary_call_belongs_to_an_entry_or_is_declared", "test_every_receiving_entry_has_an_owning_validator", "test_the_universe_sees_every_persisted_column_that_is_read")],
]
unittest.TestCase.maxDiff = None  # diagnostic rendering only; source/assertions unchanged
with (OUT / "focused.txt").open("w") as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))

case = b.EveryProbeProvesItArrived()
case.setUp()
try:
    wanted, declared = case.expected(), set(case.all_probes())
finally:
    case.doCleanups()
owners = b.EveryReceivingEntryHasOneOwner()
unowned = sorted(entry for entry in b.receiving_entries() if owners.owner_of(entry)[0] is None)
missing, orphan_probes = sorted(wanted - declared), sorted(declared - wanted)
def grouped(entries):
    return dict(sorted(Counter(entry[1].split(":")[0] for entry in entries).items()))
column_sites = []
for source, tree in b._sources():
    for site, node in b._functions(tree, source.name):
        for piece in ast.walk(node):
            read = b._member_read(piece)
            if read and read[1] in ("operation_id", "settled_at"):
                column_sites.append([site, piece.lineno, ast.unparse(piece)])
write("inventory.json", {"observed_at": started, "missing_probes": missing, "orphan_probes": orphan_probes,
      "unowned": unowned, "missing_by_module": grouped([e for e, label in missing]),
      "unowned_by_module": grouped(unowned), "column_read_sites": column_sites,
      "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)})
paths = [PYTHON / "tests/manager/test_boundary_inventory.py", PYTHON / "tools/parallel_test.py",
         *[PYTHON / p for p in ("tests/authority/test_catalog.py", "tests/authority/test_work_label_exposure.py", "tests/integration/test_driver.py", "tests/job_manager/test_review_driver.py", "tests/manager/test_credentials_engine.py", "tests/manager/test_output_custody_engine.py", "tests/manager/test_worker_container.py")],
         *sorted((PYTHON / "src/baton_v12/worker_manager").glob("*.py"))]
write("hashes.json", {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
print(json.dumps({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "missing_probes":len(missing), "orphan_probes":len(orphan_probes), "unowned":len(unowned)}))
