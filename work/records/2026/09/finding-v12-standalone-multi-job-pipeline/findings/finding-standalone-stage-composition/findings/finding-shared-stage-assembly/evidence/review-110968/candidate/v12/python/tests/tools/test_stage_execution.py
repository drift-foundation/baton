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
