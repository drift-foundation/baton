"""W321776 — STAGE A and the closed durable vocabulary, case by case.

Against the accepted packet in `work/records/2026/09/
finding-v12-complete-verification-context/findings/finding-context-packet/`
(W321780, checkpoint `6348161e608187393e45454db63c192a93f6deb3`), whose
`VERIFICATION.md` names the obligations. The rows this file covers are the ones
decidable from the task and the sealed set alone; the view-preflight rows and
the 102 gate in two materialized views belong to the two materializers, which
are not delivered here and are named as outstanding in the dossier's PROGRESS.

THE PAIRING IS ASKED OF THE REAL PACKAGE. `pairing` is composed from
`baton_v12.source_profiles.checkout_plan`, so the profile/base cases below are
answered by the party that owns the vocabulary rather than by a second copy of
its rules living in a test.

AND THE CONTEXT USED THROUGHOUT IS THE PACKET'S OWN, not a convenient one: the
whole prepared repository at `candidate/`, the working directory at its Python
subtree, `import_roots` of `["src"]`, the sealed fixture OUTSIDE the candidate
at `sealed/...`, and the in-candidate fixture as a `candidate.pins` entry at the
one path `tests/manager/input_roots.py` can read it from. Its digest and size
are the packet's measured values.
"""

import ast
import copy
import pathlib
import subprocess
import sys
import tempfile
import unittest

from baton_v12 import verification_context as context_module
from baton_v12.source_profiles import checkout as source_profiles
from baton_v12.verification_context import (
    CONTEXT_SCHEMA, ContextRefusal, EVIDENCE_SCHEMA, FAILED, INVALID_LAYOUT,
    LEGACY_PROPOSAL, LEGACY_TASK_SCHEMA, MATERIALIZATION, MISSING_INPUT,
    MalformedOutcome, NOT_RUN, PASSED, PROPOSAL_SCHEMA, READY, REFUSED,
    START_FAILURE, STATIC_STAGE, TASK_SCHEMA, TIMED_OUT, VIEW_STAGE,
    check_outcome, generation, held, import_path, ready, refused,
    reported_command, verdict)

# The packet's one declared immutable input, measured there.
VECTORS = ("sha256:fcc19dbdf021246c61d516987e5672c93053ab57a2e151af6bb66b6e"
           "6c6a9903")
VECTOR_BYTES = 19351
VECTOR_NAME = "worker-control-api-manifest-vectors"
PIN_PATH = ("work/records/2026/08/finding-v12-isolated-agent-workers/findings/"
            "finding-v12-worker-contract/findings/"
            "finding-worker-control-api-manifests/evidence/vectors.json")
BASE = "bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c"

# The literal argv the acceptance obligation names, abbreviated to its first
# two vectors here: this file tests the CONTRACT around the argv, and the gate
# itself runs in a materialized view.
ARGV = ["python3", "-m", "unittest", "tests.tools.test_user_credentials"]


def pairing(profile, declared):
    """`checkout_plan`'s own rule, asked rather than restated."""
    return source_profiles.checkout_plan(
        "/input/source", "/output", profile=profile, declared=declared)


def sealed():
    return {VECTOR_NAME: {"content_digest": VECTORS, "bytes": VECTOR_BYTES}}


def pinned():
    return {PIN_PATH: VECTORS}


def task(**replaced):
    document = {
        "schema": TASK_SCHEMA,
        "task_id": "w321776-paired-context",
        "instructions": "author the paired correction",
        "source_root": "/output",
        "source_profile": source_profiles.GIT_LINE_PROFILE,
        "declared_base": BASE,
        "verification": list(ARGV),
        "verification_context": {
            "working_directory": "candidate/v12/python",
            "candidate_destination": "candidate",
            "candidate": {
                "profile": source_profiles.GIT_LINE_PROFILE,
                "declared_base": BASE,
                "pins": [{"path": PIN_PATH, "content_digest": VECTORS}],
            },
            "import_roots": ["src"],
            "required_paths": ["src", "tests", "tests/tools", "tests/manager"],
            "inputs": [{
                "name": VECTOR_NAME,
                "destination": f"sealed/{VECTOR_NAME}/vectors.json",
                "content_digest": VECTORS,
                "bytes": VECTOR_BYTES,
            }],
        },
    }
    document.update(replaced)
    return document


