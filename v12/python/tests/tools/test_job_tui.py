"""W386308: the read-only TUI, first slice -- the contract's numbered cases 1 to 17.

Cases 1 to 11, 13 and 15 to 17 drive the pure parts (`settle`, `step`, `frame`)
and `Session` with scripted keys and snapshot sequences; no terminal exists.
Cases 12 and 14 run the real program as a child. Case 12 allocates its OWN
pseudo-terminal and sets `TERM` itself, because a worker runs verification with
no terminal and a closed environment; it fails rather than skips when no
terminal description loads.

Every expected word is taken from `job_observation.job_view` for the same
document, never from a copied literal: the TUI adds no words of its own.
"""
import copy
import datetime
import json
import os
import pty
import select
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time
import unittest
from pathlib import Path

from tools import job_observation, job_tui, job_viewer, stack, stack_command

NOW = "2026-11-26T12:00:00.000Z"
EPOCH = datetime.datetime.fromisoformat(NOW.replace("Z", "+00:00")).timestamp()
_PYTHON = Path(__file__).resolve().parents[2]

A1_ATTEMPT = "attempt-5c8cded2904fc3d5832ec474e045dde81fa63a770b5903e97a07abff7af532a2"


def held_job(job_id="job-w385263-a1", hold="model-attribution-missing"):
    """The retained A1 shape: implementation held for the owner, review waiting on it."""
    runtime = {"model_attribution_hold": hold} if hold else {}
    return {"job_id": job_id, "stages": [
        {"stage_id": job_id + "/implementation", "state": "answering", "kind": "implementation",
         "attempt_id": A1_ATTEMPT, "episode": 1, "gates": [],
         "episodes": [{"attempt_id": A1_ATTEMPT, "episode": 1}],
         "allocation": {"assignment_id": A1_ATTEMPT, "episode": 1}, "runtime": runtime},
        {"stage_id": job_id + "/review", "state": "blocked", "kind": "review",
         "attempt_id": "attempt-review", "episode": 1,
         "gates": [{"open": False, "stage_id": job_id + "/implementation", "state": "answering"}],
         "episodes": [{"attempt_id": "attempt-review", "episode": 1}], "allocation": None}]}


def queued_job(job_id):
    return {"job_id": job_id, "stages": [
        {"stage_id": job_id + "/implementation", "state": "queued", "kind": "implementation",
         "attempt_id": None, "episode": None, "gates": [], "episodes": [], "allocation": None}]}


def running_job(job_id):
    attempt = "attempt-" + job_id
    return {"job_id": job_id, "stages": [
        {"stage_id": job_id + "/implementation", "state": "running", "kind": "implementation",
         "attempt_id": attempt, "episode": 1, "gates": [],
         "episodes": [{"episode": 1, "attempt_id": attempt}],
         "allocation": {"episode": 1, "assignment_id": attempt},
         "runtime": {"activity": {"attempt_id": attempt, "bytes_observed": 0, "observed_at": NOW}},
         "exchange": {"states": [{"operation": "work", "state": "dispatched"}]}}]}


def document(*jobs, observed_at=NOW, schema=None):
    return {"schema": schema or stack.STATUS_SCHEMA, "canonical": True, "observed_at": observed_at,
            "incarnation": "publisher", "jobs": [copy.deepcopy(job) for job in jobs]}


def seen(doc, job_id):
    job = next(one for one in doc["jobs"] if one["job_id"] == job_id)
    return job_observation.job_view(doc, job)


class Clocks:
    def __init__(self):
        self.now, self.wall = 100.0, EPOCH

    def advance(self, seconds):
        self.now += seconds
        self.wall += seconds


class Fed:
    """A source the test feeds: a document, raw bytes, or an exception to raise."""

    def __init__(self, first=None):
        self.next = first
        self.reads = 0

    def __call__(self):
        self.reads += 1
        if isinstance(self.next, BaseException):
            raise self.next
        return self.next


class Case(unittest.TestCase):
    def session(self, first=None):
        self.clocks = Clocks()
        self.fed = Fed(first)
        return job_tui.Session(self.fed, clock=lambda: self.clocks.now, wall=lambda: self.clocks.wall)

    def painted(self, session, rows=24, columns=100):
        return session.frame(rows, columns)

    def text(self, session, rows=24, columns=100):
        return "\n".join(self.painted(session, rows, columns).lines)

    def selected_line(self, session, rows=24, columns=100):
        painted = self.painted(session, rows, columns)
        self.assertIsNotNone(painted.selected, painted.lines)
        return painted.lines[painted.selected]


class PhaseRowWording(Case):
    def test_phase_progress_and_admission_have_distinct_words(self):
        job = held_job("job-a", hold=None)
        impl, review = job["stages"]
        for state, expected in (("running", "running"), ("claimed", "admitted · waiting for worker to start"),
                                ("waiting", "admitted"), ("completed", "done")):
            with self.subTest(state=state):
                impl["state"] = state
                phases = seen(document(job), "job-a")["phases"]
                self.assertEqual(phases[0]["row_position"], expected)
                self.assertEqual(phases[1]["row_position"], "waiting for implementation")
        impl.pop("allocation")
        impl["state"] = "running"
        self.assertIn("admission unknown", seen(document(job), "job-a")["phases"][0]["row_position"])


