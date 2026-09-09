"""W6629 — manager intake, retention and cleanup.

`work/records/2026/08/finding-v12-manager-intake-retention-cleanup/`.

THE ACCEPTANCE, and every case below belongs to one of its lines:

  - effectively-once durable identities through W4's existing journal;
  - recoverable cancellation material, DISTINGUISHABLE from material retained
    by policy -- two different reasons for the same bytes still being there;
  - cleanup authorization, with `blocked-on-intake` used as the state it is;
  - `retained` and `complete` never conflated;
  - positive absence, and restart/retry ordering preserved;
  - the retention policy consumed by DIGEST and never interpreted.

THE FIXTURES ARE W6628'S, on purpose. Intake takes custody of a result that
module froze, so a suite that built its own frozen output would be proving
custody of a document the freeze receiver would never have produced.
"""

import contextlib
import copy
import inspect
import json
import os
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal, digest, held_secret
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager import (abandon_attempt,
                                      abandoned_gate_discharge_of,
                                      abandonment_cleanup_of,
                                      authorize_cleanup, cleanup_of,
                                      decide_retention,
                                      discharge_abandoned_quiescence_gate,
                                      discharge_quiescence_gate,
                                      gate_discharge_of,
                                      intake_operation, intake_receipt_of,
                                      manager_signature, observe,
                                      reconcile_runtime,
                                      record_intake, request_intake,
                                      request_runtime_start, retain_operation,
                                      retentions_of)
from baton_v12.worker_manager import documents
from baton_v12.worker_manager import load_manifest

from .test_offers import NOW, WHO
from .test_offers import FakeSession as _OfferSession

# W119548: the shared fake's own gate-discharge capability, held so one case
# can take it away and give it back. A deployment whose session is narrower is
# an ordinary fact this port is written for, and the case that proves the refusal
# must not leave the fake permanently narrower for every case after it.
_SATISFY_GATE = _OfferSession.satisfy_gate
from .test_attempts import Adapter as RuntimeAdapter
from .test_output import (ATTEMPT, AUTHORITY, JOB, Collector, OutputCase)
from . import input_roots

RETENTION = "sha256:" + "7" * 64
# The one deliberate secret, spelled the way `test_secrets` spells it: §13's
# rule is about a value this process is HOLDING, so the text itself is
# unremarkable and the registry is what makes it a bearer.
BEARER = "bearer-" + "9" * 40
OTHER_POLICY = "sha256:" + "9" * 64


class Custodian:
    """The adapter's collect and destroy, with every answer a case may set.

    Deliberately narrow, for the reason the freeze suite's collector is: what
    an adapter ASSERTS about its own success decides nothing here.
    """

    # W43975: THE TYPED DIRECTORY-CUSTODY SEAM every ending now settles on.
    custodian_image_digest = "sha256:" + "c" * 64

    def normalize_directory(self, store, *, assignment_id, which):
        from baton_v12.worker_manager import custody

        self.normalized.append((assignment_id, which))
        return custody._answered(
            "normalize", 0,
            {"custody": "normalize", "entries": 0, "not_ours": 0,
             "running_as": [0, 0]}, None)

    def __init__(self, answer=None, destroyed=None):
        self.normalized = []
        self.collected_with = []
        self.destroyed_with = []
        self.answer = answer
        self.failure = None
        self.destroyed = destroyed

    def collect(self, operands):
        self.collected_with.append(operands)
        if self.failure is not None:
            raise self.failure
        return self.answer

    def retain(self, operands):
        return True

    def destroy(self, command):
        # W6629 review [P1]: the manager delivers `runtimeDestroyBody` and its
        # operation now, not a bare identity. The fixture records the WHOLE
        # command, so a case asserting what crossed asserts what crossed.
        self.destroyed_with.append(command)
        runtime_id = command["runtime_id"]
        # W6636 re-review [P0]: EVERY PROVIDER ANSWERS ON EVERY DESTROY, and
        # an attempt with no such provider says `not-delivered` explicitly.
        #
        # THE DEFAULT ANSWER CARRIES BOTH; A NAMED ONE IS TAKEN VERBATIM. A
        # double that quietly completed whatever a case named would be a
        # double that hides contract violations -- and it did: filling the
        # members in made the reviewer's own omission reproduction stop
        # reproducing, because the omission never reached the manager. A case
        # about the providers names every ending it means.
        if self.destroyed is None:
            return {"runtime_id": runtime_id, "state": "absent",
                    "why": "the engine answered that this exact identity does "
                           "not exist",
                    "credentials": {"lifecycle_state": "not-delivered"},
                    "launch": {"lifecycle_state": "not-delivered"}}
        return {"runtime_id": runtime_id, **self.destroyed}


class IntakeCase(OutputCase):

    def attempt(self, *, quiescent=True, disposition="completed"):
        """W6628's attempt, with a RUNTIME ACTUALLY ATTACHED.

        The freeze suite observes quiescence directly and never starts
        anything, which is right for a suite about output: it has no runtime to
        destroy. Cleanup does, and an attempt whose axis says `quiescent` with
        no identity attached is a state the runtime slice does not produce -- so
        proving cleanup against one would be proving it against a fixture.
        """
        super().attempt(quiescent=False, disposition=None)
        runtime = RuntimeAdapter()
        # W19784 review [P0]: a runtime is not started over a directory this
        # manager has not held against its own assignment, so this suite needs
        # a REAL composed root -- built through `compose_input_root`, from the
        # very declaration this attempt was claimed against.
        # THE DOCUMENT THIS ATTEMPT WAS CLAIMED AGAINST, read back from the
        # store by its digest rather than taken from `self.declaration`. A
        # case that called `redeclared` moved `self.input_digest` and left the
        # attribute alone, so the fixture would have composed a root carrying
        # a manifest the attempt was not claimed against -- and every such
        # case would have been exercising that refusal by accident.
        inputs, _digest = input_roots.composed(
            self, input_roots.storage_under(self),
            given=load_manifest(self.store, self.input_digest,
                                "inputManifest"),
            work_ref={"authority_uuid": AUTHORITY, "work_id": JOB},
            participant=WHO, generation=1, runtime_attempt_id=ATTEMPT)
        request_runtime_start(self.store, runtime, attempt_id=ATTEMPT,
                              inputs=inputs)
        reconcile_runtime(self.store, runtime, attempt_id=ATTEMPT)
        if quiescent:
            observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                    value="quiescent")
        if disposition is not None:
            observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition",
                    value=disposition)
        return ATTEMPT

    def frozen_attempt(self, **overrides):
        """The whole W6628 happy path, ending at `frozen`."""
        self.frozen(**overrides)
        return ATTEMPT

    def collection(self, **overrides):
        """What the adapter reports it collected, ANSWERING the freeze."""
        frozen = self.frozen_output()
        body = {
            "result_id": frozen["result_id"],
            "artifacts": [{"artifact_id": one["artifact_id"],
                           "content_digest": one["content_digest"],
                           "bytes": one["bytes"],
                           "custody_locator":
                               f"file:///var/lib/baton/custody/"
                               f"{one['artifact_id']}"}
                          for one in frozen["artifacts"]],
        }
        body.update(overrides)
        return body

    def frozen_output(self):
        from baton_v12.worker_manager import frozen_output_of
        return frozen_output_of(self.store, ATTEMPT)

    def intaken(self, *, collection=None, **overrides):
        self.frozen_attempt(**overrides)
        adapter = Custodian(self.collection() if collection is None
                            else collection)
        return request_intake(self.store, self.port, adapter,
                              attempt_id=ATTEMPT), adapter

    def ended(self):
        """THE ASSIGNMENT IS OVER, which cleanup now requires.

        W6629 review [P1]: destroying the runtime of an assignment the
        authority still reports live tears out a worker that remains
        authorized to execute, so `authorize_cleanup` asks the authority and
        refuses while the fixed assignment is still the live one.

        Every case below that reaches a destroy therefore says so explicitly,
        immediately before authorizing rather than in its setup -- intake
        QUARANTINES material collected for a generation that has ended, so
        ending the assignment early would silently change what those cases are
        about.
        """
        self.session.live_assignment = None

    def attempt_axis(self, axis):
        return self.attempt_row()[axis]

    def retained_ready(self, disposition="discard-after-intake"):
        """Intaken, and every artifact decided under one policy."""
        receipt, _ = self.intaken()
        decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition=disposition, retention_policy_digest=RETENTION)
        return receipt


# -- taking custody -----------------------------------------------------------


class CustodyIsTakenOfWhatWasFrozen(IntakeCase):

    def test_the_output_axis_reaches_sealed(self):
        """W6628 ends at `frozen` and says so. Sealing is the record that this
        manager took custody, and it is intake that writes it."""
        self.frozen_attempt()
        self.assertEqual(self.attempt_axis("output"), "frozen",
                         "W6628's half of this is not where it was left")
        adapter = Custodian(self.collection())
        request_intake(self.store, self.port, adapter, attempt_id=ATTEMPT)
        self.assertEqual(self.attempt_axis("output"), "sealed")

    def test_the_receipt_names_what_arrived(self):
        receipt, adapter = self.intaken()
        self.assertEqual(receipt["custody"], "accepted")
        self.assertEqual([one["artifact_id"] for one in receipt["artifacts"]],
                         ["artifact-1"])
        self.assertEqual(receipt["artifacts"][0]["custody_locator"],
                         "file:///var/lib/baton/custody/artifact-1")
        self.assertEqual(len(adapter.collected_with), 1)

    def test_the_adapter_is_handed_the_whole_identity(self):
        """An adapter handed only a retry key cannot know which frozen result
        it is collecting, and a manager that asks for an echo it never supplied
        is asking the adapter to guess."""
        _, adapter = self.intaken()
        operands = adapter.collected_with[0]
        self.assertEqual(operands["attempt_id"], ATTEMPT)
        self.assertEqual(operands["assignment"]["participant"], WHO)
        self.assertEqual(operands["result_manifest_digest"],
                         self.frozen_output()["manifest_digest"])
        self.assertEqual(operands["output_names"], ["proposal"])

    def test_an_unfrozen_attempt_has_nothing_to_collect(self):
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            request_intake(self.store, self.port, Custodian({}),
                           attempt_id=ATTEMPT)
        self.assertIn("custody is taken of a FROZEN result",
                      caught.exception.message)

    def test_the_receipt_digest_is_recomputed_on_read_back(self):
        """The destroy command carries this digest, so what a caller receives
        is derived from the document it is reading rather than served from a
        column beside it."""
        receipt, _ = self.intaken()
        again = intake_receipt_of(self.store, ATTEMPT)
        self.assertEqual(again["receipt_digest"], receipt["receipt_digest"])
        body = {name: value for name, value in again.items()
                if name != "receipt_digest"}
        self.assertEqual(digest(body), again["receipt_digest"])

    def test_an_edited_row_cannot_authorize_a_destroy(self):
        self.intaken()
        self.store._connection.execute(
            "UPDATE intakes SET receipt_digest = ?", ("sha256:" + "0" * 64,))
        with self.assertRaises(ContractRefusal) as caught:
            intake_receipt_of(self.store, ATTEMPT)
        self.assertIn("recomputes to", caught.exception.message)

    def test_an_attempt_never_intaken_answers_absence(self):
        """Absence is an ANSWER here, and it is the one cleanup asks for."""
        self.frozen_attempt()
        self.assertIsNone(intake_receipt_of(self.store, ATTEMPT))


class NothingTheAdapterSaysIsAdopted(IntakeCase):

    def setUp(self):
        super().setUp()
        self.frozen_attempt()

    def refuses(self, collection, fragment):
        with self.assertRaises(ContractRefusal) as caught:
            request_intake(self.store, self.port, Custodian(collection),
                           attempt_id=ATTEMPT)
        self.assertIn(fragment, caught.exception.message)
        self.assertEqual(self.attempt_axis("output"), "frozen",
                         "a refused collection still sealed the output")
        return caught.exception

    def test_a_missing_artifact_is_not_an_empty_hand(self):
        """A collection that simply did not mention an artifact has not proved
        it is gone, and sealing on it would record custody of material this
        manager does not hold."""
        self.refuses(self.collection(artifacts=[]),
                     "custody is of the whole result")

    def test_an_artifact_nobody_froze_is_substitution(self):
        extra = self.collection()
        extra["artifacts"] = extra["artifacts"] + [
            {"artifact_id": "artifact-9", "content_digest": "sha256:" + "1" * 64,
             "bytes": 1, "custody_locator": "file:///tmp/x"}]
        self.refuses(extra, "which attempt")

    def test_changed_content_is_not_the_frozen_material(self):
        changed = self.collection()
        changed["artifacts"][0]["content_digest"] = "sha256:" + "3" * 64
        self.refuses(changed, "content digest")

    def test_a_changed_byte_count_refuses(self):
        changed = self.collection()
        changed["artifacts"][0]["bytes"] = 999
        self.refuses(changed, "byte count")

    def test_one_artifact_is_taken_into_custody_once(self):
        twice = self.collection()
        twice["artifacts"] = twice["artifacts"] * 2
        self.refuses(twice, "twice")

    def test_a_collection_for_another_result_refuses(self):
        self.refuses(self.collection(result_id="result-elsewhere"),
                     "and this attempt froze")


# -- custody, and why the bytes are still there -------------------------------


class TwoDifferentReasonsMaterialIsStillHere(IntakeCase):

    def test_material_from_an_ended_assignment_is_quarantined(self):
        """W6628 pinned this in the module that hands intake its work: its
        liveness read is inside the write and is still only a read, so the
        window cannot be zero, and material from an assignment that ended
        anyway is QUARANTINED AT INTAKE rather than trusted.

        Refusing would destroy the evidence of what a worker produced because
        its assignment ended while it was being collected.
        """
        self.frozen_attempt()
        self.session.live_assignment = None
        receipt, _ = self.intaken_now()
        self.assertEqual(receipt["custody"], "quarantined")
        self.assertIn("has ended", receipt["why"])
        self.assertEqual(self.attempt_axis("output"), "sealed",
                         "quarantined material was left uncollectable")

    def test_material_from_another_generation_is_quarantined(self):
        self.frozen_attempt()
        # W16823: the claim answers a closed result; the live assignment is
        # the FENCE out of it.
        self.session.live_assignment = {
            **dict(self.session.claim_answer["assignment"]), "generation": 2}
        receipt, _ = self.intaken_now()
        self.assertEqual(receipt["custody"], "quarantined")
        self.assertIn("generation 2", receipt["why"])

    def test_a_cancelled_attempt_is_recoverable_and_that_is_not_retention(self):
        """The acceptance requires these to stay distinguishable. They are two
        different reasons for the same bytes still being on disk: a cancelled
        attempt's material is kept so the work can be RECOVERED, and a retained
        artifact is kept because a policy said to keep it."""
        self.attempt(disposition="cancelled")
        from baton_v12.worker_manager import request_freeze
        request_freeze(self.store, self.port,
                       Collector(self.result(disposition="cancelled")),
                       attempt_id=ATTEMPT,
                       disposition="cancelled")
        receipt = request_intake(self.store, self.port,
                                 Custodian(self.collection()),
                                 attempt_id=ATTEMPT)
        self.assertIs(receipt["recoverable"], True)
        self.assertEqual(receipt["custody"], "accepted",
                         "a cancellation was reported as doubt about custody")
        self.assertEqual(retentions_of(self.store, ATTEMPT), (),
                         "recoverable material arrived with a policy decision "
                         "nobody made")

    def test_an_ordinary_result_is_not_recoverable_material(self):
        receipt, _ = self.intaken()
        self.assertIs(receipt["recoverable"], False)

    def intaken_now(self):
        adapter = Custodian(self.collection())
        return request_intake(self.store, self.port, adapter,
                              attempt_id=ATTEMPT), adapter


# -- effectively once ---------------------------------------------------------


class TakingCustodyHappensOnce(IntakeCase):

    def test_an_exact_retry_replays_the_receipt_it_already_produced(self):
        receipt, _ = self.intaken()
        again = record_intake(self.store, self.port, attempt_id=ATTEMPT,
                              collected=self.collection())
        self.assertEqual(again["receipt_digest"], receipt["receipt_digest"])
        held = self.store._connection.execute(
            "SELECT COUNT(*) FROM intake_artifacts").fetchone()[0]
        self.assertEqual(held, 1, "a replay took custody a second time")

    def test_different_material_under_the_same_identity_refuses(self):
        """The identity is the ACT and the signature carries the bytes. If the
        identity varied with the bytes, two different collections would be two
        different operations and BOTH would commit."""
        self.intaken()
        moved = self.collection()
        moved["artifacts"][0]["custody_locator"] = "file:///elsewhere"
        with self.assertRaises(ContractRefusal) as caught:
            record_intake(self.store, self.port, attempt_id=ATTEMPT,
                          collected=moved)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_the_operation_identity_is_derived_from_the_attempt(self):
        """Derived rather than minted, so a restart names what it already did
        instead of doing it twice."""
        self.frozen_attempt()
        row = self.attempt_row()
        self.assertEqual(intake_operation(row)["operation_id"],
                         intake_operation(row)["operation_id"])
        self.intaken_again()
        self.assertEqual(
            self.store._connection.execute(
                "SELECT intake_operation_id FROM intakes").fetchone()[0],
            intake_operation(row)["operation_id"])

    def intaken_again(self):
        adapter = Custodian(self.collection())
        return request_intake(self.store, self.port, adapter,
                              attempt_id=ATTEMPT)


