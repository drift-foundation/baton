"""W336 (finding-tui-phase-blink-countdown-stall): the live render path
drains the three-cycle phase-change blink.

The confirmed defect: Console.render() read the table through view()
while the countdown lived only in rows(), so timer renders consumed the
refresh without spending a cycle and an armed blink persisted for
hours. The fix routes every table-shaped window — main, re-rooted,
search; render and key paths — through one countdown/observation
boundary. The decisive evidence is a REAL PTY timer/render loop.
"""

from __future__ import annotations

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(
	not hasattr(__import__("pty"), "fork"), reason="no pty support")

BLINK_PHASE = re.compile(
	r"\x1b\[(?:\d+;)*0?5(?:;\d+)*m(?:\x1b\[[0-9;?]*[A-Za-z])*\s*[>!]?"
	r"(actve|queue|rview|rsrch)")


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	work = tr.create_work(store, team="lang", kind="bug",
	                      title="blinker", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]
	store.close()
	return {"config": config, "database": database, "work": work}


def test_the_live_timer_render_loop_drains_the_blink(world):
	"""The PTY regression the acceptance demands: a genuine phase
	change observed by the running console blinks, and the blink is
	GONE after three successful scheduled refresh cycles — through the
	real timer -> render path, no interaction at all."""
	def flip_phase():
		store = bw.Authority(world["database"])
		try:
			tr.set_phase(store, world["work"], actor_team="lang",
			             actor="ada", phase="active")
		finally:
			store.close()

	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 1.0),                    # cold baseline paint
		("call", flip_phase, 2.6),     # mutate externally; 1 tick
		(b"", 2.6),                    # tick 2
		(b"", 2.6),                    # tick 3
		(b"", 2.6),                    # tick 4 — must be clean
		(b"", 2.6),                    # tick 5 — stays clean
		(b"qy", 0.5),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, \
		text[-400:]
	deltas = [steps[0]] + [steps[i][len(steps[i - 1]):]
	                       for i in range(1, len(steps))]
	# the cold load never blinks
	assert not BLINK_PHASE.search(deltas[0]), "the first table blinked"
	# the observed change arms the cue on the timer path
	armed = any(BLINK_PHASE.search(delta) for delta in deltas[1:3])
	assert armed, "the phase change never blinked on the live path"
	# after three successful scheduled cycles the cue is GONE — the
	# stalled-for-hours defect cannot reproduce
	assert not BLINK_PHASE.search(deltas[4]), \
		"the blink survived past three scheduled refreshes"
	assert not BLINK_PHASE.search(deltas[5]), \
		"the blink came back after draining"


def test_search_windows_share_the_countdown_boundary(world):
	"""Search renders spend the same owed cycle: an armed blink drains
	while the console sits in search mode."""
	store = bw.Authority(world["database"])
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.rows()                          # cold baseline
	tr.set_phase(store, world["work"], actor_team="lang",
	             actor="ada", phase="active")
	console.schedule_refresh()
	console.rows()                          # observe: arms 3
	assert console.phase_blink[world["work"]] == 3
	console.search_query = "blinker"
	console.mode = "search"
	for expected in (2, 1):
		console.tick()
		console.search_rows()
		assert console.phase_blink.get(world["work"], 0) == expected, \
			"a search window did not spend the owed cycle"
	console.tick()
	console.search_rows()
	assert world["work"] not in console.phase_blink
	store.close()