class TheList(Case):
    def test_case_01_one_row_per_job_with_headline_reason_and_counts(self):
        doc = document(running_job("job-run"), held_job("job-held"), queued_job("job-wait"))
        session = self.session(doc)
        session.read()
        lines = self.painted(session).lines
        headlines = {job_id: seen(doc, job_id) for job_id in ("job-run", "job-held", "job-wait")}
        self.assertEqual(sum(view["headline"] == job_tui.DECISION_NEEDED for view in headlines.values()), 1)
        self.assertIn("3 Jobs · 1 needs a decision", lines[0])
        rows = [line for line in lines if line[2:].startswith("job-")]
        self.assertEqual([row[2:].split()[0] for row in rows], ["job-run", "job-held", "job-wait"])
        for row, job_id in zip(rows, ("job-run", "job-held", "job-wait")):
            self.assertTrue(row.rstrip().endswith(headlines[job_id]["labelled_headline"]), row)
        reasons = [line.strip() for line in lines if line.startswith("    ")]
        self.assertEqual(reasons, [view["headline_reason"] for view in headlines.values() if view["headline_reason"]])
        self.assertEqual(len(reasons), 1)

    def test_case_02_the_retained_a1_case_carries_exactly_the_read_models_strings(self):
        doc = document(held_job())
        view = seen(doc, "job-w385263-a1")
        self.assertEqual(view["headline"], "DECISION NEEDED")
        session = self.session(doc)
        session.read()
        listed = self.painted(session, columns=120).lines
        self.assertIn(view["labelled_headline"], listed[3])
        self.assertEqual(listed[4].strip(), view["headline_reason"])
        session.key("open")
        detail = self.painted(session, rows=30, columns=160).lines
        self.assertEqual(detail[0], "job-w385263-a1   " + view["labelled_headline"])
        self.assertEqual(detail[2].strip(), view["headline_reason"])
        self.assertTrue(detail[3].strip().startswith(view["summary"] + " · Job age "), detail[3])
        body = [line.strip() for line in detail]
        implementation, review = view["phases"]
        self.assertIn("> " + implementation["role"].ljust(15) + " " + implementation["row_position"], detail)
        self.assertIn("  " + review["role"].ljust(15) + " " + review["row_position"], detail)
        for phase in (implementation, review):
            self.assertIn(phase["reason"], body)
        self.assertIn("attempt 1 " + A1_ATTEMPT + " · admitted", body)
        for fact in implementation["facts"]:
            self.assertIn(fact, body)
        self.assertIn(implementation["duration"] + " · " + implementation["timeout"] + " · activity "
                      + implementation["activity"] + " · operation " + implementation["operation"], body)
        self.assertIn(implementation["model_attribution"], body)

    def test_case_03_a_selected_job_that_comes_to_need_a_decision_changes_in_place(self):
        before = document(queued_job("job-a"), held_job("job-b", hold=None))
        after = document(queued_job("job-a"), held_job("job-b"))
        self.assertNotEqual(seen(before, "job-b")["headline"], job_tui.DECISION_NEEDED)
        session = self.session(before)
        session.read()
        session.key("down")
        self.assertEqual(session.state.job_id, "job-b")
        first = self.painted(session)
        self.assertIn("0 need a decision", first.lines[0])
        self.fed.next = after
        session.read()
        second = self.painted(session)
        self.assertEqual(session.state.job_id, "job-b")
        self.assertEqual(second.selected, first.selected)
        self.assertIn(seen(after, "job-b")["labelled_headline"], second.lines[second.selected])
        self.assertEqual(second.lines[second.selected + 1].strip(), seen(after, "job-b")["headline_reason"])
        self.assertIn("1 needs a decision", second.lines[0])

    def test_case_04_the_selection_follows_its_job_through_insertion_and_reordering(self):
        session = self.session(document(queued_job("job-a"), queued_job("job-b"), queued_job("job-c")))
        session.read()
        session.key("down")
        self.assertEqual(session.state.job_id, "job-b")
        for jobs in ((queued_job("job-new"), queued_job("job-a"), queued_job("job-b"), queued_job("job-c")),
                     (queued_job("job-c"), queued_job("job-b"), queued_job("job-new"), queued_job("job-a")),
                     tuple(queued_job("job-%02d" % index) for index in range(30)) + (queued_job("job-b"),)):
            self.fed.next = document(*jobs)
            session.read()
            self.assertEqual(session.state.job_id, "job-b")
            line = self.selected_line(session, rows=10)
            self.assertTrue(line.startswith("> job-b "), line)

    def test_case_05_a_vanished_job_is_one_line_and_never_stale_content(self):
        first = document(queued_job("job-a"), held_job("job-b"), queued_job("job-c"))
        session = self.session(first)
        session.read()
        session.key("down")
        self.fed.next = document(queued_job("job-a"), queued_job("job-c"))
        session.read()
        self.assertEqual(session.state.job_id, "job-b")
        text = self.text(session)
        self.assertEqual(self.selected_line(session), "> job-b" + job_tui.ABSENT)
        self.assertNotIn("DECISION NEEDED", text)
        self.assertNotIn(seen(first, "job-b")["headline_reason"], text)
        rows = [line[2:].split()[0] for line in self.painted(session).lines if line[2:].startswith("job-")]
        self.assertEqual(rows, ["job-a", "job-b", "job-c"])       # it keeps its place until the operator moves
        session.key("open")
        detail = self.painted(session).lines
        self.assertEqual(detail[0], "job-b" + job_tui.ABSENT)
        self.assertIn("Esc back", detail[-1])
        session.key("back")
        session.key("down")
        self.assertEqual(session.state.job_id, "job-c")
        self.assertNotIn("job-b", self.text(session))
        # and upward from the vanished row selects the neighbour above
        session = self.session(first)
        session.read()
        session.key("down")
        self.fed.next = document(queued_job("job-a"), queued_job("job-c"))
        session.read()
        session.key("up")
        self.assertEqual(session.state.job_id, "job-a")


