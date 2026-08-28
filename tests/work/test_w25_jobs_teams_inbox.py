"""W25: the console is organized around Jobs, Teams and Inbox.

`work/records/2026/08/finding-tui-jobs-teams-inbox/`. The v11 console
opened directly on Work and spent its header on participant-relative
`oblig`/`park`/`due` counters. W17 then had to add a fourth owed class
to that header, and the shape stopped scaling: a counter row cannot say
what an item IS, and an operator who is addressed personally had nowhere
to go and act.

The ruled model is three top-level tabs. **Jobs** is the Work tree and
everything hanging off it, unchanged. **Teams** is an operational roster
— who is configured, what work can reach them, what they hold, and what
their runner last said about itself. **Inbox** is participant-relative:
what this member owes and has not seen.

These tests hold that contract on both interfaces, because the TUI is
one projection of the model and not its only one:

- the tabs lead the header, identity is right-aligned, and the retired
  counters do not come back;
- Inbox counts `total/unseen`, stays bold while an action is owed even
  after it has been seen, and unbolds when nothing is owed;
- Inbox rows name their type and separate owed action from attention;
- Teams defaults to the viewer's own team, browses every configured
  team deliberately, and never guesses liveness;
- every semantic field the console paints is available as typed JSON.
"""

from __future__ import annotations

import curses
import json as _json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import cli as _cli                             # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui import app                                 # noqa: E402
from baton_work.tui.app import Console, TABS                   # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

TAB = 9
NEXT_TAB = ord("]")   # W1151: `]` switches tabs; Tab moves panes
PREV_TAB = ord("[")
ESC = 27


