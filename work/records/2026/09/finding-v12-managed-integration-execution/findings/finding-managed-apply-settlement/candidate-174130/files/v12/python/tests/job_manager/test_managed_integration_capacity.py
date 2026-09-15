"""W161230 slice 1: one reservation, and the executions accounted inside it.

Every case drives the REAL owners over temporary stores: the pool is activated,
the stage is reserved through `scheduler.reserve`, the capacity root is
registered against the allocation that reservation actually wrote, and every
phase this admits carries a claim that a REAL offer, acceptance and
`submit_claim` produced in the Worker Manager. No row is edited to reach a
state, no allocation is invented, and no assignment dictionary is asserted into
existence -- review 2026-09-13T17:06:59Z found arbitrary strings standing in for
all three, and they are gone.

AND NO ENDING IS A SENTENCE ANY MORE. Review 2026-09-13T17:38:55Z found free
TEXT excluding an execution from a reservation, so every ending below resolves
its proof through the owner that watches the world: `request_cancellation` and
the Authority's own fence for an execution that never started, and a positively
observed `destroyed` runtime axis for one that did. The two cases that corrupt
persisted evidence say so in their own words and explain why no owner can be
made to emit it.
"""
import json
import os
import unittest
from unittest import mock

from baton_v12.contracts import digest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import integration_capacity as capacity
from baton_v12.job_manager import execution_limits, scheduler
from baton_v12.integration import managed_execution as managed

from baton_v12.worker_manager import attempts
from baton_v12.worker_manager.attempts import (activate_assignment,
                                              assignment_of, observe,
                                              record_attempt,
                                              request_cancellation)
from baton_v12.worker_manager.offers import (accept_offer, issue_offer,
                                             submit_claim)
from baton_v12.worker_manager.intake import (intake_receipt_of,
                                             request_intake)
from baton_v12.worker_manager.manifests import retain_manifest
from baton_v12.worker_manager.output import (freeze_operation, frozen_output_of,
                                             request_freeze)
from baton_v12.worker_manager.workspaces import configure_workspace_storage

from . import fixtures
from .test_scheduling import pool, principals
PREPARATION_PHASE_NAME = "prepare"
# AND THE INTAKE ADAPTER'S OWN FAKE, unchanged. Slice2: a freeze is not
# custody, so a preparation that an apply may import is one the manager
# actually COLLECTED -- these cases drive the real `request_intake` through
# the owner that seals it.
from ..manager.test_intake import Custodian

# THE EXISTING FAKES, UNCHANGED. `request_cancellation` checks both injected
# capabilities by shape, and these are the ones the Worker Manager's own cases
# drive its cancellation with -- a second pair written here would be a second
# account of what that owner accepts.
from ..manager.test_attempts import Adapter, Agent
# AND THE OUTPUT OWNER'S OWN FIXTURES, unchanged. A preparation's collected
# content is a FROZEN OUTPUT, and the only honest way to have one is to freeze
# one: retain the published input declaration, drive the axes, and let
# `request_freeze` validate a sealed result the way it validates any other.
from ..manager.test_output import Collector, OutputCase, sealed


def _authority_contract():
    """The Authority's own v12 assignment contract, named rather than spelled.

    A literal here would be this file's second opinion about a vocabulary the
    Authority owns, and the two would diverge silently.
    """
    from baton_v12.authority.identity import V12

    return V12


class _Authorization:
    """Whether the derived candidate was independently approved, as a fake.

    Deterministic and fake, and labelled as one -- what it exercises is that
    admission asks an OWNER rather than reading a caller's document, and that
    every operand of the answer is compared.
    """

    def __init__(self, grant):
        self.grant = grant
        self.asked = []
        self.answer = {}
        self.absent = False

    def authorized(self, operands):
        self.asked.append(dict(operands))
        if self.absent:
            return None
        held = {"schema": capacity.AUTHORIZATION_SCHEMA,
                "managed_result_id": operands["managed_result_id"],
                "canonical_target_id": operands["canonical_target_id"],
                "content_digest": operands["content_digest"],
                "derived_proposal_id": "derived-proposal-1",
                "derived_result_id": "derived-result-1",
                "derived_result_digest": "sha256:" + "e" * 64,
                "approved": True}
        held.update(self.answer)
        return held


class CapacityCase(fixtures.JobManagerCase):
    """An integration stage with one real reservation behind it."""

    ORCHESTRATION = "integration-capacity-1"

    def reserved(self):
        """The integration stage's own allocation, from the scheduler."""
        store = self.store()
        document = pool()
        scheduler.activate_pool(store, document, principals(document))
        from baton_v12.job_manager import submit
        submit(store, fixtures.submission(jobs=[fixtures.job(
            "job-a", stages=[
                fixtures.stage("integration", fixtures.WORK_A)])]))
        stage = self.integration_stage(store)
        allocation = scheduler.reserve(store, stage)
        return store, stage, allocation

    def integration_stage(self, store):
        from baton_v12.job_manager.submission import stage_rows
        from baton_v12.job_manager import episodes

        [row] = [one for one in stage_rows(store)
                 if one["kind"] == "integration"]
        live = episodes.live_of(store, row["stage_id"])
        return episodes.attempting(dict(row), live)

    def plan(self, stage, **changed):
        """The actor's separate preparation, and the PARENT'S OWN apply.

        Review 2026-09-13T18:02:07Z [P1]: the apply used to be a second
        claimed execution on another Work, another offer and another attempt,
        and nothing compared any of the three with the episode holding the
        reservation. The accepted design says the apply member names the
        parent's actual attempt -- it cannot bypass the accounting precisely
        BECAUSE it already owns the allocation -- so the apply's three
        identities are read off the episode here rather than invented.
        """
        held = [{"phase": "prepare",
                 "execution_attempt_id": "prepare-attempt-1",
                 "execution_work_id": self.EXECUTION_WORK,
                 "execution_offer_id": "prepare-offer-1",
                 "participant": self.ACTOR,
                 "task_digest": "sha256:" + "a" * 64,
                 "input_digest": self.input_digest,
                 "profile_digest": fixtures.PROFILE},
                {"phase": "apply",
                 "execution_attempt_id": stage["attempt_id"],
                 "execution_work_id": stage["work_id"],
                 "execution_offer_id": stage["offer_id"],
                 "participant": self.ACTOR,
                 "task_digest": "sha256:" + "d" * 64,
                 "input_digest": self.input_digest,
                 "profile_digest": fixtures.PROFILE}]
        for one in held:
            one.update(changed.get(one["phase"], {}))
        return held

    # THE FIXTURE'S OWN CERTIFIED PROFILE, and the participant the pool worker
    # holding this reservation is configured for: a phase executes under the
    # CONFIGURED INTEGRATION ACTOR, so the session claiming for it acts for
    # that actor rather than the fixture's default identity.
    PROFILE = fixtures.PROFILE
    ACTOR = "baton.impl-a"
    # MEASURED, step 50: a sealed result carries its assignment's Work
    # reference, and §4 refuses a Work id that does not carry its authority's
    # eight-character prefix. The shared `WORK_B` was written for paths that
    # never validate a manifest, so the preparation runs on a Work that
    # actually belongs to this fixture's Authority -- the truer fixture, and
    # the only one a frozen result can name.
    EXECUTION_WORK = fixtures.UUID[:8] + "-W2"
    # THE POLICY THE OFFER AND THE ATTEMPT ARE RECORDED UNDER. The input digest
    # is NOT a constant any more: it is the digest of the input manifest this
    # case actually retains, because a frozen result is compared against the
    # declaration its attempt names and a fabricated digest names none.
    POLICY = "sha256:" + "2" * 64
    # THE CONFIGURED CHILD WORKER'S RECORDED IDENTITY, which is what the
    # runtime attempt is recorded under before it is activated. The child runs
    # on the PUBLISHED bundle, so `prepare` overrides `input_digest` with the
    # plan's own -- this document's is deliberately a different value so a
    # composition that recorded the configured manifest instead would be seen.
    IDENTITY = {"adapter_name": "acp",
                "adapter_digest": "sha256:" + "3" * 64,
                "profile_digest": PROFILE,
                "input_digest": "sha256:" + "n" * 64,
                "policy_digest": POLICY,
                "image_digest": "sha256:" + "m" * 64,
                "toolchain_digest": "sha256:" + "t" * 64}

    def owners(self):
        """THE OWNERS EVERY CASE SHARES, built once and CLAIMING NOTHING.

        Extracted from `claimed` because construction and claiming are two
        different acts, and conflating them was a real obstruction rather than
        an inelegance: a case that wants the manager, the retained declaration
        and the port -- `execution` does -- had to claim an unrelated attempt
        to get them. A REAL Authority refuses that, because a principal holds
        ONE live claim at a time across every address it acts through, so the
        warmup claim would have spent the very slot the preparation needs.
        """
        control = getattr(self, "_control", None)
        if control is not None:
            return control
        # `JobManagerCase.control()` already certifies this profile, and a
        # second certification under a different digest is an operation
        # collision -- the store telling the truth rather than a nuisance.
        control = self._control = self.control()
        # W43975: a freeze settles on a directory-custody receipt, and a
        # custody act reads the DEPLOYMENT's configured store rather than
        # a caller's operand. The preparation's collected report is a real
        # frozen output, so this fixture configures what freezing needs.
        storage = os.path.join(self.root, "workspace-store")
        os.makedirs(storage, exist_ok=True)
        configure_workspace_storage(control, storage)
        # AND THE DECLARATION THE RESULT WILL ANSWER. Its digest is what
        # the offer and the attempt record carry, so `record_frozen_result`
        # can compare declared outputs against a document this manager
        # actually holds.
        self.declaration = self.published_declaration()
        self.input_digest = retain_manifest(
            control, self.declaration, "inputManifest")["digest"]
        self.session = self.participant_session()
        self.port = self.worker_port()
        return control

    def published_declaration(self):
        """The output declaration every result in this fixture answers.

        A SEAM because a preparation declares its OWN outputs. Most cases here
        only need a declaration to exist, so this is the shared published one;
        the adoption cases declare the two outputs a preparation actually
        produces, because an adopter that read them out of a declaration
        naming something else would be proving nothing about custody.
        """
        return OutputCase.published()

    def participant_session(self):
        """The participant-bound session this fixture's port is given.

        A SEAM RATHER THAN A CONSTANT. Most cases here are about the Job
        Manager's accounting and want a session that simply answers, so this
        is the fake; `ThePreparationIsCoordinatedEndToEnd` overrides it with a
        session minted by a real Authority, which is a different and stricter
        thing entirely.
        """
        session = fixtures.FakeSession(participant=self.ACTOR)
        session.open_work(self.EXECUTION_WORK)
        session.open_work(fixtures.WORK_A)
        # THE FAKE ANSWERS ABOUT THE WORK THIS EXECUTION IS ON. Its
        # default claim answer names the fixture's first Work, and an
        # assignment recorded against another Work is correctly refused as
        # not this offer's claim -- so the fake is pointed at the Work the
        # phase is actually claimed on rather than the refusal being
        # worked around.
        session.claim_answer = dict(
            session.claim_answer,
            assignment={"work_ref": {"authority_uuid": fixtures.UUID,
                                     "work_id": self.EXECUTION_WORK},
                        "participant": self.ACTOR, "generation": 1})
        # AND THE AUTHORITY ANSWERS ABOUT THE WORK IT IS ASKED ABOUT. Two
        # executions run under this one reservation -- the actor's separate
        # preparation Work and the PARENT's own -- so a fake that answered
        # one Work's live assignment for every question would refuse the
        # parent's activation for naming the Work it is actually on.
        session.assignment_of = lambda work_id: {
            "work_ref": {"authority_uuid": fixtures.UUID,
                         "work_id": work_id},
            "participant": self.ACTOR, "generation": 1}
        return session

    def worker_port(self):
        """The Worker Manager's narrow capability over that session."""
        from baton_v12.worker_manager import AuthorityPort

        return AuthorityPort(self.session, fixtures.fake_claim_signature)

    def claimed(self, attempt_id, offer_id, recorded_input=None,
                work_id=None):
        """One REAL Worker Manager claim for a phase execution.

        The offer is issued, accepted and claimed through the owners that own
        those acts, so `assignment_of` has something to answer with. A
        capacity membership is admitted against that answer.
        """
        held = getattr(self, "_claims", None)
        if held is None:
            held = self._claims = set()
        control = self.owners()
        # ONE CLAIM PER ATTEMPT. `issue_offer` refuses to reissue an offer it
        # already minted a bearer for (measured, step 45), and several helpers
        # legitimately want "this attempt's claimed control store" without
        # caring whether they are the first to ask.
        if attempt_id in held:
            return control
        held.add(attempt_id)
        issue_offer(control, self.port, offer_id=offer_id,
                    work_id=work_id or self.EXECUTION_WORK,
                    runtime_attempt_id=attempt_id,
                    input_digest=self.input_digest,
                    policy_digest=self.POLICY,
                    profile_digest=self.PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-" + offer_id)
        accept_offer(control, self.port, offer_id=offer_id, decision="accept",
                     bearer="bearer-" + offer_id, now=fixtures.NOW,
                     runtime_attempt_id=attempt_id,
                     work_ref={"authority_uuid": fixtures.UUID,
                               "work_id": work_id or self.EXECUTION_WORK})
        record_attempt(control, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest="sha256:" + "3" * 64,
                       profile_digest=self.PROFILE,
                       input_digest=recorded_input or self.input_digest,
                       policy_digest=self.POLICY)
        submit_claim(control, self.port, offer_id=offer_id)
        # AND THE ASSIGNMENT IS ACTIVATED, because that is what FIXES it.
        # `assignment_of` answers about an activated attempt and refuses one
        # that only claimed -- which is the right order: a membership is
        # admitted against a fixed assignment, and admission itself commits
        # before any runtime start.
        activate_assignment(control, self.port, attempt_id=attempt_id,
                            expect={"work_ref": {
                                "authority_uuid": fixtures.UUID,
                                "work_id": work_id or self.EXECUTION_WORK},
                                "participant": self.ACTOR, "generation": 1})
        return control

    def collected(self, attempt_id, *, disposition="completed",
                  outputs=None, collect=True, custody="accepted"):
        """ONE REAL FROZEN OUTPUT for this attempt, through its own owner.

        `request_freeze` proves positive quiescence and a recorded terminal
        disposition, hands the adapter the exact act it is settling, and
        `record_frozen_result` validates the sealed answer against the
        declaration this attempt names. Nothing here asserts a digest: what
        the preparation collected is whatever comes back.
        """
        observe(self._control, attempt_id=attempt_id,
                axis="execution_runtime", value="running")
        observe(self._control, attempt_id=attempt_id,
                axis="execution_runtime", value="quiescent")
        observe(self._control, attempt_id=attempt_id,
                axis="worker_disposition", value=disposition)
        frozen = request_freeze(
            self._control, self.port,
            Collector(self.sealed_result(attempt_id,
                                         disposition=disposition,
                                         outputs=outputs)),
            attempt_id=attempt_id, disposition=disposition)
        if collect:
            # THE OWNER'S OWN READ-BACK, not the freeze call's answer: the
            # artifacts an intake must answer come from `frozen_output_of`
            # (measured, step 162 -- the freeze act's own document does not
            # carry them).
            self.taken(attempt_id, frozen_output_of(self._control, attempt_id),
                       custody=custody)
        return frozen

    def taken(self, attempt_id, frozen, *, custody="accepted"):
        """AND THE MANAGER ACTUALLY TAKES IT INTO CUSTODY.

        Slice2's observed gap: `_collected_content` resolved the frozen output
        only, and a freeze is the manager's receipt over a tree that stopped
        changing -- not a statement that anything was collected. An apply
        imports from custody, so these fixtures drive the real intake owner.
        """
        collection = {
            "result_id": frozen["result_id"],
            "artifacts": [{"artifact_id": one["artifact_id"],
                           "content_digest": one["content_digest"],
                           "bytes": one["bytes"],
                           "custody_locator":
                               "file:///var/lib/baton/custody/"
                               + one["artifact_id"]}
                          for one in frozen["artifacts"]]}
        if custody == "quarantined":
            # QUARANTINE IS THE MANAGER'S OWN ANSWER, reached by ending the
            # assignment before collection: material collected for a
            # generation that has ended is held aside rather than accepted.
            self.session.assignment_of = lambda work_id: None
        return request_intake(self._control, self.port, Custodian(collection),
                              attempt_id=attempt_id)

    def sealed_result(self, attempt_id, *, disposition="completed",
                      outputs=None):
        """A result that ANSWERS the retained declaration, for this attempt."""
        row = self._control._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone()
        operation = freeze_operation({key: row[key] for key in row.keys()})
        return sealed({
            "version": {"major": 1, "minor": 0},
            "manifest_id": "result-manifest-" + attempt_id,
            "created_at": fixtures.NOW,
            "extensions": {},
            "schema": "baton.worker-manifest/result",
            "result_id": "result-" + attempt_id,
            "assignment_ref": self.claim_of(attempt_id),
            "input_manifest_digest": self.input_digest,
            "policy_digest": self.POLICY,
            "disposition": disposition,
            "outputs": OutputCase.present() if outputs is None else outputs,
            "evidence": [],
            "freeze_operation": dict(operation),
            "manager_observed_at": fixtures.NOW,
            "completion_manifest_digest": "sha256:" + "9" * 64,
        })

    def destroyed(self, attempt_id):
        """The Worker Manager's own positive observation that it is gone.

        `destroyed` is the only execution-runtime answer that ends a
        membership. `quiescent` is a runtime that stopped and still exists and
        `uncertain` is the manager saying it does not know -- the cases below
        drive both and neither excludes anything.
        """
        observe(self._control, attempt_id=attempt_id,
                axis="execution_runtime", value="destroyed")

    def fenced(self, attempt_id, *, generation=1):
        """A REAL cancellation, and the Authority's own after-state.

        `request_cancellation` journals its intent, fences at the Authority and
        writes `cancel-requested`; the fake then answers as an Authority that
        has fenced this generation and no longer holds it live. Both halves are
        needed, and the negatives below withhold one at a time.
        """
        request_cancellation(self._control, self.port, Agent(), Adapter(),
                             attempt_id=attempt_id)
        held = dict(self.session.work[self.EXECUTION_WORK],
                    work_id=self.EXECUTION_WORK,
                    fenced_generations=[{"generation": generation,
                                         "cause": "cancelled",
                                         "reason": None}])
        self.session.work[self.EXECUTION_WORK] = held
        # AND IT IS NO LONGER THE LIVE ONE. A generation both fenced and live
        # is one owner giving two answers, and the reader refuses that rather
        # than picking the convenient half.
        self.session.assignment_of = lambda work_id: None

    def admit(self, phase, attempt_id, offer_id, store):
        control = self.claimed(attempt_id, offer_id)
        return capacity.admit_integration_execution(
            store, control, orchestration_id=self.ORCHESTRATION, phase=phase,
            execution_attempt_id=attempt_id,
            assignment=self.claim_of(attempt_id))

    def prepared(self, store, *, outcome="succeeded", collect=True):
        """One preparation admitted, really collected, destroyed and ended.

        THE ORDER IS THE LIFECYCLE'S: a freeze describes a tree the writer has
        stopped changing, so quiescence and collection come first and
        destruction -- the fact that ends the MEMBERSHIP -- comes after.
        """
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        if collect:
            self.collected("prepare-attempt-1")
        self.destroyed("prepare-attempt-1")
        return capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome=outcome, exclusion="runtime-destroyed")

    def coordinated(self):
        """A real coordinator with a real entry and a real LIVE grant.

        An apply is admitted with the grant it will run under, read from the
        coordinator rather than presented by its holder -- so the capacity
        cases carry a real one rather than a lease id they wrote down.
        """
        held = getattr(self, "_coordinator", None)
        if held is None:
            import os
            from baton_v12.integration import (IntegrationStore,
                                               activate_target, enqueue,
                                               grant_lease)
            from ..integration import fixtures as coordinator_fixtures
            held = self._coordinator = IntegrationStore.open(
                os.path.join(self.root, "coordinator.sqlite3"),
                incarnation="coordinator-1", clock=self.clock)
            self.addCleanup(held.close)
            activate_target(held, coordinator_fixtures.target())
            enqueue(held, canonical_target_id=coordinator_fixtures.TARGET,
                    entry_id="entry-1",
                    eligibility=coordinator_fixtures.eligibility())
            answer = grant_lease(
                held, canonical_target_id=coordinator_fixtures.TARGET,
                entry_id="entry-1", lease_id="lease-1",
                integrator_participant="baton.integrator",
                attempt_id="attempt-1")
            self.grant = {"canonical_target_id": coordinator_fixtures.TARGET,
                          "entry_id": "entry-1", "lease_id": "lease-1",
                          "fence": answer["lease"]["fence"]}
            self.authorization = _Authorization(self.grant)
        return held

    def applying(self, store, stage, **changed):
        """The PARENT'S OWN attempt, claimed on the parent Work, with the
        grant and the authorization an apply is admitted with."""
        self.claimed(stage["attempt_id"], stage["offer_id"],
                     work_id=stage["work_id"])
        coordinator = self.coordinated()
        held = {"coordinator": coordinator, "authorization": self.authorization,
                "grant": self.grant}
        held.update(changed)
        return capacity.admit_integration_execution(
            store, self._control, orchestration_id=self.ORCHESTRATION,
            phase="apply", execution_attempt_id=stage["attempt_id"],
            assignment=self.claim_of(stage["attempt_id"]), **held)

    def registered(self, **changed):
        store, stage, allocation = self.reserved()
        # THE CLAIM MACHINERY IS BUILT FIRST, because the plan's input digest
        # is the digest of the declaration this case actually retains.
        self.preclaimed()
        answer = capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=fixtures.UUID, plan=self.plan(stage, **changed))
        return store, stage, allocation, answer

    def request(self, **changed):
        held = {"orchestration_id": self.ORCHESTRATION,
                "canonical_target_id": "target:mainline",
                "job_id": "job-a", "line_id": "line-b",
                "source_proposal_id": "proposal-1",
                "source": {"base": "a" * 40, "candidate": "c" * 40,
                           "target_revision": "d" * 40},
                "authority": {"path_set_digest": "sha256:" + "1" * 64,
                              "test_scope_digest": "sha256:" + "2" * 64},
                "harness_digest": "sha256:" + "h" * 64,
                "profile_digest": fixtures.PROFILE,
                "input_digest": self.input_digest,
                "execution_limits": execution_limits.resolved({}, 1),
                "commands": ["combined", "base", "isolated"]}
        held.update(changed)
        return managed.preparation_request(**held)

    def preclaimed(self):
        """The phase assignment the admitting cases are admitted AGAINST.

        Most cases here are about what capacity does with a claim that already
        exists, so the fixture takes one up front. A case that makes the claim
        ITSELF must not -- see `ThePreparationIsCoordinatedEndToEnd`, where the
        actor's one real claim slot belongs to the preparation under test.
        """
        return self.claimed("prepare-attempt-1", "prepare-offer-1")

    def claim_of(self, attempt_id):
        """The assignment the Worker Manager actually fixed for this attempt.

        Built from its own reader rather than spelled here: an assignment a
        test writes down is a dictionary, and what a membership must be
        admitted against is what the claim recorded.
        """
        held = assignment_of(self._control, attempt_id)
        return {"work_ref": {"authority_uuid": held["authority_uuid"],
                             "work_id": held["work_id"]},
                "participant": held["participant"],
                "generation": held["generation"]}


