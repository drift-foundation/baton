"""W275776 R3 — the dispatch boundary, cut and restarted on the composed worker.

The review authorises exactly this milestone: the selected REC-3 row "before dispatch / after
receipt with unknown provider outcome", proved with a controlled engine and the composed
worker, covering the two cuts as SEPARATE observations, with stable command identity, the
actual effect count, no duplicated provider turn, and a safe resume or an exact actionable
hold.

The durable intent at this boundary is `exchange.publish_command`: the command document is
authored from the attempt alone, so two managers compose identical bytes under an identical
derived name, an identical existing command is ADOPTED and a different one refuses. These cases
are what that property is worth on a restart.

Deterministic engine double, no live Docker and no provider process. Run standalone.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "v12", "python"))

from baton_v12.job_manager import reconcile, status, submit
from baton_v12.worker_manager import attempts as manager_attempts
from baton_v12.worker_manager import exchange, tokens

from tests.job_manager import fixtures
from tests.tools.test_single_worker import Engine, SingleWorkerCase

from tools import single_worker


class TheDispatchBoundarySurvivesARestartWithOneCommand(SingleWorkerCase):
    """One composed worker, one live runtime, one command -- across a restart."""

    def ticking(self, job, control, engine):
        return single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW)

    def watching(self, *, dying=None):
        """Record every command publication, optionally dying at one of them.

        `dying="before"` faults with nothing written -- the pre-dispatch cut. `dying="after"`
        lets the durable write happen and then faults, which is the reply-loss cut: the
        command is a file the container can act on and this manager never learned it landed.
        """
        honest = exchange.publish_command
        seen = []

        def publishing(delivery, document):
            if dying == "before" and not seen:
                seen.append({"published": None, "died": "before"})
                raise OSError("the manager stopped before publishing the command")
            answered = honest(delivery, document)
            seen.append(dict(answered))
            if dying == "after" and len(seen) == 1:
                raise OSError("the manager stopped after the command was written")
            return answered

        exchange.publish_command = publishing
        single_worker.exchange.publish_command = publishing
        self.addCleanup(setattr, exchange, "publish_command", honest)
        self.addCleanup(setattr, single_worker.exchange, "publish_command", honest)
        return seen

    def driving(self, label, engine, *, dying):
        """Ticks until the chosen cut is reached, then the stores are handed back."""
        seen = self.watching(dying=dying)
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(8):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except OSError:
                break
        attempt_id = self.only_attempt(control)
        return {"job": job, "control": control, "operations": operations,
                "attempt_id": attempt_id, "seen": seen,
                "domain": self.domain_of(control, attempt_id)}

    def domain_of(self, control, attempt_id):
        row = manager_attempts._require_attempt(control, attempt_id)
        return tokens.domain_of(
            "workspace",
            tokens.workspace_governance(control=control).identity(row))

    def only_attempt(self, control):
        rows = manager_attempts._attempts(control, "ORDER BY runtime_attempt_id")
        identities = [row["runtime_attempt_id"] for row in rows]
        self.assertEqual(len(identities), 1, identities)
        return identities[0]

    # -- cut one: BEFORE dispatch ---------------------------------------------

    def test_a_restart_BEFORE_dispatch_publishes_exactly_one_command(self):
        """Nothing durable was written, so the resumed manager must publish once -- and
        only once. The container was up and had been asked for nothing, which is the state
        this whole boundary exists to make recoverable."""
        engine = Engine()
        held = self.driving("pre-dispatch", engine, dying="before")
        self.assertEqual(held["seen"], [{"published": None, "died": "before"}],
                         "the pre-dispatch cut was never reached")
        held["operations"].close(); held["job"].close(); held["control"].close()

        resumed_job, resumed_control = self.stores("pre-dispatch")
        published = self.watching()
        resumed = self.ticking(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        wrote = [one for one in published if one.get("published")]
        self.assertEqual(len(wrote), 1,
                         f"the resume did not publish exactly one command: {published}")
        # ONE CONTAINER AND ONE ACTIVATION: the dispatch cut composed nothing new.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(engine.activations), 1)
        # AND THE RESOURCE IS STILL THIS GENERATION'S.
        self.assertEqual(len(tokens.outstanding(resumed_control, held["domain"])), 1)

    # -- cut two: AFTER dispatch, reply lost ----------------------------------

    def test_a_restart_AFTER_dispatch_does_not_ASK_AGAIN_at_all(self):
        """The command is a durable file and this manager never learned it landed.

        MEASURED, and the answer is stronger than the one I first asserted. I expected the
        resumed manager to reach the publisher and ADOPT the identical command -- the
        publisher is built for exactly that. What actually happens is that it never reaches
        the publisher: the durable command plus the canonical state already say this stage is
        dispatched and waiting, so nothing is re-asked at all. Zero further publications is
        the strongest form of "no duplicated provider turn", and the container can act on the
        file with or without this manager.
        """
        engine = Engine()
        held = self.driving("post-dispatch", engine, dying="after")
        self.assertEqual(len(held["seen"]), 1)
        self.assertTrue(held["seen"][0]["published"],
                        "the durable write never happened, so this is not the cut")
        first = held["seen"][0]["command_digest"]
        place = held["seen"][0]["place"]
        # THE FIRST PASS REACHED A LIVE RUNTIME and a published command.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(engine.activations), 1)
        held["operations"].close(); held["job"].close(); held["control"].close()

        resumed_job, resumed_control = self.stores("post-dispatch")
        published = self.watching()
        resumed = self.ticking(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        # NOTHING IS RE-ASKED, and nothing is re-launched.
        self.assertEqual(published, [],
                         f"the resume published a command again: {published}")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(engine.activations), 1)
        # THE ONE COMMAND IS STILL THE ONE THAT WAS WRITTEN, by digest, read from the file
        # the first pass named rather than from a second publication.
        self.assertTrue(os.path.exists(place))
        import hashlib

        with open(place, "rb") as reading:
            self.assertEqual("sha256:" + hashlib.sha256(reading.read()).hexdigest(),
                             first)
        # AND THE STAGE IS A STATE A READER CAN ACT ON rather than silence.
        stage = status(resumed_job, resumed,
                      observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "waiting")
        self.assertEqual(len(tokens.outstanding(resumed_control, held["domain"])), 1)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(
        loader.loadTestsFromTestCase(
            TheDispatchBoundarySurvivesARestartWithOneCommand)).wasSuccessful())
