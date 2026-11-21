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
from tools import single_worker
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


class ComposingCase(PoolCase):
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

    RECORD = ("work/records/2026/08/finding-v12-work-tags/findings/"
              "finding-v12-work-label-protocol-cli")

    def record_in(self, checkout, finding="# Finding\n", plan="# Plan\n"):
        place = Path(checkout, self.RECORD)
        place.mkdir(parents=True, exist_ok=True)
        (place / "FINDING.md").write_text(finding)
        (place / "PLAN.md").write_text(plan)
        return str(place)

    def selection(self, **changes):
        self.record_in(self.checkout)
        held = dict(worker_id="impl-c", role="implementation",
                    participant="baton.impl-c",
                    image_reference="baton-v12-worker:test",
                    image_digest=self.IMAGE, cli_build="2.1.247",
                    network=self.config["network"],
                    credential_sources=os.path.join(self.root, "credential-sources.json"),
                    credentials=["claude=operator-file:w202663-development"],
                    workspace_group=self.config["workspace_group"],
                    task_document=self.task_file(),
                    record_path=self.RECORD, checkout=self.checkout,
                    now="2026-11-19T06:30:00.000Z",
                    # THE TOPOLOGY IS SAID OUT LOUD (M385234). These cases are
                    # about everything else the verb composes, so they select
                    # legacy explicitly; the selecting cases are their own class.
                    legacy_layout=True)
        held.update(changes)
        return held

    def composing(self, **changes):
        return pool.composed(self.held, **self.selection(**changes))


class ComposingAWorkerForThisInstance(ComposingCase):
    """Everything the verb binds and derives, for an explicitly legacy worker."""

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
        # THE STRUCTURE IS THE PUBLISHED DOCUMENT'S; the provenance members
        # are bound to this instance (the provenance case holds those).
        for name in ("schema", "version", "extensions", "assignment_contract"):
            self.assertEqual(manifest[name], published[name], name)
        self.assertEqual([one["name"] for one in manifest["outputs"]],
                         [one["name"] for one in published["outputs"]])

    def test_every_provenance_member_is_bound_and_none_is_a_specimen(self):
        """Review 2026-11-19T06-06-42Z: the template's specimen record,
        retention, policy, credential, role, toolchain, id and clock values
        used to travel as this run's provenance. Each is now the digest of the
        product document that governs it, or the selection the operator
        named, and a specimen refuses."""
        import hashlib

        from baton_v12.contracts import digest, frozen
        from tools import next_run_bindings

        answer = self.composing()
        manifest = answer["worker"]["deployment"]["input_manifest"]
        template = frozen.input_manifest_template()
        for name in next_run_bindings.BOUND_MEMBERS:
            self.assertNotEqual(manifest[name], template[name], name)
        self.assertEqual(manifest["retention_policy_digest"],
                         self.held["retention_policy_digest"])
        record = Path(self.checkout, self.RECORD)
        self.assertEqual(manifest["record_binding"], {
            "root": "baton-repository", "path": self.RECORD,
            "finding_digest": "sha256:" + hashlib.sha256(
                (record / "FINDING.md").read_bytes()).hexdigest(),
            "plan_digest": "sha256:" + hashlib.sha256(
                (record / "PLAN.md").read_bytes()).hexdigest()})
        self.assertEqual(manifest["manifest_id"], "input-manifest-impl-c")
        self.assertEqual(manifest["created_at"], "2026-11-19T06:30:00.000Z")
        self.assertEqual(manifest["credential_policy_digest"], digest(
            {"schema": "baton.worker-credential-policy/1",
             "profile": {"claude": {"provider": "operator-file",
                                    "reference": "w202663-development"}}}))
        self.assertEqual(manifest["toolchain_digest"], digest(
            {"schema": "baton.worker-toolchain/1",
             "image_reference": "baton-v12-worker:test",
             "image_digest": self.IMAGE, "cli_build": "2.1.247"}))
        self.assertEqual(manifest["network_policy_digest"], digest(
            {"schema": "baton.worker-network-policy/1", "engine": "docker",
             "network": self.config["network"]}))
        # THE ROLE'S OWN DECLARATION: implementation and review differ.
        review = self.composing(worker_id="review-c", role="review",
                                participant="baton.reviewer-c")
        self.assertNotEqual(
            manifest["role_instructions_digest"],
            review["worker"]["deployment"]["input_manifest"]
            ["role_instructions_digest"])
        for name in ("tool_policy_digest", "resource_policy_digest",
                     "mount_policy_digest", "credential_policy_digest"):
            self.assertEqual(manifest[name], review["worker"]["deployment"]
                             ["input_manifest"][name], name)
        # THE RECORD IS A SELECTION: no record, no checkout, no dossier.
        for changes, said in (({"record_path": "/abs/olute"}, "relative"),
                              ({"record_path": "work/records/absent"},
                               "no readable FINDING.md"),
                              ({"checkout": None}, "no checkout")):
            with self.subTest(changes=changes):
                with self.assertRaises(pool.PoolRefusal) as caught:
                    kept = os.environ.get("X")
                    if "checkout" in changes:
                        from unittest import mock as _mock
                        with _mock.patch("tools.build_stamp.checkout",
                                         lambda start=None: None):
                            self.composing(**changes)
                    else:
                        self.composing(**changes)
                    del kept
                self.assertIn(said, str(caught.exception))
        self.unchanged()

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
        self.record_in(self.checkout)
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
                "--task-document", self.task_file(),
                "--record", self.RECORD, "--checkout", self.checkout,
                "--into", into, "--legacy-verifier-layout"]
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


