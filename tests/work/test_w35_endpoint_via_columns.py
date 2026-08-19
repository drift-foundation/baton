"""W35: the Work table tells Endpoint and Via apart.

`work/records/2026/08/finding-tui-endpoint-via-columns/`. The table
labelled one column `Route` and rendered `route.endpoint` in it. For
implementation Work that cell read `baton.impl` whether the authority
had selected the default route `impl` — Claude — or the alternate
`impl2` — Gemini.

Before W230 that was terminology. With alternate routes it is
operationally misleading: the column promised the route while showing
the address, and the route is the thing that decides who may claim.

The vocabulary is now three separate facts:

- **Endpoint** is the stable `TEAM.KIND` address, `baton.impl`;
- **Via** is the selected internal route, `impl` or `impl2`;
- **Handler** is the exact participant after a successful claim.

Before a claim, Endpoint + Via say exactly where the Work is offered;
after one, Handler says who took it. JSON is untouched — it already
carries the structured route object, and this distinction is never
encoded in a column label or a glyph.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui import app                                 # noqa: E402
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                          # noqa: E402


def alternate_document():
	"""One team whose `impl` kind offers an ALTERNATE route, which is
	the whole situation this Work exists for: one endpoint, two routes,
	two different agents."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "impl"]}})
	team = document["teams"]["lang"]
	team["routes"]["main"] = {"role": "dev", "handlers": ["ada"]}
	team["routes"]["alt"] = {"role": "dev", "handlers": ["grace"]}
	team["kinds"]["impl"] = {"display": "Impl", "route": "main",
	                         "alternates": ["alt"]}
	return document


@pytest.fixture()
def world(tmp_path):
	import json as _json
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(alternate_document(), handle, indent=2,
		           sort_keys=True)
	from baton_work import lifecycle as lc
	database = lc.init_from_config(config_path,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"store": store, "config": config_path}
	store.close()


class Screen:
	def __init__(self, height=24, width=140):
		self.rows = {}
		self.height = height
		self.width = width

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		"""OVERLAY at `x`, keeping whatever lies beyond the write.

		A terminal composes; the simpler fake used elsewhere replaces
		the tail, and the Work table paints its bold Title AFTER the
		full row at a smaller column (W23) — so a replacing fake loses
		every cell to the right of the title, which is exactly the half
		this Work is about."""
		row = self.rows.get(y, "")
		text = str(text)[:n]
		row = row.ljust(x)
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def painted(world, member="ada", width=140):
	view = Console(world["store"], "lang", member,
	               config_path=world["config"])
	screen = Screen(width=width)
	view.render(screen)
	return screen.lines()


def cell(lines, column, row):
	"""One named cell out of the painted table, by its heading."""
	header = next(line for line in lines if "Endpoint" in line)
	start = header.index(column)
	following = [header.index(name) for name in
	             ("Id", "Title", "Out", "Pr", "Phase", "Cat", "Msg/My",
	              "Endpoint", "Via", "Handler", "Agent", "Next", "New",
	              "Held")
	             if name in header and header.index(name) > start]
	end = min(following) if following else len(row)
	return row[start:end].strip()


def make(world, kind="impl", title="the work"):
	return tr.create_work(world["store"], team="lang", kind=kind,
	                      title=title, origin="self-initiated",
	                      classification="design-choice", author="ada",
	                      body="the opener")


def row_for(lines, local_id):
	return next(line for line in lines if line.startswith(local_id + " "))


# -- the columns -------------------------------------------------------------

def test_the_table_names_endpoint_and_via_separately(world):
	make(world)
	header = next(line for line in painted(world) if "Endpoint" in line)
	assert "Via" in header, header
	assert "Route" not in header, \
		"the label that promised the route and showed the address " \
		"survived"
	assert header.index("Endpoint") < header.index("Via") < \
		header.index("Handler"), header


