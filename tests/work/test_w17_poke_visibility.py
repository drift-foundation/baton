"""W17: pending conversational pokes are visible and answerable in the TUI.

`work/records/2026/08/finding-tui-poke-visibility/`. The projection-12
deployment smoke committed a poke for `baton.slaw`, the canonical
`pokes` read showed it pending, and the console said nothing at all: a
human participant could not discover the question, let alone answer it,
without knowing to run the JSON verb by hand.

The authority half was never at fault, so nothing here adds a second
delivery path. These tests hold the PRESENTATION contract:

- the header counts pending pokes addressed to this participant, in a
  counter of their own — never folded into `oblig`, `park`, `due`, or
  the personal New count, because a poke carries no workflow authority;
- the view lists the friendly question, says which end of it this
  participant is on, and shows the whole request and any answer;
- answering and withdrawing run the ordinary public verbs from the
  selected row, so no sequence is ever copied out of raw JSON;
- answered, cancelled, superseded and timed-out pokes stop being owed
  while staying readable as history.

SUPERSEDED IN PART by W25 (finding-tui-jobs-teams-inbox), 2026-08-19:
the MECHANISM of the first bullet moved. W17 counted owed pokes in a
`[poke:N]` header counter; W25 retires every header counter and gives
the participant an Inbox tab whose label carries `total/unseen` and
whose rows name each item's type. The PROPERTY is unchanged and is what
these tests still hold — a poke owed by this participant is visibly
counted, is distinguishable from an obligation or ambient New, and is
answerable without copying a sequence out of JSON. `poke_cue()` below
is the one place that knows where the count now lives.
"""

from __future__ import annotations

import os
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
from baton_work.tui.app import Console, poke_answer_states      # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

ESC = 27


@pytest.fixture()
def world(tmp_path):
	"""`ada` is the viewer; `grace` shares her team and `sl` is in
	another, so a poke can arrive from either side of a team boundary
	and the counter still has to be personal."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	# The clock is bound at construction, so a test freezing time after
	# the store exists would otherwise keep reading the wall clock.
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
	"""Every test states its own EDITOR (or its absence), so an editor
	in the developer's environment can never decide an outcome here."""
	saved = os.environ.pop("EDITOR", None)
	yield
	if saved is None:
		os.environ.pop("EDITOR", None)
	else:
		os.environ["EDITOR"] = saved


class Screen:
	"""The painted grid, in the shape the console draws it."""

	def __init__(self, height=24, width=100):
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


def console(world, member="ada", team="lang"):
	return Console(world["store"], team, member,
	               config_path=world["config"])


def painted(view):
	screen = Screen()
	view.render(screen)
	return screen.lines()


def poke(world, asker="grace", target="lang.ada", request="what's up?",
         team="lang", expires_at=None):
	return tr.poke(world["store"], actor_team=team, actor=asker,
	               target=target, request=request,
	               expires_at=expires_at)["poke"]


