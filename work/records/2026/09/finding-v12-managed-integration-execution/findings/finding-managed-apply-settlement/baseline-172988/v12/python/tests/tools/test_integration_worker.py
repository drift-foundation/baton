"""W110774: the production integration runtime port.

`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/
finding-standalone-stage-composition/findings/finding-integration-runtime-port/`.

WHAT THIS FILE OWNS. The deployment composer's CONFIGURATION and its REFUSALS
-- what it will not be constructed from, the manager attempt it prepares before
admission asks for a runtime, everything `run` refuses before any engine is
reached or any target byte is exposed, and the live continuation marker's own
rules -- AND the whole composed path: a real start over the real mount
boundary, a real worker turn over the delivery, positive quiescence, the
Authority receipt before settlement, the release, the release-tail replay and
the restart hold.

THE OWNERS ARE REAL. The manager store, the offer/claim lifecycle, the attempt
record and its activation, the accepted evidence producer, the mount boundary,
`OciAdapter.start`, `run_vector`, the worker entry and workload, the
coordinator and both drivers are the actual ones. Exactly two seams are
deterministic and both are recorded rather than assumed: the ENGINE is a
callable answering `run`, `inspect` and `ps` with no daemon, and the PROVIDER
inside the workload is a real child process. The credential bearer is
synthetic and minted by this fixture's own provider.

WHAT IS NOT REACHED, and is not claimed: no daemon, no container, no image
build or selection, no network, no live model and no live credential or secret
store. `PortCase`'s own engine seam RAISES if a case reaches it, which is what
makes the pre-exposure refusals mean what they say.
"""

import copy
import os
import shutil
import tempfile
import unittest

from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import driver, oci_delivery, runtime
from baton_v12.worker_manager import source_boundary
from baton_v12.worker_manager.attempts import attempt_runtime_of

from tools import integration_worker
from tools.integration_worker import IntegrationRuntimePort

from tests.integration.test_execution import profile as integration_profile
from tests.integration.test_runtime import PARTICIPANT
from tests.tools.test_integration_bundle import INSTRUCTIONS


IMAGE = "sha256:" + "e" * 64
TOOLCHAIN = "sha256:" + "f" * 64
ATTEMPT = "integrator-attempt"


