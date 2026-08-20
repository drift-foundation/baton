"""W4: authority-local ultra-short Work selectors.

One strict resolver (finding-local-work-selectors): every Work-valued
input accepts either the canonical `<authority>-W<seq>` id or the exact
authority-local `W<positive-sequence>` selector, scoped to the ONE
explicitly opened authority. Missing, malformed, foreign, or ambiguous
input refuses by name — never a guess from title, cursor, creation
order, or partial match. JSON exposes `local_id` beside `id`; the Work
list leads with an exact, non-truncating `Id` column.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def run(world, *argv, viewer="lang.ada"):
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = work_cli.main(["--config", world["config"],
		                      "--participant", viewer] + list(argv))
	return code, out.getvalue(), err.getvalue()


def ok(world, *argv):
	code, out, err = run(world, *argv)
	assert code == 0, err
	return _json.loads(out)["result"]


def refusal(world, *argv):
	code, _out, err = run(world, *argv)
	assert code == 1
	return _json.loads(err)["error"]


def make(world, title="w"):
	return ok(world, "create", "team=lang", "kind=bug", f"title={title}",
	          "origin=external-report",
	          "classification=suspected-defect", "body=b")["work_id"]


def digest(world):
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		return hashlib.sha256(handle.read()).hexdigest()


def test_the_resolver_is_strict_and_authority_scoped(world):
	"""The full matrix through THE one resolver: short qualifies,
	canonical passes, foreign refuses by authority, malformed refuses
	by shape, a well-formed absent selector gets the honest missing
	refusal — and nothing is ever guessed."""
	store = world["store"]
	canonical = make(world, title="target")
	local = canonical.rsplit("-", 1)[1]
	assert tr.resolve_work_selector(store, local) == canonical
	assert tr.resolve_work_selector(store, canonical) == canonical
	with pytest.raises(bw.WorkError, match="different authority"):
		tr.resolve_work_selector(store, "deadbeef-W2")
	for malformed in ("w2", "W0", "W", "2", "W2x", "W-3", "", "W 2",
	                  "nope-W1", "fefefefe-w2"):
		with pytest.raises(bw.WorkError,
		                   match="is not a Work selector"):
			tr.resolve_work_selector(store, malformed)
	assert "no work" in refusal(world, "detail", "work=W99")


def test_short_and_canonical_are_one_spelling_of_one_identity(world):
	"""Full-vs-short parity all the way into WS-5: dispatch resolves
	BEFORE the operation fingerprints its typed input, so the same
	op-id under either spelling is ONE operation — the exact retry
	replays instead of duplicating or conflicting."""
	consumer = make(world, title="consumer")
	blocker = make(world, title="blocker")
	short_c = consumer.rsplit("-", 1)[1]
	short_b = blocker.rsplit("-", 1)[1]
	first = ok(world, "block", f"work={short_c}", f"on={short_b}",
	           "rationale=provider required",
	           "op-id=edge-1")
	assert first.get("operation") is None or \
		first["operation"]["state"] != "replayed"
	again = ok(world, "block", f"work={consumer}", f"on={blocker}",
	           "rationale=provider required",
	           "op-id=edge-1")
	assert again["operation"]["state"] == "replayed", \
		"the canonical respelling was treated as a second operation"
	detail = ok(world, "detail", f"work={short_b}")
	assert detail["open_dependents"] == 1, "the edge did not commit once"


def test_every_work_valued_key_routes_through_the_resolver(world):
	"""claim/release/block/close/say/label/start-thread/detail and the
	creation links all speak the short selector; a malformed value on
	ANY of them refuses through the same resolver, by name."""
	work = make(world, title="routed")
	short = work.rsplit("-", 1)[1]
	ok(world, "claim", f"work={short}")
	ok(world, "release", f"work={short}", "expect=lang.ada",
	   "reason=cycling")
	child = ok(world, "create", "team=lang", "kind=bug", "title=child",
	           "origin=external-report",
	           "classification=suspected-defect", "body=b",
	           f"parent={short}")["work_id"]
	assert child.startswith(work.split("-")[0])
	thread = ok(world, "start-thread", "subject=s", "body=b",
	            f"label={short}")
	born = ok(world, "detail", f"work={short}")
	assert born["local_id"] == short
	closed = ok(world, "close", f"work={child.rsplit('-', 1)[1]}",
	            "rationale=done", "outcome=satisfying")
	follow = ok(world, "create", "team=lang", "kind=bug",
	            "title=follow", "origin=external-report",
	            "classification=suspected-defect", "body=b",
	            f"follow-up-of={child.rsplit('-', 1)[1]}")
	# malformed input on each Work-valued key refuses through the ONE
	# resolver — including keys whose other conditions are unmet, since
	# identity resolution precedes dispatch
	for argv in (("claim", "work=w1"),
	             ("block", "work=W1x", "on=W2", "rationale=gate"),
	             ("block", f"work={short}", "on=0W", "rationale=gate"),
	             ("close", "work=W-1", "rationale=r",
	              "outcome=rejected"),
	             ("close", f"work={short}", "rationale=r",
	              "outcome=rejected", "duplicate-of=q9"),
	             ("say", "thread=T1", "body=b", "request=lang.bug", "wait=false",
	              "on=Wx"),
	             ("label", "thread=T1", "work=1W"),
	             ("start-thread", "subject=s", "body=b", "label=ww"),
	             ("accept", "obligation=1", "body=b", "into=w9"),
	             ("create", "team=lang", "kind=bug", "title=t",
	              "origin=external-report",
	              "classification=suspected-defect", "body=b",
	              "parent=W_"),
	             ("detail", "work=W#")):
		assert "is not a Work selector" in refusal(world, *argv), argv


def test_selectors_never_consult_titles_even_twins(world):
	"""Two Works sharing one title: the selector resolves by permanent
	sequence alone — the twin titles are irrelevant and no ambiguity
	can arise from them."""
	first = make(world, title="twin")
	second = make(world, title="twin")
	assert first != second
	one = ok(world, "detail", f"work={first.rsplit('-', 1)[1]}")
	two = ok(world, "detail", f"work={second.rsplit('-', 1)[1]}")
	assert one["id"] == first and two["id"] == second
	assert one["title"] == two["title"] == "twin"


def test_json_exposes_local_id_beside_id(world):
	"""Rows and details carry BOTH the canonical id and the explicit
	local_id, and they agree by construction."""
	make(world, title="listed")
	rows = pj.tree(world["store"], viewer_team="lang",
	               viewer_member="ada")["rows"]
	assert rows
	for row in rows:
		assert row["local_id"] == row["id"].rsplit("-", 1)[1]
	detail = ok(world, "detail", f"work={rows[0]['local_id']}")
	assert detail["id"] == rows[0]["id"]
	assert detail["local_id"] == rows[0]["local_id"]


def test_a_refused_selector_leaves_no_residue(world):
	"""Malformed and foreign selectors on MUTATIONS refuse with the
	authority byte-identical — fail-closed, nothing partially
	committed."""
	work = make(world, title="held")
	before = digest(world)
	assert "is not a Work selector" in \
		refusal(world, "claim", "work=w1")
	assert "different authority" in \
		refusal(world, "close", "work=deadbeef-W2", "rationale=r",
		        "outcome=rejected")
	assert "no work" in \
		refusal(world, "block", f"work={work}", "on=W77",
		        "rationale=gate")
	assert digest(world) == before, "a refused selector left residue"


def test_the_id_column_leads_and_never_truncates(world):
	"""The Id column heads the table, sized to the longest visible
	selector — W2 and W1000 alike render whole; the width function is
	the shared layout contract."""
	from baton_work.tui.app import Console, id_column_width
	assert id_column_width([{"local_id": "W2"}]) == 2
	assert id_column_width([{"local_id": "W2"},
	                        {"local_id": "W1000"}]) == 5
	assert id_column_width([]) == 2
	make(world, title="drawn")
	painted = []

	class Screen:
		def addnstr(self, _y, _x, text, *_rest):
			painted.append(str(text))

	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(Screen(), 24, 110, console.rows())
	header = next(text for text in painted if "Title" in text)
	assert header.startswith("Id "), header
	row = next(text for text in painted if "drawn" in text)
	assert row.startswith("W2 "), row


def test_a_hidden_closed_id_does_not_widen_the_visible_table(world):
	"""The Id width is the longest VISIBLE selector. A collapsed closed
	row must not consume Title space or drop columns until `z` actually
	makes that row visible."""
	from baton_work.tui.app import Console
	make(world, title="open row")
	rows = pj.tree(world["store"], viewer_team="lang",
	               viewer_member="ada")["rows"]
	hidden = dict(rows[0], id="fefefefe-W100000", local_id="W100000",
	              title="closed hidden", status="closed", phase=None,
	              outcome="satisfying")
	painted = []

	class Screen:
		def addnstr(self, _y, _x, text, *_rest):
			painted.append(str(text))

	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(Screen(), 24, 80, rows + [hidden])
	header = next(text for text in painted if "Title" in text)
	assert header.startswith("Id Title"), \
		f"a hidden W100000 widened the visible Id column: {header!r}"


def test_an_overwide_visible_id_refuses_before_columns_are_clipped(world):
	"""Identity is never truncated, but neither may its growth silently
	clip mandatory columns. If Id + minimum Title + mandatory columns do
	not fit, the table uses its explicit narrow-terminal refusal."""
	from baton_work.tui.app import Console
	make(world, title="wide identity")
	row = pj.tree(world["store"], viewer_team="lang",
	              viewer_member="ada")["rows"][0]
	row = dict(row, id="fefefefe-W1000000000", local_id="W1000000000")
	painted = []

	class Screen:
		def addnstr(self, _y, _x, text, *_rest):
			painted.append(str(text))

	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	# W73 freed the six cells the St column held, so this refuses at a
	# narrower width than it used to, and W2938 freed the four `New`
	# held on top of that; the property is the REFUSAL, so the width
	# follows the budget.
	console._render_table(Screen(), 24, 36, [row])
	assert any("terminal too narrow" in text for text in painted), painted
	assert not any("wide identity" in text for text in painted), \
		"the renderer attempted a row whose mandatory tail would be clipped"


def test_the_bar_and_detail_speak_the_short_selector(world):
	"""The command bar accepts the short spelling end to end, and the
	detail header shows the canonical id WITH its local selector."""
	from baton_work.tui.app import Console
	work = make(world, title="typed")
	short = work.rsplit("-", 1)[1]
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.execute(f"claim work={short}")
	assert console.status.startswith("ok"), console.status
	claimed = ok(world, "detail", f"work={short}")
	assert claimed["handler"] == {"team": "lang", "member": "ada",
	                   "participant": "lang.ada"}
	header = console._detail_header(claimed)
	assert header.startswith(f"{work} ({short}) ["), header
