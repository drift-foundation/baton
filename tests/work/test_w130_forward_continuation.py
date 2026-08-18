"""W130 (finding-forward-message-page-continuation): a full forward page
is not proof of another page.

Found while reviewing W76: the reverse path had gained a proof row, and
the exact-limit regression there exposed the older forward asymmetry
underneath it. `thread(after=..., limit=N)` set `next_after` solely
because N rows came back, so a final exact-limit page advertised a
cursor whose canonical follow-up was empty.

The cursor is a promise a client acts on. These tests walk it.
"""

from __future__ import annotations

import json as _json
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


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store}
	store.close()


def conversation(world, count):
	"""A Thread with exactly `count` messages, born message included."""
	store = world["store"]
	born = tr.create_work(store, team="lang", kind="bug", title="paged",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="message 00")
	seqs = [born["seq"]]
	for index in range(1, count):
		seqs.append(tr.post_thread(
			store, born["thread"], author_team="lang", author="ada",
			body=f"message {index:02d}")["seq"])
	return born["thread"], seqs


def page(world, thread, **kw):
	return pj.thread(world["store"], thread, viewer_team="lang",
	                 viewer_member="ada", **kw)


def test_an_exact_limit_final_page_advertises_nothing(world):
	"""The reported defect, reproduced at its boundary."""
	thread, seqs = conversation(world, 5)
	first = page(world, thread, after=0, limit=5)
	assert [m["seq"] for m in first["messages"]] == seqs
	assert first["next_after"] is None, \
		"an exact-limit final page advertised an empty continuation"


def test_fewer_than_the_limit_advertises_nothing(world):
	thread, seqs = conversation(world, 3)
	only = page(world, thread, after=0, limit=5)
	assert [m["seq"] for m in only["messages"]] == seqs
	assert only["next_after"] is None


def test_one_more_than_the_limit_advertises_the_next_page(world):
	thread, seqs = conversation(world, 6)
	first = page(world, thread, after=0, limit=5)
	assert [m["seq"] for m in first["messages"]] == seqs[:5]
	assert first["next_after"] == seqs[4]
	following = page(world, thread, after=first["next_after"], limit=5)
	assert [m["seq"] for m in following["messages"]] == seqs[5:]
	assert following["next_after"] is None, \
		"the last page advertised another"


@pytest.mark.parametrize("count,limit", [
	(9, 3),      # exact multiple — the shape that hid the defect
	(10, 3),     # ragged tail
	(1, 1),      # single message, single-row pages
	(4, 1),      # exact multiple at limit 1
	(7, 20),     # one short page
])
def test_every_advertised_cursor_opens_a_non_empty_page(world, count,
                                                        limit):
	"""Walk the promise. Complete, ordered, duplicate-free, and never a
	page that opens empty."""
	thread, seqs = conversation(world, count)
	visited, cursor, pages = [], 0, 0
	while True:
		current = page(world, thread, after=cursor, limit=limit)
		assert current["messages"], \
			f"an advertised cursor opened an EMPTY page " \
			f"(count={count}, limit={limit}, after={cursor})"
		assert len(current["messages"]) <= limit
		visited.extend(m["seq"] for m in current["messages"])
		pages += 1
		assert pages <= count + 2, "the walk did not terminate"
		if current["next_after"] is None:
			break
		cursor = current["next_after"]
	assert visited == seqs, \
		f"traversal lost, repeated or reordered messages: {visited}"


def test_the_cursor_is_exclusive_and_retry_stable(world):
	"""`after` semantics are unchanged: the named message is NOT
	repeated, and re-reading the same cursor on an unchanged snapshot
	returns the identical page."""
	thread, seqs = conversation(world, 8)
	first = page(world, thread, after=0, limit=4)
	cursor = first["next_after"]
	assert cursor == seqs[3]
	second = page(world, thread, after=cursor, limit=4)
	assert cursor not in [m["seq"] for m in second["messages"]], \
		"the exclusive cursor repeated its own message"
	again = page(world, thread, after=cursor, limit=4)
	assert [m["seq"] for m in again["messages"]] == \
		[m["seq"] for m in second["messages"]]
	assert again["next_after"] == second["next_after"]


def test_the_proof_row_never_reaches_the_payload(world):
	"""Reading limit+1 is an implementation detail: the page is exactly
	`limit` long, ascending, and carries its own references and personal
	new-state."""
	thread, seqs = conversation(world, 10)
	current = page(world, thread, after=0, limit=4)
	got = [m["seq"] for m in current["messages"]]
	assert got == seqs[:4]
	assert got == sorted(got)
	for message in current["messages"]:
		assert "references" in message and "new" in message


def test_the_reverse_direction_is_unchanged(world):
	"""W130 touches the forward query only."""
	thread, seqs = conversation(world, 5)
	newest = page(world, thread, newest=True, limit=5)
	assert [m["seq"] for m in newest["messages"]] == seqs
	assert newest["next_before"] is None
	assert newest["next_after"] is None
	bigger = conversation(world, 7)
	page_two = page(world, bigger[0], newest=True, limit=3)
	assert page_two["next_before"] == bigger[1][4]


def test_unrelated_thread_facts_are_untouched(world):
	thread, seqs = conversation(world, 5)
	current = page(world, thread, after=0, limit=5)
	assert current["last_seq"] == seqs[-1]
	assert current["new"] == len(seqs), current["new"]
	assert current["snapshot_seq"] >= seqs[-1]
	assert current["local_id"].startswith("T")
