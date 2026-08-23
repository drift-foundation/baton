"""W36: authoring command prose in the operator's own editor.

`work/records/2026/08/finding-editor-backed-command-text/`. Several
operations need human prose — `body`, `rationale`, `comment` — and
quoting paragraphs into the single-row `:` bar is costly and fragile.
This is deliberately separate from W35: cursor editing serves small
corrections, this serves substantial text.

The 2026-08-18 ruling, approved by Slawomir:

- Enter parses far enough to see the operation and its operands. A
  SUPPLIED prose operand executes normally; a MISSING required one opens
  a contextual Git-commit-style template instead of returning the bare
  missing-operand refusal. No editor token in the grammar, no extra
  command, no key chord.
- Grammar METADATA, not a hard-coded verb list, says which operand this
  is.
- `EDITOR` only, parsed to an argument vector without a shell. Unset,
  malformed, unlaunchable or unsuccessful keeps the draft and reports.
- A successful save resumes the same canonical execution path. An
  unchanged template or empty body cancels and restores the draft.
- History stores the surrounding command WITHOUT the generated prose, so
  recall opens a fresh editor rather than carrying stale text.
- Only Baton's generated LEADING instructional block is removed; comment
  characters elsewhere are content.
"""

from __future__ import annotations

import curses
import hashlib
import json as _json
import os
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
from baton_work.tui.app import (Console, prose_template,        # noqa: E402
                                strip_prose_template)
import fixtures as fx                                          # noqa: E402

ENTER = 10
ESC = 27


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	console = Console(store, "lang", "ada", config_path=config_path)
	yield {"store": store, "config": config_path, "database": database,
	       "console": console, "tmp": tmp_path}
	store.close()


@pytest.fixture(autouse=True)
def _no_inherited_editor():
	"""Every test states its own EDITOR, so an editor in the developer's
	environment can never make one of these pass by accident."""
	saved = os.environ.pop("EDITOR", None)
	yield
	if saved is None:
		os.environ.pop("EDITOR", None)
	else:
		os.environ["EDITOR"] = saved


def fake_editor(tmp_path, name="ed", *, writes=None, exit_code=0,
                record=None, leave_unchanged=False):
	"""A DETERMINISTIC editor: no terminal, no interaction, and it
	records exactly the argv it was given so argument safety is
	observable rather than assumed."""
	script = tmp_path / f"{name}.py"
	body = [
		"import json, os, sys",
		"argv = sys.argv[1:]",
		f"record = {record!r}",
		"if record:",
		"    open(record, 'w').write(json.dumps(argv))",
		"path = argv[-1]",
		f"if not {leave_unchanged!r}:",
	]
	if writes is None:
		body.append("    open(path, 'w', encoding='utf-8').write('')")
	else:
		body.append("    original = open(path, encoding='utf-8').read()")
		body.append(f"    open(path, 'w', encoding='utf-8')"
		            f".write(original + {writes!r})")
	body.append(f"sys.exit({exit_code})")
	script.write_text("\n".join(body) + "\n", encoding="utf-8")
	return f"{sys.executable} {script}"


def submit(console, text):
	console.handle(ord(":"))
	for character in text:
		console.handle(ord(character))
	console.handle(ENTER)


def digest(world):
	return _digest_of(world["database"])


def _digest_of(database):
	"""Every file the authority commits into.

	WAL mode means a commit lands in `-wal` and reaches the main file
	only at a checkpoint — and this suite keeps its own connection open,
	so no checkpoint happens. Hashing the database alone would make
	"nothing changed" true no matter what committed, which is a purity
	assertion that cannot fail."""
	blob = b""
	# The database and its write-ahead log, and NOT `-shm`: the shared
	# memory index is rewritten by ordinary reads, so including it would
	# make "nothing changed" fail for a pure read — the opposite defect.
	for suffix in ("", "-wal"):
		try:
			with open(database + suffix, "rb") as handle:
				blob += handle.read()
		except FileNotFoundError:
			pass
	return hashlib.sha256(blob).hexdigest()


