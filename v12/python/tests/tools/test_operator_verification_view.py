"""The INDEPENDENT OPERATOR's fresh private view, and the named gate in it.

W321776, `work/records/2026/09/finding-v12-complete-verification-context/
findings/finding-paired-context-delivery/`, against the accepted packet in
`findings/finding-context-packet/`.

THE OTHER HALF OF THE PAIR. `tests/manager/test_verification_views.py` holds
the worker's view; this holds the operator's, and they are separate suites over
separate product code on purpose. DESIGN VER-3 requires a fresh private view at
EACH holder, and what makes a second observation worth anything is that its
bytes come from the RETAINED OUTPUT rather than from the worker's conclusions.

THE TWO SHAPES OF RETAINED OUTPUT, both covered:

  a GENERIC candidate's retained output IS the candidate tree, so there is no
  commit, no transport and nothing to resolve -- and the NAMED 102-test gate
  runs in a view built from that tree;
  a VERSION-CONTROL candidate retains an INCREMENTAL `base..HEAD` bundle, which
  does not carry the base history -- so the accepted-base object source
  supplies the prerequisites and the bundle is applied over them, with every
  prerequisite required rather than assumed.

NO VERSION-CONTROL COMMAND IS EXECUTED BY THIS SUITE. The repository capability
is INJECTED into the product, so the transport path is driven by a recorded
simulated repository and its evidence is labelled as a SIMULATED BOUNDARY.
`AGENTS.md` forbids an agent performing a mutating version-control operation --
and that prohibition is not scoped to a particular checkout, so a throwaway one
in a temporary directory would violate it exactly as much.
"""

import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

