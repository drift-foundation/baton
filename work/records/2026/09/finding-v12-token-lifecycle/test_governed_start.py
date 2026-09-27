"""W275774 — the CONNECTED caller: a governed start through request_runtime_start.

Review 15:28:31Z: "proceed to actual production caller next", and demonstrate that
the caller reserves ONE external crossing, that retries reconcile onto it, and that
a late call holds through a conclusive outcome.

TWO CORRECTIONS FROM REVIEW 15:39:57Z, both mine and both recorded here rather than
quietly fixed:

  * MY MODULE PROSE WAS WRONG. This file said these cases "drive the real
    `attempts.request_runtime_start`". They did not -- the first eight exercise the
    GOVERNANCE COMPOSITION (`reserve`, `bind`, `settle`) and the domain mapping. That
    is worth having and it is not the same claim. The end-to-end case at the bottom
    is the one that drives the real function.
  * AND I SAID NO NON-LIVE FIXTURE EXISTED for this seam. It does: the reviewer
    reached it with `TheRuntimeIsStartedOnceAndReconciled.activated` plus
    `pin_boundary_identity`, which is the approach the last case here borrows. My
    claim was an assumption I had not tested, stated as a finding.

Real disposable `ControlStore`, the attempts suite's own controlled adapter double,
no live engine, no provider, no container created or signalled.
"""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts, tokens

from tests.manager.test_attempts import ATTEMPT, AttemptCase
from tests.manager.test_intake import (RETENTION, Custodian,
                                       RetainedAndCompleteAreDifferentEndings)
from baton_v12.worker_manager import intake


