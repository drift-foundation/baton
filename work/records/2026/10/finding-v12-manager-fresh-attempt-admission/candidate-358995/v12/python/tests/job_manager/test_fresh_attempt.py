"""W358969 — the manager-owned fresh attempt, and what it refuses.

DESIGN REC-7. The pilot's `quickstart-c` died on an expired credential with
nothing spent, and trying again meant an agent authoring a script that
reserved identities, rewrote configuration and checked its own preconditions.
These cases drive the operation that replaces that script: one admission, one
reservation, one linkage back to the failure, and a refusal everywhere the
host, the Authority or the deployment cannot answer for what it is being
asked to repeat.

THE STORES ARE REAL. The Job store and the Worker Manager control store are
this build's own, on disk, and the attempts the exclusion rule judges are
recorded through `attempts.record_attempt` and moved through `observe` --
the same two calls a serving deployment uses. What is a stand-in is the
operations object, which is `test_status`'s own strict fake, and the three
owner ports, which are driven both as fakes (so a case can state one fact at
a time) and as the real adapters (so the fakes are not the only thing proved).
"""

import json
import unittest

from tools import stage_execution

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import fresh_attempt, submit
from baton_v12.job_manager.fresh_attempt import (admit, fresh_attempt_of,
                                                 successor_of, successors_of)
from baton_v12.worker_manager import attempts

if __package__:
    from .fixtures import (NOW, UUID, WORK_A, FakeOperations, JobManagerCase,
                           job, stage, submission)
else:
    from fixtures import (NOW, UUID, WORK_A, FakeOperations, JobManagerCase,
                          job, stage, submission)

from tests.tools.test_stage_execution import StageCase

PRIOR = "quickstart-c"
FRESH = "quickstart-c-retry-2"


class FakeExclusion:
    """The host's answer, one fact at a time, with every call recorded."""

    def __init__(self, answer=None):
        self.answer = answer
        self.asked = []

    def evidence_of(self, attempt_ids):
        self.asked.append(tuple(attempt_ids))
        if callable(self.answer):
            return self.answer(attempt_ids)
        if self.answer is None:
            return {one: None for one in attempt_ids}
        return {one: self.answer for one in attempt_ids}


def ceased(runtime="destroyed", cleanup="retained", token=None):
    return {"runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                        "execution_runtime": runtime, "cleanup": cleanup,
                        "assignment": None},
            "token": token}


class FakeAuthorization:
    """One Work, and a record of whether anything was created."""

    def __init__(self, status="open", known=True):
        self.status = status
        self.known = known
        self.created = []

    def work_of(self, work_id):
        if not self.known:
            return None
        return {"work_id": work_id, "status": self.status, "phase": "queued"}

    def create_work(self, work_id, *, operation_id):
        self.created.append((work_id, operation_id))
        self.known = True
        return {"work_id": work_id, "status": "open", "phase": "queued"}


class FakeBinding:
    """The deployment, with the additive bind recorded rather than performed."""

    def __init__(self, bound=(), serving=("implementation-pilot",),
                 work_id=WORK_A):
        self.bound = {one: {"job_id": one, "job_work_id": work_id}
                      for one in bound}
        self._serving = serving
        self._work_id = work_id
        self.added = []

    def binding_of(self, job_id):
        return self.bound.get(job_id)

    def bind(self, job_id, *, like, work_id):
        self.added.append((job_id, like, work_id))
        self.bound[job_id] = {"job_id": job_id, "job_work_id": work_id,
                              "source_worker_id": "implementation-pilot"}
        return self.bound[job_id]

    def serving(self, job_id, kind):
        return list(self._serving)