class TheRootNamesCapacityItDidNotCreate(CapacityCase):

    def test_a_root_binds_the_allocation_the_scheduler_wrote(self):
        """The worker, participant, principal and pool generation are READ
        from the allocation. A caller does not get to name them, because a
        root describing capacity differently from the reservation it claims to
        be would be accounting fiction."""
        _store, stage, allocation, answer = self.registered()
        root = answer["root"]
        self.assertEqual(root["root_assignment_id"],
                         allocation["assignment_id"])
        self.assertEqual(root["worker_id"], allocation["worker_id"])
        self.assertEqual(root["participant"], allocation["participant"])
        self.assertEqual(root["canonical_principal"],
                         allocation["canonical_principal"])
        self.assertEqual(root["pool_generation"], allocation["generation"])
        self.assertEqual(root["stage_id"], stage["stage_id"])
        self.assertEqual(root["lifecycle"], "open")

    def test_every_phase_starts_planned_and_claims_nothing(self):
        """A planned membership carries NO assignment: the Work and the offer
        are intended, the claim has not happened, and inventing its generation
        is exactly what this refuses to do."""
        _store, _stage, _allocation, answer = self.registered()
        self.assertEqual([one["phase"] for one in answer["members"]],
                         ["apply", "prepare"])
        for member in answer["members"]:
            with self.subTest(phase=member["phase"]):
                self.assertEqual(member["state"], "planned")
                self.assertIsNone(member["assignment"])
                self.assertIsNone(member["outcome"])

    def test_a_root_for_an_allocation_nobody_reserved_is_refused(self):
        store, stage, _allocation = self.reserved()
        self.claimed("prepare-attempt-1", "prepare-offer-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.register_integration_capacity(
                store, orchestration_id=self.ORCHESTRATION,
                root_assignment_id="attempt-nobody-reserved",
                authority_uuid=fixtures.UUID, plan=self.plan(stage))
        self.assertIn("has no allocation", str(caught.exception))

    def test_an_exact_repeat_replays_and_a_changed_plan_collides(self):
        store, stage, allocation, first = self.registered()
        again = capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=fixtures.UUID, plan=self.plan(stage))
        self.assertEqual(again, first)
        with self.assertRaises(ContractRefusal) as caught:
            capacity.register_integration_capacity(
                store, orchestration_id=self.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                authority_uuid=fixtures.UUID,
                plan=self.plan(stage,
                               prepare={"task_digest": "sha256:" + "f" * 64}))
        self.assertEqual(caught.exception.code, "operation-collision")


class ThePhasesAreSerial(CapacityCase):

    def test_the_apply_is_the_parents_own_execution(self):
        """[P1] Review 2026-09-13T18:02:07Z: the apply was a SEPARATE claimed
        execution on another Work, offer and attempt, and registration
        compared none of them with the episode holding the reservation -- so
        the membership accounted for something that was not the parent apply.

        The accepted design is explicit: the apply member names the parent's
        actual attempt, and it cannot bypass the accounting precisely because
        it already owns the allocation.
        """
        _store, stage, allocation, answer = self.registered()
        applying = {one["phase"]: one for one in answer["members"]}["apply"]
        self.assertEqual(applying["execution_attempt_id"],
                         allocation["assignment_id"])
        self.assertEqual(applying["execution_attempt_id"],
                         stage["attempt_id"])
        self.assertEqual(applying["execution_offer_id"], stage["offer_id"])
        self.assertEqual(applying["execution_work_id"], stage["work_id"])

    def test_an_apply_on_a_foreign_identity_is_refused(self):
        """Each of the three, one at a time, so none hides behind another."""
        for member, wrong in (("execution_attempt_id", "apply-attempt-1"),
                              ("execution_offer_id", "apply-offer-1"),
                              ("execution_work_id", fixtures.WORK_B)):
            with self.subTest(member=member):
                case = type(self)(self._testMethodName)
                case.setUp()
                store, stage, allocation = case.reserved()
                case.claimed("prepare-attempt-1", "prepare-offer-1")
                with self.assertRaises(ContractRefusal) as caught:
                    capacity.register_integration_capacity(
                        store, orchestration_id=case.ORCHESTRATION,
                        root_assignment_id=allocation["assignment_id"],
                        authority_uuid=fixtures.UUID,
                        plan=case.plan(stage, **{"apply": {member: wrong}}))
                self.assertIn("the apply IS the parent's own execution",
                              str(caught.exception))
                case.doCleanups()

    def test_a_preparation_wearing_the_parents_identity_is_refused(self):
        """A preparation is the actor's SEPARATE execution under this
        reservation. One that named the parent's attempt would be the apply."""
        store, stage, allocation = self.reserved()
        self.claimed("prepare-attempt-1", "prepare-offer-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.register_integration_capacity(
                store, orchestration_id=self.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                authority_uuid=fixtures.UUID,
                plan=self.plan(stage, prepare={
                    "execution_offer_id": stage["offer_id"]}))
        # THE OFFER, because naming the parent's ATTEMPT is refused one rule
        # earlier -- a plan naming one execution attempt twice (measured, step
        # 49). Both refusals are right; this case is about the parent rule, so
        # it drives the member that reaches it.
        self.assertIn("which is the parent's own", str(caught.exception))

    def test_apply_is_refused_while_preparation_is_still_live(self):
        """A parent apply and its preparation can never both be live under one
        reservation, and with this two-phase plan the APPLY GATE is the first
        thing that says so: an apply follows a preparation that ended
        successfully, and this one has not ended at all.

        The serial rule has two further enforcers behind that gate -- the
        explicit live-member check for any plan the gate does not cover, and
        the partial unique index `capacity_one_active_member`, which is
        structural. This case asserts the refusal that actually fires rather
        than the one I expected to.
        """
        store, stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertIn("an apply follows a preparation that ended successfully",
                      str(caught.exception))

    def test_the_apply_phase_is_admitted_after_preparation_ends(self):
        store, stage, _allocation, _answer = self.registered()
        self.prepared(store)
        answer = self.applying(store, stage)
        held = {one["phase"]: one for one in answer["members"]}
        self.assertEqual(held["prepare"]["state"], "ended")
        self.assertEqual(held["prepare"]["outcome"], "succeeded")
        self.assertEqual(held["apply"]["state"], "admitted")
        self.assertEqual(json.loads(held["apply"]["assignment"]),
                         self.claim_of(stage["attempt_id"]))
        # AND THE CONTENT IT IMPORTS WAS DERIVED, not declared: it is exactly
        # what the preparation's frozen output actually carried.
        self.assertEqual(held["apply"]["parent_content_digest"],
                         held["prepare"]["collected_digest"])
        self.assertEqual(
            held["prepare"]["collected_digest"],
            frozen_output_of(self._control,
                             "prepare-attempt-1")["manifest_digest"])

    def test_an_admission_naming_another_participant_is_refused(self):
        store, _stage, _allocation, _answer = self.registered()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.admit_integration_execution(
                store, self.claimed("prepare-attempt-1", "prepare-offer-1"),
                orchestration_id=self.ORCHESTRATION, phase="prepare",
                execution_attempt_id="prepare-attempt-1",
                assignment=dict(self.claim_of("prepare-attempt-1"),
                                participant="baton.somebody-else"))
        # THE CLAIM CHECK FIRES FIRST, and that is the stronger refusal: an
        # assignment that disagrees with what the owner recorded is refused
        # before anything compares it to the plan.
        self.assertIn("where the claim says", str(caught.exception))

    def test_a_plan_naming_an_offer_nobody_issued_is_refused(self):
        """[P1] The offer the claim SETTLED is the offer that was planned.

        Review 2026-09-13T17:33:59Z demonstrated the permissive form: a plan
        naming `unissued-offer` was admitted, because nothing compared it with
        the offer the claim actually settled.
        """
        store, stage, allocation = self.reserved()
        control = self.claimed("prepare-attempt-1", "prepare-offer-1")
        capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=fixtures.UUID,
            plan=self.plan(stage,
                           prepare={"execution_offer_id": "unissued-offer"}))
        with self.assertRaises(ContractRefusal) as caught:
            capacity.admit_integration_execution(
                store, control, orchestration_id=self.ORCHESTRATION,
                phase="prepare", execution_attempt_id="prepare-attempt-1",
                assignment=self.claim_of("prepare-attempt-1"))
        self.assertIn("its claim settled", str(caught.exception))

    def test_a_plan_whose_digests_disagree_with_the_claim_is_refused(self):
        """[P1] The plan says what the phase was meant to run, the offer says
        what was claimed, and the attempt record says what the manager
        configured. Two of three agreeing is not agreement."""
        for name in ("profile_digest", "input_digest"):
            with self.subTest(digest=name):
                case = type(self)(self._testMethodName)
                case.setUp()
                store, stage, allocation = case.reserved()
                control = case.claimed("prepare-attempt-1", "prepare-offer-1")
                capacity.register_integration_capacity(
                    store, orchestration_id=case.ORCHESTRATION,
                    root_assignment_id=allocation["assignment_id"],
                    authority_uuid=fixtures.UUID,
                    plan=case.plan(stage,
                                   prepare={name: "sha256:" + "f" * 64}))
                with self.assertRaises(ContractRefusal) as caught:
                    capacity.admit_integration_execution(
                        store, control,
                        orchestration_id=case.ORCHESTRATION, phase="prepare",
                        execution_attempt_id="prepare-attempt-1",
                        assignment=case.claim_of("prepare-attempt-1"))
                self.assertIn(f"planned with {name}", str(caught.exception))
                case.doCleanups()

    def test_an_unplanned_execution_cannot_be_admitted(self):
        store, _stage, _allocation, _answer = self.registered()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.admit_integration_execution(
                store, self.claimed("prepare-attempt-1", "prepare-offer-1"),
                orchestration_id=self.ORCHESTRATION, phase="prepare",
                execution_attempt_id="attempt-nobody-planned",
                assignment=self.claim_of("prepare-attempt-1"))
        # AND THE WORKER MANAGER REFUSES FIRST for an attempt it never
        # recorded, which is the honest owner of that question.
        self.assertIn("no runtime attempt", str(caught.exception))

    def test_a_failed_execution_ends_without_becoming_a_success(self):
        """`failed` is an ENDING like `succeeded` is. The outcome says what the
        execution did; the exclusion says the capacity is free. The proof here
        is the same one a success would need -- which is the point: the
        evidence is about the runtime, not about the result."""
        store, _stage, _allocation, _answer = self.registered()
        answer = self.prepared(store, outcome="failed")
        held = {one["phase"]: one for one in answer["members"]}
        self.assertEqual(held["prepare"]["state"], "ended")
        self.assertEqual(held["prepare"]["outcome"], "failed")
        self.assertEqual(held["prepare"]["exclusion"], "runtime-destroyed")
        self.assertIsNone(held["prepare"]["collected_digest"])