class ComposingAWorkerForASelectedTemplate(ComposingCase):
    """W385331 (T321608 M385374, the composer gap): the template is a
    selection of this verb. Omitted, nothing changes; a handoff-capable one
    derives the declared outputs and the role-instructions identity from the
    template that owns them; one this build does not carry is refused."""

    HANDOFF = "baton.v12.job-template.implementation-review/3"
    SECOND = "baton.v12.job-template.implementation-review/2"
    UNKNOWN = "baton.v12.job-template.implementation-review/9"

    def outputs_of(self, answer):
        return [(one["name"], one["type"], one["required"])
                for one in answer["worker"]["deployment"]["input_manifest"]
                ["outputs"]]

    def instructions_of(self, answer):
        return answer["worker"]["deployment"]["input_manifest"][
            "role_instructions_digest"]

    def test_the_default_is_byte_identical_whether_omitted_or_named(self):
        omitted = self.composing()
        named = self.composing(template_version=pool.TEMPLATE_VERSION)
        self.assertEqual(omitted["worker"], named["worker"])
        self.assertEqual(self.outputs_of(omitted),
                         [("proposal", "git-change-proposal", True)])
        self.assertEqual(omitted["template"], pool.TEMPLATE_VERSION)
        self.assertEqual(omitted["declared"], ["proposal"])

    def test_a_handoff_capable_template_declares_its_roles_union_optional(self):
        from baton_v12.contracts import job_input_identity
        from baton_v12.contracts.manifest import check_manifest_structure

        legacy = self.composing()
        answer = self.composing(template_version=self.HANDOFF)
        self.assertEqual(answer["template"], self.HANDOFF)
        self.assertEqual(self.outputs_of(answer), [
            ("proposal", "git-change-proposal", False),
            ("handoff", "directory-result", False),
            ("findings", "directory-result", False),
            ("logs", "directory-result", False),
            ("response", "directory-result", False)])
        manifest = answer["worker"]["deployment"]["input_manifest"]
        # EVERY DECLARATION IS COMPOSED FROM THE TEMPLATE'S OWN SPECIMEN: the
        # same constraints, its own name and path.
        for one in manifest["outputs"]:
            self.assertEqual(one["path"], one["name"])
            self.assertEqual(one["constraints"],
                             manifest["outputs"][0]["constraints"])
        check_manifest_structure(manifest, "inputManifest",
                                 what="the composed /3 manifest")
        # THE ROLE-INSTRUCTIONS IDENTITY IS THE SELECTED TEMPLATE'S, so a /3
        # worker and a /1 worker are two different declarations, and so are
        # their Job input identities.
        self.assertNotEqual(self.instructions_of(answer),
                            self.instructions_of(legacy))
        self.assertNotEqual(
            job_input_identity(manifest),
            job_input_identity(
                legacy["worker"]["deployment"]["input_manifest"]))
        # AND THE REVIEW ROLE OF THE SAME TEMPLATE DECLARES THE SAME UNION.
        review = self.composing(template_version=self.HANDOFF,
                                worker_id="review-c", role="review",
                                participant="baton.review-c")
        self.assertEqual([one[0] for one in self.outputs_of(review)],
                         [one[0] for one in self.outputs_of(answer)])
        self.assertNotEqual(self.instructions_of(review),
                            self.instructions_of(answer))

    def test_a_baseline_template_other_than_the_default_keeps_the_legacy_declaration(self):
        """`/2` is bound to the baseline contract: the proven one-output
        declaration stands, and only the role-instructions identity names
        the selected version."""
        legacy = self.composing()
        second = self.composing(template_version=self.SECOND)
        self.assertEqual(self.outputs_of(second), self.outputs_of(legacy))
        self.assertEqual(second["template"], self.SECOND)
        self.assertNotEqual(self.instructions_of(second),
                            self.instructions_of(legacy))

    def test_an_unsupported_template_is_refused_by_name_before_anything(self):
        with self.assertRaises(pool.PoolRefusal) as caught:
            self.composing(template_version=self.UNKNOWN)
        self.assertIn("carries the job templates", str(caught.exception))
        self.assertIn(self.UNKNOWN.rsplit("/", 1)[0] + "/9",
                      str(caught.exception))
        with self.assertRaises(pool.PoolRefusal):
            self.composing(template_version="")
        self.unchanged()

    def argv(self, into, *extra):
        return [pool.VERB_COMPOSE, "--deployment", self.place,
                "--worker-id", "impl-c", "--role", "implementation",
                "--participant", "baton.impl-c",
                "--image-reference", "baton-v12-worker:test",
                "--image-digest", self.IMAGE, "--cli-build", "2.1.247",
                "--network", self.config["network"],
                "--credential-sources",
                os.path.join(self.root, "credential-sources.json"),
                "--credential", "claude=operator-file:w202663-development",
                "--workspace-group", str(self.config["workspace_group"]),
                "--task-document", self.task_file(),
                "--record", self.RECORD, "--checkout", self.checkout,
                "--into", into, "--legacy-verifier-layout", *extra]

    def test_the_command_line_selects_the_template_and_says_so(self):
        self.record_in(self.checkout)
        into = os.path.join(self.root, "composed", "impl-c-3.json")
        said = io.StringIO()
        self.assertEqual(pool.main(self.argv(into, "--template", self.HANDOFF),
                                   stream=said), 0, said.getvalue())
        written = json.loads(Path(into).read_text())
        self.assertEqual(
            [one["name"] for one in
             written["deployment"]["input_manifest"]["outputs"]],
            ["proposal", "handoff", "findings", "logs", "response"])
        self.assertIn("template  " + self.HANDOFF, said.getvalue())
        self.assertIn("declaring proposal, handoff, findings, logs, response",
                      said.getvalue())
        self.unchanged()

    def test_the_command_line_refuses_an_unsupported_template_and_writes_nothing(self):
        self.record_in(self.checkout)
        into = os.path.join(self.root, "composed", "impl-c-9.json")
        said = io.StringIO()
        self.assertEqual(pool.main(self.argv(into, "--template", self.UNKNOWN),
                                   stream=said), 2)
        self.assertIn("refused:", said.getvalue())
        self.assertIn("carries the job templates", said.getvalue())
        self.assertFalse(os.path.lexists(into))
        self.unchanged()


