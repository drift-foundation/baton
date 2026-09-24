"""The corrected declaration, proved at BOTH adapters and downstream.

Owner 257834 selects "only the bounded output-declaration correction
identified in DIAGNOSIS.md… Correct emitted declarations for both stage roles
and prove them through real adapter selection and final-result/intake
contracts with deterministic providers. Adding proposal alone or making
outputs optional without downstream validation is insufficient."

Owner 258136 then selected the remainder review-2026-09-24T15-33-06Z found
missing: "deterministic provider output for both roles; carry actual result
bytes through sealing/intake and stage-result readers. Show positive receipts
and rejection of missing implementation proposal or review findings/logs.
Replace the task-reader sentinel as the positive proof and correct the
inaccurate test description."

So this module has three parts and none stands alone:

  1. ADMISSION. The corrected manifest is handed to the image-matched
     `ClaudeAgent.work` for an implementation turn AND for a review turn, and
     both must pass output selection. The old declaration and the
     proposal-only near-miss are kept as controls, because a correction that
     cannot show what it fixed is an assertion about itself. These cases stop
     at a sentinel on purpose: what they ask is whether a declaration is
     ACCEPTED, which is the question D1 diagnosed.
  2. REAL BYTES. Both roles then run to completion and write real trees under
     a real `/output`; the worker's own `answered` measures them and publishes
     `/output/output.json`, and the manager's `sealing._completion_envelope`
     VALIDATES those bytes. Validation is all that is -- it freezes nothing
     and commits nothing, and an earlier draft of this record called it a
     positive receipt, which it is not.
  3. COMMITTED RECEIPTS. A disposable `ControlStore` carries an attempt
     through the supported offer/claim/activation path, and
     `output.request_freeze` and `intake.request_intake` run with an adapter
     whose `seal` and `collect` ARE the product's own `sealing` functions over
     that tree. The frozen result and the intake receipt are then read back
     out of the store and handed to the stage-result readers as they stand.
     Nothing here composes a receipt.
  4. THE NEGATIVES. Optional is not permission to produce nothing, and where
     that is still enforced once nothing is required is the substance of the
     correction: `integration.driver.retain_proposal` -- executed, not cited --
     for a missing proposal and for an attempt with no completed result, and
     `review_cycles._review_result` for a committed result missing findings
     or logs.

WHAT IS REAL, stated precisely because an earlier draft of this docstring was
not. The seven image-matched worker source files, staged by hash into a fresh
tree exactly as `test_startup_boundary.py` does; the adapter's real `work`
path; the worker's real answer-holding and byte MEASUREMENT; and the manager's
real envelope intake, publication selector and verdict reader.

WHAT IS SUPPLIED, and there are three things rather than one:

  * `ClaudeAgent(run=...)`, as the accepted adapter suite injects it. The
    stand-in provider writes files into the working directory it is given --
    the only way a real provider changes anything -- and the review line's
    three object names are ANSWERED through the same seam rather than
    executed. No container, image, network, live provider, credential or
    version-control process is reached, and no repository is created, read or
    modified.
  * The CONTAINER side of the runtime adapter. `Sealer` stands in for it, and
    its two methods are the same two `sealing` calls `OciAdapter.seal` and
    `.collect` make; there is no runtime to quiesce because none was started,
    and `request_freeze` proves quiescence from durable observations anyway.
  * The WORKER'S OWN CLAIM for the retention case, named as a fixture where
    it is used: a proposal claim carries a base and a head, and the
    version-control-free profile these turns run produces neither.

WHERE THE SENTINEL IS STILL USED it is named as an admission check and is not
offered as evidence that anything was produced.

TWO SIDES FROM TWO PLACES, ON PURPOSE. The worker half -- `claude_agent` and
`baton_worker` -- is the IMAGE-MATCHED source, because the failure under
diagnosis is that image's. The manager half -- `sealing`, `integration.driver`,
`review_cycles` -- is the CURRENT tree, because that is what would admit a
future run. Anything proved here is therefore "this image's worker, against
this manager", which is the pairing a fresh packet would actually have.
"""
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ARTIFACT = (ROOT / "work/records/2026/09"
            / "finding-v12-single-implementation-proof"
            / "IMAGE-ARTIFACT-244216.json")
COMPOSER = ROOT / "work/records/2026/09/finding-v12-real-jobs-adoption-gate"

# ONE IDENTITY FOR THE WHOLE MODULE. A Work id carries its authority's prefix,
# which the settled validator checks; a pair that did not agree would be
# refused before anything these cases ask about was reached.
AUTHORITY = "a8d745e6" + "0" * 24
WORK = "a8d745e6-W1"
# The participant the accepted offer fixtures' session is bound to. A claim
# IS the binding, so an assignment naming anybody else is refused there --
# which is why this is one constant rather than a value each layer chooses.
PARTICIPANT = "baton.claude"

if str(COMPOSER) not in sys.path:                            # pragma: no cover
    sys.path.insert(0, str(COMPOSER))


class StagedImage(unittest.TestCase):
    """The seven image-matched worker files, staged by hash into a fresh tree.

    Shared by every class below so the image is staged once and identically,
    and so a later class cannot quietly drift onto current source.
    """

    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="w257627-union-")
        cls.addClassCleanup(cls.scratch.cleanup)
        image = json.loads(ARTIFACT.read_text())
        stage = Path(cls.scratch.name)
        # THE SAME HASH-MATCHED STAGING D1 USED. A correction proved against
        # unmatched current source would be a correction to a different image.
        for name, expected in image["all_worker_files"].items():
            relative = name.removeprefix("opt/baton/")
            candidates = [ROOT / "v12/worker" / relative,
                          ROOT / "v12/python/src/baton_v12" / relative]
            source = next(one for one in candidates if one.is_file())
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise AssertionError(f"image source drift: {source}")
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        sys.path.insert(0, str(stage))
        cls.addClassCleanup(sys.path.remove, str(stage))
        # A STAGED IMPORT MUST NOT OUTLIVE ITS STAGE, AND MUST NOT INHERIT
        # ONE EITHER. Both this module and the
        # accepted `test_startup_boundary` stage their own hash-matched tree,
        # and in one process the first import would win for both -- which that
        # module's own origin guard rightly refuses. So every module this
        # staging introduces is evicted again, and each module re-imports from
        # the tree it verified. Run order stops being a hidden input.
        def evict():
            for one in sorted(sys.modules):
                where = getattr(sys.modules[one], "__file__", None)
                if where and Path(where).is_relative_to(tempfile.gettempdir()):
                    del sys.modules[one]

        evict()                       # whatever an earlier stage left behind
        cls.addClassCleanup(evict)    # and whatever this one introduces
        cls.stage = stage
        cls.agent = importlib.import_module("claude_agent")
        cls.worker = importlib.import_module("baton_worker")
        for module in (cls.agent, cls.worker):
            if not Path(module.__file__).is_relative_to(stage):
                raise AssertionError(f"unexpected import origin: "
                                     f"{module.__file__}")

    # -- what the composer now emits ----------------------------------------

    def emitted(self):
        """The corrected declaration, read from the composer itself."""
        import prepare_two_jobs

        manifest = prepare_two_jobs.input_manifest(
            authority_uuid=AUTHORITY, work_id=WORK,
            task_path="task.json", raw=b"{}", artifact_id="task-1")
        return manifest["outputs"]

    def launch(self, role):
        """A launch document of the shape the adapter reads, for one role."""
        return {"schema": "baton.worker-launch/3", "role": role}