class TheRegisteredRootHoldsItsCapacity(CapacityCase):

    def test_an_open_root_refuses_to_release(self):
        store, _stage, allocation, _answer = self.registered()
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.release(store, allocation["assignment_id"],
                              "cleanup-complete")
        self.assertIn("is still open", str(caught.exception))
        self.assertEqual(
            scheduler.allocation_of(store, allocation["assignment_id"])
            ["allocation_state"], "reserved")

    def test_a_plan_without_its_parent_apply_is_refused(self):
        """Finish condition 1: the parent apply is an EXPLICIT member. An
        orchestration that plans only its preparation would run its apply
        outside the accounting, which is the hidden capacity these relations
        exist to remove."""
        store, stage, allocation = self.reserved()
        self.claimed("prepare-attempt-1", "prepare-offer-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.register_integration_capacity(
                store, orchestration_id=self.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                authority_uuid=fixtures.UUID,
                plan=[one for one in self.plan(stage)
                      if one["phase"] == "prepare"])
        self.assertIn("names every phase", str(caught.exception))

    def test_an_admitted_member_refuses_to_release(self):
        """The named branch matters: a VALIDATED COMPLETION of the parent
        stage says nothing about a preparation execution still running under
        its reservation."""
        store, _stage, allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION,
            reason="the preparation failed")
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.release(store, allocation["assignment_id"],
                              scheduler.INTEGRATION_COMPLETED)
        self.assertIn("prepare", str(caught.exception))
        self.assertIn("proved excluded", str(caught.exception))

    def test_quarantine_still_works_while_a_member_is_open(self):
        """THE GUARD IS ON THE RELEASE TRANSITION ONLY. A root that could not
        be quarantined because a member is open would be worse than the defect
        -- uncertainty is exactly when capacity must stay held AND visible."""
        store, _stage, allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        moved = scheduler.require_recovery(store,
                                           allocation["assignment_id"])
        self.assertEqual(moved["allocation_state"], "recovery-required")

    def test_capacity_releases_once_after_a_validated_ending(self):
        store, _stage, allocation, _answer = self.registered()
        self.prepared(store, outcome="failed")
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION,
            reason="the preparation failed")
        moved = scheduler.release(store, allocation["assignment_id"],
                                  "launch-failed-before-runtime")
        self.assertEqual(moved["allocation_state"], "released")
        held = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        self.assertEqual(held["root"]["lifecycle"], "ended")
        # AND THE PLANNED PHASE THAT NEVER RAN WAS CANCELLED, not ended as an
        # execution that happened.
        members = {one["phase"]: one for one in held["members"]}
        # CANCELLED, NOT ENDED: it never ran, so it has no outcome to report.
        self.assertEqual(members["apply"]["state"], "cancelled")
        self.assertIsNone(members["apply"]["outcome"])
        self.assertIn("cancelled before admission",
                      members["apply"]["ending_evidence"])

    def test_an_unregistered_allocation_keeps_its_ordinary_behaviour(self):
        store, _stage, allocation = self.reserved()
        moved = scheduler.release(store, allocation["assignment_id"],
                                  "cleanup-complete")
        self.assertEqual(moved["allocation_state"], "released")


class TheEndingTakesEvidenceItsOwnerResolved(CapacityCase):
    """[P1] Review 2026-09-13T17:38:55Z: free text excluded an execution.

    An ending is a claim about the WORLD -- that nothing is still executing
    under this reservation -- and the only honest source for it is the owner
    that watches the world. The caller NAMES which proof applies and the
    capacity owner resolves it: the Authority's own fence for an execution that
    never started, and a positively observed destroyed runtime for one that
    did. Neither name can be asserted, and neither substitutes for the other.
    """

    def admitted(self):
        store, _stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        return store

    def test_a_cancelled_execution_ends_on_the_authoritys_own_fence(self):
        store = self.admitted()
        self.fenced("prepare-attempt-1")
        answer = capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome="failed", exclusion="fenced-before-start", port=self.port)
        held = {one["phase"]: one for one in answer["members"]}["prepare"]
        self.assertEqual(held["state"], "ended")
        self.assertEqual(held["exclusion"], "fenced-before-start")
        # AND THE PROOF IS RETAINED, not a summary of it: a later reader can
        # re-derive the judgment instead of trusting the word `ended`.
        evidence = json.loads(held["ending_evidence"])
        self.assertEqual(evidence["attempt_id"], "prepare-attempt-1")
        self.assertEqual(evidence["execution_runtime"], "cancel-requested")
        self.assertEqual(evidence["assignment"],
                         self.claim_of("prepare-attempt-1"))
        self.assertNotIn("runtime_id", evidence)

    def test_a_destroyed_runtime_ends_on_the_observed_axis(self):
        store = self.admitted()
        frozen = self.collected("prepare-attempt-1")
        self.destroyed("prepare-attempt-1")
        answer = capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome="succeeded", exclusion="runtime-destroyed")
        held = {one["phase"]: one for one in answer["members"]}["prepare"]
        self.assertEqual(held["exclusion"], "runtime-destroyed")
        self.assertEqual(json.loads(held["ending_evidence"])
                         ["execution_runtime"], "destroyed")
        # THE COLLECTED CONTENT IS THE OWNER'S, not an operand: there is no
        # `collected_digest` to pass any more, and what is recorded is exactly
        # what the frozen output carries.
        self.assertEqual(held["collected_digest"], frozen["manifest_digest"])
        report = json.loads(held["collected_report"])
        self.assertEqual(report["result_id"], frozen["result_id"])
        self.assertEqual(report["disposition"], "completed")

    def test_a_running_execution_cannot_be_ended_by_saying_so(self):
        """THE DEFECT ITSELF. The old form took the sentence and excluded the
        execution; there is no sentence to take now, and the axis says
        `not-started` because nothing was ever observed."""
        store = self.admitted()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="failed",
                exclusion="runtime-destroyed")
        self.assertIn("positively observed destroyed", str(caught.exception))
        held = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        self.assertEqual({one["phase"]: one["state"]
                          for one in held["members"]}["prepare"], "admitted")

    def test_a_quiescent_runtime_is_not_a_destroyed_one(self):
        """A runtime that stopped executing STILL EXISTS. Reading `quiescent`
        as exclusion is the fabricated quiescence this Work forbids."""
        store = self.admitted()
        # COLLECTED AND STILL NOT EXCLUDED. A freeze proves the writer stopped
        # changing the tree; the container is still there, and the membership
        # is not free until something says it is gone.
        self.collected("prepare-attempt-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="succeeded",
                exclusion="runtime-destroyed")
        self.assertIn("quiescent", str(caught.exception))

    def test_a_fence_without_a_session_refuses_rather_than_assumes(self):
        store = self.admitted()
        self.fenced("prepare-attempt-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="failed",
                exclusion="fenced-before-start")
        self.assertIn("no session was given", str(caught.exception))

    def test_an_unfenced_cancellation_does_not_end_anything(self):
        """The Authority's fence is ITS act. A cancellation this manager
        journalled and an Authority that never fenced the generation are
        exactly the interrupted case, and capacity stays held."""
        store = self.admitted()
        request_cancellation(self._control, self.port, Agent(), Adapter(),
                             attempt_id="prepare-attempt-1")
        # THE PROJECTION NAMES THE WORK and no fence whatever, so the refusal
        # is about the missing fence rather than about a projection that could
        # not say which Work it described -- measured, step 40: the fixture's
        # default omits `work_id` and the reader refused THAT first, which is
        # a different (and also correct) refusal from the one this case is
        # about.
        self.session.work[self.EXECUTION_WORK] = dict(
            self.session.work[self.EXECUTION_WORK],
            work_id=self.EXECUTION_WORK, fenced_generations=[])
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="failed",
                exclusion="fenced-before-start", port=self.port)
        self.assertIn("has not fenced generation", str(caught.exception))

    def test_a_fence_is_not_a_result(self):
        """`succeeded` on a proof that it never started is a contradiction:
        accepting it would let a fence stand in for a result."""
        store = self.admitted()
        self.fenced("prepare-attempt-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1",
                outcome="succeeded", exclusion="fenced-before-start",
                port=self.port)
        self.assertIn("a fence is not a result", str(caught.exception))

    def test_an_unknown_exclusion_name_is_refused(self):
        store = self.admitted()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="failed",
                exclusion="the operator says it is gone")
        self.assertIn("an exclusion proof is one of", str(caught.exception))

    def test_a_cancelled_plan_is_never_settled_as_an_execution(self):
        """[P2] `cancelled` fell through both guards and was UPDATED to
        `ended` with an outcome -- turning "this never happened" into "this
        failed" at the moment the two are hardest to tell apart."""
        store, stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION,
            reason="the preparation will not finish")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id=stage["attempt_id"], outcome="failed",
                exclusion="runtime-destroyed")
        self.assertIn("has no outcome to record", str(caught.exception))

    def test_no_collected_report_is_its_own_answer(self):
        """[P1] Review 2026-09-13T18:02:07Z reproduced the defect exactly: a
        caller digest became the successful preparation's content while
        `frozen_output_of` answered None before and after. There is no digest
        to pass now, and absence is a refusal rather than content."""
        store = self.admitted()
        self.destroyed("prepare-attempt-1")
        self.assertIsNone(frozen_output_of(self._control,
                                           "prepare-attempt-1"))
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1",
                outcome="succeeded", exclusion="runtime-destroyed")
        self.assertIn("no report was collected", str(caught.exception))

    def test_a_report_at_another_disposition_collected_no_content(self):
        """The THIRD answer, kept apart from the other two: a report WAS
        collected and it says the worker was unable. That is not importable
        content, and reading it as one would import a failure."""
        store = self.admitted()
        self.collected("prepare-attempt-1", disposition="unable",
                       outputs=OutputCase.missing())
        self.destroyed("prepare-attempt-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1",
                outcome="succeeded", exclusion="runtime-destroyed")
        self.assertIn("only 'completed' is a collected result",
                      str(caught.exception))

    def test_a_frozen_but_uncollected_preparation_cannot_be_imported(self):
        """Slice2's observed custody gap. A freeze is the manager's receipt
        over a tree the writer stopped changing; it says nothing about whether
        the bytes were collected, and an apply reads from custody."""
        store, _stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        self.collected("prepare-attempt-1", collect=False)
        self.destroyed("prepare-attempt-1")
        self.assertIsNone(intake_receipt_of(self._control,
                                            "prepare-attempt-1"))
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1",
                outcome="succeeded", exclusion="runtime-destroyed")
        self.assertIn("not a statement that anything was taken into custody",
                      str(caught.exception))

    def test_quarantined_custody_is_not_absence_and_not_success(self):
        """Content collected and deliberately held aside is a third answer.
        Reading it as either would import material the manager set apart."""
        store, _stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        self.collected("prepare-attempt-1", custody="quarantined")
        held = intake_receipt_of(self._control, "prepare-attempt-1")
        self.assertEqual(held["custody"], "quarantined")
        self.destroyed("prepare-attempt-1")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1",
                outcome="succeeded", exclusion="runtime-destroyed")
        self.assertIn("deliberately held aside", str(caught.exception))

    def test_accepted_custody_carries_its_measured_artifacts(self):
        """An apply names content by digest and length, not by a path."""
        store, _stage, _allocation, _answer = self.registered()
        answer = self.prepared(store)
        held = {one["phase"]: one for one in answer["members"]}["prepare"]
        report = json.loads(held["collected_report"])
        self.assertEqual(report["custody"], "accepted")
        self.assertTrue(report["artifacts"])
        for one in report["artifacts"]:
            with self.subTest(artifact=one["artifact_id"]):
                self.assertEqual(sorted(one),
                                 ["artifact_id", "bytes", "content_digest"])
                self.assertIsInstance(one["bytes"], int)
                self.assertTrue(one["content_digest"].startswith("sha256:"))
        # AND THE ACT THAT TOOK CUSTODY IS NAMED, so a later reader can ask
        # the journal rather than trust the word.
        self.assertIn("operation_id", report["intake_operation"])

    def test_a_tampered_receipt_is_refused_by_the_intake_owner(self):
        """AND THAT OWNER GETS THERE FIRST, which is the right one.

        Measured, step 164: editing an intake row is caught by the intake
        reader's own digest recomputation before this capacity owner compares
        the receipt with the frozen output. My cross-owner comparison stays
        for the case that reader cannot see -- two owners legitimately
        answering about different results -- and I am not asserting a refusal
        reached by a route intake closes, nor claiming coverage of the path I
        did not reach.
        """
        store, _stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        self.collected("prepare-attempt-1")
        self.destroyed("prepare-attempt-1")
        self._control._connection.execute(
            "UPDATE intakes SET result_id = ? WHERE runtime_attempt_id = ?",
            ("result-somebody-elses", "prepare-attempt-1"))
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1",
                outcome="succeeded", exclusion="runtime-destroyed")
        self.assertIn("a row and the digest beside it moved together",
                      str(caught.exception))

    def test_a_failed_execution_records_no_collected_content(self):
        """A failed execution contributes nothing an apply may import, whatever
        it froze: what it froze is retained by its own owner and is not this
        membership's account of importable content."""
        store = self.admitted()
        self.collected("prepare-attempt-1")
        self.destroyed("prepare-attempt-1")
        answer = capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome="failed", exclusion="runtime-destroyed")
        held = {one["phase"]: one for one in answer["members"]}["prepare"]
        self.assertIsNone(held["collected_digest"])
        self.assertIsNone(held["collected_report"])


class TheUncertainExecutionHoldsItsCapacity(CapacityCase):
    """`recovery-required` is LIVE on purpose: uncertainty holds capacity.

    The honest answer to "is anything still running under this reservation" is
    sometimes "I do not know", and the conservative reading of that is that
    something is. The state is entered by its own operation and left only
    through an ending whose proof the owner resolved -- which is what
    reconciling it MEANS.
    """

    def uncertain(self):
        store, stage, allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        answer = capacity.require_integration_recovery(
            store, execution_attempt_id="prepare-attempt-1",
            reason="the engine could not be reached after the start")
        return store, stage, allocation, answer

    def test_recovery_holds_the_member_live_and_carries_no_outcome(self):
        _store, _stage, _allocation, answer = self.uncertain()
        held = {one["phase"]: one for one in answer["members"]}["prepare"]
        self.assertEqual(held["state"], "recovery-required")
        self.assertIsNone(held["outcome"])
        self.assertIsNone(held["exclusion"])
        self.assertIn("could not be reached", held["recovery_reason"])

    def test_an_uncertain_member_blocks_release(self):
        store, _stage, allocation, _answer = self.uncertain()
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="giving up")
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.release(store, allocation["assignment_id"],
                              scheduler.INTEGRATION_COMPLETED)
        self.assertIn("recovery-required", str(caught.exception))

    def test_nothing_new_is_admitted_while_one_member_is_uncertain(self):
        store, stage, _allocation, _answer = self.uncertain()
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        # The apply gate speaks first and says the same thing: the preparation
        # has not ended, so nothing follows it.
        self.assertIn("ended successfully", str(caught.exception))

    def test_recovery_is_reconciled_only_by_the_owners_own_proof(self):
        store, _stage, allocation, _answer = self.uncertain()
        with self.assertRaises(ContractRefusal):
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="failed",
                exclusion="runtime-destroyed")
        self.destroyed("prepare-attempt-1")
        answer = capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome="failed", exclusion="runtime-destroyed")
        held = {one["phase"]: one for one in answer["members"]}["prepare"]
        self.assertEqual(held["state"], "ended")
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="reconciled")
        self.assertEqual(
            scheduler.release(store, allocation["assignment_id"],
                              scheduler.INTEGRATION_COMPLETED)
            ["allocation_state"], "released")

    def test_only_an_admitted_execution_can_become_uncertain(self):
        store, stage, _allocation, _answer = self.registered()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.require_integration_recovery(
                store, execution_attempt_id=stage["attempt_id"],
                reason="it might be running")
        self.assertIn("only an admitted execution", str(caught.exception))


