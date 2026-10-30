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
import os
import pathlib
import unittest
from contextlib import contextmanager

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
from tests.tools.test_bootstrap import ValidFixture

PRIOR = "quickstart-c"
FRESH = "quickstart-c-retry-2"
# THE STAND-INS ANSWER FOR AN INSTANCE TOO. Review R17: a port that names no
# deployment cannot be checked against the others, and a fixture is not
# excused the question -- it declares a synthetic instance exactly as a real
# port declares a real one.
# WHICH DISPOSABLE INSTANCE THE STAND-INS ANSWER FOR, set by each case to
# its own temporary root. Review R18 made the Job store part of an instance's
# identity, so a fixture declaring a fictional path would be declaring
# another deployment -- which is exactly what the rule refuses. A case sets
# this once and every port it builds inherits it.
CURRENT = {}

STAND_IN = {"root": "/disposable/instance",
            "job_store": "/disposable/instance/db/jobs.sqlite3",
            "control_store": "/disposable/instance/db/control.sqlite3",
            "authority_store": "/disposable/instance/db/authority.sqlite3",
            "authority_uuid": UUID}


class FakeExclusion:
    """The host's answer, one fact at a time, with every call recorded."""

    def __init__(self, answer=None, identity=None):
        self.answer = answer
        self.asked = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    def evidence_of(self, attempt_ids):
        self.asked.append(tuple(attempt_ids))
        if callable(self.answer):
            return self.answer(attempt_ids)
        if self.answer is None:
            held = {one: None for one in attempt_ids}
        else:
            held = {one: self.answer for one in attempt_ids}
        # EVERY ANSWER NAMES THE HOST IT CAME FROM, as the real adapter's
        # does, so an absence is attributable to a named store.
        held["host"] = "/disposable/control.sqlite3"
        return held


def ceased(runtime="destroyed", cleanup="retained", token=None):
    return {"runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                        "execution_runtime": runtime, "cleanup": cleanup,
                        "assignment": None},
            "token": token}


class FakeAuthorization:
    """One Work, and a record of whether anything was created."""

    def __init__(self, status="open", known=True, identity=None):
        self.status = status
        self.known = known
        self.created = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

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
                 work_id=WORK_A, identity=None):
        self.bound = {one: {"job_id": one, "job_work_id": work_id}
                      for one in bound}
        self._serving = serving
        self._work_id = work_id
        self.added = []
        self.asked = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    def binding_of(self, job_id):
        return self.bound.get(job_id)

    def bind(self, job_id, *, like, work_id):
        self.added.append((job_id, like, work_id))
        self.bound[job_id] = {"job_id": job_id, "job_work_id": work_id,
                              "source_worker_id": "implementation-pilot"}
        return self.bound[job_id]

    def serving(self, job_id, *, stage, job):
        # THE FAKE RECORDS WHAT IT WAS ASKED, because review R3 was about the
        # operands rather than the answer: a case asserts that the SUBMITTED
        # digests and the stage's OWN profile reached this port.
        self.asked.append((job_id, dict(stage), dict(job)))
        return list(self._serving)


class FakeOwnership:
    """The instance guard, recorded rather than taken."""

    def __init__(self, holder="control.sqlite3", refusal=None,
                 running=None, lock=None, overlap=None,
                 identity=None):
        import threading

        self.holder = holder
        self.refusal = refusal
        self.held_count = 0
        self.released = 0
        # SHARED BY EVERY PORT IN ONE CASE, so two racing admissions contend
        # the way two real ones do rather than each holding their own.
        self.running = set() if running is None else running
        self.lock = threading.Lock() if lock is None else lock
        # SET BY A CASE THAT NEEDS TWO ADMISSIONS GENUINELY OVERLAPPING.
        self.overlap = overlap
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity") or STAND_IN

    @contextmanager
    def held(self):
        if self.refusal is not None:
            raise self.refusal
        self.held_count += 1
        try:
            yield self
        finally:
            self.released += 1

    @contextmanager
    def invocation(self, job_id):
        """A real in-memory exclusion, so a case about racing is about one.

        THE WINNER WAITS INSIDE ITS CRITICAL SECTION until the other request
        has tried, when a case asks for that. Without it the race was
        decided by scheduling: if the first admission finished before the
        second reached this lock, the second found nothing in flight and
        both were admitted. The case then failed about once in four full
        runs -- which is a defect in the case, not in the product, and it
        shipped in the slice that introduced it. `overlap` makes the
        interleaving the case claims to exercise the one it gets.
        """
        with self.lock:
            if job_id in self.running:
                if self.overlap is not None:
                    self.overlap.set()
                raise ContractRefusal(
                    "refused", "precondition",
                    f"another admission of {job_id!r} is in flight")
            self.running.add(job_id)
        try:
            if self.overlap is not None:
                self.overlap.wait(timeout=20)
            yield
        finally:
            with self.lock:
                self.running.discard(job_id)


