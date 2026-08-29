"""W26328 — the console half: the tab count, the `Mine` column, `m`.

`work/records/2026/08/finding-actionable-work-discovery/`.

The authority half is in `test_w26328_actionable_discovery.py`. This one holds
what an OPERATOR can see, which is where the finding's defect actually bites:
the Jobs tab never said how much awaited them, the containment window is three
levels deep, and a claimable Work on the fourth had no row, no count and no
locator anywhere in the console.

Three surfaces, three different jobs, and the separation is deliberate:

  `[Jobs N]`      the total, always spelled — `[Jobs 0]` is an answer
  `Mine`          where it is, on the containment tree the operator is reading
  `m`             the flat list of every one, with the complete path to each

`Mine` is on the ordinary containment tree and NOWHERE else. On the flattened
page every row is actionable by definition, so a column saying so of all of
them tells no two rows apart; in search and the dependency graph the question
is not "what can I claim".
"""

from __future__ import annotations

import os
import pathlib
import pty as _pty
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui import app                                 # noqa: E402
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402


@pytest.fixture()
def world(tmp_path):
	"""Two members of one team. The generated Route hands `main` to
	`ada` alone, so `grace` is a real viewer for whom nothing is
	actionable — which is what makes the zero cases mean something."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def make(world, title="parser recovery", parent=None):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener",
	                      parent=parent)["work_id"]


def chain(world, depth, prefix="level"):
	"""One containment chain, root-first. Anything past the third level
	is outside the tree window — which is the finding."""
	made, parent = [], None
	for level in range(depth):
		parent = make(world, f"{prefix} {level}", parent)
		made.append(parent)
	return made


def console(world, member="ada"):
	store = bw.Authority(world["database"])
	return Console(store, "lang", member, config_path=world["config"])


def jobs_label(view) -> str:
	return dict(view.top_tab_segments())["jobs"]


def counted(world, member="ada") -> int:
	return pj.tree(world["store"], None, viewer_team="lang",
	               viewer_member=member)["actionable_for_viewer"]


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


def header_of(lines):
	return next(line for line in lines if "Title" in line)


def cells(lines, label):
	"""One drawn column's cells, sliced at the painted header's own
	offsets — the same source of truth the human reads."""
	header = header_of(lines)
	at = header.index(label)
	# The column runs to the next HEADING, which is where the painter
	# put it: `" " + label.ljust(width)` per column, so the next label
	# starts exactly one cell past this column's end.
	after = [found.start() for found in re.finditer(r"\S+", header)
	         if found.start() > at]
	width = (after[0] - 1 - at) if after else len(header) - at
	body = lines[lines.index(header) + 1:]
	out = []
	for line in body:
		if not line.strip() or line.startswith(("(", "Enter ")):
			continue
		out.append(line.ljust(len(header))[at:at + width].strip())
	return out


# -- the tab: the total, always spelled --------------------------------------

class TestTheJobsTabAlwaysSpellsTheCount:
	"""The label carries a NUMBER, unlike Inbox's and Teams's `*`.

	W167 chose a marker because the question there is whether you owe
	anything. Here the question is how much awaits you, and a marker
	answering "some" would leave an operator opening the page to find
	out what they could have read on the tab.
	"""

	def test_zero_is_spelled_rather_than_omitted(self, world):
		"""The case the whole ruling turns on.

		A tab that went blank at zero is indistinguishable from a build
		that never carried the count, so an operator could not tell
		"nothing is waiting for you" from "this console does not say"."""
		assert jobs_label(console(world)) == "[Jobs 0]"
		assert counted(world) == 0

	def test_the_number_is_the_projection_s_own(self, world):
		for _ in range(3):
			make(world)
		assert counted(world) == 3
		assert jobs_label(console(world)) == "[Jobs 3]"

	def test_it_counts_what_is_actionable_and_not_what_exists(self, world):
		"""Three Work items, one viewer they belong to and one they do
		not. A tab spelling "how much Work is here" would say 3 twice."""
		for _ in range(3):
			make(world)
		assert jobs_label(console(world, "ada")) == "[Jobs 3]"
		assert jobs_label(console(world, "grace")) == "[Jobs 0]"

	def test_it_counts_past_the_window_bound(self, world):
		"""The finding, in one assertion: six deep, three visible."""
		chain(world, 6)
		view = console(world)
		assert jobs_label(view) == "[Jobs 6]"
		assert len(view.table_rows()[0]) == 3

	def test_a_claim_lowers_it_on_the_next_read(self, world):
		made = [make(world) for _ in range(3)]
		view = console(world)
		assert jobs_label(view) == "[Jobs 3]"
		tr.claim_work(world["store"], made[0],
		              actor_team="lang", actor="ada")
		# The console paints from a cached projection on its own timer,
		# exactly as W167's marker does: the count must move with the
		# refresh rather than needing a keystroke that rebuilds it.
		view.tick()
		assert jobs_label(view) == "[Jobs 2]"

	def test_the_header_and_the_table_come_from_one_read(self, world):
		"""One cached window feeds both, so the tab and the rows can
		never describe two authority states."""
		chain(world, 4)
		lines = painted(console(world))
		assert lines[0].startswith("[Jobs 4]  [Teams]  [Inbox]")
		assert cells(lines, "Mine") == ["me+3", "me+2", "me+1"]

	@pytest.mark.parametrize("width", [110, 60, 44, 30, 26, 24, 20])
	def test_the_narrow_rule_draws_the_counted_label_whole(self, world,
	                                                       width):
		"""W110's rule is unchanged and the count rides INSIDE the
		brackets, so it can never be the part a narrow header cuts
		off: the whole label or none of it."""
		for _ in range(3):
			make(world)
		header = painted(console(world), height=14, width=width)[0]
		assert "[Jobs" not in header or "[Jobs 3]" in header, \
			(width, header)


# -- the column: where it is, on the tree the operator is reading ------------

class TestTheMineColumnIsMandatory:
	"""It is not in `COLUMNS` and not in `DROP_ORDER`, deliberately.

	A responsive column is one an operator can do without at narrow
	widths. This one answers "is any of this mine", and the widths where
	that summary matters most are exactly the widths that would drop it.
	"""

	def test_the_heading_is_drawn_when_nothing_is_mine(self, world):
		for _ in range(2):
			make(world)
		lines = painted(console(world, "grace"))
		assert "Mine" in header_of(lines)
		assert cells(lines, "Mine") == ["", ""]

	def test_the_four_values_and_their_meanings(self, world):
		"""blank / `me` / `+N` / `me+N`, each driven separately."""
		root = make(world, "root")
		make(world, "child", parent=root)
		held = make(world, "held")
		tr.claim_work(world["store"], held, actor_team="lang",
		              actor="ada")
		lines = painted(console(world))
		drawn = dict(zip(
			[line.split()[0] for line in lines[lines.index(
				header_of(lines)) + 1:] if line.strip()
			 and not line.startswith(("(", "Enter "))],
			cells(lines, "Mine")))
		assert drawn["W2"] == "me+1", drawn      # mine, and one below
		assert drawn["W3"] == "me", drawn        # mine, nothing below
		assert drawn["W4"] == "", drawn          # claimed: neither
		# `+N` alone: a parent nobody can claim over a child they can.
		# Parked rather than claimed, because this participant already
		# holds one above and a participant holds ONE active claim —
		# and parking is the other way a row stops being claimable
		# while everything beneath it stays exactly as it was.
		tr.set_phase(world["store"], root, actor_team="lang",
		             actor="ada", phase="parked",
		             reason="deliberately deferred")
		assert dict(zip(["W2", "W3"],
		                cells(painted(console(world)), "Mine"))) \
			["W2"] == "+1"

	def test_blank_rather_than_zero_when_nothing_is_mine(self, world):
		"""A column of `0`s is noise to look past; blank reads as
		nothing, which is what it means."""
		make(world)
		assert app.mine_cell({"viewer_actionable": False,
		                      "actionable_descendants": 0}) == ""
		assert "0" not in "".join(cells(painted(console(world, "grace")),
		                                "Mine"))

	def test_a_wide_count_widens_the_column_rather_than_clipping(self,
	                                                            world):
		"""`me+12` clipped to `me+1` is a smaller NUMBER rather than a
		visibly cut one — the operator has no way to see it was cut."""
		root = make(world, "root")
		for index in range(12):
			make(world, f"child {index}", parent=root)
		lines = painted(console(world))
		assert cells(lines, "Mine")[0] == "me+12"
		assert app.mine_column_width(
			console(world).table_rows()[0]) == len("me+12")

	@pytest.mark.parametrize("width", [110, 90, 74, 60, 52, 46, 43])
	def test_no_width_that_draws_a_table_drops_it(self, world, width):
		chain(world, 3)
		lines = painted(console(world), height=20, width=width)
		if any("too narrow" in line for line in lines):
			pytest.skip(f"{width} refuses the table whole")
		assert "Mine" in header_of(lines), (width, header_of(lines))
		assert cells(lines, "Mine")[0] == "me+2", (width, lines)

	def test_the_column_is_this_view_s_and_not_the_row_s(self, world):
		"""It is the VIEW's question, exactly as `Out` and `Run` are.
		The rows carry the members everywhere; the flattened page and
		search must not grow the column because of that."""
		for index in range(3):
			make(world, f"parser recovery {index}")
		view = console(world)
		view.search_input = "parser"
		view.handle(10)
		assert "Mine" not in header_of(painted(view))
		assert view.mode == "search"

	def test_the_flattened_page_has_no_column_at_all(self, world):
		chain(world, 4)
		view = console(world)
		view.handle(ord("m"))
		lines = painted(view)
		assert not any("Mine" in line for line in lines), lines
		# ...and the count is still there, once, where it says
		# something: the page label.
		assert "awaiting me: 4 total" in lines[1], lines[1]


# -- the refusal: the width it names has to be the width it needs ------------

class TestTheTooNarrowRefusalStatesASufficientWidth:
	"""Independent review [P2]: the refusal understated the requirement.

	The table correctly refuses rather than clipping identities. The
	number it hands the operator was assembled from `id_width` alone,
	while the judgment that produced the refusal was made against the
	whole leading allocation — which since W26328 includes the mandatory
	`Mine` column and its separator. So the one action the message asks
	for produced the same message again, which is worse than no number at
	all because an operator follows it.

	MEASURED AGAINST THE WIDTH THAT ACTUALLY DRAWS, found by widening the
	terminal a cell at a time until the table appears. That is the fact
	the operator is being told, so it is the fact these cases compare the
	message to — no test-side arithmetic that could be wrong the same way
	the message was.

	The message itself is drawn with `addnstr` and a very narrow terminal
	truncates it; that is pre-existing presentation and not this review's
	concern, so the comparison is against the whole intended line and
	tolerates only the cut the terminal itself made.
	"""

	def drawn_at(self, world, width, member="ada"):
		"""`(lines, table_drawn, the refusal line or its visible part)`.

		A terminal narrower than the sentence cuts the sentence, so the
		refusal is not always detectable by its own text — the TABLE is,
		and the header is what "drew" means.
		"""
		lines = painted(console(world, member), height=20, width=width)
		drew = any("Title" in line for line in lines)
		said = next((line for line in lines if "narrow" in line), None)
		return lines, drew, said

	def smallest_drawing_width(self, world, member="ada"):
		"""The narrowest terminal that draws the table at all.

		`layout_fits` is monotone in width, so the first width that draws
		is THE minimum — and the cases below assert that monotonicity
		rather than assume it.
		"""
		for width in range(12, 200):
			_lines, drew, _said = self.drawn_at(world, width, member)
			if drew:
				return width
		raise AssertionError("the table never drew; nothing was measured")

	def test_the_message_names_the_width_that_draws_the_table(self, world):
		chain(world, 3)
		smallest = self.smallest_drawing_width(world)
		whole = f"(terminal too narrow: need {smallest} cells)"
		compared = 0
		for width in range(12, smallest):
			_lines, drew, said = self.drawn_at(world, width)
			assert not drew, (width, smallest)
			if said is None:
				# Narrower than the word "narrow" itself; there is no
				# number on screen to be right or wrong about.
				continue
			compared += 1
			# The terminal may have cut the sentence. It may not have
			# changed the number in it.
			assert whole.startswith(said.rstrip()), (width, said, whole)
		assert compared, "no width showed the message; nothing was compared"

	def test_widening_to_the_stated_minimum_admits_the_whole_table(self,
	                                                               world):
		chain(world, 3)
		smallest = self.smallest_drawing_width(world)
		drawn, drew, _said = self.drawn_at(world, smallest)
		assert drew
		# The MANDATORY column is present at the minimum, which is the
		# whole reason its allocation belongs in the arithmetic.
		assert "Mine" in header_of(drawn)
		assert cells(drawn, "Mine")[0] == "me+2", drawn

	def test_a_wide_mine_allocation_is_counted(self, world):
		"""The exact shape the review names.

		`me+12` is five cells plus a separator the old arithmetic left out
		entirely, so the number it printed was six short — far past any
		rounding, and an operator who widened to it was refused again.
		"""
		root = make(world, "root")
		for index in range(12):
			make(world, f"child {index}", parent=root)
		smallest = self.smallest_drawing_width(world)
		_lines, drew, said = self.drawn_at(world, smallest - 1)
		assert not drew and said is not None
		whole = f"(terminal too narrow: need {smallest} cells)"
		assert whole.startswith(said.rstrip()), (said, whole)
		drawn, drew, _said = self.drawn_at(world, smallest)
		assert drew
		assert cells(drawn, "Mine")[0] == "me+12", drawn


# -- the page: everything awaiting you, with the path to each ----------------

class TestTheFlattenedPageFindsWhatTheTreeCannot:

	def test_m_lists_the_work_the_window_cannot_show(self, world):
		made = chain(world, 6)
		view = console(world)
		assert [row["id"] for row in view.table_rows()[0]] == made[:3]
		view.handle(ord("m"))
		assert view.mode == "mine"
		assert [row["id"] for row in view.mine_rows()] == made

	def test_it_reaches_work_another_team_owns(self, world):
		"""`m` opens the ALL-TEAM page, and the team that matters is
		the one the ROUTE names rather than the one that owns the Work.

		`route_team` and `team` are separate columns and `pass` moves
		the first without the second, so a Work owned by another team
		and handed to a Route you handle is yours to claim — and a page
		that scoped itself by ownership would hide exactly the Work a
		handoff just gave you.
		"""
		second = pathlib.Path(world["config"]).parent / "two"
		second.mkdir()
		config_path, database = fx.build_instance(
			str(second),
			{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
			 "web": {"members": {"wren": ["dev"]}, "kinds": ["bug"]}})
		store = bw.Authority(database)
		theirs = tr.create_work(store, team="web", kind="bug",
		                        title="theirs, handed over",
		                        origin="external-report",
		                        classification="suspected-defect",
		                        author="wren", body="b")["work_id"]
		tr.claim_work(store, theirs, actor_team="web", actor="wren")
		tr.pass_work(store, theirs, actor_team="web", actor="wren",
		             to="lang.bug", comment="over to you")
		view = Console(bw.Authority(database), "lang", "ada",
		               config_path=config_path)
		view.handle(ord("m"))
		assert [row["id"] for row in view.mine_rows()] == [theirs]
		assert dict(view.top_tab_segments())["jobs"] == "[Jobs 1]"
		store.close()

	def test_it_is_not_the_current_root_s_subtree(self, world):
		"""Re-rooted three levels down, the page still answers for
		everything: a Work under a DIFFERENT root is still awaiting
		you, and a page that inherited the root would hide it exactly
		when the operator went looking."""
		deep = chain(world, 4, prefix="deep")
		other = make(world, "elsewhere")
		view = console(world)
		view._open_root(deep[0])
		view.handle(ord("m"))
		assert other in [row["id"] for row in view.mine_rows()]

	def test_the_breadcrumb_is_complete_and_wrapped(self, world):
		"""Every other bounded cell in this console CLIPS. A clipped
		title is still a title and the Id beside it is the identity; a
		clipped path is a different path, and there is no second copy
		of it on the line."""
		made = chain(world, 5, prefix="a rather long containment level")
		view = console(world)
		view.handle(ord("m"))
		lines = painted(view, height=40, width=60)
		body = [line for line in lines[2:] if line.strip()
		        and not line.startswith("j/k ")]
		# the deepest entry, rejoined from however many lines it took
		joined = " ".join(line[3:].strip() for line in body
		                  if line.startswith("W6 ") or line.startswith("   "))
		expected = " > ".join(
			entry["title"] for entry in
			pj.breadcrumb(world["store"], made[-1]))
		assert joined.endswith(expected), (joined, expected)
		assert len(expected) > 60, "the path was not long enough to wrap"

	def test_the_empty_page_says_so(self, world):
		make(world)
		view = console(world, "grace")
		view.handle(ord("m"))
		lines = painted(view)
		assert "(no work awaiting you)" in lines[3], lines
		assert "awaiting me: 0 total" in lines[1], lines[1]

	def test_a_hundred_rows_to_a_page(self, world):
		for index in range(app.MINE_LIMIT + 1):
			make(world, f"work {index}")
		view = console(world)
		view.handle(ord("m"))
		assert len(view.mine_rows()) == app.MINE_LIMIT
		assert view.mine_next is not None
		assert view.mine_total == app.MINE_LIMIT + 1
		view.handle(ord("n"))
		assert view.mine_page == 2
		assert len(view.mine_rows()) == 1
		assert view.mine_next is None
		view.handle(ord("p"))
		assert view.mine_page == 1
		assert len(view.mine_rows()) == app.MINE_LIMIT

	def test_enter_and_back_restore_the_page_and_the_row(self, world):
		for index in range(app.MINE_LIMIT + 3):
			make(world, f"work {index}")
		view = console(world)
		view.handle(ord("m"))
		view.handle(ord("n"))
		view.handle(ord("j"))
		painted(view)
		where, chosen = view.mine_page, view.selected_id
		assert where == 2 and chosen is not None
		view.handle(10)
		assert view.mode == "detail"
		view.handle(27)
		assert view.mode == "mine"
		assert (view.mine_page, view.selected_id) == (where, chosen)

	def test_a_second_page_opened_inside_the_first_restores_it(self, world):
		"""The page number has to be CAPTURED, not merely left alone.

		Nothing on the ordinary Enter/Back path disturbs it, so a
		console that captured no page at all would pass that case by
		accident. This is the reachable path that moves it: page two,
		open a Work, reach that Work's own Jobs tab, open `Awaiting me`
		AGAIN — which starts at page one — and walk back out. The first
		page is restored or it is lost.
		"""
		for index in range(app.MINE_LIMIT + 3):
			make(world, f"work {index}")
		view = console(world)
		view.handle(ord("m"))
		view.handle(ord("n"))
		view.handle(ord("j"))
		painted(view)
		where, chosen = view.mine_page, view.selected_id
		view.handle(10)                       # the Work's detail
		view.handle(ord("["))                 # its own Jobs tab
		assert view.mode == "table" and view.context_work()
		view.handle(ord("m"))                 # a second page, at page one
		assert (view.mode, view.mine_page) == ("mine", 1)
		view.handle(27)
		view.handle(27)
		assert view.mode == "mine"
		assert (view.mine_page, view.selected_id) == (where, chosen)

	def test_back_returns_to_the_exact_tree_it_opened_from(self, world):
		made = chain(world, 3)
		view = console(world)
		view.handle(ord("j"))
		before = (view.cursor, view.selected_id)
		view.handle(ord("m"))
		view.handle(ord("j"))
		view.handle(27)
		assert view.mode == "table"
		assert (view.cursor, view.selected_id) == before
		assert view.selected_id == made[1]

	def test_the_page_is_one_back_and_names_itself(self, world):
		make(world)
		view = console(world)
		view.handle(ord("m"))
		assert view.nav_segments() == ["Jobs", "awaiting me"]
		assert painted(view)[0].startswith("Jobs > awaiting me")
		# W292: the global tab row belongs to the top level only.
		assert "[Jobs " not in painted(view)[0]

	def test_the_closed_reveal_does_not_reach_it(self, world):
		"""`z` and the work filter are view state the operator set for
		a different question. A closed Work is never claimable and a
		filtered-out one is still awaiting you, so honouring either
		would let this page hide the Work it exists to surface."""
		made = [make(world, f"work {index}") for index in range(3)]
		tr.claim_work(world["store"], made[0], actor_team="lang",
		              actor="ada")
		view = console(world)
		view.work_filter = {"priority": "high"}
		view.show_closed = True
		view.handle(ord("m"))
		assert [row["id"] for row in view.mine_rows()] == made[1:]

	def test_claiming_from_the_page_uses_the_shared_path(self, world):
		made = chain(world, 5)
		view = console(world)
		view.handle(ord("m"))
		painted(view)
		view.cursor = 4
		view.handle(ord("c"))
		held = pj.tree(world["store"], made[4], viewer_team="lang",
		               viewer_member="ada")["rows"][0]
		assert (held["handler"]["team"],
		        held["handler"]["member"]) == ("lang", "ada")


# -- a real terminal ---------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_counts_finds_and_comes_back(world):
	"""Injected keys cannot see a terminal that never sends them."""
	chain(world, 6)
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.7),          # 0: the tree — three levels, the count is six
		(b"m", 0.6),         # 1: every one of the six, with its path
		(b"\x1b", 0.6),      # 2: back to the tree
		(b"qy", 0.4),
	], columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-600:]
	table, mine, back = (ptyharness.replay(step, columns=110, lines=24)
	                     for step in steps[:3])
	assert table[0].startswith("[Jobs 6]"), table[0]
	assert re.search(r"\bMine\b", table[1]), table[1]
	assert len([line for line in table if line.startswith("W")]) == 3
	# the key is TAUGHT, on the same footer that teaches the others —
	# a binding an operator has to be told about out of band is one
	# they do not have.
	assert any("m mine" in line for line in table), table[-3:]
	assert "awaiting me: 6 total · page 1 · 6 shown" in mine[1], mine[:4]
	assert [line.split()[0] for line in mine[2:] if line.startswith("W")] \
		== ["W2", "W3", "W4", "W5", "W6", "W7"], mine[2:10]
	# the level the tree could not show, with the whole path to it
	assert any("level 5" in line for line in mine), mine[2:10]
	assert back[0].startswith("[Jobs 6]"), back[0]