def with_context(**replaced):
    """One task whose `verification_context` members are replaced."""
    document = task()
    document["verification_context"].update(replaced)
    return document


def with_candidate(**replaced):
    document = task()
    document["verification_context"]["candidate"].update(replaced)
    return document


def with_input(**replaced):
    document = task()
    document["verification_context"]["inputs"][0].update(replaced)
    return document


class StageAAcceptsThePacketsOwnContext(unittest.TestCase):

    def test_the_declared_context_is_held(self):
        self.assertEqual(held(task(), sealed=sealed(), pinned=pinned(),
                              pairing=pairing),
                         ready())

    def test_a_ready_context_names_no_cause_and_no_stage(self):
        answer = held(task(), sealed=sealed(), pinned=pinned(),
                      pairing=pairing)
        self.assertEqual(answer["schema"], CONTEXT_SCHEMA)
        self.assertEqual(answer["outcome"], READY)
        self.assertIsNone(answer["cause"])
        self.assertIsNone(answer["stage"])
        self.assertIsNone(answer["detail"])

    def test_the_working_directory_may_lie_inside_the_candidate(self):
        """VER-2's overlap is about a sealed INPUT and the candidate.

        The command runs in the candidate's own Python subtree, so a rule that
        refused this would refuse the packet's own layout.
        """
        inner = task()["verification_context"]
        self.assertTrue(inner["working_directory"].startswith(
            inner["candidate_destination"] + "/"))
        self.assertEqual(held(task(), sealed=sealed(), pinned=pinned(),
                              pairing=pairing), ready())

    def test_the_derived_import_path_is_the_roots_joined_and_nothing_else(self):
        """September reached `PYTHONPATH=src` with a hand-set variable."""
        self.assertEqual(
            import_path(task()["verification_context"]),
            ["candidate/v12/python/src"])

    def test_the_argv_carries_no_environment_assignment(self):
        """The imports derive from `import_roots`, so an argv that carried the
        same fact would be a second, disagreeing source of it."""
        for one in task()["verification"]:
            self.assertNotIn("PYTHONPATH", one)

    def test_stage_a_materializes_nothing(self):
        """Structural rather than observational: this module cannot.

        A case that merely watched one directory would prove nothing about the
        paths a module might have written elsewhere, so the sweep is over the
        module's own imports and names: `re` only, and no filesystem verb.
        """
        source = pathlib.Path(context_module.__file__).read_text(
            encoding="utf-8")
        tree = ast.parse(source, context_module.__file__)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(one.name for one in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        self.assertEqual(imported, {"re"})
        for banned in ("open", "mkdir", "makedirs", "rmtree", "copy", "copy2",
                       "copytree", "remove", "unlink", "write_text",
                       "write_bytes", "Popen", "run", "system"):
            with self.subTest(verb=banned):
                self.assertNotIn(banned, _called(tree))

    def test_the_sweep_is_not_vacuous(self):
        """The same sweep, over a module that does call one of them."""
        tree = ast.parse("import os\nos.makedirs('x')\n", "<planted>")
        self.assertIn("makedirs", _called(tree))


def _called(tree):
    answer = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                answer.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                answer.add(node.func.attr)
    return answer


class TheGenerationsRefuseInTheRightDirection(unittest.TestCase):
    """VER-1: an older holder REFUSES the new member rather than ignoring it."""

    def test_a_three_context_offered_under_two_is_refused(self):
        legacy = task(schema=LEGACY_TASK_SCHEMA)
        with self.assertRaises(ContextRefusal) as refusal:
            generation(legacy)
        self.assertEqual(refusal.exception.cause, INVALID_LAYOUT)
        self.assertEqual(refusal.exception.detail, "verification_context")
        self.assertEqual(refusal.exception.stage, STATIC_STAGE)

    def test_a_two_task_without_the_member_is_its_own_generation(self):
        legacy = task(schema=LEGACY_TASK_SCHEMA)
        del legacy["verification_context"]
        self.assertEqual(generation(legacy), LEGACY_TASK_SCHEMA)

    def test_a_three_task_with_the_context_absent_is_refused(self):
        document = task()
        del document["verification_context"]
        with self.assertRaises(ContextRefusal) as refusal:
            generation(document)
        self.assertEqual(refusal.exception.detail, "verification_context")

    def test_stage_a_refuses_a_two_task_outright(self):
        legacy = task(schema=LEGACY_TASK_SCHEMA)
        del legacy["verification_context"]
        with self.assertRaises(ContextRefusal) as refusal:
            held(legacy, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertEqual(refusal.exception.detail, "schema")

    def test_another_generation_entirely_is_refused(self):
        with self.assertRaises(ContextRefusal) as refusal:
            generation(task(schema="baton.dogfood-task/4"))
        self.assertEqual(refusal.exception.detail, "schema")


class StageARefusesEveryDeclarationFault(unittest.TestCase):
    """Each row of the packet's Stage-A table, with its closed cause."""

    def refusal(self, document, *, seal=None, pin=None):
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed() if seal is None else seal,
                 pinned=pinned() if pin is None else pin, pairing=pairing)
        self.assertEqual(caught.exception.stage, STATIC_STAGE)
        return caught.exception

    def test_an_absolute_path_member(self):
        answer = self.refusal(with_context(working_directory="/etc/shadow"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)
        self.assertEqual(answer.detail,
                         "verification_context.working_directory")

    def test_a_home_relative_path_member(self):
        answer = self.refusal(with_context(working_directory="~/candidate"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_a_traversing_segment(self):
        answer = self.refusal(
            with_context(working_directory="candidate/../../etc"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_an_empty_segment(self):
        answer = self.refusal(
            with_context(working_directory="candidate//v12/python"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_a_single_dot_segment(self):
        answer = self.refusal(
            with_context(working_directory="candidate/./v12"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_a_traversing_import_root(self):
        answer = self.refusal(with_context(import_roots=["src", "../src"]))
        self.assertEqual(answer.detail,
                         "verification_context.import_roots[1]")

    def test_an_absolute_required_path(self):
        answer = self.refusal(with_context(required_paths=["/src"]))
        self.assertEqual(answer.detail,
                         "verification_context.required_paths[0]")

    def test_a_duplicate_input_destination(self):
        document = task()
        one = document["verification_context"]["inputs"][0]
        twin = dict(one, name="second-vectors")
        document["verification_context"]["inputs"].append(twin)
        answer = self.refusal(document, seal={
            VECTOR_NAME: {"content_digest": VECTORS, "bytes": VECTOR_BYTES},
            "second-vectors": {"content_digest": VECTORS,
                               "bytes": VECTOR_BYTES}})
        self.assertEqual(answer.cause, INVALID_LAYOUT)
        self.assertEqual(answer.detail,
                         "verification_context.inputs[1].destination")

    def test_a_duplicate_input_name(self):
        document = task()
        one = document["verification_context"]["inputs"][0]
        document["verification_context"]["inputs"].append(
            dict(one, destination="sealed/second/vectors.json"))
        answer = self.refusal(document)
        self.assertEqual(answer.detail, "verification_context.inputs[1].name")

    def test_an_input_destination_inside_the_candidate(self):
        """VER-2: a sealed input under the candidate is indistinguishable from
        candidate bytes, and verification could then add fixtures to the
        proposal."""
        answer = self.refusal(
            with_input(destination="candidate/sealed/vectors.json"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)
        self.assertEqual(answer.detail,
                         "verification_context.inputs[0].destination")

    def test_the_candidate_inside_an_input_destination(self):
        """The same confusion with the names swapped."""
        document = task()
        inner = document["verification_context"]
        inner["candidate_destination"] = "sealed/candidate"
        inner["working_directory"] = "sealed/candidate/v12/python"
        inner["inputs"][0]["destination"] = "sealed"
        answer = self.refusal(document)
        self.assertEqual(answer.cause, INVALID_LAYOUT)
        self.assertEqual(answer.detail,
                         "verification_context.inputs[0].destination")

    def test_a_sibling_name_sharing_a_prefix_is_not_an_overlap(self):
        """`candidate` is not a prefix match for `candidate-sealed`."""
        document = with_input(destination="candidate-sealed/vectors.json")
        self.assertEqual(held(document, sealed=sealed(), pinned=pinned(),
                              pairing=pairing), ready())

    def test_a_malformed_input_digest(self):
        answer = self.refusal(with_input(content_digest="sha1:deadbeef"))
        self.assertEqual(answer.cause, INVALID_LAYOUT)
        self.assertEqual(answer.detail,
                         "verification_context.inputs[0].content_digest")

    def test_an_uppercase_digest_is_not_canonical(self):
        answer = self.refusal(with_input(content_digest=VECTORS.upper()))
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_negative_bytes(self):
        answer = self.refusal(with_input(bytes=-1))
        self.assertEqual(answer.detail, "verification_context.inputs[0].bytes")

    def test_a_boolean_is_not_a_byte_count(self):
        answer = self.refusal(with_input(bytes=True))
        self.assertEqual(answer.detail, "verification_context.inputs[0].bytes")

    def test_an_empty_verification(self):
        answer = self.refusal(task(verification=[]))
        self.assertEqual(answer.detail, "verification")

    def test_a_verification_that_is_not_a_list(self):
        answer = self.refusal(task(verification="python3 -m unittest"))
        self.assertEqual(answer.detail, "verification")

    def test_a_verification_element_that_is_not_text(self):
        answer = self.refusal(task(verification=["python3", 3]))
        self.assertEqual(answer.detail, "verification[1]")

    def test_an_empty_verification_element(self):
        answer = self.refusal(task(verification=["python3", ""]))
        self.assertEqual(answer.detail, "verification[1]")

    def test_an_unknown_context_member(self):
        """Version agreement means both holders accept the SAME document."""
        answer = self.refusal(with_context(view_root="candidate"))
        self.assertEqual(answer.detail, "verification_context.view_root")

    def test_a_missing_context_member(self):
        document = task()
        del document["verification_context"]["required_paths"]
        answer = self.refusal(document)
        self.assertEqual(answer.detail,
                         "verification_context.required_paths")

    def test_a_missing_candidate_member(self):
        document = task()
        del document["verification_context"]["candidate"]["declared_base"]
        answer = self.refusal(document)
        self.assertEqual(answer.detail,
                         "verification_context.candidate.declared_base")


class ASealedTaskCannotCarryAnObservation(unittest.TestCase):
    """A useful authoring turn cannot know its own edits before it runs."""

    def refuses(self, document, detail):
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertEqual(caught.exception.cause, INVALID_LAYOUT)
        self.assertEqual(caught.exception.detail, detail)

    def test_an_entry_head_in_the_context(self):
        self.refuses(with_context(entry_head="a" * 40),
                     "verification_context.entry_head")

    def test_a_tree_digest_in_the_context(self):
        self.refuses(with_context(tree_digest=VECTORS),
                     "verification_context.tree_digest")

    def test_changed_paths_in_the_candidate(self):
        self.refuses(with_candidate(changed_paths=["src/a.py"]),
                     "verification_context.candidate.changed_paths")

    def test_removed_in_the_candidate(self):
        self.refuses(with_candidate(removed=["src/a.py"]),
                     "verification_context.candidate.removed")

    def test_a_collection_disclosure_in_the_candidate(self):
        self.refuses(with_candidate(collection={"ignored": []}),
                     "verification_context.candidate.collection")

    def test_the_observation_members_are_named_here_once(self):
        self.assertEqual(
            context_module.OBSERVATION_MEMBERS,
            ("entry_head", "tree_digest", "changed", "changed_paths",
             "removed", "collection"))


class TheProfilePairingIsAskedOfThePackage(unittest.TestCase):
    """`checkout_plan`'s rules, not a second copy of them."""

    def refuses(self, document):
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertEqual(caught.exception.cause, INVALID_LAYOUT)
        self.assertEqual(
            caught.exception.detail,
            "verification_context.candidate.profile+declared_base")
        return caught.exception

    def test_a_profile_outside_the_packages_vocabulary(self):
        self.refuses(with_candidate(profile="worktree"))

    def test_a_generic_profile_carrying_a_base(self):
        """"would deliver the generic boundary while its author believed a
        verification had happened"."""
        self.refuses(with_candidate(profile=source_profiles.GENERIC_PROFILE,
                                    declared_base=BASE))

    def test_a_git_profile_without_a_base(self):
        self.refuses(with_candidate(profile=source_profiles.GIT_PROFILE,
                                   declared_base=None))

    def test_a_git_line_profile_without_a_base(self):
        self.refuses(with_candidate(
            profile=source_profiles.GIT_LINE_PROFILE, declared_base=None))

    def test_a_generic_profile_without_a_base_is_held(self):
        """The three profiles are unchanged, and none is removed."""
        document = task(source_profile=source_profiles.GENERIC_PROFILE,
                        declared_base=None)
        document["verification_context"]["candidate"].update(
            profile=source_profiles.GENERIC_PROFILE, declared_base=None)
        self.assertEqual(held(document, sealed=sealed(), pinned=pinned(),
                              pairing=pairing), ready())

    def test_the_two_places_the_task_names_the_profile_must_agree(self):
        """A holder reading the task would check out one revision while a
        holder reading the context verified another."""
        document = task(source_profile=source_profiles.GIT_PROFILE)
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertEqual(caught.exception.detail,
                         "verification_context.candidate.profile")

    def test_the_two_places_the_task_names_the_base_must_agree(self):
        document = task(declared_base="a" * 40)
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertEqual(caught.exception.detail,
                         "verification_context.candidate.declared_base")

    def test_the_refusal_carries_none_of_the_packages_prose(self):
        answer = self.refuses(with_candidate(profile="worktree"))
        self.assertNotIn("worktree", answer.detail)
        self.assertNotIn("profile is", answer.detail)


class ThePinsAreDecidedAgainstTheSeal(unittest.TestCase):
    """A pin is decidable at sealing; nothing about it awaits the provider."""

    def refusal(self, document, *, pin=None):
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed(),
                 pinned=pinned() if pin is None else pin, pairing=pairing)
        return caught.exception

    def test_a_pin_absent_from_the_seal_is_missing_input(self):
        answer = self.refusal(task(), pin={})
        self.assertEqual(answer.cause, MISSING_INPUT)
        self.assertEqual(answer.detail,
                         "verification_context.candidate.pins[0].path")

    def test_a_pin_the_seal_holds_at_other_bytes_is_missing_input(self):
        answer = self.refusal(task(), pin={PIN_PATH: "sha256:" + "0" * 64})
        self.assertEqual(answer.cause, MISSING_INPUT)
        self.assertEqual(
            answer.detail,
            "verification_context.candidate.pins[0].content_digest")

    def test_a_duplicate_pin_path(self):
        document = task()
        pins = document["verification_context"]["candidate"]["pins"]
        pins.append({"path": PIN_PATH, "content_digest": VECTORS})
        answer = self.refusal(document)
        self.assertEqual(answer.cause, INVALID_LAYOUT)
        self.assertEqual(answer.detail,
                         "verification_context.candidate.pins[1].path")

    def test_an_absolute_pin_path(self):
        document = task()
        document["verification_context"]["candidate"]["pins"][0]["path"] = (
            "/etc/shadow")
        answer = self.refusal(document)
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_a_malformed_pin_digest(self):
        document = task()
        document["verification_context"]["candidate"]["pins"][0][
            "content_digest"] = "deadbeef"
        answer = self.refusal(document)
        self.assertEqual(answer.cause, INVALID_LAYOUT)

    def test_the_pin_and_the_seal_hold_one_fact(self):
        """Two independent holders of the same digest, as the packet says."""
        document = task()
        pin = document["verification_context"]["candidate"]["pins"][0]
        declared = document["verification_context"]["inputs"][0]
        self.assertEqual(pin["content_digest"], declared["content_digest"])


class TheInputsAreDecidedAgainstTheSeal(unittest.TestCase):

    def refusal(self, document, *, seal):
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=seal, pinned=pinned(), pairing=pairing)
        return caught.exception

    def test_a_declared_input_absent_from_the_seal(self):
        answer = self.refusal(task(), seal={})
        self.assertEqual(answer.cause, MISSING_INPUT)
        self.assertEqual(answer.detail, "verification_context.inputs[0].name")

    def test_a_declared_input_digest_mismatched_in_the_seal(self):
        answer = self.refusal(task(), seal={
            VECTOR_NAME: {"content_digest": "sha256:" + "1" * 64,
                          "bytes": VECTOR_BYTES}})
        self.assertEqual(answer.cause, MISSING_INPUT)
        self.assertEqual(answer.detail,
                         "verification_context.inputs[0].content_digest")

    def test_a_declared_input_size_mismatched_in_the_seal(self):
        answer = self.refusal(task(), seal={
            VECTOR_NAME: {"content_digest": VECTORS, "bytes": 1}})
        self.assertEqual(answer.cause, MISSING_INPUT)
        self.assertEqual(answer.detail, "verification_context.inputs[0].bytes")


class ARefusalNamesAMemberAndNeverAValue(unittest.TestCase):
    """`detail` is a bounded structural fact: no host path, no secret."""

    HOSTILE = "/home/sl/.baton/credential-sources.json"

    def test_an_absolute_path_is_not_echoed(self):
        with self.assertRaises(ContextRefusal) as caught:
            held(with_context(working_directory=self.HOSTILE),
                 sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertNotIn(self.HOSTILE, caught.exception.detail)
        self.assertNotIn("credential", caught.exception.detail)
        self.assertNotIn(self.HOSTILE, str(caught.exception))

    def test_a_digest_is_not_echoed(self):
        with self.assertRaises(ContextRefusal) as caught:
            held(with_input(content_digest="sha256:" + "b" * 63),
                 sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertNotIn("b" * 63, caught.exception.detail)

    def test_an_unknown_member_whose_name_is_hostile_is_not_echoed(self):
        document = task()
        document["verification_context"][self.HOSTILE] = "x"
        with self.assertRaises(ContextRefusal) as caught:
            held(document, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertNotIn(self.HOSTILE, caught.exception.detail)
        self.assertEqual(caught.exception.detail, "verification_context")

    def test_every_refusal_document_is_closed(self):
        answer = refused(MISSING_INPUT, "verification_context.inputs[0].name",
                         stage=STATIC_STAGE)
        self.assertEqual(set(answer),
                         {"schema", "outcome", "stage", "cause", "detail"})
        self.assertEqual(answer["schema"], CONTEXT_SCHEMA)
        self.assertEqual(answer["outcome"], REFUSED)

    def test_a_refusal_outside_the_four_causes_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            refused("because", "verification_context", stage=STATIC_STAGE)

    def test_a_refusal_outside_the_two_stages_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            refused(MISSING_INPUT, "verification_context", stage="halfway")

    def test_a_refusal_without_a_member_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            refused(MISSING_INPUT, "", stage=VIEW_STAGE)

    def test_the_exception_publishes_through_the_closed_vocabulary(self):
        answer = ContextRefusal(MATERIALIZATION, "inputs[0]",
                                stage=VIEW_STAGE).document()
        self.assertEqual(answer, refused(MATERIALIZATION, "inputs[0]",
                                         stage=VIEW_STAGE))


class OnlyTheFiveCombinationsAreLegal(unittest.TestCase):
    """`CONTEXT-CONTRACTS.md`'s closed table, row by row."""

    def refused_context(self, cause=MISSING_INPUT, stage=VIEW_STAGE):
        return refused(cause, "verification_context.inputs[0].name",
                       stage=stage)

    def test_ready_passed_zero_is_a_pass_verdict(self):
        self.assertEqual(verdict(ready(), PASSED, 0), PASSED)

    def test_ready_failed_nonzero_is_a_fail_verdict(self):
        self.assertEqual(verdict(ready(), FAILED, 1), FAILED)

    def test_ready_timed_out_supplies_no_verdict(self):
        self.assertIsNone(verdict(ready(), TIMED_OUT, None))

    def test_ready_not_run_supplies_no_verdict(self):
        self.assertIsNone(verdict(ready(), NOT_RUN, None))

    def test_refused_not_run_supplies_no_verdict(self):
        self.assertIsNone(verdict(self.refused_context(), NOT_RUN, None))

    def test_each_of_the_four_causes_is_reachable(self):
        for cause in (MISSING_INPUT, INVALID_LAYOUT, MATERIALIZATION,
                      START_FAILURE):
            with self.subTest(cause=cause):
                self.assertIsNone(
                    verdict(self.refused_context(cause), NOT_RUN, None))

    def test_passed_with_a_null_status_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), PASSED, None)

    def test_passed_with_a_nonzero_status_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), PASSED, 1)

    def test_failed_with_zero_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), FAILED, 0)

    def test_failed_with_a_null_status_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), FAILED, None)

    def test_a_boolean_status_is_not_an_exit_code(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), FAILED, True)

    def test_a_refusal_carrying_a_verdict_is_malformed(self):
        for command in (PASSED, FAILED, TIMED_OUT):
            with self.subTest(command=command):
                with self.assertRaises(MalformedOutcome):
                    check_outcome(self.refused_context(), command, None)

    def test_not_run_carrying_a_status_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), NOT_RUN, 0)

    def test_timed_out_carrying_a_status_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), TIMED_OUT, 137)

    def test_an_unknown_command_word_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(ready(), "crashed", None)

    def test_a_ready_context_carrying_a_cause_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(dict(ready(), cause=MISSING_INPUT), NOT_RUN, None)

    def test_a_refusal_without_a_stage_is_malformed(self):
        broken = dict(self.refused_context(), stage=None)
        with self.assertRaises(MalformedOutcome):
            check_outcome(broken, NOT_RUN, None)

    def test_a_context_that_is_neither_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(dict(ready(), outcome="maybe"), NOT_RUN, None)

    def test_a_result_without_a_context_document_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            check_outcome(None, PASSED, 0)
        with self.assertRaises(MalformedOutcome):
            check_outcome({"outcome": READY}, PASSED, 0)


