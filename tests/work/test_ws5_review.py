"""Reviewer regressions for the accepted WS-5 operation-identity contract."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug", title="w",
	                      origin="external-report", author="ada",
	                      body="born speaking")
	yield store, config_path, born
	store.close()


def test_operation_id_refuses_del_as_a_control_character(world):
	"""R82: the accepted grammar says NO control characters, not merely
	ASCII C0. DEL is Unicode category Cc and is neither whitespace nor < 32."""
	store, _config, born = world
	before = store.events()
	with pytest.raises(bw.WorkError, match="control"):
		tr.post_thread(store, born["thread"], author_team="lang",
		                   author="ada", body="must not commit",
		                   op_id="bad\x7fid")
	assert store.events() == before
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM operations").fetchone()["n"] == 0


def test_fingerprint_uses_validated_normalized_input(world):
	"""R83: accepted shorthand and its normalized typed form are the same
	semantic request. The fingerprint must be made after normalization, as the
	design promises, rather than over the caller's pre-validation container."""
	store, _config, born = world
	first = tr.create_thread(
		store, actor_team="lang", actor="ada", body="one meaning",
		labels=born["work_id"], subject="trial subject",
		op_id="normalized-label")
	retry = tr.create_thread(
		store, actor_team="lang", actor="ada", body="one meaning",
		labels=[born["work_id"]], subject="trial subject",
		op_id="normalized-label")
	assert retry["operation"]["state"] == "replayed"
	assert retry["seq"] == first["seq"]


def test_identity_removal_cannot_race_between_gate_and_replay(
		world, monkeypatch):
	"""R84: current accepted identity is the replay boundary. Validation
	and lookup must share one serializable observation; otherwise removal may
	commit between their separate reads and the removed identity still learns
	the stored result."""
	store, config_path, born = world
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="grace", body="before removal",
	                   op_id="removed-race")
	document = json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["grace"]
	with open(config_path, "w") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)

	original = store._op_replay
	fired = {"done": False}

	def remove_then_lookup(conn, participant, op_id, fingerprint):
		if not fired["done"]:
			fired["done"] = True
			lc.accept_config(config_path, actor="lang.ada")
		return original(conn, participant, op_id, fingerprint)

	monkeypatch.setattr(store, "_op_replay", remove_then_lookup)
	with pytest.raises(bw.WorkError, match="not a registered member"):
		tr.post_thread(store, born["thread"], author_team="lang",
		                   author="grace", body="before removal",
		                   op_id="removed-race")


def test_removed_identity_gate_precedes_conflicting_replay_lookup(
		world, monkeypatch):
	"""R84: the current-identity gate is also the information boundary.
	A removed participant must not learn whether its old operation id exists or
	whether a new request conflicts with the stored fingerprint."""
	store, config_path, born = world
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="grace", body="original request",
	                   op_id="removed-conflict")
	document = json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["grace"]
	with open(config_path, "w") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	original = store._op_replay
	fired = {"done": False}

	def remove_then_lookup(conn, participant, op_id, fingerprint):
		if not fired["done"]:
			fired["done"] = True
			lc.accept_config(config_path, actor="lang.ada")
		return original(conn, participant, op_id, fingerprint)

	monkeypatch.setattr(store, "_op_replay", remove_then_lookup)
	with pytest.raises(bw.WorkError, match="not a registered member"):
		tr.post_thread(store, born["thread"], author_team="lang",
		                   author="grace", body="different request",
		                   op_id="removed-conflict")
