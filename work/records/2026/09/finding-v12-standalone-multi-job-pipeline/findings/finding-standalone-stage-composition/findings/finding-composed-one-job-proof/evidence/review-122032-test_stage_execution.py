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
from types import SimpleNamespace
from unittest import mock

from baton_v12.authority import MAX_SAFE_INTEGER
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import driver
from baton_v12.job_manager import review_driver

from tools import single_worker, stage_execution

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
        deployment["launch_role"] = role
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
            "policy_generation": 1,
            "line_declared_base": "a" * 40,
            "receipt_participants": {"verification": "baton.verifier",
                                     "review": "baton.approver-review",
                                     "approval": "baton.approver"},
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
    """The SHAPE half of the session gate.

    REVIEW 2026-09-07T14-12-42Z [P1] SPLIT THIS IN TWO, and the two halves are
    deliberately proved in different places. These cases ask whether the object
    is the runtime face this deployment mints; whether its ACTOR may write the
    receipt is an Authority decision, and
    `TheReceiptActorsAreAuthorizedAndNotMerelyShaped` asks that one over a real
    Authority with real grants. A fake that answered a capability would be
    asserting against this file's idea of one.
    """

    class _Session:
        participant = "baton.actor"

        def __init__(self, *verbs):
            for verb in verbs:
                setattr(self, verb, lambda *a, **k: None)

    class _Authority:
        """Authorizes everything, and RECORDS WHAT IT WAS ASKED."""

        def __init__(self):
            self.asked = []

        def holds_capability(self, participant, capability, *, scope=None):
            self.asked.append((participant, capability, scope))
            return True

    def sessions(self, **replaced):
        held = {"verification": self._Session("verify"),
                "review": self._Session("review"),
                "approval": self._Session("approve"),
                "integrator": self._Session("integrate", "receipt"),
                "publisher": self._Session(
                    *stage_execution.PUBLISHER_CAPABILITIES)}
        held.update(replaced)
        return held

    def proved(self, held=None, authority=None, scope="scope:deployment"):
        return stage_execution._sessions(
            self.sessions() if held is None else held,
            self._Authority() if authority is None else authority, scope)

    def test_the_complete_set_is_accepted(self):
        held = self.sessions()
        self.assertIs(self.proved(held), held)

    def test_each_receipt_actor_is_asked_for_its_own_grant_in_one_scope(self):
        """The mapping, read off the gate rather than off the constant: four
        receipts, four different capabilities, one scope -- and the publisher
        is not among them, because publication is authorized by the producer's
        live assignment and there is no grant to ask about."""
        authority = self._Authority()
        self.proved(authority=authority, scope="scope:job-a")
        self.assertEqual(
            sorted(authority.asked),
            [("baton.actor", "approve", "scope:job-a"),
             ("baton.actor", "integrate", "scope:job-a"),
             ("baton.actor", "review", "scope:job-a"),
             ("baton.actor", "verify", "scope:job-a")])

    def test_a_missing_session_refuses(self):
        for name in stage_execution.RECEIPT_SESSIONS + ("publisher",):
            with self.subTest(name=name):
                with self.assertRaises(ContractRefusal) as caught:
                    self.proved(self.sessions(**{name: None}))
                self.assertEqual(caught.exception.category, "refused")
                self.assertIn(name, caught.exception.message)

    def test_a_session_without_its_verb_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.proved(self.sessions(integrator=self._Session("integrate")))
        self.assertIn("receipt", caught.exception.message)
        # THE PUBLISHER IS REACHED EARLIEST OF ALL, so a deployment missing one
        # of its three would discover it with a frozen result it can never
        # publish.
        for verb in stage_execution.PUBLISHER_CAPABILITIES:
            partial = [one for one in stage_execution.PUBLISHER_CAPABILITIES
                       if one != verb]
            with self.subTest(verb=verb):
                with self.assertRaises(ContractRefusal) as caught:
                    self.proved(self.sessions(
                        publisher=self._Session(*partial)))
                self.assertIn(verb, caught.exception.message)

    def test_a_session_without_a_participant_refuses(self):
        nameless = self._Session("verify")
        nameless.participant = None
        with self.assertRaises(ContractRefusal) as caught:
            self.proved(self.sessions(verification=nameless))
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

    def test_a_partly_constructed_object_answers_no_serving_member(self):
        """`tools.job_manager` asks a returned object for `close` by name, and
        a composition that failed before its pool existed must answer that as
        an absence rather than by delegating onto nothing."""
        composed = stage_execution.StageExecution(
            None, authority=None, integration=None, workers=[],
            given=self.held())
        self.assertIsNone(getattr(composed, "launch_pass", None))
        with self.assertRaises(AttributeError):
            composed.binding_intent
        # `close` IS ITS OWN, so a partial construction is still releasable.
        self.assertTrue(callable(composed.close))


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