class FreshAttemptCase(JobManagerCase):
    """One failed two-stage Job, exactly the pilot's shape."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()
        self.exclusion = FakeExclusion()
        self.authorization = FakeAuthorization()
        self.binding = FakeBinding()

    def prior(self, job_id=PRIOR, failed=True, stages=None):
        document = submission(
            submission_id=f"sub-{job_id}",
            jobs=[job(job_id, stages=stages if stages is not None else [
                stage("implementation", WORK_A),
                stage("review", WORK_A,
                      depends_on=[{"job_id": job_id,
                                   "kind": "implementation"}])])])
        submit(self.jobs, document)
        if failed:
            # THE PILOT'S OWN SHAPE: the implementation ends `unable`, which
            # the projection reads as `exceptional`, and the review it gates
            # stays `blocked` because the gate can never open.
            self.acts.frozen(f"{job_id}/implementation", "unable")
        return document

    def admitted(self, **named):
        held = {"prior_job_id": PRIOR, "exclusion": self.exclusion,
                "authorization": self.authorization, "binding": self.binding}
        held.update(named)
        return admit(self.jobs, self.acts, **held)

    def refused(self, **named):
        with self.assertRaises(ContractRefusal) as caught:
            self.admitted(**named)
        return caught.exception


class TheAdmission(FreshAttemptCase):

    def test_the_fresh_job_carries_the_prior_specification_unchanged(self):
        """THE SELECTION IS THE OPERATOR'S, so nothing about it is recomposed."""
        self.prior()
        answer = self.admitted()
        self.assertEqual(answer["job_id"], FRESH)
        self.assertEqual(answer["prior_job_id"], PRIOR)
        was = json.loads(self.jobs._connection.execute(
            "SELECT document FROM submissions WHERE submission_id = ?",
            (f"sub-{PRIOR}",)).fetchone()[0])["jobs"][0]
        now = json.loads(self.jobs._connection.execute(
            "SELECT document FROM submissions WHERE submission_id = ?",
            (f"sub-{FRESH}",)).fetchone()[0])["jobs"][0]
        for member in ("input_digest", "policy_digest", "test_scope",
                       "terminal_policy"):
            self.assertEqual(now[member], was[member], member)
        self.assertEqual([one["kind"] for one in now["stages"]],
                         [one["kind"] for one in was["stages"]])
        self.assertEqual([one["profile_digest"] for one in now["stages"]],
                         [one["profile_digest"] for one in was["stages"]])

    def test_the_dependency_moves_onto_the_fresh_job(self):
        """A fresh attempt gated on the failure it replaces would never run."""
        self.prior()
        self.admitted()
        now = json.loads(self.jobs._connection.execute(
            "SELECT document FROM submissions WHERE submission_id = ?",
            (f"sub-{FRESH}",)).fetchone()[0])["jobs"][0]
        self.assertEqual(now["stages"][1]["depends_on"],
                         [{"job_id": FRESH, "kind": "implementation"}])

    def test_the_prior_job_its_stages_and_its_episodes_are_untouched(self):
        self.prior()
        before = self.rows()
        self.admitted()
        after = self.rows()
        for table, column in (("jobs", "job_id"), ("stages", "job_id"),
                              ("episodes", "stage_id")):
            self.assertEqual([one for one in after[table]
                              if one[column].split("/")[0] == PRIOR],
                             before[table], table)

    def test_the_answer_links_the_fresh_job_to_what_it_replaces(self):
        self.prior()
        answer = self.admitted()
        self.assertEqual(answer["prior_submission_id"], f"sub-{PRIOR}")
        self.assertEqual(answer["prior_states"],
                         {f"{PRIOR}/implementation": "exceptional",
                          f"{PRIOR}/review": "blocked"})
        self.assertEqual(len(answer["prior_attempt_ids"]), 2)
        self.assertEqual(sorted(answer["exclusion"]),
                         sorted(answer["prior_attempt_ids"]))
        self.assertEqual(answer["stages"],
                         [f"{FRESH}/implementation", f"{FRESH}/review"])

    def test_the_reservation_is_durable_and_says_what_it_reserved(self):
        self.prior()
        self.admitted()
        held = fresh_attempt_of(self.jobs, FRESH)
        self.assertEqual(held["prior_job_id"], PRIOR)
        self.assertEqual(held["state"], "admitted")
        self.assertEqual(held["work_id"], WORK_A)
        self.assertEqual(held["submission_id"], f"sub-{FRESH}")
        self.assertIsNotNone(held["admitted_at"])
        self.assertEqual(json.loads(held["request"])["prior_job_id"], PRIOR)

    def test_the_work_is_reused_rather_than_created(self):
        """REUSE IS WHAT MAKES THE INSTALLED WORKERS ABLE TO SERVE IT."""
        self.prior()
        answer = self.admitted()
        self.assertEqual(answer["work"], {"work_id": WORK_A,
                                          "disposition": "reused",
                                          "status": "open"})
        self.assertEqual(self.authorization.created, [])

    def test_a_work_that_does_not_exist_yet_is_created_replayably(self):
        self.prior()
        self.authorization = FakeAuthorization(known=False)
        answer = self.admitted(work_id="0000000a-W9")
        self.assertEqual(answer["work"]["disposition"], "created")
        self.assertEqual(self.authorization.created,
                         [("0000000a-W9",
                           f"fresh_attempt.admit:work:{FRESH}")])

    def test_the_binding_is_added_from_the_prior_job_s_own(self):
        self.prior()
        answer = self.admitted()
        self.assertEqual(self.binding.added, [(FRESH, PRIOR, WORK_A)])
        self.assertEqual(answer["binding"]["disposition"], "added")
        self.assertEqual(answer["binding"]["serving"],
                         {"implementation": ["implementation-pilot"],
                          "review": ["implementation-pilot"]})

    def test_a_binding_already_configured_is_used_rather_than_added(self):
        self.prior()
        self.binding = FakeBinding(bound=(FRESH,))
        answer = self.admitted()
        self.assertEqual(self.binding.added, [])
        self.assertEqual(answer["binding"]["disposition"],
                         "already configured")

    def rows(self):
        held = {}
        for table in ("jobs", "stages", "episodes"):
            held[table] = [dict(one) for one in self.jobs._connection.execute(
                f"SELECT * FROM {table}").fetchall()]
        return held


