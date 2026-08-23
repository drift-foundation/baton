"""W17: the dependency-neighbor action reads `[b] deps`, never `b links`.

The footer's compressed `b links` read as "blinks" and was mistaken for
the hot-zone cue (finding-tui-dependency-key-label). The label is now
`[b] deps` — brackets separating the key from its meaning, `deps`
covering blocker and dependent neighbors alike. Wording only: the `b`
binding, the links projection, the empty state, JSON, and the protocol
are untouched.
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
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

import pty as _pty                                            # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


def build(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	consumer = tr.create_work(store, team="lang", kind="bug",
	                          title="consumer", origin="external-report",
	                          classification="suspected-defect",
	                          author="ada", body="b")["work_id"]
	blocker = tr.create_work(store, team="lang", kind="bug",
	                         title="the blocker",
	                         origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="b")["work_id"]
	tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	store.close()
	return config


def test_the_footer_reads_deps_wide_and_the_key_still_works(tmp_path):
	"""Wide: the footer advertises `[b] deps`; the ambiguous `b links`
	is gone everywhere on screen; pressing b still opens the neighbor
	view with its unchanged facts, and Esc returns."""
	config = build(tmp_path)
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6),
		# W7: `the blocker` is ready and unclaimed and now leads the
		# pool, so `j` reaches `consumer` — whose neighbor view is what
		# this test has always read.
		(b"jb", 0.5),                 # the binding is untouched
		(b"\x1b", 0.4),               # back to the table
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	table = "\n".join(ptyharness.replay(steps[0]))
	assert "[b] deps" in table, "the footer does not advertise [b] deps"
	assert "b links" not in table, "the ambiguous label survived"
	neighbors = "\n".join(ptyharness.replay(steps[1]))
	# W4996 replaced the flat blocked-by/blocks list with the dependency
	# NEIGHBOURHOOD graph, whose approved presentation is stable selectors
	# rather than titles. This Work's subject is the LABEL, and its
	# property here is that `b` still opens the neighbour view — asserted
	# in the terms the ruled view actually draws.
	assert "--blocks-->" in neighbors, \
		"the b binding no longer opens the neighbor view"
	assert "depth 1/3" in neighbors, neighbors
	back = "\n".join(ptyharness.replay(steps[2]))
	assert "[b] deps" in back, "the label did not survive the return"


def test_the_label_reads_deps_at_narrow_width_too(tmp_path):
	"""Narrow: the same `[b] deps` label, whole — never re-compressed
	into the ambiguous form — and the empty state is unchanged."""
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	tr.create_work(store, team="lang", kind="bug", title="lonely",
	               origin="external-report",
	               classification="suspected-defect",
	               author="ada", body="b")
	store.close()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6),
		(b"b", 0.5),                  # empty neighbor view
		(b"qy", 0.4),
	], columns=60, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	table = "\n".join(ptyharness.replay(steps[0], columns=60, lines=24))
	assert "[b] deps" in table, table
	assert "b links" not in table
	empty = "\n".join(ptyharness.replay(steps[1], columns=60, lines=24))
	assert "(no blocking or dependent neighbors)" in empty, \
		"the empty-state text changed with the label"
