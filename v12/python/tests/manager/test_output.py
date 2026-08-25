"""W6628 — the output freeze and the sealed artifact receiver.

`work/records/2026/08/finding-v12-manager-output-receiver/`.

THE ACCEPTANCE, and every case below belongs to one of its lines:

  - quiescence proved before freeze, with `freeze-requested` and `frozen`
    distinct;
  - the declared manifest, count, bytes and digest RECOMPUTED by the manager
    rather than adopted from the collector's account;
  - an immutable staging identity, so a retry names the same material;
  - effectively-once acceptance through W4's journal;
  - caller-local refusals, with engine and adapter status carrying no
    authority meaning;
  - `missing-optional` recorded as the answer it is.

THE INPUT DECLARATION IS THE PUBLISHED CONFORMANCE VECTOR, not a document I
wrote to pass my own rules. Every result manifest here is built to ANSWER that
declaration, which is the shape a real one has, and each case spoils exactly
one thing in it.
"""

import json
import os
import pathlib
import sqlite3
import tempfile
import unittest

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal, canonical_bytes, digest
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      accept_offer, activate_assignment,
                                      freeze_operation, frozen_output_of,
                                      issue_offer, load_manifest, observe,
                                      record_attempt, record_frozen_result,
                                      request_freeze, retain_manifest,
                                      submit_claim)
from baton_v12.worker_manager import schema

from .test_attempts import ADAPTER, ATTEMPT
from .test_offers import (FakeSession, NOW, PROFILE, WHO,
                          fake_claim_signature)

# THE PUBLISHED VECTOR'S OWN Work, and its authority. §12 rule 1 makes a Work
# id carry its authority's eight-character prefix, and the offer fixtures this
# package shares were written for a path that never validates a manifest — so
# reusing their pair here would refuse every case at the identity rule before
# it reached the comparison it is aiming at. Using the DECLARATION's own Work
# is also the truer fixture: a result answers the declaration for the Work the
# declaration names.
AUTHORITY = "43c55d4b1234567890abcdef12345678"
JOB = "43c55d4b-W1439"

