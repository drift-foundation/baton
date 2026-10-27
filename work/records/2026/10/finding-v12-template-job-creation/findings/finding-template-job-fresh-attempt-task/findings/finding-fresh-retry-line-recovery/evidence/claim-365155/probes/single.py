"""The one-producer pool, after the release: how far the retry gets."""
import json
import unittest

from baton_v12.authority import Authority
from baton_v12.job_manager import sweep, reconcile
from tests.job_manager import fixtures
from tests.tools import test_retry_task_lineage as lineage


class Probe(lineage.TheRetriedJobIsServedItsOwnTask):
    def runTest(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        out = {}
        said = []
        for _ in range(14):
            said.append(reconcile(held["jobs"], held["composed"],
                                  now=fixtures.NOW))
            said.append(sweep(held["jobs"], held["composed"],
                              now=fixtures.NOW))
        out["stages"] = self.stages(held["jobs"], held["composed"], fresh)
        out["stage"] = self.stage_of(held["jobs"], held["composed"], fresh)
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            out["gate"] = authority.project_work(self.work).get("gate")
        finally:
            authority.dispose()
        seen = []
        for report in said:
            for one in report["acts"]:
                if not one["stage_id"].startswith(fresh):
                    continue
                detail = one.get("detail")
                message = detail.get("message") if isinstance(detail, dict) \
                    else detail
                key = (one["act"], one["outcome"], message)
                if key not in seen:
                    seen.append(key)
        out["acts"] = seen
        rows = held["control"]._connection.execute(
            "SELECT line_id, state, current_checkpoint_id "
            "FROM review_lines").fetchall()
        out["lines"] = [dict(one) for one in rows]
        rows = held["control"]._connection.execute(
            "SELECT runtime_attempt_id, execution_runtime, "
            "worker_disposition, cleanup FROM attempts").fetchall()
        out["attempts"] = [dict(one) for one in rows]
        print(json.dumps(out, indent=2, default=str))


unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite([Probe()]))
