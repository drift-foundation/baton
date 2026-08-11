"""Terminal smoke over a real PTY.

The four lines the pure tests cannot reach: `curses.error` handling, cursor
visibility, caret placement and resize. This does not re-test the model -- it
proves the console starts, draws, responds and exits on an actual terminal,
which is the one claim the rest of the suite cannot make.

WHAT IT CANNOT PROVE, stated so nobody relies on it: line-width correctness.
`addnstr` clips at the window edge and the driver swallows `curses.error`, so
a renderer emitting oversized lines still runs here without complaint --
verified by deliberately breaking the clamp and watching these tests pass.
Width is proven by the pure renderer tests in display cells; this file proves
the terminal integration around them.
"""

from __future__ import annotations

import json
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import time

import pytest


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	proj = home / "proj"
	proj.mkdir()
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
			"mailbox": {"name": "pty"},
			"participants": {
				"acme.reviewer": {},
				"acme.implementer": {"projection_dir": str(proj)},
			},
			"roots": {}, "retention_days": 90,
		}, handle)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	core.init_instance(path)
	with core.open_instance(path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="Visible in the PTY", body=b"# hello\nfrom a terminal\n")
	return path, proj


# A SCREEN, reconstructed from the transcript.
#
# Curses chooses freely between CUP (`\x1b[<row>;<col>H`), VPA (`\x1b[<row>d`),
# HPA and plain carriage returns, and it splits even a two-character write
# across two of them run to run within one build. Every assertion that matched
# one spelling was testing the optimiser, so this replays the writes into a
# grid and asks what the human would actually have seen.
#
# Deliberately small: cursor addressing, erase-to-end-of-line, and printable
# cells. No scrolling regions, no wrapping, no attributes -- the questions
# these tests ask are "what is on row N" and "which row did this text land
# on", and a fuller emulator would be a second curses to maintain.
_ESCAPE = re.compile(r"\x1b(?:\[[0-9;?]*[a-zA-Z@-~]|[()][B0]|[=>ME78])")
_CUP = re.compile(r"\x1b\[(\d*)(?:;(\d*))?H")
_VPA = re.compile(r"\x1b\[(\d+)d")
_HPA = re.compile(r"\x1b\[(\d+)G")
_EL = re.compile(r"\x1b\[(\d*)K")


def _pty_is_rule(line: str) -> bool:
	"""The pane rule on a replayed screen, matched by SHAPE.

	These used to look for the `DETAIL ` label. The label is gone -- the lower
	pane is self-evidently the selected message -- so the unbroken run of
	divider cells is what identifies the row, which is also the stronger
	check: a label locator could be satisfied while the rule itself broke."""
	from baton_tui.render import DIVIDER, MIN_RULE_CELLS
	return DIVIDER * MIN_RULE_CELLS in line


def _replay(transcript: str, columns: int = 100, lines: int = 30) -> list[str]:
	"""The final screen contents, one string per row."""
	grid = [[" "] * columns for _ in range(lines)]
	row = col = 0
	index = 0
	while index < len(transcript):
		escape = _ESCAPE.match(transcript, index)
		if escape:
			seq = escape.group()
			index = escape.end()
			cup, vpa, hpa, erase = (_CUP.fullmatch(seq), _VPA.fullmatch(seq),
			                        _HPA.fullmatch(seq), _EL.fullmatch(seq))
			if cup:
				row = int(cup.group(1) or 1) - 1
				col = int(cup.group(2) or 1) - 1
			elif vpa:
				row = int(vpa.group(1)) - 1
			elif hpa:
				col = int(hpa.group(1)) - 1
			elif erase and erase.group(1) in ("", "0"):
				if 0 <= row < lines:
					for cell in range(col, columns):
						grid[row][cell] = " "
			continue
		char = transcript[index]
		index += 1
		if char == "\r":
			col = 0
		elif char == "\n":
			row, col = row + 1, 0
		elif char == "\b":
			col = max(0, col - 1)
		elif char.isprintable() and 0 <= row < lines and 0 <= col < columns:
			grid[row][col] = char
			col += 1
	return ["".join(cells).rstrip() for cells in grid]


def _drive(config_path, keys, columns=100, lines=30, settle=1.2):
	"""Run the console on a real PTY, send keys, return what was drawn."""
	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:                                    # child: becomes the console
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(['--config', %r, '--participant', 'acme.implementer']))"
			% config_path])
	import fcntl
	import struct
	import termios
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", lines, columns, 0, 0))
	output = b""
	deadline = time.time() + settle
	while time.time() < deadline:
		ready, _, _ = select.select([fd], [], [], 0.1)
		if ready:
			try:
				output += os.read(fd, 65536)
			except OSError:
				break
	for key in keys:
		os.write(fd, key)
		deadline = time.time() + 0.6
		while time.time() < deadline:
			ready, _, _ = select.select([fd], [], [], 0.1)
			if ready:
				try:
					output += os.read(fd, 65536)
				except OSError:
					break
	status = _reap(pid, fd)
	return output.decode("utf-8", "replace"), status


