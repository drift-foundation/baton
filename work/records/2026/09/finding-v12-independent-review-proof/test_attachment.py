"""The attachment arrangement, driven through the real manager boundary.

WHAT THIS IS FOR. `attachment.py` describes when W239533's reviewer may attach
to W239528's retained checkpoint. A preflight that merely restates a
validator's rules drifts away from them silently, and a drifted preflight is
worse than none: it reports "attachable" for something the manager will refuse,
or refuses something the manager would have taken. So every case here asks BOTH
accounts about the same store and requires them to agree -- the real
`review_cycles.attach_review` against a real `ControlStore`, and
`attachment.refusals` against the subject read out of that same store through
`ControlStore.open_readonly` and one coherent `snapshot()`.

WHY IT BUILDS ON THE PRODUCT'S OWN FIXTURE. `tests.manager.test_review_cycles`
already composes a real control store, a real configured workspace storage and
real writers and checkpoints through the supported API. Reusing it is what the
owner reroute asks for in as many words -- "Reuse accepted components" -- and
it means these cases exercise the same line lifecycle the product's own suite
does rather than a private imitation of it. The stub `Profile` is the product's
own test profile and is labelled as such: it stands in for Git object
materialization, and nothing here claims otherwise.

WHAT IS NOT PROVED HERE. No provider, container, image, network or credential
is involved, and no verdict is produced. These cases establish the ATTACHMENT
boundary -- which checkpoint a separate Job may review and who may review it --
and nothing about what a real reviewer would then say.
"""

import os
import pathlib
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      accept_offer, activate_assignment,
                                      attach_review, certify_profile,
                                      create_line, freeze_checkpoint,
                                      issue_offer, line_of, record_attempt,
                                      submit_claim)
from baton_v12.worker_manager.source_boundary import nominate_source
from tests.manager import input_roots
from tests.manager.test_offers import (PROFILE, ROUTE, SCOPE, FakeSession,
                                       decision, fake_claim_signature)
from tests.manager.test_review_cycles import (AUTHORITY, BASE, NOW, WORK,
                                              ReviewCycles)

# The digests an admitted attempt carries. They are this case's own operands,
# not the product's: what matters is that the SAME ones ride the offer, the
# acceptance and the attempt record, which is what `attempt.record`'s signature
# is about.
POLICY = "sha256:" + "d" * 64
ADAPTER = "sha256:" + "c" * 64

import attachment


# The reviewer identity the composed W239533 packet uses. Distinct from the
# producer's on all three axes, which is the only thing that makes it a review.
REVIEWER = {"reviewer_worker_id": "review-worker",
            "reviewer_participant": "baton.review",
            "reviewer_principal": "principal:baton.review"}


