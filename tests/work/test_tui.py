"""B1: the v11 console on a real terminal, against THE fixture.

Every assertion reads the reconstructed screen grid, not the byte stream.
The console under test is spawned as `baton-work ... tui` — the installed
entry, not an in-process shortcut — and never touches the authority except
through the shared surfaces (held by the boundary test).
"""

from __future__ import annotations

import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


@pytest.fixture(scope="module")
def world(tmp_path_factory):
	directory = tmp_path_factory.mktemp("fixture")
	cast = fixtures.build(str(directory / "work.sqlite3"))
	return cast["config_path"], cast


def test_the_console_opens_on_the_top_level_table_and_exits(world):
	path, cast = world
	text, status, _steps = ptyharness.drive(path, "lang.ada", [(b"q", 0.4)])
	screen = ptyharness.replay(text)
	assert any("top-level work" in line for line in screen)
	assert any("parser recovery" in line for line in screen), screen[:6]
	header = next(line for line in screen if "TITLE" in line)
	for column in ("ST", "READY", "CURRENT", "NEXT", "NEW"):
		assert column in header
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_enter_drills_and_the_breadcrumb_names_the_path(world):
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"\r", 0.5),                 # drill into the epic
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[0])
	assert any("parser recovery" in line and ">" not in line
	           for line in screen[:1]) or "parser recovery" in screen[0], \
		f"breadcrumb missing: {screen[0]!r}"
	assert any("confirm the defect" in line for line in screen), \
		"the child table is not drawn"
	assert any("implement the fix" in line for line in screen)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_escape_climbs_back_up_the_drilled_path(world):
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"\r", 0.5),
		(b"\x1b", 0.5),
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[1])
	assert any("top-level work" in line for line in screen[:1]), \
		"escape did not return to the home table"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_discussion_view_shows_the_timeline_and_planned_next(world):
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"\r", 0.5),                 # into the epic's children
		(b"j", 0.3),                  # select step_fix
		(b"\r", 0.5),                 # drill into it
		(b"o", 0.5),                  # open the discussion
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[3])
	assert any("next lang.rev" in line for line in screen), \
		f"the planned Next is not shown: {[l for l in screen if l][:6]}"
	assert any("take it" in line for line in screen), \
		"the discussion body is not drawn"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_marking_seen_is_explicit_and_reflected_in_new(world, tmp_path):
	"""The seen transition through the CONSOLE: grace opens the epic's
	discussion, presses `s`, and the console's own status line reports the
	cursor. The count change is asserted in the parity suite via JSON —
	here the property is that VIEWING ALONE changed nothing."""
	path, cast = world
	# Viewing without pressing s: New must be unchanged afterwards.
	import baton_work as bw
	from baton_work import lifecycle as lc
	from baton_work import projection as pj
	store = lc.open_bound(path)
	before = pj.new_count(store, cast["lang42"], viewer_team="lang",
	                      viewer_member="grace")["total"]
	assert before > 0
	text, status, _steps = ptyharness.drive(path, "lang.grace", [
		(b"\r", 0.4), (b"\x1b", 0.3), (b"q", 0.4),
	])
	after = pj.new_count(store, cast["lang42"], viewer_team="lang",
	                     viewer_member="grace")["total"]
	assert after == before, "viewing in the console changed New"
	store.close()
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_a_participant_the_config_does_not_know_refuses_before_curses(world):
	"""The Gate A gap, CLOSED BY THE CORRECTION (C3): the bound open
	validates the participant against the accepted configuration before
	curses claims the screen. This was the held xfail; the architecture the
	rulings chose flips it."""
	path, _cast = world
	text, status, _steps = ptyharness.drive(path, "ghost.gone", [(b"", 0.3)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 1
	assert "not a participant" in text, text[-300:]
	assert "\x1b[?1049h" not in text, \
		"curses claimed the screen before the refusal"


def test_the_binding_and_references_render_the_portable_facts(tmp_path):
	"""WS-6 R90: the SAME fixture serves the canonical JSON projection
	and the real-PTY console — the human sees the same portable
	root:path facts, with no resolver and no filesystem probe."""
	import json as _json

	import baton_work as bw
	from baton_work import projection as pj
	from baton_work import transitions as tr

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin monorepo"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	from baton_work import lifecycle as lc
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(
		store, team="lang", kind="bug", title="portable facts",
		origin="external-report", author="ada", body="bound at birth",
		binding="pushcoin:work/records/2026/08/finding-tui")
	tr.post_discussion(store, born["discussion"], author_team="lang",
	                   author="ada", body="evidence",
	                   refs=[f"{born['work_id']}:repro/run.sh"])
	# The canonical JSON facts this parity checkpoint must mirror.
	detail = pj.detail(store, born["work_id"], viewer_team="lang",
	                   viewer_member="ada")
	json_binding = (f"{detail['binding']['root']}:"
	                f"{detail['binding']['path']}")
	message = pj.thread(store, born["discussion"], viewer_team="lang",
	                    viewer_member="ada")["messages"][-1]
	json_reference = (f"{message['references'][0]['root']}:"
	                  f"{message['references'][0]['path']}")
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.5),                 # drill into the work
		(b"o", 0.5),                  # open the discussion view
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[1])
	flat = "\n".join(screen)
	assert f"binding {json_binding} r1" in flat, \
		f"the console does not render the binding: {screen[:6]}"
	assert f"[{json_reference}]" in flat, \
		"the console does not render the message references"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