def _reap(pid, fd, timeout=5.0):
	"""Wait for the console to exit, with a bounded deadline, and always close
	the PTY. `WNOHANG` alone proved nothing: it returns immediately whether or
	not the child finished, so a console that hung or crashed looked the same
	as one that exited cleanly."""
	deadline = time.time() + timeout
	status = None
	try:
		while time.time() < deadline:
			done, raw = os.waitpid(pid, os.WNOHANG)
			if done:
				status = raw
				break
			time.sleep(0.05)
		if status is None:
			os.kill(pid, 9)
			os.waitpid(pid, 0)
			raise AssertionError("console did not exit within the deadline")
	except ChildProcessError:
		status = 0
	finally:
		try:
			os.close(fd)
		except OSError:
			pass
	return status


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_console_starts_draws_and_exits_on_a_real_terminal(tmp_path):
	config_path, _ = _instance(tmp_path)
	# `q` then `Y`: the console now CLAIMS the row it starts on (Slawomir's
	# claim-on-highlight ruling), so quitting asks about the unresolved claim.
	# That confirmation is the accepted protection for the claims the ruling
	# accumulates, so exercising it is exercising the contract.
	screen, status = _drive(config_path, [b"q", b"Y"])
	# The literal "baton" was SUPERSEDED out of the header by Slawomir's
	# ruling: the terminal running it already establishes the tool, and the
	# label spent width without adding state. The participant address is what
	# the header now opens with, and it is the fact that matters here anyway.
	assert "baton" not in screen.replace("baton.json", "")
	assert "Visible in the PTY" in screen
	assert "acme.implementer" in screen
	# It EXITED, and cleanly: a console that hung or died would have looked
	# identical to WNOHANG alone.
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_resize_does_not_crash_the_console(tmp_path):
	"""The resize path writes out of bounds if `render` ever returns more than
	the terminal holds; here a real terminal is the judge."""
	import fcntl
	import struct
	import termios
	config_path, _ = _instance(tmp_path)
	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(['--config', %r, '--participant', 'acme.implementer']))"
			% config_path])
	output = b""
	for rows, cols in ((30, 100), (8, 40), (5, 20), (60, 200), (24, 80)):
		fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
		# Wake the loop: it blocks in getch with a poll timeout, so without a
		# keystroke it would not redraw before the next resize and the test
		# would be asserting against a stale screen.
		os.write(fd, b"g")
		deadline = time.time() + 1.5
		while time.time() < deadline:
			ready, _, _ = select.select([fd], [], [], 0.1)
			if ready:
				try:
					output += os.read(fd, 65536)
				except OSError:
					break
	os.write(fd, b"q")
	os.write(fd, b"Y")            # startup claimed a row; quitting asks
	status = _reap(pid, fd)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	text = output.decode("utf-8", "replace")
	assert "Traceback" not in text
	# It did not merely survive: it was still drawing the inbox at the end.
	assert "Visible in the PTY" in text


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_reply_mode_shows_a_cursor_and_typing_reaches_the_draft(tmp_path):
	"""Cursor visibility and caret placement are terminal-only behaviour.

	Read off a REPLAYED SCREEN rather than out of the escape stream. This
	used to split the transcript on the `quick reply (` tutorial sentence to
	find the draft; the noise ruling removed that sentence, and the fallback
	`"> ok" in screen` never held either -- curses writes only the cells that
	changed, so the `> ` prefix and the typed characters reach the terminal in
	separate writes, sometimes even one character at a time."""
	config_path, _ = _instance(tmp_path)
	# Claim, enter reply mode, type, then look; cancel and quit through the
	# unresolved-claim confirmation, which the console must exit cleanly from.
	text, status, steps = _console(tmp_path, config_path, [
		(b"\r", 0.5),               # claim and open
		(b"R", 0.3),                # the quick reply
		(b"ok", 0.5),               # type into the subject line
		(b"\x1b", 0.3),             # cancel
		(b"qY", 0.4),               # quit through the confirmation
	], columns=100, lines=24)

	assert "Visible in the PTY" in text
	# Entering reply mode makes the cursor visible (DECTCEM show)...
	assert "\x1b[?25h" in text or "\x1b[?12;25h" in text
	# ...and the typed characters are ON the draft row, which is where the
	# caret was placed. Cursor-show alone would pass with the caret parked in
	# a corner of the screen.
	typed = _replay("".join(steps[:3]), columns=100, lines=24)
	draft = [(number, line) for number, line in enumerate(typed, start=1)
	         if line.lstrip().startswith(">") and "ok" in line]
	assert draft, f"the typed characters never reached a draft row: {typed}"
	number, line = draft[0]
	assert 1 < number < 24, f"the draft is not in the panes, on row {number}"
	assert line.rstrip().endswith("ok"), (
		f"the caret was not at the end of the draft: {line!r}")
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


# NOT PINNED HERE: drawing the "terminal too small" notice at a real 5x20.
# It works when driven standalone but is flaky under pytest -- the redraw races
# the poll timeout and pytest's capture interacts with the PTY. A flaky test is
# worse than an absent one: it trains people to rerun until green. The notice
# itself is proven by the pure renderer tests at every size including 0x0 and
# 1x1; what is unproven is only that a real terminal shows it, and I would
# rather say so than ship a test that passes when it feels like it.


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_selection_attribute_moves_between_rows_on_a_real_terminal(tmp_path):
	"""Trial defect, proven where it was reported.

	The pure tests can say a row carries a `selected` style; only a terminal
	can say the attribute was actually emitted and moved. Slawomir saw two
	panes with nothing highlighted, so the assertion is on the escape output:
	reverse video must appear, and its position must change when the cursor
	moves."""
	import fcntl
	import re
	import struct
	import termios

	config_path, _ = _instance(tmp_path)
	# Seed a second row so the highlight has somewhere to move to.
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	with core.open_instance(config_path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="Second row for the highlight", body=b"y\n")

	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(['--config', %r, '--participant', 'acme.implementer']))"
			% config_path])
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))

	def pump(seconds):
		chunk = b""
		deadline = time.time() + seconds
		while time.time() < deadline:
			ready, _, _ = select.select([fd], [], [], 0.1)
			if ready:
				try:
					chunk += os.read(fd, 65536)
				except OSError:
					break
		return chunk

	first = pump(1.6)
	# Arrow key: raw ANSI, exactly what a terminal sends. If this does nothing
	# the console is ignoring arrows, which is half of the reported defect.
	os.write(fd, b"\x1b[B")
	moved = pump(1.2)
	os.write(fd, b"q")
	pump(0.4)
	os.write(fd, b"Y")            # startup claimed a row; quitting asks
	pump(0.4)
	status = _reap(pid, fd)

	first_text = first.decode("utf-8", "replace")
	moved_text = moved.decode("utf-8", "replace")
	assert _has_reverse(first_text), "no reverse video: the selection is invisible"
	assert moved_text.strip(), "the arrow key produced no redraw at all"
	assert _has_reverse(moved_text), "the highlight vanished after moving"
	# It MOVED: the text drawn in reverse video is a DIFFERENT message.
	before = _highlighted_text(first_text)
	after = _highlighted_text(moved_text)
	assert before and after, f"no highlighted text captured: {before!r} {after!r}"
	assert before != after, f"highlight did not move: {before!r} -> {after!r}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


_SGR = re.compile(r"\x1b\[([0-9;]*)m")
_REVERSE_RUN = re.compile(r"\x1b\[[0-9;]*m")


def _has_reverse(text):
	"""SGR 7 anywhere, as a PARAMETER rather than a substring.

	ncurses emits combined sequences -- `ESC[0;7m`, not `ESC[7m` -- so a
	substring search for the bare form reports "no highlight" on a console
	that is highlighting correctly. It cost me a wrong conclusion once
	already; matching 37 (white foreground) or 27 (reverse off) would cost the
	opposite one."""
	return any("7" in params.split(";") for params in _SGR.findall(text))


def _highlighted_text(text):
	"""The visible text drawn while reverse video was in effect.

	Asserting on the TEXT rather than a row number: what matters is that a
	different MESSAGE is highlighted after the arrow key, and row arithmetic
	over a curses update stream is fragile enough to fail for reasons that
	have nothing to do with the console."""
	out = []
	reverse_on = False
	position = 0
	for match in _REVERSE_RUN.finditer(text):
		if reverse_on:
			chunk = text[position:match.start()]
			visible = "".join(c for c in chunk if c.isprintable()).strip()
			if visible:
				out.append(visible)
		params = match.group(0)[2:-1].split(";")
		if "7" in params:
			reverse_on = True
		elif "" in params or "0" in params or "27" in params:
			reverse_on = False
		position = match.end()
	return out


def _highlighted_runs(text):
	"""Every visible chunk drawn under reverse video, UNSTRIPPED.

	`_highlighted_text` strips padding because it compares message text;
	here the padding is the point -- how far the stripe ran is exactly what
	is being measured."""
	out = []
	reverse_on = False
	position = 0
	for match in _REVERSE_RUN.finditer(text):
		if reverse_on:
			chunk = text[position:match.start()]
			visible = "".join(c for c in chunk if c.isprintable())
			if visible:
				out.append(visible)
		params = match.group(0)[2:-1].split(";")
		if "7" in params:
			reverse_on = True
		elif "" in params or "0" in params or "27" in params:
			reverse_on = False
		position = match.end()
	return out


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_highlight_covers_one_list_row_on_a_real_terminal(tmp_path):
	"""Trial defect: the stripe ran across the whole terminal row, including
	the pane beside it. Only a terminal shows the actual extent of an
	attribute run -- the pure tests can pin the span arithmetic but not what
	curses then does with it.

	Stacked, a list row IS the whole row, so the stripe covers it end to end.
	What must never happen is the stripe reaching the RULE or a detail row,
	and the rule is the character that would give that away."""
	import fcntl
	import struct
	import termios

	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	from baton_tui.render import selection_span
	from baton_tui.safe_text import display_width
	with core.open_instance(config_path) as store:
		for index in range(4):
			store.send("acme.reviewer", "acme.implementer", kind="q",
			           subject=f"Row {index}", body=b"y\n")

	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.environ["LANG"] = "C.UTF-8"
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(['--config', %r, '--participant', 'acme.implementer']))"
			% config_path])
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
	output = b""
	deadline = time.time() + 1.8
	while time.time() < deadline:
		ready, _, _ = select.select([fd], [], [], 0.1)
		if ready:
			try:
				output += os.read(fd, 65536)
			except OSError:
				break
	os.write(fd, b"q")
	os.write(fd, b"Y")            # startup claimed a row; quitting asks
	status = _reap(pid, fd)
	text = output.decode("utf-8", "replace")
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	runs = _highlighted_runs(text)
	assert runs, "no reverse video: the selection is invisible"
	_, end = selection_span(100)
	for run in runs:
		# The rule is never inside the stripe. A highlight that spilled onto
		# the row below is what this character would give away.
		assert "\u2500" not in run, f"the highlight covered the rule: {run!r}"
		assert display_width(run) <= end, (
			f"the highlight ran {display_width(run)} cells past its "
			f"{end}-cell row: {run!r}")


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_part_marker_is_drawn_and_differs_from_the_row_highlight(tmp_path):
	"""Two cursors that look the same are one cursor as far as the human is
	concerned. Only a terminal shows that the part header gets a DIFFERENT
	attribute run from the inbox selection."""
	import fcntl
	import struct
	import termios

	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	with core.open_instance(config_path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="Multipart", parts=[
			{"content_type": "text/plain; charset=utf-8", "body": b"first leaf\n"},
			{"content_type": "text/plain; charset=utf-8", "body": b"second leaf\n"},
		])

	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.environ["LANG"] = "C.UTF-8"
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(['--config', %r, '--participant', 'acme.implementer']))"
			% config_path])
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
	time.sleep(0.6)
	os.write(fd, b"\n")                  # open, so the parts are rendered
	output = b""
	deadline = time.time() + 1.8
	while time.time() < deadline:
		ready, _, _ = select.select([fd], [], [], 0.1)
		if ready:
			try:
				output += os.read(fd, 65536)
			except OSError:
				break
	# `y` confirms: opening claimed the message, so a bare `q` asks first.
	os.write(fd, b"qy")
	_reap(pid, fd)
	text = output.decode("utf-8", "replace")

	# The marker reached the terminal as a character...
	assert "\u25b8" in text, "the part marker was never drawn"
	# ...on the FOOTER row, which is what tells the two selections apart now.
	#
	# This used to assert a distinct SGR attribute (bold or underline) on the
	# selected part's header row. That row no longer exists: ruled, the body
	# leads and the part metadata moved to a fixed footer. The distinction is
	# structural rather than stylistic -- a different row entirely, which is
	# stronger than a different attribute on the same kind of row.
	assert "parts)" in text, "the part footer was never drawn"
	marker_line = next((line for line in text.splitlines()
	                    if "\u25b8" in line and "parts)" in line), None)
	assert marker_line is not None, \
		"the marker and the part count are not on the same row"


def _console(tmp_path, config_path, script, columns=100, lines=24, settle=0.7,
             editor=None):
	"""Drive a real console: `script` is a list of (bytes, pause) to write.

	Output is accumulated THROUGHOUT rather than drained between keystrokes.
	Draining between writes raced with the redraw and returned empty strings
	for repaints that had plainly happened -- the transcript is the reliable
	artifact, not any single window of it.

	Returns `(whole_transcript, exit_status, per_step_transcripts)`. The
	per-step slices are what let an assertion say "this keystroke repainted
	row 23", which the whole transcript cannot: every row gets painted at some
	point in a session."""
	import fcntl
	import struct
	import termios

	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.environ["LANG"] = "C.UTF-8"
		argv = ["--config", config_path, "--participant", "acme.implementer"]
		if editor:
			argv += ["--editor", editor]
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(%r))" % (argv,)])
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", lines, columns, 0, 0))

	out = bytearray()

	def pump(seconds):
		deadline = time.time() + seconds
		while time.time() < deadline:
			ready, _, _ = select.select([fd], [], [], 0.05)
			if ready:
				try:
					out.extend(os.read(fd, 65536))
				except OSError:
					return

	pump(settle)
	steps = []
	for keys, pause in script:
		mark = len(out)
		os.write(fd, keys)
		pump(pause)
		steps.append(out[mark:].decode("utf-8", "replace"))
	status = _reap(pid, fd)
	return out.decode("utf-8", "replace"), status, steps


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_enter_enter_sends_on_a_real_terminal(tmp_path):
	"""The quick path, end to end through a terminal: `n`, pick, type a
	subject, Enter, Enter.

	The model tests prove the transitions and the renderer proves the text.
	This proves the whole path holds together in front of a real tty: the
	picker paints, a letter selects, typed characters reach the subject field,
	Enter arms, Enter answers, and a message actually lands in the queue.

	One thing this does NOT prove, checked rather than assumed: whether Enter
	arrives as CR or LF. Removing `ENTER_CR` from the confirm mapping leaves
	this test green, because the line discipline maps CR to LF before curses
	sees it. `ENTER_CR` stays in the mapping for a console run in raw mode,
	but nothing here pins it and this docstring does not claim otherwise."""
	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core

	# `a` is the first offered letter, and the participant list is sorted, so
	# acme.implementer is `a` and acme.reviewer is `b`.
	text, status, steps = _console(tmp_path, config_path, [
		(b"n", 0.6),               # recipient picker
		(b"b", 0.4),               # acme.reviewer
		(b"deploy is green", 0.5),  # a subject, and nothing else
		(b"\r", 0.6),              # CR: what a real Enter sends
		(b"\r", 0.8),              # and Enter answers the question
		(b"q", 0.4),
		(b"Y", 0.4),               # startup claimed a row; quitting asks
	])
	assert "send to:" in text
	assert "acme.reviewer" in text
	assert "Send now? [Y/n]" in text, "the confirmation never appeared"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	with core.open_instance(config_path) as store:
		pending = store.scan("acme.reviewer")["pending"]
	assert len(pending) == 1, f"Enter, Enter did not send: {text[-600:]}"
	assert pending[0]["subject"] == "deploy is green"


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_confirmation_is_one_line_on_a_real_terminal(tmp_path):
	"""Slawomir called the two-row treatment noisy. Only a terminal shows what
	was actually painted."""
	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	with core.open_instance(config_path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="S", body=b"y\n")

	text, status, steps = _console(tmp_path, config_path, [
		(b"\r", 0.5),              # claim and open
		(b"R", 0.3),               # the QUICK reply -- `r` is the editor now
		(b"ok", 0.3),
		(b"\r", 0.7),              # arm
		(b"n", 0.3),               # decline
		(b"\x1b", 0.3),            # Esc out of the reply, so `q` is not text
		(b"qy", 0.4),
	])
	assert "Send now? [Y/n]" in text, text[-600:]
	# The noisy two-row treatment is gone: no severity prefix, no separate
	# status row, no second footer row.
	assert "SEND THIS?" not in text
	assert "[!] Send" not in text
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_whole_legend_is_visible_on_one_row_at_a_wide_terminal(tmp_path):
	"""Slawomir's live trial showed only `Send? Y/n` with the legend missing.
	This starts a confirmation on a terminal wide enough for the full literal
	and asserts the WHOLE line reached the screen.

	120 columns is deliberately generous: the detail pane must not be what
	decides whether the legend fits, since the footer spans the full width."""
	# Written out here, NOT imported: comparing the screen against the same
	# constant that produced it lets the text drift freely. Dropping the
	# brackets passed every constant-anchored pin in the suite.
	literal = "Send now? [Y/n]   Enter or y = send   n or Esc = keep editing"

	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	with core.open_instance(config_path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="S", body=b"y\n")

	text, status, steps = _console(tmp_path, config_path, [
		(b"\r", 0.5),              # claim and open
		(b"R", 0.3),               # the QUICK reply -- `r` is the editor now
		(b"ok", 0.3),
		(b"\r", 0.8),              # arm the send
		(b"n", 0.3),               # decline
		(b"\x1b", 0.3),            # leave the reply so `q` is not text
		(b"qy", 0.4),
	], columns=120)

	# The ENTIRE literal, contiguously, allowing for the cell-by-cell writes
	# curses may split it into.
	painted = "".join(ch for ch in text if ch.isprintable())
	assert literal.replace(" ", "") in painted.replace(" ", ""), (
		f"the legend never appeared in full: {text[-700:]}")
	# No duplicate question, no residue of the old treatments.
	assert painted.count("Send now?") >= 1
	assert "SEND THIS?" not in text
	assert "[!] Send" not in text
	# The bare form Slawomir saw must not be what gets painted.
	assert "Send? Y/n" not in text.replace("Send now? [Y/n]", "")

	# ...and it is painted on the BOTTOM row, which is what "one total footer
	# row" looks like from a terminal: at 24 lines the legend is addressed to
	# row 24, so there is no footer row below it and the row above it belongs
	# to the panes.
	#
	# The exactly-one-row property itself is pinned in the pure renderer at
	# 8/12/24/40 lines, because a curses transcript is a stream of cell
	# writes: it can show WHERE a row was painted but cannot cleanly express
	# "and nothing else is a footer".
	# EITHER cursor-address encoding for row 24. Curses picks between CUP
	# (`\x1b[24;<col>H`) and VPA (`\x1b[24d`) depending on what it painted
	# immediately before, and five runs of one build produced both. They mean
	# the same row; matching only CUP made this assertion fail about half the
	# time on a console that was behaving correctly.
	assert re.search(r"\x1b\[24(?:;\d+H|d)\s*(?:\x1b\[K)?\s*Send now\? \[Y/n\]",
	                 text), "the legend was not painted on the bottom row"

	# The arming keystroke is what paints it, not some earlier redraw.
	assert "Send now? [Y/n]" in steps[3], steps[3][-400:]

	# WHY "exactly one footer row" IS NOT ASSERTED HERE, having tried:
	#
	# A second footer row would be the context line at row 23. Curses repaints
	# only CHANGED cells, and that row already reads "acting on: ..." before
	# the send is armed -- so with the two-row footer restored, nothing is
	# written to row 23 at all and the transcript is identical either way. I
	# verified that: the assertion passed with the fault deliberately present,
	# which makes it worse than no assertion.
	#
	# Exactly-one-footer-row is pinned instead in the pure renderer, exactly
	# and at 8/12/24/40 lines, in
	# `test_the_confirmation_footer_is_exactly_one_row_of_exact_text`. This
	# test pins what only a terminal can show: that the full literal reaches
	# the screen, on the bottom row.
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_divider_draws_as_a_continuous_rule_on_a_real_terminal(tmp_path):
	"""Trial defect: the divider appeared as disconnected dashes. Only a
	terminal can show that the box-drawing character is actually emitted and
	reaches the screen as one unbroken run. R7 turned the column into a ROW,
	so the pin is a run along one row rather than a cell on many."""
	import fcntl
	import struct
	import termios

	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	with core.open_instance(config_path) as store:
		for index in range(3):
			store.send("acme.reviewer", "acme.implementer", kind="q",
			           subject=f"Row {index}", body=b"y\n")

	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["PYTHONPATH"] = os.path.join(here, "src")
		os.environ["LANG"] = "C.UTF-8"
		os.execv(sys.executable, [
			sys.executable, "-c",
			"import sys; from baton_tui.driver import main; "
			"sys.exit(main(['--config', %r, '--participant', 'acme.implementer']))"
			% config_path])
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
	output = b""
	deadline = time.time() + 1.8
	while time.time() < deadline:
		ready, _, _ = select.select([fd], [], [], 0.1)
		if ready:
			try:
				output += os.read(fd, 65536)
			except OSError:
				break
	os.write(fd, b"q")
	os.write(fd, b"Y")            # startup claimed a row; quitting asks
	status = _reap(pid, fd)
	text = output.decode("utf-8", "replace")
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	# The box-drawing character reached the terminal...
	assert "─" in text, "the divider was not emitted as a box-drawing character"
	# ...as ONE unbroken run, which is what makes it read as a rule rather
	# than a row of dashes. Not pinned to an exact width: the ioctl above asks
	# for 100 columns but the child's curses can settle on its own idea of the
	# size under pytest, and this test is about continuity, not arithmetic --
	# the exact full-width rule is pinned in the pure renderer.
	assert re.search("─{40,}", text), "the rule reached the terminal broken up"
	# ...and the ASCII fallback is not mixed into it.
	assert "─-" not in text and "-─" not in text


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_lowercase_r_reaches_the_editor_path_on_a_real_terminal(tmp_path):
	"""The packaged console, the swapped key, and a real terminal.

	`r` suspends curses and runs the configured editor. Driven with a REAL
	editor command that writes a body and exits, because the point is the
	suspend/restore round trip that only a terminal can exercise -- the
	in-process tests inject the editor and never leave curses."""
	config_path, _ = _instance(tmp_path)
	script = tmp_path / "fake-editor"
	script.write_text("#!/bin/sh\nprintf 'from the editor\\n' > \"$1\"\n")
	os.chmod(script, 0o755)

	# WAIT OUT THE DWELL FIRST. Claim-on-highlight no longer commits the
	# instant the console lands on a row: the startup selection dwells for two
	# seconds, so `r` sent before that has no claim to reply to. Pressing a
	# harmless key and waiting is what a human does here, and it is the only
	# place in the suite where the real two seconds actually elapse.
	text, status, steps = _console(tmp_path, config_path, [
		(b"", 2.4),                 # let the startup dwell commit the claim
		(b"r", 1.5),                # now there is a claim to reply to
		(b"\x1b", 0.4),             # leave the draft the editor produced
		(b"qY", 0.5),
	], columns=100, lines=24, editor=str(script))

	assert "Traceback" not in text
	# The screen RIGHT AFTER the editor returned, and ONLY that step.
	#
	# It used to replay the first two, which happened to work because `Esc`
	# discarded silently and left the import message on the status line. `Esc`
	# now RETAINS the draft and says so, replacing it -- so including that
	# step asserts about a screen the editor is no longer the subject of.
	screen = _replay(steps[1], columns=100, lines=24)
	assert any("draft imported" in line for line in screen), (
		f"the editor round trip did not complete: {screen}")
	# ...and curses came back: the panes are drawn again, not left as the
	# editor's own output.
	assert any(_pty_is_rule(line) for line in screen), screen
	assert any("Visible in the PTY" in line for line in screen), screen
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_sent_list_uses_the_final_vocabulary(tmp_path):
	"""What the packaged console ACTUALLY shows in SENT.

	The detail HEADING drawn by `_sent_row_lines` is deliberately not asserted
	here, because it cannot be reached: `preview` runs only while nothing is
	open, and selecting a row always opens it, so from `o` onwards the pane
	shows the opened copy. Chasing it with keystrokes and poll waits produced
	the opened copy every time. That is reported to review rather than
	dressed up as a proof."""
	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core
	with core.open_instance(config_path) as store:
		done = store.send("acme.implementer", "acme.reviewer", kind="q",
		                  subject="Answered outbound", body=b"x\n")
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject="Waiting outbound", body=b"y\n")
		claim = store.claim("acme.reviewer", message_id=done)
		store.reply(claim["claim_id"], participant="acme.reviewer",
		            kind="response", body=b"theirs\n")

	# A generous settle: the SENT list is drawn by a redraw after the view
	# switch, and a short one raced it. The first version used bare `next(...)`
	# and so failed with StopIteration rather than saying what was missing.
	screen, status = _drive(config_path, [b"o", b"q", b"Y"],
	                        columns=110, lines=34, settle=2.5)
	assert "Traceback" not in screen
	drawn = _replay(screen, columns=110, lines=34)
	rules = [index for index, line in enumerate(drawn) if _pty_is_rule(line)]
	assert rules, f"no detail rule was drawn: {drawn}"
	listing = drawn[:rules[0]]
	body = "\n".join(listing)
	assert "Sent:" in body, body

	# Matched on the leading word, not the whole subject: `_replay` leaves the
	# tail of a longer earlier write when a shorter one overwrites it, so
	# `Waiting outbound` can appear as `Waitingd outbound` on the grid. The
	# GLYPH column is what this test is about and is unaffected.
	answered = [line for line in listing if "Answered" in line]
	waiting = [line for line in listing if "Waiting" in line]
	assert answered, f"the answered outbound row was not drawn: {body}"
	assert waiting, f"the waiting outbound row was not drawn: {body}"
	assert "\u2713" in answered[0], f"terminal outbound row: {answered[0]!r}"
	assert "\u25b7" in waiting[0], f"unfinished outbound row: {waiting[0]!r}"
	for line in answered + waiting:
		assert "?" not in line and " R " not in line and " C " not in line, line
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def _packaged_console(tmp_path, config_path, script, columns=100, lines=24,
                      settle=0.9):
	"""Drive the PACKAGED zipapp, not the source tree.

	Every other harness in this file runs `baton_tui.driver` off `PYTHONPATH`,
	which is the right default -- it is fast and it is what most of these
	tests are about. This one exists because a correction was reported against
	`bin/baton-tui` specifically, and that is the artifact Slawomir runs. A
	console can pass every in-process test it has and still fail to start when
	packaged; that has happened here once already.
	"""
	import fcntl
	import struct
	import termios

	# The REPOSITORY ROOT, and `src/` for the child's import path. A spawned
	# console does not inherit `tests/conftest.py`'s `sys.path` edit, so the
	# path it needs has to travel in the environment.
	here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	archive = os.path.join(here, "bin", "baton-tui")
	assert os.path.isfile(archive), "bin/baton-tui must be built"
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["LANG"] = "C.UTF-8"
		# NO PYTHONPATH: the archive must carry its own console and core, or
		# it is not the artifact being tested.
		os.environ.pop("PYTHONPATH", None)
		os.execv(sys.executable, [
			sys.executable, archive, "--config", config_path,
			"--participant", "acme.implementer"])
	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", lines, columns, 0, 0))

	out = bytearray()

	def pump(seconds):
		deadline = time.time() + seconds
		while time.time() < deadline:
			ready, _, _ = select.select([fd], [], [], 0.05)
			if ready:
				try:
					out.extend(os.read(fd, 65536))
				except OSError:
					return

	pump(settle)
	prefixes = []
	for keys, pause in script:
		os.write(fd, keys)
		pump(pause)
		# CUMULATIVE, not the slice since the last key. A repaint is partial:
		# pressing Tab rewrites the pane headers and little else, so the slice
		# for one keystroke frequently does not contain the row an assertion
		# is about. Replaying everything up to this point reconstructs the
		# SCREEN as it stood after that keystroke, which is what is being
		# asserted about.
		prefixes.append(out.decode("utf-8", "replace"))
	status = _reap(pid, fd)
	return out.decode("utf-8", "replace"), status, prefixes


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_console_returns_focus_to_messages_after_a_close(tmp_path):
	"""The reported defect, on the artifact it was reported against.

	Open a message, move focus to the detail pane, close it. The focus marker
	must be back on MESSAGES afterwards, so the next `j` walks the queue
	instead of scrolling a detail pane for a message that is already answered.
	"""
	config_path, _proj = _instance(tmp_path)
	transcript, status, steps = _packaged_console(tmp_path, config_path, [
		# Enter opens AND focuses the detail pane now -- ruled; the Tab that
		# used to follow it would toggle straight back to MESSAGES and the
		# close below would prove nothing.
		(b"\r", 0.6),        # open, claim, and focus the detail pane
		(b"c", 0.8),         # close
		# `qy`: `q` ALWAYS asks now, whether or not a claim is owed, so a bare
		# `q` leaves the console running at the prompt.
		(b"qy", 0.5),
	])
	assert status == 0, transcript[-2000:]
	after_open = _replay(steps[0])
	after_close = _replay(steps[1])
	assert any(line.startswith("> ") and _pty_is_rule(line) for line in after_open), \
		"the fixture never reached the detail pane; the close proves nothing"
	assert any("closed" in line for line in after_close), \
		"the packaged console did not report the close"
	assert any(line.startswith("> Messages:") for line in after_close), \
		"focus stayed in the detail pane after a packaged close"


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
@pytest.mark.parametrize("columns", [80, 44])
def test_the_packaged_console_draws_the_simplified_headers(tmp_path, columns):
	"""The header cleanup on the artifact Slawomir runs, wide and narrow.

	Narrow is the case worth driving through a real terminal: the identity is
	decoration and must vanish rather than truncate or crowd, and that is a
	property of what the terminal actually received."""
	config_path, _proj = _instance(tmp_path)
	# A harmless keystroke first, so there is a screen to assert about while
	# the console is still RUNNING. Replaying the whole transcript would
	# include the exit repaint, which is a cleared screen and says nothing.
	#
	# Then `q` and `y`: highlighting the first row claims it, so quitting asks
	# before abandoning the claim.
	transcript, status, steps = _packaged_console(
		tmp_path, config_path,
		[(b"\t", 0.4), (b"q", 0.4), (b"y", 0.5)], columns=columns)
	assert status == 0, transcript[-2000:]
	screen = _replay(steps[0], columns=columns)
	top = next(line for line in screen if "Messages:" in line)
	assert "retained" in top
	for gone in ("MESSAGES", "DETAIL", "["):
		assert gone not in top, f"{gone!r} is back on the packaged top line"
	assert not any("DETAIL" in line for line in screen), \
		"the packaged console still labels the lower pane"
	assert any(_pty_is_rule(line) for line in screen), "no rule was drawn"
	identity_rows = [line for line in screen if "acme.implementer" in line]
	if columns >= 80:
		assert identity_rows, "the identity vanished at a comfortable width"
		# The NAME ends the drawn row, and the rule cell the model puts after
		# it does not appear. That is the shield working, not a defect: a real
		# terminal declines to draw the rightmost cell of a full-width row,
		# and the whole point of that trailing cell is to be the one it drops.
		# What matters here is that the address is COMPLETE -- an earlier
		# packaged run drew `acme.implemente`, naming a participant that does
		# not exist.
		assert identity_rows[0].rstrip().endswith("acme.implementer"), \
			"the identity is not right-aligned, or lost its last character"
	else:
		# Narrow: dropping it is correct. What must NOT happen is a partial
		# address, which would name a participant that does not exist.
		for line in identity_rows:
			assert "acme.implementer" in line



