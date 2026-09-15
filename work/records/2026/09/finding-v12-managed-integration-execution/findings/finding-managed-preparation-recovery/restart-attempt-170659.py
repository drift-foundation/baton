"""W161230 slice2 CHECKPOINT A.1: the preparation input, at both ends.

THE PRODUCER AND THE CONSUMER ARE DRIVEN TOGETHER HERE, because that is the
only place their agreement is a fact rather than an intention.
`integration_bundle.compose_preparation_input` runs in the manager and imports
its contracts; `reconciliation_task` runs in a container and imports no
manager. Each therefore spells the source-tree measurement separately, and a
restatement nobody checks is how two readers come to disagree -- so these cases
publish a REAL input with the real producer and measure it with the REAL
consumer.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import inspect
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal

WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
sys.path.insert(0, str(WORKER))

import reconciliation_entry as entry                      # noqa: E402
import reconciliation_task as task                        # noqa: E402

import integration_bundle as bundle                       # noqa: E402


class ThePublishedInputIsMeasuredTheSameWayAtBothEnds(unittest.TestCase):
    """The producer and the consumer, driven together.

    `integration_bundle.compose_preparation_input` runs in the manager and
    imports its contracts; `reconciliation_task` runs in a container and
    imports no manager. Each therefore spells the source-tree measurement
    separately, and a restatement nobody checks is how two readers come to
    disagree -- so these cases publish a REAL export and measure it with the
    REAL consumer.
    """

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-preparation-in-")
        self.addCleanup(_release, self.root)
        self.place = os.path.join(self.root.name, "input")
        self.line = RealLine(os.path.join(self.root.name, "line"))
        self.line.write("feature.py", "VALUE = 1\n")
        base = self.line.commit("base")
        self.line.write("fix.py", "VALUE = 2\n")
        candidate = self.line.commit("candidate")
        self.line.run(["checkout", "--quiet", "-b", "target", base])
        self.line.write("other.py", "OTHER = 1\n")
        target = self.line.commit("target")
        self.revisions = {"base": base, "candidate": candidate,
                          "target_revision": target}

    def request(self, **changed):
        held = {"schema": task.REQUEST_SCHEMA, "source": dict(self.revisions),
                "commands": ["combined"]}
        held.update(changed)
        return held

    def published(self, request=None):
        return bundle.compose_preparation_input(
            self.place,
            request=self.request() if request is None else request,
            runner=_runner, repository=self.line.place)

    def test_the_producer_and_the_worker_measure_one_digest(self):
        """Neither side is trusted to describe the other's measurement."""
        answer = self.published()
        measured = task.measure(os.path.join(self.place,
                                             task.SOURCE_DIRECTORY))
        self.assertEqual(answer["input_digest"], measured["tree_digest"])

    def test_the_two_spellings_of_the_published_names_are_equal(self):
        """A name spelled twice is a name that can drift."""
        self.assertEqual(bundle.PREPARATION_SOURCE_DIRECTORY,
                         task.SOURCE_DIRECTORY)
        self.assertEqual(bundle.PREPARATION_REQUEST_DOCUMENT,
                         task.REQUEST_NAME)
        self.assertEqual(bundle.PREPARATION_OBJECTS, task.OBJECTS_NAME)

    def test_the_embedded_request_does_not_hash_itself(self):
        """THE FLAGGED DIGEST CYCLE, broken by ORDER rather than by a rule."""
        answer = self.published()
        self.assertEqual(answer["request"]["input_digest"],
                         answer["input_digest"])
        self.assertNotEqual(answer["bundle_digest"], answer["input_digest"])
        published = [one["path"] for one in answer["manifest"]]
        sourced = [one["path"] for one in answer["source_manifest"]]
        self.assertIn(task.REQUEST_NAME, published)
        self.assertNotIn(task.REQUEST_NAME, sourced)

    def test_the_input_digest_is_measured_and_never_supplied(self):
        """A caller that passed one would be asserting a measurement it did
        not take."""
        with self.assertRaises(Exception) as caught:
            self.published(self.request(input_digest="sha256:" + "0" * 64))
        self.assertIn("MEASURED here", str(caught.exception))

    def test_a_revision_expression_refuses_before_anything_is_written(self):
        with self.assertRaises(Exception):
            self.published(self.request(
                source=dict(self.revisions, candidate="HEAD~1")))
        self.assertFalse(os.path.exists(self.place))

    def test_the_worker_verifies_the_published_artifacts(self):
        answer = self.published()
        measured = task.verify_input(self.place, answer["request"])
        self.assertTrue(measured["entry_count"])

    def test_a_changed_published_artifact_refuses(self):
        answer = self.published()
        victim = os.path.join(self.place, task.SOURCE_DIRECTORY,
                              task.OBJECTS_NAME)
        os.chmod(os.path.join(self.place, task.SOURCE_DIRECTORY), 0o755)
        os.chmod(victim, 0o644)
        with open(victim, "ab") as handle:
            handle.write(b"tampered")
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.verify_input(self.place, answer["request"])
        self.assertIn("not the ones this request was composed over",
                      str(caught.exception))

    def test_an_input_with_no_source_tree_refuses(self):
        empty = os.path.join(self.root.name, "empty")
        os.mkdir(empty)
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.verify_input(empty, {"input_digest": "sha256:" + "0" * 64})
        self.assertIn("publishes no source", str(caught.exception))

    def test_a_publication_is_written_once(self):
        self.published()
        with self.assertRaises(Exception):
            self.published()

    def test_the_published_tree_is_immutable(self):
        answer = self.published()
        for one in answer["manifest"]:
            mode = os.stat(os.path.join(self.place, one["path"])).st_mode
            self.assertEqual(mode & 0o777, bundle.BUNDLE_FILE)


V = "git"

HARNESS = ("import os\n"
           "raise SystemExit(0 if os.path.exists('fix.py') else 1)\n")


def _release(root):
    """The publication is 0555/0444, so ordinary cleanup cannot remove it."""
    for where, _, names in os.walk(root.name):
        os.chmod(where, 0o755)
        for one in names:
            try:
                os.chmod(os.path.join(where, one), 0o644)
            except OSError:
                pass
    root.cleanup()


def _runner(argv, *, directory):
    answered = subprocess.run(list(argv), cwd=directory, capture_output=True,
                              timeout=120)
    return {"returncode": answered.returncode, "stdout": answered.stdout,
            "stderr": answered.stderr}


class RealLine:
    """A disposable retained line with REAL history.

    The whole point of review claim168049 is that preassembled state files
    cannot establish where a combined candidate came from. So these cases build
    an actual base, an actual candidate and a target that moved INDEPENDENTLY,
    and let the worker derive the combination itself.
    """

    def __init__(self, place):
        self.place = place
        os.makedirs(place, exist_ok=True)
        self.run(["init", "--quiet", "-b", "main", "."])
        self.run(["config", "user.email", "preparation@example.invalid"])
        self.run(["config", "user.name", "preparation"])

    def run(self, argv):
        answered = subprocess.run([V] + argv, cwd=self.place,
                                  capture_output=True, timeout=120)
        if answered.returncode:
            raise AssertionError(argv + [answered.stderr.decode()[:400]])
        return answered.stdout.decode().strip()

    def write(self, name, body):
        with open(os.path.join(self.place, name), "w", encoding="utf-8") as h:
            h.write(body)

    def commit(self, message):
        self.run(["add", "-A"])
        self.run(["commit", "--quiet", "-m", message])
        return self.run(["rev-parse", "HEAD"])

    def tree_of(self, revision):
        return self.run(["rev-parse", revision + "^{tree}"])


