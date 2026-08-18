"""C4: endpoint-resolution snapshots and their immutability.

The two pinned properties: every endpoint-establishing operation records the
full `(endpoint, route, role, handlers, generation)` resolution in committed
state — never partly resolved, never bare — and a later handler or route
reassignment does NOT rewrite that history, while the live projection shows
the new resolution.
"""

from __future__ import annotations

import copy
import json
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
import fixtures as fx                                         # noqa: E402

SNAPSHOT_KEYS = {"endpoint", "route", "role", "handlers", "generation"}


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch", "impl", "rev"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store, config_path, tmp_path
	store.close()


def _snapshots_in(payload) -> list[dict]:
	found = []
	def walk(value):
		if isinstance(value, dict):
			if SNAPSHOT_KEYS <= set(value):
				found.append(value)
			else:
				for inner in value.values():
					walk(inner)
		elif isinstance(value, list):
			for inner in value:
				walk(inner)
	walk(payload)
	return found


def test_every_endpoint_establishing_event_carries_a_full_snapshot(world):
	"""The no-partly-bare rule, swept over the whole trail: create, +, @,
	=> and planned Next each produce at least one complete snapshot, and no
	endpoint-establishing event is bare."""
	store, _config, _tmp = world
	work = tr.create_work(store, team="lang", kind="rsrch", title="epic",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="report")["work_id"]
	fx.post(store, work, author_team="lang", author="ada",
	                body="fyi", include="*.bug")
	fx.post(store, work, author_team="lang", author="ada",
	                body="confirm?", request="web.bug")
	fx.post(store, work, author_team="lang", author="ada",
	                body="go", pass_to="lang.impl", set_next="lang.rev")
	fx.post(store, work, author_team="lang", author="ada",
	                body="done", pass_to="lang.rev")

	establishing = [event for event in store.events()
	                if event["kind"] in ("create_work", "post_message",
	                                     "request", "pass", "return")]
	assert len(establishing) == 5
	for event in establishing:
		snapshots = _snapshots_in(event["payload"])
		assert snapshots, f"{event['kind']} recorded no resolution"
		for snapshot in snapshots:
			assert snapshot["route"] and snapshot["role"] is not None
			assert snapshot["handlers"], f"bare snapshot in {event['kind']}"
			assert snapshot["generation"] == 1

	# The pass and its planned Next both resolved.
	passed = next(e for e in establishing if e["kind"] == "pass")
	assert passed["payload"]["pass_resolution"]["endpoint"] == "lang.impl"
	assert passed["payload"]["next_resolution"]["endpoint"] == "lang.rev"
	# ...and the obligation row carries the snapshot columns.
	obligation = store.conn.execute(
		"SELECT * FROM obligations").fetchone()
	assert obligation["route"] == "main"
	assert json.loads(obligation["handlers"]) == ["wren"]
	assert obligation["generation"] == 1


def test_reassignment_changes_the_projection_not_the_history(world):
	"""One handler swap by generation-2 acceptance: the obligation and the
	events keep generation-1 handlers; the live projection shows
	generation 2."""
	store, config_path, tmp_path = world
	work = tr.create_work(store, team="lang", kind="rsrch", title="epic",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="report")["work_id"]
	fx.post(store, work, author_team="lang", author="ada",
	                body="confirm?", request="web.bug")
	before_events = store.events()

	document = json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")

	# HISTORY UNCHANGED, byte for byte.
	after = [event for event in store.events()
	         if event["seq"] <= before_events[-1]["seq"]]
	assert after == before_events, "acceptance rewrote recorded resolutions"
	obligation = store.conn.execute("SELECT * FROM obligations").fetchone()
	assert json.loads(obligation["handlers"]) == ["wren"]
	assert obligation["generation"] == 1

	# THE LIVE VIEW MOVED: lang endpoints now resolve to grace.
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert detail["route"]["handlers"] == ["grace"]
	obligations = pj.obligations(store, viewer_team="web")
	assert obligations[0]["owed_by"]["handlers"] == ["wren"], \
		"web.bug's live resolution changed but was not reassigned"


def test_include_expansion_uses_the_generation_at_commit(world, monkeypatch):
	"""A wildcard is itself endpoint resolution, not merely parsing.

	Model a generation acceptance after the optimistic pre-read but before the
	message write.  The committed expansion must describe generation 2 in full,
	including the endpoint generation 2 added; mixing generation-1 membership
	with generation-2 snapshots is not an at-use resolution.
	"""
	store, config_path, _tmp = world
	work = tr.create_work(store, team="lang", kind="rsrch", title="epic",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="report")["work_id"]
	original = tr._expand_include

	def accept_between_expand_and_write(open_store, selectors):
		expanded = original(open_store, selectors)
		document = json.loads(open(config_path).read())
		document["generation"] = 2
		document["teams"]["web"]["kinds"]["perf"] = {
			"display": "Perf", "route": "main"}
		with open(config_path, "w") as handle:
			json.dump(document, handle, indent=2, sort_keys=True)
		lc.accept_config(config_path, actor="lang.ada")
		return expanded

	monkeypatch.setattr(tr, "_expand_include", accept_between_expand_and_write)
	fx.post(store, work, author_team="lang", author="ada",
	                body="all web endpoints", include="web.*")
	event = store.events()[-1]
	assert [(entry["endpoint"], entry["generation"])
	        for entry in event["payload"]["include"]] == [
		("web.bug", 2), ("web.perf", 2)]


def test_an_unresolvable_current_is_shown_unresolved_never_bare(world):
	"""Read-time honesty: retire a kind under an open work is refused by the
	stranding gate — so construct the closed-work case, where the endpoint
	is historical and the projection must mark it unresolved explicitly."""
	store, config_path, _tmp = world
	work = tr.create_work(store, team="web", kind="bug", title="w",
	                      origin="external-report", classification="suspected-defect", author="wren",
	                      body="b")["work_id"]
	tr.close_work(store, work, actor_team="web", actor="wren",
	              rationale="done", outcome="satisfying")
	document = json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["web"]["kinds"]["bug"]
	with open(config_path, "w") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")
	# A retired kind refuses NEW work at tag time...
	with pytest.raises(bw.WorkError, match="retired"):
		tr.create_work(store, team="web", kind="bug", title="late",
		               origin="external-report", classification="suspected-defect", author="wren", body="x")
	# ...and links to the closed work still render, with current None
	# (closed clears it) — nothing anywhere is a bare string.
	graph = pj.links(store, work)
	assert graph["id"] == work