class ThePersistedEvidenceIsOwnedEndToEnd(CapacityCase):
    """[P2] Review 2026-09-13T17:38:55Z: the journal read was half-owned.

    The first form loaded `signature["operands"]`, checked that it was a dict
    naming this attempt and read two values out of it. `operation_record` owns
    the persisted row's COLUMN shapes; what an `attempt.record` operation MEANS
    -- its envelope kind, its exact operands, its own result -- is this
    reader's fact, and a reader that owns one of the three has owned the
    easiest one.

    WHY THESE CASES WRITE ROWS DIRECTLY. No owner emits this evidence, and that
    is the point: `record_attempt` signs its own operands and `ControlStore`
    compares the envelope's kind against the row's, so a manager producing any
    of it would itself be the defect. What is under test is the CAPACITY
    OWNER's behaviour when it reads persisted evidence from a store this
    process did not write -- the case a control store exists to survive.
    """

    def corrupted(self, attempt_id, **columns):
        control = self.claimed(attempt_id, "prepare-offer-1")
        sets = ", ".join(f"{name} = ?" for name in columns)
        control._connection.execute(
            f"UPDATE operations SET {sets} WHERE operation_id = ?",
            tuple(columns.values()) + ("attempt.record:" + attempt_id,))
        return control

    def admitting(self, store, control):
        return capacity.admit_integration_execution(
            store, control, orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))

    def signed(self, kind, operands):
        return json.dumps({"kind": kind, "operands": operands},
                          sort_keys=True, separators=(",", ":"))

    def operands(self, **changed):
        held = {"attempt_id": "prepare-attempt-1", "adapter_name": "acp",
                "adapter_digest": "sha256:" + "3" * 64,
                "profile_digest": self.PROFILE,
                "input_digest": "sha256:" + "b" * 64,
                "policy_digest": "sha256:" + "2" * 64,
                "image_digest": None, "toolchain_digest": None}
        held.update(changed)
        return held

    def test_a_record_signed_as_another_kind_is_refused(self):
        """The row's `kind` column and the signature's are two accounts of one
        operation. A reader that checks the column alone accepts a row whose
        signed document is about something else entirely."""
        store, _stage, _allocation, _answer = self.registered()
        control = self.corrupted(
            "prepare-attempt-1",
            signature=self.signed("attempt.cancel", self.operands()))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("two accounts of one operation", str(caught.exception))

    def test_operands_carrying_a_member_this_build_does_not_know(self):
        """A closed contract that accepts extra members is not closed."""
        store, _stage, _allocation, _answer = self.registered()
        control = self.corrupted(
            "prepare-attempt-1",
            signature=self.signed("attempt.record",
                                  self.operands(sidecar_digest="sha256:0")))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("the attempt record's operands", str(caught.exception))

    def test_a_record_signed_over_another_attempt_is_refused(self):
        store, _stage, _allocation, _answer = self.registered()
        control = self.corrupted(
            "prepare-attempt-1",
            signature=self.signed("attempt.record",
                                  self.operands(attempt_id="another-attempt-1")))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("signed over attempt", str(caught.exception))

    def test_a_result_describing_another_attempt_is_refused(self):
        """The result is what a REPLAY hands back. A row whose two halves
        describe different attempts configures one and reports another."""
        store, _stage, _allocation, _answer = self.registered()
        control = self.corrupted(
            "prepare-attempt-1",
            result=json.dumps({"attempt_id": "another-attempt-1",
                               "adapter_name": "acp",
                               "profile_digest": self.PROFILE},
                              sort_keys=True))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("answered attempt_id", str(caught.exception))

    def test_a_refused_record_configured_nothing(self):
        """MEASURED, step 42: `operations.state` is CHECKed to `committed` or
        `refused`, so a `live` row is not a state this store can hold at all --
        the relation already answers that half. What it does hold is a REFUSED
        record at exactly this identity, which is a real outcome of a real
        `record_attempt` and configures nothing."""
        store, _stage, _allocation, _answer = self.registered()
        control = self.corrupted(
            "prepare-attempt-1", state="refused", result=None,
            refusal=json.dumps({"category": "refused", "code": "precondition",
                                "message": "the adapter was not certified",
                                "durable": True}, sort_keys=True))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("committed configured nothing", str(caught.exception))

    def test_the_recorded_attempt_may_disagree_alone(self):
        """THE THIRD ACCOUNT, on its own. The two refusals added last claim
        both changed the PLAN, so the offer disagreed too and either
        comparison could have produced them. `record_attempt` is a separate
        act from the offer -- nothing in the Worker Manager compares its
        digests to the claimed offer's -- so this drives the real owner with a
        differing input digest while plan and offer agree exactly.
        """
        store, stage, allocation = self.reserved()
        # THE CLAIM IS BUILT FIRST AND DIFFERENTLY, because claiming is
        # idempotent per attempt (measured, step 49): the plan and the offer
        # carry the retained declaration's digest and only the RECORDED
        # attempt carries another.
        control = self.claimed("prepare-attempt-1", "prepare-offer-1",
                               recorded_input="sha256:" + "e" * 64)
        capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=fixtures.UUID, plan=self.plan(stage))
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("was recorded with 'sha256:" + "e" * 20,
                      str(caught.exception))


class TheOfferIdentityIsComplete(CapacityCase):
    """An offer and the claim it settled are ONE identity.

    Work and generation were compared and the Authority and the participant
    were not -- and an offer settled for another actor, or under another
    Authority, is another claim. These cases rewrite the persisted offer for
    the same reason the journal cases rewrite the journal: the owners cannot be
    made to emit a claimed offer whose participant is not the claimant's.
    """

    def settled(self, **columns):
        control = self.claimed("prepare-attempt-1", "prepare-offer-1")
        sets = ", ".join(f"{name} = ?" for name in columns)
        control._connection.execute(
            f"UPDATE offers SET {sets} WHERE offer_id = ?",
            tuple(columns.values()) + ("prepare-offer-1",))
        return control

    def admitting(self, store, control):
        return capacity.admit_integration_execution(
            store, control, orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))

    def test_an_offer_settled_for_another_participant_is_refused(self):
        store, _stage, _allocation, _answer = self.registered()
        control = self.settled(participant="baton.somebody-else")
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("participant", str(caught.exception))
        self.assertIn("one identity", str(caught.exception))

    def test_an_offer_settled_under_another_authority_is_refused(self):
        store, _stage, _allocation, _answer = self.registered()
        control = self.settled(authority_uuid="f" * 32)
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("authority_uuid", str(caught.exception))

    def test_an_offer_pointed_at_another_attempt_stops_being_this_ones(self):
        """MEASURED, step 42: I wrote a comparison that cannot fail.

        `claimed_offers_for` selects WHERE `runtime_attempt_id` = the attempt,
        so an offer whose attempt is rewritten is not RETURNED -- it stops
        being this attempt's claimed offer rather than becoming a mismatched
        one, and the refusal is the exactly-one rule. The equality check I had
        added beside it could never fire, and an assertion that cannot fail is
        not an assertion; it is gone.
        """
        store, _stage, _allocation, _answer = self.registered()
        control = self.settled(runtime_attempt_id="another-attempt-1")
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("has 0 claimed offers", str(caught.exception))

    def test_an_offer_missing_a_compared_member_is_refused(self):
        """Absence is not agreement: a member that is not there compares equal
        to nothing, and reading it as a match would be the permissive
        direction."""
        store, _stage, _allocation, _answer = self.registered()
        control = self.settled(claim_generation=None)
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(store, control)
        self.assertIn("answers no", str(caught.exception))


class TheCompletionBranchDoesNotSpeakForTheExecutions(CapacityCase):
    """Finish condition 2, at the branch it names.

    `reconcile_allocations` releases an integration allocation on a VALIDATED
    COMPLETED INTEGRATION -- the one ending whose capacity never came back
    before W131187. That document is about the PARENT STAGE's own integration,
    and it says nothing whatever about a preparation execution still admitted
    under the same reservation. These cases drive that exact branch rather than
    calling `release` directly, because the branch is where the defect would
    live.
    """

    RUNTIME = "runtime-integration-1"

    def projected(self, stage, allocation, **members):
        """One stage's projection entry, exactly as `stage_states` builds it.

        The same shape `delegation.observation_of` has already bound to the
        stage, episode, attempt, claimed offer and the runtime's own fixed
        assignment; what `_completed_integration` then decides is whether the
        account belongs to THIS allocation.
        """
        document = {"schema": "baton.v12.integration-observation/1",
                    "stage_id": stage["stage_id"], "episode": stage["episode"],
                    "attempt_id": stage["attempt_id"],
                    "offer_id": stage["offer_id"],
                    "assignment": {"work_ref": {"authority_uuid": fixtures.UUID,
                                                "work_id": stage["work_id"]},
                                   "participant": allocation["participant"],
                                   "generation": 4},
                    "state": "completed",
                    "completion": {"proposal_id": "proposal-1",
                                   "integration_receipt_id": "receipt-1",
                                   "entry_id": "entry-1", "lease_id": "lease-1",
                                   "fence": 1,
                                   "handoff_operation_id": "integration-pass:x",
                                   "to_route": "integ",
                                   "runtime_id": self.RUNTIME,
                                   "execution_runtime": "quiescent"}}
        document.update(members)
        return {stage["stage_id"]: {
            "stage": {"stage_id": stage["stage_id"], "kind": "integration"},
            "state": "completed", "attempt": stage,
            "observed": {"runtime": {"execution_runtime": "quiescent",
                                     "cleanup": "pending",
                                     "runtime_id": self.RUNTIME},
                         "integration": document,
                         "start_failure": None,
                         "preparation_failure": None}}}

    def test_a_completed_parent_does_not_release_a_live_execution(self):
        """THE NAMED BRANCH, with a preparation still admitted under it. The
        parent's integration completed; the preparation it launched has not,
        and the reservation is what that preparation is running inside."""
        store, stage, allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="parent done")
        self.assertEqual(scheduler.reconcile_allocations(
            store, self.projected(stage, allocation)), [])
        # Automatic reconciliation leaves the owning continuation reachable.
        # Direct release still fails at the atomic guard.
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.release(store, allocation["assignment_id"], "parent done")
        self.assertIn("proved excluded", str(caught.exception))
        self.assertEqual(
            scheduler.allocation_of(store, allocation["assignment_id"])
            ["allocation_state"], "reserved")

    def test_the_same_branch_releases_once_after_every_member_ended(self):
        store, stage, allocation, _answer = self.registered()
        self.prepared(store)
        self.applying(store, stage)
        self.destroyed(stage["attempt_id"])
        capacity.end_integration_execution(
            store, self._control, execution_attempt_id=stage["attempt_id"],
            outcome="succeeded", exclusion="runtime-destroyed")
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="both phases")
        entry = self.projected(stage, allocation)
        moved = scheduler.reconcile_allocations(store, entry)
        self.assertEqual([one["release_reason"] for one in moved],
                         [scheduler.INTEGRATION_COMPLETED])
        # EXACTLY ONCE. The second pass sees an allocation that is no longer
        # live and moves nothing, and the root stays ended rather than being
        # ended twice.
        self.assertEqual(scheduler.reconcile_allocations(store, entry), [])
        self.assertEqual(
            capacity.integration_capacity_of(store, self.ORCHESTRATION)
            ["root"]["lifecycle"], "ended")

    def test_cleanup_and_pre_runtime_failure_wait_for_the_open_root(self):
        store, stage, allocation, _answer = self.registered()
        view = self.projected(stage, allocation)
        view[stage["stage_id"]]["state"] = "integrating"
        observed = view[stage["stage_id"]]["observed"]
        observed["runtime"]["cleanup"] = "retained"
        self.assertEqual(scheduler.reconcile_allocations(store, view), [])
        observed["runtime"]["cleanup"] = "pending"
        observed["start_failure"] = {"reason": "known failure"}
        self.assertEqual(scheduler.reconcile_allocations(store, view), [])
        self.assertEqual(scheduler.allocation_of(store, allocation["assignment_id"])["allocation_state"], "reserved")

    def test_pending_cleanup_does_not_mask_runtime_quarantine(self):
        store, stage, allocation, _answer = self.registered()
        view = self.projected(stage, allocation)
        view[stage["stage_id"]]["observed"]["runtime"].update(cleanup="retained", execution_runtime="uncertain")
        moved = scheduler.reconcile_allocations(store, view)
        self.assertEqual([one["allocation_state"] for one in moved], ["recovery-required"])
        self.assertEqual(capacity.integration_capacity_of(store, self.ORCHESTRATION)["root"]["lifecycle"], "open")

    def test_an_ended_episode_still_quarantines_its_pending_root(self):
        from baton_v12.job_manager import episodes
        store, stage, allocation, _answer = self.registered()
        episodes.end_episode(store, episodes.live_of(store, stage["stage_id"]), "declined", 1)
        view = self.projected(stage, allocation)
        view[stage["stage_id"]]["observed"]["runtime"]["cleanup"] = "failed"
        moved = scheduler.reconcile_allocations(store, view)
        self.assertEqual([one["allocation_state"] for one in moved], ["recovery-required"])

    def test_ordinary_cleanup_still_releases_without_a_registered_root(self):
        store, stage, allocation = self.reserved()
        view = self.projected(stage, allocation)
        view[stage["stage_id"]]["observed"]["runtime"]["cleanup"] = "retained"
        self.assertEqual([one["allocation_state"] for one in scheduler.reconcile_allocations(store, view)], ["released"])

    def test_the_release_still_claims_nothing_about_cleanup(self):
        """LOGICAL CAPACITY AND NOTHING ELSE, unchanged by this Work: the
        cleanup axis is exactly where it was, and no reader is told the
        container or workspace was destroyed."""
        store, stage, allocation, _answer = self.registered()
        self.prepared(store, outcome="failed")
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="failed")
        entry = self.projected(stage, allocation)
        scheduler.reconcile_allocations(store, entry)
        self.assertNotIn(
            "cleanup",
            scheduler.allocation_of(store, allocation["assignment_id"])
            ["release_reason"])
        self.assertEqual(
            entry[stage["stage_id"]]["observed"]["runtime"]["cleanup"],
            "pending")


