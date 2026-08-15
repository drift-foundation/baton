"""A1: schema, publication sequence, identity registration.

The three properties this step exists to pin, each tested against the way it
actually fails: sequence integrity under real concurrency (16 processes, per
the resource grant), no reuse across restart, and identity refused at
registration with the measurement in the error.
"""

from __future__ import annotations

import hashlib
import multiprocessing
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402


_PROCESS_CONTEXT = multiprocessing.get_context("spawn")


@pytest.fixture
def authority(tmp_path):
	with bw.Authority.init(str(tmp_path / "work.sqlite3")) as store:
		yield store


# -- lifecycle ---------------------------------------------------------------

def test_init_refuses_to_overwrite(tmp_path):
	path = tmp_path / "work.sqlite3"
	bw.Authority.init(str(path)).close()
	with pytest.raises(bw.WorkError, match="already exists"):
		bw.Authority.init(str(path))


def test_open_refuses_a_missing_or_foreign_schema(tmp_path):
	with pytest.raises(bw.WorkError, match="not an initialized"):
		bw.Authority(str(tmp_path / "absent.sqlite3"))
	foreign = tmp_path / "foreign.sqlite3"
	conn = sqlite3.connect(str(foreign))
	conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
	conn.execute("INSERT INTO meta VALUES ('schema_version', '999')")
	conn.commit(); conn.close()
	with pytest.raises(bw.WorkError, match="schema version"):
		bw.Authority(str(foreign))


def test_init_writes_no_handshake_file(tmp_path):
	"""SUPERSEDED BY RULING (C2, 2026-08-14): WORK.json is gone. The identity
	lives in `baton.json` and the database stores the same uuid plus the
	accepted digest — a third document would be a second place for the truth
	to disagree with itself. This test pins the ABSENCE so nobody restores
	the file out of habit."""
	bw.Authority.init(str(tmp_path / "work.sqlite3")).close()
	assert sorted(os.listdir(tmp_path)) == ["work.sqlite3"], \
		"init created something beside the database"


def test_meta_pins_protocol_and_uuid(authority):
	meta = authority.meta()
	assert meta["protocol_version"] == "11"
	assert meta["schema_version"] == "5"  # WS-2 g3: review_at/clock
	assert len(meta["authority_uuid"]) == 32


# -- the publication sequence ------------------------------------------------

def _hammer(path: str, worker: int, count: int) -> None:
	store = bw.Authority(path)
	try:
		for index in range(count):
			store.register_team(f"w{worker}i{index}"[:6],
			                    f"worker {worker} item {index}")
	finally:
		store.close()


@pytest.mark.serial
def test_sixteen_concurrent_writers_share_one_strict_sequence(tmp_path):
	"""The A1 acceptance test: 16 processes, one authority, and afterwards
	the sequence is exactly 1..N with no duplicate and no hole — which is
	what 'allocated inside the write transaction' MEANS observably."""
	path = str(tmp_path / "work.sqlite3")
	bw.Authority.init(path).close()
	workers, per_worker = 16, 25
	procs = [_PROCESS_CONTEXT.Process(target=_hammer,
	                                  args=(path, worker, per_worker))
	         for worker in range(workers)]
	for proc in procs:
		proc.start()
	for proc in procs:
		proc.join(timeout=120)
		assert proc.exitcode == 0
	with bw.Authority(path) as store:
		seqs = [event["seq"] for event in
		        store.events(limit=workers * per_worker + 10)]
		assert seqs == list(range(1, workers * per_worker + 1))
		assert store.last_seq() == workers * per_worker


def test_restart_continues_above_everything_committed(tmp_path):
	path = str(tmp_path / "work.sqlite3")
	with bw.Authority.init(path) as store:
		store.register_team("lang", "Language")
		before = store.last_seq()
	with bw.Authority(path) as store:
		result = store.register_team("web", "Web")
		assert result["seq"] == before + 1


def test_a_failed_mutation_allocates_nothing_observable(authority):
	"""A refusal mid-transaction rolls the sequence back with it: the next
	committed event is dense against the last, so a reader can treat the
	sequence as gapless."""
	authority.register_team("lang", "Language")
	with pytest.raises(bw.WorkError, match="already registered"):
		authority.register_team("lang", "Language again")
	result = authority.register_team("web", "Web")
	seqs = [event["seq"] for event in authority.events()]
	assert seqs == [1, 2]
	assert result["seq"] == 2


# -- identity ---------------------------------------------------------------

def test_handles_are_registered_with_display_names(authority):
	authority.register_team("lang", "Language Tools")
	authority.register_member("lang", "slaw", "Slawomir")
	authority.register_kind("lang", "bug", "Bug reports")
	rows = authority.conn.execute("SELECT * FROM members").fetchall()
	assert [(row["team"], row["handle"], row["display"]) for row in rows] == \
		[("lang", "slaw", "Slawomir")]


