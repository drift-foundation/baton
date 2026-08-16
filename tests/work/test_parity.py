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

from baton_work import cli                                    # noqa: E402
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
	"""TUI table rows, decoded by the APP'S OWN responsive column budget."""
	columns = app.visible_columns(width)
	fixed = sum(col_width for _n, col_width in columns) + len(columns)
	title_width = max(app.MIN_TITLE, width - fixed - 1)
	rows = []
	for line in screen[2:]:
		# W71: the table ends at the footer/help, a pane header, or a
		# blank; tree rows may be ↳-indented children.
		if line.startswith(("Msgs", "Enter details", "»Threads",
		                    " Threads")):
			break
		if not line.strip() or line.startswith("("):
			continue
		line = line.ljust(width)          # replay rstrips; offsets are fixed
		raw_title = line[:title_width].rstrip()
		depth = 1 if raw_title.startswith("↳ ") else 0
		clean = raw_title[2:] if depth else raw_title
		clean = clean.split(" ▸")[0]
		cells = {"title": clean, "depth": depth}
		rest = line[title_width:]
		offset = 0
		for name, col_width in columns:
			cells[name] = rest[offset + 1:offset + 1 + col_width].strip()
			offset += 1 + col_width
		assert cells["NEW"].isdigit(), \
			f"unparseable row (NEW={cells.get('NEW')!r}): {line!r}"
		parsed = {"title": cells["title"], "depth": cells["depth"],
		          "status": cells["ST"],
		          "ready": cells["READY"] == "yes",
		          "current": None if cells["CURRENT"] == "-"
		          else cells["CURRENT"],
		          "next": None if cells["NEXT"] == "-" else cells["NEXT"],
		          "new": int(cells["NEW"])}
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
			# Gate B: ST formats the canonical status and, when closed,
			# the canonical outcome — the same closed compact map.
			assert drawn_row["status"] == app.status_cell(json_row)
			# WS-1 parity: the TUI draws the approved COMPACT vocabulary
			# for the canonical JSON values, presentation-only.
			assert drawn_row["phase"] == app.phase_cell(
				json_row["status"], json_row["phase"])
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
			assert drawn_row["ready"] == json_row["ready"]
			expected_current = (json_row["current"] or {}).get("endpoint")
			expected_next = (json_row["next"] or {}).get("endpoint")
			assert drawn_row["current"] == expected_current
			assert drawn_row["next"] == expected_next
			assert drawn_row["new"] == json_row["new"], \
				f"{viewer} New disagrees on {json_row['title']!r}: " \
				f"TUI {drawn_row['new']} vs JSON {json_row['new']}"


def test_containment_children_agree_inline(world, capsys):
	"""W71: the ↳ children under a root are exactly the JSON children,
	in order, at depth 1 — no drill required."""
	path, cast = world
	expected = [row for row in
	            _json(capsys, path, "tree", f"work={cast["lang42"]}",
	                  viewer="lang.grace")["rows"] if row["depth"] == 1]
	screen = _screen_rows(path, "lang.grace")
	drawn = [row for row in _parse_rows(screen) if row["depth"] == 1]
	assert [row["title"] for row in drawn][:len(expected)] == \
		[row["title"] for row in expected]
	for drawn_row, json_row in zip(drawn, expected):
		assert drawn_row["new"] == json_row["new"]
		assert drawn_row["next"] == (json_row["next"] or {}).get("endpoint")


def test_actionable_state_agrees(world, capsys):
	"""The obligation count on the TUI's own header equals the JSON
	actionable list — `@` is actionable, `+` never is, on both surfaces."""
	path, _cast = world
	for viewer, team in (("push.sl", "push"), ("web.wren", "web"),
	                     ("mdb.mo", "mdb")):
		expected = _json(capsys, path, "obligations", viewer=viewer)
		screen = _screen_rows(path, viewer)
		header = screen[0]
		assert f"[oblig:{len(expected)}]" in header, \
			f"{viewer}: header {header!r} vs {len(expected)} obligations"


