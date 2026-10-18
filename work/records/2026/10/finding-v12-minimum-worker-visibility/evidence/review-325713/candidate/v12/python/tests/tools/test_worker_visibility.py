"""W324214 -- the minimum read-only worker visibility view, over REAL documents.

EVERY SNAPSHOT HERE COMES FROM `projection.status`. A fact projection tested
against a handwritten dictionary proves only that it agrees with the fixture
beside it; what is worth proving is that it reads what the Job Manager
actually publishes -- so these cases submit real Jobs into a real store, make
real scheduler reservations, record real attempts and real activity
observations in a real Worker Manager control store, and project the document
that comes out.

AND THE OWNERS ARE TRAPPED. "No database is opened, no model is reached, no
probe or scheduler act is performed, no subprocess is spawned and nothing is
written" is the acceptance, so every one of those boundaries raises while the
view runs. A green test that merely asserts the implementation's own output
would pass whatever the implementation did next.

WHERE AN ADVERSARIAL PAIRING IS USED IT IS SAID SO. The restarted-episode case
grafts episode one's REAL allocation and REAL activity onto episode two's REAL
stage row. The producer does not do that -- `materialized` reads both from the
live episode -- and that is exactly why the view must refuse the pairing on its
own evidence rather than on the producer's good behaviour.
"""

import ast
import copy
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import ContractRefusal                 # noqa: E402
from baton_v12.job_manager import Unobserved, submit, sweep      # noqa: E402
from baton_v12.job_manager import episodes, scheduler            # noqa: E402
from baton_v12.job_manager.projection import status              # noqa: E402
from baton_v12.job_manager.store import JobStore                 # noqa: E402
from baton_v12.job_manager.submission import stage_rows          # noqa: E402
from baton_v12.worker_manager import (ControlStore,               # noqa: E402
                                      attempt_activity_of,
                                      attempt_runtime_of,
                                      observe_activity,
                                      record_attempt)

from tools import worker_visibility                              # noqa: E402
from tools.worker_visibility import (VisibilityRefusal, rows_of,  # noqa: E402
                                     visibility)

from tests.job_manager import fixtures                           # noqa: E402
from tests.job_manager.fixtures import (LATER, NOW, PROFILE, UUID,  # noqa: E402
                                        FakeOperations, job, stage,
                                        submission)
from tests.job_manager.test_scheduling import pool, principals    # noqa: E402

ADAPTER = "sha256:" + "e" * 64

# A SECOND INSTANT, so a case can tell the snapshot's query time apart from an
# observation's own time. NOW is when the activity was observed; LATER is when
# the manager queried its stores to assemble the document.
QUERY_AT = LATER


def resolved(document, path):
    """The value one of this view's `source` paths actually names.

    THE PROVENANCE IS CHECKED RATHER THAN TRUSTED. A view that labelled a
    value with a path it did not come from would be worse than one that
    published no provenance at all, so these cases walk the path back into the
    source document and compare.
    """
    held = document
    for step in path.split("."):
        name, _, rest = step.partition("[")
        if name:
            held = held[name]
        while rest:
            index, _, rest = rest.partition("[")
            held = held[int(index.rstrip("]"))]
    return held


def facts_in(held):
    """Every (path, fact) in one projected row, at any depth."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "known" in node and "unknown_reason" in node:
                found.append(node)
                if isinstance(node.get("observed_at"), dict):
                    found.append(node["observed_at"])
                return
            for one in node.values():
                walk(one)
        elif isinstance(node, list):
            for one in node:
                walk(one)

    walk(held)
    return found


# WHAT THIS VIEW REPORTS, AND WHAT IT EXPLAINS WITH. The two are separated
# because REVIEW 2026-10-18T17-37-19Z caught three cases here searching the
# whole serialized row for the words `fresh`, `healthy` and `transcript` -- and
# finding them in the SENTENCES that promise their absence. A projection
# forbidden the word `healthy` in its prose cannot say "this view publishes no
# healthy verdict", which is the one sentence an operator most needs to read;
# what must not carry an invented verdict is the set of VALUES and STATE words
# a consumer branches on. So these walk that set instead.
REPORTED = ("presence", "state", "unit")
EXPLANATORY = ("reason", "note", "basis", "what", "unknown_reason", "source",
               "query_time_note")


def reported_words(held):
    """Every word this view REPORTS: fact values, presences, states, units."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "known" in node and "unknown_reason" in node:
                found.append(node.get("value"))
            for name, one in node.items():
                if name in EXPLANATORY:
                    continue
                if name in REPORTED:
                    found.append(one)
                    continue
                walk(one)
        elif isinstance(node, list):
            for one in node:
                walk(one)

    walk(held)
    return [one for one in found if isinstance(one, str)]


def keys_in(held):
    """Every member name this view PUBLISHES, at any depth.

    A member forwarded empty is still a member this surface republished, so
    the allowlist is checked by name and not only by value.
    """
    found = set()

    def walk(node):
        if isinstance(node, dict):
            found.update(node)
            for one in node.values():
                walk(one)
        elif isinstance(node, list):
            for one in node:
                walk(one)

    walk(held)
    return found


