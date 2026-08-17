"""W235 (finding-tui-selected-work-claim): lowercase `c` claims the
selected Work through the ONE canonical command path.

The shortcut invokes the same atomic `claim` operation as the JSON/CLI
surface — no second mutation contract, no optimistic local state. The
authority stays final: blocked Work, ineligible viewers, terminal Work,
and competing claims fail closed with the returned diagnostic shown,
and a successful claim schedules the ordinary refresh while the
id-anchored selection survives.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import json as _json                                          # noqa: E402

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"], "grace": ["impl"]},
		          "kinds": ["bug"]},
		 "push": {"members": {"sl": ["impl"]}, "kinds": ["bug"]}})
	# A REAL shared route: the competing-claim case needs two resolved
	# handlers of the same Current endpoint.
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "grace"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config, participant="lang.ada")
	store = bw.Authority(result["database"])
	yield {"config": config, "database": result["database"],
	       "store": store}
	store.close()


def make(world, title="claimable", team="lang", author="ada"):
	return tr.create_work(world["store"], team=team, kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="born")["work_id"]


def console(world, member="ada", team="lang"):
	return Console(world["store"], team, member,
	               config_path=world["config"])


def select(ui, work_id):
	rows, _hidden = ui.visible_rows(ui.rows())
	for index, row in enumerate(rows):
		if row["id"] == work_id:
			ui.cursor = index
			ui.selected_id = work_id
			return
	raise AssertionError(f"{work_id} is not visible")


def active(world, work_id):
	row = world["store"].conn.execute(
		"SELECT active_team, active_member FROM work WHERE id=?",
		(work_id,)).fetchone()
	return (row["active_team"], row["active_member"])


def test_c_claims_the_selected_work_canonically(world):
	work = make(world)
	ui = console(world)
	select(ui, work)
	assert ui.handle(ord("c")) is True
	assert active(world, work) == ("lang", "ada"), \
		"the shortcut did not commit the canonical claim"
	assert ui.status.startswith("ok"), ui.status
	# The audited event is the SAME canonical operation.
	newest = world["store"].events()[-1]
	assert newest["kind"] == "claim"
	assert newest["payload"]["work"] == work
	# The ordinary committed-only refresh path was scheduled and the
	# id-anchored selection survives it.
	assert ui.refresh_due is True
	rows, _hidden = ui.visible_rows(ui.rows())
	assert rows[ui.cursor]["id"] == work


def test_the_shortcut_is_scoped_to_table_navigation(world):
	work = make(world)
	ui = console(world)
	select(ui, work)
	# Inside the command bar, `c` is TEXT, never a claim.
	ui.handle(ord(":"))
	ui.handle(ord("c"))
	assert ui.command == "c"
	assert active(world, work) == (None, None), \
		"a command-bar keystroke claimed work"
	ui.handle(27)
	# Inside the detail view, `c` claims nothing either.
	ui.handle(10)
	assert ui.mode == "detail"
	ui.handle(ord("c"))
	assert active(world, work) == (None, None), \
		"a detail-view keystroke claimed work"


def test_refusals_fail_closed_with_the_returned_diagnostic(world):
	store = world["store"]
	# competing claim: grace already holds it
	contested = make(world)
	tr.claim_work(store, contested, actor_team="lang", actor="grace")
	ui = console(world)
	select(ui, contested)
	ui.handle(ord("c"))
	assert active(world, contested) == ("lang", "grace"), \
		"a competing claim was overwritten"
	assert "grace" in ui.status, \
		f"the competing-claim diagnostic is hidden: {ui.status}"
	assert ui.refresh_due is False, \
		"a refused claim scheduled a refresh"

	# blocked Work is not ready and refuses
	blocked = make(world, title="gated")
	gate = make(world, title="the gate")
	tr.add_dependency(store, blocked, gate, actor_team="lang",
	                  actor="ada")
	ui = console(world)          # a fresh snapshot sees the new rows
	select(ui, blocked)
	ui.handle(ord("c"))
	assert active(world, blocked) == (None, None)
	assert ui.status and not ui.status.startswith("ok"), ui.status

	# ineligible viewer: sl is not a handler of lang's route
	foreign = make(world, title="not mine")
	other = console(world, member="sl", team="push")
	other.path = []
	# push.sl cannot even see lang's home rows; drive the claim through
	# the same canonical path the key uses to prove the refusal shape.
	other.execute(f"claim work={foreign}")
	assert active(world, foreign) == (None, None)
	assert other.status and not other.status.startswith("ok")

	# terminal Work refuses
	done = make(world, title="finished")
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	ui = console(world)
	ui.show_closed = True
	select(ui, done)
	ui.handle(ord("c"))
	assert active(world, done) == (None, None)
	assert ui.status and not ui.status.startswith("ok"), ui.status


def test_c_claims_a_selected_search_result_and_query_text_stays_text(world):
	"""W235 R1: search results are selectable Work — the SAME shared
	canonical claim path; typing `c` in the query bar remains text and
	claims nothing."""
	work = make(world, title="findable target")
	ui = console(world)
	# open the query bar: `c` there is TEXT
	ui.handle(ord("/"))
	ui.handle(ord("c"))
	assert ui.search_input == "c"
	assert active(world, work) == (None, None), \
		"query-bar text claimed work"
	ui.handle(27)                 # cancel the stray query text
	# submit a real query and claim the selected result
	ui.handle(ord("/"))
	for ch in "findable":
		ui.handle(ord(ch))
	ui.handle(10)
	assert ui.mode == "search"
	rows, _hidden = ui.visible_rows(ui.search_rows())
	assert rows and rows[0]["id"] == work
	ui.cursor = 0
	ui.selected_id = work
	assert ui.handle(ord("c")) is True
	assert active(world, work) == ("lang", "ada"), \
		"the search-mode shortcut did not commit the canonical claim"
	assert ui.status.startswith("ok"), ui.status
	newest = world["store"].events()[-1]
	assert newest["kind"] == "claim" and newest["payload"]["work"] == work
	# selection survives on the same row
	rows, _hidden = ui.visible_rows(ui.search_rows())
	assert rows[ui.cursor]["id"] == work
