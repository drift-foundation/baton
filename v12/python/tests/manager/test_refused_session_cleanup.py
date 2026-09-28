"""W32576 — a refused handshake, carried all the way to the ending.

`settle_unsupported_version` derives the refusal from the persisted session's
own certified profile, records it, and fences the assignment at the authority.
That is where this Work stopped for four rounds, and the review said so
correctly each time: a `cancel-requested` axis and a stop order are not an
ending.  This suite is the rest of it -- exact force-removal, positive absence,
credential and launch settlement, and the lane given back only after all three.

WHY THE ENDING NEEDED A THIRD DOOR, measured rather than argued.
`authorize_cleanup`'s whole authorization is an intake receipt; `request_intake`
needs a frozen result; `request_freeze` needs a terminal worker disposition
already recorded.  A handshake this manager could not complete produces none of
them, and writing a disposition to open that door would be a fabrication AND a
lie: the worker did not cancel, complete or reject a plan -- it never got to
say anything.  `authorize_failed_start_cleanup` is the other non-receipt
ending and it is not this one: a start that failed and a handshake that refused
are different facts with different records, and W34998's ruling makes the
member sets closed against each other precisely so one authorization cannot be
spent on the other's ending.

WHAT AUTHORIZES THIS ONE is the manager's own durable
`session.unsupported-version` record, read back from the journal it was written
to.  Every case below drives one part of the order: fence at the authority,
remove the exact attached runtime, positively observe absence, settle the
delivery roots, LEAVE the untrusted result directory where it is, end at
`retained`, and only then release the lane.
"""

import os
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import (authorize_refused_session_cleanup,
                                      documents, handshake, lanes,
                                      settle_unsupported_version)

from .test_attempts import ATTEMPT
from .test_sessions import Agent, SessionCase

RETENTION = "sha256:" + "7" * 64
OTHER_POLICY = "sha256:" + "8" * 64


class Custodian:
    """W32576's capability, and ONLY it.

    An adapter carrying `destroy` would let this crossing reach the
    receipt-authorized path, and one carrying `destroy_failed_start` would let
    it reach the other non-receipt ending.  A fixture that offered all three
    would make every case below silent about which door was opened.
    """

    # W43975: the typed directory-custody seam this ending now settles on.
    custodian_image_digest = "sha256:" + "c" * 64

    def surviving_helpers(self, store, *, assignment_id, seconds=None,
                          reclaim=None):
        """W285465: THE SEAM THIS ENDING REQUIRES NOW.

        OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 removes the normalization launches from the
        refused-session ending, so what it proves at entry and establishes its roots'
        quiescence with is this observation. The double answers the EMPTY OBSERVATION -- a
        list, the shape the crossing validates -- because these cases are about the ending's
        authority and not about surviving helpers.
        """
        self.listed.append(assignment_id)
        return []

    def normalize_directory(self, store, *, assignment_id, which):
        from baton_v12.worker_manager import custody

        self.normalized.append((assignment_id, which))
        return custody._answered(
            "normalize", 0,
            # W275774: THE `submission` MEMBER, which this double predates. The
            # custody act's answer carries the submission it normalized under, and
            # `custody._accountable` refuses an answer without one -- so a double
            # that omits it makes every ending here refuse for want of an
            # accountable act rather than for the reason its case is about. The
            # intake suite's own custodian already answers it; this is the same
            # value, spelled the same way.
            {"custody": "normalize", "submission": "0" * 32,
             "entries": 0, "not_ours": 0,
             "running_as": [0, 0]}, None)

    def __init__(self, **overrides):
        self.normalized = []
        self.listed = []
        self.commands = []
        self.overrides = overrides

    def destroy_refused_session(self, command):
        self.commands.append(dict(command))
        return {"runtime_id": command["runtime_id"],
                "state": "absent",
                "why": "the engine answered that this exact identity does "
                       "not exist",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "not-delivered"},
                **self.overrides}