def make_work(world, title="a bug"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


def fake_editor(tmp_path, *, writes="because I said so", exit_code=0,
                record=None):
	"""A deterministic editor — no terminal, no interaction — that
	appends its text below Baton's instructional block. `record` keeps
	the document it was handed, which is the only way to see what the
	console asked the operator to write."""
	script = tmp_path / "ed.py"
	script.write_text("\n".join([
		"import sys",
		"path = sys.argv[-1]",
		"original = open(path, encoding='utf-8').read()",
		f"record = {record!r}",
		"if record:",
		"    open(record, 'w', encoding='utf-8').write(original)",
		f"open(path, 'w', encoding='utf-8').write(original + {writes!r})",
		f"sys.exit({exit_code})",
	]) + "\n", encoding="utf-8")
	return f"{sys.executable} {script}"


def header(world, member="ada", team="lang"):
	view = console(world, member, team)
	return painted(view)[0]


def poke_cue(world, member="ada", team="lang") -> int:
	"""How many owed POKES this participant can currently see counted.

	W25 moved the count out of the header and into the Inbox, which
	aggregates pokes with obligations and attention — so the poke-only
	number lives in the rows, where every item names its type. Reading
	it through the rendered rows rather than the projection keeps these
	tests asking what a HUMAN can see, which is what W17 is about."""
	view = console(world, member, team)
	return len([row for row in view.inbox_rows()
	            if row["kind"] == "poke" and row["owed"]])


def inbox_label(world, member="ada", team="lang") -> str:
	return console(world, member, team).top_tabs()


# -- the summary cue ---------------------------------------------------------

def test_the_header_counts_pending_pokes_addressed_to_this_participant(world):
	assert poke_cue(world) == 0
	# W167 replaced the tab's `total/unseen` with one owed-action
	# marker. The distinction this case was defending is unchanged and
	# still asserted — an absent cue and a present one are different
	# facts — but the cue is now `*`, which answers "do I owe
	# anything" instead of "how much have I not read".
	assert inbox_label(world).endswith("[Inbox]"), inbox_label(world)
	poke(world)
	assert poke_cue(world) == 1
	assert inbox_label(world).endswith("[Inbox *]"), inbox_label(world)


def test_the_counter_is_personal(world):
	"""A poke names ONE participant. Somebody else's question is not a
	cue on this operator's header, whatever team it crossed."""
	poke(world, asker="ada", target="lang.grace")
	poke(world, asker="ada", target="push.sl")
	assert poke_cue(world) == 0, \
		"pokes this participant SENT were counted as owed"
	assert poke_cue(world, member="grace") == 1
	assert poke_cue(world, member="sl", team="push") == 1


def test_many_pending_pokes_are_all_counted(world):
	"""Different askers keep independent pending pokes to one target, so
	the counter is a count and not a boolean."""
	poke(world, asker="grace")
	poke(world, asker="sl", team="push")
	assert poke_cue(world) == 2


def test_the_poke_counter_is_separate_from_obligations_and_new(world):
	"""The cue must distinguish a poke from Work, Message obligations
	and personal New counts."""
	born = make_work(world)
	tr.post_thread(world["store"], born["thread"], author_team="lang",
	               author="ada", body="lang: please advise",
	               request="lang.rsrch", on=born["work_id"], wait=False)
	line = header(world)
	assert "[oblig:" not in line and "[poke:" not in line, \
		"W25 retired the header counters; the Inbox owns owed action"
	assert poke_cue(world) == 0
	assert len([row for row in console(world).inbox_rows()
	            if row["kind"] == "obligation"]) == 1
	before = pj.tree(world["store"], None, viewer_team="lang",
	                 viewer_member="ada")["rows"]
	owed_before = list(pj.obligations(world["store"], viewer_team="lang"))
	poke(world)
	rows = console(world).inbox_rows()
	assert len([row for row in rows
	            if row["kind"] == "obligation"]) == 1, \
		"the poke inflated the obligation rows"
	assert poke_cue(world) == 1
	# and the two are TOLD APART on screen, which is the ruling: the
	# aggregate tab count never has to be disambiguated by guessing.
	kinds = {row["kind"] for row in rows}
	assert {"poke", "obligation"} <= kinds, kinds
	# and the authority agrees: no obligation, and no Work row moved —
	# not its Msg/My counters and not its personal New.
	assert [entry["seq"] for entry in
	        pj.obligations(world["store"], viewer_team="lang")] == \
		[entry["seq"] for entry in owed_before]
	assert pj.tree(world["store"], None, viewer_team="lang",
	               viewer_member="ada")["rows"] == before


def test_the_bottom_row_names_the_key_that_opens_the_view(world):
	"""A counter tells the operator something is waiting; it does not
	tell them what to press."""
	assert not any("press p" in line for line in painted(console(world))), \
		"the console advertised a poke nobody sent"
	poke(world)
	view = console(world)
	assert any("1 poke waiting for you — Tab to Inbox" in line
	           for line in painted(view)), painted(view)[-1]


def test_a_narrow_terminal_still_delivers_the_cue(world):
	"""The header suffix is clipped at narrow widths exactly as `oblig`
	and `due` already are, so the bottom-row cue is what carries the
	poke there — and it is short enough to survive."""
	poke(world)
	view = console(world)
	screen = Screen(height=14, width=44)
	view.render(screen)
	assert "1 poke waiting for you — Tab to Inbox" in screen.lines()[-1]


def test_a_short_terminal_discloses_a_clipped_detail_block(world):
	seq = poke(world, request="one two three four five six seven eight "
	                          "nine ten eleven twelve thirteen fourteen")
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="waiting", explanation="a\nb\nc\nd\ne\nf\ng\nh")
	view = console(world)
	view.handle(ord("p"))
	screen = Screen(height=12, width=44)
	view.render(screen)
	assert any("more line(s)" in line for line in screen.lines()), \
		screen.lines()


