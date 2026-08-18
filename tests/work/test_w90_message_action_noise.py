"""W90 (finding-message-work-action-noise): the reading surface stops
claiming Work capabilities.

`_facts()` rendered `available_transitions` as a `can: ...` line
directly above the Threads list. `can: prioritize` therefore sat inside
a reading context, where it reads as something you might do to the
message in front of you. It is a capability of the WORK — open to any
configured member of its owning team — and repeating it there invited
exactly that misreading.

Rendering-only: the canonical projection, the command grammar, and the
authority are untouched.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402


class Screen:
	def __init__(self):
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		self.calls.append((y, x, str(text)))

	def lines(self):
		return [text for _y, _x, text in self.calls]


@pytest.fixture()
def world(tmp_path):
	"""`ada` handles the route; `grace` is a configured team member the
	route does NOT resolve — the two viewers the finding names."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"], "grace": ["obs"]},
		          "kinds": ["bug"]},
		 "rev": {"members": {"bee": ["rview"]}, "kinds": ["bug"]}})
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["ada"]
	document["roots"] = {"baton": {"display": "Baton",
	                               "base": "/srv/checkouts/baton"}}
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store}
	store.close()


def make(world, title="reading target"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


def facts_for(world, work, member):
	detail = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member=member)
	console = Console(world["store"], "lang", member,
	                  config_path=world["config"])
	return detail, console._facts(detail)


# -- the pure renderer -------------------------------------------------------

def test_the_authorized_viewer_sees_no_capability_line(world):
	born = make(world)
	detail, facts = facts_for(world, born["work_id"], "ada")
	assert "prioritize" in detail["available_transitions"], \
		"the fixture does not exercise an authorized viewer"
	assert not any(fact.startswith("can:") for fact in facts), facts
	assert not any("prioritize" in fact for fact in facts), facts


def test_the_unauthorized_viewer_is_equally_unaffected(world):
	"""grace may still prioritize (it is an owning-team capability), and
	either way the reading surface says nothing about it."""
	born = make(world)
	detail, facts = facts_for(world, born["work_id"], "grace")
	assert not any(fact.startswith("can:") for fact in facts), facts


def test_every_other_fact_survives(world):
	"""The line removed is the ONLY thing removed: outcome, claimant,
	binding, contract revision, duplicate and follow-up all remain."""
	store = world["store"]
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="bound and claimed",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b",
	                      binding="baton:work/records/2026/08/finding-x")
	work = born["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	_detail, facts = facts_for(world, work, "ada")
	joined = "\n".join(facts)
	assert "current: lang.ada" in joined, facts
	assert "binding baton:work/records/2026/08/finding-x r1" in joined, facts

	# a terminal Work keeps its outcome and durable rationale
	done = make(world, "finished")["work_id"]
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="delivered and verified", outcome="satisfying")
	_closed, closed_facts = facts_for(world, done, "ada")
	assert any("closed satisfying — delivered and verified" in fact
	           for fact in closed_facts), closed_facts
	assert not any(fact.startswith("can:") for fact in closed_facts)


def test_the_canonical_projection_still_declares_authority(world):
	"""The client-facing guarantee W90 explicitly preserves."""
	born = make(world)
	detail = pj.detail(world["store"], born["work_id"],
	                   viewer_team="lang", viewer_member="ada")
	assert "prioritize" in detail["available_transitions"]
	assert "claim" in detail["available_transitions"]


def test_the_command_grammar_is_untouched(world):
	"""Removing the rendering must not remove the operation."""
	store = world["store"]
	work = make(world)["work_id"]
	tr.prioritize(store, work, actor_team="lang", actor="ada",
	              priority="high")
	assert store.conn.execute(
		"SELECT priority FROM work WHERE id=?",
		(work,)).fetchone()["priority"] == "high"


# -- the painted screen, wide and narrow -------------------------------------

def painted(world, member="ada", height=24, width=100):
	console = Console(world["store"], "lang", member,
	                  config_path=world["config"])
	console.detail_work = console.rows()[0]["id"]
	console.mode = "detail"
	screen = Screen()
	console._render_detail(screen, height, width)
	return console, screen.lines()


@pytest.mark.parametrize("width", [100, 44])
def test_no_capability_text_reaches_the_screen_at_either_width(world,
                                                               width):
	make(world)
	_console, lines = painted(world, width=width)
	flat = "\n".join(lines)
	assert "can:" not in flat, flat[:400]
	assert "prioritize" not in flat, flat[:400]


@pytest.mark.parametrize("width", [100, 44])
def test_the_reading_context_is_intact_at_either_width(world, width):
	make(world)
	_console, lines = painted(world, width=width)
	flat = "\n".join(lines)
	assert "Threads (" in flat, flat[:400]
	assert "Messages (" in flat, flat[:400]
	assert "the opener" in flat, \
		f"the message body stopped rendering: {flat[:400]}"


def test_the_events_tab_is_also_free_of_capability_text(world):
	"""The facts block is shared by both tabs, so the removal must hold
	on the Events surface too — and Events must still render."""
	store = world["store"]
	work = make(world)["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	console, _lines = painted(world)
	console.handle(ord("]"))
	screen = Screen()
	console._render_detail(screen, 24, 100)
	flat = "\n".join(screen.lines())
	assert "can:" not in flat, flat[:400]
	assert "Events (" in flat, f"the Events tab stopped rendering: {flat[:400]}"
