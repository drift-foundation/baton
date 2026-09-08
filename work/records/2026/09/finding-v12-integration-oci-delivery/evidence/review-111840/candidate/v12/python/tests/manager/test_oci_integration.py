"""W110934: the fenced integration mount boundary at the real OCI seam.

`work/records/2026/09/finding-v12-integration-oci-delivery/`.

WHAT THIS FILE OWNS. The three fixed binds an integration runtime is started
over, everything that refuses before the engine is asked, the immutable binding
companion, the final pre-run proof, and the observed-mount adoption. It drives
the REAL `run_vector` and the REAL `OciAdapter.start` with a deterministic
engine seam; no daemon, no provider, no network and no canonical-target
mutation.

WHAT IT DOES NOT RE-PROVE. The grant, the assignment, the delivery namespaces
and the nominated-source rules have their own suites and their own owners;
this composes them. A second set of assertions over the same rules would be a
second place for them to drift.
"""

import json
import os
import stat
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import oci_delivery, runtime
from baton_v12.integration.queue import block_target
from baton_v12.worker_manager import launch, oci
from baton_v12.worker_manager.source_boundary import nominate_source

from tests.integration.test_runtime import (PARTICIPANT, RuntimeCase,
                                            _group_of, profile)
from tests.integration.fixtures import TARGET


IMAGE = "sha256:" + "a" * 64
# THE CANONICAL LABEL SET, taken from `test_oci`'s own rather than
# re-invented: the contract's member list is closed and a second spelling of it
# is a second thing to keep true.
LABELS = {"runtime_attempt_id": "attempt-1",
          "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
          "work_id": "2b077949-W4", "participant": PARTICIPANT,
          "generation": 1,
          "principal": "principal:org-a",
          "effective_scope": "scope:deployment",
          "profile_digest": "sha256:" + "b" * 64,
          "policy_digest": "sha256:" + "d" * 64,
          "adapter_digest": "sha256:" + "c" * 64}