@pytest.fixture()
def world(tmp_path):
	"""Two teams. `grace` shares `ada`'s team but the route resolves to
	`ada` alone, so "owed by me" and "owed by my team" cannot be
	confused; `sl` is the cross-team member Teams has to browse to."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	# `Authority` binds its clock once at construction, so a test that
	# needs to stand past a deadline reads the injected instant at CALL
	# time instead — the same contract, evaluated later.
	store.clock = lambda: (os.environ.get("BATON_WORK_NOW")
	                       or bw.authority._utc_now())
	yield {"store": store, "config": config_path, "database": database,
	       "tmp": tmp_path}
	store.close()


@pytest.fixture(autouse=True)
def _unfrozen():
	yield
	os.environ.pop("BATON_WORK_NOW", None)


@pytest.fixture(autouse=True)
def _no_inherited_editor():
	saved = os.environ.pop("EDITOR", None)
	yield
	if saved is None:
		os.environ.pop("EDITOR", None)
	else:
		os.environ["EDITOR"] = saved


class Screen:
	def __init__(self, height=24, width=110):
		self.rows = {}
		self.height = height
		self.width = width

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		self.rows[y] = (self.rows.get(y, "")[:x]).ljust(x) + str(text)[:n]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


class AttrScreen(Screen):
	"""A screen that REMEMBERS attributes.

	W25 review R1: the plain fake above drops the third `addnstr`
	argument, so 70 passing cases could not see that the urgency weight
	was being painted onto every tab. Anything asserting about bold has
	to record it."""

	def __init__(self, height=24, width=110):
		super().__init__(height, width)
		self.calls = []

	def addnstr(self, y, x, text, n, *rest):
		super().addnstr(y, x, text, n, *rest)
		self.calls.append({"y": y, "x": x, "text": str(text)[:n],
		                   "attr": rest[0] if rest else 0})

	def header_cells(self):
		"""Row 0 as `{column: (character, attribute)}` — what a human
		looking at the top line would actually see, weight included."""
		cells = {}
		for call in self.calls:
			if call["y"] != 0:
				continue
			for offset, character in enumerate(call["text"]):
				cells[call["x"] + offset] = (character, call["attr"])
		return cells

	def bold_text(self, row=0):
		return self._weighted(curses.A_BOLD, row)

	def reverse_text(self, row=0):
		"""W110: the ACTIVE tab's weight. Separate from bold on
		purpose — an owed Inbox an operator is not sitting in must
		still read as owed, and the tab they ARE sitting in must not
		read as owed for being selected."""
		return self._weighted(curses.A_REVERSE, row)

	def _weighted(self, weight, row=0):
		cells = self.header_cells() if row == 0 else {}
		out = ""
		for column in sorted(cells):
			character, attr = cells[column]
			out += character if attr & weight else " "
		return out.strip()


def attr_painted(view, height=24, width=110):
	screen = AttrScreen(height, width)
	view.render(screen)
	return screen


def console(world, member="ada", team="lang", tab="jobs"):
	view = Console(world["store"], team, member,
	               config_path=world["config"])
	while view.tab != tab:
		view.handle(NEXT_TAB)
	return view


def select(view, predicate, what):
	"""Move the cursor to the first row the predicate accepts.

	BOUNDED on purpose: `j` clamps at the last row, so a `while` that
	waited for a row the list does not hold would spin forever and the
	suite would hang instead of failing."""
	rows = view.inbox_rows() if view.tab == "inbox" else view.team_rows()
	for _ in range(len(rows) + 1):
		chosen = (view._inbox_selected() if view.tab == "inbox"
		          else view._team_selected())
		if chosen is not None and predicate(chosen):
			return chosen
		view.handle(ord("j"))
	raise AssertionError(f"no {what} row among {len(rows)}")


def painted(view, height=24, width=110):
	screen = Screen(height, width)
	view.render(screen)
	return screen.lines()


def make_work(world, title="parser recovery", author="ada"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="the opener")


def ask(world, born, endpoint="lang.rsrch", body="lang: please advise"):
	return tr.post_thread(world["store"], born["thread"],
	                      author_team="lang", author="ada", body=body,
	                      request=endpoint, on=born["work_id"],
	                      wait=False)["seq"]


def poke(world, asker="grace", target="lang.ada", request="what's up?",
         team="lang"):
	return tr.poke(world["store"], actor_team=team, actor=asker,
	               target=target, request=request)["poke"]


def fake_editor(tmp_path, *, writes="because I said so"):
	script = tmp_path / "ed.py"
	script.write_text("\n".join([
		"import sys",
		"path = sys.argv[-1]",
		"original = open(path, encoding='utf-8').read()",
		f"open(path, 'w', encoding='utf-8').write(original + {writes!r})",
		"sys.exit(0)",
	]) + "\n", encoding="utf-8")
	return f"{sys.executable} {script}"


def run_json(world, *argv, member="ada", team="lang"):
	"""One canonical CLI read, exactly as an agent runs it."""
	import contextlib
	import io
	out = io.StringIO()
	with contextlib.redirect_stdout(out):
		code = _cli.main(["--config", world["config"], "--participant",
		                  f"{team}.{member}"] + list(argv))
	assert code == 0, out.getvalue()
	return _json.loads(out.getvalue())["result"]


# -- the shell ---------------------------------------------------------------

def test_the_tabs_lead_the_header_in_the_ruled_order(world):
	header = painted(console(world))[0]
	assert header.startswith("[Jobs "), header
	assert header.index("Jobs") < header.index("Teams") < \
		header.index("Inbox"), header
	assert TABS == ("jobs", "teams", "inbox")


def test_the_participant_identity_is_right_aligned(world):
	header = painted(console(world))[0]
	assert header.rstrip().endswith("lang.ada"), header
	assert not header.startswith("lang.ada"), \
		"identity is still leading the header"


def test_the_retired_header_counters_are_gone(world):
	"""'The former [oblig] [park] [due] header counters are removed.'"""
	born = make_work(world)
	ask(world, born)
	tr.set_phase(world["store"], make_work(world, "parked one")["work_id"],
	             actor_team="lang", actor="ada", phase="parked",
	             reason="deliberately deferred")
	header = painted(console(world))[0]
	for token in ("[oblig:", "[park:", "[due:", "[poke:"):
		assert token not in header, f"{token} survived in the header"


def test_every_tab_is_bracketed_and_the_active_one_is_highlighted(world):
	"""W110 supersedes W25's rule that the bracket marked the SELECTED
	tab. Work detail already bracketed both of its tabs to say "these
	are tabs", so the same bracket meaning "and this one is active" one
	level up was a grammar an operator had to learn twice. Brackets now
	mark tabs at both levels and the active one is highlighted.

	The information W25 was protecting is not lost — it moved to the
	paint, which this asserts rather than assuming."""
	view = console(world)
	# W26328: the Jobs label carries the actionable count. It is still
	# one bracketed tab and the brackets still say "this is a tab",
	# which is the whole of what this case rules on.
	assert view.top_tabs() == "[Jobs 0]  [Teams]  [Inbox]", \
		view.top_tabs()
	screen = attr_painted(view)
	assert screen.reverse_text() == "[Jobs 0]", screen.reverse_text()
	view.handle(NEXT_TAB)
	assert view.top_tabs() == "[Jobs 0]  [Teams]  [Inbox]", \
		"the label text moved with the selection"
	assert attr_painted(view).reverse_text() == "[Teams]"


def test_the_tab_cycle_runs_forward_and_backward(world):
	"""W25 ruled the CYCLE — three tabs, in order, wrapping both ways.
	W110 moved it onto `[`/`]` and W1151 retired the Tab aliases
	entirely, because Tab now cycles pane focus one level down. The
	cycle itself is what this case has always been about, and it is
	unchanged."""
	view = console(world)
	seen = []
	for _ in range(4):
		seen.append(view.tab)
		view.handle(NEXT_TAB)
	assert seen == ["jobs", "teams", "inbox", "jobs"], seen
	assert view.tab == "teams", view.tab
	view.handle(PREV_TAB)
	assert view.tab == "jobs", "`[` did not step backwards"
	view.handle(PREV_TAB)
	assert view.tab == "inbox", "`[` did not wrap"


def test_the_bracket_keys_move_the_top_level_tabs_too(world):
	"""W110 supersedes W25's separation. The keys perform the SAME
	operation at both levels — previous/next tab at the level you are
	in — so one rule replaces two gestures. The separation that
	survives is CONTEXTUAL and is pinned in `test_w110_tab_grammar`:
	inside Work detail the same keys move Messages/Events and never
	reach the top level."""
	view = console(world)
	view.handle(ord("]"))
	assert view.tab == "teams"
	view.handle(ord("["))
	assert view.tab == "jobs"


def test_only_the_inbox_tab_carries_the_urgency_weight(world):
	"""W25 review R1. The FINDING bolds the INBOX tab while an action is
	owed. Bolding the whole bar says something is owed and then hides
	which tab holds it — the one question the cue exists to answer."""
	poke(world)
	screen = attr_painted(console(world))
	bold = screen.bold_text()
	assert "Inbox" in bold, bold
	assert "Jobs" not in bold, \
		"the Jobs tab acquired the Inbox urgency cue"
	assert "Teams" not in bold, \
		"the Teams tab acquired the Inbox urgency cue"
	# the selection cue and the identity are untouched by the change
	assert screen.lines()[0].startswith("[Jobs ")
	assert screen.lines()[0].rstrip().endswith("lang.ada")


def test_no_tab_is_bold_when_nothing_is_owed(world):
	make_work(world)
	screen = attr_painted(console(world))
	assert console(world).inbox_view()["owed_action"] is False
	for name in ("Jobs", "Teams", "Inbox"):
		assert name not in screen.bold_text(), \
			f"{name} is bold with nothing owed: {screen.bold_text()!r}"


def test_the_weight_follows_owed_action_and_not_unseen(world):
	"""Seen state must never quiet the cue, and unseen attention must
	never raise it — the two halves of the same ruling."""
	born = make_work(world)
	asked = ask(world, born)
	tr.seen_thread(world["store"], born["thread"], team="lang",
	               member="ada", up_to_seq=asked)
	box = console(world).inbox_view()
	assert box["unseen"] == 0 and box["owed_action"] is True
	assert "Inbox" in attr_painted(console(world)).bold_text(), \
		"reading the question quieted the tab that says you owe it"
	tr.respond_obligation(world["store"], asked, team="lang",
	                      member="ada", body="here you are")
	after = console(world)
	assert after.inbox_view()["owed_action"] is False
	assert "Inbox" not in attr_painted(after).bold_text(), \
		"the tab stayed bold with nothing owed"


def test_the_painted_tab_bar_matches_the_joined_label(world):
	"""The header is painted label by label so one of them can be bold;
	`top_tabs()` joins the same labels. If those two ever disagree the
	brackets land on the wrong columns."""
	poke(world)
	view = console(world)
	painted_row = attr_painted(view).lines()[0]
	assert painted_row.startswith(view.top_tabs()), \
		(painted_row, view.top_tabs())


def test_a_narrow_terminal_still_says_who_and_where(world):
	"""The tab model must stay usable narrow without silently hiding
	owed action: identity overdraws last, so it is the one thing a
	narrow header cannot lose."""
	poke(world)
	view = console(world)
	header = painted(view, height=14, width=44)[0]
	assert header.rstrip().endswith("lang.ada"), header
	assert header.startswith("[Jobs "), header
	assert any("waiting for you" in line
	           for line in painted(view, height=14, width=44)), \
		"the owed cue was hidden by the narrow width"


# -- Inbox -------------------------------------------------------------------

def test_the_inbox_counts_stay_where_their_rows_are(world):
	"""W167 supersedes the `total/unseen` TEXT in this label and
	nothing else. The counters are still derived, still independent,
	and still projected — they simply no longer spend six header cells
	saying `3/3`, which is what they said almost always. The tab now
	answers the question an operator actually has at a glance."""
	born = make_work(world)
	ask(world, born)
	poke(world)
	view = console(world)
	box = view.inbox_view()
	assert box["total"] == 3 and box["unseen"] == 3, box
	assert "3/3" not in view.top_tabs(), view.top_tabs()
	assert "[Inbox *]" in view.top_tabs(), view.top_tabs()


def test_the_tab_stays_bold_while_something_is_owed_though_seen(world):
	"""'The whole Inbox tab is bold whenever at least one row is an
	unresolved action the current participant owes, even when that row
	has already been seen.'"""
	born = make_work(world)
	asked = ask(world, born)
	view = console(world)
	assert view.inbox_view()["owed_action"] is True
	tr.seen_thread(world["store"], born["thread"], team="lang",
	               member="ada", up_to_seq=asked)
	box = console(world).inbox_view()
	assert box["unseen"] == 0, "seen state did not move"
	assert box["owed"] == 1 and box["owed_action"] is True, \
		"reading the question stopped the tab saying you owe the answer"