class ReplayAndUniqueness(FreshAttemptCase):
    """One identity, one admission, and the same answer every time."""

    def test_the_same_request_replays_its_recorded_answer(self):
        self.prior()
        first = self.admitted()
        asked = len(self.exclusion.asked)
        second = self.admitted()
        self.assertEqual(first, second)
        # AND NOTHING WAS RE-DECIDED. A completed admission that re-derived
        # its preconditions could start refusing later because the host moved
        # on, which is the stale-check defect this design removes.
        self.assertEqual(len(self.exclusion.asked), asked)
        self.assertEqual(len(submission_rows_of(self.jobs)), 2)

    def test_a_replay_survives_the_prior_job_becoming_unquiet_afterwards(self):
        self.prior()
        first = self.admitted()
        self.exclusion.answer = ceased(runtime="running")
        self.assertEqual(self.admitted(), first)

    def test_the_same_identity_with_different_operands_refuses(self):
        self.prior()
        self.admitted()
        refusal = self.refused(job_id=FRESH, submission_id="sub-other")
        self.assertEqual(refusal.code, "operation-collision")
        # AND THE FIRST ADMISSION IS UNTOUCHED, which is what makes the
        # collision a refusal rather than a takeover.
        self.assertEqual(fresh_attempt_of(self.jobs, FRESH)["submission_id"],
                         f"sub-{FRESH}")

    def test_a_second_fresh_attempt_at_one_failure_refuses_naming_the_first(self):
        """A FORK IS TWO JOBS ON ONE WORK, which is what this prevents."""
        self.prior()
        self.admitted()
        refusal = self.refused(job_id="quickstart-c-elsewhere")
        self.assertIn(FRESH, refusal.message)
        self.assertTrue(refusal.durable)
        self.assertIsNone(fresh_attempt_of(self.jobs,
                                           "quickstart-c-elsewhere"))

    def test_the_chain_continues_from_the_attempt_that_failed(self):
        self.prior()
        self.admitted()
        self.acts.frozen(f"{FRESH}/implementation", "unable")
        self.binding = FakeBinding(bound=(FRESH,))
        answer = admit(self.jobs, self.acts, prior_job_id=FRESH,
                       exclusion=self.exclusion,
                       authorization=self.authorization,
                       binding=self.binding)
        self.assertEqual(answer["job_id"], "quickstart-c-retry-3")
        self.assertEqual([one["job_id"] for one in
                          successors_of(self.jobs, FRESH)],
                         ["quickstart-c-retry-3"])

    def test_the_derived_identity_is_the_next_ordinal_and_nothing_else(self):
        self.assertEqual(successor_of("quickstart-c"), "quickstart-c-retry-2")
        self.assertEqual(successor_of("quickstart-c-retry-2"),
                         "quickstart-c-retry-3")
        # A SUFFIX THAT IS NOT AN ORDINAL IS PART OF THE NAME.
        self.assertEqual(successor_of("job-retry-x"), "job-retry-x-retry-2")
        self.assertEqual(successor_of("job-retry-07"),
                         "job-retry-07-retry-2")

    def test_a_reservation_whose_submission_was_lost_resumes(self):
        """THE CUT BETWEEN THE RESERVATION AND THE SUBMISSION, driven.

        The intent is written, the process dies before `submit` commits, and
        the operator runs the same command again. It must finish rather than
        refuse itself as a duplicate.
        """
        self.prior()
        self.binding = _BindOnce(self.binding)
        with self.assertRaises(_Interrupted):
            self.admitted()
        held = fresh_attempt_of(self.jobs, FRESH)
        self.assertEqual(held["state"], "intended")
        self.assertIsNone(held["admitted_at"])
        self.binding = self.binding.held
        answer = self.admitted()
        self.assertEqual(answer["job_id"], FRESH)
        self.assertEqual(fresh_attempt_of(self.jobs, FRESH)["state"],
                         "admitted")


