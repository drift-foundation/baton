"""The expired-credential failure path, from the run's own retained bytes.

Owner pass 242683: "Use retained failure bytes in deterministic regressions
through real manager/adapter boundaries. Require prompt actionable failure,
stopped execution and positive cleanup, without a proposal or false success."

WHAT THE RETAINED BYTES ARE. `live-242687/logs/provider.stdout.log` is the
EXACT stdout the production Claude CLI produced on the owner's run: one JSON
terminal record, `is_error: true`, `terminal_reason: "api_error"`,
`"Failed to authenticate: OAuth session expired and could not be refreshed"`,
`duration_ms: 31`. It is not a fixture anyone wrote to make a test pass, and
`TheRetainedBytesAreTheOnesTheRunProduced` pins it against the copy taken from
the run directory so a later edit is a failing test rather than a quiet drift.

WHAT IS REAL AROUND THEM. The adapter is `claude_agent.ClaudeAgent`, the
ending is `review_driver.end_implementation`, the composed stage is
`stage_execution`'s, the cleanup record is the manager's own journal, and the
supervisor is `baseline.supervise`. Only the provider subprocess and the engine
are substituted -- the two accepted seams -- and the provider is substituted by
replaying these bytes, which is the whole point.

WHAT THE RUN DID BEFORE THE CORRECTION, reproduced here first and asserted
after: the stage sat in `answering` for the full 900-second bound and never
committed cleanup, because the ending published unconditionally and
`integration.retain_proposal` refuses a result that is not `completed`. See
`DIAGNOSIS-242687.md` and the claim-242687 FINDING entry.
"""
import hashlib
import json
from pathlib import Path
import unittest

from tests.job_manager import fixtures

import baseline
from test_baseline import BaselineCase

HERE = Path(__file__).resolve().parent
RETAINED = HERE / "live-242687" / "logs" / "provider.stdout.log"
TERMINAL = HERE / "live-242687" / "events" / "terminal.json"
OUTCOME = HERE / "live-242687" / "outcome.json"
# The bytes the production CLI wrote, pinned. A later edit to the evidence is a
# failing test rather than a quiet drift in what this regression is about.
RETAINED_SHA256 = "87783dd7eaf890b38f4c9f2af74b4f5eb0fee12b29b92fcb6dcb5e14f16b5e33"


class ExpiredCredentialCase(BaselineCase):
    """One implementation turn whose provider answers the retained failure."""

    def setUp(self):
        super().setUp()
        # THE PROVIDER'S OWN ANSWER, REPLAYED. `ServingContextCase.provider`
        # prints `model_output` as the terminal record when it is set, so the
        # adapter reads exactly the bytes the production CLI wrote.
        self.model_output = RETAINED.read_text(encoding="utf-8").strip()

    def failing(self, job, control, composed):
        """The turn, with the provider's own non-zero exit.

        `status=1` is the CLI's: a turn whose terminal says `is_error` did not
        exit 0. `expect=None` because the ADAPTER's answer is the subject --
        it answers `unable` rather than raising, and that is correct.
        """
        def wait(seconds):
            del seconds
            if self.states(job, composed).get("implementation") != "waiting":
                return None
            attempt = self.pending(composed, "implementation")
            if attempt is None:
                return None
            self.turned.add(attempt)
            return self.turn(control, "implementation", attempt,
                             self.mounted(composed, "implementation", attempt),
                             edits={}, status=1)
        return wait

    def supervised_failure(self, **overrides):
        packet = dict(self.packet, **overrides) if overrides else self.packet
        job, control, composed = self.serving(packet=packet)
        ticks = iter(range(0, 100000))
        outcome = baseline.supervise(
            job, control, composed, packet, clock=lambda: fixtures.NOW,
            sleep=self.failing(job, control, composed),
            monotonic=lambda: float(next(ticks)))
        return outcome, job, control, composed


class TheRetainedBytesAreTheOnesTheRunProduced(unittest.TestCase):
    """The evidence, pinned. A regression over bytes nobody can check is a
    regression over whatever the file says today."""

    def test_the_provider_terminal_is_the_authentication_failure(self):
        body = json.loads(RETAINED.read_text(encoding="utf-8"))
        self.assertIs(body["is_error"], True)
        self.assertEqual(body["terminal_reason"], "api_error")
        self.assertEqual(
            body["result"],
            "Failed to authenticate: OAuth session expired and could not be "
            "refreshed")
        # THIRTY-ONE MILLISECONDS, which is the number that makes the
        # 900-second report a defect rather than a slow path.
        self.assertEqual(body["duration_ms"], 31)
        self.assertEqual(hashlib.sha256(RETAINED.read_bytes()).hexdigest(),
                         RETAINED_SHA256)

    def test_the_adapter_answered_unable_with_a_manifest(self):
        """The adapter was RIGHT. It is not what this correction changes."""
        terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        self.assertEqual(terminal["ending"], "answered")
        self.assertEqual(terminal["disposition"], "unable")
        self.assertIsNone(terminal["fault_code"])
        self.assertTrue(terminal["manifest_digest"].startswith("sha256:"))

    def test_the_live_outcome_recorded_the_stall_this_corrects(self):
        outcome = json.loads(OUTCOME.read_text(encoding="utf-8"))
        self.assertEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "answering"})
        self.assertEqual(outcome["outstanding_cleanup"],
                         outcome["admitted_attempts"])
        self.assertGreater(outcome["served_seconds"], 900)
        self.assertEqual(outcome["cleanup_sweeps"], 55)


