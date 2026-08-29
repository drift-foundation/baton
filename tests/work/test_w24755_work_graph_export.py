"""W24755 — the portable Work-graph export.

`work/records/2026/08/finding-portable-work-graph-export/`.

The twelve acceptance groups the finding names, plus the refusals the approver's
range ruling added. Every case is driven through the public surface the
operator actually has: the projection for structure, the pure renderer for
bytes, and `cli.main` for the grammar and the raw-output branch.

WHAT THIS SUITE IS FOR, stated once so each case can be short. An export is
believed or it is useless: a consumer holding a `.dot` file has no way to tell a
complete graph from a graph that quietly dropped an edge, a snapshot from a
stitch of several, or a title from a title that decided the document's
structure. So the cases here are mostly about what CANNOT happen rather than
about what the happy path prints.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import time

import pytest

import baton_work as bw
from baton_work import cli, dot, jsonapi, projection
from baton_work import transitions as tr

import fixtures


@pytest.fixture()
def world(tmp_path):
	fixtures.build(str(tmp_path / "work.sqlite3"))
	store = bw.Authority(str(tmp_path / "work.sqlite3"))
	yield {"store": store,
	       "config": str(tmp_path / "baton.json"),
	       "database": str(tmp_path / "work.sqlite3")}
	store.close()


def depend(store, consumer, blocker):
	return tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                         actor="ada", rationale="the export needs an edge")


def finish(store, work_id, outcome="satisfying"):
	return tr.close_work(store, work_id, actor_team="lang", actor="ada",
	                     outcome=outcome, rationale="done")


def make(store, title, *, team="lang", kind="bug", parent=None,
         follow_up_of=None, author="ada", origin="self-initiated"):
	return tr.create_work(
		store, team=team, kind=kind, title=title, origin=origin,
		classification="suspected-defect", author=author,
		body=f"body for {title}", parent=parent,
		follow_up_of=follow_up_of)["work_id"]


def run(capsys, config, *operands, participant="lang.ada", expect_ok=True,
        raw=False):
	"""One CLI invocation, through the same entry point an operator drives."""
	code = cli.main(["--config", config, "--participant", participant,
	                 *operands])
	captured = capsys.readouterr()
	assert code == (0 if expect_ok else 1), captured.err
	if raw:
		return captured.out, captured.err
	if not expect_ok:
		return json.loads(captured.err)
	return json.loads(captured.out)


def edges_of(graph, relation=None):
	return [edge for edge in graph["edges"]
	        if relation is None or edge["relation"] == relation]


def node(graph, work_id):
	return next(one for one in graph["nodes"] if one["id"] == work_id)


def sample_node(work_id, **overrides):
	"""One structurally complete node, for cases whose subject is topology.

	Second review [P1] made `validate_work_graph` own member TYPES as well as
	presence, so a case that handed it `{"id": ...}` was refused for a reason
	it was not about. A complete node keeps each of those cases pointed at the
	rule it exists to measure.
	"""
	return {"id": work_id, "local_id": work_id.rsplit("-", 1)[1],
	        "team": "lang", "title": "a title", "origin": "self-initiated",
	        "classification": "suspected-defect", "priority": "normal",
	        "status": "open", "phase": "queued", "outcome": None,
	        "created_seq": 1, "last_changed_at": "2026-08-27T00:00:00Z",
	        "selected": True, **overrides}


def one_node_counts(graph):
	"""The counts a one-node, no-edge result must carry.

	`counts` is derived from the arrays since the fourth review, so a case that
	replaces the node list has to replace the counts beside it.
	"""
	return dict(graph["counts"], selected_nodes=1, context_nodes=0, nodes=1,
	            edges=0)


def a_result(nodes, edges):
	"""A structurally complete result around the nodes and edges under test.

	`validate_work_graph` owns the WHOLE result since the fourth review, so a
	case about topology has to hand it a scope and derived counts too -- or it
	refuses for a reason the case is not about.
	"""
	selected = len([one for one in nodes if one["selected"]])
	return {"scope": {"team": None, "status": "open", "changed_from": None,
	                  "changed_until": None,
	                  "closure": projection.GRAPH_CLOSURE},
	        "counts": {"selected_nodes": selected,
	                   "context_nodes": len(nodes) - selected,
	                   "nodes": len(nodes), "edges": len(edges)},
	        "nodes": nodes, "edges": edges}


def closed_node(work_id, **overrides):
	"""The other valid node state: terminal, so no phase and one outcome.

	Fourth review [P1] made the three state members ONE state, so a case that
	needs a closed node cannot get there by setting `status` alone.
	"""
	return sample_node(work_id, **{"status": "closed", "phase": None,
	                               "outcome": "satisfying", **overrides})


# -- 1. all four relation types, exact directions, predicates and sequences ----


def four_relations(store):
	"""One authority holding every relation family at once.

	Built through the ordinary transitions rather than by writing rows, so the
	relations are the ones the authority actually produces -- a fixture that
	inserted them directly would prove the exporter reads a shape this
	repository can no longer create.
	"""
	parent = make(store, "the parent")
	child = make(store, "the child", parent=parent)
	blocker = make(store, "the blocker")
	consumer = make(store, "the consumer")
	depend(store, consumer, blocker)
	predecessor = make(store, "the predecessor")
	finish(store, predecessor)
	successor = make(store, "the successor", follow_up_of=predecessor)
	survivor = make(store, "the survivor")
	rejected = make(store, "the rejected duplicate")
	tr.classify(store, rejected, actor_team="lang", actor="ada",
	            classification="duplicate")
	tr.close_work(store, rejected, actor_team="lang", actor="ada",
	              outcome="rejected", rationale="folded into the survivor",
	              duplicate_of=survivor)
	return {"parent": parent, "child": child, "blocker": blocker,
	        "consumer": consumer, "predecessor": predecessor,
	        "successor": successor, "survivor": survivor,
	        "rejected": rejected}


def test_every_relation_family_exports_with_its_ruled_direction(world):
	"""The four families, each pointing the one way the finding fixes.

	DIRECTION IS THE WHOLE POINT of a typed export: `blocks` and `blocked_by`
	are the same edge read from two ends, and a consumer that guessed wrong
	would draw the dependency graph backwards while looking entirely correct.
	"""
	store = world["store"]
	cast = four_relations(store)
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	found = {(edge["relation"], edge["source"], edge["target"]):
	         edge for edge in graph["edges"]}
	assert ("dependency", cast["blocker"], cast["consumer"]) in found
	assert ("containment", cast["parent"], cast["child"]) in found
	assert ("follow-up", cast["predecessor"], cast["successor"]) in found
	assert ("duplicate", cast["rejected"], cast["survivor"]) in found
	# THE REVERSE OF EACH IS ABSENT. Without this the case above passes for an
	# exporter that emits both directions of everything.
	assert ("dependency", cast["consumer"], cast["blocker"]) not in found
	assert ("containment", cast["child"], cast["parent"]) not in found
	assert ("follow-up", cast["successor"], cast["predecessor"]) not in found
	assert ("duplicate", cast["survivor"], cast["rejected"]) not in found
	for (relation, _source, _target), edge in found.items():
		assert edge["predicate"] == {
			"dependency": "blocks", "containment": "contains",
			"follow-up": "followed_by", "duplicate": "duplicate_of"}[relation]


def test_each_relation_sequence_is_the_moment_the_relation_began(world):
	"""The ordering keys, held to the columns that carry them.

	Every one of these is only deterministic because the underlying column
	cannot move: `parent` and `follow_up_of` are written at creation and never
	updated, and `duplicate_of` is written by the same close that sets
	`closed_seq`. Asserting the VALUES is how that stays true -- a later change
	that started reparenting would fail here rather than silently reorder
	everyone's exports.
	"""
	store = world["store"]
	cast = four_relations(store)
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	rows = {work_id: dict(store.conn.execute(
		"SELECT created_seq, closed_seq FROM work WHERE id=?",
		(work_id,)).fetchone()) for work_id in cast.values()}
	by_relation = {edge["relation"]: edge for edge in graph["edges"]
	               if edge["relation"] != "dependency"}
	assert by_relation["containment"]["relation_seq"] == \
		rows[cast["child"]]["created_seq"]
	assert by_relation["follow-up"]["relation_seq"] == \
		rows[cast["successor"]]["created_seq"]
	assert by_relation["duplicate"]["relation_seq"] == \
		rows[cast["rejected"]]["closed_seq"]
	assert rows[cast["rejected"]]["closed_seq"] is not None
	dependency = next(edge for edge in edges_of(graph, "dependency")
	                  if edge["source"] == cast["blocker"]
	                  and edge["target"] == cast["consumer"])
	assert dependency["relation_seq"] == store.conn.execute(
		"SELECT created_seq FROM edges WHERE work=? AND blocker=?",
		(cast["consumer"], cast["blocker"])).fetchone()["created_seq"]


def test_a_dependency_carries_the_obligation_it_was_created_through(world):
	"""`via_obligation` is the dependency's own member and null elsewhere."""
	store = world["store"]
	cast = four_relations(store)
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	for edge in graph["edges"]:
		if edge["relation"] != "dependency":
			assert edge["via_obligation"] is None, edge


# -- 2. several relation types between one pair remain several edges ----------


def test_one_pair_holding_two_relations_exports_two_edges(world):
	"""THE REASON THE DIGRAPH IS NOT `strict`, from a graph the authority can
	really produce.

	Graphviz's `strict` merges parallel edges sharing a tail and head: the
	later statement refers to the existing edge and applies its attributes to
	it. So a `strict` export would collapse two true relations into one and
	report the last one's label for both.

	FINDING.md says any of the four families may coexist on one pair. Driving
	that against the authority showed the reachable set is NARROWER, and the
	narrowing is worth recording rather than working around:

	  - containment + dependency on one pair is refused as a required-edge
	    cycle;
	  - follow-up + dependency is refused because a follow-up predecessor is
	    closed and a new blocker must be open;
	  - containment + duplicate is refused because a parent cannot close while
	    it holds an open child.

	What IS reachable is dependency + duplicate: A blocks B, then A is closed
	as a rejected duplicate of B. That is this case, and two parallel edges is
	all the `strict` argument needs. The renderer is separately held to four
	below, because it may be handed a graph this authority cannot currently
	build.
	"""
	store = world["store"]
	first = make(store, "the blocker that turns out to be a duplicate")
	second = make(store, "the consumer that survives")
	depend(store, second, first)
	tr.classify(store, first, actor_team="lang", actor="ada",
	            classification="duplicate")
	tr.close_work(store, first, actor_team="lang", actor="ada",
	              outcome="rejected", rationale="folded into the survivor",
	              duplicate_of=second)
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	between = [edge for edge in graph["edges"]
	           if edge["source"] == first and edge["target"] == second]
	assert sorted(edge["relation"] for edge in between) == \
		["dependency", "duplicate"]

	text = dot.render_work_graph_dot(envelope_for(store, graph))
	assert not text.startswith("strict"), text.splitlines()[0]
	statements = [line for line in text.splitlines()
	              if f'"{first}" -> "{second}"' in line]
	assert len(statements) == 2, statements
	# EACH SPELLS ITS OWN RELATION, so the two are distinguishable in the text
	# and not only in the count.
	assert sorted(one.split('baton_relation="')[1].split('"')[0]
	              for one in statements) == ["dependency", "duplicate"]


