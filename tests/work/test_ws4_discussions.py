"""WS-4 Slice A: first-class discussions, inert `#WORK` labels, live
context, per-discussion cursors, and overlap-explicit New.

Every assertion traces to the pinned rulings and R54–R60: one message
belongs to one discussion; labels are foreign-key-bound inert context
authorized by the owning team; a discussion is born labelled and speaking
and always keeps explicit Work scope; posting requires live context;
participation is monotonic; New is member-relative, distinct-counted, and
decomposed as total = own + sum(children) - overlap.
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
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402

import json as _json


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store
	store.close()


def _create(store, team="lang", member="ada", **kw):
	return tr.create_work(store, team=team, kind="bug", title="w",
	                      origin="external-report", author=member,
	                      body="born speaking", **kw)


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


# -- creation atomicity -------------------------------------------------------

def test_work_is_born_with_a_labelled_speaking_discussion(world):
	store = world
	result = _create(store)
	work, discussion = result["work_id"], result["discussion"]
	assert discussion.endswith(f"-D{result['seq']}")
	view = pj.thread(store, discussion, viewer_team="lang",
	                 viewer_member="ada")
	assert [entry["work"] for entry in view["labels"]] == [work]
	assert view["participants"] == ["lang"]
	assert len(view["messages"]) == 1
	assert view["messages"][0]["seq"] == result["seq"], \
		"the first message is not atomic with the creation"
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert [entry["id"] for entry in detail["discussions"]] == [discussion]


def test_create_discussion_requires_authorized_live_labels(world):
	store = world
	open_work = _create(store)["work_id"]
	closed = _create(store)["work_id"]
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	foreign = _create(store, team="push", member="sl")["work_id"]
	with pytest.raises(bw.WorkError, match="at least one authorized"):
		tr.create_discussion(store, actor_team="lang", actor="ada",
		                     body="b", labels=[])
	with pytest.raises(bw.WorkError, match="labelled only by"):
		tr.create_discussion(store, actor_team="lang", actor="ada",
		                     body="b", labels=[foreign])
	with pytest.raises(bw.WorkError, match="live-context"):
		tr.create_discussion(store, actor_team="lang", actor="ada",
		                     body="b", labels=[closed])
	with pytest.raises(bw.WorkError, match="applied once"):
		tr.create_discussion(store, actor_team="lang", actor="ada",
		                     body="b", labels=[open_work, open_work])
	# Spanning terminal and open context is fine — one open label carries.
	result = tr.create_discussion(store, actor_team="lang", actor="ada",
	                              body="cross-phase context",
	                              labels=[open_work, closed])
	view = pj.thread(store, result["discussion"], viewer_team="lang",
	                 viewer_member="ada")
	assert {entry["work"] for entry in view["labels"]} == \
		{open_work, closed}


# -- labels: authority and inertness ------------------------------------------

def test_labels_are_owning_team_scoped_both_ways(world):
	store = world
	mine = _create(store)
	theirs = _create(store, team="push", member="sl")
	with pytest.raises(bw.WorkError, match="labelled only by"):
		tr.label_discussion(store, mine["discussion"],
		                    theirs["work_id"], actor_team="lang",
		                    actor="ada")
	tr.label_discussion(store, mine["discussion"], theirs["work_id"],
	                    actor_team="push", actor="sl")
	with pytest.raises(bw.WorkError, match="already carries"):
		tr.label_discussion(store, mine["discussion"], theirs["work_id"],
		                    actor_team="push", actor="sl")
	with pytest.raises(bw.WorkError, match="labelled only by"):
		tr.unlabel_discussion(store, mine["discussion"],
		                      theirs["work_id"], actor_team="lang",
		                      actor="ada")
	tr.unlabel_discussion(store, mine["discussion"], theirs["work_id"],
	                      actor_team="push", actor="sl")
	with pytest.raises(bw.WorkError, match="does not carry"):
		tr.unlabel_discussion(store, mine["discussion"],
		                      theirs["work_id"], actor_team="push",
		                      actor="sl")


def test_a_label_is_inert_everywhere(world):
	"""The whole point of `#`: context, never a gate. Labelling changes no
	readiness, DEP, phase, Current, obligation, or edge — byte-for-byte
	beyond the label rows and their audit."""
	store = world
	consumer = _create(store)
	provider = _create(store, team="push", member="sl")
	before = {
		"work": [dict(row) for row in store.conn.execute(
			"SELECT * FROM work ORDER BY id")],
		"edges": store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges").fetchone()["n"],
		"obligations": store.conn.execute(
			"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"],
	}
	tr.label_discussion(store, consumer["discussion"],
	                    provider["work_id"], actor_team="push", actor="sl")
	after_work = [dict(row) for row in store.conn.execute(
		"SELECT * FROM work ORDER BY id")]
	assert after_work == before["work"], "a label touched a work row"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == \
		before["edges"], "a label created a dependency"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"] == \
		before["obligations"]
	assert pj.detail(store, provider["work_id"], viewer_team="push",
	                 viewer_member="sl")["dep"] == 0
	# Terminal work may be labelled; still inert.
	tr.close_work(store, provider["work_id"], actor_team="push",
	              actor="sl", rationale="done", outcome="satisfying")
	other = tr.create_discussion(store, actor_team="push", actor="sl",
	                             body="retro",
	                             labels=[_create(store, team="push",
	                                             member="sl")["work_id"]])
	tr.label_discussion(store, other["discussion"], provider["work_id"],
	                    actor_team="push", actor="sl")


def test_the_final_label_never_leaves(world):
	store = world
	first = _create(store)
	second = _create(store)
	tr.label_discussion(store, first["discussion"], second["work_id"],
	                    actor_team="lang", actor="ada")
	tr.unlabel_discussion(store, first["discussion"], second["work_id"],
	                      actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError, match="final label"):
		tr.unlabel_discussion(store, first["discussion"],
		                      first["work_id"], actor_team="lang",
		                      actor="ada")


# -- live context --------------------------------------------------------------

def test_posting_requires_a_labelled_open_work(world):
	store = world
	result = _create(store)
	tr.post_discussion(store, result["discussion"], author_team="push",
	                   author="sl", body="any configured member may speak")
	tr.close_work(store, result["work_id"], actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="live-context|labelled open"):
		tr.post_discussion(store, result["discussion"], author_team="lang",
		                   author="ada", body="after the end")
	# The discussion stays READABLE...
	view = pj.thread(store, result["discussion"], viewer_team="lang",
	                 viewer_member="ada")
	assert len(view["messages"]) == 2
	# ...and labelling open follow-up work makes it postable again.
	follow = tr.create_work(store, team="lang", kind="bug",
	                        title="follow-up", origin="external-report",
	                        author="ada", body="continuation",
	                        follow_up_of=result["work_id"])
	tr.label_discussion(store, result["discussion"], follow["work_id"],
	                    actor_team="lang", actor="ada")
	tr.post_discussion(store, result["discussion"], author_team="lang",
	                   author="ada", body="continued under new work")


def test_the_last_open_label_closing_mid_post_refuses_in_lock(world):
	store = world
	result = _create(store)
	other = bw.Authority(store.path)
	other.clock = store.clock
	_interleave(store, lambda: tr.close_work(
		other, result["work_id"], actor_team="lang", actor="ada",
		rationale="closed mid-post", outcome="satisfying"))
	with pytest.raises(bw.WorkError, match="live-context|labelled open"):
		tr.post_discussion(store, result["discussion"], author_team="lang",
		                   author="ada", body="racing the close")
	count = store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages WHERE discussion=?",
		(result["discussion"],)).fetchone()["n"]
	assert count == 1, "the losing post landed on dead context"
	other.close()


# -- seen, New, and the overlap identity --------------------------------------

def test_new_decomposes_with_visible_overlap(world):
	"""One discussion labelled to two siblings under one parent: each
	child's count is truthful, the parent's total counts each message
	once, and overlap says exactly how much the raw sum overstated."""
	store = world
	parent = _create(store)["work_id"]
	left = tr.create_work(store, team="lang", kind="bug", title="left",
	                      origin="decomposition", author="ada", body="l",
	                      parent=parent)
	right = tr.create_work(store, team="lang", kind="bug", title="right",
	                       origin="decomposition", author="ada", body="r",
	                       parent=parent)
	shared = tr.create_discussion(store, actor_team="lang", actor="ada",
	                              body="spans both legs",
	                              labels=[left["work_id"],
	                                      right["work_id"]])
	tr.post_discussion(store, shared["discussion"], author_team="lang",
	                   author="ada", body="second shared message")

	breakdown = pj.new_count(store, parent, viewer_team="lang",
	                         viewer_member="grace")
	left_entry = next(entry for entry in breakdown["children"]
	                  if entry["id"] == left["work_id"])
	right_entry = next(entry for entry in breakdown["children"]
	                   if entry["id"] == right["work_id"])
	# Each child truthfully counts its 2 shared + 1 own creation message.
	assert left_entry["new"] == 3 and right_entry["new"] == 3
	assert breakdown["overlap"] == 2, \
		"the shared discussion's dedup is not visible"
	assert breakdown["total"] == breakdown["own"] + \
		left_entry["new"] + right_entry["new"] - breakdown["overlap"]
	# Reading the shared discussion once clears it EVERYWHERE.
	tr.seen_discussion(store, shared["discussion"], team="lang",
	                   member="grace", up_to_seq=store.last_seq())
	after = pj.new_count(store, parent, viewer_team="lang",
	                     viewer_member="grace")
	assert after["overlap"] == 0
	assert after["total"] == after["own"] + \
		sum(entry["new"] for entry in after["children"])


def test_cursors_are_per_member_and_the_bridge_covers_all_labels(world):
	store = world
	result = _create(store)
	second = _create(store)
	tr.label_discussion(store, result["discussion"], second["work_id"],
	                    actor_team="lang", actor="ada")
	tr.post_discussion(store, result["discussion"], author_team="lang",
	                   author="ada", body="more")
	assert pj.new_count(store, second["work_id"], viewer_team="lang",
	                    viewer_member="grace")["total"] > 0
	# The Work-addressed bridge advances every labelled discussion...
	fx.mark_all_seen(store, second["work_id"], team="lang", member="grace",
	             up_to_seq=store.last_seq())
	assert pj.new_count(store, second["work_id"], viewer_team="lang",
	                    viewer_member="grace")["total"] == 0
	assert pj.new_count(store, result["work_id"], viewer_team="lang",
	                    viewer_member="grace")["total"] == 0, \
		"the bridge left a labelled discussion uncleared"
	# ...and only THAT member's cursor moved.
	assert pj.new_count(store, result["work_id"], viewer_team="lang",
	                    viewer_member="ada")["total"] > 0


# -- participation and surfaces -----------------------------------------------

def test_participation_is_monotonic_and_surfaced(world):
	store = world
	result = _create(store)
	tr.post_discussion(store, result["discussion"], author_team="push",
	                   author="sl", body="joining by speaking")
	view = pj.thread(store, result["discussion"], viewer_team="push",
	                 viewer_member="sl")
	assert view["participants"] == ["lang", "push"]
	surface = pj.discussions_for(store, viewer_team="push",
	                             viewer_member="sl")
	assert [row["id"] for row in surface["rows"]] == \
		[result["discussion"]]
	assert surface["rows"][0]["new"] > 0
	assert surface["snapshot_seq"] == store.last_seq()


# -- races, crash, restart, purity --------------------------------------------

def test_label_races_serialize_exactly_once(world):
	store = world
	first = _create(store)
	second = _create(store)
	other = bw.Authority(store.path)
	other.clock = store.clock
	_interleave(store, lambda: tr.label_discussion(
		other, first["discussion"], second["work_id"],
		actor_team="lang", actor="ada"))
	with pytest.raises(bw.WorkError, match="already carries"):
		tr.label_discussion(store, first["discussion"],
		                    second["work_id"], actor_team="lang",
		                    actor="grace")
	_interleave(store, lambda: tr.unlabel_discussion(
		other, first["discussion"], second["work_id"],
		actor_team="lang", actor="ada"))
	with pytest.raises(bw.WorkError, match="does not carry"):
		tr.unlabel_discussion(store, first["discussion"],
		                      second["work_id"], actor_team="lang",
		                      actor="grace")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM discussion_labels WHERE discussion=?",
		(first["discussion"],)).fetchone()["n"] == 1
	other.close()


def test_create_discussion_rolls_back_whole_at_every_boundary(world):
	store = world
	anchor = _create(store)["work_id"]
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	baseline = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	baseline_events = store.events()

	statement = {"n": 0, "limit": 0}
	real_conn = store.conn

	class ExplodingConn:
		def execute(self, sql, *args):
			if sql.strip().upper().startswith(
					("UPDATE", "INSERT", "DELETE")):
				statement["n"] += 1
				if statement["n"] > statement["limit"]:
					raise Exception("injected fault")
			return real_conn.execute(sql, *args)

		def __getattr__(self, name):
			return getattr(real_conn, name)

	boundary = 0
	while True:
		boundary += 1
		statement["n"], statement["limit"] = 0, boundary
		store.conn = ExplodingConn()
		try:
			tr.create_discussion(store, actor_team="lang", actor="ada",
			                     body="atomic", labels=[anchor])
			store.conn = real_conn
			break
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			now = hashlib.sha256(
				open(store.path, "rb").read()).hexdigest()
			assert now == baseline, \
				f"fault at write {boundary} left half a discussion"
			assert store.events() == baseline_events
		assert boundary < 40, "the creation never completed"


def test_restart_and_purity(world):
	store = world
	result = _create(store)
	tr.post_discussion(store, result["discussion"], author_team="lang",
	                   author="ada", body="two")
	tr.seen_discussion(store, result["discussion"], team="lang",
	                   member="ada", up_to_seq=store.last_seq())
	before = pj.thread(store, result["discussion"], viewer_team="lang",
	                   viewer_member="ada")
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	after = pj.thread(fresh, result["discussion"], viewer_team="lang",
	                  viewer_member="ada")
	assert after == before, "restart lost discussion state"
	# Purity: the new read surfaces write no byte.
	fresh.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	digest = hashlib.sha256(open(fresh.path, "rb").read()).hexdigest()
	pj.thread(fresh, result["discussion"], viewer_team="lang",
	          viewer_member="grace")
	pj.discussions_for(fresh, viewer_team="lang", viewer_member="grace")
	pj.new_count(fresh, result["work_id"], viewer_team="push",
	             viewer_member="sl")
	fresh.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert hashlib.sha256(
		open(fresh.path, "rb").read()).hexdigest() == digest, \
		"a discussion read wrote to the authority"
	fresh.close()

# -- R63: pagination and ordering are deterministic contracts -----------------

def test_pagination_is_a_bounded_positive_contract(world):
	store = world
	first = _create(store)
	d, w = first["discussion"], first["work_id"]
	for kwargs in ({"after": -1}, {"limit": 0},
	               {"limit": pj.MAX_PAGE + 1}):
		for read in (
				lambda: pj.thread(store, d, viewer_team="lang",
				                  viewer_member="ada", **kwargs),
				lambda: pj.discussions_for(store, viewer_team="lang",
				                           viewer_member="ada", **kwargs),
				lambda: pj.work_discussions(store, w, viewer_team="lang",
				                            viewer_member="ada",
				                            **kwargs)):
			with pytest.raises(bw.WorkError,
			                   match="pagination cursor|page limit"):
				read()


def test_shared_sequence_ties_order_by_identity(tmp_path):
	"""R63: several labels land at ONE sequence, and one `+` expansion
	joins several teams at ONE sequence — the projections still hold a
	total order: (added_seq, identity)."""
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["bug"]}}
	with fx.open_instance(str(tmp_path), spec) as store:
		w1 = _create(store)["work_id"]
		w2 = _create(store)["work_id"]
		# Both labels share the creation sequence, given in REVERSE
		# identity order.
		tied = tr.create_discussion(store, actor_team="lang", actor="ada",
		                            body="tie", labels=[w2, w1])
		view = pj.thread(store, tied["discussion"], viewer_team="lang",
		                 viewer_member="ada")
		assert [entry["work"] for entry in view["labels"]] == \
			sorted([w1, w2]), "a same-sequence label tie has no total order"
		# push and web join at the SAME expansion sequence.
		born = _create(store)
		fx.post(store, born["work_id"], author_team="lang",
		                author="ada", body="both join at one seq",
		                include="*.bug")
		view = pj.thread(store, born["discussion"], viewer_team="lang",
		                 viewer_member="ada")
		assert view["participants"] == ["lang", "push", "web"], \
			"a same-sequence participant tie has no total order"


def test_paged_joins_have_no_skips_or_repeats(world):
	store = world
	first = _create(store)
	w, born = first["work_id"], first["discussion"]
	expected = [born] + [
		tr.create_discussion(store, actor_team="lang", actor="ada",
		                     body=f"leg {i}", labels=[w])["discussion"]
		for i in range(6)]

	# Work -> discussions, pages of 3: full, full, partial-with-None.
	collected, after, pages = [], 0, 0
	while True:
		page = pj.work_discussions(store, w, viewer_team="lang",
		                           viewer_member="ada", after=after,
		                           limit=3)
		collected += [row["id"] for row in page["rows"]]
		pages += 1
		if page["next_after"] is None:
			break
		after = page["next_after"]
	assert collected == expected and pages == 3, \
		"the Work->discussion join skipped or repeated across pages"

	# The member surface, pages of 2 — same rows, same order, no dup.
	collected, after = [], 0
	while True:
		page = pj.discussions_for(store, viewer_team="lang",
		                          viewer_member="grace", after=after,
		                          limit=2)
		collected += [row["id"] for row in page["rows"]]
		if page["next_after"] is None:
			break
		after = page["next_after"]
	assert collected == expected, \
		"the participating-discussion join skipped or repeated"

	# The message window, pages of 2 over 5 messages.
	for i in range(4):
		tr.post_discussion(store, born, author_team="lang", author="ada",
		                   body=f"b{i}")
	seqs, after = [], 0
	while True:
		page = pj.thread(store, born, viewer_team="lang",
		                 viewer_member="ada", after=after, limit=2)
		seqs += [message["seq"] for message in page["messages"]]
		if page["next_after"] is None:
			break
		after = page["next_after"]
	assert seqs == sorted(set(seqs)) and len(seqs) == 5, \
		"the message window skipped or repeated across pages"


# -- R64: New is one snapshot, token and identity included --------------------

def test_new_names_one_state_under_an_interleaved_writer(world, monkeypatch):
	"""A message committing MID-decomposition is invisible to every leg:
	own, each child, overlap, total and the token all describe the
	snapshot, and the very next read sees the message everywhere."""
	store = world
	parent = _create(store)["work_id"]
	left = tr.create_work(store, team="lang", kind="bug", title="left",
	                      origin="decomposition", author="ada", body="l",
	                      parent=parent)["work_id"]
	right = tr.create_work(store, team="lang", kind="bug", title="right",
	                       origin="decomposition", author="ada", body="r",
	                       parent=parent)["work_id"]
	shared = tr.create_discussion(store, actor_team="lang", actor="ada",
	                              body="spans both legs",
	                              labels=[left, right])["discussion"]
	other = bw.Authority(store.path)
	other.clock = store.clock
	pinned = store.last_seq()
	real = pj._unseen_set
	fired = {"done": False}

	def racing(snap_store, works, team, member):
		if not fired["done"]:
			fired["done"] = True
			tr.post_discussion(other, shared, author_team="lang",
			                   author="ada", body="landed mid-read")
		return real(snap_store, works, team, member)

	monkeypatch.setattr(pj, "_unseen_set", racing)
	view = pj.new_count(store, parent, viewer_team="lang",
	                    viewer_member="grace")
	assert fired["done"] and store.last_seq() == pinned + 1
	assert view["id"] == parent, "the Work identity left the projection"
	assert view["snapshot_seq"] == pinned, \
		"the token named a later commit than the counts"
	assert view["own"] == 1
	assert [entry["new"] for entry in view["children"]] == [2, 2]
	assert view["overlap"] == 1
	assert view["total"] == view["own"] + \
		sum(entry["new"] for entry in view["children"]) - \
		view["overlap"] == 4, "the decomposition tore across the write"
	after = pj.new_count(store, parent, viewer_team="lang",
	                     viewer_member="grace")
	assert after["snapshot_seq"] == pinned + 1
	assert after["total"] == view["total"] + 1, \
		"the committed message never became visible"
	other.close()


# -- R65: config-generation races against the new mutations -------------------

@pytest.fixture
def raced(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def _remove_grace(config_path):
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")


@pytest.mark.parametrize("act", ["discuss", "label", "unlabel", "say",
                                 "mark-seen"])
def test_a_mid_flight_removal_refuses_each_new_mutation_in_lock(raced, act):
	"""Removal-first order, raced: the generation-2 acceptance commits
	between the optimistic membership check and the lock — the committing
	transaction revalidates and the removed member's act refuses whole."""
	store, config_path = raced
	first = _create(store)
	w1, d1 = first["work_id"], first["discussion"]
	w2 = _create(store)["work_id"]
	if act == "unlabel":
		tr.label_discussion(store, d1, w2, actor_team="lang", actor="ada")
	acts = {
		"discuss": lambda: tr.create_discussion(
			store, actor_team="lang", actor="grace", body="x",
			labels=[w1]),
		"label": lambda: tr.label_discussion(
			store, d1, w2, actor_team="lang", actor="grace"),
		"unlabel": lambda: tr.unlabel_discussion(
			store, d1, w2, actor_team="lang", actor="grace"),
		"say": lambda: tr.post_discussion(
			store, d1, author_team="lang", author="grace", body="x"),
		"mark-seen": lambda: tr.seen_discussion(
			store, d1, team="lang", member="grace",
			up_to_seq=store.last_seq()),
	}
	kinds = {"discuss": "create_discussion", "label": "label",
	         "unlabel": "unlabel", "say": "post_message",
	         "mark-seen": "mark_seen"}
	before = [event for event in store.events()
	          if event["kind"] == kinds[act]]
	_interleave(store, lambda: _remove_grace(config_path))
	with pytest.raises(bw.WorkError,
	                   match="currently accepted configuration"):
		acts[act]()
	assert [event for event in store.events()
	        if event["kind"] == kinds[act]] == before, \
		"a removed member's act still committed"