class FreshAttemptCase(JobManagerCase):
    """One failed two-stage Job, exactly the pilot's shape."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()
        # THE STAND-INS ANSWER FOR THIS CASE'S OWN DISPOSABLE INSTANCE.
        # Review R18 made the Job store part of the identity, so a fixture
        # that declared a fictional path would be declaring another
        # deployment -- which is exactly what the rule refuses.
        self.stand_in = dict(STAND_IN, root=self.root,
                             job_store=self.job_path,
                             control_store=self.control_path)
        held = CURRENT.get("identity")
        CURRENT["identity"] = self.stand_in
        self.addCleanup(CURRENT.__setitem__, "identity", held)
        self.exclusion = FakeExclusion()
        self.authorization = FakeAuthorization()
        self.binding = FakeBinding()
        self.ownership = FakeOwnership()

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
                "authorization": self.authorization, "binding": self.binding,
                "ownership": self.ownership}
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
                       binding=self.binding, ownership=self.ownership)
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

    def instance(self):
        return self.held.instance()

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
        self.exclusion = FakeExclusion(
            answer=lambda ids: {"host": "/disposable/control.sqlite3"})
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
        # THE REAL PORT, declaring the instance this case's control store is.
        # Review R17 made the identity required, and these cases supply one
        # naming their own disposable store rather than being exempted.
        self.exclusion = HostExclusion(self.control_store,
                                       identity=self.stand_in)

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
            self.assertIn("no attempt was ever recorded on this instance's "
                          "own host", held["basis"])
            self.assertIn(self.control_path, held["basis"])

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
        import shutil
        import tempfile
        from unittest import mock

        from tools import job_manager as command

        self.prior()
        seen = {}

        def admitting(store, operations, **named):
            seen.update(named)
            seen["operations"] = operations
            return {"job_id": FRESH, "reported": True}

        # A REAL INSTANCE DIRECTORY, because the command composes the
        # ownership port from this instance's own configuration and a
        # command that could skip that would not be composing it.
        instance = tempfile.mkdtemp(prefix="w358969-cli-")
        self.addCleanup(shutil.rmtree, instance, True)
        pathlib.Path(instance, "deployment.json").write_text(json.dumps(
            {"authority_uuid": UUID,
             "workers": [{"worker_id": "implementation-pilot",
                          "role": "implementation",
                          "deployment": {"workspace_storage":
                                         f"{instance}/state/workspaces"}}]}))
        # THE COMMAND HOLDS EVERY OPERAND TO THE INSTANCE'S OWN LAYOUT, so
        # a case that drives it names the stores this instance owns.
        places = pathlib.Path(instance, "db")
        places.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.job_path, places / "jobs.sqlite3")
        stream = io.StringIO()
        with mock.patch.object(command, "admit_fresh_attempt", admitting), \
                mock.patch.object(command, "ControlStore") as control, \
                mock.patch("tools.fresh_attempt_ports.Authority") as opened:
            # THE STAND-IN CONTROL HANDLE NAMES THE INSTANCE'S OWN STORE,
            # because the real host port proves the store it wraps at birth.
            control.open_readonly.return_value.__enter__.return_value = \
                mock.Mock(database=str(places / "control.sqlite3"))
            opened.open.return_value = mock.Mock(authority_uuid=UUID)
            command.main(["--store", str(places / "jobs.sqlite3"),
                          "--incarnation", "jobs-1",
                          "--authority-uuid", UUID,
                          "fresh-attempt", "--prior-job", PRIOR,
                          "--control", str(places / "control.sqlite3"),
                          "--authority", str(places / "authority.sqlite3"),
                          "--instance", instance],
                         clock=self.clock, stream=stream)

        self.assertEqual(json.loads(stream.getvalue()),
                         {"job_id": FRESH, "reported": True})
        self.assertEqual(seen["prior_job_id"], PRIOR)
        # THE DERIVED IDENTITIES ARE THE OPERATION'S, not the command's.
        self.assertIsNone(seen["job_id"])
        self.assertIsNone(seen["work_id"])
        self.assertIsNone(seen["submission_id"])
        for port in ("exclusion", "authorization", "binding",
                     "ownership"):
            self.assertIsNotNone(seen[port], port)
        # AND THE CONTROL STORE IS OPENED READ-ONLY, so an admission cannot
        # change the evidence it is judging.
        self.assertEqual(control.open_readonly.call_count, 1)
        self.assertEqual(control.open.call_count, 0)


class TheRealBindingAdapter(ValidFixture):
    """The deployment owner, driven against a REAL disposable instance.

    Review R1: the first cut of this adapter wrote `job_work_id` into a
    bootstrap Job input -- the EMITTED binding's spelling -- and the real
    `prepare` refused every call with "nothing reads jobs[1].job_work_id".
    Nothing in the candidate ran it, so a production adapter that could not
    perform its advertised retry shipped as proved. These cases run it.
    """

    def installed(self, **members):
        import io

        from tools import bootstrap

        document = self.document(**members)
        bootstrap.prepare(document, stream=io.StringIO())
        self.publish(document)
        return document

    def publish(self, document):
        pathlib.Path(self.state, "install-inputs.json").write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n")

    def port(self):
        import io

        from tools.fresh_attempt_ports import DeploymentBinding

        return DeploymentBinding(self.state, stream=io.StringIO())

    def configured(self):
        from tools import bootstrap

        return json.loads(pathlib.Path(
            bootstrap.layout(self.state)["configuration"]).read_text())

    def test_the_additive_bind_is_performed_by_the_real_operation(self):
        self.installed()
        port = self.port()
        held = port.bind("job-a-retry-2", like="job-a", work_id=self.work)
        self.assertEqual(held["job_id"], "job-a-retry-2")
        self.assertEqual(held["job_work_id"], self.work)
        # AND THE PRIOR BINDING IS STILL THERE, unchanged.
        bound = {one["job_id"]: one
                 for one in self.configured()["job_bindings"]}
        self.assertEqual(sorted(bound), ["job-a", "job-a-retry-2"])
        self.assertEqual(bound["job-a-retry-2"]["source_worker_id"],
                         bound["job-a"]["source_worker_id"])
        self.assertEqual(bound["job-a-retry-2"]["line_declared_base"],
                         bound["job-a"]["line_declared_base"])

    def test_both_stages_of_the_fresh_job_can_be_served(self):
        """THE SELECTOR'S ANSWER, over the real emitted configuration."""
        self.installed()
        port = self.port()
        port.bind("job-a-retry-2", like="job-a", work_id=self.work)
        configured = self.configured()
        for role in ("implementation", "review"):
            deployment = [one["deployment"] for one in configured["workers"]
                          if one["role"] == role][0]
            stage = {"kind": role, "work_id": self.work,
                     "profile_name": deployment["profile_name"],
                     "profile_digest": deployment["profile_digest"]}
            job = {"input_digest": stage_execution.job_input_identity(
                       deployment["input_manifest"],
                       what="a configured worker's input"),
                   "policy_digest": deployment["policy_digest"]}
            self.assertTrue(port.serving("job-a-retry-2", stage=stage,
                                         job=job), role)

    def test_a_second_bind_of_one_identity_adds_nothing(self):
        """IDEMPOTENT, which is what makes an interrupted run safe to repeat."""
        self.installed()
        port = self.port()
        port.bind("job-a-retry-2", like="job-a", work_id=self.work)
        before = self.configured()
        again = self.port()
        self.assertIsNotNone(again.binding_of("job-a-retry-2"))
        again.bind("job-a-retry-2", like="job-a", work_id=self.work)
        self.assertEqual(self.configured(), before)
        self.assertEqual(len(self.configured()["job_bindings"]), 2)

    def test_the_input_document_and_the_configuration_stay_in_step(self):
        """SO THE NEXT RETRY CAN BE PREPARED AT ALL."""
        self.installed()
        self.port().bind("job-a-retry-2", like="job-a", work_id=self.work)
        held = json.loads(pathlib.Path(self.state,
                                       "install-inputs.json").read_text())
        self.assertEqual([one["job_id"] for one in held["jobs"]],
                         ["job-a", "job-a-retry-2"])
        # AND A SECOND RETRY IN THE CHAIN PREPARES, which is the thing a
        # stale input file would have made impossible.
        self.port().bind("job-a-retry-3", like="job-a-retry-2",
                         work_id=self.work)
        self.assertEqual(
            sorted(one["job_id"]
                   for one in self.configured()["job_bindings"]),
            ["job-a", "job-a-retry-2", "job-a-retry-3"])

    def test_an_interrupted_publication_is_resumed_rather_than_doubled(self):
        """THE CUT review R4 NAMED: input written, configuration not yet.

        The input document is written first on purpose -- an input missing a
        Job the configuration binds is the direction `conflicts` refuses, and
        it would make every later retry impossible. Resuming prepares the
        document that is already there instead of appending a second entry.
        """
        document = self.installed()
        interrupted = dict(document, jobs=list(document["jobs"]) + [
            dict(document["jobs"][0], job_id="job-a-retry-2",
                 work_id=self.work)])
        self.publish(interrupted)
        self.assertIsNone(self.port().binding_of("job-a-retry-2"))
        self.port().bind("job-a-retry-2", like="job-a", work_id=self.work)
        self.assertEqual([one["job_id"]
                          for one in self.configured()["job_bindings"]],
                         ["job-a", "job-a-retry-2"])
        held = json.loads(pathlib.Path(self.state,
                                       "install-inputs.json").read_text())
        self.assertEqual(len(held["jobs"]), 2)

    def test_an_install_document_behind_the_configuration_refuses(self):
        """AN INITIAL INSTALL INPUT IS NOT THE CURRENT CONFIGURATION."""
        from tools.fresh_attempt_ports import BindingRefusal

        document = self.installed(**self.several())
        self.publish(dict(document, jobs=[document["jobs"][0]]))
        with self.assertRaises(BindingRefusal) as caught:
            self.port().bind("job-a-retry-2", like="job-a",
                             work_id=self.work)
        self.assertIn("job-b", str(caught.exception))
        self.assertIn("would drop a configured Job", str(caught.exception))
        self.assertEqual(
            sorted(one["job_id"]
                   for one in self.configured()["job_bindings"]),
            ["job-a", "job-b"])

    def test_two_concurrent_binds_do_not_overwrite_one_another(self):
        """THE REAL PUBLICATION ADAPTER, under two writers. Review R5.

        Two UNRELATED fresh attempts in one instance: an unguarded
        read/modify/prepare would have each compose its document before the
        other's Job existed, and the second rename would drop the first. Both
        land, and the configuration names all three.
        """
        import concurrent.futures

        self.installed()

        def binding(job_id):
            try:
                self.port().bind(job_id, like="job-a", work_id=self.work)
                return ("bound", job_id)
            except Exception as failure:                     # noqa: BLE001
                return ("refused", f"{type(failure).__name__}: {failure}")

        with concurrent.futures.ThreadPoolExecutor(2) as running:
            outcomes = list(running.map(binding,
                                        ["job-a-retry-2", "job-b-retry-2"]))
        self.assertEqual([one[0] for one in outcomes], ["bound", "bound"],
                         outcomes)
        self.assertEqual(
            sorted(one["job_id"]
                   for one in self.configured()["job_bindings"]),
            ["job-a", "job-a-retry-2", "job-b-retry-2"])
        held = json.loads(pathlib.Path(self.state,
                                       "install-inputs.json").read_text())
        self.assertEqual(sorted(one["job_id"] for one in held["jobs"]),
                         ["job-a", "job-a-retry-2", "job-b-retry-2"])
        # AND NO TEMPORARY FILE WAS LEFT BEHIND by either writer.
        self.assertEqual(sorted(one.name for one in
                                pathlib.Path(self.state).glob("*.tmp")), [])

    def test_a_prior_job_the_install_document_does_not_name_refuses(self):
        from tools.fresh_attempt_ports import BindingRefusal

        self.installed()
        with self.assertRaises(BindingRefusal) as caught:
            self.port().bind("ghost-retry-2", like="ghost",
                             work_id=self.work)
        self.assertIn("names no Job 'ghost'", str(caught.exception))