class RefusedSessionCase(SessionCase):

    def refused(self, attempt_id=ATTEMPT, version=9, **overrides):
        """A live execution session whose handshake this manager refuses."""
        self.opened(attempt_id=attempt_id)
        self.adapter = self.with_runtime(attempt_id)
        self.reference = dict(self.live(attempt_id=attempt_id), **overrides)
        return settle_unsupported_version(
            self.store, self.port, Agent(), self.adapter,
            session_ref=self.reference, agent_protocol_version=version)

    def ended(self):
        """THE ASSIGNMENT IS OVER, which this ending requires before it runs."""
        self.session.live_assignment = None

    def settled(self, custodian=None, *, reference=None, policy=RETENTION):
        return authorize_refused_session_cleanup(
            self.store, self.port, custodian or Custodian(),
            session_ref=reference or self.reference,
            retention_policy_digest=policy)

    def row(self, attempt_id=ATTEMPT):
        return self.store._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone()

    def corrupt(self, operation_id, **columns):
        assignments = ", ".join(f"{column} = ?" for column in columns)
        self.store._connection.execute(
            f"UPDATE operations SET {assignments} WHERE operation_id = ?",
            (*columns.values(), operation_id))

    def record_id(self):
        return handshake.unsupported_version_operation_id(self.reference)


class TheRefusedHandshakeReachesTheEnding(RefusedSessionCase):

    def test_the_ending_is_retained_and_nothing_was_fabricated(self):
        """THE ACCEPTANCE, in one case.

        No caller wrote a worker disposition and no output was frozen, and the
        cleanup axis still reaches a terminal ending.
        """
        self.refused()
        self.ended()
        answered = self.settled()
        self.assertEqual(answered["cleanup"], "retained")
        self.assertEqual(answered["state"], "absent")
        self.assertEqual(self.row()["cleanup"], "retained")
        self.assertEqual(self.row()["execution_runtime"], "destroyed")
        # THE TWO THINGS THIS ENDING MUST NEVER TOUCH.
        self.assertEqual(self.row()["worker_disposition"], "none")
        self.assertEqual(self.row()["output"], "open")

    def test_no_intake_receipt_exists_and_none_is_invented(self):
        """The whole reason this door exists, asserted rather than assumed."""
        self.refused()
        self.ended()
        self.settled()
        for table, column in (("intakes", "runtime_attempt_id"),
                              ("outputs", "runtime_attempt_id"),
                              ("intake_artifacts", "runtime_attempt_id"),
                              ("retentions", "runtime_attempt_id")):
            held = self.store._connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} = ?",
                (ATTEMPT,)).fetchone()[0]
            self.assertEqual(held, 0, table)

    def test_the_record_is_what_authorizes_it(self):
        """Not a receipt and not a failure record, and the body says which."""
        self.refused()
        self.ended()
        custodian = Custodian()
        self.settled(custodian)
        body = custodian.commands[0]
        self.assertNotIn("intake_receipt_digest", body)
        self.assertNotIn("failed_start_record_digest", body)
        self.assertEqual(sorted(body),
                         sorted(documents.REFUSED_SESSION_DESTROY_COMMAND
                                + ("operation",)))
        # THE DIGEST IS OVER THE DECODED RECORD, not over whatever bytes the
        # journal happens to store it as.
        _, committed = self.store.replay(
            self.record_id(),
            self.store.operation_record(self.record_id())["signature"],
            kind="session.unsupported-version")
        self.assertEqual(body["refusal_record_digest"], digest(committed))

    def test_the_exact_attached_runtime_is_what_is_removed(self):
        self.refused()
        self.ended()
        custodian = Custodian()
        self.settled(custodian)
        self.assertEqual(custodian.commands[0]["runtime_id"],
                         self.row()["runtime_id"])
        self.assertEqual(custodian.commands[0]["runtime_attempt_id"], ATTEMPT)

    def test_the_lane_is_given_back_only_by_the_settled_ending(self):
        """Reuse is ordered BEHIND the proof, not beside it."""
        self.refused()
        self.ended()
        self.assertTrue(lanes.runtime_lane(
            self.store, ATTEMPT)["held_by_this_attempt"])
        self.settled()
        self.assertFalse(lanes.runtime_lane(
            self.store, ATTEMPT)["held_by_this_attempt"])


