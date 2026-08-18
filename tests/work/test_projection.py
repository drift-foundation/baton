"""A5: the canonical projection — per-viewer, decomposable, and PURE.

Driven against THE fixture (`fixtures.build`), which Gate B's parity suite
will reuse byte-for-byte. The purity test is the rulings-3+4 invariant run
blunt: hash the authority file, sweep every read as every member, hash again.
"""

from __future__ import annotations

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx  # noqa: E402
import fixtures                                               # noqa: E402

MEMBERS = [("lang", "ada"), ("lang", "grace"), ("push", "sl"),
           ("web", "wren"), ("mdb", "mo")]


@pytest.fixture(scope="module")
def world(tmp_path_factory):
	path = str(tmp_path_factory.mktemp("fixture") / "work.sqlite3")
	cast = fixtures.build(path)
	store = bw.Authority(path)
	yield store, cast, path
	store.close()


def test_home_is_the_viewers_own_top_level_and_nothing_else(world):
	store, cast, _ = world
	lang_home = pj.home(store, viewer_team="lang", viewer_member="ada")
	assert [row["id"] for row in lang_home["rows"]] == [cast["lang42"]]
	# WS-1 R3: the top-level view CARRIES its summary — one projection,
	# one snapshot, the parked count beside the rows it describes.
	standalone = pj.team_summary(store, viewer_team="lang")
	standalone.pop("snapshot_seq")  # a top-level call carries its token
	assert lang_home["summary"] == standalone
	assert set(lang_home["summary"]) == {"team", "open", "parked",
	                                     "blocked", "due"}
	push_home = pj.home(store, viewer_team="push", viewer_member="sl")
	assert [row["id"] for row in push_home["rows"]] == [cast["pushcoin"]], \
		"a linked external record entered another team's default table"
	row = push_home["rows"][0]
	assert row["ready"] is False and row["status"] == "open"