class LegacyResultsAreNotReinterpreted(unittest.TestCase):
    """Absence is "this version could not say", never `not-run`."""

    def test_a_two_result_says_nothing_about_its_command(self):
        self.assertIsNone(reported_command({"schema": LEGACY_PROPOSAL}))

    def test_a_two_result_carrying_three_members_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            reported_command({"schema": LEGACY_PROPOSAL, "command": NOT_RUN})

    def test_a_three_proposal_reports_its_own_command(self):
        self.assertEqual(
            reported_command({"schema": PROPOSAL_SCHEMA, "context": ready(),
                              "command": PASSED, "exit_status": 0}),
            PASSED)

    def test_the_operator_evidence_reports_the_same_way(self):
        self.assertEqual(
            reported_command({"schema": EVIDENCE_SCHEMA, "context": ready(),
                              "command": FAILED, "exit_status": 2}),
            FAILED)

    def test_an_unknown_generation_says_nothing_rather_than_passing(self):
        with self.assertRaises(MalformedOutcome):
            reported_command({"schema": "baton.dogfood-proposal/9"})

    def test_a_three_proposal_with_an_illegal_combination_is_malformed(self):
        with self.assertRaises(MalformedOutcome):
            reported_command({"schema": PROPOSAL_SCHEMA, "context": ready(),
                              "command": PASSED, "exit_status": None})


