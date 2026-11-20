"""W385331 — the durable attributed Work message, and what it refuses.

THE FIRST VERTICAL NATIVE COMMUNICATION PATH, at the authority that attributes
it. An implementer stops at a question, the host commits that question UNDER
the implementer's own exact assignment, the configured reviewer answers it
within accepted scope or escalates it once to the configured decision
recipient, and the ownership effect either reply earns is recorded apart from
the text.

WHAT IS REAL HERE. The store, the Work, the route, the claim, the capability
grant, the policy and the operation journal are the accepted ones. There is no
fake authority, no second journal and no stub: every case below drives
`Authority` and its minted sessions.

WHAT IS DELIBERATELY ABSENT. No candidate is published, no receipt of any kind
is written, and no verdict exists anywhere in this file -- which is the point
rather than an omission: a text message never transfers ownership and never
approves code, and the vocabulary these transitions carry has no word for
either.

Every store is this fixture's own temporary file. No deployment, no engine, no
provider, no network, no model.
"""

import json
import os
import tempfile
import unittest

from baton_v12 import native_handoff
from baton_v12.authority import Authority, Refusal
from baton_v12.authority import messages
from baton_v12.authority.schema import SCHEMA_VERSION

UUID = "0123456789abcdef0123456789abcdef"
WORK = UUID[:8] + "-W1"
OTHER_WORK = UUID[:8] + "-W2"
V12 = "baton.v12.contract/1"

IMPLEMENTER = "baton.claude-native"
REVIEWER = "baton.reviewer-native"
RECEIPT_ACTOR = "baton.reviewer-receipt-native"
OWNER = "baton.slaw"
STRANGER = "baton.someone-else"

TASK = "sha256:" + "9" * 64
CONTINUATION = "sha256:" + "2" * 64
HEAD = "b" * 40
CHECKPOINT = "checkpoint-line-1-1"


def request_document(body="which of the two readings is in scope?",
                     recipient=REVIEWER, kind=native_handoff.CLARIFICATION_KIND,
                     head=HEAD):
    """One worker's own request document, in the bounded handoff contract."""
    return {"schema": native_handoff.HANDOFF_SCHEMA, "kind": kind,
            "body": body,
            "evidence": [{"reference": "v12/python/src/baton_v12/x.py",
                          "digest": "sha256:" + "1" * 64,
                          "note": "the line the question is about"}],
            "continuation": {"reference": "line-1", "digest": CONTINUATION},
            "checkpoint": {"reference": head, "digest": "sha256:" + "3" * 64},
            "recipient": recipient}


def response_document(request_id, request_digest, *, disposition="answer",
                      checkpoint=CHECKPOINT, escalation=None):
    return {"schema": native_handoff.HANDOFF_SCHEMA,
            "kind": native_handoff.RESPONSE_KIND,
            "request": {"reference": request_id, "digest": request_digest},
            "disposition": disposition,
            "body": ("the second reading is the admitted one"
                     if disposition == "answer"
                     else "this needs an owner decision"),
            "rationale": "within the accepted scope of the admitted task",
            "evidence": [],
            "checkpoint": {"reference": checkpoint,
                           "digest": "sha256:" + "3" * 64},
            "escalation": escalation}


ESCALATION = {"ambiguity": "the specification admits two incompatible bases",
              "options": ["take the narrower base", "take the wider base"],
              "recommendation": "take the narrower base and file the rest"}