# -- retention ----------------------------------------------------------------


class TheRetentionPolicyIsBoundNeverRead(IntakeCase):

    def test_a_decision_records_the_policy_that_made_it(self):
        """This resolves the question this dossier was returned with.

        `retention_policy_digest` is one of TEN `*_policy_digest` members of
        the assignment manifest and the frozen schema states the shape of NONE
        of them. That is not an omission about retention; it is how this
        contract treats policy documents. A manager binds a policy by IDENTITY
        and acts on the operation that cites it, and interpreting one here
        would be the boundary violation rather than the fix.
        """
        receipt = self.retained_ready("retain")
        decisions = retentions_of(self.store, ATTEMPT)
        self.assertEqual(len(decisions), len(receipt["artifacts"]))
        self.assertEqual(decisions[0]["disposition"], "retain")
        self.assertEqual(decisions[0]["retention_policy_digest"], RETENTION)

    def test_nothing_here_opens_the_policy_document(self):
        """The digest is all this module is ever given, and a case that passes
        one nothing could dereference is the proof."""
        self.intaken()
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="retain",
                         retention_policy_digest=RETENTION)
        self.assertEqual(retentions_of(self.store, ATTEMPT)[0]
                         ["retention_policy_digest"], RETENTION)

    def test_retention_cannot_precede_custody(self):
        """Deciding the fate of artifacts that were never taken into custody
        would record an authority over bytes nobody has."""
        self.frozen_attempt()
        with self.assertRaises(ContractRefusal) as caught:
            decide_retention(self.store, self.port, Custodian(),
                             attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                             disposition="retain",
                             retention_policy_digest=RETENTION)
        self.assertIn("has not been taken into custody",
                      caught.exception.message)

    def test_an_artifact_not_in_custody_cannot_be_decided(self):
        self.intaken()
        with self.assertRaises(ContractRefusal) as caught:
            decide_retention(self.store, self.port, Custodian(),
                             attempt_id=ATTEMPT, artifact_ids=["artifact-9"],
                             disposition="retain",
                             retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "retention")

    def test_a_disposition_outside_the_frozen_three_refuses(self):
        self.intaken()
        with self.assertRaises(ContractRefusal) as caught:
            decide_retention(self.store, self.port, Custodian(),
                             attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                             disposition="keep-forever",
                             retention_policy_digest=RETENTION)
        self.assertIn("is not a retention disposition", caught.exception.message)

    def test_a_new_policy_decides_again_and_does_not_accumulate(self):
        """Two live dispositions for one artifact would make "may this be
        destroyed" a question with two answers, which is the question cleanup
        authorization asks."""
        self.retained_ready("retain")
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="discard-after-intake",
                         retention_policy_digest=OTHER_POLICY)
        decisions = retentions_of(self.store, ATTEMPT)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["disposition"], "discard-after-intake")
        self.assertEqual(decisions[0]["retention_policy_digest"], OTHER_POLICY)

    def test_the_same_decision_under_the_same_policy_replays(self):
        self.retained_ready("retain")
        again = decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=["artifact-1"], disposition="retain",
            retention_policy_digest=RETENTION)
        self.assertEqual(again["disposition"], "retain")
        self.assertEqual(len(retentions_of(self.store, ATTEMPT)), 1)


# -- cleanup ------------------------------------------------------------------


class BlockedOnIntakeIsAStateAndNotARetry(IntakeCase):

    def test_cleanup_without_custody_is_recorded_as_blocked(self):
        """The frozen axis HAS `blocked-on-intake`, so cleanup waits on intake
        rather than racing it. An implementation that retried instead would be
        inventing a mechanism the axis already has."""
        self.frozen_attempt()
        adapter = Custodian()
        answer = authorize_cleanup(self.store, self.port, adapter,
                                   attempt_id=ATTEMPT,
                                   retention_policy_digest=RETENTION)
        self.assertEqual(self.attempt_axis("cleanup"), "blocked-on-intake")
        self.assertIn("has not been taken into custody", answer["why"])
        self.assertEqual(adapter.destroyed_with, [],
                         "the adapter was asked to destroy a runtime whose "
                         "material nobody had collected")

    def test_a_blocked_cleanup_is_not_a_refusal(self):
        """Blocked is an ANSWER. A caller that had to catch an exception to
        learn it would have to distinguish waiting from failing by reading
        prose."""
        self.frozen_attempt()
        answer = authorize_cleanup(self.store, self.port, Custodian(),
                                   attempt_id=ATTEMPT,
                                   retention_policy_digest=RETENTION)
        self.assertEqual(answer["attempt_id"], ATTEMPT)

    def test_blocked_cleanup_completes_once_intake_happens(self):
        self.frozen_attempt()
        # NOT ended yet: `blocked-on-intake` is answered before the liveness
        # gate, and ending the assignment here would quarantine the intake
        # below and change what this case is about.
        authorize_cleanup(self.store, self.port, Custodian(),
                          attempt_id=ATTEMPT,
                          retention_policy_digest=RETENTION)
        self.assertEqual(self.attempt_axis("cleanup"), "blocked-on-intake")
        adapter = Custodian(self.collection())
        request_intake(self.store, self.port, adapter, attempt_id=ATTEMPT)
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="discard-after-intake",
                         retention_policy_digest=RETENTION)
        self.ended()
        answer = authorize_cleanup(self.store, self.port, Custodian(),
                                   attempt_id=ATTEMPT,
                                   retention_policy_digest=RETENTION)
        self.assertEqual(answer["cleanup"], "complete")
        self.assertEqual(self.attempt_axis("cleanup"), "complete")


class TheDeliveryProvidersMustEndBeforeCleanupIsClean(IntakeCase):
    """W6636 [P0]: the shared start/destroy settlement crossing.

    `OciAdapter.destroy` removes the container, proves the exact identity
    absent, and then settles the two mounted roots on that same evidence --
    answering `credentials` and `launch` endings beside the runtime state. The
    manager read the runtime state and nothing else.

    TWO DEFECTS, NOT ONE, and the dossier named only the second. The contract
    for the destroy answer did not NAME the two endings at all, and
    `boundaries.document` refuses an unrecognised member rather than ignoring
    it -- so `authorize_cleanup` could not complete against the real adapter
    at all. Behind that refusal sat the defect the dossier describes: nothing
    would have read them if they had been admitted.
    """

    def test_directory_custody_is_required_before_runtime_destruction(self):
        """A mandatory ending capability is proved before the first mutation.

        Directory custody is now a precondition of every positively absent
        ending. Discovering that the adapter cannot perform it only after
        ``destroy`` removed the runtime and tore down its providers leaves a
        half-ending that the refused call claimed not to start.
        """
        self.retained_ready("discard-after-intake")
        self.ended()
        adapter = Custodian()
        adapter.normalize_directory = None

        with self.assertRaises(ContractRefusal):
            authorize_cleanup(
                self.store, self.port, adapter, attempt_id=ATTEMPT,
                retention_policy_digest=RETENTION)

        self.assertEqual(
            adapter.destroyed_with, [],
            "cleanup destroyed the runtime before proving directory custody")

    def settled(self, **endings):
        self.retained_ready("discard-after-intake")
        self.ended()
        return authorize_cleanup(
            self.store, self.port,
            # Both endings default to `not-delivered` and a case overrides
            # the one it is about, because the contract is closed: an answer
            # missing a provider is refused, not read as "no such provider".
            Custodian(destroyed={"state": "absent",
                                 "why": "the engine answered that this exact "
                                        "identity does not exist",
                                 **{"credentials":
                                    {"lifecycle_state": "not-delivered"},
                                    "launch":
                                    {"lifecycle_state": "not-delivered"}},
                                 **endings}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)

    def test_the_real_adapter_s_answer_is_admitted_at_all(self):
        """The shape `OciAdapter.destroy` actually returns.

        Before the crossing named them, this exact document was refused for
        carrying `credentials` and `launch` -- so the composed lifecycle could
        not reach any cleanup ending, clean or otherwise.
        """
        answer = self.settled(
            credentials={"attempt_id": ATTEMPT, "lifecycle_state":
                         "torn-down", "slots": ["registry"]},
            launch={"lifecycle_state": "torn-down"})
        self.assertEqual(answer["cleanup"], "complete")
        self.assertEqual(self.attempt_axis("cleanup"), "complete")

    def test_an_adapter_with_no_providers_still_settles(self):
        """The endings are OPTIONAL, and they have to be: an adapter that
        delivers neither root legitimately answers about the runtime alone,
        and every case above this one is written that way."""
        answer = self.settled()
        self.assertEqual(answer["cleanup"], "complete")

    def test_a_provider_that_never_delivered_is_not_a_reason_to_wait(self):
        """`not-delivered` is terminal. There is no root to prove gone, and
        treating "this attempt had no credential" as unfinished business would
        strand every attempt that needed none."""
        answer = self.settled(
            credentials={"lifecycle_state": "not-delivered"},
            launch={"lifecycle_state": "torn-down"})
        self.assertEqual(answer["cleanup"], "complete")

    def test_an_unresolved_launch_root_keeps_cleanup_open(self):
        """THE DEFECT. Positive container absence with a launch root still on
        disk was recorded `complete`: an attempt reported cleaned up, its lane
        reusable, and manager storage nothing would ever come back for."""
        answer = self.settled(
            credentials={"lifecycle_state": "not-delivered"},
            launch={"lifecycle_state": "unresolved",
                    "why": "the launch root is still present after removal"})
        self.assertNotIn("cleanup", answer)
        self.assertIn("still present", answer["why"])
        # THE RUNTIME OBSERVATION STANDS. The container really is gone and
        # that axis says so; it is CLEANUP that has not finished, and leaving
        # it where it is offers the retry exactly as uncertainty does.
        self.assertEqual(self.attempt_axis("execution_runtime"), "destroyed")
        self.assertEqual(self.attempt_axis("cleanup"), "pending")

    def test_an_unresolved_credential_root_keeps_cleanup_open(self):
        """The other root, driven separately: one guard covering both would
        pass with either half missing."""
        answer = self.settled(
            credentials={"lifecycle_state": "unresolved",
                         "why": "the credential root could not be removed"},
            launch={"lifecycle_state": "torn-down"})
        self.assertNotIn("cleanup", answer)
        self.assertIn("credential root", answer["why"])
        self.assertEqual(self.attempt_axis("cleanup"), "pending")

    def test_both_unresolved_roots_are_named(self):
        """Two roots can be unresolved for two different reasons, and an
        operator has to act on both -- so the reasons are a list rather than
        a boolean."""
        answer = self.settled(
            credentials={"lifecycle_state": "unresolved",
                         "why": "the credential root could not be removed"},
            launch={"lifecycle_state": "unresolved",
                    "why": "the launch root is still present after removal"})
        self.assertIn("credentials:", answer["why"])
        self.assertIn("launch:", answer["why"])

    def test_a_pending_cleanup_re_enters_provider_teardown_every_time(self):
        """RE-REVIEW [P0]: the retry skipped the adapter entirely.

        `_destroyed` short-circuited on `execution_runtime == "destroyed"` and
        answered a synthetic `absent` with NO provider endings -- and the
        endings are optional, so the retry that was supposed to finish the
        teardown recorded `complete` with no provider retried at all. The
        first destroy truthfully moves the runtime axis, which is what made
        the bypass reachable: the shape this round introduced defeated itself
        one call later.

        Three destroys, and the ADAPTER CALL COUNT is the assertion. The
        submitted retry case supplied a second positive answer and never
        checked that anything was asked, so it passed straight through the
        bypass -- which is exactly why the count is what this asserts.
        """
        self.retained_ready("discard-after-intake")
        self.ended()
        stuck = {"state": "absent", "why": "gone",
                 "credentials": {"lifecycle_state": "not-delivered"},
                 "launch": {"lifecycle_state": "unresolved",
                            "why": "the launch root is still present"}}
        calls = []
        for round_number in (1, 2):
            adapter = Custodian(destroyed=dict(stuck))
            answer = authorize_cleanup(self.store, self.port, adapter,
                                       attempt_id=ATTEMPT,
                                       retention_policy_digest=RETENTION)
            calls.append(len(adapter.destroyed_with))
            self.assertNotIn("cleanup", answer, round_number)
            # The runtime axis moves on the FIRST pass and stays there. It is
            # a fact about the container and says nothing about the roots.
            self.assertEqual(self.attempt_axis("execution_runtime"),
                             "destroyed")
            self.assertEqual(self.attempt_axis("cleanup"), "pending")
        self.assertEqual(calls, [1, 1],
                         "a pending cleanup skipped the provider teardown")

        finished = Custodian(destroyed={
            "state": "absent", "why": "gone",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "torn-down"}})
        settled = authorize_cleanup(self.store, self.port, finished,
                                    attempt_id=ATTEMPT,
                                    retention_policy_digest=RETENTION)
        self.assertEqual(len(finished.destroyed_with), 1)
        self.assertEqual(settled["cleanup"], "complete")
        self.assertEqual(self.attempt_axis("cleanup"), "complete")

    def test_a_destroyed_runtime_is_still_asked_about(self):
        """The narrow fact underneath the case above, on its own.

        An identity the engine no longer has is safe to ask about -- `destroy`
        is `rm --force` followed by an inspection, and a gone identity answers
        `absent` -- so the short-circuit bought nothing and cost the second
        half of the ending.
        """
        self.retained_ready("discard-after-intake")
        self.ended()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="destroyed")
        adapter = Custodian()
        authorize_cleanup(self.store, self.port, adapter, attempt_id=ATTEMPT,
                          retention_policy_digest=RETENTION)
        self.assertEqual(len(adapter.destroyed_with), 1)

    def test_an_unsettled_cleanup_can_be_retried_once_the_root_is_gone(self):
        """The axis staying where it is IS the offer to try again, which is
        the whole reason failing closed here is affordable."""
        first = self.settled(
            launch={"lifecycle_state": "unresolved", "why": "still present"})
        self.assertNotIn("cleanup", first)
        again = authorize_cleanup(
            self.store, self.port,
            Custodian(destroyed={"state": "absent", "why": "gone",
                                 "credentials":
                                 {"lifecycle_state": "not-delivered"},
                                 "launch": {"lifecycle_state": "torn-down"}}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        # The retry is EXACT -- same receipt, same policy -- so this only
        # passes because nothing that failed to settle was journalled.
        self.assertEqual(again["cleanup"], "complete")

    def test_an_omitted_provider_is_refused_rather_than_read_as_absent(self):
        """RE-REVIEW [P0]: omission erased a teardown that was owed.

        The endings were OPTIONAL, so a first answer of runtime `absent` with
        launch `unresolved` correctly left cleanup pending -- and a later
        answer that simply left `launch` out settled it `complete`, because an
        absent member read as "no such provider". The adapter WAS called; what
        was lost was the knowledge that a launch teardown was required.

        The manager cannot remember applicability without inventing durable
        state for it, so the contract says it: every provider answers on every
        destroy, and no provider is spelled `not-delivered` out loud.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.retained_ready("discard-after-intake")
            self.ended()
            authorize_cleanup(
                self.store, self.port,
                Custodian(destroyed={"state": "absent", "why": "gone"}),
                attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "schema")
        self.assertIn("credentials", str(caught.exception))
        self.assertEqual(self.attempt_axis("cleanup"), "pending")

    def test_an_omission_after_an_unresolved_ending_survives_a_restart(self):
        """The review's exact required regression.

        Unresolved first; the manager is REOPENED, which is what makes this
        about durable applicability rather than about one process's memory;
        then an omitting answer must not settle. Only an explicit terminal
        ending may.
        """
        self.retained_ready("discard-after-intake")
        self.ended()
        first = authorize_cleanup(
            self.store, self.port,
            Custodian(destroyed={
                "state": "absent", "why": "gone",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "unresolved",
                           "why": "the launch root is still present"}}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertNotIn("cleanup", first)

        self.store.close()
        self.store = ControlStore.open(self.path, incarnation="manager-2",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)

        omitting = Custodian(destroyed={"state": "absent", "why": "gone"})
        with self.assertRaises(ContractRefusal):
            authorize_cleanup(self.store, self.port, omitting,
                              attempt_id=ATTEMPT,
                              retention_policy_digest=RETENTION)
        self.assertEqual(self.attempt_axis("cleanup"), "pending")

        settled = authorize_cleanup(
            self.store, self.port,
            Custodian(destroyed={
                "state": "absent", "why": "gone",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "torn-down"}}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertEqual(settled["cleanup"], "complete")

    def test_an_ending_this_build_does_not_recognise_is_refused(self):
        """Not read as unresolved and not read as settled.

        A word this build does not know is a provider it was not written
        against, and guessing which of the two it meant is the choice the
        boundary exists to refuse.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(launch={"lifecycle_state": "mostly-gone"})
        self.assertEqual(caught.exception.code, "schema")
        self.assertIn("mostly-gone", str(caught.exception))

    def test_an_ending_that_is_not_a_document_is_refused(self):
        with self.assertRaises(ContractRefusal):
            self.settled(launch="torn-down")


class RetainedAndCompleteAreDifferentEndings(IntakeCase):

    def settle(self, disposition, **kwargs):
        self.retained_ready(disposition)
        self.ended()
        return authorize_cleanup(self.store, self.port,
                                 Custodian(**kwargs), attempt_id=ATTEMPT,
                                 retention_policy_digest=RETENTION)

    def test_nothing_left_behind_is_complete(self):
        answer = self.settle("discard-after-intake")
        self.assertEqual(answer["cleanup"], "complete")
        self.assertEqual(answer["kept"], [])

    def test_material_kept_by_policy_ends_retained(self):
        """Reporting retention as completion would erase the reason the
        material still exists."""
        answer = self.settle("retain")
        self.assertEqual(answer["cleanup"], "retained")
        self.assertEqual(answer["kept"], ["artifact-1"])
        self.assertEqual(self.attempt_axis("cleanup"), "retained")

    def test_material_kept_by_policy_survives_at_its_custody_locator(self):
        """A retained ending is an account of bytes that still exist.

        The manager custody tree is a sibling of the writable roots inside
        the attempt home. Removing that whole home after deciding ``retain``
        destroys the very locator the terminal document says was kept.
        """
        from baton_v12.worker_manager.workspaces import assignment_workspace

        roots = assignment_workspace(
            input_roots.configured_group(self.store), self.storage, ATTEMPT)
        locator = os.path.join(os.path.dirname(roots["workspace"]),
                               "custody", ATTEMPT, "artifact-1")
        os.makedirs(os.path.dirname(locator), exist_ok=True)
        with open(locator, "wb") as writing:
            writing.write(b"retained material")
        self.frozen_attempt()
        collection = self.collection()
        collection["artifacts"][0]["custody_locator"] = "file://" + locator
        receipt = request_intake(
            self.store, self.port, Custodian(collection), attempt_id=ATTEMPT)
        decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="retain", retention_policy_digest=RETENTION)
        self.ended()

        answer = authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION)

        self.assertEqual(answer["cleanup"], "retained")
        self.assertTrue(os.path.isfile(locator),
                        "retained cleanup deleted the custody locator")

    def test_quarantined_material_ends_retained_too(self):
        """`quarantine` is doubt keeping the bytes and `retain` is policy
        keeping them. Both are material that is still there, which is what
        `retained` records."""
        answer = self.settle("quarantine")
        self.assertEqual(answer["cleanup"], "retained")

    def test_quarantined_custody_ends_retained_whatever_the_disposition(self):
        """The custody answer outlives the per-artifact decision: material
        collected for a generation that had ended is still material somebody
        has to look at, and cleaning up around it is not completion."""
        self.frozen_attempt()
        self.session.live_assignment = None
        request_intake(self.store, self.port, Custodian(self.collection()),
                       attempt_id=ATTEMPT)
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="discard-after-intake",
                         retention_policy_digest=RETENTION)
        self.ended()
        answer = authorize_cleanup(self.store, self.port, Custodian(),
                                   attempt_id=ATTEMPT,
                                   retention_policy_digest=RETENTION)
        self.assertEqual(answer["cleanup"], "retained")

    def test_an_exact_retry_of_a_settled_destroy_replays(self):
        """Effectively-once, and it is the reason the terminal refusal sits
        BELOW the journal. A retry of the act that already settled reproduces
        its answer; nothing about today is a precondition for that."""
        answer = self.settle("discard-after-intake")
        self.ended()
        again = authorize_cleanup(self.store, self.port, Custodian(),
                                  attempt_id=ATTEMPT,
                                  retention_policy_digest=RETENTION)
        self.assertEqual(again["cleanup"], answer["cleanup"])

    def test_a_different_destroy_after_an_ending_is_refused(self):
        """And this is what the terminal check is actually for: a DIFFERENT
        act -- another policy, another receipt -- arriving after the cleanup
        axis has already settled."""
        self.settle("discard-after-intake")
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="retain",
                         retention_policy_digest=OTHER_POLICY)
        with self.assertRaises(ContractRefusal) as caught:
            self.ended()
            authorize_cleanup(self.store, self.port, Custodian(),
                              attempt_id=ATTEMPT,
                              retention_policy_digest=OTHER_POLICY)
        self.assertEqual(caught.exception.code, "already-terminal")