class GovernedStart(AttemptCase):
    """The production seam, with the token authority actually attached."""

    def attempt_row(self, attempt_id=ATTEMPT):
        return attempts._require_attempt(self.store, attempt_id)

    def domain(self):
        return tokens.domain_of("workspace",
                                tokens.workspace_identity(self.attempt_row()))

    # -- what the governance itself names --------------------------------------

    def test_the_governed_domain_is_the_workspace_object_not_the_attempt(self):
        """TOK-2 at the caller: the domain must not vary per attempt.

        `workspace_identity` reads the PINNED boundary identity, so two attempts
        over one workspace object resolve to one domain. This asserts the mapping
        directly, which is the part the domain argument still owes -- see the
        function's own docstring: naming the same object is not yet a proof that
        every overlapping resource maps to one domain.
        """
        first = tokens.workspace_identity(
            {"runtime_attempt_id": "attempt-a", "workspace_device": 66,
             "workspace_inode": 1234})
        second = tokens.workspace_identity(
            {"runtime_attempt_id": "attempt-b", "workspace_device": 66,
             "workspace_inode": 1234})
        self.assertEqual(first, second)
        self.assertEqual(tokens.domain_of("workspace", first),
                         tokens.domain_of("workspace", second))
        beside = tokens.workspace_identity(
            {"runtime_attempt_id": "attempt-c", "workspace_device": 66,
             "workspace_inode": 9999})
        self.assertNotEqual(first, beside)

    def test_an_unpinned_workspace_cannot_be_governed(self):
        """A governed start needs the boundary identity first, and says so."""
        with self.assertRaises(ContractRefusal) as caught:
            tokens.workspace_identity({"runtime_attempt_id": "attempt-a",
                                       "workspace_device": None,
                                       "workspace_inode": None})
        self.assertIn("no pinned workspace object", caught.exception.message)

    # -- the reservation, and the single crossing -------------------------------

    def test_a_reservation_journals_the_launch_under_the_start_operation(self):
        """THE LAUNCH THE TOKEN NAMES IS THE JOURNALLED START.

        Not a second act adjacent to it: the reservation is taken with the start
        operation's own identity, which is what lets a restart ask one question
        about one act instead of correlating two.
        """
        attempt = {"runtime_attempt_id": ATTEMPT, "workspace_device": 66,
                   "workspace_inode": 4242}
        governance = tokens.workspace_governance()
        reservation = governance.reserve(self.store, attempt,
                                        operation="runtime.start:op-1")
        domain = tokens.domain_of("workspace", "66:4242")
        current = tokens.token_of(self.store, domain, 1)
        self.assertEqual(current["launch"], "runtime.start:op-1")
        self.assertEqual(current["execution"], ATTEMPT)
        self.assertIsNone(current["container"])
        self.assertEqual(reservation.launch, "runtime.start:op-1")

    def test_a_retried_reservation_replays_its_own_generation(self):
        """THE RESERVATION HALF of the single-crossing property, and only that half.

        Review 15:39:57Z is right that my earlier name and claim overreached: this
        asserts that a repeated reservation of one operation replays its own
        generation instead of allocating a second. That is necessary for one external
        crossing and it is not sufficient, because nothing here observes the engine.
        The crossing itself is counted in the end-to-end case below.
        """
        attempt = {"runtime_attempt_id": ATTEMPT, "workspace_device": 66,
                   "workspace_inode": 4242}
        governance = tokens.workspace_governance()
        first = governance.reserve(self.store, attempt,
                                  operation="runtime.start:op-1")
        again = governance.reserve(self.store, attempt,
                                  operation="runtime.start:op-1")
        self.assertEqual(again.token["generation"], first.token["generation"])
        self.assertEqual(again.token["owner"], first.token["owner"])
        domain = tokens.domain_of("workspace", "66:4242")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    def test_a_competing_attempt_over_one_workspace_is_refused(self):
        """SHARED-DOMAIN EXCLUSION at the caller, not only in the token."""
        governance = tokens.workspace_governance()
        governance.reserve(self.store,
                           {"runtime_attempt_id": "attempt-a",
                            "workspace_device": 66, "workspace_inode": 4242},
                           operation="runtime.start:a")
        with self.assertRaises(ContractRefusal) as caught:
            governance.reserve(self.store,
                               {"runtime_attempt_id": "attempt-b",
                                "workspace_device": 66, "workspace_inode": 4242},
                               operation="runtime.start:b")
        self.assertIn("is owned by token generation 1", caught.exception.message)

    def test_an_unrelated_workspace_proceeds(self):
        governance = tokens.workspace_governance()
        governance.reserve(self.store,
                           {"runtime_attempt_id": "attempt-a",
                            "workspace_device": 66, "workspace_inode": 4242},
                           operation="runtime.start:a")
        beside = governance.reserve(
            self.store, {"runtime_attempt_id": "attempt-b",
                         "workspace_device": 66, "workspace_inode": 5555},
            operation="runtime.start:b")
        self.assertEqual(beside.token["generation"], 1)

    # -- the reservation's own acts, in the order the adapter performs them -----

    def test_the_reservation_binds_then_admits_then_settles(self):
        """THE ORDER THE ADAPTER DRIVES, asked of the records it leaves.

        `bind` is called between the engine's create and start and answers the
        ADMISSION capability; `settle` is called only once the adapter answered.
        """
        attempt = {"runtime_attempt_id": ATTEMPT, "workspace_device": 66,
                   "workspace_inode": 4242}
        reservation = tokens.workspace_governance().reserve(
            self.store, attempt, operation="runtime.start:op-1")
        domain = tokens.domain_of("workspace", "66:4242")
        permit = reservation.bind("runtime-1")
        self.assertEqual(tokens.token_of(self.store, domain, 1)["container"],
                         "runtime-1")
        self.assertFalse(tokens.token_of(self.store, domain, 1)["activating"],
                         "binding is not yet an admitted activation")
        admitted = permit()
        self.assertEqual(admitted["container"], "runtime-1")
        self.assertTrue(tokens.token_of(self.store, domain, 1)["activating"])
        # AND THE HOLD STANDS until the outcome is conclusive.
        with self.assertRaises(ContractRefusal):
            tokens.returned(self.store, reservation.token, cessation={
                "domain": domain, "generation": 1,
                "launch": "runtime.start:op-1", "container": "runtime-1",
                "stopped": True, "helpers": []})
        reservation.settle("runtime-1")
        self.assertFalse(tokens.token_of(self.store, domain, 1)["activating"])
        self.assertTrue(
            tokens.token_of(self.store, domain, 1)["activation_started"])

    def test_a_late_permit_after_settlement_admits_nothing(self):
        """THE LATE CALL, held through the conclusive outcome.

        A starter that wakes up after its activation was settled holds a permit
        that must no longer admit anything: what it names is history.
        """
        attempt = {"runtime_attempt_id": ATTEMPT, "workspace_device": 66,
                   "workspace_inode": 4242}
        reservation = tokens.workspace_governance().reserve(
            self.store, attempt, operation="runtime.start:op-1")
        permit = reservation.bind("runtime-1")
        permit()
        reservation.settle("runtime-1")
        with self.assertRaises(ContractRefusal) as caught:
            permit()
        self.assertIn("already been settled", caught.exception.message)