def test_the_tab_unbolds_when_nothing_is_owed(world):
	born = make_work(world)
	asked = ask(world, born)
	tr.respond_obligation(world["store"], asked, team="lang",
	                      member="ada", body="here you are")
	box = console(world).inbox_view()
	assert box["owed"] == 0 and box["owed_action"] is False
	assert box["total"] >= 1, "attention rows left with the obligation"


def test_inbox_rows_name_their_type_and_separate_owed_from_attention(world):
	born = make_work(world)
	ask(world, born)
	poke(world)
	rows = console(world, tab="inbox").inbox_rows()
	kinds = [row["kind"] for row in rows]
	assert {"poke", "obligation", "message"} <= set(kinds), kinds
	assert [row["owed"] for row in rows] == sorted(
		(row["owed"] for row in rows), reverse=True), \
		"owed rows are not first"
	attention = next(row for row in rows if row["kind"] == "message")
	assert attention["owed"] is False
	view = console(world, tab="inbox")
	painted_rows = painted(view)
	assert any("poke" in line and "answer" in line
	           for line in painted_rows), painted_rows
	assert any("you owe this" in line for line in painted_rows), \
		"the detail block does not say the viewer is the blocker"
	select(view, lambda row: row["kind"] == "message", "message")
	assert any("attention only" in line for line in painted(view)), \
		"the detail block does not distinguish attention from owed"