class TheCorrectedDeclarationIsAcceptedByBothRoles(StagedImage):
    """One manifest, two adapters, and the obligation that follows.

    ADMISSION ONLY. These cases ask whether a declaration is ACCEPTED, which
    is the question D1 diagnosed, so the task-reading sentinel is the right
    boundary for them and is kept. The positive proof that a turn actually
    PRODUCES anything is `BothRolesProduceRealBytes` below, where owner 258136
    moved it.
    """

    def test_the_emitted_declaration_is_the_union_and_none_is_required(self):
        """The correction itself, read off the composer not described."""
        declared = self.emitted()
        self.assertEqual(sorted(one["name"] for one in declared),
                         ["findings", "logs", "proposal"])
        for one in declared:
            with self.subTest(output=one["name"]):
                self.assertFalse(one["required"],
                                 "a required output is one some single turn "
                                 "cannot satisfy")
        # THE TYPES ARE THE PRODUCT'S OWN, not one type reused for three
        # different things.
        kinds = {one["name"]: one["type"] for one in declared}
        self.assertEqual(kinds["proposal"], "git-change-proposal")
        self.assertEqual(kinds["findings"], "directory-result")
        self.assertEqual(kinds["logs"], "directory-result")

    def test_the_union_is_the_images_own_set_and_not_this_dossiers(self):
        """The correction is bound to the adapter's constant, not to a list
        this record chose.

        `claude_agent.COMMON_OUTPUTS` states which outputs a SHARED Job
        carries, and `_selected` refuses any name outside it. Checking the
        emitted set against that constant is what stops the composer and the
        image from drifting apart silently later -- and the constant carries a
        fourth name, `provider-context-receipt`, which the adapter publishes
        itself rather than taking from the manifest, so the emitted set is a
        SUBSET rather than an equality.
        """
        emitted = {one["name"] for one in self.emitted()}
        self.assertLessEqual(emitted, set(self.agent.COMMON_OUTPUTS))
        self.assertEqual(emitted, set(self.agent.IMPLEMENTATION_OUTPUTS)
                         | set(self.agent.REVIEW_OUTPUTS))

    # -- the adapter half ----------------------------------------------------

    def selected(self, role):
        """What the image-matched adapter selects for one role, or its refusal.

        The provider seam is a Mock that fails if called, and `_read_task` is
        patched to a sentinel: output selection happens BEFORE either, so
        reaching the sentinel is exactly "this declaration was accepted".
        """
        child = Mock(side_effect=AssertionError("provider must not start"))
        reached = []
        with patch.object(self.agent, "_read_task",
                          side_effect=lambda *a, **k: reached.append(role)
                          or (_ for _ in ()).throw(_Reached())):
            try:
                self.agent.ClaudeAgent(run=child).work(self.launch(role),
                                                       self.emitted())
            except _Reached:
                pass
        child.assert_not_called()
        return reached

    def test_both_roles_pass_output_selection_on_the_corrected_manifest(self):
        """BOTH adapters, which is what "both stage roles" means.

        The original run only ever failed the implementation half, so a
        correction checked against one role would be half a correction.
        """
        for role in ("implementation", "review"):
            with self.subTest(role=role):
                self.assertEqual(self.selected(role), [role],
                                 f"the {role} adapter did not reach the task "
                                 f"reader on the corrected declaration")

    def test_the_original_declaration_still_refuses_implementation(self):
        """THE CONTROL: what the correction fixed, still broken without it."""
        child = Mock(side_effect=AssertionError("provider must not start"))
        original = [one for one in self.emitted()
                    if one["name"] in ("findings", "logs")]
        for one in original:
            one["required"] = True
        with patch.object(self.agent, "_read_task") as task:
            with self.assertRaises(self.agent.TaskRefusal) as caught:
                self.agent.ClaudeAgent(run=child).work(
                    self.launch("implementation"), original)
        self.assertIn("declares no proposal", str(caught.exception))
        task.assert_not_called()
        child.assert_not_called()

    def test_adding_proposal_alone_is_still_refused(self):
        """THE NEAR MISS owner 257834 names, measured rather than assumed."""
        child = Mock(side_effect=AssertionError("provider must not start"))
        partial = [dict(one) for one in self.emitted()]
        for one in partial:
            one["required"] = one["name"] in ("findings", "logs")
        with patch.object(self.agent, "_read_task") as task:
            with self.assertRaises(self.agent.TaskRefusal) as caught:
                self.agent.ClaudeAgent(run=child).work(
                    self.launch("implementation"), partial)
        self.assertIn("findings", str(caught.exception))
        task.assert_not_called()
        child.assert_not_called()

    # -- the downstream half -------------------------------------------------

    def split(self, role):
        """What the adapter itself says this role writes and answers absent.

        `_selected` is the product's own reader, and its two rules are the
        ones this correction has to satisfy: a role whose output is not
        declared refuses, and an output this role does not write may not be
        REQUIRED. Calling it directly is the downstream half's foundation --
        the statuses below are composed from its own `absent` answer.
        """
        produce = (self.agent.IMPLEMENTATION_OUTPUTS
                   if role == "implementation"
                   else self.agent.REVIEW_OUTPUTS)
        return self.agent._selected(self.emitted(), produce, role)

    def test_each_role_writes_its_half_and_answers_the_rest_absent(self):
        """The split the shared Job depends on, for BOTH roles."""
        written, absent = self.split("implementation")
        self.assertEqual([one["name"] for one in written], ["proposal"])
        self.assertEqual(sorted(one["name"] for one in absent),
                         ["findings", "logs"])

        written, absent = self.split("review")
        self.assertEqual(sorted(one["name"] for one in written),
                         ["findings", "logs"])
        self.assertEqual([one["name"] for one in absent], ["proposal"])

    def test_the_absent_half_is_reported_as_missing_optional(self):
        """OPTIONAL IS NOT SILENCE. The other role's half is REPORTED.

        `_absent` composes the entries the completion envelope carries, so a
        stage that produced its own half still states, output by output, what
        it did not write. That is the fact a final-result or intake obligation
        reads -- the correction moves the judgement to the evidence rather
        than removing it.
        """
        _written, absent = self.split("implementation")
        entries = self.agent._absent(absent)
        self.assertEqual(sorted(one["name"] for one in entries),
                         ["findings", "logs"])
        self.assertEqual({one["status"] for one in entries},
                         {"missing-optional"})
        # AND `missing-optional` IS A CLOSED STATUS the worker knows, not a
        # string this test invented.
        import baton_worker

        for one in entries:
            self.assertIn(one["status"], baton_worker.OUTPUT_STATUSES)

    def test_a_required_other_half_is_refused_by_name(self):
        """The rule that makes "none required" necessary rather than lax.

        Marking the other role's half required is exactly the declaration the
        original run carried, and `_selected` refuses it in its own words.
        """
        declared = [dict(one) for one in self.emitted()]
        for one in declared:
            if one["name"] in ("findings", "logs"):
                one["required"] = True
        with self.assertRaises(self.agent.TaskRefusal) as caught:
            self.agent._selected(declared,
                                 self.agent.IMPLEMENTATION_OUTPUTS,
                                 "implementation")
        self.assertIn("declared required", str(caught.exception))
        self.assertIn("missing-optional", str(caught.exception))


    # -- the downstream half: publication intake and §12 rule 15 -------------
    #
    # OWNER 257834: "prove them through real adapter selection and
    # final-result/intake contracts… making outputs optional without
    # downstream validation is insufficient." That objection is exactly right,
    # and answering it is what found where the obligation actually lives.
    # `required` is NOT what makes an implementation produce a proposal.
    # `integration.driver._one_output` is: publication selects the single
    # output of TYPE `git-change-proposal` and demands it `present` with both
    # its artifact and its content manifest. So:
    #
    #   * OPTIONAL IS NOT PERMISSION -- a stage that produced no proposal is
    #     refused at publication, by name, whatever its declaration said;
    #   * the shared manifest is SAFE -- a review result answers `proposal`
    #     missing-optional and can never be mistaken for a publishable one;
    #   * and the ORIGINAL declaration could never have published at all,
    #     because it carried no proposal-typed output for this selector to
    #     find. The correction is what makes publication REACHABLE, not a
    #     loosening that lets something through.
    #
    # The TYPES therefore carry weight rather than decoration: three outputs
    # of one type would give this selector three matches and no answer.

    def frozen(self, role):
        """A frozen result over the corrected declaration, for one role.

        Composed from `self.emitted()` and the ADAPTER'S OWN split, so the
        statuses below are the ones the adapter would author rather than ones
        this test chose for it.
        """
        written, absent = self.split(role)
        produced = {one["name"] for one in written}
        self.assertEqual({one["name"] for one in absent},
                         {one["name"] for one in self.emitted()} - produced)
        outputs = []
        for one in self.emitted():
            present = one["name"] in produced
            outputs.append({
                "name": one["name"], "type": one["type"],
                "path": one["path"],
                "status": "present" if present else "missing-optional",
                "artifact": f"artifact-{one['name']}" if present else None,
                "content_manifest": ({"tree_digest": "sha256:" + "b" * 64}
                                     if present else None)})
        return {"outputs": outputs}

    def test_the_implementation_result_is_the_one_publication_selects(self):
        """The correction reaches publication, by exactly one role."""
        from baton_v12.integration import driver

        output = driver._one_output(self.frozen("implementation"))
        self.assertEqual(output["name"], "proposal")
        self.assertEqual(output["type"], driver.PROPOSAL_OUTPUT)
        self.assertEqual(output["status"], "present")

    def test_a_review_result_can_never_be_published_as_a_proposal(self):
        """WHY ONE SHARED MANIFEST IS SAFE for two roles.

        Both stages declare `proposal` and only the implementation writes it.
        The review's frozen result answers it absent, and publication refuses
        that result rather than selecting the review's own half.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        with self.assertRaises(ContractRefusal) as caught:
            driver._one_output(self.frozen("review"))
        self.assertIn("not present", str(caught.exception))

    def test_optional_is_not_permission_to_produce_no_proposal(self):
        """THE OBJECTION OWNER 257834 RAISED, measured rather than argued.

        An implementation turn that published nothing is refused at
        publication by the output TYPE and its status -- not by the `required`
        flag this correction cleared. The obligation MOVED to a contract that
        reads the frozen bytes; it was not removed.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        empty = self.frozen("implementation")
        for one in empty["outputs"]:
            one["status"] = "missing-optional"
            one["artifact"] = None
            one["content_manifest"] = None
        with self.assertRaises(ContractRefusal) as caught:
            driver._one_output(empty)
        self.assertIn("not present", str(caught.exception))

    def retained(self):
        """The two ORIGINAL declarations, read from the retained evidence.

        Not a reconstruction: these are the exact `outputs` lists the failed
        attempts carried, so the controls below are about what actually ran.
        """
        evidence = json.loads((HERE / "EVIDENCE.json").read_text())
        both = [one["outputs"] for one in evidence["attempts"]]
        self.assertEqual(len(both), 2)
        return both

    def test_the_original_declaration_could_never_have_published(self):
        """The failed run was unpublishable even past the adapter.

        Publication selects by output TYPE, and neither original output was a
        proposal type -- so it finds ZERO and refuses. An independent second
        statement that the declaration was the defect, reached without the
        adapter at all.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        for index, declared in enumerate(self.retained()):
            with self.subTest(attempt=index):
                original = {"outputs": [
                    {"name": one["name"], "type": one["type"],
                     "path": one["path"], "status": "present",
                     "artifact": f"artifact-{one['name']}",
                     "content_manifest": {"tree_digest": "sha256:" + "b" * 64}}
                    for one in declared]}
                with self.assertRaises(ContractRefusal) as caught:
                    driver._one_output(original)
                self.assertIn("0 " + driver.PROPOSAL_OUTPUT,
                              str(caught.exception))

    def test_the_original_output_type_was_not_in_the_managers_vocabulary(self):
        """A SECOND defect in the same declaration, reported not repaired.

        Both original outputs were typed `text-result`, and the manager's own
        `OUTPUT_TYPES` is `git-change-proposal, directory-result,
        record-output`. Measured: no validator enforces that vocabulary, so
        the type was accepted and would simply never have matched any
        type-driven selector. The correction types the review's half
        `directory-result` -- which is what the review turn actually writes, a
        directory of two files -- so this is a real repair rather than a
        rename, but the ABSENT ENFORCEMENT is a separate observation and is
        left as one. It belongs to no owner's selected scope here.
        """
        from baton_v12.worker_manager import schema

        for declared in self.retained():
            for one in declared:
                with self.subTest(output=one["name"]):
                    self.assertEqual(one["type"], "text-result")
                    self.assertNotIn(one["type"], schema.OUTPUT_TYPES)
        for one in self.emitted():
            with self.subTest(corrected=one["name"]):
                self.assertIn(one["type"], schema.OUTPUT_TYPES)

    # -- §12 rule 15: the manager against the exact declarations -------------

    def declarations(self):
        """The manager-side view of the corrected declaration."""
        return {one["name"]: {"type": one["type"], "path": one["path"],
                              "required": one["required"]}
                for one in self.emitted()}

    def envelope(self, role):
        """The worker's published completion envelope for one role."""
        return {"outputs": [{"name": one["name"], "type": one["type"],
                             "path": one["path"], "status": one["status"]}
                            for one in self.frozen(role)["outputs"]]}

    def test_both_roles_envelopes_answer_the_assignment(self):
        """BOTH completion envelopes pass the manager's own rule 15."""
        from baton_v12.worker_manager import sealing

        for role in ("implementation", "review"):
            with self.subTest(role=role):
                answered = sealing._answers_the_assignment(
                    self.envelope(role), self.declarations())
                self.assertEqual(len(answered["outputs"]), 3)

    def test_rule_15_refuses_the_required_variant_at_the_manager(self):
        """Required was not an option DOWNSTREAM either, not just at the
        adapter.

        Had the union been declared with the other role's half required, the
        manager would refuse the very envelope the adapter authors -- so both
        ends agree about what a shared Job's stage may answer.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import sealing

        declared = self.declarations()
        for name in ("findings", "logs"):
            declared[name]["required"] = True
        with self.assertRaises(ContractRefusal) as caught:
            sealing._answers_the_assignment(self.envelope("implementation"),
                                            declared)
        self.assertIn("missing-optional", str(caught.exception))
        self.assertIn("rule 15", str(caught.exception))


class _Reached(Exception):
    """The task reader was reached, which is all those cases ask of it."""


# -- W257627, owner 258136: the same declaration, carried in actual bytes -----
#
# THE GAP review-2026-09-24T15-33-06Z NAMED, and it named it correctly: the
# cases above stop at a sentinel, so neither role ever produced result bytes,
# and the documents handed to the downstream readers were abbreviated ones this
# module composed. Owner 258136 selects the remainder -- "deterministic
# provider output for both roles; carry actual result bytes through
# sealing/intake and
# stage-result readers… positive receipts and rejection of missing
# implementation proposal or review findings/logs. Replace the task-reader
# sentinel as the positive proof."
#
# WHAT IS REAL BELOW, and it is the whole chain rather than a helper from it:
#
#   * the image-matched `ClaudeAgent.work` runs to completion for BOTH roles
#     and writes real trees under a real `/output`;
#   * `baton_worker.answered` -- the worker's own reader -- holds those answers
#     against the declarations and MEASURES the bytes, so the content manifests
#     below are measurements rather than strings this test chose;
#   * `baton_worker.publish_completion` writes the real `/output/output.json`;
#   * the manager's `sealing._completion_envelope` reads THOSE BYTES back off
#     the filesystem, validates them with the settled `completionManifest`
#     validator, holds them against this assignment and recomputes the digest.
#
# THE INJECTED SEAM IS `run`, exactly as the accepted `test_claude_agent`
# injects it: the adapter's real code path executes and one capability is
# supplied. Nothing starts a container, an image, a network, a live provider or
# a version-control binary -- the line observations below are answered by the
# same injected seam, so no repository is created, read or modified anywhere.


class RealTurnCase(StagedImage):
    """A staged `/input`, a writable `/output`, and an injected provider.

    The roots are patched on the staged modules themselves, as the accepted
    adapter suite does with the same constants: they are CONSTANTS of the
    workload contract, so there is no operand a fixture could supply.
    """

    BASE = "4" * 40
    HEAD = "5" * 40
    TREE = "6" * 40

    ASSIGNMENT = {"work_ref": {"authority_uuid": AUTHORITY,
                               "work_id": WORK},
                  "participant": PARTICIPANT, "generation": 1}

    def setUp(self):
        home = tempfile.mkdtemp(prefix="w257627-turn-")
        self.addCleanup(shutil.rmtree, home, True)
        self.home = home
        self.inputs = os.path.join(home, "input")
        self.outputs = os.path.join(home, "output")
        self.scratch = os.path.join(home, "scratch")
        self.credentials = os.path.join(home, "credentials")
        for place in (self.inputs, self.outputs, self.scratch,
                      self.credentials):
            os.makedirs(place)
        self.source = os.path.join(self.inputs, "source")
        os.makedirs(self.source)
        self.write(os.path.join(self.source, "harness.py"),
                   "print('the staged harness')\n")
        self.write(os.path.join(self.source, "preflight.py"),
                   "def _observed_readable():\n    return True\n")
        # A FILE THAT SAYS IT IS NOT A CREDENTIAL, which is the accepted
        # suite's own device: its content is never read, and a real bearer
        # would prove nothing this does not.
        self.write(os.path.join(self.credentials, "claude"),
                   "not-a-credential\n")
        for module, name, value in (
                (self.agent, "INPUT_ROOT", self.inputs),
                (self.agent, "OUTPUT_ROOT", self.outputs),
                (self.agent, "CREDENTIAL_ROOT", self.credentials),
                (self.worker, "OUTPUT_ROOT", self.outputs)):
            held = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, held)
        self.calls = []

    @staticmethod
    def write(place, body):
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    def task(self, document):
        self.write(os.path.join(self.inputs, self.agent.TASK_DOCUMENT),
                   json.dumps(document))

    # -- the two frozen tasks, one per role ----------------------------------

    def implementation_task(self):
        return {"schema": "baton.dogfood-task/2",
                "task_id": "w257627-union-implementation",
                "instructions": "Add focused coverage for _observed_readable.",
                "verification": ["python3", "harness.py"],
                "source_root": "source",
                "source_profile": "generic",
                "declared_base": None}

    def review_task(self):
        profiles = importlib.import_module("source_profiles.checkout")
        return {"schema": "baton.dogfood-task/2",
                "task_id": "w257627-union-review",
                "instructions": "Assess the frozen checkpoint.",
                # THE TASK DOCUMENT IS ONE SHAPE FOR BOTH ROLES, and it
                # requires a non-empty verification word list. A review turn
                # never runs it -- `_review` verifies nothing -- so this is
                # the contract being satisfied, not a command being invoked,
                # and the injected seam records that it was never called.
                "verification": ["python3", "harness.py"],
                "source_root": "source",
                "source_profile": profiles.GIT_LINE_PROFILE,
                "declared_base": self.BASE}

    # -- the one injected capability -----------------------------------------

    def runner(self, *, writes=None, status=0, verify=0):
        """One recorded process-running capability, and the ONLY seam.

        `writes` is what the stand-in provider puts in its working directory,
        which is the only way a real provider changes anything -- so a
        stand-in that wrote nowhere else is exactly as capable here.

        The line vectors are ANSWERED rather than executed. A review turn
        reads three object names off the mounted line; answering them here
        means no version-control process runs and no repository exists, which
        is both faithful to what the adapter does with the answers and a
        stricter statement than "it did not modify one".
        """
        answers = {f"{self.BASE}^{{commit}}": self.BASE,
                   "HEAD": self.HEAD, "HEAD^{tree}": self.TREE}

        def run(argv, **options):
            argv = list(argv)
            self.calls.append(argv)
            if argv[0] == "git":
                if argv[-3:-1] != ["rev-parse", "--verify"]:
                    raise AssertionError(f"unexpected line vector: {argv}")
                return subprocess.CompletedProcess(
                    argv, 0, answers[argv[-1]] + "\n", "")
            if argv[0] == self.agent.PROVIDER_PROGRAM:
                for name, body in (writes or {}).items():
                    self.write(os.path.join(options["cwd"], name), body)
                return subprocess.CompletedProcess(argv, status, None, None)
            return subprocess.CompletedProcess(argv, verify, None, None)

        return run

    def report(self, verdict="accepted", findings="One finding.\n"):
        return json.dumps({"schema": self.agent.REVIEW_REPORT_SCHEMA,
                           "verdict": verdict, "findings": findings})

    # -- one real turn, end to end -------------------------------------------

    def turn(self, role, *, writes=None, status=0):
        """Run the real adapter for one role and answer what it reported."""
        self.task(self.implementation_task() if role == "implementation"
                  else self.review_task())
        agent = self.agent.ClaudeAgent(run=self.runner(writes=writes,
                                                       status=status),
                                       home=self.scratch)
        return agent.work(self.launch(role), self.emitted())

    def implemented(self):
        return self.turn("implementation",
                         writes={"harness.py": "print('now covered')\n"})

    def reviewed(self, **operands):
        return self.turn("review",
                         writes={self.agent.REVIEW_REPORT:
                                 self.report(**operands)})

    def published(self, reported):
        """The worker's OWN reader and measurement over the real trees."""
        return self.worker.answered(self.emitted(), reported["outputs"])

    def envelope_on_disk(self, reported):
        """Publish `/output/output.json` the way the worker does."""
        return self.worker.publish_completion(
            self.ASSIGNMENT, reported["disposition"],
            self.published(reported))

    def declarations(self):
        return {one["name"]: {"type": one["type"], "path": one["path"],
                              "required": one["required"]}
                for one in self.emitted()}

    def taken_by_the_manager(self, disposition, *, declared=None):
        """The manager reading those bytes back off the filesystem."""
        from baton_v12.worker_manager import sealing

        return sealing._completion_envelope(
            {"workspace": self.outputs},
            self.declarations() if declared is None else declared,
            self.ASSIGNMENT, disposition)