class MountCase(RuntimeCase):
    """One live grant, one published assignment, one nominated target."""

    def setUp(self):
        super().setUp()
        self.assignment = self.compose()
        self.launch = os.path.join(self.root, "launch")
        os.makedirs(self.launch)
        self.delivery = runtime.materialize_delivery(
            self.launch, attempt_id="attempt-1",
            workspace_group=_group_of(self))
        runtime.publish_assignment(self.delivery, self.assignment)
        self.canonical = os.path.join(self.root, "canonical-target")
        os.makedirs(self.canonical)
        # THE POSTURE A DEPLOYMENT PROVISIONS. Composition proves it now, so a
        # fixture that skipped it would be measuring that proof rather than
        # whatever the case is about; the cases that WANT an incompatible
        # target set it deliberately.
        self.provisioned()
        self.target = oci_delivery.integration_target(
            TARGET, nominate_source(self.canonical))

    def provisioned(self, mode=0o2770):
        os.chown(self.canonical, -1, _group_of(self).gid)
        os.chmod(self.canonical, mode)

    def boundary(self, **changed):
        operands = {"profile": profile(), "delivery": self.delivery,
                    "assignment": self.assignment, "target": self.target,
                    "workspace_group": _group_of(self)}
        operands.update(changed)
        return oci_delivery.compose_mount_boundary(
            self.coordinator, self.manager, **operands)

    def refused(self, action, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            action(*operands, **named)
        return caught.exception

    def block(self):
        """Hold this target's leased entry, which is what ends the grant."""
        return block_target(
            self.coordinator, canonical_target_id=TARGET, entry_id="entry-1",
            lease_id="lease-1", fence=self.fence,
            reason="runtime-interrupted",
            detail={"observed": "the operator blocked it",
                    "attempt_id": "attempt-1"})

    def mounts_of(self, argv):
        """Every `--mount` this vector composed, as parsed triples."""
        found = []
        for index, word in enumerate(argv):
            if word != "--mount":
                continue
            members = dict(part.split("=", 1)
                           for part in argv[index + 1].split(","))
            found.append((members["source"], members["target"],
                          members["readonly"] == "false"))
        return found


class TheThreeBindsAreFixedAndTyped(MountCase):

    def test_the_boundary_composes_exactly_the_three_fixed_mounts(self):
        composed = oci_delivery.boundary_mounts(self.boundary())
        self.assertEqual(
            [(one[1], one[2]) for one in composed],
            [(runtime.ASSIGNMENT_TARGET, False),
             (runtime.RESULT_TARGET, True),
             (oci_delivery.TARGET_TARGET, True)])
        self.assertEqual([one[0] for one in composed],
                         [self.delivery.assignment_root,
                          self.delivery.result_root, self.canonical])

    def test_the_container_target_collides_with_no_existing_fixed_one(self):
        """The both-directions check the plan requires can only mean something
        against a target that is genuinely free."""
        from baton_v12.worker_manager import credentials, launch as launch_mod
        from baton_v12.worker_manager import source_boundary
        others = [oci.INPUT_TARGET, source_boundary.SOURCE_TARGET,
                  source_boundary.WORKSPACE_TARGET,
                  source_boundary.SCRATCH_TARGET,
                  source_boundary.SHARED_MEMORY_TARGET,
                  launch_mod.LAUNCH_TARGET, credentials.CREDENTIAL_ROOT,
                  runtime.ASSIGNMENT_TARGET, runtime.RESULT_TARGET]
        held = oci_delivery.TARGET_TARGET
        for one in others:
            with self.subTest(other=one):
                self.assertNotEqual(held, one)
                self.assertFalse(one.startswith(held.rstrip("/") + "/"))
                self.assertFalse(held.startswith(one.rstrip("/") + "/"))

    def test_a_mapping_or_a_triple_never_authorizes_a_bind(self):
        for supplied in ({"target": "/target"},
                         [(self.canonical, "/target", True)],
                         self.delivery, "/target"):
            with self.subTest(supplied=type(supplied).__name__):
                caught = self.refused(oci._integration_mounts, supplied)
                self.assertEqual((caught.category, caught.code),
                                 ("policy", "denied"))

    def test_the_boundary_cannot_be_constructed_directly(self):
        self.refused(oci_delivery.IntegrationMountBoundary, attempt_id="x")
        self.refused(oci_delivery.IntegrationTarget, TARGET, None)

    def test_a_target_is_a_proved_directory_and_not_a_path(self):
        caught = self.refused(oci_delivery.integration_target, TARGET,
                              self.canonical)
        self.assertEqual(caught.code, "denied")


class TheVectorCarriesThemAndNothingElseMoves(MountCase):

    def vector(self, **changed):
        operands = {"engine": "docker", "image_digest": IMAGE,
                    "labels": LABELS, "assignment_roots": self.roots(),
                    "posture": "execution", "name": "runtime-1",
                    "workspace_group": _group_of(self),
                    "integration_delivered": self.boundary()}
        operands.update(changed)
        engine = operands.pop("engine")
        return oci.run_vector(engine, **operands)

    def roots(self):
        inputs = os.path.join(self.root, "roots", "inputs")
        workspace = os.path.join(self.root, "roots", "workspace")
        for place in (inputs, workspace):
            os.makedirs(place, exist_ok=True)
        return {"inputs": inputs, "workspace": workspace}

    def test_the_three_binds_reach_the_argv_with_their_exact_access(self):
        found = self.mounts_of(self.vector())
        self.assertIn((self.delivery.assignment_root,
                       runtime.ASSIGNMENT_TARGET, False), found)
        self.assertIn((self.delivery.result_root, runtime.RESULT_TARGET, True),
                      found)
        self.assertIn((self.canonical, oci_delivery.TARGET_TARGET, True),
                      found)

    def test_an_ordinary_vector_composes_exactly_what_it_did_before(self):
        """Default absent, so every existing worker start is untouched."""
        self.assertEqual(self.mounts_of(self.vector(
            integration_delivered=None)), [])

    def test_the_image_is_still_last(self):
        self.assertEqual(self.vector()[-1], IMAGE)

    def test_an_ordinary_mount_can_never_land_at_or_under_the_target(self):
        """`/target` is a short path near the root, which is why this family
        asks the containment question in BOTH directions -- and why that check
        is a SECOND fence rather than the only one.

        Reported as measured rather than as designed: an ordinary mount cannot
        reach `/target` at all, because `_mounts` confines every one to the two
        assignment roots' fixed targets and refuses this before the integration
        family is composed. So the both-directions loop in `run_vector` is
        currently unreachable through the accepted families, and this case
        records that fact instead of contriving a collision the public surface
        cannot produce."""
        for target in (oci_delivery.TARGET_TARGET,
                       oci_delivery.TARGET_TARGET + "/deep"):
            with self.subTest(target=target):
                held = self.refused(self.vector, mounts=[
                    {"source": "inputs", "target": target,
                     "writable": False}])
                self.assertEqual(held.category, "integrity")


class TheFamilyIsExecutionOnlyAndBoundToItsGrant(MountCase):
    """P1 (review 2026-09-07T16-04-48Z): three probes that reached a run.

    A consent runtime started with writable result and target binds; one
    engine runtime started labelled `baton.foreign` under a grant held by
    somebody else; and one host directory bound writable at `/output` and
    writable at `/target`.
    """

    def roots(self):
        inputs = os.path.join(self.root, "e-inputs")
        workspace = os.path.join(self.root, "e-workspace")
        for place in (inputs, workspace):
            os.makedirs(place, exist_ok=True)
        os.chown(workspace, -1, _group_of(self).gid)
        os.chmod(workspace, 0o2770)
        return {"inputs": inputs, "workspace": workspace}

    def test_a_consent_vector_never_carries_an_integration_bind(self):
        caught = self.refused(
            oci.run_vector, "docker", image_digest=IMAGE, labels=LABELS,
            assignment_roots=self.roots(), posture="consent",
            name="runtime-1", integration_delivered=self.boundary())
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertIn("consent runtime mounts nothing", caught.message)

    def test_a_consent_adapter_refuses_at_construction(self):
        caught = self.refused(
            oci.OciAdapter, "docker", lambda *a, **k: None,
            identity={"image_digest": IMAGE,
                      "profile_digest": LABELS["profile_digest"],
                      "policy_digest": LABELS["policy_digest"],
                      "adapter_digest": LABELS["adapter_digest"]},
            assignment_roots=self.roots(), posture="consent",
            integration_delivery=self.boundary())
        self.assertEqual(caught.code, "denied")

    def test_a_start_for_another_participant_never_reaches_the_engine(self):
        """The boundary comparing its own assignment against a fresh
        composition through its own profile is the document agreeing with
        itself; nothing asked who this start was for."""
        calls = []

        def engine_run(argv, **options):
            calls.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}

        home = os.path.join(self.root, "foreign-launch")
        os.makedirs(home, exist_ok=True)
        held = oci.OciAdapter(
            "docker", engine_run,
            identity={"image_digest": IMAGE,
                      "profile_digest": LABELS["profile_digest"],
                      "policy_digest": LABELS["policy_digest"],
                      "adapter_digest": LABELS["adapter_digest"]},
            assignment_roots=self.roots(), posture="execution",
            integration_delivery=self.boundary(),
            launch_delivery=launch.materialize(
                home, attempt_id="attempt-1", session="session-1",
                contract="exercise the integration boundary",
                role="integration"),
            workspace_group=_group_of(self))
        caught = self.refused(
            held.start, {"labels": dict(LABELS, participant="baton.foreign"),
                         "operation_id": "start-1"})
        self.assertIn("runs under the grant it was given", caught.message)
        self.assertEqual([one for one in calls if one[1] == "run"], [])

    def test_the_ordinary_families_compose_beside_the_integration_one(self):
        """P1 (review 2026-09-07T16-34-08Z): the overlap rule compared every
        pair in the concatenation, so a valid `/output` bind collided with its
        own workspace root -- the same authorized root represented twice, not
        aliasing. Empty ordinary mounts could not have caught it."""
        roots = self.roots()
        source = os.path.join(self.root, "nominated-evidence")
        os.makedirs(source, exist_ok=True)
        argv = oci.run_vector(
            "docker", image_digest=IMAGE, labels=LABELS,
            assignment_roots=roots, posture="execution", name="runtime-1",
            workspace_group=_group_of(self),
            mounts=[{"source": roots["workspace"], "target": "/output",
                     "writable": True},
                    {"source": roots["inputs"], "target": "/input",
                     "writable": False}],
            integration_delivered=self.boundary())
        found = self.mounts_of(argv)
        self.assertIn((os.path.realpath(roots["workspace"]), "/output", True),
                      found)
        self.assertIn((os.path.realpath(roots["inputs"]), "/input", False),
                      found)
        self.assertIn((self.canonical, oci_delivery.TARGET_TARGET, True),
                      found)
        del source

    def test_a_target_that_is_the_workspace_refuses(self):
        """One host directory behind two container names, with the ordinary
        workspace rules applying to one of them and none of them applying to
        the other."""
        roots = self.roots()
        aliased = oci_delivery.integration_target(
            TARGET, nominate_source(roots["workspace"]))
        caught = self.refused(
            oci.run_vector, "docker", image_digest=IMAGE, labels=LABELS,
            assignment_roots=roots, posture="execution", name="runtime-1",
            workspace_group=_group_of(self),
            integration_delivered=self.boundary(target=aliased))
        self.assertIn("two container paths", caught.message)

    def test_a_target_containing_this_manager_s_own_roots_refuses_earlier(
            self):
        """A target that swallows the delivery is refused at COMPOSITION,
        before a vector is asked for -- the earliest of the two fences."""
        above = os.path.dirname(self.delivery.root)
        os.chown(above, -1, _group_of(self).gid)
        os.chmod(above, 0o2770)
        caught = self.refused(
            self.boundary,
            target=oci_delivery.integration_target(TARGET,
                                                   nominate_source(above)))
        self.assertIn("two container paths", caught.message)


