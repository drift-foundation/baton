"""W76207 -- the deployable one-worker Job Manager composition.

These are production-seam tests: real Job, control and Authority stores, the
public manager loop, real workspace/input/launch composition, and only the OCI
engine boundary replaced with a recording process capability.
"""

import copy
import json
import os
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.contracts import (ContractRefusal, digest, digest_of_bytes,
                                 forget_secret, live_secret, remember_secret)
from baton_v12.job_manager import (JobStore, reconcile, status, submit)
from baton_v12.worker_manager import (ControlStore,
                                      attempt_preparation_failure_of,
                                      attempt_runtime_of,
                                      attempt_start_failure_of,
                                      certify_profile, claimed_offers_for)
from baton_v12.worker_manager import documents as worker_documents

from tests.manager import input_roots
from tests.job_manager import fixtures
from tools import single_worker
from tools.user_credentials import SourceRefusal


ADAPTER = "sha256:" + "d" * 64
AUTHORITY_UUID = "0000000a" + "0" * 24


class Engine:
    """One observable OCI process boundary, without a daemon or container."""

    def __init__(self):
        self.vectors = []
        self.runtime_id = None
        self.labels = {}
        self.image = None
        self.mounts = []

    def __call__(self, argv, *, seconds=None):
        del seconds
        self.vectors.append(list(argv))
        if argv[1] == "run":
            self.runtime_id = "runtime-single-1"
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
                    "State": {"Running": True},
                    "Mounts": list(self.mounts)}
            return self.answer(stdout=json.dumps(body))
        return self.answer()

    @staticmethod
    def answer(status=0, stdout="", stderr=""):
        return {"status": status, "stdout": stdout, "stderr": stderr}

    @property
    def starts(self):
        return [one for one in self.vectors if one[1] == "run"]


class SingleWorkerCase(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory(
            prefix="v12-single-worker-")
        self.addCleanup(self._temporary.cleanup)
        self.root = self._temporary.name
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
        self.task_bytes = json.dumps(
            {"schema": "baton.dogfood-task/1", "task_id": "w81115-bootstrap",
             "instructions": "write one bounded proposal",
             "source_root": "source",
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
        self.manifest["sources"][0]["content_manifest"] = (
            single_worker.workspaces.directory_manifest(self.source))
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
            "input_source": self.source,
            "input_manifest": self.manifest,
            "task_document": self.task_document,
            "launch_contract": "v12-assignment-1",
            "launch_role": "implementation"}
        self.secret = "single-worker-secret-" + "7" * 40
        self.addCleanup(self._forget_secret)
        self.submission = fixtures.submission(
            jobs=[fixtures.job(
                input_digest=self.manifest["manifest_digest"],
                policy_digest=fixtures.POLICY_DIGEST,
                stages=[fixtures.stage(
                    work_id=fixtures.WORK_A,
                    profile_name="reference",
                    profile_digest=fixtures.PROFILE)])])

    def stores(self, incarnation):
        job = JobStore.open(self.job_path, incarnation=incarnation,
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

    def running(self, job, operations):
        for _ in range(6):
            reconcile(job, operations, now=fixtures.NOW)
            projected = status(job, operations, observed_at=fixtures.NOW)
            if projected["jobs"][0]["stages"][0]["state"] == "running":
                return projected
        self.fail("the one-worker pipeline did not become running")


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
        projected = self.running(resumed_job, resumed)
        stage = projected["jobs"][0]["stages"][0]
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(len(claimed_offers_for(resumed_control,
                                                stage["attempt_id"])), 1)
        resumed.close()

    def test_one_submission_becomes_one_observable_runtime_and_is_adopted(self):
        engine = Engine()
        job, control = self.stores("first")
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        first = self.running(job, operations)
        stage = first["jobs"][0]["stages"][0]
        self.assertEqual(stage["state"], "running")
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
        after = self.running(restarted_job, restarted)
        self.assertEqual(after["jobs"][0]["stages"][0]["state"], "running")
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
        self.running(resumed_job, resumed)
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
                if argv[1] == "run" and not self.interrupted:
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
        after = self.running(resumed_job, resumed)
        self.assertEqual(after["jobs"][0]["stages"][0]["state"], "running")
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
        """
        carrying = dict(self.config,
                        schema="baton.v12.single-worker-deployment/1")
        held = self.refused(carrying, "superseded-schema")
        self.assertEqual(held.code, "schema")
        self.assertIn("single-worker-deployment/2", held.message)

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
        projected = self.running(job, operations)
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

    def test_the_source_identity_is_proved_before_authority_is_opened(self):
        with open(os.path.join(self.source, "worker-task.txt"), "a",
                  encoding="utf-8") as writing:
            writing.write("changed\n")
        job, control = self.stores("changed-source")
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.operations_from(self.config, job, control,
                                          engine_run=Engine(),
                                          credential_provider=lambda *_:
                                          self.secret)
        self.assertEqual(caught.exception.code, "digest")
        self.assertEqual(claimed_offers_for(control, "no-attempt"), [])


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
        projected = self.running(job, operations)
        stage = projected["jobs"][0]["stages"][0]
        inputs = os.path.join(self.storage, stage["attempt_id"], "inputs")
        return engine, job, control, operations, stage, inputs

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
            ["job-a/implementation"]["state"], "running")
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
        self.assertEqual(held["job-a/implementation"]["state"], "running",
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
        projected = self.running(job, operations)
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
            input_digest=self.manifest["manifest_digest"],
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
        with self.assertRaises(ContractRefusal) as caught:
            operations._worker._input(
                {"inputs": inputs},
                {"assignment_ref": {}, "runtime_attempt_id": "unused"})
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
                self.armed = self.armed or argv[1] == "run"
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
        self.assertEqual(held["job-a/implementation"]["state"], "running")
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
        self.assertEqual(held["job-a/implementation"]["state"], "running")
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
                if argv[1] == "run":
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
            """`run` creates the container AND reports failure."""

            def __call__(self, argv, *, seconds=None):
                answer = super().__call__(argv, seconds=seconds)
                if argv[1] == "run":
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
        self.assertEqual(held["job-a/implementation"]["state"], "running")
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
