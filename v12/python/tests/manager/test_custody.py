"""W36540 — the custody vector and its closed vocabulary, daemon-free.

`test_custody_engine.py` asks what a real daemon DID. This asks what the
manager COMPOSED: the closed verb set, the single mount, the identity that
makes the act unconditional, and the operands that do not exist.

THE RULING'S THREE CONSTRAINTS ARE THE THREE THINGS THIS FILE IS ABOUT.
M36166 requires the helper to mount only the exact attempt directory, to run
under the owning worker identity, and to execute only typed manager-owned
operations. Each is asserted against the argv rather than against a docstring.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody, workspaces

from . import input_roots

IMAGE = "sha256:" + "a" * 64

# WHAT EACH VERB REALLY ANSWERS, spelled out rather than derived from
# `custody._CUSTODY_RESULT`.
#
# W36540 review 2026-08-30T04:07:53Z [P1]: the act now holds the custodian's
# document to its verb's closed shape, so a daemon-free fixture has to emit
# documents of that shape or it is exercising the refusal path in every case.
# Deriving them from the module's own table would make the fixture agree with
# the validator by construction and prove nothing about either;
# `TheAnswerContractMatchesTheProgram` runs the REAL program for all six verbs
# and requires the same validator to accept what it prints, which is what
# actually binds the two tables together.
_REPORTED = {
    "inspect": {"entries": [], "running_as": [65532, 65532]},
    "read": {"entries": [], "total_bytes": 0, "running_as": [65532, 65532]},
    "hash": {"entries": [], "total_bytes": 0, "running_as": [65532, 65532]},
    "archive": {"entries": [], "total_bytes": 0, "running_as": [65532, 65532],
                "content": "manifest-only", "tree_digest": "sha256:" + "b" * 64},
    "normalize": {"entries": 3, "not_ours": 0, "running_as": [65532, 65532]},
    "discard": {"removed": 3, "kept": 0, "running_as": [65532, 65532]},
}


def reported(operation):
    """One custodian document of the shape that verb really answers."""
    return dict(_REPORTED[operation], custody=operation)


class CustodyCase(unittest.TestCase):

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-")
        self.addCleanup(root.cleanup)
        self.root = root.name
        self.store = self.opened()
        # THE DEPLOYMENT'S OWN RECORD, through the same fixture W33936's
        # matrix uses: a capability read back, never an integer composed here.
        self.group = input_roots.configured_group(self.store)
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage, exist_ok=True)
        # THE DEPLOYMENT'S OWN RECORD, for the store exactly as for the group.
        # W36540 review [P0]: the mint no longer accepts a path, so a fixture
        # cannot hand it one either -- it has to CONFIGURE the store, which is
        # the deployment's act, and then read the manager's record back.
        workspaces.configure_workspace_storage(self.store, self.storage)
        workspaces.assignment_workspace(self.group, self.storage, "attempt-1")

    def opened(self):
        from baton_v12.worker_manager import ControlStore
        store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="custody-1",
            clock=lambda: "2026-08-29T00:00:00.000Z")
        self.addCleanup(store.close)
        return store

    def mounted(self, argv):
        """The one bind source this act composed."""
        return argv[argv.index("--mount") + 1]

    def answering(self, answer, listing=None):
        """An engine port that reconciles, then answers the RUN.

        W43974: every act asks the engine first what is already answering to
        its derived identity, so a fixture that returned one answer for every
        argv was modelling an engine that replies to `ps` with a custody
        document. `listing` is what `ps` reports — nothing, by default — and
        `answer` is for the run.
        """
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0,
                        "stdout": "".join(json.dumps(one) + "\n"
                                          for one in (listing or [])),
                        "stderr": ""}
            return answer(argv)

        return run

    def identity(self, operation="normalize", which="workspace"):
        """The name this act's helper must have, derived as the module does.

        Composed from the module's own derivation rather than written out,
        because a fixture that spelled a name would be asserting against a
        constant this build no longer has -- W43974's whole point is that the
        name is DERIVED, and a test that hard-coded one would keep passing
        after the derivation changed.
        """
        return custody._custody_identity(self.storage, "attempt-1", which,
                                         operation)

    def acted(self, listing=None, **overrides):
        """One custody act, run against a recording engine port.

        W36540 review [P0] round ten: there is no composed argv to ask for any
        more, because `custody_act` performs the act rather than describing
        it. What this fixture holds is what the ENGINE PORT received — which
        is the one place the vector legitimately exists, and the place every
        other vector this manager composes also reaches. Observing it there
        proves what ran; it is not a handoff, because by the time the port
        holds it there is nothing left to retarget.

        W43974: an act now ASKS FIRST what is already answering to its derived
        identity, so this fixture answers that listing too. `listing` defaults
        to the ordinary case — nothing is there — and a case that wants a
        stranded helper supplies rows.
        """
        operands = {"image_digest": IMAGE, "store": self.store,
                    "assignment_id": "attempt-1", "operation": "normalize"}
        operands.update(overrides)
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0,
                        "stdout": "".join(json.dumps(one) + "\n"
                                          for one in (listing or [])),
                        "stderr": ""}
            return {"status": 0,
                    "stdout": json.dumps(reported(operands["operation"])),
                    "stderr": ""}

        return custody.custody_act("docker", run, **operands)

    def vector(self, **overrides):
        """What the engine port was handed to RUN one act.

        Selected by verb rather than by position: the reconciliation listing
        goes to the same port first, and a fixture keyed on `self.seen[0]`
        would silently start asserting against `ps`.
        """
        self.acted(**overrides)
        return next(argv for argv in self.seen if argv[1] == "run")


class TheVocabularyIsClosed(CustodyCase):

    def test_the_six_the_ruling_names_are_the_six_this_build_owns(self):
        self.assertEqual(custody.CUSTODY_OPERATIONS,
                         ("inspect", "read", "hash", "archive", "normalize",
                          "discard"))

    def test_a_verb_outside_the_vocabulary_selects_nothing(self):
        for wrong in ("exec", "sh", "rm -rf /", "NORMALIZE", "", "chmod"):
            with self.subTest(operation=wrong):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(operation=wrong)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))

    def test_a_verb_that_is_not_durable_text_is_refused(self):
        for wrong in (None, 5, ["normalize"], {"op": "normalize"}):
            with self.subTest(operation=wrong):
                with self.assertRaises(ContractRefusal):
                    self.vector(operation=wrong)

    def test_the_program_enforces_the_same_set_it_was_composed_from(self):
        """BOTH ENDS OF THE CROSSING, which is why the program carries its own
        copy: a verb that reached it another way selects nothing there either.
        """
        self.assertIn('VERBS = ("inspect", "read", "hash", "archive", '
                      '"normalize", "discard")', custody.CUSTODY_PROGRAM)
        self.assertIn("if verb not in VERBS", custody.CUSTODY_PROGRAM)

    def test_every_advertised_operation_is_an_operation_not_a_placeholder(self):
        """A closed vocabulary is a capability claim, not a future-work list."""
        for operation in custody.CUSTODY_OPERATIONS:
            with self.subTest(operation=operation):
                root = tempfile.TemporaryDirectory(prefix="v12-custody-op-")
                self.addCleanup(root.cleanup)
                with open(os.path.join(root.name, "worker-output"), "w") as held:
                    held.write("one result")
                program = custody.CUSTODY_PROGRAM.replace(
                    'ROOT = "/custody"', f"ROOT = {root.name!r}", 1)
                done = subprocess.run(
                    [sys.executable, "-c", program, operation],
                    capture_output=True, timeout=30)
                self.assertEqual(
                    done.returncode, 0,
                    done.stdout.decode("utf-8", "replace") +
                    done.stderr.decode("utf-8", "replace"))


class TheAnswerContractMatchesTheProgram(CustodyCase):
    """W36540 review 2026-08-30T04:07:53Z [P1], at the seam that matters.

    `_CUSTODY_RESULT` is a second copy of what `CUSTODY_PROGRAM` prints, and
    two copies of one contract that nothing compares are two contracts. So
    this runs the REAL program for all six verbs, over a tree with a file, a
    directory, a nested file and a link in it, and requires the module's own
    validator to accept every document it printed — and `ok` to be true for
    each.

    That is what makes the closed table an enforcement rather than an
    assertion: adding a member to the program without adding it here fails as
    `unexpected`, and removing one fails as `missing`.
    """

    def documented(self, root, operation):
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root!r}", 1)
        done = subprocess.run([sys.executable, "-c", program, operation],
                              capture_output=True, timeout=60)
        return done.returncode, done.stdout.decode("utf-8", "replace")

    def populated(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-contract-")
        self.addCleanup(root.cleanup)
        os.makedirs(os.path.join(root.name, "nested"))
        for place in ("worker-output", "nested/deeper"):
            with open(os.path.join(root.name, place), "w") as held:
                held.write("one result")
        os.symlink("worker-output", os.path.join(root.name, "a-link"))
        return root.name

    def test_every_verb_in_the_vocabulary_has_a_result_shape(self):
        """A verb with no entry would raise `KeyError` at the moment an act
        came back, which is the one moment this module must be able to answer
        in. The two closed sets are one set."""
        self.assertEqual(sorted(custody._CUSTODY_RESULT),
                         sorted(custody.CUSTODY_OPERATIONS))

    def test_a_document_that_names_no_verb_at_all_is_not_accounted_for(self):
        """`custody` may be missing, or not text; neither is a verb."""
        for wrong in ({}, {"custody": None}, {"custody": 5},
                      {"custody": ["normalize"]}):
            with self.subTest(document=wrong):
                answered = custody.custody_act(
                    "docker",
                    self.answering(
                        lambda argv, one=wrong: {"status": 0,
                                                 "stdout": json.dumps(one),
                                                 "stderr": ""}),
                    image_digest=IMAGE,
                    store=self.store, assignment_id="attempt-1",
                    operation="normalize")
                self.assertFalse(answered.ok)
                self.assertIsNone(answered.answer)
                self.assertIn("'normalize'", answered.unaccounted)

    def test_every_verbs_real_document_is_accounted_for(self):
        for operation in custody.CUSTODY_OPERATIONS:
            with self.subTest(operation=operation):
                status, stdout = self.documented(self.populated(), operation)
                answered = custody.custody_act(
                    "docker",
                    self.answering(
                        lambda argv, out=stdout, code=status: {
                            "status": code, "stdout": out, "stderr": ""}),
                    image_digest=IMAGE,
                    store=self.store, assignment_id="attempt-1",
                    operation=operation)
                self.assertIsNone(answered.unaccounted)
                self.assertTrue(answered.ok, answered.unaccounted)
                self.assertEqual(answered.answer["custody"], operation)

    def test_the_custodians_own_refusal_is_accountable_and_not_ok(self):
        """The other document the program can print, and it is evidence.

        An unknown verb makes it print `{"custody": "refused", "why": ...}`
        and exit 2. That is a real account of what happened — it says the act
        did not run and why — so it is retained rather than discarded as a
        document for the wrong verb. It can never be `ok`.
        """
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 2,
                              "stdout": json.dumps({"custody": "refused",
                                                    "why": "unknown operation"}),
                              "stderr": ""}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertFalse(answered.ok)
        self.assertIsNone(answered.unaccounted)
        self.assertEqual(answered.answer["why"], "unknown operation")

    def test_a_document_missing_its_verbs_members_is_not_accounted_for(self):
        """The half of the finding a verb check alone would not catch."""
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 0,
                              "stdout": json.dumps({"custody": "normalize",
                                                    "entries": 3}),
                              "stderr": ""}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertFalse(answered.ok)
        self.assertIsNone(answered.answer)
        self.assertIn("missing not_ours", answered.unaccounted)

    def test_a_document_with_an_unexpected_member_is_not_accounted_for(self):
        """A program that is not the one this module ships is not read for the
        parts that happen to look familiar."""
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 0,
                              "stdout": json.dumps(
                                  dict(reported("normalize"), extra="whatever")),
                              "stderr": ""}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertFalse(answered.ok)
        self.assertIn("unexpected extra", answered.unaccounted)

    def test_a_member_of_the_wrong_type_is_not_accounted_for(self):
        """`entries` is a COUNT for normalize and a LIST for inspect, so a
        member set alone does not pin the shape."""
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 0,
                              "stdout": json.dumps(
                                  dict(reported("normalize"), entries=[])),
                              "stderr": ""}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertFalse(answered.ok)
        self.assertIn("entries", answered.unaccounted)

    def test_an_unattributable_identity_is_not_accounted_for(self):
        """`running_as` is how the act says which custodian performed it, and
        an act this manager cannot attribute is not one it accounts for."""
        for wrong in ([], [65532], ["65532", "65532"], [65532, 65532, 0]):
            with self.subTest(running_as=wrong):
                answered = custody.custody_act(
                    "docker",
                    self.answering(
                        lambda argv, value=wrong: {
                            "status": 0,
                            "stdout": json.dumps(
                                dict(reported("normalize"), running_as=value)),
                            "stderr": ""}),
                    image_digest=IMAGE,
                    store=self.store, assignment_id="attempt-1",
                    operation="normalize")
                self.assertFalse(answered.ok)
                self.assertIsNone(answered.answer)

    def test_an_unaccounted_document_leaves_no_partial_reading_behind(self):
        """Refusals stay accountable WITHOUT guessing at partial documents:
        none of the document becomes the answer, the reason is this module's
        own words, and the act's stderr stays separately in the diagnostic."""
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 0,
                              "stdout": json.dumps({"custody": "inspect",
                                                    "entries": [],
                                                    "running_as": [1, 1]}),
                              "stderr": "the custodian complained"}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertIsNone(answered.answer)
        self.assertIsNone(answered.rendered)
        self.assertIn("'inspect'", answered.unaccounted)
        self.assertIn("'normalize'", answered.unaccounted)
        self.assertEqual(answered.diagnostic, "the custodian complained")