@pytest.mark.parametrize("bad,fragment", [
	("implementer", "11 display cells"),          # the protocol-10 casualty
	("reviewer", "8 display cells"),
	("research", "8 display cells"),              # the canonical-flow casualty
	("", "non-empty"),
	("a b", "whitespace"),
	("a.b", "reserves"),
	("a,b", "reserves"),
	("a@b", "reserves"),
	("a*b", "reserves"),
	("=>ab", "reserves"),
	("tab\t", "whitespace"),
	("ctl\x07", "whitespace|control"),
])
def test_a_handle_that_breaks_the_grammar_is_refused(authority, bad, fragment):
	with pytest.raises(bw.WorkError, match=fragment):
		authority.register_team(bad, "display")
	assert authority.last_seq() == 0, "a refusal wrote an event"


def test_wide_and_zero_width_tricks_are_measured_not_counted(authority):
	# Six CJK characters are twelve cells: length lies, width does not.
	with pytest.raises(bw.WorkError, match="12 display cells"):
		authority.register_team("工作流程图表", "wide")
	# Three CJK characters are six cells: allowed.
	authority.register_team("工作流", "workflow")
	# A combining mark would make visual width disagree with content: refused
	# outright, not merely measured.
	with pytest.raises(bw.WorkError, match="zero-width"):
		authority.register_member("工作流", "étude", "Etude")
	# A zero-width joiner is the same trick by another codepoint.
	with pytest.raises(bw.WorkError, match="zero-width"):
		authority.register_member("工作流", "a‍b", "sneaky")


def test_kinds_retire_but_never_vanish_or_come_back(authority):
	authority.register_team("lang", "Language")
	authority.register_kind("lang", "bug", "Bug intake")
	authority.retire_kind("lang", "bug")
	with pytest.raises(bw.WorkError, match="already retired"):
		authority.retire_kind("lang", "bug")
	with pytest.raises(bw.WorkError, match="keep their name forever"):
		authority.register_kind("lang", "bug", "Bug intake II")
	row = authority.conn.execute(
		"SELECT retired FROM kinds WHERE team='lang' AND handle='bug'").fetchone()
	assert row["retired"] == 1


# -- purity ------------------------------------------------------------------

def _digest(path: str) -> str:
	return hashlib.sha256(open(path, "rb").read()).hexdigest()


def test_reads_change_no_byte(tmp_path):
	"""Rulings 3+4 at the A1 surface: meta, events, last_seq and failed
	validations leave the database file byte-identical. The full-projection
	version of this sweep arrives with A5; the property starts holding now."""
	path = str(tmp_path / "work.sqlite3")
	with bw.Authority.init(path) as store:
		store.register_team("lang", "Language")
		store.register_member("lang", "slaw", "Slawomir")
		store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	before = _digest(path)
	with bw.Authority(path) as store:
		store.meta(); store.events(); store.last_seq()
		with pytest.raises(bw.WorkError):
			store.register_team("lang", "duplicate")
		store.events(after=1); store.meta()
		store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert _digest(path) == before


def test_a_mutation_that_fails_inside_the_transaction_leaves_no_gap(authority):
	"""The first break-sweep of A1 passed WITH the break applied, because
	every refusal above happens in pre-validation, before the transaction
	opens. This test fails inside `mutate` itself — after allocation — which
	is where 'allocated inside the transaction' is actually load-bearing."""
	authority.register_team("lang", "Language")

	def exploding(conn, seq):
		raise RuntimeError("boom after allocation")

	with pytest.raises(RuntimeError, match="boom"):
		authority._write("boom", "test", {}, exploding)
	result = authority.register_team("web", "Web")
	assert result["seq"] == 2, \
		f"the failed mutation burned sequence number 2 (got {result['seq']})"
	assert [event["seq"] for event in authority.events()] == [1, 2]


def _race_same_names(path: str, worker: int) -> None:
	store = bw.Authority(path)
	try:
		for name in ("lang", "web", "build", "dq", "tui"):
			try:
				store.register_team(name, f"claimed by worker {worker}")
			except bw.WorkError:
				pass                                  # lost the race: fine
	finally:
		store.close()


@pytest.mark.serial
def test_losing_a_registration_race_burns_no_sequence_number(tmp_path):
	"""The same property through the PUBLIC api under real contention: 16
	processes race to register the same five teams. Pre-validation passes in
	several of them; the constraint refuses the losers INSIDE the
	transaction; the winners' events must still be dense."""
	path = str(tmp_path / "work.sqlite3")
	bw.Authority.init(path).close()
	procs = [_PROCESS_CONTEXT.Process(target=_race_same_names, args=(path, w))
	         for w in range(16)]
	for proc in procs:
		proc.start()
	for proc in procs:
		proc.join(timeout=120)
		assert proc.exitcode == 0
	with bw.Authority(path) as store:
		seqs = [event["seq"] for event in store.events()]
		assert len(seqs) == 5, f"expected 5 winners, got {len(seqs)}"
		assert seqs == [1, 2, 3, 4, 5], \
			f"losers burned sequence numbers: {seqs}"
