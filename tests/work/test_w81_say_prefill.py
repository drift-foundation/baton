"""W81 (finding-contextual-say-prefill): `say` seeds from where you read.

Work detail already has one canonical selected Thread, but `:say` opened
an empty bar and made the operator retype that selector. Typing exact
`say` now seeds `say thread=Tn ` — editable, never sent automatically.

The seed is a SNAPSHOT of context: later selection movement must not
retarget a command already being composed. And an explicit `thread=`
always wins, which is not merely a policy but a necessity — paste in a
curses bar is indistinguishable from fast typing, so a pasted
`say thread=T5 ...` necessarily passes through the exact-`say` moment.
"""

from __future__ import annotations

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
from baton_work.tui.app import Console, assist_text           # noqa: E402
import fixtures as fx                                         # noqa: E402


class Screen:
	def addnstr(self, *args):
		pass


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store}
	store.close()


def make(world, title="seeded"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="opener")


def console_at(world, mode="detail"):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.detail_work = console.rows()[0]["id"]
	console.mode = mode
	if mode == "detail":
		console._render_detail(Screen(), 24, 100)
	return console


def typed(console, text, fresh=True):
	"""Every character goes through the ONE real key path — which is
	also how a paste arrives."""
	if fresh:
		console.command = ""
		console.seeded_say = None
	for character in text:
		console.handle(ord(character))
	return console.command


# -- seeding -----------------------------------------------------------------

def test_exact_say_seeds_the_selected_thread(world):
	born = make(world)
	console = console_at(world)
	local = pj.work_threads(world["store"], console.detail_work,
	                        viewer_team="lang",
	                        viewer_member="ada")["rows"][0]["local_id"]
	assert typed(console, "say") == f"say thread={local} "
	assert local == "T2"


def test_the_seed_leaves_the_caret_where_the_next_operand_goes(world):
	make(world)
	console = console_at(world)
	buffer = typed(console, "say")
	assert buffer.endswith(" "), \
		"the seed did not leave room for the next operand"
	# and the assistance is still contextual: body= is what remains
	assert "body=" in assist_text(buffer), assist_text(buffer)


def test_many_threads_seed_the_currently_selected_one(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 subject="second conversation", labels=[work],
	                 body="over here")
	console = console_at(world)
	rows = pj.work_threads(store, work, viewer_team="lang",
	                       viewer_member="ada")["rows"]
	assert len(rows) == 2
	console.disc_cursor = 0
	console._render_detail(Screen(), 24, 100)
	assert typed(console, "say") == f"say thread={rows[0]['local_id']} "
	console.disc_cursor = 1
	console._render_detail(Screen(), 24, 100)
	assert typed(console, "say") == f"say thread={rows[1]['local_id']} "


def test_the_seed_is_the_visible_local_selector(world):
	"""W7 proved the pane's label ORDINAL and a Thread's identity
	diverge once label order differs from creation order. The seed must
	be the selector `say thread=` actually accepts — which is exactly
	what the pane renders."""
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 subject="second", labels=[work], body="b")
	console = console_at(world)
	rows = pj.work_threads(store, work, viewer_team="lang",
	                       viewer_member="ada")["rows"]
	console.disc_cursor = 1
	console._render_detail(Screen(), 24, 100)
	row = rows[1]
	buffer = typed(console, "say")
	assert buffer == f"say thread={row['local_id']} "
	# and it round-trips: the authority resolves the seeded spelling to
	# the very Thread the pane had selected
	resolved = tr.resolve_thread_selector(store, row["local_id"])
	assert resolved == row["id"], \
		"the seeded selector does not name the selected Thread"


# -- where it must NOT seed --------------------------------------------------

def test_the_root_view_invents_no_destination(world):
	make(world)
	console = console_at(world, mode="table")
	assert typed(console, "say") == "say"


def test_a_work_with_no_threads_seeds_nothing(world):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.mode = "detail"
	console.detail_work = None
	assert typed(console, "say") == "say"


