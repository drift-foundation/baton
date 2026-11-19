"""Focused checks for admitting ONE worker into an installed pool. W202663.

DETERMINISTIC AND OFFLINE. No provider, engine, container, Job or network is
involved. The instance these cases amend is a REAL one -- composed by
`tools.bootstrap` itself, over a real Authority -- because the subject is what
a verb does to a deployment that already exists, and a hand-written
`deployment.json` would be this suite's own idea of one rather than the thing
the install path emits.

THE FIXTURE IS BOOTSTRAP'S OWN, for the reason its `ValidFixture` docstring
gives about itself: a worker document is digest-sealed over an Authority
identity, so a valid one cannot be written for an instance this suite invented.
Reusing that case reuses the accepted stage fixture underneath it, which is the
one place in this build that knows what a valid worker document is.

WHAT IS NOT PROVED HERE is that any particular image, credential, profile or
participant is fit for production, and -- said because the verb says it about
itself -- that an admitted worker can CLAIM. A route handler is a durable
Authority act and this verb makes none; these cases prove the configuration,
which is what it changes.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import bootstrap
from tools import pool
from tools import stage_execution

try:
    from tests.tools import test_bootstrap as _bootstrap_case
except ImportError:                                         # pragma: no cover
    _bootstrap_case = None


@unittest.skipIf(_bootstrap_case is None,
                 "the accepted bootstrap fixtures are not importable")
class PoolCase(_bootstrap_case.ValidFixture if _bootstrap_case
               else unittest.TestCase):
    """One instance, really installed, with a pool this verb can grow.

    IT BINDS NO JOB, which is the ordinary fresh installation and is also the
    `/2` document -- the variant that says its bindings out loud. The one-Job
    `/1` variant serves exactly one worker per role, so it has no admission to
    make and this verb refuses it by name; that refusal is its own case below.
    """

    def setUp(self):
        super().setUp()
        document = self.document()
        document.pop("jobs", None)
        with open(os.devnull, "w") as quiet:
            self.installed = bootstrap.prepare(document, stream=quiet)
        self.place = self.installed["places"]["configuration"]
        self.before = Path(self.place).read_bytes()
        self.held = json.loads(self.before)

    # -- the worker under test ------------------------------------------------

    def candidate(self, worker_id="impl-b", role="implementation",
                  participant="baton.impl-b", **members):
        """One more worker, in the shape an input document names one.

        `stage_worker` carries a deliberately STALE principal, which is the
        accepted fixture's own device: a worker supplying the principal the
        deployment derives would make "the deployment derives it"
        unfalsifiable.
        """
        return self.stage_worker(worker_id, role, participant, **members)

    def admitting(self, worker=None, **members):
        said = io.StringIO()
        answer = pool.admit(self.place, worker or self.candidate(**members),
                            stream=said)
        answer["said"] = said.getvalue()
        return answer

    def refused(self, worker=None, **members):
        with self.assertRaises(pool.PoolRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                pool.admit(self.place, worker or self.candidate(**members),
                           stream=quiet)
        return str(raised.exception)

    def unchanged(self):
        """The configuration this verb read is the configuration on disk."""
        self.assertEqual(Path(self.place).read_bytes(), self.before)

    def written(self):
        return json.loads(Path(self.place).read_bytes())


class AValidWorkerIsAdmitted(PoolCase):
    """The whole point of the verb: one more worker, configured."""

    def test_it_is_appended_to_the_pool_the_instance_already_has(self):
        answer = self.admitting()
        written = self.written()
        self.assertEqual([one["worker_id"] for one in written["workers"]],
                         [one["worker_id"] for one in self.held["workers"]]
                         + ["impl-b"])
        self.assertEqual(answer["worker"], written["workers"][-1])

    def test_the_five_derived_members_are_the_deployments_own(self):
        """Exactly the five `bootstrap.configuration` fills in, taken from the
        instance's own configuration rather than from the supplied document."""
        entry = self.admitting()["worker"]
        deployment = entry["deployment"]
        self.assertEqual(deployment["participant"], "baton.impl-b")
        self.assertEqual(deployment["launch_role"], "implementation")
        self.assertEqual(deployment["authority_store"],
                         self.held["authority_store"])
        self.assertEqual(deployment["authority_uuid"],
                         self.held["authority_uuid"])
        # AND THE PRINCIPAL IS THE AUTHORITY'S ANSWER, not the stale one the
        # supplied document carried. If the resolution were dropped, this is
        # the assertion that would notice.
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.held["authority_store"],
            expected_authority_uuid=self.held["authority_uuid"])
        try:
            self.assertEqual(deployment["principal"],
                             authority.principal_of("baton.impl-b"))
        finally:
            authority.dispose()
        self.assertNotEqual(deployment["principal"],
                            "principal:stale-baton.impl-b")

    def test_what_it_wrote_is_a_document_the_MANAGER_still_accepts(self):
        """`admit` calls the accepted validator itself, so reaching this line
        is already the proof; asking the file back is what makes the amended
        deployment a case rather than a side effect."""
        self.admitting()
        normalized = stage_execution.held_configuration(self.written())
        self.assertEqual(
            sorted(one["worker_id"] for one in normalized["workers"]),
            ["impl-a", "impl-b", "integ-a", "review-a"])

    def test_it_says_what_it_did_and_what_it_did_NOT_do(self):
        said = self.admitting()["said"]
        self.assertIn("impl-b", said)
        self.assertIn("will be minted at the next activation", said)
        for promise in ("no Job was prepared", "nothing was submitted",
                        "no Work was created or touched",
                        "no configured worker was removed or changed"):
            self.assertIn(promise, said)

    def test_a_review_worker_is_admitted_the_same_way(self):
        """The role is not hard-wired to implementation; what a role may be is
        `bootstrap.ROLES`, and the independence rule still stands over it."""
        answer = self.admitting(worker_id="review-b", role="review",
                                participant="baton.reviewer-b",
                                review_route=self.INTEGRATION_ROUTE)
        self.assertEqual(answer["worker"]["role"], "review")
        stage_execution.held_configuration(self.written())

    def test_a_review_worker_sharing_the_IMPLEMENTATION_participant_is_refused(self):
        """An honest review is not one the implementer performs, and that rule
        is the accepted validator's rather than a second copy here."""
        said = self.refused(worker_id="review-b", role="review",
                            participant="baton.impl-a",
                            review_route=self.INTEGRATION_ROUTE)
        self.assertIn("independent review", said)
        self.unchanged()


