"""W103076 -- independent review, and the round that follows a rejection.

WHAT THESE CASES ARE ABOUT. Two things this control plane could not do:
advance a Job past a `changes-requested` verdict, and end an implementation
attempt into a published, immutable checkpoint instead of a v11 review Route.
They are not about what a checkpoint IS, who may review one, or when an offer
is owed -- `tests/manager/test_review_cycles.py` drives the custody provider
and `tests/job_manager/test_scheduling.py` drives the pool.

THE CUSTODY PROVIDER IS REAL HERE. The line, its writer, its frozen checkpoint
and its verdict are the accepted operations against a real control store, with
fakes only where a deployment would supply one: the checkpoint profile, the
authority-bound fence port and the runtime adapter. A correction round proved
against a fake line would be proving this suite's idea of `correction-ready`
rather than the one `record_verdict` actually writes.
"""

import copy
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import (POOL_SCHEMA, JobStore, Unobserved,
                                   activate_pool, episodes, reserve,
                                   review_driver, status, submit)
from baton_v12.job_manager.documents import CORRECTION_ENDINGS
from baton_v12.worker_manager import (ControlStore, certify_profile,
                                      create_line, grant_writer, line_of)
from baton_v12.worker_manager.source_boundary import nominate_source
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 configure_workspace_storage)

from tests.manager import input_roots
from tests.manager.disk_roots import disk_backed_under

from .fixtures import NOW, PROFILE, UUID, WORK_A, WORK_B, job, stage

BASE = "a" * 40
WRITER = "baton.impl"
REVIEWER = "baton.review"


class Port:
    """The authority-bound fence session, answering exactly what it is asked.

    It carries `assignment_of` as well as `cancel` because the composed freeze,
    intake, retention and cleanup all reach one of the two, and an ending that
    typed only `cancel` would discover the other in the middle of itself.
    """

    def __init__(self, participant):
        self.participant = participant
        self.calls = []

    def assignment_of(self, work_id):
        self.calls.append(("assignment_of", work_id))
        return None

    def cancel(self, expect, operation_id, reason, work_id, authority_uuid):
        self.calls.append((dict(expect), reason))
        return {"operation_id": operation_id, "participant": self.participant,
                "generation": expect["generation"], "status": "fenced"}


class Profile:
    """The checkpoint profile a deployment configures, with no VCS behind it."""

    name = "reference"

    def __init__(self):
        self.held = {}
        self.current_revision = None

    def materialize(self, source, repository, declared_base):
        if not os.path.exists(repository):
            os.mkdir(repository)
        return {"profile": self.name, "base": declared_base,
                "head": declared_base}

    def freeze(self, repository, *, line_id, revision, declared_base):
        head = f"{revision:040x}"
        paths = [f"round-{revision}.txt"]
        evidence = {"profile": self.name, "base": declared_base, "head": head,
                    "tree": f"{revision + 100:040x}", "paths": paths,
                    "path_set_digest": digest(paths),
                    "reference": f"checkpoint/{line_id}/{revision}"}
        self.held[revision] = evidence
        self.current_revision = revision
        return dict(evidence)

    def validate(self, repository, evidence, *, current=False):
        revision = int(evidence["head"], 16)
        if self.held.get(revision) != evidence:
            raise ContractRefusal("policy", "profile-uncertified",
                                  "checkpoint evidence is not retained")
        if current and self.current_revision != revision:
            raise ContractRefusal("policy", "profile-uncertified",
                                  "the line no longer matches this checkpoint")
        return dict(evidence)


def one_work_submission(submission_id="sub-1"):
    """One Job whose implementation and review stages name the SAME Work.

    The package's default fixture names two -- which the generic parser admits
    and the line provider can never attach, because a line is one
    `(authority_uuid, work_id)` pair and its reviewer is an assignment of that
    same Work. Both shapes are driven below; this is the one a real submission
    for this pipeline has to have.
    """
    return {"schema": "baton.v12.job-submission/1",
            "submission_id": submission_id,
            "jobs": [job("job-a", stages=[
                stage("implementation", WORK_A),
                stage("review", WORK_A,
                      depends_on=[{"job_id": "job-a",
                                   "kind": "implementation"}])])]}


class DriverCase(unittest.TestCase):
    """One Job store, one control store, and one durable development line."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-review-driver-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.source = os.path.join(self.root, "source")
        os.mkdir(self.source)
        self.storage = os.path.join(disk_backed_under(self), "storage")
        os.mkdir(self.storage)
        self.instants = [NOW]
        self.control = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="manager-1", clock=self.clock)
        self.addCleanup(self.control.close)
        certify_profile(self.control, "runtime", "reference", PROFILE)
        self.group = input_roots.configured_group(self.control)
        configure_workspace_storage(self.control, self.storage)
        self.profile = Profile()
        self.ports = {}
        self.jobs = JobStore.open(os.path.join(self.root, "jobs.sqlite3"),
                                  authority_uuid=UUID, incarnation="jobs-1",
                                  clock=self.clock)
        self.addCleanup(self.jobs.close)
        submit(self.jobs, one_work_submission())
        self.line = create_line(self.control, source=nominate_source(self.source),
                                declared_base=BASE, profile=self.profile,
                                authority_uuid=UUID, work_id=WORK_A)

    def clock(self):
        return self.instants[-1]

    def port(self, participant):
        return self.ports.setdefault(participant, Port(participant))

    # -- the manager rows a runtime would have written -----------------------

    def attempt(self, attempt_id, generation, participant, principal,
                work_id=WORK_A):
        self.control._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, ?, ?, ?, 'scope', "
            "'role', 'grant', 1)",
            (attempt_id, NOW, work_id, UUID, participant, generation,
             generation, principal))
        # THE DEPLOYMENT'S HALF, PERFORMED HERE BECAUSE IT IS THE
        # DEPLOYMENT'S. `writer_boundary` and `review_boundary` compose mounts
        # over an assignment workspace the manager already owns; creating one
        # inside the driver would be this leaf choosing where work happens,
        # which is W103083's.
        assignment_workspace(self.group, self.storage, attempt_id)
        return attempt_id

    def completed(self, attempt_id, *, review=False):
        self.control._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'quiescent', worker_disposition = 'completed' "
            "WHERE runtime_attempt_id = ?", ("runtime-" + attempt_id,
                                             attempt_id))
        if not review:
            return
        self.control._connection.execute(
            "UPDATE attempts SET output = 'frozen', verification = 'passed' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        self.control._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES (?, ?, "
            "'completed', ?, ?, ?)",
            (attempt_id, "result-" + attempt_id, "sha256:" + "1" * 64,
             "freeze-" + attempt_id, NOW))
        for name, filler in (("findings", "2"), ("logs", "3")):
            self.control._connection.execute(
                "INSERT INTO output_artifacts (runtime_attempt_id, "
                "output_name, artifact_id, media_type, bytes, content_digest, "
                "locator) VALUES (?, ?, ?, 'text/plain', 1, ?, ?)",
                (attempt_id, name, f"artifact-{name}-{attempt_id}",
                 "sha256:" + filler * 64, f"custody/{attempt_id}/{name}"))

    # -- one round of the accepted custody provider --------------------------

    def round(self, number, disposition, *, based=None):
        """Writer, frozen checkpoint, independent reviewer, recorded verdict."""
        writer_attempt = self.attempt(f"writer-attempt-{number}", number,
                                      WRITER, f"writer-principal-{number}")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=number,
            worker_id=f"impl-worker-{number}", profile=self.profile,
            based_checkpoint_id=based)
        self.completed(writer_attempt)
        from baton_v12.worker_manager import freeze_checkpoint
        checkpoint = freeze_checkpoint(
            self.control, writer_id=writer["writer_id"], generation=number,
            profile=self.profile, port=self.port(WRITER))
        review_attempt = self.attempt(f"review-attempt-{number}", number,
                                      REVIEWER, f"review-principal-{number}")
        attached = review_driver.prepare_review(
            self.control, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=review_attempt, generation=number,
            reviewer_worker_id=f"review-worker-{number}", profile=self.profile)
        self.completed(review_attempt, review=True)
        from baton_v12.worker_manager import record_verdict
        verdict = record_verdict(
            self.control, attachment_id=attached["attachment_id"],
            disposition=disposition, profile=self.profile,
            port=self.port(REVIEWER))
        return {"writer": writer, "checkpoint": checkpoint,
                "attachment": attached, "verdict": verdict,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "verdict_id": verdict["verdict_id"]}

    # -- Job-store views -----------------------------------------------------

    def stages(self):
        from baton_v12.job_manager import stages_of
        return {row["kind"]: row for row in stages_of(self.jobs, "job-a")}

    def correct(self, round_, **changed):
        operands = {"job_id": "job-a", "line_id": self.line["line_id"],
                    "checkpoint_id": round_["checkpoint_id"],
                    "verdict_id": round_["verdict_id"]}
        operands.update(changed)
        return episodes.advance_correction(self.jobs, self.control, **operands)

    def live(self, kind):
        from baton_v12.job_manager import live_of
        return live_of(self.jobs, f"job-a/{kind}")

    def history(self, kind):
        return episodes.episodes_of(self.jobs, f"job-a/{kind}")

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception


class ACorrectionRoundAdvancesBothStagesOrNeither(DriverCase):
    """The measured incompatibility, and the act that closes it.

    `changes-requested` was terminal: the only path to a second episode was an
    ABANDONED offer, which means nobody had decided anything. A reviewed round
    that was sent back is the opposite, and it had nowhere to go.
    """

    def test_both_episodes_end_and_both_successors_open(self):
        first = self.round(1, "changes-requested")
        answered = self.correct(first)
        for kind in ("implementation", "review"):
            history = self.history(kind)
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["ended_state"], CORRECTION_ENDINGS[0])
            self.assertIsNone(history[1]["ended_state"])
            self.assertEqual(self.live(kind)["episode"], 2)
        self.assertEqual(answered["implementation"]["episode"], 2)
        self.assertEqual(answered["review"]["episode"], 2)

    def test_the_successors_are_fresh_identities_and_carry_nothing_over(self):
        first = self.round(1, "changes-requested")
        before = {kind: self.live(kind) for kind in ("implementation",
                                                     "review")}
        self.correct(first)
        for kind in ("implementation", "review"):
            after = self.live(kind)
            self.assertNotEqual(after["offer_id"], before[kind]["offer_id"])
            self.assertNotEqual(after["attempt_id"],
                                before[kind]["attempt_id"])
            from baton_v12.job_manager import receipts_of
            self.assertEqual(receipts_of(self.jobs, f"job-a/{kind}",
                                         after["episode"]), {})

    def test_the_projection_reopens_the_implementation_and_recloses_the_review(self):
        """No new projection rule: the gate does this by itself."""
        first = self.round(1, "changes-requested")
        self.correct(first)
        answered = status(self.jobs, Unobserved(), observed_at=NOW)
        states = {one["kind"]: one for one in answered["jobs"][0]["stages"]}
        self.assertEqual(states["implementation"]["state"], "queued")
        self.assertEqual(states["review"]["state"], "blocked")
        self.assertEqual(states["implementation"]["corrections"], 1)
        self.assertEqual(states["review"]["corrections"], 1)
        self.assertEqual(
            [gate["state"] for gate in states["review"]["gates"]], ["queued"])

    def test_an_exact_replay_returns_the_same_successors_and_writes_nothing(self):
        first = self.round(1, "changes-requested")
        once = self.correct(first)
        before = [dict(row) for row in self.history("implementation")]
        self.assertEqual(self.correct(first), once)
        self.assertEqual([dict(row) for row in self.history("implementation")],
                         before)

    def test_one_checkpoint_earns_exactly_one_round(self):
        """And every operand that could have differed is now PROVED.

        The identity is keyed on the checkpoint, so a second attempt at the
        same round replays. A round presenting any other operand no longer
        reaches the journal at all: the Job's stages are read from this store,
        the verdict is resolved through the owner's reader, and the line and
        checkpoint are proved against each other. The journal collision is
        still the backstop and is simply no longer reachable from the public
        surface, which is the stronger of the two properties.
        """
        first = self.round(1, "changes-requested")
        once = self.correct(first)
        self.assertEqual(self.correct(first), once)
        self.assertEqual(len(self.history("implementation")), 2)
        second = self.round(2, "changes-requested",
                            based=first["checkpoint_id"])
        caught = self.refusal(self.correct, first,
                              verdict_id=second["verdict_id"])
        self.assertIn("another line, checkpoint", caught.message)

    def test_ten_rounds_run_on_one_line_with_no_second_materialization(self):
        """The property the two-Job proof has to demonstrate."""
        based = None
        for number in range(1, 11):
            held = self.round(number, "changes-requested", based=based)
            self.correct(held)
            based = held["checkpoint_id"]
            self.assertEqual(self.live("implementation")["episode"],
                             number + 1)
        self.assertEqual(len(self.history("implementation")), 11)
        self.assertEqual(line_of(self.control, self.line["line_id"])["revision"],
                         10)
        # ONE checkout, materialized once, whatever the round count.
        self.assertEqual(len(os.listdir(os.path.join(
            self.storage, ".baton-review-lines"))), 1)


class ACorrectionIsRefusedBeforeItWritesAnything(DriverCase):

    def test_a_line_that_asked_for_nothing_admits_no_round(self):
        held = self.round(1, "accepted")
        caught = self.refusal(self.correct, held)
        self.assertEqual(caught.category, "refused")
        self.assertIn("asks for another round", caught.message)
        self.assertEqual(self.live("implementation")["episode"], 1)

    def test_a_round_naming_another_checkpoint_is_refused(self):
        first = self.round(1, "changes-requested")
        caught = self.refusal(self.correct, first,
                              checkpoint_id="checkpoint-somebody-elses")
        self.assertEqual(caught.category, "refused")

    def test_stages_of_two_different_works_could_never_have_been_attached(self):
        """The plan review's observation, driven against a REAL submission.

        The parser admits a Job whose implementation and review name unrelated
        Works; the accepted line provider can never attach it, because a line
        is one `(authority_uuid, work_id)` pair. The refusal is read off the
        stored rows, so a caller cannot avoid it by describing them otherwise.
        """
        first = self.round(1, "changes-requested")
        submit(self.jobs, {"schema": "baton.v12.job-submission/1",
                           "submission_id": "sub-2",
                           "jobs": [job("job-b", stages=[
                               stage("implementation", WORK_A),
                               stage("review", WORK_B,
                                     depends_on=[{"job_id": "job-b",
                                                  "kind": "implementation"}])])]})
        caught = self.refusal(self.correct, first, job_id="job-b")
        self.assertIn("one development line", caught.message)

    def test_a_job_that_is_not_a_pair_has_no_round(self):
        first = self.round(1, "changes-requested")
        submit(self.jobs, {"schema": "baton.v12.job-submission/1",
                           "submission_id": "sub-3",
                           "jobs": [job("job-c", stages=[
                               stage("implementation", WORK_A)])]})
        caught = self.refusal(self.correct, first, job_id="job-c")
        self.assertIn("correction round is a pair", caught.message)

    def test_a_verdict_this_manager_never_recorded_is_refused_first(self):
        """Review [P0]: the FIRST round for a checkpoint used to take any
        identity, because the line proof said a changes-requested verdict
        exists and never that the caller had named that one. The owner's
        reader is what resolves it now."""
        first = self.round(1, "changes-requested")
        caught = self.refusal(self.correct, first,
                              verdict_id="verdict-somebody-elses")
        self.assertIn("no checkpoint verdict", caught.message)
        for kind in ("implementation", "review"):
            self.assertEqual(self.live(kind)["episode"], 1)
            self.assertEqual(len(self.history(kind)), 1)

    def test_a_verdict_recorded_about_another_checkpoint_is_refused(self):
        """A real committed verdict, resolved, and still not this round's."""
        first = self.round(1, "changes-requested")
        self.correct(first)
        second = self.round(2, "changes-requested",
                            based=first["checkpoint_id"])
        caught = self.refusal(
            episodes.advance_correction, self.jobs, self.control,
            job_id="job-a", line_id=self.line["line_id"],
            checkpoint_id=second["checkpoint_id"],
            verdict_id=first["verdict_id"])
        self.assertIn("another line, checkpoint", caught.message)
        self.assertEqual(self.live("implementation")["episode"], 2)

    def test_an_accepted_verdict_document_asks_for_no_round(self):
        """A committed verdict, proved, and still not one that asks."""
        accepted = self.round(1, "accepted")
        caught = self.refusal(self.correct, accepted)
        self.assertEqual(caught.category, "refused")
        self.assertEqual(self.live("implementation")["episode"], 1)

    def test_a_reservation_committed_at_the_cutpoint_stops_the_round(self):
        """Review [P0]: the allocation proof used to run before the write lock.

        The answers are sequenced so the preflight sees no allocation and the
        proof inside the transaction sees a reservation -- which is exactly a
        scheduler committing between the two.
        """
        first = self.round(1, "changes-requested")
        from baton_v12.job_manager import scheduler
        held = {"asked": 0}
        real = scheduler.allocation_of

        def answering(store, assignment_id):
            held["asked"] += 1
            if held["asked"] <= 2:
                return real(store, assignment_id)
            return {"assignment_id": assignment_id,
                    "allocation_state": "reserved"}

        with mock.patch.object(scheduler, "allocation_of", answering):
            caught = self.refusal(self.correct, first)
        self.assertIn("still", caught.message)
        for kind in ("implementation", "review"):
            self.assertEqual(self.live(kind)["episode"], 1)
            self.assertEqual(len(self.history(kind)), 1)

    def test_a_still_reserved_allocation_holds_the_round_back(self):
        """Capacity is released by the scheduler, so the round waits for it.

        The allocation is a REAL reservation through the accepted pool
        operation rather than a forged row: what this refuses on is the state
        the scheduler actually writes.
        """
        first = self.round(1, "changes-requested")
        activate_pool(self.jobs, {
            "schema": POOL_SCHEMA, "variant": "primary",
            "separation_class": "provider-diverse",
            "workers": [{"worker_id": "impl-a", "lane": "implementation",
                         "participant": "baton.impl-a",
                         "profile_name": "reference",
                         "profile_digest": PROFILE,
                         "eligible_kinds": ["implementation"]},
                        {"worker_id": "review-a", "lane": "review",
                         "participant": "baton.review-a",
                         "profile_name": "reference",
                         "profile_digest": PROFILE,
                         "eligible_kinds": ["review"]}]},
            {"baton.impl-a": "principal:impl-a",
             "baton.review-a": "principal:review-a"})
        from baton_v12.job_manager import attempting, live_of
        held = self.stages()["implementation"]
        reserve(self.jobs, attempting(held, live_of(self.jobs,
                                                    held["stage_id"])))
        caught = self.refusal(self.correct, first)
        self.assertIn("still", caught.message)
        self.assertEqual(self.live("implementation")["episode"], 1)

    def test_an_ending_at_the_cutpoint_rolls_the_whole_round_back(self):
        """Review [P0]: this used to commit HALF a correction.

        The act guarded and mutated one stage at a time and its guard raised a
        DURABLE refusal, which `transact` commits without rolling the act's
        savepoint back -- so a review episode that ended at the cutpoint left
        the implementation stage superseded with a live successor and the
        review stage untouched. Every guard now runs before the first row
        moves, and the refusals are ordinary so the savepoint unwinds.

        The ending is injected from `_now`, which the act calls first, so it
        lands inside the transaction exactly where the reproduction put it.
        """
        first = self.round(1, "changes-requested")
        before = {kind: [dict(row) for row in self.history(kind)]
                  for kind in ("implementation", "review")}
        real = self.jobs._now
        held = {"done": False}

        def ending():
            if not held["done"]:
                held["done"] = True
                self.jobs._connection.execute(
                    "UPDATE episodes SET ended_state = 'declined', "
                    "ended_revision = 1, ended_at = ? WHERE stage_id = "
                    "'job-a/review' AND episode = 1", (NOW,))
            return real()

        with mock.patch.object(self.jobs, "_now", ending):
            caught = self.refusal(self.correct, first)
        self.assertEqual(caught.category, "refused")
        # COMPLETE ROLLBACK: the injected ending is gone too, because it was
        # written inside the savepoint this refusal unwinds.
        for kind in ("implementation", "review"):
            self.assertEqual([dict(row) for row in self.history(kind)],
                             before[kind])
            self.assertEqual(self.live(kind)["episode"], 1)
        # AND NO CORRECTION OPERATION WAS CONSUMED, so the round is still
        # available to whoever resolves the ending.
        self.assertIsNone(self.jobs.operation_record(
            episodes.correction_operation_id("job-a",
                                             first["checkpoint_id"])))

    def test_a_stage_with_no_live_episode_has_no_round_to_correct(self):
        first = self.round(1, "changes-requested")
        live = self.live("review")
        episodes.end_episode(self.jobs, live, "declined", 1)
        caught = self.refusal(self.correct, first)
        self.assertIn("no live episode", caught.message)
        # AND THE IMPLEMENTATION STAGE IS UNTOUCHED. Both or neither.
        self.assertEqual(self.live("implementation")["episode"], 1)

    def test_a_foreign_line_cannot_advance_this_job(self):
        first = self.round(1, "changes-requested")
        caught = self.refusal(self.correct, first,
                              line_id="line-somebody-elses")
        self.assertEqual(caught.category, "refused")


