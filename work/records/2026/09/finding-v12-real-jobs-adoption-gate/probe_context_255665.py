"""Claim-255665: what an ALTERED stage context actually does."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import test_abandonment                                        # noqa: E402


class Probe(test_abandonment.TheComposedAbandonmentIsCalled):
    def runTest(self):
        from baton_v12.contracts import ContractRefusal
        held, stage = self.faulted_with_stage("probe-context")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        seen = []
        for name, one in (("job_id", dict(stage, job_id="job-somebody-else")),
                          ("stage_id", dict(stage, stage_id="job-a:review")),
                          ("episode", dict(stage,
                                           episode=(stage.get("episode") or 0) + 7)),
                          ("kind", dict(stage, kind="review"))):
            try:
                operations.abandon_attempt(attempt_id=attempt_id,
                                           reason=self.REASON, stage=one)
                seen.append((name, "accepted"))
            except ContractRefusal as refusal:
                seen.append((name, refusal.category, refusal.code,
                             refusal.message[:110]))
            except Exception as other:
                seen.append((name, type(other).__name__, str(other)[:110]))
        print(json.dumps({"stage_members": sorted(stage),
                          "outcomes": seen,
                          "committed": bool(test_abandonment.intake_cleanup(
                              control, attempt_id, digest))},
                         indent=2, default=str))


if __name__ == "__main__":
    case = Probe()
    outcome = case.run()
    for _one, text in outcome.errors + outcome.failures:
        print(text, file=sys.stderr)