def test_the_renderer_keeps_four_parallel_relations_separate(world):
	"""The renderer's own obligation, beyond what the store reaches today.

	The authority currently permits at most two same-direction relations on
	one pair (see the case above). The FORMAT still has to carry four, because
	a later rule change is a change to the authority and must not silently
	become a change to every previously exported document.
	"""
	store = world["store"]
	first = make(store, "a")
	second = make(store, "b")
	graph = projection.work_graph(store, status="open")
	graph = dict(graph, edges=[
		projection._export_edge(relation, first, second, index + 1)
		for index, relation in enumerate(projection.GRAPH_RELATIONS)])
	graph["counts"] = dict(graph["counts"], edges=4)
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	statements = [line for line in text.splitlines()
	              if f'"{first}" -> "{second}"' in line]
	assert len(statements) == 4
	assert sorted(one.split('baton_relation="')[1].split('"')[0]
	              for one in statements) == sorted(projection.GRAPH_RELATIONS)


def envelope_for(store, graph):
	result = {name: value for name, value in graph.items()
	          if name != "snapshot_seq"}
	return jsonapi.envelope(store, participant="lang.ada", result=result,
	                        snapshot_seq=graph["snapshot_seq"])


# -- 3. filters retain incident endpoints as context and do not expand --------


def test_a_filter_keeps_the_far_endpoint_as_marked_context(world):
	"""An open-only export keeps its closed blocker, and SAYS it is context.

	Dropping it would emit a dangling edge or hide a real dependency;
	promoting it to a selected row would report a closed Work as part of the
	open graph. The third answer -- present and marked -- is the only one that
	is true.
	"""
	store = world["store"]
	blocker = make(store, "the closed blocker")
	consumer = make(store, "the open consumer")
	depend(store, consumer, blocker)
	finish(store, blocker)
	graph = projection.work_graph(store, status="open")
	assert node(graph, consumer)["selected"] is True
	assert node(graph, blocker)["selected"] is False
	assert node(graph, blocker)["status"] == "closed"
	assert ("dependency", blocker, consumer) in {
		(edge["relation"], edge["source"], edge["target"])
		for edge in graph["edges"]}
	assert graph["counts"]["selected_nodes"] >= 1
	assert graph["counts"]["context_nodes"] >= 1
	assert graph["counts"]["nodes"] == \
		graph["counts"]["selected_nodes"] + graph["counts"]["context_nodes"]


def test_context_does_not_expand_into_an_unbounded_history_chain(world):
	"""CLOSURE IS ONE HOP FROM A SELECTED NODE, and never a traversal.

	A closed predecessor may itself follow up a closed predecessor, ten deep.
	If context expanded, one open Work at the end of a long history would drag
	that entire chain into an `open` export -- which is the bounded-versus-
	complete question the finding settles in favour of adjacency.
	"""
	store = world["store"]
	chain = []
	previous = None
	for index in range(4):
		work_id = make(store, f"history {index}", follow_up_of=previous)
		finish(store, work_id)
		chain.append(work_id)
		previous = work_id
	current = make(store, "the one open successor", follow_up_of=chain[-1])
	graph = projection.work_graph(store, status="open")
	present = {one["id"] for one in graph["nodes"]}
	assert current in present
	# Exactly the one hop.
	assert chain[-1] in present
	for older in chain[:-1]:
		assert older not in present, "context expanded beyond one hop"
	# AND THE EDGE BETWEEN THE TWO CONTEXT NODES IS NOT EMITTED EITHER: it is
	# incident to no selected node, so including it would describe a
	# relationship this export never claimed to cover.
	assert ("follow-up", chain[-2], chain[-1]) not in {
		(edge["relation"], edge["source"], edge["target"])
		for edge in graph["edges"]}


def test_no_exported_edge_ever_names_a_node_the_export_omitted(world):
	"""The invariant behind every filter case: no dangling endpoint, ever."""
	store = world["store"]
	four_relations(store)
	for scope in ({"status": "open"}, {"status": "closed"},
	              {"status": "open", "team": "lang"},
	              {"status": "all", "changed_from": "2000-01-01T00:00:00Z",
	               "changed_until": "2100-01-01T00:00:00Z"}):
		graph = projection.work_graph(store, **scope)
		present = {one["id"] for one in graph["nodes"]}
		for edge in graph["edges"]:
			assert edge["source"] in present and edge["target"] in present, \
				(scope, edge)


def test_a_team_filter_keeps_the_cross_team_endpoint_as_context(world):
	"""The team boundary is a SCOPE, not a wall — the open-graph ruling."""
	store = world["store"]
	mine = make(store, "ours", team="lang")
	theirs = make(store, "theirs", team="push", kind="bug", author="sl")
	depend(store, mine, theirs)
	graph = projection.work_graph(store, status="open", team="lang")
	assert node(graph, theirs)["selected"] is False
	assert node(graph, theirs)["team"] == "push"
	assert node(graph, mine)["selected"] is True


# -- 4. a closed consumer stays, even though `links.blocks` hides it -----------


def test_a_closed_consumer_remains_in_the_current_graph(world):
	"""The export is the GRAPH; `links` is an operator drill.

	`links.blocks` deliberately hides closed consumers, because "who is still
	waiting on me" is a question about live work. That makes it the wrong
	source for an export, and this case is the difference stated as a value: a
	full export that inherited the drill's omission would silently lose every
	dependency whose consumer has finished.
	"""
	store = world["store"]
	blocker = make(store, "the blocker")
	consumer = make(store, "the consumer that finishes")
	depend(store, consumer, blocker)
	finish(store, consumer)
	# The drill hides it, and that is correct behaviour for the drill.
	assert consumer not in {one["id"] for one in
	                        projection.links(store, blocker)["blocks"]}
	# The export keeps it.
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	assert ("dependency", blocker, consumer) in {
		(edge["relation"], edge["source"], edge["target"])
		for edge in graph["edges"]}


def test_a_removed_dependency_is_absent_because_this_is_not_history(world):
	"""The other half of the same rule: current, not audit."""
	store = world["store"]
	blocker = make(store, "the blocker")
	consumer = make(store, "the consumer")
	depend(store, consumer, blocker)
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	assert (blocker, consumer) in {(edge["source"], edge["target"])
	                               for edge in edges_of(graph, "dependency")}
	tr.remove_dependency(store, consumer, blocker, actor_team="lang",
	                     actor="ada", rationale="no longer required")
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until="2100-01-01T00:00:00Z")
	assert (blocker, consumer) not in {(edge["source"], edge["target"])
	                                   for edge in edges_of(graph,
	                                                        "dependency")}


# -- 5. beyond every existing UI cap, complete and uncapped -------------------


def test_more_than_five_hundred_nodes_export_whole_with_no_continuation(world):
	"""COMPLETE-OR-REFUSE, past the caps every other view carries.

	`tree` stops at three containment levels, `dependency_neighborhood` at 200
	rendered occurrences, and the pager at `MAX_PAGE` 500. An export that
	inherited any of them would hand back a partial graph with nothing in it
	saying so, which is the one failure this format cannot survive.
	"""
	store = world["store"]
	root = make(store, "the root")
	children = [make(store, f"child {index}", parent=root)
	            for index in range(520)]
	for index in range(0, 420, 2):
		depend(store, children[index], children[index + 1])
	graph = projection.work_graph(store, status="open")
	assert graph["counts"]["nodes"] > 500
	assert graph["counts"]["edges"] > 200
	assert len(graph["nodes"]) == graph["counts"]["nodes"]
	assert len(graph["edges"]) == graph["counts"]["edges"]
	mine = {edge["source"] for edge in edges_of(graph, "containment")}
	assert len([edge for edge in edges_of(graph, "containment")
	            if edge["source"] == root]) == 520
	assert len([edge for edge in edges_of(graph, "dependency")
	            if edge["source"] in set(children)]) == 210
	# NO TRUNCATION VOCABULARY AT ALL. Its absence is the promise; a member
	# that existed and happened to be false would be a promise with an
	# exception.
	for absent in ("next_after", "truncated", "deeper", "limit", "page",
	               "overflow", "omitted", "total"):
		assert absent not in graph, absent
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	assert text.count(" -> ") == graph["counts"]["edges"]


# -- 6. one snapshot, never a stitch of several -------------------------------


def test_the_snapshot_sequence_is_sampled_inside_the_transaction(world):
	"""Deterministically, at the connection -- not by winning a race.

	The interleaved-writer case below establishes the same property end to
	end, but it can only SEE a sequence sampled after the rollback when a
	commit happens to land in the microseconds between the two. Measured: the
	mutation that moves the sample outside the snapshot is caught when that
	case runs alone and missed when it runs beside the others. A guard whose
	detection is a coin flip is not a guard.

	So the sample is observed where it happens. `last_seq` reads the sequence
	table, and this records whether a transaction was open when it did.
	"""
	store = world["store"]
	make(store, "anything")
	seen = []
	real = store.conn

	class Watched:
		def execute(self, statement, *rest):
			if "FROM sequence" in statement:
				seen.append(real.in_transaction)
			return real.execute(statement, *rest)

		def __getattr__(self, name):
			return getattr(real, name)

	store.conn = Watched()
	try:
		projection.work_graph(store, status="open")
	finally:
		store.conn = real
	assert seen, "the snapshot sequence was never read"
	assert all(seen), "the sequence was sampled outside the export's snapshot"