class MessageCase(unittest.TestCase):
    """One authority, one Work, one claimed implementer, one granted reviewer."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-work-messages-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID)
        self.addCleanup(self.authority.dispose)
        self.authority.create_work(WORK, "impl", operation_id="op-create",
                                   contract=V12)
        self.authority.add_route_handler("impl", IMPLEMENTER)
        self.routed()
        self.scope = self.authority.project_work(WORK)["scope"]
        self.authority.grant_capability(REVIEWER, messages.ANSWER_CAPABILITY,
                                        scope=self.scope)
        self.implementer = self.authority.session(IMPLEMENTER)
        self.reviewer = self.authority.session(REVIEWER)
        self.expect = self.implementer.claim(
            {"work_id": WORK, "operation_id": "op-claim"})["assignment"]

    def routed(self, reviewer=REVIEWER, recipient=OWNER):
        self.authority.set_policy(messages.ROUTING_POLICY, {
            "schema": messages.ROUTING_SCHEMA, "reviewer": reviewer,
            "decision_recipient": recipient})

    # -- the two acts, as the host performs them ---------------------------

    def asked(self, *, document=None, message_id="msg-1",
              operation_id="op-ask", session=None, expect=None,
              job_id="job-a", checkpoint=CHECKPOINT, task=TASK,
              destination=None, handoff_digest=None, kind=None,
              continuation=CONTINUATION):
        held = request_document() if document is None else document
        return (session or self.implementer).request_handoff({
            "expect": expect if expect is not None else self.expect,
            "operation_id": operation_id, "message_id": message_id,
            "job_id": job_id, "kind": kind or held["kind"], "body": held,
            "handoff_digest": (handoff_digest if handoff_digest is not None
                               else native_handoff.handoff_digest(held)),
            "task_digest": task, "checkpoint_ref": checkpoint,
            "continuation_digest": continuation,
            "destination": destination or held["recipient"]})

    def answered(self, request=None, *, disposition="answer",
                 message_id="msg-2", operation_id="op-answer", session=None,
                 document=None, checkpoint=None, effect=None,
                 request_digest=None, reply_to=None, work_id=WORK,
                 job_id="job-a"):
        request = self.asked() if request is None else request
        held = document if document is not None else response_document(
            request["message_id"], request["handoff_digest"],
            disposition=disposition,
            escalation=ESCALATION if disposition == "escalate" else None)
        return (session or self.reviewer).answer_handoff({
            "operation_id": operation_id, "message_id": message_id,
            "reply_to": reply_to or held["request"]["reference"],
            "disposition": ("response" if disposition == "answer"
                            else "escalation"),
            "body": held,
            "handoff_digest": native_handoff.handoff_digest(held),
            "request_digest": (request_digest if request_digest is not None
                               else held["request"]["digest"]),
            "checkpoint_ref": (checkpoint if checkpoint is not None
                               else held["checkpoint"]["reference"]),
            "effect": effect or ("continuation" if disposition == "answer"
                                 else "held"),
            "detail": {"disposition": disposition},
            # THE WORK AND THE JOB THE REPLY ANSWERS FOR (review
            # 2026-11-20T19-39-15Z R3): the host names the review
            # assignment's own, and the Authority holds the request to them.
            "work_id": work_id, "job_id": job_id})

    def refusal(self, call, *operands, **named):
        with self.assertRaises(Refusal) as caught:
            call(*operands, **named)
        return str(caught.exception)


class ARequestIsAttributedToItsOwnAssignment(MessageCase):
    """The attribution is the authority's, and a worker supplies none of it."""

    def test_the_author_generation_and_claim_come_from_the_binding(self):
        held = self.asked()
        self.assertEqual(held["author"], IMPLEMENTER)
        self.assertEqual(held["generation"], self.expect["generation"])
        self.assertEqual(held["kind"], native_handoff.CLARIFICATION_KIND)
        self.assertEqual(held["work_id"], WORK)
        self.assertEqual(held["job_id"], "job-a")
        # THE EXACT CLAIM EVENT, which is what makes the act attributable
        # rather than merely labelled -- the same reference `activity` and
        # `proposal` carry.
        events = [one for one in self.authority.assignment_events(WORK)
                  if one["cause"] == "claimed"]
        self.assertEqual(held["claim_seq"], events[-1]["seq"])

    def test_a_worker_cannot_name_an_author_because_there_is_no_operand(self):
        """Not "it is ignored": the transition REFUSES an identity operand, so
        a caller cannot believe one was honoured."""
        for forbidden in ("actor", "participant", "author"):
            said = self.refusal(
                lambda: self.implementer.request_handoff(dict(
                    {"expect": self.expect, "operation_id": "op-x",
                     "message_id": "m-x", "job_id": "job-a",
                     "kind": native_handoff.CLARIFICATION_KIND,
                     "body": request_document(),
                     "handoff_digest": "sha256:" + "4" * 64,
                     "task_digest": TASK, "checkpoint_ref": CHECKPOINT,
                     "continuation_digest": CONTINUATION,
                     "destination": REVIEWER},
                    **{forbidden: IMPLEMENTER})))
            self.assertIn("request_handoff", said)

    def test_the_retained_body_is_the_document_and_not_a_summary(self):
        """A store holding only the digest could prove a reply was about this
        request and could not say what the request WAS."""
        document = request_document()
        held = self.asked(document=document)
        self.assertEqual(held["body"], document)
        self.assertEqual(held["handoff_digest"],
                         native_handoff.handoff_digest(document))

    def test_the_checkpoint_continuation_and_task_are_all_preserved(self):
        held = self.asked()
        self.assertEqual(held["checkpoint_ref"], CHECKPOINT)
        self.assertEqual(held["continuation_digest"], CONTINUATION)
        self.assertEqual(held["task_digest"], TASK)

    def test_a_finding_request_is_its_own_kind_and_not_a_clarification(self):
        held = self.asked(document=request_document(
            kind=native_handoff.FINDING_KIND))
        self.assertEqual(held["kind"], native_handoff.FINDING_KIND)
        self.assertIn(held["kind"], messages.REQUEST_KINDS)

    def test_a_session_cannot_ask_under_somebody_elses_assignment(self):
        self.authority.add_route_handler("impl", STRANGER)
        stranger = self.authority.session(STRANGER)
        said = self.refusal(lambda: self.asked(session=stranger,
                                               message_id="m-s",
                                               operation_id="op-s"))
        self.assertIn("this session acts for", said)

    def test_a_stale_generation_cannot_ask_at_all(self):
        """The assignment compare-and-swap is the authorization, so an
        assignment that has been ended is not one a question can be asked
        under -- which is what stops a replayed worker from reopening a
        conversation."""
        self.implementer.end({"expect": self.expect, "operation_id": "op-end"})
        said = self.refusal(lambda: self.asked(message_id="m-stale",
                                               operation_id="op-stale"))
        self.assertIn("stale assignment", said)

    def test_a_foreign_authority_in_the_assignment_refuses(self):
        foreign = {"work_ref": {"authority_uuid": "f" * 32,
                                "work_id": WORK},
                   "participant": IMPLEMENTER, "generation": 1}
        said = self.refusal(lambda: self.asked(expect=foreign,
                                               message_id="m-f",
                                               operation_id="op-f"))
        self.assertIn("assignment names authority", said)