def test_other_verbs_are_untouched(world):
	"""`say` is the only verb in the grammar with that prefix, so exact
	match is a safe trigger; every other verb reaches the bar
	unchanged."""
	make(world)
	console = console_at(world)
	for verb in ("claim", "start-thread", "filter", "close", "pass"):
		assert typed(console, verb) == verb, \
			f"{verb} picked up the say seed"


# -- explicit values win -----------------------------------------------------

def test_a_pasted_explicit_thread_displaces_the_seed(world):
	"""The whole command arrives character by character, exactly as a
	paste does, so it passes through the exact-`say` moment."""
	make(world)
	console = console_at(world)
	assert typed(console, "say thread=T9 body=hello") == \
		"say thread=T9 body=hello"
	assert console.command.count("thread=") == 1, \
		"the seed duplicated the pasted operand"


def test_a_typed_explicit_thread_displaces_the_seed(world):
	make(world)
	console = console_at(world)
	typed(console, "say")
	typed(console, "thread=T7 body=x", fresh=False)
	assert console.command.count("thread=") == 1
	assert "thread=T7" in console.command
	assert "thread=T2" not in console.command


def test_repeated_spacing_and_editing_never_duplicates(world):
	make(world)
	console = console_at(world)
	typed(console, "say")
	first = console.command
	typed(console, "   ", fresh=False)
	assert console.command.count("thread=") == 1
	# backspace back through the seed and retype: still exactly one
	for _ in range(len(console.command)):
		console.handle(127)
	typed(console, "say", fresh=False)
	assert console.command.count("thread=") <= 1


def test_editing_the_seed_away_by_hand_is_respected(world):
	make(world)
	console = console_at(world)
	typed(console, "say")
	for _ in range(4):
		console.handle(127)
	assert console.seeded_say is None, \
		"a hand-edited seed is still being managed by the client"


# -- R1: explicit operands are recognised OUTSIDE quoted values --------------

@pytest.mark.parametrize("tail,kept", [
	# quoted VALUES that merely contain the text
	('body="diagnostic contains thread=value"', True),
	("body='single quoted thread=value'", True),
	('body="two thread=a and thread=b here"', True),
	('body="trailing thread="', True),
	# a genuine operand, in every position
	("thread=T7", False),
	('body="mentions thread=x" thread=T7', False),
	("thread=T7 body=\"and thread=y\"", False),
])
def test_only_a_real_operand_displaces_the_seed(world, tail, kept):
	"""A substring count is not operand-aware, and its failure is silent
	in the worst direction: a valid contextual reply becomes a command
	with NO destination."""
	make(world)
	console = console_at(world)
	typed(console, "say")
	seeded = console.command
	typed(console, " " + tail, fresh=False)
	found = console._explicit_operands(console.command, "thread=")
	if kept:
		assert console.seeded_say is not None, \
			f"quoted text displaced the real seed: {console.command!r}"
		assert "thread=T2" in console.command
		assert found == 1, \
			f"a quoted value was counted as an operand: {console.command!r}"
	else:
		assert found == 1, \
			f"the seed was not displaced: {console.command!r}"
		assert "thread=T7" in console.command
		assert console.seeded_say is None


def test_an_open_quote_keeps_the_seed_rather_than_dropping_it(world):
	"""The bar is edited character by character, so this runs constantly
	against INCOMPLETE input. An unterminated quote must fail SAFE — it
	may only keep the seed, never silently remove it."""
	make(world)
	console = console_at(world)
	typed(console, "say")
	typed(console, ' body="still typing thread=', fresh=False)
	assert console.seeded_say is not None, \
		f"an open quote dropped the destination: {console.command!r}"
	assert "thread=T2" in console.command
	# and closing the quote still leaves it a value, not an operand
	typed(console, 'value"', fresh=False)
	assert console.seeded_say is not None
	assert console._explicit_operands(console.command, "thread=") == 1


def test_escaped_quotes_inside_a_value_do_not_end_it(world):
	make(world)
	console = console_at(world)
	typed(console, "say")
	typed(console, r' body="a \" thread=still-inside"', fresh=False)
	assert console.seeded_say is not None, console.command
	assert console._explicit_operands(console.command, "thread=") == 1