@pytest.mark.serial
def test_an_interleaved_writer_lands_wholly_before_or_after_the_export(world):
	"""THE DEFECT THAT MADE THIS WORK NECESSARY, driven for real.

	An exporter assembled from repeated `links` reads observes a different
	database state per call, so a writer running alongside it can appear in
	some edges and not in others -- a graph of a moment that never existed.
	This drives a REAL second process committing throughout, and asserts every
	export is internally consistent with exactly one state.

	Consistency is checked by RE-DERIVING the expected node set from the
	sequence each export names, rather than by counting: a count could match by
	coincidence, and the claim is that the nodes, edges, counts and
	`snapshot_seq` all describe one instant.

	IT READS UNTIL THE WRITER HAS ACTUALLY MOVED THE AUTHORITY, under a
	deadline. My first version took a fixed twelve exports, and over a small
	database all twelve finished before the writer's first commit -- so it was
	a consistency proof about a quiet store that would have passed for an
	exporter with no snapshot discipline at all. The loop is what makes the
	race real; the deadline is what keeps a stuck writer a failure.
	"""
	store = world["store"]
	# Enough rows that one export is not instantaneous, so the writer has a
	# window to commit inside.
	for index in range(300):
		make(store, f"pre-existing {index}")
	writer = subprocess.Popen(
		[sys.executable, "-c", WRITER, world["database"]],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE,
		env={**os.environ, "PYTHONPATH": os.path.join(
			os.path.dirname(os.path.dirname(os.path.dirname(
				os.path.abspath(__file__)))), "src")})
	graphs = []
	seen = set()
	deadline = time.monotonic() + 60
	try:
		while len(seen) < 3 and time.monotonic() < deadline:
			graph = projection.work_graph(store, status="open")
			graphs.append(graph)
			seen.add(graph["snapshot_seq"])
	finally:
		writer.terminate()
		_out, errors = writer.communicate(timeout=60)
	assert len(seen) >= 3, (
		f"the writer committed {len(seen)} distinct states in 60s; nothing "
		f"was raced. writer stderr: {errors.decode()[-600:]}")
	for graph in graphs:
		# Every node is at or before the sequence this export names, and every
		# Work at or before it that matches the scope is present. Neither
		# direction alone would catch a stitch; together they say "exactly one
		# state".
		assert all(one["created_seq"] <= graph["snapshot_seq"]
		           for one in graph["nodes"])
		expected = {row["id"] for row in store.conn.execute(
			"SELECT id FROM work WHERE status='open' AND created_seq<=?",
			(graph["snapshot_seq"],))}
		present = {one["id"] for one in graph["nodes"] if one["selected"]}
		assert present == expected, graph["snapshot_seq"]
		assert graph["counts"]["nodes"] == len(graph["nodes"])
		assert graph["counts"]["edges"] == len(graph["edges"])
		assert graph["counts"]["selected_nodes"] == len(present)


WRITER = """
import sys, time
import baton_work as bw
from baton_work import transitions as tr
store = bw.Authority(sys.argv[1])
index = 0
while True:
    try:
        tr.create_work(store, team="lang", kind="bug",
                       title=f"racer {index}", origin="self-initiated",
                       classification="suspected-defect", author="ada",
                       body="written during an export")
    except Exception:
        time.sleep(0.01)
    index += 1
    time.sleep(0.005)
"""


# -- 7. determinism, across repetitions and across participants ---------------


def test_an_unchanged_snapshot_renders_byte_identical_dot(world, capsys):
	"""Two exports of one unchanged authority are the same bytes.

	Byte equality rather than structural equality, because the promise is that
	a `.dot` file can be diffed and checksummed. Structural equality would
	pass for a renderer that reordered attributes on every run.
	"""
	store = world["store"]
	four_relations(store)
	first, _ = run(capsys, world["config"], "work-graph", "format=dot",
	               raw=True)
	second, _ = run(capsys, world["config"], "work-graph", "format=dot",
	                raw=True)
	assert first == second
	assert hashlib.sha256(first.encode("utf-8")).hexdigest() == \
		hashlib.sha256(second.encode("utf-8")).hexdigest()


def test_two_participants_render_the_same_bytes(world, capsys):
	"""The export is about the AUTHORITY, not about who asked.

	`New`, attention and obligations are per-viewer; a graph is not. If any
	viewer-dependent fact leaked into a node the two documents would differ
	here, and a checksum published by one operator would be wrong for another.
	"""
	store = world["store"]
	four_relations(store)
	mine, _ = run(capsys, world["config"], "work-graph", "format=dot",
	              participant="lang.ada", raw=True)
	theirs, _ = run(capsys, world["config"], "work-graph", "format=dot",
	                participant="lang.grace", raw=True)
	assert mine == theirs
	assert "lang.ada" not in mine and "grace" not in mine


def test_the_document_carries_no_instant_participant_or_path(world, capsys):
	"""Nothing that would make two identical snapshots differ."""
	store = world["store"]
	four_relations(store)
	text, _ = run(capsys, world["config"], "work-graph", "format=dot",
	              raw=True)
	assert world["config"] not in text
	assert os.path.dirname(world["config"]) not in text
	assert "participant" not in text
	assert "generated" not in text.lower()


def test_the_repeated_json_projection_is_deterministic(world):
	store = world["store"]
	four_relations(store)
	first = projection.work_graph(store, status="open")
	second = projection.work_graph(store, status="open")
	assert json.dumps(first, sort_keys=True) == \
		json.dumps(second, sort_keys=True)
	assert [one["id"] for one in first["nodes"]] == \
		sorted((one["id"] for one in first["nodes"]),
		       key=lambda work_id: (node(first, work_id)["created_seq"],
		                            work_id))


def test_every_attribute_list_is_lexicographic(world, capsys):
	"""Ordering that is decided rather than inherited from a dict."""
	store = world["store"]
	four_relations(store)
	text, _ = run(capsys, world["config"], "work-graph", "format=dot",
	              raw=True)
	for line in text.splitlines():
		if "[" not in line:
			continue
		names = [chunk.split("=")[0].strip()
		         for chunk in line[line.index("[") + 1:-1].split(", ")]
		assert names == sorted(names), line
	# AND THE GRAPH ATTRIBUTE BLOCK, which is a different list emitted by
	# different code. The case checked only the bracketed lists until the
	# mutation pass showed that shuffling the graph attributes changed nothing
	# any assertion could see.
	block = [line.strip().split("=")[0] for line in text.splitlines()
	         if line.startswith("\t") and "[" not in line
	         and "->" not in line and "=" in line]
	assert block == sorted(block), block
	assert len(block) >= 10, block


# -- 8. hostile titles neither inject syntax nor trigger escString ------------


# TITLES THE AUTHORITY WILL ACTUALLY STORE, and the list is shorter than I
# assumed. `validate_subject` refuses a literal newline or carriage return in a
# Work title -- and refuses NOTHING ELSE here. A bare TAB, a NUL, a
# right-to-left override and U+2028/U+2029 are all storable, so the renderer's
# visibility rule is load-bearing for REAL titles rather than hypothetical
# ones. U+2028 is the sharpest of them: it is a line break to a great many
# consumers, and the authority's single-line check does not see it.
HOSTILE = [
	('a "quoted" title', "plain double quotes"),
	("back\\slash", "one backslash"),
	("\\N and \\G and \\E and \\T and \\H and \\L", "escString substitutions"),
	("\\n \\l \\r", "escString line breaks"),
	('"] ; injected [label="pwned', "a statement-terminating attempt"),
	("# leading comment marker", "a comment marker"),
	("// double slash and /* block */", "the other comment markers"),
	("tab\there", "a bare tab"),
	("nul\x00inside", "a NUL"),
	("‮rightto-left-override", "a bidirectional override"),
	(" line  paragraph", "the Unicode separators"),
	("café — 日本語 — Ω", "ordinary non-ASCII"),
	("{ subgraph } -> \"x\"", "braces and an arrow"),
]

# What the authority refuses at creation. The renderer is still held to them,
# because it is a separate boundary and a later relaxation of the title rule
# must not silently become a DOT-injection defect.
UNSTORABLE = [
	("line\nbreak", "a real newline"),
	("carriage\rreturn", "a real carriage return"),
]


@pytest.mark.parametrize("title,why", HOSTILE, ids=[why for _t, why in HOSTILE])
def test_a_hostile_title_stays_one_node_statement(world, title, why):
	"""Whatever the title contains, it is DATA and never structure.

	The check is deliberately not "the output looks right": it is that the
	node's statement is exactly one line, that the document's line count is
	what the graph's shape predicts, and that the exact original bytes survive
	in base64. A title that could add, split or terminate a statement would
	fail at least one of those.
	"""
	store = world["store"]
	work_id = make(store, title)
	graph = projection.work_graph(store, status="open")
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	statements = [line for line in text.splitlines()
	              if line.startswith(f'\t"{work_id}" [')]
	assert len(statements) == 1, text
	# The document is exactly: the opening line, the graph attributes, one
	# line per node, one per edge, and the closing brace.
	graph_attributes = len([line for line in text.splitlines()
	                        if line.startswith("\tbaton_")
	                        or line.startswith("\tcharset")])
	assert len(text.splitlines()) == (
		1 + graph_attributes + graph["counts"]["nodes"]
		+ graph["counts"]["edges"] + 1)
	assert text.splitlines()[-1] == "}"
	carried = statements[0].split('baton_title_b64="')[1].split('"')[0]
	# AGAINST WHAT THE AUTHORITY HOLDS, not against what this case typed.
	# `validate_subject` calls `str.strip()`, and Python strips U+2028 as
	# whitespace -- so a title beginning with one is STORED without it. The
	# export's obligation is to reproduce the stored title exactly; comparing
	# to the input would be asserting that the authority does not normalize,
	# which is a different Work's rule and not true.
	assert base64.b64decode(carried).decode("utf-8") == node(graph,
	                                                         work_id)["title"]


