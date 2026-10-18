"""W321689 — the owner's disposition, through the subcommand an owner reaches.

These drive `python3 -m tools.stack_command disposition ...` rather than the
authority underneath it, because the pilot assessment's finding is about the
INSTALLED surface: `Session.approve` and `Session.close` exist, no packaged
verb reached them, and nothing answered "is a reviewed candidate waiting for a
human on this Work". A case against the API would prove the wrong layer.

WHAT THESE PROVE THAT THE AUTHORITY CASES CANNOT.

  THE OPERANDS OF THE HUMAN ACT. The authority binds a proposal id and a
  policy generation; which candidate BYTES and which independent review the
  approver was looking at are operands of this command, and a stale one has to
  refuse before anything is written.

  THAT A GREEN EXECUTION FLAG IS NOT AN ACCEPTANCE. `core.close` authorizes by
  capability and has no opinion about receipts, so the refusal of a satisfying
  closure over a passed verification alone is this layer's behaviour.

  THAT THE HUMAN INTEGRATION IS A FILE SOMEBODY WROTE. The authority stores a
  reference and never opens one, so reading the record, binding it to the exact
  candidate and commit, and refusing a closure whose cited record has been
  deleted or rewritten all live here.

Every store, root and record is this fixture's own temporary directory. No
deployment is started, no engine, container or provider is reached, no Git
command runs, and no owner receipt is fabricated for anything outside these
fixtures: the approvals below are a test participant's, recorded in a
disposable store.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from baton_v12.authority import Authority, Refusal, V12
from tools import disposition_command, stack_command

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W1"
OTHER = "0123abcd-W2"
WORKER = "baton.claude"
SECOND = "baton.codxpc"
REVIEWER = "baton.rvpc"
OWNER = "baton.slaw"
STRANGER = "baton.gemini"
ROUTE = "impl"
NOW = "2026-10-18T12:00:00.000Z"
LOCATOR = "operator-quickstart-7f3a91c2"
RECORD = "work/records/2026/10/finding-pilot/INTEGRATION.json"
COMMIT = "433b09d6963ca9789700849b640e242e772b9867"
DIGESTS = {"result_id": "result-1", "result_digest": "sha256:" + "1" * 64,
           "candidate_digest": "sha256:" + "2" * 64,
           "input_digest": "sha256:" + "3" * 64,
           "policy_digest": "sha256:" + "4" * 64}
CANDIDATE = DIGESTS["candidate_digest"]


class Fixture(unittest.TestCase):
    """One v12 Work carried to the point a human disposition is due.

    Built through the public faces only -- create, grant, claim, publish,
    verify, review -- because the acceptance is about what the owner's command
    does with a REAL record rather than with rows arranged behind it.
    """

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-disposition-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.store = os.path.join(self.root, "authority.sqlite3")
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(os.path.join(self.repo, os.path.dirname(RECORD)))
        authority = Authority.create(self.store, authority_uuid=UUID,
                                     clock=lambda: NOW)
        authority.create_work(WORK, ROUTE, operation_id="op-create",
                              contract=V12)
        authority.add_route_handler(ROUTE, WORKER)
        self.scope = authority.project_work(WORK)["scope"]
        authority.grant_capability(REVIEWER, "verify", scope=self.scope)
        authority.grant_capability(REVIEWER, "review", scope=self.scope)
        for capability in ("approve", "integrate", "close"):
            authority.grant_capability(OWNER, capability, scope=self.scope)
        authority.bind_dossier(WORK, LOCATOR, operation_id="op-bind")
        self.assignment = authority.session(WORKER).claim(
            {"work_id": WORK, "operation_id": "op-claim"})["assignment"]
        authority.dispose()

    # -- reaching the command -------------------------------------------------

    def run_verb(self, *operands):
        """The installed subcommand, with its streams captured.

        Through `stack_command.main`, because the gap recorded by the
        assessment was that the DEPLOYED command had no such verb -- so the
        dispatch table is part of what these prove.
        """
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = stack_command.main(["disposition", *operands])
        return code, out.getvalue(), err.getvalue()

    def said(self, out):
        return json.loads(out)

    def base(self):
        return ["--authority-store", self.store, "--authority-uuid", UUID]

    # -- carrying the Work forward -------------------------------------------

    def authority(self):
        held = Authority.open(self.store, expected_authority_uuid=UUID,
                              clock=lambda: NOW)
        self.addCleanup(held.dispose)
        return held

    def publish(self, proposal="proposal-1", **changed):
        """Publish as the producer, claiming first if nothing holds the Work.

        A producer publishes UNDER an assignment, and `ended` below releases
        it the way the line does -- so a fixture that carries the Work past one
        candidate has to be able to take it again.
        """
        authority = self.authority()
        session = authority.session(WORKER)
        held = authority.assignment_of(WORK)
        if held is None:
            held = session.claim({"work_id": WORK,
                                  "operation_id": "op-reclaim-" + proposal},
                                 )["assignment"]
        self.assignment = held
        answer = session.publish(
            dict({"expect": held,
                  "operation_id": "op-publish-" + proposal,
                  "proposal_id": proposal},
                 **dict(DIGESTS,
                        # A FROZEN RESULT NAMES THE ASSIGNMENT THAT MADE IT,
                        # so a second candidate cannot reuse the first one's
                        # identity.
                        result_id="result-" + proposal, **changed)))
        authority.dispose()
        return answer

    def ended(self, operation_id="op-end-1"):
        """The producer's assignment released, as the line releases it.

        A Work waiting on a human is not a Work somebody is executing: the
        producer published and ended, and the owner's disposition comes after.
        `test_closing_a_live_assignment_needs_its_exact_identity` is where the
        other case -- an assignment still live at closure -- is proved.
        """
        authority = self.authority()
        authority.session(WORKER).end({"expect": self.assignment,
                                       "operation_id": operation_id})
        authority.dispose()

    def verified(self, proposal="proposal-1", observation="passed"):
        authority = self.authority()
        answer = authority.session(REVIEWER).verify(
            {"proposal_id": proposal, "verification_id": "ver-" + proposal,
             "observation": observation, "operation_id": "op-ver-" + proposal})
        authority.dispose()
        return answer

    def reviewed(self, proposal="proposal-1", disposition="accepted"):
        authority = self.authority()
        answer = authority.session(REVIEWER).review(
            {"proposal_id": proposal, "review_id": "rev-" + proposal,
             "disposition": disposition, "operation_id": "op-rev-" + proposal})
        authority.dispose()
        return answer

    def accepted_candidate(self, proposal="proposal-1"):
        """Published, verified, independently accepted, producer released."""
        self.publish(proposal)
        self.verified(proposal)
        held = self.reviewed(proposal)
        self.ended("op-end-" + proposal)
        return held

    def relive(self):
        """Take the Work again, so a close has a live assignment to end."""
        authority = self.authority()
        self.assignment = authority.session(WORKER).claim(
            {"work_id": WORK, "operation_id": "op-reclaim-live"}
        )["assignment"]
        authority.dispose()
        return self.assignment

    def generation(self):
        authority = self.authority()
        held = authority.policy_generation()
        authority.dispose()
        return held

    # -- the owner's acts ----------------------------------------------------

    def approve(self, verb="approve", proposal="proposal-1", **changed):
        operands = {"--participant": OWNER, "--work": WORK,
                    "--proposal": proposal,
                    "--expect-candidate-digest": CANDIDATE,
                    "--expect-review": "rev-" + proposal,
                    "--policy-generation": str(self.generation()),
                    "--approval-id": "app-1",
                    "--operation-id": "op-approve-1"}
        operands.update(changed)
        flat = []
        for name, value in operands.items():
            if value is not None:
                flat += [name, value]
        return self.run_verb(verb, *self.base(), *flat)

    def record_document(self, **changed):
        return dict({"schema": "baton.v12.human-integration-record/1",
                     "authority_uuid": UUID, "work_id": WORK,
                     "proposal_id": "proposal-1",
                     "candidate_digest": CANDIDATE, "commit": COMMIT,
                     "integrated_by": "Slawomir",
                     "integrated_at": "2026-10-18T12:30:00Z"}, **changed)

    def write_record(self, document=None, reference=RECORD):
        whole = os.path.join(self.repo, reference)
        os.makedirs(os.path.dirname(whole), exist_ok=True)
        body = json.dumps(self.record_document() if document is None
                          else document, indent=2, sort_keys=True)
        with open(whole, "w", encoding="utf-8") as handle:
            handle.write(body)
        return whole

    def integrated(self, reference=RECORD, **changed):
        operands = {"--participant": OWNER, "--work": WORK,
                    "--proposal": "proposal-1",
                    "--expect-candidate-digest": CANDIDATE,
                    "--root": self.repo, "--reference": reference,
                    "--commit": COMMIT, "--integration-id": "int-1",
                    "--operation-id": "op-integrated-1",
                    "--evidence-operation-id": "op-cite-1"}
        operands.update(changed)
        flat = []
        for name, value in operands.items():
            if value is not None:
                flat += [name, value]
        return self.run_verb("integrated", *self.base(), *flat)

    def close(self, outcome="satisfying", **changed):
        operands = {"--participant": OWNER, "--work": WORK,
                    "--outcome": outcome, "--rationale": "pilot delivered",
                    "--operation-id": "op-close-1"}
        if outcome == "satisfying":
            operands.update({"--proposal": "proposal-1",
                             "--expect-candidate-digest": CANDIDATE,
                             "--root": self.repo})
        operands.update(changed)
        flat = []
        for name, value in operands.items():
            if value is not None:
                flat += [name, value]
        return self.run_verb("close", *self.base(), *flat)

    def delivered(self):
        """The whole selected path: accepted, approved, integrated."""
        self.accepted_candidate()
        code, _out, err = self.approve()
        self.assertEqual(code, 0, err)
        self.write_record()
        code, _out, err = self.integrated()
        self.assertEqual(code, 0, err)

    # -- reading the record back ---------------------------------------------

    def receipt(self, kind, proposal="proposal-1"):
        """A FRESH open every time: a readback is the acceptance."""
        authority = Authority.open_readonly(self.store,
                                            expected_authority_uuid=UUID)
        try:
            return authority.receipt(proposal, kind)
        finally:
            authority.dispose()

    def work_now(self):
        authority = Authority.open_readonly(self.store,
                                            expected_authority_uuid=UUID)
        try:
            return authority.project_work(WORK)
        finally:
            authority.dispose()

    def citations(self):
        authority = Authority.open_readonly(self.store,
                                            expected_authority_uuid=UUID)
        try:
            return authority.dossier_evidence(WORK)
        finally:
            authority.dispose()


class WhatIsDue(Fixture):
    """`pending`: the answer that did not exist at all."""

    def pending(self, participant=None):
        operands = ["--work", WORK]
        if participant is not None:
            operands += ["--participant", participant]
        code, out, err = self.run_verb("pending", *self.base(), *operands)
        self.assertEqual(code, 0, err)
        return self.said(out)

    def test_a_work_with_no_candidate_owes_nobody_anything(self):
        said = self.pending()
        self.assertEqual(said["owner_action"], "no-candidate")
        self.assertEqual(said["proposals"], [])
        self.assertIsNone(said["latest_proposal"])
        # And the record it belongs to is reported, because that is how a
        # human holding a directory name got here.
        self.assertEqual(said["dossier"]["locator"], LOCATOR)
        self.assertEqual(said["authority_uuid"], UUID)

    def test_each_step_of_the_line_names_the_act_that_is_actually_due(self):
        self.publish()
        self.assertEqual(self.pending()["owner_action"],
                         "awaiting-verification")
        self.verified()
        said = self.pending()
        self.assertEqual(said["owner_action"], "awaiting-review")
        # THE OWNER'S ACT FOLLOWS THE REVIEWER'S. A passed verification is
        # execution's answer, and reporting it as approval-due would be the
        # conflation this whole Work exists to refuse.
        self.assertIn("never the other way round", said["due"])
        self.reviewed()
        said = self.pending()
        self.assertEqual(said["owner_action"], "approval-due")
        self.assertEqual(said["latest_proposal"], "proposal-1")
        self.assertEqual(said["proposals"][0]["candidate_digest"], CANDIDATE)
        self.assertEqual(
            said["proposals"][0]["receipts"]["review"]["receipt_id"],
            "rev-proposal-1")
        self.assertIsNone(said["proposals"][0]["receipts"]["approval"])

    def test_a_rejected_review_leaves_the_owner_nothing_to_approve(self):
        self.publish()
        self.verified()
        self.reviewed(disposition="changes-requested")
        said = self.pending()
        self.assertEqual(said["owner_action"], "review-not-accepted")
        self.assertIn("nothing for the owner to approve", said["due"])

    def test_a_failed_verification_is_not_an_owner_question(self):
        self.publish()
        self.verified(observation="failed")
        self.assertEqual(self.pending()["owner_action"],
                         "awaiting-verification")

    def test_the_action_advances_through_approval_integration_and_closure(self):
        self.accepted_candidate()
        self.assertEqual(self.pending()["owner_action"], "approval-due")
        self.assertEqual(self.approve()[0], 0)
        self.assertEqual(self.pending()["owner_action"], "integration-due")
        self.write_record()
        self.assertEqual(self.integrated()[0], 0)
        self.assertEqual(self.pending()["owner_action"], "closure-due")
        self.assertEqual(self.close()[0], 0)
        said = self.pending()
        # A CLOSED WORK OWES NOTHING, whatever its receipts say: reporting an
        # act as due on a terminal Work would send an operator to perform one
        # the authority will refuse.
        self.assertEqual(said["owner_action"], "closed")
        self.assertEqual(said["work"]["outcome"], "satisfying")

    def test_a_denial_leaves_a_non_satisfying_ending_as_the_owner_act(self):
        self.accepted_candidate()
        self.assertEqual(self.approve(verb="deny")[0], 0)
        said = self.pending()
        self.assertEqual(said["owner_action"], "denied")
        self.assertIn("evidence is preserved", said["due"])

    def test_it_says_whether_the_asker_can_perform_the_act(self):
        self.accepted_candidate()
        said = self.pending(participant=OWNER)
        self.assertEqual(said["holds"], {"approve": True, "integrate": True,
                                         "close": True})
        # And an address with no grant is told so BEFORE it tries, which is
        # the same fact a refusal would give it later.
        said = self.pending(participant=STRANGER)
        self.assertEqual(said["holds"], {"approve": False, "integrate": False,
                                         "close": False})

    def test_pending_does_not_open_the_store_for_writing(self):
        # A read verb that took a write lock would lock a deployment somebody
        # is serving from. Proved by making the WRITABLE opener unavailable:
        # if `pending` reached for it, this would fail.
        self.accepted_candidate()
        with mock.patch.object(
                Authority, "open",
                classmethod(lambda cls, *a, **k: self.fail(
                    "pending opened the authority for writing"))):
            said = self.pending()
        self.assertEqual(said["owner_action"], "approval-due")

    def test_the_latest_candidate_is_the_one_the_answer_is_about(self):
        self.accepted_candidate("proposal-1")
        self.publish("proposal-2", candidate_digest="sha256:" + "9" * 64)
        said = self.pending()
        self.assertEqual([one["proposal_id"] for one in said["proposals"]],
                         ["proposal-1", "proposal-2"])
        # The newer candidate has no verification, so THAT is what is due --
        # an answer derived from the older accepted one would tell the owner
        # to approve bytes that have been superseded.
        self.assertEqual(said["owner_action"], "awaiting-verification")
        self.assertEqual(said["latest_proposal"], "proposal-2")


class TheOwnerDecision(Fixture):
    """`approve` and `deny`: bound to the exact candidate, review and policy."""

    def test_an_approval_binds_the_candidate_the_review_and_the_generation(self):
        self.accepted_candidate()
        code, out, err = self.approve()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["approval"]["disposition"], "approved")
        self.assertEqual(said["bound"]["candidate_digest"], CANDIDATE)
        self.assertEqual(said["bound"]["review_receipt"], "rev-proposal-1")
        self.assertEqual(said["bound"]["actor"], OWNER)
        self.assertTrue(said["integration_due"])
        # READBACK IS THE ACCEPTANCE: a fresh open of the store answers the
        # same receipt, actor, candidate and generation.
        held = self.receipt("approval")
        self.assertEqual(held["actor"], OWNER)
        self.assertEqual(held["disposition"], "approved")
        self.assertEqual(held["candidate_digest"], CANDIDATE)
        self.assertEqual(held["policy_generation"], self.generation())
        self.assertEqual(held["decision"]["endpoint"], OWNER)

    def test_the_actor_is_the_binding_and_there_is_no_operand_for_it(self):
        self.accepted_candidate()
        # No `--actor`: the session is minted for `--participant` and the
        # authority takes the receipt's actor from that binding. A caller that
        # could name one could name somebody else's.
        with self.assertRaises(SystemExit):
            self.approve(**{"--actor": OWNER})
        self.assertIsNone(self.receipt("approval"))

    def test_an_actor_without_the_capability_writes_nothing(self):
        self.accepted_candidate()
        code, _out, err = self.approve(**{"--participant": STRANGER})
        self.assertEqual(code, 2)
        self.assertIn("approve capability", err)
        self.assertIsNone(self.receipt("approval"))

    def test_a_changed_candidate_refuses_rather_than_inheriting_a_decision(self):
        self.accepted_candidate()
        code, _out, err = self.approve(
            **{"--expect-candidate-digest": "sha256:" + "f" * 64})
        self.assertEqual(code, 2)
        self.assertIn("changed candidate refuses", err)
        self.assertIsNone(self.receipt("approval"))

    def test_a_proposal_from_another_work_refuses(self):
        self.accepted_candidate()
        authority = self.authority()
        authority.create_work(OTHER, ROUTE, operation_id="op-create-2",
                              contract=V12)
        authority.add_route_handler(ROUTE, SECOND)
        elsewhere = authority.session(SECOND).claim(
            {"work_id": OTHER, "operation_id": "op-claim-2"})["assignment"]
        authority.session(SECOND).publish(
            dict({"expect": elsewhere, "operation_id": "op-publish-other",
                  "proposal_id": "proposal-other"},
                 **dict(DIGESTS, result_id="result-other")))
        authority.dispose()
        code, _out, err = self.approve(**{"--proposal": "proposal-other"})
        self.assertEqual(code, 2)
        self.assertIn("bound to the Work's own candidate", err)
        self.assertIsNone(self.receipt("approval", "proposal-other"))

    def test_an_unreviewed_candidate_cannot_be_approved(self):
        self.publish()
        self.verified()
        code, _out, err = self.approve()
        self.assertEqual(code, 2)
        self.assertIn("follows independent review", err)
        self.assertIsNone(self.receipt("approval"))

    def test_a_candidate_with_no_passed_verification_cannot_be_approved(self):
        self.publish()
        code, _out, err = self.approve()
        self.assertEqual(code, 2)
        self.assertIn("no passed verification", err)

    def test_the_review_the_owner_read_is_the_one_that_must_be_accepted(self):
        self.accepted_candidate()
        code, _out, err = self.approve(**{"--expect-review": "rev-something"})
        self.assertEqual(code, 2)
        self.assertIn("the review they actually read", err)
        self.assertIsNone(self.receipt("approval"))

    def test_a_stale_policy_generation_refuses(self):
        self.accepted_candidate()
        was = self.generation()
        authority = self.authority()
        authority.set_policy("unrelated", "reconfigured")
        authority.dispose()
        # A configuration act is a NEW generation, which is what makes the
        # generation the approver read stale.
        self.assertEqual(self.generation(), was + 1)
        code, _out, err = self.run_verb(
            "approve", *self.base(), "--participant", OWNER, "--work", WORK,
            "--proposal", "proposal-1", "--expect-candidate-digest", CANDIDATE,
            "--expect-review", "rev-proposal-1",
            "--policy-generation", str(was),
            "--approval-id", "app-1", "--operation-id", "op-approve-1")
        self.assertEqual(code, 2)
        self.assertIn("stale generation refuses", err)
        self.assertIsNone(self.receipt("approval"))
        # And the CURRENT generation is accepted, so the refusal was about
        # staleness rather than about the operand being unusable.
        self.assertEqual(self.approve()[0], 0)
        self.assertEqual(self.receipt("approval")["policy_generation"],
                         was + 1)

    def test_an_exact_retry_replays_and_a_changed_one_collides(self):
        self.accepted_candidate()
        code, first, err = self.approve()
        self.assertEqual(code, 0, err)
        code, again, err = self.approve()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(again)["approval"],
                         self.said(first)["approval"])
        # A DIFFERENT DECISION UNDER ONE IDENTITY IS A COLLISION, not a second
        # receipt and not a replayed success.
        code, _out, err = self.approve(verb="deny")
        self.assertEqual(code, 2)
        self.assertIn("different operands", err)
        self.assertEqual(self.receipt("approval")["disposition"], "approved")

    def test_a_denial_is_recorded_and_preserves_the_evidence(self):
        self.accepted_candidate()
        code, out, err = self.approve(verb="deny")
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["approval"]["disposition"], "denied")
        self.assertFalse(said["integration_due"])
        self.assertTrue(said["evidence_preserved"])
        # The candidate, its verification and its review are all still there.
        self.assertEqual(self.receipt("verification")["disposition"], "passed")
        self.assertEqual(self.receipt("review")["disposition"], "accepted")
        self.assertEqual(self.receipt("approval")["actor"], OWNER)
        # And a denied candidate has no integration to record.
        self.write_record()
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("not approved", err)


class TheHumanIntegration(Fixture):
    """`integrated`: the commit a person made, recorded as evidence of theirs."""

    def approved(self):
        self.accepted_candidate()
        code, _out, err = self.approve()
        self.assertEqual(code, 0, err)

    def test_it_cites_the_record_and_writes_the_receipt(self):
        self.approved()
        self.write_record()
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["integration"]["disposition"], "integrated")
        self.assertEqual(said["bound"]["commit"], COMMIT)
        self.assertEqual(said["bound"]["actor"], OWNER)
        self.assertFalse(said["replayed"])
        # The REQUEST's operands and the RECORD's own content are two different
        # facts and are reported as two.
        self.assertEqual(said["evidence_now"]["integrated_by"], "Slawomir")
        self.assertEqual(said["evidence_now"]["state"], "intact")
        self.assertEqual(said["request"]["request"]["commit"], COMMIT)
        self.assertEqual(said["cited"]["reference"], RECORD)
        # BOTH ACTS SURVIVE A READBACK, and they are two different facts: the
        # citation carries the commit, the receipt carries the actor.
        held = self.receipt("integration")
        self.assertEqual(held["actor"], OWNER)
        self.assertEqual(held["candidate_digest"], CANDIDATE)
        cited = self.citations()
        self.assertEqual([one["reference"] for one in cited], [RECORD])
        self.assertEqual(cited[0]["digest"], said["cited"]["digest"])

    def test_an_unapproved_candidate_has_no_integration_to_record(self):
        self.accepted_candidate()
        self.write_record()
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("a finished Job is not an approval", err)
        self.assertIsNone(self.receipt("integration"))
        self.assertEqual(self.citations(), [])

    def test_an_actor_without_the_grant_cites_nothing(self):
        # The authority refuses the RECEIPT to an actor holding no grant, which
        # is one act too late: the citation would already be recorded for
        # somebody who could not perform the integration it belongs to.
        self.approved()
        self.write_record()
        code, _out, err = self.integrated(**{"--participant": STRANGER})
        self.assertEqual(code, 2)
        self.assertIn("does not hold the integrate capability", err)
        self.assertEqual(self.citations(), [])
        self.assertIsNone(self.receipt("integration"))

    def test_a_record_naming_another_commit_refuses(self):
        self.approved()
        self.write_record(self.record_document(commit="0" * 40))
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("one integration has one commit", err)
        self.assertEqual(self.citations(), [])

    def test_a_record_of_another_integration_refuses(self):
        self.approved()
        for name, value, expect in (
                ("candidate_digest", "sha256:" + "e" * 64, "candidate_digest"),
                ("work_id", OTHER, "work_id"),
                ("proposal_id", "proposal-9", "proposal_id"),
                ("authority_uuid", "f" * 32, "authority_uuid")):
            with self.subTest(member=name):
                self.write_record(self.record_document(**{name: value}))
                code, _out, err = self.integrated()
                self.assertEqual(code, 2)
                self.assertIn("a different integration", err)
                self.assertIn(expect, err)
        self.assertEqual(self.citations(), [])
        self.assertIsNone(self.receipt("integration"))

    def test_a_record_that_is_not_one_refuses(self):
        self.approved()
        cases = {
            "missing member": (self.record_document(), "integrated_by",
                               "does not supply integrated_by"),
            "a member that is not text": (
                self.record_document(integrated_at=20261018), None,
                "does not supply integrated_at as non-empty text"),
            "an empty member": (self.record_document(integrated_by=""), None,
                                "does not supply integrated_by"),
            "unknown member": (dict(self.record_document(), mood="confident"),
                               None, "nothing here reads"),
            "wrong schema": (self.record_document(
                schema="baton.v12.human-integration-record/2"), None,
                "this command reads"),
        }
        for what, (document, drop, expect) in cases.items():
            with self.subTest(what=what):
                if drop is not None:
                    document = dict(document)
                    del document[drop]
                self.write_record(document)
                code, _out, err = self.integrated()
                self.assertEqual(code, 2)
                self.assertIn(expect, err)
        # Not a document at all, and not JSON at all.
        whole = os.path.join(self.repo, RECORD)
        with open(whole, "w", encoding="utf-8") as handle:
            handle.write("[1, 2, 3]")
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("an integration record is one document", err)
        with open(whole, "w", encoding="utf-8") as handle:
            handle.write("committed it, honest")
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("did not read as an integration record", err)
        self.assertEqual(self.citations(), [])

    def test_an_absent_record_is_an_honest_refusal(self):
        self.approved()
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("'absent'", err)
        self.assertEqual(self.citations(), [])

    def test_bytes_reached_through_a_link_are_not_under_this_root(self):
        # The containment W321688's review arrived at, reused rather than
        # reimplemented: an integration record that is a symlink to a file
        # outside the root is not this dossier's evidence.
        self.approved()
        outside = os.path.join(self.root, "elsewhere.json")
        with open(outside, "w", encoding="utf-8") as handle:
            json.dump(self.record_document(), handle)
        linked = os.path.join(self.repo, "work/records/2026/10/finding-pilot",
                              "LINKED.json")
        os.symlink(outside, linked)
        code, _out, err = self.integrated(
            **{"--reference":
               "work/records/2026/10/finding-pilot/LINKED.json"})
        self.assertEqual(code, 2)
        self.assertIn("escapes-root", err)
        self.assertEqual(self.citations(), [])

    def test_an_escaping_reference_never_reaches_the_filesystem(self):
        self.approved()
        code, _out, err = self.integrated(**{"--reference": "../secrets.json"})
        self.assertEqual(code, 2)
        self.assertIn("escapes the root", err)

    def test_a_work_with_no_dossier_cannot_cite_its_integration(self):
        # The authority's own sentence, surfaced rather than translated: a
        # citation needs a record to belong to.
        authority = self.authority()
        authority.create_work(OTHER, ROUTE, operation_id="op-create-2",
                              contract=V12)
        authority.add_route_handler(ROUTE, SECOND)
        scope = authority.project_work(OTHER)["scope"]
        for capability in ("verify", "review"):
            authority.grant_capability(REVIEWER, capability, scope=scope)
        for capability in ("approve", "integrate"):
            authority.grant_capability(OWNER, capability, scope=scope)
        elsewhere = authority.session(SECOND).claim(
            {"work_id": OTHER, "operation_id": "op-claim-2"})["assignment"]
        authority.session(SECOND).publish(
            dict({"expect": elsewhere, "operation_id": "op-pub-2",
                  "proposal_id": "proposal-2"},
                 **dict(DIGESTS, result_id="result-elsewhere")))
        authority.session(REVIEWER).verify(
            {"proposal_id": "proposal-2", "verification_id": "ver-2",
             "observation": "passed", "operation_id": "op-ver-2"})
        authority.session(REVIEWER).review(
            {"proposal_id": "proposal-2", "review_id": "rev-2",
             "disposition": "accepted", "operation_id": "op-rev-2"})
        authority.session(OWNER).approve(
            {"proposal_id": "proposal-2", "approval_id": "app-2",
             "disposition": "approved", "operation_id": "op-app-2",
             "policy_generation": 1})
        authority.dispose()
        self.write_record(self.record_document(work_id=OTHER,
                                               proposal_id="proposal-2"))
        code, _out, err = self.integrated(
            **{"--work": OTHER, "--proposal": "proposal-2"})
        self.assertEqual(code, 2)
        self.assertIn("has no canonical dossier", err)

    def test_a_moved_canonical_target_keeps_the_citation_and_says_so(self):
        """The one refusal in this path that WRITES something.

        `integrate` journals its stale-target attempt before refusing, so that
        refusal is the committed outcome of the identity it was submitted
        under: retrying it replays the refusal. An answer that said "retry"
        would send an operator round a loop that cannot end, so the durable
        case is reported as the different fact it is -- and the citation, which
        committed, is reported as standing.
        """
        self.approved()
        self.write_record()
        authority = self.authority()
        authority.set_policy("canonical_target", "sha256:" + "c" * 64)
        authority.dispose()
        code, out, err = self.integrated()
        self.assertEqual(code, 2)
        said = self.said(out)
        self.assertTrue(said["durable"])
        self.assertEqual(said["cited"]["reference"], RECORD)
        self.assertIsNone(said["integration"])
        self.assertIn("canonical target moved", err)
        self.assertIn("under NEW identities", err)
        # The citation committed and the receipt did not: two acts, reported
        # as two.
        self.assertEqual([one["reference"] for one in self.citations()],
                         [RECORD])
        self.assertIsNone(self.receipt("integration"))
        # And a satisfying closure is still refused, because the integration
        # receipt is what says the owner recorded one.
        code, _out, err = self.run_verb(
            "close", *self.base(), "--participant", OWNER, "--work", WORK,
            "--outcome", "satisfying", "--rationale", "no",
            "--operation-id", "op-close-x", "--proposal", "proposal-1",
            "--expect-candidate-digest", CANDIDATE, "--root", self.repo)
        self.assertEqual(code, 2)
        self.assertIn("integration-due", err)

    def test_an_exact_retry_replays_both_acts(self):
        self.approved()
        self.write_record()
        code, first, err = self.integrated()
        self.assertEqual(code, 0, err)
        code, again, err = self.integrated()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(again)["integration"],
                         self.said(first)["integration"])
        self.assertEqual(self.said(again)["cited"], self.said(first)["cited"])
        self.assertEqual(len(self.citations()), 1)


class TheClosure(Fixture):
    """`close`: the selected acceptance, or an honest ending that is not one."""

    def test_a_passing_verification_alone_cannot_close_satisfyingly(self):
        # THE CASE THIS WHOLE VERB EXISTS FOR. `core.close` checks a
        # capability, and the owner holds it -- so without this check a green
        # execution flag would terminalize the Work as satisfying.
        self.publish()
        self.verified()
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("awaiting-review", err)
        self.assertIn("A capability to close is not an acceptance", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_an_accepted_review_alone_cannot_close_satisfyingly(self):
        self.accepted_candidate()
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("approval-due", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_an_approval_without_a_recorded_integration_cannot(self):
        self.accepted_candidate()
        self.assertEqual(self.approve()[0], 0)
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("integration-due", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_the_whole_selected_path_closes_and_binds_its_acceptance(self):
        self.delivered()
        code, out, err = self.close()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["closed"]["outcome"], "satisfying")
        self.assertEqual(said["actor"], OWNER)
        acceptance = said["acceptance"]
        self.assertTrue(acceptance["required"])
        self.assertEqual(acceptance["candidate_digest"], CANDIDATE)
        self.assertEqual(acceptance["verification"], "ver-proposal-1")
        self.assertEqual(acceptance["review"], "rev-proposal-1")
        self.assertEqual(acceptance["approval"], "app-1")
        self.assertEqual(acceptance["integration"], "int-1")
        self.assertEqual(acceptance["human_integration"]["commit"], COMMIT)
        self.assertEqual(acceptance["human_integration"]["reference"], RECORD)
        # READBACK: outcome, rationale and the decision the close was
        # authorized under all survive a fresh open.
        work = self.work_now()
        self.assertEqual(work["status"], "closed")
        self.assertEqual(work["outcome"], "satisfying")
        # THE RATIONALE CARRIES THE SELECTED ACCEPTANCE, durably: the operator's
        # own prose first, then this command's one canonical line.
        self.assertTrue(work["rationale"].startswith("pilot delivered"),
                        work["rationale"])
        operator, stored = disposition_command._rationale_parts(
            work["rationale"])
        self.assertEqual(operator, "pilot delivered")
        self.assertEqual(stored["schema"],
                         "baton.v12.owner-closure-acceptance/1")
        self.assertEqual(stored["candidate_digest"], CANDIDATE)
        self.assertEqual(stored["evidence_reference"], RECORD)
        self.assertEqual(stored["commit"], COMMIT)
        self.assertEqual(
            [stored[name] for name in
             ("verification", "review", "approval", "integration")],
            ["ver-proposal-1", "rev-proposal-1", "app-1", "int-1"])
        self.assertEqual(work["close_decision"]["endpoint"], OWNER)
        self.assertIsNone(work["phase"])
        # And every piece of evidence is still cited.
        self.assertEqual([one["reference"] for one in self.citations()],
                         [RECORD])

    def test_a_deleted_integration_record_refuses_the_satisfying_closure(self):
        self.delivered()
        os.unlink(os.path.join(self.repo, RECORD))
        code, out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("cites no intact human integration record", err)
        self.assertEqual(self.said(out)["citations_examined"][0]["state"],
                         "unusable")
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_rewritten_integration_record_refuses_it_too(self):
        # The receipt proves the owner recorded an integration of these bytes.
        # It does not prove the human's account of it still says what it said,
        # and a satisfying closure resting on a rewritten record would be
        # resting on nothing.
        self.delivered()
        self.write_record(self.record_document(notes="actually I did not"))
        code, out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("cites no intact human integration record", err)
        self.assertEqual(self.said(out)["citations_examined"][0]["state"],
                         "changed")
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_satisfying_closure_names_the_candidate_it_accepts(self):
        self.delivered()
        code, _out, err = self.close(**{"--proposal": None,
                                        "--expect-candidate-digest": None,
                                        "--root": None})
        self.assertEqual(code, 2)
        self.assertIn("names the candidate it accepts", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_changed_candidate_refuses_the_closure(self):
        self.delivered()
        code, _out, err = self.close(
            **{"--expect-candidate-digest": "sha256:" + "a" * 64})
        self.assertEqual(code, 2)
        self.assertIn("changed candidate refuses", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_non_satisfying_ending_needs_no_acceptance_and_keeps_evidence(self):
        self.accepted_candidate()
        self.assertEqual(self.approve(verb="deny")[0], 0)
        code, out, err = self.close(outcome="non-satisfying",
                                    **{"--rationale": "owner denied it"})
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertFalse(said["acceptance"]["required"])
        # THE ACCOUNT OF WHY, reported at the ending where it is most likely to
        # be wanted later: every proposal, every receipt and every citation.
        preserved = said["preserved"]
        self.assertEqual(preserved["dossier"]["locator"], LOCATOR)
        self.assertEqual(
            preserved["proposals"][0]["receipts"]["approval"]["disposition"],
            "denied")
        self.assertEqual(
            preserved["proposals"][0]["receipts"]["review"]["disposition"],
            "accepted")
        work = self.work_now()
        self.assertEqual(work["outcome"], "non-satisfying")
        # And the receipts are still readable after the close.
        self.assertEqual(self.receipt("approval")["disposition"], "denied")

    def test_an_ending_that_is_not_satisfying_takes_no_candidate_operands(self):
        # An operand supplied and ignored is one the caller believes it chose:
        # these three bind the acceptance a satisfying closure records, and
        # dropping them here would let an operator believe a cancelled Work
        # had been checked against that candidate.
        self.delivered()
        code, _out, err = self.close(
            outcome="cancelled",
            **{"--proposal": "proposal-1",
               "--expect-candidate-digest": CANDIDATE, "--root": self.repo})
        self.assertEqual(code, 2)
        self.assertIn("does not take --proposal", err)
        self.assertEqual(self.work_now()["status"], "open")
        # Without them it is an ordinary ending.
        code, _out, err = self.close(outcome="cancelled")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.work_now()["outcome"], "cancelled")

    def test_a_denied_candidate_cannot_be_closed_satisfyingly(self):
        self.accepted_candidate()
        self.assertEqual(self.approve(verb="deny")[0], 0)
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("'denied'", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_an_actor_without_the_close_capability_closes_nothing(self):
        self.delivered()
        authority = self.authority()
        for capability in ("approve", "integrate"):
            authority.grant_capability(STRANGER, capability, scope=self.scope)
        authority.dispose()
        code, _out, err = self.close(**{"--participant": STRANGER})
        self.assertEqual(code, 2)
        self.assertIn("close capability", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_an_unknown_outcome_refuses_before_anything_is_opened(self):
        self.delivered()
        code, _out, err = self.close(outcome="shipped")
        self.assertEqual(code, 2)
        self.assertIn("not a terminal outcome", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_an_exact_retry_replays_the_close(self):
        self.delivered()
        code, first, err = self.close()
        self.assertEqual(code, 0, err)
        code, again, err = self.close()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(again)["closed"],
                         self.said(first)["closed"])
        self.assertEqual(self.work_now()["outcome"], "satisfying")

    def test_closing_a_live_assignment_needs_its_exact_identity(self):
        # The pilot's own ending: the producer's assignment is still live when
        # the owner closes, and the authority refuses a close that would end it
        # without naming it.
        self.delivered()
        self.relive()
        self.assertIsNotNone(self.work_now()["assignment"])
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("must supply --expect-assignment", err)
        self.assertEqual(self.work_now()["status"], "open")
        self.assertIn("Nothing was changed", err)
        held = os.path.join(self.root, "assignment.json")
        with open(held, "w", encoding="utf-8") as handle:
            json.dump(self.work_now()["assignment"], handle)
        # THE SAME COMMAND IDENTITY, corrected. A refusal that happened before
        # the request was bound leaves the identity usable, which is what lets
        # an operator who forgot the operand simply add it and rerun.
        code, out, err = self.close(**{"--expect-assignment": held})
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(out)["closed"]["assignment"]["participant"],
                         WORKER)
        self.assertEqual(self.work_now()["status"], "closed")

    def test_a_stale_assignment_identity_refuses(self):
        self.delivered()
        self.relive()
        stale = dict(self.work_now()["assignment"], generation=99)
        held = os.path.join(self.root, "stale.json")
        with open(held, "w", encoding="utf-8") as handle:
            json.dump(stale, handle)
        code, _out, err = self.close(**{"--expect-assignment": held})
        self.assertEqual(code, 2)
        self.assertEqual(self.work_now()["status"], "open")
        self.assertTrue(err.startswith("refused:"), err)


class WhatOneIdentityMEANS(Fixture):
    """Review 2026-10-18T16-39-10Z: one command operation, one durable act.

    Both findings were the same shape one layer apart. The authority's own
    signature covers the operands IT takes, and this command's semantic
    operands -- which record, which commit, which acceptance -- were not among
    them. So a retry under one identity could mean something else and be
    answered as though it were the same act, and a retry that WAS the same act
    could be refused because the filesystem had moved on underneath it.
    """

    def delivered_and_closed(self):
        self.delivered()
        code, out, err = self.close()
        self.assertEqual(code, 0, err)
        return self.said(out)

    # -- integration ---------------------------------------------------------

    def test_a_retry_naming_another_record_refuses_and_cites_nothing(self):
        """The reviewer's reproduction, exactly: same integration operation,
        new document, new commit, new citation operation. It exited zero, added
        a second citation and reported the new commit beside the old
        receipt."""
        self.delivered()
        other = "work/records/2026/10/finding-pilot/OTHER.json"
        changed = "a" * 40
        self.write_record(self.record_document(commit=changed),
                          reference=other)
        code, out, err = self.integrated(
            reference=other, **{"--commit": changed,
                                "--evidence-operation-id": "op-cite-other"})
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)
        self.assertIn("different operands", err)
        self.assertIn("nothing was done", err)
        # NOTHING NEW WAS WRITTEN. One citation, still the original record,
        # and the receipt still names the integration the owner recorded.
        self.assertEqual([one["reference"] for one in self.citations()],
                         [RECORD])
        self.assertEqual(self.receipt("integration")["receipt_id"], "int-1")

    def test_a_retry_naming_another_receipt_or_actor_refuses(self):
        self.delivered()
        for what, changed in (
                ("another receipt identity", {"--integration-id": "int-9"}),
                ("another actor", {"--participant": REVIEWER}),
                ("another proposal", {"--proposal": "proposal-9"})):
            with self.subTest(what=what):
                code, _out, err = self.integrated(**changed)
                self.assertEqual(code, 2)
                self.assertEqual(len(self.citations()), 1)
        self.assertEqual(self.receipt("integration")["receipt_id"], "int-1")

    def test_a_retry_naming_another_citation_operation_refuses(self):
        self.delivered()
        code, _out, err = self.integrated(
            **{"--evidence-operation-id": "op-cite-9"})
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)
        self.assertEqual(len(self.citations()), 1)

    def test_an_exact_retry_replays_the_committed_integration(self):
        self.delivered()
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["integration"]["receipt_id"], "int-1")
        self.assertEqual(said["cited"]["reference"], RECORD)
        self.assertEqual(said["evidence_now"]["state"], "intact")
        self.assertEqual(said["evidence_now"]["commit"], COMMIT)
        self.assertEqual(len(self.citations()), 1)

    def test_a_retry_after_the_record_drifts_replays_and_reports_the_drift(self):
        """The integration COMMITTED. Somebody editing the record afterwards
        does not undo it, and a retry that refused would report failure for an
        act that happened -- so the drift is a separate fact beside the
        committed outcome."""
        self.delivered()
        self.write_record(self.record_document(notes="edited afterwards"))
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["evidence_now"]["state"], "changed")
        self.assertEqual(said["evidence_now"]["cited_digest"],
                         self.citations()[0]["digest"])
        self.assertEqual(said["integration"]["disposition"], "integrated")

    def test_a_retry_after_the_record_is_deleted_replays_and_says_so(self):
        self.delivered()
        os.unlink(os.path.join(self.repo, RECORD))
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["evidence_now"]["state"], "unusable")

    # -- closure -------------------------------------------------------------

    def test_the_closed_work_says_what_it_was_closed_ON(self):
        self.delivered_and_closed()
        code, out, err = self.run_verb("pending", *self.base(),
                                       "--work", WORK, "--root", self.repo)
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["owner_action"], "closed")
        self.assertEqual(said["rationale"], "pilot delivered")
        accepted = said["closure_acceptance"]
        self.assertEqual(accepted["proposal_id"], "proposal-1")
        self.assertEqual(accepted["candidate_digest"], CANDIDATE)
        self.assertEqual(accepted["commit"], COMMIT)
        self.assertEqual(accepted["evidence_reference"], RECORD)
        self.assertEqual([accepted[name] for name in
                          ("verification", "review", "approval",
                           "integration")],
                         ["ver-proposal-1", "rev-proposal-1", "app-1",
                          "int-1"])
        # AND WHO WAS AUTHORIZED TO CLOSE IT, on the same read.
        self.assertEqual(said["close_decision"]["endpoint"], OWNER)
        self.assertEqual(said["evidence_now"]["state"], "intact")

    def test_the_acceptance_survives_a_restart_and_a_fresh_open(self):
        # Nothing in the answer above comes from this process: a fresh
        # read-only open of the store on its own answers the same acceptance.
        self.delivered_and_closed()
        authority = Authority.open_readonly(self.store,
                                            expected_authority_uuid=UUID)
        try:
            held = authority.project_work(WORK)
        finally:
            authority.dispose()
        operator, accepted = disposition_command._rationale_parts(
            held["rationale"])
        self.assertEqual(operator, "pilot delivered")
        self.assertEqual(accepted["commit"], COMMIT)
        self.assertEqual(held["close_decision"]["principal"],
                         "principal:" + OWNER)

    def test_an_exact_close_retry_after_drift_replays_the_outcome(self):
        """The recovery case: the close committed, its answer was lost, and the
        record changed before the operator reran the command. The first cut
        re-derived the acceptance from the filesystem and exited 2 while the
        Work was already closed and satisfying."""
        self.delivered_and_closed()
        self.write_record(self.record_document(notes="changed after closing"))
        code, out, err = self.close()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["closed"]["outcome"], "satisfying")
        self.assertEqual(said["acceptance"]["commit"], COMMIT)
        self.assertEqual(said["evidence_now"]["state"], "changed")
        self.assertEqual(said["work_at_invocation"]["status"], "closed")
        self.assertEqual(self.work_now()["outcome"], "satisfying")

    def test_an_exact_close_retry_without_drift_replays_too(self):
        self.delivered_and_closed()
        code, out, err = self.close()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["evidence_now"]["state"], "intact")

    def test_a_changed_close_retry_refuses_rather_than_replaying(self):
        self.delivered_and_closed()
        # Two of these are caught by the DERIVED identity carrying another
        # act's close, and three by the request binding. Both are refusals
        # with nothing changed, and each says which it is.
        for what, changed, says in (
                ("another outcome", {"--outcome": "non-satisfying",
                                     "--proposal": None,
                                     "--expect-candidate-digest": None,
                                     "--root": None},
                 "already carries a 'satisfying' close"),
                ("another actor", {"--participant": REVIEWER},
                 "already carries a 'satisfying' close"),
                ("other prose", {"--rationale": "something else"},
                 "is not the one operation"),
                ("another proposal", {"--proposal": "proposal-9"},
                 "is not the one operation"),
                ("another candidate",
                 {"--expect-candidate-digest": "sha256:" + "b" * 64},
                 "is not the one operation")):
            with self.subTest(what=what):
                code, _out, err = self.close(**changed)
                self.assertEqual(code, 2)
                self.assertIn(says, err)
        # The committed closure is untouched by every one of them.
        work = self.work_now()
        self.assertEqual(work["outcome"], "satisfying")
        operator, accepted = disposition_command._rationale_parts(
            work["rationale"])
        self.assertEqual(operator, "pilot delivered")
        self.assertEqual(accepted["candidate_digest"], CANDIDATE)

    def test_a_satisfying_retry_cannot_omit_the_operands_it_is_compared_on(self):
        # The operand shape is a rule about the REQUEST, so it is checked
        # before any state is read -- otherwise a retry that dropped the
        # candidate operands would reach the replay path and be answered
        # without the comparison those operands exist for.
        self.delivered_and_closed()
        code, _out, err = self.close(**{"--proposal": None,
                                        "--expect-candidate-digest": None,
                                        "--root": None})
        self.assertEqual(code, 2)
        self.assertIn("names the candidate it accepts", err)

    def test_a_non_satisfying_retry_still_takes_no_candidate_operands(self):
        self.accepted_candidate()
        self.assertEqual(self.approve(verb="deny")[0], 0)
        code, _out, err = self.close(outcome="non-satisfying",
                                     **{"--rationale": "denied"})
        self.assertEqual(code, 0, err)
        code, _out, err = self.close(
            outcome="non-satisfying",
            **{"--rationale": "denied", "--proposal": "proposal-1",
               "--expect-candidate-digest": CANDIDATE, "--root": self.repo})
        self.assertEqual(code, 2)
        self.assertIn("does not take --proposal", err)

    def test_a_second_close_under_a_NEW_identity_is_refused_by_the_authority(self):
        # Not a replay and not a collision: the Work is terminal, and that is
        # the authority's own sentence rather than this command's.
        self.delivered_and_closed()
        code, _out, err = self.close(**{"--operation-id": "op-close-2"})
        self.assertEqual(code, 2)
        self.assertIn("already closed", err)

    def test_a_rationale_cannot_carry_a_handwritten_acceptance(self):
        self.delivered()
        code, _out, err = self.close(
            **{"--rationale": "done owner-closure-acceptance: {\"schema\": 1}"})
        self.assertEqual(code, 2)
        self.assertIn("this command composes it", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_non_satisfying_closure_records_prose_and_no_acceptance(self):
        self.accepted_candidate()
        self.assertEqual(self.approve(verb="deny")[0], 0)
        code, out, err = self.close(outcome="non-satisfying",
                                    **{"--rationale": "owner denied it"})
        self.assertEqual(code, 0, err)
        self.assertFalse(self.said(out)["acceptance"]["required"])
        work = self.work_now()
        self.assertEqual(work["rationale"], "owner denied it")
        operator, accepted = disposition_command._rationale_parts(
            work["rationale"])
        self.assertIsNone(accepted)
        code, out, err = self.run_verb("pending", *self.base(), "--work", WORK)
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertIsNone(said["closure_acceptance"])
        self.assertEqual(said["rationale"], "owner denied it")
        self.assertEqual(said["close_decision"]["endpoint"], OWNER)
        # An exact retry of a non-satisfying close replays as well.
        code, out, err = self.close(outcome="non-satisfying",
                                    **{"--rationale": "owner denied it"})
        self.assertEqual(code, 0, err)
        self.assertTrue(self.said(out)["replayed"])


class WhatTheREQUESTBindingDecides(Fixture):
    """Review 2026-10-18T16-55-00Z: the comparison must not read the files.

    Two cuts of this command compared semantic operands by hand -- against the
    committed receipt, the citation row, and the cited file's current bytes.
    Review broke both with one move: edit the record, then retry with a
    different commit. So the complete canonical request is now journalled under
    the command's own operation identity and the AUTHORITY decides whether an
    invocation is the same act.
    """

    # -- the reviewer's two reproductions, as cases --------------------------

    def test_a_changed_commit_refuses_even_after_the_record_drifts(self):
        """`evidence/review-324482/reproduce.py`, `changed_commit_after_drift`:
        exit 0 and replayed=true before this correction."""
        self.delivered()
        self.write_record(self.record_document(notes="later drift"))
        code, out, err = self.integrated(**{"--commit": "a" * 40})
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)
        said = self.said(out)
        self.assertFalse(said["replayed"])
        self.assertEqual(said["performed"], "nothing")
        # The answer shows BOTH requests, which is the one thing an operator
        # cannot work out from their own command line.
        self.assertEqual(said["already_carries"]["request"]["commit"], COMMIT)
        self.assertEqual(said["this_request"]["commit"], "a" * 40)
        self.assertEqual(len(self.citations()), 1)
        self.assertEqual(self.receipt("integration")["receipt_id"], "int-1")

    def test_a_changed_commit_refuses_even_after_the_record_is_deleted(self):
        # The stronger form of the same rule: with no bytes at all there is
        # nothing on disk left to compare, and the request binding does not
        # need any.
        self.delivered()
        os.unlink(os.path.join(self.repo, RECORD))
        code, _out, err = self.integrated(**{"--commit": "b" * 40})
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)
        self.assertEqual(len(self.citations()), 1)
        # And the EXACT retry still replays, with the deletion reported.
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["evidence_now"]["state"], "unusable")

    def test_an_added_assignment_precondition_refuses_on_retry(self):
        """`changed_close_assignment`: a close performed with no assignment
        precondition could be retried WITH one and be answered as a replay,
        dropping the compare-and-swap the authority's close signature
        distinguishes."""
        self.delivered()
        code, _out, err = self.close()
        self.assertEqual(code, 0, err)
        held = os.path.join(self.root, "changed-assignment.json")
        with open(held, "w", encoding="utf-8") as handle:
            json.dump(self.assignment, handle)
        code, out, err = self.close(**{"--expect-assignment": held})
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)
        said = self.said(out)
        self.assertIsNone(said["already_carries"]["request"]["expect_assignment"])
        self.assertEqual(said["this_request"]["expect_assignment"],
                         self.assignment)
        self.assertEqual(said["performed"], "nothing")

    def test_a_dropped_assignment_precondition_refuses_too(self):
        # The other direction, because presence is part of the request: a close
        # performed WITH a precondition retried without one is not that act.
        self.delivered()
        self.relive()
        held = os.path.join(self.root, "assignment.json")
        with open(held, "w", encoding="utf-8") as handle:
            json.dump(self.work_now()["assignment"], handle)
        code, _out, err = self.close(**{"--expect-assignment": held})
        self.assertEqual(code, 0, err)
        code, out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)
        self.assertIsNotNone(
            self.said(out)["already_carries"]["request"]["expect_assignment"])

    # -- the binding itself --------------------------------------------------

    def test_the_authority_binds_one_request_to_one_identity(self):
        authority = self.authority()
        request = {"verb": "integrated", "commit": COMMIT}
        first = authority.bind_request(WORK, request, operation_id="op-r")
        self.assertEqual(first["verb"], "integrated")
        self.assertEqual(first["request"], request)
        # An exact retry replays the committed binding.
        self.assertEqual(
            authority.bind_request(WORK, dict(request), operation_id="op-r"),
            first)
        # A changed member collides, whichever member it is.
        for changed in ({"verb": "integrated", "commit": "a" * 40},
                        {"verb": "close", "commit": COMMIT},
                        {"verb": "integrated", "commit": COMMIT, "more": 1},
                        {"verb": "integrated"}):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(Refusal, "different operands"):
                    authority.bind_request(WORK, changed, operation_id="op-r")
        # It performs no transition: the Work reads the same afterwards.
        self.assertEqual(authority.project_work(WORK)["status"], "open")
        self.assertIsNone(authority.project_work(WORK)["outcome"])
        authority.dispose()

    def test_a_request_names_its_verb_its_work_and_is_a_document(self):
        authority = self.authority()
        for what, request in (("no verb", {"commit": COMMIT}),
                              ("an empty verb", {"verb": ""}),
                              ("a verb that is not text", {"verb": 7}),
                              ("an empty document", {}),
                              ("not a document", ["verb"]),
                              ("not data at all", object())):
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    authority.bind_request(WORK, request, operation_id="op-x")
        with self.assertRaises(Refusal):
            authority.bind_request(OTHER, {"verb": "close"},
                                   operation_id="op-y")
        # And nothing was journalled for any of them.
        self.assertIsNone(authority.operation_result("op-x"))
        self.assertIsNone(authority.operation_result("op-y"))
        authority.dispose()

    def test_a_command_identity_too_long_to_derive_from_refuses(self):
        self.accepted_candidate()
        code, _out, err = self.approve()
        self.assertEqual(code, 0, err)
        self.write_record()
        code, _out, err = self.integrated(**{"--operation-id": "o" * 158})
        self.assertEqual(code, 2)
        self.assertIn("at most 160 characters", err)
        self.assertEqual(self.citations(), [])


class WhatJUSTIFIESSkippingValidation(Fixture):
    """Review 2026-10-18T17-12-52Z: a journal result is not a provenance.

    The previous cut read the journal at the operator-supplied citation
    identity and treated ANY result there as proof that this command had
    already validated the human's record. So an ordinary `record cite` under
    that identity let a fresh request skip validation and write an integration
    receipt for a commit nobody had read. Only this complete request having
    been validated and BOUND before may justify that skip, and a result at
    either identity must be this act's own act.
    """

    def approved(self):
        self.accepted_candidate()
        code, _out, err = self.approve()
        self.assertEqual(code, 0, err)

    def cite(self, digest, reference=RECORD, operation_id="op-cite-1"):
        """An ordinary dossier citation, made by something that is not this
        command -- which is exactly what `record cite` is."""
        authority = self.authority()
        held = authority.record_dossier_evidence(
            WORK, reference, digest, operation_id=operation_id)
        authority.dispose()
        return held

    def record_digest(self):
        """The digest of the integration record as it stands on disk."""
        import hashlib

        with open(os.path.join(self.repo, RECORD), "rb") as handle:
            return "sha256:" + hashlib.sha256(handle.read()).hexdigest()

    def integration_request(self, digest=None, **changed):
        """The request document this command would bind, built through the
        command's own helper so the test cannot drift from it."""
        import argparse

        taken = argparse.Namespace(
            participant=OWNER, work=WORK, proposal="proposal-1",
            expect_candidate_digest=CANDIDATE, reference=RECORD,
            commit=COMMIT, integration_id="int-1",
            evidence_operation_id="op-cite-1")
        for name, value in changed.items():
            setattr(taken, name, value)
        return disposition_command._integration_request(
            taken, self.record_digest() if digest is None else digest)

    def test_a_standalone_citation_does_not_make_a_record_validated(self):
        """`evidence/review-324601/reproduce.py`, exactly: a citation at the
        command's evidence identity, no integration record anywhere, and
        before this correction a fresh request wrote a receipt claiming a
        commit nobody had read."""
        self.approved()
        self.cite("sha256:" + "9" * 64)
        code, _out, err = self.integrated(**{"--commit": "a" * 40})
        self.assertEqual(code, 2)
        self.assertIn("'absent'", err)
        self.assertIsNone(self.receipt("integration"))
        # The unrelated citation is untouched: this command added nothing and
        # removed nothing.
        self.assertEqual([one["digest"] for one in self.citations()],
                         ["sha256:" + "9" * 64])

    def test_a_citation_of_other_bytes_STAYS_refused_however_often_it_is_run(self):
        """`evidence/review-324673/reproduce.py`: the same command twice. The
        first call refused and the second wrote a receipt on the incompatible
        citation, because the request binding survived the refusal and nothing
        afterwards compared the digest it had validated."""
        self.approved()
        self.write_record()
        self.cite("sha256:" + "9" * 64)
        for attempt in (1, 2, 3):
            with self.subTest(attempt=attempt):
                code, out, err = self.integrated()
                self.assertEqual(code, 2)
                self.assertIn("this integration validated", err)
                said = self.said(out)
                self.assertEqual(said["performed"], "nothing")
                self.assertEqual(said["already_recorded"]["digest"],
                                 "sha256:" + "9" * 64)
                self.assertEqual(said["validated_digest"],
                                 self.record_digest())
                self.assertIsNone(self.receipt("integration"))
        # The identity was never consumed -- but changing only the citation
        # operand does not help, and the refusal says why: W321688's rule is
        # that a durable citation is not rewritten in place, and this
        # reference is already cited at other bytes.
        code, _out, err = self.integrated(
            **{"--evidence-operation-id": "op-cite-fresh"})
        self.assertEqual(code, 2)
        self.assertIn("not rewritten in place", err)
        self.assertIsNone(self.receipt("integration"))
        # THE HONEST RECOVERY is the one that sentence names: the same record
        # under its own reference, as its own request.
        beside = "work/records/2026/10/finding-pilot/INTEGRATION-2.json"
        self.write_record(reference=beside)
        code, out, err = self.integrated(
            reference=beside, **{"--operation-id": "op-integrated-2",
                                 "--evidence-operation-id": "op-cite-2"})
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(out)["cited"]["reference"], beside)
        self.assertEqual(self.receipt("integration")["receipt_id"], "int-1")

    def test_a_standalone_citation_of_the_SAME_bytes_is_convergent(self):
        # The legitimate overlap: somebody cited this exact record already.
        # Re-offering it answers the same row, and the integration proceeds on
        # a record this command read and validated itself.
        self.approved()
        whole = self.write_record()
        import hashlib

        with open(whole, "rb") as handle:
            digest = "sha256:" + hashlib.sha256(handle.read()).hexdigest()
        self.cite(digest)
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(out)["cited"]["digest"], digest)
        self.assertEqual(self.receipt("integration")["receipt_id"], "int-1")
        self.assertEqual(len(self.citations()), 1)

    def test_an_identity_carrying_something_that_is_not_a_citation_refuses(self):
        self.approved()
        self.write_record()
        authority = self.authority()
        authority.bind_request(WORK, {"verb": "something-else"},
                               operation_id="op-cite-1")
        authority.dispose()
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("not a dossier citation at all", err)
        self.assertIsNone(self.receipt("integration"))
        self.assertEqual(self.citations(), [])

    def test_an_identity_carrying_another_references_citation_refuses(self):
        self.approved()
        self.write_record()
        self.cite("sha256:" + "9" * 64,
                  reference="work/records/2026/10/finding-pilot/OTHER.json")
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("already cited", err)
        self.assertIn("OTHER.json", err)
        self.assertIsNone(self.receipt("integration"))

    def test_a_derived_identity_carrying_another_receipt_refuses(self):
        # The derived receipt identity is `<operation-id>:integrate`. If
        # something else already committed an integration there, this call is
        # not that act and must not report its receipt as its own.
        self.approved()
        self.write_record()
        authority = self.authority()
        authority.session(OWNER).integrate(
            {"proposal_id": "proposal-1", "integration_id": "int-other",
             "operation_id": "op-integrated-1:integrate"})
        authority.dispose()
        code, _out, err = self.integrated()
        self.assertEqual(code, 2)
        self.assertIn("already carries integration receipt 'int-other'", err)
        # Nothing of this call's own was written.
        self.assertEqual(self.citations(), [])
        self.assertEqual(self.receipt("integration")["receipt_id"],
                         "int-other")

    def test_a_derived_close_identity_carrying_another_act_refuses(self):
        self.delivered()
        authority = self.authority()
        authority.bind_request(WORK, {"verb": "not-a-close"},
                               operation_id="op-close-1:close")
        authority.dispose()
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("is not a close", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_bound_request_whose_citation_never_committed_completes(self):
        """GENUINE PARTIAL RECOVERY, which the skip rule must not break: the
        request was validated and bound, then the process died before the
        citation. The next identical invocation validates again -- it needs the
        digest -- and completes both acts."""
        self.approved()
        self.write_record()
        authority = self.authority()
        authority.bind_request(WORK, self.integration_request(),
                               operation_id="op-integrated-1")
        authority.dispose()
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertFalse(said["replayed"])
        self.assertEqual(said["cited"]["reference"], RECORD)
        self.assertEqual(said["integration"]["receipt_id"], "int-1")

    def test_a_bound_request_completes_from_the_journal_after_drift(self):
        """The same partial recovery with the record edited in between. The
        digest to cite comes from the BINDING, so the citation completes and
        still names exactly the bytes this request validated -- and the drift
        is reported rather than hidden. Before the digest was bound this
        refused, because it re-read the file to find something to cite."""
        self.approved()
        self.write_record()
        validated = self.record_digest()
        authority = self.authority()
        authority.bind_request(WORK, self.integration_request(validated),
                               operation_id="op-integrated-1")
        authority.dispose()
        self.write_record(self.record_document(notes="edited in between"))
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["cited"]["digest"], validated)
        self.assertEqual(said["evidence_now"]["state"], "changed")
        self.assertEqual(said["integration"]["receipt_id"], "int-1")
        # AND THE CLOSURE STILL REFUSES, which is what keeps this honest: the
        # integration is recorded against the validated bytes, and a satisfying
        # closure requires the cited record to be intact right now.
        code, _out, err = self.close()
        self.assertEqual(code, 2)
        self.assertIn("no intact human integration record", err)
        self.assertEqual(self.work_now()["status"], "open")

    def test_a_completed_integration_still_replays_after_drift(self):
        # And the recovery the skip rule exists for keeps working: both acts
        # committed under this request, the record has since been edited, and
        # an identical invocation replays rather than revalidating.
        self.delivered()
        self.write_record(self.record_document(notes="edited afterwards"))
        code, out, err = self.integrated()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertTrue(said["replayed"])
        self.assertEqual(said["evidence_now"]["state"], "changed")
        self.assertEqual(len(self.citations()), 1)