class GovernedStartEndToEnd(unittest.TestCase):
    """THE REAL FUNCTION, driven with governance attached and no live engine.

    Review 15:39:57Z showed that the deterministic path exists -- the activated
    fixture plus `pin_boundary_identity` -- after I had claimed it did not. This
    borrows exactly that approach and counts what the engine was actually asked to
    do, which is the part the composition cases above cannot establish.
    """

    def fixture(self):
        from tests.manager.test_attempts import TheRuntimeIsStartedOnceAndReconciled
        case = TheRuntimeIsStartedOnceAndReconciled()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.activated()
        attempts.pin_boundary_identity(case.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        return case

    def adapter(self):
        """A controlled adapter that honours the two-act contract and COUNTS calls."""
        from tests.manager.test_attempts import Adapter

        class Counting(Adapter):
            def __init__(self):
                super().__init__()
                self.admissions = []

            def start(self, request, *, bind=None):
                self.admissions.append(bind("runtime-1")())
                return super().start(request)

        return Counting()

    def test_the_real_caller_reserves_binds_admits_and_settles_once(self):
        case = self.fixture()
        adapter = self.adapter()
        answer = attempts.request_runtime_start(
            case.store, adapter, attempt_id=ATTEMPT,
            govern=tokens.workspace_governance())
        self.assertEqual(answer["decision"], "attached")
        # ONE CROSSING, counted at the adapter rather than inferred.
        self.assertEqual(len(adapter.started), 1)
        self.assertEqual(len(adapter.admissions), 1)
        self.assertEqual(adapter.admissions[0]["container"], "runtime-1")
        current = tokens.token_of(case.store, "workspace:66:4242", 1)
        self.assertEqual(current["container"], "runtime-1")
        self.assertEqual(current["launch"], current["operation"])
        self.assertTrue(current["activation_started"],
                        "the answered start is a conclusive activation")
        self.assertFalse(current["activating"])

    def test_a_refused_reservation_leaves_no_pending_unsubmitted_start(self):
        """THE DEFECT REVIEW 15:39:57Z FOUND, as my own case.

        The reservation sat after the start and lane commit and outside the failure
        handling, so a conflicting reservation left the attempt recorded as
        start-requested with the adapter never called. It now takes the same
        settlement boundary every other pre-engine failure takes -- and NOTHING
        CROSSED, which is what makes that honest rather than a guess.
        """
        case = self.fixture()
        tokens.acquire(case.store, "workspace:66:4242", operation="somebody-else",
                       execution="attempt-other", attempt="attempt-other")
        adapter = self.adapter()
        with self.assertRaises(ContractRefusal):
            attempts.request_runtime_start(
                case.store, adapter, attempt_id=ATTEMPT,
                govern=tokens.workspace_governance())
        self.assertEqual(adapter.started, [], "the engine was never reached")
        self.assertEqual(adapter.admissions, [])
        self.assertNotEqual(case.row()["execution_runtime"], "start-requested")


class TheResourceIsReturned(AttemptCase):
    """THE OTHER END OF THE LIFECYCLE, corrected per review 15:55:27Z.

    Two corrections from that review are asserted here rather than only described:
    the return is bound to the execution and operation THAT RESERVED the generation,
    not to whatever is outstanding now; and the cessation is the caller's evidence,
    never synthesized from a state column with an assumed absence of writers.
    """

    def attempt(self, attempt_id=ATTEMPT, inode=4242):
        return {"runtime_attempt_id": attempt_id, "workspace_device": 66,
                "workspace_inode": inode}

    def evidence(self, container="runtime-1", stopped=True, helpers=()):
        return {"container": container, "stopped": stopped,
                "helpers": list(helpers)}

    def governed(self, attempt_id=ATTEMPT, container="runtime-1"):
        governance = tokens.workspace_governance()
        operation = f"runtime.start:{attempt_id}"
        reservation = governance.reserve(self.store, self.attempt(attempt_id),
                                        operation=operation)
        reservation.bind(container)()
        reservation.settle(container)
        return governance, operation

    def test_a_confirmed_return_hands_the_workspace_to_the_next_attempt(self):
        """THE PROPERTY WHOSE ABSENCE MADE A GOVERNED START ONE-SHOT."""
        governance, operation = self.governed()
        domain = tokens.domain_of("workspace", "66:4242")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        governance.release(self.store, self.attempt(), operation=operation,
                           cessation=self.evidence())
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        second = governance.reserve(self.store, self.attempt("attempt-2"),
                                   operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)

    def test_a_stale_return_after_generation_two_does_not_release_it(self):
        """REVIEW 15:55:27Z ASKED FOR THIS BY NAME, and it is the sharp one.

        The previous cut returned "the one outstanding generation", so a recovery
        arriving late -- after generation 1 was returned and generation 2 acquired --
        would have released GENERATION 2: somebody else's live hold, freed by a
        message about a dead one. The return now resolves the generation from the
        execution and operation that reserved it, so the stale message finds its own
        already-returned generation and stops.
        """
        governance, operation = self.governed()
        domain = tokens.domain_of("workspace", "66:4242")
        governance.release(self.store, self.attempt(), operation=operation,
                           cessation=self.evidence())
        second = governance.reserve(self.store, self.attempt("attempt-2"),
                                   operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)
        # THE LATE MESSAGE ABOUT GENERATION 1, replayed after generation 2 exists.
        self.assertIsNone(
            governance.release(self.store, self.attempt(), operation=operation,
                               cessation=self.evidence()))
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [2],
                         "generation 2 must still hold the resource")

    def test_the_generation_is_found_by_its_own_execution_and_operation(self):
        governance, operation = self.governed()
        domain = tokens.domain_of("workspace", "66:4242")
        self.assertEqual(
            tokens.generation_of(self.store, domain, execution=ATTEMPT,
                                 operation=operation), 1)
        self.assertIsNone(
            tokens.generation_of(self.store, domain, execution="somebody-else",
                                 operation=operation))
        self.assertIsNone(
            tokens.generation_of(self.store, domain, execution=ATTEMPT,
                                 operation="some-other-start"))

    def test_an_ending_that_reserved_nothing_is_refused_not_guessed(self):
        governance, _ = self.governed()
        with self.assertRaises(ContractRefusal) as caught:
            governance.release(self.store, self.attempt(),
                               operation="a-start-that-never-happened",
                               cessation=self.evidence())
        self.assertIn("there is nothing this ending can return",
                      caught.exception.message)

    def test_a_repeated_return_is_idempotent_rather_than_fatal(self):
        governance, operation = self.governed()
        governance.release(self.store, self.attempt(), operation=operation,
                           cessation=self.evidence())
        self.assertIsNone(
            governance.release(self.store, self.attempt(), operation=operation,
                               cessation=self.evidence()))

    def test_the_cessation_document_is_required_in_full(self):
        """NOTHING IS DEFAULTED: not the termination, not the absence of writers."""
        governance, operation = self.governed()
        for missing in ("container", "stopped", "helpers"):
            offered = self.evidence()
            offered.pop(missing)
            with self.subTest(missing=missing):
                with self.assertRaises(ContractRefusal):
                    governance.release(self.store, self.attempt(),
                                       operation=operation, cessation=offered)

    def test_an_unconfirmed_stop_returns_nothing(self):
        governance, operation = self.governed()
        domain = tokens.domain_of("workspace", "66:4242")
        for offered in (False, "true", None):
            with self.subTest(stopped=offered):
                with self.assertRaises(ContractRefusal):
                    governance.release(
                        self.store, self.attempt(), operation=operation,
                        cessation=self.evidence(stopped=offered))
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    def test_evidence_about_another_container_returns_nothing(self):
        governance, operation = self.governed()
        with self.assertRaises(ContractRefusal) as caught:
            governance.release(
                self.store, self.attempt(), operation=operation,
                cessation=self.evidence(container="somebody-elses-runtime"))
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_a_surviving_helper_holds_the_workspace(self):
        governance, operation = self.governed()
        domain = tokens.domain_of("workspace", "66:4242")
        with self.assertRaises(ContractRefusal) as caught:
            governance.release(self.store, self.attempt(), operation=operation,
                               cessation=self.evidence(helpers=["writer-1"]))
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)


