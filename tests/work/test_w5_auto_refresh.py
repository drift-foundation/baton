"""W5: configurable timer-based automatic refresh (same-schema iteration).

The configured timer (default 2s, `tui --refresh SECONDS`, positive) is the
ONE background trigger for fresh canonical reads. Ordinary keystrokes operate
on the cached projection and never query the authority. A refresh is
read-only: no seen mark, no transition, and the selection anchors to the
Work id — rows changing never moves the cursor to a different Work.
"""

from __future__ import annotations

import json as _json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


@pytest.fixture()
def world(tmp_path):
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	from baton_work import lifecycle as lc
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	first = tr.create_work(store, team="lang", kind="bug",
	                       title="already here", origin="external-report",
	                       author="ada", body="first opener")
	store.close()
	return {"config": config_path, "database": result["database"],
	        "first": first}


def _drive_with_refresh(world, script, refresh, **kw):
	"""Drive the console with a custom --refresh via the harness's raw
	command path (the source-tree entry plus the tui flag)."""
	src = os.path.join(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__)))), "src")
	# drive() itself appends the `tui` verb; the helper adds only the
	# refresh flag after it.
	env_helper = (
		"import os,sys;"
		f"sys.path.insert(0, {src!r});"
		"from baton_work import cli;"
		"sys.exit(cli.main(sys.argv[1:] + "
		f"['--refresh', {refresh!r}]))")
	return ptyharness.drive(
		world["config"], "lang.grace", script,
		command=[sys.executable, "-c", env_helper], **kw)


def test_the_timer_is_the_one_background_trigger(world, tmp_path):
	"""In-process: paint once; keystrokes on the unchanged view hit the
	cache (zero authority reads); tick() is what re-reads; an external
	Work appears after tick and the anchored selection survives."""
	from baton_work.tui.app import Console
	from baton_work import projection as pj_mod

	store = bw.Authority(world["database"])

	class Screen:
		def addnstr(self, *_args):
			pass

	console = Console(store, "lang", "grace")
	console._render_table(Screen(), 20, 100, console.rows())

	calls = {"n": 0}
	real_tree = pj_mod.tree

	def counting_tree(*args, **kw):
		calls["n"] += 1
		return real_tree(*args, **kw)

	pj_mod.tree = counting_tree
	try:
		# Ordinary keystrokes on the SAME view: no authority reads.
		for key in (ord("j"), ord("k"), ord("j"), ord("k"), 27):
			console.handle(key)
			console._render_table(Screen(), 20, 100, console.rows())
		assert calls["n"] == 0, \
			f"keystrokes polled the authority {calls['n']} times"

		# An external participant commits a new Work.
		other = bw.Authority(world["database"])
		created = tr.create_work(other, team="lang", kind="bug",
		                         title="appeared externally",
		                         origin="external-report", author="ada",
		                         body="surprise")
		other.close()

		# Still no keystroke-driven read...
		console.handle(ord("j"))
		rows = console.rows()
		assert all(row["title"] != "appeared externally"
		           for row in rows), "a keystroke saw fresh data"
		assert calls["n"] == 0

		# ...the TICK is a producer on the one refresh path.
		console.tick()
		rows = console.rows()
		assert calls["n"] == 1
		assert any(row["title"] == "appeared externally"
		           for row in rows), "the tick did not refresh"

		# Pending requests COALESCE (pinned): several producers before
		# one consumption re-read exactly once.
		console.tick()
		console.tick()
		console.tick()
		console.rows()
		assert calls["n"] == 2, \
			"coalesced refresh requests re-read more than once"
	finally:
		pj_mod.tree = real_tree
	store.close()


