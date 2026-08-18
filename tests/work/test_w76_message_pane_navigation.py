"""W76 (finding-message-pane-navigation): spatial panes, newest first.

Two live defects. The Message index opened OLDEST first, so entering a
conversation showed its beginning rather than what just happened. And
`Ctrl-W` treated the three panes as one linear tuple, so reaching
Threads from the reader required stepping through the index — the
model was three panels, the navigation was a list.

The newest-first entry is also a purity fix: the old path could walk
forward through every bounded page hunting the first personal-new
Message, loading an entire Thread to reach its tail. Because the seen
cursor is a MONOTONIC sequence, the newest Message is itself unseen
whenever anything is, so one bounded read of the newest page lands on
new mail without the walk.
"""

from __future__ import annotations

import curses
import json as _json
import os
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
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402


class Screen:
	def __init__(self):
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		self.calls.append((y, x, str(text)))

	def lines(self):
		return [text for _y, _x, text in self.calls]


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store, "database": database}
	store.close()


def conversation(world, count=25):
	store = world["store"]
	born = tr.create_work(store, team="lang", kind="bug", title="talk",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="message 00")
	seqs = [born["seq"]]
	for index in range(1, count):
		seqs.append(tr.post_thread(
			store, born["thread"], author_team="lang", author="ada",
			body=f"message {index:02d}")["seq"])
	return born, seqs


def console_at(world, member="ada", height=14, width=100):
	console = Console(world["store"], "lang", member,
	                  config_path=world["config"])
	console.detail_work = console.rows()[0]["id"]
	console.mode = "detail"
	console._render_detail(Screen(), height, width)
	return console


# -- newest-first entry and bounded paging ----------------------------------

def test_entry_opens_the_newest_message_in_one_bounded_read(world):
	_born, seqs = conversation(world)
	reads = []
	original = pj.thread

	def counted(*args, **kw):
		reads.append(kw.get("before", "newest") if kw.get("newest")
		             else kw.get("before"))
		return original(*args, **kw)

	pj_thread = pj.thread
	try:
		pj.thread = counted
		console = console_at(world)
	finally:
		pj.thread = pj_thread
	assert console.msg_cursor == seqs[-1], \
		"entry did not select the newest Message"
	assert len(reads) == 1, \
		f"entry read {len(reads)} pages; it must be exactly one bounded " \
		f"read, never a walk toward the tail"


def test_the_index_is_ordered_newest_first(world):
	_born, seqs = conversation(world)
	console = console_at(world)
	screen = Screen()
	console._render_detail(screen, 14, 100)
	rows = [line.split()[0] for line in screen.lines()
	        if line.startswith("M") and line[1:2].isdigit()]
	assert rows, "no index rows painted"
	numbers = [int(label[1:]) for label in rows]
	assert numbers == sorted(numbers, reverse=True), \
		f"the index is not newest-first: {rows}"
	assert numbers[0] == seqs[-1]


def test_entry_lands_on_unseen_mail_without_hunting_for_it(world):
	"""The monotonic-cursor argument, tested rather than asserted."""
	born, seqs = conversation(world)
	tr.seen_thread(world["store"], born["thread"], team="lang",
	               member="grace", up_to_seq=seqs[3])
	console = console_at(world, member="grace")
	assert console.msg_cursor == seqs[-1]
	page = pj.thread(world["store"], born["thread"], viewer_team="lang",
	                 viewer_member="grace", newest=True, limit=5)
	chosen = next(m for m in page["messages"]
	              if m["seq"] == console.msg_cursor)
	assert chosen["new"] is True, \
		"the newest Message was not unseen while unseen mail existed"


def test_paging_moves_toward_older_and_p_returns_to_newest(world):
	_born, seqs = conversation(world)
	console = console_at(world)
	newest_page = list(console.viewed_seqs)
	assert console.viewed_next_before is not None, \
		"a long thread did not disclose an older page"
	console.focus = "index"
	console.handle(ord("n"))
	console._render_detail(Screen(), 14, 100)
	older_page = list(console.viewed_seqs)
	assert older_page and not set(older_page) & set(newest_page)
	assert max(older_page) < min(newest_page), \
		f"n paged toward newer messages: {older_page}"
	console.handle(ord("p"))
	console._render_detail(Screen(), 14, 100)
	assert list(console.viewed_seqs) == newest_page, \
		"p did not return to the newest page"


