"""Independent W2938 review regressions."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


def test_teams_uses_one_accepted_pickup_threshold_per_snapshot(
		tmp_path, monkeypatch):
	"""The published policy and every member state are one snapshot.

	A configuration acceptance may change the threshold concurrently.
	Reading it before the roster snapshot and again after that snapshot
	can publish states derived with one value beside a different value.
	The projection must acquire the accepted threshold once inside the
	same read transaction and return that exact value.
	"""
	document = fx.crew_document("lang", ["ada"])
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(document), encoding="utf-8")
	database = lc.init_from_config(str(path), participant="lang.ada")[
		"database"]
	store = bw.Authority(database)
	try:
		tr.create_work(store, team="lang", kind="bug", title="offered",
		               origin="external-report",
		               classification="suspected-defect", author="ada",
		               body="b")
		reads = []

		def moving_threshold(_store):
			reads.append(None)
			return 1 if len(reads) == 1 else 360

		monkeypatch.setattr(pj, "pickup_threshold", moving_threshold)
		result = pj.teams(store, viewer_team="lang", viewer_member="ada")
		assert len(reads) == 1, \
			"one roster response read two potentially different policies"
		assert result["pickup_overdue_seconds"] == 1
	finally:
		store.close()