class TheConnectedRetry(ValidFixture):
    """One fresh attempt, end to end, through the REAL adapters.

    The Authority is the instance's own, created by the real `bootstrap`; the
    deployment binding is the real adapter over the real emitted
    configuration; the Job store and the control store are real and
    disposable. What is still a stand-in is the operations object, which is
    the manager's own strict fake, and the engine and provider, which are
    never reached -- no runtime is started and no credential is read.
    """

    def setUp(self):
        import io

        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tools import bootstrap
        from tools.fresh_attempt_ports import (DeploymentBinding,
                                               HostExclusion,
                                               InstanceOwnership,
                                               WorkAuthorization)

        super().setUp()
        self.document = self.document()
        bootstrap.prepare(self.document, stream=io.StringIO())
        pathlib.Path(self.state, "install-inputs.json").write_text(
            json.dumps(self.document, indent=2, sort_keys=True) + "\n")
        self.places = bootstrap.layout(self.state)
        self.uuid = self.config["authority_uuid"]
        self.instants = [NOW]
        self.jobs = JobStore.open(self.places["job_store"],
                                  authority_uuid=self.uuid,
                                  incarnation="jobs-1", clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.control_store = ControlStore.open(self.places["control_store"],
                                               incarnation="manager-1",
                                               clock=self.clock)
        self.addCleanup(self.control_store.close)
        self.acts = FakeOperations(authority_uuid=self.uuid)
        # EVERY PORT IS BOUND TO THIS INSTANCE'S OWN IDENTITY, which is how
        # the command composes them: the facts come from the instance's
        # layout and configuration rather than from the operands.
        from tools.fresh_attempt_ports import instance_identity

        self.bound = instance_identity(self.state)
        self.exclusion = HostExclusion(self.control_store,
                                       identity=self.bound)
        self.authorization = WorkAuthorization.opened(
            self.places["authority_store"], authority_uuid=self.uuid,
            route="baton.impl", identity=self.bound)
        self.binding = DeploymentBinding(self.state, stream=io.StringIO(),
                                         identity=self.bound)
        # THE REAL INSTANCE GUARD, over this instance's own configuration.
        self.ownership = InstanceOwnership.of(
            self.control_store,
            json.loads(pathlib.Path(
                self.places["configuration"]).read_text()),
            identity=self.bound)

    def clock(self):
        return self.instants[-1]

    def failed(self, job_id="job-a"):
        """One submitted Job on this instance's own Work, failed."""
        configured = self.configured_workers()
        document = {
            "schema": "baton.v12.job-submission/2",
            "submission_id": f"sub-{job_id}",
            "jobs": [{"job_id": job_id,
                      "input_digest": configured["input_digest"],
                      "policy_digest": configured["policy_digest"],
                      "test_scope": ["v12/python/tests/job_manager"],
                      "terminal_policy": "report-and-hold",
                      "execution_limits": {"provider_turn_seconds": 3600,
                                           "verification_command_seconds":
                                               900},
                      "stages": [
                          {"kind": "implementation", "work_id": self.work,
                           "profile_name":
                               configured["implementation"]["profile_name"],
                           "profile_digest":
                               configured["implementation"]["profile_digest"],
                           "depends_on": []},
                          {"kind": "review", "work_id": self.work,
                           "profile_name":
                               configured["review"]["profile_name"],
                           "profile_digest":
                               configured["review"]["profile_digest"],
                           "depends_on": [{"job_id": job_id,
                                           "kind": "implementation"}]}]}]}
        submit(self.jobs, document)
        self.acts.frozen(f"{job_id}/implementation", "unable")
        return document

    def configured_workers(self):
        held = json.loads(pathlib.Path(
            self.places["configuration"]).read_text())
        by_role = {one["role"]: one["deployment"] for one in held["workers"]}
        return {"implementation": by_role["implementation"],
                "review": by_role["review"],
                "input_digest": stage_execution.job_input_identity(
                    by_role["implementation"]["input_manifest"],
                    what="a configured worker's input"),
                "policy_digest": by_role["implementation"]["policy_digest"]}

    def admit(self, store=None, **named):
        held = {"prior_job_id": "job-a", "exclusion": self.exclusion,
                "authorization": self.authorization,
                "binding": self.binding, "ownership": self.ownership}
        held.update(named)
        return admit(self.jobs if store is None else store, self.acts, **held)

    def test_a_fresh_attempt_is_admitted_bound_and_selectable(self):
        """THE WHOLE OUTCOME, with nothing between the parts faked."""
        self.failed()
        answer = self.admit()
        self.assertEqual(answer["job_id"], "job-a-retry-2")
        # The Work is the instance's own and it was REUSED, not created.
        self.assertEqual(answer["work"], {"work_id": self.work,
                                          "disposition": "reused",
                                          "status": "open"})
        self.assertEqual(answer["binding"]["disposition"], "added")
        self.assertEqual(sorted(answer["binding"]["serving"]),
                         ["implementation", "review"])
        # BOTH STAGES, each selected under its OWN role's profile.
        for role, workers in answer["binding"]["serving"].items():
            self.assertTrue(workers, role)
        self.assertEqual(answer["stages"],
                         ["job-a-retry-2/implementation",
                          "job-a-retry-2/review"])
        # The limits the operator selected travelled verbatim.
        now = json.loads(self.jobs._connection.execute(
            "SELECT document FROM submissions WHERE submission_id = ?",
            ("sub-job-a-retry-2",)).fetchone()[0])["jobs"][0]
        self.assertEqual(now["execution_limits"],
                         {"provider_turn_seconds": 3600,
                          "verification_command_seconds": 900})
        # And the failed Job is still bound and still recorded.
        bound = [one["job_id"] for one in json.loads(pathlib.Path(
            self.places["configuration"]).read_text())["job_bindings"]]
        self.assertEqual(sorted(bound), ["job-a", "job-a-retry-2"])

    def test_the_whole_thing_replays(self):
        self.failed()
        first = self.admit()
        self.assertEqual(self.admit(), first)
        bound = [one["job_id"] for one in json.loads(pathlib.Path(
            self.places["configuration"]).read_text())["job_bindings"]]
        self.assertEqual(sorted(bound), ["job-a", "job-a-retry-2"])

    def test_a_mismatched_submitted_input_refuses_before_admission(self):
        """R3's case: the specification, not a worker compared with itself."""
        self.failed()
        wrong = dict(self.jobs._connection.execute(
            "SELECT * FROM jobs WHERE job_id = 'job-a'").fetchone())
        del wrong
        self.jobs._connection.execute(
            "UPDATE jobs SET input_digest = ? WHERE job_id = 'job-a'",
            ("sha256:" + "f" * 64,))
        self.jobs._connection.execute(
            "UPDATE submissions SET document = replace(document, ?, ?)",
            (self.configured_workers()["input_digest"],
             "sha256:" + "f" * 64))
        with self.assertRaises(ContractRefusal) as caught:
            self.admit()
        self.assertIn("under its own submitted input", caught.exception.message)
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'job-a-retry-2'"
        ).fetchone())

    def test_a_selected_fresh_work_is_created_and_then_cannot_be_served(self):
        """WHY REUSING THE PRIOR WORK IS THE DEFAULT, measured.

        A fresh attempt may select another Work and the real Authority mints
        it -- and the configured workers' manifests name the INSTANCE's Work,
        so `_disagreements` excludes every one of them and nothing can serve
        the stage. That is the fact that decides the whole shape: a fresh
        Work means new workers, which is per-retry configuration REC-7 says
        is not required.

        AND THE REFUSAL IS HONEST ABOUT WHAT IS LEFT. The reservation exists
        and the Work was minted; the operation is incomplete rather than
        undone, and it says so rather than claiming it changed nothing.
        """
        from baton_v12.authority import Authority

        self.failed()
        fresh = f"{self.uuid[:8]}-W9"
        with self.assertRaises(ContractRefusal) as caught:
            self.admit(work_id=fresh)
        self.assertIn("no configured worker can serve",
                      caught.exception.message)
        self.assertIn("is already RESERVED in this store",
                      caught.exception.message)
        self.assertIn("run the same request again", caught.exception.message)
        with Authority.open_readonly(self.places["authority_store"],
                                     expected_authority_uuid=self.uuid) as held:
            self.assertEqual(held.project_work(fresh)["status"], "open")
        held = fresh_attempt_of(self.jobs, "job-a-retry-2")
        self.assertEqual(held["state"], "intended")
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'job-a-retry-2'"
        ).fetchone())

    def test_two_real_connections_cannot_fork_one_failure(self):
        """REVIEW R2's OWN PROBE, as a case.

        Two Job store connections, two different explicitly supported fresh
        identities, synchronized past the point where the first cut read the
        successor set. Exactly one is admitted and the store records exactly
        one successor.
        """
        import concurrent.futures
        import threading

        from baton_v12.job_manager import JobStore

        self.failed()
        gate = threading.Barrier(2, timeout=20)

        class Synchronized(FakeExclusion):
            def evidence_of(self, attempt_ids):
                answer = super().evidence_of(attempt_ids)
                if len(self.asked) == 1:
                    gate.wait()
                return answer

        def racing(job_id):
            import io

            from tools.fresh_attempt_ports import (DeploymentBinding,
                                                   WorkAuthorization)

            # EACH THREAD OPENS ITS OWN HANDLES, because a SQLite connection
            # belongs to the thread that made it -- and because two competing
            # requests in production ARE two processes with their own.
            with JobStore.open(self.places["job_store"],
                               authority_uuid=self.uuid,
                               incarnation=job_id,
                               clock=self.clock) as store:
                try:
                    return ("admitted", self.admit(
                        job_id=job_id, store=store,
                        exclusion=Synchronized(identity=self.bound),
                        authorization=WorkAuthorization.opened(
                            self.places["authority_store"],
                            authority_uuid=self.uuid, route="baton.impl",
                            identity=self.bound),
                        binding=DeploymentBinding(
                            self.state, stream=io.StringIO(),
                            identity=self.bound))["job_id"])
                except ContractRefusal as refusal:
                    gate.abort()
                    return ("refused", refusal.message)

        with concurrent.futures.ThreadPoolExecutor(2) as running:
            outcomes = list(running.map(racing,
                                        ["retry-left", "retry-right"]))
        admitted = [one for one in outcomes if one[0] == "admitted"]
        self.assertEqual(len(admitted), 1, outcomes)
        self.assertEqual([one["job_id"] for one in
                          successors_of(self.jobs, "job-a")],
                         [admitted[0][1]])
        self.assertEqual(
            sorted(one[0] for one in self.jobs._connection.execute(
                "SELECT job_id FROM jobs").fetchall()),
            sorted(["job-a", admitted[0][1]]))

    def test_a_changed_request_refuses_before_any_other_owner_is_touched(self):
        """REVIEW R4: no Work is minted for an operation nobody admitted."""
        self.failed()
        self.admit()
        before = json.loads(pathlib.Path(
            self.places["configuration"]).read_text())
        with self.assertRaises(ContractRefusal) as caught:
            self.admit(job_id="job-a-retry-2",
                       work_id=f"{self.uuid[:8]}-W77")
        self.assertEqual(caught.exception.code, "operation-collision")
        # THE AUTHORITY WAS NOT TOUCHED: the rejected Work does not exist.
        self.assertIsNone(
            self.authorization.work_of(f"{self.uuid[:8]}-W77"))
        # Nor was the deployment.
        self.assertEqual(json.loads(pathlib.Path(
            self.places["configuration"]).read_text()), before)


