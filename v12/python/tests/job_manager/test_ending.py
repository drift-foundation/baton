"""W119733 — the composed ending's obligation, and the retry that finishes it.

`work/records/2026/09/finding-v12-composed-ending-recovery/`.

THE DEFECT THESE CASES PIN. `authorize_cleanup` is the last act of the ENDING
and the second-to-last act of a COMPOSED ending: the quiescence gate discharge
and the routing of the result come after it. The projection decided whether to
ask again from that cleanup axis alone, so a manager that died between the
cleanup and the acts after it came back to a stage projected `completed`, a
Work blocked at a gate nobody was going to discharge, and no tick that would
ever ask again.

WHAT IS ASSERTED, AND WHAT DELIBERATELY IS NOT. These cases own the Job
manager's half: the closed durable records, the reads that refuse a record
this build did not write, the projection that keeps an unsettled obligation
owed, and the ordinary sweep that asks again -- including for an episode a
correction round has already replaced. The actual composed lifecycle, the
gate discharge and the historical driver resume are W119114's and
`test_review_driver`'s; a fake deployment here proves scheduling, never that
an ending finished.
"""

import contextlib
import inspect
import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import status, submit, sweep
from baton_v12.job_manager import ending
from baton_v12.job_manager.episodes import end_episode, open_next
from baton_v12.job_manager.store import job_signature

if __package__:
    from .fixtures import (LATER, NOW, SOON, UUID, WHO, WORK_A, WORK_B,
                           FakeOperations, JobManagerCase, job, stage,
                           submission)
else:
    from fixtures import (LATER, NOW, SOON, UUID, WHO, WORK_A, WORK_B,
                          FakeOperations, JobManagerCase, job, stage,
                          submission)

STAGE = "job-a/implementation"
REVIEW = "job-a/review"
TERMINAL = "sha256:" + "d" * 64
RETENTION_POLICY = "sha256:" + "e" * 64


def assignment(work_id=WORK_A, generation=1, participant=WHO,
               authority_uuid=UUID):
    return {"work_ref": {"authority_uuid": authority_uuid,
                         "work_id": work_id},
            "participant": participant, "generation": generation}


def evidence(**members):
    held = {"result_id": "result-1", "manifest_digest": "sha256:" + "c" * 64,
            "receipt_digest": "sha256:" + "f" * 64}
    held.update(members)
    return held