class AVerdictIsRoutedAndNeverInferred(DriverCase):
    """`end_review`'s one decision, and the three answers it has."""

    def ending(self, disposition):
        held = self.round(1, disposition)
        adapter = _Adapter(f"runtime-review-attempt-1")
        with _endings() as recorded:
            answered = review_driver.end_review(
                self.control, self.port(REVIEWER), adapter,
                attachment_id=held["attachment"]["attachment_id"],
                disposition="completed", verdict=disposition,
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64)
        return held, answered, recorded

    def test_an_accepted_verdict_hands_on_and_schedules_nothing_here(self):
        held, answered, _ = self.ending("accepted")
        self.assertEqual(answered["outcome"], "accepted")
        self.assertIsNone(answered["held_reason"])
        self.assertEqual(answered["verdict_id"], held["verdict_id"])

    def test_a_changes_requested_verdict_owes_a_round(self):
        held, answered, _ = self.ending("changes-requested")
        self.assertEqual(answered["outcome"], "correction")
        advanced = review_driver.open_correction(
            self.jobs, self.control, job_id="job-a", answered=answered)
        self.assertEqual(advanced["implementation"]["episode"], 2)

    def test_a_rejected_verdict_is_held_with_its_reason_and_advances_nothing(self):
        held, answered, _ = self.ending("rejected")
        self.assertEqual(answered["outcome"], "held")
        self.assertIn("decision about the Work", answered["held_reason"])
        caught = self.refusal(
            review_driver.open_correction, self.jobs, self.control,
            job_id="job-a", answered=answered)
        self.assertEqual(caught.category, "refused")
        self.assertEqual(self.live("implementation")["episode"], 1)

    def test_re_entering_the_ending_records_no_second_verdict(self):
        """A crash after the verdict and before cleanup re-enters here."""
        held = self.round(1, "accepted")
        adapter = _Adapter("runtime-review-attempt-1")
        answers = []
        for _ in (1, 2):
            with _endings():
                answers.append(review_driver.end_review(
                    self.control, self.port(REVIEWER), adapter,
                    attachment_id=held["attachment"]["attachment_id"],
                    disposition="completed", verdict="accepted",
                    profile=self.profile, retention_disposition="retain",
                    retention_policy_digest="sha256:" + "9" * 64))
        self.assertEqual(answers[0], answers[1])
        self.assertEqual(self.control._connection.execute(
            "SELECT count(*) FROM checkpoint_verdicts WHERE checkpoint_id = ?",
            (held["checkpoint_id"],)).fetchone()[0], 1)

    def test_the_ending_runs_its_steps_in_the_recorded_order(self):
        _, _, recorded = self.ending("accepted")
        self.assertEqual([one for one in recorded
                          if one in review_driver.REVIEW_ENDING],
                         list(review_driver.REVIEW_ENDING))


class TheImplementationEndingPublishesBeforeItFences(DriverCase):
    """W103068's measured ordering, driven rather than asserted in prose."""

    def ending(self, publication):
        attempt_id = self.attempt("writer-attempt-1", 1, WRITER,
                                  "writer-principal-1")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"], attempt_id=attempt_id,
            generation=1, worker_id="impl-worker-1", profile=self.profile)
        self.completed(attempt_id)
        with _endings() as recorded:
            adapter = _Adapter("runtime-writer-attempt-1", recorder=recorded)
            answered = review_driver.end_implementation(
                self.control, self.port(WRITER), adapter, publication,
                attempt_id=attempt_id, disposition="completed", terminal=None,
                writer_id=writer["writer_id"], generation=1,
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64,
                proposal={"target": "revision-1"})
        return answered, recorded

    def test_the_seam_is_asked_while_the_writer_is_still_active(self):
        seam = _Seam(self)
        answered, _ = self.ending(seam)
        self.assertEqual(seam.states, ["writing"])
        self.assertEqual(answered["checkpoint_id"],
                         answered["checkpoint"]["checkpoint_id"])

    def test_the_ending_runs_its_steps_in_the_recorded_order(self):
        answered, recorded = self.ending(_Seam(self))
        self.assertEqual([one for one in recorded
                          if one in review_driver.IMPLEMENTATION_ENDING],
                         [one for one in review_driver.IMPLEMENTATION_ENDING
                          if one != "correlate"])

    def test_a_seam_without_its_one_verb_refuses_before_anything_is_spent(self):
        attempt_id = self.attempt("writer-attempt-1", 1, WRITER,
                                  "writer-principal-1")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"], attempt_id=attempt_id,
            generation=1, worker_id="impl-worker-1", profile=self.profile)
        self.completed(attempt_id)
        caught = self.refusal(
            review_driver.end_implementation, self.control, self.port(WRITER),
            _Adapter("runtime-writer-attempt-1"), object(),
            attempt_id=attempt_id, disposition="completed", terminal=None,
            writer_id=writer["writer_id"], generation=1, profile=self.profile,
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64, proposal={})
        self.assertIn("publication seam", caught.message)
        self.assertEqual(line_of(self.control,
                                 self.line["line_id"])["state"], "writing")


class OldRoundsStayExactlyWhereTheyWere(DriverCase):
    """A correction supersedes a checkpoint; it does not revise one."""

    def test_every_earlier_checkpoint_still_resolves_unchanged(self):
        from baton_v12.worker_manager import audit_checkpoint, checkpoint_of
        held, based = [], None
        for number in (1, 2, 3):
            round_ = self.round(number, "changes-requested", based=based)
            held.append(checkpoint_of(self.control, round_["checkpoint_id"]))
            self.correct(round_)
            based = round_["checkpoint_id"]
        for earlier in held:
            again = checkpoint_of(self.control, earlier["checkpoint_id"])
            self.assertEqual(again, earlier)
            # AND IT RESOLVES WITHOUT BEING CURRENT, which is the property a
            # verdict about revision `n` depends on after revision `n + 1`
            # exists. `audit_checkpoint` answers the sealed EVIDENCE, which is
            # what a later reader has to be able to re-resolve.
            self.assertEqual(
                audit_checkpoint(self.control, earlier["checkpoint_id"],
                                 self.profile),
                earlier["evidence"])

    def test_a_reviewer_that_is_not_independent_never_gets_attached(self):
        """Not this driver's rule, and that is the point of driving it.

        `attach_review` compares the checkpoint writer's worker, participant
        and principal, and `prepare_review` composes a boundary only after it
        has. A driver that re-implemented the comparison would be a third
        account of it; a driver that skipped the call would be a way around it.
        """
        writer_attempt = self.attempt("writer-attempt-1", 1, WRITER,
                                      "shared-principal")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=1,
            worker_id="impl-worker-1", profile=self.profile)
        self.completed(writer_attempt)
        from baton_v12.worker_manager import freeze_checkpoint
        checkpoint = freeze_checkpoint(
            self.control, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.port(WRITER))
        self.attempt("review-attempt-1", 1, WRITER, "shared-principal")
        caught = self.refusal(
            review_driver.prepare_review, self.control,
            checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id="review-attempt-1", generation=1,
            reviewer_worker_id="impl-worker-1", profile=self.profile)
        self.assertIn("not independent", caught.message)


