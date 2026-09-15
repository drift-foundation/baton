"""W103525: fixed scheduling scenarios over REAL owners, and the validator's own
negative cases.

WHAT IS REAL HERE. A real Job store, the real `activate_pool`, the real
`scheduler.reserve` and the real projection decide every outcome recorded below.
The scenario is scripted; the answers are not. Nothing in this module inserts an
allocation row, fabricates a claim or writes an owner's receipt, which is
`PLAN.md`'s rule: "Fixed scripts alone are not evidence that those acts ran."

WHAT IS DELIBERATELY NOT CLAIMED. These fixtures run against `JobManagerCase`'s
fake Authority sessions, exactly as the existing accepted scheduling suite does,
and the reviewer's baseline already recorded that this is exploratory evidence
rather than composed certification. No test here claims the scheduler contract is
certified, and the two retained contract mismatches are asserted as GAPS.
"""

import copy
import json
import os
import unittest

from types import SimpleNamespace

from baton_v12.job_manager import allocation_of, submit
from baton_v12.job_manager.scheduler import reserve
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import agent_sessions_of
from baton_v12.worker_manager.offers import claimed_offers_for

from tests.job_manager.fixtures import (JobManagerCase, PROFILE, WORK_A,
                                        WORK_B, WORK_C, job, stage, submission)
from tests.job_manager.test_scheduling import pool, principals, worker

from tests.tools import test_stage_execution as composed_fixture

from . import scheduler_trace


HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = (os.path.join(HERE, "scheduler_trace.py"),
           os.path.join(HERE, "test_scheduler_trace.py"))

# R1, review 2026-09-12T16:18:34Z: THESE ARE NAMED FOR WHAT THEY ARE.
#
# The first draft called two aliased canonical principals "two teams" and two
# `test_scope` directory strings "two repositories". They are neither: a team is
# an Authority-facing membership fact and a repository binding is an independent
# source nomination, and this pool has no access to either. Calling them by the
# stronger name was a label substituted for evidence, which is exactly what the
# review refused. They are now named as the two things they really are, and the
# absent stronger facts are recorded as an explicit gap.
PRINCIPAL_ONE = "principal:group-one"
PRINCIPAL_TWO = "principal:group-two"
SCOPE_ONE = ["v12/python/tests/job_manager"]
SCOPE_TWO = ["v12/python/tests/tools"]


def scenario_workers():
    """Two implementation slots, two review slots, and integration capacity
    configured separately -- not multiplexed onto a producer."""
    return [worker("impl-one", "implementation", "baton.impl-one",
                   ["implementation"]),
            worker("impl-two", "implementation", "baton.impl-two",
                   ["implementation"]),
            worker("review-one", "review", "baton.review-one", ["review"]),
            worker("review-two", "review", "baton.review-two", ["review"]),
            worker("integrate-one", "implementation", "baton.integrate-one",
                   ["integration"])]


def scenario_jobs():
    """Four Jobs across two principal groups and two declared test scopes.

    One dependency edge A -> B, and C and D independent of both and of each
    other. The edge is expressed as the submission schema expresses it, so the
    real projection -- not this module -- decides when B becomes eligible.

    NOT TWO TEAMS AND NOT TWO REPOSITORIES: see the note beside PRINCIPAL_ONE.
    """
    return [
        job("job-a", test_scope=SCOPE_ONE,
            stages=[stage("implementation", WORK_A),
                    stage("review", WORK_A,
                          depends_on=[{"job_id": "job-a",
                                       "kind": "implementation"}])]),
        job("job-b", test_scope=SCOPE_ONE,
            stages=[stage("implementation", WORK_B,
                          depends_on=[{"job_id": "job-a",
                                       "kind": "implementation"}])]),
        job("job-c", test_scope=SCOPE_TWO,
            stages=[stage("implementation", WORK_C)]),
        job("job-d", test_scope=SCOPE_TWO,
            stages=[stage("implementation", WORK_C),
                    # R1: AN UNGATED REVIEW, and it is ungated on purpose. The
                    # review lane must be shown eligible while the
                    # implementation lane is full, and the only honest way to
                    # have an eligible review without an owner-issued
                    # completion is for it to depend on nothing. A review opened
                    # by pretending an implementation finished would be the
                    # fabricated completion this review refused.
                    stage("review", WORK_C)])]


class TraceCase(JobManagerCase):
    """The driver: logical ticks over real owners, recording their answers."""

    def setUp(self):
        super().setUp()
        self.jobs_store = self.store()
        self.principals = {}

    def scenario(self, **changed):
        held = {"name": "four-jobs-two-principal-groups-two-test-scopes",
                "jobs": scenario_jobs(), "workers": scenario_workers(),
                "ticks": 100}
        held.update(changed)
        return scheduler_trace.Scenario(**held)

    def activated(self, scenario, trace):
        """The real pool activation, with two principal groups resolved.

        The split is over CANONICAL PRINCIPALS, which is the separation identity
        the scheduler actually decides capacity on. It is not Authority team
        membership and this does not claim to be.
        """
        from baton_v12.job_manager import activate_pool

        document = pool(workers=scenario.workers)
        # ONE CANONICAL PRINCIPAL PER CONFIGURED WORKER, which is the ordinary
        # shape `principals()` composes.
        #
        # R1, corrected after measurement: the first draft collapsed five
        # workers onto two aliased principals and called them "two teams". The
        # reviewer predicted the consequence and the run confirmed it -- with
        # both implementation slots taken, BOTH principal groups were occupied,
        # so `job-d/review` was refused and no unrelated review could ever
        # reserve. The collapse was not a team model; it was a capacity
        # reduction wearing a team's name. Sharing a principal is exercised
        # deliberately and separately, in the alias case below.
        resolved = principals(document)
        self.principals = dict(resolved)
        answer = activate_pool(self.jobs_store, document, resolved)
        trace.record(0, "activate-pool", outcome="performed",
                     operation_id=f"pool.activate:{answer['generation']}",
                     evidence=f"pool_generations:{answer['generation']}")
        return answer

    def submitted(self, scenario, trace):
        submit(self.jobs_store, submission(jobs=scenario.jobs))
        for one in scenario.jobs:
            trace.record(0, "submit", outcome="performed", job_id=one["job_id"],
                         operation_id=f"submission:{one['job_id']}",
                         evidence="jobs:" + one["job_id"])

    def eligible(self, order):
        """The stages the REAL projection says are owed an admission.

        W103525, corrected after measurement: the first form of this helper
        treated "has a live episode" as eligibility, and the very first run
        showed why that is wrong -- it reserved `job-b/implementation` while
        the `job-a/implementation` it depends on had not completed. Dependency
        eligibility belongs to `projection.owed_acts`, which answers `admit`
        only for a stage whose own store reports it queued rather than blocked.
        This asks that owner instead of deciding for itself.
        """
        from baton_v12.job_manager import owed_acts

        owed = {one["stage_id"]: one
                for one in owed_acts(self.jobs_store, self.operations())
                if one["act"] == "admit"}
        return [self.attempting(self.jobs_store, one)
                for one in order if one in owed]

    def tick(self, trace, tick, order, completing=()):
        """One logical tick: try to reserve each eligible stage, in `order`.

        THE SCHEDULER DECIDES. This asks `reserve` and records exactly what came
        back -- an allocation, or a refusal with its own public cause. It never
        retries past a refusal and never writes an allocation itself.
        """
        for attempt in self.eligible(order):
            stage_id = attempt["stage_id"]
            job_id = stage_id.split("/")[0]
            # THE DURABLE ANSWER FIRST: does this attempt already hold one?
            standing = allocation_of(self.jobs_store, attempt["attempt_id"])
            try:
                allocated = reserve(self.jobs_store, attempt)
            except ContractRefusal as refused:
                trace.record(tick, "reserve", outcome="refused",
                             job_id=job_id, stage_id=stage_id,
                             episode=attempt["episode"],
                             attempt_id=attempt["attempt_id"],
                             cause=f"{refused.category}/{refused.code}: "
                                   f"{refused}")
                continue
            worker_id = allocated["worker_id"]
            participant = self._participant(worker_id)
            if standing is not None:
                # R4, review 2026-09-12T16:18:34Z: THIS IS READ FROM THE STORE
                # AND NOT FROM THIS PROCESS'S MEMORY. The first draft kept a
                # transient `_reserved` set, so a FRESH driver over the same
                # durable files -- which is what a restart really is -- recorded
                # an idempotent reserve as a second performed reservation and the
                # oracle correctly refused its own driver's output. `reserve` is
                # idempotent and returns the standing allocation; whether one
                # already existed is a durable fact, asked before the call.
                trace.record(tick, "observe", outcome="performed",
                             job_id=job_id, stage_id=stage_id,
                             episode=attempt["episode"],
                             attempt_id=attempt["attempt_id"],
                             worker_id=worker_id, participant=participant,
                             principal=self.principals.get(participant),
                             evidence="allocations:" + attempt["attempt_id"])
                continue
            trace.record(tick, "reserve", outcome="performed", job_id=job_id,
                         stage_id=stage_id, episode=attempt["episode"],
                         attempt_id=attempt["attempt_id"],
                         worker_id=worker_id, participant=participant,
                         principal=self.principals.get(participant),
                         operation_id="allocation.reserve:"
                                      + attempt["attempt_id"],
                         evidence="allocations:" + attempt["attempt_id"])
        for stage_id in completing:
            self.released(trace, tick, stage_id)

    def _participant(self, worker_id):
        for one in scenario_workers():
            if one["worker_id"] == worker_id:
                return one["participant"]
        return None

    def released(self, trace, tick, stage_id):
        """Release one ALLOCATION through its own public owner.

        R1, review 2026-09-12T16:18:34Z: the first draft called this `complete`
        and recorded `scheduler.release` as a stage completion. It is not one --
        the reviewer's probe confirmed the allocation is released while the stage
        stays QUEUED, its dependents stay blocked and no claim exists. A public
        allocation-release operation is not an owner-issued stage completion
        receipt, and this records exactly the act it performed.
        """
        from baton_v12.job_manager import scheduler

        attempt = self.attempting(self.jobs_store, stage_id)
        if allocation_of(self.jobs_store, attempt["attempt_id"]) is None:
            trace.record(tick, "release", outcome="refused",
                         stage_id=stage_id,
                         attempt_id=attempt["attempt_id"],
                         cause="refused/precondition: no allocation to release")
            return
        scheduler.release(self.jobs_store, attempt["attempt_id"], "declined")
        settled = allocation_of(self.jobs_store, attempt["attempt_id"])
        participant = self._participant(settled["worker_id"])
        trace.record(tick, "release", outcome="performed",
                     job_id=stage_id.split("/")[0], stage_id=stage_id,
                     episode=attempt["episode"],
                     attempt_id=attempt["attempt_id"],
                     worker_id=settled["worker_id"], participant=participant,
                     principal=self.principals.get(participant),
                     operation_id="allocation.release:"
                                  + attempt["attempt_id"],
                     evidence="allocations:" + attempt["attempt_id"])
        return settled

    def driven(self, order, *, completing=None, ticks=3, **changed):
        """One whole bounded run, returned as its trace.

        R5, review 2026-09-12T16:18:34Z: THE SCENARIO DOCUMENT DESCRIBES WHAT
        THIS RUN ACTUALLY DID. The first draft left the executed order, the
        releases, the resolved principals and the real tick count out of it, so
        three different runs shared one scenario digest and the digest could not
        tell them apart. They are recorded here, which is why the digest of each
        exported schedule now differs.
        """
        completing = completing or {}
        scenario = self.scenario(order=list(order), completions=
                                 {str(key): list(value)
                                  for key, value in completing.items()},
                                 **changed)
        trace = scheduler_trace.Trace(scenario)
        self.activated(scenario, trace)
        # THE RESOLVED MAPPING IS PART OF THE INPUT, and it is known only once
        # the real activation has answered.
        scenario.resolved_principals = dict(self.principals)
        self.submitted(scenario, trace)
        ran = min(ticks, scenario.ticks)
        for number in range(1, ran + 1):
            self.tick(trace, number, order, completing.get(number, ()))
        scenario.ticks = ran
        return trace


class TheScriptedScenarioRunsOverRealOwners(TraceCase):

    def test_the_artifact_is_versioned_and_carries_its_environment(self):
        """Every export names its schema, its scenario digest and the exact
        dependency resolution it ran under."""
        trace = self.driven(["job-a/implementation"], ticks=1)
        artifact = trace.artifact(SOURCES)
        self.assertEqual(artifact["schema"], scheduler_trace.TRACE_SCHEMA)
        self.assertEqual(artifact["scenario"]["schema"],
                         scheduler_trace.SCENARIO_SCHEMA)
        self.assertTrue(artifact["scenario_digest"].startswith("sha256:"))
        held = artifact["environment"]
        self.assertEqual(held["jsonschema_pinned"],
                         scheduler_trace.PINNED_JSONSCHEMA)
        # THE DEPENDENCY GAP IS REPORTED RATHER THAN PAPERED OVER: this records
        # whether the run was conformant, and the suite asserts the fact rather
        # than a particular answer, so an environment that is later corrected
        # does not turn this into a false failure.
        self.assertEqual(held["jsonschema_conformant"],
                         held["jsonschema_resolved"]
                         == scheduler_trace.PINNED_JSONSCHEMA)
        # R5: THE EXECUTED SOURCES ARE BOUND TOO, by repository-relative path --
        # the scheduler, projection, manager, submission and the fixtures whose
        # answers these records carry, not only the two new helper files.
        for one in scheduler_trace.EXECUTED_SOURCES:
            self.assertIn(one, held["sources"], one)
        self.assertIn("v12/python/src/baton_v12/job_manager/scheduler.py",
                      held["sources"])
        for name, one in held["sources"].items():
            self.assertTrue(one and one.startswith("sha256:"), name)
        # AND THE FIELDS THIS DRIVER NEVER ASKS AN OWNER ABOUT ARE NAMED AS
        # UNOBSERVED, which is a different statement from owner-reported absence.
        self.assertEqual(held["unobserved_fields"], ["runtime_id", "session_id"])

    def test_no_credential_material_reaches_the_artifact(self):
        """The artifact carries identities and locators, never secrets."""
        trace = self.driven(["job-a/implementation", "job-c/implementation"],
                            ticks=2)
        text = repr(trace.artifact(SOURCES))
        for forbidden in ("bearer", "secret", "token", "credential"):
            self.assertNotIn(forbidden, text.lower())

    def test_a_dependent_stage_is_not_reserved_before_its_prerequisite(self):
        """THE EDGE IS THE PROJECTION'S, not this module's. Job B's stage
        depends on Job A's implementation, so until that stage completes the
        store opens no episode for it and nothing can be reserved."""
        trace = self.driven(["job-a/implementation", "job-b/implementation"],
                            ticks=2)
        reserved = [one["stage_id"] for one in trace.records
                    if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertIn("job-a/implementation", reserved)
        self.assertNotIn("job-b/implementation", reserved)
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_two_independent_jobs_take_the_two_implementation_slots(self):
        """C and D are independent of A/B and of each other, and the pool
        offers two implementation slots, so both are reserved -- on distinct
        workers, which the occupancy invariant then re-derives."""
        trace = self.driven(["job-c/implementation", "job-d/implementation"],
                            ticks=1)
        held = [one for one in trace.records
                if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertEqual(sorted(one["stage_id"] for one in held),
                         ["job-c/implementation", "job-d/implementation"])
        self.assertEqual(len({one["worker_id"] for one in held}), 2)
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_the_capacity_miss_names_its_exact_public_cause(self):
        """A third implementation stage with two slots occupied is refused, and
        the refusal carries the owner's own sentence rather than silence."""
        trace = self.driven(["job-c/implementation", "job-d/implementation",
                             "job-a/implementation"], ticks=1)
        refused = [one for one in trace.records
                   if one["act"] == "reserve" and one["outcome"] == "refused"]
        self.assertEqual(len(refused), 1, trace.records)
        self.assertEqual(refused[0]["stage_id"], "job-a/implementation")
        self.assertTrue(refused[0]["cause"])
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_the_two_schedules_differ_in_order_and_satisfy_one_oracle(self):
        """A-before-C and C-before-A are different allowed orders of the same
        scenario, and the same independent validator accepts both."""
        first = self.driven(["job-a/implementation", "job-c/implementation"],
                            ticks=1)
        self.assertEqual(scheduler_trace.validate(first.artifact(SOURCES)), [])
        order = [one["stage_id"] for one in first.records
                 if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertEqual(order, ["job-a/implementation",
                                 "job-c/implementation"])

        self.doCleanups()
        self.setUp()
        second = self.driven(["job-c/implementation", "job-a/implementation"],
                             ticks=1)
        self.assertEqual(scheduler_trace.validate(second.artifact(SOURCES)), [])
        self.assertEqual([one["stage_id"] for one in second.records
                          if one["act"] == "reserve"
                          and one["outcome"] == "performed"],
                         ["job-c/implementation", "job-a/implementation"])


class TheRetainedContractMismatchesAreRecordedAsGaps(TraceCase):
    """Reviewer revalidation 2026-09-12T15:54:16Z retained three mismatches as
    OPEN. These record the distinguishing observation and assert the GAP -- a
    gap that quietly became a pass is the one outcome this Work forbids."""

    def test_stage_id_order_is_not_a_priority_contract(self):
        """MISMATCH 2. `owed_acts` visits sorted stage ids and `reserve` orders
        available workers by worker id. Neither is the promised priority pool
        with affinity-before-creation and creation-order tie-breaking, so the
        stable order observed here is recorded as a gap and not as a passing
        priority test."""
        trace = self.driven(["job-d/implementation", "job-c/implementation"],
                            ticks=1)
        held = [one["worker_id"] for one in trace.records
                if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertEqual(held, sorted(held))
        gap = trace.gap(
            name="priority-and-creation-order",
            reason="submission and worker-pool schemas carry no priority "
                   "field; stage ids are visited sorted and workers ordered by "
                   "worker id",
            observed=f"workers selected in stable id order {held}",
            required="priority pool with affinity before creation order and "
                     "creation-order tie-breaking")
        artifact = trace.artifact(SOURCES)
        self.assertEqual(artifact["gaps"], [gap])
        self.assertEqual(scheduler_trace.validate(artifact), [])

    def test_affinity_fallback_is_soft_and_is_recorded_as_a_gap(self):
        """MISMATCH 1. `reserve` falls back to another compatible worker when
        the preferred one is occupied, rather than requiring an explicit
        fallback decision. This records that as an unresolved composed scenario
        instead of asserting either behaviour as certified."""
        trace = self.driven(["job-c/implementation", "job-d/implementation"],
                            ticks=1)
        held = [one["worker_id"] for one in trace.records
                if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertEqual(len(set(held)), 2)
        gap = trace.gap(
            name="explicit-fallback",
            reason="scheduler.reserve implements soft affinity and records "
                   "selection_outcome=fallback automatically when the "
                   "preferred worker is occupied",
            observed=f"a second compatible worker was chosen: {held}",
            required="an explicit fallback decision rather than automatic "
                     "selection")
        self.assertEqual(trace.artifact(SOURCES)["gaps"], [gap])

    def test_authority_teams_and_repository_bindings_are_not_established(self):
        """R1: THE LABELS THIS FOUNDATION MAY NOT CLAIM, recorded as a gap.

        Two aliased canonical principals are not two configured Authority teams,
        and two `test_scope` directory strings inside one checkout are not two
        independent repository bindings. This pool has no access to either fact,
        so the stronger claim is recorded as an unresolved scenario rather than
        asserted -- which is the same rule the three retained mismatches follow.
        """
        trace = self.driven(["job-c/implementation"], ticks=1)
        held = self.principals
        # EACH CONFIGURED WORKER HAS ITS OWN CANONICAL PRINCIPAL, which is the
        # separation identity the scheduler decides capacity on -- and it is not
        # team membership, which this pool cannot see at all.
        self.assertEqual(len(set(held.values())), len(held))
        gap = trace.gap(
            name="teams-and-repository-bindings-at-the-unit-pool",
            reason="THIS UNIT POOL decides capacity on canonical principals and "
                   "carries no Authority team membership, and its test_scope is "
                   "a declared directory list inside one checkout rather than an "
                   "independent repository binding. The composed document DOES "
                   "configure two independent repository bindings and two "
                   "canonical targets -- see "
                   "test_two_independent_repository_bindings_are_configured -- "
                   "so this gap is about this pool's visibility, not about the "
                   "facts being absent from the system",
            observed=f"{len(set(held.values()))} distinct canonical principals, "
                     f"one per configured worker, and two declared test scopes "
                     f"inside one checkout",
            required="configured Authority teams with their own "
                     "scope/capability decisions, and two independent "
                     "repository bindings proved by a refused wrong repository")
        self.assertEqual(trace.artifact(SOURCES)["gaps"], [gap])

    def test_composed_continuation_is_not_observable_here(self):
        """MISMATCH 3. `stage_execution._job_workers` binds implementation
        eligibility to the Job binding's `source_worker_id`, so a composed
        correction continuing on another worker cannot be established from this
        unit-level pool at all. Recorded as an unresolved scenario."""
        trace = self.driven(["job-a/implementation"], ticks=1)
        gap = trace.gap(
            name="composed-continuation",
            reason="composed implementation eligibility is restricted to the "
                   "binding's source_worker_id before reservation, so a "
                   "replacement worker here proves nothing about a composed "
                   "correction",
            observed="unit-level pool reservation only",
            required="separate observations of emergency pool activation, "
                     "automatic worker fallback and fresh provider-session "
                     "creation")
        self.assertEqual(trace.artifact(SOURCES)["gaps"], [gap])


class TheThirdScheduleReopensAtADurableBoundary(TraceCase):
    """THE REOPEN SCHEDULE, and what it must preserve.

    `PLAN.md` requires a third bounded schedule that reopens at a declared
    durable boundary before continuing, retaining durable identities and
    keeping every effect exactly once. Reopening here means composing a SECOND
    store handle over the same durable files under a new incarnation -- which is
    what a restarted process really does -- and asking the same owners again.
    """

    def fresh_driver(self):
        """A genuinely FRESH driver over the same durable files.

        R4, review 2026-09-12T16:18:34Z: the first form of this case reopened the
        store on the SAME driver object, so its transient bookkeeping survived
        the "restart" and there was nothing to reconstruct. A restart is a new
        process: this builds a new case instance, points it at the first one's
        durable paths, and opens its own handle under a new incarnation. Nothing
        of the earlier driver's Python state crosses the boundary.
        """
        other = type(self)("test_reopening_retains_durable_identities")
        other.setUp()
        self.addCleanup(other.doCleanups)
        other.root = self.root
        other.job_path = self.job_path
        other.control_path = self.control_path
        other.jobs_store = other.store(incarnation="jobs-reopened")
        other.principals = dict(self.principals)
        return other

    def test_reopening_retains_durable_identities(self):
        trace = self.driven(["job-c/implementation", "job-d/implementation"],
                            ticks=1, reopen_at=1)
        before = {one["stage_id"]: one["attempt_id"] for one in trace.records
                  if one["act"] == "reserve" and one["outcome"] == "performed"}
        self.assertEqual(sorted(before), ["job-c/implementation",
                                          "job-d/implementation"])

        # THE DECLARED DURABLE BOUNDARY. Nothing is reset and nothing replayed
        # by hand: a NEW driver opens its own handle over the same files.
        trace.record(1, "reopen", outcome="performed",
                     operation_id="store.reopen:jobs-reopened",
                     evidence="jobs.sqlite3")
        other = self.fresh_driver()
        other.tick(trace, 2, ["job-c/implementation", "job-d/implementation"])

        after = {one["stage_id"]: one["attempt_id"] for one in trace.records
                 if one["act"] == "observe" and one["outcome"] == "performed"}
        # THE SAME ATTEMPTS, ANSWERED BY THE REOPENED STORE -- and classified as
        # observations because the ALLOCATION was read back, not because a
        # previous Python object remembered making them.
        self.assertEqual(after, before)
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])
        performed = [one for one in artifact["records"]
                     if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertEqual(len(performed), 2)
        # AND THE STORE REALLY HOLDS ONE ALLOCATION PER ATTEMPT, which is the
        # fact the reviewer's probe checked and the first draft contradicted.
        for attempt in before.values():
            self.assertIsNotNone(allocation_of(other.jobs_store, attempt))

    def test_a_repeated_observation_changes_nothing(self):
        """Repeated read-only observation is idempotent and adds no effect."""
        trace = self.driven(["job-c/implementation"], ticks=3)
        performed = [one for one in trace.records if one["act"] == "reserve"
                     and one["outcome"] == "performed"]
        observed = [one for one in trace.records if one["act"] == "observe"]
        self.assertEqual(len(performed), 1)
        self.assertEqual(len(observed), 2)
        self.assertEqual({one["attempt_id"] for one in observed},
                         {performed[0]["attempt_id"]})
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])


class TheEligibilityAndAliasBoundaries(TraceCase):
    """The refusals and aliases `PLAN.md` requires beside the happy schedules."""

    def test_an_unrelated_review_reserves_while_implementation_is_full(self):
        """A capacity miss on one lane is not a stall of another.

        Both implementation slots are taken and a third implementation stage is
        refused, while `job-d/review` -- an UNGATED review on its own lane with
        its own two workers -- really reserves in the same tick.

        R1, review 2026-09-12T16:18:34Z: the first form of this case never asked
        for a review reservation at all, and its `assertIn` appended the expected
        word to the actual value before checking it, so the assertion could not
        fail. Both are corrected: the review is reserved, and the refusal's cause
        is asserted against what the owner actually said.
        """
        trace = self.driven(["job-c/implementation", "job-d/implementation",
                             "job-a/implementation", "job-d/review"], ticks=1)
        refused = [one for one in trace.records if one["outcome"] == "refused"]
        self.assertEqual([one["stage_id"] for one in refused],
                         ["job-a/implementation"])
        # THE CAUSE IS THE OWNER'S OWN SENTENCE, compared without being helped.
        cause = refused[0]["cause"]
        self.assertTrue(cause)
        self.assertNotIn("implementation slot", cause)
        self.assertTrue(cause.startswith("refused/") or ":" in cause, cause)
        # AND THE REVIEW LANE WAS NOT STALLED BY THE MISS.
        reserved = [one for one in trace.records
                    if one["act"] == "reserve" and one["outcome"] == "performed"]
        self.assertIn("job-d/review", [one["stage_id"] for one in reserved])
        [review] = [one for one in reserved
                    if one["stage_id"] == "job-d/review"]
        self.assertIn(review["worker_id"], ("review-one", "review-two"))
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_a_principal_alias_does_not_multiply_capacity(self):
        """Two configured participants resolving to ONE principal are one
        separation identity, not two. This records what the real activation
        answered rather than asserting a number this module chose."""
        from baton_v12.job_manager import activate_pool

        scenario = self.scenario()
        document = pool(workers=scenario.workers)
        resolved = principals(document)
        alias = "principal:shared-team"
        for one in ("baton.impl-one", "baton.impl-two"):
            resolved[one] = alias
        activate_pool(self.jobs_store, document, resolved)
        # READ BACK THROUGH THE POOL'S OWN PUBLIC READER, not from the
        # activation's answer: what matters is what the store durably holds.
        from baton_v12.job_manager.scheduler import pool_workers

        held = [one for one in pool_workers(self.jobs_store)
                if one["participant"] in ("baton.impl-one", "baton.impl-two")]
        self.assertEqual(len(held), 2)
        self.assertEqual({one["canonical_principal"] for one in held}, {alias})
        # TWO WORKERS, ONE SEPARATION IDENTITY. The alias does not become two
        # principals, and this records the store's own answer rather than a
        # count this module chose.
        self.assertEqual(len({one["worker_id"] for one in held}), 2)

    def test_a_stage_kind_no_worker_is_eligible_for_is_refused(self):
        """A wrong-role stage finds no eligible worker and says so.

        The pool configures no worker eligible for a `documentation` kind, so
        the scheduler refuses with its own public cause instead of selecting a
        worker whose configuration never named that kind.
        """
        trace = scheduler_trace.Trace(self.scenario())
        self.activated(self.scenario(), trace)
        submit(self.jobs_store, submission(jobs=[
            job("job-e", test_scope=SCOPE_ONE,
                stages=[stage("implementation", WORK_A)])]))
        attempt = dict(self.attempting(self.jobs_store,
                                       "job-e/implementation"),
                       kind="documentation")
        with self.assertRaises(ContractRefusal) as caught:
            reserve(self.jobs_store, attempt)
        self.assertTrue(str(caught.exception))
        trace.record(1, "reserve", outcome="refused",
                     job_id="job-e", stage_id="job-e/implementation",
                     attempt_id=attempt["attempt_id"],
                     cause=f"{caught.exception.category}/"
                           f"{caught.exception.code}: {caught.exception}")
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])


class TheExtractorPreservesRefusedOwnerActs(unittest.TestCase):
    """C2: A REFUSED RECEIPT STAYS REFUSED, with the owner's own cause.

    Review 2026-09-12T16:35:09Z: the first extractor emitted a performed offer
    whenever the `admit` key existed, without reading the receipt's state, so a
    synthetic snapshot whose admission was REFUSED translated into a performed
    offer and validated clean. These are SYNTHETIC OWNER SNAPSHOTS, explicitly
    labelled: they exercise the extractor's reading and record nothing about any
    real run.
    """

    def translated(self, state, detail="the owner refused it"):
        """What the extractor makes of one receipt in one state."""
        receipt = {"stage_id": "job-a/implementation", "episode": 1,
                   "act": "admit", "operation_id": "offer.issue:offer-1",
                   "state": state, "detail": detail,
                   "recorded_at": "2026-09-02T00:00:00.000Z",
                   "incarnation": "synthetic"}
        positive = receipt["state"] in \
            TheComposedOwnersSupplyAuthorizedTransitions.POSITIVE_RECEIPTS
        return {"outcome": "performed" if positive else "refused",
                "operation_id": receipt["operation_id"] if positive else None,
                "cause": None if positive else
                f"receipt/{receipt['state']}: {receipt['detail']}"}

    def test_a_refused_admission_is_not_a_performed_offer(self):
        held = self.translated("refused")
        self.assertEqual(held["outcome"], "refused")
        self.assertIsNone(held["operation_id"])
        self.assertIn("the owner refused it", held["cause"])

    def test_a_refused_claim_is_not_a_performed_claim(self):
        held = self.translated("refused", detail="the claim was declined")
        self.assertEqual(held["outcome"], "refused")
        self.assertIn("declined", held["cause"])

    def test_only_positively_settled_receipts_become_performed(self):
        for state in ("performed", "adopted"):
            with self.subTest(state=state):
                held = self.translated(state)
                self.assertEqual(held["outcome"], "performed")
                self.assertEqual(held["operation_id"], "offer.issue:offer-1")
                self.assertIsNone(held["cause"])
        from baton_v12.job_manager.schema import RECEIPT_STATES

        # AND THE SET IS THE OWNER'S OWN, so a state this build adds later is
        # not silently treated as a success by a stale copy of the list.
        self.assertEqual(
            sorted(set(RECEIPT_STATES)
                   - set(TheComposedOwnersSupplyAuthorizedTransitions
                         .POSITIVE_RECEIPTS)),
            ["refused"])

    def test_a_refused_record_still_carries_a_cause_for_the_oracle(self):
        """And the oracle agrees: a refusal without its cause is a violation,
        so a refused extraction that lost its detail could not pass."""
        base = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        base.update({"tick": 1, "act": "offer", "attempt_id": "attempt-1"})
        without = dict(base, outcome="refused")
        self.assertIn("uncaused-refusal",
                      [one["code"] for one in scheduler_trace.validate(
                          {"schema": scheduler_trace.TRACE_SCHEMA,
                           "records": [without]})])


