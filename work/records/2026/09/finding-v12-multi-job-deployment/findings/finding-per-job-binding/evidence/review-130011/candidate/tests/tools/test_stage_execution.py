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

from tools import integration_worker, single_worker, stage_execution

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

    INTEGRATION_ROUTE = "integration"

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
        """W119403: the value this case used to name is now a variant this
        deployment SERVES, so it names one that is not.

        The rule it is about has not moved -- a document whose schema this
        build does not read is refused, and the refusal still names what it
        does read. What changed is only which value is foreign.
        """
        held = self.refused(schema="baton.v12.stage-execution-deployment/9")
        self.assertIn(stage_execution.CONFIG_SCHEMA, held.message)
        self.assertIn(stage_execution.MULTI_CONFIG_SCHEMA, held.message)

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
            # W122060: AND THE TWO ROUTES THE ORDINARY HANDOFF MOVES THIS WORK
            # TO. The routing record is explicit that the existing per-worker
            # `review_route` operand is the source and that a deployment
            # configures it rather than a new map supplying it -- so the
            # Authority has to know which participant serves each of those
            # routes, exactly as `SingleWorkerCase` already declares the
            # implementation one. Without this the reviewer's claim refuses
            # against a route nobody handles, which is a fixture that never
            # authorized the next role rather than a defect in the handoff.
            for route, who in (("rview", "baton.reviewer"),
                               (self.INTEGRATION_ROUTE, "baton.integrator")):
                authority.add_route_handler(route, who)
        finally:
            authority.dispose()

    def composed_document(self, **members):
        given = {
            "job_work_id": self.work, "review_work_id": self.work,
            "workers": [
                self.worker("implementation"),
                # W122060: THE REVIEW WORKER'S OWN OUTGOING ROUTE. Each
                # worker carries the route its own ending hands the Work on
                # to: the implementation worker's is the review route it
                # already declares, and the review worker's is the one the
                # integration role is served on. One operand per worker, which
                # is the operand this deployment already had.
                self.worker("review", participant="baton.reviewer",
                            principal=self.principals["baton.reviewer"],
                            review_route=self.INTEGRATION_ROUTE),
                self.worker(
                    "integration", participant="baton.integrator",
                    principal=self.principals["baton.integrator"],
                    # W122060: THE SLOT THE ACCEPTED INTEGRATION PORT READS ITS
                    # BEARER FROM. `integration_worker` names it, and a
                    # deployment resolving another slot is refused there rather
                    # than discovering it with a candidate published.
                    credential_slots=[integration_worker
                                      .REQUIRED_CREDENTIAL_SLOT],
                    credential_profile={
                        integration_worker.REQUIRED_CREDENTIAL_SLOT: {
                            "provider": "fixture",
                            "reference": "fixture/one"}})]}
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
            if argv[1] == "run":
                # W122060: ONE IDENTITY PER STARTED RUNTIME, which a lifecycle
                # with three roles needs and one with a single implementation
                # attempt never did. `Engine` mints `runtime-single-1` every
                # time; after the first attempt's `rm` that identity is in
                # `gone`, so the reviewer's brand-new container was reported
                # absent the moment it started and its stage projected
                # `exceptional`. The first identity is unchanged, so every
                # single-runtime expectation above still reads as it did.
                answer = original(engine, argv, seconds=seconds)
                minted = engine.__dict__.setdefault("minted", [])
                minted.append(f"runtime-single-{len(minted) + 1}")
                engine.runtime_id = minted[-1]
                # AND A FRESH RUNTIME IS RUNNING, whatever the last one did.
                engine.stopped = False
                del answer
                return Engine.answer(stdout=engine.runtime_id + "\n")
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
        # W122060: HELD SO `turn` CAN ASK THIS ROLE WHAT IT MOUNTED. A review
        # turn needs the boundary the manager composed, and the fixture's one
        # serving object is where that lives.
        self._composed = composed
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
        roots = self.mounted_view(role, attempt_id, roots)
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
            os.makedirs(scratch, exist_ok=True)
            return baton_worker.serve_exchange(
                claude_agent.ClaudeAgent(run=self.provider(**operands),
                                         home=scratch),
                delivered.document, delivered.document["session"],
                delivered.exchange.command_root, delivered.exchange.event_root)
        finally:
            for module, name, value in held:
                setattr(module, name, value)

    def mounted_view(self, role, attempt_id, roots):
        """What this role's container would SEE, composed outside one.

        W122060. THE ROLES DIFFER IN WHERE THE LINE IS, and only the review
        role needed anything: an implementation attempt mounts the line
        WRITABLE as its own workspace, which is an ordinary directory this
        fixture can hand the workload; a review attempt mounts the frozen
        checkpoint READ-ONLY at `/input/source`, and outside a container that
        mountpoint is the empty directory the frozen manifest declares.

        SO THE BIND IS COMPOSED AS A LINK, from the boundary's OWN nominated
        source rather than from a path this fixture picked. It is the same
        thing `turn` already does for `INPUT_ROOT`, `OUTPUT_ROOT` and
        `CREDENTIAL_ROOT`: this deployment has no daemon, so the container's
        view is assembled here and the workload runs against it unchanged.
        """
        if role != "review":
            return roots
        boundary = self.worker_of(self.composed_for(role),
                                  role).stage._prepared[attempt_id]["boundary"]
        staged = os.path.join(self.root, "mounted-" + attempt_id[:12])
        os.makedirs(staged, exist_ok=True)
        for entry in sorted(os.listdir(roots["inputs"])):
            target = os.path.join(staged, entry)
            if os.path.lexists(target):
                continue
            os.symlink(boundary["boundary"].source.place if entry == "source"
                       else os.path.join(roots["inputs"], entry), target)
        return dict(roots, inputs=staged)

    def composed_for(self, role):
        """The serving object this fixture is driving, held for `turn`."""
        del role
        return self._composed

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


def delattr_if_set(held, name):
    """Undo an instance attribute that shadows a class method."""
    if name in vars(held):
        delattr(held, name)


class TheComposedHandoffCarriesItsOwnQuiescenceEvidence(ComposedOneJobCase):
    """W122060, converting W119114's three scheduled assertions.

    THESE THREE USED TO MEASURE THE ABSENCE OF W119548 and said so: the
    manager's port could not reach the Authority's gate discharge, the
    completed implementation left the Work blocked on
    `runtime-quiescence:<generation>`, and the review stage's offer was refused
    against that blocked Work. All three were written as the regression for the
    Work that would land the missing act, with "when it lands they fail, and
    the composed lifecycle continues from exactly here."

    IT LANDED, AND THIS IS FROM EXACTLY HERE. The implementation ending now
    registers its obligation, runs the accepted driver, carries the manager's
    own committed positive-absence proof to the gate, routes what the answer
    earned and only then settles -- so the Work is ungated and queued when the
    ending finishes and the review stage's offer is issued on an ordinary tick.

    Owner event119712 scheduled exactly this conversion, including the class
    rename. The prior file and its reproduction are preserved in the record.
    """

    def test_the_manager_can_reach_the_operation_that_discharges_it(self):
        """W121887's accepted forwarding, measured where it is consumed.

        `satisfy_gate` is deliberately NOT in `SESSION_OPERATIONS`: that tuple
        is a CONSTRUCTION requirement, and two production deployments in this
        distribution compose narrower sessions. It is the port's one named
        optional operation, and this deployment's session forwards it exactly.
        """
        from baton_v12.worker_manager import (OPTIONAL_SESSION_OPERATIONS,
                                              SESSION_OPERATIONS)

        self.assertNotIn("satisfy_gate", SESSION_OPERATIONS)
        self.assertIn("satisfy_gate", OPTIONAL_SESSION_OPERATIONS)
        forwarding = single_worker._AuthoritySession.satisfy_gate
        self.assertTrue(callable(forwarding))
        held = []

        class Session:
            participant = "baton.impl"

            def satisfy_gate(self, operands):
                held.append(operands)
                return {"gate": operands["gate"], "kind": "runtime-absent",
                        "phase": "queued"}

        answer = single_worker._AuthoritySession(Session()).satisfy_gate(
            {"work_id": self.work, "operation_id": "op-1", "gate": "g",
             "evidence": {"kind": "runtime-absent", "runtime": "runtime-1"}})
        # EXACTLY THE OPERANDS, UNCHANGED. A forwarding member that composed
        # anything would be a second author of an act it only carries.
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["gate"], "g")
        self.assertEqual(answer["phase"], "queued")

    def test_the_completed_implementation_leaves_the_work_ungated(self):
        """The converted assertion: `block` on a quiescence gate became
        `queued` with no gate at all, and the manager's own committed cleanup
        is what cleared it."""
        from baton_v12.authority import Authority

        held = self.implemented()
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            work = authority.project_work(self.work)
        finally:
            authority.dispose()
        self.assertEqual(work["phase"], "queued")
        self.assertIsNone(work["gate"])
        self.assertTrue(work["ready"])

    def test_the_review_stage_is_queued_and_its_offer_is_issued(self):
        """The converted assertion: the offer used to be DEFERRED against an
        ungated Work, and an ordinary tick now issues it."""
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.implemented()
        self.assertEqual(self.states(held.job, held.composed)["review"],
                         "queued")
        report = tick(held.job, held.composed, now=fixtures.NOW)
        [admit] = [one for one in report["acts"] if one.get("act") == "admit"]
        self.assertEqual(admit["outcome"], "performed")
        self.assertEqual(self.states(held.job, held.composed)["review"],
                         "offered")


