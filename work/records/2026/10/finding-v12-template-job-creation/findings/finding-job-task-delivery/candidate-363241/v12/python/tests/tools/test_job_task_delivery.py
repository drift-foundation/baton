"""W363066 — the bytes a stage is ACTUALLY delivered, published and proved.

`test_creation_ports` proves the composition and the input identity.
`test_creation` proves the operation. This suite is the one the review asked
for last: it drives the REAL publication and proof path — `_SingleWorker`'s own
`_for_job`, `_published_task` and `_proved_task` over a real directory, with a
real Job store behind `single_worker.job_task_reader` — and INSPECTS THE BYTES
ON DISK rather than a source string or a rendering compared with itself.

WHY THAT PATH AND NOT A FULL LIFECYCLE. `_published_task` is where the task
becomes a file: exclusive no-follow creation, whole write, fsync, read-back
comparison against the held bytes, then 0444. `_proved_task` is the restart
half: the same three questions asked again of what is on disk. Those two
functions are the delivery, and driving them over one worker serving two Jobs
is what shows the bytes do not cross.

THE WORKER IS COMPOSED THE WAY `ThreeWorkersOneJobThreeImages` COMPOSES ONE --
`__new__` plus the held configuration -- because `_for_job`, `_published_task`
and `_proved_task` read the held configuration and their operands and nothing
else. A case that needed a live runtime to ask a delivery question would be
measuring the fixture.
"""

import json
import os
import stat
import unittest

from baton_v12.contracts import ContractRefusal, digest_of_bytes
from baton_v12.contracts.manifest import job_input_identity

from tools import job_task, single_worker

from tests.job_manager import fixtures
from tests.tools.test_single_worker import ThreeWorkersOneJobThreeImages

FIRST = "job-first"
SECOND = "job-second"


class DeliveryCase(ThreeWorkersOneJobThreeImages):
    """One configured worker, a real Job store, and real files on disk."""

    def setUp(self):
        super().setUp()
        self.jobs = []

    def selection(self, job_id, statement, *, work_id=None):
        return {"job_id": job_id, "statement": statement,
                "acceptance": [f"{job_id} is accepted"],
                "scope": {"work": ["v12/python/tools/job_task.py"],
                          "tests": []},
                "template_version":
                    "baton.v12.job-template.implementation-review/1",
                "work_id": work_id or fixtures.WORK_A}

    def composed(self, job_id, statement, *, installed):
        """One Job's own task document, from the installed bytes."""
        return job_task.per_job_delivery(
            installed, self.installed_manifest,
            self.selection(job_id, statement))

    def worker_serving(self, role, tasks):
        """One worker whose reader answers from a fixed table.

        THE TABLE IS A STAND-IN FOR THE JOB STORE and is deliberately shaped
        like `job_task_reader`'s answer: text for a Job that has its own task,
        `None` for one that does not. The reader itself is driven against a
        REAL store in `TheReaderOverARealStore` below, so neither half is
        taken on trust.
        """
        given, manifest = self.configured_as(0, role)
        self.installed_manifest = self.held(given)["input_manifest"]
        worker = self.worker_for(given)
        worker.judgment_document = None
        worker.job_task = lambda *, job_id: tasks.get(job_id)
        return worker

    def inputs(self, name):
        place = os.path.join(self.root, f"inputs-{name}")
        os.makedirs(place)
        return place

    def stage_of(self, role, job_id):
        return dict(self.stage_for(role), job_id=job_id)