class ARequestIsAuthenticatedAgainstItsConfiguredDestinations(MessageCase):
    """"A request is authenticated against the requesting assignment and its
    configured allowed destinations.\""""

    def test_an_unconfigured_deployment_admits_no_request_at_all(self):
        """FAIL-CLOSED: an unconfigured destination is not "send it
        anywhere"."""
        self.authority.set_policy(messages.ROUTING_POLICY, None)
        said = self.refusal(lambda: self.asked())
        self.assertIn("configures no native handoff routing", said)
        self.assertEqual(self.authority.work_messages(WORK), [])

    def test_a_destination_other_than_the_configured_reviewer_refuses(self):
        said = self.refusal(lambda: self.asked(
            document=request_document(recipient=RECEIPT_ACTOR)))
        self.assertIn(RECEIPT_ACTOR, said)
        self.assertIn("configured reviewer", said)

    def test_a_receipt_actor_is_not_the_agent_that_answers_a_question(self):
        """`baton.reviewer-receipt-native` is a RECEIPT ACTOR, not the
        configured native reviewer, and this authority keeps the two apart
        even when a deployment grants the capability to both."""
        self.authority.grant_capability(
            RECEIPT_ACTOR, messages.ANSWER_CAPABILITY, scope=self.scope)
        request = self.asked()
        said = self.refusal(lambda: self.answered(
            request, session=self.authority.session(RECEIPT_ACTOR)))
        self.assertIn("answering it", said)
        self.assertIn(REVIEWER, said)

    def test_a_request_is_never_addressed_to_its_own_author(self):
        self.routed(reviewer=IMPLEMENTER)
        said = self.refusal(lambda: self.asked(
            document=request_document(recipient=IMPLEMENTER)))
        self.assertIn("own participant", said)

    def test_one_assignment_holds_one_unanswered_request(self):
        self.asked()
        said = self.refusal(lambda: self.asked(message_id="msg-1b",
                                               operation_id="op-ask-2"))
        self.assertIn("unanswered request", said)
        self.assertEqual(len(self.authority.work_messages(WORK)), 1)

    def test_a_second_question_is_admitted_once_the_first_is_answered(self):
        """The bound is on PENDING requests, which is what makes a resolved
        continuation able to ask again rather than being silenced."""
        first = self.asked()
        self.answered(first)
        held = self.asked(message_id="msg-3", operation_id="op-ask-3")
        self.assertEqual(held["message_id"], "msg-3")
        self.assertEqual([one["kind"] for one in
                          self.authority.work_messages(WORK)],
                         [native_handoff.CLARIFICATION_KIND, "response",
                          native_handoff.CLARIFICATION_KIND])

    def test_a_malformed_routing_policy_is_refused_at_the_read(self):
        for broken in ({"schema": "baton.other/1", "reviewer": REVIEWER,
                        "decision_recipient": OWNER},
                       {"schema": messages.ROUTING_SCHEMA,
                        "reviewer": REVIEWER},
                       {"schema": messages.ROUTING_SCHEMA,
                        "reviewer": REVIEWER, "decision_recipient": OWNER,
                        "extra": 1},
                       {"schema": messages.ROUTING_SCHEMA,
                        "reviewer": "not an address",
                        "decision_recipient": OWNER},
                       "a string"):
            with self.subTest(broken=broken):
                self.authority.set_policy(messages.ROUTING_POLICY, broken)
                with self.assertRaises(Refusal):
                    self.authority.native_routing()

    def test_one_address_for_both_roles_is_refused_as_configuration(self):
        """"Do not route `decision` back to that same reviewer under another
        label" -- refused where it is CONFIGURED rather than discovered at the
        escalation."""
        self.authority.set_policy(messages.ROUTING_POLICY, {
            "schema": messages.ROUTING_SCHEMA, "reviewer": REVIEWER,
            "decision_recipient": REVIEWER})
        said = self.refusal(self.authority.native_routing)
        self.assertIn("HIGHER authority", said)