class TheConflictDomainExcludesOVERLAP(unittest.TestCase):
    """W275774 review 18:27:07Z: PROCEED NOW WITH THE OVERLAP EXCLUSION.

    This is the argument I have owed since 14:41:35Z and have never claimed settled.
    The token owner serializes on a string and holds no paths, so it can say two
    attempts naming ONE object share a domain -- and it cannot say two attempts naming
    DIFFERENT objects are not writing the same tree. Nested roots can differ by inode
    while sharing writable descendants, which would be an exclusion with a hole in it.

    The argument lives with the containment owner, which has the paths:
    `workspaces.governed_resource_identity` answers `device:inode` ONLY after checking
    that the root sits in the sibling position the configured storage arranges. Two
    attempts' governed roots are therefore SIBLINGS, and siblings cannot contain one
    another.
    """

    def setUp(self):
        import os
        import tempfile

        from baton_v12.worker_manager import workspaces
        from baton_v12.worker_manager.store import ControlStore
        from tests.manager import input_roots

        room = tempfile.TemporaryDirectory(prefix="v12-overlap-")
        self.addCleanup(room.cleanup)
        self.root = room.name
        self.store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"), incarnation="overlap-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage, exist_ok=True)
        workspaces.configure_workspace_storage(self.store, self.storage)
        self.group = input_roots.configured_group(self.store)
        self.workspaces = workspaces

    def allocated(self, assignment_id):
        self.workspaces.assignment_workspace(self.group, self.storage,
                                             assignment_id)
        return self.workspaces.governed_resource_identity(self.store,
                                                          assignment_id)

    def test_two_attempts_over_one_object_share_one_domain(self):
        """The property the token owner already had, re-asked through the argued
        identity so the two halves are known to agree."""
        first = self.allocated("attempt-a")
        again = self.workspaces.governed_resource_identity(self.store, "attempt-a")
        self.assertEqual(first, again)
        self.assertEqual(tokens.domain_of("workspace", first),
                         tokens.domain_of("workspace", again))

    def test_two_attempts_ARE_SIBLINGS_and_so_cannot_overlap(self):
        """THE OVERLAP EXCLUSION ITSELF.

        Distinct attempts get distinct identities, AND the reason those identities are
        safe to treat as distinct resources is structural: each root is checked to sit
        directly under its own attempt home inside one configured storage, so neither
        can contain the other. Asserted on the real filesystem rather than argued.
        """
        import os

        one = self.allocated("attempt-a")
        two = self.allocated("attempt-b")
        self.assertNotEqual(one, two)
        first = os.path.join(self.storage, "attempt-a", "workspace")
        second = os.path.join(self.storage, "attempt-b", "workspace")
        self.assertFalse(self.workspaces._within(first, second))
        self.assertFalse(self.workspaces._within(second, first))
        # AND THE PREFIX TRAP, which is why containment compares segments: a name that
        # merely starts with another is not inside it.
        self.assertFalse(self.workspaces._within(
            os.path.join(self.storage, "attempt-a-other", "workspace"), first))

    def test_a_root_outside_its_sibling_position_is_REFUSED(self):
        """A resource whose position cannot be shown is one whose overlap cannot be
        excluded, so no identity is answered for it at all."""
        import os

        self.allocated("attempt-a")
        # attempt-b's home is a LINK into attempt-a's tree: the object it reaches is
        # inside another attempt's governed root, which is exactly the arrangement an
        # identity must not paper over.
        home = os.path.join(self.storage, "attempt-b")
        os.makedirs(home, exist_ok=True)
        os.symlink(os.path.join(self.storage, "attempt-a", "workspace"),
                   os.path.join(home, "workspace"))
        with self.assertRaises(ContractRefusal) as caught:
            self.workspaces.governed_resource_identity(self.store, "attempt-b")
        self.assertIn("overlap cannot be excluded", caught.exception.message)

    def test_a_symlinked_HOME_is_refused_too_which_my_own_case_had_missed(self):
        """THE P1 FROM REVIEW 18:33:48Z, as my own case.

        My negative case symlinked the WORKSPACE. An independent probe symlinked the
        HOME -- `storage/attempt-b` pointed at `attempt-a/workspace` -- so the root
        became `attempt-a/workspace/workspace`, nested inside attempt-a's writable tree,
        with `dirname(root) == home` satisfied and the home still "within" the storage.
        Two overlapping trees, two identities, and my check passed it.

        The sibling property is that the home is a DIRECT CHILD of the storage, and that
        is what is now required.
        """
        import os

        self.allocated("attempt-a")
        os.symlink(os.path.join(self.storage, "attempt-a", "workspace"),
                   os.path.join(self.storage, "attempt-b"))
        with self.assertRaises(ContractRefusal) as caught:
            self.workspaces.governed_resource_identity(self.store, "attempt-b")
        self.assertIn("not a direct child", caught.exception.message)

    def test_the_argued_identity_must_agree_with_the_PINNED_object(self):
        """THE DOMAIN MUST NOT MOVE mid-lifecycle.

        If the live object were allowed to differ from the pinned one, a start would
        reserve under one domain and its ending would compute another and find no
        generation to return. So a disagreement refuses instead of quietly naming a
        different resource.
        """
        self.allocated("attempt-a")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.governed_workspace_identity(
                self.store, {"runtime_attempt_id": "attempt-a",
                             "workspace_device": 1, "workspace_inode": 2})
        self.assertIn("is not the resource this act would name",
                      caught.exception.message)

    def test_the_argued_identity_and_the_row_only_one_name_the_same_object(self):
        """The fallback is not a different answer, only a weaker one: it names the
        same object and makes no overlap argument."""
        import os

        argued = self.allocated("attempt-a")
        found = os.stat(os.path.join(self.storage, "attempt-a", "workspace"))
        self.assertEqual(
            argued,
            tokens.workspace_identity({"runtime_attempt_id": "attempt-a",
                                       "workspace_device": found.st_dev,
                                       "workspace_inode": found.st_ino}))


