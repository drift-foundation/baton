"""Claim-255929: what an altered `kind` does at the POOLED worker directly.

The router now binds stage_id/episode/kind against the recorded allocation. A
caller holding the worker's own `_Operations` bypasses that, so this measures
what the composition itself does -- rather than my assuming it either way.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import test_routed_abandonment                                 # noqa: E402


class Probe(test_routed_abandonment.TheRoutedAbandonmentReachesTheAllocatedWorker):
    def runTest(self):
        from baton_v12.contracts import ContractRefusal
        job, control, composed, stage, attempt_id = self.started()
        del job, control
        owners = [one["operations"] for one in composed.workers]
        [operations] = [one for one in owners
                        if getattr(one, "_worker", None) is not None
                        and attempt_id in getattr(one._worker.stage,
                                                  "_prepared", {})]
        seen = []
        for member, value in (("kind", "review"),
                              ("stage_id", "job-a:review"),
                              ("episode", (stage.get("episode") or 0) + 7)):
            try:
                operations.abandon_attempt(
                    attempt_id=attempt_id, reason="probe",
                    stage=dict(stage, **{member: value}))
                seen.append((member, "accepted"))
            except ContractRefusal as refusal:
                seen.append((member, refusal.category, refusal.code,
                             refusal.message[:130]))
            except Exception as other:
                seen.append((member, type(other).__name__, str(other)[:130]))
        print(json.dumps({"outcomes": seen,
                          "prepared_members": sorted(
                              operations._worker.stage._prepared[attempt_id])},
                         indent=2, default=str))


if __name__ == "__main__":
    case = Probe()
    outcome = case.run()
    for _one, text in outcome.errors + outcome.failures:
        print(text, file=sys.stderr)