class AnImageDigestDisagreeingWithItsManifestIsRefused(PoolCase):
    """THE COMPARISON THIS VERB MOST EXISTS TO KEEP.

    A worker's `image_digest` and its input manifest's `worker_image_digest`
    are one fact said twice, and the manifest carries its own digest over its
    own bytes -- so the two disagreeing means the configuration names an image
    the sealed manifest does not. `single_worker._held` refuses it, and this
    case proves the refusal survives being reached through THIS verb rather
    than through the install path.
    """

    def test_it_is_refused_by_name_and_nothing_is_written(self):
        worker = self.candidate()
        self.assertNotEqual(worker["deployment"]["image_digest"],
                            "sha256:" + "b" * 64)
        worker["deployment"]["image_digest"] = "sha256:" + "b" * 64
        said = self.refused(worker)
        self.assertIn("bootstrap input manifest names another worker image",
                      said)
        self.unchanged()

    def test_the_MANIFEST_cannot_be_moved_to_agree_instead(self):
        """The other direction, and it is refused EARLIER and harder.

        An operator whose two values disagree might reach for the manifest
        rather than the configuration. They cannot: the manifest declares a
        digest over its own bytes, so editing the image it names makes a
        document that no longer identifies itself. The agreement is held by
        sealing rather than by comparison alone, which is why neither side of
        it can be quietly brought to the other.
        """
        worker = self.candidate()
        worker["deployment"]["input_manifest"] = dict(
            worker["deployment"]["input_manifest"],
            worker_image_digest="sha256:" + "c" * 64)
        said = self.refused(worker)
        self.assertIn("declares a manifest digest its own bytes do not "
                      "produce", said)
        self.unchanged()

    def test_a_worker_sealed_to_ANOTHER_Authority_cannot_be_RESEALED(self):
        """The identity the manifest names is sealed the same way, which is
        why a worker written for one instance cannot be edited into another --
        and is the reason this verb fills in `authority_uuid` from the
        instance's own configuration and still refuses the document."""
        worker = self.candidate()
        worker["deployment"]["input_manifest"] = dict(
            worker["deployment"]["input_manifest"],
            work_ref=dict(worker["deployment"]["input_manifest"]["work_ref"],
                          authority_uuid="d" * 32))
        self.assertIn("declares a manifest digest its own bytes do not "
                      "produce", self.refused(worker))
        self.unchanged()