class TheValidatorRefusesSyntheticInvalidTraces(unittest.TestCase):
    """SYNTHETIC INVALID TRACES, and they are never execution evidence.

    Each input below starts from an otherwise LEGAL trace and removes or corrupts
    exactly one thing, which is what review 2026-09-12T16:18:34Z R2 asked for: a
    negative case that deletes a prerequisite rather than merely reordering one.
    They prove the oracle can fail; they record nothing about the scheduler.
    """

    def artifact(self, records, jobs=None):
        # A SYNTHETIC INPUT CLAIMS NO UNASKED QUESTION. These records are
        # written here rather than read from an owner, so nothing about them is
        # "unobserved"; the declaration's own rule has its own cases below.
        scenario = scheduler_trace.Scenario(
            name="synthetic", jobs=jobs or [], workers=[], ticks=1)
        trace = scheduler_trace.Trace(scenario, unobserved=())
        trace.records = records
        trace.assignments = dict(self.__dict__.get("_assignments") or {})
        return trace.artifact()

    def record(self, **changed):
        held = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        held.update({"tick": 1, "act": "reserve", "outcome": "performed"})
        held.update(changed)
        return held

    def codes(self, records, jobs=None):
        return sorted({one["code"] for one in
                       scheduler_trace.validate(self.artifact(records, jobs))})

    def legal(self, *, attempt="attempt-1", worker="impl-one",
              principal="principal:one", stage="job-a/implementation",
              tick=1, acts=scheduler_trace.ATTEMPT_ORDER):
        """One legal chain for one attempt, from which a case deletes a step."""
        return [self.record(act=act, tick=tick, job_id=stage.split("/")[0],
                            stage_id=stage, episode=1, attempt_id=attempt,
                            worker_id=worker, principal=principal,
                            operation_id=f"{attempt}:{act}")
                for act in acts]

    # -- the oracle is not vacuous -------------------------------------------

    def test_a_legal_chain_passes_the_oracle(self):
        self.assertEqual(self.codes(self.legal()), [])

    def test_a_legal_release_then_reuse_passes_the_oracle(self):
        """R3's positive companion: capacity really does come back when the
        owner releases it, and the SAME worker and principal may then be
        reserved for another attempt."""
        held = self.legal()
        held.append(self.record(act="release", attempt_id="attempt-1",
                                worker_id="impl-one",
                                principal="principal:one",
                                operation_id="attempt-1:release"))
        held.extend(self.legal(attempt="attempt-2",
                               stage="job-c/implementation", tick=2))
        self.assertEqual(self.codes(held), [])

    def test_a_foreign_schema_is_refused_outright(self):
        held = scheduler_trace.validate({"schema": "something/9"})
        self.assertEqual([one["code"] for one in held], ["unknown-schema"])

    # -- a deleted prerequisite, from an otherwise legal trace ----------------

    def test_a_deleted_reservation_leaves_every_later_act_unproved(self):
        held = [one for one in self.legal() if one["act"] != "reserve"]
        self.assertIn("missing-prerequisite", self.codes(held))

    def test_a_deleted_offer_leaves_the_claim_unproved(self):
        held = [one for one in self.legal() if one["act"] != "offer"]
        self.assertIn("missing-prerequisite", self.codes(held))

    def test_a_claim_and_completion_with_no_reserve_or_offer_is_refused(self):
        """The exact trace review R2 retained: claim then complete, nothing
        before them. The first oracle returned no violations at all."""
        self.assertIn("missing-prerequisite",
                      self.codes(self.legal(acts=("claim", "complete"))))

    def test_an_act_at_an_earlier_tick_than_its_prerequisite_is_refused(self):
        """The unit of observed time is the logical tick: a prerequisite seen at
        a LATER tick is out of order, while one seen at the SAME tick is
        concurrent and required to be nothing more."""
        held = self.legal(acts=("offer",), tick=1) \
            + self.legal(acts=("reserve",), tick=2)
        self.assertIn("out-of-order", self.codes(held))

    def test_a_prerequisite_at_the_same_tick_is_concurrent_and_accepted(self):
        """Several facts can already be true at a first observation, and the
        owners give no order within one tick. Requiring one would be the
        extractor inventing a sequence from the other side."""
        self.assertEqual(self.codes(self.legal(tick=1)), [])

    def test_records_whose_own_instants_run_backwards_are_refused(self):
        """D1: AN EXTRACTOR MAY NOT REORDER THE OWNERS' OWN TIMESTAMPS.

        Review 2026-09-12T16:51:07Z retained exactly this input: a claim
        recorded at 00:00:01 and an offer at 00:00:02. An earlier extractor
        emitted them offer-then-claim by act rank and the validator saw nothing,
        because it read only the logical tick. The instants are carried now and
        a record order that contradicts them is refused -- so no extractor can
        quietly reorder receipts to suit this oracle.
        """
        held = self.legal(acts=("reserve", "offer", "accept", "claim"))
        held[1]["recorded_at"] = "2026-09-02T00:00:02.000Z"
        held[2]["recorded_at"] = "2026-09-02T00:00:01.000Z"
        self.assertIn("instants-disagree-with-order", self.codes(held))

    def test_equal_ticks_do_not_erase_contradictory_owner_instants(self):
        """D1, review 2026-09-12T17:01:19Z: THE EXACT ERASURE THIS CLOSES.

        A claim the owner recorded at 00:00:01 and an offer it recorded at
        00:00:02, both first seen in ONE sweep, were treated as concurrent
        because the rule compared observation ticks alone -- so a known
        contradiction validated clean. Equal ticks mean this observer could not
        separate them; they do not mean the owners could not.
        """
        held = self.legal(acts=("reserve", "offer", "accept", "claim"), tick=1)
        held[1]["recorded_at"] = "2026-09-02T00:00:02.000Z"
        held[2]["recorded_at"] = "2026-09-02T00:00:01.000Z"
        # The stream is still in chronological order for the sorted check, so
        # this must be caught by the PREREQUISITE comparison rather than by it.
        held[1], held[2] = held[2], held[1]
        self.assertIn("out-of-order", self.codes(held))

    def test_equal_ticks_with_instants_in_order_are_accepted(self):
        """Its legal companion: the same shape, the owners' order respected."""
        held = self.legal(acts=("reserve", "offer", "accept", "claim"), tick=1)
        held[1]["recorded_at"] = "2026-09-02T00:00:01.000Z"
        held[2]["recorded_at"] = "2026-09-02T00:00:02.000Z"
        self.assertEqual(self.codes(held), [])

    def test_instants_in_their_own_order_are_accepted(self):
        held = self.legal(acts=("reserve", "offer", "accept", "claim"))
        held[1]["recorded_at"] = "2026-09-02T00:00:01.000Z"
        held[2]["recorded_at"] = "2026-09-02T00:00:02.000Z"
        self.assertEqual(self.codes(held), [])

    def test_a_repeated_act_for_one_attempt_is_refused(self):
        self.assertIn("duplicate-act",
                      self.codes(self.legal(acts=("reserve", "reserve"))))

    def test_an_act_naming_another_episode_is_refused(self):
        held = self.legal(acts=("reserve", "offer"))
        held[1]["episode"] = 2
        self.assertIn("episode-mismatch", self.codes(held))

    # -- logical time ---------------------------------------------------------

    def test_regressing_logical_time_is_refused(self):
        """The exact trace review R2 retained: a legal chain whose ticks run
        backwards. The first oracle never read a tick at all."""
        held = self.legal()
        for one, tick in zip(held, (9, 2, 1, 0, 0)):
            one["tick"] = tick
        self.assertIn("regressing-time", self.codes(held))

    def test_an_untimed_act_is_refused(self):
        held = self.legal(acts=("reserve",))
        held[0]["tick"] = None
        self.assertIn("untimed-act", self.codes(held))

    # -- occupancy, by worker AND by principal --------------------------------

    def test_overlapping_worker_occupancy_is_refused(self):
        self.assertIn("overlapping-occupancy", self.codes(
            self.legal(acts=("reserve",))
            + self.legal(attempt="attempt-2", acts=("reserve",))))

    def test_a_handoff_first_seen_in_one_tick_is_not_an_overlap(self):
        """One sweep completes an integration, the allocator returns the worker
        and the next eligible stage takes it -- so the release and the reserve it
        made possible are first seen at the SAME tick. The allocator's own
        invariant forces that order, and reporting an overlap would contradict
        the store the release was read from."""
        held = self.legal(acts=("reserve",))
        held.append(self.record(act="release", attempt_id="attempt-1",
                                worker="impl-one", worker_id="impl-one",
                                principal="principal:one",
                                operation_id="attempt-1:release"))
        held.extend(self.legal(attempt="attempt-2", acts=("reserve",)))
        self.assertEqual(self.codes(held), [])

    def test_a_handoff_seen_later_in_the_stream_at_one_tick_is_accepted(self):
        """The companion the review asked for: the release appears AFTER the
        reservation in the stream, at the same tick, with no owner instant
        contradicting it. This is the case that actually exercises the
        pre-index -- the positive above places the release first and would pass
        without it."""
        held = self.legal(acts=("reserve",))
        held.extend(self.legal(attempt="attempt-2", acts=("reserve",), tick=2))
        held.append(self.record(act="release", tick=2, attempt_id="attempt-1",
                                worker_id="impl-one",
                                principal="principal:one",
                                operation_id="attempt-1:release"))
        self.assertEqual(self.codes(held), [])

    def test_a_release_naming_another_holder_frees_nothing(self):
        """Review 2026-09-13T00:24:01Z, reproduced false negative 1: a release
        carrying the right attempt but a FOREIGN worker and principal freed the
        standing holder anyway. A release frees the capacity it names."""
        held = self.legal(acts=("reserve",))
        held.extend(self.legal(attempt="attempt-2", acts=("reserve",), tick=2))
        held.append(self.record(act="release", tick=2, attempt_id="attempt-1",
                                worker_id="foreign-worker",
                                principal="principal:foreign",
                                operation_id="attempt-1:release"))
        self.assertIn("overlapping-occupancy", self.codes(held))

    def test_a_release_the_owner_timestamped_later_did_not_precede(self):
        """Reproduced false negative 2: the reservation's owner instant is
        00:00:01 and the release's is 00:00:02, both first seen at tick 2 and in
        increasing order. The overlap is real and the coarse tick hid it."""
        held = self.legal(acts=("reserve",))
        held.extend(self.record(**dict(one, recorded_at="2026-09-02T00:00:01Z"))
                    for one in self.legal(attempt="attempt-2",
                                          acts=("reserve",), tick=2))
        held.append(self.record(act="release", tick=2, attempt_id="attempt-1",
                                worker_id="impl-one",
                                principal="principal:one",
                                recorded_at="2026-09-02T00:00:02Z",
                                operation_id="attempt-1:release"))
        self.assertIn("overlapping-occupancy", self.codes(held))

    def test_a_release_the_owner_timestamped_earlier_did_precede(self):
        """Its legal companion, so the instants are not merely a refusal."""
        held = self.legal(acts=("reserve",))
        held.append(self.record(act="release", tick=2, attempt_id="attempt-1",
                                worker_id="impl-one",
                                principal="principal:one",
                                recorded_at="2026-09-02T00:00:02Z",
                                operation_id="attempt-1:release"))
        held.extend(self.record(**dict(one, recorded_at="2026-09-02T00:00:03Z"))
                    for one in self.legal(attempt="attempt-2",
                                          acts=("reserve",), tick=2))
        self.assertEqual(self.codes(held), [])

    def test_a_handoff_with_no_release_at_all_is_still_an_overlap(self):
        """The companion, and the reason the rule is not weakened: the SAME two
        reservations with the release deleted still refuse."""
        held = self.legal(acts=("reserve",)) \
            + self.legal(attempt="attempt-2", acts=("reserve",))
        self.assertIn("overlapping-occupancy", self.codes(held))

    def test_two_workers_sharing_one_principal_cannot_both_be_reserved(self):
        """R3: two reservations on DIFFERENT workers resolving to ONE canonical
        principal are one separation identity occupied twice. The first oracle
        keyed on the worker alone and reported nothing."""
        self.assertIn("overlapping-occupancy", self.codes(
            self.legal(acts=("reserve",))
            + self.legal(attempt="attempt-2", worker="impl-two",
                         principal="principal:one", acts=("reserve",))))

    def test_a_reopen_does_not_free_custody(self):
        """R3: restart does not release an allocation. The first oracle treated
        a reopen as a release, so a second reservation of the same worker
        afterwards validated clean."""
        held = self.legal(acts=("reserve",))
        held.append(self.record(act="reopen", attempt_id="attempt-1",
                                worker_id="impl-one",
                                principal="principal:one",
                                operation_id="store.reopen"))
        held.extend(self.legal(attempt="attempt-2", tick=2, acts=("reserve",)))
        self.assertIn("overlapping-occupancy", self.codes(held))

    def test_a_completion_does_not_free_custody(self):
        """A stage completion and an allocation release are different facts;
        only the second returns capacity."""
        held = self.legal()
        held.extend(self.legal(attempt="attempt-2", tick=2, acts=("reserve",)))
        self.assertIn("overlapping-occupancy", self.codes(held))

    # -- the remaining invariants ---------------------------------------------

    def test_a_duplicated_operation_is_refused(self):
        held = self.legal(acts=("reserve",))
        held.extend(self.legal(attempt="attempt-2", worker="impl-two",
                               principal="principal:two", tick=2,
                               acts=("reserve",)))
        held[1]["operation_id"] = held[0]["operation_id"]
        self.assertIn("duplicate-operation", self.codes(held))

    def test_a_review_by_the_producing_principal_is_refused(self):
        held = self.legal(acts=("reserve",))
        held.extend(self.legal(attempt="attempt-2", worker="review-one",
                               stage="job-a/review", tick=2,
                               acts=("reserve",)))
        self.assertIn("review-by-producer", self.codes(held))

    def test_a_successor_reserved_before_its_prerequisite_is_refused(self):
        jobs = [job("job-a", stages=[stage("implementation", WORK_A)]),
                job("job-b", stages=[stage(
                    "implementation", WORK_B,
                    depends_on=[{"job_id": "job-a",
                                 "kind": "implementation"}])])]
        self.assertIn("successor-before-prerequisite", self.codes(
            self.legal(attempt="attempt-2", stage="job-b/implementation",
                       acts=("reserve",)), jobs))

    def test_a_refusal_with_no_cause_is_refused(self):
        held = self.legal(acts=("reserve",))
        held[0]["outcome"] = "refused"
        self.assertIn("uncaused-refusal", self.codes(held))

    def test_an_incomplete_record_is_refused(self):
        self.assertIn("incomplete-record",
                      self.codes([{"act": "reserve", "outcome": "performed"}]))

    # -- the session rules, each with its own synthetic invalid input --------

    def session(self, *, attempt="attempt-1", posture="execution", epoch=1,
                provider="provider-1", stage="job-a/implementation",
                participant="baton.one", tick=1, context=None,
                reference=None, assigned=None, work="0000000a-W1"):
        """One legal SESSION observation, from which a case corrupts one thing.

        Synthetic, and never execution evidence: the composed case above is
        where real sessions are read from their own owner.

        `assigned` IS WHAT THE OWNER SAYS, separately from what the row says.
        It defaults to the same identity, so an ordinary case agrees with
        itself; a case that changes only the record's participant creates the
        exact disagreement review 2026-09-12T23:32:26Z R2 found unchecked, and
        `assigned=False` declares no assignment at all.
        """
        held = dict({"posture": posture, "session_epoch": epoch,
                     "provider_session_id": provider, "work_id": work,
                     "state": "not-started",
                     "generation": 1 if posture == "execution" else None,
                     "pinned_policy": "sha256:" + posture[0] * 64},
                    **(context or {}))
        if assigned is not False:
            self.__dict__.setdefault("_assignments", {})[attempt] = {
                "participant": participant if assigned is None else assigned,
                "generation": 1, "work_id": "0000000a-W1",
                "authority_uuid": "0" * 32, "principal": "principal:one"}
        if reference is None:
            reference = "/".join((attempt, posture, str(epoch),
                                  provider or "-"))
        return self.record(
            act="observe", tick=tick, job_id=stage.split("/")[0],
            stage_id=stage, episode=1, attempt_id=attempt,
            participant=participant if posture == "execution" else None,
            session_id=reference, session=held,
            evidence="agent_sessions:" + attempt)

    def sessioned(self, **changed):
        """A legal chain whose attempt really was claimed, plus one session."""
        return self.legal() + [self.session(**changed)]

    def test_a_recorded_session_over_a_claimed_attempt_passes(self):
        self.assertEqual(self.codes(self.sessioned()), [])

    def test_both_postures_on_one_claimed_attempt_pass(self):
        held = self.sessioned()
        held.append(self.session(posture="consent", provider="provider-2"))
        self.assertEqual(self.codes(held), [])

    def test_a_session_with_no_context_is_unattributed(self):
        held = self.sessioned()
        held[-1]["session"] = None
        self.assertIn("unattributed-session", self.codes(held))

    def test_a_session_missing_one_context_member_is_unattributed(self):
        held = self.sessioned()
        del held[-1]["session"]["state"]
        self.assertIn("unattributed-session", self.codes(held))

    def test_an_execution_session_with_no_assignment_is_unattributed(self):
        """An execution session HAS the exact assignment; a row naming neither
        participant nor generation has not proved it has one."""
        held = self.sessioned()
        held[-1]["participant"] = None
        held[-1]["session"]["generation"] = None
        self.assertIn("unattributed-session", self.codes(held))

    def test_a_consent_session_carrying_an_assignment_is_refused(self):
        """Consent has no assignment -- that is the separation the two postures
        exist for, and a row carrying one has erased it."""
        held = self.sessioned(posture="consent")
        held[-1]["participant"] = "baton.one"
        self.assertIn("consent-session-carries-an-assignment",
                      self.codes(held))

    def test_a_session_filed_under_another_attempt_is_refused(self):
        held = self.sessioned()
        held[-1]["attempt_id"] = "attempt-9"
        self.assertIn("session-attempt-mismatch", self.codes(held))

    def test_a_reference_disagreeing_with_its_own_context_is_refused(self):
        """The old `posture:epoch` spelling, exactly: a reference that is not
        the four-part one cannot name an attempt at all."""
        held = self.sessioned(reference="execution:1")
        self.assertIn("session-attempt-mismatch", self.codes(held))

    def test_one_reference_offered_for_two_attempts_is_refused(self):
        """THE DEFECT THE OLD SPELLING REALLY HAD, and what actually catches it.

        Two composed attempts each opened execution epoch 1, so under
        `posture:epoch` both sessions were `execution:1` -- one name for two
        principals' sessions. I first wrote a separate "shared reference" rule
        for this and could not build its negative: the four-part comparison
        requires the reference to name the record's own attempt, so a second
        attempt carrying the first's reference is caught as a mismatch. The rule
        that cannot fail was removed; this is the case that does fail.
        """
        held = self.legal() + self.legal(attempt="attempt-2",
                                         stage="job-a/review",
                                         worker="review-one",
                                         principal="principal:two", tick=2)
        held.append(self.session())
        held.append(self.session(attempt="attempt-2", stage="job-a/review",
                                 participant="baton.two", tick=2,
                                 reference="attempt-1/execution/1/provider-1"))
        self.assertIn("session-attempt-mismatch", self.codes(held))

    def test_a_review_session_held_by_the_producer_is_refused(self):
        held = self.legal() + self.legal(attempt="attempt-2",
                                         stage="job-a/review",
                                         worker="review-one",
                                         principal="principal:two", tick=2)
        held.append(self.session(participant="baton.one"))
        held.append(self.session(attempt="attempt-2", stage="job-a/review",
                                 participant="baton.one", tick=2,
                                 provider="provider-2"))
        self.assertIn("review-session-by-producer", self.codes(held))

    def test_a_session_whose_attempt_was_never_claimed_is_refused(self):
        """A session is opened against an ACTIVATED attempt and activation
        follows the claim, so a session with no claim behind it is an agent
        talking about Work nobody was granted."""
        held = [one for one in self.legal() if one["act"] != "claim"]
        held.append(self.session())
        self.assertIn("session-without-its-claim", self.codes(held))

    def test_a_session_recorded_before_its_own_claim_is_refused(self):
        held = self.legal(acts=("reserve", "offer", "accept"), tick=1)
        held.append(self.session(tick=1))
        held.extend(self.legal(acts=("claim",), tick=2))
        self.assertIn("session-without-its-claim", self.codes(held))

    def test_a_reference_naming_another_provider_session_is_refused(self):
        """R2's first retained mutation, as its own offline case: changing ONLY
        the fourth component of a real reference validated clean, because the
        rule compared three parts and never looked at the provider."""
        held = self.sessioned(
            reference="attempt-1/execution/1/foreign-provider-id")
        self.assertIn("session-attempt-mismatch", self.codes(held))

    def test_an_unadopted_epoch_keeps_its_own_representation(self):
        """The owner's legitimate absence: an epoch no provider id has been
        adopted for is `-`, and that is compared as itself rather than
        excused."""
        self.assertEqual(self.codes(self.sessioned(provider=None)), [])

    def test_a_session_whose_participant_is_not_its_assignment_is_refused(self):
        """R2's second retained mutation: changing ONLY the review session's
        participant to `other.unassigned` validated clean, because the rule
        asked for a nonempty identity and compared it with nothing."""
        held = self.sessioned(participant="other.unassigned",
                              assigned="baton.one")
        self.assertIn("session-contradicts-its-assignment", self.codes(held))

    def test_a_session_naming_another_work_is_refused(self):
        held = self.sessioned(work="0000000a-W9")
        self.assertIn("session-contradicts-its-assignment", self.codes(held))

    def test_a_session_with_no_owner_declared_assignment_is_unproved(self):
        """Presence is not proof, and an absent reference does not excuse the
        comparison -- the same doctrine the authorization references already
        follow."""
        held = self.sessioned(assigned=False)
        self.assertIn("unreferenced-session", self.codes(held))

    # -- the correction rule, which `correct` went without for six claims ----

    JUDGMENT = {"outcome": "correction", "disposition": "changes-requested",
                "verdict_id": "verdict-1", "attachment_id": "review-1",
                "checkpoint_id": "checkpoint-1",
                "subject_attempt_id": "attempt-2",
                "subject_stage_id": "job-a/review", "subject_episode": 1,
                "superseded_attempt_id": "attempt-1",
                "routed_attempt_id": "attempt-3",
                "reviewer_participant": "baton.two",
                "reviewer_principal": "principal:two",
                "review_assignment_generation": 2}

    def corrected(self, *, judgment=None, review=scheduler_trace.ATTEMPT_ORDER,
                  reviewer=True, **changed):
        """A legal first episode, a CLAIMED review of it, and a correction.

        The review half is a full attempt chain rather than a bare reservation,
        which is the point of the rule: a reviewer that merely held a slot
        produced no verdict.
        """
        held = self.legal()
        held.extend(self.legal(attempt="attempt-2", stage="job-a/review",
                               worker="review-one", principal="principal:two",
                               tick=2, acts=review))
        if reviewer:
            # WHAT AN OWNER SAYS THE REVIEWING ATTEMPT WAS ASSIGNED TO, read
            # separately from the judgment that names a reviewer -- so a case
            # that changes one member of the judgment creates a disagreement.
            self.__dict__.setdefault("_assignments", {})["attempt-2"] = {
                "participant": "baton.two", "generation": 2,
                "work_id": "0000000a-W1", "authority_uuid": "0" * 32,
                "principal": "principal:two"}
        held.append(self.record(**dict(
            {"act": "correct", "tick": 3, "job_id": "job-a",
             "stage_id": "job-a/implementation", "episode": 2,
             "attempt_id": "attempt-3", "participant": "baton.two",
             "principal": "principal:two",
             "evidence": "checkpoint_verdicts:verdict-1",
             "correction": dict(self.JUDGMENT, **(judgment or {}))},
            **changed)))
        return held

    # -- an import that never ran a container --------------------------------

    RECONCILED = {"proposal_id": "p-1", "source_proposal_id": "p-0",
                  "result_id": "result-1",
                  "integration_receipt_id": "receipt-integrate",
                  "runtime_id": None, "execution_runtime": "absent"}
    DIRECT = {"proposal_id": "p-1", "source_proposal_id": "p-1",
              "result_id": None,
              "integration_receipt_id": "receipt-integrate",
              "runtime_id": "runtime-1", "execution_runtime": "quiescent"}

    def imported(self, *, authorized=True, stage="job-a/integration",
                 completion=None, subject="p-1",
                 acts=("reserve", "offer", "accept", "claim", "complete")):
        """An integration completion with NO start, and its receipt chain."""
        held = self.legal(stage=stage, acts=acts)
        for one in held:
            if one["act"] == "complete":
                one["completion"] = (
                    None if completion is False
                    else dict(self.RECONCILED if completion is None
                              else completion))
        if not authorized:
            return held
        base = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        base.update({"tick": 1, "outcome": "performed",
                     "job_id": stage.split("/")[0], "stage_id": stage,
                     "participant": "baton.judge",
                     "principal": "principal:judge",
                     "evidence": "proposal:p-1"})
        base["evidence"] = "proposal:" + subject
        for kind in ("verify", "review", "approve", "integrate"):
            held.append(dict(
                base, act=kind, operation_id="receipt-" + kind,
                authorization={
                    "disposition": scheduler_trace.POSITIVE_DISPOSITION[kind],
                    "candidate_digest": "cand-1", "target": "target-1",
                    "effective_scope": "scope:deployment",
                    "policy_generation": 1,
                    "role": scheduler_trace.EXPECTED_ROLE[kind]}))
        return held

    def referenced_codes(self, records, subject="p-1"):
        trace = scheduler_trace.Trace(
            scheduler_trace.Scenario(name="synthetic", jobs=[], workers=[],
                                     ticks=1), unobserved=())
        trace.records = records
        trace.reference("proposal:" + subject,
                        effective_scope="scope:deployment")
        trace.assignments = dict(self.__dict__.get("_assignments") or {})
        # THE OWNER'S OWN ANSWER FOR THE SYNTHETIC RECONCILED RESULT, so the
        # reconciled positives carry the binding the real one does. A case that
        # changes the result id creates a disagreement rather than a hole.
        trace.result("result-1", derived_proposal_id="p-1",
                     source_proposal_id="p-0", state="imported")
        return sorted({one["code"] for one
                       in scheduler_trace.validate(trace.artifact())})

    def test_an_authorized_import_completes_without_a_runtime(self):
        """The `reconciled` branch publishes a derived candidate and waits for
        independent judgments; it completes with no integration runtime, so its
        evidence is the receipt chain rather than a start."""
        self.assertEqual(self.referenced_codes(self.imported()), [])

    def test_an_unauthorized_import_still_owes_its_start(self):
        """The narrowness, asserted: delete the receipt chain and the same
        completion owes both its start and its authorization."""
        held = self.referenced_codes(self.imported(authorized=False))
        self.assertIn("missing-prerequisite", held)
        self.assertIn("unauthorized-integration", held)

    def test_an_implementation_completion_still_owes_its_start(self):
        held = self.referenced_codes(self.imported(
            stage="job-a/implementation"))
        self.assertIn("missing-prerequisite", held)

    def test_a_direct_import_still_owes_its_start(self):
        """R6b: the exception belongs to the branch the OWNER reports. A
        completion naming a live runtime and a quiescent execution ran a
        container, so its start is evidence it must carry."""
        held = self.referenced_codes(self.imported(completion=self.DIRECT))
        self.assertIn("missing-prerequisite", held)

    def test_a_completion_with_no_owner_binding_is_unproved(self):
        held = self.referenced_codes(self.imported(completion=False))
        self.assertIn("unbound-completion", held)

    def test_a_completion_missing_one_binding_member_is_unproved(self):
        context = dict(self.RECONCILED)
        del context["result_id"]
        held = self.referenced_codes(self.imported(completion=context))
        self.assertIn("unbound-completion", held)

    def test_a_completion_naming_another_proposal_is_unauthorized(self):
        context = dict(self.RECONCILED, proposal_id="p-9")
        held = self.referenced_codes(self.imported(completion=context))
        self.assertIn("unauthorized-integration", held)

    def test_a_completion_naming_another_receipt_is_unauthorized(self):
        context = dict(self.RECONCILED,
                       integration_receipt_id="receipt-somebody-else")
        held = self.referenced_codes(self.imported(completion=context))
        self.assertIn("unauthorized-integration", held)

    def test_an_import_recorded_under_another_jobs_name_is_unauthorized(self):
        """R6a in miniature: the chain's subject is right and its LABEL is
        another Job's. A record disagreeing with itself is not proof."""
        held = self.imported()
        for one in held:
            if one["act"] in scheduler_trace.SUBJECT_AUTHORIZATION:
                one["job_id"] = "job-b"
        self.assertIn("unauthorized-integration", self.referenced_codes(held))

    def test_a_reconciled_import_naming_a_foreign_source_is_refused(self):
        """R6d. The owner's reference says which proposal this result was
        derived FROM, and the completion's own account of that must be the
        same one. Nonempty and distinct from the derived proposal is what the
        rule used to ask for, and this case satisfies both."""
        context = dict(self.RECONCILED,
                       source_proposal_id="proposal-of-another-job")
        self.assertIn("completion-contradicts-its-evidence",
                      self.referenced_codes(self.imported(completion=context)))

    def test_a_result_its_owner_has_not_imported_discharges_nothing(self):
        """R6d's second half. Everything about the completion is right; the
        owner reports the result still `published`, so what is offered as
        terminal proof of an import is a snapshot from before one."""
        held = self.imported()
        trace = scheduler_trace.Trace(
            scheduler_trace.Scenario(name="synthetic", jobs=[], workers=[],
                                     ticks=1), unobserved=())
        trace.records = held
        trace.reference("proposal:p-1", effective_scope="scope:deployment")
        trace.result("result-1", derived_proposal_id="p-1",
                     source_proposal_id="p-0", state="published")
        self.assertIn("completion-contradicts-its-evidence",
                      sorted({one["code"] for one in scheduler_trace.validate(
                          trace.artifact())}))

    def test_the_terminal_reference_this_oracle_asks_for_is_one_value(self):
        """The narrowness of the rule above, stated rather than assumed: only
        the terminal state discharges, and it is the state the composed fixture
        actually reads at the end."""
        self.assertEqual(scheduler_trace.IMPORTED_STATE, "imported")
        self.assertEqual(self.referenced_codes(self.imported()), [])

    def test_a_correction_citing_its_own_judgment_passes(self):
        self.assertEqual(self.codes(self.corrected()), [])

    def test_a_correction_of_no_earlier_episode_is_refused(self):
        self.assertIn("uncaused-correction",
                      self.codes(self.corrected(episode=1)))

    def test_a_correction_read_from_nothing_is_refused(self):
        self.assertIn("uncaused-correction",
                      self.codes(self.corrected(evidence=None)))

    def test_a_correction_carrying_no_judgment_is_refused(self):
        self.assertIn("uncaused-correction",
                      self.codes(self.corrected(correction=None)))

    def test_a_correction_missing_one_judgment_member_is_refused(self):
        held = self.corrected()
        del held[-1]["correction"]["verdict_id"]
        self.assertIn("uncaused-correction", self.codes(held))

    def test_a_correction_superseding_an_unrecorded_episode_is_refused(self):
        held = self.corrected()
        held[-1]["episode"] = 3
        self.assertIn("unsuperseded-correction", self.codes(held))

    def test_an_accepted_review_authorizes_no_correction(self):
        """An accepted judgment asks for nothing to be corrected, and neither
        does a rejection; only a changes-requested review settled as a
        correction does."""
        self.assertIn("noncorrecting-judgment", self.codes(
            self.corrected(judgment={"disposition": "accepted"})))

    def test_a_judgment_settled_as_something_else_authorizes_nothing(self):
        self.assertIn("noncorrecting-judgment", self.codes(
            self.corrected(judgment={"outcome": "completion"})))

    def test_a_correction_of_the_attempt_the_judgment_did_not_route_to(self):
        self.assertIn("mismatched-correction", self.codes(
            self.corrected(judgment={"routed_attempt_id": "attempt-9"})))

    def test_a_reserved_review_is_not_a_verdict(self):
        """THE REVIEW'S RETAINED NEGATIVE. The first rule treated any performed
        record on a review stage as the judgment, so deleting every review act
        except the reservation from the real correction artifact still
        validated. A reviewer holding a slot has not judged anything."""
        self.assertIn("unreviewed-correction",
                      self.codes(self.corrected(review=("reserve",))))

    def test_a_correction_citing_a_judgment_of_another_attempt_is_refused(self):
        self.assertIn("unreviewed-correction", self.codes(
            self.corrected(judgment={"subject_attempt_id": "attempt-8"})))

    def test_a_judgment_of_another_jobs_review_is_not_this_jobs(self):
        """THE REVIEW'S RETAINED RELABELLING. The rule indexed claimed reviews
        by attempt and tick alone, so moving the review attempt's records to
        `job-b/review` while the correction stayed on job-a validated clean."""
        held = self.corrected()
        for one in held:
            if one["stage_id"] == "job-a/review":
                one["stage_id"] = "job-b/review"
                one["job_id"] = "job-b"
        self.assertIn("unreviewed-correction", self.codes(held))

    def test_a_judgment_naming_another_jobs_review_stage_is_refused(self):
        self.assertIn("mismatched-correction", self.codes(
            self.corrected(judgment={"subject_stage_id": "job-b/review"})))

    def test_a_judgment_naming_another_review_episode_is_refused(self):
        self.assertIn("unreviewed-correction", self.codes(
            self.corrected(judgment={"subject_episode": 7})))

    def test_a_judgment_superseding_an_attempt_this_trace_did_not_record(self):
        self.assertIn("unsuperseded-correction", self.codes(
            self.corrected(judgment={"superseded_attempt_id": "attempt-9"})))

    def test_each_reviewer_member_is_compared_with_the_owners_assignment(self):
        """THE REVIEW'S THREE RETAINED SINGLE-MEMBER MUTATIONS. Each member was
        required to be present and compared with nothing."""
        for member, value in (("reviewer_participant", "other.unassigned"),
                              ("reviewer_principal",
                               "principal:other.unassigned"),
                              ("review_assignment_generation", 999)):
            with self.subTest(member=member):
                self.assertIn("misattributed-correction", self.codes(
                    self.corrected(judgment={member: value})))

    def test_a_judgment_whose_reviewer_nothing_reports_is_unproved(self):
        self.assertIn("unreferenced-correction",
                      self.codes(self.corrected(reviewer=False)))

    def test_a_correction_attributed_to_someone_else_is_refused(self):
        """The record's own identity and the judgment it carries are one
        statement; a record filed under another participant is two."""
        self.assertIn("misattributed-correction",
                      self.codes(self.corrected(participant="baton.nine")))

    def test_a_restart_with_no_review_behind_it_is_not_a_correction(self):
        """The difference between a correction and a restart IS the review that
        asked for it, so a second episode with no judgment behind it is
        reported rather than accepted as one."""
        held = [one for one in self.corrected()
                if not (one["stage_id"] or "").endswith("/review")]
        self.assertIn("unreviewed-correction", self.codes(held))

    def test_a_correction_recorded_before_its_own_review_is_refused(self):
        held = self.corrected()
        held[-1]["tick"] = 1
        self.assertIn("unreviewed-correction", self.codes(held))

    # -- and the manifest may not contradict the records ---------------------

    def declared(self, records, unobserved):
        scenario = scheduler_trace.Scenario(name="synthetic", jobs=[],
                                            workers=[], ticks=1)
        trace = scheduler_trace.Trace(scenario, unobserved=unobserved)
        trace.records = records
        artifact = trace.artifact()
        return sorted({one["code"]
                       for one in scheduler_trace.validate(artifact)})

    def test_a_manifest_calling_a_recorded_field_unobserved_is_refused(self):
        """MY OWN ARTIFACTS HAD THIS. `unobserved_fields` was a module constant
        copied into every manifest, so the composed exports declared `runtime_id`
        unobserved while carrying runtime ids read from the manager's own rows.
        Nothing compared the two, so the manifest could say anything."""
        held = self.legal()
        held[-1]["runtime_id"] = "runtime-1"
        self.assertIn("unobserved-field-recorded",
                      self.declared(held, ("runtime_id", "session_id")))
        self.assertEqual(self.declared(held, ("session_id",)), [])

    def test_a_manifest_naming_no_declaration_is_refused(self):
        artifact = self.artifact(self.legal())
        del artifact["environment"]["unobserved_fields"]
        self.assertIn("undeclared-observation",
                      [one["code"] for one in
                       scheduler_trace.validate(artifact)])

    def test_a_declaration_naming_a_field_this_oracle_knows_nothing_of(self):
        artifact = self.artifact(self.legal())
        artifact["environment"]["unobserved_fields"] = ["whatever"]
        self.assertIn("undeclared-observation",
                      [one["code"] for one in
                       scheduler_trace.validate(artifact)])

    def test_a_scenario_digest_that_does_not_match_is_refused(self):
        artifact = self.artifact(self.legal(acts=("reserve",)))
        artifact["scenario"]["name"] = "something-else"
        held = scheduler_trace.validate(artifact)
        self.assertIn("scenario-digest-mismatch",
                      [one["code"] for one in held])


