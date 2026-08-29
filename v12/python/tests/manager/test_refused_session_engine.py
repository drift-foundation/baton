"""W32576 — a refused handshake and its ending, against a REAL engine.

`test_refused_session_cleanup.py` proves the manager's half against a recording
custodian: the record that authorizes the removal, the fencing order, the
observation rules, replay, and reuse.  It asks what this manager COMPOSED.
This asks what the daemon actually DID.

The difference is the whole point of the acceptance's first sentence: *a real
Docker execution reaches a genuine `unsupported-version` handshake refusal
AFTER THE CONTAINER EXISTS*.  A fake that answers `absent` proves the manager
reads an answer, not that a running container was removed -- and this ending's
distinguishing fact is precisely that the container is running when the
refusal happens.  The worker is up; it is the handshake that failed.

IT FAILS RATHER THAN SKIPS WITHOUT A DAEMON, inheriting the lifecycle gate,
for the reason W6633's gate gives.
"""

import subprocess
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (authorize_refused_session_cleanup,
                                      certify_agent_session_profile, lanes,
                                      open_agent_session, request_freeze,
                                      request_runtime_start,
                                      settle_unsupported_version)

from . import test_lifecycle_composition as W
from .test_handshake import acp_profile

RETENTION = "sha256:" + "7" * 64


