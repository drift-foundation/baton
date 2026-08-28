"""B2: same-fixture semantic parity — ONE authority state, both surfaces.

The pinned ruling verbatim: feed one authority state through the shared
projection and prove that TUI-visible rows, counts, drill relationships and
actionable state agree with the JSON result. One fixture (`fixtures.build`),
one JSON read per claim, one real-pty screen per claim, and the comparison is
value-by-value — not two suites that happen to be green.

The TUI's fixed column layout is imported from the app, not restated: a
column-width change must move the parser with it or this suite fails, which
is the coupling the parity requirement wants.
"""

from __future__ import annotations

import json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui import app                                # noqa: E402
from baton_work.tui.app import COLUMNS                        # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")

WIDTH, HEIGHT = 110, 32


@pytest.fixture(scope="module")
def world(tmp_path_factory):
	directory = tmp_path_factory.mktemp("fixture")
	cast = fixtures.build(str(directory / "work.sqlite3"))
	return cast["config_path"], cast


def _json(capsys, path, *argv, viewer):
	code = cli.main(["--config", path, "--participant", viewer] + list(argv))
	captured = capsys.readouterr()
	assert code == 0, captured.err
	return json.loads(captured.out)["result"]


def _parse_rows(screen: list[str], width: int = WIDTH) -> list[dict]:
	"""TUI table rows, decoded by the APP'S OWN responsive column budget.
	W4: the leading Id column's width comes from the painted header —
	the same source of truth the human reads."""
	header = next(line for line in screen if "Title" in line)
	id_width = header.index("Title") - 1
	# W73: whether the Out column is in the budget is a property of the
	# VIEW, and the painted header is where this parser already reads
	# such facts from — the same source of truth the human uses, so the
	# decode cannot drift from what was drawn.
	terminal = "Out" in header
	# W93: read the drawn columns from the PAINTED HEADER rather than
	# recomputing them. The console's budget carries the Id column AND
	# the optional Wait cue, and this parser was passing only the Id —
	# a divergence that stayed invisible until a width where the two
	# answers differed. The header is the same source of truth this
	# parser already uses for `Out` and `Wait`, and it cannot drift from
	# what the human saw.
	drawn = {app.HEADER_LABELS.get(name, name.capitalize()): (name, size)
	         for name, size in app.COLUMNS}
	# COLUMNS order is the drawing order; the header decides membership.
	painted_labels = set(header.split())
	columns = [(name, size) for name, size in app.COLUMNS
	           if app.HEADER_LABELS.get(name, name.capitalize())
	           in painted_labels]
	fixed = sum(col_width for _n, col_width in columns) + len(columns)
	# W39/W187: the optional Wait (dependency-cue) field sits between
	# Title and the fixed columns; its width falls out of the header
	# the app itself painted.
	blk_at = header.index("Wait") if "Wait" in header else None
	# W26328: and the mandatory `Mine` field, read the same way. It sits
	# between the cue and the fixed columns, so a parser that did not
	# know about it would read its cells as part of `Wait` — which is
	# exactly the drift the header-driven decode exists to prevent.
	mine_at = header.index("Mine") if "Mine" in header else None
	tail_at = width - 1 - fixed          # where the fixed columns begin
	mine_width = (tail_at - mine_at) if mine_at is not None else 0
	if blk_at is not None:
		cue_width = (mine_at - 1 if mine_at is not None
		             else tail_at) - blk_at
	else:
		cue_width = 0
	leading = [at for at in (blk_at, mine_at) if at is not None]
	if leading:
		title_width = min(leading) - id_width - 2
	else:
		title_width = max(app.MIN_TITLE, width - fixed - id_width - 2)
	rows = []
	for line in screen[2:]:
		# W71: the table ends at the footer/help, a pane header, or a
		# blank; tree rows may be ↳-indented children.
		# W6814 renamed the Jobs footer's first cell when Enter became
		# ordinary activation. The break is on the footer's stable
		# `Enter ` PREFIX rather than one wording of it: an Id column
		# leads every table row, so no row can start with that word,
		# and the next rewording of the help text is not a parity
		# failure.
		if line.startswith(("Msgs", "Enter ", "»Threads",
		                    " Threads")):
			break
		if not line.strip() or line.startswith("("):
			continue
		line = line.ljust(width)          # replay rstrips; offsets are fixed
		local_id = line[:id_width].strip()
		cue = line[blk_at:blk_at + cue_width].strip() \
			if blk_at is not None else ""
		rest_at = tail_at if (blk_at is not None or mine_at is not None) \
			else id_width + 1 + title_width
		mine = line[mine_at:mine_at + mine_width].strip() \
			if mine_at is not None else ""
		rest = line[rest_at:]
		line = line[id_width + 1:]
		raw_title = line[:title_width].rstrip()
		# W154: the Title cell is reserved STRUCTURE then the
		# truncatable title — `↳ ` for a containment child and `▸N ` for
		# hidden deeper Work, both ahead of the text. Parsing them off
		# the front is now the only way to read the title, which is the
		# point: neither symbol can be truncated away by a long title.
		# W155 R3: depth is decoded from the INDENT, not from a single
		# `↳ ` prefix. The old rule mapped everything that was not
		# exactly `↳ `-prefixed to depth 0, so a depth-2 row read as a
		# ROOT — a parity parser silently disagreeing with the JSON
		# about containment, which is the concrete reason that window
		# change was a breaking one.
		marker = raw_title.find("↳ ")
		if marker < 0:
			depth, clean = 0, raw_title
		else:
			depth = marker // 2 + 1
			clean = raw_title[marker + 2:]
		if clean.startswith("▸"):
			clean = clean.split(" ", 1)[1] if " " in clean else ""
		cells = {"title": clean, "depth": depth,
		         "local_id": local_id, "cue": cue, "mine": mine}
		offset = 0
		for name, col_width in columns:
			cells[name] = rest[offset + 1:offset + 1 + col_width].strip()
			offset += 1 + col_width
		# W2938 removed the `New` column from Jobs and added no
		# replacement, so the row-shape sanity check moves to a cell
		# every row must carry: HANDLER is `-` or a participant, never
		# blank, and it is the column this suite most cares about.
		assert cells["HANDLER"], f"unparseable row: {line!r}"
		# W245: ROUTE (eligible endpoint) and CURRENT (exact claimant)
		# are separate columns, so parity checks them separately.
		parsed = {"title": cells["title"], "depth": cells["depth"],
		          # W155 R3: identity is part of parity. It was computed
		          # and then dropped, so nothing could compare the two
		          # surfaces row FOR row — only field by field in an
		          # order both happened to agree on.
		          "local_id": cells["local_id"],
		          # W26328: what the operator can act on, ABSENT in a
		          # view that draws no such column.
		          "mine": cells.get("mine"),
		          # W73: `-` for an open row, the compact outcome for a
		          # terminal one, and ABSENT entirely in an open-only
		          # view that has no such column.
		          "outcome": cells.get("OUT"),
		          "route": None if cells.get("ENDPOINT", "-") == "-"
		          else cells["ENDPOINT"],
		          "handler": None if cells["HANDLER"] == "-"
		          else cells["HANDLER"],
		          "next": None if cells["NEXT"] == "-" else cells["NEXT"]}
		for key, name in (("phase", "PHASE"), ("classification", "CLS"),
		                  ("msg_my", "MSG/MY")):
			if name in cells:
				parsed[key] = cells[name]
		rows.append(parsed)
	return rows


