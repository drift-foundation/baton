"""Reviewer regressions for the append-only Work-revision slice."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


def test_revision_history_is_a_bounded_paginated_json_list(tmp_path):
	"""The canonical JSON contract says every list is bounded and paged.

	The effective revision may always be returned directly, but an iterative
	Work must not make ``detail`` grow without limit. Its history preview and
	the dedicated continuation surface must join without a gap or repeat.
	"""
	spec = {"lang": {"members": {"ada": ["dev"]},
	                 "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	with bw.Authority(database) as store:
		born = tr.create_work(store, team="lang", kind="bug", title="w",
		                      origin="external-report", author="ada",
		                      body="initial statement")
		work, discussion = born["work_id"], born["discussion"]
		for number in range(1, 54):
			message = tr.post_discussion(
				store, discussion, author_team="lang", author="ada",
				body=f"complete contract revision {number}")["seq"]
			tr.revise_work(store, work, actor_team="lang", actor="ada",
			               message_seq=message,
			               expected_revision=number - 1,
			               rationale=f"iteration {number}")

		view = pj.detail(store, work, viewer_team="lang",
		                 viewer_member="ada")
		assert view["revision"]["revision"] == 53
		assert view["revision_count"] == 53
		assert len(view["revisions"]) == 50
		assert view["revisions_truncated"] is True
		assert view["revisions_next_after"] == 50
		tail = pj.revisions(store, work, after=50, limit=50)
		assert [entry["revision"] for entry in tail["rows"]] == [51, 52, 53]
		assert tail["next_after"] is None
