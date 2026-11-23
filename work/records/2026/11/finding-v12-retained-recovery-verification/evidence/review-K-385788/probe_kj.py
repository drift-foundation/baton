"""K independent probes for W385625 joined candidate 5cb76d82 (not candidate tests)."""
import json, os, tempfile, unittest
from unittest import mock
import baton_v12.job_manager as jm
from baton_v12.job_manager import projection
from tests.job_manager import test_retained_recovery_execution as T


class KJ(T.RetainedRecoveryReachesTheIndependentReviewer):
    def captured(self, **named):
        reports = []
        real = jm.sweep
        def sweep(jobs, operations, **kw):
            out = real(jobs, operations, **kw)
            reports.append((jobs, operations, out))
            return out
        with mock.patch.object(jm, "sweep", sweep):
            self.connected_review(**named)
        jobs, operations, _ = reports[-1]
        held = projection.stage_states(jobs, operations)
        review = {k: (v.get("state"), v.get("owed")) for k, v in held.items() if k.endswith("/review")}
        tail = [o for (_, _, r) in reports[-8:] for key in ("started", "ended") for o in r.get(key, []) if o.get("outcome") != "performed"]
        return review, tail

    def test_KJ1_missing_binding_end_state(self):
        review, tail = self.captured(evidence="missing")
        print("\nKJ1 review stages:", review)
        print("KJ1 last-8-tick non-performed outcomes:", json.dumps(tail)[:1500])

    def test_KJ2_wrong_binding_end_state(self):
        review, tail = self.captured(evidence="wrong")
        print("\nKJ2 review stages:", review)
        print("KJ2 last-8-tick non-performed outcomes:", json.dumps(tail)[:1500])


class KJWorker(unittest.TestCase):
    def report(self, document):
        import claude_agent
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as room:
            with open(os.path.join(room, claude_agent.REVIEW_REPORT), "w") as f:
                json.dump(document, f)
            return claude_agent._review_report(room)

    def test_KJ3_worker_report_vocabulary(self):
        base = {"schema": "baton.review-report/1", "verdict": "accepted", "findings": "x"}
        print("\nKJ3 three-member:", self.report(base))
        print("KJ3 ordinary + recovery_digest (no recovery input):", self.report(dict(base, recovery_digest="sha256:" + "a" * 64)))
        print("KJ3 malformed digest:", self.report(dict(base, recovery_digest="abc")))
        print("KJ3 fifth member:", self.report(dict(base, extra=1)))


if __name__ == "__main__":
    unittest.main()


class KJ4(T.RetainedRecoveryReachesTheIndependentReviewer):
    def test_KJ4_missing_binding_full_report_and_status(self):
        reports = []
        real = jm.sweep
        def sweep(jobs, operations, **kw):
            out = real(jobs, operations, **kw)
            reports.append((jobs, operations, out))
            return out
        with mock.patch.object(jm, "sweep", sweep):
            self.connected_review(evidence="missing")
        jobs, operations, last = reports[-1]
        print("\nKJ4 last report:", json.dumps(last, default=str)[:3000])
        st = jm.status(jobs, operations, observed_at=self.now)
        for job in st["jobs"]:
            if job.get("job_id", "").startswith("recovery"):
                print("KJ4 status job:", json.dumps(job, default=str)[:3000])
