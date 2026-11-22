"""K probes for W385624 correction 82e1cd87 (review-only; deterministic)."""
import json, unittest
from types import SimpleNamespace
from tests.job_manager import test_retained_recovery_admission as t
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import projection, submission, sweep
from tests.job_manager import fixtures


class C(t.RecoveryCase):

    def admitted(self):
        held = self.delivered()
        read = self.read(held["key"])
        code, answer = self.decide(held["key"], read)
        self.assertEqual(code, 0, answer)
        return answer["successor"]

    def test_C1_real_sweep_twice_no_offer_and_state(self):
        job_id = self.admitted()["job_id"]
        ops = fixtures.FakeOperations(authority_uuid=self.AUTHORITY)
        for _ in range(2):
            report = sweep(self.jobs, ops, now=t.NOW)
            print("C1-ACTS", json.dumps([a for a in report.get("acts", []) if job_id in json.dumps(a, default=str)]))
        states = projection.stage_states(self.jobs, ops)
        st = states[job_id + "/review"]
        print("C1-STATE", st["state"], json.dumps(projection.gates_of(st["stage"], states), sort_keys=True)[:400])
        print("C1-OPS", json.dumps([c for c in ops.calls if job_id in json.dumps(c, default=str)]))

    def test_C2_scheduler_admit_guard(self):
        job_id = self.admitted()["job_id"]
        from baton_v12.job_manager.scheduler import PooledManagerOperations
        stage = dict(submission.stages_of(self.jobs, job_id)[0])
        try:
            PooledManagerOperations.admit(SimpleNamespace(store=self.jobs), stage, {})
            print("C2-RECOVERY", "NOT REFUSED")
        except ContractRefusal as e:
            print("C2-RECOVERY", "refused", e.message)
        ordinary = dict(submission.stages_of(self.jobs, "job-a")[0])
        try:
            PooledManagerOperations.admit(SimpleNamespace(store=self.jobs), ordinary, {})
        except ContractRefusal as e:
            print("C2-ORDINARY", "refused?!", e.message)
        except AttributeError as e:
            print("C2-ORDINARY", "passed guard (reached allocation):", str(e)[:80])

    def test_C3_status_text_for_recovery_gate(self):
        job_id = self.admitted()["job_id"]
        from tools import job_observation
        ops = fixtures.FakeOperations(authority_uuid=self.AUTHORITY)
        states = projection.stage_states(self.jobs, ops)
        st = states[job_id + "/review"]
        stage = {"gates": projection.gates_of(st["stage"], states)}
        print("C3-STATUS-TEXT", repr(job_observation._reason(stage, st["state"])))

    def test_C4_ordinary_create_refused(self):
        from tests.job_manager import test_creation as c
        case = c.CreationCase("setUp"); case.setUp()
        try:
            case.created(request=c.request(control={"profile": "stage1-verification-review/1"}))
            print("C4", "ADMITTED")
        except ContractRefusal as e:
            print("C4", "refused", e.code, e.message[:120])
        finally:
            case.doCleanups()


if __name__ == "__main__":
    unittest.main(verbosity=2)
