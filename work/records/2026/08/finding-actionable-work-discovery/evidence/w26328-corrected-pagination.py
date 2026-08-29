"""W26328 review reproduction, re-run against the CORRECTION.

This is the reviewer's own `w26328-review-pagination.py` with the two
assertions the required correction inverts, and nothing else. Their file is
kept exactly as produced.

WHY IT CANNOT BE RUN UNCHANGED. It asserts `next_after == 2` and then that
page two returns ONLY W5 -- which is the defect stated as an expectation. The
correction makes the continuation an opaque position, so `next_after` is no
longer an integer at all and page two must contain the still-actionable W4.

WHAT IS MEASURED IS UNCHANGED, and it is the measurement that decides the
feature: after an ordinary inter-page claim removes an earlier row, no
still-actionable later Work may be missing from the pages that follow.

The third and fourth probes are the other half of the same contract, which
the review names explicitly: an INSERTION before the cursor must not repeat a
row a page already returned, and a REROUTE (rather than a claim) must not skip
either.

Exit 0 means every one holds.
"""

import pathlib
import sys
import tempfile


REPOSITORY = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY / "tests" / "work"))

import baton_work as bw  # noqa: E402,F401
from baton_work import projection, transitions  # noqa: E402
import fixtures  # noqa: E402


def waiting(store, title):
	return transitions.create_work(
		store, team="lang", kind="rsrch", title=title,
		origin="external-report", author="ada",
		classification="confirmed-defect", body="body")["work_id"]


def drain(store, **extra):
	"""Every page, followed to exhaustion through the continuation."""
	seen, after = [], None
	while True:
		page = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada",
			after=after, limit=2, **extra)
		seen.extend(row["id"] for row in page["rows"])
		after = page["next_after"]
		if after is None:
			return seen


def a_claim_between_pages_skips_nothing():
	with tempfile.TemporaryDirectory(prefix="w26328-corrected-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(4)]

		first = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada", limit=2)
		assert [row["id"] for row in first["rows"]] == made[:2]
		# THE CONTINUATION IS NOT A COUNT. An integer here is the defect,
		# because it is a value a client can do arithmetic on.
		token = first["next_after"]
		assert isinstance(token, str) and token != ""
		assert not token.lstrip("-").isdigit()

		transitions.claim_work(store, made[0], actor_team="lang", actor="ada")
		second = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada",
			after=token, limit=2)

		returned = [row["id"] for row in second["rows"]]
		print("page one:", [row["local_id"] for row in first["rows"]])
		print("page two after the earlier claim:",
		      [row["local_id"] for row in second["rows"]])
		assert made[2] in returned, "the still-actionable Work was skipped"
		assert returned == made[2:]
		return True


def a_reroute_between_pages_skips_nothing():
	with tempfile.TemporaryDirectory(prefix="w26328-corrected-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(4)]
		first = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada", limit=2)
		# The OTHER way an earlier row leaves the set: its Route stops
		# resolving to this viewer. A positional cursor cannot tell the two
		# apart, and neither may skip.
		transitions.reroute_work(store, made[0], actor_team="lang",
		                         actor="ada", to="push.bug",
		                         reason="handed to another team")
		after = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada",
			after=first["next_after"], limit=2)
		returned = [row["id"] for row in after["rows"]]
		print("page two after the earlier reroute:",
		      [row["id"].rsplit("-", 1)[1] for row in after["rows"]])
		assert returned == made[2:]
		return True


def an_insertion_before_the_cursor_repeats_nothing():
	with tempfile.TemporaryDirectory(prefix="w26328-corrected-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(4)]
		first = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada", limit=2)
		returned_first = [row["id"] for row in first["rows"]]
		# A HIGH-PRIORITY arrival sorts ahead of everything already
		# returned. It belongs to a page that has been read, so a
		# continuation may not hand it back -- deliberate refresh is the
		# path to seeing it.
		late = waiting(store, "high arrival")
		transitions.prioritize(store, late, priority="high",
		                       actor_team="lang", actor="ada")
		second = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada",
			after=first["next_after"], limit=2)
		returned = [row["id"] for row in second["rows"]]
		print("page two after the earlier high-priority arrival:",
		      [row["id"].rsplit("-", 1)[1] for row in second["rows"]])
		assert late not in returned
		assert not set(returned) & set(returned_first)
		assert returned == made[2:]
		# And a REFRESH does show it, first.
		fresh = projection.actionable_work(
			store, viewer_team="lang", viewer_member="ada", limit=2)
		assert [row["id"] for row in fresh["rows"]][0] == late
		return True


def an_undisturbed_walk_returns_every_work_exactly_once():
	with tempfile.TemporaryDirectory(prefix="w26328-corrected-") as directory:
		store = fixtures.open_instance(directory)
		made = [waiting(store, f"waiting {index}") for index in range(7)]
		walked = drain(store)
		print("full walk:", [work.rsplit("-", 1)[1] for work in walked])
		assert walked == made
		return True


if __name__ == "__main__":
	ok = [a_claim_between_pages_skips_nothing(),
	      a_reroute_between_pages_skips_nothing(),
	      an_insertion_before_the_cursor_repeats_nothing(),
	      an_undisturbed_walk_returns_every_work_exactly_once()]
	print("OK" if all(ok) else "UNSAFE")
	raise SystemExit(0 if all(ok) else 1)