class AnUnableTurnFailsPromptlyAndCleansUp(ExpiredCredentialCase):
    """The four things owner pass 242683 requires, each its own check."""

    def test_the_run_stops_as_soon_as_the_stage_is_exceptional(self):
        """PROMPT. The bound is 900; this must not go near it.

        `monotonic` is a tick counter here, so the assertion is on TICKS of
        the serving loop rather than on wall clock -- which is the honest
        measurement: before the correction this ran to 901 and stopped on the
        bound, and the loop is what was spinning.
        """
        outcome, _job, _control, _composed = self.supervised_failure()
        self.assertEqual(outcome["stopped"], "exceptional")
        self.assertLess(outcome["served_seconds"], 10,
                        "the run should end when the stage does, not when the "
                        "bound elapses")
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "exceptional"})

    def test_execution_is_stopped_and_cleanup_is_positive(self):
        """STOPPED, and POSITIVELY CLEANED UP -- a committed record, not an
        observation that the container went quiet."""
        outcome, _job, _control, _composed = self.supervised_failure()
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(len(outcome["cleanup"]), 1)
        for attempt, held in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                self.assertIn(held["cleanup"], baseline.POSITIVE_CLEANUP)
                self.assertEqual(held["state"], "absent")

    def test_no_proposal_is_retained_and_nothing_reads_as_success(self):
        """NO PROPOSAL AND NO FALSE SUCCESS."""
        outcome, _job, _control, _composed = self.supervised_failure()
        self.assertEqual(outcome["state"], "held")
        self.assertEqual(outcome["workload"]["proposals"], [])
        self.assertEqual(outcome["workload"]["attribution"], [])
        self.assertNotEqual(outcome["stopped"], "completed")

    def test_the_failure_is_actionable_rather_than_a_keyerror(self):
        """ACTIONABLE. The live run reported `KeyError: 'baton.git-proposal/1'`
        -- this program's own lookup -- where an operator needed to be told the
        provider turn did not complete."""
        outcome, _job, _control, _composed = self.supervised_failure()
        shortfalls = outcome["workload"]["shortfalls"]
        self.assertTrue(any("ended 'unable'" in one for one in shortfalls),
                        shortfalls)
        self.assertTrue(
            any("retained provider log" in one for one in shortfalls),
            shortfalls)
        for one in shortfalls:
            with self.subTest(shortfall=one):
                self.assertNotIn("KeyError", one)
        # AND THE MANAGER'S OWN WORD FOR IT, machine-readable.
        self.assertEqual(
            [one["disposition"]
             for one in outcome["workload"]["dispositions"]], ["unable"])

    def test_the_provider_was_called_once_and_never_retried(self):
        outcome, _job, _control, _composed = self.supervised_failure()
        calls = [json.loads(line)
                 for line in self.calls.read_text().splitlines()]
        self.assertEqual(len(calls), 1)
        self.assertEqual(outcome["admissions"], {"implementation": 1})
        self.assertEqual(outcome["retry"], False)

    def test_the_context_generation_is_not_finalized(self):
        """A generation whose turn could not be accounted for is HELD.

        This is the half of the old behaviour that was always right, and the
        correction deliberately keeps it: the stage settles, the context use
        does not become `ready`.
        """
        from baton_v12.worker_manager import provider_context as context

        outcome, _job, control, _composed = self.supervised_failure()
        attempt = outcome["admitted_attempts"][0]
        self.assertNotEqual(
            context.context_use_of(control, attempt)["status"], "ready")

    def test_the_outcome_is_retained_where_the_packet_says(self):
        outcome, _job, _control, _composed = self.supervised_failure()
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained, outcome)


def load_tests(loader, tests, pattern):
    """THIS FILE'S OWN CHECKS, and not the ones it inherits."""
    del tests, pattern, loader
    suite = unittest.TestSuite()
    for case in (TheRetainedBytesAreTheOnesTheRunProduced,
                 AnUnableTurnFailsPromptlyAndCleansUp):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite
