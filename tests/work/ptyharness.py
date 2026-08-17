"""A small real-terminal harness for the v11 console — B1/B2.

The same discipline as `tests/tui/test_tui_pty.py`, restated compactly rather
than imported: curses chooses freely among cursor-addressing spellings, so
every assertion replays the transcript into a character grid and asks what a
human would have SEEN, never which escape sequences happened to paint it.
Kept local because coupling the v11 suite to the v10 test module would make
Gate B evidence depend on a file the v10 line may change.
"""

from __future__ import annotations

import os
import pty
import re
import select
import struct
import sys
import time

_CSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_OSC = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
_STRING = re.compile(r"\x1b[PX^_][^\x1b]*(?:\x1b\\)?")
_TWO = re.compile(r"\x1b[ -/]*[0-~]")


def replay(transcript: str, columns: int = 110, lines: int = 32,
           cursor: bool = False):
	"""The final screen, reconstructed from the raw byte stream. With
	`cursor=True` also the terminal caret a human would SEE: its final
	(row, col) and whether the last visibility control (DECTCEM) left
	it shown — W14's visible-caret evidence."""
	grid = [[" "] * columns for _ in range(lines)]
	row = col = 0
	index = 0
	# Scroll-region state: ncurses optimizes refreshes with insert/
	# delete-line and index scrolling — a replay that ignores them
	# shows stale ghost rows.
	scroll_top, scroll_bottom = 0, lines - 1

	def scroll_up(count, top, bottom):
		for _ in range(count):
			del grid[top]
			grid.insert(bottom, [" "] * columns)

	def scroll_down(count, top, bottom):
		for _ in range(count):
			del grid[bottom]
			grid.insert(top, [" "] * columns)
	while index < len(transcript):
		char = transcript[index]
		if char == "\x1b":
			for pattern in (_CSI, _OSC, _STRING, _TWO):
				match = pattern.match(transcript, index)
				if match:
					seq = match.group(0)
					if pattern is _TWO and seq in ("\x1bD", "\x1bM"):
						if seq == "\x1bD":
							if row >= scroll_bottom:
								scroll_up(1, scroll_top, scroll_bottom)
							else:
								row += 1
						else:
							if row <= scroll_top:
								scroll_down(1, scroll_top,
								            scroll_bottom)
							else:
								row = max(0, row - 1)
					if pattern is _CSI:
						final = seq[-1]
						params = seq[2:-1]
						if final in "Hf":
							parts = (params.split(";") + ["1", "1"])[:2]
							row = max(0, int(parts[0] or 1) - 1)
							col = max(0, int(parts[1] or 1) - 1)
						elif final == "d":
							row = max(0, int(params or 1) - 1)
						elif final == "G":
							col = max(0, int(params or 1) - 1)
						elif final == "A":
							row = max(0, row - int(params or 1))
						elif final == "B":
							row = row + int(params or 1)
						elif final == "C":
							col = col + int(params or 1)
						elif final == "D":
							col = max(0, col - int(params or 1))
						elif final == "K":
							for k in range(col, columns):
								grid[min(row, lines - 1)][k] = " "
						elif final == "J":
							if params in ("2", "3"):
								grid = [[" "] * columns
								        for _ in range(lines)]
							elif params in ("", "0"):
								for k in range(col, columns):
									grid[min(row, lines - 1)][k] = " "
								for r in range(row + 1, lines):
									grid[r] = [" "] * columns
						elif final == "X":
							count = int(params or 1)
							for k in range(col, min(columns, col + count)):
								grid[min(row, lines - 1)][k] = " "
						elif final == "P":
							count = int(params or 1)
							line = grid[min(row, lines - 1)]
							del line[col:col + count]
							line.extend(" " * (columns - len(line)))
						elif final == "r":
							parts = (params.split(";") + ["", ""])[:2]
							scroll_top = max(0, int(parts[0] or 1) - 1)
							scroll_bottom = min(
								lines - 1,
								int(parts[1] or lines) - 1)
							row = col = 0
						elif final == "L":
							scroll_down(int(params or 1),
							            min(row, lines - 1),
							            scroll_bottom)
						elif final == "M":
							scroll_up(int(params or 1),
							          min(row, lines - 1),
							          scroll_bottom)
						elif final == "S":
							scroll_up(int(params or 1), scroll_top,
							          scroll_bottom)
						elif final == "T":
							scroll_down(int(params or 1), scroll_top,
							            scroll_bottom)
					index = match.end()
					break
			else:
				index += 1
			continue
		if char == "\r":
			col = 0
		elif char == "\n":
			# A line feed at the bottom of the active scroll region
			# scrolls the region up — ncurses drives its hardware
			# scroll optimization exactly this way.
			if row == scroll_bottom:
				scroll_up(1, scroll_top, scroll_bottom)
			else:
				row += 1
		elif char == "\b":
			col = max(0, col - 1)
		elif char >= " ":
			if row < lines and col < columns:
				grid[row][col] = char
			col += 1
		index = index + 1
	final = ["".join(line).rstrip() for line in grid]
	if not cursor:
		return final
	visible = (transcript.rfind("\x1b[?25h")
	           > transcript.rfind("\x1b[?25l"))
	return final, (row, col, visible)