def test_a_refresh_is_read_only_and_selection_is_id_stable(world):
	"""Real PTY, the discriminating case: with [A, B, C] and the cursor
	anchored on B, another participant CLOSES A while the console
	idles — the collapsed view drops A, an index-stable cursor would
	land on C, the id anchor must keep B (Enter drills B). The refresh
	also marks nothing seen."""
	store = bw.Authority(world["database"])
	middle = tr.create_work(store, team="lang", kind="bug",
	                        title="middle target",
	                        origin="external-report", author="ada",
	                        body="the anchor")
	tr.create_work(store, team="lang", kind="bug", title="tail row",
	               origin="external-report", author="ada", body="last")
	before_new = pj.new_count(store, middle["work_id"],
	                          viewer_team="lang",
	                          viewer_member="grace")["total"]
	store.close()

	import threading

	def external():
		other = bw.Authority(world["database"])
		tr.close_work(other, world["first"]["work_id"],
		              actor_team="lang", actor="ada",
		              rationale="closed while the console idles",
		              outcome="satisfying")
		tr.post_thread(other, middle["thread"], author_team="lang",
		               author="ada", body="a fresh unseen message")
		other.close()

	timer = threading.Timer(1.4, external)
	timer.start()
	try:
		script = [
			(b"j", 0.6),              # anchor on B ("middle target")
			(b"", 2.2),               # idle across the external close
			(b"\r", 0.6),             # Enter drills the ANCHORED work
			(b"q", 0.4),
		]
		text, status, steps = _drive_with_refresh(
			world, script, "0.5", settle=1.0)
	finally:
		timer.join()
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	idle = "\n".join(ptyharness.replay(steps[1]))
	assert "already here" not in idle, \
		"the externally closed row did not leave the collapsed view"
	assert "(1 closed hidden" in idle, \
		"the collapse lost its explicit hidden count"
	detail = ptyharness.replay(steps[2])
	assert "middle target" in detail[0], \
		f"the refresh moved the selection off the anchored Work: " \
		f"{detail[0]!r}"

	store = bw.Authority(world["database"])
	after_new = pj.new_count(store, middle["work_id"],
	                         viewer_team="lang",
	                         viewer_member="grace")["total"]
	store.close()
	assert after_new == before_new + 1, \
		"the background refresh marked something seen"


def test_the_refresh_interval_must_be_positive(world):
	import subprocess
	src = os.path.join(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__)))), "src")
	env = dict(os.environ, PYTHONPATH=src)
	proc = subprocess.run(
		[sys.executable, "-m", "baton_work.cli", "--config",
		 world["config"], "--participant", "lang.ada", "tui",
		 "--refresh", "0"],
		capture_output=True, text=True, timeout=120, env=env)
	assert proc.returncode == 1
	assert "positive" in proc.stderr
	assert "\x1b[?1049h" not in proc.stdout, \
		"curses claimed the screen before the refusal"


def test_continuous_input_cannot_postpone_the_refresh(world):
	"""R1: keys arriving faster than the interval for longer than one
	interval — the wall-clock deadline still fires and the externally
	created Work appears on schedule; no key acts as a poll."""
	import threading

	def external():
		other = bw.Authority(world["database"])
		tr.create_work(other, team="lang", kind="bug",
		               title="on schedule", origin="external-report",
		               author="ada", body="appeared while typing")
		other.close()

	timer = threading.Timer(1.2, external)
	timer.start()
	try:
		# ~2.4s of keys at 150ms spacing (j/k alternating) with a
		# 0.5s interval: several deadlines pass DURING typing.
		script = [(b"j" if index % 2 else b"k", 0.15)
		          for index in range(16)]
		script += [(b"", 0.3), (b"q", 0.4)]
		text, status, steps = _drive_with_refresh(
			world, script, "0.5", settle=1.0)
	finally:
		timer.join()
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	# The Work must be visible well before the typing stops: by the
	# 12th keypress (~1.8s, three deadlines past the 1.2s commit).
	mid = "\n".join(ptyharness.replay(steps[11]))
	assert "on schedule" in mid, \
		"continuous input postponed the wall-clock refresh"


