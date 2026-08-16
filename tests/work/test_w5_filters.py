"""W5: composable Work-list filters over existing canonical facts.

One closed vocabulary (finding-work-project-filters, superseded to
team-as-project): team/status/phase/current/category/ready/new/priority,
AND composition, at most one value per field, no comma/negation/OR
dialects. The same operands ride `home`, `tree`, and `tui`; the
interactive `:filter` shares the grammar; bare `:filter` clears.
Filtering runs INSIDE the canonical snapshot after row facts project;
a matching child retains its nonmatching parent as `filter_match:false`
context; the team summary stays global; active filtering is always
disclosed. Client-local, restart-cold, authority untouched.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "grace": ["dev"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def run(world, *argv, viewer="lang.ada"):
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = work_cli.main(["--config", world["config"],
		                      "--participant", viewer] + list(argv))
	return code, out.getvalue(), err.getvalue()


def ok(world, *argv, viewer="lang.ada"):
	code, out, err = run(world, *argv, viewer=viewer)
	assert code == 0, err
	return _json.loads(out)["result"]


def refusal(world, *argv, viewer="lang.ada"):
	code, _out, err = run(world, *argv, viewer=viewer)
	assert code == 1
	return _json.loads(err)["error"]


def make(world, title="w", team="lang", author="ada", **kw):
	return tr.create_work(world["store"], team=team, kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="b", **kw)


def titles(result):
	return [row["title"] for row in result["rows"]]


def test_every_field_selects_and_composes_with_and(world):
	"""Each field filters on its canonical projected value; several
	fields intersect; the normalized filter echoes in the result."""
	store = world["store"]
	plain = make(world, "plain suspected")["work_id"]
	high = make(world, "high confirmed", priority="high")["work_id"]
	tr.classify(store, high, actor_team="lang", actor="ada",
	            classification="confirmed-defect")
	tr.claim_work(store, high, actor_team="lang", actor="ada")
	tr.set_phase(store, high, actor_team="lang", actor="ada",
	             phase="active")
	done = make(world, "closed out")["work_id"]
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert titles(ok(world, "home", "status=closed")) == ["closed out"]
	assert titles(ok(world, "home", "phase=active")) == \
		["high confirmed"]
	assert titles(ok(world, "home", "priority=high")) == \
		["high confirmed"]
	assert titles(ok(world, "home",
	                 "category=confirmed-defect")) == ["high confirmed"]
	assert "plain suspected" in titles(ok(world, "home",
	                                      "category=suspected-defect"))
	assert titles(ok(world, "home", "ready=true",
	                 "status=open", "priority=normal")) == \
		["plain suspected"]
	# W3 ordering: high ranks before normal in the canonical list
	assert titles(ok(world, "home", "team=lang", "status=open")) == \
		["high confirmed", "plain suspected"]
	echoed = ok(world, "home", "priority=high", "status=open")
	assert echoed["filter"] == {"status": "open", "priority": "high"}, \
		"the normalized filter is not echoed in canonical order"
	assert all(row["filter_match"] is True for row in echoed["rows"])
	# the team summary stays GLOBAL under any filter
	unfiltered = ok(world, "home")
	assert echoed["summary"] == unfiltered["summary"], \
		"filtering relabelled the global team summary"
	assert unfiltered["filter"] is None


def test_current_me_new_and_endpoint_filters(world):
	"""current=me needs the viewer among the RESOLVED handlers;
	current=TEAM.KIND matches the canonical endpoint; new=true tracks
	the viewer's personal New."""
	store = world["store"]
	mine = make(world, "current is lang")["work_id"]
	assert titles(ok(world, "home", "current=lang.bug")) == \
		["current is lang"]
	assert titles(ok(world, "home", "current=me")) == \
		["current is lang"]
	# grace is configured but NOT a resolved handler: me excludes
	assert titles(ok(world, "home", "current=me",
	                 viewer="lang.grace")) == []
	# personal New: ada authored (sees own message as seen after
	# mark? the born message is New until marked)
	view = pj.new_count(store, mine, viewer_team="lang",
	                    viewer_member="grace")
	assert view["total"] > 0
	assert titles(ok(world, "home", "new=true",
	                 viewer="lang.grace")) == ["current is lang"]
	born_thread = pj.work_threads(store, mine, viewer_team="lang",
	                              viewer_member="grace")["rows"][0]["id"]
	last = pj.thread(store, born_thread, viewer_team="lang",
	                 viewer_member="grace")["last_seq"]
	tr.seen_thread(store, born_thread, team="lang", member="grace",
	               up_to_seq=last)
	assert titles(ok(world, "home", "new=true",
	                 viewer="lang.grace")) == []
	assert titles(ok(world, "home", "new=false",
	                 viewer="lang.grace")) == ["current is lang"]


