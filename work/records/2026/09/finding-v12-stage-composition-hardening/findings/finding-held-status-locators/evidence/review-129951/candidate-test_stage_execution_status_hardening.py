"""W129844: configured read-only status over a real uncertain integration.

The lifecycle fixture is composed explicitly so unittest runs only this pair.
The owning record is finding-v12-stage-composition-hardening/findings/
finding-held-status-locators under work/records/2026/09.
"""

from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import unittest
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import IntegrationStore, entries_of, target_of
from baton_v12.job_manager import scheduler
from baton_v12.worker_manager import attempt_activity_of, attempt_runtime_of
from baton_v12.worker_manager.output import frozen_output_of
from tools import job_manager, single_worker, stage_execution
from tests.job_manager.fixtures import NOW
from tests.tools import test_stage_execution as assembly


class HeldIntegrationStatus(unittest.TestCase):

    def setUp(self):
        self.evidence = {}
        self.addCleanup(self.record_evidence)
        self.fixture = assembly.OrdinaryTerminalLifecycle(methodName="runTest")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.held = self.fixture.answered_integration(behavior="index")
        self.fixture.engine.stopped = True
        self.fixture.tick(self.held)
        self.deployment = self.fixture.deployment_of(self.held)
        self.configuration = Path(self.fixture.root) / "held-status.json"
        self.document = self.fixture.composed_document(line_declared_base=self.fixture.base)
        self.configuration.write_text(json.dumps(self.document))
        self.before = self.owners()
        self.assertEqual(self.before["entry"]["state"], "held")
        self.assertEqual(self.before["target"]["state"], "blocked")
        self.assertIsNone(self.before["handoff"])
        self.protected = [self.fixture.authority_path, self.fixture.integration_store,
                          self.fixture.job_path, self.fixture.control_path]
        self.database_before = self.database_snapshot()
        self.evidence["owners_before"] = self.before

    def record_evidence(self):
        destination = os.environ.get("BATON_STATUS_HARDENING_EVIDENCE")
        if destination:
            (Path(destination) / (self._testMethodName + ".json")).write_text(
                json.dumps(self.evidence, indent=2) + "\n")

    def database_snapshot(self):
        return {path: {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                       "mode": oct(os.stat(path).st_mode & 0o777)} for path in self.protected}

    def owners(self):
        target = self.deployment.given["canonical_target_id"]
        [entry] = entries_of(self.deployment.integration, target)
        attempt = self.held.integration_attempt
        return {"entry": entry, "target": target_of(self.deployment.integration, target),
                "runtime": attempt_runtime_of(self.held.control, attempt),
                "activity": attempt_activity_of(self.held.control, attempt),
                "output": frozen_output_of(self.held.control, attempt),
                "allocation": scheduler.allocation_of(self.held.job, attempt),
                "work": self.deployment.authority.project_work(self.fixture.work),
                "handoff": self.deployment.authority.operation_result("integration-pass:" + attempt)}

    def read_status(self):
        stream = io.StringIO()
        self.evidence["stdout"] = ""
        with ExitStack() as guards:
            for owner, name in ((Authority, "open"), (Authority, "session"),
                    (IntegrationStore, "open"), (stage_execution, "operations_from"),
                    (stage_execution.StageExecution, "launch"),
                    (stage_execution.StageExecution, "conclude"),
                    (stage_execution.Integration, "run"), (stage_execution.Integration, "finish"),
                    (single_worker, "worker_preflight"), (scheduler, "activate_pool"),
                    (self.held.integration_port, "refresh"), (self.held.integration_port, "prepare"),
                    (self.held.composed.sessions["integrator"], "pass_work")):
                guards.enter_context(mock.patch.object(owner, name, side_effect=AssertionError("status reached " + name)))
            guards.enter_context(mock.patch.object(stage_execution, "_checkout", return_value=self.fixture.checkout))
            guards.enter_context(mock.patch.dict(os.environ, {stage_execution.CONFIG_ENV: str(self.configuration)}))
            try:
                code = job_manager.main([
                    "--store", self.fixture.job_path, "--authority-uuid", self.fixture.config["authority_uuid"],
                    "--incarnation", "held-status-reader", "status", "--control", self.fixture.control_path,
                    "--observe", "tools.stage_execution:observing_factory"], clock=lambda: NOW, stream=stream)
            finally:
                self.evidence["stdout"] = stream.getvalue()
        self.assertEqual(code, 0)
        return json.loads(stream.getvalue())

    def assert_preserved(self):
        after = self.owners()
        databases = self.database_snapshot()
        self.evidence.update(owners_after=after, databases_before=self.database_before, databases_after=databases)
        self.assertEqual(after, self.before)
        self.assertEqual(databases, self.database_before)

    def test_configured_status_preserves_the_held_attempt_and_absent_logs(self):
        status = self.read_status()
        self.evidence["status"] = status
        [job] = status["jobs"]
        [stage] = [row for row in job["stages"] if row["kind"] == "integration"]
        expected = self.held.integration_stage
        self.assertEqual(job["job_id"], expected["job_id"])
        for name in ("job_id", "stage_id", "episode", "attempt_id", "offer_id"):
            self.assertEqual(stage[name], expected[name], name)
        self.assertEqual(stage["state"], "exceptional")
        self.assertEqual(stage["allocation"], self.before["allocation"])
        self.assertEqual(stage["runtime"]["assignment"], self.before["runtime"]["assignment"])
        self.assertEqual(stage["runtime"]["runtime_id"], self.before["runtime"]["runtime_id"])
        self.assertEqual(stage["runtime"]["execution_runtime"], self.before["runtime"]["execution_runtime"])
        self.assertEqual(stage["runtime"]["activity"], self.before["activity"])
        self.assertIsNone(self.before["output"])
        self.assertIsNone(stage["artifacts"])
        self.assertIsNone(stage["exchange"])
        self.assertEqual(stage["runtime"]["activity"], {
            "attempt_id": stage["attempt_id"], "bytes_observed": None, "observed_at": None})
        self.assert_preserved()

    def test_missing_coordinator_refuses_without_borrowing_another_result(self):
        missing = Path(self.fixture.root) / "absent-coordinator.sqlite3"
        self.document["integration_store"] = str(missing)
        self.configuration.write_text(json.dumps(self.document))
        with self.assertRaises(ContractRefusal) as caught:
            self.read_status()
        self.evidence["refusal"] = {"category": caught.exception.category, "code": caught.exception.code}
        self.assertEqual(self.evidence["stdout"], "")
        self.assertFalse(missing.exists())
        self.assert_preserved()