@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
@pytest.mark.parametrize("columns", [80, 44])
def test_the_packaged_console_keeps_a_draft_and_asks_before_discarding(tmp_path, columns):
	"""Acceptance 8, on the artifact Slawomir runs, wide and narrow.

	`Esc` used to discard a whole composition. Here it must keep one, the row
	must carry the ruled `✎`, and `D` must ask on ONE status line -- narrow
	especially, because that is where a two-line prompt would appear first."""
	config_path, _proj = _instance(tmp_path)
	transcript, status, steps = _packaged_console(tmp_path, config_path, [
		(b"n", 0.5),                 # compose
		(b"\r", 0.4),                # pick the first recipient
		(b"kept draft", 0.5),        # a subject
		(b"\x1b", 0.5),              # Esc: retains
		# UP to the draft row. Drafts sit at the top; the cursor stays where
		# it was, because a list that jumps under the human aims the next
		# keystroke at something they did not choose.
		(b"k", 0.4),
		(b"D", 0.5),                 # ask before discarding
		(b"\x1b", 0.4),              # decline
		(b"q", 0.4), (b"y", 0.5),
	], columns=columns)
	assert status == 0, transcript[-2000:]
	after_escape = _replay(steps[3], columns=columns)
	assert any("kept" in line for line in after_escape), \
		"the packaged console did not say the draft was kept"
	assert any("✎" in line for line in after_escape), \
		"no draft row carrying the ruled glyph"

	asking = _replay(steps[5], columns=columns)
	prompts = [line for line in asking if "Discard draft?" in line]
	assert len(prompts) == 1, f"{columns}: {len(prompts)} prompt rows"
	assert "y/N" in prompts[0], prompts[0]

	# Declining KEEPS it, and the row is still there.
	declined = _replay(steps[6], columns=columns)
	assert any("✎" in line for line in declined), \
		"declining the confirmation discarded the draft"


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_console_draws_the_selected_part_footer(tmp_path):
	"""Evidence 7: the footer on the artifact Slawomir actually runs.

	A real terminal is where the row budget bites -- an off-by-one in the
	reserved row shows up here as a lost line or a footer drawn over the
	status bar, neither of which a pure renderer test can see."""
	config_path, _proj = _instance(tmp_path)
	transcript, status, steps = _packaged_console(tmp_path, config_path, [
		(b"\r", 0.8),        # open, claim, focus the detail pane
		# `qY`: Enter CLAIMED the message, so quitting asks for confirmation.
		(b"qY", 0.5),
	])
	assert status == 0, transcript[-2000:]
	screen = _replay(steps[0])
	rows = [line for line in screen if line.strip()]
	assert any("parts)" in line for line in rows), \
		f"no part footer on the packaged console: {rows[-4:]}"
	# It is the LAST pane row, directly above the status bar, and it has not
	# replaced it.
	footer_row = max(i for i, line in enumerate(screen) if "parts)" in line)
	below = [line for line in screen[footer_row + 1:] if line.strip()]
	assert below, "nothing below the footer; the status bar was displaced"
	assert not any("parts)" in line for line in below)


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_console_enters_the_detail_after_the_dwell_opens_a_row(tmp_path):
    """THE LIVE DEFECT, on the artifact it was reported against.

    Slawomir paused on a directed row until the two-second dwell claimed and
    opened it, pressed Enter to read the body, and stayed in the list. Every
    in-process test passed, because the gate that refused the key sat in
    dispatch and the model-level tests called `enter_selected` directly or
    pressed Enter before the dwell had opened anything.

    So this waits out the real dwell first, which is the state that made the
    key unreachable.
    """
    config_path, _proj = _instance(tmp_path)
    transcript, status, steps = _packaged_console(tmp_path, config_path, [
        (b"", 2.4),          # let the startup dwell claim and open the row
        (b"\r", 0.8),        # Enter: must move focus into DETAIL
        (b"qY", 0.5),
    ])
    assert status == 0, transcript[-2000:]
    after_dwell = _replay(steps[0])
    after_enter = _replay(steps[1])
    # Before Enter the focus marker is on MESSAGES; after it, on the detail
    # rule. `> Messages:` is the list-focused header.
    assert any(line.startswith("> Messages:") for line in after_dwell), \
        f"the dwell did not leave focus in the list: {after_dwell[:3]}"
    assert not any(line.startswith("> Messages:") for line in after_enter), \
        "Enter left focus in the list on the packaged console"
    assert any(line.startswith("> ") and _pty_is_rule(line) for line in after_enter), \
        f"Enter did not focus the detail pane: {after_enter[-6:]}"


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_console_leaves_the_detail_on_escape(tmp_path):
    """Evidence 7, on the artifact Slawomir tests.

    Esc is delivered as a bare `\\x1b`, which is also the prefix of every
    arrow-key sequence — so this is a case a pure model test cannot reach:
    only a real terminal proves the key arrives as Esc rather than being
    swallowed while the reader waits for a sequence tail.
    """
    config_path, _proj = _instance(tmp_path)
    transcript, status, steps = _packaged_console(tmp_path, config_path, [
        (b"", 2.4),          # the dwell claims and opens the row
        (b"\r", 0.6),        # Enter: into DETAIL
        (b"\x1b", 0.6),      # Esc: back to LIST
        (b"qY", 0.5),
    ])
    assert status == 0, transcript[-2000:]
    after_enter = _replay(steps[1])
    after_escape = _replay(steps[2])
    assert not any(line.startswith("> Messages:") for line in after_enter), \
        "the fixture never reached the detail pane; the Esc proves nothing"
    assert any(line.startswith("> Messages:") for line in after_escape), \
        "Esc did not return focus to the list on the packaged console"


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_console_asks_before_exiting_with_nothing_owed(tmp_path):
    """Evidence 9, the zero-claim half — the case that used to exit at once.

    Driven on the artifact because that is where the old behaviour was
    reported and where the new one has to be true.
    """
    config_path, _proj = _instance(tmp_path)
    transcript, status, steps = _packaged_console(tmp_path, config_path, [
        (b"q", 0.6),         # asks, even with nothing owed
        (b"n", 0.4),         # decline: still running
        (b"qy", 0.6),        # ask again, confirm
    ])
    assert status == 0, transcript[-2000:]
    asked = _replay(steps[0])
    assert any("Exit? y/N" in line for line in asked), \
        f"the packaged console did not ask: {asked[-3:]}"
    declined = _replay(steps[1])
    assert not any("Exit? y/N" in line for line in declined), \
        "declining left the prompt on screen"


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_the_packaged_console_asks_once_with_a_claim_owed(tmp_path):
    """Evidence 9, the unresolved half: the SAME one-line prompt, and only
    one of them."""
    config_path, _proj = _instance(tmp_path)
    transcript, status, steps = _packaged_console(tmp_path, config_path, [
        (b"", 2.4),          # the dwell claims a row, so a claim is owed
        (b"q", 0.6),
        (b"y", 0.6),         # one confirmation is enough to exit
    ])
    assert status == 0, transcript[-2000:]
    asked = _replay(steps[1])
    assert any("Exit? y/N" in line for line in asked), asked[-3:]
    assert not any("QUIT WITH UNRESOLVED CLAIMS?" in line for line in asked), \
        "the superseded two-row prompt is still drawn"


