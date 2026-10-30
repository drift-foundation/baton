"""Run from v12/python with the prepared interpreter and PYTHONPATH=src.
Set TMPDIR to a fresh disk-backed scratch directory. No product files are edited.
"""
from contextlib import ExitStack
from unittest.mock import patch
import unittest
from tests.manager import test_boundary_inventory as inventory, test_review_cycles as lifecycle

with ExitStack() as stack:
    spies = {}
    for name in ("restore_abandoned_correction", "settle_restoration_execution"):
        spy = stack.enter_context(patch.object(lifecycle, name, wraps=getattr(lifecycle, name)))
        stack.enter_context(patch.object(inventory.review_cycles, name, spy))
        spies[name] = spy
    result = unittest.TestResult()
    inventory.StatedRules("test_review_cycle_stated_owners").run(result)
    print("errors", result.errors, "failures", result.failures)
    for name, spy in spies.items():
        print(name, "calls", spy.call_count)
    assert not result.errors and not result.failures
    assert all(spy.call_count == 0 for spy in spies.values()), "the witness now reaches an affected entry; reassess"
