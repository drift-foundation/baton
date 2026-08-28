"""W4996: the bounded dependency neighbourhood and its ASCII rendering.

`work/records/2026/08/finding-ascii-dependency-neighborhood/`, contract
approved 2026-08-22 without amendment.

The `[d] deps` page was a flat list of `blocked_by`/`blocks`/duplicate rows.
It never showed how the selected Work sits BETWEEN its upstream blockers and
its downstream dependents, so an operator reconstructed even a small N:M
neighbourhood mentally.

Two properties carry the whole design and both are asserted here rather than
argued: the graph is EXACTLY the canonical dependency projection (a renderer
does not get to invent edge lifetime), and every bound it applies is
disclosed with an exact count (a truncated graph that looks complete is worse
than no graph).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures                                               # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))), "src"))

import curses                                                 # noqa: E402

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.authority import WorkError                    # noqa: E402
from baton_work.tui import graph                              # noqa: E402




class Screen:
	"""The console's painter, recorded. Same shape the other console
	suites use: `addnstr` calls with their attributes, so a case can ask
	what was drawn AND how."""

	def __init__(self, height=24, width=120):
		self.calls = []
		self._size = (height, width)

	def erase(self):
		self.calls = []

	def getmaxyx(self):
		return self._size

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def clrtoeol(self):
		pass

	def addnstr(self, y, x, text, *rest):
		self.calls.append((y, x, str(text),
		                   rest[1] if len(rest) > 1 else 0))

	def lines(self):
		return [text for _y, _x, text, _attr in self.calls]

@pytest.fixture()
def world(tmp_path):
	fixtures.build(str(tmp_path / "work.sqlite3"))
	store = bw.Authority(str(tmp_path / "work.sqlite3"))
	yield store
	store.close()


def make(store, title):
	return tr.create_work(
		store, team="lang", kind="bug", title=title,
		origin="self-initiated", classification="design-choice",
		author="ada", body="x")["work_id"]


def depend(store, work, blocker):
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="the consumer waits on the provider")


def sides(view):
	return {"upstream": [edge["blocker"] for edge in view["edges"]
	                     if edge["side"] == "upstream"],
	        "downstream": [edge["work"] for edge in view["edges"]
	                       if edge["side"] == "downstream"]}


# -- the projection ----------------------------------------------------------

def test_the_graph_is_exactly_the_canonical_dependency_projection(world):
	"""Parity, in both directions, including the ruled ASYMMETRY.

	`blocked_by` keeps every recorded upstream edge — a satisfied one
	included — while `blocks` keeps only live consumers. A presentation read
	that widened either side would be choosing new edge lifetime, which is
	the one thing the reviewer's baseline says a renderer must not do."""
	a, b, c = make(world, "A"), make(world, "B"), make(world, "C")
	depend(world, b, a)
	depend(world, c, b)
	view = pj.dependency_neighborhood(world, b)
	assert sides(view) == {"upstream": [a], "downstream": [c]}
	assert sides(view)["upstream"] == \
		[entry["id"] for entry in pj.links(world, b)["blocked_by"]]
	assert sides(view)["downstream"] == \
		[entry["id"] for entry in pj.links(world, b)["blocks"]]
	# Close the CONSUMER: it leaves the provider's live downstream set…
	tr.close_work(world, c, outcome="satisfying", rationale="done",
	              actor_team="lang", actor="ada")
	assert sides(pj.dependency_neighborhood(world, b))["downstream"] == []
	# …and keeps its own upstream edge, because that history is recorded.
	assert sides(pj.dependency_neighborhood(world, c))["upstream"] == [b]


def test_many_to_one_and_one_to_many_around_one_center(world):
	center = make(world, "center")
	blockers = [make(world, f"up{index}") for index in range(3)]
	consumers = [make(world, f"down{index}") for index in range(3)]
	for blocker in blockers:
		depend(world, center, blocker)
	for consumer in consumers:
		depend(world, consumer, center)
	view = pj.dependency_neighborhood(world, center)
	assert sides(view) == {"upstream": blockers, "downstream": consumers}
	# Stable ORDER is the edge's own creation order, on both sides.
	assert [edge["blocker"] for edge in view["edges"]
	        if edge["side"] == "upstream"] == blockers


def test_expansion_is_directional_and_does_not_turn_corners(world):
	"""An upstream node's OTHER consumers are a different Work's
	neighbourhood. Following them would grow the view to the whole
	component and stop it being about the center."""
	blocker = make(world, "shared blocker")
	center = make(world, "center")
	sibling = make(world, "sibling consumer")
	depend(world, center, blocker)
	depend(world, sibling, blocker)
	view = pj.dependency_neighborhood(world, center, depth=3)
	assert sibling not in view["nodes"], \
		"expansion turned a corner into a lateral neighbourhood"
	# It is reached by RECENTERING, which is the contract's answer.
	assert sibling in pj.dependency_neighborhood(world, blocker)["nodes"]


def test_depth_is_bounded_and_refuses_outside_its_range(world):
	chain = [make(world, f"n{index}") for index in range(5)]
	for near, far in zip(chain, chain[1:]):
		depend(world, far, near)
	center = chain[0]
	assert len(pj.dependency_neighborhood(world, center, depth=1)["nodes"]) == 2
	assert len(pj.dependency_neighborhood(world, center, depth=2)["nodes"]) == 3
	assert len(pj.dependency_neighborhood(world, center, depth=3)["nodes"]) == 4
	for outside in (0, 4, -1, "2", True, 2.0):
		with pytest.raises(WorkError, match="outside 1..3"):
			pj.dependency_neighborhood(world, center, depth=outside)


def test_a_dense_branch_pages_with_an_exact_omitted_count(world):
	center = make(world, "center")
	consumers = [make(world, f"c{index}") for index in range(7)]
	for consumer in consumers:
		depend(world, consumer, center)
	view = pj.dependency_neighborhood(world, center)
	assert sides(view)["downstream"] == consumers[:4], \
		"a branch admitted more than one page"
	key = pj.branch_key(center, "downstream")
	assert view["omitted"] == {key: 3}, "the omission was not counted exactly"
	# Enter on the token admits one more page for THAT branch only.
	paged = pj.dependency_neighborhood(world, center, expanded={key: 8})
	assert sides(paged)["downstream"] == consumers
	assert paged["omitted"] == {}


def test_paging_one_branch_does_not_expand_another(world):
	"""An operator opening one dense blocker set has not asked to open
	every other one."""
	center = make(world, "center")
	blockers = [make(world, f"up{index}") for index in range(6)]
	consumers = [make(world, f"down{index}") for index in range(6)]
	for blocker in blockers:
		depend(world, center, blocker)
	for consumer in consumers:
		depend(world, consumer, center)
	view = pj.dependency_neighborhood(
		world, center, expanded={pj.branch_key(center, "upstream"): 8})
	assert len(sides(view)["upstream"]) == 6
	assert len(sides(view)["downstream"]) == 4
	assert view["omitted"] == {pj.branch_key(center, "downstream"): 2}


def test_the_occurrence_cap_actually_bounds_an_adversarial_branch(world):
	"""A neighbourhood is a view, not an export.

	W4996 review [P2]: the cap was a constant the response disclosed, and
	nothing crossed it. This builds a branch larger than the cap and expands
	it, so the bound is exercised rather than asserted about.

	The bound is on MATERIALIZATION too: the direct count comes from a
	`COUNT(*)` and the rows from an ordered `LIMIT`, so an adversarial
	fan-out never becomes a Python list before the cap applies."""
	center = make(world, "center")
	fanout = pj.DEPENDENCY_OCCURRENCE_CAP + 40
	for index in range(fanout):
		depend(world, make(world, f"c{index}"), center)
	key = pj.branch_key(center, "downstream")
	# Ask for the whole branch: the CAP is what must stop it, not the page.
	view = pj.dependency_neighborhood(world, center,
	                                  expanded={key: fanout + 10})
	assert view["capped"] is True, "the cap was never reached"
	assert view["occurrences"] <= view["occurrence_cap"]
	drawn = len(sides(view)["downstream"])
	assert drawn < fanout, "the cap admitted the whole branch"
	# The omission is EXACT and covers everything not drawn — a bounded view
	# that under-reported what it left out would be worse than no bound.
	assert view["omitted"][key] == fanout - drawn, view["omitted"]
	# Unexpanded, the ordinary page still applies and the cap is not reached.
	ordinary = pj.dependency_neighborhood(world, center)
	assert ordinary["capped"] is False
	assert len(sides(ordinary)["downstream"]) == pj.DEPENDENCY_BRANCH_PAGE
	assert ordinary["omitted"][key] == fanout - pj.DEPENDENCY_BRANCH_PAGE