class TheEndingIsFencedBeforeAnythingIsDestroyed(RefusedSessionCase):

    def test_a_live_assignment_refuses_before_the_adapter(self):
        """The authority is ASKED, not inferred from an axis."""
        self.refused()
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("still the live assignment", caught.exception.message)
        self.assertEqual(custodian.commands, [])
        self.assertEqual(self.row()["cleanup"], "pending")

    def test_a_terminal_cleanup_is_not_revisited(self):
        self.refused()
        self.ended()
        self.settled()
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian, policy=OTHER_POLICY)
        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertEqual(custodian.commands, [])

    def test_an_uncertain_runtime_is_never_inferred_absent(self):
        """The frozen asymmetry both siblings are under."""
        self.refused()
        self.ended()
        from baton_v12.worker_manager import observe
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="uncertain")
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertEqual(custodian.commands, [])


class TheRecordIsOwnedBeforeItIsBelieved(RefusedSessionCase):

    def test_a_refusal_with_no_attached_runtime_records_nothing(self):
        """The record must NAME the runtime it will authorize destroying.

        W32648 review [P0] on the other ending: an authorization and a command
        built from two independently read facts combine into one act. So the
        record carries the attached identity -- and a session with nothing
        attached has no such record to write. Found by the mutation harness,
        which measured this guard at ZERO on its first run: I added the check
        and wrote no case that drove it.
        """
        self.opened()
        self.reference = self.live()
        with self.assertRaises(ContractRefusal) as caught:
            settle_unsupported_version(
                self.store, self.port, Agent(), None,
                session_ref=self.reference, agent_protocol_version=9)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("no attached runtime", caught.exception.message)
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM operations WHERE kind = ?",
            ("session.unsupported-version",)).fetchone()[0], 0)

    def test_a_session_that_never_refused_has_nothing_to_end(self):
        self.opened()
        self.with_runtime()
        self.reference = self.live()
        self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("no recorded", caught.exception.message)

    def test_a_row_of_another_kind_authorizes_nothing(self):
        """A derived identity means what sits at it must be asked."""
        self.refused()
        self.ended()
        self.corrupt(self.record_id(), kind="session.something-else")
        with self.assertRaises(ContractRefusal) as caught:
            self.settled()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("another kind", caught.exception.message)

    def test_a_record_naming_another_runtime_authorizes_nothing(self):
        """W32648 review [P0], on this ending.

        A record written while the session spoke to one container must not
        authorize destroying a different one. The RECORD is what moves here:
        editing the attempt instead would move the operation identity with it
        and prove nothing about the comparison, which is what my first version
        of this case did -- the mutation harness measured the guard at ZERO and
        the case still passed, on a refusal raised somewhere else entirely.
        """
        import json
        self.refused()
        self.ended()
        held = self.store.operation_record(self.record_id())
        record = json.loads(held["result"])
        self.corrupt(self.record_id(),
                     result=json.dumps({**record,
                                        "runtime_id": "runtime-elsewhere"}))
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("must describe one runtime and one session",
                      caught.exception.message)
        self.assertEqual(custodian.commands, [])

    def test_a_record_naming_another_session_authorizes_nothing(self):
        """The session members too, and for the same reason.

        The record is filed under the session act, so a row whose own bytes
        name a different epoch is a row about somebody else's handshake.
        """
        import json
        self.refused()
        self.ended()
        held = self.store.operation_record(self.record_id())
        record = json.loads(held["result"])
        for member, wrong in (("session_epoch", 7), ("posture", "consent"),
                              ("provider_session_id", "another-session"),
                              ("attempt_id", "attempt-elsewhere")):
            with self.subTest(member=member):
                self.corrupt(self.record_id(),
                             result=json.dumps({**record, member: wrong}))
                custodian = Custodian()
                with self.assertRaises(ContractRefusal) as caught:
                    self.settled(custodian)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))
                self.assertIn(member, caught.exception.message)
                self.assertEqual(custodian.commands, [])

    def edited(self, **members):
        """The committed record with exactly these members changed.

        The member SET is preserved, so the document owner still accepts it
        and the probe reaches the rule it is about rather than the envelope.
        """
        import json
        held = self.store.operation_record(self.record_id())
        record = json.loads(held["result"])
        self.corrupt(self.record_id(),
                     result=json.dumps({**record, **members}))

    def test_the_whole_closed_verdict_is_required_not_one_member(self):
        """Review [P1], and all three members rather than the obvious one.

        `refused` is a category shared with every other refusal this manager
        raises, and `unsupported-version` in `decision` is a word a record can
        carry while its typed pair says something else. The three agree or the
        record is not the document its kind promises.
        """
        for member, wrong in (("decision", "accepted"),
                              ("category", "policy"),
                              ("code", "profile-uncertified")):
            with self.subTest(member=member):
                self.refused()
                self.ended()
                self.edited(**{member: wrong})
                custodian = Custodian()
                with self.assertRaises(ContractRefusal) as caught:
                    self.settled(custodian)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))
                self.assertIn(member, caught.exception.message)
                self.assertEqual(custodian.commands, [])
                self.tearDown()
                self.setUp()

    def test_a_version_pair_that_agrees_is_a_successful_negotiation(self):
        """The refusal's own evidence has to still be a refusal's.

        An unsupported-version answer is exactly a wire version that is NOT
        the pinned one, so two integers that agree describe a negotiation that
        SUCCEEDED and authorize nothing.
        """
        self.refused()
        self.ended()
        self.edited(agent_protocol_version=1, pinned_wire_version=1)
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("negotiation that SUCCEEDED", caught.exception.message)
        self.assertEqual(custodian.commands, [])

    def test_a_wire_version_that_is_not_an_integer_authorizes_nothing(self):
        self.refused()
        self.ended()
        self.edited(agent_protocol_version="nine")
        with self.assertRaises(ContractRefusal) as caught:
            self.settled()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("a wire version is an integer",
                      caught.exception.message)

    def test_a_refusal_about_another_profile_is_not_this_sessions(self):
        self.refused()
        self.ended()
        self.edited(profile_digest="sha256:" + "e" * 64)
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("is not evidence about this session",
                      caught.exception.message)
        self.assertEqual(custodian.commands, [])

    def test_the_verdict_is_read_off_retained_evidence_not_certification(self):
        """The check must not re-read certification, and this proves it does
        not: the profile is WITHDRAWN and the ending still settles.

        Reading certification here would make an exact retry stop working the
        moment a profile was withdrawn -- the effectively-once defect this
        Work already corrected once on the recording side, reintroduced at the
        reading one.
        """
        self.refused()
        self.ended()
        self.store._connection.execute(
            "DELETE FROM profiles WHERE digest = ?", (self.digest,))
        # WITHDRAWN FOR REAL: the reader that mints a refusal now finds
        # nothing, which is the state this case is about.
        from baton_v12.worker_manager import certified_agent_session_profile
        self.assertIsNone(
            certified_agent_session_profile(self.store, self.digest))
        self.assertEqual(self.settled()["cleanup"], "retained")

    def test_a_record_of_another_shape_is_not_read_for_an_authorization(self):
        import json
        self.refused()
        self.ended()
        self.corrupt(self.record_id(),
                     result=json.dumps({"attempt_id": ATTEMPT}))
        with self.assertRaises(ContractRefusal) as caught:
            self.settled()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_a_record_that_no_longer_says_unsupported_version_authorizes_nothing(
            self):
        """The authorizing body must still be the refusal its kind promises.

        `decision`, `category` and `code` are retained specifically so a later
        cleanup reader does not infer them from the operation name. A document
        whose shape and runtime/session identities still agree but whose own
        decision says something else is not an unsupported-version record and
        must not be reduced to a digest and spent on destruction.
        """
        import json
        self.refused()
        self.ended()
        held = self.store.operation_record(self.record_id())
        record = json.loads(held["result"])
        self.corrupt(self.record_id(),
                     result=json.dumps({**record, "decision": "accepted"}))
        custodian = Custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertEqual(custodian.commands, [])