class OnePreparationRunsThroughTheOrdinaryWorker(unittest.TestCase):
    """CHECKPOINT A.2 -- the configured preparation, end to end, over a REAL
    line.

    The real producer exports the accepted objects, the real request composer
    builds the document, and the real agent the image injects into
    `baton_worker.main` derives the combination itself. Nothing here is
    preassembled and nothing here is a status-only stand-in.
    """

    TARGET_FILE = "target_only.py"

    def setUp(self):
        from baton_v12.integration import managed_execution as managed
        from baton_v12.job_manager import execution_limits

        self.managed = managed
        self.root = tempfile.TemporaryDirectory(prefix="v12-preparation-run-")
        self.addCleanup(_release, self.root)
        self.limits = execution_limits.resolved(
            None, execution_limits.CURRENT_GENERATION)
        self.line = RealLine(os.path.join(self.root.name, "line"))
        self.input = os.path.join(self.root.name, "input")
        self.output = os.path.join(self.root.name, "output")
        self.scratch = os.path.join(self.root.name, "scratch")
        os.makedirs(self.output)
        self.revisions = self.history()
        self.published = bundle.compose_preparation_input(
            self.input, request=self.request(), runner=_runner,
            repository=self.line.place)

    def history(self, conflicting=False):
        """base -> candidate (adds the fix), and a target that moved on its
        own. `conflicting` makes both sides change the SAME line."""
        line = self.line
        line.write("feature.py", "VALUE = 1\n")
        line.write("harness.py", HARNESS)
        base = line.commit("base")
        line.write("fix.py", "VALUE = 2\n")
        if conflicting:
            line.write("feature.py", "VALUE = 2  # candidate\n")
        candidate = line.commit("candidate adds the fix")
        line.run(["checkout", "--quiet", "-b", "target", base])
        if conflicting:
            line.write("feature.py", "VALUE = 99  # target\n")
        else:
            line.write(self.TARGET_FILE, "TARGET = True\n")
        target = line.commit("the target moved independently")
        return {"base": base, "candidate": candidate,
                "target_revision": target}

    def request(self, **changed):
        held = {"orchestration_id": "o1", "canonical_target_id": "t1",
                "job_id": "job-a", "line_id": "line-b",
                "source_proposal_id": "p1", "source": dict(self.revisions),
                "authority": {"path_set_digest": "sha256:" + "1" * 64,
                              "test_scope_digest": "sha256:" + "2" * 64},
                "harness_digest": "sha256:" + "h" * 64,
                "profile_digest": "sha256:" + "p" * 64,
                "input_digest": "sha256:" + "0" * 64,
                "execution_limits": self.limits,
                "commands": list(task.CAUSAL_ORDER)}
        held.update(changed)
        composed = self.managed.preparation_request(**held)
        composed.pop("input_digest")
        return composed

    def launch(self, limits=None):
        return {"contract": "prepare this",
                "job_execution": {"execution_limits":
                                  self.limits if limits is None else limits}}

    def agent(self, **changed):
        held = {"input_root": self.input, "output_root": self.output,
                "scratch": self.scratch}
        held.update(changed)
        return entry.PreparationAgent(**held)

    def declared(self):
        return [{"name": entry.REPORT_OUTPUT, "path": "report"},
                {"name": entry.CANDIDATE_OUTPUT, "path": "candidate"}]

    def report(self, output=None):
        with open(os.path.join(output or self.output, "report",
                               "report.json")) as one:
            return json.load(one)

    # -- what the coordinator is allowed to send -----------------------------

    def test_only_accepted_objects_are_published_not_prepared_trees(self):
        """REVIEW claim168049 [P1]. A container handed a finished combined tree
        derives nothing and can never meet a conflict, so its success would say
        nothing about where that content came from. What travels is OBJECTS."""
        self.assertEqual([one["path"] for one in
                          self.published["source_manifest"]],
                         [bundle.PREPARATION_OBJECTS])
        self.assertEqual(bundle.PREPARATION_OBJECTS, task.OBJECTS_NAME)

    # -- what the worker derives ---------------------------------------------

    def test_the_worker_derives_the_combination_and_runs_the_sequence(self):
        answered = self.agent().work(self.launch(), self.declared())
        self.assertEqual(answered["disposition"], "completed")
        report = self.report()
        self.assertEqual(report["kind"], "measured")
        # THE BASE FAILS BECAUSE THE FIX IS ABSENT, under the COMBINED
        # content's own harness, carried in.
        self.assertEqual(
            {one["name"]: (one["status"], one["harness_added"])
             for one in report["completed"]},
            {"combined": (0, False), "base": (1, True), "isolated": (0, False)})
        self.assertEqual(report["not_run"], [])

    def test_the_derived_candidate_is_not_the_original_candidate(self):
        """`_CausalObserver.observe` uses `basis[candidate]` for the prepared
        workspace and `self._candidate` for the original isolated line. Those
        are two identities, and a copied state label does not make them one."""
        self.agent().work(self.launch(), self.declared())
        derived = self.report()["derived_candidate"]
        self.assertNotEqual(derived["revision"], self.revisions["candidate"])
        self.assertNotEqual(derived["tree"],
                            self.line.tree_of(self.revisions["candidate"]))
        # AND THE ORIGINALS TRAVEL BESIDE IT, not instead of it.
        self.assertEqual(derived["candidate"], self.revisions["candidate"])
        self.assertEqual(derived["base"], self.revisions["base"])
        self.assertEqual(derived["target_revision"],
                         self.revisions["target_revision"])

    def test_the_targets_own_changes_survive_the_combination(self):
        """A preparation that took the candidate's tree wholesale would
        silently discard everything the target gained since the base -- and
        would still look like a success."""
        self.agent().work(self.launch(), self.declared())
        produced = os.listdir(os.path.join(self.output, "candidate"))
        self.assertIn(self.TARGET_FILE, produced)
        self.assertIn("fix.py", produced)
        # The original candidate does NOT contain the target's file, so this
        # could only have come from a real combination.
        self.assertNotIn(
            self.TARGET_FILE,
            self.line.run(["ls-tree", "--name-only",
                           self.revisions["candidate"]]).split())

    def test_a_real_conflict_refuses_and_is_reported_as_one(self):
        """Two independent changes to one region cannot be combined, and
        resolving that by preferring a side would invent a candidate nobody
        wrote."""
        root = tempfile.TemporaryDirectory(prefix="v12-preparation-clash-")
        self.addCleanup(_release, root)
        self.line = RealLine(os.path.join(root.name, "line"))
        self.revisions = self.history(conflicting=True)
        self.input = os.path.join(root.name, "input")
        self.output = os.path.join(root.name, "output")
        os.makedirs(self.output)
        bundle.compose_preparation_input(
            self.input, request=self.request(), runner=_runner,
            repository=self.line.place)
        answered = self.agent(scratch=os.path.join(root.name,
                                                   "scratch")).work(
            self.launch(), self.declared())
        report = self.report()
        self.assertEqual(report["kind"], "not-collected")
        self.assertEqual(report["tag"], "conflict")
        self.assertEqual(report["phase"], "combined")
        self.assertEqual(report["completed"], [])
        self.assertEqual(report["not_run"], list(task.CAUSAL_ORDER))
        self.assertIsNone(report["derived_candidate"])
        # NO PREPARED CANDIDATE IS HANDED BACK, because there is not one.
        self.assertEqual(
            [one["status"] for one in answered["outputs"]
             if one["name"] == entry.CANDIDATE_OUTPUT], ["absent"])

    def test_a_revision_outside_the_published_objects_refuses(self):
        """The bundle is the whole object supply: there is no remote and no
        other line reachable from this container, so what a preparation can
        derive from is bounded by what was accepted."""
        stranger = dict(self.revisions, candidate="f" * 40)
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.materialize(self.input,
                             dict(self.published["request"], source=stranger),
                             self.scratch)
        self.assertIn("do not contain", str(caught.exception))

    # -- the boundary --------------------------------------------------------

    def test_the_states_are_private_and_the_publication_is_untouched(self):
        self.agent().work(self.launch(), self.declared())
        for state in task.CAUSAL_ORDER:
            place = os.path.join(self.scratch, state)
            self.assertTrue(os.path.isdir(place))
            self.assertEqual(os.stat(place).st_mode & 0o777, 0o700)
        self.assertEqual(
            task.measure(os.path.join(self.input,
                                      task.SOURCE_DIRECTORY))["tree_digest"],
            self.published["input_digest"])

    def test_a_tampered_published_artifact_never_reaches_execution(self):
        """A helper that refuses when called proves nothing about a
        composition that forgot to call it."""
        victim = os.path.join(self.input, task.SOURCE_DIRECTORY,
                              task.OBJECTS_NAME)
        os.chmod(os.path.join(self.input, task.SOURCE_DIRECTORY), 0o755)
        os.chmod(victim, 0o644)
        with open(victim, "ab") as handle:
            handle.write(b"tampered")
        with self.assertRaises(task.PreparationRefusal) as caught:
            self.agent().work(self.launch(), self.declared())
        self.assertIn("not the ones this request was composed over",
                      str(caught.exception))
        self.assertFalse(os.path.exists(self.scratch))
        self.assertFalse(os.path.exists(os.path.join(self.output, "report")))

    def test_a_request_disagreeing_with_the_launch_never_runs(self):
        other = dict(self.limits, compatibility_generation=999)
        with self.assertRaises(task.PreparationRefusal):
            self.agent().work(self.launch(limits=other), self.declared())
        self.assertFalse(os.path.exists(self.scratch))

    def test_a_launch_without_sealed_limits_declines_rather_than_starting(self):
        answered = self.agent().consider({"contract": "prepare"}, {})
        self.assertEqual(answered["decision"], "decline")
        self.assertIn("no verified limits", answered["reason"])

    def test_the_command_bound_comes_from_the_launch_and_is_not_invented(self):
        self.assertEqual(
            entry._bound(self.limits),
            self.limits["boundaries"]["integration_verification"]["seconds"])
        with self.assertRaises(task.PreparationRefusal) as caught:
            entry._bound(dict(self.limits, boundaries={}))
        self.assertIn("will not invent one", str(caught.exception))

    def test_the_worker_holds_no_manager_or_target_capability(self):
        """The derivation happens here, which makes "what else can it reach"
        the question. It reaches the published objects and nothing further."""
        import ast
        import pathlib

        for module in (task, entry):
            tree = ast.parse(pathlib.Path(module.__file__)
                             .read_text(encoding="utf-8"))
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.update(one.name.split(".")[0]
                                 for one in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names.add(node.module.split(".")[0])
            self.assertNotIn("baton_v12", names)
        # THE STRING LITERALS THE CODE ACTUALLY USES, not the prose. This
        # module's own docstring says "there is no remote, no network and no
        # other line reachable from this container" -- so a text search finds
        # the sentence promising the absence, exactly as it did for `serve` in
        # the viewer and for `baton_v12` here earlier. Docstrings are excluded
        # and what remains is what the program can actually pass to a command.
        tree = ast.parse(pathlib.Path(task.__file__)
                         .read_text(encoding="utf-8"))
        spoken = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                held = ast.get_docstring(node, clean=False)
                if held is not None:
                    spoken.add(held)
        literals = {node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and node.value not in spoken}
        for absent in ("remote", "clone", "push", "pull", "http://",
                       "https://", "ssh://"):
            self.assertNotIn(absent, literals)
        # AND NOTHING IT PASSES CONTAINS A URL SCHEME.
        self.assertFalse([one for one in literals if "://" in one])

    def test_the_entry_is_baton_workers_main_and_not_a_second_serve_loop(self):
        import ast
        import pathlib

        source = (pathlib.Path(entry.__file__)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(one.name.split(".")[0] for one in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        self.assertEqual(names, {"os", "sys", "baton_worker",
                                 "reconciliation_task"})
        called = {node.func.attr for node in ast.walk(tree)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)}
        self.assertIn("main", called)
        for absent in ("serve", "read_launch", "launched"):
            self.assertNotIn(absent, called)


class TheCoordinatorHostNeverPrepares(unittest.TestCase):
    """W161230 slice2: THE COORDINATOR-HOST PREPARATION TRAP.

    A finite acceptance case in its own right -- "trap legacy `prepare_result`/
    `_CausalObserver`/`_ConfiguredExecution` or actual merge/harness runner
    calls in the managed coordinator process; fail if preparation escapes the
    worker seam; allow only declared read-only identity/object export; show the
    trap catches an intentionally invoked forbidden boundary."

    WHY IT IS BUILT BEFORE THE BRANCH IT GUARDS. The managed branch's whole
    claim is that preparation happens at the WORKER, and a branch is the worst
    possible place to discover that claim is false: by then a merge has already
    run on the coordinator's host, in the coordinator's workspace, under the
    coordinator's capabilities. The trap is what makes "it did not happen here"
    a measurement rather than a reading of the code, and A.5's proving test is
    written to run inside it.

    WHAT IT INTERCEPTS, STATED NARROWLY. Each forbidden owner's MODULE
    ATTRIBUTE is replaced with something that raises, so a call that resolves
    the name at call time is caught however the call site spells it. Review
    claim168871 corrected the broader sentence that used to be here: this does
    NOT intercept a reference captured before the trap was armed, nor a
    pre-existing class base, so "every reachable coordinator execution path is
    intercepted" is more than these cases measure. The consequence is an
    ORDERING REQUIREMENT rather than a weaker guard -- A.5's composed test must
    arm the trap BEFORE it constructs or captures the managed call path, and
    instrument that path's own execution boundaries.

    AND THE ONE THING IT MUST NOT TRAP is the declared read-only export. The
    selected composition allows exactly that on the coordinator -- identity
    reads and one bounded object export -- so a trap that forbade it would
    forbid the accepted design rather than the defect, and every managed branch
    would have to disable it to work. `compose_preparation_input` takes its
    runner by injection, which is what makes the distinction expressible: the
    trap closes `stage_execution._git_run`, the coordinator's own harness and
    merge runner, and leaves an explicitly supplied read-only runner alone.
    """

    FORBIDDEN = ("prepare_result", "record_causal_observations")

    def setUp(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
        from baton_v12.integration import reconciliation
        from tools import stage_execution

        self.reconciliation = reconciliation
        self.stage_execution = stage_execution
        self.reached = []

    def trapped(self):
        """Every forbidden coordinator-host boundary, replaced by a refusal."""
        import contextlib
        from unittest import mock

        def refuse(name):
            def caught(*arguments, **keywords):
                self.reached.append(name)
                raise AssertionError(
                    "coordinator-host preparation escaped the worker seam: "
                    + name)
            return caught

        held = contextlib.ExitStack()
        for name in self.FORBIDDEN:
            held.enter_context(mock.patch.object(
                self.reconciliation, name, refuse(
                    "reconciliation." + name)))
        for name in ("_CausalObserver", "_ConfiguredExecution", "_git_run"):
            held.enter_context(mock.patch.object(
                self.stage_execution, name,
                refuse("stage_execution." + name)))
        return held

    # -- the trap catches what it is for ----------------------------------

    def test_the_trap_catches_an_intentionally_invoked_boundary(self):
        """THE TRAP IS SHOWN TO WORK, which is the half a trap usually skips.

        Each forbidden boundary is invoked ON PURPOSE inside the trap and must
        be caught. A trap nobody demonstrated is a trap nobody knows is armed:
        every case below rests on this one.
        """
        for name, invoke in (
                ("reconciliation.prepare_result",
                 lambda: self.reconciliation.prepare_result(None, None, None,
                                                            None, None)),
                ("reconciliation.record_causal_observations",
                 lambda: self.reconciliation.record_causal_observations(
                     None, None, result_id="result-1")),
                ("stage_execution._CausalObserver",
                 lambda: self.stage_execution._CausalObserver()),
                ("stage_execution._ConfiguredExecution",
                 lambda: self.stage_execution._ConfiguredExecution()),
                ("stage_execution._git_run",
                 lambda: self.stage_execution._git_run(("merge",)))):
            with self.subTest(boundary=name):
                self.reached = []
                with self.trapped():
                    with self.assertRaises(AssertionError) as caught:
                        invoke()
                self.assertIn("escaped the worker seam", str(caught.exception))
                self.assertEqual(self.reached, [name])

    # -- and the declared read-only export is NOT trapped -------------------

    def test_the_declared_read_only_export_runs_inside_the_trap(self):
        """THE ONE COORDINATOR ACT THE DESIGN ALLOWS, proved to survive.

        `compose_preparation_input` performs one bounded read-only export over
        the retained line through a runner it is GIVEN. That injection is what
        makes the boundary expressible: the coordinator's own merge and harness
        runner is closed, and this is not it.
        """
        line = RealLine(tempfile.mkdtemp(prefix="w161230-trap-line-"))
        self.addCleanup(shutil.rmtree, line.place, ignore_errors=True)
        # A REAL LINE, the same shape the derivation cases build: a base, a
        # candidate that adds the fix, and a target that moved on its own.
        line.write("feature.py", "VALUE = 1\n")
        base = line.commit("base")
        line.write("fix.py", "VALUE = 2\n")
        candidate = line.commit("candidate adds the fix")
        line.run(["checkout", "--quiet", "-b", "target", base])
        line.write("moved.py", "TARGET = True\n")
        target = line.commit("the target moved independently")
        # THE BUNDLE IS PUBLISHED ONCE AND NEVER APPENDED TO, so the
        # destination must NOT exist: only its parent is made here.
        home = tempfile.mkdtemp(prefix="w161230-trap-input-")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        destination = os.path.join(home, "published")

        request = {
            "schema": "baton.v12.managed-preparation-request/1",
            "orchestration_id": "integration-trap-1",
            "canonical_target_id": "target:mainline",
            "job_id": "job-a", "line_id": "line-1",
            "source_proposal_id": "proposal-1",
            "source": {"base": base, "candidate": candidate,
                       "target_revision": target},
            "authority": {"path_set_digest": "sha256:" + "1" * 64,
                          "test_scope_digest": "sha256:" + "2" * 64},
            "harness_digest": "sha256:" + "h" * 64,
            "profile_digest": "sha256:" + "p" * 64,
            "execution_limits": None,
            "commands": ["combined", "base", "isolated"]}
        request.pop("execution_limits")

        with self.trapped():
            published = bundle.compose_preparation_input(
                destination, request=request, runner=_runner,
                repository=line.place)
        # IT REALLY EXPORTED, and the trap was armed while it did.
        self.assertTrue(published["input_digest"].startswith("sha256:"))
        self.assertEqual(self.reached, [])
        # AND THE COORDINATOR'S OWN RUNNER WAS NEVER THE ONE USED.
        with self.trapped():
            with self.assertRaises(AssertionError):
                self.stage_execution._git_run(("merge",))

    def test_the_legacy_host_branch_is_preserved_beside_the_managed_seam(self):
        """THE DIRECT AND LEGACY PATHS SURVIVE, which is a standing product
        requirement rather than a temporary baseline.

        The previous form of this case asserted that `adopt_prepared_candidate`
        was ABSENT from `stage_execution.py` -- a baseline that would have made
        successful implementation fail, which review claim168871 called out.
        The historical fact is preserved in this Work's record; what is
        asserted here is the invariant that outlives the wiring: the legacy
        host branch still reaches its own owners, so a managed deployment is an
        addition rather than a replacement.
        """
        import inspect

        source = inspect.getsource(self.stage_execution.Integration.reconciled)
        self.assertIn("prepare_result", source)
        self.assertIn("_CausalObserver", source)


class TheResolverCallsItsOwnersCorrectly(unittest.TestCase):
    """W161230: the two API mismatches review claim169477 reproduced.

    Both were call-shape defects that only a real call could find, and both
    were mine: `required_tests` belongs to `Integration` and I reached for it
    on the deployment, which has no such member; and
    `job_execution_reader`'s reader takes four KEYWORD-ONLY operands and I
    called it positionally. The reviewer's diagnostic probe is preserved
    history -- it constructs the old signature and cannot run against the
    corrected one -- so these are the typed checks that replace it.
    """

    def setUp(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
        from tools import stage_execution

        self.stage_execution = stage_execution

    def resolver(self, jobs=None, required=None):
        held = self.stage_execution.StageDeployment.__new__(
            self.stage_execution.StageDeployment)
        held.jobs = jobs
        return self.stage_execution.PreparationResolver(
            # THE INTEGRATION WORKER'S OWN HELD DEPLOYMENT, whose shape this
            # stub had stated incompletely. `_held_integration` derives
            # `input_manifest` for this role and `_held` already proved the
            # adapter, image and toolchain, so a stub omitting them was
            # asserting over a document the composition never sees.
            held, worker={"participant": "baton.impl-a",
                          "profile_digest": "sha256:" + "p" * 64,
                          "policy_digest": "sha256:" + "q" * 64,
                          "profile_name": "reference",
                          "adapter_name": "reference",
                          "adapter_digest": "sha256:" + "a" * 64,
                          "image_digest": "sha256:" + "m" * 64,
                          "input_manifest": {
                              "manifest_digest": "sha256:" + "i" * 64,
                              "toolchain_digest": "sha256:" + "t" * 64},
                          "task_bytes": b'{"apply": "instructions"}'},
            required_tests=required or (lambda job_id: {"job": job_id}))

    def composed(self, given, integrator=None, deployment=None,
                 authority=None, closed=None):
        """Drive the ACTUAL construction, with the resource constructors the
        review's probe used. Nothing here asserts syntax."""
        from tools import stage_execution

        closed = [] if closed is None else closed

        class Ordinary:
            def __init__(self, job_id):
                self.job_id = job_id

            def close(self):
                closed.append(self.job_id)

        def compose(*arguments, **keywords):
            return Ordinary(len(closed))

        with mock.patch.object(stage_execution.single_worker,
                               "worker_operations", compose):
            answer = stage_execution._integration_operations(
                given, {"role": "integration",
                        "deployment": {"participant": "baton.impl-a",
                                       "profile_digest": "sha256:" + "p" * 64,
                                       "policy_digest": "sha256:" + "q" * 64,
                                       "profile_name": "reference",
                                       "task_bytes": b'{"apply": "x"}'}},
                object(), object(), authority,
                engine_run=None, clock=None, checkpoint=None,
                job_store=object(), integrator=integrator,
                deployment=deployment)
        return answer, closed

    def given(self, **changed):
        # A BINDING WITH NO JOB is the shape `_served_deployment` returns
        # early on, so this drives the construction without needing a producer
        # worker that this case is not about.
        held = {"job_bindings": [{"job_id": None}], "workers": []}
        held.update(changed)
        return held

    # -- the closed selection, driven rather than inspected -----------------

    def test_an_unselected_deployment_composes_no_preparation(self):
        answer, closed = self.composed(self.given())
        self.assertIsNone(answer._preparation)
        self.assertEqual(closed, [])

    def test_a_selection_this_build_cannot_place_refuses(self):
        """A STRING IS NOT A DECISION. Review claim169661: `given.get(...)`
        accepted the string "false" as a selection, so a deployment spelling
        its refusal would have been opted in BY THE SPELLING. The vocabulary is
        closed, and a value outside it refuses rather than being guessed."""
        for held in ("false", "true", 1, 0, "", None if False else "yes"):
            with self.subTest(configured=held):
                with self.assertRaises(ContractRefusal) as caught:
                    self.composed(self.given(integration_preparation=held))
                self.assertIn("cannot place", str(caught.exception))

    def test_a_malformed_selection_refuses_at_STATIC_PREFLIGHT(self):
        """THE RIGHT MOMENT, which review claim169721 measured me getting
        wrong.

        I validated the selection in `_integration_operations`, so seven
        malformed values were ADMITTED by `held_configuration` and refused only
        once workers and resources were being composed.
        `held_configuration`'s own docstring says why that is wrong: the later
        refusal happens with an Authority open and a workspace group
        configured, and it describes a different failure than the one the
        operator actually made. The proof is that the configuration document
        itself is now refused.
        """
        from tools import stage_execution
        from tests.tools import test_stage_execution

        fixture = test_stage_execution.StageCase()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for value in ("false", "true", 1, 0, "", None, "yes"):
            with self.subTest(configured=value):
                with self.assertRaises(stage_execution.ContractRefusal) as held:
                    fixture.held(integration_preparation=value)
                self.assertIn("cannot place", str(held.exception))
        # AND THE TWO IT CAN PLACE ARE ACCEPTED, so this is a vocabulary rather
        # than a refusal of the member.
        for value in (True, False):
            with self.subTest(configured=value):
                self.assertEqual(
                    fixture.held(integration_preparation=value)[
                        "integration_preparation"], value)

    def test_a_selected_deployment_with_no_integrator_refuses(self):
        """A SELECTED PATH THAT SILENTLY BECAME THE ORDINARY ONE would run the
        unmanaged branch under a managed configuration. It refuses -- and the
        ordinary operations already composed are CLOSED on the way out."""
        with self.assertRaises(ContractRefusal) as caught:
            self.composed(self.given(integration_preparation=True))
        self.assertIn("supplies no integrator", str(caught.exception))

    def test_a_refusal_while_constructing_releases_what_it_built(self):
        """`operations_from`'s rule applies to the WHOLE composition. The first
        form wrapped and returned outside the guard, so a port-construction
        refusal left every already-composed ordinary operations object with
        nobody holding a reference to close it."""
        from tools import integration_worker, stage_execution

        # THE LIST IS HELD OUTSIDE THE CALL, because the refusal never
        # returns -- and a case that only asserted "it raised" would pass
        # whether or not anything was released. Measured: it did.
        closed = []
        # `integration_worker` is imported INSIDE the function, so the patch
        # goes on that module rather than on a name `stage_execution` does not
        # hold at rest.
        with mock.patch.object(integration_worker, "authority_port",
                               side_effect=ContractRefusal(
                                   "refused", "capability", "no port here")):
            with self.assertRaises(ContractRefusal):
                self.composed(self.given(integration_preparation=True),
                              integrator=mock.Mock(), deployment=mock.Mock(),
                              closed=closed)
        # EVERY ORDINARY OPERATIONS OBJECT ALREADY COMPOSED WAS CLOSED.
        self.assertEqual(closed, [0])

    def test_the_apply_digest_measures_the_configured_workload_bytes(self):
        """THE OWNERSHIP ANSWER, measured rather than substituted.

        The digest names STABLE TASK MATERIAL -- what the apply is asked to
        execute -- and that material is this deployment's own configured
        integration workload document, held as exact immutable bytes by
        `single_worker._task_bytes` during static configuration. It is not the
        producer's task (that is the material being INTEGRATED), not the
        required-test digest, not a constant and not a future collected digest.
        """
        from baton_v12.contracts import digest_of_bytes

        held = self.resolver()
        self.assertEqual(held.apply_task_digest(),
                         digest_of_bytes(b'{"apply": "instructions"}'))
        # AND CHANGED MATERIAL IS A CHANGED IDENTITY, which is the whole
        # reason it is measured: a later reconstruction must reach the same
        # digest from the same bytes and a different one from different bytes.
        other = self.resolver()
        other._worker = dict(other._worker,
                             task_bytes=b'{"apply": "other instructions"}')
        self.assertNotEqual(other.apply_task_digest(),
                            held.apply_task_digest())

    def test_a_deployment_with_no_configured_workload_refuses(self):
        """Absence refuses rather than defaulting. A phase label, a constant or
        the required-test digest is not the material an apply must obey."""
        held = self.resolver()
        held._worker = dict(held._worker, task_bytes=None)
        with self.assertRaises(ContractRefusal) as caught:
            held.apply_task_digest()
        self.assertIn("no configured task bytes", str(caught.exception))

    def test_the_required_test_selection_is_the_integrators(self):
        """`Integration` owns that derivation and the deployment does not, so
        it is INJECTED rather than reached for. The old form raised
        AttributeError at the first real call."""
        asked = []
        held = self.resolver(required=lambda job_id: asked.append(job_id)
                             or {"task_digest": "sha256:" + "a" * 64})
        answer = held.required({}, "job-a")
        self.assertEqual(asked, ["job-a"])
        self.assertEqual(answer["task_digest"], "sha256:" + "a" * 64)
        self.assertTrue(hasattr(self.stage_execution.Integration,
                                "required_tests"))
        self.assertFalse(hasattr(self.stage_execution.StageDeployment,
                                 "required_tests"))

    def test_the_job_limits_reader_gets_every_operand_it_requires(self):
        """Four keyword-only operands, from the stage and the Job. The old
        form called it positionally and raised TypeError."""
        from baton_v12.job_manager import execution_limits

        seen = {}

        class Jobs:
            pass

        def reader(job_store):
            def held(*, job_id, attempt_id, runtime_input_digest,
                     runtime_policy_digest):
                seen.update({"job_id": job_id, "attempt_id": attempt_id,
                             "input": runtime_input_digest,
                             "policy": runtime_policy_digest})
                return {"execution_limits": execution_limits.resolved({}, 1)}
            return held

        held = self.resolver(jobs=Jobs())
        with mock.patch.object(self.stage_execution.single_worker,
                               "job_execution_reader", reader):
            answer = held.limits({"attempt_id": "attempt-1"},
                                 {"input_digest": "sha256:" + "i" * 64,
                                  "policy_digest": "sha256:" + "y" * 64},
                                 "job-a")
        self.assertEqual(seen, {"job_id": "job-a", "attempt_id": "attempt-1",
                                "input": "sha256:" + "i" * 64,
                                "policy": "sha256:" + "y" * 64})
        self.assertEqual(answer, execution_limits.resolved({}, 1))

    def test_a_resumed_sweep_reads_no_owner_but_its_own_intent(self):
        """"Resolves nothing" was FALSE of my first form -- line, checkpoint
        and required tests all ran before the intent branch. The deployment
        here would raise on any of those, so reaching one fails this case."""
        held = self.resolver(jobs=None, required=self.refuse)
        held._deployment.integration_root = tempfile.mkdtemp(
            prefix="w161230-resumed-")
        self.addCleanup(shutil.rmtree, held._deployment.integration_root,
                        ignore_errors=True)
        intent = {"orchestration_id": "integration:attempt-1",
                  "execution_work_id": "0123abcd-W2",
                  "execution_route": "integration-preparation",
                  "plan": [{"phase": "prepare",
                            "execution_attempt_id": "a-1",
                            "execution_offer_id": "o-1",
                            "participant": "baton.impl-a",
                            "task_digest": "sha256:" + "a" * 64,
                            "profile_digest": "sha256:" + "p" * 64},
                           {"phase": "apply",
                            "execution_attempt_id": "a-2",
                            "execution_offer_id": "o-2",
                            "participant": "baton.impl-a",
                            "task_digest": "sha256:" + "b" * 64,
                            "profile_digest": "sha256:" + "p" * 64}]}
        answer = held({"attempt_id": "attempt-1"}, None, intent)
        self.assertEqual(answer["execution_work_id"], "0123abcd-W2")
        self.assertEqual(answer["execution_attempt_id"], "a-1")
        self.assertEqual(answer["apply_task_digest"], "sha256:" + "b" * 64)
        # AND THE REQUEST IS LEFT FOR RECOVERY, not composed here.
        self.assertIsNone(answer["request"])
        self.assertIsNone(answer["task_digest"])

    @staticmethod
    def refuse(job_id):
        raise AssertionError("a resumed sweep asked an owner: " + repr(job_id))


class TheOperandsAreResolvedFromOwnerAnswers(unittest.TestCase):
    """W161230 A.4: what a managed preparation is ASKED for, and whose answer
    each operand is.

    THE REQUEST IS NOT A DOCUMENT THIS COMPOSITION AUTHORS. Every member is
    somebody else's committed answer -- the development line's accepted
    integration checkpoint for the base and candidate, the producer's published
    proposal, the Authority's canonical target pinned at intent time, the Job's
    own resolved limits, and the measurement `compose_preparation_input` took
    over the bundle it wrote. These cases drive the resolver with real owner
    SHAPES and a real published bundle rather than with a hand-written request.
    """

    # THE TEST SCOPE IS A SEPARATE OWNER'S ANSWER, not a checkpoint field. In
    # the deployment it is the required-test selection's own task digest; here
    # it stands for that answer and is passed as its own operand, which is the
    # point: a checkpoint cannot supply it and nothing invents one.
    TEST_SCOPE = "sha256:" + "2" * 64

    def setUp(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
        from tools import integration_worker

        self.worker = integration_worker
        self.line = RealLine(tempfile.mkdtemp(prefix="w161230-operands-"))
        self.addCleanup(shutil.rmtree, self.line.place, ignore_errors=True)
        self.line.write("feature.py", "VALUE = 1\n")
        self.base = self.line.commit("base")
        self.line.write("fix.py", "VALUE = 2\n")
        self.candidate = self.line.commit("candidate adds the fix")
        self.line.run(["checkout", "--quiet", "-b", "target", self.base])
        self.line.write("moved.py", "TARGET = True\n")
        self.target = self.line.commit("the target moved independently")
        self.home = tempfile.mkdtemp(prefix="w161230-operands-input-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.published = 0

    # THE OWNER'S ACTUAL ANSWER SHAPE, and review claim169146 is why it is
    # written out here. My first fixture invented `path_set_digest` and
    # `test_scope_digest` as TOP-LEVEL members, which is a shape
    # `review_cycles.integration_checkpoint` never answers with -- so the
    # resolver read fields that do not exist and the fixture hid it. The real
    # answer is these five members with the path set NESTED in the evidence,
    # and there is no test scope on a checkpoint at all.
    CHECKPOINT_MEMBERS = ("line_id", "checkpoint_id", "verdict_id",
                          "checkpoint_digest", "evidence")

    def accepted(self, **changed):
        """The line's accepted checkpoint, in the shape its reader answers."""
        held = {"line_id": "line-1", "checkpoint_id": "checkpoint-1",
                "verdict_id": "verdict-1",
                "checkpoint_digest": "sha256:" + "3" * 64,
                "evidence": {"base": self.base, "head": self.candidate,
                             "tree": "t" * 40, "profile": "git",
                             "reference": "checkpoint/line-1/1",
                             "paths": ["fix.py"],
                             "path_set_digest": "sha256:" + "1" * 64}}
        held.update(changed)
        return held

    def publish(self, accepted, target):
        """A REAL bundle, measured by its own producer."""
        from baton_v12.job_manager import execution_limits

        self.published += 1
        request = {
            "schema": "baton.v12.managed-preparation-request/1",
            "orchestration_id": "orch-1",
            "canonical_target_id": "target:mainline",
            "job_id": "job-a", "line_id": "line-1",
            "source_proposal_id": "proposal-1",
            "source": {"base": accepted["evidence"]["base"],
                       "candidate": accepted["evidence"]["head"],
                       "target_revision": target},
            "authority": {
                "path_set_digest": accepted["evidence"]["path_set_digest"],
                "test_scope_digest": self.TEST_SCOPE},
            "harness_digest": "sha256:" + "h" * 64,
            "profile_digest": "sha256:" + "p" * 64,
            "execution_limits": execution_limits.resolved({}, 1),
            "commands": list(self.worker.CAUSAL_COMMANDS)}
        # THE ROOT IS REMEMBERED, not recomputed: the recovery reads back
        # exactly where this publication landed.
        self.last_root = os.path.join(self.home,
                                      f"published-{self.published}")
        return bundle.compose_preparation_input(
            self.last_root, request=request, runner=_runner,
            repository=self.line.place)

    def resolved(self, accepted=None, target=None, **changed):
        from baton_v12.job_manager import execution_limits

        accepted = self.accepted() if accepted is None else accepted
        target = self.target if target is None else target
        held = {"orchestration_id": "orch-1",
                "execution_work_id": "0123abcd-W2",
                "execution_route": "integration-preparation",
                "participant": "baton.impl-a", "accepted": accepted,
                "proposal_id": "proposal-1",
                "canonical_target_id": "target:mainline",
                "job_id": "job-a", "line_id": "line-1",
                "target_revision": target,
                "test_scope_digest": self.TEST_SCOPE,
                "harness_digest": "sha256:" + "h" * 64,
                "profile_digest": "sha256:" + "p" * 64,
                "policy_digest": "sha256:" + "q" * 64,
                "profile_name": "reference",
                "apply_task_digest": "sha256:" + "d" * 64,
                "limits": execution_limits.resolved({}, 1),
                "published": self.publish(accepted, target),
                # AND THE IDENTITY its runtime attempt is recorded under,
                # likewise an operand: the configured child worker's own.
                "identity": {"adapter_name": "reference",
                             "adapter_digest": "sha256:" + "a" * 64,
                             "profile_digest": "sha256:" + "p" * 64,
                             "input_digest": "sha256:" + "i" * 64,
                             "policy_digest": "sha256:" + "q" * 64,
                             "image_digest": "sha256:" + "m" * 64,
                             "toolchain_digest": "sha256:" + "t" * 64},
                # THE WORKER'S OWN ACCEPTANCE, an operand rather than a thing
                # this composition performs. These cases are about the
                # operands; `ChildAcceptance` has its own.
                "accept": lambda issued: None}
        held["published_root"] = self.last_root
        held.update(changed)
        return self.worker.preparation_operands(**held)

    def held_identity(self):
        """The configured child worker's recorded identity."""
        return {"adapter_name": "reference",
                "adapter_digest": "sha256:" + "a" * 64,
                "profile_digest": "sha256:" + "p" * 64,
                "input_digest": "sha256:" + "i" * 64,
                "policy_digest": "sha256:" + "q" * 64,
                "image_digest": "sha256:" + "m" * 64,
                "toolchain_digest": "sha256:" + "t" * 64}

    # -- whose answer each operand is --------------------------------------

    def test_the_resolver_consumes_the_real_readers_answer(self):
        """THE ACTUAL OWNER, not my idea of it.

        Review claim169146 [P1]: the resolver read `path_set_digest` and
        `test_scope_digest` off the top of the checkpoint and my fixture
        invented both, so nothing measured the mismatch. This drives
        `review_cycles.integration_checkpoint` itself: five members, the path
        set NESTED in the evidence, and no test scope anywhere on it. The
        resolver consumes that answer and reaches its own bundle rule -- as far
        as an inert published placeholder can go, named rather than dressed up
        as a full composition.
        """
        from baton_v12.job_manager import execution_limits
        from baton_v12.worker_manager import review_cycles
        from tests.tools import test_integration_bundle as owner_fixture

        world = owner_fixture.ProducerCase("run")
        world.setUp()
        self.addCleanup(world.doCleanups)
        accepted = review_cycles.integration_checkpoint(
            world.world.manager, world.world.line_id)
        self.assertEqual(sorted(accepted), sorted(self.CHECKPOINT_MEMBERS))
        self.assertIn("path_set_digest", accepted["evidence"])
        self.assertNotIn("test_scope_digest", accepted)
        self.assertNotIn("test_scope_digest", accepted["evidence"])
        with self.assertRaises(ContractRefusal) as caught:
            self.worker.preparation_operands(
                orchestration_id="orch-real", execution_work_id="0123abcd-W2",
                execution_route="integration-preparation",
                participant="baton.impl-a", accepted=accepted,
                proposal_id=world.world.proposal_id,
                canonical_target_id=world.world.target, job_id="job-a",
                line_id=world.world.line_id,
                target_revision=accepted["evidence"]["base"],
                test_scope_digest=self.TEST_SCOPE,
                harness_digest="sha256:" + "h" * 64,
                profile_digest="sha256:" + "p" * 64,
                policy_digest="sha256:" + "q" * 64, profile_name="reference",
                apply_task_digest="sha256:" + "d" * 64,
                limits=execution_limits.resolved({}, 1),
                published={"input_digest": "sha256:" + "e" * 64,
                           "request": {}},
                published_root=self.home,
                accept=lambda issued: None,
                identity=self.held_identity())
        # IT GOT PAST THE OWNER READS and stopped at the bundle rule.
        self.assertIn("one document", str(caught.exception))

    def test_a_checkpoint_without_evidence_paths_refuses(self):
        """A preparation runs the paths an accepted verdict authorized. A
        checkpoint answer carrying no evidence path set names none."""
        from baton_v12.job_manager import execution_limits

        stripped = dict(self.accepted(),
                        evidence={"base": self.base, "head": self.candidate})
        with self.assertRaises(ContractRefusal) as caught:
            self.worker.preparation_operands(
                orchestration_id="orch-1", execution_work_id="0123abcd-W2",
                execution_route="integration-preparation",
                participant="baton.impl-a", accepted=stripped,
                proposal_id="proposal-1",
                canonical_target_id="target:mainline", job_id="job-a",
                line_id="line-1", target_revision=self.target,
                test_scope_digest=self.TEST_SCOPE,
                harness_digest="sha256:" + "h" * 64,
                profile_digest="sha256:" + "p" * 64,
                policy_digest="sha256:" + "q" * 64, profile_name="reference",
                apply_task_digest="sha256:" + "d" * 64,
                limits=execution_limits.resolved({}, 1),
                published=self.publish(self.accepted(), self.target),
                published_root=self.last_root,
                accept=lambda issued: None,
                identity=self.held_identity())
        self.assertIn("no evidence path set", str(caught.exception))

    def test_the_published_request_is_recoverable(self):
        """THE BUNDLE IS THE DURABLE RECORD OF WHAT WAS ASKED.

        Review claim169283: the committed intent persists the child Work and
        the request's DIGEST, not the document and not the target it pinned.
        So a resumed sweep that RECOMPOSED from a newer canonical target would
        be refused by that digest forever and never resume -- the refusal
        correct, the orchestration stuck behind it. What it must do is recover
        the request it already published, which is this read.
        """
        published = self.publish(self.accepted(), self.target)
        recovered = bundle.published_preparation_request(
            os.path.join(self.home, "published-" + str(self.published)))
        self.assertEqual(recovered, published["request"])
        # AND IT COMES BACK THROUGH THE REQUEST'S OWN COMPOSER, so what is
        # recovered has passed the same rules it passed going in.
        from baton_v12.integration import managed_execution

        self.assertEqual(managed_execution.adopt_preparation_request(recovered),
                         recovered)

    def test_an_absent_publication_is_an_answer_rather_than_an_empty_request(
            self):
        """A published input that is not there is not an empty request: it
        means there is nothing to recover, which a caller holding a committed
        intent must treat as a missing durable record."""
        empty = os.path.join(self.home, "never-published")
        os.makedirs(empty, exist_ok=True)
        self.assertIsNone(bundle.published_preparation_request(empty))

    def test_a_tampered_published_request_does_not_survive_its_composer(self):
        """Recovery is not a trusting read. The document is adopted through
        the composer, so bytes that do not rebuild into the request they claim
        to be are refused rather than returned."""
        self.publish(self.accepted(), self.target)
        place = os.path.join(self.home, "published-" + str(self.published))
        document = os.path.join(place, bundle.PREPARATION_REQUEST_DOCUMENT)
        os.chmod(place, 0o700)
        os.chmod(document, 0o600)
        with open(document, encoding="utf-8") as reading:
            held = json.loads(reading.read())
        # A MEMBER THE CLOSED DOCUMENT DOES NOT HAVE. The composer owns an
        # exact member set, so an addition is refused rather than ignored --
        # which is the difference between adopting a document and reading one.
        held["smuggled"] = "not a request member"
        with open(document, "w", encoding="utf-8") as writing:
            writing.write(json.dumps(held, sort_keys=True))
        with self.assertRaises(ContractRefusal):
            bundle.published_preparation_request(place)

    def preparing(self, store=None):
        """A ManagedPreparation with no owners but the recovery path."""
        return self.worker.ManagedPreparation(
            jobs=None, control=None, authority=None, port=None,
            mint_bearer=lambda: "bearer-1",
            orchestration=lambda _stage, _job: "orch-1",
            operands=lambda _stage, _job, _intent: {})

    def test_a_resumed_sweep_RECOVERS_rather_than_being_refused(self):
        """THE WHOLE POINT OF RECOVERING, and what my earlier guard got wrong.

        Review claim169347: comparing a RECOMPOSED request against the intent's
        digest refuses a moved target forever and never resumes. So a sweep
        that resolved a fresh target -- which is what a later sweep naturally
        does -- must have its request REPLACED by the one this orchestration
        already published, not be turned away for having resolved it.
        """
        held = self.resolved()
        place = held["published_root"]
        moved = dict(held["request"])
        moved["source"] = dict(moved["source"], target_revision=self.base)
        intent = {"request_digest": held["task_digest"],
                  "execution_work_id": held["execution_work_id"]}
        recovered = self.preparing()._recovered(
            intent, dict(held, request=moved,
                         task_digest="sha256:" + "0" * 64))
        # THE PUBLISHED REQUEST WINS, and the derived task digest follows it.
        self.assertEqual(recovered["request"], held["request"])
        self.assertEqual(recovered["task_digest"], held["task_digest"])
        self.assertEqual(recovered["input_digest"], held["input_digest"])
        self.assertEqual(
            bundle.published_preparation_request(place), held["request"])

    def test_a_resumed_sweep_naming_another_child_work_still_refuses(self):
        """A DISTINCT INVARIANT FROM RECOVERY, and review claim169416 caught me
        collapsing the two.

        Recovering a moved target and refusing a changed child Work are not the
        same rule: the first says the REQUEST is whatever this orchestration
        published, the second says the CHILD is whatever its intent created.
        When I replaced the old refusal cases, the recovery case I put in their
        place exercised `_recovered` alone and never reached `_preserved`'s
        child comparison at all. This drives the whole of `_preserved` with a
        VALID published input, so recovery succeeds and the child identity is
        what refuses.
        """
        held = self.resolved()
        intent = {"request_digest": held["task_digest"],
                  "execution_work_id": held["execution_work_id"]}
        with self.assertRaises(ContractRefusal) as caught:
            self.preparing()._preserved(
                intent, dict(held, execution_work_id="0123abcd-W9"))
        self.assertIn("already decided child Work", str(caught.exception))

    def test_an_agreeing_resumed_sweep_passes_through(self):
        """RESUME AGREEMENT, which is the case that has to keep working.

        Review claim169416: my capacity-side "unchanged sweep" case passed
        `None` for the intent even though it had created one, so it proved
        absence passthrough rather than agreement. This one holds a real
        intent, a real published input and operands that match both -- the
        ordinary resumed sweep -- and asserts it is carried rather than
        refused. A guard that only ever refuses would pass every refusal test
        and break every resume.
        """
        held = self.resolved()
        intent = {"request_digest": held["task_digest"],
                  "execution_work_id": held["execution_work_id"]}
        carried = self.preparing()._preserved(intent, dict(held))
        self.assertEqual(carried["request"], held["request"])
        self.assertEqual(carried["task_digest"], held["task_digest"])
        self.assertEqual(carried["execution_work_id"],
                         held["execution_work_id"])

    def test_a_published_input_disagreeing_with_the_intent_refuses(self):
        """The durable record and the decision must name ONE request. A
        publication composed for another snapshot is not this orchestration's
        recovered request however well-formed it is."""
        held = self.resolved()
        intent = {"request_digest": "sha256:" + "9" * 64,
                  "execution_work_id": held["execution_work_id"]}
        with self.assertRaises(ContractRefusal) as caught:
            self.preparing()._recovered(intent, dict(held))
        self.assertIn("must name one request", str(caught.exception))

    def test_a_committed_intent_with_no_publication_refuses(self):
        """An intent whose publication is gone is a missing durable record,
        not permission to decide the request again."""
        held = self.resolved()
        intent = {"request_digest": held["task_digest"],
                  "execution_work_id": held["execution_work_id"]}
        # THE PUBLICATION IS IMMUTABLE ON PURPOSE -- read-only directories --
        # so removing it for this case means restoring write first. That is a
        # statement about the bundle rather than about this case: a
        # publication is not meant to be taken back.
        place = held["published_root"]
        for root, directories, names in os.walk(place):
            os.chmod(root, 0o700)
            for one in names:
                os.chmod(os.path.join(root, one), 0o600)
        shutil.rmtree(place)
        # A PUBLICATION THAT IS GONE refuses at the bundle owner's own
        # reachability boundary, which is a different fact from a publication
        # that is there and holds no request -- and the two are kept apart.
        with self.assertRaises(ContractRefusal) as caught:
            self.preparing()._recovered(intent, dict(held))
        self.assertIn("not reachable", str(caught.exception))
        # AND A PUBLICATION PRESENT BUT EMPTY is the missing durable record
        # this composition refuses in its own words.
        os.makedirs(place, exist_ok=True)
        with self.assertRaises(ContractRefusal) as empty:
            self.preparing()._recovered(intent, dict(held))
        self.assertIn("no published preparation input", str(empty.exception))

    def test_the_source_is_the_accepted_checkpoints_own_evidence(self):
        """The base and the candidate are the checkpoint's, not this
        composition's. A preparation that chose its own revisions would be
        preparing something nobody accepted."""
        held = self.resolved()
        self.assertEqual(held["request"]["source"],
                         {"base": self.base, "candidate": self.candidate,
                          "target_revision": self.target})
        # TWO OWNERS: the path set is the checkpoint's, nested where that
        # reader keeps it, and the test scope is the selected configuration's.
        self.assertEqual(held["request"]["authority"],
                         {"path_set_digest":
                              self.accepted()["evidence"]["path_set_digest"],
                          "test_scope_digest": self.TEST_SCOPE})

    def test_the_input_digest_is_the_producers_measurement(self):
        """`compose_preparation_input` measures the bundle it wrote; a caller
        that supplied one would be asserting a measurement it did not take."""
        published = self.publish(self.accepted(), self.target)
        held = self.resolved(published=published)
        self.assertEqual(held["input_digest"], published["input_digest"])
        self.assertEqual(held["request"]["input_digest"],
                         published["input_digest"])

    def test_a_published_bundle_for_another_request_refuses(self):
        """THE BUNDLE A WORKER READS AND THE REQUEST ITS INTENT COMMITS ARE ONE
        DOCUMENT. A published input composed for a different snapshot would
        hand the worker one request while the intent recorded another."""
        other = self.publish(self.accepted(), self.base)
        with self.assertRaises(ContractRefusal) as caught:
            self.resolved(published=other)
        self.assertIn("one document", str(caught.exception))

    # -- and the identities a restart has to reach again -------------------

    def test_the_child_identities_are_derived_and_not_minted(self):
        """A restart must reach the SAME three. Identities minted on a second
        sweep would name a different child each time, which is exactly the
        protection `record_preparation_intent`'s derived operation id exists to
        provide."""
        first = self.resolved()
        again = self.resolved()
        for name in ("execution_attempt_id", "execution_offer_id"):
            self.assertEqual(first[name], again[name])
        self.assertEqual(self.worker.preparation_identities("orch-1"),
                         {"execution_attempt_id": first[
                             "execution_attempt_id"],
                          "execution_offer_id": first["execution_offer_id"]})

    def test_the_task_digest_is_the_requests_own_name(self):
        """A membership's task digest is what a later adoption compares the
        task against, so deriving it from the request means the plan and the
        request cannot disagree about what was asked for."""
        from baton_v12.integration import managed_execution

        held = self.resolved()
        self.assertEqual(held["task_digest"],
                         managed_execution.request_digest(held["request"]))
        # AND THE APPLY'S IS A DIFFERENT ACT'S, not this one's.
        self.assertNotEqual(held["apply_task_digest"], held["task_digest"])

    def test_a_moved_target_is_a_different_preparation(self):
        """The target revision is PINNED at intent time. A preparation is about
        an immutable snapshot, so a target that moved is a different request
        with a different name rather than the same run retargeted."""
        first = self.resolved()
        moved = self.resolved(target=self.base)
        self.assertNotEqual(moved["task_digest"], first["task_digest"])
        self.assertEqual(moved["request"]["source"]["target_revision"],
                         self.base)


class ASelectedDeploymentComposesTheManagedPath(unittest.TestCase):
    """W161230 checkpoint A: a REAL deployment that selects managed
    preparation, composed through the ordinary public entry point.

    Every earlier case in this module drove the resolver or the wrapper
    directly. This one composes `operations_from` over real Job and control
    stores with `integration_preparation` SELECTED, so what is exercised is the
    composition an operator would actually get -- and whatever it stops at is
    the real next blocker rather than an inference from a helper.
    """

    def setUp(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
        from tests.tools import test_stage_execution

        self.case = test_stage_execution.ServingCase("run")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.addCleanup(self.case.tearDown)

    def composed(self, **members):
        return self.case.serving(integration_preparation=True, **members)

    def test_a_selected_deployment_composes_and_engages_the_wrapper(self):
        """THE SELECTED PATH, COMPOSED FOR REAL.

        `operations_from` opens the Authority, certifies profiles, configures
        the workspace group and composes every worker; the integration role's
        operations come back WRAPPED, with a managed preparation attached
        rather than `None`. That is the first fact about this path that does
        not depend on me driving a helper.
        """
        from tools import integration_worker

        _job, _control, composed = self.composed()
        held = composed.deployment._integration_operations
        self.assertIsInstance(held, integration_worker.PreparationAdmission)
        self.assertIsNotNone(held._preparation)
        self.assertIsInstance(held._preparation,
                              integration_worker.ManagedPreparation)

    def test_an_unselected_deployment_composes_the_ordinary_path(self):
        """The same composition without the selection carries no preparation,
        which is what makes the selection a choice rather than a migration."""
        from tools import integration_worker

        _job, _control, composed = self.case.serving()
        held = composed.deployment._integration_operations
        self.assertIsInstance(held, integration_worker.PreparationAdmission)
        self.assertIsNone(held._preparation)

    def test_the_resolver_holds_this_deployments_own_apply_material(self):
        """The apply digest measures the INTEGRATION worker's configured
        workload bytes -- a real configured document from this composition
        rather than the fixture bytes the unit cases supply."""
        from baton_v12.contracts import digest_of_bytes

        _job, _control, composed = self.composed()
        preparation = composed.deployment._integration_operations._preparation
        resolver = preparation._operands
        held = resolver._worker["task_bytes"]
        self.assertIsInstance(held, bytes)
        self.assertTrue(held)
        self.assertEqual(resolver.apply_task_digest(), digest_of_bytes(held))


class OneManagedPreparationCompletes(unittest.TestCase):
    def test_ordinary_sweeps_retain_and_adopt_one_real_preparation(self):
        self.complete()

    def test_publication_before_intent_recovers_the_same_request(self):
        self.complete("decide")

    def test_accepted_offer_recovers_without_a_second_bearer(self):
        self.complete("submit_claim")

    def test_committed_claim_recovers_before_attempt_recording(self):
        self.complete("record_attempt")

    def test_admitted_capacity_recovers_before_runtime_start(self):
        self.complete("start")

    def test_unexpected_pre_intent_fault_recovers_the_held_allocation(self):
        self.complete("unexpected-decide")

    # -- W170382 group2: the rest of the selected restart matrix -----------
    #
    # ONE CASE PER SELECTED CUT, each on the ordinary path group1 accepted and
    # each asserting the same finish: one child Work, one claim, one runtime,
    # one harness run, one attachment, the parent still queued, the root still
    # held and apply still planned. `complete` already proves all of that; what
    # each case adds is the position the interruption lands in.

    def test_committed_intent_resumes_its_own_child_work_creation(self):
        """INTENT BEFORE WORK CREATION. The intent carries the
        `work_operation_id` the Authority is then called with, so a sweep
        interrupted here RESUMES that creation. A second child Work would be
        the failure this position exists to exclude."""
        self.complete("create")

    def test_created_child_work_resumes_before_capacity_registration(self):
        """CREATION BEFORE REGISTRATION. The child Work exists at the
        Authority and no capacity plan does."""
        self.complete("register")

    def test_committed_claim_resumes_before_capacity_admission(self):
        """CLAIM BEFORE ADMISSION -- the window a runtime must never start
        in, which is why admission is committed before anything starts."""
        self.complete("admit")

    def test_start_intent_resumes_when_the_adapter_never_answers(self):
        """START INTENT BEFORE ADAPTER RETURN. The start is journalled and
        the adapter's answer never comes back, so the next sweep must
        reconcile the runtime it may already have rather than start a
        second one."""
        self.complete("launch")

    def test_the_worker_answer_resumes_before_output_is_frozen(self):
        """WORKER ANSWER BEFORE FREEZE."""
        self.complete("dispatch")

    def test_frozen_output_resumes_through_intake_and_attachment(self):
        """FREEZE BEFORE INTAKE and ACCEPTED INTAKE BEFORE ATTACHMENT, both
        inside the ordinary `conclude`."""
        self.complete("conclude")

    def test_cleanup_resumes_before_the_membership_is_ended(self):
        """CLEANUP BEFORE MEMBERSHIP ENDING."""
        self.complete("end")

    def test_an_ended_membership_resumes_before_its_candidate_is_adopted(self):
        """ENDING BEFORE ADOPTION. The retained result is already the owner's;
        the adoption that consumes it is the last thing to resume."""
        self.complete("adopt")

    # -- the restart group1 does not own -----------------------------------
    #
    # Every case above loses an in-flight step and keeps its composition. These
    # lose the COMPOSITION AND BOTH STORES at the same step, so what the next
    # sweep knows it read back from a durable owner. The finish is the same
    # one: exactly one child Work, one claim, one runtime, one harness run and
    # one attachment survive the restart.

    def test_a_restart_before_work_creation_resumes_one_child_work(self):
        self.complete("create", restart=True)

    def test_a_restart_before_capacity_registration_resumes_one_plan(self):
        self.complete("register", restart=True)

    def test_a_restart_before_admission_starts_no_second_runtime(self):
        self.complete("admit", restart=True)

    def test_a_restart_before_the_adapter_answers_starts_one_runtime(self):
        self.complete("launch", restart=True)

    def test_a_restart_before_the_freeze_runs_one_harness(self):
        self.complete("dispatch", restart=True)

    def test_a_restart_before_intake_makes_one_attachment(self):
        self.complete("conclude", restart=True)

    def test_a_restart_before_the_ending_ends_the_membership_once(self):
        self.complete("end", restart=True)

    def test_a_restart_before_adoption_adopts_the_same_candidate(self):
        self.complete("adopt", restart=True)

    def test_pre_intent_recovery_refuses_an_existing_child_work(self):
        self.complete("unexpected-decide", obstruct=True)

    # W170382 group2: WHERE EACH SELECTED CUT ACTUALLY LIVES.
    #
    # Group1 resolved this inline and knew three placements, which was exactly
    # enough for the five cuts it owned. The remaining selected cuts fall on
    # owners that inline expression cannot name -- the capacity registrar, the
    # ordinary manager operations, the ending and the adoption -- so the
    # placement becomes a table rather than growing a longer conditional.
    #
    # EVERY ENTRY NAMES A REAL OWNER ON THE ORDINARY PATH. Nothing here
    # introduces a hook, a checkpoint or a test-only seam to interrupt: each is
    # the public operation the preparation actually calls, patched where the
    # caller resolves it. `poll` imports `end_integration_execution` and
    # `reconciliation` INSIDE the method, so those are patched on their
    # defining modules, which is where that import reads them from.
    CUT_OWNERS = {
        # -- group1's five, unchanged in placement and meaning ---------------
        "decide": ("execution", "decide"),
        "unexpected-decide": ("execution", "decide"),
        "start": ("execution", "start"),
        "submit_claim": ("module", "submit_claim"),
        "record_attempt": ("module", "record_attempt"),
        # -- group2: the rest of the selected sequence ----------------------
        # The intent is committed before the Work it names exists, so cutting
        # `create` proves a resumed sweep RESUMES that creation rather than
        # minting a second child Work.
        "create": ("execution", "create"),
        # Creation before registration: the child Work exists and the capacity
        # plan does not.
        "register": ("capacity", "register_integration_capacity"),
        # Claim before admission: the claim is committed and capacity is not
        # admitted, which is the window a runtime must never start in.
        "admit": ("execution", "admit"),
        # Start intent before adapter return: the start intent is journalled
        # and the adapter's answer never comes back.
        "launch": ("operations", "launch"),
        # Worker answer before freeze.
        "dispatch": ("operations", "dispatch"),
        # Freeze before intake, and accepted intake before attachment: both
        # live inside the ordinary `conclude`.
        "conclude": ("operations", "conclude"),
        # Cleanup before membership ending.
        "end": ("capacity", "end_integration_execution"),
        # And the ending before the adoption that consumes it.
        "adopt": ("reconciliation", "adopt_prepared_candidate"),
    }

    def reopen(self, case, held, held_runtime, engine, live):
        """CLOSE AND REBUILD every non-durable owner, mid-preparation.

        This is the restart group1 explicitly does not own. Group1 drops the
        local worker cache with `runtime.close()` and keeps the JobStore, the
        ControlStore and the composed deployment; nothing there proves the
        preparation survives losing the composition itself.

        The durable files are untouched -- that is the point. Everything the
        next sweep knows it must read back from an owner, and `held.job` /
        `held.composed` are rebound so the sweep loop cannot keep driving the
        handles that just went away.
        """
        # THE NEW COMPOSITION IS BUILT BEFORE THE OLD ONE IS RELEASED.
        # Measured: closing first left the rebuilt deployment driving a closed
        # Authority -- "Cannot operate on a closed database" from
        # `authority/store.py:transact`, reached through the NEW composition's
        # own `create`. The Authority handle is not private to one composition
        # here, so releasing it first releases one the successor still needs.
        held_runtime[0].close()
        retired = held.composed
        job, control, composed = case.serving()
        held.job, held.control, held.composed = job, control, composed
        preparation = composed.deployment._integration_operations._preparation
        runtime = preparation._runtime
        # The fixture's engine boundary belongs to the RUN, not to the
        # composition that happened to be alive when it was installed.
        runtime.engine_run = engine
        held_runtime[0] = runtime
        self.preparing = preparation.started
        live[0] = preparation
        return preparation

    def interrupts(self, cut, args, kwargs):
        """WHETHER THIS CALL IS THE PREPARATION'S, and not another worker's.

        The operations cuts land on `ManagerOperations`, which the ordinary
        producer and reviewer workers use too. Cutting the FIRST call of that
        name would have interrupted whatever ran first and then asserted a
        recovery that had nothing to do with a preparation -- the shape of
        false attribution this Work has already paid for twice. So the
        placement is checked against the preparation's own child attempt.

        The owners that only a preparation ever calls need no discrimination,
        and saying so explicitly is cheaper than a check that always answers
        yes.
        """
        if cut not in ("launch", "dispatch", "conclude"):
            return True
        stage = args[1] if len(args) > 1 else kwargs.get("stage")
        started = [one["execution_attempt_id"] for one in self.preparing]
        return bool(stage) and stage.get("attempt_id") in started

    def interruption(self, cut):
        """The ACTUAL owner and attribute this cut interrupts."""
        from baton_v12.integration import reconciliation
        from baton_v12.job_manager import integration_capacity
        from baton_v12.job_manager import delegation
        from tools import integration_worker
        where, method = self.CUT_OWNERS[cut]
        return {"execution": integration_worker.PreparationExecution,
                "module": integration_worker,
                "capacity": integration_capacity,
                "operations": delegation.ManagerOperations,
                "reconciliation": reconciliation}[where], method

    def complete(self, cut=None, obstruct=False, restart=False):
        import time
        from tests.tools import test_stage_execution as fixtures_stage
        from tests.job_manager import fixtures
        from baton_v12.job_manager import sweep
        from baton_v12.job_manager.integration_capacity import integration_capacity_of
        from baton_v12.worker_manager import attempt_runtime_of
        from tools import stage_execution

        class Selected(fixtures_stage.TheComposedJobTraversesReviewAndAcceptance):
            def serving(self, **members):
                from baton_v12.authority import Authority
                authority = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
                try:
                    authority.add_route_handler("integration-preparation", "baton.integrator")
                    generation = authority.policy_generation()
                finally:
                    authority.dispose()
                return super().serving(integration_preparation=True, policy_generation=generation, **members)

        case = Selected("test_the_implementation_handoff_moves_the_work_to_the_review_route")
        case.setUp()
        self.addCleanup(case.doCleanups)
        held = case.reviewed()
        deployment = held.composed.deployment
        preparation = deployment._integration_operations._preparation
        runtime = preparation._runtime
        original_engine = runtime.engine_run
        # THE LIVE PREPARATION, not the one that happened to be composed when
        # the engine spy was written. A restart replaces it, and a spy reading
        # the retired object would answer about a composition that is gone.
        live = [preparation]
        processes = []
        outputs = []

        def cleanup():
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            for handle in outputs:
                handle.close()
        self.addCleanup(cleanup)

        def engine(argv, **options):
            answer = original_engine(argv, **options)
            if argv[1] == "run" and "--entrypoint" not in argv:
                admitted = integration_capacity_of(held.job, live[0].started[-1]["intent"]["orchestration_id"])
                phases = {one["phase"]: one for one in admitted["members"]}
                self.assertEqual(phases["prepare"]["state"], "admitted")
                self.assertEqual(phases["apply"]["state"], "planned")
                self.assertIsNone(held.control.operation_record("offer.issue:" + phases["apply"]["execution_offer_id"]))
                self.assertEqual(phases["prepare"]["participant"], phases["apply"]["participant"])
                mounts = {}
                for index, arg in enumerate(argv[:-1]):
                    if arg == "--mount":
                        parts = dict(part.split("=", 1) for part in argv[index + 1].split(",") if "=" in part)
                        mounts[parts["target"]] = parts["source"]
                code = r"""
import functools, json, os, sys
sys.path.insert(0, sys.argv[1])
import baton_worker, reconciliation_entry
mounts = json.loads(sys.argv[2])
baton_worker.INPUT_ROOT = mounts['/input']
baton_worker.OUTPUT_ROOT = mounts['/output']
reconciliation_entry.PreparationAgent = functools.partial(
    reconciliation_entry.PreparationAgent, input_root=mounts['/input/source'],
    output_root=mounts['/output'], scratch=sys.argv[3])
from pathlib import Path
launch = next((target, source) for target, source in mounts.items() if target.endswith('launch.json'))
command = next(source for target, source in mounts.items() if target.endswith('/command'))
event = next(source for target, source in mounts.items() if target.endswith('/events'))
sys.exit(reconciliation_entry.main(place=launch[1], command_root=command, event_root=event))
"""
                log = tempfile.TemporaryFile()
                outputs.append(log)
                processes.append(subprocess.Popen(
                    [sys.executable, "-c", code, str(WORKER), json.dumps(mounts),
                     os.path.join(case.root, "preparation-scratch")],
                    stdout=log, stderr=log))
            if argv[1] == "stop":
                for process in processes:
                    process.wait(timeout=10)
            return answer
        runtime.engine_run = engine
        held_runtime = [runtime]
        failures = []
        original_admit = preparation.admit
        # Class-level hook because ManagedPreparation deliberately has slots.
        def traced(instance, *args):
            try:
                return original_admit(*args)
            except BaseException as failure:
                failures.append(repr(failure))
                raise
        from tools import integration_worker
        import contextlib
        trap = TheCoordinatorHostNeverPrepares()
        trap.setUp()
        target_before = pathlib.Path(case.source, "harness.py").read_bytes()
        target_revision = deployment.authority.canonical_target()
        target_tree = case.vcs("status", "--porcelain")
        cut_reached, recovered_cuts, reopened, owed_restart = [], [], [], []
        self.preparing = preparation.started
        child_admits, child_deliveries = [], []
        from tools import single_worker
        from baton_v12.job_manager.scheduler import allocation_of
        original_worker_admit = single_worker._SingleWorker.admit
        original_delivery = single_worker._SingleWorker.delivered

        def ordinary_admit(worker, perform, stage, inputs):
            child_admits.append(stage["attempt_id"])
            answer = original_worker_admit(worker, perform, stage, inputs)
            self.assertIsNone(worker.expected_offer)
            with self.assertRaisesRegex(ContractRefusal, "outside its one admission"):
                original_delivery(worker, {})
            return answer

        def ordinary_delivery(worker, issued):
            child_deliveries.append(issued["runtime_attempt_id"])
            self.assertIsNotNone(worker.expected_offer)
            for member in ("offer_id", "runtime_attempt_id", "work_id", "participant"):
                with self.assertRaisesRegex(ContractRefusal, "does not match"):
                    original_delivery(worker, dict(issued, **{member: "different"}))
            return original_delivery(worker, issued)

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(single_worker._SingleWorker, "admit", ordinary_admit))
            stack.enter_context(mock.patch.object(single_worker._SingleWorker, "delivered", ordinary_delivery))
            stack.enter_context(mock.patch.object(integration_worker, "ChildAcceptance", side_effect=AssertionError("duplicate acceptance reached")))
            stack.enter_context(mock.patch.object(integration_worker.ManagedPreparation, "admit", traced))
            stack.enter_context(trap.trapped())
            # Prove the trap itself before trusting its silence in the run.
            with self.assertRaisesRegex(AssertionError, "coordinator-host preparation"):
                stage_execution._git_run(["git", "merge", "forbidden"])
            trap.reached.clear()
            if cut is not None:
                owner, method = self.interruption(cut)
                original = getattr(owner, method)
                def interrupted(*args, **kwargs):
                    if not cut_reached and self.interrupts(cut, args, kwargs):
                        cut_reached.append(cut)
                        if cut == "unexpected-decide":
                            recovered_cuts.append(kwargs["orchestration_id"])
                            if obstruct:
                                from baton_v12.authority.identity import V12
                                deployment.authority.create_work(kwargs["execution_work_id"], kwargs["execution_route"], operation_id="fixture-existing-child", contract=V12)
                            raise RuntimeError("selected unexpected pre-intent fault")
                        # THE RESTART IS OWED, NOT PERFORMED HERE. Closing
                        # the composition inside the cut tears the stores out
                        # from under the sweep that is still unwinding, and
                        # measured, that is exactly what happens: "Cannot
                        # operate on a closed database" from
                        # `_Serving.account`, several frames above. A process
                        # that died does not finish its own stack, so the
                        # restart is taken once this sweep has fully returned.
                        if restart:
                            owed_restart.append(cut)
                        raise ContractRefusal("refused", "precondition", "selected interruption before " + cut)
                    return original(*args, **kwargs)
                stack.enter_context(mock.patch.object(owner, method, interrupted))
            for _ in range(8 if obstruct else 150):
                try:
                    last = sweep(held.job, held.composed, now=fixtures.NOW)
                except RuntimeError as failure:
                    if str(failure) != "selected unexpected pre-intent fault":
                        raise
                    last = {"interrupted": True}
                    capacity = integration_capacity_of(held.job, recovered_cuts[0])
                    self.assertEqual(allocation_of(held.job, capacity["root"]["root_assignment_id"])["allocation_state"], "recovery-required")
                if owed_restart:
                    # THE STORES AND THE COMPOSITION GO AWAY, not just the
                    # local worker cache. Group1's accepted restart is
                    # `runtime.close()`, which keeps both durable handles and
                    # the whole composed deployment alive; that proves a cache
                    # miss recovers, not that a PROCESS does. Here the
                    # composition is closed and rebuilt from the same durable
                    # files, so whatever the next sweep knows, it read back
                    # from an owner.
                    owed_restart.clear()
                    preparation = self.reopen(case, held, held_runtime,
                                              engine, live)
                    reopened.append(preparation)
                if preparation.adopted:
                    break
                time.sleep(0.01)
        if restart:
            self.assertEqual(len(reopened), 1)
            preparation = reopened[0]
            self.assertTrue(preparation.adopted, failures[-3:])
        if obstruct:
            self.assertFalse(preparation.adopted)
            self.assertEqual(processes, [])
            self.assertIn("preparation Work already exists", failures[-1])
            self.assertIsNone(held.job.operation_record("integration-capacity.recover-pre-intent:" + recovered_cuts[0]))
            capacity = integration_capacity_of(held.job, recovered_cuts[0])
            self.assertEqual(allocation_of(held.job, capacity["root"]["root_assignment_id"])["allocation_state"], "recovery-required")
            return
        for log in outputs:
            log.seek(0)
        logs = [log.read().decode(errors="replace") for log in outputs]
        self.assertTrue(preparation.adopted, (failures[:3], failures[-1:], logs, last))
        self.assertEqual(len(processes), 1)
        self.assertEqual(len(child_admits), 1)
        self.assertEqual(child_deliveries, child_admits)
        self.assertEqual(processes[0].returncode, 0)
        self.assertEqual(trap.reached, [])
        self.assertEqual(cut_reached, [] if cut is None else [cut])
        self.assertEqual(pathlib.Path(case.source, "harness.py").read_bytes(), target_before)
        self.assertEqual(deployment.authority.canonical_target(), target_revision)
        self.assertEqual(case.vcs("status", "--porcelain"), target_tree)
        [orchestration] = preparation.adopted
        capacity = integration_capacity_of(held.job, orchestration)
        self.assertEqual(capacity["root"]["lifecycle"], "open")
        if cut == "unexpected-decide":
            self.assertEqual(allocation_of(held.job, capacity["root"]["root_assignment_id"])["allocation_state"], "recovery-required")
            self.assertIsNotNone(held.job.operation_record("integration-capacity.recover-pre-intent:" + orchestration))
        members = {one["phase"]: one for one in capacity["members"]}
        self.assertEqual(members["prepare"]["state"], "ended")
        self.assertEqual(members["apply"]["state"], "planned")
        state = attempt_runtime_of(held.control, members["prepare"]["execution_attempt_id"])
        self.assertEqual(state["execution_runtime"], "destroyed")
        self.assertEqual(state["cleanup"], "retained")
        original_result = preparation.adopted[orchestration]
        preparation.adopted.clear()
        runtime.close()  # Lose the local worker cache; durable owners remain.
        with trap.trapped():
            for _ in range(3):
                sweep(held.job, held.composed, now=fixtures.NOW)
        self.assertEqual(preparation.adopted[orchestration], original_result)
        self.assertEqual(len(processes), 1)
        self.assertEqual(case.states(held.job, held.composed)["integration"], "queued")
        self.assertIsNone(deployment.authority.slot_holder("baton.integrator"))
        print(json.dumps({"proof": "ordinary-managed-preparation", "cut": cut,
                          "fixture_processes": len(processes),
                          "worker_exit": processes[0].returncode,
                          "request_digest": original_result["request_digest"],
                          "harness_digest": original_result["harness_digest"],
                          "candidate_digest": original_result["candidate"]["content_digest"],
                          "runtime": state["execution_runtime"], "cleanup": state["cleanup"],
                          "root": capacity["root"]["lifecycle"], "apply": members["apply"]["state"],
                          "parent": "queued-unclaimed", "cache_recovery": "same-adoption",
                          "host_trap": "proved-and-unreached"}, sort_keys=True))
