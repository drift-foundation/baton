"""Claim-255433: READ the committed cleanup document, shape and all."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_abandonment                                        # noqa: E402


class Probe(test_abandonment.TheComposedAbandonmentIsCalled):
    def runTest(self):
        from baton_v12.worker_manager import intake
        held, stage = self.faulted_with_stage("probe-1")
        control, operations, attempt_id = held[1], held[2], held[5]
        answered = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id,
            retention_policy_digest=self.config["retention_policy_digest"])
        discharge = intake.abandoned_gate_discharge_of(control, attempt_id)
        print(json.dumps({"answered": answered, "settled": settled,
                          "discharge": discharge},
                         indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    import unittest
    case = Probe()
    outcome = case.run()
    for _one, text in outcome.errors + outcome.failures:
        print(text, file=sys.stderr)