class TheCompositionRefusesBeforeAnythingIsBound(MountCase):

    def test_a_blocked_grant_refuses(self):
        self.block()
        self.refused(self.boundary)

    def test_an_assignment_for_another_attempt_refuses(self):
        other = dict(self.assignment, attempt_id="attempt-9")
        self.refused(self.boundary, assignment=other)

    def test_an_assignment_naming_another_target_refuses(self):
        other = dict(self.assignment, canonical_target_id="target-9")
        self.refused(self.boundary, assignment=other)

    def test_a_profile_wiring_other_instructions_refuses(self):
        other = profile(instructions_digest="sha256:" + "e" * 64)
        caught = self.refused(self.boundary, profile=other)
        self.assertEqual(caught.code, "denied")

    def test_an_unpublished_assignment_refuses(self):
        os.unlink(os.path.join(self.delivery.assignment_root,
                               runtime.ASSIGNMENT_DOCUMENT))
        caught = self.refused(self.boundary)
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))

    def test_a_published_assignment_that_is_not_this_one_refuses(self):
        """The WHOLE document is compared: an old assignment stays readable
        after the grant that authorized it ended."""
        place = os.path.join(self.delivery.assignment_root,
                             runtime.ASSIGNMENT_DOCUMENT)
        os.chmod(place, 0o644)
        with open(place, "wb") as writing:
            writing.write(json.dumps(
                dict(self.assignment, entry_id="entry-9"),
                sort_keys=True, separators=(",", ":")).encode("utf-8"))
        self.refused(self.boundary)

    def test_a_target_replaced_after_nomination_refuses(self):
        os.rename(self.canonical, self.canonical + "-gone")
        os.makedirs(self.canonical)
        caught = self.refused(self.boundary)
        self.assertIn("no longer the directory", caught.message)

    def test_a_target_that_is_a_link_is_never_nominated(self):
        """Refused by the accepted nominator, which is the right owner: a link
        at the name is a directory somebody else chose."""
        place = os.path.join(self.root, "linked-target")
        os.symlink(self.canonical, place)
        self.refused(nominate_source, place)

    def test_a_target_inside_a_namespace_refuses_as_an_overlap(self):
        inside = os.path.join(self.delivery.result_root, "nested")
        os.makedirs(inside)
        caught = self.refused(
            self.boundary,
            target=oci_delivery.integration_target(TARGET,
                                                   nominate_source(inside)))
        self.assertIn("two container paths", caught.message)