class TheRacesUnderOneReservation(CapacityCase):
    """What holds when two acts arrive at once, and what makes it hold.

    None of these rest on a caller being careful. The serial rule is a partial
    unique index, the ending is one act that closes admission, and every
    operation is journalled under an identity that replays exactly or collides.
    """

    def test_the_serial_rule_survives_a_read_that_saw_free_capacity(self):
        """THE READ IS NOT WHAT MAKES IT SAFE.

        A competing admission that committed after this one's checks would
        leave this one looking at free capacity -- so the checks are made to
        pass against a doctored view while the relation still holds the
        preparation admitted. `capacity_one_active_member` refuses the write.
        The clean refusal above is for the ordinary case; THIS is the last line
        and it is structural, which is why the invariant does not depend on
        anybody reading first.
        """
        import sqlite3
        store, stage, _allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        live = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        stale = [dict(one, state="ended", outcome="succeeded",
                      collected_digest="sha256:" + "c" * 64)
                 if one["phase"] == "prepare" else dict(one)
                 for one in live["members"]]
        # THE PRE-READ IS DOCTORED TOO. Measured, step 155: the apply's
        # authorization reads the preparation directly before the
        # transaction, so patching only the in-transaction view left the real
        # `admitted` row refusing at the gate -- which is correct behaviour
        # and not this case's subject. Both reads see free capacity here, and
        # the relation still refuses.
        prepared = dict(
            [one for one in stale if one["phase"] == "prepare"][0])
        real_row = capacity._row

        def reading(connection, statement, operands):
            if "phase = 'prepare'" in statement:
                return prepared
            return real_row(connection, statement, operands)

        with mock.patch.object(capacity, "_members", return_value=stale), \
                mock.patch.object(capacity, "_row", reading):
            with self.assertRaises(sqlite3.IntegrityError):
                self.applying(store, stage)
        held = {one["phase"]: one for one in capacity.integration_capacity_of(
            store, self.ORCHESTRATION)["members"]}
        self.assertEqual(held["prepare"]["state"], "admitted")
        self.assertEqual(held["apply"]["state"], "planned")

    def test_an_admission_racing_an_ending_is_refused_by_the_ending(self):
        """`begin_integration_ending` is ONE act that closes admission, so
        there is no window in which a root is ending and still admitting."""
        store, _stage, _allocation, _answer = self.registered()
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="stand down")
        with self.assertRaises(ContractRefusal) as caught:
            self.admit("prepare", "prepare-attempt-1", "prepare-offer-1",
                       store)
        self.assertIn("admission is closed", str(caught.exception))

    def test_an_ending_never_cancels_an_execution_that_was_admitted(self):
        """The other order. Closing admission is not a claim that anything
        stopped: an admitted execution is ended by its own evidence, and only a
        plan that never ran is cancelled."""
        store, _stage, allocation, _answer = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        answer = capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="stand down")
        held = {one["phase"]: one for one in answer["members"]}
        self.assertEqual(held["prepare"]["state"], "admitted")
        self.assertEqual(held["apply"]["state"], "cancelled")
        with self.assertRaises(ContractRefusal):
            scheduler.release(store, allocation["assignment_id"],
                              "cleanup-complete")

    def test_a_duplicate_release_does_not_release_twice(self):
        store, _stage, allocation, _answer = self.registered()
        self.prepared(store, outcome="failed")
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="done")
        first = scheduler.release(store, allocation["assignment_id"],
                                  scheduler.INTEGRATION_COMPLETED)
        again = scheduler.release(store, allocation["assignment_id"],
                                  scheduler.INTEGRATION_COMPLETED)
        # THE EXACT OPERATION REPLAYS its first answer rather than running a
        # second release, which is what keeps a retry from being an act.
        self.assertEqual(again, first)
        self.assertEqual(again["allocation_state"], "released")

    def test_an_exact_repeat_replays_and_changed_operands_collide(self):
        """Every operation here is journalled under an identity derived from
        what it is about, so a retry of the SAME act replays and a different
        act wearing the same identity is refused rather than performed."""
        store, _stage, _allocation, _answer = self.registered()
        first = self.admit("prepare", "prepare-attempt-1", "prepare-offer-1",
                           store)
        # THE SAME CLAIM, not a second one. `issue_offer` refuses to reissue an
        # offer it already minted a bearer for (measured, step 45), which is
        # the Worker Manager saying the same thing this case is about.
        repeated = capacity.admit_integration_execution(
            store, self.control(), orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))
        self.assertEqual(repeated, first)
        self.destroyed("prepare-attempt-1")
        ended = capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome="failed", exclusion="runtime-destroyed")
        self.assertEqual(
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="failed",
                exclusion="runtime-destroyed"),
            ended)
        with self.assertRaises(ContractRefusal) as caught:
            capacity.end_integration_execution(
                store, self._control,
                execution_attempt_id="prepare-attempt-1", outcome="succeeded",
                exclusion="runtime-destroyed")
        self.assertEqual(caught.exception.code, "operation-collision")


class TwoStoresContendForOneReservation(CapacityCase):
    """[P2] Review 2026-09-13T18:02:07Z: the earlier cases were ORDERS, not races.

    They established both sequential orders, sequential replay and a unique
    index under a patched occupancy view -- all worth keeping, and none of them
    a competing transaction. These drive TWO JobStore connections on one file,
    each taking its own `BEGIN IMMEDIATE` write transaction, so the contention
    is the store's own rather than a mock's.

    WHAT IS CONTROLLED IS THE INTERLEAVE, NOT THE OUTCOME. Each case takes the
    loser's read BEFORE the winner commits -- which is the whole hazard: a
    caller that decided against a view SQLite has already moved past. Every
    check that matters runs inside `perform`, under the loser's own lock, so
    what it sees is the committed world and not the view it started from. Both
    allowed outcomes are asserted where both are allowed: a DIFFERENT act
    refuses, an IDENTICAL one replays, and either way the relation holds one
    account.
    """

    def beside(self, store):
        """A second connection to the SAME Job store file."""
        from baton_v12.job_manager import JobStore
        second = JobStore.open(self.job_path, authority_uuid=fixtures.UUID,
                               incarnation="jobs-2", clock=self.clock)
        self.addCleanup(second.close)
        # THE STALE READ, taken before the other connection commits anything.
        self.stale = capacity.integration_capacity_of(second,
                                                      self.ORCHESTRATION)
        return second

    def members_of(self, store):
        return {one["phase"]: one for one in
                capacity.integration_capacity_of(
                    store, self.ORCHESTRATION)["members"]}

    def test_a_competing_admission_from_another_connection_is_refused(self):
        store, stage, _allocation, _answer = self.registered()
        second = self.beside(store)
        self.assertEqual(self.stale["members"][0]["state"], "planned")
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        # The second connection decided against a world in which nothing was
        # admitted. Its own transaction sees otherwise.
        self.claimed(stage["attempt_id"], stage["offer_id"],
                     work_id=stage["work_id"])
        coordinator = self.coordinated()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.admit_integration_execution(
                second, self._control, orchestration_id=self.ORCHESTRATION,
                phase="apply", execution_attempt_id=stage["attempt_id"],
                assignment=self.claim_of(stage["attempt_id"]),
                coordinator=coordinator, authorization=self.authorization,
                grant=self.grant)
        self.assertIn("ended successfully", str(caught.exception))
        held = self.members_of(second)
        self.assertEqual(held["prepare"]["state"], "admitted")
        self.assertEqual(held["apply"]["state"], "planned")

    def test_the_identical_admission_from_another_connection_replays(self):
        """THE OTHER ALLOWED OUTCOME. Two connections attempting the SAME act
        is not a conflict to refuse: the operation identity is derived from
        what the act is about, so the loser replays the winner's recorded
        answer and the relation carries one account, not two."""
        store, _stage, _allocation, _answer = self.registered()
        second = self.beside(store)
        first = self.admit("prepare", "prepare-attempt-1", "prepare-offer-1",
                           store)
        again = capacity.admit_integration_execution(
            second, self._control, orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))
        self.assertEqual(again, first)
        self.assertEqual(
            store._connection.execute(
                "SELECT count(*) FROM operations WHERE operation_id = ?",
                ("integration-capacity.admit:prepare-attempt-1",)).fetchone()[0],
            1)

    def test_an_admission_that_lost_to_an_ending_is_refused(self):
        store, _stage, _allocation, _answer = self.registered()
        second = self.beside(store)
        self.assertEqual(self.stale["root"]["lifecycle"], "open")
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="stand down")
        with self.assertRaises(ContractRefusal) as caught:
            capacity.admit_integration_execution(
                second, self.claimed("prepare-attempt-1", "prepare-offer-1"),
                orchestration_id=self.ORCHESTRATION, phase="prepare",
                execution_attempt_id="prepare-attempt-1",
                assignment=self.claim_of("prepare-attempt-1"))
        self.assertIn("admission is closed", str(caught.exception))
        self.assertEqual(self.members_of(second)["prepare"]["state"],
                         "cancelled")

    def test_an_ending_that_lost_to_an_admission_cancels_nothing(self):
        """The other direction, and the asymmetry is the point: an ending that
        arrives after an admission commits does not cancel the admitted
        execution, because closing admission is not a claim that anything
        stopped."""
        store, _stage, _allocation, _answer = self.registered()
        second = self.beside(store)
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        answer = capacity.begin_integration_ending(
            second, orchestration_id=self.ORCHESTRATION, reason="stand down")
        held = {one["phase"]: one for one in answer["members"]}
        self.assertEqual(held["prepare"]["state"], "admitted")
        self.assertEqual(held["apply"]["state"], "cancelled")

    def test_two_connections_releasing_settle_on_one_release(self):
        store, _stage, allocation, _answer = self.registered()
        self.prepared(store, outcome="failed")
        second = self.beside(store)
        capacity.begin_integration_ending(
            store, orchestration_id=self.ORCHESTRATION, reason="done")
        first = scheduler.release(store, allocation["assignment_id"],
                                  scheduler.INTEGRATION_COMPLETED)
        again = scheduler.release(second, allocation["assignment_id"],
                                  scheduler.INTEGRATION_COMPLETED)
        self.assertEqual(again, first)
        self.assertEqual(
            scheduler.allocation_of(second, allocation["assignment_id"])
            ["allocation_state"], "released")

    def test_a_second_connection_waits_for_the_write_lock(self):
        """THE CONTENTION ITSELF, deterministically ordered.

        One connection holds `BEGIN IMMEDIATE` while a thread on the other
        attempts its own write. SQLite serializes them -- the waiter blocks
        until the holder commits and then runs its checks against the
        committed world. The point is not which one wins: it is that neither
        runs its checks against a world the other has already changed.
        """
        import threading
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        store, _stage, _allocation, _answer = self.registered()
        self.claimed("prepare-attempt-1", "prepare-offer-1")
        assignment = self.claim_of("prepare-attempt-1")
        started, done = threading.Event(), []

        def admitting():
            # MEASURED, step 53: a SQLite connection belongs to the thread
            # that opened it, so the contender opens its own -- which is the
            # truer fixture anyway. Two processes contending would each have
            # their own handles too.
            mine = JobStore.open(self.job_path, authority_uuid=fixtures.UUID,
                                 incarnation="jobs-2", clock=self.clock)
            control = ControlStore.open(self.control_path,
                                        incarnation="manager-2",
                                        clock=self.clock)
            started.set()
            try:
                done.append(capacity.admit_integration_execution(
                    mine, control, orchestration_id=self.ORCHESTRATION,
                    phase="prepare",
                    execution_attempt_id="prepare-attempt-1",
                    assignment=assignment))
            except BaseException as raised:            # pragma: no cover
                done.append(raised)
            finally:
                mine.close()
                control.close()

        store._connection.execute("BEGIN IMMEDIATE")
        waiter = threading.Thread(target=admitting)
        waiter.start()
        started.wait(timeout=5)
        # THE WAITER IS BLOCKED ON THE LOCK THIS CONNECTION HOLDS, and the
        # relation still says `planned` because nothing has committed.
        self.assertEqual(
            store._connection.execute(
                "SELECT state FROM integration_capacity_members "
                "WHERE execution_attempt_id = ?",
                ("prepare-attempt-1",)).fetchone()[0], "planned")
        store._connection.execute("ROLLBACK")
        waiter.join(timeout=10)
        self.assertFalse(waiter.is_alive())
        self.assertEqual(len(done), 1)
        self.assertNotIsInstance(done[0], BaseException)
        self.assertEqual(self.members_of(store)["prepare"]["state"],
                         "admitted")


class TheApplyBringsItsGrantAndItsAuthorization(CapacityCase):
    """The last two facts the accepted design names for an apply.

    "apply requires collected successful preparation, its closed execution
    membership, and the actual authorized derived candidate/grant." The
    preparation and the membership were proved; these two were not -- and an
    admission that proves two of three is an admission that lets the third
    through.

    The authorization is asked of an OWNER rather than read from a caller's
    document, and the grant is read from the coordinator, because a lease id
    with a fence is a value a caller can repeat.
    """

    def ready(self):
        store, stage, _allocation, _answer = self.registered()
        self.prepared(store)
        # THE COORDINATOR IS COMPOSED HERE so a case can vary the owner's
        # answer or the grant before the admission reaches them.
        self.coordinated()
        return store, stage

    def test_an_apply_is_admitted_with_both(self):
        store, stage = self.ready()
        answer = self.applying(store, stage)
        held = {one["phase"]: one for one in answer["members"]}["apply"]
        self.assertEqual(held["state"], "admitted")
        # THE OWNER WAS ASKED, about this orchestration, this target and the
        # content the preparation actually collected.
        asked = self.authorization.asked[-1]
        self.assertEqual(asked["managed_result_id"], self.ORCHESTRATION)
        self.assertEqual(asked["canonical_target_id"],
                         self.grant["canonical_target_id"])
        self.assertEqual(
            asked["content_digest"],
            {one["phase"]: one
             for one in answer["members"]}["prepare"]["collected_digest"])

    def test_an_apply_without_its_grant_is_refused(self):
        store, stage = self.ready()
        for member in ("coordinator", "authorization", "grant"):
            with self.subTest(absent=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.applying(store, stage, **{member: None})
                self.assertIn("carries no", str(caught.exception))
                self.assertIn(member, str(caught.exception))

    def test_a_preparation_carrying_a_grant_is_refused(self):
        """A preparation writes no target, and capability it has no use for is
        capability nobody should hold."""
        store, _stage, _allocation, _answer = self.registered()
        control = self.claimed("prepare-attempt-1", "prepare-offer-1")
        self.coordinated()
        with self.assertRaises(ContractRefusal) as caught:
            capacity.admit_integration_execution(
                store, control, orchestration_id=self.ORCHESTRATION,
                phase="prepare", execution_attempt_id="prepare-attempt-1",
                assignment=self.claim_of("prepare-attempt-1"),
                grant=self.grant)
        self.assertIn("writes no target", str(caught.exception))

    def test_an_unapproved_candidate_is_refused(self):
        store, stage = self.ready()
        self.authorization.answer["approved"] = False
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertIn("somebody independently authorized",
                      str(caught.exception))

    def test_an_unavailable_authorization_owner_is_refused(self):
        store, stage = self.ready()
        self.authorization.absent = True
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertIn("an unavailable owner refuses an admission",
                      str(caught.exception))

    def test_an_authorization_about_other_content_is_refused(self):
        store, stage = self.ready()
        self.authorization.answer["content_digest"] = "sha256:" + "9" * 64
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertIn("the authorization names content_digest",
                      str(caught.exception))

    def test_a_grant_this_coordinator_does_not_hold_is_refused(self):
        store, stage = self.ready()
        for member, wrong in (("lease_id", "lease-somebody-elses"),
                              ("fence", self.grant["fence"] + 7),
                              ("entry_id", "entry-elsewhere")):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal):
                    self.applying(store, stage,
                                  grant=dict(self.grant, **{member: wrong}))

    def test_a_released_grant_refuses_the_admission(self):
        """The grant is read at the moment of admission, not presented."""
        from baton_v12.integration import refuse_entry
        store, stage = self.ready()
        coordinator = self.coordinated()
        refuse_entry(coordinator, lease_id="lease-1",
                     canonical_target_id=self.grant["canonical_target_id"],
                     entry_id="entry-1", fence=self.grant["fence"],
                     settlement={"reason": "policy",
                                 "detail": {"why": "withdrawn"}})
        with self.assertRaises(ContractRefusal):
            self.applying(store, stage)

    def test_an_admission_under_another_grant_collides(self):
        """The grant rides the signature, so an admission under a different
        one is a different act rather than a replay of this one."""
        store, stage = self.ready()
        first = self.applying(store, stage)
        self.assertEqual(self.applying(store, stage), first)
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage,
                          grant=dict(self.grant, entry_id="entry-other"))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_the_grant_is_proved_after_the_authorization_owner_is_asked(self):
        """[P1] Review 2026-09-14T00:55:37Z: asking the owner is a call that
        can change the world, and your probe released this very lease from
        inside one. The admission committed anyway, because the grant had been
        proved before that call."""
        from baton_v12.integration import refuse_entry
        store, stage = self.ready()
        coordinator = self.coordinated()
        real = self.authorization.authorized

        def ending(operands):
            refuse_entry(coordinator, lease_id="lease-1",
                         canonical_target_id=self.grant["canonical_target_id"],
                         entry_id="entry-1", fence=self.grant["fence"],
                         settlement={"reason": "policy",
                                     "detail": {"why": "withdrawn"}})
            return real(operands)

        self.authorization.authorized = ending
        with self.assertRaises(ContractRefusal):
            self.applying(store, stage)
        # THE MEMBER WAS NOT ADMITTED.
        held = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        self.assertEqual({one["phase"]: one["state"]
                          for one in held["members"]}["apply"], "planned")

    def test_the_authorized_candidate_is_retained(self):
        store, stage = self.ready()
        answer = self.applying(store, stage)
        held = {one["phase"]: one for one in answer["members"]}["apply"]
        self.assertEqual(held["authorized_proposal_id"], "derived-proposal-1")
        self.assertEqual(held["authorized_result_id"], "derived-result-1")
        self.assertEqual(held["authorized_result_digest"],
                         "sha256:" + "e" * 64)
        # AND A PREPARATION CARRIES NONE, because it has no candidate.
        prepared = {one["phase"]: one for one in answer["members"]}["prepare"]
        self.assertIsNone(prepared["authorized_proposal_id"])

    def test_a_retry_over_another_candidate_collides(self):
        """[P1] The identity signed the grant and not the candidate, so an
        exact retry naming another approved candidate replayed the first
        answer WITHOUT ASKING THE OWNER -- and the journal held no record of
        which candidate had been approved."""
        store, stage = self.ready()
        first = self.applying(store, stage)
        asked = len(self.authorization.asked)
        self.assertEqual(self.applying(store, stage), first)
        self.authorization.answer["derived_proposal_id"] = "derived-other"
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertEqual(caught.exception.code, "operation-collision")
        # AND THE OWNER WAS ASKED EACH TIME: a replay of an identity is not a
        # reason to skip the question its operands are about.
        self.assertGreater(len(self.authorization.asked), asked)

    def test_a_malformed_grant_never_reaches_an_identity(self):
        store, stage = self.ready()
        for grant in ({"canonical_target_id": "target:x"},
                      dict(self.grant, fence=0),
                      dict(self.grant, fence=True),
                      dict(self.grant, lease_id=7)):
            with self.subTest(grant=sorted(grant)):
                with self.assertRaises(ContractRefusal):
                    self.applying(store, stage, grant=grant)
                self.assertEqual(
                    {one["phase"]: one["state"] for one in
                     capacity.integration_capacity_of(
                         store, self.ORCHESTRATION)["members"]}["apply"],
                    "planned")

    def test_collected_content_moving_between_the_two_reads_refuses(self):
        """The owner is asked outside the transaction and the authoritative
        read is inside it. A preparation whose collected content moved in
        between is a different apply."""
        store, stage = self.ready()
        real = self.authorization.authorized

        def moving(operands):
            answer = real(operands)
            store._connection.execute(
                "UPDATE integration_capacity_members SET collected_digest = ? "
                "WHERE phase = 'prepare'", ("sha256:" + "7" * 64,))
            return answer

        self.authorization.authorized = moving
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertIn("the authorization was asked about",
                      str(caught.exception))

    def test_a_retry_after_the_collected_content_changed_collides(self):
        """[P2] The identity carried the candidate and not the content it was
        approved OVER, so a retry after the preparation's collected digest
        changed asked the owner about the NEW content and then replayed the
        ORIGINAL admission -- `transact` answers a committed identity without
        running the action, so the in-transaction comparison never ran.

        The fault is applied to a persisted row directly. No public act
        rewrites a completed preparation's collected content, and this case
        does not claim one does: what it establishes is that the durable
        identity is about the content too, so the replay cannot stand in for
        the check.
        """
        store, stage = self.ready()
        first = self.applying(store, stage)
        self.assertEqual(self.applying(store, stage), first)
        store._connection.execute(
            "UPDATE integration_capacity_members SET collected_digest = ? "
            "WHERE phase = 'prepare'", ("sha256:" + "7" * 64,))
        with self.assertRaises(ContractRefusal) as caught:
            self.applying(store, stage)
        self.assertEqual(caught.exception.code, "operation-collision")
        # AND THE OWNER WAS ASKED ABOUT THE NEW CONTENT, which is what made
        # the old identity the wrong answer to hand back.
        self.assertEqual(self.authorization.asked[-1]["content_digest"],
                         "sha256:" + "7" * 64)

    def test_an_unchanged_admission_still_replays(self):
        """The correction does not make an ordinary retry into a collision."""
        store, stage = self.ready()
        first = self.applying(store, stage)
        self.assertEqual(self.applying(store, stage), first)
        self.assertEqual(self.applying(store, stage), first)