class AnEndingProvesEveryOperandBeforeItTouchesAnything(DriverCase):
    """Review [P0] and [P1]: nothing external happens on an unproved operand.

    The composite used to quiesce, observe, freeze, collect, retain and publish
    for one attempt and only then discover that the writer or the attachment it
    was handed belonged to another -- or that the adapter could not finish. By
    then somebody's container was stopped and somebody's output was sealed. So
    every case here asserts the same two things: the refusal, and that the
    adapter was never asked to stop.
    """

    def prepared(self, number, participant=WRITER):
        attempt_id = self.attempt(f"writer-attempt-{number}", number,
                                  participant, f"writer-principal-{number}")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"], attempt_id=attempt_id,
            generation=number, worker_id=f"impl-worker-{number}",
            profile=self.profile)
        self.completed(attempt_id)
        return attempt_id, writer

    def ending(self, adapter, *, attempt_id, writer_id, generation=1,
               port=None):
        return review_driver.end_implementation(
            self.control, port if port is not None else self.port(WRITER),
            adapter, _Seam(self), attempt_id=attempt_id,
            disposition="completed", terminal=None, writer_id=writer_id,
            generation=generation, profile=self.profile,
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64, proposal={})

    def test_a_writer_belonging_to_another_attempt_stops_nothing(self):
        first, writer = self.prepared(1)
        second = self.attempt("writer-attempt-2", 2, WRITER,
                              "writer-principal-2")
        self.completed(second)
        adapter = _Adapter("runtime-writer-attempt-2")
        caught = self.refusal(self.ending, adapter, attempt_id=second,
                              writer_id=writer["writer_id"], generation=2)
        self.assertIn("one ending answers for one attempt", caught.message)
        self.assertEqual(adapter.stops, [])
        self.assertEqual(line_of(self.control,
                                 self.line["line_id"])["state"], "writing")

    def test_a_stale_generation_for_the_right_attempt_stops_nothing(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"], generation=2)
        self.assertEqual(caught.category, "refused")
        self.assertEqual(adapter.stops, [])

    def test_an_adapter_missing_a_verb_is_refused_before_the_stop(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1", verbs=("stop",))
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"])
        self.assertIn("runtime adapter's", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_port_missing_a_verb_is_refused_before_the_stop(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"],
                              port=SimpleNamespace())
        self.assertIn("authority-bound port's", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_port_with_no_participant_is_refused_before_the_stop(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        nameless = Port(WRITER)
        nameless.participant = None
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"], port=nameless)
        self.assertEqual(caught.code, "capability")
        self.assertEqual(adapter.stops, [])

    def test_a_session_acting_for_somebody_else_is_refused_before_the_stop(self):
        """Review [P1]: a non-null participant was proved and never compared,
        so a wrong session reached `refused/capability` from the custody
        operations with one stop already recorded."""
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"],
                              port=self.port(REVIEWER))
        self.assertEqual(caught.code, "capability")
        self.assertIn("one ending acts for one assignment", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_an_adapter_with_no_custodian_identity_is_refused(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1", identities=())
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"])
        self.assertIn("custodian_image_digest", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_custodian_identity_that_is_not_text_is_refused(self):
        """Third review [P1]: non-null was not the rule. The custody boundary
        takes this as TEXT and signs an act with it, so any other shape passed
        here and refused there -- after the stop."""
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        adapter.custodian_image_digest = 17
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"])
        self.assertIn("custodian_image_digest", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_valid_profile_for_another_line_makes_zero_stop_calls(self):
        """Third review [P1]: a fully callable `other-profile` handed to an
        ending prepared under this line's profile recorded one stop before
        `freeze_checkpoint` refused. The line comes from the owner-bound
        writer, so naming an agreeable line cannot satisfy it either."""
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        foreign = Profile()
        foreign.name = "other-profile"
        caught = self.refusal(
            review_driver.end_implementation, self.control, self.port(WRITER),
            adapter, _Seam(self), attempt_id=first, disposition="completed",
            terminal=None, writer_id=writer["writer_id"], generation=1,
            profile=foreign, retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64, proposal={})
        self.assertEqual(caught.code, "profile-uncertified")
        self.assertEqual(adapter.stops, [])

    def test_a_review_ending_compares_the_line_profile_before_the_stop(self):
        """The same late comparison existed on the review ending."""
        held = self.round(1, "accepted")
        adapter = _Adapter("runtime-review-attempt-1")
        foreign = Profile()
        foreign.name = "other-profile"
        caught = self.refusal(
            review_driver.end_review, self.control, self.port(REVIEWER),
            adapter, attachment_id=held["attachment"]["attachment_id"],
            disposition="completed", verdict="accepted", profile=foreign,
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64)
        self.assertEqual(caught.code, "profile-uncertified")
        self.assertEqual(adapter.stops, [])

    def test_a_review_ending_with_a_malformed_custodian_makes_no_stop(self):
        held = self.round(1, "accepted")
        adapter = _Adapter("runtime-review-attempt-1")
        adapter.custodian_image_digest = 17
        caught = self.refusal(
            review_driver.end_review, self.control, self.port(REVIEWER),
            adapter, attachment_id=held["attachment"]["attachment_id"],
            disposition="completed", verdict="accepted", profile=self.profile,
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64)
        self.assertIn("custodian_image_digest", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_profile_that_cannot_freeze_is_refused_before_the_stop(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1")
        caught = self.refusal(
            review_driver.end_implementation, self.control, self.port(WRITER),
            adapter, _Seam(self), attempt_id=first, disposition="completed",
            terminal=None, writer_id=writer["writer_id"], generation=1,
            profile=SimpleNamespace(name="reference",
                                    validate=lambda *a, **k: None),
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64, proposal={})
        self.assertIn("checkpoint profile's freeze", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_stop_answer_that_is_not_a_document_refuses_rather_than_faults(self):
        first, writer = self.prepared(1)
        adapter = _Adapter("runtime-writer-attempt-1", answer="quiescent")
        caught = self.refusal(self.ending, adapter, attempt_id=first,
                              writer_id=writer["writer_id"])
        self.assertIn("not a document", caught.message)

    def test_a_review_ending_derives_its_attempt_from_the_owner(self):
        """There is no second selector to cross-wire: the attachment names the
        attempt, and the owner's committed record is what says so."""
        held = self.round(1, "changes-requested")
        adapter = _Adapter("runtime-review-attempt-1")
        caught = self.refusal(
            review_driver.end_review, self.control, self.port(REVIEWER),
            adapter, attachment_id="review-nobody-attached",
            disposition="completed", verdict="accepted", profile=self.profile,
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64)
        self.assertIn("no review attachment", caught.message)
        self.assertEqual(adapter.stops, [])

    def test_a_disposition_the_provider_does_not_have_is_not_evidence(self):
        """Review [P1]: a caller's malformed argument is not something a
        reviewer left behind, so it refuses rather than answering `held`."""
        held = self.round(1, "accepted")
        adapter = _Adapter("runtime-review-attempt-1")
        caught = self.refusal(
            review_driver.end_review, self.control, self.port(REVIEWER),
            adapter, attachment_id=held["attachment"]["attachment_id"],
            disposition="completed", verdict="approved", profile=self.profile,
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64)
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(adapter.stops, [])


class ReviewEvidenceThisManagerCannotSettleIsHeld(DriverCase):
    """Review [P1]: the contract's held branch, which used to escape.

    `record_verdict` is what refuses stale, ambiguous or unreadable review
    evidence, and every one of those refusals left this function as an
    exception rather than as the outcome its own docstring promised. The
    provider is faked HERE and only here, because what is under test is this
    module's classification of a refusal rather than the provider's reasons for
    raising one -- `tests/manager/test_review_cycles` owns those.
    """

    def held(self, refusal):
        round_ = self.round(1, "accepted")
        adapter = _Adapter("runtime-review-attempt-1")

        def refusing(*operands, **named):
            raise refusal

        with _endings():
            with mock.patch.object(review_driver.review_cycles,
                                   "record_verdict", refusing):
                return review_driver.end_review(
                    self.control, self.port(REVIEWER), adapter,
                    attachment_id=round_["attachment"]["attachment_id"],
                    disposition="completed", verdict="accepted",
                    profile=self.profile, retention_disposition="retain",
                    retention_policy_digest="sha256:" + "9" * 64)

    def test_stale_evidence_answers_held_and_leaves_the_runtime_alone(self):
        answered = self.held(ContractRefusal(
            "refused", "precondition",
            "a verdict applies only to the active current review"))
        self.assertEqual(answered["outcome"], "held")
        self.assertIn("refused/precondition", answered["held_reason"])
        self.assertIsNone(answered["verdict_id"])
        # CLEANUP IS NOT AUTHORIZED, so the runtime stays where an operator can
        # look at it and the account says the ending is unfinished.
        self.assertFalse(answered["cleaned_up"])

    def test_ambiguous_evidence_answers_held_as_the_contract_pins(self):
        """Review [P1]: this leaf's confirmed contract says ambiguous evidence
        is held, and the round that argued otherwise was overruled -- an
        implementation paragraph is not a supersession of a pinned contract."""
        answered = self.held(ContractRefusal(
            "ambiguous", "operation",
            "the manager cannot say whether the verdict committed"))
        self.assertEqual(answered["outcome"], "held")
        self.assertIn("ambiguous/operation", answered["held_reason"])
        self.assertFalse(answered["cleaned_up"])

    def test_unreadable_evidence_answers_held_too(self):
        answered = self.held(ContractRefusal(
            "integrity", "digest",
            "persisted checkpoint fence does not match its digest"))
        self.assertEqual(answered["outcome"], "held")
        self.assertIn("integrity/digest", answered["held_reason"])

    def test_a_transport_that_is_down_still_escapes(self):
        """`unavailable` is the one that is not a held account.

        A transport or an authority that did not answer says nothing about the
        review, so it escapes and the sweep asks again rather than recording an
        outcome about evidence nobody read.
        """
        caught = self.refusal(self.held, ContractRefusal(
            "unavailable", "transport", "the authority did not answer"))
        self.assertEqual(caught.category, "unavailable")


class ThePortIsTypedAndTheSeamIsOne(unittest.TestCase):

    def test_the_publication_seam_is_exactly_one_verb(self):
        self.assertEqual(review_driver.PUBLICATION_SEAM, ("publish",))

    def test_the_verdict_outcomes_are_not_the_verdict_vocabulary(self):
        from baton_v12.worker_manager.review_cycles import DISPOSITIONS
        self.assertNotEqual(set(review_driver.VERDICT_OUTCOMES),
                            set(DISPOSITIONS))
        self.assertIn("held", review_driver.VERDICT_OUTCOMES)


# -- the deployment halves this suite supplies -------------------------------


class _Adapter:
    """The runtime adapter, carrying every verb an ending reaches.

    IT ANSWERS `stop` AND CARRIES THE REST. The ending only calls `stop`
    itself; `list`, `observe` and `seal` are what the composed manager
    operations reach, and an adapter without them has to refuse BEFORE the
    stop rather than after it -- which is what `_typed` is for and what
    `AnEndingProvesEveryOperandBeforeItTouchesAnything` drives.
    """

    custodian_image_digest = "sha256:" + "c" * 64

    def __init__(self, runtime_id, *, answer=None, verbs=None,
                 identities=review_driver.ADAPTER_IDENTITIES,
                 recorder=None, consumable=None):
        self.runtime_id = runtime_id
        self.answer = answer
        self.stops = []
        self.consumed = []
        for verb in (verbs if verbs is not None
                     else review_driver.RUNTIME_ADAPTER):
            if verb != "stop":
                setattr(self, verb, lambda *a, **k: None)
        # W105982: THE CONSUMPTION GATE IS AN ADAPTER VERB, so the order
        # recorder cannot see it by patching a module function the way it sees
        # every other step. It records itself, and `consumable` is what a case
        # uses to make the gate refuse.
        if hasattr(self, "prove_line_consumable"):
            def consume(store, **named):
                self.consumed.append(dict(named))
                if recorder is not None:
                    recorder.append("consume")
                if consumable is not None:
                    raise consumable
                return {"line_id": "line-1"}
            self.prove_line_consumable = consume
        for member in review_driver.ADAPTER_IDENTITIES:
            if member not in identities:
                setattr(self, member, None)

    def stop(self, operands):
        self.stops.append(dict(operands))
        if self.answer is not None:
            return self.answer
        return {"state": "quiescent", "runtime_id": self.runtime_id}


class _Seam:
    """W103077's publication seam, recording WHEN it was asked.

    The line's own state is what it records, because the point of the ordering
    is that the producer assignment is still live: `writing` means the writer
    has not been fenced, and `freezing` or later would mean this was called
    after the fence -- which the retained reproduction proves the Authority
    refuses.
    """

    def __init__(self, case):
        self.case = case
        self.states = []
        self.calls = []

    def publish(self, **operands):
        self.states.append(line_of(self.case.control,
                                   self.case.line["line_id"])["state"])
        self.calls.append(operands)
        return {"proposal_id": "proposal-1",
                "result_id": operands["result_id"]}


import contextlib


@contextlib.contextmanager
def _endings():
    """The manager operations an ending calls, recorded in call order.

    THEY ARE FAKED AND THE CUSTODY OPERATIONS ARE NOT. `request_freeze`,
    `request_intake`, `decide_retention` and `authorize_cleanup` need a real
    OCI adapter, a delivered workspace and a custody root -- a deployment's
    half, which W103083 owns and `tests/manager` already drives. What this
    suite must prove is the ORDER and the two operations that are this leaf's
    own: the publication seam and the fence. So the accepted custody calls
    stay real and the deployment calls are recorded.
    """
    recorded = []

    def note(name, answer=None):
        def call(*operands, **named):
            recorded.append(name)
            return answer() if callable(answer) else answer
        return call

    frozen = {"result_id": "result-1", "manifest_digest": "sha256:" + "4" * 64}
    receipt = {"receipt_digest": "sha256:" + "5" * 64,
               "artifacts": [{"artifact_id": "artifact-1"}]}
    real_freeze = review_cycles_freeze()
    real_verdict = review_cycles_verdict()

    def checkpoint(*operands, **named):
        recorded.append("checkpoint")
        return real_freeze(*operands, **named)

    def verdict(*operands, **named):
        recorded.append("verdict")
        return real_verdict(*operands, **named)

    def publish(seam, **named):
        recorded.append("publish")
        return seam.publish(**named)

    with mock.patch.object(review_driver, "reconcile_runtime",
                           note("quiesce")), \
            mock.patch.object(review_driver, "observe", note("observe")), \
            mock.patch.object(review_driver, "request_freeze",
                              note("freeze", lambda: dict(frozen))), \
            mock.patch.object(review_driver, "request_intake",
                              note("intake", lambda: dict(receipt))), \
            mock.patch.object(review_driver, "decide_retention",
                              note("retain", lambda: {"disposition": "retain"})), \
            mock.patch.object(review_driver, "authorize_cleanup",
                              note("cleanup", lambda: {"state": "absent", "cleanup": "retained"})), \
            mock.patch.object(review_driver.review_cycles, "freeze_checkpoint",
                              checkpoint), \
            mock.patch.object(review_driver.review_cycles, "record_verdict",
                              verdict), \
            mock.patch.object(_Seam, "publish", _recording(recorded)):
        yield recorded




@contextlib.contextmanager
def _frozen_endings():
    """`_endings`, with the freeze answering the attempt's REAL frozen result.

    REVIEW 2026-09-07T15-19-16Z [P1] is why this exists beside the other one.
    `_endings` returns a CANNED frozen result whose manifest digest nothing
    retains -- so the terminal correlation had nothing to compare against and
    the resolver went on to read a completely different document. Two accounts
    of one freeze, and the ending under test was the only party that could not
    tell.

    Here the freeze answers `frozen_output_of` for the exact attempt, which is
    the accepted public owner of that fact. The correlation, the resolver and
    the recorded verdict therefore all read ONE retained result -- the one this
    case actually retained.

    WHAT IS STILL RECORDED RATHER THAN PERFORMED, named rather than implied:
    the quiesce, the observation, the intake, the retention and the cleanup.
    Those need an engine, a delivered workspace and a custody tree, which are
    a deployment's half; `tests/manager` drives them and W103083 owns the
    composition. What is REAL here is every operation this channel is about:
    the frozen result and its retained manifest, the completion correlation,
    the claim reader, and `record_verdict`.

    `correlate` and `resolve` are recorded by WRAPPERS THAT DELEGATE, not by
    substitutes. The real `_correlated` and the real
    `review_verdict_from_result` run; the wrapper exists because those two are
    inline calls rather than patched module functions, and an order assertion
    that could not see them is the assertion that let their absence pass.
    """
    from baton_v12.worker_manager import frozen_output_of

    recorded = []

    def note(name, answer=None):
        def call(*operands, **named):
            recorded.append(name)
            return answer() if callable(answer) else answer
        return call

    receipt = {"receipt_digest": "sha256:" + "5" * 64,
               "artifacts": [{"artifact_id": "artifact-1"}]}

    def freeze(control, _port, _adapter, *, attempt_id, disposition):
        recorded.append("freeze")
        del disposition
        return frozen_output_of(control, attempt_id)

    real_correlated = review_driver._correlated
    real_reader = review_driver.review_verdict_from_result
    real_verdict = review_cycles_verdict()

    def correlate(*operands, **named):
        recorded.append("correlate")
        return real_correlated(*operands, **named)

    def resolve(*operands, **named):
        recorded.append("resolve")
        return real_reader(*operands, **named)

    def verdict(*operands, **named):
        recorded.append("verdict")
        return real_verdict(*operands, **named)

    with mock.patch.object(review_driver, "reconcile_runtime",
                           note("quiesce")), \
            mock.patch.object(review_driver, "observe", note("observe")), \
            mock.patch.object(review_driver, "request_freeze", freeze), \
            mock.patch.object(review_driver, "_correlated", correlate), \
            mock.patch.object(review_driver, "request_intake",
                              note("intake", lambda: dict(receipt))), \
            mock.patch.object(review_driver, "decide_retention",
                              note("retain", lambda: {"disposition": "retain"})), \
            mock.patch.object(review_driver, "review_verdict_from_result",
                              resolve), \
            mock.patch.object(review_driver.review_cycles, "record_verdict",
                              verdict), \
            mock.patch.object(review_driver, "authorize_cleanup",
                              note("cleanup", lambda: {"state": "absent", "cleanup": "retained"})):
        yield recorded


def _recording(recorded):
    original = _Seam.publish

    def publish(self, **operands):
        recorded.append("publish")
        return original(self, **operands)
    return publish


def review_cycles_freeze():
    from baton_v12.worker_manager import review_cycles
    return review_cycles.freeze_checkpoint


def review_cycles_verdict():
    from baton_v12.worker_manager import review_cycles
    return review_cycles.record_verdict


class TheEndingProvesTheLineBeforeItReadsIt(DriverCase):
    """W105982: the gate's POSITION is the whole of it.

    Ordinary custody normalization is the last thing an ending does and
    addresses the ordinary attempt roots, which are not the tree the manager
    seals. So until this gate ran, nothing had established that the manager can
    read what it is about to read.
    """

    def ending(self, adapter=None, **operands):
        attempt_id = self.attempt("writer-attempt-1", 1, WRITER,
                                  "writer-principal-1")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"], attempt_id=attempt_id,
            generation=1, worker_id="impl-worker-1", profile=self.profile)
        self.completed(attempt_id)
        with _endings() as recorded:
            held = adapter or _Adapter("runtime-writer-attempt-1",
                                       recorder=recorded, **operands)
            try:
                answered = review_driver.end_implementation(
                    self.control, self.port(WRITER), held, _Seam(self),
                    attempt_id=attempt_id, disposition="completed",
                    terminal=None, writer_id=writer["writer_id"],
                    generation=1, profile=self.profile,
                    retention_disposition="retain",
                    retention_policy_digest="sha256:" + "9" * 64,
                    proposal={"target": "revision-1"})
            except ContractRefusal as refused:
                return None, recorded, held, refused
        return answered, recorded, held, None

    def test_the_gate_runs_after_the_stop_and_before_the_first_read(self):
        _, recorded, adapter, _ = self.ending()
        self.assertIn("consume", recorded)
        # AFTER, because a proof taken while the worker is still writing is a
        # proof about a tree that is still changing.
        self.assertLess(recorded.index("quiesce"), recorded.index("consume"))
        self.assertLess(recorded.index("observe"), recorded.index("consume"))
        # BEFORE, because a consumer that discovers the denial halfway through
        # sealing has already produced a partial account of somebody's work.
        self.assertLess(recorded.index("consume"), recorded.index("freeze"))
        self.assertLess(recorded.index("consume"), recorded.index("publish"))
        self.assertLess(recorded.index("consume"), recorded.index("checkpoint"))
        # AND ORDINARY CLEANUP IS STILL LAST, which is exactly why it could
        # never have been the thing that made this line readable.
        self.assertEqual(recorded[-1], "cleanup")
        self.assertEqual(adapter.consumed,
                         [{"assignment_id": "writer-attempt-1",
                           "generation": 1}])

    def test_a_refused_gate_stops_before_the_seal_and_the_publication(self):
        answered, recorded, _, refused = self.ending(
            consumable=ContractRefusal(
                "runtime-observation", "identity-mismatch",
                "this manager cannot open the development line"))
        self.assertIsNone(answered)
        self.assertIn("cannot open", refused.message)
        for step in ("freeze", "intake", "retain", "publish", "checkpoint",
                     "cleanup"):
            self.assertNotIn(step, recorded)

    def test_an_adapter_without_the_gate_refuses_before_the_stop(self):
        verbs = [one for one in review_driver.RUNTIME_ADAPTER
                 if one != "prove_line_consumable"]
        adapter = _Adapter("runtime-writer-attempt-1", verbs=verbs)
        answered, recorded, held, refused = self.ending(adapter)
        self.assertIsNone(answered)
        self.assertEqual(held.stops, [])
        self.assertNotIn("quiesce", recorded)
        self.assertIn("prove_line_consumable", refused.message)


# -- W110772: the frozen reviewer verdict ------------------------------------


def _result_vector():
    """One published result-manifest vector, so this suite composes no second
    idea of a valid frozen result."""
    import pathlib
    place = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
             / "2026" / "08" / "finding-v12-isolated-agent-workers"
             / "findings" / "finding-v12-worker-contract" / "findings"
             / "finding-worker-control-api-manifests" / "evidence"
             / "vectors.json")
    for case in json.loads(place.read_text(encoding="utf-8"))["valid"]:
        document = case.get("document")
        if isinstance(document, dict) \
                and document.get("schema") == "baton.worker-manifest/result":
            return copy.deepcopy(document)
    raise AssertionError("the published vectors carry no result manifest")


class ReviewResultCase(DriverCase):
    """One review round whose frozen result is REALLY RETAINED.

    `DriverCase.completed` writes the rows a runtime would have written and
    names a manifest digest nothing retains, which is enough for
    `record_verdict` -- it reads the frozen summary and the artifact rows. It
    is not enough for a reader that resolves the retained manifest, and that is
    the whole point of this fixture: the claim lives inside the document the
    manager sealed, so a case that faked the document would be proving nothing
    about where a verdict comes from.

    ONE MANIFEST-VALID AUTHORITY AND WORK PAIR. §12 rule 1 makes a Work id
    carry its Authority's eight-character prefix, and the shared fixture's pair
    was written for paths that never validate a manifest -- so retaining one
    under it refuses at the identity rule before the composition being proved
    is reached. The line, the Job store and every attempt use the same pair,
    because `advance_correction` cross-binds the recorded verdict against the
    Job's own Authority.
    """

    AUTHORITY = "0000000a" + "0" * 24

    def setUp(self):
        super().setUp()
        from baton_v12.job_manager import JobStore, submit
        from baton_v12.worker_manager import create_line
        self.jobs.close()
        self.jobs = JobStore.open(
            os.path.join(self.root, "review-jobs.sqlite3"),
            authority_uuid=self.AUTHORITY, incarnation="jobs-2",
            clock=self.clock)
        self.addCleanup(self.jobs.close)
        submit(self.jobs, one_work_submission())
        self.line = create_line(
            self.control, source=nominate_source(self.source),
            declared_base=self.line_base(), profile=self.profile,
            authority_uuid=self.AUTHORITY, work_id=WORK_A)

    def verdicts(self, held):
        """How many verdicts this checkpoint carries, from the owner's table."""
        return self.control._connection.execute(
            "SELECT count(*) FROM checkpoint_verdicts WHERE checkpoint_id = ?",
            (held["checkpoint_id"],)).fetchone()[0]

    def line_base(self):
        """The revision this line is declared against.

        A HOOK RATHER THAN A CONSTANT, because `create_line` is create-or-
        recover keyed by Authority and Work: a line made against one base
        cannot be remade against another, so a case whose checkpoint evidence
        must name REAL objects has to supply its base before the line exists
        rather than correct it afterwards.
        """
        return BASE

    def attempt(self, attempt_id, generation, participant, principal,
                work_id=WORK_A):
        held = super().attempt(attempt_id, generation, participant, principal,
                               work_id)
        self.control._connection.execute(
            "UPDATE attempts SET authority_uuid = ? WHERE "
            "runtime_attempt_id = ?", (self.AUTHORITY, held))
        return held

    def retained(self, attempt_id, *, generation, observed, verdict="accepted",
                 claim=..., logs_claim=None, outputs=None, result_id=None,
                 assignment=None):
        """Retain one review result manifest and point the frozen row at it."""
        from baton_v12.contracts import digest
        from baton_v12.worker_manager import retain_manifest

        def one(name, metadata):
            entries = [{"path": f"{name}.txt", "bytes": 3,
                        "content_digest": "sha256:" + "6" * 64}]
            content = {"entries": entries, "entry_count": 1, "total_bytes": 3,
                       "tree_digest": digest(entries)}
            return {"name": name, "type": "directory-result",
                    "status": "present", "content_manifest": content,
                    "artifact": {"artifact_id": f"artifact-{name}-{attempt_id}",
                                 "media_type": "text/plain", "bytes": 3,
                                 "content_digest": content["tree_digest"],
                                 "locator": f"file:///var/lib/baton/{attempt_id}/{name}"},
                    "result_metadata": metadata}

        if claim is ...:
            claim = {"verdict": verdict, "base": observed["base"],
                     "head": observed["head"], "tree": observed["tree"]}
        findings_metadata = ({} if claim is None else
                             {review_driver.REVIEW_CLAIM_NAMESPACE: claim})
        logs_metadata = ({} if logs_claim is None else
                         {review_driver.REVIEW_CLAIM_NAMESPACE: logs_claim})
        composed = outputs if outputs is not None else [
            one("findings", findings_metadata), one("logs", logs_metadata)]
        document = dict(
            _result_vector(), result_id=result_id or ("result-" + attempt_id),
            assignment_ref=assignment or {
                "work_ref": {"authority_uuid": self.AUTHORITY,
                             "work_id": WORK_A},
                "participant": REVIEWER, "generation": generation},
            outputs=composed)
        document.pop("manifest_digest")
        document["manifest_digest"] = digest(document)
        held = retain_manifest(self.control, document,
                               "resultManifest")["digest"]
        self.control._connection.execute(
            "UPDATE outputs SET manifest_digest = ?, result_id = ? "
            "WHERE runtime_attempt_id = ?",
            (held, document["result_id"], attempt_id))
        return held, document

    def reviewed(self, number=1, disposition="accepted", record=True,
                 **retained):
        """One complete round whose review result carries a real claim.

        THE MANIFEST IS RETAINED BEFORE THE VERDICT IS RECORDED, and the order
        is not incidental. `record_verdict` binds the frozen review result into
        its own operation signature, so a manifest retained afterwards would
        make the ending's replay a DIFFERENT act under the same identity --
        which §4.2 refuses, correctly, and which would report a settled review
        as unsettleable evidence.
        """
        from baton_v12.worker_manager import freeze_checkpoint, record_verdict
        writer_attempt = self.attempt(f"writer-attempt-{number}", number,
                                      WRITER, f"writer-principal-{number}")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=number,
            worker_id=f"impl-worker-{number}", profile=self.profile,
            based_checkpoint_id=retained.pop("based", None))
        self.completed(writer_attempt)
        checkpoint = freeze_checkpoint(
            self.control, writer_id=writer["writer_id"], generation=number,
            profile=self.profile, port=self.port(WRITER))
        review_attempt = self.attempt(f"review-attempt-{number}", number,
                                      REVIEWER, f"review-principal-{number}")
        attached = review_driver.prepare_review(
            self.control, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=review_attempt, generation=number,
            reviewer_worker_id=f"review-worker-{number}", profile=self.profile)
        self.completed(review_attempt, review=True)
        evidence = checkpoint["evidence"]
        observed = {"base": evidence["base"], "head": evidence["head"],
                    "tree": evidence["tree"]}
        retained.setdefault("verdict", disposition)
        digest, document = self.retained(review_attempt, generation=number,
                                         observed=observed, **retained)
        # THE VERDICT IS RECORDED HERE ONLY WHEN A CASE ASKS FOR IT. Review
        # 2026-09-07T15-19-16Z [P1]: every ending case ran against a verdict
        # this fixture had already recorded, so the ending replayed one rather
        # than producing the first -- which is the act the channel exists for
        # and the one nothing proved.
        verdict = record_verdict(
            self.control, attachment_id=attached["attachment_id"],
            disposition=disposition, profile=self.profile,
            port=self.port(REVIEWER)) if record else None
        return {"writer": writer, "checkpoint": checkpoint,
                "attachment": attached, "verdict": verdict,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "verdict_id": None if verdict is None else verdict["verdict_id"],
                "attempt_id": review_attempt, "observed": observed,
                "result_digest": digest,
                # THE WORKER'S OWN COMPLETION ENVELOPE, which is what the
                # terminal names and what `_correlated` compares the frozen
                # result against.
                "terminal": {"manifest_digest":
                             document["completion_manifest_digest"]}}


class TheVerdictIsReadFromTheFrozenResult(ReviewResultCase):
    """W110772: the reviewer decided, and this reads that decision back."""

    def read(self, held):
        return review_driver.review_verdict_from_result(
            self.control, attachment_id=held["attachment"]["attachment_id"])

    def test_a_complete_claim_answers_the_reviewers_own_verdict(self):
        held = self.reviewed(disposition="changes-requested")
        answered = self.read(held)
        self.assertEqual(answered["verdict"], "changes-requested")
        self.assertEqual(answered["checkpoint_id"], held["checkpoint_id"])
        for member in ("base", "head", "tree"):
            self.assertEqual(answered[member], held["observed"][member])

    def test_the_reader_writes_nothing_and_repeats_itself(self):
        """A read this ending performs after the freeze, on this incarnation
        or the next one, derives the same answer from the same evidence."""
        held = self.reviewed()
        before = self.control._connection.execute(
            "SELECT count(*) FROM manifests").fetchone()[0]
        self.assertEqual(self.read(held), self.read(held))
        self.assertEqual(self.control._connection.execute(
            "SELECT count(*) FROM manifests").fetchone()[0], before)

    def test_no_claim_at_all_is_a_question_and_never_a_decision(self):
        held = self.reviewed(claim=None)
        caught = self.refusal(self.read, held)
        self.assertIn(review_driver.REVIEW_CLAIM_NAMESPACE, caught.message)
        self.assertIn(review_driver._EVIDENCE_REFUSALS[0], caught.category)

    def test_a_claim_with_another_member_is_refused_rather_than_trimmed(self):
        held = self.reviewed(claim={"verdict": "accepted", "base": "a" * 40,
                                    "head": "b" * 40, "tree": "c" * 40,
                                    "result_id": "result-review-attempt-1"})
        self.refusal(self.read, held)

    def test_a_verdict_word_this_manager_does_not_have_is_refused(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"],
                      claim={"verdict": "looks-fine",
                             "base": held["observed"]["base"],
                             "head": held["observed"]["head"],
                             "tree": held["observed"]["tree"]})
        caught = self.refusal(self.read, held)
        self.assertEqual(caught.code, "schema")

    def test_a_competing_claim_on_the_logs_output_refuses_as_ambiguous(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"],
                      logs_claim={"verdict": "rejected",
                                  "base": held["observed"]["base"],
                                  "head": held["observed"]["head"],
                                  "tree": held["observed"]["tree"]})
        caught = self.refusal(self.read, held)
        self.assertEqual(caught.category, "ambiguous")

    def test_a_head_the_checkpoint_does_not_record_is_refused(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=1,
                      observed=dict(held["observed"], head="f" * 40))
        caught = self.refusal(self.read, held)
        self.assertIn("head", caught.message)

    def test_a_tree_the_checkpoint_does_not_record_is_refused(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=1,
                      observed=dict(held["observed"], tree="e" * 40))
        self.refusal(self.read, held)

    def test_a_base_the_checkpoint_does_not_record_is_refused(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=1,
                      observed=dict(held["observed"], base="d" * 40))
        self.refusal(self.read, held)

    def test_a_manifest_naming_another_result_is_refused(self):
        held = self.reviewed()
        self.control._connection.execute(
            "UPDATE outputs SET result_id = 'result-somebody-else' "
            "WHERE runtime_attempt_id = ?", (held["attempt_id"],))
        caught = self.refusal(self.read, held)
        self.assertIn("different results", caught.message)

    def test_a_result_frozen_under_another_assignment_is_refused(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"],
                      assignment={"work_ref": {
                          "authority_uuid": self.AUTHORITY,
                          "work_id": WORK_A},
                          "participant": WRITER, "generation": 1})
        caught = self.refusal(self.read, held)
        self.assertIn("one assignment", caught.message)

    def test_a_result_frozen_under_another_generation_is_refused(self):
        held = self.reviewed()
        self.retained("review-attempt-1", generation=9,
                      observed=held["observed"])
        self.refusal(self.read, held)

    def test_an_absent_findings_output_leaves_nothing_to_read(self):
        held = self.reviewed()
        _digest, document = self.retained("review-attempt-1", generation=1,
                                          observed=held["observed"])
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"],
                      outputs=[one for one in document["outputs"]
                               if one["name"] != "findings"])
        caught = self.refusal(self.read, held)
        self.assertIn("findings", caught.message)

    def test_an_unmeasured_findings_output_is_not_evidence(self):
        held = self.reviewed()
        _digest, document = self.retained("review-attempt-1", generation=1,
                                          observed=held["observed"])
        stripped = []
        for one in document["outputs"]:
            stripped.append(dict(one, artifact=None)
                            if one["name"] == "findings" else one)
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"], outputs=stripped)
        caught = self.refusal(self.read, held)
        self.assertIn("measured", caught.message)

    def test_a_review_that_did_not_complete_decided_nothing(self):
        held = self.reviewed()
        self.control._connection.execute(
            "UPDATE outputs SET disposition = 'unable' "
            "WHERE runtime_attempt_id = ?", (held["attempt_id"],))
        caught = self.refusal(self.read, held)
        self.assertIn("did not complete", caught.message)

    def test_a_retained_manifest_that_is_absent_is_refused_as_that(self):
        held = self.reviewed()
        self.control._connection.execute(
            "UPDATE outputs SET manifest_digest = ? "
            "WHERE runtime_attempt_id = ?",
            ("sha256:" + "0" * 64, held["attempt_id"]))
        caught = self.refusal(self.read, held)
        self.assertIn("retains no result manifest", caught.message)


class TheReviewEndingTakesNoCallersVerdict(ReviewResultCase):
    """W110772: `end_review_from_result`, driven end to end.

    REVIEW 2026-09-07T15-19-16Z [P1]: these ran with `terminal=None` and a
    canned freeze, which is how the omitted correlation stayed invisible. Every
    case here now carries the worker's real completion envelope and runs over
    the retained result the resolver actually reads.
    """

    def ending(self, held, *, terminal=..., attachment=None):
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        with _frozen_endings() as recorded:
            answered = review_driver.end_review_from_result(
                self.control, self.port(REVIEWER), adapter,
                attachment_id=(attachment
                               or held["attachment"]["attachment_id"]),
                disposition="completed",
                terminal=held["terminal"] if terminal is ... else terminal,
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64)
        return answered, recorded, adapter

    def test_an_accepted_claim_is_recorded_and_hands_on(self):
        held = self.reviewed(disposition="accepted")
        answered, _recorded, _adapter = self.ending(held)
        self.assertEqual(answered["outcome"], "accepted")
        self.assertEqual(answered["verdict"], "accepted")
        self.assertEqual(answered["verdict_id"], held["verdict_id"])
        self.assertTrue(answered["cleaned_up"])

    def test_a_changes_requested_claim_reaches_the_correction_round(self):
        held = self.reviewed(disposition="changes-requested")
        answered, _recorded, _adapter = self.ending(held)
        self.assertEqual(answered["outcome"], "correction")
        advanced = review_driver.open_correction(
            self.jobs, self.control, job_id="job-a", answered=answered)
        self.assertEqual(advanced["implementation"]["episode"], 2)

    def test_a_rejected_claim_stays_held_and_advances_nothing(self):
        held = self.reviewed(disposition="rejected")
        answered, _recorded, _adapter = self.ending(held)
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(answered["verdict"], "rejected")
        # A VALID REJECTION STILL RECORDS ITS FENCE AND CLEANS UP. It is a
        # decision about the Work rather than evidence nobody can read, and
        # the two held outcomes are deliberately not the same state.
        self.assertTrue(answered["cleaned_up"])
        self.assertIsNotNone(answered["verdict_id"])
        self.refusal(review_driver.open_correction, self.jobs, self.control,
                     job_id="job-a", answered=answered)

    def test_unresolved_evidence_holds_with_no_verdict_and_no_cleanup(self):
        """The whole reason this channel exists: silence is not a decision."""
        held = self.reviewed(claim=None)
        answered, _recorded, _adapter = self.ending(held)
        self.assertEqual(answered["outcome"], "held")
        self.assertIsNone(answered["verdict"])
        self.assertIsNone(answered["verdict_id"])
        self.assertIsNone(answered["verdict_record"])
        self.assertFalse(answered["cleaned_up"])
        self.assertIn(review_driver.REVIEW_CLAIM_NAMESPACE,
                      answered["held_reason"])
        self.refusal(review_driver.open_correction, self.jobs, self.control,
                     job_id="job-a", answered=answered)
        self.assertEqual(self.live("implementation")["episode"], 1)

    def test_the_explicit_operand_ending_is_unchanged_beside_it(self):
        """`end_review` still takes a verdict, still refuses a word this
        manager does not have, and still takes no terminal -- W110772 added an
        entry point beside it and changed nothing about it."""
        held = self.reviewed()
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        caught = self.refusal(
            review_driver.end_review, self.control, self.port(REVIEWER),
            adapter, attachment_id=held["attachment"]["attachment_id"],
            disposition="completed", verdict="looks-fine",
            profile=self.profile, retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64)
        self.assertEqual(caught.code, "schema")
        self.assertEqual(adapter.stops, [])

    def test_the_legacy_entry_still_needs_no_terminal_at_all(self):
        """The other half of the same sentence, driven rather than asserted in
        prose: `end_review` reaches an accepted outcome with no completion
        envelope, because its caller is not reading a verdict out of one."""
        held = self.reviewed(disposition="accepted")
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        with _frozen_endings():
            answered = review_driver.end_review(
                self.control, self.port(REVIEWER), adapter,
                attachment_id=held["attachment"]["attachment_id"],
                disposition="completed", verdict="accepted",
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64)
        self.assertEqual(answered["outcome"], "accepted")


class TheServingEndingRequiresTheWorkersCompletionEnvelope(ReviewResultCase):
    """P1 (review 2026-09-07T15-19-16Z): `terminal=None` skipped correlation.

    The measured symptom: the serving entry reached `outcome=accepted` and
    `cleaned_up=true` having compared the worker's completion envelope against
    nothing, and a string operand reached a raw `AttributeError` after the stop
    and the freeze had already happened.
    """

    def refused_ending(self, held, terminal):
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        with _frozen_endings() as recorded:
            with self.assertRaises(ContractRefusal) as caught:
                review_driver.end_review_from_result(
                    self.control, self.port(REVIEWER), adapter,
                    attachment_id=held["attachment"]["attachment_id"],
                    disposition="completed", terminal=terminal,
                    profile=self.profile, retention_disposition="retain",
                    retention_policy_digest="sha256:" + "9" * 64)
        return caught.exception, recorded, adapter

    def test_no_terminal_refuses_before_the_stop(self):
        held = self.reviewed(record=False)
        caught, recorded, adapter = self.refused_ending(held, None)
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        # NOTHING EXTERNAL HAPPENED. The shape is owned before the first act,
        # so a deployment that forgot the terminal has not stopped a container.
        self.assertEqual(adapter.stops, [])
        self.assertEqual(recorded, [])
        self.assertEqual(self.verdicts(held), 0)

    def test_a_terminal_that_is_not_a_document_refuses_before_the_stop(self):
        """It used to reach `terminal.get` as an AttributeError, after the
        freeze; a raw attribute error is neither a refusal an operator can act
        on nor a statement about the review."""
        held = self.reviewed(record=False)
        for terminal in ("sha256:" + "1" * 64, 7, ["manifest_digest"]):
            with self.subTest(terminal=terminal):
                caught, recorded, adapter = self.refused_ending(held, terminal)
                self.assertEqual(caught.category, "integrity")
                self.assertEqual(adapter.stops, [])
                self.assertEqual(recorded, [])

    def test_a_terminal_with_no_completion_identity_refuses(self):
        held = self.reviewed(record=False)
        for terminal in ({}, {"manifest_digest": None},
                         {"manifest_digest": ""}):
            with self.subTest(terminal=terminal):
                caught, _recorded, adapter = self.refused_ending(held, terminal)
                self.assertEqual(adapter.stops, [])
                self.assertIn("completion", caught.message.lower())

    def test_a_terminal_naming_another_envelope_holds_after_the_freeze(self):
        """The comparison is a different question from the shape, and it can
        only be asked once there is a frozen result to ask it about."""
        held = self.reviewed(record=False)
        caught, recorded, _adapter = self.refused_ending(
            held, {"manifest_digest": "sha256:" + "b" * 64})
        self.assertEqual(caught.code, "operation-collision")
        self.assertIn("freeze", recorded)
        self.assertIn("correlate", recorded)
        # AND NOTHING PAST THE CORRELATION RAN.
        self.assertNotIn("verdict", recorded)
        self.assertNotIn("cleanup", recorded)
        self.assertEqual(self.verdicts(held), 0)


class TheFirstVerdictGoesThroughTheOrderedEnding(ReviewResultCase):
    """P1 (review 2026-09-07T15-19-16Z): the act nothing was proving.

    Every earlier ending case ran against a verdict this fixture had already
    recorded, so the ending replayed one. What the channel exists to do is
    produce the FIRST one from a frozen result nobody has settled, and that is
    what these drive: no verdict beforehand, the worker's real completion
    envelope, the retained result the resolver actually reads, and the full
    ordered sequence asserted rather than filtered.
    """

    def ending(self, held):
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        with _frozen_endings() as recorded:
            answered = review_driver.end_review_from_result(
                self.control, self.port(REVIEWER), adapter,
                attachment_id=held["attachment"]["attachment_id"],
                disposition="completed", terminal=held["terminal"],
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64)
        return answered, recorded, adapter

    def test_the_ending_records_the_first_verdict_for_this_checkpoint(self):
        held = self.reviewed(disposition="accepted", record=False)
        self.assertEqual(self.verdicts(held), 0)
        answered, _recorded, _adapter = self.ending(held)
        self.assertEqual(answered["outcome"], "accepted")
        self.assertEqual(self.verdicts(held), 1)
        self.assertIsNotNone(answered["verdict_id"])
        self.assertTrue(answered["cleaned_up"])

    def test_it_runs_every_recorded_step_in_the_recorded_order(self):
        """ASSERTED WHOLE. The previous version filtered the expected sequence
        down to the steps that were observed, so a missing `correlate` or
        `resolve` could not fail it -- which is exactly what happened."""
        held = self.reviewed(record=False)
        _answered, recorded, _adapter = self.ending(held)
        self.assertEqual(recorded, list(review_driver.REVIEW_RESULT_ENDING))

    def test_the_result_it_correlates_is_the_one_the_resolver_reads(self):
        """One freeze, one retained manifest, one document. The canned freeze
        this replaces answered a digest nothing retained, so the correlation
        and the resolver were looking at two different things."""
        held = self.reviewed(record=False)
        answered, _recorded, _adapter = self.ending(held)
        self.assertEqual(answered["manifest_digest"], held["result_digest"])
        read = review_driver.review_verdict_from_result(
            self.control, attachment_id=held["attachment"]["attachment_id"])
        self.assertEqual(read["result_digest"], answered["manifest_digest"])

    def test_replay_from_the_freeze_cutpoint_records_no_second_verdict(self):
        """A manager that died between the freeze and the cleanup re-enters
        here, derives the same claim from the same retained result, and
        replays the verdict it already recorded."""
        held = self.reviewed(disposition="changes-requested", record=False)
        first, _recorded, _adapter = self.ending(held)
        again, recorded, _adapter = self.ending(held)
        self.assertEqual(first, again)
        self.assertEqual(recorded, list(review_driver.REVIEW_RESULT_ENDING))
        self.assertEqual(self.verdicts(held), 1)
        self.assertEqual(again["outcome"], "correction")


class ACompetingClaimOnAnyOutputRefuses(ReviewResultCase):
    """P1 (review 2026-09-07T15-19-16Z): only `logs` was being checked.

    A schema-valid result carrying `accepted` on findings and `rejected` on the
    proposal output was read as `accepted`. The common manifest a shared Job
    declares names `proposal` expressly, so that is the shape this deployment
    actually produces rather than a hypothetical one.
    """

    def competing(self, held, name, verdict="rejected"):
        _digest, document = self.retained("review-attempt-1", generation=1,
                                          observed=held["observed"])
        claim = {"verdict": verdict, "base": held["observed"]["base"],
                 "head": held["observed"]["head"],
                 "tree": held["observed"]["tree"]}
        outputs = list(document["outputs"])
        found = [one for one in outputs if one["name"] == name]
        if found:
            outputs[outputs.index(found[0])] = dict(
                found[0], result_metadata={
                    review_driver.REVIEW_CLAIM_NAMESPACE: claim})
        else:
            outputs.append(dict(
                outputs[0], name=name, type="git-change-proposal",
                result_metadata={
                    review_driver.REVIEW_CLAIM_NAMESPACE: claim}))
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"], outputs=outputs)
        with self.assertRaises(ContractRefusal) as caught:
            review_driver.review_verdict_from_result(
                self.control, attachment_id=held["attachment"][
                    "attachment_id"])
        return caught.exception

    def test_a_claim_on_the_proposal_output_refuses_as_ambiguous(self):
        held = self.reviewed()
        caught = self.competing(held, "proposal")
        self.assertEqual(caught.category, "ambiguous")
        self.assertIn("proposal", caught.message)

    def test_a_claim_on_the_logs_output_still_refuses(self):
        held = self.reviewed()
        caught = self.competing(held, "logs")
        self.assertEqual(caught.category, "ambiguous")
        self.assertIn("logs", caught.message)

    def test_a_claim_on_the_wrong_output_and_none_on_findings_refuses(self):
        """Not a second opinion to weigh: a reviewer that decided somewhere
        this manager does not read has not decided here."""
        held = self.reviewed(record=False, claim=None)
        caught = self.competing(held, "logs", verdict="accepted")
        self.assertEqual(caught.category, "ambiguous")

    def test_a_competing_claim_holds_with_no_verdict_and_no_cleanup(self):
        held = self.reviewed(record=False)
        self.competing(held, "proposal")
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        with _frozen_endings() as recorded:
            answered = review_driver.end_review_from_result(
                self.control, self.port(REVIEWER), adapter,
                attachment_id=held["attachment"]["attachment_id"],
                disposition="completed", terminal=held["terminal"],
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64)
        self.assertEqual(answered["outcome"], "held")
        self.assertIsNone(answered["verdict"])
        self.assertFalse(answered["cleaned_up"])
        self.assertNotIn("cleanup", recorded)
        self.assertEqual(self.verdicts(held), 0)

    def test_ordinary_unrelated_metadata_on_another_output_is_untouched(self):
        """The scan is for this namespace and nothing else; an output carrying
        somebody else's extension is not a competing verdict."""
        held = self.reviewed()
        _digest, document = self.retained("review-attempt-1", generation=1,
                                          observed=held["observed"])
        outputs = [dict(one, result_metadata={"baton.git-proposal/1": {
            "base": "a" * 40, "head": "b" * 40, "transport": "objects.bundle",
            "recap": "unrelated"}}) if one["name"] == "logs" else one
            for one in document["outputs"]]
        self.retained("review-attempt-1", generation=1,
                      observed=held["observed"], outputs=outputs)
        read = review_driver.review_verdict_from_result(
            self.control, attachment_id=held["attachment"]["attachment_id"])
        self.assertEqual(read["verdict"], "accepted")

class RealLineProfile(Profile):
    """The fake profile, answering the REAL objects a repository holds.

    W110772's joined proof needs one thing the fake cannot invent: checkpoint
    evidence whose base, head and tree are the objects a real reviewer actually
    observed. Git's own checkpoint profile is `checkpoint_profiles`' and is
    proved in its own suite; what is under test here is the CHANNEL, so this
    keeps every rule of the fake -- retention, validation, current-revision
    tracking -- and substitutes the three object names for real ones.
    """

    def __init__(self, observed):
        super().__init__()
        self.observed = observed

    def freeze(self, repository, *, line_id, revision, declared_base):
        held = super().freeze(repository, line_id=line_id, revision=revision,
                              declared_base=declared_base)
        del self.held[int(held["head"], 16)]
        evidence = dict(held, base=self.observed["base"],
                        head=self.observed["head"],
                        tree=self.observed["tree"])
        self.held[revision] = evidence
        self.current_revision = revision
        return dict(evidence)

    def validate(self, repository, evidence, *, current=False):
        if self.held.get(self.current_revision) != evidence:
            raise ContractRefusal("policy", "profile-uncertified",
                                  "checkpoint evidence is not retained")
        return dict(evidence)


class TheReviewerDecidesAndTheManagerReadsThatDecision(ReviewResultCase):
    """W110772's acceptance: one real worker turn, all the way to a verdict.

    NOTHING IN THE CHANNEL IS SUBSTITUTED. The real `ClaudeAgent.work` runs a
    review turn over a real repository with a deterministic process seam in
    place of a model; `baton_worker.answered` performs the GENERIC MEASUREMENT
    of the two directories it wrote; the measured outputs are retained as a
    real result manifest; and `review_verdict_from_result` and `record_verdict`
    are the production ones. What stands in is named: the model, and the
    custody artifact identities a sealing runtime would mint.
    """

    def setUp(self):
        super().setUp()
        import sys
        worker = pathlib.Path(__file__).resolve().parents[3] / "worker"
        if str(worker) not in sys.path:
            sys.path.insert(0, str(worker))
        namespace = worker.parent / "python" / "src" / "baton_v12"
        if str(namespace) not in sys.path:
            sys.path.insert(0, str(namespace))
        global claude_agent, baton_worker
        import baton_worker
        import claude_agent
        self.write(os.path.join(self.container, "input", "task.json"),
                   json.dumps({"schema": "baton.dogfood-task/2",
                               "task_id": "w110772-joined",
                               "instructions": "Cover the new helper.",
                               "verification": ["python3", "harness.py"],
                               "source_root": "source",
                               "source_profile": "git-line",
                               "declared_base": self.observed["base"]}))

    def line_base(self):
        """The reviewed repository is built HERE, because the line has to be
        declared against a base the repository actually holds."""
        self.container = tempfile.mkdtemp(prefix="v12-w110772-", dir=self.root)
        self.reviewed_source = os.path.join(self.container, "input", "source")
        self.review_output = os.path.join(self.container, "output")
        os.makedirs(self.reviewed_source)
        os.makedirs(self.review_output)
        self.write(os.path.join(self.reviewed_source, "harness.py"),
                   "print('the reviewed harness')\n")
        self.repository("init", "-q", "-b", "main")
        self.repository("add", "--all")
        self.repository("commit", "-q", "--message", "base")
        real_base = self.repository("rev-parse", "HEAD").strip()
        self.write(os.path.join(self.reviewed_source, "covered.py"),
                   "def covered():\n    return True\n")
        self.repository("add", "--all")
        self.repository("commit", "-q", "--message", "the change")
        self.observed = {
            "base": real_base,
            "head": self.repository("rev-parse", "HEAD").strip(),
            "tree": self.repository("rev-parse", "HEAD^{tree}").strip()}
        # THE PROFILE ANSWERS THE OBJECTS THE REVIEWER WILL ACTUALLY SEE, and
        # it is composed here so the line is created under it.
        self.profile = RealLineProfile(self.observed)
        return real_base

    @staticmethod
    def write(place, body):
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    def repository(self, *arguments):
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                       "HOME": self.container,
                       "GIT_CONFIG_GLOBAL": os.devnull,
                       "GIT_CONFIG_SYSTEM": os.devnull,
                       "GIT_TERMINAL_PROMPT": "0",
                       "GIT_AUTHOR_NAME": "Baton Test",
                       "GIT_AUTHOR_EMAIL": "test@baton.invalid",
                       "GIT_COMMITTER_NAME": "Baton Test",
                       "GIT_COMMITTER_EMAIL": "test@baton.invalid"}
        answer = subprocess.run(
            ["git", "-C", self.reviewed_source] + list(arguments),
            capture_output=True, text=True, env=environment, timeout=300)
        self.assertEqual(answer.returncode, 0,
                         f"git {arguments} failed: {answer.stderr}")
        return answer.stdout

    # -- the real worker turn ------------------------------------------------

    DECLARED = [
        {"name": name, "type": "directory-result", "path": name,
         "required": False,
         "constraints": {"max_bytes": 1 << 20, "max_entries": 100,
                         "allowed_media_types": ["text/plain"],
                         "link_policy": "forbid", "validator_digest": None}}
        for name in ("findings", "logs")]

    def turn(self, verdict="accepted"):
        """One real `ClaudeAgent.work` review turn, measured by the worker."""
        def run(argv, **options):
            if argv[0] == "git":
                return subprocess.run(
                    list(argv), env={"PATH": os.environ.get("PATH", "/bin"),
                                     "HOME": self.container,
                                     "GIT_CONFIG_GLOBAL": os.devnull,
                                     "GIT_CONFIG_SYSTEM": os.devnull},
                    **options)
            # THE DETERMINISTIC PROCESS SEAM. It writes a report exactly where
            # the prompt asks for one and nowhere else, which is all a model
            # does that matters to this channel.
            self.write(os.path.join(options["cwd"],
                                    claude_agent.REVIEW_REPORT),
                       json.dumps({"schema": claude_agent.REVIEW_REPORT_SCHEMA,
                                   "verdict": verdict,
                                   "findings": "read the diff and the tests"}))
            return subprocess.CompletedProcess(argv, 0, None, None)

        held = (claude_agent.INPUT_ROOT, claude_agent.OUTPUT_ROOT,
                claude_agent.CREDENTIAL_ROOT, baton_worker.OUTPUT_ROOT)
        claude_agent.INPUT_ROOT = os.path.join(self.container, "input")
        claude_agent.OUTPUT_ROOT = self.review_output
        # THE SLOT IS A FILE THAT SAYS IT IS NOT A CREDENTIAL, exactly as the
        # adapter's own suite stages it: its bytes are never read, so a real
        # bearer would prove nothing and would put a secret in a repository.
        claude_agent.CREDENTIAL_ROOT = os.path.join(self.container,
                                                    "credentials")
        os.makedirs(claude_agent.CREDENTIAL_ROOT, exist_ok=True)
        self.write(os.path.join(claude_agent.CREDENTIAL_ROOT,
                                claude_agent.CREDENTIAL_SLOT),
                   "not-a-credential\n")
        baton_worker.OUTPUT_ROOT = self.review_output
        try:
            answered = claude_agent.ClaudeAgent(
                run=run, home=tempfile.mkdtemp(prefix="scratch-",
                                               dir=self.container)).work(
                {"contract": "the frozen task",
                 "role": claude_agent.REVIEW_ROLE}, list(self.DECLARED))
            # THE GENERIC MEASUREMENT, performed by the worker rather than by
            # this case: the agent said what it produced and `answered` walks,
            # bounds and digests the directories to say what is there.
            measured = baton_worker.answered(self.DECLARED,
                                             answered["outputs"])
        finally:
            (claude_agent.INPUT_ROOT, claude_agent.OUTPUT_ROOT,
             claude_agent.CREDENTIAL_ROOT, baton_worker.OUTPUT_ROOT) = held
        return answered, measured

    def sealed(self, attempt_id, generation, measured):
        """The measured outputs, given the custody identities a seal mints.

        NAMED AS A STAND-IN. `request_freeze` mints artifact identities from a
        live runtime, and there is none here; every other member below is the
        worker's own answer or this manager's own measurement of it.
        """
        composed = []
        for one in measured:
            content = one["content_manifest"]
            # `path` IS THE WORKER'S AND NOT THE RESULT'S. A `workerOutput`
            # says where in the container it wrote; an `artifactOutput` says
            # what the manager holds, and custody is not a container path.
            composed.append(dict(
                {member: value for member, value in one.items()
                 if member != "path"},
                artifact={
                    "artifact_id": f"artifact-{one['name']}-{attempt_id}",
                    "media_type": "text/plain",
                    "bytes": content["total_bytes"],
                    "content_digest": content["tree_digest"],
                    "locator": f"file:///var/lib/baton/{attempt_id}/"
                               f"{one['name']}"}))
        return composed

    def joined(self, verdict):
        """One real worker turn, ended through the ordered production entry.

        REVIEW 2026-09-07T15-19-16Z [P1]: this pre-recorded the verdict, passed
        no terminal and ran over a canned freeze, so the acceptance proof was
        the one place the omitted correlation could not show. It now starts
        with no verdict at all, carries the worker's own completion envelope,
        and runs over the retained result the resolver reads.
        """
        _answered, measured = self.turn(verdict)
        held = self.reviewed(disposition=verdict, record=False,
                             outputs=self.sealed("review-attempt-1", 1,
                                                 measured))
        self.assertEqual(self.verdicts(held), 0)
        adapter = _Adapter(f"runtime-{held['attempt_id']}")
        with _frozen_endings() as recorded:
            ended = review_driver.end_review_from_result(
                self.control, self.port(REVIEWER), adapter,
                attachment_id=held["attachment"]["attachment_id"],
                disposition="completed", terminal=held["terminal"],
                profile=self.profile, retention_disposition="retain",
                retention_policy_digest="sha256:" + "9" * 64)
        return held, ended, recorded

    def test_a_real_review_turn_reaches_an_accepted_verdict(self):
        answered, measured = self.turn("accepted")
        self.assertEqual(answered["disposition"], "completed")
        held = self.reviewed(disposition="accepted", record=False,
                             outputs=self.sealed("review-attempt-1", 1,
                                                 measured))
        read = review_driver.review_verdict_from_result(
            self.control, attachment_id=held["attachment"]["attachment_id"])
        self.assertEqual(read["verdict"], "accepted")
        self.assertEqual({one: read[one] for one in ("base", "head", "tree")},
                         self.observed)

    def test_the_real_turn_produces_the_first_verdict_through_the_ending(self):
        held, ended, recorded = self.joined("accepted")
        self.assertEqual(ended["outcome"], "accepted")
        self.assertEqual(recorded, list(review_driver.REVIEW_RESULT_ENDING))
        self.assertEqual(self.verdicts(held), 1)
        self.assertIsNotNone(ended["verdict_id"])

    def test_a_real_changes_requested_turn_opens_the_correction_round(self):
        _held, ended, recorded = self.joined("changes-requested")
        self.assertEqual(ended["outcome"], "correction")
        self.assertEqual(recorded, list(review_driver.REVIEW_RESULT_ENDING))
        advanced = review_driver.open_correction(
            self.jobs, self.control, job_id="job-a", answered=ended)
        self.assertEqual(advanced["implementation"]["episode"], 2)

    def test_a_real_rejected_turn_stays_held(self):
        _held, ended, _recorded = self.joined("rejected")
        self.assertEqual(ended["outcome"], "held")
        self.assertEqual(ended["verdict"], "rejected")
        self.refusal(review_driver.open_correction, self.jobs, self.control,
                     job_id="job-a", answered=ended)


# W110772, review 2026-09-07T15-37-14Z: the isolated fixtures above are kept
# unchanged. This proof adds the public custody path they deliberately replace.
from tests.manager.test_attempts import Adapter as _ReviewRuntimeTransport
from tests.manager.test_intake import Custodian as _ReviewCustodianTransport
from tests.manager.test_offers import FakeSession as _ReviewAuthorityTransport


class _EndingAuthority(_ReviewAuthorityTransport):
    def cancel(self, operands):
        answer = super().cancel(operands)
        self.live_assignment = None
        return answer


class _ReviewFileCustodian(_ReviewRuntimeTransport, _ReviewCustodianTransport):
    """Deterministic engine/Authority seams; actual file sealing and collection.

    Public manager owners create all output, intake, retention, verdict and
    cleanup records. The external engine has no container, and directory custody
    uses the existing deterministic helper response over test-owned roots.
    """

    def __init__(self, runtime_id, roots, declaration, policy):
        _ReviewRuntimeTransport.__init__(self, runtime_id)
        _ReviewCustodianTransport.__init__(self)
        from baton_v12.worker_manager.sealing import declared_outputs
        self.roots = roots
        self.declaration = declaration
        self.declared = declared_outputs(declaration["outputs"])
        self.input_digest = declaration["manifest_digest"]
        self.policy = policy
        self.custody = os.path.join(os.path.dirname(roots["workspace"]), "custody")
        os.makedirs(self.custody, exist_ok=True)
        self.seals = []

    def stop(self, operands):
        self.stopped.append(dict(operands))
        self.observation = {"state": "quiescent", "why": "deterministic engine stopped", "mounts": None}
        return {"state": "quiescent", "runtime_id": self.runtime_id}

    def seal(self, operands):
        from baton_v12.worker_manager.sealing import sealed_result
        self.seals.append(dict(operands))
        return sealed_result(operands, roots=self.roots, declared=self.declared,
                             identity={"policy_digest": self.policy}, custody=self.custody,
                             input_manifest_digest=self.input_digest)

    def collect(self, operands):
        from baton_v12.worker_manager.sealing import collected_result
        self.collected_with.append(dict(operands))
        return collected_result(operands, custody=self.custody, declared=self.declared)

    def destroy(self, command):
        answer = _ReviewCustodianTransport.destroy(self, command)
        self.listing = []
        self.observation = {"state": "absent", "why": "deterministic engine destroyed", "mounts": None}
        return answer

    def prove_line_consumable(self, store, **operands):
        raise AssertionError("a review ending does not consume an implementation line")


class TheWorkerCompletionTraversesPublicCustody(ReviewResultCase):
    """Real worker envelope, real files/stores and every public custody owner.

    The provider process, engine and Authority transport are deterministic.
    Checkpoint profile evidence uses the existing real-object profile fixture.
    No output, intake, retention, verdict or cleanup row is seeded by this proof.
    """

    line_base = TheReviewerDecidesAndTheManagerReadsThatDecision.line_base
    repository = TheReviewerDecidesAndTheManagerReadsThatDecision.repository
    write = staticmethod(TheReviewerDecidesAndTheManagerReadsThatDecision.write)
    turn = TheReviewerDecidesAndTheManagerReadsThatDecision.turn
    DECLARED = copy.deepcopy(TheReviewerDecidesAndTheManagerReadsThatDecision.DECLARED)
    for _declaration in DECLARED:
        _declaration["constraints"]["allowed_media_types"] = ["application/octet-stream"]

    def setUp(self):
        super().setUp()
        import sys
        worker = pathlib.Path(__file__).resolve().parents[3] / "worker"
        for place in (worker, worker.parent / "python/src/baton_v12"):
            if str(place) not in sys.path:
                sys.path.insert(0, str(place))
        global claude_agent, baton_worker
        import baton_worker
        import claude_agent
        self.write(os.path.join(self.container, "input/task.json"), json.dumps({
            "schema": "baton.dogfood-task/2", "task_id": "w110772-public-custody",
            "instructions": "Cover the new helper.", "verification": ["python3", "harness.py"],
            "source_root": "source", "source_profile": "git-line", "declared_base": self.observed["base"]}))
        self.store = self.control  # Existing composed-input helper's public-store operand.
        self.worker_turns = 0

    def registered(self, attempt_id, participant, principal):
        from baton_v12.worker_manager import (AuthorityPort, accept_offer, activate_assignment,
            issue_offer, record_attempt, retain_manifest, submit_claim)
        from tests.manager.test_offers import SCOPE, decision, fake_claim_signature
        from tests.manager.test_output import OutputCase, POLICY, sealed
        from tests.manager.test_attempts import ADAPTER
        declaration = sealed(dict(OutputCase.published(), work_ref={"authority_uuid": self.AUTHORITY, "work_id": WORK_A},
                                  outputs=copy.deepcopy(self.DECLARED), runtime_profile_digest=PROFILE, policy_digest=POLICY))
        input_digest = retain_manifest(self.control, declaration, "inputManifest")["digest"]
        session = _EndingAuthority(participant=participant, work={"status": "open", "phase": "queued", "handler": None,
            "gate": None, "authority_uuid": self.AUTHORITY, "scope": SCOPE, "route": "review"})
        assignment = {"work_ref": {"authority_uuid": self.AUTHORITY, "work_id": WORK_A}, "participant": participant, "generation": 1}
        session.claim_answer = {"assignment": assignment, "claim_event": 1,
            "decision": decision(participant=participant, principal=principal, role="review")}
        session.live_assignment = dict(assignment)
        session.fence_answer = {"cause": "cancelled", "assignment": dict(assignment), "phase": "block",
                                "gate": "runtime-quiescence:1", "fenced": True}
        port = AuthorityPort(session, fake_claim_signature)
        offer_id = "offer-" + attempt_id
        issue_offer(self.control, port, offer_id=offer_id, work_id=WORK_A, runtime_attempt_id=attempt_id,
                    input_digest=input_digest, policy_digest=POLICY, profile_digest=PROFILE,
                    profile_name="reference", mint_bearer=lambda: "fixture-offer-bearer")
        accept_offer(self.control, port, offer_id=offer_id, decision="accept", bearer="fixture-offer-bearer", now=NOW,
                     runtime_attempt_id=attempt_id, work_ref=assignment["work_ref"])
        record_attempt(self.control, attempt_id=attempt_id, adapter_name="acp", adapter_digest=ADAPTER,
                       profile_digest=PROFILE, input_digest=input_digest, policy_digest=POLICY)
        submit_claim(self.control, port, offer_id=offer_id)
        activate_assignment(self.control, port, attempt_id=attempt_id, expect=assignment)
        roots = assignment_workspace(self.group, self.storage, attempt_id)
        adapter = _ReviewFileCustodian("runtime-" + attempt_id, roots, declaration, POLICY)
        return port, adapter, assignment

    def start_registered(self, attempt_id, adapter, assignment):
        from baton_v12.worker_manager import reconcile_runtime, request_runtime_start
        # Source mountpoint/line boundary first, immutable input composition and
        # runtime start second, as in deployment. A frozen input root cannot grow
        # a new source mountpoint after the runtime has already started.
        inputs, _ = input_roots.composed(self, self.storage, work_ref=assignment["work_ref"], participant=assignment["participant"],
                                         generation=1, runtime_attempt_id=attempt_id, given=adapter.declaration)
        request_runtime_start(self.control, adapter, attempt_id=attempt_id, inputs=inputs)
        reconcile_runtime(self.control, adapter, attempt_id=attempt_id)

    def produced(self):
        from baton_v12.worker_manager import (authorize_cleanup, decide_retention, freeze_checkpoint,
            observe, reconcile_runtime, request_freeze, request_intake)
        writer_port, writer_adapter, writer_assignment = self.registered("public-writer", WRITER, "public-writer-principal")
        writer = review_driver.prepare_implementation(self.control, line_id=self.line["line_id"], attempt_id="public-writer",
            generation=1, worker_id="public-writer-worker", profile=self.profile)
        self.start_registered("public-writer", writer_adapter, writer_assignment)
        # The prerequisite writer has deterministic files, not a model turn.
        # Settle its real custody and lane before launching the independent review.
        with mock.patch.object(baton_worker, "OUTPUT_ROOT", writer_adapter.roots["workspace"]):
            for declaration in self.DECLARED:
                self.write(os.path.join(writer_adapter.roots["workspace"], declaration["path"], "prerequisite.txt"), "writer prerequisite\n")
            outputs = baton_worker.answered(self.DECLARED, [{"name": declaration["name"], "status": "present", "result_metadata": {}}
                                                            for declaration in self.DECLARED])
            baton_worker.publish_completion(writer_assignment, "completed", outputs)
        writer_adapter.stop({"runtime_id": writer_adapter.runtime_id})
        reconcile_runtime(self.control, writer_adapter, attempt_id="public-writer")
        observe(self.control, attempt_id="public-writer", axis="worker_disposition", value="completed")
        request_freeze(self.control, writer_port, writer_adapter, attempt_id="public-writer", disposition="completed")
        receipt = request_intake(self.control, writer_port, writer_adapter, attempt_id="public-writer")
        decide_retention(self.control, writer_port, writer_adapter, attempt_id="public-writer",
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]], disposition="retain", retention_policy_digest="sha256:" + "9" * 64)
        checkpoint = freeze_checkpoint(self.control, writer_id=writer["writer_id"], generation=1,
                                       profile=self.profile, port=writer_port)
        authorize_cleanup(self.control, writer_port, writer_adapter, attempt_id="public-writer", retention_policy_digest="sha256:" + "9" * 64)
        port, adapter, assignment = self.registered("public-review", REVIEWER, "public-review-principal")
        attachment = review_driver.prepare_review(self.control, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id="public-review", generation=1, reviewer_worker_id="public-review-worker", profile=self.profile)
        self.start_registered("public-review", adapter, assignment)
        self.review_output = adapter.roots["workspace"]
        answered, measured = self.turn("accepted")
        self.worker_turns += 1
        self.assertEqual(answered["disposition"], "completed")
        with mock.patch.object(baton_worker, "OUTPUT_ROOT", self.review_output):
            completion = baton_worker.publish_completion(assignment, answered["disposition"], measured)
        self.assertEqual(json.loads(pathlib.Path(self.review_output, "output.json").read_text()), completion)
        self.assertEqual(completion["manifest_digest"], digest({key: value for key, value in completion.items() if key != "manifest_digest"}))
        return {"checkpoint_id": checkpoint["checkpoint_id"], "attachment": attachment, "attempt_id": "public-review",
                "port": port, "adapter": adapter, "terminal": completion, "measured": measured}

    @contextlib.contextmanager
    def public_ending(self, *, interrupt_after_freeze=False):
        """Order observers delegate every call; the cut fires after real freeze."""
        recorded = []
        class AfterFreeze(Exception):
            pass
        self.after_freeze = AfterFreeze
        def wrapping(name, function):
            def call(*args, **kwargs):
                recorded.append(name)
                answer = function(*args, **kwargs)
                if name == "freeze" and interrupt_after_freeze:
                    raise AfterFreeze()
                return answer
            return call
        with contextlib.ExitStack() as stack:
            for module, member, name in ((review_driver, "reconcile_runtime", "quiesce"), (review_driver, "observe", "observe"),
                (review_driver, "request_freeze", "freeze"), (review_driver, "_correlated", "correlate"),
                (review_driver, "request_intake", "intake"), (review_driver, "decide_retention", "retain"),
                (review_driver, "review_verdict_from_result", "resolve"),
                (review_driver.review_cycles, "record_verdict", "verdict"), (review_driver, "authorize_cleanup", "cleanup")):
                stack.enter_context(mock.patch.object(module, member, wrapping(name, getattr(module, member))))
            yield recorded

    def end(self, held):
        return review_driver.end_review_from_result(self.control, held["port"], held["adapter"],
            attachment_id=held["attachment"]["attachment_id"], disposition="completed", terminal=held["terminal"],
            profile=self.profile, retention_disposition="retain", retention_policy_digest="sha256:" + "9" * 64)

    def assert_owned_custody(self, held, ended):
        from baton_v12.worker_manager import frozen_output_of, intake_receipt_of, load_manifest, retentions_of, verdict_of
        from baton_v12.worker_manager.attempts import attempt_runtime_of
        frozen = frozen_output_of(self.control, held["attempt_id"])
        result = load_manifest(self.control, frozen["manifest_digest"], "resultManifest")
        receipt = intake_receipt_of(self.control, held["attempt_id"])
        retained = retentions_of(self.control, held["attempt_id"])
        self.assertEqual(ended["outcome"], "accepted")
        self.assertTrue(ended["cleaned_up"])
        self.assertEqual(result["completion_manifest_digest"], held["terminal"]["manifest_digest"])
        self.assertNotEqual(result["completion_manifest_digest"], _result_vector()["completion_manifest_digest"])
        self.assertEqual(result["assignment_ref"], held["terminal"]["assignment_ref"])
        self.assertEqual(ended["result_id"], frozen["result_id"])
        self.assertEqual(ended["manifest_digest"], result["manifest_digest"])
        self.assertEqual(receipt["receipt_digest"], ended["receipt_digest"])
        self.assertEqual(receipt["result_id"], frozen["result_id"])
        self.assertEqual(receipt["custody"], "accepted")
        self.assertEqual({one["artifact_id"] for one in receipt["artifacts"]}, set(ended["artifacts"]))
        self.assertEqual({one["artifact_id"] for one in retained}, set(ended["artifacts"]))
        self.assertTrue(all(one["disposition"] == "retain" for one in retained))
        measured = {one["name"]: one for one in held["measured"]}
        for output in result["outputs"]:
            self.assertEqual(output["content_manifest"], measured[output["name"]]["content_manifest"])
            self.assertEqual(output["result_metadata"], measured[output["name"]]["result_metadata"])
        from baton_v12.worker_manager.workspaces import directory_manifest
        for artifact in receipt["artifacts"]:
            place = artifact["custody_locator"].removeprefix("file://")
            self.assertTrue(os.path.isdir(place))
            self.assertEqual(directory_manifest(place)["tree_digest"], artifact["content_digest"])
        persisted = verdict_of(self.control, ended["verdict_id"])
        recorded_at = persisted.pop("recorded_at")
        self.assertEqual(review_driver.boundaries.instant(recorded_at, "the verdict timestamp"), NOW)
        for source, target in (("base_object", "base"), ("head_object", "head"),
                               ("tree_object", "tree"), ("review_assignment_generation", "review_generation")):
            persisted[target] = persisted.pop(source)
        self.assertEqual(persisted, ended["verdict_record"])
        self.assertEqual(self.verdicts(held), 1)
        self.assertEqual(attempt_runtime_of(self.control, held["attempt_id"])["execution_runtime"], "destroyed")
        self.assertEqual(len(held["adapter"].destroyed_with), 1)
        self.assertFalse(os.path.exists(self.review_output))
        self.assertEqual(self.worker_turns, 1)
        self.assert_historical_replay(held, ended)

    def assert_historical_replay(self, held, ended):
        from baton_v12.worker_manager import integration_checkpoint
        session = held["port"]._session
        self.assertEqual(sum(kind == "cancel" for kind, _ in session.calls), 1)
        calls = copy.deepcopy(session.calls)
        changes = self.control._connection.total_changes
        checkpoint = review_driver.review_cycles.checkpoint_of(self.control, held["checkpoint_id"])
        with contextlib.ExitStack() as stack:
            for member in ("stop", "seal", "collect", "retain", "destroy"):
                stack.enter_context(mock.patch.object(held["adapter"], member, side_effect=AssertionError("replay makes no runtime/custody call")))
            stack.enter_context(mock.patch.object(held["port"], "cancel", side_effect=AssertionError("replay makes no fence call")))
            stack.enter_context(mock.patch.object(self, "turn", side_effect=AssertionError("replay makes no worker call")))
            eligible = integration_checkpoint(self.control, ended["line_id"])
            self.assertEqual(eligible, {"line_id": ended["line_id"], "checkpoint_id": held["checkpoint_id"],
                "verdict_id": ended["verdict_id"], "checkpoint_digest": checkpoint["checkpoint_digest"],
                "evidence": checkpoint["evidence"]})
            self.assertEqual(self.end(held), ended)
            self.assertEqual(self.end(held), ended)
            self.assertEqual(review_driver.review_cycles.record_verdict(self.control,
                attachment_id=held["attachment"]["attachment_id"], disposition="accepted",
                profile=self.profile, port=held["port"]), ended["verdict_record"])
        self.assertEqual(self.control._connection.total_changes, changes)
        self.assertEqual(session.calls, calls)
        self.assertEqual(self.verdicts(held), 1)
        self.assertEqual(len(held["adapter"].destroyed_with), 1)
        self.assertEqual(self.worker_turns, 1)

    def test_actual_completion_reaches_first_verdict_and_public_custody(self):
        from baton_v12.worker_manager import frozen_output_of, intake_receipt_of, retentions_of
        held = self.produced()
        self.assertEqual(self.verdicts(held), 0)
        self.assertIsNone(frozen_output_of(self.control, held["attempt_id"]))
        self.assertIsNone(intake_receipt_of(self.control, held["attempt_id"]))
        self.assertEqual(retentions_of(self.control, held["attempt_id"]), ())
        with self.public_ending() as recorded:
            ended = self.end(held)
        self.assertEqual(ended["outcome"], "accepted", ended["held_reason"])
        self.assertEqual(recorded, list(review_driver.REVIEW_RESULT_ENDING))
        self.assert_owned_custody(held, ended)

    def test_after_real_freeze_reentry_uses_same_completion_without_another_turn(self):
        from baton_v12.worker_manager import frozen_output_of, intake_receipt_of, retentions_of
        held = self.produced()
        with self.public_ending(interrupt_after_freeze=True) as before:
            with self.assertRaises(self.after_freeze):
                self.end(held)
        self.assertEqual(before, ["quiesce", "observe", "freeze"])
        frozen = frozen_output_of(self.control, held["attempt_id"])
        self.assertIsNotNone(frozen)
        self.assertIsNone(intake_receipt_of(self.control, held["attempt_id"]))
        self.assertEqual(retentions_of(self.control, held["attempt_id"]), ())
        self.assertEqual(self.verdicts(held), 0)
        self.assertEqual(held["adapter"].destroyed_with, [])
        with self.public_ending() as after, mock.patch.object(self, "turn", side_effect=AssertionError("no repeated worker invocation")):
            ended = self.end(held)
        self.assertEqual(ended["outcome"], "accepted", ended["held_reason"])
        self.assertEqual(after, list(review_driver.REVIEW_RESULT_ENDING))
        self.assertEqual(frozen_output_of(self.control, held["attempt_id"]), frozen)
        self.assertEqual(len(held["adapter"].seals), 2)
        self.assert_owned_custody(held, ended)

    @contextlib.contextmanager
    def no_more_external_acts(self, held):
        calls = copy.deepcopy(held["port"]._session.calls)
        changes = self.control._connection.total_changes
        with contextlib.ExitStack() as stack:
            for member in ("stop", "seal", "collect", "retain", "destroy"):
                stack.enter_context(mock.patch.object(held["adapter"], member, side_effect=AssertionError("refusal performs no external act")))
            stack.enter_context(mock.patch.object(held["port"], "cancel", side_effect=AssertionError("refusal must not fence")))
            yield
        self.assertEqual(held["port"]._session.calls, calls)
        self.assertEqual(self.control._connection.total_changes, changes)

    def custody_damage(self):
        # Deliberate corruption of this fixture's private store. The public
        # readers must refuse missing or contradictory owner evidence.
        return (
            ("missing result manifest", "DELETE FROM manifests WHERE digest = (SELECT manifest_digest FROM outputs WHERE runtime_attempt_id = 'public-review')"),
            ("missing intake", "DELETE FROM intakes WHERE runtime_attempt_id = 'public-review'"),
            ("foreign receipt", "UPDATE intakes SET result_id = 'foreign-result' WHERE runtime_attempt_id = 'public-review'"),
            ("foreign manifest", "UPDATE intakes SET manifest_digest = 'sha256:foreign' WHERE runtime_attempt_id = 'public-review'"),
            ("quarantined custody", "UPDATE intakes SET custody = 'quarantined' WHERE runtime_attempt_id = 'public-review'"),
            ("missing artifact", "DELETE FROM intake_artifacts WHERE runtime_attempt_id = 'public-review' AND artifact_id = 'public-review:logs'"),
            ("foreign measurement", "UPDATE intake_artifacts SET bytes = bytes + 1 WHERE runtime_attempt_id = 'public-review'"),
            ("missing retention", "DELETE FROM retentions WHERE runtime_attempt_id = 'public-review'"),
            ("partly retained", "DELETE FROM retentions WHERE runtime_attempt_id = 'public-review' AND artifact_id = 'public-review:logs'"),
            ("foreign policy", "UPDATE retentions SET retention_policy_digest = 'sha256:foreign' WHERE runtime_attempt_id = 'public-review'"))

    def test_first_verdict_requires_complete_matching_custody(self):
        held = self.produced()
        class BeforeVerdict(Exception):
            pass
        with mock.patch.object(review_driver.review_cycles, "record_verdict", side_effect=BeforeVerdict):
            with self.assertRaises(BeforeVerdict):
                self.end(held)
        self.assertEqual(self.verdicts(held), 0)
        for name, statement in self.custody_damage():
            with self.subTest(evidence=name):
                self.control._connection.execute("SAVEPOINT damaged")
                try:
                    self.control._connection.execute(statement)
                    with self.no_more_external_acts(held), self.assertRaises(ContractRefusal):
                        review_driver.review_cycles.record_verdict(self.control,
                            attachment_id=held["attachment"]["attachment_id"], disposition="accepted",
                            profile=self.profile, port=held["port"])
                    self.assertEqual(self.verdicts(held), 0)
                finally:
                    self.control._connection.execute("ROLLBACK TO damaged")
                    self.control._connection.execute("RELEASE damaged")
        self.assertEqual(held["adapter"].destroyed_with, [])

    def test_destroyed_without_a_verdict_cannot_create_one(self):
        held = self.produced()
        class BeforeVerdict(Exception):
            pass
        with mock.patch.object(review_driver.review_cycles, "record_verdict", side_effect=BeforeVerdict):
            with self.assertRaises(BeforeVerdict):
                self.end(held)
        self.control._connection.execute("UPDATE attempts SET execution_runtime = 'destroyed', cleanup = 'retained' WHERE runtime_attempt_id = 'public-review'")
        with self.no_more_external_acts(held):
            replay = self.end(held)
            self.assertEqual(replay["outcome"], "held")
            self.assertFalse(replay["cleaned_up"])
            self.assertIsNone(review_driver.review_cycles.integration_checkpoint(self.control, self.line["line_id"]))
        self.assertEqual(self.verdicts(held), 0)
        self.assertEqual(held["adapter"].destroyed_with, [])

    def test_historical_eligibility_and_replay_require_the_complete_committed_history(self):
        held = self.produced()
        ended = self.end(held)
        self.assertEqual(ended["outcome"], "accepted")
        fence_operation = "attempt.finalize-quiescent:" + digest({
            "attempt_id": held["attempt_id"], "assignment": held["terminal"]["assignment_ref"]}).split(":", 1)[1]
        damage = self.custody_damage() + (
            ("missing cleanup act", "DELETE FROM operations WHERE kind = 'runtime.destroy'"),
            ("wrong cleanup kind", "UPDATE operations SET kind = 'foreign.destroy' WHERE kind = 'runtime.destroy'"),
            ("cleanup still pending", "UPDATE attempts SET cleanup = 'pending' WHERE runtime_attempt_id = 'public-review'"),
            ("attachment not ended", "UPDATE review_attachments SET state = 'active', ended_at = NULL WHERE runtime_attempt_id = 'public-review'"),
            ("different runtime", "UPDATE attempts SET runtime_id = 'foreign-runtime' WHERE runtime_attempt_id = 'public-review'"),
            ("missing frozen result", "DELETE FROM outputs WHERE runtime_attempt_id = 'public-review'"),
            ("uncommitted verdict", "DELETE FROM operations WHERE kind = 'review-line.verdict'"),
            ("missing committed fence", "DELETE FROM operations WHERE operation_id = '" + fence_operation + "'"))
        for name, statement in damage:
            with self.subTest(evidence=name):
                self.control._connection.execute("SAVEPOINT damaged")
                try:
                    self.control._connection.execute(statement)
                    with self.no_more_external_acts(held):
                        with self.assertRaises(ContractRefusal):
                            review_driver.review_cycles.integration_checkpoint(self.control, ended["line_id"])
                        replay = self.end(held)
                        self.assertEqual(replay["outcome"], "held")
                        self.assertFalse(replay["cleaned_up"])
                finally:
                    self.control._connection.execute("ROLLBACK TO damaged")
                    self.control._connection.execute("RELEASE damaged")
        self.assertEqual(self.verdicts(held), 1)
        self.assertEqual(len(held["adapter"].destroyed_with), 1)

    def test_replay_refuses_changed_completion_disposition_and_retention_operands(self):
        held = self.produced()
        ended = self.end(held)
        operands = {"attachment_id": held["attachment"]["attachment_id"], "disposition": "completed",
            "terminal": held["terminal"], "profile": self.profile, "retention_disposition": "retain",
            "retention_policy_digest": "sha256:" + "9" * 64}
        for changed in ({"disposition": "unable"}, {"terminal": dict(held["terminal"], manifest_digest="sha256:foreign")},
                        {"retention_disposition": "discard-after-intake"}, {"retention_policy_digest": "sha256:foreign"}):
            with self.subTest(changed=changed), self.no_more_external_acts(held):
                replay = review_driver.end_review_from_result(self.control, held["port"], held["adapter"], **dict(operands, **changed))
                self.assertEqual(replay["outcome"], "held")
                self.assertFalse(replay["cleaned_up"])
        self.assertEqual(self.end(held), ended)

    def test_unresolved_provider_cleanup_stays_held_after_positive_runtime_absence(self):
        from baton_v12.worker_manager.attempts import attempt_runtime_of
        held = self.produced()
        held["adapter"].destroyed = {"state": "absent", "why": "runtime gone",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "unresolved", "why": "launch teardown remains unresolved"}}
        ended = self.end(held)
        self.assertEqual(ended["outcome"], "held")
        self.assertFalse(ended["cleaned_up"])
        self.assertEqual(self.verdicts(held), 1)
        state = attempt_runtime_of(self.control, held["attempt_id"])
        self.assertEqual((state["execution_runtime"], state["cleanup"]), ("destroyed", "pending"))
        with self.no_more_external_acts(held):
            with self.assertRaises(ContractRefusal):
                review_driver.review_cycles.integration_checkpoint(self.control, ended["line_id"])
            replay = self.end(held)
            self.assertEqual(replay["outcome"], "held")
            self.assertFalse(replay["cleaned_up"])
        self.assertEqual(len(held["adapter"].destroyed_with), 1)

    def test_cleanup_journal_must_record_positive_absence_and_exact_retained_evidence(self):
        held = self.produced()
        ended = self.end(held)
        operation_id = held["adapter"].destroyed_with[0]["operation"]["operation_id"]
        record = self.control.operation_record(operation_id)
        original = json.loads(record["result"])
        for changed in ({"state": "uncertain"}, {"state": "running"}, {"cleanup": "failed"},
                        {"attempt_id": "foreign-review"}, {"kept": []}, {"directory_custody": None},
                        {"operation": dict(original["operation"], signature_digest="sha256:foreign")}):
            with self.subTest(changed=changed):
                self.control._connection.execute("SAVEPOINT damaged")
                try:
                    self.control._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                        (json.dumps(dict(original, **changed)), operation_id))
                    with self.no_more_external_acts(held):
                        with self.assertRaises(ContractRefusal):
                            review_driver.review_cycles.integration_checkpoint(self.control, ended["line_id"])
                        replay = self.end(held)
                        self.assertEqual(replay["outcome"], "held")
                        self.assertFalse(replay["cleaned_up"])
                finally:
                    self.control._connection.execute("ROLLBACK TO damaged")
                    self.control._connection.execute("RELEASE damaged")

    def test_historical_cleanup_requires_both_exact_nested_directory_receipts(self):
        held = self.produced()
        ended = self.end(held)
        operation_id = held["adapter"].destroyed_with[0]["operation"]["operation_id"]
        original = json.loads(self.control.operation_record(operation_id)["result"])
        nested = original["directory_custody"]
        values = [None, {}, "not-a-receipt", [], dict(nested, extra=nested["result"])]
        for which in ("result", "workspace"):
            values.append({key: value for key, value in nested.items() if key != which})
            for wrong in (None, {}, "not-a-receipt", nested["workspace" if which == "result" else "result"]):
                values.append(dict(nested, **{which: wrong}))
            for member, wrong in (("attempt_id", "another-attempt"), ("root", "another-root"),
                                  ("verb", "discard"), ("operation", "inspect"), ("account", "{}")):
                values.append(dict(nested, **{which: dict(nested[which], **{member: wrong})}))
        for value in values:
            with self.subTest(directory_custody=value):
                self.control._connection.execute("SAVEPOINT damaged")
                try:
                    self.control._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                        (json.dumps(dict(original, directory_custody=value)), operation_id))
                    with self.no_more_external_acts(held), mock.patch.object(held["adapter"], "normalize_directory", side_effect=AssertionError("no repeated normalization")):
                        with self.assertRaises(ContractRefusal):
                            review_driver.review_cycles.integration_checkpoint(self.control, ended["line_id"])
                        replay = self.end(held)
                        self.assertEqual(replay["outcome"], "held")
                        self.assertFalse(replay["cleaned_up"])
                finally:
                    self.control._connection.execute("ROLLBACK TO damaged")
                    self.control._connection.execute("RELEASE damaged")
        self.assert_historical_replay(held, ended)

    def test_historical_cleanup_requires_the_underlying_directory_normalization_journals(self):
        from baton_v12.worker_manager import custody
        held = self.produced()
        ended = self.end(held)
        for which in ("result", "workspace"):
            operation_id = custody._custody_operation_id(held["attempt_id"], which)
            recorded = self.control.operation_record(operation_id)
            signature = json.loads(recorded["signature"])
            receipt = json.loads(recorded["result"])
            changes = [("operation_id", "foreign-operation"), ("kind", "runtime.destroy"), ("result", "null"),
                       ("result", json.dumps(dict(receipt, attempt_id="another-attempt"))),
                       ("result", json.dumps(dict(receipt, account="{}")))]
            for member, wrong in (("attempt_id", "foreign-attempt"), ("root", "another-root"),
                                  ("workspace_store", "/a/foreign/store"), ("verb", "discard")):
                changes.append(("signature", json.dumps(dict(signature, operands=dict(signature["operands"], **{member: wrong})), sort_keys=True, separators=(",", ":"))))
            for column, value in changes:
                with self.subTest(root=which, column=column, value=value):
                    self.control._connection.execute("SAVEPOINT damaged")
                    try:
                        self.control._connection.execute(f"UPDATE operations SET {column} = ? WHERE operation_id = ?", (value, operation_id))
                        with self.no_more_external_acts(held), mock.patch.object(held["adapter"], "normalize_directory", side_effect=AssertionError("no repeated normalization")):
                            with self.assertRaises(ContractRefusal):
                                review_driver.review_cycles.integration_checkpoint(self.control, ended["line_id"])
                            replay = self.end(held)
                            self.assertEqual(replay["outcome"], "held")
                            self.assertFalse(replay["cleaned_up"])
                    finally:
                        self.control._connection.execute("ROLLBACK TO damaged")
                        self.control._connection.execute("RELEASE damaged")
        self.assert_historical_replay(held, ended)


# -- W119733: the implementation ending, re-entered after its own cleanup -----
#
# `work/records/2026/09/finding-v12-composed-ending-recovery/`.
#
# WHAT THESE ADD AND WHAT THEY DELIBERATELY DO NOT. `end_implementation`
# promised that "a process death between any two steps re-enters here and
# finishes", and after step nine that promise was false: `_quiesced` wants a
# positively quiescent runtime and there is none, and `_own_writer` wants a
# writer the ending's own checkpoint has already revoked. The branch this Work
# adds is what these cases measure -- which evidence it requires, that it
# performs no external act at all, and that it answers with the ordinary
# ending's own document.
#
# THE RETAINED READERS ARE FAKED AND THE CUSTODY PROVIDER IS NOT, which is
# `_endings`' boundary applied to the resume. `frozen_output_of`,
# `intake_receipt_of` and `retentions_of` cross-bind against committed intake
# and retention operations that need a real adapter, a delivered workspace and
# a custody root -- a deployment's half, driven in `tests/manager`. The line,
# its writer, its real frozen checkpoint and the cleanup axis are all real
# here, because those are the facts this branch reads and reasons about.

POLICY = "sha256:" + "9" * 64
PROPOSAL = {"proposal_id": "proposal-1", "result_id": "result-1"}


class _NoRuntime:
    """The adapter surface, where every verb is a failed assertion.

    A resumed ending touches no runtime at all, and the honest way to say so is
    an adapter that cannot be used. `_typed` still proves the whole surface is
    callable, so a resume that reached for any of it fails by name rather than
    in a count somebody has to interpret.
    """

    custodian_image_digest = "sha256:" + "c" * 64

    def __init__(self):
        for verb in review_driver.RUNTIME_ADAPTER:
            setattr(self, verb, self._refuse(verb))

    @staticmethod
    def _refuse(verb):
        def call(*operands, **named):
            raise AssertionError(f"a resumed ending called the adapter's "
                                 f"{verb}")
        return call


class _Published:
    """The publication seam's replay half, beside a `publish` that must never
    be reached."""

    def __init__(self, answer=PROPOSAL):
        self.answer = answer
        self.asked = []

    def publish(self, **operands):
        raise AssertionError("a resumed ending published again")

    def published_of(self, *, attempt_id):
        self.asked.append(attempt_id)
        return self.answer


class TheResumeRefusesBeforeItReachesCommittedEvidence(DriverCase):
    """The narrow operand controls, kept and re-scoped.

    W120425 review 2026-09-08T15-46-16Z: these fixtures mock the retained
    readers and set the cleanup axes by hand, so they can prove which operands
    a resume refuses and that it spends nothing doing so -- and they CANNOT
    prove that a real ending left the evidence a resume reads. Every case here
    now refuses at or before the retained-evidence read, which is what this
    fixture can honestly reach; the positive lifecycle, the committed cleanup,
    the checkpoint replay and the publication history are proved against real
    component custody in `TheImplementationResumeReadsRealCommittedCustody`.
    """

    RESULT = {"result_id": "result-writer-attempt-1",
              "disposition": "completed",
              "manifest_digest": "sha256:" + "4" * 64}
    RECEIPT = {"receipt_digest": "sha256:" + "5" * 64,
               "artifacts": [{"artifact_id": "artifact-b"},
                             {"artifact_id": "artifact-a"}]}
    RETAINED = ({"artifact_id": "artifact-a", "disposition": "retain",
                 "retention_policy_digest": POLICY},
                {"artifact_id": "artifact-b", "disposition": "retain",
                 "retention_policy_digest": POLICY})

    def setUp(self):
        super().setUp()
        self.attempt_id = self.attempt("writer-attempt-1", 1, WRITER,
                                       "writer-principal-1")
        self.writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=self.attempt_id, generation=1,
            worker_id="impl-worker-1", profile=self.profile)
        self.completed(self.attempt_id)
        self.checkpoint = None
        self.publication = _Published()

    def frozen(self):
        """The real checkpoint the ordinary ending's step eight commits."""
        from baton_v12.worker_manager import freeze_checkpoint
        self.checkpoint = freeze_checkpoint(
            self.control, writer_id=self.writer["writer_id"], generation=1,
            profile=self.profile, port=self.port(WRITER))
        return self.checkpoint

    def destroyed(self, cleanup="retained", runtime="destroyed"):
        """The exact axes `authorize_cleanup` leaves behind, and no more."""
        self.control._connection.execute(
            "UPDATE attempts SET execution_runtime = ?, cleanup = ? "
            "WHERE runtime_attempt_id = ?",
            (runtime, cleanup, self.attempt_id))

    def gone(self, **changed):
        """A whole ordinary ending's durable aftermath: frozen, then cleaned."""
        self.frozen()
        self.destroyed(**changed)

    @contextlib.contextmanager
    def retained(self, *, frozen=None, receipt=None, decisions=None):
        """The three retained readers, answering what a finished ending left."""
        held = {
            "frozen_output_of": self.RESULT if frozen is None else frozen,
            "intake_receipt_of": self.RECEIPT if receipt is None else receipt,
            "retentions_of": (self.RETAINED if decisions is None
                              else decisions)}
        with contextlib.ExitStack() as stack:
            for name, answer in held.items():
                stack.enter_context(mock.patch.object(
                    review_driver, name,
                    lambda *operands, _answer=answer, **named: _answer))
            yield

    def resume(self, **changed):
        operands = {"attempt_id": self.attempt_id, "disposition": "completed",
                    "terminal": None, "writer_id": self.writer["writer_id"],
                    "generation": 1, "profile": self.profile,
                    "retention_disposition": "retain",
                    "retention_policy_digest": POLICY, "proposal": {}}
        operands.update(changed)
        return review_driver.end_implementation(
            self.control, self.port(WRITER), _NoRuntime(), self.publication,
            **operands)

    @contextlib.contextmanager
    def no_external_act(self):
        """Nothing may reach the Authority or change this store."""
        calls = list(self.port(WRITER).calls)
        changes = self.control._connection.total_changes
        yield
        self.assertEqual(self.port(WRITER).calls, calls)
        self.assertEqual(self.control._connection.total_changes, changes)

    # -- what it answers -----------------------------------------------------

    def test_a_live_runtime_still_gets_the_ordinary_ending(self):
        """The branch is chosen from durable state and never from an operand.

        A caller cannot ask for a resume, so an attempt whose runtime is still
        there reaches the ordinary ending -- which is what an adapter that
        cannot be used proves, because a resume never calls one.
        """
        with self.retained(), self.assertRaises(AssertionError) as raised:
            self.resume()
        self.assertIn("adapter's stop", str(raised.exception))

    def test_an_unsettled_cleanup_is_not_a_runtime_this_manager_let_go(self):
        """`destroyed` is eligibility; the cleanup axis is the evidence.

        `failed` is the settled ending of a cleanup whose runtime survived its
        own destroy, and the other two are endings that did not finish. None
        of them is a manager that got as far as authorizing cleanup, so none
        may be answered with the evidence of one that did.
        """
        self.frozen()
        for cleanup in ("pending", "blocked-on-intake", "failed"):
            with self.subTest(cleanup=cleanup):
                self.destroyed(cleanup=cleanup)
                with self.retained(), self.no_external_act():
                    caught = self.refusal(self.resume)
                self.assertIn("positively let go", caught.message)

    def test_an_active_writer_beside_a_destroyed_runtime_refuses(self):
        """Two facts that cannot both be true.

        The ordinary ending revokes this writer when it freezes the
        checkpoint, so an active one says the ending stopped before that --
        and answering it with retained evidence would report a lifecycle
        nobody performed.
        """
        self.destroyed()
        with self.retained(), self.no_external_act():
            caught = self.refusal(self.resume)
        self.assertIn("still holds writer", caught.message)

    def test_a_writer_belonging_to_another_attempt_or_generation_refuses(self):
        self.gone()
        self.attempt("writer-attempt-2", 2, WRITER, "writer-principal-2")
        for changed in ({"attempt_id": "writer-attempt-2"},
                        {"generation": 2}):
            with self.subTest(changed=changed):
                with self.retained(), self.no_external_act():
                    caught = self.refusal(self.resume, **changed)
                self.assertIn("one ending answers for one attempt",
                              caught.message)

    def test_a_session_acting_for_somebody_else_refuses(self):
        self.gone()
        with self.retained(), self.no_external_act():
            caught = self.refusal(
                review_driver.end_implementation, self.control,
                self.port(REVIEWER), _NoRuntime(), self.publication,
                attempt_id=self.attempt_id, disposition="completed",
                terminal=None, writer_id=self.writer["writer_id"],
                generation=1, profile=self.profile,
                retention_disposition="retain",
                retention_policy_digest=POLICY, proposal={})
        self.assertEqual(caught.code, "capability")

    # -- the evidence it requires --------------------------------------------

    def test_missing_retained_evidence_refuses_with_the_evidence_named(self):
        self.gone()
        for changed, expected in (({"frozen": {}},
                                   "no retained frozen result"),
                                  ({"receipt": {}},
                                   "no accepted intake receipt"),
                                  ({"decisions": ()},
                                   "different retention operands")):
            with self.subTest(missing=sorted(changed)):
                with self.retained(**changed), self.no_external_act():
                    caught = self.refusal(self.resume)
                self.assertIn(expected, caught.message)

    def test_changed_operands_are_not_this_endings_evidence(self):
        self.gone()
        for changed, expected in (
                ({"disposition": "unable"}, "and this ending names"),
                ({"retention_disposition": "discard-after-intake"},
                 "different retention operands"),
                ({"retention_policy_digest": "sha256:" + "7" * 64},
                 "different retention operands")):
            with self.subTest(changed=changed):
                with self.retained(), self.no_external_act():
                    caught = self.refusal(self.resume, **changed)
                self.assertIn(expected, caught.message)

    def test_a_partly_retained_result_set_refuses(self):
        self.gone()
        with self.retained(decisions=(self.RETAINED[0],
                                      dict(self.RETAINED[1],
                                           retention_policy_digest="sha256:"
                                           + "7" * 64))), \
                self.no_external_act():
            caught = self.refusal(self.resume)
        self.assertIn("different retention operands", caught.message)

    def test_a_terminal_naming_another_envelope_refuses(self):
        """`_correlated` is still what decides it, on the retained result.

        Persisting or replaying a worker's claimed terminal never promotes it
        to proof: the resume compares it against the envelope this manager
        validated, exactly as the live ending does.
        """
        self.gone()
        with self.retained(), self.no_external_act():
            caught = self.refusal(
                self.resume,
                terminal={"manifest_digest": "sha256:" + "8" * 64})
        self.assertEqual(caught.code, "operation-collision")

    def test_the_ordinary_seam_contract_is_unchanged(self):
        """An ordinary ending needed one verb and still needs exactly one.

        The replay half is typed inside the resumed branch, so a deployment
        that only ever ends live attempts is unaffected by this Work -- which
        is what keeps every existing ending and every case that drives one
        meaning what it meant.
        """
        self.assertEqual(review_driver.PUBLICATION_SEAM, ("publish",))
        self.assertNotIn("published_of", review_driver.PUBLICATION_SEAM)


