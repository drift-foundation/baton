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

from baton_v12.worker_manager import attempts, workspaces

from tools import job_task, single_worker, stage_execution

from tests.job_manager import fixtures
from tests.manager import input_roots
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


if __name__ == "__main__":
    unittest.main()
