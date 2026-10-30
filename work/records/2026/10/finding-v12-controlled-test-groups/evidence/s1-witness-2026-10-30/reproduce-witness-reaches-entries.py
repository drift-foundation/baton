"""W384870 S1 correction: the reviewer's spy reproduction, pointed at the NEW witnesses.

Run from v12/python with the prepared interpreter and PYTHONPATH=src:. (the script lives in the evidence folder). The spies
wrap both public entries under both names (the lifecycle suite's imported names
and the product module's), run each new witness, and require every spy to have
been CALLED while the witness passes -- the inverse of the reviewer's finding
against the blanket witness. No product files are edited.
"""
from contextlib import ExitStack
from unittest.mock import patch
import unittest
from tests.manager import test_boundary_inventory as inventory, test_review_cycles as lifecycle

for witness, entry in (("test_restore_abandoned_correction_profile_owner", "restore_abandoned_correction"),
                       ("test_settle_restoration_execution_profile_owner", "settle_restoration_execution")):
    with ExitStack() as stack:
        spies = {}
        for name in ("restore_abandoned_correction", "settle_restoration_execution"):
            spy = stack.enter_context(patch.object(lifecycle, name, wraps=getattr(lifecycle, name)))
            stack.enter_context(patch.object(inventory.review_cycles, name, spy))
            spies[name] = spy
        checks = stack.enter_context(patch.object(inventory.review_cycles, "_profile", wraps=inventory.review_cycles._profile))
        result = unittest.TestResult()
        inventory.StatedRules(witness).run(result)
        print(witness, "errors", result.errors, "failures", result.failures, "skipped", result.skipped)
        for name, spy in spies.items():
            print("  ", name, "calls", spy.call_count)
        print("   _profile calls", checks.call_count)
        assert not result.errors and not result.failures and not result.skipped
        assert spies[entry].call_count >= 4, f"{witness} did not reach {entry}"
        assert checks.call_count >= 3, f"{witness} did not reach _profile"
print("OK: both witnesses reach their entries and the profile check")