class TheTwoResumesShareOneEvidenceContract(DriverCase):
    """W119733: the review resume's custody reads are the implementation
    resume's, and moving them into one body changed neither.

    THE CORRELATION IS THE ADDITIVE HALF. A resumed ending compares the
    retained frozen result's own disposition against the one it was handed, so
    a caller re-entering with a different ending is refused by the evidence
    rather than carried into a verdict read. On the review side that refusal
    is EVIDENCE, so it lands as `held` with nothing advanced and nothing
    cleaned up -- which is `_ended_review`'s pinned contract and is unchanged.
    """

    def historical_review(self):
        writer_attempt = self.attempt("writer-attempt-1", 1, WRITER,
                                      "writer-principal-1")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=1,
            worker_id="impl-worker-1", profile=self.profile)
        self.completed(writer_attempt)
        from baton_v12.worker_manager import freeze_checkpoint
        checkpoint = freeze_checkpoint(
            self.control, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.port(WRITER))
        review_attempt = self.attempt("review-attempt-1", 1, REVIEWER,
                                      "review-principal-1")
        attached = review_driver.prepare_review(
            self.control, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=review_attempt, generation=1,
            reviewer_worker_id="review-worker-1", profile=self.profile)
        self.completed(review_attempt, review=True)
        self.control._connection.execute(
            "UPDATE attempts SET execution_runtime = 'destroyed', "
            "cleanup = 'retained' WHERE runtime_attempt_id = ?",
            (review_attempt,))
        return attached

    def ended(self, attachment_id, **changed):
        operands = {"attachment_id": attachment_id, "disposition": "completed",
                    "terminal": {"manifest_digest": "sha256:" + "1" * 64},
                    "profile": self.profile,
                    "retention_disposition": "retain",
                    "retention_policy_digest": POLICY}
        operands.update(changed)
        return review_driver.end_review_from_result(
            self.control, self.port(REVIEWER), _NoRuntime(), **operands)

    def test_a_retained_result_that_ended_otherwise_is_held_not_resolved(self):
        attached = self.historical_review()
        resolved = []
        with mock.patch.object(
                review_driver, "frozen_output_of",
                lambda *a, **k: {"result_id": "result-review-attempt-1",
                                 "disposition": "unable",
                                 "manifest_digest": "sha256:" + "1" * 64}), \
                mock.patch.object(
                    review_driver, "review_verdict_from_result",
                    lambda *a, **k: resolved.append("resolved")):
            answered = self.ended(attached["attachment_id"])
        self.assertEqual(answered["outcome"], "held")
        self.assertIsNone(answered["verdict"])
        self.assertFalse(answered["cleaned_up"])
        self.assertIn("and this ending names", answered["held_reason"])
        # AND THE VERDICT READ IS NEVER REACHED. A reviewer that did not
        # complete has not decided anything, and the evidence says so before
        # anything goes looking for a decision.
        self.assertEqual(resolved, [])

    def test_a_review_that_did_not_complete_keeps_its_own_refusal(self):
        """The review's own rule, and it stays in the review branch.

        `completed` is what a review ending requires of its attempt; it is not
        something every ending owes, so the shared reader does not assert it
        and this path still does.
        """
        attached = self.historical_review()
        answered = self.ended(attached["attachment_id"], disposition="unable")
        self.assertEqual(answered["outcome"], "held")
        self.assertIn("completed disposition", answered["held_reason"])
        self.assertFalse(answered["cleaned_up"])