def make_work(world, title="a bug"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="opener")


# -- the grammar decides, not a verb list ------------------------------------

@pytest.mark.parametrize("line,expected", [
	# the operand is missing and is the only thing left
	("say thread=T1", "body"),
	("close work=W1 outcome=satisfying", "rationale"),
	("pass work=W1 to=baton.bug", "comment"),
	("report obligation=3 evidence=e", "observation"),
	("release work=W1 expect=lang.ada episode=7", "reason"),
	# CONDITIONALLY required, and the analyzer knows it: parking needs a
	# reason, every other phase move does not
	("phase work=W1 to=parked", "reason"),
	("phase work=W1 to=queued", None),
	# supplied: nothing special happens
	("say thread=T1 body=hi", None),
	("close work=W1 outcome=satisfying rationale=done", None),
	# a missing NON-prose operand still refuses normally
	("close work=W1 rationale=done", None),
	("detail work=W1", None),
	# and prose is not the last thing missing: the ordinary refusal
	# names everything at once instead of spending the operator's prose
	("close work=W1", None),
	("report obligation=3", None),
	# malformed or unknown never opens an editor
	("nonsense", None),
	('say body="unterminated', None),
	("", None),
])
def test_the_grammar_answers_which_operand_needs_an_editor(line, expected):
	assert _cli.missing_prose_operand(line) == expected


def test_prose_is_metadata_on_the_one_declarative_grammar():
	"""Not a second hand-maintained verb list — which is exactly what
	the finding asks for, because a list drifts from the parser."""
	marked = {(verb, entry["name"])
	          for verb, info in _cli.GRAMMAR.items()
	          for entry in info["keys"] if entry.get("prose")}
	names = {name for _verb, name in marked}
	assert names == {"body", "comment", "observation", "rationale",
	                 "reason"}, names
	# every verb carrying one of those operands is covered, with no
	# per-verb enumeration anywhere
	for verb, info in _cli.GRAMMAR.items():
		for entry in info["keys"]:
			assert (entry["name"] in names) == bool(entry.get("prose")), \
				f"{verb} {entry['name']} disagrees with its own name"


# -- the template ------------------------------------------------------------

def test_an_opened_editor_is_never_an_unexplained_empty_file():
	document = prose_template("close", "rationale",
	                          ["Work W5 — the title", "Participant lang.ada"])
	assert document.startswith("# Baton close — authoring rationale=")
	assert "Work W5 — the title" in document
	assert "Participant lang.ada" in document
	# it names how to save, how to cancel, and which comments vanish
	assert "Save and exit" in document
	assert "cancel" in document
	assert "further down is kept" in document
	# and it ends with a blank line, so the body starts where it says
	assert document.endswith("\n\n")
	# every generated line is a comment, which is what makes the removal
	# rule able to guarantee no leak
	block = document.rstrip("\n").split("\n")
	assert all(line.startswith("#") for line in block), block


def test_the_template_is_never_submitted_and_leaves_no_trace():
	document = prose_template("say", "body", ["Thread T3"])
	assert strip_prose_template(document) == ""
	assert strip_prose_template(document + "the answer\n") == "the answer"
	# even an EDITED instructional line cannot leak: the rule is
	# positional, because a rule that only removed lines it still
	# recognised would leak the moment somebody touched one
	tampered = document.replace("Save and exit", "SAVE AND EXIT")
	assert strip_prose_template(tampered + "real\n") == "real"


@pytest.mark.parametrize("authored", [
	"one line",
	"two\nlines",
	"quotes \"double\" and 'single' and `back`",
	"a=b c=d looks like operands",
	"unicode: 漢字 — ñ — 🎯",
	"trailing spaces   ",
	"\nstarts with a blank line",
	"ends with a blank line\n",
	"# a comment line the user wrote",
	"real\n# mine\nmore",
	"x" * 5000,
])
def test_the_authored_body_round_trips_byte_for_byte(authored):
	"""Everything after the leading block and its one blank separator is
	content. The only normalization is the editor's own final
	newline."""
	document = prose_template("say", "body", [])
	assert strip_prose_template(document + authored + "\n") == authored


