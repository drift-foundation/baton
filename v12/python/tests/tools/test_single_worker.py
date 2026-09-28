"""W76207 -- the deployable one-worker Job Manager composition.

These are production-seam tests: real Job, control and Authority stores, the
public manager loop, real workspace/input/launch composition, and only the OCI
engine boundary replaced with a recording process capability.
"""

import copy
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

# THE IMAGE'S OWN MODULES, ON THIS SUITE'S OWN PATH.
#
# W71917: this suite drives the real `baton_worker` at `serve_exchange` in two
# of its classes, and it did so RELYING ON A SIDE EFFECT -- `test_claude_agent`
# inserts the worker directory at module scope, and a single-process discovery
# run happens to import that module first. That is invisible to the canonical
# discovery gate and false under the parallel runner, whose shards are one
# TestCase class in a fresh interpreter: fifteen cases here errored with
# `ModuleNotFoundError: No module named 'baton_worker'` the first time the
# corrected gate could run at all.
#
# The dependency belongs to whoever imports it, so it is declared here in the
# same shape the three sibling suites already use. It is not W71917's defect;
# it is W81857's `worked()` helper reaching the image's module, and this Work
# is simply the first thing that made the sharded gate runnable.
WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))

from baton_v12.authority import Authority
from baton_v12.contracts import (ContractRefusal, digest, digest_of_bytes,
                                 forget_secret, job_input_identity,
                                 live_secret, remember_secret)
from baton_v12.job_manager import (JobStore, reconcile, status, submit,
                                   sweep)
from baton_v12.worker_manager import (ControlStore,
                                      attempt_activity_of,
                                      attempt_preparation_failure_of,
                                      attempt_runtime_of,
                                      attempt_start_failure_of,
                                      certify_profile, claimed_offers_for,
                                      configure_workspace_group,
                                      configured_workspace_group)
from baton_v12.worker_manager import documents as worker_documents
from baton_v12.worker_manager import exchange, launch

from baton_v12.worker_manager import source_boundary
from tests.manager import disk_roots, input_roots
from tests.job_manager import fixtures
from tools import single_worker
from tools.user_credentials import SourceRefusal


ADAPTER = "sha256:" + "d" * 64
AUTHORITY_UUID = "0000000a" + "0" * 24


class TheWorkerSessionForwardsGateDischarge(unittest.TestCase):
    def setUp(self):
        from tests.authority import test_session as sessions
        self.fixture = sessions.SessionCase()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.fixture.work()
        self.work_id = sessions.WORK
        session = self.fixture.claude
        assignment = session.claim({"work_id": self.work_id, "operation_id": "claim-forwarding"})["assignment"]
        session.cancel({"expect": assignment, "operation_id": "fence-forwarding", "reason": "runtime stopped"})
        self.gate = session.project_work(self.work_id)["gate"]["token"]

        class Recording:
            def __init__(self):
                self.calls = []
                self.answer = None
                self.refusal = None

            def __getattr__(self, name):
                return getattr(session, name)

            def satisfy_gate(self, operands):
                self.calls.append(operands)
                try:
                    self.answer = session.satisfy_gate(operands)
                    return self.answer
                except BaseException as refusal:
                    self.refusal = refusal
                    raise

        self.recording = Recording()
        self.wrapper = single_worker._AuthoritySession(self.recording)
        self.port = single_worker.AuthorityPort(self.wrapper, single_worker.claim_signature)
        self.operands = {"work_id": self.work_id, "operation_id": "discharge-forwarding", "gate": self.gate,
                         "evidence": {"kind": "runtime-absent", "runtime": "runtime-forwarding"}}

    def test_wrapper_preserves_the_exact_operand_document_and_session_answer(self):
        before = copy.deepcopy(self.operands)
        answer = self.wrapper.satisfy_gate(self.operands)
        self.assertIs(self.recording.calls[0], self.operands)
        self.assertIs(answer, self.recording.answer)
        self.assertEqual(self.operands, before)
        self.assertEqual(answer, {"gate": self.gate, "kind": "runtime-absent", "phase": "queued"})

    def test_port_crosses_the_wrapper_and_replays_one_real_discharge(self):
        for _ in range(2):
            answer = self.port.satisfy_gate(**self.operands)
            self.assertEqual(self.recording.calls[-1], self.operands)
            self.assertIs(self.recording.calls[-1]["evidence"], self.operands["evidence"])
            self.assertEqual(answer, self.recording.answer)
            self.assertEqual(answer["phase"], "queued")
        self.assertEqual(len(self.recording.calls), 2)
        self.assertIsNone(self.fixture.claude.project_work(self.work_id)["gate"])
        self.assertEqual(len(self.fixture.claude.gate_evidence(self.work_id)), 1)

    def test_authority_refusals_cross_both_wrappers_unchanged(self):
        from baton_v12.authority import Refusal
        for index, changed in enumerate(({"gate": "runtime-quiescence:2"}, {"evidence": {"kind": "runtime-unreachable"}})):
            with self.subTest(changed=changed):
                operands = dict(self.operands, **changed, operation_id=f"refused-forwarding-{index}")
                with self.assertRaises(Refusal) as caught:
                    self.port.satisfy_gate(**operands)
                self.assertIs(caught.exception, self.recording.refusal)
                self.assertEqual(self.recording.calls[-1], operands)
                self.assertIs(self.recording.calls[-1]["evidence"], operands["evidence"])
                self.assertEqual(self.fixture.claude.project_work(self.work_id)["gate"]["token"], self.gate)
                self.assertEqual(self.fixture.claude.gate_evidence(self.work_id), [])


class Engine:
    """One observable OCI process boundary, without a daemon or container."""

    def __init__(self):
        self.vectors = []
        self.runtime_id = None
        self.labels = {}
        self.image = None
        self.mounts = []
        # W275774: whether the composed container is RUNNING, which `create` leaves
        # false and `start` makes true.
        self.running = False

    def __call__(self, argv, *, seconds=None):
        del seconds
        self.vectors.append(list(argv))
        if activating(argv):
            # W275774 review 16:29:48Z: ACTIVATION IS A STATE CHANGE HERE, not a
            # generic success. A fixture that answered `Running=True` straight after
            # `create` could not tell a bound-but-inert container from a running one,
            # which is the very distinction the token boundary exists to enforce.
            if argv[2] != self.runtime_id:
                return self.answer(status=1, stderr="no such container")
            self.running = True
            return self.answer()
        if launching(argv):
            self.runtime_id = "runtime-single-1"
            # CREATED AND INERT unless this vector is the single-act `run`.
            self.running = argv[1] == "run"
            self.image = argv[-1]
            self.labels = {}
            self.mounts = []
            for index, operand in enumerate(argv[:-1]):
                if operand == "--label":
                    name, value = argv[index + 1].split("=", 1)
                    self.labels[name] = value
                elif operand == "--mount":
                    parts = dict(part.split("=", 1) for part in
                                 argv[index + 1].split(",") if "=" in part)
                    self.mounts.append({"Source": parts["source"],
                                        "Destination": parts["target"],
                                        "RW": parts["readonly"] == "false"})
            return self.answer(stdout=self.runtime_id + "\n")
        if argv[1] == "ps":
            if self.runtime_id is None:
                return self.answer()
            row = {"ID": self.runtime_id, "Image": self.image,
                   "Labels": dict(self.labels)}
            return self.answer(stdout=json.dumps(row) + "\n")
        if argv[1] == "inspect":
            body = {"Id": self.runtime_id,
                    "State": {"Running": self.running},
                    "Mounts": list(self.mounts)}
            return self.answer(stdout=json.dumps(body))
        return self.answer()

    @staticmethod
    def answer(status=0, stdout="", stderr=""):
        return {"status": status, "stdout": stdout, "stderr": stderr}

    @property
    def starts(self):
        """The LAUNCH vectors: one per container composed, either shape."""
        return [one for one in self.vectors if launching(one)]

    @property
    def activations(self):
        return [one for one in self.vectors if activating(one)]


# W275774: A LAUNCH IS EITHER ENGINE SHAPE, and these doubles have to know both.
#
# A governed start composes `create` and then `start`, because a resource token must be
# bound to a container that exists and is NOT yet running -- see `oci.ACTIVATIONS`. An
# ungoverned start still composes `run --detach`. Both are ONE LAUNCH of one container,
# so every fixture below that used to ask `argv[1] == "run"` asks this instead, and the
# behavioural checks each one performs are unchanged.
LAUNCHING = ("run", "create")


def launching(argv):
    return len(argv) > 1 and argv[1] in LAUNCHING


def activating(argv):
    """The second act of a governed launch: running what `create` left inert."""
    return len(argv) > 1 and argv[1] == "start"


def running_now(argv):
    """The vector after which a container is RUNNING, either shape.

    W275774 review 16:29:48Z: the fixtures that model a process dying "after the
    engine call" were keyed on `run`, which both created and ran the container. With
    a governed two-act launch that instant moved: `create` leaves the container inert
    and `start` is when it begins running. These fixtures are about a death AFTER a
    runtime exists and runs, so they key on that instant rather than on the first of
    the two acts -- which preserves exactly the state each case was written to reach.
    """
    return len(argv) > 1 and argv[1] in ("run", "start")


class TheContextConfigurationIsRequiredAndClosed(unittest.TestCase):
    def test_exact_reserved_declaration_rejects_stale_media_and_other_shapes(self):
        from tests.manager.test_claude_context import declaration
        from baton_v12.worker_manager import provider_context
        import baton_worker
        import copy
        good = declaration()
        single_worker._context_declaration([good])
        for media in (["application/json"], ["application/json", "application/octet-stream"], [], ["text/plain"]):
            wrong = copy.deepcopy(good)
            wrong["constraints"]["allowed_media_types"] = media
            for check in (single_worker._context_declaration, provider_context.context_output_declaration):
                with self.subTest(media=media, owner=check):
                    with self.assertRaises(ContractRefusal):
                        check([wrong])
            with self.assertRaises(baton_worker.WorkerFault):
                baton_worker.context_declaration({"role": "review"}, [wrong])
        for key, value in (("path", "another"), ("type", "file-result"), ("required", True)):
            wrong = copy.deepcopy(good)
            wrong[key] = value
            with self.assertRaises(ContractRefusal):
                single_worker._context_declaration([wrong])
        for selected in ([], [good, good]):
            with self.assertRaises(ContractRefusal):
                single_worker._context_declaration(selected)

    def test_legacy_implementation_cannot_silently_omit_context(self):
        from tests.manager.test_claude_context import ServingContextCase
        case = ServingContextCase()
        self.addCleanup(case.doCleanups)
        case.setUp()
        value = case.worker("implementation")["deployment"]
        value.pop("provider_context")
        value["schema"] = "baton.v12.single-worker-deployment/4"
        with self.assertRaises(ContractRefusal):
            single_worker._held(value)
        # The one shared submitted manifest is admissible to isolated review.
        self.assertNotIn("provider_context", single_worker._held(case.worker("review")["deployment"], roles=("review",)))


class SingleWorkerCase(unittest.TestCase):
    def setUp(self):
        # W71917: A DISK-BACKED ROOT, because the boundary this composition
        # now crosses refuses a workspace on a memory filesystem. On a host
        # whose `/tmp` is a tmpfs, `TemporaryDirectory` answered a directory
        # `compose_source_boundary` correctly declines, so every case here
        # would have proved the refusal instead of the delivery.
        self.root = disk_roots.disk_backed_under(self)
        self.authority_path = os.path.join(self.root, "authority.sqlite3")
        self.job_path = os.path.join(self.root, "jobs.sqlite3")
        self.control_path = os.path.join(self.root, "control.sqlite3")
        self.source = os.path.join(self.root, "source")
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.source)
        os.makedirs(self.storage)
        with open(os.path.join(self.source, "worker-task.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("write one bounded proposal\n")

        authority = Authority.create(
            self.authority_path, authority_uuid=AUTHORITY_UUID,
            clock=lambda: fixtures.NOW)
        self.principal = authority.principal_of(fixtures.WHO)
        authority.create_work(fixtures.WORK_A, fixtures.ROUTE,
                              contract="v12-assignment-1",
                              operation_id="create-single-worker")
        authority.add_route_handler(fixtures.ROUTE, fixtures.WHO)
        authority.dispose()

        given, _assignment = input_roots.documents(
            work_ref={"authority_uuid": AUTHORITY_UUID,
                      "work_id": fixtures.WORK_A},
            participant=fixtures.WHO, generation=1,
            runtime_attempt_id="unused",
            policy_digest=fixtures.POLICY_DIGEST,
            profile_digest=fixtures.PROFILE)
        # W81115: THE PRODUCTION PROFILE, which the conformance vector is not.
        #
        # That vector's human contract is a Markdown dossier and it stages its
        # source at `workspace/source`; both are correct for a generic
        # manifest and neither is what the certified Claude workload reads.
        # This profile is the approved one: the task document IS the input
        # manifest's human-contract artifact, and the source lands at the one
        # destination the workload stages.
        self.task_document = os.path.join(self.root, "task.json")
        # W71917 bumped the workload contract to `/2` and added the profile
        # and its declared base. This deployment's fixture nominates an
        # ordinary directory, so the profile is `generic` and no base is
        # declared -- a generic profile carrying one is refused by the profile
        # package itself.
        self.task_bytes = json.dumps(
            {"schema": "baton.dogfood-task/2", "task_id": "w81115-bootstrap",
             "instructions": "write one bounded proposal",
             "source_root": "source",
             "source_profile": "generic", "declared_base": None,
             "verification": ["python3", "-c", "raise SystemExit(0)"]},
            sort_keys=True).encode("utf-8")
        with open(self.task_document, "wb") as writing:
            writing.write(self.task_bytes)
        self.manifest = copy.deepcopy(given)
        self.manifest["sources"][0]["destination"] = (
            single_worker.SOURCE_DESTINATION)
        self.manifest["human_contract"] = {
            "artifact_id": "w81115-task-1",
            "media_type": "application/json",
            "bytes": len(self.task_bytes),
            "content_digest": digest_of_bytes(self.task_bytes),
            "locator": "artifact://contracts/w81115-task-1"}
        # W71917: THE EMPTY MOUNTPOINT'S MANIFEST, NOT THE SOURCE'S.
        #
        # This used to call `directory_manifest(self.source)` -- the full
        # no-follow walk of the nominated tree that the ordinary copied
        # bootstrap performed and this Work retires. What the deployment now
        # stages at that destination is an empty directory for the read-only
        # bind to land on, so the empty tree is what the frozen manifest
        # declares, and `_source_manifest` holds a configuration to exactly
        # that.
        self.manifest["sources"][0]["content_manifest"] = {
            "entries": [], "entry_count": 0, "total_bytes": 0,
            "tree_digest": single_worker.EMPTY_TREE_DIGEST}
        # AND THE DESCRIPTOR DECLARES THE BOUNDARY. A source descriptor with
        # no declaration is a STAGED source whose content the manager measured;
        # mounting over one would deliver material its manifest does not
        # describe, and `declared_profile` refuses it.
        self.source_profile = "generic"
        self.manifest["sources"][0]["consumption"] = (
            source_boundary.source_consumption(self.source_profile))
        self.manifest.pop("manifest_digest")
        self.manifest["manifest_digest"] = digest(self.manifest)
        self.config = {
            "schema": single_worker.CONFIG_SCHEMA,
            "authority_store": self.authority_path,
            "authority_uuid": AUTHORITY_UUID,
            "participant": fixtures.WHO,
            "principal": self.principal,
            "profile_name": "reference",
            "profile_digest": fixtures.PROFILE,
            "policy_digest": fixtures.POLICY_DIGEST,
            "adapter_name": "docker-single-worker",
            "adapter_digest": ADAPTER,
            "engine": "docker",
            "image_digest": self.manifest["worker_image_digest"],
            "network": "none",
            "workspace_storage": self.storage,
            "workspace_group": os.getgid(),
            "launch_home": os.path.join(self.root, "launch"),
            "credential_home": os.path.join(self.root, "credentials"),
            "credential_sources": None,
            "credential_slots": ["api"],
            "credential_profile": {
                "api": {"provider": "fixture",
                        "reference": "fixture/one"}},
            "nominated_source": self.source,
            # W71917: EXPLICIT, AND ABOVE THE BOUNDED SCRATCH. The floor is
            # `source_boundary.MIN_WORKSPACE_BYTES` -- the whole of the
            # runtime's private `/tmp` and `/dev/shm` -- because a workspace
            # that would have fitted in scratch establishes nothing about the
            # five uses that must not rely on it. ONE MEMBER: the entry count
            # that stood beside it reached no mount and no runtime, and the
            # ruling is that this document may not declare what nothing
            # applies.
            "workspace_capacity": {
                "max_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1},
            "input_manifest": self.manifest,
            "task_document": self.task_document,
            "launch_contract": "v12-assignment-1",
            "launch_role": "implementation",
            # W81857's three: where an answered, frozen, collected result is
            # handed on, and what is decided about its untrusted bytes first.
            "review_route": "rview",
            "retention_policy_digest": "sha256:" + "5" * 64,
            "retention_disposition": "retain"}
        self.secret = "single-worker-secret-" + "7" * 40
        self.addCleanup(self._forget_secret)
        self.submission = fixtures.submission(
            jobs=[fixtures.job(
                input_digest=job_input_identity(self.manifest),
                policy_digest=fixtures.POLICY_DIGEST,
                stages=[fixtures.stage(
                    work_id=fixtures.WORK_A,
                    profile_name="reference",
                    profile_digest=fixtures.PROFILE)])])

    def stores(self, incarnation):
        # W83781: the store's Authority binding is the same one this
        # deployment's configuration names, which is the ordinary production
        # shape. `TheAuthorityBindingIsProvedBeforeAnythingIsConfigured`
        # is where they deliberately disagree.
        job = JobStore.open(self.job_path, authority_uuid=AUTHORITY_UUID,
                            incarnation=incarnation,
                            clock=lambda: fixtures.NOW)
        control = ControlStore.open(self.control_path,
                                    incarnation=incarnation,
                                    clock=lambda: fixtures.NOW)
        self.addCleanup(job.close)
        self.addCleanup(control.close)
        return job, control

    def operations(self, job, control, engine):
        return single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW)

    def _forget_secret(self):
        while live_secret(self.secret):
            forget_secret(self.secret)

    def commanded(self, job, operations):
        """Drive the pipeline until the worker has been given its command.

        W81857 CHANGED WHAT THIS WAITS FOR, and the change is the Work. This
        used to wait for `running`, which the projection answered as soon as a
        runtime identity was attached -- so every case below proved its
        composition against a stage the control plane called "working" while
        the container sat idle with nothing to do. `waiting` is the honest
        state at this point: the runtime is up, the durable command sequence is
        published, and no worker has accepted it. These cases run against a
        fake engine, so nothing inside a container answers, and `waiting` is
        where a correct pipeline stops.
        """
        for _ in range(6):
            reconcile(job, operations, now=fixtures.NOW)
            projected = status(job, operations, observed_at=fixtures.NOW)
            if projected["jobs"][0]["stages"][0]["state"] == "waiting":
                return projected
        self.fail("the one-worker pipeline did not reach a commanded worker")


class TheHostPreparationIsAccountedForBeforeAnyTaskStart(SingleWorkerCase):
    """W285464 under the owner's amended TOK-7 (2026-09-27).

    The Host manager may now allocate, stage, publish and set initial permissions
    itself. What came with that permission is what these cases drive: the host must
    DURABLY RECORD that its preparation finished, must REVALIDATE the prepared
    objects before the task is admitted, and must not launch while any host writer
    could still be finishing. A deadline proves none of it.

    H1 and H7 in part, and H4 and H6 at this seam; the composed fixture is the real
    ordinary no-context/no-review path with a fake engine.
    """

    def prepared_record(self, control, attempt_id):
        from baton_v12.worker_manager import workspaces
        return workspaces.preparation_completed(control, attempt_id)

    def test_the_finished_preparation_is_recorded_and_names_what_it_prepared(self):
        """H1: the durable account exists, and it describes the objects the task is
        started over rather than merely saying something happened."""
        from baton_v12.worker_manager import attempts as manager_attempts
        from baton_v12.worker_manager import tokens

        engine = Engine()
        job, control = self.stores("prepared-record")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        self.assertEqual(len(engine.starts), 1)
        recorded = self.prepared_record(control, attempt_id)
        self.assertIsNotNone(recorded, "no durable preparation account was written")
        self.assertEqual(recorded["attempt_id"], attempt_id)
        self.assertIn("task.json", recorded["published"])
        # THE WORKSPACE IT RECORDS IS THE OBJECT THE TASK'S OWN TOKEN CONTENDS FOR,
        # compared through the attempt row rather than through this record.
        attempt = manager_attempts._require_attempt(control, attempt_id)
        self.assertEqual(recorded["workspace"],
                         tokens.workspace_identity(attempt))
        self.assertNotEqual(recorded["inputs"], recorded["workspace"])
        operations.close()

    def test_no_task_starts_while_a_host_writer_could_still_finish(self):
        """H6: an admitted allocation with no completion means somebody may still
        be writing, and a deadline says nothing about that.

        The window is committed through the owner's own API before the worker
        reaches its start gate, so what refuses is the gate rather than a fixture.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("writer-still-open")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        roots = workspaces.assignment_workspace(
            workspaces.configured_workspace_group(control), self.storage,
            attempt_id, control=control)
        # A DIFFERENT ATTEMPT, because this one's task token is now live and an
        # allocation admission is refused for THAT reason -- measured, when the
        # task-first guard landed. What this case is about is the gate reading a
        # standing allocation, so it uses an attempt with no live token.
        workspaces._admitted_allocation(control, "attempt-elsewhere",
                                        "a second allocation")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.require_prepared(control, "attempt-elsewhere", roots,
                                        "starting this attempt's runtime")
        self.assertIn("may still be finishing", str(refused.exception))
        self.assertIn("allocation", str(refused.exception))
        operations.close()

    def test_no_task_starts_when_nothing_recorded_the_preparation(self):
        """H6: absent account, no launch -- the honest state of an interrupted
        preparation on the tick that follows it."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("nothing-recorded")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        roots = workspaces.assignment_workspace(
            workspaces.configured_workspace_group(control), self.storage,
            "attempt-never-prepared", control=control)
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.require_prepared(control, "attempt-never-prepared", roots,
                                        "starting this attempt's runtime")
        self.assertIn("recorded no completed host preparation",
                      str(refused.exception))
        self.assertIn("UNKNOWN", str(refused.exception))
        operations.close()

    def test_a_replaced_prepared_root_refuses_before_any_task_is_created(self):
        """H4: the objects are compared, not the record with itself.

        The workspace this preparation completed over is moved aside and another
        directory put at the same path -- same characters, different inode.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("replaced-root")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        recorded = self.prepared_record(control, attempt_id)
        self.assertIsNotNone(recorded)
        roots = {"inputs": os.path.join(self.storage, attempt_id, "inputs"),
                 "workspace": os.path.join(self.storage, attempt_id, "workspace")}
        # STILL THE SAME OBJECTS: the gate passes before anything is replaced.
        workspaces.require_prepared(control, attempt_id, roots,
                                    "starting this attempt's runtime")
        # THE ROOT CANNOT BE RENAMED INSIDE THE HOME, and that is itself evidence
        # the freeze happened: `compose_input_root` closes the home at `0555`, so
        # `os.rename` is EPERM -- measured, when I first wrote this case that way.
        # What a replacement therefore looks like at this gate is a composition
        # answering a DIFFERENT object at the same role, which is exactly what the
        # comparison exists to catch.
        self.assertEqual(
            stat.S_IMODE(os.lstat(os.path.dirname(roots["workspace"])).st_mode),
            0o555)
        replacement = os.path.join(self.root, "another-workspace")
        os.mkdir(replacement)
        roots = dict(roots, workspace=replacement)
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.require_prepared(control, attempt_id, roots,
                                        "starting this attempt's runtime")
        self.assertIn("is not the resource that was prepared",
                      str(refused.exception))
        self.assertIn("workspace", str(refused.exception))
        # AND THE ORIGINAL EVIDENCE IS UNCHANGED: nothing repinned itself.
        self.assertEqual(self.prepared_record(control, attempt_id), recorded)
        operations.close()

    def test_the_record_replays_rather_than_recording_a_second_preparation(self):
        """H5 at this seam: a restart walks the same preparation and writes the same
        operands at the same identity, so the account is one fact rather than two."""
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("replayed-record")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        recorded = self.prepared_record(control, attempt_id)
        roots = {"inputs": os.path.join(self.storage, attempt_id, "inputs"),
                 "workspace": os.path.join(self.storage, attempt_id, "workspace")}
        again = workspaces.record_preparation(control, attempt_id, roots,
                                             ("task.json",))
        self.assertEqual(again["attempt_id"], attempt_id)
        self.assertEqual(self.prepared_record(control, attempt_id), recorded)
        operations.close()


class ThePreparationOWNSTheRootsForItsWholeWriterLifetime(SingleWorkerCase):
    """W285464 review 2026-09-27T16-13-26Z, and the defect it reached.

    The allocation's own window closes when creation ends, so the source
    mountpoint, the task publication, the protocol pair and the freeze all ran with
    nothing excluding a competing admission -- the reviewer interposed at
    `compose_input_root`, before its publication, and a REAL removal was admitted.
    A gate before the start does not make that safe: the competing writer has
    already been admitted over material somebody was still writing.

    H3 and H6 at the composed seam; every act below is the owner's own API.
    """

    def interposed(self, act, label):
        """Run `act` inside the real staging writer, before it publishes."""
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        honest = workspaces.compose_input_root
        outcome = []

        def paused(*arguments, **named):
            attempt = named["runtime_attempt_id"]
            try:
                act(control, attempt)
                outcome.append(None)
            except ContractRefusal as refused:
                outcome.append(str(refused))
            return honest(*arguments, **named)

        with mock.patch.object(workspaces, "compose_input_root",
                               side_effect=paused):
            projected = self.commanded(job, operations)
        self.assertEqual(len(outcome), 1, "the staging writer was never reached")
        return control, projected, outcome[0], engine

    def test_a_removal_cannot_enter_while_staging_can_still_write(self):
        """The reviewer's own schedule, kept as my regression."""
        from baton_v12.worker_manager import workspaces

        control, projected, why, engine = self.interposed(
            lambda control, attempt: workspaces._admitted_removal(
                control, attempt, "competing with input publication"),
            "staging-removal")
        self.assertIsNotNone(why, "a removal was admitted mid-staging")
        self.assertIn("host preparation", why)
        self.assertIn("may still be creating, staging, publishing or freezing", why)
        # AND THE ORDINARY PATH STILL COMPLETED: the exclusion refuses the
        # competitor rather than breaking the preparation that owns the roots.
        self.assertEqual(len(engine.starts), 1)

    def test_a_cleanup_cannot_enter_while_staging_can_still_write(self):
        from baton_v12.worker_manager import workspaces

        _control, _projected, why, engine = self.interposed(
            lambda control, attempt: workspaces.admit_cleanup(
                control, attempt,
                {"operation": f"cleanup:{attempt}", "signature": "sig-1",
                 "incarnation": "probe"}, "competing cleanup"),
            "staging-cleanup")
        self.assertIsNotNone(why, "a cleanup was admitted mid-staging")
        self.assertIn("host preparation", why)
        self.assertEqual(len(engine.starts), 1)

    def test_an_adoption_cannot_enter_while_staging_can_still_write(self):
        """ONE INTERPOSED SCHEDULE PER CASE, measured: a subTest loop sharing this
        fixture reuses the attempt identity the submission derives, so the second
        iteration adopted an already-staged home, never reached the writer, and
        failed for that reason rather than on the rule."""
        from baton_v12.worker_manager import workspaces

        _control, _projected, why, engine = self.interposed(
            lambda control, attempt: workspaces._admitted_adoption(
                control, attempt, "competing adoption"),
            "staging-adoption")
        self.assertIsNotNone(why, "an adoption was admitted mid-staging")
        self.assertIn("host preparation", why)
        self.assertEqual(len(engine.starts), 1)

    def test_a_second_ALLOCATION_cannot_enter_while_staging_can_still_write(self):
        from baton_v12.worker_manager import workspaces

        _control, _projected, why, engine = self.interposed(
            lambda control, attempt: workspaces._admitted_allocation(
                control, attempt, "competing allocation"),
            "staging-allocation")
        self.assertIsNotNone(why, "a second allocation was admitted mid-staging")
        self.assertIn("host preparation", why)
        self.assertEqual(len(engine.starts), 1)

    def test_an_UNRELATED_attempt_is_free_while_this_one_prepares(self):
        """The exclusion is per-attempt, so it serializes nothing it should not.

        Inside the same interposed schedule -- this attempt's staging holding its
        roots -- an UNRELATED attempt takes its own preparation ownership.
        """
        from baton_v12.worker_manager import workspaces

        elsewhere = []

        def both(control, attempt):
            elsewhere.append(workspaces.admit_preparation(
                control, "attempt-elsewhere", "an unrelated preparation"))
            workspaces._admitted_removal(control, attempt,
                                        "competing with input publication")

        control, _projected, why, engine = self.interposed(both,
                                                          "staging-unrelated")
        self.assertIsNotNone(why)
        self.assertIn("host preparation", why)
        self.assertEqual([one.ordinal for one in elsewhere], [1])
        self.assertEqual([one for one, _ in workspaces.standing_preparation(
            control, "attempt-elsewhere")], [1])
        self.assertEqual(len(engine.starts), 1)

    def test_the_window_is_closed_by_the_COMPLETION_and_not_by_the_clock(self):
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("window-closed")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        # AFTERWARDS: the completion exists and the window is no longer standing,
        # so ordinary cleanup and removal are free again.
        self.assertIsNotNone(workspaces.preparation_completed(control,
                                                             attempt_id))
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        workspaces.refuse_if_held(control, self.storage, attempt_id,
                                  "a later ordinary act")

    def test_an_interrupted_preparation_leaves_the_window_STANDING(self):
        """H6: interruption is not an ending, and the hold is what says so.

        The window is opened through the owner's API and no completion follows --
        which is what a process that died mid-staging leaves behind. Every other
        admission is then refused, and the start gate refuses too.
        """
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("interrupted-preparation")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        owned = workspaces.admit_preparation(control, "attempt-interrupted",
                                            "a preparation that then died",
                                            "execution-one")
        self.assertEqual(owned.ordinal, 1)
        self.assertEqual([one for one, _ in workspaces.standing_preparation(
            control, "attempt-interrupted")], [1])
        for act in (lambda: workspaces._admitted_removal(
                        control, "attempt-interrupted", "a later removal"),
                    lambda: workspaces._admitted_adoption(
                        control, "attempt-interrupted", "a later adoption"),
                    lambda: workspaces.refuse_if_held(
                        control, self.storage, "attempt-interrupted",
                        "a later ordinary act")):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal) as refused:
                    act()
                self.assertIn("host preparation 1", str(refused.exception))
        # AND IT IS NOT TAKEN OVER BY ANYBODY WHO ASKS. My first version of this
        # case asserted that a second `admit_preparation` adopted ordinal 1
        # unconditionally, and review 2026-09-27T16-41-41Z was right to refuse that:
        # HOST-8 excludes a duplicate MANAGER, not a second execution inside one, so
        # an ordinal anybody receives is not authority to write.
        for asking in (None, "another-execution"):
            with self.subTest(execution=asking):
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.admit_preparation(
                        control, "attempt-interrupted",
                        "a second execution with no cessation evidence", asking)
                self.assertIn("whether that writer has stopped is UNKNOWN",
                              str(refused.exception))
        # AND THE ACT THAT HOLDS THE CAPABILITY CONTINUES ITS OWN WINDOW, which is
        # the one ground that needs no new evidence: it is the same act, and a name
        # for the same attempt is NOT that -- review 2026-09-27T17-01-18Z reached a
        # second admission through exactly that equality while the first writer was
        # still able to finish.
        again = workspaces.admit_preparation(
            control, "attempt-interrupted", "the same act continuing",
            "execution-one", holding=owned)
        self.assertEqual(again.ordinal, 1)
        self.assertIs(again, owned)