def test_an_exactly_full_newest_page_does_not_invent_an_older_page(world):
	"""A full page is not proof that another row exists. The cursor is a
	promise to the TUI, so an exact-limit Thread must not advertise `n` and
	then open an empty older page."""
	born, _seqs = conversation(world, count=5)
	page = pj.thread(world["store"], born["thread"], viewer_team="lang",
	                 viewer_member="ada", newest=True, limit=5)
	assert len(page["messages"]) == 5
	assert page["next_before"] is None, \
		"an exact-limit page invented an empty older continuation"


def test_an_exact_limit_before_page_does_not_invent_another(world):
	"""The same boundary on the OLDER-direction cursor: paging to a
	`before=` page that exactly exhausts the remaining Messages must end
	the chain rather than advertise one more."""
	born, seqs = conversation(world, count=6)
	first = pj.thread(world["store"], born["thread"], viewer_team="lang",
	                  viewer_member="ada", newest=True, limit=3)
	assert [m["seq"] for m in first["messages"]] == seqs[3:]
	assert first["next_before"] == seqs[3]
	older = pj.thread(world["store"], born["thread"], viewer_team="lang",
	                  viewer_member="ada", before=first["next_before"],
	                  limit=3)
	assert [m["seq"] for m in older["messages"]] == seqs[:3]
	assert older["next_before"] is None, \
		"the last older page invented another continuation"


def test_following_every_older_cursor_never_opens_an_empty_page(world):
	"""The cursor is a promise: walking it to exhaustion must visit only
	non-empty pages, for a Thread whose length is an exact multiple of
	the page size and for one that is not."""
	for count, limit in ((9, 3), (10, 3), (5, 5), (1, 4)):
		born, seqs = conversation(world, count=count)
		page = pj.thread(world["store"], born["thread"],
		                 viewer_team="lang", viewer_member="ada",
		                 newest=True, limit=limit)
		visited = []
		while True:
			assert page["messages"], \
				f"an older cursor opened an EMPTY page (count={count}, " \
				f"limit={limit})"
			assert len(page["messages"]) <= limit, \
				"a page exceeded its own limit"
			visited.extend(m["seq"] for m in page["messages"])
			if page["next_before"] is None:
				break
			page = pj.thread(world["store"], born["thread"],
			                 viewer_team="lang", viewer_member="ada",
			                 before=page["next_before"], limit=limit)
		assert sorted(visited) == seqs, \
			f"walking the older cursors lost or repeated Messages " \
			f"(count={count}, limit={limit})"


def test_the_probe_row_never_reaches_the_payload(world):
	"""Reading limit+1 is an implementation detail: the page itself is
	still exactly `limit` long and canonical ascending."""
	born, seqs = conversation(world, count=12)
	page = pj.thread(world["store"], born["thread"], viewer_team="lang",
	                 viewer_member="ada", newest=True, limit=4)
	got = [m["seq"] for m in page["messages"]]
	assert got == seqs[-4:], got
	assert got == sorted(got), "the payload left canonical ascending order"


def test_index_movement_follows_the_visible_order(world):
	"""Screen-down selects an OLDER Message; screen-up a newer one."""
	_born, seqs = conversation(world)
	console = console_at(world)
	console.focus = "index"
	start = console.msg_cursor
	console.handle(ord("j"))
	console._render_detail(Screen(), 14, 100)
	assert console.msg_cursor < start, "down did not move to an older Message"
	console.handle(ord("k"))
	console._render_detail(Screen(), 14, 100)
	assert console.msg_cursor == start, "up did not return to the newer one"


def test_cursor_keys_follow_the_same_visible_message_order(world):
	"""Cursor keys are first-class aliases, not a pane-only accident."""
	_born, _seqs = conversation(world)
	console = console_at(world)
	console.focus = "index"
	start = console.msg_cursor
	console.handle(curses.KEY_DOWN)
	console._render_detail(Screen(), 14, 100)
	assert console.msg_cursor < start
	console.handle(curses.KEY_UP)
	console._render_detail(Screen(), 14, 100)
	assert console.msg_cursor == start


# -- geometric pane navigation ----------------------------------------------

CTRL_W = 23


def move(console, key):
	console.handle(CTRL_W)
	console.handle(key)
	return console.focus


