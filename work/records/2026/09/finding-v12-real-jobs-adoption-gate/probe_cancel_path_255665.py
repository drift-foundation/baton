"""Claim-255665 P1: does a CANCELLED attempt reach cleanup and discharge?

Review 2026-09-24T09:35:15Z: "Trace the supported cancellation/abandonment
authority and cleanup path for the exact fenced generation and runtime.
Provide deterministic evidence of positive cleanup and discharge after the
selected stop, or a concrete product gap with exact affected paths."

This traces it. It asserts nothing and changes nothing: it stops the attempt
the way the supervisor does, runs ordinary reconciliation ticks, and prints
what each owner's durable record says after every tick.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_abandonment                                        # noqa: E402


class Probe(test_abandonment.TheComposedAbandonmentIsCalled):
    def runTest(self):
        from baton_v12.job_manager import reconcile, status
        from baton_v12.worker_manager import (attempt_runtime_of, intake,
                                              cleanup_of)
        from tests.job_manager import fixtures

        held, stage = self.faulted_with_stage("probe-cancel")
        job, control, operations, attempt_id = (held[0], held[1], held[2],
                                                held[5])
        digest = self.config["retention_policy_digest"]
        operations.cancel_attempt(attempt_id=attempt_id,
                                  reason="the supervisor stopped this attempt")

        trace = []
        for tick in range(8):
            reconcile(job, operations, now=fixtures.NOW)
            state = attempt_runtime_of(control, attempt_id)
            projected = status(job, operations, observed_at=fixtures.NOW)
            trace.append({
                "tick": tick,
                "execution_runtime": state["execution_runtime"],
                "cleanup": state["cleanup"],
                "stage_state": projected["jobs"][0]["stages"][0]["state"],
                "cleanup_record": bool(cleanup_of(
                    control, attempt_id=attempt_id,
                    retention_policy_digest=digest)),
                "gate_discharge": bool(intake.gate_discharge_of(control,
                                                               attempt_id)),
            })
        print(json.dumps({
            "trace": trace,
            "removals": sum(1 for one in self.engines[0].vectors
                            if len(one) > 1 and one[1] == "rm"),
        }, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    case = Probe()
    outcome = case.run()
    for _one, text in outcome.errors + outcome.failures:
        print(text, file=sys.stderr)