class TheObservationDecidesTheEnding(RefusedSessionCase):

    def test_an_uncertain_observation_settles_nothing(self):
        self.refused()
        self.ended()
        answered = self.settled(Custodian(state="uncertain",
                                          why="the engine did not answer"))
        self.assertEqual(answered["state"], "uncertain")
        self.assertEqual(self.row()["cleanup"], "pending")
        self.assertTrue(lanes.runtime_lane(
            self.store, ATTEMPT)["held_by_this_attempt"])

    def test_an_unsettled_provider_root_is_not_a_finished_cleanup(self):
        """Positive container absence is not the whole ending."""
        self.refused()
        self.ended()
        answered = self.settled(Custodian(
            launch={"lifecycle_state": "unresolved"}))
        self.assertIn("teardown is not settled", answered["why"])
        # The runtime really is gone and that observation stands; it is
        # CLEANUP that has not finished.
        self.assertEqual(self.row()["execution_runtime"], "destroyed")
        self.assertEqual(self.row()["cleanup"], "pending")
        self.assertTrue(lanes.runtime_lane(
            self.store, ATTEMPT)["held_by_this_attempt"])

    def test_an_adapter_answering_about_another_runtime_is_refused(self):
        self.refused()
        self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(Custodian(runtime_id="runtime-elsewhere"))
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_a_removal_that_did_not_remove_ends_failed(self):
        self.refused()
        self.ended()
        answered = self.settled(Custodian(state="running",
                                          why="it is still running"))
        self.assertEqual(answered["cleanup"], "failed")
        self.assertEqual(self.row()["cleanup"], "failed")