class AnExistingWorkerIdIsRefused(PoolCase):
    """The pool tells its workers apart by identity and cannot hold one twice.

    AND THE REFUSAL COMES BEFORE ANYTHING IS WRITTEN, which is the half that
    matters: a verb that appended the namesake and then discovered the
    collision in the accepted validator would have refused with the instance's
    own configuration already replaced.
    """

    def test_an_identity_already_configured_is_refused(self):
        said = self.refused(worker_id="impl-a", participant="baton.impl-b")
        self.assertIn("'impl-a'", said)
        self.assertIn("cannot hold it twice", said)
        self.unchanged()

    def test_it_is_refused_for_EVERY_configured_identity_not_only_its_role(self):
        for worker_id, role in (("review-a", "implementation"),
                                ("integ-a", "implementation")):
            with self.subTest(worker_id=worker_id):
                said = self.refused(worker_id=worker_id, role=role,
                                    participant="baton.impl-b")
                self.assertIn("cannot hold it twice", said)
                self.unchanged()

    def test_the_configured_worker_it_names_is_left_exactly_as_it_is(self):
        """Nothing here replaces a configured worker: the refusal is the whole
        act, and the entry the operator collided with still says what it said."""
        was = [one for one in self.held["workers"]
               if one["worker_id"] == "impl-a"][0]
        self.refused(worker_id="impl-a", participant="baton.impl-b")
        again = [one for one in self.written()["workers"]
                 if one["worker_id"] == "impl-a"][0]
        self.assertEqual(again, was)


class NothingElseInTheConfigurationChanges(PoolCase):
    """BYTE FOR BYTE, and the comparison is over the published bytes.

    `tools.bootstrap` publishes this file with one serializer, and this verb
    republishes it with the SAME one over the same document plus one entry --
    so the difference between the two files is exactly the entry, and removing
    it reproduces the original bytes. That is a stronger statement than "the
    other members compare equal", because it also catches a member reordered,
    a number reformatted or a document silently normalized on the way through.
    """

    def republished(self, document):
        """The same bytes `bootstrap._publish` would write for a document."""
        return (json.dumps(document, indent=2, sort_keys=True)
                + "\n").encode("utf-8")

    def test_removing_the_admitted_worker_reproduces_the_original_bytes(self):
        self.admitting()
        written = self.written()
        self.assertEqual(written["workers"][-1]["worker_id"], "impl-b")
        del written["workers"][-1]
        self.assertEqual(self.republished(written), self.before)

    def test_the_pool_generation_does_not_move_on_an_instance_never_activated(self):
        """The one member this verb may also move stays where it is when the
        scheduler's own rule answers the generation already configured."""
        answer = self.admitting()
        self.assertEqual(answer["pool_generation"],
                         self.held["pool_generation"])
        self.assertEqual(self.written()["pool_generation"],
                         self.held["pool_generation"])

    def test_the_custody_record_beside_it_is_not_touched_either(self):
        record = Path(self.installed["places"]["record"])
        was = record.read_bytes()
        self.admitting()
        self.assertEqual(record.read_bytes(), was)

    def test_every_worker_that_was_configured_is_unchanged(self):
        """Said separately from the byte comparison because this is the
        promise an operator actually reads: an admission is an addition."""
        self.admitting()
        written = self.written()
        self.assertEqual(written["workers"][:len(self.held["workers"])],
                         self.held["workers"])


