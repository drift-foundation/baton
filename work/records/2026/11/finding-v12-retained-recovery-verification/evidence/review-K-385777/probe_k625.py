"""K independent probes for W385625 correction 6a3ad526 (not candidate tests)."""
import sys, unittest
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import retained_recovery, retained_verification
from tests.job_manager import test_retained_recovery_execution as T


class K(T.ExecutionCase):
    def cut(self, status=0):
        self.admitted(corrected=[sys.executable, "-c", f"raise SystemExit({status})"])
        self.materialize()
        with mock.patch.object(retained_recovery, "record_verification",
                               side_effect=RuntimeError("account cut")):
            with self.assertRaises(RuntimeError):
                self.execute()
        self.assertEqual(len(self.ran.calls), 1)

    def intent(self):
        return retained_recovery.successor_of(self.jobs, "D1")

    def test_K1_unaccounted_readiness_is_truthful_and_one_tick_completes(self):
        self.cut(0)
        r = retained_verification.execution_readiness(self.jobs, self.intent())
        print("\nK1 readiness:", r)
        self.assertEqual((r["state"], r["owed"], r["review"], r["verification"]),
                         ("unaccounted", "execute", "blocked", "passed"))
        self.assertNotIn("UNKNOWN", r.get("detail", ""))
        acts = self.ticked()
        print("K1 acts:", acts)
        self.assertEqual([(a["act"], a["outcome"]) for a in acts], [("execute", "executed")])
        self.assertEqual(len(self.ran.calls), 1)
        v = retained_recovery.verification_of(self.jobs, "recovery-D1")
        res = retained_verification.execution_result_of(self.jobs, "recovery-D1")
        self.assertEqual((v["outcome"], v["exit_status"], v["argv"], v["context_digest"], v["result_digest"], v["concluded_at"]),
                         (res["outcome"], res["exit_status"], res["argv"], res["context_digest"], res["retained"]["result_digest"], res["concluded_at"]))
        self.assertFalse(self.gate()["open"])
        acts = self.ticked()
        self.assertEqual([(a["act"], a["outcome"]) for a in acts], [("hand-off", "handed-off")])
        self.assertTrue(self.gate()["open"])
        self.assertEqual(len(self.ran.calls), 1)

    def test_K2_persistent_account_refusal_is_reported_not_silent(self):
        self.cut(0)
        refusal = ContractRefusal("integrity", "digest", "probe: custody moved")
        with mock.patch.object(retained_recovery, "record_verification", side_effect=refusal):
            for _ in range(3):
                acts = self.ticked()
                print("\nK2 acts:", acts)
                self.assertEqual([(a["act"], a["outcome"]) for a in acts], [("execute", "refused")])
        self.assertEqual(len(self.ran.calls), 1)
        self.assertIsNone(retained_recovery.verification_of(self.jobs, "recovery-D1"))
        self.assertFalse(self.gate()["open"])

    def test_K3_intent_without_result_stays_unknown_and_runs_nothing(self):
        self.admitted()
        self.materialize()
        with mock.patch.object(retained_verification, "_accounted", side_effect=RuntimeError("result cut")):
            with self.assertRaises(RuntimeError):
                self.execute()
        r = retained_verification.execution_readiness(self.jobs, self.intent())
        print("\nK3 readiness:", r)
        self.assertEqual((r["state"], r["owed"]), ("unknown", None))
        self.assertEqual(self.ticked(times=3), [])
        self.assertEqual(len(self.ran.calls), 1)
        self.assertFalse(self.gate()["open"])

    def test_K4_state_vocabulary(self):
        print("\nK4 EXECUTION_STATES:", retained_verification.EXECUTION_STATES)
        print("K4 'unaccounted' declared:", "unaccounted" in retained_verification.EXECUTION_STATES)

    def test_K5_configuration_is_closed(self):
        from tools import recovery_execution
        good = {"context": dict(T.CONTEXT), "declaration": self.declaration, "destination": "baton.slaw"}
        recovery_execution.configured_verification(good)
        for bad in (dict(good, extra=1), {k: v for k, v in good.items() if k != "destination"},
                    dict(good, context=dict(T.CONTEXT, schema="other/9"))):
            with self.assertRaises(ContractRefusal):
                recovery_execution.configured_verification(bad)


if __name__ == "__main__":
    unittest.main()