def test_refusals_come_before_any_partial_view(world):
	"""Unknown fields, duplicates, malformed booleans, compact display
	spellings, unknown teams and endpoints all refuse by name — no
	plausible partial rows."""
	make(world, "held")
	assert "unknown key 'project'" in refusal(world, "home",
	                                          "project=baton")
	assert "duplicate status=" in refusal(world, "home", "status=open",
	                                      "status=closed")
	assert "ready= takes one of" in refusal(world, "home",
	                                        "ready=maybe")
	assert "category= takes one of" in refusal(world, "home",
	                                           "category=defct")
	assert "priority= takes one of" in refusal(world, "home",
	                                           "priority=Hi")
	assert "phase= takes one of" in refusal(world, "home",
	                                        "phase=actve")
	assert "not a configured team" in refusal(world, "home",
	                                          "team=ghost")
	assert "neither a configured TEAM.KIND endpoint nor me" in \
		refusal(world, "home", "current=ghost.bug")
	assert "neither a configured TEAM.KIND endpoint nor me" in \
		refusal(world, "home", "current=nonsense")


def test_parent_context_retention_in_the_tree(world):
	"""The approved containment rule: a matching child retains its
	nonmatching parent as filter_match:false context; unrelated
	children disappear; a group with no match disappears whole; a
	matching parent keeps only matching children; depth and order are
	untouched."""
	store = world["store"]
	parent = make(world, "the parent")["work_id"]
	hot_child = tr.create_work(store, team="lang", kind="bug",
	                           title="hot child",
	                           origin="external-report",
	                           classification="suspected-defect",
	                           author="ada", body="b", parent=parent,
	                           priority="high")["work_id"]
	tr.create_work(store, team="lang", kind="bug", title="cold child",
	               origin="external-report",
	               classification="suspected-defect",
	               author="ada", body="b", parent=parent)
	make(world, "unrelated root")
	window = ok(world, "tree", "priority=high")
	got = [(row["title"], row["depth"], row["filter_match"])
	       for row in window["rows"]]
	assert got == [("the parent", 0, False), ("hot child", 1, True)], \
		got
	# a matching parent keeps only matching children
	high_parent = make(world, "high parent", priority="high")["work_id"]
	tr.create_work(store, team="lang", kind="bug", title="normal kid",
	               origin="external-report",
	               classification="suspected-defect",
	               author="ada", body="b", parent=high_parent)
	window = ok(world, "tree", "priority=high")
	got = [(row["title"], row["filter_match"]) for row in window["rows"]]
	assert ("high parent", True) in got
	assert all(title != "normal kid" for title, _match in got)
	assert all(title != "unrelated root" for title, _match in got)
	# a re-rooted window filters the same way
	rooted = ok(world, "tree", f"work={parent}", "priority=high")
	got = [(row["title"], row["depth"], row["filter_match"])
	       for row in rooted["rows"]]
	assert got == [("the parent", 0, False), ("hot child", 1, True)]


