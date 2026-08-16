"""W19: the `::` multiline command batch — staging, preflight, per-slot
operation identity, sequential stop, honest per-line state.

The pinned boundary (finding-tui-command-batch): `::` on the empty bar
opens a batch buffer; Enter is only ever a newline and Ctrl-G is Go, so a
pasted newline can never execute. Go preflights EVERY pending line through
the fixed-global guard and THE shared parser before any authority access —
one static refusal and nothing runs. Execution is sequential in written
order through the same public CLI entry as the one-line bar, stopping at
the first refusal: earlier lines completed (never rolled back), the rest
unrun. Mutating lines without an explicit op-id= carry a generated
per-slot identity, retained across unedited retries (WS-5 replays instead
of duplicating) and discarded on edit; completed lines are skipped by
later Gos.
"""

from __future__ import annotations

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

from baton_work.authority import Authority                    # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402

CREATE = ("create team=lang kind=bug title={title} "
          "origin=external-report classification=suspected-defect "
          "body={body}")


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = Authority(database)
	yield store, config, database
	store.close()


def console_for(world):
	store, config, _database = world
	return Console(store, "lang", "ada", config_path=config)


def type_line(console, text):
	for char in text:
		console.handle(ord(char))


def rows_of(store):
	return pj.tree(store, viewer_team="lang", viewer_member="ada")["rows"]


def db_digest(store, database):
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(database, "rb") as handle:
		return hashlib.sha256(handle.read()).hexdigest()


# -- entry and staging -------------------------------------------------------

def test_double_colon_opens_the_batch_and_the_bar_stays_itself(world):
	"""`::` converts only the EMPTY bar; a colon after typed text stays
	literal one-line input."""
	console = console_for(world)
	console.handle(ord(":"))
	assert console.command == "" and console.batch is None
	console.handle(ord(":"))
	assert console.command is None and console.batch is not None
	assert [entry["text"] for entry in console.batch] == [""]
	console.handle(27)  # empty buffer: closes without confirmation
	assert console.batch is None
	console.handle(ord(":"))
	console.handle(ord("x"))
	console.handle(ord(":"))
	assert console.batch is None and console.command == "x:"


def test_staging_is_pure_view_state(world):
	"""Typing and newlines (a paste is exactly this stream) stage
	without executing: no authority byte changes, no Work appears."""
	store, _config, database = world
	console = console_for(world)
	before = db_digest(store, database)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="staged", body="b"))
	console.handle(13)
	type_line(console, CREATE.format(title="staged2", body="b"))
	assert len(console.batch) == 2
	assert rows_of(store) == []
	assert db_digest(store, database) == before, \
		"staging alone touched the authority"


def test_enter_is_a_newline_never_go(world):
	"""Every Enter spelling inserts a line; nothing executes."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="t", body="b"))
	for enter in (10, 13):
		console.handle(enter)
	assert len(console.batch) == 3
	assert rows_of(store) == []


# -- preflight ---------------------------------------------------------------

def test_one_syntax_error_and_nothing_executes(world):
	"""Go with any statically-invalid line refuses the WHOLE batch: the
	invalid line is failed with the public refusal, the valid mutating
	line stays staged and unexecuted, and the buffer remains editable."""
	store, _config, database = world
	console = console_for(world)
	before = db_digest(store, database)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="good", body="b"))
	console.handle(13)
	type_line(console, "close work=X outcome=bogus rationale=r")
	console.handle(7)
	good, bad = console.batch
	assert bad["state"] == "failed" and "takes one of" in bad["note"]
	assert good["state"] is None, "a valid line changed state"
	assert rows_of(store) == [], "something executed despite preflight"
	assert db_digest(store, database) == before
	assert console.batch_status.startswith("nothing ran — ")


def test_preflight_guards_fixed_globals_and_nesting(world):
	"""The session-fixed --config/--participant guard and the tui verb
	refuse per line, statically, before anything runs."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, "--participant lang.eve close work=X "
	                   "rationale=r outcome=rejected")
	console.handle(13)
	type_line(console, "tui")
	console.handle(13)
	type_line(console, CREATE.format(title="held", body="b"))
	console.handle(7)
	guard, nested, held = console.batch
	assert guard["state"] == "failed" and \
		"session's fixed global" in guard["note"]
	assert nested["state"] == "failed" and \
		nested["note"] == "already here"
	assert held["state"] is None
	assert rows_of(store) == []