# -- W120425: the resume, over custody an actual ending really committed ------
#
# `work/records/2026/09/finding-v12-composed-ending-recovery/findings/
# finding-historical-implementation-proof/`.
#
# WHY THE FIXTURE ABOVE IS NOT ENOUGH, in the reviewer's words: it "uses raw
# axes for cleanup and mocks frozen-output, intake-receipt and retention
# readers", so what it proves is which operands a resume refuses -- not that a
# real ending leaves the evidence a resume reads, and not that the resume can
# find it again in a process that did not perform it.
#
# WHAT IS REAL HERE. The line, the writer grant, the worker's own completion
# envelope, the freeze, the terminal correlation, the intake receipt, the
# retention decisions, the committed `runtime.destroy` with its directory
# custody, the frozen checkpoint, and the retained proposal manifest are all
# produced by the ACTUAL ordinary `end_implementation` over real files and the
# accepted public operations. The store is then CLOSED and REOPENED, so the
# resume runs in a handle that performed none of it.
#
# WHAT IS STILL A STAND-IN, named rather than implied. The engine and the
# Authority transports are deterministic, as they are everywhere in this
# suite. The proposal manifest is COMPOSED by this fixture rather than by
# `integration.driver.retain_proposal`: composing one is that producer's own
# accepted contract, proved in `tests/integration/test_driver.py`, and it
# requires a proposal-typed declared output this writer does not declare. What
# is under test here is the driver's CORRELATION of a retained proposal
# manifest, and that manifest is retained through the accepted public
# `retain_manifest` and re-read through the accepted public `load_manifest`.