class TheComposedEndingIsOrderedAndSettledFromItsOwnRecord(ComposedOneJobCase):
    """W122060: the obligation, the order, and the re-entry after cleanup.

    The composed ending's last act is not the driver's. Cleanup commits, and
    the gate discharge and the routing still have to happen -- so between them
    every live projection says the attempt is over and the ending is not. The
    intent is what makes that window discoverable and the settlement is what
    closes it, and both are measured here through ordinary ticks.
    """

    def cleaned_up(self):
        """One implementation attempt whose CLEANUP has committed and whose
        ending has not settled.

        THE WINDOW THIS WHOLE WORK IS ABOUT, and it is reached by ordinary
        ticks rather than composed: the first conclude after the worker turn
        runs the accepted ending all the way through `authorize_cleanup`, and
        the acts still owed -- the gate discharge and the routing -- come
        after it. The runtime is destroyed, the writer is revoked, the two
        roots are gone, and the obligation is registered and open.
        """
        from baton_v12.job_manager import submit as submit_jobs, sweep as tick
        from baton_v12.worker_manager import attempt_runtime_of
        from tests.job_manager import fixtures

        job, control, composed = self.serving()
        submit_jobs(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        attempt_id = self.only_attempt(composed, "implementation")
        roots = self.mounted(composed, "implementation", attempt_id)
        self.assertEqual(
            self.turn(control, "implementation", attempt_id, roots,
                      edits={"harness.py": "print('the corrected harness')\n"}),
            0)
        # ONE WITHHELD ACT, and it is withheld deliberately now. W124782's
        # accepted receipt fix means the ordinary ending settles on its first
        # tick, so the window these cases are about -- cleanup committed,
        # obligation open -- no longer happens by accident. Refusing the
        # discharge once produces exactly it, and the ending's own re-entry is
        # then what the cases measure.
        with mock.patch.object(
                stage_execution, "discharge_quiescence_gate",
                side_effect=ContractRefusal(
                    "refused", "precondition",
                    "the fixture withholds this discharge once")):
            tick(job, composed, now=fixtures.NOW)
        held = SimpleNamespace(job=job, control=control, composed=composed,
                               attempt_id=attempt_id, roots=roots)
        self.assertEqual(
            attempt_runtime_of(control, attempt_id)["execution_runtime"],
            "destroyed")
        record = self.ending_records(held)
        self.assertIsNotNone(record["intent"])
        self.assertIsNone(record["settlement"])
        return held

    def ending_records(self, held):
        from baton_v12.job_manager import ending as obligations

        stage_id = held.job._connection.execute(
            "SELECT stage_id FROM stages WHERE kind = 'implementation'"
        ).fetchone()[0]
        return obligations.ending_of(held.job, stage_id, 1)

    def test_the_obligation_is_registered_and_settled_by_ordinary_ticks(self):
        held = self.implemented()
        record = self.ending_records(held)
        self.assertIsNotNone(record["intent"])
        self.assertIsNotNone(record["settlement"])
        intent = record["intent"]
        self.assertEqual(intent["attempt_id"], held.attempt_id)
        self.assertEqual(intent["kind"], "implementation")
        self.assertEqual(intent["disposition"], "completed")

    def test_the_settlement_names_the_records_that_finished_the_ending(self):
        """Every member is an identity an operator can look up in the owner
        that produced it, which is the whole reason a settlement carries any."""
        from baton_v12.worker_manager import (frozen_output_of,
                                              intake_receipt_of, review_cycles)

        held = self.implemented()
        evidence = self.ending_records(held)["settlement"]["evidence"]
        frozen = frozen_output_of(held.control, held.attempt_id)
        receipt = intake_receipt_of(held.control, held.attempt_id)
        self.assertEqual(evidence["result_id"], frozen["result_id"])
        self.assertEqual(evidence["manifest_digest"],
                         frozen["manifest_digest"])
        self.assertEqual(evidence["receipt_digest"], receipt["receipt_digest"])
        checkpoint = review_cycles.checkpoint_of(held.control,
                                                 evidence["checkpoint_id"])
        writer = review_cycles.writer_of(held.control,
                                         checkpoint["writer_id"])
        self.assertEqual(writer["runtime_attempt_id"], held.attempt_id)

    def test_a_reconstructed_manager_re_enters_the_same_ending(self):
        """THE CUTPOINT THIS WORK EXISTS FOR, driven through the actual
        serving entry rather than asserted about a warm cache.

        Clearing `_prepared` is a reconstructed manager: the process that
        granted the writer is gone and the durable records are all that is
        left. The ending re-enters, recovers its writer from the attempt and
        generation rather than from the line's moved pointer, and starts,
        publishes, freezes and destroys nothing a second time.
        """
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.cleaned_up()
        before = self.publications(held)
        checkpoint = self.checkpoints(held)
        composition = self.worker_of(held.composed, "implementation").stage
        composition._prepared.clear()
        starts = len([one for one in self.engine.starts
                      if "--entrypoint" not in one])
        report = tick(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(
            [one for one in report["spoken"]
             if one["outcome"] == "deferred"], [])
        self.assertIsNotNone(self.ending_records(held)["settlement"])
        self.assertEqual(self.publications(held), before)
        self.assertEqual(self.checkpoints(held), checkpoint)
        self.assertEqual(len([one for one in self.engine.starts
                              if "--entrypoint" not in one]), starts)

    def test_the_recovered_writer_is_the_attempts_and_not_the_lines_pointer(
            self):
        """The durable operand, read through the accepted public reader."""
        from baton_v12.worker_manager import review_cycles

        held = self.cleaned_up()
        composition = self.worker_of(held.composed, "implementation").stage
        composition._prepared.clear()
        # W119405: `_prepare` takes the STAGE now, because the line it grants
        # on belongs to that stage's Job. What this case is about -- the
        # recovered writer being the ATTEMPT'S and not the line pointer's -- is
        # unchanged; only how the attempt is handed over moved.
        recovered = composition._prepare(
            {"stage_id": "job-a/implementation", "job_id": "job-a",
             "attempt_id": held.attempt_id, "kind": "implementation"})
        writer = review_cycles.writer_for_attempt(
            held.control, attempt_id=held.attempt_id,
            generation=recovered["generation"])
        self.assertEqual(recovered["writer_id"], writer["writer_id"])
        self.assertEqual(recovered["based_checkpoint_id"],
                         writer["based_checkpoint_id"])
        # AND IT MOUNTS NOTHING, because the writer this round left behind is
        # revoked. `mount` refuses rather than handing a null to a caller that
        # subscripts it.
        self.assertIsNone(recovered["boundary"])
        self.assertEqual(writer["state"], "revoked")
        with self.assertRaises(ContractRefusal) as caught:
            composition.mount(None, {"attempt_id": held.attempt_id}, None)
        self.assertIn("mounts nothing", str(caught.exception))

    def test_the_historical_entry_reconstructs_no_mount_or_credential(self):
        """The entry the ordinary ending cannot be.

        `_SingleWorker.ending` re-mounts the roots this attempt was started
        over, materializes its credential and composes a runtime adapter from
        both, before it reaches the composition. After the cleanup none of
        those exists: the writer that made the mount is revoked and the two
        roots are gone. This drives that none of them is reached and that the
        ending still completes from its recorded obligation.

        `_adopted` IS DELIBERATELY NOT AMONG THEM. The sweep's own projection
        observes the exchange to report a stage's state, which is a read this
        composition owes whatever the ending does; refusing it here would
        prove this about the projection rather than about the ending. What the
        ending must not do is take its DISPOSITION or its TERMINAL from that
        delivery, and the case below measures that directly: both come from
        the registered obligation.
        """
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.cleaned_up()
        worker = self.worker_of(held.composed, "implementation")
        worker.stage._prepared.clear()

        def never(*arguments, **operands):
            del arguments, operands
            raise AssertionError("the historical entry reconstructed live "
                                 "evidence")

        # ON THE INSTANCE, NOT THE CLASS. The review worker is another
        # `_SingleWorker`, and patching the class would refuse its ordinary
        # launch as well -- which would prove this about the wrong attempt.
        for verb in ("_mounted", "_credential", "_adapter"):
            self.addCleanup(delattr_if_set, worker, verb)
            setattr(worker, verb, never)
        report = tick(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual([one for one in report["spoken"]
                          if one["outcome"] == "deferred"], [])
        self.assertIsNotNone(self.ending_records(held)["settlement"])

    def test_the_historical_operands_come_from_the_recorded_obligation(self):
        """Not from the exchange the ordinary ending reads them off."""
        held = self.cleaned_up()
        worker = self.worker_of(held.composed, "implementation")
        stage = self.attempting(held)
        historical = worker.stage.historical(stage, {"work_ref": {}})
        intent = self.ending_records(held)["intent"]
        self.assertEqual(historical["disposition"], intent["disposition"])
        self.assertEqual(historical["terminal"]["manifest_digest"],
                         intent["terminal_manifest_digest"])
        self.assertEqual(historical["terminal"]["ending"], "answered")

    def attempting(self, held):
        from baton_v12.job_manager import episodes, submission

        stage_id = held.job._connection.execute(
            "SELECT stage_id FROM stages WHERE kind = 'implementation'"
        ).fetchone()[0]
        [stage] = [one for one in submission.stage_rows(held.job)
                   if one["stage_id"] == stage_id]
        return episodes.attempting(stage,
                                   episodes.episodes_of(held.job, stage_id)[0])

    def test_the_historical_adapter_can_perform_no_runtime_act(self):
        """A property of the object rather than a promise about the path."""
        adapter = single_worker._RecordedRuntime("sha256:" + "a" * 64)
        self.assertEqual(adapter.custodian_image_digest, "sha256:" + "a" * 64)
        for verb in review_driver.RUNTIME_ADAPTER:
            with self.subTest(verb=verb):
                held = getattr(adapter, verb, None)
                self.assertTrue(callable(held), verb)
                with self.assertRaises(ContractRefusal) as caught:
                    held()
                self.assertEqual(caught.exception.category, "refused")
                self.assertIn(verb, str(caught.exception))

    def publications(self, held):
        from baton_v12.integration import publication_for_attempt

        return publication_for_attempt(held.control,
                                       attempt_id=held.attempt_id)

    @staticmethod
    def checkpoints(held):
        return held.control._connection.execute(
            "SELECT count(*), max(checkpoint_id) FROM line_checkpoints"
        ).fetchone()[:]


class TheDischargeReceiptIsCommittedWithItsOwnKind(ComposedOneJobCase):
    """W122060, converting the regression W124782 landed the fix for.

    THIS USED TO PIN A DEFECT. `Authority.satisfy_gate` answers `kind` with
    the EVIDENCE's kind -- `runtime-absent`, the thing this manager proved --
    and `intake.discharge_quiescence_gate` required the GATE kind, so the
    remote act committed, the gate cleared, and the local receipt was never
    written. The provider now compares against the evidence kind it actually
    sends, and the receipt commits.

    The cases below are the same two facts, read the other way round.
    """

    def test_the_ordinary_ending_journals_its_gate_discharge(self):
        from baton_v12.worker_manager import gate_discharge_of

        held = self.implemented()
        receipt = gate_discharge_of(held.control, held.attempt_id)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["attempt_id"], held.attempt_id)
        self.assertEqual(receipt["kind"], "runtime-absent")
        self.assertEqual(receipt["phase"], "queued")
        self.assertTrue(receipt["gate"].startswith("runtime-quiescence:"))

    def test_the_settlement_names_that_discharge(self):
        """The obligation is closed naming the act that cleared the gate."""
        held = self.implemented()
        stage_id = held.job._connection.execute(
            "SELECT stage_id FROM stages WHERE kind = 'implementation'"
        ).fetchone()[0]
        from baton_v12.job_manager import ending as obligations

        settlement = obligations.ending_of(held.job, stage_id, 1)["settlement"]
        self.assertIsNotNone(settlement)
        self.assertIn("gate_discharge", settlement["evidence"])


class TheComposedJobTraversesReviewAndAcceptance(ComposedOneJobCase):
    """W122060: one submitted Job, past the boundary the campaign stopped at.

    THE BLOCKER WAS THE ROUTE. A composed Job's review stage is another
    assignment of the SAME Work, one Work carries one route, and the
    implementation ending left it on the route the implementation worker is
    served on -- so the reviewer's claim was refused and the campaign's
    furthest transition was "implementation completed, wrong-route review
    claim" for its whole length.

    W125189's `route_fenced` is what moves it, and the ORDER is the correction:
    the committed route change happens while this ending's own fence still
    holds the runtime gate, and only then is the gate discharged. Discharging
    first returns the Work to `queued` on the route the FINISHED role is served
    on, which is the reclaim race the routing record measured.

    WHAT THIS CLASS PROVES is one Job going through the actual serving path:
    implementation, handoff, review by a real reviewer container, an accepted
    verdict, a second handoff, and an integration stage its integrator can
    claim. Where it stops, and why, is measured too.
    """

    REPORT = {"schema": "baton.review-report/1", "verdict": "accepted",
              "findings": "the composed line reads correctly"}

    def reviewed(self, verdict="accepted"):
        """One Job carried through its real review turn."""
        import copy

        held = self.implemented()
        self.drive(held.job, held.composed, "review", "waiting")
        attempt = self.only_attempt(held.composed, "review")
        report = copy.deepcopy(self.REPORT)
        report["verdict"] = verdict
        self.assertEqual(
            self.turn(held.control, "review", attempt,
                      self.mounted(held.composed, "review", attempt),
                      edits={"review-report.json": json.dumps(report)}), 0)
        held.review = attempt
        return held

    def projected(self):
        """This Job's one Work, as the Authority holds it now."""
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            return authority.project_work(self.work)
        finally:
            authority.dispose()

    # -- the boundary the campaign stopped at --------------------------------

    def test_the_implementation_handoff_moves_the_work_to_the_review_route(
            self):
        """THE ROUTE MOVED AND THE GATE DID NOT.

        Both halves matter: a handoff that also cleared the gate would let the
        implementation participant reclaim its own Work before the reviewer
        was offered anything.
        """
        self.implemented()
        work = self.projected()
        self.assertEqual(work["route"], self.config["review_route"])

    def test_the_reviewer_claims_and_its_container_starts(self):
        """The exact transition this campaign could not make."""
        held = self.implemented()
        states = self.drive(held.job, held.composed, "review", "waiting")
        self.assertEqual(states["review"], "waiting")
        attempt = self.only_attempt(held.composed, "review")
        self.assertNotEqual(attempt, held.attempt_id)
        # ITS OWN CONTAINER, not the implementation's. Two worker starts now,
        # and the custody helper runs are counted apart as they always were.
        self.assertEqual(
            len([one for one in self.engine.starts
                 if "--entrypoint" not in one]), 2)

    def test_the_reviewers_own_verdict_completes_the_review_stage(self):
        """The verdict is READ from the reviewer's frozen result.

        Nothing in this deployment decides it: the container writes a report,
        the manager measures and seals the output it wrote, and
        `end_review_from_result` reads the claim back out of that result.
        """
        held = self.reviewed()
        report = self.tick(held)
        [concluded] = [one for one in report["spoken"]
                       if one["stage_id"] == "job-a/review"]
        self.assertEqual(concluded["outcome"], "performed")
        self.assertEqual(concluded["detail"]["verdict"], "accepted")
        self.assertEqual(self.states(held.job, held.composed)["review"],
                         "completed")

    def test_the_accepted_review_hands_off_and_the_integrator_claims(self):
        """The second handoff, and the stage it makes eligible."""
        held = self.reviewed()
        states = self.drive(held.job, held.composed, "integration", "claimed")
        self.assertEqual(states["integration"], "claimed")
        self.assertEqual(self.projected()["route"],
                         self.INTEGRATION_ROUTE)

    def test_each_handoff_left_the_runtime_gate_exactly_as_it_found_it(self):
        """A handoff moves the route and nothing else.

        Measured at the Authority after each ending rather than asserted from
        this deployment's own answer.
        """
        self.implemented()
        after_implementation = self.projected()
        self.assertEqual(after_implementation["route"],
                         self.config["review_route"])
        self.assertIsNone(after_implementation["gate"])
        self.assertEqual(after_implementation["phase"], "queued")

    def test_a_changes_requested_review_routes_back_to_the_producer(self):
        """REVIEW 2026-09-09T05:33Z [1], driven.

        A correction is not forward. The Work goes back to the route the
        reviewed checkpoint's PRODUCER was claimed on, derived from that
        checkpoint's own writer -- not to the review worker's outgoing route,
        which sent the correction round's implementation claim at
        `integration` and refused it there.
        """
        held = self.reviewed(verdict="changes-requested")
        self.tick(held)
        from tests.job_manager import fixtures

        self.assertEqual(self.projected()["route"], fixtures.ROUTE)
        states = self.drive(held.job, held.composed, "implementation",
                            "waiting", ticks=12)
        self.assertEqual(states["implementation"], "waiting")

    def test_the_correction_round_claims_and_runs_a_second_time(self):
        """The same submitted Job and the same persistent line, round two."""
        held = self.reviewed(verdict="changes-requested")
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        second = self.only_attempt_of(held.composed, "implementation",
                                      exclude=held.attempt_id)
        self.assertNotEqual(second, held.attempt_id)
        self.assertEqual(
            len([one for one in self.engine.starts
                 if "--entrypoint" not in one]), 3)

    def only_attempt_of(self, composed, role, *, exclude):
        held = sorted(one for one in
                      self.worker_of(composed, role).stage._prepared
                      if one != exclude)
        self.assertEqual(len(held), 1, held)
        return held[0]

    # -- through the accepted integration runtime port -----------------------

    def integration_port(self, held):
        """The ACCEPTED port, composed from this fixture's own operands.

        REVIEW 2026-09-09T05:33Z [3], and my report that no provider existed
        was simply wrong: `tools/integration_worker.py` is W110774's accepted
        `IntegrationRuntimePort`, and every operand it names is one this
        deployment already resolves. Nothing is recreated here and nothing is
        stubbed; this is the wiring the fixture never had.

        IT IS COMPOSED AFTER ACCEPTANCE because two of its operands do not
        exist before it: the accepted checkpoint's line and the proposal that
        checkpoint's producer published. Both are read from their own owners --
        `integration_checkpoint` and `published_proposal` -- rather than
        remembered from the tick that produced them.
        """
        from baton_v12.worker_manager import review_cycles, source_boundary

        deployment = self.deployment_of(held)
        line = review_cycles.line_of(deployment.control,
                                     deployment.line()["line_id"])
        accepted = review_cycles.integration_checkpoint(deployment.control,
                                                        line["line_id"])
        self.assertIsNotNone(accepted)
        integrator = self.worker_of(held.composed, "integration")
        given = integrator.given
        for place in (deployment.integration_root,
                      os.path.join(self.root, "integration-bundles"),
                      os.path.join(self.root, "integration-launch")):
            os.makedirs(place, exist_ok=True)
        return integration_worker.IntegrationRuntimePort(
            coordinator=deployment.integration, manager=deployment.control,
            jobs=deployment.jobs, authority=deployment.authority,
            assignment_port=integrator.port,
            profile=deployment.integration_profile,
            checkpoint_profile=deployment.profile,
            object_runner=stage_execution._git_run,
            line_id=line["line_id"],
            proposal_id=deployment.published_proposal(accepted),
            canonical_target_id=deployment.given["canonical_target_id"],
            canonical_target=self.source,
            delivery_home=deployment.integration_root,
            instructions=b"the configured integration instructions\n",
            identity={one: given[one] for one in
                      ("image_digest", "profile_digest", "policy_digest",
                       "adapter_digest")},
            adapter_name=given["adapter_name"],
            toolchain_digest="sha256:" + "7" * 64,
            input_manifest=given["input_manifest"],
            engine=given["engine"], engine_run=self.engine,
            workspace_storage=self.storage,
            workspace_group=deployment.workspace_group,
            capacity=source_boundary.workspace_capacity(1 << 30),
            bundle_home=os.path.join(self.root, "integration-bundles"),
            launch_home=os.path.join(self.root, "integration-launch"),
            launch_session="integration-session",
            launch_contract=given["launch_contract"],
            network=given["network"],
            credential_resolution=given["credential_resolution"],
            credential_home=integrator.credential_home,
            credential_provider=lambda provider, reference: self.secret)

    @staticmethod
    def deployment_of(held):
        return held.composed.workers[0]["operations"]._worker.stage.deployment

    def test_the_accepted_integration_port_composes_from_this_deployment(self):
        """Every operand this port names is one this deployment resolves."""
        held = self.reviewed()
        self.drive(held.job, held.composed, "integration", "claimed")
        port = self.integration_port(held)
        for verb in ("prepare", "run", "refresh", "observed", "may_continue"):
            self.assertTrue(callable(getattr(port, verb, None)), verb)

    def test_the_integration_stage_advances_through_that_port(self):
        """THE WIRING THE FIXTURE NEVER HAD, driven on ordinary ticks.

        A second serving object is composed with the port and the same durable
        stores. That is not a restart trick: this manager is re-enterable by
        design, and the two operands the port needs -- the accepted line and
        its published proposal -- do not exist until the review has been
        accepted.
        """
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.reviewed()
        self.drive(held.job, held.composed, "integration", "claimed")
        port = self.integration_port(held)
        # THE FIRST OBJECT IS LEFT OPEN. Closing it disposes the Authority
        # handle the port above already holds, and this fixture's cleanup owns
        # both.
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base),
            held.job, held.control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            integration_port=port)
        self.addCleanup(composed.close)
        self._composed = composed
        held.composed = composed
        report = tick(held.job, composed, now=fixtures.NOW)
        started = [one for one in report["started"]
                   if one["stage_id"] == "job-a/integration"]
        self.assertTrue(started)
        # THE PORT WAS REACHED. Whatever it then answers is its own accepted
        # contract's business; what this pins is that the deployment no longer
        # refuses for want of one.
        for one in started:
            self.assertNotIn("no integration runtime port",
                             json.dumps(one.get("detail") or {}))

    # -- and exactly where it stops ------------------------------------------

    def test_the_integration_stage_is_held_for_want_of_a_runtime_port(self):
        """THE EXACT NEXT BLOCKER, and it is this build's own statement.

        `stage_execution` refuses here rather than stubbing: no accepted
        composition in this build starts an integrator over the integration
        delivery's namespaces, and the only implementations of that port are
        focused-test doubles. Supplying one here would be helper-only success
        dressed as a lifecycle, so the stage stays claimed and this records
        why.

        IT IS CONTAINED. The refusal is reported as itself and the other
        stages of this Job keep their finished state.
        """
        held = self.reviewed()
        self.drive(held.job, held.composed, "integration", "claimed")
        report = self.tick(held)
        [started] = [one for one in report["started"]
                     if one["stage_id"] == "job-a/integration"]
        self.assertEqual(started["outcome"], "deferred")
        self.assertEqual(started["detail"]["code"], "capability")
        self.assertIn("no integration runtime port",
                      started["detail"]["message"])
        states = self.states(held.job, held.composed)
        self.assertEqual(states["implementation"], "completed")
        self.assertEqual(states["review"], "completed")

    def tick(self, held):
        from baton_v12.job_manager import sweep
        from tests.job_manager import fixtures

        return sweep(held.job, held.composed, now=fixtures.NOW)