class TheBindingCompanionIsImmutableAndPrivate(MountCase):

    def place(self):
        return os.path.join(self.delivery.root, oci_delivery.BINDING_DOCUMENT)

    def test_it_is_written_beside_the_namespaces_and_never_inside_one(self):
        self.boundary()
        self.assertTrue(os.path.isfile(self.place()))
        for root in (self.delivery.assignment_root,
                     self.delivery.result_root):
            self.assertFalse(os.path.exists(
                os.path.join(root, oci_delivery.BINDING_DOCUMENT)))

    def test_it_records_the_closed_members_and_no_runtime_state(self):
        self.boundary()
        with open(self.place(), encoding="utf-8") as handle:
            held = json.load(handle)
        self.assertEqual(sorted(held), sorted(oci_delivery.BINDING_MEMBERS))
        self.assertEqual(held["schema"], oci_delivery.BINDING_SCHEMA)
        self.assertEqual(held["attempt_id"], "attempt-1")
        self.assertEqual(held["canonical_target_id"], TARGET)
        self.assertEqual(len(held["sources"]), 3)
        for one in held["sources"]:
            self.assertEqual(sorted(one),
                             sorted(oci_delivery.SOURCE_MEMBERS))
        self.assertNotIn("runtime_id", json.dumps(held))

    def test_composing_twice_replays_the_identical_binding(self):
        self.boundary()
        with open(self.place(), "rb") as handle:
            first = handle.read()
        self.boundary()
        with open(self.place(), "rb") as handle:
            self.assertEqual(handle.read(), first)

    def test_a_conflicting_retained_binding_is_an_inspectable_refusal(self):
        """Never reconstructed as though it had always been this plan: what the
        old container was given is the evidence an operator needs."""
        self.boundary()
        with open(self.place(), encoding="utf-8") as handle:
            held = json.load(handle)
        held["sources"][2]["host_source"] = "/somewhere/else"
        # REWRITTEN AT THE PUBLISHED MODE, so this case measures the CONTENT
        # comparison rather than the mode proof beside it; the mode has its
        # own case.
        os.chmod(self.place(), 0o644)
        with open(self.place(), "w", encoding="utf-8") as handle:
            json.dump(held, handle, sort_keys=True, separators=(",", ":"))
        os.chmod(self.place(), 0o444)
        caught = self.refused(self.boundary)
        self.assertIn("returned for inspection", caught.message)

    def test_a_binding_whose_mode_moved_is_not_the_one_it_wrote(self):
        self.boundary()
        os.chmod(self.place(), 0o644)
        caught = self.refused(self.boundary)
        self.assertIn("mode", caught.message)


