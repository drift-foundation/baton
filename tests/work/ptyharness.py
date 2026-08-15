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


def replay(transcript: str, columns: int = 110, lines: int = 32) -> list[str]:
	"""The final screen, reconstructed from the raw byte stream."""
	grid = [[" "] * columns for _ in range(lines)]
	row = col = 0
	index = 0
	while index < len(transcript):
		char = transcript[index]
		if char == "\x1b":
			for pattern in (_CSI, _OSC, _STRING, _TWO):
				match = pattern.match(transcript, index)
				if match:
					seq = match.group(0)
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
					index = match.end()
					break
			else:
				index += 1
			continue
		if char == "\r":
			col = 0
		elif char == "\n":
			row += 1
		elif char == "\b":
			col = max(0, col - 1)
		elif char >= " ":
			if row < lines and col < columns:
				grid[row][col] = char
			col += 1
		index = index + 1
	return ["".join(line).rstrip() for line in grid]


def drive(authority_path: str, viewer: str, script,
          columns: int = 110, lines: int = 32, settle: float = 0.6,
          command=None):
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
		os.environ["LINES"] = str(lines)
		os.environ["COLUMNS"] = str(columns)
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
	for keys, pause in script:
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