class ADecisionIsJournalledBeforeTheWorkExists(CapacityCase):
    """Slice2 step 1: the intent that precedes a child Work.

    Creating a Work is an act at ANOTHER store, and the window between
    deciding to create one and learning that it exists is exactly where a
    crash loses track of it. The decision is committed here first, carrying
    the operation identity `Authority.create_work` will be called with -- so
    an interrupted creation is resumed rather than repeated, and a restart
    finds the Work its own intent named instead of minting a second one.
    """

    def intended(self, store, stage, allocation, **changed):
        held = {"orchestration_id": self.ORCHESTRATION,
                "root_assignment_id": allocation["assignment_id"],
                "authority_uuid": fixtures.UUID,
                "request": self.request(),
                "execution_work_id": self.EXECUTION_WORK,
                "execution_route": "baton.impl",
                "plan": self.plan(stage)}
        held.update(changed)
        return capacity.record_preparation_intent(store, **held)

    def prepared_intent(self):
        store, stage, allocation = self.reserved()
        self.claimed("prepare-attempt-1", "prepare-offer-1")
        return store, stage, allocation

    def test_an_intent_binds_the_parent_from_the_stores_own_rows(self):
        store, stage, allocation = self.prepared_intent()
        held = self.intended(store, stage, allocation)
        self.assertEqual(sorted(held),
                         sorted(capacity.PREPARATION_INTENT_MEMBERS))
        parent = held["parent"]
        self.assertEqual(parent["stage_id"], stage["stage_id"])
        self.assertEqual(parent["attempt_id"], stage["attempt_id"])
        self.assertEqual(parent["offer_id"], stage["offer_id"])
        self.assertEqual(parent["work_id"], stage["work_id"])
        self.assertEqual(parent["participant"], allocation["participant"])
        self.assertEqual(parent["canonical_principal"],
                         allocation["canonical_principal"])
        self.assertEqual(parent["pool_generation"], allocation["generation"])

    def test_the_creation_identity_is_decided_here(self):
        """`Authority.create_work` takes an explicit operation id, so an
        interrupted creation replays instead of minting a second Work."""
        store, stage, allocation = self.prepared_intent()
        held = self.intended(store, stage, allocation)
        self.assertEqual(held["work_operation_id"],
                         "integration-preparation.create-work:"
                         + self.ORCHESTRATION)
        self.assertEqual(held["execution_work_id"], self.EXECUTION_WORK)
        self.assertEqual(held["request_digest"],
                         managed.request_digest(self.request()))

    def test_an_exact_repeat_replays_and_a_changed_request_collides(self):
        store, stage, allocation = self.prepared_intent()
        first = self.intended(store, stage, allocation)
        self.assertEqual(self.intended(store, stage, allocation), first)
        with self.assertRaises(ContractRefusal) as caught:
            self.intended(store, stage, allocation,
                          request=self.request(
                              source={"base": "b" * 40, "candidate": "c" * 40,
                                      "target_revision": "d" * 40}))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_changed_route_or_work_collides(self):
        for member, wrong in (("execution_route", "baton.other"),
                              ("execution_work_id", "00000000-W9")):
            with self.subTest(member=member):
                case = type(self)(self._testMethodName)
                case.setUp()
                store, stage, allocation = case.prepared_intent()
                case.intended(store, stage, allocation)
                with self.assertRaises(ContractRefusal) as caught:
                    if member == "execution_work_id":
                        case.intended(
                            store, stage, allocation,
                            execution_work_id=wrong,
                            plan=case.plan(stage, prepare={
                                "execution_work_id": wrong}),
                            request=case.request())
                    else:
                        case.intended(store, stage, allocation,
                                      **{member: wrong})
                self.assertEqual(caught.exception.code, "operation-collision")
                case.doCleanups()

    def test_a_plan_that_disagrees_with_the_request_is_refused(self):
        store, stage, allocation = self.prepared_intent()
        for member in ("profile_digest",):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.intended(store, stage, allocation,
                                  plan=self.plan(stage, prepare={
                                      member: "sha256:" + "f" * 64}))
                self.assertIn("and the request names", str(caught.exception))

    def test_manifest_identity_is_distinct_from_published_source_content(self):
        store, stage, allocation = self.prepared_intent()
        manifest = "sha256:" + "f" * 64
        answer = self.intended(store, stage, allocation,
                               plan=self.plan(stage, prepare={"input_digest": manifest}))
        self.assertEqual(answer["plan"][0]["input_digest"], manifest)
        self.assertNotEqual(manifest, self.request()["input_digest"])
        # Admission's existing mismatched-offer tests still require the actual
        # offer/attempt to match this planned manifest.

    def test_an_intent_for_a_reservation_nobody_holds_is_refused(self):
        store, stage, _allocation = self.prepared_intent()
        with self.assertRaises(ContractRefusal) as caught:
            self.intended(store, stage, {"assignment_id": "attempt-nobody"})
        self.assertIn("has no allocation", str(caught.exception))

    def test_a_released_reservation_is_refused(self):
        store, stage, allocation = self.prepared_intent()
        scheduler.release(store, allocation["assignment_id"],
                          "cleanup-complete")
        with self.assertRaises(ContractRefusal) as caught:
            self.intended(store, stage, allocation)
        self.assertIn("accounts capacity that is actually held",
                      str(caught.exception))

    def test_a_foreign_authority_is_refused(self):
        store, stage, allocation = self.prepared_intent()
        with self.assertRaises(ContractRefusal) as caught:
            self.intended(store, stage, allocation, authority_uuid="f" * 32)
        self.assertIn("this Job store is bound to Authority",
                      str(caught.exception))

    def test_a_request_for_another_orchestration_is_refused(self):
        store, stage, allocation = self.prepared_intent()
        with self.assertRaises(ContractRefusal) as caught:
            self.intended(store, stage, allocation,
                          request=self.request(
                              orchestration_id="integration-capacity-2"))
        self.assertIn("this request is for orchestration",
                      str(caught.exception))

    def test_absence_is_an_ordinary_answer(self):
        store, stage, allocation = self.prepared_intent()
        self.assertIsNone(capacity.preparation_intent_of(store,
                                                         self.ORCHESTRATION))
        self.intended(store, stage, allocation)
        self.assertEqual(
            capacity.preparation_intent_of(store, self.ORCHESTRATION)
            ["execution_work_id"], self.EXECUTION_WORK)

    def test_a_recorded_intent_whose_halves_disagree_is_refused(self):
        store, stage, allocation = self.prepared_intent()
        self.intended(store, stage, allocation)
        store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps({"orchestration_id": "somebody-elses"}),
             "integration-capacity.intent:" + self.ORCHESTRATION))
        with self.assertRaises(ContractRefusal) as caught:
            capacity.preparation_intent_of(store, self.ORCHESTRATION)
        self.assertIn("its own operands do not produce", str(caught.exception))

    def test_registration_binds_the_decision_already_made(self):
        store, stage, allocation = self.prepared_intent()
        self.intended(store, stage, allocation)
        answer = capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=fixtures.UUID, plan=self.plan(stage))
        self.assertEqual([one["phase"] for one in answer["members"]],
                         ["apply", "prepare"])

    def test_registering_a_different_plan_than_was_decided_is_refused(self):
        store, stage, allocation = self.prepared_intent()
        self.intended(store, stage, allocation)
        with self.assertRaises(ContractRefusal) as caught:
            capacity.register_integration_capacity(
                store, orchestration_id=self.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                authority_uuid=fixtures.UUID,
                plan=self.plan(stage,
                               prepare={"task_digest": "sha256:" + "f" * 64}))
        self.assertIn("committed a different plan", str(caught.exception))

    def test_an_orchestration_with_no_intent_still_registers(self):
        """The slice1 shape stays legal: registration never required an
        intent, and refusing here would break capacity that never had a
        preparation to decide on."""
        store, stage, allocation = self.prepared_intent()
        self.assertIsNone(capacity.preparation_intent_of(store,
                                                         self.ORCHESTRATION))
        answer = capacity.register_integration_capacity(
            store, orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=fixtures.UUID, plan=self.plan(stage))
        self.assertEqual(answer["root"]["lifecycle"], "open")


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()


class TheStartIsBehindTheAdmission(ADecisionIsJournalledBeforeTheWorkExists):
    """W161230 CHECKPOINT A.3 -- the ORDER `PreparationExecution` exists for.

    Every step it composes is an existing owned operation. What the class
    contributes is the sequence, so what is worth proving is that the sequence
    cannot be walked past: a runtime start is behind capacity admission, and
    capacity admission is behind a committed decision.

    These drive the REAL readers -- `preparation_intent_of` and
    `integration_capacity_of` -- over a real store, so what refuses a start is
    what the store says rather than what the object remembers.
    """

    def execution(self, store):
        import sys
        import os as _os

        sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__)))))
        from tools.integration_worker import PreparationExecution

        return PreparationExecution(
            jobs=store, manager=self.control(), control=self.control(),
            authority=None, port=None, mint_bearer=None)

    def test_a_start_without_a_decision_refuses(self):
        """An orchestration with no intent has decided nothing, whatever Work
        happens to exist elsewhere."""
        store, stage, allocation = self.reserved()
        execution = self.execution(store)
        with self.assertRaises(ContractRefusal) as caught:
            execution.start(self.ORCHESTRATION, "prepare-attempt-1",
                            lambda: "started")
        self.assertIn("decided no preparation", str(caught.exception))
        self.assertEqual(execution.started, [])

    def test_a_start_before_admission_refuses(self):
        """CAPACITY IS THE GATE. An intent decides; it does not admit, and
        starting on the strength of one would leave a runtime nobody
        accounted for."""
        store, stage, allocation, answer = self.registered()
        execution = self.execution(store)
        execution.decide(
            orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            request=self.request(), plan=self.plan(stage),
            execution_work_id=self.EXECUTION_WORK,
            execution_route="integration-preparation")
        # THE DECISION IS COMMITTED AND THE START IS STILL REFUSED.
        self.assertIsNotNone(
            capacity.preparation_intent_of(store, self.ORCHESTRATION))
        with self.assertRaises(ContractRefusal) as caught:
            execution.start(self.ORCHESTRATION, "prepare-attempt-1",
                            lambda: "started")
        self.assertIn("has not been admitted", str(caught.exception))
        self.assertEqual(execution.started, [])

    def test_a_start_after_admission_proceeds(self):
        """And the reversal: once capacity has admitted the member, the
        ordinary launch happens -- so the refusal above means something."""
        store, stage, allocation, answer = self.registered()
        execution = self.execution(store)
        execution.decide(
            orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            request=self.request(), plan=self.plan(stage),
            execution_work_id=self.EXECUTION_WORK,
            execution_route="integration-preparation")
        capacity.admit_integration_execution(
            store, self.control(), orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))
        self.assertEqual(
            execution.start(self.ORCHESTRATION, "prepare-attempt-1",
                            lambda: "started"), "started")
        self.assertEqual(execution.started, ["prepare-attempt-1"])

    def test_the_admitted_member_is_read_from_the_store_not_remembered(self):
        """A composition that trusted its own bookkeeping would authorise a
        start against a member the store never recorded."""
        store, stage, allocation, answer = self.registered()
        execution = self.execution(store)
        execution.decide(
            orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            request=self.request(), plan=self.plan(stage),
            execution_work_id=self.EXECUTION_WORK,
            execution_route="integration-preparation")
        capacity.admit_integration_execution(
            store, self.control(), orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))
        # A DIFFERENT ATTEMPT IS NOT THIS ADMISSION.
        with self.assertRaises(ContractRefusal):
            execution.start(self.ORCHESTRATION, "some-other-attempt",
                            lambda: "started")

    def test_the_parent_offer_is_not_settled_by_preparing(self):
        """The same actor holds the parent while it prepares, so the root must
        still be held when the preparation is admitted. A composition that
        settled the parent here would hand the root back while its own
        preparation was still running on it."""
        store, stage, allocation, answer = self.registered()
        execution = self.execution(store)
        execution.decide(
            orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            request=self.request(), plan=self.plan(stage),
            execution_work_id=self.EXECUTION_WORK,
            execution_route="integration-preparation")
        capacity.admit_integration_execution(
            store, self.control(), orchestration_id=self.ORCHESTRATION,
            phase="prepare", execution_attempt_id="prepare-attempt-1",
            assignment=self.claim_of("prepare-attempt-1"))
        held = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        # THE ONE RESERVED ROOT, still the parent's own allocation.
        self.assertEqual(held["root"]["root_assignment_id"],
                         allocation["assignment_id"])
        # AND EXACTLY ONE PREPARATION MEMBER -- no second actor or allocation.
        prepared = [one for one in held["members"]
                    if one["phase"] == "prepare"]
        self.assertEqual(len(prepared), 1)
        self.assertEqual(prepared[0]["execution_attempt_id"],
                         "prepare-attempt-1")