class AttachmentCase(unittest.TestCase):
    """A produced, frozen, review-ready line -- the state W239528 left.

    IT BORROWS `ReviewCycles`'s FIXTURE WITHOUT INHERITING ITS CASES. Naming
    `ReviewCycles` as a base class ran its 130-odd product cases under this
    dossier's name and counted them as this Job's verification, which would
    have been this Job claiming credit for the product suite. The four helpers
    below are taken by reference instead: the same real `ControlStore`, the
    same configured workspace storage, the same stub `Profile`, and none of
    the cases.

    The producer here is deliberately given the SAME worker, participant and
    principal names the accepted run recorded, so the independence cases below
    are asking about the real pair rather than about two invented strings.
    """

    PRODUCER_WORKER = "implementation-worker"
    PRODUCER_PARTICIPANT = "baton.impl"
    PRODUCER_PRINCIPAL = "principal:baton.impl"

    # `ReviewCycles.setUp` calls no `super().setUp()`, so these are ordinary
    # functions with no cooperative-inheritance obligation to honour.
    prepare_store = ReviewCycles.setUp
    tearDown = ReviewCycles.tearDown
    attempt = ReviewCycles.attempt
    line = ReviewCycles.line
    port = ReviewCycles.port
    complete = ReviewCycles.complete
    review = ReviewCycles.review
    verdict = ReviewCycles.verdict

    def setUp(self):
        self.prepare_store()
        self.line_row = self.line()
        self.line_id = self.line_row["line_id"]
        self.checkpoint = self.produced(1)

    def produced(self, generation):
        """One whole implementation round: writer, work, frozen checkpoint."""
        attempt = self.attempt(f"writer-attempt-{generation}", generation,
                               self.PRODUCER_PARTICIPANT,
                               self.PRODUCER_PRINCIPAL)
        from baton_v12.worker_manager import grant_writer
        current = line_of(self.store, self.line_id)["current_checkpoint_id"]
        writer = grant_writer(
            self.store, line_id=self.line_id, attempt_id=attempt,
            generation=generation, worker_id=self.PRODUCER_WORKER,
            profile=self.profile, based_checkpoint_id=current)
        self.complete(attempt)
        return freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=generation,
            profile=self.profile, port=self.port(self.PRODUCER_PARTICIPANT))

    def admitted_attempt(self, attempt_id, work_id, *, participant,
                         principal, generation):
        """An attempt admitted the SUPPORTED way: offer, accept, record,
        claim, activate.

        Review 2026-09-23T04:50:12Z P2. The first version of the foreign-line
        case created the attempt with this fixture's own Work and then changed
        its identity with `UPDATE attempts SET work_id = ?` before granting a
        writer. That did not establish the foreign-checkpoint lifecycle it
        claimed to; it asserted it. This runs the actual authority half --
        `issue_offer`, `accept_offer`, `record_attempt`, `submit_claim`,
        `activate_assignment` -- against a session bound to the OTHER Work, so
        the attempt's assignment names that Work because the lifecycle put it
        there.

        The session, port and claim signature are the product test suite's own
        (`tests.manager.test_offers`), which is the supported admission fixture
        the review asked for.
        """
        held = {"authority_uuid": AUTHORITY, "work_id": work_id}
        live = {"work_ref": dict(held), "participant": participant,
                "generation": generation}
        session = FakeSession(participant=participant, work={
            "status": "open", "phase": "queued", "handler": None,
            "gate": None, "authority_uuid": AUTHORITY, "scope": SCOPE,
            "route": ROUTE})
        # THE DECISION IS ABOUT THIS PARTICIPANT. `decision()` defaults to
        # the product fixture's own endpoint, and `submit_claim` refuses when
        # it fences somebody else -- "a decision about somebody else does not
        # authorize this claim". That refusal is the lifecycle working, and
        # naming the participant is how the supported path is followed rather
        # than worked around.
        session.claim_answer = {"assignment": dict(live), "claim_event": 1,
                                "decision": decision(participant=participant,
                                                     principal=principal)}
        session.live_assignment = dict(live)
        port = AuthorityPort(session, fake_claim_signature)
        # AN OFFER PROMISES AN EXECUTION SHAPE, and this manager has agreed to
        # none -- "nothing certifies profile 'reference' for this manager".
        # Certifying it is part of the supported admission, not a way around
        # a refusal: the product's own offer fixture does exactly this.
        certify_profile(self.store, "runtime", "reference", PROFILE)
        given, _richer = input_roots.documents(
            work_ref=dict(held), participant=participant,
            generation=generation, runtime_attempt_id=attempt_id,
            policy_digest=POLICY, profile_digest=PROFILE)
        offer = "offer-" + attempt_id
        issue_offer(self.store, port, offer_id=offer, work_id=work_id,
                    runtime_attempt_id=attempt_id,
                    input_digest=given["manifest_digest"],
                    policy_digest=POLICY, profile_digest=PROFILE,
                    profile_name="reference", mint_bearer=lambda: "bearer-1")
        accept_offer(self.store, port, offer_id=offer, decision="accept",
                     bearer="bearer-1", now=NOW,
                     runtime_attempt_id=attempt_id, work_ref=dict(held))
        record_attempt(self.store, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       input_digest=given["manifest_digest"],
                       policy_digest=POLICY)
        submit_claim(self.store, port, offer_id=offer)
        # THE FOUR-PART FENCE, AND ONLY IT. `input_roots.documents` answers a
        # richer assignment document; `activate_assignment` requires exactly
        # work_ref, participant and generation -- "the expected assignment
        # needs work_ref, participant, generation" -- so the fence is what is
        # handed over.
        activate_assignment(self.store, port, attempt_id=attempt_id,
                            expect=dict(live))
        return attempt_id

    def reviewer_attempt(self, generation=7, *,
                         participant=None, principal=None):
        return self.attempt(f"review-attempt-{generation}", generation,
                            REVIEWER["reviewer_participant"] if participant
                            is None else participant,
                            REVIEWER["reviewer_principal"] if principal
                            is None else principal)

    def held_subject(self, checkpoint_id=None):
        """The subject, read through the SUPPORTED read-only opener.

        A fresh handle per read, closed here, because a read-only opener that
        was left open would be this case holding a connection on a store the
        writing fixture also holds.
        """
        reader = attachment.reading(self.control_path, clock=lambda: NOW)
        try:
            return attachment.subject(
                reader, line_id=self.line_id, authority_uuid=AUTHORITY,
                work_id=WORK, checkpoint_id=checkpoint_id)
        finally:
            reader.close()

    def both_accounts(self, *, checkpoint_id=None, generation=7,
                      worker_id=None, participant=None, principal=None,
                      authority_uuid=AUTHORITY, work_id=WORK):
        """Ask the preflight and the real validator about the same attachment.

        Returns `(refusals, raised)` -- this module's list, and the
        `ContractRefusal` the manager raised, or `None` when it accepted.
        """
        checkpoint_id = (self.checkpoint["checkpoint_id"]
                         if checkpoint_id is None else checkpoint_id)
        worker_id = (REVIEWER["reviewer_worker_id"] if worker_id is None
                     else worker_id)
        participant = (REVIEWER["reviewer_participant"] if participant is None
                       else participant)
        principal = (REVIEWER["reviewer_principal"] if principal is None
                     else principal)
        found = attachment.refusals(
            self.held_subject(checkpoint_id), checkpoint_id=checkpoint_id,
            reviewer_worker_id=worker_id, reviewer_participant=participant,
            reviewer_principal=principal, profile_name=self.profile.name)
        attempt = self.reviewer_attempt(generation, participant=participant,
                                        principal=principal)
        raised = None
        try:
            attach_review(self.store, checkpoint_id=checkpoint_id,
                          attempt_id=attempt, generation=generation,
                          reviewer_worker_id=worker_id, profile=self.profile)
        except ContractRefusal as failure:
            raised = failure
        return found, raised

    def assert_agree_refused(self, found, raised, *, marker):
        self.assertTrue(found, "the preflight found nothing to refuse while "
                               f"the manager raised {raised!r}")
        self.assertIsNotNone(
            raised, f"the preflight refused {found!r} and the real "
                    f"attach_review accepted; a preflight that is stricter "
                    f"than the validator is a drifted preflight")
        self.assertTrue(any(one.startswith(marker) for one in found),
                        f"no refusal begins with {marker!r}: {found!r}")


