"""Why the retry's offer waits: what holds the Work after an unable ending."""
import json
import unittest

from baton_v12.authority import Authority
from baton_v12.job_manager import sweep, reconcile
from tests.job_manager import fixtures
from tests.tools import test_retry_task_lineage as lineage


class Probe(lineage.TheRetriedJobReachesItsOwnRuntimes):
    def runTest(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        out = {}
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            out["gate_after_ending"] = authority.project_work(self.work).get("gate")
        finally:
            authority.dispose()
        names = sorted(one["name"] for one in
                        held["control"]._connection.execute(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='table'").fetchall())
        out["tables"] = names
        for table in names:
            if "attempt" in table or "clean" in table or "runtime" in table:
                out[table] = [dict(one) for one in
                              held["control"]._connection.execute(
                                  f"SELECT * FROM {table}").fetchall()]
        seen = []
        for _ in range(12):
            seen.append(reconcile(held["jobs"], held["composed"],
                                  now=fixtures.NOW))
            seen.append(sweep(held["jobs"], held["composed"],
                              now=fixtures.NOW))
        out["retry_stage"] = self.stage_of(held["jobs"], held["composed"],
                                           fresh)
        out["retry_acts"] = [one for report in seen for one in report["acts"]
                             if one["stage_id"].startswith(fresh)]
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            out["gate_after_ticks"] = authority.project_work(self.work).get("gate")
        finally:
            authority.dispose()
        out["stages_after_ticks"] = self.stages(held["jobs"], held["composed"],
                                                fresh)
        # NOW DRIVE THE RETRY THE WAY THE FIRST ATTEMPT WAS DRIVEN.
        self.driven(held["jobs"], held["composed"], fresh)
        stage = self.stage_of(held["jobs"], held["composed"], fresh)
        out["retry_after_driven"] = stage
        attempt = stage.get("attempt_id")
        out["retry_attempt_id"] = attempt
        if attempt:
            self.proposing = True
            try:
                self.turn(held["jobs"], held["control"], held["composed"],
                          "implementation", attempt, job_id=fresh)
                out["turn"] = "performed"
            except BaseException as caught:
                out["turn"] = f"{type(caught).__name__}: {caught}"
            for _ in range(16):
                sweep(held["jobs"], held["composed"], now=fixtures.NOW)
                reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
            out["stages_after_turn"] = self.stages(held["jobs"],
                                                   held["composed"], fresh)
            out["review_stage"] = self.stage_of(held["jobs"],
                                                held["composed"], fresh,
                                                kind="review")
            rows = held["control"]._connection.execute(
                "SELECT line_id, state, current_checkpoint_id "
                "FROM review_lines").fetchall()
            out["lines"] = [dict(one) for one in rows]
            rows = held["control"]._connection.execute(
                "SELECT checkpoint_id, writer_id, state FROM "
                "line_checkpoints").fetchall()
            out["checkpoints"] = [dict(one) for one in rows]
            rows = held["control"]._connection.execute(
                "SELECT attachment_id, checkpoint_id, state FROM "
                "review_attachments").fetchall()
            out["attachments"] = [dict(one) for one in rows]
            rows = held["control"]._connection.execute(
                "SELECT runtime_attempt_id, execution_runtime, "
                "worker_disposition, cleanup FROM attempts").fetchall()
            out["attempts"] = [dict(one) for one in rows]
        print(json.dumps(out, indent=2, default=str))


unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite([Probe()]))
