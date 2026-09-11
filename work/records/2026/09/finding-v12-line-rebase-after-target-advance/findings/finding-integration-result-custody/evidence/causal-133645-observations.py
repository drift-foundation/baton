"""The four causal observations, DUMPED from the case that produces them.

Section 4 requires the actual base-fail / isolated-pass / combined-pass and a
separate combined-fail output rather than canned owner answers. This runs the
same `CausalEvidenceSurvivesComposition` fixture the test module uses and
prints exactly what the pinned harness answered in each content state, so the
handoff carries the outputs and not a description of them.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = "/home/sl/src/baton/v12/python"
sys.path.insert(0, os.path.join(PYTHON, "src"))
sys.path.insert(0, PYTHON)

from tests.integration.test_reconciliation import (  # noqa: E402
    HARNESS, CausalEvidenceSurvivesComposition)


class Dump(CausalEvidenceSurvivesComposition):
    def runTest(self):
        pass


case = Dump()
case.setUp()
try:
    held, observed = case.three()
    answers = {
        "pinned_harness": HARNESS,
        "submission_base": case.base,
        "target_after_the_first_job": case.advanced,
        "result": {"result_id": held["result_id"],
                   "state": held["state"],
                   "target_revision": held["target_revision"],
                   "prepared_head": held["prepared"]["head"],
                   "prepared_tree": held["prepared"]["tree"],
                   "content": held["prepared"]["content"],
                   "content_digest": held["content_digest"]},
        "observations": observed,
    }
    # THE SEPARATE COMBINED-FAIL CONTROL. A third Job changes `scale.py`,
    # which Job B never touched, so the merge is clean and the combined
    # result is still wrong.
    moved = case.advance("scale.py", "SCALE = 2\n")
    again = case.prepare()
    answers["combined_fail"] = {
        "target_after_the_third_job": moved,
        "result_id": again["result_id"],
        "state": again["state"],
        "prepared_head": again["prepared"]["head"],
        "observation": case.observe(
            case.materialize(case.workspace, again["prepared"]["head"])),
    }
finally:
    case.doCleanups()

print(json.dumps(answers, indent=2))
ok = (answers["observations"]["base"]["returncode"] != 0
      and answers["observations"]["base"]["harness_added"] is True
      and answers["observations"]["isolated"]["returncode"] == 0
      and answers["observations"]["combined"]["returncode"] == 0
      and answers["combined_fail"]["observation"]["returncode"] != 0
      and answers["combined_fail"]["result_id"] != answers["result"]["result_id"]
      and len({one["harness_digest"] for one in
               list(answers["observations"].values())
               + [answers["combined_fail"]["observation"]]}) == 1)
print("\nCAUSAL:", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)