class TheSplitBetweenACQUISITIONandSETTLEMENT(unittest.TestCase):
    """W275774 review 18:38:39Z: PROVE THE SPLIT, and do not widen it.

    The review confirms the reasoning and adds the warning that matters: do NOT wire
    filesystem re-resolution into settlement to satisfy earlier wording. So these cases
    establish exactly what each half uses and why:

      * ACQUISITION uses the ARGUED identity, which proves containment and proves it
        equals the pinned object. That is the only moment overlap exclusion matters,
        because that is when a resource is or is not already held.
      * SETTLEMENT uses the PINNED identity, because by then the path may be absent or
        replaced -- and re-resolving would either refuse (skipping an attempt whose
        token is still held) or name a DIFFERENT resource.

    AND THE LIMIT THE REVIEW STATES: the pinned identity selects OWNERSHIP -- which
    generation this ending is about -- and it is not cessation evidence and not
    authority over a replacement's effects. Those remain the cessation's own to prove.
    """

    def setUp(self):
        import os
        import shutil
        import tempfile

        from baton_v12.worker_manager import workspaces
        from baton_v12.worker_manager.store import ControlStore
        from tests.manager import input_roots

        room = tempfile.TemporaryDirectory(prefix="v12-split-")
        self.addCleanup(room.cleanup)
        self.shutil = shutil
        self.os = os
        self.store = ControlStore.open(
            os.path.join(room.name, "control.sqlite3"), incarnation="split-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.storage = os.path.join(room.name, "storage")
        os.makedirs(self.storage, exist_ok=True)
        workspaces.configure_workspace_storage(self.store, self.storage)
        self.group = input_roots.configured_group(self.store)
        self.workspaces = workspaces

    def started(self, assignment_id="attempt-a"):
        """One ACQUISITION through the argued identity, over a real allocated root."""
        self.workspaces.assignment_workspace(self.group, self.storage, assignment_id)
        found = self.os.stat(
            self.os.path.join(self.storage, assignment_id, "workspace"))
        attempt = {"runtime_attempt_id": assignment_id,
                   "workspace_device": found.st_dev, "workspace_inode": found.st_ino}
        argued = tokens.workspace_governance(control=self.store)
        reservation = argued.reserve(self.store, attempt,
                                    operation=f"runtime.start:{assignment_id}")
        reservation.bind(f"runtime-{assignment_id}")()
        reservation.settle(f"runtime-{assignment_id}")
        return attempt, tokens.domain_of(
            "workspace", f"{found.st_dev}:{found.st_ino}")

    def test_an_ABSENT_path_still_settles_the_original_generation(self):
        attempt, domain = self.started()
        self.shutil.rmtree(self.os.path.join(self.storage, "attempt-a"))
        # THE ARGUED IDENTITY CANNOT ANSWER, which is exactly why settlement does not
        # use it: the resource is still held and re-resolving would refuse.
        with self.assertRaises(ContractRefusal):
            tokens.governed_workspace_identity(self.store, attempt)
        # THE PINNED FORM SELECTS THE ORIGINAL GENERATION and settles it.
        pinned = tokens.workspace_governance()
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        pinned.release(self.store, attempt,
                       operation="runtime.start:attempt-a",
                       cessation={"container": "runtime-attempt-a",
                                  "stopped": True, "helpers": []})
        self.assertEqual(tokens.outstanding(self.store, domain), [])

    def test_a_REPLACED_path_settles_the_original_and_not_the_new_object(self):
        """THE SHARP ONE. A new object at the same path is a DIFFERENT resource, and
        the ending is about the one its start reserved."""
        attempt, domain = self.started()
        self.shutil.rmtree(self.os.path.join(self.storage, "attempt-a"))
        self.workspaces.assignment_workspace(self.group, self.storage, "attempt-a")
        replaced = self.os.stat(
            self.os.path.join(self.storage, "attempt-a", "workspace"))
        fresh = tokens.domain_of("workspace",
                                 f"{replaced.st_dev}:{replaced.st_ino}")
        self.assertNotEqual(fresh, domain,
                            "a replaced object is a different resource")
        # The argued identity now names the NEW object, so it refuses against the
        # attempt's pinned row -- the disagreement this claim's check exists for.
        with self.assertRaises(ContractRefusal) as caught:
            tokens.governed_workspace_identity(self.store, attempt)
        self.assertIn("is not the resource this act would name",
                      caught.exception.message)
        # AND THE PINNED FORM SETTLES THE ORIGINAL, leaving the new object untouched.
        tokens.workspace_governance().release(
            self.store, attempt, operation="runtime.start:attempt-a",
            cessation={"container": "runtime-attempt-a", "stopped": True,
                       "helpers": []})
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        self.assertEqual(tokens.outstanding(self.store, fresh), [],
                         "the new object was never reserved by this ending")

    def test_a_later_attempt_over_the_replaced_object_is_ISOLATED(self):
        """A stale ending about a dead object must not reach a live later attempt."""
        attempt, domain = self.started()
        self.shutil.rmtree(self.os.path.join(self.storage, "attempt-a"))
        later, fresh = self.started("attempt-b")
        self.assertNotEqual(fresh, domain)
        self.assertEqual(len(tokens.outstanding(self.store, fresh)), 1)
        # THE STALE ENDING, about the original attempt's dead object.
        tokens.workspace_governance().release(
            self.store, attempt, operation="runtime.start:attempt-a",
            cessation={"container": "runtime-attempt-a", "stopped": True,
                       "helpers": []})
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        self.assertEqual(len(tokens.outstanding(self.store, fresh)), 1,
                         "the later attempt still holds its own resource")
        del later

    def test_the_pinned_identity_selects_OWNERSHIP_and_not_cessation(self):
        """The limit the review states, asserted: selecting the generation does not
        make its cessation proved. Evidence about another container still refuses."""
        attempt, domain = self.started()
        self.shutil.rmtree(self.os.path.join(self.storage, "attempt-a"))
        with self.assertRaises(ContractRefusal) as caught:
            tokens.workspace_governance().release(
                self.store, attempt, operation="runtime.start:attempt-a",
                cessation={"container": "somebody-elses-runtime", "stopped": True,
                           "helpers": []})
        self.assertEqual(caught.exception.code, "identity-mismatch")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)


