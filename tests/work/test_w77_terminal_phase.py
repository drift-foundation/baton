"""W77: phase applies only to open Work (same-schema iteration).

Open Work exposes exactly one non-null canonical phase; closed Work
projects `phase: null` (present, never omitted — "not applicable") and
the TUI renders `-`. No `done` phase exists; the stored last-phase value
and the audit history stay untouched.
"""

from __future__ import annotations

import json as _json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield store, config_path
	store.close()


CLOSES = [("satisfying", {}), ("non-satisfying", {}),
          ("rejected", {}), ("cancelled", {})]


@pytest.mark.parametrize("outcome,extra", CLOSES)
def test_every_terminal_outcome_projects_phase_null(world, outcome, extra):
	store, _config = world
	work = tr.create_work(store, team="lang", kind="bug",
	                      title=f"{outcome} target",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="opener")["work_id"]
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="an audited phase move")
	before = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert before["phase"] == "parked"
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale=f"closed {outcome}", outcome=outcome,
	              **extra)
	after = pj.detail(store, work, viewer_team="lang",
	                  viewer_member="ada")
	assert "phase" in after and after["phase"] is None, \
		"a terminal row kept (or omitted) its phase"
	# The internal last-phase value is PRESERVED, not rewritten — the
	# null is projection-only.
	stored = store.conn.execute(
		"SELECT phase FROM work WHERE id=?", (work,)).fetchone()["phase"]
	assert stored == "parked", "the close rewrote stored history"
	# The audit keeps the open-phase transition and gains no phase
	# erasure event.
	kinds = [event["kind"] for event in store.events()]
	assert "set_phase" in kinds
	payloads = [event["payload"] for event in store.events()
	            if event["kind"] == "set_phase"]
	assert payloads[-1]["to"] == "parked"


def test_open_work_phase_stays_required_and_non_null(world):
	store, _config = world
	work = tr.create_work(store, team="lang", kind="bug",
	                      title="stays open", origin="external-report", classification="suspected-defect",
	                      author="ada", body="opener")["work_id"]
	view = pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")
	assert view["phase"] == "queued"
	rows = pj.home(store, viewer_team="lang",
	               viewer_member="ada")["rows"]
	assert all(row["phase"] is not None for row in rows
	           if row["status"] == "open")


def test_the_tui_renders_dash_for_closed_phase(world):
	"""JSON/TUI parity for the terminal case: the revealed closed row's
	Phase cell and the focused header both draw `-`."""
	store, config_path = world
	live = tr.create_work(store, team="lang", kind="bug",
	                      title="live row", origin="external-report", classification="suspected-defect",
	                      author="ada", body="live")
	done = tr.create_work(store, team="lang", kind="bug",
	                      title="done row", origin="external-report", classification="suspected-defect",
	                      author="ada", body="old")["work_id"]
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="finished", outcome="satisfying")

	from baton_work.tui import app
	json_row = next(row for row in pj.home(
		store, viewer_team="lang", viewer_member="ada")["rows"]
		if row["id"] == done)
	assert json_row["phase"] is None
	assert app.phase_cell(json_row["status"], json_row["phase"]) == "-"

	if not hasattr(_pty, "fork"):
		return
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"z", 0.5),                  # reveal the closed row
		(b"j", 0.4), (b"\r", 0.5),    # Enter opens the DETAIL view (W71)
		(b"qy", 0.4),
	])
	revealed = ptyharness.replay(steps[0])
	done_line = next(line for line in revealed if "done row" in line)
	cells = done_line.split()
	assert "-" in cells, f"the closed row's Phase is not '-': {done_line!r}"
	assert "rview" not in done_line, \
		"the closed row leaked its stored internal phase"
	focused = "\n".join(ptyharness.replay(steps[2]))
	assert "[c/sat/-/" in focused.replace("c/sat/", "c/sat/", 1) or \
		"/-/" in focused, \
		f"the focused header does not dash the phase: {focused[:300]}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_renderer_refuses_lifecycle_mismatched_phase(world):
	"""R1: the formatter is lifecycle-aware and fail-closed BOTH ways —
	an open row with null refuses visibly (never masquerading as
	closed), a closed row with a leaked phase refuses, and only
	closed+null yields the dash."""
	from baton_work.tui import app
	assert app.phase_cell("closed", None) == "-"
	with pytest.raises(ValueError, match="open work projects one"):
		app.phase_cell("open", None)
	with pytest.raises(ValueError, match="closed work projects phase"):
		app.phase_cell("closed", "queued")
	with pytest.raises(ValueError, match="no ruled compact"):
		app.phase_cell("open", "not-a-phase")
	# The renderer boundary itself: a malformed OPEN projection row
	# refuses at _row_cells rather than painting a lie.
	store, _config = world
	work = tr.create_work(store, team="lang", kind="bug",
	                      title="boundary", origin="external-report", classification="suspected-defect",
	                      author="ada", body="opener")["work_id"]
	row = next(entry for entry in pj.home(
		store, viewer_team="lang", viewer_member="ada")["rows"]
		if entry["id"] == work)
	malformed = dict(row, phase=None)   # doctored open row
	from baton_work.tui.app import Console
	console = Console(store, "lang", "ada")
	with pytest.raises(ValueError, match="open work projects one"):
		console._row_cells(malformed)