def test_the_branch_is_read_with_a_bound_not_sliced_afterwards(world):
	"""The memory property, witnessed by the ROWS the projection reads.

	W4996 review [P2] is about materialization, and materialization has no
	visible result — the same answer comes back either way. So this counts
	what the edge query actually returns: with a count-plus-page it is the
	page, and with a fetch-then-slice it would be the whole fan-out.
	Asserting the outcome alone would leave the correction unwitnessed."""
	center = make(world, "center")
	fanout = 60
	for index in range(fanout):
		depend(world, make(world, f"c{index}"), center)
	fetched = []
	original = pj._dependency_edges

	def watching(store, work_id, side, limit):
		rows, total = original(store, work_id, side, limit)
		fetched.append((len(rows), total))
		return rows, total

	pj._dependency_edges = watching
	try:
		view = pj.dependency_neighborhood(world, center)
	finally:
		pj._dependency_edges = original
	assert fetched, "no edge query was observed; the watch is inert"
	assert max(rows for rows, _total in fetched) <= pj.DEPENDENCY_BRANCH_PAGE, \
		f"the branch was materialized in full before the page applied: {fetched}"
	# The exact total is still known, so the bound cost no information.
	assert max(total for _rows, total in fetched) == fanout
	# And the exact direct count still comes back, from the COUNT rather
	# than from the length of a list nobody wanted.
	assert view["omitted"][pj.branch_key(center, "downstream")] == \
		fanout - pj.DEPENDENCY_BRANCH_PAGE


def test_an_expanded_branch_is_materialized_only_to_the_remaining_cap(world):
	"""Branch expansion cannot widen the SQL LIMIT past the global bound.

	The ordinary page is only four rows, so observing that path does not prove
	the 200-occurrence cap bounds an overflow branch after repeated Enter.
	The count may cover the whole branch; the row page must cover at most the
	remaining rendered occurrences.
	"""
	center = make(world, "center")
	fanout = pj.DEPENDENCY_OCCURRENCE_CAP + 40
	for index in range(fanout):
		depend(world, make(world, f"c{index}"), center)
	key = pj.branch_key(center, "downstream")
	fetched = []
	original = pj._dependency_edges

	def watching(store, work_id, side, limit):
		rows, total = original(store, work_id, side, limit)
		fetched.append((len(rows), total))
		return rows, total

	pj._dependency_edges = watching
	try:
		view = pj.dependency_neighborhood(
			world, center, expanded={key: fanout + 10})
	finally:
		pj._dependency_edges = original
	assert view["capped"] is True
	assert max(rows for rows, _total in fetched) <= \
		pj.DEPENDENCY_OCCURRENCE_CAP - 1, fetched
	assert max(total for _rows, total in fetched) == fanout


def test_w4996_review_the_cap_is_disclosed_when_page_and_room_tie(world):
	"""A page bound and the remaining global allowance can stop together.

	The view still reached its hard cap and omitted a direct edge. Calling that
	ordinary branch paging would hide that no other branch can admit a row.
	"""
	center = make(world, "center")
	blockers = [make(world, f"up{index}") for index in range(195)]
	consumers = [make(world, f"down{index}") for index in range(5)]
	for blocker in blockers:
		depend(world, center, blocker)
	for consumer in consumers:
		depend(world, consumer, center)
	upstream = pj.branch_key(center, "upstream")
	downstream = pj.branch_key(center, "downstream")
	view = pj.dependency_neighborhood(
		world, center, expanded={upstream: len(blockers)})
	assert view["occurrences"] == view["occurrence_cap"]
	assert view["omitted"][downstream] == 1
	assert view["capped"] is True, \
		"the view hit its cap with an omitted edge but did not disclose it"


def test_w4996_review_a_shared_branch_does_not_invent_omissions(world):
	"""A DAG path is not another occurrence of the same canonical edge.

	The shared node's outgoing branch is already fully rendered after its
	first visit. Replaying those same edges through a second valid path must not
	consume the cap or claim that already-visible dependents were omitted.
	"""
	center = make(world, "center")
	left, right = make(world, "left"), make(world, "right")
	shared = make(world, "shared")
	depend(world, left, center)
	depend(world, right, center)
	depend(world, shared, left)
	depend(world, shared, right)
	leaves = [make(world, f"leaf{index}") for index in range(150)]
	for leaf in leaves:
		depend(world, leaf, shared)
	key = pj.branch_key(shared, "downstream")
	view = pj.dependency_neighborhood(
		world, center, depth=3, expanded={key: len(leaves)})
	assert len([edge for edge in view["edges"]
	            if edge["blocker"] == shared]) == len(leaves)
	assert key not in view["omitted"], \
		"the projection labelled already-rendered shared edges as hidden"
	assert view["capped"] is False
	assert view["occurrences"] == 1 + len(view["edges"])


def _shared_by_long_then_short(world, leaves=150):
	"""center -> a -> shared, and center -> shared directly.

	The LONGER path is walked first, because its edge is older, so the
	shared branch is expanded with one hop of depth left. The shortcut is
	walked afterwards and carries MORE depth, which the review says must
	still be admitted — and that second expansion is exactly where a
	re-query or a re-count does its damage, because by then the branch's
	own rows have already consumed most of the allowance.
	"""
	center = make(world, "center")
	first = make(world, "a")
	shared = make(world, "shared")
	depend(world, first, center)          # oldest edge: the longer path
	depend(world, shared, first)
	depend(world, shared, center)         # the shortcut, walked later
	made = [make(world, f"leaf{index}") for index in range(leaves)]
	for leaf in made:
		depend(world, leaf, shared)
	return center, shared, made


def test_a_second_deeper_visit_does_not_requery_the_direct_page(world):
	"""The `fetched` memo, witnessed by the omission it prevents.

	Re-review [P1] reported this through two equal-length paths. It arrives
	just as easily through the path the review says must KEEP working: a
	later shorter path supplies more depth, so the branch is expanded a
	second time — and by then the earlier rows have consumed the allowance,
	so a re-query would admit fewer of the SAME edges and label the rest
	hidden while they are on screen.
	"""
	center, shared, leaves = _shared_by_long_then_short(world)
	key = pj.branch_key(shared, "downstream")
	view = pj.dependency_neighborhood(
		world, center, depth=3, expanded={key: len(leaves)})
	drawn = [edge for edge in view["edges"] if edge["blocker"] == shared]
	assert len(drawn) == len(leaves)
	assert key not in view["omitted"], \
		"a re-query labelled already-rendered edges as hidden"
	assert view["capped"] is False


def test_a_shorter_path_removes_a_shared_branch_from_the_depth_frontier(world):
	"""A frontier token describes edges the depth bound actually hid.

	The shared Work is reached first at the depth boundary and later through a
	shortcut carrying one more hop.  That later visit draws its outgoing edge,
	so retaining the first visit's frontier count would show an overflow token
	for a relationship already on screen.
	"""
	center = make(world, "center")
	middle = make(world, "middle")
	shared = make(world, "shared")
	leaf = make(world, "leaf")
	depend(world, middle, center)       # older, longer path
	depend(world, shared, middle)
	depend(world, shared, center)       # later shortcut
	depend(world, leaf, shared)
	key = pj.branch_key(shared, "downstream")
	view = pj.dependency_neighborhood(world, center, depth=2)
	assert any(edge["blocker"] == shared and edge["work"] == leaf
	           for edge in view["edges"]), view["edges"]
	assert key not in view["frontier"], \
		"the graph labels an already-rendered branch as depth-hidden"


def test_a_later_longer_path_cannot_restore_an_expanded_branch_frontier(world):
	"""Frontier truth is independent of which valid DAG path is older.

	The direct shortcut reaches and expands ``shared`` first.  A later longer
	path reaches the same Work at the depth boundary.  That boundary visit must
	not restore a frontier entry for the branch whose outgoing edge is already
	on screen.
	"""
	center = make(world, "center")
	middle = make(world, "middle")
	shared = make(world, "shared")
	leaf = make(world, "leaf")
	depend(world, shared, center)       # older shortcut expands the branch
	depend(world, middle, center)       # later, longer path
	depend(world, shared, middle)
	depend(world, leaf, shared)
	key = pj.branch_key(shared, "downstream")
	view = pj.dependency_neighborhood(world, center, depth=2)
	assert any(edge["blocker"] == shared and edge["work"] == leaf
	           for edge in view["edges"]), view["edges"]
	assert key not in view["frontier"], \
		"a later depth-bound revisit restored a frontier already rendered"


def test_a_re_walked_edge_is_not_another_occurrence(world):
	"""Occurrences count RENDERED edges.

	The second expansion of the shared branch walks the same 150 edges. They
	are already drawn, so counting them would spend the view's budget on
	rows nobody sees twice — and with a large enough branch it would report
	a cap the rendered graph never reached.
	"""
	center, shared, leaves = _shared_by_long_then_short(world)
	key = pj.branch_key(shared, "downstream")
	view = pj.dependency_neighborhood(
		world, center, depth=3, expanded={key: len(leaves)})
	assert view["occurrences"] == 1 + len(view["edges"]), \
		"an occurrence was spent on an edge that is rendered once"
	assert view["occurrences"] < view["occurrence_cap"]
	assert view["capped"] is False