from tests.manager.test_output import POLICY as _CUSTODY_POLICY
from tests.integration.test_driver import LinePublisher
from baton_v12.integration import driver as integration_driver

PROPOSAL_SCHEMA = "baton.worker-manifest/proposal"

# The revision this fixture's Authority holds and the one its worker claims to
# have produced. `retain_proposal` requires the worker's declared base to BE
# the Authority's canonical target, which is the ordinary rule rather than a
# fixture convenience.
PROPOSAL_BASE = "a1" * 20
PROPOSAL_HEAD = "b2" * 20
PROPOSAL_TRANSPORT = "change.bundle"


class _ImplementationCustodian(_ReviewFileCustodian):
    """The review fixture's real file custodian, for an implementation line."""

    def prove_line_consumable(self, store, **operands):
        self.consumed = getattr(self, "consumed", [])
        self.consumed.append(dict(operands))
        return {"line_id": "line-under-proof"}


class _RealPublication:
    """The publication seam, over the ACTUAL integration owner.

    W120425 review 2026-09-08T16-18-42Z [P1]: the previous stand-in composed
    its own proposal manifest and retained it, so its "published" evidence was
    a retained proposal and its positive proof could not tell retained-but-
    unpublished from published. This calls `retain_proposal` and
    `publish_candidate` for real -- so the Authority is asked, its answer is
    verified, its readback is compared, and W120763's local record is
    committed -- and `published_of` reads that record through
    `integration.publication_of` with no publisher at all.

    THE CONTRACT W119114 HAS TO IMPLEMENT, written as the smallest thing that
    satisfies it. `published_of` keeps no cache: the selector is re-derived
    from the same durable proposal every time, so the same object answers
    identically in a process that never published.
    """

    def __init__(self, case, publisher):
        self.case = case
        self.publisher = publisher
        self.published = []
        self.retained = {}

    def _selector(self, attempt_id):
        """WHICH retained proposal this attempt's publication is about.

        A SELECTOR AND NOT THE EVIDENCE. What proves a publication happened is
        the record `publication_of` reads; this only says which proposal to
        ask about, and it is re-derivable from durable state --
        `retain_proposal` is replay-safe by construction, so an attempt whose
        result is frozen answers the same digest in any process.

        THE ANSWER IS KEPT ONLY TO AVOID WRITING ON A READ. Re-deriving it
        opens a write transaction to re-retain identical bytes, and a resume
        may not write; a control below empties this and proves the durable
        derivation still answers in a reopened process.
        """
        held = self.retained.get(attempt_id)
        if held is None:
            held = integration_driver.retain_proposal(
                self.case.control, self.publisher, attempt_id=attempt_id)
            self.retained[attempt_id] = held
        return held

    def publish(self, *, attempt_id, result_id, manifest_digest, artifacts,
                proposal):
        held = self._selector(attempt_id)
        answered = integration_driver.publish_candidate(
            self.case.control, self.publisher, attempt_id=attempt_id,
            proposal_manifest_digest=held)
        self.published.append(attempt_id)
        return answered

    def published_of(self, *, attempt_id):
        """The durable half, and it asks the owner rather than remembering."""
        return integration_driver.publication_of(
            self.case.control, attempt_id=attempt_id,
            proposal_manifest_digest=self._selector(attempt_id))