def test_the_operators_own_status_outranks_the_hint(world):
	poke(world)
	view = console(world)
	view.status = "ok seq=3"
	assert painted(view)[-1].startswith("ok seq=3")


# -- the list and its detail -------------------------------------------------

def test_the_view_lists_the_question_its_asker_and_the_action(world):
	seq = poke(world, request="are you still on the parser fix?")
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert view.mode == "pokes"
	row = next(line for line in lines if line.startswith(f"P{seq} "))
	assert "answer" in row, f"the owed row carries no action cue: {row!r}"
	assert "pending" in row, "the canonical state left the row"
	assert "from lang.grace" in row, "the asker is not named"
	assert "are you still on the parser fix?" in row
	# the whole question and its provenance, under the truncating table
	assert any("asked by lang.grace → lang.ada" in line
	           for line in lines), lines
	assert any("j/k select · a answer · Esc back" in line
	           for line in lines), lines[-3:]


def test_the_view_shows_the_answer_beside_the_question(world):
	seq = poke(world, request="status?")
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="working", explanation="mid-way through W17")
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert any("answered working" in line for line in lines), lines
	assert any("mid-way through W17" in line for line in lines), lines


def test_the_view_shows_pokes_this_participant_asked(world):
	"""Both ends of the conversation, because withdrawing is the action
	available on the end this participant asked from."""
	seq = poke(world, asker="ada", target="lang.grace")
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	row = next(line for line in lines if line.startswith(f"P{seq} "))
	assert "to lang.grace" in row, row
	assert "withdraw" in row, "the asker is offered no way to withdraw"


def test_an_empty_view_says_so_rather_than_painting_nothing(world):
	view = console(world)
	view.handle(ord("p"))
	assert any("no pokes" in line for line in painted(view))


def test_owed_pokes_sort_above_history(world):
	answered = poke(world, asker="grace", request="older")
	tr.answer_poke(world["store"], answered, actor_team="lang",
	               actor="ada", state="idle", explanation="done")
	owed = poke(world, asker="sl", team="push", request="newer")
	view = console(world)
	view.handle(ord("p"))
	lines = [line for line in painted(view) if line.startswith("P")]
	assert lines[0].startswith(f"P{owed} "), lines
	assert any(line.startswith(f"P{answered} ") for line in lines), \
		"the answered poke left the view instead of becoming history"
	assert view.poke_seq == owed, \
		"the view opened on history while a question was waiting"


def test_esc_returns_to_the_work_table(world):
	poke(world)
	view = console(world)
	view.handle(ord("p"))
	view.handle(ESC)
	assert view.mode == "table"


# -- the response flow -------------------------------------------------------

def _answer(world, view, index=1, tmp=None, writes="all quiet here"):
	os.environ["EDITOR"] = fake_editor(tmp or world["tmp"], writes=writes)
	view.handle(ord("p"))
	view.handle(ord("a"))
	view.handle(ord(str(index)))


def test_answering_from_the_view_commits_the_canonical_answer(world):
	seq = poke(world, request="what's up?")
	view = console(world)
	_answer(world, view, index=2, writes="reproducing the defect")
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang", viewer_member="ada")["pokes"]
		if entry["poke"] == seq)
	assert row["state"] == "answered", view.status
	assert row["answer"]["state"] == "working", \
		"the chooser's position did not select the state it displayed"
	assert row["answer"]["explanation"] == "reproducing the defect"


def test_the_chooser_offers_exactly_the_grammars_vocabulary(world):
	poke(world)
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	prompt = painted(view)[-1]
	assert view.poke_choice is not None
	for index, state in enumerate(poke_answer_states()):
		assert f"{index + 1} {state}" in prompt, prompt
	assert poke_answer_states() == ("idle", "working", "waiting",
	                                "needs-help"), \
		"the console would silently offer a different vocabulary"


