"""Run selected existing cases and observe the public state at the fence call."""
import json
from pathlib import Path
import unittest
from unittest import mock

from baton_v12 import worker_manager
from baton_v12.worker_manager import attempts
from tests.tools import test_dogfood_operator

case = test_dogfood_operator.TheRecoveryNeverAdoptsAnOlderIncarnationsRuntime
original_case = case.test_a_requested_start_refuses_the_pre_attach_fence
original_fence = worker_manager.fence_pre_attach_abandonment
observations = []


def observed_case(self):
    def observed_fence(store, port, *, attempt_id, reason):
        state = attempts.attempt_runtime_of(store, attempt_id)
        observations.append({
            "execution_runtime": state["execution_runtime"],
            "runtime_id": state["runtime_id"],
            "start_failure_present": attempts.attempt_start_failure_of(store, attempt_id) is not None,
        })
        return original_fence(store, port, attempt_id=attempt_id, reason=reason)

    with mock.patch.object(worker_manager, "fence_pre_attach_abandonment", observed_fence):
        original_case(self)


case.test_a_requested_start_refuses_the_pre_attach_fence = observed_case
try:
    unittest.main(module=None)
finally:
    Path(__file__).with_name("review-start-state-175026.json").write_text(json.dumps(observations, indent=2) + "\n")