class TheSplitOnREALATTEMPTROWS(RetainedAndCompleteAreDifferentEndings):
    """W275774 review 18:42:29Z: REAL ROWS THROUGH THE PRODUCTION SEAMS.

    My previous split cases built attempt DICTIONARIES and called `Governance` directly.
    The review is right that this proves the composition and not the connection, so these
    drive a real attempt row and a really-allocated workspace through the real
    `intake.authorize_cleanup`.

    CORRECTION, REVIEW 18:46:09Z, AND IT IS MINE: THE START HERE IS NOT
    `request_runtime_start`. `governed_start` below reserves, binds and settles the token
    DIRECTLY, and `allocated` calls `retained_ready` then `ended` before any token exists --
    so this class reads an already-ended fixture row and adds governance afterwards.
    Naming that method THE REAL START was wrong. What these cases do establish is the
    governance composition over a real row and a real allocation, and the split between what
    an argued identity answers and what a pinned one selects; what they do NOT establish is
    a governed execution. The later-execution case below is the same overreach: `later` is a
    copied dictionary, so its `execution` proves reservation identity and not a second
    execution.

    THE CONNECTED PROOF IS `test_connected_lifecycle.py`, where the token is acquired by
    `attempts.request_runtime_start` itself, the second execution is a second authorized
    attempt row, and both engine crossings are counted at the adapter.

    AND THE REPLACEMENT IS BY RENAME-PRESERVE, not delete-and-recreate: deleting frees
    the inode and the new object may reuse it, which would make "a different resource"
    an accident of allocation rather than a fact. Renaming the old object aside keeps it
    alive, so the new one provably has a different identity.
    """

    def allocated(self):
        """A real attempt row whose workspace is allocated through the canonical path."""
        import os

        from baton_v12.worker_manager import workspaces
        from tests.manager import input_roots

        self.retained_ready("discard-after-intake")
        self.ended()
        storage = workspaces.configured_workspace_storage(self.store).place
        workspaces.assignment_workspace(
            input_roots.configured_group(self.store), storage, ATTEMPT)
        root = os.path.join(storage, ATTEMPT, "workspace")
        found = os.stat(root)
        attempts.pin_boundary_identity(
            self.store, attempt_id=ATTEMPT, source=(66, 111),
            workspace=(found.st_dev, found.st_ino))
        return (storage, root,
                tokens.domain_of("workspace", f"{found.st_dev}:{found.st_ino}"))

    def governed_start(self):
        """THE REAL START, with the argued identity -- the production composition."""
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        governance = tokens.workspace_governance(control=self.store)
        operation = attempts._start_operation_id(attempt)
        reservation = governance.reserve(self.store, attempt, operation=operation)
        reservation.bind(attempt["runtime_id"])()
        reservation.settle(attempt["runtime_id"])
        return attempt

    def renamed_aside(self, root):
        """Replace the object while KEEPING the old one, so identities cannot collide."""
        import os

        from baton_v12.worker_manager import workspaces
        from tests.manager import input_roots

        os.rename(root, root + ".preserved")
        workspaces.assignment_workspace(
            input_roots.configured_group(self.store),
            workspaces.configured_workspace_storage(self.store).place, ATTEMPT)
        return os.stat(root)

    def test_a_real_ending_settles_the_original_token_after_an_ABSENT_path(self):
        import shutil

        storage, root, domain = self.allocated()
        self.governed_start()
        shutil.rmtree(root)
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        # THE REAL PRODUCTION ENDING, on the pinned form, over a path that is gone.
        answer = intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION,
            govern=tokens.workspace_governance())
        self.assertEqual(answer["state"], "absent")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "the ending settled the generation its start reserved")

    def test_a_real_ending_settles_the_ORIGINAL_after_a_rename_preserved_replacement(self):
        storage, root, domain = self.allocated()
        self.governed_start()
        replaced = self.renamed_aside(root)
        fresh = tokens.domain_of("workspace",
                                 f"{replaced.st_dev}:{replaced.st_ino}")
        self.assertNotEqual(fresh, domain,
                            "rename-preserve guarantees a distinct new object")
        answer = intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION,
            govern=tokens.workspace_governance())
        self.assertEqual(answer["state"], "absent")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "the ORIGINAL generation is the one settled")
        self.assertEqual(tokens.outstanding(self.store, fresh), [],
                         "and the replacement was never reserved by this ending")

    def test_a_real_LATER_EXECUTION_over_the_same_resource_holds_its_own(self):
        """THE SAME-RESOURCE later execution, which my previous case did not do.

        A second attempt row reserves the SAME workspace object after the first is
        returned, and the first attempt's ending run again does not touch it.
        """
        storage, root, domain = self.allocated()
        attempt = self.governed_start()
        intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION,
            govern=tokens.workspace_governance())
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        # GENERATION 2 over the SAME object, by a different execution.
        later = dict(attempt, runtime_attempt_id="attempt-later")
        second = tokens.workspace_governance().reserve(
            self.store, later, operation="runtime.start:attempt-later")
        self.assertEqual(second.token["generation"], 2)
        # THE FIRST ATTEMPT'S ENDING, RUN AGAIN: it replays and touches nothing else.
        intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION,
            govern=tokens.workspace_governance())
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [2],
                         "the later execution still holds the same resource")
        self.assertEqual(held[0]["execution"], "attempt-later")