def test_escape_cancels_the_chooser_without_answering(world):
	seq = poke(world)
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	view.handle(ESC)
	assert view.poke_choice is None
	assert view.mode == "pokes", "cancelling the answer left the view"
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang", viewer_member="ada")["pokes"]
		if entry["poke"] == seq)
	assert row["state"] == "pending", "Esc answered the poke"


def test_a_state_key_is_never_also_an_exit(world):
	"""The chooser owns the bottom row while it is open, exactly as the
	exit prompt does — `q` must not quit out from under an answer."""
	poke(world)
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	assert view.handle(ord("q")) is True
	assert view.confirm_exit is False
	assert view.poke_choice is not None


def test_an_empty_explanation_cancels_and_commits_nothing(world):
	seq = poke(world)
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="")
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	view.handle(ord("1"))
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang", viewer_member="ada")["pokes"]
		if entry["poke"] == seq)
	assert row["state"] == "pending", "an empty explanation was submitted"
	assert view.command is not None, \
		"the composed command was dropped instead of handed back"
	assert f"poke-answer poke={seq}" in view.command


def test_without_an_editor_the_composed_command_reaches_the_bar(world):
	"""No editor is a refusal that keeps the operator's place: the exact
	command, with the sequence already filled in, waits in the bar."""
	seq = poke(world)
	os.environ.pop("EDITOR", None)
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	view.handle(ord("1"))
	assert view.command == f"poke-answer poke={seq} state=idle", \
		view.command
	assert "explanation" in (view.command_note or "")


def test_answering_is_refused_where_the_poke_is_not_owed(world):
	"""Only the exact participant a poke names answers it, and the view
	says so without spending an editor round trip to find out."""
	poke(world, asker="ada", target="lang.grace")
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	assert view.poke_choice is None
	assert "only the exact participant" in view.status, view.status


def test_withdrawing_from_the_view_cancels_the_poke_this_one_asked(world):
	seq = poke(world, asker="ada", target="lang.grace")
	os.environ["EDITOR"] = fake_editor(world["tmp"],
	                                   writes="asked by mistake")
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("x"))
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang", viewer_member="ada")["pokes"]
		if entry["poke"] == seq)
	assert row["state"] == "cancelled", view.status


def test_a_terminal_poke_cannot_be_withdrawn_from_the_view(world):
	seq = poke(world, asker="ada", target="lang.grace")
	tr.cancel_poke(world["store"], seq, actor_team="lang", actor="ada",
	               reason="already handled")
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="again")
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("x"))
	assert "cannot be withdrawn" in view.status, view.status


def test_the_operator_is_asked_only_for_the_prose(world):
	"""The whole defect was having to carry a sequence out of raw JSON.
	The document the editor opens names the operation and the one field
	left to write — the selector and the closed state are already
	decided, by the selected row and by the chooser."""
	seq = poke(world)
	seen = str(world["tmp"] / "document.txt")
	os.environ["EDITOR"] = fake_editor(world["tmp"], record=seen,
	                                   writes="fine")
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("a"))
	view.handle(ord("1"))
	document = open(seen, encoding="utf-8").read()
	assert "Baton poke-answer — authoring explanation=" in document, \
		document
	row = next(entry for entry in pj.pokes(
		world["store"], viewer_team="lang", viewer_member="ada")["pokes"]
		if entry["poke"] == seq)
	assert row["state"] == "answered"
	assert row["answer"]["explanation"] == "fine"
	# and the recalled history carries the command WITHOUT the prose,
	# so recall reopens a fresh editor rather than stale text
	assert view.history[-1] == f"poke-answer poke={seq} state=idle", \
		view.history


# -- terminal pokes stop being owed ------------------------------------------

def test_an_answered_poke_stops_being_owed_and_stays_visible(world):
	seq = poke(world)
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="idle", explanation="nothing on my plate")
	assert poke_cue(world) == 0
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	row = next(line for line in lines if line.startswith(f"P{seq} "))
	assert "answered" in row, row
	assert "answer" not in row.replace("answered", ""), \
		f"an answered poke still advertises an action: {row!r}"


