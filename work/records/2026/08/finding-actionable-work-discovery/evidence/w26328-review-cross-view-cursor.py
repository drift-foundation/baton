"""Reproduce a continuation crossing participant-relative views.

Run from the repository root:

    python3 -B work/records/2026/08/finding-actionable-work-discovery/evidence/w26328-review-cross-view-cursor.py

The authority has two disjoint Routes. Ada has W2/W3, Grace has W4/W5.
Grace reads a real first page, so the continuation was genuinely returned by
this authority and is bound to W4's current canonical position. Reusing that
token as Ada must refuse: W4 was never in Ada's participant-relative result,
and treating it as Ada's boundary hides both Work items Ada can claim.
"""

import json
import os
import pathlib
import sys
import tempfile


REPOSITORY = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY / "tests" / "work"))

import baton_work as bw  # noqa: E402
from baton_work import lifecycle, projection, transitions  # noqa: E402
import fixtures  # noqa: E402


with tempfile.TemporaryDirectory(prefix="w26328-cross-view-") as directory:
	document = fixtures.config_document()
	team = document["teams"]["lang"]
	role = team["routes"]["main"]["role"]
	team["participants"]["grace"]["roles"] = sorted(set(
		team["participants"]["grace"]["roles"] + [role]))
	team["routes"]["second"] = {"role": role, "handlers": ["grace"]}
	team["kinds"]["rsrch"]["alternates"] = ["second"]
	place = os.path.join(directory, "baton.json")
	with open(place, "w", encoding="utf-8") as handle:
		json.dump(document, handle)
	accepted = lifecycle.init_from_config(
		place, participant=fixtures.first_participant(place))
	store = bw.Authority(accepted["database"])

	def make(title):
		return transitions.create_work(
			store, team="lang", kind="rsrch", title=title,
			origin="external-report", author="ada",
			classification="design-choice", body="body")["work_id"]

	ada = [make("ada one"), make("ada two")]
	grace = [make("grace one"), make("grace two")]
	for work in grace:
		transitions.reroute_work(
			store, work, actor_team="lang", actor="ada", to="lang.rsrch",
			route="second", reason="Grace's disjoint Route")

	grace_page = projection.actionable_work(
		store, viewer_team="lang", viewer_member="grace", limit=1)
	assert [row["id"] for row in grace_page["rows"]] == grace[:1]
	assert grace_page["next_after"] is not None

	ada_first = projection.actionable_work(
		store, viewer_team="lang", viewer_member="ada")
	assert [row["id"] for row in ada_first["rows"]] == ada

	crossed = projection.actionable_work(
		store, viewer_team="lang", viewer_member="ada",
		after=grace_page["next_after"])
	print("Grace page:", [row["local_id"] for row in grace_page["rows"]])
	print("Ada actionable:", [row["local_id"] for row in ada_first["rows"]])
	print("Ada through Grace's cursor:",
	      [row["local_id"] for row in crossed["rows"]])
	assert crossed["rows"] == []
