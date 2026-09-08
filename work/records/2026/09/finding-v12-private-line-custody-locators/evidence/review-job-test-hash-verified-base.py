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

import json
import os
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
        adapter = _Adapter("runtime-writer-attempt-1")
        with _endings() as recorded:
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
                 identities=review_driver.ADAPTER_IDENTITIES):
        self.runtime_id = runtime_id
        self.answer = answer
        self.stops = []
        for verb in (verbs if verbs is not None
                     else review_driver.RUNTIME_ADAPTER):
            if verb != "stop":
                setattr(self, verb, lambda *a, **k: None)
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
                              note("cleanup")), \
            mock.patch.object(review_driver.review_cycles, "freeze_checkpoint",
                              checkpoint), \
            mock.patch.object(review_driver.review_cycles, "record_verdict",
                              verdict), \
            mock.patch.object(_Seam, "publish", _recording(recorded)):
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