class _Interrupted(Exception):
    pass


class _BindOnce:
    """A deployment owner that dies after it has bound, once."""

    def __init__(self, held):
        self.held = held

    def binding_of(self, job_id):
        return self.held.binding_of(job_id)

    def bind(self, job_id, *, like, work_id):
        self.held.bind(job_id, like=like, work_id=work_id)
        raise _Interrupted("the host went away after the binding was written")

    def serving(self, job_id, kind):
        return self.held.serving(job_id, kind)


def submission_rows_of(store):
    return store._connection.execute("SELECT * FROM submissions").fetchall()


class WhatItRefuses(FreshAttemptCase):

    def test_a_job_this_store_does_not_hold(self):
        self.prior()
        refusal = self.refused(prior_job_id="nothing-like-this")
        self.assertIn("no such Job", refusal.message)

    def test_a_job_nothing_has_happened_to_yet(self):
        """A QUEUED STAGE IS NOT A FAILED ONE, and it is not settled either."""
        self.prior(failed=False)
        refusal = self.refused()
        self.assertIn("has not settled", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))

    def test_a_job_that_completed(self):
        """SETTLED AND NOT FAILED: the one case the second rule exists for."""
        self.prior(failed=False)
        self.acts.frozen(f"{PRIOR}/implementation", "completed")
        self.acts.frozen(f"{PRIOR}/review", "completed")
        refusal = self.refused()
        self.assertIn("FAILED execution", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))

    def test_a_stage_that_is_still_running(self):
        self.prior()
        self.acts.observed(
            f"{PRIOR}/review", claimed_by=True,
            runtime={"attempt_id": "a", "runtime_id": "runtime-1",
                     "execution_runtime": "running", "cleanup": None,
                     "assignment": None})
        refusal = self.refused()
        self.assertIn("has not settled", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))

    def test_a_blocked_stage_whose_gate_could_still_open(self):
        """BLOCKED IS NOT OVER unless the gate can never open."""
        self.prior(failed=False)
        self.acts.frozen(f"{PRIOR}/implementation", "completed")
        self.acts.frozen(f"{PRIOR}/review", "unable")
        # Implementation completed and review failed: the Job HAS failed, and
        # nothing is blocked, so this admits -- the point of the case is the
        # opposite one below.
        self.assertEqual(self.admitted()["job_id"], FRESH)

    def test_a_host_that_cannot_account_for_an_attempt(self):
        """UNKNOWN IS NOT PERMISSION. REC-4, and the pilot helper's mistake."""
        self.prior()
        self.exclusion = FakeExclusion(answer=lambda ids: {})
        refusal = self.refused()
        self.assertIn("unknown is not permission", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))

    def test_a_runtime_that_has_not_ceased(self):
        self.prior()
        self.exclusion = FakeExclusion(answer=ceased(runtime="running"))
        refusal = self.refused()
        self.assertIn("cessation is", refusal.message)

    def test_an_uncertain_runtime_is_refused_exactly_like_a_live_one(self):
        self.prior()
        self.exclusion = FakeExclusion(answer=ceased(runtime="uncertain"))
        self.assertIn("cessation is", self.refused().message)

    def test_cleanup_this_host_still_owes(self):
        self.prior()
        self.exclusion = FakeExclusion(answer=ceased(cleanup="pending"))
        self.assertIn("still owes it", self.refused().message)

    def test_a_resource_the_prior_attempt_has_not_returned(self):
        self.prior()
        self.exclusion = FakeExclusion(
            answer=ceased(token={"returned": False}))
        self.assertIn("still holds its workspace resource",
                      self.refused().message)

    def test_a_returned_resource_is_accepted_and_recorded_as_evidence(self):
        self.prior()
        self.exclusion = FakeExclusion(answer=ceased(token={"returned": True}))
        answer = self.admitted()
        for held in answer["exclusion"].values():
            self.assertEqual(held["resource"], "returned")
            self.assertEqual(held["runtime"], "destroyed")

    def test_a_work_that_is_not_open(self):
        self.prior()
        self.authorization = FakeAuthorization(status="closed")
        self.assertIn("runs under an open authorization",
                      self.refused().message)

    def test_a_deployment_where_no_worker_can_serve_a_stage(self):
        """THE BINDING EXISTING PROVES NOTHING; the selector decides."""
        self.prior()
        self.binding = FakeBinding(serving=())
        refusal = self.refused()
        self.assertIn("no configured worker can serve", refusal.message)
        # The Job was never recorded: a fresh attempt nothing can select is
        # not admitted and then left queued forever.
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (FRESH,)).fetchone())

    def test_a_deployment_that_binds_the_fresh_job_to_another_work(self):
        self.prior()
        self.binding = FakeBinding(bound=(FRESH,), work_id="0000000a-W7")
        self.assertIn("a Job's Work is a fact about the Job",
                      self.refused().message)

    def test_an_absent_owner_port(self):
        self.prior()
        self.assertIn("this operation does not decide an owner's fact",
                      self.refused(exclusion=None).message)