class CleanupIsAuthorizedByProofRatherThanByAsking(IntakeCase):

    def test_an_undecided_artifact_stops_the_destroy(self):
        """Cleanup destroys nothing nobody ruled on."""
        self.intaken()
        adapter = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.ended()
            authorize_cleanup(self.store, self.port, adapter,
                              attempt_id=ATTEMPT,
                              retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "retention")
        self.assertEqual(adapter.destroyed_with, [])

    def test_a_decision_made_under_another_policy_is_not_this_authorization(self):
        """`runtimeDestroyBody` requires the retention policy digest, and
        citing a policy the decisions were not made under would be an
        authorization nobody gave."""
        self.retained_ready("retain")
        with self.assertRaises(ContractRefusal) as caught:
            self.ended()
            authorize_cleanup(self.store, self.port, Custodian(),
                              attempt_id=ATTEMPT,
                              retention_policy_digest=OTHER_POLICY)
        self.assertEqual(caught.exception.code, "retention")
        self.assertIn("was decided under", caught.exception.message)


class PositiveAbsenceOrNoEnding(IntakeCase):

    def ready(self, **kwargs):
        self.retained_ready("discard-after-intake")
        return Custodian(**kwargs)

    def settle(self, adapter):
        self.ended()
        return authorize_cleanup(self.store, self.port, adapter,
                                 attempt_id=ATTEMPT,
                                 retention_policy_digest=RETENTION)

    def test_absence_is_what_moves_the_runtime_axis(self):
        """Only an engine that says this exact identity does not exist produces
        `absent`, and a command that returned zero is not evidence that
        anything is gone."""
        adapter = self.ready()
        self.settle(adapter)
        # The manager delivers `runtimeDestroyBody` now, so what the adapter
        # was handed is the command; the identity it acts on is inside it.
        self.assertEqual([one["runtime_id"] for one in adapter.destroyed_with],
                         ["runtime-1"])
        self.assertEqual(self.attempt_axis("execution_runtime"), "destroyed")

    def test_a_runtime_that_survived_the_destroy_is_a_failed_cleanup(self):
        """Positively still there. The destroy was ordered and the runtime
        survived it, which is a settled failure rather than an unknown."""
        answer = self.settle(self.ready(destroyed={
            "state": "running", "why": "the engine still lists it",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}}))
        self.assertEqual(answer["cleanup"], "failed")
        self.assertEqual(self.attempt_axis("cleanup"), "failed")
        self.assertNotEqual(self.attempt_axis("execution_runtime"),
                            "destroyed",
                            "a surviving runtime was recorded destroyed")

    def test_an_uncertain_answer_ends_nothing(self):
        """A cleanup axis that advanced on an account which did not settle the
        question would record an ending nobody observed. The offer to try again
        is the axis staying where it is."""
        answer = self.settle(self.ready(destroyed={
            "state": "uncertain", "why": "the engine refused to inspect it",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}}))
        self.assertEqual(answer["state"], "uncertain")
        self.assertNotIn("cleanup", answer)
        self.assertEqual(self.attempt_axis("cleanup"), "pending")
        self.assertEqual(self.attempt_axis("execution_runtime"), "quiescent")

    def test_an_uncertain_destroy_can_actually_be_tried_again(self):
        """W6636: the sentence above was true of the AXIS and false of the
        OPERATION.

        `_settle` returned the unsettled document from inside the transaction,
        so the destroy committed with "it did not settle" as its result -- and
        the retry that was supposed to finish the cleanup is the same receipt
        under the same policy, which is an exact retry and replays it. Cleanup
        stayed `pending` and could never leave it, which is a stuck attempt
        rather than a retryable one.

        Nothing that did not settle is journalled now, so this walks the whole
        offer rather than asserting the axis and stopping where the defect
        began.
        """
        self.settle(self.ready(destroyed={
            "state": "uncertain", "why": "the engine refused to inspect it",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}}))
        self.assertEqual(self.attempt_axis("cleanup"), "pending")
        # THE SAME RECEIPT UNDER THE SAME POLICY, which is what a retry of
        # this cleanup IS -- so it is an exact retry, and that is precisely
        # why journalling the non-ending made it permanent.
        again = self.settle(Custodian())
        self.assertEqual(again["cleanup"], "complete", again)
        self.assertEqual(self.attempt_axis("cleanup"), "complete")

    def test_an_uncertain_runtime_cannot_be_cleaned_up_at_all(self):
        """THE FROZEN ASYMMETRY, refused rather than worked around. `uncertain`
        may never become `destroyed` -- inferring destruction from a failure to
        look would report a cleaned-up runtime that is still executing
        somebody's code -- so cleanup waits for a reconciliation that observes
        what is true."""
        adapter = self.ready()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="uncertain")
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(adapter)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertEqual(adapter.destroyed_with, [],
                         "a runtime nobody could describe was destroyed anyway")

    def test_an_answer_about_another_runtime_is_not_this_one(self):
        adapter = self.ready()
        adapter.destroyed = {"state": "absent", "why": "gone"}
        with patch.object(adapter, "destroy", lambda runtime_id: {
                "runtime_id": "runtime-9", "state": "absent", "why": "gone",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "not-delivered"}}):
            with self.assertRaises(ContractRefusal) as caught:
                self.settle(adapter)
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_quiescent_with_nothing_attached_is_refused_not_assumed_absent(self):
        """Asking an engine to remove an identity this manager never attached
        would be asking about something that has no name -- and ASSUMING it
        absent would be the inference the whole runtime axis forbids.

        The state is built from W6628's own attempt, which observes quiescence
        without ever starting anything. It is not a state the runtime slice
        produces, which is exactly why cleanup says so instead of guessing.
        """
        OutputCase.attempt(self)
        from baton_v12.worker_manager import request_freeze
        request_freeze(self.store, self.port, Collector(self.result()),
                       attempt_id=ATTEMPT, disposition="completed")
        request_intake(self.store, self.port, Custodian(self.collection()),
                       attempt_id=ATTEMPT)
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="discard-after-intake",
                         retention_policy_digest=RETENTION)
        self.assertIsNone(self.attempt_row()["runtime_id"])
        adapter = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(adapter)
        self.assertIn("no absence to prove", caught.exception.message)
        self.assertEqual(adapter.destroyed_with, [])

    def test_an_already_destroyed_runtime_is_not_destroyed_twice(self):
        adapter = self.ready()
        self.settle(adapter)
        self.assertEqual(len(adapter.destroyed_with), 1)


class RestartOrderingIsPreserved(IntakeCase):

    def test_a_retry_of_retention_replays_rather_than_refusing_on_state(self):
        """The ordering W6628's receiver was corrected for twice: a state read
        placed above the journal makes an exact retry refuse once the state has
        moved. Retention is decided, the material is then destroyed, and the
        same decision replays instead of refusing on custody it can no longer
        prove today."""
        self.retained_ready("discard-after-intake")
        self.ended()
        authorize_cleanup(self.store, self.port, Custodian(),
                          attempt_id=ATTEMPT,
                          retention_policy_digest=RETENTION)
        self.store._connection.execute("DELETE FROM intake_artifacts")
        again = decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=["artifact-1"], disposition="discard-after-intake",
            retention_policy_digest=RETENTION)
        self.assertEqual(again["disposition"], "discard-after-intake")

    def test_a_retry_of_intake_replays_after_the_axis_moved(self):
        """The same property for custody: the axis is `sealed` by the time a
        retry arrives, and `sealed` is not `frozen`."""
        receipt, _ = self.intaken()
        self.assertEqual(self.attempt_axis("output"), "sealed")
        again = record_intake(self.store, self.port, attempt_id=ATTEMPT,
                              collected=self.collection())
        self.assertEqual(again["receipt_digest"], receipt["receipt_digest"])


# -- §13, for the four doors `test_secrets` cannot reach ----------------------


class EveryJournalledDoorRefusesALiveBearer(IntakeCase):
    """W6630 §13's public half, for this module's four journalled doors.

    `test_secrets` derives the whole exported universe and PROBES every surface
    it classifies as constructing, which is what makes those entries facts
    rather than claims. Four of this module's ten cannot be probed there: each
    of them refuses for a missing attempt long before it reaches its walk, so a
    probe against that file's fixture would pass for the wrong reason and
    report a guard it never ran -- exactly the defect that file's own re-review
    found in two prose-only entries.

    So the accounting says the walk is `manager_signature`'s, `retain_operation`
    's or `destroy_operation`'s, and it points here. This is the here: the same
    four doors, driven through the fixture that CAN reach them, against a bearer
    that is live at the moment of the call.

    AND THE GUARDS ARE LAYERED, which is worth saying because it is what these
    cases DO NOT prove. Measured by muting them one at a time: with this
    module's own walks gone the four still refuse, because `manager_signature`
    walks the signature; with that gone too they still refuse, because the
    journal walks the whole row before the commit. Each case above proves its
    door refuses -- which is §13's acceptance -- and not which of the three did
    it. The named owner is the FIRST, and the ones behind it are why removing
    one of them is not a leak.
    """

    def refuses(self, run):
        with held_secret(BEARER):
            with self.assertRaises(ContractRefusal) as caught:
                run()
        self.assertEqual(caught.exception.code, "secret-leak",
                         caught.exception.message)

    def test_record_intake_refuses_a_bearer_in_the_collection(self):
        """The adapter's OWN answer is the caller text here. A custody locator
        is the one member of a collection this manager takes rather than
        compares, so it is the member a bearer travels in."""
        self.frozen_attempt()
        self.refuses(lambda: record_intake(
            self.store, self.port, attempt_id=ATTEMPT,
            collected=self.collection(artifacts=[{
                "artifact_id": "artifact-1",
                "content_digest": self.frozen_output()["artifacts"][0][
                    "content_digest"],
                "bytes": self.frozen_output()["artifacts"][0]["bytes"],
                "custody_locator": f"https://custody.example/{BEARER}"}])))

    def test_request_intake_refuses_what_the_adapter_hands_back(self):
        """The same door, entered the way an operator enters it. The adapter is
        called and its answer goes straight into `record_intake`, so a bearer an
        adapter invents reaches the same walk as one a caller passes."""
        self.frozen_attempt()
        adapter = Custodian(self.collection(artifacts=[{
            "artifact_id": "artifact-1",
            "content_digest":
                self.frozen_output()["artifacts"][0]["content_digest"],
            "bytes": self.frozen_output()["artifacts"][0]["bytes"],
            "custody_locator": f"https://custody.example/{BEARER}"}]))
        self.refuses(lambda: request_intake(self.store, self.port, adapter,
                                            attempt_id=ATTEMPT))

    def test_decide_retention_refuses_a_bearer_in_the_policy_digest(self):
        """The policy is bound by identity and never read -- and an identity
        this manager composes into an operation id is portable, so a bearer
        arriving as one leaves inside protocol identity unless the walk runs
        first."""
        receipt, _ = self.intaken()
        self.refuses(lambda: decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="retain",
            retention_policy_digest=f"sha256:{BEARER}"))

    def test_authorize_cleanup_refuses_a_bearer_in_the_policy_digest(self):
        """The strongest of the four, because `runtimeDestroyBody` puts both
        digests in the body: the policy digest is part of the DESTROY identity
        rather than only of its signature."""
        self.retained_ready()
        self.refuses(lambda: authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=f"sha256:{BEARER}"))

    def test_the_walk_is_what_refuses_and_not_a_precondition(self):
        """THE CASE THAT MAKES THE FOUR ABOVE MEAN SOMETHING.

        A refusal is not evidence of a walk: every one of these doors refuses a
        missing attempt, an unfrozen output and an undecided artifact too, and a
        probe that never got past those would look exactly like a passing §13
        case. So the same operands are driven with the bearer FORGOTTEN, and
        each door is required to get through -- which is what proves the four
        cases above reached the walk rather than stopping short of it.
        """
        receipt, _ = self.intaken()
        decided = decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="retain",
            retention_policy_digest="sha256:" + "5" * 64)
        self.assertEqual(decided["disposition"], "retain")
        self.ended()
        settled = authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest="sha256:" + "5" * 64)
        self.assertEqual(settled["cleanup"], "retained")


# -- independent review ------------------------------------------------------


