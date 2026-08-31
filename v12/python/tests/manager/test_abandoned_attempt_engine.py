"""W44716 — an operator's abandonment, against a REAL engine.

`test_attempts.py` proves what the manager COMPOSED: the declaration, the
fence-before-removal order, replay, eligibility, and the interruption matrix.
It asks the questions a recording custodian can answer. This asks what the
daemon actually DID.

THE FACT ONLY A DAEMON SUPPLIES is the one that distinguishes this ending from
its three siblings: THE CONTAINER IS RUNNING. A failed start has no container;
a refused handshake has one that was refused; an intake receipt has one whose
worker answered. Abandonment is for the attempt whose runtime started fine and
whose worker then said nothing at all -- so the container under this ending is
up, healthy by every mechanical measure, and busy. A fake that answers `absent`
proves the manager reads an answer, not that a live container was removed.

IT FAILS RATHER THAN SKIPS WITHOUT A DAEMON, inheriting the lifecycle gate.
"""

import subprocess
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (abandon_attempt, request_runtime_start)

from . import test_lifecycle_composition as W

RETENTION = "sha256:" + "7" * 64
REASON = "the supervised worker never answered and an operator ended it"


class AnAbandonedAttemptReallyLosesItsRunningRuntime(W.Lifecycle):
    """One container, started for real, still running, and removed anyway."""

    def unanswering(self):
        """A real, RUNNING runtime whose worker this manager never heard from.

        Nothing here refuses a handshake, freezes an output or writes a worker
        disposition. That is the whole state under test: a healthy container
        and a silence, which is precisely what the three existing endings all
        decline to act on.
        """
        adapter, roots, inputs = self.prepared()
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        self.runtime_id = self.attempt_row()["runtime_id"]
        self.assertTrue(self.running(self.runtime_id),
                        "this ending is ABOUT a container that is up")
        return adapter

    def running(self, runtime_id):
        """ASKED OF THE DAEMON BY EXACT IDENTITY, and about its state.

        `container inspect` answers about exactly the identity it is given or
        fails, which is what a substring name filter cannot promise.
        """
        found = subprocess.run(
            [self.engine, "container", "inspect", runtime_id, "--format",
             "{{.State.Running}}"], capture_output=True, timeout=120)
        if found.returncode != 0:
            return False
        return found.stdout.decode("utf-8", "replace").strip() == "true"

    def present(self, runtime_id):
        found = subprocess.run([self.engine, "container", "inspect",
                                runtime_id], capture_output=True, timeout=120)
        return found.returncode == 0

    def abandoned(self, adapter, **overrides):
        operands = {"attempt_id": self.attempt, "reason": REASON,
                    "retention_policy_digest": RETENTION}
        operands.update(overrides)
        return abandon_attempt(self.store, self.port, adapter, **operands)

    # -- the acceptance ----------------------------------------------------

    def test_a_running_container_nobody_answered_for_is_really_removed(self):
        """THE ACCEPTANCE, in one case.

        The container really ran and was really up at the moment of the
        declaration; the daemon really removed it; and the manager reached
        that ending without a worker disposition, without an output, and
        without an intake receipt -- because it had none of them to read.
        """
        adapter = self.unanswering()
        row = self.attempt_row()
        self.assertEqual(row["worker_disposition"], "none")
        self.assertEqual(row["output"], "open")

        answered = self.abandoned(adapter)

        self.assertEqual(sorted(answered), ["cleanup", "fenced", "intent"])
        self.assertEqual(answered["intent"]["reason"], REASON)
        self.assertEqual(answered["intent"]["runtime_id"], self.runtime_id)
        self.assertEqual(answered["cleanup"]["cleanup"], "retained")
        self.assertEqual(answered["cleanup"]["state"], "absent")
        # THE DAEMON IS ASKED SEPARATELY, because the adapter's own answer is
        # the thing under test and cannot also be the evidence for it.
        self.assertFalse(self.present(self.runtime_id),
                         "a real daemon removed a real running container")
        row = self.attempt_row()
        self.assertEqual(row["execution_runtime"], "destroyed")
        self.assertEqual(row["cleanup"], "retained")
        self.assertEqual(row["worker_disposition"], "none",
                         "abandonment never invents a worker answer")
        self.assertEqual(row["output"], "open",
                         "and never closes an output nobody froze")

    def test_the_fence_precedes_the_removal_against_a_live_container(self):
        """Order, where it actually matters.

        Against a fake this is an ordering assertion. Against a daemon it is
        the safety property itself: for the whole interval between the fence
        and the removal, the authority already considers the generation
        cancelled while the container is still up -- and never the reverse,
        which would leave an authorized worker running with its runtime being
        torn out from under it.
        """
        adapter = self.unanswering()
        order = []
        cancel = self.session.cancel

        def fenced(operands):
            order.append(("fence", self.running(self.runtime_id)))
            return cancel(operands)

        self.session.cancel = fenced
        self.abandoned(adapter)
        order.append(("removed", self.present(self.runtime_id)))

        self.assertEqual(order[0][0], "fence")
        self.assertTrue(order[0][1],
                        "the container was STILL UP when the fence was taken")
        self.assertEqual(order[-1], ("removed", False))

    def test_a_restarted_manager_replays_the_ending_it_already_finished(self):
        """The record answers after a restart, and the daemon is not reasked.

        A resumed manager has no memory of the removal, so the only thing that
        can answer is the journal. If it instead re-derived the ending it
        would ask a daemon about a container that no longer exists and turn a
        finished attempt into an error.
        """
        adapter = self.unanswering()
        first = self.abandoned(adapter)
        self.assertFalse(self.present(self.runtime_id))

        self.store.close()
        self.store = self.open_store(incarnation="manager-w44716-2")

        replay = self.abandoned(adapter)

        self.assertEqual(replay, first)
        self.assertFalse(self.present(self.runtime_id))
        self.assertEqual(self.attempt_row()["cleanup"], "retained")

    def test_a_second_policy_after_the_ending_refuses_without_touching(self):
        """A newly derived cleanup does not revisit a finished ending.

        Review 2026-08-30T11:56:53Z [P0]. Against the daemon the consequence
        is concrete: the refusal happens before the authority is called and
        before the engine is asked about a container that is already gone.
        """
        adapter = self.unanswering()
        self.abandoned(adapter)
        fences = len([one for one in self.session.calls if one[0] == "cancel"])

        with self.assertRaises(ContractRefusal) as caught:
            self.abandoned(adapter,
                           retention_policy_digest="sha256:" + "8" * 64)

        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertEqual(len([one for one in self.session.calls
                              if one[0] == "cancel"]), fences,
                         "no second fence for a second policy")


class DockerAbandonment(AnAbandonedAttemptReallyLosesItsRunningRuntime,
                        unittest.TestCase):
    engine = "docker"
    required = True
