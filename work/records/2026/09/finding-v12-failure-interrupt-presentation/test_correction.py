"""Regressions for the W306614 correction. No engine, provider or deployed store.

The REAL two-Job supervisor and the REAL `baton_v12.job_manager.serve` loop run here
against a simulated status projection, simulated time and mocked lifecycle boundaries.
`test_diagnosis.py` holds the two witnesses that localised the defects; these hold the
behaviour the owner asked for at 306698 and the acceptance matrix in `PROPOSAL.md`.

WHAT IS SIMULATED AND WHAT IS NOT. The supervisor's own loop, its per-Job classification,
its stop decision, its outcome accounting and the CLI's interruption presentation are the
real code. The status projection, the sweep, the clock and the cleanup/cancellation
boundaries are stands-in, exactly as the accepted research witnesses used. These do not
establish connected live acceptance and are not offered as it.
"""
import contextlib
import io
import json
import os
import pathlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "finding-v12-real-jobs-adoption-gate"))

import two_job_supervisor as subject                         # noqa: E402
import baton_v12.job_manager as jobs                         # noqa: E402
from baton_v12.job_manager import manager                    # noqa: E402


class Termination:
    """The handler seam, inert. The real one is exercised by W247941's suite."""

    def install(self):
        pass

    def defer(self):
        return []

    def restore(self):
        pass


def projection(states_by_job, *, attempts=True):
    """One canonical status document, in the shape `_attempts_of` reads."""
    held = []
    for job_id, stages in sorted(states_by_job.items()):
        entry = {"job_id": job_id, "execution_limits": {}, "stages": []}
        for kind, state in sorted(stages.items()):
            stage = {"kind": kind, "state": state, "episodes": []}
            if attempts:
                stage["attempt_id"] = f"attempt-{job_id}-{kind}"
            entry["stages"].append(stage)
        held.append(entry)
    return {"jobs": held}