class IndependentContractReview(IntakeCase):
    """Regressions for the W6629 independent implementation review."""

    def test_cleanup_waits_until_the_assignment_is_ended_or_fenced(self):
        """The predecessor W4 decision is explicit: destroying the runtime of
        an assignment the authority still reports live tears out a worker that
        remains authorized to execute."""
        self.retained_ready("discard-after-intake")
        adapter = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            authorize_cleanup(self.store, self.port, adapter,
                              attempt_id=ATTEMPT,
                              retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(adapter.destroyed_with, [])

    def test_retention_is_delivered_to_the_adapter_as_a_command(self):
        """Validating that `retain` exists is not delivery. The frozen
        `output.retain` body has five required operands, and the adapter needs
        the operation identity beside them for an effectively-once command."""
        class RecordingCustodian(Custodian):
            def __init__(self):
                super().__init__()
                self.retained_with = []

            def retain(self, operands):
                self.retained_with.append(operands)
                return True

        self.intaken()
        adapter = RecordingCustodian()
        decide_retention(self.store, self.port, adapter, attempt_id=ATTEMPT,
                         artifact_ids=["artifact-1"], disposition="retain",
                         retention_policy_digest=RETENTION)
        self.assertEqual(len(adapter.retained_with), 1)
        command = adapter.retained_with[0]
        self.assertEqual(command["runtime_attempt_id"], ATTEMPT)
        self.assertEqual(command["assignment_ref"]["participant"], WHO)
        self.assertEqual(command["artifact_ids"], ["artifact-1"])
        self.assertEqual(command["disposition"], "retain")
        self.assertEqual(command["retention_policy_digest"], RETENTION)
        self.assertIn("operation", command)

    def test_one_policy_can_decide_different_artifact_groups(self):
        """`outputRetainBody` puts the artifact set and disposition in the
        command. They therefore distinguish decisions made under one policy;
        keying the operation by policy alone turns the second into a collision.
        """
        declared = self.declaration["outputs"][0]
        self.redeclared(outputs=[
            declared,
            {**declared, "name": "evidence", "path": "workspace/evidence"},
        ])
        proposal = self.present()[0]
        evidence = self.present(name="evidence")[0]
        evidence["artifact"] = {
            **evidence["artifact"], "artifact_id": "artifact-2",
            "locator": "file:///var/lib/baton/artifact-2"}
        self.frozen_attempt(outputs=[proposal, evidence])
        request_intake(self.store, self.port, Custodian(self.collection()),
                       attempt_id=ATTEMPT)
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-1"],
                         disposition="retain",
                         retention_policy_digest=RETENTION)
        decide_retention(self.store, self.port, Custodian(),
                         attempt_id=ATTEMPT, artifact_ids=["artifact-2"],
                         disposition="discard-after-intake",
                         retention_policy_digest=RETENTION)
        self.assertEqual(
            [(one["artifact_id"], one["disposition"])
             for one in retentions_of(self.store, ATTEMPT)],
            [("artifact-1", "retain"),
             ("artifact-2", "discard-after-intake")])

    def test_a_later_policy_can_replace_part_of_a_grouped_decision(self):
        """Retention stores one current decision per artifact. Replacing one
        artifact must not make the untouched row look like a forged fragment
        of the earlier command that originally decided both artifacts."""
        declared = self.declaration["outputs"][0]
        self.redeclared(outputs=[
            declared,
            {**declared, "name": "evidence", "path": "workspace/evidence"},
        ])
        proposal = self.present()[0]
        evidence = self.present(name="evidence")[0]
        evidence["artifact"] = {
            **evidence["artifact"], "artifact_id": "artifact-2",
            "locator": "file:///var/lib/baton/artifact-2"}
        self.frozen_attempt(outputs=[proposal, evidence])
        request_intake(self.store, self.port, Custodian(self.collection()),
                       attempt_id=ATTEMPT)
        decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=["artifact-1", "artifact-2"], disposition="retain",
            retention_policy_digest=RETENTION)
        decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=["artifact-2"], disposition="discard-after-intake",
            retention_policy_digest=OTHER_POLICY)
        self.assertEqual(
            [(one["artifact_id"], one["disposition"],
              one["retention_policy_digest"])
             for one in retentions_of(self.store, ATTEMPT)],
            [("artifact-1", "retain", RETENTION),
             ("artifact-2", "discard-after-intake", OTHER_POLICY)])

    def test_destroy_is_delivered_with_the_authorizing_contract_body(self):
        """A bare runtime id omits both digests that authorize destruction and
        makes the adapter guess which protocol operation it is executing."""
        class ProtocolCustodian(Custodian):
            def destroy(self, command):
                self.destroyed_with.append(command)
                # Both provider endings, because the destroy answer's member
                # contract is closed: this case is about the COMMAND that
                # crosses, and an answer that could not be read would stop it
                # before it got there.
                return {"runtime_id": command["runtime_id"], "state": "absent",
                        "why": "the exact runtime is absent",
                        "credentials": {"lifecycle_state": "not-delivered"},
                        "launch": {"lifecycle_state": "not-delivered"}}

        receipt = self.retained_ready("discard-after-intake")
        self.session.live_assignment = None
        adapter = ProtocolCustodian()
        authorize_cleanup(self.store, self.port, adapter, attempt_id=ATTEMPT,
                          retention_policy_digest=RETENTION)
        self.assertEqual(len(adapter.destroyed_with), 1)
        command = adapter.destroyed_with[0]
        self.assertEqual(command["runtime_attempt_id"], ATTEMPT)
        self.assertEqual(command["assignment_ref"]["participant"], WHO)
        self.assertEqual(command["runtime_id"], "runtime-1")
        self.assertEqual(command["intake_receipt_digest"],
                         receipt["receipt_digest"])
        self.assertEqual(command["retention_policy_digest"], RETENTION)
        self.assertIn("operation", command)

    def test_a_self_consistent_receipt_edit_is_not_journal_evidence(self):
        """A row and the digest stored beside it can be edited together. The
        committed collection/intake operation is the independent evidence that
        must authenticate the reconstructed receipt."""
        receipt, _ = self.intaken()
        forged = {name: value for name, value in receipt.items()
                  if name != "receipt_digest"}
        forged["why"] = "forged after the committed intake"
        self.store._connection.execute(
            "UPDATE intakes SET why = ?, receipt_digest = ? WHERE "
            "runtime_attempt_id = ?",
            (forged["why"], digest(forged), ATTEMPT))
        with self.assertRaises(ContractRefusal) as caught:
            intake_receipt_of(self.store, ATTEMPT)
        # `.category`, NOT `.code`. The review wrote `.code == "integrity"`
        # and no refusal can satisfy it: `integrity` is a CATEGORY in the
        # frozen closed pairing and its codes are schema, digest, path,
        # file-type, limit and secret-leak. The build asserts against the
        # combination itself -- `ContractRefusal("integrity", "integrity")`
        # raises "the pairing is closed" -- so the case could never pass
        # whatever was implemented. Corrected to the axis the review's own
        # prose names ("report divergence as integrity rather than a caller
        # collision"), and flagged in the handoff rather than quietly changed.
        self.assertEqual(caught.exception.category, "integrity")

    def test_a_retention_row_edit_cannot_authorize_cleanup(self):
        """Retention is authorization state too. Rewriting its policy and
        disposition without the committed `output.retain` operation must not
        produce a valid destroy authorization."""
        self.retained_ready("retain")
        self.session.live_assignment = None
        self.store._connection.execute(
            "UPDATE retentions SET disposition = ?, "
            "retention_policy_digest = ? WHERE runtime_attempt_id = ?",
            ("discard-after-intake", OTHER_POLICY, ATTEMPT))
        adapter = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            authorize_cleanup(self.store, self.port, adapter,
                              attempt_id=ATTEMPT,
                              retention_policy_digest=OTHER_POLICY)
        # `.category` for the same reason as the receipt case above: the
        # frozen pairing has no `integrity` CODE, and this assertion as
        # written was unsatisfiable.
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(adapter.destroyed_with, [])

    def test_a_retention_cannot_borrow_another_attempts_committed_act(self):
        """Artifact ids, policy and disposition are not globally unique. A row
        must agree with the attempt named by its committed retain result too."""
        self.retained_ready("retain")
        foreign_id = "attempt-elsewhere"
        foreign_attempt = {**self.attempt_row(),
                           "runtime_attempt_id": foreign_id}
        operation = retain_operation(
            foreign_attempt, RETENTION, ["artifact-1"], "retain")
        expect = dict(self.session.claim_answer["assignment"])
        signature = manager_signature(
            "output.retain",
            {"attempt_id": foreign_id, "expect": expect,
             "artifact_ids": ["artifact-1"], "disposition": "retain",
             "retention_policy_digest": RETENTION})
        self.store.transact(
            operation["operation_id"], "output.retain", signature,
            lambda _connection: documents.retention_decided(
                attempt_id=foreign_id, artifact_ids=["artifact-1"],
                disposition="retain", retention_policy_digest=RETENTION,
                operation=dict(operation)))
        self.store._connection.execute(
            "UPDATE retentions SET retain_operation_id = ? WHERE "
            "runtime_attempt_id = ?",
            (operation["operation_id"], ATTEMPT))
        with self.assertRaises(ContractRefusal) as caught:
            retentions_of(self.store, ATTEMPT)
        self.assertEqual(caught.exception.category, "integrity")


class TheOrdinaryEndingSurvivesInterruptionAtEveryDirectoryAct(IntakeCase):
    """W43975's public-ending matrix, for the receipt-authorized ending.

    The abandonment sibling and the receipt boundary are covered in
    `test_attempts` and `test_custody`. This is the ordinary ending, which is
    the only one that REMOVES -- so it carries the two cases the others cannot:
    a crash between the removal and the terminal commit, and the retry that
    follows it once the roots are already gone.
    """

    class Interrupted(Custodian):

        def __init__(self, fail_on=None, **overrides):
            super().__init__(**overrides)
            self.fail_on = fail_on

        def normalize_directory(self, store, *, assignment_id, which):
            if which == self.fail_on:
                self.normalized.append((assignment_id, which))
                raise RuntimeError(f"the helper died over {which}")
            return super().normalize_directory(
                store, assignment_id=assignment_id, which=which)

    def ready(self):
        self.retained_ready("discard-after-intake")
        self.ended()

    def settle(self, adapter):
        return authorize_cleanup(self.store, self.port, adapter,
                                 attempt_id=ATTEMPT,
                                 retention_policy_digest=RETENTION)

    def test_the_ending_binds_both_receipts_and_replays_them(self):
        self.ready()
        adapter = self.Interrupted()

        answered = self.settle(adapter)

        self.assertEqual([one for _a, one in adapter.normalized],
                         ["result", "workspace"])
        bound = answered["directory_custody"]
        self.assertEqual(sorted(bound), ["result", "workspace"])
        for which in ("result", "workspace"):
            self.assertEqual(bound[which]["attempt_id"], ATTEMPT)
            self.assertEqual(bound[which]["verb"], "normalize")

        replay = self.settle(adapter)

        self.assertEqual(replay, answered)
        self.assertEqual(len([one for _a, one in adapter.normalized
                              if one == "result"]), 1,
                         "a replayed ending normalized a root again")

    def test_an_interrupted_normalization_commits_no_ending_and_resumes(self):
        self.ready()
        dying = self.Interrupted(fail_on="workspace")

        with self.assertRaises(RuntimeError):
            self.settle(dying)

        self.assertEqual(self.attempt_row()["cleanup"], "pending",
                         "an ending was claimed on an unfinished custody")

        dying.fail_on = None
        answered = self.settle(dying)

        self.assertEqual(answered["cleanup"], "complete")
        self.assertEqual([one for _a, one in dying.normalized],
                         ["result", "workspace", "workspace"],
                         "the resumed ending renormalized a settled root")

    def test_a_changed_custodian_collides_rather_than_settling(self):
        """A helper swapped between the two acts is a different act over the
        same subject, and the ending must not settle under the first's
        identity."""
        self.ready()
        dying = self.Interrupted(fail_on="workspace")
        with self.assertRaises(RuntimeError):
            self.settle(dying)

        other = self.Interrupted()
        other.custodian_image_digest = "sha256:" + "e" * 64

        with self.assertRaises(ContractRefusal) as caught:
            self.settle(other)

        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual(self.attempt_row()["cleanup"], "pending")

    def test_a_crash_between_the_removal_and_the_commit_retries_clean(self):
        """THE CASE ONLY THIS ENDING HAS.

        The removal happens inside the terminal transaction, so a crash after
        it and before the commit leaves the roots GONE and the cleanup axis
        pending. The retry must then complete over an attempt whose execution
        roots no longer exist -- which is exactly what `discard_execution_roots`
        answering an absent home with `()` is for.
        """
        from baton_v12.worker_manager.workspaces import (
            discard_execution_roots)

        self.ready()
        adapter = self.Interrupted()
        # THE STATE A CRASH BETWEEN THE REMOVAL AND THE COMMIT LEAVES, modelled
        # rather than faked. The removal is a filesystem act inside the
        # terminal transaction: the transaction's writes roll back and the
        # removal does not, so what survives is roots that are GONE beside a
        # cleanup axis still `pending`. Driving `store.transact` to run its
        # action and then raise would have committed the axis moves outside
        # the journal, which is a state no crash produces.
        discard_execution_roots(self.storage, ATTEMPT)
        self.assertEqual(self.attempt_row()["cleanup"], "pending")

        home = os.path.join(self.storage, ATTEMPT)
        for name in ("inputs", "workspace"):
            self.assertFalse(os.path.exists(os.path.join(home, name)),
                             f"the {name} root survived the removal")

        answered = self.settle(adapter)

        self.assertEqual(answered["cleanup"], "complete")
        self.assertEqual(sorted(answered["directory_custody"]),
                         ["result", "workspace"])

    def test_retry_after_removal_replays_receipts_without_absent_root_access(
            self):
        """The real crash state already has both custody receipts.

        Ordinary removal is ordered after `_adopted_custody`, so a crash after
        removal and before the outer commit cannot leave unjournalled custody.
        The retry must replay both receipts and must not ask an adapter to
        normalize roots that are now absent.
        """
        from baton_v12.worker_manager import custody
        from baton_v12.worker_manager.workspaces import (
            discard_execution_roots)

        self.ready()
        adapter = self.Interrupted()
        for which in ("result", "workspace"):
            custody.normalize_directory(
                self.store, adapter, assignment_id=ATTEMPT, which=which)
        self.assertEqual([one for _a, one in adapter.normalized],
                         ["result", "workspace"])
        adapter.normalized.clear()
        discard_execution_roots(self.storage, ATTEMPT)

        answered = self.settle(adapter)

        self.assertEqual(adapter.normalized, [],
                         "retry tried to normalize an already removed root")
        self.assertEqual(answered["cleanup"], "complete")
        self.assertEqual(sorted(answered["directory_custody"]),
                         ["result", "workspace"])

    def test_a_deployment_without_the_seam_destroys_nothing(self):
        self.ready()

        class Seamless(Custodian):
            normalize_directory = None

        adapter = Seamless()

        with self.assertRaises(ContractRefusal):
            self.settle(adapter)

        self.assertEqual(adapter.destroyed_with, [],
                         "the runtime was destroyed before the missing seam "
                         "was discovered")
        self.assertEqual(self.attempt_row()["cleanup"], "pending")


# -- W119548: discharging the gate the fence installed ------------------------