def test_only_the_LEADING_comment_run_is_removed():
	document = prose_template("say", "body", [])
	body = "# this one is mine\nand this is prose"
	assert strip_prose_template(document + body + "\n") == body
	# a document with no block at all (the operator deleted it) is all
	# content
	assert strip_prose_template("just prose\n") == "just prose"


# -- the round trip ----------------------------------------------------------

def test_a_missing_prose_operand_opens_the_editor_and_submits(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = fake_editor(
		world["tmp"], writes="delivered against the acceptance boundary")

	submit(console, f"close work={work} outcome=satisfying")

	assert console.command is None, "the bar did not close on success"
	row = pj.detail(world["store"], work, viewer_team="lang",
	                viewer_member="ada")
	assert row["status"] == "closed"
	assert row["rationale"] == "delivered against the acceptance boundary"


def test_a_supplied_operand_never_invokes_the_editor(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	seen = str(world["tmp"] / "argv.json")
	os.environ["EDITOR"] = fake_editor(world["tmp"], record=seen,
	                                   writes="from the editor")

	submit(console, f"close work={work} outcome=satisfying "
	                f"rationale=typed-inline")
	assert not os.path.exists(seen), "the editor ran for a supplied operand"
	row = pj.detail(world["store"], work, viewer_team="lang",
	                viewer_member="ada")
	assert row["rationale"] == "typed-inline"


def test_multiline_unicode_prose_reaches_the_authority_exactly(world):
	"""The value is appended as an argv TOKEN, not spliced back into a
	command string, so there is no second round of shell quoting for it
	to survive."""
	console = world["console"]
	work = make_work(world)["work_id"]
	prose = ("First paragraph with \"quotes\" and a=b.\n"
	         "\n"
	         "Second paragraph — 漢字, and a # comment line.\n"
	         "  indented tail")
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes=prose)

	submit(console, f"close work={work} outcome=satisfying")
	row = pj.detail(world["store"], work, viewer_team="lang",
	                viewer_member="ada")
	assert row["rationale"] == prose


def test_the_editor_is_an_argument_vector_with_no_shell(world):
	"""`EDITOR` is SPLIT, never handed to a shell.

	The environment must not become a command-injection surface for a
	feature whose whole job is to open a text file, so shell
	metacharacters arrive at the editor as literal argument text. A
	quoted argument stays one argument, which is also what keeps a
	temporary path containing a space from being word-split."""
	console = world["console"]
	work = make_work(world)["work_id"]
	seen = str(world["tmp"] / "argv.json")
	editor = fake_editor(world["tmp"], record=seen, writes="ok")
	# `$(...)` and `;` a shell would ACT on, kept as one word so the
	# assertion is about evaluation rather than word-splitting.
	os.environ["EDITOR"] = (editor + ' "--note=one argument" '
	                        "--shell=$(echo);true")
	submit(console, f"close work={work} outcome=satisfying")
	recorded = _json.loads(open(seen).read())
	# the shell forms are TEXT, not effects
	assert "--shell=$(echo);true" in recorded, recorded
	# the quoted argument survived as exactly one argument
	assert "--note=one argument" in recorded, recorded
	# and the draft is the last argument, whole
	assert os.path.basename(recorded[-1]).startswith("baton-prose-")
	assert len(recorded) == 3, recorded


def test_the_draft_is_private_and_removed_afterwards(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	seen = str(world["tmp"] / "argv.json")
	mode = str(world["tmp"] / "mode.txt")
	script = world["tmp"] / "checker.py"
	script.write_text(
		"import json, os, sys\n"
		"path = sys.argv[-1]\n"
		f"open({seen!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
		f"open({mode!r}, 'w').write(oct(os.stat(path).st_mode & 0o777))\n"
		"open(path, 'a', encoding='utf-8').write('authored')\n",
		encoding="utf-8")
	os.environ["EDITOR"] = f"{sys.executable} {script}"
	submit(console, f"close work={work} outcome=satisfying")
	assert open(mode).read() == "0o600", open(mode).read()
	path = _json.loads(open(seen).read())[-1]
	assert not os.path.exists(path), "the draft survived the round trip"


# -- every way it can fail, safely -------------------------------------------

def _assert_draft_kept(console, line, note_matches):
	assert console.command == line, \
		f"the draft was not handed back intact: {console.command!r}"
	assert console.command_caret == len(line)
	assert note_matches in (console.command_note or ""), \
		console.command_note


def test_an_unset_editor_refuses_and_keeps_the_draft(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	before = digest(world)
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	_assert_draft_kept(console, line, "set EDITOR")
	assert digest(world) == before, "a refused editor touched the authority"
	# never silently chosen: nothing ran
	assert pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["status"] == "open"


def test_an_unlaunchable_editor_refuses_and_keeps_the_draft(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = str(world["tmp"] / "no-such-editor")
	line = f"close work={work} outcome=satisfying"
	before = digest(world)
	submit(console, line)
	_assert_draft_kept(console, line, "could not run")
	assert digest(world) == before


def test_a_malformed_editor_value_refuses_and_keeps_the_draft(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = '"unterminated'
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	_assert_draft_kept(console, line, "not a usable command")


def test_a_nonzero_exit_cancels_without_submitting(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	before = digest(world)
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="written anyway",
	                                   exit_code=3)
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	_assert_draft_kept(console, line, "editor exited 3")
	assert digest(world) == before, \
		"a failed editor still reached the authority"


def test_an_interrupted_editor_restores_the_draft_and_cleans_up(world,
		monkeypatch):
	"""The acceptance boundary names interruption separately from a
	nonzero child exit. `subprocess.run` raises `KeyboardInterrupt` when
	the foreground editor and Baton receive SIGINT together; that must
	become the same safe cancellation as another failed editor, not tear
	down the TUI after `_command_key` has already closed the bar."""
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = "a-configured-editor"
	line = f"close work={work} outcome=satisfying"
	before = digest(world)
	paths = []

	def interrupted(argv, **_kwargs):
		paths.append(argv[-1])
		raise KeyboardInterrupt

	monkeypatch.setattr("baton_work.tui.app.subprocess.run", interrupted)
	submit(console, line)

	_assert_draft_kept(console, line, "interrupted")
	assert digest(world) == before, \
		"an interrupted editor reached the authority"
	assert len(paths) == 1 and not os.path.exists(paths[0]), \
		"the interrupted editor left its private draft behind"


def test_an_unchanged_template_cancels_without_submitting(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	before = digest(world)
	os.environ["EDITOR"] = fake_editor(world["tmp"], leave_unchanged=True)
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	_assert_draft_kept(console, line, "left empty")
	assert digest(world) == before


def test_a_whitespace_only_body_cancels_rather_than_submitting_nothing(world):
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="   \n\n\t\n")
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	_assert_draft_kept(console, line, "left empty")


def test_the_restored_draft_is_immediately_editable(world):
	"""`returns to the intact command draft` means the bar, with a
	caret — the operator fixes the line or presses Esc, and the note
	retires on the next key like any other transient."""
	console = world["console"]
	work = make_work(world)["work_id"]
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	assert console.command_note
	console.handle(curses.KEY_LEFT)
	assert console.command_note is None, "the note outlived its keystroke"
	assert console.command == line
	console.handle(ESC)
	assert console.command is None


# -- history stores the surrounding command ----------------------------------

def test_history_keeps_the_command_without_the_generated_prose(world):
	"""Ruled: recall opens a FRESH editor rather than carrying a
	potentially large or stale body. The authority still received the
	exact text that was submitted."""
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="the first body")
	line = f"close work={work} outcome=satisfying"
	submit(console, line)
	assert console.history == [line], console.history
	assert "the first body" not in " ".join(console.history)
	assert pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["rationale"] == "the first body"


def test_recalling_the_command_opens_a_fresh_editor(world):
	console = world["console"]
	first = make_work(world, "first")["work_id"]
	second = make_work(world, "second")["work_id"]
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="body one")
	submit(console, f"close work={first} outcome=satisfying")

	os.environ["EDITOR"] = fake_editor(world["tmp"], name="ed2",
	                                   writes="body two")
	console.handle(ord(":"))
	console.handle(curses.KEY_UP)
	recalled = f"close work={first} outcome=satisfying"
	assert console.command == recalled
	assert "body one" not in recalled, "the prose came back with the recall"
	# retarget the recalled draft and resubmit: a NEW editor, new prose
	for _ in range(len(recalled)):
		console.handle(curses.KEY_BACKSPACE)
	for character in f"close work={second} outcome=satisfying":
		console.handle(ord(character))
	console.handle(ENTER)

	assert pj.detail(world["store"], second, viewer_team="lang",
	                 viewer_member="ada")["rationale"] == "body two"


# -- the authority boundary ---------------------------------------------------

def test_opening_an_editor_mutates_nothing_until_submission(world):
	"""Only the final explicit submission writes. The editor round trip
	itself — template, launch, read-back — touches no authority byte."""
	console = world["console"]
	work = make_work(world)["work_id"]
	seen = str(world["tmp"] / "argv.json")
	watcher = world["tmp"] / "watcher.py"
	watcher.write_text(
		"import hashlib, sys\n"
		"blob = b''\n"
		"for suffix in ('', '-wal'):\n"
		"    try:\n"
		f"        blob += open({world['database']!r} + suffix, 'rb').read()\n"
		"    except FileNotFoundError:\n"
		"        pass\n"
		f"open({seen!r}, 'w').write(hashlib.sha256(blob).hexdigest())\n"
		"open(sys.argv[-1], 'a', encoding='utf-8').write('authored')\n",
		encoding="utf-8")
	os.environ["EDITOR"] = f"{sys.executable} {watcher}"
	before = digest(world)
	submit(console, f"close work={work} outcome=satisfying")
	# what the authority looked like WHILE the editor was open
	assert open(seen).read() == before, \
		"the authority changed before the command was submitted"
	assert digest(world) != before, "the submission did not commit"


def test_an_interrupt_during_the_read_back_is_also_a_safe_cancellation(
		world, monkeypatch):
	"""The review names the WAIT, and the correction covers the whole
	round trip.

	A SIGINT landing a moment after the editor exits — while the
	authored text is being read back — escapes by exactly the same
	route and tears the console down just as completely. Catching it
	only around `subprocess.run` would leave that window open, so this
	pins the wider boundary rather than the one case that was
	reported."""
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = fake_editor(world["tmp"], writes="authored")
	line = f"close work={work} outcome=satisfying"
	before = digest(world)
	paths = []
	real_open = open

	def interrupted(path, *args, **kwargs):
		if isinstance(path, str) and "baton-prose-" in path \
				and "w" not in "".join(str(a) for a in args):
			paths.append(path)
			raise KeyboardInterrupt
		return real_open(path, *args, **kwargs)

	monkeypatch.setattr("builtins.open", interrupted)
	submit(console, line)
	monkeypatch.undo()

	_assert_draft_kept(console, line, "interrupted")
	assert digest(world) == before, \
		"an interrupted read-back reached the authority"
	assert paths and not os.path.exists(paths[0]), \
		"the interrupted round trip left its private draft behind"


def test_the_draft_descriptor_is_closed_on_every_path(world, monkeypatch):
	"""`mkstemp` hands back a raw descriptor, and the correction moved
	`fchmod` inside the `with` that owns it — so a failure between the
	two can no longer leak one. Asserted by counting the process's own
	open descriptors across a refused round trip."""
	console = world["console"]
	work = make_work(world)["work_id"]
	os.environ["EDITOR"] = str(world["tmp"] / "no-such-editor")
	line = f"close work={work} outcome=satisfying"
	before = len(os.listdir("/proc/self/fd"))
	for _ in range(5):
		submit(console, line)
		console.handle(ESC)
	assert len(os.listdir("/proc/self/fd")) <= before + 1, \
		"the editor round trip leaked a descriptor"