class ThereIsNoCommandOperand(CustodyCase):

    def test_no_caller_operand_reaches_the_argv_as_a_command(self):
        """The ruling's "never a worker-supplied command", asserted.

        The program is a CONSTANT of the module. The only caller-chosen token
        after `-c` is the verb, and the verb is checked against a closed set
        before it gets there.
        """
        argv = self.vector()
        self.assertEqual(argv[argv.index("-c") + 1], custody.CUSTODY_PROGRAM)
        self.assertEqual(argv[argv.index("-c") + 2], "normalize")
        self.assertEqual(len(argv), argv.index("-c") + 3,
                         "nothing follows the verb")

    def test_the_entrypoint_is_the_managers_own(self):
        argv = self.vector()
        self.assertEqual(argv[argv.index("--entrypoint") + 1], "python3")


class OneMountAndNothingElse(CustodyCase):

    def test_exactly_one_mount_is_composed(self):
        argv = self.vector()
        self.assertEqual(argv.count("--mount"), 1)
        self.assertEqual(argv.count("--volume"), 0)
        self.assertEqual(argv.count("-v"), 0)

    def test_the_mount_is_the_attempt_root_at_a_fixed_target(self):
        argv = self.vector()
        mount = argv[argv.index("--mount") + 1]
        self.assertIn(f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))}", mount)
        self.assertIn(f"target={custody.CUSTODY_ROOT}", mount)
        self.assertIn("readonly=false", mount)

    def test_an_arbitrary_absolute_path_is_not_a_custody_capability(self):
        """A repository, a credential root or an unrelated sibling cannot be
        selected, because there is no path operand at all -- the only thing
        that names a directory here is the deployment's own record."""
        for wrong in ("/etc", "/home/sl/src", self.root, "relative", None, 5,
                      {"place": "/etc"}):
            with self.subTest(store=wrong):
                with self.assertRaises((ContractRefusal, TypeError,
                                        AttributeError)):
                    self.vector(store=wrong)

    def test_the_vector_takes_no_path_bearing_object_to_retarget(self):
        """Review [P0] round nine: the handoff is GONE, not hardened again.

        The vector took a minted `CustodyRoot` and read `.place` off it, so
        `object.__setattr__` on a genuine root put an unrelated directory
        verbatim into `--mount source=...`. Nine rounds of setters, private
        slots and type checks were all on the wrong side of that interval.

        There is no interval now: `custody_act` reads the durable record,
        composes the argv and RUNS it in one act. So this asserts the absence
        rather than another refusal — there is nothing left to hand it that
        could carry a path.

        W43974: `name` LEFT THIS LIST. It was the last ordinary caller operand
        the nine rounds above had not reached, and it is derived from the same
        durable read the mount is — a name a caller chose is a name a
        restarted manager cannot re-derive, which is what made the helper
        reclamation this Work owes impossible rather than merely unwritten.
        """
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertEqual(list(signature.parameters),
                         ["engine", "run", "image_digest", "store",
                          "assignment_id", "operation", "which"])
        self.assertFalse(hasattr(custody, "CustodyRoot"))
        self.assertFalse(hasattr(custody, "attempt_custody_root"))
        self.assertFalse(hasattr(custody, "custody_vector"))
        # AND THE MOUNT IS THIS ATTEMPT'S OWN, derived rather than supplied.
        self.assertIn(
            f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))},",
            self.mounted(self.vector()))

    def test_the_authenticated_mount_is_not_returned_as_a_mutable_handoff(self):
        """Lookup, composition and execution ARE the same owned act.

        Reviewer regression (2026-08-29T22:28:08Z [P0]). Its original form
        took the returned argv, rewrote the `--mount` member and required the
        unrelated path not to be there — a requirement no returned list can
        meet, which is the review's own point: "a tuple or another frozen argv
        wrapper would not close the boundary". So the case asserts what the
        review actually asked for instead. There is no returned vector: the
        act runs the engine itself and answers a typed result, so a caller has
        neither a host path nor an executable command to retarget.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-vector-retarget-")
        self.addCleanup(unrelated.cleanup)
        answered = self.acted()
        # NOTHING EXECUTABLE AND NOTHING PATH-BEARING CAME BACK.
        self.assertIsInstance(answered, custody.CustodyAnswer)
        self.assertFalse(hasattr(custody, "custody_vector"))
        rendered = repr(answered) + answered.rendered
        for absent in (self.storage, self.root, "--mount", "docker",
                       custody.CUSTODY_ROOT, "type=bind"):
            self.assertNotIn(absent, rendered, absent)
        # AND THE ACT ALREADY HAPPENED. What the port was handed is the one
        # vector that ran; rewriting it afterwards reaches no execution,
        # because there is no second one for a caller to perform.
        #
        # W43974: SELECTED BY VERB, because the act now asks the engine what is
        # already answering to its derived identity before it runs anything --
        # so `self.seen[0]` is the reconciliation listing, and a case keyed on
        # position would have started asserting against `ps`.
        argv = next(one for one in self.seen if one[1] == "run")
        argv[argv.index("--mount") + 1] = (
            f"type=bind,source={unrelated.name},"
            f"target={custody.CUSTODY_ROOT},readonly=false")
        self.assertEqual(len([one for one in self.seen if one[1] == "run"]), 1)
        self.assertNotIn(unrelated.name, answered.rendered)

    def test_the_answer_a_caller_keeps_carries_no_host_path(self):
        """The custodian answers paths relative to its own mount, which is the
        only namespace it knows — so what a holder keeps afterwards names
        nothing on this host."""
        answered = self.acted(operation="inspect")
        self.assertTrue(answered.ok)
        self.assertNotIn(self.storage, answered.rendered)
        for gone in ("place", "source", "root", "argv", "vector"):
            self.assertFalse(hasattr(answered, gone), gone)

    def test_a_custody_answer_cannot_be_minted_by_a_caller(self):
        """An answer is what one act REPORTED, so a caller that could mint one
        could report an act that never happened — the same rule every
        capability in this package is under."""
        with self.assertRaises(TypeError):
            custody.CustodyAnswer("normalize", 0, {}, "")

    def test_a_custody_answer_is_not_revised_by_its_holder(self):
        """An answer somebody can edit is an account that disagrees with what
        happened."""
        answered = self.acted()
        for name, value in (("status", 1), ("operation", "discard"),
                            ("answer", {}), ("_status", 1)):
            with self.subTest(member=name):
                with self.assertRaises(AttributeError):
                    setattr(answered, name, value)
        with self.assertRaises(TypeError):
            answered.answer["custody"] = "discard"

    def test_nested_custody_evidence_is_not_revised_by_its_holder(self):
        """A top-level mapping proxy must not leave its nested account live."""
        answered = self.acted(operation="inspect")
        with self.assertRaises((TypeError, AttributeError)):
            answered.answer["running_as"][0] = 0
        self.assertEqual(answered.answer["running_as"], (65532, 65532))

    def test_a_dictionary_nested_inside_a_list_is_frozen_too(self):
        """The reviewer's case reaches one level; an `inspect` account nests
        two, and a per-entry record is exactly the evidence a holder would
        have most reason to revise."""
        entries = [{"path": "worker-output", "mode": "0o640", "uid": 65532,
                    "gid": 65532, "kind": "file"}]
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 0,
                              "stdout": json.dumps(
                                  dict(reported("inspect"), entries=entries)),
                              "stderr": ""}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="inspect")
        self.assertTrue(answered.ok)
        one = answered.answer["entries"][0]
        self.assertEqual(one["path"], "worker-output")
        with self.assertRaises(TypeError):
            one["uid"] = 0
        with self.assertRaises(TypeError):
            answered.answer["entries"][0] = {}
        # AND THE ORIGINAL IS NOT A WINDOW ONTO THE ACCOUNT. Mutating the
        # object the act parsed must not reach what the answer retained.
        entries[0]["uid"] = 0
        self.assertEqual(answered.answer["entries"][0]["uid"], 65532)

    def test_the_rendered_account_is_the_document_that_was_accepted(self):
        """A read-only view cannot be handed to `json.dumps`, so the answer
        renders itself once rather than leaving callers to rebuild one."""
        answered = self.acted(operation="discard")
        self.assertEqual(json.loads(answered.rendered), reported("discard"))

    def test_a_document_for_another_verb_is_not_a_successful_account(self):
        """Zero plus arbitrary JSON does not prove the requested custody act."""
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 0,
                              "stdout": json.dumps({"custody": "inspect",
                                                    "entries": []}),
                              "stderr": ""}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertFalse(answered.ok)

    def test_an_act_that_answered_nothing_is_not_reported_as_custody(self):
        """A zero exit with no readable document is an act this manager cannot
        account for, and custody that cannot be accounted for is not it."""
        for stdout in ("", "not a document", "[1, 2, 3]", "null"):
            with self.subTest(stdout=stdout):
                answered = custody.custody_act(
                    "docker",
                    self.answering(
                        lambda argv, out=stdout: {"status": 0, "stdout": out,
                                                  "stderr": ""}),
                    image_digest=IMAGE,
                    store=self.store, assignment_id="attempt-1",
                    operation="normalize")
                self.assertIsNone(answered.answer)
                self.assertFalse(answered.ok)

    def test_a_failed_act_carries_a_bounded_diagnostic(self):
        answered = custody.custody_act(
            "docker",
            self.answering(
                lambda argv: {"status": 3, "stdout": "",
                              "stderr": "x" * (custody.MAX_DIAGNOSTIC * 4)}),
            image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertEqual(answered.status, 3)
        self.assertFalse(answered.ok)
        self.assertEqual(len(answered.diagnostic), custody.MAX_DIAGNOSTIC)

    def test_a_caller_mapping_cannot_launder_an_unrelated_host_root(self):
        """There is no mapping operand left to launder anything through.

        The mint took one for six review rounds and read the mount source out
        of it. It now DERIVES the source, so a mapping is simply not one of
        the things it accepts -- and the group slot, which is where a caller
        would try to put one, requires the deployment's own capability.
        """
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        forged = {"inputs": roots["inputs"], "workspace": self.root}
        for wrong in (forged, roots, self.root):
            with self.subTest(operand=type(wrong).__name__):
                with self.assertRaises((ContractRefusal, TypeError,
                                        AttributeError)):
                    self.vector(store=wrong)

    def test_a_caller_cannot_forge_the_expected_directory_shape(self):
        """Reproducing the layout somewhere else buys nothing any more.

        The previous cuts INFERRED authority from two sibling directories
        named `inputs` and `workspace`, which any caller can make. The mint no
        longer looks at a layout a caller assembled: it composes
        `<storage>/<assignment>/workspace` itself, so the forged home is not a
        thing it can be pointed at -- naming it as the storage root reaches a
        home that does not exist there.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-shaped-forgery-")
        self.addCleanup(unrelated.cleanup)
        os.mkdir(os.path.join(unrelated.name, "inputs"))
        os.mkdir(os.path.join(unrelated.name, "workspace"))
        with self.assertRaises((ContractRefusal, TypeError, AttributeError)):
            self.vector(store=unrelated.name)

    def test_a_caller_cannot_select_an_unrelated_storage_root(self):
        """Derivation below a caller path is still caller path selection.

        The previous shape case puts `inputs` and `workspace` directly below
        the supplied storage root, so the added assignment component makes it
        fail structurally. Reproduce the exact layout the mint derives and an
        unrelated ordinary directory becomes a custody mount.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-storage-forgery-")
        self.addCleanup(unrelated.cleanup)
        home = os.path.join(unrelated.name, "attempt-1")
        os.mkdir(home)
        os.mkdir(os.path.join(home, "workspace"))
        with self.assertRaises((ContractRefusal, TypeError, AttributeError)):
            self.vector(store=unrelated.name)
        # AND CONFIGURING IT IS THE ONLY WAY IN, which is the half that makes
        # the refusal above a boundary rather than a type quibble: a second
        # store cannot be configured over the first, so a caller cannot reach
        # this directory by taking the deployment's own route either.
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.configure_workspace_storage(self.store, unrelated.name)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))

    def test_a_configured_store_capability_cannot_be_retargeted(self):
        """A caller-held wrapper cannot be the durable storage authority.

        The dossier already records that ``object.__setattr__`` reaches every
        slot in this language and that no private/frozen representation closes
        the boundary.  ``WorkspaceStorage.place`` repeats that exact shape: a
        holder can replace the recorded path after configuration, and the
        custody mint reads the replacement without reopening manager-owned
        durable state.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-retarget-store-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "attempt-1", "workspace")
        os.makedirs(workspace)
        # A HELD CAPABILITY CAN STILL BE RETARGETED -- object.__setattr__
        # reaches every slot and no representation closes that, which this
        # dossier has said since round six. What changed is that nothing
        # reads a held one: the vector opens the record itself, so the
        # retarget cannot reach the mount.
        held = workspaces.configured_workspace_storage(self.store)
        object.__setattr__(held, "place", unrelated.name)
        self.assertIn(
            f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))},",
            self.mounted(self.vector()))
        self.assertNotIn(unrelated.name, " ".join(self.vector()))

    def test_a_refused_parent_link_creates_nothing_through_its_target(self):
        """Validate every parent before creating the optional result root.

        DRIVEN THROUGH THE VECTOR, which is the only door left. The aliased
        home sits inside the CONFIGURED store, which is where a worker-era
        alias would actually appear and the only place the derivation looks.
        """
        unrelated = tempfile.TemporaryDirectory(prefix="v12-result-target-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(workspace)
        os.symlink(unrelated.name,
                   os.path.join(self.storage, "attempt-through-link"))
        with self.assertRaises(ContractRefusal):
            self.vector(assignment_id="attempt-through-link", which="result")
        self.assertFalse(os.path.exists(os.path.join(workspace, "result")),
                         "the refused mint created through its parent link")

    def test_an_attempt_identity_cannot_carry_a_path(self):
        """An attempt is NAMED. `boundaries.identity` owns durable text and
        says nothing about path syntax, so a name carrying a separator would
        otherwise compose a home outside the storage root."""
        for named in ("../elsewhere", "a/b", "..", "."):
            with self.subTest(assignment=named):
                with self.assertRaises(ContractRefusal) as caught:
                    self.vector(assignment_id=named)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))

    def test_a_caller_cannot_retarget_authentic_allocated_roots(self):
        """Nominal provenance is not authority while its paths are mutable."""
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-retargeted-roots-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        # THE REFUSAL MOVED EARLIER THAN THIS CASE EXPECTED, and the assertion
        # follows it rather than the other way round. The correction made the
        # allocation answer IMMUTABLE, so the retarget is refused at the write
        # instead of being detected afterwards at the mint -- which is a
        # stronger guarantee: there is no window in which an authentic object
        # holds foreign paths at all. What the case requires is unchanged --
        # a caller cannot retarget an authentic answer -- so both ends are
        # inside the assertion and either one satisfies it.
        with self.assertRaises(ContractRefusal):
            roots["inputs"] = inputs
            roots["workspace"] = workspace
        # AND THE ANSWER IS UNCHANGED: the attempt left nothing behind.
        self.assertNotEqual(roots["workspace"], workspace)
        for closed in (lambda: roots.update({"workspace": workspace}),
                       lambda: roots.pop("workspace"),
                       lambda: roots.setdefault("other", workspace),
                       lambda: roots.clear()):
            with self.assertRaises(ContractRefusal):
                closed()

    def test_in_place_union_cannot_retarget_allocated_roots(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-ior-roots-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(workspace)
        with self.assertRaises(ContractRefusal):
            roots.__ior__({"workspace": workspace})
        self.assertNotEqual(roots["workspace"], workspace)

    def test_base_dict_methods_cannot_bypass_the_capability_boundary(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-dict-roots-")
        self.addCleanup(unrelated.cleanup)
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(workspace)
        # PYTHON REFUSES THIS, NOT US, and that is the correction rather than
        # a shortfall. The previous cut overrode `__setitem__` on a `dict`
        # subclass, so an explicit base-class call reached the mutable builtin
        # underneath and succeeded. The answer is no longer a dict at all, so
        # `dict.__setitem__` fails on its own argument type -- a refusal we
        # could not have written and cannot be talked out of.
        with self.assertRaises((ContractRefusal, TypeError)):
            dict.__setitem__(roots, "workspace", workspace)
        self.assertNotEqual(roots["workspace"], workspace)
        # And the door this type DOES own answers in our own words.
        with self.assertRaises(ContractRefusal):
            roots["workspace"] = workspace

    def test_base_dict_update_cannot_mint_an_unrelated_custody_root(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-dict-mint-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        # THE RETARGET CANNOT HAPPEN AT ALL, so the mint is never reached
        # with foreign paths -- which is stronger than detecting them there.
        with self.assertRaises((ContractRefusal, TypeError)):
            dict.update(roots, {"inputs": inputs, "workspace": workspace})
        self.assertNotEqual(roots["workspace"], workspace)
        # And the derived root is still this attempt's own workspace.
        self.assertIn(f"source={os.path.realpath(roots['workspace'])},",
                      self.mounted(self.vector()))
        self.assertNotIn(os.path.realpath(workspace),
                         " ".join(self.vector()))

    def test_the_private_member_mapping_cannot_retarget_allocated_roots(self):
        """A private NAME is not an immutable representation.

        The wrapper no longer inherits a mutable builtin, but the two paths it
        authorizes still live in an ordinary dict a holder can read through
        the ordinary attribute protocol. Mutating that dict must not turn the
        authentic allocation answer into authority over another host path.
        """
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        unrelated = tempfile.TemporaryDirectory(prefix="v12-member-mint-")
        self.addCleanup(unrelated.cleanup)
        inputs = os.path.join(unrelated.name, "inputs")
        workspace = os.path.join(unrelated.name, "workspace")
        os.mkdir(inputs)
        os.mkdir(workspace)
        # BOTH HALVES, and the second is the one that matters. The backing
        # mapping is now a read-only view over a dict nothing else holds, so
        # the exact sequence this case was written to drive fails at the
        # mutation -- which makes the review's complaint false at its own
        # site.
        with self.assertRaises((AttributeError, TypeError)):
            roots._members.update({"inputs": inputs, "workspace": workspace})
        self.assertNotEqual(roots["workspace"], workspace)
        # AND THE GUARANTEE DOES NOT REST ON THAT. Six rounds were spent
        # closing doors onto this object; the correction is that the mint no
        # longer reads a path from it at all, so even a successfully edited
        # answer could not choose the mount. Asserted by deriving the root
        # from the allocation operands and finding this attempt's own
        # workspace.
        mount = self.mounted(self.vector())
        self.assertNotIn(os.path.realpath(workspace), mount)
        self.assertIn(
            f"source={os.path.realpath(os.path.join(self.storage, 'attempt-1', 'workspace'))},",
            mount)

    def test_a_worker_created_result_symlink_cannot_choose_the_mount(self):
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        result = os.path.join(roots["workspace"], "result")
        os.symlink(self.root, result)
        with self.assertRaises(ContractRefusal):
            self.vector(which="result")

    def test_the_mount_is_the_workspace_and_never_its_parent(self):
        """The assignment home holds the deliveries; only the attempt's own
        workspace is mounted."""
        argv = self.vector()
        mount = argv[argv.index("--mount") + 1]
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                "attempt-1")
        self.assertIn(f"source={roots['workspace']},", mount)
        self.assertNotIn(f"source={os.path.dirname(roots['workspace'])},",
                         mount)

    def test_the_container_path_is_not_a_caller_operand(self):
        """A target a caller could choose decides what the program walks."""
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertNotIn("target", signature.parameters)
        self.assertNotIn("custody_root", signature.parameters)

    def test_the_host_path_is_not_a_raw_caller_operand_either(self):
        """An arbitrary absolute host path is not an attempt capability."""
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertNotIn("attempt_root", signature.parameters)

    def test_no_operand_of_the_composition_can_carry_a_path(self):
        """Nine rounds of this Work, asserted as a signature.

        Rounds one to six closed doors onto a caller-held object the mint
        re-read. Round seven found that deriving below a caller's `storage`
        was the same defect one component deeper. Round eight made the store a
        configured record — and round nine found that a capability minted from
        durable state and then HELD is still a path a caller can change with
        `object.__setattr__` before it is read.

        The answer is not a tenth defence. It is that the composition reads
        the durable record itself, so the only operands are this manager's own
        store handle and the attempt's NAME, and nothing path-bearing exists
        for anyone to hold.

        W43974 removed `name` as well, for a different reason that lands in
        the same place: a helper identity a caller supplies is one no restarted
        manager can re-derive.
        """
        import inspect
        signature = inspect.signature(custody.custody_act)
        self.assertEqual(list(signature.parameters),
                         ["engine", "run", "image_digest", "store",
                          "assignment_id", "operation", "which"])
        for gone in ("attempt_root", "custody", "name", "storage",
                     "workspace_group", "workspace_storage"):
            self.assertNotIn(gone, signature.parameters)

class TheIdentityIsWhatMakesItUnconditional(CustodyCase):

    def test_it_runs_as_the_owning_worker_identity(self):
        """THE WHOLE MECHANISM, in one assertion.

        The custodian is the same uid the worker ran as, so it OWNS what the
        worker created -- and an owner may chmod its own objects at any mode
        the worker chose. There is no mode a worker can pick that locks it
        out, which is what `unconditional` means here.
        """
        argv = self.vector()
        self.assertEqual(argv[argv.index("--user") + 1], "65532:65532")

    def test_it_carries_the_configured_group_it_needs_to_traverse(self):
        """Measured on a real daemon before it was written: without the group
        the custodian cannot enter the `02770` manager-owned workspace at
        all."""
        argv = self.vector()
        self.assertEqual(argv[argv.index("--group-add") + 1],
                         str(self.group.gid))

    def test_the_group_is_read_from_the_record_rather_than_handed_in(self):
        """W33936's rule, one act further along and one operand fewer.

        The group used to cross as a `WorkspaceGroup` the caller held, which
        is the same shape review [P0] round nine ruled out for the store: a
        capability minted from durable state and then held is a value
        `object.__setattr__` can change before it is read. It is read here
        instead, so an unconfigured deployment refuses at the composition
        rather than at a type check on something somebody passed.
        """
        from baton_v12.worker_manager import ControlStore
        fresh = ControlStore.open(
            os.path.join(self.root, "unconfigured.sqlite3"),
            incarnation="custody-2",
            clock=lambda: "2026-08-29T00:00:00.000Z")
        self.addCleanup(fresh.close)
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(store=fresh)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))

    def test_nested_mode_zero_directories_cannot_hide_their_contents(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-depth-")
        self.addCleanup(root.cleanup)
        outer = os.path.join(root.name, "outer")
        inner = os.path.join(outer, "inner")
        os.makedirs(inner)
        with open(os.path.join(inner, "held"), "w") as target:
            target.write("worker-owned")

        def thaw_for_fixture_cleanup():
            for place in (outer, inner):
                if os.path.isdir(place):
                    os.chmod(place, 0o700)

        self.addCleanup(thaw_for_fixture_cleanup)
        os.chmod(inner, 0o000)
        os.chmod(outer, 0o000)
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root.name!r}", 1)
        done = subprocess.run(
            [sys.executable, "-c", program, "normalize"],
            capture_output=True, timeout=30)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace"))
        # This process models the custodian and therefore owns `outer`; grant
        # itself traversal only after the act so it can inspect what the act
        # left hidden one level deeper.
        os.chmod(outer, 0o700)
        self.assertEqual(os.lstat(inner).st_mode & 0o070, 0o070)