def test_startup_and_interactive_filters_are_one_surface(world):
	"""tui launch operands and :filter produce the same rows through
	the same grammar; replacement is atomic; bare :filter clears; a
	fresh console starts cold; a refused filter changes nothing."""
	store = world["store"]
	make(world, "stay normal")
	make(world, "go high", priority="high")
	launched = Console(store, "lang", "ada",
	                   config_path=world["config"],
	                   work_filter=pj.normalize_filter(
	                       store, {"priority": "high"}, "lang"))
	assert [row["title"] for row in launched.rows()] == ["go high"]
	interactive = Console(store, "lang", "ada",
	                      config_path=world["config"])
	interactive.execute("filter priority=high")
	assert interactive.status == "filter: priority=high"
	assert [row["title"] for row in interactive.rows()] == \
		[row["title"] for row in launched.rows()], \
		"startup and interactive filters diverged"
	# atomic replacement, not incremental accumulation
	interactive.execute("filter status=open")
	assert interactive.work_filter == {"status": "open"}
	assert {row["title"] for row in interactive.rows()} == \
		{"stay normal", "go high"}
	# a refusal leaves the current filter untouched
	interactive.execute("filter team=ghost")
	assert "not a configured team" in interactive.status
	assert interactive.work_filter == {"status": "open"}
	# bare :filter clears; a fresh console is cold (restart-cold)
	interactive.execute("filter")
	assert interactive.status == "filter cleared"
	assert interactive.work_filter is None
	fresh = Console(store, "lang", "ada", config_path=world["config"])
	assert fresh.work_filter is None


def test_filtering_is_pure_and_selection_stays_anchored(world):
	"""Applying and changing filters mutates no authority byte, and
	the id-anchored selection survives a filter that keeps the row."""
	store = world["store"]
	keep = make(world, "kept", priority="high")["work_id"]
	make(world, "dropped")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	rows = console.rows()
	console.cursor = next(index for index, row in enumerate(rows)
	                      if row["id"] == keep)
	console.selected_id = keep
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	console.execute("filter priority=high")
	filtered = console.rows()
	assert [row["id"] for row in filtered] == [keep]

	class Screen:
		def addnstr(self, *_args):
			pass

	console._render_table(Screen(), 24, 110, filtered, top=2)
	assert console.selected_id == keep, "the anchor moved"
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		assert hashlib.sha256(handle.read()).hexdigest() == before, \
			"view filtering touched the authority"


def test_the_tui_always_discloses_the_active_filter(tmp_path):
	"""PTY: Filter:N rides the header, the dedicated clause line shows
	the normalized clauses (viewported with an explicit mark at narrow
	widths), rows narrow accordingly, and clearing restores the full
	view."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	tr.create_work(store, team="lang", kind="bug", title="high-row",
	               origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="b", priority="high")
	tr.create_work(store, team="lang", kind="bug", title="normal-row",
	               origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="b")
	store.close()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b":filter priority=high\r", 0.8),
		(b":filter\r", 0.6),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	filtered = ptyharness.replay(steps[0])
	flat = "\n".join(filtered)
	assert "Filter:1" in flat, "the header does not disclose the filter"
	assert "filter: priority=high" in flat, \
		"the normalized clause line is missing"
	assert any("high-row" in line for line in filtered)
	assert not any("normal-row" in line for line in filtered), \
		"a filtered-out row still painted"
	cleared = ptyharness.replay(steps[1])
	flat = "\n".join(cleared)
	assert "Filter:" not in flat
	assert any("normal-row" in line for line in cleared), \
		"clearing did not restore the full view"


def test_narrow_disclosure_viewports_never_drops(tmp_path):
	"""PTY at 40 columns: a multi-clause filter still discloses —
	Filter:N in the header and the clause line present with an
	explicit viewport mark when clipped."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	tr.create_work(store, team="lang", kind="bug", title="target",
	               origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="b")
	store.close()
	command = (b":filter status=open category=suspected-defect "
	           b"ready=true priority=normal\r")
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(command, 0.9), (b"qy", 0.4)], columns=40, lines=20)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[0], columns=40, lines=20)
	flat = "\n".join(screen)
	assert "Filter:4" in flat
	clause_line = next(line for line in screen
	                   if line.startswith("filter: "))
	assert clause_line.endswith("…"), \
		"the clipped clause line lost its explicit viewport mark"
	assert any("target" in line for line in screen)


