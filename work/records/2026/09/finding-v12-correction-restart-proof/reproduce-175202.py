"""Independent recheck of original R1/R2 faults against candidate175150."""
import json
import os
from pathlib import Path
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import provider_context as context
from baton_v12.worker_manager import context_delivery as delivery
from tests.manager.test_provider_context import ContextCase


class ReviewProbes(ContextCase):
    def test_partial_state_write_retry(self):
        first, state = self.state()
        self.end_runtime(first)
        original_write = os.write
        original_copy = delivery._copy
        def partial(fd, body):
            original_write(fd, body[:3])
            raise RuntimeError("cut after three staged state bytes")
        def cut_copy(*args, **kwargs):
            with mock.patch.object(os, "write", side_effect=partial):
                return original_copy(*args, **kwargs)
        with mock.patch.object(delivery, "_copy", side_effect=cut_copy):
            with self.assertRaisesRegex(RuntimeError, "three staged state bytes"):
                self.finalize()
        before = context.context_use_of(self.control, self.attempt_id)
        try:
            self.finalize()
        except ContractRefusal as error:
            outcome = str(error)
        else:
            outcome = "ready"
        after = context.context_use_of(self.control, self.attempt_id)
        print(json.dumps({"probe": "partial-state-write", "before": before["status"], "retry": outcome, "after": after["status"], "reason": after.get("reason"), "engine_starts": len(self.adapter.started)}))
        self.assertEqual(after["status"], "ready")
        self.assertEqual(outcome, "ready")
        self.assertEqual(len(self.adapter.started), 1)

    def test_generation_identity_damage_observation(self):
        first, state = self.state()
        self.end_runtime(first)
        self.finalize()
        identity = self.private / first.context_id / "generations/1/identity"
        identity.chmod(0o600)
        identity.write_bytes(b'{"use_id":"foreign-use","exclusion_digest":"foreign"}')
        identity.chmod(0o400)
        observed = context.context_of(self.control, first.context_id)
        with self.assertRaises(ContractRefusal):
            self.finalize()
        replay = context.context_of(self.control, first.context_id)
        print(json.dumps({"probe": "generation-identity-damage", "observation": observed["status"], "finalize_replay": replay["status"]}))
        self.assertEqual(observed["status"], "held")
        self.assertEqual(replay["status"], "held")


if __name__ == "__main__":
    unittest.main(verbosity=2)