def test_a_branch_is_not_re_expanded_at_a_depth_it_already_had(world):
	"""The `walked` memo has no visible result, so it is watched.

	Two equal-length paths to one node ask for the identical expansion
	twice. Nothing in the response changes — the edges are deduplicated and
	the occurrences are not spent — so asserting the outcome would leave the
	memo unwitnessed, and an unwitnessed bound is one the next correction
	deletes. This counts the expansions instead.

	It deliberately does NOT assert one expansion per branch: a later
	SHORTER path carrying more depth must still be admitted, which the
	previous two cases rely on."""
	center = make(world, "center")
	left, right = make(world, "left"), make(world, "right")
	shared = make(world, "shared")
	depend(world, left, center)
	depend(world, right, center)
	depend(world, shared, left)
	depend(world, shared, right)
	for index in range(3):
		depend(world, make(world, f"leaf{index}"), shared)
	seen = []
	original = pj._expand_branch

	def watching(store, work_id, side, remaining, *rest):
		seen.append((work_id, side, remaining))
		return original(store, work_id, side, remaining, *rest)

	pj._expand_branch = watching
	try:
		pj.dependency_neighborhood(world, center, depth=3)
	finally:
		pj._expand_branch = original
	assert seen, "no expansion was observed; the watch is inert"
	# `shared` is reached by both paths at the SAME remaining depth. The
	# second ask is answered from the memo, so its branch is expanded once.
	deep = [entry for entry in seen
	        if entry[0] == shared and entry[1] == "downstream"]
	assert len(deep) == 1, deep


def test_a_node_on_two_paths_is_one_node(world):
	"""Ordinary in a DAG. Two paths to one Work must not become two
	Works, and must not be mistaken for a cycle."""
	root = make(world, "root")
	left, right = make(world, "left"), make(world, "right")
	sink = make(world, "sink")
	depend(world, left, root)
	depend(world, right, root)
	depend(world, sink, left)
	depend(world, sink, right)
	view = pj.dependency_neighborhood(world, root, depth=2)
	assert sorted(view["nodes"]) == sorted([root, left, right, sink])
	assert len([edge for edge in view["edges"]
	            if edge["work"] == sink]) == 2, \
		"the shared node lost one of the paths that reach it"


def test_w4996_review_a_walk_memo_cannot_hide_a_cycle_on_another_path(world):
	"""Memoization cannot run before the path-local safety check.

	`cycle-b` is first reached through an unrelated branch, where its edge to
	`cycle-a` is not a back edge. The later route reaches the same branch with
	`cycle-a` in its ancestry, so that exact edge closes the visible cycle.
	A `(Work, side, depth)` memo must not answer the second path before checking
	what is unique about it: its ancestors.
	"""
	center = make(world, "center")
	left = make(world, "left")
	cycle_a = make(world, "cycle-a")
	cycle_b = make(world, "cycle-b")
	depend(world, left, center)              # walked first
	depend(world, cycle_a, center)           # walked second
	depend(world, cycle_b, left)             # unrelated first path to B
	depend(world, cycle_b, cycle_a)          # A --blocks--> B
	# The authority correctly refuses the final B --blocks--> A insertion.
	# Build the damaged-file shape directly, as the existing malformed-edge
	# case does: a view must fail visibly when its store is already corrupt.
	seq = world.conn.execute(
		"SELECT COALESCE(MAX(created_seq), 0) + 1 FROM edges").fetchone()[0]
	world.conn.execute(
		"INSERT INTO edges (work, blocker, created_seq) VALUES (?, ?, ?)",
		(cycle_a, cycle_b, seq))
	world.conn.commit()
	with pytest.raises(pj.GraphInvalid, match="dependency cycle"):
		pj.dependency_neighborhood(world, center, depth=3)


def _damaged_edge(world, blocker, work):
	"""Insert an edge the authority would refuse.

	Both cycle cases need this: the authority refuses a dependency cycle at
	insertion, so a cyclic neighbourhood is reachable only from a damaged
	file — which is exactly when a view must not paper over it."""
	seq = world.conn.execute(
		"SELECT COALESCE(MAX(created_seq), 0) + 1 FROM edges").fetchone()[0]
	world.conn.execute(
		"INSERT INTO edges (work, blocker, created_seq) VALUES (?, ?, ?)",
		(work, blocker, seq))
	world.conn.commit()


def test_a_cycle_refusal_names_the_exact_closing_edge(world):
	"""'This graph has a cycle' sends an operator through the whole
	neighbourhood looking for it.

	The refusal names the exact `A --blocks--> B` that closes the loop, on
	the path that reaches it — and both cycle boundaries must say so, since
	either can be the one that fires."""
	center = make(world, "center")
	first = make(world, "first")
	second = make(world, "second")
	depend(world, first, center)
	depend(world, second, first)
	_damaged_edge(world, second, first)      # second --blocks--> first
	with pytest.raises(pj.GraphInvalid) as refusal:
		pj.dependency_neighborhood(world, center, depth=3)
	message = str(refusal.value)
	assert "dependency cycle" in message
	assert f"{second} --blocks--> {first}" in message, message


def test_a_diamond_is_not_mistaken_for_a_cycle(world):
	"""The false positive a naive check produces, and the reason the walk
	distinguishes ANCESTRY from "already finished".

	A node reached by two valid paths is ordinary in a DAG. A cycle check
	that marked nodes visited and treated any second arrival as a back edge
	would refuse the most common shape in this repository's own graph."""
	center = make(world, "center")
	left, right = make(world, "left"), make(world, "right")
	sink = make(world, "sink")
	depend(world, left, center)
	depend(world, right, center)
	depend(world, sink, left)
	depend(world, sink, right)
	view = pj.dependency_neighborhood(world, center, depth=3)
	assert len([edge for edge in view["edges"]
	            if edge["work"] == sink]) == 2
	# And a deeper diamond, so the second arrival is not adjacent to the
	# fork — the case a shallow guard would still get wrong.
	deep = make(world, "deep")
	depend(world, deep, sink)
	assert pj.dependency_neighborhood(world, center, depth=3)["edges"]


def test_the_admitted_graph_is_checked_not_the_traversal_order(world):
	"""The reviewer's finding, stated as the property rather than the case.

	A branch memo answers by `(Work, side, depth)` and cannot know which
	ancestors the second path carries. So the boundary that matters is over
	the edges the response CONTAINS — reached in either traversal order, the
	same damaged graph is refused."""
	for first_walked_is_the_loop in (False, True):
		store_dir = world
		center = make(store_dir, f"center{first_walked_is_the_loop}")
		other = make(store_dir, f"other{first_walked_is_the_loop}")
		one = make(store_dir, f"one{first_walked_is_the_loop}")
		two = make(store_dir, f"two{first_walked_is_the_loop}")
		if first_walked_is_the_loop:
			depend(store_dir, one, center)   # the cycle's branch first
			depend(store_dir, other, center)
		else:
			depend(store_dir, other, center)
			depend(store_dir, one, center)
		depend(store_dir, two, other)        # an unrelated route to `two`
		depend(store_dir, two, one)          # one --blocks--> two
		_damaged_edge(store_dir, two, one)   # two --blocks--> one
		with pytest.raises(pj.GraphInvalid, match="dependency cycle"):
			pj.dependency_neighborhood(store_dir, center, depth=3)


def test_a_cycle_outside_the_drawn_graph_is_not_invented(world):
	"""The other half of honesty. A loop whose closing edge the view never
	admitted is not in the response, and refusing over it would describe a
	graph the operator was not shown — while a bound that hid a cycle it DID
	draw would be the reported defect again."""
	center = make(world, "center")
	first = make(world, "first")
	second = make(world, "second")
	depend(world, first, center)
	depend(world, second, first)
	_damaged_edge(world, second, first)      # second --blocks--> first
	# At depth one the closing edge is outside the view, and the drawn graph
	# really is acyclic.
	shallow = pj.dependency_neighborhood(world, center, depth=1)
	assert [edge["work"] for edge in shallow["edges"]] == [first]
	# Deep enough to draw it, and it is refused. A boundary, not a blind
	# spot.
	with pytest.raises(pj.GraphInvalid, match="dependency cycle"):
		pj.dependency_neighborhood(world, center, depth=3)


def test_w4996_review_a_cycle_cut_by_the_cap_is_not_invented(world):
	"""A fetched sibling is not necessarily a rendered edge.

	The branch page is read before recursion. Its first sibling can spend the
	remaining occurrence allowance in a deep branch, leaving a later closing
	edge outside the response. The path-local guard must not describe that
	unrendered edge as a cycle before the cap rejects it; the final admitted-
	graph check remains the authority on what the response actually contains.
	"""
	center = make(world, "center")
	middle = make(world, "middle")
	dense = make(world, "dense")
	depend(world, middle, dense)              # dense --blocks--> middle first
	depend(world, center, middle)             # middle --blocks--> center
	# Fill the remaining budget under the first sibling. Center, the edge to
	# middle and the edge to dense consume three occurrences.
	for index in range(pj.DEPENDENCY_OCCURRENCE_CAP - 3):
		depend(world, dense, make(world, f"dense-blocker-{index}"))
	# This later sibling closes center -> middle -> center, but only after the
	# dense branch has filled the rendered-occurrence cap.
	_damaged_edge(world, center, middle)      # center --blocks--> middle
	dense_key = pj.branch_key(dense, "upstream")
	view = pj.dependency_neighborhood(
		world, center, depth=3,
		expanded={dense_key: pj.DEPENDENCY_OCCURRENCE_CAP})
	assert view["capped"] is True
	assert view["occurrences"] == view["occurrence_cap"]
	assert not any(edge["blocker"] == center and edge["work"] == middle
	               for edge in view["edges"]), \
		"the closing edge entered the graph after the cap was full"
	assert view["omitted"][pj.branch_key(middle, "upstream")] == 1