# -- round 2 -----------------------------------------------------------------

def test_status_closed_reveals_its_rows_despite_the_collapse(world):
	"""R1: an explicit status=closed filter shows exactly the closed
	rows it selected — the default collapse never erases the filter's
	answer — while the ordinary collapse still applies whenever no
	status filter requests closed Work."""
	store = world["store"]
	make(world, "stays open")
	done = make(world, "was finished")["work_id"]
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	# the ordinary default: closed rows collapse behind the count
	visible, hidden = console.visible_rows(console.rows())
	assert hidden == 1 and all(row["status"] == "open"
	                           for row in visible)
	console.execute("filter status=closed")
	visible, hidden = console.visible_rows(console.rows())
	assert hidden == 0
	assert [row["title"] for row in visible] == ["was finished"], \
		"the collapse erased the status=closed answer"
	# clearing restores the ordinary collapse
	console.execute("filter")
	_visible, hidden = console.visible_rows(console.rows())
	assert hidden == 1


def test_status_closed_paints_wide_and_narrow_with_context(tmp_path):
	"""R1 (PTY): a closed child under a nonmatching OPEN context parent
	paints at full and narrow widths under status=closed — the approved
	containment shape survives the collapse correction."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	parent = tr.create_work(store, team="lang", kind="bug",
	                        title="pa-open",
	                        origin="external-report",
	                        classification="suspected-defect",
	                        author="ada", body="b")["work_id"]
	child = tr.create_work(store, team="lang", kind="bug",
	                       title="kid-shut",
	                       origin="external-report",
	                       classification="suspected-defect",
	                       author="ada", body="b",
	                       parent=parent)["work_id"]
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	store.close()
	for columns, lines in ((110, 32), (60, 24)):
		text, status, steps = ptyharness.drive(config, "lang.ada", [
			(b":filter status=closed\r", 0.8), (b"qy", 0.4)],
			columns=columns, lines=lines)
		assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
		screen = ptyharness.replay(steps[0], columns=columns,
		                           lines=lines)
		assert any("kid-shut" in line for line in screen), \
			f"the closed match vanished at {columns} columns"
		assert any("pa-open" in line for line in screen), \
			f"the open context parent vanished at {columns} columns"


def test_space_seeds_the_current_clauses_for_editing(world):
	"""R2: after exact `filter`, the first SPACE seeds the buffer with
	the normalized clauses — one clause is edited without retyping the
	rest, Enter replaces atomically through the parser, and bare
	`:filter` + Enter still clears."""
	store = world["store"]
	make(world, "normal one")
	make(world, "high one", priority="high")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.execute("filter status=open priority=high")
	assert console.work_filter == {"status": "open",
	                               "priority": "high"}
	# open the bar, type `filter`, press space: the buffer seeds
	console.handle(ord(":"))
	for char in "filter":
		console.handle(ord(char))
	console.handle(ord(" "))
	assert console.command == "filter status=open priority=high", \
		"the space did not seed the current clauses"
	# edit ONLY the priority value: erase `high`, type `normal`
	for _erase in range(len("high")):
		console.handle(8)
	for char in "normal":
		console.handle(ord(char))
	console.handle(13)
	assert console.work_filter == {"status": "open",
	                               "priority": "normal"}, \
		"the edited clause did not replace atomically"
	assert [row["title"] for row in console.rows()] == ["normal one"]
	# bare :filter + Enter still clears
	console.handle(ord(":"))
	for char in "filter":
		console.handle(ord(char))
	console.handle(13)
	assert console.work_filter is None
	# without an active filter, space after `filter` stays literal
	console.handle(ord(":"))
	for char in "filter":
		console.handle(ord(char))
	console.handle(ord(" "))
	assert console.command == "filter "
	console.handle(27)
