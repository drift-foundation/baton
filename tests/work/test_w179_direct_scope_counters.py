"""W179 (finding-visible-scope-message-counts): default Work counters
describe the DIRECT visible scope.

The pinned W24-shaped regression: a visible parent with its own two
messages, several open children carrying their own conversations, one
hidden CLOSED child, a nested grandchild, and a thread deliberately
labelled to two children. The parent's plain Msg/My/New must equal
exactly the threads entering the parent exposes — identical in home
rows and detail — while the recursive union survives only in the
explicitly named `subtree_total` breakdown with honest overlap.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	_config, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield store
	store.close()


def _make(store, title, parent=None):
	return tr.create_work(store, team="lang", kind="bug", title=title,
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body=f"{title} opener",
	                      parent=parent)


def _rig(store):
	"""The W24 shape: parent (2 direct messages), open children A and B,
	a closed child C, a grandchild under A, and one thread labelled to
	BOTH A and B."""
	parent = _make(store, "the epic")
	tr.post_thread(store, parent["thread"], author_team="lang",
	               author="ada", body="the second direct message")
	a = _make(store, "child a", parent=parent["work_id"])
	b = _make(store, "child b", parent=parent["work_id"])
	c = _make(store, "hidden closed child", parent=parent["work_id"])
	grand = _make(store, "grandchild", parent=a["work_id"])
	tr.post_thread(store, c["thread"], author_team="lang",
	               author="ada", body="closed-child noise")
	tr.close_work(store, c["work_id"], actor_team="lang", actor="ada",
	              rationale="done elsewhere", outcome="satisfying")
	shared = tr.create_thread(
		store, actor_team="lang", actor="ada", body="spans a and b",
		labels=[a["work_id"], b["work_id"]],
		subject="the multiply-labelled conversation")
	return {"parent": parent, "a": a, "b": b, "c": c, "grand": grand,
	        "shared": shared}


def _detail(store, work_id, member="grace"):
	return pj.detail(store, work_id, viewer_team="lang",
	                 viewer_member=member)


def _home_row(store, work_id, member="grace"):
	rows = pj.home(store, viewer_team="lang",
	               viewer_member=member)["rows"]
	return next(row for row in rows if row["id"] == work_id)


def test_the_w24_shape_parent_counters_are_direct(world):
	"""The observed defect, pinned: the parent's plain counters name
	its two direct messages — never the descendants' 21."""
	store = world
	rig = _rig(store)
	parent = rig["parent"]["work_id"]
	detail = _detail(store, parent)
	row = _home_row(store, parent)
	# Home row and detail return IDENTICAL direct facts.
	for field in ("message_count", "my_pending_obligations", "new"):
		assert detail[field] == row[field], field
	# The direct scope is exactly the threads entering the Work
	# exposes: the born thread with its two messages.
	threads = pj.work_threads(store, parent, viewer_team="lang",
	                          viewer_member="grace")["rows"]
	assert len(threads) == 1
	assert detail["message_count"] == 2
	assert detail["new"] == 2, \
		"the parent's plain New is not its direct unseen messages"
	# Open, closed, collapsed and nested children changed nothing.
	assert _detail(store, rig["a"]["work_id"])["message_count"] == 2
	assert _detail(store, rig["c"]["work_id"])["message_count"] == 2, \
		"the closed child still reports its own conversation"


def test_hidden_closed_and_nested_children_never_inflate(world):
	store = world
	rig = _rig(store)
	parent = rig["parent"]["work_id"]
	before = _detail(store, parent)
	# Grow every kind of live descendant conversation: open child,
	# nested grandchild, and the shared thread. (The closed child's
	# noise already exists from before its close — the live-context
	# ruling rightly refuses new posts there.)
	tr.post_thread(store, rig["a"]["thread"], author_team="lang",
	               author="ada", body="more in a")
	tr.post_thread(store, rig["grand"]["thread"], author_team="lang",
	               author="ada", body="deep detail")
	tr.post_thread(store, rig["shared"]["thread"], author_team="lang",
	               author="ada", body="more shared")
	after = _detail(store, parent)
	for field in ("message_count", "my_pending_obligations", "new"):
		assert after[field] == before[field], \
			f"a descendant conversation moved the parent's direct {field}"