def _memo_hidden_cycle(world):
	"""The reviewer's shape: the closing edge is ordinary on the first path
	and closes a loop only on the second, so the branch memo answers before
	any ancestry is compared. This is the fixture where the ADMITTED-GRAPH
	check is the one that fires."""
	center = make(world, "center")
	left = make(world, "left")
	one = make(world, "cycle-a")
	two = make(world, "cycle-b")
	depend(world, left, center)              # walked first
	depend(world, one, center)               # walked second
	depend(world, two, left)                 # unrelated first path to `two`
	depend(world, two, one)                  # one --blocks--> two
	_damaged_edge(world, two, one)           # two --blocks--> one
	return center, one, two


def test_the_admitted_graph_refusal_names_its_closing_edge_too(world):
	"""Both boundaries name the exact edge, not just the walk's.

	The path-local check already did. Mutation showed the new one's message
	was unwitnessed — every cycle case reaching an assertion about the text
	was being refused by the OTHER check — so this drives the fixture where
	only the admitted-graph check can fire."""
	center, one, two = _memo_hidden_cycle(world)
	with pytest.raises(pj.GraphInvalid) as refusal:
		pj.dependency_neighborhood(world, center, depth=3)
	message = str(refusal.value)
	assert "dependency cycle" in message
	# EITHER real edge of the loop is an exact answer — which one depends on
	# where the search enters it — and naming a real one is the property:
	# "this graph has a cycle" sends an operator through the whole
	# neighbourhood looking for it.
	assert (f"{two} --blocks--> {one}" in message
	        or f"{one} --blocks--> {two}" in message), message


def test_the_walk_still_refuses_a_cycle_before_descending_into_it(world):
	"""The path-local check earns its place, and it is watched to prove it.

	With the admitted-graph boundary in place the walk's own check no longer
	changes the ANSWER — a plain cycle is refused either way — so mutation
	showed the suite green without it. What it still does is refuse at the
	first re-entry instead of walking up to the whole occurrence budget
	round a loop on a damaged store. That is work not done, so it is watched
	rather than asserted about: if the walk refuses, the final check is
	never reached at all."""
	center = make(world, "center")
	first = make(world, "first")
	second = make(world, "second")
	depend(world, first, center)
	depend(world, second, first)
	_damaged_edge(world, second, first)      # second --blocks--> first
	reached = []
	original = pj._refuse_cycles

	def watching(edges):
		reached.append(len(edges))
		return original(edges)

	pj._refuse_cycles = watching
	try:
		with pytest.raises(pj.GraphInvalid, match="dependency cycle"):
			pj.dependency_neighborhood(world, center, depth=3)
	finally:
		pj._refuse_cycles = original
	assert reached == [], \
		"the walk descended into the loop and left the refusal to the " \
		"final check"
	# The watch is not inert: an ACYCLIC neighbourhood reaches the final
	# check. It has to be a different center — every Work in the damaged
	# component above has the loop in its own neighbourhood.
	clean = make(world, "clean")
	depend(world, make(world, "clean-consumer"), clean)
	pj._refuse_cycles = watching
	try:
		pj.dependency_neighborhood(world, clean, depth=1)
	finally:
		pj._refuse_cycles = original
	assert reached, "the final check never ran, so the watch proves nothing"


def test_an_already_drawn_edge_still_meets_the_fast_cycle_guard(world):
	"""Cap admission comes first only for an edge NOT already drawn.

	An edge already in the response is part of the admitted graph, so
	refusing over it is not inventing anything — and the fast guard must
	still fire on it even when the allowance is spent, or a damaged store
	would be walked round its loop until the final check caught it.
	"""
	center = make(world, "center")
	first = make(world, "first")
	second = make(world, "second")
	depend(world, first, center)
	depend(world, second, first)
	_damaged_edge(world, second, first)       # second --blocks--> first
	reached = []
	original = pj._refuse_cycles

	def watching(edges):
		reached.append(len(edges))
		return original(edges)

	pj._refuse_cycles = watching
	try:
		with pytest.raises(pj.GraphInvalid, match="rather than recursing"):
			pj.dependency_neighborhood(world, center, depth=3)
	finally:
		pj._refuse_cycles = original
	assert reached == [], \
		"the fast guard stopped firing once cap admission moved ahead of it"


def test_a_cycle_edge_the_cap_omits_is_disclosed_not_refused(world):
	"""The reviewer's rule, driven from the other end.

	The response is bounded and acyclic, so it must come BACK — with the cap
	disclosed and the exact direct omission — rather than raise about an edge
	it does not contain. The whole point of the bound is that a view stays
	usable on a graph too big to draw; refusing would take that away over
	something the operator cannot see.
	"""
	center = make(world, "center")
	middle = make(world, "middle")
	dense = make(world, "dense")
	depend(world, center, middle)             # middle --blocks--> center
	depend(world, middle, dense)              # dense  --blocks--> middle
	for index in range(pj.DEPENDENCY_OCCURRENCE_CAP - 3):
		depend(world, dense, make(world, f"filler{index}"))
	_damaged_edge(world, center, middle)      # center --blocks--> middle
	key = pj.branch_key(dense, "upstream")
	view = pj.dependency_neighborhood(
		world, center, depth=3,
		expanded={key: pj.DEPENDENCY_OCCURRENCE_CAP})
	assert view["capped"] is True
	assert view["occurrences"] <= view["occurrence_cap"]
	# Acyclic AS RETURNED, which is what makes not refusing honest rather
	# than lenient: the final boundary agrees.
	pj._refuse_cycles(view["edges"])
	# And the closing edge really is absent, so nothing was hidden by
	# drawing it and staying quiet.
	assert not [edge for edge in view["edges"]
	            if edge["blocker"] == center and edge["work"] == middle]


def test_an_exhausted_allowance_does_not_omit_already_drawn_edges(world):
	"""Cap admission is about edges the response does NOT yet contain.

	Round-4's finding was a branch claiming its own rendered edges were
	hidden. The round-6 reordering must not reintroduce it from the other
	side: when a branch is revisited after the allowance is spent, its edges
	are already on screen, so the cap has nothing to decide about them and
	an omission would be a count of visible rows.
	"""
	center = make(world, "center")
	first = make(world, "a")
	shared = make(world, "shared")
	depend(world, first, center)              # the longer path, walked first
	depend(world, shared, first)
	depend(world, shared, center)             # the shortcut, more depth
	leaves = pj.DEPENDENCY_OCCURRENCE_CAP - 4
	for index in range(leaves):
		depend(world, make(world, f"leaf{index}"), shared)
	key = pj.branch_key(shared, "downstream")
	view = pj.dependency_neighborhood(
		world, center, depth=3, expanded={key: leaves})
	drawn = [edge for edge in view["edges"] if edge["blocker"] == shared]
	assert len(drawn) == leaves
	assert key not in view["omitted"], \
		"the revisited branch reported its own rendered edges as hidden"
	assert view["occurrences"] == 1 + len(view["edges"])


def test_a_malformed_edge_refuses_the_graph_visibly(world):
	"""Dropping the edge would draw a SMALLER graph that looks complete.

	The authority refuses a dependency cycle at insertion, so this can only
	arise from damaged data — which is exactly when a view must not paper
	over it."""
	center = make(world, "center")
	other = make(world, "other")
	depend(world, other, center)
	# The schema's foreign key already forbids a dangling blocker, which is
	# why this reaches past it: the row is removed with the constraint
	# suspended, exactly the shape a damaged file has.
	world.conn.execute("PRAGMA foreign_keys = OFF")
	world.conn.execute("DELETE FROM work WHERE id=?", (center,))
	world.conn.commit()
	world.conn.execute("PRAGMA foreign_keys = ON")
	with pytest.raises(pj.GraphInvalid, match="does not hold"):
		pj.dependency_neighborhood(world, other)


def test_the_read_is_one_snapshot_and_writes_nothing(world):
	import hashlib

	def fingerprint():
		# The write-ahead log too: a store in WAL mode keeps recent writes
		# there, so hashing the main file alone would call any read pure.
		out = hashlib.sha256()
		for suffix in ("", "-wal"):
			try:
				out.update(open(world.path + suffix, "rb").read())
			except FileNotFoundError:
				pass
		return out.hexdigest()

	before = fingerprint()
	center = make(world, "center")
	depend(world, make(world, "up"), center)
	settled = fingerprint()
	assert before != settled, "the fixture never wrote anything"
	view = pj.dependency_neighborhood(world, center, depth=3)
	assert "snapshot_seq" in view
	assert fingerprint() == settled, "the graph read wrote to the authority"