def test_a_due_trial_is_an_inbox_row(world):
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	# A deadline born expired refuses, so the only honest way to see a
	# DUE trial is to open one live and then stand past it.
	os.environ["BATON_WORK_NOW"] = "2026-08-19T09:00:00Z"
	tr.create_trial(world["store"], born["work_id"], actor_team="lang",
	                actor="ada", candidate="build-a",
	                assign=["lang.rsrch"],
	                review_at="2026-08-19T09:30:00Z")
	os.environ["BATON_WORK_NOW"] = "2026-08-19T10:00:00Z"
	rows = console(world, tab="inbox").inbox_rows()
	trial = next(row for row in rows if row["kind"] == "due_trial")
	assert trial["owed"] is True
	assert trial["work"] == born["work_id"]
	assert "assess" in trial["completes_by"]


def test_actionable_work_is_jobs_and_never_an_inbox_row(world):
	"""One queue in two tabs would make "how much do I owe" a number
	nobody can act on."""
	make_work(world)
	rows = console(world, tab="inbox").inbox_rows()
	assert all(row["kind"] != "work" for row in rows), rows
	# and the wake set still carries it, because a runner has no tabs
	actions = pj.participant_actions(world["store"], viewer_team="lang",
	                                 viewer_member="ada")["actions"]
	assert any(action["kind"] == "work" for action in actions)