class TheDetail(Case):
    def test_case_06_the_selected_phase_is_kept_and_a_vanished_one_is_one_line(self):
        job = held_job("job-a")
        session = self.session(document(job))
        session.read()
        session.key("open")
        session.key("down")
        self.assertEqual(session.state.stage_id, "job-a/review")
        changed = held_job("job-a")
        changed["stages"][0]["state"] = "completed"
        changed["stages"][0]["runtime"] = {}
        changed["stages"][1]["gates"][0].update(open=True, state="completed")
        changed["stages"][1]["state"] = "queued"
        after = document(changed)
        self.fed.next = after
        session.read()
        self.assertEqual(session.state.stage_id, "job-a/review")
        review = seen(after, "job-a")["phases"][1]
        self.assertEqual(self.selected_line(session, columns=160), "> " + review["role"].ljust(15) + " " + review["row_position"])
        gone = held_job("job-a")
        gone["stages"] = gone["stages"][:1]
        self.fed.next = document(gone)
        session.read()
        self.assertEqual(session.state.stage_id, "job-a/review")
        self.assertEqual(self.selected_line(session), "> job-a/review" + job_tui.ABSENT)
        self.assertNotIn(review["row_position"], self.text(session, columns=160))
        session.key("up")
        self.assertEqual(session.state.stage_id, "job-a/implementation")


def long_job(job_id="field-survey"):
    """A finished research phase with more recorded facts than a short screen holds."""
    def phase(name, attempt):
        return {"stage_id": job_id + "/" + name, "kind": "research", "state": "completed", "episode": 1,
                "attempt_id": attempt, "episodes": [{"episode": 1, "attempt_id": attempt}],
                "allocations": [{"assignment_id": attempt, "episode": 1, "worker_id": "field-research"}],
                "runtime": {"runtime_id": "runtime-" + name, "execution_runtime": "destroyed",
                            "model_attribution": "Requested: field-fixture; attribution: matched"},
                "artifacts": [{"output_name": "findings"}], "selected_at": NOW, "gates": [],
                "result": {"attempt_id": attempt, "locator": "file:///retained/" + name + "/findings"}}
    return {"job_id": job_id, "mode": "MANUAL", "lifecycle": "open",
            "budget": {"charged_seconds": 29, "limit_seconds": 360},
            "stages": [phase("guide", "attempt-guide"), phase("overview", "attempt-overview")]}


class TheDetailOfALongPhase(Case):
    """Review 2026-11-26T03-55-01Z [2]: a selected phase taller than the screen
    showed only its first lines, and no key reached the rest."""

    def setUp(self):
        self.doc = document(long_job(), schema=stack.MANUAL_STATUS_SCHEMA)
        self.view = seen(self.doc, "field-survey")
        self.guide = self.view["phases"][0]
        self.block = job_tui._phase_block(self.guide, True, 80, label="guide · research", label_width=19)  # as painted at 80 columns
        self.session = self.session(self.doc)
        self.session.read()
        self.session.key("open")

    def shown(self, rows=8, columns=80):
        return self.painted(self.session, rows, columns)

    def test_case_06_the_last_fact_of_a_tall_phase_is_reachable_and_the_phase_stays_selected(self):
        self.assertEqual(self.session.state.stage_id, "field-survey/guide")
        first = self.shown()
        height = 8 - (first.lines.index("") + 1) - 1     # the lines above the blank one, and the key line below
        self.assertEqual(height, 2)
        self.assertGreater(len(self.block), height)
        last_fact, attribution = "      " + self.guide["facts"][-1], "      " + self.guide["model_attribution"]
        self.assertNotIn(attribution, first.lines)
        self.assertNotIn(last_fact, first.lines)
        hidden = len(self.block) - height
        self.assertEqual(first.lines[-1], job_tui.SCROLL_KEYS % (0, hidden))      # the hint is on screen
        reached = set(first.lines)
        for pressed in range(1, hidden + 1):
            self.session.key("down")
            painted = self.shown()
            self.assertEqual(self.session.state.stage_id, "field-survey/guide", pressed)
            self.assertEqual(painted.lines[painted.selected], self.block[0])    # its own first line stays selected
            self.assertEqual(painted.lines[-1], job_tui.SCROLL_KEYS % (pressed, hidden - pressed))
            reached.update(painted.lines)
        for line in self.block:
            self.assertIn(line, reached)                                           # every line was shown at some point
        self.assertIn(last_fact, reached)
        self.assertIn(attribution, self.shown().lines)                            # and the very last line is on screen now
        # a refresh in the middle of it keeps both the phase and the place
        self.fed.next = copy.deepcopy(self.doc)
        self.session.read()
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", hidden))
        self.assertIn(attribution, self.shown().lines)
        # only now does ↓ leave the phase
        self.session.key("down")
        self.assertEqual(self.session.state.stage_id, "field-survey/overview")
        self.assertEqual(self.shown().lines[-1], job_tui.SCROLL_KEYS % (0, hidden))
        # ↑ returns to the phase above at its last lines, and on up to its first
        self.session.key("up")
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", hidden))
        for _ in range(hidden):
            self.session.key("up")
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", 0))
        self.assertEqual(self.shown().lines, first.lines)
        self.session.key("up")                                                    # nothing above the first phase
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", 0))

    def test_case_10_page_home_and_end_within_and_between_tall_phases(self):
        first = self.shown()
        hidden = len(self.block) - (8 - (first.lines.index("") + 1) - 1)
        self.session.key("pgdn")
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", min(hidden, 10)))
        self.session.key("pgup")
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", 0))
        self.shown()
        self.session.key("end")
        self.assertEqual(self.session.state.stage_id, "field-survey/overview")
        overview = "      " + self.view["phases"][1]["model_attribution"]
        self.assertIn(overview, self.shown().lines)                               # End shows the last phase's last line
        self.session.key("home")
        self.assertEqual((self.session.state.stage_id, self.session.state.stage_line), ("field-survey/guide", 0))
        self.session.key("end")
        self.session.key("pgup")
        self.assertEqual(self.session.state.stage_id, "field-survey/overview")
        # on a screen that holds everything nothing scrolls and the plain hint is back
        tall = self.shown(rows=40)
        self.assertEqual(tall.lines[-1], job_tui.DETAIL_KEYS)
        self.assertEqual(self.session.state.stage_line, 0)
        for line in job_tui._phase_block(self.view["phases"][1], True, 80, label="overview · research", label_width=19):
            self.assertIn(line, tall.lines)