class BothRolesProduceRealBytes(RealTurnCase):
    """THE POSITIVE PROOF, with the sentinel replaced by actual output."""

    def test_the_implementation_turn_writes_a_real_proposal_tree(self):
        reported = self.implemented()
        self.assertEqual(reported["disposition"], "completed")
        answered = {one["name"]: one["status"] for one in reported["outputs"]}
        self.assertEqual(answered, {"proposal": "present",
                                    "findings": "missing-optional",
                                    "logs": "missing-optional"})
        # REAL BYTES, not a status. The four declared members of a proposal
        # are on the filesystem and the candidate carries the whole tree.
        for name in ("candidate", "change.patch", "result.json",
                     "verification.txt"):
            self.assertTrue(
                os.path.exists(os.path.join(self.outputs, "proposal", name)),
                name)
        self.assertEqual(
            sorted(os.listdir(os.path.join(self.outputs, "proposal",
                                           "candidate"))),
            ["harness.py", "preflight.py"])
        self.assertFalse(os.path.exists(os.path.join(self.outputs,
                                                     "findings")))

    def test_the_review_turn_writes_real_findings_and_logs_trees(self):
        reported = self.reviewed()
        self.assertEqual(reported["disposition"], "completed")
        answered = {one["name"]: one["status"] for one in reported["outputs"]}
        self.assertEqual(answered, {"proposal": "missing-optional",
                                    "findings": "present", "logs": "present"})
        findings = os.path.join(self.outputs, "findings")
        self.assertEqual(sorted(os.listdir(findings)),
                         sorted([self.agent.REVIEW_FINDINGS,
                                 self.agent.REVIEW_RESULT]))
        self.assertEqual(os.listdir(os.path.join(self.outputs, "logs")),
                         [self.agent.REVIEW_LOG])
        self.assertFalse(os.path.exists(os.path.join(self.outputs,
                                                     "proposal")))

    def test_no_version_control_process_and_one_provider_turn(self):
        """WHAT THE INJECTED SEAM SAW, stated rather than assumed.

        A review turn reads exactly three object names off the line and runs
        the provider exactly once. Recording it here is what lets this module
        claim no repository was created, read or modified.
        """
        self.reviewed()
        vectors = [one for one in self.calls if one[0] == "git"]
        # THE OBSERVATION BRACKETS THE PROVIDER TURN, so all three names are
        # read again afterwards -- that is the adapter refusing to review a
        # line that moved under it, and the count is asserted rather than
        # rounded off.
        reading = [f"{self.BASE}^{{commit}}", "HEAD", "HEAD^{tree}"]
        self.assertEqual([one[-1] for one in vectors], reading * 2)
        for one in vectors:
            self.assertEqual(one[-3:-1], ["rev-parse", "--verify"],
                             "only reads, and only of object names")
        providers = [one for one in self.calls
                     if one[0] == self.agent.PROVIDER_PROGRAM]
        self.assertEqual(len(providers), 1)


