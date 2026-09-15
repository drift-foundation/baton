"""W161230 slice2: the preparation workload, at its own boundary.

WHAT IS PROVED HERE. The workload is the least trusted thing in this design --
it runs somewhere else, under somebody else\'s engine, and what comes back from
it is untrusted input. So these cases drive the REAL module: its request
reader, its bounded command runner, its measurement and the three answers it
may compose. Nothing is stubbed that the workload depends on.

THE IMPORT GRAPH IS PART OF THE CONTRACT. A workload that could import the
manager\'s capabilities would be a manager running under a worker\'s name, so
one case reads the module\'s own imports rather than trusting the prose that
says it has none.
"""
import ast
import json
import os
import pathlib
import subprocess
import sys
import shutil
import tempfile
import time
import unittest
from unittest import mock

WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
sys.path.insert(0, str(WORKER))

import reconciliation_task as task                     # noqa: E402

import baton_worker                                    # noqa: E402

from baton_v12.integration import managed_execution as managed   # noqa: E402
from baton_v12.job_manager import execution_limits               # noqa: E402

VCS = "git"


def _producer_request(**changed):
    """A REAL request, composed by the manager\'s own producer.

    Review claim166129 defect 1: the first fixture was written here, carried
    six fewer members than the contract and an incomplete limits document, and
    the worker accepted it while `adopt_preparation_request` refused it. A
    fixture written beside the reader it feeds can only ever prove that reader
    agrees with itself.
    """
    held = {"orchestration_id": "integration-capacity-1",
            "canonical_target_id": "target-1", "job_id": "job-a",
            "line_id": "line-b", "source_proposal_id": "proposal-1",
            "source": {"base": "a" * 40, "candidate": "c" * 40,
                       "target_revision": "d" * 40},
            "authority": {"path_set_digest": "sha256:" + "1" * 64,
                          "test_scope_digest": "sha256:" + "2" * 64},
            "harness_digest": "sha256:" + "h" * 64,
            "profile_digest": "sha256:" + "p" * 64,
            "input_digest": "sha256:" + "i" * 64,
            "execution_limits": _limits(),
            "commands": list(task.CAUSAL_ORDER)}
    held.update(changed)
    return managed.preparation_request(**held)


def _owned():
    return task.owned_limits(_launched())


def _launched(limits=None):
    """The verified launch this container runs under.

    `baton_worker` owns this document, seals its limits and refuses a bound it
    cannot verify. It is the manager-written, per-attempt anchor -- the one
    thing in the container that a request cannot talk its way past.
    """
    return {"job_execution": {"execution_limits": limits
                              if limits is not None else _limits()}}


def _limits():
    return execution_limits.resolved(None, execution_limits.CURRENT_GENERATION)


def _corrupted(**changed):
    """A real producer document, then broken ON DISK.

    A malformed request cannot be COMPOSED -- the producer refuses it, which is
    the point -- so the only honest way to build one is to compose a real
    document and then damage the parsed copy, exactly as a bad actor or a bad
    deployment would deliver it.
    """
    held = _request()
    held.update(changed)
    return held


def _request(**changed):
    """The producer\'s document as it reaches a container: through JSON.

    THE ROUND TRIP IS NOT DECORATION. The producer composes tuples and the
    worker reads a parsed document, so a contract that agreed only in memory
    would still disagree on disk -- which is where the two halves actually
    meet.
    """
    return json.loads(json.dumps(_producer_request(**changed)))