def test_enter_opens_the_rows_work_in_jobs(world):
	"""'Inbox rows link to that context' — the operator is handed to
	Jobs with the right Work already open, never asked to copy an id."""
	born = make_work(world)
	ask(world, born)
	view = console(world, tab="inbox")
	select(view, lambda row: row["kind"] == "obligation", "obligation")
	view.handle(10)
	assert view.tab == "jobs" and view.mode == "detail"
	assert view.detail_work == born["work_id"]


def test_a_poke_row_says_it_has_no_work_context(world):
	poke(world)
	view = console(world, tab="inbox")
	select(view, lambda row: row["kind"] == "poke", "poke")
	view.handle(10)
	assert view.tab == "inbox", "a poke row navigated somewhere"
	assert "no Work context" in view.status, view.status


def test_answering_a_poke_from_the_inbox_uses_the_shared_chooser(world):
	"""W17's answer flow is INTEGRATED, not duplicated: the same state
	chooser and the same public verb, reached from the Inbox row."""
	seq = poke(world)
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="all quiet")
	view = console(world, tab="inbox")
	select(view, lambda row: row["kind"] == "poke", "poke")
	view.handle(ord("a"))
	assert view.poke_choice == seq
	view.handle(ord("1"))
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang",
		viewer_member="ada")["pokes"] if entry["poke"] == seq)
	assert row["state"] == "answered", view.status
	assert row["answer"]["explanation"] == "all quiet"


def test_responding_to_an_obligation_from_the_inbox(world):
	born = make_work(world)
	asked = ask(world, born)
	os.environ["EDITOR"] = fake_editor(world["tmp"],
	                                   writes="spans are additive")
	view = console(world, tab="inbox")
	select(view, lambda row: row["kind"] == "obligation", "obligation")
	view.handle(ord("a"))
	assert not [entry for entry in pj.obligations(
		world["store"], viewer_team="lang")
		if entry["seq"] == asked], view.status


def test_marking_seen_from_the_inbox_moves_the_real_cursor(world):
	born = make_work(world)
	ask(world, born)
	view = console(world, tab="inbox")
	select(view, lambda row: row["kind"] == "message", "message")
	view.handle(ord("s"))
	box = console(world).inbox_view()
	assert box["unseen"] == 0, box
	assert box["owed_action"] is True, \
		"marking seen discharged an obligation it does not own"