class TheWorkerMeasuresWhatWasActuallyWritten(RealTurnCase):
    """`baton_worker.answered` over the real trees, not a composed document."""

    def test_each_role_publishes_measured_content_for_its_own_half(self):
        for role, produced in (("implementation", {"proposal"}),
                               ("review", {"findings", "logs"})):
            with self.subTest(role=role):
                self.setUp()
                reported = (self.implemented() if role == "implementation"
                            else self.reviewed())
                published = self.published(reported)
                self.assertEqual({one["name"] for one in published},
                                 {"proposal", "findings", "logs"})
                for one in published:
                    if one["name"] in produced:
                        self.assertEqual(one["status"], "present")
                        # MEASURED: entries, bytes and a tree digest over the
                        # bytes this turn actually wrote.
                        content = one["content_manifest"]
                        self.assertGreater(content["entry_count"], 0)
                        self.assertGreater(content["total_bytes"], 0)
                        self.assertTrue(
                            content["tree_digest"].startswith("sha256:"))
                    else:
                        self.assertEqual(one["status"], "missing-optional")
                        self.assertIsNone(one["content_manifest"])

    def test_the_measurement_is_of_these_bytes_and_moves_when_they_do(self):
        """A digest that did not depend on the bytes would prove nothing."""
        reported = self.reviewed(findings="One finding.\n")
        first = {one["name"]: one["content_manifest"]
                 for one in self.published(reported)}
        self.setUp()
        reported = self.reviewed(findings="A different finding entirely.\n")
        second = {one["name"]: one["content_manifest"]
                  for one in self.published(reported)}
        self.assertNotEqual(first["findings"]["tree_digest"],
                            second["findings"]["tree_digest"])

    def test_an_agent_cannot_answer_an_output_it_did_not_write(self):
        """The worker refuses a claim its own measurement contradicts."""
        reported = self.reviewed()
        lying = [dict(one) for one in reported["outputs"]]
        for one in lying:
            if one["name"] == "proposal":
                one["status"] = "present"
        with self.assertRaises(self.worker.WorkerFault) as caught:
            self.worker.answered(self.emitted(),
                                 [{"name": one["name"],
                                   "status": one["status"],
                                   "result_metadata": one["result_metadata"]}
                                  for one in lying])
        self.assertIn("is not there", str(caught.exception))