def test_operand_detection_uses_the_command_grammar_itself(world):
	"""W81 R3. Detection and execution must not be able to disagree, so
	this reads through `cli._partial_tokens` — the same partial-`shlex`
	interpretation the parser and the assistance already share — rather
	than a second approximate lexer.

	The two directions that broke a hand-rolled one are both here: a
	quoted value must not count, and an ESCAPED space is not a token
	boundary at all, so what follows it is still part of the same
	value."""
	count = Console._explicit_operands
	assert count("say thread=T2 body=x", "thread=") == 1
	assert count("say thread=T2 thread=T7", "thread=") == 2
	# quoted values (R1)
	assert count('say thread=T2 body="quoted thread=x"', "thread=") == 1
	assert count("say thread=T2 body='quoted thread=x'", "thread=") == 1
	# escaped whitespace (R3): shlex joins this into ONE body operand
	assert count("say thread=T2 body=diagnostic\\ thread=value",
	             "thread=") == 1
	assert count("say body=a\\ thread=b", "thread=") == 0
	# an escaped spelling shlex RESOLVES into a genuine operand counts,
	# because by then it genuinely is one
	assert count("say thread=T2 thr\\ead=T7", "thread=") == 2
	# incomplete input never over-counts
	assert count('say thread=T2 body="open thread=', "thread=") == 1
	assert count("say ", "thread=") == 0


@pytest.mark.parametrize("tail,kept", [
	# escaped whitespace keeps the value whole, so the seed survives
	("body=diagnostic\\ thread=value", True),
	("body=a\\ b\\ thread=c", True),
	# a genuine operand still displaces it, however it is spelled
	("thread=T7", False),
	("thr\\ead=T7", False),
])
def test_escaped_whitespace_never_displaces_the_seed(world, tail, kept):
	make(world)
	console = console_at(world)
	typed(console, "say")
	typed(console, " " + tail, fresh=False)
	if kept:
		assert console.seeded_say is not None, \
			f"escaped whitespace displaced the destination: " \
			f"{console.command!r}"
		assert "thread=T2" in console.command
	else:
		assert console.seeded_say is None, \
			f"a genuine operand did not displace the seed: " \
			f"{console.command!r}"
		# the buffer may hold an ESCAPED spelling; what matters is what
		# execution will see
		import shlex
		assert "thread=T7" in shlex.split(console.command), \
			f"the surviving operand is not the explicit one: " \
			f"{console.command!r}"


def test_detection_agrees_with_execution_on_every_shape(world):
	"""The property the reuse buys: whatever the buffer, the number of
	`thread=` operands detected equals the number `shlex` hands to
	execution."""
	import shlex
	for command in (
			"say thread=T2 body=x",
			"say thread=T2 thread=T7",
			'say thread=T2 body="quoted thread=x"',
			"say thread=T2 body=diagnostic\\ thread=value",
			"say thread=T2 thr\\ead=T7",
			"say body=plain"):
		detected = Console._explicit_operands(command, "thread=")
		executed = sum(1 for token in shlex.split(command)[1:]
		               if token.startswith("thread="))
		assert detected == executed, \
			f"detection and execution disagree on {command!r}: " \
			f"{detected} vs {executed}"


# -- R2: Events has no visible selected Thread -------------------------------

def test_events_does_not_invent_a_destination(world):
	"""The seed means reply where I am READING. With Events active there
	is no visible selected Thread, so the retained Messages cursor must
	not be used behind the operator's back."""
	make(world)
	console = console_at(world)
	console.handle(ord("]"))
	console._render_detail(Screen(), 24, 100)
	assert console.detail_tab == "events"
	assert typed(console, "say") == "say"
	assert console.seeded_say is None
	# returning to Messages restores the ordinary behaviour. The bar has
	# to be closed first: while it is open `[`/`]` are ordinary text,
	# which is itself the correct behaviour and asserted below.
	console.handle(27)
	console.handle(ord("["))
	console._render_detail(Screen(), 24, 100)
	assert console.detail_tab == "messages"
	assert typed(console, "say") == "say thread=T2 "