def test_default_routed_work_shows_its_address_and_its_route(world):
	born = make(world)
	lines = painted(world)
	row = row_for(lines, born["work_id"].rsplit("-", 1)[1])
	assert cell(lines, "Endpoint", row) == "lang.impl"
	assert cell(lines, "Via", row) == "main"
	assert cell(lines, "Handler", row) == "-", \
		"unclaimed Work must not look staffed"


def test_alternate_routed_work_shows_the_alternate(world):
	"""The defect, exactly: two Works on ONE endpoint, offered to two
	different agents, indistinguishable before this change."""
	default = make(world, title="through the default")
	alternate = make(world, title="through the alternate")
	tr.pass_work(world["store"], alternate["work_id"],
	             actor_team="lang", actor="ada", to="lang.impl",
	             route="alt", comment="over to the alternate route")
	lines = painted(world)
	first = row_for(lines, default["work_id"].rsplit("-", 1)[1])
	second = row_for(lines, alternate["work_id"].rsplit("-", 1)[1])
	assert cell(lines, "Endpoint", first) == "lang.impl"
	assert cell(lines, "Endpoint", second) == "lang.impl", \
		"the address is the same, which is why Via has to exist"
	assert cell(lines, "Via", first) == "main"
	assert cell(lines, "Via", second) == "alt", \
		"the alternate route is invisible again"


def test_a_claimed_alternate_shows_endpoint_via_and_handler(world):
	"""The acceptance boundary's exact assertion: the address, the
	route, and the participant who actually took it."""
	born = make(world)
	tr.pass_work(world["store"], born["work_id"], actor_team="lang",
	             actor="ada", to="lang.impl", route="alt",
	             comment="to the alternate")
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="grace")
	lines = painted(world, member="grace")
	row = row_for(lines, born["work_id"].rsplit("-", 1)[1])
	assert cell(lines, "Endpoint", row) == "lang.impl"
	assert cell(lines, "Via", row) == "alt"
	assert cell(lines, "Handler", row) == "lang.grace"


def test_via_never_disagrees_with_the_route_that_authorizes(world):
	"""'Endpoint and Via must never disagree with the selected route
	used for claim authorization.' Both come from the one resolved
	route object, so the table cannot advertise a route the claim
	would refuse."""
	born = make(world)
	tr.pass_work(world["store"], born["work_id"], actor_team="lang",
	             actor="ada", to="lang.impl", route="alt",
	             comment="to the alternate")
	lines = painted(world)
	row = row_for(lines, born["work_id"].rsplit("-", 1)[1])
	detail = pj.detail(world["store"], born["work_id"],
	                   viewer_team="lang", viewer_member="ada")
	assert cell(lines, "Via", row) == detail["route"]["route"]
	assert cell(lines, "Endpoint", row) == detail["route"]["endpoint"]
	# and the authority agrees about who that admits
	with pytest.raises(bw.WorkError, match="not a resolved handler"):
		tr.claim_work(world["store"], born["work_id"],
		              actor_team="lang", actor="ada")
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="grace")


def test_an_unresolved_route_reads_as_absent_in_both_cells(world):
	"""A retired kind resolves to nothing. The row says so in both
	cells rather than inventing an address or a route."""
	world["store"].conn.execute(
		"UPDATE kinds SET retired=1 WHERE team='lang' AND handle='impl'")
	world["store"].conn.commit()
	born = make(world, kind="bug")
	world["store"].conn.execute(
		"UPDATE work SET route_kind='impl' WHERE id=?",
		(born["work_id"],))
	world["store"].conn.commit()
	lines = painted(world)
	row = row_for(lines, born["work_id"].rsplit("-", 1)[1])
	assert cell(lines, "Endpoint", row) == "lang.impl", \
		"the address is configuration and survives retirement"
	assert cell(lines, "Via", row) == "-", \
		"a route that no longer resolves must not be guessed"