class TheFinalProofIsAskedImmediatelyBeforeTheEngine(MountCase):

    homes = []

    def adapter(self, engine_run, **changed):
        roots = {"inputs": os.path.join(self.root, "r-inputs"),
                 "workspace": os.path.join(self.root, "r-workspace")}
        for place in roots.values():
            os.makedirs(place, exist_ok=True)
        # THE WORKSPACE POSTURE THE ACCEPTED PREFLIGHT REQUIRES, established by
        # the fixture rather than asserted here: `_prove_execution_workspace`
        # is `workspaces`' own rule and this case is about the integration
        # family, not a second account of that one.
        os.chown(roots["workspace"], -1, _group_of(self).gid)
        os.chmod(roots["workspace"], 0o2770)
        # THE LAUNCH DOCUMENT IS REQUIRED AT START and is not this Work's
        # subject; it is materialized so the case measures the integration
        # boundary rather than the adapter's existing launch refusal.
        home = os.path.join(self.root, f"launch-home-{len(self.homes)}")
        os.makedirs(home, exist_ok=True)
        self.homes.append(home)
        operands = {"identity": {"image_digest": IMAGE,
                                 "profile_digest": LABELS["profile_digest"],
                                 "policy_digest": LABELS["policy_digest"],
                                 "adapter_digest": LABELS["adapter_digest"]},
                    "assignment_roots": roots, "posture": "execution",
                    "launch_delivery": launch.materialize(
                        home, attempt_id="attempt-1", session="session-1",
                        contract="exercise the integration boundary",
                        role="integration"),
                    "workspace_group": _group_of(self)}
        operands.update(changed)
        # THE DEFAULT BOUNDARY IS COMPOSED ONLY WHEN A CASE DID NOT SUPPLY
        # ONE. Composing it unconditionally would publish a binding for this
        # attempt and then refuse the case's own plan as a conflicting one.
        operands.setdefault("integration_delivery", None)
        if operands["integration_delivery"] is None:
            operands["integration_delivery"] = self.boundary()
        return oci.OciAdapter("docker", engine_run, **operands)

    def test_a_grant_blocked_during_preparation_makes_zero_engine_runs(self):
        """The cutpoint: everything above can spend time, so the grant is
        re-asked with nothing between it and the run but the call."""
        calls = []

        def engine_run(argv, **options):
            calls.append(list(argv))
            if argv[1] == "ps":
                self.block()
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}

        held = self.adapter(engine_run)
        # The block lands on the duplicate probe, which happens before the
        # final proof: the run itself must never be reached.
        self.refused(held.start,
                     {"labels": LABELS, "operation_id": "start-1"})
        self.assertEqual([one for one in calls if one[1] == "run"], [])

    def test_a_companion_whose_mode_moved_before_the_run_makes_zero_runs(self):
        """P1: the final `_read_bounded` omitted the expected mode, so the
        publication-time check did not protect this later use point."""
        calls = []

        def engine_run(argv, **options):
            calls.append(list(argv))
            if argv[1] == "ps":
                os.chmod(os.path.join(self.delivery.root,
                                      oci_delivery.BINDING_DOCUMENT), 0o666)
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}

        held = self.adapter(engine_run)
        caught = self.refused(held.start,
                              {"labels": LABELS, "operation_id": "start-1"})
        self.assertIn("mode", caught.message)
        self.assertEqual([one for one in calls if one[1] == "run"], [])

    def test_a_symlinked_ancestor_before_the_run_makes_zero_engine_runs(self):
        """P1: `O_NOFOLLOW` binds the final component only, so a moved parent
        with a link at its old name kept the target's inode identical and the
        start reached one run against the re-resolved path."""
        calls = []
        parent = os.path.join(self.root, "target-parent")
        os.makedirs(parent, exist_ok=True)
        nested = os.path.join(parent, "canonical")
        os.makedirs(nested, exist_ok=True)
        os.chown(nested, -1, _group_of(self).gid)
        os.chmod(nested, 0o2770)
        target = oci_delivery.integration_target(TARGET,
                                                 nominate_source(nested))

        moved = []

        def engine_run(argv, **options):
            calls.append(list(argv))
            if argv[1] == "ps":
                # ONCE. The probe fires on the duplicate lookup, and a second
                # rename would be moving a symlink onto a directory rather
                # than reproducing the finding.
                if not moved:
                    moved.append(True)
                    os.rename(parent, parent + "-moved")
                    os.symlink(parent + "-moved", parent)
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}

        held = self.adapter(engine_run, integration_delivery=self.boundary(
            target=target))
        caught = self.refused(held.start,
                              {"labels": LABELS, "operation_id": "start-1"})
        self.assertIn("resolves to", caught.message)
        self.assertEqual([one for one in calls if one[1] == "run"], [])

    def test_a_group_the_adapter_does_not_hold_refuses(self):
        """P1: storing the boundary's own group and checking it against itself
        is not a comparison with the group the container is given."""
        class OtherGroup:
            gid = _group_of(self).gid

        other = OtherGroup()
        other.gid = _group_of(self).gid + 1
        calls = []
        held = self.adapter(self.engine(calls))
        object.__setattr__(held, "workspace_group", other)
        self.refused(held.start, {"labels": LABELS,
                                  "operation_id": "start-1"})
        self.assertEqual([one for one in calls if one[1] == "run"], [])

    def test_a_target_replaced_before_the_run_makes_zero_engine_runs(self):
        calls = []

        def engine_run(argv, **options):
            calls.append(list(argv))
            if argv[1] == "ps":
                os.rename(self.canonical, self.canonical + "-moved")
                os.makedirs(self.canonical)
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}

        held = self.adapter(engine_run)
        self.refused(held.start,
                     {"labels": LABELS, "operation_id": "start-1"})
        self.assertEqual([one for one in calls if one[1] == "run"], [])

    def test_a_delivery_for_another_attempt_refuses_and_tears_nothing_down(
            self):
        calls = []

        def engine_run(argv, **options):
            calls.append(list(argv))
            return {"status": 0, "stdout": "", "stderr": ""}

        home = os.path.join(self.root, "launch-home-other")
        os.makedirs(home, exist_ok=True)
        held = self.adapter(engine_run, launch_delivery=launch.materialize(
            home, attempt_id="attempt-9", session="session-9",
            contract="exercise the integration boundary", role="integration"))
        caught = self.refused(
            held.start, {"labels": dict(LABELS,
                                        runtime_attempt_id="attempt-9"),
                         "operation_id": "start-1"})
        self.assertIn("one delivery belongs to one attempt", caught.message)
        self.assertEqual(calls, [])

    def engine(self, calls, *, binds=..., inspect_status=0):
        """A recorded engine whose INSPECTION answers what it was bound with.

        The observation is required now, so a fixture that answered nothing to
        `inspect` would measure the uncertainty path in every case.
        """
        def engine_run(argv, **options):
            calls.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "inspect":
                if inspect_status != 0:
                    return {"status": inspect_status, "stdout": "",
                            "stderr": "no such container"}
                mounts = ([{"Source": one[0], "Destination": one[1],
                            "RW": one[2]} for one in self.expected_binds()]
                          if binds is ... else binds)
                return {"status": 0,
                        "stdout": json.dumps({"Id": "runtime-1",
                                              "State": {"Running": True},
                                              "Mounts": mounts}),
                        "stderr": ""}
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}

        return engine_run

    def expected_binds(self):
        return [(self.delivery.assignment_root, runtime.ASSIGNMENT_TARGET,
                 False),
                (self.delivery.result_root, runtime.RESULT_TARGET, True),
                (self.canonical, oci_delivery.TARGET_TARGET, True)]

    def test_the_unchanged_case_reaches_the_run_with_the_three_binds(self):
        calls = []
        held = self.adapter(self.engine(calls))
        answered = held.start({"labels": LABELS, "operation_id": "start-1"})
        self.assertEqual(answered["runtime_id"], "runtime-1")
        [run] = [one for one in calls if one[1] == "run"]
        found = self.mounts_of(run)
        self.assertIn((self.canonical, oci_delivery.TARGET_TARGET, True),
                      found)
        self.assertIn((self.delivery.assignment_root,
                       runtime.ASSIGNMENT_TARGET, False), found)

    def test_the_answer_is_what_the_real_manager_parser_admits(self):
        """P1 (review 2026-09-07T16-34-08Z): the extra member refused at
        `attempts._started`, one call after `request_runtime_start`, AFTER the
        container existed. The parser is the contract, so it is what this
        asserts against rather than a copy of its member list."""
        from baton_v12.worker_manager import attempts
        calls = []
        held = self.adapter(self.engine(calls))
        answered = held.start({"labels": LABELS, "operation_id": "start-1"})
        self.assertEqual(sorted(answered), ["labels", "runtime_id"])
        parsed = attempts._started(answered)
        self.assertEqual(parsed["runtime_id"], "runtime-1")

    def test_an_unreadable_observation_keeps_the_id_and_the_closed_shape(self):
        """A caller that cannot name the container cannot stop it, so the
        identity survives; the uncertainty travels through `observe`."""
        calls = []
        held = self.adapter(self.engine(calls, inspect_status=1))
        answered = held.start({"labels": LABELS, "operation_id": "start-1"})
        self.assertEqual(sorted(answered), ["labels", "runtime_id"])
        self.assertEqual(answered["runtime_id"], "runtime-1")

    def test_a_runtime_the_engine_describes_with_wrong_binds_is_not_success(
            self):
        """A returned identity says the engine created something; it says
        nothing about what that something holds."""
        calls = []
        held = self.adapter(self.engine(calls, binds=[]))
        caught = self.refused(
            held.start, {"labels": LABELS, "operation_id": "start-1"})
        self.assertIn("does not carry this integration's mounts",
                      caught.message)

    def test_ordinary_observation_carries_the_mount_uncertainty(self):
        """P1: `attempts._observed` consumes `state` and `why` and ignores
        mounts, so a running container with NO integration binds reconciled as
        an ordinary healthy runtime. The state itself is the carrier now."""
        calls = []
        held = self.adapter(self.engine(calls, binds=[]))
        observed = held.observe("runtime-1")
        self.assertEqual(observed["state"], "uncertain")
        self.assertIn("integration mounts are not this attempt's",
                      observed["why"])
        # POSITIVE IDENTITY EVIDENCE SURVIVES, so an operator can still name
        # and stop this exact runtime.
        self.assertEqual(observed["candidates"][0]["runtime_id"], "runtime-1")

    def test_an_unreadable_inspection_is_uncertain_rather_than_running(self):
        calls = []
        held = self.adapter(self.engine(calls, inspect_status=1))
        self.assertEqual(held.observe("runtime-1")["state"], "uncertain")

    def test_the_agreeing_runtime_observes_as_running(self):
        calls = []
        held = self.adapter(self.engine(calls))
        observed = held.observe("runtime-1")
        self.assertEqual(observed["state"], "running")

    def test_a_recovered_boundary_observes_through_the_same_path(self):
        """The review asked for the normal consumer path including
        RECONSTRUCTED boundaries: an operator that adopted a plan after grant
        loss must still be able to observe -- and to stop -- the exact runtime,
        with the same uncertainty rules and no fresh grant anywhere."""
        calls = []
        self.boundary()
        self.block()
        recovered = oci_delivery.adopt_mount_boundary(
            self.manager, delivery=self.delivery, target=self.target,
            workspace_group=_group_of(self))
        roots = {"inputs": os.path.join(self.root, "rec-inputs"),
                 "workspace": os.path.join(self.root, "rec-workspace")}
        for place in roots.values():
            os.makedirs(place, exist_ok=True)
        held = oci.OciAdapter(
            "docker", self.engine(calls),
            identity={"image_digest": IMAGE,
                      "profile_digest": LABELS["profile_digest"],
                      "policy_digest": LABELS["policy_digest"],
                      "adapter_digest": LABELS["adapter_digest"]},
            assignment_roots=roots, posture="execution",
            integration_delivery=recovered)
        self.assertEqual(held.observe("runtime-1")["state"], "running")
        # AND A RUNTIME WHOSE BINDS ARE GONE IS STILL UNCERTAIN, through the
        # recovered plan exactly as through the composed one.
        gone = oci.OciAdapter(
            "docker", self.engine(calls, binds=[]),
            identity={"image_digest": IMAGE,
                      "profile_digest": LABELS["profile_digest"],
                      "policy_digest": LABELS["policy_digest"],
                      "adapter_digest": LABELS["adapter_digest"]},
            assignment_roots=roots, posture="execution",
            integration_delivery=recovered)
        self.assertEqual(gone.observe("runtime-1")["state"], "uncertain")
        # STOPPING DEPENDS ON NO GRANT. The target is blocked and this still
        # composes the exact stop vector for the identity it observed.
        self.assertEqual(
            oci.stop_vector("docker", runtime_id="runtime-1")[-1],
            "runtime-1")

    def test_an_adapter_with_no_integration_observes_exactly_as_before(self):
        """The downgrade is this family's and touches no ordinary worker."""
        calls = []
        roots = {"inputs": os.path.join(self.root, "p-inputs"),
                 "workspace": os.path.join(self.root, "p-workspace")}
        for place in roots.values():
            os.makedirs(place, exist_ok=True)
        plain = oci.OciAdapter(
            "docker", self.engine(calls, binds=[]),
            identity={"image_digest": IMAGE,
                      "profile_digest": LABELS["profile_digest"],
                      "policy_digest": LABELS["policy_digest"],
                      "adapter_digest": LABELS["adapter_digest"]},
            assignment_roots=roots, posture="execution")
        self.assertEqual(plain.observe("runtime-1")["state"], "running")