def test_bracket_keys_are_literal_text_inside_the_command_bar(world):
	"""Tab switching is a view-level move; while a command is being
	composed those keys belong to the buffer."""
	make(world)
	console = console_at(world)
	typed(console, "say")
	before_tab = console.detail_tab
	typed(console, "]", fresh=False)
	assert console.detail_tab == before_tab, \
		"a keystroke meant for the command bar switched tabs"
	assert console.command.endswith("]")


def test_a_seed_already_in_flight_is_never_retargeted_by_a_tab_change(
		world):
	"""Snapshot-safe in the other direction. The tab cannot actually
	change while the bar is open, so the property is tested at its real
	boundary: once seeded, `_reconcile_say_seed` never re-derives the
	selector, whatever the tab state says."""
	make(world)
	console = console_at(world)
	buffer = typed(console, "say")
	console.detail_tab = "events"          # the state the UI cannot reach
	typed(console, "body=x", fresh=False)
	assert console.command == buffer + "body=x", \
		"a tab change retargeted or erased a command in flight"
	assert "thread=T2" in console.command


# -- the seed is a snapshot ---------------------------------------------------

def test_later_selection_movement_never_retargets_the_command(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 subject="second", labels=[work], body="b")
	console = console_at(world)
	console.disc_cursor = 0
	console._render_detail(Screen(), 24, 100)
	buffer = typed(console, "say")
	# the operator moves the selection while composing
	console.disc_cursor = 1
	console._render_detail(Screen(), 24, 100)
	assert console.command == buffer, \
		"selection movement retargeted a command already in flight"


def test_refresh_and_resize_leave_the_buffer_alone(world):
	make(world)
	console = console_at(world)
	buffer = typed(console, "say")
	console.schedule_refresh()
	console._render_detail(Screen(), 24, 44)
	console._render_detail(Screen(), 40, 200)
	assert console.command == buffer


# -- purity and delivery ------------------------------------------------------

def test_opening_editing_and_cancelling_write_nothing(world):
	store = world["store"]
	born = make(world)
	before_seq = store.last_seq()
	before_new = pj.thread(store, born["thread"], viewer_team="lang",
	                       viewer_member="ada")["new"]
	console = console_at(world)
	typed(console, "say")
	typed(console, "body=drafted", fresh=False)
	console.handle(27)                     # Esc cancels
	assert console.command is None
	assert console.seeded_say is None, "a cancelled seed was retained"
	assert store.last_seq() == before_seq, \
		"composing a command wrote to the authority"
	assert pj.thread(store, born["thread"], viewer_team="lang",
	                 viewer_member="ada")["new"] == before_new, \
		"composing a command advanced a seen cursor"


def test_the_seeded_command_posts_only_to_that_thread(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 subject="the other one", labels=[work], body="b")
	console = console_at(world)
	rows = pj.work_threads(store, work, viewer_team="lang",
	                       viewer_member="ada")["rows"]
	console.disc_cursor = 0
	console._render_detail(Screen(), 24, 100)
	target = rows[0]["local_id"]
	typed(console, "say")
	typed(console, 'body="the reply"', fresh=False)
	console.handle(10)                     # Enter executes
	assert console.status == "" or "not a key=value" not in console.status, \
		console.status
	seeded = next(row for row in rows if row["local_id"] == target)
	delivered = pj.thread(store, seeded["id"], viewer_team="lang",
	                      viewer_member="ada")
	assert any(m["body"] == "the reply" for m in delivered["messages"]), \
		"the reply did not reach the seeded Thread"
	untouched = next(row for row in rows if row["local_id"] != target)
	elsewhere = pj.thread(store, untouched["id"], viewer_team="lang",
	                      viewer_member="ada")
	assert not any(m["body"] == "the reply"
	               for m in elsewhere["messages"]), \
		"the reply reached a Thread the operator was not reading"
