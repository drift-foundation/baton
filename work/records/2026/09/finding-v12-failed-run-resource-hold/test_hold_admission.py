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
            worker.given["workspace_storage"], attempt_id, control=control)
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

    def test_a_composition_failure_now_lands_behind_a_committed_claim(self):
        """THE ORDERING R2 CHANGED, revalidated rather than left stale.

        Under R1 the vector was composed BEFORE the claim, so a failure here
        committed nothing and this case said so. R2's attribution work moved
        the claim FIRST -- the act carries the token that claim commits -- so
        composition now runs behind a committed episode, and a failure here
        leaves a DURABLE hold.

        THAT IS THE CONSERVATIVE DIRECTION and it is the same answer as the
        `_reconciled` interrupt below: the manager cannot compose the vector, so
        it cannot know whether an earlier incarnation submitted one, and the
        root stays frozen until somebody reconciles it. No engine vector is
        issued either way, which is what this case still asserts.

        Review 2026-09-24T22-22-09Z asked for exactly this revalidation.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-early")
        for engine in self.engines:
            engine.removed = True
        before = self.vectors()
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
        # THE CLAIM IS COMMITTED and the hold stands, uncleared.
        [standing] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(standing["cleared"])
        self.assertEqual(standing["episode"], 0)
        # AND NOTHING CROSSED TO THE ENGINE, which is the part that matters:
        # composition is where this died, so no act was ever submitted.
        self.assertEqual(self.vectors(), before)

    def test_a_committed_hold_survives_a_crash_before_any_engine_vector(self):
        """THE OTHER BOUNDARY, and the one R1 actually turns on.

        Owner 258324 selects the "committed-hold/pre-submission crash-and-
        reopen proof". Between `_claim_episode` committing and the custodian's
        request crossing there is a second interval, and the conservative
        answer there is the OPPOSITE of the composition case above: the hold
        must be durable, because a manager that died here cannot know whether
        anything ran.

        The interrupt is placed at `_reconciled`, which is the first thing
        after the claim and the first thing that would touch the engine -- so
        the crash lands with the hold committed and NOT ONE engine vector
        issued, which is the exact state this case is about.
        """
        control, _worker, composed, attempt_id, roots = self.held_root(
            "hold-committed")
        place = os.path.join(roots["workspace"], f"result-{attempt_id}")
        sentinel = os.path.join(place, "operator-must-see-this.txt")
        with open(sentinel, "w", encoding="utf-8") as writing:
            writing.write("committed hold, nothing submitted\n")
        bytes_before = self.walked(place)
        vectors_before = self.vectors()

        held_reconciled = custody._reconciled

        def dying(*arguments, **operands):
            del arguments, operands
            raise RuntimeError("the fixture died after the claim committed")

        custody._reconciled = dying
        self.addCleanup(setattr, custody, "_reconciled", held_reconciled)
        with self.assertRaises(RuntimeError):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        custody._reconciled = held_reconciled

        # NOT ONE VECTOR CROSSED, which is what makes this the pre-submission
        # boundary rather than the post-submission one.
        self.assertEqual(self.vectors(), vectors_before,
                         "an engine vector crossed before the submission")
        # AND THE HOLD IS COMMITTED ANYWAY.
        control.close()
        reopened = self.reopened("hold-committed-again")
        self.addCleanup(reopened.close)
        holds = custody.custody_holds(reopened, attempt_id, "result")
        self.assertEqual(len(holds), 1, holds)
        self.assertFalse(holds[0]["cleared"])
        self.assertEqual(holds[0]["episode"], 0)
        self.assertEqual(holds[0]["held"]["root"], "result")

        # THE REOPENED MANAGER IS BOUND BY IT and issues nothing of its own.
        with self.assertRaises(ContractRefusal) as caught:
            custody.normalize_directory(reopened, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertIn("FROZEN", caught.exception.message)
        self.assertEqual(self.vectors(), vectors_before,
                         "the reopened manager submitted or reclaimed")
        self.assertEqual(
            len(custody.custody_holds(reopened, attempt_id, "result")), 1)
        # AND THE ROOT KEEPS ITS BYTES across the whole of it.
        self.assertEqual(self.walked(place), bytes_before,
                         "the held root's bytes changed")

    # -- controlled contested admission --------------------------------------
    #
    # Owner 258324 selects "controlled contested-admission interleavings",
    # because review-2026-09-24T15-03-35Z found the barrier above only
    # STARTS the two callers: one can finish admission before the other
    # reaches its first hold read, so the race can pass through the ordinary
    # standing-hold refusal without ever exercising the two boundaries that
    # matter. These two cases force each of them by name.

    def paused_at(self, attribute, waiting):
        """Wrap one `custody` seam so a named thread stops inside it.

        `waiting` is asked, per call, what that thread should do; returning a
        callable runs it while the caller is held at that exact point. The
        real function still runs -- these interleavings are about WHEN the
        real code proceeds, never about what it answers.
        """
        held = getattr(custody, attribute)

        def hooked(*arguments, **operands):
            answer = held(*arguments, **operands)
            pause = waiting(threading.current_thread().name, answer)
            if pause is not None:
                pause()
            return answer

        setattr(custody, attribute, hooked)
        self.addCleanup(setattr, custody, attribute, held)

    def contesting(self, attempt_id, composed, answers, lock, *, before=None):
        """One racing caller, recording how its act ended.

        `before` is handed this caller's OWN store before it acts, so a case
        can wrap that connection's `transact` -- which is the one seam that is
        provably once per claim. `_hold_identity` is not: `custody_holds`
        computes one per episode it scans, so a hook there fires several times
        per call and cannot say which one is the commit.
        """
        def racing():
            opened = self.reopened(f"contest-{threading.get_ident()}")
            if before is not None:
                before(opened)
            try:
                try:
                    custody.normalize_directory(opened, composed,
                                                assignment_id=attempt_id,
                                                which="result")
                    ended = ("settled", None)
                except ContractRefusal as refusal:
                    ended = ("refused", refusal.message)
                except BaseException as other:           # pragma: no cover
                    ended = (type(other).__name__, str(other))
            finally:
                opened.close()
            with lock:
                answers.append((threading.current_thread().name, ended))

        return racing

    def joined(self, threads):
        for one in threads:
            one.start()
        for one in threads:
            one.join(timeout=30)
            self.assertFalse(one.is_alive(),
                             f"{one.name} never finished; the interleaving "
                             f"did not release it")

    def test_two_claimants_that_selected_one_episode_commit_only_one(self):
        """THE NONCE COLLISION, forced rather than hoped for.

        Both callers are held INSIDE their own `transact` call, after each has
        selected its episode and before either commits. Every argument to
        `transact` is evaluated by then -- the identity, the kind and the
        signed body -- so neither can have committed when the other chose,
        which is precisely the interleaving the start-barrier race could not
        guarantee and the one the submitter nonce exists for.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-contest-equal")
        self.severing()
        before = self.vectors()
        chosen, lock = [], threading.Lock()
        meeting = threading.Barrier(2, timeout=20)

        def wrapping(opened):
            held = opened.transact

            def transacting(identity, kind, signature, body, *rest, **named):
                if kind == custody.CUSTODY_HOLD_KIND:
                    with lock:
                        chosen.append(identity)
                    meeting.wait()
                return held(identity, kind, signature, body, *rest, **named)

            opened.transact = transacting

        answers = []
        threads = [threading.Thread(target=self.contesting(attempt_id,
                                                           composed, answers,
                                                           lock,
                                                           before=wrapping),
                                    name=f"claimant-{index}")
                   for index in range(2)]
        self.joined(threads)

        # THE INTERLEAVING HAPPENED: both selected, and they selected THE SAME
        # episode identity. Without this the case would be a race again.
        self.assertEqual(len(chosen), 2, chosen)
        self.assertEqual(len(set(chosen)), 1, chosen)

        self.assertEqual(len(answers), 2, answers)
        self.assertTrue(all(one[1][0] == "refused" for one in answers),
                        answers)
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 1, holds)
        self.assertFalse(holds[0]["cleared"])
        # ONE SUBMISSION, AND THE LOSER RECLAIMED NOTHING.
        after = self.vectors()
        self.assertEqual(after.get("run", 0) - before.get("run", 0), 1,
                         f"submissions for one episode: {after}")
        for verb in ("stop", "rm"):
            self.assertEqual(after.get(verb, 0) - before.get(verb, 0), 0,
                             f"a contested caller reclaimed: {after}")

    def test_a_stale_absence_loses_to_the_committed_episode(self):
        """THE IN-TRANSACTION RECHECK, forced rather than hoped for.

        The loser reads the holds FIRST, while there genuinely are none, and
        is then held there until the winner has committed episode 0 and
        submitted. When it resumes, its initial answer is stale and only the
        re-read inside `BEGIN IMMEDIATE` can catch it -- so this case fails if
        that recheck is ever removed, which the nonce alone would not.
        """
        control, _worker, composed, attempt_id, _roots = self.held_root(
            "hold-contest-stale")
        self.severing()
        before = self.vectors()
        lock = threading.Lock()
        winner_committed = threading.Event()
        loser_read = threading.Event()
        seen = []

        def waiting(name, answer):
            if name != "loser":
                return None
            with lock:
                seen.append(answer)
            if len(seen) > 1:               # the re-read inside the lock
                return None
            # THE STALE READ: no hold existed when the loser looked.
            self.assertIsNone(answer, "the loser's first read saw a hold")
            def holding():
                loser_read.set()
                if not winner_committed.wait(timeout=20):   # pragma: no cover
                    raise AssertionError("the winner never committed")
            return holding

        # W257624 R3 [P1]: THE SEAM MOVED BECAUSE THE ADMISSION READ MOVED.
        # This hooked `_standing_hold` and counted calls -- first the outer read,
        # second the locked re-read. `_standing_overlap` now asks
        # `_standing_hold` ONCE PER ROOT, so counting its calls no longer
        # separates the two reads and the loser started refusing at the outer one
        # instead, which is not what this case is about. Hooking the admission
        # read itself restores exactly the original interleaving: one call per
        # read, the stale None propagates into the transaction, and only the
        # locked re-read can catch it. Every assertion is unchanged.
        self.paused_at("_standing_overlap", waiting)
        answers = []
        loser = threading.Thread(target=self.contesting(attempt_id, composed,
                                                        answers, lock),
                                 name="loser")
        loser.start()
        self.assertTrue(loser_read.wait(timeout=20),
                        "the loser never reached its first hold read")

        # NOW the winner runs to completion, on its own connection.
        winner = threading.Thread(target=self.contesting(attempt_id, composed,
                                                         answers, lock),
                                  name="winner")
        winner.start()
        winner.join(timeout=30)
        self.assertFalse(winner.is_alive(), "the winner never finished")
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 1, holds)
        winner_committed.set()
        loser.join(timeout=30)
        self.assertFalse(loser.is_alive(), "the loser never finished")

        ended = dict(answers)
        self.assertEqual(ended["winner"][0], "refused")     # the engine died
        self.assertEqual(ended["loser"][0], "refused")
        # THE LOSER REFUSED ON THE RE-READ, naming the episode it did not see
        # the first time, and saying it submitted nothing.
        self.assertIn("nothing was submitted", ended["loser"][1])
        self.assertGreaterEqual(len(seen), 2,
                                "the loser never re-read inside the lock")
        self.assertEqual(
            len(custody.custody_holds(control, attempt_id, "result")), 1)
        after = self.vectors()
        self.assertEqual(after.get("run", 0) - before.get("run", 0), 1,
                         f"submissions for one episode: {after}")
        for verb in ("stop", "rm"):
            self.assertEqual(after.get(verb, 0) - before.get(verb, 0), 0,
                             f"the losing caller reclaimed: {after}")

    # -- the runner root -----------------------------------------------------

    def test_the_runner_root_is_disk_backed_and_used_in_isolation(self):
        """The root owner 258324 selected, VERIFIED rather than assumed.

        The previous round created `/var/tmp/baton-w257624` without a grant
        and said so. The owner has now selected it, on the condition that
        disk-backed storage and ownership are verified, existing contents are
        preserved, and the tests use isolated roots. This case is that check,
        and it fails the run rather than the reviewer's patience if the runner
        is ever pointed somewhere else.
        """
        from baton_v12.worker_manager.source_boundary import (
            MEMORY_FILESYSTEMS, filesystem_of)
        from tests.manager import disk_roots

        named = os.environ.get(disk_roots.VARIABLE)
        if named is None:                                # pragma: no cover
            self.skipTest(f"{disk_roots.VARIABLE} is unset; this case is "
                          f"about the root the owner selected")
        # DISK-BACKED, by the product's own reader rather than by a name.
        self.assertNotIn(filesystem_of(named), MEMORY_FILESYSTEMS)
        # OWNED AND WRITABLE BY THIS PROCESS.
        self.assertEqual(os.stat(named).st_uid, os.getuid())
        self.assertTrue(os.access(named, os.W_OK))
        # OUTSIDE THE CHECKOUT, so nothing here can touch source or snapshots.
        checkout = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
        self.assertFalse(os.path.abspath(named).startswith(
            os.path.abspath(checkout) + os.sep))
        # AND THIS CASE'S OWN ROOT IS AN ISOLATED CHILD OF IT, not the root
        # itself -- which is what keeps existing contents preserved.
        standing = sorted(os.listdir(named))
        mine = disk_roots.disk_backed_under(self)
        self.assertEqual(os.path.dirname(os.path.abspath(mine)),
                         os.path.abspath(named))
        self.assertTrue(os.path.basename(mine).startswith("v12-w71917-"))
        self.assertEqual(sorted(one for one in os.listdir(named)
                                if one != os.path.basename(mine)), standing,
                         "an existing entry under the selected root moved")

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
