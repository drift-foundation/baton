"""W26328 re-review forged-cursor reproduction, re-run against the CORRECTION.

This is the reviewer's own `w26328-review-forged-cursor.py` with the assertion
the required correction inverts, and nothing else. Their file is kept exactly
as produced.

Run from the repository root:

    python3 -B work/records/2026/08/finding-actionable-work-discovery/evidence/w26328-corrected-forged-cursor.py

WHY IT CANNOT BE RUN UNCHANGED. Their file asserts `answer["rows"] == []` for
an invented position -- the defect stated as an expectation. The correction
refuses the token instead, so their script raises where it asserted.

WHAT IS MEASURED IS UNCHANGED, and it is the measurement that decides the
feature: a token this authority never returned must not be able to hide live
actionable Work.

The later probes are the other half of the same rule, which the review states
explicitly: a row that merely STOPPED BEING ACTIONABLE must remain a valid
cursor when its order position is unchanged, and a row whose position MOVED
must be refused with the deliberate refresh named. Binding to the wrong thing
satisfies the first probe and breaks the second, so both are here.

Exit 0 means every one holds.
"""

import base64
import pathlib
import sys
import tempfile


REPOSITORY = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY / "tests" / "work"))

import baton_work as bw  # noqa: E402,F401
from baton_work import projection, transitions  # noqa: E402
import fixtures  # noqa: E402


def token(*position, team="lang", member="ada"):
	"""A token of the CURRENT shape.

	Updated with the third review's scheme bump so these probes keep
	measuring the POSITION binding. Built at the old five-member shape they
	would refuse one check earlier, at the scheme tag, and prove only that
	the tag moved.
	"""
	text = "\x1f".join(str(one) for one in
	                   ("w2", team, member) + position)
	return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def waiting(store, title):
	return transitions.create_work(
		store, team="lang", kind="rsrch", title=title,
		origin="external-report", author="ada",
		classification="confirmed-defect", body="body")["work_id"]


def page(store, **paging):
	return projection.actionable_work(
		store, viewer_team="lang", viewer_member="ada", **paging)


def refused(store, **paging):
	try:
		page(store, **paging)
	except bw.WorkError as complaint:
		return str(complaint)
	return None


def an_invented_position_cannot_hide_live_work():
	with tempfile.TemporaryDirectory(prefix="w26328-forged-") as directory:
		store = fixtures.open_instance(directory)
		work = waiting(store, "still waiting")
		forged = token(99, 99, 999999999,
		               "not-this-authority-W999999999")
		complaint = refused(store, after=forged)
		print("forged token ->", complaint)
		assert complaint is not None, "the invented position was followed"
		assert "refresh" in complaint
		# And the Work it would have hidden is still there to be found.
		assert [row["id"] for row in page(store)["rows"]] == [work]
		return True


def a_real_work_at_a_wrong_position_is_refused():
	"""Nearer the mark and still invented: the id exists, the ranks do not
	describe it. Binding that only checked EXISTENCE would follow this."""
	with tempfile.TemporaryDirectory(prefix="w26328-forged-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(2)]
		sequence = store.conn.execute(
			"SELECT created_seq FROM work WHERE id=?",
			(made[0],)).fetchone()["created_seq"]
		complaint = refused(store, after=token(0, 0, sequence, made[0]))
		print("real id, wrong ranks ->", complaint)
		assert complaint is not None and "refresh" in complaint
		return True


def a_row_that_only_stopped_being_actionable_still_continues():
	"""THE ORDINARY CASE the whole feature exists for.

	A claim or a reroute moves a row out of the actionable set WITHOUT moving
	it in the canonical order, so continuing after it means what it meant. A
	binding written against the actionable set would refuse here, and that is
	the regression this probe exists to prevent.
	"""
	with tempfile.TemporaryDirectory(prefix="w26328-forged-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(4)]
		first = page(store, limit=2)
		transitions.claim_work(store, made[1], actor_team="lang", actor="ada")
		second = page(store, after=first["next_after"], limit=2)
		print("claimed cursor row ->",
		      [row["local_id"] for row in second["rows"]])
		assert [row["id"] for row in second["rows"]] == made[2:]
		return True


def a_row_whose_rank_moved_is_refused_and_names_the_refresh():
	"""The documented deliberate-refresh path, reached as a FACT.

	Until the binding existed nothing detected it: the old position was
	followed silently, and the rows between the two places were handed back
	twice or skipped with no way for a client to tell.
	"""
	with tempfile.TemporaryDirectory(prefix="w26328-forged-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(4)]
		first = page(store, limit=2)
		transitions.prioritize(store, made[1], priority="high",
		                       actor_team="lang", actor="ada")
		complaint = refused(store, after=first["next_after"], limit=2)
		print("cursor row reprioritized ->", complaint)
		assert complaint is not None and "refresh" in complaint
		# THE REFRESH IS A REAL PATH, not just advice: everything is readable
		# from the current first page, with the moved row where it now belongs.
		seen, after = [], None
		while True:
			one = page(store, after=after, limit=2)
			seen += [row["id"] for row in one["rows"]]
			after = one["next_after"]
			if after is None:
				break
		assert seen[0] == made[1]
		assert sorted(seen) == sorted(made)
		return True


if __name__ == "__main__":
	ok = [an_invented_position_cannot_hide_live_work(),
	      a_real_work_at_a_wrong_position_is_refused(),
	      a_row_that_only_stopped_being_actionable_still_continues(),
	      a_row_whose_rank_moved_is_refused_and_names_the_refresh()]
	print("OK" if all(ok) else "UNSAFE")
	raise SystemExit(0 if all(ok) else 1)