def test_the_inbox_selection_survives_a_refresh(world):
	born = make_work(world)
	ask(world, born)
	poke(world)
	view = console(world, tab="inbox")
	view.handle(ord("j"))
	chosen = view.inbox_key
	poke(world, asker="sl", team="push", request="another")
	view.schedule_refresh()
	painted(view)
	assert view.inbox_key == chosen, "a refresh moved the selection"


# -- Teams -------------------------------------------------------------------

def test_teams_defaults_to_the_viewers_own_team(world):
	view = console(world, tab="teams")
	assert {row["team"] for row in view.team_rows()} == {"lang"}
	assert "own team" in painted(view)[1]


def test_teams_browses_every_configured_team_deliberately(world):
	view = console(world, tab="teams")
	view.handle(ord("t"))
	assert {row["team"] for row in view.team_rows()} == {"lang", "push"}
	assert "every team" in painted(view)[1]


def test_a_member_row_shows_roles_routes_and_canonical_claims(world):
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	lines = painted(console(world, tab="teams"), height=40)
	row = next(line for line in lines if line.startswith("lang.ada"))
	# W93 slice 5 reshaped this table to the ruled vocabulary: Role,
	# Agent, State, Work, Session, Since. Roles and the route coverage
	# they imply still identify the member, and the full route detail
	# moved to the block below, which the next assertion reads.
	assert "dev" in row, row
	assert "W2" in row, row
	# W184: `Holding` is a key/value row now; the fact is unchanged.
	assert any(line.strip().startswith("Holding") and "W2" in line
	           for line in lines), lines
	assert any(line.strip().startswith("Route")
	           and "main (dev): lang.bug, lang.rsrch" in line
	           for line in lines), lines


def test_teams_never_guesses_liveness(world):
	"""A member who has never answered a poke reports UNKNOWN, and the
	roster says so in words rather than leaving a blank that reads as
	'fine'."""
	lines = painted(console(world, tab="teams"))
	assert any("never asked" in line for line in lines), lines


def test_the_raw_structured_answer_is_inspectable(world):
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace", request="status?")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="needs-help", explanation="the editor keeps failing",
	               provider="Google", model="gemini-3", session_state="live",
	               auth_state="ok", limit_state="rate-limited",
	               context_used=90, context_limit=100)
	view = console(world, tab="teams")
	select(view, lambda row: row["member"] == "grace", "grace")
	lines = painted(view, height=40)
	# W184 gave every one of these its own key. The raw structured
	# answer is still inspectable — more so, in fact, which is the
	# point of the ruling.
	def has(key, value):
		return any(line.strip().startswith(key) and value in line
		           for line in lines), lines

	assert has("Said", "needs-help")[0], lines
	assert has("Explanation", "editor keeps failing")[0], lines
	assert has("Provider", "Google")[0], lines
	assert has("Model", "gemini-3")[0], lines
	assert has("Limit state", "rate-limited")[0], lines
	assert has("Context used", "90")[0], lines


def test_poking_a_member_from_teams(world):
	os.environ["EDITOR"] = fake_editor(world["tmp"],
	                                   writes="are you still there?")
	view = console(world, tab="teams")
	select(view, lambda row: row["member"] == "grace", "grace")
	view.handle(ord("p"))
	rows = pj.pokes(world["store"], viewer_team="lang",
	                viewer_member="ada")["pokes"]
	assert [row["target"] for row in rows] == ["lang.grace"], view.status
	assert rows[0]["request"] == "are you still there?"


def test_withdrawing_a_poke_from_teams(world):
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace", request="status?")["poke"]
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="answered live")
	view = console(world, tab="teams")
	select(view, lambda row: row["member"] == "grace", "grace")
	assert any("x withdraw" in line for line in painted(view)), \
		painted(view)[-3:]
	view.handle(ord("x"))
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang",
		viewer_member="ada")["pokes"] if entry["poke"] == seq)
	assert row["state"] == "cancelled", view.status