class OwnershipAcrossTheEffects(FreshAttemptCase):
    """R5 and R6, at the manager boundary.

    The reservation says an identity is spoken for. These say who may ACT on
    it, and that nobody else may take the name while they are acting.
    """

    def test_identical_concurrent_requests_bind_once(self):
        """R5's OWN PROBE: two real connections, one identical request."""
        import concurrent.futures
        import threading

        from baton_v12.job_manager import JobStore

        self.prior()
        gate = threading.Barrier(2, timeout=20)
        # ONE RECORDING PORT SHARED BY BOTH, so the count is of effects on
        # one deployment rather than of calls to two stand-ins.
        shared = FakeBinding()

        class Synchronized(FakeExclusion):
            """Hold both requests together until both have read the host.

            The synchronization is BEFORE the reservation, which is where
            review R5's probe put it: what is under test is two admissions
            genuinely in flight at once, not two run back to back.
            """

            def evidence_of(self, attempt_ids):
                answer = super().evidence_of(attempt_ids)
                if len(self.asked) == 1:
                    gate.wait()
                return answer

        def racing(incarnation):
            with JobStore.open(self.job_path, authority_uuid=UUID,
                               incarnation=incarnation,
                               clock=self.clock) as store:
                try:
                    return ("admitted", admit(
                        store, self.acts, prior_job_id=PRIOR,
                        exclusion=Synchronized(),
                        authorization=self.authorization,
                        binding=shared,
                        ownership=FakeOwnership())["job_id"])
                except ContractRefusal as refusal:
                    gate.abort()
                    return ("refused", refusal.message)

        with concurrent.futures.ThreadPoolExecutor(2) as running:
            outcomes = list(running.map(racing, ["jobs-left", "jobs-right"]))
        self.assertEqual(len([one for one in outcomes
                              if one[0] == "admitted"]), 1, outcomes)
        # THE EXTERNAL EFFECT HAPPENED ONCE, which is the whole finding.
        self.assertEqual(len(shared.added), 1, shared.added)
        refused = [one for one in outcomes if one[0] == "refused"][0][1]
        self.assertIn("is held by", refused)

    def test_a_holder_continues_its_own_interrupted_work(self):
        self.prior()
        self.binding = _BindOnce(self.binding)
        with self.assertRaises(_Interrupted):
            self.admitted()
        held = fresh_attempt_of(self.jobs, FRESH)
        self.assertEqual(held["state"], "intended")
        self.assertEqual(held["holder"], "jobs-1@control.sqlite3")
        self.binding = self.binding.held
        self.assertEqual(self.admitted()["job_id"], FRESH)

    def test_another_manager_is_refused_rather_than_taking_over(self):
        """DECIDING AN UNSEEN MANAGER HAS STOPPED IS THE ONE THING REFUSED."""
        from baton_v12.job_manager import JobStore

        self.prior()
        self.binding = _BindOnce(self.binding)
        with self.assertRaises(_Interrupted):
            self.admitted()
        with JobStore.open(self.job_path, authority_uuid=UUID,
                           incarnation="somebody-else",
                           clock=self.clock) as other:
            with self.assertRaises(ContractRefusal) as caught:
                admit(other, self.acts, prior_job_id=PRIOR,
                      exclusion=self.exclusion,
                      authorization=self.authorization,
                      binding=self.binding.held,
                      ownership=self.ownership)
        self.assertIn("jobs-1@control.sqlite3", caught.exception.message)
        self.assertIn("re-run under the same manager incarnation",
                      caught.exception.message)

    def test_an_ordinary_submission_cannot_take_a_reserved_identity(self):
        """R6: one identity, one owner, decided in this store's own lock."""
        self.prior()
        self.binding = _BindOnce(self.binding)
        with self.assertRaises(_Interrupted):
            self.admitted()
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, submission(submission_id="sub-sneaky",
                                         jobs=[job(FRESH)]))
        self.assertIn("RESERVED by a fresh attempt", caught.exception.message)
        # ORDINARY RATHER THAN DURABLE: see the sibling case about why
        # sealing this under the reservation holder's own operation identity
        # would poison the submission it exists to admit.
        self.assertFalse(caught.exception.durable)
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (FRESH,)).fetchone())
        # AND THE RETRY STILL FINISHES, which is the point of refusing.
        self.binding = self.binding.held
        self.assertEqual(self.admitted()["job_id"], FRESH)

    def test_an_ordinary_job_that_came_first_refuses_the_retry(self):
        """THE OTHER ORDER, decided in the same place."""
        self.prior()
        submit(self.jobs, submission(submission_id="sub-first",
                                     jobs=[job(FRESH)]))
        refusal = self.refused()
        self.assertIn("already recorded in this store by an ordinary "
                      "submission", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])

    def test_the_instance_is_held_for_the_whole_admission_and_released(self):
        self.prior()
        self.admitted()
        self.assertEqual(self.ownership.held_count, 1)
        self.assertEqual(self.ownership.released, 1)

    def test_a_serving_manager_refuses_the_admission_outright(self):
        self.prior()
        self.ownership = FakeOwnership(
            refusal=ContractRefusal("policy", "denied",
                                    "another manager is already active"))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitted()
        self.assertIn("another manager is already active",
                      caught.exception.message)
        # NOTHING WAS RESERVED AND NOTHING WAS PUBLISHED.
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])


class TheRealInstanceGuard(ValidFixture):
    """R7, against `workspaces.hold_manager_instance` itself."""

    def setUp(self):
        import io

        from baton_v12.worker_manager import ControlStore
        from tools import bootstrap

        super().setUp()
        document = self.document()
        bootstrap.prepare(document, stream=io.StringIO())
        self.places = bootstrap.layout(self.state)
        self.configuration = json.loads(
            pathlib.Path(self.places["configuration"]).read_text())
        self.instants = [NOW]
        self.control_store = ControlStore.open(self.places["control_store"],
                                               incarnation="manager-1",
                                               clock=self.clock)
        self.addCleanup(self.control_store.close)

    def clock(self):
        return self.instants[-1]

    def test_the_guard_is_taken_from_the_instance_s_own_configuration(self):
        from tools.fresh_attempt_ports import InstanceOwnership

        owning = InstanceOwnership.of(self.control_store, self.configuration)
        with owning.held() as guard:
            self.assertEqual(
                guard.place,
                os.path.realpath([one["deployment"]["workspace_storage"]
                                  for one in self.configuration["workers"]
                                  ][0]))
            self.assertEqual(guard.holder, self.places["control_store"])

    def test_a_manager_already_holding_this_instance_refuses(self):
        """THE EXCLUSION, driven: a second holder is denied, not queued."""
        from baton_v12.contracts import ContractRefusal as Refusal
        from baton_v12.worker_manager import workspaces
        from tools.fresh_attempt_ports import InstanceOwnership

        place = [one["deployment"]["workspace_storage"]
                 for one in self.configuration["workers"]][0]
        serving = workspaces.hold_manager_instance(self.control_store, place)
        self.addCleanup(serving.release)
        # A SECOND PROCESS IS WHAT THIS EXCLUDES, so the probe forks: the
        # in-process cache answers the guard this process already holds,
        # which is correct and is not the question.
        answer = self.forked(place)
        self.assertEqual(answer["outcome"], "refused")
        self.assertIn("another manager is already active", answer["message"])

    def forked(self, place):
        import multiprocessing

        with multiprocessing.get_context("spawn").Pool(1) as pool:
            return pool.apply(_guarding,
                              (self.places["control_store"], place))

    def test_a_borrowed_guard_outlives_the_admission_that_borrowed_it(self):
        """REVIEW R10: admission may not release another owner's lifetime.

        The serving composition holds the instance. An admission in the same
        process is handed that very descriptor by `hold_manager_instance`'s
        documented cache -- so releasing it would drop an exclusion its owner
        still believes it holds, which a spawned process could then take.
        """
        from baton_v12.worker_manager import workspaces
        from tools.fresh_attempt_ports import InstanceOwnership

        place = [one["deployment"]["workspace_storage"]
                 for one in self.configuration["workers"]][0]
        serving = workspaces.hold_manager_instance(self.control_store, place)
        self.addCleanup(serving.release)
        self.assertEqual(self.forked(place)["outcome"], "refused")

        owning = InstanceOwnership.of(self.control_store, self.configuration)
        with owning.held() as borrowed:
            self.assertIs(borrowed, serving)
        # STILL EXCLUDED, which is the whole finding.
        self.assertEqual(self.forked(place)["outcome"], "refused")

    def test_a_borrowed_guard_survives_an_admission_that_fails(self):
        from baton_v12.worker_manager import workspaces
        from tools.fresh_attempt_ports import InstanceOwnership

        place = [one["deployment"]["workspace_storage"]
                 for one in self.configuration["workers"]][0]
        serving = workspaces.hold_manager_instance(self.control_store, place)
        self.addCleanup(serving.release)
        owning = InstanceOwnership.of(self.control_store, self.configuration)
        with self.assertRaises(RuntimeError):
            with owning.held():
                raise RuntimeError("the admission failed")
        self.assertEqual(self.forked(place)["outcome"], "refused")

    def test_two_invocations_of_one_identity_cannot_overlap(self):
        """R8 AT THE REAL LOCK, in two real processes."""
        import multiprocessing

        from tools.fresh_attempt_ports import InstanceOwnership

        owning = InstanceOwnership.of(self.control_store, self.configuration)
        with owning.invocation("job-a-retry-2"):
            answer = self.spawned(_invoking, owning._root, "job-a-retry-2")
            self.assertEqual(answer["outcome"], "refused")
            self.assertIn("in flight", answer["message"])
            # A DIFFERENT IDENTITY IS NOT BLOCKED by this one.
            self.assertEqual(
                self.spawned(_invoking, owning._root,
                             "job-b-retry-2")["outcome"], "taken")
        self.assertEqual(
            self.spawned(_invoking, owning._root,
                         "job-a-retry-2")["outcome"], "taken")

    def spawned(self, call, *operands):
        import multiprocessing

        with multiprocessing.get_context("spawn").Pool(1) as pool:
            return pool.apply(call, tuple(str(one) for one in operands))

    def test_the_guard_is_released_when_the_admission_finishes(self):
        from tools.fresh_attempt_ports import InstanceOwnership

        owning = InstanceOwnership.of(self.control_store, self.configuration)
        with owning.held():
            pass
        place = [one["deployment"]["workspace_storage"]
                 for one in self.configuration["workers"]][0]
        self.assertEqual(self.forked(place)["outcome"], "held")