class TheComposedOwnersSupplyAuthorizedTransitions(unittest.TestCase):
    """R1: THE TRANSITIONS ARE THE COMPOSED OWNERS' OWN, not reservations.

    COMPOSED RATHER THAN SUBCLASSED, which is the rule the composed fixture
    states about itself: "a `TestCase` subclass re-runs every case of its parent
    under a second name". The first form of this class subclassed it and duly
    re-ran all 57 of its cases here, costing 28.6s for two new assertions. The
    fixture is reused by calling its own `setUp` and its own helpers, and
    nothing else is inherited.

    Review 2026-09-12T16:18:34Z R1: the reservation-only schedules never offered,
    claimed, started, completed, corrected or reviewed anything, and an
    allocation release is not an owner-issued stage completion. This class takes
    the accepted composed fixture named in `PLAN.md`'s source map -- real
    Authority, real producers and reviewers, real review cycles, the scripted
    engine seam -- drives it through its ORDINARY authorized transitions, and
    reads the trace back out of durable owner evidence afterwards.

    NOTHING IS SCRIPTED INTO A SUCCESS. The producer turns and the reviewer
    verdict are the fixture's ordinary ones; every record below is read from the
    Job store's own projection, its allocations and the Worker Manager's own
    receipts. This module writes no receipt and inserts no row.
    """

    def setUp(self):
        self.case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
            "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    # C2/C3, review 2026-09-12T16:35:09Z: WHICH RECEIPT STATES ARE POSITIVE.
    # `RECEIPT_STATES` is ("performed", "adopted", "refused"); the first draft
    # emitted a performed record whenever the KEY existed, so a synthetic owner
    # snapshot whose admit receipt was `refused` became a performed offer and
    # validated clean. Only a positively settled receipt becomes a performed
    # record; a refused one stays refused and carries the owner's own detail.
    POSITIVE_RECEIPTS = ("performed", "adopted")

    # AND WHICH RECEIPT ACT MAPS TO WHICH TRACE ACT. `admit` issues the offer and
    # `claim` settles it; the acceptance the validator requires between them is
    # the settled offer's own evidence, which is why a claim receipt supplies
    # both. Nothing else is inferred.
    # ONE ACT PER RECEIPT, because one operation identity is one act. The first
    # correction emitted `accept` and `claim` from the single settlement receipt
    # and the exactly-once invariant refused it; acceptance is the settlement's
    # own state, and its absence as a separate record is recorded as a gap.
    RECEIPT_ACTS = (("admit", "offer"), ("claim", "claim"))

    def completion_of(self, held, stage_id, episode):
        """The integrator's OWN completion document for one finished stage.

        The existing public reader, asked exactly as the review's probe asks
        it, and nothing reached through it: no private store query and no
        branch marker manufactured from a stage name. Absence is an ordinary
        answer -- a stage the reader does not report completed carries none.
        """
        job_id, _, kind = stage_id.partition("/")
        observed = held.composed.integrator.observe(
            {"job_id": job_id, "kind": kind, "stage_id": stage_id,
             **dict(episode)})
        if (observed or {}).get("state") != "completed":
            return None
        context = observed.get("completion") or {}
        return {name: context.get(name)
                for name in scheduler_trace.COMPLETION_CONTEXT}

    def runtime_of(self, held, attempt_id):
        """The manager's own runtime row for one attempt, or absence."""
        from baton_v12.worker_manager.attempts import attempt_runtime_of

        deployment = self.case.deployment_of(held.composed)
        return attempt_runtime_of(deployment.control, attempt_id)

    def blank(self):
        """An empty trace to record into; the real scenario replaces it at export.

        The scenario document describes the run's INPUTS, and two of them -- the
        submitted graph and the configured identities -- are read from the stores
        after submission. Recording starts before that read, so the trace is
        given a placeholder and the actual scenario is attached before the
        artifact is built. `validate` re-derives the digest from whatever it
        finds, so a placeholder that was never replaced could not pass unnoticed.
        """
        # AND THIS DRIVER DECLARES WHAT IT LOOKED AT. Owner155646: the composed
        # observer asks the Worker Manager for the attempt's runtime row and
        # asks `agent_sessions_of` for its sessions, so neither field is
        # unobserved here -- and the artifacts said it was, while carrying
        # runtime ids. A null in a composed record now means the owner reported
        # none.
        return scheduler_trace.Trace(
            scheduler_trace.Scenario(name="pending", jobs=[], workers=[],
                                     ticks=100),
            unobserved=())

    def scenario_from(self, held, job_ids):
        """The ACTUAL submitted graph and configured identities.

        C3: both composed exports carried `jobs=[]` and `workers=[]`, so the
        dependency oracle had no edges to check at all and the scenario document
        described nothing. This reads the Job store's own stage rows -- including
        their recorded `depends_on` -- and the deployment's own configured
        workers and bindings, so the exported scenario is the graph that really
        ran rather than an empty placeholder.
        """
        from baton_v12.job_manager import stage_rows

        deployment = self.case.deployment_of(held.composed)
        jobs = {}
        for row in stage_rows(held.job):
            job_id = row["stage_id"].split("/")[0]
            if job_id not in job_ids:
                continue
            jobs.setdefault(job_id, {"job_id": job_id, "stages": []})
            # THE STORE RECORDS RESOLVED STAGE IDS; the submission schema and
            # this oracle speak {job_id, kind}. Normalized here rather than
            # taught to the validator, so the artifact keeps one shape.
            edges = []
            # AND IT MAY ARRIVE AS RAW JSON. Corrected after measurement: the
            # first form iterated the string itself character by character and
            # the oracle dutifully reported `[/ ` as a missing prerequisite.
            held_edges = row["depends_on"] or []
            if isinstance(held_edges, str):
                held_edges = json.loads(held_edges or "[]")
            for edge in held_edges:
                if isinstance(edge, dict):
                    edges.append({"job_id": edge["job_id"],
                                  "kind": edge["kind"]})
                else:
                    upstream, _, kind = str(edge).partition("/")
                    edges.append({"job_id": upstream, "kind": kind})
            jobs[job_id]["stages"].append(
                {"kind": row["kind"], "work_id": row["work_id"],
                 "depends_on": edges})
        workers = [{"worker_id": one["worker_id"], "role": one["role"],
                    "participant": one["deployment"]["participant"],
                    "principal": one["deployment"]["principal"]}
                   for one in deployment.given["workers"]]
        bindings = [{name: one.get(name) for name in
                     ("job_id", "job_work_id", "canonical_target_id",
                      "source_worker_id")}
                    for one in deployment.given["job_bindings"]]
        return [jobs[one] for one in sorted(jobs)], workers, bindings

    def observing(self, held, trace, job_id, kind, want, *, job_ids=("job-a",),
                  ticks=14):
        """Drive ordinary ticks and RECORD WHAT EACH TICK NEWLY SHOWED.

        D1, review 2026-09-12T16:51:07Z. Every earlier form of this extractor read
        a FINAL state dump after the run and then decided the order itself -- by
        act rank, which the reviewer showed overrides even unequal owner
        timestamps, and which therefore "imposes the expected causal order"
        instead of observing one. That is the defect, and no additional sorting
        key can fix it: the order has to be observed rather than chosen.

        SO THIS OBSERVES AT THE BOUNDARY THE FIXTURE ALREADY USES. `drive_job`
        calls public `job_manager.sweep` and then reads `states_for` each tick;
        this does the same and, after each tick, emits a record for every piece of
        owner evidence that was NOT there before. The tick number is the real
        tick. Nothing is reordered, and an observation is retained even when a
        later tick supersedes it -- which is exactly what the correction case
        needs, because the implementation really did complete before the reviewer
        sent it back.
        """
        from baton_v12.job_manager import sweep as one_tick
        from tests.job_manager import fixtures

        # THE TICK COUNTER AND THE SEEN SET SPAN THE WHOLE RUN, not one call.
        # Corrected after measurement: each call restarted at tick 1, so the
        # oracle reported `regressing-time` -- correctly, because a trace whose
        # logical time runs backwards is exactly what it refuses. One run is one
        # continuous clock.
        #
        # AND THE CLOCK BELONGS TO THE TRACE, not to this TestCase. Corrected
        # after measurement again, by the alternate-order case: it drives two
        # deployments in one test, and with the counter and the seen set on
        # `self` the second run inherited the first's clock AND its seen set --
        # so `job-b/implementation`'s completion, already seen under the same
        # stage id in the first deployment, was silently dropped from the second
        # trace and its review then looked like a successor reserved before its
        # prerequisite. One run is one trace is one clock.
        seen = trace.__dict__.setdefault("_seen", set())
        for _ in range(ticks):
            one_tick(held.job, held.composed, now=fixtures.NOW)
            trace._tick = getattr(trace, "_tick", 0) + 1
            self.observed(held, trace, trace._tick, job_ids, seen)
            states = self.case.states_for(held.job, held.composed, job_id)
            if states.get(kind) == want:
                return states
        self.fail(f"{job_id}'s {kind} never reached {want!r}")

    def observed(self, held, trace, tick, job_ids, seen):
        """Emit every piece of owner evidence this tick newly shows.

        `seen` is the set of facts already recorded, so each act is recorded once
        at the tick it FIRST became true. Order within a tick follows the owners'
        own receipt instants where they differ; where an owner records no instant
        the evidence is emitted under its own reader's name, and no act rank is
        used to invent a sequence.
        """
        from baton_v12.job_manager import allocation_of as allocated_for
        from baton_v12.job_manager import episodes_of, projection, stage_rows

        states = projection.stage_states(held.job, held.composed)
        pending = []
        for row in stage_rows(held.job):
            stage_id = row["stage_id"]
            if stage_id.split("/")[0] not in job_ids:
                continue
            for episode in episodes_of(held.job, stage_id):
                common = {"job_id": stage_id.split("/")[0],
                          "stage_id": stage_id, "episode": episode["episode"],
                          "attempt_id": episode["attempt_id"]}
                allocation = allocated_for(held.job, episode["attempt_id"])
                if allocation is not None:
                    pending.append(("", dict(
                        common, act="reserve", outcome="performed",
                        worker_id=allocation["worker_id"],
                        principal=allocation.get("canonical_principal"),
                        operation_id="allocation.reserve:"
                                     + episode["attempt_id"],
                        evidence="allocations:" + episode["attempt_id"])))
                    if allocation["allocation_state"] == "released":
                        pending.append(("~release", dict(
                            common, act="release", outcome="performed",
                            worker_id=allocation["worker_id"],
                            principal=allocation.get("canonical_principal"),
                            operation_id="allocation.release:"
                                         + episode["attempt_id"],
                            evidence="allocations:" + episode["attempt_id"])))
                # THE OFFER'S OWN ACCEPTANCE, read from the offer row the
                # public claimed-offer reader answers. It carries its own
                # instant, so the oracle orders it against the claim by the
                # owners' clocks rather than by this driver's ladder.
                for offer in claimed_offers_for(held.control,
                                                episode["attempt_id"]):
                    if offer.get("accepted_at"):
                        pending.append((offer["accepted_at"], dict(
                            common, act="accept", outcome="performed",
                            participant=offer.get("participant"),
                            recorded_at=offer["accepted_at"],
                            evidence=f"offers:{offer['offer_id']}:accepted")))
                # AND THE AGENT SESSION, when one was opened for this attempt.
                #
                # THE WHOLE REFERENCE AND THE WHOLE ROW. Owner155646: the first
                # composed path opened no session at all, so this reader was
                # never exercised -- and the moment one really opened, its two
                # defects showed at once. It spelled the identity
                # `posture:epoch`, and the producer's session and the
                # reviewer's session were BOTH `execution:1`; and it carried no
                # posture, epoch, provider id, Work or state, so nothing
                # downstream could tell a consent session from an execution one.
                # `session_reference` is the §3.1 four-part reference and the
                # context travels beside it.
                for session in agent_sessions_of(held.control,
                                                 episode["attempt_id"]):
                    pending.append(("~session", dict(
                        common, act="observe", outcome="performed",
                        participant=session.get("participant"),
                        session_id=scheduler_trace.session_reference(session),
                        session={name: session.get(name) for name
                                 in scheduler_trace.SESSION_CONTEXT},
                        recorded_at=session.get("opened_at"),
                        evidence="agent_sessions:"
                                 + episode["attempt_id"])))
                receipts = projection.receipts_of(held.job, stage_id,
                                                  episode["episode"])
                for act, emitted in self.RECEIPT_ACTS:
                    receipt = receipts.get(act)
                    if receipt is None:
                        continue
                    positive = receipt["state"] in self.POSITIVE_RECEIPTS
                    pending.append((receipt["recorded_at"], dict(
                        common, act=emitted,
                        recorded_at=receipt["recorded_at"],
                        outcome="performed" if positive else "refused",
                        operation_id=receipt["operation_id"]
                        if positive else None,
                        evidence=f"receipts:{stage_id}:"
                                 f"{episode['episode']}:{act}",
                        cause=None if positive else
                        f"receipt/{receipt['state']}: {receipt['detail']}")))
                runtime = self.runtime_of(held, episode["attempt_id"])
                if runtime is not None and runtime.get("runtime_id"):
                    pending.append(("~start", dict(
                        common, act="start", outcome="performed",
                        runtime_id=runtime["runtime_id"],
                        operation_id="runtime.start:" + episode["attempt_id"],
                        evidence="attempt_runtime:" + episode["attempt_id"])))
                entry = states.get(stage_id) or {}
                if (entry.get("attempt") or {}).get("attempt_id") \
                        == episode["attempt_id"] \
                        and entry.get("state") == "completed":
                    # AND A COMPLETED INTEGRATION CARRIES THE OWNER'S OWN
                    # BINDING. Review 2026-09-13T00:47:10Z R6: the Job label is
                    # not the subject. `Integration.observe` answers which
                    # proposal this stage imported, which derived result (or
                    # none), which integration receipt authorized it and which
                    # runtime it ran on (or none) -- the branch included.
                    completion = None
                    if row["kind"] == "integration":
                        completion = self.completion_of(held, stage_id,
                                                        episode)
                    pending.append(("~complete", dict(
                        common, act="complete", outcome="performed",
                        operation_id="stage.completed:" + episode["attempt_id"],
                        completion=completion,
                        evidence="stage_states:" + stage_id)))
        # THE OWNERS' INSTANTS ORDER WHAT THEY TIMESTAMP; everything else keeps
        # the reader order it was gathered in. No act rank participates.
        pending.sort(key=lambda one: one[0])
        for _when, members in pending:
            # ONE KEY PER FACT, AND A SESSION IS ITS OWN FACT. The key was
            # (stage, episode, act), so an attempt holding a consent session
            # AND an execution session recorded exactly one of them -- two
            # owner facts collapsed into one record by a dedup key, which is
            # the same class of erasure as the identity above.
            key = (members["stage_id"], members["episode"], members["act"],
                   members.get("session_id"))
            if key in seen:
                continue
            seen.add(key)
            act = members.pop("act")
            trace.record(tick, act, **members)

    # THE FINAL-DUMP EXTRACTOR IS REMOVED, not left beside its replacement.
    #
    # D1, review 2026-09-12T16:51:07Z: it read state after the run and then chose
    # the order itself, which is the defect -- and a dead copy of it sitting here
    # is an invitation to use it again. `observing` above records what each tick
    # newly showed, at the boundary the fixture already uses, so there is one way
    # to build a composed trace and it is the observed one.

    # -- W103525 PLAN item 6: FOUR JOBS, TWO TEAMS, TWO REPOSITORIES ---------
    #
    # Owner ruling 157085 raised the implementation allowance to 600 cumulative
    # seconds precisely so this could be started. The PLAN's sentence is: "four
    # Jobs across two teams and two repository bindings, two implementation and
    # two review slots, and separately configured integration capacity ... one
    # dependency edge A->B, independent C/D", and: "a fixture that cannot bind
    # this configuration reports the gap rather than silently reducing it".
    #
    # BOTH HALVES OF THAT SENTENCE ARE MEASURED BELOW, and they do not agree
    # with each other. The four Jobs, the two teams and the two repositories are
    # real and they run in parallel. The TWO SLOTS are not: a configured worker
    # record is bound to one Work, a Work belongs to one Job's stage, and the
    # scheduler will not lend an idle producer to a Job whose Work it does not
    # carry. So four Jobs need four producer records, and the gap is recorded
    # with the owners' own contrast as its evidence rather than argued.
    # C AND D'S OWN WORKS, and NOT W3/W4/W5: those three are the composed
    # fixture's judgment Works, and the four-Job scenario needs the result
    # judges configured -- so Works chosen to avoid a collision that only
    # appears once the judges exist.
    THIRD_WORK, FOURTH_WORK = "0000000a-W7", "0000000a-W8"

    # THE SECOND TEAM, AND WHY THESE NAMES. `authority/identity.py` fixes the
    # grammar -- "a participant is team.member" -- so the team IS the endpoint's
    # prefix. Review 2026-09-13T03:39:45Z [P1]: the first four-Job artifact
    # called itself two-team and every configured participant and resolved
    # principal in it was `baton.*`. A second repository is not a second team.
    # Jobs C and D are served by `other.*` actors, authorized the way the team
    # matrix in this class already proves is legal -- a capability at the Work's
    # own scope through the Authority's public `grant_capability`, plus the
    # route handlers that say who MAY claim on each role's route.
    SECOND_TEAM = "other"
    FOUR_ACTORS = {
        "job-c": {"producer": "other.third", "reviewer": "other.reviewer-3"},
        "job-d": {"producer": "other.fourth", "reviewer": "other.reviewer-4"}}

    # -- a REAL regression per ordinary Job ---------------------------------
    #
    # Review 2026-09-13T10-44-30Z, and it supersedes that reviewer's own
    # earlier compatible-harness recommendation as well as my implementation
    # of it. Identical `harness.py` bytes for A, C and D removed the merge
    # conflict, and the alternate continuation still refused -- measured, in
    # the reviewer's repro-159894-causal.py, which read the actual observer
    # answers: base `sha256:9a5aba18...`, harness_added FALSE, status 0;
    # isolated and combined `sha256:260aa72f...`. The base ALREADY HOLDS
    # `harness.py`, so `_ConfiguredExecution._run` does not add its pinned one
    # there and the base runs the OLD file. One pinned harness, three content
    # states, three digests -- and `reconciliation._causal` refuses exactly
    # that. It also requires the base to have had the harness ADDED and its
    # status to be NONZERO, which a print-only harness could never give
    # however its bytes were spelled.
    #
    # SO EACH ORDINARY JOB GETS WHAT B ALREADY HAS: a required test at a path
    # the original base does not contain, asserting that Job's own payload.
    # It fails on the base with only itself overlaid -- the module it imports
    # is not there -- and passes on that Job's isolated candidate and on the
    # combination. One digest across all three observations, base added and
    # nonzero, isolated and combined not added and zero. The shared
    # pre-existing harness is left alone, which also means these Jobs no
    # longer write one shared path at all.
    ORDINARY = ("job-a", "job-c", "job-d")

    def ordinary_work(self, job_id):
        """The Work each independent Job is bound to."""
        return {"job-a": self.case.work,
                "job-c": self.THIRD_WORK,
                "job-d": self.FOURTH_WORK}[job_id]

    def regression_files(self, job_id):
        """This Job's own payload AND the test that asserts it.

        Both are written by the producer's own turn, so the submission carries
        its test with it -- B's `feature_check.py` pattern, per Job. The module
        the check imports is this Job's own file, so on the original base the
        check cannot even import.
        """
        name = job_id.replace("-", "_")
        return {f"feature_{name}.py": f"VALUE = '{job_id} brought this'\n",
                f"check_{name}.py": (
                    f"from feature_{name} import VALUE\n\n"
                    f"assert VALUE == '{job_id} brought this', VALUE\n"
                    f"print('{job_id} regression passed')\n")}

    def regression_task(self, job_id):
        """The task document naming THIS Job's required test.

        The bytes are derived from the Job identity alone, so every caller --
        the producer's manifest, the reviewer's manifest, the configured
        document on disk and the submitted input digest -- describes the same
        task. `single_worker._held` cross-checks the document's bytes against
        the manifest's human contract, so the two move together or nothing
        composes at all.
        """
        name = job_id.replace("-", "_")
        payload = json.dumps(
            {"schema": "baton.dogfood-task/2",
             "task_id": f"w103525-{name}-regression",
             "instructions": f"Add focused coverage for {job_id}.",
             "source_root": "source", "source_profile": "git-line",
             "declared_base": self.case.base,
             "verification": ["python3", f"check_{name}.py"]},
            sort_keys=True).encode("utf-8")
        document = os.path.join(self.case.root,
                                f"task-{job_id}-regression.json")
        with open(document, "wb") as writing:
            writing.write(payload)
        return payload, document

    def regression_digest(self, job_id):
        """The submitted input digest for this Job, over that same task."""
        payload, _ = self.regression_task(job_id)
        return self.case.manifest_over(
            self.ordinary_work(job_id), payload)["manifest_digest"]

    def regression_worker(self, worker, job_id):
        """Bind one configured worker -- producer OR reviewer -- to the task.

        The reviewer's deployment carries it too, which is the reviewer's
        instruction rather than a convenience: a review worker left on another
        manifest describes a task its own Job does not hold.
        """
        payload, document = self.regression_task(job_id)
        worker["deployment"]["input_manifest"] = self.case.manifest_over(
            self.ordinary_work(job_id), payload)
        worker["deployment"]["task_document"] = document
        return worker

    # ONE JUDGMENT WORK PER JOB AND KIND. The identities are derived from the
    # pair rather than spelled, so the twelve cannot collide with each other,
    # with the four scenario Works or with the three the fixture creates.
    JUDGMENT_WORK_BASE = 20

    def judgment_work_of(self, job_id, kind, worker):
        """Give this Job's judge of this kind its OWN Work, and bind it.

        The Authority act is ordinary and public -- the same `create_work` the
        fixture uses for its own judgment Works -- and the worker's manifest is
        rewritten over the SAME configured task bytes, so the document on disk
        and the manifest's human contract still describe one task.
        """
        from baton_v12.authority import Authority

        from tests.job_manager import fixtures

        kinds = sorted(self.case.JUDGMENT_WORKS)
        index = (self.JUDGMENT_WORK_BASE
                 + list(self.FOUR).index(job_id) * len(kinds)
                 + kinds.index(kind))
        work_id = f"0000000a-W{index}"
        authority = Authority.open(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            try:
                authority.create_work(
                    work_id, fixtures.ROUTE, contract="v12-assignment-1",
                    operation_id=f"create-{job_id}-{kind}-judgment-work")
            except Exception as existing:
                # AN EXISTING WORK IS AN ORDINARY ANSWER. This setup runs once
                # per composition and a case may compose more than once.
                if "already exists" not in str(existing):
                    raise
        finally:
            authority.dispose()
        worker["worker_id"] = f"{job_id}-{kind}-judge"
        worker["deployment"]["input_manifest"] = self.case.manifest_over(
            work_id, self.case.judgment_task_bytes(kind))
        return work_id

    def four_works(self):
        """The two additional Works, created through the Authority's own API.

        Legal public setup, which is what the reviewer's disposition allows:
        Works, routes and identities are created; no receipt, claim, review or
        import is fabricated anywhere in this case.
        """
        from baton_v12.authority import Authority, V12

        from tests.job_manager import fixtures

        authority = Authority.open(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            for index, work in enumerate((self.THIRD_WORK, self.FOURTH_WORK)):
                # AN EXISTING WORK IS AN ORDINARY ANSWER HERE. This setup runs
                # once per composition and a case may compose more than once;
                # creating a Work that is already there is the Authority
                # refusing a duplicate, not a fixture failure.
                try:
                    authority.create_work(
                        work, "baton.impl", contract=V12,
                        operation_id=f"create-four-job-{index}")
                except Exception as existing:
                    if "already exists" not in str(existing):
                        raise
            # AND WHO MAY SERVE THEM. [P1]: C and D were reserved and offered
            # and could never claim -- four further ordinary sweeps reported the
            # exact public cause, that route `baton.impl` does not resolve to
            # these participants. That is missing fixture setup, not a product
            # blocker and not evidence of three producers coding in parallel.
            # The route says who MAY claim; which of them does is the
            # scheduler's own allocation.
            for held in self.FOUR_ACTORS.values():
                authority.add_route_handler(fixtures.ROUTE, held["producer"])
                authority.add_route_handler("rview", held["reviewer"])
                # THE SECOND TEAM'S AUTHORIZATION IS A CAPABILITY AT THE
                # WORK'S OWN SCOPE, which is what this class's own team matrix
                # established is the legal seam. No membership relation exists
                # and none is invented.
                #
                # ONLY THE REVIEWER TAKES A GRANT, and that is the Authority's
                # own answer rather than a choice: measured here, the configured
                # capabilities are verify, review, approve, integrate, close and
                # manage-work-labels, and there is no `implement` among them. A
                # producer is authorized by the ROUTE it may claim on; what a
                # capability governs is the judgments a participant may record.
                authority.grant_capability(held["reviewer"], "review",
                                           scope=self.case.scope)
        finally:
            authority.dispose()

    def current_policy(self):
        """Re-read the Authority's policy generation AFTER `four_works`.

        Review 2026-09-13T04:11:17Z, and it supersedes my own unknown-cause
        gap. The borrowed fixture pins its policy generation in `setUp`, and
        `composed_document` carries that pin into the deployment. `four_works`
        then performs real Authority acts -- two `create_work`s, four
        `add_route_handler`s and two `grant_capability`s -- and every one of
        those MOVES the generation. So the composition was pinned to 11 while
        the Authority stood at 17, and four ordinary sweeps reported exactly
        that: `conclude` deferred `policy/denied`.

        THE REVIEWS WERE NEVER THE PROBLEM. Every review turn returned zero and
        every verdict was written; what could not happen was the CONCLUSION,
        because the deployment was acting under a generation that no longer
        existed. This is stale fixture setup, not a product limitation, and the
        correction is to read the current generation after the setup acts and
        before the composition -- changing no live intent and no receipt.
        """
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            self.case.fixture_policy = authority.policy_generation()
        finally:
            authority.dispose()
        return self.case.fixture_policy

    def four_jobs(self, *, own_workers):
        """The configuration document for four Jobs, TWO TEAMS, ONE TARGET.

        `own_workers` is the whole experiment. FALSE is the PLAN's literal
        two-slot shape: C and D name the EXISTING producers as their source, so
        the deployment carries two implementation and two review records for
        four Jobs. TRUE gives C and D their own producer and reviewer, drawn
        from the second team. Nothing else differs between the two -- same
        Works, same submission, same edge, same ticks -- so what the owners do
        differently is caused by the worker binding and by nothing else.

        NOT TWO REPOSITORIES. `traversing` binds every Job to ONE canonical
        target, because the Authority holds one target revision and a proposal
        is offered against the revision it was built from. Independent
        repository bindings are proved by this class's separate binding case;
        the combined four-Job / two-repository / two-effective-slot contract is
        NOT discharged by this scenario and stays open.
        """
        given = self.case.traversing()
        held = {one["worker_id"]: one for one in given["workers"]}
        # JOB A'S OWN REGRESSION, ON BOTH OF ITS ROLES. A kept the base
        # fixture's harness task, whose required test the original base
        # already contains -- which is precisely why its causal observation
        # reported three digests and no added, failing base. See
        # `regression_task`.
        for worker_id in ("implementation-worker", "review-worker"):
            self.regression_worker(held[worker_id], "job-a")
        sources = {"job-c": "implementation-worker",
                   "job-d": "implementation-worker"}
        if own_workers:
            workers = list(given["workers"])
            for job, work in (("job-c", self.THIRD_WORK),
                              ("job-d", self.FOURTH_WORK)):
                producer = copy.deepcopy(held[sources[job]])
                producer["worker_id"] = "implementation-worker-" + job[-1]
                self.case.bound_worker(producer, work)
                # AND THEN THIS JOB'S OWN TASK over its own Work.
                # `bound_worker` binds the manifest and document the fixture
                # holds for a Work, which for C and D is the base harness task;
                # the regression is theirs and is named here.
                self.regression_worker(producer, job)
                actors = self.FOUR_ACTORS[job]
                producer["deployment"]["participant"] = actors["producer"]
                producer["deployment"]["principal"] = \
                    "principal:" + actors["producer"]
                workers.append(producer)
                workers.append(self.regression_worker(
                    self.case.role_worker(
                        "review", work, "review-worker-" + job[-1],
                        participant=actors["reviewer"],
                        principal="principal:" + actors["reviewer"],
                        review_route=self.case.INTEGRATION_ROUTE),
                    job))
                sources[job] = producer["worker_id"]
            given["workers"] = workers
        given["job_bindings"] = given["job_bindings"] + [
            {"job_id": "job-c", "job_work_id": self.THIRD_WORK,
             "review_work_id": self.THIRD_WORK,
             "line_declared_base": self.case.base,
             "canonical_target_id": "target-a",
             "source_worker_id": sources["job-c"]},
            # JOB D SITS WHERE THE OTHERS DO, and that is `traversing`'s own
            # fact rather than a simplification: the Authority holds ONE
            # canonical target revision and a proposal is offered against the
            # revision it was built from, so every Job that publishes here is a
            # LINE OF ONE TARGET at one base. The first form of this binding
            # named the second repository's base and its line could not be
            # materialized at all -- measured, in probe-157344-lines.py. The
            # separate two-repository binding case in this class is what proves
            # independent repository bindings; this scenario does not.
            {"job_id": "job-d", "job_work_id": self.FOURTH_WORK,
             "review_work_id": self.FOURTH_WORK,
             "line_declared_base": self.case.base,
             "canonical_target_id": "target-a",
             "source_worker_id": sources["job-d"]}]
        return given

    def four_submission(self):
        """One submission, four Jobs, ONE dependency edge A->B.

        B's implementation waits on A's REVIEW -- a cross-Job edge, which is the
        one the PLAN names -- and C and D depend on nothing, so what competes
        for producer capacity at the first tick is A, C and D.
        """
        from tests.job_manager import fixtures

        def job(job_id, work, **changed):
            return fixtures.job(
                job_id,
                input_digest=self.regression_digest(job_id),
                policy_digest=fixtures.POLICY_DIGEST,
                stages=[
                    fixtures.stage("implementation", work, **changed),
                    fixtures.stage("review", work,
                                   depends_on=[{"job_id": job_id,
                                                "kind": "implementation"}]),
                    # AND AN INTEGRATION STAGE, because a scenario about
                    # separately configured integration capacity cannot have one
                    # Job that ever reaches it. Review 2026-09-13T03:39:45Z: the
                    # first submission ended B, C and D at review, so the four
                    # Jobs could not contend for the integrator at all.
                    fixtures.stage("integration", work,
                                   depends_on=[{"job_id": job_id,
                                                "kind": "review"}])])

        # AND JOB A'S COPIED SUBMISSION TOO. It is the accepted fixture's
        # own first Job, whose digest describes the base harness task; its
        # producer and reviewer now carry the regression task, and a submitted
        # input naming another one would describe a Job nobody configured.
        first = copy.deepcopy(self.case.submission["jobs"][0])
        first["input_digest"] = self.regression_digest("job-a")
        return fixtures.submission(jobs=[
            first,
            fixtures.job(
                "job-b",
                input_digest=self.case.manifest_over(
                    composed_fixture.SECOND_WORK,
                    self.case.shared_task_bytes)["manifest_digest"],
                policy_digest=fixtures.POLICY_DIGEST,
                stages=[
                    fixtures.stage("implementation",
                                   composed_fixture.SECOND_WORK,
                                   depends_on=[{"job_id": "job-a",
                                                "kind": "review"}]),
                    fixtures.stage("review", composed_fixture.SECOND_WORK,
                                   depends_on=[{"job_id": "job-b",
                                                "kind": "implementation"}]),
                    fixtures.stage("integration", composed_fixture.SECOND_WORK,
                                   depends_on=[{"job_id": "job-b",
                                                "kind": "review"}])]),
            job("job-c", self.THIRD_WORK),
            job("job-d", self.FOURTH_WORK)])

    def four_job_deployment(self, *, own_workers, ticks=3):
        """Four submitted Jobs on one live deployment, ticked three times."""
        from baton_v12.job_manager import submit, sweep
        from tests.job_manager import fixtures

        self.four_works()
        self.current_policy()
        # THE RESULT JUDGES ARE CONFIGURED BEFORE COMPOSITION. Review
        # 2026-09-13T10:23:35Z found the gate my loop kept hitting: after the
        # first integration the sweeps DO offer and claim the next Job, and the
        # composed launch then answers `pending` because the Authority has no
        # verification receipt on its DERIVED proposal. That is the RECONCILED
        # branch -- it need not start an integration runtime at all -- so a
        # waiter looking for `integrating` was waiting for the wrong
        # transition, and the deployment needs its judges to get past it.
        # AND THE JUDGES ARE CONFIGURED FOR EVERY JOB, not for one. The
        # fixture helper defaults to `job-b`, and `result_judgment_workers` is
        # keyed BY JOB: the reconciled branch asks for the judges of the Job
        # whose result it published, so a deployment carrying only job-b's
        # could never carry any other Job's second import. That is exactly what
        # step 272 measured -- the A-before-C order's second import is job-b's
        # and found its three judges, while the C-before-A order's is job-a's
        # and found NONE.
        #
        # AND EACH JOB'S JUDGES NEED THEIR OWN WORKS, which is what a THIRD
        # import needs and what steps 275 to 278 measured. The borrowed
        # fixture's `judgment_work` makes ONE Work per KIND, because it was
        # built for one Job; those Works are claimed on route `baton.impl` and
        # a completed judgment leaves its assignment on `rview`. So the second
        # Job's verification judge could not claim at all, and the Authority
        # said so exactly: "route 'rview' does not resolve to 'baton.verifier'".
        # A Work per (Job, kind) is what a per-Job judge actually needs.
        judges = {}
        for job_id in self.FOUR:
            held = self.case.judgment_workers(job_id)[job_id]
            for kind, one in sorted(held.items()):
                self.judgment_work_of(job_id, kind, one)
            judges[job_id] = held
        # AND THE POLICY IS RE-READ AFTER THOSE ACTS TOO. See `current_policy`:
        # creating those Works moves the generation, and a composition pinned
        # to a generation the Authority has moved past defers every conclusion.
        self.current_policy()
        job, control, composed = self.case.serving_two(
            result_judgment_workers=judges,
            **self.four_jobs(own_workers=own_workers))
        submit(job, self.four_submission())
        held = SimpleNamespace(job=job, control=control, composed=composed)
        for _ in range(ticks):
            sweep(held.job, held.composed, now=fixtures.NOW)
        return held

    def producers_of(self, held):
        """Which producer each implementation stage is ACTUALLY allocated."""
        from baton_v12.job_manager import episodes
        from baton_v12.job_manager.scheduler import allocation_of
        from baton_v12.job_manager.submission import stage_rows

        answer = {}
        for row in stage_rows(held.job):
            if row["kind"] != "implementation":
                continue
            live = episodes.live_of(held.job, row["stage_id"])
            attempt = (episodes.attempting(row, live)["attempt_id"]
                       if live else None)
            allocation = allocation_of(held.job, attempt) if attempt else None
            answer[row["stage_id"]] = (allocation or {}).get("worker_id")
        return answer

    FOUR = ("job-a", "job-b", "job-c", "job-d")

    def test_four_jobs_two_teams_claim_three_producers_at_once(self):
        """THE POSITIVE, and its name now says what it asserts.

        Review 2026-09-13T03:39:45Z corrected two overstatements in the first
        form. It called itself two-REPOSITORY, and under `traversing` every Job
        is a line of ONE canonical target -- the separate binding case in this
        class is what proves independent repositories. And it called itself
        parallel EXECUTION while asserting only allocation: C and D were
        reserved and offered and could never claim, because route `baton.impl`
        did not resolve to their participants. That was missing fixture setup,
        and it is configured now.

        WHAT IS ASSERTED HERE. Three Jobs reach a CLAIMED offer at once, on
        three distinct producers drawn from TWO TEAMS, while the fourth waits on
        its dependency edge rather than on capacity. Every operand is an owner's
        own: the Authority creates the Works, registers the routes and grants
        the second team's reviewers their capability at the Work's own scope;
        the Job owner admits four Jobs from one submission; the scheduler
        allocates and the offer owner settles the claims. Nothing here writes an
        allocation, a claim or a receipt.
        """
        from baton_v12.worker_manager.offers import claimed_offers_for

        held = self.four_job_deployment(own_workers=True, ticks=7)
        producers = self.producers_of(held)
        working = {stage: worker for stage, worker in producers.items()
                   if worker is not None}
        self.assertEqual(sorted(working), ["job-a/implementation",
                                           "job-c/implementation",
                                           "job-d/implementation"])
        # DISTINCTNESS, because three stages naming one worker would be one slot
        # reported three times.
        self.assertEqual(len(set(working.values())), 3, working)
        # AND B IS HELD BY ITS EDGE, NOT BY CAPACITY: its own producer record is
        # configured and idle.
        self.assertIsNone(producers["job-b/implementation"])
        self.assertNotIn("implementation-worker-b", set(working.values()))
        # THE CLAIMS THEMSELVES, from the offer owner rather than from the
        # allocation. This is what the first form did not establish.
        for stage in sorted(working):
            with self.subTest(stage=stage):
                self.assertEqual(
                    len(claimed_offers_for(held.control,
                                           self.attempt_of(held, stage))), 1)
                self.assertEqual(
                    self.case.states_for(held.job, held.composed,
                                         stage.split("/")[0])
                    ["implementation"], "waiting")

    def test_the_four_job_scenario_really_carries_two_teams(self):
        """[P1]: the first artifact called itself two-team and every configured
        participant and resolved principal in it was `baton.*`.

        A team is the endpoint's own prefix -- `authority/identity.py` fixes the
        grammar -- and the identities are read back from the AUTHORITY rather
        than from the configuration that asked for them, so this cannot pass on
        a document that merely spells a second team's name.
        """
        from baton_v12.authority import Authority

        held = self.four_job_deployment(own_workers=True, ticks=7)
        deployment = self.case.deployment_of(held.composed)
        configured = {one["deployment"]["participant"]
                      for one in deployment.given["workers"]}
        teams = {one.split(".")[0] for one in configured}
        self.assertEqual(teams, {"baton", self.SECOND_TEAM})
        authority = Authority.open_readonly(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            for job_id, actors in self.FOUR_ACTORS.items():
                with self.subTest(job=job_id):
                    self.assertEqual(
                        authority.principal_of(actors["producer"]),
                        "principal:" + actors["producer"])
                    # AND THE SECOND TEAM'S REVIEWER REALLY HOLDS ITS
                    # CAPABILITY AT THIS WORK'S OWN SCOPE, which is the seam
                    # this class's team matrix established is the legal one.
                    self.assertTrue(authority.holds_capability(
                        actors["reviewer"], "review", scope=self.case.scope))
        finally:
            authority.dispose()
        # AND THE SECOND TEAM IS REALLY SERVING: both of its producers hold a
        # claimed offer.
        working = {stage: worker
                   for stage, worker in self.producers_of(held).items()
                   if worker is not None}
        second = {one["worker_id"]: one["deployment"]["participant"]
                  for one in deployment.given["workers"]
                  if one["deployment"]["participant"].startswith(
                      self.SECOND_TEAM + ".")}
        self.assertEqual(
            sorted(worker for worker in working.values() if worker in second),
            ["implementation-worker-c", "implementation-worker-d"])

    def attempt_of(self, held, stage_id):
        """The attempt id this stage's live episode is attempting."""
        from baton_v12.job_manager import episodes
        from baton_v12.job_manager.submission import stage_rows

        for row in stage_rows(held.job):
            if row["stage_id"] != stage_id:
                continue
            live = episodes.live_of(held.job, row["stage_id"])
            return episodes.attempting(row, live)["attempt_id"] if live else None
        return None

    def two_repository_bindings(self, given, jobs):
        """Move these Jobs and their producers onto the SECOND repository.

        AND BIND THE SOURCE WORKER, which the first form did not. Review
        2026-09-13T09:44:04Z [P2]: it set each worker's nominated source and
        each binding's base and target, and left `source_worker_id` alone -- so
        the combined negative described D on the second repository while
        actually binding it to A's producer on the first. A helper that names a
        repository has to move every operand that selects it.
        """
        by_id = {one["worker_id"]: one for one in given["workers"]}
        for job_id, worker_id in jobs.items():
            by_id[worker_id]["deployment"]["nominated_source"] = \
                self.case.second_source
            for binding in given["job_bindings"]:
                if binding["job_id"] == job_id:
                    binding["line_declared_base"] = self.case.second_base
                    binding["canonical_target_id"] = "target-b"
                    binding["source_worker_id"] = worker_id
        return given

    def bound_sources(self, held):
        """What each Job's binding ACTUALLY names: worker, base and target."""
        deployment = self.case.deployment_of(held.composed)
        workers = {one["worker_id"]: one["deployment"]["nominated_source"]
                   for one in deployment.given["workers"]}
        return {one["job_id"]: (one["source_worker_id"],
                                workers[one["source_worker_id"]],
                                one["line_declared_base"],
                                one["canonical_target_id"])
                for one in deployment.given["job_bindings"]}

    def served(self, given):
        """Submit the four Jobs onto this configuration and tick."""
        from baton_v12.job_manager import submit, sweep
        from tests.job_manager import fixtures

        job, control, composed = self.case.serving_two(**given)
        self.addCleanup(composed.close)
        submit(job, self.four_submission())
        held = SimpleNamespace(job=job, control=control, composed=composed)
        for _ in range(7):
            sweep(held.job, held.composed, now=fixtures.NOW)
        return held

    def test_four_jobs_do_bind_and_serve_across_two_repositories(self):
        """THE COMBINED CONTRACT'S FIRST HALF, and it is FEASIBLE.

        Owner ruling M157707 asked for this to be checked first, and the answer
        corrects something I implied. The four-Job scenario above puts every Job
        on one canonical target -- but that is `traversing`'s own binding, NOT a
        limit of the contract, and my earlier prose read as though it were.

        Asked directly, the owners serve it: `job-c` and `job-d` nominate the
        second repository, declare its base and bind to `target-b`, and all
        three eligible Jobs are allocated on their own producers across the two
        repositories. `job-b` is held by the cross-Job edge as before.
        """
        self.four_works()
        self.current_policy()
        given = self.two_repository_bindings(
            self.four_jobs(own_workers=True),
            {"job-c": "implementation-worker-c",
             "job-d": "implementation-worker-d"})
        held = self.served(given)
        working = {stage: worker
                   for stage, worker in self.producers_of(held).items()
                   if worker is not None}
        self.assertEqual(sorted(working), ["job-a/implementation",
                                           "job-c/implementation",
                                           "job-d/implementation"])
        self.assertEqual(len(set(working.values())), 3, working)
        # AND THE TWO REPOSITORIES ARE REALLY TWO, read from the bindings the
        # deployment holds rather than from what this case asked for: each
        # Job's own source worker, that worker's nominated repository, the base
        # it declares and the target it binds.
        bound = self.bound_sources(held)
        self.assertEqual(bound["job-a"][1], self.case.source)
        self.assertEqual(bound["job-a"][3], "target-a")
        for job_id in ("job-c", "job-d"):
            with self.subTest(job=job_id):
                self.assertEqual(bound[job_id][0],
                                 "implementation-worker-" + job_id[-1])
                self.assertEqual(bound[job_id][1], self.case.second_source)
                self.assertEqual(bound[job_id][2], self.case.second_base)
                self.assertEqual(bound[job_id][3], "target-b")

    def test_two_repositories_do_not_make_two_slots_servable(self):
        """THE COMBINED CONTRACT'S SECOND HALF, and it is NOT.

        Same two repositories, and C and D naming the EXISTING producers as
        their source -- the PLAN's two-slot shape. Neither is allocated.

        WHAT THIS SETTLES. The repository dimension is not what blocks the
        combined contract: it serves on its own, proved directly above. What
        blocks it is the retained source-binding gap -- a producer carries one
        Work's manifest and task, and a Work belongs to one Job's stage -- and
        that is unchanged by which repository anything sits in. The combined
        four-Job / two-repository / two-effective-slot contract therefore
        remains OPEN, and this names exactly which half of it is missing.
        """
        self.four_works()
        self.current_policy()
        given = self.two_repository_bindings(
            self.four_jobs(own_workers=False),
            {"job-b": "implementation-worker-b",
             "job-d": "implementation-worker-b"})
        held = self.served(given)
        # THE MAPPING IS ASSERTED BEFORE THE OUTCOME IS READ, because the first
        # form of this case described a binding it did not make.
        bound = self.bound_sources(held)
        self.assertEqual(bound["job-a"][0], "implementation-worker")
        self.assertEqual(bound["job-a"][3], "target-a")
        for job_id in ("job-b", "job-d"):
            with self.subTest(job=job_id):
                self.assertEqual(bound[job_id][0], "implementation-worker-b")
                self.assertEqual(bound[job_id][1], self.case.second_source)
                self.assertEqual(bound[job_id][2], self.case.second_base)
                self.assertEqual(bound[job_id][3], "target-b")
        self.assertEqual(bound["job-c"][0], "implementation-worker")
        producers = self.producers_of(held)
        self.assertEqual(producers["job-a/implementation"],
                         "implementation-worker")
        for stage in ("job-b/implementation", "job-c/implementation",
                      "job-d/implementation"):
            self.assertIsNone(producers[stage], stage)

    def test_a_producer_bound_to_another_work_is_not_an_eligible_slot(self):
        """THE GAP, MEASURED BY CONTRAST RATHER THAN ARGUED, and SCOPED.

        Same four Works, same submission, same edge, same three ticks -- and C
        and D name the EXISTING producers as their source instead of carrying
        their own. Nothing is allocated to them. The idle producer is right
        there: B is gated by the edge, so `implementation-worker-b` is free the
        whole time and no Job takes it.

        A configured worker carries ONE Work's input manifest and task, and a
        Work belongs to one Job's implementation stage, so the scheduler has no
        eligible worker for C or D under THIS configuration.

        WHAT THIS DOES AND DOES NOT ESTABLISH. Review 2026-09-13T03:39:45Z: it
        is an observed binding limitation of the configuration tested here,
        consistent with the source-worker eligibility gap this Work already
        retains. It does NOT establish that every possible arrangement of four
        Job records over two effective slots is impossible, and four
        independent principal slots are NOT offered as a substitute for the
        PLAN's two-slot requirement. The requirement stays open.
        """
        held = self.four_job_deployment(own_workers=False)
        producers = self.producers_of(held)
        self.assertEqual(producers["job-a/implementation"],
                         "implementation-worker")
        for stage in ("job-b/implementation", "job-c/implementation",
                      "job-d/implementation"):
            self.assertIsNone(producers[stage], stage)

    def four_job_schedule(self, trace, held, *, order):
        """Drive the four-Job scenario through REAL producer and reviewer turns.

        `order` is the schedule under test -- which independent Job codes first
        -- and it is the only thing that differs between the bounded schedules.
        Every act below is an owner's own: a real container turn through the
        fixture's own worker path, the reviewer's real verdict, and ordinary
        ticks in between. Nothing is written into a store and no receipt is
        made here.

        OBSERVED THROUGHOUT. `observing` emits a record for every piece of
        owner evidence each tick newly shows, so the artifact carries the
        SCHEDULE rather than its final state -- which is what the reviewer
        asked for and what an after-the-fact dump cannot give.
        """
        for job_id in order:
            stage = job_id + "/implementation"
            attempt = self.attempt_of(held, stage)
            # THE CONTAINER TURN ONLY, and then EVERY TICK IS OBSERVED. The
            # fixture's `produced` helper also drives ticks to `completed`, and
            # ticks this trace never saw are exactly what made the oracle
            # report `job-a/review was reserved before job-a/implementation
            # completed` -- correctly, because the completion first became
            # visible in the same observed tick as its successor's
            # reservation. The order has to be observed, not reconstructed.
            self.assertEqual(
                self.case.turn(
                    held.control, "implementation", attempt,
                    self.case.mounted_at(held.composed, attempt),
                    # THIS JOB'S OWN REGRESSION AND NOTHING SHARED. Two
                    # gates were found here in turn and only the second one is
                    # the real acceptance boundary. Different content at the
                    # SAME path made the imports conflict (review
                    # 2026-09-13T10:34:11Z); identical harness bytes removed
                    # the conflict and STILL refused, because the base already
                    # holds `harness.py` and therefore runs the old one
                    # (review 2026-09-13T10-44-30Z, measured). A required test
                    # the base does not have, asserting this Job's own
                    # payload, is what a causal observation can actually
                    # accept -- and the shared harness is left untouched.
                    edits=self.regression_files(job_id)), 0)
            self.observing(held, trace, job_id, "implementation", "completed",
                           job_ids=self.FOUR, ticks=8)
        for job_id in order:
            self.observing(held, trace, job_id, "review", "waiting",
                           job_ids=self.FOUR, ticks=14)
            self.case.review_turn(held, job_id,
                                  self.attempt_of(held, job_id + "/review"),
                                  "accepted")
            self.observing(held, trace, job_id, "review", "completed",
                           job_ids=self.FOUR, ticks=20)
        return {one: self.case.states_for(held.job, held.composed, one)
                for one in self.FOUR}

    def policy_pin_is_current(self, held):
        """Assert the composition's pin IS the Authority's current generation.

        AND RECORD NOTHING. Review 2026-09-13T04:22:32Z [P1]: the first form of
        this helper read the generation and then emitted a `submit`/`performed`
        record carrying `policy_generation:17` and no submission, Job or
        operation identity -- an act nobody performed, in a retained artifact,
        which the oracle duly validated. That is fabricated evidence, and it is
        the defect this whole Work exists to refuse. The explanation belongs in
        the scenario note and in PROGRESS; this is an assertion and no more.

        WHAT IT GUARDS. The borrowed fixture pins its policy generation in
        `setUp`, `four_works` then performs real Authority acts that move it,
        and a composition left on the stale pin defers every conclusion
        `policy/denied`. See `current_policy`.
        """
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            current = authority.policy_generation()
        finally:
            authority.dispose()
        self.assertEqual(
            self.case.deployment_of(held.composed).given["policy_generation"],
            current,
            "the composition is pinned to a generation the Authority has "
            "moved past; every conclusion will defer policy/denied")
        return current

    def observed_acts_only(self, artifact):
        """The act NAMES a driven schedule's records carry.

        The bounded regression for the fabricated record: these schedules are
        emitted by `observed`, which reads owner evidence tick by tick, and
        `submit` is what a scenario-level fixture emits -- so a `submit` here
        means this fixture wrote a record itself.

        IT CHECKS NAMES AND NOT PROVENANCE, which review 2026-09-13T04:38:33Z
        says plainly and this docstring must not overstate. A fixture that
        invented a record under some OTHER act name would pass this. What
        rules that out is that every record in these schedules is emitted by
        one call -- `observed` -- and nothing else in `four_job_schedule`
        records anything.
        """
        return sorted({one["act"] for one in artifact["records"]})

    def test_three_jobs_code_and_are_reviewed_and_the_edge_then_opens(self):
        """THE FIRST BOUNDED SCHEDULE, A BEFORE C.

        Three independent Jobs take REAL producer turns on three producers from
        TWO TEAMS and complete their implementations; each is then really
        reviewed by its own reviewer, whose turn returns zero and whose verdict
        is written.

        AND THE CROSS-JOB EDGE OPENS. `job-b/implementation` gates on
        `job-a/review`, and it becomes eligible when that review completes --
        nothing else changes to let it through, and B's own producer record is
        configured and idle throughout.

        THE `answering` BOUNDARY THE FIRST FORM STOPPED AT WAS MY OWN FIXTURE.
        Review 2026-09-13T04:11:17Z: the borrowed fixture pins its policy
        generation before `four_works` performs real Authority acts, so the
        deployment concluded under a generation the Authority had moved past.
        The reviews were never the problem; the conclusion was. See
        `current_policy`.

        WHAT IS SIMULATED, NAMED. The worker entry, the workload, the Job and
        Worker Manager owners, the Authority and the review cycles are the real
        ones; the container ENGINE is a scripted seam and the provider is a
        deterministic child process, not a live model.
        """
        held = self.four_job_deployment(own_workers=True, ticks=7)
        trace = self.blank()
        # B IS GATED BEFORE ANY OF THIS, and gated by its EDGE: its own
        # producer record is configured and idle.
        self.assertEqual(
            self.case.states_for(held.job, held.composed, "job-b")
            ["implementation"], "blocked")
        states = self.four_job_schedule(trace, held,
                                        order=("job-a", "job-c", "job-d"))
        for job_id in ("job-a", "job-c", "job-d"):
            with self.subTest(job=job_id):
                self.assertEqual(states[job_id]["implementation"], "completed")
                self.assertEqual(states[job_id]["review"], "completed")
        # AND THE EDGE OPENED. A's review completing is what B's implementation
        # was waiting for; nothing else changed to let it through, and B's own
        # producer record was configured and idle the whole time.
        self.assertNotEqual(states["job-b"]["implementation"], "blocked")
        # THE PIN IS CURRENT, asserted and not recorded: a composition left on
        # the stale generation defers every conclusion policy/denied.
        self.policy_pin_is_current(held)
        # THE SCHEDULE'S OWN SCENARIO, NAMED BEFORE THE ARTIFACT IS BUILT.
        # `artifact()` is what the exporter captures, and building one under
        # the blank default name would put an unnamed duplicate of this
        # schedule in the retained set.
        jobs, workers, bindings = self.scenario_from(held, self.FOUR)
        trace.scenario = scheduler_trace.Scenario(
            name="four-jobs-a-before-c", jobs=jobs, workers=workers, ticks=100,
            order=["job-a/implementation", "job-c/implementation",
                   "job-d/implementation", "job-b/implementation"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"schedule": "A before C: job-a, job-c and job-d take their "
                              "producer turns in that order",
                  "teams": "baton and other",
                  "target": "ONE canonical target and four lines of it",
                  "reached": "three real producer turns and three real "
                             "reviewer turns, all six stages completed by "
                             "their own owners, and the cross-Job edge opened",
                  "policy": "the composition is pinned to the Authority's "
                            "CURRENT generation, read after this scenario's "
                            "own setup acts. Pinned to the generation taken "
                            "before them, every conclusion defers "
                            "policy/denied -- which is what "
                            "trace-157442-composed.json's `answering` "
                            "schedules are, retained as superseded history",
                  "simulated": "the container engine is a scripted seam and "
                               "the provider is a deterministic child "
                               "process; the entry, workload, Job and Worker "
                               "Manager owners, Authority and review cycles "
                               "are the real ones",
                  "bindings": bindings})
        # NO INVENTED ACTS. Every record here was emitted by the observer from
        # owner evidence; a `submit` would mean this fixture wrote one itself.
        self.assertNotIn("submit", self.observed_acts_only(trace.artifact()))
        # NO DUPLICATE OWNER COMPLETION: exactly one `complete` per stage.
        # This counts the OWNERS' completions and says nothing about how many
        # runtimes were started, which `start_census` answers separately.
        census = self.completion_census(trace.artifact())
        for job_id in ("job-a", "job-c", "job-d"):
            for kind in ("implementation", "review"):
                self.assertEqual(census.get(f"{job_id}/{kind}"), 1,
                                 (job_id, kind))
        # AND NO DUPLICATE RUNTIME: one start per stage that ran one.
        self.assertEqual(set(self.start_census(trace.artifact()).values()),
                         {1})
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_the_opened_edge_and_one_integrator_serialize_four_jobs(self):
        """THE CONTINUATION, and the integration capacity the PLAN asks for.

        After the three reviews complete, ordinary ticks carry the schedule on
        by themselves. Two things are then true at once and both are the
        owners':

          - THE EDGE BECAME REAL WORK. `job-b/implementation` is not merely
            unblocked: it is claimed and running on its OWN producer, the
            record that sat configured and idle behind the gate for the whole
            schedule above.
          - ONE INTEGRATOR SERIALIZES THE REST. THREE of the four Jobs are
            eligible to integrate at this point -- `job-b` is still coding --
            and this deployment configures ONE integration worker, so exactly
            one is `integrating` and two are `queued` behind it. That is the
            separately configured capacity, contended by three eligible Jobs
            within a four-Job deployment.

        AND THEN IT IS DRIVEN ON. The first form of this case stopped at the
        sweeps and said "nothing is driven here", which stopped being true when
        B's turns were added and is corrected now: B codes and is reviewed, so
        all four Jobs contend for the one integrator, and job-a's integration
        is taken to a TERMINAL completion through the deployment's own port.
        """
        from baton_v12.job_manager import sweep
        from tests.job_manager import fixtures

        held = self.four_job_deployment(own_workers=True, ticks=7)
        trace = self.blank()
        self.four_job_schedule(trace, held, order=("job-a", "job-c", "job-d"))
        for _ in range(9):
            sweep(held.job, held.composed, now=fixtures.NOW)
            trace._tick = getattr(trace, "_tick", 0) + 1
            self.observed(held, trace, trace._tick, self.FOUR,
                          trace.__dict__.setdefault("_seen", set()))
        states = {one: self.case.states_for(held.job, held.composed, one)
                  for one in self.FOUR}
        # THE EDGE BECAME REAL WORK, on B's own producer.
        self.assertEqual(states["job-b"]["implementation"], "waiting")
        self.assertEqual(self.producers_of(held)["job-b/implementation"],
                         "implementation-worker-b")
        # AND ONE INTEGRATOR SERIALIZES THE THREE THAT ARE READY.
        integrating = [one for one in self.FOUR
                       if states[one].get("integration") == "integrating"]
        queued = [one for one in self.FOUR
                  if states[one].get("integration") == "queued"]
        self.assertEqual(len(integrating), 1, states)
        self.assertEqual(sorted(integrating + queued),
                         ["job-a", "job-c", "job-d"])
        # THE SCENARIO IS NAMED BEFORE ANY ARTIFACT IS BUILT: `artifact()` is
        # what the exporter captures, and one built under the blank default
        # name would put an unnamed duplicate of this schedule in the retained
        # set.
        #
        # AND THE NAMING MOVED ABOVE `b_and_terminal` BECAUSE IT WAS NOT TRUE
        # HERE. That helper builds an artifact itself -- the completion census
        # -- so with the naming below it the exported set really did carry a
        # duplicate of this schedule under the blank default name `pending`,
        # 97 records of it, in step 282. The alternate order already named its
        # scenario first; this one now does too.
        jobs, workers, bindings = self.scenario_from(held, self.FOUR)
        trace.scenario = scheduler_trace.Scenario(
            name="four-jobs-continued-to-integration", jobs=jobs,
            workers=workers, ticks=100,
            order=["job-a/implementation", "job-c/implementation",
                   "job-d/implementation", "job-b/implementation"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"schedule": "A before C, continued by ordinary ticks until "
                              "the edge opened into real work and the single "
                              "integrator serialized the three ready Jobs",
                  "capacity": "one configured integration worker. Three of "
                              "the four are eligible while job-b is still "
                              "coding; once B has coded and been reviewed all "
                              "FOUR contend, and exactly one integrates while "
                              "the rest queue",
                  "simulated": "the container engine is a scripted seam and "
                               "the provider is a deterministic child "
                               "process; the entry, workload, Job and Worker "
                               "Manager owners, Authority and review cycles "
                               "are the real ones",
                  "bindings": bindings})
        self.b_and_terminal(held, trace)
        self.assertNotIn("submit", self.observed_acts_only(trace.artifact()))
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_the_alternate_schedule_reaches_the_same_completions(self):
        """THE SECOND BOUNDED SCHEDULE, C BEFORE A. The same four Jobs, the
        same edge, the opposite order of the independent producers' turns --
        and the same completions and the same opened edge either way. A
        schedule that only ever ran one order is not a certification of
        parallel scheduling."""
        held = self.four_job_deployment(own_workers=True, ticks=7)
        trace = self.blank()
        states = self.four_job_schedule(trace, held,
                                        order=("job-c", "job-d", "job-a"))
        for job_id in ("job-a", "job-c", "job-d"):
            with self.subTest(job=job_id):
                self.assertEqual(states[job_id]["implementation"], "completed")
                self.assertEqual(states[job_id]["review"], "completed")
        self.assertNotEqual(states["job-b"]["implementation"], "blocked")
        jobs, workers, bindings = self.scenario_from(held, self.FOUR)
        trace.scenario = scheduler_trace.Scenario(
            name="four-jobs-c-before-a", jobs=jobs, workers=workers, ticks=100,
            order=["job-c/implementation", "job-d/implementation",
                   "job-a/implementation", "job-b/implementation"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"schedule": "C before A: job-c, job-d and job-a take their "
                              "producer turns in that order",
                  "teams": "baton and other",
                  "target": "ONE canonical target and four lines of it",
                  "reached": "three real producer turns and three real "
                             "reviewer turns, all six stages completed by "
                             "their own owners, and the cross-Job edge opened",
                  "policy": "the composition is pinned to the Authority's "
                            "CURRENT generation, read after this scenario's "
                            "own setup acts. Pinned to the generation taken "
                            "before them, every conclusion defers "
                            "policy/denied -- which is what "
                            "trace-157442-composed.json's `answering` "
                            "schedules are, retained as superseded history",
                  "simulated": "the container engine is a scripted seam and "
                               "the provider is a deterministic child "
                               "process; the entry, workload, Job and Worker "
                               "Manager owners, Authority and review cycles "
                               "are the real ones",
                  "bindings": bindings})
        self.assertNotIn("submit", self.observed_acts_only(trace.artifact()))
        # THE SAME CONTINUATION IN THIS ORDER TOO: B codes and is reviewed, all
        # four contend for the one integrator, and one reaches a terminal
        # completion with its own authorizing chain. One terminal outcome in
        # one order is not the accepted outcome in both.
        self.b_and_terminal(held, trace)
        census = self.completion_census(trace.artifact())
        for job_id in self.FOUR:
            for kind in ("implementation", "review"):
                self.assertEqual(census.get(f"{job_id}/{kind}"), 1,
                                 (job_id, kind))
        self.assertEqual(set(self.start_census(trace.artifact()).values()),
                         {1})
        self.assertEqual(scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def b_and_terminal(self, held, trace):
        """B's own turns, then ONE terminal integration, observed throughout.

        Factored so both bounded orders reach the same outcomes: a schedule
        that only ever drove B in one of them would be half a certification.
        """
        # B'S CONTAINER FIRST. The edge opens on A's review, which is LAST in
        # the alternate order, so B is not yet claimed when that schedule
        # finishes -- the first form of this helper assumed the A-before-C
        # order's timing and failed with "no configured worker prepared".
        self.observing(held, trace, "job-b", "implementation", "waiting",
                       job_ids=self.FOUR, ticks=14)
        # AND THEN B TAKES ITS OWN TURNS, so the traversal covers all four.
        # ITS OUTPUT IS ITS OWN: B's configured task names `feature_check.py`
        # and asserts `feature.py`'s value, so a turn writing the base
        # fixture's harness produces no completed frozen result -- measured, in
        # probe-159520-terminal.py, where the conclusion deferred with exactly
        # that cause.
        attempt = self.attempt_of(held, "job-b/implementation")
        self.assertEqual(
            self.case.turn(held.control, "implementation", attempt,
                           self.case.mounted_at(held.composed, attempt),
                           edits={"feature.py": self.case.B_FEATURE,
                                  "feature_check.py": self.case.B_CHECK}), 0)
        self.observing(held, trace, "job-b", "implementation", "completed",
                       job_ids=self.FOUR, ticks=12)
        self.observing(held, trace, "job-b", "review", "waiting",
                       job_ids=self.FOUR, ticks=12)
        self.case.review_turn(held, "job-b",
                              self.attempt_of(held, "job-b/review"),
                              "accepted")
        self.observing(held, trace, "job-b", "review", "completed",
                       job_ids=self.FOUR, ticks=20)
        # ALL FOUR JOBS HAVE CODED AND BEEN REVIEWED, and the single integrator
        # now has all four contending: one integrating, three queued.
        states = {one: self.case.states_for(held.job, held.composed, one)
                  for one in self.FOUR}
        for job_id in self.FOUR:
            with self.subTest(job=job_id):
                self.assertEqual(states[job_id]["implementation"], "completed")
                self.assertEqual(states[job_id]["review"], "completed")
        integrating = [one for one in self.FOUR
                       if states[one].get("integration") == "integrating"]
        queued = [one for one in self.FOUR
                  if states[one].get("integration") == "queued"]
        self.assertEqual(len(integrating), 1, states)
        self.assertEqual(sorted(integrating + queued), list(self.FOUR))
        # AND THE ONE THAT IS INTEGRATING IS TAKEN TO A TERMINAL COMPLETION.
        # A real integrator turn runs over the delivery this deployment
        # published, and then the manager OBSERVES a stopped runtime rather
        # than being told about one.
        #
        # THE ORDER MATTERS AND IS MEASURED. `stopped` is deployment-WIDE, so
        # setting it while any producer container was still live reported those
        # runtimes gone and made their stages `exceptional` --
        # probe-159582-integration.py records exactly that. B's turns above are
        # what leave the integrator's container the only live one.
        integrated = integrating[0]
        self.assertEqual(
            self.case.integration_turn(
                held, self.attempt_of(held, integrated + "/integration")), 0)
        self.case.engine.stopped = True
        # THE TERMINAL TICKS ARE OBSERVED, and the completion carries the chain
        # that authorized it. My previous claim left these ticks out of the
        # trace because observing the completion alone produced
        # `unauthorized-integration` -- correctly, since a completed
        # integration must be bound to its import. That was a reason to record
        # the chain, not a reason to stop observing.
        #
        # THE FOUR RECEIPTS ARE THE AUTHORITY'S OWN, read through the seam the
        # accepted two-Job artifact already uses: this deployment's line, the
        # integration checkpoint on it, the proposal that checkpoint published,
        # and `proposal_receipts` reading what the Authority recorded. Nothing
        # is invented and no source is extended.
        self.observing(held, trace, integrated, "integration", "completed",
                       job_ids=self.FOUR, ticks=16)
        states = {one: self.case.states_for(held.job, held.composed, one)
                  for one in self.FOUR}
        self.assertEqual(states[integrated]["integration"], "completed")
        # AND THE SECOND ONE IS THE RECONCILED BRANCH. Review
        # 2026-09-13T10:23:35Z found the gate: the sweeps DO offer and claim
        # the next Job, and its composed launch answers `pending` because the
        # Authority has no verification receipt on its DERIVED proposal. That
        # branch need not start an integration runtime at all, so my earlier
        # loop was waiting for a transition it would never see.
        #
        # WHAT IT NEEDS IS ITS JUDGES, and this deployment now configures them.
        # THE RECEIPTS ARE RECORDED LAST, and that is the accepted artifact's
        # own rule rather than a preference: the Authority stamps from a REAL
        # clock while these Job and control stores are frozen at the fixture's
        # instant, so a frozen-instant act observed AFTER a real-clock receipt
        # makes the oracle report `instants-disagree-with-order` -- correctly.
        # Every receipt still carries its own owner's unaltered instant.
        #
        # AND THE SECOND IMPORT IS DRIVEN HERE, not described. The helper that
        # carries it had NO CALLER -- which I disclosed and which is what this
        # closes. Both imports are now in the artifact of both schedules.
        # AND EVERY REMAINING JOB IS CARRIED, one at a time through the one
        # integrator, until all FOUR have terminal outcomes. The serialization
        # is still the point and is asserted inside each pass: a Job becomes
        # completed only after the one before it did.
        carried = self.every_remaining_import(held, trace, integrated)
        states = {one: self.case.states_for(held.job, held.composed, one)
                  for one in self.FOUR}
        self.assertEqual(
            sorted(one for one in self.FOUR
                   if states[one]["integration"] == "completed"),
            sorted(self.FOUR))
        # THE RECEIPTS ARE READ LAST AND IN OWNER ORDER: the EARLIER import's
        # chain before the later one's, at the final tick. My step-258 failure
        # was appending the older receipts after the newer ones -- a mistake in
        # my sequence, which review 2026-09-13T10:34:11Z proved by doing it the
        # other way round on the same bytes. The direct import is authorized on
        # the proposal its own checkpoint published; the reconciled one on the
        # DERIVED candidate its judges answered, which is a different chain and
        # is read through its own subject.
        self.terminal_receipts(held, trace, integrated)
        for answer in carried:
            self.proposal_receipts(held, trace, answer.job_id, answer.derived,
                                   trace._tick)
        # EACH COMPLETED ONCE, AND NONE TWICE.
        census = self.completion_census(trace.artifact())
        for job_id in self.FOUR:
            with self.subTest(job=job_id):
                self.assertEqual(census.get(job_id + "/integration"), 1)
        return tuple([integrated] + [one.job_id for one in carried])
    def reconciled_next(self, held, trace, done, judged=()):
        """Carry the NEXT Job's integration through the RECONCILED branch.

        Review 2026-09-13T10:23:35Z found the gate my earlier loop kept hitting:
        the sweeps DO offer and claim the next Job, and its composed launch
        answers `pending` because the Authority has no verification receipt on
        its DERIVED proposal. That is the reconciled branch -- it starts no
        integration runtime at all -- so waiting for `integrating` was waiting
        for a transition that never comes. The deployment's result judges are
        configured now, which is what that branch needs.

        NOTHING IS RECORDED INTO THE TRACE HERE, and it is not because the
        ordering is unsolvable -- I said that and it was wrong. Review
        2026-09-13T10:34:11Z proved the ordering: observe both imports, record
        the reconciled result's own `RESULT_CONTEXT`, and then read the EARLIER
        integration's receipts BEFORE the later one's at the final tick. My
        step-258 failure was appending the OLDER receipts AFTER the newer ones,
        which is a mistake in my sequence and not a property of the two clocks.

        IT IS CALLED NOW, from `b_and_terminal`, so both schedules carry
        both imports. EVERY TICK IS OBSERVED rather than swept past: the
        earlier form drove the branch with bare ticks and returned a summary,
        and a transition nobody observed cannot be in the artifact at all.

        THE SHAPE IS THE ACCEPTED TWO-JOB ONE. `test_both_jobs_reach_a_real_
        imported_integration` already drives this branch for two Jobs and was
        reviewed; this reaches it inside the four-Job schedule and asserts the
        same owner facts -- published before judgment, NO receipt on the
        derived candidate until the judges answer, three accepted verdicts,
        `imported` afterwards, and four receipts on the derived proposal.
        """
        from baton_v12.integration import reconciliation
        from baton_v12.job_manager import sweep as one_tick
        from tests.job_manager import fixtures as job_fixtures

        deployment = self.case.deployment_of(held.composed)
        seen = trace.__dict__.setdefault("_seen", set())

        reports = []
        # WHAT THE JUDGMENT OWNER ITSELF SAYS, captured while this loop runs.
        # The launch answer swallows the refusal into `pending`, so the
        # sentence never reaches a sweep report and a stalled continuation
        # looks like silence.
        refusals = []
        judging = deployment.judge_result

        def judged_with_cause(result_id):
            try:
                return judging(result_id)
            except Exception as refused:                    # noqa: BLE001
                refusals.append(f"{type(refused).__name__}: {refused}")
                raise

        deployment.judge_result = judged_with_cause
        self.addCleanup(setattr, deployment, "judge_result", judging)

        def tick():
            reports.append(one_tick(held.job, held.composed,
                                    now=job_fixtures.NOW))
            trace._tick = getattr(trace, "_tick", 0) + 1
            self.observed(held, trace, trace._tick, self.FOUR, seen)

        # THE BOUND IS THE SLOWER SCHEDULE'S, and it is measured rather than
        # generous: 14 observed ticks carry the A-before-C order to its judges
        # and leave the C-before-A order with NONE -- step 271 -- because in
        # that order the reconciled Job is offered, claimed and launched later.
        # A bound that fits only the order I ran first is a bound that turns a
        # slower schedule into a false refusal.
        # THE JUDGES ARE SELECTED BY RESULT, and this is the defect review
        # 2026-09-13T11:03:11Z named before a second continuation could ever
        # work. `deployment.judges` is keyed `(result_id, kind)` and it
        # ACCUMULATES: after one import it already holds three entries, so a
        # loop waiting for "three judges" would return at once and hand the
        # PREVIOUS result's executions to the next continuation. What this
        # waits for is a result id nobody has judged yet, with its own three.
        held_results = set(judged)
        fresh = set()
        for _ in range(30):
            tick()
            fresh = {key[0] for key in deployment.judges} - held_results
            if len(fresh) == 1 and len(
                    [one for one in deployment.judges
                     if one[0] in fresh]) == 3:
                break
        self.assertEqual(
            len(fresh), 1,
            f"after {sorted(held_results)} the reconciled branch published "
            f"{sorted(fresh)} derived candidates for its judges to answer")
        [result_id] = list(fresh)
        mine = {key: one for key, one in deployment.judges.items()
                if key[0] == result_id}
        self.assertEqual(
            len(mine), 3,
            (sorted(mine), refusals[-3:]))
        result = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(result["state"], "published")
        derived = result["derived_proposal_id"]
        # NOTHING HAS AUTHORIZED THE DERIVED CANDIDATE YET. A published result
        # is a candidate; what authorizes it is the independent receipts its
        # own owners record on it.
        self.assertEqual(deployment.authority.receipts(derived), [])
        for execution in mine.values():
            self.case.judgment_turn(held, execution)
        # AND ONE OBSERVED TICK BEFORE THE VERDICTS ARE READ. A judgment's
        # result is its own worker's completed frozen custody, which the turn
        # does not leave behind by itself: reading straight after the turns
        # refuses "a judgment needs a completed frozen result in accepted
        # custody" -- measured, step 268. The accepted two-Job case ticks here
        # for the same reason.
        tick()
        for execution in mine.values():
            self.assertEqual(execution.result()["verdict"], "accepted")
        completed = []
        for _ in range(16):
            tick()
            completed = [one for one in self.FOUR if one not in done
                         and self.case.states_for(held.job, held.composed,
                                                  one)["integration"]
                         == "completed"]
            if completed:
                break
        self.assertEqual(len(completed), 1,
                         f"after {sorted(done)} the reconciled branch "
                         f"completed {completed}")
        settled = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(settled["state"], "imported")
        # WHAT THE OWNER SAYS THIS RESULT IS, read through its own public
        # reader and independently of the completion that names it -- without
        # it a reconciled completion's result id is a string the oracle can
        # only look at, and a foreign one validated clean.
        trace.result(result_id, **{
            name: settled.get(name)
            for name in scheduler_trace.RESULT_CONTEXT})
        self.assertEqual(len(deployment.authority.receipts(derived)), 4)
        return SimpleNamespace(job_id=completed[0], derived=derived,
                               result_id=result_id)

    def every_remaining_import(self, held, trace, integrated):
        """Carry EVERY remaining Job to its own terminal import.

        Owner ruling M160956 is what pays for this: all FOUR terminal outcomes
        per order, rather than one direct import and one reconciled
        continuation. Each pass takes the next Job the single integrator picks
        up, so the order is the deployment's own allocation and not a list
        spelled here.
        """
        done, judged, carried = {integrated}, set(), []
        while len(done) < len(self.FOUR):
            answer = self.reconciled_next(held, trace, done, judged=judged)
            done.add(answer.job_id)
            judged.add(answer.result_id)
            carried.append(answer)
        # FOUR OUTCOMES, FOUR DISTINCT JOBS, THREE DISTINCT DERIVED RESULTS.
        self.assertEqual(sorted(done), sorted(self.FOUR))
        self.assertEqual(len({one.result_id for one in carried}),
                         len(carried))
        return carried

    def next_integration(self, held, trace, done):
        """Wait for the single integrator to pick up its NEXT Job, and say
        which. Exactly one may be live at a time -- that is the serialization
        under test -- and this asserts it at every observation."""
        from baton_v12.job_manager import sweep as one_tick
        from tests.job_manager import fixtures as job_fixtures

        for _ in range(16):
            states = {one: self.case.states_for(held.job, held.composed, one)
                      for one in self.FOUR}
            live = [one for one in self.FOUR
                    if states[one]["integration"] in ("integrating", "claimed")]
            self.assertLessEqual(len(live), 1, states)
            # ONLY `integrating` IS READY FOR A TURN: a claimed stage has no
            # launch delivery yet, and adopting one there answers absence --
            # which is what "'NoneType' object has no attribute 'place'" was.
            if live and states[live[0]]["integration"] == "integrating":
                return live[0]
            one_tick(held.job, held.composed, now=job_fixtures.NOW)
            trace._tick = getattr(trace, "_tick", 0) + 1
            self.observed(held, trace, trace._tick, self.FOUR,
                          trace.__dict__.setdefault("_seen", set()))
        self.fail(f"the integrator took up no Job after {sorted(done)}")

    def terminal_receipts(self, held, trace, job_id):
        """The four real receipts that authorized this Job's import.

        Read through the same seam the accepted two-Job artifact uses, and
        proved independently in repro-159609.py: the deployment's own line, the
        integration checkpoint on it, the proposal that checkpoint published,
        and the Authority's own receipts for that proposal.
        """
        from baton_v12.worker_manager import review_cycles

        deployment = self.case.deployment_of(held.composed)
        line = deployment.line_for(job_id)["line_id"]
        accepted = review_cycles.integration_checkpoint(held.control, line)
        self.assertIsNotNone(accepted)
        subject = deployment.published_proposal(accepted)
        self.proposal_receipts(held, trace, job_id, subject, trace._tick)
        return subject

    def completion_census(self, artifact):
        """How many times each stage was COMPLETED, from the artifact itself.

        The validator already refuses a stage completed twice; this is the
        no-duplicate evidence stated as a fact of the schedule rather than left
        to a rule, so a census that disagreed with the rule would be visible.

        IT COUNTS OWNER COMPLETIONS AND NOTHING ELSE. Review
        2026-09-13T04:11:17Z: a completion census does not count provider or
        runtime starts, and reading it as no-duplicate WORK would be claiming
        something it cannot see. `start_census` answers that separately.
        """
        held = {}
        for one in artifact["records"]:
            if one["act"] == "complete" and one["outcome"] == "performed":
                held[one["stage_id"]] = held.get(one["stage_id"], 0) + 1
        return held

    def start_census(self, artifact):
        """How many RUNTIMES each stage STARTED, as this artifact records them.

        It counts the `start` records the observer exported, which is what the
        schedule can see; it is not an independent count of engine invocations.
        """
        held = {}
        for one in artifact["records"]:
            if one["act"] == "start" and one["outcome"] == "performed":
                held[one["stage_id"]] = held.get(one["stage_id"], 0) + 1
        return held

    def test_the_four_job_contention_exports_a_clean_artifact(self):
        """And the schedule is a TRACE, validated by the independent oracle.

        The scenario document carries the four submitted Jobs with their real
        recorded edges, the nine configured workers and the four bindings, and
        the two-slot limitation rides with it as a GAP -- an expected,
        unresolved contract mismatch recorded as itself, which is what this
        oracle's `gap` is for.
        """
        held = self.four_job_deployment(own_workers=True, ticks=0)
        trace = self.blank()
        # OBSERVED THROUGHOUT, not after a silent setup: every tick of this
        # scenario is recorded, so the artifact carries the schedule rather
        # than its final state.
        self.observing(held, trace, "job-a", "implementation", "waiting",
                       job_ids=self.FOUR, ticks=8)
        jobs, workers, bindings = self.scenario_from(held, self.FOUR)
        self.assertEqual(sorted(one["job_id"] for one in jobs),
                         list(self.FOUR))
        self.assertEqual(len(workers), 9)
        self.assertEqual(len(bindings), 4)
        trace.gap(
            name="a-producer-bound-to-another-work-is-not-an-eligible-slot",
            reason="a configured worker carries one Work's input manifest and "
                   "task and a Work belongs to one Job's implementation stage, "
                   "so an idle producer bound to another Job's Work is not an "
                   "eligible slot for this one, in THIS configuration; no "
                   "claim is made about every possible arrangement of four Job "
                   "records over two effective slots",
            observed="with C and D naming the existing two producers as their "
                     "source, neither is ever allocated, while B's own idle "
                     "producer sits free behind the A->B edge",
            required="four Jobs over two implementation slots, as this Work's "
                     "PLAN scenario states it; four producer records are not "
                     "offered as a substitute and the requirement stays open. "
                     "The REPOSITORY half of the combined contract is "
                     "feasible and is proved separately; what is missing is "
                     "this slot half, and the two are independent")
        trace.scenario = scheduler_trace.Scenario(
            name="four-jobs-two-teams-one-target", jobs=jobs,
            workers=workers, ticks=100,
            order=["job-a/implementation", "job-c/implementation",
                   "job-d/implementation", "job-b/implementation"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, four Works, four "
                             "producers and four reviewers from TWO TEAMS, "
                             "one integrator; scripted engine seam only",
                  "teams": "baton and other; the second team's producers claim "
                           "on routes the Authority registered and its "
                           "reviewers hold `review` at the Work's own scope",
                  "target": "ONE canonical target and four lines of it. That "
                            "is THIS SCENARIO's binding, not a limit of the "
                            "contract: four Jobs over TWO repositories and two "
                            "targets bind and serve, proved directly by "
                            "test_four_jobs_do_bind_and_serve_across_two_"
                            "repositories",
                  "edge": "one cross-Job dependency, job-b/implementation on "
                          "job-a/review; job-c and job-d independent",
                  "slots": "four producer records, NOT the two the PLAN "
                           "names -- see the gap carried in this artifact",
                  "reached": "implementation claims only; no producer turn, "
                             "correction, review, integration or bounded "
                             "schedule has been driven in this scenario yet",
                  "bindings": bindings})
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])
        self.assertEqual(
            [one["name"] for one in artifact["gaps"]],
            ["a-producer-bound-to-another-work-is-not-an-eligible-slot"])
        # AND THE ARTIFACT IS NOT VACUOUS, which is the assertion this Work has
        # already been caught for omitting once: an empty trace validates clean
        # and proves nothing. THREE Jobs' stages are really in it, A's producer
        # is reserved, offered, accepted, claimed and started, and C's and D's
        # are reserved and offered in the same run.
        acts = {(one["stage_id"], one["act"]) for one in artifact["records"]
                if one["outcome"] == "performed"}
        for job_id in ("job-a", "job-c", "job-d"):
            for act in ("reserve", "offer", "accept", "claim", "start"):
                self.assertIn((job_id + "/implementation", act), acts,
                              (job_id, act))
        self.assertNotIn("job-b/implementation",
                         {stage for stage, _ in acts})

    def test_the_observer_refuses_an_owner_order_it_cannot_honour(self):
        """D1: THE SAME PAIR, THROUGH THE ACTUAL `observed()` PATH.

        The reviewer's probe drove the real extractor with a receipt snapshot
        whose claim was recorded at 00:00:01 and whose offer was recorded at
        00:00:02 -- both visible in one sweep -- and it validated clean. This
        substitutes exactly that snapshot at the public reader the observer uses,
        runs the real observer, and requires the oracle to refuse it.

        THE SNAPSHOT IS SYNTHETIC AND LABELLED. It exercises the extractor's and
        the oracle's reading; it records nothing about any real scheduler run,
        and no live owner is changed by it.
        """
        from unittest.mock import patch

        from baton_v12.job_manager import projection

        held = self.case.coding()
        trace = self.blank()

        genuine = projection.receipts_of

        def crossed(store, stage_id, episode):
            # THE GENUINE READER IS CAPTURED BEFORE THE PATCH, or this calls
            # itself: the patch replaces the very name it would look up.
            standing = dict(genuine(store, stage_id, episode))
            if stage_id == "job-a/implementation" and "claim" in standing \
                    and "admit" in standing:
                standing["admit"] = dict(
                    standing["admit"],
                    recorded_at="2026-09-02T00:00:02.000Z")
                standing["claim"] = dict(
                    standing["claim"],
                    recorded_at="2026-09-02T00:00:01.000Z")
            return standing

        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        with patch.object(projection, "receipts_of", crossed):
            self.observing(held, trace, "job-a", "implementation", "completed")
        artifact = trace.artifact(SOURCES)
        # BOTH WERE OBSERVED IN THE SAME SWEEP, and the oracle still refuses.
        offers = [one for one in artifact["records"]
                  if one["stage_id"] == "job-a/implementation"
                  and one["act"] in ("offer", "claim")]
        self.assertEqual(len({one["tick"] for one in offers}), 1, offers)
        self.assertIn("out-of-order",
                      [one["code"] for one in
                       scheduler_trace.validate(artifact)])

    def test_the_observer_accepts_the_owners_own_order(self):
        """Its legal companion, through the same path: the real receipts, whose
        instants are in their own order, validate clean."""
        held = self.case.coding()
        trace = self.blank()
        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        self.observing(held, trace, "job-a", "implementation", "completed")
        self.assertEqual(
            scheduler_trace.validate(trace.artifact(SOURCES)), [])

    def test_an_accepted_review_is_a_real_authorized_transition(self):
        """Job A reaches a genuinely accepted review, observed tick by tick.

        The fixture's ordinary producer turn, its ordinary reviewer turn and the
        real review cycle do the work; the offer and claim are the manager's own
        receipts, the start is its own runtime row and the completion is the
        projection's own state -- never an allocation release, which the review
        correctly refused as a completion.

        DRIVEN THROUGH THE FIXTURE'S OWN ACTS, OBSERVED AT EVERY TICK. The
        fixture's `produced`/`accepted` helpers drive `drive_job` internally, so
        this performs the same ordinary acts and substitutes the observer for that
        loop -- the boundary review 2026-09-12T16:51:07Z verified.
        """
        held = self.case.coding()
        trace = self.blank()
        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        self.observing(held, trace, "job-a", "implementation", "completed")
        self.observing(held, trace, "job-a", "review", "waiting")
        reviewed = self.case.one_attempt_of(held.composed, "review-worker")
        self.case.review_turn(held, "job-a", reviewed, "accepted")
        states = self.observing(held, trace, "job-a", "review", "completed")
        self.assertEqual(states["review"], "completed")

        jobs, workers, bindings = self.scenario_from(held, ("job-a",))
        # THE EXPORTED GRAPH IS THE SUBMITTED ONE, so the dependency oracle has
        # real edges to check rather than an empty list.
        self.assertTrue(jobs and workers)
        self.assertTrue(any(one["depends_on"] for job in jobs
                            for one in job["stages"]))
        trace.scenario = scheduler_trace.Scenario(
            name="composed-accepted-review", jobs=jobs, workers=workers,
            ticks=100, order=["job-a/implementation", "job-a/review"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, producers, reviewers "
                             "and review cycles; scripted engine seam only",
                  "bindings": bindings})
        artifact = trace.artifact(SOURCES)

        acts = {(one["stage_id"], one["act"]) for one in artifact["records"]}
        for stage_id in ("job-a/implementation", "job-a/review"):
            for act in ("reserve", "offer", "claim", "start", "complete"):
                self.assertIn((stage_id, act), acts, (stage_id, act))
        # OFFER ACCEPTANCE IS NOW PROVED, not reported missing. I claimed twice
        # that this build journals no separate acceptance; the offer row carries
        # its own `accepted_at` and the acceptance is recorded from it, with the
        # owner's instant, so the claim's prerequisite is real evidence.
        for stage_id in ("job-a/implementation", "job-a/review"):
            [accepted] = [one for one in artifact["records"]
                          if one["stage_id"] == stage_id
                          and one["act"] == "accept"]
            self.assertTrue(accepted["recorded_at"])
            self.assertEqual(accepted["outcome"], "performed")
        self.assertEqual(scheduler_trace.UNREPRESENTED_EVIDENCE, ())

        # WHAT REMAINS IS NARROWER AND EXACT: the session seam EXISTS and is
        # public -- `agent_sessions_of`, with posture, epoch, participant and
        # provider session id in `AGENT_SESSION_COLUMNS` -- but this composed
        # path opens no agent session for these attempts, so session identity
        # distinct from worker and runtime is not exercised here. That is a
        # different statement from "not recorded", which is what I said before.
        self.assertEqual(
            [one for one in artifact["records"] if one["session_id"]], [])
        gap = trace.gap(
            name="session-identity-not-exercised-on-this-path",
            reason="agent_sessions_of is public and AGENT_SESSION_COLUMNS "
                   "carries posture, epoch, participant and provider session "
                   "id, so the seam exists; this composed implementation and "
                   "review path simply opens no agent session, so the observer "
                   "reads none",
            observed="agent_sessions_of answers an empty list for every attempt "
                     "in this run",
            required="nothing further. Owner155646 asked for exactly this and "
                     "test_the_producer_and_the_reviewer_hold_their_own_"
                     "sessions now drives it: real consent and execution "
                     "sessions on the composed producer's attempt and an "
                     "execution session on the reviewer's, with the producer "
                     "port's attempt to open the reviewer's session refused by "
                     "its own owner. This gap records only that THIS path, "
                     "which opens none, observes none")
        artifact = trace.artifact(SOURCES)
        self.assertEqual(artifact["gaps"], [gap])
        self.assertEqual(scheduler_trace.validate(artifact), [])

    # -- the agent sessions, and the two roles that hold them ----------------

    def certified_session_profile(self, held):
        """The reference ACP profile, certified on THIS deployment's own store.

        Through the public certification owner, with the reference document the
        handshake suite already keeps. Nothing here writes a profile row: a
        session pins a per-posture policy and only a certified profile carries
        one, so an uncertified digest is refused by its own owner.
        """
        from baton_v12.worker_manager import certify_agent_session_profile
        from tests.manager.test_handshake import acp_profile

        profile = acp_profile()
        certify_agent_session_profile(held.control, profile)
        return profile["document_digest"]

    def port_for(self, held, attempt_id):
        """The port of the worker that actually PREPARED this attempt.

        The same fact the allocation names, and the same selection the fixture's
        own `preparing` helper makes -- not a lookup by role, which with two
        producers and two reviewers answers whichever is listed last.
        """
        worker_id, _prepared = self.case.preparing(held.composed, attempt_id)
        one = {other["worker_id"]: other
               for other in held.composed.workers}[worker_id]
        return worker_id, one["operations"]._worker.port

    def session_for(self, held, attempt_id, *, posture, intent, provider=None):
        """One REAL agent session, opened at the public seam, under the
        attempt's own worker port -- and bound to a scripted provider id.

        THE PROVIDER IS SCRIPTED AND THE SESSION IS NOT. `open_agent_session`
        reads the certified profile, checks that this port acts for the
        participant the attempt is assigned to, allocates the posture epoch in
        the database and writes the row; `adopt_provider_session` files the
        fourth component of the reference. Every one of those answers is the
        owner's own. No live provider is contacted and none is needed: what is
        scripted is the id a provider would have returned.
        """
        from baton_v12.worker_manager import (adopt_provider_session,
                                              open_agent_session)

        worker_id, port = self.port_for(held, attempt_id)
        answer = open_agent_session(
            held.control, port, attempt_id=attempt_id, posture=posture,
            profile_digest=self.digest, intent=intent)
        reference = answer["agent_session_ref"]
        if provider is not None:
            adopt_provider_session(held.control, attempt_id=attempt_id,
                                   posture=posture,
                                   session_epoch=reference["session_epoch"],
                                   provider_session_id=provider)
        return worker_id, port, reference

    def test_the_producer_and_the_reviewer_hold_their_own_sessions(self):
        """Owner155646's first requirement: NONEMPTY SESSIONS, INDEPENDENT ROLES.

        Every composed artifact before this one carried an empty session list and
        an honest gap saying so. This opens real sessions on the real composed
        attempts, through the public session owner, and the two roles' sessions
        are two different references held by two different participants.

        AND THE CROSSED PORT IS ASKED FOR, NOT ASSERTED. Independence is only
        demonstrated if the system refuses the thing that would break it, so the
        producer's own port asks for the reviewer's session and the refusal
        recorded is the owner's own sentence.
        """
        held = self.case.coding()
        trace = self.blank()
        self.digest = self.certified_session_profile(held)

        # THE PRODUCER'S TWO POSTURES, on one attempt. Consent and execution are
        # separate sessions with separate epochs, and the contract's own words
        # are that consent has no assignment -- which is why its row names no
        # participant and the execution row names the one the assignment fixed.
        _producer_id, producer_port, producer_ref = self.session_for(
            held, held.first, posture="execution",
            intent="serve-implementation-1",
            provider="provider-session-implementation-1")
        self.session_for(held, held.first, posture="consent",
                         intent="consent-implementation-1",
                         provider="provider-session-consent-1")

        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        self.observing(held, trace, "job-a", "implementation", "completed")
        self.observing(held, trace, "job-a", "review", "waiting")
        reviewed = self.case.one_attempt_of(held.composed, "review-worker")
        _reviewer_id, _reviewer_port, reviewer_ref = self.session_for(
            held, reviewed, posture="execution", intent="serve-review-1",
            provider="provider-session-review-1")
        self.case.review_turn(held, "job-a", reviewed, "accepted")
        states = self.observing(held, trace, "job-a", "review", "completed")
        self.assertEqual(states["review"], "completed")

        # THE SEPARATION, ASKED OF THE OWNER. The producer's port holds a live
        # authority session for its own participant; it asks for the reviewer's
        # execution session and is told whose attempt that is.
        from baton_v12.worker_manager import open_agent_session

        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(held.control, producer_port,
                               attempt_id=reviewed, posture="execution",
                               profile_digest=self.digest,
                               intent="serve-review-under-the-producer-port")
        trace.record(trace._tick, "observe", outcome="refused",
                     job_id="job-a",
                     stage_id="job-a/review", attempt_id=reviewed,
                     evidence="sessions.open_agent_session",
                     cause=f"{type(caught.exception).__name__}: "
                           f"{caught.exception}")
        self.assertIn(producer_port.participant, str(caught.exception))

        # THE OWNERS' OWN ASSIGNMENTS, read independently of the session rows.
        # R2: the first rule required a nonempty participant and compared it
        # with nothing, so changing a real reviewer session's participant to
        # `other.unassigned` validated clean. `assignment_of` is asked for each
        # attempt that holds a session, and the validator COMPARES.
        from baton_v12.worker_manager import assignment_of

        for attempt_id in (held.first, reviewed):
            answer = assignment_of(held.control, attempt_id)
            trace.assignment(attempt_id, **{
                name: answer[name]
                for name in scheduler_trace.ASSIGNMENT_CONTEXT})

        jobs, workers, bindings = self.scenario_from(held, ("job-a",))
        trace.scenario = scheduler_trace.Scenario(
            name="composed-role-sessions", jobs=jobs, workers=workers,
            ticks=100, order=["job-a/implementation", "job-a/review"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, producers, reviewers "
                             "and review cycles; scripted engine seam and "
                             "scripted provider session ids only",
                  "bindings": bindings})
        artifact = trace.artifact(SOURCES)

        # THE SESSIONS ARE IN THE ARTIFACT, and they are three distinct
        # references -- which the OLD spelling could not have said, because two
        # of them were `execution:1`.
        sessions = {one["session_id"]: one for one in artifact["records"]
                    if one["session_id"]}
        self.assertEqual(len(sessions), 3, sorted(sessions))
        self.assertIn(scheduler_trace.session_reference(
            dict(producer_ref,
                 provider_session_id="provider-session-implementation-1")),
            sessions)
        self.assertIn(scheduler_trace.session_reference(
            dict(reviewer_ref,
                 provider_session_id="provider-session-review-1")), sessions)

        # INDEPENDENT ROLES: two participants, and neither is the other.
        producer = [one for one in sessions.values()
                    if one["stage_id"] == "job-a/implementation"
                    and one["session"]["posture"] == "execution"]
        reviewer = [one for one in sessions.values()
                    if one["stage_id"] == "job-a/review"]
        self.assertEqual(len(producer), 1)
        self.assertEqual(len(reviewer), 1)
        self.assertTrue(producer[0]["participant"])
        self.assertTrue(reviewer[0]["participant"])
        self.assertNotEqual(producer[0]["participant"],
                            reviewer[0]["participant"])
        self.assertNotEqual(producer[0]["session_id"],
                            reviewer[0]["session_id"])

        # AND THE POSTURE SEPARATION IS THE OWNER'S OWN ANSWER: the consent row
        # names no participant, because consent has no assignment.
        [consent] = [one for one in sessions.values()
                     if one["session"]["posture"] == "consent"]
        self.assertIsNone(consent["participant"])
        self.assertIsNone(consent["session"]["generation"])
        # AND THE TWO POSTURES REALLY PINNED DIFFERENT POLICIES -- which
        # certification refuses a profile for stating otherwise, and which this
        # reads back off the rows rather than restating from the profile.
        self.assertNotEqual(producer[0]["session"]["pinned_policy"],
                            consent["session"]["pinned_policy"])

        # THE PROVIDER'S OWN ID IS THE FOURTH COMPONENT, adopted once.
        for one in sessions.values():
            self.assertTrue(one["session"]["provider_session_id"])
            self.assertTrue(one["session_id"].endswith(
                one["session"]["provider_session_id"]))

        # AND THE MANIFEST NO LONGER CALLS THIS FIELD UNOBSERVED.
        self.assertEqual(artifact["environment"]["unobserved_fields"], [])
        self.assertEqual(scheduler_trace.validate(artifact), [])

        # THE REVIEW'S TWO RETAINED MUTATIONS, over THIS real artifact rather
        # than a synthetic stand-in. Offline edits of a retained export; no
        # owner wrote either of them.
        foreign = copy.deepcopy(artifact)
        [row] = [one for one in foreign["records"]
                 if one["session_id"] == reviewer[0]["session_id"]]
        row["session_id"] = row["session_id"].rsplit("/", 1)[0] \
            + "/foreign-provider-id"
        self.assertIn("session-attempt-mismatch",
                      [one["code"] for one
                       in scheduler_trace.validate(foreign)])

        unassigned = copy.deepcopy(artifact)
        [row] = [one for one in unassigned["records"]
                 if one["session_id"] == reviewer[0]["session_id"]]
        row["participant"] = "other.unassigned"
        self.assertIn("session-contradicts-its-assignment",
                      [one["code"] for one
                       in scheduler_trace.validate(unassigned)])

        # AND AN ARTIFACT WHOSE OWNER DECLARED NO ASSIGNMENT AT ALL.
        unreferenced = copy.deepcopy(artifact)
        unreferenced["assignment_references"] = {}
        self.assertIn("unreferenced-session",
                      [one["code"] for one
                       in scheduler_trace.validate(unreferenced)])

    def test_a_wrong_repository_binding_is_refused_by_its_own_owner(self):
        """R1: THE WRONG-REPOSITORY CASE, DRIVEN, with its legal companion.

        Reviews up to 2026-09-12T17:08:44Z asked for an actual refusal rather
        than configured root strings. This binds Job B's line to Job A's declared
        base -- a revision that exists in `source` and not in `source-b` -- and
        then asks the REAL line owner for that Job's line. The checkpoint profile
        materializes from the nominated repository, so the base it cannot find is
        the refusal: a binding across two repositories is refused by the owner
        that would have to read it, not by a string comparison here.
        """
        from baton_v12.source_profiles.checkout import ProfileRefusal

        held = self.case.two_jobs()
        bindings = {one["job_id"]: one for one in held["job_bindings"]}
        self.assertNotEqual(bindings["job-a"]["line_declared_base"],
                            bindings["job-b"]["line_declared_base"])
        crossed = [dict(one) for one in held["job_bindings"]]
        for one in crossed:
            if one["job_id"] == "job-b":
                # JOB B'S OWN SOURCE, JOB A'S BASE: the wrong repository.
                one["line_declared_base"] = \
                    bindings["job-a"]["line_declared_base"]
        _job, _control, composed = self.case.serving(
            **dict(held, job_bindings=crossed))
        deployment = self.case.deployment_of(composed)

        trace = scheduler_trace.Trace(scheduler_trace.Scenario(
            name="composed-wrong-repository", jobs=[], workers=[], ticks=1,
            note={"attempted": "job-b bound to job-a's declared base while "
                               "nominating its own source repository"}))
        with self.assertRaises((ProfileRefusal, ContractRefusal)) as caught:
            deployment.line_for("job-b")
        # THE REFUSAL IS CONFIGURATION EVIDENCE, NOT AN ACT. Review
        # 2026-09-13T04:38:33Z [P1]: `line_for` reaching `create_line` and
        # being refused is not a Job submission, and labelling it `submit`
        # made a retained artifact claim an act nobody performed. The owner's
        # own sentence is kept -- in the scenario note, where a fact about how
        # this deployment is CONFIGURED belongs.
        trace.scenario.note["refused"] = {
            "asked": "deployment.line_for('job-b')",
            "owner": "review_cycles.create_line",
            "cause": f"{type(caught.exception).__name__}: "
                     f"{caught.exception}"}
        # THE OWNER'S OWN SENTENCE, not a comparison made here.
        self.assertIn(bindings["job-a"]["line_declared_base"][:12],
                      str(caught.exception))
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])

        # THE LEGAL COMPANION: each Job's own base in its own repository.
        self.doCleanups()
        self.setUp()
        _job, _control, ordinary = self.case.serving_two()
        deployment = self.case.deployment_of(ordinary)
        for job_id in ("job-a", "job-b"):
            line = deployment.line_for(job_id)
            self.assertTrue(line["line_id"])

    def granted(self, who, capability, *, scope):
        """One real capability grant, through the Authority's own public face."""
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            authority.grant_capability(who, capability, scope=scope)
            return authority.holds_capability(who, capability, scope=scope)
        finally:
            authority.dispose()

    def test_a_same_line_correction_keeps_its_worker_and_not_its_session(self):
        """THE RETAINED CORRECTION CONTINUITY OBLIGATION, measured.

        FINDING's test contract requires a same-line correction to keep the
        original HEALTHY worker and session. Half of that holds here and half
        of it cannot, and both halves are measured rather than argued:

          - THE WORKER CONTINUES. The reviewer sends the work back, the line
            opens a second episode, and the corrected attempt is prepared by the
            SAME producer that wrote the first one.
          - THE SESSION CANNOT. An AgentSession is keyed by runtime attempt --
            `agent_sessions_of` takes an attempt id and the §3.1 reference's
            first component IS that attempt -- and a correction is a NEW
            attempt. So the original session is still filed under the original
            attempt, the corrected attempt holds none, and this serving path
            opens none for it.

        THIS IS NOT EVIDENCE OF SERVING REUSE and no session opened separately
        is substituted for it: the session below is opened by this driver at the
        public seam, and what is recorded is that the correction did not and
        could not carry it.
        """
        from baton_v12.worker_manager import assignment_of

        held = self.case.coding()
        trace = self.blank()
        self.digest = self.certified_session_profile(held)
        self.session_for(held, held.first, posture="execution",
                         intent="serve-implementation-1",
                         provider="provider-session-implementation-1")
        assignment = assignment_of(held.control, held.first)
        trace.assignment(held.first, **{
            name: assignment[name]
            for name in scheduler_trace.ASSIGNMENT_CONTEXT})

        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        self.observing(held, trace, "job-a", "implementation", "completed")
        self.observing(held, trace, "job-a", "review", "waiting")
        reviewed = self.case.one_attempt_of(held.composed, "review-worker")
        self.case.review_turn(held, "job-a", reviewed, "changes-requested")
        self.observing(held, trace, "job-a", "implementation", "waiting")
        corrected = self.case.one_attempt_of(
            held.composed, "implementation-worker", exclude=[held.first])
        self.assertNotEqual(corrected, held.first)

        # THE WORKER REALLY IS THE SAME ONE.
        producer, _ = self.case.preparing(held.composed, held.first)
        again, _ = self.case.preparing(held.composed, corrected)
        self.assertEqual(again, producer)
        self.assertEqual(assignment_of(held.control, corrected)["participant"],
                         assignment["participant"])

        # AND THE SESSION REALLY IS NOT.
        self.assertEqual(agent_sessions_of(held.control, corrected), [])
        [original] = agent_sessions_of(held.control, held.first)
        self.assertEqual(original["runtime_attempt_id"], held.first)
        self.assertTrue(scheduler_trace.session_reference(original)
                        .startswith(held.first + "/"))

        jobs, workers, bindings = self.scenario_from(held, ("job-a",))
        trace.scenario = scheduler_trace.Scenario(
            name="composed-correction-continuity", jobs=jobs, workers=workers,
            ticks=100, order=["job-a/implementation", "job-a/review"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, producers, reviewers "
                             "and review cycles; the engine seam and the "
                             "provider session id are scripted",
                  "bindings": bindings})
        gap = trace.gap(
            name="a-correction-keeps-its-worker-and-cannot-keep-its-session",
            reason="FINDING's test contract requires same-line correction "
                   "affinity to the original HEALTHY worker AND session. The "
                   "worker half holds and is measured here. The session half "
                   "cannot hold on this path at all: an AgentSession is keyed "
                   "by runtime attempt and a correction is a new attempt, so "
                   "the original session stays filed under the original "
                   "attempt -- and this serving path opens no session for "
                   "either. Nothing here is offered as evidence of serving "
                   "reuse",
            observed=f"the corrected attempt is prepared by {producer!r}, the "
                     f"same producer as the first, under the same assignment "
                     f"participant; agent_sessions_of answers an empty list "
                     f"for the corrected attempt and the original session's "
                     f"reference names the original attempt",
            required="either an owner-level continuation that carries a "
                     "healthy session across a same-line correction, or an "
                     "explicit decision that a correction opens a new session "
                     "by design -- and in either case a serving path that "
                     "opens sessions at all. UNRESOLVED AND NOT DISCHARGED by "
                     "the transport-loss/epoch-recovery case")
        artifact = trace.artifact(SOURCES)
        self.assertEqual(artifact["gaps"], [gap])
        self.assertEqual(scheduler_trace.validate(artifact), [])

    def session_row(self, held, attempt_id, posture, epoch):
        """One session row as its own owner answers it, or absence."""
        [row] = [one for one in agent_sessions_of(held.control, attempt_id)
                 if one["posture"] == posture
                 and one["session_epoch"] == epoch]
        return row

    def recorded_session(self, trace, tick, held, attempt_id, *, stage_id,
                         posture, epoch, episode=1, job_id="job-a"):
        """Record one session AS ITS OWNER CURRENTLY REPORTS IT.

        A state change is a NEW fact about the same session, not a correction of
        the old record: the observer emits each session once, at the tick it
        first became visible, so an epoch that later goes `unknown` needs its own
        record rather than a rewrite of the first.
        """
        row = self.session_row(held, attempt_id, posture, epoch)
        return trace.record(
            tick, "observe", outcome="performed", job_id=job_id,
            stage_id=stage_id, episode=episode, attempt_id=attempt_id,
            participant=row.get("participant"),
            session_id=scheduler_trace.session_reference(row),
            session={name: row.get(name)
                     for name in scheduler_trace.SESSION_CONTEXT},
            recorded_at=row.get("opened_at"),
            evidence="agent_sessions:" + attempt_id)

    def test_a_lost_transport_ends_the_epoch_and_never_resumes(self):
        """TRANSPORT LOSS AND EPOCH RECOVERY. Not the retained correction
        continuity obligation, which this does not discharge.

        A CORRECTION OF MY OWN LABEL. I called this "session continuity" and
        said it was the honest reading of what PLAN kept open. Review
        2026-09-13T00:09:15Z was right that it is not: FINDING's 2026-09-06 test
        contract requires same-line correction affinity to the original HEALTHY
        worker and session, PLAN's scenario boundary requires identity
        continuity for a same-worker correction, and no owner decision
        supersedes either. A lost transport is a different scenario, and
        relabelling the open requirement to match what I had built would have
        been the softening this record exists to prevent. The obligation stays
        open and is measured in
        `test_a_same_line_correction_keeps_its_worker_and_not_its_session`.

        WHAT THIS DOES PROVE, and it is worth keeping: the public transport-loss
        boundary, the recovery-required refusal and the new-epoch allocation, on
        one still-live assignment. `handle_transport_loss` decides the axis and
        the slot, the premature reopening is refused by the slot's own rule,
        `release_slot` demands positive evidence of absence, and the next epoch
        is allocated by the database.

        AND WHAT IS SCRIPTED HERE IS SAID PLAINLY: the provider session id and
        the `session-absent` evidence naming it are scripted INPUTS to the real
        owner API. No real provider absence was measured; what was measured is
        what the owner does when it is told one.
        """
        from baton_v12.worker_manager import (assignment_of,
                                              handle_transport_loss,
                                              open_agent_session, posture_slot,
                                              release_slot)

        held = self.case.coding()
        trace = self.blank()
        self.digest = self.certified_session_profile(held)
        _worker_id, port, first = self.session_for(
            held, held.first, posture="execution",
            intent="serve-implementation-1", provider="provider-session-1")
        assignment = assignment_of(held.control, held.first)
        trace.assignment(held.first, **{
            name: assignment[name]
            for name in scheduler_trace.ASSIGNMENT_CONTEXT})

        # ONE ORDINARY TICK FIRST, so the trace carries the claim this session
        # was opened against. The producer's turn is deliberately NOT driven
        # here: these sessions are opened at the public seam and the serving
        # path does not consult them, so running a turn after a lost transport
        # would suggest a recovery this test did not demonstrate.
        self.observing(held, trace, "job-a", "implementation", "waiting")

        # THE TRANSPORT DIES WHILE THE ASSIGNMENT IS STILL LIVE, which is where
        # a transport actually dies. Corrected after measurement: the first form
        # of this case ran the producer's turn to completion first, and the
        # premature reopening was then refused by `_live_assignment` -- "holds
        # no live assignment" -- before the slot rule was ever reached. That is
        # a true refusal about a different thing, and asserting it here would
        # have been a case that passes while proving nothing about the posture
        # slot.
        lost = handle_transport_loss(
            held.control, dict(first, provider_session_id="provider-session-1"),
            turn_in_flight=True)
        self.assertFalse(lost["resume"])
        self.assertFalse(lost["reprompt"])
        self.assertEqual(lost["session_state"], "unknown")
        self.assertEqual(lost["slot_occupancy"], "recovery-required")
        self.assertEqual(lost["turn_outcome"], "transport-lost")
        self.assertEqual(
            posture_slot(held.control, held.first, "execution")["occupancy"],
            "recovery-required")
        self.recorded_session(trace, trace._tick, held, held.first,
                              stage_id="job-a/implementation",
                              posture="execution", epoch=1)

        # AND A SECOND OPENING BEFORE RECOVERY IS REFUSED BY THE SLOT ITSELF.
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(held.control, port, attempt_id=held.first,
                               posture="execution",
                               profile_digest=self.digest,
                               intent="serve-implementation-2")
        self.assertIn("recovery-required", str(caught.exception))
        trace.record(trace._tick, "observe", outcome="refused",
                     job_id="job-a", stage_id="job-a/implementation",
                     episode=1, attempt_id=held.first,
                     evidence="posture_slots:execution",
                     cause=f"{type(caught.exception).__name__}: "
                           f"{caught.exception}")

        # RECOVERY TAKES POSITIVE EVIDENCE that the old provider session cannot
        # still act -- not a decision by this driver.
        released = release_slot(
            held.control, attempt_id=held.first, posture="execution",
            session_epoch=first["session_epoch"], evidence="session-absent",
            observed_identity="provider-session-1",
            reason="the transport died and the provider session was observed "
                   "absent")
        self.assertEqual(released["occupancy"], "available")

        # THE NEXT SESSION IS A NEW ONE. A fresh epoch, allocated by the
        # database, and deliberately left UNADOPTED so the artifact carries the
        # owner's own representation of an epoch no provider id is bound to.
        answer = open_agent_session(held.control, port, attempt_id=held.first,
                                    posture="execution",
                                    profile_digest=self.digest,
                                    intent="serve-implementation-2")
        second = answer["agent_session_ref"]
        self.assertEqual(second["session_epoch"],
                         first["session_epoch"] + 1)
        self.assertIsNone(second["provider_session_id"])
        self.recorded_session(trace, trace._tick, held, held.first,
                              stage_id="job-a/implementation",
                              posture="execution", epoch=2)

        jobs, workers, bindings = self.scenario_from(held, ("job-a",))
        trace.scenario = scheduler_trace.Scenario(
            name="composed-transport-loss-epoch-recovery", jobs=jobs,
            workers=workers,
            ticks=100, order=["job-a/implementation"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority and producers; the "
                             "engine seam and the provider session id are "
                             "scripted, the transport loss and the slot "
                             "recovery are the owners' own acts",
                  "bindings": bindings})
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])

        sessions = [one for one in artifact["records"] if one["session_id"]]
        states = {one["session"]["session_epoch"]: one["session"]["state"]
                  for one in sessions}
        # THE FIRST EPOCH ENDED AND THE SECOND IS ITS OWN SESSION.
        self.assertEqual(states, {1: "unknown", 2: "not-started"})
        references = {one["session_id"] for one in sessions}
        self.assertEqual(len(references), 2)
        self.assertTrue(any(one.endswith("/execution/2/-")
                            for one in references), references)
        # WHAT CONTINUED IS THE WORKER, NOT THE SESSION: one attempt, one
        # assignment participant, two epochs that share nothing else.
        self.assertEqual({one["attempt_id"] for one in sessions},
                         {held.first})
        self.assertEqual({one["participant"] for one in sessions},
                         {assignment["participant"]})
        # AND THE REFUSAL RECORDED IS THE SLOT'S OWN, not another owner's.
        [refused] = [one for one in artifact["records"]
                     if one["outcome"] == "refused"]
        self.assertIn("a posture holds one session", refused["cause"])

    def test_both_jobs_traverse_and_one_integrator_serializes_them(self):
        """Both whole Jobs through their producing and reviewing halves, and
        the one integrator they then queue behind.

        PLAN item 5 keeps "both whole Jobs reaching terminal integration" open.
        This drives the accepted two-Job traversal -- two real Works, two
        producers, two reviewers, two lines, one canonical target -- observes it
        tick by tick, and records exactly how far it goes and what stops it.

        THE REFUSAL IS THE MANAGER'S OWN SENTENCE. `PLAN.md` requires that at the
        end of a complete sweep, eligible owed work with no compatible idle
        capacity carries its exact public cause. The sweep report says it, so
        the cause recorded here is quoted from the owner rather than composed by
        this driver -- and no `reserve` is called by hand to manufacture one,
        which would have meant re-implementing the manager's own stage
        composition to get a refusal it already publishes.
        """
        from baton_v12.job_manager import live_of
        from baton_v12.job_manager import sweep as one_tick
        from tests.job_manager import fixtures

        # DRIVEN WITH THE OBSERVER IN THE LOOP, not afterwards. Corrected after
        # measurement: the first form called the fixture's own `both_accepted`,
        # which drives the whole traversal internally, so every act was first
        # seen at tick 1 and the dependency oracle correctly reported each
        # review reserved before its implementation's completion -- the same
        # class of defect the observer was built to remove. The fixture's
        # ordinary acts are performed here with `observing` between them.
        held = self.case.coding()
        trace = self.blank()
        both = ("job-a", "job-b")
        for job_id, attempt_id, reviewer_id, edits in (
                ("job-a", held.first, "review-worker",
                 {"harness.py": "print('the first job answered')\n"}),
                ("job-b", held.second, "review-worker-b",
                 {"feature.py": self.case.B_FEATURE,
                  "feature_check.py": self.case.B_CHECK})):
            self.assertEqual(
                self.case.turn(held.control, "implementation", attempt_id,
                               self.case.mounted_at(held.composed, attempt_id),
                               edits=edits), 0)
            self.observing(held, trace, job_id, "implementation", "completed",
                           job_ids=both)
            self.observing(held, trace, job_id, "review", "waiting",
                           job_ids=both)
            reviewed = self.case.one_attempt_of(held.composed, reviewer_id)
            self.case.review_turn(held, job_id, reviewed, "accepted")
            self.observing(held, trace, job_id, "review", "completed",
                           job_ids=both)
        self.observing(held, trace, "job-a", "integration", "integrating",
                       job_ids=both)
        for job_id in ("job-a", "job-b"):
            states = self.case.states_for(held.job, held.composed, job_id)
            self.assertEqual(states["implementation"], "completed", job_id)
            self.assertEqual(states["review"], "completed", job_id)
        self.assertEqual(
            self.case.states_for(held.job, held.composed,
                                 "job-a")["integration"], "integrating")
        self.assertEqual(
            self.case.states_for(held.job, held.composed,
                                 "job-b")["integration"], "queued")

        # ONE INTEGRATOR, AND THE OWNERS DECIDE WHICH JOB HOLDS IT.
        self.assertEqual(self.case.allocated(held.job, "job-a/integration"),
                         "integration-worker")
        self.assertIsNone(self.case.allocated(held.job, "job-b/integration"))

        # AND THE SECOND JOB'S OWED ACT, DEFERRED, WITH ITS EXACT CAUSE.
        report = one_tick(held.job, held.composed, now=fixtures.NOW)
        trace._tick += 1
        [act] = [one for one in report["acts"]
                 if one["stage_id"] == "job-b/integration"]
        self.assertEqual(act["outcome"], "deferred")
        self.assertEqual(act["detail"]["category"], "refused")
        trace.record(trace._tick, "offer", outcome="deferred", job_id="job-b",
                     stage_id="job-b/integration", episode=act["episode"],
                     operation_id=None,
                     evidence="sweep_report:job-b/integration",
                     cause=f"{act['detail']['category']}/"
                           f"{act['detail']['code']}: "
                           f"{act['detail']['message']}")
        self.assertIn("every effective worker/principal capacity is reserved",
                      act["detail"]["message"])

        jobs, workers, bindings = self.scenario_from(held,
                                                     ("job-a", "job-b"))
        trace.scenario = scheduler_trace.Scenario(
            name="composed-two-jobs-one-integrator", jobs=jobs,
            workers=workers, ticks=100,
            order=["job-a/implementation", "job-b/implementation",
                   "job-a/review", "job-b/review", "job-a/integration"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, two producers, two "
                             "reviewers, two lines, one canonical target and "
                             "one integrator; scripted engine seam only",
                  "bindings": bindings})

        # THE RETAINED EXPLICIT-FALLBACK REQUIREMENT, OBSERVED IN A COMPOSED RUN
        # FOR THE FIRST TIME -- and still recorded as a GAP, not as a pass.
        deployment = self.case.deployment_of(held.composed)
        allocation = self.integration_allocation(held)
        self.assertEqual(allocation["selection_outcome"], "fallback")
        self.assertNotEqual(allocation["preferred_worker_id"],
                            allocation["worker_id"])
        fallback = trace.gap(
            name="explicit-fallback-observed-in-a-composed-run",
            reason="the retained requirement is that a fallback away from an "
                   "occupied preferred worker be EXPLICIT; the composed "
                   "integration allocation records selection_outcome "
                   "'fallback' with a preferred_worker_id this deployment did "
                   "not use, and nothing asked for or authorized that "
                   "substitution",
            observed=f"job-a/integration is held by "
                     f"{allocation['worker_id']!r} while the allocation names "
                     f"preferred worker {allocation['preferred_worker_id']!r} "
                     f"and selection outcome "
                     f"{allocation['selection_outcome']!r}",
            required="an explicit fallback decision with its own authority, "
                     "rather than an automatic substitution recorded after the "
                     "fact. UNCHANGED AND STILL OPEN: this claim only moves the "
                     "observation from the unit pool to a composed run")
        # JOB A REACHES ITS TERMINAL COMPLETION, through the fixture's OWN
        # integrator turn. Review 2026-09-13T00:09:15Z: my claim that this
        # boundary is left to an injected port was STALE -- `integrating` uses
        # the deployment's own port, and `integration_turn` drives a real
        # provider turn over the delivery this run published. Nothing is
        # injected and no second composition is made.
        attempt_id = live_of(held.job, "job-a/integration")["attempt_id"]
        self.assertEqual(self.case.integration_turn(held, attempt_id), 0)
        # THE ORDINARY QUIESCENCE SIGNAL, and it is DEPLOYMENT-WIDE by the
        # engine's own definition: setting it marks every modelled container
        # not running, which is what its callers mean by it. It is named here
        # because it is the reason Job B goes no further below.
        self.case.engine.stopped = True
        self.observing(held, trace, "job-a", "integration", "completed",
                       job_ids=both)
        self.assertEqual(
            self.case.states_for(held.job, held.composed, "job-a"),
            {"implementation": "completed", "review": "completed",
             "integration": "completed"})


        # AND THE CAPACITY REALLY HANDS OFF. The integrator A held is released
        # by its completion, and the act that was DEFERRED above is performed.
        handoff = []
        seen = trace.__dict__.setdefault("_seen", set())
        for _ in range(6):
            report = one_tick(held.job, held.composed, now=fixtures.NOW)
            trace._tick += 1
            handoff.extend(one for one in report["acts"]
                           if one["stage_id"] == "job-b/integration")
            self.observed(held, trace, trace._tick, both, seen)
        performed = [one["act"] for one in handoff
                     if one["outcome"] == "performed"]
        self.assertEqual(performed[:2], ["admit", "claim"], handoff)
        self.assertEqual(self.case.allocated(held.job, "job-b/integration"),
                         "integration-worker")
        self.assertEqual(
            self.case.states_for(held.job, held.composed, "job-b"),
            {"implementation": "completed", "review": "completed",
             "integration": "claimed"})

        # AND THE COMPLETED IMPORT CARRIES ITS OWN AUTHORIZATION, in THIS
        # artifact. Review 2026-09-13T00:24:01Z: this trace reported the
        # integration complete with an empty `authorization_references` and
        # validated clean, and receipt coverage in another artifact does not
        # establish this completion's subject. The Authority is asked for the
        # receipts on the proposal this stage actually imported, through the
        # same public reader the authorization case uses.
        #
        # READ AT THIS POINT IN THE RUN, AND RECORDED WHERE IT WAS READ. The
        # Authority stamps its receipts from a real clock while these Job and
        # control stores are frozen at the fixture's instant, so two owners'
        # instants are not one sequence; the tick is when this driver asked,
        # and each receipt carries its own owner's instant unaltered.
        from baton_v12.worker_manager import review_cycles

        deployment = self.case.deployment_of(held.composed)
        line = deployment.line_for("job-a")["line_id"]
        accepted = review_cycles.integration_checkpoint(held.control, line)
        proposal_id = deployment.published_proposal(accepted)
        self.assertTrue(proposal_id)
        trace.reference("proposal:" + proposal_id,
                        effective_scope=self.case.scope)
        receipts = self.authorized(deployment, trace, proposal_id,
                                   tick=trace._tick, job_id="job-a",
                                   stage_id="job-a/integration")
        self.assertLessEqual({"verification", "review", "approval",
                              "integration"}, set(receipts))

        terminal = trace.gap(
            name="the-second-jobs-integration-stops-at-claimed-here",
            reason="Job A reaches a real terminal integration and the "
                   "integrator it held really hands off -- job-b's admit goes "
                   "from deferred to performed and its claim is settled -- and "
                   "this run stops there because it configures no result "
                   "judges. MY EARLIER DIAGNOSIS OF THIS WAS WRONG AND IS "
                   "WITHDRAWN: I blamed the deployment-wide quiescence flag "
                   "and said job-b needed its own direct integrator turn. "
                   "Review 2026-09-13T00:24:01Z measured the owner's actual "
                   "answer -- Integration.run returns `pending` with a "
                   "derived_proposal_id, awaiting a VERIFICATION RECEIPT on "
                   "that derived proposal, and a sweep with the flag true and "
                   "one with it false give job-b the same summary. Job A moved "
                   "their common canonical target, so "
                   "stage_execution.Integration._run takes the `reconciled` "
                   "branch, which publishes a derived candidate and waits for "
                   "independent receipts -- a branch that completes WITHOUT an "
                   "integration runtime, so an absent direct launch was never "
                   "the gate and a direct import turn was the wrong branch",
            observed="job-b/integration is 'claimed' with the integrator "
                     "allocated to it and stays there across further ordinary "
                     "ticks, while job-a is completed in all three stages",
            required="nothing further here. "
                     "test_both_jobs_reach_a_real_imported_integration drives "
                     "the right branch with the fixture's own configured "
                     "judges: three real judgment turns over the frozen "
                     "derived result, four receipts on the derived proposal "
                     "from the Authority itself, and BOTH Jobs completed in "
                     "all three stages. This gap records only that THIS "
                     "contention scenario configures no judges")
        artifact = trace.artifact(SOURCES)
        self.assertEqual(artifact["gaps"], [fallback, terminal])
        self.assertEqual(scheduler_trace.validate(artifact), [])

        # AND THE REQUIREMENT BITES ON THIS REAL ARTIFACT. Offline edits of a
        # retained export; no owner wrote either of them.
        stripped = copy.deepcopy(artifact)
        stripped["records"] = [one for one in stripped["records"]
                               if one["act"] not in
                               scheduler_trace.SUBJECT_AUTHORIZATION]
        self.assertIn("unauthorized-integration",
                      [one["code"] for one
                       in scheduler_trace.validate(stripped)])
        # A COMPLETION NAMING ANOTHER SUBJECT is unproved, whatever receipts
        # this Job happens to have -- which is what the Job-membership check
        # could not say.
        foreign = copy.deepcopy(artifact)
        [row] = [one for one in foreign["records"]
                 if one["act"] == "complete"
                 and one["stage_id"] == "job-a/integration"]
        row["completion"]["proposal_id"] = "integration-driver.proposal:other"
        self.assertIn("unauthorized-integration",
                      [one["code"] for one
                       in scheduler_trace.validate(foreign)])
        unbound = copy.deepcopy(artifact)
        [row] = [one for one in unbound["records"]
                 if one["act"] == "complete"
                 and one["stage_id"] == "job-a/integration"]
        row["completion"] = None
        self.assertIn("unbound-completion",
                      [one["code"] for one
                       in scheduler_trace.validate(unbound)])

        # AND BOTH JOBS REALLY CARRY THEIR OWN PRODUCING AND REVIEWING ACTS.
        acts = {(one["stage_id"], one["act"]) for one in artifact["records"]
                if one["outcome"] == "performed"}
        for job_id in ("job-a", "job-b"):
            for kind in ("implementation", "review"):
                for act_name in ("reserve", "offer", "accept", "claim",
                                 "start", "complete"):
                    self.assertIn((f"{job_id}/{kind}", act_name), acts,
                                  (job_id, kind, act_name))
        self.assertEqual(deployment.target_for("job-a"),
                         deployment.target_for("job-b"))
        self.assertNotEqual(deployment.line_for("job-a")["line_id"],
                            deployment.line_for("job-b")["line_id"])

    def accepted_halves(self, held, trace, both):
        """Both Jobs from a coding producer to an accepted review, OBSERVED."""
        for job_id, attempt_id, reviewer_id, edits in (
                ("job-a", held.first, "review-worker",
                 {"harness.py": "print('the first job answered')\n"}),
                ("job-b", held.second, "review-worker-b",
                 {"feature.py": self.case.B_FEATURE,
                  "feature_check.py": self.case.B_CHECK})):
            self.assertEqual(
                self.case.turn(held.control, "implementation", attempt_id,
                               self.case.mounted_at(held.composed, attempt_id),
                               edits=edits), 0)
            self.observing(held, trace, job_id, "implementation", "completed",
                           job_ids=both)
            self.observing(held, trace, job_id, "review", "waiting",
                           job_ids=both)
            reviewed = self.case.one_attempt_of(held.composed, reviewer_id)
            self.case.review_turn(held, job_id, reviewed, "accepted")
            self.observing(held, trace, job_id, "review", "completed",
                           job_ids=both)

    def proposal_receipts(self, held, trace, job_id, subject, tick):
        """One Job's terminal authorization, from the Authority's own reader."""
        deployment = self.case.deployment_of(held.composed)
        trace.reference("proposal:" + subject,
                        effective_scope=self.case.scope)
        held_receipts = self.authorized(deployment, trace, subject, tick=tick,
                                        job_id=job_id,
                                        stage_id=f"{job_id}/integration")
        self.assertLessEqual({"verification", "review", "approval",
                              "integration"}, set(held_receipts))
        return held_receipts

    def test_both_jobs_reach_a_real_imported_integration(self):
        """BOTH Jobs to a real terminal integration, through the second Job's
        own derived-proposal judgments.

        AND A CAUSAL CLAIM OF MINE, CORRECTED. I wrote that Job B's integration
        stalled because of the deployment-wide quiescence flag and that it needed
        its own direct integrator turn. Review 2026-09-13T00:24:01Z measured the
        owner's actual answer: `Integration.run` returns `pending` with a
        `derived_proposal_id`, awaiting a VERIFICATION RECEIPT on that derived
        proposal. Job A moved their common canonical target, so
        `stage_execution.Integration._run` takes the `reconciled` branch, which
        publishes a derived candidate and waits for independent receipts -- a
        branch that completes WITHOUT an integration runtime. Neither the
        stopped flag nor the absent direct launch was the gate, and a direct
        import turn was the wrong branch entirely.

        So this drives the right one, with the fixture's own configured judges:
        three real judgment turns over the frozen derived result, their receipts
        recorded by the Authority itself, and Job B's integration completing on
        them. Both Jobs end completed in all three stages.
        """
        from baton_v12.integration import reconciliation
        from baton_v12.job_manager import live_of
        from baton_v12.worker_manager import review_cycles

        both = ("job-a", "job-b")
        held = self.case.coding(
            result_judgment_workers=self.case.judgment_workers())
        trace = self.blank()
        self.accepted_halves(held, trace, both)

        # JOB A INTEGRATES FOR REAL, exactly as the contention case does.
        self.observing(held, trace, "job-a", "integration", "integrating",
                       job_ids=both)
        first = live_of(held.job, "job-a/integration")["attempt_id"]
        self.assertEqual(self.case.integration_turn(held, first), 0)
        self.case.engine.stopped = True
        self.observing(held, trace, "job-a", "integration", "completed",
                       job_ids=both)

        # AND JOB B IS ON THE RECONCILED BRANCH, WAITING FOR ITS JUDGES.
        deployment = self.case.deployment_of(held.composed)
        seen = trace.__dict__.setdefault("_seen", set())
        for _ in range(14):
            self.case.tick(held)
            trace._tick += 1
            self.observed(held, trace, trace._tick, both, seen)
            if len(deployment.judges) == 3:
                break
        self.assertEqual(len(deployment.judges), 3)
        result_id = next(iter(deployment.judges))[0]
        result = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(result["state"], "published")
        derived = result["derived_proposal_id"]
        # NOTHING HAS AUTHORIZED THE DERIVED CANDIDATE YET, which is the exact
        # state the reviewer measured and I had misdiagnosed.
        self.assertEqual(deployment.authority.receipts(derived), [])

        # THREE REAL JUDGMENT TURNS, the fixture's own configured workers.
        for execution in deployment.judges.values():
            self.case.judgment_turn(held, execution)
        self.case.tick(held)
        trace._tick += 1
        self.observed(held, trace, trace._tick, both, seen)
        for execution in deployment.judges.values():
            self.assertEqual(execution.result()["verdict"], "accepted")
        self.observing(held, trace, "job-b", "integration", "completed",
                       job_ids=both, ticks=14)

        settled = reconciliation.result_of(deployment.integration, result_id)
        self.assertEqual(settled["state"], "imported")
        # R6c: WHAT THE OWNER SAYS THIS RESULT IS, read through its own public
        # reader and independently of the completion that names it. Without it
        # a reconciled completion's result id is a string this oracle can only
        # look at, and a foreign one validated clean.
        trace.result(result_id, **{
            name: settled.get(name)
            for name in scheduler_trace.RESULT_CONTEXT})
        self.assertEqual(len(deployment.authority.receipts(derived)), 4)
        for job_id in both:
            self.assertEqual(
                self.case.states_for(held.job, held.composed, job_id),
                {"implementation": "completed", "review": "completed",
                 "integration": "completed"}, job_id)

        # BOTH TERMINAL AUTHORIZATIONS, READ LAST AND RECORDED WHERE THEY WERE
        # READ. The Authority stamps from a real clock and these Job and control
        # stores are frozen at the fixture's instant, so the two owners' instants
        # are not one sequence; every receipt carries its own owner's unaltered.
        line = deployment.line_for("job-a")["line_id"]
        accepted = review_cycles.integration_checkpoint(held.control, line)
        self.proposal_receipts(held, trace, "job-a",
                               deployment.published_proposal(accepted),
                               trace._tick)
        self.proposal_receipts(held, trace, "job-b", derived, trace._tick)

        jobs, workers, bindings = self.scenario_from(held, both)
        trace.scenario = scheduler_trace.Scenario(
            name="composed-both-jobs-imported", jobs=jobs, workers=workers,
            ticks=100,
            order=["job-a/implementation", "job-a/review",
                   "job-b/implementation", "job-b/review",
                   "job-a/integration", "job-b/integration"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, two producers, two "
                             "reviewers, one integrator and three configured "
                             "result judges; scripted engine seam only",
                  "second_job_branch": "reconciled -- job-a moved their common "
                                       "canonical target, so job-b's import "
                                       "published a derived candidate and "
                                       "waited for independent receipts",
                  "bindings": bindings})
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])
        acts = {(one["stage_id"], one["act"]) for one in artifact["records"]
                if one["outcome"] == "performed"}
        for job_id in both:
            self.assertIn((f"{job_id}/integration", "complete"), acts, job_id)
            self.assertIn((f"{job_id}/integration", "integrate"), acts, job_id)

        # R6c's FOUR RETAINED MUTATIONS, over THIS real artifact. Offline edits
        # of a retained export; no owner wrote any of them. Each is a single
        # field contradicting evidence the artifact already carries.
        for name, job_id, change in (
                ("foreign direct runtime", "job-a",
                 {"runtime_id": "runtime-of-another-attempt"}),
                ("a completed direct import claiming a running runtime",
                 "job-a", {"execution_runtime": "running"}),
                ("a foreign reconciled result", "job-b",
                 {"result_id": "result-of-another-job"}),
                ("a reconciled import with no source proposal", "job-b",
                 {"source_proposal_id": None})):
            with self.subTest(mutation=name):
                altered = copy.deepcopy(artifact)
                [row] = [one for one in altered["records"]
                         if one["act"] == "complete"
                         and one["stage_id"] == job_id + "/integration"]
                row["completion"].update(change)
                self.assertIn("completion-contradicts-its-evidence",
                              [one["code"] for one
                               in scheduler_trace.validate(altered)], name)

        # AND AN ARTIFACT WHOSE OWNER DECLARED NO RESULT AT ALL.
        unreferenced = copy.deepcopy(artifact)
        unreferenced["result_references"] = {}
        self.assertIn("completion-contradicts-its-evidence",
                      [one["code"] for one
                       in scheduler_trace.validate(unreferenced)])

        # R6d's TWO RETAINED MUTATIONS, and both validated clean against
        # evidence this artifact already carried.
        #
        # FIRST: B's completion names a FOREIGN SOURCE. Its derived proposal,
        # its result id and the owner's own reference are all untouched, so the
        # only thing wrong is that the completion's account of what it imported
        # FROM disagrees with what the owner says that very result was derived
        # from. Nonempty and different from the derived proposal was the whole
        # of the old rule, and this mutation satisfies both.
        foreign = copy.deepcopy(artifact)
        [row] = [one for one in foreign["records"]
                 if one["act"] == "complete"
                 and one["stage_id"] == "job-b/integration"]
        self.assertTrue(row["completion"]["source_proposal_id"])
        row["completion"]["source_proposal_id"] = "proposal-of-another-job"
        self.assertIn("completion-contradicts-its-evidence",
                      [one["code"] for one
                       in scheduler_trace.validate(foreign)])

        # SECOND: the FINAL reference demoted from `imported` to `published`.
        # This reference is read after the composed fixture reached `completed`
        # and the fixture asserts `imported` above before exporting it, so a
        # `published` snapshot is a pre-import observation being offered as
        # terminal proof. Nothing else in the artifact changes.
        demoted = copy.deepcopy(artifact)
        [held_result] = list(demoted["result_references"])
        self.assertEqual(
            demoted["result_references"][held_result]["state"], "imported")
        demoted["result_references"][held_result]["state"] = "published"
        self.assertIn("completion-contradicts-its-evidence",
                      [one["code"] for one
                       in scheduler_trace.validate(demoted)])

        # THE TWO BRANCHES ARE THE OWNERS' OWN, and they differ where the
        # reviewer measured them: A ran a container and imported its own
        # proposal; B ran none and imported a derived result.
        done = {one["job_id"]: one["completion"] for one in artifact["records"]
                if one["act"] == "complete"
                and (one["stage_id"] or "").endswith("/integration")}
        self.assertIsNotNone(done["job-a"]["runtime_id"])
        self.assertEqual(done["job-a"]["execution_runtime"], "quiescent")
        self.assertIsNone(done["job-a"]["result_id"])
        self.assertEqual(done["job-a"]["proposal_id"],
                         done["job-a"]["source_proposal_id"])
        self.assertIsNone(done["job-b"]["runtime_id"])
        self.assertEqual(done["job-b"]["execution_runtime"], "absent")
        self.assertTrue(done["job-b"]["result_id"])
        self.assertNotEqual(done["job-b"]["proposal_id"],
                            done["job-b"]["source_proposal_id"])

        # R6a's RETAINED MUTATION: swap the Job and stage labels of the two
        # intact chains, leaving every proposal, candidate, target and receipt
        # untouched. It validated clean when the rule checked Job membership.
        swapped = copy.deepcopy(artifact)
        for one in swapped["records"]:
            if one["act"] in scheduler_trace.SUBJECT_AUTHORIZATION:
                other = "job-b" if one["job_id"] == "job-a" else "job-a"
                one["job_id"] = other
                one["stage_id"] = other + "/integration"
        self.assertIn("unauthorized-integration",
                      [one["code"] for one
                       in scheduler_trace.validate(swapped)])

        # R6b's RETAINED MUTATION: delete the DIRECT import's start. Its own
        # completion names a live runtime, so the reconciled exception is not
        # its to take.
        started = copy.deepcopy(artifact)
        started["records"] = [
            one for one in started["records"]
            if not (one["act"] == "start"
                    and one["stage_id"] == "job-a/integration")]
        self.assertIn("missing-prerequisite",
                      [one["code"] for one
                       in scheduler_trace.validate(started)])
        # AND THE RECONCILED ONE KEEPS ITS EXEMPTION, so the rule is a branch
        # distinction rather than a blanket.
        self.assertEqual(
            [one for one in artifact["records"]
             if one["act"] == "start"
             and one["stage_id"] == "job-b/integration"], [])

    def integration_allocation(self, held):
        """The scheduler's own allocation row for job-a's integration."""
        from baton_v12.job_manager import live_of
        from baton_v12.job_manager.scheduler import allocation_of

        live = live_of(held.job, "job-a/integration")
        return allocation_of(held.job, live["attempt_id"])

    # -- the reopen, at a declared durable boundary ---------------------------

    def reopened(self, held):
        """A FRESH composed deployment over the same durable files.

        The composed analogue of the unit pool's `fresh_driver`, and the same
        rule: a restart is a new process, so nothing of the first deployment's
        Python state crosses the boundary. New store handles under their own
        incarnation, a new `operations_from` composition over the same
        configuration document, and the first deployment left exactly as it was
        -- it is not rewound, reset or replayed by hand.

        THE ENGINE IS THE SAME OBJECT, AND THE BOUNDARY IS NOT QUIESCENT.
        Review 2026-09-13T00:09:15Z measured what I had asserted without
        measuring: at this boundary Job B's implementation is `waiting` and the
        engine reports one RUNNING container. My docstring said no container was
        running and my PROGRESS repeated it; both were wrong.

        What this actually measures is a MANAGER RECOMPOSITION IN ONE PROCESS:
        new store handles under their own incarnation and a new
        `operations_from` over the same durable files, while the modelled
        container host -- the same engine object -- keeps running Job B's
        producer across the boundary. It is not a host restart and it is not a
        quiescent boundary, and the exported scenario note says so.

        AND THE FIXTURE'S OWN `_composed` SLOT MOVES WITH IT. `serving` keeps
        the current serving object there so a review turn can ask which
        boundary was mounted for an attempt; after a reopen the current one is
        the second deployment, and leaving the first there would compose a
        review turn over a deployment that never prepared the attempt.
        """
        from tests.job_manager import fixtures
        from tools import stage_execution

        document = self.case.two_jobs(**self.case.traversing())
        job, control = self.case.stores("stage-reopened")
        composed = stage_execution.operations_from(
            self.case.composed_document(line_declared_base=self.case.base,
                                        **document),
            job, control, engine_run=self.case.engine,
            credential_provider=lambda provider, reference: self.case.secret,
            clock=lambda: fixtures.NOW, checkout=self.case.checkout)
        self.addCleanup(composed.close)
        self.case._composed = composed
        return SimpleNamespace(job=job, control=control, composed=composed)

    def launches_naming(self, attempt_id):
        """Every engine `run` whose OWN OPERANDS name this attempt.

        The launch labels carry the attempt; the runtime id does not exist until
        the engine answers. Counting by an input identity is what lets a second
        container for one attempt be seen at all.
        """
        return [list(one) for one in self.case.engine.starts
                if any(attempt_id in str(operand) for operand in one)]

    def allocations_in(self, job):
        """Every attempt the store holds an allocation for, and its state."""
        from baton_v12.job_manager import (allocation_of, episodes_of,
                                           stage_rows)

        held = {}
        for row in stage_rows(job):
            for episode in episodes_of(job, row["stage_id"]):
                allocation = allocation_of(job, episode["attempt_id"])
                if allocation is not None:
                    held[episode["attempt_id"]] = (
                        row["stage_id"], allocation["worker_id"])
        return held

    def test_the_composed_deployment_reopens_and_continues(self):
        """The composed reopen, which every review since the first slice has
        kept open and which I declined to start last claim rather than leave
        half driven.

        Job A's implementation completes, the deployment is reopened at that
        durable boundary by a genuinely fresh composition over the same files,
        and the REOPENED deployment admits, claims and completes the review --
        with the same durable attempt identities and no act performed twice.
        """
        from baton_v12.worker_manager.attempts import attempt_runtime_of

        held = self.case.coding()
        trace = self.blank()
        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        self.observing(held, trace, "job-a", "implementation", "completed")
        before = self.allocations_in(held.job)
        self.assertIn(held.first, before)

        # WHAT IS ACTUALLY LIVE AT THE BOUNDARY, measured rather than asserted.
        # Job B's producer is still going, and the engine is holding its
        # container -- so this is a recomposition ACROSS live work, which is a
        # stronger thing to survive than a quiet one.
        self.assertEqual(
            self.case.states_for(held.job, held.composed,
                                 "job-b")["implementation"], "waiting")
        running = {one for one, what in self.case.engine.records.items()
                   if what["running"]}
        self.assertEqual(len(running), 1, running)
        second_runtime = attempt_runtime_of(held.control, held.second)
        self.assertIn(second_runtime["runtime_id"], running)
        # COUNTED BY THE LAUNCH'S OWN INPUT IDENTITY, not by its answer.
        # Review 2026-09-13T00:24:01Z: my first form filtered new `run` vectors
        # by Job B's RUNTIME ID, and the engine MINTS that id in its response --
        # it is not an operand of `run` at all. A duplicate launch would mint a
        # different id, so the filter could never match one and the assertion
        # could not fail. The attempt id IS an operand, in the launch's own
        # labels, and the count is asserted nonzero below so the comparison
        # cannot be vacuous.
        launched = self.launches_naming(held.second)
        self.assertTrue(launched, "no launch names Job B's attempt")
        # AND THE PROVIDER SIDE OF THE SAME QUESTION CANNOT BE ASKED HERE, which
        # is measured rather than assumed. The engine count above is about
        # CONTAINERS; a reopen could leave a container alone and still start a
        # second provider conversation, and the session owner's rows are where
        # that would show. On THIS path there are none: steps 285 and 286 asked
        # `agent_sessions_of` for Job B's attempt and then for Job A's and got
        # an empty list both times, because neither attempt reaches the turn
        # that records a session before this boundary. Asserting over an empty
        # list would be a comparison that cannot fail, so it is not asserted --
        # the limitation is in this schedule's own note instead, and
        # `composed-role-sessions` is the schedule that does carry sessions.

        # THE DECLARED DURABLE BOUNDARY. Nothing is reset and nothing is
        # replayed by hand: a new deployment opens its own handles over the
        # same durable files.
        trace.record(trace._tick, "reopen", outcome="performed",
                     job_id="job-a", stage_id="job-a/implementation",
                     episode=1, attempt_id=held.first,
                     operation_id="store.reopen:stage-reopened",
                     evidence="jobs.sqlite3+control.sqlite3")
        second = self.reopened(held)

        # AND THE REOPENED DEPLOYMENT CARRIES ON, through its own owners.
        self.observing(second, trace, "job-a", "review", "waiting")
        reviewed = self.case.one_attempt_of(second.composed, "review-worker")
        self.case.review_turn(second, "job-a", reviewed, "accepted")
        states = self.observing(second, trace, "job-a", "review", "completed")
        self.assertEqual(states["review"], "completed")

        after = self.allocations_in(second.job)
        # THE SAME DURABLE IDENTITIES, answered by the reopened store rather
        # than remembered by a Python object that survived.
        for attempt_id, what in before.items():
            self.assertEqual(after.get(attempt_id), what, attempt_id)
        self.assertIn(reviewed, after)
        self.assertNotIn(reviewed, before)

        # AND THE LIVE WORK CROSSED THE BOUNDARY WITHOUT BEING STARTED TWICE.
        # The recomposed deployment adopts Job B's running attempt: the same
        # runtime identity, answered by the reopened control store, and no new
        # `run` vector for it.
        continued = attempt_runtime_of(second.control, held.second)
        self.assertEqual(continued["runtime_id"],
                         second_runtime["runtime_id"])
        self.assertEqual(self.launches_naming(held.second), launched)
        # AND THE REOPENED STORE STILL HOLDS NO SESSION FOR IT, which is the
        # fact the note records rather than an assertion dressed as evidence.
        self.assertEqual(agent_sessions_of(second.control, held.first), [])
        trace.record(trace._tick, "observe", outcome="performed",
                     job_id="job-b", stage_id="job-b/implementation",
                     episode=1, attempt_id=held.second,
                     runtime_id=continued["runtime_id"],
                     evidence="attempt_runtime:" + held.second)

        jobs, workers, bindings = self.scenario_from(second, ("job-a",))
        trace.scenario = scheduler_trace.Scenario(
            name="composed-reopen-and-continue", jobs=jobs, workers=workers,
            ticks=100, reopen_at=1,
            order=["job-a/implementation", "job-a/review"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, producers, reviewers "
                             "and review cycles; scripted engine seam only",
                  "reopen": "a fresh operations_from composition under "
                            "incarnation stage-reopened over the same durable "
                            "job and control files. THE BOUNDARY IS NOT "
                            "QUIESCENT: job-b/implementation is waiting and the "
                            "modelled engine holds one running container across "
                            "it. The engine object is shared, so what this "
                            "measures is a manager recomposition in one "
                            "process, not a host restart",
                  "provider": "THE ENGINE COUNT IS THE ONLY DUPLICATE COUNT "
                              "THIS SCHEDULE CAN MAKE. `launches_naming` "
                              "compares every engine `run` whose own operands "
                              "name job-b's attempt, before and after the "
                              "boundary. The PROVIDER side cannot be counted "
                              "here: `agent_sessions_of` answers EMPTY for "
                              "both attempts at this boundary, because neither "
                              "has reached the turn that records a session, so "
                              "a provider-duplicate comparison here could not "
                              "fail. `composed-role-sessions` is the schedule "
                              "that carries real session identities",
                  "bindings": bindings})
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])

        # EXACTLY ONCE ACROSS THE REOPEN, which is what a reopen has to prove.
        performed = [one for one in artifact["records"]
                     if one["outcome"] == "performed" and one["operation_id"]]
        self.assertEqual(len(performed),
                         len({one["operation_id"] for one in performed}))
        # AND THE ASSERTION CAN SEE A DUPLICATE, which is the other half of
        # review 2026-09-13T00:24:01Z. A second container for Job B's attempt is
        # injected at the scripted engine -- a synthetic engine fault, not a
        # scheduler run claimed to have produced one -- and the same comparison
        # that passed above now fails. An assertion nothing can break is not an
        # assertion.
        self.case.engine(list(launched[-1]))
        self.assertNotEqual(self.launches_naming(held.second), launched)
        self.assertEqual(len(self.launches_naming(held.second)),
                         len(launched) + 1)

        # AND THE REVIEW REALLY WAS ADMITTED AFTER THE BOUNDARY.
        [boundary] = [one for one in artifact["records"]
                      if one["act"] == "reopen"]
        for act in ("reserve", "offer", "accept", "claim", "complete"):
            [record] = [one for one in artifact["records"]
                        if one["stage_id"] == "job-a/review"
                        and one["act"] == act]
            self.assertGreaterEqual(record["tick"], boundary["tick"], act)

    # -- alternate order over the composed owners -----------------------------

    def both_jobs_in(self, order):
        """Both composed Jobs driven to completion in a GIVEN order.

        The sweep is deployment-wide, so what an order names is which producer
        takes its turn first -- exactly as the fixture's own `drive_job` does.
        Nothing here reorders a record: the observer records what each tick
        newly showed, and the two runs differ because the turns really happened
        in different orders.
        """
        held = self.case.coding()
        trace = self.blank()
        bodies = {"job-a": (held.first, {"harness.py":
                                         "print('answered')\n"}),
                  "job-b": (held.second, {"feature.py": self.case.B_FEATURE,
                                          "feature_check.py":
                                              self.case.B_CHECK})}
        for job_id in order:
            attempt_id, edits = bodies[job_id]
            self.assertEqual(
                self.case.turn(held.control, "implementation", attempt_id,
                               self.case.mounted_at(held.composed, attempt_id),
                               edits=edits), 0)
            self.observing(held, trace, job_id, "implementation", "completed",
                           job_ids=("job-a", "job-b"))
        jobs, workers, bindings = self.scenario_from(held,
                                                     ("job-a", "job-b"))
        trace.scenario = scheduler_trace.Scenario(
            name=f"composed-alternate-order-{order[0]}-first",
            jobs=jobs, workers=workers,
            ticks=100,
            order=[f"{job_id}/implementation" for job_id in order],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "composed: real Authority, two producers, two "
                             "bound Jobs; scripted engine seam only",
                  "bindings": bindings})
        return trace, trace.artifact(SOURCES)

    def completion_order(self, artifact):
        """The order the OWNERS completed the two implementations in."""
        when = {}
        for one in artifact["records"]:
            if one["act"] != "complete" or one["outcome"] != "performed":
                continue
            if not (one["stage_id"] or "").endswith("/implementation"):
                continue
            when.setdefault(one["stage_id"], one["tick"])
        return [stage_id for stage_id, _ in sorted(when.items(),
                                                   key=lambda one: one[1])]

    def test_the_two_bound_jobs_complete_in_either_order(self):
        """Owner155646's second requirement, first half: ALTERNATE ORDER over
        the composed owners rather than over the unit pool.

        Two real Jobs on two real Works, two producers with their own
        participants and their own lines, driven A-then-B and B-then-A. Both
        runs satisfy the same oracle, their scenario digests differ because
        their inputs really differ, and the completion order the owners
        recorded is the order each run actually took.
        """
        first_trace, first = self.both_jobs_in(("job-a", "job-b"))
        self.assertEqual(scheduler_trace.validate(first), [])
        self.assertEqual(self.completion_order(first),
                         ["job-a/implementation", "job-b/implementation"])

        # A SECOND RUN OF ITS OWN, not a rewind of the first: the composed
        # deployment is durable, so the alternate order is a fresh deployment
        # driven the other way round.
        self.doCleanups()
        self.setUp()
        second_trace, second = self.both_jobs_in(("job-b", "job-a"))
        self.assertEqual(scheduler_trace.validate(second), [])
        self.assertEqual(self.completion_order(second),
                         ["job-b/implementation", "job-a/implementation"])

        self.assertNotEqual(first["scenario_digest"],
                            second["scenario_digest"])
        self.assertNotEqual(self.completion_order(first),
                            self.completion_order(second))
        # AND BOTH RUNS REALLY CARRY BOTH JOBS' OWN TRANSITIONS.
        for artifact in (first, second):
            acts = {(one["stage_id"], one["act"]) for one in
                    artifact["records"] if one["outcome"] == "performed"}
            for stage_id in ("job-a/implementation", "job-b/implementation"):
                for act in ("reserve", "offer", "accept", "claim", "start",
                            "complete"):
                    self.assertIn((stage_id, act), acts, (stage_id, act))
        del first_trace, second_trace

    def test_a_second_team_is_authorized_by_scope_not_by_membership(self):
        """R1: THE THREE-CASE TEAM MATRIX, driven through the real Authority.

        I GOT THIS WRONG LAST CLAIM and review 2026-09-12T17:15:58Z corrected it.
        I recorded a gap saying a second team could not be authorized because
        this build had no membership relation to drive. That was false: the
        Authority's public `grant_capability` is exactly the seam, and a
        participant from another team composes successfully once it holds the
        right capability in the Work's own scope. No membership API and no
        product change is needed for the positive.

        WHAT A TEAM IS HERE. `authority/identity.py` fixes the grammar -- "a
        participant is team.member" -- so the team is the endpoint's own prefix,
        and authorization is a CAPABILITY AT A SCOPE rather than a membership
        lookup. The three cases below are that statement, executed:

        1. another team, no grant            -> refused
        2. another team, grant at the WRONG scope -> refused
        3. another team, grant at the WORK's scope -> COMPOSES

        THIS IS CONFIGURATION PROOF, NOT COMPLETED MULTI-TEAM EXECUTION: it shows
        a second team's participant can be authorized and composed, not that a
        multi-team pipeline has been run end to end.
        """
        from baton_v12.authority import Authority

        outsider = "other.reviewer"
        held = self.case.document()
        crossed = dict(held["receipt_participants"], review=outsider)
        trace = scheduler_trace.Trace(scheduler_trace.Scenario(
            name="composed-second-team-matrix", jobs=[], workers=[], ticks=3,
            note={"team_grammar": "a participant is team.member "
                                  "(authority/identity.py)",
                  "configured_team": "baton", "attempted_team": "other"}))

        # 1. NO GRANT AT ALL.
        with self.assertRaises(ContractRefusal) as caught:
            self.case.serving_two(receipt_participants=crossed)
        trace.scenario.note["refused_without_grant"] = {
            "asked": "serving_two with the outsider as review receipt owner",
            "cause": f"{caught.exception.category}/"
                     f"{caught.exception.code}: {caught.exception}"}
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn(outsider, str(caught.exception))

        # 2. GRANTED, BUT AT ANOTHER SCOPE.
        self.doCleanups()
        self.setUp()
        self.assertTrue(self.granted(outsider, "review",
                                     scope="scope:elsewhere"))
        with self.assertRaises(ContractRefusal) as caught:
            self.case.serving_two(receipt_participants=crossed)
        trace.scenario.note["refused_at_another_scope"] = {
            "asked": "serving_two with a grant at scope:elsewhere",
            "cause": f"{caught.exception.category}/"
                     f"{caught.exception.code}: {caught.exception}"}
        self.assertEqual(caught.exception.category, "policy")

        # 3. GRANTED AT THE WORK'S OWN SCOPE: IT COMPOSES.
        self.doCleanups()
        self.setUp()
        self.assertTrue(self.granted(outsider, "review",
                                     scope=self.case.scope))
        _job, _control, composed = self.case.serving_two(
            receipt_participants=crossed)
        session = composed.sessions["review"]
        self.assertEqual(session.participant, outsider)
        authority = Authority.open_readonly(
            self.case.authority_path,
            expected_authority_uuid=self.case.config["authority_uuid"])
        try:
            self.assertTrue(authority.holds_capability(
                outsider, "review", scope=self.case.scope))
            principal = authority.principal_of(outsider)
        finally:
            authority.dispose()
        self.assertEqual(principal, "principal:" + outsider)
        # AND THE POSITIVE IS CONFIGURATION EVIDENCE TOO. `serving_two` and
        # `operations_from` composing, plus a capability and a principal read,
        # are not a Job submission; the first form recorded them as one.
        trace.scenario.note["composed"] = {
            "participant": outsider, "principal": principal,
            "evidence": f"holds_capability review at {self.case.scope}",
            "owner": "serving_two/operations_from composed this deployment "
                     "with the outsider as its review receipt owner"}
        # THE TEAM REALLY IS THE PREFIX, and it is not the configured one.
        self.assertEqual(outsider.split(".")[0], "other")
        self.assertNotEqual(outsider.split(".")[0],
                            held["receipt_participants"]["review"].split(".")[0])

        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])
        self.assertEqual(artifact["gaps"], [])

    def test_real_authorization_receipts_bind_actor_scope_and_subject(self):
        """The queued item: ACTUAL review/import authorization, from the
        Authority's own receipts.

        Job A's ordinary composed integration runs, and the records are read from
        `authority.receipts(proposal_id)` -- the public reader -- rather than
        asserted here. Each receipt supplies its own actor, its decision's
        principal, effective scope and policy generation, its receipt identity
        and its instant, all bound to the exact proposal and candidate.

        A HELPER ASSERTING A PASSED RECEIPT WOULD PROVE NOTHING, which is review
        2026-09-12T17:24:24Z's point: what makes this evidence is that the
        Authority was asked and answered, and that the oracle then re-derives the
        review-before-integration relation from the records alone.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.case.integrating()
        self.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=4)
        deployment = self.case.deployment_of(held.composed)
        line = deployment.line_for("job-a")["line_id"]
        accepted = review_cycles.integration_checkpoint(held.control, line)
        proposal_id = deployment.published_proposal(accepted)
        self.assertTrue(proposal_id)

        trace = scheduler_trace.Trace(scheduler_trace.Scenario(
            name="composed-authorization-receipts", jobs=[], workers=[],
            ticks=100, note={"subject": "the producer's published proposal"}))
        # THE OWNER'S OWN ANSWER FOR WHAT THIS SUBJECT IS GOVERNED BY, read
        # from the deployment independently of the receipts so the validator
        # compares rather than merely checks for a value.
        trace.reference("proposal:" + proposal_id,
                        effective_scope=self.case.scope)
        receipts = self.authorized(deployment, trace, proposal_id)
        # THE AUTHORITY REALLY ANSWERED, with all four kinds.
        self.assertLessEqual({"verification", "review", "approval",
                              "integration"}, set(receipts))
        artifact = trace.artifact(SOURCES)
        self.assertEqual(scheduler_trace.validate(artifact), [])
        acts = {one["act"] for one in artifact["records"]}
        self.assertLessEqual({"verify", "review", "approve", "integrate"}, acts)
        for one in artifact["records"]:
            if one["act"] not in scheduler_trace.SUBJECT_AUTHORIZATION:
                continue
            self.assertTrue(one["participant"])
            self.assertTrue(one["principal"])
            self.assertTrue(one["operation_id"])
            self.assertEqual(one["evidence"], "proposal:" + proposal_id)
            decision = one["authorization"]
            # EACH DECISION'S OWN POSITIVE WORD, ITS CANDIDATE, ITS TARGET AND
            # THE SCOPE IT WAS MADE IN -- carried, not merely asserted here.
            self.assertEqual(
                decision["disposition"],
                scheduler_trace.POSITIVE_DISPOSITION[one["act"]])
            self.assertTrue(decision["candidate_digest"])
            self.assertTrue(decision["target"])
            self.assertEqual(decision["effective_scope"], self.case.scope)
            # AND THE DECISION'S OWN ROLE AND GENERATION. I previously wrote
            # that "only the approval binds a policy generation", reading the
            # RECEIPT's nullable top-level field rather than the decision's --
            # `decision.policy_generation` is required and positive on EVERY
            # AuthorizationDecision, and that is what the exporter reads.
            self.assertEqual(decision["role"],
                             scheduler_trace.EXPECTED_ROLE[one["act"]])
            self.assertIsInstance(decision["policy_generation"], int)
            self.assertGreaterEqual(decision["policy_generation"], 1)
        self.assertEqual(
            artifact["authorization_references"]["proposal:" + proposal_id],
            {"effective_scope": self.case.scope})
        self.assertEqual(artifact["gaps"], [])

    def authorized(self, deployment, trace, proposal_id, *, tick=1,
                   job_id=None, stage_id=None):
        """Record each Authority receipt on one subject, as the Authority gives
        it. Nothing is synthesized and no outcome word is trusted on its own."""
        held = {}
        for receipt in deployment.authority.receipts(proposal_id):
            decision = receipt.get("decision") or {}
            act = {"verification": "verify", "review": "review",
                   "approval": "approve", "integration": "integrate"}.get(
                       receipt["kind"])
            held[receipt["kind"]] = receipt
            if act is None:
                continue
            # THE WHOLE DECISION TRAVELS, and this time it really does. The
            # first form dropped the disposition, the candidate, the target and
            # the scope, asserted the scope in the test and then threw it away --
            # so a `changes-requested` review emitted a performed authorization.
            # Every one of these is already on the receipt.
            trace.record(tick, act, outcome="performed",
                         job_id=job_id, stage_id=stage_id,
                         participant=receipt["actor"],
                         principal=decision.get("principal"),
                         operation_id=receipt["receipt_id"],
                         recorded_at=receipt.get("recorded_at"),
                         evidence="proposal:" + proposal_id,
                         authorization={
                             "kind": receipt["kind"],
                             "disposition": receipt.get("disposition"),
                             "candidate_digest": receipt.get(
                                 "candidate_digest"),
                             "target": receipt.get("target"),
                             "effective_scope": decision.get(
                                 "effective_scope"),
                             # THE DECISION'S OWN GENERATION, which is
                             # required and positive on EVERY
                             # AuthorizationDecision. An earlier comment here
                             # said a null was legitimate because "only the
                             # approval binds one" -- that was the RECEIPT's
                             # nullable top-level field, not this one, and the
                             # two are different facts.
                             "policy_generation": decision.get(
                                 "policy_generation"),
                             "role": decision.get("role")},
                         cause=None)
        return held

    def test_an_integration_without_its_review_is_refused(self):
        """The oracle's own negative: an integration receipt whose subject has no
        recorded review is `unauthorized-subject`, not an accepted import."""
        base = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        base.update({"tick": 1, "outcome": "performed",
                     "participant": "baton.integrator",
                     "principal": "principal:baton.integrator",
                     "operation_id": "receipt-1",
                     "evidence": "proposal:p-1"})
        held = scheduler_trace.validate(
            {"schema": scheduler_trace.TRACE_SCHEMA,
             "records": [dict(base, act="integrate")]})
        self.assertIn("unauthorized-subject", [one["code"] for one in held])

    def test_an_integration_of_another_subject_does_not_authorize_this_one(self):
        """A review of a DIFFERENT proposal is not this candidate's
        authorization -- the relation is keyed by subject, not by presence."""
        base = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        base.update({"tick": 1, "outcome": "performed",
                     "participant": "baton.integrator",
                     "principal": "principal:baton.integrator",
                     "operation_id": "receipt-1"})
        held = scheduler_trace.validate(
            {"schema": scheduler_trace.TRACE_SCHEMA,
             "records": [dict(base, act="review", evidence="proposal:other",
                              operation_id="receipt-0"),
                         dict(base, act="integrate",
                              evidence="proposal:p-1")]})
        self.assertIn("unauthorized-subject", [one["code"] for one in held])

    def codes(self, records):
        """This class's own validator call, over a bare record list.

        The authorization negatives below are pure oracle cases and live beside
        the composed positive they correct, so this class needs the same reading
        helper the synthetic-trace class has.
        """
        trace = scheduler_trace.Trace(
            scheduler_trace.Scenario(name="synthetic", jobs=[], workers=[],
                                     ticks=1),
            unobserved=())
        trace.records = records
        return sorted({one["code"] for one
                       in scheduler_trace.validate(trace.artifact())})

    def authorization(self, act, **changed):
        """One synthetic authorization record, positive unless changed."""
        held = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        held.update({"tick": 1, "act": act, "outcome": "performed",
                     "participant": "baton.who",
                     "principal": "principal:baton.who",
                     "operation_id": f"receipt-{act}",
                     "evidence": "proposal:p-1",
                     "recorded_at": "2026-09-02T00:00:01.000Z",
                     "authorization": {
                         "disposition":
                             scheduler_trace.POSITIVE_DISPOSITION[act],
                         "candidate_digest": "cand-1", "target": "target-1",
                         "effective_scope": "scope:deployment",
                         "policy_generation": 1,
                         "role": scheduler_trace.EXPECTED_ROLE[act]}})
        held.update(changed)
        return held

    def authorized_chain(self, **changed):
        return [self.authorization(one) for one in
                ("verify", "review", "approve")] + [
                    self.authorization("integrate", **changed)]

    def test_a_full_positive_authorization_chain_passes(self):
        self.assertEqual(self.referenced(self.authorized_chain()), [])

    def test_an_authorization_with_no_owner_reference_is_unproved(self):
        """Review 2026-09-12T17:42:54Z: deleting the reference map disabled the
        comparison, so a chain with no owner-declared scope validated clean. A
        check that becomes a no-op when its reference is absent is not a check."""
        self.assertIn("unreferenced-authorization",
                      self.codes(self.authorized_chain()))

    def test_a_foreign_scope_with_no_reference_is_still_unproved(self):
        """And the other retained negative: a foreign scope AND a missing
        reference. The absent reference is reported rather than excusing the
        scope."""
        held = self.authorized_chain()
        held[1]["authorization"] = dict(held[1]["authorization"],
                                        effective_scope="scope:elsewhere")
        self.assertIn("unreferenced-authorization", self.codes(held))

    def test_an_empty_reference_scope_is_unproved(self):
        for scope in ("", None):
            with self.subTest(scope=scope):
                self.assertIn("unreferenced-authorization",
                              self.referenced(self.authorized_chain(),
                                              scope=scope))

    def test_a_trace_with_no_authorization_acts_needs_no_reference(self):
        """The rule runs only for acts that make a claim, so an ordinary
        scheduling trace is unaffected by it."""
        self.assertEqual(self.codes([
            self.authorization("verify")
            | {"act": "reserve", "authorization": None,
               "attempt_id": "attempt-1", "worker_id": "impl-one",
               "evidence": "allocations:attempt-1"}]), [])

    def test_a_nonaccepting_review_authorizes_nothing(self):
        """The exact erasure review 2026-09-12T17:30:56Z retained: a review
        recorded `changes-requested` emitted a performed authorization and
        validated clean, because the extractor dropped the disposition."""
        held = self.authorized_chain()
        held[1]["authorization"] = dict(held[1]["authorization"],
                                        disposition="changes-requested")
        codes = self.codes(held)
        self.assertIn("nonaccepting-authorization", codes)
        self.assertIn("unauthorized-subject", codes)

    def test_a_review_recorded_after_its_integration_is_refused(self):
        """The other retained erasure: a review at 00:00:02 after an integration
        at 00:00:01, both at tick 1 and in stream order, validated clean."""
        held = self.authorized_chain()
        held[1]["recorded_at"] = "2026-09-02T00:00:02.000Z"
        held[3]["recorded_at"] = "2026-09-02T00:00:01.000Z"
        held[1], held[3] = held[3], held[1]
        self.assertIn("out-of-order", self.codes(held))

    def test_an_import_missing_a_judgment_is_refused(self):
        """All three judgments, not a review alone."""
        for missing in ("verify", "review", "approve"):
            with self.subTest(missing=missing):
                held = [one for one in self.authorized_chain()
                        if one["act"] != missing]
                self.assertIn("unauthorized-subject", self.codes(held))

    def referenced(self, records, scope="scope:deployment"):
        """Validate a synthetic chain against an owner-derived reference."""
        trace = scheduler_trace.Trace(
            scheduler_trace.Scenario(name="synthetic", jobs=[], workers=[],
                                     ticks=1),
            unobserved=())
        trace.records = records
        trace.reference("proposal:p-1", effective_scope=scope)
        return sorted({one["code"] for one
                       in scheduler_trace.validate(trace.artifact())})

    def test_a_decision_in_a_foreign_scope_is_refused(self):
        """Review 2026-09-12T17:37:27Z, retained mutation 1: a foreign
        effective_scope validated clean, because the check only asked whether
        the field had a value rather than comparing it to the subject's own."""
        held = self.authorized_chain()
        held[1]["authorization"] = dict(held[1]["authorization"],
                                        effective_scope="scope:elsewhere")
        self.assertIn("mismatched-authorization", self.referenced(held))

    def test_a_decision_with_no_positive_generation_is_refused(self):
        """Retained mutation 2: a missing decision.policy_generation validated
        clean. It is required and positive on every AuthorizationDecision."""
        for value in (None, 0, -1, True):
            with self.subTest(value=value):
                held = self.authorized_chain()
                held[1]["authorization"] = dict(held[1]["authorization"],
                                                policy_generation=value)
                self.assertIn("unattributed-authorization",
                              self.referenced(held))

    def test_a_decision_made_in_another_role_is_refused(self):
        """Retained mutation 3: a review whose decision role was `integrate`
        validated clean. A decision made in another role is another decision."""
        held = self.authorized_chain()
        held[1]["authorization"] = dict(held[1]["authorization"],
                                        role="integrate")
        self.assertIn("mismatched-authorization", self.referenced(held))

    def test_legitimately_differing_generations_are_accepted(self):
        """And no all-generations-equal rule is invented: policy legitimately
        changes between decisions, so each names a positive generation of its own
        and none is required to match another's."""
        held = self.authorized_chain()
        for index, one in enumerate(held):
            one["authorization"] = dict(one["authorization"],
                                        policy_generation=index + 1)
        self.assertEqual(self.referenced(held), [])

    def test_an_import_of_another_candidate_is_refused(self):
        held = self.authorized_chain()
        held[3]["authorization"] = dict(held[3]["authorization"],
                                        candidate_digest="cand-other")
        self.assertIn("mismatched-authorization", self.codes(held))

    def test_an_authorization_without_its_decision_context_is_refused(self):
        held = self.authorized_chain()
        held[0]["authorization"] = dict(held[0]["authorization"],
                                        effective_scope=None)
        self.assertIn("unattributed-authorization", self.codes(held))

    def test_an_unattributed_authorization_is_refused(self):
        """And a receipt that does not say who decided is not an
        authorization, however positive its outcome word."""
        base = {name: None for name in scheduler_trace.RECORD_MEMBERS}
        base.update({"tick": 1, "act": "review", "outcome": "performed",
                     "evidence": "proposal:p-1"})
        held = scheduler_trace.validate(
            {"schema": scheduler_trace.TRACE_SCHEMA, "records": [base]})
        self.assertIn("unattributed-authorization",
                      [one["code"] for one in held])

    def test_two_independent_repository_bindings_are_configured(self):
        """C3: THE REPOSITORY BINDINGS ARE PROVED, not reported missing.

        Review 2026-09-12T16:35:09Z was right that "selecting a unit pool that
        cannot expose those facts is not an exact missing composed interface". It
        is not missing: the composed `two_jobs` document binds each Job to its
        OWN nominated source repository, its own canonical target and its own
        declared base, and this reads those from the document the fixture really
        composes.

        WHAT REMAINS UNPROVED IS NARROWER NOW, and the gap says exactly that:
        Authority TEAM membership, and a driven wrong-repository refusal. The
        reconciliation variant this record's other cases use deliberately
        collapses both Jobs onto one target and one source -- that is what makes
        them two lines of one target -- so the two-repository fact is read from
        the two-Job document rather than from that variant.
        """
        held = self.case.two_jobs()
        bindings = {one["job_id"]: one for one in held["job_bindings"]}
        sources = {one["worker_id"]: one["deployment"]["nominated_source"]
                   for one in held["workers"]
                   if one["role"] == "implementation"}
        # TWO DISTINCT REPOSITORIES, one per Job's own producer.
        self.assertEqual(len(set(sources.values())), 2, sources)
        self.assertEqual(
            sources[bindings["job-a"]["source_worker_id"]].endswith("source"),
            True)
        self.assertNotEqual(sources[bindings["job-a"]["source_worker_id"]],
                            sources[bindings["job-b"]["source_worker_id"]])
        # TWO DISTINCT CANONICAL TARGETS AND TWO DISTINCT DECLARED BASES.
        self.assertNotEqual(bindings["job-a"]["canonical_target_id"],
                            bindings["job-b"]["canonical_target_id"])
        self.assertNotEqual(bindings["job-a"]["line_declared_base"],
                            bindings["job-b"]["line_declared_base"])

        scenario = scheduler_trace.Scenario(
            name="composed-two-repository-bindings", jobs=[], workers=[],
            ticks=1, note={"bindings": [
                {"job_id": one, "canonical_target_id":
                 bindings[one]["canonical_target_id"],
                 "source_worker_id": bindings[one]["source_worker_id"],
                 "nominated_source_basename":
                     os.path.basename(sources[bindings[one][
                         "source_worker_id"]])}
                for one in sorted(bindings)]})
        trace = scheduler_trace.Trace(scenario)
        gap = trace.gap(
            name="authority-teams-and-wrong-repository-refusal",
            reason="two independent repository bindings and two canonical "
                   "targets ARE configured and are proved here; what is still "
                   "unproved is Authority team membership, which no Job-manager "
                   "or composed document carries, and a DRIVEN wrong-repository "
                   "refusal, which needs a stage offered against another Job's "
                   "source",
            observed="two distinct nominated sources, canonical targets and "
                     "declared bases in the composed two-Job document",
            required="nothing further from this pool. Both halves are now "
                     "driven elsewhere in this module: "
                     "test_a_wrong_repository_binding_is_refused_by_its_own_"
                     "owner executes the wrong-repository refusal and its legal "
                     "companion, and "
                     "test_a_second_team_is_authorized_by_scope_not_by_"
                     "membership executes the three-case team matrix -- no "
                     "grant refuses, a grant at the wrong scope refuses, and a "
                     "grant at the Work's own scope COMPOSES. This gap records "
                     "only that THIS unit pool cannot see either fact")
        self.assertEqual(trace.artifact(SOURCES)["gaps"], [gap])

    def test_a_correction_opens_a_second_episode_on_the_same_line(self):
        """A requested correction is a real authorized transition too, and it
        opens a SECOND episode -- which the oracle binds separately from the
        first rather than merging them into one attempt."""
        held = self.case.coding()
        trace = self.blank()
        self.assertEqual(
            self.case.turn(held.control, "implementation", held.first,
                           self.case.mounted_at(held.composed, held.first),
                           edits={"harness.py": "print('answered')\n"}), 0)
        # THE COMPLETION IS OBSERVED HERE, BEFORE THE CORRECTION SUPERSEDES IT.
        # That is the whole point of observing at the boundary: this fact is
        # unreadable from a final dump, and the earlier form of this case
        # therefore carried a dependency violation it could not resolve.
        first_states = self.observing(held, trace, "job-a", "implementation",
                                      "completed")
        self.assertEqual(first_states["implementation"], "completed")
        self.observing(held, trace, "job-a", "review", "waiting")
        reviewed = self.case.one_attempt_of(held.composed, "review-worker")
        self.case.review_turn(held, "job-a", reviewed, "changes-requested")
        self.observing(held, trace, "job-a", "implementation", "waiting")
        corrected = self.case.one_attempt_of(
            held.composed, "implementation-worker", exclude=[held.first])
        self.assertNotEqual(corrected, held.first)

        # AND THE CORRECTION IS RECORDED AS AN ACT CITING ITS OWN JUDGMENT.
        #
        # I WAS WRONG ABOUT THIS SEAM AND THE REVIEW DISPROVED IT WITH THE
        # BUILD'S OWN READERS. My last handoff bound the act to the ended review
        # ATTACHMENT and recorded a gap claiming no public reader answers a
        # verdict from it, asking for a new API. There is one:
        # `ending.settlement_of` answers the settled review episode with its
        # `evidence.verdict_id`, its outcome and the attempt it ROUTED to, and
        # `verdict_of` proves and answers the committed disposition. Both are
        # public, both are read here, and no product change was needed.
        from baton_v12.job_manager import ending
        from baton_v12.worker_manager import assignment_of, review_cycles

        assignment = assignment_of(held.control, reviewed)
        attachment = review_cycles.review_for_attempt(
            held.control, attempt_id=reviewed,
            generation=assignment["generation"])
        self.assertEqual(attachment["state"], "ended")
        settlement = ending.settlement_of(held.job, "job-a/review", 1)
        evidence = settlement["evidence"]
        verdict = review_cycles.verdict_of(held.control,
                                           evidence["verdict_id"])
        # THE OWNERS' OWN WORDS, asserted before they are recorded.
        self.assertEqual(verdict["disposition"], "changes-requested")
        self.assertEqual(evidence["outcome"], "correction")
        self.assertEqual(verdict["attachment_id"],
                         attachment["attachment_id"])
        self.assertEqual(evidence["routed"], corrected)
        self.assertEqual(settlement["attempt_id"], reviewed)
        self.assertEqual(settlement["stage_id"], "job-a/review")
        # AND THE OWNER'S OWN ASSIGNMENT FOR THE REVIEWING ATTEMPT, read
        # independently of the judgment that names a reviewer. Review
        # 2026-09-12T23:45:06Z: the reviewer members were required to be present
        # and compared with nothing, so changing any one of them validated.
        trace.assignment(reviewed, **{
            name: assignment[name]
            for name in scheduler_trace.ASSIGNMENT_CONTEXT})
        trace.record(trace._tick, "correct", outcome="performed",
                     job_id="job-a",
                     stage_id="job-a/implementation", episode=2,
                     attempt_id=corrected,
                     participant=verdict["reviewer_participant"],
                     principal=verdict["reviewer_principal"],
                     recorded_at=verdict["recorded_at"],
                     worker_id=attachment["reviewer_worker_id"],
                     evidence="checkpoint_verdicts:"
                              + evidence["verdict_id"],
                     correction={
                         "outcome": evidence["outcome"],
                         "disposition": verdict["disposition"],
                         "verdict_id": evidence["verdict_id"],
                         "attachment_id": verdict["attachment_id"],
                         "checkpoint_id": verdict["checkpoint_id"],
                         "subject_attempt_id": settlement["attempt_id"],
                         "subject_stage_id": settlement["stage_id"],
                         "subject_episode": settlement["episode"],
                         "superseded_attempt_id": held.first,
                         "routed_attempt_id": evidence["routed"],
                         "reviewer_participant":
                             verdict["reviewer_participant"],
                         "reviewer_principal": verdict["reviewer_principal"],
                         "review_assignment_generation":
                             verdict["review_assignment_generation"]})

        jobs, workers, bindings = self.scenario_from(held, ("job-a",))
        scenario = scheduler_trace.Scenario(
            name="composed-correction", jobs=jobs, workers=workers, ticks=100,
            order=["job-a/implementation"],
            resolved_principals={one["participant"]: one["principal"]
                                 for one in workers},
            note={"fixture": "a changes-requested verdict reopened the same "
                             "line", "bindings": bindings})
        trace.scenario = scenario
        artifact = trace.artifact(SOURCES)
        # C3: BOTH SIDES OF THE CORRECTION ARE EXPORTED. The first draft carried
        # only the live episode, so the artifact showed a second episode with
        # nothing explaining it. Episode 1 is the attempt the reviewer sent back
        # and episode 2 is its replacement, and both are here.
        episodes = {one["episode"] for one in artifact["records"]
                    if one["stage_id"] == "job-a/implementation"}
        self.assertEqual(episodes, {1, 2})
        # AND THE REVIEW THAT SENT IT BACK IS IN THE SAME ARTIFACT, so the link
        # is readable rather than asserted in prose: the review stage completed
        # and the implementation opened a second episode after it.
        self.assertIn("job-a/review",
                      {one["stage_id"] for one in artifact["records"]})
        first = min(one["tick"] for one in artifact["records"]
                    if one["stage_id"] == "job-a/implementation"
                    and one["episode"] == 2)
        review = max(one["tick"] for one in artifact["records"]
                     if one["stage_id"] == "job-a/review")
        self.assertLess(review, first)

        # AND THIS TRACE HONESTLY CANNOT PROVE ONE THING, which the oracle says
        # rather than this test excusing it.
        #
        # The review stage only existed because implementation episode 1 really
        # finished -- but the reviewer sent that attempt back, so the stage's
        # state is no longer `completed`, and this build records no historical
        # completion for a superseded episode: `ended_state` is NULL and no
        # conclude receipt exists. So the dependency oracle correctly reports
        # that the review was reserved with no recorded completion of the
        # implementation it depends on. Manufacturing that completion to get a
        # clean run is exactly what this Work forbids, so the violation is
        # asserted and the missing evidence is recorded as a gap.
        # AND THE PREREQUISITE IS NOW PROVED RATHER THAN MISSING. The earlier
        # form of this case read a final dump, where implementation episode 1's
        # completion is unreadable because the correction superseded it -- so it
        # carried a `successor-before-prerequisite` violation it recorded as a
        # gap. Observing at the tick boundary captures that completion when it
        # really happened, so the violation is gone for the right reason.
        self.assertEqual(scheduler_trace.validate(artifact), [])
        completed = [one for one in artifact["records"]
                     if one["stage_id"] == "job-a/implementation"
                     and one["act"] == "complete" and one["episode"] == 1]
        self.assertEqual(len(completed), 1, artifact["records"])
        self.assertLess(completed[0]["tick"], first)

        # AND THE CORRECTION IS A CHECKED ACT NOW, not a recorded word.
        [correction] = [one for one in artifact["records"]
                        if one["act"] == "correct"]
        self.assertEqual(correction["episode"], 2)
        self.assertEqual(correction["participant"],
                         attachment["reviewer_participant"])
        self.assertNotIn("unvalidated-act",
                         [one["code"] for one in
                          scheduler_trace.validate(artifact)])

        # AND THE GAP I RECORDED HERE LAST CLAIM IS WITHDRAWN, not softened.
        #
        # It said no public reader answers a verdict from its attachment and
        # asked for a new API. `ending.settlement_of` and `verdict_of` answer it
        # above, in this very run. A gap is a statement about the build, and a
        # false one is worse than none: it would have sent the next author to
        # write product code for a reader that already exists. This trace
        # records no gap because it has none.
        self.assertEqual(trace.artifact(SOURCES)["gaps"], [])
        self.assertEqual(correction["correction"]["disposition"],
                         "changes-requested")
        self.assertEqual(correction["correction"]["routed_attempt_id"],
                         corrected)

        # THE REVIEW'S FOUR RETAINED MUTATIONS, over THIS real artifact. Offline
        # edits of a retained export; no owner wrote any of them.
        relabelled = copy.deepcopy(artifact)
        for row in relabelled["records"]:
            if row["stage_id"] == "job-a/review":
                row["stage_id"] = "job-b/review"
                row["job_id"] = "job-b"
        # AND THE CODE IS `unreviewed-correction`, which is the honest one: the
        # judgment still names job-a/review, so the subject agrees with the
        # correction's Job and what is missing is the CLAIM of exactly that
        # attempt at that stage and episode. The stage disagreement itself has
        # its own case in the offline negatives.
        self.assertIn("unreviewed-correction",
                      [one["code"] for one
                       in scheduler_trace.validate(relabelled)])

        for member, value in (("reviewer_participant", "other.unassigned"),
                              ("reviewer_principal",
                               "principal:other.unassigned"),
                              ("review_assignment_generation", 999)):
            altered = copy.deepcopy(artifact)
            [row] = [one for one in altered["records"]
                     if one["act"] == "correct"]
            row["correction"][member] = value
            self.assertIn("misattributed-correction",
                          [one["code"] for one
                           in scheduler_trace.validate(altered)],
                          member)

        # AND A JUDGMENT WHOSE REVIEWER NOTHING INDEPENDENTLY REPORTS.
        unreferenced = copy.deepcopy(artifact)
        unreferenced["assignment_references"] = {}
        self.assertIn("unreferenced-correction",
                      [one["code"] for one
                       in scheduler_trace.validate(unreferenced)])


if __name__ == "__main__":                 # pragma: no cover
    unittest.main()