# -- execution: sequential stop, honest state --------------------------------

def test_sequential_stop_with_completed_failed_unrun(world):
	"""The first authority refusal stops the batch: the earlier line is
	completed and committed (never rolled back), the stopping line is
	failed with the public refusal, the rest are unrun."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="first", body="b"))
	console.handle(13)
	type_line(console, "close work=NOPE rationale=r outcome=rejected")
	console.handle(13)
	type_line(console, CREATE.format(title="never", body="b"))
	console.handle(7)
	first, failing, never = console.batch
	assert first["state"] == "completed" and \
		first["note"].startswith("ok work_id=")
	assert failing["state"] == "failed" and "NOPE" in failing["note"]
	assert never["state"] == "unrun"
	titles = [row["title"] for row in rows_of(store)]
	assert titles == ["first"], \
		"the committed prefix is not exactly the completed lines"
	assert "1 completed; stopped:" in console.batch_status


def test_quoted_values_execute_verbatim(world):
	"""Shell quoting and embedded `=` reach the authority exactly as
	the one-line bar would deliver them."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, 'create team=lang kind=bug '
	                   'title="spaced = title" origin=external-report '
	                   'classification=suspected-defect '
	                   'body="two words"')
	console.handle(7)
	assert console.batch[0]["state"] == "completed"
	assert [row["title"] for row in rows_of(store)] == ["spaced = title"]


# -- identity and retry ------------------------------------------------------

def test_per_slot_identity_retained_and_reset_on_edit(world):
	"""A mutating line gets ONE generated identity per slot, keeps it
	across an unedited retry, and loses it on any edit (an edited line
	is a new command under WS-5's typed-input fingerprint)."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="kept", body="b"))
	console.handle(13)
	type_line(console, "close work=NOPE rationale=r outcome=rejected")
	console.handle(7)
	completed_op = console.batch[0]["op_id"]
	failed_op = console.batch[1]["op_id"]
	assert completed_op and failed_op and completed_op != failed_op
	console.handle(7)  # unedited re-Go: same identity, completed skipped
	assert console.batch[0]["op_id"] == completed_op
	assert console.batch[0]["state"] == "completed"
	assert console.batch[1]["op_id"] == failed_op
	assert len(rows_of(store)) == 1, "a completed line re-executed"
	console.batch_cursor = 1
	console.handle(8)  # edit the failed line
	assert console.batch[1]["op_id"] is None
	assert console.batch[1]["state"] is None


def test_identical_lines_are_two_commands(world):
	"""A batch is a list, never a set: two identical mutating lines get
	distinct identities and BOTH commit."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	line = CREATE.format(title="twin", body="b")
	type_line(console, line)
	console.handle(13)
	type_line(console, line)
	console.handle(7)
	first, second = console.batch
	assert first["op_id"] != second["op_id"]
	assert first["state"] == second["state"] == "completed"
	assert len([row for row in rows_of(store)
	            if row["title"] == "twin"]) == 2


def test_explicit_op_id_is_honored_and_replays(world):
	"""An explicit op-id= is never overwritten or doubled — and an
	exact cross-batch retry under it REPLAYS the committed result
	instead of duplicating the mutation (WS-5 through the batch)."""
	store, _config, _database = world
	console = console_for(world)
	line = CREATE.format(title="once", body="b") + " op-id=mine-1"
	for _round in range(2):
		console.handle(ord(":")); console.handle(ord(":"))
		type_line(console, line)
		console.handle(7)
		entry = console.batch[0]
		assert entry["state"] == "completed"
		assert entry["op_id"] is None, \
			"a generated identity shadowed the explicit op-id="
		console.handle(27)  # all completed: closes without confirm
		assert console.batch is None
	assert len([row for row in rows_of(store)
	            if row["title"] == "once"]) == 1, \
		"the exact retry duplicated the mutation"


# -- cancellation and retained buffer ----------------------------------------