def test_the_act_first_then_removal_both_commit(raced):
	"""The other order: grace's message commits under generation 1, the
	non-stranding removal then accepts cleanly, history stands, and the
	next act by the removed identity refuses at the door."""
	store, config_path = raced
	first = _create(store)
	d1 = first["discussion"]
	spoken = tr.post_discussion(store, d1, author_team="lang",
	                            author="grace", body="before removal")
	_remove_grace(config_path)
	assert store.meta()["accepted_generation"] == "2"
	kept = [event for event in store.events()
	        if event["kind"] == "post_message" and
	        event["actor"] == "lang.grace"]
	assert [event["seq"] for event in kept] == [spoken["seq"]], \
		"the removal rewrote committed history"
	with pytest.raises(bw.WorkError, match="not a registered member"):
		tr.post_discussion(store, d1, author_team="lang", author="grace",
		                   body="after removal")


def test_label_audits_the_committing_work_status(world):
	"""R65: a close landing between the pre-lock read and the label
	transaction — the audit records the COMMITTING status, not the
	optimistic diagnostic."""
	store = world
	first = _create(store)
	d1 = first["discussion"]
	w2 = _create(store)["work_id"]
	_interleave(store, lambda: tr.close_work(
		store, w2, actor_team="lang", actor="ada",
		rationale="done first", outcome="satisfying"))
	result = tr.label_discussion(store, d1, w2, actor_team="lang",
	                             actor="ada")
	event = next(event for event in store.events()
	             if event["seq"] == result["seq"])
	assert event["payload"]["work_status"] == "closed", \
		"the label audited a pre-lock status the commit no longer had"