def test_the_public_links_response_is_unchanged(world):
	"""The graph is an ADDITION. A client reading `links` sees exactly what
	it saw before, containment and duplicates included."""
	center = make(world, "center")
	depend(world, center, make(world, "up"))
	response = pj.links(world, center)
	assert set(response) >= {"id", "parent", "contains", "blocked_by",
	                         "blocks", "duplicate_of", "duplicates",
	                         "follow_up_of", "follow_ups"}


# -- the rendering -----------------------------------------------------------

def chain(store):
	blocker, center, consumer = (make(store, "blocker"), make(store, "center"),
	                             make(store, "consumer"))
	depend(store, center, blocker)
	depend(store, consumer, center)
	return blocker, center, consumer


def test_every_edge_spells_its_direction_without_unicode_or_colour(world):
	_blocker, center, _consumer = chain(world)
	view = pj.dependency_neighborhood(world, center)
	rendered = graph.rows(view, 100)
	text = "\n".join(row["text"] for row in rendered)
	assert "--blocks-->" in text
	assert text.isascii(), "the graph leaned on a non-ASCII glyph"
	# One row per relationship, and the center appears on both.
	assert sum(1 for row in rendered if "--blocks-->" in row["text"]) == 2


def test_the_center_sits_in_one_column_between_the_two_sides(world):
	"""What makes it layered rather than a list: every occurrence of the
	center token starts at the same offset, so the eye follows one vertical
	line and sees which side of it a Work is on."""
	_blocker, center, _consumer = chain(world)
	view = pj.dependency_neighborhood(world, center)
	rendered = graph.rows(view, 100)
	marker = graph.token(view["nodes"][center])
	columns = {row["text"].index(marker) for row in rendered
	           if marker in row["text"]}
	assert len(columns) == 1, "the center did not line up in one column"


def test_deeper_edges_keep_each_node_in_its_wide_layer_column(world):
	"""A layered graph gives one column to one shortest-path layer.

	For A -> B -> C, B cannot be the target in a downstream column on one
	row and then jump back into A's center column as the source on the next.
	That is an adjacency list with indentation, not the approved layered form.
	"""
	center = make(world, "center")
	first = make(world, "first")
	second = make(world, "second")
	depend(world, first, center)
	depend(world, second, first)
	view = pj.dependency_neighborhood(world, center, depth=2)
	rows = graph.rows(view, 160)
	near = next(row for row in rows
	            if row.get("blocker") == center and row.get("consumer") == first)
	far = next(row for row in rows
	           if row.get("blocker") == first and row.get("consumer") == second)
	first_token = graph.token(view["nodes"][first])
	assert near["text"].index(first_token) == far["text"].index(first_token), \
		"the depth-one node moved back into the center column on its deeper edge"


def test_w4996_review_a_shortcut_node_keeps_one_wide_column(world):
	"""A legal DAG may reach one Work by a direct and a longer path.

	The corrected renderer promises that shortest-path layer determines one
	column per Work. A back-crossing canonical edge must not silently paint the
	same selector in a second, farther column.
	"""
	center = make(world, "center")
	shortcut = make(world, "shortcut")
	alternate = make(world, "alternate")
	far = make(world, "far")
	depend(world, shortcut, center)
	depend(world, alternate, center)
	depend(world, far, alternate)
	depend(world, shortcut, far)
	view = pj.dependency_neighborhood(world, center, depth=3)
	rendered = graph.rows(view, 240)
	marker = graph.token(view["nodes"][shortcut])
	columns = {row["text"].index(marker) for row in rendered
	           if marker in row["text"]}
	assert len(columns) == 1, \
		"a shortcut Work moved columns on its longer canonical path"


def test_depth_two_renders_the_edges_that_actually_exist(world):
	"""A deeper node is linked to its predecessor, not directly to center.

	The projection carries exact directed edges. Flattening every layer back
	onto the center would both drop a canonical edge and draw one the authority
	never held.
	"""
	center = make(world, "center")
	first = make(world, "first")
	second = make(world, "second")
	depend(world, first, center)
	depend(world, second, first)
	view = pj.dependency_neighborhood(world, center, depth=2)
	text = "\n".join(row["text"] for row in graph.rows(view, 120))
	center_token = graph.token(view["nodes"][center])
	first_token = graph.token(view["nodes"][first])
	second_token = graph.token(view["nodes"][second])
	assert f"{center_token} {graph.ARROW} {first_token}" in text
	assert f"{first_token} {graph.ARROW} {second_token}" in text, \
		"the renderer dropped the canonical depth-two edge"
	assert f"{center_token} {graph.ARROW} {second_token}" not in text, \
		"the renderer invented a direct edge from the center"


def test_width_chooses_the_renderer_and_never_the_graph(world):
	"""A narrow terminal loses LAYOUT, never a relationship. An operator
	who widened the window and saw a new edge appear would have been
	looking at a lie."""
	_blocker, center, _consumer = chain(world)
	view = pj.dependency_neighborhood(world, center)
	seen = []
	for width in (120, 60, 40, 24):
		rendered = graph.rows(view, width)
		assert all(len(row["text"]) <= width for row in rendered), width
		seen.append({row["work"] for row in rendered
		             if row["kind"] == graph.ROW_WORK})
	assert all(entry == seen[0] for entry in seen), \
		"a narrower terminal showed a different set of Work"


def test_every_rendered_edge_is_a_canonical_edge_at_every_depth(world):
	"""The guarantee this view is built on, asserted against the projection
	rather than against a shape.

	W4996 review [P1]: the renderers paired every node with the CENTER, so a
	depth-two chain drew an `A --blocks--> C` the authority never held and
	dropped the `B --blocks--> C` it did."""
	chain = [make(world, f"n{index}") for index in range(4)]
	for near, far in zip(chain, chain[1:]):
		depend(world, far, near)
	fan = make(world, "other consumer")
	depend(world, fan, chain[1])
	for center, depth in ((chain[0], 3), (chain[2], 2), (chain[1], 3)):
		view = pj.dependency_neighborhood(world, center, depth=depth)
		canonical = {(edge["blocker"], edge["work"]) for edge in view["edges"]}
		for width in (140, 70, 24):
			drawn = set()
			for row in graph.rows(view, width):
				if row["kind"] != graph.ROW_WORK or row["side"] == "center":
					continue
				drawn.add((row["blocker"], row["consumer"]))
			assert drawn == canonical, (center, depth, width, drawn, canonical)


def test_every_selectable_row_shows_the_token_for_its_own_work(world):
	"""A console that highlighted one Work and recentered on another would
	be worse than no graph. Asserted in every renderer, not only the one the
	review found."""
	center = make(world, "center")
	depend(world, center, make(world, "up"))
	depend(world, make(world, "down"), center)
	view = pj.dependency_neighborhood(world, center)
	for width in (140, 70, 24):
		for row in graph.rows(view, width):
			if row["kind"] != graph.ROW_WORK:
				continue
			assert graph.token(view["nodes"][row["work"]]) in row["text"], \
				(width, row)


def test_a_terminal_too_narrow_for_one_selector_refuses(world):
	"""A clipped identity is a different Work as far as the operator's eyes
	are concerned, and this view exists to be acted on."""
	_blocker, center, _consumer = chain(world)
	view = pj.dependency_neighborhood(world, center)
	with pytest.raises(graph.GraphTooNarrow, match="complete selector"):
		graph.rows(view, 4)


def test_the_row_order_is_the_same_at_every_width(world):
	"""`j`/`k` mean one thing. If the order changed with the window, a
	muscle-memory keypress would act on a different Work after a resize."""
	center = make(world, "center")
	for index in range(3):
		depend(world, make(world, f"down{index}"), center)
	depend(world, center, make(world, "up"))
	view = pj.dependency_neighborhood(world, center)
	orders = []
	for width in (120, 60, 30):
		orders.append([row["work"] for row in graph.rows(view, width)
		               if row["kind"] == graph.ROW_WORK])
	assert orders[0] == orders[1] == orders[2]


def test_every_selectable_stacked_row_displays_its_own_work(world):
	"""Narrow layout cannot label one Work while Enter targets another."""
	_blocker, center, _consumer = chain(world)
	view = pj.dependency_neighborhood(world, center)
	rendered = graph.rows(view, 24)
	for row in rendered:
		if row["kind"] != graph.ROW_WORK:
			continue
		assert graph.token(view["nodes"][row["work"]]) in row["text"], \
			"the selectable identity differs from the Work shown on its row"


def test_an_overflow_token_names_its_exact_count_and_side(world):
	center = make(world, "center")
	for index in range(7):
		depend(world, make(world, f"c{index}"), center)
	view = pj.dependency_neighborhood(world, center)
	rendered = graph.rows(view, 100)
	tokens = [row for row in rendered if row["kind"] == graph.ROW_OVERFLOW]
	assert len(tokens) == 1
	assert tokens[0]["text"].strip() == "[+3 dependents]"
	assert tokens[0]["count"] == 3
	assert tokens[0]["side"] == "downstream"
	# It sits with its BRANCH. Re-review [P2] fixed what that means: the
	# token follows the last VISIBLE sibling of the branch it opens, which
	# for a center whose only branch is downstream is the last row. My
	# earlier assertion here — "not at the end of the page" — encoded the
	# old placement, where the token sat beside the center instead, and it
	# would now refuse the correct order.
	siblings = [index for index, row in enumerate(rendered)
	            if row["kind"] == graph.ROW_WORK
	            and row["side"] == "downstream"]
	assert rendered.index(tokens[0]) == max(siblings) + 1
	# An upstream overflow says blockers, so the two sides never read alike.
	other = make(world, "other")
	for index in range(6):
		depend(world, other, make(world, f"u{index}"))
	upstream = graph.rows(pj.dependency_neighborhood(world, other), 100)
	assert [row["text"].strip() for row in upstream
	        if row["kind"] == graph.ROW_OVERFLOW] == ["[+2 blockers]"]


