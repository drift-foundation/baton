"""W275776 R3 — the provider effect and its receipt, cut and restarted.

This is the one proof review 2026-09-27T12-20-22Z says remains: the published command must be
CONSUMED by a deterministic executor, the effect COUNTED, a RECEIPT identity produced, the
manager interrupted after the possible effect with that observation unseen, and then -- with
fresh stores -- the actual resume must show ONE effect across the restart, or an exact
actionable unknown hold that does not ask again.

The executor here is deterministic and local: it reads the command file the manager published,
performs one counted effect, and writes the worker-side RECEIPT document into the exchange's
event root, which is exactly what `exchange.observation` reconstructs the sequence from. No
provider process, no container, no live engine.

Run standalone.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "v12", "python"))

from baton_v12.job_manager import reconcile, status, submit
from baton_v12.worker_manager import attempts as manager_attempts
from baton_v12.worker_manager import exchange, launch, tokens

from tests.job_manager import fixtures
from tests.tools.test_single_worker import Engine, SingleWorkerCase

from tools import single_worker


class Executor:
    """A deterministic consumer of ONE published command.

    It is the provider's place in this proof and nothing more: it reads the command the
    manager published, counts one effect for it, and writes the worker-side receipt. Asked
    twice for the same command it records a SECOND effect -- deliberately, because a consumer
    that silently ignored a repeat would hide the very duplication this cut is about.
    """

    def __init__(self, delivery):
        self.delivery = delivery
        self.effects = []
        self.receipts = []

    def consume(self):
        """Read the command the way the in-container worker does, and receipt it.

        The command FILE is what a worker reads -- `exchange.observation` deliberately does
        not surface the session to a manager-side reader, and the session is a member of the
        worker's receipt -- so this takes it from the bytes at the fixed name, and derives the
        digest from the same bytes the manager digested.
        """
        import hashlib

        held = exchange.observation(self.delivery)
        command = held.get("command")
        if command is None:
            return None
        name = exchange.sequence_of(self.delivery.attempt_id) + ".json"
        place = os.path.join(self.delivery.command_root, name)
        with open(place, "rb") as reading:
            raw = reading.read()
        document = json.loads(raw.decode("utf-8"))
        digested = "sha256:" + hashlib.sha256(raw).hexdigest()
        assert digested == command["command_digest"], (digested, command)
        self.effects.append(digested)
        receipt = {"schema": exchange.RECEIPT_SCHEMA,
                   "session": document["session"],
                   "attempt_id": document["attempt_id"],
                   "sequence_id": document["sequence_id"],
                   "command_digest": digested,
                   "accepted_at": fixtures.NOW}
        place = os.path.join(self.delivery.event_root,
                             exchange.RECEIPT_DOCUMENT)
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(receipt, writing)
        self.receipts.append(receipt)
        return receipt


class TheProviderEffectIsPerformedOnceAcrossARestart(SingleWorkerCase):
    """One command, one consumer, one effect -- with the manager interrupted between."""

    def ticking(self, job, control, engine):
        return single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW)

    def only_attempt(self, control):
        rows = manager_attempts._attempts(control, "ORDER BY runtime_attempt_id")
        identities = [row["runtime_attempt_id"] for row in rows]
        self.assertEqual(len(identities), 1, identities)
        return identities[0]

    def domain_of(self, control, attempt_id):
        row = manager_attempts._require_attempt(control, attempt_id)
        return tokens.domain_of(
            "workspace",
            tokens.workspace_governance(control=control).identity(row))

    def _adopted(self, attempt_id):
        """This attempt's exchange delivery, through the EXCHANGE's own reader.

        `launch.adopt` re-authors and compares the whole launch document -- including the Job
        execution half it re-resolves through its own owner -- and refusing to re-compose all
        of that here is deliberate: this fixture is a CONSUMER of the exchange, not a second
        author of a launch. `exchange.adopt` is the reader the launch path itself calls once
        the document has been proved (`launch.py` line ~840), and it proves the two namespaces
        it needs. Measured route: my first two attempts re-authored the launch document and
        were correctly refused as "not the one this manager would have written".
        """
        from baton_v12.worker_manager import workspaces

        root = os.path.join(os.path.realpath(self.config["launch_home"]), attempt_id)
        delivery = exchange.adopt(
            root, attempt_id=attempt_id,
            workspace_group=workspaces.configured_workspace_group(self.control))
        self.assertIsNotNone(delivery,
                             f"no exchange namespaces under {root}")
        return delivery

    def dispatched(self, label, engine):
        """Ticks until the command is published and the runtime is live."""
        job, control = self.stores(label)
        self.control = control
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(8):
            reconcile(job, operations, now=fixtures.NOW)
        attempt_id = self.only_attempt(control)
        delivery = self._adopted(attempt_id)
        held = exchange.observation(delivery)
        self.assertIsNotNone(held.get("command"),
                             "the command was never published, so this is not the cut")
        return {"job": job, "control": control, "operations": operations,
                "attempt_id": attempt_id, "delivery": delivery,
                "command": held["command"],
                "domain": self.domain_of(control, attempt_id)}

    def inviting(self, executor_for):
        """Wire ONE effect recorder to the REAL invitation seam, and keep it wired.

        W275776 review 2026-09-27T12-28-08Z rejected my previous version, correctly: it called
        the consumer by hand on both sides of the restart and then asserted two effects, which
        proves the FIXTURE can repeat a command and says nothing about whether the production
        resume asks again.

        So the recorder is attached to `exchange.publish_command` -- the manager's own
        invitation -- and it stays attached across the interruption AND the reopen. Every
        invitation that actually WRITES a command invites the consumer exactly once; an
        adoption of an existing command invites nobody, because no new turn was asked for.
        The count is therefore driven by production invitations rather than by this fixture,
        and if the resumed manager asked again the recorder would fire again.
        """
        honest = exchange.publish_command
        seen = {"invitations": [], "publications": []}

        def inviting(delivery, document):
            answered = honest(delivery, document)
            seen["publications"].append(dict(answered))
            if answered["published"]:
                seen["invitations"].append(answered["command_digest"])
                executor_for(delivery).consume()
            return answered

        exchange.publish_command = inviting
        single_worker.exchange.publish_command = inviting
        self.addCleanup(setattr, exchange, "publish_command", honest)
        self.addCleanup(setattr, single_worker.exchange, "publish_command", honest)
        return seen

    def test_ONE_effect_in_total_and_the_resume_never_invites_another(self):
        """The acceptance case: the recorder is wired to the production invitation and stays
        wired across the restart, so the effect count is the product's, not the fixture's.

        One command is published, the consumer performs ONE effect and receipts it, the
        manager is interrupted without observing that receipt, the stores are reopened, and
        the real resume is driven for eight ticks WITH THE RECORDER STILL ATTACHED. It never
        fires again: no second publication, no second invitation, no further activation -- and
        the receipt persists, so the resume has what it needs without asking.
        """
        engine = Engine()
        executors = {}

        def executor_for(delivery):
            return executors.setdefault(
                delivery.attempt_id, Executor(delivery))

        seen = self.inviting(executor_for)
        job, control = self.stores("one-effect")
        self.control = control
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(8):
            reconcile(job, operations, now=fixtures.NOW)
        attempt_id = self.only_attempt(control)
        domain = self.domain_of(control, attempt_id)
        # ONE INVITATION AND ONE EFFECT so far, both driven by the production publish.
        self.assertEqual(len(seen["invitations"]), 1, seen)
        executor = executors[attempt_id]
        self.assertEqual(len(executor.effects), 1)
        self.assertEqual(len(executor.receipts), 1)
        operations.close(); job.close(); control.close()

        resumed_job, resumed_control = self.stores("one-effect")
        self.control = resumed_control
        resumed = self.ticking(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        ticks = 0
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
            ticks += 1
        self.assertEqual(ticks, 8, "the resume was never driven")
        # ONE EFFECT IN TOTAL, and the recorder was attached the whole time.
        self.assertEqual(len(executor.effects), 1,
                         f"the resume invited another turn: {seen}")
        self.assertEqual(len(seen["invitations"]), 1, seen)
        self.assertEqual(len(seen["publications"]), 1,
                         f"the resume published again: {seen}")
        # NO FURTHER ACTIVATION OF THAT COMMAND'S CONTAINER either.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(engine.activations), 1)
        # AND THE RECEIPT IS STILL READABLE by the production observation, which is what
        # makes asking again unnecessary rather than merely skipped.
        after = exchange.observation(self._adopted(attempt_id))
        self.assertIsNotNone(after.get("receipt"))
        self.assertEqual(after["state"], "working")
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)

    def test_the_recorder_DOES_catch_a_duplicate_control_case(self):
        """A NEGATIVE CONTROL, and explicitly not an acceptance case.

        The review is right that a count can pass by never being given a chance to fire. So
        this deliberately consumes the same command twice and asserts the counter reaches two
        -- proving the instrument in the case above can detect a repeat, and that its result
        of one is a measurement rather than a silence.
        """
        engine = Engine()
        executors = {}

        def executor_for(delivery):
            return executors.setdefault(delivery.attempt_id, Executor(delivery))

        seen = self.inviting(executor_for)
        job, control = self.stores("duplicate-control")
        self.control = control
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        self.addCleanup(operations.close)
        for _ in range(8):
            reconcile(job, operations, now=fixtures.NOW)
        attempt_id = self.only_attempt(control)
        executor = executors[attempt_id]
        self.assertEqual(len(executor.effects), 1)
        self.assertEqual(len(seen["invitations"]), 1)
        # THE DELIBERATE REPEAT, by the fixture and labelled as such.
        executor.consume()
        self.assertEqual(len(executor.effects), 2,
                         "the recorder cannot detect a repeated effect at all")

    def test_a_receipt_with_no_terminal_is_WORKING_held_and_asks_nothing_further(self):
        """The unknown-provider-outcome half, with the exact values asserted.

        A receipt proves the turn was accepted and says NOTHING about whether it finished.
        `exchange.observation` answers `working` for that -- the module's own vocabulary, and
        deliberately not rounded to lost -- so the manager holds. Renamed from the earlier
        `INCOMPLETE` spelling, which review 2026-09-27T12-28-08Z correctly flagged as stale
        wording for a value the view never uses.

        The recorder stays attached here too, so "asks nothing further" is measured rather
        than assumed, and the stage's EXACT state is asserted rather than a not-in list.
        """
        engine = Engine()
        executors = {}

        def executor_for(delivery):
            return executors.setdefault(delivery.attempt_id, Executor(delivery))

        seen = self.inviting(executor_for)
        job, control = self.stores("provider-unknown")
        self.control = control
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(8):
            reconcile(job, operations, now=fixtures.NOW)
        attempt_id = self.only_attempt(control)
        domain = self.domain_of(control, attempt_id)
        executor = executors[attempt_id]
        self.assertEqual(len(executor.effects), 1)
        self.assertEqual(len(executor.receipts), 1)
        operations.close(); job.close(); control.close()

        resumed_job, resumed_control = self.stores("provider-unknown")
        self.control = resumed_control
        resumed = self.ticking(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        after = exchange.observation(self._adopted(attempt_id))
        self.assertIsNotNone(after.get("receipt"))
        self.assertIsNone(after.get("terminal"),
                          "a terminal exists, so this is not the unknown cut")
        self.assertEqual(after["state"], "working")
        # THE EXACT STAGE STATE, not a not-in list. MEASURED: `running`, which is the
        # honest projection for a receipted turn whose outcome nobody has established --
        # the worker accepted the command and the manager is waiting on an answer it has
        # not been given. It is deliberately NOT one of the success states, and the case
        # below the count asserts that nothing further was asked to reach it.
        stage = status(resumed_job, resumed,
                      observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "running")
        # AND NOTHING FURTHER WAS ASKED: one effect, one invitation, one publication, one
        # activation -- all counted by instruments that were attached throughout.
        self.assertEqual(len(executor.effects), 1)
        self.assertEqual(len(seen["invitations"]), 1, seen)
        self.assertEqual(len(seen["publications"]), 1, seen)
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(engine.activations), 1)
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(
        loader.loadTestsFromTestCase(
            TheProviderEffectIsPerformedOnceAcrossARestart)).wasSuccessful())