def _screen_rows(path, viewer, script=()):
	text, status, steps = ptyharness.drive(
		path, viewer, list(script) + [(b"qy", 0.4)],
		columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	rendered = steps[-2] if len(steps) > 1 else text
	return ptyharness.replay(rendered, columns=WIDTH, lines=HEIGHT)


def test_home_rows_agree_value_by_value(world, capsys):
	path, _cast = world
	for viewer in ("lang.ada", "lang.grace", "push.sl", "web.wren"):
		# W71 R3: ONE canonical tree-window projection — the very result
		# the TUI paints, not a composition the test repeats from
		# separate reads.
		window = _json(capsys, path, "tree", viewer=viewer)
		expected = window["rows"]
		# The projection's own token is hoisted into the envelope
		# (established contract); the result keeps rows + summary.
		assert "summary" in window
		screen = _screen_rows(path, viewer)
		drawn = _parse_rows(screen)
		assert len(drawn) == len(expected), \
			f"{viewer}: {len(drawn)} drawn vs {len(expected)} projected"
		for drawn_row, json_row in zip(drawn, expected):
			assert drawn_row["title"] == json_row["title"][:len(drawn_row["title"])]
			# W71 R3: the indentation depth itself is projected, not
			# reconstructed client-side.
			assert drawn_row["depth"] == json_row["depth"]
			# W26328: the Mine cell is the two projected facts and
			# nothing the console decided for itself. Both surfaces
			# answer the same question, so a console that computed its
			# own claimability would show it here.
			assert drawn_row["mine"] == app.mine_cell(json_row), \
				(viewer, json_row["id"], drawn_row["mine"])
			# W73: Out formats the canonical outcome, and `-` while
			# open. In an open-only view the column is not drawn at
			# all, and parity is that BOTH surfaces agree it is absent
			# — the projection's status is still `open` for every row.
			if drawn_row["outcome"] is None:
				assert json_row["status"] == "open", json_row
			else:
				assert drawn_row["outcome"] == app.outcome_cell(json_row)
			# WS-1 parity: the TUI draws the approved COMPACT vocabulary
			# for the canonical JSON values, presentation-only.
			# HISTORY, not current behaviour: W226 painted a pickup
			# prefix in this cell and W65 made it the primary unclaimed
			# cue. W15 removed both, because projection 8's `Current`
			# already states the claimant and is blank when there is
			# none.
			#
			# The `lstrip` below is deliberate belt-and-braces: it would
			# TOLERATE a marker rather than assert one, so the value
			# check keeps working on the compact vocabulary alone and
			# the assertion after it is what actually forbids a marker
			# from coming back.
			# W93: a column the layout omitted at this width has nothing
			# to compare. Parity is between what was DRAWN and the JSON,
			# so an absent column is skipped rather than asserted into a
			# KeyError — the omission itself is the responsive-width
			# suite's subject, not this one's.
			if "phase" in drawn_row:
				assert drawn_row["phase"].lstrip("> !") == app.phase_cell(
					json_row["status"], json_row["phase"]).strip()
				assert not drawn_row["phase"].startswith((">", "!")), \
					(drawn_row["phase"], json_row.get("pickup"))
				assert "!" not in drawn_row["phase"], \
					(drawn_row["phase"], json_row.get("pickup"))
			if "classification" in drawn_row:
				assert drawn_row["classification"] == \
					app.compact_classification(json_row["classification"])
			# W71: Prog/Dep left the table; the canonical row still
			# carries progress and the explicit live graph fields.
			assert "progress" in json_row
			assert "open_blockers" in json_row
			assert "open_dependents" in json_row
			assert "dep" not in json_row, \
				"the ambiguous dep field survived"
			# W36 parity: the compact pair is exactly the two canonical
			# fields, combined in the TUI alone.
			assert drawn_row["msg_my"] == (
				f"{json_row['message_count']}"
				f"/{json_row['my_pending_obligations']}")
			# W39: Ready is no longer painted — the dependency cue
			# carries the gate's identity instead (own parity suite).
			expected_route = (json_row["route"] or {}).get("endpoint")
			expected_next = (json_row["next"] or {}).get("endpoint")
			assert drawn_row["route"] == expected_route
			assert drawn_row["next"] == expected_next
			# W245: the claimant column is the one that must read `-`
			# when nobody holds the Work — the whole point of the split.
			expected_current = (json_row["handler"] or {}).get("participant")
			assert drawn_row["handler"] == expected_current, \
				f"TUI Handler {drawn_row['handler']!r} disagrees with " \
				f"JSON {expected_current!r} on {json_row['title']!r}"
			# W2938: the Jobs list no longer paints personal New, and
			# adds no per-Job pickup cue in its place — pickup is a
			# PARTICIPANT obligation and lives on Teams. So there is no
			# per-row field left here whose parity this loop can ask
			# about beyond the identity and workflow cells above.


def test_containment_children_agree_inline(world, capsys):
	"""W71: the ↳ children under a root are exactly the JSON children,
	in order, at depth 1 — no drill required."""
	path, cast = world
	expected = [row for row in
	            _json(capsys, path, "tree", f"work={cast["lang42"]}",
	                  viewer="lang.grace")["rows"] if row["depth"] == 1]
	screen = _screen_rows(path, "lang.grace")
	drawn = [row for row in _parse_rows(screen) if row["depth"] == 1]
	# W78: the parent's `Wait` cell now names its displayed child gate,
	# which widens the cue column; the title absorbs the remainder and
	# is the one column that truncates. Parity is about the two surfaces
	# agreeing on the SAME rows in the same order, so the drawn title is
	# compared as the prefix it is — the identity beside it is never
	# abbreviated and is checked whole below.
	for drawn_row, json_row in zip(drawn, expected):
		assert json_row["title"].startswith(drawn_row["title"].rstrip()), \
			f"{drawn_row['title']!r} is not a prefix of {json_row['title']!r}"
	assert len(drawn) >= len(expected)
	for drawn_row, json_row in zip(drawn, expected):
		assert drawn_row["next"] == (json_row["next"] or {}).get("endpoint")


def test_actionable_state_agrees(world, capsys):
	"""The owed count on the TUI's own header equals the JSON — `@` is
	actionable, `+` never is, on both surfaces.

	W25 moved WHERE that count is painted: the retired `[oblig:N]`
	counter became the Inbox tab's `total/unseen`, which aggregates
	obligations with pokes and unseen attention. The parity question is
	unchanged and is asked here against the `inbox` projection the tab
	is drawn from, with the obligation half still checked against
	`obligations` so the aggregate cannot hide a disagreement."""
	path, _cast = world
	for viewer, team in (("push.sl", "push"), ("web.wren", "web"),
	                     ("mdb.mo", "mdb")):
		expected = _json(capsys, path, "obligations", viewer=viewer)
		box = _json(capsys, path, "inbox", viewer=viewer)
		screen = _screen_rows(path, viewer)
		header = screen[0]
		# W167: the tab shows one owed-action marker instead of the
		# counts. Parity is still parity — the console and the JSON
		# must agree about whether this viewer owes anything.
		assert ("[Inbox *]" in header) is box["owed_action"], \
			f"{viewer}: header {header!r} vs {box}"
		owed = [row for row in box["rows"]
		        if row["kind"] == "obligation"]
		assert len(owed) == len(expected), (viewer, owed, expected)


def test_a_seen_transition_moves_both_surfaces_identically(world, capsys):
	"""One mark_seen through the CONSOLE, then both surfaces re-read: the
	same fixture keeps agreeing after a mutation, not only in its initial
	state."""
	path, cast = world
	before = _json(capsys, path, "new", f"work={cast["lang42"]}", viewer="lang.grace")
	assert before["subtree_total"] > 0
	# grace drills into the epic and marks the epic's own thread seen.
	text, status, _steps = ptyharness.drive(path, "lang.grace", [
		# W6814: the epic has children, so Enter roots at it; `]` opens
		# that same Work's Messages tab, which is what this case marks
		# seen. The keys after it are unchanged.
		(b"\r]", 0.5),       # drill: the epic's own Messages
		(b"o", 0.5),         # the focused view + thread set
		(b"\r", 0.5),        # open the epic's own thread
		(b"", 0.4),          # W2597: entry already focuses the index
		# W76: newest-first entry already selects the LAST message, so
		# no walk is needed to mark the whole thread seen.
		(b"s", 0.5),         # seen through the selected (newest) message
		(b"qy", 0.4),
	], columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	after = _json(capsys, path, "new", f"work={cast["lang42"]}", viewer="lang.grace")
	assert after["own"] == 0, "the console's s did not commit the cursor"
	assert after["subtree_total"] == before["subtree_total"] - before["own"], \
		"the decomposition moved by a different amount than own"
	# ...and the canonical read agrees. W2938 removed the Jobs `New`
	# cell, so this no longer has a list column to compare against; the
	# personal count is still canonical and is still painted where it
	# drives action, which the Inbox and thread suites assert.
	screen = _screen_rows(path, "lang.grace")
	assert _parse_rows(screen), "the table stopped painting rows"


def _local(work_id):
	return work_id.split("-")[-1]


def test_the_parked_summary_agrees_from_one_snapshot(world, capsys):
	"""WS-1 R3: the parked count the TUI paints and the JSON home summary
	are the SAME projection — park one work, both surfaces move together."""
	path, cast = world
	import baton_work as bw
	from baton_work import transitions as tr
	database = os.path.join(os.path.dirname(path), "work.sqlite3")
	with bw.Authority(database) as store:
		# W38 R1: park a LEAF. Work with open children is `block`,
		# and block leaves only through its condition-bound wake.
		leaf = tr.create_work(store, team="push", kind="bug",
		                      title="parkable leaf",
		                      origin="self-initiated",
		                      classification="suspected-defect",
		                      author="sl", body="b")["work_id"]
		tr.set_phase(store, leaf, actor_team="push", actor="sl",
		             phase="parked", reason="parity checkpoint")
	try:
		home = _json(capsys, path, "home", viewer="push.sl")
		assert home["summary"]["parked"] == 1
		screen = _screen_rows(path, "push.sl")
		# W25 retired the header's parked counter: parked Work stays
		# visible and filterable in Jobs, and duplicating it in a
		# global header was ruled noise. The JSON summary above is
		# still the canonical count, and the row itself is still on
		# the Jobs table, which is what parity now means here.
		assert "[park:" not in screen[0], \
			f"the retired parked counter came back: {screen[0]!r}"
		# W2938 changed which columns the responsive layout keeps, and
		# the Title is the one column it may truncate — so the row is
		# located by the Id, which is identity and is never
		# abbreviated, with the drawn title checked as the prefix it
		# is. Same rule the containment parity above already follows.
		row = next((line for line in screen
		            if line.startswith(f"{_local(leaf)} ")), None)
		assert row is not None, screen
		drawn_title = row.split(None, 1)[1][:len("parkable leaf")].strip()
		assert "parkable leaf".startswith(drawn_title), row
	finally:
		with bw.Authority(database) as store:
			tr.set_phase(store, leaf, actor_team="push",
			             actor="sl", phase="queued")


def test_the_round_line_agrees_with_the_canonical_projection(
		tmp_path, capsys, monkeypatch):
	"""WS-2 group 3 bounded parity: the compact trial line distinguishes
	due/pending/reported/withdrawn and shows the raw observation SEPARATELY
	from the reviewer's assessment — every value from the same canonical
	projection the JSON agent reads."""
	import fixtures as fx
	from baton_work import transitions as tr
	import baton_work as bw
	spec = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["verify"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["verify"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	monkeypatch.setenv("BATON_WORK_NOW", "2026-08-15T10:00:00Z")
	with bw.Authority(database) as store:
		work = tr.create_work(store, team="lang", kind="rsrch",
		                      title="parser recovery",
		                      origin="external-report", classification="suspected-defect", author="ada",
		                      body="provider")["work_id"]
		created = tr.create_trial(
			store, work, actor_team="lang", actor="ada",
			candidate="driftc-A", assign=["push.verify", "web.verify"],
			review_at="2026-08-15T12:00:00Z")
		tr.report(store, created["assignments"][0], team="push",
		          member="sl", observation="failed", evidence="crash")
		tr.assess(store, created["assignments"][0], actor_team="lang",
		          actor="ada", assessment="rejected",
		          rationale="consumer config error")
	monkeypatch.setenv("BATON_WORK_NOW", "2026-08-15T13:00:00Z")

	expected = _json(capsys, config_path, "detail", f"work={work}",
	                 viewer="lang.ada")["trials"][0]
	assert expected["due"] is True

	text, status, steps = ptyharness.drive(
		config_path, "lang.ada",
		[(b"\r", 0.5), (b"o", 0.6), (b"qy", 0.4)],
		columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	rendered = steps[-2] if len(steps) > 1 else text
	screen = ptyharness.replay(rendered, columns=WIDTH, lines=HEIGHT)
	joined = "\n".join(screen)
	round_line = (f"Trial {expected['trial']} {expected['candidate']} "
	              f"{expected['progress']} due "
	              f"wthdr:{expected['withdrawn']}")
	assert round_line in joined, \
		f"TUI trial line missing or wrong: {joined!r}"
	push_entry = next(entry for entry in expected["assignments"]
	                  if entry["endpoint"] == "push.verify")
	assert f"push.verify {push_entry['observation']}/" \
		f"{push_entry['effective_assessment']['assessment']}" in joined, \
		"raw observation and assessment are not shown as separate axes"
	assert "web.verify pending/-" in joined, \
		"a pending assignment is not distinguished"


def test_links_on_demand_agree_with_the_json_edges(world, capsys):
	"""Gate B: the `d` dependency view draws exactly the JSON `links`
	edges — same far Works, both directions, no extras.

	W4996 replaced the flat far-row list with the dependency
	NEIGHBOURHOOD graph, so the drawn CELLS are the ruled selector rather
	than a status/endpoint/title line. The parity this gate exists for is
	unchanged and is asserted on what both surfaces still name: the exact
	set of dependency edges around the Work, with duplicates and
	follow-ups deliberately outside this view.
	"""
	path, cast = world
	expected = _json(capsys, path, "links", f"work={cast["lang42"]}",
	                 viewer="lang.ada")
	screen = _screen_rows(path, "lang.ada", [(b"d", 0.5)])
	drawn = [line for line in screen[2:]
	         if "--blocks-->" in line]
	edges = expected["blocked_by"] + expected["blocks"]
	assert len(drawn) == len(edges), (drawn, edges)
	for entry in edges:
		local = entry["id"].split("-", 1)[1]
		assert any(f"[{local} " in line for line in drawn), \
			f"the graph does not draw the canonical edge to {entry['id']}"
	# The center is drawn too, and it is not one of the edge rows.
	center = cast["lang42"].split("-", 1)[1]
	assert any(line.strip().startswith(f"[{center} ") for line in screen[2:])


def test_collapsed_resolved_rows_agree_on_both_surfaces(tmp_path, capsys):
	"""Gate B: closed rows leave the DEFAULT table with an explicit hidden
	count, and `z` reveals exactly the JSON row set — the filter is
	presentation over the projection's own status."""
	import fixtures as fx
	from baton_work import transitions as tr
	import baton_work as bw
	spec = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	with bw.Authority(database) as store:
		tr.create_work(store, team="lang", kind="bug", title="stays open",
		               origin="external-report", classification="suspected-defect", author="ada", body="live")
		done = tr.create_work(store, team="lang", kind="bug",
		                      title="already done",
		                      origin="external-report", classification="suspected-defect", author="ada",
		                      body="old")["work_id"]
		tr.close_work(store, done, actor_team="lang", actor="ada",
		              rationale="delivered before the checkpoint",
		              outcome="satisfying")
	expected = _json(capsys, config_path, "home", viewer="lang.ada")["rows"]
	open_rows = [row for row in expected if row["status"] == "open"]
	assert len(open_rows) < len(expected)

	screen = _screen_rows(config_path, "lang.ada")
	drawn = _parse_rows(screen)
	assert [row["title"] for row in drawn] == \
		[row["title"] for row in open_rows]
	hidden = len(expected) - len(open_rows)
	assert any(f"({hidden} closed hidden" in line for line in screen), \
		"the collapse is silent about what it hides"

	revealed = _parse_rows(_screen_rows(config_path, "lang.ada",
	                                    [(b"z", 0.5)]))
	assert [row["title"] for row in revealed] == \
		[row["title"] for row in expected]
	closed_drawn = next(row for row in revealed
	                    if row["title"] == "already done")
	closed_json = next(row for row in expected
	                   if row["title"] == "already done")
	assert closed_drawn["outcome"] == app.outcome_cell(closed_json) == "sat"
	# and an open row in the SAME revealed view dashes its outcome
	# rather than borrowing the closed row's column meaning
	open_drawn = next(row for row in revealed
	                  if row["title"] != "already done")
	assert open_drawn["outcome"] == "-", open_drawn


def test_three_levels_agree_between_json_and_the_tui(tmp_path_factory,
                                                     capsys):
	"""W155 R3: the acceptance contract says canonical `tree` JSON and
	the TUI expose the SAME bounded window, and until now nothing
	compared them below depth 1.

	A root/child/grandchild/fourth-level chain is the case that matters:
	the fourth level must be absent from both surfaces, and its visible
	ancestor must disclose it on both. Identity, order, depth, title
	prefix and `deeper` are compared row by row — the parser that
	decodes this screen is the one W155's review found mapping a
	depth-2 row to a root.
	"""
	directory = tmp_path_factory.mktemp("threedeep")
	home = directory / "home"
	home.mkdir()
	config_path, database = fixtures.build_instance(
		str(home), {"lang": {"members": {"grace": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	made, parent = [], None
	for level in range(4):
		parent = tr.create_work(
			store, team="lang", kind="bug", title=f"level {level} work",
			origin="external-report" if level == 0 else "decomposition",
			classification="suspected-defect", author="grace", body="b",
			parent=parent)["work_id"]
		made.append(parent)
	store.close()

	expected = _json(capsys, config_path, "tree", viewer="lang.grace")["rows"]
	drawn = _parse_rows(_screen_rows(config_path, "lang.grace"))

	assert [row["id"] for row in expected] == made[:3], \
		"the JSON window is not the three-level chain"
	assert made[3] not in [row["id"] for row in expected], \
		"the fourth level reached the JSON window"
	assert len(drawn) == len(expected), \
		f"the surfaces disagree about how many rows: {drawn}"
	for drawn_row, json_row in zip(drawn, expected):
		assert drawn_row["local_id"] == json_row["local_id"], \
			f"row order differs: {drawn_row} vs {json_row}"
		assert drawn_row["depth"] == json_row["depth"], \
			(f"{json_row['local_id']} is depth {json_row['depth']} in JSON "
			 f"and {drawn_row['depth']} on screen")
		assert json_row["title"].startswith(drawn_row["title"].rstrip()), \
			f"{drawn_row['title']!r} is not a prefix of {json_row['title']!r}"
	# the disclosure is the same fact on both surfaces
	deepest = expected[-1]
	assert deepest["deeper"] is True, \
		"the JSON does not disclose the fourth level"
	assert not any(row["deeper"] for row in expected[:-1]), \
		"a row whose children are visible claims to hide Work"
	screen = _screen_rows(config_path, "lang.grace")
	marked = [line for line in screen if "▸" in line]
	assert len(marked) == 1, f"the screen disclosure is not one row: {marked}"
	assert deepest["local_id"] in marked[0], marked[0]
	assert "level 3 work" not in "\n".join(screen), \
		"the fourth level painted"
