"""W71875 — the one entry point, and the loop it drives.

THE COMMAND LINE IS THE DOCUMENTED SUBMISSION SURFACE, so these cases drive
`tools/job_manager.py` the way an operator would: a JSON document in, a
versioned document out, and the same answer whether the caller used the tool
or called the package.

THE LOOP'S WAITING AND STOPPING ARE INJECTED, which is what makes a long-lived
process testable at all. `serve` is driven here with a counting predicate and
a recording sleep, so the cases measure the ORDER -- recover once, then sweep
until told to stop -- rather than waiting for wall time to pass.
"""

import io
import json
import os
import sys
import unittest

# THE DISTRIBUTION ROOT, NAMED FROM THIS FILE. `tools` is repository tooling
# rather than part of the wheel, so it is importable only when the
# distribution root is on `sys.path` -- which the canonical gate arranges with
# `-t .` and this Work's focused vector, rooted at the test directory, does
# not. `tests/tools/test_dogfood_operator.py` reaches its command exactly this
# way.
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import ContractRefusal                 # noqa: E402
from baton_v12.job_manager import TICK_SECONDS, serve, submit   # noqa: E402

from tools.job_manager import main                              # noqa: E402

if __package__:
    from .fixtures import (LATER, NOW, FakeOperations, JobManagerCase, job,
                           submission)
else:
    from fixtures import (LATER, NOW, FakeOperations, JobManagerCase, job,
                          submission)


class ToolCase(JobManagerCase):

    def run_tool(self, *argv):
        stream = io.StringIO()
        code = main(list(argv), clock=self.clock, stream=stream)
        self.assertEqual(code, 0)
        return json.loads(stream.getvalue())

    def document(self, value=None):
        path = os.path.join(self.root, "submission.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value if value is not None else submission(), handle)
        return path


class Submitting(ToolCase):

    def test_submitting_a_document_records_the_pipeline(self):
        answer = self.run_tool("--store", self.job_path,
                               "--incarnation", "jobs-1",
                               "submit", "--document", self.document())
        self.assertEqual(answer["submission_id"], "sub-1")
        self.assertEqual(answer["stages"],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])

    def test_resubmitting_through_the_tool_replays(self):
        first = self.run_tool("--store", self.job_path,
                              "--incarnation", "jobs-1",
                              "submit", "--document", self.document())
        self.instants.append(LATER)
        second = self.run_tool("--store", self.job_path,
                               "--incarnation", "jobs-2",
                               "submit", "--document", self.document())
        self.assertEqual(first, second)

    def test_an_invalid_document_refuses_rather_than_recording_half(self):
        path = self.document(submission(jobs=[job(terminal_policy="auto")]))
        with self.assertRaises(ContractRefusal):
            self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                          "submit", "--document", path)

    def test_a_store_path_is_required_rather_than_defaulted(self):
        import contextlib

        # `argparse` prints its own usage; the case is about the exit, so the
        # usage is captured rather than left in the suite's output.
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["submit", "--document", self.document()],
                     clock=self.clock, stream=io.StringIO())


# W85500: THE TWO OBSERVATION FACTORIES these cases name by module:attribute.
#
# Module level, because the tool RESOLVES the operand by import and nothing is
# searched for -- a factory reachable only from inside a test method would not
# be reachable the way the real one is.
_OBSERVING = {"closed": 0, "asked": []}


class _Observer:
    """The one member an observation factory owes, and one extra it must not
    be able to hand on."""

    def __init__(self, refusal=None):
        self._refusal = refusal

    def observe_exchange(self, stage):
        _OBSERVING["asked"].append(stage["stage_id"])
        if self._refusal is not None:
            return {"transport": "baton.worker-exchange/1",
                    "sequence_id": None, "command": None, "receipt": None,
                    "states": [], "terminal": None, "foreign": [],
                    "state": "unreadable",
                    "unreadable": {"category": "refused",
                                   "code": self._refusal}}
        return {"transport": "baton.worker-exchange/1",
                "sequence_id": "sequence-" + stage["attempt_id"],
                "command": {"published": True}, "receipt": {"seen": True},
                "states": [], "foreign": [], "state": "faulted",
                "terminal": {"ending": "faulted", "fault_code": "output",
                             "disposition": None, "manifest_digest": None}}

    def conclude(self, stage, job):
        """DELIBERATELY PRESENT. `_Observing` must not hand this on."""
        raise AssertionError("an observation surface reached an ending")

    def close(self):
        _OBSERVING["closed"] += 1