class TheManagerTakesTheRealEnvelope(RealTurnCase):
    """POSITIVE RECEIPTS: the manager reads the published bytes back."""

    def test_both_roles_envelopes_are_taken_from_the_filesystem(self):
        for role in ("implementation", "review"):
            with self.subTest(role=role):
                self.setUp()
                reported = (self.implemented() if role == "implementation"
                            else self.reviewed())
                written = self.envelope_on_disk(reported)
                place = os.path.join(self.outputs,
                                     self.worker.OUTPUT_MANIFEST)
                self.assertTrue(os.path.exists(place))
                taken, taken_digest = self.taken_by_the_manager(
                    reported["disposition"])
                # THE MANAGER'S OWN READING, not the worker's return value.
                self.assertEqual(taken["manifest_digest"],
                                 written["manifest_digest"])
                self.assertEqual(taken_digest, written["manifest_digest"])
                self.assertEqual(
                    {one["name"]: one["status"] for one in taken["outputs"]},
                    {one["name"]: one["status"]
                     for one in written["outputs"]})

    def test_the_manager_refuses_an_envelope_for_another_assignment(self):
        """The receipt is bound to THIS attempt, proved on real bytes."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import sealing

        reported = self.implemented()
        self.envelope_on_disk(reported)
        other = json.loads(json.dumps(self.ASSIGNMENT))
        other["generation"] = 2
        with self.assertRaises(ContractRefusal) as caught:
            sealing._completion_envelope({"workspace": self.outputs},
                                         self.declarations(), other,
                                         reported["disposition"])
        self.assertIn("another assignment", str(caught.exception))

    def test_a_required_other_half_is_refused_against_real_bytes(self):
        """Required was never an option, now shown end to end.

        The worker refuses to PUBLISH the envelope and the manager refuses to
        TAKE one, so the union had to be optional at both ends. The publish
        side is checked first because a worker that will not publish is where
        the failed run would have stopped.
        """
        from baton_v12.contracts import ContractRefusal

        reported = self.implemented()
        required = [dict(one) for one in self.emitted()]
        for one in required:
            if one["name"] in ("findings", "logs"):
                one["required"] = True
        with self.assertRaises(self.worker.WorkerFault) as caught:
            self.worker.answered(required, reported["outputs"])
        self.assertIn("is required and is answered", str(caught.exception))

        self.envelope_on_disk(reported)
        declared = self.declarations()
        for name in ("findings", "logs"):
            declared[name]["required"] = True
        with self.assertRaises(ContractRefusal) as refused:
            self.taken_by_the_manager(reported["disposition"],
                                      declared=declared)
        self.assertIn("missing-optional", str(refused.exception))


class MissingHalvesAreRejectedDownstream(RealTurnCase):
    """THE NEGATIVES owner 258136 names, each at its own real reader."""

    def measured_result(self, reported):
        """A frozen result over the REAL measurements, for publication."""
        return {"outputs": [
            {"name": one["name"], "type": one["type"], "path": one["path"],
             "status": one["status"],
             # CARRIED OPAQUELY, exactly as the frozen result carries it: the
             # worker's claim travels in `result_metadata` and the manager
             # composes nothing into it.
             "result_metadata": one["result_metadata"],
             "content_manifest": one["content_manifest"],
             "artifact": ({"artifact_id": f"attempt:{one['name']}",
                           "content_digest":
                               one["content_manifest"]["tree_digest"],
                           "bytes": one["content_manifest"]["total_bytes"],
                           "media_type": "application/octet-stream",
                           "locator": "file://"
                                      + os.path.join(self.outputs,
                                                     one["path"])}
                          if one["status"] == "present" else None)}
            for one in self.published(reported)]}

    def test_a_real_implementation_result_publishes_and_a_review_cannot(self):
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        output = driver._one_output(self.measured_result(self.implemented()))
        self.assertEqual(output["name"], "proposal")
        self.assertEqual(output["status"], "present")
        # AND THE DIGEST IS THE MEASURED ONE, so publication is selecting the
        # bytes this turn wrote rather than a value the test supplied.
        self.assertEqual(output["artifact"]["content_digest"],
                         output["content_manifest"]["tree_digest"])

        self.setUp()
        with self.assertRaises(ContractRefusal) as caught:
            driver._one_output(self.measured_result(self.reviewed()))
        self.assertIn("not present", str(caught.exception))

    def test_an_implementation_that_produced_no_candidate_cannot_publish(self):
        """OPTIONAL IS NOT PERMISSION, on a real turn that produced nothing.

        MEASURED, AND IT CORRECTED WHAT I EXPECTED TWICE. I assumed a turn
        that changed nothing would answer its proposal absent, so
        `_one_output`'s present check would refuse it. It does not: the
        adapter writes the proposal tree either way -- the transcript and the
        empty patch ARE the account of a turn that produced nothing -- so the
        output is present and that selector is satisfied. I then expected
        `_claim_of` to be the discriminator. It is not the one HERE: the
        worker's claim carries a base and a head, and this suite runs the
        version-control-free `generic` profile, so NEITHER turn attaches one
        and that reader refuses both. Saying so is the point -- it bounds what
        this evidence covers instead of borrowing a refusal that fires anyway.

        WHAT DOES DISCRIMINATE, measured from the two real turns, is the
        DISPOSITION: a turn that produced a candidate answers `completed` and
        one that produced nothing answers `unable`. That member is exactly
        what publication's precondition reads -- `retain_proposal` refuses an
        attempt with "no completed frozen result to propose". That precondition
        is NOT executed here, because it takes a live manager store and a
        publisher session; what is established is that the value it reads
        differs between a turn that produced a candidate and one that did not.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        reported = self.turn("implementation", writes={})
        self.assertEqual(reported["disposition"], "unable")
        empty = driver._one_output(self.measured_result(reported))
        self.assertEqual(empty["result_metadata"], {})
        with self.assertRaises(ContractRefusal) as caught:
            driver._claim_of(empty)
        self.assertIn("carries no", str(caught.exception))

        # THE OTHER TURN, for the comparison that makes the disposition the
        # discriminator rather than a value that is always the same.
        self.setUp()
        made = self.implemented()
        self.assertEqual(made["disposition"], "completed")
        # ...and `_claim_of` refuses this one too, which is why it is named
        # above as not discriminating under this profile.
        with self.assertRaises(ContractRefusal):
            driver._claim_of(driver._one_output(self.measured_result(made)))

    def test_a_review_missing_findings_or_logs_earns_no_verdict(self):
        """THE REVIEW-SIDE NEGATIVE, at the reader that owns it.

        `review_cycles._review_result` is where a verdict is admitted, and it
        requires SEPARATELY FROZEN findings and logs. A review that produced
        only one of them is refused there -- so making the declaration
        optional did not make a half-finished review acceptable.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import review_cycles

        reported = self.reviewed()
        artifacts = [
            {"output_name": one["name"],
             "artifact_id": f"attempt:{one['name']}",
             "media_type": "application/octet-stream",
             "bytes": one["content_manifest"]["total_bytes"],
             "content_digest": one["content_manifest"]["tree_digest"],
             "locator": "file://" + os.path.join(self.outputs, one["path"])}
            for one in self.published(reported)
            if one["status"] == "present"]
        self.assertEqual(sorted(one["output_name"] for one in artifacts),
                         ["findings", "logs"])

        def frozen(kept):
            return {"attempt_id": "attempt-" + "c" * 32,
                    "result_id": "result-" + "c" * 32,
                    "disposition": "completed",
                    "manifest_digest": "sha256:" + "d" * 64,
                    "freeze_operation_id": "output.freeze:" + "e" * 64,
                    "frozen_at": "2026-09-24T00:00:00.000Z",
                    "artifacts": [one for one in artifacts
                                  if one["output_name"] in kept]}

        # BOTH HALVES: the verdict is admitted.
        taken = review_cycles._review_result(frozen({"findings", "logs"}))
        self.assertEqual(len(taken["artifacts"]), 2)

        # EITHER HALF MISSING: no verdict, by name.
        for kept in ({"findings"}, {"logs"}, set()):
            with self.subTest(kept=sorted(kept)):
                with self.assertRaises(ContractRefusal) as caught:
                    review_cycles._review_result(frozen(kept))
                self.assertIn("separately frozen findings and logs",
                              str(caught.exception))

    def test_a_review_whose_provider_reported_nothing_is_unable(self):
        """A turn with no report places no claim, on a real run.

        The provider writes no report at all. The adapter answers `unable`
        and reports `findings` absent -- so there is nothing for the verdict
        reader to admit, and the refusal above is reached from a real turn
        rather than only from a hand-trimmed artifact list.
        """
        reported = self.turn("review", writes={})
        self.assertEqual(reported["disposition"], "unable")
        answered = {one["name"]: one["status"] for one in reported["outputs"]}
        self.assertEqual(answered["findings"], "missing-optional")
        published = self.published(reported)
        present = sorted(one["name"] for one in published
                         if one["status"] == "present")
        self.assertNotIn("findings", present)


# -- W257627, owner 258233: committed receipts and the publication gate -------
#
# review-2026-09-24T16-14-50Z found two portions of owner 258136 still unmet,
# and was right about both: `sealing._completion_envelope` VALIDATES an
# envelope, it does not freeze, commit or collect anything, so "positive
# receipts" and "whole chain" overstated what the cases above establish; and
# the implementation rejection precondition was never executed, so contrasting
# `unable` with `completed` did not prove the publication distinction.
#
# Owner 258233: "Use disposable real manager state and supported freeze/collect
# operations; read committed receipts and pass their actual bindings to
# stage-result readers. Exercise otherwise-valid implementation fixtures
# showing successful proposal retention and rejection before publication when
# proposal is missing. Do not substitute constructed receipt-like documents."
#
# So nothing below composes a receipt. A disposable `ControlStore` is opened,
# an attempt is carried through the supported offer/claim/activation path, and
# `output.request_freeze` and `intake.request_intake` are called with an
# adapter whose `seal` and `collect` ARE the product's own `sealing` functions
# over the real tree the adapter turn wrote. The frozen result and the intake
# receipt are then READ BACK out of the store and handed to the stage-result
# readers as they stand.


class Sealer:
    """The runtime adapter's two capabilities, and nothing invented.

    `OciAdapter.seal` and `.collect` are thin wrappers over exactly these two
    `sealing` calls -- the measurement, staging and shape all live there. What
    this stands in for is the CONTAINER, not the manager: there is no runtime
    to quiesce because no runtime was started, and `request_freeze` proves
    quiescence from the durable observations either way.
    """

    def __init__(self, *, roots, declared, identity, custody, input_digest):
        self.roots = roots
        self.declared = declared
        self.identity = identity
        self.custody = custody
        self.input_digest = input_digest
        self.sealed = []
        self.collected = []

    def seal(self, request):
        from baton_v12.worker_manager import sealing

        self.sealed.append(request["attempt_id"])
        return sealing.sealed_result(
            request, roots=self.roots, declared=self.declared,
            identity=self.identity, custody=self.custody,
            input_manifest_digest=self.input_digest)

    def collect(self, operands):
        from baton_v12.worker_manager import sealing

        self.collected.append(operands["attempt_id"])
        return sealing.collected_result(operands, custody=self.custody,
                                        declared=self.declared)


class Publisher:
    """The one publisher capability retention reads: the canonical target."""

    participant = PARTICIPANT

    def __init__(self, target):
        self.target = target

    def canonical_target(self):
        return self.target


class CommittedReceiptCase(RealTurnCase):
    """One attempt, carried to a committed freeze and a committed intake."""

    ATTEMPT = "attempt-" + "7" * 32
    POLICY = "sha256:" + "2" * 64
    ADAPTER_DIGEST = "sha256:" + "3" * 64

    def setUp(self):
        super().setUp()
        from tests.manager.test_offers import (NOW, PROFILE, ROUTE, SCOPE,
                                               FakeSession, decision,
                                               fake_claim_signature)
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import AuthorityPort, ControlStore

        self.NOW, self.PROFILE = NOW, PROFILE
        self.control = os.path.join(self.home, "control.sqlite3")
        self.store = ControlStore.open(self.control, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        manager.certify_profile(self.store, "runtime", "reference", PROFILE)
        storage = os.path.join(self.home, "workspace-store")
        os.makedirs(storage, exist_ok=True)
        manager.workspaces.configure_workspace_storage(self.store, storage)
        self.custody = os.path.join(self.home, "custody")
        os.makedirs(self.custody, exist_ok=True)

        self.live = {"work_ref": {"authority_uuid": AUTHORITY,
                                  "work_id": WORK},
                     "participant": self.ASSIGNMENT["participant"],
                     "generation": 1}
        session = FakeSession(
            work={"status": "open", "phase": "queued", "handler": None,
                  "gate": None, "authority_uuid": AUTHORITY,
                  "scope": SCOPE, "route": ROUTE})
        fixed = json.loads(json.dumps(self.live))
        session.claim_answer = {"assignment": fixed, "claim_event": 1,
                                "decision": decision()}
        session.live_assignment = json.loads(json.dumps(self.live))
        self.port = AuthorityPort(session, fake_claim_signature)

    # THE ASSIGNMENT THE WHOLE CHAIN AGREES ON. `RealTurnCase` publishes the
    # envelope under this, the offer path fixes the same one, and the freeze
    # compares them -- so a disagreement is a refusal rather than a fixture
    # that quietly proved nothing.
    def manifest(self):
        import prepare_two_jobs

        return prepare_two_jobs.input_manifest(
            authority_uuid=AUTHORITY, work_id=WORK, task_path="task.json",
            raw=b"{}", artifact_id="task-1")

    def admitted(self, disposition):
        """The supported path from offer to an answered, quiescent attempt."""
        import baton_v12.worker_manager as manager

        self.input_digest = manager.retain_manifest(
            self.store, self.manifest(), "inputManifest")["digest"]
        manager.issue_offer(self.store, self.port, offer_id="offer-1",
                            work_id=WORK, runtime_attempt_id=self.ATTEMPT,
                            input_digest=self.input_digest,
                            policy_digest=self.POLICY,
                            profile_digest=self.PROFILE,
                            profile_name="reference",
                            mint_bearer=lambda: "bearer-1")
        manager.accept_offer(self.store, self.port, offer_id="offer-1",
                             decision="accept", bearer="bearer-1",
                             now=self.NOW, runtime_attempt_id=self.ATTEMPT,
                             work_ref=self.live["work_ref"])
        manager.record_attempt(self.store, attempt_id=self.ATTEMPT,
                               adapter_name="acp",
                               adapter_digest=self.ADAPTER_DIGEST,
                               profile_digest=self.PROFILE,
                               input_digest=self.input_digest,
                               policy_digest=self.POLICY)
        manager.submit_claim(self.store, self.port, offer_id="offer-1")
        manager.activate_assignment(self.store, self.port,
                                    attempt_id=self.ATTEMPT,
                                    expect=self.live)
        for value in ("running", "quiescent"):
            manager.observe(self.store, attempt_id=self.ATTEMPT,
                            axis="execution_runtime", value=value)
        manager.observe(self.store, attempt_id=self.ATTEMPT,
                        axis="worker_disposition", value=disposition)
        return self.ATTEMPT

    def sealer(self):
        return Sealer(roots={"workspace": self.outputs},
                      declared={one["name"]: one for one in self.emitted()},
                      identity={"policy_digest": self.POLICY,
                                "profile_digest": self.PROFILE,
                                "adapter_digest": self.ADAPTER_DIGEST},
                      custody=self.custody, input_digest=self.input_digest)

    def committed(self, reported, *, claim=None):
        """Publish the envelope, then freeze and collect it for real."""
        import baton_v12.worker_manager as manager

        outputs = [dict(one) for one in reported["outputs"]]
        if claim is not None:
            for one in outputs:
                if one["name"] == "proposal":
                    one["result_metadata"] = claim
        self.worker.publish_completion(
            self.ASSIGNMENT, reported["disposition"],
            self.worker.answered(self.emitted(), outputs))
        attempt = self.admitted(reported["disposition"])
        adapter = self.sealer()
        frozen = manager.request_freeze(self.store, self.port, adapter,
                                        attempt_id=attempt,
                                        disposition=reported["disposition"])
        receipt = manager.request_intake(self.store, self.port, adapter,
                                         attempt_id=attempt)
        return frozen, receipt, adapter


class TheFreezeAndIntakeAreCommitted(CommittedReceiptCase):
    """A committed receipt, not a validated envelope."""

    def test_each_role_freezes_and_collects_its_own_half_for_real(self):
        for role in ("implementation", "review"):
            with self.subTest(role=role):
                self.setUp()
                reported = (self.implemented() if role == "implementation"
                            else self.reviewed())
                frozen, receipt, adapter = self.committed(reported)
                # THE PRODUCT'S OWN SEAL AND COLLECT RAN, once each.
                self.assertEqual(adapter.sealed, [self.ATTEMPT])
                self.assertEqual(adapter.collected, [self.ATTEMPT])
                self.assertEqual(receipt["custody"], "accepted")
                self.assertEqual(receipt["manifest_digest"],
                                 frozen["manifest_digest"])
                produced = ({"proposal"} if role == "implementation"
                            else {"findings", "logs"})
                self.assertEqual(
                    {one["name"] for one in frozen["outputs"]
                     if one["status"] == "present"}, produced)
                self.assertEqual(
                    {one["artifact_id"].split(":")[-1]
                     for one in receipt["artifacts"]}, produced)

    def test_the_committed_record_is_read_back_out_of_the_store(self):
        """Read from durable state, not from the call's return value."""
        from baton_v12.worker_manager import (frozen_output_of,
                                              intake_receipt_of, load_manifest)

        frozen, receipt, _adapter = self.committed(self.reviewed())
        back = frozen_output_of(self.store, self.ATTEMPT)
        self.assertEqual(back["manifest_digest"], frozen["manifest_digest"])
        self.assertEqual(back["disposition"], "completed")
        self.assertEqual(intake_receipt_of(self.store, self.ATTEMPT)
                         ["receipt_digest"], receipt["receipt_digest"])
        # AND THE RETAINED RESULT MANIFEST CARRIES THE MEASUREMENTS, so what
        # was committed describes the bytes the turn wrote.
        manifest = load_manifest(self.store, back["manifest_digest"],
                                 "resultManifest")
        content = {one["name"]: one["content_manifest"]
                   for one in manifest["outputs"]}
        self.assertIsNone(content["proposal"])
        for name in ("findings", "logs"):
            self.assertGreater(content[name]["entry_count"], 0)

    def test_the_custody_copy_holds_the_same_bytes_the_turn_wrote(self):
        """Custody is a copy of the real tree, walked and compared."""
        self.committed(self.reviewed())
        for name in ("findings", "logs"):
            written = os.path.join(self.outputs, name)
            held = os.path.join(self.custody, name)
            self.assertTrue(os.path.isdir(held), name)
            self.assertEqual(sorted(os.listdir(written)),
                             sorted(os.listdir(held)))
            for leaf in os.listdir(written):
                with open(os.path.join(written, leaf), "rb") as handle:
                    wrote = handle.read()
                with open(os.path.join(held, leaf), "rb") as handle:
                    self.assertEqual(handle.read(), wrote, leaf)