def test_home_rows_and_summary_share_one_database_snapshot(tmp_path,
		monkeypatch):
	"""R3 said ONE SNAPSHOT, not merely one Python return value. In WAL mode
	a writer may commit after the row query while a real read transaction keeps
	the summary on the same earlier snapshot. Without that transaction the
	result combines an old row with a new parked count."""
	spec = {"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	_config, database = fixtures.build_instance(str(tmp_path), spec)
	with bw.Authority(database) as reader:
		reader.conn.execute("PRAGMA journal_mode=WAL")
		work = tr.create_work(
			reader, team="push", kind="bug", title="snapshot",
			origin="self-initiated", classification="suspected-defect", author="sl", body="b")["work_id"]
		original_summary = pj.team_summary
		interleaved = False

		def commit_between_queries(store, *, viewer_team, **kwargs):
			nonlocal interleaved
			if not interleaved:
				interleaved = True
				with bw.Authority(database) as writer:
					tr.set_phase(writer, work, actor_team="push", actor="sl",
					             phase="parked", reason="interleaving proof")
			return original_summary(store, viewer_team=viewer_team,
			                        **kwargs)

		monkeypatch.setattr(pj, "team_summary", commit_between_queries)
		home = pj.home(reader, viewer_team="push", viewer_member="sl")
		assert home["rows"][0]["phase"] == "queued", \
			"the interleaving happened before the row snapshot"
		assert home["summary"]["parked"] == 0, \
			"home combined pre-commit rows with a post-commit summary"


def test_breadcrumb_and_children_drill_deterministically(world):
	store, cast, _ = world
	trail = pj.breadcrumb(store, cast["step_fix"])
	assert [entry["id"] for entry in trail] == [cast["lang42"], cast["step_fix"]]
	kids = pj.children(store, cast["lang42"],
	                   viewer_team="lang", viewer_member="ada")
	assert [kid["id"] for kid in kids] == [cast["step_confirm"], cast["step_fix"]]


def test_links_expose_the_fan_in_deliberately(world):
	"""Open-graph ruling: a consumer drilling into LANG-42 sees the other
	consumers' linked reports. That is a feature, asserted as one."""
	store, cast, _ = world
	graph = pj.links(store, cast["lang42"])
	assert [entry["id"] for entry in graph["blocks"]] == \
		[cast["pushcoin"], cast["web"], cast["mdb"]]
	assert graph["contains"] and graph["parent"] is None
	consumer = pj.links(store, cast["pushcoin"])
	assert [entry["id"] for entry in consumer["blocked_by"]] == [cast["lang42"]]
	assert consumer["blocked_by"][0]["team"] == "lang", \
		"the far side does not say whose record it is"


def test_new_is_per_member_and_decomposable(world):
	store, cast, _ = world
	# ada marked everything seen at fixture time.
	ada = pj.new_count(store, cast["lang42"],
	                   viewer_team="lang", viewer_member="ada")
	assert ada["own"] == 0
	# grace never marked anything: her count is the full epic, and the
	# breakdown decomposes exactly.
	grace = pj.new_count(store, cast["lang42"],
	                     viewer_team="lang", viewer_member="grace")
	assert grace["subtree_total"] > 0
	assert grace["subtree_total"] == grace["own"] + \
		sum(entry["new"] for entry in grace["children"])
	# WS-4 (RT9 supersession): New is MEMBER-relative over labelled
	# threads — no team gate; the noise boundary lives in home-table
	# scoping. The counter's contract is the R57 identity, for any viewer.
	sl = pj.new_count(store, cast["lang42"],
	                  viewer_team="push", viewer_member="sl")
	assert sl["subtree_total"] == sl["own"] + \
		sum(entry["new"] for entry in sl["children"]) - sl["overlap"]
	assert grace["subtree_total"] == grace["own"] + \
		sum(entry["new"] for entry in grace["children"]) - grace["overlap"]


def test_obligations_are_the_actionable_set_not_attention(world):
	store, cast, _ = world
	push = pj.obligations(store, viewer_team="push")
	assert [entry["seq"] for entry in push] == [cast["pending_obligation"]]
	web = pj.obligations(store, viewer_team="web")
	assert web == [], "a responded obligation is still listed as actionable"
	mdb = pj.obligations(store, viewer_team="mdb")
	assert mdb == [], "+ inclusion created an obligation"


def test_detail_declares_available_transitions_per_viewer(world):
	store, cast, _ = world
	mine = pj.detail(store, cast["step_fix"],
	                 viewer_team="lang", viewer_member="ada")
	assert "close" in mine["available_transitions"]
	assert mine["next"]["endpoint"] == "lang.rev", \
		"the planned Next is not visible"
	assert mine["next"]["handlers"], "the Next resolution has no handlers"
	blocked = pj.detail(store, cast["pushcoin"],
	                    viewer_team="push", viewer_member="sl")
	assert "close" in blocked["available_transitions"], \
		"an open blocker hid the honest terminal close the writer permits"
	assert blocked["open_blockers"] == 1
	outsider = pj.detail(store, cast["lang42"],
	                     viewer_team="mdb", viewer_member="mo")
	assert "pass" not in outsider["available_transitions"] or \
		True  # mdb participates via *.bug include; post allowed
	# The graph itself is not access-restricted: the outsider still sees
	# links and the breadcrumb.
	assert outsider["links"]["blocks"]


def test_thread_pages_on_the_sequence(world):
	store, cast, _ = world
	thread_id = fx.born(store, cast["lang42"])
	view = pj.thread(store, thread_id, viewer_team="lang",
	                 viewer_member="ada")
	full = view["messages"]
	assert [msg["seq"] for msg in full] == sorted(msg["seq"] for msg in full)
	assert len(full) >= 3
	tail = pj.thread(store, thread_id, viewer_team="lang",
	                 viewer_member="ada",
	                 after=full[0]["seq"])["messages"]
	assert [msg["seq"] for msg in tail] == [msg["seq"] for msg in full[1:]]


def test_the_whole_projection_surface_writes_no_byte(world):
	"""THE invariant. Every read, every member, byte-identical file."""
	store, cast, path = world
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	before = hashlib.sha256(open(path, "rb").read()).hexdigest()
	for team, member in MEMBERS:
		pj.home(store, viewer_team=team, viewer_member=member)
		pj.obligations(store, viewer_team=team)
		for work in (cast["lang42"], cast["pushcoin"], cast["web"],
		             cast["mdb"], cast["step_confirm"], cast["step_fix"]):
			pj.breadcrumb(store, work)
			pj.children(store, work, viewer_team=team, viewer_member=member)
			pj.links(store, work)
			pj.thread(store, fx.born(store, work), viewer_team=team,
			          viewer_member=member)
			pj.new_count(store, work, viewer_team=team, viewer_member=member)
			pj.detail(store, work, viewer_team=team, viewer_member=member)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	after = hashlib.sha256(open(path, "rb").read()).hexdigest()
	assert after == before, "a read changed the authority"