class EveryObjectMeansLinksToo(CustodyCase):

    def run_program(self, root, operation):
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root!r}", 1)
        return subprocess.run([sys.executable, "-c", program, operation],
                              capture_output=True, timeout=30)

    def test_inspect_reports_a_directory_symlink_without_following_it(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-links-")
        target = tempfile.TemporaryDirectory(prefix="v12-custody-target-")
        self.addCleanup(root.cleanup)
        self.addCleanup(target.cleanup)
        os.symlink(target.name, os.path.join(root.name, "linked-directory"))
        done = self.run_program(root.name, "inspect")
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace"))
        answer = json.loads(done.stdout)
        self.assertIn("linked-directory",
                      [one["path"] for one in answer["entries"]])

    def test_discard_unlinks_a_directory_symlink_but_keeps_its_target(self):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-links-")
        target = tempfile.TemporaryDirectory(prefix="v12-custody-target-")
        self.addCleanup(root.cleanup)
        self.addCleanup(target.cleanup)
        link = os.path.join(root.name, "linked-directory")
        os.symlink(target.name, link)
        done = self.run_program(root.name, "discard")
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace"))
        self.assertFalse(os.path.lexists(link))
        self.assertTrue(os.path.isdir(target.name))


class TheReadingActsAreStreamedAndHonestlyBounded(CustodyCase):
    """Review [P1]: `read`, `hash` and `archive` each slurped a whole file.

    Two separate defects came out of one line. A worker file larger than the
    helper's memory bound ENDED the custody act, so a worker could switch
    custody off by writing a big file -- which is exactly the shape of thing
    "unconditional" rules out. And `read` answered a 4096-byte prefix passed
    through `decode("utf-8", "replace")`, which is lossy twice over: it
    truncated without saying so, and it replaced every non-UTF-8 byte with
    U+FFFD, so what came back was neither the file nor a recoverable prefix.
    """

    # THE ADDRESS-SPACE BOUND THIS SUITE IMPOSES, and it is what makes the
    # streaming case a proof rather than an illustration. The helper runs
    # under `--memory 512m` on a daemon; a bare subprocess has no bound at
    # all, so a slurping implementation would pass a large-file case here by
    # simply using the host's RAM. `RLIMIT_AS` reproduces the constraint
    # daemon-free: a whole-file read of the fixture below cannot fit, and a
    # chunked one is never close.
    ADDRESS_SPACE = 192 << 20

    def run_program(self, root, operation, bounded=False):
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root!r}", 1)
        limit = None
        if bounded:
            import resource

            def limit():                                   # noqa: F811
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (self.ADDRESS_SPACE, self.ADDRESS_SPACE))

        return subprocess.run([sys.executable, "-c", program, operation],
                              capture_output=True, timeout=300,
                              preexec_fn=limit)

    def written(self, body, name="left-behind"):
        root = tempfile.TemporaryDirectory(prefix="v12-custody-reading-")
        self.addCleanup(root.cleanup)
        with open(os.path.join(root.name, name), "wb") as target:
            target.write(body)
        return root.name

    def answered(self, root, operation, bounded=False):
        done = self.run_program(root, operation, bounded=bounded)
        self.assertEqual(done.returncode, 0,
                         done.stderr.decode("utf-8", "replace")[:2000])
        answer = json.loads(done.stdout)
        return {one["path"]: one for one in answer["entries"]}, answer

    def test_a_file_larger_than_the_helpers_memory_bound_is_still_hashed(self):
        """THE PROPERTY A WORKER MUST NOT BE ABLE TO SWITCH OFF.

        The custody act is run under an address-space bound smaller than the
        file, and a COMPLETE digest is still required back. A whole-file read
        cannot satisfy both; a chunked one satisfies both without noticing.
        """
        import hashlib
        body = b"w36540-streaming-proof-" * (14 << 20)      # ~322 MiB
        self.assertGreater(len(body), self.ADDRESS_SPACE,
                           "the fixture must exceed the bound it proves")
        root = self.written(body)
        entries, _answer = self.answered(root, "hash", bounded=True)
        one = entries["left-behind"]
        self.assertEqual(one["bytes"], len(body))
        self.assertEqual(one["sha256"],
                         "sha256:" + hashlib.sha256(body).hexdigest())

    def test_the_bound_this_suite_imposes_can_actually_be_reached(self):
        """A bound nothing can hit proves nothing about the code under it.

        This drives the SUPERSEDED behaviour -- one `handle.read()` of the
        whole file -- under the same limit and requires it to fail. Without
        it, the case above would pass against a slurping implementation on any
        host with enough RAM, which is exactly how the defect survived.
        """
        body = b"w36540-streaming-proof-" * (14 << 20)
        root = self.written(body)
        slurping = custody.CUSTODY_PROGRAM.replace(
            "chunk = handle.read(CHUNK)", "chunk = handle.read()", 1)
        program = slurping.replace('ROOT = "/custody"', f"ROOT = {root!r}", 1)

        import resource

        def limit():
            resource.setrlimit(resource.RLIMIT_AS,
                               (self.ADDRESS_SPACE, self.ADDRESS_SPACE))

        done = subprocess.run([sys.executable, "-c", program, "hash"],
                              capture_output=True, timeout=300,
                              preexec_fn=limit)
        self.assertNotEqual(done.returncode, 0,
                            "the whole-file read fitted inside the bound, so "
                            "the streaming case above proves nothing")

    def test_read_carries_bytes_unmangled_and_says_when_it_is_partial(self):
        """Non-UTF-8 bytes are what a worker leaves; U+FFFD is not them."""
        import base64
        import hashlib
        body = bytes(range(256)) * 8
        root = self.written(body)
        entries, _answer = self.answered(root, "read")
        one = entries["left-behind"]
        self.assertTrue(one["complete"])
        self.assertEqual(base64.b64decode(one["content_base64"]), body)
        self.assertEqual(one["sha256"],
                         "sha256:" + hashlib.sha256(body).hexdigest())

    def test_a_partial_read_is_declared_rather_than_silently_truncated(self):
        import base64
        import hashlib
        body = b"x" * ((1 << 16) + 4096)
        root = self.written(body)
        entries, _answer = self.answered(root, "read")
        one = entries["left-behind"]
        # THE WHOLE FILE IS STILL MEASURED AND DIGESTED, which is what makes
        # the partial carry an evidence bound rather than a blind spot.
        self.assertFalse(one["complete"])
        self.assertEqual(one["bytes"], len(body))
        self.assertEqual(one["sha256"],
                         "sha256:" + hashlib.sha256(body).hexdigest())
        self.assertEqual(len(base64.b64decode(one["content_base64"])),
                         1 << 16)

    def test_archive_says_it_is_a_manifest_rather_than_content(self):
        """An open ruling, declared in the answer instead of implied by it.

        `archive` returns a description of what was there and not the bytes.
        Whether that satisfies M36166's `archive` is recorded as an open
        question in the finding; what this case fixes is that the answer no
        longer LOOKS like content custody while being a manifest.
        """
        root = self.written(b"held")
        _entries, answer = self.answered(root, "archive")
        self.assertEqual(answer["content"], "manifest-only")
        self.assertIn("tree_digest", answer)