REPOSITORY = pathlib.Path(__file__).resolve().parents[4]
VECTORS = (REPOSITORY / "work" / "records" / "2026" / "08"
           / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")

POLICY = "sha256:" + "2" * 64
CONTENT = "sha256:" + "8" * 64


def sealed(document):
    """A document that identifies itself — the digest recomputed over its own
    bytes with that member omitted, exactly as §12 states it."""
    body = {name: value for name, value in document.items()
            if name != "manifest_digest"}
    return {**body, "manifest_digest": digest(body)}


class Collector:
    """The runtime adapter's seal, with every answer a case may need to set.

    Deliberately narrow: what an adapter ASSERTS about its own success decides
    nothing here, so this records what it was handed and answers with whatever
    the case wants validated.
    """

    def __init__(self, answer=None):
        self.sealed_with = []
        self.answer = answer
        self.failure = None

    def seal(self, operands):
        self.sealed_with.append(operands)
        if self.failure is not None:
            raise self.failure
        return self.answer


class OutputCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-output-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        worker_manager.certify_profile(self.store, "runtime", "reference",
                                       PROFILE)
        self.session = FakeSession(
            work={"status": "open", "phase": "queued", "handler": None,
                  "gate": None, "authority_uuid": AUTHORITY})
        self.session.claim_answer = {
            "work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
            "participant": WHO, "generation": 1}
        self.session.live_assignment = dict(self.session.claim_answer)
        self.port = AuthorityPort(self.session, fake_claim_signature)
        self.declaration = self.published()
        self.input_digest = retain_manifest(
            self.store, self.declaration, "inputManifest")["digest"]

    # -- the published declaration ----------------------------------------

    @staticmethod
    def published():
        vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
        for case in vectors["valid"]:
            document = case["document"]
            if document.get("schema") == "baton.worker-manifest/input":
                return document
        raise AssertionError("the published vectors carry no input manifest")

    def redeclared(self, **members):
        """The published declaration with members replaced and RESEALED, then
        retained — so a case aiming at a comparison is not stopped by the
        identity rule on the way."""
        document = sealed(dict(self.declaration, **members))
        self.input_digest = retain_manifest(
            self.store, document, "inputManifest")["digest"]
        return document

    # -- the attempt ------------------------------------------------------

    def attempt(self, *, quiescent=True, disposition="completed"):
        issue_offer(self.store, self.port, offer_id="offer-1", work_id=JOB,
                    runtime_attempt_id=ATTEMPT,
                    input_digest=self.input_digest, policy_digest=POLICY,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-1")
        accept_offer(self.store, self.port, offer_id="offer-1",
                     decision="accept", bearer="bearer-1", now=NOW,
                     runtime_attempt_id=ATTEMPT,
                     work_ref={"authority_uuid": AUTHORITY, "work_id": JOB})
        record_attempt(self.store, attempt_id=ATTEMPT, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       input_digest=self.input_digest, policy_digest=POLICY)
        submit_claim(self.store, self.port, offer_id="offer-1")
        activate_assignment(
            self.store, self.port, attempt_id=ATTEMPT,
            expect={"work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
                    "participant": WHO, "generation": 1})
        if quiescent:
            observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                    value="running")
            observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                    value="quiescent")
        if disposition is not None:
            observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition",
                    value=disposition)
        return ATTEMPT

    def attempt_row(self):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                (ATTEMPT,)).fetchone()
            return {k: found[k] for k in found.keys()}
        finally:
            beside.close()

    # -- the sealed result ------------------------------------------------

    def result(self, *, disposition="completed", outputs=None, **members):
        """A result that ANSWERS the declaration, sealed."""
        row = self.attempt_row()
        operation = freeze_operation(row)
        body = {
            "version": {"major": 1, "minor": 0},
            "manifest_id": "result-manifest-1",
            "created_at": NOW,
            "extensions": {},
            "schema": "baton.worker-manifest/result",
            "result_id": "result-1",
            "assignment_ref": {
                "work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
                "participant": WHO, "generation": 1},
            "input_manifest_digest": self.input_digest,
            "policy_digest": POLICY,
            "disposition": disposition,
            "outputs": self.present() if outputs is None else outputs,
            "evidence": [],
            "freeze_operation": dict(operation),
            "manager_observed_at": NOW,
        }
        body.update(members)
        return sealed(body)

    @staticmethod
    def present(name="proposal", bytes_=64, entries=1,
                media_type="text/plain", artifact_bytes=None):
        """A `present` output whose content manifest is SELF-CONSISTENT.

        The aggregates are recomputed here rather than asserted, because §12
        rule 6 already refuses a manifest whose count, total or tree digest
        does not match its entries — so a fixture that lied about one would be
        refused by the validator before it reached the rule a case is aiming
        at, which is the vacuous-probe shape this campaign keeps correcting.

        The paths are zero-padded so they stay bytewise sorted past ten, which
        the same rule requires.
        """
        entry_list = [{"path": f"file-{index:04d}.txt", "bytes": bytes_,
                       "content_digest": CONTENT}
                      for index in range(entries)]
        total = sum(entry["bytes"] for entry in entry_list)
        return [{
            "name": name, "type": "directory-result", "status": "present",
            "content_manifest": {
                "entries": entry_list,
                "entry_count": len(entry_list),
                "total_bytes": total,
                "tree_digest": digest(entry_list)},
            "artifact": {"artifact_id": "artifact-1",
                         "media_type": media_type,
                         "bytes": total if artifact_bytes is None
                                  else artifact_bytes,
                         "content_digest": CONTENT,
                         "locator": "file:///var/lib/baton/artifact-1"},
        }]

    @staticmethod
    def missing(name="proposal"):
        return [{"name": name, "type": "directory-result",
                 "status": "missing-optional",
                 "content_manifest": None, "artifact": None}]

    def frozen(self, **overrides):
        """The whole happy path: freeze, seal, record."""
        self.attempt()
        adapter = Collector(self.result(**overrides))
        return request_freeze(self.store, self.port, adapter,
                              attempt_id=ATTEMPT,
                              disposition=overrides.get("disposition",
                                                        "completed")), adapter