class TheFailureMatrix(Fixture):
    """Review 2026-10-18T17-21-14Z asks for the matrix rather than another
    single case: repeat and restart the command after a bounded failure at
    EVERY point between validation, binding, citation and receipt.

    Three corrections in a row came from the same place -- what one invocation
    may assume about what an earlier one did -- so the invariant is stated as a
    table of interruptions instead of as another anecdote. Each case stops the
    command at one stage, reruns it, and says what must be true afterwards.
    """

    def approved(self):
        self.accepted_candidate()
        code, _out, err = self.approve()
        self.assertEqual(code, 0, err)
        self.write_record()

    def digest(self):
        import hashlib

        with open(os.path.join(self.repo, RECORD), "rb") as handle:
            return "sha256:" + hashlib.sha256(handle.read()).hexdigest()

    def request(self, digest=None):
        import argparse

        taken = argparse.Namespace(
            participant=OWNER, work=WORK, proposal="proposal-1",
            expect_candidate_digest=CANDIDATE, reference=RECORD,
            commit=COMMIT, integration_id="int-1",
            evidence_operation_id="op-cite-1")
        return disposition_command._integration_request(
            taken, self.digest() if digest is None else digest)

    def stop_after(self, stage):
        """Leave the authority in the state a crash at `stage` would leave.

        Each state is built through the PUBLIC acts the command itself uses,
        in the command's own order, so these are the states a real
        interruption produces rather than hand-made rows.
        """
        authority = self.authority()
        if stage in ("binding", "citation"):
            authority.bind_request(WORK, self.request(),
                                   operation_id="op-integrated-1")
        if stage == "citation":
            authority.record_dossier_evidence(
                WORK, RECORD, self.digest(), operation_id="op-cite-1")
        authority.dispose()

    def test_an_interruption_at_each_stage_is_recovered_by_the_same_command(self):
        for stage, expect_cited, expect_receipt in (
                ("validation", False, False),
                ("binding", False, False),
                ("citation", True, False)):
            with self.subTest(stage=stage):
                self.setUp()
                self.approved()
                self.stop_after(stage)
                self.assertEqual(bool(self.citations()), expect_cited)
                self.assertIs(self.receipt("integration") is not None,
                              expect_receipt)
                code, out, err = self.integrated()
                self.assertEqual(code, 0, err)
                said = self.said(out)
                self.assertEqual(said["cited"]["digest"], self.digest())
                self.assertEqual(said["integration"]["receipt_id"], "int-1")
                self.assertEqual(said["evidence_now"]["state"], "intact")
                self.assertEqual(len(self.citations()), 1)

    def test_an_interruption_at_each_stage_survives_the_record_being_edited(self):
        # The same table with the record edited after the interruption, and the
        # rows differ in WHICH bytes get cited -- which is the whole point of
        # binding the digest.
        #
        #   validation: nothing was bound, so there is no provenance to take a
        #     digest from. This is an ordinary first execution: it validates
        #     what is on disk NOW and cites that.
        #   binding, citation: the validated digest is in the journal, so the
        #     recovery cites exactly the bytes the first attempt validated and
        #     reports the drift beside it.
        for stage, from_binding in (("validation", False), ("binding", True),
                                    ("citation", True)):
            with self.subTest(stage=stage):
                self.setUp()
                self.approved()
                validated = self.digest()
                self.stop_after(stage)
                self.write_record(self.record_document(notes="edited"))
                code, out, err = self.integrated()
                self.assertEqual(code, 0, err)
                said = self.said(out)
                self.assertEqual(said["integration"]["receipt_id"], "int-1")
                if from_binding:
                    self.assertEqual(said["cited"]["digest"], validated)
                    self.assertEqual(said["evidence_now"]["state"], "changed")
                else:
                    self.assertEqual(said["cited"]["digest"], self.digest())
                    self.assertNotEqual(said["cited"]["digest"], validated)
                    self.assertEqual(said["evidence_now"]["state"], "intact")

    def test_an_interruption_at_each_stage_survives_the_record_being_deleted(self):
        for stage, expect in (("validation", 2), ("binding", 0),
                              ("citation", 0)):
            with self.subTest(stage=stage):
                self.setUp()
                self.approved()
                validated = self.digest()
                self.stop_after(stage)
                os.unlink(os.path.join(self.repo, RECORD))
                code, out, err = self.integrated()
                self.assertEqual(code, expect, err)
                if expect == 0:
                    said = self.said(out)
                    self.assertEqual(said["cited"]["digest"], validated)
                    self.assertEqual(said["evidence_now"]["state"], "unusable")
                else:
                    self.assertIsNone(self.receipt("integration"))

    def test_a_changed_request_after_an_interruption_refuses_at_every_stage(self):
        # And no interruption makes a DIFFERENT request acceptable: once the
        # request is bound, a changed commit collides whatever has or has not
        # happened since, and before it is bound the record itself refuses the
        # changed commit.
        for stage, says in (("validation", "one integration has one commit"),
                            ("binding", "is not the one operation"),
                            ("citation", "is not the one operation")):
            with self.subTest(stage=stage):
                self.setUp()
                self.approved()
                self.stop_after(stage)
                code, _out, err = self.integrated(**{"--commit": "a" * 40})
                self.assertEqual(code, 2)
                self.assertIn(says, err)
                self.assertIsNone(self.receipt("integration"))

    def test_a_completed_command_replays_at_every_later_invocation(self):
        self.approved()
        code, first, err = self.integrated()
        self.assertEqual(code, 0, err)
        for attempt in (2, 3):
            with self.subTest(attempt=attempt):
                code, again, err = self.integrated()
                self.assertEqual(code, 0, err)
                self.assertTrue(self.said(again)["replayed"])
                self.assertEqual(self.said(again)["integration"],
                                 self.said(first)["integration"])
                self.assertEqual(self.said(again)["cited"],
                                 self.said(first)["cited"])
                self.assertEqual(len(self.citations()), 1)

    def test_the_closure_recovers_the_same_way_at_each_of_its_stages(self):
        # `close` has two stages -- the binding and the close itself -- and the
        # same rule: an interruption between them is recovered by the same
        # command, and a changed request after either is refused.
        self.approved()
        code, _out, err = self.integrated()
        self.assertEqual(code, 0, err)
        authority = self.authority()
        authority.bind_request(
            WORK, disposition_command._closure_request(
                argparse_namespace(
                    participant=OWNER, work=WORK, outcome="satisfying",
                    rationale="pilot delivered", proposal="proposal-1",
                    expect_candidate_digest=CANDIDATE), None),
            operation_id="op-close-1")
        authority.dispose()
        self.assertEqual(self.work_now()["status"], "open")
        code, out, err = self.close()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(out)["closed"]["outcome"], "satisfying")
        # The completed close replays, and a changed one refuses.
        code, out, err = self.close()
        self.assertEqual(code, 0, err)
        self.assertTrue(self.said(out)["replayed"])
        code, _out, err = self.close(**{"--rationale": "something else"})
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation", err)