class ARefusedHandshakeReallyEndsItsRuntime(W.Lifecycle):
    """One container, started for real, refused for real, and removed."""

    def refusing(self, version=9):
        """A real running runtime whose handshake this manager refuses.

        THE REFUSAL IS DERIVED, not injected: the session is opened against a
        certified profile pinned to wire version 1, and the agent answers a
        version that profile does not accept.  Nothing here manufactures a
        `ContractRefusal`.
        """
        adapter, roots, inputs = self.prepared()
        self.roots_of_this_attempt = roots
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        self.runtime_id = self.attempt_row()["runtime_id"]
        self.assertTrue(self.present(self.runtime_id))
        profile = acp_profile()
        certify_agent_session_profile(self.store, profile)
        open_agent_session(self.store, self.port, attempt_id=self.attempt,
                           posture="execution",
                           profile_digest=profile["document_digest"],
                           intent="open-execution-1")
        self.reference = {"runtime_attempt_id": self.attempt,
                          "posture": "execution", "session_epoch": 1,
                          "provider_session_id": None}
        answer = settle_unsupported_version(
            self.store, self.port, W.RecordingAgent(self.trace), adapter,
            session_ref=self.reference, agent_protocol_version=version)
        return adapter, answer

    def present(self, runtime_id):
        """ASKED OF THE DAEMON BY EXACT IDENTITY, not by a name filter.

        `docker ps --filter name=` is a SUBSTRING match on the name, and the
        identity this manager attaches is not guaranteed to be one -- so the
        question is put to `container inspect`, which answers about exactly
        the identity it was given or fails.
        """
        found = subprocess.run([self.engine, "container", "inspect",
                                runtime_id],
                               capture_output=True, timeout=120)
        return found.returncode == 0

    def ended(self):
        self.session.live_assignment = None

    def settled(self, adapter, **overrides):
        return authorize_refused_session_cleanup(
            self.store, self.port, adapter, session_ref=self.reference,
            retention_policy_digest=RETENTION, **overrides)

    # -- the acceptance ---------------------------------------------------

    def test_a_real_refusal_after_the_container_exists_reaches_the_ending(self):
        """THE ACCEPTANCE, in one case.

        The container really ran, the refusal is really derived from the
        session's own certified profile, the daemon really removed it, and the
        manager never wrote a worker disposition or froze an output to get
        there.
        """
        adapter, answer = self.refusing()
        self.assertEqual((answer["category"], answer["code"]),
                         ("refused", "unsupported-version"))
        self.assertEqual(answer["runtime_id"], self.runtime_id)
        self.assertEqual(self.attempt_row()["worker_disposition"], "none")
        self.ended()
        settled = self.settled(adapter)
        self.assertEqual(settled["cleanup"], "retained")
        self.assertEqual(settled["state"], "absent")
        # THE DAEMON IS ASKED SEPARATELY, because the adapter's own answer is
        # the thing under test and cannot also be the evidence for it.
        self.assertFalse(self.present(self.runtime_id))
        row = self.attempt_row()
        self.assertEqual(row["execution_runtime"], "destroyed")
        self.assertEqual(row["cleanup"], "retained")
        self.assertEqual(row["worker_disposition"], "none")
        self.assertEqual(row["output"], "open")

    def test_the_delivered_roots_are_torn_down_on_that_absence(self):
        """Positive container absence is what makes it safe to settle the
        roots, and the roots are what this case measures."""
        import os
        adapter, _answer = self.refusing()
        launch_root = adapter.launch_delivery.root
        self.assertTrue(os.path.exists(launch_root))
        self.ended()
        self.settled(adapter)
        self.assertFalse(os.path.exists(launch_root))

    def test_the_untrusted_result_directory_survives_the_removal(self):
        """Whatever the worker wrote before the handshake refused was written
        by a worker this manager never negotiated with: it began untrusted and
        stays untrusted and in place."""
        import os
        adapter, _answer = self.refusing()
        place = os.path.join(self.roots_of_this_attempt["workspace"],
                             f"result-{self.attempt}")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "sentinel.txt"), "wb") as handle:
            handle.write(b"the worker got this far")
        self.ended()
        self.settled(adapter)
        self.assertFalse(self.present(self.runtime_id))
        with open(os.path.join(place, "sentinel.txt"), "rb") as handle:
            self.assertEqual(handle.read(), b"the worker got this far")

    def test_a_second_attempts_container_is_untouched(self):
        """SIBLING PRESERVATION, over two real containers.

        The removal names ONE identity, and the way to prove it reached no
        other is to have another one running while it happens.
        """
        adapter, _answer = self.refusing()
        beside = f"{W.MARK}-w32576-{self.attempt}-sibling"
        self.made.append(beside)
        started = subprocess.run(
            [self.engine, "run", "--detach", "--name", beside,
             "--entrypoint", "sleep", self.image, "300"],
            capture_output=True, timeout=300)
        self.assertEqual(started.returncode, 0,
                         started.stderr.decode("utf-8", "replace")[:2000])
        self.ended()
        self.settled(adapter)
        self.assertFalse(self.present(self.runtime_id))
        self.assertTrue(self.present(beside))

    def test_a_restart_between_the_refusal_and_the_ending_still_ends_once(self):
        """RESTART, and it is a real one: a new store handle over the same
        file, which is what a manager that died between the two boundaries
        comes back as."""
        adapter, _answer = self.refusing()
        self.ended()
        first = self.settled(adapter)
        # A RESTART IS A SECOND INCARNATION OVER THE SAME FILE, which is what
        # a manager that died between the two boundaries comes back as.
        self.store = self.open_store(incarnation="manager-after-restart")
        again = self.settled(adapter)
        self.assertEqual(again, first)
        self.assertFalse(self.present(self.runtime_id))
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM operations WHERE kind = ?",
            ("runtime.destroy-refused-session",)).fetchone()[0], 1)

    def test_the_lane_is_given_back_only_after_the_daemon_agrees(self):
        adapter, _answer = self.refusing()
        self.ended()
        self.assertTrue(lanes.runtime_lane(
            self.store, self.attempt)["held_by_this_attempt"])
        self.settled(adapter)
        self.assertFalse(lanes.runtime_lane(
            self.store, self.attempt)["held_by_this_attempt"])

    def test_a_successful_negotiation_leaves_the_container_running(self):
        """The refusal is DERIVED, so a version the profile accepts has no
        ending to settle -- and the container is still there to prove the
        seam refused before anything destructive."""
        with self.assertRaises(ContractRefusal) as caught:
            self.refusing(version=1)
        self.assertIn("negotiated wire version", str(caught.exception))
        self.assertTrue(self.present(self.runtime_id))
        self.assertEqual(self.attempt_row()["execution_runtime"], "running")

    def test_the_freeze_door_is_still_shut_and_this_one_is_not(self):
        """Measured rather than argued, against the real composition.

        `request_freeze` needs a terminal worker disposition already recorded
        and this ending produces none -- which is exactly why the third door
        exists. A case that only asserted the new door works would not show
        the old one was unreachable.
        """
        adapter, _answer = self.refusing()
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, adapter,
                           attempt_id=self.attempt, disposition="completed")
        self.assertNotEqual(caught.exception.category, "integrity")
        self.ended()
        self.assertEqual(self.settled(adapter)["cleanup"], "retained")


class DockerRefusedSession(ARefusedHandshakeReallyEndsItsRuntime,
                           unittest.TestCase):
    engine = "docker"
    required = True


class PodmanRefusedSession(ARefusedHandshakeReallyEndsItsRuntime,
                           unittest.TestCase):
    engine = "podman"
    required = False