class Served(unittest.TestCase):
    """One bounded run, with everything below the supervisor stood in for."""

    JOBS = ("job-a", "job-b")

    def serve_with(self, answers, *, total=8, reserve=2, status=None,
                   storage_root=None, task_ids=None):
        """Run `supervise` over a scripted sequence of status projections.

        `answers` is one entry per SERVING TICK, and the last entry repeats. The corrected
        supervisor reads the canonical projection ONCE PER TICK and keeps the whole
        document -- it used to call the per-Job helper once per Job -- so one read is one
        tick here. An entry that is an Exception class or instance is RAISED, which is how
        the unreadable case is driven.
        """
        now = [0]
        sleeps = []
        reports = []
        reads = [0]
        pending = list(answers)

        def sleep(seconds):
            sleeps.append(seconds)
            now[0] += seconds

        def reading(*_args, **_kwargs):
            held = pending[min(reads[0], len(pending) - 1)]
            reads[0] += 1
            if isinstance(held, BaseException) or (
                    isinstance(held, type) and issubclass(held, BaseException)):
                raise held
            return held

        sweep = {"jobs": []}
        with tempfile.TemporaryDirectory(prefix="w306614-") as root, \
                contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(manager, "reconcile",
                                                  return_value=sweep))
            swept = stack.enter_context(mock.patch.object(manager, "sweep",
                                                         return_value=sweep))
            stack.enter_context(mock.patch.object(
                jobs, "status", side_effect=status or reading))
            stack.enter_context(mock.patch.object(subject, "generations_from",
                                                  return_value={}))
            stack.enter_context(mock.patch.object(subject, "verdicts_of",
                                                  return_value={}))
            stack.enter_context(mock.patch.object(subject.baseline,
                                                  "_cancel_active",
                                                  return_value={}))
            stack.enter_context(mock.patch.object(
                subject.baseline, "_cleanups",
                return_value={"cleanup": {}, "outstanding": []}))
            stack.enter_context(mock.patch.object(subject.baseline,
                                                  "_retention_of",
                                                  return_value="sha256:" + "a" * 64))
            measured = subject.supervise(
                object(), object(), mock.Mock(), job_ids=list(self.JOBS),
                bounds={"total_seconds": total, "cleanup_seconds": reserve},
                outcome_path=str(Path(root) / "outcome.json"),
                deployment_path="not-opened.json",
                clock=lambda: "2026-09-29T00:00:00.000Z",
                sleep=sleep, monotonic=lambda: now[0],
                termination=Termination(), report=reports.append,
                storage_root=storage_root, task_ids=task_ids)
        return measured, sleeps, reports, swept

    def interrupted_with(self, answers, **operands):
        """The same run, when `supervise` ends by raising the retained interruption."""
        try:
            return self.serve_with(answers, **operands) + (None,)
        except subject.baseline.SupervisorInterrupted as stopped:
            return (stopped.outcome, None, None, None, stopped)

    # ---- the acceptance matrix ------------------------------------------

    def test_an_INTERRUPTION_in_the_status_read_STOPS_ADMISSION_at_once(self):
        """Review R1, and the counterexample it measured, inverted.

        The reviewer injected `KeyboardInterrupt` into the status read and watched the run
        reach `serving-bound-exceeded`: the old `_observed` caught `BaseException`,
        recorded it and carried on, so a signal arriving in the new read left admission
        open until the deadline. A non-`Exception` now propagates to the serving
        interruption handler `supervise` already installs.
        """
        active = projection({one: {"implementation": "active"}
                             for one in self.JOBS})
        measured, _sleeps, _reports, _swept, stopped = self.interrupted_with(
            [KeyboardInterrupt("reviewer injected signal during status"), active],
            total=6, reserve=2)

        self.assertIsNotNone(stopped, "the interruption did not reach the caller")
        self.assertEqual(measured["stopped"], "interrupted")
        self.assertNotEqual(measured["stopped"], "serving-bound-exceeded")
        self.assertTrue(any("KeyboardInterrupt" in one
                            for one in measured["interruptions"]),
                        measured["interruptions"])
        # ADMISSION WAS CLOSED BEFORE ANYTHING WAS CANCELLED, and the shutdown ran.
        self.assertIs(measured["admission_closed_before_cancellation"], True)
        self.assertEqual(measured["state"], "held")

    # ---- the REAL consumption boundary ----------------------------------
    #
    # W306614 review 2026-09-29T17-33-48Z: my first version invented
    # `exchange["diagnostic"]`, a field the exchange observation does not publish, so it
    # proved closed-value parsing and nothing about whether a real diagnostic can ever be
    # consumed. These build an ACTUAL retained adapter report on disk, in the actual
    # custody layout, and declare it the way the manager declares an artifact -- so the
    # supervisor's reader is exercised end to end, including every refusal.

    OAUTH = {"schema": "baton.provider-diagnostic/1", "http_status": 401,
             "classification": "authentication_failed",
             "explanation": ("Failed to authenticate: OAuth session expired and "
                             "could not be refreshed"),
             "explanation_status": "supported-constant",
             "request_id": None, "request_id_status": "unavailable"}

    def retained(self, storage, *, attempt, task_id, diagnostic=None,
                 reason="api-error", status=1, output="proposal",
                 filename="result.json", schema="baton.dogfood-proposal/2",
                 raw=None, custody=None):
        """Write one adapter report where the manager would, and declare its artifact row."""
        place = (pathlib.Path(storage) / (custody or "custody") / attempt
                 / output)
        place.mkdir(parents=True, exist_ok=True)
        document = {"schema": schema, "task_id": task_id,
                    "disposition": "provider-failed",
                    "provider": {"failure_reason": reason, "status": status,
                                 "seconds_bound": 180}}
        if diagnostic is not None:
            document["provider"]["diagnostic"] = diagnostic
        (place / filename).write_text(
            raw if raw is not None else json.dumps(document),
            encoding="utf-8")
        return {"output_name": output, "artifact_id": f"{attempt}:{output}",
                "locator": "file://" + str(place)}

    def failed_with(self, storage, rows, *, running=()):
        """A projection whose failed implementation carries the given artifact rows.

        `running` names Jobs that are still ACTIVE in this tick, which is how a case keeps
        serving alive long enough to reach a second tick -- a projection in which every
        pipeline is already terminal ends the run at once, correctly, and my first versions
        of the two multi-tick cases below never got their second tick because of it.
        """
        failed = projection({
            one: ({"implementation": "active"} if one in running
                  else {"implementation": "exceptional", "review": "blocked"})
            for one in self.JOBS})
        for entry in failed["jobs"]:
            for stage in entry["stages"]:
                if stage["state"] != "exceptional":
                    continue
                stage.update(stage_id=f"{entry['job_id']}/implementation",
                             work_id=f"W-{entry['job_id']}", episode=1,
                             offer_id=f"offer-{entry['job_id']}",
                             runtime={"runtime_id": f"runtime-{entry['job_id']}",
                                      "execution_runtime": "destroyed",
                                      "assignment": f"assignment-{entry['job_id']}",
                                      "activity": None},
                             # THE REAL PUBLISHER SHAPE. `worker_manager/exchange.py`
                             # `_terminal` returns a NESTED document; review
                             # 2026-09-29T17-44-50Z R2b is right that flat keys of my
                             # own invention proved nothing about it.
                             exchange={"state": "faulted",
                                       "sequence_id": f"sequence-{entry['job_id']}",
                                       "terminal": {
                                           "ending": "faulted",
                                           "answered": ["open", "work"],
                                           "disposition": None,
                                           "fault_code": "agent",
                                           "manifest_digest": None},
                                       "command": {"operation": "work",
                                                   "operation_id": "op-1"},
                                       "receipt": {"state": "recorded"}},
                             artifacts=rows(entry["job_id"],
                                            stage["attempt_id"]))
        return failed

    def tasks(self):
        return {one: f"probe-{one}" for one in self.JOBS}

    def test_a_PUBLISHED_OAUTH_report_reaches_the_cause_through_the_real_reader(self):
        """The positive the reviewer asked for, through the actual consumption path."""
        with tempfile.TemporaryDirectory(prefix="w306614-storage-") as storage:
            failed = self.failed_with(
                storage, lambda job_id, attempt: [self.retained(
                    storage, attempt=attempt, task_id=f"probe-{job_id}",
                    diagnostic=self.OAUTH)])
            measured, _sleeps, reports, _swept = self.serve_with(
                [failed], storage_root=storage, task_ids=self.tasks())

        for one in self.JOBS:
            with self.subTest(job=one):
                facts = measured["failures"][one]
                self.assertEqual(
                    facts["provider_cause"],
                    "provider-reported-oauth-session-expired-refresh-failed")
                self.assertEqual(facts["provider_diagnostic"]["classification"],
                                 "authentication_failed")
                self.assertEqual(facts["adapter_report"]["availability"],
                                 "available")
                self.assertEqual(facts["adapter_report"]["provider_reason"],
                                 "api-error")
                # THE CANONICAL TERMINAL RECORD IS PRESERVED BESIDE IT, from where the
                # publisher actually puts it.
                self.assertEqual(facts["terminal"]["state"], "faulted")
                self.assertEqual(facts["terminal"]["terminal"]["ending"], "faulted")
                self.assertEqual(facts["terminal"]["terminal"]["fault_code"], "agent")
                self.assertEqual(facts["terminal"]["terminal"]["answered"],
                                 ["open", "work"])
                self.assertEqual(facts["terminal"]["sequence_id"],
                                 f"sequence-{one}")
                self.assertEqual(facts["terminal"]["command"]["operation"], "work")
                self.assertEqual(facts["terminal"]["receipt"]["state"], "recorded")
                # AND THE IDENTITY IS BOUND.
                self.assertEqual(facts["attempt_id"],
                                 f"attempt-{one}-implementation")
                self.assertEqual(facts["assignment"], f"assignment-{one}")
                line = [x for x in reports if f"Job {one} FAILED" in x][0]
                self.assertIn("provider-reported-oauth-session-expired-refresh-failed",
                              line)
        self.assertTrue(any("provider cause provider-reported-oauth" in why
                            for why in measured["held_because"]),
                        measured["held_because"])

    def test_the_OAUTH_cause_survives_the_INTERRUPTION_summary(self):
        """"Prove the cause through interruption", end to end."""
        import contextlib

        with tempfile.TemporaryDirectory(prefix="w306614-interrupt-") as storage:
            # job-b STAYS ACTIVE, so serving reaches the tick the signal arrives in.
            failed = self.failed_with(
                storage, lambda job_id, attempt: [self.retained(
                    storage, attempt=attempt, task_id=f"probe-{job_id}",
                    diagnostic=self.OAUTH)], running={"job-b"})
            measured, _s, _r, _w, stopped = self.interrupted_with(
                [failed, KeyboardInterrupt("signal 2")],
                storage_root=storage, task_ids=self.tasks())
            del failed

        self.assertIsNotNone(stopped)
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            printed = self.presented(measured)
        del printed
        self.assertIn("provider-reported-oauth-session-expired-refresh-failed",
                      said.getvalue())
        self.assertIn("Job job-a had already FAILED", said.getvalue())
        self.assertNotIn("Job job-b had already FAILED", said.getvalue())

    def presented(self, outcome):
        """`main`'s interruption presentation over a retained outcome, nothing else."""
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution

        handles = [mock.Mock(), mock.Mock(), mock.Mock()]
        with tempfile.TemporaryDirectory(prefix="w306614-present-") as root, \
                contextlib.ExitStack() as stack:
            root = pathlib.Path(root)
            (root / "deployment.json").write_text(json.dumps(
                {"authority_uuid": "a" * 32,
                 "job_bindings": [{"job_id": one} for one in self.JOBS]}))
            (root / "submission.json").write_text("{}")
            retained = root / "outcome.json"

            def interrupted(*_args, **_kwargs):
                subject.baseline._publish(str(retained), outcome)  # noqa: SLF001
                raise subject.baseline.SupervisorInterrupted("signal 2", outcome)

            stack.enter_context(mock.patch.object(jobs.JobStore, "open",
                                                  return_value=handles[0]))
            stack.enter_context(mock.patch.object(ControlStore, "open",
                                                  return_value=handles[1]))
            stack.enter_context(mock.patch.object(stage_execution,
                                                  "operations_from",
                                                  return_value=handles[2]))
            stack.enter_context(mock.patch.object(jobs, "submit"))
            stack.enter_context(mock.patch.object(subject, "supervise",
                                                  side_effect=interrupted))
            return subject.main(
                ["--deployment", str(root / "deployment.json"),
                 "--submission", str(root / "submission.json"),
                 "--job-store", "unused", "--control-store", "unused",
                 "--incarnation", "present", "--outcome", str(retained)])

    def test_a_FOREIGN_or_WRONG_TASK_report_is_refused_as_unknown(self):
        """Wrong task, foreign attempt, and a locator outside this run's storage."""
        cases = {
            "wrong task": lambda storage, job_id, attempt: [self.retained(
                storage, attempt=attempt, task_id="somebody-elses-task",
                diagnostic=self.OAUTH)],
            "foreign attempt": lambda storage, job_id, attempt: [dict(
                self.retained(storage, attempt="attempt-somebody-else",
                              task_id=f"probe-{job_id}", diagnostic=self.OAUTH),
                artifact_id=f"{attempt}:proposal")],
            "two rows for one output": lambda storage, job_id, attempt: [
                self.retained(storage, attempt=attempt,
                              task_id=f"probe-{job_id}", diagnostic=self.OAUTH),
                self.retained(storage, attempt=attempt,
                              task_id=f"probe-{job_id}", diagnostic=self.OAUTH)],
        }
        for name, rows in sorted(cases.items()):
            with self.subTest(refusal=name):
                with tempfile.TemporaryDirectory(prefix="w306614-neg-") as storage:
                    failed = self.failed_with(
                        storage,
                        lambda job_id, attempt, rows=rows: rows(storage, job_id,
                                                                attempt))
                    measured, _sleeps, _reports, _swept = self.serve_with(
                        [failed], storage_root=storage, task_ids=self.tasks())
                for one in self.JOBS:
                    facts = measured["failures"][one]
                    self.assertEqual(facts["provider_cause"], "unknown", name)
                    self.assertEqual(facts["adapter_report"]["availability"],
                                     "unavailable", name)
                    self.assertTrue(facts["adapter_report"]["why"], name)

    def test_a_MALFORMED_or_UNREADABLE_report_is_refused_as_unknown(self):
        """Duplicate members, non-JSON constants, absent files and bad locators."""
        secret = "Bearer sk-not-a-real-token"
        cases = {
            "duplicate member": dict(
                raw='{"schema": "baton.dogfood-proposal/2", "task_id": "probe-job-a",'
                    ' "task_id": "probe-job-a"}'),
            "non-JSON constant": dict(
                raw='{"schema": "baton.dogfood-proposal/2", "provider": NaN}'),
            "absent report": dict(filename="not-the-report.json"),
            "unsupported reason": dict(reason="something-else"),
            "status out of contract": dict(status=9999),
            "prose instead of a diagnostic": dict(
                diagnostic=dict(dict(self.OAUTH), explanation=secret)),
        }
        for name, operands in sorted(cases.items()):
            with self.subTest(refusal=name):
                with tempfile.TemporaryDirectory(prefix="w306614-bad-") as storage:
                    failed = self.failed_with(
                        storage,
                        lambda job_id, attempt, operands=operands: [self.retained(
                            storage, attempt=attempt, task_id=f"probe-{job_id}",
                            **operands)])
                    measured, _sleeps, reports, _swept = self.serve_with(
                        [failed], storage_root=storage, task_ids=self.tasks())
                for one in self.JOBS:
                    facts = measured["failures"][one]
                    self.assertEqual(facts["provider_cause"], "unknown", name)
                    self.assertIsNone(facts["provider_diagnostic"]["explanation"])
                self.assertNotIn(secret, json.dumps(measured), name)
                self.assertNotIn(secret, "\n".join(reports), name)

    def test_an_ANCESTOR_SYMLINK_cannot_escape_the_selected_storage(self):
        """Review R2a, and the reviewer's own escape reproduced as a refusal.

        `O_NOFOLLOW` on the whole path protects the FINAL NAME only, and the lexical
        `relative_to` check reads the DECLARED path -- so `storage/custody` pointing at a
        sibling tree answered `available` with an `authentication_failed` cause attributed
        from outside the selected root. Every component is walked with a directory
        descriptor now.
        """
        with tempfile.TemporaryDirectory(prefix="w306614-escape-") as root:
            root = pathlib.Path(root)
            storage = root / "storage"
            foreign = root / "foreign"
            storage.mkdir()
            (foreign / "custody").mkdir(parents=True)
            # THE REPORT IS REAL, VALID AND OUTSIDE THE ROOT.
            for one in self.JOBS:
                attempt = f"attempt-{one}-implementation"
                place = foreign / "custody" / attempt / "proposal"
                place.mkdir(parents=True)
                (place / "result.json").write_text(json.dumps(
                    {"schema": "baton.dogfood-proposal/2",
                     "task_id": f"probe-{one}",
                     "provider": {"failure_reason": "api-error", "status": 1,
                                  "diagnostic": self.OAUTH}}), encoding="utf-8")
            (storage / "custody").symlink_to(foreign / "custody",
                                             target_is_directory=True)
            failed = self.failed_with(
                str(storage),
                lambda job_id, attempt: [{
                    "output_name": "proposal",
                    "artifact_id": f"{attempt}:proposal",
                    "locator": "file://" + str(storage / "custody" / attempt
                                               / "proposal")}])
            measured, _sleeps, _reports, _swept = self.serve_with(
                [failed], storage_root=str(storage), task_ids=self.tasks())

        for one in self.JOBS:
            with self.subTest(job=one):
                facts = measured["failures"][one]
                self.assertEqual(facts["provider_cause"], "unknown",
                                 facts["adapter_report"])
                self.assertEqual(facts["adapter_report"]["availability"],
                                 "unavailable")
                self.assertIn("could not be read", facts["adapter_report"]["why"])

    def test_a_SPECIAL_FILE_is_refused_without_blocking(self):
        """Review R2a: `O_NONBLOCK` before the regular-file check.

        A FIFO would otherwise block in `open` before `fstat` could refuse it, which in a
        serving loop is a supervisor that never returns.
        """
        with tempfile.TemporaryDirectory(prefix="w306614-fifo-") as storage:
            for one in self.JOBS:
                place = (pathlib.Path(storage) / "custody"
                         / f"attempt-{one}-implementation" / "proposal")
                place.mkdir(parents=True)
                os.mkfifo(place / "result.json")
            failed = self.failed_with(
                storage,
                lambda job_id, attempt: [{
                    "output_name": "proposal",
                    "artifact_id": f"{attempt}:proposal",
                    "locator": "file://" + str(pathlib.Path(storage) / "custody"
                                               / attempt / "proposal")}])
            measured, _sleeps, _reports, _swept = self.serve_with(
                [failed], storage_root=storage, task_ids=self.tasks())

        for one in self.JOBS:
            facts = measured["failures"][one]
            self.assertEqual(facts["provider_cause"], "unknown")
            self.assertIn("not a regular report", facts["adapter_report"]["why"])

    def test_a_WRONG_JSON_SHAPE_is_unknown_and_does_NOT_fail_serving(self):
        """Review R2a: `[]` at the root and `provider: [1]` raised AttributeError.

        In `supervise` that became `serving-failed`, which ends healthy Jobs because a
        SUPPLEMENTARY report was malformed. That is the consequence being held here, not
        just the return value.
        """
        for name, raw in sorted({
                "a list at the root": "[]",
                "a provider that is not an object":
                    '{"schema": "baton.dogfood-proposal/2", '
                    '"task_id": "probe-job-a", "provider": [1]}',
        }.items()):
            with self.subTest(shape=name):
                with tempfile.TemporaryDirectory(prefix="w306614-shape-") as storage:
                    failed = self.failed_with(
                        storage,
                        lambda job_id, attempt, raw=raw: [self.retained(
                            storage, attempt=attempt, task_id=f"probe-{job_id}",
                            raw=raw)])
                    measured, _sleeps, _reports, _swept = self.serve_with(
                        [failed], storage_root=storage, task_ids=self.tasks())
                self.assertIsNone(measured["serving_failure"], name)
                self.assertEqual(measured["stopped"], "pipelines-terminal", name)
                for one in self.JOBS:
                    facts = measured["failures"][one]
                    self.assertEqual(facts["provider_cause"], "unknown", name)
                    self.assertEqual(facts["adapter_report"]["availability"],
                                     "unavailable", name)

    def test_a_FOREIGN_identity_late_report_never_relabels_the_first_failure(self):
        """Review R2c: the supplement is bound to the SAME failure or it does not happen.

        job-a fails on the first tick with no report. On the second it is a DIFFERENT
        attempt -- a different episode and assignment -- whose report does validate. That
        cause belongs to that observation, not to the first one.
        """
        with tempfile.TemporaryDirectory(prefix="w306614-foreign-") as storage:
            first = self.failed_with(storage, lambda job_id, attempt: [],
                                     running={"job-b"})
            later = self.failed_with(
                storage, lambda job_id, attempt: [self.retained(
                    storage, attempt="attempt-somebody-else",
                    task_id=f"probe-{job_id}", diagnostic=self.OAUTH)],
                running={"job-b"})
            # THE SECOND TICK'S FAILED STAGE IS A DIFFERENT ATTEMPT AND EPISODE.
            for entry in later["jobs"]:
                for stage in entry["stages"]:
                    if stage["state"] == "exceptional":
                        stage.update(attempt_id="attempt-somebody-else",
                                     episode=2,
                                     runtime=dict(stage["runtime"],
                                                  assignment="assignment-other"))
            measured, _sleeps, reports, _swept = self.serve_with(
                [first, later], storage_root=storage, task_ids=self.tasks())

        facts = measured["failures"]["job-a"]
        # THE FIRST FAILURE KEEPS ITS OWN IDENTITY AND ITS OWN HONEST UNKNOWN.
        self.assertEqual(facts["attempt_id"], "attempt-job-a-implementation")
        self.assertEqual(facts["episode"], 1)
        self.assertEqual(facts["provider_cause"], "unknown")
        self.assertIsNone(facts.get("cause_supplemented"))
        self.assertNotIn("provider-reported-oauth", json.dumps(facts))

    def test_a_SAME_identity_late_cause_is_reported_exactly_ONCE(self):
        """Review R2c: a cause that becomes known must be announced, and only once.

        The dedup key held stage states and attempt names only, so a newly validated cause
        with unchanged states was retained in the outcome and never reported.
        """
        with tempfile.TemporaryDirectory(prefix="w306614-late-report-") as storage:
            nothing = self.failed_with(storage, lambda job_id, attempt: [],
                                       running={"job-b"})
            later = self.failed_with(
                storage, lambda job_id, attempt: [self.retained(
                    storage, attempt=attempt, task_id=f"probe-{job_id}",
                    diagnostic=self.OAUTH)], running={"job-b"})
            measured, _sleeps, reports, _swept = self.serve_with(
                [nothing, later, later, later], storage_root=storage,
                task_ids=self.tasks())

        about = [one for one in reports if "Job job-a FAILED" in one]
        # ONE for the failure with no cause yet, ONE when the cause is validated,
        # and NOTHING for the identical ticks after it.
        self.assertEqual(len(about), 2, reports)
        self.assertIn("provider cause unknown", about[0])
        self.assertIn("provider-reported-oauth-session-expired-refresh-failed",
                      about[1])
        self.assertIs(measured["failures"]["job-a"]["cause_supplemented"], True)

    def test_a_LATER_validated_cause_SUPPLEMENTS_a_provisional_unknown(self):
        """The report may be retained after the stage first projects exceptional.

        Review 2026-09-29T17-33-48Z: do not suppress a later available cause solely
        because `failures[job_id]` already exists, and do not rewrite the first canonical
        failure either.
        """
        with tempfile.TemporaryDirectory(prefix="w306614-late-") as storage:
            # NO REPORT YET, and job-b still active so there is a second tick at all.
            nothing = self.failed_with(storage, lambda job_id, attempt: [],
                                       running={"job-b"})
            later = self.failed_with(
                storage, lambda job_id, attempt: [self.retained(
                    storage, attempt=attempt, task_id=f"probe-{job_id}",
                    diagnostic=self.OAUTH)])
            measured, _sleeps, _reports, _swept = self.serve_with(
                [nothing, later], storage_root=storage, task_ids=self.tasks())

        # job-a failed on the first tick with NO report, and the second tick found one.
        for one in ("job-a",):
            facts = measured["failures"][one]
            self.assertIs(facts.get("cause_supplemented"), True)
            self.assertEqual(
                facts["provider_cause"],
                "provider-reported-oauth-session-expired-refresh-failed")
            # THE FIRST CANONICAL OBSERVATION IS UNCHANGED.
            self.assertEqual(facts["state"], "exceptional")
            self.assertEqual(facts["attempt_id"], f"attempt-{one}-implementation")
            self.assertTrue(facts["cause_observed_at"])

    def test_a_LATER_unreadable_status_does_NOT_erase_a_confirmed_failure(self):
        """Review R2's second counterexample, inverted.

        The reviewer drove [A-exceptional/B-active, RuntimeError] and watched the run
        retain `pipelines={}` with only generic missing-verdict and read-error reasons,
        so `main` could not repeat the original failure after an interruption.
        """
        first = projection({"job-a": {"implementation": "exceptional"},
                            "job-b": {"implementation": "active"}})
        measured, _sleeps, reports, _swept = self.serve_with(
            [first, RuntimeError("status unavailable")], total=6, reserve=2)

        # CURRENT ELIGIBILITY IS EMPTY, because the last read did not answer.
        self.assertEqual(measured["pipelines"], {})
        # THE CONFIRMED FAILURE STANDS.
        self.assertIn("job-a", measured["failures"])
        self.assertEqual(measured["failures"]["job-a"]["state"], "exceptional")
        self.assertTrue(any("Job job-a ended exceptionally" in why
                            for why in measured["held_because"]),
                        measured["held_because"])
        self.assertEqual(len(reports), 1, reports)
        # AND AN UNKNOWN READ IS STILL NOT A STOP: the deadline ended it.
        self.assertEqual(measured["stopped"], "serving-bound-exceeded")

    def test_BOTH_failed_reports_each_ONCE_and_stops_before_the_deadline(self):
        """Matrix row 1. This is what run 01 and run 02 could not do.

        Both implementations exceptional, both reviews blocked behind them: one prompt
        report per Job, serving over before the bound, and the failures named in the
        retained outcome rather than only "no attributed verdict".
        """
        failed = projection({one: {"implementation": "exceptional",
                                   "review": "blocked"} for one in self.JOBS})
        measured, sleeps, reports, _swept = self.serve_with([failed])

        self.assertEqual(measured["stopped"], "pipelines-terminal")
        self.assertEqual(sleeps, [], "serving slept after every pipeline was terminal")
        self.assertEqual(len(reports), 2, reports)
        for one in self.JOBS:
            with self.subTest(job=one):
                self.assertTrue(any(f"Job {one} FAILED" in line for line in reports),
                                reports)
                self.assertEqual(measured["pipelines"][one]["reached"], "exceptional")
                self.assertTrue(
                    any(f"Job {one} ended exceptionally" in why
                        for why in measured["held_because"]),
                    measured["held_because"])
        self.assertEqual(measured["state"], "held")

    def test_ONE_failure_does_NOT_end_the_other_Jobs_serving(self):
        """Matrix row 2, and the property `_terminal` over a flattened map would break.

        job-a is exceptional from the first tick; job-b is still active. The run must
        report job-a and KEEP SERVING, because job-b can still do useful work.
        """
        mixed = projection({"job-a": {"implementation": "exceptional",
                                      "review": "blocked"},
                            "job-b": {"implementation": "active",
                                      "review": "queued"}})
        done = projection({"job-a": {"implementation": "exceptional",
                                     "review": "blocked"},
                           "job-b": {"implementation": "completed",
                                     "review": "completed"}})
        # THREE TICKS of the mixed state, then job-b finishes.
        measured, sleeps, reports, _swept = self.serve_with(
            [mixed, mixed, mixed, done])

        self.assertEqual(measured["stopped"], "pipelines-terminal")
        # IT KEPT SERVING while job-b was runnable, and stopped when it was not.
        self.assertEqual(sleeps, [1, 1, 1], sleeps)
        # AND job-a WAS REPORTED ONCE, on the first tick, not three times.
        self.assertEqual(len(reports), 1, reports)
        self.assertIn("Job job-a FAILED", reports[0])
        self.assertEqual(measured["pipelines"]["job-a"]["reached"], "exceptional")
        self.assertEqual(measured["pipelines"]["job-b"]["reached"], "completed")

    def test_ALL_completed_stops_promptly_and_is_still_not_a_success(self):
        """Matrix row 3. Stopping is not acceptance: the verdicts decide that."""
        done = projection({one: {"implementation": "completed",
                                 "review": "completed"} for one in self.JOBS})
        measured, sleeps, reports, _swept = self.serve_with([done])

        self.assertEqual(measured["stopped"], "pipelines-terminal")
        self.assertEqual(sleeps, [])
        self.assertEqual(reports, [], "a completed pipeline reported a failure")
        # NO VERDICTS WERE COLLECTED in this fixture, so the run is HELD -- a stop is
        # not a success, and `held_because` still says why.
        self.assertEqual(measured["state"], "held")
        self.assertTrue(any("produced no attributed verdict" in why
                            for why in measured["held_because"]))

    def test_an_UNREADABLE_projection_is_unknown_rather_than_terminal(self):
        """Matrix row 4. Silence is not failure, and it is not success either.

        The deadline stays the backstop it was, the uncertainty is recorded ONCE rather
        than once per tick, and nothing is reported as failed.
        """
        measured, sleeps, reports, _swept = self.serve_with(
            [RuntimeError("the fixture severed this read")], total=6, reserve=2)

        self.assertEqual(measured["stopped"], "serving-bound-exceeded")
        self.assertEqual(sleeps, [1, 1, 1, 1], sleeps)
        self.assertEqual(reports, [])
        self.assertEqual(measured["pipelines"], {})
        # ONE entry per distinct failure, not one per tick: the read is one call for the
        # whole selected set, and the same message is recorded once however often it
        # recurs.
        unreadable = [one for one in measured["uncertainty"]
                      if "did not complete" in one]
        self.assertEqual(len(unreadable), 1, measured["uncertainty"])
        self.assertEqual(measured["state"], "held")

    def test_a_LATER_different_failure_on_the_same_Job_is_reported_again(self):
        """Deduplication is by what was OBSERVED, not by "this Job was mentioned"."""
        first = projection({"job-a": {"implementation": "exceptional",
                                      "review": "queued"},
                            "job-b": {"implementation": "active"}})
        second = projection({"job-a": {"implementation": "exceptional",
                                       "review": "exceptional"},
                             "job-b": {"implementation": "active"}})
        third = projection({"job-a": {"implementation": "exceptional",
                                      "review": "exceptional"},
                            "job-b": {"implementation": "completed"}})
        measured, _sleeps, reports, _swept = self.serve_with(
            [first, second, third])

        self.assertEqual(len(reports), 2, reports)
        self.assertTrue(all("Job job-a FAILED" in line for line in reports), reports)
        self.assertEqual(measured["stopped"], "pipelines-terminal")