class PhaseNames(Case):
    """W386361 acceptance cases; snapshots are deterministic, with no live provider."""

    def detail(self, job):
        doc = document(job, schema=stack.MANUAL_STATUS_SCHEMA)
        session = self.session(doc)
        session.read()
        session.key("open")
        return session, seen(doc, job["job_id"])["phases"]

    def test_case_01_manual_research_phases_have_distinct_names(self):
        session, phases = self.detail(long_job())
        lines = self.painted(session, rows=40).lines
        expected = ["> " + "guide · research".ljust(19) + " " + phases[0]["row_position"],
                    "  overview · research " + phases[1]["row_position"]]
        self.assertNotEqual(expected[0][2:], expected[1][2:])
        for row in expected:
            self.assertIn(row, lines)
            self.assertIn("research", row)
        # A named Job also aligns unnamed labels; short names keep the 15-column floor.
        job = queued_job("job-a")
        job["stages"].append(dict(job["stages"][0], stage_id="job-a/a", kind="research"))
        session, phases = self.detail(job)
        lines = self.painted(session).lines
        self.assertIn("> implementation  " + phases[0]["row_position"], lines)
        self.assertIn("  " + "a · research".ljust(15) + " " + phases[1]["row_position"], lines)
        job["stages"][1]["stage_id"] = "job-a/overview"
        session, phases = self.detail(job)
        self.assertIn("> " + "implementation".ljust(19) + " " + phases[0]["row_position"], self.painted(session).lines)

    def test_case_02_refresh_preserves_overview_identity_and_label(self):
        job = long_job()
        session, phases = self.detail(job)
        self.painted(session, rows=40)
        session.key("down")
        self.assertEqual(session.state.stage_id, "field-survey/overview")
        third = dict(job["stages"][0], stage_id="field-survey/extra")
        job["stages"] = [job["stages"][1], third, job["stages"][0]]
        self.fed.next = document(job, schema=stack.MANUAL_STATUS_SCHEMA)
        session.read()
        self.assertEqual(session.state.stage_id, "field-survey/overview")
        self.assertEqual(session.state.stage_at, 0)
        self.assertEqual(self.selected_line(session, rows=50), "> overview · research " + phases[1]["row_position"])

    def test_case_03_ordinary_rows_are_byte_equal(self):
        session, phases = self.detail(held_job("job-a"))
        lines = self.painted(session).lines
        for mark, phase in zip(("> ", "  "), phases):
            old = mark + phase["role"].ljust(15) + " " + phase["row_position"]
            self.assertIn(old.encode(), [line.encode() for line in lines])
            self.assertNotIn("·", old)

    def test_case_04_missing_invalid_and_role_only_ids_keep_old_row(self):
        for identity in ("research", None, 42, [], {}, "", "unknown", "job-a/", "job-a/unknown"):
            with self.subTest(stage_id=identity):
                job = queued_job("job-a")
                phase = job["stages"][0]
                phase["kind"] = "research"
                if identity is None:
                    del phase["stage_id"]
                else:
                    phase["stage_id"] = identity
                session, phases = self.detail(job)
                row = self.selected_line(session)
                self.assertEqual(row.encode(), ("> " + "research".ljust(15) + " " + phases[0]["row_position"]).encode())
                self.assertNotIn("·", row)

    def test_case_05_prefixed_role_is_not_duplicated(self):
        job = queued_job("job-a")
        job["stages"][0].update(stage_id="job-a/research", kind="research")
        session, phases = self.detail(job)
        self.assertEqual(self.selected_line(session), "> " + "research".ljust(15) + " " + phases[0]["row_position"])

    def test_case_06_foreign_prefix_is_shown_whole(self):
        for identity in ("job-ab/overview", "other/overview", "overview", "job-a"):
            with self.subTest(stage_id=identity):
                job = queued_job("job-a")
                job["stages"][0].update(stage_id=identity, kind="research")
                session, phases = self.detail(job)
                self.assertEqual(self.selected_line(session), "> " + (identity + " · research").ljust(15) + " " + phases[0]["row_position"])

    def test_case_07_long_name_is_ellipsized_without_wrapping(self):
        job = queued_job("job-a")
        job["stages"][0].update(stage_id="job-a/" + "long-name-" * 12, kind="research")
        session, _ = self.detail(job)
        painted = self.painted(session, columns=60)
        self.assertEqual(painted.lines[painted.selected], ("> " + "long-name-" * 12)[:59] + "…")
        self.assertEqual(sum("long-name" in line for line in painted.lines), 1)
        self.assertTrue(all(len(line) <= 60 for line in painted.lines))

    def test_case_08_tall_phase_keeps_named_first_line_pinned(self):
        session, phases = self.detail(long_job())
        first = self.painted(session, rows=8)
        expected = "> " + "guide · research".ljust(19) + " " + phases[0]["row_position"]
        self.assertEqual(first.lines[first.selected], expected)
        session.key("down")
        second = self.painted(session, rows=8)
        self.assertEqual(second.lines[second.selected], expected)
        self.assertEqual(session.state.stage_id, "field-survey/guide")
        self.assertEqual(session.state.stage_line, 1)
        self.assertNotEqual(first.lines[first.selected + 1], second.lines[second.selected + 1])

    def test_case_09_vanished_named_phase_keeps_absent_line(self):
        job = long_job()
        session, _ = self.detail(job)
        job["stages"] = job["stages"][1:]
        self.fed.next = document(job, schema=stack.MANUAL_STATUS_SCHEMA)
        session.read()
        self.assertEqual(session.state.stage_id, "field-survey/guide")
        self.assertEqual(self.selected_line(session), "> field-survey/guide — not in the current snapshot")

    def test_case_10_named_labels_leave_other_phase_lines_and_list_unchanged(self):
        job = long_job()
        session, phases = self.detail(job)
        lines = self.painted(session, rows=40).lines
        old_block = job_tui._phase_block(phases[0], True, 100)
        at = lines.index("> " + "guide · research".ljust(19) + " " + phases[0]["row_position"])
        self.assertEqual(list(lines[at + 1:at + len(old_block)]), old_block[1:])
        session.key("back")
        before = self.painted(session).lines
        for phase in job["stages"]:
            phase["stage_id"] = "field-survey/research"
        self.fed.next = document(job, schema=stack.MANUAL_STATUS_SCHEMA)
        session.read()
        self.assertEqual(self.painted(session).lines, before)


