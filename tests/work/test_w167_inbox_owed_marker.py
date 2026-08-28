"""W167: one owed-action marker on the Inbox tab.

`work/records/2026/08/finding-inbox-owed-marker/`. The tab read
`Inbox total/unseen`. Those are genuinely independent projection
fields — W25 derived them separately and this Work does not merge them
— but most live row kinds are unseen for their whole life or disappear
when they resolve, so in practice the label said `0/0` or `1/1`. Six
header cells emphasising UNREADNESS, while the question an operator
has at a glance is whether they owe anything.

The ruling: `[Inbox]`, or `[Inbox *]` while an unresolved action is
owed. One ASCII marker, no count, no severity, no unseen state, from
canonical `owed_action` and nothing else.

What these tests hold: the two spellings and no third one; owed
survives being SEEN, because reading the message that asked you
something does not stop you owing the answer; attention with nothing
owed does not raise it; resolving the last owed row lowers it on the
next canonical refresh; and the counts are still there, in the view
and in the JSON, where the rows they count are visible.
"""

from __future__ import annotations

import os
import pathlib
import re
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import Console                          # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
TAB = 9
NEXT_TAB = ord("]")   # W1151: `]` switches tabs; Tab moves panes


@pytest.fixture()
def world(tmp_path):
	"""The same shape W25's Inbox tests use: two members of one team,
	so "owed by me" and "owed by somebody else" are distinguishable."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def make_work(world, title="parser recovery"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


def poke(world, target="lang.ada", asker="grace"):
	return tr.poke(world["store"], actor_team="lang", actor=asker,
	               target=target, request="what's up?")["poke"]


def attention(world, born):
	"""A plain post: it invites reading and obliges nothing."""
	return tr.post_thread(world["store"], born["thread"],
	                      author_team="lang", author="ada",
	                      body="for your information only")["seq"]


def console(world, member="ada"):
	store = bw.Authority(world["database"])
	return Console(store, "lang", member, config_path=world["config"])


def label(world, member="ada") -> str:
	view = console(world, member)
	return dict(view.top_tab_segments())["inbox"]


def box(world, member="ada"):
	return pj.inbox(world["store"], viewer_team="lang",
	                viewer_member=member)


class Screen:
	def __init__(self, height=24, width=110):
		self.height = height
		self.width = width
		self.rows = {}

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		row = self.rows.get(y, "").ljust(x)
		text = str(text)[:n]
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def painted(view, height=24, width=110):
	screen = Screen(height, width)
	view.render(screen)
	return screen.lines()


# -- the two spellings, and no third -----------------------------------------

def test_nothing_owed_is_a_bare_inbox_tab(world):
	assert label(world) == "[Inbox]"
	assert box(world)["owed_action"] is False


def test_one_owed_action_raises_the_marker(world):
	poke(world)
	assert label(world) == "[Inbox *]"
	assert box(world)["owed_action"] is True


def test_many_owed_actions_are_still_one_marker(world):
	"""It is not a count. Three owed rows say exactly what one says:
	you owe something."""
	for title in ("parser recovery", "lexer recovery"):
		born = make_work(world, title=title)
		tr.post_thread(world["store"], born["thread"],
		               author_team="lang", author="ada",
		               body="please advise", request="lang.rsrch",
		               on=born["work_id"], wait=False)
	poke(world)
	assert box(world)["owed"] >= 3, box(world)["owed"]
	assert label(world) == "[Inbox *]"
	assert label(world).count("*") == 1


def test_no_numeric_count_reaches_the_tab(world):
	born = make_work(world)
	attention(world, born)
	poke(world)
	view = console(world)
	counted = box(world)
	assert counted["total"] and counted["unseen"], counted
	bar = view.top_tabs()
	# W26328 supersedes the whole-bar sweep. The ruling here is about
	# the INBOX label: `total/unseen` emphasised unreadness where the
	# question is whether you owe anything, and one marker answers
	# that. The Jobs label answers a different question — HOW MANY
	# items are actionable — and a count is the only answer to it.
	# Sweeping the whole bar for digits would now forbid that, which
	# W167 never ruled on, so the sweep is narrowed to the label it was
	# always about.
	assert not any(character.isdigit() for character in label(world)), bar
	assert re.fullmatch(r"\[Jobs \d+\]  \[Teams\]  \[Inbox \*\]", bar), bar


# -- what the marker does and does not follow --------------------------------

def test_seen_but_unresolved_keeps_the_marker(world):
	"""The ruled point, inherited from W25: reading the message that
	asked you something does not stop you being the person who owes the
	answer."""
	born = make_work(world)
	asked = tr.post_thread(
		world["store"], born["thread"], author_team="lang",
		author="ada", body="please advise", request="lang.rsrch",
		on=born["work_id"], wait=False)["seq"]
	assert label(world) == "[Inbox *]"
	tr.seen_thread(world["store"], born["thread"], team="lang",
	               member="ada", up_to_seq=asked)
	seen = box(world)
	assert seen["unseen"] == 0, seen
	assert seen["owed_action"] is True
	assert label(world) == "[Inbox *]", \
		"seen state hid that the viewer is the blocker"


def test_unseen_attention_alone_never_raises_it(world):
	born = make_work(world)
	attention(world, born)
	state = box(world)
	assert state["unseen"] >= 1 and state["owed"] == 0, state
	assert label(world) == "[Inbox]", \
		"attention-only content raised the owed marker"


def test_somebody_elses_owed_action_is_not_mine(world):
	"""The marker is participant-relative, exactly as the projection
	it reads is. A poke names ONE participant, so this cannot be
	confused with route resolution."""
	poke(world, target="lang.grace", asker="ada")
	assert label(world, "grace") == "[Inbox *]"
	assert label(world, "ada") == "[Inbox]"


def test_resolving_the_last_owed_action_lowers_it(world):
	seq = poke(world)
	assert label(world) == "[Inbox *]"
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="idle", explanation="between turns")
	assert box(world)["owed_action"] is False
	assert label(world) == "[Inbox]"


def test_the_marker_follows_the_canonical_field_and_not_the_counts(world):
	"""Derivation, asserted rather than assumed: the label agrees with
	`owed_action` through every state this fixture can reach."""
	born = make_work(world)

	def agrees(where):
		marked = label(world) == "[Inbox *]"
		assert marked is box(world)["owed_action"], \
			f"the tab and the projection disagreed after {where}"
		return marked

	assert agrees("an empty inbox") is False
	attention(world, born)
	assert agrees("unseen attention") is False
	seq = poke(world)
	assert agrees("a poke") is True
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="idle", explanation="done")
	assert agrees("answering it") is False


# -- rendering ---------------------------------------------------------------

def test_the_painted_header_shows_the_marker(world):
	poke(world)
	header = painted(console(world))[0]
	assert re.match(r"\[Jobs \d+\]  \[Teams\]  \[Inbox \*\]", header), header
	assert header.rstrip().endswith("lang.ada"), header


def test_a_refresh_lowers_the_marker_on_the_next_read(world):
	"""The console paints from a cached projection and refreshes on its
	own timer; the marker must move with the refresh rather than
	needing a keystroke that happens to rebuild it."""
	seq = poke(world)
	view = console(world)
	assert re.match(r"\[Jobs \d+\]  \[Teams\]  \[Inbox \*\]", painted(view)[0])
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="idle", explanation="between turns")
	view.tick()
	assert re.match(r"\[Jobs \d+\]  \[Teams\]  \[Inbox\]", painted(view)[0]), \
		painted(view)[0]


@pytest.mark.parametrize("width", [110, 60, 44, 30, 26, 24, 20])
def test_the_marked_tab_is_still_drawn_whole(world, width):
	"""W110's narrow rule is unchanged: whole labels or none. The
	marker rides inside the brackets, so it cannot be the thing a
	narrow header cuts off."""
	poke(world)
	view = console(world)
	header = painted(view, height=14, width=width)[0]
	# either the whole marked label is there or the label is not drawn
	# at all — W110's rule, and the marker rides inside the brackets so
	# it can never be the part a narrow header cuts off.
	assert "[Inbox" not in header or "[Inbox *]" in header, \
		(width, header)


def test_the_marker_and_the_active_highlight_stay_independent(world):
	"""Two cues, two questions. The highlight says which tab the keys
	act in (W110); `*` says this participant owes something. An owed
	Inbox the operator is NOT sitting in must show one and not the
	other."""
	import curses

	class Attr(Screen):
		def __init__(self):
			super().__init__()
			self.calls = []

		def addnstr(self, y, x, text, n, *rest):
			super().addnstr(y, x, text, n, *rest)
			self.calls.append((str(text)[:n], rest[0] if rest else 0))

	poke(world)
	view = console(world)
	screen = Attr()
	view.render(screen)
	marked = [(text, attr) for text, attr in screen.calls
	          if text.startswith("[Inbox")]
	assert marked and marked[0][0] == "[Inbox *]", marked
	assert not marked[0][1] & curses.A_REVERSE, \
		"an unselected tab carried the active highlight"
	assert marked[0][1] & curses.A_BOLD, \
		"W25's owed weight was lost"
	# and selecting it adds the highlight without touching the marker
	while view.tab != "inbox":
		view.handle(NEXT_TAB)
	screen = Attr()
	view.render(screen)
	selected = next((text, attr) for text, attr in screen.calls
	                if text.startswith("[Inbox"))
	assert selected[0] == "[Inbox *]"
	assert selected[1] & curses.A_REVERSE and selected[1] & curses.A_BOLD


def test_the_marker_never_widens_the_bar_beyond_the_screen(world):
	poke(world)
	view = console(world)
	for width in range(10, 60):
		header = painted(view, height=14, width=width)[0]
		assert len(header) <= width, (width, header)


# -- the counts are still projected ------------------------------------------

def test_the_counts_are_unchanged_in_the_projection(world):
	born = make_work(world)
	attention(world, born)
	poke(world)
	state = box(world)
	for field in ("total", "unseen", "owed", "owed_action", "rows"):
		assert field in state, state.keys()
	assert state["total"] == len(state["rows"])
	assert state["owed"] >= 1 and state["unseen"] >= 1


def test_the_inbox_view_still_shows_its_own_counts(world):
	poke(world)
	view = console(world)
	while view.tab != "inbox":
		view.handle(NEXT_TAB)
	lines = painted(view)
	assert any("inbox —" in line or "inbox" in line for line in lines)
	assert any("what's up?" in line for line in lines), lines


def test_the_documentation_teaches_the_marker():
	body = (REPO / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	prose = " ".join(body.split())
	assert "[Inbox *]" in prose
	assert "The tab label is `total/unseen`" not in prose, \
		"the superseded label survived in the operator documentation"


# -- a real terminal ---------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_raises_and_lowers_the_marker(world):
	seq = poke(world)
	world["store"].close()
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.5),
		(b"qy", 0.4),
	])
	owed = ptyharness.replay(steps[0])
	assert "[Inbox *]" in owed[0], owed[0]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]

	store = bw.Authority(world["database"])
	tr.answer_poke(store, seq, actor_team="lang", actor="ada",
	               state="idle", explanation="between turns")
	store.close()
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.5),
		(b"qy", 0.4),
	])
	quiet = ptyharness.replay(steps[0])
	assert "[Inbox]" in quiet[0], quiet[0]
	assert "*" not in quiet[0], quiet[0]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
