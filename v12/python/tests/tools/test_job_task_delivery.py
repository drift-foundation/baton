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
import shutil
import stat
import unittest

from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.contracts.manifest import check_input_pair, job_input_identity

from baton_v12.job_manager import templates
from baton_v12.worker_manager import attempts, workspaces

from tools import job_task, single_worker, stage_execution

from tests.job_manager import fixtures
from tests.manager import input_roots
from tests.tools.test_stage_execution import (ComposedOneJobCase,
                                              ServingCase,
                                              _ConcurrentEngine)
from tests.tools.test_single_worker import (
    Engine, SingleWorkerCase, TheAnsweredEndingRunsThroughTheRealOwners,
    ThreeWorkersOneJobThreeImages, claimed_offers_for, reconcile, status,
    submit, sweep)

FIRST = "job-first"
SECOND = "job-second"


class DeliveryCase(SingleWorkerCase):
    """One configured worker, a real Job store, and real files on disk.

    THE HELPERS ARE BORROWED AND THE TESTS ARE NOT. Subclassing
    `ThreeWorkersOneJobThreeImages` re-ran ITS cases under every subclass
    here, which is noise at best and -- because its `worker_for` composes a
    worker through `__new__` for a preflight question -- a fixture asking a
    different question under this suite's name. Binding the four helpers
    explicitly takes what this suite needs from the owner that has it,
    without inheriting a single assertion.
    """

    ROLES = ThreeWorkersOneJobThreeImages.ROLES
    configured_as = ThreeWorkersOneJobThreeImages.configured_as
    held = ThreeWorkersOneJobThreeImages.held
    stage_for = ThreeWorkersOneJobThreeImages.stage_for
    job_for = ThreeWorkersOneJobThreeImages.job_for
    worker_for = ThreeWorkersOneJobThreeImages.worker_for

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
        """One fresh input root, under a parent this case can still write.

        `compose_input_root` FREEZES the root 0555 when it finishes, which is
        the product doing its job -- so every root gets its own parent
        directory and a case that has to mutate a frozen one re-opens it with
        `writable` below. A fixture that created the second root beside a
        frozen first one met `PermissionError` and was measuring the freeze.
        """
        place = os.path.join(self.root, f"inputs-{name}", "inputs")
        os.makedirs(place)
        return place

    def writable(self, root):
        """Re-open a frozen root so a case can tamper with what is inside."""
        os.chmod(root, 0o755)
        held = os.path.join(root, single_worker.TASK_DOCUMENT)
        if os.path.exists(held):
            os.chmod(held, 0o644)
        return root

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


class TheConnectedPreparationPath(DeliveryCase):
    """W363066 review 2026-10-26T20-28-59Z: the OWNING sequence, not helpers.

    The previous round's cases called `_for_job` and the file helpers directly
    and bypassed both production boundaries the reviewer then reproduced:
    `_matches` compared the INSTALLED manifest and refused the composed Job,
    and `_assignment_manifest` minted an assignment against the installed
    digest while `_input` published the per-Job one -- which
    `compose_input_root` refuses as "two halves of two deliveries", after
    `task.json` is already on disk.

    SO THESE CASES DRIVE WHAT `_prepared` DRIVES, in its order: one document
    from `_given_for(stage)`, then the real `_matches`, the real
    `_assignment_manifest`, and the real `_input` -- which calls the real
    `compose_input_root`. No engine and no provider: the sequence under test
    ends where a runtime would start.
    """

    def row_for(self, worker):
        """The claimed-offer row `_assignment_manifest` reads."""
        return dict(worker.given["input_manifest"]["work_ref"],
                    participant=worker.given["participant"],
                    claim_generation=1,
                    claim_principal=worker.given["principal"],
                    claim_scope="scope:deployment", claim_role="baton.impl",
                    claim_grant="direct", claim_policy_generation=1,
                    claim_event_seq=1, accepted_at=fixtures.NOW,
                    decided_at=fixtures.NOW)

    def prepared(self, role, job_id, statement, *, worker=None, name=None):
        """One stage's preparation, through the owning sequence."""
        worker = worker or self.worker_serving(role, {})
        installed = self.held(self.configured_as(0, role)[0])["task_bytes"]
        made = self.composed(job_id, statement, installed=installed)
        held = {job_id: made["task_document"]}
        existing = worker.job_task
        worker.job_task = lambda *, job_id: held.get(
            job_id, existing(job_id=job_id) if existing else None)
        stage = self.stage_of(role, job_id)
        given = worker._given_for(stage)
        manifest = given["input_manifest"]
        worker._matches(stage, self.job_for(manifest))
        assignment = single_worker._assignment_manifest(
            given, self.row_for(worker), stage["attempt_id"],
            stage["offer_id"])
        root = self.inputs(name or f"{role}-{job_id}")
        mount = os.path.join(root, manifest["sources"][0]["destination"])
        os.makedirs(mount)
        from types import SimpleNamespace

        read = worker._input({"inputs": root}, assignment,
                             SimpleNamespace(mountpoint=mount), stage)
        return {"worker": worker, "stage": stage, "given": given,
                "assignment": assignment, "root": root, "mount": mount,
                "read": read, "composed": made}

    def published(self, root):
        with open(os.path.join(root, single_worker.TASK_DOCUMENT),
                  "rb") as reading:
            return reading.read()

    def test_both_ordinary_roles_prepare_the_requested_task(self):
        """THE WHOLE SEQUENCE, for implementation AND review."""
        for role in ("implementation", "review"):
            with self.subTest(role=role):
                held = self.prepared(role, FIRST, "The requested task.")
                manifest = held["given"]["input_manifest"]
                # THE ASSIGNMENT AND THE ROOT ARE ONE PAIR.
                self.assertEqual(held["assignment"]["input_manifest_digest"],
                                 manifest["manifest_digest"])
                self.assertEqual(held["read"]["manifest_digest"],
                                 manifest["manifest_digest"])
                # AND THE FILE IN THE ROOT IS THIS JOB'S TASK.
                document = json.loads(self.published(held["root"]).decode())
                self.assertEqual(document["task_id"], FIRST)
                self.assertIn("The requested task.",
                              document["instructions"])
                # AND NONE OF THOSE IS THE INSTALLED IDENTITY.
                installed = self.held(self.configured_as(0, role)[0])
                self.assertNotEqual(manifest["manifest_digest"],
                                    installed["input_manifest"][
                                        "manifest_digest"])

    def test_the_recorded_and_launch_identities_are_the_delivered_one(self):
        """EVERY OWNER DESCRIBES ONE RUNTIME INPUT.

        `start` records the attempt from this document and `_job_execution`
        composes the execution context from it, so the digest an operator
        reads back is the digest of the root the container is given.
        """
        held = self.prepared("implementation", FIRST, "The requested task.")
        worker, stage = held["worker"], held["stage"]
        manifest = held["given"]["input_manifest"]
        self.assertEqual(
            worker._given_for(stage)["input_manifest"]["manifest_digest"],
            manifest["manifest_digest"])
        # THE ADAPTER IDENTITY TOO, when the caller names the stage.
        self.assertEqual(
            worker._given_for(stage)["input_manifest"]["toolchain_digest"],
            manifest["toolchain_digest"])

    def test_two_jobs_prepare_independently_on_one_worker(self):
        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        made = {one: self.composed(one, f"Task for {one}.",
                                   installed=installed)
                for one in (FIRST, SECOND)}
        worker.job_task = lambda *, job_id: made[job_id]["task_document"] \
            if job_id in made else None
        roots = {}
        for job_id in (FIRST, SECOND):
            stage = self.stage_of("implementation", job_id)
            given = worker._given_for(stage)
            worker._matches(stage, self.job_for(given["input_manifest"]))
            assignment = single_worker._assignment_manifest(
                given, self.row_for(worker), f"attempt-{job_id}",
                stage["offer_id"])
            root = self.inputs(f"two-{job_id}")
            mount = os.path.join(
                root, given["input_manifest"]["sources"][0]["destination"])
            os.makedirs(mount)
            from types import SimpleNamespace

            worker._input({"inputs": root}, assignment,
                          SimpleNamespace(mountpoint=mount), stage)
            roots[job_id] = root
        first = json.loads(self.published(roots[FIRST]).decode())
        second = json.loads(self.published(roots[SECOND]).decode())
        self.assertEqual(first["task_id"], FIRST)
        self.assertEqual(second["task_id"], SECOND)
        self.assertNotIn(SECOND, json.dumps(first))
        self.assertNotIn(FIRST, json.dumps(second))
        self.assertEqual(worker.given["task_bytes"], installed)

    def test_a_reopened_preparation_proves_the_same_root(self):
        """RESTART THROUGH THE OWNING PATH, not a second rendering.

        `_input` is called again over the root the first preparation composed:
        `read_input_root` succeeds now, so the comparison branch runs and
        `_proved_task` reads what is on disk.
        """
        held = self.prepared("implementation", FIRST, "The requested task.")
        from types import SimpleNamespace

        again = held["worker"]._input(
            {"inputs": held["root"]}, held["assignment"],
            SimpleNamespace(mountpoint=held["mount"]), held["stage"])
        self.assertEqual(again["manifest_digest"],
                         held["given"]["input_manifest"]["manifest_digest"])
        self.assertEqual(json.loads(self.published(held["root"]).decode())[
            "task_id"], FIRST)

    def test_an_assignment_from_the_installed_manifest_refuses(self):
        """THE REVIEWER'S R2, AS A CASE.

        An assignment minted against the installed digest beside a per-Job
        root is what `compose_input_root` refuses, and it must stay refused:
        the pair in one root is one pair.
        """
        from types import SimpleNamespace

        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])[
            "task_bytes"]
        made = self.composed(FIRST, "The requested task.",
                             installed=installed)
        worker.job_task = lambda *, job_id: made["task_document"]
        stage = self.stage_of("implementation", FIRST)
        manifest = worker._given_for(stage)["input_manifest"]
        # MINTED FROM THE INSTALLED CONFIGURATION, which is what `_prepared`
        # did before this correction.
        assignment = single_worker._assignment_manifest(
            worker.given, self.row_for(worker), stage["attempt_id"],
            stage["offer_id"])
        root = self.inputs("mismatched")
        mount = os.path.join(root, manifest["sources"][0]["destination"])
        os.makedirs(mount)
        with self.assertRaises(ContractRefusal) as caught:
            worker._input({"inputs": root}, assignment,
                          SimpleNamespace(mountpoint=mount), stage)
        self.assertIn("two halves of two deliveries",
                      caught.exception.message)

    def test_a_tampered_root_refuses_on_the_reopened_preparation(self):
        from types import SimpleNamespace

        held = self.prepared("implementation", FIRST, "The requested task.")
        place = os.path.join(self.writable(held["root"]),
                             single_worker.TASK_DOCUMENT)
        with open(place, "r+b") as writing:
            writing.seek(0)
            writing.write(b"{")
        with self.assertRaises(ContractRefusal):
            held["worker"]._input(
                {"inputs": held["root"]}, held["assignment"],
                SimpleNamespace(mountpoint=held["mount"]), held["stage"])

    def test_a_missing_task_refuses_on_the_reopened_preparation(self):
        from types import SimpleNamespace

        held = self.prepared("implementation", FIRST, "The requested task.")
        os.unlink(os.path.join(self.writable(held["root"]),
                               single_worker.TASK_DOCUMENT))
        with self.assertRaises(ContractRefusal):
            held["worker"]._input(
                {"inputs": held["root"]}, held["assignment"],
                SimpleNamespace(mountpoint=held["mount"]), held["stage"])

    def test_a_job_with_no_own_task_prepares_the_installed_one(self):
        """THE PRESERVED PATH, through the same owning sequence."""
        from types import SimpleNamespace

        worker = self.worker_serving("implementation", {})
        installed = self.held(self.configured_as(0, "implementation")[0])
        stage = self.stage_of("implementation", "job-legacy")
        given = worker._given_for(stage)
        self.assertIs(given, worker.given)
        worker._matches(stage, self.job_for(given["input_manifest"]))
        assignment = single_worker._assignment_manifest(
            given, self.row_for(worker), stage["attempt_id"],
            stage["offer_id"])
        root = self.inputs("legacy")
        mount = os.path.join(
            root, given["input_manifest"]["sources"][0]["destination"])
        os.makedirs(mount)
        worker._input({"inputs": root}, assignment,
                      SimpleNamespace(mountpoint=mount), stage)
        self.assertEqual(self.published(root), installed["task_bytes"])