class Freshness(Case):
    def test_case_07_stale_at_fifteen_seconds_on_both_screens_and_fresh_again(self):
        session = self.session(document(held_job("job-a")))
        session.read()
        for screen in ("list", "detail"):
            if screen == "detail":
                session.key("open")
            self.clocks.now, self.clocks.wall = 100.0, EPOCH + 14
            self.fed.next = document(held_job("job-a"))
            session.read()
            self.assertNotIn("STALE", self.text(session))
            self.assertIn("observed " + NOW + " (14s old)", self.painted(session).lines[1])
            self.clocks.wall = EPOCH + 15
            said = self.painted(session).lines[1]
            self.assertEqual(said, "!! STALE observed 15s ago; observed " + NOW)
            later = (datetime.datetime.fromtimestamp(EPOCH + 15, datetime.timezone.utc)
                     .isoformat(timespec="milliseconds").replace("+00:00", "Z"))
            self.fed.next = document(held_job("job-a"), observed_at=later)
            session.read()
            self.assertNotIn("STALE", self.text(session))
        # Reading the same old observation again does not make it fresh.
        self.clocks.wall = EPOCH + 600
        session.read()
        self.assertIn("!! STALE", self.painted(session).lines[1])
        self.assertEqual(job_observation.STALE_SECONDS, 15.0)

    def test_case_08_a_failed_read_says_why_and_keeps_the_last_good_content(self):
        good = document(held_job("job-a"))
        malformed = document(held_job("job-a"))
        malformed["jobs"].append("not a Job")
        unknown = document(held_job("job-a"), schema="baton.v12.job-status/999")
        failures = (FileNotFoundError(2, "No such file or directory"),
                    b'{"schema": "baton.v12.job-status/9", "jobs": [',
                    b" " * (job_viewer.MAX_SNAPSHOT_BYTES + 1),
                    json.dumps(unknown).encode(), json.dumps(malformed).encode())
        for failure in failures:
            with self.subTest(failure=repr(failure)[:40]):
                session = self.session(good)
                session.read()
                kept = self.painted(session).lines[3:6]
                self.clocks.advance(7)
                self.fed.next = failure
                session.read()
                painted = self.painted(session, columns=260)
                self.assertEqual(painted.lines[1], "!! DISCONNECTED last read 7s ago; observed " + NOW + "; "
                                 + str(session.snapshot.failure))
                self.assertTrue(str(session.snapshot.failure))
                # on a narrow terminal the cause is what is cut, never the ages
                self.assertTrue(self.painted(session, columns=60).lines[1].startswith(
                    "!! DISCONNECTED last read 7s ago; observed 2026-11-26T12:00"))
                self.assertEqual(self.painted(session).lines[3:6], kept)
                session.key("open")
                self.assertTrue(self.painted(session).lines[1].startswith("!! DISCONNECTED "))
                self.fed.next = good
                session.read()
                self.assertNotIn("DISCONNECTED", self.text(session))

    def test_case_09_no_status_file_at_start_says_not_read_yet_and_stays_up(self):
        session = self.session(FileNotFoundError(2, "No such file or directory"))
        first = self.painted(session)
        self.assertEqual(first.lines[1], "not read yet")
        self.assertIn("0 Jobs · 0 need a decision", first.lines[0])
        self.assertIn("no snapshot has been read", "\n".join(first.lines))
        session.read()
        said = self.painted(session).lines[1]
        self.assertTrue(said.startswith("not read yet"), said)
        self.assertIn("FileNotFoundError", said)
        for key in ("down", "open", "back", "next", "read"):
            session.key(key)
        self.assertFalse(session.state.quit)
        self.fed.next = document(held_job("job-a"))
        session.read()
        self.assertIn("job-a", self.text(session))


