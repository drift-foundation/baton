"""Source-only inventory comparison, not passing product acceptance."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tests.manager import test_boundary_inventory as inventory


class Compare(unittest.TestCase):
    def test_compare_exact_prechange_source(self):
        package = inventory.PACKAGE
        with tempfile.TemporaryDirectory(prefix="w32577-inventory-") as temporary:
            baseline = Path(temporary) / "worker_manager"
            shutil.copytree(package, baseline, ignore=shutil.ignore_patterns("__pycache__", "deadlines.py"))
            path = baseline / "attempts.py"
            source = path.read_text().replace(
                "def request_runtime_start(store, adapter, *, attempt_id, inputs=None, deadline_policy=None):",
                "def request_runtime_start(store, adapter, *, attempt_id, inputs=None):")
            source = source.replace('    # W32577: validate an existing immutable selection before the mutable-axis\n    # refusal, including retries that omit an earlier selected deadline.\n    from . import deadlines\n    deadlines._selection(store, attempt, deadline_policy)\n', '')
            source = source.replace('    deadlines._pin_start(store, attempt, deadline_policy)\n', '')
            source = source.replace('        deadlines._start_allowed(store, _require_attempt(store, attempt_id), deadline_policy)\n', '')
            path.write_text(source)
            path = baseline / "documents.py"
            path.write_text(path.read_text().split('\n\n# W32577. Closed manager-local')[0])
            path = baseline / "oci.py"
            source = path.read_text()
            start, end = source.index('    def destroy_deadline('), source.index('    def _removed(')
            path.write_text(source[:start] + source[end:])
            path = baseline / "intake.py"
            source = path.read_text()
            start, end = source.index('def _authorize_deadline_cleanup('), source.index('def _settle_recordless_cleanup(')
            path.write_text(source[:start] + source[end:])
            expected = {
                "attempts.py": "8c321ac7d9c1c5764c4f181e50a1e99d911c481dad0c20ea1ac11d7a2b349730",
                "documents.py": "b3fc43f26ffef5a76f1329b273ea722f04c4544b722511c681c3c1a0418b20bd",
                "intake.py": "d326fe41d0ad8ca90950be9735f4c05b1c537e70e6827f760867969830eae7b7",
                "oci.py": "68bb8831331ec1ac07b7b6bdb8a559573be348fe80ba796e50607d4b94af7b2f"}
            for name, digest in expected.items():
                self.assertEqual(hashlib.sha256((baseline / name).read_bytes()).hexdigest(), digest, name)

            def measure(root):
                inventory.PACKAGE = root
                for value in vars(inventory).values():
                    if hasattr(value, "cache_clear"):
                        value.cache_clear()
                case = inventory.EveryReceivingEntryHasOneOwner()
                entries = inventory.receiving_entries()
                records = inventory.boundary_occurrences()
                claims = inventory._boundary_claims(records, entries, inventory.DELEGATED)
                _, residual = inventory._account_boundary_calls(records, claims, inventory.NOT_AN_ENTRY)
                return (set(entry for entry in entries if case.owner_of(entry)[0] is None),
                        {(row.site, row.kind, row.label) for row in residual})

            try:
                prior, prior_orphans = measure(baseline)
                current, current_orphans = measure(package)
            finally:
                inventory.PACKAGE = package
            report = {"baseline_unowned_count": len(prior), "current_unowned_count": len(current),
                      "introduced": sorted(current - prior), "removed": sorted(prior - current),
                      "baseline_orphan_count": len(prior_orphans), "current_orphan_count": len(current_orphans),
                      "introduced_orphans": sorted(current_orphans - prior_orphans),
                      "baseline_hashes": expected}
            (Path(__file__).parent / "inventory-audit-162766.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2))