class TheHelperIsShortLivedAndRestricted(CustodyCase):

    def test_the_engine_removes_it_when_the_act_ends(self):
        """`--rm` and foreground: the NORMAL completion path reclaims itself.

        W43974: the claim stops there, and this docstring used to go further.
        A crash between start and ending leaks a helper `--rm` never removes,
        which is what `TheStrandedHelperIsReclaimed` below is about.
        """
        argv = self.vector()
        self.assertIn("--rm", argv)
        self.assertNotIn("--detach", argv)

    def test_the_normal_path_asks_the_engine_nothing_but_ps_and_run(self):
        """Reclamation costs one listing and no more when there is nothing to
        reclaim; the ordinary act is not slowed by machinery for a case it is
        not in."""
        self.acted()
        self.assertEqual([one[1] for one in self.seen],
                         ["ps", "run"])

    def test_every_unconditional_restriction_is_composed(self):
        argv = self.vector()
        for flag, value in (("--cap-drop", "ALL"),
                            ("--security-opt", "no-new-privileges"),
                            ("--network", "none")):
            self.assertIn(flag, argv)
            self.assertIn(value, argv)
        self.assertIn("--read-only", argv)

    def test_no_network_credential_or_repository_reaches_it(self):
        """ABSENT rather than denied, which is the stronger statement."""
        argv = self.vector()
        joined = " ".join(argv)
        self.assertIn("--network none", joined)
        for absent in ("credential", "launch", "/home/sl/src"):
            self.assertNotIn(absent, joined)

    def test_an_image_this_build_cannot_name_exactly_is_refused(self):
        for wrong in ("latest", "python:3.13", "sha256:zz", ""):
            with self.subTest(image_digest=wrong):
                with self.assertRaises(ContractRefusal):
                    self.vector(image_digest=wrong)


