"""Independent review: actual factory defaults versus injected component control.

Run from v12/python with PYTHONPATH=src:tools:.; only the engine and credential
reader at single_worker's external boundary are controlled. No stage factory,
operations_from, port mapping or StageDeployment capability is patched.
"""
import json
import os
import unittest
from unittest.mock import patch

from tests.tools.test_stage_execution import TwoBoundJobsTraverseServingAndCorrection as Base
from tools import stage_execution, single_worker
from baton_v12.contracts import ContractRefusal


class FactoryDefaults(Base):
    def setUp(self):
        previous = os.getcwd()
        os.chdir("/tmp")
        self.addCleanup(os.chdir, previous)
        super().setUp()

    def serving(self, **members):
        self.engine = self.quiescing()
        job, control = self.stores("actual-factory")
        document = self.composed_document(line_declared_base=self.base, **members)
        for worker in document["workers"]:
            worker["deployment"]["credential_sources"] = os.path.join(self.root, "credential-registry")
        place = os.path.join(self.root, "factory-config.json")
        with open(place, "w") as writing:
            json.dump(document, writing)
        for boundary in (
            patch.object(single_worker, "_engine_run", self.engine),
            patch.object(single_worker, "UserCredentialSources", return_value=lambda *_: self.secret),
            patch.dict(os.environ, {stage_execution.CONFIG_ENV: place}),
        ):
            boundary.start()
            self.addCleanup(boundary.stop)
        composed = stage_execution.factory(job, control)
        self.addCleanup(composed.close)
        self._composed = composed
        return job, control, composed

    def test_actual_factory_keeps_required_capabilities_absent(self):
        # Composition is real; no need to spend a full lifecycle to prove
        # the constructor's deterministic precondition over these defaults.
        job, control, composed = self.serving_two(**self.traversing())
        deployment = composed.deployment
        self.assertIsNone(deployment._engine_run)
        self.assertIsNone(deployment._credential_provider)
        self.assertEqual(composed.integrator.ports, {"job-a": None, "job-b": None})
        with self.assertRaises(ContractRefusal) as caught:
            deployment.integration_port_for("job-a", line_id="unused-line", proposal_id="unused-proposal", canonical_target_id="target-a")
        self.assertEqual((caught.exception.category, caught.exception.code), ("refused", "capability"))
        self.assertIn("no engine run capability", caught.exception.message)
        print("ACTUAL FACTORY REFUSAL:", caught.exception.message, flush=True)


if __name__ == "__main__":
    suite = unittest.TestSuite([
        FactoryDefaults("test_actual_factory_keeps_required_capabilities_absent"),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
