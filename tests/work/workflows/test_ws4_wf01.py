"""WS4-WF-01 — deterministic pagination and total tie-break order (R63).

Both directions of the Work/discussion relation page with bounded positive
limits, non-negative cursors, and explicit continuation state; several
labels landing at ONE sequence and several teams joining at ONE sequence
still read back in a total (added_seq, identity) order; and every page walk
completes without skips or repeats — through the real CLI/JSON surface in
source and packaged modes alike.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                     # noqa: E402
                      assert_refusal_changes_nothing, document,
                      standard_teams)


def _walk(flow, *argv, viewer, limit):
	"""Page a collection to exhaustion, returning (pages, rows)."""
	pages, rows, after = 0, [], 0
	while True:
		page = flow.ok(*argv, "--after", str(after), "--limit",
		               str(limit), viewer=viewer)
		rows += page["rows"] if "rows" in page else page["messages"]
		pages += 1
		if page["next_after"] is None:
			return pages, rows
		after = page["next_after"]


def test_ws4_wf01_paging_and_ties(flow):
	flow.init(document(standard_teams()))

	# 1. Two Works; the second discussion carries BOTH labels at one
	# sequence, given in REVERSE identity order — the projection's label
	# order is total, not insertion or luck.
	born = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	               "--title", "paging provider", "--origin",
	               "self-initiated", "--body", "root", viewer="lang.ada")
	a, d0 = born["work_id"], born["discussion"]
	sibling = flow.ok("create", "--team", "lang", "--kind", "impl",
	                  "--title", "the sibling", "--origin",
	                  "self-initiated", "--body", "leg", viewer="lang.ada")
	b, b_born = sibling["work_id"], sibling["discussion"]
	tie = flow.ok("discuss", "--body", "tie", "--label", b, "--label", a,
	              viewer="lang.ada")["discussion"]
	labels = flow.ok("thread", tie, viewer="lang.ada")["labels"]
	assert [entry["work"] for entry in labels] == sorted([a, b]), \
		"a same-sequence label tie has no total order"

	# 2. One `+*.*` joins every other team at ONE sequence; the
	# participant list still reads back in (added_seq, team) order.
	flow.post(a, "--body", "all hands", "--include", "*.*",
	        viewer="lang.ada")
	participants = flow.ok("thread", d0, viewer="lang.ada")["participants"]
	assert participants == ["lang", "mdb", "ops", "push", "web"], \
		"a same-sequence participant tie has no total order"

	# 3. Work -> discussions across pages: 8 rows in pages of 3 —
	# full, full, partial-carrying-None — no skips, no repeats.
	legs = [flow.ok("discuss", "--body", f"leg {i}", "--label", a,
	                viewer="lang.ada")["discussion"] for i in range(6)]
	expected = [d0, tie] + legs
	pages, rows = _walk(flow, "work-discussions", a, viewer="lang.grace",
	                    limit=3)
	assert pages == 3 and [row["id"] for row in rows] == expected, \
		"the Work->discussion join skipped or repeated across pages"

	# 4. The member surface in pages of 4: the same discussions plus the
	# sibling's born one, ordered by creation, exactly once each.
	pages, rows = _walk(flow, "discussions", viewer="lang.grace", limit=4)
	assert [row["id"] for row in rows] == [d0, b_born, tie] + legs, \
		"the participating-discussion join skipped or repeated"

	# 5. The message window in pages of 2 over 5 messages: strictly
	# ascending, no duplicate, final page carries the explicit None.
	for i in range(4):
		flow.ok("say", tie, "--body", f"reply {i}", viewer="lang.grace")
	pages, messages = _walk(flow, "thread", tie, viewer="lang.ada",
	                        limit=2)
	seqs = [message["seq"] for message in messages]
	assert pages == 3 and seqs == sorted(set(seqs)) and len(seqs) == 5, \
		"the message window skipped or repeated across pages"

	# 6. The bounds are refusals, not clamps — and refuse changing
	# nothing: negative cursor, zero and over-max limits, and a mark-seen
	# cursor beyond the observed sequence.
	for argv in (("thread", tie, "--after", "-1"),
	             ("thread", tie, "--limit", "0"),
	             ("thread", tie, "--limit", "501"),
	             ("thread", tie, "--limit", "1000"),
	             ("work-discussions", a, "--limit", "600"),
	             ("discussions", "--after", "-1")):
		error = assert_refusal_changes_nothing(flow, "lang.ada", *argv)
		assert "pagination cursor" in error or "page limit" in error, \
			f"{argv} was clamped instead of refused"
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "mark-seen", tie, "--up-to", "999999")
	assert "beyond the observed" in error

	# 7. R67: a relation added to OLD context after a page cursor has
	# advanced is discovered by the very next page, exactly once — in
	# both directions of the relation.
	late = flow.ok("create", "--team", "lang", "--kind", "bug",
	               "--title", "late", "--origin", "self-initiated",
	               "--body", "late", viewer="lang.ada")
	first = flow.ok("work-discussions", late["work_id"], "--limit", "1",
	                viewer="lang.ada")
	assert [row["id"] for row in first["rows"]] == [late["discussion"]]
	flow.ok("label", d0, "--work", late["work_id"], viewer="lang.ada")
	found = flow.ok("work-discussions", late["work_id"], "--after",
	                str(first["next_after"]), "--limit", "1",
	                viewer="lang.ada")
	assert [row["id"] for row in found["rows"]] == [d0], \
		"a label added to old context fell behind the page cursor"
	tail = flow.ok("work-discussions", late["work_id"], "--after",
	               str(found["next_after"]), "--limit", "1",
	               viewer="lang.ada")
	assert tail["rows"] == [] and tail["next_after"] is None, \
		"the late label was discovered more than once"

	# The attention surface, same shape: push holds a full first page,
	# then joins the OLD tie discussion by speaking in it.
	push_born = flow.ok("create", "--team", "push", "--kind", "bug",
	                    "--title", "push local", "--origin",
	                    "self-initiated", "--body", "local",
	                    viewer="push.sl")["discussion"]
	first = flow.ok("discussions", "--limit", "2", viewer="push.sl")
	assert [row["id"] for row in first["rows"]] == [d0, push_born]
	flow.ok("say", tie, "--body", "push joins old context now",
	        viewer="push.sl")
	found = flow.ok("discussions", "--after", str(first["next_after"]),
	                "--limit", "2", viewer="push.sl")
	assert [row["id"] for row in found["rows"]] == [tie], \
		"new participation in old context fell behind the page cursor"
	assert found["next_after"] is None

	# 8. R69: Work detail advertises no removed Work-addressed operation;
	# the surviving public posting/seen surface names a discussion.
	advertised = flow.ok("detail", a,
	                     viewer="lang.ada")["available_transitions"]
	assert "post_message" not in advertised and \
		"mark_seen" not in advertised, \
		"detail advertises a removed Work-addressed bridge"

	assert_dense_audit(flow, "lang.ada")