@pytest.mark.parametrize("side", ("upstream", "downstream"))
def test_each_overflow_token_follows_its_visible_branch_siblings(world, side):
	"""The token occupies the next traversal slot for the branch it opens."""
	center = make(world, f"{side} center")
	for index in range(7):
		far = make(world, f"{side} {index}")
		if side == "upstream":
			depend(world, center, far)
		else:
			depend(world, far, center)
	view = pj.dependency_neighborhood(world, center)
	rendered = graph.rows(view, 120)
	token_index = next(index for index, row in enumerate(rendered)
	                   if row["kind"] == graph.ROW_OVERFLOW
	                   and row["side"] == side)
	sibling_indices = [index for index, row in enumerate(rendered)
	                   if row["kind"] == graph.ROW_WORK
	                   and row["side"] == side]
	assert token_index == max(sibling_indices) + 1, (side, rendered)


def test_a_deeper_branch_token_follows_ITS_siblings_not_its_owner(world):
	"""The upstream half of the token rule, where the two candidate rules
	stop coinciding.

	For the CENTER's upstream branch, "after the last visible blocker" and
	"immediately before the center" are the same slot — the center's
	blockers are always the rows just above it — so the reported case cannot
	tell the branch rule from an owner-relative one. With TWO nodes in the
	depth-one layer they diverge: each one's blockers are drawn as a group,
	and the first node's token must close the FIRST group rather than drift
	down to sit beside its owner."""
	center = make(world, "center")
	near = [make(world, "near-a"), make(world, "near-b")]
	for one in near:
		depend(world, center, one)
		for index in range(7):
			depend(world, one, make(world, f"{one}-far{index}"))
	view = pj.dependency_neighborhood(world, center, depth=2)
	rendered = graph.rows(view, 200)
	for one in near:
		siblings = [index for index, row in enumerate(rendered)
		            if row["kind"] == graph.ROW_WORK
		            and row["side"] == "upstream"
		            and row.get("consumer") == one]
		assert siblings, "the deeper branch drew no visible blockers"
		token = next(index for index, row in enumerate(rendered)
		             if row["kind"] == graph.ROW_OVERFLOW
		             and row["work"] == one and row["side"] == "upstream")
		assert token == max(siblings) + 1, (one, rendered)


def test_an_overflow_token_sits_in_its_siblings_column(world):
	"""Order is not the whole rule in the wide form: a token indented to its
	OWNER's column would read as something about the owner rather than as
	one more of the rows above it. Its siblings are one layer out, so that
	is the column it takes."""
	center = make(world, "center")
	for index in range(7):
		depend(world, center, make(world, f"blocker{index}"))
	view = pj.dependency_neighborhood(world, center)
	rendered = graph.rows(view, 200)
	token = next(row for row in rendered
	             if row["kind"] == graph.ROW_OVERFLOW)
	siblings = [row for row in rendered
	            if row["kind"] == graph.ROW_WORK and row["side"] == "upstream"]
	assert siblings, "no visible sibling to line up with"
	indent = lambda text: len(text) - len(text.lstrip(" "))
	assert indent(token["text"]) == indent(siblings[0]["text"]), rendered
	# And NOT the center's column, which is where the owner sits.
	center_row = next(row for row in rendered if row["side"] == "center")
	assert indent(token["text"]) != indent(center_row["text"])


def test_the_footer_states_the_depth_and_the_cap(world):
	"""A graph that has stopped expanding looks exactly like one that had
	nothing more to show, unless it says so."""
	_blocker, center, _consumer = chain(world)
	view = pj.dependency_neighborhood(world, center)
	assert "depth 1/3" in graph.footer(view)
	assert "[Enter] recenter" in graph.footer(view)
	assert "view cap" not in graph.footer(view)
	assert "view cap 200 reached" in graph.footer({**view, "capped": True})


def test_a_lone_work_renders_as_itself(world):
	"""No edges is a real answer, not an error."""
	alone = make(world, "alone")
	view = pj.dependency_neighborhood(world, alone)
	rendered = graph.rows(view, 80)
	assert [row["work"] for row in rendered] == [alone]
	assert "--blocks-->" not in rendered[0]["text"]


# -- the console -------------------------------------------------------------
#
# The second slice. `[d]` opens the graph, `j`/`k` move by ROW while selection
# is anchored by IDENTITY, Enter recenters or widens one branch, `+`/`-` move
# depth inside 1..3, and every one of those rides the universal navigation
# frame so Esc restores the exact prior graph.


def console(world, tmp_path):
	from baton_work.tui.app import Console
	return Console(world, "lang", "ada", config_path=str(tmp_path / "c.json"))


def open_graph(view, work):
	ids = [row["id"] for row in view.rows()]
	view.cursor = ids.index(work)
	view.selected_id = work
	view.handle(ord("d"))
	return view


def test_d_opens_the_graph_and_esc_returns_to_the_table(world, tmp_path):
	blocker, center, consumer = chain(world)
	view = console(world, tmp_path)
	ids = [row["id"] for row in view.rows()]
	view.cursor = ids.index(center)
	view.selected_id = center
	# Captured with the operator's row already selected — Esc must return
	# to the table they left, not to the top of it.
	before = (view.mode, list(view.path), view.cursor, view.selected_id)
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view.graph_center == center
	assert view.graph_depth == pj.DEPENDENCY_DEPTH_MIN
	assert view.graph_anchor == center, "selection did not start at the center"
	assert view.graph_expanded == {}
	drawn = {row["work"] for row in view._graph_row_set()}
	assert {center, blocker, consumer} <= drawn, drawn
	view.handle(27)
	assert (view.mode, list(view.path), view.cursor,
	        view.selected_id) == before, \
		"Esc did not restore the table the operator left"


def test_d_opens_the_graph_from_a_search_result(world, tmp_path):
	"""The approved entry boundary names both the table and search results."""
	target = make(world, "graph-search-target")
	view = console(world, tmp_path)
	view.handle(ord("/"))
	for char in "graph-search-target":
		view.handle(ord(char))
	view.handle(curses.KEY_ENTER)
	assert view.mode == "search"
	rows, _hidden = view.visible_rows(view.search_rows())
	assert [row["id"] for row in rows] == [target], rows
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view.graph_center == target


def test_selection_is_anchored_by_identity_not_by_row(world, tmp_path):
	"""The whole reason `graph_anchor` is a Work id.

	A row index means a different Work after a depth change, a branch
	expansion or a refresh — which is the selection drift the Jobs table
	already forbids."""
	# The fixture has to SEPARATE the two answers, and a downstream-only
	# chain does not: deepening appends rows after the selection, so a row
	# index and an identity agree. An UPSTREAM layer is inserted ABOVE the
	# center, which shifts every later row down — and that is where a
	# stored index quietly starts meaning a different Work.
	center = make(world, "center")
	blocker = make(world, "blocker")
	deeper = make(world, "deeper blocker")
	consumer = make(world, "consumer")
	second = make(world, "second deeper blocker")
	depend(world, center, blocker)          # blocker --blocks--> center
	depend(world, blocker, deeper)          # deeper  --blocks--> blocker
	# TWO of them, so lifting the depth adds two rows where the frontier
	# token had one — otherwise the token conveniently occupies the slot
	# its own edge will take, and the two answers agree by accident.
	depend(world, blocker, second)
	depend(world, consumer, center)         # center  --blocks--> consumer
	view = open_graph(console(world, tmp_path), center)
	while view.graph_anchor != consumer:
		view.handle(ord("j"))
	shallow = [view._graph_row_key(row) for row in view._graph_row_set()]
	assert shallow.index(consumer) == len(shallow) - 1, shallow
	view.handle(ord("+"))
	assert view.graph_depth == 2
	deep = [view._graph_row_key(row) for row in view._graph_row_set()]
	assert deep.index(consumer) != shallow.index(consumer), \
		"the fixture no longer separates a row index from an identity"
	assert view.graph_anchor == consumer, \
		"a depth change moved the selection to another Work"
	# And the OPERATOR sees it there. Asserting the attribute alone would
	# be satisfied by a console that kept the field and painted from a row
	# index anyway, which is the implementation this rule exists to rule
	# out — so the check is on what was drawn.
	screen = Screen(30, 200)
	view.render(screen)
	highlighted = [text for _y, _x, text, attr in screen.calls
	               if attr & curses.A_REVERSE]
	assert highlighted, screen.lines()
	marker = graph.token(view._graph_view()["nodes"][consumer])
	assert all(marker in text for text in highlighted), highlighted