class OrdinaryTerminalLifecycle(ComposedOneJobCase):
    """W122060: coherent provisioning and one actual terminal lifecycle."""

    REPORT = TheComposedJobTraversesReviewAndAcceptance.REPORT
    reviewed = TheComposedJobTraversesReviewAndAcceptance.reviewed
    projected = TheComposedJobTraversesReviewAndAcceptance.projected
    only_attempt_of = TheComposedJobTraversesReviewAndAcceptance.only_attempt_of
    deployment_of = staticmethod(TheComposedJobTraversesReviewAndAcceptance.deployment_of)
    tick = TheComposedJobTraversesReviewAndAcceptance.tick
    INSTRUCTIONS = b"the configured integration instructions\n"

    def setUp(self):
        from baton_v12.authority import Authority

        super().setUp()
        # Provision the disposable target at its Git-reviewed ordinary mode,
        # independently of the test process umask, before starting any worker.
        os.chmod(os.path.join(self.source, "harness.py"), 0o644)
        authority = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
        try:
            # Pin once after bootstrap; subsequent policy drift still refuses.
            self.fixture_policy = authority.policy_generation()
        finally:
            authority.dispose()
        self.lifecycle_reports = []

    def composed_document(self, **members):
        from baton_v12.contracts import digest_of_bytes

        given = super().composed_document(**members)
        given["policy_generation"] = self.fixture_policy
        given["integration_profile"]["instructions_digest"] = digest_of_bytes(self.INSTRUCTIONS)
        return given

    def integration_port(self, held):
        from baton_v12.integration import TARGET_SCHEMA, activate_target

        deployment = self.deployment_of(held)
        activate_target(deployment.integration, {"schema": TARGET_SCHEMA,
                        "canonical_target_id": deployment.given["canonical_target_id"],
                        "description": "the disposable composed lifecycle target"})
        port = TheComposedJobTraversesReviewAndAcceptance.integration_port(self, held)
        port.object_runner = self.object_runner
        return port

    def object_runner(self, argv, *, directory):
        import subprocess

        answer = subprocess.run(list(argv), cwd=f"/proc/self/fd/{directory}", pass_fds=(directory,),
                                env=self.environment(), capture_output=True, timeout=10)
        return {"returncode": answer.returncode, "stdout": answer.stdout, "stderr": answer.stderr}

    def accepted_correction(self):
        held = self.reviewed("changes-requested")
        line_id = self.deployment_of(held).line()["line_id"]
        self.drive(held.job, held.composed, "implementation", "waiting", ticks=12)
        corrected = self.only_attempt_of(held.composed, "implementation", exclude=held.attempt_id)
        self.assertEqual(self.turn(held.control, "implementation", corrected,
                                  self.mounted(held.composed, "implementation", corrected),
                                  edits={"harness.py": "print('the accepted correction')\n"}), 0)
        self.drive(held.job, held.composed, "review", "waiting", ticks=12)
        reviewer = self.only_attempt_of(held.composed, "review", exclude=held.review)
        self.assertEqual(self.turn(held.control, "review", reviewer,
                                  self.mounted(held.composed, "review", reviewer),
                                  edits={"review-report.json": json.dumps(self.REPORT)}), 0)
        self.drive(held.job, held.composed, "integration", "claimed", ticks=12)
        self.assertEqual(self.deployment_of(held).line()["line_id"], line_id)
        held.corrected = corrected
        return held

    def connect_integration(self, held):
        port = self.integration_port(held)
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base), held.job, held.control,
            engine_run=self.engine, credential_provider=lambda *_: self.secret,
            clock=lambda: NOW, checkout=self.checkout, integration_port=port)
        self.addCleanup(composed.close)
        self._composed = composed
        held.composed = composed
        held.integration_port = port

    def integration_turn(self, held, attempt_id, *, behavior="import"):
        import subprocess
        import sys
        import claude_agent
        import integration_entry
        from baton_v12.integration import runtime
        from tests.manager.test_integration_worker import PROVIDER_SOURCE
        from unittest.mock import patch

        deployment = self.deployment_of(held)
        delivery = runtime.adopt_delivery(deployment.integration_root, attempt_id=attempt_id,
                                          workspace_group=deployment.workspace_group)
        script = os.path.join(self.root, "integration-provider.py")
        self.write(script, PROVIDER_SOURCE)

        def runner(argv, **options):
            return subprocess.run([sys.executable, "-I", "-B", script, behavior, argv[-1]],
                                  cwd=options.get("cwd"), env=dict(options.get("env") or {}),
                                  stdout=options.get("stdout"), stderr=options.get("stderr"), timeout=10)

        from baton_v12.worker_manager import launch

        launched = launch.adopt(os.path.join(self.root, "integration-launch"), attempt_id=attempt_id,
                               session="integration-session", contract=self.config["launch_contract"],
                               role=integration_worker.LAUNCH_ROLE)
        launch_place = launched.place
        scratch = os.path.join(self.root, "integration-scratch")
        os.mkdir(scratch, 0o700)
        agent_home = os.path.join(self.root, "integration-agent")
        os.mkdir(agent_home, 0o700)
        credentials = os.path.join(self.root, "integration-credentials")
        os.mkdir(credentials, 0o700)
        self.write(os.path.join(credentials, "claude"), "not-a-credential\n")
        with patch.object(claude_agent, "CREDENTIAL_ROOT", credentials):
            return integration_entry.main(
                agent=claude_agent.ClaudeAgent(run=runner, home=agent_home),
                launch_place=launch_place, assignment_root=delivery.assignment_root,
                result_root=delivery.result_root,
                bundle_root=os.path.join(self.root, "integration-bundles", attempt_id),
                target_root=self.source, scratch=scratch)

    def test_one_job_completes_correction_integration_and_terminal_handoff(self):
        from baton_v12.integration import entries_of, lease_of

        held = self.accepted_correction()
        self.connect_integration(held)
        report = self.tick(held)
        self.lifecycle_reports.append(report)
        [started] = [one for one in report["started"] if one["stage_id"] == "job-a/integration"]
        self.assertEqual(started["outcome"], "started", started)
        self.assertEqual(self.states(held.job, held.composed)["integration"], "integrating")
        attempt_id = started["attempt_id"]
        self.assertEqual(self.integration_turn(held, attempt_id), 0)
        from baton_v12.integration import runtime

        deployment = self.deployment_of(held)
        delivery = runtime.adopt_delivery(deployment.integration_root, attempt_id=attempt_id,
                                          workspace_group=deployment.workspace_group)
        observed = runtime.observed_delivery(delivery, runtime.published_assignment(delivery))
        self.assertEqual(observed["state"], "answered", observed)
        self.assertEqual(observed["result"]["outcome"], "integrated", observed)
        self.engine.stopped = True
        report = self.tick(held)
        self.lifecycle_reports.append(report)
        [ended] = [one for one in report["spoken"] if one["stage_id"] == "job-a/integration"]
        self.assertEqual(ended["outcome"], "performed", ended)
        self.assertEqual(ended["detail"]["outcome"], "integrated", ended)
        self.assertIsNotNone(ended["detail"]["authority_receipt"])
        deployment = self.deployment_of(held)
        [entry] = entries_of(deployment.integration, deployment.given["canonical_target_id"])
        self.assertEqual(entry["state"], "integrated")
        self.assertEqual(lease_of(deployment.integration, runtime.published_assignment(delivery)["lease_id"])["state"], "released")
        self.assertEqual(pathlib.Path(self.source, "harness.py").read_text(), "print('the accepted correction')\n")
        states = self.drive(held.job, held.composed, "integration", "completed", ticks=3)
        self.assertEqual(states, {"implementation": "completed", "review": "completed", "integration": "completed"})
        self.assertIsNone(self.projected()["handler"])
        from baton_v12.worker_manager import attempt_runtime_of

        fixed = attempt_runtime_of(held.control, attempt_id)["assignment"]
        outgoing = self.worker_of(held.composed, "integration").given["review_route"]
        handoff = deployment.authority.operation_result("integration-pass:" + attempt_id)
        self.assertEqual(handoff["assignment"], fixed)
        self.assertEqual(handoff["route"], outgoing)
        self.assertEqual(handoff["cause"], "pass")
        self.assertFalse(handoff["fenced"])
        self.assertIsNone(handoff["gate"])
        self.assertEqual(self.projected()["route"], outgoing)
        self.assertNotEqual(entry["assignment_generation"], fixed["generation"])
        self.terminal_evidence = {"states": states, "entry": entry,
            "lease": lease_of(deployment.integration, runtime.published_assignment(delivery)["lease_id"]),
            "integration_receipt": ended["detail"]["authority_receipt"], "handoff": handoff,
            "runtime": attempt_runtime_of(held.control, attempt_id), "work": self.projected()}

    def test_the_corrected_rounds_retained_bytes_reopen_at_their_locator(self):
        """W119114: the mandatory custody check, on the JOINED chain.

        `TheRetainedResultReopensAfterOrdinaryCleanup` proves this for the
        first implementation round. What integration actually consumes is the
        CORRECTION's result, and that round has its own attempt, its own
        ending and its own retained tree -- so the check is made again over
        the bytes that carry the accepted proposal, by the same rule: reopen
        at the RECORDED locator and measure against the digest the intake
        receipt carries, never a pathname and never a row read back.
        """
        from baton_v12.contracts import digest
        from baton_v12.worker_manager import intake_receipt_of

        held = self.accepted_correction()
        receipt = intake_receipt_of(held.control, held.corrected)
        [artifact] = receipt["artifacts"]
        locator = artifact["custody_locator"]
        self.assertTrue(locator.startswith("file://"), locator)
        place = locator[len("file://"):]
        entries = TheRetainedResultReopensAfterOrdinaryCleanup.measured(place)
        self.assertTrue(entries, place)
        self.assertEqual(digest(entries), artifact["content_digest"])
        # AND IT WAS NEVER INSIDE THE TREE THAT ROUND HAD WRITABLE, asked of
        # the real mount this attempt's container was started over.
        writable = os.path.realpath(self.mounted(
            held.composed, "implementation", held.corrected)["workspace"])
        self.assertFalse(
            os.path.realpath(place).startswith(writable + os.sep),
            f"{place} is inside the writable mount {writable}")
        self.custody = {"receipt": receipt, "artifact": artifact,
                        "entries": len(entries), "writable": writable}

    def test_the_accepted_checkpoint_is_the_corrections_and_its_pin_holds(
            self):
        """W119114: one line, two rounds, and the pin the integration reads.

        The eligibility the integration stage consumes must name the
        CORRECTION's checkpoint rather than the round the review sent back,
        and that checkpoint's pin must still revalidate through the accepted
        profile over the real repository after both endings have run.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.accepted_correction()
        deployment = self.deployment_of(held)
        line = deployment.line()
        accepted = review_cycles.integration_checkpoint(deployment.control,
                                                        line["line_id"])
        self.assertIsNotNone(accepted)
        checkpoint = review_cycles.checkpoint_of(deployment.control,
                                                 accepted["checkpoint_id"])
        writer = review_cycles.writer_of(deployment.control,
                                         checkpoint["writer_id"])
        self.assertEqual(writer["runtime_attempt_id"], held.corrected)
        self.assertNotEqual(writer["runtime_attempt_id"], held.attempt_id)
        # THE PIN IS REOPENED, not read: the profile revalidates it against
        # the line checkout that survived both rounds' endings.
        validated = deployment.profile.validate(line["line_path"],
                                                checkpoint["evidence"])
        self.assertEqual(validated, checkpoint["evidence"])
        self.assertEqual(validated["base"], self.base)
        self.assertGreater(line["revision"], 1)
        self.pins = {"line": line, "checkpoint": checkpoint, "writer": writer}

    # W119114 review 2026-09-09T17:41Z [P1]: the recovered Job, finished.
    # The four recovery helpers are bound at the foot of this module, because
    # the class that owns them is defined below this one and a class body
    # cannot name it yet.

    def recovered_correction(self):
        """The SAME held Job, recovered and then corrected for real.

        `accepted_correction` is the ordinary run's version of this and stays
        exactly as it is; this is the abandoned one, which reaches the same
        place through A, B, C and ordinary ticks. One fixture, not two.
        """
        held = self.started_correction(self.committed_handoff())
        line_id = self.deployment_of(held).line()["line_id"]
        self.declare_abandoned(held)
        self.recover(held)
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        corrected = sorted(
            one for one in self.worker_of(held.composed,
                                          "implementation").stage._prepared
            if one not in (held.attempt_id, held.abandoned))
        self.assertEqual(len(corrected), 1, corrected)
        held.corrected = corrected[0]
        # HELD NOW, because `connect_integration` composes a FRESH serving
        # object and the mounts this round was started over live on the one
        # that started it.
        held.corrected_roots = self.mounted(held.composed, "implementation",
                                            held.corrected)
        # THE FRESH WORKER REALLY RUNS, which is what the previous candidate
        # stopped short of and what the handoff wrongly claimed.
        self.assertEqual(
            self.turn(held.control, "implementation", held.corrected,
                      self.mounted(held.composed, "implementation",
                                   held.corrected),
                      edits={"harness.py": "print('the recovered correction')\n"}),
            0)
        self.drive(held.job, held.composed, "review", "waiting", ticks=12)
        reviewer = sorted(one for one in
                          self.worker_of(held.composed, "review").stage._prepared
                          if one != held.review)
        self.assertEqual(len(reviewer), 1, reviewer)
        self.assertEqual(
            self.turn(held.control, "review", reviewer[0],
                      self.mounted(held.composed, "review", reviewer[0]),
                      edits={"review-report.json": json.dumps(self.REPORT)}), 0)
        self.drive(held.job, held.composed, "integration", "claimed", ticks=12)
        # THE SAME DURABLE LINE THROUGHOUT.
        self.assertEqual(self.deployment_of(held).line()["line_id"], line_id)
        return held

    def test_the_recovered_job_finishes_and_its_manifest_reopens(self):
        """[P1] THE RECOVERED JOB, DRIVEN TO ITS TERMINAL HANDOFF, and then
        its corrected result reopened.

        My previous candidate stopped at `implementation waiting` and my
        handoff said an ordinary worker turn corrects it and the same Job
        finishes. The reviewer is right that neither was established. This is
        the same held Job -- abandoned, recovered through A/B/C, and then
        carried through its fresh correction, an independent accepted review,
        actual integration and the terminal handoff.
        """
        from baton_v12.contracts import digest
        from baton_v12.integration import entries_of, lease_of, runtime
        from baton_v12.worker_manager import (attempt_runtime_of,
                                              intake_receipt_of, line_of,
                                              checkpoint_of, load_manifest,
                                              frozen_output_of, review_cycles)

        held = self.recovered_correction()
        self.connect_integration(held)
        [started] = [one for one in self.tick(held)["started"]
                     if one["stage_id"] == "job-a/integration"]
        self.assertEqual(started["outcome"], "started", started)
        attempt_id = started["attempt_id"]
        self.assertEqual(self.integration_turn(held, attempt_id), 0)
        self.engine.stopped = True
        [ended] = [one for one in self.tick(held)["spoken"]
                   if one["stage_id"] == "job-a/integration"]
        self.assertEqual(ended["detail"]["outcome"], "integrated", ended)

        deployment = self.deployment_of(held)
        [entry] = entries_of(deployment.integration,
                             deployment.given["canonical_target_id"])
        self.assertEqual(entry["state"], "integrated")
        # THE INTEGRATED BYTES ARE THE RECOVERED CORRECTION'S.
        self.assertEqual(pathlib.Path(self.source, "harness.py").read_text(),
                         "print('the recovered correction')\n")
        states = self.drive(held.job, held.composed, "integration",
                            "completed", ticks=3)
        self.assertEqual(states, {"implementation": "completed",
                                  "review": "completed",
                                  "integration": "completed"})
        # AND THE TERMINAL HANDOFF IS THE AUTHORITY'S OWN RECORD.
        fixed = attempt_runtime_of(held.control, attempt_id)["assignment"]
        handoff = deployment.authority.operation_result(
            "integration-pass:" + attempt_id)
        self.assertEqual(handoff["assignment"], fixed)
        self.assertEqual(handoff["cause"], "pass")
        self.assertIsNone(self.projected()["handler"])

        # -- the corrected result, REOPENED at its own recorded locator ------
        receipt = intake_receipt_of(held.control, held.corrected)
        [artifact] = receipt["artifacts"]
        locator = artifact["custody_locator"]
        self.assertTrue(locator.startswith("file://"), locator)
        place = locator[len("file://"):]
        entries = TheRetainedResultReopensAfterOrdinaryCleanup.measured(place)
        self.assertTrue(entries, place)
        self.assertEqual(digest(entries), artifact["content_digest"])
        # THE RETAINED MANIFEST NAMES THOSE SAME BYTES.
        frozen = frozen_output_of(held.control, held.corrected)
        sealed = load_manifest(held.control, frozen["manifest_digest"],
                               "resultManifest")
        [produced] = [one for one in sealed["outputs"]
                      if one["status"] == "present"]
        self.assertEqual(produced["artifact"]["content_digest"],
                         artifact["content_digest"])
        self.assertEqual(produced["artifact"]["artifact_id"],
                         artifact["artifact_id"])
        # AND IT WAS NEVER INSIDE THE TREE THAT ROUND HAD WRITABLE.
        writable = os.path.realpath(held.corrected_roots["workspace"])
        self.assertFalse(os.path.realpath(place).startswith(writable + os.sep),
                         f"{place} is inside the writable mount {writable}")

        # -- the pins, and the candidate integration actually consumed -------
        line = line_of(held.control, deployment.line()["line_id"])
        accepted = review_cycles.integration_checkpoint(held.control,
                                                        line["line_id"])
        self.assertIsNotNone(accepted)
        checkpoint = checkpoint_of(held.control, accepted["checkpoint_id"])
        writer = review_cycles.writer_of(held.control, checkpoint["writer_id"])
        self.assertEqual(writer["runtime_attempt_id"], held.corrected)
        validated = deployment.profile.validate(line["line_path"],
                                                checkpoint["evidence"])
        self.assertEqual(validated, checkpoint["evidence"])
        self.assertEqual(validated["base"], self.base)
        # THE INTEGRATED CANDIDATE IS THE CORRECTED ROUND'S OWN PUBLICATION.
        #
        # MEASURED, not assumed: asking `published_proposal` here refuses,
        # because it re-derives the proposal against the Authority's CURRENT
        # canonical target and the integration has just advanced it -- "a
        # proposal is offered against the revision it was built from". So the
        # correlation is read from the two committed records instead, which is
        # the more direct claim anyway.
        published = stage_execution.publication_for_attempt(
            held.control, attempt_id=held.corrected)
        self.assertIsNotNone(published)
        self.assertEqual(entry["proposal_id"], published["proposal_id"])
        # THE ORIGINAL HANDOFF AND PUBLICATION SURVIVED THE WHOLE ARC.
        self.assertEqual(stage_execution.publication_for_attempt(
            held.control, attempt_id=held.attempt_id), held.publication)
        self.assertEqual(review_cycles.checkpoint_of(held.control,
                                                     held.checkpoint),
                         held.frozen)
        delivery = runtime.adopt_delivery(
            deployment.integration_root, attempt_id=attempt_id,
            workspace_group=deployment.workspace_group)
        self.assertEqual(lease_of(deployment.integration,
                                  runtime.published_assignment(
                                      delivery)["lease_id"])["state"],
                         "released")
        self.joined = {"states": states, "entry": entry, "handoff": handoff,
                       "receipt": receipt, "checkpoint": checkpoint,
                       "line": line, "published": published}

    def answered_integration(self, *, behavior="import"):
        held = self.accepted_correction()
        self.connect_integration(held)
        with mock.patch.object(held.composed.integrator, "observe", wraps=held.composed.integrator.observe) as observed:
            started = self.tick(held)
        [launched] = [one for one in started["started"] if one["stage_id"] == "job-a/integration"]
        held.integration_attempt = launched["attempt_id"]
        held.integration_stage = next(dict(call.args[0]) for call in reversed(observed.call_args_list)
                                      if call.args[0].get("kind") == "integration")
        self.assertEqual(self.integration_turn(held, held.integration_attempt, behavior=behavior), 0)
        return held

    def test_running_integrator_result_cannot_end_its_assignment(self):
        held = self.answered_integration()
        session = held.composed.sessions["integrator"]
        with mock.patch.object(session, "pass_work", wraps=session.pass_work) as passed:
            report = self.tick(held)
        self.assertFalse(passed.called)
        self.assertEqual(self.projected()["handler"], "baton.integrator")
        self.assertEqual(self.states(held.job, held.composed)["integration"], "answering")
        self.assertEqual(report["spoken"][0]["detail"]["outcome"], "running")

    def test_foreign_receipt_or_lease_cannot_authorize_terminal_handoff(self):
        held = self.answered_integration()
        self.engine.stopped = True
        with mock.patch.object(held.composed.integrator, "finish"):
            self.tick(held)
        authority = held.composed.authority
        receipt = authority.receipt
        def foreign(proposal, kind):
            return dict(receipt(proposal, kind), candidate_digest="foreign-candidate")
        with mock.patch.object(authority, "receipt", side_effect=foreign):
            with self.assertRaises(ContractRefusal) as refused:
                held.composed.integrator.finish(held.integration_stage)
        self.assertEqual(refused.exception.code, "operation-collision")
        lease_of = stage_execution.lease_of
        with mock.patch.object(stage_execution, "lease_of", side_effect=lambda *args: dict(lease_of(*args), fence=999)):
            with self.assertRaises(ContractRefusal) as refused:
                held.composed.integrator.finish(held.integration_stage)
        self.assertEqual(refused.exception.code, "operation-collision")
        self.assertIsNone(authority.operation_result("integration-pass:" + held.integration_attempt))
        self.assertEqual(self.projected()["handler"], "baton.integrator")

    def test_lost_pass_answer_remains_completed_after_a_later_assignment(self):
        from baton_v12.authority import Refusal

        held = self.answered_integration()
        self.engine.stopped = True
        session = held.composed.sessions["integrator"]
        original = session.pass_work
        def lost(operands):
            original(operands)
            raise Refusal("the probe loses the committed pass answer")
        with mock.patch.object(session, "pass_work", side_effect=lost) as passed:
            self.tick(held)
        self.assertEqual(passed.call_count, 1)
        authority = held.composed.authority
        operation = "integration-pass:" + held.integration_attempt
        committed = authority.operation_result(operation)
        later = authority.session("baton.reviewer").claim({"work_id": self.work, "operation_id": "later-review-claim"})
        with mock.patch.object(session, "pass_work", side_effect=AssertionError("a historical pass must not run again")), \
                mock.patch.object(held.composed.integrator, "_run", side_effect=AssertionError("integration must not run again")):
            self.assertEqual(self.states(held.job, held.composed)["integration"], "completed")
            self.tick(held)
        self.assertEqual(authority.operation_result(operation), committed)
        self.assertEqual(self.projected()["assignment"], later["assignment"])

    def test_uncertain_integration_effect_stays_held(self):
        from baton_v12.integration import entries_of, target_of

        held = self.answered_integration(behavior="index")
        self.engine.stopped = True
        self.tick(held)
        deployment = self.deployment_of(held)
        [entry] = entries_of(deployment.integration, deployment.given["canonical_target_id"])
        self.assertEqual(entry["state"], "held")
        self.assertEqual(target_of(deployment.integration, deployment.given["canonical_target_id"])["state"], "blocked")
        self.assertEqual(self.states(held.job, held.composed)["integration"], "exceptional")
        self.assertEqual(self.projected()["handler"], "baton.integrator")
        self.assertIsNone(deployment.authority.operation_result("integration-pass:" + held.integration_attempt))

    def test_serving_observation_reads_only_existing_owners(self):
        held = self.answered_integration()
        with mock.patch.object(held.composed.integrator, "_run", side_effect=AssertionError("read invoked driver")), \
                mock.patch.object(held.integration_port, "refresh", side_effect=AssertionError("read refreshed runtime")), \
                mock.patch.object(held.composed.sessions["integrator"], "pass_work", side_effect=AssertionError("read passed Work")), \
                mock.patch.object(stage_execution.review_cycles, "create_line", side_effect=AssertionError("read created line")), \
                mock.patch.object(stage_execution, "retain_proposal", side_effect=AssertionError("read retained proposal")):
            self.assertEqual(self.states(held.job, held.composed)["integration"], "answering")

    def test_committed_handoff_recovers_before_local_acknowledgement(self):
        from baton_v12.job_manager import ending, submit
        from baton_v12.worker_manager import review_cycles

        job, control, composed = self.serving()
        submit(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        attempt = self.only_attempt(composed, "implementation")
        self.assertEqual(self.turn(control, "implementation", attempt,
                                  self.mounted(composed, "implementation", attempt),
                                  edits={"harness.py": "print('retained handoff')\n"}), 0)
        held = SimpleNamespace(job=job, control=control, composed=composed)
        with mock.patch.object(stage_execution.ending, "settle_ending", side_effect=ContractRefusal("refused", "precondition", "lost local acknowledgement")):
            self.tick(held)
        record = ending.ending_of(job, "job-a/implementation", 1)
        self.assertIsNone(record["settlement"])
        authority = composed.authority
        operation = "route-fenced:" + attempt + ":" + self.config["review_route"]
        handoff = authority.operation_result(operation)
        self.assertIsNotNone(handoff)
        self.assertIsNone(authority.project_work(self.work)["gate"])
        writer = review_cycles.writer_for_attempt(control, attempt_id=attempt, generation=handoff["assignment"]["generation"])
        publication = stage_execution.publication_for_attempt(control, attempt_id=attempt)
        starts = len(self.engine.starts)
        composed.close()
        job.close()
        control.close()
        job, control = self.stores("after-committed-handoff")
        restarted = stage_execution.operations_from(self.composed_document(line_declared_base=self.base), job, control,
            engine_run=self.engine, credential_provider=lambda *_: self.secret, clock=lambda: NOW, checkout=self.checkout)
        self.addCleanup(restarted.close)
        self._composed = restarted
        resumed = SimpleNamespace(job=job, control=control, composed=restarted)
        self.tick(resumed)
        settled = ending.ending_of(job, "job-a/implementation", 1)
        self.assertIsNotNone(settled["settlement"])
        self.assertEqual(restarted.authority.operation_result(operation), handoff)
        self.assertEqual(review_cycles.writer_for_attempt(control, attempt_id=attempt, generation=handoff["assignment"]["generation"]), writer)
        self.assertEqual(stage_execution.publication_for_attempt(control, attempt_id=attempt), publication)
        self.assertEqual(len(self.engine.starts), starts)
        self.assertEqual(self.states(job, restarted)["implementation"], "completed")
        checkpoint = settled["settlement"]["evidence"]["checkpoint_id"]
        self.assertEqual(review_cycles.checkpoint_of(control, checkpoint)["writer_id"], writer["writer_id"])

    READONLY_PROCESS = r'''
import contextlib
import json
import sys
from unittest.mock import patch
from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import IntegrationStore
from baton_v12.job_manager import JobStore, status
from baton_v12.worker_manager import ControlStore
from tools import job_manager, stage_execution

spec = json.load(open(sys.argv[1]))
clock = lambda: "2026-09-02T00:00:00.000Z"
counts = {"authority_open": 0, "authority_dispose": 0, "coordinator_open": 0, "coordinator_close": 0}
open_authority, dispose = Authority.open_readonly, Authority.dispose
open_coordinator, close = IntegrationStore.open_readonly, IntegrationStore.close
def authority_open(*args, **kwargs):
    assert kwargs["expected_authority_uuid"] == spec["uuid"]
    result = open_authority(*args, **kwargs)
    counts["authority_open"] += 1
    return result
def coordinator_open(*args, **kwargs):
    result = open_coordinator(*args, **kwargs)
    counts["coordinator_open"] += 1
    return result
def disposed(owner):
    counts["authority_dispose"] += 1
    dispose(owner)
def closed(owner):
    counts["coordinator_close"] += 1
    close(owner)

with JobStore.open(spec["job"], authority_uuid=spec["uuid"], incarnation="readonly-child", clock=clock) as job, \
        ControlStore.open(spec["control"], incarnation="readonly-child", clock=clock) as control, contextlib.ExitStack() as guards:
    for owner, name in ((Authority, "open"), (Authority, "session"), (IntegrationStore, "open"),
            (stage_execution, "operations_from"), (stage_execution.Integration, "run"),
            (stage_execution.Integration, "finish"), (stage_execution.scheduler, "activate_pool"),
            (stage_execution.single_worker, "worker_preflight"), (stage_execution, "retain_proposal"),
            (stage_execution.review_cycles, "create_line")):
        guards.enter_context(patch.object(owner, name, side_effect=AssertionError("read reached " + name)))
    guards.enter_context(patch.object(stage_execution, "_checkout", return_value=spec["checkout"]))
    guards.enter_context(patch.object(Authority, "open_readonly", side_effect=authority_open))
    guards.enter_context(patch.object(IntegrationStore, "open_readonly", side_effect=coordinator_open))
    guards.enter_context(patch.object(Authority, "dispose", disposed))
    guards.enter_context(patch.object(IntegrationStore, "close", closed))
    reader = job_manager._observation_from("tools.stage_execution:observing_factory", job, control)
    observed = reader.observe_integration(spec["stage"])
    assert observed["state"] == "completed", observed
    completion = observed["completion"]
    assert observed["assignment"] == spec["fixed"]
    for member in ("proposal_id", "integration_receipt_id", "entry_id", "lease_id", "fence", "handoff_operation_id", "to_route", "runtime_id"):
        assert completion[member] == spec["completion"][member], (member, completion)
    projected = status(job, job_manager._Observing(control, reader), observed_at=clock())
    assert {row["kind"]: row["state"] for row in projected["jobs"][0]["stages"]} == {
        "implementation": "completed", "review": "completed", "integration": "completed"}
    actual = Authority.operation_result
    with patch.object(Authority, "operation_result", lambda self, op: None if op == completion["handoff_operation_id"] else actual(self, op)):
        assert reader.observe_integration(spec["stage"])["state"] == "answered"
    receipt = Authority.receipt
    with patch.object(Authority, "receipt", lambda self, *args: dict(receipt(self, *args), candidate_digest="foreign")):
        try:
            reader.observe_integration(spec["stage"])
        except ContractRefusal as refusal:
            assert refusal.code == "operation-collision"
        else:
            raise AssertionError("foreign receipt completed")
    for name, value in (("integration_store", spec["missing_coordinator"]), ("authority_store", spec["foreign_authority"])):
        document = json.load(open(spec["config"]))
        document[name] = value
        alternate = stage_execution.observation_from(document, job, control, checkout=spec["checkout"])
        try:
            alternate.observe_integration(spec["stage"])
        except ContractRefusal:
            pass
        else:
            raise AssertionError("missing/foreign evidence completed")
    assert counts["authority_open"] == counts["authority_dispose"], counts
    assert counts["coordinator_open"] == counts["coordinator_close"], counts
    print(json.dumps({"observation": observed, "status": projected, "handles": counts,
        "checks": ["configured UUID", "closed-serving completion", "missing handoff stays owed", "foreign receipt refuses",
                   "absent coordinator refuses", "foreign Authority refuses", "no serving acts", "all reader handles disposed"]}))
'''

    def test_fresh_process_observes_owned_completion_after_serving_closes(self):
        import subprocess
        import sys
        from baton_v12.authority import Authority

        made = []
        create = stage_execution.operations_from
        def tracked(*args, **kwargs):
            result = create(*args, **kwargs)
            made.append(result)
            return result
        with mock.patch.object(stage_execution, "operations_from", side_effect=tracked):
            held = self.answered_integration()
        self.engine.stopped = True
        self.tick(held)
        expected = held.composed.integrator.observe(held.integration_stage)
        self.assertEqual(expected["state"], "completed")
        foreign = os.path.join(self.root, "foreign-authority.db")
        Authority.create(foreign, authority_uuid="0000000b000000000000000000000000").dispose()
        configuration = os.path.join(self.root, "readonly-config.json")
        self.write(configuration, json.dumps(self.composed_document(line_declared_base=self.base)))
        spec = {"job": self.job_path, "control": self.control_path, "uuid": self.config["authority_uuid"],
                "checkout": self.checkout, "config": configuration, "stage": held.integration_stage,
                "fixed": expected["assignment"], "completion": expected["completion"],
                "foreign_authority": foreign, "missing_coordinator": os.path.join(self.root, "absent-coordinator.db")}
        for composed in reversed(made):
            composed.close()
        held.job.close()
        held.control.close()
        protected = (self.authority_path, self.integration_store, self.job_path, self.control_path)
        before = {path: (pathlib.Path(path).read_bytes(), os.stat(path).st_mode) for path in protected}
        script = os.path.join(self.root, "read-completed.py")
        self.write(script, self.READONLY_PROCESS)
        specification = os.path.join(self.root, "read-spec.json")
        self.write(specification, json.dumps(spec))
        result = subprocess.run([sys.executable, script, specification], cwd=REPOSITORY / "v12/python",
            env={**self.environment(), "PYTHONPATH": "src:.", stage_execution.CONFIG_ENV: configuration},
            capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path: (pathlib.Path(path).read_bytes(), os.stat(path).st_mode) for path in protected}, before)
        self.assertFalse(os.path.exists(spec["missing_coordinator"]))
        self.readonly_evidence = json.loads(result.stdout)


class UnfinishedWorkIsFencedBeforeAnythingRepeatsIt(ComposedOneJobCase):
    """W119114's remaining acceptance: safe abandonment of scratch work.

    `RESTART-ACCEPTANCE-2026-09-09.md` asks for one thing W122060's
    committed-handoff cut does not cover. That cut proves a manager can be
    reconstructed and finish a handoff it already committed. This asks the
    other half: a worker that is still THERE, holding a writable mount over
    the line, with unfinished scratch nobody committed -- stop and fence it,
    prove the exclusion, and then let a fresh assignment repeat the work from
    the last committed handoff and its retained checkpoint.

    THE ABANDONMENT IS AN OPERATOR ACT AND IS PERFORMED AS ONE. W44716's
    `abandon_attempt` says calling it IS the declaration, and
    `single_worker.conclude` says in as many words that deciding it is not
    this composition's. So nothing here asks the composition to abandon
    anything: the declaration is made against the deployment's OWN control
    store, port and adapter, which is the shape a Route policy or an operator
    would use, and every consequence is then read back off the ordinary ticks.
    """

    REPORT = TheComposedJobTraversesReviewAndAcceptance.REPORT
    reviewed = TheComposedJobTraversesReviewAndAcceptance.reviewed
    projected = TheComposedJobTraversesReviewAndAcceptance.projected
    only_attempt_of = TheComposedJobTraversesReviewAndAcceptance.only_attempt_of
    deployment_of = staticmethod(
        TheComposedJobTraversesReviewAndAcceptance.deployment_of)
    tick = TheComposedJobTraversesReviewAndAcceptance.tick
    REASON = "the correction worker stopped answering and is declared abandoned"

    def committed_handoff(self):
        """One Job driven to the last committed handoff before a correction.

        The reviewed checkpoint is retained, the Work is back on the producer's
        route, and the correction round is the thing about to repeat.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.reviewed(verdict="changes-requested")
        self.tick(held)
        deployment = self.deployment_of(held)
        line = deployment.line()
        held.line_id = line["line_id"]
        held.checkpoint = line["current_checkpoint_id"]
        self.assertIsNotNone(held.checkpoint)
        held.frozen = review_cycles.checkpoint_of(deployment.control,
                                                  held.checkpoint)
        self.assertEqual(held.frozen["state"], "frozen")
        held.route = self.projected()["route"]
        held.publication = stage_execution.publication_for_attempt(
            held.control, attempt_id=held.attempt_id)
        return held

    def started_correction(self, held):
        """The correction round, started and then left unfinished.

        `drive` runs ordinary ticks until the stage is waiting on its worker,
        which is exactly the state a worker that stopped answering leaves
        behind: the runtime is attached, the line writer is granted, and the
        mount is writable.
        """
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        held.abandoned = self.only_attempt_of(held.composed, "implementation",
                                              exclude=held.attempt_id)
        held.abandoned_roots = self.mounted(held.composed, "implementation",
                                            held.abandoned)
        # THE SCRATCH NOBODY COMMITTED. A real abandoned worker leaves bytes in
        # the tree it had writable; writing one here is what makes "unfinished
        # work may be lost" a measured claim rather than an empty one.
        self.write(os.path.join(held.abandoned_roots["workspace"],
                                "scratch-nobody-committed.py"),
                   "print('the abandoned round never finished this')\n")
        return held

    def declare_abandoned(self, held):
        """The operator's declaration, through the accepted public operation."""
        from baton_v12 import worker_manager
        from baton_v12.worker_manager import attempt_runtime_of

        worker = self.worker_of(held.composed, "implementation")
        state = attempt_runtime_of(held.control, held.abandoned)
        self.assertIsNotNone(state["runtime_id"])
        delivery, orphan = worker._credential(held.abandoned, state,
                                              held.abandoned_roots)
        adapter = worker._adapter(held.abandoned_roots, delivery, orphan, None)
        return worker_manager.abandon_attempt(
            held.control, worker.port, adapter, attempt_id=held.abandoned,
            reason=self.REASON,
            retention_policy_digest=self.deployment_of(
                held).retention_policy_digest)

    def recover(self, held, *, discharge=True, restore=True, replace=True):
        """The three accepted providers, in their own order, and nothing else.

        A: W128682's `discharge_abandoned_quiescence_gate` carries the
        abandonment's own positive-absence evidence to the gate its fence
        installed. B: W128692's `restore_abandoned_correction` puts the
        checkout back on the retained checkpoint and revokes the excluded
        writer. C: W128698's `restart_abandoned_correction` ends exactly the
        one live episode that could never finish.

        NOTHING HERE OPENS AN ASSIGNMENT. The successor is the ordinary sweep's,
        which is the whole point: this wiring reaches the accepted public
        operations and then gets out of the way.
        """
        from baton_v12.job_manager.episodes import restart_abandoned_correction
        from baton_v12.worker_manager import (
            discharge_abandoned_quiescence_gate)
        from baton_v12.worker_manager.review_cycles import (
            restore_abandoned_correction)

        deployment = self.deployment_of(held)
        worker = self.worker_of(held.composed, "implementation")
        generation = deployment.generation_of(held.abandoned)
        held.generation = generation
        policy = deployment.retention_policy_digest
        answered = {}
        if discharge:
            answered["discharge"] = discharge_abandoned_quiescence_gate(
                held.control, worker.port, attempt_id=held.abandoned,
                retention_policy_digest=policy)
        if restore:
            answered["restore"] = restore_abandoned_correction(
                held.control, attempt_id=held.abandoned,
                generation=generation, retention_policy_digest=policy,
                profile=deployment.profile)
        if replace:
            # ORDINARY TICKS FIRST, and this is C's own rule rather than a
            # convenience. `episodes._unheld` refuses while the abandoned
            # episode's allocation is still reserved: releasing a worker is
            # the SCHEDULER's act, not this recovery's, and opening a
            # successor over a live reservation would let one Job hold two
            # workers in one lane. So the sweep releases it and C proceeds --
            # measured, because my first cut called C immediately and was
            # refused exactly there.
            for _ in range(4):
                self.tick(held)
            answered["replace"] = restart_abandoned_correction(
                held.job, held.control, job_id="job-a",
                attempt_id=held.abandoned, generation=generation)
        held.recovery = answered
        return answered

    def test_the_declaration_fences_the_generation_and_destroys_the_runtime(
            self):
        """STOP AND FENCE, read back off the owners rather than the answer."""
        from baton_v12.worker_manager import (assignment_of,
                                              attempt_runtime_of)

        held = self.started_correction(self.committed_handoff())
        before = assignment_of(held.control, held.abandoned)
        answered = self.declare_abandoned(held)
        # POSITIVE ABSENCE, IN THE ENGINE'S OWN SENTENCE, and a cleanup that
        # settled at `retained` -- the ending deletes nothing.
        self.assertEqual(answered["cleanup"]["state"], "absent")
        self.assertEqual(answered["cleanup"]["cleanup"], "retained")
        runtime = attempt_runtime_of(held.control, held.abandoned)
        self.assertEqual(runtime["execution_runtime"], "destroyed")
        # THE IDENTITY IS REMEMBERED RATHER THAN CLEARED, and the engine was
        # really asked to remove that exact one -- which is what makes the
        # destruction attributable to this runtime rather than to a state
        # word.
        self.assertIn(runtime["runtime_id"], self.engine.gone)
        # THE FENCE IS THE AUTHORITY'S OWN RECORD, replayed through the
        # operation the declaration itself named, at the exact generation the
        # abandoned attempt held -- not a generation this fixture chose.
        fenced = self.deployment_of(held).authority.operation_result(
            answered["intent"]["authority_operation_id"])
        self.assertEqual(fenced, answered["fenced"])
        self.assertTrue(fenced["fenced"])
        self.assertEqual(fenced["assignment"]["generation"],
                         before["generation"])
        # AND THE WORK IS HELD BEHIND THIS ATTEMPT'S OWN QUIESCENCE GATE, so
        # the exclusion is the Authority's rather than this deployment's
        # promise: nothing can claim the Work at the fenced generation.
        self.assertEqual(fenced["phase"], "block")
        self.assertEqual(fenced["gate"],
                         "runtime-quiescence:%d" % before["generation"])
        self.assertEqual(self.projected()["gate"]["token"], fenced["gate"])
        self.assertEqual(answered["intent"]["reason"], self.REASON)
        self.assertEqual(answered["intent"]["decision"], "abandoned")
        self.abandonment = {"answer": answered, "runtime": runtime,
                            "fence": fenced}

    def test_the_committed_effects_the_declaration_crossed_are_all_intact(
            self):
        """REPEATED COMPUTATION IS PERMITTED; COMMITTED EFFECT IS NOT REDONE.

        The reviewed checkpoint, the route the handoff committed and the
        proposal the implementation round published are all effects that
        committed BEFORE this attempt existed. An abandonment that disturbed
        any of them would be losing committed work rather than scratch.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.started_correction(self.committed_handoff())
        self.declare_abandoned(held)
        deployment = self.deployment_of(held)
        self.assertEqual(review_cycles.checkpoint_of(deployment.control,
                                                     held.checkpoint),
                         held.frozen)
        self.assertEqual(self.projected()["route"], held.route)
        self.assertEqual(stage_execution.publication_for_attempt(
            held.control, attempt_id=held.attempt_id), held.publication)

    def test_the_abandoned_scratch_reaches_no_proposal(self):
        """WHAT THE ABANDONED WORKER WROTE IS LEFT UNTRUSTED AND UNUSED.

        M33800's rule for all four endings, read at this composition: the
        declaration freezes nothing and collects nothing, so the bytes that
        worker left behind never become a candidate.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.started_correction(self.committed_handoff())
        published = stage_execution.publication_for_attempt(
            held.control, attempt_id=held.abandoned)
        self.assertIsNone(published)
        self.declare_abandoned(held)
        self.assertIsNone(stage_execution.publication_for_attempt(
            held.control, attempt_id=held.abandoned))
        line = review_cycles.line_of(self.deployment_of(held).control,
                                     held.line_id)
        self.assertEqual(line["current_checkpoint_id"], held.checkpoint)

    def test_the_recovered_correction_reaches_a_fresh_assignment(self):
        """THE TRANSITION `review-2026-09-09T14-55-17Z.md` MEASURED AS
        IMPOSSIBLE, now driven.

        This case used to assert the blocked outcome and name the three owners
        a correction had to reach. All three are accepted now -- W128682's
        abandoned-family gate discharge, W128692's checkpoint restoration and
        writer exclusion, W128698's exactly-one replacement episode -- and this
        is the same fixture crossing the same boundary through them.

        WHAT IS WIRED AND WHAT IS NOT. The three public operations are called
        in their own order and nothing else is: no store edit, no hidden reset,
        no synthetic verdict and no engine-state guess. The successor
        assignment is the ORDINARY sweep's, and the correction round that
        follows is an ordinary worker turn.
        """
        from baton_v12.job_manager import episodes, projection
        from baton_v12.worker_manager import review_cycles

        held = self.started_correction(self.committed_handoff())
        deployment = self.deployment_of(held)
        generation = deployment.generation_of(held.abandoned)
        self.declare_abandoned(held)

        # THE STATE THAT USED TO BE THE END OF THE ROAD, measured before the
        # recovery rather than asserted about it.
        for _ in range(2):
            self.tick(held)
        stage_id = "job-a/implementation"
        self.assertEqual(self.states(held.job, held.composed)["implementation"],
                         "exceptional")
        self.assertIsNone(episodes.live_of(held.job, stage_id)["ended_state"])
        self.assertEqual(self.projected()["gate"]["token"],
                         "runtime-quiescence:%d" % generation)

        answered = self.recover(held)

        # A: THE GATE IS ACTUALLY DISCHARGED, read from the Authority.
        self.assertEqual(answered["discharge"]["gate"],
                         "runtime-quiescence:%d" % generation)
        self.assertIsNone(self.projected()["gate"])
        # B: THE LINE IS BACK AT ITS RETAINED CHECKPOINT WITH THE WRITER OUT.
        self.assertEqual(answered["restore"]["checkpoint_id"], held.checkpoint)
        line = review_cycles.line_of(deployment.control, held.line_id)
        self.assertEqual(line["state"], "correction-ready")
        self.assertEqual(line["current_checkpoint_id"], held.checkpoint)
        self.assertEqual(review_cycles.writer_for_attempt(
            deployment.control, attempt_id=held.abandoned,
            generation=generation)["state"], "revoked")
        # C: EXACTLY THAT EPISODE ENDED, and it is now replaceable.
        self.assertEqual(answered["replace"]["ended_state"],
                         "abandoned-after-exclusion")
        self.assertIsNone(episodes.live_of(held.job, stage_id))
        self.assertTrue(projection.replaceable(
            projection.stage_states(held.job, held.composed)[stage_id]))

        # AND THE ORDINARY TICKS DO THE REST. Nothing below reaches a provider.
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        fresh = sorted(one for one in
                       self.worker_of(held.composed,
                                      "implementation").stage._prepared
                       if one not in (held.attempt_id, held.abandoned))
        self.assertEqual(len(fresh), 1, fresh)
        held.fresh = fresh[0]
        self.recovered = {"discharge": answered["discharge"],
                          "restore": answered["restore"],
                          "replace": answered["replace"], "fresh": held.fresh,
                          "line": line}

    def test_the_fresh_assignment_writes_only_after_the_exclusion(self):
        """NO NEW WRITER BEFORE THE EXCLUSION, in the order the acceptance
        states it: every earlier step is refused, and only the completed
        recovery admits one."""
        from baton_v12.worker_manager import review_cycles

        held = self.started_correction(self.committed_handoff())
        deployment = self.deployment_of(held)
        self.declare_abandoned(held)
        # Before any recovery: the line is still held by the abandoned writer.
        self.assertEqual(review_cycles.line_of(deployment.control,
                                               held.line_id)["state"],
                         "writing")
        # After A alone: still held -- a discharged gate is not an exclusion.
        self.recover(held, restore=False, replace=False)
        self.assertEqual(review_cycles.line_of(deployment.control,
                                               held.line_id)["state"],
                         "writing")
        # After B: excluded and ready, and only then does C end the episode.
        self.recover(held, discharge=False, replace=False)
        self.assertEqual(review_cycles.line_of(deployment.control,
                                               held.line_id)["state"],
                         "correction-ready")
        self.recover(held, discharge=False, restore=False)
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        fresh = sorted(one for one in
                       self.worker_of(held.composed,
                                      "implementation").stage._prepared
                       if one not in (held.attempt_id, held.abandoned))
        self.assertEqual(len(fresh), 1, fresh)

    def test_the_discarded_scratch_is_gone_and_the_checkpoint_bytes_are_back(
            self):
        """THE UNCOMMITTED WORK IS LOST AND THE RETAINED CHECKPOINT IS NOT.

        The abandoned round's scratch was written into the tree it had
        writable; after the restore that tree is the checkpoint's own, proved
        through the accepted profile rather than by reading a row.
        """
        from baton_v12.worker_manager import review_cycles

        held = self.started_correction(self.committed_handoff())
        deployment = self.deployment_of(held)
        checkout = held.abandoned_roots["workspace"]
        self.assertTrue(os.path.exists(
            os.path.join(checkout, "scratch-nobody-committed.py")))
        self.declare_abandoned(held)
        self.recover(held)

        self.assertFalse(os.path.exists(
            os.path.join(checkout, "scratch-nobody-committed.py")))
        checkpoint = review_cycles.checkpoint_of(deployment.control,
                                                 held.checkpoint)
        self.assertEqual(checkpoint, held.frozen)
        # THE PIN IS REOPENED rather than read: the profile revalidates the
        # restored checkout against the retained checkpoint.
        validated = deployment.profile.validate(
            review_cycles.line_of(deployment.control,
                                  held.line_id)["line_path"],
            checkpoint["evidence"], current=True)
        self.assertEqual(validated, checkpoint["evidence"])

    def test_the_recovery_replays_and_committed_effects_are_unchanged(self):
        """REPEATED COMPUTATION IS PERMITTED; COMMITTED EFFECT IS NOT REDONE.

        Every one of the three operations answers its committed result a
        second time, no second episode is opened, and the reviewed checkpoint,
        the route and the first round's publication are byte-identical
        afterwards.
        """
        from baton_v12.job_manager import episodes

        held = self.started_correction(self.committed_handoff())
        self.declare_abandoned(held)
        first = self.recover(held)
        self.drive(held.job, held.composed, "implementation", "waiting",
                   ticks=12)
        successor = episodes.live_of(held.job, "job-a/implementation")

        again = self.recover(held)
        self.assertEqual(again, first)
        self.assertEqual(episodes.live_of(held.job, "job-a/implementation"),
                         successor)
        self.assertEqual(self.projected()["route"], held.route)
        self.assertEqual(stage_execution.publication_for_attempt(
            held.control, attempt_id=held.attempt_id), held.publication)

    def test_an_unrecovered_declaration_still_reaches_no_assignment(self):
        """THE NEGATIVE THAT WAS THIS CASE'S WHOLE POINT, kept: without the
        recovery the stage still stops, so the positive proof above is the
        recovery's doing and not the fixture's."""
        from baton_v12.job_manager import episodes, projection

        held = self.started_correction(self.committed_handoff())
        self.declare_abandoned(held)
        for _ in range(4):
            self.tick(held)
        stage_id = "job-a/implementation"
        self.assertEqual(self.states(held.job, held.composed),
                         {"implementation": "exceptional", "review": "blocked",
                          "integration": "blocked"})
        self.assertIsNone(episodes.live_of(held.job, stage_id)["ended_state"])
        self.assertFalse(projection.replaceable(
            projection.stage_states(held.job, held.composed)[stage_id]))
        self.assertEqual(
            sorted(self.worker_of(held.composed,
                                  "implementation").stage._prepared),
            sorted([held.attempt_id, held.abandoned]))

    def test_a_running_or_foreign_selection_recovers_nothing(self):
        """The accepted owners' own refusals, reached through this fixture."""
        from baton_v12.job_manager.episodes import restart_abandoned_correction
        from baton_v12.worker_manager.review_cycles import (
            restore_abandoned_correction)

        held = self.started_correction(self.committed_handoff())
        deployment = self.deployment_of(held)
        generation = deployment.generation_of(held.abandoned)
        policy = deployment.retention_policy_digest
        # STILL RUNNING: nothing has been declared, so there is nothing to
        # restore and nothing to replace.
        with self.assertRaises(ContractRefusal):
            restore_abandoned_correction(
                held.control, attempt_id=held.abandoned,
                generation=generation, retention_policy_digest=policy,
                profile=deployment.profile)
        with self.assertRaises(ContractRefusal):
            restart_abandoned_correction(held.job, held.control,
                                         job_id="job-a",
                                         attempt_id=held.abandoned,
                                         generation=generation)
        self.declare_abandoned(held)
        self.recover(held, restore=False, replace=False)
        # A FOREIGN GENERATION selects an abandonment this deployment never
        # committed.
        with self.assertRaises(ContractRefusal):
            restore_abandoned_correction(
                held.control, attempt_id=held.abandoned,
                generation=generation + 5, retention_policy_digest=policy,
                profile=deployment.profile)
        self.recover(held, discharge=False)
        with self.assertRaises(ContractRefusal):
            restart_abandoned_correction(held.job, held.control,
                                         job_id="job-a",
                                         attempt_id=held.attempt_id,
                                         generation=1)