class ThePreparationIsCoordinatedEndToEnd(CapacityCase):
    """W161230 CHECKPOINT A.3 -- `prepare` run against real owners.

    EVERY OWNER IN THIS PATH IS THE REAL ONE, and the previous intermediate
    label is withdrawn. The Authority is a disposable `Authority.create`; the
    child Work is created at it under the intent's own operation id; the
    participant session is MINTED by that same Authority; the Worker Manager's
    port is the DEPLOYMENT'S OWN composition over it -- `integration_worker`
    `authority_port`, which is what `single_worker._compose_one` builds in
    production -- carrying the authority's real `claim_signature`; and the
    offer, its acceptance, the recorded attempt, the claim, the activation,
    the assignment read-back and the capacity admission are all the ordinary
    acts.

    THE BLOCKER I REPORTED AT M168341 WAS WRONG AND IS SUPERSEDED. It is true
    that a BARE `authority.Session` carries no `publish_answer` and that a port
    over it refuses; the inference that no real-Authority-backed port could be
    built was false, because the deployment already supplies the adapter that
    closes exactly that gap with an explicit capability refusal. The true part
    of the fact is kept as `test_a_bare_session_is_not_a_port_and_the_adapter_
    is_why` rather than as a reason for a fake, and it no longer requires a
    missing capability to stay missing.

    WHAT A REAL AUTHORITY CHANGES ABOUT THE FIXTURE, named because it is a
    product fact rather than a test detail: a PRINCIPAL HOLDS ONE LIVE CLAIM at
    a time across every address it acts through. The shared fixture's
    pre-claimed `prepare-attempt-1` would spend the actor's only slot, so this
    case builds the owners without claiming and lets the preparation take it --
    which is the honest shape anyway, since this is the case that makes the
    claim rather than one that is handed one.

    No engine, model or image is involved, and nothing fabricates a Work id,
    an offer, a claim receipt or an assignment.
    """

    # THE ROUTE THE CHILD WORK IS CREATED ON, and the one the actor is
    # configured to handle. Registering a handler is a DEPLOYMENT act -- it is
    # who may be given this kind of work -- so the fixture does it and the
    # coordinator does not.
    CHILD_ROUTE = "integration-preparation"

    # AND THE CONTRACT THE CHILD WORK IS CREATED UNDER. The manager's port
    # owns a CLOSED claim result -- an assignment, the authority's own
    # immutable claim event and its authorization decision -- and a v11
    # assignment tuple mints no such event. So the operand exists, and this is
    # what it is for.
    CONTRACT = _authority_contract()

    def test_a_bare_session_is_not_a_port_and_the_adapter_is_why(self):
        """THE TRUE HALF OF THE SUPERSEDED BLOCKER, kept as a boundary fact.

        `AuthorityPort` requires the whole of `SESSION_OPERATIONS`, and a bare
        `baton_v12.authority.Session` implements every one of them EXCEPT
        `publish_answer`, which is required rather than one of the
        `OPTIONAL_SESSION_OPERATIONS`. So the port refuses a bare session --
        and that is a statement about the ADAPTER being load-bearing, not about
        a capability anybody is waiting for.

        The deployment's adapter closes it by REFUSING the operation explicitly
        rather than by answering a successful-looking no-op, which is the
        difference between "this deployment runs no inquiry sessions" and "this
        deployment silently drops conversational answers". Both halves are
        asserted here, so neither can rot into the other.
        """
        from baton_v12.authority.session import Session
        from baton_v12.worker_manager import AuthorityPort
        from baton_v12.worker_manager.authority_port import (
            OPTIONAL_SESSION_OPERATIONS, SESSION_OPERATIONS)

        bare = self.authority().session(self.ACTOR)
        self.assertIsInstance(bare, Session)
        self.assertEqual([one for one in SESSION_OPERATIONS
                          if getattr(bare, one, None) is None],
                         ["publish_answer"])
        self.assertNotIn("publish_answer", OPTIONAL_SESSION_OPERATIONS)
        with self.assertRaises(ContractRefusal) as caught:
            AuthorityPort(bare, fixtures.fake_claim_signature)
        self.assertIn("publish_answer", str(caught.exception))
        # AND THE ADAPTER THE DEPLOYMENT ACTUALLY USES CONSTRUCTS, with the
        # one member it adds being a refusal rather than an answer.
        adapted = self.adapted(bare)
        AuthorityPort(adapted, self.signature())
        with self.assertRaises(ContractRefusal) as refused:
            adapted.publish_answer({})
        self.assertEqual(refused.exception.code, "capability")

    def test_the_port_is_bound_to_the_authoritys_own_participant(self):
        """The manager supplies no claimant: the session takes it from its
        BINDING. So the port this fixture hands the composition acts for the
        configured integration actor and for nobody else."""
        self.owners()
        self.assertEqual(self.port.participant, self.ACTOR)

    def signature(self):
        """THE AUTHORITY'S OWN derivation of claim identity, consumed rather
        than recomputed -- the port's whole reason for taking it by injection.
        """
        from baton_v12.authority import claim_signature

        return claim_signature

    def adapted(self, minted):
        """The deployment's own session adapter, reused rather than restated.

        `integration_worker.authority_port` composes it, and that function is
        what production `single_worker._compose_one` already composes: one
        minted session, the manager's narrow view of it, the real signature. A
        second adapter written here would be a second account of a capability
        this deployment already decides.
        """
        return self.composition().manager_session(minted)

    def composition(self):
        import os as _os
        import sys as _sys

        _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__)))))
        from tools import integration_worker

        return integration_worker

    def participant_session(self):
        """MINTED BY THE AUTHORITY, never constructed. The fake is gone."""
        return self.authority().session(self.ACTOR)

    def worker_port(self):
        """The deployment's own port composition, over that minted session."""
        return self.composition().authority_port(self.authority(), self.ACTOR)

    def preclaimed(self):
        """NOTHING IS PRE-CLAIMED HERE, and the refusal that proves why is
        asserted rather than assumed -- see
        `test_the_actor_holds_one_live_claim_and_the_preparation_takes_it`."""
        return self.owners()

    def authority(self):
        held = getattr(self, "_authority", None)
        if held is None:
            import os as _os

            from baton_v12.authority import Authority

            held = self._authority = Authority.create(
                _os.path.join(self.root, "authority.sqlite"),
                authority_uuid=fixtures.UUID)
            self.addCleanup(held.dispose)
            # THE DEPLOYMENT'S CONFIGURATION, not the composition's act.
            held.add_route_handler(self.CHILD_ROUTE, self.ACTOR)
        return held

    def execution(self, store):
        from tools.integration_worker import PreparationExecution

        self.composition()
        # THE PORT AND THE CONTROL STORE ARE THE FIXTURE'S REAL ONES, built
        # WITHOUT claiming: the actor's one live claim belongs to the
        # preparation this case is about.
        self.owners()
        return PreparationExecution(
            jobs=store, manager=self._control, control=self._control,
            authority=self.authority(), port=self.port,
            mint_bearer=lambda: "bearer-" + self.FRESH["prepare"][
                "execution_offer_id"])

    # FRESH IDENTITIES FOR THE PHASE THIS CASE ACTUALLY ISSUES. The shared
    # fixture's `prepare-attempt-1`/`prepare-offer-1` exist so that other
    # cases have an assignment to admit against; this case is about `prepare`
    # ISSUING the offer itself, so it registers a plan naming identities
    # nobody has minted a bearer for yet.
    FRESH = {"prepare": {"execution_attempt_id": "prepare-attempt-9",
                         "execution_offer_id": "prepare-offer-9"}}

    def prepared(self):
        store, stage, allocation, answer = self.registered(**self.FRESH)
        execution = self.execution(store)
        held = execution.prepare(
            orchestration_id=self.ORCHESTRATION,
            root_assignment_id=allocation["assignment_id"],
            request=self.request(), plan=self.plan(stage, **self.FRESH),
            execution_work_id=self.EXECUTION_WORK,
            execution_route=self.CHILD_ROUTE,
            policy_digest=self.POLICY, profile_name="reference",
            accept=self.accepting(), identity=self.IDENTITY,
        contract=self.CONTRACT)
        return store, stage, allocation, execution, held

    def accepting(self):
        """THE WORKER'S OWN ACCEPTANCE, through the real owner.

        The composition refuses to accept on a worker's behalf, so this case
        supplies it the way the shared fixture does -- which is also the point:
        the handshake has two sides and only one of them is the coordinator.
        """
        from baton_v12.worker_manager import accept_offer

        def accepted(offer_id):
            accept_offer(
                self._control, self.port, offer_id=offer_id,
                decision="accept", bearer="bearer-" + offer_id,
                now=fixtures.NOW,
                runtime_attempt_id=self.FRESH["prepare"][
                    "execution_attempt_id"],
                work_ref={"authority_uuid": fixtures.UUID,
                          "work_id": self.EXECUTION_WORK})
            # THE RUNTIME ATTEMPT IS NOT RECORDED HERE ANY MORE. This fixture
            # used to record it, which made the seam stand in for work the
            # composition owed: SLICE2-SCOPE-165724 lines 66-73 fix that
            # `PreparationExecution` calls the SAME public `record_attempt`
            # with the child worker's own operands. A fixture that kept
            # recording it would have hidden a composition that did not.

        def accept(issued):
            # THE ISSUED DOCUMENT, not the identity: an acceptance fences what
            # was actually issued, so the composition hands the whole answer.
            return accepted(issued["offer_id"] if isinstance(issued, dict)
                            else issued)
        return accept

    def test_the_runtime_attempt_is_recorded_by_the_composition(self):
        """THE OWNER ACT THIS COMPOSITION OWES, and whose operands.

        SLICE2-SCOPE-165724 lines 66-73 fix that `PreparationExecution` calls
        the SAME public `record_attempt` with the child worker's own operands.
        Until this round the FIXTURE recorded it, which meant the seam was
        standing in for work the composition never did -- and activation then
        refused "no runtime attempt" on the real traversal.

        The input digest is the one case where the child's own configuration
        is NOT the answer: it runs on the PUBLISHED bundle, so the attempt is
        recorded under the digest its offer was issued with. `IDENTITY` carries
        a deliberately different value so a composition that recorded the
        configured manifest instead would fail here rather than at admission.
        """
        _store, _stage, _allocation, _execution, held = self.prepared()
        # THE WORKER MANAGER'S OWN STORE, which is where attempts live; the
        # Job Manager store `prepared` returns has no attempts table at all.
        row = attempts._attempt_row(self._control,
                                    held["execution_attempt_id"])
        self.assertIsNotNone(row, "the composition records the attempt")
        self.assertEqual(row["adapter_name"], self.IDENTITY["adapter_name"])
        self.assertEqual(row["adapter_digest"],
                         self.IDENTITY["adapter_digest"])
        self.assertEqual(row["image_digest"], self.IDENTITY["image_digest"])
        self.assertEqual(row["toolchain_digest"],
                         self.IDENTITY["toolchain_digest"])
        # THE PUBLISHED INPUT, not the configured one.
        self.assertEqual(row["input_digest"], self.input_digest)
        self.assertNotEqual(row["input_digest"],
                            self.IDENTITY["input_digest"])

    def test_the_whole_sequence_runs_against_real_owners(self):
        store, stage, allocation, execution, held = self.prepared()
        # A REAL CHILD WORK AT THE AUTHORITY.
        projected = self.authority().project_work(self.EXECUTION_WORK)
        self.assertEqual(projected["work_id"], self.EXECUTION_WORK)
        self.assertEqual(projected["route"], self.CHILD_ROUTE)
        # AND THE AUTHORITY'S OWN LIVE ASSIGNMENT IS THIS CLAIM, which is what
        # a real session makes assertable at all: the fake answered whatever
        # it was asked about, so agreeing with it proved nothing.
        self.assertEqual(
            self.authority().assignment_of(self.EXECUTION_WORK)["participant"],
            self.ACTOR)
        self.assertEqual(self.authority().slot_holder(self.ACTOR),
                         self.EXECUTION_WORK)
        # A REAL CLAIM, read back through the Worker Manager's OWN reader
        # rather than from what this composition thinks it issued.
        self.assertEqual(
            [one["offer_id"] for one in
             execution.claimed_offer(held["execution_attempt_id"])],
            [held["offer_id"]])
        # AND THE ASSIGNMENT IS THE MANAGER'S ANSWER.
        self.assertEqual(held["assignment"]["participant"], self.ACTOR)

    def test_the_actor_holds_one_live_claim_and_the_preparation_takes_it(self):
        """WHY THIS FIXTURE PRE-CLAIMS NOTHING, asserted rather than asserted
        about.

        A principal holds ONE live claim across every address it acts through.
        The shared fixture's `prepare-attempt-1` would have spent the actor's
        only slot before the preparation could take it, which is what forced
        `preclaimed` to become a seam. So: the preparation holds the slot, and
        a second claim for another Work by the same actor is REFUSED -- through
        the deployment adapter's own translation, in the manager's closed
        vocabulary rather than as a raw Authority exception.
        """
        store, stage, allocation, execution, held = self.prepared()
        self.assertEqual(self.authority().slot_holder(self.ACTOR),
                         self.EXECUTION_WORK)
        # AND THE WORK IT CANNOT CLAIM IS THE PARENT'S OWN, which is the
        # selected acceptance rather than an arbitrary second Work: the apply
        # may not claim or start while its own actor is preparing. Here that
        # is not a rule this composition enforces -- it is the Authority's,
        # and it holds whether or not anybody remembered to check.
        parent = stage["work_id"]
        self.authority().create_work(parent, self.CHILD_ROUTE,
                                     contract=self.CONTRACT,
                                     operation_id="create-parent-" + parent)
        projected = self.authority().project_work(parent)
        with self.assertRaises(ContractRefusal) as caught:
            self.port.claim(parent, "claim-parent-" + parent, fixtures.UUID,
                            projected["scope"], projected["route"])
        self.assertIn("ONE active claim", str(caught.exception))
        # AND THE PREPARATION'S OWN CLAIM IS UNTOUCHED by the refusal.
        self.assertEqual(self.authority().slot_holder(self.ACTOR),
                         self.EXECUTION_WORK)
        self.assertIsNone(self.authority().assignment_of(parent))

    def test_the_claim_carries_the_authoritys_own_authorization(self):
        """The assignment is not the whole of what a claim answers.

        `activate_assignment` reads the principal, effective scope, role, grant
        and policy generation off THE ROW THIS MANAGER WROTE FROM THE
        AUTHORITY'S ANSWER, and refuses an attempt claimed by an offer that
        retains none. A fake answering a well-formed assignment could satisfy
        the four-part fence and carry no authorization at all; a real claim
        cannot, because the authority decides those and this composition never
        supplies them.
        """
        store, stage, allocation, execution, held = self.prepared()
        [offer] = execution.claimed_offer(held["execution_attempt_id"])
        # NAMED FROM THE SCHEMA'S OWN CONTRACT rather than spelled here: a
        # list written in this file would be this case's second opinion about
        # which columns a claim retains, and the two would drift.
        from baton_v12.worker_manager.schema import CLAIM_CONTEXT

        for member, _stored, _answered in CLAIM_CONTEXT:
            self.assertIsNotNone(offer[member], member)
        projected = self.authority().project_work(self.EXECUTION_WORK)
        # THE ROLE IS THE ROUTE THE OFFER FROZE, and the scope is the Work's
        # own -- the port proves both relations at the crossing, so a decision
        # authorising something else is not this offer's claim.
        self.assertEqual(offer["claim_role"], projected["route"])
        self.assertEqual(offer["claim_scope"], projected["scope"])

    def test_the_offer_is_the_one_the_plan_registered(self):
        """Admission compares the membership against the registered plan, so a
        composition that minted its own offer id would issue one offer and be
        admitted against another."""
        store, stage, allocation, execution, held = self.prepared()
        [planned] = [one for one in self.plan(stage, **self.FRESH)
                     if one["phase"] == "prepare"]
        self.assertEqual(held["offer_id"], planned["execution_offer_id"])
        self.assertEqual(held["execution_attempt_id"],
                         planned["execution_attempt_id"])

    def test_admission_is_committed_before_anything_starts(self):
        store, stage, allocation, execution, held = self.prepared()
        capacity_held = capacity.integration_capacity_of(store,
                                                         self.ORCHESTRATION)
        [member] = [one for one in capacity_held["members"]
                    if one["phase"] == "prepare"]
        self.assertEqual(member["state"], "admitted")
        # NOTHING HAS STARTED YET -- admission is the gate, not the start.
        self.assertEqual(execution.started, [])
        self.assertEqual(
            execution.start(self.ORCHESTRATION, held["execution_attempt_id"],
                            lambda: "started"), "started")

    def test_a_resumed_creation_does_not_mint_a_second_child_work(self):
        """The intent carries the operation id `create_work` is called with,
        so an interrupted creation is RESUMED rather than repeated.

        AND THE REPLAY IS OPERAND-EXACT, which the real Authority taught this
        case rather than the other way round: the first form re-created under
        the default contract and the Authority refused -- "operation id was
        reused for different operands". That is the protection working. A
        resumption that could quietly reach a DIFFERENT creation under one
        identity would be exactly the second child Work this step exists to
        prevent, so the resumed call replays every operand the first one made.
        """
        store, stage, allocation, execution, held = self.prepared()
        again = execution.create(held["intent"], contract=self.CONTRACT)
        self.assertEqual(
            again, self.authority().create_work(
                self.EXECUTION_WORK, self.CHILD_ROUTE, contract=self.CONTRACT,
                operation_id=held["intent"]["work_operation_id"]))
        # AND A DIFFERING OPERAND UNDER THE SAME IDENTITY IS REFUSED, not
        # quietly accepted as "already created".
        from baton_v12.authority import Refusal

        with self.assertRaises(Refusal):
            execution.create(held["intent"])
        # ONE CHILD WORK, still.
        self.assertEqual(
            self.authority().project_work(self.EXECUTION_WORK)["route"],
            self.CHILD_ROUTE)

    def test_the_parent_keeps_its_one_reserved_root(self):
        """The same actor holds the parent while it prepares: one root, one
        preparation member, and the parent's own allocation still bound."""
        store, stage, allocation, execution, held = self.prepared()
        capacity_held = capacity.integration_capacity_of(store,
                                                         self.ORCHESTRATION)
        self.assertEqual(capacity_held["root"]["root_assignment_id"],
                         allocation["assignment_id"])
        self.assertEqual(
            len([one for one in capacity_held["members"]
                 if one["phase"] == "prepare"]), 1)
        # AND THE PREPARATION RUNS ON ITS OWN CHILD WORK, not the parent's.
        self.assertNotEqual(held["intent"]["execution_work_id"],
                            stage["work_id"])

    def test_the_wrapper_admits_preparation_and_defers_the_parent(self):
        """THE SELECTED SEAM, END TO END, and the deferral actually reached.

        Review claim168871 placed this at `PooledManagerOperations.admit`:
        the allocation exists and the parent offer does not. So the wrapper
        registers the capacity root and its two-phase plan against the real
        allocation, drives the real child through `PreparationExecution` --
        real Authority child Work, real offer, acceptance, claim, activation
        and capacity admission -- and then DEFERS the parent.

        THE DEFERRAL IS THE POINT AND IT IS A REFUSAL, not a return.
        `manager._delegate` treats a normal return with no journalled parent
        offer as an integrity fault, and it is right to: that is a stage
        reported admitted with nothing authorizing it. A NONDURABLE refusal
        with no receipt is what it reads as `deferred`, leaving the admit owed
        for a later sweep.
        """
        from tools.integration_worker import (ManagedPreparation,
                                              PreparationAdmission)

        store, stage, allocation, answer = self.registered(**self.FRESH)
        self.composition()
        ordinary = []

        class Ordinary:
            def admit(self, held, job):
                ordinary.append(held["stage_id"])
                return None

        request = self.request()
        operands = {
            "orchestration_id": self.ORCHESTRATION,
            "execution_attempt_id": self.FRESH["prepare"][
                "execution_attempt_id"],
            "execution_work_id": self.EXECUTION_WORK,
            "execution_offer_id": self.FRESH["prepare"]["execution_offer_id"],
            "participant": self.ACTOR,
            "task_digest": "sha256:" + "a" * 64,
            "apply_task_digest": "sha256:" + "d" * 64,
            "input_digest": request["input_digest"],
            "profile_digest": self.PROFILE,
            "policy_digest": self.POLICY, "profile_name": "reference",
            "execution_route": self.CHILD_ROUTE, "contract": self.CONTRACT,
            "request": request, "accept": self.accepting(),
            "identity": self.IDENTITY}
        preparation = ManagedPreparation(
            jobs=store, control=self._control, authority=self.authority(),
            port=self.port, mint_bearer=lambda: "bearer-" + operands[
                "execution_offer_id"],
            orchestration=lambda _stage, _job: self.ORCHESTRATION,
            operands=lambda _stage, _job, _intent: operands)
        wrapper = PreparationAdmission(Ordinary(), preparation)

        with self.assertRaises(ContractRefusal) as deferred:
            wrapper.admit(stage, {"input_digest": request["input_digest"]})
        self.assertIn("the parent offer is not issued",
                      str(deferred.exception))
        # NONDURABLE, which is what `_delegate` reads as deferred rather than
        # as a settled outcome.
        self.assertFalse(deferred.exception.durable)
        # AND THE PARENT ADMIT NEVER HAPPENED: no offer was issued for it.
        self.assertEqual(ordinary, [])
        # ASKED OF THE MANAGER'S OWN TABLE rather than of a helper: the
        # parent's offer id exists on the stage row from the moment the
        # episode opened, and what must NOT exist is an offer issued under it.
        self.assertEqual(
            self._control._connection.execute(
                "SELECT COUNT(*) FROM offers WHERE offer_id = ?",
                (stage["offer_id"],)).fetchone()[0], 0)
        # THE CHILD, HOWEVER, IS REALLY ADMITTED -- before anything started.
        [answered] = preparation.started
        self.assertEqual(answered["execution_attempt_id"],
                         self.FRESH["prepare"]["execution_attempt_id"])
        held = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        [member] = [one for one in held["members"]
                    if one["phase"] == PREPARATION_PHASE_NAME]
        self.assertEqual(member["state"], "admitted")
        # AND THE APPLY IS PLANNED UNDER THE PARENT'S OWN IDENTITIES, which
        # the episode owner minted before any offer was issued -- read, not
        # predicted.
        [applying] = [one for one in held["members"]
                      if one["phase"] == "apply"]
        self.assertEqual(applying["state"], "planned")
        self.assertEqual(applying["execution_attempt_id"],
                         stage["attempt_id"])
        self.assertEqual(applying["execution_offer_id"], stage["offer_id"])
        # AND THE ONE RESERVED ROOT IS THE PARENT'S OWN ALLOCATION.
        self.assertEqual(held["root"]["root_assignment_id"],
                         allocation["assignment_id"])

    def test_a_committed_intent_with_no_published_input_refuses(self):
        """THE CASE THAT REPLACED TWO OF MINE, and the reason is the point.

        My earlier `..._moved_the_target_refuses` and
        `..._naming_a_second_child_work_refuses` drove `_preserved` with no
        published root at all. Review claim169347 showed that shape is the
        defect rather than the guard: an intent whose request can only be
        RECOMPOSED is refused forever and never resumes. So a missing durable
        record is now its own refusal, reached before any comparison, and the
        recovery path those two cases meant to describe is exercised where a
        real published bundle exists -- `test_managed_preparation`'s
        `TheOperandsAreResolvedFromOwnerAnswers`.
        """
        store, stage, allocation, execution, held = self.prepared()
        wrapper, preparation, operands = self.wrapped(store)
        with self.assertRaises(ContractRefusal) as caught:
            preparation._preserved(self.intent(store), dict(operands))
        self.assertIn("name no published input root", str(caught.exception))

    def test_an_absent_intent_carries_no_constraint(self):
        """NAMED FOR WHAT IT PROVES, which review claim169416 caught me getting
        wrong. This passes `None` for the intent, so it establishes ABSENCE
        PASSTHROUGH and not resume agreement -- and it kept the old name long
        enough to read as the latter. The honest agreement case needs a real
        intent AND a real published input, so it lives in
        `test_managed_preparation`'s `TheOperandsAreResolvedFromOwnerAnswers`
        where a real bundle exists."""
        store, stage, allocation, execution, held = self.prepared()
        wrapper, preparation, operands = self.wrapped(store)
        self.assertEqual(preparation._preserved(None, dict(operands)),
                         operands)

    def test_the_first_sweep_carries_no_constraint(self):
        """An absent intent means nothing has been decided yet, so there is
        nothing for these operands to contradict."""
        store, stage, allocation, answer = self.registered(**self.FRESH)
        wrapper, preparation, operands = self.wrapped(store)
        self.assertIsNone(capacity.preparation_intent_of(store,
                                                         self.ORCHESTRATION))
        self.assertEqual(preparation._preserved(None, dict(operands)),
                         operands)

    def intent(self, store):
        """This orchestration's committed intent, from its own owner."""
        return capacity.preparation_intent_of(store, self.ORCHESTRATION)

    def wrapped(self, store):
        """The wrapper, its preparation and the operands it would resolve."""
        from tools.integration_worker import (ManagedPreparation,
                                              PreparationAdmission)

        self.composition()
        request = self.request()
        operands = {
            "orchestration_id": self.ORCHESTRATION,
            "execution_attempt_id": self.FRESH["prepare"][
                "execution_attempt_id"],
            "execution_work_id": self.EXECUTION_WORK,
            "execution_offer_id": self.FRESH["prepare"]["execution_offer_id"],
            "participant": self.ACTOR,
            "task_digest": "sha256:" + "a" * 64,
            "apply_task_digest": "sha256:" + "d" * 64,
            "input_digest": request["input_digest"],
            "profile_digest": self.PROFILE, "policy_digest": self.POLICY,
            "profile_name": "reference", "execution_route": self.CHILD_ROUTE,
            "contract": self.CONTRACT, "request": request,
            "accept": self.accepting(), "identity": self.IDENTITY}
        preparation = ManagedPreparation(
            jobs=store, control=self._control, authority=self.authority(),
            port=self.port, mint_bearer=lambda: "bearer-1",
            orchestration=lambda _stage, _job: self.ORCHESTRATION,
            operands=lambda _stage, _job, _intent: operands)
        return PreparationAdmission(object(), preparation), preparation, operands

    def test_a_plan_without_a_preparation_phase_refuses(self):
        store, stage, allocation, answer = self.registered()
        execution = self.execution(store)
        with self.assertRaises(ContractRefusal) as caught:
            execution.prepare(
                orchestration_id=self.ORCHESTRATION,
                root_assignment_id=allocation["assignment_id"],
                request=self.request(),
                plan=[one for one in self.plan(stage, **self.FRESH)
                      if one["phase"] != "prepare"],
                execution_work_id=self.EXECUTION_WORK,
                execution_route="integration-preparation",
                policy_digest=self.POLICY, profile_name="reference",
                accept=self.accepting(), identity=self.IDENTITY)
        self.assertIn("registers no prepare", str(caught.exception))