def test_every_appearance_of_the_selected_work_is_drawn_selected(world,
                                                                 tmp_path):
	"""One Work on three edges is one Work."""
	import curses as _curses
	center = make(world, "center")
	shared = make(world, "shared")
	for index in range(3):
		middle = make(world, f"middle{index}")
		depend(world, middle, center)
		depend(world, shared, middle)
	view = open_graph(console(world, tmp_path), center)
	view.graph_depth = 2
	rows = view._graph_row_set()
	appearances = [row for row in rows if row["work"] == shared]
	assert len(appearances) == 3, rows
	view.graph_anchor = shared
	screen = Screen(30, 200)
	view.render(screen)
	selected = [text for _y, _x, text, attr in screen.calls
	            if attr & _curses.A_REVERSE]
	assert len(selected) == 3, selected


def test_j_moves_past_every_appearance_of_one_shared_work(world, tmp_path):
	"""Traversal is by unique Work identity, not by canonical-edge row.

	A shared DAG Work is painted on every relationship row, but pressing `j`
	on that identity must advance to the next Work.  Re-resolving the anchor to
	its first occurrence after every key otherwise traps selection forever on
	the first of two consecutive appearances.
	"""
	center = make(world, "center")
	left, right = make(world, "left"), make(world, "right")
	shared = make(world, "shared")
	tail = make(world, "tail")
	depend(world, left, center)
	depend(world, right, center)
	depend(world, shared, left)
	depend(world, shared, right)
	depend(world, tail, shared)
	view = open_graph(console(world, tmp_path), center)
	view.graph_depth = 3
	rows = view._graph_row_set()
	assert len([row for row in rows if row.get("work") == shared]) == 2
	assert any(row.get("work") == tail for row in rows), rows
	view.graph_anchor = shared
	view.handle(ord("j"))
	assert view.graph_anchor == tail, \
		"selection was trapped on a repeated row for the same Work"


def test_enter_recenters_and_esc_restores_the_exact_prior_graph(world,
                                                                tmp_path):
	center = make(world, "center")
	near = make(world, "near")
	depend(world, near, center)
	view = open_graph(console(world, tmp_path), center)
	view.handle(ord("+"))
	view.handle(ord("j"))
	depth, anchor = view.graph_depth, view.graph_anchor
	assert anchor != center
	view.handle(curses.KEY_ENTER)
	assert view.mode == "links", "Enter left the graph"
	assert view.graph_center == anchor, "Enter did not recenter"
	assert view.graph_depth == depth, "recentering lost the depth"
	assert view.graph_anchor == anchor, "selection is not the new center"
	assert view.graph_expanded == {}, "branch pages survived a recenter"
	view.handle(27)
	assert view.graph_center == center and view.graph_depth == depth
	assert view.graph_anchor == anchor, \
		"Back restored a graph with a different selection"


def test_enter_on_an_overflow_token_widens_only_that_branch(world, tmp_path):
	center = make(world, "center")
	for index in range(pj.DEPENDENCY_BRANCH_PAGE + 3):
		depend(world, make(world, f"down{index}"), center)
	for index in range(pj.DEPENDENCY_BRANCH_PAGE + 2):
		depend(world, center, make(world, f"up{index}"))
	view = open_graph(console(world, tmp_path), center)
	token = next(row for row in view._graph_row_set()
	             if row["kind"] == graph.ROW_OVERFLOW
	             and row["side"] == "downstream")
	view.graph_anchor = view._graph_row_key(token)
	view.handle(curses.KEY_ENTER)
	assert view.mode == "links", "Enter on a token left the graph"
	downstream = pj.branch_key(center, "downstream")
	upstream = pj.branch_key(center, "upstream")
	assert downstream in view.graph_expanded
	assert upstream not in view.graph_expanded, \
		"expanding one branch widened another"
	drawn = [row for row in view._graph_row_set()
	         if row["kind"] == graph.ROW_WORK and row["side"] == "downstream"]
	assert len(drawn) == pj.DEPENDENCY_BRANCH_PAGE + 3


def test_depth_is_bounded_and_the_keys_say_so(world, tmp_path):
	_blocker, center, _consumer = chain(world)
	view = open_graph(console(world, tmp_path), center)
	for _press in range(5):
		view.handle(ord("+"))
	assert view.graph_depth == pj.DEPENDENCY_DEPTH_MAX
	for _press in range(5):
		view.handle(ord("-"))
	assert view.graph_depth == pj.DEPENDENCY_DEPTH_MIN


def test_reducing_depth_returns_selection_to_the_center(world, tmp_path):
	"""Ruled: if the selected Work leaves the neighbourhood, selection
	returns to the center. Nothing else moves it."""
	center = make(world, "center")
	near = make(world, "near")
	depend(world, near, center)
	far = make(world, "far")
	depend(world, far, near)
	view = open_graph(console(world, tmp_path), center)
	view.handle(ord("+"))
	view.graph_anchor = far
	assert any(row["work"] == far for row in view._graph_row_set())
	view.handle(ord("-"))
	assert view.graph_depth == 1
	assert view.graph_anchor == center, \
		"the selection stayed on a Work the view no longer contains"


def test_a_resize_moves_nothing(world, tmp_path):
	"""A resize that moved the selection would move an ACTION to another
	Work, which is the reason this is a rule rather than a nicety."""
	center = make(world, "center")
	near = make(world, "near")
	depend(world, near, center)
	view = open_graph(console(world, tmp_path), center)
	view.handle(ord("j"))
	before = (view.graph_center, view.graph_depth, view.graph_anchor,
	          dict(view.graph_expanded))
	order = [view._graph_row_key(row) for row in view._graph_row_set()]
	for width in (200, 90, 44, 200):
		view.render(Screen(30, width))
		after = (view.graph_center, view.graph_depth, view.graph_anchor,
		         dict(view.graph_expanded))
		assert after == before, width
		assert [view._graph_row_key(row)
		        for row in view._graph_row_set()] == order, width


def test_a_terminal_too_narrow_refuses_rather_than_clipping(world, tmp_path):
	_blocker, center, _consumer = chain(world)
	view = open_graph(console(world, tmp_path), center)
	screen = Screen(30, 6)
	view.render(screen)
	assert any("columns to draw one complete selector" in text
	           for text in screen.lines()), screen.lines()


def test_the_depth_frontier_names_its_count_and_its_key(world, tmp_path):
	"""The two absences never share a token: a dense branch is widened
	with Enter, and the depth bound is lifted with `+`."""
	center = make(world, "center")
	near = make(world, "near")
	depend(world, near, center)
	for index in range(3):
		depend(world, make(world, f"beyond{index}"), near)
	view = open_graph(console(world, tmp_path), center)
	deeper = [row for row in view._graph_row_set()
	          if row["kind"] == graph.ROW_DEEPER]
	assert len(deeper) == 1, view._graph_row_set()
	assert deeper[0]["text"].strip() == "[+3 deeper dependents]"
	# Enter on it does NOT expand a branch page — `+` is its key, and the
	# console says so rather than doing something plausible.
	view.graph_anchor = view._graph_row_key(deeper[0])
	view.handle(curses.KEY_ENTER)
	assert view.graph_expanded == {}, "Enter widened a depth frontier"
	assert "+" in view.status
	view.handle(ord("+"))
	assert view.graph_depth == 2
	assert not [row for row in view._graph_row_set()
	            if row["kind"] == graph.ROW_DEEPER
	            and row["work"] == near], "the frontier survived the depth"


def test_a_captured_frame_owns_its_branch_expansions(world, tmp_path):
	"""`_nav_capture` copies lists and now dicts. A shared expansion map
	would let widening a branch after Back rewrite the frame the operator
	came from."""
	center = make(world, "center")
	for index in range(pj.DEPENDENCY_BRANCH_PAGE + 2):
		depend(world, make(world, f"down{index}"), center)
	near = make(world, "near")
	depend(world, near, center)
	view = open_graph(console(world, tmp_path), center)
	token = next(row for row in view._graph_row_set()
	             if row["kind"] == graph.ROW_OVERFLOW)
	view.graph_anchor = view._graph_row_key(token)
	view.handle(curses.KEY_ENTER)
	widened = dict(view.graph_expanded)
	assert widened
	view.graph_anchor = near
	view.handle(curses.KEY_ENTER)              # recenter on the neighbour
	assert view.graph_expanded == {}
	view.graph_expanded["invented|downstream"] = 99
	view.handle(27)
	assert view.graph_expanded == widened, \
		"the restored frame shared its expansion map with the one above it"