def test_escstring_sequences_cannot_reach_graphviz_as_substitutions(world):
	"""`\\N` in a title must render as two characters, not as the node name.

	Graphviz expands `\\N`, `\\G`, `\\E`, `\\T`, `\\H` and `\\L` inside label
	values. The renderer doubles every user backslash first, so the emitted
	text carries `\\\\N` -- which Graphviz renders as a literal backslash
	followed by `N`. Asserting the emitted bytes is the only way to check
	this without running Graphviz, which this repository deliberately does not
	depend on.
	"""
	store = world["store"]
	work_id = make(store, "\\N \\G \\E \\T \\H \\L \\n \\l \\r")
	graph = projection.work_graph(store, status="open")
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	statement = next(line for line in text.splitlines()
	                 if line.startswith(f'\t"{work_id}" ['))
	label = statement.split('label="')[1].split('"')[0]
	for sequence in ("N", "G", "E", "T", "H", "L", "n", "l", "r"):
		assert f"\\\\{sequence}" in label, (sequence, label)
		# And no BARE one survives: a single backslash before the letter is
		# exactly the substitution this protects against.
		assert not _has_bare_escape(label, sequence), (sequence, label)


def _has_bare_escape(text: str, letter: str) -> bool:
	"""True when `\\<letter>` appears preceded by an EVEN number of
	backslashes — that is, when the backslash before it is not itself
	escaped, which is precisely when Graphviz would substitute."""
	for index, char in enumerate(text):
		if char != letter or index == 0 or text[index - 1] != "\\":
			continue
		run_length = 0
		back = index - 1
		while back >= 0 and text[back] == "\\":
			run_length += 1
			back -= 1
		if run_length % 2 == 1:
			return True
	return False


@pytest.mark.parametrize("title,why", UNSTORABLE,
                         ids=[why for _t, why in UNSTORABLE])
def test_a_title_the_authority_refuses_is_still_safe_to_render(world, title,
                                                               why):
	"""The renderer holds even for text the store will not accept today.

	`validate_subject` refuses these, so they cannot arrive through
	`create_work` -- which is exactly why the guard belongs at the renderer as
	well. A boundary that is safe only because a DIFFERENT boundary filters
	its input is one relaxation away from not being safe at all.
	"""
	store = world["store"]
	with pytest.raises(bw.WorkError, match="single line"):
		make(store, title)
	real = make(store, "a storable title")
	graph = projection.work_graph(store, status="open")
	graph = dict(graph)
	graph["nodes"] = [dict(one, title=title) if one["id"] == real else one
	                  for one in graph["nodes"]]
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	statements = [line for line in text.splitlines()
	              if line.startswith(f'\t"{real}" [')]
	assert len(statements) == 1, text
	carried = statements[0].split('baton_title_b64="')[1].split('"')[0]
	assert base64.b64decode(carried).decode("utf-8") == title


def test_a_control_character_never_reaches_the_document(world):
	"""Not only in `label` — in EVERY value.

	The first version of the renderer made text visible at the label alone, so
	a raw tab or newline still reached `baton_title`. One rule at one owner
	instead, and this case is what holds it there: it walks every line of the
	whole document rather than one attribute of one statement.
	"""
	store = world["store"]
	for title, _why in HOSTILE:
		make(store, title)
	graph = projection.work_graph(store, status="open")
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	import unicodedata
	for line in text.splitlines():
		body = line.lstrip("\t")
		bad = [char for char in body
		       if unicodedata.category(char) in ("Cc", "Cf", "Cs", "Co",
		                                         "Zl", "Zp")]
		assert not bad, (line, [hex(ord(char)) for char in bad])


# -- 9. refusals emit no DOT at all -------------------------------------------


def test_a_malformed_operand_refuses_with_empty_stdout(world, capsys):
	"""Empty rather than partial: an operator's `> work.dot` is a real file.

	A refusal that had already written a plausible prefix would leave a
	syntactically valid-looking graph on disk, and the exit status is not in
	the file.
	"""
	for operands in (("work-graph", "status=bogus"),
	                 ("work-graph", "format=svg"),
	                 ("work-graph", "format=dot", "team=nope"),
	                 ("work-graph", "format=dot", "status=all"),
	                 ("work-graph", "format=dot", "status=all",
	                  "changed-from=2026-01-01T00:00:00Z"),
	                 ("work-graph", "format=dot", "status=all",
	                  "changed-from=2026-01-01T00:00:00Z",
	                  "changed-until=2026-01-01T00:00:00Z"),
	                 ("work-graph", "format=dot", "status=all",
	                  "changed-from=2026-02-01T00:00:00Z",
	                  "changed-until=2026-01-01T00:00:00Z"),
	                 ("work-graph", "format=dot", "status=open",
	                  "changed-from=2026-01-01", "changed-until=2026-02-01"),
	                 # A COMPLETE DATE-TIME CARRYING NO OFFSET, which is the
	                 # spelling the offset requirement actually exists to
	                 # refuse. Measured: the bare-date case above fails the
	                 # grammar for a different reason (no time part at all), so
	                 # making the offset optional changed nothing any case
	                 # could see.
	                 ("work-graph", "format=dot", "status=open",
	                  "changed-from=2026-01-01T00:00:00",
	                  "changed-until=2026-02-01T00:00:00")):
		code = cli.main(["--config", world["config"], "--participant",
		                 "lang.ada", *operands])
		captured = capsys.readouterr()
		assert code == 1, operands
		assert captured.out == "", (operands, captured.out[:200])
		assert json.loads(captured.err)["error"], operands


def test_time_bounds_accept_only_rfc3339_spelling(world, capsys):
	"""`datetime.fromisoformat` accepts a larger language than RFC 3339.

	A space separator, ISO week date and basic date/time are all valid inputs to
	that Python parser and none is the approved public grammar. Each must refuse
	before raw DOT reaches stdout rather than normalize a different language as
	though the operator had supplied RFC 3339.
	"""
	for value in ("2026-01-01 00:00:00Z",
	              "2026-W01-1T00:00:00Z",
	              "20260101T000000Z"):
		code = cli.main([
			"--config", world["config"], "--participant", "lang.ada",
			"work-graph", "format=dot", "status=all",
			f"changed-from={value}",
			"changed-until=2027-01-01T00:00:00Z"])
		captured = capsys.readouterr()
		assert code == 1, value
		assert captured.out == "", (value, captured.out[:200])
		assert "RFC 3339" in json.loads(captured.err)["error"]


def test_the_dot_branch_writes_once_and_only_a_whole_document(world,
                                                              monkeypatch):
	"""Nothing reaches stdout until the entire document exists.

	The refusal cases above prove stdout is EMPTY when the projection refuses
	-- but they cannot see a renderer that streamed a prefix and then raised,
	because by then the projection has already succeeded. So this observes the
	write itself: exactly one call, carrying a string that both opens and
	closes the digraph.

	MEASURED: without this, moving the opening line to a separate earlier
	`write` changed nothing any case could see.
	"""
	store = world["store"]
	four_relations(store)
	writes = []
	real = sys.stdout.write
	monkeypatch.setattr(sys.stdout, "write",
	                    lambda text: (writes.append(text), real(text))[1])
	code = cli.main(["--config", world["config"], "--participant", "lang.ada",
	                 "work-graph", "format=dot"])
	assert code == 0
	assert len(writes) == 1, writes[:3]
	assert writes[0].startswith('digraph "baton_work" {')
	assert writes[0].endswith("}\n")


def test_a_damaged_endpoint_refuses_the_whole_export(world):
	"""No fallback omits an offending edge.

	The store cannot produce this today -- every endpoint column is a foreign
	key -- so it is driven at the validator, which is the boundary that has to
	hold when the renderer is called by something other than this projection.
	"""
	store = world["store"]
	work_id = make(store, "present")
	with pytest.raises(bw.WorkError, match="not in the exported graph"):
		projection.validate_work_graph(a_result(
			[sample_node(work_id)],
			[projection._export_edge("dependency", work_id,
			                         "fefefefe-W9999", 1)]))


def test_a_duplicate_typed_edge_refuses(world):
	"""Unrepresentable through the authority, refused at the boundary anyway.

	`edges` is keyed `(work, blocker)` and the other three families are
	single-valued columns, so this cannot arrive from the store. The renderer
	and the projection are separate boundaries, and neither may assume the
	other built its input -- so the rule is stated where it can be enforced
	rather than left as a property of today's schema.
	"""
	store = world["store"]
	first = make(store, "a")
	second = make(store, "b")
	nodes = [sample_node(first), sample_node(second)]
	edge = projection._export_edge("dependency", first, second, 1)
	with pytest.raises(bw.WorkError, match="appears twice"):
		projection.validate_work_graph(a_result(nodes, [edge, dict(edge)]))
	# AND A NODE NAMED TWICE, which the validator now owns as well: a caller
	# that had already built a mapping would have collapsed the pair before
	# anything could object, and an export naming one Work twice is as broken
	# as one naming an endpoint it never described.
	with pytest.raises(bw.WorkError, match="twice; one Work is one node"):
		projection.validate_work_graph(
			a_result([sample_node(first), sample_node(first)], []))


def test_an_invalid_relation_or_predicate_refuses(world):
	store = world["store"]
	work_id = make(store, "a")
	nodes = [sample_node(work_id)]
	with pytest.raises(bw.WorkError, match="not a Work-graph relation"):
		projection.validate_work_graph(a_result(nodes, [
			{"relation": "vibes", "predicate": "blocks", "source": work_id,
			 "target": work_id, "relation_seq": 1, "via_obligation": None}]))
	with pytest.raises(bw.WorkError, match="spells its predicate"):
		projection.validate_work_graph(a_result(nodes, [
			{"relation": "dependency", "predicate": "contains",
			 "source": work_id, "target": work_id, "relation_seq": 1,
			 "via_obligation": None}]))


def test_the_renderer_refuses_a_malformed_envelope():
	"""The renderer owns its input; it is not only ever called by us."""
	for bad, why in ((None, "not a document"),
	                 ({}, "no members at all"),
	                 ({"authority_uuid": "x", "projection_version": "1",
	                   "protocol_version": 1, "snapshot_seq": 1,
	                   "result": []}, "a result that is not a document"),
	                 ({"authority_uuid": "x", "projection_version": "1",
	                   "protocol_version": 1, "snapshot_seq": 1,
	                   "result": {"scope": {}, "counts": {}, "nodes": {},
	                              "edges": []}}, "nodes that are not a list")):
		with pytest.raises(bw.WorkError):
			dot.render_work_graph_dot(bad)


