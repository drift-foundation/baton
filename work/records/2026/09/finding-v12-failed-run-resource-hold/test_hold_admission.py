"""R1: ONE exclusive submission before any destructive helper act.

Owner 257693 selects R1 only: "Demonstrate one submitter, no submission or
reclamation behind a standing hold, and durable crash/reopen behavior using
real stores and fake engine."

WHAT IS REAL HERE: the manager's own `custody_act`, its own `ControlStore`
transactions, and real directories on a disk-backed root. The ENGINE is the
accepted fake port every focused case in this campaign uses, so no daemon,
container or image is reached, and a timeout here proves nothing about a
daemon -- which is exactly why the hold exists.

THE RACE IS BARRIER-DRIVEN, not slept: two threads on two connections meet at
a `threading.Barrier` and then both try to claim. Sleep ordering would prove
whichever order the sleep produced.
"""
import json
import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import custody                   # noqa: E402
from baton_v12.worker_manager import workspaces                # noqa: E402

from test_abandonment import TheComposedAbandonmentIsCalled    # noqa: E402


class TheHoldAdmitsExactlyOneSubmitter(TheComposedAbandonmentIsCalled):
    """The parent fixture's real faulted attempt, asked a narrower question."""

    def held_root(self, incarnation):
        """A real attempt, its real roots, and the composed custody adapter."""
        held, _stage = self.faulted_with_stage(incarnation)
        control, worker, attempt_id = held[1], held[2]._worker, held[5]
        roots = workspaces.adopted_assignment_workspace(
            worker.given["workspace_storage"], attempt_id)
        return control, worker, worker._adapter(roots, None, None,
                                                None), attempt_id, roots

    def severing(self, *, after=None):
        """Make the custodian's own vector produce NO engine answer.

        That is the one shape the hold is for: the request crossed and nothing
        came back. `after` lets a case sever only once, so a later act can be
        allowed to answer.
        """
        seen = []
        for engine in self.engines:
            held_acting = engine.__class__.acting

            def severed(one, argv, mount, verb, _held=held_acting):
                # RECORDED ON THE ENGINE, exactly as the real `acting` does:
                # a submission that crossed is a vector this fixture issued,
                # whether or not anything answered it. Counting only in a
                # private list would have hidden the submission from
                # `vectors()` -- which it did, until this line.
                one.vectors.append(list(argv))
                seen.append(list(argv))
                if after is None or len(seen) <= after:
                    raise RuntimeError("the fixture killed the client")
                return _held(one, argv, mount, verb)

            engine.__class__.acting = severed
            self.addCleanup(setattr, engine.__class__, "acting", held_acting)
            # THE PRE-ACT RECONCILIATION ANSWERS "NOTHING STRANDED", which is
            # the fake's post-removal listing. Without it the base listing
            # answers a worker row the custody reader rightly rejects, and
            # these cases would be about that instead.
            engine.removed = True
        return seen

    def vectors(self):
        """Every engine vector this fixture has been asked for, by verb."""
        counted = {}
        for engine in self.engines:
            for vector in engine.vectors:
                verb = vector[1] if len(vector) > 1 else None
                counted[verb] = counted.get(verb, 0) + 1
        return counted

    # -- one submitter -------------------------------------------------------

    def test_two_racing_callers_produce_exactly_one_submission(self):
        """A BARRIER, two connections, and one winner.

        Both threads reach the claim together. One owns episode 0; the other
        refuses, and the refusal must arrive having submitted nothing.
        """
        control, worker, composed, attempt_id, _roots = self.held_root(
            "hold-race")
        self.severing()
        before = self.vectors()

        # TWO CONNECTIONS, as the plan requires and as SQLite enforces: a
        # store's connection belongs to the thread that opened it, so a
        # one-connection "race" would not be one. Each racer opens its own
        # handle on the same file, which is what two managers actually are.
        start = threading.Barrier(2, timeout=10)
        answers = []
        lock = threading.Lock()

        def racing():
            opened = self.reopened(f"race-{threading.get_ident()}")
            try:
                start.wait()
                try:
                    custody.normalize_directory(opened, composed,
                                                assignment_id=attempt_id,
                                                which="result")
                    answered = ("settled", None)
                except ContractRefusal as refusal:
                    answered = ("refused", refusal.message)
                except BaseException as other:           # pragma: no cover
                    answered = (type(other).__name__, str(other))
            finally:
                opened.close()
            with lock:
                answers.append(answered)

        threads = [threading.Thread(target=racing) for _ in range(2)]
        for one in threads:
            one.start()
        for one in threads:
            one.join(timeout=20)
            self.assertFalse(one.is_alive(), "a racing caller never finished")

        self.assertEqual(len(answers), 2, answers)
        # NEITHER SETTLES -- the engine answered nothing, so both endings are
        # refusals. What this case is about is how MANY of them submitted.
        self.assertTrue(all(one[0] == "refused" for one in answers), answers)

        # EXACTLY ONE EPISODE EXISTS, so exactly one caller claimed.
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 1, holds)
        self.assertFalse(holds[0]["cleared"])

        # AND EXACTLY ONE SUBMISSION CROSSED. The custodian's own vector is
        # the submission; the loser issued none.
        after = self.vectors()
        submits = after.get("run", 0) - before.get("run", 0)
        self.assertEqual(submits, 1,
                         f"{submits} submissions crossed for one episode: "
                         f"{after}")
        del worker

    def test_a_held_root_admits_no_submission_and_no_reclamation(self):
        """THE HELD PATH ISSUES NOTHING AT ALL.

        Owner 257693: "no submission OR RECLAMATION behind a standing hold".
        The reconciliation used to run first, so a second caller listed the
        engine and would have stopped and removed a stranded candidate before
        anything checked. Those are destructive vectors on a path that must
        issue none.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-shut")
        self.severing()
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        [episode] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(episode["cleared"])

        before = self.vectors()
        with self.assertRaises(ContractRefusal) as caught:
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertIn("FROZEN", caught.exception.message)
        self.assertIn("no submission, no reclamation",
                      caught.exception.message)
        # NOT ONE VECTOR of any kind, which is stronger than "no stop or
        # remove" and is what "before submission or reclamation" means.
        self.assertEqual(self.vectors(), before,
                         "the held path touched the engine")

    def test_a_late_visible_helper_is_not_reclaimed_behind_the_hold(self):
        """A helper APPEARS afterwards, and the held path still touches it not.

        This is the case the hold exists for: the daemon's accepted request
        creates the helper after the client died. A second act must not stop
        it, remove it, or treat its presence as permission.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-late")
        self.severing()
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        [episode] = custody.custody_holds(control, attempt_id, "result")
        helper = episode["held"]["helper_identity"]

        # THE HELPER IS NOW VISIBLE to the engine, named exactly as the hold
        # records it.
        for engine in self.engines:
            engine.removed = False
            engine.runtime_id = helper
            engine.labels = {}
            engine.image = episode["held"]["custodian_image_digest"]

        before = self.vectors()
        with self.assertRaises(ContractRefusal) as caught:
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertIn("FROZEN", caught.exception.message)
        self.assertIn(helper, caught.exception.message)
        self.assertEqual(self.vectors(), before,
                         "a late helper was observed or reclaimed behind a "
                         "standing hold")

    # -- durability ----------------------------------------------------------

    def test_the_episode_survives_a_reopen_of_the_store(self):
        """CRASH AFTER SUBMISSION: the hold is durable, not in memory.

        The store is closed and reopened on the same file, which is what a
        restarted manager does.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-reopen")
        self.severing()
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        control.close()

        reopened = self.reopened("hold-reopen-again")
        self.addCleanup(reopened.close)
        holds = custody.custody_holds(reopened, attempt_id, "result")
        self.assertEqual(len(holds), 1, holds)
        self.assertFalse(holds[0]["cleared"])
        self.assertEqual(holds[0]["held"]["root"], "result")
        # AND THE REOPENED MANAGER IS BOUND BY IT, having issued nothing.
        before = self.vectors()
        with self.assertRaises(ContractRefusal) as caught:
            custody.normalize_directory(reopened, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertIn("FROZEN", caught.exception.message)
        self.assertEqual(self.vectors(), before)

    def test_a_crash_before_submission_leaves_no_episode(self):
        """CRASH BEFORE SUBMISSION: nothing is claimed and nothing is held.

        Everything before the request crosses is a refusal that submitted
        nothing, and it must keep committing nothing -- which is the accepted
        rule this stage must not break.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-early")
        for engine in self.engines:
            engine.removed = True
        held_vector = custody._custody_vector

        def failing(*arguments, **operands):
            del arguments, operands
            raise RuntimeError("the fixture died composing the vector")

        custody._custody_vector = failing
        self.addCleanup(setattr, custody, "_custody_vector", held_vector)
        with self.assertRaises(RuntimeError):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        custody._custody_vector = held_vector
        self.assertEqual(custody.custody_holds(control, attempt_id, "result"),
                         [], "a pre-submission death claimed an episode")

    def test_the_held_root_keeps_its_bytes(self):
        """NOTHING UNDER THE HELD ROOT CHANGES -- measured, not asserted."""
        control, _worker, composed, attempt_id, roots = self.held_root(
            "hold-bytes")
        place = os.path.join(roots["workspace"],
                             f"result-{attempt_id}")
        sentinel = os.path.join(place, "operator-must-see-this.txt")
        with open(sentinel, "w", encoding="utf-8") as writing:
            writing.write("the held tree is untouched\\n")
        before = self.walked(place)

        self.severing()
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertEqual(self.walked(place), before,
                         "the held root's bytes changed")

    def reopened(self, incarnation):
        """A SECOND manager over the same control store file."""
        from baton_v12.worker_manager import ControlStore
        from tests.job_manager import fixtures

        return ControlStore.open(self.control_path, incarnation=incarnation,
                                 clock=lambda: fixtures.NOW)

    @staticmethod
    def walked(place):
        """Every path and its bytes under one root."""
        found = {}
        for current, _directories, files in os.walk(place):
            for name in sorted(files):
                one = os.path.join(current, name)
                with open(one, "rb") as reading:
                    found[os.path.relpath(one, place)] = reading.read()
        return found

    def test_the_record_replay_does_not_authorize_a_second_submitter(self):
        """"Replay of the record must not authorize a second caller to submit."

        The episode's own identity replays its document to anyone who asks --
        that is what a journal does. What must NOT follow is a second act
        treating that replay as its own claim.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-replay")
        self.severing()
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        [episode] = custody.custody_holds(control, attempt_id, "result")
        identity = custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                          attempt_id, "result", 0)
        record = control.operation_record(identity)
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["kind"], custody.CUSTODY_HOLD_KIND)
        # THE CLAIMANT IS RECORDED, which is what makes one submitter
        # distinguishable from another at one identity.
        self.assertTrue(json.loads(record["result"])["claimant"])

        before = self.vectors()
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertEqual(self.vectors(), before)
        self.assertEqual(
            len(custody.custody_holds(control, attempt_id, "result")), 1)
        del episode


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only this module's own cases."""
    suite = unittest.TestSuite()
    for name in loader.getTestCaseNames(TheHoldAdmitsExactlyOneSubmitter):
        if name in TheHoldAdmitsExactlyOneSubmitter.__dict__:
            suite.addTest(TheHoldAdmitsExactlyOneSubmitter(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
