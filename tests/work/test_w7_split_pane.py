"""W7: split-pane Work and Thread navigation (same-schema iteration).

The ruled model: the top pane stays the Work table; the bottom pane shows
Msgs for the Work highlighted above. Enter keeps its ONE stable meaning
(drill into child Work) — a leaf's communication is already visible below,
never behind an empty drill. Tab moves focus; changing the highlight marks
nothing seen; the pane defaults to the thread with personal New; threads
stay distinct and explicitly switchable; only the explicit `s` writes.
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
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


@pytest.fixture()
def world(tmp_path):
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	first = tr.create_work(store, team="lang", kind="bug",
	                       title="first leaf", origin="external-report",
	                       author="ada", body="first opener")
	second = tr.create_work(store, team="lang", kind="bug",
	                        title="second leaf",
	                        origin="external-report", author="ada",
	                        body="second opener")
	tr.post_thread(store, second["thread"], author_team="lang",
	               author="ada", body="the second conversation body")
	cast = {"config": config_path, "first": first, "second": second,
	        "database": result["database"]}
	store.close()
	return cast


def test_the_home_screen_previews_the_highlighted_work(world):
	"""The bottom pane follows the highlight: the first row's Msgs by
	default, the second row's after j — and VIEWING marks nothing."""
	store = bw.Authority(world["database"])
	before = pj.new_count(store, world["second"]["work_id"],
	                      viewer_team="lang",
	                      viewer_member="grace")["total"]
	assert before > 0
	store.close()

	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"", 0.5),                   # the default split screen
		(b"j", 0.5),                  # highlight the second work
		(b"q", 0.4),
	])
	first = "\n".join(ptyharness.replay(steps[0]))
	assert "Msgs T1/1 — first leaf" in first, first[:600]
	assert "first opener" in first
	assert "second conversation" not in first
	second = "\n".join(ptyharness.replay(steps[1]))
	assert "Msgs T1/1 — second leaf" in second
	assert "the second conversation body" in second
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	store = bw.Authority(world["database"])
	after = pj.new_count(store, world["second"]["work_id"],
	                     viewer_team="lang",
	                     viewer_member="grace")["total"]
	store.close()
	assert after == before, "previewing marked messages seen"


