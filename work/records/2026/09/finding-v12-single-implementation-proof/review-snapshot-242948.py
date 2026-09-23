"""Run actual main/compose while importing product code from the successor."""
import json
from pathlib import Path
import time
from unittest import mock

from baton_v12.job_manager import review_driver
from tests.job_manager import fixtures
from tools import stage_execution
import baseline
from test_entrypoints import TheDocumentedSupervisorRunsThroughMain

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "MANAGER-SOURCE-242687.json").read_text())
selected = json.loads((HERE / "SELECTIONS-FAILURE-242687.json").read_text())["compose"]
snapshot = Path(manifest["path"]).resolve()
for module in (review_driver, stage_execution):
    assert Path(module.__file__).resolve().is_relative_to(snapshot), module.__file__


class SnapshotMain(TheDocumentedSupervisorRunsThroughMain):
    RUN = selected["run_id"]

    def run_implementation(self, control, composed, **kwargs):
        attempt = self.pending(composed, "implementation")
        if attempt is not None:
            self.turned.add(attempt)
            return self.turn(control, "implementation", attempt,
                self.mounted(composed, "implementation", attempt), edits={}, status=1)

    def composing(self, driven):
        def compose(packet, job, control, stream):
            original = stage_execution.operations_from

            def boundaries(*args, **kwargs):
                kwargs.update(engine_run=self.engine,
                              credential_provider=lambda p, r: self.secret,
                              clock=lambda: fixtures.NOW)
                return original(*args, **kwargs)

            with mock.patch.object(stage_execution, "operations_from", side_effect=boundaries):
                composed = baseline._compose(packet, job, control, stream)
            self._composed = composed
            driven.append((job, control, composed))
            return composed
        return compose


started = time.monotonic()
case = SnapshotMain("test_main_completes_one_implementation_and_exits_zero")
try:
    case.setUp()
    case.model_output = (HERE / "live-242687/logs/provider.stdout.log").read_text().strip()
    packet = case.main_packet(
        manager_source={key: manifest[key] for key in ("path", "packages", "file_count", "files")},
        code_boundary=str(snapshot), bounds=selected["bounds"])
    code, text, driven = case.run_main(packet)
    outcome = json.loads(Path(packet["outcome_path"]).read_text())
    assert code == 1 and outcome["state"] == "held", text
    assert outcome["stopped"] == "exceptional", text
    assert outcome["outstanding_cleanup"] == [], text
    assert outcome["workload"]["proposals"] == [], text
    assert outcome["workload"]["dispositions"][0]["disposition"] == "unable", text
    assert len(case.calls.read_text().splitlines()) == 1
    result = {"driver": review_driver.__file__, "stage": stage_execution.__file__,
              "exit_code": code, "bounds": packet["bounds"], "outcome": outcome,
              "seconds": time.monotonic() - started,
              "scope": "Actual baseline.main/_compose and successor product imports; disposable fixtures; provider replay and engine/credential boundaries simulated."}
    (HERE / "review-snapshot-242948.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("driver", "stage", "exit_code", "seconds", "bounds")}, indent=2))
finally:
    case.doCleanups()
