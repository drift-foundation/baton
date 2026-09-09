"""Do W124784's branch or W124782's landed intake fix explain the five
test_stage_execution failures? Run them with the new branch neutralised."""
import unittest
from unittest import mock

from baton_v12.job_manager import review_driver

NAMES = [
    "tests.tools.test_stage_execution.TheComposedEndingIsOrderedAndSettledFromItsOwnRecord.test_a_reconstructed_manager_re_enters_the_same_ending",
    "tests.tools.test_stage_execution.TheComposedEndingIsOrderedAndSettledFromItsOwnRecord.test_the_historical_entry_reconstructs_no_mount_or_credential",
    "tests.tools.test_stage_execution.TheComposedEndingIsOrderedAndSettledFromItsOwnRecord.test_the_historical_operands_come_from_the_recorded_obligation",
    "tests.tools.test_stage_execution.TheComposedEndingIsOrderedAndSettledFromItsOwnRecord.test_the_recovered_writer_is_the_attempts_and_not_the_lines_pointer",
    "tests.tools.test_stage_execution.TheDischargeReceiptIsNeverJournalled.test_the_gate_is_cleared_and_no_discharge_is_recorded",
]

for label, patched in (("branch live", False), ("branch neutralised", True)):
    suite = unittest.defaultTestLoader.loadTestsFromNames(NAMES)
    result = unittest.TestResult()
    if patched:
        with mock.patch.object(review_driver, "_fence_settled",
                               return_value=False):
            suite.run(result)
    else:
        suite.run(result)
    print(f"{label}: run={result.testsRun} failures={len(result.failures)} "
          f"errors={len(result.errors)}")