def freshness_in(held):
    """Every freshness block in one projected document or row."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "state" in node and "reason" in node and "note" in node:
                found.append(node)
            for one in node.values():
                walk(one)
        elif isinstance(node, list):
            for one in node:
                walk(one)

    walk(held)
    return found


# A VERDICT NOBODY OBSERVED, in every spelling this view might have invented.
INVENTED = ("healthy", "offline", "alive", "dead", "stuck", "wedged",
            "degraded", "fresh", "stale", "recent", "idle")

# A DERIVED MEMBER NOBODY ASKED FOR. These are names rather than words: a view
# that computed an age or a freshness verdict would have to publish it under
# one of them.
DERIVED = ("age", "age_seconds", "elapsed", "current_as_of", "fresh",
           "stale", "last_seen", "seconds_since", "progress",
           "progress_percent", "percent", "tokens", "tokens_used")


class VisibilityCase(fixtures.JobManagerCase):
    """One real Job store, one real control store, one real status document.

    `JobManagerCase` is the Job Manager suite's own fixture -- the same one
    `tests/job_manager/test_status.py` drives the projection with -- so the
    documents here are the producer's, not this file's.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()

    def submitted(self, document=None):
        submit(self.jobs, document if document is not None else submission())
        return self.jobs

    def document(self, *, observed_at=QUERY_AT, operations=None):
        return status(self.jobs, operations if operations is not None
                      else self.acts, observed_at=observed_at)

    def unread(self, *, observed_at=QUERY_AT):
        """The same projection through a reader holding no control store."""
        return status(self.jobs, Unobserved(), observed_at=observed_at)

    def row(self, document, stage_id):
        for one in rows_of(document):
            if one["stage"]["stage_id"]["value"] == stage_id:
                return one
        raise AssertionError(stage_id)

    # -- real producer material ---------------------------------------------

    def attempt_of(self, stage_id="job-a/implementation"):
        return episodes.live_of(self.jobs, stage_id)["attempt_id"]

    def reserved(self, stage_id="job-a/implementation"):
        """A REAL scheduler reservation, through the scheduler's own act.

        Not an invented allocation document: the members this view reports are
        `stage_allocations`' own columns joined with the pool's, and a fixture
        that wrote its own names would let the view miss the real shape.
        """
        document = pool()
        scheduler.activate_pool(self.jobs, document, principals(document))
        [row] = [one for one in stage_rows(self.jobs)
                 if one["stage_id"] == stage_id]
        live = episodes.live_of(self.jobs, stage_id)
        return dict(scheduler.reserve(self.jobs,
                                      episodes.attempting(dict(row), live)))

    def runtime_control(self):
        control = self.control()
        return control

    def observed_runtime(self, attempt_id, *, control=None):
        """The Worker Manager's OWN runtime projection for a real attempt.

        Recorded through `record_attempt` and read back through
        `attempt_runtime_of`, so what reaches the status document is the
        producer's document rather than this file's idea of one.
        """
        control = control if control is not None else self.control()
        record_attempt(control, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       policy_digest="sha256:" + "2" * 64)
        return control, attempt_runtime_of(control, attempt_id)

    def observed_activity(self, control, attempt_id, total):
        """A REAL activity observation, written and read back.

        `observe_activity` is the owner of the count and the instant; this
        takes both from it rather than spelling a pair here.
        """
        observe_activity(control, attempt_id=attempt_id, bytes_observed=total)
        return attempt_activity_of(control, attempt_id)

    def running(self, stage_id="job-a/implementation", *, total=None,
                execution_runtime="running", exchange_state=None):
        """One stage carrying a real runtime, and optionally real activity.

        The runtime axis word is moved onto the producer's own document rather
        than replacing it: `record_attempt` leaves an attempt at
        `not-started`, and advancing it to `running` through the manager's
        activation would need an offer, a claim and an adapter this read-only
        case has no business building.
        """
        attempt_id = self.attempt_of(stage_id)
        control, runtime = self.observed_runtime(attempt_id)
        runtime = dict(runtime, execution_runtime=execution_runtime,
                       runtime_id="runtime-1",
                       assignment={"work_ref": {"authority_uuid": UUID,
                                                "work_id": fixtures.WORK_A},
                                   "participant": fixtures.WHO,
                                   "generation": 1})
        activity = (None if total is None
                    else self.observed_activity(control, attempt_id, total))
        self.acts.observed(stage_id, claimed_by=True, runtime=runtime,
                           activity=activity)
        if exchange_state is not None:
            self.acts.commanded(stage_id, state=exchange_state,
                                receipt={"accepted_at": NOW})
        return attempt_id, control


class TheProducerShapeIsWhatThisViewWasBuiltAgainst(VisibilityCase):
    """Revalidated rather than assumed, because the brief says so and because
    a view built on the wrong shape passes against its own fixture."""

    def test_the_runtime_carries_no_attempt_id_and_the_activity_does(self):
        """The one asymmetry every association check in this view turns on."""
        self.submitted(submission(jobs=[job("job-a")]))
        attempt_id, _control = self.running(total=4096)
        document = self.document()
        runtime = document["jobs"][0]["stages"][0]["runtime"]
        self.assertEqual(sorted(runtime),
                         ["activity", "assignment", "execution_runtime",
                          "runtime_id"])
        self.assertNotIn("attempt_id", runtime)
        self.assertEqual(runtime["activity"]["attempt_id"], attempt_id)

    def test_the_worker_managers_own_runtime_reader_names_five_members(self):
        """What `projection` narrows: the producer's reader carries the attempt
        id and the cleanup axis, and the status document publishes neither."""
        self.submitted(submission(jobs=[job("job-a")]))
        attempt_id = self.attempt_of()
        _control, runtime = self.observed_runtime(attempt_id)
        self.assertEqual(sorted(runtime),
                         ["assignment", "attempt_id", "cleanup",
                          "execution_runtime", "runtime_id"])
        self.assertEqual(runtime["attempt_id"], attempt_id)

    def test_an_unobserved_recorded_attempt_answers_nulls_not_zero(self):
        """The producer's own distinction, which this view has to carry."""
        self.submitted(submission(jobs=[job("job-a")]))
        attempt_id = self.attempt_of()
        control, _runtime = self.observed_runtime(attempt_id)
        self.assertEqual(attempt_activity_of(control, attempt_id),
                         {"attempt_id": attempt_id, "bytes_observed": None,
                          "observed_at": None})


class EveryCurrentStageGetsARow(VisibilityCase):

    def test_every_stage_including_an_unassigned_one_is_reported(self):
        self.submitted()
        rows = rows_of(self.document())
        self.assertEqual([one["stage"]["stage_id"]["value"] for one in rows],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])
        for one in rows:
            self.assertEqual(one["allocation"]["presence"], "unallocated")

    def test_the_exact_identities_are_reported_rather_than_summarised(self):
        self.submitted(submission(jobs=[job("job-a")]))
        document = self.document()
        stage = document["jobs"][0]["stages"][0]
        held = self.row(document, "job-a/implementation")["stage"]
        for member in ("stage_id", "job_id", "kind", "state", "work_id",
                       "episode", "attempt_id", "offer_id"):
            self.assertTrue(held[member]["known"], member)
            self.assertEqual(held[member]["value"], stage[member], member)

    def test_the_job_identities_travel_with_the_row(self):
        self.submitted()
        held = self.row(self.document(), "job-b/implementation")["job"]
        self.assertEqual(held["job_id"]["value"], "job-b")
        self.assertEqual(held["submission_id"]["value"], "sub-1")

    def test_the_schema_is_this_views_own_and_names_the_one_it_read(self):
        self.submitted()
        held = visibility(self.document())
        self.assertEqual(held["schema"], "baton.v12.worker-visibility/1")
        self.assertEqual(held["source_schema"], "baton.v12.job-status/6")

    def test_every_known_fact_resolves_to_the_path_it_claims(self):
        """The provenance is walked back into the source document.

        This is the case that makes every `source` in this view mean
        something: a value labelled with a path it did not come from would
        pass every other assertion here.
        """
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096, exchange_state="working")
        self.reserved()
        document = self.document()
        checked = 0
        for row in rows_of(document):
            for fact in facts_in(row):
                if not fact["known"] or fact["source"] is None:
                    continue
                self.assertEqual(fact["value"],
                                 resolved(document, fact["source"]),
                                 fact["source"])
                checked += 1
        self.assertGreater(checked, 20)