class TheVerdictReaderTakesTheCommittedResult(CommittedReceiptCase):
    """The stage-result reader, fed the store's own committed bindings."""

    def frozen_in_the_store(self, reported):
        from baton_v12.worker_manager import frozen_output_of

        self.committed(reported)
        return frozen_output_of(self.store, self.ATTEMPT)

    def test_a_committed_review_result_is_admitted_by_the_verdict_reader(self):
        from baton_v12.worker_manager import review_cycles

        taken = review_cycles._review_result(
            self.frozen_in_the_store(self.reviewed()))
        self.assertEqual(sorted(one["output_name"]
                                for one in taken["artifacts"]),
                         ["findings", "logs"])
        # THE ARTIFACTS ARE THE COMMITTED ONES: every locator points into the
        # custody this manager took, not into the worker's writable output.
        for one in taken["artifacts"]:
            self.assertTrue(one["locator"].startswith("file://"))
            self.assertIn(self.custody, one["locator"])

    def test_a_committed_result_without_both_halves_earns_no_verdict(self):
        """THE NEGATIVE, from a real committed result of this same Job.

        The implementation stage of this shared Job freezes a proposal and
        answers findings and logs absent -- so its committed result is exactly
        "a completed attempt of this Job with neither review half" and the
        verdict reader refuses it by name. That is the confusion one shared
        manifest could otherwise cause, refused at the reader that owns it.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import review_cycles

        with self.assertRaises(ContractRefusal) as caught:
            review_cycles._review_result(
                self.frozen_in_the_store(self.implemented()))
        self.assertIn("separately frozen findings and logs",
                      str(caught.exception))

    def test_either_half_alone_is_still_refused(self):
        """And one half is not most of a verdict."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import review_cycles

        committed = self.frozen_in_the_store(self.reviewed())
        for kept in ("findings", "logs"):
            with self.subTest(kept=kept):
                trimmed = dict(committed, artifacts=[
                    one for one in committed["artifacts"]
                    if one["output_name"] == kept])
                with self.assertRaises(ContractRefusal) as caught:
                    review_cycles._review_result(trimmed)
                self.assertIn("separately frozen findings and logs",
                              str(caught.exception))