class TheObservedMountsAreAskedOfTheEngine(MountCase):

    def observed(self, entries):
        return oci_delivery.observed_disagreement(self.boundary(), entries)

    def live(self, **changed):
        held = [{"source": self.delivery.assignment_root,
                 "target": runtime.ASSIGNMENT_TARGET, "writable": False},
                {"source": self.delivery.result_root,
                 "target": runtime.RESULT_TARGET, "writable": True},
                {"source": self.canonical,
                 "target": oci_delivery.TARGET_TARGET, "writable": True}]
        if changed.get("replace") is not None:
            held[changed["replace"][0]] = changed["replace"][1]
        if changed.get("extra") is not None:
            held.append(changed["extra"])
        if changed.get("drop") is not None:
            held.pop(changed["drop"])
        return held

    def test_the_exact_plan_agrees(self):
        self.assertIsNone(self.observed(self.live()))

    def test_an_unreadable_observation_is_never_agreement(self):
        self.assertIn("nothing about its integration mounts is proved",
                      self.observed(None))

    def test_a_missing_bind_disagrees(self):
        self.assertIn("carries 0 binds", self.observed(self.live(drop=2)))

    def test_a_duplicate_bind_disagrees(self):
        self.assertIn("carries 2 binds", self.observed(self.live(
            extra={"source": self.canonical,
                   "target": oci_delivery.TARGET_TARGET, "writable": True})))

    def test_a_foreign_source_disagrees(self):
        self.assertIn("comes from", self.observed(self.live(
            replace=(2, {"source": "/elsewhere",
                         "target": oci_delivery.TARGET_TARGET,
                         "writable": True}))))

    def test_a_read_only_target_disagrees(self):
        self.assertIn("read-only", self.observed(self.live(
            replace=(2, {"source": self.canonical,
                         "target": oci_delivery.TARGET_TARGET,
                         "writable": False}))))

    def test_a_writable_assignment_namespace_disagrees(self):
        self.assertIn("writable", self.observed(self.live(
            replace=(0, {"source": self.delivery.assignment_root,
                         "target": runtime.ASSIGNMENT_TARGET,
                         "writable": True}))))

    def test_an_ancestor_bind_over_the_namespaces_disagrees(self):
        """Review [P1]: this looked only BELOW an expected target, so
        `/run/baton/integration` -- the parent of two of the three -- was
        reported as agreement while shadowing both."""
        self.assertIn("contains or is contained by", self.observed(self.live(
            extra={"source": "/elsewhere",
                   "target": "/run/baton/integration", "writable": True})))

    def test_a_bind_over_the_container_root_disagrees(self):
        self.assertIn("contains or is contained by", self.observed(self.live(
            extra={"source": "/elsewhere", "target": "/run",
                   "writable": True})))

    def test_an_extra_bind_below_a_fixed_target_disagrees(self):
        self.assertIn("did not authorize", self.observed(self.live(
            extra={"source": "/elsewhere",
                   "target": oci_delivery.TARGET_TARGET + "/inner",
                   "writable": True})))

    def test_an_unrelated_bind_is_left_alone(self):
        self.assertIsNone(self.observed(self.live(
            extra={"source": "/elsewhere", "target": "/input/source",
                   "writable": False})))