class TheEndingIsEffectivelyOnce(RefusedSessionCase):

    def test_an_exact_retry_replays_the_one_removal(self):
        self.refused()
        self.ended()
        first = self.settled()
        custodian = Custodian()
        again = self.settled(custodian)
        self.assertEqual(again, first)
        # THE ADAPTER IS NOT CALLED AGAIN: a retry replays an act that already
        # happened rather than performing it a second time.
        self.assertEqual(custodian.commands, [])
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM operations WHERE kind = ?",
            ("runtime.destroy-refused-session",)).fetchone()[0], 1)

    def test_a_retry_survives_a_newly_opened_store(self):
        """A restart is a new process reading the same file."""
        from baton_v12.worker_manager import ControlStore
        from .test_offers import NOW
        self.refused()
        self.ended()
        first = self.settled()
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation="manager-2",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        self.assertEqual(self.settled(), first)

    def test_another_retention_policy_is_another_act(self):
        """Destroying under a different policy is a different removal, so it
        does not replay the first one's answer."""
        self.refused()
        self.ended()
        self.settled()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(policy=OTHER_POLICY)
        self.assertEqual(caught.exception.code, "already-terminal")


class TheDoorsStayClosedAgainstEachOther(RefusedSessionCase):

    def test_an_adapter_without_this_capability_is_refused(self):
        class Wrong:
            def destroy(self, command):
                raise AssertionError("the receipt-authorized path was reached")

            def destroy_failed_start(self, command):
                raise AssertionError("the failed-start path was reached")

        self.refused()
        self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(Wrong())
        self.assertIn("refused-session destroy", caught.exception.message)

    def test_this_command_is_not_a_failed_start_command(self):
        """The member sets are closed AGAINST each other."""
        from baton_v12.worker_manager import oci
        with self.assertRaises(ContractRefusal):
            documents.refused_session_destroy_command(
                assignment_ref={}, runtime_attempt_id=ATTEMPT,
                runtime_id="runtime-1",
                failed_start_record_digest=RETENTION,
                retention_policy_digest=RETENTION)
        self.assertNotIn("failed_start_record_digest",
                         documents.REFUSED_SESSION_DESTROY_COMMAND)
        self.assertNotIn("refusal_record_digest",
                         documents.FAILED_START_DESTROY_COMMAND)
        self.assertNotIn("refusal_record_digest", documents.DESTROY_COMMAND)
        self.assertTrue(hasattr(oci.OciAdapter, "destroy_refused_session"))