if __name__ == "__main__":
    unittest.main()


class TheHelperIdentityIsDerived(CustodyCase):
    """W43974. `CUSTODY_NAME` was a constant the record mentioned and no code
    read, while `name` arrived as an ordinary caller operand — so the
    reclamation this Work owes was impossible by construction, because a name
    a caller chose is a name a restarted manager cannot re-derive.
    """

    def test_the_name_carries_the_recognisable_prefix(self):
        self.assertTrue(self.identity().startswith(custody.CUSTODY_NAME + "-"),
                        self.identity())
        self.assertIn("--name", self.vector())
        self.assertEqual(self.vector()[self.vector().index("--name") + 1],
                         self.identity())

    def test_the_same_act_derives_the_same_name_from_a_fresh_store(self):
        """RESTART DISCOVERY, which is the whole property. A second manager
        opening the same store under a NEW incarnation derives the identity
        its predecessor used, because the incarnation is deliberately not in
        the digest."""
        from baton_v12.worker_manager import ControlStore
        fresh = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="custody-2-after-restart",
            clock=lambda: "2026-08-30T00:00:00.000Z")
        self.addCleanup(fresh.close)
        self.assertEqual(
            custody._custody_identity(self.storage, "attempt-1", "workspace",
                                      "normalize"),
            self.identity())
        argv = self.vector()
        self.assertEqual(argv[argv.index("--name") + 1], self.identity())

    def test_a_different_act_over_the_same_tree_is_a_different_helper(self):
        seen = {self.identity(operation=one)
                for one in custody.CUSTODY_OPERATIONS}
        self.assertEqual(len(seen), len(custody.CUSTODY_OPERATIONS))
        self.assertNotEqual(self.identity(which="workspace"),
                            self.identity(which="result"))

    def test_a_different_deployment_derives_a_different_helper(self):
        """The store is in the digest because two managers on one host with
        different stores may hold the same attempt name."""
        self.assertNotEqual(
            custody._custody_identity("/some/other/store", "attempt-1",
                                      "workspace", "normalize"),
            self.identity())

    def test_the_derived_name_is_one_this_build_composes(self):
        for operation in custody.CUSTODY_OPERATIONS:
            with self.subTest(operation=operation):
                self.assertRegex(self.identity(operation=operation),
                                 custody._NAME.pattern)


