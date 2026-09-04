"""W76207 -- the deployable one-worker Job Manager composition.

These are production-seam tests: real Job, control and Authority stores, the
public manager loop, real workspace/input/launch composition, and only the OCI
engine boundary replaced with a recording process capability.
"""

import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.contracts import (ContractRefusal, digest, forget_secret,
                                 live_secret, remember_secret)
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
        self.manifest = copy.deepcopy(given)
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
