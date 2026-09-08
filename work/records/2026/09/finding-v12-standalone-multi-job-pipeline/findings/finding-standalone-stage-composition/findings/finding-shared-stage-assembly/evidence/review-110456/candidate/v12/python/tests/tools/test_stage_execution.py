"""W103083: the standalone stage deployment's configuration boundary.

`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/
finding-standalone-stage-composition/findings/finding-shared-stage-assembly/`.

WHAT THIS FILE OWNS, AND IT IS THE FIRST OF THREE CHECKPOINTS. The serving
factory is wired here: one closed document, three roles over one Authority, and
every refusal that must happen while nothing has been opened. The composed
lifecycle and the restart cutpoint are the checkpoints after it.

THE WORKER HALF IS NOT RE-PROVED HERE. `single_worker`'s own suite owns the
launch document, the credential boundary and the mount posture, and this
deployment calls that module's parameterized halves rather than a copy of them
-- so a second set of assertions over the same rules would be a second place
for them to drift.
"""

import copy
import json
import os
import pathlib
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import review_driver

from tools import stage_execution

from tests.job_manager.fixtures import NOW, UUID, WORK_A
from tests.job_manager.test_review_driver import DriverCase, REVIEWER, WRITER

from .test_single_worker import SingleWorkerCase


REPOSITORY = pathlib.Path(__file__).resolve().parents[4]
VECTORS = (REPOSITORY / "work" / "records" / "2026" / "08"
           / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")


def _vector(schema):
    """One published manifest vector, so this suite composes no second idea of
    a valid document."""
    for case in json.loads(VECTORS.read_text(encoding="utf-8"))["valid"]:
        document = case.get("document")
        if isinstance(document, dict) and document.get("schema") == schema:
            return copy.deepcopy(document)
    raise AssertionError(f"the published vectors carry no {schema}")


class StageCase(SingleWorkerCase):
    """One valid single-worker document, reused as three configured roles.

    Reusing `SingleWorkerCase` rather than rebuilding its fixture is the same
    decision the module makes: the launch document's rules have one owner, and
    a test that hand-rolled a second valid document would be asserting against
    its own idea of one.
    """

    def setUp(self):
        super().setUp()
        self.integration_store = os.path.join(self.root, "integration.sqlite3")
        self.state_root = os.path.join(self.root, "state")
        # THE FIXTURE OWNS ITS OWN "CHECKOUT". This suite's disk-backed root
        # has to sit inside the distribution -- `/tmp` is a tmpfs and a
        # workspace may not live there -- so a case that used the real
        # repository root would be refused for the fixture's own reason rather
        # than the one it is asserting. The rule is proved against a checkout
        # this case controls, and `_checkout` is proved separately.
        self.checkout = os.path.join(self.root, "checkout")
        os.makedirs(self.checkout)

    def worker(self, role, *, participant=None, principal=None, **members):
        deployment = copy.deepcopy(self.config)
        if participant is not None:
            deployment["participant"] = participant
        if principal is not None:
            deployment["principal"] = principal
        deployment.update(members)
        return {"worker_id": f"{role}-worker", "role": role,
                "deployment": deployment}

    def document(self, **members):
        given = {
            "schema": stage_execution.CONFIG_SCHEMA,
            "authority_store": self.authority_path,
            "authority_uuid": self.config["authority_uuid"],
            "integration_store": self.integration_store,
            "state_root": self.state_root,
            "pool_generation": 1,
            "job_work_id": "work-1",
            "review_work_id": "work-1",
            "canonical_target_id": "target-1",
            "checkpoint_profile": "git",
            "integration_profile": {
                "profile_kind": "git", "profile_version": 1,
                "integrator_participant": "baton.integrator",
                "instructions_digest": "sha256:" + "e" * 64},
            "retention_policy_digest": "sha256:" + "5" * 64,
            "retention_disposition": "retain",
            "workers": [
                self.worker("implementation"),
                self.worker("review", participant="baton.reviewer",
                            principal="reviewer-principal"),
                self.worker("integration", participant="baton.integrator",
                            principal="integrator-principal")]}
        given.update(members)
        return given

    def refused(self, **members):
        with self.assertRaises(ContractRefusal) as caught:
            self.held(**members)
        return caught.exception

    def held(self, **members):
        return stage_execution.held_configuration(self.document(**members),
                                                  checkout=self.checkout)


class TheDeploymentDocumentIsClosed(StageCase):

    def test_a_well_formed_document_is_held_with_its_three_roles(self):
        given = self.held()
        self.assertEqual([one["role"] for one in given["workers"]],
                         list(stage_execution.ROLES))
        self.assertEqual(given["schema"], stage_execution.CONFIG_SCHEMA)

    def test_another_generation_of_the_schema_is_refused(self):
        held = self.refused(schema="baton.v12.stage-execution-deployment/2")
        self.assertIn(stage_execution.CONFIG_SCHEMA, held.message)

    def test_an_unknown_or_missing_member_is_refused(self):
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(
                dict(self.document(), invented="value"),
                checkout=self.checkout)
        short = self.document()
        del short["canonical_target_id"]
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(short, checkout=self.checkout)

    def test_a_pool_generation_counts_from_one(self):
        for generation in (0, -1, True, "1", None):
            with self.subTest(generation=generation):
                self.refused(pool_generation=generation)


class TheConfigurationCarriesNoCredentialBytes(StageCase):

    def test_a_bearer_anywhere_in_the_document_is_refused(self):
        """Walked rather than spot-checked: the member that matters is
        whichever one somebody added last."""
        for where, mutate in (
                ("root", lambda one: dict(one, bearer="not-a-credential")),
                ("profile", lambda one: dict(
                    one, integration_profile=dict(
                        one["integration_profile"], token="x"))),
                ("worker", lambda one: dict(
                    one, workers=[dict(one["workers"][0],
                                       deployment=dict(
                                           one["workers"][0]["deployment"],
                                           password="x"))]
                    + one["workers"][1:]))):
            with self.subTest(where=where):
                with self.assertRaises(ContractRefusal) as caught:
                    stage_execution.held_configuration(
                        mutate(self.document()), checkout=self.checkout)
                self.assertEqual(caught.exception.category, "policy")

    def test_the_secret_sweep_reaches_into_nested_lists(self):
        with self.assertRaises(ContractRefusal):
            stage_execution.held_configuration(
                dict(self.document(),
                     workers=[{"worker_id": "w", "role": "implementation",
                               "deployment": {"nested": [{"secret": "x"}]}}]),
                checkout=self.checkout)


class OneJobsReviewIsOverItsOwnImplementation(StageCase):

    def test_a_review_stage_naming_another_work_is_refused(self):
        held = self.refused(review_work_id="work-2")
        self.assertIn("one Job's review is over its own implementation",
                      held.message)
        self.assertEqual(held.category, "refused")

    def test_the_matching_case_is_held(self):
        self.assertEqual(self.held(job_work_id="work-9",
                                   review_work_id="work-9")["job_work_id"],
                         "work-9")


class IndependenceIsRefusedBeforeAnythingIsOpened(StageCase):

    def test_one_participant_cannot_implement_and_review(self):
        held = self.refused(workers=[
            self.worker("implementation"),
            self.worker("review", principal="reviewer-principal"),
            self.worker("integration", participant="baton.integrator",
                        principal="integrator-principal")])
        self.assertIn("not one the implementer performs", held.message)
        self.assertEqual(held.category, "policy")

    def test_one_principal_cannot_implement_and_review(self):
        held = self.refused(workers=[
            self.worker("implementation"),
            self.worker("review", participant="baton.reviewer"),
            self.worker("integration", participant="baton.integrator",
                        principal="integrator-principal")])
        self.assertIn("not one the implementer performs", held.message)

    def test_the_integrator_may_share_neither_rule_forbids(self):
        """Independence is named for the pair that needs it, not asserted at
        large: an integrator sharing an identity with the implementer is a
        deployment choice, and this leaf does not invent a rule for it."""
        self.held(workers=[
            self.worker("implementation"),
            self.worker("review", participant="baton.reviewer",
                        principal="reviewer-principal"),
            self.worker("integration")])


class EveryStageHasExactlyOneWorker(StageCase):

    def test_a_missing_stage_is_refused(self):
        held = self.refused(workers=[
            self.worker("implementation"),
            self.worker("review", participant="baton.reviewer",
                        principal="reviewer-principal")])
        self.assertIn("integration", held.message)

    def test_two_workers_for_one_stage_are_refused(self):
        held = self.refused(workers=[
            self.worker("implementation"),
            self.worker("implementation", participant="baton.second",
                        principal="second-principal"),
            self.worker("review", participant="baton.reviewer",
                        principal="reviewer-principal"),
            self.worker("integration", participant="baton.integrator",
                        principal="integrator-principal")])
        self.assertIn("exactly one", held.message)

    def test_a_role_this_deployment_does_not_serve_is_refused(self):
        held = self.refused(workers=[
            self.worker("tuning"),
            self.worker("review", participant="baton.reviewer",
                        principal="reviewer-principal"),
            self.worker("integration", participant="baton.integrator",
                        principal="integrator-principal")])
        self.assertIn("not a stage role", held.message)

    def test_a_worker_naming_another_authority_is_refused(self):
        held = self.refused(workers=[
            self.worker("implementation",
                        authority_uuid="f" * 32),
            self.worker("review", participant="baton.reviewer",
                        principal="reviewer-principal"),
            self.worker("integration", participant="baton.integrator",
                        principal="integrator-principal")])
        self.assertEqual(held.category, "refused")
        self.assertIn("configured for", held.message)


class MutableStateStaysOutsideTheCheckout(StageCase):

    def test_a_store_inside_the_checkout_is_refused(self):
        inside = os.path.join(self.checkout, "state.db")
        held = self.refused(integration_store=inside)
        self.assertIn("inside the checkout", held.message)
        self.assertEqual(held.category, "policy")

    def test_a_state_root_inside_the_checkout_is_refused(self):
        inside = os.path.join(self.checkout, "state")
        self.assertIn("inside the checkout",
                      self.refused(state_root=inside).message)

    def test_a_worker_workspace_inside_the_checkout_is_refused(self):
        inside = os.path.join(self.checkout, "storage")
        held = self.refused(workers=[
            self.worker("implementation", workspace_storage=inside),
            self.worker("review", participant="baton.reviewer",
                        principal="reviewer-principal"),
            self.worker("integration", participant="baton.integrator",
                        principal="integrator-principal")])
        self.assertIn("inside the checkout", held.message)

    def test_a_relative_or_traversing_path_is_refused(self):
        for place in ("state", "/a/../b", ""):
            with self.subTest(place=place):
                self.refused(state_root=place)


class TheAcceptedIntegrationSessionsAreProvedBeforePublication(StageCase):

    class _Session:
        participant = "baton.actor"

        def __init__(self, *verbs):
            for verb in verbs:
                setattr(self, verb, lambda *a, **k: None)

    def sessions(self, **replaced):
        held = {"verification": self._Session("verify"),
                "review": self._Session("review"),
                "approval": self._Session("approve"),
                "integrator": self._Session("integrate", "receipt"),
                "publisher": self._Session(
                    *stage_execution.PUBLISHER_CAPABILITIES)}
        held.update(replaced)
        return held

    def test_the_complete_set_is_accepted(self):
        held = self.sessions()
        self.assertIs(stage_execution._sessions(held), held)

    def test_a_missing_session_refuses(self):
        for name in stage_execution.RECEIPT_SESSIONS + ("publisher",):
            with self.subTest(name=name):
                with self.assertRaises(ContractRefusal) as caught:
                    stage_execution._sessions(self.sessions(**{name: None}))
                self.assertEqual(caught.exception.category, "refused")
                self.assertIn(name, caught.exception.message)

    def test_a_session_without_its_verb_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution._sessions(
                self.sessions(integrator=self._Session("integrate")))
        self.assertIn("receipt", caught.exception.message)
        # THE PUBLISHER IS REACHED EARLIEST OF ALL, so a deployment missing one
        # of its three would discover it with a frozen result it can never
        # publish.
        for verb in stage_execution.PUBLISHER_CAPABILITIES:
            partial = [one for one in stage_execution.PUBLISHER_CAPABILITIES
                       if one != verb]
            with self.subTest(verb=verb):
                with self.assertRaises(ContractRefusal) as caught:
                    stage_execution._sessions(
                        self.sessions(publisher=self._Session(*partial)))
                self.assertIn(verb, caught.exception.message)

    def test_a_session_without_a_participant_refuses(self):
        nameless = self._Session("verify")
        nameless.participant = None
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution._sessions(self.sessions(verification=nameless))
        self.assertIn("participant", caught.exception.message)


class ConstructionFailureReleasesWhatItOpened(StageCase):

    class _Handle:
        def __init__(self, name, journal, failing=False):
            self.name, self.journal, self.failing = name, journal, failing

        def close(self):
            self.journal.append(self.name)
            if self.failing:
                raise OSError("this handle refuses to close")

        dispose = close
        release = close

    def composed(self, journal, **members):
        composed = stage_execution.StageExecution(
            None, authority=self._Handle("authority", journal),
            integration=self._Handle("integration", journal),
            workers=[{"role": "implementation",
                      "operations": self._Handle("implementation", journal)},
                     {"role": "review",
                      "operations": self._Handle("review", journal)}],
            given={})
        for name, value in members.items():
            setattr(composed, name, value)
        return composed

    def test_every_handle_is_released_in_reverse_order(self):
        journal = []
        self.composed(journal).release()
        self.assertEqual(journal, ["review", "implementation", "integration",
                                   "authority"])

    def test_a_partial_construction_releases_only_what_exists(self):
        journal = []
        composed = stage_execution.StageExecution(
            None, authority=self._Handle("authority", journal),
            integration=None, workers=[], given={})
        composed.release()
        self.assertEqual(journal, ["authority"])

    def test_one_failing_release_never_stops_the_others(self):
        journal = []
        composed = self.composed(journal)
        composed.integration.failing = True
        with self.assertRaises(ContractRefusal) as caught:
            composed.release()
        self.assertEqual(journal, ["review", "implementation", "integration",
                                   "authority"])
        self.assertIn("integration store", caught.exception.message)

    def test_the_pooled_surface_is_delegated_rather_than_respelled(self):
        journal = []
        composed = self.composed(journal)
        composed.pooled = type(
            "Pooled", (), {"canonical": True,
                           "dispatch": lambda self: "asked"})()
        self.assertEqual(composed.dispatch(), "asked")


class TheFactoryReadsOnlyItsNamedConfiguration(StageCase):

    def test_an_unset_environment_refuses_before_anything_is_opened(self):
        held = dict(os.environ)
        os.environ.pop(stage_execution.CONFIG_ENV, None)
        self.addCleanup(os.environ.update, held)
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.factory(object(), object())
        self.assertIn(stage_execution.CONFIG_ENV, caught.exception.message)
        self.assertEqual(caught.exception.category, "refused")

    def test_a_document_wider_than_the_ceiling_is_refused(self):
        place = os.path.join(self.root, "wide.json")
        with open(place, "w", encoding="utf-8") as writing:
            writing.write(
                json.dumps({"padding": "x" *
                            (stage_execution.MAX_CONFIG_BYTES + 16)}))
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution._read(place)
        self.assertEqual(caught.exception.code, "limit")

    def test_an_unreadable_document_is_refused_as_one(self):
        place = os.path.join(self.root, "broken.json")
        with open(place, "w", encoding="utf-8") as writing:
            writing.write("{not json")
        with self.assertRaises(ContractRefusal):
            stage_execution._read(place)


class ThePublicationSeamIsTwoAcceptedOperations(StageCase):
    """W103874's producer and W103077's publication, in the order that works.

    The ending calls this while the producer assignment is still live. What
    matters here is that the seam composes nothing of its own: the manifest
    digest comes from `retain_proposal` and is handed to `publish_candidate` as
    a SELECTOR, so no publication member is supplied from this deployment's
    configuration -- if one were, the deployment would be asserting something
    the frozen result is supposed to prove.
    """

    def seam(self, retained="sha256:" + "a" * 64, answer=None):
        asked = []

        def retain(control, publisher, *, attempt_id):
            asked.append(("retain", control, publisher, attempt_id))
            return retained

        def publish(control, publisher, *, attempt_id,
                    proposal_manifest_digest):
            asked.append(("publish", control, publisher, attempt_id,
                          proposal_manifest_digest))
            return answer if answer is not None else {"published": True}

        return asked, retain, publish

    def published(self, **members):
        asked, retain, publish = self.seam(**members)
        seam = stage_execution.Publication("control", "publisher")
        for name, replacement in (("retain_proposal", retain),
                                  ("publish_candidate", publish)):
            self.addCleanup(setattr, stage_execution, name,
                            getattr(stage_execution, name))
            setattr(stage_execution, name, replacement)
        return asked, seam

    def test_the_retained_digest_is_what_publication_selects_on(self):
        asked, seam = self.published()
        answer = seam.publish(attempt_id="attempt-1", result_id="result-1",
                              manifest_digest="sha256:" + "b" * 64,
                              artifacts=["artifact-1"],
                              proposal={"target": "revision-1"})
        self.assertEqual(answer, {"published": True})
        self.assertEqual(
            asked,
            [("retain", "control", "publisher", "attempt-1"),
             ("publish", "control", "publisher", "attempt-1",
              "sha256:" + "a" * 64)])

    def test_the_seam_records_what_it_published_and_invents_nothing(self):
        _asked, seam = self.published()
        seam.publish(attempt_id="attempt-1", result_id="result-1",
                     manifest_digest="sha256:" + "b" * 64,
                     artifacts=["artifact-1"],
                     proposal={"target": "revision-1"})
        self.assertEqual(seam.published, [{
            "attempt_id": "attempt-1", "result_id": "result-1",
            "manifest_digest": "sha256:" + "b" * 64,
            "artifacts": ["artifact-1"],
            "proposal_manifest_digest": "sha256:" + "a" * 64}])

    def test_a_producer_refusal_stops_before_the_authority_is_asked(self):
        asked, seam = self.published()

        def refusing(control, publisher, *, attempt_id):
            asked.append(("retain", attempt_id))
            raise ContractRefusal("refused", "precondition",
                                  "no frozen result")

        stage_execution.retain_proposal = refusing
        with self.assertRaises(ContractRefusal):
            seam.publish(attempt_id="attempt-1", result_id="result-1",
                         manifest_digest="sha256:" + "b" * 64,
                         artifacts=[], proposal={})
        self.assertEqual([one[0] for one in asked], ["retain"])
        self.assertEqual(seam.published, [])


class TheDriverFacingMembersComeFromTheConfiguration(StageCase):

    def test_the_integration_profile_is_composed_from_the_document(self):
        profile = stage_execution.integration_from(self.held())
        self.assertEqual(profile["profile_kind"], "git")
        self.assertEqual(profile["integrator_participant"],
                         "baton.integrator")
        self.assertEqual(profile["instructions_digest"], "sha256:" + "e" * 64)

    def test_a_composition_without_sessions_carries_no_publication(self):
        """A status surface receives an observation-only object, and a seam
        that could publish is exactly what such a surface must not hold."""
        composed = stage_execution.StageExecution(
            None, authority=None, integration=None, workers=[],
            given=self.held())
        self.assertIsNone(composed.publication)
        self.assertIsNotNone(composed.integration_profile)


class Publisher:
    """The Authority a publication is performed against, answering what it is
    asked.

    Derived from the operands rather than scripted, which is what makes
    `publish_candidate`'s own equality check meaningful over a manifest the
    real producer composed: the answer is a function of what it was sent, so
    the case proves the producer's receipt digest binds it.
    """

    participant = "baton.impl"
    target = "a" * 40

    def __init__(self):
        self.calls = []
        self.recorded = None

    def canonical_target(self):
        return self.target

    def publish(self, operands):
        self.calls.append(dict(operands))
        self.recorded = {
            "proposal_id": operands["proposal_id"],
            "assignment_ref": operands["expect"],
            "result_id": operands["result_id"],
            "result_digest": operands["result_digest"],
            "candidate_digest": operands["candidate_digest"],
            "input_digest": operands["input_digest"],
            "policy_digest": operands["policy_digest"],
            "target": operands["target"]}
        return dict(self.recorded)

    def proposal(self, proposal_id):
        return dict(self.recorded, decision={},
                    published_at="2026-09-07T00:00:00.000Z")


class ComposedLifecycleCase(DriverCase):
    """W103083 item 3: one Job through the drivers this factory composes.

    WHAT IS REAL, because that is the whole question a composed proof answers.
    The control store, the Job store and the development line are real;
    `prepare_implementation`, `freeze_checkpoint`, `prepare_review`,
    `record_verdict` and `open_correction` are the accepted operations against
    them; the result manifest each round publishes is REALLY RETAINED and read
    back through `load_manifest`; and the publication seam is the factory's own
    `Publication`, calling the real `retain_proposal` and `publish_candidate`.
    That is what the ruling means by using the real retained-manifest producer
    rather than a mock supplying the missing document.

    WHAT STANDS IN, named rather than implied. The freeze, intake, retention
    and cleanup OPERATIONS are not performed: they need an engine, a delivered
    workspace and a custody tree, which is the live proof's half. The frozen
    RESULT they would name is real and retained, so the producer composes over
    durable state rather than over a fixture's idea of one. The Authority is a
    fake that answers what it is asked.
    """

    # §12 RULE 1 IS WHY THIS AUTHORITY IS NOT THE JOB FIXTURE'S. A Work id
    # carries its Authority's eight-character prefix, and the shared
    # job-manager fixture's pair was written for a path that never validates a
    # manifest -- so reusing it here refuses at the identity rule before the
    # composition it is proving is reached. The line and every attempt below
    # use one manifest-valid pair.
    AUTHORITY = "0000000a" + "0" * 24
    WORK = WORK_A

    def setUp(self):
        super().setUp()
        from baton_v12.job_manager import JobStore, submit
        from baton_v12.worker_manager import create_line, retain_manifest
        from baton_v12.worker_manager.source_boundary import nominate_source
        from tests.job_manager.test_review_driver import one_work_submission
        # THE JOB STORE IS REBOUND TO THE SAME AUTHORITY as the line, because
        # `advance_correction` cross-binds the recorded verdict against the
        # Job's own Authority and Work. Two stores bound to two Authorities is
        # exactly the mismatch it exists to refuse.
        self.jobs.close()
        self.jobs = JobStore.open(
            os.path.join(self.root, "composed-jobs.sqlite3"),
            authority_uuid=self.AUTHORITY, incarnation="jobs-2",
            clock=self.clock)
        self.addCleanup(self.jobs.close)
        submit(self.jobs, one_work_submission())
        self.line = create_line(
            self.control, source=nominate_source(self.source),
            declared_base="a" * 40, profile=self.profile,
            authority_uuid=self.AUTHORITY, work_id=self.WORK)
        self.publisher = Publisher()
        self.seam = stage_execution.Publication(self.control, self.publisher)
        self.input_digest = retain_manifest(
            self.control, _vector("baton.worker-manifest/input"),
            "inputManifest")["digest"]
        self.retained = {}

    # -- the frozen result a round publishes ---------------------------------

    def frozen(self, attempt_id, generation):
        """One really retained result manifest, and the row that names it."""
        from baton_v12.contracts import digest
        from baton_v12.worker_manager import retain_manifest
        entries = [{"path": "change.patch", "bytes": 4,
                    "content_digest": "sha256:" + "6" * 64},
                   {"path": "objects.bundle", "bytes": 8,
                    "content_digest": "sha256:" + "7" * 64}]
        entries.sort(key=lambda one: one["path"].encode("utf-8"))
        content = {"entries": entries, "entry_count": len(entries),
                   "total_bytes": sum(one["bytes"] for one in entries),
                   "tree_digest": digest(entries)}
        artifact = {"artifact_id": f"{attempt_id}:proposal",
                    "media_type": "application/octet-stream",
                    "bytes": content["total_bytes"],
                    "content_digest": content["tree_digest"],
                    "locator": f"file:///var/lib/baton/{attempt_id}/proposal"}
        claim = {"base": self.publisher.target,
                 "head": f"{generation:040x}",
                 "transport": "objects.bundle",
                 "recap": f"candidate: round {generation}"}
        document = dict(_vector("baton.worker-manifest/result"),
                        result_id=f"result-{attempt_id}",
                        input_manifest_digest=self.input_digest,
                        assignment_ref={
                            "work_ref": {"authority_uuid": self.AUTHORITY,
                                         "work_id": self.WORK},
                            "participant": WRITER, "generation": generation},
                        outputs=[{"name": "proposal",
                                  "type": "git-change-proposal",
                                  "status": "present",
                                  "content_manifest": content,
                                  "artifact": artifact,
                                  "result_metadata": {
                                      "baton.git-proposal/1": claim}}])
        document.pop("manifest_digest")
        document["manifest_digest"] = digest(document)
        held = retain_manifest(self.control, document,
                               "resultManifest")["digest"]
        self.control._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES (?, ?, "
            "'completed', ?, ?, ?)",
            (attempt_id, document["result_id"], held, "freeze-" + attempt_id,
             NOW))
        return held, document

    # -- one composed round --------------------------------------------------

    def composed_round(self, number, disposition, *, based=None):
        """Implementation, real publication, checkpoint, review, verdict."""
        from baton_v12.worker_manager import (freeze_checkpoint,
                                              record_verdict)
        writer_attempt = self.attempt(f"writer-attempt-{number}", number,
                                      WRITER, f"writer-principal-{number}")
        self.control._connection.execute(
            "UPDATE attempts SET authority_uuid = ? WHERE "
            "runtime_attempt_id = ?", (self.AUTHORITY, writer_attempt))
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=number,
            worker_id=f"impl-worker-{number}", profile=self.profile,
            based_checkpoint_id=based)
        self.completed(writer_attempt)
        result_digest, document = self.frozen(writer_attempt, number)

        # THE FACTORY'S OWN SEAM, and the ordering the ending imposes: this
        # runs while the producer assignment is still live, BEFORE the
        # checkpoint fences it. A publication after the fence refuses.
        answer = self.seam.publish(
            attempt_id=writer_attempt, result_id=document["result_id"],
            manifest_digest=result_digest, artifacts=[],
            proposal={"target": self.publisher.target})
        self.retained[writer_attempt] = \
            self.seam.published[-1]["proposal_manifest_digest"]

        checkpoint = freeze_checkpoint(
            self.control, writer_id=writer["writer_id"], generation=number,
            profile=self.profile, port=self.port(WRITER))
        review_attempt = self.attempt(f"review-attempt-{number}", number,
                                      REVIEWER, f"review-principal-{number}")
        self.control._connection.execute(
            "UPDATE attempts SET authority_uuid = ? WHERE "
            "runtime_attempt_id = ?", (self.AUTHORITY, review_attempt))
        attached = review_driver.prepare_review(
            self.control, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=review_attempt, generation=number,
            reviewer_worker_id=f"review-worker-{number}",
            profile=self.profile)
        self.completed(review_attempt, review=True)
        verdict = record_verdict(
            self.control, attachment_id=attached["attachment_id"],
            disposition=disposition, profile=self.profile,
            port=self.port(REVIEWER))
        return {"checkpoint_id": checkpoint["checkpoint_id"],
                "verdict_id": verdict["verdict_id"], "published": answer,
                "result_digest": result_digest}