def argparse_namespace(**members):
    """The operand carrier this command's helpers read, for the cases that
    build a request document without running the command."""
    import argparse

    return argparse.Namespace(**members)


class ThePublicationInventory(Fixture):
    """`Authority.proposals_of`: the read the pending answer needs."""

    def test_it_answers_this_works_candidates_in_publication_order(self):
        self.publish("proposal-1")
        self.publish("proposal-2", candidate_digest="sha256:" + "7" * 64)
        authority = Authority.open_readonly(self.store,
                                            expected_authority_uuid=UUID)
        try:
            held = authority.proposals_of(WORK)
            self.assertEqual([one["proposal_id"] for one in held],
                             ["proposal-1", "proposal-2"])
            self.assertEqual(held[1]["candidate_digest"],
                             "sha256:" + "7" * 64)
            # A Work that has published nothing answers an empty list rather
            # than refusing: "no candidate" is an answer.
            self.assertEqual(authority.proposals_of(OTHER), [])
            with self.assertRaises(Refusal):
                authority.proposals_of("not-a-work-id")
        finally:
            authority.dispose()

    def test_another_works_candidates_are_not_in_this_answer(self):
        self.publish("proposal-1")
        authority = self.authority()
        authority.create_work(OTHER, ROUTE, operation_id="op-create-2",
                              contract=V12)
        authority.add_route_handler(ROUTE, SECOND)
        elsewhere = authority.session(SECOND).claim(
            {"work_id": OTHER, "operation_id": "op-claim-2"})["assignment"]
        authority.session(SECOND).publish(
            dict({"expect": elsewhere, "operation_id": "op-pub-2",
                  "proposal_id": "proposal-other"}, **DIGESTS))
        self.assertEqual([one["proposal_id"]
                          for one in authority.proposals_of(WORK)],
                         ["proposal-1"])
        self.assertEqual([one["proposal_id"]
                          for one in authority.proposals_of(OTHER)],
                         ["proposal-other"])
        authority.dispose()


class TheInstalledSurface(Fixture):
    """That the deployed command is where this lives."""

    def test_the_subcommand_is_registered_and_its_help_needs_no_store(self):
        self.assertIn("disposition", stack_command.COMMANDS)
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as caught:
                stack_command.main(["disposition", "--help"])
        self.assertEqual(caught.exception.code, 0)
        said = out.getvalue()
        for verb in ("pending", "approve", "deny", "integrated", "close"):
            self.assertIn(verb, said)
        # And it says what it will not do, where an operator reads it.
        self.assertIn("runs no Git command", said)

    def test_a_verb_is_required_rather_than_defaulted(self):
        with self.assertRaises(SystemExit):
            self.run_verb(*self.base())


if __name__ == "__main__":
    unittest.main()
