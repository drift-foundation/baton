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
	path = str(tmp_path_factory.mktemp("fixture") / "work.sqlite3")
	cast = fixtures.build(path)
	return path, cast


def _run(capsys, path, *argv, viewer=None, expect_ok=True):
	args = ["--authority", path]
	if viewer:
		args += ["--viewer", viewer]
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
	                    "authority_uuid", "snapshot_seq", "viewer", "result"}
	assert out["projection_version"] == jsonapi.PROJECTION_VERSION
	assert out["protocol_version"] == 11
	assert out["viewer"] == "lang.ada"
	assert out["snapshot_seq"] == cast["last_seq"]
	assert [row["id"] for row in out["result"]] == [cast["lang42"]]


def test_an_incompatible_projection_version_fails_clearly(world, capsys):
	path, _ = world
	error = _run(capsys, path, "--expect-projection", "2.0", "home",
	             viewer="lang.ada", expect_ok=False)
	assert "not compatible" in error["error"]
	ok = _run(capsys, path, "--expect-projection", "1.7", "home",
	          viewer="lang.ada")
	assert ok["result"], "a compatible minor was refused"


def test_errors_are_json_with_exit_one(world, capsys):
	path, _ = world
	error = _run(capsys, path, "detail", "nope-W1", viewer="lang.ada",
	             expect_ok=False)
	assert error == {"error": "no work 'nope-W1'"}


# -- typed traversal ---------------------------------------------------------

def test_the_fan_in_is_reachable_by_relation_alone(world, capsys):
	"""From a consumer's own Work to every co-consumer, following typed
	edges only — never search: pushcoin -> blocked_by -> LANG-42 -> blocks."""
	path, cast = world
	mine = _run(capsys, path, "links", cast["pushcoin"])["result"]
	assert [edge["id"] for edge in mine["blocked_by"]] == [cast["lang42"]]
	provider = _run(capsys, path, "links",
	                mine["blocked_by"][0]["id"])["result"]
	co_consumers = [edge["id"] for edge in provider["blocks"]]
	assert co_consumers == [cast["pushcoin"], cast["web"], cast["mdb"]]


# -- pagination on the sequence ----------------------------------------------

def test_pagination_joins_cleanly_across_a_same_second_burst(tmp_path, capsys):
	"""The protocol-10 defect, demonstrated fixed: publish a burst well
	inside one second, page with a small limit, and the pages join with no
	skip and no repeat — because the cursor is the sequence, not a
	timestamp."""
	path = str(tmp_path / "burst.sqlite3")
	_run(capsys, path, "init")
	_run(capsys, path, "register-team", "--team", "lang", "--display", "L")
	_run(capsys, path, "register-member", "--team", "lang", "--member",
	     "ada", "--display", "Ada")
	_run(capsys, path, "register-kind", "--team", "lang", "--kind", "bug",
	     "--display", "Bugs")
	work = _run(capsys, path, "create", "--team", "lang", "--kind", "bug",
	            "--title", "burst", "--origin", "self-initiated",
	            "--body", "first", viewer="lang.ada")["result"]["work_id"]
	for index in range(40):
		_run(capsys, path, "post", work, "--body", f"burst {index}",
		     viewer="lang.ada")

	full = _run(capsys, path, "discussion", work)["result"]
	assert len(full) == 41
	paged, after = [], 0
	for _page in range(50):
		page = _run(capsys, path, "discussion", work, "--after", str(after),
		            "--limit", "7")["result"]
		if not page:
			break
		paged.extend(page)
		after = page[-1]["seq"]
	assert [m["seq"] for m in paged] == [m["seq"] for m in full], \
		"pages skipped or repeated rows"


# -- mutations return the committed record -----------------------------------

def test_mutating_verbs_return_the_committed_state(tmp_path, capsys):
	path = str(tmp_path / "mut.sqlite3")
	_run(capsys, path, "init")
	_run(capsys, path, "register-team", "--team", "lang", "--display", "L")
	_run(capsys, path, "register-member", "--team", "lang", "--member",
	     "ada", "--display", "Ada")
	for kind in ("rsrch", "impl", "rev"):
		_run(capsys, path, "register-kind", "--team", "lang", "--kind", kind,
		     "--display", kind)
	created = _run(capsys, path, "create", "--team", "lang", "--kind",
	               "rsrch", "--title", "t", "--origin", "external-report",
	               "--body", "b", viewer="lang.ada")["result"]
	assert created["work_id"].endswith(f"-W{created['seq']}")

	passed = _run(capsys, path, "post", created["work_id"], "--body", "go",
	              "--pass-to", "lang.impl", "--set-next", "lang.rev",
	              viewer="lang.ada")["result"]
	assert passed["kind"] == "pass"
	returned = _run(capsys, path, "post", created["work_id"], "--body",
	                "done", "--pass-to", "lang.rev",
	                viewer="lang.ada")["result"]
	assert returned["kind"] == "return", \
		"the CLI lost the audited return distinction"

	closed = _run(capsys, path, "close", created["work_id"],
	              "--disposition", "verified", viewer="lang.ada")["result"]
	assert closed["kind"] == "close_work"
	detail = _run(capsys, path, "detail", created["work_id"],
	              viewer="lang.ada")["result"]
	assert detail["status"] == "closed"
	assert detail["available_transitions"] == ["reopen"]


def test_a_mutation_without_a_viewer_is_refused(world, capsys):
	path, cast = world
	error = _run(capsys, path, "post", cast["lang42"], "--body", "anon",
	             expect_ok=False)
	assert "needs --viewer" in error["error"]