def test_cancellation_confirms_over_unexecuted_text(world):
	"""Esc over unexecuted text asks one-row confirmation: n returns to
	the untouched buffer, y discards; a fully-completed batch closes
	directly, carrying its summary to the status row."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="pending", body="b"))
	console.handle(27)
	assert console.batch_confirm and console.batch is not None
	console.handle(ord("n"))
	assert not console.batch_confirm
	assert console.batch[0]["text"].startswith("create team=lang")
	console.handle(27)
	console.handle(ord("y"))
	assert console.batch is None
	assert rows_of(store) == [], "cancellation executed something"
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="done", body="b"))
	console.handle(7)
	assert console.batch[0]["state"] == "completed"
	console.handle(27)  # nothing left to lose: no confirmation
	assert console.batch is None
	assert console.status == "batch: 1 completed"


def test_failed_and_unrun_input_is_retained_for_editing(world):
	"""After a stop, the failed line is edited in place and a later Go
	runs ONLY the non-completed lines, in order."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="base", body="b"))
	console.handle(13)
	type_line(console, "close work=NOPE rationale=done "
	                   "outcome=satisfying")
	console.handle(7)
	assert [entry["state"] for entry in console.batch] == \
		["completed", "failed"]
	work_id = rows_of(store)[0]["id"]
	console.batch_cursor = 1
	entry = console.batch[1]
	while entry["text"]:
		console.handle(8)
	type_line(console, f"close work={work_id} rationale=done "
	                   f"outcome=satisfying")
	console.handle(7)
	assert [e["state"] for e in console.batch] == \
		["completed", "completed"]
	assert console.batch_status == "batch: 1 completed"
	assert rows_of(store)[0]["status"] == "closed"
	assert len(rows_of(store)) == 1, "the completed create re-executed"


# -- real terminal -----------------------------------------------------------

def test_pasted_batch_stages_without_executing(tmp_path):
	"""W19 (PTY): a multiline paste lands as staged lines under the
	visible legend; no execution, authority bytes identical; Esc asks
	before discarding."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	with open(database, "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	paste = (CREATE.format(title="p1", body="b") + "\r"
	         + CREATE.format(title="p2", body="b")).encode()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"::", 0.5), (paste, 0.7), (b"\x1b", 0.4), (b"y", 0.4),
		(b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	staged = ptyharness.replay(steps[1])
	assert any("title=p1" in line for line in staged), staged[-6:]
	assert any("title=p2" in line for line in staged)
	assert any("Ctrl-G go" in line for line in staged), \
		"the legend naming Go/cancel is not visible"
	confirm = ptyharness.replay(steps[2])
	assert any("Discard batch? y/N" in line for line in confirm)
	with open(database, "rb") as handle:
		after = hashlib.sha256(handle.read()).hexdigest()
	assert after == before, "a pasted newline executed something"


def test_batch_run_renders_honest_line_states(tmp_path):
	"""W19 (PTY): after a mid-batch refusal the pane distinguishes
	completed (ok), failed (!!), and unrun (--) lines, with the stop
	summary on the legend row."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	script = (CREATE.format(title="ok1", body="b") + "\r"
	          + "close work=NOPE rationale=r outcome=rejected\r"
	          + CREATE.format(title="held", body="b")).encode()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"::", 0.5), (script, 0.7), (b"\x07", 1.0), (b"\x1b", 0.4),
		(b"y", 0.4), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	ran = ptyharness.replay(steps[2])
	assert any(line.startswith("ok create") and "ok1" in line
	           for line in ran), ran[-8:]
	assert any(line.startswith("!! close work=NOPE")
	           for line in ran), ran[-8:]
	assert any(line.startswith("-- create") and "held" in line
	           for line in ran), ran[-8:]
	assert any("1 completed; stopped:" in line for line in ran)


