"""W71: the superseding navigation contract (final schema-14 item).

Main screen: a bounded three-level containment tree (roots, ↳ children
and their children — W155 superseded W71's two-level cap,
disclosure counts for deeper children). Enter has ONE meaning — open the
Work detail; `u` unfolds/re-roots with real breadcrumbs. The detail view
stacks the Threads list above the selected Thread's Messages with Ctrl-W
pane navigation, explicit seen, a separate Refs section, and no internal
`after #N` cursor anywhere. JSON replaces `dep` with `open_blockers` /
`open_dependents`.
"""

from __future__ import annotations

import json as _json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	root = tr.create_work(store, team="lang", kind="bug",
	                      title="the root", origin="external-report", classification="suspected-defect",
	                      author="ada", body="root opener")
	child = tr.create_work(store, team="lang", kind="bug",
	                       title="the child", origin="decomposition", classification="suspected-defect",
	                       author="ada", body="child opener",
	                       parent=root["work_id"])
	grand = tr.create_work(store, team="lang", kind="bug",
	                       title="the grandchild",
	                       origin="decomposition", classification="suspected-defect", author="ada",
	                       body="grand opener",
	                       parent=child["work_id"])
	cast = {"config": config_path, "database": database, "root": root,
	        "child": child, "grand": grand}
	store.close()
	return cast


def test_the_tree_is_three_levels_with_disclosure(world):
	"""W155 supersedes W71's two-level cap: root, child and grandchild
	paint together, each at its own fixed indent, and the deepest
	visible row discloses anything below it.

	W154's rule is unchanged and composes here — the disclosure sits in
	reserved structural space ahead of the title, so no title length can
	delete it. Only the level that carries it moved, because a
	grandchild is now visible rather than hidden.
	"""
	text, status, _steps = ptyharness.drive(world["config"], "lang.ada",
	                                        [(b"qy", 0.4)])
	screen = ptyharness.replay(text)
	flat = "\n".join(screen)
	assert "the root" in flat
	assert "↳ the child" in flat, \
		f"the containment child is missing: {flat[:400]}"
	assert "  ↳ the grandchi" in flat, \
		f"the third level does not paint: {flat[:400]}"
	# the child's children are now INSIDE the window, so it discloses
	# nothing; there is nothing hidden under it to disclose.
	child_row = next(line for line in screen
	                 if "↳ the child" in line)
	assert "▸" not in child_row, child_row
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_unfold_re_roots_and_esc_returns(world):
	"""u on the ↳ child re-roots the window (child + grandchild) with a
	real breadcrumb; Esc returns upward to the root view."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"j", 0.4),                  # select ↳ the child
		(b"u", 0.5),                  # re-root
		(b"\x1b", 0.5),               # back up
		(b"qy", 0.4),
	])
	rooted = ptyharness.replay(steps[1])
	assert "the root > the child" in rooted[0], \
		f"the re-rooted breadcrumb is wrong: {rooted[0]!r}"
	assert any("↳ the grandchild" in line for line in rooted)
	back = ptyharness.replay(steps[2])
	assert back[0].startswith("[Jobs]"), "Esc did not return upward"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_unfolding_the_current_root_is_idempotent(world):
	"""Once a Work is the root of the sliding window, `u` on that same
	row is a no-op: it must not duplicate the breadcrumb or require an
	extra Esc to return to the previous level."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"u", 0.5),                  # root at "the root"
		(b"u", 0.5),                  # must not append it again
		(b"\x1b", 0.5),               # one Back returns home
		(b"qy", 0.4),
	])
	twice = ptyharness.replay(steps[1])
	assert "the root > the root" not in twice[0], \
		f"the re-root stack duplicated its current Work: {twice[0]!r}"
	back = ptyharness.replay(steps[2])
	assert back[0].startswith("[Jobs]") and " > " not in back[0], \
		f"one Esc did not return from one logical unfold: {back[0]!r}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_enter_opens_details_never_drills(world):
	"""Enter on a parent opens ITS detail (threads/messages) — the
	child table does not replace the view; the breadcrumb names the
	detailed Work."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),                 # detail of "the root"
		(b"qy", 0.4),
	])
	detail = ptyharness.replay(steps[0])
	assert "the root" in detail[0], detail[0]
	flat = "\n".join(detail)
	assert "Threads (1)" in flat, "the detail lost its thread list"
	assert "root opener" in flat, "the selected thread's messages missing"
	assert "↳" not in flat, "Enter drilled into children"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_ctrl_w_moves_panes_and_footer_advertises(world):
	"""Ctrl-W j focuses the Msgs pane, Ctrl-W k returns, Ctrl-W Ctrl-W
	cycles; the footer advertises the controls; no after-cursor text
	appears anywhere."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),
		(b"\x17j", 0.5),              # Ctrl-W j → the Message index
		(b"\x17j", 0.5),              # Ctrl-W j → the reader (W14)
		(b"\x17\x17", 0.5),           # Ctrl-W Ctrl-W → cycle to Threads
		(b"qy", 0.4),
	])
	opened = "\n".join(ptyharness.replay(steps[0]))
	assert "»Threads" in opened, "the Threads pane focus marker missing"
	assert "Ctrl-W panes" in opened, "the footer does not advertise Ctrl-W"
	assert "after #" not in opened, \
		"the internal projection cursor leaked (W71)"
	msgs = "\n".join(ptyharness.replay(steps[1]))
	assert "»Messages (" in msgs, \
		"Ctrl-W j did not focus the Message index"
	reader = "\n".join(ptyharness.replay(steps[2]))
	# W30: the reader heading is gone. Focus now shows on the reader's
	# own metadata row, and the index heading beside it drops its
	# marker — the two panes share one row, so both halves are checked.
	assert "»#" in reader and "»Messages (" not in reader, \
		"the second Ctrl-W j did not focus the reader"
	cycled = "\n".join(ptyharness.replay(steps[3]))
	assert "»Threads" in cycled, "Ctrl-W Ctrl-W did not cycle to Threads"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_json_replaces_dep_with_explicit_graph_fields(world):
	"""open_blockers/open_dependents replace the ambiguous dep; both are
	live counts and progress survives."""
	store = bw.Authority(world["database"])
	provider = world["root"]["work_id"]
	consumer = tr.create_work(store, team="push", kind="bug",
	                          title="consumer",
	                          origin="external-report", classification="suspected-defect", author="sl",
	                          body="waits")["work_id"]
	tr.add_dependency(store, consumer, provider, actor_team="push",
	                  actor="sl", rationale="test dependency")
	provider_row = pj.detail(store, provider, viewer_team="lang",
	                         viewer_member="ada")
	consumer_row = pj.detail(store, consumer, viewer_team="push",
	                         viewer_member="sl")
	assert "dep" not in provider_row
	assert provider_row["open_dependents"] == 1
	assert provider_row["open_blockers"] == 0
	assert consumer_row["open_blockers"] == 1
	assert consumer_row["open_dependents"] == 0
	assert provider_row["progress"]["children"] == 1
	# The close withdraws the live edge from BOTH counts.
	tr.close_work(store, consumer, actor_team="push", actor="sl",
	              rationale="done", outcome="cancelled")
	assert pj.detail(store, provider, viewer_team="lang",
	                 viewer_member="ada")["open_dependents"] == 0
	store.close()


