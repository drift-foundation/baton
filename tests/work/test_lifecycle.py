"""C2: config↔authority binding — crash-safe init, bound open, audited
generation+1 acceptance, capability gate, stranding refusal, no reuse.
"""

from __future__ import annotations

import copy
import json
import multiprocessing
import os
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from test_config import VALID                                 # noqa: E402


def _write_config(tmp_path, document) -> str:
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
	return str(path)


def _generation(document, generation) -> dict:
	document = copy.deepcopy(document)
	document["generation"] = generation
	return document


@pytest.fixture
def world(tmp_path):
	config_path = _write_config(tmp_path, VALID)
	lc.init_from_config(config_path, participant="lang.ada")
	return tmp_path, config_path


# -- init ---------------------------------------------------------------------

def test_init_binds_uuid_digest_and_topology(world):
	tmp_path, config_path = world
	assert sorted(p for p in os.listdir(tmp_path)
	              if not p.startswith(".")) == ["baton.json", "work.sqlite3"]
	with lc.open_bound(config_path) as store:
		meta = store.meta()
		assert meta["authority_uuid"] == VALID["instance"]["authority_uuid"]
		assert meta["accepted_generation"] == "1"
		routes = store.conn.execute(
			"SELECT team, handle, role FROM routes WHERE removed=0 "
			"ORDER BY team, handle").fetchall()
		assert [(r["team"], r["handle"], r["role"]) for r in routes] == \
			[("lang", "intake", "rsrch"), ("lang", "review", "rev"),
			 ("web", "all", "dev")]
		caps = store.conn.execute(
			"SELECT team, member FROM member_capabilities "
			"WHERE capability='config'").fetchall()
		assert [(c["team"], c["member"]) for c in caps] == [("lang", "ada")]
		events = store.events()
		assert [e["kind"] for e in events] == ["accept_config"]
		assert events[0]["payload"]["generation_to"] == 1


def test_init_refuses_generation_beyond_one_and_existing_db(tmp_path):
	path = _write_config(tmp_path, _generation(VALID, 3))
	with pytest.raises(bw.WorkError, match="accepts generation 1"):
		lc.init_from_config(path, participant="lang.ada")
	path = _write_config(tmp_path, VALID)
	lc.init_from_config(path, participant="lang.ada")
	with pytest.raises(bw.WorkError, match="already exists"):
		lc.init_from_config(path, participant="lang.ada")


def test_init_is_crash_safe_at_the_publish(tmp_path, monkeypatch):
	"""Crash at the publish link: NOTHING at work.sqlite3, and the retry
	succeeds cleanly — the ruled refusal/retry behavior. (R1 replaced the
	rename with link(2), so the crash point moved with it.)"""
	config_path = _write_config(tmp_path, VALID)
	real_link = os.link

	def crash(src, dst, **kwargs):
		if dst.endswith("work.sqlite3"):
			raise OSError("simulated crash at the commit point")
		return real_link(src, dst, **kwargs)

	monkeypatch.setattr(os, "link", crash)
	with pytest.raises(OSError, match="simulated crash"):
		lc.init_from_config(config_path, participant="lang.ada")
	monkeypatch.undo()
	assert not os.path.lexists(tmp_path / "work.sqlite3")
	result = lc.init_from_config(config_path, participant="lang.ada")
	assert result["generation"] == 1
	lc.open_bound(config_path).close()


def _race_init(config_dir: str, report: str) -> None:
	import json as _json
	try:
		lc.init_from_config(os.path.join(config_dir, "baton.json"),
		                    participant="lang.ada")
		outcome = "won"
	except bw.WorkError as refusal:
		outcome = f"refused: {refusal}"
	with open(report, "w") as handle:
		_json.dump({"outcome": outcome}, handle)