class TheWrongRouteClaimDefersInsteadOfStoppingTheSweep(ComposedOneJobCase):
    """W125032's accepted negative, RESTORED with its precondition made
    deliberate.

    Review 2026-09-09T05:33Z [4]: retiring this was not mine to do, and the
    PLAN preserves it explicitly. What changed underneath it is that W122060's
    handoff now moves the Work to the review route, so the wrong-route claim no
    longer happens by accident -- exactly as W124782's fix stopped the
    deferred-cleanup window happening by accident. The precondition is
    therefore withheld on purpose and the expected behaviour is unchanged.

    THE BEHAVIOUR IT PINS. A concrete Authority `Refusal` is not a
    `ContractRefusal`, so the scheduler's per-stage handler did not contain it
    and one refused claim left the tick entirely. The deployment's manager
    session maps it into this manager's closed vocabulary, so the stage defers,
    stays owed, and the tick finishes.
    """

    def wrong_route(self):
        """One Job whose implementation ending did not hand its Work on.

        THE HANDOFF IS WITHHELD, not broken: `_handed_off` is the act that
        moves the Work to the review route, and without it the Work stays on
        the route the implementation worker is served on -- which is the state
        this negative is about.
        """
        with mock.patch.object(stage_execution.StageComposition,
                               "_handed_off", lambda *arguments: None):
            return self.implemented()

    def test_the_wrong_route_claim_defers_and_the_sweep_finishes(self):
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.wrong_route()
        reports = [tick(held.job, held.composed, now=fixtures.NOW)
                   for _ in range(4)]
        # THE SWEEP RETURNED EVERY TIME, which is the whole correction. Before
        # it, the first refused claim left the tick entirely.
        self.assertEqual(len(reports), 4)
        claims = [one for report in reports for one in report["acts"]
                  if one.get("act") == "claim"]
        self.assertTrue(claims)
        self.assertEqual({one["outcome"] for one in claims}, {"deferred"})
        for claim in claims:
            self.assertEqual(claim["detail"]["category"], "refused")
            self.assertEqual(claim["detail"]["code"], "precondition")
            self.assertIn("does not resolve to", claim["detail"]["message"])
            self.assertIn("baton.reviewer", claim["detail"]["message"])

    def test_no_claim_receipt_and_no_review_runtime_follow_it(self):
        """A contained refusal is not a quiet success."""
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.wrong_route()
        starts = len([one for one in self.engine.starts
                      if "--entrypoint" not in one])
        for _ in range(4):
            tick(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(self.states(held.job, held.composed)["review"],
                         "offered")
        self.assertEqual(len([one for one in self.engine.starts
                              if "--entrypoint" not in one]), starts)
        self.assertEqual(held.control._connection.execute(
            "SELECT count(*) FROM attempts WHERE assignment_generation "
            "IS NOT NULL AND runtime_attempt_id != ?",
            (held.attempt_id,)).fetchone()[0], 0)


class OneRefusedClaimLeavesEveryOtherJobAlone(ComposedOneJobCase):
    """W125032's accepted class, RESTORED with the same deliberate
    precondition.

    Review [4]. Its subject is the composed deployment's own limits and the
    containment measured against them, and both still hold; only the way its
    wrong-route state is reached has changed, for the reason the class above
    gives.

    JOB B IS OWED AND DOES NOT PROGRESS HERE, and this class says so plainly.
    The joined proof -- one Job claiming successfully in the same sweep as the
    other's concrete refusal -- is `TwoIndependentlyBoundWorkersShareOneSweep`,
    which composes its own two workers because this deployment cannot carry
    them; the three owner refusals that stop it are measured below.
    """

    wrong_route = TheWrongRouteClaimDefersInsteadOfStoppingTheSweep.wrong_route

    def carried(self):
        """Job A at its wrong-route review claim, with Job B owed beside it."""
        from baton_v12.job_manager import submit as submit_jobs
        from tests.job_manager import fixtures

        held = self.wrong_route()
        [first] = self.submission["jobs"]
        submit_jobs(held.job, fixtures.submission(
            submission_id="sub-2",
            jobs=[fixtures.job("job-b",
                               input_digest=first["input_digest"],
                               policy_digest=first["policy_digest"],
                               stages=[fixtures.stage("implementation",
                                                      self.work)])]))
        return held

    def test_the_other_jobs_act_is_still_reached_in_the_same_tick(self):
        """THE HARM THE ESCAPE ACTUALLY DID, and its repair."""
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.carried()
        for _ in range(4):
            report = tick(held.job, held.composed, now=fixtures.NOW)
            spoken = {one["stage_id"]: one for one in report["acts"]}
            self.assertIn("job-a/review", spoken)
            self.assertIn("job-b/implementation", spoken)
            claim = spoken["job-a/review"]
            if claim["act"] == "claim":
                self.assertEqual(claim["outcome"], "deferred")
                self.assertEqual(claim["detail"]["code"], "precondition")
                self.assertIn("does not resolve to",
                              claim["detail"]["message"])

    def test_without_the_containment_the_other_job_is_never_reached(self):
        """The counterfactual, driven rather than described."""
        from baton_v12.authority import Refusal
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.carried()
        tick(held.job, held.composed, now=fixtures.NOW)
        direct = single_worker._AuthoritySession.claim
        with mock.patch.object(single_worker._ManagerClaimSession, "claim",
                               direct):
            with self.assertRaises(Refusal) as caught:
                tick(held.job, held.composed, now=fixtures.NOW)
        self.assertIn("does not resolve to", str(caught.exception))
        report = tick(held.job, held.composed, now=fixtures.NOW)
        self.assertIn("job-b/implementation",
                      {one["stage_id"] for one in report["acts"]})

    def test_correcting_the_route_lets_the_same_claim_succeed(self):
        """THE FIXED CLAIM IDENTITY, not a second one."""
        from baton_v12.authority import Authority
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.carried()
        for _ in range(3):
            tick(held.job, held.composed, now=fixtures.NOW)
        offered = self.offers(held, "job-a/review")
        self.assertEqual(len(offered), 1)
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.add_route_handler(fixtures.ROUTE, "baton.reviewer")
        finally:
            authority.dispose()
        performed = []
        for _ in range(3):
            performed.extend(
                one for one in tick(held.job, held.composed,
                                    now=fixtures.NOW)["acts"]
                if one["stage_id"] == "job-a/review"
                and one.get("act") == "claim"
                and one["outcome"] == "performed")
        self.assertTrue(performed)
        self.assertEqual(self.offers(held, "job-a/review"), offered)

    def test_why_the_joined_proof_is_composed_outside_this_deployment(self):
        """The three owner refusals that stop this deployment carrying a
        second progressing Job, measured rather than asserted."""
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.carried()
        report = tick(held.job, held.composed, now=fixtures.NOW)
        [admit] = [one for one in report["acts"]
                   if one["stage_id"] == "job-b/implementation"]
        self.assertEqual((admit["act"], admit["outcome"]),
                         ("admit", "deferred"))
        self.assertIn("already has a live offer", admit["detail"]["message"])
        self.assertEqual(self.job_states(held, "job-b")["implementation"],
                         "queued")

    def test_a_second_worker_for_one_role_is_refused_by_the_document(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.serving(workers=[
                self.worker("implementation"),
                dict(self.worker("implementation"),
                     worker_id="second-implementation-worker"),
                self.worker("review", participant="baton.reviewer",
                            principal=self.principals["baton.reviewer"],
                            review_route=self.INTEGRATION_ROUTE),
                self.worker("integration", participant="baton.integrator",
                            principal=self.principals["baton.integrator"])])
        self.assertIn("each stage is served by exactly one",
                      str(caught.exception))

    def test_the_two_jobs_are_served_by_the_two_configured_participants(self):
        held = self.carried()
        roles = {one["role"]: one["operations"]._worker.port.participant
                 for one in held.composed.workers}
        self.assertEqual(roles["implementation"], "baton.claude")
        self.assertEqual(roles["review"], "baton.reviewer")
        self.assertNotEqual(roles["implementation"], roles["review"])

    @staticmethod
    def job_states(held, job_id):
        from baton_v12.job_manager import status as projected_status
        from tests.job_manager import fixtures

        projected = projected_status(held.job, held.composed,
                                     observed_at=fixtures.NOW)
        [job] = [one for one in projected["jobs"] if one["job_id"] == job_id]
        return {one["kind"]: one["state"] for one in job["stages"]}

    @staticmethod
    def offers(held, stage_id):
        return sorted(row[0] for row in held.job._connection.execute(
            "SELECT offer_id FROM episodes WHERE stage_id = ?", (stage_id,)))


class TwoIndependentlyBoundWorkersShareOneSweep(SingleWorkerCase):
    """W125032: one concrete claim refuses; the other Job gets its turn.

    THIS IS WHAT THE CONTAINMENT IS FOR. `sweep` walks every Job in one tick,
    and `authority.errors.Refusal` is not a `ContractRefusal` -- so before this
    Work the first refused claim ended the tick and took every other Job's owed
    act with it. Proving that needs two Jobs that can both really act, which
    the composed one-Job deployment cannot give: it configures one worker per
    role, binds each worker to one Work and one bootstrap input, and one Work
    carries one live offer.

    SO THE TWO WORKERS ARE COMPOSED FROM THE PUBLIC CONSTRUCTORS, as review
    2026-09-09T05-01-39Z directs: `worker_preflight` and `worker_operations`
    build each one over its own Work, participant, session and input manifest,
    `activate_pool` declares both, and `PooledManagerOperations` serves them.
    That is the same public path `stage_execution` itself takes once per
    configured worker; nothing here copies its private composition, relaxes its
    one-worker-per-role rule or touches that file.

    THE REFUSAL IS THE REAL ONE. Work B is routed to `rview`, which no
    participant handles, so the Authority refuses its claim exactly as it
    refuses the composed Job's wrong-route review claim. Work C is routed to
    the second participant and its claim performs.
    """

    SECOND = "baton.second"
    SECOND_NAME = "second-reference"
    SECOND_PROFILE = "sha256:" + "5a" * 32
    REFUSING = "aa-refusing-worker"
    PROGRESSING = "bb-progressing-worker"
    REFUSING_JOB = "job-a-refusing"
    PROGRESSING_JOB = "job-b-progressing"

    def works(self):
        """Two Works: one nobody can claim, one the second participant can."""
        from baton_v12.authority import Authority
        from tests.job_manager import fixtures

        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.create_work(fixtures.WORK_B, "rview",
                                  contract="v12-assignment-1",
                                  operation_id="create-refusing-work")
            authority.create_work(fixtures.WORK_C, fixtures.ROUTE,
                                  contract="v12-assignment-1",
                                  operation_id="create-progressing-work")
            authority.add_route_handler(fixtures.ROUTE, self.SECOND)
            return authority.principal_of(self.SECOND)
        finally:
            authority.dispose()

    def configured(self, *, work_id, participant, principal, profile_name,
                   profile_digest, home):
        """One worker's whole deployment document, bound to its own Work.

        The manifest is this fixture's own with its Work reference and runtime
        profile replaced and its digest recomputed, because a manifest digest
        is over the document it describes. The two workers keep separate launch
        and credential homes for the same reason two deployments would.
        """
        import copy

        from baton_v12.contracts import digest

        manifest = copy.deepcopy(self.manifest)
        manifest["work_ref"] = dict(manifest["work_ref"], work_id=work_id)
        manifest["runtime_profile_digest"] = profile_digest
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        return dict(self.config, input_manifest=manifest,
                    participant=participant, principal=principal,
                    profile_name=profile_name, profile_digest=profile_digest,
                    launch_home=os.path.join(self.root, "launch-" + home),
                    credential_home=os.path.join(self.root,
                                                 "credentials-" + home))

    def serving_pair(self):
        """Both workers, one pool, one manager surface, two submitted Jobs."""
        from baton_v12.authority import Authority
        from baton_v12.job_manager import scheduler, submit
        from baton_v12.job_manager.scheduler import PooledManagerOperations
        from tests.job_manager import fixtures
        from .test_single_worker import Engine

        principal = self.works()
        given = {
            self.REFUSING: self.configured(
                work_id=fixtures.WORK_B, participant=fixtures.WHO,
                principal=self.principal, profile_name="reference",
                profile_digest=fixtures.PROFILE, home="refusing"),
            self.PROGRESSING: self.configured(
                work_id=fixtures.WORK_C, participant=self.SECOND,
                principal=principal, profile_name=self.SECOND_NAME,
                profile_digest=self.SECOND_PROFILE, home="progressing")}
        job, control = self.stores("two-bound-workers")
        engine = Engine()
        operations = {}
        for worker_id, document in given.items():
            # `_held` IS WHAT `stage_execution` READS EACH WORKER'S DEPLOYMENT
            # WITH, and this composes workers the same way rather than a second
            # way. Both public constructors take the document in that form.
            held = single_worker._held(document)
            opened = Authority.open(
                self.authority_path,
                expected_authority_uuid=document["authority_uuid"])
            self.addCleanup(opened.dispose)
            provider = single_worker.worker_preflight(
                held, control, credential_provider=lambda *_: self.secret,
                engine_run=engine)
            operations[worker_id] = single_worker.worker_operations(
                held, control, opened, provider, engine_run=engine,
                clock=lambda: fixtures.NOW, dispose=lambda: None)
        resolved = {fixtures.WHO: self.principal, self.SECOND: principal}
        generation = scheduler.activate_pool(job, {
            "schema": scheduler.POOL_SCHEMA,
            "variant": "two-bound-workers",
            "separation_class": "provider-diverse",
            "workers": [
                {"worker_id": self.REFUSING, "lane": "implementation",
                 "participant": fixtures.WHO, "profile_name": "reference",
                 "profile_digest": fixtures.PROFILE,
                 "eligible_kinds": ["implementation"]},
                {"worker_id": self.PROGRESSING, "lane": "implementation",
                 "participant": self.SECOND,
                 "profile_name": self.SECOND_NAME,
                 "profile_digest": self.SECOND_PROFILE,
                 "eligible_kinds": ["implementation"]}]},
            resolved)["generation"]
        pooled = PooledManagerOperations(
            job, {(generation, worker_id): held
                  for worker_id, held in operations.items()},
            resolved_principals=resolved)
        submit(job, fixtures.submission(jobs=[
            self.one_job(self.REFUSING_JOB, given[self.REFUSING],
                         fixtures.WORK_B, "reference", fixtures.PROFILE),
            self.one_job(self.PROGRESSING_JOB, given[self.PROGRESSING],
                         fixtures.WORK_C, self.SECOND_NAME,
                         self.SECOND_PROFILE)]))
        return SimpleNamespace(job=job, control=control, pooled=pooled,
                               engine=engine)

    @staticmethod
    def one_job(job_id, given, work_id, profile_name, profile_digest):
        from tests.job_manager import fixtures

        return fixtures.job(
            job_id, input_digest=given["input_manifest"]["manifest_digest"],
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[fixtures.stage(work_id=work_id,
                                   profile_name=profile_name,
                                   profile_digest=profile_digest)])

    def ticks(self, held, count=4):
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        return [tick(held.job, held.pooled, now=fixtures.NOW)
                for _ in range(count)]

    @staticmethod
    def claims(reports):
        return [one for report in reports for one in report["acts"]
                if one.get("act") == "claim"]

    def states(self, held):
        from baton_v12.job_manager import status
        from tests.job_manager import fixtures

        projected = status(held.job, held.pooled, observed_at=fixtures.NOW)
        return {one["job_id"]: one["stages"][0]["state"]
                for one in projected["jobs"]}

    # -- the proof -----------------------------------------------------------

    def test_one_claim_refuses_while_the_other_performs_in_one_sweep(self):
        """BOTH IN ONE TICK, which is the whole statement."""
        held = self.serving_pair()
        together = []
        for report in self.ticks(held):
            spoken = {one["stage_id"]: one for one in report["acts"]
                      if one.get("act") == "claim"}
            if len(spoken) == 2:
                together.append(spoken)
        self.assertTrue(together, "no tick carried both Jobs' claims")
        for spoken in together:
            refused = spoken[self.REFUSING_JOB + "/implementation"]
            performed = spoken[self.PROGRESSING_JOB + "/implementation"]
            self.assertEqual(refused["outcome"], "deferred")
            self.assertEqual(refused["detail"]["category"], "refused")
            self.assertEqual(refused["detail"]["code"], "precondition")
            self.assertIn("does not resolve to", refused["detail"]["message"])
            self.assertEqual(performed["outcome"], "performed")

    def test_the_other_job_advances_past_the_one_that_refuses(self):
        """Performing an act is not the same as getting somewhere."""
        held = self.serving_pair()
        self.ticks(held, 6)
        states = self.states(held)
        self.assertEqual(states[self.REFUSING_JOB], "offered")
        self.assertNotIn(states[self.PROGRESSING_JOB],
                         ("blocked", "queued", "offered"))

    def test_the_refused_claim_records_no_success_and_releases_nothing(self):
        """A contained refusal is not a quiet success, and not a retirement.

        The stage keeps the offer it was refused on, its allocation stays
        reserved rather than released, and no claim is recorded for it.

        `claimed_offers_for` IS KEYED BY THE ATTEMPT, and review
        2026-09-09T05-09-21Z caught this call passing a participant instead:
        the reader then answered an empty list whatever the target attempt's
        claim state was, so the assertion held for the wrong reason and would
        have gone on holding if a claim had been recorded. The positive case
        below is what stops that from being invisible again -- an absence
        reader nobody has seen say "present" is not evidence of absence.
        """
        from baton_v12.job_manager.scheduler import allocation_of
        from baton_v12.worker_manager import claimed_offers_for

        held = self.serving_pair()
        self.ticks(held)
        refused = self.attempt_of(held, self.REFUSING_JOB)
        allocation = allocation_of(held.job, refused)
        self.assertEqual(allocation["allocation_state"], "reserved")
        self.assertEqual(claimed_offers_for(held.control, refused), [])

    def test_the_same_reader_sees_the_claim_the_other_job_did_record(self):
        """THE POSITIVE CONTROL for the reader the case above trusts.

        Same store, same tick sequence, same call -- and the attempt whose
        claim performed answers one claimed offer naming it. That is what
        makes the empty answer above a fact about the refused attempt rather
        than about the query.
        """
        from baton_v12.worker_manager import claimed_offers_for

        held = self.serving_pair()
        self.ticks(held)
        progressed = self.attempt_of(held, self.PROGRESSING_JOB)
        [claimed] = claimed_offers_for(held.control, progressed)
        self.assertEqual(claimed["runtime_attempt_id"], progressed)
        self.assertEqual(claimed["state"], "claimed")
        self.assertEqual(
            claimed_offers_for(held.control,
                               self.attempt_of(held, self.REFUSING_JOB)), [])

    @staticmethod
    def attempt_of(held, job_id):
        [attempt] = [row["attempt_id"] for row in held.job._connection.execute(
            "SELECT attempt_id FROM episodes WHERE stage_id = ?",
            (job_id + "/implementation",))]
        return attempt

    def test_correcting_the_route_lets_the_same_offer_claim(self):
        """THE FIXED CLAIM IDENTITY, not a second one.

        `add_route_handler` is an authorized Authority bootstrap action taken
        by this fixture, not a production routing remedy -- that is W124786's.
        What it establishes here is that the deferral left the claim intact:
        the very offer that was refused is the one that succeeds.
        """
        from baton_v12.authority import Authority
        from tests.job_manager import fixtures

        held = self.serving_pair()
        self.ticks(held)
        stage_id = self.REFUSING_JOB + "/implementation"
        before = self.offers(held, stage_id)
        self.assertEqual(len(before), 1)
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.add_route_handler("rview", fixtures.WHO)
        finally:
            authority.dispose()
        performed = [one for one in self.claims(self.ticks(held))
                     if one["stage_id"] == stage_id
                     and one["outcome"] == "performed"]
        self.assertTrue(performed)
        self.assertEqual(self.offers(held, stage_id), before)

    def test_without_the_containment_the_other_job_is_never_reached(self):
        """The counterfactual, driven rather than described.

        Forwarding the claim directly is what this deployment did before. The
        refusing Job sorts first, so the concrete `Refusal` leaves the sweep
        before the other Job's claim is reached at all -- and the contained
        run reaches it in the very next tick.
        """
        from baton_v12.authority import Refusal
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.serving_pair()
        tick(held.job, held.pooled, now=fixtures.NOW)
        direct = single_worker._AuthoritySession.claim
        with mock.patch.object(single_worker._ManagerClaimSession, "claim",
                               direct):
            with self.assertRaises(Refusal) as caught:
                tick(held.job, held.pooled, now=fixtures.NOW)
        self.assertIn("does not resolve to", str(caught.exception))
        report = tick(held.job, held.pooled, now=fixtures.NOW)
        self.assertIn(self.PROGRESSING_JOB + "/implementation",
                      {one["stage_id"] for one in report["acts"]})

    @staticmethod
    def offers(held, stage_id):
        return sorted(row[0] for row in held.job._connection.execute(
            "SELECT offer_id FROM episodes WHERE stage_id = ?", (stage_id,)))


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


# W119114 review 2026-09-09T17:41Z [P1]: ONE FIXTURE, BOUND LATE.
#
# `OrdinaryTerminalLifecycle` owns the terminal machinery and
# `UnfinishedWorkIsFencedBeforeAnythingRepeatsIt` owns the abandonment and its
# recovery, and the second is defined after the first. Binding here rather than
# duplicating either keeps the recovered Job on the SAME fixture the ordinary
# one uses, which is what the review asks for.
for _borrowed in ("committed_handoff", "started_correction",
                  "declare_abandoned", "recover", "REASON"):
    setattr(OrdinaryTerminalLifecycle, _borrowed,
            getattr(UnfinishedWorkIsFencedBeforeAnythingRepeatsIt, _borrowed))
del _borrowed


class TheMultiWorkerPoolComposesWithoutASecondAllocator(ServingCase):
    """W119403: several workers for one role, through the existing pool.

    THE LIMITATION THIS ANSWERS. `_held_workers` refused a repeated role, so a
    deployment could never offer two implementation workers and additional
    submitted Jobs could not be served at once. That is a composition limit
    rather than a defect in the accepted scheduler -- which already takes one
    pool entry per configured worker -- so what is added is a CONFIGURATION
    VARIANT and not a second allocator.

    THE ONE-JOB DOCUMENT IS UNTOUCHED. `/1` still refuses two workers for one
    role and every refusal control above it still passes; a deployment asks for
    the wider pool by naming `/2`.

    WHAT THIS CUT DOES NOT CLAIM. Per-Job source, task, line, checkpoint and
    target binding is the next cut's, and the questions that need one producer
    refuse here with a sentence saying so rather than choosing the first
    worker. Pool acceptance alone is not multi-Job execution.
    """

    SECOND_PRODUCER = "baton.second"
    SECOND_REVIEWER = "baton.reviewer-2"

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            # THE AUTHORITY'S OWN MAPPING, read rather than chosen: an endpoint
            # nobody has bound resolves to this Authority's default principal,
            # and a deployment that named a different one is refused by
            # `_resolved` for exactly that reason.
            self.principals.update(
                {who: authority.principal_of(who)
                 for who in (self.SECOND_PRODUCER, self.SECOND_REVIEWER)})
        finally:
            authority.dispose()

    def multi(self, **members):
        """The `/2` document: two producers, two reviewers, one integrator.

        The extra workers are DERIVED from the ones the accepted composed
        document already builds, so each keeps its role's own operands -- the
        review worker's outgoing route, the integration worker's bearer slot --
        rather than this case inventing a second idea of a valid worker.
        """
        given = self.composed_document()
        held = {one["role"]: one for one in given["workers"]}
        producer = copy.deepcopy(held["implementation"])
        producer["worker_id"] = "implementation-worker-2"
        producer["deployment"]["participant"] = self.SECOND_PRODUCER
        producer["deployment"]["principal"] = \
            self.principals[self.SECOND_PRODUCER]
        reviewer = copy.deepcopy(held["review"])
        reviewer["worker_id"] = "review-worker-2"
        reviewer["deployment"]["participant"] = self.SECOND_REVIEWER
        reviewer["deployment"]["principal"] = \
            self.principals[self.SECOND_REVIEWER]
        workers = [held["implementation"], producer, held["review"], reviewer,
                   held["integration"]]
        answer = {"schema": stage_execution.MULTI_CONFIG_SCHEMA,
                  "workers": workers,
                  # W119405: `/2` now binds each Job to its own source, base,
                  # Work and target, so a document that named none could not
                  # serve one. The pool cases keep asserting the POOL; this is
                  # the smallest binding that lets them.
                  "job_bindings": [self.binding("job-a")]}
        answer.update(members)
        return answer

    def binding(self, job_id, **members):
        """One Job's own binding, defaulted from this fixture's own values."""
        held = {"job_id": job_id, "job_work_id": self.work,
                "review_work_id": self.work,
                "line_declared_base": "a" * 40,
                "canonical_target_id": "target-1",
                "source_worker_id": "implementation-worker"}
        held.update(members)
        return held

    def multi_held(self, **members):
        return stage_execution.held_configuration(
            self.document(**self.multi(**members)), checkout=self.checkout)

    def multi_refused(self, **members):
        with self.assertRaises(ContractRefusal) as caught:
            self.multi_held(**members)
        return caught.exception

    def serving_multi(self, **members):
        return self.serving(**self.multi(**members))

    def deployment_of(self, composed):
        return composed.workers[0]["operations"]._worker.stage.deployment

    # -- configuration --------------------------------------------------------

    def test_the_variant_admits_several_workers_for_one_role(self):
        held = self.multi_held()
        self.assertEqual(held["schema"], stage_execution.MULTI_CONFIG_SCHEMA)
        self.assertEqual(
            [(one["worker_id"], one["role"]) for one in held["workers"]],
            [("implementation-worker", "implementation"),
             ("implementation-worker-2", "implementation"),
             ("review-worker", "review"),
             ("review-worker-2", "review"),
             ("integration-worker", "integration")])

    def test_the_one_job_document_still_refuses_a_repeated_role(self):
        """The closed variant is closed, said beside the one that opens it."""
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.held_configuration(
                self.document(**dict(self.multi(),
                                     schema=stage_execution.CONFIG_SCHEMA)),
                checkout=self.checkout)
        self.assertIn("exactly one", caught.exception.message)

    def test_a_repeated_worker_identity_is_refused(self):
        """The rule `/1` got for free from its roles: the pool tells its
        workers apart by identity, so it cannot hold one twice."""
        workers = self.multi()["workers"]
        workers[1] = dict(workers[1], worker_id="implementation-worker")
        self.assertIn("cannot hold it twice",
                      self.multi_refused(workers=workers).message)

    def test_a_participant_serving_both_sides_of_a_review_is_refused(self):
        """Independence is the whole reason a review exists, and the wider
        pool is not bought with it."""
        workers = copy.deepcopy(self.multi()["workers"])
        workers[3]["deployment"]["participant"] = self.SECOND_PRODUCER
        held = self.multi_refused(workers=workers)
        self.assertEqual((held.category, held.code), ("policy", "denied"))
        workers = copy.deepcopy(self.multi()["workers"])
        workers[3]["deployment"]["principal"] = \
            self.principals[self.SECOND_PRODUCER]
        self.assertEqual(self.multi_refused(workers=workers).category,
                         "policy")

    def test_another_authority_and_a_role_mismatch_still_refuse(self):
        workers = copy.deepcopy(self.multi()["workers"])
        workers[1]["deployment"]["authority_uuid"] = "0" * 32
        self.assertEqual(self.multi_refused(workers=workers).code, "capability")
        workers = copy.deepcopy(self.multi()["workers"])
        workers[1]["deployment"]["launch_role"] = "review"
        self.assertIn("configured for it",
                      self.multi_refused(workers=workers).message)

    def test_every_role_is_still_served(self):
        workers = [one for one in self.multi()["workers"]
                   if one["role"] != "integration"]
        self.assertIn("integration",
                      self.multi_refused(workers=workers).message)

    # -- activation and reconstruction ----------------------------------------

    def test_every_configured_worker_reaches_the_pool_with_its_own_lane(self):
        """The scheduler's own rule, quoted rather than restated: a review kind
        is the review lane and everything else the implementation lane, and a
        worker is eligible for exactly the kind it was configured for."""
        from baton_v12.job_manager import scheduler

        job, _control, composed = self.serving_multi()
        self.assertEqual(scheduler.active_generation(job)["generation"], 1)
        pooled = {one["worker_id"]: one for one in scheduler.pool_workers(job)}
        self.assertEqual(sorted(pooled),
                         ["implementation-worker", "implementation-worker-2",
                          "integration-worker", "review-worker",
                          "review-worker-2"])
        self.assertEqual(pooled["implementation-worker-2"]["lane"],
                         "implementation")
        self.assertEqual(pooled["review-worker-2"]["lane"], "review")
        self.assertEqual(pooled["implementation-worker-2"]["participant"],
                         self.SECOND_PRODUCER)
        self.assertEqual(sorted(composed.pooled.workers),
                         [(1, "implementation-worker"),
                          (1, "implementation-worker-2"),
                          (1, "integration-worker"), (1, "review-worker"),
                          (1, "review-worker-2")])

    def test_the_eligible_kinds_are_the_roles_each_worker_was_configured_for(
            self):
        from baton_v12.job_manager import scheduler

        job, _control, _composed = self.serving_multi()
        # THE STORE ANSWERS ITS OWN COLUMN, which is the encoded list rather
        # than a Python one; decoding it here is reading what was written.
        self.assertEqual(
            {one["worker_id"]: sorted(json.loads(one["eligible_kinds"])
                                      if isinstance(one["eligible_kinds"], str)
                                      else one["eligible_kinds"])
             for one in scheduler.pool_workers(job)},
            {"implementation-worker": ["implementation"],
             "implementation-worker-2": ["implementation"],
             "review-worker": ["review"], "review-worker-2": ["review"],
             "integration-worker": ["integration"]})

    def test_every_pooled_worker_carries_its_configured_profile(self):
        from baton_v12.job_manager import scheduler

        job, _control, _composed = self.serving_multi()
        for one in scheduler.pool_workers(job):
            self.assertEqual(one["profile_name"], self.config["profile_name"])
            self.assertEqual(one["profile_digest"],
                             self.config["profile_digest"])

    def test_reconstruction_reattaches_the_same_pool(self):
        """A second composition over the same stores is a RECONSTRUCTION, not
        a new generation: `activate_pool` replays and the workers are the ones
        already configured."""
        from baton_v12.job_manager import scheduler
        from tests.job_manager import fixtures

        from .test_single_worker import Engine

        job, control, composed = self.serving_multi()
        before = sorted(one["worker_id"]
                        for one in scheduler.pool_workers(job))
        again = stage_execution.operations_from(
            self.composed_document(**self.multi()), job, control,
            engine_run=Engine(),
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(again.close)
        self.assertEqual(scheduler.active_generation(job)["generation"], 1)
        self.assertEqual(sorted(one["worker_id"]
                                for one in scheduler.pool_workers(job)), before)
        self.assertEqual(sorted(again.pooled.workers),
                         sorted(composed.pooled.workers))

    # -- the seam the next cut selects on -------------------------------------

    def test_the_role_seam_answers_every_worker_and_never_a_singleton(self):
        _job, _control, composed = self.serving_multi()
        deployment = self.deployment_of(composed)
        self.assertEqual(
            [one["worker_id"]
             for one in deployment.workers_for("implementation")],
            ["implementation-worker", "implementation-worker-2"])
        self.assertEqual(
            [one["worker_id"] for one in deployment.workers_for("review")],
            ["review-worker", "review-worker-2"])
        self.assertEqual(deployment.sole_worker("integration")["worker_id"],
                         "integration-worker")

    def test_selecting_among_producers_is_still_not_a_pool_question(self):
        """W119405 CONVERTS THE SECOND HALF OF THIS CASE, and keeps the first.

        When the pool cut wrote it, `line()` reached one global Work and source
        and refused here -- correctly, because choosing the first configured
        producer would have been that cut inventing a binding it did not own.
        The per-Job binding cut owns it now and answers it, so asserting the
        refusal would be asserting the absence of a capability that has since
        landed.

        WHAT DOES NOT MOVE is the half this class is actually about: asking a
        POOL which of several producers is "the" one is still a question with
        no answer, and `sole_worker` still refuses it.
        """
        _job, _control, composed = self.serving_multi()
        deployment = self.deployment_of(composed)
        with self.assertRaises(ContractRefusal) as caught:
            deployment.sole_worker("implementation")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("per-Job binding cut", caught.exception.message)
        # AND THE LINE IS NOW REACHED THROUGH THE JOB THAT OWNS IT. This
        # class's source is not a version-controlled tree -- it proves the
        # POOL -- so what is asserted here is the binding the line is derived
        # from; materializing one is the per-Job class's own proof.
        self.assertEqual(deployment.works_for("job-a"), (self.work, self.work))
        self.assertEqual(deployment.target_for("job-a"), "target-1")
        self.assertEqual(deployment.binding_for("job-a")["source_worker_id"],
                         "implementation-worker")
        with self.assertRaises(ContractRefusal):
            deployment.binding_for("job-nobody-bound")

    def test_each_producer_gets_its_own_publisher_session(self):
        """`Authority.publish` takes the PRODUCER's live assignment, and a
        session refuses to act on an assignment naming somebody else -- so a
        pool with two producers needs two publisher sessions."""
        _job, _control, composed = self.serving_multi()
        deployment = self.deployment_of(composed)
        self.assertEqual(sorted(deployment.publishers),
                         sorted([self.config["participant"],
                                 self.SECOND_PRODUCER]))
        self.assertEqual(
            sorted(one for one in composed.sessions
                   if one.startswith("publisher")),
            sorted(["publisher:" + self.config["participant"],
                    "publisher:" + self.SECOND_PRODUCER]))


# W119405: the second Job's Work, named here so the binding cases read as one
# fact rather than as a fixtures import three classes away.
SECOND_WORK = "0000000a-W2"


class EachJobBindsItsOwnDeploymentAndLine(ComposedOneJobCase):
    """W119405: two Jobs, two lines, and no global fallback anywhere.

    THE LIMITATION THIS ANSWERS. `StageDeployment.line` reached one source, one
    declared base and one Work, and `_prepare` reached that line from an
    attempt alone -- so a second submitted Job could only ever share the first
    one's checkout. The pool cut made the deployment able to hold several
    workers; this one makes each JOB hold its own source, base, Works, line and
    integration target.

    THE FIXTURE IS THE COMPOSED ONE, so the sources are real
    version-controlled trees and the lines are materialized by the accepted
    checkpoint profile rather than described. Two Jobs get two sources, and
    what is asserted is that the accepted line provider answers two different
    lines for them.

    WHAT IS SELECTED AND HOW. A Job's binding is selected by its own `job_id`
    and its source by a configured worker's IDENTITY; the worker serving a
    stage is selected by the scheduler's own recorded allocation. Nothing here
    selects by list order, which is the one thing this cut may not do.
    """

    SECOND_PRODUCER = "baton.second"
    SECOND_REVIEWER = "baton.reviewer-2"

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority

        # A SECOND REAL SOURCE, because a second Job's line is materialized
        # from its own tree and a fixture that shared one would be proving the
        # opposite of this cut.
        self.second_source = os.path.join(self.root, "source-b")
        os.makedirs(self.second_source)
        self.vcs_at(self.second_source, "init", "-q", "-b", "main")
        self.write(os.path.join(self.second_source, "harness.py"),
                   "print('the second job')\n")
        self.vcs_at(self.second_source, "add", "--all")
        self.vcs_at(self.second_source, "commit", "-q", "--message", "base")
        self.second_base = self.vcs_at(self.second_source, "rev-parse",
                                       "HEAD").strip()
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            # UPDATED, NOT REPLACED: `composed_document` needs the reviewer
            # and integrator principals this fixture already read.
            self.principals.update(
                {who: authority.principal_of(who)
                 for who in (self.SECOND_PRODUCER, self.SECOND_REVIEWER)})
        finally:
            authority.dispose()

    def vcs_at(self, place, *arguments):
        import subprocess

        argv = ["git", "-C", place] + list(arguments)
        answer = subprocess.run(
            argv, capture_output=True, text=True, timeout=300,
            env=dict(self.environment(), GIT_AUTHOR_NAME="Baton Test",
                     GIT_AUTHOR_EMAIL="test@baton.invalid",
                     GIT_COMMITTER_NAME="Baton Test",
                     GIT_COMMITTER_EMAIL="test@baton.invalid"))
        self.assertEqual(answer.returncode, 0, f"{argv}: {answer.stderr}")
        return answer.stdout

    def two_jobs(self, **members):
        """One `/2` document binding two Jobs to two sources and two Works."""
        given = self.composed_document(line_declared_base=self.base)
        held = {one["role"]: one for one in given["workers"]}
        producer = copy.deepcopy(held["implementation"])
        producer["worker_id"] = "implementation-worker-b"
        producer["deployment"]["participant"] = self.SECOND_PRODUCER
        producer["deployment"]["principal"] = \
            self.principals[self.SECOND_PRODUCER]
        # ITS OWN SOURCE, named as the RAW member the worker document carries;
        # `single_worker._held` is what turns it into the held nomination this
        # deployment binds a Job's line to.
        producer["deployment"]["nominated_source"] = self.second_source
        workers = [held["implementation"], producer, held["review"],
                   held["integration"]]
        answer = {
            "schema": stage_execution.MULTI_CONFIG_SCHEMA,
            "workers": workers,
            "job_bindings": [
                {"job_id": "job-a", "job_work_id": self.work,
                 "review_work_id": self.work,
                 "line_declared_base": self.base,
                 "canonical_target_id": "target-a",
                 "source_worker_id": "implementation-worker"},
                {"job_id": "job-b", "job_work_id": SECOND_WORK,
                 "review_work_id": SECOND_WORK,
                 "line_declared_base": self.second_base,
                 "canonical_target_id": "target-b",
                 "source_worker_id": "implementation-worker-b"}]}
        answer.update(members)
        return answer

    def held_two(self, **members):
        return stage_execution.held_configuration(
            self.composed_document(**self.two_jobs(**members)),
            checkout=self.checkout)

    def refused_two(self, **members):
        with self.assertRaises(ContractRefusal) as caught:
            self.held_two(**members)
        return caught.exception

    def serving_two(self, **members):
        return self.serving(**self.two_jobs(**members))

    def deployment_of(self, composed):
        return composed.workers[0]["operations"]._worker.stage.deployment

    # -- the binding, held before anything durable ----------------------------

    def test_each_job_binds_its_own_source_base_works_and_target(self):
        held = self.held_two()
        bound = {one["job_id"]: one for one in held["job_bindings"]}
        self.assertEqual(sorted(bound), ["job-a", "job-b"])
        self.assertEqual(bound["job-a"]["canonical_target_id"], "target-a")
        self.assertEqual(bound["job-b"]["canonical_target_id"], "target-b")
        self.assertEqual(bound["job-b"]["job_work_id"], SECOND_WORK)
        self.assertNotEqual(bound["job-a"]["line_declared_base"],
                            bound["job-b"]["line_declared_base"])
        self.assertEqual(bound["job-b"]["source_worker_id"],
                         "implementation-worker-b")

    def test_two_bindings_for_one_job_are_refused(self):
        bindings = self.two_jobs()["job_bindings"]
        held = self.refused_two(job_bindings=bindings + [bindings[0]])
        self.assertIn("binds one source", held.message)

    def test_a_source_worker_this_deployment_does_not_configure_is_refused(
            self):
        bindings = copy.deepcopy(self.two_jobs()["job_bindings"])
        bindings[1]["source_worker_id"] = "implementation-worker-nobody"
        held = self.refused_two(job_bindings=bindings)
        self.assertEqual((held.category, held.code),
                         ("refused", "precondition"))
        self.assertIn("does not configure", held.message)

    def test_a_review_work_that_differs_from_the_implementation_is_refused(
            self):
        """One development line carries one Work, and `attach_review` binds the
        reviewer to the writer's own -- so those stages could never attach."""
        bindings = copy.deepcopy(self.two_jobs()["job_bindings"])
        bindings[1]["review_work_id"] = self.work
        held = self.refused_two(job_bindings=bindings)
        self.assertIn("could never be attached", held.message)

    def test_the_one_job_document_carries_no_bindings(self):
        """Two places for one fact is how they drift: `/1` says these things
        once, globally, and is refused for saying them twice."""
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.held_configuration(
                self.composed_document(
                    line_declared_base=self.base,
                    job_bindings=self.two_jobs()["job_bindings"]),
                checkout=self.checkout)
        self.assertIn("names no job_bindings", caught.exception.message)

    def test_the_one_job_document_still_derives_its_own_binding(self):
        """`/1` is not asked for a new member; its binding is derived from what
        it already says, so every existing assertion about those members
        stands."""
        held = stage_execution.held_configuration(
            self.composed_document(line_declared_base=self.base),
            checkout=self.checkout)
        [binding] = held["job_bindings"]
        self.assertIsNone(binding["job_id"])
        self.assertEqual(binding["job_work_id"], self.work)
        self.assertEqual(binding["line_declared_base"], self.base)
        self.assertEqual(binding["canonical_target_id"],
                         held["canonical_target_id"])

    # -- two Jobs, two real lines ---------------------------------------------

    def test_two_jobs_materialize_two_distinct_persistent_lines(self):
        """THE LIMITATION, GONE. `create_line` derives its identity from
        `(authority, work)`, so two bound Works give two checkouts -- and each
        is materialized from its OWN nominated source at its OWN declared
        base, proved by reading the line back through the accepted provider."""
        from baton_v12.worker_manager import line_of

        _job, control, composed = self.serving_two()
        deployment = self.deployment_of(composed)
        first = deployment.line_for("job-a")
        second = deployment.line_for("job-b")
        self.assertNotEqual(first["line_id"], second["line_id"])
        self.assertNotEqual(first["line_path"], second["line_path"])
        self.assertEqual(first["work_id"], self.work)
        self.assertEqual(second["work_id"], SECOND_WORK)
        self.assertEqual(first["declared_base"], self.base)
        self.assertEqual(second["declared_base"], self.second_base)
        self.assertEqual(first["source_path"], self.source)
        self.assertEqual(second["source_path"], self.second_source)
        # READ BACK THROUGH THE PROVIDER'S OWN READER, not from what this
        # composition just returned.
        self.assertEqual(line_of(control, second["line_id"])["declared_base"],
                         self.second_base)

    def test_the_same_job_reaches_the_same_line_every_time(self):
        """`create_line` is create-or-recover by that derived identity, so a
        second composition over the same stores recovers rather than making a
        second checkout -- which is what makes a correction the same line."""
        _job, control, composed = self.serving_two()
        deployment = self.deployment_of(composed)
        first = deployment.line_for("job-b")
        again = self.deployment_of(composed).line_for("job-b")
        self.assertEqual(again["line_id"], first["line_id"])
        self.assertEqual(again["line_path"], first["line_path"])

    def test_an_unbound_job_is_refused_before_any_line_is_made(self):
        from baton_v12.worker_manager import review_cycles

        _job, control, composed = self.serving_two()
        deployment = self.deployment_of(composed)
        before = control._connection.execute(
            "SELECT count(*) FROM review_lines").fetchone()[0]
        with self.assertRaises(ContractRefusal) as caught:
            deployment.line_for("job-nobody-submitted")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("binds no Job", caught.exception.message)
        self.assertEqual(control._connection.execute(
            "SELECT count(*) FROM review_lines").fetchone()[0], before)
        del review_cycles

    def test_one_line_asked_of_a_two_job_deployment_names_its_job(self):
        """`line()` is the one-Job spelling and says so: a line belongs to a
        Job, so a deployment serving two is asked which."""
        _job, _control, composed = self.serving_two()
        with self.assertRaises(ContractRefusal) as caught:
            self.deployment_of(composed).line()
        self.assertIn("so its Job is named", caught.exception.message)

    # -- the worker a stage reaches is the allocated one ----------------------

    def test_the_worker_for_a_stage_is_the_scheduler_s_allocation(self):
        """Actual allocation evidence selects a worker; list order never
        does."""
        from baton_v12.job_manager import scheduler, submit

        job, _control, composed = self.serving_two()
        submit(job, self.submission)
        self.drive(job, composed, "implementation", "waiting")
        # THE EPISODE'S OWN ATTEMPT, read from the Job store. With two
        # implementation workers `only_attempt` reads one worker's prepared
        # map, and which one prepared is the SCHEDULER's answer -- which is the
        # very thing this case is about.
        from baton_v12.job_manager import live_of

        attempt_id = live_of(job, "job-a/implementation")["attempt_id"]
        deployment = self.deployment_of(composed)
        allocated = scheduler.allocation_of(job, attempt_id)
        self.assertIsNotNone(allocated)
        stage = {"stage_id": "job-a/implementation", "job_id": "job-a",
                 "attempt_id": attempt_id, "kind": "implementation"}
        self.assertEqual(deployment.worker_for(stage)["worker_id"],
                         allocated["worker_id"])
        # AND IT IS ONE OF THE CONFIGURED PRODUCERS rather than whichever the
        # composition happens to list first.
        self.assertIn(allocated["worker_id"],
                      ["implementation-worker", "implementation-worker-b"])

    def test_a_stage_with_no_allocation_is_refused_rather_than_guessed(self):
        _job, _control, composed = self.serving_two()
        deployment = self.deployment_of(composed)
        with self.assertRaises(ContractRefusal) as caught:
            deployment.worker_for({"stage_id": "job-a/implementation",
                                   "job_id": "job-a",
                                   "attempt_id": "attempt-nobody-allocated",
                                   "kind": "implementation"})
        self.assertIn("not this composition's order", caught.exception.message)