def test_the_renderer_revalidates_edge_integrity(world):
	"""The renderer is a boundary, not a projection-only private helper.

	The projection validator cannot protect another structured caller. The DOT
	renderer must independently refuse duplicate typed edges and a missing
	endpoint instead of emitting a complete-looking false graph.
	"""
	store = world["store"]
	first = make(store, "first")
	second = make(store, "second")
	depend(store, second, first)
	graph = projection.work_graph(store)
	edge = edges_of(graph, "dependency")[0]

	duplicate = dict(graph, edges=[edge, dict(edge)])
	duplicate["counts"] = dict(graph["counts"], edges=2)
	with pytest.raises(bw.WorkError, match="appears twice"):
		dot.render_work_graph_dot(envelope_for(store, duplicate))

	dangling = dict(graph, nodes=[node(graph, first)])
	dangling["counts"] = {"selected_nodes": 1, "context_nodes": 0,
	                      "nodes": 1, "edges": 1}
	with pytest.raises(bw.WorkError, match="not in the exported graph"):
		dot.render_work_graph_dot(envelope_for(store, dangling))

	forged = dict(graph, edges=[dict(edge, predicate="contains")])
	with pytest.raises(bw.WorkError, match="spells its predicate"):
		dot.render_work_graph_dot(envelope_for(store, forged))




def test_rfc3339_spellings_the_contract_does_accept(world, capsys):
	"""The other half of the strict-grammar rule.

	A grammar check that only ever refuses is indistinguishable from a
	boundary that refuses everything, so the accepted spellings are named:
	lower-case `t` and `z` (RFC 3339 §5.6 makes both case-insensitive),
	fractional seconds, and a numeric offset which must normalize to the same
	UTC instant as its `Z` equivalent.
	"""
	store = world["store"]
	make(store, "anything")
	same = []
	for value in ("2026-08-27T00:00:00Z", "2026-08-27t00:00:00z",
	              "2026-08-27T00:00:00.000Z", "2026-08-26T20:00:00-04:00",
	              "2026-08-27T04:00:00+04:00"):
		graph = projection.work_graph(store, status="all",
		                              changed_from=value,
		                              changed_until="2100-01-01T00:00:00Z")
		same.append(graph["scope"]["changed_from"])
	assert len(set(same)) == 1, same
	# The canonical form carries no invented precision: a whole second is
	# spelled as one. Second review [P1] moved this off `datetime`'s fixed
	# microseconds, so `.000` no longer becomes `.000000`.
	assert same[0] == "2026-08-27T00:00:00Z"
	# ...and an arbitrary fraction survives intact, with only trailing zeros
	# canonicalized away.
	for spelled, canonical in (
			("2026-08-27T00:00:00.0000001Z", "2026-08-27T00:00:00.0000001Z"),
			("2026-08-27T00:00:00.10Z", "2026-08-27T00:00:00.1Z"),
			("2026-08-27T00:00:00.000Z", "2026-08-27T00:00:00Z")):
		graph = projection.work_graph(store, status="all",
		                              changed_from=spelled,
		                              changed_until="2100-01-01T00:00:00Z")
		assert graph["scope"]["changed_from"] == canonical, spelled


def test_a_well_shaped_instant_that_names_no_moment_refuses(world):
	"""The regex has no opinion about February 30th; the parse does.

	Both checks are needed and neither subsumes the other -- which is why the
	grammar check did not replace the parse.
	"""
	store = world["store"]
	for value in ("2026-02-30T00:00:00Z", "2026-13-01T00:00:00Z",
	              "2026-08-27T25:00:00Z"):
		with pytest.raises(bw.WorkError, match="names no moment"):
			projection.work_graph(store, status="all", changed_from=value,
			                      changed_until="2100-01-01T00:00:00Z")


def test_rfc3339_fractional_instants_do_not_collapse_at_microseconds(world):
	"""RFC 3339 permits one or more fractional-second digits.

	Two different approved bounds must remain two different normalized scopes.
	`datetime` has only microsecond precision and silently truncates later
	digits, so delegating canonicalization to it can turn distinct instants into
	the same exported question.
	"""
	store = world["store"]
	first = projection.work_graph(
		store, status="all", changed_from="2026-08-27T00:00:00.0000001Z",
		changed_until="2100-01-01T00:00:00Z")
	second = projection.work_graph(
		store, status="all", changed_from="2026-08-27T00:00:00.0000009Z",
		changed_until="2100-01-01T00:00:00Z")
	assert first["scope"]["changed_from"] != second["scope"]["changed_from"]


def test_the_configured_team_is_read_inside_the_named_snapshot(world):
	"""Review [P2]: every authority read that admits the export is in the
	transaction the export names.

	OBSERVED AT THE CONNECTION, not inferred from where the call sits in the
	source. The teams query is recorded together with whether a transaction
	was open when it ran, so moving the check back outside the snapshot fails
	here rather than passing on a reading of the code.
	"""
	store = world["store"]
	make(store, "anything")
	seen = []
	real = store.conn

	class Watched:
		"""A proxy AROUND the connection, because `sqlite3.Connection`
		attributes are read-only and cannot be patched in place."""

		def execute(self, statement, *rest):
			if "FROM teams" in statement:
				seen.append(real.in_transaction)
			return real.execute(statement, *rest)

		def __getattr__(self, name):
			return getattr(real, name)

	store.conn = Watched()
	try:
		projection.work_graph(store, team="lang", status="open")
	finally:
		store.conn = real
	assert seen, "the configured-team fact was never read"
	assert all(seen), "the team was admitted outside the export's snapshot"


def test_the_renderer_and_the_projection_share_one_validator(world):
	"""ONE ENFORCEMENT, not two statements of one rule.

	The reviewer's requirement was not "add checks to the renderer" but "one
	enforcement on every renderer input". A second copy would agree with the
	first until it didn't, so this asserts the renderer calls the projection's
	validator rather than restating its rules -- by AST, because a duplicated
	rule that happened to behave identically today would pass any behavioural
	check.
	"""
	import ast
	import pathlib
	tree = ast.parse(pathlib.Path(dot.__file__).read_text())
	called = {node_.func.id for node_ in ast.walk(tree)
	          if isinstance(node_, ast.Call)
	          and isinstance(node_.func, ast.Name)}
	assert "validate_work_graph" in called
	# And the rule TEXT lives in exactly one module.
	for phrase in ("appears twice", "never described",
	               "spells its predicate"):
		assert phrase not in pathlib.Path(dot.__file__).read_text(), phrase
		assert phrase in pathlib.Path(projection.__file__).read_text(), phrase


def test_the_renderer_owns_structured_member_types(world):
	"""Presence is not ownership when a value changes the document's meaning.

	A string ``"false"`` is truthy in Python and would be rendered as selected,
	while a non-text title currently escapes as ``AttributeError`` during
	base64 encoding. Both are malformed structured inputs and must be explicit
	Work refusals before any DOT is composed.
	"""
	store = world["store"]
	make(store, "one")
	graph = projection.work_graph(store)
	for member, value in (("selected", "false"), ("title", 7)):
		nodes = [dict(one, **{member: value}) for one in graph["nodes"]]
		bad = dict(graph, nodes=nodes)
		with pytest.raises(bw.WorkError, match=member):
			dot.render_work_graph_dot(envelope_for(store, bad))





def test_a_bound_orders_correctly_across_the_fraction_boundary(world):
	"""The trap the ordering key exists to avoid, measured as selection.

	Canonical instants CANNOT be compared as text: `...00:00:00Z` and
	`...00:00:00.0000001Z` compare `Z` against `0`, so the whole second sorts
	AFTER the instant a tenth of a microsecond later. A range built on text
	comparison therefore selects the wrong side of that boundary while looking
	entirely reasonable.

	Driven through selection rather than through the key, because the key is an
	implementation detail and the question is which Work the operator gets.
	"""
	store = world["store"]
	work_id = make(store, "the only one")
	stamp = store.conn.execute(
		"SELECT last_changed_at FROM work WHERE id=?",
		(work_id,)).fetchone()["last_changed_at"]
	whole = stamp.split(".")[0] + "Z"

	# The row is at `whole` plus some fraction, so a range STARTING at the
	# whole second must contain it...
	inside = projection.work_graph(store, status="all", changed_from=whole,
	                               changed_until="2100-01-01T00:00:00Z")
	assert work_id in {one["id"] for one in inside["nodes"] if one["selected"]}
	# ...and a range ENDING at the whole second must not, because the bound is
	# exclusive and the row is later.
	outside = projection.work_graph(store, status="all",
	                                changed_from="2000-01-01T00:00:00Z",
	                                changed_until=whole)
	assert work_id not in {one["id"] for one in outside["nodes"]
	                       if one["selected"]}
	# And the fraction really is what decides it: the same range widened by
	# one microsecond past the row's own instant contains it again.
	assert projection._export_ordering(whole) < \
		projection._export_ordering(projection._export_instant(
			stamp, "a stored last_changed_at"))


def test_every_fixed_member_is_owned_by_type_not_only_by_presence(world):
	"""The WHOLE schema, not the two values the review happened to find.

	A pair of one-off guards would leave every other member exactly as it was
	and would have to be extended by whoever next notices one. So each fixed
	member is corrupted in turn and each must refuse by name.
	"""
	store = world["store"]
	work_id = make(store, "one")
	graph = projection.work_graph(store)
	edge = projection._export_edge("dependency", work_id, work_id, 1)

	# TWO WRONG VALUES PER TYPE, and the second one is the point for `int`.
	# `bool` is a subclass of `int` in Python, so an `isinstance` check would
	# accept `created_seq=True` -- a sequence that is a boolean. Measured: with
	# only a string in the table, relaxing the exact-type test to `isinstance`
	# changed nothing any case could see.
	wrong = {str: (7, True), int: ("seven", True), bool: ("false", 1)}
	for member in projection.GRAPH_NODE_MEMBERS:
		wanted, _nullable = projection._MEMBER_TYPES[member]
		for value in wrong[wanted]:
			bad = dict(graph, edges=[],
			           nodes=[sample_node(work_id, **{member: value})])
			with pytest.raises(bw.WorkError, match=member):
				dot.render_work_graph_dot(envelope_for(store, bad))
	for member in projection.GRAPH_EDGE_MEMBERS:
		wanted, _nullable = projection._MEMBER_TYPES[member]
		for value in wrong[wanted]:
			bad = dict(graph, nodes=[sample_node(work_id)],
			           edges=[dict(edge, **{member: value})])
			with pytest.raises(bw.WorkError, match=member):
				dot.render_work_graph_dot(envelope_for(store, bad))