class ThePublicationGateIsExecuted(CommittedReceiptCase):
    """`retain_proposal` itself, on committed results of this shared Job."""

    # THE WORKER'S OWN HALF, AND IT IS A FIXTURE -- named as one.
    #
    # `retain_proposal` ADOPTS the worker's claim: the base it built on, the
    # head it made and where its objects sit. These runs use the
    # version-control-free `generic` profile, which produces no head, so no
    # real turn here can author one. The claim below therefore stands in for
    # what a checkpoint-profile implementation turn would attach, and it is
    # carried the way a worker carries it -- in the completion envelope's
    # `result_metadata`, through the real freeze, into the committed result.
    # EVERY OTHER MEMBER of the retained manifest is read back from its
    # accepted producer, which is what makes this a real retention.
    #
    # `transport` names a path inside the declared output, and the reader
    # checks it against the MEASURED entry list -- so it is `change.patch`,
    # a file the adapter genuinely wrote, rather than a name chosen freely.
    BASE_OBJECT = "4" * 40
    HEAD_OBJECT = "5" * 40

    def claim(self):
        from baton_v12.integration import driver

        return {driver.CLAIM_NAMESPACE: {
            "base": self.BASE_OBJECT, "head": self.HEAD_OBJECT,
            "transport": "change.patch",
            "recap": "candidate: one focused change (1 changed path(s))"}}

    def test_a_committed_implementation_result_is_retained(self):
        """THE POSITIVE, with `retain_proposal` actually called."""
        from baton_v12.integration import driver
        from baton_v12.worker_manager import frozen_output_of, load_manifest

        frozen, _receipt, _adapter = self.committed(self.implemented(),
                                                    claim=self.claim())
        retained = driver.retain_proposal(self.store,
                                          Publisher(self.BASE_OBJECT),
                                          attempt_id=self.ATTEMPT)
        held = load_manifest(self.store, retained, "proposalManifest")
        # THE RETAINED MANIFEST IS BOUND TO THE COMMITTED RESULT, member by
        # member, rather than merely existing.
        self.assertEqual(held["result_id"], frozen["result_id"])
        self.assertEqual(held["result_manifest_digest"],
                         frozen["manifest_digest"])
        self.assertEqual(frozen_output_of(self.store,
                                          self.ATTEMPT)["manifest_digest"],
                         held["result_manifest_digest"])
        self.assertEqual(held["input_manifest_digest"], self.input_digest)
        # THE WORKER'S ADOPTED HALF, and the manager's own measured half.
        self.assertEqual(held["source_base"]["hex"], self.BASE_OBJECT)
        self.assertEqual(held["proposal_head"]["hex"], self.HEAD_OBJECT)
        self.assertEqual(held["proposal_artifact"]["artifact_id"],
                         f"{self.ATTEMPT}:proposal")
        self.assertIn(self.custody, held["proposal_artifact"]["locator"])
        # AND THE OUTPUT DIGEST IS THE MEASUREMENT OF THE BYTES THE ADAPTER
        # WROTE, carried from the committed result rather than recomputed here.
        measured = {one["name"]: one["content_manifest"]
                    for one in load_manifest(self.store,
                                             frozen["manifest_digest"],
                                             "resultManifest")["outputs"]}
        self.assertEqual(held["output_digest"],
                         measured["proposal"]["tree_digest"])

    def test_a_committed_result_with_no_proposal_is_refused_before_it(self):
        """THE NEGATIVE, and the refusal precedes any retention.

        The review stage of this shared Job commits a completed result whose
        proposal is absent -- the case a shared manifest makes possible. It is
        refused at publication, and NOTHING is retained: the store holds no
        proposal manifest afterwards, which is the part that makes "refused
        before publication" a fact rather than a reading of the message.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        self.committed(self.reviewed())
        with self.assertRaises(ContractRefusal) as caught:
            driver.retain_proposal(self.store, Publisher(self.BASE_OBJECT),
                                   attempt_id=self.ATTEMPT)
        self.assertIn("not present", str(caught.exception))
        self.assertEqual(self.proposal_manifests(), 0)

    def test_an_unable_implementation_never_reaches_the_output_check(self):
        """A turn that produced no candidate is stopped earlier still.

        Its disposition is `unable`, and publication refuses an attempt with
        no COMPLETED frozen result to propose -- before it looks at any
        output. This is the precondition the previous round named and did not
        execute; it is executed here.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.integration import driver

        self.committed(self.turn("implementation", writes={}),
                       claim=self.claim())
        with self.assertRaises(ContractRefusal) as caught:
            driver.retain_proposal(self.store, Publisher(self.BASE_OBJECT),
                                   attempt_id=self.ATTEMPT)
        self.assertIn("no completed frozen result", str(caught.exception))
        self.assertEqual(self.proposal_manifests(), 0)

    def proposal_manifests(self):
        return self.store._connection.execute(
            "SELECT COUNT(*) FROM manifests WHERE schema = ?",
            ("baton.worker-manifest/proposal",)).fetchone()[0]


CASES = (TheCorrectedDeclarationIsAcceptedByBothRoles,
         BothRolesProduceRealBytes,
         TheWorkerMeasuresWhatWasActuallyWritten,
         TheManagerTakesTheRealEnvelope,
         MissingHalvesAreRejectedDownstream,
         TheFreezeAndIntakeAreCommitted,
         TheVerdictReaderTakesTheCommittedResult,
         ThePublicationGateIsExecuted)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Named explicitly so the shared bases never run as cases of their own."""
    suite = unittest.TestSuite()
    for case in CASES:
        for name in loader.getTestCaseNames(case):
            suite.addTest(case(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