class Presented(unittest.TestCase):
    """The CLI boundary: an expected interruption is a report, not a traceback."""

    def test_an_INTERRUPTION_prints_the_retained_outcome_and_returns_130(self):
        """Matrix row 5, and the other half of `supervise`'s publish-then-raise contract.

        The lower-level contract is unchanged -- `supervise` still publishes and still
        raises, which W247941's
        `test_an_interruption_publishes_the_outcome_and_still_raises` holds. What is new
        is that `main` catches it, names the ORIGINAL per-Job failures before the
        interruption, says where the outcome is, and returns 130.
        """
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution

        outcome = {
            "state": "held", "stopped": "interrupted",
            "held_because": ["Job job-a ended exceptionally at implementation "
                             "exceptional; this run has no retry, so its dependent "
                             "stages could not run"],
            # CURRENT ELIGIBILITY IS EMPTY HERE ON PURPOSE: the last status read before
            # the interruption failed, which is exactly the case review R2 raised. The
            # original failure must still be reportable.
            "pipelines": {},
            "failures": {"job-a": {
                "job_id": "job-a", "kind": "implementation",
                "state": "exceptional", "attempt_id": "attempt-a",
                "episode": 1, "work_id": "0000000a-W1",
                "provider_cause":
                    "provider-reported-oauth-session-expired-refresh-failed",
                "provider_diagnostic": {"classification": "authentication_failed"},
                "diagnostic_locators": ["artifact://contracts/probe-a"]}},
            "unresolved_cleanup": [], "outstanding_cleanup": []}
        handles = [mock.Mock(), mock.Mock(), mock.Mock()]
        said = io.StringIO()
        with tempfile.TemporaryDirectory(prefix="w306614-main-") as root, \
                contextlib.ExitStack() as stack:
            root = Path(root)
            (root / "deployment.json").write_text(json.dumps(
                {"authority_uuid": "a" * 32,
                 "job_bindings": [{"job_id": "job-a"}, {"job_id": "job-b"}]}))
            (root / "submission.json").write_text("{}")
            retained = root / "outcome.json"

            def interrupted(*_args, **_kwargs):
                subject.baseline._publish(str(retained), outcome)  # noqa: SLF001
                raise subject.baseline.SupervisorInterrupted("signal 2", outcome)

            stack.enter_context(mock.patch.object(jobs.JobStore, "open",
                                                  return_value=handles[0]))
            stack.enter_context(mock.patch.object(ControlStore, "open",
                                                  return_value=handles[1]))
            stack.enter_context(mock.patch.object(stage_execution,
                                                  "operations_from",
                                                  return_value=handles[2]))
            stack.enter_context(mock.patch.object(jobs, "submit"))
            stack.enter_context(mock.patch.object(subject, "supervise",
                                                  side_effect=interrupted))
            status = subject.main(
                ["--deployment", str(root / "deployment.json"),
                 "--submission", str(root / "submission.json"),
                 "--job-store", "unused", "--control-store", "unused",
                 "--incarnation", "regression", "--outcome", str(retained)],
                stream=said)

            self.assertEqual(status, 130)
            printed = said.getvalue()
            self.assertIn("interrupted: signal 2", printed)
            self.assertIn(f"the outcome WAS retained at {retained}", printed)
            # THE ORIGINAL CAUSE SURVIVES THE LAST EVENT -- and survives the unreadable
            # status that emptied `pipelines`, which is the property R2 asked for.
            self.assertIn("Job job-a had already FAILED", printed)
            self.assertIn("attempt attempt-a", printed)
            self.assertIn("provider-reported-oauth-session-expired-refresh-failed",
                          printed)
            self.assertIn("artifact://contracts/probe-a", printed)
            self.assertNotIn("Job job-b had already FAILED", printed)
            self.assertIn("state 'held', stopped 'interrupted'", printed)
            self.assertIn("1 held reason(s)", printed)
            self.assertIn("0 unresolved cleanup", printed)
            # AND THE OUTCOME ON DISK IS UNTOUCHED by the presentation.
            self.assertEqual(json.loads(retained.read_text()), outcome)
        for handle in handles:
            handle.close.assert_called_once()

    def test_an_ORDINARY_held_outcome_still_returns_1_and_a_fault_still_raises(self):
        """The catch is narrow: only the expected published interruption.

        A programming fault must stay visible, and a held run must stay a nonzero exit
        that is NOT the interrupted one.
        """
        from baton_v12.worker_manager import ControlStore
        from tools import stage_execution

        handles = [mock.Mock(), mock.Mock(), mock.Mock()]
        with tempfile.TemporaryDirectory(prefix="w306614-exit-") as root, \
                contextlib.ExitStack() as stack:
            root = Path(root)
            (root / "deployment.json").write_text(json.dumps(
                {"authority_uuid": "a" * 32,
                 "job_bindings": [{"job_id": "job-a"}, {"job_id": "job-b"}]}))
            (root / "submission.json").write_text("{}")
            stack.enter_context(mock.patch.object(jobs.JobStore, "open",
                                                  return_value=handles[0]))
            stack.enter_context(mock.patch.object(ControlStore, "open",
                                                  return_value=handles[1]))
            stack.enter_context(mock.patch.object(stage_execution,
                                                  "operations_from",
                                                  return_value=handles[2]))
            stack.enter_context(mock.patch.object(jobs, "submit"))
            operands = ["--deployment", str(root / "deployment.json"),
                        "--submission", str(root / "submission.json"),
                        "--job-store", "unused", "--control-store", "unused",
                        "--incarnation", "regression",
                        "--outcome", str(root / "outcome.json")]

            held = {"state": "held", "stopped": "pipelines-terminal"}
            with mock.patch.object(subject, "supervise", return_value=held):
                self.assertEqual(subject.main(operands, stream=io.StringIO()), 1)

            settled = {"state": "settled", "stopped": "pipelines-terminal"}
            with mock.patch.object(subject, "supervise", return_value=settled):
                self.assertEqual(subject.main(operands, stream=io.StringIO()), 0)

            with mock.patch.object(subject, "supervise",
                                   side_effect=ValueError("a programming fault")):
                with self.assertRaises(ValueError):
                    subject.main(operands, stream=io.StringIO())


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main(verbosity=2)