class ThePreparationMatrixIsClosedInBothDirections(SingleWorkerCase):
    """W285464 review 2026-09-27T16-41-41Z, the three edges it reached.

    My admission checked removal, cleanup and adoption and omitted the standing
    ALLOCATION; custody's reciprocal callback knew about removals and maintenance
    windows and not about this one; and a second `admit_preparation` was answered
    the standing ordinal without anything proving the first writer had stopped.
    Each is driven here through the owner's own APIs.
    """

    def stored(self, label):
        _job, control = self.stores(label)
        from baton_v12.worker_manager import workspaces
        workspaces.configure_workspace_storage(control, self.storage)
        return control

    def excluded_by(self, label, act, named):
        """`act` is admitted first; a new preparation must then refuse.

        ONE STORE PER CASE, measured twice now: this fixture answers one control
        store per test, so a subTest loop left the first iteration's window standing
        and the later acts refused each other instead of refusing the preparation.
        """
        from baton_v12.worker_manager import workspaces

        control = self.stored(f"matrix-{label}")
        act(control)
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_preparation(control, "attempt-1",
                                         "a competing preparation",
                                         "execution-one")
        self.assertIn(named, str(refused.exception))
        self.assertIn("recorded no completion", str(refused.exception))
        self.assertEqual(workspaces.standing_preparation(control, "attempt-1"),
                         [])

    def test_an_admitted_allocation_excludes_a_new_preparation(self):
        """The edge the reviewer reached: my admission omitted this one."""
        from baton_v12.worker_manager import workspaces

        self.excluded_by("allocation",
                         lambda control: workspaces._admitted_allocation(
                             control, "attempt-1", "an existing allocator"),
                         "allocation 1")

    def test_an_admitted_removal_excludes_a_new_preparation(self):
        from baton_v12.worker_manager import workspaces

        self.excluded_by("removal",
                         lambda control: workspaces._admitted_removal(
                             control, "attempt-1", "an existing remover"),
                         "removal 1")

    def test_an_admitted_adoption_excludes_a_new_preparation(self):
        from baton_v12.worker_manager import workspaces

        self.excluded_by("adoption",
                         lambda control: workspaces._admitted_adoption(
                             control, "attempt-1", "an existing adopter"),
                         "adoption 1")

    def test_an_admitted_cleanup_excludes_a_new_preparation(self):
        from baton_v12.worker_manager import workspaces

        self.excluded_by("cleanup",
                         lambda control: workspaces.admit_cleanup(
                             control, "attempt-1",
                             {"operation": "cleanup:attempt-1",
                              "signature": "sig-1", "incarnation": "probe"},
                             "an existing cleanup"),
                         "cleanup 1")

    def test_a_standing_preparation_excludes_a_custody_claim(self):
        """The reciprocal edge custody was missing."""
        from baton_v12.worker_manager import custody, workspaces

        control = self.stored("matrix-custody")
        workspaces.admit_preparation(control, "attempt-1", "preparing inputs",
                                     "execution-one")
        with self.assertRaises(ContractRefusal) as refused:
            custody._claim_episode(
                control, "attempt-1", "workspace", "normalize",
                "sha256:" + "e" * 64,
                custody._custody_identity(self.storage, "attempt-1",
                                          "workspace", "normalize"))
        self.assertIn("host preparation 1", str(refused.exception))
        self.assertEqual(custody.custody_holds(control, "attempt-1",
                                               "workspace"), [])

    def test_a_standing_preparation_excludes_a_maintenance_act(self):
        """And the facility's own shared reader, so the edge holds both ways."""
        from baton_v12.worker_manager import maintenance, workspaces

        control = self.stored("matrix-maintenance")
        workspaces.admit_preparation(control, "attempt-1", "preparing inputs",
                                     "execution-one")
        why = maintenance._conflicting(control, "attempt-1", "workspace")
        self.assertIsNotNone(why)
        self.assertIn("host preparation 1", why)

    def test_an_unnamed_or_foreign_execution_cannot_take_the_window(self):
        from baton_v12.worker_manager import workspaces

        control = self.stored("matrix-adoption")
        owned = workspaces.admit_preparation(control, "attempt-1",
                                            "the first writer", "execution-one")
        self.assertEqual(owned.ordinal, 1)
        for asking in (None, "execution-two"):
            with self.subTest(execution=asking):
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.admit_preparation(control, "attempt-1",
                                                 "a second execution", asking)
                self.assertIn("whether that writer has stopped is UNKNOWN",
                              str(refused.exception))
                self.assertIn("ordinal is not authority to write",
                              str(refused.exception))
        # EVEN THE SAME NAME IS REFUSED WITHOUT THE CAPABILITY, which is the
        # correction: only the act HOLDING the ownership continues it.
        with self.assertRaises(ContractRefusal):
            workspaces.admit_preparation(control, "attempt-1", "resuming by name",
                                         "execution-one")
        self.assertIs(workspaces.admit_preparation(
            control, "attempt-1", "resuming with the capability", "execution-one",
            holding=owned), owned)

    def test_a_HELD_GUARD_IS_NOT_A_GROUND_and_the_uncertainty_is_held(self):
        """MY OWN GROUND, WITHDRAWN, and the record says why.

        I had allowed a takeover when the window's incarnation differed and this
        process held the manager instance guard, arguing a gone process leaves no
        in-process writer. Review 2026-09-27T17-26-12Z is right that the premise was
        unproved: a held flock establishes PRESENT exclusivity, not that the previous
        process died or that its writers drained -- and my own fixture only relabelled
        an incarnation inside one live process, which is not an observation of
        anything. It also reached `os.path.realpath` under a write lock, which DB-1
        and DB-2 forbid.

        So the uncertainty is HELD, and what resolves it is a reconciliation that
        establishes the earlier writer ended -- which for a writer that RETURNS is the
        release recorded by its own unwinding, and for a manager that DIED mid-write is
        W285465's restart work.
        """
        from baton_v12.worker_manager import workspaces

        control = self.stored("guard-not-a-ground")
        earlier = workspaces.admit_preparation(control, "attempt-1",
                                               "an earlier manager's preparation",
                                               "execution-one")
        self.assertEqual(earlier.ordinal, 1)
        guard = workspaces.hold_manager_instance(control, self.storage)
        self.addCleanup(guard.release)
        control.incarnation = "manager-after-restart"
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_preparation(control, "attempt-1",
                                         "the successor's preparation",
                                         "execution-two")
        self.assertIn("whether that writer has stopped is UNKNOWN",
                      str(refused.exception))
        self.assertIn("reconciled", str(refused.exception))
        self.assertEqual([one for one, _ in workspaces.standing_preparation(
            control, "attempt-1")], [1])

    def test_a_RETURNED_writer_releases_its_window_and_that_is_the_cessation(self):
        """The one in-process ending that IS provable: the writer returned.

        Reaching the release is being inside that act's own unwinding, so there is no
        writer left -- no deadline, no label, no inference about another process. A
        manager that dies mid-write runs no unwinding, which is exactly why that case
        stays held.
        """
        from baton_v12.worker_manager import workspaces

        control = self.stored("released-window")
        owned = workspaces.admit_preparation(control, "attempt-1", "preparing",
                                             "execution-one")
        self.assertEqual([one for one, _ in workspaces.standing_preparation(
            control, "attempt-1")], [1])
        # ONLY THE HOLDER MAY RELEASE.
        with self.assertRaises(ContractRefusal):
            workspaces.release_preparation(control, None, "somebody else")
        workspaces.release_preparation(control, owned,
                                       "the writer returned without completing")
        self.assertEqual(workspaces.standing_preparation(control, "attempt-1"), [])
        # AND A RELEASE IS NOT A COMPLETION: the start gate still refuses.
        self.assertIsNone(workspaces.preparation_completed(control, "attempt-1"))
        roots = {"inputs": os.path.join(self.storage, "attempt-1", "inputs"),
                 "workspace": os.path.join(self.storage, "attempt-1", "workspace")}
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.require_prepared(control, "attempt-1", roots, "starting")
        self.assertIn("recorded no completed host preparation",
                      str(refused.exception))

    def test_no_FILESYSTEM_read_happens_inside_the_admission_transaction(self):
        """H8 at this admission, and it was a real source violation of mine.

        My withdrawn guard ground called `_real` -- and so `os.path.realpath` -- from
        inside `BEGIN IMMEDIATE`. The instrument records any `realpath` or `lstat` that
        happens while this connection is in a transaction, and asserts the instrument
        itself is live so an unused trap cannot pass.
        """
        from baton_v12.worker_manager import workspaces

        control = self.stored("no-io-under-lock")
        seen = []
        honest_realpath, honest_lstat = os.path.realpath, os.lstat

        def realpath(*arguments, **named):
            if control._connection.in_transaction:
                seen.append(("realpath", arguments[:1]))
            return honest_realpath(*arguments, **named)

        def lstat(*arguments, **named):
            if control._connection.in_transaction:
                seen.append(("lstat", arguments[:1]))
            return honest_lstat(*arguments, **named)

        with mock.patch.object(os.path, "realpath", side_effect=realpath), \
                mock.patch.object(os, "lstat", side_effect=lstat):
            # THE INSTRUMENT IS LIVE: inside a transaction it records.
            control._connection.execute("BEGIN IMMEDIATE")
            os.path.realpath(self.storage)
            control._connection.execute("COMMIT")
            # LIVE, asserted rather than assumed -- `realpath` itself calls `lstat`,
            # so this records more than one entry; what matters is that it records.
            self.assertTrue(seen, "the instrument saw nothing and cannot fail")
            self.assertIn("realpath", [one for one, _ in seen])
            seen.clear()
            owned = workspaces.admit_preparation(control, "attempt-1",
                                                 "preparing", "execution-one")
            second = workspaces.admit_preparation(control, "attempt-1",
                                                  "continuing", "execution-one",
                                                  holding=owned)
        self.assertIs(second, owned)
        self.assertEqual(seen, [],
                         "the preparation admission observed the filesystem while "
                         "holding a write lock")


class OnlyTheHOLDEROfAPreparationMayContinueIt(SingleWorkerCase):
    """W285464 review 2026-09-27T17-01-18Z, and my third correction of one rule.

    First I adopted any standing window. Then I compared an EXECUTION name -- and the
    production path passes the attempt identity, so every re-entry for that attempt
    compared equal and a second act was admitted while the first could still write.
    Continuation is a CAPABILITY now: the object the opening admission answered.
    """

    def test_a_second_call_with_the_production_operands_is_refused(self):
        """The reviewer's own schedule, kept as my regression: the real staging
        writer is paused and the admission is called again with exactly the operands
        the worker passes."""
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("holder-only")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        honest = workspaces.compose_input_root
        outcome = []

        def paused(*arguments, **named):
            attempt = named["runtime_attempt_id"]
            try:
                workspaces.admit_preparation(
                    control, attempt, "a second execution while the first is paused",
                    attempt)
                outcome.append(None)
            except ContractRefusal as refused:
                outcome.append(str(refused))
            return honest(*arguments, **named)

        with mock.patch.object(workspaces, "compose_input_root",
                               side_effect=paused):
            self.commanded(job, operations)
        self.assertEqual(len(outcome), 1)
        self.assertIsNotNone(outcome[0], "a second execution was admitted")
        self.assertIn("ordinal is not authority to write", outcome[0])
        self.assertEqual(len(engine.starts), 1)

    def test_a_caller_cannot_mint_an_ownership(self):
        from baton_v12.worker_manager import workspaces

        with self.assertRaises(ContractRefusal) as refused:
            workspaces.PreparationOwnership("attempt-1", 1)
        self.assertIn("minted by the admission", str(refused.exception))

    def test_an_ownership_is_not_revised_by_its_holder(self):
        from baton_v12.worker_manager import workspaces

        control = self.stores("holder-immutable")[1]
        workspaces.configure_workspace_storage(control, self.storage)
        owned = workspaces.admit_preparation(control, "attempt-1", "preparing",
                                            "execution-one")
        for name in ("_ordinal", "_attempt", "ordinal"):
            with self.subTest(member=name):
                with self.assertRaises(ContractRefusal):
                    setattr(owned, name, 99)
        self.assertEqual(owned.ordinal, 1)
        self.assertEqual(owned.attempt, "attempt-1")

    def test_an_ownership_for_another_window_does_not_continue_this_one(self):
        from baton_v12.worker_manager import workspaces

        control = self.stores("holder-foreign")[1]
        workspaces.configure_workspace_storage(control, self.storage)
        mine = workspaces.admit_preparation(control, "attempt-1", "preparing one",
                                           "execution-one")
        other = workspaces.admit_preparation(control, "attempt-2", "preparing two",
                                            "execution-two")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_preparation(control, "attempt-1",
                                         "another attempt's ownership",
                                         "execution-one", holding=other)
        self.assertIn("ordinal is not authority to write",
                      str(refused.exception))
        self.assertIs(workspaces.admit_preparation(
            control, "attempt-1", "its own ownership", "execution-one",
            holding=mine), mine)

    def test_the_preparation_path_SPAWNS_NOTHING_which_is_the_guard_premise(self):
        """The invariant the takeover ground rests on, driven rather than asserted.

        The guard ground says a gone process has no surviving writer BECAUSE every
        writer of this path is a call in the manager process. That is only true while
        preparation spawns nothing, so this measures it: from the preparation
        admission to the completion record, no subprocess is created and the engine
        is not called.
        """
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("no-subprocess")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        spawned = []
        honest_popen = subprocess.Popen
        honest_admit = workspaces.admit_preparation
        honest_record = workspaces.record_preparation
        watching = {"inside": False}

        def opened(*arguments, **named):
            # THE HONEST FUNCTION, captured before the patch: calling the module
            # attribute here recursed through the patch -- measured, as a
            # RecursionError.
            answer = honest_admit(*arguments, **named)
            watching["inside"] = True
            return answer

        def recorded(*arguments, **named):
            watching["inside"] = False
            return honest_record(*arguments, **named)

        def popen(*arguments, **named):
            if watching["inside"]:
                spawned.append(arguments[:1])
            return honest_popen(*arguments, **named)

        with mock.patch.object(workspaces, "admit_preparation",
                               side_effect=opened), \
                mock.patch.object(workspaces, "record_preparation",
                                  side_effect=recorded), \
                mock.patch.object(subprocess, "Popen", side_effect=popen):
            self.commanded(job, operations)
        self.assertEqual(spawned, [],
                         "host preparation spawned a process, so a gone manager "
                         "could leave a surviving writer and the guard ground is "
                         "no longer sound")
        self.assertEqual(len(engine.starts), 1,
                         "the task still started, after preparation completed")


class TheTaskTOKENIsAcquiredUnderThePreparationCondition(SingleWorkerCase):
    """W285464 review 2026-09-27T17-37-14Z, the oldest outstanding item.

    `require_prepared` is the early refusal and it reads the OBJECTS, which needs a
    filesystem and therefore cannot happen under a lock. That left a gap: a conflict
    arriving between the check and `tokens.acquire` was excluded by nothing. The
    condition now travels INTO the acquisition as `tokens.acquire`'s own
    pure-database `eligible` predicate, so the decision is made under the acquiring
    `BEGIN IMMEDIATE`.
    """

    def interposed_before_acquisition(self, act, label):
        """Run `act` after the start gate and before the token is acquired."""
        from baton_v12.worker_manager import tokens

        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        honest = tokens.acquire
        outcome = []

        def racing(asking, domain, **named):
            if not outcome:
                outcome.append(act(control))
            return honest(asking, domain, **named)

        with mock.patch.object(tokens, "acquire", side_effect=racing):
            try:
                self.commanded(job, operations)
                refused = None
            except AssertionError as failed:
                refused = str(failed)
        return control, engine, outcome, refused

    def test_a_conflict_arriving_before_the_acquisition_refuses_the_start(self):
        """The reached interleaving: the gate has passed and a real removal is
        admitted, and the ACQUISITION is what refuses."""
        from baton_v12.worker_manager import tokens, workspaces

        control, engine, outcome, _refused = self.interposed_before_acquisition(
            lambda control: workspaces._admitted_removal(
                control, self.attempt_of(control), "a removal after the gate"),
            "condition-in-acquisition")
        self.assertEqual(len(outcome), 1, "the interleaving was never reached")
        # NO TASK STARTED, and the engine is the witness.
        self.assertEqual(engine.starts, [])
        # AND NO TOKEN WAS TAKEN over the workspace object.
        attempt = self.attempt_of(control)
        held = os.lstat(os.path.join(self.storage, attempt, "workspace"))
        domain = tokens.domain_of("workspace",
                                  f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])

    def test_the_ordinary_path_still_acquires_and_starts(self):
        """The positive control: with nothing interposed, the condition is satisfied
        and the ordinary start happens exactly once."""
        from baton_v12.worker_manager import tokens

        engine = Engine()
        job, control = self.stores("condition-satisfied")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        self.assertEqual(len(engine.starts), 1)
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual([one["execution"]
                          for one in tokens.outstanding(control, domain)],
                         [attempt_id])

    def test_the_eligibility_predicate_reads_ONLY_the_journal(self):
        """H8 at the acquisition: the predicate runs inside `BEGIN IMMEDIATE`, so a
        filesystem call there would be the DB-2 violation this Work has already been
        corrected for once. Instrumented, with a live-instrument control."""
        engine = Engine()
        job, control = self.stores("predicate-journal-only")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        seen = []
        honest_realpath, honest_lstat = os.path.realpath, os.lstat

        def realpath(*arguments, **named):
            if control._connection.in_transaction:
                seen.append("realpath")
            return honest_realpath(*arguments, **named)

        def lstat(*arguments, **named):
            if control._connection.in_transaction:
                seen.append("lstat")
            return honest_lstat(*arguments, **named)

        with mock.patch.object(os.path, "realpath", side_effect=realpath), \
                mock.patch.object(os, "lstat", side_effect=lstat):
            control._connection.execute("BEGIN IMMEDIATE")
            os.lstat(self.storage)
            control._connection.execute("COMMIT")
            self.assertEqual(seen, ["lstat"], "the instrument cannot fail")
            seen.clear()
            self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(seen, [],
                         "something observed the filesystem while this connection "
                         "held a write lock")

    def attempt_of(self, control):
        """This submission's attempt identity, read from the storage it allocated."""
        return sorted(one for one in os.listdir(self.storage)
                      if one.startswith("attempt-"))[0]


class ALiveTaskTOKENOwnsTheRootsUntilItIsReturned(SingleWorkerCase):
    """W285464 review 2026-09-27T17-48-17Z, the opposite acquisition order.

    The acquisition decides the preparation condition under its own lock, which closes
    the conflict-arrives-first schedule. The reviewer let the real acquisition COMMIT
    and then admitted a real removal for the same attempt: both actors held authority,
    because a first-winner predicate is not a transfer when the loser never asks about
    the winner.

    The loser asks now -- journal-only, from the attempt row's PINNED workspace object,
    so no `lstat` happens under any transaction.
    """

    def with_a_live_task_token(self, label):
        """Drive the ordinary path to a started task, then answer its store."""
        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        self.assertEqual(len(engine.starts), 1)
        return control, attempt_id

    def test_a_removal_is_refused_while_the_task_token_is_outstanding(self):
        """The reviewer's own schedule, as an ordinary after-the-fact assertion."""
        from baton_v12.worker_manager import tokens, workspaces

        control, attempt_id = self.with_a_live_task_token("task-owns-removal")
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual([one["execution"]
                          for one in tokens.outstanding(control, domain)],
                         [attempt_id])
        with self.assertRaises(ContractRefusal) as refused:
            workspaces._admitted_removal(control, attempt_id,
                                         "a removal beside a live task")
        self.assertIn("is held by token generation 1", str(refused.exception))
        self.assertIn("ownership is transferred after that token is returned",
                      str(refused.exception))

    def test_a_cleanup_is_refused_while_the_task_token_is_outstanding(self):
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.with_a_live_task_token("task-owns-cleanup")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_cleanup(
                control, attempt_id,
                {"operation": f"cleanup:{attempt_id}", "signature": "sig-1",
                 "incarnation": "probe"}, "a cleanup beside a live task")
        self.assertIn("is held by token generation 1", str(refused.exception))

    def test_an_adoption_is_refused_while_the_task_token_is_outstanding(self):
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.with_a_live_task_token("task-owns-adoption")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces._admitted_adoption(control, attempt_id,
                                          "an adoption beside a live task")
        self.assertIn("is held by token generation 1", str(refused.exception))

    def test_a_FOREIGN_preparation_is_refused_while_the_task_token_is_outstanding(self):
        """A second preparation of the same attempt by anything that is not its own
        execution: refused, because taking the roots back is an ownership transfer."""
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.with_a_live_task_token("task-owns-preparation")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_preparation(control, attempt_id,
                                         "a foreign preparation", "somebody-else")
        self.assertIn("is held by token generation 1", str(refused.exception))

    def test_the_attempts_OWN_reentry_is_not_refused_by_its_own_token(self):
        """The exemption, and it is why the ordinary path still reconciles.

        MEASURED: without it, every later tick's admission refused against the token
        its own start had taken -- eighteen composed cases failed with my own refusal
        text, which is how I found it.
        """
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.with_a_live_task_token("task-owns-own-reentry")
        owned = workspaces.admit_preparation(control, attempt_id,
                                             "its own re-entry", attempt_id)
        self.assertEqual(owned.attempt, attempt_id)

    def test_the_task_eligibility_also_refuses_a_standing_MAINTENANCE_window(self):
        """The reviewer's source concern: the predicate did not name the maintenance
        window, so an open window before any token could have been read as free."""
        from baton_v12.worker_manager import maintenance, workspaces

        engine = Engine()
        job, control = self.stores("maintenance-before-token")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        honest = workspaces.require_prepared
        opened = []

        def gated(store, attempt, roots, what):
            answer = honest(store, attempt, roots, what)
            if not opened:
                opened.append(maintenance._admitted(
                    store, attempt, "workspace",
                    operation=maintenance.ESTABLISH_RESULT_ROOT,
                    name="baton-maintenance-" + "f" * 32,
                    domain="workspace:probe", pre_allocation="probe/place"))
            return answer

        with mock.patch.object(workspaces, "require_prepared", side_effect=gated):
            try:
                self.commanded(job, operations)
                started = True
            except AssertionError:
                started = False
        self.assertEqual(len(opened), 1, "the window was never opened")
        self.assertFalse(started, "a task started beside an open maintenance window")
        self.assertEqual(engine.starts, [])


class TheREENTRYBesideALiveTaskIsAREVALIDATION(SingleWorkerCase):
    """W285464 review 2026-09-27T18-00-36Z, the last two matrix edges.

    A custody claim and a mutating ALLOCATION admission were both still obtainable
    while the task ran. Both are writers -- `_own_directory` attempts a `mkdir` and
    the group adoption chmods -- so "the same attempt" is not a licence to write again
    after handoff. The ordinary re-entry now takes a read-only revalidation instead,
    and anything missing, replaced or partial refuses rather than being repaired.
    """

    def running(self, label):
        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        projected = self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)
        return control, projected["jobs"][0]["stages"][0]["attempt_id"]

    def test_a_custody_claim_is_refused_beside_a_live_task(self):
        from baton_v12.worker_manager import custody

        control, attempt_id = self.running("live-custody-edge")
        with self.assertRaises(ContractRefusal) as refused:
            custody._claim_episode(
                control, attempt_id, "workspace", "normalize",
                "sha256:" + "c" * 64,
                custody._custody_identity(self.storage, attempt_id, "workspace",
                                          "normalize"))
        self.assertIn("is held by token generation 1", str(refused.exception))
        self.assertEqual(custody.custody_holds(control, attempt_id, "workspace"),
                         [])

    def test_a_mutating_allocation_admission_is_refused_beside_a_live_task(self):
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.running("live-allocation-edge")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces._admitted_allocation(control, attempt_id,
                                            "a new allocation beside a live task")
        self.assertIn("is held by token generation 1", str(refused.exception))
        self.assertEqual(workspaces.standing_allocation(control, attempt_id), [])

    def test_the_ordinary_reentry_REVALIDATES_and_writes_nothing(self):
        """The positive half, with positive instrumentation.

        `assignment_workspace` is called again while the task is live -- which is what
        every later tick does -- and it answers the same roots having performed no
        `mkdir`, `chmod` or `chown` at all.
        """
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.running("live-reentry")
        group = workspaces.configured_workspace_group(control)
        made, moded, owned = [], [], []
        honest_mkdir = os.mkdir

        def mkdir(*arguments, **named):
            made.append(arguments[:1])
            return honest_mkdir(*arguments, **named)

        with mock.patch.object(os, "mkdir", side_effect=mkdir), \
                mock.patch.object(os, "chmod", side_effect=lambda *a: moded.append(a)), \
                mock.patch.object(os, "chown", side_effect=lambda *a: owned.append(a)):
            # THE INSTRUMENTS ARE LIVE.
            honest_mkdir(os.path.join(self.root, "instrument-control"))
            os.mkdir(os.path.join(self.root, "instrument-live"))
            self.assertEqual(len(made), 1)
            made.clear()
            roots = workspaces.assignment_workspace(group, self.storage,
                                                    attempt_id, control=control)
        self.assertEqual(made, [], "the re-entry created something")
        self.assertEqual(moded, [], "the re-entry changed a mode")
        self.assertEqual(owned, [], "the re-entry changed a group")
        self.assertEqual(roots["workspace"],
                         os.path.join(self.storage, attempt_id, "workspace"))
        self.assertEqual(roots["inputs"],
                         os.path.join(self.storage, attempt_id, "inputs"))

    def test_the_revalidation_REFUSES_material_that_is_gone(self):
        """And it does not repair: a removed entry refuses beside a live task."""
        from baton_v12.worker_manager import workspaces

        control, attempt_id = self.running("live-reentry-missing")
        group = workspaces.configured_workspace_group(control)
        # THE HOME IS FROZEN AT 0555 by `compose_input_root`, so an entry cannot be
        # removed from it -- measured, as EPERM on `rmdir`. What a lost entry looks
        # like at this seam is therefore an attempt whose home never held one, which is
        # the same question the revalidation asks.
        self.assertEqual(
            stat.S_IMODE(os.lstat(os.path.join(self.storage,
                                               attempt_id)).st_mode), 0o555)
        elsewhere = "attempt-partially-prepared"
        os.makedirs(os.path.join(self.storage, elsewhere, "workspace"))
        os.makedirs(os.path.join(self.storage, elsewhere, "inputs"))
        with self.assertRaises(ContractRefusal) as refused:
            workspaces._revalidated_roots(self.storage, elsewhere,
                                          "revalidating a partial home")
        self.assertIn("is not the object this manager prepared",
                      str(refused.exception))
        self.assertIn("rather than repaired beside a live task",
                      str(refused.exception))
        # AND IT REPAIRED NOTHING: the missing entries are still missing.
        for name in workspaces.HOME_ENTRIES:
            if name in ("workspace", "inputs"):
                continue
            self.assertFalse(os.path.exists(os.path.join(self.storage, elsewhere,
                                                         name)), name)