class TheReplyIsBoundToTheExactPendingRequest(MessageCase):

    def test_an_answer_names_the_request_its_digest_and_its_checkpoint(self):
        request = self.asked()
        held = self.answered(request)
        reply = held["message"]
        self.assertEqual(reply["reply_to"], request["message_id"])
        self.assertEqual(reply["kind"], "response")
        self.assertEqual(reply["author"], REVIEWER)
        self.assertEqual(reply["checkpoint_ref"], request["checkpoint_ref"])
        self.assertEqual(reply["destination"], REVIEWER)
        # THE ADMITTED TASK AND THE CONTINUATION TRAVEL UNCHANGED, read off
        # the request rather than supplied by the reply: an answer is a
        # separate continuation input and never a new task.
        self.assertEqual(reply["task_digest"], request["task_digest"])
        self.assertEqual(reply["continuation_digest"],
                         request["continuation_digest"])

    def test_a_reply_answering_for_another_work_refuses(self):
        """R3. A grant in a Work's scope is not an invitation to answer every
        request that scope covers: the reply names the Work its own review
        assignment is fixed to, and a request of another Work refuses."""
        self.authority.create_work(OTHER_WORK, "impl", operation_id="op-other",
                                   contract=V12)
        self.authority.grant_capability(REVIEWER, messages.ANSWER_CAPABILITY,
                                        scope=self.scope)
        request = self.asked()
        said = self.refusal(lambda: self.answered(request, work_id=OTHER_WORK))
        self.assertIn("belongs to", said)
        self.assertIn("never another Work's", said)
        self.assertIsNone(self.authority.work_message_reply(
            request["message_id"]))
        self.assertEqual(len(self.authority.work_messages(WORK)), 1)
        self.assertEqual(self.authority.work_messages(OTHER_WORK), [])

    def test_a_reply_answering_for_another_job_refuses(self):
        request = self.asked()
        said = self.refusal(lambda: self.answered(request, job_id="job-b"))
        self.assertIn("was asked by Job", said)
        self.assertIsNone(self.authority.work_message_reply(
            request["message_id"]))
        self.assertIsNone(self.authority.work_message_transition("msg-2"))

    def test_the_work_and_job_answered_for_are_in_the_signed_operands(self):
        request = self.asked()
        first = self.answered(request)
        self.assertEqual(self.answered(request), first)
        said = self.refusal(lambda: self.answered(request, job_id="job-b"))
        self.assertIn("different operands", said)
        self.assertEqual(len(self.authority.work_messages(WORK)), 2)

    def test_the_reply_relation_is_readable_from_both_ends(self):
        request = self.asked()
        held = self.answered(request)
        self.assertEqual(
            self.authority.work_message_reply(request["message_id"]),
            held["message"])
        self.assertEqual(
            self.authority.work_message(held["message"]["message_id"])
            ["reply_to"], request["message_id"])

    def test_a_reply_binding_another_digest_refuses(self):
        request = self.asked()
        said = self.refusal(lambda: self.answered(
            request, request_digest="sha256:" + "e" * 64))
        self.assertIn("about the request it names", said)

    def test_a_reply_naming_another_checkpoint_refuses(self):
        request = self.asked()
        said = self.refusal(lambda: self.answered(
            request, document=response_document(
                request["message_id"], request["handoff_digest"],
                checkpoint="checkpoint-line-1-9")))
        self.assertIn("exact retained checkpoint", said)

    def test_an_unknown_request_is_not_answered_into_existence(self):
        said = self.refusal(lambda: self.answered(
            {"message_id": "msg-nothing",
             "handoff_digest": "sha256:" + "5" * 64}))
        self.assertIn("no message", said)
        self.assertEqual(self.authority.work_messages(WORK), [])

    def test_a_reply_to_a_reply_refuses(self):
        request = self.asked()
        held = self.answered(request)
        said = self.refusal(lambda: self.answered(
            held["message"], message_id="msg-3", operation_id="op-answer-2"))
        self.assertIn("a reply answers a request", said)

    def test_one_request_earns_exactly_one_reply(self):
        request = self.asked()
        self.answered(request)
        said = self.refusal(lambda: self.answered(
            request, message_id="msg-3", operation_id="op-answer-2"))
        self.assertIn("already answered", said)
        self.assertEqual(len(self.authority.work_messages(WORK)), 2)

    def test_a_stale_request_cannot_be_answered_as_a_newer_one(self):
        """Two questions, each with its own digest: a reply holding the first
        one's digest cannot consume the second."""
        first = self.asked()
        self.answered(first)
        second = self.asked(document=request_document(body="and this one?"),
                            message_id="msg-3", operation_id="op-ask-3")
        said = self.refusal(lambda: self.answered(
            second, message_id="msg-4", operation_id="op-answer-2",
            request_digest=first["handoff_digest"]))
        self.assertIn("about the request it names", said)

    def test_an_ungranted_participant_cannot_answer(self):
        self.authority.add_route_handler("impl", STRANGER)
        request = self.asked()
        said = self.refusal(lambda: self.answered(
            request, session=self.authority.session(STRANGER)))
        self.assertIn(messages.ANSWER_CAPABILITY, said)

    def test_the_review_capability_grants_no_answer_by_implication(self):
        """"Existing `review` or route membership grants no new capability by
        implication.\""""
        self.authority.grant_capability(STRANGER, "review", scope=self.scope)
        self.authority.add_route_handler("impl", STRANGER)
        request = self.asked()
        said = self.refusal(lambda: self.answered(
            request, session=self.authority.session(STRANGER)))
        self.assertIn(messages.ANSWER_CAPABILITY, said)

    def test_a_grant_in_another_scope_does_not_reach_this_work(self):
        self.authority.revoke_capability(REVIEWER, messages.ANSWER_CAPABILITY,
                                         scope=self.scope)
        self.authority.grant_capability(REVIEWER, messages.ANSWER_CAPABILITY,
                                        scope="scope:somewhere-else")
        request = self.asked()
        said = self.refusal(lambda: self.answered(request))
        self.assertIn(messages.ANSWER_CAPABILITY, said)

    def test_the_decision_the_answer_was_authorized_under_is_retained(self):
        request = self.asked()
        held = self.answered(request)
        decision = self.authority.decision_of(
            "response", held["message"]["message_id"])
        self.assertEqual(decision["endpoint"], REVIEWER)
        self.assertEqual(decision["role"], messages.ANSWER_CAPABILITY)
        self.assertEqual(decision["effective_scope"], self.scope)