class Keys(Case):
    def test_case_10_every_key_at_the_top_middle_and_bottom_and_unknown_keys(self):
        jobs = [queued_job("job-a"), held_job("job-b"), queued_job("job-c"), held_job("job-d"), queued_job("job-e")]
        session = self.session(document(*jobs))
        session.read()
        self.assertEqual(session.state.job_id, "job-a")
        moves = (("up", "job-a"), ("down", "job-b"), ("down", "job-c"), ("end", "job-e"), ("down", "job-e"),
                 ("up", "job-d"), ("home", "job-a"), ("pgdn", "job-e"), ("pgup", "job-a"))
        for key, expected in moves:
            session.key(key)
            self.assertEqual(session.state.job_id, expected, key)
        # n: the next Job needing a decision, in snapshot order, wrapping once
        for expected in ("job-b", "job-d", "job-b"):
            session.key("next")
            self.assertEqual(session.state.job_id, expected)
        before = session.state
        for unknown in (None, "x", "tab", 7):
            self.assertEqual(session.key(unknown), before)
        self.assertEqual(session.key("back"), before)             # nowhere to go back to on the list
        session.key("open")
        self.assertEqual((session.state.screen, session.state.stage_id), ("detail", "job-b/implementation"))
        for key, expected in (("up", "job-b/implementation"), ("down", "job-b/review"), ("down", "job-b/review"),
                              ("home", "job-b/implementation"), ("end", "job-b/review")):
            session.key(key)
            self.assertEqual(session.state.stage_id, expected, key)
        held = session.state
        self.assertEqual(session.key("next"), held)               # n belongs to the list
        session.key("back")
        self.assertEqual((session.state.screen, session.state.job_id), ("list", "job-b"))
        reads = self.fed.reads
        session.key("read")
        self.assertEqual(self.fed.reads, reads + 1)
        # n with one, and with none
        one = self.session(document(queued_job("job-a"), held_job("job-b")))
        one.read()
        for _ in range(2):
            one.key("next")
            self.assertEqual(one.state.job_id, "job-b")
        none = self.session(document(queued_job("job-a"), queued_job("job-b")))
        none.read()
        self.assertEqual(none.key("next").job_id, "job-a")
        self.assertTrue(session.key("quit").quit)
        # the terminal's key codes
        import curses
        for code, name in ((curses.KEY_UP, "up"), (ord("k"), "up"), (curses.KEY_DOWN, "down"), (ord("j"), "down"),
                           (curses.KEY_PPAGE, "pgup"), (curses.KEY_NPAGE, "pgdn"), (curses.KEY_HOME, "home"),
                           (curses.KEY_END, "end"), (10, "open"), (curses.KEY_ENTER, "open"), (curses.KEY_RIGHT, "open"),
                           (27, "back"), (curses.KEY_LEFT, "back"), (curses.KEY_BACKSPACE, "back"), (127, "back"),
                           (ord("n"), "next"), (ord("r"), "read"), (ord("q"), "quit"), (3, "quit"),
                           (ord("x"), None), (curses.KEY_F1, None), (-1, None)):
            self.assertEqual(job_tui.key_name(code, curses), name, code)

    def test_case_11_narrow_wide_long_and_resized_terminals_keep_the_selection(self):
        long_reason = held_job("job-" + "x" * 70)
        jobs = [queued_job("job-%02d" % index) for index in range(40)] + [long_reason]
        session = self.session(document(*jobs))
        session.read()
        for _ in range(25):
            session.key("down")
        self.assertEqual(session.state.job_id, "job-25")
        for rows, columns in ((24, 60), (12, 200), (9, 61), (40, 100), (8, 60)):
            painted = self.painted(session, rows, columns)
            self.assertEqual(len(painted.lines), rows)
            self.assertTrue(all(len(line) <= columns for line in painted.lines), (rows, columns))
            self.assertTrue(painted.lines[painted.selected].startswith("> job-25 "), (rows, columns))
            self.assertEqual(session.state.job_id, "job-25")
        session.key("end")
        narrow = self.painted(session, 24, 60)
        self.assertTrue(narrow.lines[narrow.selected].endswith("…"))
        self.assertTrue(narrow.lines[narrow.selected + 1].endswith("…"))      # the reason is cut, not wrapped
        self.assertEqual(len(narrow.lines[narrow.selected + 1]), 60)
        # the offset moves only when it has to
        session.key("home")
        top = self.painted(session, 12, 100).state.job_top
        session.key("down")
        self.assertEqual(self.painted(session, 12, 100).state.job_top, top)
        small = self.painted(session, 7, 100)
        self.assertEqual(small.lines[0], "terminal too small: needs 60x8")
        self.assertIsNone(small.selected)
        self.assertTrue(self.painted(session, 24, 59).lines[0].startswith("terminal too small"))
        self.assertTrue(self.selected_line(session, 24, 100).startswith("> job-01 "))