def test_refs_render_under_a_separate_section(world):
	"""References appear under an explicit Refs heading, one canonical
	reference per line — never as body text."""
	store = bw.Authority(world["database"])
	config = _json.load(open(world["config"]))
	config["generation"] = 2
	config["roots"] = {"pushcoin": {"display": "PushCoin", "base": "/srv/checkouts/pushcoin"}}
	with open(world["config"], "w") as handle:
		_json.dump(config, handle, indent=2, sort_keys=True)
	lc.accept_config(world["config"], actor="lang.ada")
	tr.post_thread(store, world["root"]["thread"], author_team="lang",
	               author="ada", body="see the trace",
	               refs=["pushcoin:docs/trace.md"])
	store.close()
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),
		# W76: the index reads newest-first, so the LAST posted message
		# is the entry selection — no walk needed.
		(b"\x17j", 0.4),              # W14: the Message index
		(b"qy", 0.4)])
	screen = ptyharness.replay(steps[1])
	flat = "\n".join(screen)
	# W14: the selected message's block paints in the READER.
	assert "  Refs:" in flat, f"the Refs heading is missing"
	assert "[pushcoin:docs/trace.md]" in flat, \
		"the reference is not its own indented line"
	body_line = next(line for line in screen
	                 if "see the trace" in line)
	assert "pushcoin" not in body_line, "the ref crowded the body line"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_a_mid_read_commit_cannot_produce_a_mixed_tree(world, monkeypatch):
	"""W71 R3: the tree window is ONE canonical projection under one read
	transaction. A writer committing between the projection's internal row
	reads must be entirely invisible: no new root appears, every painted
	row keeps the pre-commit state, and the snapshot token names the
	pre-commit sequence — never a mix of two authority states."""
	database = world["database"]
	with bw.Authority(database) as reader:
		reader.conn.execute("PRAGMA journal_mode=WAL")
		before_seq = reader.last_seq()
		original_row_view = pj._row_view
		interleaved = False

		def commit_between_row_reads(store, row, viewer_team,
		                             viewer_member, **kwargs):
			nonlocal interleaved
			if not interleaved:
				interleaved = True
				with bw.Authority(database) as writer:
					# W38 R1: the root has open children, so it is
					# `waiting` and cannot be parked. The interloper is
					# a leaf, and parking it is the same interleaving
					# proof — a second visible commit mid-read.
					interloper = tr.create_work(
						writer, team="lang", kind="bug",
						title="the interloper",
						origin="external-report", classification="suspected-defect", author="ada",
						body="committed mid-read")["work_id"]
					tr.set_phase(
						writer, interloper,
						actor_team="lang", actor="ada",
						phase="parked",
						reason="interleaving proof")
			return original_row_view(store, row, viewer_team,
			                         viewer_member, **kwargs)

		monkeypatch.setattr(pj, "_row_view", commit_between_row_reads)
		window = pj.tree(reader, viewer_team="lang", viewer_member="ada")
		assert interleaved, "the interleaved writer never ran"
		titles = [row["title"] for row in window["rows"]]
		assert "the interloper" not in titles, \
			"a mid-read commit leaked a new root into the tree"
		root_row = next(row for row in window["rows"]
		                if row["title"] == "the root")
		# W38 R1: the root has open children, so its snapshot phase is
		# `waiting` — the point is that it is the PRE-commit value.
		assert root_row["phase"] == "block", \
			"the tree mixed a post-commit phase into pre-commit rows"
		assert window["summary"]["parked"] == 0, \
			"the summary came from a later snapshot than the rows"
		assert window["snapshot_seq"] == before_seq, \
			"the snapshot token does not name the painted state"