def test_concurrent_initialization_has_one_winner_untouched(tmp_path):
	"""R1. Two initializers race: exactly one wins, the loser refuses, and
	the winner's published bytes are preserved byte-for-byte — rename would
	have let the second silently replace the first."""
	import hashlib
	_write_config(tmp_path, VALID)
	reports = [str(tmp_path / f"init-{index}.json") for index in range(8)]
	procs = [multiprocessing.Process(target=_race_init,
	                                 args=(str(tmp_path), report))
	         for report in reports]
	for proc in procs:
		proc.start()
	for proc in procs:
		proc.join(timeout=120)
		assert proc.exitcode == 0
	outcomes = [json.load(open(report))["outcome"] for report in reports]
	assert outcomes.count("won") == 1, outcomes
	assert all("already exists" in outcome for outcome in outcomes
	           if outcome != "won"), outcomes
	# The winner still opens and binds — nothing overwrote it.
	with lc.open_bound(str(tmp_path / "baton.json")) as store:
		assert store.meta()["accepted_generation"] == "1"


# -- bound open ---------------------------------------------------------------

def test_open_refuses_an_edited_unaccepted_config(world):
	tmp_path, config_path = world
	document = copy.deepcopy(VALID)
	document["teams"]["web"]["display"] = "Web Platform"
	_write_config(tmp_path, document)
	with pytest.raises(bw.WorkError, match="edited but not accepted"):
		lc.open_bound(config_path)


def test_open_refuses_a_foreign_authority(world, tmp_path):
	_tmp, config_path = world
	with bw.Authority(lc._database_path(config_path)) as store:
		store.conn.execute("UPDATE meta SET value='ff'||substr(value,3) "
		                   "WHERE key='authority_uuid'")
		store.conn.commit()
	with pytest.raises(bw.WorkError, match="not a pair"):
		lc.open_bound(config_path)


def test_open_refuses_a_generation_disagreement(world):
	tmp_path, config_path = world
	with bw.Authority(lc._database_path(config_path)) as store:
		store.conn.execute(
			"UPDATE meta SET value='7' WHERE key='accepted_generation'")
		store.conn.commit()
	with pytest.raises(bw.WorkError, match="accepted 7"):
		lc.open_bound(config_path)


# -- acceptance ---------------------------------------------------------------

def _proposal(world, change) -> str:
	tmp_path, _config_path = world
	document = _generation(VALID, 2)
	change(document)
	return _write_config(tmp_path, document)


def test_acceptance_applies_projects_and_audits(world):
	tmp_path, config_path = world
	path = _proposal(world, lambda d: (
		d["teams"]["lang"]["participants"].__setitem__(
			"linus", {"display": "Linus", "roles": ["impl"]}),
		d["teams"]["lang"]["routes"]["intake"].__setitem__(
			"handlers", ["ada"]),
		d["teams"]["web"]["kinds"].__setitem__(
			"perf", {"display": "Performance", "route": "all"})))
	result = lc.accept_config(path, actor="lang.ada")
	assert result["generation"] == 2
	assert "member:lang.linus" in result["changes"]["added"]
	assert "kind:web.perf" in result["changes"]["added"]
	with lc.open_bound(config_path) as store:
		assert store.meta()["accepted_generation"] == "2"
		assert store.conn.execute(
			"SELECT 1 FROM members WHERE team='lang' AND handle='linus' "
			"AND removed=0").fetchone()
		kinds = [e["kind"] for e in store.events()]
		assert kinds == ["accept_config", "accept_config"]


def test_acceptance_records_handler_rerouting(world):
	tmp_path, config_path = world
	path = _proposal(world, lambda d: (
		d["teams"]["lang"]["participants"]["grace"]["roles"].append("rsrch"),
		d["teams"]["lang"]["routes"]["intake"].__setitem__(
			"handlers", ["grace"])))
	result = lc.accept_config(path, actor="lang.ada")
	assert result["changes"]["rerouted"] == ["lang.intake"]
	with lc.open_bound(config_path) as store:
		handlers = store.conn.execute(
			"SELECT member FROM route_handlers WHERE team='lang' "
			"AND route='intake'").fetchall()
		assert [h["member"] for h in handlers] == ["grace"]