class TwoJobsOnOneWorkerGetTheirOwnBytes(DeliveryCase):

    def test_the_published_file_is_this_jobs_own_task(self):
        """THE BYTES ON DISK, read back and compared whole."""
        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        first = self.composed(FIRST, "Close the first finding.",
                              installed=installed)
        second = self.composed(SECOND, "Close the second finding.",
                               installed=installed)
        worker.job_task = lambda *, job_id: {
            FIRST: first["task_document"],
            SECOND: second["task_document"]}.get(job_id)
        for job_id, held in ((FIRST, first), (SECOND, second)):
            with self.subTest(job=job_id):
                manifest, task = worker._for_job(
                    self.stage_of("implementation", job_id))
                place = self.inputs(job_id)
                worker._published_task(place, content=task)
                with open(os.path.join(place, single_worker.TASK_DOCUMENT),
                          "rb") as reading:
                    found = reading.read()
                self.assertEqual(found, task)
                document = json.loads(found.decode("utf-8"))
                self.assertEqual(document["task_id"], job_id)
                self.assertIn(f"{job_id} is accepted",
                              document["instructions"])
                # AND THE MANIFEST THAT TRAVELS WITH IT NAMES THESE BYTES.
                contract = manifest["human_contract"]
                self.assertEqual(contract["bytes"], len(found))
                self.assertEqual(contract["content_digest"],
                                 digest_of_bytes(found))

    def test_neither_jobs_bytes_reach_the_others_root(self):
        """NO CROSS-JOB EFFECT, from ONE worker object.

        The worker is shared and immutable; `_for_job` composes per stage from
        a fresh copy, so there is nothing on the worker for one Job to leave
        behind for the next.
        """
        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        first = self.composed(FIRST, "Close the first finding.",
                              installed=installed)
        second = self.composed(SECOND, "Close the second finding.",
                               installed=installed)
        worker.job_task = lambda *, job_id: {
            FIRST: first["task_document"],
            SECOND: second["task_document"]}.get(job_id)
        places = {}
        for job_id, held in ((FIRST, first), (SECOND, second)):
            _manifest, task = worker._for_job(
                self.stage_of("implementation", job_id))
            places[job_id] = self.inputs(job_id)
            worker._published_task(places[job_id], content=task)
        held_first = open(os.path.join(places[FIRST],
                                       single_worker.TASK_DOCUMENT),
                          "rb").read().decode("utf-8")
        held_second = open(os.path.join(places[SECOND],
                                        single_worker.TASK_DOCUMENT),
                           "rb").read().decode("utf-8")
        self.assertNotEqual(held_first, held_second)
        self.assertNotIn("second finding", held_first)
        self.assertNotIn("first finding", held_second)
        self.assertNotIn(SECOND, held_first)
        self.assertNotIn(FIRST, held_second)
        # AND THE SHARED CONFIGURATION IS UNTOUCHED.
        self.assertEqual(worker.given["task_bytes"], installed)

    def test_the_two_jobs_input_identities_differ_and_both_are_consistent(
            self):
        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        first = self.composed(FIRST, "A first task.", installed=installed)
        second = self.composed(SECOND, "A second task.", installed=installed)
        worker.job_task = lambda *, job_id: {
            FIRST: first["task_document"],
            SECOND: second["task_document"]}.get(job_id)
        held = {}
        for job_id in (FIRST, SECOND):
            manifest, _task = worker._for_job(
                self.stage_of("implementation", job_id))
            held[job_id] = job_input_identity(manifest)
        self.assertNotEqual(held[FIRST], held[SECOND])
        self.assertEqual(held[FIRST],
                         job_input_identity(first["input_manifest"]))
        self.assertEqual(held[SECOND],
                         job_input_identity(second["input_manifest"]))
        self.assertNotEqual(held[FIRST],
                            job_input_identity(worker.given["input_manifest"]))

    def test_the_review_role_is_delivered_the_same_task(self):
        """ROLE-SPECIFIC SEMANTICS PRESERVED, and the task is the JOB's.

        An implementer and a reviewer read different role instructions -- that
        is `role_instructions_digest`, which `job_input_identity` projects OUT
        -- and they read the SAME task, because a reviewer judging a different
        task than the implementer performed is the one thing a shared Job
        cannot survive.
        """
        installed = {}
        composed = {}
        for role in ("implementation", "review"):
            worker = self.worker_serving(role, {})
            installed[role] = self.held(self.configured_as(0, role)[0])[
                "task_bytes"]
            composed[role] = self.composed(FIRST, "One task, two roles.",
                                           installed=installed[role])
            worker.job_task = lambda *, job_id: composed[role][
                "task_document"] if job_id == FIRST else None
            _manifest, task = worker._for_job(self.stage_of(role, FIRST))
            place = self.inputs(f"{role}-{FIRST}")
            worker._published_task(place, content=task)
            with open(os.path.join(place, single_worker.TASK_DOCUMENT),
                      "rb") as reading:
                composed[role] = reading.read()
        self.assertEqual(composed["implementation"], composed["review"],
                         "one Job is one task whoever serves the stage")