class ReuseIsOrderedBehindTheEnding(RefusedSessionCase):
    """W32649's rule, and this ending is what satisfies it.

    A successor over the same Work does not start while this attempt's
    runtime, deliveries or custody are unsettled -- the authority releases its
    claim slot before this manager's cleanup finishes, and the gap between the
    two is where two executions over one assignment's material would overlap.
    A refused handshake used to leave exactly that gap open forever: the lane
    was held by an attempt whose ending had no door.
    """

    def successor(self):
        """The NEXT generation over the same Work, prepared exactly as the
        first was: the authority has issued and this manager has claimed a new
        assignment, and only the unfinished cleanup stands between it and the
        engine."""
        from baton_v12.worker_manager import (accept_offer,
                                              activate_assignment, issue_offer,
                                              record_attempt,
                                              request_runtime_start,
                                              submit_claim)
        from .test_attempts import ADAPTER
        from .test_offers import NOW, PROFILE, UUID, WHO, WORK
        from .test_sessions import Adapter
        expect = {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                  "participant": WHO, "generation": 2}
        self.session.live_assignment = dict(expect)
        self.session.claim_answer = {**self.session.claim_answer,
                                     "assignment": dict(expect)}
        if self.row("attempt-successor") is None:
            issue_offer(self.store, self.port, offer_id="offer-successor",
                        work_id=WORK, runtime_attempt_id="attempt-successor",
                        input_digest="sha256:" + "1" * 64,
                        policy_digest="sha256:" + "2" * 64,
                        profile_digest=PROFILE, profile_name="reference",
                        mint_bearer=lambda: "bearer-successor")
            accept_offer(self.store, self.port, offer_id="offer-successor",
                         decision="accept", bearer="bearer-successor", now=NOW,
                         runtime_attempt_id="attempt-successor",
                         work_ref={"authority_uuid": UUID, "work_id": WORK})
            record_attempt(self.store, attempt_id="attempt-successor",
                           adapter_name="acp", adapter_digest=ADAPTER,
                           profile_digest=PROFILE,
                           policy_digest="sha256:" + "2" * 64)
            submit_claim(self.store, self.port, offer_id="offer-successor")
            activate_assignment(self.store, self.port,
                                attempt_id="attempt-successor", expect=expect)
        started = request_runtime_start(self.store, Adapter(),
                                        attempt_id="attempt-successor")
        self.ended()
        return started

    def test_a_successor_waits_for_this_ending_and_then_proceeds(self):
        self.refused()
        self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.successor()
        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.settled()
        # AND NOW IT MAY, because the lane was given back by an ending that
        # proved absence and settled every delivered root first.
        self.assertIsNotNone(self.successor())

    def test_an_unsettled_ending_does_not_release_the_lane(self):
        """The half-finished ending is the one that matters: the runtime is
        gone and a delivered root is not, so reuse stays closed."""
        self.refused()
        self.ended()
        self.settled(Custodian(launch={"lifecycle_state": "unresolved"}))
        with self.assertRaises(ContractRefusal):
            self.successor()


if __name__ == "__main__":
    unittest.main()