@pytest.mark.parametrize("member,value", (("status", "bogus"),
                                           ("phase", "review"),
                                           ("outcome", "done")))
def test_the_renderer_owns_the_closed_node_state_vocabularies(world, member,
                                                               value):
	"""A text member still has a domain; type ownership is not enough.

	`status`, `phase` and `outcome` give the node its current-state meaning in
	both the readable label and the machine-readable attributes. A structured
	caller may not invent a fifth phase or a third status and receive
	complete-looking DOT merely because each invention happens to be a string.
	"""
	store = world["store"]
	work_id = make(store, "one")
	graph = projection.work_graph(store)
	bad = dict(graph, edges=[],
	           nodes=[sample_node(work_id, **{member: value})])
	with pytest.raises(bw.WorkError, match=member):
		dot.render_work_graph_dot(envelope_for(store, bad))


def test_every_closed_vocabulary_is_owned_not_only_the_three_found(world):
	"""SIX members carry a closed domain, not the three the review named.

	`origin`, `classification` and `priority` are closed in exactly the same
	way as `status`, `phase` and `outcome`, and each reaches both the readable
	label and a `baton_*` attribute. Validating only the members that happened
	to be found would be the guard-extended-one-at-a-time shape the second
	review already corrected once.

	The vocabularies are ASSERTED to be the authority's own, by identity, so a
	renderer-only copy would fail here rather than drift quietly.
	"""
	from baton_work import transitions as tr
	assert projection._MEMBER_VOCABULARIES == {
		"status": (tr.OPEN, tr.CLOSED), "phase": tr.PHASES,
		"outcome": tr.OUTCOMES, "origin": tr.ORIGINS,
		"classification": tr.CLASSIFICATIONS, "priority": tr.PRIORITIES}

	store = world["store"]
	work_id = make(store, "one")
	graph = projection.work_graph(store)
	for member, allowed in projection._MEMBER_VOCABULARIES.items():
		bad = dict(graph, edges=[],
		           nodes=[sample_node(work_id, **{member: "forged"})])
		with pytest.raises(bw.WorkError, match=member):
			dot.render_work_graph_dot(envelope_for(store, bad))
		# ...and every legitimate value still renders, or the rule would be a
		# way of refusing everything.
		#
		# EACH VALUE IN A STATE THAT CAN LEGALLY HOLD IT. status, phase and
		# outcome are one coupled state since the fourth review, so a phase
		# belongs on an open node and an outcome on a closed one; asking for
		# an open node with an outcome would be testing a combination the
		# projection never emits and the validator rightly refuses.
		for value in allowed:
			if member == "phase":
				node_ = sample_node(work_id, phase=value)
			elif member == "outcome":
				node_ = closed_node(work_id, outcome=value)
			elif member == "status":
				node_ = (sample_node(work_id) if value == tr.OPEN
				         else closed_node(work_id))
			else:
				node_ = sample_node(work_id, **{member: value})
			ok = dict(graph, edges=[], nodes=[node_],
			          counts=one_node_counts(graph))
			assert dot.render_work_graph_dot(envelope_for(store, ok))


@pytest.mark.parametrize("status,phase,outcome,member", (
	("open", None, None, "phase"),
	("open", "queued", "satisfying", "outcome"),
	("closed", "queued", "satisfying", "phase"),
	("closed", None, None, "outcome"),
))
def test_node_state_members_are_valid_as_one_state_not_three_values(
		world, status, phase, outcome, member):
	"""The three closed vocabularies are coupled, not independent fields.

	The approved schema says open Work has one scheduler phase and no outcome;
	terminal Work has one outcome and no phase. Every value here is individually
	type-correct and in-domain, so only validation of the whole node state can
	refuse the impossible combination.
	"""
	store = world["store"]
	work_id = make(store, "one")
	graph = projection.work_graph(store)
	bad = dict(graph, edges=[], nodes=[sample_node(
		work_id, status=status, phase=phase, outcome=outcome)])
	with pytest.raises(bw.WorkError, match=member):
		dot.render_work_graph_dot(envelope_for(store, bad))


def test_only_a_dependency_may_name_obligation_provenance(world):
	"""`via_obligation` belongs to dependency creation, and is null elsewhere."""
	store = world["store"]
	first = make(store, "first")
	second = make(store, "second")
	graph = projection.work_graph(store)
	edge = projection._export_edge("containment", first, second, 1,
	                               via_obligation=7)
	bad = dict(graph, edges=[edge])
	bad["counts"] = dict(graph["counts"], edges=1)
	with pytest.raises(bw.WorkError, match="via_obligation"):
		dot.render_work_graph_dot(envelope_for(store, bad))


@pytest.mark.parametrize("part,pattern", (("status", "status"),
	("closure", "closure"), ("changed_from", "changed[-_]from"),
	("counts", "counts|nodes")))
def test_the_renderer_owns_fixed_scope_and_count_semantics(world, part,
	                                                        pattern):
	"""The renderer promises the whole structured result, not nodes alone."""
	store = world["store"]
	make(store, "one")
	graph = projection.work_graph(store)
	bad = dict(graph)
	if part == "counts":
		bad["counts"] = dict(graph["counts"], nodes=2)
	else:
		value = {"status": "bogus", "closure": "recursive",
		         "changed_from": "yesterday"}[part]
		bad["scope"] = dict(graph["scope"], **{part: value})
	with pytest.raises(bw.WorkError, match=pattern):
		dot.render_work_graph_dot(envelope_for(store, bad))


def test_null_is_accepted_exactly_where_the_contract_allows_it(world):
	"""Null is legal in the two valid STATES, not on three independent fields.

	CORRECTED, and the correction is the point. This case used to assert that
	`phase=None` renders on the helper's OPEN node -- which the confirmed
	schema forbids, because open Work is always in one scheduler phase. It
	passed because the validator treated the three members independently, so my
	case and the code agreed with each other and both disagreed with the
	schema. That is worse than a missing case: a test asserting the wrong thing
	is a defect with a guard in front of it.

	It now exercises the two valid paired states, and holds the line the
	original was reaching for -- that the rule must not become a way of
	refusing every null, which would reject every terminal Work and every
	non-dependency edge.
	"""
	store = world["store"]
	work_id = make(store, "one")
	graph = projection.work_graph(store)
	nullable = {name for name, (_type, allowed)
	            in projection._MEMBER_TYPES.items() if allowed}
	assert nullable == {"phase", "outcome", "via_obligation"}, nullable

	# THE TWO VALID STATES BOTH RENDER: an open node whose `outcome` is null,
	# and a terminal one whose `phase` is null.
	#
	# The edges go with the nodes: replacing the node list alone would leave
	# the fixture's own edges naming endpoints this graph no longer describes,
	# and the case would refuse for a reason it is not about.
	for node_ in (sample_node(work_id), closed_node(work_id)):
		ok = dict(graph, edges=[], nodes=[node_],
		          counts=one_node_counts(graph))
		assert dot.render_work_graph_dot(envelope_for(store, ok))
	# A NULL IN THE OTHER STATE IS REFUSED, which is what makes the two above
	# a contract rather than a coincidence.
	for node_ in (sample_node(work_id, phase=None),
	              closed_node(work_id, outcome=None)):
		bad = dict(graph, edges=[], nodes=[node_],
		           counts=one_node_counts(graph))
		with pytest.raises(bw.WorkError):
			dot.render_work_graph_dot(envelope_for(store, bad))
	# And every member with no nullable domain at all refuses null in either
	# state.
	for member in projection.GRAPH_NODE_MEMBERS:
		if member in nullable:
			continue
		bad = dict(graph, edges=[],
		           nodes=[sample_node(work_id, **{member: None})],
		           counts=one_node_counts(graph))
		with pytest.raises(bw.WorkError, match="always present"):
			dot.render_work_graph_dot(envelope_for(store, bad))





def test_the_renderer_refuses_one_input_per_category_it_claims_to_own(world):
	"""THE DOCSTRING'S LIST, ENFORCED ITEM BY ITEM.

	`render_work_graph_dot` says it owns the scope document, the derived
	counts, every member's presence, type and closed vocabulary, the coupled
	node state, edge provenance and graph topology. Across four review rounds
	every finding against this Work was a sentence like that one being wider
	than the code -- so the sentence is now a table with a case behind it, and
	a category added to the prose without a refusal behind it fails here.

	This is not a substitute for the focused cases above; it is the check that
	the CLAIM and the enforcement have the same shape.
	"""
	store = world["store"]
	first = make(store, "first")
	second = make(store, "second")
	depend(store, second, first)
	graph = projection.work_graph(store)
	edge = edges_of(graph, "dependency")[0]
	one = one_node_counts(graph)

	catalogue = {
		"the scope document":
			dict(graph, scope=dict(graph["scope"], closure="recursive")),
		"the derived counts":
			dict(graph, counts=dict(graph["counts"], edges=99)),
		"member presence":
			dict(graph, edges=[], counts=one,
			     nodes=[{name: value for name, value
			             in sample_node(first).items() if name != "origin"}]),
		"member type":
			dict(graph, edges=[], counts=one,
			     nodes=[sample_node(first, created_seq="one")]),
		"a closed vocabulary":
			dict(graph, edges=[], counts=one,
			     nodes=[sample_node(first, priority="urgent")]),
		"the coupled node state":
			dict(graph, edges=[], counts=one,
			     nodes=[sample_node(first, outcome="satisfying")]),
		"edge provenance":
			dict(graph, edges=[projection._export_edge(
				"containment", first, second, 1, via_obligation=3)]),
		"graph topology":
			dict(graph, edges=[edge, dict(edge)],
			     counts=dict(graph["counts"], edges=2)),
	}
	for category, malformed in catalogue.items():
		with pytest.raises(bw.WorkError):
			dot.render_work_graph_dot(envelope_for(store, malformed))

	# The prose and the table name the same categories. A category added to
	# one and not the other is the drift this case exists to catch.
	import inspect
	prose = inspect.getdoc(dot.render_work_graph_dot) + \
		inspect.getsource(dot.render_work_graph_dot)
	for category in catalogue:
		assert category in prose, category