class RestartProvesWhatWasPublished(DeliveryCase):
    """The resumed attempt reads the bytes the first one wrote, or refuses."""

    def published(self, job_id="job-first", statement="A first task."):
        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        held = self.composed(job_id, statement, installed=installed)
        worker.job_task = lambda *, job_id_asked=None, job_id=None: (
            held["task_document"] if job_id == job_id_asked or job_id
            else None)
        worker.job_task = lambda *, job_id: held["task_document"]
        _manifest, task = worker._for_job(
            self.stage_of("implementation", job_id))
        place = self.inputs(job_id)
        worker._published_task(place, content=task)
        return worker, place, task

    def test_a_restart_proves_the_published_task_and_continues(self):
        """NOT A SECOND RENDERING COMPARED WITH ITSELF.

        `_proved_task` reads what is on disk and compares it with the bytes
        this delivery holds, so this is the resumed attempt's own question
        asked of real material the first attempt wrote.
        """
        worker, place, task = self.published()
        worker._proved_task(place, content=task)
        found = open(os.path.join(place, single_worker.TASK_DOCUMENT),
                     "rb").read()
        self.assertEqual(found, task)
        mode = stat.S_IMODE(os.stat(os.path.join(
            place, single_worker.TASK_DOCUMENT)).st_mode)
        self.assertEqual(mode, 0o444,
                         "the published task is read-only on disk")

    def test_a_restart_that_would_deliver_another_task_refuses(self):
        """THE MISMATCH, which is the cross-Job accident made concrete."""
        worker, place, _task = self.published()
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        other = self.composed(SECOND, "A second task.", installed=installed)
        with self.assertRaises(ContractRefusal) as caught:
            worker._proved_task(
                place, content=job_task.delivered_bytes(
                    other["task_document"]))
        # REFUSED BEFORE LAUNCH, and `_proved_task` names the fact rather
        # than the member: the document on disk is not the content this
        # delivery holds.
        self.assertIn(caught.exception.code, ("digest", "precondition"))
        self.assertIn("another task document", caught.exception.message)

    def test_a_tampered_published_task_refuses(self):
        worker, place, task = self.published()
        held = os.path.join(place, single_worker.TASK_DOCUMENT)
        os.chmod(held, 0o644)
        with open(held, "wb") as writing:
            writing.write(task[:-1] + b" ")
        with self.assertRaises(ContractRefusal):
            worker._proved_task(place, content=task)

    def test_a_missing_published_task_refuses(self):
        worker, place, task = self.published()
        os.unlink(os.path.join(place, single_worker.TASK_DOCUMENT))
        with self.assertRaises(ContractRefusal) as caught:
            worker._proved_task(place, content=task)
        self.assertIn("path", caught.exception.code)

    def test_publishing_over_an_existing_task_refuses(self):
        """PROVENANCE THIS COMPOSITION CANNOT PROVE.

        `_published_task` creates exclusively, so a document somebody else
        left at that name is refused rather than overwritten -- unchanged by
        this Work and asserted because the per-Job content now flows through
        it.
        """
        worker, place, task = self.published()
        with self.assertRaises(ContractRefusal) as caught:
            worker._published_task(place, content=task)
        self.assertIn("already carries", caught.exception.message)


class TheInstalledDeliveryIsPreserved(DeliveryCase):
    """A Job with no own task is served exactly as before this Work."""

    def test_a_job_the_reader_answers_none_for_gets_the_installed_task(self):
        worker = self.worker_serving("implementation", {})
        installed_given = self.held(self.configured_as(0, "implementation")[0])
        manifest, task = worker._for_job(
            self.stage_of("implementation", "job-legacy"))
        self.assertEqual(task, installed_given["task_bytes"])
        self.assertEqual(manifest, installed_given["input_manifest"])

    def test_a_worker_with_no_reader_at_all_gets_the_installed_task(self):
        worker = self.worker_serving("implementation", {})
        worker.job_task = None
        installed_given = self.held(self.configured_as(0, "implementation")[0])
        manifest, task = worker._for_job(
            self.stage_of("implementation", FIRST))
        self.assertEqual(task, installed_given["task_bytes"])
        self.assertEqual(manifest, installed_given["input_manifest"])

    def test_a_stage_with_no_job_gets_the_installed_task(self):
        """THE BOOTSTRAP COMPOSITION, which binds no Job."""
        worker = self.worker_serving("implementation", {})
        installed_given = self.held(self.configured_as(0, "implementation")[0])
        for stage in (None, {"kind": "implementation"}):
            with self.subTest(stage=stage):
                _manifest, task = worker._for_job(stage)
                self.assertEqual(task, installed_given["task_bytes"])


class TheReaderOverARealStore(DeliveryCase):
    """`job_task_reader` against a real Job store, not a stand-in table."""

    def test_it_answers_the_stored_document_and_none_for_everything_else(
            self):
        from baton_v12.job_manager import JobStore
        from baton_v12.job_manager.creation import job_task_of

        place = os.path.join(self.root, "jobs.sqlite3")
        store = JobStore.open(place, authority_uuid=fixtures.UUID,
                              incarnation="jobs-1",
                              clock=lambda: fixtures.NOW)
        self.addCleanup(store.close)
        reader = single_worker.job_task_reader(store)
        self.assertIsNone(reader(job_id="job-nobody-created"))
        self.assertIsNone(reader(job_id=None))
        self.assertIsNone(job_task_of(store, "job-nobody-created"))
        # AND A ROW WITH A TASK IS ANSWERED VERBATIM. Written through the
        # store's own connection rather than through a creation, because what
        # is under test here is the READER and a creation would need its four
        # owner ports.
        store._connection.execute(
            "INSERT INTO template_jobs (job_id, work_id, submission_id, "
            "template_version, state, request, request_digest, "
            "resolution_digest, resolution, task_document, "
            "submission_signature, intended_at, created_at, incarnation) "
            "VALUES ('job-stored', ?, 'sub-stored', 'v/1', 'intended', '{}', "
            "'sha256:r', 'sha256:x', '{}', ?, '{}', ?, NULL, 'jobs-1')",
            (fixtures.WORK_A, '{"schema":"baton.dogfood-task/2"}',
             fixtures.NOW))
        self.assertEqual(reader(job_id="job-stored"),
                         '{"schema":"baton.dogfood-task/2"}')


if __name__ == "__main__":
    unittest.main()