# -- the retained manifests --------------------------------------------------

class ADigestIsNotARecord(OutputCase):

    def test_a_declaration_is_retained_and_read_back(self):
        loaded = load_manifest(self.store, self.input_digest, "inputManifest")
        self.assertEqual(loaded["schema"], "baton.worker-manifest/input")
        self.assertEqual(loaded["outputs"][0]["name"], "proposal")

    def test_retention_is_idempotent_by_construction(self):
        """The key IS the digest, so the same document stored twice is the
        same row — and the answer says which call actually wrote it."""
        again = retain_manifest(self.store, self.declaration, "inputManifest")
        self.assertEqual(again["digest"], self.input_digest)
        self.assertIs(again["retained"], False)

    def test_an_absent_digest_is_absence_not_an_error(self):
        self.assertIsNone(load_manifest(self.store, "sha256:" + "e" * 64,
                                        "inputManifest"))

    def test_being_at_the_key_is_not_being_the_named_thing(self):
        """A retained RESULT manifest is a perfectly valid thing to hold.
        Naming one as an attempt's input digest would let its similarly shaped
        output rows be read as trusted DECLARATIONS."""
        self.attempt()
        result = self.result()
        retained = retain_manifest(self.store, result, "resultManifest")
        with self.assertRaises(ContractRefusal) as caught:
            load_manifest(self.store, retained["digest"], "inputManifest")
        self.assertEqual(caught.exception.code, "schema")

    def test_a_caller_that_names_no_kind_has_checked_nothing(self):
        for spoiled in ("", None, 1):
            with self.subTest(definition=spoiled):
                with self.assertRaises(ContractRefusal):
                    load_manifest(self.store, self.input_digest, spoiled)

    def test_a_hand_edited_body_does_not_outlive_the_guard_on_the_way_in(self):
        """A store nobody validates on the way OUT is a store where a hand
        edit outlives every guard on the way in."""
        other = sealed(dict(self.declaration, manifest_id="input-manifest-2"))
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("UPDATE manifests SET body = ? WHERE digest = ?",
                       (canonical_bytes(other).decode("utf-8"),
                        self.input_digest))
        beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            load_manifest(self.store, self.input_digest, "inputManifest")
        self.assertEqual(caught.exception.code, "digest")

    def test_a_digest_cannot_name_two_documents(self):
        """Not something SHA-256 hands out — and "cannot happen" is not a
        reason to write the second one over the first."""
        other = sealed(dict(self.declaration, manifest_id="input-manifest-2"))
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("UPDATE manifests SET body = ? WHERE digest = ?",
                       (canonical_bytes(other).decode("utf-8"),
                        self.input_digest))
        beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            retain_manifest(self.store, self.declaration, "inputManifest")
        self.assertIn("cannot name two", caught.exception.message)

    def test_a_malformed_document_is_never_retained(self):
        """The store is not the place a document this manager could not read
        survives."""
        with self.assertRaises(ContractRefusal):
            retain_manifest(self.store, dict(self.declaration, outputs=[]),
                            "inputManifest")


# -- quiescence before freeze ------------------------------------------------