class ComposingAWorkerThatSelectsTheVerifierLayout(ComposingCase):
    """W321608 native-labels-4 (T321608 M385233, M385234): the worker image
    built from e670e624 carries W325695's verifier-layout marker, and this verb
    wrote `/4` unconditionally -- so no `/run/baton/verifier-layout.json` was
    delivered and the adapter refused before the provider, reported as an
    anonymous `agent` fault after the Work had been admitted and claimed.

    THE CHAIN THESE CASES PROVE, deterministically and offline: the verb emits
    the supported `/6` deployment for a selected marker and refuses a missing
    or mismatched selection with a sentence an operator can act on; the
    instance admits that worker and the manager's validator still accepts it;
    the serving start's per-worker preflight (`stage_execution` calls
    `single_worker.worker_preflight` for every configured worker) materializes
    the layout selection under the manager's own launch home before any
    runtime exists; and the worker's own reader accepts exactly that document
    beside the shipped marker, and refuses before the provider without it.

    WHAT IS NOT PROVED HERE: that any particular image was built with that
    marker. The verb does not inspect images -- the marker is an operand read
    from the build's own recipe input by the operator who selected the image
    (`source_boundary.compose_verifier_layout`) -- so a marker image selected
    as legacy still refuses inside the worker; what changed is that the choice
    is now recorded in the deployment rather than defaulted.
    """

    def marker(self, **changed):
        from baton_v12.worker_manager import source_boundary
        held = source_boundary.image_layout_marker()
        held.update(changed)
        return held

    def selecting(self, **changes):
        return self.composing(legacy_layout=False, verifier_layout=self.marker(),
                              **changes)

    def refusing(self, **changes):
        with self.assertRaises(pool.PoolRefusal) as caught:
            self.composing(**changes)
        self.unchanged()
        return str(caught.exception)

    def test_no_selection_is_refused_before_anything_is_written(self):
        said = self.refusing(legacy_layout=False)
        for wanted in ("--verifier-layout", "--legacy-verifier-layout",
                       "before the provider", "Nothing was changed"):
            self.assertIn(wanted, said)
        into = os.path.join(self.root, "composed", "unselected.json")
        with self.assertRaises(pool.PoolRefusal):
            with open(os.devnull, "w") as quiet:
                pool.compose(self.place, into=into, stream=quiet,
                             **self.selection(legacy_layout=False))
        self.assertFalse(os.path.lexists(into))
        self.unchanged()

    def test_both_selections_refuse(self):
        self.assertIn("not both", self.refusing(legacy_layout=True,
                                                verifier_layout=self.marker()))

    def test_the_marker_selects_the_supported_layout_deployment(self):
        from baton_v12.worker_manager import source_boundary

        answer = self.selecting()
        deployment = answer["worker"]["deployment"]
        self.assertEqual(deployment["schema"], single_worker.LAYOUT_CONFIG_SCHEMA)
        self.assertEqual(deployment["verifier_layout"],
                         source_boundary.image_layout_marker())
        self.assertIsNone(deployment["provider_context"])
        self.assertEqual(answer["layout"],
                         {"selection": "trusted",
                          "layout_digest": source_boundary.layout_digest()})
        # `/6` IS `/4` PLUS THE TWO MEMBERS, and nothing else moves.
        legacy = self.composing()["worker"]["deployment"]
        self.assertEqual(legacy["schema"], single_worker.CONFIG_SCHEMA)
        self.assertEqual(
            {name: value for name, value in deployment.items()
             if name not in ("schema", "verifier_layout", "provider_context")},
            {name: value for name, value in legacy.items() if name != "schema"})

    def test_the_legacy_selection_is_the_unchanged_legacy_document(self):
        answer = self.composing()
        deployment = answer["worker"]["deployment"]
        self.assertEqual(deployment["schema"], single_worker.CONFIG_SCHEMA)
        self.assertNotIn("verifier_layout", deployment)
        self.assertNotIn("provider_context", deployment)
        self.assertEqual(answer["layout"],
                         {"selection": "legacy", "layout_digest": None})

    def test_a_marker_from_another_topology_or_shape_refuses(self):
        from baton_v12.worker_manager import source_boundary

        mine = source_boundary.layout_digest()
        partial = self.marker()
        del partial["mode"]
        for marker, wanted in (
                (self.marker(layout_digest="0" * 64),
                 ("declares verifier topology", "this build composes", mine)),
                (self.marker(schema="baton.v12.verifier-layout-marker/2"),
                 ("this build reads", source_boundary.MARKER_SCHEMA)),
                (partial, ("missing mode",)),
                (self.marker(image="sha256:" + "f" * 64), ("unexpected image",)),
                (self.marker(roots={}), ("names roots", "layout_digest")),
                ("marker", ("marker document",)),
                (None, ("--verifier-layout",))):
            with self.subTest(marker=marker):
                said = self.refusing(legacy_layout=False, verifier_layout=marker)
                for one in wanted:
                    self.assertIn(one, said)

    def test_the_command_line_selects_either_topology(self):
        from baton_v12.worker_manager import source_boundary

        self.record_in(self.checkout)
        marker = os.path.join(self.root, "verifier-layout-marker.json")
        Path(marker).write_text(json.dumps(self.marker()))
        argv = [pool.VERB_COMPOSE, "--deployment", self.place,
                "--worker-id", "impl-c", "--role", "implementation",
                "--participant", "baton.impl-c",
                "--image-reference", "baton-v12-worker:test",
                "--image-digest", self.IMAGE, "--cli-build", "2.1.247",
                "--network", self.config["network"],
                "--credential-sources", os.path.join(self.root, "credential-sources.json"),
                "--credential", "claude=operator-file:w202663-development",
                "--workspace-group", str(self.config["workspace_group"]),
                "--task-document", self.task_file(),
                "--record", self.RECORD, "--checkout", self.checkout]
        trusted = os.path.join(self.root, "composed", "trusted.json")
        said = io.StringIO()
        self.assertEqual(pool.main(argv + ["--into", trusted, "--verifier-layout", marker],
                                   stream=said), 0, said.getvalue())
        written = json.loads(Path(trusted).read_text())
        self.assertEqual(written["deployment"]["schema"],
                         single_worker.LAYOUT_CONFIG_SCHEMA)
        self.assertEqual(written["deployment"]["verifier_layout"],
                         source_boundary.image_layout_marker())
        self.assertIn("layout    trusted " + source_boundary.layout_digest(),
                      said.getvalue())
        legacy = os.path.join(self.root, "composed", "legacy.json")
        said = io.StringIO()
        self.assertEqual(pool.main(argv + ["--into", legacy, "--legacy-verifier-layout"],
                                   stream=said), 0, said.getvalue())
        self.assertEqual(json.loads(Path(legacy).read_text())["deployment"]["schema"],
                         single_worker.CONFIG_SCHEMA)
        self.assertIn("layout    legacy (explicitly selected", said.getvalue())
        unselected = os.path.join(self.root, "composed", "unselected.json")
        said = io.StringIO()
        self.assertEqual(pool.main(argv + ["--into", unselected], stream=said), 2)
        self.assertIn("--legacy-verifier-layout", said.getvalue())
        self.assertFalse(os.path.lexists(unselected))
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                pool.main(argv + ["--into", unselected, "--verifier-layout",
                                  marker, "--legacy-verifier-layout"],
                          stream=io.StringIO())
        self.unchanged()

    def admitted_selecting_worker(self):
        worker = self.selecting()["worker"]
        os.makedirs(worker["deployment"]["nominated_source"])
        self.admitting(worker)
        normalized = stage_execution.held_configuration(self.written(),
                                                        checkout=self.checkout)
        return next(one for one in normalized["workers"]
                    if one["worker_id"] == "impl-c")

    def test_the_selecting_worker_is_admitted_and_the_manager_accepts_it(self):
        from baton_v12.worker_manager import source_boundary

        found = self.admitted_selecting_worker()
        self.assertEqual(found["deployment"]["schema"],
                         single_worker.LAYOUT_CONFIG_SCHEMA)
        self.assertEqual(found["deployment"]["verifier_layout"],
                         source_boundary.image_layout_marker())
        self.assertEqual(found["deployment"]["launch_role"], "implementation")

    def delivered(self, label):
        """The serving start's own per-worker preflight, for the admitted
        selecting worker: what `stage_execution.operations_from` runs for every
        configured worker before any runtime exists."""
        from .test_single_worker import Engine
        from tests.job_manager import fixtures

        found = self.admitted_selecting_worker()
        # The install creates the instance's state roots; this instance was
        # only prepared, so the roots the preflight holds are made here.
        for name in ("workspace_storage", "launch_home", "credential_home"):
            os.makedirs(found["deployment"][name], exist_ok=True)
        engine = Engine()
        _job, control = self.stores(label)
        single_worker.worker_preflight(
            found["deployment"], control,
            credential_provider=lambda provider, reference: self.secret,
            engine_run=engine)
        place = os.path.join(found["deployment"]["launch_home"],
                             "verifier-layout", "verifier-layout.json")
        self.assertEqual(engine.starts, [])
        return found, control, place

    def test_the_serving_preflight_delivers_the_selection_before_any_runtime(self):
        from baton_v12.worker_manager import source_boundary, workspaces

        found, control, place = self.delivered("w321608-layout-preflight")
        self.assertTrue(os.path.isfile(place), place)
        document = json.loads(Path(place).read_bytes())
        self.assertEqual(document["schema"], source_boundary.LAYOUT_SCHEMA)
        self.assertEqual(document["layout_digest"], source_boundary.layout_digest())
        self.assertEqual(document["image_digest"], self.IMAGE)
        self.assertEqual(document["profile_digest"],
                         found["deployment"]["profile_digest"])
        identity = workspaces.identity_for(
            single_worker.configured_workspace_group(control))
        self.assertEqual((document["uid"], document["gid"]),
                         (identity.uid, identity.gid))
        self.assertFalse(os.access(place, os.W_OK))

    def adapter(self):
        """The worker's own reader, imported the way its image lays modules
        out: the adapter beside the shared contract modules, both top-level."""
        here = Path(__file__).resolve()
        added = [str(here.parents[3] / "worker"),
                 str(here.parents[2] / "src" / "baton_v12")]
        for one in reversed(added):
            sys.path.insert(0, one)
        try:
            import claude_agent
        finally:
            for one in added:
                sys.path.remove(one)
        return claude_agent

    def test_the_worker_reads_the_delivered_selection_and_refuses_without_it(self):
        from baton_v12.worker_manager import source_boundary

        _found, _control, place = self.delivered("w321608-layout-worker")
        claude_agent = self.adapter()
        shipped = json.loads(
            (Path(__file__).resolve().parents[3] / "worker"
             / "verifier-layout-marker.json").read_bytes())
        # THE MARKER THE OPERATOR NAMES IS THE ONE THE RECIPE SHIPS.
        self.assertEqual(shipped, source_boundary.image_layout_marker())
        agent = claude_agent.ClaudeAgent.__new__(claude_agent.ClaudeAgent)
        agent._seen = {}
        read = agent._selected_layout(place=place, marker=shipped)
        self.assertEqual(read, json.loads(Path(place).read_bytes()))
        self.assertEqual(read["roots"], claude_agent.ClaudeAgent.LAYOUT_ROOTS)
        absent = os.path.join(self.root, "never-delivered.json")
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            agent._selected_layout(place=absent, marker=shipped)
        self.assertIn("no trusted layout selection was delivered",
                      str(caught.exception))
        self.assertIn("refuses before the provider", str(caught.exception))


def _work_or_none(authority, work_id):
    try:
        return authority.project_work(work_id)
    except Exception:                                        # noqa: BLE001
        return None


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
