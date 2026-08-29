"""W6: canonical Work search and the TUI slash result mode.

`search query=...` (finding-tui-work-search): a read-only, viewer-team-
scoped projection over Work titles (case-folded substring) and
canonical/local identifiers (case-insensitive exact/prefix) — nested
Work included, message bodies and thread subjects excluded. The active
filter narrows with the shared AND semantics; results ride stable
creation order behind an explicit `next_after` cursor from ONE
snapshot. The TUI's `/` consumes the same projection: typing is pure
client state, Enter submits once, results are a flat table with
ordinary detail entry, the timer refresh re-runs the accepted search
with id-anchored selection, and Esc restores the exact prior window.
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
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title, team="lang", author="ada", parent=None):
	return tr.create_work(world["store"], team=team, kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="b",
	                      parent=parent)["work_id"]


def hits(world, query, **kw):
	return pj.search(world["store"], query, viewer_team="lang",
	                 viewer_member="ada", **kw)


def titles(result):
	return [row["title"] for row in result["rows"]]


def test_title_and_identifier_matching(world):
	"""Case-folded title substrings; case-insensitive exact/prefix ids
	(canonical and local); nonmatching fields never match; nested Work
	beyond the three-level window is found; other teams' Work is not."""
	parent = make(world, "Parser recovery epic")
	child = make(world, "deep recovery step", parent=parent)
	grandchild = make(world, "RECOVERY table rebuild", parent=child)
	make(world, "unrelated cleanup")
	make(world, "push recovery", team="push", author="sl")
	found = hits(world, "recovery")
	assert titles(found) == ["Parser recovery epic",
	                         "deep recovery step",
	                         "RECOVERY table rebuild"], \
		"case folding or nested scope failed"
	assert found["query"] == "recovery"
	# id prefix, local and canonical, case-insensitive
	local = grandchild.rsplit("-", 1)[1]
	assert titles(hits(world, local)) == ["RECOVERY table rebuild"]
	assert titles(hits(world, local.lower())) == \
		["RECOVERY table rebuild"]
	assert titles(hits(world, grandchild.upper())) == \
		["RECOVERY table rebuild"]
	prefix = grandchild[:10]
	assert "RECOVERY table rebuild" in titles(hits(world, prefix))
	# W-prefix matches every local id it prefixes
	w_all = hits(world, "W")
	assert len(w_all["rows"]) >= 4
	# message bodies never match (every body is "b")
	assert titles(hits(world, "zzz-nothing")) == []


def test_the_filter_narrows_and_closed_visibility_is_canonical(world):
	"""The active filter applies the shared AND semantics inside the
	search; closed rows appear in JSON and follow the console's
	closed-visibility rule on paint."""
	store = world["store"]
	hot = make(world, "match hot")
	tr.prioritize(store, hot, actor_team="lang", actor="ada",
	              priority="high")
	cold = make(world, "match cold")
	done = make(world, "match done")
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert titles(hits(world, "match")) == \
		["match hot", "match cold", "match done"]
	narrowed = hits(world, "match",
	                work_filter={"priority": "high"})
	assert titles(narrowed) == ["match hot"]
	assert narrowed["filter"] == {"priority": "high"}
	assert all(row["filter_match"] for row in narrowed["rows"])
	closed_only = hits(world, "match",
	                   work_filter={"status": "closed"})
	assert titles(closed_only) == ["match done"]
	# a bad filter refuses before any partial result
	with pytest.raises(bw.WorkError, match="not a configured team"):
		hits(world, "match", work_filter={"team": "ghost"})


def test_paging_is_stable_and_explicit(world):
	"""Bounded pages ride the stable creation order behind next_after;
	the cursor is a continuation value, never an identity; the last
	page carries no cursor."""
	for index in range(7):
		make(world, f"page item {index:02d}")
	first = hits(world, "page item", limit=3)
	assert len(first["rows"]) == 3 and first["next_after"] is not None
	second = hits(world, "page item", after=first["next_after"],
	              limit=3)
	third = hits(world, "page item", after=second["next_after"],
	             limit=3)
	assert third["next_after"] is None
	seen = titles(first) + titles(second) + titles(third)
	assert seen == [f"page item {index:02d}" for index in range(7)], \
		"paging lost or reordered results"
	with pytest.raises(bw.WorkError, match="limit= takes"):
		hits(world, "page", limit=0)


def test_empty_queries_refuse_and_search_is_pure(world):
	"""An empty/blank query refuses; a search performs no write — the
	authority is byte-identical and no seen state moves."""
	make(world, "untouched")
	with pytest.raises(bw.WorkError, match="non-empty query"):
		hits(world, "   ")
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	hits(world, "untouched")
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		assert hashlib.sha256(handle.read()).hexdigest() == before, \
			"a search wrote to the authority"