class QuiescenceIsProvedBeforeFreeze(OutputCase):

    def test_only_a_positive_quiescent_observation_permits_a_freeze(self):
        """`uncertain` is not quiescence — it is a failure to look — and
        `destroyed` is not either: a writer that is gone was never observed to
        have finished."""
        for value in ("not-started", "running", "uncertain", "destroyed"):
            with self.subTest(execution_runtime=value):
                self.setUp()
                self.attempt(quiescent=False)
                if value != "not-started":
                    observe(self.store, attempt_id=ATTEMPT,
                            axis="execution_runtime", value=value)
                with self.assertRaises(ContractRefusal) as caught:
                    request_freeze(self.store, self.port, Collector(),
                                   attempt_id=ATTEMPT,
                                   disposition="completed")
                self.assertEqual(caught.exception.code, "quiescence-unknown")

    def test_quiescence_is_rechecked_inside_the_freeze_write(self):
        """A newer runtime observation between the optimistic read and the
        journal write must decide the freeze.

        This opens that window deterministically rather than hoping two
        processes happen to interleave there: `request_freeze` has already
        adopted its attempt row when it reaches `transact`, then the newer
        observation lands before the real transaction begins.
        """
        self.attempt()
        transact = self.store.transact

        def runtime_moves_first(operation_id, kind, signature, action):
            if kind == "output.freeze":
                observe(self.store, attempt_id=ATTEMPT,
                        axis="execution_runtime", value="uncertain")
            return transact(operation_id, kind, signature, action)

        self.store.transact = runtime_moves_first
        adapter = Collector()
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, adapter,
                           attempt_id=ATTEMPT, disposition="completed")
        self.assertEqual(self.attempt_row()["output"], "open")
        self.assertEqual(adapter.sealed_with, [])
        self.assertEqual(caught.exception.code, "quiescence-unknown")

    def test_the_outer_check_is_optimistic_and_the_inner_one_decides(self):
        """The correction's shape, asserted as a property.

        The reviewer's case above proves the newer observation wins. This
        proves the SPLIT: the outside check refuses without ever taking a
        write lock, and the inside one is what authorizes the transition.
        """
        self.attempt(quiescent=False)
        journalled = []
        transact = self.store.transact

        def watching(operation_id, kind, signature, action):
            journalled.append(kind)
            return transact(operation_id, kind, signature, action)

        self.store.transact = watching
        with self.assertRaises(ContractRefusal):
            request_freeze(self.store, self.port, Collector(),
                           attempt_id=ATTEMPT, disposition="completed")
        self.assertEqual(journalled, [],
                         "a plainly unready attempt reached the journal")

    def test_the_disposition_axis_is_terminal_once(self):
        """The reliance the inner re-check's inertness rests on.

        Only the quiescence half can move between the optimistic read and the
        write lock: every disposition beyond `none` has an empty successor
        set, so one proved terminal and equal outside is still both inside. If
        that ever stops being true the inner half stops being inert, and this
        case is what says so rather than leaving it to an assumption nobody
        re-checks.
        """
        moves = worker_manager.TRANSITIONS["worker_disposition"]
        self.assertEqual(set(moves["none"]), set(schema.DISPOSITIONS))
        for disposition in schema.DISPOSITIONS:
            with self.subTest(disposition=disposition):
                self.assertEqual(moves[disposition], (),
                                 "a terminal disposition gained a successor")

    def test_a_freeze_needs_a_recorded_terminal_disposition(self):
        self.attempt(disposition=None)
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, Collector(),
                           attempt_id=ATTEMPT, disposition="completed")
        self.assertIn("no recorded worker disposition",
                      caught.exception.message)

    def test_the_declared_disposition_is_compared_not_accepted(self):
        """The turn outcome gates the disposition and never chooses it. A
        proof the caller can write is not a proof."""
        self.attempt(disposition="unable")
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, Collector(),
                           attempt_id=ATTEMPT, disposition="completed")
        self.assertIn("recorded disposition unable", caught.exception.message)

    def test_an_unactivated_attempt_freezes_nothing(self):
        record_attempt(self.store, attempt_id="attempt-loose",
                       adapter_name="acp", adapter_digest=ADAPTER,
                       profile_digest=PROFILE)
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, Collector(),
                           attempt_id="attempt-loose", disposition="completed")
        self.assertIn("no fixed assignment", caught.exception.message)

    def test_a_foreign_session_freezes_nothing(self):
        self.attempt()
        other = AuthorityPort(FakeSession(participant="lang.bee"),
                              fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, other, Collector(), attempt_id=ATTEMPT,
                           disposition="completed")
        self.assertEqual(caught.exception.code, "capability")

    def test_a_dead_assignment_is_never_published_on(self):
        self.attempt()
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, Collector(),
                           attempt_id=ATTEMPT, disposition="completed")
        self.assertEqual(caught.exception.category, "stale-assignment")

    def test_an_adapter_without_seal_is_refused_before_anything_moves(self):
        self.attempt()

        class Nothing:
            pass

        with self.assertRaises(ContractRefusal):
            request_freeze(self.store, self.port, Nothing(),
                           attempt_id=ATTEMPT, disposition="completed")
        self.assertEqual(self.attempt_row()["output"], "open")

    def test_the_adapter_is_handed_the_whole_operation_identity(self):
        """An adapter handed only the retry key cannot echo the binding, and a
        manager that asks for an echo it never supplied is asking the adapter
        to guess."""
        _answer, adapter = self.frozen()
        handed = adapter.sealed_with[0]["operation"]
        self.assertEqual(sorted(handed), ["operation_id", "signature_digest"])
        self.assertEqual(handed, dict(freeze_operation(self.attempt_row())))


