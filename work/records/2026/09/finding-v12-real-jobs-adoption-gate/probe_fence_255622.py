"""Claim-255622: what a prior cancellation actually leaves behind."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_abandonment                                        # noqa: E402


class Probe(test_abandonment.TheComposedAbandonmentIsCalled):
    def runTest(self):
        from baton_v12.worker_manager import (attempt_runtime_of, intake)
        held, stage = self.faulted_with_stage("probe-fence")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        answered = operations.cancel_attempt(
            attempt_id=attempt_id, reason="the operator stopped this attempt")
        state = attempt_runtime_of(control, attempt_id)
        print(json.dumps({
            "cancel_answer_keys": sorted(answered) if isinstance(answered, dict) else str(type(answered)),
            "cancel_cleanup": (answered or {}).get("cleanup"),
            "runtime_state": {k: state[k] for k in state.keys()} if hasattr(state, "keys") else str(state),
            "abandonment_cleanup": intake.abandonment_cleanup_of(
                control, attempt_id=attempt_id,
                retention_policy_digest=digest),
            "gate_discharge": intake.gate_discharge_of(control, attempt_id),
            "abandoned_discharge": intake.abandoned_gate_discharge_of(
                control, attempt_id),
        }, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    case = Probe()
    outcome = case.run()
    for _one, text in outcome.errors + outcome.failures:
        print(text, file=sys.stderr)