@pytest.mark.parametrize("generation,fragment", [
	(1, "next acceptable proposal is 2"),
	(3, "next acceptable proposal is 2"),
])
def test_acceptance_requires_exactly_generation_plus_one(world, generation,
                                                        fragment):
	tmp_path, _config = world
	document = _generation(VALID, generation)
	document["teams"]["web"]["display"] = "Web!"
	path = _write_config(tmp_path, document)
	with pytest.raises(bw.WorkError, match=fragment):
		lc.accept_config(path, actor="lang.ada")


def test_a_proposal_cannot_authorize_its_own_acceptor(world):
	"""grace grants herself the config capability IN THE PROPOSAL and then
	tries to accept it: refused against the accepted generation."""
	path = _proposal(world, lambda d: d["teams"]["lang"]["participants"]
	                 ["grace"].__setitem__("capabilities", ["config"]))
	with pytest.raises(bw.WorkError, match="cannot authorize its own"):
		lc.accept_config(path, actor="lang.grace")
	# ada accepts the same proposal; from then on grace may accept gen 3.
	lc.accept_config(path, actor="lang.ada")


def test_acceptance_refuses_uuid_reassignment_and_noop(world):
	tmp_path, _config = world
	path = _proposal(world, lambda d: d["instance"].__setitem__(
		"authority_uuid", "cd" * 16))
	with pytest.raises(bw.WorkError, match="identity is never re-assigned"):
		lc.accept_config(path, actor="lang.ada")
	same = _write_config(tmp_path, VALID)
	with pytest.raises(bw.WorkError, match="nothing to accept|generation"):
		lc.accept_config(same, actor="lang.ada")


def test_removed_identities_are_never_silently_reused(world):
	tmp_path, config_path = world
	# Generation 2 removes web.wren's kind 'bug' (retires it) by dropping it.
	document = _generation(VALID, 2)
	del document["teams"]["web"]["kinds"]["bug"]
	lc.accept_config(_write_config(tmp_path, document), actor="lang.ada")
	# Generation 3 brings 'bug' back: refused as reuse.
	document = copy.deepcopy(document)
	document["generation"] = 3
	document["teams"]["web"]["kinds"]["bug"] = \
		{"display": "Bugs again", "route": "all"}
	with pytest.raises(bw.WorkError, match="never silently reused"):
		lc.accept_config(_write_config(tmp_path, document), actor="lang.ada")


def test_a_stranding_proposal_is_refused_naming_the_records(world):
	tmp_path, config_path = world
	with lc.open_bound(config_path) as store:
		work = tr.create_work(store, team="web", kind="bug",
		                      title="live work", origin="external-report", classification="suspected-defect",
		                      author="wren", body="open")["work_id"]
	document = _generation(VALID, 2)
	del document["teams"]["web"]["kinds"]["bug"]
	path = _write_config(tmp_path, document)
	with pytest.raises(bw.WorkError, match=f"work {work}"):
		lc.accept_config(path, actor="lang.ada")
	# Close the work under the ACCEPTED config; then re-propose and accept.
	# (`_write_config` reuses one filename, so the proposal must be written
	# again after the restore — the first version of this test overwrote its
	# own proposal and accidentally proposed generation 1.)
	restored = _write_config(tmp_path, VALID)
	with lc.open_bound(restored) as store:
		tr.close_work(store, work, actor_team="web", actor="wren",
		              rationale="done", outcome="satisfying")
	path = _write_config(tmp_path, document)
	lc.accept_config(path, actor="lang.ada")


def _race(config_dir: str, index: int) -> None:
	try:
		lc.accept_config(os.path.join(config_dir, "baton.json"),
		                 actor="lang.ada")
	except bw.WorkError:
		pass                                        # losing legibly is fine