def test_the_subtree_breakdown_stays_honest_and_named(world):
	store = world
	rig = _rig(store)
	parent = rig["parent"]["work_id"]
	breakdown = pj.new_count(store, parent, viewer_team="lang",
	                         viewer_member="grace")
	assert "total" not in breakdown, \
		"the recursive union kept its unqualified name"
	assert breakdown["own"] == _detail(store, parent)["new"], \
		"own disagrees with the plain direct cell"
	child_sum = sum(child["new"] for child in breakdown["children"])
	assert breakdown["subtree_total"] == \
		breakdown["own"] + child_sum - breakdown["overlap"]
	# The multiply-labelled thread counts for EACH child directly...
	assert _detail(store, rig["a"]["work_id"])["new"] == \
		_detail(store, rig["b"]["work_id"])["new"]
	# ...but the union counts it once: the overlap is visible.
	assert breakdown["overlap"] > 0, \
		"the shared thread's dedup is not visible as overlap"
	# The hidden closed child still reports honestly inside the
	# explicitly requested breakdown (its scope is named, not hidden).
	closed_entry = next(child for child in breakdown["children"]
	                    if child["id"] == rig["c"]["work_id"])
	assert closed_entry["new"] > 0


def test_marking_a_direct_thread_seen_moves_only_direct_counters(world):
	store = world
	rig = _rig(store)
	parent = rig["parent"]["work_id"]
	child_before = {work: _detail(store, rig[work]["work_id"])["new"]
	                for work in ("a", "b", "c", "grand")}
	tr.seen_thread(store, rig["parent"]["thread"], team="lang",
	               member="grace", up_to_seq=store.last_seq())
	assert _detail(store, parent)["new"] == 0, \
		"seen on the direct thread did not clear the direct New"
	for work, before in child_before.items():
		assert _detail(store, rig[work]["work_id"])["new"] == before, \
			f"seen on the parent's thread moved {work}'s counters"
	breakdown = pj.new_count(store, parent, viewer_team="lang",
	                         viewer_member="grace")
	assert breakdown["own"] == 0
	assert breakdown["subtree_total"] > 0, \
		"the explicit subtree read lost the descendants"


def test_discussion_obligation_follows_every_direct_thread_label(world):
	"""The ruled visible-reuse branch: one @ in a shared Thread is visible
	in each Work whose detail exposes that Thread, never its container."""
	store = world
	rig = _rig(store)
	parent = rig["parent"]["work_id"]
	a, b = rig["a"]["work_id"], rig["b"]["work_id"]
	asked = tr.post_thread(
		store, rig["shared"]["thread"], author_team="lang", author="ada",
		body="please verify the shared symptom", request="lang.bug", wait=False, on=a)
	assert _detail(store, a, member="ada")["my_pending_obligations"] == 1
	assert _detail(store, b, member="ada")["my_pending_obligations"] == 1, \
		"the second direct view hid an obligation visible in its Thread"
	assert _detail(store, parent, member="ada")["my_pending_obligations"] == 0, \
		"containment inflated the parent's direct My"
	tr.respond_obligation(store, asked["seq"], team="lang", member="ada",
	                      body="verified")
	assert _detail(store, a, member="ada")["my_pending_obligations"] == 0
	assert _detail(store, b, member="ada")["my_pending_obligations"] == 0


def test_threadless_trial_assignment_belongs_only_to_its_work(world):
	"""A trial assignment has no Thread to follow. It remains visible on
	the owning Work only, and never leaks upward through containment."""
	store = world
	rig = _rig(store)
	parent = rig["parent"]["work_id"]
	a = rig["a"]["work_id"]
	trial = tr.create_trial(store, a, actor_team="lang", actor="ada",
	                        candidate="staged-build-17",
	                        assign=["lang.bug"])
	assert _detail(store, a, member="ada")["my_pending_obligations"] == 1
	assert _detail(store, parent, member="ada")["my_pending_obligations"] == 0, \
		"a child's threadless trial assignment inflated its parent"
	tr.report(store, trial["assignments"][0], team="lang", member="ada",
	          observation="passed", evidence="staged suite green")
	assert _detail(store, a, member="ada")["my_pending_obligations"] == 0