class TheRefusedSessionEndingSurvivesInterruption(RefusedSessionCase):
    """W43975's public-ending matrix, for the refused-handshake sibling."""

    def interrupted(self, fail_on=None):
        from baton_v12.worker_manager import custody

        adapter = Custodian()

        def normalize_directory(store, *, assignment_id, which):
            adapter.normalized.append((assignment_id, which))
            if which == fail_on:
                raise RuntimeError(f"the helper died over {which}")
            return custody._answered(
                "normalize", 0,
                # W275774: the `submission` member the custody act answers with; a double
                # that omits it makes every ending refuse for want of an accountable act.
                {"custody": "normalize", "submission": "0" * 32,
                 "entries": 0, "not_ours": 0,
                 "running_as": [0, 0]}, None)

        def surviving_helpers(store, *, assignment_id, seconds=None,
                              reclaim=None):
            # W285465: the act this ending performs now, and the one that can die.
            adapter.listed.append(assignment_id)
            if fail_on == "listing":
                raise RuntimeError("the engine died while listing writers")
            return []

        adapter.normalize_directory = normalize_directory
        adapter.surviving_helpers = surviving_helpers
        return adapter

    def committed(self, answered):
        from baton_v12.worker_manager import intake

        return intake.historical_writer_cessation(self.store,
                                                  answered["operation"])

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

    def test_the_ending_binds_both_receipts_and_replays_them(self):
        self.refused()
        self.ended()
        adapter = self.interrupted()

        answered = self.settled(adapter)

        # W285465 under OWNER-NO-AUTOMATIC-NORMALIZATION-20260928: no helper ran, and the
        # ending binds the establishment it committed. The property -- an ending binds the
        # account of its roots and replays without acting again -- is unchanged.
        self.assertEqual(adapter.normalized, [],
                         "the ending launched a normalization helper")
        self.assertEqual(adapter.listed, [ATTEMPT])
        self.assertIsNone(answered["directory_custody"])
        self.assertIsNotNone(self.committed(answered),
                             "the ending committed no establishment")
        self.assertEqual(self.settled(adapter), answered,
                         "the settled ending did not replay")

    def test_an_interrupted_ESTABLISHMENT_commits_no_ending_and_resumes(self):
        self.refused()
        self.ended()
        dying = self.interrupted(fail_on="listing")

        with self.assertRaises(RuntimeError):
            self.settled(dying)
        self.assertEqual(self.attempt_row()["cleanup"], "pending",
                         "an ending was claimed on an unfinished establishment")

        resumed = self.interrupted()
        answered = self.settled(resumed)

        self.assertEqual(answered["cleanup"], "retained")
        self.assertEqual(resumed.normalized, [],
                         "the resumed ending launched a helper")
        self.assertIsNotNone(self.committed(answered))

    def test_a_SURVIVING_writer_refuses_this_ending_too(self):
        """This family's positive-cessation control."""
        self.refused()
        self.ended()
        adapter = self.interrupted()
        adapter.surviving_helpers = lambda store, *, assignment_id, \
            seconds=None, reclaim=None: [
                {"helper_identity": "baton-custody-" + "a" * 32,
                 "why": "the engine listed this helper as running"}]
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(adapter)
        self.assertIn("still survives", str(caught.exception))
        self.assertEqual(self.attempt_row()["cleanup"], "pending")

    def test_an_UNREADABLE_listing_answer_is_RECORDED_and_does_not_hold(self):
        # W285465 under OWNER-SIMPLE-COMPLETION-20260928: SUPERSEDED. Confined container
        # cessation proves the confined writers stopped, so neither a missing listing nor an
        # unreadable answer holds this ending; what the record must not do is claim the listing
        # established anything.
        self.refused()
        self.ended()
        adapter = self.interrupted()
        adapter.surviving_helpers = lambda store, *, assignment_id, \
            seconds=None, reclaim=None: None
        answered = self.settled(adapter)
        self.assertEqual(answered["cleanup"], "retained")
        ceased = self.committed(answered)
        self.assertEqual(ceased["established"], "container-cessation")
        self.assertIn("not an observation this manager can read",
                      ceased["listing"])

    def test_a_deployment_that_CANNOT_LIST_is_refused_before_the_destroy(self):
        """REPLACES the changed-custodian collision on this path.

        W285465: that case swapped the custodian image between two normalization acts, and
        this ending performs none. What the seam rule still says is that the capability this
        ending USES is proved before any destructive work, so a deployment that cannot list
        is refused and nothing is destroyed. The historical collision rule itself is unchanged
        where normalization is still performed, in `test_custody`.
        """
        self.refused()
        self.ended()
        adapter = self.interrupted()
        adapter.surviving_helpers = None
        # W285465 under OWNER-SIMPLE-COMPLETION-20260928: SUPERSEDED -- a deployment that
        # offers no listing COMPLETES on the container's own cessation. What is still refused
        # before any destructive work is a listing that is OFFERED and cannot be used.
        answered = self.settled(adapter)
        self.assertEqual(answered["cleanup"], "retained")
        adapter = self.interrupted()
        adapter.surviving_helpers = "not a callable"
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(adapter)
        self.assertIn("writer-listing act", str(caught.exception))

    def test_the_home_is_retained_rather_than_removed(self):
        self.refused()
        self.ended()
        # W285465: THE ROOTS ARE ALLOCATED THE WAY THE HOST ALLOCATES THEM, not composed by
        # hand. The ending establishes that its output is readable by the configured workspace
        # group, and a directory this fixture invented is not a root this manager can account
        # for -- measured, and it is the allocator that owns those modes and that group.
        from baton_v12.worker_manager import workspaces as _workspaces
        from tests.manager import input_roots as _input_roots

        home = os.path.join(self.storage, ATTEMPT)
        _workspaces.assignment_workspace(
            _input_roots.configured_group(self.store), self.storage, ATTEMPT)

        self.settled(self.interrupted())

        self.assertTrue(os.path.isdir(os.path.join(home, "workspace")),
                        "a recordless ending removed the material it retained")