def test_a_seen_transition_moves_both_surfaces_identically(world, capsys):
	"""One mark_seen through the CONSOLE, then both surfaces re-read: the
	same fixture keeps agreeing after a mutation, not only in its initial
	state."""
	path, cast = world
	before = _json(capsys, path, "new", f"work={cast["lang42"]}", viewer="lang.grace")
	assert before["total"] > 0
	# grace drills into the epic and marks the epic's own thread seen.
	text, status, _steps = ptyharness.drive(path, "lang.grace", [
		(b"\r", 0.5),        # drill: path = [lang42]
		(b"o", 0.5),         # the focused view + thread set
		(b"\r", 0.5),        # open the epic's own thread
		(b"s", 0.5),         # THE explicit seen transition
		(b"qy", 0.4),
	], columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	after = _json(capsys, path, "new", f"work={cast["lang42"]}", viewer="lang.grace")
	assert after["own"] == 0, "the console's s did not commit the cursor"
	assert after["total"] == before["total"] - before["own"], \
		"the decomposition moved by a different amount than own"
	# ...and the TUI's home row shows the same reduced number.
	screen = _screen_rows(path, "lang.grace")
	drawn = _parse_rows(screen)
	assert drawn[0]["new"] == after["total"]


def test_the_parked_summary_agrees_from_one_snapshot(world, capsys):
	"""WS-1 R3: the parked count the TUI paints and the JSON home summary
	are the SAME projection — park one work, both surfaces move together."""
	path, cast = world
	import baton_work as bw
	from baton_work import transitions as tr
	database = os.path.join(os.path.dirname(path), "work.sqlite3")
	with bw.Authority(database) as store:
		tr.set_phase(store, cast["pushcoin"], actor_team="push", actor="sl",
		             phase="parked", reason="parity checkpoint")
	try:
		home = _json(capsys, path, "home", viewer="push.sl")
		assert home["summary"]["parked"] == 1
		screen = _screen_rows(path, "push.sl")
		assert "[park:1]" in screen[0], \
			f"TUI header {screen[0]!r} disagrees with the JSON summary"
	finally:
		with bw.Authority(database) as store:
			tr.set_phase(store, cast["pushcoin"], actor_team="push",
			             actor="sl", phase="queued")


def test_the_round_line_agrees_with_the_canonical_projection(
		tmp_path, capsys, monkeypatch):
	"""WS-2 group 3 bounded parity: the compact round line distinguishes
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
		created = tr.create_round(
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
	                 viewer="lang.ada")["rounds"][0]
	assert expected["due"] is True

	text, status, steps = ptyharness.drive(
		config_path, "lang.ada",
		[(b"\r", 0.5), (b"o", 0.6), (b"qy", 0.4)],
		columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	rendered = steps[-2] if len(steps) > 1 else text
	screen = ptyharness.replay(rendered, columns=WIDTH, lines=HEIGHT)
	joined = "\n".join(screen)
	round_line = (f"R{expected['round']} {expected['candidate']} "
	              f"{expected['progress']} due "
	              f"wthdr:{expected['withdrawn']}")
	assert round_line in joined, \
		f"TUI round line missing or wrong: {joined!r}"
	push_entry = next(entry for entry in expected["assignments"]
	                  if entry["endpoint"] == "push.verify")
	assert f"push.verify {push_entry['observation']}/" \
		f"{push_entry['effective_assessment']['assessment']}" in joined, \
		"raw observation and assessment are not shown as separate axes"
	assert "web.verify pending/-" in joined, \
		"a pending assignment is not distinguished"


def test_links_on_demand_agree_with_the_json_edges(world, capsys):
	"""Gate B: the `b` links view draws exactly the JSON `links` far-row
	summaries — same edges, same far status/endpoint/title, same order."""
	path, cast = world
	expected = _json(capsys, path, "links", f"work={cast["lang42"]}",
	                 viewer="lang.ada")
	screen = _screen_rows(path, "lang.ada", [(b"b", 0.5)])
	drawn = [line for line in screen[2:] if line.strip()
	         and not line.startswith("(")]
	blocks = expected["blocks"]
	assert len(drawn) == len(expected["blocked_by"]) + len(blocks)
	for line, entry in zip(drawn[len(expected["blocked_by"]):], blocks):
		endpoint = (entry["current"] or {}).get("endpoint") or "-"
		assert line == (f"blocks {entry['id']} {entry['team']} "
		                f"{entry['status']} {endpoint} "
		                f"{entry['title']}"), \
			f"links line disagrees: {line!r} vs {entry}"


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
	assert closed_drawn["status"] == app.status_cell(closed_json) == "c/sat"
