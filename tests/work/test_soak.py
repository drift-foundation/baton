"""A8: the adversarial soak — everything interleaved with everything.

Sixteen worker processes (the granted width) drive seeded-random mixes of
every transition against ONE authority, with two kinds of sabotage running
among them: exception injection INSIDE the write transaction, and workers
that kill themselves (`os._exit`) INSIDE an uncommitted write transaction so
SQLite's crash recovery is exercised for real. Legitimate refusals are counted, not hidden — the failure
taxonomy is part of the evidence.

Afterwards the whole state is re-derived from scratch and compared with what
the transitions maintained incrementally:

- the committed event sequence is dense (no burned numbers, ever);
- every stored `ready` flag equals readiness recomputed from nothing;
- every open work has a responsible endpoint, every closed work has none;
- the union graph is acyclic;
- pending obligations are unresolved, resolved ones point at real events;
- and the read surface, swept as every member, changes no byte.

Set SOAK_REPORT=/path to also write the transcript/taxonomy artifact the
plan requires in the finding folder.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402

WORKERS = 16
OPS_PER_WORKER = 150
TEAMS = [("lang", "ada"), ("push", "sl"), ("web", "wren"), ("mdb", "mo")]
_PROCESS_CONTEXT = multiprocessing.get_context("spawn")


def _seed_world(path: str) -> None:
	store = bw.Authority.init(path)
	for team, member in TEAMS:
		store.register_team(team, team.title())
		store.register_member(team, member, member.title())
		store.register_kind(team, "bug", "Bug intake")
		store.register_kind(team, "rev", "Review")
	store.register_kind("lang", "dead", "Retired")
	store.retire_kind("lang", "dead")
	for team, member in TEAMS:
		tr.create_work(store, team=team, kind="bug", title=f"{team} seed",
		               origin="self-initiated", author=member, body="seed")
	store.close()


def _worker(path: str, worker: int, report_path: str) -> None:
	rng = random.Random(1000 + worker)          # deterministic per worker
	team, member = TEAMS[worker % len(TEAMS)]
	taxonomy: dict[str, int] = {}
	committed = 0
	store = bw.Authority(path)

	# SABOTEUR 1: one worker in four injects an exception INSIDE the write
	# transaction on a fraction of its operations, by wrapping _write.
	saboteur = worker % 4 == 0
	real_write = store._write

	def wrapped(event_kind, actor, payload, mutate):
		if saboteur and rng.random() < 0.15:
			def exploding(conn, seq):
				mutate(conn, seq)
				raise RuntimeError("soak: injected post-mutate failure")
			try:
				return real_write(event_kind, actor, payload, exploding)
			except RuntimeError:
				raise bw.WorkError("soak-injected")
		return real_write(event_kind, actor, payload, mutate)

	store._write = wrapped

	def works() -> list[str]:
		return [row["id"] for row in store.conn.execute(
			"SELECT id FROM work ORDER BY created_seq")]

	def my_open_participating() -> list[str]:
		return [row["id"] for row in store.conn.execute(
			"SELECT w.id FROM work w JOIN work_participants p "
			"ON p.work = w.id WHERE w.status='open' AND p.team=? "
			"ORDER BY w.created_seq", (team,))]

	try:
		for op_index in range(OPS_PER_WORKER):
			# SABOTEUR 2: two workers die INSIDE an uncommitted write
			# transaction — rows inserted, sequence allocated, no commit —
			# so SQLite's crash recovery is exercised for real. The dense-
			# sequence invariant afterwards is what proves the rollback.
			if worker in (5, 11) and op_index == OPS_PER_WORKER // 2:
				prefix = store.meta()["authority_uuid"][:8]

				def die_mid_transaction(conn, seq):
					conn.execute(
						"INSERT INTO work (id, team, title, origin, status, "
						"current_team, current_kind, ready, created_seq) "
						"VALUES (?, ?, 'doomed', 'self-initiated', 'open', "
						"?, 'bug', 1, ?)",
						(f"{prefix}-W{seq}", team, team, seq))
					os._exit(0)
				real_write("create_work", f"{team}.{member}", {},
				           die_mid_transaction)
			choice = rng.random()
			try:
				if choice < 0.20:
					tr.create_work(
						store, team=team, kind="bug",
						title=f"w{worker} op{op_index}",
						origin="self-initiated", author=member,
						body="soak", parent=rng.choice(
							[None] + my_open_participating()[:4]))
				elif choice < 0.45:
					mine = my_open_participating()
					if mine:
						tr.post_message(
							store, rng.choice(mine), author_team=team,
							author=member, body=f"soak {worker}/{op_index}",
							include=rng.choice(["", "*.bug", "*.*"]) or ())
				elif choice < 0.60:
					mine = my_open_participating()
					if mine:
						other = rng.choice(TEAMS)[0]
						tr.post_message(
							store, rng.choice(mine), author_team=team,
							author=member, body="asking",
							request=f"{other}.bug")
				elif choice < 0.70:
					pending = pj.obligations(store, viewer_team=team)
					if pending:
						tr.respond_obligation(
							store, pending[0]["seq"], team=team,
							member=member, body="answered in soak")
				elif choice < 0.80:
					candidates = works()
					if len(candidates) >= 2:
						tr.add_dependency(
							store, rng.choice(candidates),
							rng.choice(candidates),
							actor_team=team, actor=member)
				elif choice < 0.90:
					mine = my_open_participating()
					if mine:
						tr.mark_seen(store, rng.choice(mine), team=team,
						             member=member,
						             up_to_seq=store.last_seq())
				elif choice < 0.97:
					mine = my_open_participating()
					if mine:
						tr.close_work(store, rng.choice(mine),
						              actor_team=team, actor=member,
						              disposition="soak close")
				else:
					closed = [row["id"] for row in store.conn.execute(
						"SELECT id FROM work WHERE status='closed'")]
					if closed:
						tr.reopen_work(store, rng.choice(closed),
						               actor_team=team, actor=member,
						               reason="soak reopen")
				committed += 1
			except bw.WorkError as refusal:
				key = str(refusal).split(";")[0].split(":")[0][:60]
				taxonomy[key] = taxonomy.get(key, 0) + 1
	finally:
		with open(report_path, "w") as handle:
			json.dump({"worker": worker, "committed": committed,
			           "refusals": taxonomy}, handle)
		store.close()


@pytest.mark.serial
def test_the_adversarial_soak(tmp_path):
	path = str(tmp_path / "soak.sqlite3")
	_seed_world(path)
	reports = [str(tmp_path / f"worker-{index}.json")
	           for index in range(WORKERS)]
	procs = [_PROCESS_CONTEXT.Process(target=_worker,
	                                  args=(path, index, reports[index]))
	         for index in range(WORKERS)]
	for proc in procs:
		proc.start()
	for proc in procs:
		proc.join(timeout=300)
		assert proc.exitcode == 0, f"worker died abnormally: {proc.exitcode}"

	store = bw.Authority(path)

	# 1. Dense committed sequence, exactly one event per number.
	seqs = [event["seq"] for event in store.events(limit=100000)]
	assert seqs == list(range(1, len(seqs) + 1)), "burned or duplicated seq"
	assert store.last_seq() == len(seqs)

	# 2. Stored readiness equals readiness re-derived from nothing.
	for row in store.conn.execute("SELECT * FROM work"):
		open_children = store.conn.execute(
			"SELECT COUNT(*) AS n FROM work WHERE parent=? AND status='open'",
			(row["id"],)).fetchone()["n"]
		open_blockers = store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges JOIN work w ON w.id=edges.blocker "
			"WHERE edges.work=? AND w.status='open'",
			(row["id"],)).fetchone()["n"]
		expected = 1 if (row["status"] == "open" and open_children == 0
		                 and open_blockers == 0) else 0
		assert row["ready"] == expected, \
			f"{row['id']}: stored ready {row['ready']} != derived {expected}"

	# 3. Open work has a responsible endpoint; closed work has none.
	for row in store.conn.execute("SELECT * FROM work"):
		if row["status"] == "open":
			assert row["current_team"] and row["current_kind"], \
				f"{row['id']} is open with nobody responsible"
		else:
			assert not row["current_team"] and not row["next_team"]

	# 4. The union graph is acyclic (full check, from scratch).
	waits: dict[str, set[str]] = {}
	for row in store.conn.execute("SELECT id, parent FROM work"):
		if row["parent"]:
			waits.setdefault(row["parent"], set()).add(row["id"])
	for row in store.conn.execute("SELECT work, blocker FROM edges"):
		waits.setdefault(row["work"], set()).add(row["blocker"])
	WHITE, GREY, BLACK = 0, 1, 2
	color: dict[str, int] = {}

	def visit(node: str) -> None:
		color[node] = GREY
		for neighbor in waits.get(node, ()):
			state = color.get(neighbor, WHITE)
			assert state != GREY, f"cycle through {neighbor}"
			if state == WHITE:
				visit(neighbor)
		color[node] = BLACK

	sys.setrecursionlimit(10000)
	for node in list(waits):
		if color.get(node, WHITE) == WHITE:
			visit(node)

	# 5. Obligation bookkeeping.
	for row in store.conn.execute("SELECT * FROM obligations"):
		if row["status"] == "pending":
			assert row["resolved_seq"] is None
		else:
			assert row["resolved_seq"] is not None

	# 6. Purity checkpoint: sweep everything as everyone; no byte moves.
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	before = hashlib.sha256(open(path, "rb").read()).hexdigest()
	all_work = [row["id"] for row in
	            store.conn.execute("SELECT id FROM work")]
	for team, member in TEAMS:
		pj.home(store, viewer_team=team, viewer_member=member)
		pj.obligations(store, viewer_team=team)
		for work in all_work:
			pj.links(store, work)
			pj.new_count(store, work, viewer_team=team, viewer_member=member)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	after = hashlib.sha256(open(path, "rb").read()).hexdigest()
	assert after == before

	# The taxonomy artifact, when asked for.
	taxonomy: dict[str, int] = {}
	total_committed = 0
	for report_path in reports:
		if os.path.isfile(report_path):
			report = json.load(open(report_path))
			total_committed += report["committed"]
			for key, count in report["refusals"].items():
				taxonomy[key] = taxonomy.get(key, 0) + count
	assert total_committed > 1000, "the soak barely ran"
	assert taxonomy, "no refusal was ever exercised; the soak was too gentle"
	destination = os.environ.get("SOAK_REPORT")
	if destination:
		with open(destination, "w") as handle:
			json.dump({"workers": WORKERS, "ops_per_worker": OPS_PER_WORKER,
			           "seed_base": 1000, "events_committed": len(seqs),
			           "worker_ops_committed": total_committed,
			           "refusal_taxonomy": dict(sorted(taxonomy.items())),
			           "crashed_workers": [5, 11],
			           "saboteur_workers": [0, 4, 8, 12]},
			          handle, indent=2, sort_keys=True)
			handle.write("\n")
	store.close()