@pytest.mark.parametrize("start,key,expected", [
	# up from EITHER message pane reaches Threads directly — the defect
	("reader", ord("k"), "threads"),
	("index", ord("k"), "threads"),
	("threads", ord("j"), "index"),
	("index", ord("j"), "reader"),
	("index", ord("l"), "reader"),
	("reader", ord("h"), "index"),
	# unmapped edges stay put
	("threads", ord("k"), "threads"),
	("reader", ord("j"), "reader"),
	("threads", ord("h"), "threads"),
	("threads", ord("l"), "threads"),
	("index", ord("h"), "index"),
	("reader", ord("l"), "reader"),
	# Every vi direction has an exactly equivalent cursor-key spelling.
	("reader", curses.KEY_UP, "threads"),
	("index", curses.KEY_UP, "threads"),
	("threads", curses.KEY_DOWN, "index"),
	("index", curses.KEY_DOWN, "reader"),
	("index", curses.KEY_RIGHT, "reader"),
	("reader", curses.KEY_LEFT, "index"),
	("threads", curses.KEY_UP, "threads"),
	("reader", curses.KEY_DOWN, "reader"),
	("threads", curses.KEY_LEFT, "threads"),
	("threads", curses.KEY_RIGHT, "threads"),
	("index", curses.KEY_LEFT, "index"),
	("reader", curses.KEY_RIGHT, "reader"),
])
def test_the_geometric_neighbour_map(world, start, key, expected):
	conversation(world, count=4)
	console = console_at(world)
	console.focus = start
	assert move(console, key) == expected


def test_a_second_ctrl_w_still_cycles_all_three(world):
	conversation(world, count=4)
	console = console_at(world)
	console.focus = "threads"
	seen = [console.focus]
	for _ in range(3):
		seen.append(move(console, CTRL_W))
	assert seen == ["threads", "index", "reader", "threads"], seen


def test_exactly_one_pane_is_marked_focused(world):
	conversation(world, count=4)
	console = console_at(world)
	for pane in ("threads", "index", "reader"):
		console.focus = pane
		screen = Screen()
		console._render_detail(screen, 14, 100)
		marked = [line for line in screen.lines() if line.startswith("»")]
		assert len(marked) == 1, \
			f"focus {pane} painted {len(marked)} markers: {marked}"


def test_an_empty_thread_still_marks_exactly_one_pane(world):
	store = world["store"]
	tr.create_work(store, team="lang", kind="bug", title="quiet",
	               origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="only opener")
	console = console_at(world)
	console.focus = "reader"
	screen = Screen()
	console._render_detail(screen, 14, 100)
	marked = [line for line in screen.lines() if line.startswith("»")]
	assert len(marked) == 1, marked


def test_focus_and_layout_survive_a_resize(world):
	conversation(world, count=6)
	console = console_at(world)
	console.focus = "reader"
	chosen = console.msg_cursor
	console._render_detail(Screen(), 14, 44)     # narrow stack
	assert console.focus == "reader", "the resize dropped pane focus"
	assert console.msg_cursor == chosen, "the resize moved the selection"
	# the same logical map applies in the narrow geometry
	assert move(console, ord("k")) == "threads"


# -- purity ------------------------------------------------------------------

def test_no_navigation_advances_the_seen_cursor(world):
	born, seqs = conversation(world)
	store = world["store"]
	before_new = pj.thread(store, born["thread"], viewer_team="lang",
	                       viewer_member="ada")["new"]
	before_seq = store.last_seq()
	console = console_at(world)
	for key in (CTRL_W, ord("j"), CTRL_W, ord("k"), ord("j"), ord("k"),
	            ord("n"), ord("p"), CTRL_W, ord("l"), ord("j")):
		console.handle(key)
		console._render_detail(Screen(), 14, 100)
	after = pj.thread(store, born["thread"], viewer_team="lang",
	                  viewer_member="ada")
	assert after["new"] == before_new, \
		"navigation advanced the seen cursor"
	assert store.last_seq() == before_seq, \
		"navigation wrote to the authority"


def test_explicit_s_still_bounds_at_the_selected_message(world):
	born, seqs = conversation(world)
	store = world["store"]
	console = console_at(world, member="grace")
	console.focus = "index"
	console.handle(ord("j"))          # one OLDER than the newest
	console._render_detail(Screen(), 14, 100)
	chosen = console.msg_cursor
	assert chosen == seqs[-2]
	console.handle(ord("s"))
	view = pj.thread(store, born["thread"], viewer_team="lang",
	                 viewer_member="grace")
	assert view["new"] == 1, \
		"s did not stop at the selected Message"
	assert view["messages"][-1]["seq"] == seqs[-1]