def _invoking(root, job_id):
    """Take one admission's invocation lock in a SEPARATE process."""
    import os as _os

    _os.environ.setdefault("BATON_V12_STACK_TEST_ROOT", "/var/tmp")
    from baton_v12.contracts import ContractRefusal as Refusal
    from tools.fresh_attempt_ports import InstanceOwnership

    owning = InstanceOwnership(None, root)
    try:
        with owning.invocation(job_id):
            return {"outcome": "taken", "message": None}
    except Refusal as refusal:
        return {"outcome": "refused", "message": refusal.message}


def _guarding(control_path, place):
    """Take the instance guard in a SEPARATE process, and say what happened."""
    import os as _os

    _os.environ.setdefault("BATON_V12_STACK_TEST_ROOT", "/var/tmp")
    from baton_v12.contracts import ContractRefusal as Refusal
    from baton_v12.worker_manager import ControlStore, workspaces

    with ControlStore.open_readonly(control_path, incarnation="probe",
                                    clock=lambda: NOW) as control:
        try:
            guard = workspaces.hold_manager_instance(control, place)
        except Refusal as refusal:
            return {"outcome": "refused", "message": refusal.message}
        guard.release()
        return {"outcome": "held", "message": None}


class ExclusiveInvocation(FreshAttemptCase):
    """R8: a holder is a NAME; an invocation is a LOCK."""

    def test_same_incarnation_concurrent_requests_bind_once(self):
        """THE CASE THE PREVIOUS RACE MISSED, because it varied incarnations."""
        import concurrent.futures
        import threading

        from baton_v12.job_manager import JobStore

        self.prior()
        gate = threading.Barrier(2, timeout=20)
        shared = FakeBinding()
        running, lock = set(), threading.Lock()
        # AND THE WINNER STAYS INSIDE until the loser has tried, so the
        # overlap is the one this case claims rather than whichever one the
        # scheduler happened to produce.
        overlap = threading.Event()

        class Synchronized(FakeOwnership):
            """Hold both admissions together BEFORE either takes the lock."""

            @contextmanager
            def held(self):
                with super().held() as owner:
                    gate.wait()
                    yield owner

        def racing(which):
            del which
            with JobStore.open(self.job_path, authority_uuid=UUID,
                               incarnation="jobs-1",     # THE SAME ONE.
                               clock=self.clock) as store:
                try:
                    return ("admitted", admit(
                        store, self.acts, prior_job_id=PRIOR,
                        exclusion=FakeExclusion(),
                        authorization=self.authorization,
                        binding=shared,
                        ownership=Synchronized(
                            running=running, lock=lock,
                            overlap=overlap))["job_id"])
                except ContractRefusal as refusal:
                    gate.abort()
                    return ("refused", refusal.message)

        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            outcomes = list(pool.map(racing, [1, 2]))
        self.assertEqual(len([one for one in outcomes
                              if one[0] == "admitted"]), 1, outcomes)
        self.assertEqual(len(shared.added), 1, shared.added)
        self.assertIn("in flight",
                      [one for one in outcomes if one[0] == "refused"][0][1])

    def test_a_completed_admission_still_replays_after_the_lock_is_gone(self):
        self.prior()
        first = self.admitted()
        self.assertEqual(self.admitted(), first)
        self.assertEqual(len(self.binding.added), 1)


class TheIntendedSubmissionIsImmutable(FreshAttemptCase):
    """R9: a reservation names an intent, and a name is not one."""

    def test_the_same_submission_name_with_another_document_refuses(self):
        self.prior()
        self.binding = _BindOnce(self.binding)
        with self.assertRaises(_Interrupted):
            self.admitted()
        # The reserved submission id, carrying a DIFFERENT specification.
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, submission(
                submission_id=f"sub-{FRESH}",
                jobs=[job(FRESH, stages=[stage("implementation", WORK_A)])]))
        self.assertIn("for a different document than this one",
                      caught.exception.message)
        # NOT DURABLE, deliberately. A durable refusal is a committed outcome
        # for an operation identity derived from the submission id -- which
        # belongs to the reservation holder -- so sealing one here would let
        # a rejected document permanently poison the very submission the
        # reservation exists to admit. The case below proves it does not.
        self.assertFalse(caught.exception.durable)
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?", (FRESH,)).fetchone())
        # AND THE RETRY'S OWN DOCUMENT STILL PASSES.
        self.binding = self.binding.held
        answer = self.admitted()
        self.assertEqual(answer["stages"],
                         [f"{FRESH}/implementation", f"{FRESH}/review"])

    def test_the_reservation_records_the_document_it_is_for(self):
        self.prior()
        self.admitted()
        held = fresh_attempt_of(self.jobs, FRESH)
        recorded = self.jobs._connection.execute(
            "SELECT signature FROM submissions WHERE submission_id = ?",
            (f"sub-{FRESH}",)).fetchone()[0]
        self.assertEqual(held["submission_signature"], recorded)

    def test_a_submission_identity_already_used_refuses_before_effects(self):
        """THE COLLISION IS MET BEFORE THE WORK AND THE BINDING, not after."""
        self.prior()
        submit(self.jobs, submission(submission_id=f"sub-{FRESH}",
                                     jobs=[job("something-else")]))
        refusal = self.refused()
        # THE JOURNAL ANSWERS FIRST, and it is the stronger statement: the
        # operation identity is settled, so this submission id can never
        # record this document however often the request is repeated.
        self.assertIn("is already settled in this store's journal",
                      refusal.message)
        self.assertIn("choose another submission identity", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])
        self.assertEqual(self.authorization.created, [])


class UnknownResourceIsNotPermission(FreshAttemptCase):
    """R11: an absent token is uncertainty, and the owning reader says so."""

    def test_a_destroyed_runtime_with_no_token_refuses(self):
        self.prior()
        self.exclusion = FakeExclusion(answer=ceased(token=None))
        refusal = self.refused()
        self.assertIn("an absent token is uncertainty", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))

    def test_a_quiescent_runtime_with_no_token_refuses(self):
        self.prior()
        self.exclusion = FakeExclusion(
            answer=ceased(runtime="quiescent", token=None))
        self.assertIn("an absent token is uncertainty",
                      self.refused().message)

    def test_an_attempt_that_was_never_launched_is_positively_established(self):
        """THE ONE READING THAT IS NOT A GUESS."""
        self.prior()
        held = ceased(runtime="not-started", cleanup="complete", token=None)
        held["runtime"]["runtime_id"] = None
        self.exclusion = FakeExclusion(answer=held)
        answer = self.admitted()
        for one in answer["exclusion"].values():
            self.assertEqual(one["resource"],
                             "never acquired: this attempt was never launched")

    def test_a_never_started_axis_with_a_runtime_identity_still_refuses(self):
        """NOT-STARTED BESIDE A MINTED RUNTIME IS A CONTRADICTION, not proof."""
        self.prior()
        held = ceased(runtime="not-started", cleanup="complete", token=None)
        held["runtime"]["runtime_id"] = "runtime-7"
        self.exclusion = FakeExclusion(answer=held)
        self.assertIn("an absent token is uncertainty",
                      self.refused().message)