class PoolDeliveryCase(DeliveryCase):
    """One pool role, one real development line, and NO version control.

    W363066 review at handoff E363761 named the route and this is it. The
    bootstrap composition cannot serve either remaining scenario -- it binds
    one Work, composes `roles=("implementation",)` and serves one stage at a
    time -- and the pool's own serving loop materializes its line through the
    configured `git` checkpoint profile, which this implementer may not run.
    What the product already supports instead is the PROFILE SEAM:
    `create_line`, `prepare_implementation`, `freeze_checkpoint` and
    `prepare_review` all take the checkpoint profile as an operand, and
    `tests.job_manager.test_review_driver.Profile` is the
    deployment-configured profile "with no VCS behind it" -- its own words.

    So the line, the writer grant, the frozen checkpoint, the review
    attachment and both mounts here are the ACCEPTED OPERATIONS over a real
    control store, composed by the real `stage_execution.StageComposition`
    the serving loop composes; the checkpoint profile and the engine are the
    two deterministic seams. EVERY CASE IN THIS CLASS PROVES ITS OWN ABSENCE
    OF VERSION CONTROL: `no_version_control` replaces the process runners
    with ones that refuse any version-control invocation, so a case that
    reached one would fail rather than quietly perform it.
    """

    def setUp(self):
        super().setUp()
        from tests.job_manager.test_review_driver import Port, Profile

        self.profile_seam = Profile()
        self.ports = {}
        self.lines = {}
        self.no_version_control()

    def port_for(self, who):
        from tests.job_manager.test_review_driver import Port

        return self.ports.setdefault(who, Port(who))

    def no_version_control(self):
        """Refuse every version-control process for the rest of this case."""
        import subprocess

        held_run, held_popen = subprocess.run, subprocess.Popen

        def refuse(argv):
            first = str(argv[0]).split("/")[-1] if argv else ""
            if first == "git":
                raise AssertionError(
                    "this case spawned version control: "
                    + " ".join(str(one) for one in argv))

        def run(argv, *arguments, **named):
            refuse(argv)
            return held_run(argv, *arguments, **named)

        def popen(argv, *arguments, **named):
            refuse(argv)
            return held_popen(argv, *arguments, **named)

        subprocess.run, subprocess.Popen = run, popen
        self.addCleanup(setattr, subprocess, "Popen", held_popen)
        self.addCleanup(setattr, subprocess, "run", held_run)

    def configured(self, incarnation):
        """One control store a deployment has configured, and its Job store."""
        from baton_v12.worker_manager import certify_profile
        from baton_v12.worker_manager.workspaces import \
            configure_workspace_storage

        job, control = self.stores(incarnation)
        certify_profile(control, "runtime", "reference", fixtures.PROFILE)
        configure_workspace_storage(control, self.storage)
        self.group = input_roots.configured_group(control)
        return job, control

    def line_for_job(self, control, job_id, work_id=None):
        """One real persistent line per Job, as `line_for` answers one."""
        from baton_v12.worker_manager import create_line
        from baton_v12.worker_manager.source_boundary import nominate_source

        source = os.path.join(self.root, "line-source-" + job_id)
        os.makedirs(source, exist_ok=True)
        held = create_line(
            control, source=nominate_source(source),
            declared_base="a" * 40, profile=self.profile_seam,
            authority_uuid=self.config["authority_uuid"],
            work_id=work_id or fixtures.WORK_A)
        self.lines[job_id] = held
        return held

    def composition(self, control, role, *, worker_id):
        """The real `StageComposition`, over this case's lines and profile."""
        lines = self.lines
        held_control, held_profile = control, self.profile_seam

        class Deployment:
            control = held_control
            profile = held_profile

            def generation_of(self, _attempt_id):
                return 1

            def line_for(self, job_id):
                # THE LINE IS READ BACK, not remembered: `_prepare` composes a
                # writer or an attachment against the line's CURRENT
                # checkpoint, and a stale copy would hide exactly the ordering
                # this harness exists to exercise.
                from baton_v12.worker_manager import review_cycles

                return review_cycles.line_of(held_control,
                                             lines[job_id]["line_id"])

        return stage_execution.StageComposition(
            Deployment(), role=role, worker_id=worker_id)

    def attempt_row(self, control, worker, attempt_id, *, input_digest):
        """One attempt, recorded by the PRODUCT and activated by the fixture.

        THE HALF THAT IS UNDER TEST IS THE PRODUCT'S. `start` records an
        attempt through `attempts.record_attempt` with the input digest of
        the document the stage is served under, and that is the call made
        here, with this worker's own adapter, profile and image identity --
        so the durable input identity every later question is held against is
        written by the operation that owns it.

        THE HALF THAT IS SETUP IS THE FIXTURE'S, and it is the owning suite's
        own device: `tests.job_manager.test_review_driver.DriverCase.attempt`
        writes the four-part assignment identity directly, because activating
        one needs a minted Authority session this harness does not compose.
        `assignment_workspace` is allocated for the same stated reason -- a
        worker cannot have written into roots that were never created.
        """
        from baton_v12.worker_manager import attempts as recorder
        from baton_v12.worker_manager import workspaces

        given = worker.given
        recorder.record_attempt(
            control, attempt_id=attempt_id,
            adapter_name=given["adapter_name"],
            adapter_digest=given["adapter_digest"],
            profile_digest=given["profile_digest"],
            input_digest=input_digest,
            policy_digest=given["input_manifest"]["policy_digest"],
            image_digest=given["image_digest"])
        control._connection.execute(
            "UPDATE attempts SET work_id = ?, authority_uuid = ?, "
            "assignment_participant = ?, assignment_generation = 1, "
            "assignment_claim_event_seq = 1, assignment_principal = ?, "
            "assignment_scope = 'scope:deployment', assignment_role = "
            "'role', assignment_grant = 'grant', "
            "assignment_policy_generation = 1 WHERE runtime_attempt_id = ?",
            (given["input_manifest"]["work_ref"]["work_id"],
             self.config["authority_uuid"], given["participant"],
             given["principal"], attempt_id))
        workspaces.assignment_workspace(
            self.group, self.config["workspace_storage"], attempt_id,
            control=control)
        return attempt_id

    def completed_attempt(self, control, attempt_id):
        control._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'quiescent', worker_disposition = 'completed' WHERE "
            "runtime_attempt_id = ?", ("runtime-" + attempt_id, attempt_id))

    def pool_worker(self, control, role, tasks, *, index=None,
                    deployment=None, **changed):
        """One pool worker, composed far enough to prepare a stage.

        `worker_for` builds a `_SingleWorker` through `__new__` for the
        preflight questions; this needs more of the object -- `_mounted`,
        `_input` and `_adapter` all read the control store -- so the same
        construction is given the three attributes those three read, plus the
        per-Job reader the pool wires and the stage composition. Nothing
        about the held configuration is invented: it is `_held` over
        `configured_as`, the same deployment document the pool composes.
        """
        given, _manifest = self.configured_as(
            {"implementation": 0, "review": 1}[role] if index is None
            else index, role, **changed)
        if deployment is not None:
            given = dict(given, **deployment)
        self.installed_manifest = self.held(given)["input_manifest"]
        worker = single_worker._SingleWorker.__new__(
            single_worker._SingleWorker)
        worker.given = self.held(given)
        worker.control = control
        worker.group = self.group
        worker.job_task = lambda *, job_id: tasks.get(job_id)
        worker.judgment_document = None
        worker.stage = None
        # THE TWO SEAMS `_adapter` COMPOSES OVER, and nothing more. Nothing
        # in these cases starts a runtime -- what is asked of the adapter is
        # the identity it describes -- but the composition reads the engine
        # callable and the credential home, so both are the deployment's own
        # values rather than stand-ins of this file's.
        worker.engine = Engine()
        # AND `None` FOR THE GRANTED CREDENTIAL HOME, which is the
        # adapter's own documented default: "absent, this adapter derives its
        # own exactly as before". The split home is a capability a credential
        # grant produces, and these cases make no grant -- handing a PATH
        # there is refused, correctly, because a path is not that capability.
        worker.credential_home = None
        return worker

    def mounted(self, worker, composition, stage):
        """The roots and boundary THIS ROLE'S container is started over.

        `_SingleWorker._mounted` allocates the roots and then calls
        `stage.mount`, which is the accepted grant or attachment and the
        accepted boundary composer behind it. Driven here through the
        composition rather than around it.
        """
        from baton_v12.worker_manager import workspaces

        roots = workspaces.assignment_workspace(
            self.group, self.config["workspace_storage"],
            stage["attempt_id"], control=worker.control)
        composed = composition.mount(worker, stage, roots)
        return composed["roots"], composed["boundary"]

    def delivered_through(self, worker, composition, stage, *, offer=None):
        """`_prepared`'s own sequence for one stage: mount, assign, publish.

        The three calls are `_prepared`'s, in `_prepared`'s order, with
        `_prepared`'s operands: `_mounted` through the stage composition, the
        real `_assignment_manifest` over the claimed-offer row, and the real
        `_input` -- which publishes the task and the protocol pair and
        freezes the root. What is NOT run is everything after the input root:
        the launch document, the credential delivery and the runtime start,
        which need an Authority session this harness does not mint. That
        boundary is named in PROGRESS rather than implied.
        """
        given = worker._given_for(stage)
        roots, boundary = self.mounted(worker, composition, stage)
        assignment = single_worker._assignment_manifest(
            given, offer or self.row_for(worker), stage["attempt_id"],
            stage["offer_id"])
        manifest = worker._input(roots, assignment, boundary, stage)
        return {"roots": roots, "boundary": boundary, "given": given,
                "manifest": manifest}

    def published_task(self, roots):
        with open(os.path.join(roots["inputs"],
                               single_worker.TASK_DOCUMENT), "rb") as reading:
            return reading.read()

    def row_for(self, worker):
        """The claimed-offer row `_assignment_manifest` reads."""
        return dict(worker.given["input_manifest"]["work_ref"],
                    participant=worker.given["participant"],
                    claim_generation=1,
                    claim_principal=worker.given["principal"],
                    claim_scope="scope:deployment", claim_role="baton.impl",
                    claim_grant="direct", claim_policy_generation=1,
                    claim_event_seq=1, accepted_at=fixtures.NOW,
                    decided_at=fixtures.NOW)


class TheRuntimePathDeliversAndRecoversOneIdentity(SingleWorkerCase):
    """W363066 review 2026-10-26T20-45Z: THE RUNTIME'S OWN ENTRYPOINTS.

    Everything above this drives the preparation sequence; the reviewer's
    remaining objection was that none of it invokes `reconcile`, the launch,
    or the recovery and cleanup entrypoints -- so it could not establish that
    the runtime connects them. These cases do.

    WHAT IS REAL HERE. The production bootstrap composition
    (`single_worker.operations_from`), a real Job store with a real
    submission, a real control store, and the serving loop's own
    `reconcile`/`status` -- which offer, claim, reconcile the claimed stage
    through `_prepared`, publish the input root through `_input`, record the
    attempt, compose the launch adapter and start it. The engine is
    `test_single_worker.Engine`, the suite's deterministic process boundary,
    and the credential provider is the same fixture every case in that suite
    uses. Nothing in a container answers, which is why `commanded` stops at
    `waiting`.

    WHAT IS SUBSTITUTED, AND ONLY THIS. The per-Job task READER on the
    composed worker, because a Job store row carrying a `task_document` is
    written by `creation.create_template_job`, which needs an installed
    deployment and a Work binding this suite has neither of.
    `TheReaderOverARealStore` above drives `job_task_reader` against a real
    store, so the read is not taken on trust either -- but these cases are
    about what the RUNTIME does with the answer.

    THE REVIEW ROLE IS NOT THIS CLASS. An earlier draft of this docstring
    named a class that was removed before the candidate was written, which
    claimed coverage nothing performed; the review-role runtime delivery is
    `TheReviewRoleRuntimeIsDeliveredTheSameTask` below, over its own
    deployment and its upstream frozen checkpoint.
    """

    def delivered(self, statement="The requested runtime task."):
        """The composed per-Job delivery for this deployment's one Job."""
        installed = single_worker._held(self.config)
        selection = {
            "job_id": "job-a", "statement": statement,
            "acceptance": ["the delivered task is accepted"],
            "scope": {"work": ["v12/python/tools/single_worker.py"],
                      "tests": []},
            "template_version":
                "baton.v12.job-template.implementation-review/1",
            "work_id": fixtures.WORK_A}
        return job_task.per_job_delivery(installed["task_bytes"],
                                         installed["input_manifest"],
                                         selection)

    def submission_for(self, made):
        """The submission a created Job would carry: ITS OWN identity.

        `_matches` holds a Job's `input_digest` to the identity of the
        document the stage is served under, so a Job delivered its own task
        declares its own identity -- which is exactly what
        `creation.submission_for_admission` writes and `_task_agrees`
        refuses to let drift.
        """
        return fixtures.submission(jobs=[fixtures.job(
            input_digest=job_input_identity(made["input_manifest"]),
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[fixtures.stage(work_id=fixtures.WORK_A,
                                   profile_name="reference",
                                   profile_digest=fixtures.PROFILE)])])

    def running(self, incarnation="delivered-1", made=None):
        """One started attempt over a delivered task, through `reconcile`."""
        made = made or self.delivered()
        job, control = self.stores(incarnation)
        engine = Engine()
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        operations._worker.job_task = lambda *, job_id: (
            made["task_document"] if job_id == "job-a" else None)
        submit(job, self.submission_for(made))
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        attempt = stage["attempt_id"]
        return {"made": made, "job": job, "control": control,
                "engine": engine, "operations": operations,
                "worker": operations._worker, "stage": stage,
                "attempt": attempt,
                "roots": workspaces.assignment_workspace(
                    operations._worker.group, self.storage, attempt,
                    control=control)}

    def test_the_started_attempt_is_recorded_against_the_delivered_input(self):
        """THE RECORD AND THE DISK, after a real start."""
        held = self.running()
        delivered = job_input_identity(held["made"]["input_manifest"])
        installed = job_input_identity(self.manifest)
        self.assertNotEqual(delivered, installed)
        self.assertEqual(
            attempts.recorded_input_of(held["control"], held["attempt"]),
            held["made"]["input_manifest"]["manifest_digest"])
        with open(os.path.join(held["roots"]["inputs"],
                               single_worker.TASK_DOCUMENT), "rb") as reading:
            self.assertEqual(reading.read(),
                             held["made"]["task_document"].encode("utf-8"))
        self.assertEqual(len(held["engine"].starts), 1)

    def test_the_stageless_adapter_describes_the_delivered_input(self):
        """THE CORRECTION, asked of the function the recovery callers use.

        A recovery caller has roots and an attempt and no stage. Before this
        Work the adapter it built carried the INSTALLED manifest digest and
        the installed `outputs` -- and `OciAdapter.seal` stamps that digest
        into the frozen result, so a per-Job attempt would have been sealed
        with provenance naming an input it was never given.
        """
        held = self.running()
        manifest = held["made"]["input_manifest"]
        adapter = held["worker"]._adapter(held["roots"], None, None, None,
                                          attempt_id=held["attempt"])
        self.assertEqual(adapter.input_manifest_digest,
                         manifest["manifest_digest"])
        self.assertNotEqual(adapter.input_manifest_digest,
                            self.manifest["manifest_digest"])
        # `declared_outputs` is keyed by name, owned by `sealing`.
        self.assertEqual(sorted(adapter.declared_outputs),
                         sorted(one["name"] for one in manifest["outputs"]))

    def test_the_recovery_entrypoint_identifies_the_delivered_attempt(self):
        """`refresh_runtime`, the serving loop's own runtime read.

        It is given `{"attempt_id": ...}` and nothing else -- no `job_id` --
        so it is the exact caller that could not resolve a Job's task, and it
        reaches the engine through the stage-less adapter.
        """
        held = self.running()
        refreshed = held["worker"].refresh_runtime(
            {"attempt_id": held["attempt"]})
        self.assertIsNotNone(refreshed)
        self.assertEqual(refreshed, {"execution_runtime": "running"})
        # AND THE ENGINE WAS ASKED, rather than an answer manufactured here.
        self.assertTrue([one for one in held["engine"].vectors
                         if one[1] in ("ps", "inspect")])

    def reopened(self, root):
        """Re-open a frozen root far enough to replace what is in it."""
        os.chmod(os.path.dirname(root), 0o755)
        os.chmod(root, 0o755)
        for name in os.listdir(root):
            place = os.path.join(root, name)
            if not os.path.isdir(place):
                os.chmod(place, 0o644)
        return root

    def test_an_attempt_whose_root_HALF_was_substituted_refuses(self):
        """ONE DOCUMENT REPLACED, which is a MISMATCHED pair.

        W363066 review at handoff E363761 corrected this case's own claim: it
        writes `input.json` only, so `assignment.json` still names the
        delivered manifest and `read_input_root` refuses the pair itself
        before any provenance question is asked. That is a real and separate
        thing to refuse -- half of one delivery beside half of another -- and
        it is kept as exactly that. The COMPLETE self-consistent substitution
        is the case below, and it is the one that needed writing.
        """
        held = self.running()
        root = self.reopened(held["roots"]["inputs"])
        with open(os.path.join(root, "input.json"), "w") as writing:
            json.dump(self.manifest, writing)
        with self.assertRaises(ContractRefusal) as refused:
            held["worker"]._adapter(held["roots"], None, None, None,
                                    attempt_id=held["attempt"])
        self.assertEqual((refused.exception.category, refused.exception.code),
                         ("integrity", "digest"))
        # AND IT IS THE PAIR RULE THAT REFUSED, not the record.
        with self.assertRaises(ContractRefusal) as read:
            workspaces.read_input_root(root)
        self.assertIn("two halves of two deliveries", str(read.exception))
        self.assertEqual(len(held["engine"].starts), 1)

    def test_an_attempt_whose_WHOLE_root_was_substituted_refuses(self):
        """A COMPLETE, INTERNALLY VALID PAIR, refused by the RECORD alone.

        Both documents are replaced by one consistent installed delivery
        minted for THIS attempt and THIS assignment: the assignment manifest
        is rebuilt against the installed input digest the way
        `_assignment_manifest` builds one, so `check_input_pair` accepts the
        pair, `read_input_root` accepts the root, the activated assignment
        still agrees in all four parts and the runtime attempt id still
        agrees. Nothing about the root is wrong with itself.

        The durable record is the only thing that disagrees, and it is
        enough. A manager that read the root on its own authority would have
        mounted a substituted delivery and sealed a result naming it.
        """
        held = self.running()
        root = self.reopened(held["roots"]["inputs"])
        with open(os.path.join(root, "assignment.json")) as reading:
            assignment = json.load(reading)
        self.assertEqual(assignment["input_manifest_digest"],
                         held["made"]["input_manifest"]["manifest_digest"])
        assignment["input_manifest_digest"] = self.manifest["manifest_digest"]
        assignment.pop("manifest_digest")
        assignment["manifest_digest"] = digest(assignment)
        # THE PRODUCT'S OWN PAIR RULE ACCEPTS IT. If this refused, the case
        # below would be measuring a malformed fixture rather than provenance.
        check_input_pair(self.manifest, assignment)
        for name, document in (("input.json", self.manifest),
                               ("assignment.json", assignment)):
            with open(os.path.join(root, name), "w") as writing:
                json.dump(document, writing)
        given, delivered = workspaces.read_input_root(root)
        self.assertEqual(given["manifest_digest"],
                         self.manifest["manifest_digest"])
        self.assertEqual(delivered["runtime_attempt_id"], held["attempt"])
        # AND THE MANAGER STILL REFUSES.
        with self.assertRaises(ContractRefusal) as refused:
            held["worker"]._adapter(held["roots"], None, None, None,
                                    attempt_id=held["attempt"])
        self.assertEqual((refused.exception.category, refused.exception.code),
                         ("integrity", "digest"))
        self.assertIn("not claimed against", str(refused.exception))
        self.assertEqual(len(held["engine"].starts), 1)
        # AND THE RECOVERY PATH CONTAINS IT rather than starting anything.
        self.assertIsNone(held["worker"]._naming(held["attempt"]))
        self.assertEqual(len(held["engine"].starts), 1)

    def test_a_removed_root_refuses_rather_than_substituting_the_installed(
            self):
        """A ROOT THAT CANNOT BE PROVED IS NOT ANSWERED FROM ELSEWHERE."""
        held = self.running()
        root = held["roots"]["inputs"]
        os.chmod(root, 0o755)
        os.chmod(os.path.join(root, "input.json"), 0o644)
        os.remove(os.path.join(root, "input.json"))
        with self.assertRaises(ContractRefusal):
            held["worker"]._adapter(held["roots"], None, None, None,
                                    attempt_id=held["attempt"])
        # AND THE RECOVERY PATH CONTAINS IT. `_naming` is the one adapter
        # composition whose contract is an answer rather than a raise: a
        # failure already on its way out must not become a retry loop.
        self.assertIsNone(held["worker"]._naming(held["attempt"]))

    def test_an_installed_attempt_with_no_root_still_reconciles(self):
        """THE PRESERVED PATH, and it must not acquire a new failure.

        An attempt recorded against the installed input needs no root read at
        all, so cleanup after the root is gone still composes an adapter --
        which is what every Job before this Work does and what a cleanup owes
        an ending.
        """
        made = self.delivered()
        job, control = self.stores("installed-1")
        engine = Engine()
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        operations._worker.job_task = lambda *, job_id: None
        submit(job, self.submission)
        stage = self.commanded(job, operations)["jobs"][0]["stages"][0]
        attempt = stage["attempt_id"]
        roots = workspaces.assignment_workspace(
            operations._worker.group, self.storage, attempt, control=control)
        self.assertEqual(
            attempts.recorded_input_of(control, attempt),
            self.manifest["manifest_digest"])
        # The composition FREEZES the root 0555, so a case that removes one
        # re-opens it first -- the same reason `writable` exists above.
        os.chmod(os.path.dirname(roots["inputs"]), 0o755)
        os.chmod(roots["inputs"], 0o755)
        for name in os.listdir(roots["inputs"]):
            place = os.path.join(roots["inputs"], name)
            os.chmod(place, 0o755 if os.path.isdir(place) else 0o644)
        shutil.rmtree(roots["inputs"])
        adapter = operations._worker._adapter(roots, None, None, None,
                                             attempt_id=attempt)
        self.assertEqual(adapter.input_manifest_digest,
                         self.manifest["manifest_digest"])
        del made
        # AND NOT BY REACHING THE DISK. `workspaces.assignment_workspace`
        # independently refuses a missing prepared root, so the callers that
        # revalidate roots never arrive here with one -- which is why this
        # must not add a SECOND refusal for an attempt that owns no other
        # input: `_naming` composes its paths by derivation and would then
        # answer `None` for every ordinary cleanup.
        self.assertFalse(os.path.exists(roots["inputs"]))

    def test_a_stage_that_resolves_the_wrong_input_refuses(self):
        """THE OTHER ROUTE TO THE SAME WRONG ANSWER, closed.

        `refresh_runtime` is handed `{"attempt_id": ...}`, which carries no
        `job_id` -- so a stage-scoped caller given that shape would resolve
        the INSTALLED document and describe a delivered attempt with it. The
        recorded digest decides, so passing it as a stage refuses instead.
        """
        held = self.running()
        with self.assertRaises(ContractRefusal) as refused:
            held["worker"]._adapter(held["roots"], None, None, None,
                                    stage={"attempt_id": held["attempt"]},
                                    attempt_id=held["attempt"])
        self.assertEqual((refused.exception.category, refused.exception.code),
                         ("integrity", "digest"))
        self.assertIn(held["made"]["input_manifest"]["manifest_digest"],
                      str(refused.exception))