def test_a_cancelled_poke_stops_being_owed_and_stays_visible(world):
	seq = poke(world)
	tr.cancel_poke(world["store"], seq, actor_team="lang", actor="grace",
	               reason="found out another way")
	assert poke_cue(world) == 0
	view = console(world)
	view.handle(ord("p"))
	assert any(line.startswith(f"P{seq} ") and "cancelled" in line
	           for line in painted(view))


def test_a_superseded_poke_stops_being_owed_and_stays_visible(world):
	"""One asker re-asking supersedes their earlier pending poke: the
	counter must follow the newest question, not both."""
	first = poke(world, request="first ask")
	second = poke(world, request="second ask")
	assert poke_cue(world) == 1
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert any(line.startswith(f"P{first} ") and "superseded" in line
	           for line in lines), lines
	owed = next(line for line in lines if line.startswith(f"P{second} "))
	assert "answer" in owed


def test_a_timed_out_poke_stops_being_owed_and_stays_visible(world):
	"""Expiry is derived at read time — nothing writes a status — so the
	console must call the row what every other reader calls it."""
	os.environ["BATON_WORK_NOW"] = "2026-08-19T04:00:00Z"
	seq = poke(world, expires_at="2026-08-19T05:00:00Z")
	assert poke_cue(world) == 1
	os.environ["BATON_WORK_NOW"] = "2026-08-19T06:00:00Z"
	assert poke_cue(world) == 0, "a timed-out poke stayed owed"
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert any(line.startswith(f"P{seq} ") and "timed-out" in line
	           for line in lines), lines
	view.handle(ord("a"))
	assert view.poke_choice is None, "a timed-out poke offered an answer"


def test_the_owed_set_survives_a_full_history_window(world):
	"""The history page is bounded and the owed set is not: owed rows
	come from the participant projection, so a window full of old
	answered pokes can never hide an unanswered question."""
	from baton_work.tui import app
	for index in range(app.POKE_PAGE + 2):
		seq = poke(world, asker="grace", request=f"old {index}")
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="ada", state="idle", explanation="done")
	owed = poke(world, asker="sl", team="push", request="the live one")
	assert poke_cue(world) == 1
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert any(line.startswith(f"P{owed} ") and "answer" in line
	           for line in lines), lines
	assert any("not shown" in line for line in lines), \
		"a full history window was not disclosed"


def test_a_full_history_window_keeps_the_newest_terminal_pokes(world):
	"""The bounded history is a RECENT-history window. The canonical
	`pokes` read pages ascending, so sorting its first page backwards is
	not equivalent to opening the newest page: it hides the newest rows
	and then incorrectly says the oldest rows were omitted."""
	latest = None
	for index in range(102):
		latest = poke(world, asker="grace", request=f"status {index}")
		tr.answer_poke(world["store"], latest, actor_team="lang",
		               actor="ada", state="idle",
		               explanation=f"answer {index}")
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert any(line.startswith(f"P{latest} ") for line in lines), \
		"the bounded view kept the oldest page and hid recent history"


def test_the_asker_window_is_the_newest_one_too(world):
	"""R1 covers BOTH narrowings. The pokes this participant sent page
	ascending exactly as the ones sent to them do, and the view is where
	withdrawal is offered — an operator who cannot see the poke they
	just sent cannot withdraw it."""
	latest = None
	for index in range(102):
		latest = poke(world, asker="ada", target="lang.grace",
		              request=f"sent {index}")
		tr.answer_poke(world["store"], latest, actor_team="lang",
		               actor="grace", state="idle",
		               explanation=f"answer {index}")
	view = console(world)
	view.handle(ord("p"))
	lines = painted(view)
	assert any(line.startswith(f"P{latest} ") for line in lines), \
		"the sent-poke window kept its oldest page"