def observing(job_store, control_store):
    del job_store, control_store
    _OBSERVING.update(closed=0, asked=[])
    return _Observer()


def refusing(job_store, control_store):
    del job_store, control_store
    _OBSERVING.update(closed=0, asked=[])
    return _Observer(refusal="precondition")


class Reading(ToolCase):

    def test_status_without_a_control_store_reports_nobody_looked(self):
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--incarnation", "jobs-1", "status")
        self.assertFalse(answer["canonical"])
        self.assertEqual(answer["schema"], "baton.v12.job-status/3")
        self.assertEqual([one["job_id"] for one in answer["jobs"]],
                         ["job-a", "job-b"])

    def test_status_with_a_control_store_observes_it(self):
        self.control().close()
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--incarnation", "jobs-1", "status",
                               "--control", self.control_path)
        self.assertTrue(answer["canonical"])
        self.assertEqual(answer["jobs"][0]["stages"][0]["state"], "queued")

    # -- W85500: the observation-only status branch --------------------------

    def test_status_without_the_operand_still_reports_nobody_looked(self):
        """THE DEFAULT IS UNCHANGED and that is the whole compatibility half.

        W81857 ruled that the standalone read-only status always reports
        `exchange: null` because it has no deployment factory. W85500
        supersedes only the narrowness of that -- it does not make looking the
        default -- so a status run with no `--observe` answers exactly what it
        answered before.
        """
        self.control().close()
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--incarnation", "jobs-1", "status",
                               "--control", self.control_path)
        for job in answer["jobs"]:
            for stage in job["stages"]:
                self.assertIsNone(stage["exchange"])

    def test_the_operand_is_resolved_asked_and_then_released(self):
        """The wiring, end to end through the real tool.

        WHAT THIS DELIBERATELY DOES NOT ASSERT is the exchange appearing in the
        document. `delegation._bound` drops every attempt-keyed observation for
        a stage whose attempt no claim binds to it -- correctly, because an
        unclaimed attempt has nothing to say about this stage -- and these
        stages are submitted and never claimed. The exchange REACHING a status
        document is proved where a real claim exists, in
        `tests.tools.test_single_worker`, against a real faulted terminal.
        """
        self.control().close()
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool(
            "--store", self.job_path, "--incarnation", "jobs-1", "status",
            "--control", self.control_path,
            "--observe", "tests.job_manager.test_tool:observing")
        self.assertTrue(answer["canonical"])
        self.assertEqual(answer["schema"], "baton.v12.job-status/3")
        self.assertEqual([one["job_id"] for one in answer["jobs"]],
                         ["job-a", "job-b"])
        # THE READER WAS ASKED FOR EVERY STAGE, which is what the projection
        # does with an exchange read it has been given.
        self.assertEqual(sorted(_OBSERVING["asked"]),
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])
        # AND THE FACTORY WAS GIVEN BACK WHAT IT OPENED, exactly once.
        self.assertEqual(_OBSERVING["closed"], 1)

    def test_the_observation_surface_carries_no_act_and_no_refresh(self):
        """The composition, not the factory's promise about itself.

        `_Observing` takes ONE member by name from whatever the factory
        answers. A factory carrying a dispatch or an ending hands neither of
        them on, and the refresh is absent because refreshing RECORDS -- a
        status that recorded would be a read that mutates.
        """
        from tools.job_manager import _Observing

        self.control().close()
        control = self.control(incarnation="manager-obs")
        surface = _Observing(control, _Observer())
        for act in ("admit", "claim", "launch", "dispatch", "conclude",
                    "recover", "attach", "drain"):
            self.assertFalse(hasattr(surface, act), act)
        self.assertIsNone(surface.refresh_runtime({"attempt_id": "a"}))

    def test_a_factory_that_cannot_read_the_exchange_is_refused_by_name(self):
        self.control().close()
        control = self.control(incarnation="manager-bare")
        from tools.job_manager import _Observing

        with self.assertRaises(SystemExit) as caught:
            _Observing(control, object())
        self.assertIn("observe_exchange", str(caught.exception))

    def test_an_operand_that_is_not_module_attribute_is_refused(self):
        self.control().close()
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        with self.assertRaises(SystemExit) as caught:
            self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                          "status", "--control", self.control_path,
                          "--observe", "not-a-factory")
        self.assertIn("module:attribute", str(caught.exception))

    def test_a_refusing_exchange_read_still_produces_a_status_document(self):
        """One damaged launch root must not stop a status run from reporting
        anything at all, which is this Work's own defect in miniature.

        The real reader answers an `unreadable` observation rather than
        raising, and this proves the tool carries that all the way to a
        document instead of exiting.
        """
        self.control().close()
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool(
            "--store", self.job_path, "--incarnation", "jobs-1", "status",
            "--control", self.control_path,
            "--observe", "tests.job_manager.test_tool:refusing")
        self.assertTrue(answer["canonical"])
        self.assertEqual(len(answer["jobs"]), 2)
        self.assertEqual(sorted(_OBSERVING["asked"]),
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])

    def test_observe_without_a_control_store_is_refused_not_ignored(self):
        """W85500 review 2026-09-04T14-27-54Z [P1].

        `_status` answered `Unobserved()` before it looked at the operand, so
        an operator who ASKED for observation got a successful run, `exchange:
        null`, and no indication the request had not been performed -- which is
        the same shape as the defect this Work exists to correct.
        """
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        # THE MODULE-LEVEL RECORD IS CLEARED HERE, because it is shared by
        # every case that resolves a factory and this one asserts an ABSENCE.
        _OBSERVING.update(closed=0, asked=[])
        with self.assertRaises(SystemExit) as caught:
            self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                          "status",
                          "--observe", "tests.job_manager.test_tool:observing")
        self.assertIn("--control", str(caught.exception))
        # AND THE FACTORY WAS NEVER RESOLVED, so the refusal is about the
        # operand combination rather than about anything the factory did.
        self.assertEqual(_OBSERVING["asked"], [])

    def test_the_status_surface_holds_no_authority_capability(self):
        from tools.job_manager import _ReadOnly

        self.control().close()
        control = self.control(incarnation="manager-2")
        surface = _ReadOnly(control)
        self.assertFalse(hasattr(surface, "admit"))
        self.assertFalse(hasattr(surface, "claim"))
        self.assertFalse(hasattr(surface, "recover"))

    def test_the_tool_and_the_package_answer_the_same_document(self):
        from baton_v12.job_manager import Unobserved, status

        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        through_tool = self.run_tool("--store", self.job_path,
                                     "--incarnation", "jobs-1", "status")
        store = self.store()
        self.assertEqual(through_tool,
                         status(store, Unobserved(), observed_at=NOW))