class ARestartAdoptsTheDeliveredAttempt(SingleWorkerCase):
    """W363066 review at handoff E363761, scenario 3: CRASH AND RESTART.

    `TheProductionCompositionIsRestartSafe` crashes the production
    composition at each of its own checkpoints, restarts it over the same
    durable state and proves one launch and one claimed offer. This runs the
    same machinery for an attempt that owns a REQUESTED task, and asks the
    questions that machinery cannot: whether the second incarnation adopts
    the same delivered identity, or quietly re-prepares the attempt against
    the installed one.

    IT IS A REAL RESTART. The first composition dies inside the operation at
    the named checkpoint -- no unwinding of the durable state -- and the
    second is a fresh `operations_from` over fresh store handles with a new
    incarnation, which is what a restarted deployment is.

    THE TWO HELPERS ARE BORROWED AND NOT INHERITED, for the reason the
    reviewer gave this suite once already: subclassing a case class re-runs
    its assertions under this name, which is noise at best.

    WHAT THESE CASES DO NOT CLAIM, stated because the review asked for the
    limit exactly: every crash point here is BEFORE the engine is asked to
    start anything. The six are `claimed`, `attempt`, `boundary`, `input`,
    `manifest` and `credential`, and the engine's one launch happens after
    all of them -- so what is proved is that a restart re-prepares and
    adopts the same delivered identity and launches ONCE, not that a crash
    AFTER an engine-start effect is recovered. `prepared`, `launch` and
    `runtime` are checkpoints this one-worker loop does not reach, so no case
    here can crash between the start vector and its record.
    """

    delivered = TheRuntimePathDeliversAndRecoversOneIdentity.delivered
    submission_for = TheRuntimePathDeliversAndRecoversOneIdentity.submission_for

    # THE POINTS THIS DEPLOYMENT ACTUALLY REACHES, which is not every name
    # `_prepared` can checkpoint: `prepared`, `launch` and `runtime` sit in
    # branches a one-worker bootstrap serving loop does not take, and a case
    # that listed them would be asserting a crash that never happens.
    #
    # AND ONE POINT PER CASE, which is not a style choice. `self.stores`
    # re-opens ONE pair of store files under a new incarnation and the attempt
    # id is derived from the stage, so a loop over points inside one test
    # would find the second point's work already durably done and never reach
    # it -- a subtest that passes by not running. A first draft did exactly
    # that and three of its points were silently inert.

    def crashed_then_restarted(self, point, made, *, resumed_task=None):
        """One crash at `point` and one restart, both serving one Job."""
        engine = Engine()
        job, control = self.stores("delivered-before-" + point)
        submit(job, self.submission_for(made))
        crashed = []

        def checkpoint(name):
            if name == point and not crashed:
                crashed.append(name)
                raise RuntimeError("fixture process stopped")

        first = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=checkpoint)
        first._worker.job_task = lambda *, job_id: (
            made["task_document"] if job_id == "job-a" else None)
        with self.assertRaisesRegex(RuntimeError, "process stopped"):
            for _ in range(6):
                reconcile(job, first, now=fixtures.NOW)
        self.assertEqual(crashed, [point])
        first.close()
        job.close()
        control.close()

        resumed_job, resumed_control = self.stores("delivered-after-" + point)
        resumed = self.operations(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        held = resumed_task or made["task_document"]
        resumed._worker.job_task = lambda *, job_id: (
            held if job_id == "job-a" else None)
        return {"engine": engine, "control": resumed_control,
                "job": resumed_job, "operations": resumed,
                "worker": resumed._worker, "made": made}

    def resumed(self, point, made):
        """The restart driven to a commanded worker, and what it adopted."""
        held = self.crashed_then_restarted(point, made)
        stage = self.commanded(held["job"], held["operations"])[
            "jobs"][0]["stages"][0]
        held["stage"] = stage
        held["attempt"] = stage["attempt_id"]
        held["roots"] = workspaces.assignment_workspace(
            held["worker"].group, self.storage, held["attempt"],
            control=held["control"])
        return held

    def adopted_the_delivered_identity(self, point):
        """ONE LAUNCH, ONE OFFER, AND ONE DELIVERED IDENTITY."""
        made = self.delivered("The task that survives a restart.")
        identity = made["input_manifest"]["manifest_digest"]
        self.assertNotEqual(identity, self.manifest["manifest_digest"])
        held = self.resumed(point, made)
        # THE RESTART MACHINERY'S OWN TWO QUESTIONS.
        self.assertEqual(len(held["engine"].starts), 1)
        self.assertEqual(
            len(claimed_offers_for(held["control"], held["attempt"])), 1)
        # AND THIS WORK'S THREE. The attempt is RECORDED against the
        # delivered input; the ROOT on disk still carries the delivered task;
        # and the ADAPTER a recovery would now build over that root describes
        # the delivered input rather than the installed one.
        self.assertEqual(
            attempts.recorded_input_of(held["control"], held["attempt"]),
            identity)
        with open(os.path.join(held["roots"]["inputs"],
                               single_worker.TASK_DOCUMENT), "rb") as reading:
            self.assertEqual(reading.read(),
                             made["task_document"].encode("utf-8"))
        adapter = held["worker"]._adapter(held["roots"], None, None, None,
                                         attempt_id=held["attempt"])
        self.assertEqual(adapter.input_manifest_digest, identity)
        # AND THE RECOVERY ENTRYPOINT ITSELF, over the adopted runtime.
        self.assertEqual(
            held["worker"].refresh_runtime({"attempt_id": held["attempt"]}),
            {"execution_runtime": "running"})
        return held

    def test_a_crash_before_the_claim_resumes_on_the_delivered_identity(self):
        """THE EARLY CONTROL: nothing has been prepared yet."""
        self.adopted_the_delivered_identity("claimed")

    def test_a_crash_at_the_recorded_attempt_resumes_delivered(self):
        """The point where `record_attempt` has fixed the input digest."""
        self.adopted_the_delivered_identity("attempt")

    def test_a_crash_at_the_boundary_resumes_delivered(self):
        self.adopted_the_delivered_identity("boundary")

    def test_a_crash_at_the_published_input_resumes_delivered(self):
        """THE ONE THAT MATTERS MOST: the root is on disk, half-trusted."""
        self.adopted_the_delivered_identity("input")

    def test_a_crash_at_the_retained_manifest_resumes_delivered(self):
        self.adopted_the_delivered_identity("manifest")

    def test_a_crash_at_the_credential_resumes_delivered(self):
        self.adopted_the_delivered_identity("credential")

    def test_a_restart_that_would_deliver_another_task_publishes_nothing(self):
        """AND THE ADOPTION IS NOT A RE-PREPARATION.

        The first incarnation publishes the root and dies after it; the
        second is given a DIFFERENT rendering for the same Job. WHAT ACTUALLY
        HAPPENS, read from the durable state rather than assumed: the stage
        does not progress, nothing is launched, the root still carries the
        first rendering and the attempt is still recorded against the first
        identity.

        AND THE REFUSAL IS EARLIER THAN I FIRST WROTE. A drafted version of
        this case expected `_proved_task` to raise out of `reconcile`; it does
        not get that far. The Job declares the FIRST rendering's input
        identity, so the re-preparation is refused by the identity comparison
        in `_matches` before any publication is attempted, and the serving
        loop treats a worker that does not match as one that cannot serve
        this stage -- no durable preparation failure, no exception, and
        nothing on disk touched. `_proved_task`'s own refusal over drifted
        bytes is asserted directly by `RestartProvesWhatWasPublished` above;
        this case is about what the LOOP does, and the answer is that the
        attempt stays where it was.
        """
        made = self.delivered("The first rendering.")
        other = self.delivered("A SECOND rendering of the same Job.")
        self.assertNotEqual(other["task_document"], made["task_document"])
        self.assertNotEqual(other["input_manifest"]["manifest_digest"],
                            made["input_manifest"]["manifest_digest"])
        held = self.crashed_then_restarted(
            "credential", made, resumed_task=other["task_document"])
        for _ in range(6):
            reconcile(held["job"], held["operations"], now=fixtures.NOW)
        stage = status(held["job"], held["operations"],
                       observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "claimed")
        self.assertEqual(len(held["engine"].starts), 0)
        self.assertEqual(
            attempts.recorded_input_of(held["control"], stage["attempt_id"]),
            made["input_manifest"]["manifest_digest"])
        roots = workspaces.assignment_workspace(
            held["worker"].group, self.storage, stage["attempt_id"],
            control=held["control"])
        with open(os.path.join(roots["inputs"],
                               single_worker.TASK_DOCUMENT), "rb") as reading:
            self.assertEqual(reading.read(),
                             made["task_document"].encode("utf-8"))
        # AND THE COMPARISON THAT DID IT, asked directly so the case names a
        # mechanism rather than an outcome.
        with self.assertRaises(ContractRefusal) as refused:
            held["worker"]._matches(
                dict(stage, kind="implementation"),
                {"job_id": "job-a",
                 "input_digest": job_input_identity(made["input_manifest"]),
                 "policy_digest": fixtures.POLICY_DIGEST})
        self.assertIn("another bootstrap input", str(refused.exception))


class TwoRequestedJobsThroughOneServingLoop(SingleWorkerCase):
    """W363066 review at handoff E363761, scenario 1: TWO JOBS, ONE LOOP.

    `TwoJobsOnOneWorkerGetTheirOwnBytes` asks this of the composition and
    `test_two_jobs_prepare_independently_on_one_worker` asks it of the
    preparation sequence. Neither drives the SERVING LOOP, and the loop is
    where a shared worker object actually serves two Jobs one after the
    other: one deployment, one worker, one pair of stores, two requested
    tasks, two attempts, two input roots.

    THE FIRST JOB IS REALLY FINISHED, because a one-worker deployment serves
    one stage at a time and the second Job is `queued` until the first ends.
    So the first attempt is driven to an ANSWERED TERMINAL by the real
    in-image program over the real exchange this deployment mounted -- the
    same `baton_worker.serve_exchange` entry `TheAnsweredEndingRunsThroughThe
    RealOwners` uses -- and the ending is the Worker Manager's own: seal,
    intake, retention, Authority pass and cleanup, driven by `sweep`. Only
    the engine and the in-image provider stand in, exactly as there.
    """

    quiescing = TheAnsweredEndingRunsThroughTheRealOwners.quiescing

    def requested(self, job_id, statement, work_id):
        installed = single_worker._held(self.config)
        return job_task.per_job_delivery(
            installed["task_bytes"], installed["input_manifest"],
            {"job_id": job_id, "statement": statement,
             "acceptance": [f"{job_id} is accepted"],
             "scope": {"work": ["v12/python/tools/single_worker.py"],
                       "tests": []},
             "template_version":
                 "baton.v12.job-template.implementation-review/1",
             "work_id": work_id})

    def two_jobs(self):
        """One submission, two Jobs, each declaring its OWN input identity."""
        first = self.requested("job-a", "The FIRST requested task.",
                               fixtures.WORK_A)
        # BOTH ON THIS DEPLOYMENT'S WORK, and that is not a convenience.
        # `_matches` holds a stage's `work_id` to the one this worker's
        # manifest declares, so a second Job on another Work is never
        # servable by this worker at all -- a first draft used WORK_B and
        # the second Job sat `queued` for ever, proving nothing. Two Jobs
        # over one Work is what a shared pool actually serves.
        second = self.requested("job-b", "The SECOND requested task.",
                                fixtures.WORK_A)
        self.assertNotEqual(first["task_document"], second["task_document"])
        submission = {
            "schema": "baton.v12.job-submission/1",
            "submission_id": "sub-two",
            "jobs": [
                fixtures.job(
                    job_id="job-a",
                    input_digest=job_input_identity(first["input_manifest"]),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage(work_id=fixtures.WORK_A,
                                           profile_name="reference",
                                           profile_digest=fixtures.PROFILE)]),
                fixtures.job(
                    job_id="job-b",
                    input_digest=job_input_identity(second["input_manifest"]),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage(work_id=fixtures.WORK_A,
                                           profile_name="reference",
                                           profile_digest=fixtures.PROFILE)])]}
        return first, second, submission

    def stage_named(self, job, operations, job_id):
        for one in status(job, operations,
                          observed_at=fixtures.NOW)["jobs"]:
            if one["job_id"] == job_id:
                return one["stages"][0]
        self.fail(f"no projected stage for {job_id}")

    def served(self, job, operations, job_id):
        """Tick until this Job's stage has a commanded worker."""
        for _ in range(8):
            reconcile(job, operations, now=fixtures.NOW)
            stage = self.stage_named(job, operations, job_id)
            if stage["state"] == "waiting":
                return stage
        self.fail(f"{job_id} never reached a commanded worker")

    def published(self, control, worker, attempt_id):
        roots = workspaces.assignment_workspace(
            worker.group, self.storage, attempt_id, control=control)
        with open(os.path.join(roots["inputs"], single_worker.TASK_DOCUMENT),
                  "rb") as reading:
            return roots, reading.read()

    def answered(self, job, control, operations, stage, made):
        """Drive the real in-image program to an answered terminal.

        The launch delivery is ADOPTED with this Job's own execution context,
        whose `runtime_input_digest` is the DELIVERED manifest digest --
        adoption compares canonical bytes, so a context naming the installed
        input would refuse here rather than quietly working.
        """
        import baton_worker
        import scripted_agent

        attempt_id = stage["attempt_id"]
        home = os.path.join(self.storage, attempt_id)
        delivered = single_worker.launch.adopt(
            self.config["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=self.config["launch_contract"], role="implementation",
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            job_execution=single_worker.job_execution_reader(job)(
                job_id=stage["job_id"], attempt_id=attempt_id,
                runtime_input_digest=made["input_manifest"][
                    "manifest_digest"],
                runtime_policy_digest=self.config["policy_digest"]),
            workspace_group=single_worker.configured_workspace_group(control))
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", os.path.join(home, "inputs")),
                (baton_worker, "OUTPUT_ROOT", os.path.join(home, "workspace")),
                (scripted_agent, "OUTPUT_ROOT",
                 os.path.join(home, "workspace"))):
            held = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, held)
        self.assertEqual(
            baton_worker.serve_exchange(
                scripted_agent.ScriptedAgent(), delivered.document,
                delivered.document["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root), 0)
        report = sweep(job, operations, now=fixtures.NOW)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["spoken"]],
                         [("conclude", "performed")])
        return report

    def test_the_served_job_gets_its_own_bytes_and_the_second_waits(self):
        """WHAT ONE BOOTSTRAP LOOP CAN ACTUALLY SERVE, measured.

        This case was written to serve BOTH Jobs through one loop and it
        cannot, for two structural reasons it establishes rather than
        assumes -- so it asserts what the loop does do, and the second half
        of that scenario belongs to the POOL. See PROGRESS.

          `_matches` holds a stage's `work_id` to the one THIS worker's
          manifest declares, so a second Job on another Work is never
          servable by this deployment: with `WORK_B` the second stage stays
          `queued` for ever and a case that stopped there would be asserting
          a fixture.
          And two Jobs over ONE Work do not finish the scenario either: the
          first ending passes the Work on to its `review_route` -- which is
          the ending's own reported act -- so the second stage is OFFERED and
          its claim never completes. Measured here over eight further ticks
          after a real ending, and over thirty in a probe: `offered`, no
          recorded attempt, no roots, no second launch.

        WHAT IS PROVED. One shared worker object, the real serving loop, a
        requested task delivered to the attempt it belongs to, a real
        in-image worker turn, the real ending through `sweep`, and a second
        requested Job that is NEVER delivered the first one's bytes.
        """
        first, second, submission = self.two_jobs()
        installed = self.manifest["manifest_digest"]
        identity = first["input_manifest"]["manifest_digest"]
        self.assertEqual(
            len({identity, second["input_manifest"]["manifest_digest"],
                 installed}), 3)

        engine = self.quiescing()
        job, control = self.stores("two-requested-jobs")
        submit(job, submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        table = {"job-a": first["task_document"],
                 "job-b": second["task_document"]}
        # ONE READER OVER BOTH JOBS, which is what a deployment has: the
        # worker object is shared and the answer is per Job.
        operations._worker.job_task = lambda *, job_id: table.get(job_id)

        held = self.served(job, operations, "job-a")
        self.assertEqual(self.stage_named(job, operations, "job-b")["state"],
                         "queued")
        self.assertEqual(
            attempts.recorded_input_of(control, held["attempt_id"]),
            identity)
        roots, published = self.published(
            control, operations._worker, held["attempt_id"])
        self.assertEqual(published, first["task_document"].encode("utf-8"))
        self.assertEqual(len(engine.starts), 1)
        adapter = operations._worker._adapter(
            roots, None, None, None, attempt_id=held["attempt_id"])
        self.assertEqual(adapter.input_manifest_digest, identity)

        # THE FIRST JOB IS REALLY ENDED, through the real in-image program
        # and the Worker Manager's own ending.
        self.answered(job, control, operations, held, first)
        self.assertEqual(self.stage_named(job, operations, "job-a")["state"],
                         "completed")

        # AND THE SECOND IS STILL QUEUED, for the reason in the docstring --
        # not because anything delivered it the wrong bytes.
        for _ in range(8):
            reconcile(job, operations, now=fixtures.NOW)
            sweep(job, operations, now=fixtures.NOW)
        second_stage = self.stage_named(job, operations, "job-b")
        self.assertEqual(second_stage["state"], "offered")
        self.assertIsNone(
            attempts.recorded_input_of(control, second_stage["attempt_id"]))
        self.assertFalse(os.path.exists(os.path.join(
            self.storage, second_stage["attempt_id"])))
        # THE FIRST JOB'S ROOT IS UNTOUCHED BY ANY OF IT.
        with open(os.path.join(roots["inputs"],
                               single_worker.TASK_DOCUMENT), "rb") as reading:
            self.assertEqual(reading.read(),
                             first["task_document"].encode("utf-8"))
        self.assertEqual(len(engine.starts), 1)
        # AND THE TWO JOBS ARE ONE WORK'S WITH TWO IDENTITIES.
        self.assertNotEqual(
            job_input_identity(first["input_manifest"]),
            job_input_identity(second["input_manifest"]))
        self.assertEqual(
            {first["input_manifest"]["work_ref"]["work_id"],
             second["input_manifest"]["work_ref"]["work_id"]},
            {self.manifest["work_ref"]["work_id"]})


class TheReviewRoleRuntimeIsDeliveredTheSameTask(PoolDeliveryCase):
    """W363066 review at handoff E363761, scenario 2: THE REVIEW ROLE.

    A review attempt is not an implementation attempt with another word on
    it. It mounts somebody else's FROZEN CHECKPOINT read-only beside its own
    writable output, behind a review ATTACHMENT that
    `review_driver.prepare_review` grants against the line's current
    checkpoint -- a different source path from the writable line an
    implementation attempt is granted. So "the requested task reaches the
    review role too" cannot be answered by the implementation path, and this
    class answers it over the real thing:

      a real line, a real writer grant, a real `freeze_checkpoint`, a real
      `prepare_review` against that checkpoint, and the real
      `review_boundary` behind the attachment -- all composed by the real
      `StageComposition` the serving loop composes, with the checkpoint
      profile as the one deterministic seam and NO version control, which
      every case here proves by refusing the process.

    AND THE JOB IS ONE JOB. The same requested task document reaches both
    roles, each role composes its OWN per-Job input manifest from its own
    installed one, and the two Job-scoped identities are equal -- which is
    the whole point of W202663's heterogeneous pool and the reason a Job can
    declare one `input_digest` for three stages.
    """

    def requested(self, job_id, statement):
        """The Job's own task document, composed once for the Job."""
        installed = self.held(self.configured_as(0, "implementation")[0])
        return job_task.per_job_delivery(
            installed["task_bytes"], installed["input_manifest"],
            self.selection(job_id, statement))

    def upstream(self, control, job_id, made):
        """One real implementation round, up to a frozen checkpoint."""
        from baton_v12.worker_manager import freeze_checkpoint

        tasks = {job_id: made["task_document"]}
        worker = self.pool_worker(control, "implementation", tasks)
        composition = self.composition(control, "implementation",
                                       worker_id="impl-worker-1")
        stage = dict(self.stage_for("implementation"), job_id=job_id,
                     attempt_id="writer-attempt-1",
                     stage_id=f"{job_id}/implementation")
        self.attempt_row(
            control, worker, stage["attempt_id"],
            input_digest=worker._given_for(stage)[
                "input_manifest"]["manifest_digest"])
        held = self.delivered_through(worker, composition, stage)
        self.completed_attempt(control, stage["attempt_id"])
        checkpoint = freeze_checkpoint(
            control,
            writer_id=composition._prepared[stage["attempt_id"]]["writer_id"],
            generation=1, profile=self.profile_seam,
            port=self.port_for(worker.given["participant"]))
        return {"worker": worker, "stage": stage, "roots": held["roots"],
                "checkpoint": checkpoint, "given": held["given"],
                "boundary": held["boundary"], "composition": composition}

    def reviewed(self, job_id="job-first", statement="A reviewed task.",
                 *, task=True):
        """One real review attempt over that frozen checkpoint."""
        job, control = self.configured("pool-review")
        self.line_for_job(control, job_id)
        made = self.requested(job_id, statement)
        upstream = self.upstream(control, job_id, made)

        tasks = {job_id: made["task_document"]} if task else {}
        worker = self.pool_worker(control, "review", tasks)
        composition = self.composition(control, "review",
                                       worker_id="review-worker-1")
        stage = dict(self.stage_for("review"), job_id=job_id,
                     attempt_id="review-attempt-1",
                     stage_id=f"{job_id}/review")
        identity = worker._given_for(stage)["input_manifest"]["manifest_digest"]
        self.attempt_row(control, worker, stage["attempt_id"],
                         input_digest=identity)
        held = self.delivered_through(worker, composition, stage)
        return {"job": job, "control": control, "worker": worker,
                "composition": composition, "stage": stage, "made": made,
                "identity": identity, "upstream": upstream, **held}

    def test_the_review_attempt_is_delivered_the_jobs_requested_task(self):
        """THE BYTES IN THE REVIEW ATTEMPT'S OWN INPUT ROOT."""
        held = self.reviewed()
        self.assertEqual(self.published_task(held["roots"]),
                         held["made"]["task_document"].encode("utf-8"))
        # AND THEY ARE NOT THE INSTALLED ONES.
        self.assertNotEqual(
            self.published_task(held["roots"]),
            self.held(self.configured_as(1, "review")[0])["task_bytes"])
        # THE MANIFEST THAT TRAVELS WITH THEM IS THIS ROLE'S OWN, with the
        # human contract naming the delivered bytes.
        manifest = held["manifest"]
        self.assertEqual(manifest["manifest_digest"], held["identity"])
        self.assertEqual(manifest["worker_image_digest"],
                         held["worker"].given["image_digest"])
        self.assertEqual(
            manifest["human_contract"]["content_digest"],
            digest_of_bytes(held["made"]["task_document"].encode("utf-8")))

    def test_one_job_gives_both_roles_one_job_scoped_identity(self):
        """ONE JOB, TWO ROLES, TWO RUNTIME MANIFESTS, ONE IDENTITY."""
        held = self.reviewed()
        review = held["manifest"]
        implementation = held["upstream"]["given"]["input_manifest"]
        self.assertNotEqual(review["manifest_digest"],
                            implementation["manifest_digest"])
        self.assertEqual(job_input_identity(review),
                         job_input_identity(implementation))
        self.assertEqual(review["human_contract"],
                         implementation["human_contract"])

    def test_the_review_mount_is_the_frozen_checkpoint_read_only(self):
        """REVIEW SEMANTICS, from the boundary the manager composed.

        The attachment is the real one `prepare_review` granted against the
        line's current checkpoint, and the boundary behind it is the accepted
        `review_boundary`. What this asserts is that the mount under test is
        that attachment's -- not the writable line an implementation attempt
        is granted -- and that the checkpoint it names is the one the
        upstream round really froze.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.reviewed()
        attempt_id = held["stage"]["attempt_id"]
        prepared = held["composition"]._prepared[attempt_id]
        self.assertEqual(prepared["checkpoint_id"],
                         held["upstream"]["checkpoint"]["checkpoint_id"])
        # THE DURABLE ATTACHMENT, read back through the accepted reader.
        attached = review_cycles.review_for_attempt(
            held["control"], attempt_id=attempt_id, generation=1)
        self.assertEqual(attached["attachment_id"], prepared["attachment_id"])
        self.assertEqual(attached["state"], "active")
        self.assertEqual(attached["checkpoint_id"],
                         held["upstream"]["checkpoint"]["checkpoint_id"])
        self.assertEqual(attached["reviewer_participant"],
                         held["worker"].given["participant"])
        # AND IT IS A DIFFERENT SOURCE PATH FROM THE IMPLEMENTATION'S, which
        # is the half a both-role composition at the configuration level
        # cannot reach: the reviewer is mounted the line's frozen CHECKOUT,
        # the writer was mounted the line itself.
        reviewed_source = str(prepared["boundary"]["boundary"].source)
        wrote_source = str(held["upstream"]["boundary"].source)
        self.assertNotEqual(reviewed_source, wrote_source)
        self.assertIn("checkout", reviewed_source)
        # THE ROOTS THE CONTAINER WOULD BE STARTED OVER ARE THIS ATTEMPT'S.
        self.assertEqual(held["roots"]["inputs"],
                         os.path.join(self.config["workspace_storage"],
                                      attempt_id, "inputs"))

    def test_the_stageless_adapter_over_a_review_attempt_is_the_delivered_one(
            self):
        """AND THE RECOVERY PATH, for the role that was never covered.

        The adapter a review attempt's identification, adoption, cleanup or
        recovery would build carries the DELIVERED manifest digest -- read
        back off the published root and held to the recorded attempt by
        `authorize_input_root`, which is what `_delivered_manifest` does with
        no stage in hand.
        """
        held = self.reviewed()
        adapter = held["worker"]._adapter(
            held["roots"], None, None, None,
            attempt_id=held["stage"]["attempt_id"])
        self.assertEqual(adapter.input_manifest_digest, held["identity"])
        self.assertNotEqual(
            adapter.input_manifest_digest,
            self.held(self.configured_as(1, "review")[0])[
                "input_manifest"]["manifest_digest"])

    def test_a_review_job_with_no_own_task_is_delivered_the_installed_one(self):
        """THE PRESERVED PATH for the review role, through the same mount."""
        held = self.reviewed(task=False)
        installed = self.held(self.configured_as(1, "review")[0])
        self.assertEqual(self.published_task(held["roots"]),
                         installed["task_bytes"])
        self.assertEqual(held["identity"],
                         installed["input_manifest"]["manifest_digest"])


class TwoRequestedJobsThroughOnePool(PoolDeliveryCase):
    """W363066 review at handoff E363761, scenario 1: TWO JOBS, ONE POOL.

    The bootstrap loop cannot express this -- see
    `TwoRequestedJobsThroughOneServingLoop`, which measures why -- because it
    binds one Work and passes that Work on when its one stage ends. A POOL
    serves a Job per line: `StageComposition._prepare` reads
    `deployment.line_for(stage["job_id"])`, which is the whole reason a
    second submitted Job is not forced onto the first one's checkout.

    So this is two Jobs, two lines, ONE worker object with ONE held
    configuration and ONE reader, and the question is whether each attempt
    gets its own requested bytes and its own identity with nothing of the
    other's in it -- and whether the shared configuration survives both.
    """

    def requested(self, job_id, statement):
        installed = self.held(self.configured_as(0, "implementation")[0])
        return job_task.per_job_delivery(
            installed["task_bytes"], installed["input_manifest"],
            self.selection(job_id, statement))

    # TWO JOBS ARE TWO WORKS AND TWO LINES, and that is the product's rule
    # rather than this fixture's convenience: `create_line` refuses a second
    # line for one Authority and Work ("this Authority and Work already own a
    # line under different immutable operands"), and a pool worker's manifest
    # declares the Work its stages belong to. So a pool serving two Jobs is
    # two deployments over ONE control store, one storage, one workspace
    # group and -- here -- ONE shared reader table holding BOTH Jobs' tasks,
    # which is what makes a crossed delivery possible to observe at all.
    WORKS = {0: fixtures.WORK_A, 1: fixtures.WORK_B}

    def both(self):
        """Two Jobs prepared through one pool, in one loop's order."""
        job, control = self.configured("pool-two-jobs")
        del job
        first = self.requested(FIRST, "The FIRST requested task.")
        second = self.requested(SECOND, "The SECOND requested task.")
        tasks = {FIRST: first["task_document"],
                 SECOND: second["task_document"]}
        held = {}
        snapshots = {}
        for index, (job_id, made) in enumerate(
                ((FIRST, first), (SECOND, second))):
            work_id = self.WORKS[index]
            worker = self.pool_worker(
                control, "implementation", tasks, index=index,
                work_ref=dict(self.manifest["work_ref"], work_id=work_id),
                deployment={"participant": f"baton.impl-{index}",
                            "principal": f"principal:baton.impl-{index}"})
            # THE SNAPSHOT IS SHALLOW ON PURPOSE. A deep copy of the held
            # configuration is refused by the product -- `SourceBoundary` and
            # the declared capacity are immutable objects that refuse
            # `__setattr__`, which is them doing their job -- so what is held
            # is the mapping itself plus a serialization of the two members a
            # per-Job delivery composes over. Between them, a replaced member
            # and an in-place mutation are both visible.
            snapshots[job_id] = {
                "members": dict(worker.given),
                "manifest": json.dumps(worker.given["input_manifest"],
                                       sort_keys=True),
                "task": worker.given["task_bytes"]}
            self.line_for_job(control, job_id, work_id=work_id)
            composition = self.composition(
                control, "implementation", worker_id=f"impl-worker-{index}")
            stage = dict(self.stage_for("implementation"), job_id=job_id,
                         work_id=work_id,
                         attempt_id=f"attempt-{job_id}",
                         stage_id=f"{job_id}/implementation",
                         offer_id=f"offer-{job_id}")
            identity = worker._given_for(stage)[
                "input_manifest"]["manifest_digest"]
            # AND THE SELECTOR ADMITS THIS WORKER FOR THIS JOB, asked of the
            # real `_matches` with the Job's own declared identity -- so the
            # pair under test is one the serving loop would have chosen.
            worker._matches(stage, {"job_id": job_id,
                                    "input_digest": job_input_identity(
                                        worker._given_for(stage)[
                                            "input_manifest"]),
                                    "policy_digest": fixtures.POLICY_DIGEST})
            self.attempt_row(control, worker, stage["attempt_id"],
                             input_digest=identity)
            prepared = self.delivered_through(worker, composition, stage)
            held[job_id] = dict(prepared, made=made, stage=stage,
                                identity=identity, composition=composition,
                                worker=worker)
        return {"control": control, "before": snapshots, "jobs": held}

    def test_each_job_gets_its_own_bytes_identity_and_root(self):
        """TWO ATTEMPTS, TWO ROOTS, NOTHING OF EITHER IN THE OTHER."""
        held = self.both()
        first, second = held["jobs"][FIRST], held["jobs"][SECOND]
        self.assertNotEqual(first["roots"]["inputs"],
                            second["roots"]["inputs"])
        for one in (first, second):
            self.assertEqual(self.published_task(one["roots"]),
                             one["made"]["task_document"].encode("utf-8"))
            self.assertEqual(one["manifest"]["manifest_digest"],
                             one["identity"])
            adapter = one["worker"]._adapter(
                one["roots"], None, None, None,
                attempt_id=one["stage"]["attempt_id"])
            self.assertEqual(adapter.input_manifest_digest, one["identity"])
        self.assertNotEqual(first["identity"], second["identity"])
        self.assertNotEqual(job_input_identity(first["manifest"]),
                            job_input_identity(second["manifest"]))
        # AND NEITHER ROOT CARRIES A WORD OF THE OTHER JOB.
        self.assertNotIn(SECOND.encode("utf-8"),
                         self.published_task(first["roots"]))
        self.assertNotIn(FIRST.encode("utf-8"),
                         self.published_task(second["roots"]))

    def test_each_job_is_granted_its_own_line(self):
        """THE POOL'S OWN REASON this is possible at all."""
        held = self.both()
        lines = {job_id: self.lines[job_id]["line_id"]
                 for job_id in (FIRST, SECOND)}
        self.assertEqual(len(set(lines.values())), 2)
        self.assertNotEqual(lines[FIRST], lines[SECOND])
        from baton_v12.worker_manager import review_cycles

        for job_id in (FIRST, SECOND):
            attempt_id = f"attempt-{job_id}"
            prepared = held["jobs"][job_id]["composition"]._prepared[
                attempt_id]
            self.assertEqual(prepared["line_id"], lines[job_id])
            # THE DURABLE GRANT, read back through the accepted reader rather
            # than from the composition's own cache.
            granted = review_cycles.writer_for_attempt(
                held["control"], attempt_id=attempt_id, generation=1)
            self.assertEqual(granted["line_id"], lines[job_id])
            self.assertEqual(granted["state"], "active")
            self.assertEqual(granted["writer_id"], prepared["writer_id"])

    def test_the_shared_configuration_is_not_mutated_by_either_job(self):
        """ONE WORKER OBJECT, SERVING TWO JOBS, UNCHANGED BY BOTH."""
        held = self.both()
        for job_id in (FIRST, SECOND):
            worker = held["jobs"][job_id]["worker"]
            before = held["before"][job_id]
            self.assertEqual(dict(worker.given), before["members"])
            self.assertEqual(json.dumps(worker.given["input_manifest"],
                                        sort_keys=True), before["manifest"])
            self.assertEqual(worker.given["task_bytes"], before["task"])
        # AND THE DOCUMENT EACH STAGE WAS SERVED UNDER IS A FRESH ONE.
        for job_id in (FIRST, SECOND):
            one = held["jobs"][job_id]
            self.assertIsNot(one["given"], one["worker"].given)
            self.assertNotEqual(one["given"]["input_manifest"],
                                one["worker"].given["input_manifest"])


class TheCreatedJobRunsThroughThePoolServingLoop(ServingCase):
    """W363066 review at handoff E363900: THE POOL'S OWN SERVING LOOP.

    Everything this suite proved before stopped short of one thing the
    reviewer kept asking for and was right to: the loop. `reconcile` and
    `sweep` offering, claiming, preparing, publishing and STARTING a Job that
    a real creation operation put in a real Job store, served by a real pool
    composed from a real deployment document.

    IT IS REACHABLE WITHOUT VERSION CONTROL, and the reviewer found the seam:
    `stage_execution.operations_from` takes `checkpoint_profile`, the document
    names the profile by name, and `tests.job_manager.test_review_driver.
    Profile` is the deployment-configured profile "with no VCS behind it".
    Every case here installs refusing process runners, so a case that reached
    version control would fail rather than perform it.

    AND THE JOB IS REALLY CREATED. `creation.create_template_job` -- the
    operation W361912 added and this child's parent owns -- resolves the
    template, derives the per-Job task, admits the submission and writes the
    `template_jobs` row. Nothing here hand-writes a Job, a task document, an
    offer, a claim, an attempt, an activation, a preparation or a launch:
    every one of those is the loop's.

    WHAT THIS FOUND. The first run of this class could not offer the stage at
    all, and the scheduler said why in as many words:

        no worker this deployment configures for the 'implementation' stage
        can serve Job 'job-pool-a': {'implementation-worker': ['the
        submitted input']}

    `_with_job_task` returned the installed document whenever the binding's
    `job_id` was `None` -- which, in the ordinary one-Job `/1` document, it
    always is. So a created Job's own task never reached the pool's
    compatibility derivation, every configured worker was excluded as
    disagreeing about the submitted input, and the POOL path for a created
    Job was dead. The fix is in `tools/stage_execution.py` and the negative
    control for it is `test_a_job_with_no_own_task_is_served_the_installed_one`
    below, which proves the installed path still behaves as it always did.
    """

    def setUp(self):
        super().setUp()
        from tests.job_manager.test_review_driver import Profile

        self.profile_seam = Profile()
        self.no_version_control()

    no_version_control = PoolDeliveryCase.no_version_control

    def worker_of(self, composed, role):
        """One role's composed worker, through the public worker list."""
        return {one["role"]: one["operations"]._worker
                for one in composed.workers}[role]

    def identity_for(self, case_root=None):
        """The instance identity the creation ports answer for."""
        del case_root
        return {"root": self.root, "job_store": self.job_path,
                "control_store": self.control_path,
                "authority_store": self.authority_path,
                "authority_uuid": self.config["authority_uuid"]}

    def creation_ports(self, installed, *, work_id):
        """The four ports `create_template_job` takes, over THIS pool.

        Three of them are the owning suite's recorded stand-ins -- the Work
        authorization, the deployment binding and the instance ownership --
        because what they own is W361912's and is proved by
        `tests.job_manager.test_creation`. The DERIVATION is this pool's own:
        it answers the installed manifest's Job-scoped identity, the pool's
        configured profiles, and the per-Job task composed by
        `tools.job_task` exactly as `tools.creation_ports` composes it for an
        installed instance -- including the per-Job `input_digest`, without
        which `creation._task_agrees` refuses before anything is reserved.
        """
        from tests.job_manager.test_creation import (FakeAuthorization,
                                                     FakeBinding,
                                                     FakeDerivation,
                                                     FakeOwnership)

        manifest = installed["input_manifest"]
        identity = self.identity_for()

        def task(selection):
            held = job_task.per_job_delivery(
                installed["task_bytes"], manifest,
                dict(selection, work_id=work_id))
            return dict(held, input_digest=job_input_identity(
                held["input_manifest"]))

        derivation = FakeDerivation(
            identity=identity, work_id=work_id,
            input_digest=job_input_identity(manifest),
            policy_digest=manifest["policy_digest"],
            profiles={kind: {"profile_name": self.config["profile_name"],
                             "profile_digest": self.config["profile_digest"]}
                      for kind in ("implementation", "review")},
            task=task)
        return {"derivation": derivation,
                "authorization": FakeAuthorization(identity=identity),
                "binding": FakeBinding(identity=identity, work_id=work_id),
                "ownership": FakeOwnership(identity=identity)}

    def create(self, jobs, installed, *, task_id, statement, work_id=None,
               task=True):
        """One Job, created by the real operation."""
        from baton_v12.job_manager import creation
        from tests.job_manager.fixtures import FakeOperations

        ports = self.creation_ports(installed,
                                    work_id=work_id or self.work)
        if not task:
            ports["derivation"].task = None
        request = {
            "schema": templates.REQUEST_SCHEMA,
            "task": {"task_id": task_id, "statement": statement},
            "source_selection": creation.INSTALLED_SOURCE,
            "scope": {"work": ["v12/python/tools/stage_execution.py"],
                      "tests": ["v12/python/tests/tools/"
                                "test_job_task_delivery.py"]},
            "acceptance": ["The requested task reaches the pool runtime."]}
        answered = creation.create_template_job(
            jobs, FakeOperations(authority_uuid=self.config["authority_uuid"]),
            request=request, **ports)
        return answered

    def pool(self, jobs, control, **members):
        """The real pool, with the profile and engine as the two seams."""
        self.engine = Engine()
        composed = stage_execution.operations_from(
            self.composed_document(checkpoint_profile=self.config[
                "profile_name"], **members),
            jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        return composed

    def driven(self, jobs, composed, job_id, kind="implementation",
               want="waiting", ticks=10):
        """Ordinary ticks until this Job's stage reaches a state.

        No operator act: nothing here offers, claims, prepares, publishes,
        starts or ends anything by hand.
        """
        from baton_v12.job_manager import reconcile, sweep

        seen = []
        for _ in range(ticks):
            reconcile(jobs, composed, now=fixtures.NOW)
            seen.append(sweep(jobs, composed, now=fixtures.NOW))
            held = self.stages(jobs, composed, job_id)
            if held.get(kind) == want:
                return held
        self.fail(f"{job_id}'s {kind} stage never reached {want!r}: "
                  f"{self.stages(jobs, composed, job_id)}; last acts "
                  f"{[one['acts'] for one in seen[-1:]]}")

    def stages(self, jobs, composed, job_id):
        from baton_v12.job_manager import status as projected

        for one in projected(jobs, composed,
                             observed_at=fixtures.NOW)["jobs"]:
            if one["job_id"] == job_id:
                return {stage["kind"]: stage["state"]
                        for stage in one["stages"]}
        self.fail(f"no projected Job {job_id!r}")

    def stage_of(self, jobs, composed, job_id, kind="implementation"):
        from baton_v12.job_manager import status as projected

        for one in projected(jobs, composed,
                             observed_at=fixtures.NOW)["jobs"]:
            if one["job_id"] == job_id:
                for stage in one["stages"]:
                    if stage["kind"] == kind:
                        return stage
        self.fail(f"no {kind} stage for {job_id!r}")

    def published(self, attempt_id):
        place = os.path.join(self.config["workspace_storage"], attempt_id,
                             "inputs", single_worker.TASK_DOCUMENT)
        with open(place, "rb") as reading:
            return reading.read()

    def served(self, task_id="pool-a", statement="A requested pool task.",
               *, task=True):
        """One created Job, served by the loop to a started runtime."""
        jobs, control = self.stores("pool-created-" + task_id)
        installed = single_worker._held(
            self.worker("implementation")["deployment"])
        answered = self.create(jobs, installed, task_id=task_id,
                               statement=statement, task=task)
        composed = self.pool(jobs, control)
        job_id = answered["job_id"]
        self.driven(jobs, composed, job_id)
        stage = self.stage_of(jobs, composed, job_id)
        return {"jobs": jobs, "control": control, "composed": composed,
                "installed": installed, "created": answered,
                "job_id": job_id, "stage": stage,
                "attempt": stage["attempt_id"],
                "worker": self.worker_of(composed, "implementation")}

    def test_the_created_jobs_own_task_reaches_a_started_runtime(self):
        """THE WHOLE SCENARIO: creation, loop, publication, start."""
        held = self.served()
        delivered = held["created"]["task"]
        self.assertEqual(delivered["job_id"], held["job_id"])
        # THE BYTES THE RUNTIME MOUNTS.
        document = json.loads(self.published(held["attempt"]).decode("utf-8"))
        self.assertEqual(document["task_id"], held["job_id"])
        self.assertIn("The requested task reaches the pool runtime.",
                      document["instructions"])
        self.assertNotEqual(self.published(held["attempt"]),
                            held["installed"]["task_bytes"])
        # AND THE ENGINE REALLY STARTED ONE CONTAINER OVER THEM.
        self.assertEqual(len(self.engine.starts), 1)
        self.assertEqual(len(self.engine.activations), 1)
        # THE RECORDED ATTEMPT IDENTITY IS THE DELIVERED DOCUMENT'S, not the
        # installed one, read from the manager's own durable record.
        served = held["worker"]._given_for(
            dict(held["stage"], job_id=held["job_id"]))
        self.assertEqual(
            attempts.recorded_input_of(held["control"], held["attempt"]),
            served["input_manifest"]["manifest_digest"])
        self.assertNotEqual(
            served["input_manifest"]["manifest_digest"],
            held["installed"]["input_manifest"]["manifest_digest"])
        # AND THE JOB-SCOPED IDENTITY IS WHAT THE JOB DECLARED.
        self.assertEqual(job_input_identity(served["input_manifest"]),
                         held["created"]["source"]["input_digest"])

    def test_the_stageless_adapter_over_the_pool_attempt_is_the_delivered_one(
            self):
        """THE RECOVERY IDENTITY, after a real pool start."""
        held = self.served(task_id="pool-recovery")
        from baton_v12.worker_manager import workspaces

        roots = workspaces.assignment_workspace(
            held["worker"].group, self.config["workspace_storage"],
            held["attempt"], control=held["control"])
        adapter = held["worker"]._adapter(roots, None, None, None,
                                          attempt_id=held["attempt"])
        self.assertEqual(
            adapter.input_manifest_digest,
            attempts.recorded_input_of(held["control"], held["attempt"]))
        self.assertNotEqual(
            adapter.input_manifest_digest,
            held["installed"]["input_manifest"]["manifest_digest"])

    def test_a_job_with_no_own_task_is_served_the_installed_one(self):
        """THE PRESERVED PATH, through the same loop and the same fix.

        A deployment that composes no per-Job task creates Jobs with no task
        document, the reader answers `None`, and `_with_job_task` returns the
        installed document -- which is what every Job did before this Work.
        """
        held = self.served(task_id="pool-installed", task=False)
        self.assertEqual(self.published(held["attempt"]),
                         held["installed"]["task_bytes"])
        served = held["worker"]._given_for(
            dict(held["stage"], job_id=held["job_id"]))
        self.assertIs(served, held["worker"].given)
        self.assertEqual(
            attempts.recorded_input_of(held["control"], held["attempt"]),
            held["installed"]["input_manifest"]["manifest_digest"])
        self.assertEqual(len(self.engine.starts), 1)


class TwoCreatedJobsRunThroughOnePoolServingLoop(ServingCase):
    """W363066 review at handoff E363900, scenario 1: BOTH JOBS, ONE LOOP.

    One pool, one Job store, one control store, one `sweep`. Two Jobs, each
    created by the real `create_template_job` with its OWN requested task,
    each bound to its own Work, line and producer by a `/2` deployment
    document -- which is what a pool serving two Jobs is: `_PerJob`'s own
    rule, "a source, a base, a Work and a target are facts about a Job".

    WHY TWO WORKS AND TWO PRODUCERS. A worker's manifest declares the Work
    its stages belong to, and `create_line` derives a line's identity from
    `(authority, work)` -- so two Jobs on one Work would share one line and
    one producer, and the second would wait for the first's capacity rather
    than being served. Two Works is the shape that makes "both Jobs served"
    a question about delivery instead of about scheduling order.

    The second Work and its handlers are created in the fixture Authority,
    which is setup: no offer, claim, attempt, activation, preparation or
    launch is written by this class. Everything else is ordinary ticks.

    THE ENGINE, AND A CLAIM OF MINE THAT WAS FALSE. claim364051 said "every
    engine double in this repository models ONE container" and reported the
    second Job's start as blocked by that. The reviewer disproved it in one
    line: `test_stage_execution._ConcurrentEngine` is "one observable OCI
    process boundary holding SEVERAL containers", written for exactly this
    fact, and calling `both()` with it started both Jobs. I had read
    `ComposedOneJobCase.quiescing`, found it modelled successive containers
    rather than simultaneous ones, and generalized from the two doubles I
    happened to open to the whole repository without searching for a third.
    The correction is recorded in PROGRESS claim364233 as well as here.

    SO THE SUCCESS IS THE REGRESSION AND THE REFUSAL IS ITS OWN CASE.
    `both()` takes the engine: the multi-container double for two Jobs coding
    simultaneously, and the single-container one for
    `test_the_single_container_engine_refuses_the_second_delivery` below --
    which is worth keeping, because what it measures is the manager declining
    to adopt a runtime labelled for another attempt.
    """

    SECOND_WORK = "0000000a-W2"
    SECOND_PRODUCER = "baton.second"
    SECOND_REVIEWER = "baton.reviewer-2"

    # THE HELPERS ARE BORROWED AND THE CASES ARE NOT, for the reason this
    # suite has been corrected for twice: subclassing a case class re-runs
    # its assertions under this name.
    owner = TheCreatedJobRunsThroughThePoolServingLoop
    # ONE RUNTIME IDENTITY PER STARTED CONTAINER, which two concurrent
    # attempts need and `Engine` alone cannot give: it mints
    # `runtime-single-1` every time, so the second attempt's delivery was
    # refused -- correctly -- for naming a container labelled with the first
    # attempt's id. `ComposedOneJobCase.quiescing` is the owning suite's own
    # correction for exactly that, borrowed as a seam and not as a case.
    quiescing = ComposedOneJobCase.quiescing
    no_version_control = owner.no_version_control
    identity_for = owner.identity_for
    creation_ports = owner.creation_ports
    create = owner.create
    driven = owner.driven
    stages = owner.stages
    stage_of = owner.stage_of
    published = owner.published
    worker_of = owner.worker_of

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority
        from tests.job_manager.test_review_driver import Profile

        self.profile_seam = Profile()
        self.no_version_control()
        self.second_source = os.path.join(self.root, "source-b")
        os.makedirs(self.second_source)
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.create_work(self.SECOND_WORK, fixtures.ROUTE,
                                  contract="v12-assignment-1",
                                  operation_id="create-second-work")
            self.second_principals = {
                who: authority.principal_of(who)
                for who in (self.SECOND_PRODUCER, self.SECOND_REVIEWER)}
            scope = authority.project_work(self.SECOND_WORK)["scope"]
            for who, capability in self.receipt_grants.items():
                authority.grant_capability(who, capability, scope=scope)
            # THE TWO ROUTES THIS JOB'S STAGES MOVE THROUGH, declared the
            # way `ServingCase` declares the first Job's: an offer whose
            # route resolves to nobody is refused at the claim, which is a
            # fixture that never authorized the participant rather than
            # anything about delivery.
            authority.add_route_handler(fixtures.ROUTE, self.SECOND_PRODUCER)
            authority.add_route_handler("rview", self.SECOND_REVIEWER)
        finally:
            authority.dispose()

    def manifest_for(self, work_id):
        """This Job's own input manifest: its Work, and its own digest.

        The task document is NOT moved with it, and that is the difference
        from `EachJobBindsItsOwnDeploymentAndLine`'s helper of the same name:
        both producers carry the deployment's one INSTALLED task here, so the
        only thing that can make their deliveries differ is the per-Job task
        each created Job owns -- which is the thing under test.
        """
        from baton_v12.contracts import digest

        manifest = json.loads(json.dumps(self.manifest))
        manifest["work_ref"] = dict(manifest["work_ref"], work_id=work_id)
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        return manifest

    def second_worker(self, role, worker_id, participant, **members):
        """One configured worker for the second Job, on the second Work."""
        held = self.worker(role, participant=participant,
                           principal=self.second_principals[participant],
                           **members)
        held["worker_id"] = worker_id
        held["deployment"]["input_manifest"] = self.manifest_for(
            self.SECOND_WORK)
        held["deployment"]["nominated_source"] = self.second_source
        held["deployment"]["launch_home"] = os.path.join(self.root,
                                                         "launch-b")
        held["deployment"]["credential_home"] = os.path.join(self.root,
                                                             "cred-b")
        return held

    def two_job_document(self):
        """One `/2` document binding two Jobs to two sources and two Works.

        Built the way `EachJobBindsItsOwnDeploymentAndLine.held_two` builds
        one: the members go THROUGH `composed_document`, so the `/1` members
        it already carries stay exactly where that suite leaves them and only
        the schema, the worker list and the bindings are this document's own.
        """
        held = {one["role"]: one
                for one in self.composed_document()["workers"]}
        workers = [held["implementation"], held["review"],
                   held["integration"],
                   self.second_worker("implementation",
                                      "implementation-worker-b",
                                      self.SECOND_PRODUCER),
                   self.second_worker("review", "review-worker-b",
                                      self.SECOND_REVIEWER,
                                      review_route=self.INTEGRATION_ROUTE)]
        return self.composed_document(
            checkpoint_profile=self.config["profile_name"],
            schema=stage_execution.MULTI_CONFIG_SCHEMA,
            workers=workers,
            job_bindings=[
                {"job_id": "job-pool-first", "job_work_id": self.work,
                 "review_work_id": self.work,
                 "line_declared_base": "a" * 40,
                 "canonical_target_id": "target-a",
                 "source_worker_id": "implementation-worker"},
                {"job_id": "job-pool-second",
                 "job_work_id": self.SECOND_WORK,
                 "review_work_id": self.SECOND_WORK,
                 "line_declared_base": "b" * 40,
                 "canonical_target_id": "target-b",
                 "source_worker_id": "implementation-worker-b"}])

    def both(self, engine=None):
        """Two created Jobs, both driven by ONE loop over one store pair."""
        jobs, control = self.stores("pool-two-created")
        first_installed = single_worker._held(
            self.worker("implementation")["deployment"])
        second_installed = single_worker._held(
            self.second_worker("implementation", "implementation-worker-b",
                               self.SECOND_PRODUCER)["deployment"])
        created = {
            "job-pool-first": self.create(
                jobs, first_installed, task_id="pool-first",
                statement="The FIRST requested pool task."),
            "job-pool-second": self.create(
                jobs, second_installed, task_id="pool-second",
                statement="The SECOND requested pool task.",
                work_id=self.SECOND_WORK)}
        self.engine = engine or _ConcurrentEngine()
        composed = stage_execution.operations_from(
            self.two_job_document(), jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        # ORDINARY TICKS, AND NOTHING ELSE. Each Job is driven as far as this
        # engine lets it go; the states are asserted by the cases rather than
        # required here, so one helper serves both the success and the
        # single-container refusal.
        from baton_v12.job_manager import reconcile, sweep

        for _ in range(12):
            reconcile(jobs, composed, now=fixtures.NOW)
            sweep(jobs, composed, now=fixtures.NOW)
            states = {job_id: self.stages(jobs, composed,
                                          job_id)["implementation"]
                      for job_id in created}
            if all(one in ("waiting", "exceptional")
                   for one in states.values()):
                break
        held = {job_id: self.stage_of(jobs, composed, job_id)
                for job_id in created}
        return {"jobs": jobs, "control": control, "composed": composed,
                "created": created, "stages": held,
                "installed": {"job-pool-first": first_installed,
                              "job-pool-second": second_installed}}

    def test_both_created_jobs_are_served_their_own_requested_bytes(self):
        """TWO JOBS, ONE LOOP, TWO DELIVERIES, NOTHING CROSSED."""
        held = self.both()
        published = {}
        for job_id, stage in held["stages"].items():
            document = json.loads(
                self.published(stage["attempt_id"]).decode("utf-8"))
            published[job_id] = document
            self.assertEqual(document["task_id"], job_id)
            # AND NOT THE DEPLOYMENT'S INSTALLED TASK.
            self.assertNotEqual(self.published(stage["attempt_id"]),
                                held["installed"][job_id]["task_bytes"])
        self.assertNotEqual(published["job-pool-first"]["instructions"],
                            published["job-pool-second"]["instructions"])
        self.assertIn("The FIRST requested pool task.",
                      published["job-pool-first"]["instructions"])
        self.assertIn("The SECOND requested pool task.",
                      published["job-pool-second"]["instructions"])
        # NEITHER ROOT CARRIES A WORD OF THE OTHER JOB.
        self.assertNotIn(
            "job-pool-second",
            self.published(
                held["stages"]["job-pool-first"]["attempt_id"]).decode())
        self.assertNotIn(
            "job-pool-first",
            self.published(
                held["stages"]["job-pool-second"]["attempt_id"]).decode())

    def test_both_attempts_are_recorded_against_their_own_identity(self):
        """THE DURABLE RECORD, for both, written by the loop."""
        held = self.both()
        recorded = {}
        for job_id, stage in held["stages"].items():
            recorded[job_id] = attempts.recorded_input_of(
                held["control"], stage["attempt_id"])
            self.assertIsNotNone(recorded[job_id])
            self.assertNotEqual(
                recorded[job_id],
                held["installed"][job_id]["input_manifest"][
                    "manifest_digest"])
        self.assertNotEqual(recorded["job-pool-first"],
                            recorded["job-pool-second"])

    def test_both_jobs_reach_their_own_started_runtime(self):
        """TWO JOBS CODING SIMULTANEOUSLY, through one loop.

        The regression the reviewer's probe established, written as a case:
        both stages reach `waiting`, the engine composed TWO containers, each
        attempt is attached to its own, and each started runtime's input root
        is that Job's own stored task -- compared against
        `creation.job_task_of`, the Job store's own answer, so the bytes on
        disk are held to the created Job rather than to a value this case
        recomposed.
        """
        from baton_v12.job_manager import creation

        held = self.both()
        states = {job_id: self.stages(held["jobs"], held["composed"],
                                      job_id)["implementation"]
                  for job_id in held["stages"]}
        self.assertEqual(set(states.values()), {"waiting"})
        self.assertEqual(len(self.engine.starts), 2)
        runtimes = {job_id: stage["runtime"]["runtime_id"]
                    for job_id, stage in held["stages"].items()}
        self.assertEqual(len(set(runtimes.values())), 2)
        self.assertNotIn(None, set(runtimes.values()))
        for job_id, stage in held["stages"].items():
            self.assertEqual(
                self.published(stage["attempt_id"]),
                creation.job_task_of(held["jobs"], job_id).encode("utf-8"))
            self.assertEqual(stage["runtime"]["execution_runtime"], "running")

    def test_the_single_container_engine_refuses_the_second_delivery(self):
        """AND THE REFUSAL IS KEPT, because it is worth keeping.

        With a double that models ONE container, the second attempt is shown
        the FIRST attempt's runtime and the manager declines to adopt it --
        "one delivery carries one identity". That is correct behaviour and
        the only way this suite can reach it: a manager that treated another
        attempt's container as its own would be a far worse defect than a
        fixture that cannot show two.

        BOTH ROOTS ARE STILL PUBLISHED WITH THEIR OWN TASK, which is what
        makes this a launch-identity case rather than a delivery one.
        """
        from baton_v12.job_manager import creation

        held = self.both(engine=self.quiescing())
        states = {job_id: self.stages(held["jobs"], held["composed"],
                                      job_id)["implementation"]
                  for job_id in held["stages"]}
        self.assertEqual(states["job-pool-first"], "waiting")
        self.assertEqual(states["job-pool-second"], "exceptional")
        self.assertEqual(len(self.engine.starts), 1)
        second = held["stages"]["job-pool-second"]
        self.assertIsNone(second["runtime"]["runtime_id"])
        self.assertEqual(second["runtime"]["execution_runtime"], "uncertain")
        self.assertTrue(
            second["attempt_diagnostics"]["start_failure_recorded"]["value"])
        self.assertEqual(
            held["stages"]["job-pool-first"]["runtime"]["execution_runtime"],
            "running")
        for job_id, stage in held["stages"].items():
            self.assertEqual(
                self.published(stage["attempt_id"]),
                creation.job_task_of(held["jobs"], job_id).encode("utf-8"))

    def test_each_job_reached_its_own_line_and_producer(self):
        """THE POOL'S OWN PER-JOB BINDING, read back through its reader."""
        from baton_v12.worker_manager import review_cycles

        held = self.both()
        deployment = held["composed"].workers[0]["operations"]._worker.stage \
            .deployment
        lines = {job_id: deployment.line_for(job_id)
                 for job_id in held["stages"]}
        self.assertNotEqual(lines["job-pool-first"]["line_id"],
                            lines["job-pool-second"]["line_id"])
        self.assertEqual(lines["job-pool-first"]["work_id"], self.work)
        self.assertEqual(lines["job-pool-second"]["work_id"],
                         self.SECOND_WORK)
        for job_id, stage in held["stages"].items():
            granted = review_cycles.writer_for_attempt(
                held["control"], attempt_id=stage["attempt_id"],
                generation=1)
            self.assertEqual(granted["line_id"], lines[job_id]["line_id"])
            self.assertEqual(granted["state"], "active")
            # AND THE PRODUCER THE SCHEDULER ALLOCATED IS THIS JOB'S OWN.
            self.assertEqual(stage["allocation"]["worker_id"],
                             "implementation-worker"
                             if job_id == "job-pool-first"
                             else "implementation-worker-b")


class TheReviewStageRunsThroughThePoolServingLoop(ServingCase):
    """W363066 review at handoff E364325: THE REVIEW RUNTIME, VIA THE LOOP.

    The last milestone, and it is the whole chain: a Job created by the real
    `creation.create_template_job`; the pool's own `reconcile`/`sweep`
    offering, claiming, preparing, publishing and starting its implementation
    stage; one real in-image worker turn; the real ending -- seal, intake,
    retention, `retain_proposal`, `publish_candidate`, `freeze_checkpoint`;
    and then the loop reaching the REVIEW stage, granting its attachment over
    that frozen checkpoint and starting its runtime with the JOB'S OWN
    REQUESTED TASK in its input root.

    No offer, claim, activation, preparation or launch is written by this
    class. The states it waits for are the projection's own.

    THE THREE DETERMINISTIC SEAMS, NAMED. The ENGINE is the suite's double.
    The CHECKPOINT PROFILE is `test_review_driver.Profile`, the
    deployment-configured profile "with no VCS behind it", so the line is
    materialized and frozen without version control -- and every case here
    installs process runners that refuse any version-control invocation. The
    WORKER is `scripted_agent.ScriptedAgent` with one addition below.

    WHAT IS SYNTHETIC, LABELLED RATHER THAN IMPLIED. A real producer's
    proposal is a patch and an object bundle that version control wrote in
    the line, and its claim names the base it was taken from. This fixture's
    agent writes `objects.bundle` with fixed bytes and answers a claim naming
    the configured canonical target as its base and a fixed head. Those bytes
    are NOT a change proposal anybody could apply, and nothing here claims a
    live proposal or an owner receipt. What they are is the operand shape the
    publication validates -- and it does validate them: an earlier draft
    without the bundle was refused by the publication itself, "the worker
    names its object transport at 'objects.bundle' and the frozen content
    manifest measured nothing there", which is how this fixture knows the
    rule is not being bypassed. `ComposedLifecycleCase.frozen` composes a
    synthetic proposal the same way, for the same reason.
    """

    BASE = "a" * 40
    HEAD = "b" * 40
    PROPOSAL_OUTPUTS = (("proposal", "git-change-proposal"),
                        ("findings", "directory-result"),
                        ("logs", "directory-result"))

    # THE HELPERS ARE BORROWED AND THE CASES ARE NOT.
    owner = TheCreatedJobRunsThroughThePoolServingLoop
    no_version_control = owner.no_version_control
    identity_for = owner.identity_for
    creation_ports = owner.creation_ports
    create = owner.create
    driven = owner.driven
    stages = owner.stages
    stage_of = owner.stage_of
    published = owner.published
    worker_of = owner.worker_of
    quiescing = ComposedOneJobCase.quiescing

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority
        from tests.job_manager.test_review_driver import Profile

        self.profile_seam = Profile()
        self.no_version_control()
        # THE CANONICAL TARGET THE PUBLICATION BINDS TO. `ComposedOneJobCase`
        # sets this to its real base commit; here it is the line's declared
        # base, which is this fixture's synthetic one.
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.BASE)
        finally:
            authority.dispose()

    def proposal_manifest(self):
        """The manifest a Job whose result is PUBLISHED has to declare.

        `ComposedOneJobCase`'s shape, which is the pool's own: three outputs,
        each at its own name, none required -- because each role writes its
        half and answers the other `missing-optional` -- and the proposal
        typed `git-change-proposal`, which is what `publish_candidate`
        requires exactly one of. The human contract is untouched: the
        installed task document is unchanged, and `single_worker._held`
        proves those two against each other.
        """
        manifest = json.loads(json.dumps(self.manifest))
        held = manifest["outputs"][0]
        manifest["outputs"] = [
            dict(held, name=name, type=kind, path=name, required=False)
            for name, kind in self.PROPOSAL_OUTPUTS]
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        return manifest

    def proposing_workers(self):
        """Every configured worker, carrying that one manifest."""
        manifest = self.proposal_manifest()
        held = []
        for one in self.composed_document()["workers"]:
            one["deployment"]["input_manifest"] = manifest
            held.append(one)
        return held

    def agent(self):
        """The scripted worker, plus the proposal a producer would publish."""
        import scripted_agent

        base, head = self.BASE, self.HEAD

        class Proposing(scripted_agent.ScriptedAgent):
            def work(self, seen, declared):
                answered = super().work(seen, declared)
                kinds = {one["name"]: one["type"] for one in declared}
                paths = {one["name"]: one["path"] for one in declared}
                for name, kind in kinds.items():
                    if kind != "git-change-proposal":
                        continue
                    # THE TRANSPORT THE CLAIM NAMES. Synthetic bytes; the
                    # publication measures the tree and refuses a claim whose
                    # transport is not in it.
                    with open(os.path.join(scripted_agent.OUTPUT_ROOT,
                                           paths[name], "objects.bundle"),
                              "wb") as writing:
                        writing.write(b"a synthetic object transport\n")
                for one in answered["outputs"]:
                    if kinds[one["name"]] == "git-change-proposal":
                        one["result_metadata"] = {
                            "baton.git-proposal/1": {
                                "base": base, "head": head,
                                "transport": "objects.bundle",
                                "recap": "a synthetic candidate"}}
                return answered

        return Proposing()

    def turn(self, jobs, control, composed, role, attempt_id):
        """One real in-image worker turn over the MOUNTED roots.

        The roots are the composition's own, which matters: in the pool an
        implementation attempt's workspace is the LINE CHECKOUT, not
        `<storage>/<attempt>/workspace`. A first version derived the paths and
        the ending deferred with "published no 'output.json'" -- the agent had
        written the envelope into a directory nothing mounts.
        """
        import baton_worker
        import scripted_agent

        worker = self.worker_of(composed, role)
        roots = dict(worker.stage._prepared[attempt_id]["boundary"]["roots"])
        delivered = single_worker.launch.adopt(
            worker.given["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=worker.given["launch_contract"], role=role,
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            job_execution=single_worker.job_execution_reader(jobs)(
                job_id=self.job_id, attempt_id=attempt_id,
                runtime_input_digest=attempts.recorded_input_of(control,
                                                               attempt_id),
                runtime_policy_digest=worker.given["policy_digest"]),
            workspace_group=single_worker.configured_workspace_group(control))
        held = []
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", roots["inputs"]),
                (baton_worker, "OUTPUT_ROOT", roots["workspace"]),
                (scripted_agent, "OUTPUT_ROOT", roots["workspace"])):
            held.append((module, name, getattr(module, name)))
            setattr(module, name, value)
        try:
            return baton_worker.serve_exchange(
                self.agent(), delivered.document,
                delivered.document["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root)
        finally:
            for module, name, value in held:
                setattr(module, name, value)

    def reviewed(self):
        """One created Job carried by the loop to a started REVIEW runtime."""
        from baton_v12.job_manager import reconcile, sweep

        jobs, control = self.stores("pool-review")
        workers = self.proposing_workers()
        installed = single_worker._held(workers[0]["deployment"])
        answered = self.create(jobs, installed, task_id="pool-review",
                               statement="A reviewed pool task.")
        self.job_id = answered["job_id"]
        self.engine = self.quiescing()
        composed = stage_execution.operations_from(
            self.composed_document(
                checkpoint_profile=self.config["profile_name"],
                line_declared_base=self.BASE, workers=workers),
            jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        self.driven(jobs, composed, self.job_id)
        implementation = self.stage_of(jobs, composed, self.job_id)
        self.assertEqual(
            self.turn(jobs, control, composed, "implementation",
                      implementation["attempt_id"]), 0)
        for _ in range(12):
            sweep(jobs, composed, now=fixtures.NOW)
            reconcile(jobs, composed, now=fixtures.NOW)
            if self.stages(jobs, composed, self.job_id).get(
                    "review") == "waiting":
                break
        return {"jobs": jobs, "control": control, "composed": composed,
                "installed": installed, "created": answered,
                "implementation": implementation,
                "review": self.stage_of(jobs, composed, self.job_id,
                                        kind="review")}

    def test_the_review_runtime_is_started_with_the_requested_task(self):
        """THE MILESTONE: the loop, the ending, and the review runtime."""
        from baton_v12.job_manager import creation

        held = self.reviewed()
        self.assertEqual(self.stages(held["jobs"], held["composed"],
                                     self.job_id),
                         {"implementation": "completed", "review": "waiting"})
        review = held["review"]
        # THE BYTES THE REVIEW RUNTIME MOUNTS ARE THE JOB'S OWN, compared
        # against the Job store's own answer.
        self.assertEqual(
            self.published(review["attempt_id"]),
            creation.job_task_of(held["jobs"], self.job_id).encode("utf-8"))
        self.assertNotEqual(self.published(review["attempt_id"]),
                            held["installed"]["task_bytes"])
        # AND A CONTAINER WAS REALLY STARTED FOR IT.
        self.assertIsNotNone(review["runtime"]["runtime_id"])
        self.assertEqual(review["runtime"]["execution_runtime"], "running")
        self.assertNotEqual(review["runtime"]["runtime_id"],
                            held["implementation"]["runtime"]["runtime_id"])
        self.assertEqual(len(self.engine.starts), 2)

    def test_the_review_attempt_is_recorded_and_adapted_on_the_delivered_input(
            self):
        """THE IDENTITIES: recorded, manifest, context and adapter."""
        from baton_v12.worker_manager import workspaces

        held = self.reviewed()
        review = held["review"]
        worker = self.worker_of(held["composed"], "review")
        served = worker._given_for(dict(review, job_id=self.job_id))
        identity = served["input_manifest"]["manifest_digest"]
        # THE RECORDED ATTEMPT is the delivered document's, not the installed.
        self.assertEqual(
            attempts.recorded_input_of(held["control"],
                                       review["attempt_id"]),
            identity)
        self.assertNotEqual(
            identity, worker.given["input_manifest"]["manifest_digest"])
        # THE JOB-SCOPED IDENTITY is the one the Job declared, and it is the
        # same one the implementation stage was served under: one Job, two
        # roles, two runtime manifests, one identity.
        self.assertEqual(job_input_identity(served["input_manifest"]),
                         held["created"]["source"]["input_digest"])
        # THE LAUNCH CONTEXT the manager wrote carries that identity: adoption
        # compares canonical bytes, so a context naming anything else refuses.
        self.assertEqual(
            self.turn_adoption(held, review["attempt_id"]), identity)
        # AND THE STAGE-LESS ADAPTER over the review roots describes it.
        roots = workspaces.assignment_workspace(
            worker.group, worker.given["workspace_storage"],
            review["attempt_id"], control=held["control"])
        adapter = worker._adapter(roots, None, None, None,
                                  attempt_id=review["attempt_id"])
        self.assertEqual(adapter.input_manifest_digest, identity)

    def turn_adoption(self, held, attempt_id):
        """The identity the manager's own launch document carries.

        `launch.adopt` refuses a Job context that is not the one this manager
        would have written, so adopting with the recorded identity and having
        it ACCEPTED is the assertion -- the value is returned so the caller
        can compare it with the served document.
        """
        recorded = attempts.recorded_input_of(held["control"], attempt_id)
        worker = self.worker_of(held["composed"], "review")
        single_worker.launch.adopt(
            worker.given["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=worker.given["launch_contract"], role="review",
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            job_execution=single_worker.job_execution_reader(held["jobs"])(
                job_id=self.job_id, attempt_id=attempt_id,
                runtime_input_digest=recorded,
                runtime_policy_digest=worker.given["policy_digest"]),
            workspace_group=single_worker.configured_workspace_group(
                held["control"]))
        return recorded

    def test_the_review_mount_is_the_checkpoint_the_round_froze(self):
        """REVIEW SEMANTICS, from the attachment the loop granted."""
        from baton_v12.worker_manager import review_cycles

        held = self.reviewed()
        review = held["review"]
        worker = self.worker_of(held["composed"], "review")
        attached = review_cycles.review_for_attempt(
            held["control"], attempt_id=review["attempt_id"],
            generation=worker.stage.deployment.generation_of(
                review["attempt_id"]))
        self.assertEqual(attached["state"], "active")
        self.assertEqual(attached["reviewer_participant"],
                         worker.given["participant"])
        line = worker.stage.deployment.line_for(self.job_id)
        self.assertEqual(attached["checkpoint_id"],
                         line["current_checkpoint_id"])
        self.assertIsNotNone(line["current_checkpoint_id"])
        # AND THE MOUNT IS THAT CHECKPOINT'S CHECKOUT, not the writable line
        # the producer was granted.
        prepared = worker.stage._prepared[review["attempt_id"]]
        self.assertEqual(prepared["checkpoint_id"],
                         line["current_checkpoint_id"])
        self.assertIn("checkout", str(prepared["boundary"]["boundary"].source))


class ObservationReproducesTheDeliveredIdentity(
        TheRuntimePathDeliversAndRecoversOneIdentity):
    """W370555 — the read-only observation adopts what serving materialized.

    THE DEFECT, MEASURED IN PRODUCTION BEFORE IT WAS UNDERSTOOD. A live run
    (W370268) admitted a template Job, started a real container, and watched
    the status surface report the implementation stage `exceptional` with
    `exchange: unreadable (policy/denied)` for eighteen minutes while the
    stage was in fact working and then COMPLETED with a real candidate and no
    intervention. Nothing was wrong with serving; the reader was wrong.

    WHY. `_SingleWorker._job_execution` composes the launch context from
    `_given_for(stage)` -- this Job's own manifest -- and
    `_Observation._job_execution` composed it from `self.given`, the INSTALLED
    one. `launch.adopt` re-authors the launch document and compares canonical
    bytes exactly, so for every Job created with its own task the two
    compositions disagreed about `runtime_input_digest` and adoption refused.
    A Job-bound launch was therefore unreadable on every single status pass.

    THE EXACT-BYTE CHECK IS NOT WHAT WAS WRONG and these cases do not weaken
    it. `TheObservationStillRefusesALaunchItCannotReproduce` below keeps the
    refusals, because a reader that adopted anything would be worth nothing.

    THESE CASES BORROW THE RUNTIME HARNESS AND ADD THEIR OWN QUESTIONS. The
    inherited class drives the real production composition -- offer, claim,
    `_prepared`, `_input`, the recorded attempt, the launch adapter and the
    engine start -- so what a case here asks of a REAL materialized launch is
    a question about the reader rather than about a fixture.
    """

    def observing(self, held, *, job_store=None, control_store=None,
                  substitute=True):
        """A real `_Observation` over this deployment, as `status --observe`
        builds one: the same configuration document and the same two stores.

        THE READER IS SUBSTITUTED FOR THE SAME REASON THE SERVING ONE IS, and
        the inherited class states it: a Job store row carrying a
        `task_document` is written by `creation.create_template_job`, which
        needs an installed deployment and a Work binding this suite has
        neither of. So this harness substitutes the reader on BOTH sides --
        the same answer to both -- and what the cases then measure is whether
        the two COMPOSITIONS agree given one answer, which is the identity
        question. `TheReaderOverARealStore` drives the real
        `job_task_reader` against a real store, so the read itself is not
        taken on trust either.

        `substitute=False` leaves the real reader in place, which is how a
        case asks what an unsubstituted observation builds.
        """
        observation = single_worker.observation_from(
            self.config,
            held["job"] if job_store is None else job_store,
            held["control"] if control_store is None else control_store)
        if substitute:
            document = held["made"]["task_document"]
            observation.job_task = lambda *, job_id: (
                document if job_id == "job-a" else None)
        return observation

    def test_the_two_compositions_agree_on_the_launch_context(self):
        """THE IDENTITY AGREEMENT, asserted directly on the bytes.

        This is the whole Work in one assertion: the context the serving
        deployment composes for a stage and the context the observation
        composes for the same stage must be the same document, because
        adoption compares exactly that.
        """
        held = self.running("observe-agree")
        stage = held["stage"]
        serving = held["worker"]._job_execution(stage)
        observed = self.observing(held)._job_execution(stage)
        self.assertEqual(observed, serving)
        # AND IT IS THE JOB'S OWN IDENTITY, not the installed one -- a case
        # where the two happened to be equal would assert nothing.
        delivered = held["made"]["input_manifest"]["manifest_digest"]
        self.assertNotEqual(delivered, self.manifest["manifest_digest"])
        self.assertEqual(observed["runtime_input_digest"], delivered)

    def test_the_observation_adopts_the_materialized_launch(self):
        """THE BEHAVIOUR AN OPERATOR SEES, through the real surface.

        `observe_exchange` never raises: it answers a projection or the safe
        `unreadable` category. `unreadable` is produced ONLY by a refusal, so
        anything else is proof that adoption succeeded over the launch the
        serving loop actually wrote.
        """
        held = self.running("observe-adopt")
        answered = self.observing(held).observe_exchange(held["stage"])
        if answered is not None:
            self.assertNotEqual(answered.get("state"), "unreadable",
                                answered.get("unreadable"))

    def test_the_policy_digest_and_the_limits_are_still_the_deployments(self):
        """ONLY the input manifest and the task move.

        The correction substitutes a per-Job document; it must not have
        started resolving the policy identity, the limits or the allocation
        from somewhere else.
        """
        held = self.running("observe-policy")
        observed = self.observing(held)._job_execution(held["stage"])
        self.assertEqual(observed["runtime_policy_digest"],
                         self.config["policy_digest"])
        self.assertEqual(observed["job_id"], "job-a")
        self.assertEqual(observed["attempt_id"], held["attempt"])

    def test_a_fresh_reader_over_the_same_state_reproduces_the_context(self):
        """RESTART. A reader that remembered anything would fail here.

        The context is re-derived from the Job owner's own record by a second
        `_Observation` over FRESH store handles under a new incarnation --
        which is what a restarted `status --observe` is.
        """
        held = self.running("observe-restart")
        first = self.observing(held)._job_execution(held["stage"])
        job, control = self.stores("observe-restart-2")
        self.addCleanup(job.close)
        self.addCleanup(control.close)
        again = self.observing(held, job_store=job,
                               control_store=control)._job_execution(
                                   held["stage"])
        self.assertEqual(again, first)

    def test_the_installed_delivery_is_still_what_a_jobless_task_gets(self):
        """THE FALLBACK, preserved. A Job with no own task is every Job that
        predates the per-Job relation, and its delivery is the installed one.
        """
        held = self.running("observe-installed")
        observation = self.observing(held)
        # The reader answers `None` for this Job, exactly as a real store does
        # for a Job nobody created with a task.
        observation.job_task = lambda *, job_id: None
        observed = observation._job_execution(held["stage"])
        self.assertEqual(observed["runtime_input_digest"],
                         self.manifest["manifest_digest"])

    def test_the_shared_configuration_is_never_written_to(self):
        """NO CONTAMINATION. The installed document is shared by every Job
        this worker serves, so resolving one Job's delivery must not touch it.
        """
        held = self.running("observe-shared")
        observation = self.observing(held)
        # IDENTITY RATHER THAN A SERIALIZATION, because the held
        # configuration carries owned objects a dump cannot render -- and
        # because `is` is the stronger question: the shared document and the
        # shared manifest must be the SAME objects afterwards, not merely
        # equal ones.
        document, manifest = observation.given, observation.given[
            "input_manifest"]
        keys = sorted(observation.given)
        observation._job_execution(held["stage"])
        observation.observe_exchange(held["stage"])
        self.assertIs(observation.given, document)
        self.assertIs(observation.given["input_manifest"], manifest)
        self.assertEqual(sorted(observation.given), keys)
        # AND THE INSTALLED MANIFEST IS STILL THE INSTALLED ONE.
        self.assertEqual(
            observation.given["input_manifest"]["manifest_digest"],
            self.manifest["manifest_digest"])
        # WHILE THE RESOLVED DOCUMENT WAS A DIFFERENT ONE, or nothing was
        # being kept apart.
        resolved = single_worker.given_for_job(
            observation.given, observation.job_task, held["stage"])
        self.assertIsNot(resolved, document)
        self.assertNotEqual(resolved["input_manifest"]["manifest_digest"],
                            manifest["manifest_digest"])

    def test_two_jobs_on_one_worker_resolve_their_own_contexts(self):
        """CROSS-CONTAMINATION, asked of the reader rather than the writer.

        `TwoJobsOnOneWorkerGetTheirOwnBytes` proves the serving side. This
        proves the observation side over ONE reader: two stages naming two
        Jobs resolve two different input identities, and asking for one does
        not change the answer for the other.
        """
        held = self.running("observe-two")
        first = self.delivered("The first statement.")
        second = self.delivered("The second statement.")
        # Two Jobs with different statements compose different identities, or
        # this case would pass without distinguishing anything.
        self.assertNotEqual(first["input_manifest"]["manifest_digest"],
                            second["input_manifest"]["manifest_digest"])
        observation = self.observing(held)
        composed = {FIRST: first["task_document"],
                    SECOND: second["task_document"]}
        observation.job_task = lambda *, job_id: composed.get(job_id)

        def resolved(job_id):
            return single_worker.given_for_job(
                observation.given, observation.job_task,
                dict(held["stage"], job_id=job_id))["input_manifest"][
                    "manifest_digest"]

        self.assertEqual(resolved(FIRST),
                         first["input_manifest"]["manifest_digest"])
        self.assertEqual(resolved(SECOND),
                         second["input_manifest"]["manifest_digest"])
        # ASKED AGAIN, IN THE OTHER ORDER: a reader that cached would answer
        # the first Job's identity for the second.
        self.assertEqual(resolved(SECOND),
                         second["input_manifest"]["manifest_digest"])
        self.assertEqual(resolved(FIRST),
                         first["input_manifest"]["manifest_digest"])


class TheObservationStillRefusesALaunchItCannotReproduce(
        TheRuntimePathDeliversAndRecoversOneIdentity):
    """W370555 — the correction must not have made the reader credulous.

    The defect was a reader that could not reproduce a correct launch. The
    wrong correction is a reader that accepts an incorrect one, and the
    diagnostic review said so in terms: weakening the exact-byte check would
    be the wrong fix. So these cases keep the refusals, and they drive them
    through the same public surface an operator reads.
    """

    observing = ObservationReproducesTheDeliveredIdentity.observing

    def unreadable(self, observation, stage):
        """What the surface answers, held to the refusal shape."""
        answered = observation.observe_exchange(stage)
        self.assertIsNotNone(answered)
        self.assertEqual(answered["state"], "unreadable")
        # THE PROSE STAYS OUT, which is the exchange owner's rule: what comes
        # back is the category and the code and nothing else.
        self.assertEqual(sorted(answered["unreadable"]), ["category", "code"])
        return answered["unreadable"]

    def test_a_stage_naming_another_attempt_is_refused(self):
        """CROSS-ATTEMPT. The launch on disk belongs to one attempt."""
        held = self.running("refuse-cross")
        observation = self.observing(held)
        stranger = dict(held["stage"],
                        attempt_id="attempt-" + ("c" * 64))
        answered = observation.observe_exchange(stranger)
        # Absence is the honest answer for an attempt with no launch at all;
        # what must never happen is adopting THIS attempt's material under
        # another attempt's name.
        if answered is not None:
            self.assertEqual(answered["state"], "unreadable")

    def test_a_stage_naming_another_job_is_refused(self):
        """THE EXACT-BYTE CHECK, still doing its work.

        The launch was written for `job-a`; a stage naming another Job
        composes a different context, so the re-authored document differs and
        adoption refuses. This is the same mechanism that produced the defect
        -- kept, because it is correct.
        """
        held = self.running("refuse-job")
        observation = self.observing(held)
        self.unreadable(observation, dict(held["stage"], job_id="job-other"))

    def test_a_corrupted_launch_document_is_refused(self):
        """TAMPERING. The bytes on disk are proved, not trusted."""
        held = self.running("refuse-corrupt")
        place = os.path.join(self.config["launch_home"], held["attempt"],
                             "launch.json")
        self.assertTrue(os.path.exists(place), place)
        os.chmod(place, 0o644)
        with open(place, "r+", encoding="utf-8") as handle:
            document = json.load(handle)
            document["role"] = "review"
            handle.seek(0)
            handle.truncate()
            json.dump(document, handle)
        self.unreadable(self.observing(held), held["stage"])

    def test_a_stage_naming_no_job_is_refused(self):
        """AN UNBOUND EXECUTION. Both compositions refuse it, identically,
        because two readers that disagreed about the defaults would disagree
        about the bytes.
        """
        held = self.running("refuse-jobless")
        observation = self.observing(held)
        stage = dict(held["stage"])
        stage.pop("job_id", None)
        with self.assertRaises(ContractRefusal):
            observation._job_execution(stage)

    def test_the_observation_still_holds_no_act_and_no_engine(self):
        """WHAT IT IS NOT, re-asserted after the correction added a reader."""
        held = self.running("refuse-surface")
        observation = self.observing(held)
        for act in ("admit", "claim", "launch", "dispatch", "conclude",
                    "start", "delivered", "ending", "command",
                    "refresh_runtime"):
            self.assertFalse(hasattr(observation, act), act)
        self.assertTrue(hasattr(observation, "observe_exchange"))
        # AND THE READER IT BUILDS ITSELF IS REAL, asked of an observation
        # this case did not substitute: the correction's whole point is that
        # `status --observe` carries one.
        self.assertTrue(callable(
            self.observing(held, substitute=False).job_task))


if __name__ == "__main__":
    unittest.main()