def test_k_also_moves_by_unique_work_and_the_ends_hold(world, tmp_path):
	"""The other direction, and both boundaries.

	The reported case covers `j` off a repeated Work. `k` takes the same
	path and would be trapped identically, and a traversal that WRAPPED
	would move an action to the far end of the graph on one keypress."""
	center = make(world, "center")
	left, right = make(world, "left"), make(world, "right")
	shared = make(world, "shared")
	tail = make(world, "tail")
	depend(world, left, center)
	depend(world, right, center)
	depend(world, shared, left)
	depend(world, shared, right)
	depend(world, tail, shared)
	view = open_graph(console(world, tmp_path), center)
	view.graph_depth = 3
	keys = view._graph_keys(view._graph_row_set())
	assert keys.count(shared) == 1, "the traversal repeats a Work"
	view.graph_anchor = tail
	view.handle(ord("k"))
	assert view.graph_anchor == shared, \
		"k was trapped on a repeated row for the same Work"
	# The ends hold rather than wrapping.
	view.graph_anchor = keys[0]
	view.handle(ord("k"))
	assert view.graph_anchor == keys[0]
	view.graph_anchor = keys[-1]
	view.handle(ord("j"))
	assert view.graph_anchor == keys[-1]
	# Every distinct key is reachable by pressing j from the top.
	view.graph_anchor = keys[0]
	walked = [keys[0]]
	for _press in range(len(keys)):
		view.handle(ord("j"))
		if view.graph_anchor != walked[-1]:
			walked.append(view.graph_anchor)
	assert walked == keys, (walked, keys)


def test_a_token_and_its_work_are_separate_stops(world, tmp_path):
	"""A branch token is not its owner. Collapsing the two would make one
	keypress skip the token that opens the branch — or worse, put Enter's
	two meanings on one stop."""
	center = make(world, "center")
	for index in range(pj.DEPENDENCY_BRANCH_PAGE + 2):
		depend(world, make(world, f"down{index}"), center)
	view = open_graph(console(world, tmp_path), center)
	rows = view._graph_row_set()
	keys = view._graph_keys(rows)
	token = next(row for row in rows if row["kind"] == graph.ROW_OVERFLOW)
	assert view._graph_row_key(token) in keys
	assert center in keys
	assert view._graph_row_key(token) != center


def test_a_deeper_visit_clears_the_frontier_it_recorded(world, tmp_path):
	"""The console half of the stale-token defect.

	The projection no longer keeps the entry, so the RENDERER must stop
	drawing the token — a graph that says a dependent is hidden by depth
	while drawing that exact edge is describing something other than what
	is on screen."""
	# The reported topology, at the DEPTH THAT EXERCISES IT. Mutation showed
	# my first fixture never recorded a frontier for the shared branch at
	# all, so its assertion of absence was vacuous — true whether or not the
	# expansion clears anything. Depth 2 is where the longer path runs out
	# and the shortcut still has a hop.
	center = make(world, "center")
	middle = make(world, "middle")
	shared = make(world, "shared")
	leaf = make(world, "leaf")
	depend(world, middle, center)         # the longer path, walked first
	depend(world, shared, middle)
	depend(world, shared, center)         # the shortcut, one more hop
	depend(world, leaf, shared)
	view = open_graph(console(world, tmp_path), center)
	view.graph_depth = 2
	response = view._graph_view()
	key = pj.branch_key(shared, "downstream")
	assert any(edge["blocker"] == shared and edge["work"] == leaf
	           for edge in response["edges"]), response["edges"]
	assert key not in response["frontier"], response["frontier"]
	# And the CONSOLE half: the renderer must not draw the token either.
	assert not [row for row in view._graph_row_set()
	            if row["kind"] == graph.ROW_DEEPER and row["work"] == shared], \
		"the graph drew a depth-frontier token for an edge it is showing"
	# The fixture is not vacuous: at depth ONE the branch really is beyond
	# the bound, and the token is drawn, so the case above is about the
	# clearing rather than about a token that never existed.
	view.graph_depth = 1
	assert [row for row in view._graph_row_set()
	        if row["kind"] == graph.ROW_DEEPER], view._graph_row_set()


def test_search_entry_carries_the_search_state_back(world, tmp_path):
	"""Opening the graph from a search result is a drill like any other:
	one frame, and Back returns the exact result page."""
	target = make(world, "graph-search-return")
	view = console(world, tmp_path)
	view.handle(ord("/"))
	for char in "graph-search-return":
		view.handle(ord(char))
	view.handle(curses.KEY_ENTER)
	assert view.mode == "search"
	before = (view.search_query, view.cursor, view.selected_id,
	          view.search_page)
	view.handle(ord("d"))
	assert view.mode == "links" and view.graph_center == target
	assert view.nav_segments()[-1] == "deps"
	view.handle(27)
	assert view.mode == "search", "Back did not return to the results"
	assert (view.search_query, view.cursor, view.selected_id,
	        view.search_page) == before


def test_the_frontier_is_the_same_whichever_path_was_created_first(world):
	"""Disclosure is a property of the RESPONSE, not of edge creation order.

	Both traversal orders of one topology must answer identically: the
	shared branch is expanded, so it is not a frontier — whether the
	expanding path arrived before or after the depth-bound one. Two
	corrections were needed for that and each covered one direction, which
	is exactly why this asserts the two orders AGREE rather than asserting
	each separately."""
	answers = []
	for shortcut_first in (True, False):
		tag = "a" if shortcut_first else "b"
		center = make(world, f"center{tag}")
		middle = make(world, f"middle{tag}")
		shared = make(world, f"shared{tag}")
		leaf = make(world, f"leaf{tag}")
		if shortcut_first:
			depend(world, shared, center)     # the direct path is older
			depend(world, middle, center)
		else:
			depend(world, middle, center)     # the longer path is older
			depend(world, shared, center)
		depend(world, shared, middle)         # the longer path's last hop
		depend(world, leaf, shared)
		view = pj.dependency_neighborhood(world, center, depth=2)
		key = pj.branch_key(shared, "downstream")
		assert any(edge["blocker"] == shared and edge["work"] == leaf
		           for edge in view["edges"]), (shortcut_first, view["edges"])
		answers.append((shortcut_first, key in view["frontier"]))
	assert answers == [(True, False), (False, False)], answers


def test_a_branch_beyond_the_depth_is_still_disclosed(world):
	"""The correction must not silence a real frontier.

	A branch nothing expanded IS hidden by the depth bound, and saying so is
	the whole reason the field exists — a bound that reported nothing would
	be as dishonest as one that reported a rendered edge."""
	center = make(world, "center")
	near = make(world, "near")
	depend(world, near, center)
	for index in range(3):
		depend(world, make(world, f"beyond{index}"), near)
	shallow = pj.dependency_neighborhood(world, center, depth=1)
	assert shallow["frontier"][pj.branch_key(near, "downstream")] == 3
	deep = pj.dependency_neighborhood(world, center, depth=2)
	assert pj.branch_key(near, "downstream") not in deep["frontier"]


def test_a_presentation_row_is_not_selectable(world, tmp_path):
	"""The crash the PTY matrix found, pinned where it is cheap to run.

	The stacked fallback draws source, arrow and target on three rows and
	only one of them displays its own Work — the other two are presentation
	and carry no identity at all. A selection anchor that assumed every row
	had one killed the console on a 30-column terminal while every focused
	case passed."""
	center = make(world, "center")
	near = make(world, "near")
	depend(world, near, center)
	view = pj.dependency_neighborhood(world, center)
	# Wide enough for one complete selector — otherwise the renderer
	# REFUSES, which is the other boundary — and too narrow for a whole
	# edge on one line, which is what reaches the stacked form.
	stacked = graph.rows(view, 24)
	assert any(row.get("work") is None for row in stacked), stacked
	# `tmp_path`, like every other console case in this file. Review [P2]:
	# this one minted its own `mkdtemp` and nothing owned it, so each run
	# left an empty root behind — the same class of residue W2907 exists to
	# stop, reintroduced by one case that bypassed the managed fixture the
	# section around it already uses.
	console_view = open_graph(console(world, tmp_path), center)
	console_view._graph_width = 25
	rows = console_view._graph_row_set()
	assert any(row.get("work") is None for row in rows), rows
	# None of these raises, and a presentation row is no movement stop.
	keys = console_view._graph_keys(rows)
	assert all(key is not None for key in keys), keys
	console_view._graph_reanchor(rows)
	console_view.handle(ord("j"))
	console_view.handle(ord("k"))
	console_view.render(Screen(24, 25))


def test_this_suite_mints_no_temporary_root_of_its_own():
	"""The residue guard, scoped to what this Work owns.

	Review [P2]: one console case bypassed pytest's managed `tmp_path` and
	called `tempfile.mkdtemp()` directly, so every run left an empty root
	behind. `tmp_path` is the v11 convention precisely because it is owned
	and removed; a case that mints its own is not covered by anything.

	Asserting the SOURCE rather than counting `/tmp` entries is deliberate:
	a count is affected by every other process on the machine, and this is a
	property of the file."""
	import pathlib
	source = pathlib.Path(__file__).read_text(encoding="utf-8")
	# Everything BEFORE this guard — the guard necessarily names the calls
	# it forbids, and a check that matched its own text would be a check
	# that can never pass.
	cases = source.split("def test_this_suite_mints_no_temporary_root")[0]
	for minted in ("tempfile.mkdtemp", "mkdtemp(", "TemporaryDirectory"):
		assert minted not in cases, \
			f"this suite mints its own temporary root with {minted}; " \
			f"pytest's tmp_path is owned and removed, and a hand-minted " \
			f"root is not"