# -- the two states are two states -------------------------------------------

class FreezingIsNotAccepting(OutputCase):

    def test_the_axis_moves_through_freeze_requested_to_frozen(self):
        self.frozen()
        self.assertEqual(self.attempt_row()["output"], "frozen")

    def test_a_failed_seal_leaves_the_freeze_requested(self):
        """The request landed and the result did not. That is a real durable
        state and the axis says so rather than pretending the freeze never
        happened."""
        self.attempt()
        adapter = Collector()
        adapter.failure = RuntimeError("the collector died")
        with self.assertRaises(RuntimeError):
            request_freeze(self.store, self.port, adapter, attempt_id=ATTEMPT,
                           disposition="completed")
        self.assertEqual(self.attempt_row()["output"], "freeze-requested")

    def test_invalid_is_still_reachable_from_frozen(self):
        """Material can be frozen and THEN found invalid, which a receiver
        collapsing frozen and sealed could not express."""
        self.frozen()
        self.assertIn("invalid", worker_manager.TRANSITIONS["output"]["frozen"])
        observe(self.store, attempt_id=ATTEMPT, axis="output", value="invalid")
        self.assertEqual(self.attempt_row()["output"], "invalid")

    def test_this_slice_never_writes_sealed(self):
        """Sealing is somebody else's, and the axis is left where this slice
        can honestly say it is."""
        self.frozen()
        self.assertEqual(self.attempt_row()["output"], "frozen")


# -- the immutable record identity -------------------------------------------

class TheRecordIdentityIsTheAct(OutputCase):

    def test_the_same_result_replays(self):
        first, _adapter = self.frozen()
        again = record_frozen_result(self.store, attempt_id=ATTEMPT,
                                     sealed=self.result())
        self.assertEqual(first, again)

    def test_changed_bytes_under_the_same_identity_refuse(self):
        """If the identity varied with the bytes, two different results would
        be two different operations and BOTH would commit — the opposite of
        what an immutable record means."""
        self.frozen()
        with self.assertRaises(ContractRefusal) as caught:
            record_frozen_result(self.store, attempt_id=ATTEMPT,
                                 sealed=self.result(result_id="result-2"))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_replay_asks_nothing_about_today(self):
        """Replay is a fact about an identity that already settled. The frozen
        host was corrected twice for consulting today's state first — once the
        output axis, once the declaration lookup."""
        first, _adapter = self.frozen()
        observe(self.store, attempt_id=ATTEMPT, axis="output", value="invalid")
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("DELETE FROM manifests WHERE digest = ?",
                       (self.input_digest,))
        beside.close()
        self.assertEqual(record_frozen_result(self.store, attempt_id=ATTEMPT,
                                              sealed=self.result()), first)

    def test_the_freeze_identity_is_fixed_per_attempt_and_generation(self):
        self.attempt()
        row = self.attempt_row()
        self.assertEqual(freeze_operation(row), freeze_operation(row))
        other = dict(row, assignment_generation=2)
        self.assertNotEqual(freeze_operation(row)["operation_id"],
                            freeze_operation(other)["operation_id"])


# -- binding the sealed observation to THIS attempt --------------------------

