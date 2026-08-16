"""W3: the three-level team-local Work priority on schema 15.

Exactly high | normal | low (finding-work-priority): an ORDERING signal
only — readiness, dependencies, Current/Next, phase, status, and
closure are untouched. `create` accepts it optionally (default normal);
`prioritize work=... as=...` is the audited effectively-once revision,
authorized to ANY configured member of the owning team (independent of
Current, claimant, phase, readiness), refused cross-team, on closed
Work, and for a same-value change. Root siblings and each child sibling
group rank high, normal, low then created_seq without breaking
containment. JSON keeps the full strings; the TUI renders the two-cell
`Pr` column (Hi/No/Lo), dropped FIRST under width pressure.
"""

from __future__ import annotations

import contextlib
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
from baton_work.tui.app import (COLUMNS, DROP_ORDER, Console,  # noqa: E402
                                compact_priority, visible_columns)
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "grace": ["dev"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["dev"]},
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


def make(world, title="w", priority=None):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b",
	                      priority=priority)["work_id"]


def row_of(world, work_id):
	rows = pj.tree(world["store"], viewer_team="lang",
	               viewer_member="ada")["rows"]
	return next(row for row in rows if row["id"] == work_id)


def test_creation_accepts_priority_and_defaults_to_normal(world):
	"""Omission is the natural default; explicit high/low record
	atomically at birth; an invalid value refuses at the grammar."""
	assert row_of(world, make(world, "plain"))["priority"] == "normal"
	assert row_of(world,
	              make(world, "hot", "high"))["priority"] == "high"
	assert row_of(world,
	              make(world, "later", "low"))["priority"] == "low"
	code, _out, err = run(world, "create", "team=lang", "kind=bug",
	                      "title=x", "origin=external-report",
	                      "classification=suspected-defect", "body=b",
	                      "priority=urgent")
	assert code == 1 and "priority= takes one of" in err, \
		"the closed creation vocabulary leaked"


def test_prioritize_is_owning_team_authority(world):
	"""ANY configured owning-team member may revise — independent of
	Current, claimant, phase, readiness; cross-team refuses without
	changing anything; closed refuses; same-value refuses."""
	work = make(world, "governed")
	# ada claims and moves the phase; GRACE (not the claimant, not
	# necessarily the resolved handler) still holds priority authority
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="active")
	result = tr.prioritize(world["store"], work, actor_team="lang",
	                       actor="grace", priority="high")
	assert row_of(world, work)["priority"] == "high"
	# cross-team: discussion belongs in a Thread, not here
	with pytest.raises(bw.WorkError, match="owning-team authority"):
		tr.prioritize(world["store"], work, actor_team="push",
		              actor="sl", priority="low")
	assert row_of(world, work)["priority"] == "high"
	# same-value refuses — silence never masquerades as a change
	with pytest.raises(bw.WorkError, match="already high"):
		tr.prioritize(world["store"], work, actor_team="lang",
		              actor="ada", priority="high")
	# closed refuses
	done = make(world, "finished")
	tr.close_work(world["store"], done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="closed work"):
		tr.prioritize(world["store"], done, actor_team="lang",
		              actor="ada", priority="high")


def test_prioritize_is_audited_and_effectively_once(world):
	"""The revision advances the ordinary change identity, lands one
	audited event, and an exact op-id retry replays the committed
	result instead of re-mutating or refusing."""
	work = make(world, "audited")
	before = row_of(world, work)
	first = tr.prioritize(world["store"], work, actor_team="lang",
	                      actor="ada", priority="low", op_id="pri-1")
	after = row_of(world, work)
	assert after["priority"] == "low"
	assert after["last_change_seq"] > before["last_change_seq"], \
		"the revision did not advance the change identity"
	event = world["store"].conn.execute(
		"SELECT kind, payload FROM events ORDER BY seq DESC "
		"LIMIT 1").fetchone()
	assert event["kind"] == "prioritize"
	payload = _json.loads(event["payload"])
	assert payload["from"] == "normal" and payload["to"] == "low"
	replay = tr.prioritize(world["store"], work, actor_team="lang",
	                       actor="ada", priority="low", op_id="pri-1")
	assert replay["operation"]["state"] == "replayed"
	assert row_of(world, work)["priority"] == "low"


def test_priority_never_touches_the_workflow_axes(world):
	"""The ordering signal mutates NOTHING else: phase, status,
	readiness, Current, Next, claimant, and dependency counts are
	byte-for-byte identical across a revision."""
	work = make(world, "isolated")
	gate = make(world, "the gate")
	tr.add_dependency(world["store"], work, gate, actor_team="lang",
	                  actor="ada")
	before = row_of(world, work)
	tr.prioritize(world["store"], work, actor_team="lang", actor="ada",
	              priority="high")
	after = row_of(world, work)
	untouched = ("phase", "status", "ready", "current", "next",
	             "active", "open_blockers", "open_dependents",
	             "first_open_blocker", "claimed_at")
	for field in untouched:
		assert after[field] == before[field], field
	assert after["priority"] == "high" and before["priority"] == "normal"