def drive(authority_path: str, viewer: str, script,
          columns: int = 110, lines: int = 32, settle: float = 0.6,
          command=None, dynamic_size: bool = False):
	"""Spawn the console on a real pty, feed `script` [(bytes, pause)...],
	return (whole_transcript, exit_status, per_step_prefixes).

	`command` selects the ENTRY: None drives the source tree via
	`-m baton_work.cli`; a list (e.g. [sys.executable, archive]) drives a
	packaged artifact — with PYTHONPATH deliberately absent, so the
	archive stands alone (B3)."""
	import fcntl
	import termios

	src = os.path.join(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__)))), "src")
	pid, fd = pty.fork()
	if pid == 0:
		os.environ["TERM"] = "xterm"
		os.environ["ESCDELAY"] = "25"
		# DETERMINISTIC GEOMETRY: the parent's TIOCSWINSZ races curses
		# initialization in the child (it lost under pytest's slower start,
		# rendering an 80x24 layout the parser then misread). curses honors
		# LINES/COLUMNS over the ioctl, so state them.
		if not dynamic_size:
			os.environ["LINES"] = str(lines)
			os.environ["COLUMNS"] = str(columns)
		else:
			# R4 resize tests: geometry must stay ioctl-driven so a
			# mid-script TIOCSWINSZ (+SIGWINCH) reaches curses. Any
			# INHERITED LINES/COLUMNS (pytest's own terminal) would
			# override the ioctl, so they are removed — and the initial
			# size cannot race curses startup, so the CHILD stamps its
			# own slave winsize BEFORE exec.
			# readline (initialized by pytest) putenv()s COLUMNS/LINES
			# at C level where os.environ never sees them — unset at
			# BOTH levels or the exec'd curses inherits a stale 80x24.
			os.environ.pop("LINES", None)
			os.environ.pop("COLUMNS", None)
			os.unsetenv("LINES")
			os.unsetenv("COLUMNS")
			fcntl.ioctl(0, termios.TIOCSWINSZ,
			            struct.pack("HHHH", lines, columns, 0, 0))
		os.environ["LANG"] = "C.UTF-8"
		if command is None:
			os.environ["PYTHONPATH"] = src
			argv = [sys.executable, "-m", "baton_work.cli"]
		else:
			os.environ.pop("PYTHONPATH", None)
			argv = list(command)
		os.execv(argv[0], argv + ["--config", authority_path,
		                          "--participant", viewer, "tui"])
	fcntl.ioctl(fd, termios.TIOCSWINSZ,
	            struct.pack("HHHH", lines, columns, 0, 0))
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
	import signal
	for entry in script:
		if entry[0] == "resize":
			# A mid-script terminal resize: new winsize + SIGWINCH; the
			# console consumes KEY_RESIZE and repaints at the new size.
			_tag, (new_columns, new_lines), pause = entry
			fcntl.ioctl(fd, termios.TIOCSWINSZ,
			            struct.pack("HHHH", new_lines, new_columns,
			                        0, 0))
			os.kill(pid, signal.SIGWINCH)
			pump(pause)
			prefixes.append(out.decode("utf-8", "replace"))
			continue
		if entry[0] == "call":
			# W336: an in-script Python hook — lets a test mutate the
			# authority from THIS process while the console runs, so a
			# live timer/render loop can observe a genuine change.
			_tag, hook, pause = entry
			hook()
			pump(pause)
			prefixes.append(out.decode("utf-8", "replace"))
			continue
		keys, pause = entry
		os.write(fd, keys)
		pump(pause)
		prefixes.append(out.decode("utf-8", "replace"))
	deadline = time.time() + 5
	status = 0
	while time.time() < deadline:
		done, status = os.waitpid(pid, os.WNOHANG)
		if done:
			break
		pump(0.05)
	else:
		os.kill(pid, 9)
		os.waitpid(pid, 0)
		raise AssertionError("console did not exit; transcript tail: "
		                     + out[-800:].decode("utf-8", "replace"))
	try:
		os.close(fd)
	except OSError:
		pass
	return out.decode("utf-8", "replace"), status, prefixes