class ThePreparationIsAdmittedBeforeTheParentOffer(CapacityCase):
    """W161230 A.4 -- the RESERVED-BEFORE-PARENT-OFFER interception.

    Review claim168871 corrected the placement I had proposed. The ordinary Job
    path is `manager._launch` (claimed stages only) -> `StageExecution.launch`
    -> `Integration.run` -> `reconciled`, so a preparation claimed at
    `reconciled` is claimed AFTER the parent has taken this principal's one
    Authority slot -- and a principal holds one live claim, so it could never
    be claimed at all. `scheduler.PooledManagerOperations.admit` reserves the
    allocation and only THEN calls the selected worker's `admit`; that is the
    one place where the reservation exists and the parent offer does not.

    THESE CASES DRIVE THE WRAPPER, not a description of it: a real allocation
    from the real scheduler, the real capacity owner, and the real refusal that
    `manager._delegate` reads as `deferred`.
    """

    def operations(self, admitted=None):
        """The ordinary operations this wrapper wraps, recorded."""
        held = admitted if admitted is not None else []

        class Ordinary:
            def __init__(self): self.calls = []

            def admit(self, stage, job):
                self.calls.append(("admit", stage["stage_id"]))
                held.append(stage["stage_id"])
                return None

            def claim(self, stage):
                self.calls.append(("claim", stage["stage_id"]))
                return {"claimed": True}

            def close(self):
                self.calls.append(("close", None))

        return Ordinary()

    def wrapper(self, preparation=None):
        from tools.integration_worker import PreparationAdmission

        self.ordinary = self.operations()
        return PreparationAdmission(self.ordinary, preparation)

    # -- transparency, which is what makes wiring the seam safe -------------

    def test_an_unselected_deployment_gets_the_operations_it_always_had(self):
        """No managed preparation configured means this adds nothing. The
        wrapper sits on the path EVERY integration stage takes, so a
        composition that changed behaviour for deployments that did not ask
        for it would be a migration nobody selected."""
        store, stage, allocation = self.reserved()
        held = self.wrapper()
        self.assertIsNone(held.admit(stage, {"input_digest": "d"}))
        self.assertEqual(self.ordinary.calls, [("admit", stage["stage_id"])])
        # AND EVERY OTHER ACT IS FORWARDED rather than reimplemented.
        self.assertEqual(held.claim(stage), {"claimed": True})
        held.close()
        self.assertEqual(self.ordinary.calls[-1], ("close", None))

    # -- and what it does when preparation IS selected ---------------------

    def prepared(self, store, stage, allocation, **changed):
        from tools.integration_worker import ManagedPreparation

        self.owners()
        request = self.request()
        held = {"orchestration_id": self.ORCHESTRATION,
                "execution_attempt_id": "prepare-attempt-1",
                "execution_work_id": self.EXECUTION_WORK,
                "execution_offer_id": "prepare-offer-1",
                "participant": self.ACTOR,
                "task_digest": "sha256:" + "a" * 64,
                "apply_task_digest": "sha256:" + "d" * 64,
                "input_digest": self.input_digest,
                "profile_digest": self.PROFILE,
                "policy_digest": self.POLICY,
                "profile_name": "reference",
                "execution_route": "baton.impl",
                "request": request,
                "accept": lambda offer_id: None,
                "identity": self.IDENTITY}
        held.update(changed)
        return ManagedPreparation(
            jobs=store, control=self._control, authority=None,
            port=self.port, mint_bearer=lambda: "bearer-1",
            orchestration=lambda _stage, _job: held["orchestration_id"],
            operands=lambda _stage, _job, _intent: held)

    def test_a_stage_with_no_allocation_is_refused_before_anything(self):
        """The wrapper runs INSIDE the pooled admit, which reserves FIRST. A
        stage with no allocation at all means the seam was reached out of
        order, and there is no reservation for a preparation to run inside."""
        store = self.store()
        document = pool()
        scheduler.activate_pool(store, document, principals(document))
        from baton_v12.job_manager import submit

        submit(store, fixtures.submission(jobs=[fixtures.job(
            "job-a", stages=[
                fixtures.stage("integration", fixtures.WORK_A)])]))
        stage = self.integration_stage(store)
        # DELIBERATELY NOT RESERVED. `PooledManagerOperations.admit` calls
        # `_allocation(stage, create=True)` before the worker's admit, so this
        # state is only reachable by calling the seam out of order.
        held = self.wrapper(self.prepared(store, stage, None))
        with self.assertRaises(ContractRefusal) as caught:
            held.admit(stage, {"input_digest": self.input_digest})
        self.assertIn("holds no scheduler allocation", str(caught.exception))
        self.assertEqual(self.ordinary.calls, [])

    def test_a_released_reservation_is_refused_by_its_own_owner(self):
        """MEASURED, and it changed this case. `release` leaves the allocation
        row in place, so the wrapper's own absence guard is not what catches a
        released reservation -- the capacity owner is, with a better sentence
        than the wrapper could write. That is the right division: the wrapper
        refuses what it can see for itself and does not restate a rule the
        capacity owner already owns."""
        store, stage, allocation = self.reserved()
        scheduler.release(store, stage["attempt_id"], "released for this case")
        held = self.wrapper(self.prepared(store, stage, allocation))
        with self.assertRaises(ContractRefusal) as caught:
            held.admit(stage, {"input_digest": self.input_digest})
        self.assertIn("was already released", str(caught.exception))
        self.assertEqual(self.ordinary.calls, [])

    def test_an_already_claimed_parent_refuses_managed_conversion(self):
        """A stage whose parent already holds the claim has already taken this
        principal's one slot. It stays on its recorded legacy path; this does
        not release and reclaim it to make room."""
        store, stage, allocation = self.reserved()
        held = self.wrapper(self.prepared(store, stage, allocation))
        with self.assertRaises(ContractRefusal) as caught:
            held.admit(dict(stage, state="claimed"),
                       {"input_digest": self.input_digest})
        self.assertIn("stays on its recorded legacy path",
                      str(caught.exception))
        self.assertEqual(self.ordinary.calls, [])
