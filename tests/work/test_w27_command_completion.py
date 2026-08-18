"""W27: Tab completes what the assistant already knows.

The command bar could already tell an operator which verbs, keys and
closed values were valid — and then made them type every character of
`outcome=non-satisfying` anyway. Tab turns that same analysis into
conservative editing.

Conservative is the operative word. A unique candidate completes and
appends its ruled delimiter; several extend only their common prefix; a
repeated Tab that can make no further progress does nothing and leaves
the assist line as the candidate display. Nothing here becomes accepted
grammar: shorthand is an input gesture, and execution still demands full
canonical spellings.
"""

from __future__ import annotations

import curses
import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

TAB = 9


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug", title="w",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")
	yield {"store": store, "config": config_path, "work": born["work_id"],
	       "thread": born["thread"], "database": database}
	store.close()


def _complete(text):
	return cli.complete_partial(text)


def _console(world, work_filter=None):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"], work_filter=work_filter)
	console.command = ""
	return console


def _type(console, text):
	for character in text:
		console.handle(TAB if character == "\t" else ord(character))


# -- the analyzer ------------------------------------------------------------

def test_a_unique_command_prefix_completes_with_a_space():
	result = _complete("clo")
	assert result["buffer"] == "close "
	assert result["progressed"] is True


def test_a_unique_operand_prefix_completes_through_the_equals():
	"""'`ou<Tab>` in a `close` command becomes `outcome=`'."""
	assert _complete("close ou")["buffer"] == "close outcome="


@pytest.mark.parametrize("typed,expected", [
	("sat", "close outcome=satisfying "),
	("non", "close outcome=non-satisfying "),
	("rej", "close outcome=rejected "),
	("can", "close outcome=cancelled "),
])
def test_a_unique_closed_value_completes_whole_with_a_space(typed, expected):
	"""Both examples the ruling names, plus the rest of the vocabulary —
	`non` is the one that matters, because a naive prefix walk over
	`non-satisfying` is where an operator most wants the help."""
	assert _complete(f"close outcome={typed}")["buffer"] == expected


def test_several_candidates_extend_only_the_common_prefix():
	result = _complete("cl")
	assert result["buffer"].startswith("cl")
	assert result["buffer"] != "cl " and not result["buffer"].endswith(" ")
	assert len(result["candidates"]) > 1


def test_no_progress_leaves_the_buffer_exactly(world):
	"""'If that makes no progress, the existing hint area lists the
	candidates; a repeated Tab does not silently choose one.'"""
	first = _complete("close o")
	assert first["buffer"] == "close o"
	assert first["progressed"] is False
	assert first["candidates"] == ["op-id=", "outcome="]
	# and a second Tab is the same answer, not a rotation
	second = _complete(first["buffer"])
	assert second["buffer"] == first["buffer"]
	assert second["candidates"] == first["candidates"]


def test_no_candidate_leaves_the_buffer_and_the_diagnostic():
	for line in ("zzz", "close nosuchkey", "close outcome=zzz"):
		result = _complete(line)
		assert result["buffer"] == line, line
		assert result["progressed"] is False


@pytest.mark.parametrize("line", [
	# these fall to a diagnostic on their own …
	'close rationale="it is ',
	"close rationale='half",
	# … and this one does NOT: the live token is a clean key prefix and
	# the analysis is `operands`, so only the open-quote guard stops
	# completion writing `close "outcome=` and stranding the quote it
	# would have to reopen. Without a case like it the guard looks
	# load-bearing and is not exercised at all.
	'close "ou',
	"close 'outcome=sat",
])
def test_an_open_quote_is_never_rewritten(line):
	"""Completion replaces only the live token and never touches
	quoting, so inside an open quoted value it declines."""
	result = _complete(line)
	assert result["buffer"] == line, line
	assert result["progressed"] is False


def test_earlier_text_and_quoting_survive_byte_for_byte():
	line = 'close work=W2 rationale="a quoted reason" ou'
	result = _complete(line)
	assert result["buffer"] == line[:-2] + "outcome="
	assert result["buffer"].startswith(
		'close work=W2 rationale="a quoted reason" ')


def test_an_embedded_equals_in_a_value_is_left_alone():
	line = 'say body="a=b" thr'
	result = _complete(line)
	assert result["buffer"] == 'say body="a=b" thread='


# -- the effective candidate set --------------------------------------------

def test_a_supplied_singular_key_is_not_offered_again():
	"""`key_matches` alone is not the answer: a key already supplied
	would be refused by the parser, and completing to it would be
	completing to a refusal."""
	assert "outcome=" not in _complete("close outcome=satisfying ou")["candidates"]
	assert _complete("close outcome=satisfying ou")["progressed"] is False


def test_a_repeatable_key_stays_available():
	first = _complete("close ref=baton:a.md re")
	assert "ref=" in first["candidates"] or first["buffer"].endswith("ref=")


def test_an_exactly_one_choice_is_offered_until_one_is_chosen():
	"""`accept` takes exactly one of `into=` / `create=`."""
	offered = _complete("accept obligation=4 i")
	assert offered["buffer"].endswith("into=") or "into=" in offered["candidates"]
	# once chosen, the alternative is no longer a candidate
	after = _complete("accept obligation=4 into=W9 cr")
	assert "create=" not in after["candidates"]
	assert after["progressed"] is False