class TheResultMustBeThisAttemptsResult(OutputCase):

    def refusing(self, phrase, **members):
        self.attempt()
        adapter = Collector(self.result(**members))
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, adapter, attempt_id=ATTEMPT,
                           disposition="completed")
        self.assertIn(phrase, caught.exception.message)
        return caught.exception

    def test_a_result_naming_another_assignment_is_refused(self):
        failure = self.refusing("is fixed to", assignment_ref={
            "work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
            "participant": WHO, "generation": 2})
        self.assertEqual(failure.category, "stale-assignment")

    def test_a_result_naming_another_input_is_refused(self):
        self.refusing("declares input digest",
                      input_manifest_digest="sha256:" + "d" * 64)

    def test_a_result_naming_another_policy_is_refused(self):
        self.refusing("declares policy digest",
                      policy_digest="sha256:" + "c" * 64)

    def test_a_result_declaring_another_disposition_is_refused(self):
        self.refusing("declares unable", disposition="unable")

    def test_a_result_settling_another_freeze_is_refused(self):
        self.refusing("settles", freeze_operation={
            "operation_id": "output.freeze:" + "a" * 64,
            "signature_digest": "sha256:" + "a" * 64})

    def test_an_echoed_key_with_any_signature_is_not_a_binding(self):
        """The frozen host's review [P1]: only the id was compared, so a result
        echoing the right retry key with any schema-shaped digest was accepted
        as settling this freeze. The key is the retry; the signature binds."""
        self.attempt()
        operation = dict(freeze_operation(self.attempt_row()),
                         signature_digest="sha256:" + "b" * 64)
        adapter = Collector(self.result(freeze_operation=operation))
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, adapter, attempt_id=ATTEMPT,
                           disposition="completed")
        self.assertEqual(caught.exception.code, "digest")

    def test_a_declaration_nobody_retained_compares_against_nothing(self):
        self.attempt()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("DELETE FROM manifests WHERE digest = ?",
                       (self.input_digest,))
        beside.close()
        adapter = Collector(self.result())
        with self.assertRaises(ContractRefusal) as caught:
            request_freeze(self.store, self.port, adapter, attempt_id=ATTEMPT,
                           disposition="completed")
        self.assertIn("nobody retained", caught.exception.message)


# -- the declarations, compared both ways ------------------------------------

class EveryDeclarationIsAnsweredAndEveryAnswerDeclared(OutputCase):

    def recording(self, outputs, disposition="completed"):
        self.attempt(disposition=disposition)
        with self.assertRaises(ContractRefusal) as caught:
            record_frozen_result(
                self.store, attempt_id=ATTEMPT,
                sealed=self.result(outputs=outputs, disposition=disposition))
        return caught.exception

    def test_an_undeclared_output_is_never_collected(self):
        outputs = self.present() + self.present(name="scratch")
        failure = self.recording(outputs)
        self.assertIn("does not declare", failure.message)

    def test_a_declaration_the_result_ignores_is_not_answered(self):
        failure = self.recording([])
        self.assertIn("does not answer it", failure.message)

    def test_two_answers_to_one_declaration_is_not_an_answer(self):
        failure = self.recording(self.present() + self.present())
        self.assertIn("twice", failure.message)

    def test_a_declared_type_is_compared(self):
        outputs = [dict(self.present()[0], type="record-output")]
        failure = self.recording(outputs)
        self.assertIn("is declared directory-result", failure.message)

    def test_a_required_output_missing_under_completed_is_not_a_completion(
            self):
        failure = self.recording(self.missing())
        self.assertIn("required", failure.message)

    def test_an_inability_may_return_evidence_without_the_result(self):
        """An inability disposition may return evidence without pretending the
        requested result exists — which is exactly why the rule above is
        conditioned on the disposition rather than refused outright."""
        self.attempt(disposition="unable")
        adapter = Collector(self.result(disposition="unable",
                                        outputs=self.missing()))
        answer = request_freeze(self.store, self.port, adapter,
                                attempt_id=ATTEMPT, disposition="unable")
        self.assertEqual(answer["disposition"], "unable")