class TheConnectedHANDOFFIsProvedEndToEnd(SingleWorkerCase):
    """W285464: the composed H set, on the real ordinary no-context/no-review path.

    Every case here drives `submit -> claim -> prepare -> start` through the actual
    composition with real disposable stores and the fake engine. The H labels are the
    PLAN's; each assertion is a hook that actually fired rather than a description.
    """

    def traced(self, label):
        """One ordinary run, with every preparation hook recorded in order."""
        from baton_v12.worker_manager import tokens, workspaces

        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        order = []
        honest = {name: getattr(workspaces, name)
                  for name in ("admit_preparation", "record_preparation",
                               "require_prepared")}
        acts = {name: getattr(tokens, name)
                for name in ("acquire", "journal_launch", "bind_container",
                             "admit_activation", "settle_activation")}

        def noting(name, function):
            def noted(*arguments, **named):
                order.append(name)
                return function(*arguments, **named)
            return noted

        patches = [mock.patch.object(workspaces, name,
                                     side_effect=noting(name, honest[name]))
                   for name in honest]
        patches += [mock.patch.object(tokens, name,
                                      side_effect=noting(name, acts[name]))
                    for name in acts]
        # THE ENGINE'S OWN ACTS JOIN THE SAME SEQUENCE, so the order compares token
        # and engine steps against each other rather than two separate lists.
        def recorded(argv, *, seconds=None):
            # WRAPPED AT CONSTRUCTION, because the composition captures the callable it
            # is given -- patching the instance afterwards records nothing, which this
            # case and H8 both measured.
            if launching(argv):
                order.append("create" if argv[1] == "create" else argv[1])
            elif activating(argv):
                order.append("start")
            return engine(argv, seconds=seconds)

        operations = self.operations(job, control, recorded)
        self.addCleanup(operations.close)
        for one in patches:
            one.start()
            self.addCleanup(one.stop)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        # THE JOB AND THE OPERATIONS TRAVEL BACK, so a case can RE-ENTER this very
        # composition rather than call one function on the side: review
        # 2026-09-27T18-47-03Z refused my re-entry case for exactly that.
        return control, engine, attempt_id, order, job, operations

    def test_H1_the_whole_ordering_is_claim_prepare_account_revalidate_acquire_start(self):
        from baton_v12.worker_manager import tokens, workspaces

        control, engine, attempt_id, order, _job, _operations = self.traced(
            "H1-ordering")
        # THE CLAIM CAME FIRST: the canonical offer is claimed for this attempt.
        self.assertEqual(len(claimed_offers_for(control, attempt_id)), 1)
        # THEN OWNERSHIP, THE ACCOUNT, THE REVALIDATION AND THE ACQUISITION, in that
        # order -- and the acquisition is LAST of the four.
        first = {}
        for index, name in enumerate(order):
            first.setdefault(name, index)
        self.assertLess(first["admit_preparation"], first["record_preparation"])
        self.assertLess(first["record_preparation"], first["require_prepared"])
        self.assertLess(first["require_prepared"], first["acquire"])
        # THE DURABLE ACCOUNT EXISTS and the window it opened is closed.
        self.assertIsNotNone(workspaces.preparation_completed(control, attempt_id))
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        # THE TOKEN ACTS AND THE ENGINE ACTS, IN ORDER, and counted exactly: review
        # 2026-09-27T18-29-46Z is right that four preparation hooks are not the whole
        # ordering. `bind` and `admit` are the token's, `create` and `start` are the
        # engine's, and the interleaving is the two-act shape the resource token
        # requires -- create, bind, admit, then start.
        self.assertEqual(order[first["acquire"]:],
                         ["acquire", "journal_launch", "create", "bind_container",
                          "admit_activation", "start", "settle_activation"])
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(engine.starts[0][1], "create")
        self.assertEqual(len([one for one in engine.vectors
                              if activating(one)]), 1,
                         "the bound container must be activated exactly once")
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        outstanding = tokens.outstanding(control, domain)
        self.assertEqual([one["execution"] for one in outstanding], [attempt_id])
        current = tokens.token_of(control, domain, outstanding[0]["generation"])
        self.assertEqual(current["container"], engine.runtime_id)
        self.assertTrue(current["activation_settled"] if "activation_settled"
                        in current else not current["activating"])

    def refused_at_the_gate(self, label, mutate, expected):
        """Drive the real run with `_claim`'s own reader MUTATED at the gate.

        Review 2026-09-27T18-47-03Z: my first H2 cases fabricated rows that omitted the
        members `_claim` compares, so they could collide on `offer_id` before the named
        condition was exercised. `mutate` receives the HONEST reader's real rows for
        this attempt and answers what the gate should see, so exactly one thing about an
        otherwise-valid offer differs.

        ONE RUN, and no preliminary store: reading the row from a second run first made
        this fixture answer stores whose task was already started, and the pipeline then
        did nothing at all -- measured, as an empty refusal list.
        """
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        seen, refusals, offered = [], [], []
        honest_reader = single_worker.claimed_offers_for
        honest_admit = workspaces.admit_preparation
        honest_refuse = single_worker._refuse

        def answering(control_store, attempt):
            rows = honest_reader(control_store, attempt)
            offered.append(len(rows))
            return mutate(rows)

        def noting(*arguments, **named):
            seen.append(arguments[1])
            return honest_admit(*arguments, **named)

        def noting_refusal(message, **named):
            refusals.append(message)
            return honest_refuse(message, **named)

        for patcher in (mock.patch.object(single_worker, "claimed_offers_for",
                                          side_effect=answering),
                        mock.patch.object(workspaces, "admit_preparation",
                                          side_effect=noting),
                        mock.patch.object(single_worker, "_refuse",
                                          side_effect=noting_refusal)):
            patcher.start()
            self.addCleanup(patcher.stop)
        for _ in range(3):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except ContractRefusal:
                pass
        self.assertTrue(any(expected in one for one in refusals),
                        f"the gate never refused with {expected!r}: {refusals}")
        # THE GATE WAS REACHED WITH A REAL ROW BEHIND IT.
        self.assertTrue(offered and max(offered) >= 1,
                        "the honest reader never answered this attempt's own offer")
        self.assertEqual(seen, [], "a preparation was admitted without a claim")
        self.assertEqual(engine.starts, [])
        self.assertEqual(sorted(os.listdir(self.storage)),
                         [".baton-manager-instance", ".baton-workspace-authority"])

    def test_H2_no_claimed_offer_reaches_the_gate_and_prepares_nothing(self):
        """A lost race: the gate sees none of this attempt's own offers."""
        self.refused_at_the_gate("H2-no-claim", lambda rows: [],
                                 "has 0 claimed offers")

    def test_H2_two_claimed_offers_reach_the_gate_and_prepare_nothing(self):
        """The REAL row, duplicated: one launch requires exactly one."""
        self.refused_at_the_gate("H2-two-claims",
                                 lambda rows: [dict(rows[0]), dict(rows[0])]
                                 if rows else [],
                                 "has 2 claimed offers")

    def test_H2_another_stages_offer_reaches_the_gate_and_prepares_nothing(self):
        """The REAL row with ONE member mutated: another stage's offer id."""
        self.refused_at_the_gate(
            "H2-other-offer",
            lambda rows: [dict(rows[0], offer_id="offer-somebody-else")]
            if rows else [],
            "the claimed offer's offer_id does not match this stage")

    def test_H2_another_participants_offer_reaches_the_gate_too(self):
        """The REAL row with the participant mutated: somebody else's worker."""
        self.refused_at_the_gate(
            "H2-other-worker",
            lambda rows: [dict(rows[0], participant="baton.somebody-else")]
            if rows else [],
            "the claimed offer's participant does not match this stage")

    def test_H2_a_STALE_assignment_is_excluded_by_the_SELECTION_itself(self):
        """The stale case, corrected to what the product actually does.

        MEASURED, and it is why my earlier case was wrong: `_claim` does not compare
        `runtime_attempt_id` or `expires_at` at all. Staleness is excluded one layer
        earlier -- `claimed_offers_for` SELECTS by attempt, so another attempt's claimed
        offer is never returned to this one, and the gate then refuses on the count. The
        offer's EXPIRY is the Authority's own admission rule rather than this gate's,
        and I no longer claim any test here reaches it.
        """
        engine = Engine()
        job, control = self.stores("H2-stale")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        rows = claimed_offers_for(control, attempt_id)
        self.assertEqual([one["runtime_attempt_id"] for one in rows], [attempt_id])
        self.assertEqual(claimed_offers_for(control, "attempt-somebody-else"), [])

    def test_H1_the_claim_exists_BEFORE_the_preparation_is_admitted(self):
        """Review 2026-09-27T18-47-03Z: H1 counted the claimed offer only after the
        run. This observes it AT the admission, which is where the ordering matters."""
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        job, control = self.stores("H1-claim-first")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        observed = []
        honest = workspaces.admit_preparation

        def noting(*arguments, **named):
            observed.append(len(claimed_offers_for(arguments[0], arguments[1])))
            return honest(*arguments, **named)

        with mock.patch.object(workspaces, "admit_preparation",
                               side_effect=noting):
            self.commanded(job, operations)
        self.assertEqual(observed[:1], [1],
                         "the preparation was admitted before the claim existed")
        self.assertEqual(len(engine.starts), 1)

    def test_H7_a_refusal_DURING_staging_unwinds_and_launches_nothing(self):
        """H7: the refusal-cleanup path, instrumented.

        The task document is published and then the protocol pair refuses, which is the
        one ordering `_input` is written for: a death or refusal between them leaves a
        partial root the next process refuses rather than repairs. This asserts what
        DID happen (the publication, the refusal, the released window) and what did NOT
        (no completion, no token, no launch).
        """
        from baton_v12.worker_manager import tokens, workspaces

        engine = Engine()
        job, control = self.stores("H7-staging-refusal")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        published = []
        honest_compose = workspaces.compose_input_root

        def refusing(*arguments, **named):
            published.append(os.path.isfile(
                os.path.join(arguments[0], "task.json")))
            raise ContractRefusal("policy", "denied",
                                  "the fixture refuses the protocol pair")

        with mock.patch.object(workspaces, "compose_input_root",
                               side_effect=refusing):
            for _ in range(4):
                try:
                    reconcile(job, operations, now=fixtures.NOW)
                except ContractRefusal:
                    pass
        attempt_id = [one for one in sorted(os.listdir(self.storage))
                      if one.startswith("attempt-")][0]
        # WHAT DID HAPPEN: the task document was published before the pair refused.
        self.assertEqual(published[:1], [True])
        # WHAT DID NOT: no completion, no token, no launch.
        self.assertIsNone(workspaces.preparation_completed(control, attempt_id))
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])
        self.assertEqual(engine.starts, [])
        # AND THE WINDOW IS RELEASED, because this writer RETURNED -- the refusal ran
        # its unwinding, which is the one in-process ending that is provable. A partial
        # root is therefore refused by the account being absent, not by a standing
        # window nobody can discharge.
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        roots = {"inputs": os.path.join(self.storage, attempt_id, "inputs"),
                 "workspace": os.path.join(self.storage, attempt_id, "workspace")}
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.require_prepared(control, attempt_id, roots, "starting")
        self.assertIn("recorded no completed host preparation",
                      str(refused.exception))

    HOST_WRITERS = ("mkdir", "makedirs", "chmod", "chown", "lchown", "rename",
                    "replace", "unlink", "remove", "rmdir", "symlink", "link",
                    "truncate", "mkfifo", "utime")

    def host_writes(self):
        """Every host WRITE this fixture's tree sees, by name and pathname.

        Review 2026-09-27T18-47-03Z: instrumenting `mkdir`/`chmod`/`chown` alone is
        not "no host write" -- a publication, a rename or an unlink would all have
        passed. This covers the creating, renaming, removing and permission-changing
        boundaries the composition actually uses, plus `os.open` with any writing
        flag, and it filters to this fixture's own root so the interpreter's own
        reads are not counted. The control and job stores are excluded BY NAME
        because a tick legitimately writes its own journal; every other pathname
        under the root is a host write and is recorded.
        """
        seen = []
        honest = {name: getattr(os, name) for name in self.HOST_WRITERS}
        honest_open = os.open
        writing = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC

        def mine(place):
            return (isinstance(place, str) and place.startswith(self.root)
                    and "sqlite3" not in place)

        def noting(name):
            def noted(*arguments, **named):
                if arguments and mine(arguments[0]):
                    seen.append((name, arguments[0]))
                return honest[name](*arguments, **named)
            return noted

        def opening(place, flags, *arguments, **named):
            if mine(place) and flags & writing:
                seen.append(("open", place))
            return honest_open(place, flags, *arguments, **named)

        for name in self.HOST_WRITERS:
            patcher = mock.patch.object(os, name, side_effect=noting(name))
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(os, "open", side_effect=opening)
        patcher.start()
        self.addCleanup(patcher.stop)
        # THE INSTRUMENT IS PROVED LIVE, positively, on an object in this root --
        # an unused trap cannot pass. Two records, from two different boundaries.
        probe = os.path.join(self.root, "host-writer-instrument")
        os.mkdir(probe)
        handle = os.open(os.path.join(probe, "one"),
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(handle)
        self.assertEqual([name for name, _place in seen], ["mkdir", "open"],
                         "the host-writer instrument cannot fail")
        seen.clear()
        return seen

    def test_H7_a_composed_REENTRY_writes_nothing_and_starts_nothing_NEW(self):
        """H7's re-entry half, through the COMPOSITION itself.

        The job and the operations are RETAINED and reconciled again -- which is what
        a later tick of a live manager is -- with every host writer instrumented.

        MEASURED, AND IT IS WHY THIS ASSERTS A SET RATHER THAN NOTHING AT ALL: a later
        tick does call `makedirs(<launch home>/logs, exist_ok=True)` while adopting the
        log delivery. It creates nothing -- the inode is unchanged across all of it --
        and it is outside every root this attempt's container mounts, so what this
        proves is that NO write reaches the attempt's own material and no second launch
        is composed, with the one ensure named rather than hidden.
        """
        from baton_v12.worker_manager import tokens, workspaces

        control, engine, attempt_id, _order, job, operations = self.traced(
            "H7-composed-reentry")
        account = workspaces.preparation_completed(control, attempt_id)
        self.assertIsNotNone(account)
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        before = tokens.outstanding(control, domain)
        logs = os.path.join(self.config["launch_home"], "logs")
        marked = os.lstat(logs)
        written = self.host_writes()
        reconciled = 0
        for _ in range(3):
            reconcile(job, operations, now=fixtures.NOW)
            status(job, operations, observed_at=fixtures.NOW)
            reconciled += 1
        # THE PATH WAS REACHED: three further ticks ran over a started attempt and it
        # is still the commanded one.
        self.assertEqual(reconciled, 3)
        self.assertEqual(
            status(job, operations,
                   observed_at=fixtures.NOW)["jobs"][0]["stages"][0]["state"],
            "waiting")
        # NO POST-HANDOFF WRITE TOUCHES THIS ATTEMPT'S MATERIAL -- not its input root,
        # not its workspace, not its scratch, not its launch or credential delivery.
        owned = (os.path.join(self.storage, attempt_id),
                 os.path.join(self.config["launch_home"], attempt_id),
                 os.path.join(self.config["credential_home"]),
                 os.path.join(logs, attempt_id), self.source)
        self.assertEqual([one for one in written
                          if any(one[1].startswith(root) for root in owned)], [])
        # AND THE ONLY WRITER CALLED AT ALL IS THE SHARED LOG ROOT'S IDEMPOTENT
        # ENSURE, which found what was already there.
        self.assertEqual({one[1] for one in written}, {logs})
        self.assertEqual({one[0] for one in written}, {"makedirs", "mkdir"})
        after = os.lstat(logs)
        self.assertEqual((marked.st_dev, marked.st_ino, marked.st_mode),
                         (after.st_dev, after.st_ino, after.st_mode))
        # NO SECOND LAUNCH, NO SECOND CREATE, NO SECOND ACTIVATION.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len([one for one in engine.vectors
                              if activating(one)]), 1)
        # AND NO SECOND PREPARATION: the account is the same one, the window stays
        # closed, and the token generation is unchanged.
        self.assertEqual(workspaces.preparation_completed(control, attempt_id),
                         account)
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        self.assertEqual([one["generation"] for one in
                          tokens.outstanding(control, domain)],
                         [one["generation"] for one in before])

    def test_H7_the_ALLOCATION_ALONE_writes_nothing_over_a_prepared_root(self):
        """The allocation boundary on its own, relabelled.

        Review 2026-09-27T18-47-03Z is right that this is NOT the composed re-entry --
        it calls `assignment_workspace` directly, with no claim, no gate and no start.
        What it does prove, and what the case above cannot isolate, is that the
        ALLOCATION itself is read-only over roots that already exist: the adoption
        half of HOST-8, with the whole writer set watched.
        """
        from baton_v12.worker_manager import workspaces

        control, engine, attempt_id, _order, _job, _operations = self.traced(
            "H7-allocation-only")
        written = self.host_writes()
        group = workspaces.configured_workspace_group(control)
        roots = workspaces.assignment_workspace(group, self.storage, attempt_id,
                                                control=control)
        self.assertEqual(written, [], "the allocation wrote over a prepared root")
        # AND IT ANSWERED THE SAME ROOTS the launch was composed over.
        self.assertEqual(roots["inputs"],
                         os.path.join(self.storage, attempt_id, "inputs"))
        self.assertEqual(roots["workspace"],
                         os.path.join(self.storage, attempt_id, "workspace"))
        self.assertEqual(len(engine.starts), 1, "a second launch was composed")

    def test_H7_a_FAILED_publication_removes_the_name_it_created(self):
        """The publication-failure unwind, driven at the write itself.

        The task document is created O_EXCL and then written; a write that cannot
        complete leaves a pathname that exists and holds the wrong bytes, and the
        product removes it -- the name its own exclusive creation established was free.
        This drives the real refusal (`os.write` answering 0 for those bytes, which is
        the product's own "could not be written whole" condition) and asserts the
        removal, not a description of it.
        """
        from baton_v12.worker_manager import tokens, workspaces

        engine = Engine()
        job, control = self.stores("H7-publication-failure")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        honest_write = os.write
        removed, stalled_at = [], []
        honest_unlink = os.unlink

        def stalled(handle, data):
            if data[:16] == self.task_bytes[:16]:
                stalled_at.append(len(data))
                return 0
            return honest_write(handle, data)

        def noting_unlink(place, **named):
            removed.append(place)
            return honest_unlink(place, **named)

        for patcher in (mock.patch.object(os, "write", side_effect=stalled),
                        mock.patch.object(os, "unlink",
                                          side_effect=noting_unlink)):
            patcher.start()
            self.addCleanup(patcher.stop)
        for _ in range(3):
            reconcile(job, operations, now=fixtures.NOW)
        projected = status(job, operations, observed_at=fixtures.NOW)
        stage = projected["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        # THE INTENDED PATH WAS REACHED: the write seam was driven with this
        # deployment's own task bytes, and the deployment RECORDED the refusal --
        # measured, and it corrects what I first asserted: this refusal does not
        # escape `reconcile`, it ends the stage.
        self.assertEqual(stalled_at, [len(self.task_bytes)])
        self.assertEqual(stage["state"], "exceptional")
        failure = attempt_preparation_failure_of(control, attempt_id)
        self.assertIsNotNone(failure)
        self.assertIn("could not be written whole", json.dumps(failure))
        place = os.path.join(self.storage, attempt_id, "inputs",
                             single_worker.TASK_DOCUMENT)
        # THE NAME IT CREATED IS GONE, by the unlink it performed.
        self.assertIn(place, removed)
        self.assertFalse(os.path.lexists(place))
        # AND NOTHING WAS ACCOUNTED FOR, TOKENED OR STARTED.
        self.assertIsNone(workspaces.preparation_completed(control, attempt_id))
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])
        self.assertEqual(engine.starts, [])

    def test_H7_the_prestart_unwind_ends_the_CREDENTIAL_before_the_LAUNCH(self):
        """The pre-start unwind's ORDER, at the gate that refuses latest.

        `require_prepared` is the last thing before a container exists, and by then
        both pre-start deliveries are on the host. The product's rule is credential
        first -- its teardown proves the bytes gone and only then releases the
        registered value -- and the launch root second. This refuses exactly there
        and asserts both the order and the residue.
        """
        from baton_v12.worker_manager import workspaces
        from baton_v12.worker_manager import credentials, launch

        engine = Engine()
        job, control = self.stores("H7-prestart-unwind")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        order = []
        honest_tear_down = credentials.CredentialHome.tear_down
        honest_discard = launch.discard

        def noting_tear_down(home, delivery, *arguments, **named):
            # AUTOSPEC, so the instance arrives and the honest method can be called.
            order.append("credential")
            return honest_tear_down(home, delivery, *arguments, **named)

        def noting_discard(root, *arguments, **named):
            order.append("launch")
            return honest_discard(root, *arguments, **named)

        def refusing(*arguments, **named):
            raise ContractRefusal("refused", "precondition",
                                  "the fixture refuses at the preparation gate")

        for patcher in (mock.patch.object(credentials.CredentialHome,
                                          "tear_down",
                                          side_effect=noting_tear_down,
                                          autospec=True),
                        mock.patch.object(launch, "discard",
                                          side_effect=noting_discard),
                        mock.patch.object(workspaces, "require_prepared",
                                          side_effect=refusing)):
            patcher.start()
            self.addCleanup(patcher.stop)
        for _ in range(3):
            reconcile(job, operations, now=fixtures.NOW)
        projected = status(job, operations, observed_at=fixtures.NOW)
        stage = projected["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        # THE GATE REFUSED, WITH BOTH DELIVERIES ALREADY COMPOSED, so the unwind had
        # something to do -- and it did the two in the product's stated order. The
        # refusal is RECORDED rather than raised, which is this deployment's own
        # ending for a post-claim composition that cannot carry the attempt further.
        self.assertEqual(stage["state"], "exceptional")
        recorded = attempt_preparation_failure_of(control, attempt_id)
        self.assertIsNotNone(recorded)
        self.assertIn("preparation gate", json.dumps(recorded))
        self.assertEqual(order[:2], ["credential", "launch"])
        # AND NEITHER DELIVERY IS LEFT ON THE HOST, with no container created.
        self.assertFalse(os.path.lexists(
            os.path.join(self.config["launch_home"], attempt_id, "launch.json")))
        self.assertFalse(os.path.lexists(
            os.path.join(self.config["credential_home"], "credentials",
                         attempt_id)))
        self.assertEqual(engine.starts, [])

    def test_H8_a_second_connection_progresses_while_a_FILESYSTEM_writer_is_paused(self):
        """H8's other half: the paused writer is a FILESYSTEM one, not the engine.

        Review 2026-09-27T18-29-46Z: the engine boundary alone is not the obligation.
        This pauses the real `compose_input_root` -- the staging writer that publishes
        the protocol pair and freezes the root -- and completes an unrelated attempt's
        preparation on a SECOND connection while it is in flight.

        RESTORED VERBATIM, claim 288344. Review 2026-09-27T19-20-00Z found it gone: my
        H7/H9 rewrite of the preceding claim replaced a span that reached from the
        re-entry case to the engine-boundary H8, and this case sat inside it. An
        accepted slice deleted by a splice is a coverage regression whoever did it, so
        it is back unchanged and the H8 pair is whole again.
        """
        from baton_v12.worker_manager import ControlStore, workspaces

        engine = Engine()
        job, control = self.stores("H8-paused-writer")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        honest = workspaces.compose_input_root
        transacting, progressed = [], []

        def paused(*arguments, **named):
            transacting.append(control._connection.in_transaction)
            second = ControlStore.open(self.control_path,
                                       incarnation="second-during-staging",
                                       clock=lambda: fixtures.NOW)
            try:
                progressed.append(workspaces.admit_preparation(
                    second, "attempt-unrelated-writer",
                    "an unrelated attempt while staging is paused").ordinal)
            finally:
                second.close()
            return honest(*arguments, **named)

        with mock.patch.object(workspaces, "compose_input_root",
                               side_effect=paused):
            self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(transacting, [False],
                         "the staging writer ran while a write lock was held")
        self.assertEqual(progressed, [1],
                         "a second connection could not progress while the "
                         "filesystem writer was in flight")

    def test_H9_the_task_vectors_mount_exactly_what_this_deployment_allows(self):
        """H9: the ACTUAL created vector, compared as a VECTOR.

        Review 2026-09-27T18-47-03Z: keying the mounts by destination DISCARDS a
        duplicate, so the previous form could not have failed on one. This compares
        the whole list of (source, destination, mode) tuples -- count first, then
        the exact set, then uniqueness -- against this attempt's known delivery
        pathnames, so a duplicate, an extra and a retargeted source all fail.
        """
        control, engine, attempt_id, _order, _job, _operations = self.traced(
            "H9-vectors")
        created = engine.starts[0]
        home = os.path.join(self.storage, attempt_id)
        delivery = os.path.join(self.config["launch_home"], attempt_id)
        # THE DOUBLED SEGMENT IS THE CREDENTIAL HOME'S OWN LAYOUT, measured off the
        # created vector rather than assumed: the volatile root is
        # `<credential home>/credentials/<attempt>` and the slot is one file in it.
        credential = os.path.join(self.config["credential_home"], "credentials",
                                  attempt_id, "api")
        expected = [
            (os.path.join(home, "inputs"), "/input", "ro"),
            (os.path.join(home, "workspace"), "/output", "rw"),
            (os.path.join(home, "scratch"), "/scratch", "rw"),
            # THE SOURCE NOMINATION IS THE NOMINATED TREE ITSELF, mounted read-only
            # at the mountpoint inside the input root rather than copied into it.
            (self.source, "/input/source", "ro"),
            (credential, "/run/baton/credentials/api", "ro"),
            (os.path.join(delivery, "launch.json"), "/run/baton/launch.json", "ro"),
            (os.path.join(delivery, "command"), "/run/baton/exchange/command", "ro"),
            (os.path.join(delivery, "events"), "/run/baton/exchange/events", "rw"),
            (os.path.join(self.config["launch_home"], "logs", attempt_id),
             "/run/baton/attempt-logs", "rw"),
        ]
        vector = [(one["Source"], one["Destination"],
                   "rw" if one["RW"] else "ro") for one in engine.mounts]
        # THE COUNT, FIRST: an extra mount fails here before any comparison.
        self.assertEqual(len(vector), len(expected), vector)
        self.assertEqual(sorted(vector), sorted(expected))
        # NO DUPLICATE, IN EITHER SENSE -- the same tuple twice, or two mounts over
        # one destination.
        self.assertEqual(len(set(vector)), len(vector))
        self.assertEqual(len({one[1] for one in vector}), len(vector))
        # THE CREDENTIAL DELIVERY IS ONE FILE that really exists, read-only, under
        # the credential prefix -- not the attempt's credential directory.
        self.assertTrue(os.path.isfile(credential), credential)
        # NO SIBLING, NO ATTEMPT CREDENTIAL HOME AND NO CONTROL DATABASE.
        for one in engine.mounts:
            self.assertNotEqual(one["Source"], self.storage)
            self.assertNotEqual(one["Source"], os.path.join(home, "credentials"))
            self.assertNotEqual(one["Source"],
                                os.path.join(home, "credential-state"))
            self.assertNotIn("control.sqlite3", one["Source"])
        self.assertNotIn(self.control_path, " ".join(created))

    def test_H8_a_second_connection_makes_progress_during_the_engine_call(self):
        """H8: the external boundary runs with no transaction held, and an unrelated
        act on another connection completes while it is in flight.

        THE ENGINE IS WRAPPED AT CONSTRUCTION, because the composition captures the
        callable it is given: patching the instance afterwards changed nothing, which
        is how I found it.
        """
        from baton_v12.worker_manager import ControlStore, workspaces

        engine = Engine()
        job, control = self.stores("H8-second-connection")
        submit(job, self.submission)
        progressed = []
        transacting = []

        def watched(argv, *, seconds=None):
            if launching(argv) and not transacting:
                transacting.append(control._connection.in_transaction)
                second = ControlStore.open(self.control_path,
                                           incarnation="second-connection",
                                           clock=lambda: fixtures.NOW)
                try:
                    progressed.append(workspaces.admit_preparation(
                        second, "attempt-unrelated",
                        "an unrelated attempt's preparation").ordinal)
                finally:
                    second.close()
            return engine(argv, seconds=seconds)

        operations = self.operations(job, control, watched)
        self.addCleanup(operations.close)
        self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(transacting, [False],
                         "the engine was called while a write lock was held")
        self.assertEqual(progressed, [1],
                         "a second connection could not make unrelated progress "
                         "while the external call was in flight")


class AnABRUPTDeathLeavesTheWindowStandingAndLaunchesNothing(SingleWorkerCase):
    """H6: a manager that dies mid-write runs no `finally`.

    Everything in-process unwinds, so a genuine abrupt death cannot be simulated by
    raising: the release would run. This forks a child that performs the real
    preparation and calls `os._exit` inside it -- no unwinding, no atexit, no
    `finally` -- and the parent then reopens the journal and asks what is true.

    DETERMINISTIC AND OFFLINE: the child uses the same fake engine and the same
    disposable stores, and there is no second Host manager and no live engine. The
    child's exit code is checked, so a child that failed for another reason cannot be
    read as the death this case is about.
    """

    def killed_during(self, point):
        """Fork, prepare until `point`, and leave the process without unwinding."""
        job, control = self.stores("abrupt-parent")
        submit(job, self.submission)
        job.close()
        control.close()
        read, write = os.pipe()
        child = os.fork()
        if child == 0:                                   # pragma: no cover
            code = 3
            try:
                os.close(read)
                from baton_v12.worker_manager import workspaces as inner
                job, control = self.stores("abrupt-child")
                engine = Engine()

                def checkpoint(name):
                    if name == point:
                        standing = inner.standing_preparation(
                            control, sorted(os.listdir(self.storage))[-1]
                            if os.listdir(self.storage) else "none")
                        os.write(write, b"reached")
                        # NO UNWINDING AT ALL: not an exception, not `sys.exit`.
                        os._exit(9)

                operations = single_worker.operations_from(
                    self.config, job, control, engine_run=engine,
                    credential_provider=lambda *_: self.secret,
                    clock=lambda: fixtures.NOW, checkpoint=checkpoint)
                for _ in range(6):
                    reconcile(job, operations, now=fixtures.NOW)
            except BaseException:
                code = 4
            os._exit(code)
        os.close(write)
        signalled = os.read(read, 16)
        os.close(read)
        _pid, status = os.waitpid(child, 0)
        self.assertEqual(signalled, b"reached",
                         "the child never reached the preparation")
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 9,
                         "the child did not die the way this case is about")
        return self.stores("abrupt-after")

    def test_the_window_stands_and_no_task_is_launched_or_reused(self):
        from baton_v12.worker_manager import tokens, workspaces

        job, control = self.killed_during("workspace")
        attempt = [one for one in sorted(os.listdir(self.storage))
                   if one.startswith("attempt-")]
        self.assertEqual(len(attempt), 1,
                         "the child did not reach its own allocation")
        attempt_id = attempt[0]
        # THE WINDOW IS STANDING: no completion and no release, because nothing ran.
        self.assertEqual([one for one, _ in workspaces.standing_preparation(
            control, attempt_id)], [1])
        self.assertIsNone(workspaces.preparation_completed(control, attempt_id))
        # NOTHING WAS LAUNCHED: no token was ever acquired over the workspace object.
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])
        # AND NOTHING MAY REUSE THESE ROOTS: every ownership-transferring admission and
        # the start gate refuse, naming the window nobody closed.
        roots = {"inputs": os.path.join(self.storage, attempt_id, "inputs"),
                 "workspace": os.path.join(self.storage, attempt_id, "workspace")}
        for act in (lambda: workspaces.require_prepared(control, attempt_id, roots,
                                                       "starting this attempt"),
                    lambda: workspaces._admitted_removal(control, attempt_id,
                                                         "a later removal"),
                    lambda: workspaces._admitted_adoption(control, attempt_id,
                                                          "a later adoption"),
                    lambda: workspaces.admit_preparation(control, attempt_id,
                                                         "a later preparation",
                                                         attempt_id)):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal) as refused:
                    act()
                self.assertIn("host preparation 1", str(refused.exception))

    def test_a_fresh_manager_does_not_launch_over_the_standing_window(self):
        """The reuse half, driven through the real composition rather than by hand."""
        from baton_v12.worker_manager import workspaces

        job, control = self.killed_during("workspace")
        engine = Engine()
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        for _ in range(6):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except ContractRefusal:
                pass
        self.assertEqual(engine.starts, [],
                         "a fresh manager launched over an unreconciled window")
        attempt_id = [one for one in sorted(os.listdir(self.storage))
                      if one.startswith("attempt-")][0]
        self.assertEqual([one for one, _ in workspaces.standing_preparation(
            control, attempt_id)], [1])


class EveryHOSTPREPARATIONPHASEIsRecoveredOrHeld(SingleWorkerCase):
    """W285465 HP1/HP2/HP3/HP5: an abrupt death in EACH host preparation phase.

    The accepted predecessor proved one cut -- a death at the allocation -- and the
    W285465 handoff is explicit that this does not prove every phase. So this forks a
    child per phase, kills it with `os._exit` inside the real composition, and asks the
    reopened journal what is true. The phases are the composition's own checkpoints:

        workspace   the private allocation exists; nothing is staged yet
        boundary    the source mountpoint exists inside the input root
        input       the task document and the protocol pair are published and the
                    root is FROZEN -- the filesystem work is COMPLETE
        manifest    the retained manifest is committed and the completion is NOT
                    (HP2's distinct row: the last moment before `record_preparation`)
        prepared    the durable completion IS committed (HP3's positive resume)

    HP5 IS A PROPERTY OF THE HARNESS, not a separate cut: the child's process-local
    `_preparations` map dies with it, and every question below is asked through handles
    opened afterwards over the same persisted state. An empty map is never read as "no
    writer" -- what answers is the journal.

    WHAT THESE CUTS ARE NOT, corrected by review 2026-09-27T23-45-11Z and stated here
    rather than left to be inferred from a test name: every cut lands on a PHASE
    BOUNDARY -- the instant after a phase's writes returned -- so they prove that a
    COMPLETED phase authorizes nothing further. They are NOT interior partial writes: a
    half-created directory tree, a mid-publication document or a partly applied
    permission set is a different cut, and the interior ones remain unproved here. The
    one interior effect this suite does reach is the publication's own failure path,
    `TheConnectedHANDOFFIsProvedEndToEnd.test_H7_a_FAILED_publication_removes_the_name_
    it_created`, which stalls the write itself.

    DETERMINISTIC AND OFFLINE, as the predecessor was: the same fake engine, the same
    disposable stores, one Host manager, no live engine or provider, and the child's
    exact exit status is checked so a child that failed some other way cannot be read
    as the death this case is about.
    """

    SIBLING = "attempt-" + "5" * 64

    def sibling(self):
        """An unrelated attempt's material, and its exact identity beforehand.

        HP1 requires that sibling bytes and identities are unchanged by an
        interruption and by the recovery that follows, so there has to BE a sibling:
        a real home beside the one the child prepares, with content of its own.
        """
        home = os.path.join(self.storage, self.SIBLING)
        os.makedirs(os.path.join(home, "inputs"))
        os.makedirs(os.path.join(home, "workspace"))
        with open(os.path.join(home, "inputs", "task.json"), "wb") as writing:
            writing.write(b'{"schema":"the sibling own task"}')
        with open(os.path.join(home, "workspace", "answer.txt"), "wb") as writing:
            writing.write(b"the sibling own answer\n")
        return self.identity_of(home)

    @staticmethod
    def identity_of(root):
        """Every entry under `root` by relative name: mode, object and content."""
        found = {}
        for walked, directories, files in os.walk(root):
            directories.sort()
            for name in sorted(directories) + sorted(files):
                place = os.path.join(walked, name)
                held = os.lstat(place)
                content = None
                if stat.S_ISREG(held.st_mode):
                    with open(place, "rb") as reading:
                        content = hashlib.sha256(reading.read()).hexdigest()
                found[os.path.relpath(place, root)] = (
                    stat.S_IMODE(held.st_mode), held.st_dev, held.st_ino, content)
        return found

    def killed_at(self, point):
        """Fork, prepare up to `point`, and leave without unwinding anything."""
        job, control = self.stores("hp-parent")
        submit(job, self.submission)
        job.close()
        control.close()
        read, write = os.pipe()
        child = os.fork()
        if child == 0:                                   # pragma: no cover
            code = 3
            try:
                os.close(read)
                job, control = self.stores("hp-child")
                engine = Engine()

                def checkpoint(name):
                    if name == point:
                        os.write(write, b"reached")
                        # NO UNWINDING AT ALL: not an exception, not `sys.exit`, so
                        # no `finally` releases the window and no cleanup repairs
                        # anything. This is the fact a RuntimeError cannot model.
                        os._exit(9)

                operations = single_worker.operations_from(
                    self.config, job, control, engine_run=engine,
                    credential_provider=lambda *_: self.secret,
                    clock=lambda: fixtures.NOW, checkpoint=checkpoint)
                for _ in range(6):
                    reconcile(job, operations, now=fixtures.NOW)
            except BaseException:
                code = 4
            os._exit(code)
        os.close(write)
        signalled = os.read(read, 16)
        os.close(read)
        _pid, status = os.waitpid(child, 0)
        self.assertEqual(signalled, b"reached",
                         f"the child never reached {point!r}")
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 9,
                         "the child did not die the way this case is about")
        # FRESH HANDLES OVER THE SAME PERSISTED STATE, which is HP5: nothing of the
        # dead writer's process-local tracking survives to be consulted.
        job, control = self.stores("hp-after")
        attempts = [one for one in sorted(os.listdir(self.storage))
                    if one.startswith("attempt-") and one != self.SIBLING]
        self.assertEqual(len(attempts), 1,
                         f"the child did not allocate exactly one home: {attempts}")
        return job, control, attempts[0]

    def held_after(self, point, sibling):
        """The whole HELD outcome for a cut before the completion is written."""
        from baton_v12.worker_manager import tokens, workspaces

        job, control, attempt_id = self.killed_at(point)
        # THE WINDOW IS STANDING, at this attempt and this exact ordinal: the journal
        # says a writer was admitted and neither completed nor released.
        self.assertEqual(workspaces.standing_preparation(control, attempt_id)[0][0],
                         1)
        self.assertEqual(len(workspaces.standing_preparation(control, attempt_id)), 1)
        # AND THERE IS NO COMPLETION, so the files on disk -- however complete they
        # are -- are not an account that anything may consume.
        self.assertIsNone(workspaces.preparation_completed(control, attempt_id))
        # NO TASK TOKEN WAS EVER ACQUIRED over the workspace object.
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])
        # THE HOLD IS ACTIONABLE AND NAMES THE RESOURCE: every act that would take
        # these roots over refuses, naming the window nobody closed.
        roots = {"inputs": os.path.join(self.storage, attempt_id, "inputs"),
                 "workspace": os.path.join(self.storage, attempt_id, "workspace")}
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.require_prepared(control, attempt_id, roots,
                                        "starting this attempt")
        self.assertIn("host preparation 1", str(refused.exception))
        for act, what in (
                (lambda: workspaces._admitted_removal(
                    control, attempt_id, "a later removal"), "removal"),
                (lambda: workspaces._admitted_adoption(
                    control, attempt_id, "a later adoption"), "adoption"),
                (lambda: workspaces.admit_preparation(
                    control, attempt_id, "a later preparation", attempt_id),
                 "preparation")):
            with self.assertRaises(ContractRefusal) as refused:
                act()
            self.assertIn("host preparation 1", str(refused.exception),
                          f"the {what} did not name the standing window")
        # AND A WHOLE FRESH COMPOSITION LAUNCHES NOTHING over it -- the recovery a
        # restarted manager actually performs, not a hand-made call.
        engine = Engine()
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        for _ in range(6):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except ContractRefusal:
                pass
        self.assertEqual(engine.starts, [],
                         "a restarted manager launched over a standing window")
        self.assertEqual(engine.vectors, [],
                         "a restarted manager reached the engine at all")
        self.assertIsNone(workspaces.preparation_completed(control, attempt_id))
        self.assertEqual(len(workspaces.standing_preparation(control, attempt_id)), 1)
        # THE SIBLING IS UNTOUCHED, by the interruption and by the recovery.
        self.assertEqual(
            self.identity_of(os.path.join(self.storage, self.SIBLING)), sibling,
            "the interrupted attempt or its recovery changed a sibling")
        return control, attempt_id

    def test_HP1_a_death_AFTER_the_ALLOCATION_holds_and_launches_nothing(self):
        # THE CUT IS THE BOUNDARY AFTER `assignment_workspace` RETURNED, not a
        # half-made tree: what this proves is that a finished allocation with nothing
        # staged into it authorizes nothing.
        sibling = self.sibling()
        _control, attempt_id = self.held_after("workspace", sibling)
        # THE PHASE IS PROVED REACHED BY WHAT IS THERE: the private home exists and
        # nothing has been staged into the input root yet.
        home = os.path.join(self.storage, attempt_id)
        self.assertTrue(os.path.isdir(os.path.join(home, "workspace")))
        self.assertEqual(os.listdir(os.path.join(home, "inputs")), [])

    def test_HP1_a_death_after_the_SOURCE_MOUNTPOINT_holds_and_launches_nothing(self):
        sibling = self.sibling()
        _control, attempt_id = self.held_after("boundary", sibling)
        # THE MOUNTPOINT IS THERE AND EMPTY, and the task is NOT published yet: this
        # is the staging phase, distinguishable from the two around it.
        inputs = os.path.join(self.storage, attempt_id, "inputs")
        mountpoint = os.path.join(inputs, single_worker.SOURCE_DESTINATION)
        self.assertTrue(os.path.isdir(mountpoint))
        self.assertEqual(os.listdir(mountpoint), [])
        self.assertFalse(os.path.lexists(
            os.path.join(inputs, single_worker.TASK_DOCUMENT)))

    def test_HP1_a_death_after_PUBLICATION_and_PERMISSIONS_holds_and_launches(self):
        """The publication and permission phase: the filesystem work is COMPLETE."""
        sibling = self.sibling()
        _control, attempt_id = self.held_after("input", sibling)
        inputs = os.path.join(self.storage, attempt_id, "inputs")
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        # THE DOCUMENT IS PUBLISHED, WITH THIS DEPLOYMENT'S OWN BYTES, and the
        # PERMISSIONS are the ones the delivery promises -- the read-only document
        # inside a frozen root. That is the phase, proved by its own effects.
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(), self.task_bytes)
        self.assertEqual(stat.S_IMODE(os.lstat(place).st_mode), 0o444)
        self.assertEqual(stat.S_IMODE(os.lstat(inputs).st_mode), 0o555)
        # AND THIS CUT IS EARLIER THAN HP2's: the manifest has NOT been retained
        # yet, which is what distinguishes the two adjacent phases by their effects
        # rather than by the checkpoint name I asked for.
        self.assertEqual(_control._connection.execute(
            "SELECT count(*) FROM manifests").fetchone()[0], 0)

    def test_HP2_a_COMPLETE_FILESYSTEM_without_the_record_proves_nothing(self):
        """HP2, and it is the row the whole design rests on.

        The cut is after `retain_manifest` and before `record_preparation`: every host
        write has happened and the durable completion has not. The files are therefore
        as complete as they will ever be, and they still authorize nothing -- no task
        admission, no launch, no reuse. `held_after` asks all of that; what this adds
        is the positive proof that the filesystem really is finished at this cut, so
        the refusal cannot be explained by something missing on disk.
        """
        from baton_v12.worker_manager import workspaces

        sibling = self.sibling()
        control, attempt_id = self.held_after("manifest", sibling)
        inputs = os.path.join(self.storage, attempt_id, "inputs")
        home = os.path.join(self.storage, attempt_id)
        with open(os.path.join(inputs, single_worker.TASK_DOCUMENT), "rb") as reading:
            self.assertEqual(reading.read(), self.task_bytes)
        for name in ("workspace", "scratch", "credentials"):
            self.assertTrue(os.path.isdir(os.path.join(home, name)), name)
        self.assertTrue(os.path.isdir(
            os.path.join(inputs, single_worker.SOURCE_DESTINATION)))
        self.assertEqual(stat.S_IMODE(os.lstat(inputs).st_mode), 0o555)
        # THE MANIFEST WAS RETAINED -- the DB write immediately before the completion
        # -- so this cut is the LAST moment before the account rather than an earlier
        # phase. Read off the store's own table, because that is the effect.
        # MEASURED: the table keys the row by the DOCUMENT'S schema, not by the
        # definition name the caller passes, and the row survived the abrupt exit --
        # so the retention really did commit before the death.
        self.assertEqual(
            [one[0] for one in control._connection.execute(
                "SELECT schema FROM manifests").fetchall()],
            [self.manifest["schema"]])
        # AND THE ACCOUNT IS ABSENT. Files plus a retained manifest are not a
        # completion, and nothing here infers one from them.
        self.assertIsNone(workspaces.preparation_completed(control, attempt_id))

    def test_HP3_a_death_AFTER_the_record_resumes_to_EXACTLY_ONE_task(self):
        """HP3, and the connected POSITIVE path: zero launches is not success.

        The completion is committed and the writer is gone. A restarted manager with
        fresh handles and an empty process-local map must revalidate the durable
        identities and reach EXACTLY ONE task -- one create, one start -- without
        redoing host work and without a second preparation account.
        """
        from baton_v12.worker_manager import tokens, workspaces

        sibling = self.sibling()
        job, control, attempt_id = self.killed_at("prepared")
        # THE ACCOUNT IS DURABLE AND THE WINDOW IS CLOSED BY IT.
        account = workspaces.preparation_completed(control, attempt_id)
        self.assertIsNotNone(account)
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        # AND NO TASK EXISTS YET: the completion is not admission.
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])
        engine = Engine()
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        # THE RECOVERY'S OWN HOST WRITES ARE COUNTED SEPARATELY from its durable
        # acts: an exclusive creation of the task document would mean the resume
        # republished what the dead writer had already published.
        published, admitted, accounted = [], [], []
        honest_open = os.open
        honest_admit = workspaces.admit_preparation
        honest_record = workspaces.record_preparation

        def opening(place, flags, *arguments, **named):
            if isinstance(place, str) \
                    and place.endswith(single_worker.TASK_DOCUMENT) \
                    and flags & os.O_EXCL:
                published.append(place)
            return honest_open(place, flags, *arguments, **named)

        def noting_admit(*arguments, **named):
            admitted.append(arguments[1])
            return honest_admit(*arguments, **named)

        def noting_record(*arguments, **named):
            accounted.append(arguments[1])
            return honest_record(*arguments, **named)

        for patcher in (mock.patch.object(os, "open", side_effect=opening),
                        mock.patch.object(workspaces, "admit_preparation",
                                          side_effect=noting_admit),
                        mock.patch.object(workspaces, "record_preparation",
                                          side_effect=noting_record)):
            patcher.start()
            self.addCleanup(patcher.stop)
        projected = self.commanded(job, operations)
        # EXACTLY ONE TASK: one inert create, one activation, and the same attempt.
        self.assertEqual(projected["jobs"][0]["stages"][0]["attempt_id"], attempt_id)
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(engine.starts[0][1], "create")
        self.assertEqual(len([one for one in engine.vectors
                              if activating(one)]), 1)
        # NO REPUBLICATION, and the account is the SAME one -- `record_preparation`
        # was reached again on the ordinary path and replayed at the same identity
        # rather than writing a second preparation.
        self.assertEqual(published, [],
                         "the resume republished the task document")
        self.assertEqual(accounted, [attempt_id])
        self.assertEqual(workspaces.preparation_completed(control, attempt_id),
                         account)
        # THE WINDOW THE RESUME OPENED IS CLOSED AGAIN, and the token is held by
        # this attempt's own execution.
        self.assertEqual(admitted, [attempt_id])
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        outstanding = tokens.outstanding(control, domain)
        self.assertEqual([one["execution"] for one in outstanding], [attempt_id])
        self.assertEqual(
            tokens.token_of(control, domain,
                            outstanding[0]["generation"])["container"],
            engine.runtime_id)
        # AND THE SIBLING IS STILL UNTOUCHED by a recovery that DID launch.
        self.assertEqual(
            self.identity_of(os.path.join(self.storage, self.SIBLING)), sibling)


    def test_HP6_a_REPLACED_root_after_the_record_refuses_and_repins_nothing(self):
        """HP6/HP7's mismatch half, through the RECOVERY rather than in-process.

        The accepted predecessor proved a replaced root refuses before any task is
        created; what this adds is the same substitution across an abrupt death, so the
        manager deciding it has nothing in memory. The completion names the objects it
        completed over by `device:inode`; a directory of the right shape at the right
        path is a different object, and the recovery must refuse it, launch nothing,
        and leave the account exactly as it found it -- no silent repinning.
        """
        from baton_v12.worker_manager import tokens, workspaces

        sibling = self.sibling()
        job, control, attempt_id = self.killed_at("prepared")
        account = workspaces.preparation_completed(control, attempt_id)
        self.assertIsNotNone(account)
        home = os.path.join(self.storage, attempt_id)
        workspace = os.path.join(home, "workspace")
        before = os.lstat(workspace)
        # THE HOME IS FROZEN AT 0555 by `compose_input_root`, so the substitution has
        # to be made by the fixture acting as the host -- measured, because a rename
        # inside the frozen home is EPERM.
        os.chmod(home, 0o755)
        os.rename(workspace, os.path.join(home, "workspace-moved-aside"))
        os.mkdir(workspace, 0o770)
        os.chmod(home, 0o555)
        after = os.lstat(workspace)
        self.assertNotEqual((before.st_dev, before.st_ino),
                            (after.st_dev, after.st_ino),
                            "the substitution did not change the object")
        engine = Engine()
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        for _ in range(6):
            reconcile(job, operations, now=fixtures.NOW)
        # ZERO TASKS, and the refusal is the recorded ending of this deployment.
        self.assertEqual(engine.starts, [])
        stage = status(job, operations,
                       observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "exceptional")
        recorded = attempt_preparation_failure_of(control, attempt_id)
        self.assertIsNotNone(recorded)
        # WHICH GATE CAUGHT IT, MEASURED RATHER THAN ASSUMED: on the recovery path the
        # WRITE-ONCE BOUNDARY PIN fires first -- it re-observes the roots before the
        # completion record is consulted -- and its refusal says the workspace became
        # another object and will not be re-pinned. The completion record's own
        # revalidation is the accepted predecessor's
        # `test_a_replaced_prepared_root_refuses_before_any_task_is_created`; this row
        # does not claim to reach it, and asserting the pin is what actually happens.
        self.assertEqual(recorded["failure"]["code"], "operation-collision")
        self.assertIn("a root that became another object is refused rather than "
                      "re-pinned", recorded["failure"]["message"])
        # NOTHING WAS REPINNED: the completion is the same account, over the same
        # named objects, and no token was taken over the substitute.
        self.assertEqual(workspaces.preparation_completed(control, attempt_id),
                         account)
        domain = tokens.domain_of("workspace", f"{after.st_dev}:{after.st_ino}")
        self.assertEqual(tokens.outstanding(control, domain), [])
        # AND NO WINDOW IS LEFT STANDING: the refused writer RETURNED, so it released
        # what it opened -- a refusal is not an abandoned window.
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        self.assertEqual(
            self.identity_of(os.path.join(self.storage, self.SIBLING)), sibling)

    def test_HP4_a_writer_that_can_still_FINISH_blocks_the_launch_then_finishes(self):
        """HP4: while a host writer may still complete, nothing may launch or reuse.

        WHAT THIS ACTUALLY MODELS, stated rather than implied: ONE Host manager, with
        the real writer interposed INSIDE `compose_input_root` -- review
        2026-09-27T23-45-11Z is right that a checkpoint taken after the writes returned
        is a weaker seam, so the delay is now taken while that writer is IN FLIGHT and
        has not yet returned. At that instant it genuinely can still finish. Every
        question is asked on an INDEPENDENT coordination connection, so each answer is
        the journal's to somebody who is not the writer. There is no second manager and
        no uncontrolled process: the handoff forbids both.

        THREE THINGS ARE ASKED THERE, and the third is the one the review required:

          * the start gate refuses, naming the standing window;
          * a SECOND preparation admission for this same attempt refuses -- an ordinal
            anybody can read is not authority to write;
          * a replay carrying the WRONG ATTEMPT is refused for its OWN reason, and the
            distinct refusal is the proof that no cross-attempt effect occurred: stale
            evidence about another name neither resolves this window nor completes
            anything. Review 2026-09-27T23-45-11Z is right that my previous lookup of
            `preparation_completed` for an unused name proved nothing at all.

        THEN THE WRITER FINISHES, and the same composition reaches exactly one task. A
        hold that never clears would satisfy the first half and be useless.
        """
        from baton_v12.worker_manager import ControlStore, tokens, workspaces

        engine = Engine()
        job, control = self.stores("HP4-delayed-writer")
        submit(job, self.submission)
        asked = []
        other = "attempt-" + "9" * 64
        honest_compose = workspaces.compose_input_root

        def paused(*arguments, **named):
            if asked:
                return honest_compose(*arguments, **named)
            attempt_id = [one for one in sorted(os.listdir(self.storage))
                          if one.startswith("attempt-")][0]
            roots = {"inputs": os.path.join(self.storage, attempt_id, "inputs"),
                     "workspace": os.path.join(self.storage, attempt_id,
                                               "workspace")}
            second = ControlStore.open(self.control_path,
                                       incarnation="hp4-independent-reader",
                                       clock=lambda: fixtures.NOW)
            try:
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.require_prepared(
                        second, attempt_id, roots,
                        "starting while a writer can still finish")
                gate = str(refused.exception)
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.admit_preparation(
                        second, attempt_id,
                        "a second preparation while the first can still finish",
                        attempt_id)
                again = str(refused.exception)
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.require_prepared(
                        second, other, roots,
                        "starting a DIFFERENT attempt over these roots")
                stale = str(refused.exception)
                asked.append((attempt_id, gate, again, stale))
                self.assertIsNone(
                    workspaces.preparation_completed(second, attempt_id))
                self.assertEqual(
                    [one for one, _ in workspaces.standing_preparation(
                        second, attempt_id)], [1])
                self.assertEqual(
                    workspaces.standing_preparation(second, other), [])
            finally:
                second.close()
            return honest_compose(*arguments, **named)

        patcher = mock.patch.object(workspaces, "compose_input_root",
                                    side_effect=paused)
        patcher.start()
        self.addCleanup(patcher.stop)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        projected = self.commanded(job, operations)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        # THE SEAM WAS REACHED ONCE, at this attempt, with the writer in flight.
        self.assertEqual([one[0] for one in asked], [attempt_id])
        _at, gate, again, stale = asked[0]
        self.assertIn("host preparation 1", gate)
        self.assertIn("host preparation 1", again)
        # THE WRONG-ATTEMPT REPLAY IS REFUSED FOR ITS OWN REASON: the distinct text is
        # what proves this window did not answer for another name.
        self.assertNotIn("host preparation 1", stale)
        self.assertIn(other[:24], stale)
        # AND THE HOLD CLEARED BY THE WRITER FINISHING -- not by a deadline, not by a
        # deletion, and not by anything the fixture told the journal.
        self.assertIsNotNone(workspaces.preparation_completed(control, attempt_id))
        self.assertEqual(workspaces.standing_preparation(control, attempt_id), [])
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len([one for one in engine.vectors
                              if activating(one)]), 1)
        held = os.lstat(os.path.join(self.storage, attempt_id, "workspace"))
        domain = tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")
        self.assertEqual([one["execution"] for one in
                          tokens.outstanding(control, domain)], [attempt_id])
        # AND THE OTHER NAME GAINED NOTHING FROM ANY OF IT, counted separately from
        # this attempt's own effects.
        self.assertIsNone(workspaces.preparation_completed(control, other))
        self.assertEqual(workspaces.standing_preparation(control, other), [])
        self.assertEqual(
            tokens.outstanding(control, tokens.domain_of("workspace", "0:0")), [])