class TheRealHostAdapter(FreshAttemptCase):
    """The exclusion rule against the Worker Manager's OWN records.

    The fakes above state one host fact at a time. This drives the adapter
    the CLI actually composes, over a real control store whose attempts were
    recorded and moved by the manager's own calls -- so the vocabulary the
    rule compares against is the one the host really writes.
    """

    def setUp(self):
        super().setUp()
        from tools.fresh_attempt_ports import HostExclusion

        self.control_store = self.control()
        self.exclusion = HostExclusion(self.control_store)

    def record(self, attempt_id):
        attempts.record_attempt(
            self.control_store, attempt_id=attempt_id,
            adapter_name="reference", adapter_digest="sha256:" + "c" * 64,
            profile_digest="sha256:" + "b" * 64)

    def attempt_ids(self):
        from baton_v12.job_manager.episodes import identities

        return [identities(UUID, f"{PRIOR}/{kind}", 1)[1]
                for kind in ("implementation", "review")]

    def test_an_attempt_this_host_never_recorded_is_an_answer(self):
        """A STAGE THAT FAILED BEFORE IT RAN, which is the common case."""
        self.prior()
        answer = self.admitted()
        for held in answer["exclusion"].values():
            self.assertEqual(held["basis"],
                             "no attempt was ever recorded on this host")

    def test_a_recorded_attempt_that_never_started_is_ceased(self):
        self.prior()
        for attempt_id in self.attempt_ids():
            self.record(attempt_id)
        refusal = self.refused()
        # `cleanup` defaults to `pending`: the host has recorded the attempt
        # and has not finished accounting for it, so this refuses -- which is
        # the fail-closed answer and not an accident of the fixture.
        self.assertIn("still owes it", refusal.message)

    def test_a_recorded_attempt_whose_cleanup_completed_is_admitted(self):
        self.prior()
        for attempt_id in self.attempt_ids():
            self.record(attempt_id)
            attempts.observe(self.control_store, attempt_id=attempt_id,
                             axis="cleanup", value="complete")
        answer = self.admitted()
        for held in answer["exclusion"].values():
            self.assertEqual(held["runtime"], "not-started")
            self.assertEqual(held["cleanup"], "complete")

    def test_a_live_runtime_in_the_real_store_refuses(self):
        self.prior()
        for attempt_id in self.attempt_ids():
            self.record(attempt_id)
            attempts.observe(self.control_store, attempt_id=attempt_id,
                             axis="cleanup", value="complete")
            attempts.observe(self.control_store, attempt_id=attempt_id,
                             axis="execution_runtime",
                             value="start-requested")
        self.assertIn("cessation is", self.refused().message)

    def test_the_rule_asks_the_host_again_after_the_reservation(self):
        """A CHECK BEFORE A RESERVATION IS A CHECK ABOUT THE PAST."""
        self.prior()
        self.exclusion = FakeExclusion()
        self.admitted()
        self.assertEqual(len(self.exclusion.asked), 2)


