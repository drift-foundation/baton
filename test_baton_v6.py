"""Protocol-8 Baton storage-core tests (Handoff 1: T1-T6, T9, T10, T16-T18, T23-T25 core).

Fixtures are deliberately neutral (no host-project names): a small
multi-workspace shop with participants under `acme.*` and `hq.*`.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import sqlite3

import pytest

import baton_v6 as b6



def make_config(generation: int = 1) -> dict:
	return {
		"config_version": 1,
		"protocol_version": b6.PROTOCOL_VERSION,
		"generation": generation,
		"mailbox": {"name": "acme-local"},
		"participants": {
			"acme.reviewer": {},
			"acme.implementer": {},
			"hq.lead": {"capabilities": ["recovery", "config"]},
		},
		"roots": {},
	}


@pytest.fixture
def instance(tmp_path):
	config_path = str(tmp_path / "baton.json")
	with open(config_path, "w") as handle:
		json.dump(make_config(), handle)
	b6.init_instance(config_path)
	return config_path


@pytest.fixture
def store(instance):
	st = b6.open_instance(instance)
	yield st
	st.close()


def send_one(store, body=b"hello", retention="durable", sender="acme.reviewer",
             recipient="acme.implementer", kind="question", thread="topic-1"):
	return store.send(sender, recipient, kind=kind,
	                  body=body, thread_id=thread, retention=retention)


# ---------------------------------------------------------------------------
# init / open validation (T10, T22-core, T24)
# ---------------------------------------------------------------------------

class TestInitOpen:
	def test_init_creates_wal_instance_beside_config(self, instance, tmp_path):
		assert (tmp_path / "mailbox.sqlite3").is_file()
		with b6.open_instance(instance) as st:
			assert st.conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
			row = st.conn.execute("SELECT * FROM instance_meta").fetchone()
			assert row["protocol"] == b6.PROTOCOL_VERSION
			assert row["accepted_generation"] == 1

	def test_init_refuses_existing_db(self, instance):
		with pytest.raises(b6.BatonError, match="refusing to initialize"):
			b6.init_instance(instance)

	def test_open_without_db_fails_closed_never_creates(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		with pytest.raises(b6.BatonError, match="run init"):
			b6.open_instance(config_path)
		assert not (tmp_path / "mailbox.sqlite3").exists()

	def test_symlink_db_refused(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		real = tmp_path / "elsewhere.sqlite3"
		real.write_bytes(b"")
		os.symlink(real, tmp_path / "mailbox.sqlite3")
		with pytest.raises(b6.BatonError, match="symlink"):
			b6.open_instance(config_path)

	def test_symlink_config_refused(self, tmp_path):
		real = tmp_path / "real.json"
		with open(real, "w") as handle:
			json.dump(make_config(), handle)
		link = tmp_path / "baton.json"
		os.symlink(real, link)
		with pytest.raises(b6.BatonError, match="symlink"):
			b6.load_config(str(link))

	def test_wrong_journal_mode_refused(self, instance, tmp_path):
		conn = sqlite3.connect(tmp_path / "mailbox.sqlite3")
		conn.execute("PRAGMA journal_mode=DELETE")
		conn.close()
		with pytest.raises(b6.BatonError, match="journal_mode"):
			b6.open_instance(instance)

	def test_user_version_gate(self, instance, tmp_path):
		conn = sqlite3.connect(tmp_path / "mailbox.sqlite3")
		conn.execute("PRAGMA user_version=5")
		conn.close()
		with pytest.raises(b6.BatonError, match="protocol 5"):
			b6.open_instance(instance)

	def test_schema_drift_refused(self, instance, tmp_path):
		conn = sqlite3.connect(tmp_path / "mailbox.sqlite3")
		conn.execute("DROP INDEX contents_sha_idx")
		conn.close()
		with pytest.raises(b6.BatonError, match="schema validation failed"):
			b6.open_instance(instance)

	def test_corrupted_db_fails_closed(self, instance, tmp_path):
		db = tmp_path / "mailbox.sqlite3"
		with open(db, "r+b") as handle:
			handle.seek(0)
			handle.write(b"\x00" * 32)
		with pytest.raises(b6.BatonError):
			b6.open_instance(instance)

	def test_config_generation_mismatch_refused(self, instance, tmp_path):
		with open(instance, "w") as handle:
			json.dump(make_config(generation=2), handle)
		with pytest.raises(b6.BatonError, match="regen"):
			b6.open_instance(instance)

	def test_config_content_drift_refused(self, instance, tmp_path):
		cfg = make_config()
		cfg["participants"]["acme.newcomer"] = {}
		with open(instance, "w") as handle:
			json.dump(cfg, handle)
		with pytest.raises(b6.BatonError, match="digest"):
			b6.open_instance(instance)

	def test_readonly_store_rejects_writes(self, instance):
		with b6.open_instance(instance, readonly=True) as st:
			with pytest.raises(b6.BatonError, match="read-only"):
				send_one(st)

	def test_sidecars_beside_db(self, instance, tmp_path):
		with b6.open_instance(instance) as st:
			send_one(st)
			names = {p.name for p in tmp_path.iterdir()}
			assert "mailbox.sqlite3-wal" in names


class TestStrictJson:
	def test_duplicate_keys_rejected(self):
		with pytest.raises(b6.BatonError, match="duplicate"):
			b6.loads_strict('{"a": 1, "a": 2}')

	def test_nan_rejected(self):
		with pytest.raises(b6.BatonError, match="non-finite"):
			b6.loads_strict('{"a": NaN}')

	def test_trailing_content_rejected(self):
		with pytest.raises(b6.BatonError, match="parse error"):
			b6.loads_strict('{"a": 1} trailing')

	def test_bool_is_not_int(self):
		cfg = make_config()
		cfg["generation"] = True
		with pytest.raises(b6.BatonError, match="integer"):
			b6.validate_config(cfg)

	def test_unknown_field_rejected(self):
		cfg = make_config()
		cfg["surprise"] = 1
		with pytest.raises(b6.BatonError, match="unknown field"):
			b6.validate_config(cfg)

	def test_unknown_participant_field_rejected(self):
		cfg = make_config()
		cfg["participants"]["acme.reviewer"]["extra"] = 1
		with pytest.raises(b6.BatonError, match="unknown field"):
			b6.validate_config(cfg)


# ---------------------------------------------------------------------------
# send / claim (T1, T9)
# ---------------------------------------------------------------------------

class TestSendClaim:
	def test_send_then_claim_roundtrip(self, store):
		mid = send_one(store, body=b"payload")
		claim = store.claim("acme.implementer")
		assert claim["message_id"] == mid
		assert claim["state"] == "active"
		msg = store.get_message(mid)
		assert msg["state"] == "claimed"
		assert msg["body"] == b"payload"

	def test_claim_empty_mailbox_is_none(self, store):
		with pytest.raises(b6.BatonError) as excinfo:
			store.claim("acme.implementer")
		assert excinfo.value.exit_code == b6.EXIT_NONE

	def test_undeclared_participants_rejected(self, store):
		with pytest.raises(b6.BatonError, match="not declared"):
			store.send("acme.reviewer", "acme.ghost",
			           kind="question", body=b"x")
		with pytest.raises(b6.BatonError, match="not declared"):
			store.send("acme.ghost", "acme.reviewer",
			           kind="question", body=b"x")

	def test_participant_address_is_the_whole_identity(self, store):
		"""There is no second factor. A caller either names a configured
		participant or does not; nothing further is presented or validated."""
		store.send("hq.lead", "acme.reviewer", kind="ruling", body=b"x")
		with pytest.raises(b6.BatonError, match="not declared in the config"):
			store.send("hq.ghost", "acme.reviewer", kind="ruling", body=b"x")
		with pytest.raises(b6.BatonError, match="not declared in the config"):
			store.claim("acme.nobody")

	def test_old_identity_config_is_rejected_not_ignored(self, tmp_path):
		"""A pre-8 config that still declares actors must fail closed. Silently
		accepting it would leave operators believing an actor binding is
		enforced when nothing enforces it."""
		for stale in ({"identity": "agent"},
		              {"identity": "singleton", "singleton_actor": "lead"},
		              {"singleton_actor": "lead"},
		              # named explicitly so generic unknown-field handling
		              # cannot silently become the only thing rejecting these
		              {"actor": "k"},
		              {"seed": "a" * 32},
		              {"actor": "k", "seed": "a" * 32}):
			cfg = make_config()
			cfg["participants"]["acme.reviewer"] = stale
			with pytest.raises(b6.BatonError, match="removed at protocol"):
				b6.validate_config(cfg)

	def test_body_xor_attach_exactly_one(self, store):
		with pytest.raises(b6.BatonError, match="exactly one"):
			store.send("acme.reviewer", "acme.implementer",
			           kind="question", body=b"x", attach={"root_id": "r", "path": "p"})
		with pytest.raises(b6.BatonError, match="exactly one"):
			store.send("acme.reviewer", "acme.implementer",
			           kind="question", body=None)
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO messages(id, from_participant, to_participant, kind, retention, "
					"created_ts, state) VALUES('nobody1', 'acme.reviewer', 'acme.implementer', "
					"'k', 'durable', 'now', 'pending')")
		finally:
			store._txn_rollback()

	def test_transient_body_cap(self, store):
		with pytest.raises(b6.BatonError, match="exceeds"):
			send_one(store, body=b"x" * (b6.TRANSIENT_BODY_MAX_BYTES + 1), retention="transient")


def _race_claim(config_path, results):
	try:
		with b6.open_instance(config_path) as st:
			claim = st.claim("acme.implementer")
			results.put(("won", claim["claim_id"]))
	except b6.BatonError as exc:
		results.put(("lost", exc.exit_code))


class TestClaimRace:
	def test_concurrent_claim_single_winner(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st)
		ctx = multiprocessing.get_context("spawn")
		results = ctx.Queue()
		procs = [ctx.Process(target=_race_claim, args=(instance, results)) for _ in range(8)]
		for p in procs:
			p.start()
		for p in procs:
			p.join(60)
		outcomes = [results.get(timeout=10) for _ in procs]
		wins = [o for o in outcomes if o[0] == "won"]
		losses = [o for o in outcomes if o[0] == "lost"]
		assert len(wins) == 1
		assert len(losses) == 7
		assert all(code in (b6.EXIT_NONE, b6.EXIT_RACE) for _, code in losses)

	def test_partial_unique_index_backstop(self, store):
		mid = send_one(store)
		store.claim("acme.implementer", message_id=mid)
		store._txn_begin("claim")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO claims(claim_id, message_id, participant, claimed_ts, state) "
					"VALUES(?, ?, 'acme.implementer', 'now', 'active')", (b6.new_id(), mid))
		finally:
			store._txn_rollback()


# ---------------------------------------------------------------------------
# reply / close / retry idempotence (T3, T4, T5)
# ---------------------------------------------------------------------------

class TestReplyClose:
	def test_reply_publishes_and_completes(self, store):
		mid = send_one(store, body=b"question?")
		claim = store.claim("acme.implementer")
		result = store.reply(claim["claim_id"], participant=claim["participant"],
		                     kind="answer", body=b"the answer", outcome="done")
		assert result["already_committed"] is False
		out = store.get_message(result["response_message_id"])
		assert out["to_participant"] == "acme.reviewer"
		assert out["state"] == "pending"
		assert out["responds_to"] == mid
		assert out["body"] == b"the answer"
		assert store.get_message(mid)["state"] == "completed"
		assert store.get_claim(claim["claim_id"])["state"] == "completed"

	def test_reply_retry_is_redelivery_not_recreation(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		first = store.reply(claim["claim_id"], participant=claim["participant"],
		                    kind="answer", body=b"same bytes", outcome="ok")
		retry = store.reply(claim["claim_id"], participant=claim["participant"],
		                    kind="answer", body=b"same bytes", outcome="ok")
		assert retry["already_committed"] is True
		assert retry["response_message_id"] == first["response_message_id"]
		count = store.conn.execute(
			"SELECT COUNT(*) FROM messages WHERE responds_to IS NOT NULL").fetchone()[0]
		assert count == 1

	def test_reply_retry_content_mismatch_fails_closed(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"],
		            kind="answer", body=b"committed", outcome="ok")
		with pytest.raises(b6.BatonError, match="content differs"):
			store.reply(claim["claim_id"], participant=claim["participant"],
			            kind="answer", body=b"different", outcome="ok")
		with pytest.raises(b6.BatonError, match="outcome differs"):
			store.reply(claim["claim_id"], participant=claim["participant"],
			            kind="answer", body=b"committed", outcome="changed")
		with pytest.raises(b6.BatonError, match="mismatches"):
			store.close_claim(claim["claim_id"], participant=claim["participant"], outcome="ok")

	def test_failed_reply_leaves_nothing(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="not declared"):
			store.reply(claim["claim_id"], participant=claim["participant"],
			            kind="answer", body=b"x", recipient="acme.ghost")
		assert store.get_message(mid)["state"] == "claimed"
		assert store._existing_disposition(claim["claim_id"]) is None
		result = store.reply(claim["claim_id"], participant=claim["participant"],
		                     kind="answer", body=b"x")
		assert result["already_committed"] is False

	def test_reply_wrong_owner_refused(self, store):
		"""Only the participant that holds the claim may dispose of it. Under
		protocol 8 that is the whole of ownership: there is no credential to
		present in place of being the recipient."""
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="belongs to"):
			store.reply(claim["claim_id"], participant="acme.reviewer",
			            kind="answer", body=b"x")
		with pytest.raises(b6.BatonError, match="belongs to"):
			store.close_claim(claim["claim_id"], participant="hq.lead")
		# the true owner still can
		assert store.reply(claim["claim_id"], participant="acme.implementer",
		                   kind="answer", body=b"x")["already_committed"] is False
		# ...and the refusal survives the commit. A retry is where an ownership
		# check is most likely to be skipped, because the disposition already
		# exists and the code is looking for idempotence rather than authority.
		with pytest.raises(b6.BatonError, match="belongs to"):
			store.reply(claim["claim_id"], participant="acme.reviewer",
			            kind="answer", body=b"x")
		with pytest.raises(b6.BatonError, match="belongs to"):
			store.close_claim(claim["claim_id"], participant="acme.reviewer")
		# the owner's exact retry still redelivers the committed disposition
		assert store.reply(claim["claim_id"], participant="acme.implementer",
		                   kind="answer", body=b"x")["already_committed"] is True

	def test_close_ownership_enforced_on_first_and_retry(self, store):
		"""The close seam has its own ownership check; a test of reply alone
		would not catch a divergence between them."""
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="belongs to"):
			store.close_claim(claim["claim_id"], participant="acme.reviewer")
		store.close_claim(claim["claim_id"], participant="acme.implementer")
		with pytest.raises(b6.BatonError, match="belongs to"):
			store.close_claim(claim["claim_id"], participant="acme.reviewer")
		assert store.close_claim(claim["claim_id"],
		                         participant="acme.implementer")["already_committed"] is True

	def test_close_with_outcome_and_body(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer")
		result = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                           body=b"final signoff", outcome="signed_off")
		assert result["already_committed"] is False
		assert store.get_message(mid)["state"] == "closed"
		retry = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                          body=b"final signoff", outcome="signed_off")
		assert retry["already_committed"] is True

	def test_bodyless_close(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		assert store.get_message(mid)["state"] == "closed"

	def test_second_disposition_blocked_by_constraint(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"], outcome="ok")
		store._txn_begin("close")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO dispositions(claim_id, kind, outcome, created_ts) "
					"VALUES(?, 'close', 'dup', 'now')", (claim["claim_id"],))
		finally:
			store._txn_rollback()


# ---------------------------------------------------------------------------
# transient retention (T16) and per-owner content (T17)
# ---------------------------------------------------------------------------

class TestRetentionContent:
	def test_transient_scrub_in_consuming_txn(self, store):
		mid = send_one(store, body=b"ephemeral", retention="transient")
		sha = store.get_message(mid)["content_sha256"]
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"], outcome="seen")
		msg = store.get_message(mid)
		assert msg["content_id"] is None
		assert msg["body"] is None
		assert msg["content_sha256"] == sha
		assert msg["state"] == "closed"

	def test_durable_body_retained(self, store):
		mid = send_one(store, body=b"the record", retention="durable")
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		assert store.get_message(mid)["body"] == b"the record"

	def test_per_owner_content_rows_no_dedup(self, store):
		send_one(store, body=b"identical bytes", retention="transient")
		mid2 = send_one(store, body=b"identical bytes", retention="durable")
		count = store.conn.execute(
			"SELECT COUNT(*) FROM contents WHERE sha256=?",
			(store.get_message(mid2)["content_sha256"],)).fetchone()[0]
		assert count == 2
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		assert store.get_message(mid2)["body"] == b"identical bytes"

	def test_contents_immutable(self, store):
		send_one(store)
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="immutable"):
				store.conn.execute("UPDATE contents SET body=X'00'")
		finally:
			store._txn_rollback()

	def test_content_delete_needs_authorized_verb(self, store):
		send_one(store)
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="retention"):
				store.conn.execute("DELETE FROM contents")
		finally:
			store._txn_rollback()


# ---------------------------------------------------------------------------
# ledger + attribution + state graph (T2-core, T6, T18, T25)
# ---------------------------------------------------------------------------

class TestLedger:
	def test_birth_and_transition_events(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		rows = store.conn.execute(
			"SELECT entity, entity_id, from_state, to_state, verb, participant FROM transitions ORDER BY seq").fetchall()
		events = [(r["entity"], r["from_state"], r["to_state"], r["verb"]) for r in rows]
		assert ("message", None, "pending", "send") in events
		assert ("claim", None, "active", "claim") in events
		assert ("message", "pending", "claimed", "claim") in events
		assert ("message", "claimed", "completed", "reply") in events
		assert ("claim", "active", "completed", "reply") in events
		assert ("message", None, "pending", "reply") in events  # outgoing birth
		assert all(r["participant"] in ("acme.reviewer", "acme.implementer") for r in rows)

	def test_uncontextual_mutation_fails_closed(self, store):
		mid = send_one(store)
		with pytest.raises(sqlite3.IntegrityError, match="uncontextual|context"):
			store.conn.execute("UPDATE messages SET state='claimed' WHERE id=?", (mid,))
		with pytest.raises(sqlite3.IntegrityError, match="context"):
			store.conn.execute(
				"INSERT INTO messages(id, from_participant, to_participant, kind, retention, "
				"created_ts, state) VALUES('x', 'a.b', 'c.d', 'k', 'durable', 'now', 'pending')")

	def test_context_bearing_direct_sql_is_logged(self, store):
		mid = send_one(store)
		store._txn_begin("claim", participant="acme.implementer")
		try:
			store.conn.execute(
				"INSERT INTO claims(claim_id, message_id, participant, claimed_ts, state) "
				"VALUES('deadbeef', ?, 'acme.implementer', 'now', 'active')", (mid,))
			store._txn_commit()
		except BaseException:
			store._txn_rollback()
			raise
		row = store.conn.execute(
			"SELECT participant, verb FROM transitions WHERE entity='claim' AND entity_id='deadbeef'").fetchone()
		assert row["participant"] == "acme.implementer"
		assert row["verb"] == "claim"

	def test_illegal_state_edge_aborts(self, store):
		mid = send_one(store)
		store._txn_begin("claim")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="illegal message state edge"):
				store.conn.execute("UPDATE messages SET state='completed' WHERE id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_ledger_append_only(self, store):
		send_one(store)
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="append-only"):
				store.conn.execute("DELETE FROM transitions")
			with pytest.raises(sqlite3.IntegrityError, match="append-only"):
				store.conn.execute("UPDATE transitions SET participant='hq.forged'")
		finally:
			store._txn_rollback()

	def test_claim_history_immutable_columns(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store._txn_begin("claim")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="immutable claim column"):
				store.conn.execute("UPDATE claims SET participant='hq.lead' WHERE claim_id=?",
				                   (claim["claim_id"],))
		finally:
			store._txn_rollback()


# ---------------------------------------------------------------------------
# writer serialization (T9)
# ---------------------------------------------------------------------------

class TestBusy:
	def test_second_writer_gets_bounded_busy(self, instance, monkeypatch):
		monkeypatch.setattr(b6, "BUSY_TIMEOUT_MS", 200)
		with b6.open_instance(instance) as st1, b6.open_instance(instance) as st2:
			st1._txn_begin("send")
			try:
				with pytest.raises(b6.BatonError) as excinfo:
					st2.send("acme.reviewer", "acme.implementer", kind="question", body=b"x")
				assert excinfo.value.exit_code == b6.EXIT_RACE
			finally:
				st1._txn_rollback()


# ---------------------------------------------------------------------------
# extraction purity (T26 partial: grep sweep)
# ---------------------------------------------------------------------------

class TestExtractionPurity:
	def test_no_host_project_references(self):
		source = open(os.path.join(os.path.dirname(__file__), "baton_v6.py")).read()
		for banned in ("dri" + "ft", "wo" + "rk/", "fin" + "ding-", "AGE" + "NTS"):
			assert banned not in source, f"host-project reference {banned!r} in reusable module"


# ---------------------------------------------------------------------------
# Review round 1 fixes: transaction-time gates, stranded txn, transient close,
# scrub/timestamp guards, crash-atomic init, retry thread pin, retention override
# ---------------------------------------------------------------------------

class TestTxnTimeGates:
	def test_stale_open_writer_blocked_by_maintenance(self, instance):
		with b6.open_instance(instance) as a:
			b6.maintenance_enter(instance, participant="hq.lead",
			                     reason="gate test")
			with pytest.raises(b6.BatonError) as excinfo:
				send_one(a)
			assert excinfo.value.exit_code == b6.EXIT_GATED
			assert not a.conn.in_transaction

	def test_stale_open_writer_blocked_by_move(self, instance, tmp_path):
		dest = tmp_path / "dest"
		dest.mkdir()
		dest_config = str(dest / "baton.json")
		with b6.open_instance(instance) as a:
			token = b6.maintenance_enter(instance, participant="hq.lead", reason="moving", move=True,
			                             destination=dest_config)["move_token"]
			b6.move_copy(instance, participant="hq.lead")
			b6.move_bind_destination(dest_config, participant="hq.lead", token=token)
			b6.move_activate(dest_config, participant="hq.lead",
			                 token=token)
			b6.move_decommission(instance, participant="hq.lead",
			                     token=token, moved_to=dest_config)
			with pytest.raises(b6.BatonError) as excinfo:
				send_one(a)
			assert excinfo.value.exit_code == b6.EXIT_GATED

	def test_raw_gate_mutation_is_corruption_negative(self, store):
		with pytest.raises(sqlite3.IntegrityError, match="authorized ceremony"):
			store.conn.execute("UPDATE instance_meta SET maintenance=1 WHERE one_row=1")
		with pytest.raises(sqlite3.IntegrityError, match="immutable"):
			store.conn.execute("UPDATE instance_meta SET uuid='forged' WHERE one_row=1")
		with pytest.raises(sqlite3.IntegrityError, match="regen/migrate"):
			store.conn.execute("UPDATE instance_meta SET accepted_generation=9 WHERE one_row=1")
		store._txn_begin("move", ceremony=None)
		try:
			with pytest.raises(sqlite3.IntegrityError, match="illegal move_status edge"):
				store.conn.execute(
					"UPDATE instance_meta SET maintenance=1, move_status='moved', "
					"move_token='t', move_role='source', move_peer='/x', moved_to='/x' "
					"WHERE one_row=1")
		finally:
			store._txn_rollback()

	def test_stale_open_writer_blocked_after_regen(self, instance, tmp_path):
		a = b6.open_instance(instance)
		try:
			with open(instance, "w") as handle:
				json.dump(make_config(generation=2), handle)
			b6.regen_instance(instance, participant="hq.lead")
			with pytest.raises(b6.BatonError, match="stale"):
				send_one(a)
		finally:
			a.close()
		with b6.open_instance(instance) as fresh:
			send_one(fresh)

	def test_regen_generation_must_be_exactly_next(self, instance):
		with open(instance, "w") as handle:
			json.dump(make_config(generation=3), handle)
		with pytest.raises(b6.BatonError, match="regen requires config generation 2"):
			b6.regen_instance(instance, participant="hq.lead")


class TestTxnStrand:
	def test_begin_failure_never_strands_transaction(self, store):
		store.conn.execute(
			"CREATE TEMP TRIGGER break_ctx BEFORE UPDATE ON op_context "
			"BEGIN SELECT RAISE(ABORT, 'break'); END")
		try:
			with pytest.raises(b6.BatonError):
				send_one(store)
			assert not store.conn.in_transaction
		finally:
			store.conn.execute("DROP TRIGGER break_ctx")
		mid = send_one(store)
		assert store.get_message(mid)["state"] == "pending"
		assert store.conn.execute(
			"SELECT op_id FROM op_context WHERE one_row=1").fetchone()[0] is None


class TestTransientClose:
	def test_transient_close_retains_identity_not_bytes(self, store):
		send_one(store, body=b"incoming", retention="transient")
		claim = store.claim("acme.implementer")
		body = b"should be transient"
		result = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                           body=body, outcome="noted")
		import hashlib
		sha = hashlib.sha256(body).hexdigest()
		assert result["content_sha256"] == sha
		count = store.conn.execute(
			"SELECT COUNT(*) FROM contents WHERE sha256=?", (sha,)).fetchone()[0]
		assert count == 0
		disp = store.conn.execute(
			"SELECT content_id, content_sha256 FROM dispositions WHERE claim_id=?",
			(claim["claim_id"],)).fetchone()
		assert disp["content_id"] is None
		assert disp["content_sha256"] == sha
		retry = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                          body=body, outcome="noted")
		assert retry["already_committed"] is True
		with pytest.raises(b6.BatonError, match="content differs"):
			store.close_claim(claim["claim_id"], participant=claim["participant"],
			                  body=b"other", outcome="noted")

	def test_transient_close_body_cap(self, store):
		send_one(store, body=b"x", retention="transient")
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="exceeds"):
			store.close_claim(claim["claim_id"], participant=claim["participant"],
			                  body=b"y" * (b6.TRANSIENT_BODY_MAX_BYTES + 1))

	def test_durable_close_retains_body(self, store):
		send_one(store, body=b"incoming", retention="durable")
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"], body=b"kept record")
		row = store.conn.execute(
			"SELECT c.body FROM dispositions d JOIN contents c ON c.content_id=d.content_id "
			"WHERE d.claim_id=?", (claim["claim_id"],)).fetchone()
		assert row["body"] == b"kept record"


class TestScrubAndTimestampGuards:
	def test_uncontextual_scrub_rejected(self, store):
		mid = send_one(store, body=b"x", retention="transient")
		with pytest.raises(sqlite3.IntegrityError, match="consuming operation"):
			store.conn.execute("UPDATE messages SET content_id=NULL WHERE id=?", (mid,))

	def test_wrong_verb_scrub_rejected(self, store):
		mid = send_one(store, body=b"x", retention="transient")
		store._txn_begin("claim")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="consuming operation"):
				store.conn.execute("UPDATE messages SET content_id=NULL WHERE id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_uncontextual_timestamp_rewrites_rejected(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		with pytest.raises(sqlite3.IntegrityError, match="completed_ts"):
			store.conn.execute("UPDATE messages SET completed_ts='1999-01-01T00:00:00Z' WHERE id=?", (mid,))
		with pytest.raises(sqlite3.IntegrityError, match="terminal_ts"):
			store.conn.execute("UPDATE claims SET terminal_ts='1999-01-01T00:00:00Z' WHERE claim_id=?",
			                   (claim["claim_id"],))


class TestCrashAtomicInit:
	def test_final_db_mode_is_private(self, instance, tmp_path):
		mode = os.stat(tmp_path / "mailbox.sqlite3").st_mode & 0o777
		assert mode == 0o600

	def test_stale_scratch_does_not_block_init(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		(tmp_path / ".init-deadbeef.sqlite3").write_bytes(b"stale scratch")
		b6.init_instance(config_path)
		assert (tmp_path / "mailbox.sqlite3").is_file()
		assert (tmp_path / ".init-deadbeef.sqlite3").is_file()  # doctor's, not ours

	def test_partial_final_refused_scratch_cleaned(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		(tmp_path / "mailbox.sqlite3").write_bytes(b"partial garbage")
		with pytest.raises(b6.BatonError, match="refusing to initialize"):
			b6.init_instance(config_path)
		leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".init-")]
		assert leftovers == []


class TestRetryRouting:
	def test_retry_thread_mismatch_fails_closed(self, store):
		send_one(store, thread="topic-1")
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
		            body=b"x", thread_id="topic-1")
		with pytest.raises(b6.BatonError, match="thread differs"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
			            body=b"x", thread_id="topic-2")

	def test_retry_recipient_and_kind_mismatch(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		with pytest.raises(b6.BatonError, match="kind differs"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="other", body=b"x")
		with pytest.raises(b6.BatonError, match="recipient differs"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
			            body=b"x", recipient="hq.lead")


class TestRetentionOverride:
	def test_response_inherits_by_default(self, store):
		send_one(store, retention="transient")
		claim = store.claim("acme.implementer")
		result = store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"r")
		assert store.get_message(result["response_message_id"])["retention"] == "transient"

	def test_explicit_override_preserved_from_v5(self, store):
		send_one(store, retention="transient")
		claim = store.claim("acme.implementer")
		result = store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
		                     body=b"r", retention="durable")
		assert store.get_message(result["response_message_id"])["retention"] == "durable"
		with pytest.raises(b6.BatonError, match="invalid retention"):
			send_one(store)
			claim2 = store.claim("acme.implementer")
			store.reply(claim2["claim_id"], participant=claim2["participant"], kind="answer",
			            body=b"r", retention="forever")


# ---------------------------------------------------------------------------
# Handoff 2: notices (T12), recovery (T2, T11), gc (T16), attachments, regen
# ---------------------------------------------------------------------------

class TestNotices:
	def test_see_marks_and_dedupes(self, store):
		nid = store.send_notice("hq.lead", kind="announcement",
		                        body=b"all hands")
		seen = store.see("acme.implementer")
		assert [n["id"] for n in seen] == [nid]
		assert seen[0]["body"] == b"all hands"
		assert store.see("acme.implementer") == []
		other = store.see("acme.reviewer")
		assert [n["id"] for n in other] == [nid]

	def test_author_early_expire_single_txn(self, store):
		nid = store.send_notice("hq.lead", kind="announcement",
		                        body=b"oops")
		store.see("acme.implementer")
		with pytest.raises(b6.BatonError, match="not its exact authoring participant"):
			store.expire("acme.implementer", notice_id=nid)
		removed = store.expire("hq.lead", notice_id=nid)
		assert removed == [nid]
		assert store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 0
		assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
		assert store.conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0] == 0

	def test_ttl_sweep(self, store):
		import time
		store.send_notice("hq.lead", kind="tick",
		                  body=b"short", ttl_seconds=1)
		keep = store.send_notice("hq.lead", kind="keep", body=b"long")
		time.sleep(1.1)
		removed = store.expire("hq.lead")
		assert len(removed) == 1
		remaining = [r[0] for r in store.conn.execute("SELECT id FROM notices")]
		assert remaining == [keep]


class TestRecovery:
	def test_recover_then_reclaim_preserves_history(self, store):
		mid = send_one(store)
		claim1 = store.claim("acme.implementer")
		result = store.recover_claim(claim1["claim_id"], participant="hq.lead",
		                             reason="imp1 host died")
		assert result["message_id"] == mid
		assert store.get_message(mid)["state"] == "pending"
		old = store.get_claim(claim1["claim_id"])
		assert old["state"] == "recovered"
		assert old["participant"] == "acme.implementer"
		claim2 = store.claim("acme.implementer")
		assert claim2["claim_id"] != claim1["claim_id"]
		assert claim2["message_id"] == mid
		audits = store.conn.execute(
			"SELECT claim_id, participant, reason FROM recoveries").fetchall()
		assert len(audits) == 1
		assert audits[0]["claim_id"] == claim1["claim_id"]
		assert audits[0]["reason"] == "imp1 host died"

	def test_recovery_requires_reason(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="reason"):
			store.recover_claim(claim["claim_id"], participant="hq.lead", reason="  ")

	def test_recovered_claim_cannot_reply(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store.recover_claim(claim["claim_id"], participant="hq.lead", reason="dead")
		with pytest.raises(b6.BatonError, match="recovered"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"late")

	def test_recover_inactive_claim_refused(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		with pytest.raises(b6.BatonError, match="not active"):
			store.recover_claim(claim["claim_id"], participant="hq.lead", reason="x")


class TestGc:
	def _consume_transient(self, store):
		mid = send_one(store, body=b"old news", retention="transient")
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		return mid

	def test_gc_removes_aged_transient_with_ledger_events(self, store):
		mid = self._consume_transient(store)
		future = "2027-01-01T00:00:00Z"
		result = store.gc(participant="hq.lead", now=future)
		assert mid in result["messages"]
		assert store.conn.execute(
			"SELECT COUNT(*) FROM messages WHERE id=?", (mid,)).fetchone()[0] == 0
		events = store.conn.execute(
			"SELECT entity, to_state, verb FROM transitions WHERE entity_id=? AND to_state='gc'",
			(mid,)).fetchall()
		assert len(events) == 1
		assert events[0]["verb"] == "gc"
		assert store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] > 0

	def test_gc_spares_recent_durable_and_recovered(self, store):
		durable_mid = send_one(store, body=b"keep me", retention="durable")
		recent_mid = self._consume_transient(store)
		rec_mid = send_one(store, body=b"rec", retention="transient")
		claim = store.claim("acme.implementer", message_id=rec_mid)
		store.recover_claim(claim["claim_id"], participant="hq.lead", reason="dead")
		claim2 = store.claim("acme.implementer", message_id=rec_mid)
		store.close_claim(claim2["claim_id"], participant=claim2["participant"])
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert recent_mid in result["messages"]
		assert rec_mid not in result["messages"]  # recovery-referenced audit chain preserved
		assert durable_mid not in result["messages"]
		result2 = store.gc(participant="hq.lead")  # real now: nothing aged
		assert result2["messages"] == []

	def test_gc_permanent_ledger_and_recoveries(self, store):
		self._consume_transient(store)
		before = store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
		store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		after = store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
		assert after > before  # gc appended events, deleted none


class TestAttachments:
	@pytest.fixture
	def rooted(self, tmp_path):
		root = tmp_path / "evidence"
		(root / "sub").mkdir(parents=True)
		(root / "sub" / "report.md").write_bytes(b"evidence bytes")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		st = b6.open_instance(config_path)
		yield st, root
		st.close()

	def test_attachment_pinned_and_claimable(self, rooted):
		store, root = rooted
		mid = store.send("acme.reviewer", "acme.implementer",
		                 kind="evidence", body=None,
		                 attach={"root_id": "evidence", "path": "sub/report.md"})
		msg = store.get_message(mid)
		assert msg["attach_sha256"] is not None
		claim = store.claim("acme.implementer")
		assert claim["message_id"] == mid

	def test_post_publication_mutation_fails_at_claim(self, rooted):
		"""Tampered content is never delivered. Since the skip-and-continue
		contract, a PLAIN claim reports nothing deliverable (so one damaged
		message cannot block the queue) while an EXPLICITLY named target still
		fails closed with the damage diagnostic. Both halves asserted: the
		guarded property is that the tampered bytes never reach a consumer."""
		store, root = rooted
		mid = store.send("acme.reviewer", "acme.implementer",
		                 kind="evidence", body=None,
		                 attach={"root_id": "evidence", "path": "sub/report.md"})
		(root / "sub" / "report.md").write_bytes(b"tampered")
		with pytest.raises(b6.BatonError, match="pinned hash") as excinfo:
			store.claim("acme.implementer", message_id=mid)
		assert excinfo.value.exit_code == b6.EXIT_DAMAGE
		with pytest.raises(b6.BatonError) as excinfo:
			store.claim("acme.implementer")
		assert excinfo.value.exit_code == b6.EXIT_NONE
		assert "damaged attachments" in str(excinfo.value)
		assert store.get_message(mid)["state"] == "pending"
		assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0

	def test_containment_and_symlink_refusal(self, rooted, tmp_path):
		store, root = rooted
		outside = tmp_path / "outside.md"
		outside.write_bytes(b"outside")
		os.symlink(outside, root / "escape.md")
		with pytest.raises(b6.BatonError, match="symlink"):
			store.send("acme.reviewer", "acme.implementer",
			           kind="evidence", body=None,
			           attach={"root_id": "evidence", "path": "escape.md"})
		for bad in ("../outside.md", "/etc/passwd", "sub/../../x", ""):
			with pytest.raises(b6.BatonError):
				store.send("acme.reviewer", "acme.implementer",
				           kind="evidence", body=None,
				           attach={"root_id": "evidence", "path": bad})

	def test_undeclared_root_refused(self, rooted):
		store, root = rooted
		with pytest.raises(b6.BatonError, match="not declared"):
			store.send("acme.reviewer", "acme.implementer",
			           kind="evidence", body=None,
			           attach={"root_id": "ghost", "path": "x.md"})


# ---------------------------------------------------------------------------
# Review round 2 pins: disposition retention, notice authorship, recovery
# authority, regen live-state guards, state-coupled triggers, init fault
# matrix, attachment snapshot, root validation
# ---------------------------------------------------------------------------

class TestDispositionRetention:
	def test_reply_retry_retention_mismatch_fails_closed(self, store):
		send_one(store, retention="durable")
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		with pytest.raises(b6.BatonError, match="retention differs"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
			            body=b"x", retention="transient")
		retry = store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		assert retry["already_committed"] is True
		assert retry["retention"] == "durable"

	def test_close_override_transient_to_durable_retains_body(self, store):
		send_one(store, retention="transient")
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"],
		                  body=b"promoted record", retention="durable")
		row = store.conn.execute(
			"SELECT c.body FROM dispositions d JOIN contents c ON c.content_id=d.content_id "
			"WHERE d.claim_id=?", (claim["claim_id"],)).fetchone()
		assert row["body"] == b"promoted record"

	def test_close_override_durable_to_transient_drops_body(self, store):
		send_one(store, retention="durable")
		claim = store.claim("acme.implementer")
		result = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                           body=b"ephemeral note", retention="transient")
		count = store.conn.execute(
			"SELECT COUNT(*) FROM contents WHERE sha256=?", (result["content_sha256"],)).fetchone()[0]
		assert count == 0
		with pytest.raises(b6.BatonError, match="retention differs"):
			store.close_claim(claim["claim_id"], participant=claim["participant"],
			                  body=b"ephemeral note", retention="durable")
		retry = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                          body=b"ephemeral note", retention="transient")
		assert retry["already_committed"] is True

	def test_close_invalid_retention(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="invalid retention"):
			store.close_claim(claim["claim_id"], participant=claim["participant"],
			                  body=b"x", retention="forever")


class TestNoticeAuthorship:
	def test_only_the_authoring_participant_may_expire_early(self, store):
		"""Authorship is the participant. Any other participant is refused;
		the author itself succeeds."""
		nid = store.send_notice("acme.reviewer", kind="announcement", body=b"mine")
		for other in ("acme.implementer", "hq.lead"):
			with pytest.raises(b6.BatonError, match="exact authoring participant"):
				store.expire(other, notice_id=nid)
		removed = store.expire("acme.reviewer", notice_id=nid)
		assert removed == [nid]

	def test_ttl_default_finite(self, store):
		nid = store.send_notice("hq.lead", kind="note", body=b"x")
		ttl = store.conn.execute("SELECT ttl_seconds FROM notices WHERE id=?", (nid,)).fetchone()[0]
		assert ttl == b6.DEFAULT_NOTICE_TTL_SECONDS
		with pytest.raises(b6.BatonError, match="positive"):
			store.send_notice("hq.lead", kind="note",
			                  body=b"x", ttl_seconds=0)
		with pytest.raises(sqlite3.IntegrityError):
			store._txn_begin("send")
			try:
				store.conn.execute(
					"INSERT INTO notices(id, from_participant, kind, "
					"content_sha256, created_ts, ttl_seconds) "
					"VALUES('immortal', 'hq.lead', 'k', 'sha', 'now', 0)")
			finally:
				store._txn_rollback()

	def test_notice_immutability_and_context(self, store):
		nid = store.send_notice("hq.lead", kind="note", body=b"x")
		with pytest.raises(sqlite3.IntegrityError, match="immutable"):
			store.conn.execute("UPDATE notices SET from_participant='hq.forged' WHERE id=?", (nid,))
		with pytest.raises(sqlite3.IntegrityError, match="context"):
			store.conn.execute(
				"INSERT INTO notices(id, from_participant, kind, "
				"content_sha256, created_ts, ttl_seconds) "
				"VALUES('raw', 'hq.lead', 'k', 'sha', 'now', 60)")
		with pytest.raises(sqlite3.IntegrityError, match="context"):
			store.conn.execute(
				"INSERT INTO notice_seen(notice_id, participant, seen_ts) "
				"VALUES(?, 'acme.reviewer', 'now')", (nid,))


class TestRecoveryAuthority:
	def test_unconfigured_participant_refused(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="not declared"):
			store.recover_claim(claim["claim_id"], participant="ghost.admin",
			                    reason="x")

	def test_participant_without_capability_refused(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="'recovery' capability"):
			store.recover_claim(claim["claim_id"], participant="acme.reviewer",
			                    reason="x")

	def test_recovery_still_requires_the_capability(self, store):
		"""Recovery authority is an explicit capability, unchanged by the
		identity simplification — it is not inferred from being a
		participant."""
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="recovery"):
			store.recover_claim(claim["claim_id"], participant="acme.reviewer",
			                    reason="x")
		result = store.recover_claim(claim["claim_id"], participant="hq.lead",
		                             reason="host died")
		assert result["claim_id"] == claim["claim_id"]

	def test_agent_with_declared_capability_allowed(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["participants"]["acme.oncall"] = {"capabilities": ["recovery"]}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			send_one(st)
			claim = st.claim("acme.implementer")
			st.recover_claim(claim["claim_id"], participant="acme.oncall",
			                 reason="authority is a capability")

	def test_unknown_capability_rejected_in_config(self):
		cfg = make_config()
		cfg["participants"]["acme.reviewer"]["capabilities"] = ["sudo"]
		with pytest.raises(b6.BatonError, match="unknown capabilities"):
			b6.validate_config(cfg)

	def test_audit_row_carries_full_identity(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store.recover_claim(claim["claim_id"], participant="hq.lead", reason="host died")
		row = store.conn.execute("SELECT participant FROM recoveries").fetchone()
		assert row["participant"] == "hq.lead"
		ledger = store.conn.execute(
			"SELECT participant FROM transitions WHERE verb='recover' AND entity='claim'").fetchone()
		assert ledger["participant"] == "hq.lead"

	def test_regen_requires_config_capability(self, instance):
		with open(instance, "w") as handle:
			json.dump(make_config(generation=2), handle)
		with pytest.raises(b6.BatonError, match="'config' capability"):
			b6.regen_instance(instance, participant="acme.reviewer")

	def test_gc_requires_configured_participant(self, store):
		with pytest.raises(b6.BatonError, match="not declared"):
			store.gc(participant="ghost.admin")


class TestRegenLiveState:
	def test_participant_removal_refused_while_live(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st)  # pending message to acme.implementer
		cfg = make_config(generation=2)
		del cfg["participants"]["acme.implementer"]
		with open(instance, "w") as handle:
			json.dump(cfg, handle)
		with pytest.raises(b6.BatonError, match="named by live"):
			b6.regen_instance(instance, participant="hq.lead")

	def test_additive_change_accepted(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st)
		cfg = make_config(generation=2)
		cfg["participants"]["acme.newcomer"] = {}
		with open(instance, "w") as handle:
			json.dump(cfg, handle)
		result = b6.regen_instance(instance, participant="hq.lead")
		assert result["accepted_generation"] == 2

	def test_attachment_root_remap_refused(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		(root / "e.md").write_bytes(b"evidence")
		other = tmp_path / "other"
		other.mkdir()
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			mid = st.send("acme.reviewer", "acme.implementer",
			              kind="evidence", body=None, attach={"root_id": "evidence", "path": "e.md"})
			claim = st.claim("acme.implementer", message_id=mid)
			st.close_claim(claim["claim_id"], participant=claim["participant"])  # durable, retained
		cfg2 = make_config(generation=2)
		cfg2["roots"] = {"evidence": str(other)}
		with open(config_path, "w") as handle:
			json.dump(cfg2, handle)
		with pytest.raises(b6.BatonError, match="keep its accepted mapping"):
			b6.regen_instance(config_path, participant="hq.lead")
		cfg3 = make_config(generation=2)
		cfg3["roots"] = {"evidence": str(root), "extra": str(other)}
		with open(config_path, "w") as handle:
			json.dump(cfg3, handle)
		result = b6.regen_instance(config_path, participant="hq.lead")
		assert result["accepted_generation"] == 2

	def test_regen_exact_next_race(self, instance):
		with open(instance, "w") as handle:
			json.dump(make_config(generation=2), handle)
		b6.regen_instance(instance, participant="hq.lead")
		with pytest.raises(b6.BatonError, match="regen requires config generation 3"):
			b6.regen_instance(instance, participant="hq.lead")


class TestStateCoupledTriggers:
	def test_context_bearing_wrong_row_timestamp_rejected(self, store):
		mid = send_one(store)  # pending
		store._txn_begin("reply")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="terminal transition"):
				store.conn.execute(
					"UPDATE messages SET completed_ts='1999-01-01T00:00:00Z' WHERE id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_context_bearing_pending_scrub_rejected(self, store):
		mid = send_one(store, retention="transient")  # pending transient
		store._txn_begin("reply")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="terminal transient"):
				store.conn.execute("UPDATE messages SET content_id=NULL WHERE id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_durable_terminal_scrub_rejected(self, store):
		mid = send_one(store, retention="durable")
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		store._txn_begin("close")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="terminal transient"):
				store.conn.execute("UPDATE messages SET content_id=NULL WHERE id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_terminal_ts_without_edge_rejected(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store._txn_begin("reply")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="terminal transition"):
				store.conn.execute(
					"UPDATE claims SET terminal_ts='1999-01-01T00:00:00Z' WHERE claim_id=?",
					(claim["claim_id"],))
		finally:
			store._txn_rollback()


def _init_with_fault(config_path, point, queue):
	import baton_v6 as mod
	def hook(p):
		if p == point:
			os._exit(9)
	mod._FAULT_HOOK = hook
	try:
		mod.init_instance(config_path)
		queue.put("completed")
	except mod.BatonError as exc:
		queue.put(f"error:{exc}")


class TestInitFaultMatrix:
	POINTS = ["init:post-commit", "init:post-checkpoint", "init:pre-link",
	          "init:post-link", "init:post-unlink"]

	@pytest.mark.parametrize("point", POINTS)
	def test_kill_at_boundary_leaves_absent_or_valid(self, tmp_path, point):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		ctx = multiprocessing.get_context("spawn")
		queue = ctx.Queue()
		proc = ctx.Process(target=_init_with_fault, args=(config_path, point, queue))
		proc.start()
		proc.join(60)
		assert proc.exitcode == 9
		final = tmp_path / "mailbox.sqlite3"
		if final.exists():
			with b6.open_instance(config_path) as st:  # fully valid or open would fail closed
				st.conn.execute("SELECT 1 FROM instance_meta").fetchone()
			with pytest.raises(b6.BatonError, match="refusing to initialize"):
				b6.init_instance(config_path)
		else:
			b6.init_instance(config_path)  # retry-safe
			with b6.open_instance(config_path) as st:
				st.conn.execute("SELECT 1 FROM instance_meta").fetchone()
		scratch = [p.name for p in tmp_path.iterdir() if p.name.startswith(".init-")]
		assert all(name.startswith(".init-") for name in scratch)  # recognizable, never partial finals


class TestAttachmentSnapshot:
	def test_mid_hash_mutation_refused(self, tmp_path, monkeypatch):
		root = tmp_path / "evidence"
		root.mkdir()
		target = root / "e.md"
		target.write_bytes(b"original")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		def mutate(point):
			if point == "attach:post-hash":
				target.write_bytes(b"mutated mid-hash")
		monkeypatch.setattr(b6, "_FAULT_HOOK", mutate)
		with b6.open_instance(config_path) as st:
			with pytest.raises(b6.BatonError, match="changed while being hashed"):
				st.send("acme.reviewer", "acme.implementer",
				        kind="evidence", body=None, attach={"root_id": "evidence", "path": "e.md"})


class TestRootValidation:
	def test_non_canonical_root_refused(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"bad": str(tmp_path) + "/sub/../sub"}
		(tmp_path / "sub").mkdir()
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		with pytest.raises(b6.BatonError, match="canonical"):
			b6.init_instance(config_path)

	def test_symlink_root_refused(self, tmp_path):
		real = tmp_path / "real"
		real.mkdir()
		os.symlink(real, tmp_path / "link")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"linked": str(tmp_path / "link")}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		with pytest.raises(b6.BatonError, match="symlink"):
			b6.init_instance(config_path)

	def test_missing_root_fails_at_open(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		root.rmdir()
		with pytest.raises(b6.BatonError, match="openable directory"):
			b6.open_instance(config_path)


class TestRootBindingGenerations:
	@pytest.fixture
	def bound(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		(root / "e.md").write_bytes(b"evidence")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		return config_path, root, tmp_path

	def test_unrelated_regen_does_not_invalidate_attachments(self, bound):
		config_path, root, tmp_path = bound
		with b6.open_instance(config_path) as st:
			mid = st.send("acme.reviewer", "acme.implementer",
			              kind="evidence", body=None, attach={"root_id": "evidence", "path": "e.md"})
			assert st.get_message(mid)["attach_generation"] == 1
		cfg = make_config(generation=2)
		cfg["roots"] = {"evidence": str(root)}
		cfg["participants"]["acme.newcomer"] = {}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.regen_instance(config_path, participant="hq.lead")
		with b6.open_instance(config_path) as st:
			binding = st.conn.execute(
				"SELECT binding_generation FROM accepted_roots WHERE root_id='evidence'").fetchone()
			assert binding["binding_generation"] == 1  # unchanged root keeps its binding
			claim = st.claim("acme.implementer")  # still verifiable
			assert claim["message_id"] == mid

	def test_new_root_gets_current_generation(self, bound):
		config_path, root, tmp_path = bound
		extra = tmp_path / "extra"
		extra.mkdir()
		cfg = make_config(generation=2)
		cfg["roots"] = {"evidence": str(root), "extra": str(extra)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.regen_instance(config_path, participant="hq.lead")
		with b6.open_instance(config_path) as st:
			rows = {r["root_id"]: r["binding_generation"] for r in st.conn.execute(
				"SELECT root_id, binding_generation FROM accepted_roots")}
			assert rows == {"evidence": 1, "extra": 2}

	def test_binding_generation_mismatch_is_damage(self, bound):
		"""A root rebound under a different generation is damage, and is
		treated as such by both claim paths: explicit target fails closed with
		the diagnostic, plain claim skips it as undeliverable rather than
		delivering an attachment resolved through the wrong binding."""
		config_path, root, tmp_path = bound
		with b6.open_instance(config_path) as st:
			mid = st.send("acme.reviewer", "acme.implementer",
			              kind="evidence", body=None,
			              attach={"root_id": "evidence", "path": "e.md"})
		_raw_corrupt(config_path, lambda conn: conn.execute(
			"UPDATE accepted_roots SET binding_generation=9 WHERE root_id='evidence'"))
		with b6.open_instance(config_path) as st:
			with pytest.raises(b6.BatonError, match="binding generation") as excinfo:
				st.claim("acme.implementer", message_id=mid)
			assert excinfo.value.exit_code == b6.EXIT_DAMAGE
			with pytest.raises(b6.BatonError) as excinfo:
				st.claim("acme.implementer")
			assert excinfo.value.exit_code == b6.EXIT_NONE
			assert st.get_message(mid)["state"] == "pending"


# ---------------------------------------------------------------------------
# Review round 3 pins: effective-route retry, bidirectional CHECK coupling,
# GC reply chains, component-walk no-follow, seen/recovery guards, snapshot
# ---------------------------------------------------------------------------

class TestEffectiveRouteRetry:
	def test_first_explicit_retry_omitted_fails_closed(self, store):
		send_one(store, thread="t1")  # from acme.reviewer
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
		            body=b"x", recipient="hq.lead", thread_id="t2")
		with pytest.raises(b6.BatonError, match="recipient differs"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")

	def test_first_explicit_thread_retry_omitted_fails_closed(self, store):
		send_one(store, thread="t1")
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
		            body=b"x", thread_id="t2")
		with pytest.raises(b6.BatonError, match="thread differs"):
			store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")

	def test_first_default_retry_omitted_redelivers(self, store):
		send_one(store, thread="t1")
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		retry = store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		assert retry["already_committed"] is True

	def test_first_default_retry_explicit_same_redelivers(self, store):
		send_one(store, thread="t1")
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"], kind="answer", body=b"x")
		retry = store.reply(claim["claim_id"], participant=claim["participant"], kind="answer",
		                    body=b"x", recipient="acme.reviewer", thread_id="t1")
		assert retry["already_committed"] is True


class TestBidirectionalCoupling:
	def test_terminal_transition_without_timestamp_rejected(self, store):
		mid = send_one(store)
		store.claim("acme.implementer")
		store._txn_begin("reply")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute("UPDATE messages SET state='completed' WHERE id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_claim_terminal_without_timestamp_rejected(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		store._txn_begin("reply")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute("UPDATE claims SET state='completed' WHERE claim_id=?",
				                   (claim["claim_id"],))
		finally:
			store._txn_rollback()

	def test_prefilled_terminal_timestamp_birth_rejected(self, store):
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO messages(id, from_participant, to_participant, kind, retention, "
					"content_sha256, created_ts, state, completed_ts) "
					"VALUES('prefilled', 'acme.reviewer', 'acme.implementer', 'k', 'durable', "
					"'sha', 'now', 'pending', 'already')")
		finally:
			store._txn_rollback()


class TestGcReplyChains:
	def _chain(self, store, incoming_retention="transient", response_retention=None):
		mid_a = send_one(store, retention=incoming_retention)
		claim_a = store.claim("acme.implementer", message_id=mid_a)
		result = store.reply(claim_a["claim_id"], participant=claim_a["participant"], kind="answer",
		                     body=b"resp", retention=response_retention)
		mid_b = result["response_message_id"]
		claim_b = store.claim("acme.reviewer", message_id=mid_b)
		store.close_claim(claim_b["claim_id"], participant=claim_b["participant"])
		return mid_a, mid_b, claim_a["claim_id"]

	def test_all_transient_chain_collected(self, store):
		mid_a, mid_b, _ = self._chain(store)
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert set(result["messages"]) >= {mid_a, mid_b}
		remaining = store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
		assert remaining == 0

	def test_durable_incoming_anchors_transient_response(self, store):
		mid_a, mid_b, _ = self._chain(store, incoming_retention="durable",
		                              response_retention="transient")
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert mid_a not in result["messages"]
		assert mid_b not in result["messages"]  # retained disposition anchors its response metadata
		assert store.conn.execute(
			"SELECT COUNT(*) FROM messages WHERE id IN (?,?)", (mid_a, mid_b)).fetchone()[0] == 2

	def test_transient_incoming_anchored_by_durable_response(self, store):
		mid_a, mid_b, _ = self._chain(store, incoming_retention="transient",
		                              response_retention="durable")
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert mid_a not in result["messages"]  # retained child references its parent
		assert mid_b not in result["messages"]

	def test_gc_never_aborts_and_retry_after_gc_is_clean(self, store):
		mid_a, mid_b, claim_a = self._chain(store)
		ledger_before = store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert set(result["messages"]) >= {mid_a, mid_b}
		assert store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] > ledger_before
		with pytest.raises(b6.BatonError, match="unknown claim"):
			store.reply(claim_a, participant="acme.implementer", kind="answer", body=b"resp")
		again = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert again["messages"] == []


class TestComponentWalkNoFollow:
	def test_intermediate_symlink_root_refused(self, tmp_path):
		base = tmp_path / "base"
		base.mkdir()
		target = tmp_path / "target"
		(target / "leaf").mkdir(parents=True)
		os.symlink(target, base / "link")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"bad": str(base / "link" / "leaf")}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		with pytest.raises(b6.BatonError, match="symlink"):
			b6.init_instance(config_path)

	def test_intermediate_symlink_instance_dir_refused(self, tmp_path):
		real = tmp_path / "real"
		real.mkdir()
		os.symlink(real, tmp_path / "link")
		config_path = str(tmp_path / "link" / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		with pytest.raises(b6.BatonError, match="symlink"):
			b6.init_instance(config_path)


class TestSeenAndRecoveryGuards:
	def test_notice_seen_immutable_and_delete_guarded(self, store):
		nid = store.send_notice("hq.lead", kind="note", body=b"x")
		store.see("acme.implementer")
		with pytest.raises(sqlite3.IntegrityError, match="immutable"):
			store.conn.execute("UPDATE notice_seen SET participant='hq.forged'")
		with pytest.raises(sqlite3.IntegrityError, match="removable only"):
			store.conn.execute("DELETE FROM notice_seen")
		assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 1
		removed = store.expire("hq.lead", notice_id=nid)
		assert removed == [nid]
		assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0

	def test_uncontextual_recovery_row_rejected(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(sqlite3.IntegrityError, match="context"):
			store.conn.execute(
				"INSERT INTO recoveries(recovery_id, claim_id, participant, reason, "
				"created_ts) VALUES('forged', ?, 'ghost.admin', 'because', 'now')",
				(claim["claim_id"],))


class TestSnapshotHardening:
	def test_same_size_restored_mtime_mutation_refused(self, tmp_path, monkeypatch):
		root = tmp_path / "evidence"
		root.mkdir()
		target = root / "e.md"
		target.write_bytes(b"original")
		st = os.stat(target)
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		def mutate(point):
			if point == "attach:post-hash":
				target.write_bytes(b"mutated!")  # same size as b"original"
				os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns))
		monkeypatch.setattr(b6, "_FAULT_HOOK", mutate)
		with b6.open_instance(config_path) as store:
			with pytest.raises(b6.BatonError, match="changed while being hashed"):
				store.send("acme.reviewer", "acme.implementer",
				           kind="evidence", body=None, attach={"root_id": "evidence", "path": "e.md"})

	def test_fifo_attachment_rejected_without_hanging(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		os.mkfifo(root / "pipe")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		try:
			with b6.open_instance(config_path) as store:
				with pytest.raises(b6.BatonError, match="not a regular file"):
					store.send("acme.reviewer", "acme.implementer",
					           kind="evidence", body=None, attach={"root_id": "evidence", "path": "pipe"})
		finally:
			os.unlink(root / "pipe")  # host tooling that scans tmp trees must never meet a FIFO


class TestDurableCloseAnchor:
	def test_transient_envelope_durable_close_retained(self, store):
		mid = send_one(store, retention="transient")
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant=claim["participant"],
		                  body=b"durable signoff record", outcome="signed_off",
		                  retention="durable")
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert mid not in result["messages"]
		assert store.conn.execute(
			"SELECT COUNT(*) FROM messages WHERE id=?", (mid,)).fetchone()[0] == 1
		assert store.get_claim(claim["claim_id"])["state"] == "completed"
		row = store.conn.execute(
			"SELECT c.body FROM dispositions d JOIN contents c ON c.content_id=d.content_id "
			"WHERE d.claim_id=?", (claim["claim_id"],)).fetchone()
		assert row["body"] == b"durable signoff record"
		retry = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                          body=b"durable signoff record", outcome="signed_off",
		                          retention="durable")
		assert retry["already_committed"] is True

	def test_transient_envelope_transient_close_still_collected(self, store):
		mid = send_one(store, retention="transient")
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant=claim["participant"], outcome="seen")
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert mid in result["messages"]


# ---------------------------------------------------------------------------
# Maintenance / move / migrate ceremonies (T7, T15, T22-move)
# ---------------------------------------------------------------------------

class TestMaintenance:
	def test_enter_gates_writes_and_exit_clears(self, instance):
		result = b6.maintenance_enter(instance, participant="hq.lead", reason="planned upkeep")
		assert result == {"maintenance": True, "move_token": None, "destination": None}
		with pytest.raises(b6.BatonError) as excinfo:
			with b6.open_instance(instance) as st:
				send_one(st)
		assert excinfo.value.exit_code == b6.EXIT_GATED
		with b6.open_instance(instance, readonly=True) as ro:
			assert ro.conn.execute(
				"SELECT maintainer_reason FROM instance_meta").fetchone()[0] == "planned upkeep"
		b6.maintenance_exit(instance, participant="hq.lead",
		                    reason="done")
		with b6.open_instance(instance) as st:
			send_one(st)
		with b6.open_instance(instance, readonly=True) as ro:
			kinds = [r[0] for r in ro.conn.execute("SELECT kind FROM ceremonies ORDER BY created_ts")]
			assert kinds == ["maintenance_enter", "maintenance_exit"]

	def test_enter_requires_capability_and_reason(self, instance):
		with pytest.raises(b6.BatonError, match="'config' capability"):
			b6.maintenance_enter(instance, participant="acme.reviewer", reason="nope")
		with pytest.raises(b6.BatonError, match="reason"):
			b6.maintenance_enter(instance, participant="hq.lead", reason=" ")

	def test_double_enter_refused(self, instance):
		b6.maintenance_enter(instance, participant="hq.lead",
		                     reason="first")
		with pytest.raises(b6.BatonError, match="already under maintenance"):
			b6.maintenance_enter(instance, participant="hq.lead",
			                     reason="second")

	def test_ceremony_rows_immutable(self, instance):
		b6.maintenance_enter(instance, participant="hq.lead",
		                     reason="upkeep")
		with b6.open_instance(instance, _for_ceremony=True) as st:
			with pytest.raises(sqlite3.IntegrityError, match="immutable"):
				st.conn.execute("UPDATE ceremonies SET reason='forged'")
			with pytest.raises(sqlite3.IntegrityError, match="immutable"):
				st.conn.execute("DELETE FROM ceremonies")
			with pytest.raises(sqlite3.IntegrityError, match="context"):
				st.conn.execute(
					"INSERT INTO ceremonies(ceremony_id, kind, participant, created_ts) "
					"VALUES('raw', 'migrate', 'p.q', 'now')")


class TestCheckpointDrain:
	def test_drain_waits_for_reader_then_converges(self, instance, monkeypatch):
		monkeypatch.setattr(b6, "CHECKPOINT_DRAIN_ATTEMPTS", 3)
		monkeypatch.setattr(b6, "CHECKPOINT_DRAIN_SLEEP_S", 0.05)
		with b6.open_instance(instance) as writer:
			send_one(writer)
			reader = b6.open_instance(instance, readonly=True)
			reader.conn.execute("BEGIN")
			reader.conn.execute("SELECT COUNT(*) FROM messages").fetchone()
			try:
				with pytest.raises(b6.BatonError, match="did not converge"):
					b6.checkpoint_drain(writer)
			finally:
				reader.conn.execute("COMMIT")
				reader.close()
			log, ckpt = b6.checkpoint_drain(writer)
			assert log == ckpt


class TestMoveCeremony:
	def _setup(self, tmp_path):
		src = tmp_path / "src"
		src.mkdir()
		config_path = str(src / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			send_one(st)
		dest = tmp_path / "dest"
		dest.mkdir()
		return config_path, str(dest / "baton.json")

	def _enter(self, config_path, dest_config):
		return b6.maintenance_enter(config_path, participant="hq.lead", reason="relocating", move=True,
		                            destination=dest_config)["move_token"]

	def _lead(self):
		return {"participant": "hq.lead"}

	def test_full_move_happy_path_with_idempotent_retries(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		copy1 = b6.move_copy(config_path, **self._lead())
		assert copy1["stage"] == "copied" and copy1["already_committed"] is False
		copy2 = b6.move_copy(config_path, **self._lead())  # pre-bind resume
		assert copy2["already_committed"] is True and copy2["stage"] == "copied"
		bind = b6.move_bind_destination(dest_config, token=token, **self._lead())
		assert bind["already_committed"] is False
		rebind = b6.move_bind_destination(dest_config, token=token, **self._lead())
		assert rebind["already_committed"] is True
		copy3 = b6.move_copy(config_path, **self._lead())  # post-bind stage discovery
		assert copy3["already_committed"] is True and copy3["stage"] == "bound"
		act = b6.move_activate(dest_config, token=token, **self._lead())
		assert act["already_committed"] is False
		react = b6.move_activate(dest_config, token=token, **self._lead())
		assert react["already_committed"] is True
		copy4 = b6.move_copy(config_path, **self._lead())  # post-activation discovery
		assert copy4["already_committed"] is True and copy4["stage"] == "activated"
		with b6.open_instance(dest_config) as st:
			assert len(st.scan("acme.implementer")["pending"]) == 1
			send_one(st)
		dec = b6.move_decommission(config_path, token=token, moved_to=dest_config, **self._lead())
		assert dec["already_committed"] is False
		redec = b6.move_decommission(config_path, token=token, moved_to=dest_config, **self._lead())
		assert redec["already_committed"] is True
		with pytest.raises(b6.BatonError, match="has moved to"):
			with b6.open_instance(config_path) as st:
				send_one(st)
		with b6.open_instance(dest_config, readonly=True) as ro:
			uuid_dest = ro.conn.execute("SELECT uuid FROM instance_meta").fetchone()[0]
		with b6.open_instance(config_path, readonly=True, _for_ceremony=True) as ro:
			uuid_src = ro.conn.execute("SELECT uuid FROM instance_meta").fetchone()[0]
		assert uuid_src == uuid_dest

	def test_three_authority_repro_is_impossible(self, tmp_path):
		"""The reviewer's fork repro: source + two copies must NOT all activate."""
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		b6.move_copy(config_path, **self._lead())
		# The source cannot activate (role='source').
		with pytest.raises(b6.BatonError, match="can never activate"):
			b6.move_activate(config_path, token=token, **self._lead())
		# An unbound copy cannot activate either.
		with pytest.raises(b6.BatonError, match="can never activate"):
			b6.move_activate(dest_config, token=token, **self._lead())
		# A second destination cannot exist: copy only goes to the bound peer,
		# and a copy manually placed elsewhere refuses to bind.
		rogue = os.path.dirname(dest_config) + "-rogue"
		os.mkdir(rogue)
		import shutil
		shutil.copy(dest_config.replace("baton.json", "mailbox.sqlite3"),
		            os.path.join(rogue, "mailbox.sqlite3"))
		shutil.copy(os.path.join(os.path.dirname(dest_config), "baton.json"),
		            os.path.join(rogue, "baton.json"))
		with pytest.raises(b6.BatonError, match="DESTINATION route"):
			b6.move_bind_destination(os.path.join(rogue, "baton.json"), token=token, **self._lead())
		# Only the bound copy can bind + activate; afterwards the source still
		# cannot activate and must decommission.
		b6.move_bind_destination(dest_config, token=token, **self._lead())
		b6.move_activate(dest_config, token=token, **self._lead())
		with pytest.raises(b6.BatonError, match="can never activate"):
			b6.move_activate(config_path, token=token, **self._lead())
		active = 0
		for path in (config_path, dest_config, os.path.join(rogue, "baton.json")):
			try:
				with b6.open_instance(path) as st:
					send_one(st)
				active += 1
			except b6.BatonError:
				pass
		assert active == 1

	def test_generic_clear_refused_on_both_roles(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		b6.move_copy(config_path, **self._lead())
		for path in (config_path, dest_config):
			with pytest.raises(b6.BatonError, match="generic maintenance clear is refused"):
				b6.maintenance_exit(path, participant="hq.lead",
				                    reason="oops")

	def test_abort_is_source_only(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		b6.move_copy(config_path, **self._lead())
		with pytest.raises(b6.BatonError, match="SOURCE route"):
			b6.abort_move(dest_config, token=token, destination_destroyed=True,
			              reason="copy must die instead", **self._lead())
		with pytest.raises(b6.BatonError, match="attestation"):
			b6.abort_move(config_path, token=token, destination_destroyed=False,
			              reason="abort", **self._lead())
		with pytest.raises(b6.BatonError, match="boolean"):
			b6.abort_move(config_path, token=token, destination_destroyed="yes",
			              reason="abort", **self._lead())
		with pytest.raises(b6.BatonError, match="token does not match"):
			b6.abort_move(config_path, token="0" * 32, destination_destroyed=True,
			              reason="abort", **self._lead())
		b6.abort_move(config_path, token=token, destination_destroyed=True,
		              reason="destination destroyed by hand", **self._lead())
		with b6.open_instance(config_path) as st:
			send_one(st)

	def test_decommission_role_and_peer_validation(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		b6.move_copy(config_path, **self._lead())
		with pytest.raises(b6.BatonError, match="SOURCE route"):
			b6.move_decommission(dest_config, token=token, moved_to=dest_config, **self._lead())
		with pytest.raises(b6.BatonError, match="does not match the bound destination"):
			b6.move_decommission(config_path, token=token, moved_to="/somewhere/else", **self._lead())

	def test_copy_requires_move_gate(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		with pytest.raises(b6.BatonError, match="maintenance_enter"):
			b6.move_copy(config_path, **self._lead())
		b6.maintenance_enter(config_path, participant="hq.lead",
		                     reason="plain, not move")
		with pytest.raises(b6.BatonError, match="maintenance_enter"):
			b6.move_copy(config_path, **self._lead())

	def test_mismatching_destination_artifact_fails_closed(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		(tmp_path / "dest" / "mailbox.sqlite3").write_bytes(b"squatter")
		with pytest.raises(b6.BatonError) as excinfo:
			b6.move_copy(config_path, **self._lead())
		assert excinfo.value.exit_code == b6.EXIT_DAMAGE

	def test_enter_validates_destination_shape(self, tmp_path):
		config_path, _ = self._setup(tmp_path)
		for bad in ("relative/baton.json", "/nonexistent-dir/baton.json",
		            str(tmp_path / "dest") + "/", str(tmp_path)):
			with pytest.raises(b6.BatonError):
				b6.maintenance_enter(config_path, participant="hq.lead", reason="move", move=True, destination=bad)
		with pytest.raises(b6.BatonError, match="boolean"):
			b6.maintenance_enter(config_path, participant="hq.lead", reason="move", move=1,
			                     destination=str(tmp_path / "dest" / "baton.json"))

	def test_crash_window_zero_active_and_human_recovery(self, tmp_path):
		config_path, dest_config = self._setup(tmp_path)
		token = self._enter(config_path, dest_config)
		b6.move_copy(config_path, **self._lead())
		for path in (config_path, dest_config):
			with pytest.raises(b6.BatonError) as excinfo:
				with b6.open_instance(path) as st:
					send_one(st)
			assert excinfo.value.exit_code == b6.EXIT_GATED
		b6.move_bind_destination(dest_config, token=token, **self._lead())
		b6.move_activate(dest_config, token=token, **self._lead())
		with b6.open_instance(dest_config) as st:
			send_one(st)


def _move_copy_with_fault(config_path, point, queue):
	import baton_v6 as mod
	def hook(p):
		if p == point:
			os._exit(9)
	mod._FAULT_HOOK = hook
	try:
		mod.move_copy(config_path, participant="hq.lead")
		queue.put("completed")
	except mod.BatonError as exc:
		queue.put(f"error:{exc}")


class TestMoveFaultMatrix:
	POINTS = ["move:pre-drain", "move:post-drain", "move:config-copied", "move:db-copied"]

	@pytest.mark.parametrize("point", POINTS)
	def test_kill_then_resume_same_move(self, tmp_path, point):
		src = tmp_path / "src"
		src.mkdir()
		config_path = str(src / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			send_one(st)
		dest = tmp_path / "dest"
		dest.mkdir()
		dest_config = str(dest / "baton.json")
		token = b6.maintenance_enter(config_path, participant="hq.lead", reason="relocating", move=True,
		                             destination=dest_config)["move_token"]
		ctx = multiprocessing.get_context("spawn")
		queue = ctx.Queue()
		proc = ctx.Process(target=_move_copy_with_fault, args=(config_path, point, queue))
		proc.start()
		proc.join(60)
		assert proc.exitcode == 9
		# Fresh-process resume of the SAME move: completes to 'copied'.
		result = b6.move_copy(config_path, participant="hq.lead")
		assert result["stage"] == "copied"
		b6.move_bind_destination(dest_config, token=token, participant="hq.lead")
		b6.move_activate(dest_config, token=token, participant="hq.lead")
		with b6.open_instance(dest_config) as st:
			assert len(st.scan("acme.implementer")["pending"]) == 1


class TestMigrateGate:
	def test_migrate_requires_maintenance_and_reports_no_path(self, instance):
		"""The gate is an audited refusal, not a capability: this tool knows
		only protocol 8, and gains a migration path only alongside a protocol
		bump together with the frozen definition of what it migrates from.
		The ATTEMPT is durably audited before the refusal is reported."""
		with pytest.raises(b6.BatonError, match="maintenance gate"):
			b6.migrate_instance(instance, participant="hq.lead")
		b6.maintenance_enter(instance, participant="hq.lead",
		                     reason="migration attempt")
		with pytest.raises(b6.BatonError, match="no migration path") as excinfo:
			b6.migrate_instance(instance, participant="hq.lead")
		assert excinfo.value.exit_code == b6.EXIT_PROTOCOL
		with b6.open_instance(instance, _for_ceremony=True) as st:
			rows = st.conn.execute(
				"SELECT reason FROM ceremonies WHERE kind='migrate'").fetchall()
			assert len(rows) == 1 and "attempted migration" in rows[0][0]

	def test_migrate_requires_capability(self, instance):
		with pytest.raises(b6.BatonError, match="'config' capability"):
			b6.migrate_instance(instance, participant="acme.reviewer")


# ---------------------------------------------------------------------------
# Move round-5 pins: post-bind clone, routing history, committed-boundary
# crash matrix, streaming copy
# ---------------------------------------------------------------------------

def _move_setup(tmp_path):
	src = tmp_path / "src"
	src.mkdir()
	config_path = str(src / "baton.json")
	with open(config_path, "w") as handle:
		json.dump(make_config(), handle)
	b6.init_instance(config_path)
	with b6.open_instance(config_path) as st:
		send_one(st)
	dest = tmp_path / "dest"
	dest.mkdir()
	dest_config = str(dest / "baton.json")
	token = b6.maintenance_enter(config_path, participant="hq.lead", reason="relocating", move=True,
	                             destination=dest_config)["move_token"]
	return config_path, dest_config, token


LEAD = {"participant": "hq.lead"}


class TestPostBindClone:
	def test_post_bind_clone_cannot_activate(self, tmp_path):
		"""Red-first order per review: rogue activation is attempted BEFORE
		the real destination activates."""
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		rogue = tmp_path / "rogue"
		rogue.mkdir()
		shutil.copy(os.path.join(os.path.dirname(dest_config), "mailbox.sqlite3"),
		            rogue / "mailbox.sqlite3")
		shutil.copy(dest_config, rogue / "baton.json")
		with pytest.raises(b6.BatonError, match="DESTINATION route") as excinfo:
			b6.move_activate(str(rogue / "baton.json"), token=token, **LEAD)
		assert excinfo.value.exit_code == b6.EXIT_DAMAGE
		b6.move_activate(dest_config, token=token, **LEAD)
		writable = []
		for path in (dest_config, str(rogue / "baton.json")):
			try:
				with b6.open_instance(path) as st:
					send_one(st)
				writable.append(path)
			except b6.BatonError:
				pass
		assert writable == [dest_config]

	def test_activated_clone_cannot_acknowledge_retry(self, tmp_path):
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		rogue = tmp_path / "rogue2"
		rogue.mkdir()
		shutil.copy(os.path.join(os.path.dirname(dest_config), "mailbox.sqlite3"),
		            rogue / "mailbox.sqlite3")
		shutil.copy(dest_config, rogue / "baton.json")
		with pytest.raises(b6.BatonError, match="DESTINATION route"):
			b6.move_activate(str(rogue / "baton.json"), token=token, **LEAD)

	def test_bound_clone_cannot_acknowledge_bind_retry(self, tmp_path):
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		rogue = tmp_path / "rogue3"
		rogue.mkdir()
		shutil.copy(os.path.join(os.path.dirname(dest_config), "mailbox.sqlite3"),
		            rogue / "mailbox.sqlite3")
		shutil.copy(dest_config, rogue / "baton.json")
		with pytest.raises(b6.BatonError, match="DESTINATION route"):
			b6.move_bind_destination(str(rogue / "baton.json"), token=token, **LEAD)


class TestRoutingHistory:
	def test_decommission_retry_wrong_route_rejects(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		retry = b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		assert retry["already_committed"] is True
		with pytest.raises(b6.BatonError, match="differs from the committed route"):
			b6.move_decommission(config_path, token=token,
			                     moved_to="/definitely/wrong/baton.json", **LEAD)

	def test_ceremony_rows_retain_route(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		with b6.open_instance(dest_config, readonly=True) as ro:
			rows = {r["kind"]: r["peer"] for r in ro.conn.execute(
				"SELECT kind, peer FROM ceremonies WHERE token=?", (token,))}
		assert rows["move_bind_destination"] == dest_config
		assert rows["move_activate"] == dest_config


def _ceremony_with_fault(func_name, args, kwargs, point, queue):
	import baton_v6 as mod
	def hook(p):
		if p == point:
			os._exit(9)
	mod._FAULT_HOOK = hook
	try:
		getattr(mod, func_name)(*args, **kwargs)
		queue.put("completed")
	except mod.BatonError as exc:
		queue.put(f"error:{exc}")


class TestCommittedBoundaryCrashes:
	def _kill(self, func_name, args, kwargs, point):
		ctx = multiprocessing.get_context("spawn")
		queue = ctx.Queue()
		proc = ctx.Process(target=_ceremony_with_fault,
		                   args=(func_name, args, kwargs, point, queue))
		proc.start()
		proc.join(60)
		assert proc.exitcode == 9

	def test_enter_committed_crash_is_discoverable_and_resumable(self, tmp_path):
		src = tmp_path / "src"
		src.mkdir()
		config_path = str(src / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		b6.init_instance(config_path)
		dest = tmp_path / "dest"
		dest.mkdir()
		dest_config = str(dest / "baton.json")
		self._kill("maintenance_enter", (config_path,),
		           dict(reason="relocating", move=True, destination=dest_config, **LEAD),
		           "enter:committed")
		state = b6.move_status_inspect(config_path)
		assert state["move_status"] == "moving"
		assert state["move_peer"] == dest_config
		token = state["move_token"]
		assert token is not None
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		with b6.open_instance(dest_config) as st:
			send_one(st)

	def test_bind_activate_decommission_committed_crashes_resume(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		self._kill("move_bind_destination", (dest_config,),
		           dict(token=token, **LEAD), "bind:committed")
		rebind = b6.move_bind_destination(dest_config, token=token, **LEAD)
		assert rebind["already_committed"] is True
		self._kill("move_activate", (dest_config,),
		           dict(token=token, **LEAD), "activate:committed")
		react = b6.move_activate(dest_config, token=token, **LEAD)
		assert react["already_committed"] is True
		self._kill("move_decommission", (config_path,),
		           dict(token=token, moved_to=dest_config, **LEAD), "decommission:committed")
		redec = b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		assert redec["already_committed"] is True
		active = 0
		for path in (config_path, dest_config):
			try:
				with b6.open_instance(path) as st:
					send_one(st)
				active += 1
			except b6.BatonError:
				pass
		assert active == 1


class TestStreamingCopy:
	def test_bounded_chunks_and_resume(self, tmp_path, monkeypatch):
		monkeypatch.setattr(b6, "COPY_CHUNK", 7)  # tiny chunks: bounded by construction
		config_path, dest_config, token = _move_setup(tmp_path)
		result = b6.move_copy(config_path, **LEAD)
		assert result["stage"] == "copied"
		again = b6.move_copy(config_path, **LEAD)
		assert again["already_committed"] is True

	def test_premature_eof_fails_closed(self, tmp_path):
		scratch_dir = tmp_path / "s"
		scratch_dir.mkdir()
		src = tmp_path / "short.bin"
		src.write_bytes(b"abc")
		sfd = os.open(src, os.O_RDONLY)
		dfd = os.open(scratch_dir, os.O_DIRECTORY)
		try:
			with pytest.raises(b6.BatonError, match="premature EOF"):
				b6._stream_publish_from_fd(sfd, 10, dfd, "out.bin", 0o600)
			assert not (scratch_dir / "out.bin").exists()
			leftovers = [p for p in scratch_dir.iterdir()]
			assert leftovers == []  # scratch cleaned
		finally:
			os.close(sfd)
			os.close(dfd)

	def test_fifo_destination_artifact_rejected(self, tmp_path):
		scratch_dir = tmp_path / "s"
		scratch_dir.mkdir()
		os.mkfifo(scratch_dir / "out.bin")
		src = tmp_path / "src.bin"
		src.write_bytes(b"payload")
		sfd = os.open(src, os.O_RDONLY)
		dfd = os.open(scratch_dir, os.O_DIRECTORY)
		try:
			with pytest.raises(b6.BatonError, match="not a regular file"):
				b6._stream_publish_from_fd(sfd, 7, dfd, "out.bin", 0o600)
		finally:
			os.close(sfd)
			os.close(dfd)
			os.unlink(scratch_dir / "out.bin")  # FIFO must not meet tmp scanners

	def test_mismatching_existing_artifact_fails_closed(self, tmp_path):
		scratch_dir = tmp_path / "s"
		scratch_dir.mkdir()
		(scratch_dir / "out.bin").write_bytes(b"different")
		src = tmp_path / "src.bin"
		src.write_bytes(b"payload")
		sfd = os.open(src, os.O_RDONLY)
		dfd = os.open(scratch_dir, os.O_DIRECTORY)
		try:
			with pytest.raises(b6.BatonError, match="MISMATCHING"):
				b6._stream_publish_from_fd(sfd, 7, dfd, "out.bin", 0o600)
		finally:
			os.close(sfd)
			os.close(dfd)


# ---------------------------------------------------------------------------
# Move round-6 pins: symmetric source route, activation-gated decommission,
# nonblocking config artifacts
# ---------------------------------------------------------------------------

class TestSourceRouteBinding:
	def _rogue_from(self, src_dir, tmp_path, name="rogue-src"):
		import shutil
		rogue = tmp_path / name
		rogue.mkdir()
		shutil.copy(os.path.join(src_dir, "mailbox.sqlite3"), rogue / "mailbox.sqlite3")
		shutil.copy(os.path.join(src_dir, "baton.json"), rogue / "baton.json")
		return str(rogue / "baton.json")

	def test_two_active_abort_repro_is_impossible(self, tmp_path):
		"""The round-6 repro: rogue source-role copy + truthful attestation."""
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		rogue_config = self._rogue_from(os.path.dirname(dest_config), tmp_path)
		import shutil
		shutil.rmtree(os.path.dirname(dest_config))  # destination truly destroyed
		with pytest.raises(b6.BatonError, match="SOURCE route"):
			b6.abort_move(rogue_config, token=token, destination_destroyed=True,
			              reason="rogue tries first", **LEAD)
		b6.abort_move(config_path, token=token, destination_destroyed=True,
		              reason="destination destroyed", **LEAD)
		active = []
		for path in (config_path, rogue_config):
			try:
				with b6.open_instance(path) as st:
					send_one(st)
				active.append(path)
			except b6.BatonError:
				pass
		assert active == [config_path]

	def test_rogue_source_copy_cannot_decommission_or_copy(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		rogue_config = self._rogue_from(os.path.dirname(config_path), tmp_path, "rogue-src2")
		with pytest.raises(b6.BatonError, match="SOURCE route"):
			b6.move_decommission(rogue_config, token=token, moved_to=dest_config, **LEAD)
		with pytest.raises(b6.BatonError, match="SOURCE route"):
			b6.move_copy(rogue_config, **LEAD)
		result = b6.move_copy(config_path, **LEAD)  # true source still drives the move
		assert result["already_committed"] is True

	def test_enter_must_run_at_source_route(self, tmp_path):
		src = tmp_path / "src"
		src.mkdir()
		config_path = str(src / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		b6.init_instance(config_path)
		dest = tmp_path / "dest"
		dest.mkdir()
		token = b6.maintenance_enter(config_path, participant="hq.lead", reason="ok", move=True,
		                             destination=str(dest / "baton.json"))["move_token"]
		state = b6.move_status_inspect(config_path)
		assert state["move_peer"] == str(dest / "baton.json")


class TestActivationGatedDecommission:
	def test_decommission_refused_before_copy_bind_activation(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		with pytest.raises(b6.BatonError, match="does not exist yet"):
			b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		b6.move_copy(config_path, **LEAD)
		with pytest.raises(b6.BatonError, match="not active"):
			b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		with pytest.raises(b6.BatonError, match="not active"):
			b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		result = b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		assert result["already_committed"] is False
		retry = b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		assert retry["already_committed"] is True


class TestNonblockingConfigArtifacts:
	def test_fifo_destination_config_refuses_without_hanging(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		os.mkfifo(dest_config)
		try:
			with pytest.raises(b6.BatonError):
				b6.move_copy(config_path, **LEAD)
		finally:
			os.unlink(dest_config)

	def test_fifo_instance_config_refuses_without_hanging(self, tmp_path):
		os.mkfifo(tmp_path / "baton.json")
		try:
			with pytest.raises(b6.BatonError, match="regular file"):
				b6.load_config(str(tmp_path / "baton.json"))
		finally:
			os.unlink(tmp_path / "baton.json")


# ---------------------------------------------------------------------------
# Move round-7 pins: symlink-route repro, directory replacement, immutable
# move bindings, inspect completeness
# ---------------------------------------------------------------------------

class TestSymlinkRouteIdentity:
	def test_symlink_route_two_active_repro_impossible(self, tmp_path):
		"""The reviewer's exact five-step repro: symlink the source path at a
		rogue source-role copy; both aborts must NOT succeed."""
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		rogue = tmp_path / "rogue"
		rogue.mkdir()
		shutil.copy(os.path.join(os.path.dirname(dest_config), "mailbox.sqlite3"),
		            rogue / "mailbox.sqlite3")
		shutil.copy(os.path.join(os.path.dirname(dest_config), "baton.json"),
		            rogue / "baton.json")
		shutil.rmtree(os.path.dirname(dest_config))  # attestation true
		src_dir = os.path.dirname(config_path)
		aside = src_dir + "-aside"
		os.rename(src_dir, aside)
		os.symlink(rogue, src_dir)
		try:
			with pytest.raises(b6.BatonError):
				b6.abort_move(config_path, token=token, destination_destroyed=True,
				              reason="rogue via symlinked source path", **LEAD)
		finally:
			os.unlink(src_dir)
			os.rename(aside, src_dir)
		b6.abort_move(config_path, token=token, destination_destroyed=True,
		              reason="true source aborts", **LEAD)
		active = []
		for path in (config_path, str(rogue / "baton.json")):
			try:
				with b6.open_instance(path) as st:
					send_one(st)
				active.append(path)
			except b6.BatonError:
				pass
		assert active == [config_path]

	def test_replaced_source_directory_refuses_source_ceremonies(self, tmp_path):
		"""Rename-aside + fresh directory at the same path: new inode, so the
		bound identity no longer matches even for byte-identical contents."""
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		src_dir = os.path.dirname(config_path)
		aside = src_dir + "-aside"
		os.rename(src_dir, aside)
		shutil.copytree(aside, src_dir)  # same path, DIFFERENT directory inode
		try:
			with pytest.raises(b6.BatonError, match="directory identity|physically reside"):
				b6.abort_move(config_path, token=token, destination_destroyed=True,
				              reason="replaced dir", **LEAD)
			with pytest.raises(b6.BatonError, match="directory identity|physically reside"):
				b6.move_copy(config_path, **LEAD)
		finally:
			shutil.rmtree(src_dir)
			os.rename(aside, src_dir)
		retry = b6.move_copy(config_path, **LEAD)  # true source still works
		assert retry["already_committed"] is True

	def test_replaced_destination_directory_refuses_bind_activate(self, tmp_path):
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		dest_dir = os.path.dirname(dest_config)
		aside = dest_dir + "-aside"
		os.rename(dest_dir, aside)
		shutil.copytree(aside, dest_dir)
		try:
			with pytest.raises(b6.BatonError, match="directory identity|physically reside"):
				b6.move_bind_destination(dest_config, token=token, **LEAD)
		finally:
			shutil.rmtree(dest_dir)
			os.rename(aside, dest_dir)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)


class TestMoveBindingAuthority:
	def test_moves_row_created_and_immutable(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		with b6.open_instance(config_path, readonly=True, _for_ceremony=True) as ro:
			row = ro.conn.execute("SELECT * FROM moves WHERE token=?", (token,)).fetchone()
			assert row["source_config"] == config_path
			assert row["destination_config"] == dest_config
			assert row["source_ino"] > 0 and row["destination_ino"] > 0
		with b6.open_instance(config_path, _for_ceremony=True) as st:
			with pytest.raises(sqlite3.IntegrityError, match="immutable"):
				st.conn.execute("UPDATE moves SET source_config='/forged' WHERE token=?", (token,))
			with pytest.raises(sqlite3.IntegrityError, match="immutable"):
				st.conn.execute("DELETE FROM moves")
			with pytest.raises(sqlite3.IntegrityError, match="move entry"):
				st.conn.execute(
					"INSERT INTO moves(token, instance_uuid, source_config, source_dev, source_ino, "
					"destination_config, destination_dev, destination_ino, created_ts) "
					"VALUES('raw', 'u', '/s', 1, 1, '/d', 1, 1, 'now')")

	def test_binding_survives_activation_and_inspect_is_complete(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		state = b6.move_status_inspect(config_path)
		assert state["move_source"] == config_path
		assert state["binding"]["destination_config"] == dest_config
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		with b6.open_instance(dest_config, readonly=True) as ro:
			row = ro.conn.execute("SELECT * FROM moves WHERE token=?", (token,)).fetchone()
			assert row is not None
			assert row["source_config"] == config_path
			assert row["destination_config"] == dest_config


# ---------------------------------------------------------------------------
# Move round-8 pins: same-directory rejection, binding as sole authority,
# entry-verb-guarded bindings
# ---------------------------------------------------------------------------

class TestSameDirectoryMove:
	def test_same_config_path_and_same_dir_other_basename_refused(self, tmp_path):
		src = tmp_path / "src"
		src.mkdir()
		config_path = str(src / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		b6.init_instance(config_path)
		for bad_dest in (config_path, str(src / "other-config.json")):
			with pytest.raises(b6.BatonError, match="same directory"):
				b6.maintenance_enter(config_path, participant="hq.lead", reason="fold", move=True, destination=bad_dest)
			with b6.open_instance(config_path) as st:
				send_one(st)  # source remains active and unchanged after refusal


class TestBindingSoleAuthority:
	def _replaced(self, path):
		import shutil
		aside = path + "-aside"
		os.rename(path, aside)
		shutil.copytree(aside, path)
		return aside

	def test_destination_replacement_fails_stage_discovery(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		dest_dir = os.path.dirname(dest_config)
		aside = self._replaced(dest_dir)
		try:
			with pytest.raises(b6.BatonError, match="directory identity|physically reside"):
				b6.move_copy(config_path, **LEAD)
		finally:
			import shutil
			shutil.rmtree(dest_dir)
			os.rename(aside, dest_dir)
		again = b6.move_copy(config_path, **LEAD)
		assert again["already_committed"] is True

	def test_destination_replacement_fails_decommission(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		b6.move_copy(config_path, **LEAD)
		b6.move_bind_destination(dest_config, token=token, **LEAD)
		b6.move_activate(dest_config, token=token, **LEAD)
		dest_dir = os.path.dirname(dest_config)
		aside = self._replaced(dest_dir)
		try:
			with pytest.raises(b6.BatonError, match="directory identity|physically reside"):
				b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		finally:
			import shutil
			shutil.rmtree(dest_dir)
			os.rename(aside, dest_dir)
		result = b6.move_decommission(config_path, token=token, moved_to=dest_config, **LEAD)
		assert result["already_committed"] is False

	def test_forged_binding_uuid_is_corruption(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		with b6.open_instance(config_path, _for_ceremony=True) as st:
			st._txn_begin("move_enter", ceremony="move")
			try:
				st.conn.execute(
					"INSERT INTO moves(token, instance_uuid, source_config, source_dev, source_ino, "
					"destination_config, destination_dev, destination_ino, created_ts) "
					"VALUES('ffffffffffffffffffffffffffffffff', 'foreign-uuid', ?, 1, 1, ?, 1, 1, 'now')",
					(config_path, dest_config))
				st._txn_commit()
			except BaseException:
				st._txn_rollback()
				raise
			with pytest.raises(b6.BatonError, match="different instance uuid"):
				st._move_binding("ffffffffffffffffffffffffffffffff")

	def test_noncanonical_caller_spelling_refused(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		alias = os.path.dirname(config_path) + "/./baton.json"
		with pytest.raises(b6.BatonError):
			b6.move_copy(alias, **LEAD)
		result = b6.move_copy(config_path, **LEAD)  # exact spelling proceeds
		assert result["stage"] == "copied"

	def test_binding_insert_requires_entry_verb(self, tmp_path):
		config_path, dest_config, token = _move_setup(tmp_path)
		with b6.open_instance(config_path, _for_ceremony=True) as st:
			st._txn_begin("move", ceremony="move")
			try:
				with pytest.raises(sqlite3.IntegrityError, match="move entry"):
					st.conn.execute(
						"INSERT INTO moves(token, instance_uuid, source_config, source_dev, "
						"source_ino, destination_config, destination_dev, destination_ino, "
						"created_ts) VALUES('deadbeefdeadbeefdeadbeefdeadbeef', 'u', '/s', 1, 1, "
						"'/d', 1, 1, 'now')")
			finally:
				st._txn_rollback()


# ---------------------------------------------------------------------------
# Move round-9 pins: post-publication identity, non-regular source config
# ---------------------------------------------------------------------------

class TestPostPublicationValidation:
	def test_destination_substitution_after_publication_fails(self, tmp_path, monkeypatch):
		import shutil
		config_path, dest_config, token = _move_setup(tmp_path)
		dest_dir = os.path.dirname(dest_config)
		state = {}
		def substitute(point):
			if point == "move:db-copied":
				aside = dest_dir + "-aside"
				os.rename(dest_dir, aside)
				shutil.copytree(aside, dest_dir)
				state["aside"] = aside
		monkeypatch.setattr(b6, "_FAULT_HOOK", substitute)
		with pytest.raises(b6.BatonError, match="directory identity|physically reside"):
			b6.move_copy(config_path, **LEAD)
		monkeypatch.setattr(b6, "_FAULT_HOOK", None)
		shutil.rmtree(dest_dir)
		os.rename(state["aside"], dest_dir)
		result = b6.move_copy(config_path, **LEAD)  # restored original resumes
		assert result["stage"] == "copied"

	def test_non_regular_source_config_rejected_promptly(self, tmp_path, monkeypatch):
		config_path, dest_config, token = _move_setup(tmp_path)
		def replace_with_fifo(point):
			if point == "move:post-drain":
				os.unlink(config_path)
				os.mkfifo(config_path)
		monkeypatch.setattr(b6, "_FAULT_HOOK", replace_with_fifo)
		try:
			with pytest.raises(b6.BatonError, match="regular file"):
				b6.move_copy(config_path, **LEAD)
		finally:
			monkeypatch.setattr(b6, "_FAULT_HOOK", None)
			os.unlink(config_path)
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		state = b6.move_status_inspect(config_path)
		assert state["move_status"] == "moving"  # move stays gated and resumable
		result = b6.move_copy(config_path, **LEAD)
		assert result["stage"] == "copied"


# ---------------------------------------------------------------------------
# wait/eventing + CLI + observability phase (T8/T19 core + CLI matrix)
# ---------------------------------------------------------------------------
import threading
import time as _time


class TestWait:
	def test_wait_returns_existing_immediately(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st)
		result = b6.wait_for_message(instance, "acme.implementer",
		                            timeout_s=5)
		assert result["claim"]["state"] == "active"
		assert result["message"]["body"]["utf8"] == "hello"

	def test_wait_wakes_on_late_send(self, instance):
		def sender():
			_time.sleep(0.5)
			with b6.open_instance(instance) as st:
				send_one(st)
		thread = threading.Thread(target=sender)
		thread.start()
		start = _time.monotonic()
		result = b6.wait_for_message(instance, "acme.implementer",
		                            timeout_s=30, rescan_interval_s=20)
		elapsed = _time.monotonic() - start
		thread.join()
		assert result["claim"]["state"] == "active"
		assert elapsed < 15  # woken by the watch, not the 20s rescan

	def test_wait_timeout_is_clean_none(self, instance):
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer",
			                    timeout_s=0.3, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE

	def test_degraded_polling_parity(self, instance, monkeypatch):
		class Broken:
			def __init__(self, _dir):
				raise OSError("inotify unavailable")
		monkeypatch.setattr(b6, "_InotifyWatch", Broken)
		def sender():
			_time.sleep(0.4)
			with b6.open_instance(instance) as st:
				send_one(st)
		thread = threading.Thread(target=sender)
		thread.start()
		result = b6.wait_for_message(instance, "acme.implementer",
		                            timeout_s=30, rescan_interval_s=0.2)
		thread.join()
		assert result["claim"]["state"] == "active"

	def test_wait_stands_down_when_gated(self, instance):
		b6.maintenance_enter(instance, participant="hq.lead",
		                     reason="gate")
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer",
			                    timeout_s=5)
		assert excinfo.value.exit_code == b6.EXIT_GATED


class TestObservability:
	def test_doctor_healthy_and_scratch_report(self, instance, tmp_path):
		with b6.open_instance(instance) as st:
			send_one(st)
			st.claim("acme.implementer")
		report = b6.doctor(instance)
		assert report["ok"] is True
		assert report["messages_by_state"] == {"claimed": 1}
		assert len(report["active_claims"]) == 1
		(tmp_path / ".init-stale.sqlite3").write_bytes(b"x")
		(tmp_path / "surprise.txt").write_bytes(b"x")
		report = b6.doctor(instance)
		assert report["stale_scratch"] == [".init-stale.sqlite3"]
		assert report["unrecognized_files"] == ["surprise.txt"]
		assert report["ok"] is True  # residue is a warning, never a problem
		assert len(report["warnings"]) == 2

	def test_dump_carries_no_bearer_credential(self, instance):
		"""Protocol 8 has no credential to leak, and this asserts it stays that
		way. The protocol-7 defect was exactly this: an unauthenticated
		read-only view printed the only authentication factor, and one
		participant authenticated as another using a value read from it."""
		with b6.open_instance(instance) as st:
			send_one(st)
			claim = st.claim("acme.implementer")
			st.close_claim(claim["claim_id"], participant="acme.implementer")
			nid = st.send_notice("hq.lead", kind="ann", body=b"x")
			st.see("acme.reviewer")
			assert nid
		snapshot = b6.dump(instance)

		def walk(node, path=""):
			if isinstance(node, dict):
				for key, value in node.items():
					assert "seed" not in key.lower(), f"credential key at {path}.{key}"
					assert "actor" not in key.lower(), f"actor key at {path}.{key}"
					walk(value, f"{path}.{key}")
			elif isinstance(node, list):
				for i, value in enumerate(node):
					walk(value, f"{path}[{i}]")
		walk(snapshot)
		assert "seed" not in json.dumps(snapshot).lower()

	def test_dump_redacts_bodies(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st, body=b"secret payload")
		snapshot = b6.dump(instance)
		assert snapshot["messages"][0]["state"] == "pending"
		assert "bytes>" in snapshot["contents"][0]["body"]

	def test_materialize_byte_exact_and_idempotent(self, instance, tmp_path):
		with b6.open_instance(instance) as st:
			mid = send_one(st, body=b"# durable record\\n")
		out = tmp_path / "projections"
		out.mkdir()
		path1 = b6.materialize(instance, mid, str(out))
		assert open(path1, "rb").read() == b"# durable record\\n"
		path2 = b6.materialize(instance, mid, str(out))
		assert path2 == path1  # idempotent re-emit

	def test_materialize_refuses_scrubbed(self, instance, tmp_path):
		with b6.open_instance(instance) as st:
			mid = send_one(st, body=b"gone", retention="transient")
			claim = st.claim("acme.implementer")
			st.close_claim(claim["claim_id"], participant=claim["participant"])
		with pytest.raises(b6.BatonError, match="transient"):
			b6.materialize(instance, mid, str(tmp_path))


class TestCli:
	def _run(self, *argv):
		import io, contextlib
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			code = b6.main(list(argv))
		return code, out.getvalue()

	def test_cli_roundtrip(self, tmp_path, monkeypatch):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		code, _ = self._run("--config", config_path, "init")
		assert code == 0
		monkeypatch.setattr("sys.stdin", type("S", (), {"buffer": __import__("io").BytesIO(b"question body")})())
		code, out = self._run("--config", config_path, "send",
		                      "--participant", "acme.reviewer", "--to", "acme.implementer",
		                      "--kind", "question", "--thread", "t1")
		assert code == 0
		code, out = self._run("--config", config_path, "claim",
		                      "--participant", "acme.implementer")
		assert code == 0
		delivery = json.loads(out)
		claim_id = delivery["claim"]["claim_id"]
		assert delivery["message"]["body"]["utf8"] == "question body"
		assert delivery["message"]["attachment"] is None
		monkeypatch.setattr("sys.stdin", type("S", (), {"buffer": __import__("io").BytesIO(b"answer body")})())
		code, out = self._run("--config", config_path, "reply", claim_id,
		                      "--participant", "acme.implementer", "--kind", "answer", "--outcome", "done")
		assert code == 0
		assert json.loads(out)["already_committed"] is False
		code, out = self._run("--config", config_path, "scan")
		assert code == 0
		assert len(json.loads(out)["pending"]) == 1  # the reply

	def test_cli_exit_codes(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		self._run("--config", config_path, "init")
		code, _ = self._run("--config", config_path, "claim",
		                    "--participant", "acme.implementer")
		assert code == b6.EXIT_NONE
		code, _ = self._run("--config", config_path, "maintenance-enter",
		                    "--participant", "hq.lead", "--reason", "gate")
		assert code == 0
		code, _ = self._run("--config", config_path, "send",
		                    "--participant", "acme.reviewer", "--to", "acme.implementer",
		                    "--kind", "k", "--body", "/dev/null")
		assert code == b6.EXIT_GATED
		code, _ = self._run("--config", config_path, "doctor")
		assert code == 0

	def test_cli_missing_config(self):
		code, _ = self._run("scan")
		assert code == b6.EXIT_PROTOCOL


# ---------------------------------------------------------------------------
# wait/CLI round-2 pins: lossless delivery, CLI totality, event matrix,
# doctor logical checks, durable-only materialize
# ---------------------------------------------------------------------------



def _raw_corrupt(config_path, mutate):
	"""EXPLICIT test-only corruption construction: drop all guard triggers,
	apply the mutation, restore the exact schema triggers. Production
	mutation paths stay guarded; this simulates offline tampering."""
	db = os.path.join(os.path.dirname(config_path), "mailbox.sqlite3")
	conn = sqlite3.connect(db)
	try:
		for (name,) in conn.execute(
				"SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
			conn.execute(f"DROP TRIGGER {name}")
		mutate(conn)
		for sql in b6._TRIGGERS.values():
			conn.execute(sql)
		conn.commit()
	finally:
		conn.close()

class TestLosslessDelivery:
	def test_non_utf8_and_empty_bodies(self, store):
		import base64
		raw = bytes(range(256))
		mid = store.send("acme.reviewer", "acme.implementer",
		                 kind="blob", body=raw)
		claim = store.claim("acme.implementer", message_id=mid)
		delivery = b6._delivery(store, claim)
		body = delivery["message"]["body"]
		assert base64.b64decode(body["base64"]) == raw
		assert body["size"] == 256
		assert "utf8" not in body
		mid2 = store.send("acme.reviewer", "acme.implementer",
		                  kind="empty", body=b"")
		claim2 = store.claim("acme.implementer", message_id=mid2)
		body2 = b6._delivery(store, claim2)["message"]["body"]
		assert body2["size"] == 0 and body2["utf8"] == ""

	def test_transient_body_readable_after_claim_until_consumed(self, store):
		mid = store.send("acme.reviewer", "acme.implementer",
		                 kind="t", body=b"still here", retention="transient")
		claim = store.claim("acme.implementer", message_id=mid)
		delivery = b6._delivery(store, claim)
		assert delivery["message"]["body"]["utf8"] == "still here"
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		post = b6._delivery(store, dict(claim))
		assert post["message"]["body"] is None
		assert post["message"]["content_sha256"] is not None

	def test_attachment_delivery_tuple(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		(root / "e.md").write_bytes(b"evidence")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as store:
			mid = store.send("acme.reviewer", "acme.implementer",
			                 kind="ev", body=None, attach={"root_id": "evidence", "path": "e.md"})
			claim = store.claim("acme.implementer", message_id=mid)
			delivery = b6._delivery(store, claim)
			assert delivery["message"]["body"] is None
			att = delivery["message"]["attachment"]
			assert att["root_id"] == "evidence" and att["path"] == "e.md"
			assert att["sha256"] and att["size"] == 8 and att["generation"] == 1


class TestCliTotality:
	def _run(self, *argv, stdin=b""):
		import io, contextlib
		out = io.StringIO()
		err = io.StringIO()
		import sys as _sys
		old_stdin = _sys.stdin
		_sys.stdin = type("S", (), {"buffer": __import__("io").BytesIO(stdin)})()
		try:
			with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
				code = b6.main(list(argv))
		finally:
			_sys.stdin = old_stdin
		return code, out.getvalue(), err.getvalue()

	def _instance(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "w") as handle:
			json.dump(make_config(), handle)
		b6.main(["--config", config_path, "init"])
		return config_path

	def test_usage_error_is_validation_code(self, tmp_path):
		code, _, _ = self._run("no-such-command")
		assert code == b6.EXIT_PROTOCOL
		code, _, _ = self._run("--help")
		assert code == 0

	def test_body_attach_mutually_exclusive_at_parser(self, tmp_path):
		config_path = self._instance(tmp_path)
		code, _, _ = self._run("--config", config_path, "send",
		                       "--participant", "acme.reviewer", "--to", "acme.implementer", "--kind", "k",
		                       "--body", "/dev/null", "--attach", "r:p")
		assert code == b6.EXIT_PROTOCOL  # argparse mutual exclusion -> 4

	def test_missing_body_file_clean(self, tmp_path):
		config_path = self._instance(tmp_path)
		code, _, err = self._run("--config", config_path, "send",
		                         "--participant", "acme.reviewer", "--to", "acme.implementer", "--kind", "k",
		                         "--body", "/nonexistent/body.txt")
		assert code == b6.EXIT_PROTOCOL
		assert "unreadable" in err and "Traceback" not in err

	def test_bad_attach_syntax_clean(self, tmp_path):
		config_path = self._instance(tmp_path)
		code, _, err = self._run("--config", config_path, "send",
		                         "--participant", "acme.reviewer", "--to", "acme.implementer", "--kind", "k",
		                         "--attach", "no-colon")
		assert code == b6.EXIT_PROTOCOL
		assert "ROOT_ID" in err

	def test_malformed_utf8_config_clean(self, tmp_path):
		config_path = str(tmp_path / "baton.json")
		with open(config_path, "wb") as handle:
			handle.write(bytes([0xFF, 0xFE]) + b" not json")
		code, _, err = self._run("--config", config_path, "scan")
		assert code == b6.EXIT_PROTOCOL
		assert "UTF-8" in err and "Traceback" not in err

	def test_bad_wait_numerics_clean(self, tmp_path):
		config_path = self._instance(tmp_path)
		for bad in ("nan", "inf", "-1"):
			code, _, err = self._run("--config", config_path, "wait",
			                         "--participant", "acme.implementer", "--timeout", bad)
			assert code == b6.EXIT_PROTOCOL
		code, _, _ = self._run("--config", config_path, "wait",
		                       "--participant", "acme.implementer", "--timeout", "0.1", "--interval", "0")
		assert code == b6.EXIT_PROTOCOL

	def test_cli_attachment_path(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		(root / "e.md").write_bytes(b"evidence")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.main(["--config", config_path, "init"])
		code, out, _ = self._run("--config", config_path, "send",
		                         "--participant", "acme.reviewer", "--to", "acme.implementer",
		                         "--kind", "ev", "--attach", "evidence:e.md")
		assert code == 0
		code, out, _ = self._run("--config", config_path, "claim",
		                         "--participant", "acme.implementer")
		assert code == 0
		delivery = json.loads(out)
		assert delivery["message"]["attachment"]["path"] == "e.md"
		assert delivery["message"]["body"] is None


class TestEventMatrix:
	def test_arm_race_closed_by_requery(self, instance, monkeypatch):
		sent = {}
		def publish_during_arm(point):
			if point == "wait:armed" and not sent:
				sent["done"] = True
				with b6.open_instance(instance) as st:
					send_one(st)
		monkeypatch.setattr(b6, "_FAULT_HOOK", publish_during_arm)
		start = _time.monotonic()
		result = b6.wait_for_message(instance, "acme.implementer",
		                            timeout_s=30, rescan_interval_s=25)
		assert result["claim"]["state"] == "active"
		assert _time.monotonic() - start < 10  # requery caught it; no event needed

	def test_wal_checkpoint_reset_still_wakes(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st)
			claim = st.claim("acme.implementer")
			st.close_claim(claim["claim_id"], participant=claim["participant"])
			st.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
		def sender():
			_time.sleep(0.4)
			with b6.open_instance(instance) as st:
				send_one(st)
		thread = threading.Thread(target=sender)
		thread.start()
		result = b6.wait_for_message(instance, "acme.implementer",
		                            timeout_s=30, rescan_interval_s=20)
		thread.join()
		assert result["claim"]["state"] == "active"

	@pytest.mark.parametrize("flag_name,mask", [
		("overflow", 0x00004000), ("ignored", 0x00008000),
		("move_self", 0x00000800), ("delete_self", 0x00000400),
		("unmount", 0x00002000)])
	def test_decoder_classifies_each_disruption(self, flag_name, mask):
		import struct
		record = struct.pack("iIII", 1, mask, 0, 0)
		flags = b6._decode_inotify(record)
		assert flags["revalidate"] is True
		named = struct.pack("iIII", 1, 0x00000002, 0, 16) + b"mailbox.sqlite3\x00"
		flags = b6._decode_inotify(named)
		assert flags["revalidate"] is False and flags["relevant"] is True
		other = struct.pack("iIII", 1, 0x00000002, 0, 16) + b"unrelated.file\x00\x00"
		assert b6._decode_inotify(other)["relevant"] is False

	def test_armed_mask_contains_required_bits(self):
		for bit in (b6._IN_CREATE, b6._IN_DELETE, b6._IN_MODIFY, b6._IN_MOVED_TO,
		            b6._IN_MOVE_SELF, b6._IN_DELETE_SELF, b6._IN_UNMOUNT):
			assert b6._WATCH_MASK & bit

	@pytest.mark.parametrize("flag_name,mask", [
		("overflow", 0x00004000), ("ignored", 0x00008000),
		("move_self", 0x00000800), ("unmount", 0x00002000)])
	def test_decoded_disruption_forces_validated_reopen(self, instance, monkeypatch,
	                                                    flag_name, mask):
		import struct
		record = struct.pack("iIII", 1, mask, 0, 0)
		decoded = b6._decode_inotify(record)
		assert decoded["revalidate"] is True
		opens = {"count": 0}
		real_open = b6.open_instance
		def counting_open(*args, **kwargs):
			opens["count"] += 1
			return real_open(*args, **kwargs)
		monkeypatch.setattr(b6, "open_instance", counting_open)
		class FakeWatch:
			calls = 0
			def __init__(self, _dir):
				pass
			def close(self):
				pass
			def poll(self, timeout_s):
				FakeWatch.calls += 1
				if FakeWatch.calls == 1:
					return dict(decoded)  # the REAL decoder's verdict for this mask
				return {"revalidate": False, "relevant": False}
		monkeypatch.setattr(b6, "_InotifyWatch", FakeWatch)
		def sender():
			_time.sleep(0.5)
			with real_open(instance) as st:
				send_one(st)
		thread = threading.Thread(target=sender)
		thread.start()
		before = opens["count"]
		result = b6.wait_for_message(instance, "acme.implementer",
		                             timeout_s=30, rescan_interval_s=0.2)
		thread.join()
		assert result["claim"]["state"] == "active"
		assert opens["count"] > before + 1  # requery reopened with full validation

	def test_wal_reset_while_blocked_still_wakes(self, instance, monkeypatch):
		armed = threading.Event()
		def on_arm(point):
			if point == "wait:armed":
				armed.set()
		monkeypatch.setattr(b6, "_FAULT_HOOK", on_arm)
		def churn_and_send():
			assert armed.wait(20)  # the waiter is DEMONSTRABLY armed and blocking
			_time.sleep(0.2)  # let it enter poll()
			with b6.open_instance(instance) as st:
				st.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # resets -wal under the waiter
			with b6.open_instance(instance) as st:
				send_one(st)
		thread = threading.Thread(target=churn_and_send)
		thread.start()
		result = b6.wait_for_message(instance, "acme.implementer",
		                             timeout_s=30, rescan_interval_s=20)
		thread.join()
		assert result["claim"]["state"] == "active"

	def test_degraded_sleep_receives_configured_interval(self, instance, monkeypatch):
		class Broken:
			def __init__(self, _dir):
				raise OSError("no inotify")
		monkeypatch.setattr(b6, "_InotifyWatch", Broken)
		sleeps = []
		import time as _t
		real_sleep = _t.sleep
		def recording_sleep(seconds):
			sleeps.append(seconds)
			if len(sleeps) == 1:
				with b6.open_instance(instance) as st:
					send_one(st)  # published during the first degraded sleep
			real_sleep(0.01)
		monkeypatch.setattr(_t, "sleep", recording_sleep)
		result = b6.wait_for_message(instance, "acme.implementer",
		                             timeout_s=None, rescan_interval_s=3.0)
		assert result["claim"]["state"] == "active"
		assert sleeps[0] == 3.0  # the CONFIGURED interval reached sleep() exactly

	def test_gate_while_blocked_stands_down(self, instance):
		def gater():
			_time.sleep(0.4)
			b6.maintenance_enter(instance, participant="hq.lead",
			                     reason="mid-wait gate")
		thread = threading.Thread(target=gater)
		thread.start()
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer",
			                    timeout_s=30, rescan_interval_s=0.2)
		thread.join()
		assert excinfo.value.exit_code == b6.EXIT_GATED

	def test_invalid_wait_inputs_rejected(self, instance):
		import math
		for bad_timeout in (float("nan"), float("inf"), -1, True):
			with pytest.raises(b6.BatonError, match="finite|timeout"):
				b6.wait_for_message(instance, "acme.implementer",
				                    timeout_s=bad_timeout, rescan_interval_s=1)
		for bad_interval in (0, -5, float("nan"), True):
			with pytest.raises(b6.BatonError, match="rescan"):
				b6.wait_for_message(instance, "acme.implementer",
				                    timeout_s=0.1, rescan_interval_s=bad_interval)


def notice_one(store, body=b"all hands", kind="announcement", ttl_seconds=None):
	return store.send_notice("hq.lead", kind=kind,
	                         body=body, ttl_seconds=ttl_seconds)


class TestWaitNoticeDelivery:
	"""A broadcast notice must WAKE and be DELIVERED by `wait`. Before this
	work the wake happened and the delivery did not: the waiter requeried only
	claimable directed messages, so an unseen notice was reachable solely
	through `see` — a command a blocked waiter is by definition not running."""

	def _run(self, *argv):
		import io, contextlib
		out = io.StringIO()
		err = io.StringIO()
		with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
			code = b6.main(list(argv))
		return code, out.getvalue(), err.getvalue()

	# -- wake + delivery ---------------------------------------------------

	def test_notice_wakes_blocked_wait(self, instance):
		def publisher():
			_time.sleep(0.5)
			with b6.open_instance(instance) as st:
				notice_one(st, body=b"broadcast")
		thread = threading.Thread(target=publisher)
		thread.start()
		start = _time.monotonic()
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=30, rescan_interval_s=20)
		elapsed = _time.monotonic() - start
		thread.join()
		assert result["notice"]["body"]["utf8"] == "broadcast"
		assert elapsed < 15  # woken by the watch, not the 20s safety rescan

	def test_existing_unseen_notice_delivered_immediately(self, instance):
		with b6.open_instance(instance) as st:
			nid = notice_one(st)
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert set(result) == {"notice"}  # a notice delivery is never claim-shaped
		assert result["notice"]["id"] == nid
		assert result["notice"]["from_participant"] == "hq.lead"

	# -- no claim, ever ----------------------------------------------------

	def test_notice_delivery_creates_no_claim(self, instance):
		with b6.open_instance(instance) as st:
			nid = notice_one(st)
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert result["notice"]["id"] == nid
		with b6.open_instance(instance) as st:
			assert st.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
			assert st.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
			assert st.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] == 0
			# the receipt is the ONLY state the delivery wrote
			assert [tuple(row) for row in st.conn.execute(
				"SELECT participant FROM notice_seen")] == [
				("acme.implementer",)]
		assert b6.doctor(instance)["ok"] is True

	# -- receipt: written once, atomically ---------------------------------

	def test_notice_not_delivered_twice(self, instance):
		with b6.open_instance(instance) as st:
			nid = notice_one(st)
		first = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert first["notice"]["id"] == nid
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=0.4, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE

	def test_notice_receipt_atomic_with_selection(self, instance, monkeypatch):
		"""Selection and receipt commit together: a crash after the receipt
		insert but before commit leaves NO receipt, and the notice stays
		deliverable."""
		with b6.open_instance(instance) as st:
			nid = notice_one(st, body=b"atomic")
		class Boom(Exception):
			pass
		def blow_up(point):
			if point == "see:selected":
				raise Boom("crash between receipt insert and commit")
		monkeypatch.setattr(b6, "_FAULT_HOOK", blow_up)
		with pytest.raises(Boom):
			b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		monkeypatch.setattr(b6, "_FAULT_HOOK", None)
		with b6.open_instance(instance) as st:
			assert st.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert result["notice"]["id"] == nid

	def test_receipt_survives_crash_after_commit(self, instance, monkeypatch):
		"""The other half of the atomicity contract: once the receipt commits,
		it stays committed even if the consumer dies before it can act on the
		bytes. That is the documented at-most-once property — broadcast has no
		acknowledgement to wait for, so a post-commit crash loses the notice
		rather than redelivering it."""
		with b6.open_instance(instance) as st:
			nid = notice_one(st, body=b"lost to the crash")
		class Died(Exception):
			pass
		def die_after_commit(_notice):
			raise Died("consumer died holding the delivery")
		monkeypatch.setattr(b6, "_notice_delivery", die_after_commit)
		with pytest.raises(Died):
			b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		monkeypatch.undo()
		with b6.open_instance(instance) as st:
			assert [tuple(row) for row in st.conn.execute(
				"SELECT notice_id, participant FROM notice_seen")] == [
				(nid, "acme.implementer")]
		# the same participant does NOT get a second chance...
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=0.4, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE
		# ...and the loss is scoped to that receipt, not to the notice: a
		# different participant still receives it
		other = b6.wait_for_message(instance, "acme.reviewer", timeout_s=5)
		assert other["notice"]["id"] == nid

	def test_expired_oldest_does_not_mask_live_notice(self, instance):
		"""TTL filtering happens in Python, after the ordered SELECT, so an
		expired oldest row must be skipped rather than consuming the limit. A
		future `LIMIT 1` pushed into SQL would silently reintroduce exactly
		this: `wait` blocking forever behind a dead notice."""
		with b6.open_instance(instance) as st:
			dead = notice_one(st, body=b"already dead", kind="tick", ttl_seconds=1)
		_time.sleep(1.2)
		with b6.open_instance(instance) as st:
			live = notice_one(st, body=b"still live", kind="announcement")
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert result["notice"]["id"] == live
		assert result["notice"]["body"]["utf8"] == "still live"
		with b6.open_instance(instance) as st:
			# the expired notice was skipped, never marked seen
			assert [row[0] for row in st.conn.execute(
				"SELECT notice_id FROM notice_seen")] == [live]
			assert dead != live

	def test_author_receives_own_notice(self, instance):
		"""Parity with `see`, which has never excluded self-authored notices.
		The receipt key is (notice_id, participant), so an author's own
		waiter is just another reader. Pinned here because the contract is now
		documented; if Slawomir rules the other way, `see` and `wait` must
		change together — this test is the tripwire for changing only one."""
		with b6.open_instance(instance) as st:
			nid = st.send_notice("acme.implementer",
			                     kind="announcement", body=b"self broadcast")
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert result["notice"]["id"] == nid
		assert result["notice"]["from_participant"] == "acme.implementer"
		with b6.open_instance(instance) as st:
			assert st.see("acme.implementer") == []

	def test_wait_and_see_share_one_receipt(self, instance):
		"""`wait` and `see` read the same receipt table through the same code
		path, so neither can redeliver what the other consumed."""
		with b6.open_instance(instance) as st:
			nid = notice_one(st)
		delivered = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert delivered["notice"]["id"] == nid
		with b6.open_instance(instance) as st:
			assert st.see("acme.implementer") == []
			# the reverse direction: consumed by `see`, invisible to `wait`
			assert [n["id"] for n in st.see("acme.reviewer",)] == [nid]
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.reviewer",
			                    timeout_s=0.4, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE

	# -- directed-message parity -------------------------------------------

	def test_directed_message_wins_over_notice(self, instance):
		"""Claimable work is never delayed behind advisory broadcast, and the
		directed delivery shape is untouched."""
		with b6.open_instance(instance) as st:
			notice_one(st, body=b"broadcast")  # published FIRST
			mid = send_one(st, body=b"directed")
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert set(result) == {"claim", "message"}
		assert result["message"]["id"] == mid
		assert result["message"]["body"]["utf8"] == "directed"
		assert result["claim"]["state"] == "active"
		with b6.open_instance(instance) as st:
			# no receipt written while a directed message was the delivery
			assert st.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0

	def test_notice_delivered_after_directed_drains(self, instance):
		with b6.open_instance(instance) as st:
			nid = notice_one(st, body=b"broadcast")
			send_one(st, body=b"directed")
		first = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert first["message"]["body"]["utf8"] == "directed"
		second = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert second["notice"]["id"] == nid

	# -- independent per-participant delivery ------------------------------

	def test_notice_delivered_to_each_participant(self, instance):
		with b6.open_instance(instance) as st:
			nid = notice_one(st)
		for participant in ("acme.implementer", "acme.reviewer"):
			result = b6.wait_for_message(instance, participant,
			                             timeout_s=5)
			assert result["notice"]["id"] == nid

	def test_notice_receipt_is_per_participant(self, instance):
		"""Actors are gone: a notice is seen once per participant, and each
		participant receives its own independent copy."""
		with b6.open_instance(instance) as st:
			nid = notice_one(st)
		for participant in ("acme.implementer", "acme.reviewer"):
			result = b6.wait_for_message(instance, participant, timeout_s=5)
			assert result["notice"]["id"] == nid
		with b6.open_instance(instance) as st:
			assert st.conn.execute(
				"SELECT COUNT(*) FROM notice_seen WHERE notice_id=?", (nid,)).fetchone()[0] == 2
			assert [tuple(r) for r in st.conn.execute(
				"SELECT participant FROM notice_seen ORDER BY participant")] == [
				("acme.implementer",), ("acme.reviewer",)]

	# -- the wake paths ----------------------------------------------------

	def test_notice_delivered_on_degraded_polling(self, instance, monkeypatch):
		class Broken:
			def __init__(self, _dir):
				raise OSError("inotify unavailable")
		monkeypatch.setattr(b6, "_InotifyWatch", Broken)
		def publisher():
			_time.sleep(0.4)
			with b6.open_instance(instance) as st:
				notice_one(st, body=b"polled")
		thread = threading.Thread(target=publisher)
		thread.start()
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=30, rescan_interval_s=0.2)
		thread.join()
		assert result["notice"]["body"]["utf8"] == "polled"

	def test_notice_arm_race_closed_by_requery(self, instance, monkeypatch):
		"""A notice published in the window between the first query and the
		armed watch is caught by the post-arm requery, not by the rescan."""
		published = {}
		def publish_during_arm(point):
			if point == "wait:armed" and not published:
				published["done"] = True
				with b6.open_instance(instance) as st:
					notice_one(st, body=b"raced")
		monkeypatch.setattr(b6, "_FAULT_HOOK", publish_during_arm)
		start = _time.monotonic()
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=30, rescan_interval_s=25)
		assert result["notice"]["body"]["utf8"] == "raced"
		assert _time.monotonic() - start < 10  # requery caught it; no event needed

	# -- the idle waiter stays read-only -----------------------------------

	def test_idle_wait_takes_no_write_transaction(self, instance, monkeypatch):
		"""`see` transacts, but a waiter polls indefinitely. An idle poll must
		stay read-only: BEGIN IMMEDIATE on every cycle would contend with real
		writers, and an unrelated transient busy raises EXIT_RACE, which
		stands the waiter down. Before the read-only probe this loop opened a
		write transaction per poll."""
		begins = []
		real_begin = b6.Store._txn_begin
		def counting_begin(self, verb, *args, **kwargs):
			begins.append(verb)
			return real_begin(self, verb, *args, **kwargs)
		monkeypatch.setattr(b6.Store, "_txn_begin", counting_begin)
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=0.5, rescan_interval_s=0.02)
		assert excinfo.value.exit_code == b6.EXIT_NONE
		assert begins == []  # many poll cycles, zero write transactions
		with b6.open_instance(instance) as st:
			notice_one(st)
		begins.clear()
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert result["notice"]["from_participant"] == "hq.lead"
		assert begins == ["see"]  # exactly one, and only once there is work

	# -- TTL, gates, timeout -----------------------------------------------

	def test_expired_notice_never_delivered(self, instance, monkeypatch):
		begins = []
		real_begin = b6.Store._txn_begin
		def counting_begin(self, verb, *args, **kwargs):
			begins.append(verb)
			return real_begin(self, verb, *args, **kwargs)
		with b6.open_instance(instance) as st:
			notice_one(st, body=b"short", kind="tick", ttl_seconds=1)
		_time.sleep(1.2)
		monkeypatch.setattr(b6.Store, "_txn_begin", counting_begin)
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=0.4, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE
		# an expired notice must not make the waiter spin on the write lock
		assert begins == []
		with b6.open_instance(instance) as st:
			# an expired notice is never marked seen either
			assert st.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0

	def test_notice_path_respects_gate(self, instance):
		with b6.open_instance(instance) as st:
			notice_one(st)
		b6.maintenance_enter(instance, participant="hq.lead",
		                     reason="gate")
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert excinfo.value.exit_code == b6.EXIT_GATED

	def test_seen_only_notice_times_out_clean(self, instance):
		with b6.open_instance(instance) as st:
			notice_one(st)
			st.see("acme.implementer")
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=0.4, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE
		assert "notice" in str(excinfo.value)  # the diagnostic covers both channels

	# -- lossless body -----------------------------------------------------

	@pytest.mark.parametrize("body", [b"\xc3\xa9 broadcast\n", b"\xff\xfe\x00binary"])
	def test_notice_body_lossless(self, instance, body):
		import base64, hashlib as _h
		with b6.open_instance(instance) as st:
			notice_one(st, body=body)
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		notice = result["notice"]
		rep = notice["body"]
		assert base64.b64decode(rep["base64"]) == body
		assert rep["size"] == len(body)
		assert rep["sha256"] == _h.sha256(body).hexdigest() == notice["content_sha256"]
		try:
			decoded = body.decode("utf-8")
		except UnicodeDecodeError:
			assert "utf8" not in rep  # undecodable bytes travel base64-only
		else:
			assert rep["utf8"] == decoded
		assert notice["kind"] == "announcement"
		assert notice["seen_ts"] and notice["created_ts"]
		assert notice["ttl_seconds"] == b6.DEFAULT_NOTICE_TTL_SECONDS
		assert json.loads(json.dumps(result)) == result  # delivery is JSON-clean

	def test_notice_delivery_refuses_corrupt_body(self, instance):
		with b6.open_instance(instance) as st:
			notice_one(st, body=b"real bytes")
		_raw_corrupt(instance, lambda conn: conn.execute(
			"UPDATE contents SET body=X'6861636b6564'"))  # 'hacked'
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert excinfo.value.exit_code == b6.EXIT_DAMAGE

	# -- CLI ---------------------------------------------------------------

	def test_cli_wait_delivers_notice(self, instance):
		code, out, _ = self._run(
			"--config", instance, "send-notice", "--participant", "hq.lead",
			"--kind", "announcement",
			"--body", "/dev/stdin")
		assert code == 0
		code, out, _ = self._run(
			"--config", instance, "wait", "--participant", "acme.implementer",
			"--timeout", "5")
		assert code == 0
		delivery = json.loads(out)
		assert "claim" not in delivery
		assert delivery["notice"]["kind"] == "announcement"
		# and the CLI `see` agrees it is consumed
		code, out, _ = self._run(
			"--config", instance, "see", "--participant", "acme.implementer")
		assert code == 0 and json.loads(out)["notices"] == []

	# -- `see` itself is unregressed ---------------------------------------

	def test_see_limit_partial_drain(self, store):
		first = notice_one(store, body=b"1", kind="a")
		second = notice_one(store, body=b"2", kind="b")
		stamps = {row[0]: row[1] for row in
		          store.conn.execute("SELECT id, created_ts FROM notices")}
		oldest, newest = sorted((first, second), key=lambda i: (stamps[i], i))
		one = store.see("acme.implementer", limit=1)
		assert [n["id"] for n in one] == [oldest]
		rest = store.see("acme.implementer")
		assert [n["id"] for n in rest] == [newest]  # unlimited call still full-drains
		assert store.see("acme.implementer") == []

	@pytest.mark.parametrize("bad", [0, -1, 1.5, "1", True])
	def test_see_rejects_bad_limit(self, store, bad):
		notice_one(store)
		with pytest.raises(b6.BatonError, match="limit"):
			store.see("acme.implementer", limit=bad)


def _attach_instance(tmp_path):
	"""An instance whose config declares an attachment root, plus that root."""
	root = tmp_path / "src"
	root.mkdir()
	config_path = str(tmp_path / "baton.json")
	cfg = make_config()
	cfg["roots"] = {"src": str(root)}
	with open(config_path, "w") as handle:
		json.dump(cfg, handle)
	b6.init_instance(config_path)
	return config_path, root


def _send_attached(config_path, root, name, body=b"original bytes\n"):
	"""Publish an attachment-backed message and return (message_id, path)."""
	path = root / name
	path.write_bytes(body)
	with b6.open_instance(config_path) as st:
		mid = st.send("acme.reviewer", "acme.implementer",
		              kind="evidence", body=None,
		              attach={"root_id": "src", "path": name})
	return mid, path


class TestDamagedAttachmentQueue:
	"""A message whose pinned attachment changed after publication must not
	block the messages behind it. Before this work `Store.claim` selected the
	single oldest pending message, verified its pin, and had no fallthrough —
	so one damaged message made every plain `claim`/`wait` for that recipient
	fail with EXIT_DAMAGE permanently, and the damaged message could not be
	claimed, closed, or collected in order to clear it."""

	def test_damaged_head_does_not_block_healthy_message(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")  # invalidates the pin
		with b6.open_instance(config_path) as st:
			healthy = send_one(st, body=b"still deliverable")
			claim = st.claim("acme.implementer")
			assert claim["message_id"] == healthy
			delivery = b6._delivery(st, claim)
		assert delivery["message"]["body"]["utf8"] == "still deliverable"
		with b6.open_instance(config_path) as st:
			# the damaged message is untouched: still pending, still unclaimed
			assert st.get_message(damaged)["state"] == "pending"
			assert st.conn.execute(
				"SELECT COUNT(*) FROM claims WHERE message_id=?", (damaged,)).fetchone()[0] == 0

	def test_wait_receives_message_published_behind_damage(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		_, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		def sender():
			_time.sleep(0.4)
			with b6.open_instance(config_path) as st:
				send_one(st, body=b"published later")
		thread = threading.Thread(target=sender)
		thread.start()
		result = b6.wait_for_message(config_path, "acme.implementer", timeout_s=30, rescan_interval_s=20)
		thread.join()
		assert result["message"]["body"]["utf8"] == "published later"

	def test_damaged_only_queue_waits_without_spinning(self, tmp_path, monkeypatch):
		"""Damage must read as 'nothing eligible', not as an error and not as
		a reason to churn: the waiter stays live, opens no write transaction,
		and creates no claim."""
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		begins = []
		real_begin = b6.Store._txn_begin
		def counting_begin(self, verb, *args, **kwargs):
			begins.append(verb)
			return real_begin(self, verb, *args, **kwargs)
		monkeypatch.setattr(b6.Store, "_txn_begin", counting_begin)
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_message(config_path, "acme.implementer", timeout_s=0.5, rescan_interval_s=0.02)
		assert excinfo.value.exit_code == b6.EXIT_NONE  # eligible-nothing, not damage
		assert begins == []
		with b6.open_instance(config_path) as st:
			assert st.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
			assert st.get_message(damaged)["state"] == "pending"

	def test_explicit_claim_of_damaged_still_fails_closed(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		with b6.open_instance(config_path) as st:
			with pytest.raises(b6.BatonError) as excinfo:
				st.claim("acme.implementer", message_id=damaged)
			assert excinfo.value.exit_code == b6.EXIT_DAMAGE
			assert "pinned hash" in str(excinfo.value)
			assert st.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
			assert st.get_message(damaged)["state"] == "pending"

	def test_skipped_damage_stays_pending_and_visible(self, tmp_path):
		"""Skipping is not erasure: the damaged message keeps its pin and
		stays inventoried, and `scan` reports it in a machine-readable way
		without disturbing the healthy pending list."""
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		with b6.open_instance(config_path) as st:
			healthy = send_one(st, body=b"fine")
			report = st.scan("acme.implementer")
		assert sorted(m["id"] for m in report["pending"]) == sorted([damaged, healthy])
		assert [d["id"] for d in report["damaged"]] == [damaged]
		entry = report["damaged"][0]
		assert entry["to_participant"] == "acme.implementer"
		assert entry["attachment"]["path"] == "EVIDENCE.md"
		assert entry["attachment"]["root_id"] == "src"
		assert "pinned hash" in entry["failure"]
		assert b6.doctor(config_path)["ok"] is False  # still a problem until dispositioned

	def test_scan_damaged_empty_when_healthy(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		_send_attached(config_path, root, "EVIDENCE.md")
		with b6.open_instance(config_path) as st:
			send_one(st)
			report = st.scan()
		assert report["damaged"] == []
		assert len(report["pending"]) == 2
		assert b6.doctor(config_path)["ok"] is True

	def test_healthy_attachment_claim_reply_unchanged(self, tmp_path):
		"""Parity: an undamaged attachment message still claims, delivers its
		pinned tuple, and completes through reply exactly as before."""
		config_path, root = _attach_instance(tmp_path)
		mid, _ = _send_attached(config_path, root, "EVIDENCE.md", body=b"intact\n")
		with b6.open_instance(config_path) as st:
			claim = st.claim("acme.implementer")
			assert claim["message_id"] == mid
			delivery = b6._delivery(st, claim)
			assert set(delivery) == {"claim", "message"}
			assert delivery["message"]["attachment"]["path"] == "EVIDENCE.md"
			assert delivery["message"]["body"] is None
			result = st.reply(claim["claim_id"], participant=claim["participant"],
			                  kind="response", body=b"ack")
			assert result["already_committed"] is False
			assert st.get_message(mid)["state"] == "completed"

	def test_ordering_is_deterministic_across_multiple_damaged(self, tmp_path):
		"""Skipping preserves (created_ts, id) order over the healthy
		remainder rather than reshuffling the queue."""
		config_path, root = _attach_instance(tmp_path)
		_, p1 = _send_attached(config_path, root, "a.md")
		with b6.open_instance(config_path) as st:
			first = send_one(st, body=b"first healthy")
		_, p2 = _send_attached(config_path, root, "b.md")
		with b6.open_instance(config_path) as st:
			second = send_one(st, body=b"second healthy")
		p1.write_bytes(b"mutated\n")
		p2.write_bytes(b"mutated\n")
		with b6.open_instance(config_path) as st:
			# created_ts is second-resolution, so the total order is
			# (created_ts, id) — derive the expectation rather than assuming
			# publication order survived a same-second tie.
			stamps = {row[0]: row[1] for row in
			          st.conn.execute("SELECT id, created_ts FROM messages")}
			expected = sorted([first, second], key=lambda i: (stamps[i], i))
			assert [st.claim("acme.implementer")["message_id"],
			        st.claim("acme.implementer")["message_id"]] == expected
			with pytest.raises(b6.BatonError) as excinfo:
				st.claim("acme.implementer")
			assert excinfo.value.exit_code == b6.EXIT_NONE  # only damage left
			assert "damaged attachments" in str(excinfo.value)

	def test_degraded_polling_also_skips_damage(self, tmp_path, monkeypatch):
		class Broken:
			def __init__(self, _dir):
				raise OSError("inotify unavailable")
		monkeypatch.setattr(b6, "_InotifyWatch", Broken)
		config_path, root = _attach_instance(tmp_path)
		_, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		def sender():
			_time.sleep(0.4)
			with b6.open_instance(config_path) as st:
				send_one(st, body=b"polled past damage")
		thread = threading.Thread(target=sender)
		thread.start()
		result = b6.wait_for_message(config_path, "acme.implementer", timeout_s=30, rescan_interval_s=0.2)
		thread.join()
		assert result["message"]["body"]["utf8"] == "polled past damage"

	def test_notice_still_delivered_when_only_damage_pends(self, tmp_path):
		"""The two inbound channels stay independent: damaged directed mail
		must not suppress broadcast delivery."""
		config_path, root = _attach_instance(tmp_path)
		_, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		with b6.open_instance(config_path) as st:
			nid = notice_one(st, body=b"broadcast past damage")
		result = b6.wait_for_message(config_path, "acme.implementer", timeout_s=5)
		assert result["notice"]["id"] == nid

	def test_missing_attachment_file_also_skipped(self, tmp_path):
		"""Damage is not only a changed hash — a deleted file must skip too,
		and must not be mistaken for an empty queue."""
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.unlink()
		with b6.open_instance(config_path) as st:
			healthy = send_one(st, body=b"unaffected")
			assert st.claim("acme.implementer")["message_id"] == healthy
			assert [d["id"] for d in st.scan()["damaged"]] == [damaged]

	def test_cli_scan_exposes_damage(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		import io, contextlib
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			code = b6.main(["--config", config_path, "scan",
			                "--participant", "acme.implementer"])
		assert code == 0
		report = json.loads(out.getvalue())
		assert [d["id"] for d in report["damaged"]] == [damaged]
		assert "failure" in report["damaged"][0]


LEAD_ID = {"participant": "hq.lead"}


def _damage(config_path, root, name="EVIDENCE.md"):
	mid, path = _send_attached(config_path, root, name)
	path.write_bytes(b"edited after publication\n")
	return mid


class TestQuarantineAttachment:
	"""The audited disposition for damaged attachments. `claim` skips them so
	they cannot block a queue; this is how they stop being unresolved, and it
	is deliberately NOT a claim — a claim asserts Baton verified the message
	enough to deliver it, and damaged content is never delivered."""

	def test_quarantine_pending_is_atomic_and_audited(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		with b6.open_instance(config_path) as st:
			result = st.quarantine_attachment(mid, reason="pin invalidated by edit", **LEAD_ID)
			assert result["already_committed"] is False
			assert result["prior_state"] == "pending" and result["state"] == "quarantined"
			assert "pinned hash" in result["failure"]
			msg = st.get_message(mid)
			assert msg["state"] == "quarantined" and msg["completed_ts"] is not None
			# the ORIGINAL pin survives on the message AND in the audit row
			row = st.conn.execute("SELECT * FROM quarantines WHERE message_id=?", (mid,)).fetchone()
			assert row["attach_path"] == "EVIDENCE.md" and row["attach_root_id"] == "src"
			assert row["attach_sha256"] == msg["attach_sha256"]
			assert row["prior_state"] == "pending"
			assert row["participant"] == "hq.lead"
			assert row["reason"] == "pin invalidated by edit"
			assert "pinned hash" in row["failure"]
			# and the transition is in the immutable ledger under its own verb
			edge = st.conn.execute(
				"SELECT from_state, to_state, verb FROM transitions "
				"WHERE entity='message' AND entity_id=? ORDER BY rowid DESC LIMIT 1",
				(mid,)).fetchone()
			assert tuple(edge) == ("pending", "quarantined", "quarantine")

	def test_quarantine_clears_the_queue_block(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		assert b6.doctor(config_path)["ok"] is False
		with b6.open_instance(config_path) as st:
			st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
			assert st.scan("acme.implementer")["pending"] == []
			assert st.scan("acme.implementer")["damaged"] == []
		report = b6.doctor(config_path)
		assert report["ok"] is True  # acknowledged damage no longer blocks health
		assert report["quarantined"] == [mid]
		assert any("quarantined" in w for w in report["warnings"])  # still visible

	def test_quarantine_refuses_healthy_message(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid, _ = _send_attached(config_path, root, "EVIDENCE.md")
		with b6.open_instance(config_path) as st:
			with pytest.raises(b6.BatonError, match="verifies cleanly"):
				st.quarantine_attachment(mid, reason="no damage here", **LEAD_ID)
			assert st.get_message(mid)["state"] == "pending"
			assert st.conn.execute("SELECT COUNT(*) FROM quarantines").fetchone()[0] == 0

	def test_quarantine_refuses_unknown_bodyless_and_unauthorized(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		with b6.open_instance(config_path) as st:
			with pytest.raises(b6.BatonError) as excinfo:
				st.quarantine_attachment("0" * 32, reason="ghost", **LEAD_ID)
			assert excinfo.value.exit_code == b6.EXIT_NONE
			plain = send_one(st)  # body-backed, no attachment to damage
			with pytest.raises(b6.BatonError, match="no attachment"):
				st.quarantine_attachment(plain, reason="not applicable", **LEAD_ID)
			# authority is an explicit capability, never inferred
			with pytest.raises(b6.BatonError, match="recovery"):
				st.quarantine_attachment(mid, reason="unauthorized",
				                         participant="acme.implementer")
			with pytest.raises(b6.BatonError, match="reason"):
				st.quarantine_attachment(mid, reason="   ", **LEAD_ID)
			assert st.conn.execute("SELECT COUNT(*) FROM quarantines").fetchone()[0] == 0

	def test_quarantine_retry_is_idempotent_and_mismatch_fails_closed(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		with b6.open_instance(config_path) as st:
			first = st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
			again = st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
			assert again["already_committed"] is True
			assert again["quarantine_id"] == first["quarantine_id"]
			assert again["prior_state"] == "pending"
			with pytest.raises(b6.BatonError, match="differs from the committed"):
				st.quarantine_attachment(mid, reason="a different story", **LEAD_ID)
			assert st.conn.execute("SELECT COUNT(*) FROM quarantines").fetchone()[0] == 1

	def test_quarantine_refuses_a_claimed_message(self, tmp_path):
		"""In-flight work is not silently dispositioned out from under its
		owner; the claim must be resolved or recovered first."""
		config_path, root = _attach_instance(tmp_path)
		mid, path = _send_attached(config_path, root, "EVIDENCE.md")
		with b6.open_instance(config_path) as st:
			st.claim("acme.implementer")
			path.write_bytes(b"edited while claimed\n")
			with pytest.raises(b6.BatonError) as excinfo:
				st.quarantine_attachment(mid, reason="damaged mid-flight", **LEAD_ID)
			assert excinfo.value.exit_code == b6.EXIT_RACE
			assert st.get_message(mid)["state"] == "claimed"
			assert st.conn.execute("SELECT COUNT(*) FROM quarantines").fetchone()[0] == 0

	def test_quarantine_of_already_terminal_message(self, tmp_path):
		"""The `da19ba84` case: content really was delivered, and only the
		retained attachment later went stale. History is acknowledged, never
		rewritten — the terminal state stays exactly as it was."""
		config_path, root = _attach_instance(tmp_path)
		mid, path = _send_attached(config_path, root, "EVIDENCE.md")
		with b6.open_instance(config_path) as st:
			claim = st.claim("acme.implementer")
			st.close_claim(claim["claim_id"], participant=claim["participant"])
			assert st.get_message(mid)["state"] == "closed"
		path.write_bytes(b"edited long after delivery\n")
		assert b6.doctor(config_path)["ok"] is False
		with b6.open_instance(config_path) as st:
			result = st.quarantine_attachment(mid, reason="retained pin went stale", **LEAD_ID)
			assert result["prior_state"] == "closed"
			assert result["state"] == "closed"  # NOT rewritten to quarantined
			assert st.get_message(mid)["state"] == "closed"
		assert b6.doctor(config_path)["ok"] is True

	def test_quarantine_records_are_immutable_and_permanent(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		with b6.open_instance(config_path) as st:
			st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
			with pytest.raises(sqlite3.IntegrityError, match="immutable"):
				st.conn.execute("UPDATE quarantines SET reason='rewritten'")
			with pytest.raises(sqlite3.IntegrityError, match="permanent"):
				st.conn.execute("DELETE FROM quarantines")
			with pytest.raises(sqlite3.IntegrityError, match="quarantine ceremony"):
				st.conn.execute(
					"INSERT INTO quarantines(quarantine_id, message_id, participant, "
					"reason, prior_state, attach_root_id, attach_path, attach_sha256, "
					"attach_size, attach_generation, failure, created_ts) "
					"VALUES('x',?,'hq.lead','r','pending','src','p','s',1,1,'f','t')",
					(mid,))

	def test_quarantined_message_is_not_reclaimable(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		with b6.open_instance(config_path) as st:
			st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
			with pytest.raises(b6.BatonError) as excinfo:
				st.claim("acme.implementer", message_id=mid)
			assert excinfo.value.exit_code in (b6.EXIT_NONE, b6.EXIT_DAMAGE)
			assert st.get_message(mid)["state"] == "quarantined"
			# and the illegal revival edge is refused by the schema itself
			with pytest.raises(sqlite3.IntegrityError, match="illegal message state edge"):
				st.conn.execute("UPDATE messages SET state='pending' WHERE id=?", (mid,))

	def test_cli_quarantine_roundtrip(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		import io, contextlib
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			code = b6.main(["--config", config_path, "quarantine-attachment", mid,
			                "--participant", "hq.lead", "--reason", "stale pin from a doc edited after publication"])
		assert code == 0
		result = json.loads(out.getvalue())
		assert result["state"] == "quarantined" and result["already_committed"] is False
		assert b6.doctor(config_path)["ok"] is True


class TestQuarantineUnderGate:
	"""Review round 1: the accepted operating sequence is migrate → quarantine
	→ verify healthy → reopen. Quarantine must therefore run WITH the
	maintenance gate still closed, while still refusing a move."""

	def test_quarantine_runs_under_maintenance_and_doctor_agrees(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		b6.maintenance_enter(config_path, reason="protocol upgrade", **LEAD_ID)
		result = b6.quarantine_attachment_instance(
			config_path, mid, reason="stale pin", **LEAD_ID)
		assert result["state"] == "quarantined"
		report = b6.doctor(config_path)  # verified BEFORE reopening
		assert report["ok"] is True and report["quarantined"] == [mid]
		b6.maintenance_exit(config_path, reason="done", **LEAD_ID)
		assert b6.doctor(config_path)["ok"] is True

	def test_ordinary_writes_stay_gated_while_quarantine_is_allowed(self, tmp_path):
		"""The exception is scoped to the ceremony, not a hole in the gate."""
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		b6.maintenance_enter(config_path, reason="upgrade", **LEAD_ID)
		with b6.open_instance(config_path, _for_ceremony=True) as st:
			with pytest.raises(b6.BatonError) as excinfo:
				send_one(st)
			assert excinfo.value.exit_code == b6.EXIT_GATED
			assert st.quarantine_attachment(mid, reason="ok", **LEAD_ID)["state"] == "quarantined"

	def test_quarantine_refused_during_a_move(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		dest = tmp_path / "dest"
		dest.mkdir()
		b6.maintenance_enter(config_path, reason="moving", move=True,
		                     destination=str(dest / "baton.json"), **LEAD_ID)
		with pytest.raises(b6.BatonError) as excinfo:
			b6.quarantine_attachment_instance(config_path, mid, reason="nope", **LEAD_ID)
		assert excinfo.value.exit_code == b6.EXIT_GATED
		assert "move" in str(excinfo.value)

	def test_doctor_flags_incoherent_quarantine_state(self, tmp_path):
		"""Both directions of the state/audit agreement are checked."""
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		with b6.open_instance(config_path) as st:
			st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
		assert b6.doctor(config_path)["ok"] is True
		_raw_corrupt(config_path, lambda conn: conn.execute(
			"UPDATE quarantines SET attach_sha256='0'*64"))
		report = b6.doctor(config_path)
		assert report["ok"] is False
		assert any("different pin" in p for p in report["problems"])

	def test_doctor_flags_quarantined_state_without_record(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		_raw_corrupt(config_path, lambda conn: conn.execute(
			"UPDATE messages SET state='quarantined', completed_ts='2099-01-01T00:00:00Z' "
			"WHERE id=?", (mid,)))
		report = b6.doctor(config_path)
		assert report["ok"] is False
		assert any("no quarantine record" in p for p in report["problems"])

	def test_retry_identity_is_the_full_tuple(self, tmp_path):
		"""A second operator cannot inherit someone else's audit row by
		offering the same reason."""
		config_path, root = _attach_instance(tmp_path)
		mid = _damage(config_path, root)
		cfg = json.load(open(config_path))
		cfg["participants"]["hq.deputy"] = {

			"capabilities": ["recovery", "config"]}
		cfg["generation"] = 2
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.regen_instance(config_path, **LEAD_ID)
		with b6.open_instance(config_path) as st:
			st.quarantine_attachment(mid, reason="stale pin", **LEAD_ID)
			with pytest.raises(b6.BatonError, match="participant"):
				st.quarantine_attachment(mid, reason="stale pin", participant="hq.deputy")
			assert st.conn.execute("SELECT COUNT(*) FROM quarantines").fetchone()[0] == 1


class TestMaintenanceDrainInvariant:
	"""The no-active-claims invariant belongs to the operation that CLOSES the
	gate. `reply` and `close` are themselves gated, so a claim that survives
	into maintenance has lost its normal route to resolution — catching it
	later, at migrate time, is too late to be 'just a retry'."""

	def test_maintenance_entry_refuses_active_claims_atomically(self, instance):
		with b6.open_instance(instance) as st:
			mid = send_one(st)
			claim = st.claim("acme.implementer")
		with pytest.raises(b6.BatonError) as excinfo:
			b6.maintenance_enter(instance, reason="upgrade", **LEAD_ID)
		assert excinfo.value.exit_code == b6.EXIT_RACE
		assert "active claim" in str(excinfo.value)
		assert "acme.implementer" in str(excinfo.value)  # names the holder
		# REFUSAL LEAVES THE INSTANCE UNGATED, so the holder can still drain
		with b6.open_instance(instance) as st:
			assert b6._meta(st)["maintenance"] == 0
			st.close_claim(claim["claim_id"], participant=claim["participant"])
			assert st.get_message(mid)["state"] == "closed"
		assert b6.maintenance_enter(instance, reason="upgrade",
		                            **LEAD_ID)["maintenance"] is True

	def test_refusal_writes_no_ceremony_record(self, instance):
		with b6.open_instance(instance) as st:
			send_one(st)
			st.claim("acme.implementer")
		with pytest.raises(b6.BatonError):
			b6.maintenance_enter(instance, reason="upgrade", **LEAD_ID)
		with b6.open_instance(instance) as st:
			assert st.conn.execute(
				"SELECT COUNT(*) FROM ceremonies WHERE kind='maintenance_enter'"
			).fetchone()[0] == 0

	def test_move_entry_refuses_active_claims_too(self, instance, tmp_path):
		with b6.open_instance(instance) as st:
			send_one(st)
			st.claim("acme.implementer")
		dest = tmp_path / "dest"
		dest.mkdir()
		with pytest.raises(b6.BatonError) as excinfo:
			b6.maintenance_enter(instance, reason="moving", move=True,
			                     destination=str(dest / "baton.json"), **LEAD_ID)
		assert excinfo.value.exit_code == b6.EXIT_RACE
		with b6.open_instance(instance) as st:
			row = b6._meta(st)
			assert row["maintenance"] == 0 and row["move_status"] == "none"
			assert st.conn.execute("SELECT COUNT(*) FROM moves").fetchone()[0] == 0

	def test_recovered_claim_no_longer_blocks_the_gate(self, instance):
		"""A dead holder is unblocked through `recover-claim`, not by forcing
		the gate — the refusal points at the right remedy."""
		with b6.open_instance(instance) as st:
			send_one(st)
			claim = st.claim("acme.implementer")
			st.recover_claim(claim["claim_id"], reason="host died", **LEAD_ID)
		assert b6.maintenance_enter(instance, reason="upgrade",
		                            **LEAD_ID)["maintenance"] is True


class TestSnapshot:
	def test_snapshot_is_validated_and_restorable(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		with b6.open_instance(config_path) as st:
			mid = send_one(st, body=b"must survive a restore")
		b6.maintenance_enter(config_path, reason="upgrade", **LEAD_ID)
		dest = str(tmp_path / "snap")
		result = b6.snapshot_instance(config_path, dest, **LEAD_ID)
		assert result["protocol"] == b6.PROTOCOL_VERSION
		assert result["messages"] == 1 and result["active_claims"] == 0
		import hashlib as _h
		assert _h.sha256(open(os.path.join(dest, "mailbox.sqlite3"), "rb").read()).hexdigest() \
			== result["database_sha256"]
		# the snapshot is a usable instance on its own, with the same content
		b6.maintenance_exit(os.path.join(dest, "baton.json"), reason="open the copy", **LEAD_ID)
		with b6.open_instance(os.path.join(dest, "baton.json")) as copy:
			assert copy.get_message(mid)["body"] == b"must survive a restore"
		b6.maintenance_exit(config_path, reason="done", **LEAD_ID)

	def test_snapshot_persists_its_own_directory_entry(self, tmp_path, monkeypatch):
		"""The publication helpers fsync the copied files and the destination
		directory, which persists what is INSIDE dest — not dest's own entry
		in its parent. A crash after the migration commits could otherwise
		lose the rollback directory's name with every byte in it synced."""
		config_path, root = _attach_instance(tmp_path)
		with b6.open_instance(config_path) as st:
			send_one(st)
		b6.maintenance_enter(config_path, reason="upgrade", **LEAD_ID)
		synced = []
		real_fsync = os.fsync
		def recording_fsync(fd):
			try:
				st = os.fstat(fd)
				synced.append((st.st_dev, st.st_ino))
			except OSError:
				pass
			return real_fsync(fd)
		monkeypatch.setattr(os, "fsync", recording_fsync)
		parent = tmp_path / "backups"
		parent.mkdir()
		dest = str(parent / "snap")
		b6.snapshot_instance(config_path, dest, **LEAD_ID)
		monkeypatch.undo()
		parent_st = os.stat(parent)
		assert (parent_st.st_dev, parent_st.st_ino) in synced, \
			"parent directory was never fsynced; the snapshot dir entry is not durable"
		dest_st = os.stat(dest)
		assert (dest_st.st_dev, dest_st.st_ino) in synced

	def test_snapshot_requires_gate_and_capability(self, tmp_path):
		config_path, root = _attach_instance(tmp_path)
		dest = str(tmp_path / "snap")
		with pytest.raises(b6.BatonError, match="maintenance gate"):
			b6.snapshot_instance(config_path, dest, **LEAD_ID)
		b6.maintenance_enter(config_path, reason="upgrade", **LEAD_ID)
		with pytest.raises(b6.BatonError, match="config"):
			b6.snapshot_instance(config_path, dest, participant="acme.implementer")

	def test_snapshot_folds_the_wal_in(self, tmp_path):
		"""The reason a bare `cp` is not a backup: committed state can live in
		the -wal sibling. The snapshot drains it first, so the single copied
		file carries everything."""
		config_path, root = _attach_instance(tmp_path)
		with b6.open_instance(config_path) as st:
			for i in range(20):
				send_one(st, body=f"row {i}".encode())
		b6.maintenance_enter(config_path, reason="upgrade", **LEAD_ID)
		dest = str(tmp_path / "snap")
		result = b6.snapshot_instance(config_path, dest, **LEAD_ID)
		assert result["messages"] == 20
		# The copied MAIN FILE is self-contained: discard every sibling, as a
		# restore onto a fresh directory would, and it still holds everything.
		# That is the property a bare `cp` of a WAL database does not have.
		for sibling in ("mailbox.sqlite3-wal", "mailbox.sqlite3-shm"):
			path = os.path.join(dest, sibling)
			if os.path.exists(path):
				os.unlink(path)
		b6.maintenance_exit(os.path.join(dest, "baton.json"), reason="check", **LEAD_ID)
		with b6.open_instance(os.path.join(dest, "baton.json")) as copy:
			assert copy.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 20


class TestDoctorLogical:
	def test_orphan_content_detected(self, store):
		send_one(store, body=b"x")
		import hashlib as _h
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"INSERT INTO contents(content_id, body, sha256, size, created_ts) "
			"VALUES('orphan01', X'00', ?, 1, 'now')", (_h.sha256(b"\x00").hexdigest(),)))
		report = b6.doctor(store.config_path)
		assert any("owners" in p or "orphan" in p for p in report["problems"])
		assert report["ok"] is False

	def test_accepted_roots_config_mismatch_detected(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		_raw_corrupt(config_path, lambda conn: conn.execute("DELETE FROM accepted_roots"))
		report = b6.doctor(config_path)
		assert any("accepted_roots" in p for p in report["problems"])

	def test_materialize_refuses_pending_and_claimed_transient(self, instance, tmp_path):
		with b6.open_instance(instance) as st:
			mid = send_one(st, body=b"t", retention="transient")
			with pytest.raises(b6.BatonError, match="transient"):
				b6.materialize(instance, mid, str(tmp_path))
			st.claim("acme.implementer", message_id=mid)
			with pytest.raises(b6.BatonError, match="transient"):
				b6.materialize(instance, mid, str(tmp_path))


# ---------------------------------------------------------------------------
# Round-3 additions: atomic wait delivery, root guards, audit-chain doctor
# ---------------------------------------------------------------------------

def _raw_set_maintenance(config_path, reason="externally gated"):
	"""Set the maintenance gate WITHOUT going through `maintenance_enter`.

	Since the drain invariant landed, the ceremony refuses to gate an instance
	that has an active claim — which is the point. The seam it protects is
	still real, because a gate can arrive by other routes: a concurrent
	process on an older executable, or a future ceremony. These tests
	construct that condition directly so the delivery-robustness property
	stays covered rather than becoming unreachable and untested."""
	db = os.path.join(os.path.dirname(config_path), "mailbox.sqlite3")
	conn = sqlite3.connect(db)
	try:
		guard = conn.execute(
			"SELECT sql FROM sqlite_master WHERE name='trg_meta_gate_guard'").fetchone()[0]
		conn.execute("DROP TRIGGER trg_meta_gate_guard")
		conn.execute("UPDATE instance_meta SET maintenance=1, maintainer_participant='lead', "
		             "maintainer_reason=? WHERE one_row=1", (reason,))
		conn.execute(guard)
		conn.commit()
	finally:
		conn.close()


class TestAtomicWaitDelivery:
	def test_gate_after_claim_still_delivers(self, instance, monkeypatch):
		with b6.open_instance(instance) as st:
			send_one(st, body=b"already owned")
		def gate_after_claim(point):
			if point == "wait:claimed":
				b6._FAULT_HOOK = None
				_raw_set_maintenance(instance, "post-claim gate")
		monkeypatch.setattr(b6, "_FAULT_HOOK", gate_after_claim)
		result = b6.wait_for_message(instance, "acme.implementer",
		                             timeout_s=10)
		assert result["message"]["body"]["utf8"] == "already owned"

	def test_content_hash_mismatch_is_damage_not_delivery(self, instance):
		with b6.open_instance(instance) as st:
			mid = send_one(st, body=b"real bytes")
		_raw_corrupt(instance, lambda conn: conn.execute(
			"UPDATE contents SET body=X'6861636b6564'"))  # 'hacked'
		with b6.open_instance(instance) as st:
			claim = st.claim("acme.implementer", message_id=mid)
			with pytest.raises(b6.BatonError, match="recorded sha256") as excinfo:
				b6._delivery(st, claim)
			assert excinfo.value.exit_code == b6.EXIT_DAMAGE


class TestAcceptedRootsGuards:
	def test_uncontextual_and_wrong_verb_mutations_refused(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			with pytest.raises(sqlite3.IntegrityError, match="regen"):
				st.conn.execute("DELETE FROM accepted_roots")
			with pytest.raises(sqlite3.IntegrityError, match="regen"):
				st.conn.execute("UPDATE accepted_roots SET binding_generation=9")
			st._txn_begin("move", ceremony=None)
			try:
				with pytest.raises(sqlite3.IntegrityError, match="regen"):
					st.conn.execute(
						"INSERT INTO accepted_roots(root_id, path, binding_generation) "
						"VALUES('forged', '/f', 1)")
			finally:
				st._txn_rollback()
		# The public regen path still succeeds (the only authorized writer).
		extra = tmp_path / "extra"
		extra.mkdir()
		cfg2 = make_config(generation=2)
		cfg2["roots"] = {"evidence": str(root), "extra": str(extra)}
		with open(config_path, "w") as handle:
			json.dump(cfg2, handle)
		result = b6.regen_instance(config_path, participant="hq.lead")
		assert result["accepted_generation"] == 2


class TestAuditChainDoctor:
	def test_duplicate_birth_detected(self, store):
		mid = send_one(store)
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, "
			"participant, verb, at_ts) VALUES('message', ?, NULL, 'pending', "
			"'forged0000000000forged0000000000', 'p.q', 'send', 'now')", (mid,)))
		report = b6.doctor(store.config_path)
		assert any("birth" in p for p in report["problems"])

	def test_broken_chain_detected(self, store):
		mid = send_one(store)
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, "
			"participant, verb, at_ts) VALUES('message', ?, 'completed', 'closed', "
			"'forged0000000000forged0000000000', 'p.q', 'close', 'now')", (mid,)))
		report = b6.doctor(store.config_path)
		assert any("breaks" in p or "illegal edge" in p or "disagrees" in p
		           for p in report["problems"])

	def test_wrong_tail_detected(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"DELETE FROM transitions WHERE entity='message' AND to_state='closed'"))
		report = b6.doctor(store.config_path)
		assert any("disagrees" in p for p in report["problems"])

	def test_attachment_mutation_detected_by_doctor(self, tmp_path):
		root = tmp_path / "evidence"
		root.mkdir()
		(root / "e.md").write_bytes(b"original")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"evidence": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			st.send("acme.reviewer", "acme.implementer",
			        kind="ev", body=None, attach={"root_id": "evidence", "path": "e.md"})
		assert b6.doctor(config_path)["ok"] is True
		(root / "e.md").write_bytes(b"tampered")
		report = b6.doctor(config_path)
		assert any("attachment" in p for p in report["problems"])
		assert report["ok"] is False

	def test_content_byte_mismatch_detected(self, store):
		send_one(store, body=b"real")
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"UPDATE contents SET body=X'00'"))
		report = b6.doctor(store.config_path)
		assert any("disagree with recorded" in p for p in report["problems"])

	def test_projection_inventory(self, tmp_path):
		proj = tmp_path / "proj"
		proj.mkdir()
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["participants"]["acme.reviewer"]["projection_dir"] = str(proj)
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			mid = st.send("acme.reviewer", "acme.implementer",
			              kind="q", body=b"# record\\n")
		path = b6.materialize(config_path, mid, str(proj))
		report = b6.doctor(config_path)
		assert report["projections"]["checked"] == 1
		assert report["projections"]["orphans"] == []
		(proj / "message-2020-01-01T00-00-00Z-deadbeefdeadbeefdeadbeefdeadbeef.md").write_bytes(b"x")
		report = b6.doctor(config_path)
		assert len(report["projections"]["orphans"]) == 1
		assert report["ok"] is True  # orphan projections warn, never fail


class TestStrictJsonOutput:
	def test_non_string_keys_and_nonfinite_rejected(self):
		with pytest.raises(b6.BatonError, match="non-string"):
			b6._to_jsonable({1: "x"})
		with pytest.raises(b6.BatonError, match="non-finite"):
			b6._to_jsonable({"x": float("inf")})


class TestRound4Additions:
	def test_forged_attribution_detected(self, store):
		mid = send_one(store)
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		# Valid chain/edge/verb; ONLY the attribution is malformed.
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"UPDATE transitions SET participant='NotAnAddress' WHERE entity='claim'"))
		report = b6.doctor(store.config_path)
		assert any("malformed participant" in p for p in report["problems"])
		assert not any("birth" in p or "breaks" in p or "illegal" in p or "disagrees" in p
		               for p in report["problems"])

	def test_configured_projection_prefix_used(self, tmp_path):
		proj = tmp_path / "proj"
		proj.mkdir()
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["participants"]["acme.reviewer"]["projection_dir"] = str(proj)
		cfg["participants"]["acme.reviewer"]["projection_prefix"] = "review"
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as st:
			mid = st.send("acme.reviewer", "acme.implementer",
			              kind="q", body=b"# record\n")
		path = b6.materialize(config_path, mid, str(proj), prefix="review")
		assert os.path.basename(path).startswith("review-")
		report = b6.doctor(config_path)
		assert report["projections"]["checked"] == 1  # configured prefix inventoried
		assert report["projections"]["orphans"] == []
		default_named = b6.materialize(config_path, mid, str(proj))  # default prefix ignored here
		report = b6.doctor(config_path)
		assert report["projections"]["checked"] == 1  # only the configured prefix counts
		with pytest.raises(b6.BatonError, match="invalid projection prefix"):
			b6.materialize(config_path, mid, str(proj), prefix="Bad Prefix!")

	def test_gate_between_claim_and_fetch_still_delivers(self, instance, monkeypatch):
		"""The seam now fires BEFORE _delivery: content is fetched through the
		already-open store after the instance has been gated."""
		with b6.open_instance(instance) as st:
			send_one(st, body=b"claimed then gated")
		def gate_at_seam(point):
			if point == "wait:claimed":
				b6._FAULT_HOOK = None
				_raw_set_maintenance(instance, "between claim and fetch")
		monkeypatch.setattr(b6, "_FAULT_HOOK", gate_at_seam)
		result = b6.wait_for_message(instance, "acme.implementer",
		                             timeout_s=10)
		assert result["message"]["body"]["utf8"] == "claimed then gated"


class TestAttributionCoherence:
	def test_impossible_edge_verb_pairing_detected(self, store):
		mid = send_one(store)
		store.claim("acme.implementer", message_id=mid)
		# Chain and tail stay valid; ONLY the verb becomes impossible for
		# the pending->claimed edge.
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"UPDATE transitions SET verb='migrate' WHERE entity='message' "
			"AND from_state='pending' AND to_state='claimed'"))
		report = b6.doctor(store.config_path)
		assert any("cannot be produced by verb" in p for p in report["problems"])
		assert not any("birth" in p or "breaks" in p or "disagrees" in p
		               for p in report["problems"])

	def test_same_op_attribution_split_detected(self, store):
		mid = send_one(store)
		store.claim("acme.implementer", message_id=mid)
		# The claim transaction emits two rows under one op_id; split the
		# participant on exactly one of them, keeping every field lexically valid.
		def split(conn):
			op = conn.execute(
				"SELECT op_id FROM transitions WHERE verb='claim' LIMIT 1").fetchone()[0]
			seq = conn.execute(
				"SELECT seq FROM transitions WHERE op_id=? ORDER BY seq LIMIT 1", (op,)).fetchone()[0]
			conn.execute("UPDATE transitions SET participant='hq.other' WHERE seq=?", (seq,))
		_raw_corrupt(store.config_path, split)
		report = b6.doctor(store.config_path)
		assert any("distinct attribution tuples" in p for p in report["problems"])
		assert not any("cannot be produced" in p for p in report["problems"])

	def test_oversized_participant_detected(self, store):
		send_one(store)
		long_addr = "a." + "b" * 80
		_raw_corrupt(store.config_path, lambda conn: conn.execute(
			"UPDATE transitions SET participant=? WHERE participant IS NOT NULL",
			(long_addr,)))
		report = b6.doctor(store.config_path)
		assert any("malformed participant" in p for p in report["problems"])


# ---------------------------------------------------------------------------
# Phase 5: packaging, distribution, extraction purity
# ---------------------------------------------------------------------------

class TestPackaging:
	def _builder(self):
		import importlib.util
		spec = importlib.util.spec_from_file_location(
			"build_zipapp", os.path.join(os.path.dirname(__file__), "build_zipapp.py"))
		builder = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(builder)
		return builder

	def test_zipapp_deterministic_and_runnable(self, tmp_path):
		import subprocess, sys as _sys
		builder = self._builder()
		m1 = builder.build(str(tmp_path / "a"))
		m2 = builder.build(str(tmp_path / "b"))
		assert m1["artifact_sha256"] == m2["artifact_sha256"]
		assert open(tmp_path / "a" / "bin" / "baton", "rb").read() == \
			open(tmp_path / "b" / "bin" / "baton", "rb").read()
		proc = subprocess.run([_sys.executable, str(tmp_path / "a" / "bin" / "baton"),
		                       "--version"], capture_output=True, text=True)
		assert proc.returncode == 0
		assert f"protocol {b6.PROTOCOL_VERSION}" in proc.stdout

	def test_distribution_root_contract(self, tmp_path):
		"""The manifest's artifact path RESOLVES from the root it sits in and
		hashes to the recorded value."""
		import hashlib as _h
		builder = self._builder()
		root = tmp_path / "dist"
		manifest = builder.build(str(root))
		assert (root / "DISTRIBUTION.json").is_file()
		artifact = root / manifest["artifact"]
		assert artifact.is_file(), "manifest artifact must resolve from the distribution root"
		assert _h.sha256(artifact.read_bytes()).hexdigest() == manifest["artifact_sha256"]
		committed = json.loads(open(os.path.join(os.path.dirname(__file__),
		                                          "DISTRIBUTION.json")).read())
		committed_artifact = os.path.join(os.path.dirname(__file__), committed["artifact"])
		assert os.path.isfile(committed_artifact), "checked-in bin/baton must exist"
		assert _h.sha256(open(committed_artifact, "rb").read()).hexdigest() == \
			committed["artifact_sha256"]
		here_src = open(os.path.join(os.path.dirname(__file__), "baton_v6.py"), "rb").read()
		assert committed["source_sha256"] == _h.sha256(here_src).hexdigest(), \
			"committed manifest is stale against baton_v6.py — rerun build_zipapp.py"
		# The generic protocol doc ships in the distribution root and is
		# hash-pinned by the manifest.
		proto_built = root / manifest["protocol_doc"]
		assert proto_built.is_file()
		assert _h.sha256(proto_built.read_bytes()).hexdigest() == manifest["protocol_doc_sha256"]
		proto_committed = os.path.join(os.path.dirname(__file__), committed["protocol_doc"])
		assert os.path.isfile(proto_committed)
		assert _h.sha256(open(proto_committed, "rb").read()).hexdigest() == \
			committed["protocol_doc_sha256"], "committed manifest stale against the protocol doc"

	def test_bootstrap_floor_syntax_and_logic(self, tmp_path):
		builder = self._builder()
		import ast
		tree = ast.parse(builder.BOOTSTRAP)
		for node in ast.walk(tree):
			assert not isinstance(node, ast.NamedExpr)
			assert type(node).__name__ != "Match"
		lines = builder.BOOTSTRAP.splitlines()
		floor_idx = next(i for i, l in enumerate(lines) if "version_info < (3, 11)" in l)
		import_idx = next(i for i, l in enumerate(lines) if "from baton_v6" in l)
		assert floor_idx < import_idx

	def test_zipapp_imports_own_module_under_poisoned_cwd(self, tmp_path):
		import subprocess, sys as _sys
		builder = self._builder()
		root = tmp_path / "dist"
		builder.build(str(root))
		poison = tmp_path / "poison"
		poison.mkdir()
		(poison / "baton_v6.py").write_text("raise RuntimeError('poisoned import')\n")
		proc = subprocess.run([_sys.executable, str(root / "bin" / "baton"), "--version"],
		                      capture_output=True, text=True, cwd=str(poison),
		                      env={"PATH": os.environ["PATH"], "PYTHONPATH": str(poison)})
		assert proc.returncode == 0, proc.stderr
		assert "poisoned" not in proc.stderr

	REUSABLE_ASSETS = ["baton_v6.py", "test_baton_v6.py", "build_zipapp.py",
	                   "example-baton.json", "config-schema.json", "README.md",
	                   "baton", "DISTRIBUTION.json", "AGENTS-MAILBOX-PROTO.md"]

	@pytest.mark.skipif(os.environ.get("BATON_ISOLATED") == "1",
	                    reason="already inside the isolated run")
	def test_isolated_checkout_runs_full_reusable_suite(self, tmp_path):
		"""T26: the ENTIRE reusable set — including this test file — passes
		from a bare copied tree whose cwd/PYTHONPATH exclude the host."""
		import shutil, subprocess, sys as _sys
		iso = tmp_path / "iso"
		iso.mkdir()
		here = os.path.dirname(__file__)
		for asset in self.REUSABLE_ASSETS:
			src = os.path.join(here, asset)
			shutil.copy(src, iso / asset)
		(iso / "bin").mkdir()
		shutil.copy(os.path.join(here, "bin", "baton"), iso / "bin" / "baton")
		env = {"PATH": os.environ["PATH"], "PYTHONPATH": str(iso),
		       "BATON_ISOLATED": "1", "HOME": str(tmp_path)}
		proc = subprocess.run(
			[_sys.executable, "-m", "pytest", "test_baton_v6.py", "-q", "-x",
			 "-p", "no:cacheprovider"],
			capture_output=True, text=True, cwd=str(iso), env=env, timeout=420)
		assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]
		assert " passed" in proc.stdout

	def test_distribution_roundtrip_under_poisoned_env(self, tmp_path):
		"""The PACKED distribution (bin/baton) drives send/claim/reply/doctor
		end-to-end with poisoned CWD and PYTHONPATH — the archive must prefer
		its own module over hostile ones for the full workflow, not just
		--version."""
		import shutil, subprocess, sys as _sys
		builder = self._builder()
		root = tmp_path / "dist"
		builder.build(str(root))
		poison = tmp_path / "poison"
		poison.mkdir()
		(poison / "baton_v6.py").write_text("raise RuntimeError('poisoned import')\n")
		inst = tmp_path / "inst"
		inst.mkdir()
		config_path = str(inst / "baton.json")
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"), config_path)
		env = {"PATH": os.environ["PATH"], "PYTHONPATH": str(poison), "HOME": str(tmp_path)}
		def run(*args, stdin=b""):
			return subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config", config_path, *args],
				input=stdin, capture_output=True, cwd=str(poison), env=env, timeout=60)
		assert run("init").returncode == 0
		proc = run("send", "--participant", "team.reviewer",
		           "--to", "team.implementer", "--kind", "q",
		           stdin=b"distribution body")
		assert proc.returncode == 0, proc.stderr
		proc = run("claim", "--participant", "team.implementer")
		assert proc.returncode == 0, proc.stderr
		delivery = json.loads(proc.stdout)
		assert delivery["message"]["body"]["utf8"] == "distribution body"
		proc = run("reply", delivery["claim"]["claim_id"], "--participant",
		           "team.implementer",
		           "--kind", "a", stdin=b"distribution answer")
		assert proc.returncode == 0, proc.stderr
		assert json.loads(proc.stdout)["already_committed"] is False
		proc = run("doctor")
		assert proc.returncode == 0, proc.stderr
		assert json.loads(proc.stdout)["ok"] is True

	def test_extraction_purity_grep_gate(self):
		"""Project-specific needles across EVERY reusable asset, including
		the packed archive bytes."""
		here = os.path.dirname(__file__)
		# Needles are split-constructed so this tuple (and this comment) can
		# never match itself: host policy-file references are banned, while
		# the distribution's own protocol document is a legitimate
		# self-reference.
		banned = ("dri" + "ft-lang", "dri" + "ft.", "/wo" + "rk/",
		          "fin" + "ding-", "AGE" + "NTS.md")
		for asset in self.REUSABLE_ASSETS + [os.path.join("bin", "baton")]:
			path = os.path.join(here, asset)
			data = open(path, "rb").read()
			for needle in banned:
				assert needle.encode() not in data, \
					f"{needle!r} found in reusable asset {asset}"

	def test_schema_asset_matches_validator_and_example(self):
		here = os.path.dirname(__file__)
		schema = json.loads(open(os.path.join(here, "config-schema.json")).read())
		assert set(schema["fields"]) == set(b6._CONFIG_FIELDS)
		assert set(schema["fields"]["participants"]["value_fields"]) == \
			set(b6._PARTICIPANT_FIELDS)
		example = b6.loads_strict(open(os.path.join(here, "example-baton.json")).read())
		b6.validate_config(example)