def test_concurrent_acceptance_burns_nothing(world):
	"""Sixteen processes race to accept ONE generation-2 proposal: exactly
	one acceptance event lands and the sequence stays dense."""
	tmp_path, config_path = world
	document = _generation(VALID, 2)
	document["teams"]["web"]["display"] = "Web Platform"
	_write_config(tmp_path, document)
	procs = [multiprocessing.Process(target=_race,
	                                 args=(str(tmp_path), index))
	         for index in range(16)]
	for proc in procs:
		proc.start()
	for proc in procs:
		proc.join(timeout=120)
		assert proc.exitcode == 0
	with lc.open_bound(config_path) as store:
		events = store.events()
		accepts = [e for e in events if e["kind"] == "accept_config"]
		assert len(accepts) == 2                    # init + one winner
		seqs = [e["seq"] for e in events]
		assert seqs == list(range(1, len(seqs) + 1)), "a loser burned a seq"
		assert store.meta()["accepted_generation"] == "2"


# -- the C2 review's four regressions (R1 is above with the init race) --------

def test_the_in_lock_gate_catches_work_the_precheck_never_saw(world,
                                                              monkeypatch):
	"""R2, deterministically: the pre-lock check is silenced for one call to
	model a Work committing between it and the transaction; the in-lock gate
	must still refuse. If the pre-check were the gate, this would project a
	stranding configuration."""
	tmp_path, config_path = world
	with lc.open_bound(config_path) as store:
		work = tr.create_work(store, team="web", kind="bug",
		                      title="raced in", origin="external-report", classification="suspected-defect",
		                      author="wren", body="committed late")["work_id"]
	document = _generation(VALID, 2)
	del document["teams"]["web"]["kinds"]["bug"]
	path = _write_config(tmp_path, document)

	real_gate = lc._gate_checks
	calls = []

	def first_call_blind(conn, doc):
		calls.append(1)
		if len(calls) == 1:
			return                       # the racing writer's window
		return real_gate(conn, doc)

	monkeypatch.setattr(lc, "_gate_checks", first_call_blind)
	with pytest.raises(bw.WorkError, match=f"work {work}"):
		lc.accept_config(path, actor="lang.ada")
	assert len(calls) == 2, "the in-lock gate never ran"
	# The file currently holds the refused proposal, so bound open would
	# refuse on digest; read the authority directly for the assertion.
	with bw.Authority(lc._database_path(config_path)) as store:
		assert store.meta()["accepted_generation"] == "1", \
			"the stranding proposal was projected"


def test_removed_route_names_are_never_reused(world):
	"""R3: routes are named identities like everything else."""
	tmp_path, config_path = world
	document = _generation(VALID, 2)
	# Retire lang's 'review' route (and the kind that references it).
	del document["teams"]["lang"]["routes"]["review"]
	del document["teams"]["lang"]["kinds"]["rev"]
	lc.accept_config(_write_config(tmp_path, document), actor="lang.ada")
	# Generation 3 reintroduces the route name with a DIFFERENT role.
	document = copy.deepcopy(document)
	document["generation"] = 3
	document["teams"]["lang"]["routes"]["review"] = \
		{"role": "impl", "handlers": ["grace"]}
	with pytest.raises(bw.WorkError, match="route:lang.review"):
		lc.accept_config(_write_config(tmp_path, document), actor="lang.ada")


def test_a_role_only_route_change_is_audited_as_rerouted(world):
	"""R4: same handler, different role — the responsibility mapping moved
	and the audit must say so."""
	tmp_path, _config = world
	document = _generation(VALID, 2)
	document["teams"]["lang"]["participants"]["ada"]["roles"].append("impl")
	document["teams"]["lang"]["routes"]["intake"]["role"] = "impl"
	# handlers stay ["ada"] — the old audit missed exactly this.
	result = lc.accept_config(_write_config(tmp_path, document),
	                          actor="lang.ada")
	assert result["changes"]["rerouted"] == ["lang.intake"]
