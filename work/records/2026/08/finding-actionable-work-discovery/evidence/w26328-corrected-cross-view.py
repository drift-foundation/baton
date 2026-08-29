"""W26328 third-review cross-view reproduction, re-run against the CORRECTION.

This is the reviewer's own `w26328-review-cross-view-cursor.py` with the
assertion the required correction inverts, and nothing else. Their file is kept
exactly as produced.

Run from the repository root:

    python3 -B work/records/2026/08/finding-actionable-work-discovery/evidence/w26328-corrected-cross-view.py

WHY IT CANNOT BE RUN UNCHANGED. Their file asserts that Ada's read through
Grace's cursor returns an empty page -- the defect stated as an expectation.
The correction refuses the token instead, so their script raises where it
asserted.

WHAT IS MEASURED IS UNCHANGED: a continuation genuinely returned by this
authority, unedited, must not be able to hide one participant's actionable Work
behind another participant's position.

The later probes are the other side of the same rule, and they are the ones a
careless binding breaks. A cursor bound to CLAIMABILITY rather than to the VIEW
would refuse the ordinary same-viewer continuation that the previous two
corrections exist for; a binding that only checked the row would leave this
defect exactly where it was.

Exit 0 means every one holds.
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


def disjoint(directory):
	"""Two Routes on one kind, one handler each, no overlap."""
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
	return bw.Authority(accepted["database"])


def split(directory):
	store = disjoint(directory)

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
	return store, ada, grace


def page(store, member, **paging):
	return projection.actionable_work(
		store, viewer_team="lang", viewer_member=member, **paging)


def refused(store, member, **paging):
	try:
		page(store, member, **paging)
	except bw.WorkError as complaint:
		return str(complaint)
	return None


def another_participants_cursor_cannot_hide_my_work():
	with tempfile.TemporaryDirectory(prefix="w26328-cross-") as directory:
		store, ada, grace = split(directory)
		theirs = page(store, "grace", limit=1)
		assert [row["id"] for row in theirs["rows"]] == grace[:1]
		assert theirs["next_after"] is not None

		complaint = refused(store, "ada", after=theirs["next_after"])
		print("Grace's cursor read as Ada ->", complaint)
		assert complaint is not None, "the cross-view cursor was followed"
		assert "different participant" in complaint
		# And the Work it would have hidden is still there to be found.
		assert [row["id"] for row in page(store, "ada")["rows"]] == ada
		return True


def the_refusal_does_not_send_them_round_a_refresh_loop():
	"""A cursor belonging to another participant is not a snapshot that
	moved, and it is answered before the row is looked up. Telling its holder
	to refresh would send them somewhere that cannot help -- their next page
	would be this page again."""
	with tempfile.TemporaryDirectory(prefix="w26328-cross-") as directory:
		store, _ada, _grace = split(directory)
		theirs = page(store, "grace", limit=1)
		complaint = refused(store, "ada", after=theirs["next_after"])
		assert "refresh" not in complaint, complaint
		assert "who is asking" in complaint
		print("the two refusals stay different mistakes")
		return True


def each_participant_walks_their_own_view_to_the_end():
	"""The binding costs neither of them anything."""
	with tempfile.TemporaryDirectory(prefix="w26328-cross-") as directory:
		store, ada, grace = split(directory)
		walked = {}
		for member, expected in (("ada", ada), ("grace", grace)):
			seen, after = [], None
			while True:
				one = page(store, member, after=after, limit=1)
				seen += [row["id"] for row in one["rows"]]
				after = one["next_after"]
				if after is None:
					break
			walked[member] = seen
			assert seen == expected, (member, seen, expected)
		print("each view walks its own set:",
		      {who: [work.rsplit("-", 1)[1] for work in rows]
		       for who, rows in walked.items()})
		return True


def the_same_participants_ordinary_continuation_still_works():
	"""THE REGRESSION A VIEW BINDING MOST EASILY CAUSES.

	The binding is on the VIEW, not on the row's claimability: a cursor row
	that merely stopped being actionable for the SAME viewer must still
	continue, which is what the first correction exists for.
	"""
	with tempfile.TemporaryDirectory(prefix="w26328-cross-") as directory:
		store, ada, _grace = split(directory)
		first = page(store, "ada", limit=1)
		transitions.claim_work(store, ada[0], actor_team="lang", actor="ada")
		second = page(store, "ada", after=first["next_after"], limit=1)
		print("same viewer, claimed cursor row ->",
		      [row["local_id"] for row in second["rows"]])
		assert [row["id"] for row in second["rows"]] == ada[1:]
		return True


if __name__ == "__main__":
	ok = [another_participants_cursor_cannot_hide_my_work(),
	      the_refusal_does_not_send_them_round_a_refresh_loop(),
	      each_participant_walks_their_own_view_to_the_end(),
	      the_same_participants_ordinary_continuation_still_works()]
	print("OK" if all(ok) else "UNSAFE")
	raise SystemExit(0 if all(ok) else 1)