class TheModuleStaysImportableByTheWorker(unittest.TestCase):
    """It travels to the image under its own name, like `source_profiles`.

    A worker that could import the manager is a worker one bug away from
    holding the manager's capabilities, so the separation is held in both
    directions by a sweep rather than by a docstring.
    """

    def test_the_contract_imports_nothing_from_the_distribution(self):
        source = pathlib.Path(context_module.__file__).read_text(
            encoding="utf-8")
        tree = ast.parse(source, context_module.__file__)
        for node in ast.walk(tree):
            named = []
            if isinstance(node, ast.Import):
                named = [one.name for one in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                named = [node.module or ""]
            elif isinstance(node, ast.ImportFrom):
                named = ["baton_v12 (relative)"]
            for one in named:
                with self.subTest(module=one):
                    self.assertNotIn("baton_v12", one)

    def test_it_imports_cleanly_with_no_distribution_on_the_path(self):
        """The worker has no `baton_v12`; the module must still load there."""
        place = pathlib.Path(context_module.__file__).resolve()
        with tempfile.TemporaryDirectory() as root:
            (pathlib.Path(root) / place.name).write_bytes(place.read_bytes())
            answer = subprocess.run(
                [sys.executable, "-c",
                 "import verification_context as v;"
                 "assert v.TASK_SCHEMA.endswith('/3')"],
                cwd=root, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": root},
                capture_output=True, text=True, timeout=30)
        self.assertEqual((answer.returncode, answer.stderr), (0, ""))

    def test_the_worker_image_recipe_carries_it(self):
        recipe = (pathlib.Path(context_module.__file__).resolve()
                  .parents[3] / "worker" / "Dockerfile.claude")
        self.assertIn("verification_context.py",
                      recipe.read_text(encoding="utf-8"))



class TheDeclaredContextIsNotMutatedByBeingRead(unittest.TestCase):
    """Stage A answers a question; it does not normalize the caller's task."""

    def test_the_task_is_unchanged(self):
        document = task()
        before = copy.deepcopy(document)
        held(document, sealed=sealed(), pinned=pinned(), pairing=pairing)
        self.assertEqual(document, before)

    def test_the_sealed_maps_are_unchanged(self):
        seal, pin = sealed(), pinned()
        before = (copy.deepcopy(seal), copy.deepcopy(pin))
        held(task(), sealed=seal, pinned=pin, pairing=pairing)
        self.assertEqual((seal, pin), before)


if __name__ == "__main__":
    unittest.main()