class TheLoop(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        self.waited = []

    def continues(self, times):
        remaining = [times]

        def answer():
            remaining[0] -= 1
            return remaining[0] >= 0

        return answer

    def test_the_loop_recovers_once_and_then_sweeps(self):
        serve(self.jobs, self.acts, clock=self.clock,
              sleep=self.waited.append, should_continue=self.continues(2),
              interval=1)
        self.assertEqual([call for call in self.acts.calls
                          if call[0] == "recover"], [("recover", NOW)])
        self.assertEqual(self.waited, [1, 1])

    def test_the_loop_answers_the_last_report(self):
        report = serve(self.jobs, self.acts, clock=self.clock,
                       sleep=self.waited.append,
                       should_continue=self.continues(1), interval=2)
        self.assertEqual(report["observed_at"], NOW)
        # The recovery belongs to the resume, not to the ordinary tick that
        # answered.
        self.assertIsNone(report["recovered"])
        self.assertEqual(self.waited, [2])

    def test_a_loop_that_never_ticks_still_reconciles(self):
        report = serve(self.jobs, self.acts, clock=self.clock,
                       sleep=self.waited.append,
                       should_continue=self.continues(0))
        self.assertIsNotNone(report["recovered"])
        self.assertEqual(self.waited, [])
        self.assertEqual([one["outcome"] for one in report["acts"]],
                         ["performed"])

    def test_the_wait_and_the_stop_condition_are_capabilities(self):
        for operands in ({"sleep": None}, {"should_continue": "stop"},
                         {"clock": 7}):
            held = {"clock": self.clock, "sleep": self.waited.append,
                    "should_continue": self.continues(0)}
            held.update(operands)
            with self.assertRaises(ContractRefusal):
                serve(self.jobs, self.acts, **held)

    def test_an_interval_that_is_not_a_positive_whole_number_refuses(self):
        for interval in (0, -1, 1.5, "5"):
            with self.subTest(interval=interval):
                with self.assertRaises(ContractRefusal):
                    serve(self.jobs, self.acts, clock=self.clock,
                          sleep=self.waited.append,
                          should_continue=self.continues(0),
                          interval=interval)

    def test_the_default_tick_is_stated_rather_than_hidden(self):
        self.assertEqual(TICK_SECONDS, 5)


# W76207: the factory this module's release cases import by `module:attribute`,
# exactly as an operator names a production one.
_ACQUIRED = []


class _Released:
    """An operations object that records having been released."""

    canonical = False

    def __init__(self, name):
        self.name = name
        _ACQUIRED.append(name)

    def close(self):
        _ACQUIRED.remove(self.name)


def releasing_factory(store, control):
    return _Released("operations")


def failing_factory(store, control):
    """A factory that acquires one handle and THEN fails.

    The shape review [P1] named: an Authority opened, and a refusal on the next
    operand. Its own partial acquisition is its to clean up, and it does -- the
    tool never saw it.
    """
    held = _Released("half-built")
    try:
        raise ContractRefusal("integrity", "schema",
                              "the configured image digest is not a digest")
    except BaseException:
        held.close()
        raise


def leaking_factory(store, control):
    """The same, WITHOUT cleaning up after itself.

    Kept so the boundary this tool can and cannot hold is a measured fact
    rather than a claim: the handle stays acquired, and the tool is not what
    lost it.
    """
    _Released("leaked")
    raise ContractRefusal("integrity", "schema", "and nothing was released")


class TheFactoryHandleIsReleased(ToolCase):
    """Review [P1]: construction now happens INSIDE the release boundary.

    The earlier version called the factory in front of the `try`, so an object
    it returned was released but a factory that failed mid-construction left
    nothing for the tool to close -- while a comment and PROGRESS.md both
    claimed construction-failure cleanup the code did not provide.
    """

    def setUp(self):
        super().setUp()
        _ACQUIRED.clear()
        store = self.store()
        submit(store, submission(jobs=[job("job-a")]))
        store.close()

    def serve_with(self, attribute):
        return self.run_tool(
            "--store", self.job_path, "--incarnation", "jobs-1", "serve",
            "--control", self.control_path, "--once",
            # THIS MODULE, BY THE NAME IT IS ACTUALLY RUNNING UNDER. Naming
            # it literally imported a SECOND copy under discovery -- the
            # package path and the top-level path are two module objects with
            # two `_ACQUIRED` lists, so the case observed the wrong one.
            "--operations", f"{__name__}:{attribute}")

    def test_a_returned_operations_object_is_always_released(self):
        with self.assertRaises(Exception):
            # `_Released` refuses every act, so the run fails -- which is the
            # point: the release must happen however the block is left.
            self.serve_with("releasing_factory")
        self.assertEqual(_ACQUIRED, [])

    def test_a_factory_that_cleans_up_its_own_failure_leaves_nothing_held(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.serve_with("failing_factory")
        self.assertIn("not a digest", caught.exception.message)
        self.assertEqual(_ACQUIRED, [],
                         "the factory released what it had taken")

    def test_a_factory_that_leaks_is_not_hidden_by_this_tool(self):
        """The honest limit, measured rather than promised.

        Nothing here ever saw the leaked handle, so the tool cannot close it.
        The original failure still reaches the operator unchanged, which is
        the property that matters: a cleanup problem must not replace the
        refusal that caused it.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.serve_with("leaking_factory")
        self.assertIn("nothing was released", caught.exception.message)
        self.assertEqual(_ACQUIRED, ["leaked"])


if __name__ == "__main__":
    unittest.main()
