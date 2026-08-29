"""W34998 — the failed-start removal, against a REAL engine.

`test_failed_start_destroy.py` proves the manager's half against a recording
fake: the closed bodies, the cross-call refusals, the shared core and the
custody the provider must not touch.  That is the right shape for the refusal
paths and it is not this claim.  It asks what this manager COMPOSED; this asks
what the daemon actually DID.

The difference is the whole point of the acceptance's removal sentence.  A
force-remove followed by an inspection is two engine acts, and "the exact
container is gone" is a fact only the daemon can supply -- a fake that answers
`absent` proves the manager reads an answer, not that anything was removed.

IT FAILS RATHER THAN SKIPS WITHOUT A DAEMON, inheriting `ContainerCase`, for
the reason W6633's gate gives.
"""

import json
import os
import subprocess
import tempfile
import uuid

from baton_v12.worker_manager import documents, launch, oci

from baton_v12.worker_manager import ControlStore

from . import input_roots
from .test_worker_container import ENGINE, MARK, ContainerCase

RETENTION = "sha256:" + "7" * 64
FAILED_START = "sha256:" + "9" * 64
ASSIGNMENT = {"work_ref": {"authority_uuid": "0123456789abcdef" * 2,
                           "work_id": "01234567-W1"},
              "participant": "baton.claude", "generation": 1}


class ARealContainerIsRemovedAndProvedGone(ContainerCase):

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w34998-engine-")
        self.addCleanup(self._release)
        self.inputs = os.path.join(self.home, "inputs")
        self.workspace = os.path.join(self.home, "workspace")
        for place in (self.inputs, self.workspace):
            os.makedirs(place, exist_ok=True)
        self.made = []
        self.addCleanup(self._remove_containers)
        self.store = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="fs-engine-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = input_roots.configured_group(self.store)
        # THE BUILT IMAGE'S OWN DIGEST, asked of the daemon rather than
        # assumed: the adapter compares what it starts against this, and a
        # constant would agree with itself.
        self.digest = json.loads(subprocess.run(
            [ENGINE, "image", "inspect", self.image, "--format", "{{json .Id}}"],
            capture_output=True, timeout=120).stdout.decode("utf-8"))

    def _release(self):
        # THE LAUNCH DOCUMENT IS FROZEN READ-ONLY on purpose, so the fixture
        # has to be able to take it away again -- and so does its directory,
        # which `launch.materialize` closes for the same reason.
        for current, directories, files in os.walk(self.home, topdown=False):
            os.chmod(current, 0o700)
            for name in files:
                place = os.path.join(current, name)
                os.chmod(place, 0o600)
                os.remove(place)
            for name in directories:
                place = os.path.join(current, name)
                os.chmod(place, 0o700)
                os.rmdir(place)
        os.rmdir(self.home)

    def _remove_containers(self):
        for name in self.made:
            subprocess.run([ENGINE, "rm", "--force", name],
                           capture_output=True, timeout=120)

    def launched(self):
        home = os.path.join(self.home, f"launch-{uuid.uuid4().hex[:8]}")
        os.makedirs(home)
        return launch.materialize(home, attempt_id="attempt-1",
                                  session="session-1",
                                  contract="prove a failed-start removal",
                                  role="implementer")

    def adapter(self):
        return oci.OciAdapter(
            ENGINE, oci.EnginePort(self.spawn),
            identity={"image_digest": self.digest,
                      "profile_digest": "sha256:" + "b" * 64,
                      "policy_digest": "sha256:" + "d" * 64,
                      "adapter_digest": "sha256:" + "c" * 64},
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group,
            launch_delivery=self.launched())

    @staticmethod
    def spawn(argv):
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        return {"status": finished.returncode,
                "stdout": finished.stdout.decode("utf-8", "replace"),
                "stderr": finished.stderr.decode("utf-8", "replace")}

    def started(self):
        """A REAL container this manager did not start through `start`.

        A failed start is one that reached the engine, CREATED a container and
        then failed -- so the state this removal acts on is exactly a container
        that exists and that no successful start ever recorded. Creating it
        directly is the honest reproduction of that state; going through
        `start` would produce the state the other suite already covers.
        """
        name = f"{MARK}-w34998-{uuid.uuid4().hex[:10]}"
        self.made.append(name)
        finished = subprocess.run(
            [ENGINE, "run", "--detach", "--name", name,
             "--entrypoint", "sleep", self.image, "300"],
            capture_output=True, timeout=300)
        self.assertEqual(finished.returncode, 0,
                         finished.stderr.decode("utf-8", "replace")[:2000])
        return name

    def command(self, runtime_id, **overrides):
        body = documents.failed_start_destroy_command(
            assignment_ref=dict(ASSIGNMENT), runtime_attempt_id="attempt-1",
            runtime_id=runtime_id, failed_start_record_digest=FAILED_START,
            retention_policy_digest=RETENTION)
        body.update(overrides)
        return body

    def present(self, name):
        found = subprocess.run(
            [ENGINE, "ps", "--all", "--quiet", "--filter", f"name=^{name}$"],
            capture_output=True, timeout=120)
        return bool(found.stdout.decode("utf-8").strip())

    def test_the_exact_container_is_gone_and_the_daemon_says_so(self):
        name = self.started()
        self.assertTrue(self.present(name))
        answered = self.adapter().destroy_failed_start(self.command(name))
        self.assertEqual(answered["runtime_id"], name)
        self.assertEqual(answered["state"], "absent", answered)
        # THE DAEMON IS ASKED SEPARATELY, because the adapter's own answer is
        # the thing under test and cannot also be the evidence for it.
        self.assertFalse(self.present(name))

    def test_repeating_it_answers_the_same_absence(self):
        name = self.started()
        adapter = self.adapter()
        self.assertEqual(
            adapter.destroy_failed_start(self.command(name))["state"],
            "absent")
        self.assertEqual(
            adapter.destroy_failed_start(self.command(name))["state"],
            "absent")

    def test_the_untrusted_result_directory_survives_the_removal(self):
        """The acceptance's sentinel, over a real removal.

        The directory a failed start left behind was created untrusted and
        stays in place untrusted -- and what proves that is a byte still being
        there after the container it belonged to is gone.
        """
        place = os.path.join(self.workspace, "result-attempt-1")
        os.makedirs(place)
        with open(os.path.join(place, "sentinel.txt"), "wb") as handle:
            handle.write(b"the worker got this far")
        name = self.started()
        self.adapter().destroy_failed_start(self.command(name))
        self.assertFalse(self.present(name))
        with open(os.path.join(place, "sentinel.txt"), "rb") as handle:
            self.assertEqual(handle.read(), b"the worker got this far")

    def test_a_receipt_authorized_body_is_refused_before_the_engine(self):
        """No fallback, against the real thing.

        The container is still there afterwards, which is the strongest form
        of "refused before engine activity" this suite can state.
        """
        from baton_v12.contracts import ContractRefusal
        name = self.started()
        receipted = documents.destroy_command(
            assignment_ref=dict(ASSIGNMENT), runtime_attempt_id="attempt-1",
            runtime_id=name, intake_receipt_digest=FAILED_START,
            retention_policy_digest=RETENTION)
        with self.assertRaises(ContractRefusal):
            self.adapter().destroy_failed_start(receipted)
        self.assertTrue(self.present(name))