class AnUnresolvedQuestionEscALATESOnceAndStaysHeld(MessageCase):

    def test_an_escalation_is_addressed_to_the_configured_recipient(self):
        request = self.asked()
        held = self.answered(request, disposition="escalate",
                             effect="held")
        self.assertEqual(held["message"]["kind"], "escalation")
        self.assertEqual(held["message"]["destination"], OWNER)
        self.assertEqual(held["message"]["author"], REVIEWER)
        self.assertEqual(held["transition"]["effect"], "held")

    def test_the_escalation_carries_ambiguity_options_and_recommendation(self):
        request = self.asked()
        held = self.answered(request, disposition="escalate", effect="held")
        body = held["message"]["body"]
        self.assertEqual(body["escalation"], ESCALATION)
        self.assertEqual(body["disposition"],
                         native_handoff.ESCALATE_DISPOSITION)

    def test_an_escalation_that_carries_none_of_the_three_is_refused(self):
        """"An escalation that carries none is a refusal to answer wearing a
        disposition." Refused by the document contract before the authority is
        asked at all."""
        with self.assertRaises(Exception):
            native_handoff.check_handoff(response_document(
                "msg-1", "sha256:" + "1" * 64, disposition="escalate"))

    def test_an_escalation_never_routes_back_to_the_answering_reviewer(self):
        """THE CONFIGURATION IS WHERE THIS IS CAUGHT, which is earlier and
        stronger than catching it at the escalation: a deployment whose
        decision recipient IS its reviewer admits no native request at all,
        so there is no question for the self-route to be attempted on."""
        request = self.asked()
        self.routed(reviewer=REVIEWER, recipient=REVIEWER)
        said = self.refusal(lambda: self.answered(
            request, disposition="escalate", effect="held"))
        self.assertIn("HIGHER authority", said)
        self.assertEqual(len(self.authority.work_messages(WORK)), 1)

    def test_one_durable_escalation_per_request_and_no_second(self):
        request = self.asked()
        self.answered(request, disposition="escalate", effect="held")
        said = self.refusal(lambda: self.answered(
            request, disposition="escalate", effect="held",
            message_id="msg-3", operation_id="op-answer-2"))
        self.assertIn("already answered", said)
        self.assertEqual(len(self.authority.handoff_escalations(WORK)), 1)

    def test_the_escalation_is_readable_by_the_recipient_with_no_claim(self):
        """The decision recipient holds no assignment on this Work and should
        need none: the inventory read is on the bootstrap face."""
        request = self.asked()
        self.answered(request, disposition="escalate", effect="held")
        held = self.authority.handoff_escalations(WORK)
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["destination"], OWNER)

    def test_an_escalation_still_leaves_the_request_answered(self):
        """It is a reply: the question is not pending any more, and nothing
        else may answer it. What is unresolved is the DECISION, which the
        transition receipt records as `held`."""
        request = self.asked()
        self.answered(request, disposition="escalate", effect="held")
        self.assertEqual(self.authority.pending_handoff_requests(WORK), [])