class TheSubmissionIdentityIsOwnedToo(FreshAttemptCase):
    """R12: a reservation owns BOTH names, not only its Job.

    The lookup selected reservations by the incoming document's Job ids, so
    a second submission reusing the reserved SUBMISSION id for an unrelated
    Job saw no reservation and recorded itself -- and the retry, whose
    operation identity is derived from that submission id, collided after it
    had already published a binding.
    """

    def interrupted(self):
        """A retry stopped after its binding, with its reservation standing."""
        self.prior()
        self.binding = _BindOnce(self.binding)
        with self.assertRaises(_Interrupted):
            self.admitted()
        self.binding = self.binding.held
        return fresh_attempt_of(self.jobs, FRESH)

    def test_a_nonoverlapping_job_cannot_take_the_reserved_submission_id(self):
        held = self.interrupted()
        self.assertEqual(held["submission_id"], f"sub-{FRESH}")
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, submission(submission_id=f"sub-{FRESH}",
                                         jobs=[job("other-job")]))
        self.assertIn("is RESERVED by the fresh attempt for Job",
                      caught.exception.message)
        self.assertIn(FRESH, caught.exception.message)
        # NOTHING WAS RECORDED: not the submission, not its Job, not a stage.
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'other-job'").fetchone())
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT submission_id FROM submissions WHERE submission_id = ?",
            (f"sub-{FRESH}",)).fetchone())

    def test_the_retry_still_completes_after_that_rejection(self):
        """THE REJECTION MUST NOT POISON THE OPERATION IT PROTECTS."""
        self.interrupted()
        with self.assertRaises(ContractRefusal):
            submit(self.jobs, submission(submission_id=f"sub-{FRESH}",
                                         jobs=[job("other-job")]))
        answer = self.admitted()
        self.assertEqual(answer["job_id"], FRESH)
        self.assertEqual(answer["submission_id"], f"sub-{FRESH}")
        self.assertEqual(answer["stages"],
                         [f"{FRESH}/implementation", f"{FRESH}/review"])
        # AND IT REPLAYS afterwards, unchanged.
        self.assertEqual(self.admitted(), answer)

    def test_an_ordinary_submission_that_came_first_refuses_the_retry(self):
        """THE OTHER ORDER, on the submission name rather than the Job."""
        self.prior()
        submit(self.jobs, submission(submission_id=f"sub-{FRESH}",
                                     jobs=[job("other-job")]))
        refusal = self.refused()
        # THE JOURNAL ANSWERS FIRST, and it is the stronger statement: the
        # operation identity is settled, so this submission id can never
        # record this document however often the request is repeated.
        self.assertIn("is already settled in this store's journal",
                      refusal.message)
        self.assertIn("choose another submission identity", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])
        self.assertEqual(self.authorization.created, [])

    def test_two_retry_intents_cannot_share_one_submission_identity(self):
        self.prior()
        self.prior(job_id="quickstart-x")
        self.admitted()
        with self.assertRaises(ContractRefusal) as caught:
            admit(self.jobs, self.acts, prior_job_id="quickstart-x",
                  exclusion=self.exclusion,
                  authorization=self.authorization,
                  binding=self.binding, ownership=self.ownership,
                  submission_id=f"sub-{FRESH}")
        self.assertIn("one submission identity names one intent",
                      caught.exception.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, "quickstart-x-retry-2"))

    def test_the_exact_intended_document_is_still_admissible(self):
        """THE ONE SUBMISSION THE RESERVATION EXISTS FOR."""
        held = self.interrupted()
        document = json.loads(self.jobs._connection.execute(
            "SELECT document FROM submissions WHERE submission_id = ?",
            (f"sub-{PRIOR}",)).fetchone()[0])
        del document
        self.assertEqual(held["state"], "intended")
        self.assertEqual(self.admitted()["job_id"], FRESH)

    def test_an_unrelated_submission_is_untouched_by_the_reservation(self):
        """THE RULE IS NARROW: it owns two names, not every submission."""
        self.interrupted()
        recorded = submit(self.jobs, submission(
            submission_id="sub-unrelated", jobs=[job("unrelated-job")]))
        self.assertEqual(recorded["jobs"], ["unrelated-job"])
        self.assertEqual(self.admitted()["job_id"], FRESH)


class TheJournalOwnsTheSubmissionIdentity(FreshAttemptCase):
    """R15: a settled operation owns a name even with no submission row.

    `store.transact` journals a DURABLE REFUSAL as that operation's committed
    outcome, so `submission.record:<id>` can be permanently settled while
    `submissions` holds nothing. The reservation read only the rows, so it
    reserved, published a binding, and met the journal's immutable signature
    at `submit` -- where nothing could be done about it, and where the
    refusal told the caller to repeat a request that could never succeed.
    """

    def settled_by_a_durable_refusal(self):
        """An ordinary submission that refuses durably under the retry's id.

        It reuses the PRIOR Job's identity, which `_unclaimed` refuses
        durably -- so the journal records an outcome and `submissions`
        records nothing, which is exactly the shape the review reproduced.
        """
        self.prior()
        with self.assertRaises(ContractRefusal) as caught:
            submit(self.jobs, submission(submission_id=f"sub-{FRESH}",
                                         jobs=[job(PRIOR)]))
        self.assertTrue(caught.exception.durable)
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT submission_id FROM submissions WHERE submission_id = ?",
            (f"sub-{FRESH}",)).fetchone())
        self.assertIsNotNone(self.jobs._connection.execute(
            "SELECT state FROM operations WHERE operation_id = ?",
            (f"submission.record:sub-{FRESH}",)).fetchone())

    def test_a_settled_refusal_refuses_the_retry_before_any_effect(self):
        self.settled_by_a_durable_refusal()
        refusal = self.refused()
        self.assertIn("is already settled in this store's journal",
                      refusal.message)
        self.assertIn("refused", refusal.message)
        self.assertIn("choose another submission identity", refusal.message)
        # NO RESERVATION, NO WORK, NO BINDING.
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])
        self.assertEqual(self.authorization.created, [])

    def test_it_does_not_promise_a_repair_that_cannot_happen(self):
        """THE ADVICE IS THE DEFECT'S OTHER HALF."""
        self.settled_by_a_durable_refusal()
        refusal = self.refused()
        self.assertNotIn("run the same request again", refusal.message)
        self.assertIn("repeating this request will not change it",
                      refusal.message)

    def test_the_earlier_outcome_is_preserved_rather_than_freed(self):
        """NOTHING IS ERASED OR RENAMED TO MAKE THE NAME AVAILABLE."""
        self.settled_by_a_durable_refusal()
        before = self.jobs._connection.execute(
            "SELECT operation_id, kind, signature, state, refusal "
            "FROM operations WHERE operation_id = ?",
            (f"submission.record:sub-{FRESH}",)).fetchone()
        self.refused()
        after = self.jobs._connection.execute(
            "SELECT operation_id, kind, signature, state, refusal "
            "FROM operations WHERE operation_id = ?",
            (f"submission.record:sub-{FRESH}",)).fetchone()
        self.assertEqual(tuple(after), tuple(before))

    def test_another_submission_identity_admits_the_same_retry(self):
        """THE ACTIONABLE OUTCOME IS ACTIONABLE."""
        self.settled_by_a_durable_refusal()
        self.refused()
        answer = self.admitted(submission_id="sub-quickstart-c-retry-2b")
        self.assertEqual(answer["job_id"], FRESH)
        self.assertEqual(answer["submission_id"],
                         "sub-quickstart-c-retry-2b")
        self.assertEqual(answer["stages"],
                         [f"{FRESH}/implementation", f"{FRESH}/review"])

    def test_an_incompatible_committed_submission_refuses_the_same_way(self):
        self.prior()
        submit(self.jobs, submission(submission_id=f"sub-{FRESH}",
                                     jobs=[job("unrelated-job")]))
        refusal = self.refused()
        self.assertIn("is already settled in this store's journal",
                      refusal.message)
        self.assertIn("committed", refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])

    def test_the_retrys_own_committed_submission_replays(self):
        """A LOST COMPLETION, which is the case this must NOT refuse.

        The admission recorded its submission and died before cut C marked
        the intent admitted, so the journal holds `submission.record:<id>`
        committed with THIS document's signature while the reservation still
        reads `intended`. The same request must finish.

        THE CRASH IS SIMULATED BY RESTORING THE ROW cut C would not yet have
        written -- the one column a lost completion leaves behind -- rather
        than by recording a submission with no reservation, which is a state
        this operation cannot reach and which its own Job check refuses.
        """
        self.prior()
        self.admitted()
        self.jobs._connection.execute(
            "UPDATE fresh_attempts SET state = 'intended', "
            "admitted_at = NULL WHERE job_id = ?", (FRESH,))
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (f"fresh_attempt.admit:{FRESH}",))
        self.assertEqual(fresh_attempt_of(self.jobs, FRESH)["state"],
                         "intended")
        self.assertIsNotNone(self.jobs._connection.execute(
            "SELECT state FROM operations WHERE operation_id = ?",
            (f"submission.record:sub-{FRESH}",)).fetchone())

        answer = self.admitted()
        self.assertEqual(answer["job_id"], FRESH)
        self.assertEqual(answer["submission_id"], f"sub-{FRESH}")
        self.assertEqual(fresh_attempt_of(self.jobs, FRESH)["state"],
                         "admitted")
        # AND NOTHING WAS DONE TWICE.
        self.assertEqual(len(self.binding.added), 1)
        self.assertEqual(len(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?",
            (FRESH,)).fetchall()), 1)


class TheExclusionOutlivesEveryBorrower(TheRealInstanceGuard):
    """R13: overlapping admissions, and who is allowed to let go.

    The first cut asked whether the guard existed, acquired, and released
    unless it had been borrowed. Two overlapping admissions both saw it
    unheld, both received the same cached descriptor, and the FIRST one out
    closed it while the second was still running.
    """

    def owning(self):
        from tools.fresh_attempt_ports import InstanceOwnership

        return InstanceOwnership.of(self.control_store, self.configuration)

    def place(self):
        return [one["deployment"]["workspace_storage"]
                for one in self.configuration["workers"]][0]

    def test_the_first_borrower_out_does_not_release_the_second(self):
        place = self.place()
        with self.owning().held():
            self.assertEqual(self.forked(place)["outcome"], "refused")
            with self.owning().held():
                self.assertEqual(self.forked(place)["outcome"], "refused")
            # THE INNER ONE EXITED AND THE OUTER IS STILL RUNNING.
            self.assertEqual(self.forked(place)["outcome"], "refused")
        self.assertEqual(self.forked(place)["outcome"], "held")

    def test_overlapping_lifetimes_in_either_exit_order(self):
        """THE PROBE'S OWN INTERLEAVING: the FIRST context exits first."""
        import contextlib

        place = self.place()
        with contextlib.ExitStack() as stack:
            first = stack.enter_context(self.owning().held())
            second = self.owning().held()
            second.__enter__()
            self.assertEqual(self.forked(place)["outcome"], "refused")
            # Close the FIRST one while the second is still open.
            stack.close()
            del first
            self.assertEqual(self.forked(place)["outcome"], "refused")
            second.__exit__(None, None, None)
            del second
        self.assertEqual(self.forked(place)["outcome"], "held")

    def test_an_error_exit_releases_no_more_than_an_ordinary_one(self):
        place = self.place()
        with self.owning().held():
            with self.assertRaises(RuntimeError):
                with self.owning().held():
                    raise RuntimeError("the admission failed")
            self.assertEqual(self.forked(place)["outcome"], "refused")
        self.assertEqual(self.forked(place)["outcome"], "held")

    def test_a_serving_owner_is_never_released_by_any_borrower(self):
        from baton_v12.worker_manager import workspaces

        place = self.place()
        serving = workspaces.hold_manager_instance(self.control_store, place)
        self.addCleanup(serving.release)
        with self.owning().held() as borrowed:
            self.assertIs(borrowed, serving)
            with self.owning().held():
                pass
        self.assertEqual(self.forked(place)["outcome"], "refused")

    def test_the_borrow_count_returns_to_zero(self):
        from baton_v12.worker_manager import workspaces

        place = self.place()
        self.assertEqual(workspaces.borrowers_of(place), 0)
        with self.owning().held():
            self.assertEqual(workspaces.borrowers_of(place), 1)
            with self.owning().held():
                self.assertEqual(workspaces.borrowers_of(place), 2)
            self.assertEqual(workspaces.borrowers_of(place), 1)
        self.assertEqual(workspaces.borrowers_of(place), 0)

    def test_a_forked_child_inherits_no_borrow(self):
        """THE CACHE'S FORK RULE, extended to the count beside it."""
        from baton_v12.worker_manager import workspaces

        place = self.place()
        with self.owning().held():
            self.assertEqual(workspaces.borrowers_of(place), 1)
            workspaces._forget_inherited_guards()
            self.assertEqual(workspaces.borrowers_of(place), 0)
        # The guard this process acquired is already disowned; a separate
        # process can take it, which is what a child must not have prevented.
        self.assertEqual(self.forked(place)["outcome"], "held")