class ItPreparesNoJobAndTouchesNoWork(PoolCase):
    """The verb's own list of what it does not do, proved rather than stated."""

    def authority(self):
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.held["authority_store"],
            expected_authority_uuid=self.held["authority_uuid"])
        self.addCleanup(authority.dispose)
        return authority

    def test_no_Work_grant_or_Job_store_is_composed(self):
        before = self.authority().policy_generation()
        self.admitting()
        authority = self.authority()
        self.assertIsNone(_work_or_none(authority, self.work))
        for who in self.held["receipt_participants"].values():
            self.assertEqual(authority.grants_of(who), [], who)
        self.assertEqual(authority.grants_of("baton.impl-b"), [])
        # AND NO ROUTE HANDLER, which is the durable act this verb does not
        # make and says so: `add_route_handler` bumps the policy generation,
        # so an unmoved generation is the evidence that none was added.
        self.assertEqual(authority.policy_generation(), before)

    def test_it_creates_no_Job_store_to_read_a_generation_from(self):
        """An instance whose scheduler has never run has no Job store, and
        asking what generation would be minted must not manufacture one."""
        place = pool.job_store_of(self.held)
        self.assertFalse(os.path.exists(place), place)
        self.assertEqual(self.admitting()["pool_generation"], 1)
        self.assertFalse(os.path.exists(place), place)

    def test_the_job_store_is_the_Authority_stores_sibling_in_BOTH_layouts(self):
        """`job_store_of` derives one path from another, and this is why it
        may: the two layouts this build writes agree about it."""
        from tools import instance

        for places in (bootstrap.layout("/somewhere/root"),
                       instance.layout("/somewhere/destination")):
            with self.subTest(places=places["authority_store"]):
                self.assertEqual(
                    pool.job_store_of({"authority_store":
                                       places["authority_store"]}),
                    places["job_store"])


class ThePoolGenerationIsTheSchedulersOwnAnswer(PoolCase):
    """READ FROM THE STORE, not decided here.

    `stage_execution._pool_generation` refuses a deployment whose configured
    generation is not the one activating its pool would answer, so a verb that
    changed the pool and left the number behind would write a configuration the
    manager refuses to serve -- an instance broken by the command meant to grow
    it. These cases drive the other side of that rule: a pool that HAS been
    activated.
    """

    def activated(self):
        """This instance's own pool, activated at generation 1."""
        from baton_v12.job_manager import JobStore, scheduler
        from tests.job_manager import fixtures

        store = JobStore.open(pool.job_store_of(self.held),
                              authority_uuid=self.held["authority_uuid"],
                              incarnation="pool-case",
                              clock=lambda: fixtures.NOW)
        self.addCleanup(store.close)
        scheduler.activate_pool(
            store, stage_execution._pool(
                stage_execution.held_configuration(self.held), None),
            {one["deployment"]["participant"]: one["deployment"]["principal"]
             for one in self.held["workers"]})
        self.assertEqual(scheduler.active_generation(store)["generation"], 1)
        return store

    def test_an_activated_pool_moves_the_generation_on_by_one(self):
        self.activated()
        answer = self.admitting()
        self.assertEqual(answer["pool_generation"], 2)
        self.assertEqual(self.written()["pool_generation"], 2)
        self.assertIn("generation 2 will be minted", answer["said"])

    def test_the_activated_generation_itself_is_left_alone(self):
        """It activates nothing: the store still holds generation 1, and the
        four workers it was activated over."""
        from baton_v12.job_manager import scheduler

        store = self.activated()
        self.admitting()
        active = scheduler.active_generation(store)
        self.assertEqual(active["generation"], 1)
        self.assertEqual(
            sorted(one["worker_id"]
                   for one in scheduler.pool_workers(store, 1)),
            ["impl-a", "integ-a", "review-a"])

    def test_what_it_wrote_is_a_deployment_that_would_still_ACTIVATE(self):
        """The whole reason the member moves. The amended configuration is
        handed to the rule that refuses a stale generation, and it passes."""
        store = self.activated()
        self.admitting()
        self.assertEqual(
            stage_execution._pool_generation(
                store, stage_execution.held_configuration(self.written()),
                None)["workers"][0]["worker_id"],
            "impl-a")

    def test_a_STALE_generation_is_what_that_rule_refuses(self):
        """The counter-case, so the one above is not passing for free."""
        from baton_v12.contracts import ContractRefusal

        store = self.activated()
        self.admitting()
        stale = dict(self.written(), pool_generation=1)
        with self.assertRaises(ContractRefusal) as raised:
            stage_execution._pool_generation(
                store, stage_execution.held_configuration(stale), None)
        self.assertIn("would answer generation 2", raised.exception.message)