class RecoveryAdoptsAndNeverRecreates(MountCase):
    """P1 (review 2026-09-07T16-04-48Z): publication and recovery were one act.

    The only minting path required a fresh grant, so a blocked target left a
    running container nobody could reach through the public surface; and the
    binding was published whenever it was absent, so a removed companion was
    silently recreated with identical bytes and the evidence that it had ever
    gone was destroyed by the act of looking.
    """

    def place(self):
        return os.path.join(self.delivery.root, oci_delivery.BINDING_DOCUMENT)

    def test_a_blocked_grant_still_yields_an_inspectable_boundary(self):
        self.boundary()
        self.block()
        # Composition refuses, because that is the act that authorizes a bind.
        self.refused(self.boundary)
        # Adoption does not, because inspecting and stopping an exact runtime
        # after grant loss is what it exists for.
        recovered = oci_delivery.adopt_mount_boundary(
            self.manager, delivery=self.delivery, target=self.target,
            workspace_group=_group_of(self))
        self.assertEqual(recovered.attempt_id, "attempt-1")
        self.assertEqual(len(recovered.sources), 3)

    def test_a_recovered_boundary_may_never_start_a_runtime(self):
        self.boundary()
        recovered = oci_delivery.adopt_mount_boundary(
            self.manager, delivery=self.delivery, target=self.target,
            workspace_group=_group_of(self))
        caught = self.refused(oci_delivery.revalidate_boundary, recovered)
        self.assertIn("RECOVERED rather than composed", caught.message)

    def test_a_removed_binding_is_never_silently_recreated(self):
        self.boundary()
        os.chmod(self.delivery.root, 0o700)
        os.unlink(self.place())
        caught = self.refused(
            oci_delivery.adopt_mount_boundary, self.manager,
            delivery=self.delivery, target=self.target,
            workspace_group=_group_of(self))
        self.assertIn("never composes a replacement", caught.message)
        self.assertFalse(os.path.exists(self.place()))

    def test_a_recovered_source_that_moved_is_reported_not_re_resolved(self):
        self.boundary()
        os.rename(self.canonical, self.canonical + "-moved")
        os.makedirs(self.canonical)
        self.provisioned()
        caught = self.refused(
            oci_delivery.adopt_mount_boundary, self.manager,
            delivery=self.delivery, target=self.target,
            workspace_group=_group_of(self))
        self.assertIn("reports what it found", caught.message)

    def test_a_recovery_naming_another_directory_under_one_id_refuses(self):
        """P2: only the opaque id was compared, so a different real directory
        nominated under the same id was accepted -- the recovered object
        pointed at one tree while its mounts still named another."""
        self.boundary()
        other = os.path.join(self.root, "other-configured")
        os.makedirs(other)
        os.chown(other, -1, _group_of(self).gid)
        os.chmod(other, 0o2770)
        caught = self.refused(
            oci_delivery.adopt_mount_boundary, self.manager,
            delivery=self.delivery,
            target=oci_delivery.integration_target(TARGET,
                                                   nominate_source(other)),
            workspace_group=_group_of(self))
        self.assertIn("the plan it found", caught.message)

    def test_a_recovery_for_another_target_refuses(self):
        self.boundary()
        other = os.path.join(self.root, "other-target")
        os.makedirs(other)
        os.chown(other, -1, _group_of(self).gid)
        os.chmod(other, 0o2770)
        caught = self.refused(
            oci_delivery.adopt_mount_boundary, self.manager,
            delivery=self.delivery,
            target=oci_delivery.integration_target("target:other",
                                                   nominate_source(other)),
            workspace_group=_group_of(self))
        self.assertIn("the plan recorded", caught.message)