class TheHostIsThisInstanceS(TheConnectedRetry):
    """R14: the relationship is established, not asserted by repetition."""

    def other_control(self):
        import tempfile

        from baton_v12.worker_manager import ControlStore

        place = tempfile.mkdtemp(prefix="w359719-elsewhere-")
        self.addCleanup(__import__("shutil").rmtree, place, True)
        store = ControlStore.open(str(pathlib.Path(place,
                                                   "control.sqlite3")),
                                  incarnation="manager-1", clock=self.clock)
        self.addCleanup(store.close)
        return store

    def identity(self):
        return self.bound

    def test_an_unrelated_control_store_refuses_before_any_effect(self):
        """THE PROBE'S OWN COMPOSITION: real ports, a DIFFERENT empty store."""
        from tools.fresh_attempt_ports import HostExclusion

        self.failed()
        with self.assertRaises(ContractRefusal) as caught:
            self.admit(exclusion=HostExclusion(self.other_control(),
                                               identity=self.identity()))
        self.assertIn("evidence about another deployment",
                      caught.exception.message)
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'job-a-retry-2'"
        ).fetchone())
        # AND THE DEPLOYMENT WAS NOT TOUCHED: no binding for the fresh Job.
        self.assertIsNone(self.binding.binding_of("job-a-retry-2"))

    def test_ports_answering_for_two_deployments_refuse(self):
        """THE MANAGER'S OWN CHECK, independent of how a caller composed."""
        import tempfile

        from tools.fresh_attempt_ports import HostExclusion

        self.failed()
        elsewhere = dict(self.identity(),
                         root=tempfile.mkdtemp(prefix="w359719-other-"))
        self.addCleanup(__import__("shutil").rmtree, elsewhere["root"], True)
        with self.assertRaises(ContractRefusal) as caught:
            self.admit(exclusion=HostExclusion(self.control_store,
                                               identity=elsewhere))
        self.assertIn("answer for different deployments",
                      caught.exception.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, "job-a-retry-2"))

    def test_a_configuration_for_another_authority_refuses(self):
        from tools.fresh_attempt_ports import HostExclusion

        self.failed()
        foreign = dict(self.identity(), authority_uuid="f" * 32)
        with self.assertRaises(ContractRefusal) as caught:
            self.admit(exclusion=HostExclusion(self.control_store,
                                               identity=foreign))
        self.assertIn("two of them are two namespaces",
                      caught.exception.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, "job-a-retry-2"))

    def test_the_right_instance_still_admits(self):
        """THE POSITIVE CASE, with every port bound to this instance."""
        from tools.fresh_attempt_ports import (DeploymentBinding,
                                               HostExclusion,
                                               InstanceOwnership,
                                               WorkAuthorization)

        import io

        self.failed()
        identity = self.identity()
        answer = self.admit(
            exclusion=HostExclusion(self.control_store, identity=identity),
            authorization=WorkAuthorization.opened(
                self.places["authority_store"], authority_uuid=self.uuid,
                route="baton.impl", identity=identity),
            binding=DeploymentBinding(self.state, stream=io.StringIO(),
                                      identity=identity),
            ownership=InstanceOwnership.of(self.control_store,
                                           self.configured(),
                                           identity=identity))
        self.assertEqual(answer["job_id"], "job-a-retry-2")
        self.assertEqual(answer["binding"]["disposition"], "added")

    def configured(self):
        return json.loads(pathlib.Path(
            self.places["configuration"]).read_text())

    def test_the_command_refuses_a_store_the_instance_does_not_own(self):
        """AT THE ACTUAL CLI WIRING, not only in the composition."""
        import io
        import tempfile

        from tools import job_manager as command

        self.failed()
        elsewhere = tempfile.mkdtemp(prefix="w359719-cli-")
        self.addCleanup(__import__("shutil").rmtree, elsewhere, True)
        with self.assertRaises(ContractRefusal) as caught:
            command.main(["--store", self.places["job_store"],
                          "--incarnation", "jobs-2",
                          "--authority-uuid", self.uuid,
                          "fresh-attempt", "--prior-job", "job-a",
                          "--control",
                          str(pathlib.Path(elsewhere, "control.sqlite3")),
                          "--authority", self.places["authority_store"],
                          "--instance", self.state],
                         clock=self.clock, stream=io.StringIO())
        self.assertIn("control store this command was given",
                      caught.exception.message)
        self.assertIn(self.places["control_store"], caught.exception.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, "job-a-retry-2"))


class TheBorrowIsAtomic(TheRealInstanceGuard):
    """R16: acquiring a lifetime and releasing the last one cannot interleave.

    The first cut obtained the cached guard and THEN registered its borrow.
    A probe paused between the two while the last borrower decremented to
    zero and closed the descriptor: the second user entered holding a guard
    that guarded nothing, and a spawned process took the instance.
    """

    def owning(self):
        from tools.fresh_attempt_ports import InstanceOwnership

        return InstanceOwnership.of(self.control_store, self.configuration)

    def place(self):
        return [one["deployment"]["workspace_storage"]
                for one in self.configuration["workers"]][0]

    def test_a_holder_paused_mid_acquisition_keeps_its_exclusion(self):
        """THE PROBE'S OWN INTERLEAVING, at the real function boundary.

        The second borrower is paused exactly where the probe paused it --
        immediately after `hold_manager_instance` returns -- and the first
        borrower then exits. The descriptor the second holds must still be
        live and the instance must still be excluded from another process.

        WHAT MAKES THAT TRUE is that holding is counted inside
        `hold_manager_instance` itself, in the same critical section as the
        cache read: by the time it returns, this holder is registered, so
        there is no window for a last release to close it underneath.

        EVERY SPAWN HAPPENS ON THIS THREAD. `multiprocessing` from a worker
        thread of a process that also forks guards is its own hazard, and a
        case about a lock should not become a case about that.
        """
        import threading

        from baton_v12.worker_manager import workspaces

        place = self.place()
        paused = threading.Event()
        proceed = threading.Event()
        linger = threading.Event()
        answers = {}
        real = workspaces.hold_manager_instance

        def pausing(store, where):
            guard = real(store, where)
            if threading.current_thread().name == "second":
                paused.set()
                proceed.wait(timeout=30)
            return guard

        first = self.owning().held()
        first.__enter__()

        def second():
            with self.owning().held() as guard:
                answers["descriptor"] = guard._descriptor
                answers["holders"] = workspaces.holders_of(place)
                linger.wait(timeout=30)

        workspaces.hold_manager_instance = pausing
        self.addCleanup(setattr, workspaces, "hold_manager_instance", real)
        running = threading.Thread(target=second, name="second")
        running.start()
        self.assertTrue(paused.wait(timeout=30))

        # THE FIRST BORROWER LEAVES WHILE THE SECOND IS MID-ACQUISITION.
        first.__exit__(None, None, None)
        proceed.set()
        for _ in range(300):
            if "descriptor" in answers:
                break
            threading.Event().wait(0.01)
        self.assertIsNotNone(answers.get("descriptor"),
                             "the first holder's exit closed the second's "
                             "descriptor")
        self.assertEqual(self.forked(place)["outcome"], "refused")
        linger.set()
        running.join(timeout=30)
        self.assertFalse(running.is_alive())
        self.assertEqual(workspaces.holders_of(place), 0)
        self.assertEqual(self.forked(place)["outcome"], "held")

    def test_many_concurrent_borrowers_hold_one_instance(self):
        """THE SAME QUESTION WITHOUT A PAUSE: real threads, real contention."""
        import concurrent.futures
        import threading

        from baton_v12.worker_manager import workspaces

        place = self.place()
        ready = threading.Barrier(5, timeout=30)
        seen = []

        release = threading.Event()

        def borrowing(which):
            del which
            with self.owning().held() as guard:
                seen.append(guard._descriptor is not None)
                ready.wait()
                # Hold every borrower open while THIS thread asks whether
                # another process can take the instance.
                release.wait(timeout=30)
            return "left"

        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            running = [pool.submit(borrowing, one) for one in range(4)]
            ready.wait()
            excluded = self.forked(place)["outcome"]
            release.set()
            outcomes = [one.result(timeout=30) for one in running]
        self.assertEqual(excluded, "refused")
        self.assertEqual(outcomes, ["left"] * 4)
        self.assertEqual(seen, [True] * 4)
        self.assertEqual(workspaces.borrowers_of(place), 0)
        self.assertEqual(self.forked(place)["outcome"], "held")


