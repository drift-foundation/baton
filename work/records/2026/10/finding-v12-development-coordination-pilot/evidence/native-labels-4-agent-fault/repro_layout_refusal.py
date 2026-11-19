"""native-labels-4 w29401-labels-3 implementation fault: deterministic reproduction.

Read-only against the retained instance; nothing here opens a store, a
container or a credential. It proves, from the product bytes at the installed
checkpoint (a62bc9a3, whose `v12/worker` tree is byte-identical to e670e624,
the image's build source), the chain the diagnosis names:

  1. the worker image recipe copies `verifier-layout-marker.json` into
     `/opt/baton`, so the adapter's `_trusted_marker()` is not None;
  2. the deployment the pool's `compose-worker` writes is
     `baton.v12.single-worker-deployment/4` with no `verifier_layout`, so
     `single_worker.layout_delivery` answers None and no
     `/run/baton/verifier-layout.json` is bound into the container (the
     retained container's mount table agrees);
  3. with a marker and no document, `ClaudeAgent._selected_layout` raises
     `TaskRefusal` ("no trusted layout selection was delivered ... refuses
     before the provider") -- the W325695 "new image, missing layout" case;
  4. `TaskRefusal` is neither a `WorkerFault` nor an
     `AdapterDeclarationRefusal`, so `baton_worker.serve_exchange` reaches
     its generic clause and publishes `faulted` with fault code `agent` and
     `adapter_failure: null` -- exactly the retained terminal document;
  5. the manager's own topology digest equals the marker's, so a delivered
     selection would have been the compatible pair.

Run from `v12/python` with the prepared interpreter:

  PYTHONPATH=src:.:../worker:src/baton_v12 <venv>/bin/python <this file>
"""

import json
import os
import tempfile
import unittest

import baton_worker
import claude_agent
from baton_v12.worker_manager import source_boundary
from tools import single_worker

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *([os.pardir] * 7)))
MARKER = os.path.join(REPO, "v12", "worker", "verifier-layout-marker.json")
RECIPE = os.path.join(REPO, "v12", "worker", "Dockerfile.claude")
COMPOSED = os.path.join(HERE, os.pardir, os.pardir, "config",
                        "impl-a-a62bc9a3.json")
# The retained terminal document the manager adopted (copied by the owner
# into evidence/native-labels-4-execution/terminal.json).
TERMINAL = os.path.join(HERE, os.pardir, "native-labels-4-execution",
                        "terminal.json")


class NewImageWithoutLayoutSelection(unittest.TestCase):

    def test_the_marker_image_refuses_before_the_provider(self):
        # 1. the recipe ships the marker; the adapter reads it as "new image".
        with open(RECIPE, encoding="utf-8") as reading:
            recipe = reading.read()
        self.assertIn("/opt/baton/verifier-layout-marker.json", recipe)
        with open(MARKER, encoding="utf-8") as reading:
            marker = json.load(reading)
        agent = claude_agent.ClaudeAgent()
        self.assertEqual(agent._trusted_marker(place=MARKER)["layout_digest"],
                         marker["layout_digest"])

        # 2. the composed deployment selects no layout, so nothing is bound.
        with open(COMPOSED, encoding="utf-8") as reading:
            composed = json.load(reading)
        deployment = composed["deployment"] if "deployment" in composed else composed
        self.assertEqual(deployment["schema"], single_worker.CONFIG_SCHEMA)
        self.assertEqual(deployment["schema"],
                         "baton.v12.single-worker-deployment/4")
        self.assertNotIn("verifier_layout", deployment)
        self.assertIsNone(single_worker.layout_delivery(deployment, None))

        # 3. marker present, document absent: the adapter refuses.
        with tempfile.TemporaryDirectory(prefix="repro-layout-") as room:
            absent = os.path.join(room, "verifier-layout.json")
            with self.assertRaises(claude_agent.TaskRefusal) as caught:
                agent._selected_layout(place=absent, marker=marker)
        said = str(caught.exception)
        self.assertIn("no trusted layout selection was delivered", said)
        self.assertIn("refuses before the provider", said)

        # 4. that refusal is the worker's anonymous `agent` fault.
        self.assertFalse(issubclass(claude_agent.TaskRefusal,
                                    baton_worker.WorkerFault))
        self.assertFalse(issubclass(
            claude_agent.TaskRefusal,
            baton_worker.adapter_refusal.AdapterDeclarationRefusal))
        with open(TERMINAL, encoding="utf-8") as reading:
            terminal = json.load(reading)
        self.assertEqual(terminal["ending"], "faulted")
        self.assertEqual(terminal["fault_code"], "agent")
        self.assertIsNone(terminal["adapter_failure"])
        self.assertEqual(terminal["answered"], ["describe"])

        # 5. the pair would be compatible once a selection is delivered.
        self.assertEqual(source_boundary.layout_digest(),
                         marker["layout_digest"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