class AnAssignedStageShowsItsWorker(VisibilityCase):

    def test_a_real_reservation_is_reported_with_its_worker_identity(self):
        self.submitted(submission(jobs=[job("job-a")]))
        allocation = self.reserved()
        held = self.row(self.document(), "job-a/implementation")["allocation"]
        self.assertEqual(held["presence"], "allocated")
        self.assertTrue(held["attempt_association"]["verified"])
        for member in ("assignment_id", "worker_id", "participant", "lane",
                       "generation", "allocation_state",
                       "selection_outcome"):
            self.assertTrue(held["facts"][member]["known"], member)
            self.assertEqual(held["facts"][member]["value"],
                             allocation[member], member)
        self.assertEqual(held["facts"]["reserved_at"]["value"],
                         allocation["reserved_at"])

    def test_a_reservation_exists_before_any_runtime_does(self):
        """Reserved, not yet started: the question an operator asks first."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.reserved()
        row = self.row(self.document(), "job-a/implementation")
        self.assertEqual(row["allocation"]["presence"], "allocated")
        self.assertEqual(row["runtime"]["presence"], "not-reported")
        self.assertFalse(row["runtime"]["facts"]["runtime_id"]["known"])

    def test_an_unallocated_stage_is_not_an_unknown_one(self):
        """The distinction the brief names: nobody reserved a worker, which is
        a fact, versus this document cannot be read, which is not."""
        self.submitted(submission(jobs=[job("job-a")]))
        held = self.row(self.document(), "job-a/implementation")["allocation"]
        self.assertEqual(held["presence"], "unallocated")
        self.assertIn("no worker reservation", held["reason"])
        self.assertFalse(held["facts"]["worker_id"]["known"])

    def test_a_malformed_allocation_is_unknown_and_says_which(self):
        document = self.submitted(submission(jobs=[job("job-a")])) and \
            self.document()
        document["jobs"][0]["stages"][0]["allocation"] = ["not", "a", "doc"]
        held = self.row(document, "job-a/implementation")["allocation"]
        self.assertEqual(held["presence"], "unknown")
        self.assertIn("other than a document", held["reason"])
        self.assertNotEqual(held["presence"], "unallocated")

    def test_the_reserved_workers_configured_profile_is_not_a_runtime_fact(self):
        self.submitted(submission(jobs=[job("job-a")]))
        allocation = self.reserved()
        row = self.row(self.document(), "job-a/implementation")
        self.assertEqual(
            row["allocation"]["facts"]["worker_profile_digest"]["value"],
            allocation["worker_profile_digest"])
        # AND THE STAGE'S OWN CONFIGURED PROFILE IS ITS OWN BLOCK, apart from
        # everything observed.
        self.assertEqual(
            row["configured_profile"]["facts"]["profile_digest"]["value"],
            PROFILE)
        self.assertEqual(row["runtime"]["presence"], "not-reported")


class TheRuntimeIsReportedAndNeverDiagnosed(VisibilityCase):

    def test_a_missing_runtime_is_an_absence_with_a_reason(self):
        self.submitted(submission(jobs=[job("job-a")]))
        held = self.row(self.document(), "job-a/implementation")["runtime"]
        self.assertEqual(held["presence"], "not-reported")
        self.assertIn("reports no runtime", held["reason"])
        for name, fact in held["facts"].items():
            self.assertFalse(fact["known"], name)
            self.assertIsNone(fact["value"], name)
        self.assertEqual(held["assignment"]["presence"], "not-reported")

    def test_a_reported_runtime_forwards_the_identity_and_the_axis_word(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(execution_runtime="quiescent")
        held = self.row(self.document(), "job-a/implementation")["runtime"]
        self.assertEqual(held["presence"], "reported")
        self.assertEqual(held["facts"]["runtime_id"]["value"], "runtime-1")
        self.assertEqual(held["facts"]["execution_runtime"]["value"],
                         "quiescent")

    def test_a_quiet_runtime_is_never_called_healthy_or_offline(self):
        """The whole family of defect this view is bounded against: a word
        this view invented standing in for an observation nobody made.

        ASSERTED OVER WHAT IS REPORTED, not over what is explained -- see
        `reported_words`. The producer's own axis word comes through unmapped,
        every freshness verdict stays `unknown`, and no value or state word in
        the row is a diagnosis.
        """
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(execution_runtime="quiescent")
        row = self.row(self.document(), "job-a/implementation")
        self.assertEqual(row["runtime"]["facts"]["execution_runtime"]["value"],
                         "quiescent")
        self.assertEqual(row["runtime"]["presence"], "reported")
        reported = [one.lower() for one in reported_words(row)]
        self.assertIn("quiescent", reported)
        for invented in INVENTED:
            self.assertNotIn(invented, reported, invented)
        for name in DERIVED:
            self.assertNotIn(name, keys_in(row), name)
        held = freshness_in(row)
        self.assertGreaterEqual(len(held), 3)
        for found in held:
            self.assertEqual(found["state"], "unknown")
            self.assertEqual(found["reason"], "no freshness policy selected")

    def test_the_runtime_association_is_declared_unverifiable_not_claimed(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running()
        held = self.row(self.document(), "job-a/implementation")["runtime"]
        self.assertFalse(held["attempt_association"]["verified"])
        self.assertIn("no attempt id on the runtime",
                      held["attempt_association"]["basis"])

    def test_the_fixed_assignment_is_reported_member_by_member(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running()
        held = self.row(self.document(),
                        "job-a/implementation")["runtime"]["assignment"]
        self.assertEqual(held["presence"], "reported")
        self.assertEqual(held["facts"]["work_id"]["value"], fixtures.WORK_A)
        self.assertEqual(held["facts"]["authority_uuid"]["value"], UUID)
        self.assertEqual(held["facts"]["participant"]["value"], fixtures.WHO)
        self.assertEqual(held["facts"]["generation"]["value"], 1)

    def test_a_malformed_runtime_is_unknown_rather_than_half_read(self):
        self.submitted(submission(jobs=[job("job-a")]))
        document = self.document()
        document["jobs"][0]["stages"][0]["runtime"] = "running"
        held = self.row(document, "job-a/implementation")["runtime"]
        self.assertEqual(held["presence"], "unknown")
        self.assertFalse(held["facts"]["execution_runtime"]["known"])


class TheActivityCountIsBytesAndNothingElse(VisibilityCase):

    def test_a_real_observation_carries_the_count_and_its_own_instant(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        held = self.row(self.document(), "job-a/implementation")["activity"]
        self.assertEqual(held["presence"], "observed")
        self.assertEqual(held["unit"], "bytes")
        self.assertEqual(held["facts"]["bytes_observed"]["value"], 4096)
        # THE INSTANT IS THE PRODUCER'S, CARRIED ON THE COUNT.
        self.assertEqual(
            held["facts"]["bytes_observed"]["observed_at"]["value"], NOW)
        self.assertEqual(held["facts"]["observed_at"]["value"], NOW)
        self.assertTrue(held["attempt_association"]["verified"])

    def test_the_count_is_bytes_and_is_not_offered_as_progress(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        held = self.row(self.document(), "job-a/implementation")["activity"]
        self.assertIn("bytes", held["what"])
        self.assertIn("not tokens", held["what"])
        for invented in ("token", "percent", "progress_percent"):
            self.assertNotIn(invented, json.dumps(held["facts"]))

    def test_a_runtime_without_activity_reports_nothing_observed(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=None)
        held = self.row(self.document(), "job-a/implementation")["activity"]
        self.assertEqual(held["presence"], "not-observed")
        self.assertFalse(held["facts"]["bytes_observed"]["known"])
        self.assertIsNone(held["facts"]["bytes_observed"]["value"])

    def test_a_recorded_attempt_nobody_observed_is_not_a_zero(self):
        """The producer's own `{bytes_observed: null, observed_at: null}`."""
        self.submitted(submission(jobs=[job("job-a")]))
        attempt_id = self.attempt_of()
        control, runtime = self.observed_runtime(attempt_id)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime=runtime,
                           activity=attempt_activity_of(control, attempt_id))
        held = self.row(self.document(), "job-a/implementation")["activity"]
        self.assertEqual(held["presence"], "not-observed")
        self.assertIn("observed none of its session stream", held["reason"])
        self.assertIsNone(held["facts"]["bytes_observed"]["value"])
        self.assertNotEqual(held["facts"]["bytes_observed"]["value"], 0)

    def test_an_observed_zero_is_a_known_zero(self):
        """Written through the real producer, which accepts a zero total and
        stamps it. `known: false` here would discard an observation that was
        actually made; `0` on the case above would invent one."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=0)
        held = self.row(self.document(), "job-a/implementation")["activity"]
        self.assertEqual(held["presence"], "observed")
        self.assertTrue(held["facts"]["bytes_observed"]["known"])
        self.assertEqual(held["facts"]["bytes_observed"]["value"], 0)
        self.assertEqual(
            held["facts"]["bytes_observed"]["observed_at"]["value"], NOW)

    def test_the_two_absences_and_the_zero_are_three_different_answers(self):
        """Side by side in one document, so none of them can pass because
        another one set the shape."""
        self.submitted(submission(jobs=[job("job-zero"), job("job-quiet"),
                                        job("job-bare")]))
        self.running("job-zero/implementation", total=0)
        self.running("job-quiet/implementation", total=None)
        document = self.document()
        zero = self.row(document, "job-zero/implementation")["activity"]
        quiet = self.row(document, "job-quiet/implementation")["activity"]
        bare = self.row(document, "job-bare/implementation")["activity"]
        self.assertEqual(
            [zero["presence"], quiet["presence"], bare["presence"]],
            ["observed", "not-observed", "unknown"])
        self.assertEqual(zero["facts"]["bytes_observed"]["value"], 0)
        self.assertIsNone(quiet["facts"]["bytes_observed"]["value"])
        self.assertIn("reports no runtime", bare["reason"])

    def test_a_malformed_count_is_unknown_and_never_evidence(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        document = self.document()
        for spoiled in ("4096", -1, True, 10 ** 400, {"bytes": 1}):
            held = copy.deepcopy(document)
            held["jobs"][0]["stages"][0]["runtime"]["activity"][
                "bytes_observed"] = spoiled
            found = self.row(held, "job-a/implementation")["activity"]
            self.assertEqual(found["presence"], "unknown", repr(spoiled)[:20])
            self.assertIsNone(found["facts"]["bytes_observed"]["value"])

    def test_a_malformed_activity_document_is_unknown_not_a_count(self):
        self.submitted(submission(jobs=[job("job-a")]))
        document = self.document()
        self.running(total=4096)
        document = self.document()
        document["jobs"][0]["stages"][0]["runtime"]["activity"] = 4096
        held = self.row(document, "job-a/implementation")["activity"]
        self.assertEqual(held["presence"], "unknown")
        self.assertIn("other than a document", held["reason"])


class NoObservationIsAttachedToAnAttemptThatDidNotEarnIt(VisibilityCase):
    """The restarted-episode rule, driven over real material.

    THE PAIRING IS ADVERSARIAL AND THE PARTS ARE NOT. Episode one's allocation
    and activity are the scheduler's and the Worker Manager's own documents;
    episode two's stage row is the projection's. The producer keeps them apart
    and this view must not depend on that.
    """

    def restarted(self):
        """Episode one, observed for real; then episode two, observed for real.

        THE OBSERVATION MOVES WITH THE EPISODE, and that correction is the
        whole reason this fixture is shaped the way it is. REVIEW
        2026-10-18T17-37-19Z: this used to open episode two and leave the fake
        control plane holding EPISODE ONE's claim -- `observed(claimed_by=True)`
        spells episode one's offer id and nothing moved it -- so
        `delegation._bound` refused the projection outright and all four cases
        below errored before the view was reached. That refusal is the
        producer defending itself correctly, and a fixture that provokes it is
        modelling a state the Worker Manager does not publish.

        SO EPISODE TWO GETS ITS OWN CLAIM, ITS OWN RECORDED ATTEMPT AND ITS
        OWN ACTIVITY, each through the producer that owns it, and the live
        episode's own `offer_id` is read back rather than derived here.

        AND THE ADVERSARIAL PAIRING IS KEPT -- it is now sharper than it was.
        Episode one's REAL allocation and REAL activity are returned so the
        cases below can graft them onto episode two's row, where they must
        displace episode two's own genuine facts and still be refused. Before
        this correction the row they were grafted onto had nothing of its own.
        """
        self.submitted(submission(jobs=[job("job-a")]))
        first = self.attempt_of()
        allocation = self.reserved()
        control, runtime = self.observed_runtime(first)
        activity = self.observed_activity(control, first, 4096)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime=runtime, activity=activity)
        before = self.document()
        live = episodes.live_of(self.jobs, "job-a/implementation")
        ended = episodes.end_episode(self.jobs, live,
                                     "abandoned-after-restart", 1)
        episodes.open_next(self.jobs, "job-a/implementation", ended)
        opened = episodes.live_of(self.jobs, "job-a/implementation")
        second = opened["attempt_id"]
        self.assertNotEqual(first, second)
        # EPISODE TWO'S OWN MATERIAL, through the same two producers, and a
        # DIFFERENT count so no case can pass on episode one's number.
        _control, restarted = self.observed_runtime(second, control=control)
        fresh = self.observed_activity(control, second, 8192)
        self.acts.observed("job-a/implementation",
                           claimed_by=opened["offer_id"],
                           runtime=dict(restarted, runtime_id="runtime-2",
                                        execution_runtime="running"),
                           activity=fresh)
        after = self.document()
        return first, second, allocation, activity, before, after

    def test_the_new_episode_is_the_one_reported(self):
        first, second, _allocation, _activity, _before, after = self.restarted()
        held = self.row(after, "job-a/implementation")["stage"]
        self.assertEqual(held["attempt_id"]["value"], second)
        self.assertEqual(held["episode"]["value"], 2)
        self.assertNotEqual(held["attempt_id"]["value"], first)

    def test_the_new_episodes_own_observation_is_the_one_reported(self):
        """What the grafts below have to displace.

        WITHOUT THIS THE REFUSALS PROVE LESS. A row carrying nothing of its
        own would answer `unknown` to an old episode's activity and to no
        activity at all, and the two cases could not be told apart. So the
        restarted stage's OWN count is established first, and the cases that
        graft episode one's facts on top are then refusing something in favour
        of a real alternative.
        """
        first, second, _allocation, _activity, before, after = self.restarted()
        was = self.row(before, "job-a/implementation")
        now = self.row(after, "job-a/implementation")
        self.assertEqual(was["activity"]["facts"]["bytes_observed"]["value"],
                         4096)
        self.assertEqual(now["activity"]["facts"]["bytes_observed"]["value"],
                         8192)
        self.assertTrue(now["activity"]["attempt_association"]["verified"])
        self.assertEqual(now["runtime"]["facts"]["runtime_id"]["value"],
                         "runtime-2")
        self.assertEqual(was["stage"]["attempt_id"]["value"], first)
        self.assertEqual(now["stage"]["attempt_id"]["value"], second)

    def test_the_old_episodes_allocation_is_refused_on_the_new_one(self):
        _first, _second, allocation, _activity, _before, after = \
            self.restarted()
        after["jobs"][0]["stages"][0]["allocation"] = allocation
        held = self.row(after, "job-a/implementation")["allocation"]
        self.assertEqual(held["presence"], "unknown")
        self.assertIn("does not belong to this stage's current attempt",
                      held["reason"])
        self.assertFalse(held["attempt_association"]["verified"])
        self.assertFalse(held["facts"]["worker_id"]["known"])
        self.assertNotIn(allocation["worker_id"],
                         json.dumps(self.row(after, "job-a/implementation")))

    def test_the_old_episodes_activity_is_refused_on_the_new_one(self):
        _first, _second, _allocation, activity, _before, after = \
            self.restarted()
        after["jobs"][0]["stages"][0]["runtime"] = {
            "runtime_id": "runtime-1", "execution_runtime": "running",
            "assignment": None, "activity": activity}
        held = self.row(after, "job-a/implementation")["activity"]
        self.assertEqual(held["presence"], "unknown")
        self.assertIn("names another attempt", held["reason"])
        self.assertIsNone(held["facts"]["bytes_observed"]["value"])
        self.assertNotIn("4096", json.dumps(held))

    def test_the_episode_instant_comes_from_the_live_record_only(self):
        """No history fallback: the ended episode's `opened_at` is in the same
        document and must not become the current episode's."""
        _first, _second, _allocation, _activity, _before, after = \
            self.restarted()
        stage = after["jobs"][0]["stages"][0]
        self.assertEqual([one["episode"] for one in stage["episodes"]], [1, 2])
        held = self.row(after, "job-a/implementation")["stage"]
        self.assertEqual(held["episode_opened_at"]["source"],
                         "jobs[0].stages[0].episodes[1].opened_at")
        self.assertEqual(held["episode_opened_at"]["value"],
                         stage["episodes"][1]["opened_at"])

    def test_an_ended_record_under_the_current_number_is_not_read(self):
        """A document that contradicts itself answers unknown rather than
        publishing the instant of an attempt that is over."""
        self.submitted(submission(jobs=[job("job-a")]))
        document = self.document()
        stage = document["jobs"][0]["stages"][0]
        stage["episodes"][0]["ended_state"] = "abandoned-after-restart"
        stage["episodes"][0]["ended_at"] = NOW
        held = self.row(document, "job-a/implementation")["stage"]
        self.assertFalse(held["episode_opened_at"]["known"])
        self.assertIn("no live record", held["episode_opened_at"][
            "unknown_reason"])

    def test_a_stage_between_episodes_reports_no_attempt_and_no_facts(self):
        """`_observed_state`'s honest gap: an ended episode with no
        replacement names no attempt, so nothing may be attached to one."""
        self.submitted(submission(jobs=[job("job-a")]))
        live = episodes.live_of(self.jobs, "job-a/implementation")
        episodes.end_episode(self.jobs, live, "abandoned-after-restart", 1)
        row = self.row(self.document(), "job-a/implementation")
        self.assertFalse(row["stage"]["attempt_id"]["known"])
        self.assertFalse(row["stage"]["episode"]["known"])
        self.assertEqual(row["allocation"]["presence"], "unallocated")
        self.assertEqual(row["activity"]["presence"], "unknown")