def _terminal():
    """The first terminal description that loads, or a failure -- never a skip."""
    for name in ("xterm", "vt100", "linux", "ansi"):
        done = subprocess.run([sys.executable, "-c", "import curses,sys;curses.setupterm(sys.argv[1],1)", name],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if done.returncode == 0:
            return name
    raise AssertionError("no terminal description loads for xterm, vt100, linux or ansi; "
                         "the clean-exit cases cannot run here and are not skipped")


def _environment(term=None):
    held = {"PATH": "/usr/bin:/bin", "PYTHONPATH": "src:.", "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"}
    if term:
        held["TERM"] = term
    return held


class TheRealProgram(unittest.TestCase):
    def setUp(self):
        self._room = tempfile.TemporaryDirectory(prefix="v12-job-tui-")
        self.addCleanup(self._room.cleanup)
        self.status = os.path.join(self._room.name, "status.json")
        with open(self.status, "w") as stream:
            json.dump(document(held_job()), stream)

    def under_a_terminal(self, *, send=None, sign=None, size=None, expect=b"DECISION NEEDED"):
        term = _terminal()
        master, slave = pty.openpty()
        if size is not None:
            import fcntl
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", size[0], size[1], 0, 0))
        self.addCleanup(lambda: [os.close(fd) for fd in (master, slave) if _open(fd)])
        before = termios.tcgetattr(slave)

        def controlling():
            os.setsid()
            import fcntl
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        child = subprocess.Popen([sys.executable, "-B", "-m", "tools.job_tui", "--status", self.status],
                                 stdin=slave, stdout=slave, stderr=slave, cwd=str(_PYTHON),
                                 env=_environment(term), preexec_fn=controlling)
        drawn, deadline = b"", time.monotonic() + 20
        while expect not in drawn and time.monotonic() < deadline:
            if select.select([master], [], [], 0.2)[0]:
                try:
                    drawn += os.read(master, 65536)
                except OSError:
                    break
        self.assertIn(expect, drawn, "the program never drew what was expected")
        self.drawn = drawn
        if send is not None:
            os.write(master, send)
        if sign is not None:
            child.send_signal(sign)
        deadline = time.monotonic() + 20
        while child.poll() is None and time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    os.read(master, 65536)
                except OSError:
                    pass
        if child.poll() is None:
            child.kill()
            child.wait()
            self.fail("the program did not exit")
        self.assertEqual(termios.tcgetattr(slave), before, "terminal attributes were not restored")
        with self.assertRaises(ProcessLookupError):                 # no child of its own is left behind
            os.killpg(child.pid, 0)
        return child.returncode

    def test_case_12_q_ctrl_c_and_sigterm_restore_the_terminal_and_leave_nothing(self):
        self.assertEqual(self.under_a_terminal(send=b"q"), 0)
        self.assertEqual(self.under_a_terminal(send=b"\x03"), 0)
        self.assertEqual(self.under_a_terminal(sign=signal.SIGTERM), 128 + signal.SIGTERM)

    def test_case_11_the_real_program_accepts_exactly_60_by_8_and_refuses_one_less(self):
        """Review 2026-11-26T03-55-01Z [1]: the loop laid out one column short, so
        a terminal of exactly the stated minimum was told it was too small."""
        self.assertEqual(self.under_a_terminal(send=b"q", size=(job_tui.MIN_ROWS, job_tui.MIN_COLUMNS)), 0)
        self.assertIn(b"job-w385263-a1", self.drawn)
        self.assertNotIn(b"terminal too small", self.drawn)
        for rows, columns in ((job_tui.MIN_ROWS, job_tui.MIN_COLUMNS - 1), (job_tui.MIN_ROWS - 1, job_tui.MIN_COLUMNS)):
            self.assertEqual(self.under_a_terminal(send=b"q", size=(rows, columns), expect=b"terminal too small"), 0)
            self.assertNotIn(b"DECISION NEEDED", self.drawn)

    def test_case_14_without_a_terminal_it_refuses_with_exit_2_and_draws_nothing(self):
        done = subprocess.run([sys.executable, "-B", "-m", "tools.job_tui", "--status", self.status],
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60,
                              cwd=str(_PYTHON), env=_environment())
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertEqual(done.stdout, "")
        self.assertIn("refused: the TUI needs a terminal", done.stderr)
        self.assertIn("monitor", done.stderr)


def _open(fd):
    try:
        os.fstat(fd)
        return True
    except OSError:
        return False


class ItOnlyReads(Case):
    def test_case_13_a_whole_session_opens_only_the_status_file_read_only(self):
        with tempfile.TemporaryDirectory(prefix="v12-job-tui-") as room:
            status = os.path.join(room, "status.json")
            with open(status, "w") as stream:
                json.dump(document(held_job("job-a"), queued_job("job-b")), stream)

            def whole_session():
                clocks = Clocks()
                session = job_tui.Session(job_tui.source_from(status), clock=lambda: clocks.now, wall=lambda: clocks.wall)
                for key in ("read", "down", "open", "down", "read", "back", "next", "up", "read"):
                    session.key(key)
                    session.frame(24, 100)
                    clocks.advance(6)
                    if session.due():
                        session.read()
                return session

            whole_session()                     # once unobserved, so lazy imports are not mistaken for reads
            events, watching = [], [True]

            def audit(event, args):
                if watching[0] and event in ("open", "sqlite3.connect", "subprocess.Popen", "os.remove",
                                             "os.rename", "os.mkdir", "os.rmdir", "socket.connect", "os.truncate"):
                    events.append((event, args))

            sys.addaudithook(audit)
            before = sorted(os.listdir(room))
            try:
                session = whole_session()
            finally:
                watching[0] = False
            self.assertGreaterEqual(len(events), 3)
            for event, args in events:
                self.assertEqual(event, "open", (event, args))
                self.assertIsInstance(args[0], str, args)
                self.assertEqual(args[0], status)
                flags = args[2] if len(args) > 2 and isinstance(args[2], int) else os.O_RDONLY
                self.assertEqual(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND), 0, args)
            self.assertEqual(sorted(os.listdir(room)), before)
            self.assertEqual(session.state.screen, "list")


