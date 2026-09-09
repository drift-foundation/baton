"""W71875 — the seam onto the v12 operations, driven against the real ones.

THE IDENTITIES ARE PINNED HERE, and that is the point of the file. This
control plane decides whether a restart already performed an act by asking the
Worker Manager's journal for an operation identity IT DERIVES. If the manager
ever spelled that identity differently, every sweep would repeat a committed
offer -- so these cases call `issue_offer` and the claim for real and assert
the manager journalled exactly what `canonical_operation` builds.

The rest of the file proves the other half of the composition claim: the
observation is four public reads and no opinion, and the bearer `issue_offer`
answers with is delivered once and stored nowhere.
"""

import copy
import json
import unittest

from baton_v12.contracts import ContractRefusal
# W126558: the optional member is imported from its OWNER rather than
# the package. `job_manager/__init__.py` is not among this Work's seven
# paths, so re-exporting it there is a bounded follow-up the handoff
# names rather than an edit taken on the way past.
from baton_v12.job_manager import delegation
from baton_v12.job_manager.delegation import OBSERVATION_OPTIONAL
from baton_v12.job_manager import (CANONICAL_OPERATIONS, INTENT_OPERANDS,
                                   OBSERVATION_MEMBERS, OPERATIONS,
                                   ManagerOperations, Unobserved,
                                   canonical_operation, check_binding, job_of,
                                   stage_intent, stage_rows, submit)
from baton_v12.worker_manager import accept_offer

if __package__:
    from .fixtures import NOW, WORK_A, JobManagerCase, job, submission
else:
    from fixtures import NOW, WORK_A, JobManagerCase, job, submission


class CanonicalIdentities(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission())
        self.stages = {row["stage_id"]: self.attempting(self.jobs,
                                                        row["stage_id"])
                       for row in stage_rows(self.jobs)}
        self.stage = self.stages["job-a/implementation"]
        self.job = {"input_digest": "sha256:" + "1" * 64,
                    "policy_digest": "sha256:" + "2" * 64}
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def accept(self):
        issued = self.delivered[-1]
        return accept_offer(self.control_store, self.acts.port,
                            offer_id=self.stage["offer_id"], decision="accept",
                            bearer=issued["bearer"], now=NOW,
                            runtime_attempt_id=self.stage["attempt_id"],
                            work_ref={"authority_uuid": "0" * 31 + "a",
                                      "work_id": WORK_A})

    def test_the_manager_journals_the_admit_identity_this_build_derives(self):
        self.acts.admit(self.stage, self.job)
        derived = canonical_operation("admit", self.stage["offer_id"])
        self.assertEqual(derived, f"offer.issue:{self.stage['offer_id']}")
        self.assertNotIn("/", self.stage["offer_id"])
        record = self.acts.receipt_of(derived)
        self.assertIsNotNone(
            record,
            "the Job manager decides what a restart already did by asking the "
            "manager's journal for this identity; a spelling change here "
            "would make every sweep repeat the offer")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["kind"], "offer.issue")

    def test_the_manager_journals_the_claim_identity_this_build_derives(self):
        self.acts.admit(self.stage, self.job)
        self.accept()
        self.acts.claim(self.stage)
        derived = canonical_operation("claim", self.stage["offer_id"])
        self.assertEqual(derived, f"offer.settle:{self.stage['offer_id']}")
        record = self.acts.receipt_of(derived)
        self.assertIsNotNone(record)
        self.assertEqual(record["kind"], "offer.settle")

    def test_an_act_outside_the_closed_vocabulary_is_refused(self):
        with self.assertRaises(ContractRefusal):
            canonical_operation("integrate", "offer:x")

    def test_both_acts_have_a_template(self):
        self.assertEqual(sorted(CANONICAL_OPERATIONS), ["admit", "claim"])