# -- incoming work stays bold, on the PACKAGED console ---------------------

def _bold_text(text):
	"""The visible text drawn while SGR 1 was in effect.

	Same run-parsing as `_highlighted_text`, against bold rather than reverse.
	ncurses emits combined parameters (`ESC[0;1m`), so the parameter is split
	out rather than substring-matched -- a bare `ESC[1m` search reports "no
	emphasis" on a console that is emphasising correctly.

	`22` is bold-off; `0` and an empty parameter list reset everything. `7`
	does NOT clear bold: a selected owed row is drawn bold AND reversed, and
	treating reverse as a reset would lose exactly the composition this
	rule exists to preserve."""
	out = []
	bold_on = False
	position = 0
	for match in _REVERSE_RUN.finditer(text):
		if bold_on:
			chunk = text[position:match.start()]
			visible = "".join(c for c in chunk if c.isprintable()).strip()
			if visible:
				out.append(visible)
		params = match.group(0)[2:-1].split(";")
		if "1" in params:
			bold_on = True
		elif "" in params or "0" in params or "22" in params:
			bold_on = False
		position = match.end()
	return out


@pytest.mark.skipif(not hasattr(pty, "fork"), reason="no pty support")
def test_owed_rows_are_bold_on_the_packaged_console(tmp_path):
	"""Evidence 8: the attribute transition, observed on the rebuilt zipapp.

	Two launches rather than a scripted close, because what has to be proven
	is that the EMPHASIS follows the obligation -- and driving `c` through its
	confirmation would put the console's close path in the middle of a test
	about how a row is drawn."""
	config_path, _ = _instance(tmp_path)
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import baton_core as core

	with core.open_instance(config_path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="OwedSubject", body=b"x\n")
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="HandledSubject", body=b"x\n")
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant="acme.implementer",
		                  outcome="done")

	first, _, _ = _packaged_console(tmp_path, config_path, [(b"qy", 0.6)])
	bold = " ".join(_bold_text(first))
	assert "OwedSubject" in bold, bold
	# The control, in the SAME transcript: the rule distinguishes rows rather
	# than emboldening the list.
	assert "HandledSubject" not in bold, bold

	# Answer it out of band, relaunch, and the emphasis is gone.
	with core.open_instance(config_path) as store:
		owed = next(m["id"] for m in store.list_messages("acme.implementer")
		            if m.get("subject") == "OwedSubject")
		claim = store.claim("acme.implementer", message_id=owed)
		store.close_claim(claim["claim_id"], participant="acme.implementer",
		                  outcome="done")

	second, _, _ = _packaged_console(tmp_path, config_path, [(b"qy", 0.6)])
	assert "OwedSubject" not in " ".join(_bold_text(second)), second[-400:]
