"""B1: the v11 console on a real terminal, against THE fixture.

Every assertion reads the reconstructed screen grid, not the byte stream.
The console under test is spawned as `baton-work ... tui` — the installed
entry, not an in-process shortcut — and never touches the authority except
through the shared surfaces (held by the boundary test).
"""

from __future__ import annotations

import os
import pty as _pty
import re
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
	text, status, _steps = ptyharness.drive(path, "lang.ada", [(b"qy", 0.4)])
	screen = ptyharness.replay(text)
	# W74: the root header is identity + live summary only — the
	# redundant "— top-level work" prose is gone.
	assert screen[0].startswith("lang.ada"), screen[0]
	assert "top-level work" not in screen[0]
	assert "[oblig:" in screen[0], "the live summary left the header"
	assert any("parser recovery" in line for line in screen), screen[:6]
	header = next(line for line in screen if "Title" in line)
	# Trial finding 26de18dd-W2: initial-capital header labels.
	# W71: Prog/Dep left the table — containment shows as indentation,
	# graph counts live in details/links.
	# W73: `St` is GONE from the default open-only table — every row in
	# it was `open`, which is a property of the view, not of a row.
	for column in ("Handler", "Next", "New"):
		assert column in header
	assert "St" not in header, \
		"the redundant State column survived in an open-only view"
	assert "Out" not in header, \
		"the terminal Outcome column appeared with no terminal rows in view"
	assert "Prog" not in header and "Dep " not in header
	assert "TITLE" not in header and "READY" not in header
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_tree_shows_children_inline_and_u_re_roots(world):
	"""W71/W155: the main screen is a three-level containment tree — children
	appear as ↳ rows under their roots without any drill; `u` re-roots
	the window at the selected Work with a real breadcrumb."""
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"", 0.5),                   # the root tree
		(b"u", 0.5),                  # re-root at the epic
		(b"qy", 0.4),
	])
	tree = ptyharness.replay(steps[0])
	# W78: the epic is gated by its own open children, so its `Wait`
	# cell now names the displayed child gate instead of sitting empty
	# beside a running clock. That widens the cue column at this
	# terminal width, and the title — the one column that absorbs the
	# remainder — takes the truncation, exactly as it does for any
	# other cue. The ↳ containment marker is a different fact and is
	# untouched, which is what this test is about.
	assert any("↳ confirm the de" in line for line in tree), \
		"children are not inline ↳ rows"
	assert any("↳ implement the" in line for line in tree)
	rooted = ptyharness.replay(steps[1])
	assert "parser recovery" in rooted[0], \
		f"the re-rooted breadcrumb is missing: {rooted[0]!r}"
	assert any("↳ confirm the de" in line for line in rooted)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_escape_climbs_back_up_the_drilled_path(world):
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"u", 0.5),
		(b"\x1b", 0.5),
		(b"qy", 0.4),
	])
	screen = ptyharness.replay(steps[1])
	# W74: the root view is recognized by the identity-led header with
	# no breadcrumb trail, not by the removed prose.
	assert screen[0].startswith("lang.ada") and ">" not in screen[0], \
		"escape did not return to the home table"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_thread_view_shows_the_timeline_and_planned_next(world):
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"j", 0.3), (b"j", 0.3),     # select ↳ step_fix in the tree
		(b"\r", 0.6),                 # Enter opens its DETAIL (W71)
		(b"\x17j", 0.4),              # W14: the Message index
		(b"j", 0.5),                  # W171: the pass left no message —
		                              # selection stays on the born body
		(b"qy", 0.4),
	])
	flat = "\n".join(ptyharness.replay(steps[2]))
	assert "next lang.rev" in flat, \
		f"the planned Next is not shown: {flat[:300]}"
	selected = "\n".join(ptyharness.replay(steps[4]))
	assert "after confirmation" in selected, \
		"the selected body is not drawn"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_marking_seen_is_explicit_and_reflected_in_new(world, tmp_path):
	"""The seen transition through the CONSOLE: grace opens the epic's
	thread, presses `s`, and the console's own status line reports the
	cursor. The count change is asserted in the parity suite via JSON —
	here the property is that VIEWING ALONE changed nothing."""
	path, cast = world
	# Viewing without pressing s: New must be unchanged afterwards.
	import baton_work as bw
	from baton_work import lifecycle as lc
	from baton_work import projection as pj
	store = lc.open_bound(path)
	before = pj.new_count(store, cast["lang42"], viewer_team="lang",
	                      viewer_member="grace")["subtree_total"]
	assert before > 0
	text, status, _steps = ptyharness.drive(path, "lang.grace", [
		(b"\r", 0.4), (b"\x1b", 0.3), (b"qy", 0.4),
	])
	after = pj.new_count(store, cast["lang42"], viewer_team="lang",
	                     viewer_member="grace")["subtree_total"]
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
	document["roots"] = {"pushcoin": {"display": "PushCoin monorepo", "base": "/srv/checkouts/pushcoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	from baton_work import lifecycle as lc
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(
		store, team="lang", kind="bug", title="portable facts",
		origin="external-report", classification="suspected-defect", author="ada", body="bound at birth",
		binding="pushcoin:work/records/2026/08/finding-tui")
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="ada", body="evidence",
	                   refs=[f"{born['work_id']}:repro/run.sh"])
	# The canonical JSON facts this parity checkpoint must mirror.
	detail = pj.detail(store, born["work_id"], viewer_team="lang",
	                   viewer_member="ada")
	json_binding = (f"{detail['binding']['root']}:"
	                f"{detail['binding']['path']}")
	message = pj.thread(store, born["thread"], viewer_team="lang",
	                    viewer_member="ada")["messages"][-1]
	json_reference = (f"{message['references'][0]['root']}:"
	                  f"{message['references'][0]['path']}")
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.6),                 # Enter opens the DETAIL (W71)
		# W76: the reference-carrying message is the newest, so it is
		# the entry selection
		(b"\x17j", 0.4),              # W14: the Message index
		(b"qy", 0.4),
	])
	flat = "\n".join(ptyharness.replay(steps[1]))
	assert f"binding {json_binding} r1" in flat, \
		f"the console does not render the binding: {flat[:300]}"
	assert "Refs:" in flat, "the Refs section is missing"
	assert f"[{json_reference}]" in flat, \
		"the console does not render the message references"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_a_narrow_terminal_omits_whole_columns_never_identities(world):
	"""Responsive omission (prototype under the ruling): at a narrow width
	whole low-priority columns disappear; the title keeps a working width
	and identities are never squeezed into ambiguity."""
	from baton_work.tui import app
	path, _cast = world
	# W39 removed the Ready column, so the budget tightens later: 68
	# is the first interesting narrow width now.
	narrow = 68
	columns = [name for name, _w in app.visible_columns(narrow)]
	assert "CLS" not in columns, "the lowest-priority column survived"
	# W73 freed the six cells `St` used, so more of the interesting
	# columns survive this width than before; the property is unchanged.
	assert {"ROUTE", "HANDLER", "NEXT", "NEW"} <= set(columns)
	text, status, _steps = ptyharness.drive(path, "lang.ada",
	                                        [(b"qy", 0.4)],
	                                        columns=narrow, lines=24)
	screen = ptyharness.replay(text, columns=narrow, lines=24)
	header = next(line for line in screen if "Title" in line)
	assert "Cat" not in header, \
		"the omitted category column left its header behind"
	assert "Handler" in header and "New" in header
	# The title keeps its working width (truncated, never squeezed away)
	# and the 6/6 identities are drawn whole.
	assert any("parser rec" in line for line in screen)
	assert any("lang.ada" in line for line in screen)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_links_are_on_demand_and_escape_returns(world):
	"""Blocking/dependent neighbors on demand (ruled): `b` on the selected
	row shows the far-row facts from the links projection; escape returns
	to the same table."""
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"b", 0.5),                  # links of the selected epic
		(b"\x1b", 0.5),               # back to the table
		(b"qy", 0.4),
	])
	screen = ptyharness.replay(steps[0])
	joined = "\n".join(screen)
	assert f"blocks {cast['pushcoin']} push open" in joined and \
		"checkout fails" in joined, \
		f"the dependent consumers are not drawn: {screen[2:8]}"
	assert f"blocks {cast['web']} web open" in joined
	assert f"blocks {cast['mdb']} mdb open" in joined
	back = ptyharness.replay(steps[1])
	assert any("Title" in line for line in back), \
		"escape did not return to the table"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_focused_facts_and_collapse_come_from_the_projection(tmp_path):
	"""Gate B: a closed Work leaves the default table (with an explicit
	hidden count), `z` reveals it showing the canonical outcome, and the
	focused view states outcome/rationale, the effective contract
	revision, and the typed waiting condition — every value canonical."""
	import json as _json

	import baton_work as bw
	from baton_work import transitions as tr
	from baton_work import lifecycle as lc

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	live = tr.create_work(store, team="lang", kind="bug",
	                      title="stays open", origin="external-report", classification="suspected-defect",
	                      author="ada", body="live")
	tr.claim_work(store, live["work_id"], actor_team="lang", actor="ada")
	promoted = tr.post_thread(
		store, live["thread"], author_team="lang", author="ada",
		body="the complete revised contract")
	tr.revise_work(store, live["work_id"], actor_team="lang",
	               actor="ada", message_seq=promoted["seq"],
	               expected_revision=0,
	               rationale="agreed at triage")
	done = tr.create_work(store, team="lang", kind="bug",
	                      title="already done", origin="external-report", classification="suspected-defect",
	                      author="ada", body="old")["work_id"]
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="delivered before the checkpoint",
	              outcome="satisfying")
	blocker = tr.create_work(store, team="lang", kind="bug",
	                         title="the gate", origin="external-report", classification="suspected-defect",
	                         author="ada", body="prereq")["work_id"]
	tr.add_dependency(store, live["work_id"], blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="test dependency")
	store.close()

	# Default: the closed row is collapsed and NAMED as hidden.
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"", 0.4),                   # the untouched default screen
		(b"z", 0.5),                  # reveal
		(b"qy", 0.4),
	])
	first = ptyharness.replay(steps[0])
	assert any("stays open" in line for line in first)
	assert not any("already done" in line for line in first), \
		"a closed row leaked into the default table"
	assert any("(1 closed hidden" in line for line in first), \
		"the collapse hid work silently"
	revealed = ptyharness.replay(steps[1])
	# W73: revealing terminal Work brings the Out column with it, and it
	# carries the outcome rather than the word `closed` the reveal
	# already implies.
	assert any("Out" in line for line in revealed), \
		"the Out column did not appear with the revealed closed row"
	assert any("already done" in line and "sat" in line
	           for line in revealed), \
		"the revealed closed row does not show the canonical outcome"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	# The focused view: contract revision on the open work; outcome and
	# rationale on the closed one.
	# W7: `the gate` is a ready unclaimed blocker and now leads the
	# pool, so `j` reaches `stays open` — the revised Work this
	# assertion has always been about.
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"j\r", 0.5), (b"o", 0.5), (b"qy", 0.4)])
	focused = "\n".join(ptyharness.replay(steps[1]))
	assert "contract rev r1" in focused, focused[:400]
	# W78: the focused row names the GATE, not the condition kind —
	# `wait W3` points at something an operator can open.
	assert re.search(r"wait W\d+", focused), \
		f"the displayed gate is not stated: {focused[:400]}"
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"z", 0.4), (b"jj", 0.3), (b"\r", 0.5), (b"o", 0.5),
		(b"qy", 0.4)])
	closed_view = "\n".join(ptyharness.replay(steps[3]))
	assert "closed satisfying — delivered before the checkpoint" \
		in closed_view, closed_view[:400]