class TheIntegrationStageConsumesTheAcceptedPort(StageCase):
    """W103083 obligation115920, owner ruling M115946.

    The requirement is DERIVED from configured material, and a later tick
    refreshes before it asks the port's own marker whether this execution may
    continue. Every driver call is recorded rather than performed: which
    driver a tick chooses, and with what, is this assembly's decision, and the
    drivers have their own suites for what they then do.
    """

    def group(self):
        """The manager's own nominal WorkspaceGroup, not its integer.

        Review 2026-09-08T04:06:54Z [P1]: the assembly held `.gid`, and the
        public delivery readers require the group object -- so a fixture that
        supplied an integer could not have noticed.
        """
        from baton_v12.worker_manager import ControlStore, workspaces

        control = ControlStore.open(self.control_path,
                                    incarnation="stage-group",
                                    clock=lambda: NOW)
        self.addCleanup(control.close)
        workspaces.configure_workspace_group(control, os.getgid())
        workspaces.configure_workspace_storage(control, self.storage)
        return workspaces.configured_workspace_group(control)

    def deployment(self, **members):
        # THE FACTORY'S OWN HELD FORM, not the raw document. Review
        # 2026-09-08T04:06:54Z [P1]: these cases supplied the raw
        # configuration, so they could not see that `required_tests`
        # re-validated a document the factory had already held.
        given = members.pop("given", None) or stage_execution.held_configuration(
            self.document(), checkout=self.checkout)
        held = SimpleNamespace(
            given=given, control=object(), jobs=object(), authority=object(),
            integration=object(), integration_profile=given[
                "integration_profile"],
            integration_root=os.path.join(self.root, "integration-root"),
            workspace_group=self.group(),
            sessions={one: SimpleNamespace(name=one) for one in
                      ("verification", "review", "approval", "integrator")},
            line=lambda: {"line_id": "line-1"},
            published_proposal=lambda accepted: "proposal-1")
        for name, value in members.items():
            setattr(held, name, value)
        return held

    def port(self, *, runtime_state="running", continuable=True):
        calls = []

        def observed(attempt_id, assignment):
            calls.append(("observed", attempt_id))
            return {"execution_runtime": runtime_state}

        return SimpleNamespace(
            calls=calls,
            prepare=lambda stage, job: calls.append(("prepare",
                                                     stage["attempt_id"])),
            refresh=lambda attempt_id: calls.append(("refresh", attempt_id)),
            observed=observed,
            may_continue=lambda assignment, delivery=None: (
                calls.append(("may_continue", None)) or continuable))

    def driven(self, *, delivery=None, assignment=None, port=None,
               deployment=None):
        """One tick, with every driver and public reader recorded."""
        held = self.deployment() if deployment is None else deployment
        taken = self.port() if port is None else port
        seen = {}
        with mock.patch.object(stage_execution, "admit_accepted",
                               side_effect=lambda *a, **k: seen.setdefault(
                                   "admit", k) or {"outcome": "running"}
                               ) as admit, \
                mock.patch.object(
                    stage_execution, "continue_accepted",
                    side_effect=lambda *a, **k: seen.setdefault(
                        "continue", k) or {"outcome": "running"}
                    ) as keep, \
                mock.patch.object(stage_execution.runtime, "adopt_delivery",
                                  return_value=delivery), \
                mock.patch.object(stage_execution.runtime,
                                  "published_assignment",
                                  return_value=assignment), \
                mock.patch.object(stage_execution.review_cycles,
                                  "integration_checkpoint",
                                  return_value={"checkpoint_id": "cp-1"}):
            answer = stage_execution.Integration(held, taken).run(
                {"attempt_id": "attempt-1", "kind": "integration"},
                {"job_id": "job-1"})
        return answer, taken.calls, admit, keep, seen

    # -- the derived requirement --------------------------------------------

    def test_the_requirement_is_derived_from_the_configured_task(self):
        """Not from what the worker REPORTED: from the task bytes this
        deployment configured and the input manifest they are bound to."""
        import hashlib
        import json as _json

        held = stage_execution.Integration(self.deployment(), self.port())
        derived = held.required_tests()
        given = stage_execution.held_configuration(
            self.document(), checkout=self.checkout)["workers"][0][
                "deployment"]
        payload = given["task_bytes"]
        self.assertEqual(derived, {
            "task_id": _json.loads(payload)["task_id"],
            "task_digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "argv": _json.loads(payload)["verification"],
            "input_manifest_digest":
                given["input_manifest"]["manifest_digest"]})
        # AND THE ACCEPTED DRIVER'S OWN READER ADMITS IT.
        self.assertEqual(driver._owned_requirements(derived), derived)

    def test_a_deployment_without_exactly_one_producer_refuses(self):
        given = stage_execution.held_configuration(self.document(),
                                                   checkout=self.checkout)
        given["workers"] = [one for one in given["workers"]
                            if one["role"] != "implementation"]
        held = stage_execution.Integration(
            self.deployment(given=given), self.port())
        with self.assertRaises(ContractRefusal) as caught:
            held.required_tests()
        self.assertIn("implementation workers", caught.exception.message)

    def test_the_published_reader_adopts_a_real_delivery_with_the_group(self):
        """W103083 review 2026-09-08T04:06:54Z [P1], proved through the REAL
        public readers over a real materialized delivery rather than a mock.

        The manager's nominal group adopts; the integer that used to be stored
        in its place refuses, which is the defect this pins. An absent delivery
        cannot show either, because `adopt_delivery` answers `None` before it
        validates the group.
        """
        from baton_v12.integration import runtime as integration_runtime

        group = self.group()
        held = self.deployment(workspace_group=group)
        os.makedirs(held.integration_root, exist_ok=True)
        integration_runtime.materialize_delivery(
            held.integration_root, attempt_id="attempt-1",
            workspace_group=group)

        delivery, assignment = stage_execution.Integration(
            held, self.port())._published({"attempt_id": "attempt-1"})
        self.assertIsNotNone(delivery)
        # NOTHING WAS PUBLISHED INTO IT YET, and that is an ordinary answer
        # rather than an invented assignment.
        self.assertIsNone(assignment)

        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.Integration(
                self.deployment(workspace_group=group.gid),
                self.port())._published({"attempt_id": "attempt-1"})
        self.assertIn(str(group.gid), caught.exception.message)

    # -- which driver a tick chooses ----------------------------------------

    def test_the_first_tick_prepares_and_then_admits(self):
        _, calls, admit, keep, seen = self.driven()
        self.assertEqual(calls, [("prepare", "attempt-1")])
        admit.assert_called_once()
        keep.assert_not_called()
        # THE OPERAND THAT WAS MISSING ENTIRELY travels now.
        self.assertIn("required_tests", seen["admit"])
        self.assertEqual(sorted(seen["admit"]["required_tests"]),
                         ["argv", "input_manifest_digest", "task_digest",
                          "task_id"])

    def test_a_later_tick_refreshes_before_it_continues(self):
        """Owner ruling M115946: refresh FIRST, then the port's own marker."""
        _, calls, admit, keep, seen = self.driven(
            delivery=object(), assignment={"attempt_id": "attempt-1"})
        self.assertEqual(calls, [("observed", "attempt-1"),
                                 ("refresh", "attempt-1"),
                                 ("may_continue", None)])
        keep.assert_called_once()
        admit.assert_not_called()
        self.assertIn("required_tests", seen["continue"])
        # AND CONTINUATION IS NEVER HANDED A PORT: it cannot start anything.
        self.assertNotIn("port", seen["continue"])

    def test_a_lost_marker_falls_through_to_admission(self):
        """A fresh serving incarnation holds no marker, so the driver's own
        restart behaviour is what answers -- reading a persisted assignment
        grants no continuation permission."""
        _, calls, admit, keep, _ = self.driven(
            delivery=object(), assignment={"attempt_id": "attempt-1"},
            port=self.port(continuable=False))
        self.assertEqual(calls, [("observed", "attempt-1"),
                                 ("refresh", "attempt-1"),
                                 ("may_continue", None)])
        admit.assert_called_once()
        keep.assert_not_called()

    def test_a_delivery_with_no_started_runtime_is_not_refreshed(self):
        """The namespaces are materialized before the container, so a delivery
        can exist with no runtime behind it. That attempt is admission's to
        re-enter, and refreshing it would ask reconciliation about a runtime
        nobody requested.

        W103083 review 2026-09-08T12:41:47Z [P1], owner approval M118923: it
        is PREPARED before that re-entry, and this case's recorded calls are
        the one thing that changed. Re-entering admission with no
        execution-local credential delivery is what a reconstructed port
        refused on, and the other three assertions here -- no refresh, exactly
        one admission, no continuation -- are unchanged and are why the
        preparation is the whole of the correction.
        """
        _, calls, admit, keep, _ = self.driven(
            delivery=object(), assignment={"attempt_id": "attempt-1"},
            port=self.port(runtime_state="not-started"))
        self.assertEqual(calls, [("observed", "attempt-1"),
                                 ("prepare", "attempt-1")])
        admit.assert_called_once()
        keep.assert_not_called()

    def test_a_started_or_uncertain_runtime_is_never_prepared_here(self):
        """The other side of that branch, which is why it IS a branch.

        Preparation mints a bearer only for an attempt whose runtime has not
        started; the credential custody of a runtime this execution did not
        start belongs to that runtime. So a started or uncertain attempt with
        no marker is refreshed and then admitted exactly as before, and the
        hold `admit_accepted` has always owned is what answers it.
        """
        for state in ("running", "uncertain"):
            with self.subTest(runtime=state):
                _, calls, admit, keep, _ = self.driven(
                    delivery=object(),
                    assignment={"attempt_id": "attempt-1"},
                    port=self.port(runtime_state=state, continuable=False))
                self.assertEqual(calls, [("observed", "attempt-1"),
                                         ("refresh", "attempt-1"),
                                         ("may_continue", None)])
                admit.assert_called_once()
                keep.assert_not_called()

    def test_a_delivery_carrying_no_assignment_is_the_first_tick(self):
        """Absent or unpublished: neither invents an assignment."""
        for delivery in (None, object()):
            with self.subTest(delivery=delivery is not None):
                _, calls, admit, keep, _ = self.driven(delivery=delivery,
                                                       assignment=None)
                self.assertEqual(calls, [("prepare", "attempt-1")])
                admit.assert_called_once()
                keep.assert_not_called()


class AFreshPortReentersANeverStartedDelivery(unittest.TestCase):
    """W119113: this assembly's dispatch over the REAL production port.

    COMPOSED, NOT SUBCLASSED, for the reason the port suite's own fixture
    records: a subclass re-runs every one of its parent's cases under a second
    name. This borrows that composed world whole -- the real Worker Manager,
    coordinator, Authority, delivery namespaces, admission and continuation
    drivers, and the deterministic engine and provider that stand in for a
    daemon and a model -- and asks it the one question the recorded-port cases
    above cannot answer: what a fresh `IntegrationRuntimePort` actually does
    when the tick finds a delivery it published and never started.

    THE MEASURED DEFECT, W103083 review 2026-09-08T12:41:47Z [P1]. A first
    admission that dies between publishing the assignment and starting the
    runtime leaves durable namespaces, a durable assignment and a runtime the
    manager's own axis still calls `not-started`. The next incarnation holds
    no in-memory credential delivery, and it used to re-enter admission
    without preparing one, so the attempt could never start again.
    """

    def setUp(self):
        from .test_integration_worker import (
            ATTEMPT, TheWholeIntegrationRunsThroughThisPort)

        self.attempt = ATTEMPT
        case = TheWholeIntegrationRunsThroughThisPort()
        case.setUp()
        self.addCleanup(case.doCleanups)
        self.case = case
        self.world = case.world

    # -- the world, read through its own owners -----------------------------

    def deployment(self):
        """The operands `Integration.run` resolves, from the borrowed world.

        Two members answer for this fixture rather than deriving: `line` and
        `published_proposal`, whose replay of the accepted checkpoint's own
        writer/attempt/manifest chain belongs to the composed lifecycle cases
        and to `W119114`. Everything this class is about is the real thing --
        the public delivery readers, the production port, both drivers, and
        the manager's own runtime witness.
        """
        case, world = self.case, self.world
        return SimpleNamespace(
            given={"canonical_target_id": world.target,
                   "policy_generation": world.authority.policy_generation()},
            control=world.manager, jobs=world.jobs,
            authority=world.authority_read, integration=world.coordinator,
            integration_profile=case.profile,
            integration_root=case.launch_root,
            workspace_group=case.owner.group,
            sessions={"verification": world.sessions["verify"],
                      "review": world.sessions["review"],
                      "approval": world.sessions["approve"],
                      "integrator": world.integrator},
            line=lambda: {"line_id": world.line_id},
            published_proposal=lambda accepted: world.proposal_id)

    def recording(self, port=None):
        """One production port whose two acts are recorded and not replaced.

        `wraps` rather than a substitute: what each call then does is the
        port's own, and the assertions here are about which of them this
        assembly makes.
        """
        held = self.case.port() if port is None else port
        held.prepare = mock.Mock(wraps=held.prepare)
        held.refresh = mock.Mock(wraps=held.refresh)
        return held

    def tick(self, port):
        """One `Integration.run`, with the driver it chose recorded.

        The requirement is the world's own selection. This borrowed deployment
        carries no configured workers to derive one from, and the derivation
        has its own real-factory cases above; substituting it here keeps this
        boundary about dispatch and preparation.
        """
        held = stage_execution.Integration(self.deployment(), port)
        with mock.patch.object(held, "required_tests",
                               return_value=self.world.required), \
                mock.patch.object(stage_execution, "admit_accepted",
                                  wraps=stage_execution.admit_accepted
                                  ) as admit, \
                mock.patch.object(stage_execution, "continue_accepted",
                                  wraps=stage_execution.continue_accepted
                                  ) as keep:
            answer = held.run(self.case.stage(), {"job_id": "job-1"})
        return answer, admit, keep

    def starts(self):
        """How many runtimes this world's engine was asked to run."""
        return len([one for one in self.case.engine_calls if one[1] == "run"])

    def witness(self):
        """The manager's own accepted axis for this attempt."""
        from baton_v12.integration import runtime as integration_runtime

        return integration_runtime.prior_runtime_witness(
            self.world.manager, self.attempt)["execution_runtime"]

    def interrupted(self):
        """One first admission that dies between publication and the start."""
        held = self.case.port()
        held.prepare(self.case.stage(), None)
        with mock.patch.object(
                held, "run",
                side_effect=ContractRefusal(
                    "refused", "precondition",
                    "the injected interruption before the runtime start")):
            with self.assertRaises(ContractRefusal):
                self.case.admit(held)
        return held

    # -- the controls, which say what an unbroken tick does ------------------

    def test_an_ordinary_first_tick_prepares_and_starts_exactly_once(self):
        """The valid initial case: nothing is published yet, so this is the
        first tick the recorded-port cases describe, performed for real."""
        port = self.recording()
        answer, admit, keep = self.tick(port)

        self.assertEqual(answer["outcome"], "running")
        self.assertEqual(port.prepare.call_count, 1)
        port.refresh.assert_not_called()
        admit.assert_called_once()
        keep.assert_not_called()
        self.assertEqual(self.starts(), 1)
        self.assertEqual(self.witness(), "running")

    def test_a_second_tick_in_the_same_execution_starts_nothing_again(self):
        """The same-execution case: this port holds the marker it made, so the
        tick refreshes and continues, and no second runtime is asked for."""
        port = self.recording()
        self.tick(port)
        answer, admit, keep = self.tick(port)

        self.assertEqual(port.prepare.call_count, 1)
        self.assertEqual(port.refresh.call_count, 1)
        keep.assert_called_once()
        admit.assert_not_called()
        self.assertEqual(self.starts(), 1)
        self.assertEqual(answer["outcome"], "running")

    # -- the correction ------------------------------------------------------

    def test_an_interrupted_first_admission_leaves_a_never_started_delivery(
            self):
        """The predecessor state this correction is about, measured rather
        than assumed: a real published assignment over a runtime the manager's
        own axis says was never started, and no engine start at all."""
        from baton_v12.integration import runtime as integration_runtime

        self.interrupted()
        delivery = integration_runtime.adopt_delivery(
            self.case.launch_root, attempt_id=self.attempt,
            workspace_group=self.case.owner.group)
        self.assertIsNotNone(delivery)
        self.assertIsNotNone(
            integration_runtime.published_assignment(delivery))
        self.assertEqual(self.witness(), "not-started")
        self.assertEqual(self.starts(), 0)

    def test_a_fresh_port_prepares_that_delivery_and_then_starts_it(self):
        """W103083 review 2026-09-08T12:41:47Z [P1], and the whole of W119113.

        The reconstructed port receives the preparation it needs before
        admission -- and receives it without a refresh, because reconciling an
        attempt no start was ever requested for is a write this branch has
        never made.
        """
        self.interrupted()
        port = self.recording()
        answer, admit, keep = self.tick(port)

        self.assertEqual(answer["outcome"], "running")
        self.assertEqual(port.prepare.call_count, 1)
        port.refresh.assert_not_called()
        admit.assert_called_once()
        keep.assert_not_called()
        # ONE START, from the incarnation that prepared it.
        self.assertEqual(self.starts(), 1)
        self.assertEqual(self.witness(), "running")

    def test_a_runtime_this_execution_did_not_start_is_still_held(self):
        """The hold this correction must not spend: a started attempt is NOT
        prepared, because its credential custody belongs to the runtime that
        holds it, and no second writer is ever run for it."""
        self.case.started()
        minted = len(self.case.minted)
        self.assertEqual(self.starts(), 1)

        port = self.recording()
        answer, admit, keep = self.tick(port)

        self.assertEqual(answer["outcome"], "held")
        port.prepare.assert_not_called()
        self.assertEqual(port.refresh.call_count, 1)
        admit.assert_called_once()
        keep.assert_not_called()
        self.assertEqual(self.starts(), 1)
        self.assertEqual(len(self.case.minted), minted)