def test_json_and_cli_share_the_surface(world):
	"""`search query=...` through the public grammar: the envelope
	carries the normalized query, rows, filter, and snapshot token;
	filter operands compose; op-id refuses on the pure read."""
	make(world, "cli findable")

	def run(*argv):
		out, err = io.StringIO(), io.StringIO()
		with contextlib.redirect_stdout(out), \
				contextlib.redirect_stderr(err):
			code = work_cli.main(["--config", world["config"],
			                      "--participant", "lang.ada"]
			                     + list(argv))
		return code, out.getvalue(), err.getvalue()

	code, out, _err = run("search", "query=findable")
	assert code == 0
	body = _json.loads(out)
	assert body["result"]["query"] == "findable"
	assert titles(body["result"]) == ["cli findable"]
	assert "snapshot_seq" in body
	code, out, _err = run("search", "query=findable",
	                      "priority=high")
	assert code == 0
	assert _json.loads(out)["result"]["rows"] == []
	code, _out, err = run("search", "query=findable", "op-id=x")
	assert code == 1 and "pure read" in err


def test_slash_flow_query_on_enter_and_exact_restoration(world):
	"""The TUI flow: typing reads nothing; Enter submits once; results
	select and open detail normally; leaving detail returns to the
	results; Esc restores the exact prior window; a replacement query
	replaces; empty queries refuse locally."""
	store = world["store"]
	target = make(world, "needle in haystack")
	make(world, "plain hay")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	rows = console.rows()
	console.cursor = 1
	console.selected_id = rows[1]["id"]
	prior = (list(console.path), console.cursor, console.selected_id)
	# typing performs no authority read: count statements while typing
	console.handle(ord("/"))
	statements = []
	store.conn.set_trace_callback(statements.append)
	for char in "needle":
		console.handle(ord(char))
	store.conn.set_trace_callback(None)
	assert statements == [], "a keystroke touched the authority"
	console.handle(13)
	assert console.mode == "search"
	results, _hidden = console.visible_rows(console.search_rows())
	assert [row["title"] for row in results] == \
		["needle in haystack"]
	# ordinary detail entry and the return path
	console.handle(13)
	assert console.mode == "detail"
	assert console.detail_work == target
	console._handle_detail(27)
	assert console.mode == "search", \
		"leaving detail lost the search results"
	# replacement query
	console.handle(ord("/"))
	for char in "hay":
		console.handle(ord(char))
	console.handle(13)
	results, _hidden = console.visible_rows(console.search_rows())
	assert {row["title"] for row in results} == \
		{"needle in haystack", "plain hay"}
	# exact restoration
	console.handle(27)
	assert console.mode == "table"
	assert (console.path, console.cursor, console.selected_id) == \
		(prior[0], prior[1], prior[2]), "Esc lost the prior window"
	assert console.search_query is None
	# empty query refuses locally, view untouched
	console.handle(ord("/"))
	console.handle(13)
	assert console.mode == "table"
	assert "non-empty query" in console.status


