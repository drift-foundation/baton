"""Reviewer regressions for the WS-4 Slice A seen boundary."""

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
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture
def discussion(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	created = tr.create_work(store, team="lang", kind="bug", title="w",
	                         origin="self-initiated", author="ada", body="one")
	yield store, created["discussion"]
	store.close()


def test_seen_cursor_cannot_advance_beyond_the_observed_authority(discussion):
	"""An arbitrary future cursor would hide messages that do not exist yet."""
	store, discussion_id = discussion
	before = store.events()
	with pytest.raises(bw.WorkError, match="future|last|observed|sequence"):
		tr.seen_discussion(store, discussion_id, team="lang", member="grace",
		                   up_to_seq=store.last_seq() + 100)
	assert store.events() == before
	assert store.conn.execute(
		"SELECT 1 FROM seen WHERE team='lang' AND member='grace' AND "
		"discussion=?", (discussion_id,)).fetchone() is None


def test_losing_seen_race_reports_the_committed_cursor_without_an_event(
		discussion):
	"""A stale lower mark is an idempotent no-op, even across the write race."""
	store, discussion_id = discussion
	tr.post_discussion(store, discussion_id, author_team="lang", author="ada",
	                   body="two")
	tr.post_discussion(store, discussion_id, author_team="lang", author="ada",
	                   body="three")
	other = bw.Authority(store.path)
	original = store._write

	def interleaved(kind, actor, payload, mutate, **kw):
		store._write = original
		tr.seen_discussion(other, discussion_id, team="lang", member="grace",
		                   up_to_seq=3)
		return original(kind, actor, payload, mutate, **kw)

	store._write = interleaved
	before_marks = len([event for event in store.events()
	                    if event["kind"] == "mark_seen"])
	result = tr.seen_discussion(store, discussion_id, team="lang",
	                            member="grace", up_to_seq=2)
	after_marks = len([event for event in store.events()
	                   if event["kind"] == "mark_seen"])
	assert result == {"seq": None, "kind": "mark_seen", "advanced": False,
	                  "cursor": 3, "operation": None}
	assert after_marks == before_marks + 1
	other.close()


def test_relation_pages_follow_relation_addition_not_discussion_birth(tmp_path):
	"""Joining or labelling old context after a cursor must remain discoverable."""
	spec = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	old = tr.create_work(store, team="lang", kind="bug", title="old",
	                     origin="self-initiated", author="ada", body="old")
	target = tr.create_work(store, team="lang", kind="bug", title="target",
	                        origin="self-initiated", author="ada",
	                        body="target")
	push = tr.create_work(store, team="push", kind="bug", title="push",
	                      origin="self-initiated", author="sl", body="push")

	# Advance each relation cursor beyond the OLD discussion's birth.
	work_page = pj.work_discussions(
		store, target["work_id"], viewer_team="lang", viewer_member="ada",
		limit=1)
	attention_page = pj.discussions_for(
		store, viewer_team="push", viewer_member="sl", limit=1)
	assert [row["id"] for row in work_page["rows"]] == [target["discussion"]]
	assert [row["id"] for row in attention_page["rows"]] == \
		[push["discussion"]]

	# The OLD discussion gains both relations only now.
	tr.label_discussion(store, old["discussion"], target["work_id"],
	                    actor_team="lang", actor="ada")
	tr.post_discussion(store, old["discussion"], author_team="push",
	                   author="sl", body="push joins old context now")

	work_next = pj.work_discussions(
		store, target["work_id"], viewer_team="lang", viewer_member="ada",
		after=work_page["next_after"], limit=1)
	attention_next = pj.discussions_for(
		store, viewer_team="push", viewer_member="sl",
		after=attention_page["next_after"], limit=1)
	assert [row["id"] for row in work_next["rows"]] == [old["discussion"]], \
		"a newly added label to old context fell behind the page cursor"
	assert [row["id"] for row in attention_next["rows"]] == \
		[old["discussion"]], \
		"new participation in old context fell behind the page cursor"
	store.close()


def test_explicit_over_max_thread_limit_refuses_instead_of_clamping(discussion):
	store, discussion_id = discussion
	with pytest.raises(bw.WorkError, match="page limit"):
		pj.thread(store, discussion_id, viewer_team="lang",
		          viewer_member="ada", limit=pj.MAX_PAGE + 500)


def test_work_detail_does_not_advertise_removed_work_bridges(discussion):
	"""R60/R61: an agent must not be offered operations no public API accepts."""
	store, discussion_id = discussion
	work_id = pj.thread(store, discussion_id, viewer_team="lang",
	                    viewer_member="ada")["labels"][0]["work"]
	available = pj.detail(store, work_id, viewer_team="lang",
	                      viewer_member="ada")["available_transitions"]
	assert "post_message" not in available, \
		"Work detail advertises the removed Work-addressed posting bridge"
	assert "mark_seen" not in available, \
		"Work detail advertises the removed Work-addressed seen bridge"


def test_console_marks_only_the_discussion_snapshot_it_rendered(discussion):
	"""A message committed after paint must remain New after the user's mark."""
	store, discussion_id = discussion
	work_id = pj.thread(store, discussion_id, viewer_team="lang",
	                    viewer_member="grace")["labels"][0]["work"]

	class Screen:
		def addnstr(self, *_args):
			pass

	console = Console(store, "lang", "grace")
	console.path = [work_id]
	console.mode = "discussion"
	console._render_discussion(Screen(), 24, 100)
	tr.post_discussion(store, discussion_id, author_team="lang", author="ada",
	                   body="committed after the displayed snapshot")
	console.handle(ord("s"))
	assert pj.thread(store, discussion_id, viewer_team="lang",
	                 viewer_member="grace")["new"] == 1, \
		"mark-seen hid a message the console never displayed"


def test_console_does_not_mark_past_the_returned_thread_page(
		discussion, monkeypatch):
	"""A discussion-wide last_seq is not the end of the returned page."""
	store, discussion_id = discussion
	work_id = pj.thread(store, discussion_id, viewer_team="lang",
	                    viewer_member="grace")["labels"][0]["work"]
	tr.post_discussion(store, discussion_id, author_team="lang", author="ada",
	                   body="outside the bounded page")
	original = pj.thread

	def first_message_page(*args, **kwargs):
		page = original(*args, **kwargs)
		page["messages"] = page["messages"][:1]
		page["next_after"] = page["messages"][-1]["seq"]
		return page

	class Screen:
		def addnstr(self, *_args):
			pass

	monkeypatch.setattr(pj, "thread", first_message_page)
	console = Console(store, "lang", "grace")
	console.path = [work_id]
	console.mode = "discussion"
	console._render_discussion(Screen(), 24, 100)
	console.handle(ord("s"))
	monkeypatch.setattr(pj, "thread", original)
	assert original(store, discussion_id, viewer_team="lang",
	                viewer_member="grace")["new"] == 1, \
		"mark-seen hid a message outside the returned thread page"


def test_every_include_selector_that_lands_nowhere_refuses(discussion):
	"""The selector rule applies to wildcard-shaped selectors too."""
	store, discussion_id = discussion
	before = store.events()
	with pytest.raises(bw.WorkError, match="matches no live endpoint"):
		tr.post_discussion(store, discussion_id, author_team="lang",
		                   author="ada", body="nobody", include="ghost.*")
	assert store.events() == before