class TheComposedLifecycleRunsOverRealStores(ComposedLifecycleCase):
    """Item 3's own cases, over the harness above."""

    def test_one_job_runs_implementation_correction_and_acceptance(self):
        from baton_v12.worker_manager import (integration_checkpoint,
                                              line_of)
        first = self.composed_round(1, "changes-requested")
        self.assertEqual(first["published"]["result_digest"],
                         first["result_digest"])
        self.assertEqual(line_of(self.control,
                                 self.line["line_id"])["revision"], 1)

        # THE VERDICT ADVANCES THE JOB through the one act that touches it.
        review_driver.open_correction(
            self.jobs, self.control, job_id="job-a",
            answered={"outcome": "correction",
                      "line_id": self.line["line_id"],
                      "checkpoint_id": first["checkpoint_id"],
                      "verdict_id": first["verdict_id"]})
        # THE LINE IS READY FOR A CORRECTION, and round two below can only
        # attach a writer by naming exactly this checkpoint -- `grant_writer`
        # refuses any other, which is what makes the next round the SAME line
        # rather than a second one.
        self.assertEqual(line_of(self.control,
                                 self.line["line_id"])["state"],
                         "correction-ready")

        # ROUND TWO: the SAME line, based on the checkpoint that was rejected.
        second = self.composed_round(2, "accepted",
                                     based=first["checkpoint_id"])
        held = line_of(self.control, self.line["line_id"])
        self.assertEqual(held["revision"], 2)
        self.assertEqual(held["current_checkpoint_id"],
                         second["checkpoint_id"])
        self.assertNotEqual(second["result_digest"], first["result_digest"])

        # AND THE ACCEPTED CHECKPOINT IS THE ONE AN INTEGRATION WOULD ADMIT.
        accepted = integration_checkpoint(self.control, self.line["line_id"])
        self.assertEqual(accepted["checkpoint_id"], second["checkpoint_id"])
        self.assertEqual(accepted["verdict_id"], second["verdict_id"])

    def test_every_publication_selects_on_a_really_retained_manifest(self):
        """The producer is real, so the digest publication selects on is one
        `load_manifest` answers rather than one a mock supplied."""
        from baton_v12.worker_manager import load_manifest
        self.composed_round(1, "accepted")
        self.assertEqual(len(self.retained), 1)
        for attempt_id, retained in self.retained.items():
            held = load_manifest(self.control, retained, "proposalManifest")
            self.assertIsNotNone(held, attempt_id)
            self.assertEqual(held["result_manifest_digest"],
                             self.result_digest_of(attempt_id))
            self.assertEqual(held["source_base"],
                             {"algorithm": "sha1",
                              "hex": self.publisher.target})

    def result_digest_of(self, attempt_id):
        from baton_v12.worker_manager import frozen_output_of
        return frozen_output_of(self.control, attempt_id)["manifest_digest"]

    def test_publication_happens_while_the_producer_is_still_live(self):
        """W103068's measured ordering, driven rather than asserted in prose:
        the seam is asked before the checkpoint fences the writer."""
        from baton_v12.worker_manager import line_of
        states = []
        held = self.seam.publish

        def watched(**operands):
            states.append(line_of(self.control,
                                  self.line["line_id"])["state"])
            return held(**operands)

        self.seam.publish = watched
        self.composed_round(1, "accepted")
        self.assertEqual(states, ["writing"])