class EndingCase(JobManagerCase):
    """One Job whose review stage gates on its implementation.

    ONE JOB AND NOT THE DEFAULT TWO, because half of what these cases measure
    is a gate staying closed -- and a second Job's ordinary progress in the
    same report is exactly the noise that would make a closed gate hard to
    read.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a", stages=[
            stage("implementation", WORK_A),
            stage("review", WORK_B,
                  depends_on=[{"job_id": "job-a",
                               "kind": "implementation"}])])]))
        self.acts = FakeOperations()

    def register(self, stage_id=STAGE, **changed):
        operands = {"assignment": assignment(),
                    "disposition": "completed",
                    "terminal_manifest_digest": TERMINAL,
                    "retention_disposition": "retain",
                    "retention_policy_digest": RETENTION_POLICY}
        operands.update(changed)
        return ending.register_ending(self.jobs, self.attempting(
            self.jobs, stage_id), **operands)

    def settle(self, stage_id=STAGE, **changed):
        operands = {"assignment": assignment(), "evidence": evidence()}
        operands.update(changed)
        return ending.settle_ending(self.jobs, self.attempting(
            self.jobs, stage_id), **operands)

    def cleaned_up(self, stage_id=STAGE):
        """The exact durable state a finished composed ending leaves behind.

        `cleanup: retained` is terminal, the runtime is gone, and this control
        plane holds no exchange read -- which is what the read-only surface
        sees and what a restarted serving manager sees before it looks at
        anything else.
        """
        self.acts.frozen(stage_id, "completed",
                         execution_runtime="destroyed", cleanup="retained")

    def projected(self, stage_id=None):
        held = {one["stage_id"]: one for job_status in
                status(self.jobs, self.acts, observed_at=SOON)["jobs"]
                for one in job_status["stages"]}
        return held if stage_id is None else held[stage_id]

    def concluded(self):
        return [one for one in self.acts.calls if one[0] == "conclude"]

    def journalled(self, kind, document, stage_id=STAGE, episode=1):
        """Commit a document at a selected identity, through the public API.

        The reviewer's own technique, kept because it is the honest one: this
        is not a hand edit of the store, it is the journal being used exactly
        as this module uses it.
        """
        return self.jobs.transact(
            f"{kind}:{stage_id}:{episode}", kind,
            job_signature(kind, document), lambda connection: document)

    def intent_record(self, **changed):
        live = self.attempting(self.jobs)
        held = dict({member: live[member] for member in ending.SELECTORS},
                    assignment=assignment(), disposition="completed",
                    terminal_manifest_digest=TERMINAL,
                    retention_disposition="retain",
                    retention_policy_digest=RETENTION_POLICY)
        held.update(changed)
        return held

    def settlement_record(self, obligation, proof=None, **changed):
        held = dict({member: obligation[member]
                     for member in ending.SELECTORS},
                    assignment=obligation["assignment"],
                    intent=ending.intent_operation_id(STAGE, 1),
                    evidence=evidence() if proof is None else proof)
        held.update(changed)
        return held

    def assert_refuses_every_decision(self):
        """No reader, no discovery and no projection may answer past this."""
        with self.assertRaises(ContractRefusal) as raised:
            ending.ending_of(self.jobs, STAGE, 1)
        with self.assertRaises(ContractRefusal):
            ending.pending_endings(self.jobs)
        with self.assertRaises(ContractRefusal):
            self.projected()
        return raised.exception


    def spoken(self, report):
        return [(one["stage_id"], one["episode"], one["act"], one["outcome"])
                for one in report["spoken"]]


# -- the two records ---------------------------------------------------------


@contextlib.contextmanager
def fresh_store():
    """One disposable Job store per shape, set up and torn down.

    A SAVEPOINT will not do here: `JobStore.transact` opens its own
    `BEGIN IMMEDIATE`, so the damaged-and-rolled-back idiom the other suites
    use cannot wrap a journalled write. A fresh case is the honest
    alternative and costs a temporary directory.
    """
    case = EndingCase("run")
    case.setUp()
    try:
        yield case
    finally:
        case.doCleanups()


class TheObligationIsOneClosedCorrelatedRecord(EndingCase):
    """What is written, and that nothing outside the contract gets written.

    An obligation whose selectors are not enough to rebuild the ending is an
    obligation nobody can act on, and one that accepts extra members is a
    place for a deployment to smuggle a fact nobody owns.
    """

    def test_a_registered_ending_carries_exactly_its_contract(self):
        registered = self.register()
        self.assertEqual(tuple(registered), ending.INTENT_MEMBERS)
        self.assertEqual(registered["stage_id"], STAGE)
        self.assertEqual(registered["job_id"], "job-a")
        self.assertEqual(registered["kind"], "implementation")
        self.assertEqual(registered["episode"], 1)
        self.assertEqual(registered["work_id"], WORK_A)
        self.assertEqual(registered["assignment"], assignment())
        self.assertEqual(registered["terminal_manifest_digest"], TERMINAL)
        live = self.attempting(self.jobs)
        self.assertEqual(registered["offer_id"], live["offer_id"])
        self.assertEqual(registered["attempt_id"], live["attempt_id"])

    def test_the_selectors_rebuild_the_same_attempt_without_a_cache(self):
        """W119733's whole reason for persisting them.

        A resumed ending is driven from the record and nothing else, so the
        record has to produce the same view a live tick would have passed.
        """
        registered = self.register()
        self.assertEqual(ending.attempt_of(self.jobs, registered),
                         self.attempting(self.jobs))

    def test_registering_twice_replays_the_first_record(self):
        first = self.register()
        self.assertEqual(self.register(), first)
        self.assertEqual(len(ending.pending_endings(self.jobs)), 1)

    def test_a_changed_operand_collides_rather_than_rewriting(self):
        self.register()
        for changed in ({"disposition": "unable"},
                        {"terminal_manifest_digest": "sha256:" + "9" * 64},
                        {"retention_disposition": "discard-after-intake"},
                        {"retention_policy_digest": "sha256:" + "9" * 64},
                        {"assignment": assignment(generation=2)}):
            with self.subTest(changed=changed):
                with self.assertRaises(ContractRefusal) as raised:
                    self.register(**changed)
                self.assertEqual(raised.exception.code, "operation-collision")
        self.assertEqual(ending.intent_of(self.jobs, STAGE, 1)["disposition"],
                         "completed")

    def test_a_settlement_names_its_intent_and_the_acts_that_finished_it(self):
        self.register()
        settled = self.settle(evidence=evidence(
            checkpoint_id="checkpoint-1", gate_discharge="gate:1",
            outcome="accepted"))
        self.assertEqual(tuple(settled), ending.SETTLEMENT_MEMBERS)
        self.assertEqual(settled["intent"],
                         ending.intent_operation_id(STAGE, 1))
        self.assertEqual(settled["evidence"]["checkpoint_id"], "checkpoint-1")
        self.assertEqual(settled["evidence"]["gate_discharge"], "gate:1")
        self.assertEqual(ending.settlement_of(self.jobs, STAGE, 1), settled)
        self.assertEqual(ending.pending_endings(self.jobs), [])

    def test_an_ordinary_pass_may_settle_with_no_gate_discharge_at_all(self):
        """A no-gate pass is not a reason to fabricate a quiescence
        obligation.

        The discharge member is optional because whether a gate was owed is
        the Authority's fact; a settlement that required one would make this
        store assert something it cannot see.
        """
        self.register()
        settled = self.settle()
        self.assertNotIn("gate_discharge", settled["evidence"])
        self.assertEqual(ending.pending_endings(self.jobs), [])

    def test_settled_evidence_is_closed_in_both_directions(self):
        self.register()
        for held in ({"result_id": "result-1",
                      "manifest_digest": "sha256:" + "c" * 64},
                     evidence(invented="anything"),
                     "not-a-document", None):
            with self.subTest(evidence=held):
                with self.assertRaises(ContractRefusal):
                    self.settle(evidence=held)
        self.assertIsNone(ending.settlement_of(self.jobs, STAGE, 1))


class ARecordIsProvedAgainstTheRowsThisStoreHolds(EndingCase):
    """A journalled document is not its own authority.

    Every selector names a row, so every selector is compared back against
    one. Acting on a record whose episode names another attempt would drive
    an ending for work this stage never did.
    """

    def test_an_unknown_stage_or_episode_refuses(self):
        live = self.attempting(self.jobs)
        for changed, code in ((("stage_id", "job-a/nowhere"), "precondition"),
                              (("episode", 4), "precondition"),
                              (("job_id", "job-z"), "operation-collision"),
                              (("kind", "review"), "operation-collision"),
                              (("work_id", WORK_B), "operation-collision"),
                              (("offer_id", "offer-elsewhere"),
                               "operation-collision"),
                              (("attempt_id", "attempt-elsewhere"),
                               "operation-collision")):
            member, value = changed
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as raised:
                    ending.register_ending(
                        self.jobs, dict(live, **{member: value}),
                        assignment=assignment(), disposition="completed",
                        terminal_manifest_digest=TERMINAL,
                        retention_disposition="retain",
                        retention_policy_digest=RETENTION_POLICY)
                self.assertEqual(raised.exception.code, code)

    def test_an_assignment_for_another_work_refuses(self):
        with self.assertRaises(ContractRefusal) as raised:
            self.register(assignment=assignment(work_id=WORK_B))
        self.assertEqual(raised.exception.code, "operation-collision")

    def test_a_malformed_assignment_refuses_before_anything_is_written(self):
        for held in ({"participant": WHO, "generation": 1},
                     dict(assignment(), extra="anything"),
                     dict(assignment(), generation="one"),
                     dict(assignment(), work_ref={"work_id": WORK_A}),
                     dict(assignment(),
                          work_ref={"authority_uuid": "not-a-uuid",
                                    "work_id": WORK_A}),
                     None):
            with self.subTest(assignment=held):
                with self.assertRaises(ContractRefusal):
                    self.register(assignment=held)
        self.assertIsNone(ending.intent_of(self.jobs, STAGE, 1))

    def test_a_settlement_without_an_intent_refuses(self):
        with self.assertRaises(ContractRefusal) as raised:
            self.settle()
        self.assertEqual(raised.exception.category, "refused")
        self.assertIsNone(ending.settlement_of(self.jobs, STAGE, 1))

    def test_an_old_obligation_cannot_settle_a_newer_generation(self):
        self.register()
        with self.assertRaises(ContractRefusal) as raised:
            self.settle(assignment=assignment(generation=2))
        self.assertEqual(raised.exception.category, "stale-assignment")
        self.assertIsNone(ending.settlement_of(self.jobs, STAGE, 1))
        # AND THE OBLIGATION IS STILL OWED. A refused settlement that had
        # closed the retry would be worse than no settlement at all.
        self.assertEqual([one["stage_id"] for one in
                          ending.pending_endings(self.jobs)], [STAGE])


class ASignatureIsNotOwnership(EndingCase):
    """W120424, from `review-2026-09-08T15-46-16Z.md` [P1].

    THE DEFECT, AND IT WAS NOT CORRUPTION. Every record the reviewer's probe
    used was a genuine, correctly signed, committed act of this build. What it
    did was file one at ANOTHER stage's selected identity through the public
    journal -- and the reader proved the member set, the kind, the committed
    state and the self-signature, all of which a legitimate record for a
    different stage also satisfies. Pending discovery then found nothing, the
    implementation projected `completed`, and its dependent opened.

    So these cases ask the question the reader was not asking: whose record is
    this? Each one asserts the refusal AND that the two decisions it used to
    corrupt -- discovery and the dependent gate -- refuse with it rather than
    quietly answering.
    """

    def test_another_stages_settlement_at_this_identity_refuses(self):
        """The reproduction, and it is the whole reason this Work exists."""
        self.register()
        self.cleaned_up()
        self.register(REVIEW, assignment=assignment(work_id=WORK_B))
        foreign = self.settle(REVIEW, assignment=assignment(work_id=WORK_B))
        held = self.jobs.operation_record(
            ending.settlement_operation_id(REVIEW, 1))
        self.jobs.transact(ending.settlement_operation_id(STAGE, 1),
                           ending.SETTLED_KIND, held["signature"],
                           lambda connection: foreign)
        caught = self.assert_refuses_every_decision()
        self.assertEqual(caught.code, "operation-collision")
        # AND THE REVIEW STAGE'S OWN RECORD IS STILL ITS OWN. The copy did not
        # damage it, so a reader asking the right question still gets the
        # right answer.
        self.assertEqual(ending.settlement_of(self.jobs, REVIEW, 1), foreign)

    def test_a_record_filed_under_another_episodes_identity_refuses(self):
        registered = self.register()
        self.journalled(ending.INTENT_KIND, registered, STAGE, 2)
        with self.assertRaises(ContractRefusal) as raised:
            ending.intent_of(self.jobs, STAGE, 2)
        self.assertIn("derive", raised.exception.message)
        self.assertEqual(raised.exception.code, "operation-collision")

    def test_a_settlement_with_no_obligation_at_its_identity_refuses(self):
        """An orphan is not a settlement.

        It says "the obligation over there finished", so a settlement whose
        obligation this store never registered is not evidence that anything
        finished -- and reading one as though it were is how an ending that
        never happened stopped being owed.
        """
        live = self.attempting(self.jobs)
        orphan = dict({member: live[member] for member in ending.SELECTORS},
                      assignment=assignment(),
                      intent=ending.intent_operation_id(STAGE, 1),
                      evidence=evidence())
        self.journalled(ending.SETTLED_KIND, orphan)
        caught = self.assert_refuses_every_decision()
        self.assertEqual(caught.category, "refused")
        self.assertIn("never registered", caught.message)

    def test_a_settlement_naming_another_obligation_refuses(self):
        registered = self.register()
        crossed = dict({member: registered[member]
                        for member in ending.SELECTORS},
                       assignment=assignment(),
                       intent=ending.intent_operation_id(REVIEW, 1),
                       evidence=evidence())
        self.journalled(ending.SETTLED_KIND, crossed)
        caught = self.assert_refuses_every_decision()
        self.assertEqual(caught.code, "operation-collision")
        self.assertIn("settles", caught.message)

    def test_a_settlement_disagreeing_with_its_own_obligation_refuses(self):
        registered = self.register()
        crossed = dict({member: registered[member]
                        for member in ending.SELECTORS},
                       assignment=assignment(generation=2),
                       intent=ending.intent_operation_id(STAGE, 1),
                       evidence=evidence())
        self.journalled(ending.SETTLED_KIND, crossed)
        caught = self.assert_refuses_every_decision()
        self.assertIn("assignment", caught.message)

    def test_a_recorded_foreign_authority_refuses_on_every_read(self):
        """W83781's collision, one layer up.

        `authority_uuid` and `work_id` are a pair and this store is bound to
        one Authority, so a record naming another one is not this store's --
        however well it names this stage's Work.
        """
        live = self.attempting(self.jobs)
        foreign = dict({member: live[member] for member in ending.SELECTORS},
                       assignment=assignment(authority_uuid="9" * 32),
                       disposition="completed",
                       terminal_manifest_digest=TERMINAL,
                       retention_disposition="retain",
                       retention_policy_digest=RETENTION_POLICY)
        self.journalled(ending.INTENT_KIND, foreign)
        caught = self.assert_refuses_every_decision()
        self.assertEqual(caught.code, "operation-collision")
        self.assertIn("Authority", caught.message)


class WhatAWriteWillNotAcceptEither(EndingCase):
    """The two accepted write operands the review found, not injected damage.

    Both were reached through the ordinary public calls with ordinary
    arguments, which is what makes them worse than a corrupted row: nothing
    had to go wrong for either to be recorded.
    """

    def test_an_assignment_for_another_authority_is_refused(self):
        with self.assertRaises(ContractRefusal) as raised:
            self.register(assignment=assignment(authority_uuid="9" * 32))
        self.assertEqual(raised.exception.code, "operation-collision")
        self.assertIn("Authority", raised.exception.message)
        self.assertIsNone(ending.intent_of(self.jobs, STAGE, 1))

    def test_a_settlement_naming_no_owner_record_is_refused(self):
        """A member that may be null is a member that is not required.

        The point of these three is that an operator reading this store can
        find the acts that finished the ending; a settlement carrying none of
        them closed the obligation and opened the dependent stage.
        """
        self.register()
        self.cleaned_up()
        for member in ("result_id", "manifest_digest", "receipt_digest"):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal):
                    self.settle(evidence=evidence(**{member: None}))
        self.assertIsNone(ending.settlement_of(self.jobs, STAGE, 1))
        # AND THE OBLIGATION IS STILL OWED, which is what the refusal is for.
        self.assertEqual(self.projected(STAGE)["state"], "answering")
        self.assertEqual(self.projected(REVIEW)["state"], "blocked")
        self.assertEqual([one["stage_id"] for one in
                          ending.pending_endings(self.jobs)], [STAGE])

    def test_an_optional_reference_is_omitted_rather_than_emptied(self):
        self.register()
        with self.assertRaises(ContractRefusal):
            self.settle(evidence=evidence(gate_discharge=None))
        settled = self.settle(evidence=evidence(gate_discharge="gate:1"))
        self.assertEqual(settled["evidence"]["gate_discharge"], "gate:1")


class TheWholePayloadIsOwnedOnTheWayOutToo(EndingCase):
    """W120424 review 2026-09-08T16-00-28Z [P1].

    THE CONTRACT WAS ENFORCED IN ONE DIRECTION. The reader owned the member
    set, the signature, the selectors and the assignment and then reached past
    everything else -- so a correctly signed record standing at its own
    identity carried a null terminal digest, a list where a disposition
    belongs, an evidence list, an unknown evidence member or three null
    references, read back clean, emptied pending discovery, projected the
    implementation `completed` and opened its dependent. Validating on the way
    in did not discharge it: the process that wrote a durable value is not the
    process that reads it.
    """

    def test_stored_evidence_is_owned_when_it_is_read_back(self):
        """The three shapes an ordinary write now refuses, stored anyway."""
        for name, proof in (
                ("null references", evidence(result_id=None,
                                             manifest_digest=None,
                                             receipt_digest=None)),
                ("not a document", []),
                ("an unknown member", evidence(unowned=True)),
                ("a missing member", {"result_id": "result-1",
                                      "manifest_digest": "sha256:" + "c" * 64}),
                ("a wrong-type member", evidence(receipt_digest=7))):
            with self.subTest(evidence=name), fresh_store() as case:
                registered = case.register()
                case.cleaned_up()
                case.journalled(ending.SETTLED_KIND,
                                case.settlement_record(registered, proof))
                case.assert_refuses_every_decision()

    def test_a_stored_intent_payload_is_owned_when_it_is_read_back(self):
        held = self.intent_record(disposition=[],
                                  terminal_manifest_digest=None,
                                  retention_disposition={},
                                  retention_policy_digest=False)
        self.journalled(ending.INTENT_KIND, held)
        self.journalled(ending.SETTLED_KIND, self.settlement_record(held))
        self.cleaned_up()
        caught = self.assert_refuses_every_decision()
        self.assertEqual(caught.category, "integrity")

    def test_each_intent_payload_member_is_owned_on_its_own(self):
        for member, value in (("disposition", None), ("disposition", []),
                              ("terminal_manifest_digest", None),
                              ("terminal_manifest_digest", 7),
                              ("retention_disposition", {}),
                              ("retention_policy_digest", False)):
            with self.subTest(member=member, value=value), \
                    fresh_store() as case:
                case.journalled(ending.INTENT_KIND,
                                case.intent_record(**{member: value}))
                with self.assertRaises(ContractRefusal):
                    ending.intent_of(case.jobs, STAGE, 1)

    def test_a_stored_obligation_identity_is_owned_too(self):
        registered = self.register()
        self.journalled(ending.SETTLED_KIND,
                        self.settlement_record(registered, intent=None))
        self.assert_refuses_every_decision()

    def test_an_honest_record_still_reads_back_unchanged(self):
        """The positive half, and it is what stops this from being a wall.

        Every control above stores something this build would not write. What
        a resumed manager actually has to do is read back what it DID write,
        and the whole point of one shared validator is that the ordinary
        record survives it.
        """
        registered = self.register()
        self.cleaned_up()
        self.assertEqual(ending.intent_of(self.jobs, STAGE, 1), registered)
        self.assertEqual(self.projected(STAGE)["state"], "answering")
        self.assertEqual([one["stage_id"] for one in
                          ending.pending_endings(self.jobs)], [STAGE])
        settled = self.settle(evidence=evidence(checkpoint_id="checkpoint-1",
                                                gate_discharge="gate:1"))
        self.assertEqual(ending.ending_of(self.jobs, STAGE, 1),
                         {"intent": registered, "settlement": settled})
        self.assertEqual(self.projected(STAGE)["state"], "completed")
        self.assertEqual(self.projected(REVIEW)["state"], "queued")
        self.assertEqual(ending.pending_endings(self.jobs), [])


class NoCallerDocumentStandsInForAStoredRecord(EndingCase):
    """W120424 review 2026-09-08T16-00-28Z [P2].

    THE OPTIONAL OPERANDS ARE GONE, AND THAT IS THE CORRECTION. `intent=` let
    a fabricated obligation answer a settlement whose obligation this store
    does not hold; `stage=` let a fabricated stage row answer an intent whose
    Work this store's stage does not carry. Both were offered as reuse of
    something a caller had already read, and a public reader cannot tell that
    apart from something a caller made up -- matching members are not
    ownership. The claimed single moment was not real either: two ordinary
    reads on one connection are two reads.
    """

    def public_reader(self, name):
        return inspect.signature(getattr(ending, name)).parameters

    def test_the_public_readers_take_no_document_from_their_caller(self):
        for name, expected in (("intent_of", ("store", "stage_id", "episode")),
                               ("settlement_of",
                                ("store", "stage_id", "episode")),
                               ("ending_of", ("store", "stage_id", "episode")),
                               ("attempt_of", ("store", "intent"))):
            with self.subTest(reader=name):
                self.assertEqual(tuple(self.public_reader(name)), expected)

    def test_an_orphan_settlement_refuses_however_it_is_asked_for(self):
        live = self.attempting(self.jobs)
        orphan = dict({member: live[member] for member in ending.SELECTORS},
                      assignment=assignment(),
                      intent=ending.intent_operation_id(STAGE, 1),
                      evidence=evidence())
        self.jobs.transact(ending.settlement_operation_id(STAGE, 1),
                           ending.SETTLED_KIND,
                           job_signature(ending.SETTLED_KIND, orphan),
                           lambda connection: orphan)
        self.assertIsNone(ending.intent_of(self.jobs, STAGE, 1))
        with self.assertRaises(ContractRefusal) as raised:
            ending.settlement_of(self.jobs, STAGE, 1)
        self.assertIn("never registered", raised.exception.message)
        with self.assertRaises(ContractRefusal):
            ending.ending_of(self.jobs, STAGE, 1)

    def test_a_stored_record_naming_another_work_refuses(self):
        live = self.attempting(self.jobs)
        foreign = dict({member: live[member] for member in ending.SELECTORS},
                       work_id=WORK_B, assignment=assignment(work_id=WORK_B),
                       disposition="completed",
                       terminal_manifest_digest=TERMINAL,
                       retention_disposition="retain",
                       retention_policy_digest=RETENTION_POLICY)
        self.jobs.transact(ending.intent_operation_id(STAGE, 1),
                           ending.INTENT_KIND,
                           job_signature(ending.INTENT_KIND, foreign),
                           lambda connection: foreign)
        with self.assertRaises(ContractRefusal) as raised:
            ending.intent_of(self.jobs, STAGE, 1)
        self.assertEqual(raised.exception.code, "operation-collision")

    def test_the_many_stage_pass_answers_what_the_single_reads_answer(self):
        """`pending_endings` reads the stage rows once; it proves the same.

        The one read it reuses is its own, built inside the call from this
        store's rows -- so the batch and the single reader have to agree, and
        this is where that is measured rather than asserted.
        """
        self.register()
        self.cleaned_up()
        self.register(REVIEW, assignment=assignment(work_id=WORK_B))
        pending = {one["stage_id"] for one in ending.pending_endings(self.jobs)}
        self.assertEqual(pending, {STAGE, REVIEW})
        for stage_id in (STAGE, REVIEW):
            held = ending.ending_of(self.jobs, stage_id, 1)
            self.assertIsNotNone(held["intent"])
            self.assertIsNone(held["settlement"])
        self.settle()
        self.assertEqual([one["stage_id"] for one in
                          ending.pending_endings(self.jobs)], [REVIEW])


class APresentInvalidRecordIsNotAbsence(EndingCase):
    """`intake.gate_discharge_of`'s rule, applied to this store's records.

    A reader that answered `None` for a record it could not own would resume
    an ending it cannot describe, or report one finished that never was. Only
    a genuinely missing row answers absence.
    """

    def damage(self, statement, *values):
        self.jobs._connection.execute(statement, values)

    def test_absence_is_the_ordinary_answer(self):
        self.assertIsNone(ending.intent_of(self.jobs, STAGE, 1))
        self.assertIsNone(ending.settlement_of(self.jobs, STAGE, 1))
        self.assertIsNone(ending.ending_of(self.jobs, STAGE, 1))
        self.assertEqual(ending.pending_endings(self.jobs), [])

    def test_a_result_its_own_signature_does_not_name_refuses(self):
        registered = self.register()
        self.damage("UPDATE operations SET result = ? WHERE operation_id = ?",
                    json.dumps(dict(registered, disposition="unable"),
                               sort_keys=True),
                    ending.intent_operation_id(STAGE, 1))
        with self.assertRaises(ContractRefusal) as raised:
            ending.intent_of(self.jobs, STAGE, 1)
        self.assertEqual(raised.exception.code, "operation-collision")

    def test_a_record_under_a_foreign_kind_refuses(self):
        registered = self.register()
        self.damage("UPDATE operations SET kind = ?, signature = ? "
                    "WHERE operation_id = ?", "foreign.intent",
                    job_signature("foreign.intent", registered),
                    ending.intent_operation_id(STAGE, 1))
        with self.assertRaises(ContractRefusal) as raised:
            ending.intent_of(self.jobs, STAGE, 1)
        self.assertEqual(raised.exception.code, "operation-collision")

    def test_a_record_missing_a_selector_refuses(self):
        registered = self.register()
        short = {member: registered[member] for member in registered
                 if member != "offer_id"}
        self.damage("UPDATE operations SET result = ?, signature = ? "
                    "WHERE operation_id = ?",
                    json.dumps(short, sort_keys=True),
                    job_signature(ending.INTENT_KIND, short),
                    ending.intent_operation_id(STAGE, 1))
        with self.assertRaises(ContractRefusal):
            ending.intent_of(self.jobs, STAGE, 1)

    def test_a_record_whose_selectors_no_longer_bind_refuses(self):
        registered = self.register()
        self.damage("UPDATE episodes SET attempt_id = ? WHERE stage_id = ? "
                    "AND episode = 1", "attempt-somebody-elses", STAGE)
        with self.assertRaises(ContractRefusal) as raised:
            ending.attempt_of(self.jobs, registered)
        self.assertEqual(raised.exception.code, "operation-collision")


# -- what the projection does with it ----------------------------------------


class ARegisteredEndingStaysOwedAfterTerminalCleanup(EndingCase):
    """The defect, stated as the property that now holds.

    Terminal cleanup and `exchange: null` together are exactly what a crashed
    composed ending looks like, and they are what every reader saw as a
    finished stage.
    """

    def test_an_unsettled_ending_is_answering_and_owes_its_conclude(self):
        self.register()
        self.cleaned_up()
        held = self.projected(STAGE)
        self.assertEqual(held["state"], "answering")
        self.assertIsNone(held["exchange"])
        self.assertEqual(held["runtime"]["execution_runtime"], "destroyed")

    def test_the_dependent_stage_stays_blocked_until_it_settles(self):
        self.register()
        self.cleaned_up()
        self.assertEqual(self.projected(REVIEW)["state"], "blocked")
        self.assertEqual(self.projected(REVIEW)["gates"],
                         [{"stage_id": STAGE, "state": "answering",
                           "open": False}])
        self.register()
        self.settle()
        self.assertEqual(self.projected(STAGE)["state"], "completed")
        self.assertEqual(self.projected(REVIEW)["state"], "queued")

    def test_an_unregistered_stage_keeps_its_generic_cleanup_semantics(self):
        """The rule this Work did NOT change.

        A deployment that composes no obligation still gets exactly the
        projection it had, which is what keeps every existing ending -- and
        every case that asserts one -- meaning what it meant.
        """
        self.cleaned_up()
        self.assertEqual(self.projected(STAGE)["state"], "completed")
        self.assertEqual(self.projected(REVIEW)["state"], "queued")

    def test_a_settlement_does_not_answer_for_an_unfinished_cleanup(self):
        """A settled record is not a licence to stop reading the axis.

        The generic rules still decide a settled obligation, so a settlement
        written while the cleanup axis is `pending` cannot make an unfinished
        ending look done.
        """
        self.register()
        self.settle()
        self.acts.frozen(STAGE, "completed", execution_runtime="quiescent",
                         cleanup="pending")
        self.assertEqual(self.projected(STAGE)["state"], "answering")

    def test_the_read_only_status_resumes_nothing(self):
        """W119733's read-only rule, measured rather than asserted in prose.

        Status reads the Job journal and the canonical observations it is
        given, and it performs no serving act -- so an operator asking what is
        running never drives an ending.
        """
        self.register()
        self.cleaned_up()
        before = list(self.acts.calls)
        self.assertEqual(self.projected(STAGE)["state"], "answering")
        self.assertEqual(self.acts.calls, before)
        self.assertEqual(self.concluded(), [])
        self.assertEqual([one["stage_id"] for one in
                          ending.pending_endings(self.jobs)], [STAGE])


# -- what the ordinary sweep does with it ------------------------------------


class TheOrdinaryTickAsksAgainUntilItSettles(EndingCase):

    def setUp(self):
        super().setUp()
        self.acts.endings[STAGE] = {"disposition": "completed"}

    def test_a_pending_ending_is_concluded_once_a_tick(self):
        self.register()
        self.cleaned_up()
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(self.spoken(report),
                         [(STAGE, 1, "conclude", "performed")])
        self.assertEqual(self.concluded(), [("conclude", STAGE)])

    def test_a_settled_ending_is_never_concluded_again(self):
        self.register()
        self.cleaned_up()
        sweep(self.jobs, self.acts, now=SOON)
        self.settle()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([one for one in self.spoken(report)
                          if one[0] == STAGE], [])
        self.assertEqual(len(self.concluded()), 1)

    def test_a_refused_ending_leaves_the_next_tick_asking_again(self):
        self.acts.endings[STAGE] = ContractRefusal(
            "refused", "precondition", "the gate discharge is not reachable")
        self.register()
        self.cleaned_up()
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(self.spoken(report),
                         [(STAGE, 1, "conclude", "deferred")])
        self.assertEqual(report["spoken"][0]["detail"]["code"],
                         "precondition")
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.concluded()), 2)
        self.assertEqual([one["stage_id"] for one in
                          ending.pending_endings(self.jobs)], [STAGE])


class ACorrectionRoundDoesNotStrandTheEndingItReplaced(EndingCase):
    """The crash window a live-episode projection cannot see at all.

    `advance_correction` ends the episode that owed the ending and opens its
    successor in one act. Everything the projection derives is about the live
    episode, so an obligation left behind by the previous one is invisible
    there -- and this is the pass that finds it.
    """

    def setUp(self):
        super().setUp()
        self.acts.endings[STAGE] = {"disposition": "completed"}

    def corrected(self):
        """The old episode ended and its successor opened, as a round does."""
        from baton_v12.job_manager import live_of

        ended = end_episode(self.jobs, live_of(self.jobs, STAGE),
                            "superseded-by-correction", 1)
        return open_next(self.jobs, STAGE, ended)

    def test_a_prior_episodes_obligation_is_still_enumerated(self):
        registered = self.register()
        opened = self.corrected()
        self.assertEqual(opened["episode"], 2)
        self.assertEqual(ending.pending_endings(self.jobs), [registered])
        # AND THE NEW EPISODE OWES NOTHING OF ITS OWN.
        self.assertIsNone(ending.intent_of(self.jobs, STAGE, 2))

    def test_the_resumed_conclude_names_the_old_attempt_and_not_the_new(self):
        registered = self.register()
        self.corrected()
        report = sweep(self.jobs, self.acts, now=SOON)
        resumed = [one for one in report["spoken"]
                   if one["act"] == "conclude"]
        self.assertEqual(len(resumed), 1)
        self.assertEqual(resumed[0]["episode"], 1)
        self.assertEqual(resumed[0]["attempt_id"], registered["attempt_id"])
        self.assertEqual(resumed[0]["outcome"], "performed")
        self.assertNotEqual(registered["attempt_id"],
                            self.attempting(self.jobs)["attempt_id"])

    def test_settling_the_old_round_ends_the_asking(self):
        registered = self.register()
        self.corrected()
        sweep(self.jobs, self.acts, now=SOON)
        ending.settle_ending(self.jobs,
                             ending.attempt_of(self.jobs, registered),
                             assignment=assignment(), evidence=evidence())
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([one for one in report["spoken"]
                          if one["act"] == "conclude"], [])
        self.assertEqual(len(self.concluded()), 1)

    def test_one_tick_never_concludes_one_pending_ending_twice(self):
        """The live episode's ending is `_converse`'s and this pass skips it.

        Owner replay makes a second call harmless; a sweep report saying a
        tick concluded one stage twice is a report of something that did not
        happen.
        """
        self.register()
        self.cleaned_up()
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(self.spoken(report),
                         [(STAGE, 1, "conclude", "performed")])
        self.assertEqual(len(self.concluded()), 1)


if __name__ == "__main__":
    unittest.main()