class WhatItIsBuiltOn(Case):
    def test_case_15_manual_jobs_show_the_read_models_labelled_headline_and_counts(self):
        opened = queued_job("study-open")
        opened.update(mode="MANUAL", lifecycle="open", budget={"charged_seconds": 3, "limit_seconds": 60})
        opened["stages"][0].update(kind="research", selected_at=None)
        closed = queued_job("study-closed")
        closed.update(mode="MANUAL", lifecycle="closed", closed_at=NOW)
        closed["stages"][0].update(kind="research", selected_at=None)
        doc = document(opened, closed, schema=stack.MANUAL_STATUS_SCHEMA)
        session = self.session(doc)
        session.read()
        text = self.text(session, columns=120)
        for job_id in ("study-open", "study-closed"):
            view = seen(doc, job_id)
            self.assertTrue(view["labelled_headline"].startswith("MANUAL"), view["labelled_headline"])
            self.assertIn(view["labelled_headline"], text)
        self.assertIn("    " + seen(doc, "study-closed")["headline_reason"], text)
        self.assertIn("never selected", seen(doc, "study-closed")["headline_reason"])
        session.key("down")
        session.key("open")
        detail = self.painted(session, columns=120).lines
        self.assertEqual(detail[0], "study-closed   " + seen(doc, "study-closed")["labelled_headline"])
        self.assertIn(seen(doc, "study-closed")["summary"], detail[3])

    def test_case_16_it_edits_nothing_it_is_built_on_and_is_reachable_beside_monitor(self):
        source = (_PYTHON / "tools" / "job_tui.py").read_text()
        for private in ("job_viewer._", "job_observation._", "sqlite3", "subprocess", "socket"):
            self.assertNotIn(private, source, private)
        for name in ("job_view", "job_age"):
            self.assertIn("job_observation." + name, source)
        self.assertIn("tui", stack_command.COMMANDS)
        self.assertIn("monitor", stack_command.COMMANDS)
        from unittest import mock
        with mock.patch.object(job_tui, "main", return_value=0) as entered:
            self.assertEqual(stack.main(["--root", "/srv/state", "tui", "--interval", "2"]), 0)
        entered.assert_called_once_with(["--status", str(stack.snapshot_path("/srv/state")), "--interval", "2.0"])
        with mock.patch.object(stack, "main", return_value=0) as entered:
            stack_command.COMMANDS["tui"](["--instance", "/srv/d/instance.json", "--interval", "9"])
        entered.assert_called_once_with(["--instance", "/srv/d/instance.json", "tui", "--interval", "9"])

    def test_case_17_a_review_held_for_its_report_shows_the_read_models_sentence(self):
        job = held_job("job-a", hold=None)
        job["stages"][0].update(state="completed", runtime={})
        job["stages"][1].update(
            state="answering", gates=[{"open": True, "stage_id": "job-a/implementation", "state": "completed"}],
            allocation={"assignment_id": "attempt-review", "episode": 1},
            attempt_diagnostics={"schema": "baton.v12.attempt-failure-cause/1", "attempt_id": "attempt-review",
                                 "worker_declaration": {"review_report": {"known": True, "value": "missing"}}})
        doc = document(job)
        review = seen(doc, "job-a")["phases"][1]
        self.assertEqual(review["reason"], "Review held: review report missing")
        session = self.session(doc)
        session.read()
        session.key("open")
        session.key("down")
        lines = self.painted(session, columns=120).lines
        at = lines.index("> " + review["role"].ljust(15) + " " + review["row_position"])
        self.assertEqual(lines[at + 1].strip(), review["reason"])


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