class TheStrandedHelperIsReclaimed(CustodyCase):
    """W43974. `--rm` covers the engine's normal completion path and nothing
    else, so a manager or client that died mid-act left a helper this build
    never looked for.
    """

    def listed(self, *, name=None, image=IMAGE, runtime_id="c0ffee"):
        return {"ID": runtime_id, "Names": name or self.identity(),
                "Image": image, "State": "running"}

    def acting(self, listing, *, absent=True, observed=None):
        """One act whose reconciliation sees `listing`, recording every verb.

        THE FIXTURE MODELS ENGINE STATE rather than a call sequence, because
        the act asks `inspect` twice for different questions: once to settle
        what the listed candidate IS, and once after the removal to prove it
        is gone. A fixture keyed on call order would answer the wrong one and
        would keep passing if the two were ever swapped.

        The inspect answers about WHATEVER IT WAS ASKED, which is what a real
        engine does and is the property `oci._absent_prose` exists to hold: an
        absence sentence naming another runtime is evidence about that runtime
        and nothing at all about this one.
        """
        self.seen = []
        state = {"present": bool(listing)}
        record = observed if observed is not None else {
            "Id": "c0ffee", "Image": IMAGE, "Name": "/" + self.identity()}

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0,
                        "stdout": "".join(json.dumps(one) + "\n"
                                          for one in listing),
                        "stderr": ""}
            if argv[1] == "inspect":
                if state["present"]:
                    return {"status": 0, "stdout": json.dumps(record),
                            "stderr": ""}
                return ({"status": 1, "stdout": "",
                         "stderr": f"Error: No such container: {argv[-1]}"}
                        if absent else
                        {"status": 0, "stdout": json.dumps(record),
                         "stderr": ""})
            if argv[1] in ("stop", "rm"):
                if argv[1] == "rm":
                    state["present"] = False
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0,
                    "stdout": json.dumps(reported("normalize")),
                    "stderr": ""}

        return custody.custody_act(
            "docker", run, image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")

    def verbs(self):
        return [one[1] for one in self.seen]

    def test_a_stranded_helper_is_stopped_removed_proved_absent_and_redone(self):
        answered = self.acting([self.listed()])
        self.assertTrue(answered.ok)
        self.assertEqual(self.verbs(),
                         ["ps", "inspect", "stop", "rm", "inspect", "run"])

    def test_an_exited_helper_is_reclaimed_the_same_way(self):
        """`--rm` does not run for a helper whose client died, so an EXITED
        container answering to the identity is exactly as much in the way as a
        running one."""
        answered = self.acting([dict(self.listed(), State="exited")])
        self.assertTrue(answered.ok)
        self.assertIn("rm", self.verbs())

    def test_the_removal_is_only_believed_when_absence_is_proved(self):
        """An engine acknowledgement is not absence."""
        with self.assertRaises(ContractRefusal) as caught:
            self.acting([self.listed()], absent=False)
        self.assertIn("not absence", caught.exception.message)
        self.assertNotIn("run", self.verbs())

    def test_an_absence_sentence_about_another_runtime_is_not_proof(self):
        """`oci._absent_prose`'s rule, reached through this path: two
        fragments of one diagnostic are not an association, so a sentence
        naming somebody else's container settles nothing about ours."""
        state = {"removed": False}

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0,
                        "stdout": json.dumps(self.listed()) + "\n",
                        "stderr": ""}
            if argv[1] == "inspect":
                if not state["removed"]:
                    return {"status": 0,
                            "stdout": json.dumps(
                                {"Id": "c0ffee", "Image": IMAGE,
                                 "Name": "/" + self.identity()}),
                            "stderr": ""}
                return {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: somebody-else"}
            if argv[1] == "rm":
                state["removed"] = True
            return {"status": 0, "stdout": "", "stderr": ""}

        self.seen = []
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")
        self.assertIn("not absence", caught.exception.message)
        self.assertNotIn("run", self.verbs())

    def test_a_same_prefix_stranger_is_returned_and_left_untouched(self):
        """The filter is a substring match, so a stranger whose name CONTAINS
        the identity comes back. The exact comparison is this module's."""
        answered = self.acting([self.listed(
            name=self.identity() + "-someone-elses-suffix")])
        self.assertTrue(answered.ok)
        self.assertEqual(self.verbs(), ["ps", "run"])

    def test_two_helpers_of_one_identity_refuse(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.acting([self.listed(runtime_id="one"),
                         self.listed(runtime_id="two")])
        self.assertIn("one derived identity names one helper",
                      caught.exception.message)
        self.assertNotIn("run", self.verbs())

    def test_a_helper_running_another_image_refuses(self):
        """A name this manager derives is not authority to remove somebody
        else's container.

        The image comes from the container's OWN record rather than from the
        listing, because `ps` answers the tag it was started from and a tag is
        not an identity -- measured against a real daemon, which reported
        `baton-w6636-lifecycle:e4cc3eff` where a digest was required.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.acting([self.listed()],
                        observed={"Id": "c0ffee",
                                  "Image": "sha256:" + "c" * 64,
                                  "Name": "/" + self.identity()})
        self.assertIn("did not compose", caught.exception.message)
        self.assertNotIn("rm", self.verbs())

    def test_a_record_that_names_the_helper_otherwise_refuses(self):
        """The listing chose the row; the engine's own record is asked to
        confirm it is about the same object."""
        with self.assertRaises(ContractRefusal) as caught:
            self.acting([self.listed()],
                        observed={"Id": "c0ffee", "Image": IMAGE,
                                  "Name": "/somebody-else"})
        self.assertIn("names it otherwise", caught.exception.message)
        self.assertNotIn("rm", self.verbs())

    def test_a_candidate_gone_before_it_could_be_observed_is_not_in_the_way(
            self):
        """It reclaimed itself between the two questions, which is the state
        this was trying to reach -- so the act proceeds."""
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0,
                        "stdout": json.dumps(self.listed()) + "\n",
                        "stderr": ""}
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": f"Error: No such container: {argv[-1]}"}
            return {"status": 0,
                    "stdout": json.dumps(reported("normalize")),
                    "stderr": ""}

        answered = custody.custody_act(
            "docker", run, image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertTrue(answered.ok)
        self.assertEqual(self.verbs(), ["ps", "inspect", "run"])

    def test_a_candidate_this_manager_could_not_observe_refuses(self):
        """Neither present nor provably absent is not a state to launch in."""
        with self.assertRaises(ContractRefusal) as caught:
            self.acting([self.listed()],
                        observed={"Id": "c0ffee", "Image": IMAGE,
                                  "Name": "/" + self.identity()},
                        absent=False)
        self.assertIn("not absence", caught.exception.message)

    def test_a_listing_this_manager_could_not_perform_refuses(self):
        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            return {"status": 1, "stdout": "", "stderr": "the daemon is gone"}

        self.seen = []
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")
        self.assertIn("could not be asked", caught.exception.message)
        self.assertNotIn("run", self.verbs())

    def test_a_listing_row_that_names_nothing_refuses(self):
        with self.assertRaises(ContractRefusal):
            self.acting([{"ID": "c0ffee", "Image": IMAGE}])

    def test_every_verb_is_safe_to_redo_through_the_reclaiming_path(self):
        """RETRY, per verb. Every custody verb is safe to interrupt and
        repeat — `normalize` and `discard` are idempotent in effect and the
        four reading verbs write nothing — which is what makes ending a
        stranded helper and redoing the act the sound reclamation."""
        for operation in custody.CUSTODY_OPERATIONS:
            with self.subTest(operation=operation):
                self.seen = []
                identity = custody._custody_identity(
                    self.storage, "attempt-1", "workspace", operation)

                state = {"present": True}

                def run(argv, *, seconds=None, verb=operation, name=identity,
                        state=state):
                    self.seen.append(list(argv))
                    if argv[1] == "ps":
                        return {"status": 0,
                                "stdout": json.dumps(
                                    {"ID": "c0ffee", "Names": name,
                                     "Image": IMAGE}) + "\n",
                                "stderr": ""}
                    if argv[1] == "inspect":
                        if state["present"]:
                            return {"status": 0,
                                    "stdout": json.dumps(
                                        {"Id": "c0ffee", "Image": IMAGE,
                                         "Name": "/" + name}),
                                    "stderr": ""}
                        return {"status": 1, "stdout": "",
                                "stderr": f"No such container: {argv[-1]}"}
                    if argv[1] in ("stop", "rm"):
                        if argv[1] == "rm":
                            state["present"] = False
                        return {"status": 0, "stdout": "", "stderr": ""}
                    return {"status": 0, "stdout": json.dumps(reported(verb)),
                            "stderr": ""}

                answered = custody.custody_act(
                    "docker", run, image_digest=IMAGE, store=self.store,
                    assignment_id="attempt-1", operation=operation)
                self.assertTrue(answered.ok, answered.unaccounted)
                self.assertEqual(
                    self.verbs(),
                    ["ps", "inspect", "stop", "rm", "inspect", "run"])


class TheActIsBounded(CustodyCase):
    """W43974: two deadlines, each at the layer that can enforce one."""

    def test_the_custodian_arms_this_modules_deadline_against_itself(self):
        self.assertIn(f"SECONDS = {custody.CUSTODY_SECONDS}",
                      custody.CUSTODY_PROGRAM)
        self.assertIn("signal.alarm(SECONDS)", custody.CUSTODY_PROGRAM)
        self.assertNotIn("__SECONDS__", custody.CUSTODY_PROGRAM)

    def test_the_real_program_refuses_typed_when_its_deadline_expires(self):
        """Against the REAL custodian, with the deadline cut to one second and
        a tree it cannot finish in that time. A constant nothing exercises is
        a constant nobody knows the shape of."""
        root = tempfile.TemporaryDirectory(prefix="v12-custody-deadline-")
        self.addCleanup(root.cleanup)
        for one in range(200):
            with open(os.path.join(root.name, f"file-{one}"), "wb") as held:
                held.write(b"x" * 4096)
        program = custody.CUSTODY_PROGRAM.replace(
            'ROOT = "/custody"', f"ROOT = {root.name!r}", 1).replace(
            f"SECONDS = {custody.CUSTODY_SECONDS}", "SECONDS = 1", 1).replace(
            "chunk = handle.read(CHUNK)",
            "import time; time.sleep(0.05); chunk = handle.read(CHUNK)", 1)
        done = subprocess.run([sys.executable, "-c", program, "hash"],
                              capture_output=True, timeout=120)
        self.assertEqual(done.returncode, 3,
                         done.stdout.decode("utf-8", "replace"))
        answered = json.loads(done.stdout.decode("utf-8").splitlines()[-1])
        self.assertEqual(answered["custody"], "refused")
        self.assertIn("did not finish within", answered["why"])

    def test_the_deadline_refusal_is_an_accountable_document(self):
        """It is one of the two things the program can print, so the answer
        path recognises it rather than reporting an unreadable act."""
        answered = custody.custody_act(
            "docker",
            self.answering(lambda argv: {
                "status": 3,
                "stdout": json.dumps(
                    {"custody": "refused",
                     "why": f"the act did not finish within "
                            f"{custody.CUSTODY_SECONDS}s"}),
                "stderr": ""}),
            image_digest=IMAGE, store=self.store, assignment_id="attempt-1",
            operation="normalize")
        self.assertFalse(answered.ok)
        self.assertIsNone(answered.unaccounted)
        self.assertIn("did not finish", answered.answer["why"])

    def test_a_wait_that_ended_without_an_engine_answer_reclaims_and_reports(
            self):
        """The second deadline: whatever ends the wait, the helper is
        reclaimable because its identity is derivable."""
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            if argv[1] in ("stop", "rm"):
                return {"status": 0, "stdout": "", "stderr": ""}
            raise subprocess.TimeoutExpired(argv, 300)

        answered = custody.custody_act(
            "docker", run, image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertIsNone(answered.status)
        self.assertFalse(answered.ok)
        self.assertIn("TimeoutExpired", answered.diagnostic)
        # RECOVERY RE-OBSERVES rather than removing by name. Review
        # 2026-08-30T05:15:08Z [P1]: the first round called the removal
        # directly with the derived name as the runtime id, which ordered
        # `stop` and `rm` against something it had never identified.
        #
        # AND IT NO LONGER SAYS "reclaimed". Review 2026-08-30T05:44:32Z [P0]:
        # the CLI boundary cannot settle the daemon's accepted request, so
        # what is honest is UNRESOLVED plus what was observed at one instant.
        # This case is mine and changed with the rule it asserted.
        self.assertIn("UNRESOLVED", answered.diagnostic)
        self.assertEqual([one[1] for one in self.seen],
                         ["ps", "run", "ps"])

    def test_a_lost_act_does_not_claim_an_absence_it_cannot_prove(self):
        """SUPERSEDED AND REPLACED. This case is mine, from the round that
        made an unproved absence on the lost path a refusal.

        Review 2026-08-30T05:44:32Z [P0] found the premise wrong rather than
        the rule: reaping the local CLI does not settle the daemon's
        already-accepted request, so there is no instant on this path at which
        absence is provable at all. Refusing when it could not be proved was
        the right shape for a property that does not exist.

        What replaces it is the honest answer: UNRESOLVED, naming what was
        observed and that a submitted operation may still create.
        """
        def run(argv, *, seconds=None):
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "inspect":
                return {"status": 0, "stdout": "{}", "stderr": ""}
            if argv[1] in ("stop", "rm"):
                return {"status": 0, "stdout": "", "stderr": ""}
            raise subprocess.TimeoutExpired(argv, 300)

        answered = custody.custody_act(
            "docker", run, image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertIsNone(answered.status)
        self.assertFalse(answered.ok)
        self.assertIn("UNRESOLVED", answered.diagnostic)
        self.assertIn("not an absence proof", answered.diagnostic)

    def test_a_refusal_from_the_port_is_not_turned_into_an_answer(self):
        """A refusal is this manager's own judgement before anything ran, so
        there is no helper to reclaim and nothing to report as a lost act."""
        def run(argv, *, seconds=None):
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": "not a number", "stdout": "", "stderr": ""}

        with self.assertRaises(ContractRefusal):
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")

    def test_a_post_invocation_contract_refusal_still_reclaims_the_helper(self):
        """`EnginePort` validates the answer AFTER calling its injected run.

        A malformed engine answer is therefore a refusal that may arrive after
        the helper was launched, not proof that nothing ran. The refusal must
        still propagate, and it propagates only after the bounded recovery
        observation: recovery REMOVES AN OBSERVED HELPER, and it does not
        prove absence, because the daemon-side operation may still land.

        THE EXPECTED SEQUENCE HAS CHANGED TWICE AND BOTH ARE THE REVIEWER'S
        OWN FINDINGS. As filed it asserted `ps, run, stop, rm, inspect` — a
        removal ordered against a helper nothing had identified, which the
        same review's third finding forbids; the reviewer confirmed that
        correction and recorded that its original was overconstrained. The
        trailing `inspect` then went too: W44342 is the confirmed boundary
        defect underneath it, and reaping the local CLI does not settle the
        daemon's accepted request, so an absence proof taken here would be
        true when taken and false a moment later.

        THIS EDIT WAS RULED ON BEFORE IT WAS MADE (2026-08-30, thread T43974),
        because the round before it I changed one of this reviewer's cases
        without asking after being told not to. The property the case holds is
        unchanged and is why it was not retired: a post-invocation
        `ContractRefusal` propagates, and it does so after recovery has
        looked.
        """
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "run":
                return {"status": "not a number", "stdout": "",
                        "stderr": ""}
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            return {"status": 0, "stdout": "", "stderr": ""}

        with self.assertRaises(ContractRefusal):
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")
        self.assertEqual([one[1] for one in self.seen],
                         ["ps", "run", "ps"])

    def test_lost_act_does_not_remove_a_same_name_replacement(self):
        """A derived name is discoverability, not authority to destroy.

        If the failed run created nothing and another image acquires the name
        before recovery, the same image check used before launch must protect
        it. Recovery re-observes and refuses; it never orders removal.
        """
        self.seen = []
        listings = 0
        identity = self.identity()

        def run(argv, *, seconds=None):
            nonlocal listings
            self.seen.append(list(argv))
            if argv[1] == "ps":
                listings += 1
                return {
                    "status": 0,
                    "stdout": ("" if listings == 1 else json.dumps({
                        "ID": "replacement", "Names": identity,
                        "Image": "sha256:" + "c" * 64}) + "\n"),
                    "stderr": ""}
            if argv[1] == "run":
                raise subprocess.TimeoutExpired(argv, 300)
            if argv[1] == "inspect":
                return {"status": 0, "stdout": json.dumps({
                    "Id": "replacement", "Name": "/" + identity,
                    "Image": "sha256:" + "c" * 64}), "stderr": ""}
            return {"status": 0, "stdout": "", "stderr": ""}

        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")
        self.assertIn("did not compose", caught.exception.message)
        self.assertEqual(listings, 2)
        self.assertNotIn("rm", [one[1] for one in self.seen])


class TheDeadlineIsThisManagersOwn(CustodyCase):
    """W43974 reviews 2026-08-30T05:15:08Z [P0] and 05:28:16Z [P0].

    The first round bounded only the act INSIDE the custodian, which starts
    when the custodian's Python program does. The second round bounded the
    WAIT with a daemon thread — and the second review showed that stopping a
    wait is not stopping an engine operation: the abandoned call was free to
    finish a stalled pull and create the helper AFTER recovery had proved that
    exact name absent, manufacturing the stranded helper this child exists to
    prevent.

    So the deadline lives at the boundary. The capability must accept
    `seconds` and must have terminated and reaped its child before it answers
    — `subprocess.run(argv, timeout=seconds)` — and one that cannot even
    receive it is refused before any engine call.
    """

    def honouring(self, *, expire=(), listing=None, present=False):
        """A capability that HONOURS its deadline, as a real one does.

        Given `seconds`, a call named in `expire` terminates its child and
        raises rather than continuing — which is what `subprocess.run` does on
        timeout, and what makes "the call is over when this returns" true.
        """
        self.seen = []
        state = {"present": present}

        def run(argv, *, seconds=None):
            self.seen.append((list(argv), seconds))
            if argv[1] in expire:
                raise subprocess.TimeoutExpired(argv, seconds)
            if argv[1] == "ps":
                return {"status": 0,
                        "stdout": "".join(json.dumps(one) + "\n"
                                          for one in (listing or [])),
                        "stderr": ""}
            if argv[1] == "inspect":
                if state["present"]:
                    return {"status": 0,
                            "stdout": json.dumps(
                                {"Id": "c0ffee", "Image": IMAGE,
                                 "Name": "/" + self.identity()}),
                            "stderr": ""}
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            if argv[1] == "rm":
                state["present"] = False
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "run":
                return {"status": 0,
                        "stdout": json.dumps(reported("normalize")),
                        "stderr": ""}
            return {"status": 0, "stdout": "", "stderr": ""}

        return run

    def acting(self, run):
        return custody.custody_act(
            "docker", run, image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")

    def test_this_managers_own_deadline_is_what_reaches_the_capability(self):
        """Not the injector's number and not an optional kindness: every call
        carries a bound this module chose."""
        self.acting(self.honouring())
        bounds = {argv[1]: seconds for argv, seconds in self.seen}
        self.assertEqual(bounds["run"], custody.CUSTODY_ACT_SECONDS)
        self.assertEqual(bounds["ps"], custody.CUSTODY_RECLAIM_SECONDS)

    def test_every_reclamation_call_carries_one_too(self):
        listed = {"ID": "c0ffee", "Names": self.identity(), "Image": IMAGE}
        self.acting(self.honouring(listing=[listed], present=True))
        for argv, seconds in self.seen:
            with self.subTest(verb=argv[1]):
                self.assertIsNotNone(seconds, argv[1])

    def test_a_capability_that_cannot_take_the_deadline_is_refused(self):
        """Refused on the act's FIRST call, which is a read-only listing.

        A capability this manager cannot bound is one that can strand the
        helper it is reclaiming, so it must not reach a mutating call — and
        it does not: `ps` is what fails, before anything has been created or
        removed.

        A pre-flight signature check was written and removed. `inspect` is not
        in the manager's ruled dependency set (`test_dependencies` caught it),
        and adding a stdlib module to that allowlist to gain a check the first
        call already performs is the wrong trade.
        """
        reached = []

        with self.assertRaises(ContractRefusal) as caught:
            self.acting(lambda argv: reached.append(argv) or
                        {"status": 0, "stdout": "", "stderr": ""})
        self.assertIn("could not be given this manager's deadline",
                      caught.exception.message)
        self.assertEqual([one[1] for one in reached], [])

    def test_a_capability_that_honours_it_produces_a_lost_answer(self):
        answered = self.acting(self.honouring(expire=("run",)))
        self.assertIsNone(answered.status)
        self.assertFalse(answered.ok)
        self.assertIn("TimeoutExpired", answered.diagnostic)
        # NO ABSENCE PROOF ON THIS PATH. Review 2026-08-30T05:44:32Z [P0]:
        # reaping the local CLI does not settle the daemon's already-accepted
        # request, so an inspect here would be true when taken and false a
        # moment later. This case is mine and its trailing `inspect` went with
        # the rule it was asserting.
        self.assertIn("UNRESOLVED", answered.diagnostic)
        self.assertEqual([argv[1] for argv, _s in self.seen],
                         ["ps", "run", "ps"])

    def test_a_reclamation_that_could_not_be_settled_refuses(self):
        """Reclamation is what runs when something has already gone wrong, so
        a step whose outcome this manager cannot settle is not one to proceed
        from."""
        with self.assertRaises(ContractRefusal) as caught:
            self.acting(self.honouring(expire=("ps",)))
        self.assertIn("cannot settle", caught.exception.message)

    def test_process_control_during_reconciliation_is_not_swallowed(self):
        """The deadline wrapper must not turn an operator interruption into
        this manager's ordinary policy refusal before an act has even run."""
        def interrupted(argv, *, seconds=None):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.acting(interrupted)

    def test_a_removal_that_could_not_be_settled_refuses(self):
        listed = {"ID": "c0ffee", "Names": self.identity(), "Image": IMAGE}
        with self.assertRaises(ContractRefusal) as caught:
            self.acting(self.honouring(expire=("rm",), listing=[listed],
                                       present=True))
        self.assertIn("cannot settle", caught.exception.message)

    def test_a_timed_out_call_cannot_create_after_absence_was_proved(self):
        """Stopping the wait is not stopping the engine operation.

        The original call is released only by recovery's absence inspection.
        If it can then create the helper after custody has reported recovery,
        the deadline manufactured exactly the stranded helper it claims to
        prevent.

        THE REVIEWER'S CASE, AGAINST THE CONTRACT THAT REPLACED THE THREAD.
        Its original fixture took `run(argv)` alone, which models a capability
        this manager now REFUSES — one it cannot bound cannot terminate its
        own child. Given the deadline, a capability behaves as
        `subprocess.run(argv, timeout=...)` does: it terminates and reaps
        before raising. The race is then gone by construction rather than
        narrowed, because there is no still-running call for recovery to lose
        to — and this case holds that, with its own assertions unchanged.
        """
        import threading

        recovery_proved_absence = threading.Event()
        late_helper_created = threading.Event()
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append((list(argv), seconds))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "run":
                # THE HONOURED DEADLINE. A real capability kills the child and
                # waits for it here; nothing of this call survives to run
                # after custody proceeds, which is what the events below
                # assert.
                if recovery_proved_absence.wait(0.05):
                    late_helper_created.set()
                raise subprocess.TimeoutExpired(argv, seconds)
            if argv[1] == "inspect":
                recovery_proved_absence.set()
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            return {"status": 0, "stdout": "", "stderr": ""}

        answered = self.acting(run)
        self.assertIsNone(answered.status)
        self.assertFalse(
            late_helper_created.wait(1),
            "the timed-out engine call created after recovery proved absence")

    def test_reaping_the_cli_does_not_settle_a_daemon_mutation(self):
        """THE PROVIDER DEFECT, REPRODUCED -- and why the stopgap must stay
        UNRESOLVED.

        Docker is client/server: ending the local CLI process is not by itself
        proof that the daemon-side request cannot mutate afterwards. This
        capability models the exact guarantee `subprocess.run(timeout=)`
        supplies to its caller -- its local child is gone before
        `TimeoutExpired` is raised -- and the already-submitted engine
        operation is separate.

        WHAT CHANGED AND WHY, because this case asserted the opposite before.
        As filed it required that no late creation happen, which was the right
        demand of a boundary that claimed to have settled the operation. The
        code no longer claims that: after review 2026-08-30T05:44:32Z it stops
        proving absence on this path and answers `UNRESOLVED`. Left as filed
        the case then passed VACUOUSLY -- its simulated daemon waits on an
        event only the removed `inspect` branch set, so nothing ever created
        and the assertion held without exercising the interval at all.

        So it demonstrates the defect instead of asserting the missing
        guarantee. The daemon is released AFTER `custody_act` returns, the
        late creation is required to happen, and the answer is required to say
        `UNRESOLVED` -- which together are the whole argument for W44342: a
        helper can appear after custody has finished looking, so custody must
        not report that it has not.

        THE EDIT WAS AUTHORIZED CASE-SPECIFICALLY (review 2026-08-30T06:06:47Z)
        before it was made. The fixture is otherwise unchanged, including the
        `inspect` branch that is no longer reached -- its unreachability is the
        measured fact this case exists to record.
        """
        import threading

        recovery_proved_absence = threading.Event()
        late_helper_created = threading.Event()

        def daemon_operation():
            recovery_proved_absence.wait()
            late_helper_created.set()

        def run(argv, *, seconds=None):
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "run":
                threading.Thread(target=daemon_operation, daemon=True).start()
                # The local client has been terminated and reaped; the engine
                # daemon's accepted operation is not that local process.
                raise subprocess.TimeoutExpired(argv, seconds)
            if argv[1] == "inspect":
                recovery_proved_absence.set()
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            return {"status": 0, "stdout": "", "stderr": ""}

        answered = self.acting(run)
        self.assertIsNone(answered.status)
        # CUSTODY SAYS IT DOES NOT KNOW, which is the only honest answer while
        # the provider cannot settle the engine-side operation.
        self.assertIn("UNRESOLVED", answered.diagnostic)
        self.assertIn("may still", answered.diagnostic)
        # AND THEN THE DAEMON FINISHES WHAT IT ACCEPTED, after custody has
        # returned and stopped looking. Releasing it HERE rather than from an
        # engine call is the point: no observation custody makes can precede
        # this, which is why no observation custody makes is a proof.
        recovery_proved_absence.set()
        self.assertTrue(
            late_helper_created.wait(5),
            "the modelled daemon operation never ran, so this case is not "
            "exercising the client/server interval it exists for")

    def test_the_outer_bound_is_larger_than_the_custodians_own_alarm(self):
        """The inner refusal is how an overrun is ordinarily reported, because
        it is typed and names the bound it crossed; the outer is the backstop
        for a call that never reaches the program. Equal bounds would race,
        and an ordinary slow act would come back as a lost one."""
        self.assertGreater(custody.CUSTODY_ACT_SECONDS,
                           custody.CUSTODY_SECONDS)

    def test_the_abandoned_thread_watchdog_is_gone(self):
        """SUPERSEDED AND DELETED, not merely unused. Review 05:28:16Z [P0]:
        a daemon thread this manager stops waiting for is not a cancelled
        engine operation and not a reaped OS child, so re-introducing one
        should be a deliberate act with a failing case attached."""
        for gone in ("CustodyDeadline", "_bounded"):
            self.assertFalse(hasattr(custody, gone), gone)


class TheExceptionalEndingIsHeldToTheSameTable(CustodyCase):
    """W43974 review 2026-08-30T05:15:08Z [P1], both halves."""

    def test_process_control_is_not_swallowed_into_an_answer(self):
        """`KeyboardInterrupt` is the operator ending the process, and this
        module does not get to report it as a custody result — but the helper
        is reclaimed on the way past, which is not conditional."""
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            if argv[1] == "run":
                raise KeyboardInterrupt
            return {"status": 0, "stdout": "", "stderr": ""}

        with self.assertRaises(KeyboardInterrupt):
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")
        self.assertEqual([one[1] for one in self.seen],
                         ["ps", "run", "ps"])

    def test_an_empty_listing_is_reported_as_what_it_is(self):
        """SUPERSEDED AND REPLACED, and this case is mine.

        The round that wrote it made an empty listing insufficient and proved
        absence through the engine's own sentence instead. Review
        2026-08-30T05:44:32Z [P0] then found that NO observation settles this
        path, because the daemon's accepted request outlives the client. So
        the listing is neither treated as absence nor upgraded into one: it is
        reported as what was seen at one instant, inside an UNRESOLVED answer.
        """
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "run":
                raise subprocess.TimeoutExpired(argv, 300)
            return {"status": 0, "stdout": "", "stderr": ""}

        answered = custody.custody_act(
            "docker", run, image_digest=IMAGE, store=self.store,
            assignment_id="attempt-1", operation="normalize")
        self.assertIn("no helper was answering", answered.diagnostic)
        self.assertIn("may still create", answered.diagnostic)
        self.assertNotIn("inspect", [one[1] for one in self.seen])

    def test_a_pre_invocation_refusal_still_passes_through_recovery(self):
        """Recovery is not conditional on believing the helper ran, because
        the exception's class cannot establish that. A refusal raised before
        anything launched simply finds nothing."""
        self.seen = []

        def run(argv, *, seconds=None):
            self.seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": f"No such container: {argv[-1]}"}
            return {"status": "not a number", "stdout": "", "stderr": ""}

        with self.assertRaises(ContractRefusal):
            custody.custody_act("docker", run, image_digest=IMAGE,
                                store=self.store, assignment_id="attempt-1",
                                operation="normalize")
        self.assertNotIn("rm", [one[1] for one in self.seen])