class TheEffectIsRecordedApartFromTheText(MessageCase):

    def test_an_answer_earns_a_continuation_and_an_escalation_a_hold(self):
        for disposition, effect in (("answer", "continuation"),
                                    ("escalate", "held")):
            with self.subTest(disposition=disposition):
                self.setUp()
                request = self.asked()
                held = self.answered(request, disposition=disposition,
                                     effect=effect)
                recorded = self.authority.work_message_transition(
                    held["message"]["message_id"])
                self.assertEqual(recorded["effect"], effect)
                self.assertEqual(recorded["work_id"], WORK)

    def test_a_request_earns_no_effect_of_any_kind(self):
        """A question is not an effect. Until somebody answers it, there is no
        transition receipt to read."""
        held = self.asked()
        self.assertIsNone(
            self.authority.work_message_transition(held["message_id"]))

    def test_no_receipt_of_any_kind_is_written_by_either_act(self):
        """THE BOUNDARY THE SLICE DRAWS, asked of the authority that would
        have to write one. A response is a clarification interpretation and
        never an `accepted` technical review."""
        request = self.asked()
        self.answered(request)
        rows = self.rows("SELECT count(*) FROM receipt")
        self.assertEqual(rows, 0)
        self.assertEqual(self.rows("SELECT count(*) FROM proposal"), 0)
        self.assertEqual(self.rows("SELECT count(*) FROM integration_attempt"),
                         0)
        # And the canonical target did not move.
        self.assertEqual(self.authority.canonical_target(), "base-1")

    def rows(self, statement):
        import sqlite3

        connection = sqlite3.connect(self.path)
        try:
            return connection.execute(statement).fetchone()[0]
        finally:
            connection.close()

    def test_an_unknown_effect_word_refuses(self):
        request = self.asked()
        said = self.refusal(lambda: self.answered(request, effect="accepted"))
        self.assertIn("effect is one of", said)