def test_the_projection_validates_its_own_output(world):
	"""A producer exempt from the rules its consumer enforces is how the two
	come to disagree.

	Observed by counting the calls rather than by reading the source: the
	projection must run the SAME validator on the result it is about to
	answer with.
	"""
	store = world["store"]
	make(store, "one")
	seen = []
	real = projection.validate_work_graph
	try:
		projection.validate_work_graph = lambda result: (
			seen.append(result), real(result))[1]
		answered = projection.work_graph(store)
	finally:
		projection.validate_work_graph = real
	assert len(seen) == 1, seen
	assert seen[0]["nodes"] == answered["nodes"]
	assert seen[0]["counts"] == answered["counts"]
	# The validated document is what the renderer will see -- everything the
	# envelope carries except the snapshot sequence the CLI lifts out.
	assert set(seen[0]) == set(answered) - {"snapshot_seq"}


def test_each_count_is_derived_from_the_arrays_individually(world):
	"""All four, separately: three of them could be right by accident."""
	store = world["store"]
	first = make(store, "first")
	second = make(store, "second")
	depend(store, second, first)
	graph = projection.work_graph(store)
	for name in projection.GRAPH_COUNT_MEMBERS:
		bad = dict(graph, counts=dict(graph["counts"],
		                              **{name: graph["counts"][name] + 1}))
		with pytest.raises(bw.WorkError, match=name):
			dot.render_work_graph_dot(envelope_for(store, bad))
	# A count that is not an integer is refused as such rather than compared.
	bad = dict(graph, counts=dict(graph["counts"], nodes="two"))
	with pytest.raises(bw.WorkError, match="not an integer"):
		dot.render_work_graph_dot(envelope_for(store, bad))


def test_the_scope_document_is_a_fixed_shape(world):
	"""An unknown member is refused, and so is a missing one.

	The scope reaches the DOT graph attributes, where a reader takes it for the
	authoritative description of what the export covers. A document carrying an
	extra member would be describing something this projection does not do.
	"""
	store = world["store"]
	make(store, "one")
	graph = projection.work_graph(store)
	extra = dict(graph, scope=dict(graph["scope"], depth=3))
	with pytest.raises(bw.WorkError, match="depth"):
		dot.render_work_graph_dot(envelope_for(store, extra))
	for name in projection.GRAPH_SCOPE_MEMBERS:
		short = {key: value for key, value in graph["scope"].items()
		         if key != name}
		with pytest.raises(bw.WorkError, match=name):
			dot.render_work_graph_dot(envelope_for(store,
			                                       dict(graph, scope=short)))
	# The bounds are still an interval in the document, not only in the
	# operands: reversed, half-supplied and unparseable all refuse.
	for scope, pattern in (
			({"changed_from": "2026-02-01T00:00:00Z",
			  "changed_until": "2026-01-01T00:00:00Z"}, "not before"),
			({"changed_from": "2026-01-01T00:00:00Z"}, "alone"),
			({"changed_from": "yesterday",
			  "changed_until": "2026-01-01T00:00:00Z"}, "RFC 3339")):
		bad = dict(graph, scope=dict(graph["scope"], **scope))
		with pytest.raises(bw.WorkError, match=pattern):
			dot.render_work_graph_dot(envelope_for(store, bad))


@pytest.mark.parametrize("field,value", (
	("changed_from", "2026-01-01T01:00:00+01:00"),
	("changed_from", "2026-01-01t00:00:00z"),
	("changed_from", "2026-01-01T00:00:00.100Z"),
	("changed_until", "2027-01-01T01:00:00+01:00"),
	("changed_until", "2027-01-01t00:00:00z"),
	("changed_until", "2027-01-01T00:00:00.100Z"),
))
def test_a_structured_scope_carries_the_canonical_utc_instant(world,
	                                                           field, value):
	"""Validation must not admit several bytes for one normalized scope.

	The public operand accepts each spelling, but the projection normalizes it
	to UTC, upper-case separators and a minimal significant fraction. A direct
	structured caller bypassing that normalization must be refused rather than
	produce different DOT metadata for the same approved scope instant.
	"""
	store = world["store"]
	make(store, "one")
	graph = projection.work_graph(store)
	scope = {**graph["scope"], "changed_from": "2026-01-01T00:00:00Z",
	         "changed_until": "2027-01-01T00:00:01Z", field: value}
	bad = dict(graph, scope=scope)
	with pytest.raises(bw.WorkError, match=f"{field}|canonical|UTC"):
		dot.render_work_graph_dot(envelope_for(store, bad))





def test_one_instant_spelled_two_ways_gives_one_document(world, capsys):
	"""THE PROMISE THE CANONICAL RULE EXISTS TO KEEP, end to end.

	`2026-01-01T01:00:00+01:00` and `2026-01-01T00:00:00Z` are one approved
	lower bound. An operator may type either, and both must produce the SAME
	bytes -- because the export is diffed and checksummed, and two files
	differing only in how somebody spelled a timezone would read as two
	different graphs.

	This is the converse of `test_two_scopes_over_one_snapshot_do_not_collide`:
	that one says different scopes must differ, this one says one scope must
	not. Neither implies the other, and the fifth review found the second half
	missing while the first half had been asserted since the opening round.
	"""
	store = world["store"]
	four_relations(store)
	spellings = ("2026-01-01T00:00:00Z", "2026-01-01T01:00:00+01:00",
	             "2026-01-01t00:00:00z", "2026-01-01T00:00:00.000Z")
	documents = set()
	for spelled in spellings:
		text, _err = run(capsys, world["config"], "work-graph", "format=dot",
		                 "status=all", f"changed-from={spelled}",
		                 "changed-until=2027-01-01T00:00:00Z", raw=True)
		documents.add(text)
	assert len(documents) == 1, [len(one) for one in documents]
	assert 'baton_scope_changed_from="2026-01-01T00:00:00Z"' in \
		documents.pop()


def test_the_operand_path_still_accepts_every_legal_spelling(world, capsys):
	"""The canonical rule is the DOCUMENT's, never the operator's.

	A rule that leaked into the operand path would refuse the numeric offset,
	the lower-case separator and the trailing-zero fraction that RFC 3339
	blesses -- turning a determinism guarantee into a usability regression.
	The two paths meet exactly here: the operand accepts every legal spelling
	and normalizes it, and the document then carries only what normalization
	produced.
	"""
	store = world["store"]
	make(store, "one")
	for spelled in ("2026-01-01T00:00:00Z", "2026-01-01T01:00:00+01:00",
	                "2026-01-01t00:00:00z", "2026-01-01T00:00:00.000Z",
	                "2025-12-31T19:00:00-05:00"):
		answered = run(capsys, world["config"], "work-graph", "status=all",
		               f"changed-from={spelled}",
		               "changed-until=2027-01-01T00:00:00Z")
		assert answered["result"]["scope"]["changed_from"] == \
			"2026-01-01T00:00:00Z", spelled
	# ...and the projection's own output satisfies the document rule it
	# imposes on everyone else, which is what makes the two paths one contract
	# rather than two.
	graph = projection.work_graph(store, status="all",
	                              changed_from="2026-01-01T01:00:00+01:00",
	                              changed_until="2027-01-01T00:00:00Z")
	projection._export_scope_document(graph["scope"])



# -- 10. cycles and parallel edges export without traversal -------------------


def test_a_dependency_cycle_exports_rather_than_refusing_or_hanging(world):
	"""A complete export of a DAMAGED topology is exactly what it is for.

	`dependency_neighborhood` refuses a cycle because it walks; this does not
	walk at all, so a cycle is three ordinary rows. Refusing here would deny
	the operator the export precisely when they most need to look at the
	graph.
	"""
	store = world["store"]
	first = make(store, "first")
	second = make(store, "second")
	third = make(store, "third")
	pairs = ((first, second), (second, third), (third, first))
	for consumer, blocker in pairs:
		try:
			depend(store, consumer, blocker)
		except bw.WorkError:
			# The authority may refuse to CREATE the closing edge; the export
			# is still obliged to render whatever the store holds, which is
			# what the assertions below check.
			pass
	graph = projection.work_graph(store, status="open")
	found = {(edge["source"], edge["target"])
	         for edge in edges_of(graph, "dependency")}
	assert found, "no dependency survived; the case proves nothing"
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	assert text.count(" -> ") == len(edges_of(graph))


def test_a_self_referencing_edge_would_render_as_one_statement(world):
	"""A loop is a row like any other; the renderer does not special-case it."""
	store = world["store"]
	work_id = make(store, "alone")
	graph = projection.work_graph(store, status="open")
	graph = dict(graph)
	graph["edges"] = [projection._export_edge("dependency", work_id, work_id, 1)]
	graph["counts"] = dict(graph["counts"], edges=1)
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	assert text.count(f'"{work_id}" -> "{work_id}"') == 1


# -- 11. the read leaves the authority byte-identical -------------------------


@pytest.mark.serial
def test_a_full_export_writes_nothing_to_the_authority(world, capsys):
	"""PURE, proved the blunt way — the same way this repository already
	proves it for the rest of the read side.

	The database file AND its write-ahead log are hashed before and after,
	because a projection that opened a write transaction could leave the file
	untouched while moving the WAL.
	"""
	store = world["store"]
	four_relations(store)
	store.close()

	def fingerprint():
		out = {}
		for suffix in ("", "-wal", "-shm"):
			path = world["database"] + suffix
			out[suffix] = (hashlib.sha256(open(path, "rb").read()).hexdigest()
			               if os.path.exists(path) else None)
		return out

	before = fingerprint()
	run(capsys, world["config"], "work-graph")
	run(capsys, world["config"], "work-graph", "format=dot", raw=True)
	run(capsys, world["config"], "work-graph", "status=closed")
	assert fingerprint() == before
	world["store"] = bw.Authority(world["database"])


# -- 12. no Graphviz, ever ----------------------------------------------------