class TheFocusedChecksItemFourNames(ComposedLifecycleCase):
    """W103083 item 4, over the composition item 3 just proved.

    Five checks, each one the smallest thing that would actually catch its own
    failure. Deliberately not a failure-injection campaign: the expanded
    restart/status matrix is W103950's, and this leaf's ruling says so.
    """

    # -- one representative restart/replay cutpoint --------------------------

    def test_a_restart_at_the_publication_cutpoint_replays_rather_than_repeats(
            self):
        """The cutpoint chosen is publication, because it is the one act that
        reaches OUTSIDE this deployment.

        A manager that died after the Authority recorded a proposal and before
        it wrote anything of its own must, on the next incarnation, arrive at
        the same proposal rather than a second one. Retention is keyed by the
        digest of the bytes, so re-composing the manifest is what proves it:
        the same frozen result produces the same digest and therefore the same
        retained document.
        """
        from baton_v12.worker_manager import load_manifest, retain_manifest
        writer_attempt = self.attempt("writer-attempt-1", 1, WRITER,
                                      "writer-principal-1")
        self.control._connection.execute(
            "UPDATE attempts SET authority_uuid = ? WHERE "
            "runtime_attempt_id = ?", (self.AUTHORITY, writer_attempt))
        review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=1,
            worker_id="impl-worker-1", profile=self.profile)
        self.completed(writer_attempt)
        result_digest, document = self.frozen(writer_attempt, 1)

        first = self.seam.publish(
            attempt_id=writer_attempt, result_id=document["result_id"],
            manifest_digest=result_digest, artifacts=[],
            proposal={"target": self.publisher.target})
        held = self.control._connection.execute(
            "SELECT COUNT(*) FROM manifests WHERE schema = ?",
            ("baton.worker-manifest/proposal",)).fetchone()[0]

        # THE RESTART. A fresh seam over the same store, exactly as a new
        # incarnation would compose it, with no memory of the first.
        again = stage_execution.Publication(self.control, self.publisher)
        second = again.publish(
            attempt_id=writer_attempt, result_id=document["result_id"],
            manifest_digest=result_digest, artifacts=[],
            proposal={"target": self.publisher.target})

        self.assertEqual(second, first)
        self.assertEqual(again.published[0]["proposal_manifest_digest"],
                         self.seam.published[0]["proposal_manifest_digest"])
        # ONE RETAINED ACCOUNT, not two: the digest IS the key.
        self.assertEqual(self.control._connection.execute(
            "SELECT COUNT(*) FROM manifests WHERE schema = ?",
            ("baton.worker-manifest/proposal",)).fetchone()[0], held)
        self.assertIsNotNone(load_manifest(
            self.control, again.published[0]["proposal_manifest_digest"],
            "proposalManifest"))
        self.assertEqual(retain_manifest(self.control, document,
                                         "resultManifest")["digest"],
                         result_digest)

    # -- role and session separation -----------------------------------------

    def test_the_reviewer_is_never_the_writer_it_reviews(self):
        """Independence is refused twice, and the two refusals are different
        questions.

        The configuration refuses a shared identity before anything is opened;
        `attach_review` refuses one at the attachment, against the checkpoint's
        own recorded writer. This proves the second, over the real line the
        lifecycle just built, so the configuration rule is not the only thing
        standing between a Job and a self-review.
        """
        from baton_v12.worker_manager import freeze_checkpoint
        writer_attempt = self.attempt("writer-attempt-1", 1, WRITER,
                                      "writer-principal-1")
        self.control._connection.execute(
            "UPDATE attempts SET authority_uuid = ? WHERE "
            "runtime_attempt_id = ?", (self.AUTHORITY, writer_attempt))
        writer = review_driver.prepare_implementation(
            self.control, line_id=self.line["line_id"],
            attempt_id=writer_attempt, generation=1,
            worker_id="impl-worker-1", profile=self.profile)
        self.completed(writer_attempt)
        checkpoint = freeze_checkpoint(
            self.control, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.port(WRITER))
        with self.assertRaises(ContractRefusal):
            review_driver.prepare_review(
                self.control, checkpoint_id=checkpoint["checkpoint_id"],
                attempt_id=writer_attempt, generation=1,
                reviewer_worker_id="impl-worker-1", profile=self.profile)

    def test_the_composed_rounds_carry_distinct_identities(self):
        held = self.composed_round(1, "accepted")
        self.assertIsNotNone(held["checkpoint_id"])
        rows = dict(self.control._connection.execute(
            "SELECT runtime_attempt_id, assignment_participant FROM attempts"
        ).fetchall())
        self.assertEqual(rows["writer-attempt-1"], WRITER)
        self.assertEqual(rows["review-attempt-1"], REVIEWER)
        self.assertNotEqual(rows["writer-attempt-1"], rows["review-attempt-1"])

    # -- operator-held uncertainty -------------------------------------------

    def test_a_rejected_verdict_is_held_rather_than_acted_on(self):
        """`rejected` is a decision about the Work, and this composition
        schedules nothing on it.

        `open_correction` refuses anything that is not a correction, which is
        what keeps a held outcome from being quietly turned into another round.
        """
        held = self.composed_round(1, "rejected")
        with self.assertRaises(ContractRefusal) as caught:
            review_driver.open_correction(
                self.jobs, self.control, job_id="job-a",
                answered={"outcome": "held",
                          "line_id": self.line["line_id"],
                          "checkpoint_id": held["checkpoint_id"],
                          "verdict_id": held["verdict_id"]})
        self.assertIn("correction round follows", caught.exception.message)

    def test_the_held_outcome_is_one_this_composition_never_invents(self):
        self.assertEqual(sorted(review_driver.VERDICT_OUTCOMES),
                         ["accepted", "correction", "held"])


class NothingIsOpenedBeforeTheConfigurationIsProved(StageCase):
    """Item 4's pre-launch refusal, asked as "what exists on disk afterwards".

    A composer that refused only after opening its Authority would leave a lock
    nobody holds a reference to, and the refusal message would describe the
    wrong moment. The question a case can actually answer is whether the store
    files it would have created are there.
    """

    def composed(self, **members):
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.operations_from(
                self.document(**members), object(), object(),
                checkout=self.checkout)
        return caught.exception

    def test_a_refused_document_opens_no_integration_store(self):
        self.composed(review_work_id="work-2")
        self.assertFalse(os.path.exists(self.integration_store))

    def test_a_job_store_bound_elsewhere_refuses_before_opening_anything(self):
        from types import SimpleNamespace
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.operations_from(
                self.document(),
                SimpleNamespace(authority_uuid="f" * 32), object(),
                checkout=self.checkout)
        self.assertEqual(caught.exception.category, "refused")
        self.assertFalse(os.path.exists(self.integration_store))


if __name__ == "__main__":
    unittest.main()
