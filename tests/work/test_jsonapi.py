"""A6: the versioned JSON surface and `baton-work` CLI.

Driven in-process through `cli.main(argv)` (same code path as the installed
entry point) with capsys, against THE fixture. The two named acceptance
properties get their own tests: sequence-cursor pagination joins cleanly
across a same-second burst, and the LANG-42 fan-in is reachable by typed
traversal alone.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

from baton_work import cli, jsonapi                           # noqa: E402
import fixtures                                               # noqa: E402


@pytest.fixture(scope="module")
def world(tmp_path_factory):
	directory = tmp_path_factory.mktemp("fixture")
	cast = fixtures.build(str(directory / "work.sqlite3"))
	return cast["config_path"], cast


def _run(capsys, path, *argv, viewer=None, expect_ok=True):
	args = ["--config", path]
	if viewer:
		args += ["--participant", viewer]
	code = cli.main(args + list(argv))
	captured = capsys.readouterr()
	if expect_ok:
		assert code == 0, captured.err
		return json.loads(captured.out)
	assert code == 1, captured.out
	return json.loads(captured.err)


# -- the envelope ------------------------------------------------------------

def test_every_response_carries_the_full_envelope(world, capsys):
	path, cast = world
	out = _run(capsys, path, "home", viewer="lang.ada")
	assert set(out) == {"projection_version", "protocol_version",
	                    "authority_uuid", "snapshot_seq", "participant",
	                    "result"}
	assert out["projection_version"] == jsonapi.PROJECTION_VERSION
	assert out["protocol_version"] == 11
	assert out["participant"] == "lang.ada"
	assert out["snapshot_seq"] == cast["last_seq"]
	assert [row["id"] for row in out["result"]["rows"]] == [cast["lang42"]]
	assert out["result"]["summary"]["team"] == "lang", \
		"the top-level view no longer carries its one-snapshot summary"


def test_an_incompatible_projection_version_fails_clearly(world, capsys):
	path, _ = world
	error = _run(capsys, path, "--expect-projection", "5.0", "home",
	             viewer="lang.ada", expect_ok=False)
	assert "not compatible" in error["error"], \
		"the honest-breaking 5.0 still satisfied a 4.x demand"
	ok = _run(capsys, path, "--expect-projection", "11.0", "home",
	          viewer="lang.ada")
	assert ok["result"], "a compatible minor was refused"


def test_errors_are_json_with_exit_one(world, capsys):
	path, _ = world
	error = _run(capsys, path, "detail", "work=nope-W1", viewer="lang.ada",
	             expect_ok=False)
	# W4: a malformed selector refuses BY NAME through the one strict
	# resolver before any lookup runs.
	assert "'nope-W1' is not a Work selector" in error["error"]


# -- typed traversal ---------------------------------------------------------

def test_the_fan_in_is_reachable_by_relation_alone(world, capsys):
	"""From a consumer's own Work to every co-consumer, following typed
	edges only — never search: pushcoin -> blocked_by -> LANG-42 -> blocks."""
	path, cast = world
	mine = _run(capsys, path, "links", f"work={cast["pushcoin"]}",
	            viewer="push.sl")["result"]
	assert [edge["id"] for edge in mine["blocked_by"]] == [cast["lang42"]]
	provider = _run(capsys, path, "links",
	                f"work={mine['blocked_by'][0]['id']}",
	                viewer="push.sl")["result"]
	co_consumers = [edge["id"] for edge in provider["blocks"]]
	assert co_consumers == [cast["pushcoin"], cast["web"], cast["mdb"]]


# -- pagination on the sequence ----------------------------------------------

def test_pagination_joins_cleanly_across_a_same_second_burst(tmp_path, capsys):
	"""The protocol-10 defect, demonstrated fixed: publish a burst well
	inside one second, page with a small limit, and the pages join with no
	skip and no repeat — because the cursor is the sequence, not a
	timestamp."""
	import fixtures as fx
	path, _db = fx.build_instance(str(tmp_path))
	created = _run(capsys, path, "create", "team=lang",
	               "kind=bug", "title=burst", "origin=self-initiated", "classification=suspected-defect",
	               "body=first", viewer="lang.ada")["result"]
	work, thread_id = created["work_id"], created["thread"]
	for index in range(40):
		_run(capsys, path, "say", f"thread={thread_id}", f"body=burst {index}",
		     viewer="lang.ada")

	full = _run(capsys, path, "thread", f"thread={thread_id}",
	            viewer="lang.ada")["result"]["messages"]
	assert len(full) == 41
	# R63: the continuation token is EXPLICIT — pages join on next_after
	# with no skip and no repeat, because the cursor is the sequence.
	paged, after = [], 0
	for _page in range(50):
		result = _run(capsys, path, "thread", f"thread={thread_id}",
		              f"after={after}", "limit=7",
		              viewer="lang.ada")["result"]
		paged.extend(result["messages"])
		if result["next_after"] is None:
			break
		after = result["next_after"]
	assert [m["seq"] for m in paged] == [m["seq"] for m in full], \
		"pages skipped or repeated rows"


# -- mutations return the committed record -----------------------------------

def test_mutating_verbs_return_the_committed_state(tmp_path, capsys):
	import fixtures as fx
	path, _db = fx.build_instance(str(tmp_path))
	created = _run(capsys, path, "create", "team=lang",
	               "kind=rsrch", "title=t", "origin=external-report", "classification=suspected-defect",
	               "body=b", viewer="lang.ada")["result"]
	assert created["work_id"].endswith(f"-W{created['seq']}")

	passed = _run(capsys, path, "pass", f"work={created["work_id"]}",
	              "to=lang.impl", "set-next=lang.rev", "comment=go",
	              viewer="lang.ada")["result"]
	assert passed["kind"] == "pass"
	returned = _run(capsys, path, "pass", f"work={created["work_id"]}",
	                "to=lang.rev", "comment=done",
	                viewer="lang.ada")["result"]
	assert returned["kind"] == "return", \
		"the CLI lost the audited return distinction"

	closed = _run(capsys, path, "close", f"work={created["work_id"]}",
	              "rationale=verified", "outcome=satisfying",
	              viewer="lang.ada")["result"]
	assert closed["kind"] == "close_work"
	detail = _run(capsys, path, "detail", f"work={created["work_id"]}",
	              viewer="lang.ada")["result"]
	assert detail["status"] == "closed"
	assert detail["available_transitions"] == [], \
		"closure is immutable (WS-2); closed work offers no transition"


def test_a_mutation_without_a_viewer_is_refused(world, capsys):
	path, cast = world
	error = _run(capsys, path, "say", "thread=some-thread", "body=anon",
	             expect_ok=False)
	assert "needs --participant" in error["error"]