def test_only_a_successful_mutation_invalidates_the_cache(world):
	"""R2: a refused command and a successful pure read leave the cache
	alone; a successful mutating act refreshes its committed result."""
	from baton_work.tui.app import Console
	from baton_work import projection as pj_mod

	store = bw.Authority(world["database"])

	class Screen:
		def addnstr(self, *_args):
			pass

	console = Console(store, "lang", "grace",
	                  config_path=world["config"])
	console._render_table(Screen(), 20, 100, console.rows())
	target = world["first"]["work_id"]

	calls = {"n": 0}
	real_tree = pj_mod.tree

	def counting_tree(*args, **kw):
		calls["n"] += 1
		return real_tree(*args, **kw)

	pj_mod.tree = counting_tree
	try:
		# A REFUSED command (close without rationale): cache intact.
		console.execute(f"close {target}")
		assert "rationale" in console.status
		console.rows()
		assert calls["n"] == 0, "a refused command flushed the cache"

		# A successful PURE READ: cache intact.
		console.execute(f"breadcrumb {target}")
		assert console.status.startswith("ok")
		console.rows()
		assert calls["n"] == 0, "a pure read flushed the cache"

		# A successful MUTATION: the next paint re-reads.
		console.execute("create --team lang --kind bug "
		                "--title committed --origin self-initiated "
		                "--body fresh")
		assert console.status.startswith("ok")
		rows = console.rows()
		assert calls["n"] == 1, \
			"a committed mutation did not refresh its result"
		assert any(row["title"] == "committed" for row in rows)

		# R4: the SAME public grammar with leading globals — the verb,
		# not the first raw token, decides. An --op-id mutation commits
		# and is visible immediately; the cache flushed exactly once.
		console.execute("--op-id bar-1 create --team lang --kind bug "
		                "--title protected-commit "
		                "--origin self-initiated --body fresh")
		assert console.status.startswith("ok")
		rows = console.rows()
		assert calls["n"] == 2, \
			"an --op-id-prefixed mutation left the view stale"
		assert any(row["title"] == "protected-commit" for row in rows)

		# ...and an ACTUAL --ref-carrying mutation likewise (R6): the
		# independent reference rides a say into the first work's
		# thread through the same leading-global grammar.
		thread_id = world["first"]["thread"]
		console.execute(f"--ref pushcoin:docs/evidence.md "
		                f"say {thread_id} --body evidence-noted")
		assert console.status.startswith("ok"), console.status
		console.rows()
		assert calls["n"] == 3, \
			"a --ref-prefixed say left the view stale"

		# The negatives stay negative under the new classifier: a
		# refused command with leading globals flushes nothing.
		console.execute(f"--op-id bar-3 close {target}")
		assert "rationale" in console.status
		console.rows()
		assert calls["n"] == 3, \
			"a refused global-prefixed command flushed the cache"

		# R7: an effectively-once REPLAY changes no storage — the exact
		# retry of bar-1 succeeds but schedules nothing.
		console.execute("--op-id bar-1 create --team lang --kind bug "
		                "--title protected-commit "
		                "--origin self-initiated --body fresh")
		assert console.status.startswith("ok")
		assert console.refresh_due is False, \
			"an operation replay scheduled a refresh"
		console.rows()
		assert calls["n"] == 3, "a replay flushed the cache"

		# R7: mark-seen — the first advance schedules, the already-seen
		# retry is a successful NO-OP and schedules nothing.
		last = pj_mod.thread(store, thread_id, viewer_team="lang",
		                     viewer_member="grace")["last_seq"]
		console.execute(f"mark-seen {thread_id} --up-to {last}")
		assert console.status.startswith("ok")
		assert console.refresh_due is True, \
			"the advancing mark-seen did not schedule"
		console.rows()
		assert calls["n"] == 4
		console.execute(f"mark-seen {thread_id} --up-to {last}")
		assert console.status.startswith("ok")
		assert console.refresh_due is False, \
			"an already-seen mark-seen scheduled a refresh"
		console.rows()
		assert calls["n"] == 4, "a no-op mark-seen flushed the cache"

		# R7, the direct-s path: prime the detail view on an
		# already-seen page — s reports "already seen" and schedules
		# nothing.
		console.mode = "detail"
		console.detail_work = target
		console.focus = "msgs"
		console.viewed_thread = thread_id
		console.viewed_last_seq = last
		console.handle(ord("s"))
		assert console.status == "already seen"
		assert console.refresh_due is False, \
			"an already-seen direct s scheduled a refresh"
	finally:
		pj_mod.tree = real_tree
	store.close()


@pytest.mark.parametrize("value", ["inf", "nan", "1e9"])
def test_unusable_intervals_refuse_before_curses(world, value):
	"""R3: non-finite or unrepresentable intervals refuse with the JSON
	contract before curses claims the screen."""
	import subprocess
	src = os.path.join(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__)))), "src")
	env = dict(os.environ, PYTHONPATH=src)
	proc = subprocess.run(
		[sys.executable, "-m", "baton_work.cli", "--config",
		 world["config"], "--participant", "lang.ada", "tui",
		 "--refresh", value],
		capture_output=True, text=True, timeout=120, env=env)
	assert proc.returncode == 1
	assert "finite positive" in proc.stderr
	assert "\x1b[?1049h" not in proc.stdout, \
		"curses claimed the screen before the refusal"
