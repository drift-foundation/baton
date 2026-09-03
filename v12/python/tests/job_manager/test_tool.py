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


class Reading(ToolCase):

    def test_status_without_a_control_store_reports_nobody_looked(self):
        self.run_tool("--store", self.job_path, "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--incarnation", "jobs-1", "status")
        self.assertFalse(answer["canonical"])
        self.assertEqual(answer["schema"], "baton.v12.job-status/1")
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


if __name__ == "__main__":
    unittest.main()