# -- missing-optional is a status, not an absence ----------------------------

class MissingOptionalIsAnAnswer(OutputCase):

    def optional(self):
        outputs = [dict(self.declaration["outputs"][0], required=False)]
        self.redeclared(outputs=outputs)

    def test_a_missing_optional_output_is_recorded_as_the_answer_it_is(self):
        """An output the assignment declared as not required and which did not
        appear is REPORTED. A receiver that treated it as nothing to record
        would lose the fact that the worker was asked and answered."""
        self.optional()
        self.attempt()
        adapter = Collector(self.result(outputs=self.missing()))
        answer = request_freeze(self.store, self.port, adapter,
                                attempt_id=ATTEMPT, disposition="completed")
        self.assertEqual(answer["outputs"],
                         [{"name": "proposal", "type": "directory-result",
                           "status": "missing-optional"}])

    def test_it_carries_no_artifact_row_and_is_still_not_lost(self):
        """The artifact table is the INDEXED half; the retained result document
        is the record, and it preserves every output whole."""
        self.optional()
        self.attempt()
        adapter = Collector(self.result(outputs=self.missing()))
        answer = request_freeze(self.store, self.port, adapter,
                                attempt_id=ATTEMPT, disposition="completed")
        stored = frozen_output_of(self.store, ATTEMPT)
        self.assertEqual(stored["artifacts"], [])
        retained = load_manifest(self.store, answer["manifest_digest"],
                                 "resultManifest")
        self.assertEqual(retained["outputs"][0]["status"], "missing-optional")

    def test_a_missing_output_that_carries_material_contradicts_itself(self):
        self.optional()
        self.attempt()
        material = self.present()[0]["content_manifest"]
        contradictory = [dict(self.missing()[0], content_manifest=material)]
        with self.assertRaises(ContractRefusal) as caught:
            record_frozen_result(self.store, attempt_id=ATTEMPT,
                                 sealed=self.result(outputs=contradictory))
        self.assertIn("a missing output is missing", caught.exception.message)

    def test_a_present_output_must_carry_both_representations(self):
        """A status word is not material, and the nullable members exist so a
        MISSING output can say so — not so a present one can choose which half
        to supply."""
        for what in ("content_manifest", "artifact"):
            with self.subTest(missing=what):
                self.setUp()
                self.attempt()
                half = [dict(self.present()[0], **{what: None})]
                with self.assertRaises(ContractRefusal) as caught:
                    record_frozen_result(
                        self.store, attempt_id=ATTEMPT,
                        sealed=self.result(outputs=half))
                self.assertIn("binds both", caught.exception.message)


# -- the declared limits -----------------------------------------------------

class TheDeclaredLimitsAreEnforcedWhereTheyAreDecidable(OutputCase):

    def refusing(self, outputs):
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            record_frozen_result(self.store, attempt_id=ATTEMPT,
                                 sealed=self.result(outputs=outputs))
        return caught.exception

    def test_an_oversized_tree_is_refused(self):
        failure = self.refusing(self.present(bytes_=2 * 1024 * 1024,
                                             artifact_bytes=64))
        self.assertEqual(failure.code, "limit")
        self.assertIn("tree", failure.message)

    def test_an_oversized_artifact_is_refused(self):
        """BOTH sizes, because a present output has two representations of the
        thing the declaration bounds. Measuring only whichever one happened to
        be there leaves the other unbounded."""
        failure = self.refusing(self.present(artifact_bytes=2 * 1024 * 1024))
        self.assertEqual(failure.code, "limit")
        self.assertIn("artifact", failure.message)

    def test_too_many_entries_are_refused(self):
        failure = self.refusing(self.present(bytes_=1, entries=101))
        self.assertEqual(failure.code, "limit")
        self.assertIn("entries", failure.message)

    def test_a_media_type_the_declaration_does_not_allow_is_denied(self):
        failure = self.refusing(self.present(media_type="application/x-thing"))
        self.assertEqual((failure.category, failure.code),
                         ("policy", "denied"))

    def test_an_empty_allow_list_permits_nothing(self):
        """An allow-list that permits everything when it names nothing is a
        fail-open reading of a rule written to close."""
        constraints = dict(self.declaration["outputs"][0]["constraints"],
                           allowed_media_types=[])
        self.redeclared(outputs=[dict(self.declaration["outputs"][0],
                                      constraints=constraints)])
        failure = self.refusing(self.present())
        self.assertEqual(failure.code, "denied")