def test_withdrawal_is_offered_only_where_one_is_outstanding(world):
	view = console(world, tab="teams")
	assert not any("x withdraw" in line for line in painted(view))
	view.handle(ord("x"))
	assert "no pending poke" in view.status, view.status


# -- interface parity --------------------------------------------------------

def test_the_console_facts_are_all_available_as_typed_json(world):
	"""'CLI/JSON must expose enough typed, participant-relative data for
	an agent to derive the same Jobs, Teams, Inbox counts, owed-action
	cue, navigation targets, and allowed actions.'"""
	born = make_work(world)
	ask(world, born)
	poke(world)
	box = run_json(world, "inbox")
	view = console(world, tab="inbox")
	assert box["total"] == view.inbox_view()["total"]
	assert box["unseen"] == view.inbox_view()["unseen"]
	assert box["owed_action"] is True
	for row in box["rows"]:
		# navigation targets and allowed actions, as fields
		assert set(row) >= {"kind", "owed", "seen", "selector", "work",
		                    "thread", "message", "completes_by"}
	roster = run_json(world, "teams")
	member = next(entry for team in roster["teams"]
	              for entry in team["members"]
	              if entry["participant"] == "lang.ada")
	assert member["roles"] == ["dev"]
	assert member["routes"][0]["endpoints"] == ["lang.bug", "lang.rsrch"]
	assert member["last_answer"] is None
	assert roster["teams"][0]["mine"] is True


def test_the_two_verbs_are_reads_and_carry_no_operands(world):
	for verb in ("teams", "inbox"):
		assert verb in _cli.GRAMMAR
		assert _cli.GRAMMAR[verb]["keys"] == ()
		assert verb not in _cli.MUTATIONS


def test_the_inbox_owed_set_is_the_wake_set_and_not_a_second_opinion(world):
	"""W39 is the finding that says what a second endpoint resolution
	costs; Inbox reads the same derivation `wait` consumes."""
	born = make_work(world)
	ask(world, born)
	poke(world)
	owed = {row["action_key"] for row in
	        pj.inbox(world["store"], viewer_team="lang",
	                 viewer_member="ada")["rows"] if row["owed"]}
	wake = {action["action_key"] for action in pj.participant_actions(
		world["store"], viewer_team="lang",
		viewer_member="ada")["actions"] if action["kind"] != "work"}
	assert owed == wake, (owed, wake)


def test_the_roster_reports_an_alternate_route_as_coverage(world):
	"""W230 alternates decide who work can reach, so a roster that
	omitted them would answer its own question wrongly."""
	roster = pj.teams(world["store"], viewer_team="lang",
	                  viewer_member="ada")
	member = next(entry for team in roster["teams"]
	              for entry in team["members"]
	              if entry["participant"] == "lang.ada")
	assert member["routes"], member
	assert all("endpoints" in entry for entry in member["routes"])


# -- the real terminal -------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_shows_the_tabs_and_switches_them(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	tr.poke(store, actor_team="lang", actor="grace", target="lang.ada",
	        request="are you awake?")
	store.close()
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"", 0.5),
		(b"]", 0.5),
		(b"]", 0.5),
		(b"qy", 0.4),
	])
	jobs = ptyharness.replay(steps[0])
	assert jobs[0].startswith("[Jobs "), jobs[0]
	assert jobs[0].rstrip().endswith("lang.ada"), jobs[0]
	teams = ptyharness.replay(steps[1])
	assert "[Teams]" in teams[0], teams[0]
	assert any("lang.grace" in line for line in teams), teams[:8]
	inbox = ptyharness.replay(steps[2])
	assert "[Inbox *]" in inbox[0], inbox[0]
	assert any("are you awake?" in line for line in inbox), inbox[:8]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