def test_the_renderer_imports_no_graphviz_and_starts_no_process():
	"""Baton emits DOT; it does not render images and does not need Graphviz.

	Checked by AST over the module's own source rather than by monkeypatching:
	an import that only happens on one branch would be invisible to a test
	that merely called the function once.
	"""
	import ast
	import pathlib
	source = pathlib.Path(dot.__file__).read_text()
	tree = ast.parse(source)
	imported = []
	for node_ in ast.walk(tree):
		if isinstance(node_, ast.Import):
			imported += [alias.name for alias in node_.names]
		elif isinstance(node_, ast.ImportFrom):
			imported.append(node_.module or "")
	for name in imported:
		root = name.split(".")[0]
		assert root in ("base64", "unicodedata", "baton_work", "__future__"), \
			f"the renderer imports {name}"
	# BY AST, NOT BY GREP -- the same correction `test_boundaries` records
	# about itself. The first version of this case scanned the raw source and
	# failed on the module docstring SAYING it starts no subprocess. Read the
	# names the module actually uses.
	used = {node_.id for node_ in ast.walk(tree) if isinstance(node_, ast.Name)}
	used |= {node_.attr for node_ in ast.walk(tree)
	         if isinstance(node_, ast.Attribute)}
	for banned in ("subprocess", "graphviz", "pydot", "system", "popen",
	               "which", "open", "run", "Popen", "check_output"):
		assert banned not in used, f"the renderer uses {banned!r}"


def test_the_export_succeeds_with_no_dot_executable_on_path(world, capsys,
                                                            monkeypatch):
	"""An operator without Graphviz installed still gets their export."""
	store = world["store"]
	four_relations(store)
	monkeypatch.setenv("PATH", "")
	text, _ = run(capsys, world["config"], "work-graph", "format=dot",
	              raw=True)
	assert text.startswith('digraph "baton_work" {')
	assert text.endswith("}\n")


# -- the surface itself -------------------------------------------------------


def test_the_zero_operand_default_is_every_team_and_open_status(world, capsys):
	"""The approver's correction, held to: `open`, not `all`.

	The default is the useful current operational graph. `all` would bury it
	under terminal history, which is why the same ruling made `all` demand an
	explicit interval.
	"""
	store = world["store"]
	answered = run(capsys, world["config"], "work-graph")
	assert answered["result"]["scope"] == {
		"team": None, "status": "open", "changed_from": None,
		"changed_until": None, "closure": "incident-endpoints"}
	assert answered["projection_version"] == "12.8"
	# BOTH DEFAULTS, because there are two and either could drift.
	#
	# MEASURED, and the measurement added this line. The CLI grammar carries
	# `status="open"` and passes it explicitly, so changing the PROJECTION's
	# own default changed nothing this case could see -- one default masking
	# the other, and the assertion above passing either way. A caller reaching
	# `work_graph` directly (a future renderer, an analysis script) gets the
	# projection's default and not the CLI's.
	assert cli.GRAMMAR["work-graph"]["keys"][1]["default"] == "open"
	assert projection.work_graph(store)["scope"]["status"] == "open"


def test_json_is_the_default_format_and_dot_must_be_asked_for(world, capsys):
	"""Existing automation keeps reading an envelope unless it says otherwise."""
	store = world["store"]
	out, _err = run(capsys, world["config"], "work-graph", raw=True)
	assert json.loads(out)["result"]["scope"]["status"] == "open"
	dotted, _err = run(capsys, world["config"], "work-graph", "format=dot",
	                   raw=True)
	assert dotted.startswith('digraph "baton_work" {')


def test_the_range_is_half_open_and_selects_by_last_changed_at(world, capsys):
	"""Inclusive lower bound, exclusive upper, over the canonical column."""
	store = world["store"]
	early = make(store, "early")
	row = store.conn.execute(
		"SELECT last_changed_at FROM work WHERE id=?", (early,)).fetchone()
	moment = row["last_changed_at"]
	graph = projection.work_graph(store, status="all", changed_from=moment,
	                              changed_until="2100-01-01T00:00:00Z")
	assert early in {one["id"] for one in graph["nodes"] if one["selected"]}
	# The lower bound is INCLUSIVE and the upper is EXCLUSIVE, so a range
	# ending exactly at this instant excludes it.
	graph = projection.work_graph(store, status="all",
	                              changed_from="2000-01-01T00:00:00Z",
	                              changed_until=moment)
	assert early not in {one["id"] for one in graph["nodes"] if one["selected"]}


def test_the_range_normalizes_offsets_to_utc(world):
	"""One instant, however it is spelled."""
	store = world["store"]
	make(store, "anything")
	as_utc = projection.work_graph(store, status="all",
	                               changed_from="2026-08-27T00:00:00Z",
	                               changed_until="2026-08-28T00:00:00Z")
	as_offset = projection.work_graph(store, status="all",
	                                  changed_from="2026-08-26T20:00:00-04:00",
	                                  changed_until="2026-08-27T20:00:00-04:00")
	assert as_utc["scope"]["changed_from"] == \
		as_offset["scope"]["changed_from"]
	assert as_utc["scope"]["changed_until"] == \
		as_offset["scope"]["changed_until"]


def test_the_range_is_optional_for_open_and_closed(world, capsys):
	store = world["store"]
	make(store, "anything")
	for status in ("open", "closed"):
		answered = run(capsys, world["config"], "work-graph",
		               f"status={status}")
		assert answered["result"]["scope"]["status"] == status


def test_an_empty_selection_is_a_valid_metadata_bearing_graph(world, capsys):
	"""Nothing selected is an ANSWER, not a refusal."""
	store = world["store"]
	text, _ = run(capsys, world["config"], "work-graph", "format=dot",
	              "status=closed", raw=True)
	assert text.startswith('digraph "baton_work" {')
	assert 'baton_snapshot_seq="' in text
	assert 'baton_scope_status="closed"' in text
	assert " -> " not in text
	assert text.endswith("}\n")


def test_every_structured_node_member_survives_into_the_dot(world, capsys):
	"""The DOT carries the projection, not a summary of it."""
	store = world["store"]
	work_id = make(store, "a title")
	graph = projection.work_graph(store, status="open")
	text = dot.render_work_graph_dot(envelope_for(store, graph))
	statement = next(line for line in text.splitlines()
	                 if line.startswith(f'\t"{work_id}" ['))
	# AN ABSENT VALUE IS THE LITERAL `null`, in both directions. An empty
	# string would be indistinguishable from a genuinely empty value, and a
	# missing attribute from a renderer that dropped it. Nothing observed this
	# until the mutation pass replaced `null` with `""` and every case passed.
	assert 'baton_outcome="null"' in statement
	closed = make(store, "a finished one")
	finish(store, closed)
	after = projection.work_graph(store, status="closed")
	closed_statement = next(
		line for line in dot.render_work_graph_dot(
			envelope_for(store, after)).splitlines()
		if line.startswith(f'\t"{closed}" ['))
	assert 'baton_phase="null"' in closed_statement
	assert 'baton_outcome="satisfying"' in closed_statement
	# EVERY member, including `selected` -- review [P1]. `baton_scope` is the
	# readable role and `baton_selected` is the projection's exact boolean, and
	# the two are complementary rather than alternatives.
	assert 'baton_scope="selected"' in statement
	for member in projection.GRAPH_NODE_MEMBERS:
		assert f"baton_{member}=" in statement, member
	# The edge's `source` and `target` are the STATEMENT -- `a -> b` -- rather
	# than attributes beside it, which is what makes the document a graph to a
	# reader that understands DOT and nothing about Baton. The other four
	# members are attributes.
	statement = dot._edge_statement(
		projection._export_edge("dependency", work_id, work_id, 1))
	assert statement.strip().startswith(f'"{work_id}" -> "{work_id}"')
	for member in projection.GRAPH_EDGE_MEMBERS:
		if member in ("source", "target"):
			continue
		assert f"baton_{member}=" in statement, member


def test_selected_keeps_its_ruled_baton_member_beside_scope(world):
	"""`baton_scope` is readable context, not a replacement schema member.

	The approved format separately requires `scope=selected|context` and one
	`baton_*` attribute for every structured node member. Both fit in DOT and
	both are useful: the former is the readable role and the latter preserves
	the projection's boolean without a format-specific reverse mapping.
	"""
	store = world["store"]
	work_id = make(store, "selected")
	graph = projection.work_graph(store)
	statement = next(
		line for line in dot.render_work_graph_dot(
			envelope_for(store, graph)).splitlines()
		if line.startswith(f'\t"{work_id}" ['))
	assert 'baton_scope="selected"' in statement
	assert 'baton_selected="true"' in statement


def test_the_document_spells_its_whole_scope_and_identity(world, capsys):
	"""One authority, one snapshot and one SCOPE give one document — so the
	scope has to be entirely in the document, or two different questions
	could produce identical bytes."""
	store = world["store"]
	make(store, "anything")
	text, _ = run(capsys, world["config"], "work-graph", "format=dot",
	              "status=all", "changed-from=2026-08-01T00:00:00Z",
	              "changed-until=2026-09-01T00:00:00Z", raw=True)
	for attribute in ("baton_authority_uuid", "baton_dot_version",
	                  "baton_projection_version", "baton_protocol_version",
	                  "baton_snapshot_seq", "baton_scope_status",
	                  "baton_scope_team", "baton_scope_changed_from",
	                  "baton_scope_changed_until", "baton_scope_closure",
	                  "charset"):
		assert f"\t{attribute}=" in text, attribute
	assert 'baton_dot_version="1"' in text
	assert 'charset="UTF-8"' in text


def test_two_scopes_over_one_snapshot_do_not_collide(world, capsys):
	"""The consequence of the case above, measured.

	`status=open` and a `status=all` range that happens to select the same
	rows must still be two distinguishable documents.
	"""
	store = world["store"]
	make(store, "the only Work")
	first, _ = run(capsys, world["config"], "work-graph", "format=dot",
	               raw=True)
	second, _ = run(capsys, world["config"], "work-graph", "format=dot",
	                "status=all", "changed-from=2000-01-01T00:00:00Z",
	                "changed-until=2100-01-01T00:00:00Z", raw=True)
	assert first != second


def test_the_verb_is_in_the_public_help(world, capsys):
	"""A surface an operator cannot discover is a surface that does not
	exist."""
	rendered = cli.render_help(None)
	assert "work-graph" in rendered
	one = cli.render_help("work-graph")
	for operand in ("format", "status", "team", "changed-from",
	                "changed-until"):
		assert operand in one, operand


def test_the_export_is_a_pure_read_and_takes_no_operation_identity(world,
                                                                   capsys):
	"""`op-id=` protects mutations; an export is not one."""
	code = cli.main(["--config", world["config"], "--participant", "lang.ada",
	                 "work-graph", "op-id=nope"])
	captured = capsys.readouterr()
	assert code == 1
	assert "pure read" in json.loads(captured.err)["error"]
