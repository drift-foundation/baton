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
from baton_work.tui.app import COLUMNS                        # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")

WIDTH, HEIGHT = 110, 32


@pytest.fixture(scope="module")
def world(tmp_path_factory):
	path = str(tmp_path_factory.mktemp("fixture") / "work.sqlite3")
	cast = fixtures.build(path)
	return path, cast


def _json(capsys, path, *argv, viewer):
	code = cli.main(["--authority", path, "--viewer", viewer] + list(argv))
	captured = capsys.readouterr()
	assert code == 0, captured.err
	return json.loads(captured.out)["result"]


def _parse_rows(screen: list[str]) -> list[dict]:
	"""TUI table rows, decoded by the APP'S OWN column budget."""
	fixed = sum(width for _n, width in COLUMNS) + len(COLUMNS)
	title_width = max(10, WIDTH - fixed - 1)
	rows = []
	for line in screen[2:]:
		if not line.strip() or line.startswith("("):
			continue
		line = line.ljust(WIDTH)          # replay rstrips; offsets are fixed
		title = line[:title_width].rstrip()
		rest = line[title_width:]
		values = []
		offset = 0
		for _name, width in COLUMNS:
			values.append(rest[offset + 1:offset + 1 + width].strip())
			offset += 1 + width
		status, ready, current, next_endpoint, new = values
		assert new.strip().isdigit(), \
			f"unparseable row (NEW={new!r}): {line!r}"
		rows.append({"title": title, "status": status,
		             "ready": ready == "yes",
		             "current": None if current == "-" else current,
		             "next": None if next_endpoint == "-" else next_endpoint,
		             "new": int(new)})
	return rows


def _screen_rows(path, viewer, script=()):
	text, status, steps = ptyharness.drive(
		path, viewer, list(script) + [(b"q", 0.4)],
		columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	rendered = steps[-2] if len(steps) > 1 else text
	return ptyharness.replay(rendered, columns=WIDTH, lines=HEIGHT)


def test_home_rows_agree_value_by_value(world, capsys):
	path, _cast = world
	for viewer in ("lang.ada", "lang.grace", "push.sl", "web.wren"):
		expected = _json(capsys, path, "home", viewer=viewer)
		screen = _screen_rows(path, viewer)
		drawn = _parse_rows(screen)
		assert len(drawn) == len(expected), \
			f"{viewer}: {len(drawn)} drawn vs {len(expected)} projected"
		for drawn_row, json_row in zip(drawn, expected):
			assert drawn_row["title"] == json_row["title"][:len(drawn_row["title"])]
			assert drawn_row["status"] == json_row["status"][:6]
			assert drawn_row["ready"] == json_row["ready"]
			assert drawn_row["current"] == json_row["current"]
			assert drawn_row["next"] == json_row["next"]
			assert drawn_row["new"] == json_row["new"], \
				f"{viewer} New disagrees on {json_row['title']!r}: " \
				f"TUI {drawn_row['new']} vs JSON {json_row['new']}"


def test_drill_relationships_agree(world, capsys):
	"""The children the TUI draws after Enter are exactly the JSON children,
	in the same order."""
	path, cast = world
	expected = _json(capsys, path, "children", cast["lang42"],
	                 viewer="lang.grace")
	screen = _screen_rows(path, "lang.grace", [(b"\r", 0.5)])
	drawn = _parse_rows(screen)
	assert [row["title"] for row in drawn] == \
		[row["title"] for row in expected]
	for drawn_row, json_row in zip(drawn, expected):
		assert drawn_row["new"] == json_row["new"]
		assert drawn_row["next"] == json_row["next"]


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
	before = _json(capsys, path, "new", cast["lang42"], viewer="lang.grace")
	assert before["total"] > 0
	# grace drills into the epic and marks the epic's own discussion seen.
	text, status, _steps = ptyharness.drive(path, "lang.grace", [
		(b"\r", 0.5),        # drill: path = [lang42]
		(b"o", 0.5),         # discussion of lang42
		(b"s", 0.5),         # THE explicit seen transition
		(b"q", 0.4),
	], columns=WIDTH, lines=HEIGHT)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	after = _json(capsys, path, "new", cast["lang42"], viewer="lang.grace")
	assert after["own"] == 0, "the console's s did not commit the cursor"
	assert after["total"] == before["total"] - before["own"], \
		"the decomposition moved by a different amount than own"
	# ...and the TUI's home row shows the same reduced number.
	screen = _screen_rows(path, "lang.grace")
	drawn = _parse_rows(screen)
	assert drawn[0]["new"] == after["total"]