DISTRIBUTION = pathlib.Path(__file__).resolve().parents[2]
_TOOLS = str(DISTRIBUTION / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import dogfood_operator                                        # noqa: E402
from baton_v12 import verification_context as contract         # noqa: E402

from tests.manager import verification_fixtures as fixtures     # noqa: E402


class OperatorViewCase(unittest.TestCase):
    """A retained proposal, a staged seal, and nothing else.

    What a retained proposal carries is exactly what the worker published: the
    candidate tree for a generic profile, the patch, the transcript and the
    result record. The operator reads the RECORD for the observation and gets
    its bytes from the retained output -- never from an ambient checkout.
    """

    def setUp(self):
        home = tempfile.mkdtemp(prefix="v12-w321776-op-")
        self.addCleanup(shutil.rmtree, home, True)
        self.home = home
        self.proposal = os.path.join(home, "storage", "proposal")
        self.inputs = os.path.join(home, "input")
        os.makedirs(self.proposal)
        os.makedirs(self.inputs)
        self.pin_digest = fixtures.digest_of(
            fixtures.REPOSITORY / fixtures.VECTORS)
        self.sealed = fixtures.gate_seal(self.inputs,
                                         pin_digest=self.pin_digest)
        self.seal_root = os.path.join(self.inputs,
                                      dogfood_operator.SEAL_ROOT)

    # -- the retained output -------------------------------------------------

    def retain(self, candidate_builder, *, changed=None, removed=(),
               head=None, entry=None, base=None, bundle=False,
               profile="generic"):
        """Everything the worker published, and nothing it did not."""
        candidate = (candidate_builder(self.proposal)
                     if candidate_builder is not None else None)
        measured = []
        for one in (changed or []):
            measured.append({"path": one,
                             "content_digest": fixtures.digest_of(
                                 os.path.join(candidate, one))})
        record = {"schema": contract.PROPOSAL_SCHEMA,
                  "task_id": "w321776-paired-gate",
                  "disposition": "candidate", "why": "verification passed",
                  "changed_paths": sorted(one["path"] for one in measured),
                  "source_entries": 1, "collection": None,
                  "base": base, "entry_head": entry, "head": head,
                  "provider": {"status": 0, "failure_reason": None},
                  "verification": {"status": 0,
                                   "argv": list(fixtures.GATE_ARGV)},
                  "context": contract.ready(), "command": contract.PASSED,
                  "exit_status": 0,
                  "candidate_changed": measured,
                  "candidate_removed": sorted(removed)}
        with open(os.path.join(self.proposal, "result.json"), "w",
                  encoding="utf-8") as writing:
            writing.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
        with open(os.path.join(self.proposal, "change.patch"), "w",
                  encoding="utf-8") as writing:
            writing.write("")
        with open(os.path.join(self.proposal, "verification.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("$ the worker's own transcript\n")
        if bundle:
            with open(os.path.join(self.proposal, "objects.bundle"), "wb") as w:
                w.write(b"# a simulated object transport\n")
        self.record = record
        return record

    def task(self, *, profile="generic", base=None, context=None, argv=None):
        return fixtures.gate_task(profile=profile, base=base,
                                  pin_digest=self.pin_digest,
                                  context=context, argv=argv)

    def derived(self, task, *, objects=None, runner=None):
        return dogfood_operator._derived_in_view(
            self.proposal, os.path.join(self.proposal, "candidate"), task,
            seal_root=self.seal_root, objects=objects, runner=runner)

    # -- the simulated repository -------------------------------------------

    def repository(self, *, failing=(), places=None):
        """A RECORDED SIMULATED REPOSITORY, and never a real one.

        `failing` names the sub-commands that answer non-zero, so each named
        prerequisite can be made to fail on its own; `places` lets a successful
        step put bytes where a real one would, because a view with no files is
        not a view the next stage can be asked about.
        """
        self.asked = []

        def ask(argv, **options):
            self.asked.append(list(argv))
            verb = tuple(one for one in argv if not one.startswith("-"))
            for name in failing:
                if name in argv:
                    return _Answered(1)
            if places is not None:
                places(argv)
            del verb
            return _Answered(0)

        return ask


class _Answered:
    def __init__(self, returncode):
        self.returncode = returncode
        self.stdout = ""
        self.stderr = ""


class TheNamedGatePassesInTheOperatorsOwnView(OperatorViewCase):
    """VER-5's acceptance obligation, at the second holder.

    "The selected historical 102-test credential gate must pass in BOTH
    independently materialized views with no skips or context errors." The
    worker's is the other suite's; this is the independent operator's, built
    from the retained output and the same seal.
    """

    def test_the_gate_passes_in_the_operators_view(self):
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        answered = self.derived(self.task())
        self.assertEqual(answered["verification_status"], 0, answered)
        evidence = answered["operator_evidence"]
        self.assertEqual(evidence["context"], contract.ready())
        self.assertEqual(evidence["command"], contract.PASSED)
        self.assertEqual(evidence["exit_status"], 0)
        self.assertEqual(
            contract.verdict(evidence["context"], evidence["command"],
                             evidence["exit_status"]), contract.PASSED)

    def test_the_evidence_is_bound_to_the_retained_output_it_verified(self):
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        with open(os.path.join(self.proposal, "result.json"), "rb") as reading:
            raw = reading.read()
        evidence = self.derived(self.task())["operator_evidence"]
        self.assertEqual(
            evidence["result_digest"],
            "sha256:" + hashlib.sha256(raw).hexdigest())
        self.assertEqual(evidence["task_id"], "w321776-paired-gate")
        contract.held_evidence(evidence)

    def test_the_measured_members_are_measured_and_not_copied(self):
        """Evidence that restated the declaration would agree with the task by
        construction and prove nothing about the view."""
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        evidence = self.derived(self.task())["operator_evidence"]
        measured = {one["path"]: one["content_digest"]
                    for one in evidence["candidate_changed"]}
        self.assertEqual(
            measured["v12/python/src/baton_v12/__init__.py"],
            fixtures.digest_of(os.path.join(
                self.proposal, "candidate", "v12", "python", "src",
                "baton_v12", "__init__.py")))
        self.assertEqual(
            [one["name"] for one in evidence["inputs"]],
            [fixtures.INPUT_NAME])
        self.assertEqual(evidence["inputs"][0]["content_digest"],
                         self.pin_digest)

    def test_a_generic_candidate_is_identified_without_a_head(self):
        """"Nothing asks for a head it cannot have."""
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        evidence = self.derived(self.task())["operator_evidence"]
        self.assertIsNone(evidence["result_head"])
        self.assertIsNone(evidence["transport"])
        self.assertIsNone(evidence["candidate_base"])
        self.assertIsNone(evidence["candidate_entry"])
        self.assertEqual(evidence["candidate_profile"], "generic")

    def test_the_view_is_removed_and_the_retained_output_is_not(self):
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        before = fixtures.digest_of(os.path.join(
            self.proposal, "candidate", "v12", "python", "src", "baton_v12",
            "__init__.py"))
        self.derived(self.task())
        self.assertEqual(fixtures.digest_of(os.path.join(
            self.proposal, "candidate", "v12", "python", "src", "baton_v12",
            "__init__.py")), before)
        residue = [one for one in os.listdir(
            dogfood_operator.VERIFICATION_TEMP_ROOT)
            if one.startswith("dogfood-view-")]
        self.assertEqual(residue, [], "the operator left a view behind")

    def test_the_sealed_inputs_are_byte_unchanged_afterwards(self):
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        before = fixtures.digest_of(os.path.join(self.seal_root,
                                                 fixtures.INPUT_NAME))
        self.derived(self.task())
        self.assertEqual(fixtures.digest_of(os.path.join(
            self.seal_root, fixtures.INPUT_NAME)), before)

    def test_the_gate_passes_with_a_hostile_ambient_import_path(self):
        """The derived path REPLACES the ambient one rather than extending
        it."""
        hostile = os.path.join(self.home, "hostile")
        os.makedirs(hostile)
        with open(os.path.join(hostile, "unittest.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("raise SystemExit('the hostile entry was used')\n")
        held = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = hostile
        self.addCleanup(lambda: (os.environ.__setitem__("PYTHONPATH", held)
                                 if held is not None
                                 else os.environ.pop("PYTHONPATH", None)))
        self.retain(lambda root: fixtures.gate_candidate(root),
                    changed=["v12/python/src/baton_v12/__init__.py"])
        answered = self.derived(self.task())
        self.assertEqual(answered["verification_status"], 0, answered)


class TheOperatorsViewRefusesWhatThePacketSays(OperatorViewCase):
    """Stage B at the second holder, with the same causes and the same
    order."""

    def tiny(self, root):
        candidate = fixtures.tiny_candidate(root)
        landing = os.path.join(candidate, fixtures.VECTORS)
        os.makedirs(os.path.dirname(landing), exist_ok=True)
        shutil.copyfile(fixtures.REPOSITORY / fixtures.VECTORS, landing)
        return candidate

    def tiny_context(self, **changes):
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        context.update(changes)
        return context

    def refused(self, *, context=None, **retained):
        self.retain(self.tiny, **retained)
        answered = self.derived(self.task(
            context=context or self.tiny_context(),
            argv=["python3", "-c", "print('ran')"]))
        return answered["operator_evidence"]

    def test_an_absent_required_path_is_missing_input(self):
        evidence = self.refused(
            context=self.tiny_context(required_paths=["harness.py",
                                                      "not-there.py"]))
        self.assertEqual(evidence["context"]["stage"], contract.VIEW_STAGE)
        self.assertEqual(evidence["context"]["cause"], contract.MISSING_INPUT)
        self.assertEqual(evidence["command"], contract.NOT_RUN)
        self.assertIsNone(evidence["exit_status"])

    def test_an_absent_import_root_is_invalid_layout(self):
        evidence = self.refused(
            context=self.tiny_context(import_roots=["no-such-root"]))
        self.assertEqual(evidence["context"]["cause"], contract.INVALID_LAYOUT)
        self.assertEqual(evidence["command"], contract.NOT_RUN)

    def test_a_reported_change_the_view_does_not_hold_is_materialization(self):
        """A SUBSTITUTED BASE REFUSES. The view is bound to the paths the
        retained result reported changed, so a tree that does not hold them
        cannot pass as the changed candidate."""
        self.retain(self.tiny, changed=["harness.py"])
        record = dict(self.record)
        record["candidate_changed"] = [
            {"path": "harness.py",
             "content_digest": "sha256:" + "0" * 64}]
        with open(os.path.join(self.proposal, "result.json"), "w",
                  encoding="utf-8") as writing:
            writing.write(json.dumps(record, indent=1, sort_keys=True))
        evidence = self.derived(self.task(
            context=self.tiny_context(),
            argv=["python3", "-c", "print('ran')"]))["operator_evidence"]
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertEqual(evidence["command"], contract.NOT_RUN)

    def test_a_reported_deletion_still_present_is_materialization(self):
        self.retain(self.tiny, removed=["harness.py"])
        evidence = self.derived(self.task(
            context=self.tiny_context(),
            argv=["python3", "-c", "print('ran')"]))["operator_evidence"]
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertIn("removed[0]", evidence["context"]["detail"])

    def test_a_drifted_in_candidate_pin_is_materialization(self):
        self.retain(self.tiny)
        with open(os.path.join(self.proposal, "candidate", fixtures.VECTORS),
                  "w", encoding="utf-8") as writing:
            writing.write("{\"drifted\": true}\n")
        evidence = self.derived(self.task(
            context=self.tiny_context(),
            argv=["python3", "-c", "print('ran')"]))["operator_evidence"]
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertIn("candidate.pins[0]", evidence["context"]["detail"])

    def test_a_refusal_is_not_reported_as_a_passing_verification(self):
        """A context fault must not earn the authority pass the ending decides
        on `verification_status`."""
        answered = self.derived(self.task(
            context=self.tiny_context(required_paths=["not-there.py"]),
            argv=["python3", "-c", "print('ran')"])) \
            if self.retain(self.tiny) else None
        self.assertNotEqual(answered["verification_status"], 0)
        self.assertEqual(answered["operator_evidence"]["command"],
                         contract.NOT_RUN)

    def test_the_view_is_gone_after_every_refusal(self):
        self.refused(
            context=self.tiny_context(required_paths=["not-there.py"]))
        residue = [one for one in os.listdir(
            dogfood_operator.VERIFICATION_TEMP_ROOT)
            if one.startswith("dogfood-view-")]
        self.assertEqual(residue, [])


class TheTransportsPrerequisitesAreRequiredNotAssumed(OperatorViewCase):
    """The version-control shape, driven by a SIMULATED repository.

    Each row is a different prerequisite being wrong, and each one has its own
    cause -- because "the bundle is missing its history" and "the bundle is for
    another head" are different facts about a candidate.

    SIMULATED BOUNDARY. No version-control command is executed here; the
    product's injected capability is answered by a recorded fake, so what these
    cases establish is the product's ordering, operands and refusal mapping,
    not that a real repository behaves as described.
    """

    HEAD = "f" * 40
    BASE = "a" * 40

    def line_context(self):
        context = fixtures.gate_context(profile="git-line", base=self.BASE,
                                        pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        return context

    def line_task(self):
        return self.task(profile="git-line", base=self.BASE,
                         context=self.line_context(),
                         argv=["python3", "-c", "print('ran')"])

    def retained_line(self, **changes):
        # NO CANDIDATE TREE, which is exactly what `_publish_line` retains for
        # a line profile: a patch, a transcript, a record and the objects.
        self.retain(None, head=self.HEAD, entry=self.HEAD, base=self.BASE,
                    bundle=True, profile="git-line", **changes)

    def places(self, argv):
        """What a real step would leave behind, so the next one has a view."""
        if "checkout" in argv:
            where = argv[argv.index("--work-tree") + 1]
            os.makedirs(where, exist_ok=True)
            with open(os.path.join(where, "harness.py"), "w",
                      encoding="utf-8") as writing:
                writing.write("print('the resolved candidate')\n")

    def objects_root(self):
        place = os.path.join(self.home, "accepted-base.git")
        os.makedirs(place, exist_ok=True)
        return place

    def refused_with(self, *, failing=(), objects=None):
        self.retained_line()
        answered = self.derived(self.line_task(),
                                objects=(self.objects_root()
                                         if objects is None else objects),
                                runner=self.repository(failing=failing,
                                                       places=self.places))
        return answered["operator_evidence"]

    def test_an_absent_accepted_base_object_source_is_missing_input(self):
        evidence = self.refused_with(
            objects=os.path.join(self.home, "no-such-objects"))
        self.assertEqual(evidence["context"]["cause"], contract.MISSING_INPUT)
        self.assertEqual(evidence["context"]["detail"],
                         contract.BASE_SOURCE_DETAIL)
        self.assertEqual(evidence["command"], contract.NOT_RUN)

    def test_an_object_source_that_does_not_hold_the_base_is_missing_input(self):
        evidence = self.refused_with(failing=("cat-file",))
        self.assertEqual(evidence["context"]["cause"], contract.MISSING_INPUT)
        self.assertEqual(evidence["context"]["detail"],
                         contract.BASE_SOURCE_DETAIL)

    def test_an_unsatisfied_bundle_prerequisite_is_materialization(self):
        evidence = self.refused_with(failing=("verify",))
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertEqual(evidence["context"]["detail"],
                         contract.TRANSPORT_DETAIL)

    def test_a_transport_resolving_another_head_is_materialization(self):
        """A bundle for some other head is not this result's candidate.

        The step that decides it is the one asking the RECEIVING repository
        for the head the retained result published -- a fetch that succeeded
        against some other object would not say.
        """
        evidence = self.refused_with(failing=(f"{self.HEAD}^{{commit}}",))
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertEqual(evidence["context"]["detail"],
                         contract.TRANSPORT_DETAIL)

    def test_a_bundle_whose_objects_cannot_be_fetched_is_materialization(self):
        """The fetch of the transport itself, told apart from the base's.

        Both steps are a `fetch`, so the operands are what distinguish them:
        failing the one naming the BUNDLE leaves the base's own fetch
        succeeding, which is how the two refusals stay two.
        """
        self.retained_line()
        transport = os.path.join(self.proposal, "objects.bundle")
        answered = self.derived(
            self.line_task(), objects=self.objects_root(),
            runner=self.repository(failing=(transport,),
                                   places=self.places))
        evidence = answered["operator_evidence"]
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertEqual(evidence["context"]["detail"],
                         contract.TRANSPORT_DETAIL)

    def test_a_base_that_is_not_an_ancestor_is_invalid_layout(self):
        evidence = self.refused_with(failing=("merge-base",))
        self.assertEqual(evidence["context"]["cause"], contract.INVALID_LAYOUT)
        self.assertEqual(evidence["context"]["detail"],
                         contract.ANCESTRY_DETAIL)

    def test_the_base_is_never_checked_out_into_the_view(self):
        """"A view built at the base would discard the very changes the
        verification exists to measure."""
        self.retained_line()
        self.derived(self.line_task(), objects=self.objects_root(),
                     runner=self.repository(places=self.places))
        checkouts = [one for one in self.asked if "checkout" in one]
        self.assertEqual(len(checkouts), 1, self.asked)
        self.assertIn(self.HEAD, checkouts[0])
        self.assertNotIn(self.BASE, checkouts[0])

    def test_the_base_objects_are_fetched_before_the_bundle(self):
        self.retained_line()
        self.derived(self.line_task(), objects=self.objects_root(),
                     runner=self.repository(places=self.places))
        order = [one for one in self.asked
                 if "fetch" in one or "verify" in one]
        self.assertIn(self.objects_root(), order[0])
        self.assertIn("verify", order[1])

    def test_a_result_with_no_head_resolves_nothing(self):
        self.retain(None, head=None, base=self.BASE, bundle=True,
                    profile="git-line")
        evidence = self.derived(
            self.line_task(), objects=self.objects_root(),
            runner=self.repository(places=self.places))["operator_evidence"]
        self.assertEqual(evidence["context"]["cause"], contract.MISSING_INPUT)
        self.assertEqual(evidence["command"], contract.NOT_RUN)

    def test_a_missing_transport_refuses_rather_than_falling_back(self):
        self.retain(None, head=self.HEAD, base=self.BASE, bundle=False,
                    profile="git-line")
        evidence = self.derived(
            self.line_task(), objects=self.objects_root(),
            runner=self.repository(places=self.places))["operator_evidence"]
        self.assertEqual(evidence["context"]["cause"],
                         contract.MATERIALIZATION)
        self.assertEqual(evidence["context"]["detail"],
                         contract.TRANSPORT_DETAIL)

    def test_no_repository_capability_at_all_is_an_operational_refusal(self):
        self.retained_line()
        with self.assertRaises(dogfood_operator.OperatorRefusal) as refused:
            self.derived(self.line_task(), objects=self.objects_root(),
                         runner=None)
        self.assertIn("repository capability", str(refused.exception))


class TheSealIsOneMeasurement(unittest.TestCase):
    """One measurement, two documents, and the declaration cannot drift from
    the seal."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w321776-seal-")
        self.addCleanup(shutil.rmtree, self.home, True)

    def test_the_seal_and_the_declaration_carry_one_digest(self):
        document, declared = dogfood_operator.compose_seal(
            self.home,
            inputs=[{"name": fixtures.INPUT_NAME,
                     "source": str(fixtures.REPOSITORY / fixtures.VECTORS),
                     "destination": fixtures.INPUT_DESTINATION}],
            pins=[fixtures.VECTORS], candidate=str(fixtures.REPOSITORY))
        self.assertEqual(document["inputs"][0]["content_digest"],
                         declared[0]["content_digest"])
        self.assertEqual(document["pins"][0]["content_digest"],
                         declared[0]["content_digest"])

    def test_the_sealed_bytes_are_written_where_the_document_says(self):
        document, _declared = dogfood_operator.compose_seal(
            self.home,
            inputs=[{"name": fixtures.INPUT_NAME,
                     "source": str(fixtures.REPOSITORY / fixtures.VECTORS),
                     "destination": fixtures.INPUT_DESTINATION}],
            pins=[], candidate=str(fixtures.REPOSITORY))
        place = os.path.join(self.home, dogfood_operator.SEAL_ROOT,
                             document["inputs"][0]["place"])
        self.assertEqual(fixtures.digest_of(place),
                         document["inputs"][0]["content_digest"])

    def test_an_input_the_host_does_not_hold_refuses(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator.compose_seal(
                self.home,
                inputs=[{"name": "nothing-here",
                         "source": os.path.join(self.home, "absent"),
                         "destination": "sealed/absent"}],
                pins=[], candidate=self.home)

    def test_a_pin_the_candidate_does_not_hold_refuses(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator.compose_seal(
                self.home, inputs=[], pins=["not/there.json"],
                candidate=self.home)

    def test_the_seal_is_read_back_through_the_shared_hold(self):
        dogfood_operator.compose_seal(
            self.home,
            inputs=[{"name": fixtures.INPUT_NAME,
                     "source": str(fixtures.REPOSITORY / fixtures.VECTORS),
                     "destination": fixtures.INPUT_DESTINATION}],
            pins=[fixtures.VECTORS], candidate=str(fixtures.REPOSITORY))
        sealed, pinned = dogfood_operator.read_seal(self.home)
        self.assertEqual(sorted(sealed), [fixtures.INPUT_NAME])
        self.assertEqual(sorted(pinned), [fixtures.VECTORS])

    def test_a_three_task_whose_declaration_the_seal_refuses_does_not_stage(self):
        pin = fixtures.digest_of(fixtures.REPOSITORY / fixtures.VECTORS)
        task = fixtures.gate_task(pin_digest=pin)
        task["verification_context"]["inputs"][0]["content_digest"] = (
            "sha256:" + "0" * 64)
        with self.assertRaises(dogfood_operator.OperatorRefusal) as refused:
            dogfood_operator._staged_seal(
                task, self.home,
                [{"name": fixtures.INPUT_NAME,
                  "source": str(fixtures.REPOSITORY / fixtures.VECTORS)}],
                str(fixtures.REPOSITORY))
        self.assertIn("missing-input", str(refused.exception))

    def test_a_three_task_naming_an_input_nobody_supplies_refuses(self):
        pin = fixtures.digest_of(fixtures.REPOSITORY / fixtures.VECTORS)
        with self.assertRaises(dogfood_operator.OperatorRefusal) as refused:
            dogfood_operator._staged_seal(
                fixtures.gate_task(pin_digest=pin), self.home, [],
                str(fixtures.REPOSITORY))
        self.assertIn(fixtures.INPUT_NAME, str(refused.exception))

    def test_a_legacy_task_stages_no_seal_at_all(self):
        self.assertIsNone(dogfood_operator._staged_seal(
            {"schema": contract.LEGACY_TASK_SCHEMA}, self.home, None,
            self.home))
        self.assertFalse(os.path.exists(
            os.path.join(self.home, dogfood_operator.SEAL_DOCUMENT)))

    def test_sealed_inputs_for_a_legacy_task_refuse(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator._staged_seal(
                {"schema": contract.LEGACY_TASK_SCHEMA}, self.home,
                [{"name": "x", "source": self.home}], self.home)


class BothEndsAgreeOnTheNewConstants(unittest.TestCase):
    """The seal's two names and the two generations, held at both ends."""

    def worker(self):
        import importlib.util

        worker = DISTRIBUTION.parent / "worker"
        for one in (str(worker),
                    str(DISTRIBUTION / "src" / "baton_v12")):
            if one not in sys.path:
                sys.path.insert(0, one)
        place = worker / "claude_agent.py"
        spec = importlib.util.spec_from_file_location("claude_agent", place)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_the_seal_document_and_root_are_one_pair(self):
        worker = self.worker()
        self.assertEqual(dogfood_operator.SEAL_DOCUMENT, worker.SEAL_DOCUMENT)
        self.assertEqual(dogfood_operator.SEAL_ROOT, worker.SEAL_ROOT)

    def test_the_two_generations_are_one_pair(self):
        worker = self.worker()
        self.assertEqual(dogfood_operator._TASK_GENERATIONS,
                         worker.TASK_GENERATIONS)
        self.assertEqual(sorted(dogfood_operator._CONTEXT_TASK_MEMBERS),
                         sorted(worker.CONTEXT_TASK_MEMBERS))

    def test_both_ends_refuse_a_legacy_task_carrying_the_new_member(self):
        pin = "sha256:" + "0" * 64
        document = {**fixtures.gate_task(pin_digest=pin),
                    "schema": contract.LEGACY_TASK_SCHEMA}
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator.held_task(document)
        worker = self.worker()
        with self.assertRaises(worker.TaskRefusal):
            _worker_held(worker, document)

    def test_both_ends_accept_the_same_three_task(self):
        pin = fixtures.digest_of(fixtures.REPOSITORY / fixtures.VECTORS)
        document = fixtures.gate_task(pin_digest=pin)
        self.assertEqual(dogfood_operator.held_task(document), document)
        worker = self.worker()
        self.assertEqual(_worker_held(worker, document)[0], document)


def _worker_held(worker, document):
    """The worker's own read, applied to a document rather than a mount.

    Asked through the adapter's real reader rather than through a copy of its
    rules: a constants comparison standing in for a predicate is the confusion
    this campaign has already corrected once.
    """
    home = tempfile.mkdtemp(prefix="v12-w321776-held-")
    try:
        place = os.path.join(home, "task.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(document, writing)
        return worker._read_task(place)
    finally:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