class PortCase(unittest.TestCase):
    """One real accepted world, one claimed integrator offer, one port.

    COMPOSED, NOT SUBCLASSED, and the imports are inside the method: a
    module-level `TestCase` binding is collected by the loader and a subclass
    re-runs every one of its parent's cases under a second name. Both
    inflations happened in this campaign and both are avoided deliberately.
    """

    def setUp(self):
        from tests.tools.test_integration_bundle import ProducerCase

        self.producer = ProducerCase("run")
        self.producer.setUp()
        self.addCleanup(self.producer.doCleanups)
        self.world = self.producer.world
        self.owner = self.world.owner
        self.root = tempfile.mkdtemp(prefix="v12-w110774-")
        self.addCleanup(shutil.rmtree, self.root, True)

        self.profile = self.producer.profile
        self.calls = []
        self.target_place = self.place("canonical-target")
        os.chown(self.target_place, -1, self.owner.group.gid)
        os.chmod(self.target_place, 0o2770)
        self.launch_root = self.place("integration-deliveries")
        self.assignment_port = self._offered()
        self._credentials()

    # W110774 review 2026-09-08T02:29:59Z [P1]: THE CREDENTIAL CONFIGURATION,
    # supplied with SYNTHETIC bytes. The selected entry reads its bearer from
    # the `claude` slot, so a port without one is not configured -- and no live
    # credential, provider or secret store is reached to prove that.
    BEARER = "synthetic-integration-bearer"

    def _credentials(self):
        from baton_v12.worker_manager import credentials

        self.minted = []
        self.credential_home = credentials.CredentialHome(
            self.place("credential-home"))
        self.credential_resolution = credentials.resolved_delivery(
            ["claude"], profile={"claude": {"provider": "fixture",
                                            "reference": "kv/claude"}})

        def mint(name, reference):
            self.minted.append((name, reference))
            return self.BEARER

        self.credential_provider = mint

    # -- the world's own material -------------------------------------------

    def place(self, *parts):
        made = os.path.join(self.root, *parts)
        os.makedirs(made, exist_ok=True)
        return made

    def _offered(self):
        """One claimed offer for the integrator attempt, and NO attempt row.

        The lifecycle fixture's `registered` also records and activates the
        attempt; this deliberately stops before both, because recording and
        activating IS what `prepare` is for, and a fixture that did it first
        would leave nothing for the port to be measured on.
        """
        from baton_v12.worker_manager import (AuthorityPort, accept_offer,
                                              issue_offer, retain_manifest,
                                              submit_claim)
        from tests.job_manager.test_review_driver import (NOW, PROFILE,
                                                          WORK_A,
                                                          _EndingAuthority)
        from tests.manager.test_offers import (SCOPE, decision,
                                               fake_claim_signature)
        from tests.manager.test_output import OutputCase, POLICY, sealed
        from tests.manager.test_attempts import ADAPTER

        declaration = sealed(dict(
            OutputCase.published(),
            work_ref={"authority_uuid": self.owner.AUTHORITY,
                      "work_id": WORK_A},
            outputs=copy.deepcopy(self.owner.DECLARED),
            runtime_profile_digest=PROFILE, policy_digest=POLICY))
        self.input_digest = retain_manifest(
            self.world.manager, declaration, "inputManifest")["digest"]
        self.input_manifest = declaration
        self.policy_digest, self.profile_digest = POLICY, PROFILE
        self.adapter_digest = ADAPTER
        assignment = {"work_ref": {"authority_uuid": self.owner.AUTHORITY,
                                   "work_id": WORK_A},
                      "participant": PARTICIPANT, "generation": 1}
        session = _EndingAuthority(
            participant=PARTICIPANT,
            work={"status": "open", "phase": "queued", "handler": None,
                  "gate": None, "authority_uuid": self.owner.AUTHORITY,
                  "scope": SCOPE, "route": "review"})
        session.claim_answer = {
            "assignment": assignment, "claim_event": 1,
            "decision": decision(participant=PARTICIPANT,
                                 principal="integrator-principal",
                                 role="review")}
        session.live_assignment = dict(assignment)
        port = AuthorityPort(session, fake_claim_signature)
        issue_offer(self.world.manager, port, offer_id="offer-" + ATTEMPT,
                    work_id=WORK_A, runtime_attempt_id=ATTEMPT,
                    input_digest=self.input_digest, policy_digest=POLICY,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "fixture-offer-bearer")
        accept_offer(self.world.manager, port, offer_id="offer-" + ATTEMPT,
                     decision="accept", bearer="fixture-offer-bearer",
                     now=NOW, runtime_attempt_id=ATTEMPT,
                     work_ref=assignment["work_ref"])
        submit_claim(self.world.manager, port, offer_id="offer-" + ATTEMPT)
        self.claimed_assignment = assignment
        return port

    def engine_run(self, argv, **options):
        """The engine seam NO case in this module reaches, and that is the
        assertion: a refusal before exposure is one that asked nothing."""
        self.calls.append(list(argv))
        raise AssertionError("no case in this module starts a runtime")

    def port(self, **changed):
        operands = {
            "coordinator": self.world.coordinator,
            "manager": self.world.manager, "jobs": self.world.jobs,
            "authority": self.world.authority_read,
            "assignment_port": self.assignment_port,
            "profile": self.profile,
            "checkpoint_profile": self.producer.checkpoint,
            "object_runner": self.producer.objects,
            "line_id": self.world.line_id,
            "proposal_id": self.world.proposal_id,
            "canonical_target_id": self.world.target,
            "canonical_target": self.target_place,
            "delivery_home": self.launch_root,
            "instructions": INSTRUCTIONS,
            "identity": {"image_digest": IMAGE,
                         "profile_digest": self.profile_digest,
                         "policy_digest": self.policy_digest,
                         "adapter_digest": self.adapter_digest},
            "adapter_name": "acp", "toolchain_digest": TOOLCHAIN,
            "input_manifest": self.input_manifest,
            "engine": "docker", "engine_run": self.engine_run,
            "workspace_storage": self.owner.storage,
            "workspace_group": self.owner.group,
            "capacity": source_boundary.workspace_capacity(1 << 30),
            "bundle_home": self.place("bundles"),
            "launch_home": self.place("launch-home"),
            "launch_session": "integration-session",
            "launch_contract": "baton.worker-control/1",
            "network": "none",
            "credential_resolution": self.credential_resolution,
            "credential_home": self.credential_home,
            "credential_provider": self.credential_provider}
        operands.update(changed)
        return IntegrationRuntimePort(**operands)

    def stage(self, **changed):
        held = {"stage_id": "stage-integration", "attempt_id": ATTEMPT,
                "kind": integration_worker.INTEGRATION_STAGE_KIND,
                "job_id": "job-1"}
        held.update(changed)
        return held

    def assignment(self, **changed):
        """One assignment document shaped like the coordinator's own.

        These cases are about what `run` refuses BEFORE it composes anything,
        so the members it compares are what has to be real here; a composed
        grant is the composed-start proof's material and not this module's.
        """
        held = {"schema": "baton.integration-assignment/1",
                "canonical_target_id": self.world.target,
                "entry_id": "entry-1", "lease_id": "lease-1", "fence": 1,
                "attempt_id": ATTEMPT,
                "integrator_participant":
                    self.profile["integrator_participant"],
                "profile_kind": self.profile["profile_kind"],
                "profile_version": self.profile["profile_version"],
                "instructions_digest": self.profile["instructions_digest"],
                "target_access": "writable"}
        held.update(changed)
        return held

    def refused(self, action, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            action(*operands, **named)
        return caught.exception

    def target_state(self):
        """Every path under the disposable target, with its mode."""
        found = {}
        for base, _, names in os.walk(self.target_place):
            for one in sorted(names):
                whole = os.path.join(base, one)
                with open(whole, "rb") as handle:
                    found[os.path.relpath(whole, self.target_place)] = (
                        handle.read(), os.stat(whole).st_mode & 0o777)
        return found


class TheportIsConstructedFromResolvedOperands(PortCase):
    """W110774 FINDING: construction receives already-resolved stores,
    identity, engine/image and typed bindings, and infers nothing."""

    def test_a_configured_port_holds_its_own_resolved_operands(self):
        held = self.port()
        self.assertEqual(held.line_id, self.world.line_id)
        self.assertEqual(held.proposal_id, self.world.proposal_id)
        self.assertEqual(held.identity["image_digest"], IMAGE)
        self.assertEqual(held._storage, self.owner.storage)
        self.assertEqual(held.network, "none")
        # AND IT NAMES THE ACCEPTED PORT CONTRACT'S ONE VERB.
        from baton_v12.integration import INTEGRATION_PORT
        for verb in INTEGRATION_PORT:
            self.assertTrue(callable(getattr(held, verb, None)))

    def test_an_engine_this_manager_does_not_drive_refuses(self):
        caught = self.refused(self.port, engine="not-an-engine")
        self.assertIn("not one this manager drives", caught.message)

    def test_an_identity_that_is_not_the_closed_set_refuses(self):
        for changed in ({"image_digest": IMAGE},
                        dict(image_digest=IMAGE, profile_digest="p",
                             policy_digest="q", adapter_digest="r",
                             extra="s")):
            with self.subTest(identity=sorted(changed)):
                self.refused(self.port, identity=changed)

    def test_a_workspace_storage_that_is_not_provisioned_refuses(self):
        """The two assignment roots are ALLOCATED by their own owner from
        this storage; a deployment that named them itself would supply roots
        nothing had proved belonged to one assignment."""
        caught = self.refused(self.port, workspace_storage="/nope")
        self.assertIn("not a directory this deployment provisioned",
                      caught.message)
        self.refused(self.port, workspace_storage="relative/storage")

    def test_a_relative_or_absent_canonical_target_refuses(self):
        self.refused(self.port, canonical_target="relative/target")
        self.refused(self.port,
                     canonical_target=os.path.join(self.root, "absent"))
        self.refused(self.port, delivery_home=os.path.join(self.root, "gone"))

    def test_the_target_identity_is_configured_and_not_taken_from_a_grant(
            self):
        """W110774 review 2026-09-08T02:07:47Z [P1]: a port that held only a
        DIRECTORY took the identity to bind it under from the assignment, so
        every lower check compared the plan against a target composed out of
        the very document being checked."""
        held = self.port()
        self.assertEqual(held._target_id, self.world.target)
        self.assertEqual(held._configured_target().canonical_target_id,
                         self.world.target)
        self.refused(self.port, canonical_target_id=None)

    def test_instruction_bytes_are_bytes_this_deployment_configured(self):
        self.refused(self.port, instructions="not bytes")
        self.refused(self.port, instructions=b"")

    def test_an_unconfigured_or_foreign_credential_resolution_refuses(self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: these operands defaulted
        to `None` and were passed through untouched, so an unavailable
        credential reached a real engine start."""
        from baton_v12.worker_manager import credentials

        self.assertIn("resolved delivery",
                      self.refused(self.port,
                                   credential_resolution=None).message)
        self.assertIn("resolved delivery",
                      self.refused(self.port,
                                   credential_resolution=()).message)
        # A RESOLUTION FOR SOMEBODY ELSE'S SLOT IS NOT THIS ONE'S.
        foreign = credentials.resolved_delivery(
            ["api"], profile={"api": {"provider": "fixture",
                                      "reference": "kv/api"}})
        caught = self.refused(self.port, credential_resolution=foreign)
        self.assertIn("reads its bearer from slot", caught.message)
        self.assertIn(integration_worker.REQUIRED_CREDENTIAL_SLOT,
                      caught.message)
        self.refused(self.port, credential_home=object())
        self.refused(self.port, credential_provider=None)

    def test_a_store_or_session_that_is_not_a_capability_refuses(self):
        self.refused(self.port, manager=object())
        self.refused(self.port, assignment_port=object())
        self.refused(self.port, checkpoint_profile=object())


class ThePreparationUsesTheManagersOwnOwners(PortCase):
    """The contract's preparation row: `record_attempt`/`activate_assignment`
    over the claimed integrator stage, replaying exactly and starting
    nothing."""

    def test_it_records_and_activates_this_stages_attempt(self):
        answer = self.port().prepare(self.stage(), {"job_id": "job-1"})
        self.assertEqual(answer["attempt_id"], ATTEMPT)
        self.assertEqual(answer["assignment"], self.claimed_assignment)
        held = attempt_runtime_of(self.world.manager, ATTEMPT)
        # THE ONE STATE ADMISSION WILL ACCEPT, and no runtime was started to
        # reach it.
        self.assertEqual(held["execution_runtime"], "not-started")
        self.assertEqual(self.calls, [])

    def test_an_identical_preparation_replays(self):
        self.port().prepare(self.stage(), None)
        self.port().prepare(self.stage(), None)
        self.assertEqual(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"], "not-started")

    def test_a_preparation_with_another_identity_refuses(self):
        """An operand that rides the attempt's signature is not a detail: a
        second deployment identity for one attempt is a collision, not a
        replay."""
        self.port().prepare(self.stage(), None)
        other = self.port(identity={"image_digest": "sha256:" + "9" * 64,
                                    "profile_digest": self.profile_digest,
                                    "policy_digest": self.policy_digest,
                                    "adapter_digest": self.adapter_digest})
        self.refused(other.prepare, self.stage(), None)

    def test_a_replayed_preparation_reuses_the_exact_prepared_credential(
            self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: an identical replay
        REMINTED, asking the secret source again for a delivery this execution
        was already holding."""
        held = self.port()
        first = held.prepare(self.stage(), None)
        self.assertEqual(len(self.minted), 1)
        # THE CUSTODY THIS DEPLOYMENT NOW HOLDS. The lifecycle record is the
        # owner's to write when a runtime attaches; what exists after
        # materialization is the attempt's own private root, so that is what
        # a replay must not disturb.
        state = self.credential_home.read_state(ATTEMPT)
        self.assertTrue(os.path.lexists(
            self.credential_home.volatile_root(ATTEMPT)))

        second = held.prepare(self.stage(), None)
        self.assertEqual(second["attempt_id"], first["attempt_id"])
        # THE PROVIDER WAS NOT ASKED AGAIN and the custody record still stands.
        self.assertEqual(len(self.minted), 1)
        self.assertEqual(self.credential_home.read_state(ATTEMPT), state)
        self.assertTrue(os.path.lexists(
            self.credential_home.volatile_root(ATTEMPT)))

    def test_a_stage_of_another_kind_is_not_this_ports_to_prepare(self):
        caught = self.refused(self.port().prepare,
                              self.stage(kind="implementation"), None)
        self.assertIn("prepares only", caught.message)
        self.assertIsNone(attempt_runtime_of(self.world.manager, ATTEMPT))

    def test_a_stage_whose_job_disagrees_with_it_refuses(self):
        self.refused(self.port().prepare, self.stage(),
                     {"job_id": "another-job"})
        self.assertIsNone(attempt_runtime_of(self.world.manager, ATTEMPT))

    def test_an_attempt_with_no_claimed_offer_refuses(self):
        caught = self.refused(self.port().prepare,
                              self.stage(attempt_id="never-offered"), None)
        self.assertIn("claimed offers", caught.message)


class TheStartRefusesBeforeAnythingIsExposed(PortCase):
    """The matrix's item 6: wrong attempt, participant, instructions or
    posture refuse before writable exposure, with the target unchanged."""

    def setUp(self):
        super().setUp()
        self.port_held = self.port()
        self.port_held.prepare(self.stage(), None)
        self.before = self.target_state()

    def unchanged(self):
        self.assertEqual(self.target_state(), self.before)
        self.assertEqual(self.calls, [])

    def test_an_assignment_for_another_integrator_refuses(self):
        caught = self.refused(
            self.port_held.run, None,
            self.assignment(integrator_participant="baton.somebody-else"))
        self.assertIn("this port is configured for", caught.message)
        self.unchanged()

    def test_an_assignment_naming_other_instructions_refuses(self):
        caught = self.refused(
            self.port_held.run, None,
            self.assignment(instructions_digest="sha256:" + "7" * 64))
        self.assertIn("this port carries", caught.message)
        self.unchanged()

    def test_a_target_access_that_is_not_writable_refuses(self):
        caught = self.refused(self.port_held.run, None,
                              self.assignment(target_access="read-only"))
        self.assertIn("only over a writable target access", caught.message)
        self.unchanged()

    def test_an_assignment_with_no_attempt_refuses(self):
        self.refused(self.port_held.run, None,
                     self.assignment(attempt_id=None))
        self.unchanged()

    def test_a_grant_over_another_target_never_reaches_this_directory(self):
        """THE TWO-TARGET NEGATIVE. The assignment is well formed and its
        grant may be perfectly live -- over target B. This port serves target
        A, and A's directory is what it would have exposed."""
        caught = self.refused(
            self.port_held.run, None,
            self.assignment(canonical_target_id="target:somebody-else"))
        self.assertIn("never authorizes exposure of another's directory",
                      caught.message)
        self.unchanged()
        # AND NOTHING WAS COMPOSED FOR IT: no bundle, no launch document.
        self.assertEqual(os.listdir(os.path.join(self.root, "bundles")), [])
        self.assertEqual(os.listdir(os.path.join(self.root, "launch-home")),
                         [])


class TheLiveMarkerIsBookkeepingAndNeverAuthority(PortCase):
    """The contract's marker rules: bound to the whole assignment and
    delivery, taken only by a validated start, and never durable."""

    def test_an_execution_that_started_nothing_may_continue_nothing(self):
        held = self.port()
        self.assertFalse(held.may_continue(self.assignment()))

    def test_the_marker_binds_the_whole_assignment(self):
        held = self.port()
        # The marker a validated start would take, taken here directly: what
        # this case is about is the COMPARISON, and a composed start is the
        # separate proof this module still owes.
        held._live[ATTEMPT] = {"assignment": self.assignment(),
                               "delivery_root": self.launch_root,
                               "bundle_digest": "sha256:" + "3" * 64}
        self.assertTrue(held.may_continue(self.assignment()))
        for changed in ({"fence": 2}, {"lease_id": "lease-9"},
                        {"entry_id": "entry-9"},
                        {"canonical_target_id": "target:other"}):
            with self.subTest(changed=sorted(changed)):
                self.assertFalse(held.may_continue(self.assignment(**changed)))

    def test_a_second_execution_of_this_deployment_holds_no_marker(self):
        """A restart loses it by construction, because it never left memory."""
        started = self.port()
        started._live[ATTEMPT] = {"assignment": self.assignment(),
                                  "delivery_root": self.launch_root,
                                  "bundle_digest": "sha256:" + "3" * 64}
        self.assertFalse(self.port().may_continue(self.assignment()))
        started.forget(ATTEMPT)
        self.assertFalse(started.may_continue(self.assignment()))

    def test_a_status_read_needs_no_marker_and_no_preceding_start(self):
        """W110774 review 2026-09-08T02:07:47Z [P1], and this case CHANGED
        with it: it previously asserted that a status read without this
        execution's marker refuses, which codified the defect rather than the
        rule. PLAN item 4 schedules that correction ("restart observation
        locators"), so the expectation is now the required behaviour --
        observation is CONFIGURED and continuation is EARNED.

        A port constructed after a restart holds no marker and can still look:
        it resolves the delivery from its configured delivery home and the
        target from its configured identity, answers the manager's durable
        runtime state, and says plainly that continuation is not permitted.
        """
        # The attempt exists durably, as it does after any real restart; what
        # this second port does NOT have is the marker, and a start it never
        # performed.
        self.port().prepare(self.stage(), None)
        answer = self.port().observed(ATTEMPT, self.assignment())
        self.assertEqual(answer["attempt_id"], ATTEMPT)
        self.assertEqual(answer["execution_runtime"], "not-started")
        # NOTHING WAS MATERIALIZED for this attempt, which is an ordinary
        # answer and not a refusal.
        self.assertIsNone(answer["delivery"])
        self.assertIsNone(answer["observed"])
        self.assertFalse(answer["continuable"])


class TheWholeIntegrationRunsThroughThisPort(PortCase):
    """THE COMPOSED PROOF: an accepted proposal, this port, a real worker turn
    over a disposable target, and a released lease.

    The two deterministic seams are the ENGINE, which answers `run`, `inspect`
    and `ps` without a daemon, and the PROVIDER, which is a real child process
    that imports the reviewed bytes. Everything between them is the actual
    thing: the real bundle producer, the real mount boundary, the real
    `OciAdapter.start` and `run_vector`, the real worker entry and workload,
    the real coordinator and the real admission/continuation drivers.
    """

    ORIGINAL = b"the reviewed base\n"
    CANDIDATE = b"the reviewed candidate\n"

    def setUp(self):
        super().setUp()
        self.running = True
        self.engine_calls = []
        self.reviewed = self.producer.evidence()["paths"][0]
        self.harness = "harness.py"
        self._retained_trees()
        self._provisioned_target()

    # -- the world's material ------------------------------------------------

    def _retained_trees(self):
        """The retained base and head trees the bundle is read out of."""
        from tests.tools.test_integration_bundle import BASE_TREE

        held = self.owner.observed
        self.producer.objects.tree(BASE_TREE, {})
        self.producer.objects.tree(held["tree"],
                                   {self.reviewed: ("100644", self.CANDIDATE)})

    def _provisioned_target(self):
        """The disposable canonical target, carrying the accepted command."""
        argv = self.world.required["argv"]
        script = os.path.join(self.target_place, argv[-1])
        with open(script, "w", encoding="utf-8") as handle:
            handle.write("print('the accepted verification ran')\n")
        os.chmod(script, 0o644)

    def engine_run(self, argv, **options):
        """A recorded engine that answers what it was bound with.

        `self.running` is the container's own life: the workload writes its
        result and the process ends, so a case that has driven the entry flips
        it and the manager's own reconciliation OBSERVES a stopped runtime
        rather than being told about one.
        """
        import json

        self.engine_calls.append(list(argv))
        if argv[1] == "ps":
            return {"status": 0, "stdout": "", "stderr": ""}
        if argv[1] == "inspect":
            delivery = self.delivery()
            mounts = [{"Source": delivery.assignment_root,
                       "Destination": runtime.ASSIGNMENT_TARGET, "RW": False},
                      {"Source": delivery.result_root,
                       "Destination": runtime.RESULT_TARGET, "RW": True},
                      {"Source": self.target_place,
                       "Destination": oci_delivery.TARGET_TARGET, "RW": True}]
            return {"status": 0,
                    "stdout": json.dumps({"Id": "runtime-" + ATTEMPT,
                                          "State": {"Running": self.running},
                                          "Mounts": mounts}),
                    "stderr": ""}
        return {"status": 0, "stdout": "runtime-" + ATTEMPT, "stderr": ""}

    def delivery(self):
        return runtime.adopt_delivery(self.launch_root, attempt_id=ATTEMPT,
                                      workspace_group=self.owner.group)

    # -- the drivers ---------------------------------------------------------

    def admit(self, port):
        return driver.admit_accepted(
            self.world.coordinator, self.world.manager, self.world.jobs,
            self.world.authority_read, self.world.sessions["verify"],
            self.world.sessions["review"], self.world.sessions["approve"],
            self.world.integrator, port,
            canonical_target_id=self.world.target,
            line_id=self.world.line_id, proposal_id=self.world.proposal_id,
            policy_generation=self.world.authority.policy_generation(),
            profile=self.profile, attempt_id=ATTEMPT,
            launch_root=self.launch_root, workspace_group=self.owner.group,
            required_tests=self.world.required)

    def keep_going(self):
        return driver.continue_accepted(
            self.world.coordinator, self.world.manager, self.world.jobs,
            self.world.authority_read, self.world.sessions["verify"],
            self.world.sessions["review"], self.world.sessions["approve"],
            self.world.integrator,
            canonical_target_id=self.world.target,
            line_id=self.world.line_id, proposal_id=self.world.proposal_id,
            policy_generation=self.world.authority.policy_generation(),
            profile=self.profile, attempt_id=ATTEMPT,
            launch_root=self.launch_root, workspace_group=self.owner.group,
            required_tests=self.world.required)

    def started(self):
        """Prepare, then admit: the deployment's own two calls, in order."""
        held = self.port()
        held.prepare(self.stage(), None)
        answer = self.admit(held)
        return held, answer

    def worker_turn(self, *, behaviour="import"):
        """The REAL entry and workload, over exactly the bound namespaces."""
        import json
        import subprocess
        import sys

        from tests.manager import test_integration_worker as workload_fixture

        worker = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), "..", "worker")
        worker = os.path.normpath(worker)
        if worker not in sys.path:
            sys.path.insert(0, worker)
        import claude_agent
        import integration_entry

        script = os.path.join(self.place("provider"), "provider.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(workload_fixture.PROVIDER_SOURCE)

        def runner(argv, **options):
            return subprocess.run(
                [sys.executable, script, behaviour, argv[-1]],
                capture_output=True, text=True, cwd=options.get("cwd"),
                timeout=300)

        from baton_v12.worker_manager import launch as launch_module

        document = launch_module.launch_document(
            session="integration-session",
            contract="baton.worker-control/1",
            role=integration_worker.LAUNCH_ROLE)
        place = os.path.join(self.place("worker"), "launch.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        os.chmod(place, 0o444)
        delivery = self.delivery()
        bundle = os.path.join(self.root, "bundles", ATTEMPT)
        # THE REVISION THE CANDIDATE WAS REVIEWED AGAINST, read out of the
        # bundle's own eligibility rather than chosen here: the workload
        # refuses a target at any other revision, and a fixture that answered
        # its own idea of one would be proving something about itself.
        import integration_contract

        expected = integration_contract.read_bundle(
            bundle)["envelope"]["eligibility"]["expected_target_revision"]
        return integration_entry.main(
            agent=claude_agent.ClaudeAgent(run=runner,
                                           home=self.place("agent-home")),
            launch_place=place,
            assignment_root=delivery.assignment_root,
            result_root=delivery.result_root,
            bundle_root=bundle,
            target_root=self.target_place,
            scratch=self.place("worker-scratch"),
            revision=lambda place: expected)

    def imported(self):
        whole = os.path.join(self.target_place, self.reviewed)
        with open(whole, "rb") as handle:
            return handle.read(), os.stat(whole).st_mode & 0o777

    # -- the cases -----------------------------------------------------------

    def test_the_start_composes_the_three_binds_and_answers_running(self):
        """Matrix item 2's first half: the port starts the integrator and the
        driver answers `running` -- not an ending, and nothing settled."""
        held, answer = self.started()
        self.assertEqual(answer["outcome"], "running")
        self.assertIsNone(answer["authority_receipt"])
        [run] = [one for one in self.engine_calls if one[1] == "run"]
        bound = []
        for index, word in enumerate(run):
            if word == "--mount":
                members = dict(part.split("=", 1)
                               for part in run[index + 1].split(","))
                bound.append((members["target"],
                              members["readonly"] == "false"))
        self.assertIn((runtime.ASSIGNMENT_TARGET, False), bound)
        self.assertIn((runtime.RESULT_TARGET, True), bound)
        self.assertIn((oci_delivery.TARGET_TARGET, True), bound)
        # THE BUNDLE THE RUNTIME READS EXISTS AND IS BOUND READ-ONLY.
        self.assertIn((source_boundary.SOURCE_TARGET, False), bound)
        self.assertTrue(os.path.isdir(os.path.join(self.root, "bundles",
                                                   ATTEMPT)))
        # AND THE MARKER IS TAKEN, because this execution started it.
        self.assertTrue(held.may_continue(answer["assignment"]))
        self.assertEqual(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"], "running")

    def test_the_start_mounts_this_attempts_own_credential_slot(self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: the composed start
        reached a real engine with NO credential mount in its argv. The
        bearer is synthetic and this deployment's own provider minted it; no
        live credential, secret store or provider is reached."""
        from baton_v12.worker_manager import credentials

        self.started()
        [run] = [one for one in self.engine_calls if one[1] == "run"]
        bound = []
        for index, word in enumerate(run):
            if word == "--mount":
                members = dict(part.split("=", 1)
                               for part in run[index + 1].split(","))
                bound.append((members["source"], members["target"],
                              members["readonly"] == "false"))
        credential = [one for one in bound
                      if one[1].startswith(credentials.CREDENTIAL_ROOT)]
        self.assertTrue(credential, bound)
        # READ-ONLY, and this attempt's own private root rather than the home.
        self.assertFalse(any(one[2] for one in credential))
        for source, _, _ in credential:
            self.assertIn(ATTEMPT, source)
        # THE PROVIDER WAS ASKED EXACTLY ONCE, for the reference the resolved
        # delivery mapped this deployment's `claude` slot to.
        self.assertEqual(self.minted, [("fixture", "kv/claude")])

    def unavailable(self, name, reference):
        raise ContractRefusal("policy", "denied",
                              "the configured credential source refused")

    def test_an_unavailable_credential_refuses_before_writable_exposure(self):
        """W110774 review 2026-09-08T02:53:32Z [P1] moved WHERE this refusal
        lands, and the case moved with it under PLAN item 4's scheduled
        "pre-start refusal ending".

        The bearer is now minted in PREPARATION, before admission takes a
        lease, because a secret source is the one fallible external dependency
        in this composition and a start is not where a deployment may discover
        it is unavailable. So the refusal leaves no lease to strand: no entry,
        no delivery, no engine call, an untouched target, and the accepted
        runtime axis exactly as it was.
        """
        from baton_v12.integration import entries_of

        before = self.target_state()
        held = self.port(credential_provider=self.unavailable)
        with self.assertRaises(ContractRefusal):
            held.prepare(self.stage(), None)
        # NOTHING WAS LEASED AND NOTHING WAS PUBLISHED.
        self.assertEqual(entries_of(self.world.coordinator,
                                    self.world.target), [])
        self.assertIsNone(self.delivery())
        self.assertEqual([one for one in self.engine_calls
                          if one[1] == "run"], [])
        self.assertEqual(self.target_state(), before)
        self.assertFalse(held.may_continue(self.assignment()))
        # AND THE ACCEPTED AXIS STILL SAYS `not-started`, which is the positive
        # statement a successor needs rather than an unaccountable one.
        self.assertEqual(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"], "not-started")

    def test_a_failed_preparation_leaves_the_successor_boundary_intact(self):
        """The other half of acceptance matrix item 6: a pre-mutation refusal
        must preserve the target AND leave the accepted reconciliation state a
        later writer is admitted behind.

        `refresh` is the only public way this port touches that axis, and it
        now REFUSES to reconcile an attempt no start was ever requested for --
        reconciliation would answer that it can name no runtime, record
        `uncertain`, and destroy the very evidence the predecessor gate reads.
        Nothing here invents quiescence or retries an uncertain runtime: the
        proof is that the same attempt, prepared again with a working
        provider, goes on to complete the whole integration.
        """
        held = self.port(credential_provider=self.unavailable)
        with self.assertRaises(ContractRefusal):
            held.prepare(self.stage(), None)
        caught = self.refused(held.refresh, ATTEMPT)
        self.assertIn("no requested runtime to reconcile", caught.message)
        self.assertEqual(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"], "not-started")

        # THE SUCCESSOR BOUNDARY, PROVED BY USING IT.
        working, answer = self.started()
        self.assertEqual(answer["outcome"], "running")
        self.assertEqual(self.worker_turn(), 0)
        self.running = False
        working.refresh(ATTEMPT)
        self.assertEqual(self.keep_going()["outcome"], "integrated")
        self.assertEqual(self.imported(), (self.CANDIDATE, 0o644))

    def test_the_whole_path_imports_settles_and_releases_in_order(self):
        """THE ORDINARY ENDING, end to end: a real worker turn imports the
        reviewed bytes, the runtime stops, and continuation writes the
        Authority receipt BEFORE the coordinator settles and releases."""
        from baton_v12.integration import entries_of, lease_of, target_of

        held, answer = self.started()
        self.assertEqual(answer["outcome"], "running")
        # STILL PENDING WHILE THE WRITER IS UP, whatever is on disk.
        self.assertEqual(self.keep_going()["outcome"], "running")

        self.assertEqual(self.worker_turn(), 0)
        imported, mode = self.imported()
        self.assertEqual(imported, self.CANDIDATE)
        self.assertEqual(mode, 0o644)
        # A COMPLETE RESULT BEHIND A LIVE WRITER IS NOT AN ENDING.
        pending = self.keep_going()
        self.assertEqual(pending["outcome"], "running")
        self.assertEqual(
            lease_of(self.world.coordinator,
                     answer["assignment"]["lease_id"])["state"], "live")

        # THE CONTAINER ENDS, and the manager OBSERVES it rather than being
        # told: `refresh` reconciles through the port's own adapter.
        self.running = False
        self.assertIsNotNone(held.refresh(ATTEMPT))
        self.assertIn(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"],
            runtime.QUIESCENT_STATES)

        order = []
        real_receipt = driver._integrate_receipt
        real_complete = driver.execution.complete_integrated

        def receipt(*operands, **named):
            order.append("receipt")
            return real_receipt(*operands, **named)

        def complete(*operands, **named):
            order.append("complete")
            return real_complete(*operands, **named)

        with mock.patch.object(driver, "_integrate_receipt", receipt), \
                mock.patch.object(driver.execution, "complete_integrated",
                                  complete):
            ended = self.keep_going()
        self.assertEqual(ended["outcome"], "integrated")
        # THE ORDERING THE COORDINATOR REQUIRES, measured rather than assumed.
        self.assertEqual(order, ["receipt", "complete"])
        self.assertIsNotNone(ended["authority_receipt"])
        [entry] = [one for one in entries_of(self.world.coordinator,
                                             self.world.target)
                   if one["entry_id"] == ended["entry"]]
        self.assertEqual(entry["state"], "integrated")
        self.assertEqual(
            lease_of(self.world.coordinator,
                     answer["assignment"]["lease_id"])["state"], "released")
        self.assertEqual(target_of(self.world.coordinator,
                                   self.world.target)["state"], "open")
        # AND THE TARGET STILL HOLDS THE CANDIDATE'S OWN BYTES.
        self.assertEqual(self.imported(), (self.CANDIDATE, 0o644))

    def test_a_repeated_tick_after_completion_duplicates_nothing(self):
        """Matrix item 3: repeated ticks cannot duplicate a start, a receipt,
        a settlement or a release.

        TIGHTENED under owner ruling M115526, which approved requiring the
        correct terminal answer instead of tolerating a refusal. It was
        written permissively because the release-tail defect made a later
        tick refuse at the immutable approval receipt; with that corrected,
        the driver replays `integrated` and this says so.
        """
        from baton_v12.integration import entries_of, lease_of

        held, answer = self.started()
        self.assertEqual(self.worker_turn(), 0)
        self.running = False
        held.refresh(ATTEMPT)
        first = self.keep_going()
        self.assertEqual(first["outcome"], "integrated")
        receipts = [one for one in
                    self.world.publisher.receipts(self.world.proposal_id)
                    if one.get("kind") == "integration"]
        self.assertEqual(len(receipts), 1)

        for _ in range(2):
            again = self.keep_going()
            self.assertEqual(again["outcome"], "integrated")
            self.assertIsNotNone(again["authority_receipt"])
        # NOTHING MOVED: one engine start, one integration receipt, the entry
        # still integrated and its lease still released.
        self.assertEqual(
            len([one for one in self.engine_calls if one[1] == "run"]), 1)
        self.assertEqual(
            [one for one in
             self.world.publisher.receipts(self.world.proposal_id)
             if one.get("kind") == "integration"], receipts)
        [entry] = [one for one in entries_of(self.world.coordinator,
                                             self.world.target)
                   if one["entry_id"] == first["entry"]]
        self.assertEqual(entry["state"], "integrated")
        self.assertEqual(
            lease_of(self.world.coordinator,
                     answer["assignment"]["lease_id"])["state"], "released")
        self.assertEqual(self.imported(), (self.CANDIDATE, 0o644))

    def test_a_settled_entry_replays_its_live_release_tail(self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: SETTLEMENT AND RELEASE
        ARE TWO DURABLE ACTS, and a process can die between them.

        Both entry points wrote the accepted receipts before dispatching a
        settled entry to the terminal owner, and an accepted receipt is
        immutable -- so every later tick refused at the approval receipt and
        the integrated entry kept its live exclusion forever. The interruption
        is injected at `release_lease` alone, after the real receipt and the
        real settlement, which is exactly the window the contract names.
        """
        from baton_v12.integration import entries_of, lease_of

        held, answer = self.started()
        self.assertEqual(self.worker_turn(), 0)
        self.running = False
        held.refresh(ATTEMPT)
        lease = answer["assignment"]["lease_id"]
        with mock.patch.object(
                driver.execution, "release_lease",
                side_effect=ContractRefusal("integrity", "schema",
                                            "the injected interruption")):
            with self.assertRaises(ContractRefusal):
                self.keep_going()
        # THE STRANDED STATE THE PROBE MEASURED: settled, and still excluding
        # every later writer.
        [entry] = [one for one in entries_of(self.world.coordinator,
                                             self.world.target)
                   if one["entry_id"] == answer["entry"]]
        self.assertEqual(entry["state"], "integrated")
        self.assertEqual(lease_of(self.world.coordinator, lease)["state"],
                         "live")

        # AND THE REPLAY DRAINS IT, through the driver's own terminal owner,
        # reading the existing Authority receipt rather than reissuing one.
        drained = self.keep_going()
        self.assertEqual(drained["outcome"], "integrated")
        self.assertIsNotNone(drained["authority_receipt"])
        self.assertEqual(lease_of(self.world.coordinator, lease)["state"],
                         "released")
        self.assertEqual(self.imported(), (self.CANDIDATE, 0o644))

    def test_a_reconstructed_port_also_drains_that_release_tail(self):
        """The same tail, reached through admission after a restart: a new
        incarnation holds no marker and must still be able to finish this."""
        from baton_v12.integration import lease_of

        held, answer = self.started()
        self.assertEqual(self.worker_turn(), 0)
        self.running = False
        held.refresh(ATTEMPT)
        lease = answer["assignment"]["lease_id"]
        with mock.patch.object(
                driver.execution, "release_lease",
                side_effect=ContractRefusal("integrity", "schema",
                                            "the injected interruption")):
            with self.assertRaises(ContractRefusal):
                self.keep_going()
        drained = self.admit(self.port())
        self.assertEqual(drained["outcome"], "integrated")
        self.assertEqual(lease_of(self.world.coordinator, lease)["state"],
                         "released")
        # ONE START EVER: a terminal replay starts no writer.
        self.assertEqual(
            len([one for one in self.engine_calls if one[1] == "run"]), 1)

    def test_a_repeated_tick_replays_the_terminal_answer(self):
        """ADDITIVE, and deliberately stricter than the existing repeated-tick
        case, which tolerates a refusal: with the release tail corrected, a
        later tick REPLAYS `integrated` and writes nothing new. The looser case
        is left exactly as it is pending the owner's test-scope ruling."""
        from baton_v12.integration import lease_of

        held, answer = self.started()
        self.assertEqual(self.worker_turn(), 0)
        self.running = False
        held.refresh(ATTEMPT)
        self.assertEqual(self.keep_going()["outcome"], "integrated")
        receipts = [one for one in
                    self.world.publisher.receipts(self.world.proposal_id)
                    if one.get("kind") == "integration"]
        for _ in range(2):
            again = self.keep_going()
            self.assertEqual(again["outcome"], "integrated")
            self.assertIsNotNone(again["authority_receipt"])
        self.assertEqual(
            [one for one in
             self.world.publisher.receipts(self.world.proposal_id)
             if one.get("kind") == "integration"], receipts)
        self.assertEqual(
            lease_of(self.world.coordinator,
                     answer["assignment"]["lease_id"])["state"], "released")
        self.assertEqual(
            len([one for one in self.engine_calls if one[1] == "run"]), 1)

    def test_a_reconstructed_incarnation_holds_and_starts_no_second_writer(
            self):
        """Matrix item 5: a new serving execution that finds a started
        delivery takes the existing hold and never runs a second writer."""
        self.started()
        self.assertEqual(self.worker_turn(), 0)
        fresh = self.port()
        self.assertFalse(fresh.may_continue(
            runtime.published_assignment(self.delivery())))
        answer = self.admit(fresh)
        self.assertEqual(answer["outcome"], "held")
        self.assertEqual(
            len([one for one in self.engine_calls if one[1] == "run"]), 1)

    def test_an_uncertain_reconciliation_revokes_this_executions_marker(self):
        """W110774 review 2026-09-08T02:07:47Z [P1]: the marker survived the
        exact event meant to revoke it, because the member this tested is not
        one a public reconciliation document carries."""
        from baton_v12.worker_manager import documents

        held, answer = self.started()
        self.assertTrue(held.may_continue(answer["assignment"]))
        shapes = [documents.runtime_uncertain(attempt_id=ATTEMPT,
                                              decision="uncertain",
                                              why="nothing could be named"),
                  {"decision": "attached", "runtime_id": "runtime-" + ATTEMPT,
                   "observed": "uncertain", "why": "inconclusive"}]
        for shape in shapes:
            with self.subTest(decision=shape["decision"]):
                held._live[ATTEMPT] = {
                    "assignment": dict(answer["assignment"]),
                    "delivery_root": self.launch_root,
                    "bundle_digest": "sha256:" + "3" * 64}
                with mock.patch.object(integration_worker,
                                       "reconcile_runtime",
                                       return_value=shape):
                    held.refresh(ATTEMPT)
                self.assertFalse(held.may_continue(answer["assignment"]))

    def test_a_failed_observation_construction_revokes_the_marker(self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: the adapter was composed
        BEFORE the invalidation boundary, so a failure adopting the delivery,
        nominating the target or composing the plan left continuation
        permission standing. The nominated directory is moved aside and put
        back by this case; nothing outside its own disposable root changes.
        """
        held, answer = self.started()
        self.assertTrue(held.may_continue(answer["assignment"]))
        moved = self.target_place + "-moved"
        os.rename(self.target_place, moved)
        try:
            with self.assertRaises(ContractRefusal):
                held.refresh(ATTEMPT)
        finally:
            os.rename(moved, self.target_place)
        self.assertFalse(held.may_continue(answer["assignment"]))
        # AND OBSERVATION STILL WORKS once the configuration is sound again:
        # losing permission is not losing the ability to look.
        self.assertEqual(
            held.observed(ATTEMPT, answer["assignment"])["execution_runtime"],
            "running")

    def test_a_preparation_after_a_start_refuses_and_keeps_its_custody(self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: preparation discarded
        whatever credential root it found, so repeating it against a RUNNING
        attempt asked the provider again and destroyed the custody that
        runtime holds. `discard_orphan` requires its caller to prove the root
        stale, and having no in-memory delivery is not that proof.
        """
        self.started()
        self.assertEqual(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"], "running")
        minted = len(self.minted)
        state = self.credential_home.read_state(ATTEMPT)
        self.assertTrue(os.path.lexists(
            self.credential_home.volatile_root(ATTEMPT)))

        # A SECOND INCARNATION holds no delivery for this attempt.
        caught = self.refused(self.port().prepare, self.stage(), None)
        self.assertIn("has not started", caught.message)
        # NOTHING WAS ASKED AND NOTHING WAS DISCARDED.
        self.assertEqual(len(self.minted), minted)
        self.assertEqual(self.credential_home.read_state(ATTEMPT), state)
        self.assertTrue(os.path.lexists(
            self.credential_home.volatile_root(ATTEMPT)))
        self.assertEqual(
            attempt_runtime_of(self.world.manager,
                               ATTEMPT)["execution_runtime"], "running")

    def test_a_failed_witness_read_during_refresh_revokes_the_marker(self):
        """W110774 review 2026-09-08T02:29:59Z [P1]: the no-start preflight
        was added in FRONT of the invalidation boundary, so a witness read
        that raised left continuation permission standing -- the same leak the
        boundary was introduced to close."""
        held, answer = self.started()
        self.assertTrue(held.may_continue(answer["assignment"]))
        with mock.patch.object(
                integration_worker.runtime, "prior_runtime_witness",
                side_effect=ContractRefusal("policy", "denied",
                                            "the witness cannot be read")):
            with self.assertRaises(ContractRefusal):
                held.refresh(ATTEMPT)
        self.assertFalse(held.may_continue(answer["assignment"]))

    def test_observation_survives_a_lost_marker(self):
        """Restart observation stays possible while continuation does not."""
        held, answer = self.started()
        held.forget(ATTEMPT)
        seen = held.observed(ATTEMPT, answer["assignment"])
        self.assertEqual(seen["execution_runtime"], "running")
        self.assertIsNotNone(seen["delivery"])
        self.assertFalse(seen["continuable"])


if __name__ == "__main__":
    unittest.main()