class TheQuiescenceGateIsDischargedFromTheCommittedCleanup(IntakeCase):
    """W119548: the missing half of the ordinary ending, driven end to end.

    THE MEASURED GAP. A fence ends the assignment and installs
    `runtime-quiescence:<generation>` in one transaction, because ending an
    assignment is not evidence that the container is gone. Only a positive
    observation of the exact runtime is, and `authorize_cleanup` makes exactly
    that observation -- and nothing carried it across, so a Work whose every
    local ending had settled stayed blocked with no accepted act able to move
    it. The composed one-Job lifecycle stopped there; the executable
    reproduction is retained in W119114's `evidence/implementation-119398/`.

    WHAT THESE CASES DRIVE. The real `authorize_cleanup`, the real journal, the
    real derived identities and the port's real crossing. The AUTHORITY is the
    shared fake session, which models exactly its two rules that matter here:
    the gate token must be the one actually holding the Work, and an operation
    identity that already committed replays its recorded answer.
    """

    def setUp(self):
        super().setUp()
        # W124782: the concrete Authority returns the evidence kind. Keep this
        # bounded correction in the discharge fixture, not the shared fake.
        self.session.discharge_answer["kind"] = "runtime-absent"

    def settled(self, **endings):
        """One ordinary cleanup, committed the way every other case does."""
        self.retained_ready("discard-after-intake")
        self.ended()
        return authorize_cleanup(
            self.store, self.port,
            Custodian(destroyed={"state": "absent",
                                 "why": "the engine answered that this exact "
                                        "identity does not exist",
                                 "credentials":
                                     {"lifecycle_state": "not-delivered"},
                                 "launch":
                                     {"lifecycle_state": "not-delivered"},
                                 **endings}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)

    def gated(self, generation=1):
        """The Work as the authority leaves it after a fence."""
        self.session._work = dict(self.session._work, phase="block",
                                  gate=f"runtime-quiescence:{generation}")

    def discharge(self, **overrides):
        operands = {"attempt_id": ATTEMPT,
                    "retention_policy_digest": RETENTION}
        operands.update(overrides)
        return discharge_quiescence_gate(self.store, self.port, **operands)

    def refused(self, **overrides):
        with self.assertRaises(ContractRefusal) as caught:
            self.discharge(**overrides)
        return caught.exception

    def satisfied(self):
        return [one for one in self.session.calls if one[0] == "satisfy_gate"]

    # -- the act ------------------------------------------------------------

    def test_a_settled_cleanup_discharges_the_gate_and_frees_the_work(self):
        self.settled()
        self.gated()
        answered = self.discharge()
        self.assertEqual(answered["gate"], "runtime-quiescence:1")
        self.assertEqual(answered["phase"], "queued")
        self.assertEqual(answered["attempt_id"], ATTEMPT)
        self.assertEqual(answered["runtime_id"],
                         self.attempt_row()["runtime_id"])
        self.assertEqual(answered["cleanup"], "complete")
        # THE WORK IS ACTUALLY UNGATED, read from the authority rather than
        # from what this manager asked for.
        self.assertIsNone(self.session._work["gate"])
        self.assertEqual(self.session._work["phase"], "queued")

    def test_the_evidence_is_positive_absence_naming_the_exact_runtime(self):
        """The one thing the authority takes for this gate, and it is the
        attempt's own attached identity rather than anything a caller offered
        or the settlement document happened to carry."""
        self.settled()
        self.gated()
        self.discharge()
        [evidence] = self.session.gate_evidence
        self.assertEqual(
            evidence,
            {"kind": "runtime-absent",
             "runtime": self.attempt_row()["runtime_id"]})

    def test_the_gate_token_is_derived_from_the_attempts_own_generation(self):
        self.settled()
        self.gated()
        self.discharge()
        [(_act, operands)] = self.satisfied()
        self.assertEqual(operands["gate"], "runtime-quiescence:1")
        self.assertEqual(operands["work_id"], JOB)

    def test_the_caller_supplies_no_absence_runtime_gate_or_assignment(self):
        """Its two operands are the attempt and the policy that selects the
        cleanup proof; everything the authority acts on is derived here."""
        import inspect

        signature = inspect.signature(discharge_quiescence_gate)
        self.assertEqual(
            [name for name in signature.parameters
             if signature.parameters[name].kind.name == "KEYWORD_ONLY"],
            ["attempt_id", "retention_policy_digest"])

    # -- effectively once, and the crash window ------------------------------

    def test_a_second_call_replays_and_asks_the_authority_nothing_again(self):
        self.settled()
        self.gated()
        first = self.discharge()
        self.assertEqual(len(self.satisfied()), 1)
        for _ in range(2):
            self.assertEqual(self.discharge(), first)
        self.assertEqual(len(self.satisfied()), 1)
        self.assertEqual(len(self.session.gate_evidence), 1)

    def test_the_replay_precedes_every_check_on_mutable_work_state(self):
        """A remote commit whose local receipt was lost must reproduce its
        answer EVEN AFTER THE WORK HAS MOVED. Checking today's gate before
        recognising that replay is what would strand successful work."""
        self.settled()
        self.gated()
        first = self.discharge()
        # The Work moves on: claimed again, fenced again, gated at a LATER
        # generation. None of it is this discharge's business any more.
        self.session._work = dict(self.session._work, phase="block",
                                  gate="runtime-quiescence:9")
        self.assertEqual(self.discharge(), first)
        self.assertEqual(len(self.satisfied()), 1)
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:9")

    def test_a_lost_local_receipt_is_finished_without_a_second_remote_act(
            self):
        """THE CRASH WINDOW THIS DESIGN IS WRITTEN AROUND. The remote act
        commits first and the local journal second, so a death between them
        leaves the authority holding a discharge this store has no record of.
        The next call re-derives the SAME operation identity, the authority
        replays its own answer rather than acting twice, and the local receipt
        is written at last."""
        self.settled()
        self.gated()
        with patch.object(self.store, "transact",
                          side_effect=ContractRefusal(
                              "unavailable", "transport",
                              "the injected interruption after the remote "
                              "commit")):
            with self.assertRaises(ContractRefusal):
                self.discharge()
        # THE AUTHORITY COMMITTED and this store did not.
        self.assertEqual(len(self.satisfied()), 1)
        self.assertIsNone(self.session._work["gate"])
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

        answered = self.discharge()
        self.assertEqual(answered["phase"], "queued")
        # ONE REMOTE ACT EVER, replayed rather than repeated, and one piece of
        # evidence journalled at the authority.
        self.assertEqual(len(self.satisfied()), 2)
        self.assertEqual(len(self.session.gate_evidence), 1)
        self.assertEqual(gate_discharge_of(self.store, ATTEMPT), answered)

    def test_the_outstanding_obligation_is_discoverable_after_cleanup(self):
        """`authorize_cleanup` commits its terminal axis and its receipt
        together, so a consumer deciding what is owed from that axis alone sees
        nothing outstanding. This is the read that answers the other question,
        and it is why the discharge is not lost at a restart."""
        self.settled()
        self.assertEqual(self.attempt_axis("cleanup"), "complete")
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.gated()
        answered = self.discharge()
        self.assertEqual(gate_discharge_of(self.store, ATTEMPT), answered)

    def test_a_never_activated_attempt_has_no_discharge_to_discover(self):
        from baton_v12.worker_manager import record_attempt

        self.attempt()
        record_attempt(self.store, attempt_id="loose", adapter_name="acp",
                       adapter_digest="sha256:" + "a" * 64,
                       profile_digest=self.attempt_row()["profile_digest"])
        self.assertIsNone(gate_discharge_of(self.store, "loose"))

    # -- the proof it is authorized by ---------------------------------------

    def test_a_cleanup_that_never_committed_authorizes_nothing(self):
        """The mutable axis is not the proof. This attempt's runtime axis is
        set to the terminal value by hand and no `runtime.destroy` was ever
        committed, which is exactly the store edit the committed-result rule
        exists for."""
        self.retained_ready("discard-after-intake")
        self.ended()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="destroyed")
        observe(self.store, attempt_id=ATTEMPT, axis="cleanup",
                value="complete")
        self.gated()
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("committed no such operation", caught.message)
        self.assertEqual(self.satisfied(), [])

    def test_another_retention_policy_selects_a_cleanup_nobody_committed(self):
        """The policy is half the key to the destroy identity, so naming a
        different one selects an operation this manager never committed rather
        than authorizing this act under one it did."""
        self.settled()
        self.gated()
        caught = self.refused(retention_policy_digest=OTHER_POLICY)
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertEqual(self.satisfied(), [])

    def test_an_attempt_with_no_intake_receipt_is_refused_as_that(self):
        self.frozen_attempt()
        self.gated()
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("no intake receipt", caught.message)
        self.assertEqual(self.satisfied(), [])

    def test_a_surviving_runtime_discharges_nothing(self):
        """`failed` is the settled ending of a cleanup whose runtime survived
        its own destroy. It is evidence AGAINST absence, and the gate takes
        positive absence of the exact runtime."""
        settled = self.settled(state="running",
                               why="the engine answered that it is running")
        self.assertEqual(settled["cleanup"], "failed")
        self.gated()
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("POSITIVE absence", caught.message)
        self.assertEqual(self.satisfied(), [])

    def test_a_retained_ending_is_admitted_beside_a_complete_one(self):
        """Both followed positive absence; only the kept material differs, and
        a gate does not care which."""
        self.retained_ready("retain")
        self.ended()
        settled = authorize_cleanup(
            self.store, self.port,
            Custodian(destroyed={"state": "absent",
                                 "why": "the engine answered that this exact "
                                        "identity does not exist",
                                 "credentials":
                                     {"lifecycle_state": "not-delivered"},
                                 "launch":
                                     {"lifecycle_state": "not-delivered"}}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertEqual(settled["cleanup"], "retained")
        self.gated()
        self.assertEqual(self.discharge()["cleanup"], "retained")

    # -- who may perform it --------------------------------------------------

    def test_a_session_acting_for_another_participant_is_refused_first(self):
        from baton_v12.worker_manager import AuthorityPort

        from .test_offers import FakeSession, fake_claim_signature

        self.settled()
        self.gated()
        foreign = AuthorityPort(FakeSession(participant="somebody.else"),
                                fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            discharge_quiescence_gate(self.store, foreign, attempt_id=ATTEMPT,
                                      retention_policy_digest=RETENTION)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertEqual(self.satisfied(), [])

    def test_a_session_that_cannot_reach_the_discharge_says_so(self):
        """Both production deployments in this distribution compose narrower
        session surfaces, so the port names this capability without requiring
        it. A deployment that cannot reach it is told which capability is
        missing rather than faulting on an attribute."""
        from baton_v12.worker_manager import AuthorityPort

        from .test_offers import FakeSession, fake_claim_signature

        self.settled()
        self.gated()
        narrow = FakeSession()
        # THE SAME AUTHORITY AND PARTICIPANT, so what this case measures is the
        # missing capability rather than one of the two bindings proved ahead
        # of it. A fake projecting another authority would refuse earlier and
        # for a different reason, which is a case about `_same_authority`.
        narrow._work = dict(self.session._work)
        del narrow.__class__.satisfy_gate
        try:
            port = AuthorityPort(narrow, fake_claim_signature)
            with self.assertRaises(ContractRefusal) as caught:
                discharge_quiescence_gate(self.store, port, attempt_id=ATTEMPT,
                                          retention_policy_digest=RETENTION)
        finally:
            FakeSession.satisfy_gate = _SATISFY_GATE
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertIn("carries no satisfy_gate", caught.exception.message)

    # -- the stale generation ------------------------------------------------

    def test_old_cleanup_evidence_cannot_discharge_a_newer_gate(self):
        """The attempt composes the token for the generation it was fenced at,
        and the authority compares it for equality against the gate actually
        holding the Work. A newer gate is refused by the owner of that fact."""
        self.settled()
        self.gated(generation=4)
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:4")
        # AND NOTHING WAS JOURNALLED, so the next legitimate discharge is not
        # replaying a refusal.
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    def test_an_ungated_work_is_refused_by_the_authority_and_not_recorded(
            self):
        self.settled()
        caught = self.refused()
        self.assertEqual(caught.category, "refused")
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    # -- the review's counterexamples, as controls ---------------------------
    #
    # W119548 review 2026-09-08T14:27:00Z. Each of the three findings is driven
    # here from the state the reviewer's probe built, so a regression cannot
    # reintroduce one quietly. Every case requires the same three things: a
    # typed refusal, the gate still closed, and NO discharge receipt -- because
    # a journalled false completion is what would defeat consumer recovery.

    def unchanged_after_refusal(self, caught):
        """A refusal left the authority and this store exactly as they were."""
        self.assertIsInstance(caught, ContractRefusal)
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
        self.assertEqual(self.session.gate_evidence, [])
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    def test_a_runtime_changed_after_cleanup_cannot_be_certified_absent(self):
        """[P1] `destroy_operation` splits its binding: the identity covers the
        attempt, assignment, receipt and policy, and the SIGNATURE is the half
        that covers the runtime. Comparing only the identity let an edited
        `runtime_id` select the committed act and then certify a runtime this
        manager never observed absent."""
        self.settled()
        self.gated()
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("runtime-never-observed-absent", ATTEMPT))
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("signature", caught.message)
        self.assertEqual(self.satisfied(), [])
        self.unchanged_after_refusal(caught)

    def test_an_attempt_whose_runtime_is_gone_from_the_row_refuses(self):
        """The null half of the same binding. A cleanup cannot reach positive
        absence without a runtime, so a row that no longer names one disagrees
        with its own committed proof."""
        self.settled()
        self.gated()
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = NULL "
            "WHERE runtime_attempt_id = ?",
            (ATTEMPT,))
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertEqual(self.satisfied(), [])
        self.unchanged_after_refusal(caught)

    def spoil_cleanup_result(self, operation):
        """Rewrite what the committed cleanup RECORDED, leaving its signature.

        The journal's signature still replays, so this is precisely the store
        edit the committed-result rule exists for: the row is self-consistent
        by the replay's own test, and its content is not what this manager
        wrote.
        """
        settled = self.settled()
        record = self.store.operation_record(
            settled["operation"]["operation_id"])
        held = json.loads(self.store._connection.execute(
            "SELECT result FROM operations WHERE operation_id = ?",
            (record["operation_id"],)).fetchone()["result"])
        held["operation"] = operation
        self.store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(held), record["operation_id"]))
        self.gated()

    def test_a_malformed_nested_cleanup_proof_refuses_before_the_authority(
            self):
        for operation in ([], {}, {"operation_id": "runtime.destroy:x"},
                          {"operation_id": "runtime.destroy:x",
                           "signature_digest": "sha256:" + "0" * 64,
                           "surprise": 1}):
            with self.subTest(operation=repr(operation)):
                self.setUp()
                self.spoil_cleanup_result(operation)
                caught = self.refused()
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.assertEqual(self.satisfied(), [])
                self.unchanged_after_refusal(caught)

    # -- what the authority actually answered --------------------------------

    def answering(self, **answer):
        """A session that returns one reply and performs no act at all."""
        self.session.satisfy_gate = lambda operands: dict(answer)

    def test_an_answer_about_another_gate_is_not_this_gates_discharge(self):
        """[P1] The probe's exact reply. Without this the manager journalled a
        discharge for gate 1, `gate_discharge_of` returned it, and the real
        gate stayed closed with no evidence sent -- and the retry then
        replayed that false completion forever."""
        self.settled()
        self.gated()
        self.answering(gate="runtime-quiescence:99", kind=[], phase="block")
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("runtime-quiescence:99", caught.message)
        self.unchanged_after_refusal(caught)

    def test_a_reply_that_does_not_release_the_work_is_not_a_discharge(self):
        self.settled()
        self.gated()
        for phase in ("block", "parked", "", None, 1):
            with self.subTest(phase=repr(phase)):
                self.answering(gate="runtime-quiescence:1",
                               kind="runtime-absent", phase=phase)
                caught = self.refused()
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.unchanged_after_refusal(caught)

    def test_a_reply_whose_kind_is_not_this_gates_kind_refuses(self):
        self.settled()
        self.gated()
        for kind in ([], 1, "", "contract-runtime", "runtime-quiescence"):
            with self.subTest(kind=repr(kind)):
                self.answering(gate="runtime-quiescence:1", kind=kind,
                               phase="queued")
                caught = self.refused()
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.unchanged_after_refusal(caught)

    def test_a_reply_missing_a_member_refuses_at_the_port(self):
        self.settled()
        self.gated()
        for answer in ({}, {"gate": "runtime-quiescence:1"},
                       {"gate": "runtime-quiescence:1", "phase": "queued"}):
            with self.subTest(answer=sorted(answer)):
                self.answering(**answer)
                caught = self.refused()
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.unchanged_after_refusal(caught)

    def test_the_receipt_records_what_the_authority_answered(self):
        """Not what this manager asked for. The two are proved equal at the
        port, so recording the answer is what keeps the receipt a statement
        about what happened."""
        self.settled()
        self.gated()
        answered = self.discharge()
        [(_act, operands)] = self.satisfied()
        self.assertEqual(answered["gate"], operands["gate"])
        self.assertEqual(answered["kind"], "runtime-absent")
        self.assertEqual(answered["phase"], "queued")

    # -- the adopted receipt, on both public exits ---------------------------

    def spoil_receipt(self, **members):
        """Rewrite the journalled discharge, keeping its signature."""
        state = self.discharge()
        held = dict(state, **members)
        self.store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(held), state["operation_id"]))

    def test_a_journalled_receipt_that_is_not_a_discharge_is_refused(self):
        """[P1] Both public exits adopt the receipt. Generic JSON parsing
        establishes that bytes decode and nothing about what they say, and the
        consumer recovery that reads this is exactly who would be misled."""
        for members in ({"kind": "contract-runtime"}, {"kind": "runtime-quiescence"}, {"phase": "block"},
                        {"cleanup": "failed"}, {"runtime_id": None},
                        {"gate": 1}):
            with self.subTest(spoiled=sorted(members)):
                self.setUp()
                self.settled()
                self.gated()
                self.spoil_receipt(**members)
                with self.assertRaises(ContractRefusal) as caught:
                    gate_discharge_of(self.store, ATTEMPT)
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))
                # AND THE REPLAY EXIT REFUSES THE SAME ROW, rather than handing
                # a caller a receipt the read would not stand behind.
                with self.assertRaises(ContractRefusal):
                    self.discharge()

    # -- the receipt is bound to the record it came out of --------------------
    #
    # W119548 review 2026-09-08T14:43:50Z [P2]. Checking each field proved
    # every member well-formed and nothing about WHOSE receipt it is. This
    # reader is a consumer's proof that its selected attempt owes no discharge,
    # so a typed receipt about another attempt, gate, operation or runtime is
    # exactly the answer it must not give -- and a raw fault is not a refusal it can retry.

    RECEIPT_COUNTEREXAMPLES = (
        {"assignment": None},
        {"assignment": {}},
        {"assignment": {"work_ref": None, "participant": "baton.claude",
                        "generation": 1}},
        {"attempt_id": "another-attempt"},
        {"gate": "runtime-quiescence:99"},
        {"operation_id": "some-other-operation"},
        {"cleanup_operation_id": "runtime.destroy:another"},
        {"runtime_id": "foreign-runtime"},
    )

    def both_exits_refuse(self, **members):
        """One spoiled journal row, asked of BOTH public exits.

        The operation id and its signature are left untouched, so the row still
        replays by the journal's own test -- which is precisely the persisted
        input this contract exists for.
        """
        self.settled()
        self.gated()
        self.spoil_receipt(**members)
        asked = len(self.satisfied())
        def reading():
            return gate_discharge_of(self.store, ATTEMPT)

        for exit_name, run in (("discovery", reading),
                               ("replay", self.discharge)):
            with self.subTest(exit=exit_name):
                with self.assertRaises(ContractRefusal) as caught:
                    run()
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))
        # AND NO NEW REMOTE ACT WAS MADE on the way to either refusal.
        self.assertEqual(len(self.satisfied()), asked)

    def test_a_receipt_about_something_else_is_refused_by_both_exits(self):
        for members in self.RECEIPT_COUNTEREXAMPLES:
            with self.subTest(spoiled=sorted(members)):
                self.setUp()
                self.both_exits_refuse(**members)

    def spoil_journal(self, column, value):
        """Change the journal ROW itself, leaving the receipt it holds alone."""
        state = self.discharge()
        self.store._connection.execute(
            "UPDATE operations SET " + column + " = ? WHERE operation_id = ?",
            (value, state["operation_id"]))

    def test_a_present_invalid_record_is_never_reported_as_absence(self):
        """W119548 review 2026-09-08T14:53:10Z [P2]. The two exits had each
        written their own presence check and disagreed: replay refused a record
        of the wrong kind and a record whose decoded result is null, while
        discovery answered `None` for both.

        A consumer acts on `None` as outstanding work it may still perform, so
        reporting an integrity failure that way invites a remote act on the
        strength of a record this manager could not read. One reader now decides
        it for both, and only a genuinely absent operation answers `None`.
        """
        for column, value in (("result", "null"),
                              ("kind", "unrelated.operation"),
                              ("result", "[]")):
            with self.subTest(column=column, value=value):
                self.setUp()
                self.settled()
                self.gated()
                self.spoil_journal(column, value)
                asked = len(self.satisfied())

                def reading():
                    return gate_discharge_of(self.store, ATTEMPT)

                for exit_name, run in (("discovery", reading),
                                       ("replay", self.discharge)):
                    with self.subTest(exit=exit_name):
                        with self.assertRaises(ContractRefusal) as caught:
                            run()
                        self.assertEqual((caught.exception.category,
                                          caught.exception.code),
                                         ("integrity", "schema"))
                self.assertEqual(len(self.satisfied()), asked)

    def test_only_a_genuinely_absent_operation_answers_absence(self):
        """The other half, kept explicit so the correction cannot be read as
        "refuse more". An attempt that was never assigned and one whose
        discharge was never committed both still answer `None`."""
        from baton_v12.worker_manager import record_attempt

        self.settled()
        record_attempt(self.store, attempt_id="loose", adapter_name="acp",
                       adapter_digest="sha256:" + "a" * 64,
                       profile_digest=self.attempt_row()["profile_digest"])
        # NEVER ASSIGNED, so there is no identity to look one up by.
        self.assertIsNone(gate_discharge_of(self.store, "loose"))
        # ASSIGNED AND CLEANED UP, and the discharge simply has not run.
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        # ...and the act itself treats that absence as work still to do rather
        # than as a refusal.
        self.gated()
        self.assertIsNotNone(self.discharge())

    def test_a_null_assignment_refuses_rather_than_faulting(self):
        """`documents.assignment` takes keywords and `**None` is a TypeError.
        A raw exception at a persisted-input boundary bypasses the portable
        refusal and retry path every other reader here uses."""
        self.settled()
        self.gated()
        self.spoil_receipt(assignment=None)
        for run in (lambda: gate_discharge_of(self.store, ATTEMPT),
                    self.discharge):
            with self.assertRaises(ContractRefusal) as caught:
                run()
            self.assertEqual(caught.exception.category, "integrity")

    def test_the_gate_is_derived_from_the_receipts_own_assignment(self):
        """A generation-1 assignment carrying gate 99 is not a document about
        one discharge, however well formed each half is alone."""
        self.settled()
        self.gated()
        self.spoil_receipt(gate="runtime-quiescence:99")
        with self.assertRaises(ContractRefusal) as caught:
            gate_discharge_of(self.store, ATTEMPT)
        self.assertIn("runtime-quiescence:99", caught.exception.message)
        self.assertIn("runtime-quiescence:1", caught.exception.message)

    def test_changing_any_signed_operand_breaks_the_recorded_signature(self):
        """The one comparison that binds the five together.

        `discharge_quiescence_gate` signs the attempt, the fixed assignment,
        the gate, the runtime and the cleanup operation into one signature and the
        store recorded it. Recomposing that signature from the receipt's own
        operands is what makes five independent field checks into one
        relationship -- and a member changed on its own cannot reproduce it.
        """
        self.settled()
        self.gated()
        self.spoil_receipt(runtime_id="foreign-runtime")
        with self.assertRaises(ContractRefusal) as caught:
            gate_discharge_of(self.store, ATTEMPT)
        self.assertIn("ONE signed relationship", caught.exception.message)

    def test_absence_stays_a_different_answer_from_a_malformed_receipt(self):
        """"No discharge is recorded" is what a consumer acts on; "one is
        recorded and this manager cannot own it" is an operator's problem. The
        read must not report the second as the first."""
        self.settled()
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.gated()
        self.discharge()
        self.assertIsNotNone(gate_discharge_of(self.store, ATTEMPT))
        self.spoil_receipt(attempt_id="another-attempt")
        with self.assertRaises(ContractRefusal):
            gate_discharge_of(self.store, ATTEMPT)

    def test_a_valid_receipt_still_replays_after_the_work_has_moved(self):
        """The binding must use the receipt's own durable context, not today's
        rows. A correct receipt keeps replaying after the Work is claimed and
        fenced again, and after the mutable runtime row has moved on."""
        self.settled()
        self.gated()
        answered = self.discharge()
        self.session._work = dict(self.session._work, phase="block",
                                  gate="runtime-quiescence:9")
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("runtime-replaced-since", ATTEMPT))
        self.assertEqual(self.discharge(), answered)
        self.assertEqual(gate_discharge_of(self.store, ATTEMPT), answered)
        self.assertEqual(len(self.satisfied()), 1)
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:9")

    # -- the authority binding, not just the participant ---------------------

    def test_a_session_on_another_authority_never_reaches_the_act(self):
        """[P2] The probe's third scenario: same participant, same Work
        selector, same generation, different authority. A four-part assignment
        is not three quarters of one, and this crossing was reading one."""
        self.settled()
        self.gated()
        self.session._work = dict(self.session._work, authority_uuid="9" * 32)
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "capability"))
        self.assertEqual(self.satisfied(), [])
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    def test_a_session_projecting_no_such_work_refuses(self):
        self.settled()
        self.gated()
        self.session._work = None
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertEqual(self.satisfied(), [])

    def interrupted_after_the_remote_commit(self):
        """The crash window: the authority committed, this store did not."""
        self.settled()
        self.gated()
        with patch.object(self.store, "transact",
                          side_effect=ContractRefusal(
                              "unavailable", "transport",
                              "the injected interruption after the remote "
                              "commit")):
            with self.assertRaises(ContractRefusal):
                self.discharge()
        self.assertEqual(len(self.satisfied()), 1)
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    def test_a_lost_receipt_is_finished_after_the_work_has_moved_on(self):
        """The review's rule, driven: a remote commit whose local receipt was
        lost must finish EVEN AFTER the Work moved. Today's gate and phase are
        not consulted on the way there, so a Work claimed and fenced again at a
        later generation does not strand the earlier act."""
        self.interrupted_after_the_remote_commit()
        self.session._work = dict(self.session._work, phase="block",
                                  gate="runtime-quiescence:9")
        answered = self.discharge()
        self.assertEqual(answered["phase"], "queued")
        self.assertEqual(answered["gate"], "runtime-quiescence:1")
        self.assertEqual(gate_discharge_of(self.store, ATTEMPT), answered)
        # ONE ACT AT THE AUTHORITY, replayed rather than repeated, and the
        # LATER gate is untouched: this discharge was never about it.
        self.assertEqual(len(self.session.gate_evidence), 1)
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:9")

    def test_a_lost_receipt_is_not_finished_through_a_foreign_authority(self):
        """The other side of that rule, and the distinction is the point.

        What may not gate a replay is today's Work STATE. The authority binding
        is not that: finishing a lost receipt means making the remote call
        again, and a session speaking for another authority may not make it.
        The obligation stays outstanding and discoverable for a correctly bound
        session rather than being completed by the wrong one.
        """
        self.interrupted_after_the_remote_commit()
        self.session._work = dict(self.session._work,
                                  authority_uuid="9" * 32)
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "capability"))
        self.assertEqual(len(self.satisfied()), 1)
        self.assertEqual(len(self.session.gate_evidence), 1)
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    # -- what it leaves alone ------------------------------------------------

    def test_ordinary_cleanup_keeps_its_own_api_and_authority_effect(self):
        """The discharge is a separate act. Cleanup neither performs it nor
        gains an operand for it, and its own ending is unchanged."""
        import inspect

        settled = self.settled()
        self.assertEqual(settled["cleanup"], "complete")
        self.assertEqual(self.attempt_axis("cleanup"), "complete")
        # Cleanup asked the authority nothing about a gate.
        self.assertEqual(self.satisfied(), [])
        self.assertEqual(
            sorted(one for one in
                   inspect.signature(authorize_cleanup).parameters),
            ["adapter", "attempt_id", "port", "retention_policy_digest",
             "store"])

    def test_the_discharge_writes_no_manager_axis(self):
        self.settled()
        self.gated()
        before = dict(self.attempt_row())
        self.discharge()
        self.assertEqual(dict(self.attempt_row()), before)

    def test_a_malformed_operand_is_refused_before_anything_is_asked(self):
        self.settled()
        self.gated()
        for operands in ({"attempt_id": ""}, {"attempt_id": []},
                         {"retention_policy_digest": ""},
                         {"retention_policy_digest": 1}):
            with self.subTest(operands=operands):
                caught = self.refused(**operands)
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
        self.assertEqual(self.satisfied(), [])