class TheMOUNTEDRootIsProvedInEitherArrangement(unittest.TestCase):
    """W275774 review 22:07:51Z: THE LAYOUT REPAIRED WITHOUT DROPPING THE ARGUMENT.

    My first correction to the private-line mismatch passed pins-only governance at the
    tool's fresh start, which also dropped the ORDINARY start's overlap exclusion -- the
    review refused that, and it was right. `governed_resource_identity` now takes the root
    the caller is about to MOUNT and proves it sits in one of the two sibling arrangements
    this build supports; the pinned-equality check above it is unchanged.

    Both arrangements are read off their composers rather than guessed: the ordinary root
    is `<storage>/<assignment>/workspace`, and a private line's is
    `<storage>/.baton-review-lines/<line>/checkout`, which is what
    `review_cycles._line_place` builds. My first cut of the prover had the line root one
    level too shallow and every line start refused, which is how I learned it.
    """

    def setUp(self):
        import os
        import tempfile

        from baton_v12.worker_manager import ControlStore, workspaces

        self.root = tempfile.mkdtemp(prefix="v12-mounted-root-")
        self.addCleanup(self._remove, self.root)
        self.place = os.path.join(self.root, "storage")
        os.makedirs(self.place)
        self.store = ControlStore.open(os.path.join(self.root, "control.sqlite3"),
                                       incarnation="manager-1",
                                       clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        workspaces.configure_workspace_storage(self.store, self.place)

    @staticmethod
    def _remove(place):
        import shutil
        shutil.rmtree(place, ignore_errors=True)

    def identity(self, assignment_id, mounted):
        from baton_v12.worker_manager import workspaces
        return workspaces.governed_resource_identity(
            self.store, assignment_id, mounted=mounted)

    def made(self, *parts):
        import os
        place = os.path.join(self.place, *parts)
        os.makedirs(place, exist_ok=True)
        return place

    @staticmethod
    def object_of(place):
        import os
        found = os.stat(place)
        return f"{found.st_dev}:{found.st_ino}"

    def test_the_ORDINARY_root_answers_its_own_object(self):
        root = self.made("attempt-a", "workspace")
        self.assertEqual(self.identity("attempt-a", root), self.object_of(root))

    def test_a_LINE_CHECKOUT_answers_its_own_object(self):
        from baton_v12.worker_manager import workspaces

        root = self.made(workspaces._REVIEW_LINE_HOME, "line-1", "checkout")
        self.assertEqual(self.identity("attempt-a", root), self.object_of(root))

    def test_a_NESTED_root_is_REFUSED(self):
        """The overlap the argument exists for: a root inside another attempt's tree."""
        self.made("attempt-a", "workspace")
        nested = self.made("attempt-a", "workspace", "inner")
        with self.assertRaises(ContractRefusal) as caught:
            self.identity("attempt-b", nested)
        self.assertIn("overlap cannot be excluded", caught.exception.message)

    def test_a_root_OUTSIDE_BOTH_NAMESPACES_is_REFUSED(self):
        import os

        outside = os.path.join(self.root, "elsewhere")
        os.makedirs(outside)
        with self.assertRaises(ContractRefusal):
            self.identity("attempt-a", outside)

    def test_ANOTHER_ATTEMPTS_workspace_is_refused_for_this_attempt(self):
        """The ordinary root must be THIS attempt's own, which is what makes the
        arrangement a sibling one rather than a free-for-all."""
        beside = self.made("attempt-b", "workspace")
        with self.assertRaises(ContractRefusal):
            self.identity("attempt-a", beside)

    def test_TWO_ATTEMPTS_OVER_ONE_OBJECT_SHARE_A_DOMAIN(self):
        """And the exclusion still follows from the identity: one object, one domain, so
        the second acquisition is refused rather than counted separately."""
        root = self.made("attempt-a", "workspace")
        first = self.identity("attempt-a", root)
        governance = tokens.workspace_governance()
        governance.reserve(self.store,
                           {"runtime_attempt_id": "attempt-a",
                            "workspace_device": int(first.split(":")[0]),
                            "workspace_inode": int(first.split(":")[1])},
                           operation="runtime.start:a")
        with self.assertRaises(ContractRefusal) as caught:
            governance.reserve(self.store,
                               {"runtime_attempt_id": "attempt-b",
                                "workspace_device": int(first.split(":")[0]),
                                "workspace_inode": int(first.split(":")[1])},
                               operation="runtime.start:b")
        self.assertIn("is owned by token generation 1", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