def test_the_walk_reaches_the_tail_across_many_pages(monkeypatch, world):
	"""The window is reached by walking forward, so the loop itself is
	the thing under test — a single fetch large enough to swallow the
	fixture would prove nothing about it."""
	from baton_work.tui import app
	monkeypatch.setattr(app, "POKE_FETCH", 3)
	monkeypatch.setattr(app, "POKE_PAGE", 4)
	latest = None
	for index in range(11):
		latest = poke(world, asker="grace", request=f"walked {index}")
		tr.answer_poke(world["store"], latest, actor_team="lang",
		               actor="ada", state="idle", explanation="done")
	view = console(world)
	view.handle(ord("p"))
	rows, older = view.poke_rows()
	assert [row["poke"] for row in rows] == \
		sorted((row["poke"] for row in rows), reverse=True), rows
	assert rows[0]["poke"] == latest, "the walk stopped short of the tail"
	assert len(rows) == 4 and older == 7, (len(rows), older)


def test_the_disclosure_counts_the_rows_it_actually_omitted(world):
	"""`N older not shown` is a claim about the authority's own rows.
	It is exact or it is misinformation."""
	from baton_work.tui import app
	for index in range(app.POKE_PAGE + 2):
		seq = poke(world, asker="grace", request=f"old {index}")
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="ada", state="idle", explanation="done")
	poke(world, asker="sl", team="push", request="the live one")
	view = console(world)
	view.handle(ord("p"))
	rows, older = view.poke_rows()
	assert len(rows) == app.POKE_PAGE
	assert older == 3, older      # 103 distinct, 100 kept
	assert any(f"{older} older not shown" in line
	           for line in painted(view)), painted(view)[1]


def test_a_window_that_holds_everything_discloses_nothing(world):
	poke(world)
	view = console(world)
	view.handle(ord("p"))
	assert view.poke_rows()[1] == 0
	assert "not shown" not in painted(view)[1], painted(view)[1]


def test_a_self_poke_is_one_row_in_both_windows(world):
	"""The self-poke is the ONE overlap between the two narrowings — the
	end-to-end diagnostic the authority deliberately allows. It must
	appear once, be answerable as owed, and never be counted twice in
	the omission total."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.ada", request="does my own bus work?")["poke"]
	view = console(world)
	view.handle(ord("p"))
	rows, older = view.poke_rows()
	assert [row["poke"] for row in rows] == [seq], rows
	assert older == 0, "the self-poke was counted in both windows"
	painted_rows = [line for line in painted(view)
	                if line.startswith(f"P{seq} ")]
	assert len(painted_rows) == 1, painted_rows
	assert "answer" in painted_rows[0], painted_rows[0]
	assert poke_cue(world) == 1


def test_self_pokes_do_not_inflate_the_omission_total(world):
	"""The correction has to hold when the window is actually full."""
	from baton_work.tui import app
	for index in range(app.POKE_PAGE + 2):
		seq = tr.poke(world["store"], actor_team="lang", actor="ada",
		              target="lang.ada", request=f"self {index}")["poke"]
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="ada", state="idle", explanation="done")
	view = console(world)
	view.handle(ord("p"))
	rows, older = view.poke_rows()
	assert len(rows) == app.POKE_PAGE
	# 102 distinct pokes, each in BOTH windows; naive addition would
	# report 104 and claim 104 - 100 = 4 hidden rows that do not exist.
	assert older == 2, older


# -- selection is stable across refresh --------------------------------------

def test_a_background_refresh_keeps_the_operator_on_the_same_question(world):
	first = poke(world, asker="grace", request="one")
	second = poke(world, asker="sl", team="push", request="two")
	view = console(world)
	view.handle(ord("p"))
	view.handle(ord("j"))
	chosen = view.poke_seq
	assert chosen in (first, second)
	poke(world, asker="sl", team="push", request="three")
	view.schedule_refresh()
	painted(view)
	assert view.poke_seq == chosen, \
		"a refresh moved the cursor onto a different poke"


# -- the real terminal -------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_shows_the_cue_and_opens_the_view(tmp_path):
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
		(b"p", 0.5),
		(b"qy", 0.4),
	])
	table = ptyharness.replay(steps[0])
	assert "[Inbox *]" in table[0], table[0]
	assert any("Tab to Inbox" in line for line in table), table[-3:]
	view = ptyharness.replay(steps[1])
	assert any("are you awake?" in line for line in view), view[:8]
	assert any("a answer" in line for line in view), view[-4:]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