class TheProductionCompositionIsRestartSafe(SingleWorkerCase):
    def crash_and_restart(self, point):
        engine = Engine()
        job, control = self.stores("before-" + point)
        submit(job, self.submission)
        crashed = []

        def checkpoint(name):
            if name == point and not crashed:
                crashed.append(name)
                raise RuntimeError("fixture process stopped")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=checkpoint)
        with self.assertRaisesRegex(RuntimeError, "process stopped"):
            for _ in range(6):
                reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual(crashed, [point])
        operations.close()
        job.close()
        control.close()

        resumed_job, resumed_control = self.stores("after-" + point)
        resumed = self.operations(resumed_job, resumed_control, engine)
        projected = self.commanded(resumed_job, resumed)
        stage = projected["jobs"][0]["stages"][0]
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(claimed_offers_for(resumed_control,
                                                stage["attempt_id"])), 1)
        resumed.close()

    def test_the_production_start_is_governed_by_a_resource_token(self):
        """W275774: THE COMPOSED VERIFICATION that governance is actually ON here.

        "162 tests pass" proves nothing by itself about whether the governed path
        was taken, so this asks the engine and the journal directly:

          * the launch composed `create` and then `start`, which is the two-act
            shape a resource token requires -- a container bound before it runs;
          * the workspace object this attempt mounts carries a token generation
            whose launch is the journalled start operation and whose container is
            the runtime the engine named;
          * and the activation was settled, so the resource is held by a live
            generation rather than by an unresolved one.
        """
        from baton_v12.worker_manager import attempts as manager_attempts
        from baton_v12.worker_manager import tokens

        engine = Engine()
        job, control = self.stores("governed-start")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        # THE ENGINE'S OWN ACCOUNT: one launch, and it was the inert shape.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(engine.starts[0][1], "create",
                         "a governed start must compose the inert vector")
        self.assertEqual(len(engine.activations), 1,
                         "the bound container must then be activated exactly once")
        self.assertEqual(engine.activations[0][2], engine.runtime_id)
        # AND THE JOURNAL'S: the workspace object is held by this attempt's start.
        attempt = manager_attempts._require_attempt(control, attempt_id)
        domain = tokens.domain_of(
            "workspace", tokens.workspace_identity(attempt))
        held = tokens.outstanding(control, domain)
        self.assertEqual([one["execution"] for one in held], [attempt_id])
        current = tokens.token_of(control, domain, held[0]["generation"])
        self.assertEqual(current["container"], engine.runtime_id)
        self.assertEqual(current["launch"],
                         manager_attempts._start_operation_id(attempt))
        self.assertTrue(current["activation_started"])
        self.assertFalse(current["activating"])
        operations.close()
        job.close()
        control.close()

    def test_a_refused_admission_leaves_the_created_container_unrun(self):
        """W275774 review 16:29:48Z: THE NEGATIVE EFFECT CONTROL.

        The composed case above is the positive control -- the admission succeeds
        and the container runs. This is its counterpart, and it is the property the
        whole two-act boundary exists for: when the resource token will not admit
        the activation, the container that was created MUST NOT RUN.

        The refusal is injected at the token owner rather than faked at the engine,
        so what is measured is the production path's response to a real refusal: no
        activation vector reaches the engine, the container stays inert by the
        fixture's own state, and the pipeline does not report a running worker.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import tokens

        honest = tokens.admit_activation

        def refusing(control, token, *, container):
            raise ContractRefusal("refused", "precondition",
                                  "the fixture withholds this activation")

        tokens.admit_activation = refusing
        try:
            engine = Engine()
            job, control = self.stores("refused-admission")
            submit(job, self.submission)
            operations = self.operations(job, control, engine)
            for _ in range(6):
                try:
                    reconcile(job, operations, now=fixtures.NOW)
                except ContractRefusal:
                    break
        finally:
            tokens.admit_activation = honest
        # THE CONTAINER WAS COMPOSED AND NEVER RAN.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(engine.starts[0][1], "create")
        self.assertEqual(engine.activations, [],
                         "an unadmitted activation must never reach the engine")
        self.assertFalse(engine.running,
                         "the created container must still be inert")
        operations.close()
        job.close()
        control.close()

    def test_one_submission_becomes_one_observable_runtime_and_is_adopted(self):
        engine = Engine()
        job, control = self.stores("first")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        first = self.commanded(job, operations)
        stage = first["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "waiting")
        self.assertEqual(len(engine.starts), 1)
        attempt_id = stage["attempt_id"]
        self.assertEqual(attempt_runtime_of(control, attempt_id)["runtime_id"],
                         engine.runtime_id)
        self.assertEqual(len(claimed_offers_for(control, attempt_id)), 1)
        self.assertNotIn(self.secret, json.dumps(first))
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        operations.close()
        job.close()
        control.close()

        restarted_job, restarted_control = self.stores("restarted")
        restarted = self.operations(restarted_job, restarted_control, engine)
        after = self.commanded(restarted_job, restarted)
        self.assertEqual(after["jobs"][0]["stages"][0]["state"], "waiting")
        self.assertEqual(len(engine.starts), 1,
                         "restart started a duplicate OCI runtime")
        self.assertEqual(len(claimed_offers_for(restarted_control,
                                                attempt_id)), 1)
        self.assertNotIn(self.secret, json.dumps(after))
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        restarted.close()

    def test_a_credential_source_refusal_is_exceptional_and_not_retried(self):
        engine = Engine()
        job, control = self.stores("credential-refusal")
        submit(job, self.submission)
        calls = []

        def unavailable(provider, reference):
            calls.append((provider, reference))
            raise SourceRefusal("the fixture source is unavailable")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=unavailable, clock=lambda: fixtures.NOW)
        for _ in range(6):
            reconcile(job, operations, now=fixtures.NOW)
        projected = status(job, operations, observed_at=fixtures.NOW)
        self.assertEqual(projected["jobs"][0]["stages"][0]["state"],
                         "exceptional")
        self.assertEqual(calls, [("fixture", "fixture/one")])
        self.assertEqual(engine.starts, [])
        for _ in range(3):
            reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual(calls, [("fixture", "fixture/one")],
                         "a durable pre-start ending was retried")
        self.assertEqual(engine.starts, [])
        # AND THE LAUNCH DOCUMENT THIS INVOCATION AUTHORED IS GONE.
        # Re-review 2026-09-03T18:49:20Z [P1]: the reordering put the launch
        # delivery first, and the pre-start unwind tore down only the
        # credential -- so a stage that ends here left an attempt's
        # `launch.json` on disk with nothing that would ever come back for it.
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        self.assertFalse(
            os.path.lexists(os.path.join(
                os.path.realpath(self.config["launch_home"]), attempt_id)),
            "a launch delivery this invocation authored was left behind")
        operations.close()

    def test_an_accepted_offer_is_adopted_after_restart(self):
        engine = Engine()
        job, control = self.stores("accepted")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        reconcile(job, operations, now=fixtures.NOW)
        before = status(job, operations, observed_at=fixtures.NOW)
        self.assertEqual(before["jobs"][0]["stages"][0]["state"], "offered")
        operations.close()
        job.close()
        control.close()
        resumed_job, resumed_control = self.stores("accepted-resume")
        resumed = self.operations(resumed_job, resumed_control, engine)
        self.commanded(resumed_job, resumed)
        self.assertEqual(len(engine.starts), 1)
        resumed.close()

    def test_restart_after_the_claim_commits(self):
        self.crash_and_restart("claimed")

    def test_restart_after_the_attempt_record_commits(self):
        self.crash_and_restart("attempt")

    def test_restart_after_activation_commits(self):
        self.crash_and_restart("activation")

    def test_restart_after_workspace_allocation(self):
        self.crash_and_restart("workspace")

    # W71917: THE TWO NEW BOUNDARIES A CRASH CAN LAND BETWEEN. `boundary` is
    # after the source is proved and the empty mountpoint established and
    # before the input root is frozen; `adopted-boundary` is after the
    # pre-start re-proof and before the engine is called. A restart from
    # either has to adopt the SAME manager-owned workspace and the same
    # mountpoint rather than allocate a second one, which is what
    # `crash_and_restart` asserts by requiring exactly one start and one
    # claimed offer.
    def test_restart_after_the_source_boundary_is_composed(self):
        self.crash_and_restart("boundary")

    def test_restart_after_the_boundary_is_adopted_for_the_start(self):
        self.crash_and_restart("adopted-boundary")

    def test_restart_after_input_composition(self):
        self.crash_and_restart("input")

    def test_restart_after_manifest_retention(self):
        self.crash_and_restart("manifest")

    def test_restart_after_credential_materialization(self):
        self.crash_and_restart("credential")

    def test_restart_after_launch_delivery(self):
        self.crash_and_restart("launch")

    def test_restart_after_the_runtime_start_commits(self):
        self.crash_and_restart("runtime")

    def test_restart_reconciles_the_start_journal_engine_call_window(self):
        class InterruptedEngine(Engine):
            def __init__(self):
                super().__init__()
                self.interrupted = False

            def __call__(self, argv, *, seconds=None):
                if running_now(argv) and not self.interrupted:
                    answer = super().__call__(argv, seconds=seconds)
                    self.interrupted = True
                    raise KeyboardInterrupt("fixture process stopped")
                return super().__call__(argv, seconds=seconds)

        engine = InterruptedEngine()
        job, control = self.stores("start-window")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        with self.assertRaisesRegex(KeyboardInterrupt, "process stopped"):
            for _ in range(6):
                reconcile(job, operations, now=fixtures.NOW)
        projected = status(job, operations, observed_at=fixtures.NOW)
        attempt_id = projected["jobs"][0]["stages"][0]["attempt_id"]
        self.assertEqual(attempt_runtime_of(control, attempt_id)
                         ["execution_runtime"], "start-requested")
        self.assertIsNone(single_worker.credentials.CredentialHome(
            self.config["credential_home"]).read_state(attempt_id))
        operations.close()
        job.close()
        control.close()

        resumed_job, resumed_control = self.stores("start-window-resumed")
        resumed = self.operations(resumed_job, resumed_control, engine)
        after = self.commanded(resumed_job, resumed)
        self.assertEqual(after["jobs"][0]["stages"][0]["state"], "waiting")
        self.assertEqual(len(engine.starts), 1,
                         "reconciliation started a duplicate OCI runtime")
        resumed.close()

    def test_an_unbound_profile_is_refused_before_an_offer_or_engine_act(self):
        engine = Engine()
        job, control = self.stores("wrong-profile")
        wrong = copy.deepcopy(self.submission)
        wrong["jobs"][0]["stages"][0]["profile_name"] = "somebody-else"
        submit(job, wrong)
        operations = self.operations(job, control, engine)
        certify_profile(control, "runtime", "somebody-else",
                        fixtures.PROFILE)
        tick = reconcile(job, operations, now=fixtures.NOW)
        projected = status(job, operations, observed_at=fixtures.NOW)
        stage = projected["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "queued")
        self.assertEqual(tick["acts"][0]["outcome"], "deferred")
        self.assertEqual(tick["acts"][0]["detail"]["code"], "precondition")
        self.assertIsNone(control.operation_record(
            operations.canonical_operation("admit", stage["offer_id"])))
        self.assertEqual(engine.vectors, [])
        operations.close()

    def test_authority_bootstrap_paths_do_not_cross_into_the_runtime_composer(self):
        engine = Engine()
        job, control = self.stores("capabilities")
        operations = self.operations(job, control, engine)
        self.assertNotIn("authority_store", operations._worker.given)
        self.assertNotIn("principal", operations._worker.given)
        self.assertNotIn("credential_sources", operations._worker.given)
        self.assertNotIn("bearer", json.dumps(self.config))
        operations.close()


class TheConfigurationBoundaryIsClosed(SingleWorkerCase):
    def test_static_authority_contract_and_role_relationships_are_bound(self):
        cases = [
            ("authority_uuid", "f" * 32, "precondition"),
            ("launch_contract", "some-other-contract", "precondition"),
            ("launch_role", "review", "denied")]
        for member, value, code in cases:
            with self.subTest(member=member):
                job, control = self.stores("wrong-" + member)
                configured = dict(self.config, **{member: value})
                with self.assertRaises(ContractRefusal) as caught:
                    single_worker.operations_from(
                        configured, job, control, engine_run=Engine(),
                        credential_provider=lambda *_: self.secret)
                self.assertEqual(caught.exception.code, code)

    def test_authority_resolves_the_exact_configured_principal(self):
        job, control = self.stores("wrong-principal")
        configured = dict(self.config, principal="principal-somebody-else")
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(
                configured, job, control, engine_run=Engine(),
                credential_provider=lambda *_: self.secret)
        self.assertEqual(caught.exception.code, "capability")
        self.assertEqual(claimed_offers_for(control, "no-attempt"), [])

    def test_authority_resolves_the_exact_configured_participant(self):
        job, control = self.stores("wrong-participant")
        configured = dict(self.config, participant="other.member")
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(
                configured, job, control, engine_run=Engine(),
                credential_provider=lambda *_: self.secret)
        self.assertEqual(caught.exception.code, "capability")
        self.assertEqual(claimed_offers_for(control, "no-attempt"), [])

    def test_the_public_factory_reads_only_its_named_configuration(self):
        registry = os.path.join(self.root, "credential-sources.json")
        source = os.path.join(self.root, "provider.token")
        with open(source, "w", encoding="utf-8") as writing:
            writing.write(self.secret)
        os.chmod(source, 0o600)
        with open(registry, "w", encoding="utf-8") as writing:
            json.dump({"schema": "baton.user-credential-sources/1",
                       "sources": [{"provider": "fixture",
                                    "reference": "fixture/one",
                                    "path": source}]}, writing)
        os.chmod(registry, 0o600)
        configured = dict(self.config, credential_sources=registry)
        place = os.path.join(self.root, "single-worker.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(configured, writing)
        job, control = self.stores("factory")
        with mock.patch.dict(os.environ,
                             {single_worker.CONFIG_ENV: place}, clear=False):
            operations = single_worker.factory(job, control)
        self.assertNotIn("authority_store", operations._worker.given)
        operations.close()

    def resealed(self, **members):
        """One configuration whose manifest carries these overrides."""
        manifest = copy.deepcopy(self.manifest)
        manifest.update(members)
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        return dict(self.config, input_manifest=manifest)

    def refused(self, configured, name):
        job, control = self.stores(name)
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(
                configured, job, control, engine_run=Engine(),
                credential_provider=lambda *_: self.secret)
        # NOTHING WAS REACHED. Static task validation happens before the
        # Authority is opened and before any offer exists, so a refusal here
        # leaves no claimed offer and no attempt root to be partial.
        self.assertEqual(claimed_offers_for(control, "no-attempt"), [])
        self.assertEqual(os.listdir(self.storage), [])
        return caught.exception

    def test_a_configuration_of_the_superseded_schema_is_refused(self):
        """W81115: `/2` adds a required member, so it is a new contract.

        There is no fallback on purpose: a `/1` document names no task, and a
        deployment that started anyway would start the certified worker over a
        root it refuses before it does any provider work.

        W71917 MOVED THIS TO `/4` AND THE RULE IS UNCHANGED, which is why the
        case is amended rather than replaced. `/4` renames the source member
        and adds the workspace quota; a `/2` document is still refused by
        equality, and what the message must name is the version this build
        actually reads.
        """
        carrying = dict(self.config,
                        schema="baton.v12.single-worker-deployment/2")
        held = self.refused(carrying, "superseded-schema")
        self.assertEqual(held.code, "schema")
        self.assertIn("single-worker-deployment/4", held.message)

    def test_a_configuration_without_a_task_document_is_refused(self):
        carrying = dict(self.config)
        carrying.pop("task_document")
        held = self.refused(carrying, "no-task-member")
        self.assertEqual(held.code, "schema")
        self.assertIn("task_document", held.message)

    def test_task_material_this_deployment_cannot_hold_is_refused(self):
        """Every static negative, before anything exists to undo."""
        linked = os.path.join(self.root, "task-link.json")
        os.symlink(self.task_document, linked)
        directory = os.path.join(self.root, "task-directory")
        os.makedirs(directory)
        wide = os.path.join(self.root, "task-wide.json")
        with open(wide, "wb") as writing:
            writing.write(b"x" * (single_worker.MAX_TASK_BYTES + 1))
        fifo = os.path.join(self.root, "task-fifo.json")
        os.mkfifo(fifo)
        cases = [
            ("missing", os.path.join(self.root, "absent.json"), "path"),
            ("symlink", linked, "path"),
            ("directory", directory, "path"),
            # THE ANTI-HANG BOUNDARY, EXECUTED. Review 2026-09-04T00:56:36Z
            # [P2]: a directory refuses at the open, so it never reached the
            # case `O_NONBLOCK` is there for. Nothing has this FIFO open for
            # writing, so an ordinary blocking open would hang the whole
            # deployment before it started rather than refusing it.
            ("fifo", fifo, "path"),
            ("oversized", wide, "limit")]
        for name, place, code in cases:
            with self.subTest(case=name):
                held = self.refused(dict(self.config, task_document=place),
                                    "task-" + name)
                self.assertEqual(held.code, code)

    def test_a_task_that_is_not_the_declared_human_contract_is_refused(self):
        """The approved relationship, held in both directions.

        This profile DEFINES the task document as the input manifest's
        human-contract artifact, so the manifest's own media type, width and
        digest are what the held bytes are proved against. A profile whose
        human contract describes something else -- the conformance vector's
        Markdown dossier, say -- must refuse rather than deliver an unproved
        document.
        """
        contract = dict(self.manifest["human_contract"])
        cases = [
            ("media_type", dict(contract, media_type="text/markdown"),
             "precondition"),
            ("bytes", dict(contract, bytes=contract["bytes"] + 1), "digest"),
            ("content_digest",
             dict(contract, content_digest="sha256:" + "e" * 64), "digest"),
            ("width", dict(contract,
                           bytes=single_worker.MAX_TASK_BYTES + 1), "limit")]
        for name, human, code in cases:
            with self.subTest(member=name):
                held = self.refused(self.resealed(human_contract=human),
                                    "human-" + name)
                self.assertEqual(held.code, code)

    def test_a_source_destination_the_workload_does_not_read_is_refused(self):
        """The adjacent fact the reproduction found beside the missing task.

        The certified task contract fixes `source_root` and the adapter copies
        exactly `/input/source`, so a manifest staging anywhere else composes
        a root the worker cannot use -- which is how this deployment reached
        `running` with both fixed worker paths absent.
        """
        sources = copy.deepcopy(self.manifest["sources"])
        sources[0]["destination"] = "workspace/source"
        held = self.refused(self.resealed(sources=sources), "wrong-source")
        self.assertEqual((held.category, held.code), ("policy", "denied"))
        self.assertIn("workspace/source", held.message)

    def test_the_held_bytes_and_not_the_path_are_what_is_delivered(self):
        """A change to the configured path after construction changes nothing.

        The document is read once, at configuration time, and the constructed
        deployment carries the BYTES. Reopening the path at composition would
        put the delivery back at the mercy of whatever the path names then.
        """
        engine = Engine()
        job, control = self.stores("held-bytes")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        with open(self.task_document, "wb") as writing:
            writing.write(b'{"schema":"somebody-elses-task"}')
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        place = os.path.join(self.storage, stage["attempt_id"], "inputs",
                             single_worker.TASK_DOCUMENT)
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(), self.task_bytes)
        operations.close()

    def test_unknown_configuration_members_are_refused(self):
        job, control = self.stores("closed-config")
        carrying = dict(self.config, surprise=True)
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(carrying, job, control,
                                          engine_run=Engine(),
                                          credential_provider=lambda *_:
                                          self.secret)
        self.assertEqual(caught.exception.code, "schema")

    def test_a_changed_nominated_source_is_not_a_configuration_refusal(self):
        """W71917 REPLACED THE CHECK THAT STOOD HERE, and the replacement is
        the Work rather than a dropped obligation.

        `/3` measured `input_source` with `workspaces.directory_manifest` and
        compared it against the manifest's declared content -- a full
        no-follow walk that opened, read and digested every file in the
        nominated tree, performed by a manager ruled not to walk, copy,
        snapshot, enumerate or hash it. This proves the walk is gone: the
        content changes and the deployment is constructed, because the content
        was never this manager's to have an opinion about.

        WHAT IS NOT WEAKENED is proved by the case below it. The declaration
        the deployment CAN keep -- that it stages an empty mountpoint at that
        destination -- is still held, and still with the `digest` code the
        retired comparison used, so a manifest describing measured material at
        a nominated destination is refused before an offer exists.
        """
        with open(os.path.join(self.source, "worker-task.txt"), "a",
                  encoding="utf-8") as writing:
            writing.write("changed\n")
        job, control = self.stores("changed-source")
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=Engine(),
            credential_provider=lambda *_: self.secret)
        self.assertEqual(claimed_offers_for(control, "no-attempt"), [])
        operations.close()

    def test_a_manifest_claiming_measured_content_is_refused(self):
        sources = copy.deepcopy(self.manifest["sources"])
        sources[0]["content_manifest"] = (
            single_worker.workspaces.directory_manifest(self.source))
        held = self.refused(self.resealed(sources=sources), "measured-source")
        self.assertEqual((held.category, held.code), ("integrity", "digest"))

    def test_a_source_that_does_not_declare_the_boundary_is_refused(self):
        """A staged descriptor is not a nominated one, and mounting over it
        would deliver material the manifest does not describe."""
        sources = copy.deepcopy(self.manifest["sources"])
        sources[0]["consumption"] = {"baton.directory/1": {"layout": "flat"}}
        held = self.refused(self.resealed(sources=sources), "undeclared")
        self.assertEqual((held.category, held.code), ("integrity", "schema"))

    def test_a_nominated_source_that_is_a_link_is_refused(self):
        """A link at the nominated name is a source somebody else chose, and
        it is refused before the Authority is opened."""
        linked = os.path.join(self.root, "linked-source")
        os.symlink(self.source, linked)
        job, control = self.stores("linked-source")
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(dict(self.config,
                                               nominated_source=linked),
                                          job, control, engine_run=Engine(),
                                          credential_provider=lambda *_:
                                          self.secret)
        self.assertEqual(caught.exception.code, "path")
        self.assertEqual(claimed_offers_for(control, "no-attempt"), [])

    def test_a_workspace_capacity_inside_the_scratch_bound_is_refused(self):
        """The deterministic form of "the ruled uses must not rely on tmpfs".

        A workspace declared no larger than the private scratch beside it is
        one whose whole contents would have fitted in memory, so nothing about
        the delivery would distinguish a disk-backed checkout from one that
        happened to live in `/tmp`.
        """
        job, control = self.stores("small-capacity")
        carrying = dict(self.config, workspace_capacity={
            "max_bytes": source_boundary.MIN_WORKSPACE_BYTES})
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(carrying, job, control,
                                          engine_run=Engine(),
                                          credential_provider=lambda *_:
                                          self.secret)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))

    def test_a_workspace_capacity_declaring_an_entry_ceiling_is_refused(self):
        """The closed member set is what makes the removal a refusal.

        W71917's approved ruling removes `max_entries` because it reached no
        mount, no runtime and no sweep. A deployment that still declares it is
        answering a question this delivery never asks, and a document read
        with an ignored member would let it believe an entry ceiling applies.
        """
        job, control = self.stores("entry-ceiling")
        carrying = dict(self.config, workspace_capacity={
            "max_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1,
            "max_entries": 2000})
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(carrying, job, control,
                                          engine_run=Engine(),
                                          credential_provider=lambda *_:
                                          self.secret)
        self.assertEqual(caught.exception.code, "schema")
        self.assertIn("max_entries", caught.exception.message)


class TheWorkloadDocumentIsDeliveredWithTheProtocolPair(SingleWorkerCase):
    """W81115: the composed root the certified worker can actually read.

    W76207's production tests replace the OCI engine and prove the START
    VECTOR, so they proved a `running` projection over a root missing both
    paths the workload fixes. What is asserted here is the root itself.
    """

    def composed(self, name="workload-root"):
        engine = Engine()
        job, control = self.stores(name)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        inputs = os.path.join(self.storage, stage["attempt_id"], "inputs")
        return engine, job, control, operations, stage, inputs

    def judgment_root(self):
        engine = Engine()
        job, control = self.stores("judgment-input")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        worker = operations._worker
        worker.judgment_document = b'{"result_id":"derived-result","kind":"review"}'
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        inputs = os.path.join(self.storage, stage["attempt_id"], "inputs")
        self.addCleanup(operations.close)
        return worker, inputs

    def test_judgment_subject_is_delivered_read_only_beside_unchanged_task(self):
        worker, inputs = self.judgment_root()
        place = os.path.join(inputs, "judgment.json")
        self.assertEqual(stat.S_IMODE(os.stat(place).st_mode), 0o444)
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(), worker.judgment_document)
        with open(os.path.join(inputs, "task.json"), "rb") as reading:
            self.assertEqual(reading.read(), self.task_bytes)
        manifest, assignment = single_worker.workspaces.read_input_root(inputs)
        self.assertEqual(worker._input({"inputs": inputs}, assignment, None), manifest)

    def test_changed_judgment_subject_refuses_recovery_without_repair(self):
        worker, inputs = self.judgment_root()
        place = os.path.join(inputs, "judgment.json")
        os.chmod(place, 0o644)
        with open(place, "wb") as writing:
            writing.write(b'{"result_id":"foreign"}')
        os.chmod(place, 0o444)
        _, assignment = single_worker.workspaces.read_input_root(inputs)
        with self.assertRaises(ContractRefusal):
            worker._input({"inputs": inputs}, assignment, None)
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(), b'{"result_id":"foreign"}')

    def test_the_root_carries_both_manifests_the_task_and_the_source(self):
        engine, _job, _control, operations, _stage, inputs = self.composed()
        self.assertEqual(
            sorted(os.listdir(inputs)),
            ["assignment.json", "input.json", "source", "task.json"])
        with open(os.path.join(inputs, single_worker.TASK_DOCUMENT),
                  "rb") as reading:
            self.assertEqual(reading.read(), self.task_bytes)
        self.assertTrue(os.path.isdir(
            os.path.join(inputs, single_worker.SOURCE_DESTINATION)))
        self.assertEqual(len(engine.starts), 1)
        operations.close()

    def test_the_task_is_read_only_inside_a_frozen_root(self):
        """The mode says on disk what the delivery says in prose, and the
        frozen root is what stops the host replacing a bound file."""
        _engine, _job, _control, operations, _stage, inputs = self.composed(
            "workload-modes")
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        self.assertEqual(stat.S_IMODE(os.stat(place).st_mode), 0o444)
        self.assertEqual(stat.S_IMODE(os.stat(inputs).st_mode), 0o555)
        self.assertFalse(os.path.lexists(place + ".composing"),
                         "a staging name survived the composition")
        operations.close()

    def test_the_engine_is_given_the_root_that_carries_the_task(self):
        """The mount vector and the composed root are one fact, not two."""
        engine, _job, _control, operations, _stage, inputs = self.composed(
            "workload-mount")
        mounted = [one for one in engine.mounts
                   if one["Destination"] == "/input"]
        self.assertEqual(len(mounted), 1)
        self.assertEqual(os.path.realpath(mounted[0]["Source"]),
                         os.path.realpath(inputs))
        self.assertFalse(mounted[0]["RW"])
        operations.close()

    def test_a_restart_neither_rewrites_the_task_nor_starts_a_second_runtime(
            self):
        """The already-composed root is ADOPTED, and proving it now includes
        the workload document."""
        engine, job, control, operations, stage, inputs = self.composed(
            "workload-restart")
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        before = os.stat(place)
        operations.close()
        resumed_job, resumed_control = self.stores("workload-restart-again")
        resumed = self.operations(resumed_job, resumed_control, engine)
        for _ in range(6):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        after = os.stat(place)
        self.assertEqual((after.st_ino, after.st_mtime_ns),
                         (before.st_ino, before.st_mtime_ns),
                         "a restart republished the task document")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(
            self.staged(status(resumed_job, resumed,
                               observed_at=fixtures.NOW))
            ["job-a/implementation"]["state"], "waiting")
        resumed.close()

    @staticmethod
    def staged(projected):
        return {one["stage_id"]: one
                for job_status in projected["jobs"]
                for one in job_status["stages"]}

    def rewritten(self, place, payload):
        """Replace a delivered document inside the frozen root."""
        os.chmod(os.path.dirname(place), 0o755)
        os.chmod(place, 0o644)
        with open(place, "wb") as writing:
            writing.write(payload)
        os.chmod(place, 0o444)
        os.chmod(os.path.dirname(place), 0o555)

    def test_a_changed_task_in_a_composed_root_refuses_rather_than_repairs(
            self):
        """`read_input_root` reads exactly the two PROTOCOL documents, so a
        matching manifest pair says nothing about the workload material beside
        it. Inferring the task from `input.json` would be this deployment
        concluding something the reader it called never looked at."""
        engine, _job, _control, operations, _stage, inputs = self.composed(
            "workload-changed")
        operations.close()
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        self.rewritten(place, b'{"schema": "somebody-elses-task"}')
        resumed_job, resumed_control = self.stores("workload-changed-again")
        resumed = self.operations(resumed_job, resumed_control, engine)
        for _ in range(6):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        held = self.staged(status(resumed_job, resumed,
                                  observed_at=fixtures.NOW))
        self.assertEqual(held["job-a/implementation"]["state"], "waiting",
                         "the already-started runtime was not left alone")
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(),
                             b'{"schema": "somebody-elses-task"}',
                             "the changed task was repaired in place")
        self.assertEqual(len(engine.starts), 1)
        resumed.close()

    def contended(self, name, plant):
        """One real composition with `plant` racing the task's creation.

        THE SEAM IS THE EXCLUSIVE CREATION ITSELF, because that is the only
        pathname this operation has left: the document is created directly at
        its final name and every act after it is on that descriptor. `plant`
        runs immediately before the real `os.open`, which is the whole of the
        interval a racing creator gets.
        """
        engine = Engine()
        job, control = self.stores(name)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        raced = []
        opener = os.open

        def racing(place, flags, *rest, **options):
            if isinstance(place, str) \
                    and place.endswith(single_worker.TASK_DOCUMENT) \
                    and flags & os.O_CREAT and not raced:
                raced.append(place)
                plant(place)
            return opener(place, flags, *rest, **options)

        with mock.patch.object(single_worker.os, "open", racing):
            for _ in range(6):
                reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual(len(raced), 1, "the publishing seam was never driven")
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        stage = held["job-a/implementation"]
        # ONE RECORDED ENDING AND NO RUNTIME, whatever was planted.
        self.assertEqual(stage["state"], "exceptional")
        self.assertEqual(engine.starts, [], "a runtime ran over that root")
        self.assertIsNotNone(
            attempt_preparation_failure_of(control, stage["attempt_id"]))
        operations.close()
        return raced[0]

    def test_a_target_that_appears_before_the_creation_is_refused(self):
        """Review 2026-09-04T00:56:36Z [P1]: the rename seam clobbered.

        `O_EXCL` guarded only a staging name, and the act finished with
        `os.replace`, which CLOBBERS -- so a creator that won the interval
        between the absence check and the rename had its document silently
        replaced by this one. The exclusive creation of the final name is both
        decisions at once now, and this drives a creator winning it.
        """
        foreign = b'{"schema": "somebody-elses-task"}'

        def plant(place):
            with open(place, "xb") as writing:
                writing.write(foreign)

        place = self.contended("workload-collision", plant)
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(), foreign,
                             "the racing document was replaced")

    def test_a_link_at_the_final_name_is_refused_and_never_followed(self):
        """Review 2026-09-04T01:06:30Z [P1]: the proved descriptor and the
        published object must be one inode.

        The correction that removed the rename left the STAGING name as a
        mutable pathname between the proof and the publication, so a creator
        that unlinked it and put a symlink there had that symlink hard-linked
        at the final name and reported as success. There is no second pathname
        now, so the substitution has nowhere to happen -- and a link that
        arrives at the FINAL name is refused by the same exclusive creation
        rather than written through.
        """
        elsewhere = os.path.join(self.root, "foreign-task.json")
        with open(elsewhere, "wb") as writing:
            writing.write(b'{"schema": "somebody-elses-task"}')

        place = self.contended("workload-linked",
                               lambda where: os.symlink(elsewhere, where))
        self.assertTrue(os.path.islink(place), "the link was replaced")
        with open(elsewhere, "rb") as reading:
            self.assertEqual(reading.read(),
                             b'{"schema": "somebody-elses-task"}',
                             "the link was followed and its target written")

    def test_the_published_document_is_the_held_bytes_at_a_real_file(self):
        """The positive half of the same rule, asserted at the final name.

        What the root carries is an ordinary file -- not a link, not a
        directory -- whose bytes are exactly the ones this deployment read once
        and holds, and whose mode is the read-only one that says on disk what
        the delivery says in prose.
        """
        _engine, _job, _control, operations, _stage, inputs = self.composed(
            "workload-identity")
        place = os.path.join(inputs, single_worker.TASK_DOCUMENT)
        found = os.lstat(place)
        self.assertTrue(stat.S_ISREG(found.st_mode), "the task is not a file")
        self.assertFalse(stat.S_ISLNK(found.st_mode))
        self.assertEqual(stat.S_IMODE(found.st_mode), 0o444)
        self.assertEqual(found.st_nlink, 1,
                         "the published document carries another name")
        with open(place, "rb") as reading:
            self.assertEqual(reading.read(), self.task_bytes)
        operations.close()

    def test_a_task_changed_before_the_root_is_adopted_is_refused(self):
        """Review [P2]: the changed-task case only covered a live runtime.

        This is the other one: composition completed, the process stopped
        before the start, and the workload document changed before the next
        process adopted the root. `read_input_root` would accept that root --
        its protocol pair is untouched -- so the task proof is the only thing
        standing between a worker and a document nobody delivered.
        """
        engine = Engine()
        job, control = self.stores("workload-adopt-changed")
        submit(job, self.submission)
        stopped = []

        def dying(point):
            if point == "input" and not stopped:
                stopped.append(point)
                raise RuntimeError("fixture process stopped")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=dying)
        with self.assertRaisesRegex(RuntimeError, "process stopped"):
            for _ in range(6):
                reconcile(job, operations, now=fixtures.NOW)
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        attempt_id = held["job-a/implementation"]["attempt_id"]
        inputs = os.path.join(self.storage, attempt_id, "inputs")
        self.assertEqual(sorted(os.listdir(inputs)),
                         ["assignment.json", "input.json", "source",
                          "task.json"], "the root was not composed")
        self.assertEqual(engine.starts, [], "a runtime was already started")
        operations.close()

        foreign = b'{"schema": "somebody-elses-task"}'
        self.rewritten(os.path.join(inputs, single_worker.TASK_DOCUMENT),
                       foreign)
        resumed_job, resumed_control = self.stores("workload-adopt-again")
        resumed = self.operations(resumed_job, resumed_control, engine)
        for _ in range(6):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        self.assertEqual(
            self.staged(status(resumed_job, resumed,
                               observed_at=fixtures.NOW))
            ["job-a/implementation"]["state"], "exceptional")
        self.assertEqual(engine.starts, [], "a runtime ran over that root")
        self.assertIsNotNone(
            attempt_preparation_failure_of(resumed_control, attempt_id))
        with open(os.path.join(inputs, single_worker.TASK_DOCUMENT),
                  "rb") as reading:
            self.assertEqual(reading.read(), foreign,
                             "the changed task was repaired in place")
        resumed.close()

    def test_a_task_this_composition_did_not_write_is_never_replaced(self):
        """An input root carrying workload material from somewhere else is
        material whose provenance this deployment cannot prove, and W76207's
        rule for exactly that is one recorded preparation ending."""
        engine = Engine()
        job, control = self.stores("workload-foreign")
        submit(job, self.submission)
        planted = []

        def before_input(point):
            if point == "workspace" and not planted:
                planted.append(point)
                held = self.staged(status(job, operations,
                                          observed_at=fixtures.NOW))
                inputs = os.path.join(
                    self.storage,
                    held["job-a/implementation"]["attempt_id"], "inputs")
                with open(os.path.join(inputs,
                                       single_worker.TASK_DOCUMENT),
                          "wb") as writing:
                    writing.write(b'{"schema": "somebody-elses-task"}')

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=before_input)
        for _ in range(6):
            reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual(planted, ["workspace"],
                         "the fixture never planted a foreign task")
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        self.assertEqual(engine.starts, [], "a runtime ran over that root")
        self.assertIsNotNone(attempt_preparation_failure_of(
            control, held["job-a/implementation"]["attempt_id"]))
        operations.close()

    def test_an_interrupted_composition_refuses_rather_than_completing_it(
            self):
        """W76207's partial-root rule, now with workload material in it.

        A death after the task is published and before the protocol pair is
        frozen leaves a partial root, and the next process refuses it rather
        than finishing somebody else's composition.
        """
        engine = Engine()
        job, control = self.stores("workload-partial")
        submit(job, self.submission)
        stopped = []

        def dying(*args, **members):
            del args, members
            stopped.append("composing")
            raise RuntimeError("fixture process stopped")

        operations = self.operations(job, control, engine)
        # THE INTERVAL IS INSIDE `_input`, which is why this is not a
        # checkpoint: the `input` checkpoint fires after the whole root is
        # composed. What a death here leaves is the workload material this
        # composition published and the protocol pair it never wrote.
        with mock.patch.object(single_worker.workspaces,
                               "compose_input_root", dying):
            with self.assertRaisesRegex(RuntimeError, "process stopped"):
                for _ in range(6):
                    reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual(stopped, ["composing"])
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        attempt_id = held["job-a/implementation"]["attempt_id"]
        inputs = os.path.join(self.storage, attempt_id, "inputs")
        self.assertIn(single_worker.TASK_DOCUMENT, os.listdir(inputs))
        self.assertNotIn("input.json", os.listdir(inputs),
                         "the fixture stopped after the pair was composed")
        self.assertEqual(stopped, ["composing"])
        operations.close()

        resumed_job, resumed_control = self.stores("workload-partial-again")
        resumed = self.operations(resumed_job, resumed_control, engine)
        for _ in range(6):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        self.assertEqual(
            self.staged(status(resumed_job, resumed,
                               observed_at=fixtures.NOW))
            ["job-a/implementation"]["state"], "exceptional")
        self.assertEqual(engine.starts, [])
        self.assertIsNotNone(
            attempt_preparation_failure_of(resumed_control, attempt_id))
        resumed.close()


class TheCertifiedWorkerReachesTheDeliveredTask(SingleWorkerCase):
    """W81115's acceptance, proved from the RECEIVING end.

    Every other case here asserts what this deployment composes. This one
    asserts that the certified workload can use it: the real `baton_worker`
    program, in this process, over the real framed transport, with the real
    `ClaudeAgent` behind the documented `main(agent=...)` seam and only the
    provider process replaced -- driven at the exact root `single_worker`
    produced.

    A HOST-SIDE PARSER CALL WOULD NOT BE THIS. The reproduction that opened
    this Work called `claude_agent._task` directly, which proves the document
    is readable and nothing about whether a `work` request gets that far. The
    defect was that the worker refuses BEFORE any provider work, so the
    evidence has to be the provider seam being reached.

    NO DAEMON AND NO PROVIDER CREDENTIAL. The engine boundary is this suite's
    recording fixture as everywhere else, the transport is a pipe pair, and
    the provider is an injected process-running capability.
    """

    def composed_root(self):
        engine = Engine()
        job, control = self.stores("reachability")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        projected = self.commanded(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        operations.close()
        return os.path.join(self.storage, stage["attempt_id"], "inputs")

    def test_a_work_request_over_the_composed_root_reaches_the_provider(self):
        from tests.manager.test_worker_entry import (LiveWorker,
                                                     launch_document, spoken)
        import baton_worker
        import claude_agent
        from claude_agent import ClaudeAgent

        inputs = self.composed_root()
        # W71917: THE CONTAINER'S VIEW OF THE BIND, staged here because this
        # process has no mount namespace.
        #
        # The manager composes `inputs/source` as an EMPTY mountpoint on
        # purpose -- nothing is walked, copied or hashed -- and the runtime
        # binds the nominated directory over it. Inside the container the
        # worker sees the nominated tree at that path, so what is modelled
        # here is that view and not the host's. Copying the nominated source's
        # own bytes in is the closest this suite can get without the privilege
        # to mount, and it is the read-only side of the transition under test;
        # the WRITABLE side -- the checkout and candidate landing in the
        # workspace rather than on the tmpfs -- is real and is asserted below.
        mountpoint = os.path.join(inputs, single_worker.SOURCE_DESTINATION)
        self.assertEqual(os.listdir(mountpoint), [],
                         "the manager staged material into the mountpoint")
        os.chmod(inputs, 0o700)
        os.chmod(mountpoint, 0o700)
        for base, _directories, files in os.walk(self.source):
            for name in files:
                full = os.path.join(base, name)
                landing = os.path.join(
                    mountpoint, os.path.relpath(full, self.source))
                os.makedirs(os.path.dirname(landing), exist_ok=True)
                shutil.copyfile(full, landing)
        # THE WORKLOAD'S OWN CONSTANTS, held against this deployment's copies.
        # The image cannot import this package and this package cannot import
        # the image, so the two fixed names exist twice; this is where they
        # stop being allowed to disagree.
        self.assertEqual(single_worker.TASK_DOCUMENT,
                         claude_agent.TASK_DOCUMENT)
        self.assertEqual(single_worker.SOURCE_DESTINATION,
                         claude_agent.SOURCE_ROOT)
        outputs = os.path.join(self.root, "worker-output")
        scratch = os.path.join(self.root, "worker-scratch")
        credentials = os.path.join(self.root, "worker-credentials")
        for place in (outputs, scratch, credentials):
            os.makedirs(place)
        with open(os.path.join(credentials, "claude"), "w",
                  encoding="utf-8") as writing:
            writing.write("not-a-credential\n")
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", inputs),
                (baton_worker, "OUTPUT_ROOT", outputs),
                (claude_agent, "INPUT_ROOT", inputs),
                (claude_agent, "OUTPUT_ROOT", outputs),
                (claude_agent, "CREDENTIAL_ROOT", credentials)):
            held = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, held)

        spoke = []

        def provider(argv, **options):
            spoke.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, None, None)

        agent = ClaudeAgent(run=provider, home=scratch)
        answered = spoken(self, LiveWorker(agent, launch_document(self)),
                          ["work"], ["op-w81115-1"])
        self.assertEqual(answered["ending"], "answered", answered["why"])
        answer = answered["answers"][0]
        self.assertTrue(answer["ok"], answer)
        # THE PROVIDER SEAM WAS REACHED, which is the whole acceptance: the
        # worker read the delivered task, staged the delivered source, and got
        # as far as running the thing this deployment cannot run for it.
        self.assertTrue(spoke, "the work turn never reached the provider")
        self.assertEqual(spoke[0][0], claude_agent.PROVIDER_PROGRAM)
        # AND THE PROMPT IS THE DELIVERED TASK'S OWN INSTRUCTIONS, so the
        # document that crossed is the one this deployment published rather
        # than any other readable file.
        held = json.loads(self.task_bytes.decode("utf-8"))
        self.assertTrue(
            any(held["instructions"] in one for one in spoke[0]),
            "the provider was not given the delivered task's instructions")
        # W71917: AND THE WORK HAPPENED IN THE WORKSPACE, not on the tmpfs.
        #
        # This is the transition the run7 candidate composed plans for and
        # never performed. The editable copy is under the writable workspace
        # bind, it is NOT under the private scratch, and the read-only mount
        # still holds exactly what it held before the turn.
        candidate = os.path.join(outputs, claude_agent.CANDIDATE_NAME)
        self.assertTrue(os.path.isdir(candidate),
                        f"no candidate in the workspace: {os.listdir(outputs)}")
        self.assertFalse(os.path.exists(os.path.join(
            scratch, claude_agent.CANDIDATE_NAME)),
            "the editable copy is still being made on the tmpfs")
        self.assertEqual(
            sorted(os.listdir(candidate)), sorted(os.listdir(mountpoint)),
            "the workspace copy is not the mounted source's content")
        self.assertEqual(sorted(os.listdir(mountpoint)),
                         sorted(os.listdir(self.source)),
                         "the turn modified the read-only source")


class PreparationCase(SingleWorkerCase):
    """One submission this deployment serves, beside one it never can.

    `job-b` names the same Work, so the deployment's admission defers it on
    every tick rather than refusing it once: it is the stage that has to STILL
    BE REACHED after `job-a` ends badly, and a sweep that aborted on the first
    failure would never report it again.
    """

    def setUp(self):
        super().setUp()
        self.submission["jobs"].append(fixtures.job(
            job_id="job-b",
            input_digest=job_input_identity(self.manifest),
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[fixtures.stage(work_id=fixtures.WORK_A,
                                   profile_name="reference",
                                   profile_digest=fixtures.PROFILE)]))
        self.launches = []

    def offered(self, name, engine):
        """One tick, so the offer and its attempt identity are readable."""
        job, control = self.stores(name)
        submit(job, self.submission)
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        reconcile(job, operations, now=fixtures.NOW)
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        self.assertEqual(held["job-a/implementation"]["state"], "offered")
        return job, control, operations, held["job-a/implementation"]

    @staticmethod
    def staged(projected):
        return {one["stage_id"]: one
                for job_status in projected["jobs"]
                for one in job_status["stages"]}

    def serve(self, job, operations, ticks=6):
        for _ in range(ticks):
            reconcile(job, operations, now=fixtures.NOW)
        return self.staged(status(job, operations, observed_at=fixtures.NOW))


class APreparationFailureEndsInTheOwnersJournal(PreparationCase):
    """Review 2026-09-03T17:23:00Z [P1]: the boundaries with no ending.

    Workspace adoption, input composition and manifest retention ran OUTSIDE
    the settlement, so a foreign workspace or a partial input root returned to
    the control plane with no failed-start record: an ordinary refusal was
    reported as a condition and asked again on every tick, and a durable one
    aborted the whole sweep. Neither is one exceptional, non-retried stage.
    """

    def spoiled(self, name, spoil):
        self.assertLess("job-a/implementation", "job-b/implementation",
                        "the failing stage must sort first for this to prove "
                        "the sweep was not abandoned at it")
        engine = Engine()
        job, control, operations, stage = self.offered(name, engine)
        attempt_id = stage["attempt_id"]
        spoil(os.path.join(self.storage, attempt_id))
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        recorded = attempt_preparation_failure_of(control, attempt_id)
        self.assertIsNotNone(recorded,
                             "the deployment left the owner no preparation "
                             "record to project")
        self.assertIsNone(attempt_start_failure_of(control, attempt_id),
                          "a preparation that never reached an adapter must "
                          "not be filed as the start act it did not perform")
        # NOT RETRIED. `claimed` is the first checkpoint of every launch, so
        # counting it counts the times this stage was driven at all.
        self.assertEqual(self.launches, ["claimed"],
                         "the ended stage was asked again")
        self.assertEqual(engine.starts, [], "nothing reached the engine")
        # AND THE SWEEP IS STILL SERVING THE OTHER STAGE. It is `queued`
        # because this one-worker deployment admits only one assignment at a
        # time; what matters is that a later tick still reaches and reports it.
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        report = reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual([one["stage_id"] for one in report["acts"]],
                         ["job-b/implementation"])
        operations.close()
        return recorded

    def test_a_structurally_foreign_workspace_is_exceptional_and_not_retried(self):
        """An `inputs` entry that is not this attempt's own directory."""
        def spoil(home):
            os.makedirs(home)
            with open(os.path.join(home, "inputs"), "w",
                      encoding="utf-8") as writing:
                writing.write("not a directory\n")

        recorded = self.spoiled("foreign-workspace", spoil)
        self.assertEqual(recorded["failure"]["kind"], "refusal")
        self.assertIn("inputs root", recorded["failure"]["message"])

    def test_a_partial_input_root_is_exceptional_and_not_retried(self):
        """The crash-mid-composition shape: material, and no protocol pair.

        `compose_input_root` copies the staged source and only then writes
        `input.json` and `assignment.json`, so a process that died between
        them leaves exactly this. Restart refuses rather than completing
        material whose provenance it cannot prove -- and that refusal is now
        an ending rather than a condition asked again forever.
        """
        def spoil(home):
            inputs = os.path.join(home, "inputs")
            os.makedirs(inputs)
            with open(os.path.join(inputs, "half-copied.txt"), "w",
                      encoding="utf-8") as writing:
                writing.write("material with no protocol pair\n")

        recorded = self.spoiled("partial-input", spoil)
        self.assertEqual(recorded["failure"]["kind"], "refusal")
        self.assertEqual((recorded["failure"]["category"],
                          recorded["failure"]["code"]),
                         ("integrity", "path"),
                         "the partial-input branch raised a pair §9 does not "
                         "carry, so it rejected its own raising site")
        self.assertIn("partial", recorded["failure"]["message"])

    def test_the_partial_input_refusal_is_typed_rather_than_an_assertion(self):
        """Driven through `_input`, not the private helper.

        The reviewer's probe called `_refuse` directly; this reaches the same
        branch the way production does, so what is proved is the branch rather
        than the spelling of one call.
        """
        engine = Engine()
        job, control, operations, stage = self.offered("typed-pair", engine)
        inputs = os.path.join(self.storage, stage["attempt_id"], "inputs")
        os.makedirs(inputs)
        with open(os.path.join(inputs, "half-copied.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("material with no protocol pair\n")
        # W71917: THE BRANCH NOW NEEDS A COMPOSED BOUNDARY, because "partial"
        # is no longer "not empty" -- the empty mountpoint is the ordinary
        # pre-composition state. The roots and the boundary are obtained the
        # way production obtains them, so what this drives is still the branch
        # rather than a spelling: `half-copied.txt` is an entry that is NOT the
        # mountpoint, which is exactly what the rule refuses.
        worker = operations._worker
        roots = single_worker.workspaces.assignment_workspace(
            worker.group, self.storage, stage["attempt_id"])
        boundary = source_boundary.compose_source_boundary(
            worker.given["source_nomination"], roots,
            worker.given["workspace_capacity"])
        with self.assertRaises(ContractRefusal) as caught:
            worker._input(
                roots,
                {"assignment_ref": {}, "runtime_attempt_id": "unused"},
                boundary)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "path"))
        operations.close()