def test_a_leaf_never_needs_an_empty_drill(world):
	"""Enter keeps its stable drill meaning; the drilled leaf's empty
	child table still shows the leaf's own Msgs below."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.5),                 # drill into the (leaf) first work
		(b"q", 0.4),
	])
	screen = "\n".join(ptyharness.replay(steps[0]))
	assert "(no work here)" in screen, "the drill lost its meaning"
	assert "Msgs T1/1 — first leaf" in screen, \
		"a leaf's communication is hidden behind the empty drill"
	assert "first opener" in screen
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_tab_focuses_the_pane_and_s_marks_the_painted_page(world):
	"""Tab moves focus; in the focused pane only the explicit s writes,
	bounded by the painted page; Tab-focus alone writes nothing."""
	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"j", 0.4),                  # highlight the second work
		(b"\t", 0.4),                 # focus the Msgs pane
		(b"s", 0.5),                  # THE explicit seen write
		(b"q", 0.4),
	])
	focused = "\n".join(ptyharness.replay(steps[1]))
	assert "[msgs focused — Tab returns]" in focused
	marked = "\n".join(ptyharness.replay(steps[2]))
	assert "seen up to #" in marked
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	store = bw.Authority(world["database"])
	remaining = pj.new_count(store, world["second"]["work_id"],
	                         viewer_team="lang",
	                         viewer_member="grace")["total"]
	store.close()
	assert remaining == 0, "the explicit s did not commit the cursor"


def test_the_preview_defaults_to_the_new_bearing_thread(world):
	"""The ruled default: the pane opens on the thread carrying the
	viewer's personal New; j under focus switches to the other DISTINCT
	thread — never merged."""
	store = bw.Authority(world["database"])
	extra = tr.create_thread(
		store, actor_team="lang", actor="ada",
		body="second-thread evidence",
		labels=[world["first"]["work_id"]],
		subject="the follow-up questions")
	# grace has seen the born thread but not the new one.
	tr.seen_thread(store, world["first"]["thread"], team="lang",
	               member="grace", up_to_seq=store.last_seq())
	store.close()

	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"", 0.5),                   # default: the New-bearing thread
		(b"\t", 0.4),                 # focus the pane
		(b"k", 0.5),                  # switch UP to the born thread
		(b"q", 0.4),
	])
	default = "\n".join(ptyharness.replay(steps[0]))
	assert "Msgs T2/2 — the follow-up questions" in default, \
		default[:600]
	assert "second-thread evidence" in default
	switched = "\n".join(ptyharness.replay(steps[2]))
	assert "Msgs T1/2 — first leaf" in switched, \
		"threads are not explicitly switchable"
	assert "first opener" in switched
	assert "second-thread evidence" not in switched, \
		"switching merged two threads"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_threads_beyond_the_bounded_page_stay_reachable(world):
	"""R1: with more threads than one bounded page, the default
	selection still finds personal New on a LATER page, the honest
	total shows N+ while pages remain, and focused k walks back across
	the page boundary."""
	from baton_work.tui import app
	store = bw.Authority(world["database"])
	for index in range(app.DISC_PAGE + 1):
		last = tr.create_thread(
			store, actor_team="lang", actor="ada",
			body=f"conversation {index + 2} opener",
			labels=[world["first"]["work_id"]],
			subject=f"conversation {index + 2:02d}")
	# grace has seen everything EXCEPT the final thread (page two).
	for thread_id in [world["first"]["thread"]] + [
			row["id"] for row in __import__("baton_work.projection",
			fromlist=["projection"]).work_threads(
				store, world["first"]["work_id"], viewer_team="lang",
				viewer_member="grace", limit=100)["rows"]
			if row["id"] != last["thread"]]:
		tr.seen_thread(store, thread_id, team="lang", member="grace",
		               up_to_seq=store.last_seq())
	store.close()

	total = app.DISC_PAGE + 2
	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"", 0.6),                   # default: New on page TWO
		(b"\t", 0.4),                 # focus the pane
		(b"k", 0.5),                  # within page two: T11
		(b"k", 0.5),                  # cross BACK over the boundary: T10
		(b"q", 0.4),
	])
	default = "\n".join(ptyharness.replay(steps[0]))
	assert f"Msgs T{total}/{total} — conversation {total:02d}" \
		in default, default[:600]
	within = "\n".join(ptyharness.replay(steps[2]))
	assert f"Msgs T{total - 1}/{total} — conversation {total - 1:02d}" \
		in within
	back = "\n".join(ptyharness.replay(steps[3]))
	assert f"Msgs T{app.DISC_PAGE}/{app.DISC_PAGE}+ — " \
		f"conversation {app.DISC_PAGE:02d}" in back, \
		"k did not walk back across the bounded page boundary"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_a_short_terminal_never_focuses_an_invisible_pane(world):
	"""R2: below MIN_SPLIT_HEIGHT no pane is painted, so Tab must not
	move focus — j keeps selecting Work rows and Enter drills the row
	the human sees highlighted."""
	from baton_work.tui import app
	short = app.MIN_SPLIT_HEIGHT - 2
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\t", 0.4),                 # must be inert: nothing to focus
		(b"j", 0.4),                  # selects the SECOND work row
		(b"\r", 0.5),                 # drills it
		(b"q", 0.4),
	], lines=short)
	flat = "\n".join(ptyharness.replay(steps[0], lines=short))
	assert "Msgs" not in flat, "a pane painted below the minimum height"
	drilled = ptyharness.replay(steps[2], lines=short)
	assert "second leaf" in drilled[0], \
		f"keys were routed to an invisible pane: {drilled[:3]}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