class TheDeploymentRule(StageCase):
    """`servable_workers`, the selector's own rule, asked of documents.

    The manager needs to know whether a configured worker could serve a fresh
    Job's stage BEFORE the Job exists. Until this Work the only way to ask was
    to construct a live `Deployment`, which needs a control store and an
    authority the question has nothing to do with -- so a helper copied the
    comparison instead, and copied it wrong.

    THE DOCUMENT IS `StageCase`'S, deliberately. A deployment document
    hand-rolled here would be this case asserting against its own idea of a
    valid one; the fixture that owns the launch contract owns this too.
    """

    def given(self, **members):
        return self.document(**members)

    def binding(self, given, *, work_id=None, source="implementation-worker"):
        # THE BINDING'S WORK IS THE ONE THE WORKERS CARRY. `StageCase`'s
        # document names its own `job_work_id` and its workers' manifests
        # name the fixture's; the rule under test compares the manifest
        # against the BINDING, so the binding is built from the manifest and
        # a case that wants disagreement says so by passing `work_id`.
        held = self.worker_deployment(given, "implementation")
        return {"job_id": PRIOR,
                "job_work_id": (held["input_manifest"]["work_ref"]["work_id"]
                                if work_id is None else work_id),
                "review_work_id": given["review_work_id"],
                "source_worker_id": source,
                "canonical_target_id": given["canonical_target_id"],
                "line_declared_base": given["line_declared_base"]}

    def staged(self, given, kind="implementation"):
        held = self.worker_deployment(given, kind)
        return {"stage_id": f"{PRIOR}/{kind}", "job_id": PRIOR, "kind": kind,
                "work_id": held["input_manifest"]["work_ref"]["work_id"],
                "profile_name": held["profile_name"],
                "profile_digest": held["profile_digest"]}

    def worker_deployment(self, given, role):
        for one in given["workers"]:
            if one["role"] == role:
                return one["deployment"]
        raise AssertionError(role)

    def job_of(self, given, role="implementation"):
        held = self.worker_deployment(given, role)
        return {"input_digest": stage_execution.job_input_identity(
                    held["input_manifest"], what="a configured worker's input"),
                "policy_digest": held["policy_digest"]}

    def test_a_worker_whose_operands_agree_can_serve(self):
        given = self.given()
        held = stage_execution.servable_workers(
            given, self.binding(given), self.staged(given),
            self.job_of(given))
        self.assertEqual([one["worker_id"] for one in held],
                         ["implementation-worker"])

    def test_a_worker_on_another_work_cannot(self):
        """THE FACT THAT DECIDED THE PILOT'S SHAPE, asserted directly."""
        given = self.given()
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.servable_workers(
                given, self.binding(given, work_id="another-work"),
                self.staged(given), self.job_of(given))
        self.assertIn("the Work", caught.exception.message)

    def test_an_implementation_lane_is_bound_to_the_job_s_own_producer(self):
        """AGREEING ON EVERY DIGEST IS NOT BEING THE NAMED PRODUCER."""
        given = self.given()
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.servable_workers(
                given, self.binding(given, source="somebody-else"),
                self.staged(given), self.job_of(given))
        self.assertIn("no worker this deployment configures",
                      caught.exception.message)

    def test_the_review_lane_is_not_narrowed_to_the_producer(self):
        given = self.given()
        held = stage_execution.servable_workers(
            given, self.binding(given), self.staged(given, "review"),
            self.job_of(given, "review"))
        self.assertEqual([one["worker_id"] for one in held],
                         ["review-worker"])

    def test_the_live_selector_and_the_document_rule_are_one_rule(self):
        """`_job_workers` IS this function plus the two live facts."""
        import inspect

        source = inspect.getsource(stage_execution._job_workers)
        self.assertIn("return binding, servable_workers(", source)