# -- what is recorded --------------------------------------------------------

class TheSealedObservationIsRetainedNotSummarized(OutputCase):

    def test_the_whole_document_is_retained_under_its_recomputed_digest(self):
        answer, _adapter = self.frozen()
        retained = load_manifest(self.store, answer["manifest_digest"],
                                 "resultManifest")
        self.assertEqual(retained["result_id"], "result-1")
        self.assertEqual(
            retained["outputs"][0]["content_manifest"]["tree_digest"],
            self.present()[0]["content_manifest"]["tree_digest"])
        self.assertEqual(retained["freeze_operation"],
                         dict(freeze_operation(self.attempt_row())))

    def test_the_stored_digest_is_a_computation_not_a_claim(self):
        """The number stored beside the result is derived from the bytes rather
        than lifted from a member the document filled in about itself."""
        answer, _adapter = self.frozen()
        document = self.result()
        recomputed = digest({name: value for name, value in document.items()
                             if name != "manifest_digest"})
        self.assertEqual(answer["manifest_digest"], recomputed)

    def test_the_artifact_references_are_indexed(self):
        self.frozen()
        stored = frozen_output_of(self.store, ATTEMPT)
        self.assertEqual(len(stored["artifacts"]), 1)
        self.assertEqual(stored["artifacts"][0]["output_name"], "proposal")
        self.assertEqual(stored["artifacts"][0]["media_type"], "text/plain")
        self.assertEqual(stored["freeze_operation_id"],
                         freeze_operation(self.attempt_row())["operation_id"])

    def test_an_attempt_that_never_froze_has_no_output(self):
        self.attempt()
        self.assertIsNone(frozen_output_of(self.store, ATTEMPT))

    def test_a_result_recorded_against_no_requested_freeze_is_refused(self):
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            record_frozen_result(self.store, attempt_id=ATTEMPT,
                                 sealed=self.result())
        self.assertIn("recorded against a requested freeze",
                      caught.exception.message)


# -- the store carries what this build writes --------------------------------

class TheStoreKnowsItsOwnShape(OutputCase):

    def test_the_three_tables_are_declared(self):
        for table in ("manifests", "outputs", "output_artifacts"):
            self.assertIn(table, schema.TABLES)

    def test_the_schema_version_moved_with_the_shape(self):
        """Past seven: a store written before the retained manifests and the
        frozen result existed cannot be adopted by a build that requires
        them. Which number the newest shape is at is the newest slice's fact,
        and `test_store` pins that the store records this constant."""
        self.assertGreater(schema.SCHEMA_VERSION, 7)

    def test_one_frozen_result_per_attempt(self):
        """A table that could hold two would make "which of these is this
        attempt's result" a question with no answer a manager may guess at."""
        self.frozen()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        with self.assertRaises(sqlite3.IntegrityError):
            beside.execute(
                "INSERT INTO outputs (runtime_attempt_id, result_id, "
                "disposition, manifest_digest, freeze_operation_id, frozen_at)"
                " VALUES (?, 'result-2', 'completed', 'sha256:x', 'op', ?)",
                (ATTEMPT, NOW))

    def test_a_persisted_disposition_this_contract_never_had_is_refused(self):
        """The store is a receiving trust domain: this process did not write
        the bytes it is reading."""
        self.frozen()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("PRAGMA ignore_check_constraints = ON")
        beside.execute("UPDATE outputs SET disposition = 'accepted'")
        beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            frozen_output_of(self.store, ATTEMPT)
        self.assertEqual(caught.exception.code, "schema")


if __name__ == "__main__":
    unittest.main()