class TheNominalBoundaryIsFrozenThrough(MountCase):
    """P2: blocking attribute assignment while storing live dictionaries left
    the assignment, the profile and every source editable through the public
    attributes -- and `boundary_mounts` then answered a caller's own flag."""

    def test_the_public_views_cannot_be_written_through(self):
        held = self.boundary()
        for view, key, value in ((held.assignment, "target_access", "read"),
                                 (held.profile, "profile_kind", "other"),
                                 (held.sources[2], "writable", False)):
            with self.subTest(key=key):
                with self.assertRaises(TypeError):
                    view[key] = value

    def test_the_composed_mounts_are_unaffected_by_a_held_view(self):
        held = self.boundary()
        taken = held.sources
        del taken
        self.assertEqual(
            [one[2] for one in oci_delivery.boundary_mounts(held)],
            [False, True, True])

    def test_mutating_the_caller_s_own_operands_changes_nothing(self):
        held = self.boundary()
        self.assignment["target_access"] = "read"
        self.assertEqual(held.assignment["target_access"], "writable")


class TheTargetPostureIsProvedAndNeverRepaired(MountCase):

    def test_a_target_in_the_configured_group_and_group_writable_is_held(self):
        held = oci_delivery.prove_target_posture(self.boundary(),
                                                 _group_of(self))
        self.assertEqual(held["gid"], _group_of(self).gid)

    def test_composition_itself_refuses_an_incompatible_target(self):
        """The proof has a production caller now: a start never reaches the
        engine with a target the runtime's group cannot work in."""
        self.provisioned(mode=0o755)
        caught = self.refused(self.boundary)
        self.assertIn("operator provisioning", caught.message)
        # AND NOTHING WAS REPAIRED.
        self.assertEqual(stat.S_IMODE(os.stat(self.canonical).st_mode), 0o755)

    def test_group_write_without_traversal_is_not_access(self):
        """A directory the group cannot enter is one whose write bit describes
        a permission it can never reach."""
        self.provisioned(mode=0o2760)
        self.refused(self.boundary)

    # A "target owned by another group" case is deliberately absent: an
    # ordinary uid cannot `chown` a directory into a group it does not hold,
    # so the case would only run on some hosts. The group comparison itself is
    # `adopt_delivery`'s and has its own suite.


class TheModulesImportInEitherOrder(unittest.TestCase):
    """The confirmed cycle: `integration` imports `worker_manager`, so the
    resolution has to be at the use point rather than at module scope."""

    def test_neither_order_fails(self):
        import subprocess
        import sys
        for first, second in (
                ("baton_v12.worker_manager.oci",
                 "baton_v12.integration.oci_delivery"),
                ("baton_v12.integration.oci_delivery",
                 "baton_v12.worker_manager.oci")):
            with self.subTest(first=first):
                answer = subprocess.run(
                    [sys.executable, "-c",
                     f"import {first}; import {second}; print('ok')"],
                    capture_output=True, text=True, timeout=120,
                    env=dict(os.environ, PYTHONPATH="src"),
                    cwd=str(__import__("pathlib").Path(__file__).resolve()
                            .parents[2]))
                self.assertEqual(answer.stdout.strip(), "ok", answer.stderr)

    def test_the_manager_names_no_integration_module_at_import_time(self):
        import ast
        import pathlib
        place = (pathlib.Path(oci.__file__).resolve())
        tree = ast.parse(place.read_text(encoding="utf-8"), str(place))
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = ([alias.name for alias in node.names]
                         if isinstance(node, ast.Import)
                         else [node.module or ""])
                for name in names:
                    self.assertNotIn("integration", name)


if __name__ == "__main__":
    unittest.main()