def test_a_terminal_row_reports_no_eligibility_in_either_cell(world):
	"""Eligibility is a LIVE question. The canonical projection already
	reports `route: null` and `handler: null` for terminal Work — the
	same rule that empties Phase — so both new cells read `-` exactly as
	Handler does. Via must not invent a route for Work that admits
	nobody; the route it was executed through stays in Events."""
	born = make(world)
	tr.pass_work(world["store"], born["work_id"], actor_team="lang",
	             actor="ada", to="lang.impl", route="alt",
	             comment="to the alternate")
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="grace")
	tr.close_work(world["store"], born["work_id"], actor_team="lang",
	              actor="grace", outcome="satisfying", rationale="done")
	view = Console(world["store"], "lang", "ada",
	               config_path=world["config"])
	view.show_closed = True
	screen = Screen(width=140)
	view.render(screen)
	lines = screen.lines()
	row = row_for(lines, born["work_id"].rsplit("-", 1)[1])
	detail = pj.detail(world["store"], born["work_id"],
	                   viewer_team="lang", viewer_member="ada")
	assert detail["route"] is None and detail["handler"] is None
	assert cell(lines, "Endpoint", row) == "-"
	assert cell(lines, "Via", row) == "-", \
		"a closed row advertises a route that admits nobody"
	assert cell(lines, "Handler", row) == "-"
	assert cell(lines, "Out", row) == "sat", \
		"the terminal row lost the outcome it was revealed for"


# -- responsive omission -----------------------------------------------------

def test_whole_columns_are_dropped_and_handler_outlives_both(world):
	"""'Responsive omission may drop Endpoint and Via before Handler,
	but it must drop whole columns rather than truncate identities.'"""
	widths = range(140, 40, -1)
	lost_via = lost_endpoint = lost_handler = None
	for width in widths:
		names = [name for name, _size in app.visible_columns(width)]
		if lost_via is None and "VIA" not in names:
			lost_via = width
		if lost_endpoint is None and "ENDPOINT" not in names:
			lost_endpoint = width
		if lost_handler is None and "HANDLER" not in names:
			lost_handler = width
	assert lost_via is not None and lost_endpoint is not None
	assert lost_via > lost_endpoint, \
		"Via must go before Endpoint — a bare route handle without its " \
		"address is the more ambiguous half"
	assert lost_handler is None, \
		"Handler was dropped; who is executing survives longest"


def test_a_narrow_table_never_truncates_an_identity(world):
	"""The columns are dropped whole; the title is the only thing the
	layout may cut, and identities are drawn complete or not at all."""
	born = make(world)
	tr.pass_work(world["store"], born["work_id"], actor_team="lang",
	             actor="ada", to="lang.impl", route="alt",
	             comment="to the alternate")
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="grace")
	for width in (140, 120, 100, 90, 80):
		lines = painted(world, width=width)
		header = next((line for line in lines if "Handler" in line), None)
		if header is None:
			continue
		row = row_for(lines, born["work_id"].rsplit("-", 1)[1])
		if "Endpoint" in header:
			assert cell(lines, "Endpoint", row) == "lang.impl", width
		if "Via" in header:
			assert cell(lines, "Via", row) == "alt", width
		assert cell(lines, "Handler", row) == "lang.grace", width


# -- JSON is untouched -------------------------------------------------------

def test_json_encodes_the_distinction_structurally_and_not_by_label(world):
	"""'JSON keeps the already explicit structured route object.' The
	console reads the same two fields the authorization does."""
	born = make(world)
	tr.pass_work(world["store"], born["work_id"], actor_team="lang",
	             actor="ada", to="lang.impl", route="alt",
	             comment="to the alternate")
	rows = pj.tree(world["store"], None, viewer_team="lang",
	               viewer_member="ada")["rows"]
	row = next(entry for entry in rows
	           if entry["id"] == born["work_id"])
	assert row["route"]["endpoint"] == "lang.impl"
	assert row["route"]["route"] == "alt"
	assert row["route"]["handlers"] == ["grace"]
	assert "via" not in row and "Via" not in _json_keys(row), \
		"the presentation vocabulary leaked into the projection"


def _json_keys(row):
	return set(row)
