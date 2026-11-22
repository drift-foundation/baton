"""K probes for W385624 candidate 5bc260b6 (review-only; deterministic; no live provider)."""
import json, unittest
from tests.job_manager import test_retained_recovery_admission as t
from baton_v12.job_manager import projection, submission, job_control


class P(t.RecoveryCase):

    def test_P1_successor_review_stage_is_immediately_queued(self):
        held = self.delivered()
        read = self.read(held["key"])
        code, answer = self.decide(held["key"], read)
        self.assertEqual(code, 0, answer)
        job_id = answer["successor"]["job_id"]
        rows = submission.stages_of(self.jobs, job_id)
        print("P1-ROWS", json.dumps([{k: r[k] for k in ("stage_id", "kind", "depends_on")} for r in rows]))
        print("P1-READINESS", json.dumps(answer["successor"]["readiness"], sort_keys=True))
        ops = getattr(self, "acts", None)
        try:
            states = projection.stage_states(self.jobs, ops)
            mine = {k: v["state"] for k, v in states.items() if k.startswith(job_id)}
            print("P1-STATE", json.dumps(mine))
            owed = projection.owed_acts(self.jobs, ops, held=states)
            print("P1-OWED", json.dumps([o for o in owed if job_id in json.dumps(o, default=str)], default=str)[:800])
        except Exception as e:  # report, do not hide
            print("P1-PROJECTION-ERROR", type(e).__name__, str(e)[:300])
            gates = projection.gates_of(dict(rows[0]), {})
            print("P1-GATES", gates, "=> queued" if all(g["open"] for g in gates) else "=> blocked")

    def test_P2_ordinary_create_may_select_recovery_profile(self):
        from tests.job_manager import test_creation as c
        case = c.CreationCase("setUp"); case.setUp()
        try:
            created = case.created(request=c.request(control={"profile": "stage1-verification-review/1"}))
            stages = [r["kind"] for r in submission.stages_of(case.jobs, created["job_id"])]
            print("P2-ADMITTED", created["control"]["profile"], stages)
        except Exception as e:
            print("P2-REFUSED", type(e).__name__, str(e)[:300])
        finally:
            case.doCleanups()


if __name__ == "__main__":
    unittest.main(verbosity=2)


class P3(t.RecoveryCase):

    def test_P3_real_sweep_offers_the_successor_review(self):
        from baton_v12.job_manager import sweep
        from tests.job_manager import fixtures
        held = self.delivered()
        read = self.read(held["key"])
        code, answer = self.decide(held["key"], read)
        self.assertEqual(code, 0, answer)
        job_id = answer["successor"]["job_id"]
        ops = fixtures.FakeOperations(authority_uuid=self.AUTHORITY)
        try:
            report = sweep(self.jobs, ops, now=t.NOW)
            mine = [a for a in report.get("acts", []) if job_id in json.dumps(a, default=str)]
            print("P3-SWEEP-ACTS", json.dumps(mine, default=str, sort_keys=True)[:1500])
            calls = [c for c in getattr(ops, "calls", []) if job_id in json.dumps(c, default=str)]
            print("P3-OPS-CALLS", json.dumps(calls, default=str)[:800])
            states = projection.stage_states(self.jobs, ops)
            print("P3-STATE", json.dumps({k: v["state"] for k, v in states.items() if k.startswith(job_id)}))
        except Exception as e:
            print("P3-SWEEP-ERROR", type(e).__name__, str(e)[:500])