def test_detail_preview_reports_truncation_explicitly(world):
	"""R67: the bounded preview shares the relation order and NAMES its
	truncation — count, flag, and a continuation cursor that hands off to
	`work_discussions` without a gap or a repeat."""
	store = world
	w = _create(store)["work_id"]
	for i in range(52):
		tr.create_discussion(store, actor_team="lang", actor="ada",
		                     body=f"d{i}", labels=[w])
	view = pj.detail(store, w, viewer_team="lang", viewer_member="ada")
	assert view["discussion_count"] == 53
	assert len(view["discussions"]) == 50
	assert view["discussions_truncated"] is True, \
		"a 51st discussion exists and the preview never said so"
	assert view["discussions_next_after"] == \
		view["discussions"][-1]["added_seq"]
	rest = pj.work_discussions(store, w, viewer_team="lang",
	                           viewer_member="ada",
	                           after=view["discussions_next_after"],
	                           limit=10)
	assert len(rest["rows"]) == 3 and rest["next_after"] is None
	assert not {row["id"] for row in rest["rows"]} & \
		{entry["id"] for entry in view["discussions"]}, \
		"the preview handoff repeated a discussion"
	small = _create(store)["work_id"]
	view = pj.detail(store, small, viewer_team="lang",
	                 viewer_member="ada")
	assert view["discussion_count"] == 1
	assert view["discussions_truncated"] is False
	assert view["discussions_next_after"] is None