def test_the_cli_speaks_prioritize_with_short_selectors(world):
	"""`prioritize work=Wn as=...` end to end through the public
	grammar — closed vocabulary on as=, W4 selector routing on work=."""
	work = make(world, "typed")
	short = work.rsplit("-", 1)[1]
	code, out, _err = run(world, "prioritize", f"work={short}",
	                      "as=high")
	assert code == 0
	assert row_of(world, work)["priority"] == "high"
	code, _out, err = run(world, "prioritize", f"work={short}",
	                      "as=sky-high")
	assert code == 1 and "as= takes one of" in err
	code, _out, err = run(world, "prioritize", "work=w9", "as=low")
	assert code == 1 and "is not a Work selector" in err


def test_siblings_rank_by_priority_inside_their_groups(world):
	"""Root siblings order high, normal, low then created_seq; each
	child group orders identically UNDER its parent — a high child
	never leaves its normal parent to chase the global sort."""
	first = make(world, "root normal one")
	second = make(world, "root high", "high")
	third = make(world, "root low", "low")
	fourth = make(world, "root normal two")
	child_low = tr.create_work(world["store"], team="lang", kind="bug",
	                           title="child low",
	                           origin="external-report",
	                           classification="suspected-defect",
	                           author="ada", body="b", parent=first,
	                           priority="low")["work_id"]
	child_high = tr.create_work(world["store"], team="lang", kind="bug",
	                            title="child high",
	                            origin="external-report",
	                            classification="suspected-defect",
	                            author="ada", body="b", parent=first,
	                            priority="high")["work_id"]
	window = pj.tree(world["store"], viewer_team="lang",
	                 viewer_member="ada")["rows"]
	order = [(row["id"], row["depth"]) for row in window]
	assert order == [
		(second, 0),                 # high root first
		(first, 0),                  # then normal roots by created_seq
		(child_high, 1),             # ...whose children rank in place
		(child_low, 1),
		(fourth, 0),
		(third, 0),                  # low root last
	], order
	# a later revision reorders on the next canonical read
	tr.prioritize(world["store"], third, actor_team="lang",
	              actor="ada", priority="high")
	window = pj.tree(world["store"], viewer_team="lang",
	                 viewer_member="ada")["rows"]
	tops = [row["id"] for row in window if row["depth"] == 0]
	assert tops[:2] == [second, third], \
		"the revision did not reorder the sibling group"


def test_priority_survives_restart(world):
	"""The persisted fact and its ordering are identical after a
	fresh open of the same authority."""
	work = make(world, "persisted", "high")
	world["store"].close()
	reopened = bw.Authority(world["database"])
	try:
		rows = pj.tree(reopened, viewer_team="lang",
		               viewer_member="ada")["rows"]
		row = next(entry for entry in rows if entry["id"] == work)
		assert row["priority"] == "high"
		assert rows[0]["id"] == work, "the high row lost its rank"
	finally:
		reopened.close()
		world["store"] = bw.Authority(world["database"])


def test_the_tui_renders_pr_and_drops_it_first(world):
	"""The two-cell Pr column renders Hi/No/Lo beside canonical JSON's
	full strings; under width pressure Pr is the FIRST whole column
	omitted, leaving every older narrow layout intact."""
	assert ("PR", 2) in COLUMNS
	assert DROP_ORDER[0] == "PR"
	assert compact_priority("high") == "Hi"
	assert compact_priority("normal") == "No"
	assert compact_priority("low") == "Lo"
	with pytest.raises(ValueError):
		compact_priority("Hi")       # compact input is never canonical
	make(world, "ranked", "high")
	painted = []

	class Screen:
		def addnstr(self, _y, _x, text, *_rest):
			painted.append(str(text))

	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(Screen(), 24, 110, console.rows())
	header = next(text for text in painted if "Title" in text)
	assert " Pr " in header, header
	row = next(text for text in painted if "ranked" in text)
	assert " Hi " in row, row
	# the first width that drops anything drops exactly PR
	wide = [name for name, _w in visible_columns(110)]
	assert "PR" in wide
	narrower = next(width for width in range(110, 40, -1)
	                if len(visible_columns(width)) < len(COLUMNS))
	dropped = [name for name, _w in visible_columns(narrower)]
	assert "PR" not in dropped and "CLS" in dropped, \
		"width pressure did not drop Pr first"