class TheAcceptedProposalIsAttachableByAnIndependentReviewer(AttachmentCase):
    def test_the_preflight_and_the_manager_both_accept(self):
        found, raised = self.both_accounts()
        self.assertEqual(found, [])
        self.assertIsNone(raised)
        self.assertEqual(line_of(self.store, self.line_id)["state"],
                         "reviewing")

    def test_the_subject_names_the_producer_and_the_exact_bytes(self):
        held = self.held_subject()
        self.assertEqual(held["producer"]["worker_id"], self.PRODUCER_WORKER)
        self.assertEqual(held["producer"]["participant"],
                         self.PRODUCER_PARTICIPANT)
        self.assertEqual(held["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        self.assertEqual(held["checkpoint_state"], "frozen")
        self.assertEqual(held["line_state"], "review-ready")
        self.assertEqual(held["declared_base"], BASE)
        self.assertEqual(held["authority_uuid"], AUTHORITY)
        self.assertEqual(held["work_id"], WORK)


class ASecondJobRecoversTheSameLineRatherThanCreatingOne(AttachmentCase):
    """The whole arrangement, in the one call that decides it.

    `StageDeployment.line_for` calls `create_line` on EVERY tick of EVERY
    deployment, with the deployment's own Authority and the binding's Work. A
    second Job -- the reviewer's -- therefore reaches this same function, and
    what it gets back is what decides whether a separate Job can review a
    retained proposal at all.
    """

    def test_the_same_authority_and_work_answer_the_producers_line(self):
        again = create_line(self.store, source=nominate_source(self.source),
                            declared_base=BASE, profile=self.profile,
                            authority_uuid=AUTHORITY, work_id=WORK)
        self.assertEqual(again["line_id"], self.line_id)
        # AND IT REPLAYED RATHER THAN MATERIALIZING AGAIN. One materialize call
        # for the producer's creation and none for the recovery: the reviewer
        # Job does not rebuild the tree it is about to read.
        self.assertEqual(self.profile.materialize_calls, 1)

    def test_a_different_v12_work_reaches_a_different_line(self):
        other = create_line(self.store, source=nominate_source(self.source),
                            declared_base=BASE, profile=self.profile,
                            authority_uuid=AUTHORITY, work_id=WORK + "-other")
        self.assertNotEqual(other["line_id"], self.line_id)
        self.assertIsNone(
            line_of(self.store, other["line_id"])["current_checkpoint_id"],
            "a line created under another Work holds no producer checkpoint, "
            "which is exactly why the reviewer Job must name the producer's "
            "own v12 Work rather than a fresh one")

    def test_the_named_line_is_proved_against_the_named_work(self):
        """No public reader finds a line from an Authority and Work, so the
        packet NAMES the line and this is the proof that it is the right one.

        `GAPS[0]` records that missing lookup rather than routing around it.
        """
        reader = attachment.reading(self.control_path, clock=lambda: NOW)
        try:
            with self.assertRaises(attachment.AttachmentRefusal) as caught:
                attachment.subject(reader, line_id=self.line_id,
                                   authority_uuid=AUTHORITY,
                                   work_id=WORK + "-other")
            said = str(caught.exception)
            self.assertIn(WORK, said)
            self.assertIn("the same line", said)
        finally:
            reader.close()


class AWrongCheckpointIsRefusedByBothAccounts(AttachmentCase):
    def test_a_checkpoint_this_line_never_held(self):
        found, raised = self.both_accounts(checkpoint_id="checkpoint-" + "f" * 8)
        self.assertTrue(found)
        self.assertIsNotNone(raised)
        self.assertTrue(any(one.startswith("WRONG:") for one in found), found)

    def test_a_checkpoint_belonging_to_another_line(self):
        """A REAL frozen checkpoint on a line the reviewer's Work does not
        name, produced through the ordinary lifecycle from an attempt this
        case ADMITTED rather than relabelled."""
        from baton_v12.worker_manager import grant_writer

        other_work = AUTHORITY[:8] + "-W99999"
        foreign_line = create_line(
            self.store, source=nominate_source(self.source),
            declared_base=BASE, profile=self.profile,
            authority_uuid=AUTHORITY, work_id=other_work)
        attempt = self.admitted_attempt(
            "foreign-writer-attempt", other_work,
            participant="baton.other-impl",
            principal="principal:baton.other-impl", generation=3)
        writer = grant_writer(self.store, line_id=foreign_line["line_id"],
                              attempt_id=attempt, generation=3,
                              worker_id="foreign-worker", profile=self.profile)
        self.complete(attempt)
        foreign = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=3,
            profile=self.profile, port=self.port("baton.other-impl"))
        self.assertNotEqual(foreign["checkpoint_id"],
                            self.checkpoint["checkpoint_id"])
        found, raised = self.both_accounts(
            checkpoint_id=foreign["checkpoint_id"])
        self.assert_agree_refused(found, raised, marker="WRONG:")
        self.assertIn(foreign_line["line_id"], found[0])


class AStaleCheckpointIsRefusedByBothAccounts(AttachmentCase):
    """A superseded checkpoint of the RIGHT line -- the dangerous case.

    It is the right Authority, the right Work, the right line and a real frozen
    checkpoint the producer actually made. Only the revision is behind, and a
    reviewer that took it would judge bytes the producer has already replaced.
    """

    def setUp(self):
        super().setUp()
        self.stale = self.checkpoint
        # THE ORDINARY WAY A CHECKPOINT BECOMES STALE, and there is no other:
        # a review attaches, returns `changes-requested`, and the line admits
        # a correction writer whose freeze becomes the new current checkpoint.
        # Granting a second writer on a `review-ready` line is refused -- "line
        # state 'review-ready' does not admit a writer" -- so a stale
        # checkpoint cannot be manufactured, only produced.
        attached = self.review(self.stale["checkpoint_id"], 1)
        self.verdict(attached, 1, "changes-requested")
        self.checkpoint = self.produced(2)

    def test_the_superseded_revision_is_named_as_stale(self):
        self.assertNotEqual(self.stale["checkpoint_id"],
                            self.checkpoint["checkpoint_id"])
        found, raised = self.both_accounts(
            checkpoint_id=self.stale["checkpoint_id"])
        self.assert_agree_refused(found, raised, marker="STALE:")

    def test_the_current_revision_is_still_attachable(self):
        found, raised = self.both_accounts()
        self.assertEqual(found, [])
        self.assertIsNone(raised)


class AProducerCannotReviewItself(AttachmentCase):
    def test_all_three_identities_shared(self):
        found, raised = self.both_accounts(
            worker_id=self.PRODUCER_WORKER,
            participant=self.PRODUCER_PARTICIPANT,
            principal=self.PRODUCER_PRINCIPAL)
        self.assert_agree_refused(found, raised, marker="NOT INDEPENDENT AT:")
        self.assertIn("worker, participant, principal", found[0])

    def test_one_shared_identity_is_enough_to_refuse(self):
        for axis, operands in (
                ("worker", {"worker_id": self.PRODUCER_WORKER}),
                ("participant", {"participant": self.PRODUCER_PARTICIPANT}),
                ("principal", {"principal": self.PRODUCER_PRINCIPAL})):
            with self.subTest(axis=axis):
                self.setUp()
                found, raised = self.both_accounts(**operands)
                self.assert_agree_refused(found, raised,
                                          marker="NOT INDEPENDENT AT:")
                self.assertIn(axis, found[0])


class AReviewCannotAttachWhileTheLineIsBeingCorrected(AttachmentCase):
    """What is actually reachable, and the distinction is worth stating.

    `attach_review` carries a branch for "read-only review cannot coexist with
    a writer". Trying to reach it from the state W239528 left showed that it is
    DEFENSIVE rather than ordinary: a `review-ready` line refuses a writer at
    all -- "line state 'review-ready' does not admit a writer" -- so the only
    way to have an active writer is to have already left review-ready, and by
    then the earlier `review-ready`/current-checkpoint precondition is what
    refuses first.

    So this case proves the reachable thing, and says which refusal actually
    fires. `attachment.refusals` reports both the line state and the active
    writer, and the first entry is the one the manager raised -- which is what
    "the validator's order" in that function's docstring means.
    """

    def test_a_correction_round_closes_the_line_to_review(self):
        attached = self.review(self.checkpoint["checkpoint_id"], 1)
        self.verdict(attached, 1, "changes-requested")
        from baton_v12.worker_manager import grant_writer
        attempt = self.attempt("writer-attempt-2", 2,
                               self.PRODUCER_PARTICIPANT,
                               self.PRODUCER_PRINCIPAL)
        grant_writer(self.store, line_id=self.line_id, attempt_id=attempt,
                     generation=2, worker_id=self.PRODUCER_WORKER,
                     profile=self.profile,
                     based_checkpoint_id=self.checkpoint["checkpoint_id"])
        held = self.held_subject()
        self.assertEqual(held["line_state"], "writing")
        found, raised = self.both_accounts(generation=8)
        self.assert_agree_refused(found, raised, marker="LINE STATE:")
        # AND THE REFUSAL SAYS WHAT `writing` MEANS. There is no separate
        # "active writer" entry any more: no public reader lists a line's
        # writers (`GAPS[2]`), and the raw scan that produced one was the
        # bypass review 2026-09-23T04:40:30Z refused. The line state is the
        # signal the validator itself acts on, and it is the reachable one.
        self.assertIn("under correction", found[0])


class TheSurveyReadsThroughTheSupportedOpener(AttachmentCase):
    """AGENTS.md's rule, kept -- and what it cost to keep it.

    THE FIRST VERSION OF THIS MODULE OPENED THE STORE WITH `sqlite3.connect`
    AND WROTE ITS OWN `SELECT`s. Review 2026-09-23T04:40:30Z refused that as a
    P1 and it was right: "Never read it directly either: if a question about
    the coordination state can only be answered by opening the store, that
    inability is the finding." The premise I built it on -- that
    `ControlStore.open` might migrate -- was true but incomplete, because
    `open_readonly` already existed and refuses an empty or unrecognized store
    without initializing it.

    These cases hold the replacement to what it claims: the supported opener,
    one coherent snapshot, public readers only, and no write.
    """

    def test_it_opens_through_control_store_open_readonly(self):
        reader = attachment.reading(self.control_path, clock=lambda: NOW)
        try:
            self.assertIsInstance(reader, ControlStore)
            self.assertTrue(getattr(reader, "_readonly", False),
                            "the survey holds a WRITING handle on the "
                            "producer's retained store")
        finally:
            reader.close()

    def test_the_line_checkpoint_and_writer_are_one_coherent_read(self):
        """One `snapshot()` spans all three, so they cannot be three moments.

        Measured rather than asserted: the survey is asked for its snapshot
        depth while it is inside the boundary, and the three records it
        answers are read there.
        """
        reader = attachment.reading(self.control_path, clock=lambda: NOW)
        depths = []
        try:
            held = reader.snapshot
            import contextlib

            @contextlib.contextmanager
            def watched():
                with held():
                    depths.append(reader._snapshots)
                    yield reader

            reader.snapshot = watched
            found = attachment.survey(reader, line_id=self.line_id)
        finally:
            reader.close()
        self.assertEqual(depths, [1], "the survey took no snapshot, or took "
                                      "more than one")
        self.assertEqual(found["line"]["line_id"], self.line_id)
        self.assertEqual(found["checkpoint"]["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        self.assertEqual(found["producer"]["worker_id"], self.PRODUCER_WORKER)

    def test_the_stores_own_bytes_and_rows_do_not_change(self):
        import hashlib

        def digest_of(path):
            with open(path, "rb") as handle:
                return hashlib.sha256(handle.read()).hexdigest()

        def counted():
            return (line_of(self.store, self.line_id)["state"],
                    line_of(self.store, self.line_id)["current_checkpoint_id"])

        before, state = digest_of(self.control_path), counted()
        held = self.held_subject()
        self.assertEqual(held["line_id"], self.line_id)
        self.assertEqual(digest_of(self.control_path), before)
        self.assertEqual(counted(), state)

    def test_a_supported_mutator_refuses_on_the_readonly_handle(self):
        """The boundary the module promises, measured through a real act.

        Review 2026-09-23T04:50:12Z: the first version of this ran `DELETE
        FROM review_lines` on the handle's private connection. That proves
        SQLite refuses a write; it does not prove the SUPPORTED interface
        cannot change the store through this handle, which is what the module
        claims. `create_line` is one of the product's own mutators, and the
        operands name a Work this store holds NO line for, so it has to INSERT
        one.

        THE FIRST DRAFT OF THIS CASE PASSED THE EXISTING WORK AND NOTHING WAS
        RAISED -- correctly: that call is a pure replay, and a replay writes
        nothing. Measuring a read-only boundary with an operand that needs no
        write measures nothing at all, and the draft is recorded here rather
        than quietly replaced.
        """
        fresh = AUTHORITY[:8] + "-W31337"
        reader = attachment.reading(self.control_path, clock=lambda: NOW)
        try:
            with self.assertRaises(Exception) as caught:
                create_line(reader, source=nominate_source(self.source),
                            declared_base=BASE, profile=self.profile,
                            authority_uuid=AUTHORITY, work_id=fresh)
            self.assertIn("readonly", str(caught.exception).lower())
        finally:
            reader.close()
        # AND THE STORE IS AS IT WAS.
        self.assertEqual(line_of(self.store, self.line_id)["state"],
                         "review-ready")

    def test_an_absent_store_is_an_operational_finding(self):
        with self.assertRaises(attachment.AttachmentRefusal) as caught:
            attachment.reading(
                os.path.join(self.temporary.name, "absent.sqlite3"),
                clock=lambda: NOW)
        said = str(caught.exception)
        self.assertIn("operational finding", said)
        self.assertIn("not a reason to open it another way", said)

    def test_the_documented_clock_is_one_the_opener_accepts(self):
        """The operator page's own step 1, run.

        It printed `clock=lambda: "now"`, and `open_readonly` calls the clock
        through the public instant grammar, which rejects that string -- so
        the documented survey could not run as printed. Review
        2026-09-23T11:30:47Z R1. This runs the corrected block's clock against
        the real opener on a disposable store.
        """
        reader = attachment.reading(self.control_path, clock=attachment.now)
        try:
            self.assertEqual(
                attachment.subject(reader, line_id=self.line_id,
                                   authority_uuid=AUTHORITY,
                                   work_id=WORK)["line_id"], self.line_id)
        finally:
            reader.close()

    def test_the_operator_page_names_that_clock_rather_than_a_string(self):
        said = pathlib.Path(HERE, "OPERATOR-239533.md").read_text(
            encoding="utf-8")
        self.assertIn("clock=attachment.now", said)
        self.assertNotIn('clock=lambda: "now"', said)

    def test_a_store_that_is_not_a_manager_is_refused_not_initialized(self):
        """`open_readonly`'s own promise, exercised: an empty file is refused
        rather than migrated into a manager."""
        import os.path

        place = os.path.join(self.temporary.name, "empty.sqlite3")
        with open(place, "wb") as handle:
            handle.write(b"")
        with self.assertRaises(attachment.AttachmentRefusal):
            attachment.reading(place, clock=lambda: NOW)
        self.assertEqual(os.path.getsize(place), 0,
                         "the refused store was written to")

    def test_the_missing_public_lookups_are_recorded_rather_than_bypassed(self):
        said = "\n".join(attachment.GAPS)
        self.assertIn("No public function answers", said)
        self.assertIn("SUPPORTED ALTERNATIVE", said)
        # AND THE BYPASS IS GONE, not merely documented. Asked of the parsed
        # module rather than of its text, because the docstring NAMES what was
        # removed and a substring search would be satisfied by the confession.
        import ast

        tree = ast.parse(
            pathlib.Path(attachment.__file__).read_text(encoding="utf-8"))
        imported = set()
        executes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(one.name for one in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(
                    node.func, ast.Attribute) and node.func.attr in (
                        "execute", "executemany", "executescript"):
                executes.append(ast.dump(node.func))
        self.assertNotIn("sqlite3", imported,
                         "the survey imports sqlite3 again")
        self.assertEqual(executes, [],
                         "the survey issues its own statements again")


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only this module's own cases.

    `ReviewCycles` is imported as a base class, and an unrestricted loader
    would re-run the product suite's own cases under this dossier's name and
    count them as this Job's verification.
    """
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if isinstance(value, type) and issubclass(value, unittest.TestCase) \
                and value.__module__ == __name__ and name != "AttachmentCase":
            suite.addTests(loader.loadTestsFromTestCase(value))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