@pytest.mark.parametrize("columns", [44, 56])
def test_the_responsive_column_budget_always_fits_the_terminal(columns):
	"""Dropping a column means dropping it whole. Even at the narrow
	prototype widths, the returned layout must fit before curses truncates a
	Current/Next identity or silently pushes New off screen."""
	from baton_work.tui import app
	visible = app.visible_columns(columns)
	fixed = sum(width for _name, width in visible) + len(visible)
	assert app.MIN_TITLE + fixed <= columns - 1, \
		f"the {columns}-cell layout still needs {app.MIN_TITLE + fixed + 1} cells"


def test_a_full_page_still_names_the_closed_rows_it_hides(tmp_path):
	"""Collapse may never become silent merely because open rows fill the
	viewport. The operator must still see the ruled hidden count."""
	import baton_work as bw
	from baton_work import transitions as tr

	spec = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fixtures.build_instance(str(tmp_path), spec)
	with bw.Authority(database) as store:
		for index in range(5):
			tr.create_work(store, team="lang", kind="bug",
			               title=f"open row {index}",
			               origin="self-initiated", classification="suspected-defect", author="ada", body="live")
		done = tr.create_work(store, team="lang", kind="bug",
		                      title="closed row", origin="self-initiated", classification="suspected-defect",
		                      author="ada", body="done")["work_id"]
		tr.close_work(store, done, actor_team="lang", actor="ada",
		              outcome="satisfying", rationale="complete")
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", [(b"", 0.4), (b"qy", 0.4)],
		columns=80, lines=8)
	screen = ptyharness.replay(steps[0], columns=80, lines=8)
	assert any("(1 closed hidden" in line for line in screen), screen
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_selection_scrolls_so_the_row_enter_will_open_is_visible(tmp_path):
	"""A cursor beyond the painted slice is an invisible destructive aim:
	Enter would drill into Work the human cannot see. Long tables must scroll
	or otherwise keep the selected row on screen."""
	import baton_work as bw
	from baton_work import transitions as tr

	spec = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fixtures.build_instance(str(tmp_path), spec)
	with bw.Authority(database) as store:
		for index in range(8):
			tr.create_work(store, team="lang", kind="bug",
			               title=f"row {index}", origin="self-initiated", classification="suspected-defect",
			               author="ada", body="live")
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", [(b"jjjjjj", 0.5), (b"qy", 0.4)],
		columns=80, lines=8)
	screen = ptyharness.replay(steps[0], columns=80, lines=8)
	assert any("row 6" in line for line in screen), screen
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_declared_transitions_stay_in_json_and_off_the_reading_surface(
		world):
	"""W90 supersedes the original form of this test.

	The principle it protected — a human must not discover authority by
	attempting invisible operations — survives in the canonical JSON,
	which still declares every transition for every client. What changed
	is WHERE the console renders it: `can: prioritize` sat directly above
	the Threads list, where it read as something you might do to the
	message you were looking at, when it is a capability of the Work open
	to any configured member of its owning team.

	There is no Work-actions surface in the console yet (the `o` view the
	module prose describes was superseded by W71's Enter-to-detail), so
	the reading surface simply omits it; that surface is where it should
	reappear."""
	from baton_work import lifecycle as lc
	from baton_work import projection as pj
	path, cast = world
	with lc.open_bound(path) as store:
		available = pj.detail(store, cast["lang42"], viewer_team="lang",
		                      viewer_member="ada")["available_transitions"]
	assert available, "the canonical projection stopped declaring authority"
	assert "prioritize" in available
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"\r", 0.5), (b"qy", 0.4)])
	screen = "\n".join(ptyharness.replay(steps[0]))
	assert "can:" not in screen, \
		f"the reading surface still renders Work capabilities: {screen[:500]}"
	assert "prioritize" not in screen, \
		f"a Work capability leaked onto the Messages surface: {screen[:500]}"
	# and the reading context itself is intact
	assert "Threads (" in screen and "Messages (" in screen, \
		f"removing the capability line cost reading context: {screen[:500]}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_command_bar_cannot_replace_the_validated_participant(tmp_path):
	"""C3 carries one validated participant context through reads and
	transitions. Re-entering a global --participant in the command bar must not
	turn a lang console into an identity-by-assertion push actor."""
	from baton_work import lifecycle as lc
	from baton_work import projection as pj

	spec = {
		"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
		"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	}
	config_path, _database = fixtures.build_instance(str(tmp_path), spec)
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b":--participant push.sl create --team push --kind bug "
		 b"--title impersonated --origin self-initiated --classification suspected-defect --body nope\n", 0.8),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	with lc.open_bound(config_path) as store:
		rows = pj.home(store, viewer_team="push", viewer_member="sl")["rows"]
	assert not any(row["title"] == "impersonated" for row in rows), \
		"the command bar replaced the console's validated participant"
	painted = "\n".join(ptyharness.replay(steps[0]))
	assert "participant" in painted or "global" in painted, \
		"the refused identity override was not explained"


