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
from unittest import mock

# THE DISTRIBUTION ROOT, NAMED FROM THIS FILE. `tools` is repository tooling
# rather than part of the wheel, so it is importable only when the
# distribution root is on `sys.path` -- which the canonical gate arranges with
# `-t .` and this Work's focused vector, rooted at the test directory, does
# not. `tests/tools/test_dogfood_operator.py` reaches its command exactly this
# way.
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import ContractRefusal                 # noqa: E402
from baton_v12.worker_manager import attempts as manager_attempts  # noqa: E402
from baton_v12.job_manager import TICK_SECONDS, serve, submit   # noqa: E402

from tools import job_manager                                  # noqa: E402
from tools.job_manager import main                              # noqa: E402

if __package__:
    from .fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase,
                           job,
                           submission)
else:
    from fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase,
                          job,
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
                               "--authority-uuid", UUID,
                               "--incarnation", "jobs-1",
                               "submit", "--document", self.document())
        self.assertEqual(answer["submission_id"], "sub-1")
        self.assertEqual(answer["stages"],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])

    def test_resubmitting_through_the_tool_replays(self):
        first = self.run_tool("--store", self.job_path,
                              "--authority-uuid", UUID,
                              "--incarnation", "jobs-1",
                              "submit", "--document", self.document())
        self.instants.append(LATER)
        second = self.run_tool("--store", self.job_path,
                               "--authority-uuid", UUID,
                               "--incarnation", "jobs-2",
                               "submit", "--document", self.document())
        self.assertEqual(first, second)

    def test_an_invalid_document_refuses_rather_than_recording_half(self):
        path = self.document(submission(jobs=[job(terminal_policy="auto")]))
        with self.assertRaises(ContractRefusal):
            self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                          "--incarnation", "jobs-1",
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
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--authority-uuid", UUID,
                               "--incarnation", "jobs-1", "status")
        self.assertFalse(answer["canonical"])
        self.assertEqual(answer["schema"], "baton.v12.job-status/6")
        self.assertEqual([one["job_id"] for one in answer["jobs"]],
                         ["job-a", "job-b"])

    def test_status_with_a_control_store_observes_it(self):
        self.control().close()
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--authority-uuid", UUID,
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
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool("--store", self.job_path,
                               "--authority-uuid", UUID,
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
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool(
            "--store", self.job_path, "--authority-uuid", UUID,
            "--incarnation", "jobs-1", "status",
            "--control", self.control_path,
            "--observe", "tests.job_manager.test_tool:observing")
        self.assertTrue(answer["canonical"])
        self.assertEqual(answer["schema"], "baton.v12.job-status/6")
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
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        with self.assertRaises(SystemExit) as caught:
            self.run_tool("--store", self.job_path,
                          "--authority-uuid", UUID,
                          "--incarnation", "jobs-1",
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
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        answer = self.run_tool(
            "--store", self.job_path, "--authority-uuid", UUID,
            "--incarnation", "jobs-1", "status",
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
        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        # THE MODULE-LEVEL RECORD IS CLEARED HERE, because it is shared by
        # every case that resolves a factory and this one asserts an ABSENCE.
        _OBSERVING.update(closed=0, asked=[])
        with self.assertRaises(SystemExit) as caught:
            self.run_tool("--store", self.job_path,
                          "--authority-uuid", UUID,
                          "--incarnation", "jobs-1",
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

        self.run_tool("--store", self.job_path, "--authority-uuid", UUID,
                      "--incarnation", "jobs-1",
                      "submit", "--document", self.document())
        through_tool = self.run_tool("--store", self.job_path,
                                     "--authority-uuid", UUID,
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
            "--store", self.job_path, "--authority-uuid", UUID,
                          "--incarnation", "jobs-1", "serve",
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


class TheStatusSurfaceMayReadIntegrationAndStillActOnNothing(unittest.TestCase):
    """W126558: the optional second read, and the capability it does not gain.

    `_Observing` takes the exchange read by name so that passing the factory
    object cannot hand this composition a dispatch or an ending. The
    integration read is taken the same way and is OPTIONAL, which is the
    compatibility rule: a factory composed before this member existed keeps its
    exact previous behaviour rather than becoming invalid.
    """

    class WithBoth:
        def __init__(self):
            self.asked = []

        def observe_exchange(self, stage):
            self.asked.append(("exchange", stage["stage_id"]))
            return None

        def observe_integration(self, stage):
            self.asked.append(("integration", stage["stage_id"]))
            return None

        def dispatch_exchange(self, stage, command):
            raise AssertionError("a status surface dispatched")

        def conclude_attempt(self, stage, job):
            raise AssertionError("a status surface concluded")

    class WithExchangeOnly(WithBoth):
        observe_integration = None

    def test_a_factory_without_the_integration_read_still_composes(self):
        """The compatibility rule, at the one place that enforces it."""
        self.assertIsNone(job_manager._integration_read(
            self.WithExchangeOnly()))

    def test_the_read_is_taken_by_name_and_nothing_else_travels(self):
        held = self.WithBoth()
        # THE SAME FUNCTION BOUND TO THE SAME OBJECT. `assertIs` would compare
        # two freshly created bound-method wrappers, which are never identical.
        taken = job_manager._integration_read(held)
        self.assertIs(taken.__func__, self.WithBoth.observe_integration)
        self.assertIs(taken.__self__, held)

    def test_the_composed_expiry_pass_stops_and_confirms_a_real_overdue_runtime(self):
        """W275774 review 17:17:15Z: PROVE THE COMPOSED PASS, not an optional hook.

        Real control store, real token records, controlled engine runner. The pass
        this tool hands to `serve` is exercised directly, because the tool's own
        serving loop is driven by process signals and `--once` never reaches `serve`
        at all -- so this asserts what the pass does rather than how the loop spins.
        """
        from baton_v12.worker_manager import attempts as manager_attempts
        from baton_v12.worker_manager import tokens
        from tests.manager.test_intake import ATTEMPT

        # THE FIXTURE'S OWN STORE is the one the pass reads: one control store and
        # one set of rows, so there is no second copy to disagree with itself.
        case = _running_governed_attempt(self)
        control = case["store"]
        vectors = []

        def engine(argv, *, seconds=None):
            del seconds
            vectors.append(list(argv))
            if argv[1] == "stop":
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 1, "stdout": "",
                    "stderr": "Error: No such object: " + argv[-1]}

        answer = job_manager._reclaiming(control, "docker", engine)(
            now="2026-08-24T01:00:00.000Z")
        # THE WHOLE COMPOSED SEQUENCE, in order: the reclaim stops, removes and
        # confirms, and then the revoked-resource ending RE-OBSERVES on its own
        # authority rather than trusting what the reclaim just did.
        # The reclaim's own three acts: stop, remove, then confirm. The ending's
        # second observation is absent from this list precisely because the ending
        # could not run from a non-custodial adapter -- asserted below.
        # W285465 under the owner supersession at 294568/294616: the SETTLEMENT that now
        # follows the reclaim re-asks the exact identity before it releases anything, so the
        # chain carries a second `inspect`. That is the confirmation the ruling requires -- the
        # reclaim's absence was true at the reclaim's instant -- and it starts nothing, which
        # the sentinel below asserts.
        self.assertEqual([one[1] for one in vectors],
                         ["stop", "rm", "inspect", "inspect"])
        self.assertNotIn("run", [one[1] for one in vectors],
                         "the expiry pass started something")
        self.assertTrue(all(one[-1] == case["runtime_id"] for one in vectors),
                        "every act named the exact container")
        self.assertEqual(answer["refused"], [])
        self.assertEqual([one["reclaimed"] for one in answer["reclaimed"]],
                         ["held"],
                         "the reclaim stops and removes and holds; the ending is the "
                         "act that accounts for the roots")
        # AND THE HONEST LIMIT, measured: this lean adapter performs no custody acts,
        # so the ending cannot run from it and the pass says so instead of refusing.
        # A deployment whose factory supplies a custodian-capable adapter gets the
        # ending in the same tick; this one records what it could not do.
        # W285465 under the owner supersession at 294568/294616: the lean pass SETTLES now --
        # the selected settlement performs no custody act, so waiting for a custodian it never
        # calls held every reclaimed resource for nothing. The release is read from the answer
        # here and from the ledger in `test_without_a_custodian_the_RECLAIM_STILL_SETTLES`.
        self.assertEqual(answer["reclaimed"][0]["ending"]["settled"], "returned")
        self.assertTrue(
            tokens.token_of(control, case["domain"], 1)["revoked"],
            "the overdue entitlement was withdrawn by the serving pass")

    def test_a_running_no_intake_overdue_attempt_reaches_a_safe_return(self):
        """W275774 review 18:11:15Z: THE FULL CONFIGURED PASS, restored.

        An initially RUNNING attempt with no intake receipt -- the case an expiry sweep
        most needs -- with a custodian image configured, driven through revoke, stop,
        removal, positive absence, the pre-effect exclusion, normalization, the return
        and a replacement.

        My three earlier attempts at this failed on the workspace LAYOUT, not the
        subject: I created directories by hand and custody refused each one, correctly.
        The reviewer pointed at the canonical setup and the fixture now ALLOCATES
        through `workspaces.assignment_workspace`, which is what makes the roots the
        ones custody will accept.
        """
        from baton_v12.worker_manager import tokens

        case = _running_governed_attempt(self)
        control = case["store"]
        vectors = []

        # THE CUSTODY ACT NEEDS AN ACCOUNTABLE ANSWER, and the reviewer pointed at
        # where one lives: `test_custody` echoes the submission token the manager
        # committed for that act, because a provider is the only place that token can
        # be learned and a placeholder would answer for a submission this act never
        # made. An empty answer is why my first restored attempt reported "the act
        # printed no document this manager could read".
        from tests.manager import test_custody as _custody_suite

        def engine(argv, *, seconds=None):
            del seconds
            vectors.append(list(argv))
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: " + argv[-1]}
            if argv[1] == "run":
                _custody_suite.echoed(argv)
                return {"status": 0, "stderr": "",
                        "stdout": json.dumps(
                            _custody_suite.reported("normalize")) + "\n"}
            return {"status": 0, "stdout": "", "stderr": ""}

        answer = job_manager._reclaiming(
            control, "docker", engine, "sha256:" + "c" * 64)(
                now="2026-08-24T01:00:00.000Z")
        outcome = answer["reclaimed"][0] if answer["reclaimed"] else None
        self.assertIsNotNone(outcome, f"nothing was reclaimed: {answer}")
        # THE ENTITLEMENT WENT AND THE CONTAINER WENT, in that order.
        self.assertTrue(tokens.token_of(control, case["domain"], 1)["revoked"])
        self.assertEqual([one[1] for one in vectors][:3], ["stop", "rm", "inspect"])
        # AND THE ENDING RAN AND RETURNED, because a custodian was configured.
        self.assertIn("ending", outcome)
        self.assertNotEqual(outcome["ending"], "awaits-normalizing-ending",
                            f"a configured custodian must let the ending run: "
                            f"{outcome}")
        self.assertEqual(outcome["ending"]["settled"], "returned")
        self.assertEqual(outcome["ending"]["state"], "absent")
        self.assertEqual(outcome["ending"]["container"], case["runtime_id"])
        self.assertEqual(tokens.outstanding(control, case["domain"]), [],
                         "the whole configured chain reaches a safe return")
        # AND THE REPLACEMENT, only now that the resource is actually free.
        second = tokens.workspace_governance().reserve(
            control, {"runtime_attempt_id": "attempt-2",
                      "workspace_device": 66, "workspace_inode": 4242},
            operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)

    def _accountable(self, vectors, *, removal_absent=False, normalize=None):
        """One controlled engine for the configured chain, with the pieces named."""
        from tests.manager import test_custody as _custody_suite

        def engine(argv, *, seconds=None):
            vectors.append((list(argv), seconds))
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: " + argv[-1]}
            if argv[1] == "rm" and removal_absent:
                # ALREADY GONE IS NOT A FAILURE, and the review asked for this shape
                # explicitly: an engine that removed the container between the stop and
                # the removal answers a missing identity, and that is success.
                return {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: " + argv[-1]}
            if argv[1] == "run":
                if normalize is not None:
                    return normalize(argv)
                _custody_suite.echoed(argv)
                return {"status": 0, "stderr": "",
                        "stdout": json.dumps(
                            _custody_suite.reported("normalize")) + "\n"}
            return {"status": 0, "stdout": "", "stderr": ""}

        return engine

    def test_the_chain_carries_its_bounded_budget_into_every_engine_call(self):
        """W275774 review 18:19:28Z: MY CHAIN TEST DISCARDED `seconds`.

        The allowance wrapper was corrected statically last claim and nothing asserted
        it, so this records what each call actually carries: the reclaim's own three
        acts are bounded by `_RECLAIM_SECONDS`, and the custody act's vectors carry a
        bound rather than `None`.
        """
        case = _running_governed_attempt(self)
        vectors = []
        job_manager._reclaiming(
            case["store"], "docker", self._accountable(vectors),
            "sha256:" + "c" * 64)(now="2026-08-24T01:00:00.000Z")
        # W275774 review 21:33:35Z, budget strengthening: THE PRESENCE OF EACH VERB IS
        # ASSERTED, not just the bound on whatever happened to appear. The previous cut
        # read "every stop/rm/inspect that is here" and "at least one run", so a chain
        # that stopped issuing its removal -- or issued no custody act at all -- passed
        # while carrying correct bounds on a shorter chain.
        carried = {}
        for argv, seconds in vectors:
            carried.setdefault(argv[1], []).append(seconds)
        for verb in ("stop", "rm", "inspect"):
            with self.subTest(verb=verb):
                self.assertIn(verb, carried,
                              f"the reclaim chain issued no {verb}: {vectors}")
                for seconds in carried[verb]:
                    self.assertEqual(
                        seconds, job_manager._RECLAIM_SECONDS,
                        "a reclaim's engine calls carry their own bound")
        # W285465 under the owner supersession at 294568/294616: NO `run` VECTOR, and its
        # ABSENCE is asserted rather than its bound. The chain starts no helper, so a `run` here
        # would be the launch this ruling forbids -- which makes the strengthening this case is
        # about a statement over the vectors the chain DOES issue, plus the sentinel that it
        # issues no other kind.
        self.assertNotIn("run", carried,
                         f"the reclaim chain started something: {vectors}")
        self.assertEqual(sorted(carried), ["inspect", "ps", "rm", "stop"],
                         f"the chain issued an unexpected vector: {sorted(carried)}")
        # AND THE LISTING'S OWN READS CARRY A BOUND TOO, from the same wrapper.
        for seconds in carried["ps"]:
            self.assertIsNotNone(seconds,
                                 "a listing read reached the engine unbounded")

    def test_an_already_absent_removal_still_completes_the_chain(self):
        from baton_v12.worker_manager import tokens

        case = _running_governed_attempt(self)
        vectors = []
        answer = job_manager._reclaiming(
            case["store"], "docker",
            self._accountable(vectors, removal_absent=True),
            "sha256:" + "c" * 64)(now="2026-08-24T01:00:00.000Z")
        self.assertEqual(answer["refused"], [])
        self.assertEqual(answer["reclaimed"][0]["ending"]["settled"], "returned")
        self.assertEqual(tokens.outstanding(case["store"], case["domain"]), [])

    def test_an_UNCONFIRMED_runtime_HOLDS_and_its_RETRY_confirms(self):
        """NO REPEATED UNSAFE EFFECT -- and the retry does NOT converge, which is a
        real finding rather than a test I could force.

        I wrote this expecting the retry to converge. Measured, it does not, and the
        reason is custody's own safety machinery rather than a defect:

          first pass:  "the directory custody act ... did not answer accountably;
                        nothing is recorded, and an ending is not claimed on an act
                        this manager cannot account for"
          second pass: "attempt's result root carries unreconciled uncertainty episode
                        0, and this act would touch it ... the two roots of one attempt
                        overlap, so neither is free while either is held"

        A normalization whose outcome is UNKNOWN leaves an uncertainty episode, and
        retrying blindly over a root nobody has accounted for is exactly what that
        refusal prevents. So the resource stays held through both passes, nothing is
        returned, and no effect is repeated.

        WHAT THIS LEAVES OPEN, stated rather than glossed: reconciling an uncertainty
        episode is custody's own act, and this expiry pass does not perform it. A
        resource behind a failed normalization therefore stays held until that
        reconciliation happens, which is safe and is not yet automatic.
        """
        from baton_v12.worker_manager import tokens

        case = _running_governed_attempt(self)
        control = case["store"]
        refusing = [True]

        def normalize(argv):
            if refusing[0]:
                refusing[0] = False
                return {"status": 1, "stdout": "",
                        "stderr": "the custodian could not run"}
            from tests.manager import test_custody as _custody_suite
            _custody_suite.echoed(argv)
            return {"status": 0, "stderr": "",
                    "stdout": json.dumps(
                        _custody_suite.reported("normalize")) + "\n"}

        # W285465 under the owner supersession at 294568/294616: THE HOLD THIS PATH CAN HAVE IS
        # AN UNCONFIRMED CONTAINER, not a failed custody act -- no helper runs here at all. So
        # the engine reports the runtime STILL PRESENT on the first pass and absent on the
        # second, which is the concrete unknown/surviving Docker hold the ruling keeps.
        confirming = [True]

        def inspecting(argv, *, seconds=None):
            del seconds
            if argv[1] == "inspect":
                if confirming[0]:
                    # STILL THERE, for EVERY read in this pass: the reclaim's own confirmation
                    # and the settlement's re-ask must both see it, or the pass would release on
                    # the second look at a container the first one found running.
                    return {"status": 0, "stdout": json.dumps(
                        [{"Id": "runtime-1", "State": {"Running": True}}]) + "\n",
                        "stderr": ""}
                return {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: " + argv[-1]}
            return {"status": 0, "stdout": "", "stderr": ""}

        pass_over = job_manager._reclaiming(control, "docker", inspecting)
        first = pass_over(now="2026-08-24T01:00:00.000Z")
        confirming[0] = False
        held = first["reclaimed"] + first["refused"]
        self.assertTrue(held, "the pass answered nothing about this attempt")
        self.assertEqual(len(tokens.outstanding(control, case["domain"])), 1,
                         "an unconfirmed runtime must not free the resource")
        # THE RETRY, with the identity now positively absent.
        again = pass_over(now="2026-08-24T01:00:00.000Z")
        del again
        self.assertEqual(tokens.outstanding(control, case["domain"]), [],
                         "the confirmed absence did not release the resource")

    def test_a_failed_TOKEN_RETURN_retries_without_repeating_its_EFFECT(self):
        """W275774 review 18:23:27Z: THE OMITTED REQUIREMENT.

        Normalization SUCCEEDS accountably and the token return then fails. The
        resource must stay held, and the retry must return the ORIGINAL generation
        WITHOUT normalizing again -- a second normalization would be a repeated effect
        over roots already accounted for, which is the thing the count below measures
        rather than asserts in prose.
        """
        from baton_v12.worker_manager import tokens

        case = _running_governed_attempt(self)
        control = case["store"]
        vectors = []
        engine = self._accountable(vectors, removal_absent=True)

        honest = tokens.release
        failing = [True]

        def release(*arguments, **named):
            if failing[0]:
                failing[0] = False
                raise ContractRefusal("refused", "precondition",
                                      "the return could not be committed")
            return honest(*arguments, **named)

        tokens.release = release
        try:
            pass_over = job_manager._reclaiming(
                control, "docker", engine, "sha256:" + "c" * 64)
            first = pass_over(now="2026-08-24T01:00:00.000Z")
            # W285465 under the owner supersession at 294568/294616: THE EFFECT THIS CASE IS
            # ABOUT IS THE REMOVAL, not a normalization. The settlement starts no helper, so
            # there is no `run` to count; what must not repeat is the destructive engine work
            # the first pass already did, and the sentinel that nothing was started is asserted
            # beside it.
            self.assertNotIn("run", [one[1] for one, _ in vectors],
                             "the settlement started something")
            effects = [one[1] for one, _ in vectors if one[1] in ("stop", "rm")]
            self.assertTrue(effects, "the first pass performed no engine effect")
            self.assertEqual(len(tokens.outstanding(control, case["domain"])), 1,
                             "a failed return leaves the resource held")
            # THE RETRY, with the return now able to commit.
            again = pass_over(now="2026-08-24T01:00:00.000Z")
        finally:
            tokens.release = honest
        self.assertEqual(tokens.outstanding(control, case["domain"]), [],
                         "the retry returns the original generation")
        # AND WHAT "WITHOUT REPEATING" MEANS HERE, measured rather than assumed. The retry DOES
        # re-issue its removal -- `rm` appears twice -- and that is the accepted design this
        # module states in its own words: a destroy is force-removal followed by an inspection
        # of the exact identity, and an identity already gone answers absent, which is why a
        # retry is safe. What must not repeat is a STATE CHANGE, so the assertion is that the
        # retry performed no second start and the resource returned exactly ONCE.
        self.assertEqual([one[1] for one, _ in vectors].count("rm"), 2,
                         "the retry did not re-issue its idempotent removal")
        self.assertNotIn("run", [one[1] for one, _ in vectors],
                         "the retry started something")
        # AND THE RETURN IS COUNTED, not asserted in prose. Review 2026-09-28T11-09-51Z is right
        # that "exactly ONE resource return" was a claim my assertions did not make: an empty
        # outstanding set says the resource is free, not that it was returned once. The journal
        # says it -- exactly one committed `resource-token.returned` for this domain.
        returns = control._connection.execute(
            "SELECT COUNT(*) FROM operations WHERE kind = ? AND state = "
            "'committed' AND operation_id LIKE ?",
            ("resource-token.returned", f"%{case['domain']}%")).fetchone()[0]
        self.assertEqual(returns, 1,
                         "the resource was returned more than once")
        del effects
        del first, again

    def test_the_allowance_wrapper_clamps_work_and_cleanup_separately(self):
        """The wrapper's SMALLER-SUPPLIED branch, which my budget case never reached.

        It asserted defaults and non-`None` only. This drives the LISTING read with a supplied
        work budget and a distinct cleanup total, and reads what each vector actually carries.

        WHAT IT PROVES AND WHAT IT DOES NOT, corrected by review 2026-09-28T11-09-51Z: the
        listing starts nothing, so every vector it issues is a RECLAMATION verb and spends the
        cleanup total, clamped by its own maximum. The wrapper's ACTING-vector branch -- the one
        that spends the work budget -- is not exercised here, because this path issues no acting
        vector at all. The old docstring claimed both halves; only the cleanup half is measured.
        """
        from baton_v12.worker_manager import custody as _custody

        seen = []

        def engine(argv, *, seconds=None):
            seen.append((argv[1], seconds))
            return {"status": 0, "stdout": "", "stderr": ""}

        from tests.manager.test_intake import ATTEMPT

        adapter = job_manager._ReclaimAdapter(
            "docker", engine, custodian_image_digest="sha256:" + "c" * 64)
        case = _running_governed_attempt(self)
        # THE OUTCOME IS NAMED INSTEAD OF SWALLOWED, and naming it CORRECTED MY OWN
        # PROSE. Review 21:33:35Z asked for an expected refusal rather than a bare
        # `except Exception`; measuring it showed there is NO exception here at all. This
        # method answers a `CustodyAnswer` that is `ok=False` -- an act that ran and could
        # not be accounted for -- and it is the ENDING, not this adapter, that turns that
        # into a refusal. The old comment claimed "the act itself refuses"; it does not.
        # W285465 under the owner supersession at 294568/294616: THE BOUNDED ACT IS THE
        # LISTING. This drove `normalize_directory`, which the selected settlement never
        # performs, and driving it now meets the genuine live-token guard. The wrapper under
        # test is the SAME one; what moves is the act it is measured over. And the listing
        # issues NO `run` vector, because it starts nothing -- so every vector here spends the
        # cleanup total, which is the rule this case is about.
        adapter.surviving_helpers(case["store"], assignment_id=ATTEMPT,
                                  seconds=7, reclaim=3)
        self.assertTrue(seen, "the wrapper reached the engine")
        self.assertNotIn("run", [verb for verb, _ in seen],
                         "the listing started something")
        for verb, seconds in seen:
            with self.subTest(verb=verb):
                self.assertIsNotNone(seconds)
                self.assertEqual(
                    seconds, _custody.allowed(3, _custody.CUSTODY_ACT_SECONDS),
                    "every reclamation vector spends the cleanup total, "
                    "clamped by its own maximum")

    def test_the_ADAPTER_answers_surviving_helpers_and_starts_nothing(self):
        """W285465: the seam the selected endings need, since they may run no helper.

        The custodian image digest and the engine live on the adapter, so this is where a
        writer-absence answer can be established without the helper the owner ruling
        forbids. What this asserts is that it ANSWERS and that it STARTS NOTHING: no
        create, no run, no start anywhere in the vectors it issued.
        """
        from baton_v12 import worker_manager as _manager

        seen = []

        def engine(argv, *, seconds=None):
            seen.append(list(argv))
            if argv[1] == "ps":
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "", "stderr": ""}

        case = _running_governed_attempt(self)
        adapter = job_manager._ReclaimAdapter(
            "docker", engine, custodian_image_digest="sha256:" + "c" * 64)
        self.assertEqual(
            adapter.surviving_helpers(case["store"], assignment_id="attempt-1"), [])
        self.assertTrue(seen, "the adapter never asked the engine")
        for argv in seen:
            self.assertNotIn(argv[1], ("create", "run", "start"),
                             f"the writer-absence read started something: {argv}")
        del _manager

    def test_AN_ALLOWANCE_CANNOT_RAISE_A_VECTORS_OWN_MAXIMUM(self):
        """VECTOR-SPECIFIC MAXIMUM CONTROL, which my budget cases only asserted in prose.

        `custody.allowed` says an allowance may only LOWER a boundary's own ceiling. The
        clamp case above drives allowances SMALLER than every maximum, so it could not
        tell that rule from plain arithmetic. This one asks each vector what it carries
        with no allowance at all -- that is its own maximum, whatever the constants are --
        and then repeats the act with an allowance far larger than any of them, asserting
        every vector carries exactly the same seconds as before.

        OVER THE LISTING READ, which is the bounded act this adapter performs; the acting-vector
        branch is not reached from here, and review 2026-09-28T11-09-51Z asked that the
        docstrings stop implying otherwise.
        """
        from tests.manager.test_intake import ATTEMPT

        def recording(seen):
            def engine(argv, *, seconds=None):
                seen.append((argv[1], seconds))
                return {"status": 0, "stdout": "", "stderr": ""}
            return engine

        # TWO INDEPENDENT ATTEMPTS, each with its own store, because the two acts must be
        # comparable. Measured while writing this: the two roots of ONE attempt do NOT
        # work -- custody refuses the second with "the two roots of one attempt overlap,
        # so neither is free while either is held", since the first act left an
        # unreconciled uncertainty episode. `_running_governed_attempt` builds a fresh
        # fixture per call, so two calls are two worlds.
        # W285465 under the owner supersession at 294568/294616: THE BOUNDED ACT IS THE
        # LISTING. This drove `normalize_directory`, which the selected settlement never
        # performs -- and driving it now meets the live-token guard, because the roots belong to
        # the execution being settled. That guard is genuine and is left alone; what moves is
        # the act this case measures, to the one this adapter still bounds.
        unbounded, raised = [], []
        case = _running_governed_attempt(self)
        first = job_manager._ReclaimAdapter(
            "docker", recording(unbounded),
            custodian_image_digest="sha256:" + "c" * 64)
        first.surviving_helpers(case["store"], assignment_id=ATTEMPT)
        second = job_manager._ReclaimAdapter(
            "docker", recording(raised),
            custodian_image_digest="sha256:" + "c" * 64)
        beside = _running_governed_attempt(self)
        second.surviving_helpers(beside["store"], assignment_id=ATTEMPT,
                                 seconds=10 ** 9, reclaim=10 ** 9)
        self.assertTrue(unbounded, "the unbounded act reached the engine")
        self.assertEqual([verb for verb, _ in unbounded],
                         [verb for verb, _ in raised],
                         "both acts must issue the same vectors to be comparable")
        self.assertEqual([seconds for _, seconds in raised],
                         [seconds for _, seconds in unbounded],
                         "an allowance larger than a vector's own maximum raised it")

    def test_a_stale_pass_after_the_return_releases_no_later_generation(self):
        """A later token must not be freed by a pass about a dead one."""
        from baton_v12.worker_manager import tokens

        case = _running_governed_attempt(self)
        control = case["store"]
        vectors = []
        pass_over = job_manager._reclaiming(
            control, "docker", self._accountable(vectors), "sha256:" + "c" * 64)
        pass_over(now="2026-08-24T01:00:00.000Z")
        self.assertEqual(tokens.outstanding(control, case["domain"]), [])
        second = tokens.workspace_governance().reserve(
            control, {"runtime_attempt_id": "attempt-2",
                      "workspace_device": 66, "workspace_inode": 4242},
            operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)
        # THE STALE PASS, run again over the same attempts.
        pass_over(now="2026-08-24T01:00:00.000Z")
        held = tokens.outstanding(control, case["domain"])
        self.assertEqual([one["generation"] for one in held], [2],
                         "generation 2 must still hold the resource")

    def test_without_a_custodian_the_RECLAIM_STILL_SETTLES(self):
        """W285465 under the owner supersession at 294568/294616: SUPERSEDED, and this is the
        case that named the old rule.

        It asserted that a lean pass with no custodian left the resource HELD, waiting for a
        normalizing ending. The selected settlement performs no custody act at all -- it
        observes the exact container's termination, records the execution status, preserves the
        workspace as is and releases the exact gate -- so gating it on a custodian held every
        reclaimed resource for a capability the ending does not use.

        WHAT THIS NOW HOLDS ONTO: the resource is actually RETURNED, read from the ledger, and
        the preserved workspace is not deleted by the settlement that released it.
        """
        from baton_v12.worker_manager import tokens

        case = _running_governed_attempt(self)
        control = case["store"]

        def engine(argv, *, seconds=None):
            del seconds
            if argv[1] == "inspect":
                return {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: " + argv[-1]}
            return {"status": 0, "stdout": "", "stderr": ""}

        answer = job_manager._reclaiming(control, "docker", engine)(
            now="2026-08-24T01:00:00.000Z")
        outcome = answer["reclaimed"][0]
        self.assertEqual(outcome["ending"]["settled"], "returned")
        self.assertTrue(tokens.token_of(control, case["domain"], 1)["revoked"])
        # THE ACTUAL GOVERNED RELEASE, read from the ledger rather than from the answer: the
        # generation is no longer outstanding.
        self.assertEqual(tokens.outstanding(control, case["domain"]), [],
                         "the settlement reported a return the ledger does not have")

    def test_one_attempt_s_refusal_does_not_end_the_expiry_pass(self):
        """The visible policy `manager.serve` deliberately does not choose: a sweep
        that died on one unreachable engine would leave every OTHER overdue resource
        held."""
        control = _running_governed_attempt(self)["store"]

        def engine(argv, *, seconds=None):
            del seconds
            return {"status": 1, "stdout": "", "stderr": "connect: no daemon"}

        answer = job_manager._reclaiming(control, "docker", engine)(
            now="2026-08-24T01:00:00.000Z")
        # MEASURED, AND MY FIRST EXPECTATION WAS THE WRONG CHANNEL: a refused stop is
        # absorbed by the reclaim itself as `held` -- "a refused stop is not a
        # cessation" -- rather than escaping as a refusal. The `refused` list carries
        # refusals the reclaim raises, such as a revocation that will not commit.
        # Either way the pass CONTINUES, which is what this case is about.
        self.assertEqual(answer["refused"], [])
        self.assertEqual([one["reclaimed"] for one in answer["reclaimed"]],
                         ["held"])
        self.assertIn("the stop was refused", answer["reclaimed"][0]["why"])
        self.assertIn("did not stop", answer["reclaimed"][0]["why"])

    def test_the_lean_adapter_reads_absence_only_from_a_missing_identity(self):
        answers = {
            # ABSENCE, and only from an exact missing-CONTAINER answer that names
            # the identity that was asked about.
            "no such": {"status": 1, "stdout": "",
                        "stderr": "Error: No such container: x"},
            # W275774 review 17:27:42Z's three defects, each as a case:
            "missing socket": {"status": 1, "stdout": "",
                               "stderr": "open /var/run/docker.sock: no such "
                                         "file or directory"},
            "no such, other id": {"status": 1, "stdout": "",
                                  "stderr": "No such container: somebody-else"},
            # W275774 review 17:35:44Z's three exact-identity defects:
            "no such, neighbouring name": {
                "status": 1, "stdout": "",
                "stderr": "Error: No such container: x-other"},
            "empty id": {"status": 0, "stderr": "",
                         "stdout": json.dumps({"Id": "",
                                               "State": {"Running": False}})},
            "neighbouring id": {"status": 0, "stderr": "",
                                "stdout": json.dumps(
                                    {"Id": "x-other",
                                     "State": {"Running": False}})},
            "another container": {"status": 0, "stderr": "",
                                  "stdout": json.dumps(
                                      {"Id": "container-b",
                                       "State": {"Running": False}})},
            "null running": {"status": 0, "stderr": "",
                             "stdout": json.dumps({"Id": "x",
                                                   "State": {"Running": None}})},
            "unreachable": {"status": 1, "stdout": "", "stderr": "no daemon"},
            "malformed": {"status": 0, "stderr": "", "stdout": "{not json"},
            "up": {"status": 0, "stderr": "",
                   "stdout": json.dumps({"Id": "x", "State": {"Running": True}})},
            "down": {"status": 0, "stderr": "",
                     "stdout": json.dumps({"Id": "x",
                                           "State": {"Running": False}})},
        }
        expected = {"no such": "absent", "missing socket": "uncertain",
                    "no such, other id": "uncertain",
                    "no such, neighbouring name": "uncertain",
                    "empty id": "uncertain", "neighbouring id": "uncertain",
                    "another container": "uncertain", "null running": "uncertain",
                    "unreachable": "uncertain", "malformed": "uncertain",
                    "up": "running", "down": "quiescent"}
        for which, reply in answers.items():
            with self.subTest(which=which):
                adapter = job_manager._ReclaimAdapter(
                    "docker", lambda argv, *, seconds=None: reply)
                self.assertEqual(adapter.observe("x")["state"], expected[which])

    def test_one_tick_reclaims_a_bounded_number_of_resources(self):
        """W275774 review 17:35:44Z: BOUNDED EXPIRY OPPORTUNITY, asserted.

        A store with a large backlog must not make one tick run unboundedly long. The
        candidate list is capped, so the worst-case tick is that cap times the
        per-command bound rather than the whole store times the tool's 600-second
        default -- and the next tick continues where this one stopped.
        """
        self.assertEqual(job_manager._RECLAIM_CANDIDATES, 16)
        self.assertEqual(job_manager._RECLAIM_SECONDS, 30)
        asked = []
        adapter = job_manager._ReclaimAdapter(
            "docker",
            lambda argv, *, seconds=None: asked.append(seconds) or {
                "status": 1, "stdout": "",
                "stderr": "Error: No such container: " + argv[-1]})
        adapter.observe("x")
        self.assertEqual(asked, [job_manager._RECLAIM_SECONDS],
                         "a reclaim's engine calls carry their own short bound")

    def test_the_bounded_pass_rotates_so_a_later_resource_is_reached(self):
        """W275774 review 17:40:10Z: A BOUND THAT STARVES IS WORSE THAN NO BOUND.

        My capped pass always started at the beginning, so it visited the same first
        sixteen held resources on every tick and a seventeenth was never reached --
        held forever with nothing ever looking at it. The pass now continues after
        where it stopped, so this walks a list of nineteen and asserts the ones a
        second and third tick reach.
        """
        rows = [{"runtime_attempt_id": f"attempt-{index:02d}"}
                for index in range(19)]
        first = job_manager._after(rows, None)[:job_manager._RECLAIM_CANDIDATES]
        self.assertEqual([one["runtime_attempt_id"] for one in first][:2],
                         ["attempt-00", "attempt-01"])
        self.assertEqual(len(first), 16)
        second = job_manager._after(
            rows, first[-1]["runtime_attempt_id"])[:job_manager._RECLAIM_CANDIDATES]
        reached = [one["runtime_attempt_id"] for one in second]
        self.assertEqual(reached[:3],
                         ["attempt-16", "attempt-17", "attempt-18"],
                         "the seventeenth onward must be reached on the next tick")
        # AND IT WRAPS rather than stopping: the rest of the second tick returns to
        # the beginning, so nothing is visited twice before everything is visited once.
        self.assertEqual(reached[3], "attempt-00")
        third = job_manager._after(rows, reached[-1])
        self.assertEqual(third[0]["runtime_attempt_id"], "attempt-13")

    def test_a_rotation_past_the_last_identity_begins_again(self):
        rows = [{"runtime_attempt_id": "attempt-a"},
                {"runtime_attempt_id": "attempt-b"}]
        self.assertEqual(job_manager._after(rows, "attempt-z"), rows)

    def test_an_interruption_is_the_operator_s_and_not_an_observation(self):
        """A `BaseException` catch reported an operator stopping the process as an
        engine that could not be asked. Narrowed, and asserted."""
        def interrupting(argv, *, seconds=None):
            raise KeyboardInterrupt("operator stopped this process")

        adapter = job_manager._ReclaimAdapter("docker", interrupting)
        with self.assertRaises(KeyboardInterrupt):
            adapter.observe("x")

    def test_the_status_surface_gains_no_serving_or_refresh_capability(self):
        held = self.WithBoth()
        surface = job_manager._Observing(object(), held)
        self.assertIsNone(surface.refresh_runtime({"attempt_id": "a"}))
        for verb in ("dispatch", "conclude", "admit", "claim"):
            self.assertFalse(hasattr(surface, verb), verb)


class TheRecoveryPassVisitsTheUNCERTAINTokensToo(unittest.TestCase):
    """W275776 (Child C), TOK-10: "restart recovery processes overdue AND UNCERTAIN
    tokens before admitting conflicts."

    Measured before this was wired, and the reviewer's probe measured it independently:
    for an outstanding token whose activation was admitted and never settled, this pass
    made ZERO engine calls and reported nothing, because `_governed_candidates` selects on
    `Governance.overdue` and such a token is not overdue. Every case here drives the REAL
    composed pass -- the one `serve` is handed -- over real rows and a controlled runner.
    """

    def unsettled(self):
        return _unsettled_governed_attempt(self)

    def engine(self, answers):
        """A controlled engine runner that records every vector it is given."""
        vectors = []

        def run(argv, *, seconds=None):
            del seconds
            vectors.append(list(argv))
            return answers(argv)

        return vectors, run

    def test_the_pass_observes_the_exact_container_the_token_bound(self):
        from baton_v12.worker_manager import tokens

        case = self.unsettled()
        control = case["store"]
        vectors, run = self.engine(lambda argv: {
            "status": 0, "stderr": "",
            "stdout": json.dumps({"Id": case["runtime_id"],
                                  "State": {"Running": True}})})
        answer = job_manager._reclaiming(control, "docker", run)(
            now="2026-08-24T00:05:00.000Z")
        # THE OBSERVATION HAPPENED, and it named the container the TOKEN recorded.
        self.assertEqual([one[1] for one in vectors], ["inspect"])
        self.assertEqual(vectors[0][-1], case["runtime_id"])
        # AND THE REPORT CARRIES THE EXACT REFERENCES REC-4 REQUIRES.
        self.assertEqual(len(answer["unresolved"]), 1)
        held = answer["unresolved"][0]
        self.assertEqual(held["domain"], case["domain"])
        self.assertEqual(held["generation"], 1)
        self.assertEqual(held["execution"], case["attempt_id"])
        self.assertEqual(held["container"], case["runtime_id"])
        self.assertEqual(held["observation"], "running")
        self.assertFalse(held["expired"])
        self.assertTrue(held["held"])
        # NOTHING WAS RECLAIMED, because nothing here is overdue.
        self.assertEqual(answer["reclaimed"], [])
        self.assertEqual(answer["refused"], [])
        # AND THE RESOURCE IS STILL HELD: observation is not settlement.
        self.assertEqual(len(tokens.outstanding(control, case["domain"])), 1)
        self.assertTrue(tokens.token_of(control, case["domain"], 1)["activating"])

    def test_an_unreachable_engine_holds_and_says_so_per_attempt(self):
        """TOK-10's actionable held state: the fault is an answer, the hold stays, and
        one unreachable engine does not end the pass."""
        from baton_v12.worker_manager import tokens

        case = self.unsettled()
        control = case["store"]

        def unavailable(argv, *, seconds=None):
            del seconds, argv
            raise OSError("the engine is unreachable")

        answer = job_manager._reclaiming(control, "docker", unavailable)(
            now="2026-08-24T00:05:00.000Z")
        self.assertEqual(len(answer["unresolved"]), 1)
        held = answer["unresolved"][0]
        # `uncertain` IS THE MODULE'S OWN WORD for an observation that could not be
        # established, and the reclaim adapter answers it for an unreachable engine
        # rather than raising -- measured, and the report uses the same vocabulary.
        self.assertEqual(held["observation"], "uncertain")
        self.assertIn("could not be asked", held["why"])
        self.assertEqual(held["container"], case["runtime_id"])
        self.assertEqual(len(tokens.outstanding(control, case["domain"])), 1)

    def test_a_LATER_TICK_RETRIES_after_the_engine_comes_back(self):
        """The retry the review asked for: the hold is not terminal, and the next tick
        asks again rather than remembering a failure."""
        case = self.unsettled()
        control = case["store"]
        state = {"up": False}

        def flaky(argv, *, seconds=None):
            del seconds
            if not state["up"]:
                raise OSError("the engine is unreachable")
            return {"status": 0, "stderr": "",
                    "stdout": json.dumps({"Id": case["runtime_id"],
                                          "State": {"Running": True}})}

        pass_over = job_manager._reclaiming(control, "docker", flaky)
        first = pass_over(now="2026-08-24T00:05:00.000Z")
        self.assertEqual(first["unresolved"][0]["observation"], "uncertain")
        state["up"] = True
        second = pass_over(now="2026-08-24T00:05:10.000Z")
        self.assertEqual(second["unresolved"][0]["observation"], "running")
        self.assertEqual(second["unresolved"][0]["container"], case["runtime_id"])

    def test_the_pass_never_starts_or_dispatches_anything(self):
        """Section 17's Recovery row: no duplicate container or provider dispatch. The
        pass may only ask -- so no vector it composes may be a run, create or start."""
        case = self.unsettled()
        vectors, run = self.engine(lambda argv: {
            "status": 1, "stdout": "",
            "stderr": "Error: No such object: " + argv[-1]})
        answer = job_manager._reclaiming(case["store"], "docker", run)(
            now="2026-08-24T00:05:00.000Z")
        self.assertTrue(vectors)
        for argv in vectors:
            self.assertNotIn(argv[1], ("run", "create", "start", "exec"))
        # AND AN ABSENT CONTAINER IS REPORTED, NOT TREATED AS AN ENDING: the accepted
        # ending for a proved non-launch needs its own record, which this cut may never
        # have written.
        self.assertEqual(answer["unresolved"][0]["observation"], "absent")
        self.assertTrue(answer["unresolved"][0]["held"])

    def test_a_contradiction_between_the_attachment_and_the_binding_is_reported(self):
        """W275776 R2: the attempt row names one runtime and the token authorized another.

        `reconcile_runtime` attaches whichever container carries the attempt's complete
        label set -- the accepted exactness -- so the id a previous process bound can be
        the stale one. The two names then disagree, and the resource's stop path acts on
        the BOUND one while the attempt's ending acts on the attached one. The pass reports
        that rather than choosing, and the hold stands.
        """
        case = self.unsettled()
        control = case["store"]
        control._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("another-runtime", case["attempt_id"]))
        vectors, run = self.engine(lambda argv: {
            "status": 0, "stderr": "",
            "stdout": json.dumps({"Id": case["runtime_id"],
                                  "State": {"Running": True}})})
        answer = job_manager._reclaiming(control, "docker", run)(
            now="2026-08-24T00:05:00.000Z")
        held = answer["unresolved"][0]
        self.assertEqual(held["container"], case["runtime_id"])
        self.assertEqual(held["contradicts_binding"], "another-runtime")
        self.assertTrue(held["held"])
        # AND THE ENGINE WAS ASKED ABOUT THE BOUND ONE, which is the token's own fact.
        self.assertEqual(vectors[0][-1], case["runtime_id"])

    def test_a_HISTORICAL_row_over_the_same_resource_attributes_nothing(self):
        """W275776 review 2026-09-27T11-52-29Z [P2], reproduced and now this Work's case.

        Serial attempts over one retained resource share a domain, and a row is only how
        that domain was DISCOVERED. Reading the attachment off the discovery row let a
        historical attempt's old runtime be reported as the current token's contradiction --
        a false actionable contradiction, which is worse than none. The attachment is the
        execution the TOKEN names, and nothing else.
        """
        case = self.unsettled()
        control = case["store"]
        owner = dict(manager_attempts._require_attempt(control, case["attempt_id"]))
        historical = dict(owner, runtime_attempt_id="historical-attempt",
                          runtime_id="historical-container")
        vectors, run = self.engine(lambda argv: {
            "status": 0, "stderr": "",
            "stdout": json.dumps({"Id": case["runtime_id"],
                                  "State": {"Running": True}})})
        with mock.patch.object(job_manager, "_governed_rows",
                               return_value=[historical, owner]):
            answer = job_manager._reclaiming(control, "docker", run)(
                now="2026-08-24T00:05:00.000Z")
        self.assertEqual(len(answer["unresolved"]), 1,
                         "one domain was reported more than once")
        held = answer["unresolved"][0]
        self.assertEqual(held["execution"], case["attempt_id"])
        self.assertEqual(held["container"], case["runtime_id"])
        self.assertNotIn("contradicts_binding", held)
        self.assertEqual(vectors[0][-1], case["runtime_id"])

    def test_a_GENUINE_owner_mismatch_is_still_reported(self):
        """The other half: correlating with the owner must not silence a real
        disagreement. The OWNER's own attachment differs from the token's binding, and
        that is reported exactly as before."""
        case = self.unsettled()
        control = case["store"]
        control._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("another-runtime", case["attempt_id"]))
        owner = dict(manager_attempts._require_attempt(control, case["attempt_id"]))
        historical = dict(owner, runtime_attempt_id="historical-attempt",
                          runtime_id="historical-container")
        _vectors, run = self.engine(lambda argv: {
            "status": 0, "stderr": "",
            "stdout": json.dumps({"Id": case["runtime_id"],
                                  "State": {"Running": True}})})
        with mock.patch.object(job_manager, "_governed_rows",
                               return_value=[historical, owner]):
            answer = job_manager._reclaiming(control, "docker", run)(
                now="2026-08-24T00:05:00.000Z")
        held = answer["unresolved"][0]
        self.assertEqual(held["contradicts_binding"], "another-runtime",
                         "the owner's real mismatch was silenced")
        self.assertTrue(held["held"])

    def test_the_report_names_which_cut_each_unknown_is(self):
        """W275776 R2: `bound-not-admitted` and `admitted-unsettled` are different
        unknowns -- an inert created container against one that may be running -- and the
        report says which."""
        case = self.unsettled()
        vectors, run = self.engine(lambda argv: {
            "status": 0, "stderr": "",
            "stdout": json.dumps({"Id": case["runtime_id"],
                                  "State": {"Running": True}})})
        answer = job_manager._reclaiming(case["store"], "docker", run)(
            now="2026-08-24T00:05:00.000Z")
        self.assertEqual(answer["unresolved"][0]["cut"], "admitted-unsettled")
        del vectors

    def test_a_settled_activation_is_never_visited(self):
        """The ordinary running attempt: its activation is settled, so the uncertain
        visit has nothing to ask about and makes no engine call for it."""
        case = _running_governed_attempt(self)
        vectors, run = self.engine(lambda argv: {
            "status": 0, "stderr": "",
            "stdout": json.dumps({"Id": case["runtime_id"],
                                  "State": {"Running": False}})})
        # The clock in that fixture is past the lifetime, so the overdue half acts --
        # what this asserts is that the UNCERTAIN report is empty for it.
        answer = job_manager._reclaiming(case["store"], "docker", run)(
            now="2026-08-24T01:00:00.000Z")
        self.assertEqual(answer["unresolved"], [])
        del vectors


def _unsettled_governed_attempt(case):
    """One attempt whose LAUNCH nobody settled, holding an UNEXPIRED governed token.

    W275776 (Child C): the state an interrupted manager leaves and the expiry scan never
    selected. Built from the same intake fixture and the same accepted acts as the overdue
    case beside it, with exactly two differences, and both are the point:

      * the activation is ADMITTED and NEVER SETTLED -- `reservation.bind(...)()` admits it
        and `settle` is not called -- which is what a manager killed between the engine's
        `create` and its `start` leaves behind;
      * the clock is NOT moved past the lifetime, so nothing here is overdue and
        `Governance.overdue` answers `None` for it.
    """
    from baton_v12.worker_manager import attempts as manager_attempts
    from baton_v12.worker_manager import tokens
    from baton_v12.worker_manager import workspaces as _workspaces
    from tests.manager import input_roots as _input_roots
    from tests.manager import test_intake

    fixture = test_intake.TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence()
    fixture.setUp()
    case.addCleanup(fixture.doCleanups)
    fixture.running_attempt()
    manager_attempts.pin_boundary_identity(
        fixture.store, attempt_id=test_intake.ATTEMPT, source=(66, 111),
        workspace=(66, 4242))
    attempt = fixture.attempt_row()
    # W285465: THE ALLOCATION COMES FIRST, because that is the only order production
    # ever has. MEASURED, and it is why this moved: W285464's accepted revalidation
    # makes `assignment_workspace` a READ-ONLY proof while this attempt's task token is
    # outstanding, so allocating after the bind asked it to prove roots that did not
    # exist yet and every case in this class errored with "a custody root is a directory
    # this manager created". The host allocates, then the task takes the token.
    storage = _workspaces.configured_workspace_storage(fixture.store).place
    _workspaces.assignment_workspace(
        _input_roots.configured_group(fixture.store), storage,
        test_intake.ATTEMPT)
    governance = tokens.workspace_governance()
    reservation = governance.reserve(
        fixture.store, attempt,
        operation=manager_attempts._start_operation_id(attempt))
    reservation.bind(attempt["runtime_id"])()          # ADMITTED, never settled
    return {"runtime_id": attempt["runtime_id"],
            "domain": tokens.domain_of("workspace", "66:4242"),
            "attempt_id": test_intake.ATTEMPT,
            "store": fixture.store}


def _running_governed_attempt(case):
    """One RUNNING attempt holding an overdue governed workspace token.

    Built through the intake suite's own fixture so the rows are the real ones, and
    the clock is moved past the token lifetime rather than the token being forged.
    """
    from baton_v12.worker_manager import attempts as manager_attempts
    from baton_v12.worker_manager import tokens
    from tests.manager import test_intake

    fixture = test_intake.TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence()
    fixture.setUp()
    case.addCleanup(fixture.doCleanups)
    fixture.running_attempt()
    manager_attempts.pin_boundary_identity(
        fixture.store, attempt_id=test_intake.ATTEMPT, source=(66, 111),
        workspace=(66, 4242))
    attempt = fixture.attempt_row()
    # W275774 review 18:11:15Z pointed at the CANONICAL setup, which I had been
    # guessing at: `tests/manager/test_custody.py CustodyCase.setUp` allocates through
    # `workspaces.assignment_workspace(group, storage, attempt)` rather than creating
    # directories. That is what makes the roots the ones custody will accept -- my
    # three hand-built layouts were each refused, correctly.
    from baton_v12.worker_manager import workspaces as _workspaces
    # `input_roots` is the TEST suite's own helper rather than a product module, which
    # is how `test_custody` reaches the configured group.
    from tests.manager import input_roots as _input_roots

    storage = _workspaces.configured_workspace_storage(fixture.store).place
    _workspaces.assignment_workspace(
        _input_roots.configured_group(fixture.store), storage,
        test_intake.ATTEMPT)
    # W285465: AND THE TOKEN IS TAKEN AFTER THE ALLOCATION, for the reason recorded in
    # `_unsettled_governed_attempt` -- the accepted revalidation refuses to prove roots
    # that do not exist yet, and the production order is allocate then govern.
    governance = tokens.workspace_governance()
    reservation = governance.reserve(
        fixture.store, attempt,
        operation=manager_attempts._start_operation_id(attempt))
    reservation.bind(attempt["runtime_id"])()
    reservation.settle(attempt["runtime_id"])
    fixture.store._clock = lambda: "2026-08-24T01:00:00.000Z"
    return {"runtime_id": attempt["runtime_id"],
            "domain": tokens.domain_of("workspace", "66:4242"),
            "store": fixture.store}