class ServingCase(StageCase):
    """One deployment composed the way the serving loop composes it.

    REVIEW 2026-09-07T13-29-13Z [P1] IS WHY THESE EXIST AT ALL. The cases
    above prove what a configuration refuses and the cases below prove what
    the drivers do; between them sat an object that had been constructed but
    never asked to serve anything. These ask it.
    """

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority
        from tests.job_manager import fixtures
        self.work = fixtures.WORK_A
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            self.principals = {
                who: authority.principal_of(who)
                for who in ("baton.reviewer", "baton.integrator")}
            # THE SCOPE THE RECEIPTS WILL ACTUALLY BE AUTHORIZED IN, read from
            # the Work rather than assumed to be the deployment's.
            self.scope = authority.project_work(self.work)["scope"]
            # AND THE FOUR GRANTS, WHICH THIS FIXTURE PREVIOUSLY DID NOT NEED.
            # Review 2026-09-07T14-12-42Z [P1]: the composition proved only
            # that each session object had callable methods of the right name,
            # and every minted session has all of them -- so every case here
            # composed a deployment whose receipt actors were authorized for
            # nothing at all, and the deployment would have discovered that at
            # `_write_receipt`, with a candidate already published.
            self.receipt_grants = {"baton.verifier": "verify",
                                   "baton.approver-review": "review",
                                   "baton.approver": "approve",
                                   "baton.integrator": "integrate"}
            for who, capability in self.receipt_grants.items():
                authority.grant_capability(who, capability, scope=self.scope)
        finally:
            authority.dispose()

    def composed_document(self, **members):
        given = {
            "job_work_id": self.work, "review_work_id": self.work,
            "workers": [
                self.worker("implementation"),
                self.worker("review", participant="baton.reviewer",
                            principal=self.principals["baton.reviewer"]),
                self.worker("integration", participant="baton.integrator",
                            principal=self.principals["baton.integrator"])]}
        given.update(members)
        return self.document(**given)

    def serving(self, **members):
        from tests.job_manager import fixtures
        from .test_single_worker import Engine
        job, control = self.stores("stage-serving")
        composed = stage_execution.operations_from(
            self.composed_document(**members), job, control,
            engine_run=Engine(),
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        return job, control, composed


class TheServingPathReachesTheAcceptedDrivers(ServingCase):
    """P1: the object the loop drives, not the attributes beside it."""

    def test_each_stage_worker_carries_its_own_composition(self):
        _job, _control, composed = self.serving()
        held = {one["role"]: one["operations"]._worker.stage
                for one in composed.workers}
        for role in ("implementation", "review"):
            with self.subTest(role=role):
                self.assertIsInstance(held[role],
                                      stage_execution.StageComposition)
                self.assertEqual(held[role].role, role)
                self.assertEqual(held[role].worker_id, f"{role}-worker")
        # THE INTEGRATION WORKER HAS NO WORKER-LAUNCH COMPOSITION, because an
        # accepted integration is not started through an offer, a claim and an
        # exchange: `admit_accepted` leases the candidate and drives its own
        # delivery. Giving it a stage composition would be composing a mount
        # and an ending nothing would ever call.
        self.assertIsNone(held["integration"])

    def test_a_review_stage_is_admitted_by_the_review_worker(self):
        """The measured symptom: `_matches` refused every kind but
        `implementation`, so no review stage could ever be launched."""
        _job, _control, composed = self.serving()
        worker = {one["role"]: one["operations"]._worker
                  for one in composed.workers}["review"]
        stage = {"stage_id": "job-a:review", "kind": "review",
                 "work_id": self.work,
                 "profile_name": worker.given["profile_name"],
                 "profile_digest": worker.given["profile_digest"]}
        job = {"input_digest":
               worker.given["input_manifest"]["manifest_digest"],
               "policy_digest": worker.given["policy_digest"]}
        # No refusal: the stage matches the worker composed for it.
        self.assertIsNone(worker._matches(stage, job))
        with self.assertRaises(ContractRefusal) as caught:
            worker._matches(dict(stage, kind="implementation"), job)
        self.assertIn("only 'review'", caught.exception.message)

    def test_the_integration_kind_is_driven_by_the_integration_driver(self):
        _job, _control, composed = self.serving()
        asked = []
        composed.integrator = type(
            "Recording", (), {"run": lambda _self, stage, job:
                              asked.append((stage["kind"], job)) or "driven"})()
        stage = {"kind": "integration", "attempt_id": "attempt-i",
                 "stage_id": "job-a:integration"}
        self.assertEqual(composed.launch(stage, {"job": 1}), "driven")
        self.assertEqual(composed.conclude(stage, {"job": 1}), "driven")
        self.assertEqual([one[0] for one in asked],
                         ["integration", "integration"])

    def test_an_integration_without_a_runtime_port_refuses_as_that(self):
        """The one capability this build does not have, reported rather than
        stubbed and contained to its own stage."""
        _job, _control, composed = self.serving()
        with self.assertRaises(ContractRefusal) as caught:
            composed.launch({"kind": "integration", "attempt_id": "attempt-i"},
                            {})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertIn("integration runtime port", caught.exception.message)

    def test_the_pool_is_activated_from_the_configuration(self):
        """Nobody issues an operator transition to create capacity: the
        deployment's own workers ARE the pool generation it serves under."""
        from baton_v12.job_manager import scheduler
        job, _control, composed = self.serving()
        active = scheduler.active_generation(job)
        self.assertEqual(active["generation"], 1)
        self.assertEqual(
            sorted(one["worker_id"] for one in scheduler.pool_workers(job)),
            ["implementation-worker", "integration-worker", "review-worker"])
        self.assertEqual(sorted(composed.pooled.workers),
                         [(1, "implementation-worker"),
                          (1, "integration-worker"), (1, "review-worker")])

    def test_a_configuration_naming_another_pool_generation_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.serving(pool_generation=4)
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertIn("moved on", caught.exception.message)


class TheFactorysOwnOperandsReachTheIntegrationStage(ServingCase):
    """W119113: review 119091's independent controls, kept as ordinary tests.

    Review 2026-09-08T12:41:47Z accepted the held/raw and nominal-group
    corrections through a probe over the ACTUAL `operations_from` factory,
    because the recorded-port cases build their deployment by hand and could
    not have seen either defect. These ask the same questions here, so the
    acceptance is a test this suite runs rather than only retained evidence.
    """

    def producer(self, composed):
        """The factory's own held implementation deployment."""
        return next(one["deployment"] for one in
                    composed.deployment.given["workers"]
                    if one["role"] == "implementation")

    def test_the_composed_integration_derives_its_requirement_from_it(self):
        """The held form is consumed AS IT STANDS: re-validating it through
        the raw-document validator refused the factory's own derived members,
        and every real integration tick stopped there."""
        import hashlib

        _job, _control, composed = self.serving()
        held = self.producer(composed)
        derived = composed.integrator.required_tests()
        self.assertEqual(derived["task_digest"],
                         "sha256:" + hashlib.sha256(
                             held["task_bytes"]).hexdigest())
        self.assertEqual(derived["input_manifest_digest"],
                         held["input_manifest"]["manifest_digest"])
        # AND THE ACCEPTED DRIVER'S OWN READER ADMITS WHAT THE FACTORY BUILT.
        self.assertEqual(driver._owned_requirements(derived), derived)

    def test_replacing_the_task_document_after_construction_changes_nothing(
            self):
        """The bytes were read once at configuration, no-follow and bounded.
        A file replaced afterwards would otherwise substitute new expected
        bytes for the producer this Job actually ran."""
        _job, _control, composed = self.serving()
        derived = composed.integrator.required_tests()
        with open(self.task_document, "wb") as writing:
            writing.write(b'{"task_id": "replaced", '
                          b'"verification": ["a-different-command"]}')
        self.assertEqual(composed.integrator.required_tests(), derived)

    def test_a_producer_task_naming_no_verification_refuses(self):
        """An integration is admitted behind an ordinary test run and never
        ahead of one, so a producer configured without a command refuses."""
        _job, _control, composed = self.serving()
        held = self.producer(composed)
        task = json.loads(held["task_bytes"].decode("utf-8"))
        task.pop("verification", None)
        held["task_bytes"] = json.dumps(task).encode("utf-8")
        with self.assertRaises(ContractRefusal) as caught:
            composed.integrator.required_tests()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("names no verification command",
                      caught.exception.message)

    def test_a_job_naming_another_producers_input_refuses(self):
        """M115946's correspondence check, over the factory's own operands: a
        required-test selection describes the producer this Job ran."""
        _job, _control, composed = self.serving()
        integration = composed.integrator
        derived = integration.required_tests()
        # The Job this deployment's producer really ran passes.
        self.assertIsNone(integration._correspondent(
            {"input_digest": derived["input_manifest_digest"]}, derived))
        with self.assertRaises(ContractRefusal) as caught:
            integration._correspondent({"input_digest": "sha256:" + "f" * 64},
                                       derived)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("sha256:" + "f" * 64, caught.exception.message)

    def test_the_factory_holds_the_group_a_real_delivery_is_adopted_with(
            self):
        """The manager's nominal `WorkspaceGroup`, proved by adopting a really
        materialized delivery at the factory's own integration root."""
        from baton_v12.integration import runtime as integration_runtime
        from baton_v12.worker_manager import workspaces

        _job, _control, composed = self.serving()
        group = composed.deployment.workspace_group
        self.assertIsInstance(group, workspaces.WorkspaceGroup)
        root = composed.deployment.integration_root
        os.makedirs(root, exist_ok=True)
        made = integration_runtime.materialize_delivery(
            root, attempt_id="attempt-f", workspace_group=group)

        delivery, assignment = composed.integrator._published(
            {"attempt_id": "attempt-f"})
        self.assertEqual(delivery.root, made.root)
        # NOTHING WAS PUBLISHED INTO IT, which is an ordinary answer rather
        # than an invented assignment.
        self.assertIsNone(assignment)


class ThePublicFactoryResolvesEveryRequiredSession(ServingCase):
    """P1: the entry point, not `_sessions` called by hand."""

    def factory(self, **members):
        from tests.job_manager import fixtures
        from .test_single_worker import Engine
        place = os.path.join(self.root, "stage-config.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(self.composed_document(**members), writing)
        job, control = self.stores("stage-factory")
        # THE FACTORY'S OWN READ OF ITS OWN ENVIRONMENT, and then the same
        # composition it performs -- with the two capabilities a focused run
        # supplies in place of a live engine and secret registry, which is
        # what `single_worker`'s own factory cases do.
        with unittest.mock.patch.dict(
                os.environ, {stage_execution.CONFIG_ENV: place}):
            composed = stage_execution.operations_from(
                stage_execution._configuration(), job, control,
                engine_run=Engine(),
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        return composed

    def test_the_five_sessions_are_minted_and_proved(self):
        composed = self.factory()
        self.assertEqual(
            sorted(composed.sessions),
            ["approval", "integrator", "publisher", "review", "verification"])
        for name, session in composed.sessions.items():
            with self.subTest(name=name):
                self.assertIsNotNone(session.participant)

    def test_the_publisher_is_the_producer_and_not_a_configured_name(self):
        """`Authority.publish` takes the producer's live assignment as its
        compare-and-swap operand, and a session refuses to act on one naming
        somebody else -- so any other publisher could only ever be wrong."""
        composed = self.factory()
        self.assertEqual(composed.sessions["publisher"].participant,
                         self.config["participant"])
        self.assertIs(composed.publication.publisher,
                      composed.sessions["publisher"])

    def test_the_integrator_session_is_the_profiles_own_participant(self):
        composed = self.factory()
        self.assertEqual(composed.sessions["integrator"].participant,
                         "baton.integrator")

    def test_a_missing_receipt_participant_refuses_before_serving(self):
        for name in ("verification", "review", "approval"):
            with self.subTest(name=name):
                held = dict(self.document()["receipt_participants"])
                held[name] = ""
                with self.assertRaises(ContractRefusal) as caught:
                    self.serving(receipt_participants=held)
                self.assertIn(name, caught.exception.message)


class TheReceiptActorsAreAuthorizedAndNotMerelyShaped(ServingCase):
    """P1 (review 2026-09-07T14-12-42Z): a callable method is not a grant.

    THE MEASURED SYMPTOM. An independent probe configured `baton.not-configured`
    as this deployment's approval participant. `operations_from` composed a
    serving object, and that object's OWN Authority answered
    `holds_capability(actor, "approve")` false. The configuration had passed
    the gate this module advertises with no authority to write the receipt it
    will be asked for -- and it would have found that out after publication,
    which is the one step a deployment cannot back out of.

    The gate now asks the Authority, in the scope the receipt will actually be
    written in. These cases are over a REAL Authority with real grants, because
    a fake answering `True` would prove only that this file agrees with itself.
    """

    def refused_composition(self, name, **members):
        """One refused composition, with the stores it was refused over."""
        from tests.job_manager import fixtures
        from .test_single_worker import Engine
        job, control = self.stores(name)
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.operations_from(
                self.composed_document(**members), job, control,
                engine_run=Engine(),
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: fixtures.NOW, checkout=self.checkout)
        return caught.exception, job, control

    def assertNothingWasWritten(self, job, control):
        """What a refusal must leave behind, asked of the owners.

        REVIEW [P1] REQUIRED THIS SHAPE rather than "construction raised": the
        old ordering DID raise, and had configured a control store and
        activated a pool on the way. So each fact is read back through the
        owner that would answer it in production -- the workspace group through
        the Worker Manager's own reader, the pool through the scheduler's, and
        the integration store through the filesystem, because a store that was
        never opened has no reader at all.
        """
        from baton_v12.job_manager import scheduler
        from baton_v12.worker_manager import configured_workspace_group
        with self.assertRaises(ContractRefusal):
            configured_workspace_group(control)
        self.assertIsNone(scheduler.active_generation(job))
        self.assertFalse(os.path.exists(self.integration_store))

    def test_every_configured_receipt_actor_really_holds_its_grant(self):
        """The authorized positive, asked of the Authority the COMPOSITION
        opened rather than of the fixture that granted."""
        _job, _control, composed = self.serving()
        for name, capability in stage_execution.RECEIPT_CAPABILITIES.items():
            with self.subTest(name=name):
                self.assertTrue(composed.authority.holds_capability(
                    composed.sessions[name].participant, capability,
                    scope=self.scope))

    def test_an_actor_holding_no_grant_refuses_and_writes_nothing(self):
        held = dict(self.document()["receipt_participants"],
                    approval="baton.not-configured")
        refusal, job, control = self.refused_composition(
            "no-grant", receipt_participants=held)
        self.assertEqual((refusal.category, refusal.code),
                         ("policy", "denied"))
        self.assertIn("baton.not-configured", refusal.message)
        self.assertIn("approve", refusal.message)
        self.assertNothingWasWritten(job, control)

    def test_a_grant_in_another_scope_does_not_reach_this_work(self):
        """The reason the scope is READ from the Work. An actor granted
        `verify` somewhere else holds the capability name and not the
        authorization, and `_write_receipt` -- which derives the scope from the
        Work the proposal belongs to -- would refuse it after publication."""
        from baton_v12.authority import Authority
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.grant_capability("baton.elsewhere", "verify",
                                       scope="scope:elsewhere")
            self.assertFalse(authority.holds_capability(
                "baton.elsewhere", "verify", scope=self.scope))
        finally:
            authority.dispose()
        held = dict(self.document()["receipt_participants"],
                    verification="baton.elsewhere")
        refusal, job, control = self.refused_composition(
            "other-scope", receipt_participants=held)
        self.assertEqual((refusal.category, refusal.code),
                         ("policy", "denied"))
        self.assertIn(self.scope, refusal.message)
        self.assertNothingWasWritten(job, control)

    def test_a_malformed_actor_refuses_in_this_boundarys_own_vocabulary(self):
        """The second half of the same finding: the mint's raw `Refusal`
        escaped, so a fault this module could see in the document it was handed
        arrived as an exception from a package the caller never asked about --
        and it arrived AFTER the control store had been configured."""
        held = dict(self.document()["receipt_participants"],
                    verification="not-an-address")
        refusal, job, control = self.refused_composition(
            "malformed", receipt_participants=held)
        self.assertIsInstance(refusal, ContractRefusal)
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "capability"))
        self.assertIn("not-an-address", refusal.message)
        self.assertNothingWasWritten(job, control)

    def test_a_worker_participant_resolving_elsewhere_refuses_first(self):
        """The identity check moved to the same side of the line, because it
        is one this module can answer from the Authority alone."""
        refusal, job, control = self.refused_composition(
            "principal", workers=[
                self.worker("implementation"),
                self.worker("review", participant="baton.reviewer",
                            principal="principal:somebody-else"),
                self.worker("integration", participant="baton.integrator",
                            principal=self.principals["baton.integrator"])])
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "capability"))
        self.assertIn("principal:somebody-else", refusal.message)
        self.assertNothingWasWritten(job, control)


class ARefusedPoolGenerationLeavesThePoolAlone(ServingCase):
    """P1 (review 2026-09-07T14-12-42Z): the refusal had already activated it.

    With a fresh Job store and a configuration naming generation 4, the
    composition refused for the mismatch -- and `active_generation` had moved
    from `None` to 1, because the comparison read the ANSWER of the activation
    it was meant to prevent. A refusal that changed the thing it refused over
    is not a refusal.
    """

    def test_a_generation_the_next_activation_would_not_answer_refuses(self):
        from baton_v12.job_manager import scheduler
        from tests.job_manager import fixtures
        from .test_single_worker import Engine
        job, control = self.stores("pool-generation")
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.operations_from(
                self.composed_document(pool_generation=4), job, control,
                engine_run=Engine(),
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertIn("before it activates one", caught.exception.message)
        # THE POOL IS EXACTLY AS IT WAS FOUND, read from the scheduler.
        self.assertIsNone(scheduler.active_generation(job))
        self.assertEqual(scheduler.pool_workers(job), [])

    def test_reattaching_to_the_live_generation_is_not_a_new_one(self):
        """The other side of the prediction: composing the same deployment
        twice revalidates generation 1 rather than minting generation 2, so a
        restart under an unchanged configuration is not a pool change."""
        from baton_v12.job_manager import scheduler
        job, _control, first = self.serving()
        self.assertEqual(scheduler.active_generation(job)["generation"], 1)
        first.close()
        job, _control, again = self.serving()
        self.assertEqual(scheduler.active_generation(job)["generation"], 1)
        self.assertEqual(sorted(again.pooled.workers),
                         [(1, "implementation-worker"),
                          (1, "integration-worker"), (1, "review-worker")])


class ThePublicFactoryComposesThroughItsOwnEntryPoint(ServingCase):
    """P1: the exported `factory`, not `operations_from` called beside it.

    REVIEW 2026-09-07T14-12-42Z asked for this exactly: the cases named "public
    factory" invoked `operations_from` after `_configuration`, so the one thing
    `tools.job_manager` actually calls -- `module:attribute` with two operands
    and nothing else -- was never run. This runs it, with the two external
    dependencies a focused case can supply for real: a credential registry on
    disk and this fixture's own engine, which is what `single_worker`'s own
    public-factory case does for the same reason.
    """

    def registry(self):
        """A real user credential registry, so the production provider is the
        one that is built."""
        source = os.path.join(self.root, "provider.token")
        with open(source, "w", encoding="utf-8") as writing:
            writing.write(self.secret)
        os.chmod(source, 0o600)
        place = os.path.join(self.root, "credential-sources.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump({"schema": "baton.user-credential-sources/1",
                       "sources": [{"provider": "fixture",
                                    "reference": "fixture/one",
                                    "path": source}]}, writing)
        os.chmod(place, 0o600)
        return place

    def composed(self, **members):
        registry = self.registry()
        document = self.composed_document(**members)
        for one in document["workers"]:
            one["deployment"] = dict(one["deployment"],
                                     credential_sources=registry)
        place = os.path.join(self.root, "stage-config.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(document, writing)
        job, control = self.stores("public-factory")
        from .test_single_worker import Engine
        # THE TWO SUBSTITUTIONS, NAMED. `factory` takes exactly two operands,
        # so a case cannot inject anything through it -- the engine is this
        # suite's own, for the reason every case here uses one, and `_checkout`
        # is the fixture's, because this suite's disk-backed root must live
        # inside the distribution and the real answer would refuse it for the
        # fixture's reason rather than the one under test. `_checkout` itself
        # is proved separately.
        with unittest.mock.patch.dict(
                os.environ, {stage_execution.CONFIG_ENV: place}), \
                unittest.mock.patch.object(stage_execution, "_checkout",
                                           lambda: self.checkout), \
                unittest.mock.patch.object(stage_execution.single_worker,
                                           "_engine_run", Engine()):
            return job, stage_execution.factory(job, control)

    def test_the_entry_point_job_manager_loads_composes_and_serves(self):
        from baton_v12.job_manager import scheduler
        job, composed = self.composed()
        self.addCleanup(composed.close)
        self.assertEqual(
            sorted(composed.sessions),
            ["approval", "integrator", "publisher", "review", "verification"])
        self.assertIsNotNone(composed.publication)
        self.assertEqual(scheduler.active_generation(job)["generation"], 1)
        # AND ITS ACTORS ARE AUTHORIZED, through the same entry point rather
        # than through a composer a case assembled by hand.
        for name, capability in stage_execution.RECEIPT_CAPABILITIES.items():
            with self.subTest(name=name):
                self.assertTrue(composed.authority.holds_capability(
                    composed.sessions[name].participant, capability,
                    scope=self.scope))

    def test_the_entry_point_refuses_an_unauthorized_actor(self):
        held = dict(self.document()["receipt_participants"],
                    review="baton.not-configured")
        with self.assertRaises(ContractRefusal) as caught:
            self.composed(receipt_participants=held)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertIn("baton.not-configured", caught.exception.message)


class AGenerationOutsideTheInteroperableRangeIsRefused(ServingCase):
    """P2 (review 2026-09-07T14-44-03Z): the ceiling nobody was checking.

    THE MEASURED SYMPTOM. `policy_generation=9007199254740992` counted from one
    and so passed the configuration gate. The composition then created the
    integration store, configured the workspace group and activated a pool --
    and the real approval Session refused that same operand much later, at the
    one moment a deployment cannot back out of, because it is outside the
    interoperable range the Authority publishes.

    Both members are proved, at the ceiling and one past it, because they are
    checked by one rule and an exemption for either would have no reason.
    """

    def test_the_ceiling_itself_is_an_accepted_generation(self):
        """The maximum ACCEPTED value, so the bound refuses what is outside
        the range rather than the edge of it."""
        for name in ("pool_generation", "policy_generation"):
            with self.subTest(name=name):
                held = self.held(**{name: MAX_SAFE_INTEGER})
                self.assertEqual(held[name], MAX_SAFE_INTEGER)

    def test_one_past_the_ceiling_is_refused_as_a_limit(self):
        for name in ("pool_generation", "policy_generation"):
            with self.subTest(name=name):
                caught = self.refused(**{name: MAX_SAFE_INTEGER + 1})
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "limit"))
                self.assertIn(name.replace("_", " "), caught.message)

    def test_counting_from_one_is_still_the_other_half_of_the_rule(self):
        """The existing type, bool and zero checks are preserved rather than
        replaced: a bound above says nothing about the bound below."""
        for value in (0, -1, True, "1", 1.0):
            with self.subTest(value=value):
                caught = self.refused(policy_generation=value)
                self.assertIn("counts from one", caught.message)

    def test_a_generation_past_the_ceiling_writes_nothing(self):
        from baton_v12.job_manager import scheduler
        from baton_v12.worker_manager import configured_workspace_group
        from tests.job_manager import fixtures
        from .test_single_worker import Engine
        job, control = self.stores("policy-ceiling")
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.operations_from(
                self.composed_document(
                    policy_generation=MAX_SAFE_INTEGER + 1), job, control,
                engine_run=Engine(),
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.assertEqual(caught.exception.code, "limit")
        # THE SAME QUESTION THE OTHER PRE-SETUP REFUSALS ARE ASKED, and asked
        # of the owners rather than of the exception: a deployment that would
        # have failed at approval must not have configured a control store or
        # activated a pool on its way to saying so.
        with self.assertRaises(ContractRefusal):
            configured_workspace_group(control)
        self.assertIsNone(scheduler.active_generation(job))
        self.assertFalse(os.path.exists(self.integration_store))

    def test_the_ceiling_is_the_authoritys_own_and_not_a_second_copy(self):
        from baton_v12.authority import MAX_SAFE_INTEGER as published
        self.assertEqual(MAX_SAFE_INTEGER, published)
        self.assertEqual(published, 2 ** 53 - 1)


class TheObservationSurfaceIsSeparateAndReadOnly(ServingCase):
    """P2: `status --observe` receives an object that CANNOT serve."""

    def observing(self):
        self.submitted = []
        job, control = self.stores("stage-observing")
        # The control store's group is what `launch.adopt` validates against,
        # and an observation neither configures nor certifies anything -- so
        # this run composes the serving deployment first, exactly as an
        # operator's `serve` process would already have done.
        self.serving()
        return job, control, stage_execution.observation_from(
            self.composed_document(), job, control, checkout=self.checkout)

    def test_it_carries_the_exchange_read_and_no_act(self):
        from tools import job_manager
        _job, _control, observed = self.observing()
        self.assertEqual(job_manager._exchange_read(observed).__func__,
                         type(observed).observe_exchange)
        for act in ("launch", "dispatch", "conclude", "admit", "claim",
                    "recover", "attach", "drain", "refresh_runtime",
                    "binding_intent", "close", "release"):
            with self.subTest(act=act):
                self.assertIsNone(getattr(observed, act, None))

    def test_a_stage_with_no_allocation_is_answered_by_no_worker(self):
        """The rule `PooledManagerOperations._reader` keeps, for the same
        reason: reporting one worker's silence as another's state is a false
        observation rather than a missing one."""
        _job, _control, observed = self.observing()
        self.assertIsNone(
            observed.observe_exchange({"attempt_id": "attempt-nobody-holds",
                                       "stage_id": "job-a:implementation"}))

    def test_it_reads_through_the_worker_the_scheduler_allocated(self):
        job, _control, observed = self.observing()
        asked = []
        for worker_id in observed.readers:
            observed.readers[worker_id] = type(
                "Reader", (),
                {"observe_exchange":
                 (lambda _self, stage, held=worker_id:
                  asked.append(held) or {"state": held})})()
        # THE SCHEDULER'S OWN RESERVATION, not a hand-written row: which
        # worker holds a stage is exactly the answer this surface must not
        # compose a second idea of.
        stage = self.reserved(job, "review")
        self.assertEqual(observed.observe_exchange(stage),
                         {"state": "review-worker"})
        self.assertEqual(asked, ["review-worker"])
        # AND THE IMPLEMENTATION STAGE REACHES THE OTHER ONE.
        self.assertEqual(observed.observe_exchange(
            self.reserved(job, "implementation")),
            {"state": "implementation-worker"})
        self.assertEqual(asked, ["review-worker", "implementation-worker"])

    def reserved(self, job, kind):
        from baton_v12.job_manager import episodes, scheduler, submit
        from tests.job_manager.test_review_driver import one_work_submission
        if not self.submitted:
            submit(job, one_work_submission())
            self.submitted.append(True)
        stage_id = [row["stage_id"] for row in job._connection.execute(
            "SELECT stage_id, kind FROM stages ORDER BY stage_id")
            if row["kind"] == kind][0]
        live = episodes.live_of(job, stage_id)
        stage = {"stage_id": stage_id, "episode": live["episode"],
                 "attempt_id": live["attempt_id"], "kind": kind,
                 "job_id": stage_id.split(":")[0], "work_id": self.work,
                 "profile_name": self.config["profile_name"],
                 "profile_digest": self.config["profile_digest"]}
        scheduler.reserve(job, stage)
        return stage


class TheReviewersVerdictHasNoChannelAndIsNotInvented(StageCase):
    """The exact missing public capability, reported rather than worked
    around -- the same disposition this leaf took over the absent retained
    proposal manifest, which became W103874."""

    def test_a_composition_with_no_supplied_verdict_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution._no_verdict(None, "attempt-r")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertIn("carries the reviewer's verdict out of its container",
                      caught.exception.message)


# W119114: THE IMAGE'S OWN `source_profiles`, declared here for the same reason
# `test_single_worker` declares the worker directory. `claude_agent` imports it
# as a top-level module because nothing from `baton_v12` travels into that
# image, so a suite that drives the real workload has to put it where the image
# puts it. Declared at import rather than inside a case, so a sharded gate that
# collects this module alone still runs it.
import sys as _sys                                            # noqa: E402

_WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
for _place in (str(_WORKER), str(_WORKER.parent / "python" / "src"
                                 / "baton_v12")):
    if _place not in _sys.path:
        _sys.path.insert(0, _place)


# The three outputs a SHARED Job declares, and which role writes which half.
# `claude_agent.COMMON_OUTPUTS` is the same list one layer over; it is spelled
# here rather than imported so a drift between the image's idea of the set and
# the manifest this deployment composes is caught by a failing case rather than
# hidden behind a shared constant.
SHARED_OUTPUTS = (("proposal", "git-change-proposal"),
                  ("findings", "directory-result"),
                  ("logs", "directory-result"))


class ComposedOneJobCase(ServingCase):
    """W119114: the real factory, ordinary manager ticks, one real worker turn.

    WHAT IS REAL HERE, because that is the whole question this record exists to
    answer and every earlier round in this campaign stopped short of it. The
    serving object is `operations_from`'s own; the Authority, Job, Control and
    Integration stores are real local ones; the development line is a real
    version-controlled checkout materialized by the accepted checkpoint profile
    from a real nominated source; the worker is the actual `claude_agent`
    workload entered through `baton_worker.serve_exchange` over the namespaces
    this deployment mounted; and the ending is `review_driver`'s, so the seal,
    the intake receipt, the retention decision, the publication, the checkpoint
    freeze and the cleanup are the accepted public operations rather than rows
    a fixture wrote.

    THE TWO DETERMINISTIC SEAMS ARE NAMED RATHER THAN IMPLIED, and both are the
    allowance this leaf's ruling already grants. The ENGINE is a callable with
    no daemon, and `quiescing` below models exactly three real facts about one:
    a stopped container stops running, a removed one is positively absent to a
    later inspection IN THE ENGINE'S OWN ABSENCE SENTENCE, and the custody
    helper answers the verb it was asked for. The PROVIDER inside the workload
    is injected, exactly as `test_claude_agent` injects it. Version control is
    not simulated at all.

    WHAT IS NOT REACHED, and is not claimed: no daemon, no container, no image,
    no network, no live model and no live credential.
    """

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority
        from baton_v12.contracts import digest, digest_of_bytes
        from tests.job_manager import fixtures

        # A REAL VERSION-CONTROLLED SOURCE, because the composed line is one.
        # The accepted profile clones it and detaches at the declared base, and
        # a fixture that nominated an ordinary directory would be proving that
        # profile's refusal rather than this deployment's composition.
        self.vcs("init", "-q", "-b", "main")
        self.write(os.path.join(self.source, "harness.py"),
                   "print('the accepted verification ran')\n")
        self.vcs("add", "--all")
        self.vcs("commit", "-q", "--message", "base")
        self.base = self.vcs("rev-parse", "HEAD").strip()

        # THE AUTHORITY'S CANONICAL TARGET IS THAT SAME OBJECT. It is what
        # `retain_proposal` reads and what `publish_candidate` binds to, so a
        # target this Authority cannot name as an object refuses at the
        # publication -- one step past everything these cases are about.
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.base)
        finally:
            authority.dispose()

        self.task_bytes = json.dumps(
            {"schema": "baton.dogfood-task/2",
             "task_id": "w119114-composed-lifecycle",
             "instructions": "Add focused coverage for the composed line.",
             "source_root": "source", "source_profile": "git-line",
             "declared_base": self.base,
             "verification": ["python3", "harness.py"]},
            sort_keys=True).encode("utf-8")
        with open(self.task_document, "wb") as writing:
            writing.write(self.task_bytes)

        # THE ONE MANIFEST A SHARED JOB CARRIES, declaring the union of both
        # stages' outputs. `single_worker._matches` compares every stage
        # against the Job's ONE input digest, so an implementation manifest
        # and a review manifest could never both satisfy it; each role writes
        # its own half
        # and answers the other `missing-optional`. NONE of the three is
        # required for that reason: the worker refuses a required output
        # answered absent, so a declaration the other stage owns being required
        # would be a declaration no single turn can satisfy.
        manifest = copy.deepcopy(self.config["input_manifest"])
        held = manifest["outputs"][0]
        manifest["outputs"] = [dict(held, name=name, type=kind, path=name,
                                    required=False)
                               for name, kind in SHARED_OUTPUTS]
        manifest["human_contract"] = dict(
            manifest["human_contract"], bytes=len(self.task_bytes),
            content_digest=digest_of_bytes(self.task_bytes))
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        self.config["input_manifest"] = manifest
        self.manifest = manifest
        self.submission = fixtures.submission(jobs=[fixtures.job(
            "job-a", input_digest=manifest["manifest_digest"],
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[
                fixtures.stage("implementation", self.work),
                fixtures.stage("review", self.work,
                               depends_on=[{"job_id": "job-a",
                                            "kind": "implementation"}]),
                fixtures.stage("integration", self.work,
                               depends_on=[{"job_id": "job-a",
                                            "kind": "review"}])])])

    # -- real version control, composed environment -------------------------

    def environment(self):
        """What every child here runs under: NO ambient configuration.

        The container has none, so a case that passed only because a global
        hooks path, signing key or identity happened to be set in the ambient
        environment would be passing for a reason the image does not have.
        """
        return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": self.root,
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_TERMINAL_PROMPT": "0"}

    def vcs(self, *arguments):
        """The FIXTURE's own history, with the fixture's own identity.

        Deliberately not the adapter's environment: the adapter composes its
        identity onto its own command line, and lending it one here would erase
        the property that makes its authorship provable inside the image.
        """
        import subprocess

        argv = ["git", "-C", self.source] + list(arguments)
        answer = subprocess.run(
            argv, capture_output=True, text=True, timeout=300,
            env=dict(self.environment(), GIT_AUTHOR_NAME="Baton Test",
                     GIT_AUTHOR_EMAIL="test@baton.invalid",
                     GIT_COMMITTER_NAME="Baton Test",
                     GIT_COMMITTER_EMAIL="test@baton.invalid"))
        self.assertEqual(answer.returncode, 0,
                         f"{argv} failed: {answer.stderr}")
        return answer.stdout

    @staticmethod
    def write(place, body):
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    # -- the deterministic engine seam ---------------------------------------

    def quiescing(self):
        """One engine callable, modelling three real facts and no daemon.

        `Engine` alone cannot carry an ending: `adapter.stop` ORDERS and then
        OBSERVES, and `authorize_cleanup` settles on POSITIVE ABSENCE of the
        exact identity in the engine's own absence sentence -- so a fixture
        that reported the same container forever could reach neither the
        freeze nor a settled cleanup. What is added is only what a real engine
        would do.
        """
        from tests.manager.test_custody import reported

        from .test_single_worker import Engine

        original = Engine.__call__

        def call(engine, argv, *, seconds=None):
            gone = engine.__dict__.setdefault("gone", set())
            if argv[1] == "run" and "--entrypoint" in argv:
                # THE CUSTODY HELPER, and the verb it is answering is its own
                # last operand rather than one this fixture chose.
                engine.vectors.append(list(argv))
                return Engine.answer(stdout=json.dumps(reported(argv[-1])))
            if argv[1] == "rm":
                gone.add(argv[-1])
                if engine.runtime_id == argv[-1]:
                    engine.runtime_id = None
                engine.vectors.append(list(argv))
                return Engine.answer()
            if argv[1] == "inspect" and argv[-1] in gone:
                # THE ENGINE'S OWN SENTENCE, NAMING THIS IDENTITY. `observe`
                # refuses to read absence out of any other prose, and it is
                # right to: a manager that treated confusion as death would
                # release an assignment whose worker is still running.
                engine.vectors.append(list(argv))
                return Engine.answer(
                    status=1,
                    stderr=("Error response from daemon: No such container: "
                            + argv[-1]))
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

    # -- the serving object, and the ticks that drive it ---------------------

    def serving(self, **members):
        from tests.job_manager import fixtures

        self.engine = self.quiescing()
        job, control = self.stores("stage-composed")
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base, **members),
            job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        return job, control, composed

    def states(self, job, composed):
        from baton_v12.job_manager import status as projected_status
        from tests.job_manager import fixtures

        projected = projected_status(job, composed, observed_at=fixtures.NOW)
        return {one["kind"]: one["state"]
                for one in projected["jobs"][0]["stages"]}

    def drive(self, job, composed, kind, want, ticks=10):
        """Ordinary ticks until one stage reaches a state, and no operator act.

        `sweep` is the whole of it. Nothing here reserves an allocation, issues
        an offer, claims, starts, commands or ends anything by hand: every one
        of those is derived from canonical state by the manager this deployment
        was handed to.
        """
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        for _ in range(ticks):
            tick(job, composed, now=fixtures.NOW)
            held = self.states(job, composed)
            if held.get(kind) == want:
                return held
        self.fail(f"the {kind} stage never reached {want!r}: "
                  f"{self.states(job, composed)}")

    def worker_of(self, composed, role):
        return {one["role"]: one["operations"]._worker
                for one in composed.workers}[role]

    def mounted(self, composed, role, attempt_id):
        """The roots this role's container was really started over."""
        held = self.worker_of(composed, role).stage._prepared[attempt_id]
        return held["boundary"]["roots"]

    def only_attempt(self, composed, role):
        held = sorted(self.worker_of(composed, role).stage._prepared)
        self.assertEqual(len(held), 1, held)
        return held[0]

    # -- one real worker turn ------------------------------------------------

    def provider(self, edits=None, status=0):
        """The adapter's one process seam: real version control, and an
        injected model.

        The version-control child really runs; the PROVIDER writes into the
        candidate, which is the only way a real one changes anything; and the
        task's own verification command really runs, because whether it passed
        is a fact the workload publishes, and a fixture that answered it
        would be publishing its own.
        """
        import subprocess

        import claude_agent

        def run(argv, **options):
            if argv[0] == "git":
                return subprocess.run(list(argv), env=self.environment(),
                                      **options)
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                for name, body in (edits or {}).items():
                    self.write(os.path.join(options["cwd"], name), body)
                return subprocess.CompletedProcess(argv, status, None, None)
            return subprocess.run(list(argv), **options)

        return run

    def turn(self, control, role, attempt_id, roots, **operands):
        """One REAL worker turn over exactly the namespaces this run mounted.

        The roots are patched onto the two modules exactly as
        `test_single_worker` and `test_claude_agent` patch them: they are
        CONSTANTS of the workload contract, so there is no operand for a
        deployment to supply and none for a fixture to invent.
        """
        import baton_worker
        import claude_agent

        from baton_v12.contracts import digest
        from tools.single_worker import exchange, launch

        credentials = os.path.join(self.root, "credential-" + attempt_id[:12])
        os.makedirs(credentials, exist_ok=True)
        # A FILE THAT SAYS IT IS NOT A CREDENTIAL. Its content is never read,
        # so a real bearer would prove nothing this does not and would put a
        # secret in a repository.
        self.write(os.path.join(credentials, "claude"), "not-a-credential\n")
        delivered = launch.adopt(
            self.config["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=self.config["launch_contract"], role=role,
            transport=exchange.EXCHANGE_TRANSPORT,
            workspace_group=single_worker.configured_workspace_group(control))
        held = []
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", roots["inputs"]),
                (baton_worker, "OUTPUT_ROOT", roots["workspace"]),
                (claude_agent, "INPUT_ROOT", roots["inputs"]),
                (claude_agent, "OUTPUT_ROOT", roots["workspace"]),
                (claude_agent, "CREDENTIAL_ROOT", credentials)):
            held.append((module, name, getattr(module, name)))
            setattr(module, name, value)
        try:
            scratch = os.path.join(self.root, "scratch-" + attempt_id[:12])
            return baton_worker.serve_exchange(
                claude_agent.ClaudeAgent(run=self.provider(**operands),
                                         home=scratch),
                delivered.document, delivered.document["session"],
                delivered.exchange.command_root, delivered.exchange.event_root)
        finally:
            for module, name, value in held:
                setattr(module, name, value)

    # -- the composed round these cases are about ----------------------------

    def implemented(self, **operands):
        """Submit one Job and carry its implementation stage to its ending.

        Every transition below is a tick. The only thing this method does that a
        serving loop would not is RUN THE CONTAINER, which is the one boundary
        this build has no daemon for.
        """
        from baton_v12.job_manager import submit as submit_jobs

        job, control, composed = self.serving()
        submit_jobs(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        attempt_id = self.only_attempt(composed, "implementation")
        roots = self.mounted(composed, "implementation", attempt_id)
        operands.setdefault("edits",
                            {"harness.py": "print('the corrected harness')\n"})
        self.assertEqual(
            self.turn(control, "implementation", attempt_id, roots,
                      **operands), 0)
        self.drive(job, composed, "implementation", "completed")
        return SimpleNamespace(job=job, control=control, composed=composed,
                               attempt_id=attempt_id, roots=roots)


class TheComposedImplementationHalfRunsOnOrdinaryTicks(ComposedOneJobCase):
    """W119114 item 3, for the half the undischarged gate leaves reachable.

    Every earlier round of this campaign proved its own component and stopped.
    This drives the composed thing: one submitted Job, the factory's own serving
    object, and nothing but `sweep` between the submission and a completed
    implementation stage carrying a published proposal and a frozen checkpoint.
    """

    def test_one_submitted_job_reaches_a_completed_implementation_stage(self):
        """No operator transition after the submission, measured as one.

        The pool activation, the offer, the claim, the attempt, its activation,
        the line, the mount, the start, the command and the whole ending are all
        derived from canonical state by the manager.
        """
        held = self.implemented()
        self.assertEqual(self.states(held.job, held.composed)["implementation"],
                         "completed")
        # ONE WORKER CONTAINER EVER, for one attempt. The custody helper runs
        # are the manager's own normalization acts and are counted apart: they
        # carry `--entrypoint`, which no worker start does.
        self.assertEqual(
            len([one for one in self.engine.starts
                 if "--entrypoint" not in one]), 1)

    def test_the_real_worker_committed_the_line_and_claimed_its_objects(self):
        """The producer is the actual workload, so its claim is its own.

        `retain_proposal` reads exactly this claim out of the frozen result, and
        a deployment that composed one would be asserting what the result is
        supposed to prove.
        """
        import claude_agent
        from baton_v12.worker_manager import frozen_output_of, load_manifest

        held = self.implemented()
        frozen = frozen_output_of(held.control, held.attempt_id)
        sealed = load_manifest(held.control, frozen["manifest_digest"],
                               "resultManifest")
        [produced] = [one for one in sealed["outputs"]
                      if one["status"] == "present"]
        self.assertEqual(produced["name"], "proposal")
        claim = produced["result_metadata"][claude_agent.CLAIM_NAMESPACE]
        self.assertEqual(claim["base"], self.base)
        self.assertNotEqual(claim["head"], self.base)
        self.assertEqual(claim["transport"], "objects.bundle")
        # AND THE OTHER STAGE'S HALF IS ABSENT RATHER THAN INVENTED, which is
        # the shared-Job declaration set working.
        self.assertEqual(sorted(one["name"] for one in sealed["outputs"]
                                if one["status"] != "present"),
                         ["findings", "logs"])

    def test_the_ending_reached_every_accepted_owner(self):
        """Read back from each owner's own durable record, not from the answer
        the composition returned."""
        from baton_v12.worker_manager import (attempt_runtime_of,
                                              frozen_output_of,
                                              intake_receipt_of, line_of,
                                              retentions_of)

        held = self.implemented()
        self.assertEqual(frozen_output_of(held.control,
                                          held.attempt_id)["disposition"],
                         "completed")
        self.assertIsNotNone(intake_receipt_of(held.control, held.attempt_id))
        self.assertEqual(
            [one["disposition"]
             for one in retentions_of(held.control, held.attempt_id)],
            ["retain"])
        runtime = attempt_runtime_of(held.control, held.attempt_id)
        # POSITIVE ABSENCE OF THE EXACT RUNTIME, which is what an ordinary
        # cleanup settles on and what a `failed` one does not reach.
        self.assertEqual(runtime["execution_runtime"], "destroyed")
        line = line_of(held.control, held.composed.deployment.line()["line_id"])
        self.assertEqual(line["revision"], 1)
        self.assertIsNotNone(line["current_checkpoint_id"])

    def test_the_publication_named_the_proposal_the_authority_recorded(self):
        """The publication is the real one, so the accepted checkpoint's own
        writer chain replays to the identity the Authority holds."""
        from baton_v12.worker_manager import integration_checkpoint

        held = self.implemented()
        line = held.composed.deployment.line()
        accepted = integration_checkpoint(held.control, line["line_id"])
        # THE LINE IS AWAITING REVIEW, so no checkpoint is accepted for
        # integration yet -- which is the honest state at this boundary.
        self.assertIsNone(accepted)
        # AND THE PROPOSAL IS STILL RESOLVABLE FROM THE FROZEN CHECKPOINT'S
        # OWN WRITER, which is the replay `published_proposal` performs.
        self.assertIsNotNone(
            held.composed.deployment.published_proposal(
                {"checkpoint_id": line["current_checkpoint_id"]}))


class TheRetainedResultReopensAfterOrdinaryCleanup(ComposedOneJobCase):
    """W105982's one remaining acceptance check, carried here as its review
    `review-2026-09-07T15-46-38Z.md` directed.

    THE CHECK IS ABOUT BYTES, and the review says so in as many words: a
    pathname assertion, a surviving checkpoint reference, a fixture teardown or
    a canned receipt cannot substitute. So the sealed result is really retained
    by `request_intake` and `decide_retention`, ordinary manager-authorized
    cleanup really settles, and only then are the artifact bytes reopened AT
    THEIR RECORDED LOCATOR and measured against the digest the receipt carries.
    """

    def retained(self, held):
        from baton_v12.worker_manager import intake_receipt_of

        receipt = intake_receipt_of(held.control, held.attempt_id)
        [artifact] = receipt["artifacts"]
        place = artifact["custody_locator"]
        self.assertTrue(place.startswith("file://"), place)
        return artifact, place[len("file://"):]

    @staticmethod
    def measured(place):
        """The content manifest of one tree, by the rules the manager uses."""
        import hashlib

        entries = []
        for base, _directories, names in os.walk(place):
            for one in sorted(names):
                whole = os.path.join(base, one)
                with open(whole, "rb") as reading:
                    body = reading.read()
                entries.append({"path": os.path.relpath(whole, place),
                                "bytes": len(body),
                                "content_digest": "sha256:" + hashlib.sha256(
                                    body).hexdigest()})
        entries.sort(key=lambda one: one["path"].encode("utf-8"))
        return entries

    def test_the_cleanup_that_ran_was_the_ordinary_authorized_one(self):
        """`retained` is TERMINAL and is not `complete`, and neither is
        `failed`: material kept on purpose and a runtime that survived its own
        removal are different endings, and only one of them is this proof."""
        held = self.implemented()
        row = held.control._connection.execute(
            "SELECT cleanup FROM attempts WHERE runtime_attempt_id = ?",
            (held.attempt_id,)).fetchone()
        self.assertEqual(row["cleanup"], "retained")

    def test_the_artifact_bytes_reopen_at_their_recorded_locator(self):
        from baton_v12.contracts import digest

        held = self.implemented()
        artifact, place = self.retained(held)
        entries = self.measured(place)
        self.assertTrue(entries, place)
        self.assertEqual(digest(entries), artifact["content_digest"])

    def test_the_retained_manifest_reopens_and_names_those_same_bytes(self):
        from baton_v12.worker_manager import frozen_output_of, load_manifest

        held = self.implemented()
        artifact, _place = self.retained(held)
        frozen = frozen_output_of(held.control, held.attempt_id)
        sealed = load_manifest(held.control, frozen["manifest_digest"],
                               "resultManifest")
        self.assertIsNotNone(sealed)
        [produced] = [one for one in sealed["outputs"]
                      if one["status"] == "present"]
        self.assertEqual(produced["artifact"]["content_digest"],
                         artifact["content_digest"])
        self.assertEqual(produced["artifact"]["artifact_id"],
                         artifact["artifact_id"])

    def test_the_retained_sibling_was_never_a_writable_worker_mount(self):
        """The custody tree is beside the line, not inside it.

        `roots['workspace']` is the directory this attempt's container had
        WRITABLE -- the line checkout itself under this profile -- so the
        containment question is asked of the real mount rather than of a
        pathname this case composed.
        """
        held = self.implemented()
        _artifact, place = self.retained(held)
        writable = os.path.realpath(held.roots["workspace"])
        self.assertFalse(
            os.path.realpath(place).startswith(writable + os.sep),
            f"{place} is inside the writable mount {writable}")
        # AND IT IS THE LINE'S OWN SIBLING rather than an unrelated directory:
        # the custody tree and the checkout share the line's root.
        self.assertEqual(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.realpath(place)))),
            os.path.dirname(writable))

    def test_the_persistent_line_and_its_pin_survive_that_cleanup(self):
        """Ordinary attempt cleanup neither deletes the line nor moves its pin.

        The checkpoint is re-validated through the accepted profile over the
        real repository, so this is the pin being REOPENED rather than a row
        being read back.
        """
        from baton_v12.worker_manager import checkpoint_of, line_of

        held = self.implemented()
        line = line_of(held.control,
                       held.composed.deployment.line()["line_id"])
        self.assertEqual(line["state"], "review-ready")
        self.assertTrue(os.path.isdir(held.roots["workspace"]))
        checkpoint = checkpoint_of(held.control, line["current_checkpoint_id"])
        validated = held.composed.deployment.profile.validate(
            held.roots["workspace"], checkpoint["evidence"])
        self.assertEqual(validated, checkpoint["evidence"])
        self.assertEqual(validated["base"], self.base)


class TheComposedHandoffStopsAtTheUndischargedQuiescenceGate(
        ComposedOneJobCase):
    """W119548, measured here because this is where it stops the campaign.

    The implementation ending FENCES the producer assignment at the checkpoint
    freeze, and the Authority installs `runtime-quiescence:<generation>`. The
    review stage of a composed Job is another assignment of the SAME Work -- the
    configuration refuses a review stage naming another Work, and a line is one
    `(authority_uuid, work_id)` pair -- so that gate holds the whole lifecycle.

    NOTHING IN THIS BUILD DISCHARGES IT. `worker_manager.SESSION_OPERATIONS`
    omits `satisfy_gate`, so the manager's port cannot reach the Authority
    operation that would; no production caller of it exists; and `attempts.py`
    says so in as many words. The manager DOES hold the evidence the gate
    requires -- the case above measures `execution_runtime == 'destroyed'` --
    so what is missing is an accepted act carrying it across, which is W119548's
    and deliberately not this five-path scope's to invent.

    THESE CASES ARE THE REGRESSION FOR THAT WORK. When it lands they fail, and
    the composed lifecycle continues from exactly here.
    """

    def test_the_manager_cannot_reach_the_operation_that_would_discharge_it(
            self):
        from baton_v12.worker_manager import SESSION_OPERATIONS

        self.assertNotIn("satisfy_gate", SESSION_OPERATIONS)

    def test_the_completed_implementation_leaves_the_work_gated(self):
        from baton_v12.authority import Authority

        held = self.implemented()
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            work = authority.project_work(self.work)
        finally:
            authority.dispose()
        self.assertEqual(work["phase"], "block")
        self.assertEqual(work["gate"]["kind"], "runtime-quiescence")
        self.assertFalse(work["ready"])

    def test_the_review_stage_is_queued_and_its_offer_is_refused(self):
        """The stage is eligible and its gate is open; what refuses is the
        offer, against a Work the checkpoint fence left blocked."""
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.implemented()
        report = tick(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(self.states(held.job, held.composed)["review"],
                         "queued")
        [admit] = [one for one in report["acts"]
                   if one.get("act") == "admit"]
        self.assertEqual(admit["outcome"], "deferred")
        self.assertIn("ungated Work", admit["detail"]["message"])


# -- W119114: the two consumer seams the accepted providers require -----------
#
# `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/
# finding-standalone-stage-composition/findings/finding-composed-one-job-proof/`.
#
# BOTH ARE BOUNDED CORRECTIONS INSIDE THE FIVE OWNED PATHS, and neither is the
# assembled lifecycle proof this Work still owes. What they close is the pair
# of places where the accepted drivers now expect something this deployment did
# not yet provide: the publication seam's replay half, and a second `conclude`
# that used to refuse at `grant_writer`.


class TheDeploymentAnswersTheAcceptedReplayHalves(unittest.TestCase):

    def test_the_publication_seam_carries_the_verb_the_driver_names(self):
        """`PUBLICATION_HISTORY` is typed inside the resumed branch only.

        An ordinary ending still needs one verb, so this asserts the seam
        answers both rather than that the driver requires both.
        """
        self.assertEqual(review_driver.PUBLICATION_SEAM, ("publish",))
        self.assertEqual(review_driver.PUBLICATION_HISTORY,
                         ("published_of",))
        for verb in review_driver.PUBLICATION_SEAM + \
                review_driver.PUBLICATION_HISTORY:
            self.assertTrue(
                callable(getattr(stage_execution.Publication, verb, None)),
                verb)

    def test_the_replay_half_reads_the_owner_and_not_its_own_list(self):
        """An in-memory list says nothing about a process that has died.

        `published_of` must reach `publication_for_attempt`, which takes no
        publisher and no remembered selector; a seam answering from
        `self.published` would satisfy the driver's shape and fail every
        restart.
        """
        publication = stage_execution.Publication(object(), object())
        publication.published.append({"attempt_id": "attempt-1"})
        with mock.patch.object(stage_execution, "publication_for_attempt",
                               return_value=None) as owner:
            self.assertIsNone(
                publication.published_of(attempt_id="attempt-1"))
        self.assertEqual(owner.call_args.kwargs, {"attempt_id": "attempt-1"})
        self.assertEqual(owner.call_args.args, (publication.control,))