class EveryOwnerSaysWhichInstance(FreshAttemptCase):
    """R17: an undeclared port is not an exempt one."""

    def test_an_unbound_port_refuses_before_anything_is_read(self):
        class Silent(FakeExclusion):
            def instance(self):
                return None

        self.prior()
        self.exclusion = Silent()
        refusal = self.refused()
        self.assertIn("does not say which instance it answers for",
                      refusal.message)
        self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))
        self.assertEqual(self.binding.added, [])
        self.assertEqual(self.authorization.created, [])

    def test_each_of_the_four_is_required_to_declare(self):
        self.prior()
        for name in ("exclusion", "authorization", "binding", "ownership"):
            port = getattr(self, name)
            held, port.instance = port.instance, lambda: None
            try:
                refusal = self.refused()
            finally:
                port.instance = held
            self.assertIn("does not say which instance", refusal.message)
            self.assertIsNone(fresh_attempt_of(self.jobs, FRESH))

    def test_a_real_host_port_cannot_be_built_without_one(self):
        """THE PRODUCTION CONSTRUCTOR, not only the manager's check."""
        from tools.fresh_attempt_ports import HostExclusion

        with self.assertRaises(ContractRefusal) as caught:
            HostExclusion(object(), None)
        self.assertIn("composed without an instance identity",
                      caught.exception.message)

    def test_a_real_host_port_proves_the_store_it_wraps_at_birth(self):
        from baton_v12.worker_manager import ControlStore
        from tools.fresh_attempt_ports import HostExclusion

        control = ControlStore.open(self.control_path, incarnation="probe",
                                    clock=self.clock)
        self.addCleanup(control.close)
        with self.assertRaises(ContractRefusal) as caught:
            HostExclusion(control, STAND_IN)
        self.assertIn("evidence about another deployment",
                      caught.exception.message)


class OneCoherentOwnershipRule(TheRealInstanceGuard):
    """R19: lifetime owners and borrowers are both just holders."""

    def owning(self):
        from tools.fresh_attempt_ports import InstanceOwnership

        return InstanceOwnership.of(self.control_store, self.configuration)

    def place(self):
        return [one["deployment"]["workspace_storage"]
                for one in self.configuration["workers"]][0]

    def test_a_serving_lifetime_taken_during_a_borrow_survives_it(self):
        """THE REVIEWER'S SEQUENCE, exactly: borrow, then serve, then leave."""
        from baton_v12.worker_manager import workspaces

        place = self.place()
        borrow = self.owning().held()
        borrow.__enter__()
        serving = workspaces.hold_manager_instance(self.control_store, place)
        self.addCleanup(serving.release)
        borrow.__exit__(None, None, None)
        # THE SERVING OWNER STILL HOLDS IT.
        self.assertIsNotNone(serving._descriptor)
        self.assertEqual(self.forked(place)["outcome"], "refused")
        self.assertEqual(workspaces.holders_of(place), 1)

    def test_a_borrow_survives_a_serving_lifetime_ending_under_it(self):
        """THE RECIPROCAL, which the review also named."""
        from baton_v12.worker_manager import workspaces

        place = self.place()
        serving = workspaces.hold_manager_instance(self.control_store, place)
        with self.owning().held() as borrowed:
            serving.release()
            self.assertIsNotNone(borrowed._descriptor)
            self.assertEqual(self.forked(place)["outcome"], "refused")
        self.assertEqual(workspaces.holders_of(place), 0)
        self.assertEqual(self.forked(place)["outcome"], "held")

    def test_the_last_holder_of_either_kind_closes_it(self):
        from baton_v12.worker_manager import workspaces

        place = self.place()
        serving = workspaces.hold_manager_instance(self.control_store, place)
        with self.owning().held():
            with self.owning().held():
                self.assertEqual(workspaces.holders_of(place), 3)
            self.assertEqual(workspaces.holders_of(place), 2)
        self.assertEqual(workspaces.holders_of(place), 1)
        self.assertEqual(self.forked(place)["outcome"], "refused")
        serving.release()
        self.assertEqual(workspaces.holders_of(place), 0)
        self.assertEqual(self.forked(place)["outcome"], "held")


class TheForkedChildIsNotStuck(TheRealInstanceGuard):
    """R20: a child must inherit no authority and no locked mutex."""

    def place(self):
        return [one["deployment"]["workspace_storage"]
                for one in self.configuration["workers"]][0]

    def test_a_child_forked_while_the_mutex_is_held_can_still_borrow(self):
        """THE REVIEWER'S BOUNDED PROBE, as a case.

        A helper thread holds the real `_BORROWING` mutex; the main thread
        forks. The child inherits the lock LOCKED and the thread that owns
        it does not exist there, so without the fork handler reinitialising
        it the child waits forever. The child reports through an exit code
        and is reaped with a bounded wait.

        PYTHON WARNS ABOUT FORKING A MULTITHREADED PROCESS and is right to;
        this is a controlled check of the guard's own fork contract, which
        the product explicitly has, rather than a suggestion to fork.
        """
        import os
        import threading

        from baton_v12.worker_manager import workspaces

        place = self.place()
        holding = threading.Event()
        release = threading.Event()

        def keeper():
            with workspaces._BORROWING:
                holding.set()
                release.wait(timeout=30)

        thread = threading.Thread(target=keeper, name="keeper")
        thread.start()
        self.addCleanup(thread.join, 30)
        self.addCleanup(release.set)
        self.assertTrue(holding.wait(timeout=30))

        child = os.fork()
        if child == 0:                                  # pragma: no cover
            code = 70
            try:
                import signal

                signal.alarm(5)
                with workspaces.borrow_manager_instance(self.control_store,
                                                        place):
                    code = 0
            except BaseException:
                code = 71
            finally:
                os._exit(code)
        release.set()
        thread.join(timeout=30)
        for _ in range(300):
            waited, status = os.waitpid(child, os.WNOHANG)
            if waited:
                break
            threading.Event().wait(0.02)
        else:                                           # pragma: no cover
            os.kill(child, 9)
            os.waitpid(child, 0)
            self.fail("the forked child hung on the inherited mutex")
        self.assertTrue(os.WIFEXITED(status), status)
        self.assertEqual(os.WEXITSTATUS(status), 0,
                         "the child could not take a borrow")

    def test_a_child_inherits_no_holder_count(self):
        from baton_v12.worker_manager import workspaces

        place = self.place()
        with self.owning().held():
            self.assertEqual(workspaces.holders_of(place), 1)
            workspaces._forget_inherited_guards()
            self.assertEqual(workspaces.holders_of(place), 0)
            self.assertEqual(workspaces.borrowers_of(place), 0)

    def owning(self):
        from tools.fresh_attempt_ports import InstanceOwnership

        return InstanceOwnership.of(self.control_store, self.configuration)


class TheJobStoreBelongsToTheInstance(TheConnectedRetry):
    """R18: sharing an Authority does not make two deployments one."""

    def elsewhere(self):
        """A SECOND REAL INSTANCE, prepared with the same Authority uuid."""
        import io
        import tempfile

        from tools import bootstrap
        from tools.fresh_attempt_ports import instance_identity

        place = tempfile.mkdtemp(prefix="w359719-second-",
                                 dir=os.path.dirname(self.state))
        self.addCleanup(__import__("shutil").rmtree, place, True)
        root = os.path.join(place, "bootstrap-deployment")
        bootstrap.persist_identity(bootstrap.layout(root), self.uuid)
        document = dict(self.document, state_root=root)
        bootstrap.prepare(document, stream=io.StringIO())
        pathlib.Path(root, "install-inputs.json").write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n")
        return root, instance_identity(root)

    def test_another_instance_s_ports_cannot_admit_this_store_s_job(self):
        import io

        from baton_v12.worker_manager import ControlStore
        from tools import bootstrap
        from tools.fresh_attempt_ports import (DeploymentBinding,
                                               HostExclusion,
                                               InstanceOwnership,
                                               WorkAuthorization)

        self.failed()
        root, other = self.elsewhere()
        places = bootstrap.layout(root)
        control = ControlStore.open(places["control_store"],
                                    incarnation="manager-1",
                                    clock=self.clock)
        self.addCleanup(control.close)
        configuration = json.loads(
            pathlib.Path(places["configuration"]).read_text())
        with self.assertRaises(ContractRefusal) as caught:
            self.admit(
                exclusion=HostExclusion(control, identity=other),
                authorization=WorkAuthorization.opened(
                    places["authority_store"], authority_uuid=self.uuid,
                    route="baton.impl", identity=other),
                binding=DeploymentBinding(root, stream=io.StringIO(),
                                          identity=other),
                ownership=InstanceOwnership.of(control, configuration,
                                               identity=other))
        self.assertIn("an Authority two instances share does not make them "
                      "one", caught.exception.message)
        # NOTHING WAS ADMITTED AND NOTHING WAS PUBLISHED, in either place.
        self.assertIsNone(fresh_attempt_of(self.jobs, "job-a-retry-2"))
        self.assertIsNone(
            DeploymentBinding(root).binding_of("job-a-retry-2"))
        self.assertIsNone(self.binding.binding_of("job-a-retry-2"))

    def test_this_instance_s_own_store_still_admits(self):
        self.failed()
        self.assertEqual(self.admit()["job_id"], "job-a-retry-2")


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
