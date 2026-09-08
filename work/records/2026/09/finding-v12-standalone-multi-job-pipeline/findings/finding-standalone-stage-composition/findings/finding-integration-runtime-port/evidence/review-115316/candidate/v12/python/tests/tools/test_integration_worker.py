"""W110774: the production integration runtime port.

`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/
finding-standalone-stage-composition/findings/finding-integration-runtime-port/`.

WHAT THIS FILE OWNS TODAY. The deployment composer's CONFIGURATION and its
REFUSALS: what it will not be constructed from, the manager attempt it prepares
through public owners before admission asks for a runtime, everything `run`
refuses before any engine is reached or any target byte is exposed, and the
live continuation marker's own rules.

WHAT IT DOES NOT YET COVER, stated here rather than left to be discovered: the
composed start through the real mount boundary and `OciAdapter.start`, the real
worker turn over the delivery, and the settlement/release ordering behind a
quiescent runtime. That proof is required by this Work's review and is not
supplied by this module yet; PROGRESS says so in the same words.

THE OWNERS ARE REAL. The manager store, the offer/claim lifecycle, the
attempt record and its activation, the accepted evidence producer and the
integration profile are the actual ones; what is deterministic is the ENGINE,
which is a recording callable that no case here reaches, and that is the point
of the refusal cases.
"""

import copy
import os
import shutil
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
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
        roots = {"inputs": self.place("r-inputs"),
                 "workspace": self.place("r-workspace")}
        os.chown(roots["workspace"], -1, self.owner.group.gid)
        os.chmod(roots["workspace"], 0o2770)
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
            "canonical_target": self.target_place,
            "instructions": INSTRUCTIONS,
            "identity": {"image_digest": IMAGE,
                         "profile_digest": self.profile_digest,
                         "policy_digest": self.policy_digest,
                         "adapter_digest": self.adapter_digest},
            "adapter_name": "acp", "input_digest": self.input_digest,
            "toolchain_digest": TOOLCHAIN,
            "engine": "docker", "engine_run": self.engine_run,
            "roots": roots, "workspace_group": self.owner.group,
            "capacity": source_boundary.workspace_capacity(1 << 30),
            "bundle_home": self.place("bundles"),
            "launch_home": self.place("launch-home"),
            "launch_session": "integration-session",
            "launch_contract": "baton.worker-control/1"}
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
        self.assertEqual(sorted(held._roots), ["inputs", "workspace"])
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

    def test_roots_that_are_not_this_deployments_directories_refuse(self):
        caught = self.refused(self.port, roots={"inputs": "/nope",
                                                "workspace": "/nope"})
        self.assertIn("not a directory this deployment provisioned",
                      caught.message)
        self.refused(self.port, roots={"inputs": self.place("i")})

    def test_a_relative_or_absent_canonical_target_refuses(self):
        self.refused(self.port, canonical_target="relative/target")
        self.refused(self.port,
                     canonical_target=os.path.join(self.root, "absent"))

    def test_instruction_bytes_are_bytes_this_deployment_configured(self):
        self.refused(self.port, instructions="not bytes")
        self.refused(self.port, instructions=b"")

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

    def test_a_status_read_needs_this_executions_own_delivery_root(self):
        caught = self.refused(self.port().observed, ATTEMPT,
                              self.assignment())
        self.assertIn("holds no delivery root", caught.message)


if __name__ == "__main__":
    unittest.main()