class TheExchangeIsReportedAsItWasAnswered(VisibilityCase):

    def test_an_unread_exchange_is_nobody_looked_rather_than_idle(self):
        self.submitted(submission(jobs=[job("job-a")]))
        held = self.row(self.document(), "job-a/implementation")["exchange"]
        self.assertEqual(held["presence"], "not-read")
        self.assertIn("nobody looked", held["reason"])

    def test_a_read_exchange_reports_its_state_and_the_receipts_instant(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(exchange_state="working")
        held = self.row(self.document(), "job-a/implementation")["exchange"]
        self.assertEqual(held["presence"], "reported")
        self.assertEqual(held["facts"]["state"]["value"], "working")
        self.assertEqual(held["receipt"]["accepted_at"]["value"], NOW)
        self.assertFalse(held["attempt_association"]["verified"])

    def test_an_exchange_with_no_command_yet_is_not_a_malformed_one(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(exchange_state="not-requested")
        document = self.document()
        document["jobs"][0]["stages"][0]["exchange"]["command"] = None
        held = self.row(document, "job-a/implementation")["exchange"]
        self.assertFalse(held["command"]["command_digest"]["known"])
        self.assertIn("as null",
                      held["command"]["command_digest"]["unknown_reason"])

    def test_worker_authored_entry_names_are_never_forwarded(self):
        """`foreign` is bytes a container chose. Reporting them here would
        make this view their publisher."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(exchange_state="working")
        document = self.document()
        document["jobs"][0]["stages"][0]["exchange"]["foreign"] = [
            "/etc/shadow", "secret-token.txt"]
        held = json.dumps(self.row(document, "job-a/implementation"))
        self.assertNotIn("shadow", held)
        self.assertNotIn("secret-token", held)


class TheSafeAllowlistIsTheWholeSurface(VisibilityCase):

    def spoiled(self):
        """A real document with untrusted material added everywhere this view
        reads. Every one of these is a member the allowlists do not name."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096, exchange_state="working")
        allocation = self.reserved()
        document = self.document()
        stage = document["jobs"][0]["stages"][0]
        stage["allocation"] = dict(allocation,
                                   bearer="bearer-SECRET",
                                   release_reason="raw log: SECRET")
        stage["runtime"]["argv"] = ["docker", "run", "--token", "SECRET"]
        stage["runtime"]["credentials"] = {"api_key": "SECRET"}
        stage["runtime"]["activity"]["transcript_path"] = "/private/SECRET"
        stage["exchange"]["payload"] = {"stdout": "SECRET"}
        stage["context_path"] = "/private/context/SECRET"
        return document

    def test_nothing_outside_the_allowlists_reaches_the_view(self):
        """The planted material, by VALUE and by MEMBER NAME.

        BY NAME AS WELL AS BY VALUE, because a member forwarded empty is still
        one this surface republished. AND BY THE PLANTED NAMES RATHER THAN BY
        WORD: `_context`'s note states that this view reads no transcript,
        provider session or private context path, and the earlier assertion
        here searched the whole document for `transcript` and so forbade the
        sentence that states the guarantee.
        """
        document = self.spoiled()
        projected = visibility(document)
        held = json.dumps(projected)
        # EVERY PLANTED VALUE, none of which is in any allowlist.
        for planted in ("SECRET", "/private/", "bearer-", "docker",
                        "--token", "raw log"):
            self.assertNotIn(planted, held, planted)
        # AND EVERY PLANTED MEMBER NAME.
        reported = keys_in(projected)
        for planted in ("argv", "credentials", "api_key", "transcript_path",
                        "bearer", "release_reason", "payload", "context_path",
                        "foreign"):
            self.assertNotIn(planted, reported, planted)

    def test_the_allowlisted_members_still_come_through(self):
        """A filter that dropped everything would pass the case above."""
        document = self.spoiled()
        row = self.row(document, "job-a/implementation")
        self.assertTrue(row["allocation"]["facts"]["worker_id"]["known"])
        self.assertEqual(row["runtime"]["facts"]["runtime_id"]["value"],
                         "runtime-1")
        self.assertEqual(row["activity"]["facts"]["bytes_observed"]["value"],
                         4096)

    def test_the_source_document_is_not_mutated_by_being_viewed(self):
        document = self.spoiled()
        before = json.dumps(document, sort_keys=True)
        visibility(document)
        rows_of(document)
        self.assertEqual(json.dumps(document, sort_keys=True), before)

    def test_an_overlong_text_member_is_unknown_rather_than_republished(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running()
        document = self.document()
        document["jobs"][0]["stages"][0]["runtime"]["runtime_id"] = "x" * 5000
        held = self.row(document, "job-a/implementation")["runtime"]
        self.assertFalse(held["facts"]["runtime_id"]["known"])
        self.assertNotIn("x" * 300, json.dumps(held))

    def test_no_locator_inside_the_document_is_followed(self):
        """A visibility view that opened what a locator names would be reading
        whatever that names rather than reporting this document."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.acts.frozen("job-a/implementation", "completed", artifacts=[
            {"output_name": "proposal", "artifact_id": "artifact-1",
             "media_type": "application/x-patch", "bytes": 1024,
             "content_digest": "sha256:" + "d" * 64,
             "locator": "/private/never-opened.patch"}])
        document = self.document()
        opened = []
        real = open

        def watched(*args, **kwargs):
            opened.append(args[0] if args else None)
            return real(*args, **kwargs)

        with mock.patch("builtins.open", watched):
            held = json.dumps(visibility(document))
        self.assertEqual(opened, [])
        self.assertNotIn("never-opened", held)


class TheSnapshotsOwnInstantIsOnlyEverTheQueryTime(VisibilityCase):

    def test_the_query_time_is_named_as_such_and_not_as_contact(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        held = visibility(self.document(observed_at=QUERY_AT))
        self.assertEqual(held["snapshot"]["query_time"]["value"], QUERY_AT)
        self.assertIn("not a worker contact time",
                      held["snapshot"]["query_time_note"])

    def test_no_fact_borrows_the_query_time_as_its_own(self):
        """The defect this guards: a view with one timestamp to hand reporting
        it wherever an instant was wanted."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        row = self.row(self.document(observed_at=QUERY_AT),
                       "job-a/implementation")
        self.assertNotEqual(NOW, QUERY_AT)
        for fact in facts_in(row):
            self.assertNotEqual(fact["value"], QUERY_AT,
                                fact.get("source"))

    def test_contact_and_context_are_unsupported_with_the_reason(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        row = self.row(self.document(), "job-a/implementation")
        contact = row["contact"]["facts"]["last_contact"]
        self.assertFalse(contact["known"])
        self.assertEqual(contact["unknown_reason"],
                         "unsupported by this status contract")
        self.assertIn("snapshot query time is not one", row["contact"]["note"])
        for name in ("context_used", "context_limit"):
            fact = row["context"]["facts"][name]
            self.assertFalse(fact["known"])
            self.assertEqual(fact["unknown_reason"],
                             "unsupported by this status contract")

    def test_no_per_field_observation_time_is_invented(self):
        """Only the members the contract gives an instant to have one."""
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        row = self.row(self.document(), "job-a/implementation")
        timed = [fact for fact in facts_in(row)
                 if isinstance(fact.get("observed_at"), dict)
                 and fact["observed_at"]["known"]]
        self.assertEqual([fact["source"] for fact in timed],
                         ["jobs[0].stages[0].runtime.activity.bytes_observed"])
        for fact in facts_in(row):
            if isinstance(fact.get("observed_at"), dict) \
                    and not fact["observed_at"]["known"]:
                self.assertTrue(fact["observed_at"]["unknown_reason"])


class FreshnessIsNotDecidedHere(VisibilityCase):

    def test_freshness_is_unknown_with_the_selected_reason(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        held = visibility(self.document())
        row = held["stages"][0]
        for found in (held["freshness"], row["freshness"],
                      row["activity"]["freshness"], row["contact"]["freshness"]):
            self.assertEqual(found["state"], "unknown")
            self.assertEqual(found["reason"], "no freshness policy selected")

    def test_an_old_observation_cannot_become_fresh_by_being_read_again(self):
        """The viewer's claim168071 defect, in this surface's terms: the same
        unchanged source read many times answers the same instants and never a
        verdict about them.

        THE CLAIM IS SEMANTIC AND SO IS THE ASSERTION. What must not change is
        the reported instant; what must not appear is a freshness VERDICT or a
        derived age -- not the words `fresh` and `stale` inside the sentence
        that says this view publishes neither.
        """
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        document = self.document()
        first = visibility(document)
        for _ in range(3):
            self.assertEqual(visibility(document), first)
        # THE INSTANT IS STILL THE PRODUCER'S, UNMOVED.
        row = first["stages"][0]
        self.assertEqual(row["activity"]["facts"]["observed_at"]["value"], NOW)
        self.assertEqual(
            row["activity"]["facts"]["bytes_observed"]["observed_at"]["value"],
            NOW)
        held = freshness_in(first)
        self.assertGreaterEqual(len(held), 4)
        for found in held:
            self.assertEqual(found["state"], "unknown")
            self.assertEqual(found["reason"], "no freshness policy selected")
        reported = [one.lower() for one in reported_words(first)]
        for invented in INVENTED:
            self.assertNotIn(invented, reported, invented)
        for name in DERIVED:
            self.assertNotIn(name, keys_in(first), name)

    def test_a_local_read_time_is_named_separately_and_alters_nothing(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        document = self.document()
        bare = visibility(document)
        early = visibility(document, read_at="2026-09-02T01:00:00.000Z")
        late = visibility(document, read_at="2027-01-01T00:00:00.000Z")
        self.assertEqual(early["stages"], late["stages"])
        self.assertEqual(early["stages"], bare["stages"])
        self.assertEqual(early["snapshot"], late["snapshot"])
        self.assertEqual(late["read"]["local_read_time"]["value"],
                         "2027-01-01T00:00:00.000Z")
        self.assertFalse(bare["read"]["local_read_time"]["known"])

    def test_a_local_read_time_that_is_not_an_instant_refuses(self):
        self.submitted(submission(jobs=[job("job-a")]))
        with self.assertRaises(VisibilityRefusal):
            visibility(self.document(), read_at="yesterday-ish")


class TheDocumentIsValidatedBeforeAnythingIsReported(VisibilityCase):

    def test_an_unsupported_schema_refuses(self):
        self.submitted()
        document = self.document()
        document["schema"] = "baton.v12.job-status/99"
        with self.assertRaises(VisibilityRefusal) as caught:
            visibility(document)
        self.assertIn("baton.v12.job-status/6", str(caught.exception))

    def test_the_refusal_does_not_echo_the_rejected_input(self):
        """A message assembled out of an untrusted document lets that document
        choose what lands in a log."""
        self.submitted()
        document = self.document()
        document["schema"] = "baton.v12.job-status/" + "A" * 4000
        with self.assertRaises(VisibilityRefusal) as caught:
            visibility(document)
        held = str(caught.exception)
        self.assertNotIn("A" * 40, held)
        self.assertLess(len(held), 400)

    def test_a_malformed_envelope_refuses_rather_than_reporting_rows(self):
        """Including the two near-instants REVIEW 2026-10-18T17-37-19Z found
        accepted: a bare date, and a naive time in no zone."""
        self.submitted()
        for spoiled in ({"observed_at": None}, {"observed_at": "whenever"},
                        {"observed_at": "2026-09-02T00:00:00.000Z" + "0" * 40},
                        {"observed_at": "2026-10-18"},
                        {"observed_at": "2026-10-18T12:00:00"},
                        {"observed_at": "2026-10-18T12:00:00Z"},
                        {"observed_at": "2026-10-18T12:00:00+00:00"},
                        {"observed_at": "2026-9-02T00:00:00.0000Z"},
                        {"observed_at": "2026-99-99T99:99:99.999Z"},
                        {"canonical": "yes"}, {"jobs": {"job-a": {}}},
                        {"jobs": None}, {"incarnation": 7}):
            document = self.document()
            document.update(spoiled)
            with self.assertRaises(VisibilityRefusal):
                visibility(document)

    def test_a_malformed_nested_structure_refuses(self):
        """The viewer's claim168169 shape: a document with the right schema
        whose stages are not documents.

        `{"stages": null}` AND A JOB WITH NO STAGES AT ALL ARE IN THE LIST.
        REVIEW 2026-10-18T17-37-19Z: both were accepted as a Job with zero
        rows, so a malformed document answered a confident, machine-readable
        "no stage is in any state". See `worker_visibility._enumerable` for why
        this surface is deliberately stricter than the terminal viewer here.
        """
        self.submitted()
        for spoiled in ([None], [{"stages": None}], [{"stages": [None]}],
                        [{"stages": [{"episodes": 7}]}], [{"job_id": "job-a"}],
                        [{"stages": {"job-a/implementation": {}}}]):
            document = self.document()
            document["jobs"] = spoiled
            with self.assertRaises(VisibilityRefusal):
                visibility(document)

    def test_a_job_whose_stages_are_unreadable_publishes_no_row_at_all(self):
        """NOT EVEN THE READABLE JOBS, which is the decision worth stating.

        A document carrying one good Job and one whose stages cannot be read
        is refused whole. Publishing the good Job's rows would answer a
        consumer's "every current stage" with a subset it has no way to know
        was a subset.
        """
        self.submitted()
        document = self.document()
        self.assertEqual(len(document["jobs"]), 2)
        document["jobs"][1] = dict(document["jobs"][1], stages=None)
        with self.assertRaises(VisibilityRefusal) as caught:
            visibility(document)
        self.assertIn("row set this document does not support",
                      str(caught.exception))
        self.assertNotIn("job-b", str(caught.exception))

    def test_the_instant_grammar_is_the_producers_own(self):
        """ACCEPTED EXACTLY WHEN THE PRODUCER'S BOUNDARY ACCEPTS.

        `worker_visibility` restates `boundaries.GRAMMAR` rather than importing
        it, because importing it would import the Worker Manager package --
        the owner of the control store this view must not be able to open, and
        a boundary `TheViewOpensNothingAndActsNotAtAll` traps. This is what
        keeps the restatement from drifting: the same vector list through both.
        """
        from baton_v12.worker_manager import boundaries

        vectors = (NOW, LATER, "2026-09-02T00:00:00.000Z",
                   "2026-10-18", "2026-10-18T12:00:00",
                   "2026-10-18T12:00:00Z", "2026-10-18T12:00:00+00:00",
                   "2026-10-18T12:00:00.000000Z",
                   "2026-9-02T00:00:00.0000Z",
                   "2026-99-99T99:99:99.999Z",
                   "2026-02-30T00:00:00.000Z",
                   "2026-09-02t00:00:00.000z", "2026-09-02T00:00:00.000",
                   " 2026-09-02T00:00:00.000Z", "", "whenever",
                   "٢026-09-02T00:00:00.000Z")
        agreed = 0
        for text in vectors:
            try:
                boundaries.instant(text, "an instant")
            except ContractRefusal:
                owned = False
            else:
                owned = True
            self.assertEqual(
                worker_visibility._instant_text(text) is not None, owned,
                repr(text))
            agreed += 1
        self.assertEqual(agreed, len(vectors))
        self.assertTrue(worker_visibility._instant_text(NOW))

    def test_a_near_instant_is_not_a_known_source_time(self):
        """And the fact it would have timed keeps its own value.

        THE TWO ARE SEPARATE FACTS. A malformed observation time does not
        discard the count the producer really recorded; it makes the count's
        TIME unknown with a bounded reason, which is a consumer being told
        what it does not know rather than being handed a guess.
        """
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        for spoiled in ("2026-10-18", "2026-10-18T12:00:00",
                        "2026-10-18T12:00:00Z", 1760000000, "", None):
            document = self.document()
            document["jobs"][0]["stages"][0]["runtime"]["activity"][
                "observed_at"] = spoiled
            held = self.row(document, "job-a/implementation")["activity"]
            self.assertEqual(held["presence"], "observed", repr(spoiled))
            self.assertEqual(held["facts"]["bytes_observed"]["value"], 4096)
            when = held["facts"]["bytes_observed"]["observed_at"]
            self.assertFalse(when["known"], repr(spoiled))
            self.assertIsNone(when["value"])
            self.assertTrue(when["unknown_reason"])
            self.assertFalse(held["facts"]["observed_at"]["known"])
            if isinstance(spoiled, str) and spoiled:
                # AND THE REJECTED TEXT IS NOT REPUBLISHED as the value it was
                # refused as being.
                self.assertNotIn(spoiled, json.dumps(held))

    def test_a_list_or_a_scalar_is_not_a_status_document(self):
        for spoiled in ([], 7, "status", None):
            with self.assertRaises(VisibilityRefusal):
                visibility(spoiled)

    def test_the_schema_this_view_reads_is_the_producers_own_constant(self):
        from baton_v12.job_manager import documents

        self.assertEqual(worker_visibility.SOURCE_SCHEMA,
                         documents.STATUS_SCHEMA)
        self.assertEqual(documents.STATUS_SCHEMA, "baton.v12.job-status/6")

    def test_an_oversize_document_refuses_rather_than_truncating(self):
        self.submitted()
        body = json.dumps(self.document()).encode("utf-8")
        body += b" " * (worker_visibility.MAX_SNAPSHOT_BYTES + 1 - len(body))
        with self.assertRaises(VisibilityRefusal) as caught:
            visibility(body)
        self.assertIn("unknown subset", str(caught.exception))

    def test_the_input_bound_is_the_existing_viewers_own(self):
        from tools import job_viewer

        self.assertEqual(worker_visibility.MAX_SNAPSHOT_BYTES,
                         job_viewer.MAX_SNAPSHOT_BYTES)


class TheCommandReadsAFileAndAnswersJSON(VisibilityCase):

    def written(self, document=None, *, name="status.json"):
        place = os.path.join(self.root, name)
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document if document is not None else self.document(),
                      handle)
        return place

    def ran(self, argv):
        import io

        stream = io.StringIO()
        code = worker_visibility.main(argv, stream=stream)
        return code, stream.getvalue()

    def test_it_reads_a_status_document_an_operator_already_has(self):
        self.submitted()
        self.running(total=4096)
        code, output = self.ran(["--snapshot", self.written()])
        self.assertEqual(code, 0)
        held = json.loads(output)
        self.assertEqual(held["schema"], "baton.v12.worker-visibility/1")
        self.assertEqual([one["stage"]["stage_id"]["value"]
                          for one in held["stages"]],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])
        self.assertEqual(
            held["stages"][0]["activity"]["facts"]["bytes_observed"]["value"],
            4096)

    def test_the_command_answers_the_same_facts_the_function_does(self):
        self.submitted(submission(jobs=[job("job-a")]))
        self.running(total=4096)
        document = self.document()
        code, output = self.ran(["--snapshot", self.written(document)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["stages"], visibility(
            document)["stages"])

    def test_an_unreadable_file_refuses_in_JSON_with_status_two(self):
        code, output = self.ran(["--snapshot",
                                 os.path.join(self.root, "absent.json")])
        self.assertEqual(code, 2)
        self.assertIn("refused", json.loads(output))

    def test_an_unsupported_version_refuses_in_JSON_with_status_two(self):
        self.submitted()
        document = self.document()
        document["schema"] = "baton.v12.job-status/99"
        code, output = self.ran(["--snapshot", self.written(document)])
        self.assertEqual(code, 2)
        self.assertIn("baton.v12.job-status/6", json.loads(output)["refused"])
        self.assertNotIn("stages", json.loads(output))

    def test_an_oversize_file_refuses_rather_than_reading_a_subset(self):
        self.submitted()
        place = self.written()
        with open(place, "a", encoding="utf-8") as handle:
            handle.write(" " * (worker_visibility.MAX_SNAPSHOT_BYTES + 1))
        code, output = self.ran(["--snapshot", place])
        self.assertEqual(code, 2)
        self.assertIn("unknown subset", json.loads(output)["refused"])

    def test_the_module_is_callable_as_a_module(self):
        """`python3 -m tools.worker_visibility` is the named interface."""
        self.assertTrue(hasattr(worker_visibility, "main"))
        source = pathlib.Path(worker_visibility.__file__).read_text(
            encoding="utf-8")
        self.assertIn('if __name__ == "__main__":', source)


class TheViewOpensNothingAndActsNotAtAll(VisibilityCase):
    """THE BOUNDARIES ARE TRAPPED rather than described.

    Every owner below raises if the view reaches it, so "no store, no model,
    no probe, no scheduler act, no subprocess, no write" is the owners' own
    refusal rather than this file's assurance.
    """

    def traps(self, guards):
        import sqlite3
        import subprocess

        for owner, method in ((JobStore, "open"), (ControlStore, "open"),
                              (scheduler, "reserve"),
                              (scheduler, "activate_pool"),
                              (subprocess, "run"), (subprocess, "Popen"),
                              (sqlite3, "connect")):
            guards.enter_context(mock.patch.object(
                owner, method,
                side_effect=AssertionError("the view acted: "
                                           + getattr(owner, "__name__",
                                                     str(owner))
                                           + "." + method)))

    def test_projecting_opens_no_store_and_performs_no_act(self):
        from contextlib import ExitStack

        self.submitted()
        self.running(total=4096, exchange_state="working")
        self.reserved()
        document = self.document()
        before = list(self.acts.calls)
        with ExitStack() as guards:
            self.traps(guards)
            held = visibility(document)
            rows_of(document)
        self.assertEqual(len(held["stages"]), 3)
        self.assertEqual(self.acts.calls, before)

    def test_the_command_opens_no_store_and_performs_no_act(self):
        from contextlib import ExitStack
        import io

        self.submitted()
        place = os.path.join(self.root, "status.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(self.document(), handle)
        before = list(self.acts.calls)
        with ExitStack() as guards:
            self.traps(guards)
            stream = io.StringIO()
            code = worker_visibility.main(["--snapshot", place],
                                          stream=stream)
        self.assertEqual(code, 0)
        self.assertEqual(self.acts.calls, before)
        self.assertEqual(json.loads(stream.getvalue())["source_schema"],
                         "baton.v12.job-status/6")

    def test_the_stores_are_unchanged_by_being_viewed(self):
        """The disposable owner state is established before and compared
        after, rather than assumed."""
        self.submitted()
        self.running(total=4096)
        before = json.dumps(self.document(), sort_keys=True)
        for _ in range(3):
            visibility(self.document())
        self.assertEqual(json.dumps(self.document(), sort_keys=True), before)

    def test_the_module_imports_no_store_engine_or_subprocess(self):
        """Read the imports rather than the paragraph promising the absence."""
        source = pathlib.Path(worker_visibility.__file__).read_text(
            encoding="utf-8")
        names = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                names.update(one.name for one in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        self.assertEqual(names, {"argparse", "datetime", "json", "sys",
                                 "baton_v12.job_manager", "tools"})

    def test_the_module_names_no_act_and_no_reader_of_its_own(self):
        """The identifiers, not the prose: this module's docstring promises
        the absence of several of these words, so a text search would find the
        promise rather than an act."""
        source = pathlib.Path(worker_visibility.__file__).read_text(
            encoding="utf-8")
        used = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
        for absent in ("serve", "submit", "claim", "cancel", "reconcile",
                       "sweep", "reserve", "probe", "inquire", "scheduler",
                       "JobStore", "ControlStore", "Deployment", "connect",
                       "execute", "executemany", "commit", "cursor",
                       "subprocess", "run", "Popen", "status",
                       "observation_of", "operations_from"):
            self.assertNotIn(absent, used, absent)

    def test_job_status_six_is_unchanged_by_this_work(self):
        """The contract this view reads is the producer's and stays theirs."""
        from baton_v12.job_manager import documents

        self.assertEqual(documents.STATUS_SCHEMA, "baton.v12.job-status/6")
        self.assertEqual(
            documents.CONTRACTS["stage.status"][0],
            ("stage_id", "job_id", "kind", "state", "work_id", "profile_name",
             "profile_digest", "episode", "offer_id", "attempt_id",
             "episodes", "corrections", "allocation", "allocations", "gates",
             "receipts", "deferral", "runtime", "exchange", "artifacts"))


class TheUnreadManagerIsNotAQuietDeployment(VisibilityCase):

    def test_a_projection_with_no_control_store_says_nobody_looked(self):
        self.submitted()
        held = visibility(self.unread())
        self.assertFalse(held["snapshot"]["canonical"]["value"])
        self.assertEqual(len(held["stages"]), 3)
        for row in held["stages"]:
            self.assertEqual(row["runtime"]["presence"], "not-reported")
            self.assertEqual(row["activity"]["presence"], "unknown")

    def test_a_canonical_read_says_so(self):
        self.submitted()
        held = visibility(self.document())
        self.assertTrue(held["snapshot"]["canonical"]["value"])

    def test_an_empty_store_reports_no_rows_rather_than_a_quiet_one(self):
        held = visibility(self.document())
        self.assertEqual(held["stages"], [])
        self.assertTrue(held["snapshot"]["canonical"]["value"])


class TheSweptPipelineIsReportedToo(VisibilityCase):
    """One pass of the real sweep, so the view is exercised over a document
    whose stages have actually been admitted rather than only submitted."""

    def test_an_admitted_stage_reports_its_offer_and_attempt(self):
        self.submitted(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        document = self.document()
        row = self.row(document, "job-a/implementation")
        stage = document["jobs"][0]["stages"][0]
        self.assertEqual(row["stage"]["state"]["value"], stage["state"])
        self.assertEqual(row["stage"]["offer_id"]["value"], stage["offer_id"])
        self.assertEqual(row["stage"]["attempt_id"]["value"],
                         stage["attempt_id"])
        self.assertEqual(row["allocation"]["presence"], "unallocated")


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