def test_narrow_batch_line_keeps_the_caret_viewport(tmp_path):
	"""W19 (PTY): the cursor line inherits the W14 caret/viewport —
	over-width batch input scrolls behind a `<` marker with the caret
	visible; the buffer itself is never cut."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	line = CREATE.format(title="a-title-long-enough-to-overflow",
	                     body="still-typing").encode()
	assert len(line) > 40
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"::", 0.5), (line, 0.7), (b"\x1b", 0.4), (b"y", 0.4),
		(b"qy", 0.4)],
		columns=44, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	narrow, (row, col, visible) = ptyharness.replay(
		steps[1], columns=44, lines=24, cursor=True)
	bar = next(text_line for text_line in narrow if "<" in text_line)
	assert bar.endswith("body=still-typing"), bar
	assert visible, "no visible caret on the batch cursor line"
	assert col == 42, (row, col)


# -- round 2 -----------------------------------------------------------------

def test_buffer_mutation_invalidates_the_stale_summary(world):
	"""R1: any buffer mutation (text edit, line insert/delete) clears
	the previous run summary so the legend's controls return; mere
	cursor movement keeps a still-applicable summary."""
	store, _config, _database = world
	console = console_for(world)
	console.handle(ord(":")); console.handle(ord(":"))
	type_line(console, CREATE.format(title="base", body="b"))
	console.handle(13)
	type_line(console, "close work=NOPE rationale=r outcome=rejected")
	console.handle(7)
	assert "stopped:" in console.batch_status
	# cursor-only movement: the summary still applies
	import curses as _curses
	console.handle(_curses.KEY_UP)
	console.handle(_curses.KEY_DOWN)
	assert "stopped:" in console.batch_status
	# failed-line correction: the first backspace invalidates it
	console.handle(8)
	assert console.batch_status == "", \
		"a stale refusal survived the correction"
	# run to completion, then edit the COMPLETED line: summary clears
	entry = console.batch[1]
	while entry["text"]:
		console.handle(8)
	work_id = rows_of(store)[0]["id"]
	type_line(console, f"close work={work_id} rationale=done "
	                   f"outcome=satisfying")
	console.handle(7)
	assert console.batch_status == "batch: 1 completed"
	console.batch_cursor = 0
	console.handle(ord("x"))
	assert console.batch_status == "", \
		"a stale completion survived editing a completed line"
	assert console.batch[0]["state"] is None
	# line insertion and line deletion invalidate too
	console.handle(7)  # leaves a fresh summary (preflight refusal)
	assert console.batch_status != ""
	console.handle(13)
	assert console.batch_status == ""
	console.handle(7)
	assert console.batch_status != ""
	console.handle(8)  # empty cursor line: deletes the line
	assert console.batch_status == ""


def test_editing_restores_the_visible_legend(tmp_path):
	"""R1 (PTY): after a stop the legend row carries the refusal; the
	first correcting keystroke restores the Ctrl-G/Esc legend on
	screen."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	script = "close work=NOPE rationale=r outcome=rejected".encode()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"::", 0.5), (script, 0.6), (b"\x07", 0.8), (b"\x7f", 0.5),
		(b"\x1b", 0.4), (b"y", 0.4), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	stopped = ptyharness.replay(steps[2])
	assert any("stopped:" in line for line in stopped), stopped[-4:]
	corrected = ptyharness.replay(steps[3])
	assert any("Ctrl-G go" in line for line in corrected), \
		"the controls did not return after the correcting keystroke"
	assert not any("stopped:" in line for line in corrected), \
		"the stale refusal is still on screen"


def test_batch_viewport_survives_a_wider_resize(tmp_path):
	"""R2 (PTY): the over-width batch line clipped behind `<` at 44
	columns reappears WHOLE after a resize to 110 — same preserved
	buffer, caret still visible at the insertion point."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, _database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	line = (b"create team=lang kind=bug title=past-narrow "
	        b"origin=external-report classification=suspected-defect "
	        b"body=t")
	# overflows the 44-column pane (40 free cells) but fits the 110-
	# column one (106), so the resize must show it whole again
	assert 40 < len(line) < 106, len(line)
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"::", 0.6), (line, 0.8), ("resize", (110, 32), 1.0),
		(b"\x1b", 0.4), (b"y", 0.4), (b"qy", 0.4)],
		columns=44, lines=24, dynamic_size=True, settle=1.2)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	narrow, (_row, col, visible) = ptyharness.replay(
		steps[1], columns=44, lines=24, cursor=True)
	assert any(text_line.lstrip().startswith("<")
	           for text_line in narrow), narrow[-6:]
	assert visible and col == 42, (col, visible)
	wide, (wrow, wcol, wvisible) = ptyharness.replay(
		steps[2], columns=110, lines=32, cursor=True)
	decoded = line.decode()
	bar = next((text_line for text_line in wide
	            if decoded in text_line), None)
	assert bar is not None, \
		f"the buffer did not reappear whole: {wide[-8:]}"
	assert "<" not in bar, bar
	assert wvisible, "the caret vanished across the resize"
	assert wcol == bar.index(decoded) + len(decoded), (wcol, bar)