class WhatTheVerbRefusesBeforeItReadsAWorker(PoolCase):
    """Every fault an operator can make about the instance itself."""

    def test_a_configuration_that_is_not_there_is_named(self):
        gone = os.path.join(self.root, "no-such-deployment.json")
        with self.assertRaises(pool.PoolRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                pool.admit(gone, self.candidate(), stream=quiet)
        self.assertIn(gone, str(raised.exception))
        self.assertIn("Nothing was changed", str(raised.exception))

    def test_the_one_job_variant_has_no_admission_to_make(self):
        """`/1` serves exactly one worker per role, and nothing here rewrites
        a deployment's schema to make room."""
        one_job = os.path.join(self.root, "one-job-deployment.json")
        Path(one_job).write_text(json.dumps(
            dict(self.held, schema=stage_execution.CONFIG_SCHEMA)))
        with self.assertRaises(pool.PoolRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                pool.admit(one_job, self.candidate(), stream=quiet)
        self.assertIn("exactly one worker per role", str(raised.exception))
        self.assertIn(stage_execution.MULTI_CONFIG_SCHEMA,
                      str(raised.exception))

    def test_a_worker_naming_a_member_nothing_reads_is_refused(self):
        worker = self.candidate()
        worker["nominated_source"] = "/tmp"
        said = self.refused(worker)
        self.assertIn("nominated_source", said)
        self.assertIn("nothing reads", said)
        self.unchanged()

    def test_a_worker_missing_a_member_is_refused_by_NAME(self):
        worker = self.candidate()
        del worker["participant"]
        self.assertIn("participant", self.refused(worker))
        self.unchanged()

    def test_a_worker_id_that_is_not_ONE_NAME_is_refused(self):
        said = self.refused(worker_id="x/../../escape")
        self.assertIn("one path component", said)
        self.unchanged()

    def test_a_role_this_deployment_does_not_serve_is_refused(self):
        said = self.refused(role="auditing")
        self.assertIn("'auditing'", said)
        self.unchanged()


class TheCommandLine(PoolCase):
    """One verb, and its two operands."""

    def written_worker(self, worker=None, **members):
        place = os.path.join(self.root, "worker-document.json")
        Path(place).write_text(json.dumps(worker or self.candidate(**members)))
        return place

    def running(self, argv):
        said = io.StringIO()
        return pool.main(argv, stream=said), said.getvalue()

    def parsing(self, argv):
        """argparse writes its own usage to stderr; a suite's output is not
        the place for it."""
        with contextlib.redirect_stderr(io.StringIO()):
            return self.running(argv)

    def test_add_worker_admits_and_returns_zero(self):
        code, said = self.running([pool.VERB, "--deployment", self.place,
                                   "--worker", self.written_worker()])
        self.assertEqual(code, 0, said)
        self.assertIn("impl-b", said)
        self.assertEqual(len(self.written()["workers"]), 4)

    def test_a_refusal_is_said_rather_than_raised_and_returns_two(self):
        worker = self.candidate()
        worker["deployment"]["image_digest"] = "sha256:" + "b" * 64
        code, said = self.running([pool.VERB, "--deployment", self.place,
                                   "--worker", self.written_worker(worker)])
        self.assertEqual(code, 2)
        self.assertIn("refused: ", said)
        self.assertIn("another worker image", said)
        self.unchanged()

    def test_a_worker_document_that_is_not_JSON_is_refused(self):
        place = os.path.join(self.root, "not-json.json")
        Path(place).write_text("{not json")
        code, said = self.running([pool.VERB, "--deployment", self.place,
                                   "--worker", place])
        self.assertEqual(code, 2)
        self.assertIn("one UTF-8 JSON document", said)
        self.unchanged()

    def test_it_is_the_ONLY_verb_and_it_adds_nothing_else(self):
        """The Work admits one tool and one verb. A second one arriving here
        by accident is what this notices."""
        with self.assertRaises(SystemExit):
            self.parsing(["remove-worker", "--deployment", self.place,
                          "--worker", "/dev/null"])


class ComposingAWorkerForThisInstance(PoolCase):
    """W321608 (reusable kickoff): a worker document for an installed
    instance is composed by the product from THIS BUILD'S OWN documents --
    the runtime profile, policy and adapter `next_run_bindings` composes and
    the published manifest vector -- plus ordinary operator configuration
    (image, CLI build, network, credential registry and mapping, workspace
    group, task document). Nothing is inherited from another instance's
    protocol documents, and no installation needs a dossier script."""

    IMAGE = "sha256:" + "c" * 64

    def task_file(self, task_id="labels-cli", name="labels-task.json"):
        held = json.loads(Path(self.config["task_document"]).read_bytes())
        held["task_id"] = task_id
        held["instructions"] = "deliver the " + task_id + " slice"
        place = os.path.join(self.root, name)
        Path(place).write_bytes(json.dumps(held, sort_keys=True).encode())
        return place

    def selection(self, **changes):
        held = dict(worker_id="impl-c", role="implementation",
                    participant="baton.impl-c",
                    image_reference="baton-v12-worker:test",
                    image_digest=self.IMAGE, cli_build="2.1.247",
                    network=self.config["network"],
                    credential_sources=os.path.join(self.root, "credential-sources.json"),
                    credentials=["claude=operator-file:w202663-development"],
                    workspace_group=self.config["workspace_group"],
                    task_document=self.task_file())
        held.update(changes)
        return held

    def composing(self, **changes):
        return pool.composed(self.held, **self.selection(**changes))

    def test_the_facts_are_this_builds_own_and_the_instance_binds_the_rest(self):
        from baton_v12.contracts import digest_of_bytes
        from baton_v12.contracts.manifest import check_manifest_structure
        from baton_v12.job_manager import execution_limits
        from tools import next_run_bindings

        answer = self.composing()
        worker = answer["worker"]
        deployment = worker["deployment"]
        manifest = deployment["input_manifest"]
        destination = str(Path(self.held["state_root"]).parent)
        limits = execution_limits.resolved(None)["boundaries"]
        expected = next_run_bindings.deployment_identities(
            image_reference="baton-v12-worker:test", image_digest=self.IMAGE,
            cli_build="2.1.247", network=None, provider_network=self.config["network"],
            runtime_uid=None, turn_seconds=limits["provider_turn"]["seconds"],
            verification_seconds=limits["ordinary_verification"]["seconds"],
            implementer_invocations=1, contextual=False) \
            if False else next_run_bindings.deployment_identities(
            image_reference="baton-v12-worker:test", image_digest=self.IMAGE,
            cli_build="2.1.247", provider_network=self.config["network"],
            runtime_uid=None, turn_seconds=limits["provider_turn"]["seconds"],
            verification_seconds=limits["ordinary_verification"]["seconds"],
            implementer_invocations=1, contextual=False)
        # THE THREE IDENTITIES ARE THE PRODUCT'S, computed the way the standard
        # next-run packet computes them.
        self.assertEqual(deployment["profile_digest"], expected["profile_digest"])
        self.assertEqual(deployment["policy_digest"], expected["policy_digest"])
        self.assertEqual(deployment["adapter_digest"], expected["adapter_digest"])
        self.assertEqual(deployment["profile_name"], "claude-fresh-implementation")
        self.assertEqual(deployment["adapter_name"], "docker-single-worker")
        self.assertEqual(manifest["runtime_profile_digest"],
                         expected["profile_digest"])
        self.assertEqual(manifest["policy_digest"], expected["policy_digest"])
        # THE INSTANCE BINDS THE REST.
        self.assertEqual(deployment["image_digest"], self.IMAGE)
        self.assertEqual(manifest["worker_image_digest"], self.IMAGE)
        self.assertEqual(manifest["work_ref"],
                         {"authority_uuid": self.held["authority_uuid"],
                          "work_id": self.held["authority_uuid"][:8] + "-W1"})
        raw = Path(deployment["task_document"]).read_bytes()
        self.assertEqual(manifest["human_contract"],
                         {"artifact_id": "labels-cli",
                          "media_type": "application/json",
                          "bytes": len(raw),
                          "content_digest": digest_of_bytes(raw),
                          "locator": "artifact://contracts/labels-cli"})
        check_manifest_structure(manifest, "inputManifest")
        self.assertEqual(manifest["outputs"][0]["name"], "proposal")
        self.assertEqual(deployment["credential_profile"],
                         {"claude": {"provider": "operator-file",
                                     "reference": "w202663-development"}})
        self.assertEqual(deployment["credential_slots"], ["claude"])
        self.assertEqual(deployment["workspace_group"],
                         self.config["workspace_group"])
        self.assertEqual(deployment["review_route"], "rview")
        self.assertEqual(deployment["retention_policy_digest"],
                         self.held["retention_policy_digest"])
        self.assertEqual(deployment["workspace_storage"],
                         os.path.join(destination, "state", "workspaces"))
        self.assertEqual(deployment["nominated_source"],
                         os.path.join(destination, "repo", "source-impl-c"))
        self.assertEqual(deployment["launch_home"],
                         os.path.join(destination, "state", "launch"))
        for name in ("authority_uuid", "authority_store", "principal",
                     "launch_role"):
            self.assertNotIn(name, deployment)
        review = self.composing(worker_id="review-c", role="review",
                                participant="baton.reviewer-c")
        self.assertEqual(review["worker"]["deployment"]["review_route"],
                         "integration")

    def test_the_manifest_template_is_an_installed_resource_not_a_dossier(self):
        """Review 2026-11-19T03-36-07Z: the template is shipped beside the
        schema assets and read from the package, equal byte-for-byte in
        content to the published conformance vector's valid document; the
        composer reaches no checkout and no dossier, from any directory."""
        from baton_v12.contracts import frozen
        from tests.manager import input_roots

        corpus = json.loads(input_roots.VECTORS.read_text())
        published = next(one["document"] for one in corpus["valid"]
                         if one["document"].get("schema")
                         == "baton.worker-manifest/input")
        self.assertEqual(frozen.input_manifest_template(), published)
        self.assertTrue(str(frozen._SCHEMA_DIRECTORY).endswith(
            os.path.join("baton_v12", "contracts", "schema")))
        self.assertFalse(hasattr(pool, "VECTORS"))
        elsewhere = os.path.join(self.root, "elsewhere")
        os.makedirs(elsewhere)
        before = os.getcwd()
        os.chdir(elsewhere)
        try:
            answer = self.composing()
        finally:
            os.chdir(before)
        manifest = answer["worker"]["deployment"]["input_manifest"]
        for name in ("credential_policy_digest", "mount_policy_digest",
                     "record_binding", "extensions", "version"):
            if name in published:
                self.assertEqual(manifest[name], published[name], name)

    def test_two_defined_tasks_compose_two_workers_without_an_installation(self):
        first = self.composing(task_document=self.task_file("task-one", "a.json"))
        second = self.composing(worker_id="impl-d", participant="baton.impl-d",
                                task_document=self.task_file("task-two",
                                                             "b.json"))
        self.assertNotEqual(first["manifest_digest"], second["manifest_digest"])
        self.assertEqual(first["identities"], second["identities"])
        self.unchanged()

    def test_a_composed_worker_is_admitted_once_its_source_exists(self):
        answer = self.composing()
        worker = answer["worker"]
        os.makedirs(worker["deployment"]["nominated_source"])
        admitted = self.admitting(worker)
        normalized = stage_execution.held_configuration(self.written())
        self.assertIn("impl-c",
                      [one["worker_id"] for one in normalized["workers"]])
        self.assertEqual(admitted["worker"]["deployment"]["authority_uuid"],
                         self.held["authority_uuid"])

    def test_what_it_refuses_and_that_nothing_is_written(self):
        for changes, said in (
                ({"image_digest": "sha256:short"}, "64 hex"),
                ({"task_document": os.path.join(self.root, "absent.json")},
                 "could not be read"),
                ({"task_document": "relative/task.json"}, "absolute"),
                ({"credentials": ["claude"]}, "slot=provider:reference"),
                ({"credentials": []}, "at least one credential"),
                ({"workspace_group": 0}, "positive group id"),
                ({"worker_id": "../escape"}, None)):
            with self.subTest(changes=changes):
                with self.assertRaises(Exception) as caught:
                    self.composing(**changes)
                if said is not None:
                    self.assertIn(said, str(caught.exception))
        self.unchanged()

    def fresh(self, into, **changes):
        said = io.StringIO()
        try:
            answer = pool.compose(self.place, into=into, stream=said,
                                  **self.selection(**changes))
        except pool.PoolRefusal as refusal:
            return None, str(refusal)
        return answer, said.getvalue()

    def test_an_existing_entry_is_never_replaced_or_followed(self):
        """Review 2026-11-19T02-52-40Z: a dangling symlink at --into was
        followed and reported success. Any existing entry refuses and keeps
        its bytes; a symlink is never followed, resolving or not."""
        occupied = Path(self.root) / "occupied.json"
        occupied.write_text("the operator's own bytes")
        answer, said = self.fresh(str(occupied))
        self.assertIsNone(answer)
        self.assertIn("already exists", said)
        self.assertEqual(occupied.read_text(), "the operator's own bytes")
        dangling = Path(self.root) / "dangling.json"
        elsewhere = Path(self.root) / "elsewhere.json"
        dangling.symlink_to(elsewhere)
        answer, said = self.fresh(str(dangling))
        self.assertIsNone(answer)
        self.assertIn("already exists", said)
        self.assertTrue(dangling.is_symlink())
        self.assertFalse(elsewhere.exists())
        resolving = Path(self.root) / "resolving.json"
        resolving.symlink_to(occupied)
        answer, said = self.fresh(str(resolving))
        self.assertIsNone(answer)
        self.assertEqual(occupied.read_text(), "the operator's own bytes")
        directory = Path(self.root) / "a-directory.json"
        directory.mkdir()
        answer, said = self.fresh(str(directory))
        self.assertIsNone(answer)
        self.assertTrue(directory.is_dir())
        self.unchanged()

    def test_a_concurrently_occupied_path_refuses_at_the_write(self):
        """The check and the write are one exclusive operation: a file that
        appears after composition and before the write is refused, and its
        bytes stand."""
        target = Path(self.root) / "raced.json"
        real = pool._written_fresh

        def racing(place, body):
            Path(place).write_text("arrived first")
            return real(place, body)

        with mock.patch.object(pool, "_written_fresh", racing):
            answer, said = self.fresh(str(target))
        self.assertIsNone(answer)
        self.assertIn("already exists", said)
        self.assertEqual(target.read_text(), "arrived first")

    def test_the_command_line_writes_one_fresh_file_and_refuses_a_second(self):
        into = os.path.join(self.root, "composed", "impl-c.json")
        argv = [pool.VERB_COMPOSE, "--deployment", self.place,
                "--worker-id", "impl-c", "--role", "implementation",
                "--participant", "baton.impl-c",
                "--image-reference", "baton-v12-worker:test",
                "--image-digest", self.IMAGE, "--cli-build", "2.1.247",
                "--network", self.config["network"],
                "--credential-sources", os.path.join(self.root, "credential-sources.json"),
                "--credential", "claude=operator-file:w202663-development",
                "--workspace-group", str(self.config["workspace_group"]),
                "--task-document", self.task_file(), "--into", into]
        said = io.StringIO()
        self.assertEqual(pool.main(argv, stream=said), 0, said.getvalue())
        written = json.loads(Path(into).read_text())
        self.assertEqual(written["worker_id"], "impl-c")
        self.assertEqual(written["deployment"]["profile_name"],
                         "claude-fresh-implementation")
        self.assertIn("the instance's configuration was not changed",
                      said.getvalue())
        self.unchanged()
        said = io.StringIO()
        self.assertEqual(pool.main(argv, stream=said), 2)
        self.assertIn("already exists", said.getvalue())
        from tools import stack_command

        self.assertIn("pool", stack_command.COMMANDS)


def _work_or_none(authority, work_id):
    try:
        return authority.project_work(work_id)
    except Exception:                                        # noqa: BLE001
        return None


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