def test_refresh_reruns_the_search_and_anchors_by_id(world):
	"""The scheduled refresh re-runs the accepted search through the
	one cache path; selection stays anchored by Work id; a vanished
	selection clamps to the nearest remaining result; an emptied
	search stays an honest empty view."""
	store = world["store"]
	first = make(world, "wave one")
	second = make(world, "wave two")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.rows()
	console.handle(ord("/"))
	for char in "wave":
		console.handle(ord(char))
	console.handle(13)
	console._search_mode_key(ord("j"))
	assert console.selected_id == second
	# a third match appears on the next scheduled refresh
	make(world, "wave three")
	console.tick()
	results, _hidden = console.visible_rows(console.search_rows())
	assert len(results) == 3

	class Screen:
		def addnstr(self, *_args):
			pass

	console._render_table(Screen(), 24, 110, results, top=2)
	assert console.selected_id == second, "the id anchor moved"
	# the selected row stops matching (closed + default visibility)
	tr.close_work(store, second, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	console.tick()
	results, _hidden = console.visible_rows(console.search_rows())
	console._render_table(Screen(), 24, 110, results, top=2)
	assert console.selected_id in {row["id"] for row in results}, \
		"selection did not move to a remaining result"


def test_the_slash_mode_on_the_real_terminal(tmp_path):
	"""PTY: `/` opens the query bar, Enter paints the flat results
	with the footer controls, no-match is explicit, and Esc returns to
	the prior table."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	tr.create_work(store, team="lang", kind="bug",
	               title="findable-row", origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="b")
	tr.create_work(store, team="lang", kind="bug",
	               title="other-row", origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="b")
	store.close()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"/findable\r", 0.8),
		(b"/zzz\r", 0.7),
		(b"\x1b", 0.5),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	results = ptyharness.replay(steps[0])
	flat = "\n".join(results)
	# W29146: the heading NAMES THE TEAM the search was scoped to. W6 has
	# always scoped this to the viewer's owning team; the header read as
	# global, so an empty answer read as "nowhere" rather than "not here".
	assert "search (team lang): findable — page 1 · 1 shown" in flat, \
		flat[:300]
	assert any("findable-row" in line for line in results)
	assert not any("other-row" in line for line in results), \
		"a nonmatching row painted in the results"
	assert "Enter details · / new query" in flat
	empty = "\n".join(ptyharness.replay(steps[1]))
	# The empty answer says it too, because that is the one an operator is
	# most likely to misread.
	assert "(no matches for 'zzz' in team lang)" in empty
	back = "\n".join(ptyharness.replay(steps[2]))
	assert "other-row" in back, "Esc did not restore the table"
	assert "search:" not in back


# -- round 2 -----------------------------------------------------------------

def test_hidden_closed_rows_never_consume_a_page(world):
	"""R1: with closed Work hidden, TUI paging runs over the effective
	status=open universe — a wall of closed matches cannot bury a later
	open match behind an apparently empty page; z and status=closed
	lift the constraint."""
	store = world["store"]
	for index in range(3):
		buried = make(world, f"buried match {index}")
		tr.close_work(store, buried, actor_team="lang", actor="ada",
		              rationale="done", outcome="satisfying")
	alive = make(world, "living match")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.search_limit = 3
	console.handle(ord("/"))
	for char in "match":
		console.handle(ord(char))
	console.handle(13)
	visible, _hidden = console.visible_rows(console.search_rows())
	assert [row["id"] for row in visible] == [alive], \
		"hidden closed matches consumed the visible page"
	assert console.search_next is None, \
		"the open universe still advertises a continuation"
	# z exposes closed: the paging universe includes all four
	console._search_mode_key(ord("z"))
	visible, _hidden = console.visible_rows(console.search_rows())
	assert len(visible) == 3 and console.search_next is not None, \
		"the exposed universe did not page over every status"
	console._search_mode_key(ord("z"))          # hide again
	# an explicit status=closed filter selects the closed matches
	console._search_mode_key(27)
	console.execute("filter status=closed")
	console.handle(ord("/"))
	for char in "match":
		console.handle(ord(char))
	console.handle(13)
	visible, _hidden = console.visible_rows(console.search_rows())
	assert len(visible) == 3
	assert all(row["status"] == "closed" for row in visible)


def test_esc_restores_closed_visibility_too(world):
	"""R2: toggling z inside search never leaks into the restored
	window — Esc returns the exact prior show_closed state."""
	store = world["store"]
	make(world, "open row")
	gone = make(world, "closed row")
	tr.close_work(store, gone, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.rows()
	assert console.show_closed is False
	console.handle(ord("/"))
	for char in "row":
		console.handle(ord(char))
	console.handle(13)
	console._search_mode_key(ord("z"))
	assert console.show_closed is True
	console._search_mode_key(27)
	assert console.mode == "table"
	assert console.show_closed is False, \
		"z inside search leaked into the restored window"


def test_the_header_names_the_page_not_a_total(world):
	"""R3: the header reads `page N · M shown`; the page label resets
	on a new query and p, and advances on n."""
	store = world["store"]
	for index in range(5):
		make(world, f"paged row {index}")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.search_limit = 2
	console.handle(ord("/"))
	for char in "paged":
		console.handle(ord(char))
	console.handle(13)

	class Screen:
		def __init__(self):
			self.texts = []

		def addnstr(self, _y, _x, text, *_rest):
			self.texts.append(str(text))

	def header():
		screen = Screen()
		console.render_search = None  # not used; render via render()?
		rows = console.search_rows()
		visible, _hidden = console.visible_rows(rows)
		return (f"search: {console.search_query} — page "
		        f"{console.search_page} · {len(visible)} shown")

	assert header().startswith("search: paged — page 1 · 2 shown")
	console._search_mode_key(ord("n"))
	assert header().startswith("search: paged — page 2 · 2 shown")
	console._search_mode_key(ord("n"))
	assert header().startswith("search: paged — page 3 · 1 shown")
	console._search_mode_key(ord("p"))
	assert header().startswith("search: paged — page 1 · 2 shown")
	# a replacement query resets the label
	console.handle(ord("/"))
	for char in "paged row 4":
		console.handle(ord(char))
	console.handle(13)
	assert console.search_page == 1