class TheBearer(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission())
        self.stage = self.attempting(self.jobs)
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def test_the_bearer_is_minted_delivered_once_and_answered_nowhere(self):
        answer = self.acts.admit(self.stage,
                                 {"input_digest": "sha256:" + "1" * 64,
                                  "policy_digest": "sha256:" + "2" * 64})
        self.assertIsNone(answer, "an act answers nothing a caller could "
                                  "mistake for the secret")
        self.assertEqual(self.minted, ["bearer-1"])
        self.assertEqual(len(self.delivered), 1)
        self.assertEqual(self.delivered[0]["bearer"], "bearer-1")

    def test_no_durable_row_in_either_store_carries_the_bearer(self):
        self.acts.admit(self.stage, {"input_digest": "sha256:" + "1" * 64,
                                     "policy_digest": "sha256:" + "2" * 64})
        for store in (self.jobs, self.control_store):
            for row in store._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"):
                for entry in store._connection.execute(
                        f"SELECT * FROM {row[0]}").fetchall():
                    for value in tuple(entry):
                        self.assertNotIn("bearer-1", str(value))

    def test_a_capability_that_cannot_be_called_is_refused_at_construction(self):
        with self.assertRaises(ContractRefusal):
            ManagerOperations(self.control_store, self.acts.port,
                              mint_bearer=None, deliver_bearer=self.deliver)
        with self.assertRaises(ContractRefusal):
            ManagerOperations(self.control_store, self.acts.port,
                              mint_bearer=self.mint, deliver_bearer="nope")


class Observation(JobManagerCase):

    def test_an_unstarted_stage_observes_absence_rather_than_a_guess(self):
        jobs = self.store()
        submit(jobs, submission())
        stage = self.attempting(jobs)
        observed = self.operations().observe(stage)
        self.assertEqual(sorted(observed),
                         sorted(OBSERVATION_MEMBERS + OBSERVATION_OPTIONAL))
        self.assertEqual(observed, {"claimed_by": None, "runtime": None,
                                    "activity": None, "output": None,
                                    "start_failure": None,
                                    "preparation_failure": None,
                                    # W81857: a deployment that supplied no
                                    # exchange read answers `None`, which is
                                    # "nobody looked" rather than "nothing is
                                    # happening".
                                    "exchange": None,
                                    # W126558: and the same answer for the
                                    # integration read, for the same reason.
                                    "integration": None})

    def test_the_closed_surface_is_what_a_deployment_must_supply(self):
        acts = self.operations()
        for member in OPERATIONS:
            self.assertTrue(hasattr(acts, member), member)

    def test_the_runtime_refresh_is_a_capability_and_not_a_read(self):
        """W85500: absent means `None`, and `None` means nobody looked.

        Every OTHER missing capability on this surface REFUSES, because a
        control plane that cannot start, command or end a worker is reporting
        work it can never do. This one is different and deliberately so: a
        deployment with no engine is a real deployment, and silence about a
        runtime is not the same claim as a runtime that is gone.
        """
        acts = self.operations()
        self.assertIsNone(acts.refresh_runtime({"stage_id": "job-a/x",
                                                "attempt_id": "attempt-1"}))

    def test_a_supplied_refresh_is_called_with_the_attempted_stage(self):
        seen = []
        acts = self.operations(refresh_runtime=lambda stage: seen.append(
            stage) or {"execution_runtime": "quiescent"})
        answer = acts.refresh_runtime({"stage_id": "job-a/x",
                                       "attempt_id": "attempt-1"})
        self.assertEqual(answer, {"execution_runtime": "quiescent"})
        self.assertEqual(seen, [{"stage_id": "job-a/x",
                                 "attempt_id": "attempt-1"}])

    def test_the_refresh_answer_is_an_exact_document_with_exactly_one_member(
            self):
        """W85500 re-review 2026-09-04T19:08:40Z [P1].

        `isinstance(answer, dict)` plus `.get` is a floor rather than a
        contract. An undeclared member was accepted and silently discarded --
        so a deployment that answered a second fact was told nothing, and a
        build that started reading that member would change meaning under a
        deployment that never heard about it. And a `dict` SUBCLASS reached
        the boundary as itself, so its own `.get` ran INSIDE the validation
        and whatever it raised came out of the seam that exists to stop
        exactly that.
        """

        class Hostile(dict):
            def get(self, *_args, **_kwargs):
                raise RuntimeError("a subclass method ran inside the boundary")

        stage = {"stage_id": "job-a/x", "attempt_id": "attempt-1"}
        for wrong in ({"execution_runtime": "quiescent", "unexpected": 1},
                      Hostile(execution_runtime="quiescent")):
            acts = self.operations(refresh_runtime=lambda _stage, answer=wrong:
                                   answer)
            with self.assertRaises(ContractRefusal) as raised:
                acts.refresh_runtime(stage)
            self.assertEqual((raised.exception.category,
                              raised.exception.code),
                             ("integrity", "schema"), wrong)
        # AND THE ANSWER THAT IS ACCEPTED IS THIS SEAM'S OWN COPY, so a
        # deployment holding a reference to what it returned cannot reach into
        # what the sweep is about to project.
        answered = {"execution_runtime": "quiescent"}
        acts = self.operations(refresh_runtime=lambda _stage: answered)
        taken = acts.refresh_runtime(stage)
        self.assertEqual(taken, answered)
        self.assertIsNot(taken, answered)

    def test_a_refresh_that_cannot_be_called_is_refused_before_it_is_spent(
            self):
        """Typed at construction, like every other capability here: one that
        could not be called would otherwise fault in the middle of a sweep."""
        with self.assertRaises(ContractRefusal):
            self.operations(refresh_runtime="not a capability")

    def test_a_status_surface_with_no_control_store_refuses_every_act(self):
        # `observe` still answers -- emptily -- because a read-only status has
        # to be able to say "nobody looked" without pretending it did.
        unobserved = Unobserved()
        self.assertFalse(unobserved.canonical)
        # W85500: AND THE REFRESH ANSWERS `None` RATHER THAN REFUSING, because
        # refreshing RECORDS what it saw and a status surface that recorded
        # would be a read that mutates.
        self.assertIsNone(unobserved.refresh_runtime({"attempt_id": "a"}))
        self.assertEqual(unobserved.observe({"attempt_id": "attempt:x"}),
                         {"claimed_by": None, "runtime": None,
                          "activity": None, "output": None,
                          "start_failure": None,
                          "preparation_failure": None, "exchange": None,
                          "integration": None})
        for call in (lambda: unobserved.receipt_of("offer.issue:x"),
                     lambda: unobserved.recover(now=NOW),
                     lambda: unobserved.admit({}, {}),
                     lambda: unobserved.claim({}),
                     lambda: unobserved.dispatch({}, {}),
                     lambda: unobserved.conclude({}, {})):
            with self.assertRaises(ContractRefusal) as caught:
                call()
            self.assertEqual(caught.exception.code, "capability")


