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

import os
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal, digest, held_secret
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager import (authorize_cleanup, decide_retention,
                                      intake_operation, intake_receipt_of,
                                      manager_signature, observe,
                                      reconcile_runtime,
                                      record_intake, request_intake,
                                      request_runtime_start, retain_operation,
                                      retentions_of)
from baton_v12.worker_manager import documents
from baton_v12.worker_manager import load_manifest

from .test_offers import NOW, WHO
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