class ConcreteAuthorityDischargeReceipts(IntakeCase):
    """W124782: concrete remote acts and local receipts over disposable stores.

    Preparation reuses the manager fixture; the discharge and every Authority
    claim, fence, evidence read and operation replay below are real.
    """

    settled = TheQuiescenceGateIsDischargedFromTheCommittedCleanup.settled
    discharge = TheQuiescenceGateIsDischargedFromTheCommittedCleanup.discharge

    def setUp(self):
        from baton_v12.authority import Authority, V12

        super().setUp()
        self.authority_path = os.path.join(self._root.name, "authority.sqlite3")
        self.authority = Authority.create(self.authority_path, authority_uuid=AUTHORITY, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.authority.create_work(JOB, "impl", contract=V12, operation_id="create-discharge-work")
        self.authority.add_route_handler("impl", WHO)
        self.concrete = self.authority.session(WHO)
        self.assignment = self.concrete.claim({"work_id": JOB, "operation_id": "claim-original"})["assignment"]
        self.remote_calls = []
        self.reply_kind = None

    def connected(self, session):
        from baton_v12.authority.identity import claim_signature
        from baton_v12.worker_manager import AuthorityPort
        from tools.single_worker import _AuthoritySession

        owner = self
        wrapper = _AuthoritySession(session)

        class Recording:
            def __getattr__(self, name):
                return getattr(wrapper, name)

            def satisfy_gate(self, operands):
                owner.remote_calls.append(copy.deepcopy(operands))
                answer = wrapper.satisfy_gate(operands)
                if owner.reply_kind is not None:
                    return dict(answer, kind=owner.reply_kind)
                return answer

        self.port = AuthorityPort(Recording(), claim_signature)

    def ready(self, **endings):
        self.cleanup_receipt = self.settled(**endings)
        self.concrete.cancel({"expect": self.assignment, "operation_id": "fence-original", "reason": "original runtime ended"})
        self.connected(self.concrete)
        self.assertEqual(self.concrete.project_work(JOB)["gate"]["token"], "runtime-quiescence:1")
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    def reopened(self):
        from baton_v12.authority import Authority

        self.store.close()
        self.authority.dispose()
        self.store = ControlStore.open(self.path, incarnation="manager-reopened", clock=lambda: NOW)
        self.addCleanup(self.store.close)
        self.authority = Authority.open(self.authority_path, expected_authority_uuid=AUTHORITY, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.concrete = self.authority.session(WHO)
        self.connected(self.concrete)

    def moved(self):
        later = self.concrete.claim({"work_id": JOB, "operation_id": "claim-later"})["assignment"]
        self.assertEqual(later["generation"], self.assignment["generation"] + 1)
        self.concrete.cancel({"expect": later, "operation_id": "fence-later", "reason": "later runtime ended"})
        return self.concrete.project_work(JOB)

    def assert_receipt(self, receipt):
        self.assertEqual(receipt, {
            "attempt_id": ATTEMPT, "assignment": self.assignment,
            "gate": "runtime-quiescence:1", "kind": "runtime-absent", "phase": "queued",
            "runtime_id": self.attempt_row()["runtime_id"], "cleanup": "complete",
            "cleanup_operation_id": self.cleanup_receipt["operation"]["operation_id"],
            "operation_id": self.remote_calls[0]["operation_id"],
        })
        self.assertEqual(gate_discharge_of(self.store, ATTEMPT), receipt)
        evidence = self.concrete.gate_evidence(JOB)
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["evidence"], {"kind": "runtime-absent", "runtime": receipt["runtime_id"]})

    def test_concrete_answer_commits_and_survives_reopening_both_owners(self):
        self.ready()
        receipt = self.discharge()
        self.assert_receipt(receipt)
        self.assertIsNone(self.concrete.project_work(JOB)["gate"])
        self.reopened()
        later = self.moved()
        self.assertEqual(self.discharge(), receipt)
        self.assert_receipt(receipt)
        self.assertEqual(len(self.remote_calls), 1)
        self.assertEqual(self.concrete.project_work(JOB), later)

    def test_remote_success_local_loss_replays_after_later_movement_and_reopening(self):
        self.ready()
        interruption = ContractRefusal("unavailable", "transport", "lost local receipt write")
        with patch.object(self.store, "transact", side_effect=interruption):
            with self.assertRaises(ContractRefusal) as caught:
                self.discharge()
        self.assertIs(caught.exception, interruption)
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.assertIsNone(self.concrete.project_work(JOB)["gate"])
        original_operands = copy.deepcopy(self.remote_calls[0])
        later = self.moved()
        self.reopened()
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        receipt = self.discharge()
        self.assert_receipt(receipt)
        self.assertEqual(self.remote_calls, [original_operands, original_operands])
        self.assertEqual(self.concrete.project_work(JOB), later)
        self.reopened()
        self.assertEqual(self.discharge(), receipt)
        self.assert_receipt(receipt)
        self.assertEqual(len(self.remote_calls), 2)

    def test_a_gate_kind_reply_cannot_be_committed_as_absence_evidence(self):
        self.ready()
        self.reply_kind = "runtime-quiescence"
        with self.assertRaises(ContractRefusal) as caught:
            self.discharge()
        self.assertEqual((caught.exception.category, caught.exception.code), ("integrity", "schema"))
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.assertIsNone(self.concrete.project_work(JOB)["gate"])
        self.reply_kind = None
        self.assert_receipt(self.discharge())
        self.assertEqual(self.remote_calls[0], self.remote_calls[1])

    def test_original_cleanup_cannot_discharge_a_later_generation(self):
        from baton_v12.authority import Refusal

        self.ready()
        self.concrete.satisfy_gate({"work_id": JOB, "operation_id": "separate-discharge", "gate": "runtime-quiescence:1",
                                   "evidence": {"kind": "runtime-absent", "runtime": self.attempt_row()["runtime_id"]}})
        later = self.moved()
        evidence = self.concrete.gate_evidence(JOB)
        with self.assertRaises(Refusal):
            self.discharge()
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.assertEqual(self.concrete.project_work(JOB), later)
        self.assertEqual(self.concrete.gate_evidence(JOB), evidence)

    def test_another_concrete_authority_cannot_commit_this_receipt(self):
        from baton_v12.authority import Authority, V12

        self.ready()
        foreign = Authority.create(os.path.join(self._root.name, "foreign.sqlite3"), authority_uuid=AUTHORITY[:8] + "f" * 24, clock=lambda: NOW)
        self.addCleanup(foreign.dispose)
        foreign.create_work(JOB, "impl", contract=V12, operation_id="create-foreign-work")
        foreign.add_route_handler("impl", WHO)
        session = foreign.session(WHO)
        self.connected(session)
        with self.assertRaises(ContractRefusal) as caught:
            self.discharge()
        self.assertEqual((caught.exception.category, caught.exception.code), ("refused", "capability"))
        self.assertEqual(self.remote_calls, [])
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.assertEqual(self.concrete.project_work(JOB)["gate"]["token"], "runtime-quiescence:1")
        self.assertEqual(self.concrete.gate_evidence(JOB), [])
        self.assertEqual(session.gate_evidence(JOB), [])

    def test_an_unreachable_runtime_supplies_no_discharge_proof(self):
        self.ready(state="uncertain", why="runtime engine is unreachable")
        with self.assertRaises(ContractRefusal) as caught:
            self.discharge()
        self.assertEqual((caught.exception.category, caught.exception.code), ("integrity", "schema"))
        self.assertIn("committed no such operation", caught.exception.message)
        self.assertEqual(self.attempt_axis("cleanup"), "pending")
        self.assertEqual(self.remote_calls, [])
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))
        self.assertEqual(self.concrete.project_work(JOB)["gate"]["token"], "runtime-quiescence:1")
        self.assertEqual(self.concrete.gate_evidence(JOB), [])