class EveryActIsEffectivelyOnce(MessageCase):

    def test_an_exact_retry_replays_and_writes_no_second_message(self):
        first = self.asked()
        again = self.asked()
        self.assertEqual(first, again)
        self.assertEqual(len(self.authority.work_messages(WORK)), 1)

    def test_a_reused_operation_id_with_changed_operands_refuses(self):
        self.asked()
        said = self.refusal(lambda: self.asked(
            document=request_document(body="a different question"),
            message_id="msg-9"))
        self.assertIn("different operands", said)
        self.assertEqual(len(self.authority.work_messages(WORK)), 1)

    def test_an_exact_reply_retry_replays_its_whole_answer(self):
        request = self.asked()
        first = self.answered(request)
        again = self.answered(request)
        self.assertEqual(first, again)
        self.assertEqual(len(self.authority.work_messages(WORK)), 2)
        self.assertEqual(
            self.authority.work_message_transition(
                first["message"]["message_id"])["effect"], "continuation")

    def test_a_message_identity_is_claimed_once(self):
        self.asked()
        said = self.refusal(lambda: self.asked(
            document=request_document(body="another"),
            operation_id="op-ask-2"))
        self.assertIn("is already the", said)

    def test_a_reply_identity_cannot_reuse_a_requests(self):
        request = self.asked()
        said = self.refusal(lambda: self.answered(request,
                                                  message_id="msg-1"))
        self.assertIn("is already the", said)


class TheReadsAnswerHonestlyAndGateNothing(MessageCase):

    def test_a_work_with_no_messages_reads_as_an_empty_list(self):
        self.assertEqual(self.authority.work_messages(WORK), [])
        self.assertEqual(self.authority.pending_handoff_requests(WORK), [])
        self.assertEqual(self.authority.handoff_escalations(WORK), [])

    def test_an_unknown_message_reads_as_NONE_rather_than_failing(self):
        self.assertIsNone(self.authority.work_message("msg-nothing"))
        self.assertIsNone(self.authority.work_message_reply("msg-nothing"))
        self.assertIsNone(
            self.authority.work_message_transition("msg-nothing"))

    def test_nobody_has_to_READ_a_message_for_anything_to_proceed(self):
        """NO READ-ACK GATE. There is no seen cursor, no acknowledgement
        column and no read receipt anywhere in this model -- so an answer
        commits and a continuation is earned without any party having read
        anything, which is what keeps a read receipt from becoming a
        prerequisite for progress.
        """
        request = self.asked()
        held = self.answered(request)
        self.assertEqual(held["transition"]["effect"], "continuation")
        import sqlite3

        connection = sqlite3.connect(self.path)
        try:
            columns = {one[1] for one in connection.execute(
                "PRAGMA table_info(work_message)")}
        finally:
            connection.close()
        for forbidden in ("seen", "seen_at", "read_at", "acknowledged",
                          "ack", "cursor"):
            self.assertNotIn(forbidden, columns)

    def test_one_retained_record_serves_humans_and_agents_alike(self):
        """The participant-bound session and the operator face answer the SAME
        document: there is one read model, not a second rendering."""
        request = self.asked()
        self.assertEqual(self.implementer.work_messages(WORK),
                         self.authority.work_messages(WORK))
        self.assertEqual(self.reviewer.work_message(request["message_id"]),
                         self.authority.work_message(request["message_id"]))

    def test_a_messages_work_scoped_read_sees_no_other_works(self):
        self.authority.create_work(OTHER_WORK, "impl",
                                   operation_id="op-create-2", contract=V12)
        self.asked()
        self.assertEqual(self.authority.work_messages(OTHER_WORK), [])

    def test_the_configured_routing_is_not_a_session_read(self):
        """It is CONFIGURATION, and the runtime face reads facts."""
        self.assertFalse(hasattr(self.implementer, "native_routing"))
        self.assertIsNotNone(self.authority.native_routing())


