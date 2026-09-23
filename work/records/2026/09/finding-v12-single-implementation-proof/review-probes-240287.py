"""Independent entrypoint/preparation probes; disposable state only."""
import io
import json
from pathlib import Path
import tempfile
import time
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.authority.core import UNESTABLISHED_TARGET
from tests.job_manager import fixtures
from tools import stage_execution
import baseline
from test_entrypoints import TheDocumentedSupervisorRunsThroughMain

HERE = Path(__file__).resolve().parent
observed = {}
started = time.monotonic()

# The actual Authority acts printed in operator step 5a, on a new test store.
with tempfile.TemporaryDirectory(prefix="w239528-review-240287-") as root:
    authority = Authority.create(str(Path(root) / "authority.sqlite3"),
                                 authority_uuid=fixtures.UUID)
    try:
        authority.create_work(fixtures.WORK_A, "impl",
                              contract="v12-assignment-1",
                              operation_id="w239528-single-implementation")
        scope = authority.project_work(fixtures.WORK_A)["scope"]
        authority.add_route_handler("impl", "baton.implementer")
        authority.add_route_handler("integration", "baton.integrator")
        for who, capability in (("baton.verifier", "verify"),
                                 ("baton.reviewreceipt", "review"),
                                 ("baton.approver", "approve"),
                                 ("baton.integrator", "integrate")):
            authority.grant_capability(who, capability, scope=scope)
        observed["step5a_canonical_target"] = authority.canonical_target()
        assert authority.canonical_target() == UNESTABLISHED_TARGET
    finally:
        authority.dispose()


class RealComposition(TheDocumentedSupervisorRunsThroughMain):
    def composing(self, driven):
        def compose(packet, job, control, stream):
            original = stage_execution.operations_from

            def at_engine_boundary(*args, **kwargs):
                kwargs.update(engine_run=self.engine,
                              credential_provider=lambda p, r: self.secret,
                              clock=lambda: fixtures.NOW)
                return original(*args, **kwargs)

            with mock.patch.object(stage_execution, "operations_from",
                                   side_effect=at_engine_boundary):
                composed = baseline._compose(packet, job, control, stream)
            self._composed = composed
            driven.append((job, control, composed))
            return composed
        return compose


for absent in (False, True):
    case = RealComposition("test_main_completes_one_implementation_and_exits_zero")
    try:
        case.setUp()
        if absent:
            authority = Authority.open(case.authority_path,
                expected_authority_uuid=case.config["authority_uuid"])
            try:
                authority.set_policy("canonical_target", UNESTABLISHED_TARGET)
            finally:
                authority.dispose()
        packet = case.main_packet(bounds=dict(case.packet["bounds"],
                                             total_seconds=5, cleanup_seconds=2))
        code, output, driven = case.run_main(packet)
        outcome = json.loads(Path(packet["outcome_path"]).read_text())
        observed["real_compose_" + ("unestablished_target" if absent else "positive")] = {
            "exit_code": code, "state": outcome["state"],
            "stopped": outcome["stopped"], "held_because": outcome["held_because"],
            "outstanding_cleanup": outcome["outstanding_cleanup"],
            "stage_states": outcome["stage_states"]}
        # Both settle: this implementation-only stage retains a proposal;
        # canonical-target publication is a later stage. Do not mistake a
        # missing later-stage prerequisite for a baseline failure.
        assert code == 0, output
    finally:
        case.doCleanups()

# Demonstrates proxy scope, not an engine simulation: foreign ending/recovery
# calls cross the gate unchanged. The real manager invokes these store-wide.
operations = mock.Mock()
gate = baseline.AdmissionGate(operations, caps={"implementation": 1},
                              job_id="selected-job")
gate.recover(now=fixtures.NOW)
gate.refresh_runtime({"stage_id": "old-stage", "attempt_id": "old-attempt"})
gate.conclude({"stage_id": "old-stage", "attempt_id": "old-attempt"},
              {"job_id": "old-job"})
observed["foreign_operations_forwarded"] = [str(call) for call in operations.mock_calls]
assert operations.recover.called and operations.conclude.called
observed["seconds"] = time.monotonic() - started
observed["scope"] = "Disposable fixtures only; no deployed store, provider or engine."
(HERE / "review-probes-240287.json").write_text(json.dumps(observed, indent=2) + "\n")
print(json.dumps(observed, indent=2))