# -- W120762: reading the committed cleanup, without acting -------------------
#
# `work/records/2026/09/finding-v12-committed-cleanup-reader/`.
#
# WHAT `cleanup_of` IS FOR. A consumer recovering a composed ending had two
# ways to ask whether this manager finished with the runtime and both were
# wrong: the mutable `cleanup` column, which an edit reaches, and
# `authorize_cleanup`, which is a serving act that reads the live assignment
# from the Authority when it finds no committed destroy. These cases drive the
# read half over the same real retain and discard endings the suite above
# settles, then over a REOPENED store, and then over each way the evidence can
# fail to be this attempt's.


class TheCommittedCleanupIsReadableWithoutActing(IntakeCase):

    def settled(self, disposition="retain", **kwargs):
        """One real ordinary cleanup, through the ordinary serving act."""
        self.retained_ready(disposition)
        self.ended()
        return authorize_cleanup(self.store, self.port, Custodian(**kwargs),
                                 attempt_id=ATTEMPT,
                                 retention_policy_digest=RETENTION)

    def read(self, **changed):
        operands = {"attempt_id": ATTEMPT,
                    "retention_policy_digest": RETENTION}
        operands.update(changed)
        return cleanup_of(self.store, **operands)

    def reopened(self):
        """A handle that performed none of it."""
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation="manager-2",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        return self.store

    @contextlib.contextmanager
    def no_act(self):
        """Nothing this reader does may reach the Authority or write."""
        calls = copy.deepcopy(self.session.calls)
        changes = self.store._connection.total_changes
        yield
        self.assertEqual(self.session.calls, calls)
        self.assertEqual(self.store._connection.total_changes, changes)

    @contextlib.contextmanager
    def damaged(self, statement, values=()):
        self.store._connection.execute("SAVEPOINT damaged")
        try:
            self.store._connection.execute(statement, values)
            yield
        finally:
            self.store._connection.execute("ROLLBACK TO damaged")
            self.store._connection.execute("RELEASE damaged")

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception

    # -- what it answers -----------------------------------------------------

    def test_it_takes_no_port_and_no_adapter(self):
        """The structural half of "performs no external act".

        A reader that accepted either could reach one; this one has nowhere to
        put a session or a runtime.
        """
        self.assertEqual(list(inspect.signature(cleanup_of).parameters),
                         ["store", "attempt_id", "retention_policy_digest"])

    def test_a_retained_ending_reads_back_exactly_as_it_settled(self):
        settled = self.settled("retain")
        with self.no_act():
            self.assertEqual(self.read(), settled)
        self.assertEqual(settled["cleanup"], "retained")
        self.assertEqual(settled["kept"], ["artifact-1"])

    def test_a_discarded_ending_reads_back_exactly_as_it_settled(self):
        """The kept-material comparison, which is where a discard used to fail.

        `discard-after-intake` is a decision that deliberately keeps nothing,
        so a reader comparing `kept` against every retention decision reports
        an honest discard as a store disagreeing with itself.
        """
        settled = self.settled("discard-after-intake")
        with self.no_act():
            self.assertEqual(self.read(), settled)
        self.assertEqual(settled["cleanup"], "complete")
        self.assertEqual(settled["kept"], [])
        self.assertTrue(retentions_of(self.store, ATTEMPT))

    def test_a_reopened_manager_reads_the_same_answer(self):
        settled = self.settled("retain")
        self.reopened()
        with self.no_act():
            self.assertEqual(self.read(), settled)
            self.assertEqual(self.read(), settled)

    def test_the_nested_directory_custody_is_the_committed_normalization(self):
        from baton_v12.worker_manager import custody
        settled = self.settled("retain")
        self.reopened()
        held = self.read()
        self.assertEqual(sorted(held["directory_custody"]),
                         ["result", "workspace"])
        for which in ("result", "workspace"):
            self.assertEqual(
                held["directory_custody"][which],
                custody.historical_directory_custody(self.store, ATTEMPT,
                                                     which))
        self.assertEqual(held["directory_custody"],
                         settled["directory_custody"])

    # -- absence, which is not a fault ---------------------------------------

    def test_an_attempt_with_no_cleanup_answers_absence(self):
        self.retained_ready("retain")
        with self.no_act():
            self.assertIsNone(self.read())

    def test_an_attempt_with_no_intake_receipt_answers_absence(self):
        """Half the destroy identity is the receipt digest, so without one
        there is no operation this manager could ever have committed."""
        self.frozen_attempt()
        self.assertIsNone(intake_receipt_of(self.store, ATTEMPT))
        with self.no_act():
            self.assertIsNone(self.read())

    def test_another_policy_selects_an_act_this_manager_never_committed(self):
        self.settled("retain")
        with self.no_act():
            self.assertIsNone(self.read(
                retention_policy_digest=OTHER_POLICY))

    def test_an_unknown_attempt_refuses_rather_than_answering_absence(self):
        self.settled("retain")
        self.refusal(self.read, attempt_id="attempt-nobody-holds")

    # -- present, and not this attempt's -------------------------------------

    def test_a_record_of_another_kind_refuses(self):
        self.settled("retain")
        operation = self.store._connection.execute(
            "SELECT operation_id FROM operations WHERE kind = "
            "'runtime.destroy'").fetchone()[0]
        with self.damaged("UPDATE operations SET kind = 'foreign.destroy' "
                          "WHERE operation_id = ?", (operation,)), \
                self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    def test_a_result_its_own_signature_does_not_name_refuses(self):
        settled = self.settled("retain")
        operation = settled["operation"]["operation_id"]
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(settled, cleanup="failed")), operation)), \
                self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    def test_a_changed_runtime_moves_the_signature_and_refuses(self):
        """`operation_id` binds the attempt, assignment, receipt and policy;
        `signature_digest` binds the runtime. Comparing one and dropping the
        other lets an edited runtime keep a real cleanup's evidence."""
        self.settled("retain")
        with self.damaged("UPDATE attempts SET runtime_id = 'another-runtime' "
                          "WHERE runtime_attempt_id = ?", (ATTEMPT,)), \
                self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    def test_a_receipt_naming_another_attempt_refuses(self):
        settled = self.settled("retain")
        operation = settled["operation"]["operation_id"]
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(settled, attempt_id="another-attempt")),
                 operation)), self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    def test_a_malformed_receipt_refuses(self):
        settled = self.settled("retain")
        operation = settled["operation"]["operation_id"]
        for name, changed in (
                ("no ending", {"cleanup": None}),
                ("an unknown ending", {"cleanup": "tidied"}),
                ("no observed state", {"state": None}),
                ("no account", {"why": None}),
                ("kept is not a list", {"kept": "artifact-1"}),
                ("a kept name that is not an identity", {"kept": [7]}),
                ("no operation", {"operation": None}),
                ("a half operation",
                 {"operation": {"operation_id": operation}})):
            with self.subTest(receipt=name):
                with self.damaged(
                        "UPDATE operations SET result = ? WHERE "
                        "operation_id = ?",
                        (json.dumps(dict(settled, **changed)), operation)), \
                        self.no_act():
                    self.assertIsInstance(self.refusal(self.read),
                                          ContractRefusal)

    def test_an_unknown_receipt_member_refuses(self):
        settled = self.settled("retain")
        operation = settled["operation"]["operation_id"]
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(settled, invented="anything")), operation)), \
                self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    # -- kept material and nested custody ------------------------------------

    def test_every_artifact_must_carry_a_decision_under_this_policy(self):
        """W120762 review 2026-09-08T16-43-59Z [P1]: empty is not evidence.

        Deleting every decision after a real DISCARD left `kept` and the kept
        filter agreeing on two empty lists, so a cleanup that destroyed
        material nobody ruled on read back as `complete`. The proof is the one
        `authorize_cleanup` already required before destroying anything, and
        it is asked of the same owner rather than restated here.
        """
        for name, disposition in (("a discard", "discard-after-intake"),
                                  ("a retain", "retain")):
            with self.subTest(cleanup=name):
                case = self.__class__("run")
                case.setUp()
                try:
                    case.settled(disposition)
                    case.reopened()
                    with case.damaged("DELETE FROM retentions WHERE "
                                      "runtime_attempt_id = ?", (ATTEMPT,)), \
                            case.no_act():
                        caught = case.refusal(case.read)
                    self.assertIn("no retention decision", caught.message)
                finally:
                    case.doCleanups()

    def test_a_decision_made_under_another_policy_refuses(self):
        self.settled("retain")
        self.reopened()
        with self.damaged("UPDATE retentions SET retention_policy_digest = ? "
                          "WHERE runtime_attempt_id = ?",
                          (OTHER_POLICY, ATTEMPT)), self.no_act():
            caught = self.refusal(self.read)
        # THE RETENTION OWNER REFUSES FIRST AND SAYS MORE. A row edited away
        # from the act that decided it fails that owner's own authentication
        # before this reader's policy comparison is reached, which is the
        # stronger of the two answers.
        self.assertIn("the journal did not", caught.message)

    def test_a_kept_set_the_decisions_do_not_name_refuses(self):
        settled = self.settled("retain")
        operation = settled["operation"]["operation_id"]
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(settled, kept=[])), operation)), \
                self.no_act():
            caught = self.refusal(self.read)
        self.assertIn("one set of material", caught.message)

    def test_the_ending_must_be_the_one_those_facts_settle(self):
        """[P1]: an ending is derived from the facts, not recorded beside them.

        A retained receipt holding material read as `complete`, and an honest
        discard read as `retained`, because nothing re-derived `_settle`'s own
        rule.
        """
        for name, disposition, claimed in (
                ("kept material called complete", "retain", "complete"),
                ("a discard called retained", "discard-after-intake",
                 "retained")):
            with self.subTest(ending=name):
                case = self.__class__("run")
                case.setUp()
                try:
                    settled = case.settled(disposition)
                    case.reopened()
                    operation = settled["operation"]["operation_id"]
                    with case.damaged(
                            "UPDATE operations SET result = ? WHERE "
                            "operation_id = ?",
                            (json.dumps(dict(settled, cleanup=claimed)),
                             operation)), case.no_act():
                        caught = case.refusal(case.read)
                    self.assertIn("settle", caught.message)
                finally:
                    case.doCleanups()

    def test_quarantined_custody_settles_retained_and_reads_back(self):
        """The other half of `_settle`'s rule: doubt keeps the bytes too."""
        self.frozen_attempt()
        # QUARANTINE IS EARNED, NOT WRITTEN. Intake quarantines material
        # collected for a generation that has already ended, so the assignment
        # ends before the collection rather than after it.
        self.ended()
        receipt = request_intake(self.store, self.port,
                                 Custodian(self.collection()),
                                 attempt_id=ATTEMPT)
        self.assertEqual(receipt["custody"], "quarantined")
        decide_retention(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="discard-after-intake",
            retention_policy_digest=RETENTION)
        settled = authorize_cleanup(self.store, self.port, Custodian(),
                                    attempt_id=ATTEMPT,
                                    retention_policy_digest=RETENTION)
        self.assertEqual(settled["cleanup"], "retained")
        self.assertEqual(settled["kept"], [])
        self.reopened()
        with self.no_act():
            self.assertEqual(self.read(), settled)

    def test_an_unsettled_or_invented_runtime_state_is_never_an_ending(self):
        """[P1]: `uncertain` is not an ending and `_settle` never commits one.

        `_not_an_ending` returns before any transaction, so a journalled
        receipt carrying it describes a commit this manager cannot have made;
        a state outside the closed destroy vocabulary is not one either.
        """
        settled = self.settled("retain", destroyed={
            "state": "running", "why": "the engine still lists it",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}})
        self.reopened()
        operation = settled["operation"]["operation_id"]
        for state in ("uncertain", "invented"):
            with self.subTest(state=state):
                with self.damaged(
                        "UPDATE operations SET result = ? WHERE "
                        "operation_id = ?",
                        (json.dumps(dict(settled, state=state)), operation)), \
                        self.no_act():
                    self.assertIsInstance(self.refusal(self.read),
                                          ContractRefusal)

    def test_a_signature_this_manager_does_not_derive_refuses(self):
        """[P1]: `_committed` replays under the ROW's own signature.

        That is right for the families it serves and leaves the column itself
        unowned, so a record signed `{}` replayed and answered. The operands an
        ordinary cleanup signs are derived here and compared.
        """
        settled = self.settled("retain")
        self.reopened()
        operation = settled["operation"]["operation_id"]
        for signature in ("{}", json.dumps(
                {"kind": "runtime.destroy", "operands": {}})):
            with self.subTest(signature=signature):
                with self.damaged("UPDATE operations SET signature = ? WHERE "
                                  "operation_id = ?", (signature, operation)), \
                        self.no_act():
                    caught = self.refusal(self.read)
                self.assertIn("does not derive", caught.message)

    def test_an_ordinary_receipt_carries_no_kind_member(self):
        """[P2]: `kind` belongs to the recordless sibling's settlement.

        Ordinary `_settle` never writes one, and this reader is expressly
        ordinary-only, so admitting it returned a foreign member unchanged.
        """
        settled = self.settled("retain")
        self.reopened()
        operation = settled["operation"]["operation_id"]
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(settled, kind=["foreign", "ending"])),
                 operation)), self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    def test_empty_or_foreign_nested_custody_refuses(self):
        """The gap this provider exists to close: nothing was compared.

        A settled positive absence normalizes both roots and records both
        receipts, so a receipt carrying an empty document, one root, or
        somebody else's normalization is describing acts nobody performed.
        """
        settled = self.settled("retain")
        operation = settled["operation"]["operation_id"]
        held = settled["directory_custody"]
        for name, custody in (
                ("nothing at all", {}),
                ("not a document", None),
                ("only one root", {"result": held["result"]}),
                ("an unknown root", dict(held, elsewhere=held["result"])),
                ("the same root twice",
                 {"result": held["result"], "workspace": held["result"]}),
                ("a foreign receipt",
                 {"result": dict(held["result"], attempt_id="another-attempt"),
                  "workspace": held["workspace"]})):
            with self.subTest(custody=name):
                with self.damaged(
                        "UPDATE operations SET result = ? WHERE "
                        "operation_id = ?",
                        (json.dumps(dict(settled, directory_custody=custody)),
                         operation)), self.no_act():
                    self.assertIsInstance(self.refusal(self.read),
                                          ContractRefusal)

    def test_a_missing_normalization_journal_refuses(self):
        self.settled("retain")
        with self.damaged("DELETE FROM operations WHERE kind = "
                          "'directory-custody.normalize'"), self.no_act():
            self.assertIsInstance(self.refusal(self.read), ContractRefusal)

    def test_a_failed_cleanup_carries_no_custody_and_reads_back(self):
        """A runtime that survived its destroy normalizes nothing.

        `_settle` returns before any directory act on that branch, so the
        receipt must carry `null` there -- and one claiming custody would be
        describing something that did not happen.
        """
        settled = self.settled("retain", destroyed={
            "state": "running", "why": "the engine still lists it",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}})
        self.assertEqual(settled["cleanup"], "failed")
        self.assertIsNone(settled["directory_custody"])
        with self.no_act():
            self.assertEqual(self.read(), settled)
        operation = settled["operation"]["operation_id"]
        with self.damaged(
                "UPDATE operations SET result = ? WHERE operation_id = ?",
                (json.dumps(dict(settled, directory_custody={
                    "result": {}, "workspace": {}})), operation)), \
                self.no_act():
            caught = self.refusal(self.read)
        self.assertIn("normalizes nothing", caught.message)


class TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence(IntakeCase):
    """W128682: the fourth ending's own absence evidence, and its own gate.

    THE MEASURED GAP, discovered by W119114's composed one-Job proof. An
    operator declaration ends the attempt, `port.cancel` fences its generation
    and the authority installs `runtime-quiescence:<generation>` in that same
    transaction. The abandonment then POSITIVELY OBSERVES the exact runtime
    absent -- and nothing could read that observation, so the gate stayed shut
    with no ordinary ending anywhere in the Work's future to discharge it.

    WHY A SEPARATE FAMILY RATHER THAN A WIDER ONE. `_absence_proof` requires an
    `intake_receipt_of` and reads `runtime.destroy` BY NAME. An abandonment has
    neither: nothing was frozen or collected, which is the whole reason it
    exists, and its removal commits under `runtime.destroy-abandoned`. Widening
    the ordinary reader would let one family ride the other's identity, and
    manufacturing a receipt would be inventing the evidence these cases are
    about. So the ordinary reader, act and receipt are untouched, and the last
    two cases here say so.
    """

    REASON = "the supervised worker conversation was lost"

    class Abandoner(Custodian):
        """The custodian, plus the one verb abandonment needs.

        The whole command is recorded, so a case asserting what crossed asserts
        what crossed rather than what this fixture would have liked to send.
        """

        def __init__(self, *arguments, abandoned=None, **operands):
            super().__init__(*arguments, **operands)
            self.abandoned_with = []
            self.abandoned = abandoned

        def destroy_abandoned(self, command):
            self.abandoned_with.append(dict(command))
            runtime_id = command["runtime_id"]
            if self.abandoned is not None:
                return {"runtime_id": runtime_id, **self.abandoned}
            return {"runtime_id": runtime_id, "state": "absent",
                    "why": "the engine answered that this exact identity does "
                           "not exist",
                    "credentials": {"lifecycle_state": "not-delivered"},
                    "launch": {"lifecycle_state": "not-delivered"}}

    def setUp(self):
        super().setUp()
        # The concrete authority answers the evidence KIND it was given, as the
        # ordinary discharge fixture already establishes.
        self.session.discharge_answer["kind"] = "runtime-absent"

    def running_attempt(self):
        """An attempt whose runtime STARTED and whose worker never answered.

        That is the only state abandonment ends, and `_declared` proves all
        three of its conditions inside the write transaction -- so a fixture
        that handed it a completed disposition would be exercising a refusal
        rather than this ending.
        """
        return self.attempt(quiescent=False, disposition=None)

    def fence_for_this_attempt(self):
        """THE FENCE THE AUTHORITY WOULD ANSWER FOR THIS ATTEMPT.

        The shared fake composes its default from the OFFER's live assignment,
        and this suite's attempts are fixed to their own Work -- so an answer
        left at the default is a fence of somebody else's assignment, which the
        port refuses before this ending is reached at all.
        """
        from baton_v12.worker_manager import documents as manager_documents

        row = self.attempt_row()
        expect = manager_documents.assignment(
            work_ref=manager_documents.work_ref(
                authority_uuid=row["authority_uuid"],
                work_id=row["work_id"]),
            participant=row["assignment_participant"],
            generation=row["assignment_generation"])
        self.session.fence_answer = {
            "cause": "cancelled", "assignment": dict(expect), "phase": "block",
            "gate": f"runtime-quiescence:{expect['generation']}",
            "fenced": True}
        return expect

    def abandoned(self, adapter=None, **overrides):
        """One committed abandonment, through the accepted public operation."""
        self.running_attempt()
        self.fence_for_this_attempt()
        adapter = self.Abandoner(**overrides) if adapter is None else adapter
        self.adapter = adapter
        answered = abandon_attempt(
            self.store, self.port, adapter, attempt_id=ATTEMPT,
            reason=self.REASON, retention_policy_digest=RETENTION)
        return answered

    def gated(self, generation=1):
        """The Work as the authority leaves it after the abandonment fence."""
        self.session._work = dict(self.session._work, phase="block",
                                  gate=f"runtime-quiescence:{generation}")

    def read(self, **overrides):
        operands = {"attempt_id": ATTEMPT,
                    "retention_policy_digest": RETENTION}
        operands.update(overrides)
        return abandonment_cleanup_of(self.store, **operands)

    def discharge(self, **overrides):
        operands = {"attempt_id": ATTEMPT,
                    "retention_policy_digest": RETENTION}
        operands.update(overrides)
        return discharge_abandoned_quiescence_gate(self.store, self.port,
                                                   **operands)

    def refused(self, act, **overrides):
        with self.assertRaises(ContractRefusal) as caught:
            act(**overrides)
        return caught.exception

    def satisfied(self):
        return [one for one in self.session.calls if one[0] == "satisfy_gate"]

    def rewrite_operation(self, operation_id, **columns):
        """Edit one journal row, which is what every integrity case is about.

        The reader's whole premise is that a stored row and the digest beside
        it can be edited together, so the cases that prove it say so by really
        editing one.
        """
        sets = ", ".join(f"{name} = ?" for name in columns)
        self.store._connection.execute(
            f"UPDATE operations SET {sets} WHERE operation_id = ?",
            (*columns.values(), operation_id))

    def destroy_operation_id(self):
        from baton_v12.worker_manager import intake

        attempt = self.attempt_row()
        declared = intake._abandonment_declaration(self.store, attempt, ATTEMPT)
        return intake._abandoned_destroy_operation(
            attempt, declared["digest"], RETENTION)["operation_id"]

    # -- the read -----------------------------------------------------------

    def test_a_committed_abandonment_reads_as_its_own_absence_evidence(self):
        answered = self.abandoned()
        held = self.read()
        self.assertEqual(held["schema"], "baton.v12.abandoned-cleanup/1")
        self.assertEqual(held["attempt_id"], ATTEMPT)
        self.assertEqual(held["runtime_id"], self.attempt_row()["runtime_id"])
        self.assertEqual(held["retention_policy_digest"], RETENTION)
        # THE THREE COMMITTED FACTS, adopted from the journal rather than
        # recomposed: the declaration, the authority's own fence answer and
        # the removal's settled cleanup.
        self.assertEqual(held["intent"], answered["intent"])
        self.assertEqual(held["intent"]["reason"], self.REASON)
        self.assertEqual(held["fence"], answered["fenced"])
        self.assertEqual(held["cleanup"], answered["cleanup"])
        self.assertEqual(held["cleanup"]["state"], "absent")
        self.assertEqual(held["cleanup"]["cleanup"], "retained")
        self.assertEqual(held["assignment"], held["fence"]["assignment"])

    def test_reading_writes_nothing_and_calls_nothing(self):
        """It takes no port and no adapter, and there is no branch in it that
        could reach one."""
        self.abandoned()
        before = self.store._connection.execute(
            "SELECT count(*) AS held FROM operations").fetchone()["held"]
        calls = len(self.session.calls)
        self.assertIsNotNone(self.read())
        self.assertEqual(
            self.store._connection.execute(
                "SELECT count(*) AS held FROM operations").fetchone()["held"],
            before)
        self.assertEqual(len(self.session.calls), calls)
        signature = inspect.signature(abandonment_cleanup_of)
        self.assertEqual(
            [name for name in signature.parameters
             if signature.parameters[name].kind.name == "KEYWORD_ONLY"],
            ["attempt_id", "retention_policy_digest"])

    def test_an_undeclared_attempt_has_no_abandoned_cleanup(self):
        """ABSENCE IS HONEST. An attempt nobody declared abandoned has no
        declaration, and that is not a fault."""
        self.running_attempt()
        self.assertIsNone(self.read())

    def test_a_declaration_whose_removal_never_committed_is_absence(self):
        """The intent commits BEFORE any external call, so this state is real:
        a merely recorded declaration never supplies successful absence."""
        adapter = self.Abandoner()
        adapter.destroy_abandoned = lambda command: (_ for _ in ()).throw(
            RuntimeError("the engine was unreachable"))
        self.running_attempt()
        self.fence_for_this_attempt()
        with self.assertRaises(RuntimeError):
            abandon_attempt(self.store, self.port, adapter, attempt_id=ATTEMPT,
                            reason=self.REASON,
                            retention_policy_digest=RETENTION)
        self.assertIsNone(self.read())

    def test_a_runtime_that_survived_its_removal_supplies_no_absence(self):
        """MEASURED RATHER THAN ASSUMED. I expected a surviving runtime to
        leave nothing journalled at all; it does not. `_settle_recordless_
        cleanup` commits the composite with the ending `failed`, which is a
        correct record saying the runtime SURVIVED -- so the row is present and
        this read refuses on the fact rather than answering absence.

        AND THE CATEGORY IS `refused/precondition`, not an integrity fault:
        the record is this family's own committed act and there is nothing
        wrong with it, exactly as `_absence_proof` decides for the ordinary
        family's `failed` ending.
        """
        answered = self.abandoned(adapter=self.Abandoner(abandoned={
            "state": "running",
            "why": "the engine still reports this identity",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}}))
        self.assertEqual(answered["cleanup"]["cleanup"], "failed")
        refusal = self.refused(self.read)
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("evidence against absence", refusal.message)
        # AND THE GATE STAYS SHUT, which is the consequence that matters.
        self.gated()
        self.assertEqual(self.refused(self.discharge).category, "refused")
        self.assertEqual(self.satisfied(), [])
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")

    def test_another_policy_selects_an_act_this_manager_never_committed(self):
        """The declaration's digest and the policy are the two halves of the
        removal identity, exactly as the receipt's digest and the policy are
        for an ordinary cleanup."""
        self.abandoned()
        self.assertIsNone(self.read(retention_policy_digest=OTHER_POLICY))

    def test_an_edited_runtime_cannot_keep_a_real_removals_evidence(self):
        """The declaration names ONE runtime, and this read compares it against
        the attempt as it stands now."""
        self.abandoned()
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("runtime-somebody-else", ATTEMPT))
        refusal = self.refused(self.read)
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertIn("one abandonment", refusal.message)

    def test_a_removal_row_signed_over_anything_else_refuses(self):
        """Replaying under the row's OWN signature proves the row is
        self-consistent and nothing else; `cleanup_of` learned that and this
        reader is held to it."""
        self.abandoned()
        self.rewrite_operation(self.destroy_operation_id(), signature="{}")
        refusal = self.refused(self.read)
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertIn("signature this manager does not derive",
                      refusal.message)

    def test_a_removal_row_committed_under_another_kind_refuses(self):
        self.abandoned()
        self.rewrite_operation(self.destroy_operation_id(),
                               kind="runtime.destroy")
        refusal = self.refused(self.read)
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertIn("runtime.destroy", refusal.message)

    # -- the act ------------------------------------------------------------

    def test_the_committed_abandonment_discharges_its_own_gate(self):
        self.abandoned()
        self.gated()
        receipt = self.discharge()
        self.assertEqual(receipt["schema"],
                         "baton.v12.abandoned-gate-discharge/1")
        self.assertEqual(receipt["attempt_id"], ATTEMPT)
        self.assertEqual(receipt["gate"], "runtime-quiescence:1")
        self.assertEqual(receipt["authority_receipt"]["phase"], "queued")
        self.assertEqual(receipt["authority_receipt"]["kind"], "runtime-absent")
        # THE WORK IS ACTUALLY UNGATED, read from the authority rather than
        # from what this manager asked for.
        self.assertIsNone(self.session._work["gate"])
        self.assertEqual(self.session._work["phase"], "queued")

    def test_the_evidence_is_positive_absence_naming_the_exact_runtime(self):
        self.abandoned()
        self.gated()
        self.discharge()
        [evidence] = self.session.gate_evidence
        self.assertEqual(evidence,
                         {"kind": "runtime-absent",
                          "runtime": self.attempt_row()["runtime_id"]})

    def test_the_receipt_binds_the_original_cleanup_operation(self):
        """The contract's own requirement: the cleanup's identity AND its
        signature ride the discharge, because the signature is the half that
        names the runtime."""
        self.abandoned()
        self.gated()
        receipt = self.discharge()
        held = self.read()
        self.assertEqual(receipt["cleanup_operation"],
                         held["cleanup"]["operation"])
        self.assertEqual(receipt["operation_id"].split(":")[0],
                         "authority.discharge-quiescence-abandoned")

    def test_it_is_read_back_and_replayed_without_a_second_remote_act(self):
        self.abandoned()
        self.gated()
        first = self.discharge()
        self.assertEqual(abandoned_gate_discharge_of(self.store, ATTEMPT),
                         first)
        asked = len(self.satisfied())
        self.assertEqual(self.discharge(), first)
        self.assertEqual(len(self.satisfied()), asked)

    def test_a_lost_local_receipt_reissues_the_identical_remote_operation(self):
        """FOUR AND FIVE CANNOT BE ONE TRANSACTION. The remote act commits
        first; a crash before the journal must reproduce the answer, and the
        authority's own replay is what makes that idempotent -- even though the
        Work has since been ungated."""
        self.abandoned()
        self.gated()
        with patch.object(type(self.store), "transact",
                          side_effect=RuntimeError("the local receipt is lost")):
            with self.assertRaises(RuntimeError):
                self.discharge()
        self.assertIsNone(abandoned_gate_discharge_of(self.store, ATTEMPT))
        self.assertIsNone(self.session._work["gate"])
        receipt = self.discharge()
        self.assertEqual(receipt["gate"], "runtime-quiescence:1")
        [first, second] = [operands for _act, operands in self.satisfied()]
        self.assertEqual(first, second)
        self.assertEqual(abandoned_gate_discharge_of(self.store, ATTEMPT),
                         receipt)

    def test_an_old_generations_evidence_cannot_clear_a_newer_gate(self):
        """The authority's own equality check is what refuses it, which is the
        owner of that fact deciding rather than a comparison composed here."""
        self.abandoned()
        self.gated(generation=2)
        refusal = self.refused(self.discharge)
        self.assertIn("not the one holding this Work", refusal.message)
        self.assertIsNone(abandoned_gate_discharge_of(self.store, ATTEMPT))

    def test_no_committed_abandonment_is_not_a_gate_to_discharge(self):
        self.running_attempt()
        self.gated()
        refusal = self.refused(self.discharge)
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("never on the absence of one", refusal.message)
        self.assertEqual(self.satisfied(), [])

    def test_a_session_acting_for_another_participant_is_refused_first(self):
        from baton_v12.worker_manager import AuthorityPort

        from .test_offers import FakeSession, fake_claim_signature

        self.abandoned()
        self.gated()
        foreign = AuthorityPort(FakeSession(participant="somebody.else"),
                                fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            discharge_abandoned_quiescence_gate(
                self.store, foreign, attempt_id=ATTEMPT,
                retention_policy_digest=RETENTION)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertEqual(self.satisfied(), [])

    def test_a_session_on_another_authority_never_reaches_the_act(self):
        """Same participant, same Work selector, same generation, another
        authority. A four-part assignment is not three quarters of one."""
        self.abandoned()
        self.gated()
        self.session._work = dict(self.session._work, authority_uuid="9" * 32)
        refusal = self.refused(self.discharge)
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "capability"))
        self.assertEqual(self.satisfied(), [])
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
        self.assertIsNone(abandoned_gate_discharge_of(self.store, ATTEMPT))

    def test_a_receipt_edited_member_by_member_cannot_reproduce_its_signature(
            self):
        """One comparison for a relationship six field checks cannot state."""
        self.abandoned()
        self.gated()
        receipt = self.discharge()
        from baton_v12.worker_manager import intake

        operation_id = receipt["operation_id"]
        spoiled = dict(receipt, runtime_id="runtime-somebody-else",
                       evidence={"kind": "runtime-absent",
                                 "runtime": "runtime-somebody-else"})
        self.rewrite_operation(operation_id, result=json.dumps(spoiled))
        refusal = self.refused(
            lambda: abandoned_gate_discharge_of(self.store, ATTEMPT))
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertIn("ONE signed relationship", refusal.message)
        self.assertEqual(intake.ABANDONED_GATE_DISCHARGE_KIND,
                         "authority.discharge-quiescence-abandoned")

    def test_a_discharge_row_committed_under_another_kind_refuses(self):
        self.abandoned()
        self.gated()
        receipt = self.discharge()
        self.rewrite_operation(receipt["operation_id"],
                               kind="authority.discharge-quiescence")
        refusal = self.refused(
            lambda: abandoned_gate_discharge_of(self.store, ATTEMPT))
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))

    def test_the_caller_supplies_no_absence_runtime_gate_or_assignment(self):
        signature = inspect.signature(discharge_abandoned_quiescence_gate)
        self.assertEqual(
            [name for name in signature.parameters
             if signature.parameters[name].kind.name == "KEYWORD_ONLY"],
            ["attempt_id", "retention_policy_digest"])

    # -- the ordinary family is untouched ------------------------------------

    def test_the_ordinary_readers_answer_nothing_about_an_abandonment(self):
        """THE FOUR FAMILIES STAY APART. `cleanup_of` reads `runtime.destroy`
        by name and `gate_discharge_of` derives the ordinary identity, so
        neither admits this ending by accident -- and the abandoned reader is
        equally blind to an ordinary one."""
        self.abandoned()
        self.gated()
        self.discharge()
        self.assertIsNone(cleanup_of(self.store, attempt_id=ATTEMPT,
                                     retention_policy_digest=RETENTION))
        self.assertIsNone(gate_discharge_of(self.store, ATTEMPT))

    def test_the_ordinary_discharge_still_refuses_an_abandoned_attempt(self):
        """It refuses for its OWN reason -- there is no intake receipt -- which
        is the sentence that made a separate family necessary."""
        self.abandoned()
        self.gated()
        refusal = self.refused(
            lambda: discharge_quiescence_gate(
                self.store, self.port, attempt_id=ATTEMPT,
                retention_policy_digest=RETENTION))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("no intake receipt", refusal.message)
        self.assertEqual(self.satisfied(), [])

    def test_an_ordinary_cleanup_is_not_read_as_an_abandoned_one(self):
        """The other direction of the same rule."""
        self.retained_ready("discard-after-intake")
        self.ended()
        authorize_cleanup(self.store, self.port, Custodian(),
                          attempt_id=ATTEMPT,
                          retention_policy_digest=RETENTION)
        self.assertIsNotNone(cleanup_of(self.store, attempt_id=ATTEMPT,
                                        retention_policy_digest=RETENTION))
        self.assertIsNone(self.read())
        self.assertIsNone(abandoned_gate_discharge_of(self.store, ATTEMPT))
