"""Measure the v11 TUI's no-input loop through a real pseudo-terminal.

The child uses the repository source against the deployed v11 configuration.
FINDING.md records the source/deployed byte comparison that makes this a valid
probe of the deployed loop.  The first render is measured separately; the idle
sample starts after it and stops when the parent sends the first input byte.
"""

from __future__ import annotations

import cProfile
import io
import json
import os
import pty
import pstats
import select
import sys
import time
from pathlib import Path


CONFIG = "/home/sl/baton-v11.14aecfb/baton.json"
PARTICIPANT = "baton.slaw"
SAMPLE_SECONDS = 8.25
MODE = sys.argv[1] if len(sys.argv) > 1 else "normal"
VIEW = sys.argv[2] if len(sys.argv) > 2 else "jobs"


def _child(metrics_fd: int) -> None:
	os.environ["TERM"] = "xterm"
	os.environ["ESCDELAY"] = "25"
	os.environ["LINES"] = "32"
	os.environ["COLUMNS"] = "110"
	sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "src"))
	from baton_work import cli
	from baton_work.tui import app

	stats = {
		"initial_render_wall_seconds": 0.0,
		"initial_render_cpu_seconds": 0.0,
		"idle_read_calls": 0,
		"idle_read_timeouts": 0,
		"idle_read_blocked_wall_seconds": 0.0,
		"idle_renders": 0,
		"idle_render_wall_seconds": 0.0,
		"idle_render_cpu_seconds": 0.0,
		"idle_ticks": 0,
		"idle_poll_cpu_seconds": 0.0,
		"idle_tree_calls": 0,
		"idle_tree_cpu_seconds": 0.0,
		"idle_windows": 0,
		"idle_window_wall_seconds": 0.0,
		"idle_window_cpu_seconds": 0.0,
	}
	state = {"first_render": True, "active": False}
	real_read = app._read_key
	real_init = app.Console.__init__
	real_render = app.Console.render
	real_tick = app.Console.tick
	real_window = app.Console._window
	real_tree = app.projection.tree

	def measured_init(self, *args, **kwargs):
		real_init(self, *args, **kwargs)
		self.tab = VIEW

	def measured_read(screen):
		started = time.monotonic()
		key = real_read(screen)
		if state["active"]:
			stats["idle_read_calls"] += 1
			stats["idle_read_blocked_wall_seconds"] += time.monotonic() - started
			if key == -1:
				stats["idle_read_timeouts"] += 1
			else:
				state["active"] = False
				stats["idle_elapsed_seconds"] = time.monotonic() - stats["idle_started_wall"]
				stats["idle_cpu_seconds"] = time.process_time() - stats["idle_started_cpu"]
		return key

	def measured_render(self, screen):
		started_wall = time.monotonic()
		started_cpu = time.process_time()
		result = real_render(self, screen)
		wall = time.monotonic() - started_wall
		cpu = time.process_time() - started_cpu
		if state["first_render"]:
			state["first_render"] = False
			stats["initial_render_wall_seconds"] = wall
			stats["initial_render_cpu_seconds"] = cpu
			stats["idle_started_wall"] = time.monotonic()
			stats["idle_started_cpu"] = time.process_time()
			state["active"] = True
		elif state["active"]:
			stats["idle_renders"] += 1
			stats["idle_render_wall_seconds"] += wall
			stats["idle_render_cpu_seconds"] += cpu
		return result

	def measured_tick(self):
		if state["active"]:
			stats["idle_ticks"] += 1
		if MODE == "poll-only":
			started_cpu = time.process_time()
			self.store.last_seq()
			stats["idle_poll_cpu_seconds"] += time.process_time() - started_cpu
			return None
		return real_tick(self)

	def measured_window(self):
		started_wall = time.monotonic()
		started_cpu = time.process_time()
		result = real_window(self)
		if state["active"]:
			stats["idle_windows"] += 1
			stats["idle_window_wall_seconds"] += time.monotonic() - started_wall
			stats["idle_window_cpu_seconds"] += time.process_time() - started_cpu
		return result

	def measured_tree(*args, **kwargs):
		started_cpu = time.process_time()
		profile = None
		if state["active"] and stats["idle_tree_calls"] == 0:
			profile = cProfile.Profile()
			profile.enable()
		result = real_tree(*args, **kwargs)
		if profile is not None:
			profile.disable()
			stream = io.StringIO()
			pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(20)
			stats["first_idle_tree_profile"] = stream.getvalue()
		if state["active"]:
			stats["idle_tree_calls"] += 1
			stats["idle_tree_cpu_seconds"] += time.process_time() - started_cpu
			stats["tree_rows"] = len(result["rows"])
			stats["tree_active_trails"] = len(result.get("active_trails") or ())
		return result

	app._read_key = measured_read
	app.Console.__init__ = measured_init
	app.Console.render = measured_render
	app.Console.tick = measured_tick
	app.Console._window = measured_window
	app.projection.tree = measured_tree
	try:
		status = cli.main(["--config", CONFIG, "--participant", PARTICIPANT, "tui"])
		stats["exit_status"] = status
	except BaseException as error:
		stats["error"] = f"{type(error).__name__}: {error}"
	finally:
		os.write(metrics_fd, json.dumps(stats, sort_keys=True).encode() + b"\n")


def main() -> int:
	metrics_read, metrics_write = os.pipe()
	pid, terminal = pty.fork()
	if pid == 0:
		os.close(metrics_read)
		try:
			_child(metrics_write)
		except BaseException as error:
			os.write(metrics_write, json.dumps({
				"bootstrap_error": f"{type(error).__name__}: {error}",
			}).encode() + b"\n")
		os._exit(0)
	os.close(metrics_write)
	transcript = bytearray()
	started = time.monotonic()
	while time.monotonic() - started < SAMPLE_SECONDS:
		ready, _, _ = select.select([terminal], [], [], 0.05)
		if ready:
			try:
				transcript.extend(os.read(terminal, 65536))
			except OSError:
				break
	os.write(terminal, b"q")
	time.sleep(0.05)
	os.write(terminal, b"y")
	deadline = time.monotonic() + 5.0
	while time.monotonic() < deadline:
		finished, status, usage = os.wait4(pid, os.WNOHANG)
		if finished:
			break
		ready, _, _ = select.select([terminal], [], [], 0.05)
		if ready:
			try:
				transcript.extend(os.read(terminal, 65536))
			except OSError:
				pass
	else:
		print(json.dumps({"error": "child did not exit after q/y", "pid": pid}))
		return 2
	metrics = os.read(metrics_read, 65536).decode().strip()
	if not metrics:
		print(json.dumps({
			"error": "child emitted no metrics",
			"transcript_tail": transcript[-2000:].decode(errors="replace"),
			"wait_status": status,
		}, indent=2, sort_keys=True))
		return 3
	result = json.loads(metrics)
	result.update({
		"child_user_seconds": usage.ru_utime,
		"child_system_seconds": usage.ru_stime,
		"parent_sample_seconds": SAMPLE_SECONDS,
		"probe_mode": MODE,
		"probe_view": VIEW,
		"terminal_output_bytes": len(transcript),
		"wait_status": status,
	})
	print(json.dumps(result, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