def test_the_command_bar_cannot_abbreviate_a_participant_override(tmp_path):
	"""argparse accepts unambiguous long-option abbreviations by default.
	The fixed-session guard must cover the grammar the parser actually accepts,
	not only the full spelling of --participant."""
	from baton_work import lifecycle as lc
	from baton_work import projection as pj

	spec = {
		"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
		"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	}
	config_path, _database = fixtures.build_instance(str(tmp_path), spec)
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b":--part push.sl create --team push --kind bug "
		 b"--title abbreviated-impersonation --origin self-initiated --classification suspected-defect "
		 b"--body nope\n", 0.8),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	with lc.open_bound(config_path) as store:
		rows = pj.home(store, viewer_team="push", viewer_member="sl")["rows"]
	assert not any(row["title"] == "abbreviated-impersonation"
	               for row in rows), \
		"an argparse abbreviation replaced the validated participant"
	painted = "\n".join(ptyharness.replay(steps[0]))
	assert "participant" in painted or "global" in painted, \
		"the refused abbreviated identity override was not explained"


def test_links_drill_through_to_the_far_work(world):
	"""R105: the links view is NAVIGABLE — j selects among the far rows
	and Enter performs the deliberate cross-team drill-through, with the
	breadcrumb reconstructing the far Work's real position."""
	path, cast = world
	text, status, steps = ptyharness.drive(path, "lang.ada", [
		(b"b", 0.5),                  # links of the selected epic
		(b"j", 0.4),                  # select the second dependent (web)
		(b"\r", 0.5),                 # drill through
		(b"qy", 0.4),
	])
	screen = ptyharness.replay(steps[2])
	assert any("render crash" in line for line in screen[:1]), \
		f"the drill-through did not land on the far work: {screen[:3]}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_thread_selection_never_merges_timelines(tmp_path):
	"""R105: a Work with several labelled threads lists them
	selectably (ids, personal New); Enter opens exactly the chosen one —
	the other thread's messages never bleed in."""
	import json as _json

	import baton_work as bw
	from baton_work import lifecycle as lc
	from baton_work import transitions as tr

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="two threads", origin="external-report", classification="suspected-defect",
	                      author="ada", body="the born conversation")
	work = born["work_id"]
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="ada", body="first-thread evidence")
	second = tr.create_thread(store, actor_team="lang", actor="ada",
	                              body="second-thread opener",
	                              labels=[work], subject="trial subject")["thread"]
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.6),                 # Enter opens the DETAIL (W71)
		(b"j", 0.5),                  # Threads pane: select the SECOND
		(b"qy", 0.4),
	])
	listing = "\n".join(ptyharness.replay(steps[0]))
	assert "Threads (2)" in listing
	assert second in listing, "the second thread is not listed"
	switched = "\n".join(ptyharness.replay(steps[1]))
	assert "second-thread opener" in switched
	assert "first-thread evidence" not in switched, \
		"another thread's messages bled into the msgs pane"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_thread_set_pages_beyond_the_first_fifty(tmp_path):
	"""The canonical Work-threads read exposes continuation. A bounded
	TUI list must let the operator reach every page rather than silently making
	thread 51 and later inaccessible."""
	import json as _json

	import baton_work as bw
	from baton_work import lifecycle as lc
	from baton_work import transitions as tr

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="many threads", origin="external-report", classification="suspected-defect",
	                      author="ada", body="born")
	last = None
	for index in range(50):
		last = tr.create_thread(
			store, actor_team="lang", actor="ada",
			body=f"separate thread {index + 2}",
			labels=[born["work_id"]],
			subject="trial subject")["thread"]
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.4), (b"o", 0.4),
		(b"n" * 60, 0.8),             # advance through every bounded page
		(b"qy", 0.4),
	], lines=14)
	listing = "\n".join(ptyharness.replay(steps[2], lines=14))
	assert last in listing, \
		"the thread after the first 50 is unreachable from the TUI"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_thread_pages_are_bounded_and_navigable(tmp_path):
	"""R105 on W76's newest-first index: a long thread is read in
	BOUNDED pages through the canonical thread read — n moves to the
	OLDER page, p returns to the newest one, and the seen mark stays
	bounded by the PAINTED page."""
	import json as _json

	import baton_work as bw
	from baton_work import lifecycle as lc
	from baton_work import projection as pj
	from baton_work import transitions as tr

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="long talk", origin="external-report", classification="suspected-defect",
	                      author="ada", body="opener")
	for index in range(1, 25):
		tr.post_thread(store, born["thread"],
		                   author_team="lang", author="ada",
		                   body=f"message number {index:02d}")

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.6),                             # detail: first page
		(b"\x17j", 0.4),                           # Ctrl-W j: Msgs pane
		(b"n", 0.5),                               # the OLDER page
		(b"s", 0.5),                               # seen: PAGE-bounded
		(b"p", 0.5),                               # back to the newest
		(b"qy", 0.4),
	], lines=12)
	import re as _re

	def numbers(text):
		return {int(match) for match in
		        _re.findall(r"message number (\d+)", text)}

	# W76: the FIRST page is the newest one, so the thread's opener is
	# nowhere near it.
	first = "\n".join(ptyharness.replay(steps[0], lines=12))
	assert "message number 24" in first, \
		"the entry page is not the newest page"
	assert "opener" not in first, \
		"the newest page reached back to the thread's opener"
	assert "message number 01" not in first, \
		"the page is not bounded by the viewport"
	second = "\n".join(ptyharness.replay(steps[2], lines=12))
	assert "after #" not in second and "before #" not in second, \
		"the internal projection cursor leaked into the TUI (W71)"
	# Page two holds only messages OLDER than everything page one
	# painted — derived from the painted pages, not a hardcoded window,
	# so the bound survives formatting changes to lines-per-message.
	assert numbers(second), second[:400]
	assert max(numbers(second)) < min(numbers(first)), \
		"n did not page toward older messages"
	back = "\n".join(ptyharness.replay(steps[4], lines=12))
	assert "message number 24" in back, \
		"p did not return to the newest page"

	# The s pressed on the OLDER page marked only through that page's
	# selected message — newer messages stay New.
	new = pj.new_count(store, born["work_id"], viewer_team="lang",
	                   viewer_member="ada")["subtree_total"]
	assert new > 0, "the page-bounded seen marked the whole thread"
	store.close()
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_below_the_minimum_the_table_refuses_explicitly(world):
	"""R106: when even the core columns cannot fit with a working title,
	the table REFUSES with an explicit too-narrow line — identities are
	never truncated into ambiguity to fake a fit."""
	from baton_work.tui import app
	path, _cast = world
	# W73: dropping the six-cell St column moved this boundary down —
	# 30 now fits where it did not. The property under test is the
	# REFUSAL, so the width follows the budget.
	narrow = 28
	assert not app.layout_fits(narrow)
	text, status, _steps = ptyharness.drive(path, "lang.ada",
	                                        [(b"qy", 0.4)],
	                                        columns=narrow, lines=12)
	screen = ptyharness.replay(text, columns=narrow, lines=12)
	joined = "\n".join(screen)
	assert "too narrow" in joined, screen[:4]
	assert "parser rec" not in joined, \
		"rows were drawn despite the too-narrow refusal"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_thread_set_pages_beyond_one_full_page(tmp_path):
	"""R116: the thread SET itself is paged — a Work with more
	labelled threads than one page still reaches every one through
	`n` (the canonical continuation cursor) and returns with `p`."""
	import json as _json

	import baton_work as bw
	from baton_work.tui import app
	from baton_work import lifecycle as lc
	from baton_work import transitions as tr

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="many talks", origin="external-report", classification="suspected-defect",
	                      author="ada", body="opener")
	work = born["work_id"]
	extras = [tr.create_thread(store, actor_team="lang",
	                               actor="ada",
	                               body=f"topic {index:02d}",
	                               labels=[work], subject="trial subject")["thread"]
	          for index in range(app.DISC_PAGE + 2)]
	store.close()
	beyond = extras[app.DISC_PAGE:]

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.6),                 # detail: page one of the set
		(b"n", 0.5),                  # the continuation page
		(b"p", 0.5),                  # back to the start
		(b"qy", 0.4),
	])
	first = "\n".join(ptyharness.replay(steps[0]))
	assert f"Threads ({app.DISC_PAGE + 3})" in first
	assert "(n: more threads)" in first, \
		"the full page does not announce more"
	for extra in beyond:
		assert extra not in first, "page one leaked later threads"
	second = "\n".join(ptyharness.replay(steps[1]))
	for extra in beyond:
		assert extra in second, \
			"a thread beyond the first page is unreachable"
	back = "\n".join(ptyharness.replay(steps[2]))
	assert born["thread"] in back, "p did not return to the start"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_message_panes_are_role_labelled_not_content_repeating(tmp_path):
	"""W176 (superseding the W31 subject-repeating pin): the Thread row
	alone owns the subject; `Messages (total/unseen)` names the lower index,
	while the reader begins with its own `#N` metadata instead of a repeated
	`Message M…` heading. Several conversations are still never mistaken
	because SELECTION lives in the Thread rows."""
	import json as _json

	import baton_work as bw
	from baton_work import lifecycle as lc
	from baton_work import transitions as tr

	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="two conversations",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="opener")
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 body="second opener", labels=[born["work_id"]],
	                 subject="the follow-up questions")
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.6),                 # the detail: Threads + Msgs
		(b"j", 0.5),                  # select the SECOND thread
		(b"qy", 0.4),
	])
	listing = "\n".join(ptyharness.replay(steps[0]))
	assert "T2 two conversations" in listing, listing[:400]
	assert "T3 the follow-up questions" in listing
	msgs = "\n".join(ptyharness.replay(steps[1]))
	assert "Messages (1/" in msgs, msgs[:400]
	# W30: the reader heading is gone — its row now carries the
	# reader's own canonical metadata, so the selected identity is
	# stated once rather than three times.
	assert "Message M" not in msgs, "the redundant reader heading survived"
	assert "Msgs —" not in msgs, "the content-repeating heading survived"
	assert msgs.count("the follow-up questions") == 1, \
		"the subject leaked out of its Thread row"
	assert "second opener" in msgs
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_category_header_reads_cat_when_present(world):
	"""finding-tui-category-header: the classification column renders as
	`Cat` (presentation only; the canonical field and compact values are
	unchanged). At full width the header carries it; the narrow-width
	story above proves it disappears WHOLE when the column is omitted."""
	path, _cast = world
	text, status, _steps = ptyharness.drive(path, "lang.ada",
	                                        [(b"qy", 0.4)],
	                                        columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(text, columns=110, lines=24)
	header = next(line for line in screen if "Title" in line)
	assert "Cat" in header, "the ruled Cat label is missing"
	assert "Cls" not in header, "the superseded Cls label survived"


def test_a_confirmed_defect_renders_defct_on_the_real_console(world):
	"""W6 (ruled): the compact classification label for confirmed-defect
	is `defct` — presentation only, on a REAL PTY; canonical JSON keeps
	the full value."""
	path, cast = world
	import baton_work as _bw
	from baton_work import transitions as _tr
	store = _bw.Authority(os.path.join(os.path.dirname(path),
	                                   "work.sqlite3"))
	work = _tr.create_work(store, team="lang", kind="bug",
	                       title="a confirmed one",
	                       origin="external-report",
	                       classification="confirmed-defect",
	                       author="ada", body="b")["work_id"]
	store.close()
	text, status, _steps = ptyharness.drive(path, "lang.ada",
	                                        [(b"qy", 0.4)],
	                                        columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(text, columns=110, lines=24)
	row = next(line for line in screen if "a confirmed one" in line)
	assert "defct" in row, row
	assert "cnfrm" not in row
	from baton_work.tui.app import compact_classification
	assert compact_classification("confirmed-defect") == "defct"
	# The compact label is PRESENTATION only: canonical JSON keeps the
	# full classification value, pinned beside the drawn row.
	import json as _json
	from baton_work import projection as _pj
	store = _bw.Authority(os.path.join(os.path.dirname(path),
	                                   "work.sqlite3"))
	try:
		view = _pj.detail(store, work, viewer_team="lang",
		                  viewer_member="ada")
		assert view["classification"] == "confirmed-defect", \
			"the canonical JSON value drifted with the display label"
		assert "defct" not in _json.dumps(view), \
			"a compact display label leaked into canonical JSON"
	finally:
		store.close()


def test_q_asks_before_exit_and_cancellation_changes_nothing(world):
	"""W9 (ruled): normal-navigation q opens one bottom-row Exit? y/N
	prompt. n cancels to the unchanged view, an irrelevant key neither
	confirms nor cancels, Esc cancels, and y exits — with no authority
	or seen mutation from any of it."""
	import hashlib
	path, _cast = world
	database = os.path.join(os.path.dirname(path), "work.sqlite3")
	with open(database, "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	# q -> prompt; x (irrelevant) stays prompting; n cancels; the view
	# survives; q again; Esc cancels; q; y exits clean.
	text, status, steps = ptyharness.drive(
		path, "lang.ada",
		[(b"q", 0.3), (b"x", 0.3), (b"n", 0.3), (b"q", 0.3),
		 (b"\x1b", 0.3), (b"q", 0.3), (b"y", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	prompt = ptyharness.replay(steps[0], columns=110, lines=24)
	assert any("Exit? y/N" in line for line in prompt), prompt[-3:]
	still = ptyharness.replay(steps[1], columns=110, lines=24)
	assert any("Exit? y/N" in line for line in still), \
		"an irrelevant key dismissed or confirmed the prompt"
	cancelled = ptyharness.replay(steps[2], columns=110, lines=24)
	assert not any("Exit? y/N" in line for line in cancelled), \
		"n did not cancel the prompt"
	assert any("Title" in line for line in cancelled), \
		"cancellation lost the view"
	with open(database, "rb") as handle:
		after = hashlib.sha256(handle.read()).hexdigest()
	assert after == before, "the exit prompt mutated authority state"


def test_the_exit_prompt_is_exactly_one_row_wide_and_narrow(world):
	"""W9 R2: exactly ONE matching prompt row at both widths, and the
	uppercase halves of the key matrix behave: N cancels, Y exits."""
	path, _cast = world
	for columns in (110, 44):
		text, status, steps = ptyharness.drive(
			path, "lang.ada",
			[(b"q", 0.3), (b"N", 0.3), (b"q", 0.3), (b"Y", 0.4)],
			columns=columns, lines=24)
		assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, \
			f"uppercase Y did not exit at {columns} columns"
		prompt = ptyharness.replay(steps[0], columns=columns, lines=24)
		hits = [line for line in prompt if "Exit? y/N" in line]
		assert len(hits) == 1, (columns, hits)
		cancelled = ptyharness.replay(steps[1], columns=columns,
		                              lines=24)
		assert not any("Exit? y/N" in line for line in cancelled), \
			f"uppercase N did not cancel at {columns} columns"


def test_cancelling_the_prompt_keeps_the_visible_status(world):
	"""W9 R1: the prompt OVERLAYS the footer — a visible status line
	survives q + cancel exactly as it was."""
	path, _cast = world
	# A refused command produces a visible status; q then n must return
	# to that same status, not a cleared footer.
	script = [(b":", 0.2), (b"close nothing\r", 0.4),
	          (b"q", 0.3), (b"n", 0.3), (b"q", 0.3), (b"y", 0.4)]
	text, status, steps = ptyharness.drive(path, "lang.ada", script,
	                                       columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	with_status = ptyharness.replay(steps[1], columns=110, lines=24)
	visible = [line for line in with_status if line.strip()][-1]
	assert visible.strip(), "no status was produced to preserve"
	prompted = ptyharness.replay(steps[2], columns=110, lines=24)
	assert any("Exit? y/N" in line for line in prompted)
	cancelled = ptyharness.replay(steps[3], columns=110, lines=24)
	restored = [line for line in cancelled if line.strip()][-1]
	assert restored == visible, \
		f"cancellation lost the status: {visible!r} -> {restored!r}"


def test_command_bar_q_stays_literal(world):
	"""W9: text entry keeps q literal — typing a command containing q
	must not open the exit prompt."""
	path, _cast = world
	text, status, steps = ptyharness.drive(
		path, "lang.ada",
		[(b":", 0.3), (b"q", 0.3), (b"\x1b", 0.3), (b"q", 0.3),
		 (b"y", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	typing = ptyharness.replay(steps[1], columns=110, lines=24)
	assert any(line.startswith(":q") for line in typing), \
		"the command bar did not keep q literal"
	assert not any("Exit? y/N" in line for line in typing), \
		"typing q in the command bar opened the exit prompt"


def test_the_detail_header_leads_with_the_exact_work_id(tmp_path):
	"""W12 (ruled): the detail view exposes the selected Work's exact
	canonical id — LEADING the header row so narrow widths keep it
	whole, and following the SELECTION across duplicate titles."""
	import baton_work as _bw
	from baton_work import transitions as _tr
	import fixtures as _fx
	path, database = _fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = _bw.Authority(database)
	first = _tr.create_work(store, team="lang", kind="bug",
	                        title="the twin", origin="external-report",
	                        classification="suspected-defect",
	                        author="ada", body="a")["work_id"]
	second = _tr.create_work(store, team="lang", kind="bug",
	                         title="the twin", origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="b")["work_id"]
	store.close()
	# Open the FIRST twin's detail (row 0); then back out, move one
	# down, and open the SECOND — the shown id must follow the
	# selection, at a narrow supported width too.
	for columns in (110, 44):
		text, status, steps = ptyharness.drive(
			path, "lang.ada",
			[(b"", 0.3), (b"", 0.1), (b"\r", 0.4), (b"\x1b", 0.3),
			 (b"j", 0.2), (b"\r", 0.4), (b"q", 0.2), (b"y", 0.4)],
			columns=columns, lines=24)
		assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
		def header_row(screen):
			# The detail header is the row carrying the status block —
			# the ONE row the id must LEAD.
			return next(line for line in screen if "[open/" in line)

		opened_first = ptyharness.replay(steps[2], columns=columns,
		                                 lines=24)
		assert header_row(opened_first).startswith(first), \
			(columns, first, header_row(opened_first))
		opened_second = ptyharness.replay(steps[5], columns=columns,
		                                  lines=24)
		assert header_row(opened_second).startswith(second), \
			(columns, second, header_row(opened_second))
		assert not any(first in line for line in opened_second), \
			"the detail id did not follow the selection"
