"""W32577's separately authorized real-Docker gate; never builds or pulls.

Prepared under claim162766, not executed by that deterministic assignment.
Requires a reviewed, already-present reference-worker image by exact digest.
The engine and delivery/custody providers are real. Authority and the agent
are deterministic boundary fixtures; no live model or provider is contacted.
"""
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest
import uuid

from baton_v12.worker_manager import (advance_deadline, deadline_cleanup_of,
    deadline_of, observe_deadline, request_runtime_start, runtime_lane)
from baton_v12.worker_manager.oci import EnginePort, OciAdapter
from .test_attempts import Agent
from .test_lifecycle_composition import Lifecycle, POLICY, RETENTION, PROFILE, ADAPTER
from .test_offers import NOW


GATE_PATH = Path(__file__).resolve().parents[4] / "work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/engine-gate.py"
_spec = importlib.util.spec_from_file_location("w32577_engine_gate", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


class DeadlineDocker(Lifecycle, unittest.TestCase):
    engine = "docker"
    required = True

    @classmethod
    def docker(cls, words):
        return cls.control.docker(words)

    @classmethod
    def setUpClass(cls):
        root = os.environ.get("BATON_W32577_GATE_DIR")
        assert root, "run this gate through its reviewed engine-gate.py supervisor"
        cls.control = gate.ChildControl(root)
        assert importlib.metadata.version("jsonschema") == "4.26.0", "required jsonschema4.26.0 is unavailable"
        assert shutil.which("docker"), "required Docker executable is unavailable"
        cls.image_digest = os.environ.get("BATON_W32577_IMAGE_DIGEST", "")
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", cls.image_digest), "set BATON_W32577_IMAGE_DIGEST to the reviewed, preloaded reference-worker image identity"
        version = cls.docker(["version", "--format", "{{.Server.Version}}"])
        assert version.returncode == 0, version.stderr.decode("utf-8", "replace")
        inspected = cls.docker(["image", "inspect", cls.image_digest])
        assert inspected.returncode == 0, "required preloaded image is unavailable; this gate never pulls or builds"
        image = json.loads(inspected.stdout)[0]
        assert image["Id"] == cls.image_digest
        assert image["Config"]["Entrypoint"] == ["python3", "/opt/baton/baton_worker.py"]
        print(json.dumps({"gate": "W32577", "engine": version.stdout.decode().strip(),
                          "image_digest": cls.image_digest, "jsonschema": "4.26.0",
                          "authority": "deterministic boundary fixture", "live_model": False}))

    def setUp(self):
        super().setUp()
        self.now = NOW
        self.store._clock = lambda: self.now
        self.session.discharge_answer["kind"] = "runtime-absent"
        original = self.session.cancel

        def cancel(command):
            answer = original(command)
            self.session.live_assignment = None
            self.session._work = dict(self.session._work, phase="block", gate="runtime-quiescence:1",
                fenced_generations=[{"generation": 1, "cause": "cancelled", "reason": command["reason"]}])
            return answer

        self.session.cancel = cancel

    def spawn(self, argv, *, seconds=None):
        self.assertEqual(argv[0], "docker")
        if "--name" in argv:
            self.made.append(argv[argv.index("--name") + 1])
        self.engine_calls.append(list(argv))
        self.trace.append(("engine", list(argv)))
        result = self.docker(argv[1:])
        return {"status": result.returncode, "stdout": result.stdout.decode("utf-8", "replace"),
                "stderr": result.stderr.decode("utf-8", "replace")}

    def remove_everything(self):
        # The surviving supervisor owns the one reserved container cleanup phase.
        # Names remain durable even if this child is stopped before unittest cleanup.
        pass

    def doCleanups(self):
        # Keep fixture roots as run evidence. Inherited directory/provider cleanup
        # must not race the parent's later container removal on a failing body.
        # These fixtures use synthetic credentials; no live provider is involved.
        gate.durable(self.control.root / "fixture-retained.json", {
            "home": getattr(self, "home", None),
            "deferred_callbacks": [getattr(function, "__name__", type(function).__name__)
                                   for function, _, _ in self._cleanups]})
        self._cleanups.clear()
        if getattr(self, "store", None) is not None:
            self.addCleanup(self.store.close)
        return super().doCleanups()

    def test_reached_fence_exact_removal_providers_custody_and_discharge(self):
        given, assignment = self.activated()
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        adapter = OciAdapter("docker", EnginePort(self.spawn),
            identity={"image_digest": self.image_digest, "profile_digest": PROFILE,
                      "policy_digest": POLICY, "adapter_digest": ADAPTER},
            assignment_roots=dict(roots), posture="execution", mounts=self.plan(roots),
            workspace_group=self.group, outputs=[], credential_delivery=delivery,
            input_manifest_digest=self.input_digest, launch_delivery=self.launch(), interactive=True)
        policy = {"policy_digest": POLICY, "policy_generation": 1, "duration_seconds": 1, "action": "cancel"}
        request_runtime_start(self.store, adapter, attempt_id=self.attempt, inputs=inputs, deadline_policy=policy)
        runtime_id = self.attempt_row()["runtime_id"]
        self.assertEqual(adapter.observe(runtime_id)["state"], "running")
        held_lane = runtime_lane(self.store, self.attempt)
        self.assertEqual(held_lane["holder"], self.attempt)
        self.assertIs(held_lane["held_by_this_attempt"], True)
        sibling = "w32577-sibling-" + uuid.uuid4().hex[:10]
        self.made.append(sibling)
        created = self.docker(["run", "--detach", "--network", "none", "--name", sibling,
                               "--entrypoint", "sleep", self.image_digest, "120"])
        self.assertEqual(created.returncode, 0, created.stderr.decode("utf-8", "replace"))
        sentinel = os.path.join(roots["workspace"], "deadline-partial.txt")
        with open(sentinel, "wb") as handle:
            handle.write(b"untrusted bytes retained at deadline")
        pin = deadline_of(self.store, attempt_id=self.attempt)
        self.now = pin["deadline_at"]
        before = list(self.trace)
        observe_deadline(self.store, self.port, attempt_id=self.attempt)
        self.assertEqual(self.trace, before)
        result = advance_deadline(self.store, self.port, Agent(), adapter, attempt_id=self.attempt,
                                  retention_policy_digest=RETENTION)
        proof = result["cleanup"]
        self.assertEqual(proof, deadline_cleanup_of(self.store, attempt_id=self.attempt, retention_policy_digest=RETENTION))
        self.assertEqual(proof["observed"]["state"], "absent")
        for provider in ("credentials", "launch"):
            self.assertEqual(proof["observed"][provider]["lifecycle_state"], "torn-down")
        self.assertEqual(proof["cleanup"]["cleanup"], "retained")
        released_lane = runtime_lane(self.store, self.attempt)
        self.assertEqual(released_lane["lane"], held_lane["lane"])
        self.assertIsNone(released_lane["holder"])
        self.assertIs(released_lane["held_by_this_attempt"], False)
        self.assertIsNotNone(result["discharge"])
        self.assertIsNone(self.session._work["gate"])
        self.assertEqual(self.attempt_row()["worker_disposition"], "none")
        self.assertEqual(self.attempt_row()["output"], "open")
        with open(sentinel, "rb") as handle:
            self.assertEqual(handle.read(), b"untrusted bytes retained at deadline")
        alive = self.docker(["inspect", "--format", "{{.State.Running}}", sibling])
        self.assertEqual((alive.returncode, alive.stdout.strip()), (0, b"true"))
        fence_index = next(index for index, (kind, _) in enumerate(self.trace) if kind == "authority.cancel")
        for index, (kind, argv) in enumerate(self.trace):
            if kind == "engine" and argv[1] in ("stop", "rm") and argv[-1] == runtime_id:
                self.assertGreater(index, fence_index)
        before = list(self.trace)
        self.assertEqual(advance_deadline(self.store, self.port, Agent(), adapter, attempt_id=self.attempt,
                                        retention_policy_digest=RETENTION), result)
        self.assertEqual(self.trace, before)
        self.assertEqual(runtime_lane(self.store, self.attempt), released_lane)