class CredentialRestartProvesTheLiveRuntimeFirst(PreparationCase):
    """Review 2026-09-03T17:23:00Z [P1]: adoption compared a record with itself.

    The composition read the credential lifecycle record and called
    `CredentialHome.adopt` with the runtime id taken out of that same record,
    so bearer bytes were re-registered before anything proved the live
    container was the one the record names or that it holds the intended
    mount. `OciAdapter.recover_credentials` is the owner boundary for exactly
    that question, and ordinary `reconcile_runtime` performs none of it.
    """

    def published(self, name):
        """Stop in the ONE window this branch exists for.

        `OciAdapter.start` writes the credential lifecycle record as soon as
        the engine names a runtime, and `reconcile_runtime` attaches that
        identity to the attempt afterwards. A process that dies between them
        leaves `start-requested`, no attached runtime -- so the stage is still
        `claimed` and is launched again -- and a published record naming a
        container this incarnation never saw. That is the restart the adoption
        proof is about.
        """
        class Published(Engine):
            def __init__(self):
                super().__init__()
                self.armed = False

            def __call__(self, argv, *, seconds=None):
                if argv[1] == "ps" and self.armed:
                    self.armed = False
                    raise KeyboardInterrupt("fixture process stopped")
                answer = super().__call__(argv, seconds=seconds)
                self.armed = self.armed or running_now(argv)
                return answer

        engine = Published()
        job, control = self.stores(name)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        with self.assertRaisesRegex(KeyboardInterrupt, "process stopped"):
            for _ in range(6):
                reconcile(job, operations, now=fixtures.NOW)
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        stage = held["job-a/implementation"]
        self.assertEqual(attempt_runtime_of(control, stage["attempt_id"])
                         ["execution_runtime"], "start-requested")
        self.assertIsNotNone(single_worker.credentials.CredentialHome(
            self.config["credential_home"]).read_state(stage["attempt_id"]),
            "this window is the one where a delivery IS published")
        operations.close()
        job.close()
        control.close()
        return engine, stage

    def ended(self, job, control, operations, stage, detail):
        """The half the last correction left open: LATER ticks, not the first.

        Review 2026-09-03T18:16:57Z [P1]: a recovery refusal was re-raised as
        an ordinary condition, so the stage stayed `claimed` and was asked
        again forever -- and the account the code claimed to preserve was not
        in fact repeated, because the first recovery's bounded stop and
        cleanup had already changed what the next one could find. The refusal
        is now the manager's own durable preparation record, so this asserts
        the state SIX ticks later and that nothing asked again.
        """
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        recorded = attempt_preparation_failure_of(control,
                                                  stage["attempt_id"])
        self.assertIsNotNone(recorded)
        # THE REFUSAL'S OWN ACCOUNT IS WHAT WAS RECORDED, and what the
        # control plane was told is that account plus which record this
        # manager wrote for it.
        self.assertTrue(detail.startswith(recorded["failure"]["message"]),
                        "the reported refusal is not the recorded one")
        self.assertIn("the failed preparation is journalled as", detail)
        # THE RECORD NAMES WHAT THE IDENTIFICATION FOUND, which is why it is
        # written after it: `start-requested` would be this manager saying
        # `None` about a runtime it had just attached, or about one it had
        # just proved it could not establish.
        self.assertNotEqual(recorded["execution_runtime"], "start-requested")
        self.assertEqual(recorded["runtime_id"],
                         attempt_runtime_of(control,
                                            stage["attempt_id"])["runtime_id"])
        self.assertIsNone(attempt_start_failure_of(control,
                                                   stage["attempt_id"]),
                          "a preparation is not the start act's record")
        self.assertEqual(self.launches, ["claimed"],
                         "the ended stage was asked again on a later tick")
        # AND THE SWEEP IS STILL SERVING. The ending is contained to its
        # stage; the other one is still reached and reported.
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        return held

    def resumed(self, name, engine):
        job, control = self.stores(name)
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        return job, control, operations

    def test_the_exact_recovery_adopts_through_the_public_proof(self):
        """The positive case: the engine is ASKED before any bearer is
        reread."""
        engine, stage = self.published("recovery-exact")
        job, control, operations = self.resumed("recovery-exact-again", engine)
        asked = len(engine.vectors)
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "waiting")
        self.assertEqual(len(engine.starts), 1,
                         "recovery started a second runtime")
        # THE PROOF IS ENGINE TRAFFIC, and adoption used to make none of it.
        self.assertIn("ps", [one[1] for one in engine.vectors[asked:]])
        self.assertIn("inspect", [one[1] for one in engine.vectors[asked:]])
        self.assertIsNone(attempt_start_failure_of(control,
                                                   stage["attempt_id"]))
        operations.close()

    def test_a_record_naming_another_runtime_is_refused_without_adopting(self):
        """The live runtime is not the one this manager's record names.

        Nothing is exactly identified here, so the recovery contract leaves
        every candidate where it is and reports it. What must not happen is
        the adoption: no bearer is re-registered, no output is accepted, and
        no replacement runtime is started.
        """
        engine, stage = self.published("recovery-mismatch")

        class Renamed(Engine):
            def __call__(self, argv, *, seconds=None):
                answer = engine(argv, seconds=seconds)
                if argv[1] == "ps":
                    return self.answer(
                        stdout=answer["stdout"].replace(
                            engine.runtime_id, "runtime-somebody-else"))
                return answer

        job, control, operations = self.resumed("recovery-mismatch-again",
                                                Renamed())
        report = reconcile(job, operations, now=fixtures.NOW)
        detail = report["started"][0]["detail"]["message"]
        self.assertIn("cannot be recovered", detail)
        self.assertIn("the lifecycle record names", detail)
        self.assertIn("0 exactly identified runtime(s) were stopped", detail,
                      "an unidentified candidate must be left untouched")
        self.ended(job, control, operations, stage, detail)
        self.assertEqual(len(engine.starts), 1,
                         "a refused recovery started a replacement")
        # AND IT IS NAMED RATHER THAN LEFT ANONYMOUS. Adopting the delivery
        # was refused; identifying the container the engine reports under this
        # attempt's whole label set is the separate act that leaves an
        # operator something to end.
        self.assertIsNotNone(
            attempt_runtime_of(control, stage["attempt_id"])["runtime_id"],
            "the refused recovery left the runtime with no identity")
        operations.close()

    def test_a_mismatched_credential_mount_is_refused_and_stopped(self):
        """Exactly identified, and what disagrees is what it has mounted.

        This is the one candidate the recovery contract permits stopping, so
        the bounded stop and the cleanup that follows it ride out with the
        refusal and are preserved here rather than replaced by a tidier
        ending.
        """
        engine, stage = self.published("recovery-mount")
        root = single_worker.credentials.CREDENTIAL_ROOT

        class Unmounted(Engine):
            def __call__(self, argv, *, seconds=None):
                answer = engine(argv, seconds=seconds)
                if argv[1] != "inspect":
                    return answer
                body = json.loads(answer["stdout"])
                body["Mounts"] = [one for one in body["Mounts"]
                                  if not one["Destination"].startswith(root)]
                return self.answer(stdout=json.dumps(body))

        engine.vectors.clear()
        job, control, operations = self.resumed("recovery-mount-again",
                                                Unmounted())
        report = reconcile(job, operations, now=fixtures.NOW)
        detail = report["started"][0]["detail"]["message"]
        self.assertIn("cannot be recovered", detail)
        self.assertIn("carries 0 binds", detail)
        self.assertIn("1 exactly identified runtime(s) were stopped", detail,
                      "the one candidate the ruling permits stopping")
        self.assertIn(engine.runtime_id, json.dumps(engine.vectors),
                      "the stop never reached the engine")
        self.assertEqual(engine.starts, [],
                         "a refused recovery started a replacement")
        self.ended(job, control, operations, stage, detail)
        self.assertIsNotNone(
            attempt_runtime_of(control, stage["attempt_id"])["runtime_id"],
            "the refused recovery left the runtime with no identity")
        operations.close()


class ThePostStartLaunchDeliveryIsAdoptedAndNeverReauthored(
        CredentialRestartProvesTheLiveRuntimeFirst):
    """Review 2026-09-03T18:16:57Z [P1], twice over.

    The composition materialized a launch document whenever `launch.adopt`
    answered absence, INCLUDING after the start operation had committed. The
    launch owner says absence is ordinary only until a caller knows a runtime
    started, and that caller must then refuse; the pinned finding says
    contradictory or partial material refuses rather than being repaired.
    Authoring a fresh document under a container that may already hold the
    mount turns lost durable evidence into state that looks valid.

    AND THE ORDER WAS THE SECOND HALF OF IT. Credential recovery rereads and
    REGISTERS bearer bytes; a launch document that refused afterwards left
    those registrations live with nothing holding the delivery, and the next
    tick registered them again. The launch is proved first now, so this case
    also proves the recovery never ran at all.
    """

    def test_a_missing_launch_delivery_after_the_start_is_ended_and_named(self):
        """Re-review 2026-09-03T18:49:20Z [P1]: refusing was not enough.

        Ending the stage while the container the previous process created kept
        running, with nothing in this manager's rows saying which one it was,
        is an unmanaged live worker rather than a bounded failure. The ending
        is recorded first and the runtime is then reconciled, so the identity
        the ordinary destroy crossing needs exists.

        WHAT IS STILL NOT DONE, and is asserted so nobody has to guess: no
        replacement runtime, no launch bytes, and no bearer reread. The
        credential lifecycle record survives BECAUSE the container survives --
        removing a mount source out from under a live container is the one act
        the credential contract calls worse than leaving it.
        """
        engine, stage = self.published("launch-lost")
        attempt_id = stage["attempt_id"]
        root = os.path.join(os.path.realpath(self.config["launch_home"]),
                            attempt_id)
        self.assertTrue(single_worker.launch.discard(root),
                        "the fixture did not remove the launch delivery")
        job, control, operations = self.resumed("launch-lost-again", engine)
        asked = len(engine.vectors)
        report = reconcile(job, operations, now=fixtures.NOW)
        detail = report["started"][0]["detail"]
        self.assertEqual(detail["code"], "precondition")
        self.assertIn("launch delivery is absent", detail["message"])
        # THE ENGINE IS ASKED ONLY TO IDENTIFY. `ps` selects on this attempt's
        # whole label set and `inspect` reads the one it found; nothing else.
        self.assertEqual([one[1] for one in engine.vectors[asked:]],
                         ["ps", "inspect"])
        self.assertEqual(len(engine.starts), 1,
                         "a refused launch adoption started a replacement")
        # AND NO BYTES WERE REPAIRED.
        self.assertFalse(os.path.lexists(root),
                         "a replacement launch document was authored under a "
                         "container that may already hold the mount")
        # THE RUNTIME IS NAMED, which is what the ordinary destroy crossing
        # needs and what refusing alone left nobody holding.
        self.assertEqual(attempt_runtime_of(control, attempt_id)["runtime_id"],
                         engine.runtime_id)
        # AND ITS CREDENTIAL LIFECYCLE IS STILL THE LIVE ONE, unread.
        recorded = single_worker.credentials.CredentialHome(
            self.config["credential_home"]).read_state(attempt_id)
        self.assertIsNotNone(recorded)
        self.assertEqual(recorded["runtime_id"], engine.runtime_id)
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        self.assertIsNotNone(
            attempt_preparation_failure_of(control, attempt_id))
        self.assertEqual(self.launches, ["claimed"],
                         "the ended stage was asked again on a later tick")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        operations.close()

    def test_a_missing_launch_delivery_before_a_start_is_authored_once(self):
        """The other side of the same rule: before a start, absence is
        ordinary and this deployment is the manager that composes one."""
        engine = Engine()
        job, control = self.stores("launch-fresh")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "waiting")
        root = os.path.join(
            os.path.realpath(self.config["launch_home"]),
            held["job-a/implementation"]["attempt_id"])
        self.assertTrue(os.path.isdir(root))
        operations.close()