class TheBoundedDocumentContractRefusesWhatItMustRefuse(unittest.TestCase):
    """The pure half, driven directly: undeclared, mixed, missing or foreign."""

    def refusing(self, document):
        with self.assertRaises(Exception) as caught:
            native_handoff.check_handoff(document)
        return str(caught.exception)

    def test_the_approved_four_kinds_and_nothing_else(self):
        self.assertEqual(native_handoff.HANDOFF_KINDS,
                         ("final-submission", "clarification-request",
                          "finding-request", "response"))
        said = self.refusing(dict(request_document(), kind="question"))
        self.assertIn("an unknown kind is held", said)

    def test_a_foreign_schema_refuses_as_a_VERSION(self):
        said = self.refusing(dict(request_document(),
                                  schema="baton.native-handoff/2"))
        self.assertIn("another revision is not one to read", said)

    def test_a_final_submission_carries_no_request_members(self):
        self.assertEqual(
            native_handoff.check_handoff(
                {"schema": native_handoff.HANDOFF_SCHEMA,
                 "kind": native_handoff.FINAL_KIND}),
            {"schema": native_handoff.HANDOFF_SCHEMA,
             "kind": native_handoff.FINAL_KIND})
        said = self.refusing({"schema": native_handoff.HANDOFF_SCHEMA,
                              "kind": native_handoff.FINAL_KIND,
                              "body": "x"})
        self.assertIn("unexpected body", said)

    def test_a_MIXED_document_is_refused_as_the_mixture_it_is(self):
        said = self.refusing(dict(request_document(),
                                  escalation=ESCALATION))
        self.assertIn("unexpected escalation", said)

    def test_a_MISSING_member_refuses_and_names_itself(self):
        held = request_document()
        del held["continuation"]
        self.assertIn("missing continuation", self.refusing(held))

    def test_a_response_that_answers_and_escalates_at_once_refuses(self):
        said = self.refusing(response_document(
            "msg-1", "sha256:" + "1" * 64, escalation=ESCALATION))
        self.assertIn("one response decides once", said)

    def test_there_is_no_word_here_for_approving_code(self):
        self.assertEqual(native_handoff.DISPOSITIONS, ("answer", "escalate"))
        for forbidden in ("accepted", "approve", "approved", "integrate"):
            said = self.refusing(dict(
                response_document("msg-1", "sha256:" + "1" * 64),
                disposition=forbidden))
            self.assertIn("no word here for approving code", said)

    def test_duplicate_keys_are_refused_before_canonicalization(self):
        """A document with two readings has no identity, and the one a digest
        is taken over need not be the one a reader sees."""
        payload = (b'{"schema": "baton.native-handoff/1", '
                   b'"kind": "final-submission", "kind": "response"}')
        with self.assertRaises(Exception) as caught:
            native_handoff.handoff_of_bytes(payload)
        self.assertIn("two readings", str(caught.exception))

    def test_the_encoded_ceiling_is_enforced_at_the_read(self):
        with self.assertRaises(Exception) as caught:
            native_handoff.handoff_of_bytes(
                b" " * (native_handoff.MAX_HANDOFF_BYTES + 1))
        self.assertIn(str(native_handoff.MAX_HANDOFF_BYTES),
                      str(caught.exception))

    def test_the_digest_is_over_the_whole_document_with_no_member_for_one(self):
        held = request_document()
        self.assertNotIn("digest", held)
        first = native_handoff.handoff_digest(held)
        self.assertEqual(first, native_handoff.handoff_digest(dict(held)))
        self.assertNotEqual(first, native_handoff.handoff_digest(
            dict(held, body="a different question")))


class TheSchemaBoundaryIsExplicit(MessageCase):

    def test_this_build_speaks_the_version_that_carries_the_message(self):
        self.assertEqual(SCHEMA_VERSION, 7)

    def test_the_two_relations_exist_and_are_separate(self):
        import sqlite3

        connection = sqlite3.connect(self.path)
        try:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            connection.close()
        self.assertIn("work_message", tables)
        self.assertIn("work_message_transition", tables)

    def test_a_message_cannot_name_a_work_this_authority_does_not_hold(self):
        said = self.refusal(lambda: self.asked(expect={
            "work_ref": {"authority_uuid": UUID, "work_id": OTHER_WORK},
            "participant": IMPLEMENTER, "generation": 1}))
        self.assertIn("no such Work", said)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
