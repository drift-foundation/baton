"""W1217: the Event reader names only meaningful relationships.

`work/records/2026/08/finding-event-relation-display/`. Every row in a
Work's Events tab is there because it relates to that Work, so a
`roles: subject` line restated the view and spent a line doing it — in
vocabulary that reads like a member role rather than an Event
relationship.

The typed relationship is not redundant in general: `consumer`,
`blocker`, `parent`, `provider` and their kin explain why an Event that
primarily concerns ANOTHER Work appears here, which an operator cannot
infer from the row. Those are named.

The ruling: omit the line when `subject` is the only value; render
`relation: X` for one meaningful value and `relations: X, Y` for
several; never show `subject` beside a meaningful one. The canonical
`roles` array is untouched — this is the reader deciding what to say,
not the projection deciding what to hold, and these tests assert that
distinction directly.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import Console, soft_wrap               # noqa: E402
import fixtures as fx                                          # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		          "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	return {"store": store, "config": config_path}


def make(world, title="the work", parent=None, follow_up_of=None):
	extra = {}
	if parent:
		extra["parent"] = parent
	if follow_up_of:
		extra["follow_up_of"] = follow_up_of
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b", **extra)


def console(world):
	return Console(world["store"], "lang", "ada",
	               config_path=world["config"])


def events(world, work):
	return pj.work_events(world["store"], work)["events"]


def reader(world, work):
	"""Every Event of one Work as the reader renders it."""
	view = console(world)
	return {entry["seq"]: view._event_lines(entry)
	        for entry in events(world, work)}


def relation_rows(lines):
	return [line.strip() for line in lines
	        if line.strip().startswith(("relation:", "relations:",
	                                    "roles:"))]


# -- the redundant row is gone ------------------------------------------------

def test_a_direct_event_says_nothing_about_its_relationship(world):
	born = make(world)
	for seq, lines in reader(world, born["work_id"]).items():
		assert relation_rows(lines) == [], (seq, lines)


def test_every_ordinary_transition_stays_quiet(world):
	"""create, claim, pass, close — the Events an operator reads most,
	and the ones that were spending a line on `subject`."""
	born = make(world)
	work = born["work_id"]
	store = world["store"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.rsrch", comment="over to you")
	# the fixture's one route resolves to `ada`, so the pass moves the
	# endpoint without moving who may claim
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	kinds = {entry["seq"]: entry["kind"] for entry in events(world, work)}
	for seq, lines in reader(world, work).items():
		assert relation_rows(lines) == [], (kinds[seq], lines)
	assert {"create_work", "claim", "pass", "close_work"} <= set(
		kinds.values()), sorted(set(kinds.values()))


def test_the_word_roles_is_gone_from_the_reader(world):
	"""It read like a member role, which is what made it worse than
	merely redundant."""
	born = make(world)
	work = born["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	for lines in reader(world, work).values():
		assert not any("roles:" in line for line in lines), lines


# -- meaningful relationships are named ---------------------------------------

def test_a_cross_linked_event_names_its_one_relationship(world):
	consumer = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="the prerequisite")

	def rows(work):
		return [row for lines in reader(world, work).values()
		        for row in relation_rows(lines)]

	assert rows(consumer) == ["relation: consumer"]
	assert rows(blocker) == ["relation: blocker"]


def test_the_two_ends_of_one_dependency_read_differently(world):
	"""Direction is the point: the same Event says something different
	from each side, and neither says `subject`."""
	consumer = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="the prerequisite")
	from_consumer = [line for lines in reader(world, consumer).values()
	                 for line in lines if "relation" in line]
	from_blocker = [line for lines in reader(world, blocker).values()
	                for line in lines if "relation" in line]
	assert from_consumer != from_blocker
	assert "subject" not in "".join(from_consumer + from_blocker)


def test_a_parent_sees_the_childs_creation_as_a_relationship(world):
	parent = make(world, "the parent")["work_id"]
	make(world, "the child", parent=parent)
	rows = [row for lines in reader(world, parent).values()
	        for row in relation_rows(lines)]
	assert "relation: parent" in rows, rows


def test_a_predecessor_sees_its_follow_up(world):
	first = make(world, "the first attempt")["work_id"]
	tr.claim_work(world["store"], first, actor_team="lang", actor="ada")
	tr.close_work(world["store"], first, actor_team="lang", actor="ada",
	              outcome="non-satisfying", rationale="superseded")
	make(world, "the follow-up", follow_up_of=first)
	rows = [row for lines in reader(world, first).values()
	        for row in relation_rows(lines)]
	assert "relation: predecessor" in rows, rows


def test_several_meaningful_values_are_all_kept_and_ordered(world):
	"""The plural label, asserted on the reader's own formatter so the
	case does not depend on finding an Event that happens to carry two
	relationships."""
	view = console(world)
	entry = dict(events(world, make(world)["work_id"])[0])
	entry["roles"] = ["consumer", "parent", "provider"]
	lines = view._event_lines(entry)
	assert relation_rows(lines) == \
		["relations: consumer, parent, provider"], lines
	# and the order is the projection's, not re-sorted
	entry["roles"] = ["provider", "consumer"]
	assert relation_rows(view._event_lines(entry)) == \
		["relations: provider, consumer"]


def test_subject_is_never_shown_beside_a_meaningful_value(world):
	"""`close_work` on a duplicate target carries both; the baseline
	must not ride along."""
	view = console(world)
	entry = dict(events(world, make(world)["work_id"])[0])
	entry["roles"] = ["subject", "duplicate_target"]
	assert relation_rows(view._event_lines(entry)) == \
		["relation: duplicate_target"]
	entry["roles"] = ["subject", "parent", "provider"]
	assert relation_rows(view._event_lines(entry)) == \
		["relations: parent, provider"]


# -- the projection keeps everything ------------------------------------------

def test_the_canonical_roles_array_is_untouched(world):
	consumer = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada", rationale="r")
	for work, expected in ((consumer, "consumer"), (blocker, "blocker")):
		roles = [entry["roles"] for entry in events(world, work)]
		assert all(isinstance(entry, list) and entry for entry in roles)
		assert any(expected in entry for entry in roles), (work, roles)
	# every direct Event still carries `subject` in JSON
	plain = make(world, "plain")["work_id"]
	assert [entry["roles"] for entry in events(world, plain)] == \
		[["subject"]]


def test_the_reader_reads_and_writes_nothing(world):
	work = make(world)["work_id"]
	before = world["store"].last_seq()
	reader(world, work)
	assert world["store"].last_seq() == before


# -- narrow and wrapped -------------------------------------------------------

@pytest.mark.parametrize("width", [120, 60, 40, 24])
def test_the_label_and_every_value_survive_wrapping(world, width):
	view = console(world)
	entry = dict(events(world, make(world)["work_id"])[0])
	entry["roles"] = ["consumer", "duplicate_target", "predecessor"]
	wrapped = []
	for line in view._event_lines(entry):
		wrapped.extend(soft_wrap(line, width))
	joined = " ".join(piece.strip() for piece in wrapped)
	assert "relations:" in joined, (width, wrapped[:6])
	for value in ("consumer", "duplicate_target", "predecessor"):
		assert value in joined, (width, value)


def test_the_related_work_rows_are_untouched(world):
	"""W123's `related:` rows name the OTHER Work and its role; this
	Work changes the relationship line above them and nothing else."""
	consumer = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada", rationale="r")
	lines = [line for entry in reader(world, consumer).values()
	         for line in entry]
	assert any(line.strip() == f"related: {blocker} (blocker)"
	           for line in lines), lines