class TheCommandRequestsTheOperation(FreshAttemptCase):
    """REC-7: "The CLI requests the operation and reports its outcome."

    What is proved here is that the command holds no rule. It composes the
    three owner ports and hands them to the manager operation; it does not
    pre-check cessation, uniqueness, Work reuse or binding compatibility, and
    it does not reach into a store the operation did not ask for. A command
    that decided any of those would be the helper this Work replaces.
    """

    def test_the_verb_delegates_every_decision_to_the_manager(self):
        import io
        from unittest import mock

        from tools import job_manager as command

        self.prior()
        seen = {}

        def admitting(store, operations, **named):
            seen.update(named)
            seen["operations"] = operations
            return {"job_id": FRESH, "reported": True}

        stream = io.StringIO()
        with mock.patch.object(command, "admit_fresh_attempt", admitting), \
                mock.patch.object(command, "ControlStore") as control, \
                mock.patch("tools.fresh_attempt_ports.Authority") as opened:
            control.open_readonly.return_value.__enter__.return_value = \
                "the control store"
            opened.open.return_value = "the authority"
            command.main(["--store", self.job_path,
                          "--incarnation", "jobs-1",
                          "--authority-uuid", UUID,
                          "fresh-attempt", "--prior-job", PRIOR,
                          "--control", self.control_path,
                          "--authority", "/nowhere/authority.sqlite3",
                          "--instance", "/nowhere"],
                         clock=self.clock, stream=stream)

        self.assertEqual(json.loads(stream.getvalue()),
                         {"job_id": FRESH, "reported": True})
        self.assertEqual(seen["prior_job_id"], PRIOR)
        # THE DERIVED IDENTITIES ARE THE OPERATION'S, not the command's.
        self.assertIsNone(seen["job_id"])
        self.assertIsNone(seen["work_id"])
        self.assertIsNone(seen["submission_id"])
        for port in ("exclusion", "authorization", "binding"):
            self.assertIsNotNone(seen[port], port)
        # AND THE CONTROL STORE IS OPENED READ-ONLY, so an admission cannot
        # change the evidence it is judging.
        self.assertEqual(control.open_readonly.call_count, 1)
        self.assertEqual(control.open.call_count, 0)


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