class AnEndingIsReachedEvenWhenTheAccountCannotBeCarried(PreparationCase):
    """Re-review 2026-09-03T18:49:20Z [P1]: §13 took the ending with it.

    `ContractRefusal` refuses to be CONSTRUCTED around a live bearer, and the
    manager's signature walks every durable member again before it writes. So
    a credential source whose own diagnostic quoted a registered value made
    this deployment raise `integrity/secret-leak` with no record behind it:
    the secret never reached a durable surface, and the accepted exceptional,
    non-retried ending was lost. The provider was then called again on every
    tick.
    """

    def test_a_source_refusal_quoting_a_live_bearer_still_ends_the_stage(self):
        engine = Engine()
        job, control = self.stores("unsayable")
        submit(job, self.submission)
        held_secret = "live-bearer-" + "4" * 40
        remember_secret(held_secret)
        self.addCleanup(lambda: [forget_secret(held_secret)
                                 for _ in range(3)
                                 if live_secret(held_secret)])
        calls = []

        def quoting(provider, reference):
            calls.append((provider, reference))
            raise SourceRefusal(f"the fixture source refused while holding "
                                f"{held_secret}")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=quoting, clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        held = self.serve(job, operations)
        stage = held["job-a/implementation"]
        self.assertEqual(stage["state"], "exceptional")
        self.assertEqual(calls, [("fixture", "fixture/one")],
                         "the source was asked again after a durable ending")
        self.assertEqual(self.launches, ["claimed"])
        self.assertEqual(engine.starts, [])
        # ONE SAFE RECORD, and the closed pair survives even though the text
        # could not.
        recorded = attempt_preparation_failure_of(control,
                                                  stage["attempt_id"])
        self.assertIsNotNone(recorded)
        self.assertEqual((recorded["failure"]["category"],
                          recorded["failure"]["code"]), ("policy", "denied"))
        self.assertIn("quoted a value", recorded["failure"]["message"])
        # AND THE BEARER IS IN NEITHER THE DURABLE NOR THE REPORTED OUTPUT.
        self.assertNotIn(held_secret, json.dumps(recorded))
        self.assertNotIn(held_secret, json.dumps(held))
        self.assertNotIn(held_secret,
                         json.dumps(reconcile(job, operations,
                                              now=fixtures.NOW)))
        self.assertNotIn(held_secret, json.dumps(engine.vectors))
        operations.close()


class ARealStartRefusalKeepsItsOwnAccount(PreparationCase):
    """Re-review 2026-09-03T18:49:20Z [P1]: the catcher overwrote the reason.

    `request_runtime_start` journals `runtime.start-failed`, settles the
    execution axis and re-raises. Sending that refusal on to the preparation
    writer got `already-terminal` back, and since status reports only the
    exceptional state, the sweep report -- the one place the low-level account
    appears -- carried this deployment's note about why it could not write a
    record instead of the engine's reason for refusing.
    """

    def test_an_engine_that_denies_the_start_reports_its_own_refusal(self):
        class Denying(Engine):
            def __call__(self, argv, *, seconds=None):
                if launching(argv):
                    self.vectors.append(list(argv))
                    return self.answer(status=1, stderr="engine denied start")
                return super().__call__(argv, seconds=seconds)

        engine = Denying()
        job, control = self.stores("denied-start")
        submit(job, self.submission)
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        report = None
        for _ in range(6):
            tick = reconcile(job, operations, now=fixtures.NOW)
            if tick["started"]:
                report = report or tick
        held = self.staged(status(job, operations, observed_at=fixtures.NOW))
        stage = held["job-a/implementation"]
        self.assertEqual(stage["state"], "exceptional")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(self.launches, ["claimed"], "the start was retried")
        # ONLY THE START-FAILURE RECORD, because a start act DID happen.
        recorded = attempt_start_failure_of(control, stage["attempt_id"])
        self.assertIsNotNone(recorded)
        self.assertIsNone(
            attempt_preparation_failure_of(control, stage["attempt_id"]))
        # AND THE REPORTED PAIR AND MESSAGE ARE THE ENGINE'S OWN.
        detail = report["started"][0]["detail"]
        self.assertEqual((detail["category"], detail["code"]),
                         (recorded["failure"]["category"],
                          recorded["failure"]["code"]))
        self.assertIn("engine denied start", detail["message"])
        self.assertNotIn("already-terminal", detail["message"])
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        operations.close()


class IdentificationIsOwedUntilItIsDone(
        CredentialRestartProvesTheLiveRuntimeFirst):
    """Re-review 2026-09-03T19:24:19Z [P1]: naming was a one-shot act.

    The preparation record makes the stage `exceptional`, and the control
    plane calls this deployment only for `claimed` stages -- so a naming step
    that ran AFTER the record had no second chance. A crash or an ordinary
    naming refusal in between orphaned the runtime permanently, and only the
    one branch that noticed absence reached the naming at all.

    Identification rides the same owner call now, BEFORE the record, so the
    obligation is discharged or the stage stays claimed for the next tick.
    """

    def test_a_crash_between_the_ending_and_the_naming_still_converges(self):
        """The reviewer's probe, driven as a regression.

        The process dies where the record used to be committed with the naming
        still to come. Because the naming now happens first, what a crash can
        leave is a stage still CLAIMED -- which the next tick drives through
        the same path again -- rather than an ended stage nobody will revisit.
        """
        engine, stage = self.published("naming-crash")
        attempt_id = stage["attempt_id"]
        root = os.path.join(os.path.realpath(self.config["launch_home"]),
                            attempt_id)
        self.assertTrue(single_worker.launch.discard(root))
        job, control = self.stores("naming-crash-again")
        stopped = []

        def dying(point):
            if point == "claimed":
                self.launches.append(point)
                if len(stopped) < 1:
                    stopped.append(point)
                    raise RuntimeError("fixture process stopped")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=dying)
        with self.assertRaisesRegex(RuntimeError, "process stopped"):
            reconcile(job, operations, now=fixtures.NOW)
        # NOTHING WAS LOST AND NOTHING WAS DECIDED: no ending, and the stage is
        # still the control plane's to drive.
        self.assertIsNone(attempt_preparation_failure_of(control, attempt_id))
        self.assertEqual(
            self.staged(status(job, operations,
                               observed_at=fixtures.NOW))
            ["job-a/implementation"]["state"], "claimed")
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        self.assertEqual(attempt_runtime_of(control, attempt_id)["runtime_id"],
                         engine.runtime_id,
                         "the runtime was never named")
        self.assertEqual(len(engine.starts), 1)
        self.assertFalse(os.path.lexists(root),
                         "a replacement launch document was authored")
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        operations.close()

    def test_contradictory_launch_material_is_named_and_never_repaired(self):
        """`adopt` REFUSES rather than answering absence for these bytes.

        That refusal used to bypass the naming entirely, because only the
        absence branch reached it. It is an ordinary preparation refusal now
        and takes the same ending as every other one.
        """
        engine, stage = self.published("launch-contradictory")
        attempt_id = stage["attempt_id"]
        root = os.path.join(os.path.realpath(self.config["launch_home"]),
                            attempt_id)
        place = os.path.join(root, "launch.json")
        os.chmod(root, 0o700)
        os.chmod(place, 0o600)
        with open(place, "wb") as writing:
            writing.write(b'{"schema": "baton.worker-launch/1"}')
        os.chmod(place, 0o444)
        os.chmod(root, 0o555)
        before = os.stat(place).st_size
        job, control, operations = self.resumed("launch-contradictory-again",
                                                engine)
        report = reconcile(job, operations, now=fixtures.NOW)
        self.assertEqual(report["started"][0]["outcome"], "refused")
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        self.assertIsNotNone(
            attempt_preparation_failure_of(control, attempt_id))
        self.assertEqual(attempt_runtime_of(control, attempt_id)["runtime_id"],
                         engine.runtime_id,
                         "a launch refusal ended the stage without naming the "
                         "runtime it left behind")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(os.stat(place).st_size, before,
                         "contradictory launch bytes were repaired")
        self.assertEqual(self.launches, ["claimed"])
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        operations.close()


class TheEndingAndTheNamingAreOneAct(
        CredentialRestartProvesTheLiveRuntimeFirst):
    """Re-review 2026-09-03T21:24:16Z [P1]: two durable acts, either order.

    Naming before recording was the last correction, and it moved the loss
    rather than closing it. A successful reconciliation attaches the runtime,
    which projects the stage `running` -- and the control plane calls this
    deployment for `claimed` stages alone, so a death in between left an
    ordinary running stage that no launch would ever follow and an exceptional
    ending nobody would ever write.

    There is no third ordering, because whichever act goes first is the one
    that removes the obligation. The engine is asked before anything is
    written and its answer is committed inside the transaction that writes the
    ending, so what a death can leave is all of it or none of it.
    """

    def dying_between(self):
        """The exact interval: the attachment has landed inside the act and
        the ending row does not exist yet."""
        def dying(**members):
            del members
            raise KeyboardInterrupt("fixture process stopped")

        return mock.patch.object(worker_documents,
                                 "runtime_preparation_failed", dying)

    def test_a_death_between_the_naming_and_the_ending_leaves_neither(self):
        """The reviewer's probe, driven at the interval it names.

        Nothing durable survives the interrupted act, which is what keeps the
        stage in the one state the control plane drives -- and the runtime is
        neither attached nor started a second time by the tick that resumes.
        """
        engine, stage = self.published("one-act")
        attempt_id = stage["attempt_id"]
        root = os.path.join(os.path.realpath(self.config["launch_home"]),
                            attempt_id)
        self.assertTrue(single_worker.launch.discard(root))
        job, control, operations = self.resumed("one-act-again", engine)
        with self.dying_between():
            with self.assertRaisesRegex(KeyboardInterrupt, "process stopped"):
                reconcile(job, operations, now=fixtures.NOW)
        # NEITHER FACT LANDED. The attachment is the half that used to survive
        # alone, and surviving alone is what lost the ending.
        interrupted = attempt_runtime_of(control, attempt_id)
        self.assertIsNone(interrupted["runtime_id"])
        self.assertEqual(interrupted["execution_runtime"], "start-requested")
        self.assertIsNone(attempt_preparation_failure_of(control, attempt_id))
        # SO THE STAGE IS STILL THE CONTROL PLANE'S TO DRIVE, which is the
        # whole property: `running` would never be asked again.
        self.assertEqual(
            self.staged(status(job, operations, observed_at=fixtures.NOW))
            ["job-a/implementation"]["state"], "claimed")
        asked = len(engine.vectors)
        held = self.serve(job, operations)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        recorded = attempt_preparation_failure_of(control, attempt_id)
        self.assertEqual(recorded["runtime_id"], engine.runtime_id)
        self.assertEqual(attempt_runtime_of(control, attempt_id)["runtime_id"],
                         engine.runtime_id, "the runtime was never named")
        self.assertEqual(len(engine.starts), 1)
        self.assertGreater(len(engine.vectors) - asked, 0,
                           "the resuming tick never asked the engine")
        self.assertFalse(os.path.lexists(root),
                         "a replacement launch document was authored")
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        operations.close()


class TheFailedStartEndingCommitsWithItsNaming(PreparationCase):
    """Re-review 2026-09-03T22:00:26Z [P1], through the Job projection.

    The sibling ending had the same shape the preparation ending was corrected
    for: `reconcile_runtime` attached the runtime as its own act, which
    projects the stage `running`, and the control plane calls this deployment
    for `claimed` stages alone -- so a death before `runtime.start-failed` was
    written made that record permanently unreachable.

    THE ENGINE THAT DENIES A START IT ALREADY MADE. `ARealStartRefusalKeeps
    ItsOwnAccount` drives a denial that creates nothing, so reconciliation
    finds nothing to attach and the dangerous interval never opens. This one
    leaves the container behind, which is the shape the ending has to name.
    """

    def denying(self):
        class CreatedThenDenied(Engine):
            """The launch leaves a RUNNING container behind AND reports failure.

            W275774: the denial is keyed on the instant the container starts
            running -- `run` for an ungoverned launch, `start` for a governed one --
            and the container is deliberately left running. That is the shape this
            case is about: a failure reported over a runtime that exists and
            executes, which is the dangerous interval the ending has to name.
            Denying the inert `create` instead would be a different case, the one
            `ItsOwnAccount` already drives, where nothing was created at all.
            """

            def __call__(self, argv, *, seconds=None):
                answer = super().__call__(argv, seconds=seconds)
                if running_now(argv):
                    self.running = True
                    return self.answer(status=1,
                                       stderr="engine denied start")
                return answer

        return CreatedThenDenied()

    def dying_between(self):
        def dying(**members):
            del members
            raise KeyboardInterrupt("fixture process stopped")

        return mock.patch.object(worker_documents, "runtime_start_failed",
                                 dying)

    def deployed(self, engine):
        """Named apart from the base helper: that one DRIVES a pipeline to
        `running`, and this one only opens the stores and the operations."""
        job, control = self.stores("denied-start-created")
        submit(job, self.submission)
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        return job, control, operations

    def roots(self, attempt_id):
        """The two manager-owned mount sources this attempt's container gets."""
        return (os.path.join(os.path.realpath(self.config["launch_home"]),
                             attempt_id),
                single_worker.credentials.CredentialHome(
                    self.config["credential_home"]).volatile_root(attempt_id))

    def test_a_denied_start_that_left_a_container_ends_and_names_it(self):
        """The ordinary case, so the crash case is a difference rather than a
        state nobody reached."""
        engine = self.denying()
        job, control, operations = self.deployed(engine)
        held = self.serve(job, operations)
        stage = held["job-a/implementation"]
        self.assertEqual(stage["state"], "exceptional")
        recorded = attempt_start_failure_of(control, stage["attempt_id"])
        self.assertIsNotNone(recorded)
        self.assertEqual(recorded["runtime_id"], engine.runtime_id)
        self.assertEqual(
            attempt_runtime_of(control, stage["attempt_id"])["runtime_id"],
            engine.runtime_id, "the container it left is unnamed")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(self.launches, ["claimed"], "the start was retried")
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        operations.close()

    def test_the_live_runtimes_mount_sources_are_left_where_they_are(self):
        """Re-review 2026-09-03T22:20:58Z [P1]: the deployment deleted them.

        `OciAdapter._undelivered` asks the engine, sees the runtime this start
        created and leaves both roots `unresolved` on purpose -- and it said so
        only in the refusal prose its caller composes, so the deployment's own
        unwind, still holding the pre-start `fresh`, removed exactly what that
        owner had refused to remove. The container was then left running over
        storage this manager had declared gone.

        THE BEARER STAYS REGISTERED, and that is the same rule rather than a
        second one: `CredentialHome.tear_down` releases the registry only
        after the bytes are proved gone, so a root that may still be mounted
        keeps its registration too.
        """
        engine = self.denying()
        job, control, operations = self.deployed(engine)
        held = self.serve(job, operations)
        stage = held["job-a/implementation"]
        launch_root, credential_root = self.roots(stage["attempt_id"])
        self.assertEqual(stage["state"], "exceptional")
        # THE ENGINE WAS GIVEN BOTH, so both are what the container holds.
        mounted = sorted(one["Source"] for one in engine.mounts)
        self.assertIn(credential_root + "/api", mounted)
        self.assertIn(launch_root + "/launch.json", mounted)
        self.assertTrue(os.path.lexists(launch_root),
                        "the live runtime's launch document was removed")
        self.assertTrue(os.path.lexists(credential_root),
                        "the live runtime's credential root was removed")
        self.assertTrue(live_secret(self.secret),
                        "the registry was released over bytes still present")
        # AND THE STAGE IS STILL ENDED AND STILL NOT RETRIED: what changed is
        # what was removed, not what was reported.
        self.assertEqual(self.launches, ["claimed"])
        self.assertEqual(len(engine.starts), 1)
        operations.close()

    def test_a_refusal_before_that_boundary_still_ends_both_deliveries(self):
        """The other side of the same rule, and why `fresh` is still it.

        No runtime owner reached the settlement here, so nobody decided and
        both mounts are this composition's to end -- exactly as they were
        before the adapter's answer was carried across. An adapter that never
        settled anything must not be read as one that decided to keep them.
        """
        engine = Engine()
        job, control = self.stores("refused-before-start")
        submit(job, self.submission)
        composed = []

        def refusing(point):
            if point == "claimed":
                self.launches.append(point)
            if point == "credential":
                composed.append(point)
                raise ContractRefusal(
                    "refused", "precondition",
                    "the fixture refuses after the composition")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=refusing)
        held = self.serve(job, operations)
        stage = held["job-a/implementation"]
        launch_root, credential_root = self.roots(stage["attempt_id"])
        self.assertEqual(composed, ["credential"],
                         "the composition never reached the refusal")
        self.assertEqual(stage["state"], "exceptional")
        self.assertEqual(engine.starts, [], "a runtime was started")
        self.assertFalse(os.path.lexists(launch_root),
                         "a launch document no runtime received was left")
        self.assertFalse(os.path.lexists(credential_root),
                         "a credential root no runtime received was left")
        self.assertFalse(live_secret(self.secret),
                         "the bearer is still registered")
        self.assertIsNotNone(
            attempt_preparation_failure_of(control, stage["attempt_id"]))
        operations.close()

    def test_a_death_between_the_naming_and_the_record_leaves_neither(self):
        """The exact interval, interrupted.

        WHAT THIS PROVES IS THAT NOTHING IS LOST OR DUPLICATED, and it is
        worth being exact about what it does NOT prove. The engine's account
        of why the start failed is not recoverable across this death: the only
        durable trace of it would have been the record, and a resumed manager
        can no more distinguish "the start reported an error and left a
        container" from "the start succeeded" than it could if the process had
        died one statement earlier. What atomicity is for is that the stage
        never rests in a state the control plane will not revisit -- so the
        next process re-derives from canonical state and the engine, and
        reaches whatever those two say, rather than an ordinary running
        success no launch would ever follow with an ending nobody wrote.
        """
        engine = self.denying()
        job, control, operations = self.deployed(engine)
        with self.dying_between():
            with self.assertRaisesRegex(KeyboardInterrupt, "process stopped"):
                for _ in range(6):
                    reconcile(job, operations, now=fixtures.NOW)
        stage = self.staged(status(job, operations,
                                   observed_at=fixtures.NOW))[
                                       "job-a/implementation"]
        attempt_id = stage["attempt_id"]
        # NEITHER FACT LANDED, so the stage is still the control plane's.
        self.assertIsNone(attempt_start_failure_of(control, attempt_id))
        interrupted = attempt_runtime_of(control, attempt_id)
        self.assertIsNone(interrupted["runtime_id"])
        self.assertEqual(interrupted["execution_runtime"], "start-requested")
        self.assertEqual(stage["state"], "claimed")
        held = self.serve(job, operations)
        # AND THE RESUMED PROCESS NEITHER STARTS A SECOND CONTAINER NOR
        # LEAVES THE ONE THAT EXISTS UNNAMED.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(attempt_runtime_of(control, attempt_id)["runtime_id"],
                         engine.runtime_id)
        # AND IT REACHES WHAT CANONICAL STATE AND THE ENGINE ACTUALLY SAY: a
        # container carrying these labels exists and observes as running, so
        # `running` is the truthful reading. It is asserted exactly rather
        # than negatively, because a future change to what a resumed process
        # concludes here should be visible as a change rather than pass a
        # loose check.
        self.assertEqual(held["job-a/implementation"]["state"], "waiting")
        self.assertNotIn(self.secret, json.dumps(engine.vectors))
        self.assertEqual(held["job-b/implementation"]["state"], "queued")
        operations.close()


class WhatNoRuntimeReceivedIsThisCompositionsToEnd(PreparationCase):
    """Re-review 2026-09-03T19:24:19Z [P1]: authorship was the wrong boundary.

    A launch document published by a process that crashed before its
    credential is ADOPTED by the next one, so the invocation that ends the
    stage did not author it -- and the previous rule then left its root
    present forever, with no runtime that could ever have mounted it. What
    decides is the state the manager already proved: `not-started` says no
    runtime received either delivery.
    """

    def test_a_launch_adopted_after_a_crash_is_disposed_of_by_the_ending(self):
        engine = Engine()
        job, control = self.stores("launch-adopted")
        submit(job, self.submission)
        crashed = []

        def after_launch(point):
            if point == "claimed":
                self.launches.append(point)
            if point == "credential" and not crashed:
                crashed.append(point)
                raise RuntimeError("fixture process stopped")

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW, checkpoint=after_launch)
        with self.assertRaisesRegex(RuntimeError, "process stopped"):
            for _ in range(6):
                reconcile(job, operations, now=fixtures.NOW)
        attempt_id = self.staged(status(job, operations,
                                        observed_at=fixtures.NOW))[
            "job-a/implementation"]["attempt_id"]
        root = os.path.join(os.path.realpath(self.config["launch_home"]),
                            attempt_id)
        self.assertTrue(os.path.isdir(root),
                        "the fixture did not publish a launch delivery")
        operations.close()
        job.close()
        control.close()

        resumed_job, resumed_control = self.stores("launch-adopted-again")
        calls = []

        def unavailable(provider, reference):
            calls.append((provider, reference))
            raise SourceRefusal("the fixture source is unavailable")

        resumed = single_worker.operations_from(
            self.config, resumed_job, resumed_control, engine_run=engine,
            credential_provider=unavailable, clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        held = self.serve(resumed_job, resumed)
        self.assertEqual(held["job-a/implementation"]["state"], "exceptional")
        self.assertEqual(calls, [("fixture", "fixture/one")])
        self.assertEqual(engine.starts, [])
        self.assertFalse(os.path.lexists(root),
                         "a launch delivery no runtime received was left on "
                         "the host by a terminal stage")
        resumed.close()


class AnUntrustedBearerIsNeverAllowedToWedgeTheManager(PreparationCase):
    """Re-review 2026-09-03T19:24:19Z [P1]: the provider's answer is untrusted.

    A bearer equal to this attempt's own durable identity is registered live
    by `materialize`, and every later §13 walk over a row containing that
    identity then refuses -- so the manager could not read its own attempt,
    settle the delivery, record an ending or report one, and the credential
    and launch roots stayed. The delivery's owner stays live across every
    pre-start boundary that follows materialization, so the colliding value is
    released -- after its bytes are proved gone -- before durable state is read
    again.
    """

    def test_a_bearer_equal_to_the_attempt_id_still_ends_the_stage(self):
        engine = Engine()
        job, control = self.stores("colliding-bearer")
        submit(job, self.submission)
        seen = []

        def collide(provider, reference):
            attempt_id = self.staged(status(job, operations,
                                            observed_at=fixtures.NOW))[
                "job-a/implementation"]["attempt_id"]
            seen.append(attempt_id)
            return attempt_id

        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=collide, clock=lambda: fixtures.NOW,
            checkpoint=lambda point: self.launches.append(point)
            if point == "claimed" else None)
        held = self.serve(job, operations)
        stage = held["job-a/implementation"]
        self.assertEqual(len(seen), 1, "the provider was asked again")
        self.assertEqual(self.launches, ["claimed"], "the stage was retried")
        self.assertEqual(stage["state"], "exceptional")
        self.assertEqual(engine.vectors, [], "the engine was reached")
        # THE COLLIDING VALUE IS RELEASED, and only after its bytes were
        # proved gone -- so both roots are settled and nothing holds it live.
        self.assertFalse(live_secret(seen[0]),
                         "the colliding bearer is still registered")
        self.assertFalse(os.path.lexists(os.path.join(
            os.path.realpath(self.config["launch_home"]), seen[0])))
        self.assertIsNone(single_worker.credentials.CredentialHome(
            self.config["credential_home"]).read_state(seen[0]))
        # ONE SAFE ENDING, READ AND REPORTED.
        self.assertIsNotNone(
            attempt_preparation_failure_of(control, seen[0]))
        operations.close()


if __name__ == "__main__":
    unittest.main()