class TheImplementationResumeReadsRealCommittedCustody(ReviewResultCase):
    """One real implementation ending, reopened, and resumed from its records."""

    line_base = TheWorkerCompletionTraversesPublicCustody.line_base
    repository = TheWorkerCompletionTraversesPublicCustody.repository
    write = staticmethod(TheWorkerCompletionTraversesPublicCustody.write)
    # W120425: AND A PROPOSAL OUTPUT, because a real publication is composed
    # from one. `retain_proposal` selects the single present proposal-typed
    # output of the frozen result and reads the worker's own four-member claim
    # out of it; a fixture that declared none could only ever manufacture that
    # producer's evidence.
    DECLARED = copy.deepcopy(
        TheWorkerCompletionTraversesPublicCustody.DECLARED) + [
        dict(copy.deepcopy(
            TheWorkerCompletionTraversesPublicCustody.DECLARED[0]),
            name="proposal", path="proposal",
            type=integration_driver.PROPOSAL_OUTPUT)]

    ATTEMPT = "public-implementation"
    POLICY = "sha256:" + "9" * 64

    def setUp(self):
        super().setUp()
        import sys
        worker = pathlib.Path(__file__).resolve().parents[3] / "worker"
        for place in (worker, worker.parent / "python/src/baton_v12"):
            if str(place) not in sys.path:
                sys.path.insert(0, str(place))
        global baton_worker
        import baton_worker
        self.store = self.control
        self.publisher = LinePublisher(PROPOSAL_BASE)
        self.publication = _RealPublication(self, self.publisher)

    # -- the plumbing, kept beside the proof it serves ------------------------

    def registered(self, attempt_id, participant, principal):
        """One activated attempt over the real offer/claim/activation owners.

        The same shape `TheWorkerCompletionTraversesPublicCustody.registered`
        composes, written here rather than inherited because inheriting that
        class would re-run its model turn for every case below.
        """
        from baton_v12.worker_manager import (AuthorityPort, accept_offer,
            activate_assignment, issue_offer, record_attempt, retain_manifest,
            submit_claim)
        from tests.manager.test_offers import (SCOPE, decision,
                                               fake_claim_signature)
        from tests.manager.test_output import OutputCase, sealed
        from tests.manager.test_attempts import ADAPTER
        declaration = sealed(dict(
            OutputCase.published(),
            work_ref={"authority_uuid": self.AUTHORITY, "work_id": WORK_A},
            outputs=copy.deepcopy(self.DECLARED),
            runtime_profile_digest=PROFILE, policy_digest=_CUSTODY_POLICY))
        input_digest = retain_manifest(self.control, declaration,
                                       "inputManifest")["digest"]
        session = _EndingAuthority(participant=participant, work={
            "status": "open", "phase": "queued", "handler": None,
            "gate": None, "authority_uuid": self.AUTHORITY, "scope": SCOPE,
            "route": "review"})
        assignment = {"work_ref": {"authority_uuid": self.AUTHORITY,
                                   "work_id": WORK_A},
                      "participant": participant, "generation": 1}
        session.claim_answer = {"assignment": assignment, "claim_event": 1,
            "decision": decision(participant=participant, principal=principal,
                                 role="review")}
        session.live_assignment = dict(assignment)
        session.fence_answer = {"cause": "cancelled",
                                "assignment": dict(assignment),
                                "phase": "block",
                                "gate": "runtime-quiescence:1", "fenced": True}
        port = AuthorityPort(session, fake_claim_signature)
        offer_id = "offer-" + attempt_id
        issue_offer(self.control, port, offer_id=offer_id, work_id=WORK_A,
                    runtime_attempt_id=attempt_id, input_digest=input_digest,
                    policy_digest=_CUSTODY_POLICY, profile_digest=PROFILE,
                    profile_name="reference",
                    mint_bearer=lambda: "fixture-offer-bearer")
        accept_offer(self.control, port, offer_id=offer_id, decision="accept",
                     bearer="fixture-offer-bearer", now=NOW,
                     runtime_attempt_id=attempt_id,
                     work_ref=assignment["work_ref"])
        record_attempt(self.control, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       input_digest=input_digest,
                       policy_digest=_CUSTODY_POLICY)
        submit_claim(self.control, port, offer_id=offer_id)
        activate_assignment(self.control, port, attempt_id=attempt_id,
                            expect=assignment)
        roots = assignment_workspace(self.group, self.storage, attempt_id)
        adapter = _ImplementationCustodian("runtime-" + attempt_id, roots,
                                           declaration, _CUSTODY_POLICY)
        return port, adapter, assignment

    def started(self, attempt_id, adapter, assignment):
        from baton_v12.worker_manager import (reconcile_runtime,
                                              request_runtime_start)
        inputs, _ = input_roots.composed(
            self, self.storage, work_ref=assignment["work_ref"],
            participant=assignment["participant"], generation=1,
            runtime_attempt_id=attempt_id, given=adapter.declaration)
        request_runtime_start(self.control, adapter, attempt_id=attempt_id,
                              inputs=inputs)
        reconcile_runtime(self.control, adapter, attempt_id=attempt_id)

    # -- the ordinary ending, actually performed -----------------------------

    def implemented(self):
        """One real implementation attempt, ended through the real driver."""
        port, adapter, assignment = self.registered(
            self.ATTEMPT, WRITER, "public-implementation-principal")
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=self.ATTEMPT, generation=1,
            worker_id="public-implementation-worker", profile=self.profile)
        self.started(self.ATTEMPT, adapter, assignment)
        claim = {"base": PROPOSAL_BASE, "head": PROPOSAL_HEAD,
                 "transport": PROPOSAL_TRANSPORT, "recap": "implemented"}
        with mock.patch.object(baton_worker, "OUTPUT_ROOT",
                               adapter.roots["workspace"]):
            for declaration in self.DECLARED:
                # THE TRANSPORT IS A FILE THE MANAGER MEASURES. `_claim_of`
                # refuses a locator the content manifest did not weigh, so the
                # worker writes its objects where it says they are.
                name = (PROPOSAL_TRANSPORT if declaration["name"] == "proposal"
                        else "produced.txt")
                self.write(os.path.join(adapter.roots["workspace"],
                                        declaration["path"], name),
                           "implementation output\n")
            outputs = baton_worker.answered(
                self.DECLARED,
                [{"name": declaration["name"], "status": "present",
                  "result_metadata": (
                      {integration_driver.CLAIM_NAMESPACE: dict(claim)}
                      if declaration["name"] == "proposal" else {})}
                 for declaration in self.DECLARED])
            terminal = baton_worker.publish_completion(assignment, "completed",
                                                       outputs)
        ended = review_driver.end_implementation(
            self.control, port, adapter, self.publication,
            attempt_id=self.ATTEMPT, disposition="completed",
            terminal=terminal, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, retention_disposition="retain",
            retention_policy_digest=self.POLICY, proposal=None)
        return {"port": port, "adapter": adapter, "writer": writer,
                "terminal": terminal, "ended": ended}

    def reopened(self):
        """A control store handle that performed none of the ending above."""
        from baton_v12.worker_manager import ControlStore
        place = os.path.join(self.root, "control.sqlite3")
        self.control.close()
        self.control = ControlStore.open(place, incarnation="manager-2",
                                         clock=self.clock)
        self.addCleanup(self.control.close)
        return self.control

    def resume(self, held, **changed):
        operands = {"attempt_id": self.ATTEMPT, "disposition": "completed",
                    "terminal": held["terminal"],
                    "writer_id": held["writer"]["writer_id"], "generation": 1,
                    "profile": self.profile,
                    "retention_disposition": "retain",
                    "retention_policy_digest": self.POLICY, "proposal": None}
        operands.update(changed)
        return review_driver.end_implementation(
            self.control, held["port"], _NoRuntime(), self.publication,
            **operands)

    @contextlib.contextmanager
    def no_runtime_or_write(self, held, *, authority=True):
        """No runtime, no worker, no publication, and no control write.

        `authority=False` is used by exactly one case, which documents the one
        residual this Work could not close from its two owned paths: see
        `test_a_cleanup_axis_without_its_committed_destroy_refuses`.
        """
        calls = copy.deepcopy(held["port"]._session.calls)
        changes = self.control._connection.total_changes
        published = list(self.publication.published)
        with contextlib.ExitStack() as stack:
            for verb in ("stop", "seal", "collect", "retain", "destroy",
                         "normalize_directory", "prove_line_consumable"):
                stack.enter_context(mock.patch.object(
                    held["adapter"], verb,
                    side_effect=AssertionError(
                        f"a resumed ending called the adapter's {verb}")))
            stack.enter_context(mock.patch.object(
                self.publication, "publish",
                side_effect=AssertionError("a resumed ending published")))
            yield
        if authority:
            self.assertEqual(held["port"]._session.calls, calls)
        self.assertEqual(self.control._connection.total_changes, changes)
        self.assertEqual(self.publication.published, published)

    @contextlib.contextmanager
    def no_external_act(self, held):
        """No runtime, no worker, no Authority, and no control write."""
        with self.no_runtime_or_write(held):
            yield

    # -- the positive proof --------------------------------------------------

    def test_the_ordinary_ending_leaves_every_record_a_resume_reads(self):
        """The precondition, measured at each owner rather than assumed."""
        from baton_v12.worker_manager import (attempt_runtime_of,
            frozen_output_of, intake_receipt_of, load_manifest, retentions_of)
        held = self.implemented()
        frozen = frozen_output_of(self.control, self.ATTEMPT)
        receipt = intake_receipt_of(self.control, self.ATTEMPT)
        retained = retentions_of(self.control, self.ATTEMPT)
        runtime = attempt_runtime_of(self.control, self.ATTEMPT)
        self.assertEqual(frozen["disposition"], "completed")
        self.assertEqual(receipt["custody"], "accepted")
        self.assertTrue(retained)
        self.assertTrue(all(one["disposition"] == "retain"
                            and one["retention_policy_digest"] == self.POLICY
                            for one in retained))
        self.assertEqual((runtime["execution_runtime"], runtime["cleanup"]),
                         ("destroyed", "retained"))
        self.assertEqual(len(held["adapter"].destroyed_with), 1)
        # THE COMMITTED ACT, not the axis: the destroy is a journalled
        # operation and this is the one the resume replays.
        self.assertEqual(self.control._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = 'runtime.destroy' "
            "AND state = 'committed'").fetchone()[0], 1)
        # THE PUBLICATION IS REAL AND ITS LOCAL RECORD IS COMMITTED. The
        # ordinary ending answers with the Authority's own recorded proposal;
        # what a resume reads is the record `publish_candidate` committed
        # after that answer was verified.
        self.assertEqual(held["ended"]["published"]["candidate_digest"],
                         PROPOSAL_HEAD)
        self.assertEqual(self.publication.published, [self.ATTEMPT])
        selector = self.publication.retained[self.ATTEMPT]
        self.assertIsNotNone(review_driver.load_manifest(
            self.control, selector, "proposalManifest"))
        self.assertIsNotNone(integration_driver.publication_of(
            self.control, attempt_id=self.ATTEMPT,
            proposal_manifest_digest=selector))

    def test_a_reopened_manager_finishes_the_ending_from_those_records(self):
        held = self.implemented()
        ended = held["ended"]
        self.reopened()
        with self.no_external_act(held):
            resumed = self.resume(held)
        self.assertEqual(sorted(resumed), sorted(ended))
        for member in ("attempt_id", "disposition", "result_id",
                       "manifest_digest", "receipt_digest", "artifacts",
                       "retention", "checkpoint_id", "checkpoint"):
            self.assertEqual(resumed[member], ended[member], member)
        # THE PUBLICATION IS THE DURABLE HISTORY AND NOT THE PUBLISH ANSWER,
        # which is the one member the two paths cannot share: the ordinary
        # ending reports what the Authority answered and a resume reports the
        # retained manifest that answer was composed from.
        self.assertEqual(resumed["published"]["attempt_id"], self.ATTEMPT)
        self.assertEqual(resumed["published"]["proposal_manifest_digest"],
                         self.publication.retained[self.ATTEMPT])
        self.assertEqual(resumed["published"]["published"],
                         ended["published"])

    def test_resuming_again_answers_the_same_and_still_spends_nothing(self):
        held = self.implemented()
        self.reopened()
        with self.no_external_act(held):
            first = self.resume(held)
            self.assertEqual(self.resume(held), first)
            self.assertEqual(self.resume(held), first)

    def test_the_line_its_writer_and_its_checkpoint_are_left_alone(self):
        from baton_v12.worker_manager import checkpoint_of, writer_of
        held = self.implemented()
        self.reopened()
        before = (line_of(self.control, self.line["line_id"]),
                  writer_of(self.control, held["writer"]["writer_id"]),
                  checkpoint_of(self.control,
                                held["ended"]["checkpoint_id"]))
        with self.no_external_act(held):
            self.resume(held)
        self.assertEqual(
            (line_of(self.control, self.line["line_id"]),
             writer_of(self.control, held["writer"]["writer_id"]),
             checkpoint_of(self.control, held["ended"]["checkpoint_id"])),
            before)

    # -- the negative proof, against the same real records -------------------

    def damaged(self, held, statement, values=(), *, authority=True):
        """One committed record altered, with everything else left real."""
        self.control._connection.execute("SAVEPOINT damaged")
        try:
            self.control._connection.execute(statement, values)
            with self.no_runtime_or_write(held, authority=authority):
                return self.refusal(self.resume, held)
        finally:
            self.control._connection.execute("ROLLBACK TO damaged")
            self.control._connection.execute("RELEASE damaged")

    def test_a_cleanup_axis_without_its_committed_destroy_refuses(self):
        """The reviewer's exact reproduction, over real custody.

        The axis says the runtime is gone and the journal does not, which is
        what an edit reaches and what an ending never produces.

        AND THE RESIDUAL IS CLOSED. The previous pass measured one Authority
        read here, because it asked the SERVING `authorize_cleanup` and that
        act queries the live assignment when it finds no committed destroy to
        replay. W120762's `cleanup_of` takes no port and no adapter, so there
        is no branch left that could reach the Authority -- and
        `no_external_act` asserts the call list is unchanged rather than
        tolerating one read.
        """
        held = self.implemented()
        self.reopened()
        caught = self.damaged(held, "DELETE FROM operations WHERE kind = "
                                    "'runtime.destroy'")
        self.assertIn("no committed ordinary cleanup", caught.message)

    def test_a_cleanup_committed_for_another_runtime_refuses(self):
        held = self.implemented()
        self.reopened()
        caught = self.damaged(held, "UPDATE attempts SET runtime_id = "
                                    "'another-runtime' WHERE "
                                    "runtime_attempt_id = ?", (self.ATTEMPT,))
        self.assertIsInstance(caught, ContractRefusal)

    def test_the_cleanup_axis_no_longer_decides_anything(self):
        """The [P1] correction, stated as the property that now holds.

        The first version asked the mutable `cleanup` column and then asked a
        serving act to confirm it. `cleanup_of` derives the destroy identity
        from the intake receipt and the retention policy and answers from the
        COMMITTED act, so moving the column changes neither the answer nor
        anything the resume does with it -- and an axis edited without its
        journal cannot manufacture a resume, which
        `test_a_cleanup_axis_without_its_committed_destroy_refuses` measures
        from the other side.
        """
        held = self.implemented()
        self.reopened()
        with self.no_external_act(held):
            answered = self.resume(held)
        for cleanup in ("pending", "blocked-on-intake", "failed"):
            with self.subTest(cleanup=cleanup):
                self.control._connection.execute("SAVEPOINT moved")
                try:
                    self.control._connection.execute(
                        "UPDATE attempts SET cleanup = ? WHERE "
                        "runtime_attempt_id = ?", (cleanup, self.ATTEMPT))
                    with self.no_external_act(held):
                        self.assertEqual(self.resume(held), answered)
                finally:
                    self.control._connection.execute("ROLLBACK TO moved")
                    self.control._connection.execute("RELEASE moved")

    def test_an_incomplete_retention_refuses(self):
        held = self.implemented()
        self.reopened()
        for name, statement in (
                ("no decision at all", "DELETE FROM retentions WHERE "
                                       "runtime_attempt_id = ?"),
                ("another policy", "UPDATE retentions SET "
                                   "retention_policy_digest = 'sha256:foreign'"
                                   " WHERE runtime_attempt_id = ?")):
            with self.subTest(retention=name):
                caught = self.damaged(held, statement, (self.ATTEMPT,))
                # EITHER REFUSAL IS THE RIGHT ONE. A missing decision is this
                # driver's comparison; a decision whose policy no longer
                # matches the act that made it is the retention owner's own
                # authentication, which refuses first and says more.
                self.assertIsInstance(caught, ContractRefusal)
                self.assertTrue("retention operands" in caught.message
                                or "the journal did not" in caught.message,
                                caught.message)

    def test_a_partly_retained_result_set_refuses(self):
        """One artifact's decision removed, which the cleanup receipt names.

        The committed destroy records exactly what it KEPT, so a retention set
        that no longer matches it is a store whose two accounts disagree.
        """
        held = self.implemented()
        self.reopened()
        caught = self.damaged(
            held, "DELETE FROM retentions WHERE runtime_attempt_id = ? AND "
                  "artifact_id = (SELECT min(artifact_id) FROM retentions "
                  "WHERE runtime_attempt_id = ?)",
            (self.ATTEMPT, self.ATTEMPT))
        self.assertIsInstance(caught, ContractRefusal)

    def test_a_missing_intake_receipt_refuses(self):
        held = self.implemented()
        self.reopened()
        caught = self.damaged(held, "DELETE FROM intakes WHERE "
                                    "runtime_attempt_id = ?", (self.ATTEMPT,))
        self.assertIn("no accepted intake receipt", caught.message)

    def test_a_missing_frozen_result_refuses(self):
        held = self.implemented()
        self.reopened()
        caught = self.damaged(held, "DELETE FROM outputs WHERE "
                                    "runtime_attempt_id = ?", (self.ATTEMPT,))
        self.assertIn("no retained frozen result", caught.message)

    def test_a_foreign_terminal_envelope_refuses(self):
        held = self.implemented()
        self.reopened()
        with self.no_external_act(held):
            caught = self.refusal(
                self.resume, held,
                terminal={"manifest_digest": "sha256:" + "8" * 64})
        self.assertEqual(caught.code, "operation-collision")

    def test_the_resume_survives_the_line_moving_on(self):
        """W120425 review 2026-09-08T16-18-42Z: the required later-state proof.

        The first version required the line's CURRENT checkpoint to be this
        writer's, which is a mutable pointer that every later round moves --
        so an honest recovery of an earlier ending became impossible exactly
        when a correction had happened. `freeze_checkpoint` selects by
        `writer_id`, so the resume finds this writer's own checkpoint whatever
        the line has since done, and this drives the pointer away from it and
        asserts the answer is unchanged.

        A POSITIVE PROOF AND NOT A CORRUPTION REFUSAL. The pointer moving is
        what line movement IS to this path; the case asserts recovery still
        succeeds and still answers this ending's checkpoint.
        """
        held = self.implemented()
        self.reopened()
        with self.no_external_act(held):
            answered = self.resume(held)
        for name, statement, values in (
                ("the line has advanced past it",
                 "UPDATE review_lines SET revision = 9, "
                 "current_checkpoint_id = 'checkpoint-later' WHERE "
                 "line_id = ?", (self.line["line_id"],)),
                ("the line holds no checkpoint at all",
                 "UPDATE review_lines SET revision = 0, "
                 "current_checkpoint_id = NULL WHERE line_id = ?",
                 (self.line["line_id"],))):
            with self.subTest(moved=name):
                self.control._connection.execute("SAVEPOINT moved")
                try:
                    self.control._connection.execute(statement, values)
                    with self.no_external_act(held):
                        resumed = self.resume(held)
                    self.assertEqual(resumed, answered)
                    self.assertEqual(resumed["checkpoint_id"],
                                     held["ended"]["checkpoint_id"])
                finally:
                    self.control._connection.execute("ROLLBACK TO moved")
                    self.control._connection.execute("RELEASE moved")

    def test_a_publication_this_manager_never_committed_refuses(self):
        """The durable half, measured by taking the owner's record away.

        The retained proposal manifest stays exactly where it was, which is
        the point: a proposal was prepared and this manager holds no record
        that it was ever published, so the resume refuses instead of reading
        preparation as evidence.
        """
        held = self.implemented()
        self.reopened()
        self.assertIsNotNone(review_driver.load_manifest(
            self.control, self.publication.retained[self.ATTEMPT],
            "proposalManifest"))
        caught = self.damaged(held, "DELETE FROM operations WHERE kind = ?",
                              (integration_driver.PUBLICATION_KIND,))
        self.assertIn("no committed publication history", caught.message)

    def test_the_publication_selector_is_derivable_after_reopening(self):
        """The seam keeps no evidence, only which proposal to ask about.

        Emptying what it remembered and re-deriving it in a reopened process
        answers the same digest, so the record it then reads is reached from
        durable state rather than from anything this process carried.
        """
        held = self.implemented()
        selector = self.publication.retained[self.ATTEMPT]
        self.reopened()
        self.publication.retained.clear()
        self.assertEqual(
            self.publication.published_of(
                attempt_id=self.ATTEMPT)["proposal_manifest_digest"],
            selector)
        with self.no_external_act(held):
            self.assertIsNotNone(self.resume(held))

    def test_a_publication_history_that_names_another_result_refuses(self):
        held = self.implemented()
        self.reopened()
        answered = self.publication.published_of(attempt_id=self.ATTEMPT)
        for name, changed in (
                ("another attempt", {"attempt_id": "another-attempt"}),
                ("another result", {"result_id": "another-result"}),
                ("another result manifest",
                 {"result_manifest_digest": "sha256:" + "3" * 64}),
                ("another assignment",
                 {"assignment": dict(answered["assignment"],
                                     generation=99)})):
            with self.subTest(history=name):
                with mock.patch.object(
                        self.publication, "published_of",
                        return_value=dict(answered, **changed)):
                    with self.no_external_act(held):
                        self.assertIsInstance(self.refusal(self.resume, held),
                                              ContractRefusal)

    def test_a_malformed_publication_history_refuses(self):
        held = self.implemented()
        self.reopened()
        for answer in ([], {}, "published", {"attempt_id": self.ATTEMPT},
                       dict(self.publication.published_of(
                           attempt_id=self.ATTEMPT), extra="anything")):
            with self.subTest(history=answer):
                with mock.patch.object(self.publication, "published_of",
                                       return_value=answer):
                    with self.no_external_act(held):
                        self.assertIsInstance(self.refusal(self.resume, held),
                                              ContractRefusal)

    def test_a_seam_with_no_replay_half_refuses(self):
        held = self.implemented()
        self.reopened()
        self.publication = SimpleNamespace(publish=lambda **named: None)
        with self.assertRaises(ContractRefusal) as raised:
            self.resume(held)
        self.assertIn("published_of", raised.exception.message)

    # -- the seven cases restored, per review 2026-09-08T16-18-42Z ------------
    #
    # The previous pass removed these from the mock-seam class when the
    # corrections made their fixtures unable to reach a positive answer. The
    # review is right that an author's own unaccepted tests are not exempt
    # from "preserve all existing assertions", so each is restored HERE by its
    # original name, with its behavioural assertion intact, over the real
    # committed custody that now makes it honest. Two are driven differently
    # because the correction removed what they used to depend on, and each
    # says so in its own words rather than quietly asserting something else.

    def test_the_resume_answers_the_ordinary_endings_document(self):
        held = self.implemented()
        ended = held["ended"]
        self.reopened()
        with self.no_external_act(held):
            answered = self.resume(held)
        self.assertEqual(sorted(answered), sorted(
            ("attempt_id", "disposition", "result_id", "manifest_digest",
             "receipt_digest", "artifacts", "retention", "published",
             "checkpoint_id", "checkpoint")))
        self.assertEqual(answered["attempt_id"], self.ATTEMPT)
        self.assertEqual(answered["disposition"], "completed")
        self.assertEqual(answered["result_id"], ended["result_id"])
        self.assertEqual(answered["manifest_digest"], ended["manifest_digest"])
        self.assertEqual(answered["receipt_digest"], ended["receipt_digest"])
        self.assertEqual(answered["artifacts"], ended["artifacts"])
        self.assertEqual(answered["artifacts"],
                         sorted(answered["artifacts"]))
        self.assertEqual(answered["retention"], ended["retention"])

    def test_the_checkpoint_is_the_one_this_ending_already_froze(self):
        held = self.implemented()
        self.reopened()
        with self.no_external_act(held):
            answered = self.resume(held)
        self.assertEqual(answered["checkpoint"], held["ended"]["checkpoint"])
        self.assertEqual(answered["checkpoint_id"],
                         held["ended"]["checkpoint_id"])
        self.assertEqual(answered["checkpoint_id"],
                         answered["checkpoint"]["checkpoint_id"])

    def test_resuming_twice_answers_the_same_thing_and_does_nothing(self):
        held = self.implemented()
        self.reopened()
        with self.no_external_act(held):
            first = self.resume(held)
            self.assertEqual(self.resume(held), first)
            self.assertEqual(self.resume(held), first)

    def test_the_line_and_its_writer_are_left_exactly_where_they_were(self):
        from baton_v12.worker_manager import writer_of
        held = self.implemented()
        self.reopened()
        before = (line_of(self.control, self.line["line_id"]),
                  writer_of(self.control, held["writer"]["writer_id"]))
        with self.no_external_act(held):
            self.resume(held)
        self.assertEqual(
            (line_of(self.control, self.line["line_id"]),
             writer_of(self.control, held["writer"]["writer_id"])), before)

    def test_a_checkpoint_that_is_not_this_writers_frozen_one_refuses(self):
        """Restored, and driven by the writer's own record rather than the
        line's pointer.

        The behavioural assertion is unchanged: a checkpoint this ending did
        not freeze refuses, and nothing reaches the Authority while it does.
        What changed is what makes that true. The pointer version required the
        line's CURRENT checkpoint to be this writer's, which is exactly the
        mutable dependency the review required removing; here the writer's own
        committed freeze is taken away instead, so `freeze_checkpoint` finds
        nothing to replay and refuses on the destroyed runtime.
        """
        held = self.implemented()
        self.reopened()
        caught = self.damaged(held, "DELETE FROM operations WHERE kind = "
                                    "'review-line.freeze'")
        self.assertIsInstance(caught, ContractRefusal)

    def test_a_seam_that_cannot_answer_the_committed_publication_refuses(self):
        held = self.implemented()
        self.reopened()
        self.assertEqual(review_driver.PUBLICATION_HISTORY,
                         ("published_of",))
        for name, publication, expected in (
                ("no replay half",
                 SimpleNamespace(publish=lambda **named: None),
                 "published_of"),
                ("nothing committed",
                 SimpleNamespace(publish=lambda **named: None,
                                 published_of=lambda **named: None),
                 "no committed publication history")):
            with self.subTest(seam=name):
                self.publication = publication
                with self.assertRaises(ContractRefusal) as raised:
                    self.resume(held)
                self.assertIn(expected, raised.exception.message)

    def test_the_resumed_steps_are_the_ones_the_resume_performs(self):
        self.assertEqual(review_driver.HISTORICAL_IMPLEMENTATION_ENDING,
                         ("correlate", "intake", "retain", "cleanup",
                          "checkpoint", "publish"))
        for absent in ("quiesce", "observe", "consume", "freeze"):
            self.assertIn(absent, review_driver.IMPLEMENTATION_ENDING)
            self.assertNotIn(absent,
                             review_driver.HISTORICAL_IMPLEMENTATION_ENDING)

    def test_the_recorded_steps_are_the_ones_the_resume_performs(self):
        held = self.implemented()
        self.reopened()
        recorded = []
        real = {"_correlated": review_driver._correlated,
                "cleanup_of": review_driver.cleanup_of}
        forbidden = ("request_freeze", "observe", "request_intake",
                     "decide_retention", "reconcile_runtime",
                     "authorize_cleanup")
        with contextlib.ExitStack() as stack:
            for name in forbidden:
                stack.enter_context(mock.patch.object(
                    review_driver, name, side_effect=AssertionError(
                        f"a resumed ending called {name}")))
            stack.enter_context(mock.patch.object(
                review_driver, "_correlated",
                lambda *a, **k: (recorded.append("correlate"),
                                 real["_correlated"](*a, **k))[1]))
            stack.enter_context(mock.patch.object(
                review_driver, "cleanup_of",
                lambda *a, **k: (recorded.append("cleanup"),
                                 real["cleanup_of"](*a, **k))[1]))
            with self.no_external_act(held):
                self.resume(held)
        self.assertEqual(recorded, ["correlate", "cleanup"])
        self.assertEqual(review_driver.HISTORICAL_IMPLEMENTATION_ENDING,
                         ("correlate", "intake", "retain", "cleanup",
                          "checkpoint", "publish"))
        for absent in ("quiesce", "observe", "consume", "freeze"):
            self.assertIn(absent, review_driver.IMPLEMENTATION_ENDING)
            self.assertNotIn(absent,
                             review_driver.HISTORICAL_IMPLEMENTATION_ENDING)
