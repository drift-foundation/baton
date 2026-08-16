"""W31: subject-bearing Threads — Work -> Threads -> Messages.

The canonical entity is the Thread: born with a REQUIRED concise subject,
labelled to one or more Work items, carrying Messages that never repeat the
subject. No Discussion vocabulary remains anywhere on the public surface.
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
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	_config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield store
	store.close()


def _work(store, title="tracked activity"):
	return tr.create_work(store, team="lang", kind="bug", title=title,
	                      origin="external-report", author="ada",
	                      body="seed")


def test_a_thread_requires_a_concise_single_line_subject(world):
	store = world
	work = _work(store)["work_id"]
	before = store.events()
	for bad, needle in ((None, "non-empty subject"),
	                    ("", "non-empty subject"),
	                    ("   ", "non-empty subject"),
	                    ("two\nlines", "single line"),
	                    ("x" * 81, "80 UTF-8 bytes")):
		with pytest.raises(bw.WorkError, match=needle):
			tr.create_thread(store, actor_team="lang", actor="ada",
			                 body="body", labels=[work], subject=bad)
	assert store.events() == before, "a refused subject left residue"
	made = tr.create_thread(store, actor_team="lang", actor="ada",
	                        body="body", labels=[work],
	                        subject="  concise subject  ")
	view = pj.thread(store, made["thread"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["subject"] == "concise subject", \
		"the stored subject is not the normalized one"


def test_the_born_thread_subject_is_the_work_title(world):
	store = world
	born = _work(store, title="checkout fails at boot")
	view = pj.thread(store, born["thread"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["subject"] == "checkout fails at boot"
	assert born["thread"].split("-")[-1].startswith("T"), \
		"thread ids carry the T marker"


def test_one_thread_many_works_and_many_threads_one_work(world):
	"""Several Threads label one Work; one Thread labels several Work
	items — each keeps its ONE subject, and the Work's thread set lists
	subjects with stable ordinals."""
	store = world
	first = _work(store, title="first work")
	second = _work(store, title="second work")
	shared = tr.create_thread(
		store, actor_team="lang", actor="ada", body="spans both",
		labels=[first["work_id"], second["work_id"]],
		subject="the shared conversation")
	extra = tr.create_thread(
		store, actor_team="lang", actor="ada", body="only the first",
		labels=[first["work_id"]], subject="a second conversation")
	rows = pj.work_threads(store, first["work_id"], viewer_team="lang",
	                       viewer_member="ada")["rows"]
	assert [(row["ordinal"], row["subject"]) for row in rows] == [
		(1, "first work"),
		(2, "the shared conversation"),
		(3, "a second conversation")]
	other = pj.work_threads(store, second["work_id"],
	                        viewer_team="lang",
	                        viewer_member="ada")["rows"]
	assert [(row["ordinal"], row["subject"]) for row in other] == [
		(1, "second work"),
		(2, "the shared conversation")]
	assert pj.thread(store, shared["thread"], viewer_team="lang",
	                 viewer_member="ada")["subject"] == \
		"the shared conversation"
	assert extra["thread"] != shared["thread"]


def test_replies_never_repeat_or_replace_the_subject(world):
	store = world
	born = _work(store)
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="a plain reply")
	view = pj.thread(store, born["thread"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["subject"] == "tracked activity"
	assert all("subject" not in message for message in
	           view["messages"]), \
		"messages must not carry their own subject"


def test_the_subject_participates_in_the_effectively_once_fingerprint(world):
	store = world
	work = _work(store)["work_id"]
	first = tr.create_thread(store, actor_team="lang", actor="ada",
	                         body="body", labels=[work],
	                         subject="first meaning", op_id="thread-1")
	replay = tr.create_thread(store, actor_team="lang", actor="ada",
	                          body="body", labels=[work],
	                          subject="first meaning", op_id="thread-1")
	assert replay["thread"] == first["thread"]
	assert replay["seq"] == first["seq"]
	assert replay["operation"]["state"] == "replayed"
	before = store.events()
	with pytest.raises(bw.WorkError, match="different request"):
		tr.create_thread(store, actor_team="lang", actor="ada",
		                 body="body", labels=[work],
		                 subject="different meaning", op_id="thread-1")
	assert store.events() == before, \
		"a changed subject replayed or left authority residue"


@pytest.mark.parametrize("title", ["two\nlines", "x" * 81])
def test_the_born_thread_obeys_the_same_subject_contract(world, title):
	"""W31 rev3 (R2, approved by Slawomir): Work titles and Thread
	subjects share ONE normalized contract, so a title the subject
	validator refuses REFUSES the creation whole — the authority can
	never contain a Thread subject its own validator rejects."""
	store = world
	before = store.events()
	with pytest.raises(bw.WorkError,
	                   match="single line|80 UTF-8 bytes"):
		_work(store, title=title)
	assert store.events() == before, \
		"a refused title left authority residue"
	# The invariant the pre-ruling regression asserted, preserved: every
	# stored born subject passes the one public validator.
	born = _work(store, title="  a valid concise title  ")
	view = pj.thread(store, born["thread"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["subject"] == "a valid concise title"
	assert tr.validate_subject(view["subject"]) == view["subject"]