class AFaultedTerminalSurvivesTheContainerThatWroteIt(SingleWorkerCase):
    """W85500: the fault/exit race, through the real owners.

    THE MEASURED DEFECT. The W71917 run6 worker wrote a correlated terminal
    with `ending: faulted` and `fault_code: output`, then its container exited
    with code 1. More than a minute later the live persistent Job Manager still
    projected the stage as `starting`, the runtime as `running`, and
    `exchange: null` -- while the engine independently reported that exact
    runtime exited.

    WHAT THESE CASES REPRODUCE, EXACTLY. The race and not the code. The
    terminal here is a real one written by the real `baton_worker` over the
    real exchange, but its `Silent` agent FAILS ITS TURN, so the code the
    worker correlates is `fault_code: agent` and every assertion below names
    that. Producing run6's `output` needs a broken completion-envelope
    publication rather than a failing provider -- a different defect, and not
    this Work's; `Silent`'s own docstring carries the reasoning. Every member
    of `exchange.FAULT_CODES` reaches the projection identically, because it
    is the terminal's `ending` that maps to `exceptional` and the code travels
    beside it, so the defect above is reproduced by a correlated FAULTED
    terminal on disk with the container gone and nothing having asked.

    Nothing about the terminal is hand-written, so a change to the worker's own
    correlation rules fails here rather than being agreed with by a fixture.
    """

    class Exiting(Engine):
        """A container that stops on its own, as a faulted worker's does.

        `TheAnsweredEndingRunsThroughTheRealOwners.quiescing` models a runtime
        the MANAGER stopped. This one exits without being asked, which is the
        whole race: nothing ordered it, so nothing in the manager had a reason
        to look.
        """

        def __init__(self):
            super().__init__()
            self.exited = False
            # W85500 re-review 2026-09-04T19:08:40Z [P1]: what the ENGINE
            # BOUNDARY itself raises, so a case can drive the real
            # `_SingleWorker.refresh_runtime` translation rather than a
            # stand-in for it. `None` is every other case's ordinary engine.
            self.raising = None
            # W85500 re-review 2026-09-04T21:52:30Z [P2]: what a DEAD DAEMON
            # answers, which is an ordinary non-zero result and not a raised
            # exception. Set to a whole answer document so the case owns the
            # exact shape the CLI produces.
            self.refusing = None

        def __call__(self, argv, *, seconds=None):
            if self.raising is not None:
                raise self.raising
            if self.refusing is not None:
                # RECORDED AND ANSWERED, because a refused vector is one the
                # engine was still asked for; only the answer differs.
                self.vectors.append(list(argv))
                return dict(self.refusing)
            answer = super().__call__(argv, seconds=seconds)
            if argv[1] == "inspect" and self.exited:
                body = json.loads(answer["stdout"])
                body["State"]["Running"] = False
                answer = Engine.answer(stdout=json.dumps(body))
            return answer

    class Silent:
        """A provider substitute whose turn fails, as run6's effectively did.

        THE FAULT IS THE WORKER'S OWN, not this class's. `baton_worker` turns
        an agent exception into a correlated faulted terminal carrying
        `fault_code: agent` and nothing else -- no traceback, no message, no
        type name -- and returns 1. So what these cases drive is the real
        correlation path over the real exchange.

        WHY NOT run6's EXACT `output` CODE. That one is raised when a
        well-formed `work` answer cannot name the completion envelope, and the
        worker PUBLISHES that envelope itself from the answer -- so producing
        it needs a broken publication rather than a failing provider, which is
        a different defect and not this Work's. Every member of
        `exchange.FAULT_CODES` reaches the projection identically: the
        terminal's `ending` is what maps to `exceptional`, and the code
        travels beside it. The cases below assert the code is in that closed
        vocabulary as well as naming this one, so a build that widened the set
        fails here.
        """

        def __init__(self):
            self.turns = 0

        def consider(self, seen, request):
            return {"decision": "decline", "contract_digest": "",
                    "reason": "this fixture agent is not asked to consent"}

        def work(self, seen, declared):
            del seen, declared
            self.turns += 1
            raise RuntimeError("the fixture provider could not finish")

    def faulted(self, incarnation):
        """Drive the pipeline to a real correlated faulted terminal.

        Returns everything a later sweep or a fresh incarnation needs, plus
        the agent, so a restart can prove the provider was not entered twice.
        """
        import baton_worker

        engine = self.Exiting()
        job, control = self.stores(incarnation)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        stage = self.commanded(job, operations)["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        home = os.path.join(self.storage, attempt_id)
        delivered = single_worker.launch.adopt(
            self.config["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=self.config["launch_contract"], role="implementation",
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            # W156162, scheduled in PLAN by review 2026-09-13T02:10:47Z: this
            # helper adopts the delivery ITSELF, so it must supply the same Job
            # context the deployment composed -- adoption compares canonical
            # bytes. Setup only: no assertion and no expected outcome changes.
            job_execution=single_worker.job_execution_reader(job)(
                job_id=stage["job_id"], attempt_id=attempt_id,
                runtime_input_digest=self.config["input_manifest"][
                    "manifest_digest"],
                runtime_policy_digest=self.config["policy_digest"]),
            workspace_group=single_worker.configured_workspace_group(control))
        for name, value in (("INPUT_ROOT", os.path.join(home, "inputs")),
                            ("OUTPUT_ROOT", os.path.join(home, "workspace"))):
            held = getattr(baton_worker, name)
            setattr(baton_worker, name, value)
            self.addCleanup(setattr, baton_worker, name, held)
        agent = self.Silent()
        # THE WORKER ANSWERS NON-ZERO, which is what a faulted turn does.
        self.assertEqual(
            baton_worker.serve_exchange(
                agent, delivered.document, delivered.document["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root), 1)
        # AND THEN THE CONTAINER GOES AWAY, between sweeps and unasked.
        engine.exited = True
        return job, control, operations, engine, agent, attempt_id, delivered

    def projected(self, job, operations):
        return status(job, operations,
                      observed_at=fixtures.NOW)["jobs"][0]["stages"][0]

    def test_the_next_sweep_reports_exceptional_and_a_quiescent_runtime(self):
        """BOTH AXES, FROM ONE SWEEP, and neither derived from the other."""
        job, _control, operations, engine, _agent, _attempt, _held = \
            self.faulted("fault-1")
        before = len(engine.starts)
        report = sweep(job, operations, now=fixtures.NOW)
        held = self.projected(job, operations)
        self.assertEqual(held["state"], "exceptional")
        # THE EXCHANGE AXIS: the worker's own correlated terminal, read from
        # the durable file rather than from a live container.
        self.assertEqual(held["exchange"]["state"], "faulted")
        self.assertEqual(held["exchange"]["terminal"]["ending"], "faulted")
        self.assertEqual(held["exchange"]["terminal"]["fault_code"], "agent")
        self.assertIn(held["exchange"]["terminal"]["fault_code"],
                      single_worker.exchange.FAULT_CODES)
        # THE RUNTIME AXIS: the exact container, observed as gone.
        self.assertEqual(held["runtime"]["execution_runtime"], "quiescent")
        refreshed = {one["attempt_id"]: one for one in report["refreshed"]}
        self.assertEqual(refreshed[held["attempt_id"]]["state"], "quiescent")
        # AND NOTHING WAS STARTED TO FIND THAT OUT.
        self.assertEqual(len(engine.starts), before)
        operations.close()

    def unreachable(self, incarnation, raising):
        """One sweep whose engine cannot be asked, through the real seam."""
        job, control, operations, engine, _agent, _attempt, _held = \
            self.faulted(incarnation)
        before = self.projected(job, operations)["runtime"][
            "execution_runtime"]
        engine.raising = raising
        report = sweep(job, operations, now=fixtures.NOW)
        engine.raising = None
        held = self.projected(job, operations)
        operations.close()
        return report, held, before

    def test_an_engine_that_cannot_be_asked_is_uncertain_not_gone(self):
        """W85500 re-review 2026-09-04T19:08:40Z [P1], at the real seam.

        The manager used to catch `OSError` itself and then catch `Exception`
        after it. It is the DEPLOYMENT that knows which of its own failures
        mean the engine could not be reached, so it names them: this
        composition's runner is `subprocess.run`, and an invocation that could
        not be made at all -- a missing engine binary -- arrives from it as
        `OSError`. A dead daemon is NOT this shape, which
        `test_a_dead_daemon_is_a_refusal_and_not_an_unreachable_engine`
        measures.

        NOTHING IS RECORDED FROM AN UNASKED QUESTION. The runtime axis keeps
        exactly what it last knew, which is the honest difference between
        "gone" and "nobody could ask" -- and the durable terminal, which lives
        on a different axis entirely, is still read and still projected.
        """
        report, held, before = self.unreachable(
            "fault-unreachable", OSError("no such engine binary"))
        refreshed = {one["attempt_id"]: one for one in report["refreshed"]}
        self.assertEqual(refreshed[held["attempt_id"]]["state"], None)
        self.assertEqual(refreshed[held["attempt_id"]]["detail"],
                         {"category": "uncertain",
                          "code": "engine-unreachable", "error": "OSError"})
        # THE ENGINE'S OWN PROSE IS NOWHERE IN THE REPORT.
        self.assertNotIn("no such engine binary", json.dumps(report))
        # THE RUNTIME AXIS IS UNTOUCHED, not quiesced and not destroyed.
        self.assertEqual(held["runtime"]["execution_runtime"], before)
        # AND THE OTHER AXIS WAS READ ANYWAY.
        self.assertEqual(held["exchange"]["state"], "faulted")
        self.assertEqual(held["exchange"]["terminal"]["fault_code"], "agent")
        self.assertEqual(held["state"], "exceptional")

    def test_a_runner_that_timed_out_is_the_same_unasked_question(self):
        """The type that used to reach the blanket branch.

        `subprocess.TimeoutExpired` is not an `OSError`, and it is the same
        operational fact: the question could not be put. Under the previous
        candidate it was reported as an implementation `fault` -- and on any
        tick but the last one of a serving run, reported nowhere at all.
        """
        report, held, _before = self.unreachable(
            "fault-timeout",
            subprocess.TimeoutExpired(["docker", "inspect"], 600))
        refreshed = {one["attempt_id"]: one for one in report["refreshed"]}
        self.assertEqual(refreshed[held["attempt_id"]]["detail"],
                         {"category": "uncertain",
                          "code": "engine-unreachable",
                          "error": "TimeoutExpired"})
        self.assertEqual(held["state"], "exceptional")

    def test_a_dead_daemon_is_a_refusal_and_not_an_unreachable_engine(self):
        """Review 2026-09-04T21:52:30Z [P2]: WHAT THIS BOUNDARY REALLY SEES.

        The operator documentation and the source comment both promised that a
        dead daemon socket arrives as `OSError` and is therefore reported
        `uncertain / engine-unreachable`. It does not. The CLI runs perfectly
        well and answers NON-ZERO, so `OciAdapter.list` refuses the listing
        `policy / denied`, and that is the category and code the stage carries.

        The accepted containment boundary is untouched by that -- the refusal
        stays on this stage, nothing is recorded on the runtime axis, and the
        durable terminal is still read and still projected -- so what this
        pins is the PROMISE rather than the behaviour. Telling an unreachable
        daemon apart from a genuine policy or integrity refusal needs a typed
        adapter failure this build does not have, and a later build that adds
        one has to change this case to say so.
        """
        job, _control, operations, engine, _agent, _attempt, _held = \
            self.faulted("fault-dead-daemon")
        before = self.projected(job, operations)["runtime"][
            "execution_runtime"]
        engine.refusing = Engine.answer(
            status=1, stderr="Cannot connect to the Docker daemon at "
                             "unix:///var/run/docker.sock. Is the docker "
                             "daemon running?\n")
        report = sweep(job, operations, now=fixtures.NOW)
        engine.refusing = None
        held = self.projected(job, operations)
        operations.close()
        refreshed = {one["attempt_id"]: one for one in report["refreshed"]}
        self.assertEqual(refreshed[held["attempt_id"]]["state"], None)
        self.assertEqual(refreshed[held["attempt_id"]]["detail"],
                         {"category": "policy", "code": "denied"})
        # THE DAEMON'S OWN PROSE IS NOWHERE IN THE REPORT.
        self.assertNotIn("docker daemon", json.dumps(report))
        # THE RUNTIME AXIS IS UNTOUCHED, and the other axis was read anyway.
        self.assertEqual(held["runtime"]["execution_runtime"], before)
        self.assertEqual(held["exchange"]["state"], "faulted")
        self.assertEqual(held["exchange"]["terminal"]["fault_code"], "agent")
        self.assertEqual(held["state"], "exceptional")

    def test_an_arbitrary_defect_in_this_composition_escapes(self):
        """AND THE OTHER HALF OF THE SAME RULE.

        Only what this deployment NAMED is translated. A defect in its own
        code is not an unreachable engine, must not be dressed as one, and
        must not become per-tick report data that `serve` discards on the next
        successful tick. It escapes to whoever is running the loop.
        """
        job, _control, operations, engine, _agent, _attempt, _held = \
            self.faulted("fault-defect")
        engine.raising = RuntimeError("this composition has a defect")
        with self.assertRaises(RuntimeError) as raised:
            sweep(job, operations, now=fixtures.NOW)
        self.assertIn("this composition has a defect", str(raised.exception))
        engine.raising = None
        operations.close()

    def test_the_fault_alone_authorizes_no_act_at_all(self):
        """The acceptance's negative half, read from the OWNERS' own records.

        A faulted terminal is not a successful answer. No freeze, no intake, no
        retention, no Authority pass, no cleanup, no replacement attempt, no
        second command and no second provider turn follow from it.
        """
        from baton_v12.worker_manager import (intake_receipt_of,
                                              retentions_of)

        job, control, operations, engine, agent, attempt_id, _held = \
            self.faulted("fault-2")
        commands = [one for one in engine.vectors if one[1] == "run"]
        report = sweep(job, operations, now=fixtures.NOW)
        self.assertEqual(report["spoken"], [])
        self.assertEqual(report["acts"], [])
        self.assertIsNone(intake_receipt_of(control, attempt_id))
        self.assertFalse(retentions_of(control, attempt_id))
        self.assertEqual(agent.turns, 1)
        self.assertEqual([one for one in engine.vectors if one[1] == "run"],
                         commands)
        self.assertEqual(self.projected(job, operations)["episode"], 1)
        operations.close()

    def test_repeated_sweeps_replay_the_same_facts_and_do_nothing(self):
        job, _control, operations, engine, agent, _attempt, _held = \
            self.faulted("fault-3")
        first = self.projected(job, operations)
        sweep(job, operations, now=fixtures.NOW)
        after = self.projected(job, operations)
        sweep(job, operations, now=fixtures.NOW)
        again = self.projected(job, operations)
        self.assertEqual(after, again)
        self.assertEqual(again["state"], "exceptional")
        self.assertEqual(agent.turns, 1)
        self.assertEqual(len(engine.starts), 1)
        del first
        operations.close()

    def test_a_fresh_incarnation_reconstructs_the_same_observation(self):
        """THE RESTART CONTROL. The manager's lifetime is not the container's,
        and the terminal is a file: a process that saw none of this reaches
        exactly the same answer by rereading exactly the same bytes."""
        job, control, operations, engine, agent, attempt_id, held = \
            self.faulted("fault-4")
        sweep(job, operations, now=fixtures.NOW)
        was = self.projected(job, operations)
        operations.close()
        job.close()
        control.close()

        resumed_job, resumed_control = self.stores("fault-4-resumed")
        resumed = self.operations(resumed_job, resumed_control, engine)
        report = reconcile(resumed_job, resumed, now=fixtures.NOW)
        now = status(resumed_job, resumed,
                     observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(now["state"], "exceptional")
        self.assertEqual(now["exchange"]["terminal"]["fault_code"], "agent")
        self.assertEqual(now["runtime"]["execution_runtime"], "quiescent")
        self.assertEqual(now["attempt_id"], was["attempt_id"])
        self.assertEqual(now["episode"], was["episode"])
        # NOTHING WAS RE-DONE: no new runtime, no second provider turn, no act.
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(agent.turns, 1)
        self.assertEqual(report["spoken"], [])
        self.assertEqual(report["acts"], [])
        # AND THE RETAINED EVIDENCE IS STILL THERE, unmodified.
        self.assertTrue(os.path.lexists(os.path.join(
            held.exchange.event_root,
            single_worker.exchange.TERMINAL_DOCUMENT)))
        del attempt_id
        resumed.close()

    def test_the_observation_only_status_surface_reports_the_same_terminal(
            self):
        """PLAN ITEM 5, WHERE A CLAIM EXISTS.

        The tool's own cases prove the operand is resolved, asked and released;
        this proves the thing the operator actually wanted -- a faulted
        terminal appearing in a status document produced with NO serving
        deployment, no Authority and no engine.
        """
        from baton_v12.job_manager import status as project
        from tools.job_manager import _Observing

        job, control, operations, _engine, _agent, _attempt, _held = \
            self.faulted("fault-5")
        sweep(job, operations, now=fixtures.NOW)
        operations.close()

        observed = single_worker.observation_from(self.config, job, control)
        held = project(job, _Observing(control, observed),
                       observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(held["exchange"]["state"], "faulted")
        self.assertEqual(held["exchange"]["terminal"]["fault_code"], "agent")
        self.assertEqual(held["state"], "exceptional")
        # AND THE RUNTIME AXIS IS THE SERVING LOOP'S, reported exactly as the
        # store holds it rather than refreshed by this read.
        self.assertEqual(held["runtime"]["execution_runtime"], "quiescent")

    def test_a_real_observing_status_run_mutates_no_durable_state(self):
        """W85500 review 2026-09-04T14-27-54Z [P1]: BEHAVIOUR, not capability.

        The other cases prove the surface HOLDS no act and that its
        `refresh_runtime` answers `None`. Neither of them would notice a
        durable write arriving by some other route, and "no Authority acts AND
        no durable mutation" is the accepted distinction from serving
        operations.

        So this runs the REAL `tools.job_manager status --observe` command --
        the operator's actual invocation, through `main`, with both stores
        closed first so nothing this process holds can mask a write -- and
        compares every byte of every durable file this deployment owns before
        and after. The terminal must still come back, or the run proved
        nothing: an observation that returned nothing would also mutate
        nothing.
        """
        import hashlib
        import io as streams

        from tools.job_manager import main as tool

        job, control, operations, _engine, _agent, _attempt, _held = \
            self.faulted("observe-durable")
        sweep(job, operations, now=fixtures.NOW)
        operations.close()
        job.close()
        control.close()

        def durable():
            """Every durable byte this deployment owns, by path.

            The two stores AND their write-ahead siblings, plus the launch and
            exchange trees, because a write that landed only in a `-wal` file
            is still a write.
            """
            found = {}
            for root in (self.root,):
                for base, _directories, files in os.walk(root):
                    for name in files:
                        place = os.path.join(base, name)
                        with open(place, "rb") as reading:
                            found[os.path.relpath(place, root)] = \
                                hashlib.sha256(reading.read()).hexdigest()
            return found

        # THE OPERATOR'S OWN INVOCATION, which resolves its configuration from
        # the environment exactly as the documented command does. Written
        # OUTSIDE the tree this case digests, so staging it is not itself the
        # change being measured.
        #
        # W71917: A SECOND DISK-BACKED DIRECTORY, named rather than derived.
        # This used to reach the parent of a `TemporaryDirectory` this case no
        # longer owns; the root it digests is now allocated by
        # `disk_roots.disk_backed_under`, and pointing at ITS parent would
        # write into whichever shared directory that helper chose. A separate
        # allocation is outside the digested root by construction and goes
        # away with the case.
        place = os.path.join(disk_roots.disk_backed_under(self),
                             "observe-config.json")
        self.assertFalse(os.path.abspath(place).startswith(
            os.path.abspath(self.root) + os.sep),
            "the configuration must be written outside the digested root")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(self.config, writing)

        before = durable()
        # A SNAPSHOT OF NOTHING WOULD COMPARE EQUAL TO A SNAPSHOT OF NOTHING.
        # The stores and the launch tree are all under this root, so an empty
        # inventory here means the walk is looking in the wrong place.
        self.assertGreater(len(before), 10, sorted(before))
        self.assertTrue(any(one.endswith("jobs.sqlite3") for one in before),
                        sorted(before))
        self.assertTrue(any(one.endswith("control.sqlite3") for one in before),
                        sorted(before))
        stream = streams.StringIO()
        with mock.patch.dict(os.environ,
                             {single_worker.CONFIG_ENV: place}, clear=False):
            code = tool(["--store", self.job_path,
                         "--authority-uuid", AUTHORITY_UUID,
                         "--incarnation", "observing-1",
                         "status", "--control", self.control_path,
                         "--observe",
                         "tools.single_worker:observing_factory"],
                        clock=lambda: fixtures.NOW, stream=stream)
        after = durable()

        self.assertEqual(code, 0)
        answered = json.loads(stream.getvalue())
        stage = answered["jobs"][0]["stages"][0]
        # THE TERMINAL CAME BACK, or this measured an empty run.
        self.assertEqual(stage["exchange"]["state"], "faulted")
        self.assertEqual(stage["exchange"]["terminal"]["fault_code"], "agent")
        self.assertEqual(stage["state"], "exceptional")
        # AND NOTHING THIS DEPLOYMENT OWNS CHANGED, byte for byte.
        self.assertEqual(sorted(after), sorted(before),
                         "an observing status run added or removed a durable "
                         "file")
        altered = sorted(one for one in before
                         if before[one] != after.get(one))
        self.assertEqual(altered, [],
                         f"an observing status run rewrote durable state: "
                         f"{altered}")

    def test_the_observation_only_surface_opens_no_authority_and_no_engine(
            self):
        """What it is NOT, asserted rather than promised."""
        job, control, operations, _engine, _agent, _a, _h = \
            self.faulted("fault-6")
        operations.close()
        observed = single_worker.observation_from(self.config, job, control)
        for act in ("admit", "claim", "launch", "dispatch", "conclude",
                    "start", "delivered", "ending", "command",
                    "refresh_runtime"):
            self.assertFalse(hasattr(observed, act), act)
        self.assertTrue(hasattr(observed, "observe_exchange"))


class TheAnsweredEndingRunsThroughTheRealOwners(SingleWorkerCase):
    """W81857 review 2026-09-04T03-43-45Z [P1]: the ending, not a fake of it.

    Every other case in this file stops where the container would start doing
    work. This one runs the REAL in-image program over the REAL exchange this
    deployment composed, and then drives `_SingleWorker.ending` through the
    Worker Manager's own quiescence, disposition, freeze, intake, retention,
    Authority pass and cleanup operations. Only the engine boundary is the
    recording fixture, as everywhere else here.

    IT EXISTS BECAUSE THE TERMINAL'S DIGEST WAS NEVER ENFORCED. The member was
    carried and never compared, so an `answered` terminal naming any envelope
    drove the whole success path whenever a separately valid `output.json`
    happened to exist. Writing the comparison was not enough either: the first
    correction compared the terminal against the FROZEN RESULT's own
    `manifest_digest`, which is the manager's result manifest rather than the
    worker's completion envelope, and would have refused every honest attempt.
    A case that ran only fakes would have agreed with that mistake.
    """

    def quiescing(self):
        """An engine whose runtime stops running once it is told to stop.

        `adapter.stop` orders and then OBSERVES, and the freeze takes a
        positively quiescent runtime, so a fixture that reported `Running`
        forever could never reach the ending at all.
        """
        original = Engine.__call__

        def call(engine, argv, *, seconds=None):
            if argv[1] == "stop":
                engine.stopped = True
            answer = original(engine, argv, seconds=seconds)
            if argv[1] == "inspect" and getattr(engine, "stopped", False):
                body = json.loads(answer["stdout"])
                body["State"]["Running"] = False
                answer = Engine.answer(stdout=json.dumps(body))
            return answer

        Engine.__call__ = call
        self.addCleanup(setattr, Engine, "__call__", original)
        return Engine()

    def worked(self, incarnation):
        """Drive the pipeline to a real answered terminal.

        The worker is `baton_worker` itself, entered at `serve_exchange` with
        the launch document this deployment wrote, over the command and event
        namespaces this deployment mounted. Nothing about the protocol is
        simulated; what is substituted is the provider, exactly as the
        reference image's own fixture agent substitutes it.
        """
        import baton_worker
        import scripted_agent

        engine = self.quiescing()
        job, control = self.stores(incarnation)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        stage = self.commanded(job, operations)["jobs"][0]["stages"][0]
        attempt_id = stage["attempt_id"]
        home = os.path.join(self.storage, attempt_id)
        delivered = single_worker.launch.adopt(
            self.config["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=self.config["launch_contract"], role="implementation",
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            # W156162, scheduled in PLAN by review 2026-09-13T02:10:47Z: this
            # helper adopts the delivery ITSELF, so it must supply the same Job
            # context the deployment composed -- adoption compares canonical
            # bytes. Setup only: no assertion and no expected outcome changes.
            job_execution=single_worker.job_execution_reader(job)(
                job_id=stage["job_id"], attempt_id=attempt_id,
                runtime_input_digest=self.config["input_manifest"][
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
        return job, control, operations, attempt_id, delivered.exchange

    def spoke(self, report):
        return [(one["act"], one["outcome"]) for one in report["spoken"]]

    def test_a_matching_terminal_drives_the_whole_ending(self):
        from baton_v12.worker_manager import intake_receipt_of, retentions_of

        job, control, operations, attempt_id, held = self.worked("ending-ok")
        report = sweep(job, operations, now=fixtures.NOW)
        self.assertEqual(self.spoke(report), [("conclude", "performed")])
        detail = report["spoken"][0]["detail"]
        self.assertEqual(detail["disposition"], "completed")
        self.assertEqual(detail["retention"], "retain")
        self.assertEqual(detail["review_route"], self.config["review_route"])
        # EVERY OWNER ACTUALLY RAN, read back from its own durable record
        # rather than from what the composition said it did.
        self.assertIsNotNone(intake_receipt_of(control, attempt_id))
        self.assertTrue(retentions_of(control, attempt_id))
        self.assertEqual(
            status(job, operations,
                   observed_at=fixtures.NOW)["jobs"][0]["stages"][0]["state"],
            "completed")
        operations.close()

    def test_the_ending_is_not_asked_again_once_cleanup_is_settled(self):
        job, control, operations, _attempt_id, _held = self.worked("ending-once")
        sweep(job, operations, now=fixtures.NOW)
        report = sweep(job, operations, now=fixtures.NOW)
        self.assertEqual(report["spoken"], [])
        operations.close()

    def test_a_terminal_naming_another_envelope_stops_before_intake(self):
        """The mismatch control, through the real owners.

        The freeze is durable and has committed; what must not happen is
        everything after it. A result nobody took custody of cannot reach
        review, and a runtime is not removed on the strength of a correlation
        that failed.
        """
        from baton_v12.worker_manager import intake_receipt_of

        job, control, operations, attempt_id, held = self.worked("ending-bad")
        self.rewrite(held, "sha256:" + "9" * 64)
        report = sweep(job, operations, now=fixtures.NOW)
        self.assertEqual(self.spoke(report), [("conclude", "deferred")])
        self.assertEqual(report["spoken"][0]["detail"]["code"],
                         "operation-collision")
        self.assertIsNone(intake_receipt_of(control, attempt_id))
        self.assertEqual(
            status(job, operations,
                   observed_at=fixtures.NOW)["jobs"][0]["stages"][0]["state"],
            "answering")
        operations.close()

    def test_a_terminal_with_no_usable_digest_never_reaches_the_ending(self):
        """The missing and malformed controls, refused at their own owner.

        `exchange.observation` holds an answered terminal to a canonical
        sha256 digest, so a null or malformed one makes the whole exchange
        `unreadable` -- the stage is `exceptional` and the ending is never
        owed. The refusal is one layer earlier than the mismatch above, which
        is where a shape rule belongs.
        """
        job, control, operations, attempt_id, held = self.worked("ending-null")
        for spoiled in (None, "not-a-digest"):
            with self.subTest(manifest_digest=spoiled):
                self.rewrite(held, spoiled)
                self.assertEqual(
                    single_worker.exchange.observation(held)["state"],
                    "unreadable")
                report = sweep(job, operations, now=fixtures.NOW)
                self.assertEqual(report["spoken"], [])
                self.assertEqual(
                    status(job, operations, observed_at=fixtures.NOW)
                    ["jobs"][0]["stages"][0]["state"], "exceptional")
        operations.close()

    def rewrite(self, held, manifest_digest):
        """Replace the worker's terminal digest, as the provider could.

        The event namespace is writable by the container and the provider runs
        under the same identity, so this is not a contrived edit: it is the
        exact substitution the untrusted-input rule exists to survive.
        """
        place = os.path.join(held.event_root,
                             single_worker.exchange.TERMINAL_DOCUMENT)
        with open(place, encoding="utf-8") as reading:
            document = json.load(reading)
        document["manifest_digest"] = manifest_digest
        os.chmod(place, 0o644)
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(document, writing)


class TheAuthorityBindingIsProvedBeforeAnythingIsConfigured(SingleWorkerCase):
    """W83781 — a Job store bound elsewhere is refused before any side effect.

    `operations_from` used to `del job_store` with a note that this deployment
    needed no private Job-store read. That was true while a Job store knew
    nothing about which Authority it belonged to. It no longer is: the store's
    episode identities are derived in its Authority's namespace and the
    containers those identities name carry that Authority as an immutable
    label, so a store bound to one Authority driven by a configuration naming
    another would start runtimes labelled for an Authority its own identities
    were never derived in.

    THE ORDERING IS THE CORRECTION. Everything after that comparison WRITES --
    the workspace group and storage are configured on the control store, a
    profile is certified, storage is allocated, an Authority is opened -- so a
    mismatch found later would leave this deployment half-configured against a
    store it must not touch at all.
    """

    OTHER = "1" * 31 + "b"

    def foreign_store(self):
        job = JobStore.open(os.path.join(self.root, "foreign.sqlite3"),
                            authority_uuid=self.OTHER, incarnation="foreign",
                            clock=lambda: fixtures.NOW)
        self.addCleanup(job.close)
        return job

    def test_a_store_bound_to_another_authority_refuses(self):
        engine = Engine()
        control = ControlStore.open(self.control_path, incarnation="mismatch",
                                    clock=lambda: fixtures.NOW)
        self.addCleanup(control.close)
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(
                self.config, self.foreign_store(), control,
                engine_run=engine,
                credential_provider=lambda *_: self.secret,
                clock=lambda: fixtures.NOW)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_the_refusal_leaves_the_control_store_unconfigured(self):
        """Nothing durable happened, which is the half a later check loses.

        The workspace group is the first thing `operations_from` would have
        written, so its absence is the evidence that the comparison really did
        come before every side effect.
        """
        from baton_v12.worker_manager import workspaces

        engine = Engine()
        control = ControlStore.open(self.control_path, incarnation="mismatch",
                                    clock=lambda: fixtures.NOW)
        self.addCleanup(control.close)
        with self.assertRaises(ContractRefusal):
            single_worker.operations_from(
                self.config, self.foreign_store(), control,
                engine_run=engine,
                credential_provider=lambda *_: self.secret,
                clock=lambda: fixtures.NOW)
        with self.assertRaises(ContractRefusal):
            workspaces.configured_workspace_group(control)
        self.assertEqual(engine.vectors, [],
                         "no engine call is made on the refused path")

    def test_the_matching_store_still_composes(self):
        engine = Engine()
        job, control = self.stores("matching")
        operations = self.operations(job, control, engine)
        self.assertEqual(job.authority_uuid, self.config["authority_uuid"])
        operations.close()



# -- W122060: the historical composed ending's entry --------------------------
#
# `work/records/2026/09/finding-v12-composed-ending-consumer/`.
#
# ADDITIVE, and the ordinary ending above is unchanged. What these cover is the
# one branch this Work added to `_SingleWorker.ending`: an attempt whose
# composed obligation is registered and whose runtime is already destroyed goes
# to the composition directly, with none of the live evidence the ordinary
# ending reconstructs.


class TheHistoricalEntryTakesNoLiveEvidence(unittest.TestCase):
    """The branch, driven at the seam rather than through a whole fixture.

    The assembled proof lives in `test_stage_execution`, where the obligation
    is registered by ordinary ticks and the cleanup really commits. What
    belongs here is the deployment-side contract: WHEN the branch is taken,
    WHAT it hands the composition, and that the ordinary path is untouched
    when it is not.
    """

    class Composition:
        def __init__(self, answer):
            self.answer = answer
            self.asked = []
            self.ended = []

        def historical(self, stage, assignment):
            self.asked.append((stage, assignment))
            return self.answer

        def end(self, worker, stage, job, context):
            self.ended.append(context)
            return {"ended": context["attempt_id"]}

    def worker(self, answer):
        held = single_worker._SingleWorker.__new__(
            single_worker._SingleWorker)
        held.stage = self.Composition(answer)
        held.given = {"image_digest": "sha256:" + "b" * 64}
        return held

    def ending(self, worker, stage):
        return single_worker._SingleWorker.ending(worker, stage, {"job": 1})

    def patched(self, worker, row):
        def never(*arguments, **operands):
            del arguments, operands
            raise AssertionError("the historical entry read live evidence")

        worker._matches = lambda stage, job: None
        worker._claim = lambda stage: row
        for verb in ("_adopted", "_mounted", "_credential", "_adapter"):
            setattr(worker, verb, never)
        return worker

    ROW = {"authority_uuid": "0" * 32, "work_id": "0000000a-W1",
           "participant": "baton.impl", "claim_generation": 1}

    def test_the_composition_is_entered_with_the_recorded_operands(self):
        answer = {"attempt_id": "attempt-1", "disposition": "completed",
                  "terminal": {"ending": "answered",
                               "manifest_digest": "sha256:" + "c" * 64},
                  "assignment": {"work_ref": {}}, "intent": {"episode": 1}}
        worker = self.patched(self.worker(answer), self.ROW)
        held = self.ending(worker, {"attempt_id": "attempt-1"})
        self.assertEqual(held, {"ended": "attempt-1"})
        [context] = worker.stage.ended
        self.assertEqual(context["disposition"], "completed")
        self.assertEqual(context["terminal"], answer["terminal"])
        # NO ROOTS, which is the whole point: there are none left to name.
        self.assertIsNone(context["roots"])
        self.assertIsInstance(context["adapter"],
                              single_worker._RecordedRuntime)

    def test_the_assignment_carried_in_is_the_claim_rows_own(self):
        answer = {"attempt_id": "attempt-1", "disposition": "completed",
                  "terminal": {}, "assignment": {"work_ref": {}}}
        worker = self.patched(self.worker(answer), self.ROW)
        self.ending(worker, {"attempt_id": "attempt-1"})
        [(_, assignment)] = worker.stage.asked
        self.assertEqual(assignment, {
            "work_ref": {"authority_uuid": "0" * 32,
                         "work_id": "0000000a-W1"},
            "participant": "baton.impl", "generation": 1})

    def test_absence_falls_through_to_the_ordinary_ending(self):
        """`None` means there is nothing historical here, and the ordinary
        path answers -- including its own refusals."""
        worker = self.patched(self.worker(None), self.ROW)
        with self.assertRaises(AssertionError) as caught:
            self.ending(worker, {"attempt_id": "attempt-1"})
        self.assertIn("read live evidence", str(caught.exception))
        self.assertEqual(worker.stage.ended, [])

    def test_a_bootstrap_worker_never_asks_at_all(self):
        """`self.stage is None` is the ordinary single-worker deployment, whose
        ending this Work did not change."""
        worker = self.patched(self.worker(None), self.ROW)
        worker.stage = None
        with self.assertRaises(AssertionError):
            self.ending(worker, {"attempt_id": "attempt-1"})


class TheRecordedRuntimeAdapterPerformsNothing(unittest.TestCase):
    """W122060. A historical ending is TYPED against an adapter and must not be
    able to use one; this makes that a property of the object.

    `review_driver._typed` proves the whole adapter surface before the branch
    that decides which ending is being performed -- correctly, because "a
    composite that finds out halfway through that it cannot finish has already
    stopped somebody's container". After a cleanup there are no roots left to
    compose a real adapter over, so what crosses is a shape whose every verb
    refuses.
    """

    def adapter(self):
        return single_worker._RecordedRuntime("sha256:" + "d" * 64)

    def test_it_satisfies_exactly_what_the_driver_types(self):
        from baton_v12.job_manager import review_driver

        adapter = self.adapter()
        for verb in review_driver.RUNTIME_ADAPTER:
            self.assertTrue(callable(getattr(adapter, verb, None)), verb)
        for member in review_driver.ADAPTER_IDENTITIES:
            self.assertIsInstance(getattr(adapter, member, None), str)

    def test_every_verb_refuses_and_names_itself(self):
        adapter = self.adapter()
        for verb in single_worker._RecordedRuntime.VERBS:
            with self.subTest(verb=verb):
                with self.assertRaises(ContractRefusal) as caught:
                    getattr(adapter, verb)("anything", operand=1)
                self.assertEqual(caught.exception.category, "refused")
                self.assertEqual(caught.exception.code, "capability")
                self.assertIn(verb, caught.exception.message)

    def test_the_deployments_surface_matches_the_drivers(self):
        """A verb added to the driver's tuple and not to this one refuses at
        `_typed` with the verb named, which is the failure this wants."""
        from baton_v12.job_manager import review_driver

        self.assertEqual(sorted(single_worker._RecordedRuntime.VERBS),
                         sorted(review_driver.RUNTIME_ADAPTER))

    def test_it_carries_nothing_else(self):
        adapter = self.adapter()
        for absent in ("start", "run", "engine", "assignment_roots",
                       "credential_delivery", "mounts"):
            with self.subTest(name=absent):
                with self.assertRaises(AttributeError):
                    getattr(adapter, absent)


# -- W125032: the concrete claim refusal, contained at this deployment --------
#
# `work/records/2026/09/finding-v12-composed-ending-consumer/findings/
# finding-concrete-claim-adapter/`, implementing the approved
# `finding-authority-refusal-containment/ALLOCATION-PROPOSAL-2026-09-09.md`.
#
# ADDITIVE. `_AuthoritySession`'s own forwarding cases above are unchanged, and
# so is every assertion about them.


class _Refusing:
    """A session whose `claim` refuses exactly as the Authority's does."""

    participant = "baton.impl"

    def __init__(self, refusal=None, answer=None):
        self.refusal = refusal
        self.answer = answer
        self.claims = []

    def claim(self, *arguments):
        self.claims.append(arguments)
        if self.refusal is not None:
            raise self.refusal
        return self.answer

    def satisfy_gate(self, operands):
        return {"gate": operands["gate"], "kind": "runtime-absent",
                "phase": "queued"}

    def project_work(self, *arguments):
        return {"projected": arguments}


class TheManagerClaimSessionMapsOneRefusalAndNothingElse(unittest.TestCase):
    """W125032: what a concrete Authority claim refusal means to this manager.

    ONE REFUSED CLAIM USED TO ABORT A WHOLE SERVING SWEEP.
    `authority.errors.Refusal` is not a `ContractRefusal`, so the scheduler's
    per-stage handler did not contain it and one Job's ordinary wrong-route
    claim stopped every other Job in the same tick. The mapping below is what
    this deployment adds; the assertions are as much about what it does NOT
    change as about what it does.
    """

    def session(self, **operands):
        held = _Refusing(**operands)
        return held, single_worker._ManagerClaimSession(held)

    def refusal(self, **operands):
        from baton_v12.authority import Refusal

        return Refusal("route 'baton.impl' does not resolve to "
                       "'baton.reviewer'", **operands)

    def claimed(self, **operands):
        _, adapter = self.session(refusal=self.refusal(**operands))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.claim("work", "operands")
        return caught.exception

    # -- the closed mapping --------------------------------------------------

    def test_an_ordinary_refusal_becomes_a_precondition(self):
        """No code and not durable: the ordinary claim-raising shape.

        The scheduler defers without recording success and without retiring
        the fixed claim, so an ordinary retry may succeed when the actual
        precondition does.
        """
        held = self.claimed()
        self.assertEqual((held.category, held.code),
                         ("refused", "precondition"))
        self.assertIs(held.durable, False)
        self.assertIn("does not resolve to", held.message)

    def test_a_remotely_durable_refusal_becomes_ambiguous(self):
        """A durable failure THERE is not a manager receipt HERE.

        `durable` stays false on the way out deliberately: durability is a
        statement about a local receipt, and this is exactly the case where
        this manager has none. Settlement is left to the existing public
        operation recovery.
        """
        held = self.claimed(durable=True)
        self.assertEqual((held.category, held.code),
                         ("ambiguous", "operation"))
        self.assertIs(held.durable, False)

    def test_a_source_code_this_build_cannot_read_is_not_classified(self):
        """An unknown code is not copied into a closed vocabulary."""
        held = self.claimed(code="some-future-authority-code")
        self.assertEqual((held.category, held.code), ("integrity", "schema"))
        self.assertIs(held.durable, False)
        self.assertNotIn("some-future-authority-code", held.message)

    def test_a_malformed_durability_is_not_read_as_yes(self):
        """`1 == True`, and a flag of any other shape is a source this build
        was not written against rather than a quiet yes."""
        for flag in (1, "true", [], object()):
            with self.subTest(flag=type(flag).__name__):
                refusal = self.refusal()
                refusal.durable = flag
                _, adapter = self.session(refusal=refusal)
                with self.assertRaises(ContractRefusal) as caught:
                    adapter.claim()
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))

    def test_a_refusal_missing_its_members_entirely_is_still_contained(self):
        from baton_v12.authority import Refusal

        class Bare(Refusal):
            def __init__(self):
                Exception.__init__(self, "bare")

        _, adapter = self.session(refusal=Bare())
        with self.assertRaises(ContractRefusal) as caught:
            adapter.claim()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    # -- the diagnostic ------------------------------------------------------

    def test_the_sources_words_are_carried_bounded(self):
        from baton_v12.contracts.errors import MESSAGE_LIMIT

        refusal = self.refusal()
        refusal.message = "x" * 100_000
        _, adapter = self.session(refusal=refusal)
        with self.assertRaises(ContractRefusal) as caught:
            adapter.claim()
        self.assertLess(len(caught.exception.message), MESSAGE_LIMIT)

    def test_an_unencodable_diagnostic_does_not_replace_the_refusal(self):
        """A lone surrogate used to be the kind of value that turns a refusal
        into a `UnicodeEncodeError` the moment anything logs it."""
        refusal = self.refusal()
        refusal.message = "route \ud800 broken"
        _, adapter = self.session(refusal=refusal)
        with self.assertRaises(ContractRefusal) as caught:
            adapter.claim()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        caught.exception.message.encode("utf-8")

    def test_only_the_diagnostic_rejection_reaches_the_static_fallback(self):
        """The rejection this fallback is FOR.

        `ContractRefusal` classifies a message that is not text, not encodable
        or too long as a defect at the raising site and says so with an
        assertion. That is the one operand this boundary composes, so that is
        the one rejection it absorbs -- and the refusal keeps its meaning while
        losing only the words it could not carry.
        """
        _, adapter = self.session(refusal=self.refusal())
        with mock.patch.object(single_worker, "ContractRefusal",
                               side_effect=[AssertionError("rejected"),
                                            ContractRefusal(
                                                "refused", "precondition",
                                                "the static fallback")]):
            with self.assertRaises(ContractRefusal) as caught:
                adapter.claim()
        self.assertEqual(caught.exception.message, "the static fallback")

    def test_an_unrelated_failure_at_that_constructor_is_not_absorbed(self):
        """REVIEW 2026-09-09T04-50-13Z [1]. The first cut caught
        `BaseException` here, so an injected `KeyboardInterrupt`, `MemoryError`
        or `RuntimeError` at this exact constructor became an ordinary
        `refused/precondition` result -- the broad catch this boundary exists
        to avoid, one line away from the mapping that avoids it.

        These are raised at the CONSTRUCTOR rather than by the underlying
        claim, which is the distinction the review drew: the cases above prove
        the claim path and say nothing about this one.
        """
        for failure in (KeyboardInterrupt(), MemoryError(),
                        RuntimeError("an unrelated failure")):
            with self.subTest(kind=type(failure).__name__):
                _, adapter = self.session(refusal=self.refusal())
                with mock.patch.object(single_worker, "ContractRefusal",
                                       side_effect=failure):
                    with self.assertRaises(type(failure)) as caught:
                        adapter.claim()
                self.assertIs(caught.exception, failure)

    def test_no_source_exception_is_chained_out(self):
        """A chained cause would carry the source exception -- and the
        diagnostic this boundary just decided not to carry -- out through
        every reader of the refusal.

        `__suppress_context__` rather than an absent `__context__`, and the
        difference is worth stating: Python records the exception being
        handled either way, and `raise ... from None` is what stops every
        traceback, logger and reporter from rendering it.
        """
        _, adapter = self.session(refusal=self.refusal(code="unknown"))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.claim()
        self.assertIsNone(caught.exception.__cause__)
        self.assertIs(caught.exception.__suppress_context__, True)

    # -- and everything it does not touch ------------------------------------

    def test_a_successful_claim_is_answered_exactly(self):
        answer = {"assignment": {"generation": 1}, "claim_event": 7}
        held, adapter = self.session(answer=answer)
        self.assertIs(adapter.claim("a", "b"), answer)
        self.assertEqual(held.claims, [("a", "b")])

    def test_an_existing_contract_refusal_keeps_its_identity(self):
        held = _Refusing()
        held.refusal = ContractRefusal("policy", "profile-uncertified",
                                       "an existing manager refusal")
        adapter = single_worker._ManagerClaimSession(held)
        with self.assertRaises(ContractRefusal) as caught:
            adapter.claim()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "profile-uncertified"))
        self.assertEqual(caught.exception.message,
                         "an existing manager refusal")

    def test_an_unrelated_exception_travels_out_untouched(self):
        """A boundary that swallowed these would hide defects rather than
        contain refusals."""
        for failure in (KeyError("a programming error"),
                        OSError("a transport failure"),
                        MemoryError()):
            with self.subTest(kind=type(failure).__name__):
                held = _Refusing()
                held.refusal = failure
                adapter = single_worker._ManagerClaimSession(held)
                with self.assertRaises(type(failure)):
                    adapter.claim()

    def test_every_other_forwarder_is_the_inherited_one(self):
        """It overrides ONE method, so each of the others keeps its own result
        and refusal identity -- `satisfy_gate` included."""
        for name in ("project_work", "slot_holder", "assignment_of", "cancel",
                     "settle_operation", "satisfy_gate", "publish_answer",
                     "pass_work"):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(single_worker._ManagerClaimSession, name),
                    getattr(single_worker._AuthoritySession, name))
        self.assertIsNot(single_worker._ManagerClaimSession.claim,
                         single_worker._AuthoritySession.claim)

    def test_it_forwards_the_same_minted_session_and_mints_nothing(self):
        held, adapter = self.session()
        self.assertIs(adapter._session, held)
        self.assertEqual(adapter.participant, held.participant)
        self.assertEqual(adapter.project_work("w"), {"projected": ("w",)})

    def test_the_deployment_keeps_the_plain_forwarder(self):
        """Both views wrap the same already-minted participant session; what
        differs is only which of them the manager's port was handed."""
        held = _Refusing(refusal=self.refusal())
        plain = single_worker._AuthoritySession(held)
        from baton_v12.authority import Refusal

        with self.assertRaises(Refusal):
            plain.claim()
        self.assertIs(plain._session, held)


class TheActivityAdmissionExcludesASecondHelperPerStore(unittest.TestCase):
    """W61599: one ingestion helper per held control store, and no second one.

    THE COUNTEREXAMPLE THAT SETTLED THE DESIGN. An earlier revision keyed the
    slot on `(store, attempt)`, which excluded nothing: a composition holding a
    blocked helper for attempt A left `(store, B)` free, so a replacement
    started a SECOND helper against the same store while the first was still
    unresolved. Two writers, one store. The key carries no attempt.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="v12-activity-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.place = os.path.join(self.root, "control.sqlite3")
        self.other = os.path.join(self.root, "other.sqlite3")
        self.addCleanup(self.forget)

    def forget(self):
        """Never leave this process's module-level registry occupied."""
        with single_worker._ACTIVITY_LOCK:
            single_worker._ACTIVITY_HELPERS.clear()

    def store(self, place=None, *, incarnation="i-1"):
        held = ControlStore.open(place or self.place, incarnation=incarnation,
                                 clock=lambda: fixtures.NOW)
        self.addCleanup(held.close)
        return held

    def admitted(self, store):
        helper = single_worker.activity_ingestion(store)
        if helper is not None:
            self.addCleanup(helper.stop, 5)
        return helper

    def test_the_identity_is_the_file_the_held_store_actually_has_open(self):
        """ASKED OF THE HANDLE rather than of a configuration, because neither
        factory is given a control-store path at all."""
        self.assertEqual(single_worker._store_identity(self.store()),
                         os.path.realpath(self.place))

    def test_a_store_with_no_file_admits_nothing(self):
        held = ControlStore.open(":memory:", incarnation="i-1",
                                 clock=lambda: fixtures.NOW)
        self.addCleanup(held.close)
        self.assertIsNone(single_worker._store_identity(held))
        self.assertIsNone(single_worker.activity_ingestion(held))

    def test_one_helper_is_admitted_and_a_second_over_the_same_store_is_not(self):
        first = self.admitted(self.store())
        self.assertIsNotNone(first)
        # A SECOND COMPOSITION over the same store -- its own handle, its own
        # incarnation, everything a distinct deployment would have.
        second = single_worker.activity_ingestion(
            self.store(incarnation="i-2"))
        self.assertIsNone(second)

    def test_a_distinct_composition_for_another_attempt_starts_no_helper(self):
        """THE ACCEPTANCE CASE, with DIFFERENT ATTEMPTS. C1 holds an
        unresolved helper H1 for attempt A; C2 composes for attempt B and must
        start NO helper at all -- proved by the helper never running, not by
        B's documents going uningested. H2 starts only after H1 positively
        exits."""
        import threading

        started = []
        original = single_worker._ActivityIngestion.start

        def watching(inner):
            started.append(inner)
            return original(inner)

        with mock.patch.object(single_worker._ActivityIngestion, "start",
                               watching):
            control = self.store()
            first = single_worker.activity_ingestion(control)
            self.assertIsNotNone(first)
            self.addCleanup(first.stop, 5)
            self.assertEqual(len(started), 1)

            # H1 IS MADE UNRESOLVED: its thread is wedged, so a stop within the
            # bound cannot observe it exit.
            wedged = threading.Event()
            self.addCleanup(wedged.set)
            with mock.patch.object(single_worker._ActivityIngestion,
                                   "_ingest",
                                   staticmethod(lambda _s, _r:
                                                wedged.wait(30))):
                first.enqueue({"attempt_id": "attempt-A", "root": self.root,
                               "session": "session-A"})
                self.assertFalse(first.stop(0.2))

                # C2, A DISTINCT COMPOSITION, FOR A DIFFERENT ATTEMPT.
                second = single_worker.activity_ingestion(
                    self.store(incarnation="i-2"))
                self.assertIsNone(second, "a second helper was started")
                self.assertEqual(len(started), 1,
                                 "the replacement composition started a "
                                 "helper")

                # AND THE SLOT IS STILL HELD, indefinitely, which is the
                # point: no successor may start while one may still be
                # writing.
                self.assertIn(os.path.realpath(self.place),
                              single_worker._ACTIVITY_HELPERS)

            # ONLY A POSITIVE EXIT FREES IT.
            wedged.set()
            self.assertTrue(first.stop(5))
            third = single_worker.activity_ingestion(
                self.store(incarnation="i-3"))
            self.addCleanup(lambda: third and third.stop(5))
            self.assertIsNotNone(third)
            self.assertEqual(len(started), 2)

    def test_repeated_stops_keep_the_live_thread_handle_and_store(self):
        import threading
        from types import SimpleNamespace

        entered, release = threading.Event(), threading.Event()
        closed, writers = [], []
        fake_store = SimpleNamespace(close=lambda: closed.append(threading.get_ident()))
        control = self.store()
        helper = self.admitted(control)
        thread = helper._thread

        def ingest(store, request):
            self.assertIs(store, fake_store)
            writers.append(threading.get_ident())
            entered.set()
            release.wait(5)

        with mock.patch.object(ControlStore, "open", return_value=fake_store), \
                mock.patch.object(single_worker._ActivityIngestion, "_ingest", staticmethod(ingest)):
            try:
                helper.enqueue({"attempt_id": "a"})
                self.assertTrue(entered.wait(2))
                self.assertFalse(helper.stop(0.01))
                self.assertFalse(helper.stop(0.01))
                self.assertIs(helper._thread, thread)
                self.assertTrue(thread.is_alive())
                self.assertEqual(closed, [])
                self.assertIn(os.path.realpath(self.place), single_worker._ACTIVITY_HELPERS)
                with self.assertRaises(ContractRefusal):
                    single_worker.activity_release(helper)
                self.assertEqual(closed, [])
            finally:
                release.set()
                # The captured handle also cleans up the intentionally broken
                # baseline during the regression's negative control.
                thread.join(5)
                self.assertFalse(thread.is_alive())
        self.assertTrue(helper.stop(0.01))
        self.assertEqual(closed, writers)
        self.assertEqual(len(closed), 1)
        self.assertNotIn(os.path.realpath(self.place), single_worker._ACTIVITY_HELPERS)

    def test_two_different_stores_each_admit_their_own(self):
        """THE EXCLUSION IS PER STORE and not a process-wide singleton: two
        unrelated deployments must both get their diagnostic."""
        first = self.admitted(self.store())
        second = self.admitted(self.store(self.other))
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)

    def test_the_registry_is_bounded_and_fails_toward_no_diagnostic(self):
        with single_worker._ACTIVITY_LOCK:
            for index in range(single_worker.MAX_ACTIVITY_ADMISSIONS):
                single_worker._ACTIVITY_HELPERS[f"held-{index}"] = object()
        self.assertIsNone(single_worker.activity_ingestion(self.store()))

    def test_a_helper_that_never_started_releases_its_slot(self):
        """PARTIAL CONSTRUCTION UNWINDS WHAT IT ACQUIRED. A half-built
        composition must not leave a slot occupied by a helper that does not
        exist."""
        with mock.patch.object(single_worker._ActivityIngestion, "start",
                               side_effect=RuntimeError("no thread")):
            with self.assertRaises(RuntimeError):
                single_worker.activity_ingestion(self.store())
        self.assertEqual(single_worker._ACTIVITY_HELPERS, {})
        self.assertIsNotNone(self.admitted(self.store()))

    def test_an_over_bound_stop_refuses_and_leaves_the_slot_held(self):
        """LEAKING A HANDLE IS THE LESSER FAULT. Closing one under a live
        writer is a use-after-close, so the handle and the admission are
        deliberately left alone and the fact is REPORTED."""
        import threading

        wedged = threading.Event()
        helper = self.admitted(self.store())
        self.addCleanup(wedged.set)
        with mock.patch.object(single_worker._ActivityIngestion, "_ingest",
                               staticmethod(lambda _s, _r: wedged.wait(30))):
            helper.enqueue({"attempt_id": "a", "root": self.root,
                            "session": "s"})
            with self.assertRaises(ContractRefusal) as caught:
                single_worker.activity_release(helper, seconds=0.2)
            self.assertEqual(caught.exception.category, "unavailable")
            self.assertIn(os.path.realpath(self.place),
                          single_worker._ACTIVITY_HELPERS)

    def test_releasing_nothing_is_not_a_refusal(self):
        single_worker.activity_release(None)


class TheActivityHelperIngestsOffTheServingLoop(unittest.TestCase):
    """W61599: what the helper actually does with one request.

    ITS STORE HANDLE IS ITS OWN AND IS OPENED ON ITS OWN THREAD, because a
    `sqlite3` connection belongs to the thread that opened it. Nothing here
    runs on the sweep: the sweep assigns a slot and returns.
    """

    ATTEMPT = "attempt-1"
    SESSION = "session-one"

    def setUp(self):
        from baton_v12.worker_manager import record_attempt

        self.root = tempfile.mkdtemp(prefix="v12-ingest-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.place = os.path.join(self.root, "control.sqlite3")
        self.launch_home = os.path.join(self.root, "launch")
        os.makedirs(self.launch_home)
        self.control = ControlStore.open(self.place, incarnation="i-1",
                                         clock=lambda: fixtures.NOW)
        self.addCleanup(self.control.close)
        configure_workspace_group(self.control, os.getgid())
        self.group = configured_workspace_group(self.control)
        certify_profile(self.control, "runtime", "reference",
                        "sha256:" + "3" * 64)
        record_attempt(self.control, attempt_id=self.ATTEMPT,
                       adapter_name="acp",
                       adapter_digest="sha256:" + "a" * 64,
                       profile_digest="sha256:" + "3" * 64)
        self.delivered = launch.materialize(
            self.launch_home, attempt_id=self.ATTEMPT, session=self.SESSION,
            contract="do the thing", role="implementation",
            transport=exchange.EXCHANGE_TRANSPORT, workspace_group=self.group)
        self.held = self.delivered.exchange
        exchange.publish_command(
            self.held, exchange.command_document(session=self.SESSION,
                                                 attempt_id=self.ATTEMPT))
        self.addCleanup(self.forget)

    def forget(self):
        with single_worker._ACTIVITY_LOCK:
            single_worker._ACTIVITY_HELPERS.clear()

    def wrote(self, total, **overrides):
        digested = exchange.observation(self.held)["command"]["command_digest"]
        document = {"schema": exchange.ACTIVITY_SCHEMA,
                    "session": self.SESSION, "attempt_id": self.ATTEMPT,
                    "sequence_id": exchange.sequence_of(self.ATTEMPT),
                    "command_digest": digested, "operation": "work",
                    "operation_id": exchange.worker_operation_id(self.ATTEMPT,
                                                                 "work"),
                    "bytes_observed": total}
        document.update(overrides)
        with open(os.path.join(self.held.event_root,
                               exchange.ACTIVITY_DOCUMENT), "w",
                  encoding="utf-8") as writing:
            json.dump(document, writing)

    def request(self, attempt_id=None, session=None):
        return {"attempt_id": attempt_id or self.ATTEMPT,
                "root": self.delivered.root,
                "session": session or self.SESSION}

    def ingest(self, request=None):
        single_worker._ActivityIngestion._ingest(self.control,
                                                 request or self.request())

    def activity(self):
        return attempt_activity_of(self.control, self.ATTEMPT)

    def test_a_blocked_resolver_leaves_enqueue_and_manager_reads_usable(self):
        import threading

        self.wrote(4096)
        helper = single_worker.activity_ingestion(self.control)
        self.assertIsNotNone(helper)
        thread = helper._thread
        entered, release = threading.Event(), threading.Event()
        original = os.path.realpath

        def resolving(path, *args, **kwargs):
            if threading.current_thread() is thread and path == self.delivered.root:
                entered.set()
                release.wait(5)
            return original(path, *args, **kwargs)

        with mock.patch.object(os.path, "realpath", resolving):
            try:
                helper.enqueue(self.request())
                self.assertTrue(entered.wait(2), "resolver seam was not reached")
                helper.enqueue(self.request())
                self.assertIsNone(self.activity()["bytes_observed"])
                self.assertFalse(release.is_set())
                self.assertFalse(helper.stop(0.01))
            finally:
                release.set()
                thread.join(5)
                self.assertFalse(thread.is_alive())
        self.assertTrue(helper.stop(0.01))
        self.assertEqual(self.activity()["bytes_observed"], 4096)

    def test_a_bound_count_reaches_the_managers_own_record(self):
        self.wrote(4096)
        self.ingest()
        found = self.activity()
        self.assertEqual(found["bytes_observed"], 4096)
        self.assertIsNotNone(found["observed_at"])

    def test_an_absent_document_records_nothing(self):
        self.ingest()
        self.assertIsNone(self.activity()["bytes_observed"])

    def test_a_document_bound_to_another_turn_is_not_ingested(self):
        self.wrote(4096, attempt_id="attempt-9")
        self.ingest()
        self.assertIsNone(self.activity()["bytes_observed"])

    def test_a_hostile_count_is_not_ingested(self):
        self.wrote(-1)
        self.ingest()
        self.assertIsNone(self.activity()["bytes_observed"])

    def test_a_zero_is_never_recorded_as_an_observation(self):
        """`None` AND `0` ARE DIFFERENT ANSWERS. Writing a zero would assert
        "observed, and empty" for a stream nobody has measured."""
        self.wrote(0)
        self.ingest()
        self.assertIsNone(self.activity()["bytes_observed"])

    def test_the_owners_own_rules_decide_repeats_and_regressions(self):
        self.wrote(4096)
        self.ingest()
        first = self.activity()["observed_at"]
        self.wrote(4096)
        self.ingest()
        self.assertEqual(self.activity()["observed_at"], first,
                         "a repeat moved the receipt instant")
        self.wrote(10)
        self.ingest()
        self.assertEqual(self.activity()["bytes_observed"], 4096)

    def test_a_root_naming_nothing_ingests_nothing_and_does_not_raise(self):
        self.ingest(dict(self.request(),
                         root=os.path.join(self.root, "never-made")))
        self.assertIsNone(self.activity()["bytes_observed"])

    def test_no_launch_adoption_runs_on_the_diagnostic_path(self):
        """`launch.adopt` PROVES A DELIVERY BY AUTHORING AND COMPARING ITS
        CANONICAL BYTES, which is a write-path proof this diagnostic has no
        business performing -- and the design forbids it here by name."""
        self.wrote(4096)
        with mock.patch.object(launch, "adopt",
                               side_effect=AssertionError("adopted")):
            self.ingest()
        self.assertEqual(self.activity()["bytes_observed"], 4096)

    def test_the_helper_ingests_from_its_own_thread_and_its_own_handle(self):
        """END TO END THROUGH THE REAL THREAD, which is the half a direct call
        cannot prove: the sweep never touches the store here."""
        import time

        self.wrote(2048)
        helper = single_worker.activity_ingestion(self.control)
        self.assertIsNotNone(helper)
        self.addCleanup(helper.stop, 5)
        helper.enqueue(self.request())
        for _ in range(200):
            if self.activity()["bytes_observed"] is not None:
                break
            time.sleep(0.01)
        self.assertEqual(self.activity()["bytes_observed"], 2048)
        self.assertTrue(helper.stop(5))

    def test_the_newest_request_wins_and_enqueueing_cannot_block(self):
        helper = single_worker.activity_ingestion(self.control)
        self.addCleanup(helper.stop, 5)
        for index in range(1000):
            helper.enqueue(dict(self.request(), session=f"s-{index}"))
        self.assertIsNotNone(helper._slot)


class TheBootstrapCompositionOwnsOneIngestionHelper(SingleWorkerCase):
    """W61599: the factory half, on the hook a bootstrap deployment has.

    A BOOTSTRAP COMPOSITION NEVER REACHES `StageExecution._closers`, so its
    teardown is `_Operations.close`'s single `dispose` hand-back. The two
    factories share the ADMISSION primitive and not the unwind: each
    constructs one helper and releases it through the hook it owns.
    """

    def setUp(self):
        super().setUp()
        self.addCleanup(self.forget)

    def forget(self):
        with single_worker._ACTIVITY_LOCK:
            single_worker._ACTIVITY_HELPERS.clear()

    def test_the_composition_admits_one_and_hands_its_enqueue_to_the_worker(self):
        job, control = self.stores("i-1")
        operations = self.operations(job, control, Engine())
        try:
            helper = single_worker._ACTIVITY_HELPERS.get(
                os.path.realpath(self.control_path))
            self.assertIsNotNone(helper, "no helper was admitted")
            self.assertIsNotNone(operations._worker.activity)
        finally:
            operations.close()

    def test_close_stops_the_helper_and_frees_the_admission(self):
        job, control = self.stores("i-1")
        operations = self.operations(job, control, Engine())
        operations.close()
        self.assertEqual(single_worker._ACTIVITY_HELPERS, {})
        # AND A LATER COMPOSITION OVER THE SAME STORE IS ADMITTED AGAIN.
        again = self.operations(job, control, Engine())
        try:
            self.assertIsNotNone(again._worker.activity)
        finally:
            again.close()

    def test_a_second_composition_over_one_store_composes_with_no_helper(self):
        """IT STILL COMPOSES AND STILL RUNS. Only the optional diagnostic is
        absent, which is what optional has meant throughout."""
        job, control = self.stores("i-1")
        first = self.operations(job, control, Engine())
        try:
            second = self.operations(job, control, Engine())
            try:
                self.assertIsNone(second._worker.activity)
            finally:
                second.close()
        finally:
            first.close()

    def test_an_over_bound_stop_is_reported_out_of_close(self):
        """THE FACT IS CARRIED, not swallowed. An operator is told that a
        helper is unresolved and that its handle and admission are held."""
        import threading

        job, control = self.stores("i-1")
        operations = self.operations(job, control, Engine())
        wedged = threading.Event()
        helper = operations._worker.activity.__self__
        self.addCleanup(helper.stop, 5)
        self.addCleanup(wedged.set)
        with mock.patch.object(single_worker._ActivityIngestion, "_ingest",
                               staticmethod(lambda _s, _r: wedged.wait(30))), \
                mock.patch.object(single_worker, "ACTIVITY_STOP_SECONDS", 0.2):
            operations._worker.activity({"attempt_id": "a",
                                         "root": self.root,
                                         "session": "s"})
            with self.assertRaises(ContractRefusal) as caught:
                operations.close()
        self.assertEqual(caught.exception.category, "unavailable")
        # AND THE AUTHORITY IS STILL RELEASED: a diagnostic must not strand a
        # lock, so the refusal is raised after the ordinary teardown ran.
        resumed = self.operations(job, control, Engine())
        self.addCleanup(resumed.close)

    def test_the_serving_loops_runtime_read_enqueues_and_reads_no_file(self):
        """THE HOOK IS AN ASSIGNMENT. `refresh_runtime` already runs per tick
        on the serving path; what it gains is a slot write, and neither a file
        read, a store write nor a launch adoption happens on this thread."""
        job, control = self.stores("i-1")
        engine = Engine()
        operations = self.operations(job, control, engine)
        try:
            submit(job, self.submission)
            self.commanded(job, operations)
            seen = []
            operations._worker.activity = seen.append
            stage = status(job, operations,
                           observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
            enqueue = single_worker._SingleWorker._enqueue_activity

            def checked_enqueue(worker, attempt_id):
                # Existing runtime reconciliation legitimately checks its
                # workspace. Assert the diagnostic addition performs no I/O.
                with mock.patch.object(os.path, "realpath", side_effect=AssertionError("resolved")) as resolved, \
                        mock.patch.object(os, "lstat", side_effect=AssertionError("stat")) as stated:
                    enqueue(worker, attempt_id)
                resolved.assert_not_called()
                stated.assert_not_called()

            with mock.patch.object(launch, "adopt", side_effect=AssertionError("adopted")), \
                    mock.patch.object(exchange, "observation", side_effect=AssertionError("read")), \
                    mock.patch.object(single_worker._SingleWorker, "_enqueue_activity", checked_enqueue):
                refreshed = operations._worker.refresh_runtime({"attempt_id": stage["attempt_id"]})
            self.assertIsNotNone(refreshed)
            [request] = seen
            self.assertEqual(sorted(request),
                             ["attempt_id", "root", "session"])
            self.assertEqual(request["attempt_id"], stage["attempt_id"])
            self.assertEqual(
                request["root"],
                os.path.join(os.path.realpath(self.config["launch_home"]),
                             stage["attempt_id"]))
            self.assertTrue(os.path.isdir(
                os.path.join(request["root"], exchange.EVENT_DIRECTORY)))
        finally:
            operations.close()

    def test_an_attempt_with_no_runtime_enqueues_nothing(self):
        job, control = self.stores("i-1")
        operations = self.operations(job, control, Engine())
        try:
            seen = []
            operations._worker.activity = seen.append
            self.assertIsNone(
                operations._worker.refresh_runtime({"attempt_id": "never"}))
            self.assertEqual(seen, [])
        finally:
            operations.close()

    def test_a_failing_enqueue_never_stops_the_sweep(self):
        job, control = self.stores("i-1")
        engine = Engine()
        operations = self.operations(job, control, engine)
        try:
            submit(job, self.submission)
            self.commanded(job, operations)

            def exploding(_request):
                raise RuntimeError("the helper is gone")

            operations._worker.activity = exploding
            stage = status(job, operations,
                           observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
            self.assertIsNotNone(operations._worker.refresh_runtime(
                {"attempt_id": stage["attempt_id"]}))
        finally:
            operations.close()


class OptionalIntegrationContextDeclaration(SingleWorkerCase):
    """The manager and worker agree on this exact optional declaration."""

    def test_exact_context_free_integration_declaration_is_accepted(self):
        from tests.manager.test_claude_context import declaration
        given = copy.deepcopy(self.config)
        given["launch_role"] = "integration"
        manifest = given["input_manifest"]
        manifest["outputs"].append(declaration())
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        self.assertEqual(single_worker._held(given, roles=("integration",))["launch_role"], "integration")

    def test_reserved_declaration_variants_remain_refused(self):
        import baton_worker
        from tests.manager.test_claude_context import declaration
        variants = [dict(declaration(), required=True), dict(declaration(), path="other"), dict(declaration(), name="other")]
        for key, value in [("allowed_media_types", ["application/json"]), ("max_bytes", 16385), ("max_entries", 2), ("validator_digest", "sha256:" + "1" * 64), ("link_policy", "allow")]:
            one = declaration(); one["constraints"][key] = value; variants.append(one)
        for one in variants:
            with self.subTest(declaration=one), self.assertRaises(baton_worker.WorkerFault):
                baton_worker.context_declaration({"role": "integration", "schema": "baton.worker-launch/3"}, [one])
        with self.assertRaises(baton_worker.WorkerFault):
            baton_worker.context_declaration({"role": "integration"}, [declaration(), declaration()])
        for role in ("implementation", "unknown"):
            with self.subTest(role=role), self.assertRaises(baton_worker.WorkerFault):
                baton_worker.context_declaration({"role": role}, [declaration()])


class ThreeWorkersOneJobThreeImages(SingleWorkerCase):
    """W202663 — heterogeneous capacity at the LAUNCH boundary, not just the
    contract's.

    `tests/manager/test_manifest_rules.py` fixes what the projection IS. This
    fixes what the deployment DOES with it: `_held` still binds a worker to its
    own image, `_matches` admits a worker whose runtime manifest differs from
    the Job's producer in every worker-runtime member, and both halves of the
    old coupling still refuse when they should.

    Review206898 [R2] required the positive to use INDEPENDENTLY COMPOSED
    manifests rather than clones, and `configured_as` below is written for that:
    every member a separately configured worker would legitimately differ in is
    given a different value, including the manifest's own id and creation
    instant.
    """

    ROLES = ("implementation", "review", "integration")

    def configured_as(self, index, role, **changed):
        """One worker's own deployment and its own runtime manifest.

        Nothing is cloned from `self.config` except the Job-scoped members,
        which is the point: what these three agree about is the Job.
        """
        manifest = dict(self.manifest)
        manifest.update(
            manifest_id=f"input-{role}-attempt",
            created_at=f"2031-0{index + 1}-01T00:00:00.000Z",
            worker_image_digest="sha256:" + str(index) * 64,
            toolchain_digest="sha256:" + chr(97 + index) * 64,
            credential_policy_digest="sha256:" + chr(100 + index) * 64,
            # HEX ONLY. A first draft reached past 'f' for a distinct
            # character and the frozen schema refused the digest's PATTERN
            # before any of this could be measured.
            role_instructions_digest="sha256:" + str(index + 3) * 64)
        manifest.update(changed)
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        given = dict(self.config,
                     input_manifest=manifest,
                     image_digest=manifest["worker_image_digest"],
                     launch_role=role,
                     participant=f"baton.{role}-worker",
                     principal=f"principal:baton.{role}-worker",
                     review_route={"implementation": "rview",
                                   "review": "integration",
                                   "integration": "integration"}[role],
                     launch_home=os.path.join(self.root, "launch-" + role),
                     credential_home=os.path.join(self.root, "cred-" + role))
        return given, manifest

    def held(self, given):
        return single_worker._held(given, roles=(given["launch_role"],))

    def stage_for(self, role):
        return {"stage_id": f"job-a/{role}", "attempt_id": f"attempt-{role}",
                "offer_id": f"offer-{role}", "kind": role,
                "work_id": fixtures.WORK_A, "profile_name": "reference",
                "profile_digest": fixtures.PROFILE}

    def job_for(self, manifest):
        return {"job_id": "job-a",
                "input_digest": job_input_identity(manifest),
                "policy_digest": fixtures.POLICY_DIGEST}

    def worker_for(self, given):
        """A `_SingleWorker` composed far enough to answer `_matches`.

        `_matches` reads only the held configuration and its operands, so this
        deliberately constructs no store, port, engine or credential provider:
        a case that needed a live runtime to ask a preflight question would be
        measuring the fixture.
        """
        worker = single_worker._SingleWorker.__new__(
            single_worker._SingleWorker)
        worker.given = self.held(given)
        return worker

    def test_three_roles_on_three_images_all_match_one_job(self):
        """THE POSITIVE. Three workers, three images, three runtime manifests,
        one Job -- and every one of them is admitted for its own stage."""
        composed = [self.configured_as(index, role)
                    for index, role in enumerate(self.ROLES)]
        runtimes = {manifest["manifest_digest"] for _given, manifest in composed}
        images = {given["image_digest"] for given, _manifest in composed}
        self.assertEqual(len(runtimes), 3, "three workers, three runtimes")
        self.assertEqual(len(images), 3, "three workers, three images")

        job = self.job_for(composed[0][1])
        for (given, manifest), role in zip(composed, self.ROLES):
            with self.subTest(role=role):
                # EACH ONE'S OWN MANIFEST PRODUCES THE JOB'S DIGEST.
                self.assertEqual(job_input_identity(manifest),
                                 job["input_digest"])
                # AND THE DEPLOYMENT ADMITS IT FOR ITS OWN STAGE.
                self.assertIsNone(
                    self.worker_for(given)._matches(self.stage_for(role), job))

    def test_a_worker_whose_image_is_not_its_own_manifests_is_refused(self):
        """`single_worker.py:267` is intact, and it is what stops "each worker
        picks its own image" becoming "any worker may run any image"."""
        given, manifest = self.configured_as(0, "implementation")
        given = dict(given, image_digest="sha256:" + "f" * 64)
        with self.assertRaises(ContractRefusal) as caught:
            self.held(given)
        self.assertIn("names another worker image", caught.exception.message)

    def test_a_worker_that_moved_a_shared_member_is_still_refused(self):
        """The Job half. A heterogeneous pool must not become a pool that
        agrees about nothing: move the WORK and the worker is not this Job's."""
        first = self.configured_as(0, "implementation")[1]
        # THE RECORD BINDING, not the Work. `_matches` compares the stage's
        # own `work_id` against the manifest FIRST, so a moved Work refuses
        # there and never reaches the rule under test -- which would make this
        # a case that passes for the wrong reason. The record binding is
        # shared, is not cross-checked anywhere earlier, and is exactly the
        # kind of Job fact a worker must not be able to move.
        moved = dict(first["record_binding"],
                     path=first["record_binding"]["path"] + "/elsewhere")
        given, _manifest = self.configured_as(1, "review",
                                              record_binding=moved)
        with self.assertRaises(ContractRefusal) as caught:
            self.worker_for(given)._matches(self.stage_for("review"),
                                            self.job_for(first))
        self.assertIn("another bootstrap input", caught.exception.message)

    def test_a_legacy_job_naming_the_whole_manifest_digest_says_so(self):
        """Review206898 [R3]. This IS a semantic change, so a Job submitted
        under the old rule refuses -- and is told which of the two digests it
        named rather than being sent to look for someone else's input."""
        given, manifest = self.configured_as(0, "implementation")
        legacy = {"job_id": "job-a",
                  "input_digest": manifest["manifest_digest"],
                  "policy_digest": fixtures.POLICY_DIGEST}
        with self.assertRaises(ContractRefusal) as caught:
            self.worker_for(given)._matches(self.stage_for("implementation"),
                                            legacy)
        said = caught.exception.message
        self.assertIn("whole runtime manifest digest", said)
        self.assertIn(job_input_identity(manifest), said)
        self.assertIn("is not rewritten", said)

    def test_the_two_refusals_are_told_apart(self):
        """The whole reason the legacy branch exists: a migratable Job and a
        Job about someone else's input must not read the same."""
        given, manifest = self.configured_as(0, "implementation")
        stage = self.stage_for("implementation")
        worker = self.worker_for(given)
        messages = []
        for job in ({"job_id": "job-a",
                     "input_digest": manifest["manifest_digest"],
                     "policy_digest": fixtures.POLICY_DIGEST},
                    {"job_id": "job-a",
                     "input_digest": "sha256:" + "e" * 64,
                     "policy_digest": fixtures.POLICY_DIGEST}):
            with self.assertRaises(ContractRefusal) as caught:
                worker._matches(stage, job)
            messages.append(caught.exception.message)
        self.assertNotEqual(messages[0], messages[1])


class TheDeploymentCanStopWhatItStarted(SingleWorkerCase):
    """W236087 R2a: the composed worker's own cancellation, and its honesty.

    A bounded owner supervisor reaching its deadline with a provider turn in
    flight had nothing to drive: closing its admission gate stops the NEXT
    runtime and the ordinary ending path has nothing to finish while this one
    waits. The stop belongs to the deployment, because the port, the agent and
    the adapter are its own.
    """

    def test_the_agent_reports_the_absent_channel_rather_than_pretending(self):
        """This worker speaks through a durable file exchange.

        Nothing here can reach a provider turn already in flight, so the
        settlement SAYS so and travels back un-summarized. A bare success
        would be a deployment telling the manager that a worker cooperated
        with an order it never received.
        """
        agent = single_worker._UncooperativeAgent(self.config)
        answered = agent.cancel({"attempt_id": "attempt-1",
                                 "assignment": {"participant": fixtures.WHO},
                                 "runtime_id": "runtime-1",
                                 "operation_id": "cancel-1"})
        self.assertIs(answered["cooperative"], False)
        self.assertEqual(answered["attempt_id"], "attempt-1")
        self.assertEqual(answered["operation_id"], "cancel-1")
        self.assertEqual(answered["participant"], self.config["participant"])
        self.assertIn("no cooperative cancellation channel", answered["why"])

    def test_the_agent_refuses_a_command_it_cannot_own(self):
        agent = single_worker._UncooperativeAgent(self.config)
        with self.assertRaises(ContractRefusal):
            agent.cancel({"attempt_id": "attempt-1"})

    def test_cancellation_goes_through_the_accepted_manager_path(self):
        """FENCE, THEN STOP -- and this composes neither half itself.

        `attempts.request_cancellation` fences the exact participant and
        generation at the Authority before ordering quiescence. What this
        asserts is that the worker hands it this deployment's own store, port,
        agent and runtime adapter, and nothing else.
        """
        from unittest import mock

        engine = Engine()
        operations = self.operations(*self.stores("cancel-seam"), engine)
        self.addCleanup(operations.close)
        worker = operations._worker
        with mock.patch.object(single_worker.attempts,
                               "request_cancellation") as cancelling:
            cancelling.return_value = {"fenced": {"generation": 1}}
            answered = operations.cancel_attempt(attempt_id="attempt-1",
                                                 reason="overall bound")
        self.assertEqual(answered, {"fenced": {"generation": 1}})
        (store, port, agent, adapter), named = cancelling.call_args
        self.assertIs(store, worker.control)
        self.assertIs(port, worker.port)
        self.assertIsInstance(agent, single_worker._UncooperativeAgent)
        self.assertIsInstance(adapter, single_worker.OciAdapter)
        self.assertEqual(named, {"attempt_id": "attempt-1",
                                 "reason": "overall bound"})

    def test_a_malformed_attempt_identity_refuses_before_anything_opens(self):
        engine = Engine()
        operations = self.operations(*self.stores("cancel-refusal"), engine)
        self.addCleanup(operations.close)
        with self.assertRaises(ContractRefusal):
            operations.cancel_attempt(attempt_id="", reason="overall bound")
