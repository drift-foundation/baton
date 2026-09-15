"""Observe selected child admission with real disposable owners and fake engine/provider."""
import json
import sys
import unittest

from baton_v12.authority import Authority
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import TheComposedJobTraversesReviewAndAcceptance
from tools import stage_execution


class Selected(TheComposedJobTraversesReviewAndAcceptance):
    def serving(self, **members):
        return super().serving(integration_preparation=True, **members)


class ObserveChild(unittest.TestCase):
    def run_case(self, register):
        case = Selected()
        self.addCleanup(case.doCleanups)
        case.setUp()
        if register:
            authority = Authority.open(case.authority_path, expected_authority_uuid=case.config["authority_uuid"])
            try:
                authority.add_route_handler(stage_execution.PREPARATION_ROUTE, "baton.integrator")
            finally:
                authority.dispose()
        held = case.reviewed()
        preparation = held.composed.deployment._integration_operations._preparation
        observations = []
        for index in range(4):
            try:
                report = sweep(held.job, held.composed, now=fixtures.NOW)
                observations.append({"sweep": index, "acts": [{"stage": act["stage_id"], "act": act["act"], "outcome": act["outcome"], "message": (act.get("detail") or {}).get("message")} for act in report["acts"]]})
            except Exception as error:
                observations.append({"sweep": index, "exception": type(error).__name__, "message": str(error)})
            observations[-1]["completed_prepare_calls"] = len(preparation.started)
        print(json.dumps({"route_registered": register, "observations": observations}, indent=2), flush=True)

    def test_without_child_handler(self):
        self.run_case(False)

    def test_with_child_handler(self):
        self.run_case(True)


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ObserveChild))
sys.exit(not result.wasSuccessful())