def test_a_conditionally_forbidden_key_is_not_offered():
	"""Completing to a key the form conditions forbid would be
	completing to something the parser then refuses."""
	result = _complete("pass work=W2 to=lang.bug ph")
	assert result["progressed"] is False
	assert "phase=" not in result["candidates"]


# -- the bar -----------------------------------------------------------------

def test_tab_completes_in_the_bar(world):
	console = _console(world)
	_type(console, "clo\t")
	assert console.command == "close "


def test_tab_never_executes(world):
	console = _console(world)
	before = console.status
	_type(console, "clo\t")
	assert console.command is not None, "Tab submitted the line"
	assert console.status == before


def test_tab_on_an_empty_bar_is_inert_or_common(world):
	console = _console(world)
	console.handle(TAB)
	assert console.command in ("", cli.complete_partial("")["buffer"])
	assert console.command is not None


def test_the_say_seed_survives_verb_completion(world):
	"""'`sa<Tab>` may not produce an unseeded `say `.'

	Seeding fires at the moment the buffer becomes exactly `say`, which
	assigning the finished completion would skip entirely."""
	console = _console(world)
	console.detail_work = world["work"]
	console.mode = "detail"

	class Screen:
		def addnstr(self, *args, **kwargs):
			pass

	console._render_detail(Screen(), 30, 110)
	console.command = ""
	_type(console, "sa\t")
	assert console.command.startswith("say thread="), \
		f"verb completion bypassed the say seed: {console.command!r}"
	assert console.command.endswith(" ")


def test_the_filter_seed_survives_verb_completion(world):
	"""'`fi<Tab>` may not bypass editable current-filter seeding.'"""
	console = _console(world, work_filter={"status": "open"})
	_type(console, "fi\t")
	assert console.command == "filter status=open", \
		f"verb completion bypassed the filter seed: {console.command!r}"


def test_completion_composes_with_ordinary_editing(world):
	console = _console(world)
	_type(console, "clo\t")
	_type(console, "ou\t")
	_type(console, "sat\t")
	assert console.command == "close outcome=satisfying "
	console.handle(curses.KEY_BACKSPACE)
	assert console.command == "close outcome=satisfying"


def test_search_to_completion_is_one_gesture(world):
	"""'Tab first adopts the displayed history match into the normal
	buffer and then runs this same completion operation.'"""
	console = _console(world)
	console.history = ["clo"]
	console.handle(18)                    # Ctrl-R
	console.handle(TAB)
	assert console.reverse is None, "search did not close"
	assert console.command == "close ", console.command


def test_right_still_adopts_without_completing(world):
	console = _console(world)
	console.history = ["clo"]
	console.handle(18)
	console.handle(curses.KEY_RIGHT)
	assert console.command == "clo", \
		"Right completed as well as adopting"


def test_batch_input_is_untouched(world):
	"""'it does not … change `::` batch input.'"""
	console = _console(world)
	console.handle(ord(":"))              # `::` opens the batch buffer
	assert console.batch is not None
	before = list(console.batch)
	console.handle(TAB)
	assert console.batch == before or console.batch[0] != "close ", \
		"Tab completed inside the batch buffer"


# -- purity ------------------------------------------------------------------

def test_completion_reads_no_authority(world):
	"""'performs no authority/config/filesystem read.'"""
	before = hashlib.sha256(
		open(world["database"], "rb").read()).digest()
	last = world["store"].last_seq()
	console = _console(world)
	for line in ("clo\t", "close ou\t", "close outcome=sat\t", "cl\t"):
		console.command = ""
		_type(console, line)
	assert world["store"].last_seq() == last, "Tab mutated the authority"
	assert hashlib.sha256(
		open(world["database"], "rb").read()).digest() == before


def test_the_analyzer_is_pure_of_the_console():
	"""Completion lives beside the grammar, not in curses: the analyzer
	answers without a Console at all."""
	assert cli.complete_partial("clo")["buffer"] == "close "


def test_shorthand_is_never_accepted_grammar(world):
	"""'Full spellings remain mandatory at execution; shorthand is an
	input gesture, not accepted grammar.'"""
	from baton_work.cli import main
	assert main(["--config", world["config"], "--participant", "lang.ada",
	             "clo"]) == 1


# -- a real terminal ---------------------------------------------------------

@pytest.mark.serial
def test_tab_completes_on_a_real_terminal(world):
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b":", 0.5), (b"clo", 0.4), (b"\t", 0.6), (b"\x1b", 0.4),
		 (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	completed = "\n".join(ptyharness.replay(steps[2], columns=110, lines=24))
	assert ":close" in completed, \
		f"Tab did not complete on a real terminal: {completed[-300:]}"


@pytest.mark.serial
def test_an_ambiguous_tab_leaves_the_candidates_visible(world):
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b":", 0.5), (b"cl", 0.4), (b"\t", 0.6), (b"\x1b", 0.4),
		 (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	screen = ptyharness.replay(steps[2], columns=110, lines=24)
	bar = screen[-1]
	assert ":cl" in bar, bar
	assert "close" in "\n".join(screen), \
		"the ambiguous candidates are not displayed"