class TheWorkloadImportsNoManager(unittest.TestCase):

    def test_only_the_standard_library_is_imported(self):
        """Read the imports rather than the paragraph that promises them."""
        tree = ast.parse((WORKER / "reconciliation_task.py")
                         .read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(one.name.split(".")[0] for one in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        self.assertEqual(names, {"hashlib", "json", "os", "select", "signal",
                                 "stat", "subprocess", "time"})
        self.assertNotIn("baton_v12", names)

    def test_it_uses_no_target_capability(self):
        """It has no lease, grant or publisher: what leaves it is measured
        content, not a reference somebody moved.

        THE IDENTIFIERS ARE READ, NOT THE PROSE. A text search would be
        satisfied -- or defeated -- by the very paragraph that promises the
        absence, so this walks the names and attributes the module actually
        uses.
        """
        tree = ast.parse((WORKER / "reconciliation_task.py")
                         .read_text(encoding="utf-8"))
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                used.add(node.name)
        for absent in ("lease_id", "live_grant", "settle_integrated",
                       "advance", "Authority", "publish", "publication",
                       "record_managed_result", "transact"):
            self.assertNotIn(absent, used)


class TheRequestIsReadOrRefused(unittest.TestCase):
    """THE TWO INDEPENDENT IMPLEMENTATIONS MUST ACCEPT THE SAME SET.

    Every case here drives BOTH readers -- the manager's
    `adopt_preparation_request` and the worker's `read_request` -- over the
    same bytes. That is the whole content of defect 1: the first worker form
    validated a subset, so a document the manager refused was accepted inside
    the container, where nobody could see it.
    """

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-preparation-")
        self.addCleanup(self.root.cleanup)

    def written(self, body):
        place = os.path.join(self.root.name, task.REQUEST_NAME)
        with open(place, "w", encoding="utf-8") as handle:
            if isinstance(body, str):
                handle.write(body)
            else:
                json.dump(body, handle)
        return self.root.name

    def assertBothRefuse(self, held, because):
        """NEITHER READER MAY BE THE LENIENT ONE."""
        with self.assertRaises(Exception) as manager_said:
            managed.adopt_preparation_request(held)
        self.assertNotIsInstance(manager_said.exception, AssertionError)
        with self.assertRaises(task.PreparationRefusal) as worker_said:
            task.read_request(self.written(held), owned=_owned())
        return manager_said.exception, worker_said.exception

    def test_a_real_producer_document_is_accepted_by_both(self):
        """The agreement, in the direction that matters most: the worker must
        not refuse what the manager composes and accepts."""
        held = _request()
        self.assertEqual(managed.adopt_preparation_request(held), held)
        self.assertEqual(task.read_request(self.written(held), owned=_owned()), held)

    def test_a_digest_form_the_manager_permits_is_not_refused_here(self):
        """THE MIRRORED HALF OF DEFECT 1. The manager reads digests through
        `boundaries.text`, not a hex rule, and a worker enforcing `sha256:`
        plus sixty-four hex characters would refuse real accepted documents.
        Being stricter than the contract is the same disagreement inverted."""
        held = _request()
        self.assertFalse(all(one in "0123456789abcdef"
                             for one in held["harness_digest"][7:]))
        self.assertEqual(task.read_request(self.written(held), owned=_owned()), held)

    def test_an_absent_request_refuses_before_anything_runs(self):
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.read_request(self.root.name, owned=_owned())
        self.assertIn("runs what it was asked for", str(caught.exception))

    def test_an_unreadable_or_foreign_request_refuses(self):
        with self.assertRaises(task.PreparationRefusal):
            task.read_request(self.written("{not json"), owned=_owned())
        self.assertBothRefuse({"schema": "baton.v12.something/1"},
                              "a foreign schema")

    def test_a_missing_member_refuses_in_both(self):
        for member in task.REQUEST_MEMBERS:
            with self.subTest(member=member):
                held = _request()
                held.pop(member)
                self.assertBothRefuse(held, "a missing member")

    def test_an_extra_member_refuses_in_both(self):
        """The manager rebuilds a request through its own composer, so a
        surplus member makes the rebuild unequal. A worker that ignored
        surplus would accept what the manager cannot."""
        _, worker = self.assertBothRefuse(_corrupted(extra="member"),
                                          "a surplus member")
        self.assertIn("extra", str(worker))

    def test_a_revision_expression_refuses_in_both(self):
        """A preparation is about an immutable snapshot: `HEAD~1` and a branch
        name both resolve to something different tomorrow."""
        for member in task.SOURCE_MEMBERS:
            for wrong in ("HEAD~1", "main", "a" * 39, None):
                with self.subTest(member=member, value=wrong):
                    held = _request()
                    held["source"] = dict(held["source"], **{member: wrong})
                    self.assertBothRefuse(held, "a revision expression")

    def test_an_unknown_generation_refuses_in_both(self):
        """THE DEFECT IS CLOSED, NOT FROZEN.

        The previous form of this case ASSERTED the disagreement, which review
        claim166368 rightly called diagnostic history rather than desired
        behaviour. Generation 999 is refused by the manager because
        `owned_generation` will not accept a resolution this build cannot
        reproduce -- and it is refused here because it is not the resolution
        this container was LAUNCHED under. No generation table was copied into
        the worker, and no rule about which generations exist is spelled here.
        """
        self.assertBothRefuse(
            _corrupted(execution_limits=dict(_limits(),
                                             compatibility_generation=999)),
            "a generation this build cannot reproduce")

    def test_the_launch_decides_and_the_request_does_not(self):
        """Equality against the launch's sealed document, so EVERY semantic
        corruption is refused by one rule rather than by a growing list of
        them -- including ones nobody has thought of yet."""
        owned = _limits()
        name = sorted(owned["boundaries"])[0]
        moved = dict(owned["boundaries"])
        moved[name] = dict(moved[name], seconds=moved[name]["seconds"] + 1)
        for label, broken in (
                ("units", dict(owned, units="minutes")),
                ("scope", dict(owned, scope="per-job")),
                ("generation", dict(owned, compatibility_generation=999)),
                ("one boundary second", dict(owned, boundaries=moved)),
                ("a dropped member",
                 {k: v for k, v in owned.items() if k != "requested"}),
                ("a surplus member", dict(owned, surplus=1)),
        ):
            with self.subTest(broken=label):
                with self.assertRaises(task.PreparationRefusal) as caught:
                    task.read_request(
                        self.written(_corrupted(execution_limits=broken)),
                        owned=_owned())
                self.assertIn("the launch decides", str(caught.exception))

    def test_a_float_does_not_pass_an_integer_owned_contract(self):
        """THE SELECTED NUMERIC-TYPE CORRECTION. `300 == 300.0` is True and so
        is `{"seconds": 300} == {"seconds": 300.0}`, so a float representation
        walks through an equality that looks exact while the manager -- whose
        boundary is integer-owned -- refuses it. `True == 1` is the same hole
        one step down."""
        owned = _limits()
        name = sorted(owned["boundaries"])[0]
        seconds = owned["boundaries"][name]["seconds"]
        for label, value in (("a float", float(seconds)), ("a flag", True)):
            with self.subTest(value=label):
                floated = dict(owned["boundaries"])
                floated[name] = dict(floated[name], seconds=value)
                broken = dict(owned, boundaries=floated)
                with self.assertRaises(task.PreparationRefusal) as caught:
                    task.read_request(
                        self.written(_corrupted(execution_limits=broken)),
                        owned=_owned())
                self.assertIn("is still not one", str(caught.exception))
                # AND THE MANAGER REFUSES IT TOO -- that is the whole point.
                with self.assertRaises(Exception):
                    managed.adopt_preparation_request(
                        _corrupted(execution_limits=broken))

    def test_a_container_launched_without_a_job_execution_refuses(self):
        """No verified resolution means no bound this container can honour,
        and a preparation is not run under a limit nobody sealed."""
        for launch in ({}, {"job_execution": {}}, {"job_execution": None}):
            with self.subTest(launch=str(launch)):
                with self.assertRaises(task.PreparationRefusal) as caught:
                    task.owned_limits(launch)
                self.assertIn("no verified limits", str(caught.exception))

    def test_a_command_this_workload_does_not_run_refuses(self):
        for wrong in (["combined", "publish"], [], ["base", "base"]):
            with self.subTest(commands=wrong):
                with self.assertRaises(task.PreparationRefusal):
                    task.read_request(self.written(_corrupted(commands=wrong)),
                                      owned=_owned())

    def test_the_request_is_not_read_through_a_symlink(self):
        """A link out of the input namespace would let the document that
        decides what runs be chosen from somewhere nobody declared."""
        elsewhere = os.path.join(self.root.name, "elsewhere.json")
        with open(elsewhere, "w", encoding="utf-8") as handle:
            json.dump(_request(), handle)
        inside = tempfile.mkdtemp(dir=self.root.name)
        os.symlink(elsewhere, os.path.join(inside, task.REQUEST_NAME))
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.read_request(inside, owned=_owned())
        self.assertIn("without following a link", str(caught.exception))

    def test_a_symlinked_input_ROOT_refuses(self):
        """REVIEW claim166235 DEFECT 2. Checking `islink` on the final
        filename says nothing about the root: a symlinked input root was
        accepted, so the document deciding what runs could be chosen from
        outside the namespace that declared it."""
        real = tempfile.mkdtemp(prefix="v12-real-")
        self.addCleanup(shutil.rmtree, real)
        with open(os.path.join(real, task.REQUEST_NAME), "w") as handle:
            json.dump(_request(), handle)
        linked = os.path.join(self.root.name, "linked-root")
        os.symlink(real, linked)
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.read_request(linked, owned=_owned())
        self.assertIn("without following a link", str(caught.exception))

    def test_a_symlinked_ANCESTOR_of_the_input_root_refuses(self):
        """An ancestor link is the same defect one level further up, and
        `os.walk(followlinks=False)` would not see it either."""
        real = tempfile.mkdtemp(prefix="v12-real-")
        self.addCleanup(shutil.rmtree, real)
        inner = os.path.join(real, "inner")
        os.makedirs(inner)
        with open(os.path.join(inner, task.REQUEST_NAME), "w") as handle:
            json.dump(_request(), handle)
        linked = os.path.join(self.root.name, "linked-parent")
        os.symlink(real, linked)
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.read_request(os.path.join(linked, "inner"), owned=_owned())
        self.assertIn("without following a link", str(caught.exception))

    def test_an_input_root_that_is_not_a_directory_refuses(self):
        place = os.path.join(self.root.name, "not-a-directory")
        with open(place, "w") as handle:
            handle.write("x")
        with self.assertRaises(task.PreparationRefusal):
            task.read_request(place, owned=_owned())

    def test_the_request_is_read_from_the_descriptor_it_was_checked_on(self):
        """A SWAP BETWEEN THE CHECK AND THE READ. Establishing size and type
        by path and then opening BY NAME leaves a window in which the name can
        be repointed, so the bound was proved about a file that is no longer
        the one being read. Here a fifo left in place of the request refuses
        for what the DESCRIPTOR is -- and, because the open is non-blocking,
        it refuses instead of waiting forever for a writer."""
        os.mkfifo(os.path.join(self.root.name, task.REQUEST_NAME))
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.read_request(self.root.name, owned=_owned())
        self.assertIn("not a regular file", str(caught.exception))

    def test_an_unbounded_request_refuses(self):
        place = os.path.join(self.root.name, task.REQUEST_NAME)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(" " * (task.MAX_REQUEST_BYTES + 1))
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.read_request(self.root.name, owned=_owned())
        self.assertIn("larger than", str(caught.exception))


class ATimeoutIsNotAnExitCode(unittest.TestCase):
    """The whole vocabulary this workload is careful about."""

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-preparation-")
        self.addCleanup(self.root.cleanup)

    def test_a_real_status_is_the_one_the_command_exited_with(self):
        answered = task.run_bounded([sys.executable, "-c", "raise SystemExit(3)"],
                                    self.root.name, 30)
        self.assertEqual(answered["status"], 3)
        self.assertIsNone(answered["tag"])

    def test_a_timeout_produces_no_status_at_all(self):
        answered = task.run_bounded(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            self.root.name, 1)
        self.assertIsNone(answered["status"])
        self.assertEqual(answered["tag"], "timeout")
        self.assertIn("no status", answered["output"])

    def test_a_forked_descendant_does_not_outlive_the_bound(self):
        """REVIEW claim166235. `subprocess.run(timeout=...)` signals the
        DIRECT CHILD only, so a harness that forks leaves descendants running
        with the pipe still open -- the read blocks on them and the workload
        reports a timeout while the work it started carries on. The child owns
        a process GROUP and the group is what ends."""
        marker = os.path.join(self.root.name, "descendant.pid")
        child = (
            "import os, sys, time\n"
            "pid = os.fork()\n"
            "if pid == 0:\n"
            "    open(%r, 'w').write(str(os.getpid()))\n"
            "    time.sleep(120)\n"
            "    sys.exit(0)\n"
            "time.sleep(120)\n" % marker)
        answered = task.run_bounded([sys.executable, "-c", child],
                                    self.root.name, 2)
        self.assertIsNone(answered["status"])
        self.assertEqual(answered["tag"], "timeout")
        # THE DESCENDANT IS GONE, and that is checked rather than assumed.
        with open(marker) as handle:
            descendant = int(handle.read())
        for _ in range(200):
            try:
                os.kill(descendant, 0)
            except OSError:
                break
            time.sleep(0.01)
        else:
            self.fail("the forked descendant %d outlived the bound"
                      % descendant)

    def _alive(self, pid, within=3.0):
        until = time.monotonic() + within
        while time.monotonic() < until:
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            time.sleep(0.01)
        return True

    def _descendant(self, body, marker):
        """A leader that forks `body` and then EXITS, leaving the descendant
        behind -- the shape `child.poll()` cannot see."""
        return ("import os, sys, time\n"
                "if os.fork() == 0:\n"
                "    open(%r, 'w').write(str(os.getpid()))\n"
                "    sys.stdout.close()\n"
                + body +
                "    sys.exit(0)\n"
                "sys.exit(0)\n") % marker

    def _marker(self):
        place = os.path.join(self.root.name, "descendant.pid")
        until = time.monotonic() + 5.0
        while time.monotonic() < until:
            if os.path.exists(place) and os.path.getsize(place):
                with open(place) as handle:
                    return int(handle.read())
            time.sleep(0.01)
        self.fail("the descendant never announced itself")

    def test_a_leader_that_exits_first_does_not_end_the_group(self):
        """REVIEW claim166368 [P1]. The leader exits immediately, so
        `child.poll()` reports a finished process while the descendant runs
        on. Watching the leader would call this an ordinary completion; the
        group is what must be observed, and the descendant must be gone."""
        answered = task.run_bounded(
            [sys.executable, "-c",
             self._descendant("    time.sleep(120)\n",
                              os.path.join(self.root.name,
                                           "descendant.pid"))],
            self.root.name, 2)
        # The leader's OWN status is real and is reported; what must not
        # happen is the descendant surviving because `poll()` said "finished".
        self.assertEqual(answered["status"], 0)
        self.assertFalse(self._alive(self._marker()),
                         "the descendant outlived its group's ending")

    def test_a_TERM_resistant_descendant_is_still_excluded(self):
        """A descendant that ignores SIGTERM broke the old sequence before
        SIGKILL was ever sent, because the LEADER had died to the TERM."""
        body = ("    import signal\n"
                "    signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "    time.sleep(120)\n")
        answered = task.run_bounded(
            [sys.executable, "-c",
             self._descendant(body, os.path.join(self.root.name,
                                                 "descendant.pid"))],
            self.root.name, 2)
        self.assertEqual(answered["status"], 0)
        self.assertFalse(self._alive(self._marker()),
                         "a TERM-resistant descendant was never SIGKILLed")

    def test_an_ordinary_exit_with_a_surviving_child_is_still_ended(self):
        """The leader exits ZERO and leaves work running. A measured status is
        not handed back while this workload's own group is still alive."""
        body = ("    time.sleep(120)\n")
        answered = task.run_bounded(
            [sys.executable, "-c",
             self._descendant(body, os.path.join(self.root.name,
                                                 "descendant.pid"))],
            self.root.name, 30)
        descendant = self._marker()
        self.assertEqual(answered["status"], 0)
        self.assertFalse(self._alive(descendant),
                         "an ordinary exit left its group running")

    def test_an_inherited_pipe_eof_is_not_a_finished_group(self):
        """EOF says every writer closed its copy; a descendant that closed the
        inherited pipe and kept running produces exactly that."""
        body = ("    time.sleep(120)\n")
        answered = task.run_bounded(
            [sys.executable, "-c",
             self._descendant(body, os.path.join(self.root.name,
                                                 "descendant.pid"))],
            self.root.name, 30)
        self.assertIsNotNone(self._marker())
        self.assertEqual(answered["status"], 0)

    def test_the_output_is_bounded_as_it_is_drained(self):
        """`capture_output` buffers everything and only then slices, so
        MAX_OUTPUT bounded the report and not the memory. What is not kept is
        never held -- and what was dropped is SAID, because output that
        silently stops looks exactly like output that ended."""
        loud = ("import sys\n"
                "sys.stdout.write('x' * 200000)\n"
                "sys.stdout.flush()\n")
        answered = task.run_bounded([sys.executable, "-c", loud],
                                    self.root.name, 30)
        self.assertEqual(answered["status"], 0)
        self.assertLess(len(answered["output"]), task.MAX_OUTPUT + 200)
        self.assertIn("further bytes were not kept", answered["output"])

    def test_a_command_that_cannot_start_produces_no_status(self):
        answered = task.run_bounded(["/nonexistent/harness"],
                                    self.root.name, 5)
        self.assertIsNone(answered["status"])
        self.assertEqual(answered["tag"], "start-failed")


class TheMeasurementDescribesTheTreeItMeasured(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-preparation-")
        self.addCleanup(self.root.cleanup)
        self.place = self.root.name

    def write(self, name, body):
        full = os.path.join(self.place, name)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(body)

    def test_every_file_is_measured_by_digest_and_length(self):
        self.write("a.py", "VALUE = 1\n")
        self.write("pkg/b.py", "VALUE = 2\n")
        held = task.measure(self.place)
        self.assertEqual([one["path"] for one in held["entries"]],
                         ["a.py", os.path.join("pkg", "b.py")])
        self.assertEqual(held["entry_count"], 2)
        self.assertEqual(held["total_bytes"], 20)
        for one in held["entries"]:
            self.assertTrue(one["content_digest"].startswith("sha256:"))

    def test_the_same_content_measures_the_same_tree(self):
        self.write("a.py", "VALUE = 1\n")
        first = task.measure(self.place)
        second = task.measure(self.place)
        self.assertEqual(first["tree_digest"], second["tree_digest"])

    def test_a_symlink_refuses_rather_than_disappearing(self):
        """CORRECTED UNDER STANDING TEST AUTHORITY (review claim166129 defect
        2). The first form of this case asserted the symlink was OMITTED, and
        omission is the defect: one tree_digest would then describe a tree with
        the link and a tree without it -- two different trees with one
        identity, which is the exact thing a content identity exists to
        prevent."""
        self.write("a.py", "VALUE = 1\n")
        os.symlink("/etc/hostname", os.path.join(self.place, "escape"))
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.measure(self.place)
        self.assertIn("escape", str(caught.exception))
        self.assertIn("one identity", str(caught.exception))

    def test_a_symlinked_directory_refuses_too(self):
        """`os.walk` leaves it out of the traversal on its own, so checking
        only files would let a whole subtree vanish without a word."""
        self.write("a.py", "VALUE = 1\n")
        outside = tempfile.mkdtemp(prefix="v12-outside-")
        self.addCleanup(os.rmdir, outside)
        os.symlink(outside, os.path.join(self.place, "linked"))
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.measure(self.place)
        self.assertIn("linked", str(caught.exception))

    def test_a_non_regular_entry_refuses(self):
        """A fifo has no content to describe, so it cannot be measured and
        must not be passed over in silence."""
        self.write("a.py", "VALUE = 1\n")
        os.mkfifo(os.path.join(self.place, "pipe"))
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.measure(self.place)
        self.assertIn("pipe", str(caught.exception))


class TheReportSaysWhatItObserved(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-preparation-")
        self.addCleanup(self.root.cleanup)
        self.states = {}
        for name in task.CAUSAL_ORDER:
            place = os.path.join(self.root.name, name)
            os.makedirs(place)
            with open(os.path.join(place, "feature.py"), "w") as handle:
                handle.write("VALUE = 1\n")
            self.states[name] = {"path": place, "revision": "a" * 40}

    def harness(self, name, body):
        with open(os.path.join(self.states[name]["path"], "harness.py"),
                  "w", encoding="utf-8") as handle:
            handle.write(body)

    def test_a_passing_sequence_is_measured_with_no_suffix(self):
        for name in task.CAUSAL_ORDER:
            self.harness(name, "raise SystemExit(0)\n")
        completed, not_run, tag, failed, pinned = task.observe(_request(), self.states, 30)
        self.assertEqual([one["name"] for one in completed],
                         list(task.CAUSAL_ORDER))
        self.assertEqual(not_run, [])
        self.assertIsNone(tag)
        report = task.compose_report(_request(), self.states, completed,
                                     not_run, tag, failed, pinned)
        self.assertEqual(report["kind"], "measured")
        self.assertEqual(report["status"], 0)

    def test_a_genuine_base_failure_is_a_real_integer(self):
        """A base that fails BECAUSE the fix is absent is positive evidence,
        and it is carried as the status it actually exited with."""
        # THE PINNED HARNESS is the combined content's own, and it is what
        # decides every state: it passes where the fix is present and fails
        # where it is not.
        for name in task.CAUSAL_ORDER:
            self.harness(name, "import os\n"
                               "raise SystemExit(0 if os.path.exists('fix.py')"
                               " else 1)\n")
        for name in ("combined", "isolated"):
            with open(os.path.join(self.states[name]["path"], "fix.py"),
                      "w") as handle:
                handle.write("VALUE = 2\n")
        completed, not_run, tag, failed, pinned = task.observe(_request(), self.states, 30)
        report = task.compose_report(_request(), self.states, completed,
                                     not_run, tag, failed, pinned)
        self.assertEqual(report["kind"], "measured")
        self.assertEqual(report["status"], 1)
        self.assertEqual(
            {one["name"]: one["status"] for one in report["completed"]},
            {"combined": 0, "base": 1, "isolated": 0})
        self.assertEqual(report["not_run"], [])

    def test_a_combined_failure_remains_a_measured_failure(self):
        for name in task.CAUSAL_ORDER:
            self.harness(name, "import os\nraise SystemExit(7 if os.path.basename(os.getcwd()) == 'combined' else 0)\n")
        report = task.compose_report(_request(), self.states,
                                     *task.observe(_request(), self.states, 5))
        self.assertEqual(report["kind"], "measured")
        self.assertEqual(report["status"], 7)
        self.assertEqual([row["status"] for row in report["completed"]], [7, 0, 0])
        self.assertEqual(report["not_run"], [])

    def test_each_causal_position_times_out_with_its_exact_prefix_and_suffix(self):
        for index, phase in enumerate(task.CAUSAL_ORDER):
            with self.subTest(phase=phase):
                for name in task.CAUSAL_ORDER:
                    self.harness(name, "import os, time\ntime.sleep(3 if os.path.basename(os.getcwd()) == " + repr(phase) + " else 0)\n")
                report = task.compose_report(_request(), self.states,
                                             *task.observe(_request(), self.states, 1))
                self.assertEqual(report["kind"], "collected-without-status")
                self.assertIsNone(report["status"])
                self.assertEqual(report["tag"], "timeout")
                self.assertEqual(report["phase"], phase)
                self.assertEqual([row["name"] for row in report["completed"]], list(task.CAUSAL_ORDER[:index]))
                self.assertEqual(report["not_run"], list(task.CAUSAL_ORDER[index + 1:]))

    def test_each_causal_position_start_failure_preserves_the_real_prefix(self):
        original = task.subprocess.Popen
        for index, phase in enumerate(task.CAUSAL_ORDER):
            with self.subTest(phase=phase):
                for name in task.CAUSAL_ORDER:
                    self.harness(name, "raise SystemExit(0)\n")
                calls = []

                def start(argv, **options):
                    current = os.path.basename(options["cwd"])
                    calls.append(current)
                    if current == phase:
                        raise FileNotFoundError("selected unavailable executable")
                    return original(argv, **options)

                with mock.patch.object(task.subprocess, "Popen", start):
                    report = task.compose_report(_request(), self.states,
                                                 *task.observe(_request(), self.states, 5))
                self.assertEqual(calls, list(task.CAUSAL_ORDER[:index + 1]))
                self.assertEqual(report["kind"], "collected-without-status")
                self.assertIsNone(report["status"])
                self.assertEqual(report["tag"], "start-failed")
                self.assertEqual(report["phase"], phase)
                self.assertEqual([row["name"] for row in report["completed"]], list(task.CAUSAL_ORDER[:index]))
                self.assertEqual(report["not_run"], list(task.CAUSAL_ORDER[index + 1:]))

    def test_a_cut_phase_is_not_counted_as_never_having_run(self):
        """CORRECTED UNDER STANDING TEST AUTHORITY (review claim166129 defect
        3). The first form asserted `not_run == [base, isolated]`, which says
        the base never ran. It DID run and produced no status -- and the
        accepted `_CausalObserver` reports exactly that: phase=base with the
        suffix [isolated]. A phase that was attempted is evidence; one that
        never started is not, and merging them destroys the difference."""
        # The pinned harness sleeps where the fix is absent, so the CARRIED
        # copy is what exceeds the bound in the base state.
        self.harness("combined", "import os, time\n"
                                 "time.sleep(0 if os.path.exists('fix.py')"
                                 " else 5)\n")
        self.harness("isolated", "raise SystemExit(0)\n")
        with open(os.path.join(self.states["combined"]["path"], "fix.py"),
                  "w") as handle:
            handle.write("VALUE = 2\n")
        completed, not_run, tag, failed, pinned = task.observe(_request(),
                                                       self.states, 1)
        report = task.compose_report(_request(), self.states, completed,
                                     not_run, tag, failed, pinned)
        self.assertEqual(report["kind"], "collected-without-status")
        self.assertIsNone(report["status"])
        self.assertEqual(report["tag"], "timeout")
        self.assertEqual([one["name"] for one in report["completed"]],
                         ["combined"])
        # THE OBSERVER'S OWN SHAPE: the attempted phase, and the suffix that
        # genuinely never started -- separately.
        self.assertEqual(report["phase"], "base")
        self.assertEqual(report["not_run"], ["isolated"])
        self.assertNotIn("base", report["not_run"])

    def test_nothing_observed_at_all_is_its_own_answer(self):
        for name in task.CAUSAL_ORDER:
            self.harness(name, "raise SystemExit(0)\n")
        report = task.compose_report(_request(), self.states, [], [], None)
        self.assertEqual(report["kind"], "not-collected")
        self.assertIsNone(report["status"])
        self.assertIsNone(report["tag"])

    def test_the_report_claims_nothing_about_collection(self):
        """A workload cannot say its output was frozen, taken into custody or
        accepted: those are the manager\'s acts."""
        self.harness("combined", "raise SystemExit(0)\n")
        self.harness("base", "raise SystemExit(0)\n")
        self.harness("isolated", "raise SystemExit(0)\n")
        completed, not_run, tag, failed, pinned = task.observe(_request(), self.states, 30)
        report = task.compose_report(_request(), self.states, completed,
                                     not_run, tag, failed, pinned)
        body = json.dumps(report)
        for absent in ("accepted", "custody", "frozen", "integrated",
                       "receipt"):
            self.assertNotIn(absent, body)
        # AND IT CARRIES THE MEASURED CONTENT of every state it ran against.
        self.assertEqual(sorted(report["states"]),
                         sorted(task.CAUSAL_ORDER))
        for name in task.CAUSAL_ORDER:
            self.assertTrue(report["states"][name]["content"]["entries"])

    def test_the_base_is_measured_with_the_combined_harness(self):
        """`_CausalObserver`\'s rule, held here: the base predates the test the
        producer brought with the fix, so the base runs the COMBINED content\'s
        harness -- not whatever file the base happens to contain."""
        self.harness("combined", "open('/dev/null','w')\nraise SystemExit(0)\n")
        # The base\'s OWN harness would pass. The combined one must not.
        self.harness("base", "raise SystemExit(0)\n")
        self.harness("isolated", "raise SystemExit(0)\n")
        carried = os.path.join(self.states["combined"]["path"], "harness.py")
        with open(carried, "w") as handle:
            handle.write("import os\n"
                         "raise SystemExit(0 if os.path.exists('fix.py') "
                         "else 7)\n")
        completed, not_run, tag, failed, pinned = task.observe(_request(), self.states, 30)
        answers = {one["name"]: one for one in completed}
        # The base has no `fix.py`, so the CARRIED harness fails there with its
        # own status -- which is the positive evidence about the missing fix.
        self.assertEqual(answers["base"]["status"], 7)
        self.assertTrue(answers["base"]["harness_added"])
        self.assertFalse(answers["combined"]["harness_added"])
        self.assertFalse(answers["isolated"]["harness_added"])
        # AND THE CARRY REALLY REPLACED the base\'s own file on disk.
        with open(os.path.join(self.states["base"]["path"], "harness.py")) as h:
            self.assertIn("fix.py", h.read())

    def test_a_combined_state_with_no_harness_refuses(self):
        """Its status would measure something else, and carrying nothing
        forward would let the base run whatever it happened to contain. The
        refusal now precedes the run, because the harness is pinned first."""
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.observe(_request(commands=["combined", "base"]),
                         self.states, 30)
        self.assertIn("would measure something else", str(caught.exception))

    def test_a_base_without_a_preceding_combined_state_refuses(self):
        """The carry has no source, and the base\'s own file is not a
        substitute: it would answer a different question under this name."""
        self.harness("base", "raise SystemExit(0)\n")
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.observe(_request(commands=["base"]), self.states, 30)
        self.assertIn("has not run the combined state", str(caught.exception))

    def test_a_harness_that_rewrites_itself_refuses(self):
        """What was measured and what is carried must be the same bytes. A
        harness read only AFTER its own run could report one identity and hand
        the base a different test."""
        self.harness("combined", "open('harness.py','w').write('x=1\\n')\n")
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.observe(_request(commands=["combined", "base"]),
                         self.states, 30)
        self.assertIn("rewrote itself", str(caught.exception))

    def test_the_report_names_the_harness_it_actually_pinned(self):
        for name in task.CAUSAL_ORDER:
            self.harness(name, "raise SystemExit(0)\n")
        completed, not_run, tag, failed, pinned = task.observe(
            _request(), self.states, 30)
        report = task.compose_report(_request(), self.states, completed,
                                     not_run, tag, failed, pinned)
        self.assertTrue(report["harness_measured_digest"]
                        .startswith("sha256:"))
        # The REQUESTED digest is echoed; the MEASURED one is observed. They
        # are different facts and this report does not conflate them.
        self.assertNotEqual(report["harness_measured_digest"],
                            report["harness_digest"])

    def test_a_command_this_workload_does_not_run_is_refused(self):
        self.harness("combined", "raise SystemExit(0)\n")
        with self.assertRaises(task.PreparationRefusal) as caught:
            task.observe(_request(commands=["combined", "publish"]),
                         self.states, 30)
        self.assertIn("this workload runs", str(caught.exception))


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