class Binding(JobManagerCase):
    """What `check_binding` answers, act by act, at the seam itself.

    The reproduction that refused the first candidate lives in `test_restart`,
    against two real stores. These are the surrounding cases: an offer nobody
    has issued, a caller with no control store at all, and a journal row whose
    signature this build cannot read.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.stage = self.attempting(self.jobs)
        self.job = job_of(self.jobs, "job-a")
        self.control_store = self.control()
        self.acts = self.operations(control=self.control_store)

    def test_an_unissued_offer_is_absence_and_not_a_foreign_act(self):
        self.assertIsNone(check_binding(self.acts, self.stage, self.job))

    def test_a_caller_with_no_control_store_is_answered_without_a_read(self):
        # `Unobserved.receipt_of` refuses, so an implementation that asked
        # anyway would make a read-only status surface impossible to assemble.
        self.assertIsNone(check_binding(Unobserved(), self.stage, self.job))

    def test_the_committed_offers_own_intent_is_what_agrees(self):
        self.acts.admit(self.stage, self.job)
        record = check_binding(self.acts, self.stage, self.job)
        self.assertEqual(record["operation_id"],
                         canonical_operation("admit", self.stage["offer_id"]))
        # AND THE REAL SIGNATURE IS WHERE THE INTENT CAME FROM. If `issue_offer`
        # ever stopped signing one of these operands, this build would be
        # comparing against a member that is not there -- which is a refusal to
        # discover here rather than a proof that silently stops proving.
        signed = json.loads(record["signature"])["operands"]
        wanted = stage_intent(self.stage, self.job)
        for member in INTENT_OPERANDS:
            self.assertEqual(signed[member], wanted[member], member)

    def test_a_signature_this_build_cannot_read_is_refused_not_trusted(self):
        """Answering "it matches" for an unreadable row is the fail-open.

        The signature is durable text this process did not write, so a row that
        is not an operation signature at all cannot say whether the act was
        ours -- and a proof that passes when it cannot tell is not a proof.
        """
        self.acts.admit(self.stage, self.job)
        operation_id = canonical_operation("admit", self.stage["offer_id"])
        for spoiled in ("not json", "[]", "null", '{"operands": "text"}',
                        '{"kind": "offer.issue"}'):
            with self.subTest(signature=spoiled):
                self.control_store._connection.execute(
                    "UPDATE operations SET signature = ? "
                    "WHERE operation_id = ?", (spoiled, operation_id))
                with self.assertRaises(ContractRefusal) as caught:
                    check_binding(self.acts, self.stage, self.job)
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))


if __name__ == "__main__":
    unittest.main()


# -- W126558: the integration observation's binding and shape ----------------
#
# `work/records/2026/09/finding-v12-composed-ending-consumer/findings/
# finding-integration-stage-observation/OBSERVATION.md` revision 1.
#
# AN INTEGRATION ATTEMPT WRITES NO EXCHANGE AND FREEZES NO OUTPUT, so every
# member the canonical observation already carried is honestly absent for it.
# What is added is one optional member, and what is proved here is that a
# supplied document is bound to THIS stage's own claim before anything reads
# it.


class TheIntegrationObservationIsBoundBeforeItIsRead(unittest.TestCase):

    ASSIGNMENT = {"work_ref": {"authority_uuid": "0" * 32,
                               "work_id": "0000000a-W1"},
                  "participant": "baton.integrator", "generation": 5}
    # THE KIND IS AN OPERAND OF THIS BOUNDARY, named rather than omitted:
    # review 2026-09-09T09:13Z [1] found that the ids alone bind a document to
    # an ATTEMPT, and an implementation stage's attempt is just as bindable.
    STAGE = {"stage_id": "job-a/integration", "kind": "integration",
             "episode": 1, "attempt_id": "attempt-1", "offer_id": "offer-1"}

    def document(self, **changed):
        held = {"schema": delegation.INTEGRATION_OBSERVATION_SCHEMA,
                "stage_id": "job-a/integration", "episode": 1,
                "attempt_id": "attempt-1", "offer_id": "offer-1",
                "assignment": copy.deepcopy(self.ASSIGNMENT),
                "state": "pending", "completion": None}
        held.update(changed)
        return held

    def completion(self, **changed):
        held = {"proposal_id": "proposal-1",
                "integration_receipt_id": "receipt-1", "entry_id": "entry-1",
                "lease_id": "lease-1", "fence": 2,
                "handoff_operation_id": "pass:attempt-1",
                "to_route": "rview", "runtime_id": "runtime-1",
                "execution_runtime": "destroyed"}
        held.update(changed)
        return held

    def observed(self, integration, **changed):
        held = {"claimed_by": "offer-1",
                "runtime": {"attempt_id": "attempt-1",
                            "runtime_id": "runtime-1",
                            "execution_runtime": "running",
                            "assignment": copy.deepcopy(self.ASSIGNMENT)},
                "activity": None, "output": None, "start_failure": None,
                "preparation_failure": None, "exchange": None,
                "integration": integration}
        held.update(changed)
        return held

    def bound(self, integration=..., **changed):
        held = self.observed(self.document() if integration is ... else
                             integration, **changed)
        return delegation._bound(held, dict(self.STAGE))

    def refusing(self, **operands):
        with self.assertRaises(ContractRefusal) as caught:
            self.bound(**operands)
        return caught.exception

    # -- the compatible answer -----------------------------------------------

    def test_an_observation_without_the_member_is_accepted_unchanged(self):
        """THE COMPATIBILITY RULE. A deployment composed before this member
        existed is still complete, and its behaviour is exactly what it was."""
        held = dict(self.observed(None))
        del held["integration"]
        answered = delegation._bound(held, dict(self.STAGE))
        self.assertIsNone(answered["integration"])
        self.assertEqual(answered["exchange"], None)

    def test_none_is_nobody_looked_and_not_a_state(self):
        self.assertIsNone(self.bound(integration=None)["integration"])

    def test_an_unclaimed_attempt_answers_nothing_at_all(self):
        """`_bound` already refuses to project an unclaimed attempt's facts,
        and a supplied document does not change that."""
        answered = delegation._bound(
            self.observed(self.document(), claimed_by=None),
            dict(self.STAGE))
        self.assertIsNone(answered["integration"])
        self.assertIsNone(answered["runtime"])

    # -- bound to this stage's own claim --------------------------------------

    def test_the_document_is_bound_to_the_stage_and_its_claimed_offer(self):
        for member, value in (("stage_id", "job-b/integration"),
                              ("episode", 2), ("attempt_id", "attempt-2"),
                              ("offer_id", "offer-2")):
            with self.subTest(member=member):
                held = self.refusing(
                    integration=self.document(**{member: value}))
                self.assertEqual(held.category, "refused")
                self.assertEqual(held.code, "operation-collision")
                self.assertIn(member, held.message)

    def test_the_offer_is_compared_to_the_proved_claim_not_the_operand(self):
        """The claim is what binds an attempt to an offer, so a document
        naming the stage's offer while another holds the claim refuses."""
        with self.assertRaises(ContractRefusal) as caught:
            delegation._bound(self.observed(self.document(),
                                            claimed_by="offer-9"),
                              dict(self.STAGE))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_the_assignment_is_the_runtimes_own_fixed_one(self):
        other = copy.deepcopy(self.ASSIGNMENT)
        other["generation"] = 3
        held = self.refusing(integration=self.document(assignment=other))
        self.assertEqual(held.code, "operation-collision")
        self.assertIn("fixed assignment", held.message)

    def test_a_document_before_activation_fails_closed(self):
        runtime = {"attempt_id": "attempt-1", "runtime_id": None,
                   "execution_runtime": "not-started", "assignment": None}
        held = self.refusing(runtime=runtime)
        self.assertEqual(held.category, "refused")
        self.assertIn("before activation", held.message)

    def test_a_document_supplied_for_another_kind_refuses(self):
        """[1]. The ids and the assignment bind this document to an attempt,
        and every kind of stage has one -- so without this check the same
        completed account projected an implementation stage completed with no
        worker output at all."""
        for kind in ("implementation", "review", None):
            with self.subTest(kind=kind):
                stage = dict(self.STAGE, kind=kind)
                with self.assertRaises(ContractRefusal) as caught:
                    delegation._bound(self.observed(self.document()), stage)
                self.assertEqual(caught.exception.category, "refused")
                self.assertEqual(caught.exception.code, "operation-collision")
                self.assertIn("integration observation is evidence about an "
                              "integration stage", caught.exception.message)

    def test_an_integration_stage_still_accepts_its_own(self):
        self.assertEqual(self.bound()["integration"]["state"], "pending")

    # -- the closed shape -----------------------------------------------------

    def test_a_foreign_schema_refuses(self):
        held = self.refusing(integration=self.document(
            schema="baton.v12.integration-stage-observation/2"))
        self.assertEqual((held.category, held.code), ("integrity", "schema"))

    def test_an_unknown_state_refuses(self):
        held = self.refusing(integration=self.document(state="integrated"))
        self.assertEqual((held.category, held.code), ("integrity", "schema"))

    def test_a_missing_or_extra_member_refuses(self):
        dropped = self.document()
        del dropped["completion"]
        self.assertEqual(self.refusing(integration=dropped).code, "schema")
        self.assertEqual(
            self.refusing(integration=self.document(invented=1)).code,
            "schema")

    def test_a_boolean_episode_refuses(self):
        """`True == 1` and a first episode is 1."""
        held = self.refusing(integration=self.document(episode=True))
        self.assertEqual((held.category, held.code), ("integrity", "schema"))
        self.assertIn("whole number", held.message)

    def test_a_boolean_generation_refuses(self):
        assignment = copy.deepcopy(self.ASSIGNMENT)
        assignment["generation"] = True
        held = self.refusing(integration=self.document(assignment=assignment))
        self.assertEqual((held.category, held.code), ("integrity", "schema"))

    # -- the completion account ----------------------------------------------

    def test_a_completed_document_carries_its_whole_account(self):
        answered = self.bound(integration=self.document(
            state="completed", completion=self.completion()))
        self.assertEqual(answered["integration"]["completion"]["fence"], 2)

    def test_completion_without_an_account_refuses(self):
        held = self.refusing(integration=self.document(state="completed"))
        self.assertIn("names no account", held.message)

    def test_an_account_on_any_other_state_refuses(self):
        for state in ("unstarted", "pending", "answered", "held"):
            with self.subTest(state=state):
                held = self.refusing(integration=self.document(
                    state=state, completion=self.completion()))
                self.assertIn("only a completed integration", held.message)

    def test_an_incomplete_account_refuses(self):
        for member in delegation.INTEGRATION_COMPLETION_MEMBERS:
            with self.subTest(member=member):
                account = self.completion()
                del account[member]
                held = self.refusing(integration=self.document(
                    state="completed", completion=account))
                self.assertEqual(held.code, "schema")

    def test_a_boolean_fence_refuses(self):
        held = self.refusing(integration=self.document(
            state="completed", completion=self.completion(fence=True)))
        self.assertIn("whole number", held.message)

    def test_a_running_exclusion_account_refuses(self):
        """A completion whose runtime is still running is one nobody had
        excluded the worker from."""
        held = self.refusing(integration=self.document(
            state="completed",
            completion=self.completion(execution_runtime="running")))
        self.assertIn("proved exclusion", held.message)
