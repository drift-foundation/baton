"""Baton storage-core conformance.

This corpus was written against the frozen `baton_v6.py` and exercised it for
the whole scaffolding period, with `test_core_parity.py` bridging it to the
shipping core. Protocol 10 retires that arrangement: active parity ends, and
this corpus moves ONTO the core it was always describing.

It moved WHOLE. Nobody selected which properties were "still valid", because a
hand-picked port is how an inconvenient property quietly stops being checked --
and the corpus passing against `baton_core._impl` unchanged is itself the
evidence that the transfer was faithful.

FOUR imports, not one. The first attempt reported "one line", which was the
module-level import; three more sit inside multiprocessing entry points, where
the child re-imports for the fault-injection tests. Those three passed while
still exercising the RETIRED module in child processes, so the port looked
complete and was not. `test_retired_oracle.py` is what caught it, and it now
parses this tree rather than reading it, so a combined or nested import cannot
hide the same way.

It tests `_impl` DIRECTLY, private names included, and that is deliberate: a
conformance corpus for a protocol implementation is entitled to see the
implementation. The public surface has its own tests in `test_core_api.py`.

Fixtures are deliberately neutral (no host-project names): a small
multi-workspace shop with participants under `acme.*` and `hq.*`.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import sqlite3

import pytest

import baton_core._impl as b6



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
             recipient="acme.implementer", kind="question", thread="topic-1",
             **content):
	return store.send(sender, recipient, kind=kind,
	                  body=body, thread_id=thread, retention=retention, **content)


BINARY_TYPE = "application/octet-stream"


def only_part(content):
	"""The single leaf of a one-part content envelope. Every message carries a
	multipart container even when it holds exactly one part, so this asserts
	the shape rather than assuming it."""
	assert content["content_type"] == b6.DEFAULT_CONTAINER_TYPE
	assert len(content["parts"]) == 1
	return content["parts"][0]


def part_bytes(part):
	"""Raw bytes of a delivered leaf, through whichever ONE representation it
	carries. Returns None for a scrubbed part, which has neither."""
	if part["encoding"] == b6.ENCODING_TEXT:
		return part["text"].encode("utf-8")
	if part["encoding"] == b6.ENCODING_BASE64:
		import base64
		return base64.b64decode(part["base64"])
	assert part["encoding"] is None
	return None


def delivered_bytes(content):
	return part_bytes(only_part(content))


def external_row(store, message_id):
	"""The stored external part row of a message."""
	return store.conn.execute(
		"SELECT * FROM parts WHERE owner_kind='message' AND owner_id=? AND storage='external'",
		(message_id,)).fetchone()


def external_part(content, index=0):
	"""The external leaf of a delivered content envelope. An attachment is a
	PART now, so it is addressed through the manifest like any other."""
	leaves = [p for p in content["parts"] if p.get("storage") == "external"]
	return leaves[index]


def stored_body(store, message_id):
	"""Bytes of a stored message's first leaf, or None once scrubbed."""
	parts = store.get_message(message_id)["parts"]
	return parts[0]["body"] if parts else None


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
		assert stored_body(store, mid) == b"payload"

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

	def test_message_requires_content_and_may_carry_both_kinds(self, store):
		"""Protocol 9 removed the body-XOR-attachment rule. A message can now
		carry an inline explanation AND pinned evidence, which is the whole
		point of converging attachments into parts -- the old model forced
		splitting one statement across two messages.

		An unknown root still fails, and a message with no content at all is
		still refused."""
		with pytest.raises(b6.BatonError, match="not declared in the config"):
			store.send("acme.reviewer", "acme.implementer",
			           kind="question", body=b"x", attach={"root_id": "r", "path": "p"})
		with pytest.raises(b6.BatonError, match="requires content"):
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
		assert stored_body(store, result["response_message_id"]) == b"the answer"
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
		with pytest.raises(b6.BatonError, match="content manifest differs"):
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
		manifest = store.get_message(mid)["manifest_sha256"]
		part_sha = store.get_message(mid)["parts"][0]["sha256"]
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"], outcome="seen")
		msg = store.get_message(mid)
		# The bytes go; the MANIFEST stays. A consumed transient message can
		# still state what it carried, what type it was, and what it hashed to.
		assert msg["parts"][0]["body"] is None
		assert msg["parts"][0]["sha256"] == part_sha
		assert msg["parts"][0]["content_type"] == b6.DEFAULT_CONTENT_TYPE
		assert msg["manifest_sha256"] == manifest
		assert msg["state"] == "closed"
		assert store.conn.execute(
			"SELECT content_id FROM parts WHERE owner_id=?", (mid,)).fetchone()[0] is None

	def test_durable_body_retained(self, store):
		mid = send_one(store, body=b"the record", retention="durable")
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		assert stored_body(store, mid) == b"the record"

	def test_per_owner_content_rows_no_dedup(self, store):
		send_one(store, body=b"identical bytes", retention="transient")
		mid2 = send_one(store, body=b"identical bytes", retention="durable")
		count = store.conn.execute(
			"SELECT COUNT(*) FROM contents WHERE sha256=?",
			(store.get_message(mid2)["parts"][0]["sha256"],)).fetchone()[0]
		assert count == 2
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		assert stored_body(store, mid2) == b"identical bytes"

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
		"""The SHIPPING implementation, not the retired oracle.

		This read `baton_v6.py` until protocol 10 retired it, at which point it
		was checking the purity of a file nobody ships while the file everyone
		ships went unchecked."""
		source = open(os.path.join(os.path.dirname(__file__),
		                           "baton_core", "_impl.py")).read()
		# The SAME needles the packaging gate uses, and scoped for a reason:
		# a bare "dri"+"ft" bans an ordinary English word, and the core uses
		# it as a verb twice ("the exclusion cannot drift"). Pointing this at
		# the shipping implementation exposed that immediately -- the oracle
		# happened not to use the word, so the loose needle had never been
		# tested against real prose.
		for banned in ("dri" + "ft-lang", "dri" + "ft.", "/wo" + "rk/",
		               "fin" + "ding-", "AGE" + "NTS.md"):
			assert banned not in source, \
				f"host-project reference {banned!r} in the core implementation"


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
		count = store.conn.execute(
			"SELECT COUNT(*) FROM contents WHERE sha256=?", (sha,)).fetchone()[0]
		assert count == 0
		# The disposition keeps the whole manifest -- media type, size and hash
		# of each part -- while holding none of the bytes.
		disp = store.conn.execute(
			"SELECT content_type, manifest_sha256 FROM dispositions WHERE claim_id=?",
			(claim["claim_id"],)).fetchone()
		assert disp["content_type"] == b6.DEFAULT_CONTAINER_TYPE
		assert disp["manifest_sha256"] == result["manifest_sha256"]
		part = store.conn.execute(
			"SELECT content_id, sha256, size, content_type FROM parts "
			"WHERE owner_kind='disposition' AND owner_id=?", (claim["claim_id"],)).fetchone()
		assert part["content_id"] is None
		assert part["sha256"] == sha
		assert part["size"] == len(body)
		assert part["content_type"] == b6.DEFAULT_CONTENT_TYPE
		retry = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                          body=body, outcome="noted")
		assert retry["already_committed"] is True
		with pytest.raises(b6.BatonError, match="content manifest differs"):
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
			"SELECT c.body FROM parts p JOIN contents c ON c.content_id=p.content_id "
			"WHERE p.owner_kind='disposition' AND p.owner_id=?", (claim["claim_id"],)).fetchone()
		assert row["body"] == b"kept record"


class TestScrubAndTimestampGuards:
	def test_uncontextual_scrub_rejected(self, store):
		mid = send_one(store, body=b"x", retention="transient")
		with pytest.raises(sqlite3.IntegrityError, match="consuming operation"):
			store.conn.execute(
				"UPDATE parts SET content_id=NULL WHERE owner_kind='message' AND owner_id=?", (mid,))

	def test_wrong_verb_scrub_rejected(self, store):
		mid = send_one(store, body=b"x", retention="transient")
		store._txn_begin("claim")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="consuming operation"):
				store.conn.execute(
				"UPDATE parts SET content_id=NULL WHERE owner_kind='message' AND owner_id=?", (mid,))
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
		assert seen[0]["parts"][0]["body"] == b"all hands"
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
		assert external_row(store, mid)["sha256"] is not None
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
			"SELECT c.body FROM parts p JOIN contents c ON c.content_id=p.content_id "
			"WHERE p.owner_kind='disposition' AND p.owner_id=?", (claim["claim_id"],)).fetchone()
		assert row["body"] == b"promoted record"

	def test_close_override_durable_to_transient_drops_body(self, store):
		send_one(store, retention="durable")
		claim = store.claim("acme.implementer")
		import hashlib as _h
		result = store.close_claim(claim["claim_id"], participant=claim["participant"],
		                           body=b"ephemeral note", retention="transient")
		assert result["manifest_sha256"] is not None
		count = store.conn.execute(
			"SELECT COUNT(*) FROM contents WHERE sha256=?",
			(_h.sha256(b"ephemeral note").hexdigest(),)).fetchone()[0]
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
					"INSERT INTO notices(id, from_participant, kind, content_type, "
					"manifest_sha256, created_ts, ttl_seconds) "
					"VALUES('immortal', 'hq.lead', 'k', 'multipart/mixed', 'sha', 'now', 0)")
			finally:
				store._txn_rollback()

	def test_notice_immutability_and_context(self, store):
		nid = store.send_notice("hq.lead", kind="note", body=b"x")
		with pytest.raises(sqlite3.IntegrityError, match="immutable"):
			store.conn.execute("UPDATE notices SET from_participant='hq.forged' WHERE id=?", (nid,))
		with pytest.raises(sqlite3.IntegrityError, match="context"):
			store.conn.execute(
				"INSERT INTO notices(id, from_participant, kind, content_type, "
				"manifest_sha256, created_ts, ttl_seconds) "
				"VALUES('raw', 'hq.lead', 'k', 'multipart/mixed', 'sha', 'now', 60)")
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
				store.conn.execute(
				"UPDATE parts SET content_id=NULL WHERE owner_kind='message' AND owner_id=?", (mid,))
		finally:
			store._txn_rollback()

	def test_durable_terminal_scrub_rejected(self, store):
		mid = send_one(store, retention="durable")
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		store._txn_begin("close")
		try:
			with pytest.raises(sqlite3.IntegrityError, match="terminal transient"):
				store.conn.execute(
				"UPDATE parts SET content_id=NULL WHERE owner_kind='message' AND owner_id=?", (mid,))
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
	import baton_core._impl as mod
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
			assert external_row(st, mid)["generation"] == 1
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
					"content_type, manifest_sha256, created_ts, state, completed_ts) "
					"VALUES('prefilled', 'acme.reviewer', 'acme.implementer', 'k', 'durable', "
					"'multipart/mixed', 'sha', 'now', 'pending', 'already')")
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
			"SELECT c.body FROM parts p JOIN contents c ON c.content_id=p.content_id "
			"WHERE p.owner_kind='disposition' AND p.owner_id=?", (claim["claim_id"],)).fetchone()
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
	import baton_core._impl as mod
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
	import baton_core._impl as mod
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
		assert delivered_bytes(result["message"]["content"]) == b"hello"

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
		assert delivered_bytes(delivery["message"]["content"]) == b"question body"
		assert all(p["attachment"] is None for p in delivery["message"]["content"]["parts"])
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
		                 kind="blob", body=raw, content_type=BINARY_TYPE)
		claim = store.claim("acme.implementer", message_id=mid)
		delivery = b6._delivery(store, claim)
		part = only_part(delivery["message"]["content"])
		assert part["encoding"] == b6.ENCODING_BASE64
		assert base64.b64decode(part["base64"]) == raw
		assert part["size"] == 256
		# Exactly ONE representation, chosen by the declared type.
		assert "text" not in part
		mid2 = store.send("acme.reviewer", "acme.implementer",
		                  kind="empty", body=b"")
		claim2 = store.claim("acme.implementer", message_id=mid2)
		part2 = only_part(b6._delivery(store, claim2)["message"]["content"])
		assert part2["size"] == 0 and part2["encoding"] == b6.ENCODING_TEXT
		assert part2["text"] == "" and "base64" not in part2

	def test_undeclared_binary_is_refused_not_mislabelled(self, store):
		"""The default type declares charset=utf-8, so bytes that are not UTF-8
		are refused at publication with the fix named.

		Falling back to base64 whenever the bytes failed to decode would put
		back exactly what this envelope removed: a representation that changes
		with the payload, leaving the declared type describing something the
		content is not. A consumer acts on the label, so a wrong label is worse
		than a refusal."""
		with pytest.raises(b6.BatonError, match="not valid UTF-8"):
			store.send("acme.reviewer", "acme.implementer", kind="blob", body=b"\xff\xfe")
		# Declaring the type is the whole fix, and it round-trips losslessly.
		mid = store.send("acme.reviewer", "acme.implementer", kind="blob",
		                 body=b"\xff\xfe", content_type=BINARY_TYPE)
		claim = store.claim("acme.implementer", message_id=mid)
		assert delivered_bytes(b6._delivery(store, claim)["message"]["content"]) == b"\xff\xfe"

	def test_transient_body_readable_after_claim_until_consumed(self, store):
		mid = store.send("acme.reviewer", "acme.implementer",
		                 kind="t", body=b"still here", retention="transient")
		claim = store.claim("acme.implementer", message_id=mid)
		delivery = b6._delivery(store, claim)
		assert delivered_bytes(delivery["message"]["content"]) == b"still here"
		store.close_claim(claim["claim_id"], participant=claim["participant"])
		# Bytes gone, manifest intact -- checked in STORAGE, because delivery
		# now refuses a leaf without bytes on any path. A message is delivered
		# only while pending or claimed, so absent bytes there always mean
		# something removed them, whatever the retention says.
		stored = store.get_message(mid)["parts"][0]
		assert stored["body"] is None
		assert stored["sha256"] is not None
		assert stored["content_type"] == b6.DEFAULT_CONTENT_TYPE
		assert store.get_message(mid)["manifest_sha256"] is not None
		with pytest.raises(b6.BatonError) as excinfo:
			b6._delivery(store, dict(claim))
		assert excinfo.value.exit_code == b6.EXIT_DAMAGE

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
			part = external_part(delivery["message"]["content"])
			assert part["attachment"]["root_id"] == "evidence"
			assert part["attachment"]["path"] == "e.md"
			assert part["attachment"]["generation"] == 1
			assert part["sha256"] and part["size"] == 8
			# Bytes are POINTED AT, never inlined into the envelope.
			assert part["encoding"] is None
			assert "text" not in part and "base64" not in part


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
		assert external_part(delivery["message"]["content"])["attachment"]["path"] == "e.md"


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


def notice_one(store, body=b"all hands", kind="announcement", ttl_seconds=None,
               **content):
	return store.send_notice("hq.lead", kind=kind,
	                         body=body, ttl_seconds=ttl_seconds, **content)


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
		assert delivered_bytes(result["notice"]["content"]) == b"broadcast"
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
		assert delivered_bytes(result["notice"]["content"]) == b"still live"
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
		assert delivered_bytes(result["message"]["content"]) == b"directed"
		assert result["claim"]["state"] == "active"
		with b6.open_instance(instance) as st:
			# no receipt written while a directed message was the delivery
			assert st.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0

	def test_notice_delivered_after_directed_drains(self, instance):
		with b6.open_instance(instance) as st:
			nid = notice_one(st, body=b"broadcast")
			send_one(st, body=b"directed")
		first = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert delivered_bytes(first["message"]["content"]) == b"directed"
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
		assert delivered_bytes(result["notice"]["content"]) == b"polled"

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
		assert delivered_bytes(result["notice"]["content"]) == b"raced"
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

	@pytest.mark.parametrize("body,content_type", [
		(b"\xc3\xa9 broadcast\n", b6.DEFAULT_CONTENT_TYPE),
		(b"\xff\xfe\x00binary", BINARY_TYPE)])
	def test_notice_body_lossless(self, instance, body, content_type):
		"""A notice carries the SAME content envelope as a directed message,
		and each part uses exactly one representation, chosen by its declared
		type rather than by whether the bytes happen to decode."""
		import hashlib as _h
		with b6.open_instance(instance) as st:
			notice_one(st, body=body, content_type=content_type)
		result = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		notice = result["notice"]
		content = notice["content"]
		assert content["content_type"] == b6.DEFAULT_CONTAINER_TYPE
		rep = only_part(content)
		assert part_bytes(rep) == body
		assert rep["size"] == len(body)
		assert rep["sha256"] == _h.sha256(body).hexdigest()
		assert rep["content_type"] == content_type
		if content_type == BINARY_TYPE:
			assert rep["encoding"] == b6.ENCODING_BASE64 and "text" not in rep
		else:
			assert rep["encoding"] == b6.ENCODING_TEXT and "base64" not in rep
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

	def test_cli_wait_exits_3_when_the_timeout_finds_nothing(self, instance):
		"""The exit status is a PUBLIC contract now that the docs tell runner
		loops to branch on it, and it was pinned only one layer down.

		`test_blocking_readiness_times_out_like_wait` asserts the helper
		raises with EXIT_NONE. That would stay green if dispatch, error
		handling or the exit-code mapping changed underneath it -- and the
		thing that breaks is every supervisor that treats non-zero as failure
		and would start reporting an idle mailbox as an error.

		Asserted through `main`, which is what those loops actually call."""
		code, out, _ = self._run(
			"--config", instance, "wait", "--participant", "acme.implementer",
			"--timeout", "0.2", "--interval", "0.1")
		assert code == 3, f"idle timeout exited {code}, not the documented 3"
		assert out == "", "an idle timeout printed a readiness object"

	def test_cli_wait_exits_0_when_work_exists(self, instance):
		"""The other half of the documented pair, at the same boundary."""
		with b6.open_instance(instance) as store:
			send_one(store)
		code, out, _ = self._run(
			"--config", instance, "wait", "--participant", "acme.implementer",
			"--timeout", "5")
		assert code == 0
		assert json.loads(out)["ready"] is True

	def test_cli_wait_reports_a_notice_without_consuming_it(self, instance):
		"""REWRITTEN for the 2026-08-10 ruling that plain `wait` is read-only.

		It previously asserted that `wait` delivered the notice AND that a
		following `see` found nothing left -- i.e. that waiting consumed it.
		That is exactly the behaviour the ruling removed, so the old assertion
		could not be kept: an unattended `wait` consuming a broadcast is the
		same hazard as one holding a claim.

		What replaces it is the mirror property: `wait` says a notice is
		there, and `see` still finds it."""
		code, out, _ = self._run(
			"--config", instance, "send-notice", "--participant", "hq.lead",
			"--kind", "announcement",
			"--body", "/dev/stdin")
		assert code == 0
		code, out, _ = self._run(
			"--config", instance, "wait", "--participant", "acme.implementer",
			"--timeout", "5")
		assert code == 0
		state = json.loads(out)
		assert state["ready"] is True and state["channel"] == "notice"
		assert "notice" not in state and "claim" not in state
		# STILL THERE: reading it is `see`'s job, and waiting did not do it.
		code, out, _ = self._run(
			"--config", instance, "see", "--participant", "acme.implementer")
		assert code == 0
		assert [n["kind"] for n in json.loads(out)["notices"]] == ["announcement"]

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
		assert delivered_bytes(delivery["message"]["content"]) == b"still deliverable"
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
		assert delivered_bytes(result["message"]["content"]) == b"published later"

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
		assert entry["parts"][0]["path"] == "EVIDENCE.md"
		assert entry["parts"][0]["root_id"] == "src"
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
			assert external_part(
				delivery["message"]["content"])["attachment"]["path"] == "EVIDENCE.md"
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
		assert delivered_bytes(result["message"]["content"]) == b"polled past damage"

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
			# the ORIGINAL pin survives on the PART and in the audit row
			row = st.conn.execute("SELECT * FROM quarantines WHERE message_id=?", (mid,)).fetchone()
			assert row["path"] == "EVIDENCE.md" and row["root_id"] == "src"
			part = external_row(st, mid)
			assert row["sha256"] == part["sha256"]
			assert row["part_id"] == part["part_id"]
			assert row["part_ordinal"] == "0"
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
			with pytest.raises(b6.BatonError, match="no externally stored part"):
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
					"reason, prior_state, part_id, part_ordinal, content_type, root_id, "
					"path, sha256, size, generation, failure, created_ts) "
					"VALUES('x',?,'hq.lead','r','pending','p0','0','text/plain; charset=utf-8',"
					"'src','p','s',1,1,'f','t')",
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
			"UPDATE quarantines SET sha256='0'*64"))
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
			assert stored_body(copy, mid) == b"must survive a restore"
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
		assert delivered_bytes(result["message"]["content"]) == b"already owned"

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
		assert delivered_bytes(result["message"]["content"]) == b"claimed then gated"


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

class TestTypedContentEnvelope:
	"""Acceptance for the typed, multipart-capable content envelope.

	One requirement per test, against the finding's required list."""

	# -- 1. an ordered parts collection from protocol inception ------------

	def test_every_message_carries_a_multipart_envelope(self, store):
		"""Even a one-part message delivers the container shape, so a reader
		never has to handle two envelope layouts and a second part is not a
		new shape."""
		mid = send_one(store, body=b"single")
		claim = store.claim("acme.implementer", message_id=mid)
		content = b6._delivery(store, claim)["message"]["content"]
		assert content["content_type"] == "multipart/mixed"
		assert isinstance(content["parts"], list) and len(content["parts"]) == 1
		assert content["manifest_sha256"]

	def test_notice_and_message_share_one_representation(self, store):
		"""The two inbound channels diverged once before. Same bytes and type
		on each must produce the same content envelope."""
		body = b"same bytes\n"
		mid = send_one(store, body=body)
		claim = store.claim("acme.implementer", message_id=mid)
		directed = b6._delivery(store, claim)["message"]["content"]
		store.send_notice("hq.lead", kind="announcement", body=body)
		broadcast = b6._notice_delivery(store.see("acme.reviewer")[0])["notice"]["content"]
		assert directed == broadcast

	# -- 2. leaf metadata and exactly one representation -------------------

	def test_leaf_carries_full_metadata_and_one_representation(self, store):
		mid = store.send("acme.reviewer", "acme.implementer", kind="doc",
		                 body=b"%PDF-1.4\n", content_type="application/pdf",
		                 disposition="attachment", part_name="report.pdf")
		claim = store.claim("acme.implementer", message_id=mid)
		part = only_part(b6._delivery(store, claim)["message"]["content"])
		assert part["content_type"] == "application/pdf"
		assert part["disposition"] == "attachment"
		assert part["part_name"] == "report.pdf"
		assert part["size"] == 9
		assert part["sha256"]
		assert part["encoding"] == b6.ENCODING_BASE64
		assert "text" not in part

	def test_representation_follows_the_declared_type_not_the_bytes(self, store):
		"""The old `utf8` field appeared only when the bytes decoded, so the
		same key came and went with the payload. Identical ASCII bytes under
		two declared types must now deliver through different keys."""
		ascii_bytes = b"plain ascii"
		as_text = store.send("acme.reviewer", "acme.implementer", kind="a",
		                     body=ascii_bytes)
		as_blob = store.send("acme.reviewer", "acme.implementer", kind="b",
		                     body=ascii_bytes, content_type=BINARY_TYPE)
		text_part = only_part(b6._delivery(
			store, store.claim("acme.implementer", message_id=as_text))["message"]["content"])
		blob_part = only_part(b6._delivery(
			store, store.claim("acme.implementer", message_id=as_blob))["message"]["content"])
		assert text_part["encoding"] == b6.ENCODING_TEXT
		assert "base64" not in text_part
		assert blob_part["encoding"] == b6.ENCODING_BASE64
		assert "text" not in blob_part
		assert part_bytes(text_part) == part_bytes(blob_part) == ascii_bytes

	def test_no_delivered_part_ever_carries_both_representations(self, store):
		"""Swept structurally rather than per-case: whatever the tree, no leaf
		may carry `text` and `base64` at once."""
		mid = store.send("acme.reviewer", "acme.implementer", kind="mixed", parts=[
			{"content_type": "text/plain; charset=utf-8", "body": b"words"},
			{"content_type": "image/png", "body": b"\x89PNG"},
			{"content_type": "text/markdown; charset=iso-8859-1", "body": b"\xe9"},
		])
		claim = store.claim("acme.implementer", message_id=mid)
		content = b6._delivery(store, claim)["message"]["content"]

		def walk(part):
			if "parts" in part:
				for child in part["parts"]:
					walk(child)
				return
			present = [k for k in ("text", "base64") if k in part]
			assert len(present) == 1, f"{part['content_type']} delivered {present}"
			assert part["encoding"] == present[0]
		for node in content["parts"]:
			walk(node)

	# -- 3. order and metadata stored independently of the owner row -------

	def test_parts_are_rows_with_explicit_order_not_owner_columns(self, store):
		mid = store.send("acme.reviewer", "acme.implementer", kind="ordered", parts=[
			{"content_type": "text/plain; charset=utf-8", "body": b"first"},
			{"content_type": "text/plain; charset=utf-8", "body": b"second"},
			{"content_type": "text/plain; charset=utf-8", "body": b"third"},
		])
		rows = store.conn.execute(
			"SELECT ordinal, sha256 FROM parts WHERE owner_kind='message' AND owner_id=? "
			"AND parent_part_id IS NULL ORDER BY ordinal", (mid,)).fetchall()
		assert [r["ordinal"] for r in rows] == [0, 1, 2]
		import hashlib as _h
		assert [r["sha256"] for r in rows] == [
			_h.sha256(b).hexdigest() for b in (b"first", b"second", b"third")]
		# The message row holds a container type and a manifest digest only --
		# no per-part column exists to hold a second part's metadata.
		columns = {r[1] for r in store.conn.execute("PRAGMA table_info(messages)")}
		assert "content_id" not in columns and "content_sha256" not in columns
		assert {"content_type", "manifest_sha256"} <= columns

	def test_part_order_is_uniquely_constrained_at_every_level(self, store):
		"""SQLite treats NULLs as distinct in a UNIQUE constraint, so a single
		composite index would leave TOP-LEVEL ordinals unconstrained. Both
		levels are checked because that was the easy thing to get wrong."""
		mid = store.send("acme.reviewer", "acme.implementer", kind="dup", parts=[
			{"content_type": "multipart/alternative", "parts": [
				{"content_type": "text/plain; charset=utf-8", "body": b"a"},
			]},
		])
		root = store.conn.execute(
			"SELECT part_id FROM parts WHERE owner_id=? AND parent_part_id IS NULL",
			(mid,)).fetchone()[0]
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO parts(part_id, owner_kind, owner_id, parent_part_id, ordinal, "
					"content_type, disposition, sha256, size, created_ts) "
					"VALUES('dup-root', 'message', ?, NULL, 0, 'text/plain; charset=utf-8', "
					"'inline', 'x', 1, 'now')", (mid,))
		finally:
			store._txn_rollback()
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO parts(part_id, owner_kind, owner_id, parent_part_id, ordinal, "
					"content_type, disposition, sha256, size, created_ts) "
					"VALUES('dup-child', 'message', ?, ?, 0, 'text/plain; charset=utf-8', "
					"'inline', 'x', 1, 'now')", (mid, root))
		finally:
			store._txn_rollback()

	def test_container_part_holds_no_bytes_and_leaf_holds_no_children(self, store):
		"""Enforced by the schema, not only by the Python that normally writes
		it -- the same standard every other guarded table is held to."""
		mid = send_one(store)
		store._txn_begin("send")
		try:
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO parts(part_id, owner_kind, owner_id, parent_part_id, ordinal, "
					"content_type, disposition, sha256, size, created_ts) "
					"VALUES('bad-container', 'message', ?, NULL, 9, 'multipart/mixed', "
					"'inline', 'deadbeef', 4, 'now')", (mid,))
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO parts(part_id, owner_kind, owner_id, parent_part_id, ordinal, "
					"content_type, disposition, sha256, size, created_ts) "
					"VALUES('bad-leaf', 'message', ?, NULL, 8, 'text/plain; charset=utf-8', "
					"'inline', NULL, NULL, 'now')", (mid,))
		finally:
			store._txn_rollback()

	# -- 4. retry identity covers the whole manifest, metadata included ----

	@pytest.mark.parametrize("changed", ["content_type", "disposition", "part_name"])
	def test_retry_with_identical_bytes_but_changed_metadata_fails_closed(self, store, changed):
		"""THE requirement of this finding. Every byte matches; only metadata
		moved. Comparing a body hash would report `already_committed` for an
		operation that was never committed."""
		send_one(store)
		claim = store.claim("acme.implementer")
		base = dict(kind="answer", body=b"identical", content_type="text/plain; charset=utf-8",
		            disposition="inline", part_name="a.txt")
		store.reply(claim["claim_id"], participant=claim["participant"], **base)
		retried = dict(base)
		retried[changed] = {"content_type": "text/markdown; charset=utf-8",
		                    "disposition": "attachment", "part_name": "b.txt"}[changed]
		with pytest.raises(b6.BatonError, match="content manifest differs") as excinfo:
			store.reply(claim["claim_id"], participant=claim["participant"], **retried)
		assert excinfo.value.exit_code == b6.EXIT_PROTOCOL
		# The unchanged retry still redelivers, so the refusal above is the
		# metadata check and not a broken retry path.
		again = store.reply(claim["claim_id"], participant=claim["participant"], **base)
		assert again["already_committed"] is True

	def test_retry_with_reordered_parts_fails_closed(self, store):
		"""Same bytes, same metadata, different ORDER. Order is part of what
		the message means, so it is part of the manifest."""
		send_one(store)
		claim = store.claim("acme.implementer")
		first = {"content_type": "text/plain; charset=utf-8", "body": b"one"}
		second = {"content_type": "text/plain; charset=utf-8", "body": b"two"}
		store.reply(claim["claim_id"], participant=claim["participant"],
		            kind="answer", parts=[first, second])
		with pytest.raises(b6.BatonError, match="content manifest differs"):
			store.reply(claim["claim_id"], participant=claim["participant"],
			            kind="answer", parts=[second, first])
		assert store.reply(claim["claim_id"], participant=claim["participant"],
		                   kind="answer", parts=[first, second])["already_committed"] is True

	def test_close_retry_metadata_mismatch_also_fails_closed(self, store):
		"""`reply` and `close` are two seams; a test of one would not catch
		them diverging."""
		send_one(store)
		claim = store.claim("acme.implementer")
		store.close_claim(claim["claim_id"], participant=claim["participant"],
		                  body=b"noted", content_type="text/plain; charset=utf-8")
		with pytest.raises(b6.BatonError, match="content manifest differs"):
			store.close_claim(claim["claim_id"], participant=claim["participant"],
			                  body=b"noted", content_type="text/markdown; charset=utf-8")

	# -- 5. materialize addresses a specific part --------------------------

	def test_materialize_addresses_a_part(self, tmp_path):
		target = tmp_path / "proj"
		target.mkdir()
		instance = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["participants"]["acme.implementer"] = {
			"projection_dir": str(target), "projection_prefix": "review"}
		with open(instance, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(instance)
		with b6.open_instance(instance) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="report", parts=[
				{"content_type": "text/markdown; charset=utf-8", "body": b"# summary\n"},
				{"content_type": "multipart/alternative", "parts": [
					{"content_type": "text/plain; charset=utf-8", "body": b"plain\n"},
					{"content_type": "text/html; charset=utf-8", "body": b"<p>rich</p>\n"},
				]},
			])
		# Part 0 keeps the historical unsuffixed name so single-part projection
		# directories do not churn; the suffix follows the declared type.
		zero = b6.materialize(instance, mid, str(target), prefix="review")
		assert zero.endswith(f"{mid}.md")
		assert open(zero, "rb").read() == b"# summary\n"
		nested = b6.materialize(instance, mid, str(target), prefix="review", part="1.1")
		assert nested.endswith(f"{mid}-part1-1.html")
		assert open(nested, "rb").read() == b"<p>rich</p>\n"
		# A container has no bytes to project, and an absent part is EXIT_NONE.
		with pytest.raises(b6.BatonError, match="container"):
			b6.materialize(instance, mid, str(target), prefix="review", part="1")
		with pytest.raises(b6.BatonError) as excinfo:
			b6.materialize(instance, mid, str(target), prefix="review", part="7")
		assert excinfo.value.exit_code == b6.EXIT_NONE
		# doctor still reconciles the projection directory it owns, across the
		# new per-part filenames as well as the historical unsuffixed one.
		report = b6.doctor(instance)
		assert report["projections"]["checked"] == 2
		assert report["projections"]["orphans"] == []

	# -- 6/7. readers accept multipart; containers nest without a schema change

	def test_nested_containers_need_no_schema_change(self, store):
		"""multipart/alternative inside multipart/mixed, round-tripped through
		storage and delivery on the SAME tables a one-part message uses."""
		before = {r[0] for r in store.conn.execute(
			"SELECT name FROM sqlite_master WHERE type='table'")}
		mid = store.send("acme.reviewer", "acme.implementer", kind="rich", parts=[
			{"content_type": "multipart/alternative", "parts": [
				{"content_type": "text/plain; charset=utf-8", "body": b"plain\n"},
				{"content_type": "text/html; charset=utf-8", "body": b"<p>rich</p>\n"},
			]},
			{"content_type": "image/png", "disposition": "attachment",
			 "part_name": "chart.png", "body": b"\x89PNG\r\n\x1a\n"},
		])
		after = {r[0] for r in store.conn.execute(
			"SELECT name FROM sqlite_master WHERE type='table'")}
		assert before == after
		claim = store.claim("acme.implementer", message_id=mid)
		content = b6._delivery(store, claim)["message"]["content"]
		alternative, image = content["parts"]
		assert alternative["content_type"] == "multipart/alternative"
		assert [p["content_type"] for p in alternative["parts"]] == [
			"text/plain; charset=utf-8", "text/html; charset=utf-8"]
		assert alternative["parts"][0]["text"] == "plain\n"
		assert "size" not in alternative and "encoding" not in alternative
		assert image["part_name"] == "chart.png" and image["disposition"] == "attachment"
		assert part_bytes(image) == b"\x89PNG\r\n\x1a\n"

	def test_multipart_survives_gc_and_expire(self, store):
		"""Deleting a tree must not orphan children behind a parent's foreign
		key, and must take every content row with it."""
		nid = store.send_notice("hq.lead", kind="announcement", parts=[
			{"content_type": "multipart/alternative", "parts": [
				{"content_type": "text/plain; charset=utf-8", "body": b"n-plain"},
			]},
		], ttl_seconds=1)
		assert store.conn.execute(
			"SELECT COUNT(*) FROM parts WHERE owner_id=?", (nid,)).fetchone()[0] == 2
		store.expire("hq.lead", notice_id=nid)
		assert store.conn.execute(
			"SELECT COUNT(*) FROM parts WHERE owner_id=?", (nid,)).fetchone()[0] == 0
		assert store.conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0] == 0

	# -- open questions, answered ------------------------------------------

	def test_default_content_type_is_declared_markdown(self, store):
		"""An undeclared body defaults to text/markdown WITH a charset, and the
		type is stated in every delivery rather than left implicit."""
		assert b6.DEFAULT_CONTENT_TYPE == "text/markdown; charset=utf-8"
		mid = send_one(store, body=b"# hi\n")
		claim = store.claim("acme.implementer", message_id=mid)
		part = only_part(b6._delivery(store, claim)["message"]["content"])
		assert part["content_type"] == "text/markdown; charset=utf-8"

	def test_text_types_must_declare_a_charset(self, store):
		"""RFC 7763 makes charset required for text/markdown, and the delivery
		encoding depends on it, so a bare text/* type is refused with the fix
		named rather than silently rewritten."""
		with pytest.raises(b6.BatonError, match="charset"):
			send_one(store, body=b"x", content_type="text/markdown")
		with pytest.raises(b6.BatonError, match="charset"):
			send_one(store, body=b"x", content_type="text/plain")
		# Non-text types need no charset.
		assert send_one(store, body=b"x", content_type="application/pdf")

	@pytest.mark.parametrize("raw,canonical", [
		("text/markdown; charset=UTF-8", "text/markdown; charset=utf-8"),
		("TEXT/Markdown;charset=utf-8", "text/markdown; charset=utf-8"),
		("text/markdown ; charset=utf-8 ", "text/markdown; charset=utf-8"),
		('text/plain; charset="utf-8"', "text/plain; charset=utf-8"),
	])
	def test_media_types_canonicalize_to_one_spelling(self, raw, canonical):
		"""The manifest digest hashes this string, so two spellings of one type
		must not read as two different contents."""
		assert b6.canonical_media_type(raw) == canonical

	@pytest.mark.parametrize("raw", [
		"", "text", "text/", "/markdown", "text/markdown; charset",
		"text/markdown; charset=utf-8; charset=ascii", 'text/plain; charset="utf-8',
		"text/pl ain; charset=utf-8", "multipart/mixed; boundary=xyz"])
	def test_malformed_media_types_are_refused(self, raw):
		with pytest.raises(b6.BatonError):
			b6.canonical_media_type(raw)

	@pytest.mark.parametrize("name", [
		"nul\x00byte", "ctrl\x01", "", "x" * 256])
	def test_part_name_refuses_what_baton_cannot_carry(self, store, name):
		"""SUPERSEDED by protocol 10 and its ruled part-name semantics.

		(Named rather than cited: this file ships inside a reusable checkout,
		and a path into one project's notes is not reusable by anyone else.
		The purity gate caught the citation immediately, which is the fourth
		time it has caught me and the reason it exists.)

		This used to include `../escape`, `a/b`, `a\\b`, `.`, `..` and `-rf`,
		refused on the theory that a careless consumer might use the label as a
		path. Protocol 10 rejects the premise: a part name is an uninterpreted
		label, the recipient decides whether it ever becomes a file, and
		refusing those spellings was Baton deciding what a label means to
		somebody else's software. They are accepted losslessly now and pinned
		as such in `TestPartNameIsNotAFilename`.

		What remains is about BATON: an empty label is not a name, a control
		character is a display-injection hazard in every inbox that draws it,
		NUL cannot cross the boundaries this string crosses, and the byte bound
		exists because the label sits in every manifest and on one line of a
		list."""
		with pytest.raises(b6.BatonError):
			send_one(store, body=b"x", part_name=name)

	def test_materialize_ignores_the_advisory_part_name(self, instance, tmp_path):
		target = tmp_path / "proj"
		target.mkdir()
		with b6.open_instance(instance) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="doc",
			                 body=b"# doc\n", part_name="attacker-chosen.md")
		path = b6.materialize(instance, mid, str(target), prefix="review")
		assert os.path.basename(path).startswith("review-")
		assert "attacker-chosen" not in path

	def test_transient_ceiling_bounds_the_message_not_each_part(self, store):
		"""Bounding each part instead would let a caller carry an unbounded
		transient payload by splitting it."""
		half = b"x" * (b6.TRANSIENT_BODY_MAX_BYTES // 2 + 1)
		with pytest.raises(b6.BatonError, match="across all parts"):
			store.send("acme.reviewer", "acme.implementer", kind="big",
			           retention="transient", parts=[
				{"content_type": BINARY_TYPE, "body": half},
				{"content_type": BINARY_TYPE, "body": half}])

	# -- damage: the manifest is the check bytes alone cannot make ---------

	def test_tampered_part_tree_is_damage_not_a_silent_redefinition(self, instance):
		"""A part dropped behind the API leaves every remaining byte valid.
		Only the manifest digest notices, and it must refuse to deliver."""
		with b6.open_instance(instance) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="two", parts=[
				{"content_type": "text/plain; charset=utf-8", "body": b"one"},
				{"content_type": "text/plain; charset=utf-8", "body": b"two"},
			])
		_raw_corrupt(instance, lambda conn: conn.execute(
			"DELETE FROM parts WHERE owner_id=? AND ordinal=1", (mid,)))
		with b6.open_instance(instance) as store:
			claim = store.claim("acme.implementer", message_id=mid)
			with pytest.raises(b6.BatonError) as excinfo:
				b6._delivery(store, claim)
			assert excinfo.value.exit_code == b6.EXIT_DAMAGE
		report = b6.doctor(instance)
		assert report["ok"] is False
		assert any("content manifest" in p for p in report["problems"])

	def test_retyped_part_is_damage(self, instance):
		"""Same bytes, same order, different declared type: the message now
		means something else, and the manifest is what catches it."""
		with b6.open_instance(instance) as store:
			mid = send_one(store, body=b"# doc\n")
		_raw_corrupt(instance, lambda conn: conn.execute(
			"UPDATE parts SET content_type='text/html; charset=utf-8' WHERE owner_id=?", (mid,)))
		report = b6.doctor(instance)
		assert report["ok"] is False
		assert any("content manifest" in p for p in report["problems"])

	# -- byte presence: the check the manifest deliberately cannot make -----

	def test_missing_bytes_outside_retention_is_damage_not_a_scrub(self, instance):
		"""Reported by baton.reviewer against the committed protocol-8 build,
		reproduced before fixing.

		The manifest digest EXCLUDES byte presence, on purpose, so that it
		survives lawful transient scrubbing. That left nothing checking byte
		presence at all: deleting a durable message's content rows read as
		healthy and delivered `encoding: null`, indistinguishable from a
		consumed transient."""
		with b6.open_instance(instance) as store:
			mid = send_one(store, body=b"durable payload", retention="durable")

		def strip(conn):
			cid = conn.execute(
				"SELECT content_id FROM parts WHERE owner_id=?", (mid,)).fetchone()[0]
			conn.execute("UPDATE parts SET content_id=NULL WHERE owner_id=?", (mid,))
			conn.execute("DELETE FROM contents WHERE content_id=?", (cid,))
		_raw_corrupt(instance, strip)

		report = b6.doctor(instance)
		assert report["ok"] is False
		assert any("no stored bytes" in p for p in report["problems"])
		with b6.open_instance(instance) as store:
			claim = store.claim("acme.implementer", message_id=mid)
			with pytest.raises(b6.BatonError) as excinfo:
				b6._delivery(store, claim)
			assert excinfo.value.exit_code == b6.EXIT_DAMAGE

	def test_lawful_transient_scrub_stays_healthy(self, instance):
		"""The other side of the same check: the legitimate case must not
		become a false positive, or the check above is useless."""
		with b6.open_instance(instance) as store:
			mid = send_one(store, body=b"ephemeral", retention="transient")
			claim = store.claim("acme.implementer", message_id=mid)
			store.close_claim(claim["claim_id"], participant=claim["participant"])
			stored = store.get_message(mid)["parts"][0]
			assert stored["body"] is None and stored["sha256"] is not None
		report = b6.doctor(instance)
		assert report["ok"] is True and report["problems"] == []

	def test_notice_part_without_bytes_is_always_damage(self, instance):
		"""A notice is never scrubbed -- expire and gc delete it whole -- so a
		notice part with no bytes has no lawful explanation."""
		with b6.open_instance(instance) as store:
			nid = notice_one(store, body=b"broadcast")
		_raw_corrupt(instance, lambda conn: conn.execute(
			"UPDATE parts SET content_id=NULL WHERE owner_id=?", (nid,)))
		report = b6.doctor(instance)
		assert report["ok"] is False
		assert any("no stored bytes" in p for p in report["problems"])

	# -- reply dispositions were excluded from the manifest pass -----------

	def test_reply_disposition_manifest_is_checked_against_its_response(self, instance):
		"""Reported by baton.reviewer, reproduced before fixing.

		A reply disposition stores no parts of its own -- its content IS the
		response message -- so the owner-manifest pass skipped it and left it
		unchecked entirely. doctor read healthy while effectively-once was
		broken underneath: a CORRECT retry was refused as a mismatch."""
		with b6.open_instance(instance) as store:
			send_one(store)
			claim = store.claim("acme.implementer")
			store.reply(claim["claim_id"], participant=claim["participant"],
			            kind="answer", body=b"the answer")
		_raw_corrupt(instance, lambda conn: conn.execute(
			"UPDATE dispositions SET manifest_sha256=? WHERE claim_id=?",
			("0" * 64, claim["claim_id"])))
		report = b6.doctor(instance)
		assert report["ok"] is False
		assert any("reply disposition" in p and "disagrees" in p
		           for p in report["problems"])

	def test_reply_disposition_cannot_dangle_past_its_response(self, instance):
		"""Deleting the response message out from under a reply disposition is
		caught by FOREIGN KEY integrity at open, before doctor's own pass runs.

		That is the stronger guarantee, so it is what gets pinned. doctor keeps
		a branch for a dangling reference so the manifest pass reports rather
		than crashes, but the reference should never reach it."""
		with b6.open_instance(instance) as store:
			send_one(store)
			claim = store.claim("acme.implementer")
			result = store.reply(claim["claim_id"], participant=claim["participant"],
			                     kind="answer", body=b"the answer")
		_raw_corrupt(instance, lambda conn: conn.execute(
			"DELETE FROM messages WHERE id=?", (result["response_message_id"],)))
		with pytest.raises(b6.BatonError, match="foreign_key_check") as excinfo:
			b6.doctor(instance)
		assert excinfo.value.exit_code == b6.EXIT_DAMAGE

	# -- R4: explicit metadata is validated, never silently defaulted -------

	@pytest.mark.parametrize("field,value", [
		("content_type", ""), ("disposition", ""), ("part_name", ""),
		("content_type", "not-a-media-type"), ("disposition", "sideways"),
	])
	def test_explicit_invalid_metadata_is_rejected_not_defaulted(self, store, field, value):
		"""`raw.get(k) or DEFAULT` could not tell "absent" from "supplied
		empty", so an explicit empty content_type became text/markdown and an
		explicit empty disposition became inline -- the caller asked for
		something meaningless and got silence plus a type it never named."""
		with pytest.raises(b6.BatonError):
			store.send("acme.reviewer", "acme.implementer", kind="k",
			           parts=[{"body": b"x", field: value}])

	def test_absent_metadata_still_defaults(self, store):
		"""The other side of the same check: omitting a field must still
		default, or the fix above is just a new way to fail."""
		nodes = b6.normalize_parts([{"body": b"x"}])
		assert nodes[0]["content_type"] == b6.DEFAULT_CONTENT_TYPE
		assert nodes[0]["disposition"] == b6.DISPOSITION_INLINE
		assert nodes[0]["part_name"] is None

	@pytest.mark.parametrize("kwargs", [
		{"content_type": "application/pdf"},
		{"disposition": "attachment"},
		{"part_name": "evidence.pdf"},
		{"container_type": "multipart/alternative"},
	])
	def test_metadata_without_content_is_refused(self, store, kwargs):
		"""content_spec returned (None, None) and discarded everything passed
		beside it. An attachment-only send or a bodyless close that names a
		content type is asking for something the operation cannot do, and
		dropping it silently tells the caller it worked."""
		with pytest.raises(b6.BatonError, match="no content to describe"):
			b6.content_spec(None, None, **kwargs)

	def test_bodyless_close_refuses_content_metadata(self, store):
		send_one(store)
		claim = store.claim("acme.implementer")
		with pytest.raises(b6.BatonError, match="no content to describe"):
			store.close_claim(claim["claim_id"], participant=claim["participant"],
			                  content_type="application/pdf")
		# The same close without the metadata still works.
		assert store.close_claim(claim["claim_id"],
		                         participant=claim["participant"])["kind"] == "close"

	def test_attachment_only_send_applies_content_metadata(self, tmp_path):
		"""Under convergence this metadata is no longer orphaned -- it types
		the external PART, which is exactly what the old model could not do.
		An attachment used to arrive with no declared media type at all."""
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
			mid = store.send("acme.reviewer", "acme.implementer", kind="ev",
			                 attach={"root_id": "evidence", "path": "e.md"},
			                 content_type="text/plain; charset=utf-8",
			                 part_name="e.md")
			claim = store.claim("acme.implementer", message_id=mid)
			part = external_part(b6._delivery(store, claim)["message"]["content"])
			assert part["content_type"] == "text/plain; charset=utf-8"
			assert part["disposition"] == "attachment"
			assert part["part_name"] == "e.md"
		# An undeclared external part gets the RFC 2046 unknown-bytes type
		# rather than a guess sniffed from the file extension.
		with b6.open_instance(config_path) as store:
			mid2 = store.send("acme.reviewer", "acme.implementer", kind="ev",
			                  attach={"root_id": "evidence", "path": "e.md"})
			claim2 = store.claim("acme.implementer", message_id=mid2)
			part2 = external_part(b6._delivery(store, claim2)["message"]["content"])
			assert part2["content_type"] == b6.DEFAULT_ATTACHMENT_TYPE

	def test_cli_flags_do_not_forge_an_explicit_value(self, tmp_path):
		"""argparse defaults would make an omitted flag indistinguishable from
		an explicit one, which is what let the store default silently."""
		parser = b6._build_parser()
		ns = parser.parse_args(["--config", "/x", "send", "--participant", "a.b",
		                        "--to", "c.d", "--kind", "k"])
		assert ns.content_type is None and ns.disposition is None and ns.part_name is None
		ns2 = parser.parse_args(["--config", "/x", "send", "--participant", "a.b",
		                         "--to", "c.d", "--kind", "k",
		                         "--content-type", "application/pdf"])
		assert ns2.content_type == "application/pdf"

	# -- R5: part_name bound is bytes, as the contract claims ---------------

	def test_part_name_cap_is_bytes_not_characters(self, store):
		"""The documented cap was 255 bytes while the code counted Python
		characters, so 255 multibyte characters -- 510 bytes -- passed. The
		bound is bytes because that is what a filesystem enforces."""
		assert b6.validate_part_name("a" * 255) == "a" * 255
		with pytest.raises(b6.BatonError, match="255 bytes"):
			b6.validate_part_name("a" * 256)
		with pytest.raises(b6.BatonError, match="255 bytes"):
			b6.validate_part_name("é" * 255)   # 510 bytes as UTF-8
		assert b6.validate_part_name("é" * 127)  # 254 bytes, fits

	# -- R5: gc must reach the actual deletion path, not only expire -------

	def test_multipart_survives_gc(self, store):
		"""The earlier coverage exercised only `expire`. gc has its own
		deletion path, and parts.parent_part_id is a self-referencing foreign
		key -- deleting a nested tree parent-first would orphan its children."""
		mid = store.send("acme.reviewer", "acme.implementer", kind="nested",
		                 retention="transient", parts=[
			{"content_type": "multipart/alternative", "parts": [
				{"content_type": "text/plain; charset=utf-8", "body": b"a"},
				{"content_type": "text/plain; charset=utf-8", "body": b"b"},
			]},
			{"content_type": "text/plain; charset=utf-8", "body": b"c"},
		])
		claim = store.claim("acme.implementer", message_id=mid)
		# The close disposition owns its own nested tree as well, so gc must
		# clear both owners. It stays transient: a DURABLE close deliberately
		# anchors the message against collection, which would make this test
		# pass for the wrong reason.
		store.close_claim(claim["claim_id"], participant=claim["participant"],
		                  retention="transient", parts=[
			{"content_type": "multipart/alternative", "parts": [
				{"content_type": "text/plain; charset=utf-8", "body": b"closed"},
			]},
		])
		assert store.conn.execute(
			"SELECT COUNT(*) FROM parts WHERE owner_id=?", (mid,)).fetchone()[0] == 4
		assert store.conn.execute(
			"SELECT COUNT(*) FROM parts WHERE owner_id=?",
			(claim["claim_id"],)).fetchone()[0] == 2
		result = store.gc(participant="hq.lead", now="2027-01-01T00:00:00Z")
		assert mid in result["messages"]
		for owner in (mid, claim["claim_id"]):
			assert store.conn.execute(
				"SELECT COUNT(*) FROM parts WHERE owner_id=?", (owner,)).fetchone()[0] == 0
		assert store.conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0] == 0

	def test_dump_covers_the_parts_table(self, instance):
		with b6.open_instance(instance) as store:
			send_one(store, body=b"dumped")
		out = b6.dump(instance)
		assert "parts" in out and len(out["parts"]) == 1
		assert out["parts"][0]["content_type"] == b6.DEFAULT_CONTENT_TYPE
		# Bytes stay redacted wherever they appear.
		assert "bytes>" in out["contents"][0]["body"]


class TestAttachmentPartConvergence:
	"""R3: external storage is a PART representation, not a second content
	model. One message, one ordered manifest, one retry identity."""

	@pytest.fixture
	def rooted(self, tmp_path):
		root = tmp_path / "src"
		root.mkdir()
		(root / "EVIDENCE.md").write_bytes(b"pinned evidence\n")
		(root / "SECOND.md").write_bytes(b"second evidence\n")
		config_path = str(tmp_path / "baton.json")
		cfg = make_config()
		cfg["roots"] = {"src": str(root)}
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		b6.init_instance(config_path)
		return config_path, root

	def test_messages_table_has_no_attachment_columns(self, store):
		"""The five `attach_*` columns are gone. Their absence is the check --
		while they exist, something can keep writing the old model."""
		columns = {r[1] for r in store.conn.execute("PRAGMA table_info(messages)")}
		assert not any(c.startswith("attach") for c in columns)
		part_columns = {r[1] for r in store.conn.execute("PRAGMA table_info(parts)")}
		assert {"storage", "root_id", "path", "generation"} <= part_columns

	def test_inline_note_and_pinned_evidence_in_one_message(self, rooted):
		"""The case protocol 8 could not express at all: a `CHECK` forced a
		choice between "here is the file" and "here is what it means", so one
		statement had to be split across two messages that could interleave."""
		config_path, _ = rooted
		with b6.open_instance(config_path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="report", parts=[
				{"content_type": "text/markdown; charset=utf-8",
				 "body": b"# Findings\nSee attached.\n"},
				{"content_type": "text/markdown; charset=utf-8", "disposition": "attachment",
				 "part_name": "EVIDENCE.md", "attach": "src:EVIDENCE.md"},
			])
			claim = store.claim("acme.implementer", message_id=mid)
			content = b6._delivery(store, claim)["message"]["content"]
		inline, external = content["parts"]
		assert inline["storage"] == "inline"
		assert inline["text"] == "# Findings\nSee attached.\n"
		assert inline["attachment"] is None
		assert external["storage"] == "external"
		assert external["content_type"] == "text/markdown; charset=utf-8"
		assert external["attachment"]["path"] == "EVIDENCE.md"
		# External bytes are POINTED AT, never copied into the envelope.
		assert external["encoding"] is None
		assert "text" not in external and "base64" not in external
		assert external["sha256"] and external["size"] == 16

	def test_several_external_parts_in_one_message(self, rooted):
		"""One attachment per message was a limit with no reason to exist once
		parts are rows."""
		config_path, _ = rooted
		with b6.open_instance(config_path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="report", parts=[
				{"content_type": "text/markdown; charset=utf-8",
				 "disposition": "attachment", "attach": "src:EVIDENCE.md"},
				{"content_type": "text/markdown; charset=utf-8",
				 "disposition": "attachment", "attach": "src:SECOND.md"},
			])
			claim = store.claim("acme.implementer", message_id=mid)
			parts = b6._delivery(store, claim)["message"]["content"]["parts"]
		assert [p["attachment"]["path"] for p in parts] == ["EVIDENCE.md", "SECOND.md"]

	def test_manifest_covers_external_parts_through_one_mechanism(self, rooted):
		"""Retry identity is ONE mechanism. The same bytes pinned at a
		different path, or carried inline instead of externally, are different
		messages -- only one of them can go stale under your feet."""
		config_path, root = rooted
		with b6.open_instance(config_path) as store:
			send_one(store)
			claim = store.claim("acme.implementer")
			base = dict(kind="answer", parts=[
				{"content_type": "text/markdown; charset=utf-8",
				 "disposition": "attachment", "attach": "src:EVIDENCE.md"}])
			store.reply(claim["claim_id"], participant=claim["participant"], **base)
			assert store.reply(claim["claim_id"], participant=claim["participant"],
			                   **base)["already_committed"] is True
			# Same bytes, different root path -> different manifest.
			(root / "COPY.md").write_bytes(b"pinned evidence\n")
			with pytest.raises(b6.BatonError, match="content manifest differs"):
				store.reply(claim["claim_id"], participant=claim["participant"],
				            kind="answer", parts=[
					{"content_type": "text/markdown; charset=utf-8",
					 "disposition": "attachment", "attach": "src:COPY.md"}])
			# Same bytes, carried INLINE instead of pinned -> different manifest.
			with pytest.raises(b6.BatonError, match="content manifest differs"):
				store.reply(claim["claim_id"], participant=claim["participant"],
				            kind="answer", parts=[
					{"content_type": "text/markdown; charset=utf-8",
					 "disposition": "attachment", "body": b"pinned evidence\n"}])

	def test_damaged_external_part_never_delivers_and_does_not_block(self, rooted):
		"""The behaviour from the damaged-attachment work must survive
		convergence: damaged content is never delivered, and one damaged
		message must not block the healthy ones behind it."""
		config_path, root = rooted
		with b6.open_instance(config_path) as store:
			damaged = store.send("acme.reviewer", "acme.implementer", kind="ev", parts=[
				{"content_type": "text/markdown; charset=utf-8",
				 "body": b"note beside the evidence\n"},
				{"content_type": "text/markdown; charset=utf-8",
				 "disposition": "attachment", "attach": "src:EVIDENCE.md"},
			])
			healthy = send_one(store, body=b"published behind the damage")
		(root / "EVIDENCE.md").write_bytes(b"replaced after publication\n")
		with b6.open_instance(config_path) as store:
			# The healthy message behind it is delivered, not blocked.
			claim = store.claim("acme.implementer")
			assert claim["message_id"] == healthy
			store.close_claim(claim["claim_id"], participant=claim["participant"])
			# Naming the damaged one explicitly still fails closed.
			with pytest.raises(b6.BatonError) as excinfo:
				store.claim("acme.implementer", message_id=damaged)
			assert excinfo.value.exit_code == b6.EXIT_DAMAGE
			# Its INLINE part is healthy, but the message is damaged as a whole:
			# partial delivery would be delivering an incomplete statement.
			scan = store.scan("acme.implementer")
			assert [d["id"] for d in scan["damaged"]] == [damaged]
			assert scan["damaged"][0]["parts"][0]["path"] == "EVIDENCE.md"

	def test_quarantine_records_the_damaged_part(self, rooted):
		config_path, root = rooted
		with b6.open_instance(config_path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="ev", parts=[
				{"content_type": "text/markdown; charset=utf-8", "body": b"note\n"},
				{"content_type": "text/markdown; charset=utf-8",
				 "disposition": "attachment", "attach": "src:EVIDENCE.md"},
			])
		(root / "EVIDENCE.md").write_bytes(b"replaced\n")
		with b6.open_instance(config_path) as store:
			result = store.quarantine_attachment(mid, participant="hq.lead",
			                                     reason="pin invalidated")
			assert result["state"] == "quarantined"
			row = store.conn.execute(
				"SELECT * FROM quarantines WHERE message_id=?", (mid,)).fetchone()
			# The audit row names the PART, by id and by manifest address, so
			# a reader can tell WHICH of several attachments went stale.
			assert row["part_ordinal"] == "1"
			assert row["path"] == "EVIDENCE.md"
			assert row["content_type"] == "text/markdown; charset=utf-8"
			part = store.conn.execute(
				"SELECT part_id FROM parts WHERE part_id=?", (row["part_id"],)).fetchone()
			assert part is not None
		report = b6.doctor(config_path)
		assert report["ok"] is True   # acknowledged damage no longer blocks health
		assert any("quarantined" in w for w in report["warnings"])

	def test_doctor_reports_a_damaged_external_part(self, rooted):
		config_path, root = rooted
		with b6.open_instance(config_path) as store:
			store.send("acme.reviewer", "acme.implementer", kind="ev", parts=[
				{"content_type": "text/markdown; charset=utf-8",
				 "disposition": "attachment", "attach": "src:EVIDENCE.md"}])
		(root / "EVIDENCE.md").write_bytes(b"mutated\n")
		report = b6.doctor(config_path)
		assert report["ok"] is False
		assert any("pinned hash" in p for p in report["problems"])

	def test_external_part_survives_regen_and_holds_its_binding(self, rooted):
		"""Root binding generations were pinned per message; they are pinned
		per part now, and regen must still refuse to strand them."""
		config_path, root = rooted
		with b6.open_instance(config_path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="ev",
			                 attach="src:EVIDENCE.md")
			assert external_row(store, mid)["generation"] == 1
		cfg = make_config(generation=2)
		cfg["roots"] = {}          # drops a root a live part still pins
		with open(config_path, "w") as handle:
			json.dump(cfg, handle)
		with pytest.raises(b6.BatonError, match="must keep its accepted mapping"):
			b6.regen_instance(config_path, participant="hq.lead")

	def test_external_parts_are_refused_where_damage_cannot_be_resolved(self, rooted):
		"""Reported by baton.reviewer at the release gate, reproduced before
		fixing: external leaves were accepted on notices and close
		dispositions, pinned at publication, and then never verified again.

		A damaged broadcast was the worst of it -- `see` committed the
		at-most-once receipt and delivered the pin, so that participant lost
		the content permanently while `doctor` reported healthy.

		The contract chosen: external storage lives only where its damage
		lifecycle does. A message has claim-time verification,
		skip-and-continue, quarantine and doctor. A notice has no claim to
		skip or quarantine, and its receipt commits inside a write transaction
		where file IO does not belong. A close disposition is never delivered
		at all."""
		config_path, _ = rooted
		external = [{"content_type": "text/markdown; charset=utf-8",
		             "disposition": "attachment", "attach": "src:EVIDENCE.md"}]
		with b6.open_instance(config_path) as store:
			with pytest.raises(b6.BatonError, match="notice cannot carry an externally stored part"):
				store.send_notice("hq.lead", kind="announcement", parts=external)
			mid = send_one(store)
			claim = store.claim("acme.implementer", message_id=mid)
			with pytest.raises(b6.BatonError,
			                   match="close disposition cannot carry an externally stored part"):
				store.close_claim(claim["claim_id"], participant=claim["participant"],
				                  retention="durable", parts=external)
			# Nested inside a container is still refused -- the check walks.
			with pytest.raises(b6.BatonError, match="cannot carry an externally stored part"):
				store.send_notice("hq.lead", kind="announcement", parts=[
					{"content_type": "multipart/alternative", "parts": external}])
			# A directed message still accepts it, and the claim still resolves.
			assert store.send("acme.reviewer", "acme.implementer", kind="ev",
			                  attach="src:EVIDENCE.md")

	def test_doctor_catches_an_external_part_on_a_forbidden_owner(self, rooted):
		"""Defence in depth: publication refuses it, and doctor still reports
		one that reached the table another way."""
		config_path, _ = rooted
		with b6.open_instance(config_path) as store:
			store.send("acme.reviewer", "acme.implementer", kind="ev",
			           attach="src:EVIDENCE.md")
		_raw_corrupt(config_path, lambda conn: conn.execute(
			"UPDATE parts SET owner_kind='notice' WHERE storage='external'"))
		report = b6.doctor(config_path)
		assert report["ok"] is False
		assert any("damage lifecycle" in p for p in report["problems"])

	def test_attach_sugar_validates_explicit_metadata(self, rooted):
		"""R4 reappeared in the attachment-only `send` sugar: `content_type or
		DEFAULT` cannot tell absent from empty, so an explicit "" was silently
		defaulted instead of reaching its validator."""
		config_path, _ = rooted
		with b6.open_instance(config_path) as store:
			with pytest.raises(b6.BatonError):
				store.send("acme.reviewer", "acme.implementer", kind="ev",
				           attach="src:EVIDENCE.md", content_type="")
			with pytest.raises(b6.BatonError):
				store.send("acme.reviewer", "acme.implementer", kind="ev",
				           attach="src:EVIDENCE.md", disposition="")
			# Absent still defaults.
			mid = store.send("acme.reviewer", "acme.implementer", kind="ev",
			                 attach="src:EVIDENCE.md")
			claim = store.claim("acme.implementer", message_id=mid)
			part = external_part(b6._delivery(store, claim)["message"]["content"])
			assert part["content_type"] == b6.DEFAULT_ATTACHMENT_TYPE
			assert part["disposition"] == b6.DISPOSITION_ATTACHMENT

	def test_cli_sends_body_and_attachment_together(self, rooted):
		config_path, _ = rooted
		import io, contextlib
		out = io.StringIO()
		old_stdin = sys.stdin if False else None
		with contextlib.redirect_stdout(out):
			code = b6.main(["--config", config_path, "send",
			                "--participant", "acme.reviewer", "--to", "acme.implementer",
			                "--kind", "ev", "--body", str(_write_tmp_body(config_path)),
			                "--attach", "src:EVIDENCE.md"])
		assert code == 0
		out2 = io.StringIO()
		with contextlib.redirect_stdout(out2):
			assert b6.main(["--config", config_path, "claim",
			                "--participant", "acme.implementer"]) == 0
		parts = json.loads(out2.getvalue())["message"]["content"]["parts"]
		assert [p["storage"] for p in parts] == ["inline", "external"]
		assert parts[0]["text"] == "explanation\n"
		assert parts[1]["attachment"]["path"] == "EVIDENCE.md"


def _write_tmp_body(config_path):
	path = os.path.join(os.path.dirname(config_path), "note.md")
	with open(path, "wb") as handle:
		handle.write(b"explanation\n")
	return path


class TestSubject:
	"""A structured, immutable, one-line subject — what an inbox lists before
	anything is opened. Optional at the protocol level so status traffic can
	fall back to `kind`, but lossless and validated when supplied."""

	def test_subject_is_carried_losslessly_to_delivery(self, store):
		mid = send_one(store, subject="Review the protocol-9 handoff")
		claim = store.claim("acme.implementer", message_id=mid)
		envelope = b6._delivery(store, claim)["message"]
		assert envelope["subject"] == "Review the protocol-9 handoff"
		assert store.get_message(mid)["subject"] == "Review the protocol-9 handoff"

	def test_subject_is_optional_and_absent_stays_null(self, store):
		"""Status traffic falls back to `kind`; an absent subject must not
		become an empty string or a synthesized one."""
		mid = send_one(store)
		claim = store.claim("acme.implementer", message_id=mid)
		assert b6._delivery(store, claim)["message"]["subject"] is None

	def test_subject_appears_in_scan_for_inbox_listing(self, store):
		"""An inbox lists without opening anything, so the subject has to be
		in the listing view, not only in the delivery."""
		send_one(store, subject="Needs your decision")
		entry = store.scan("acme.implementer")["pending"][0]
		assert entry["subject"] == "Needs your decision"

	def test_notice_carries_a_subject_too(self, store):
		nid = store.send_notice("hq.lead", kind="announcement",
		                        subject="Channel maintenance at 14:00", body=b"details")
		seen = store.see("acme.implementer")
		assert seen[0]["id"] == nid
		assert b6._notice_delivery(seen[0])["notice"]["subject"] == "Channel maintenance at 14:00"

	def test_reply_inherits_the_subject_it_answers(self, store):
		"""So a thread reads as one conversation in an inbox rather than as
		unrelated lines."""
		send_one(store, subject="Protocol 9 review")
		claim = store.claim("acme.implementer")
		result = store.reply(claim["claim_id"], participant=claim["participant"],
		                     kind="answer", body=b"done")
		assert store.get_message(result["response_message_id"])["subject"] == "Protocol 9 review"

	def test_reply_may_override_the_subject(self, store):
		send_one(store, subject="Protocol 9 review")
		claim = store.claim("acme.implementer")
		result = store.reply(claim["claim_id"], participant=claim["participant"],
		                     kind="answer", subject="Blocker found", body=b"done")
		assert store.get_message(result["response_message_id"])["subject"] == "Blocker found"

	def test_retry_compares_the_effective_subject(self, store):
		"""Inherited on both sides must match; an explicit change is a
		different operation and fails closed."""
		send_one(store, subject="Protocol 9 review")
		claim = store.claim("acme.implementer")
		store.reply(claim["claim_id"], participant=claim["participant"],
		            kind="answer", body=b"done")
		# Inherited retry still matches the inherited commit.
		assert store.reply(claim["claim_id"], participant=claim["participant"],
		                   kind="answer", body=b"done")["already_committed"] is True
		# Explicitly restating the inherited value also matches.
		assert store.reply(claim["claim_id"], participant=claim["participant"],
		                   kind="answer", subject="Protocol 9 review",
		                   body=b"done")["already_committed"] is True
		with pytest.raises(b6.BatonError, match="subject differs"):
			store.reply(claim["claim_id"], participant=claim["participant"],
			            kind="answer", subject="Something else", body=b"done")

	@pytest.mark.parametrize("bad", [
		"", "   ", " leading", "trailing ", "two\nlines", "tab\there",
		"bell\x07", "\x7f", "x" * 256, "é" * 200])
	def test_invalid_subjects_are_rejected_not_sanitized(self, store, bad):
		"""Rejected rather than stripped: a newline or control character in a
		subject is a display-injection hazard for every consumer that lists an
		inbox, and quietly fixing it leaves the sender believing they sent
		something they did not."""
		with pytest.raises(b6.BatonError):
			send_one(store, subject=bad)

	def test_subject_bound_is_bytes_not_characters(self, store):
		"""Same lesson as `part_name`: a character count is not what any
		downstream store enforces."""
		assert b6.validate_subject("a" * 255) == "a" * 255
		with pytest.raises(b6.BatonError, match="255 bytes"):
			b6.validate_subject("a" * 256)
		with pytest.raises(b6.BatonError, match="255 bytes"):
			b6.validate_subject("é" * 200)      # 400 bytes as UTF-8
		assert b6.validate_subject("é" * 127)    # 254 bytes, fits

	def test_subject_is_immutable(self, store):
		mid = send_one(store, subject="Original")
		with pytest.raises(sqlite3.IntegrityError, match="immutable message column"):
			store.conn.execute("UPDATE messages SET subject='Rewritten' WHERE id=?", (mid,))

	def test_cli_send_and_reply_carry_a_subject(self, instance, tmp_path):
		import io, contextlib
		body = tmp_path / "b.md"
		body.write_bytes(b"hello\n")

		def run(*argv):
			out = io.StringIO()
			with contextlib.redirect_stdout(out):
				code = b6.main(list(argv))
			return code, out.getvalue()

		code, _ = run("--config", instance, "send", "--participant", "acme.reviewer",
		              "--to", "acme.implementer", "--kind", "q",
		              "--subject", "Please review", "--body", str(body))
		assert code == 0
		code, out = run("--config", instance, "claim", "--participant", "acme.implementer")
		delivery = json.loads(out)
		assert delivery["message"]["subject"] == "Please review"
		code, out = run("--config", instance, "reply", delivery["claim"]["claim_id"],
		                "--participant", "acme.implementer", "--kind", "a",
		                "--body", str(body))
		assert code == 0
		code, out = run("--config", instance, "claim", "--participant", "acme.reviewer")
		assert json.loads(out)["message"]["subject"] == "Please review"   # inherited


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
		# SUPERSEDED SOURCE: the CLI is built from `baton_core` now, so
		# `source_sha256` pins the core's implementation rather than the
		# frozen oracle. `baton_v6.py` stays in the tree as the differential
		# oracle and is deliberately NOT what the manifest describes.
		here_src = open(os.path.join(os.path.dirname(__file__),
		                             "baton_core", "_impl.py"), "rb").read()
		assert committed["source_sha256"] == _h.sha256(here_src).hexdigest(), \
			"committed manifest is stale against baton_core/_impl.py — rerun build_zipapp.py"
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
		# The bootstrap imports the CORE now. What this test is about is
		# unchanged and is the whole reason it exists: the floor check must
		# come BEFORE the import, or an old interpreter dies on the import
		# instead of printing the diagnostic the exit code promises.
		import_idx = next(i for i, l in enumerate(lines) if "from baton_core" in l)
		assert floor_idx < import_idx

	def test_zipapp_imports_own_module_under_poisoned_cwd(self, tmp_path):
		import subprocess, sys as _sys
		builder = self._builder()
		root = tmp_path / "dist"
		builder.build(str(root))
		poison = tmp_path / "poison"
		poison.mkdir()
		# POISON WHAT THE ARTIFACT ACTUALLY IMPORTS. Both of these wrote a
		# hostile `baton_v6.py` until protocol 10 retired that name -- after
		# which nothing imported it and the test passed however the zipapp
		# behaved. A PACKAGE shape, because `baton_core` is a package and a
		# bare module of that name would not shadow it the same way.
		hostile = poison / "baton_core"
		hostile.mkdir()
		for name in ("__init__.py", "_impl.py", "cli.py"):
			(hostile / name).write_text("raise RuntimeError('poisoned import')\n")
		proc = subprocess.run([_sys.executable, str(root / "bin" / "baton"), "--version"],
		                      capture_output=True, text=True, cwd=str(poison),
		                      env={"PATH": os.environ["PATH"], "PYTHONPATH": str(poison)})
		assert proc.returncode == 0, proc.stderr
		assert "poisoned" not in proc.stderr

	REUSABLE_ASSETS = ["test_core_conformance.py", "build_zipapp.py",
	                   "example-baton.json", "config-schema.json", "README.md",
	                   "baton", "DISTRIBUTION.json", "AGENTS-MAILBOX-PROTO.md"]
	# The CLI is built from the core, so the core is a reusable asset too: a
	# bare checkout that cannot build the executable is not a reusable
	# checkout. `baton_v6.py` is NO LONGER in the list: protocol 10 retired
	# it, nothing imports it, and shipping a retired implementation inside a
	# reusable checkout invites someone to build against it.
	REUSABLE_PACKAGES = ["baton_core"]

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
		for package in self.REUSABLE_PACKAGES:
			shutil.copytree(os.path.join(here, package), iso / package)
		(iso / "bin").mkdir()
		shutil.copy(os.path.join(here, "bin", "baton"), iso / "bin" / "baton")
		env = {"PATH": os.environ["PATH"], "PYTHONPATH": str(iso),
		       "BATON_ISOLATED": "1", "HOME": str(tmp_path)}
		proc = subprocess.run(
			[_sys.executable, "-m", "pytest", "test_core_conformance.py", "-q", "-x",
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
		# POISON WHAT THE ARTIFACT ACTUALLY IMPORTS. Both of these wrote a
		# hostile `baton_v6.py` until protocol 10 retired that name -- after
		# which nothing imported it and the test passed however the zipapp
		# behaved. A PACKAGE shape, because `baton_core` is a package and a
		# bare module of that name would not shadow it the same way.
		hostile = poison / "baton_core"
		hostile.mkdir()
		for name in ("__init__.py", "_impl.py", "cli.py"):
			(hostile / name).write_text("raise RuntimeError('poisoned import')\n")
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
		assert delivered_bytes(delivery["message"]["content"]) == b"distribution body"
		proc = run("reply", delivery["claim"]["claim_id"], "--participant",
		           "team.implementer",
		           "--kind", "a", stdin=b"distribution answer")
		assert proc.returncode == 0, proc.stderr
		assert json.loads(proc.stdout)["already_committed"] is False
		proc = run("doctor")
		assert proc.returncode == 0, proc.stderr
		assert json.loads(proc.stdout)["ok"] is True

	def test_packaged_cli_authors_a_multipart_message_in_option_order(self, tmp_path):
		"""The four authoring verbs, driven through the PACKED executable.

		In-process parser tests cannot see this: the options live in the core
		package, and whether they reached the shipped archive is a packaging
		question. A console that cannot start still passes every unit test it
		has, which is a lesson this suite has already learned once.

		Order is the property under test. `--part a --attach b --part c` must
		arrive as three leaves in that order, because leaf order is part of the
		manifest digest and the manifest is what retry compares."""
		import shutil, subprocess, sys as _sys
		root = tmp_path / "dist"
		self._builder().build(str(root))
		inst = tmp_path / "inst"
		inst.mkdir()
		files = tmp_path / "files"
		files.mkdir()
		(files / "one.md").write_text("first leaf\n")
		(files / "two.txt").write_text("third leaf\n")
		(files / "refs.txt").write_text("src:baton_core/_impl.py\nsrc:README.md\n")
		config = json.loads(
			open(os.path.join(os.path.dirname(__file__), "example-baton.json")).read())
		config["roots"] = {"src": str(files)}
		config_path = str(inst / "baton.json")
		open(config_path, "w").write(json.dumps(config))
		env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}

		def run(*args, stdin=b""):
			return subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config", config_path,
				 *args], input=stdin, capture_output=True, cwd=str(tmp_path),
				env=env, timeout=60)

		assert run("init").returncode == 0
		proc = run("send", "--participant", "team.reviewer",
		           "--to", "team.implementer", "--kind", "q", "--subject", "S",
		           "--part", f"source={files / 'one.md'}&type=text/markdown;%20charset=utf-8",
		           "--attach", "src:two.txt",
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		proc = run("claim", "--participant", "team.implementer")
		assert proc.returncode == 0, proc.stderr
		delivery = json.loads(proc.stdout)
		leaves = delivery["message"]["content"]["parts"]
		assert [leaf["content_type"] for leaf in leaves] == [
			"text/markdown; charset=utf-8",
			"application/octet-stream",
			"text/vnd.baton.references; charset=utf-8"]
		assert leaves[0]["text"] == "first leaf\n"
		assert leaves[1]["storage"] == "external"
		assert leaves[2]["text"] == "src:baton_core/_impl.py\nsrc:README.md\n"

		# reply and close carry the same surface, or the four verbs are not
		# symmetric and the human has to remember which is which.
		claim_id = delivery["claim"]["claim_id"]
		proc = run("reply", claim_id, "--participant", "team.implementer",
		           "--kind", "a",
		           "--part", f"source={files / 'one.md'}&type=text/plain;%20charset=utf-8"
		                     "&disposition=attachment&name=Answer.txt")
		assert proc.returncode == 0, proc.stderr
		proc = run("claim", "--participant", "team.reviewer")
		assert proc.returncode == 0, proc.stderr
		answer = json.loads(proc.stdout)
		leaf = answer["message"]["content"]["parts"][0]
		assert leaf["content_type"] == "text/plain; charset=utf-8"
		# The surface says `name` and protocol 10 stores `part_name`. The
		# translation happens inward, so the CLI never teaches a word it is
		# about to retire.
		assert leaf["part_name"] == "Answer.txt"
		close_claim_id = answer["claim"]["claim_id"]
		proc = run("close", close_claim_id, "--participant",
		           "team.reviewer", "--outcome", "done",
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		# A close disposition is a terminal audit record and is never
		# delivered, so exit status is ALL a caller sees -- and a close whose
		# content was silently dropped exits zero just as happily as one that
		# carried it. Asserting the status alone pins nothing, which an earlier
		# version of this test did: removing `close`'s wiring left it green.
		# `dump` is the observable route to what the close actually stored.
		proc = run("dump")
		assert proc.returncode == 0, proc.stderr
		dumped = json.loads(proc.stdout)
		closed = [d for d in dumped["dispositions"]
		          if d["claim_id"] == close_claim_id]
		assert len(closed) == 1, "the close disposition must be recorded"
		assert closed[0]["manifest_sha256"] is not None, \
			"a close carrying parts must have a manifest"
		owned = [part for part in dumped["parts"]
		         if part["owner_kind"] == "disposition"
		         and part["owner_id"] == close_claim_id]
		assert [part["content_type"] for part in owned] == \
			["text/vnd.baton.references; charset=utf-8"]

		proc = run("send-notice", "--participant", "team.reviewer", "--kind", "fyi",
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		proc = run("see", "--participant", "team.implementer")
		assert proc.returncode == 0, proc.stderr
		notices = json.loads(proc.stdout)["notices"]
		assert len(notices) == 1
		assert notices[0]["content"]["parts"][0]["content_type"] == \
			"text/vnd.baton.references; charset=utf-8"

	def test_packaged_cli_names_which_part_was_wrong(self, tmp_path):
		"""With a repeatable option, "unknown field" on a command carrying four
		of them tells the human almost nothing.

		The descriptor may hold a path or a media type from anywhere, so the
		VALUE is never echoed back to the terminal — which leaves the
		occurrence count as the only thing that can distinguish them, and makes
		it load-bearing rather than decorative."""
		import subprocess, sys as _sys
		root = tmp_path / "dist"
		self._builder().build(str(root))
		inst = tmp_path / "inst"
		inst.mkdir()
		config_path = str(inst / "baton.json")
		import shutil
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"),
		            config_path)
		env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}

		def run(*args):
			return subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config", config_path,
				 *args], capture_output=True, text=True, cwd=str(tmp_path),
				env=env, timeout=60)

		assert run("init").returncode == 0
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--part", "source=a.md&type=text/markdown",
		           "--part", "source=b.md&type=text/plain",
		           "--part", "source=c.md&type=text/plain&nope=1")
		assert proc.returncode != 0
		assert "--part #3" in proc.stderr, proc.stderr
		assert "nope" in proc.stderr
		assert "c.md" not in proc.stderr, "the descriptor value must not be echoed"

	def _authoring_instance(self, tmp_path):
		"""A built distribution, a config with one root, and a runner."""
		import shutil, subprocess, sys as _sys
		root = tmp_path / "dist"
		self._builder().build(str(root))
		inst = tmp_path / "inst"
		inst.mkdir()
		files = tmp_path / "files"
		files.mkdir()
		(files / "body.md").write_text("BODY MUST SURVIVE\n")
		(files / "one.md").write_text("first leaf\n")
		(files / "refs.txt").write_text("src:baton_core/_impl.py\n")
		config = json.loads(
			open(os.path.join(os.path.dirname(__file__), "example-baton.json")).read())
		config["roots"] = {"src": str(files)}
		config_path = str(inst / "baton.json")
		open(config_path, "w").write(json.dumps(config))
		env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}

		def run(*args, stdin=b""):
			return subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config", config_path,
				 *args], input=stdin, capture_output=True, cwd=str(tmp_path),
				env=env, timeout=60)

		assert run("init").returncode == 0
		return run, files

	def test_packaged_cli_never_silently_drops_an_authored_body(self, tmp_path):
		"""THE REGRESSION, pinned where it actually happened.

		`send --body body.md --references refs.txt` returned success and
		published only the references leaf. In-process tests did not see it and
		would not have: the drop was in the verb dispatch, not the builder.

		A command that succeeds while discarding content the caller named is
		worse than one that fails, so this is pinned per verb rather than once.
		"""
		run, files = self._authoring_instance(tmp_path)
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--body", str(files / "body.md"),
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		proc = run("claim", "--participant", "team.implementer")
		assert proc.returncode == 0, proc.stderr
		delivery = json.loads(proc.stdout)
		leaves = delivery["message"]["content"]["parts"]
		assert leaves[0]["text"] == "BODY MUST SURVIVE\n", \
			"the authored body must survive beside a references leaf"
		assert leaves[1]["content_type"] == "text/vnd.baton.references; charset=utf-8"

		# reply and close carry the same risk and the same fix.
		claim_id = delivery["claim"]["claim_id"]
		proc = run("reply", claim_id, "--participant", "team.implementer",
		           "--kind", "a", "--body", str(files / "body.md"),
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		proc = run("claim", "--participant", "team.reviewer")
		answer = json.loads(proc.stdout)
		assert answer["message"]["content"]["parts"][0]["text"] == "BODY MUST SURVIVE\n"
		proc = run("close", answer["claim"]["claim_id"], "--participant",
		           "team.reviewer", "--outcome", "done",
		           "--body", str(files / "body.md"),
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		dumped = json.loads(run("dump").stdout)
		owned = [part for part in dumped["parts"]
		         if part["owner_kind"] == "disposition"
		         and part["owner_id"] == answer["claim"]["claim_id"]]
		assert len(owned) == 2, "the close body must survive beside its references"

		proc = run("send-notice", "--participant", "team.reviewer", "--kind", "fyi",
		           "--body", str(files / "body.md"),
		           "--references", str(files / "refs.txt"))
		assert proc.returncode == 0, proc.stderr
		notices = json.loads(run("see", "--participant", "team.implementer").stdout)
		assert notices["notices"][0]["content"]["parts"][0]["text"] == \
			"BODY MUST SURVIVE\n"

	def test_packaged_cli_refuses_a_body_beside_a_general_part(self, tmp_path):
		"""The combination has no obviously right reading -- a `--part` carries
		its own type, name and position, `--body` carries a type and no
		position -- so it is refused rather than resolved by guessing. Refused
		BEFORE reading, so the diagnostic is about a message that still could
		have existed."""
		run, files = self._authoring_instance(tmp_path)
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--body", str(files / "body.md"),
		           "--part", f"source={files / 'one.md'}&type=text/plain;%20charset=utf-8")
		assert proc.returncode != 0
		assert "--body cannot be combined with --part" in proc.stderr.decode()

	def test_packaged_cli_refuses_body_metadata_with_no_body(self, tmp_path):
		"""`--content-type` describes `--body`. With parts and no body it
		describes nothing, and silently ignoring it would tell the caller their
		declaration was honoured."""
		run, files = self._authoring_instance(tmp_path)
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--content-type", "text/plain; charset=utf-8",
		           "--references", str(files / "refs.txt"))
		assert proc.returncode != 0
		assert "--content-type" in proc.stderr.decode()

	def test_packaged_close_does_not_offer_an_external_attachment(self, tmp_path):
		"""External storage is refused on a disposition -- a close is a
		terminal audit record with no delivery, so nothing could ever notice or
		resolve a stale pin. An option whose every use is refused is a worse
		surface than no option."""
		run, _files = self._authoring_instance(tmp_path)
		proc = run("close", "--help")
		assert proc.returncode == 0
		assert "--attach" not in proc.stdout.decode()
		assert "--part" in proc.stdout.decode(), \
			"inline attachment-disposition parts remain available"
		proc = run("send-notice", "--help")
		assert "--attach" not in proc.stdout.decode()
		for verb in ("send", "reply"):
			assert "--attach" in run(verb, "--help").stdout.decode()

	def test_packaged_cli_diagnoses_an_unreadable_references_file(self, tmp_path):
		"""A bare `.decode("utf-8")` raises `UnicodeDecodeError`, which `main`
		does not catch -- so a mis-encoded references file printed a traceback
		instead of a diagnostic. The bytes are not echoed back: they are by
		definition not valid UTF-8."""
		run, files = self._authoring_instance(tmp_path)
		bad = files / "bad-refs.txt"
		bad.write_bytes(b"src:caf\xe9/notes.md\n")

		def refused(proc):
			assert proc.returncode != 0, proc.stdout
			stderr = proc.stderr.decode()
			assert "Traceback" not in stderr, "an encoding error must not be a crash"
			assert "not valid UTF-8" in stderr

		for verb, extra in (("send", ["--to", "team.implementer", "--kind", "q"]),
		                    ("send-notice", ["--kind", "fyi"])):
			refused(run(verb, "--participant", "team.reviewer", *extra,
			            "--references", str(bad)))

		# ALL FOUR. `reply` and `close` need a real held claim to reach the
		# authoring path at all, which is why they were missing -- and being
		# harder to set up is not a reason for the two verbs that write a
		# TERMINAL record to be the untested ones.
		assert run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", stdin=b"?\n").returncode == 0
		claim = json.loads(run("claim", "--participant", "team.implementer").stdout)
		claim_id = claim["claim"]["claim_id"]
		refused(run("reply", claim_id, "--participant", "team.implementer",
		            "--kind", "a", "--references", str(bad)))
		refused(run("close", claim_id, "--participant", "team.implementer",
		            "--outcome", "done", "--references", str(bad)))

		# And nothing was committed by either refusal: the claim is still
		# active and no disposition exists. A refusal that had already written
		# a terminal record would leave the human unable to retry.
		dumped = json.loads(run("dump").stdout)
		held = [c for c in dumped["claims"] if c["claim_id"] == claim_id]
		assert held and held[0]["state"] == "active", \
			"a refused disposition resolved the claim anyway"
		assert not [d for d in dumped["dispositions"]
		            if d["claim_id"] == claim_id], \
			"a refused close committed a disposition"

	def test_packaged_cli_requires_a_query_shaped_descriptor(self, tmp_path):
		"""A descriptor is an RFC 3986 query. Raw spaces and raw non-ASCII are
		refused, because the same command would otherwise mean different things
		depending on the shell, locale and terminal encoding it passed
		through."""
		run, files = self._authoring_instance(tmp_path)
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--part", f"source={files / 'one.md'}&type=text/plain; charset=utf-8")
		assert proc.returncode != 0
		assert "RFC 3986 query" in proc.stderr.decode()
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--part", f"source={files / 'one.md'}&type=text/plain;%20charset=utf-8")
		assert proc.returncode == 0, proc.stderr

	def test_packaged_send_notice_and_reply_still_default_to_stdin(self, tmp_path):
		"""`--body` on these two verbs used `default="-"`. That default moved
		into the dispatch so the namespace could still distinguish "no body
		supplied" from "body read from stdin" -- which part mode needs and the
		argparse default was erasing.

		Moving a default is exactly the kind of change that looks inert and is
		not, so the behaviour it used to provide is pinned here rather than
		assumed."""
		run, _files = self._authoring_instance(tmp_path)
		proc = run("send-notice", "--participant", "team.reviewer", "--kind", "fyi",
		           stdin=b"NOTICE FROM STDIN\n")
		assert proc.returncode == 0, proc.stderr
		notices = json.loads(run("see", "--participant", "team.implementer").stdout)
		assert notices["notices"][0]["content"]["parts"][0]["text"] == \
			"NOTICE FROM STDIN\n"

		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", stdin=b"Q\n")
		assert proc.returncode == 0, proc.stderr
		claim = json.loads(run("claim", "--participant", "team.implementer").stdout)
		proc = run("reply", claim["claim"]["claim_id"], "--participant",
		           "team.implementer", "--kind", "a", stdin=b"REPLY FROM STDIN\n")
		assert proc.returncode == 0, proc.stderr
		answer = json.loads(run("claim", "--participant", "team.reviewer").stdout)
		assert answer["message"]["content"]["parts"][0]["text"] == \
			"REPLY FROM STDIN\n"

	def test_packaged_omitted_body_does_not_consume_stdin_in_part_mode(self, tmp_path):
		"""Ruled clause: when an explicit content source is supplied, an
		omitted `--body` does NOT implicitly consume standard input.

		Two verbs used to default `--body` to `-`, so without this the mere
		presence of `--references` would have silently swallowed whatever was
		on stdin and published it as a leaf nobody asked for. Stdin here holds
		bytes that must not appear anywhere in the message."""
		run, files = self._authoring_instance(tmp_path)
		intruder = b"THIS MUST NOT BE PUBLISHED\n"
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q",
		           "--references", str(files / "refs.txt"), stdin=intruder)
		assert proc.returncode == 0, proc.stderr
		delivery = json.loads(run("claim", "--participant", "team.implementer").stdout)
		leaves = delivery["message"]["content"]["parts"]
		assert len(leaves) == 1, "only the references leaf was asked for"
		assert leaves[0]["content_type"] == "text/vnd.baton.references; charset=utf-8"
		assert b"MUST NOT BE PUBLISHED" not in json.dumps(delivery).encode()

		for verb, extra in (("send-notice", ["--kind", "fyi"]),):
			proc = run(verb, "--participant", "team.reviewer", *extra,
			           "--references", str(files / "refs.txt"), stdin=intruder)
			assert proc.returncode == 0, proc.stderr
			seen = json.loads(run("see", "--participant", "team.implementer").stdout)
			assert len(seen["notices"][0]["content"]["parts"]) == 1
			assert b"MUST NOT BE PUBLISHED" not in json.dumps(seen).encode()

	def test_packaged_reply_never_silently_drops_an_attachment(self, tmp_path):
		"""R9, and the same class as R1: success while discarding a source the
		caller named.

		`--attach` was exposed on `reply`, but `reply` has no store-level
		`attach=` parameter the way `send` does. A lone `--attach` therefore
		fell back to a legacy route that did not exist on this verb, and the
		response was published without it. Whether a verb HAS a legacy route is
		the distinction, and it is now stated by the caller rather than guessed
		at."""
		run, files = self._authoring_instance(tmp_path)
		(files / "evidence.txt").write_text("EVIDENCE\n")
		assert run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", stdin=b"?\n").returncode == 0
		claim = json.loads(run("claim", "--participant", "team.implementer").stdout)

		# Attachment ONLY -- and stdin holds bytes that must not be published,
		# because an omitted body must not be invented from it.
		proc = run("reply", claim["claim"]["claim_id"], "--participant",
		           "team.implementer", "--kind", "a", "--attach", "src:evidence.txt",
		           stdin=b"STDIN MUST NOT APPEAR\n")
		assert proc.returncode == 0, proc.stderr
		answer = json.loads(run("claim", "--participant", "team.reviewer").stdout)
		leaves = answer["message"]["content"]["parts"]
		assert len(leaves) == 1, "an attachment-only reply invented a body leaf"
		assert leaves[0]["storage"] == "external"
		assert b"STDIN MUST NOT APPEAR" not in json.dumps(answer).encode()
		run("close", answer["claim"]["claim_id"], "--participant", "team.reviewer",
		    "--outcome", "done")

		# Body FIRST, attachment second.
		assert run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", stdin=b"?\n").returncode == 0
		claim = json.loads(run("claim", "--participant", "team.implementer").stdout)
		proc = run("reply", claim["claim"]["claim_id"], "--participant",
		           "team.implementer", "--kind", "a",
		           "--body", str(files / "body.md"), "--attach", "src:evidence.txt")
		assert proc.returncode == 0, proc.stderr
		answer = json.loads(run("claim", "--participant", "team.reviewer").stdout)
		leaves = answer["message"]["content"]["parts"]
		assert leaves[0]["text"] == "BODY MUST SURVIVE\n"
		assert leaves[1]["storage"] == "external"

	def test_packaged_reply_attachment_retry_keeps_the_manifest_contract(self, tmp_path):
		"""An attachment that reaches the parts plan is an ordinary part, so it
		is covered by retry identity like any other. Pinned because the fix
		changed WHICH path builds it, and a part built by a different path
		that no longer retried the same would be a quieter kind of wrong."""
		run, files = self._authoring_instance(tmp_path)
		(files / "evidence.txt").write_text("EVIDENCE\n")
		assert run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", stdin=b"?\n").returncode == 0
		claim = json.loads(run("claim", "--participant", "team.implementer").stdout)
		claim_id = claim["claim"]["claim_id"]
		first = run("reply", claim_id, "--participant", "team.implementer",
		            "--kind", "a", "--attach", "src:evidence.txt")
		assert first.returncode == 0, first.stderr
		assert json.loads(first.stdout)["already_committed"] is False

		# EXACT retry: effectively-once.
		again = run("reply", claim_id, "--participant", "team.implementer",
		            "--kind", "a", "--attach", "src:evidence.txt")
		assert again.returncode == 0, again.stderr
		assert json.loads(again.stdout)["already_committed"] is True

		# Changed attachment identity: fails closed rather than committing a
		# second, different response under the same claim.
		(files / "evidence.txt").write_text("EVIDENCE CHANGED\n")
		changed = run("reply", claim_id, "--participant", "team.implementer",
		              "--kind", "a", "--attach", "src:evidence.txt")
		assert changed.returncode != 0, changed.stdout

	def test_packaged_references_are_checked_against_configured_roots(self, tmp_path):
		"""The root is validated against THE AUTHORITY, not against a list this
		process made up. That is the whole reason the root is required: one
		instance may coordinate several repositories, and an address naming a
		root the participants do not share resolves for nobody."""
		run, files = self._authoring_instance(tmp_path)
		unknown = files / "unknown-root.txt"
		unknown.write_text("nosuchroot:a.md\n")
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", "--references", str(unknown))
		assert proc.returncode != 0
		stderr = proc.stderr.decode()
		assert "no root 'nosuchroot' is configured" in stderr
		assert "src" in stderr, "the diagnostic should name the roots that DO exist"

		bare = files / "bare.txt"
		bare.write_text("a.md\n")
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", "--references", str(bare))
		assert proc.returncode != 0
		assert "ROOT_ID:RELATIVE/PATH" in proc.stderr.decode()

		# And the configured root travels. The path deliberately does NOT
		# exist: a reference is navigational metadata, so nothing reads it.
		ghost = files / "ghost.txt"
		ghost.write_text("src:does/not/exist/anywhere.md\n")
		proc = run("send", "--participant", "team.reviewer", "--to",
		           "team.implementer", "--kind", "q", "--references", str(ghost))
		assert proc.returncode == 0, proc.stderr
		delivery = json.loads(run("claim", "--participant", "team.implementer").stdout)
		assert delivery["message"]["content"]["parts"][0]["text"] == \
			"src:does/not/exist/anywhere.md\n"

	def test_packaged_help_teaches_the_ruled_reference_address(self, tmp_path):
		"""All four verbs, on the PACKED executable.

		The help said "repository-relative POSIX paths" after the ruling made
		references root-qualified -- so `--help` was instructing a fresh user
		to produce exactly the input the parser now refuses. Documentation
		that contradicts the validator is worse than none: it costs the user
		the time to follow it before failing.

		Asserted on the RENDERED help of every verb rather than on the shared
		source, because whether all four reach that source is the thing that
		can regress."""
		import subprocess, sys as _sys
		root = tmp_path / "dist"
		self._builder().build(str(root))
		inst = tmp_path / "inst"
		inst.mkdir()
		import shutil
		config_path = str(inst / "baton.json")
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"),
		            config_path)
		env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}
		for verb in ("send", "send-notice", "reply", "close"):
			proc = subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config",
				 config_path, verb, "--help"], capture_output=True, text=True,
				cwd=str(tmp_path), env=env, timeout=60)
			assert proc.returncode == 0, proc.stderr
			text = " ".join(proc.stdout.split())
			assert "ROOT_ID:RELATIVE/POSIX/PATH" in text, f"{verb}: {text}"
			assert "repository-relative POSIX paths" not in text, \
				f"{verb} still teaches the superseded bare-path form"

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
		assets = self.REUSABLE_ASSETS + [os.path.join("bin", "baton")]
		# Every packaged core module too. It ships inside the executable now,
		# so a host needle in it travels exactly as far as one in the old
		# single source file did.
		for package in self.REUSABLE_PACKAGES:
			for name in sorted(os.listdir(os.path.join(here, package))):
				if name.endswith(".py"):
					assets.append(os.path.join(package, name))
		for asset in assets:
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


class TestScanInboxMetadata:
	"""An inbox lists before it opens anything, on both sides of a claim."""

	def test_scan_carries_inbox_metadata_on_pending_and_claimed(self, store):
		"""Post-gate cleanup requested by baton.reviewer. Showing a subject
		only until someone claims a message hides it exactly when the holder
		most needs to know what they are holding."""
		mid = send_one(store, subject="Decide on the rollout", kind="question",
		               thread="topic-1")
		pending = store.scan("acme.implementer")["pending"][0]
		assert pending["subject"] == "Decide on the rollout"
		assert pending["kind"] == "question" and pending["thread_id"] == "topic-1"
		store.claim("acme.implementer", message_id=mid)
		claimed = store.scan("acme.implementer")["claimed"][0]
		assert claimed["subject"] == "Decide on the rollout"
		assert claimed["kind"] == "question" and claimed["thread_id"] == "topic-1"
		assert claimed["claimed_by"] == "acme.implementer"
		# Same metadata keys on both sides, so one renderer serves both.
		for key in ("kind", "subject", "thread_id"):
			assert key in pending and key in claimed


class TestPartNameIsNotAFilename:
	"""Protocol 10 renamed the field, and the rename has to STAY renamed.

	The finding's whole argument is that a part is not a file: the sender names
	a part, and the recipient decides whether it is ever written anywhere. Two
	things must therefore hold, and the second is the one a tidy-up would
	break."""

	def test_no_protocol_surface_says_filename(self, instance):
		"""Swept across the live surface — schema, delivery, dump — rather
		than read off the diff. Protocol 10 contains `part_name` only; there
		is no compatibility alias to find."""
		with b6.open_instance(instance) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 parts=[{"content_type": "text/plain; charset=utf-8",
			                         "body": b"x\n", "part_name": "notes.txt"}])
			claim = store.claim("acme.implementer")
			delivery = b6._delivery(store, claim)
			schema = "\n".join(
				row[0] or "" for row in store.conn.execute(
					"SELECT sql FROM sqlite_master"))
		dumped = json.dumps(b6.dump(instance))
		assert "filename" not in schema, "the schema still has a filename column"
		assert "filename" not in json.dumps(delivery), \
			"a delivery still carries filename"
		assert "filename" not in dumped, "dump still emits filename"

		# SIGNATURES too. The name claimed "no protocol surface" while checking
		# three; a Store keyword still spelled `filename` would be a public
		# break that schema, delivery and dump all miss.
		import inspect
		for method in (b6.Store.send, b6.Store.send_notice, b6.Store.reply,
		               b6.Store.close_claim, b6.content_spec,
		               b6.normalize_parts, b6.validate_part_name):
			text = str(inspect.signature(method))
			assert "filename" not in text, f"{method.__name__}{text}"
		leaf = delivery["message"]["content"]["parts"][0]
		assert leaf["part_name"] == "notes.txt"

	# The other half of this property -- that the CONSOLE still has a real
	# `filename()` for real files -- is pinned in `test_tui_drafts.py`.
	# It cannot live here: the core is independent of the console, and the
	# isolated-checkout test proves that by running this corpus without
	# `baton_tui` present at all.

	def test_a_part_name_is_an_uninterpreted_label(self, instance):
		"""Protocol 10 dropped the filesystem rules, not just the word.

		`validate_filename` refused `/`, `\\`, `.`, `..` and a leading `-` on
		the theory that a careless consumer might use the label as a path.
		Keeping those rules under the new key would have been the old concept
		wearing the new word -- which is the exact failure the finding exists
		to prevent.

		The label round-trips BYTE FOR BYTE. It is strange, it means nothing to
		Baton, and it reaches the recipient as written."""
		odd = ["../diagram", "a/b.png", ".", "..", "-flag", "C:\\x5cwin.bin"]
		with b6.open_instance(instance) as store:
			for name in odd:
				assert b6.validate_part_name(name) == name
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 parts=[{"content_type": "text/plain; charset=utf-8",
			                         "body": b"x\n", "part_name": name}
			                        for name in odd])
			delivery = b6._delivery(store, store.claim("acme.implementer"))
		assert [leaf["part_name"] for leaf
		        in delivery["message"]["content"]["parts"]] == odd

	@pytest.mark.parametrize("bad", ["", "a\x1b[2Jb", "a\x00b", "x" * 256])
	def test_a_part_name_still_refuses_what_baton_cannot_carry(self, bad):
		"""Each refusal is about BATON, not about a filesystem: an empty label
		is not a name, a control character is a display-injection hazard in
		every inbox that draws it, NUL cannot cross the boundaries this string
		crosses, and the byte bound exists because the label sits in every
		manifest and on one line of a list."""
		with pytest.raises(b6.BatonError):
			b6.validate_part_name(bad)

	def test_materialize_ignores_the_part_name_completely(self, instance, tmp_path):
		"""The other half of "the recipient decides". Now that `../diagram` is
		a legal label, the output path must demonstrably not come from it."""
		with b6.open_instance(instance) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 retention="durable",
			                 parts=[{"content_type": "text/plain; charset=utf-8",
			                         "body": b"x\n", "part_name": "../escaped"}])
			store.claim("acme.implementer")
		target = tmp_path / "out"
		target.mkdir()
		written = b6.materialize(instance, mid, str(target), prefix="review")
		assert os.path.dirname(written) == str(target), "the label chose the directory"
		assert "escaped" not in os.path.basename(written)
		# Nothing anywhere is named after the label -- not in the output
		# directory, not beside the authority, not above either. The instance
		# fixture already owns files here, so this asks the sharper question:
		# did the LABEL create anything?
		escaped = [q for q in tmp_path.rglob("*") if "escaped" in q.name]
		assert escaped == [], escaped


	def test_the_packaged_cli_speaks_only_part_name(self, tmp_path):
		"""The surface a human actually types at, on the BUILT executable.

		Schema and delivery can be clean while `--filename` still works,
		because argparse is a separate surface from the store."""
		import subprocess, sys as _sys, shutil
		root = tmp_path / "dist"
		TestPackaging()._builder().build(str(root))
		inst = tmp_path / "inst"
		inst.mkdir()
		config_path = str(inst / "baton.json")
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"),
		            config_path)
		env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}

		def run(*args, stdin=b""):
			return subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config",
				 config_path, *args], input=stdin, capture_output=True,
				cwd=str(tmp_path), env=env, timeout=60)

		assert run("init").returncode == 0
		for verb in ("send", "send-notice", "reply", "close"):
			help_text = run(verb, "--help").stdout.decode()
			assert "--part-name" in help_text, verb
			assert "--filename" not in help_text, verb

		# The removed option is REFUSED, not quietly ignored.
		refused = run("send", "--participant", "team.reviewer", "--to",
		              "team.implementer", "--kind", "q", "--filename", "x",
		              stdin=b"body\n")
		assert refused.returncode != 0
		assert "--filename" in refused.stderr.decode()

		# And the descriptor still says `name`, which never moved.
		body = tmp_path / "b.md"
		body.write_text("hello\n")
		ok = run("send", "--participant", "team.reviewer", "--to",
		         "team.implementer", "--kind", "q",
		         "--part", f"source={body}&type=text/plain;%20charset=utf-8&name=Q3.txt")
		assert ok.returncode == 0, ok.stderr
		claimed = json.loads(run("claim", "--participant", "team.implementer").stdout)
		leaf = claimed["message"]["content"]["parts"][0]
		assert leaf["part_name"] == "Q3.txt"
		assert "filename" not in json.dumps(claimed)


class TestScopeSelectors:
	"""The pure half of scoped audiences: what a selector means, before any
	notice exists to carry one."""

	def test_the_ruled_example(self):
		assert b6.expand_scope("baton.*", [
			"baton.reviewer", "baton.implementer", "lang.reviewer"]) == \
			["baton.implementer", "baton.reviewer"]

	def test_a_longer_first_segment_is_a_different_segment(self):
		"""The case the ruling names, and the reason matching compares SEGMENTS
		rather than string prefixes: `"baton."` is a prefix of
		`"baton_extra.reviewer"`... no it is not, and that near-miss is exactly
		why a string test would have looked correct while being correct by
		luck. `baton` and `baton_extra` are different segments, full stop."""
		with pytest.raises(b6.BatonError):
			b6.expand_scope("baton.*", ["baton_extra.reviewer", "batonx.lead"])

	def test_a_scope_does_not_match_its_own_prefix_as_an_address(self):
		"""`baton.*` addresses the members of a group, not the group. There
		must be something after the dot."""
		segments = b6.validate_scope("baton.*")
		assert not b6.scope_matches(segments, "baton")

	def test_deeper_addresses_match_and_this_is_a_choice(self):
		"""`baton.*` matches `baton.a.b` as well as `baton.reviewer`.

		The ruling names two-segment examples and does not say what a deeper
		address does, so this is my reading rather than a quoted rule: a scope
		names a DOMAIN, and everything under that domain is in it. The
		alternative — matching exactly one further segment — would make
		`baton.*` silently skip a participant that every human reading it would
		expect to be included, which is the worse failure for an announcement.

		Flagged in the handoff rather than buried here."""
		assert b6.expand_scope("baton.*", ["baton.a.b", "baton.reviewer"]) == \
			["baton.a.b", "baton.reviewer"]

	@pytest.mark.parametrize("selector", [
		"baton", "baton.", "*", ".*", "baton.*.x", "Baton.*", "baton.reviewer",
		"baton..*", "_baton.*", "1baton.*", "baton.*extra", "x" * 70 + ".*"])
	def test_a_malformed_selector_is_refused(self, selector):
		with pytest.raises(b6.BatonError):
			b6.validate_scope(selector)

	def test_a_selector_that_matches_nobody_is_refused(self):
		"""A notice addressed to nobody is a publication that silently does
		nothing, and the likeliest cause is a typo — which is exactly when the
		author most wants to be told."""
		with pytest.raises(b6.BatonError) as caught:
			b6.expand_scope("nosuch.*", ["baton.reviewer"])
		assert "matches no configured participant" in str(caught.value)

	def test_the_expansion_is_sorted(self):
		"""It is STORED and COMPARED. An audience that depended on how the
		config happened to be written would make retry identity depend on it
		too."""
		scrambled = ["baton.zulu", "baton.alpha", "baton.mike"]
		assert b6.expand_scope("baton.*", scrambled) == \
			["baton.alpha", "baton.mike", "baton.zulu"]
		assert b6.expand_scope("baton.*", list(reversed(scrambled))) == \
			b6.expand_scope("baton.*", scrambled)

	def test_expansion_reaches_no_authority(self):
		"""Pure: it takes the participant list and returns a list. Nothing
		here opens a store, which is what lets it be the first thing built and
		the first thing tested."""
		assert b6.expand_scope("t.*", ["t.a"]) == ["t.a"]


class TestScopedNoticeAudience:
	"""The audience is frozen at publication -- global and scoped alike.

	Ruled: a broadcast is to the participants who existed when it was sent, so
	a config addition cannot grant a new identity access to historic broadcast
	content."""

	def test_a_scope_reaches_its_team_and_nobody_else(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                  body=b"team only\n", ttl_seconds=3600)
			reached = [p["address"] for p in store.list_participants()
			           if store.see(p["address"])]
		assert all(a.startswith("acme.") for a in reached), reached
		assert len(reached) >= 2, "the scope reached fewer than the whole team"

	def test_a_global_notice_still_reaches_everyone(self, instance):
		"""Author parity unchanged: a matching author is in their own
		audience."""
		with b6.open_instance(instance) as store:
			everyone = sorted(p["address"] for p in store.list_participants())
			store.send_notice("hq.lead", kind="fyi", body=b"all\n", ttl_seconds=3600)
			reached = sorted(p for p in everyone if store.see(p))
		assert reached == everyone

	def test_a_newcomer_added_by_regen_cannot_receive_an_older_notice(self, tmp_path):
		"""THE RULED BEHAVIOUR CHANGE, through a REAL generation transition.

		An earlier version of this test only asked an undeclared identity to
		call `see` and watched it fail — which proves nothing, because an
		unconfigured address fails for a different reason entirely. It never
		edited the config and never ran `regen`, so it could not have caught a
		newcomer inheriting old broadcasts.

		This adds a participant by regen and asserts both halves: they do NOT
		receive the notice published before they existed, and they DO receive
		one published after."""
		import shutil
		home = tmp_path / "inst"
		home.mkdir()
		config_path = str(home / "baton.json")
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"),
		            config_path)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as store:
			store.send_notice("org.lead", kind="fyi", body=b"before\n",
			                  ttl_seconds=3600)

		config = json.loads(open(config_path).read())
		config["participants"]["team.newcomer"] = {}
		config["generation"] += 1
		open(config_path, "w").write(json.dumps(config))
		b6.regen_instance(config_path, participant="org.lead")

		with b6.open_instance(config_path) as store:
			assert store.see("team.newcomer") == [], \
				"a newcomer inherited a broadcast published before they existed"
			assert store.has_unseen_notice("team.newcomer") is False
			# ...and is a full member of anything published from now on.
			store.send_notice("org.lead", kind="fyi", body=b"after\n",
			                  ttl_seconds=3600)
			later = store.see("team.newcomer")
		assert len(later) == 1

	def test_how_it_was_addressed_is_recorded_beside_who_it_reached(self, instance):
		"""The audience table alone cannot tell `--scope acme.*` from a global
		notice that happened to match the same people, and both retry identity
		and the detail header need to."""
		with b6.open_instance(instance) as store:
			scoped = store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                           body=b"x\n", ttl_seconds=3600)
			glob = store.send_notice("hq.lead", kind="fyi", body=b"y\n",
			                         ttl_seconds=3600)
			rows = {r["id"]: (r["audience_kind"], r["selector"]) for r in
			        store.conn.execute("SELECT id, audience_kind, selector FROM notices")}
		assert rows[scoped] == ("scope", "acme.*")
		assert rows[glob] == ("global", None)

	@pytest.mark.parametrize("selector", ["nosuch.*", "acme", "*", "ACME.*"])
	def test_a_bad_scope_writes_nothing_at_all(self, instance, selector):
		"""Refused BEFORE the transaction opens, so a typo costs no authority
		write -- not a rolled-back one, none."""
		with b6.open_instance(instance) as store:
			before = store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
			with pytest.raises(b6.BatonError):
				store.send_notice("hq.lead", kind="fyi", scope=selector,
				                  body=b"x\n", ttl_seconds=3600)
			after = store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
		assert after == before

	def test_the_audience_is_immutable(self, instance):
		"""It is the record of who a broadcast was addressed to, and a record
		that can be edited is not that record."""
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="fyi", body=b"x\n", ttl_seconds=3600)
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute("UPDATE notice_audience SET participant='x.y'")

	def test_an_explicit_open_by_id_refuses_a_non_member(self, instance):
		"""R1, and it was the critical one.

		`see`, `list_notices` and `list_notice_activity` select BY membership,
		so scope holds there by construction. `mark_notice_seen` selects by ID,
		which is a different question — and any configured participant who
		learned a scoped notice's id could read team-only content and record a
		receipt for it.

		The refusal is deliberately INDISTINGUISHABLE from "unknown notice": a
		different message would confirm the id exists, which is itself
		information a non-member is not entitled to."""
		with b6.open_instance(instance) as store:
			notice_id = store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                              body=b"team only\n", ttl_seconds=3600)
			with pytest.raises(b6.BatonError) as caught:
				store.mark_notice_seen("hq.lead", notice_id)
			assert "unknown notice" in str(caught.value)
			# NO receipt was recorded, so the non-member did not consume the
			# notice on behalf of anyone.
			seen = store.conn.execute(
				"SELECT COUNT(*) FROM notice_seen WHERE notice_id=?",
				(notice_id,)).fetchone()[0]
			assert seen == 0
			# And a member still gets it, once.
			opened = store.mark_notice_seen("acme.implementer", notice_id)
			assert opened.get("already_seen") is not True
			again = store.mark_notice_seen("acme.implementer", notice_id)
			assert again["already_seen"] is True

	def test_the_schema_refuses_a_receipt_outside_the_audience(self, instance):
		"""Authorization in the schema as well as the code path, so another
		query cannot recreate the bypass."""
		with b6.open_instance(instance) as store:
			notice_id = store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                              body=b"x\n", ttl_seconds=3600)
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute(
					"INSERT INTO notice_seen(notice_id, participant, seen_ts) "
					"VALUES(?,?,?)", (notice_id, "hq.lead", "2026-01-01T00:00:00Z"))

	def test_the_idle_probe_does_not_report_another_teams_notice(self, instance):
		"""R2. The probe keeps an idle waiter out of a write transaction. With
		no membership predicate a scoped notice woke every unrelated
		participant, who then took the `see` write lock to be told there was
		nothing for them — reintroducing the exact contention the probe exists
		to avoid, across teams."""
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                  body=b"team only\n", ttl_seconds=3600)
			assert store.has_unseen_notice("acme.implementer") is True
			assert store.has_unseen_notice("hq.lead") is False, \
				"an unrelated participant was woken by another team's notice"
			# And the probe agrees with what `see` would actually hand over.
			assert store.see("hq.lead") == []

	def test_dump_carries_the_frozen_audience(self, instance):
		"""`dump` promises every protocol table, and the immutable answer to
		"who received this?" is exactly the sort of thing an inspection surface
		exists for."""
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                  body=b"x\n", ttl_seconds=3600)
		dumped = b6.dump(instance)
		assert "notice_audience" in dumped
		assert {row["participant"] for row in dumped["notice_audience"]} == \
			{"acme.implementer", "acme.reviewer"}

	def test_the_packaged_cli_publishes_and_shows_a_scoped_notice(self, tmp_path):
		"""End to end on the built executable: a team notice reaches its team,
		does not reach anyone else, and says which team it was for."""
		import subprocess, sys as _sys, shutil
		root = tmp_path / "dist"
		TestPackaging()._builder().build(str(root))
		inst = tmp_path / "inst"
		inst.mkdir()
		config_path = str(inst / "baton.json")
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"),
		            config_path)
		env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path)}

		def run(*args, stdin=b""):
			return subprocess.run(
				[_sys.executable, str(root / "bin" / "baton"), "--config",
				 config_path, *args], input=stdin, capture_output=True,
				cwd=str(tmp_path), env=env, timeout=60)

		assert run("init").returncode == 0
		# The example config has team.* and org.lead.
		proc = run("send-notice", "--participant", "org.lead", "--kind", "fyi",
		           "--scope", "team.*", stdin=b"team only\n")
		assert proc.returncode == 0, proc.stderr

		seen = json.loads(run("see", "--participant", "team.reviewer").stdout)
		assert len(seen["notices"]) == 1
		assert seen["notices"][0]["selector"] == "team.*"
		assert seen["notices"][0]["audience_kind"] == "scope"

		# The author is outside the scope and gets nothing.
		assert json.loads(run("see", "--participant", "org.lead").stdout)["notices"] == []

		# A malformed scope is refused, and writes nothing.
		bad = run("send-notice", "--participant", "org.lead", "--kind", "fyi",
		          "--scope", "nosuch.*", stdin=b"x\n")
		assert bad.returncode != 0
		assert "matches no configured participant" in bad.stderr.decode()

	def test_regen_will_not_strand_an_addressee(self, tmp_path):
		"""R3. The gate protected notice AUTHORS and not addressees, so a
		removal could freeze a participant into an immutable audience and
		simultaneously make them undeclared and unable to consume it.

		The refusal is not permanent: once they have seen it, or the notice
		expires or is collected, the removal goes through — without ever
		rewriting retained history."""
		import shutil
		home = tmp_path / "inst"
		home.mkdir()
		config_path = str(home / "baton.json")
		shutil.copy(os.path.join(os.path.dirname(__file__), "example-baton.json"),
		            config_path)
		b6.init_instance(config_path)
		with b6.open_instance(config_path) as store:
			store.send_notice("org.lead", kind="fyi", scope="team.*",
			                  body=b"x\n", ttl_seconds=3600)

		original = open(config_path).read()

		def drop(address):
			config = json.loads(open(config_path).read())
			config["participants"].pop(address)
			config["generation"] += 1
			open(config_path, "w").write(json.dumps(config))

		drop("team.reviewer")
		with pytest.raises(b6.BatonError) as caught:
			b6.regen_instance(config_path, participant="org.lead")
		assert "team.reviewer" in str(caught.value)

		# Restore the config VERBATIM -- same generation, same digest -- so the
		# instance accepts it again without a regen, and let the addressee take
		# delivery.
		open(config_path, "w").write(original)
		with b6.open_instance(config_path) as store:
			assert store.see("team.reviewer")

		# Now nothing is stranded and the removal goes through.
		drop("team.reviewer")
		b6.regen_instance(config_path, participant="org.lead")


class TestScopedNoticeWakeup:
	"""A scoped notice must wake its team and nobody else — through the real
	`wait` path, not only the probe.

	The existing global-wait tests cannot catch a missing scope predicate,
	because every participant belongs to a global audience. These are the
	scoped equivalents."""

	def test_a_scoped_notice_already_present_wakes_only_its_team(self, instance):
		with b6.open_instance(instance) as st:
			st.send_notice("hq.lead", kind="fyi", scope="acme.*",
			               body=b"team only\n", ttl_seconds=3600)
		got = b6.wait_for_message(instance, "acme.implementer", timeout_s=5)
		assert got["notice"]["selector"] == "acme.*"
		# The unrelated participant times out rather than being woken.
		with pytest.raises(b6.BatonError) as caught:
			b6.wait_for_message(instance, "hq.lead", timeout_s=0.4,
			                    rescan_interval_s=0.1)
		assert caught.value.exit_code == b6.EXIT_NONE

	def test_a_scoped_notice_published_while_blocked_wakes_the_member(self, instance):
		def publisher():
			_time.sleep(0.5)
			with b6.open_instance(instance) as st:
				st.send_notice("hq.lead", kind="fyi", scope="acme.*",
				               body=b"late\n", ttl_seconds=3600)
		thread = threading.Thread(target=publisher)
		thread.start()
		start = _time.monotonic()
		got = b6.wait_for_message(instance, "acme.reviewer", timeout_s=30,
		                          rescan_interval_s=20)
		elapsed = _time.monotonic() - start
		thread.join()
		assert got["notice"]["audience_kind"] == "scope"
		assert elapsed < 15, "woken by the 20s rescan rather than the watch"

	def test_degraded_polling_still_scopes(self, instance, monkeypatch):
		"""Without inotify this is pure interval polling, and the membership
		predicate has to hold on that path too."""
		class Broken:
			def __init__(self, _dir):
				raise OSError("inotify unavailable")

		monkeypatch.setattr(b6, "_InotifyWatch", Broken)

		def publisher():
			_time.sleep(0.4)
			with b6.open_instance(instance) as st:
				st.send_notice("hq.lead", kind="fyi", scope="acme.*",
				               body=b"late\n", ttl_seconds=3600)

		thread = threading.Thread(target=publisher)
		thread.start()
		got = b6.wait_for_message(instance, "acme.implementer", timeout_s=30,
		                          rescan_interval_s=0.2)
		thread.join()
		assert got["notice"]["selector"] == "acme.*"

	def test_an_unrelated_participant_records_no_receipt_and_stays_read_only(
			self, instance):
		"""The contention half of the contract. An unrelated participant must
		not be told there is work, and must therefore never enter `see`'s
		write transaction to be told there is not."""
		with b6.open_instance(instance) as st:
			st.send_notice("hq.lead", kind="fyi", scope="acme.*",
			               body=b"team only\n", ttl_seconds=3600)
			assert st.has_unseen_notice("hq.lead") is False
			assert st.see("hq.lead") == []
			receipts = st.conn.execute(
				"SELECT COUNT(*) FROM notice_seen").fetchone()[0]
		assert receipts == 0, "an unrelated participant recorded a receipt"


def _publish_scoped_with_fault(config_path, point, queue):
	"""Publish a scoped notice, failing at an injected point after the notice
	and its audience rows are written."""
	import baton_core._impl as mod
	original = mod.Store._write_parts

	def explode(self, owner_kind, owner_id, nodes, now):
		if point == "after_audience":
			raise RuntimeError("injected fault")
		return original(self, owner_kind, owner_id, nodes, now)

	mod.Store._write_parts = explode
	try:
		with mod.open_instance(config_path) as store:
			store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                  body=b"x\n", ttl_seconds=3600)
		queue.put("committed")
	except BaseException as error:
		queue.put(f"failed: {error}")


class TestScopedNoticeAtomicity:
	def test_a_fault_after_the_audience_rolls_everything_back(self, instance):
		"""Notice, audience rows and parts commit together or not at all. A
		surviving notice with no audience would be unreachable by anyone; a
		surviving audience with no notice is the orphan doctor looks for."""
		queue = multiprocessing.Queue()
		process = multiprocessing.Process(
			target=_publish_scoped_with_fault,
			args=(instance, "after_audience", queue))
		process.start()
		process.join(30)
		assert queue.get(timeout=5).startswith("failed:")
		with b6.open_instance(instance) as store:
			assert store.conn.execute(
				"SELECT COUNT(*) FROM notices").fetchone()[0] == 0
			assert store.conn.execute(
				"SELECT COUNT(*) FROM notice_audience").fetchone()[0] == 0
		assert b6.doctor(instance)["problems"] == []


def _damage_is_caught(instance, fragment):
	"""Either doctor names it, or an earlier integrity layer refuses to open
	the instance at all.

	Both are the system catching corruption; only one of them is doctor's job.
	Asserting the disjunction is honest about which states are reachable — an
	earlier version of these tests demanded the doctor branch specifically and
	failed, because the store will not open a database whose foreign keys are
	broken, which is a better outcome than a report."""
	try:
		problems = b6.doctor(instance)["problems"]
	except b6.BatonError as refusal:
		return "integrity" in str(refusal) or "foreign_key" in str(refusal)
	return any(fragment in problem for problem in problems)


class TestDoctorNoticeAudience:
	"""Each of the five new doctor branches, driven by the damage it exists to
	find. A check nobody has ever seen fail is a check nobody knows works.

	The guards make this awkward on purpose — every one of these has to defeat
	an immutability trigger to plant the damage, which is itself evidence that
	the ordinary paths cannot produce it. `PRAGMA defer_foreign_keys` and a
	direct connection are the test's tools, not the product's."""

	def _corrupt(self, instance, statements):
		"""Plant damage the ordinary paths cannot produce.

		It needs the operation context the product itself sets, because the
		insert guards refuse writes outside one -- which is itself worth
		noticing: every state below required defeating a guard to create, so
		none of them can arise from an ordinary publication. Doctor is the
		net under corruption from elsewhere, not under this code.
		"""
		import sqlite3 as sql
		path = os.path.join(os.path.dirname(instance), "mailbox.sqlite3")
		conn = sql.connect(path)
		try:
			conn.execute("PRAGMA foreign_keys=OFF")
			conn.execute(
				"UPDATE op_context SET op_id='doctor-test', participant='hq.lead', "
				"verb='gc', ts='2026-01-01T00:00:00Z' WHERE one_row=1")
			for statement, args in statements:
				conn.execute(statement, args)
			conn.execute("UPDATE op_context SET op_id=NULL, participant=NULL, "
			             "verb=NULL, ts=NULL WHERE one_row=1")
			conn.commit()
		finally:
			conn.close()

	def test_an_empty_audience_is_detected(self, instance):
		"""Reported by doctor OR refused before doctor can run -- and which
		one it is is worth knowing rather than papering over.

		Deleting the audience leaves the receipt foreign key dangling, so the
		instance fails its integrity check on OPEN and never reaches the
		doctor branch. That is a stronger outcome than a report, and the
		branch remains as the net for damage that does not break referential
		integrity."""
		with b6.open_instance(instance) as store:
			notice_id = store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                              body=b"x\n", ttl_seconds=3600)
			store.see("acme.implementer")
		self._corrupt(instance, [
			("DELETE FROM notice_audience WHERE notice_id=?", (notice_id,))])
		assert _damage_is_caught(instance, "empty frozen audience")

	def test_a_receipt_outside_the_audience_is_detected(self, instance):
		with b6.open_instance(instance) as store:
			notice_id = store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                              body=b"x\n", ttl_seconds=3600)
		self._corrupt(instance, [
			("INSERT INTO notice_seen(notice_id, participant, seen_ts) VALUES(?,?,?)",
			 (notice_id, "hq.lead", "2026-01-01T00:00:00Z"))])
		assert _damage_is_caught(instance, "not in its audience")

	def test_a_non_address_in_the_audience_is_detected(self, instance):
		with b6.open_instance(instance) as store:
			notice_id = store.send_notice("hq.lead", kind="fyi", body=b"x\n",
			                              ttl_seconds=3600)
		self._corrupt(instance, [
			("DELETE FROM notice_audience WHERE notice_id=?", (notice_id,)),
			("INSERT INTO notice_audience(notice_id, participant) VALUES(?,?)",
			 (notice_id, "a" * 70 + ".x"))])
		assert _damage_is_caught(instance, "not a participant address")

	def test_an_unparseable_selector_is_detected(self, instance):
		"""Overlong rather than malformed, deliberately: it MATCHES the regex
		and fails the bound, which is exactly what a bare `.match` missed."""
		with b6.open_instance(instance) as store:
			notice_id = store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                              body=b"x\n", ttl_seconds=3600)
		# The trigger is dropped to plant the damage and RESTORED immediately,
		# so what doctor sees is a bad selector rather than a missing trigger.
		# Leaving it dropped would test schema validation instead, which is a
		# different check and already covered.
		self._corrupt(instance, [
			("DROP TRIGGER trg_notice_frozen", ()),
			("UPDATE notices SET selector=? WHERE id=?",
			 ("a" * 70 + ".*", notice_id)),
			("CREATE TRIGGER trg_notice_frozen BEFORE UPDATE ON notices "
			 "BEGIN SELECT RAISE(ABORT, 'notices are immutable'); END", ())])
		assert _damage_is_caught(instance, "is not a scope")

	def test_an_orphaned_audience_row_is_detected(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="fyi", body=b"x\n", ttl_seconds=3600)
		self._corrupt(instance, [
			("INSERT INTO notice_audience(notice_id, participant) VALUES(?,?)",
			 ("no-such-notice", "acme.implementer"))])
		assert _damage_is_caught(instance, "outlived their notice")

	def test_a_healthy_instance_reports_none_of_them(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="fyi", scope="acme.*",
			                  body=b"x\n", ttl_seconds=3600)
			store.see("acme.implementer")
		assert b6.doctor(instance)["problems"] == []

	def test_a_scoped_notice_published_during_the_arm_window(self, instance, monkeypatch):
		"""The query-to-arm race, scoped.

		The global version cannot catch a missing membership predicate,
		because every participant is in a global audience. This publishes to
		`acme.*` in the window between the first query and the armed watch,
		and asserts the member is woken by the REQUERY rather than by the
		rescan — and, in the same run, that the unrelated participant sees
		nothing at all."""
		published = {}

		def publish_during_arm(point):
			if point == "wait:armed" and not published:
				published["done"] = True
				with b6.open_instance(instance) as st:
					st.send_notice("hq.lead", kind="fyi", scope="acme.*",
					               body=b"raced\n", ttl_seconds=3600)

		monkeypatch.setattr(b6, "_FAULT_HOOK", publish_during_arm)
		start = _time.monotonic()
		got = b6.wait_for_message(instance, "acme.implementer",
		                          timeout_s=30, rescan_interval_s=25)
		assert got["notice"]["selector"] == "acme.*"
		assert _time.monotonic() - start < 10, "the rescan caught it, not the requery"
		monkeypatch.setattr(b6, "_FAULT_HOOK", None)
		with b6.open_instance(instance) as st:
			assert st.has_unseen_notice("hq.lead") is False
			assert st.see("hq.lead") == []


class TestMultiRecipientPublication:
	"""One publication, N ordinary messages.

	The finding's requirement is that per-recipient lifecycles stay
	independent and exact. Under this shape that is true BY CONSTRUCTION —
	they are ordinary messages and were never joined — so these tests are
	checking that nothing accidentally joined them, not that a separation
	mechanism works."""

	def test_each_recipient_gets_an_independent_lifecycle(self, instance):
		with b6.open_instance(instance) as store:
			publication = store.send("hq.lead", ["acme.implementer", "acme.reviewer"],
			                         kind="q", subject="both", body=b"x\n")
			first = store.claim("acme.implementer")
			store.close_claim(first["claim_id"], participant="acme.implementer",
			                  outcome="done")
			# Resolving one leaves the other actionable, untouched.
			second = store.claim("acme.reviewer")
			assert second["state"] == "active"
			states = dict(store.conn.execute(
				"SELECT to_participant, state FROM messages WHERE publication_id=?",
				(publication,)).fetchall())
		assert states == {"acme.implementer": "closed", "acme.reviewer": "claimed"}

	def test_a_single_recipient_still_returns_a_message_id(self, instance):
		"""The historical shape is unchanged. A caller addressing one
		participant sees exactly what it always saw."""
		with b6.open_instance(instance) as store:
			returned = store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			row = store.conn.execute(
				"SELECT id, publication_id FROM messages WHERE id=?",
				(returned,)).fetchone()
		assert row is not None, "the return value is not a message id"
		assert row["publication_id"] is not None, \
			"a single-recipient send has no publication row"

	def test_the_audience_survives_a_collected_delivery(self, instance):
		"""WHY the publication record exists at all. Deriving the audience
		from surviving message rows would shrink it as deliveries are removed,
		and the detail header and later authorization both read it."""
		with b6.open_instance(instance) as store:
			publication = store.send("hq.lead", ["acme.implementer", "acme.reviewer"],
			                         kind="q", body=b"x\n")
			# Under the `gc` verb, because that is the only thing allowed to
			# remove a delivery -- the guard refused a bare DELETE, which is
			# itself the evidence that this state cannot arise casually.
			store.conn.execute(
				"UPDATE op_context SET op_id='t', participant='hq.lead', "
				"verb='gc', ts='2026-01-01T00:00:00Z' WHERE one_row=1")
			store.conn.execute("DELETE FROM messages WHERE to_participant=? "
			                   "AND publication_id=?",
			                   ("acme.implementer", publication))
			store.conn.execute(
				"UPDATE op_context SET op_id=NULL, participant=NULL, verb=NULL, "
				"ts=NULL WHERE one_row=1")
			audience = {r["participant"] for r in store.conn.execute(
				"SELECT participant FROM publication_audience WHERE publication_id=?",
				(publication,))}
		assert audience == {"acme.implementer", "acme.reviewer"}

	@pytest.mark.parametrize("recipients,fragment", [
		(["acme.implementer", "acme.implementer"], "duplicate recipient"),
		(["acme.*"], "is a scope"),
		(["acme.implementer", "acme.*"], "is a scope"),
		([], "at least one recipient"),
		(["nobody.here"], "nobody.here"),
	])
	def test_a_bad_audience_writes_nothing(self, instance, recipients, fragment):
		"""Refused before the transaction opens. A wildcard in `--to` is the
		one worth naming: it would turn "assign this work to a team" into
		something with no per-recipient claim."""
		with b6.open_instance(instance) as store:
			before = store.conn.execute(
				"SELECT COUNT(*) FROM publications").fetchone()[0]
			with pytest.raises(b6.BatonError) as caught:
				store.send("hq.lead", recipients, kind="q", body=b"x\n")
			assert fragment in str(caught.value)
			after = store.conn.execute(
				"SELECT COUNT(*) FROM publications").fetchone()[0]
		assert after == before

	def test_publication_is_atomic_across_recipients(self, instance):
		"""Either every delivery exists or none. A partial audience would
		leave some recipients holding work the others were never told about,
		with nothing in the store able to say which."""
		with b6.open_instance(instance) as store:
			original = store._insert_message
			calls = {"n": 0}

			def explode(*args, **kwargs):
				calls["n"] += 1
				if calls["n"] == 2:
					raise RuntimeError("injected fault on the second delivery")
				return original(*args, **kwargs)

			store._insert_message = explode
			with pytest.raises(RuntimeError):
				store.send("hq.lead", ["acme.implementer", "acme.reviewer"],
				           kind="q", body=b"x\n")
			store._insert_message = original
			assert store.conn.execute(
				"SELECT COUNT(*) FROM messages").fetchone()[0] == 0
			assert store.conn.execute(
				"SELECT COUNT(*) FROM publications").fetchone()[0] == 0
			assert store.conn.execute(
				"SELECT COUNT(*) FROM publication_audience").fetchone()[0] == 0

	def test_possible_duplicate_is_the_senders_assertion_and_immutable(self, instance):
		"""Publication is at-least-once by ruling. The flag says the SENDER
		could not tell whether an earlier attempt committed — Baton does not
		identify or correlate the original, and the recipient decides what to
		do about it.

		Immutable, because a warning that can be set or cleared afterwards is
		a rumour rather than a record."""
		with b6.open_instance(instance) as store:
			plain = store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			warned = store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n",
			                    possible_duplicate=True)
			flags = dict(store.conn.execute(
				"SELECT m.id, p.possible_duplicate FROM messages m "
				"JOIN publications p ON p.publication_id = m.publication_id").fetchall())
			assert flags[plain] == 0
			assert flags[warned] == 1
			# Two deliberate identical publications remain possible, and the
			# second is a SEPARATE publication rather than a retry of the first.
			assert plain != warned
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute("UPDATE publications SET possible_duplicate=0")


class TestAudienceOnDelivery:
	"""The audience reaches the RECIPIENT, not just the database.

	The finding requires that delivery identify the original audience so a
	human can tell a private message from work deliberately assigned to
	several participants. `to_participant` says "me" in both cases, so
	without this the distinction exists only in tables nobody reads while
	deciding whether to start work.
	"""

	def test_every_recipient_sees_the_whole_audience(self, instance):
		with b6.open_instance(instance) as store:
			store.send("hq.lead", ["acme.implementer", "acme.reviewer"],
			           kind="q", subject="both", body=b"x\n")
			delivered = b6._delivery(store, store.claim("acme.implementer"))
		assert delivered["message"]["audience"] == ["acme.implementer", "acme.reviewer"], \
			"a recipient of shared work cannot see that it was shared"

	def test_a_private_message_carries_only_its_one_recipient(self, instance):
		"""The distinction has to cut both ways to be worth anything."""
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			delivered = b6._delivery(store, store.claim("acme.implementer"))
		assert delivered["message"]["audience"] == ["acme.implementer"]

	def test_the_delivered_audience_does_not_shrink_with_a_collected_delivery(self, instance):
		"""Reading the audience off surviving `messages` rows would tell the
		remaining recipient the work was more private than it was -- and it
		would change as GC ran, so the same message would read differently on
		Tuesday. The canonical audience is the publication's."""
		with b6.open_instance(instance) as store:
			publication = store.send("hq.lead", ["acme.implementer", "acme.reviewer"],
			                         kind="q", subject="both", body=b"x\n")
			# Removed under the `gc` verb, the only thing permitted to collect
			# a delivery -- the same route the sibling audience test uses. A
			# bare DELETE is refused by the guard, which is itself evidence
			# that this state cannot arise casually.
			store.conn.execute(
				"UPDATE op_context SET op_id='t', participant='hq.lead', "
				"verb='gc', ts='2026-01-01T00:00:00Z' WHERE one_row=1")
			store.conn.execute("DELETE FROM messages WHERE publication_id=? "
			                   "AND to_participant=?", (publication, "acme.reviewer"))
			store.conn.execute(
				"UPDATE op_context SET op_id=NULL, participant=NULL, verb=NULL, "
				"ts=NULL WHERE one_row=1")
			delivered = b6._delivery(store, store.claim("acme.implementer"))
		assert delivered["message"]["audience"] == ["acme.implementer", "acme.reviewer"], \
			"the audience shrank when another recipient's delivery was collected"

	def test_the_duplicate_warning_reaches_a_directed_recipient(self, instance):
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n",
			           possible_duplicate=True)
			delivered = b6._delivery(store, store.claim("acme.implementer"))
		assert delivered["message"]["possible_duplicate"] is True

	def test_an_ordinary_message_carries_no_warning(self, instance):
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			delivered = b6._delivery(store, store.claim("acme.implementer"))
		assert delivered["message"]["possible_duplicate"] is False


class TestNoticeDuplicateWarning:
	"""The ruling covers `send-notice` as well as `send`.

	A broadcast can be republished after an ambiguous result exactly as a
	directed message can, and a recipient deciding what to do about the second
	copy needs the same sender-supplied warning."""

	def test_a_repeated_notice_can_carry_the_warning(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="ann", body=b"deploy\n",
			                  possible_duplicate=True)
			delivered = [b6._notice_delivery(n) for n in store.see("acme.implementer")]
		assert delivered[0]["notice"]["possible_duplicate"] is True, \
			"the warning does not reach a broadcast recipient"

	def test_an_ordinary_notice_carries_no_warning(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="ann", body=b"deploy\n")
			delivered = [b6._notice_delivery(n) for n in store.see("acme.implementer")]
		assert delivered[0]["notice"]["possible_duplicate"] is False

	def test_the_notice_warning_is_immutable(self, instance):
		"""Same reason as the publication column: it is the sender's assertion
		about what they could observe at one moment, and a later edit would
		rewrite what they said."""
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="ann", body=b"deploy\n",
			                  possible_duplicate=True)
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute("UPDATE notices SET possible_duplicate=0")


class TestReplyPublication:
	"""A response is a directed message, so it has a publication too.

	It did not. `send` created the publication and `reply` called
	`_insert_message` directly, so every response carried a NULL link and
	delivered `audience: []` -- while the stage plan already required
	otherwise. The two creation paths are now one, which is the part that
	stops this recurring."""

	def test_a_reply_creates_its_own_publication(self, instance):
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			claim = store.claim("acme.implementer")
			result = store.reply(claim["claim_id"], participant="acme.implementer",
			                     kind="a", body=b"y\n")
			row = store.conn.execute(
				"SELECT publication_id FROM messages WHERE id=?",
				(result["response_message_id"],)).fetchone()
		assert row["publication_id"] is not None, \
			"the response message has no publication record"

	def test_the_reply_audience_is_the_original_sender(self, instance):
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			claim = store.claim("acme.implementer")
			store.reply(claim["claim_id"], participant="acme.implementer",
			            kind="a", body=b"y\n")
			delivered = b6._delivery(store, store.claim("hq.lead"))
		assert delivered["message"]["audience"] == ["hq.lead"], \
			"a reply does not name its own single recipient"

	def test_a_retried_reply_does_not_mint_a_second_publication(self, instance):
		"""The claim disposition stays the effectively-once key. If a retry
		published again, one response would have two publication records and
		the audience would depend on which was read."""
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			claim = store.claim("acme.implementer")
			first = store.reply(claim["claim_id"], participant="acme.implementer",
			                    kind="a", body=b"y\n")
			before = store.conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
			again = store.reply(claim["claim_id"], participant="acme.implementer",
			                    kind="a", body=b"y\n")
			after = store.conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
		assert again["already_committed"] is True
		assert again["response_message_id"] == first["response_message_id"]
		assert after == before, "the retry created another publication"

	def test_no_directed_message_is_left_without_a_publication(self, instance):
		"""The invariant itself, over every path that creates one. A future
		fifth verb that inserts a message directly fails here rather than in
		somebody's delivery six weeks later."""
		with b6.open_instance(instance) as store:
			store.send("hq.lead", ["acme.implementer", "acme.reviewer"],
			           kind="q", subject="s", body=b"x\n")
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			claim = store.claim("acme.implementer")
			store.reply(claim["claim_id"], participant="acme.implementer",
			            kind="a", body=b"y\n")
			orphans = store.conn.execute(
				"SELECT id, kind FROM messages WHERE publication_id IS NULL").fetchall()
		assert [dict(r) for r in orphans] == []


class TestReadiness:
	"""Blocking readiness: says work exists, takes none of it.

	The safety property is not "it returns quickly" -- it is that a process
	left in a terminal that never wakes its agent cannot end up holding work.
	Every test here is really asking the same question: did observing change
	anything?"""

	def test_readiness_reports_directed_work_without_claiming_it(self, instance):
		with b6.open_instance(instance) as store:
			send_one(store)
			state = store.readiness("acme.implementer")
			claims = store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
			# The work is STILL THERE for an ordinary consumer.
			claim = store.claim("acme.implementer")
		assert state["ready"] is True and state["channel"] == "message"
		assert claims == 0, "readiness created a claim"
		assert claim["message_id"] == state["message_id"]

	def test_readiness_returns_no_content(self, instance):
		"""Metadata only. A readiness result carrying the body would make the
		'safe' verb the one that quietly delivers work nobody acknowledged."""
		with b6.open_instance(instance) as store:
			send_one(store)
			state = store.readiness("acme.implementer")
		assert "content" not in state and "parts" not in state
		assert "subject" not in state and "body" not in state

	def test_readiness_reports_a_notice_without_writing_a_receipt(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="ann", body=b"deploy\n")
			state = store.readiness("acme.implementer")
			receipts = store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0]
			# Still deliverable: the receipt belongs to `see`, not to looking.
			delivered = store.see("acme.implementer")
		assert state["ready"] is True and state["channel"] == "notice"
		assert receipts == 0, "readiness consumed the notice"
		assert len(delivered) == 1

	def test_readiness_does_not_name_the_notice(self, instance):
		"""Naming one would invite the caller to consume that specific notice,
		while `see` drains oldest-first -- so a notice arriving in between
		would be consumed under another one's name."""
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="ann", body=b"one\n")
			state = store.readiness("acme.implementer")
		assert "notice_id" not in state

	def test_directed_work_outranks_a_notice(self, instance):
		with b6.open_instance(instance) as store:
			store.send_notice("hq.lead", kind="ann", body=b"deploy\n")
			send_one(store)
			state = store.readiness("acme.implementer")
		assert state["channel"] == "message"

	def test_an_empty_inbox_is_not_ready(self, instance):
		with b6.open_instance(instance) as store:
			state = store.readiness("acme.implementer")
		assert state["ready"] is False and state["channel"] is None

	def test_blocking_readiness_wakes_on_a_late_send_without_claiming(self, instance):
		"""The reviewer's regression target: this must fail if the event wake
		is dead, not pass a minute later on the safety rescan. The rescan is
		set to 20s and the assertion is 15s, so only a real filesystem event
		can satisfy it."""
		def sender():
			_time.sleep(0.5)
			with b6.open_instance(instance) as st:
				send_one(st)
		thread = threading.Thread(target=sender)
		thread.start()
		start = _time.monotonic()
		state = b6.wait_for_readiness(instance, "acme.implementer",
		                              timeout_s=30, rescan_interval_s=20)
		elapsed = _time.monotonic() - start
		thread.join()
		assert state["ready"] is True and state["channel"] == "message"
		assert elapsed < 15, "woken by the safety rescan, not the watch"
		with b6.open_instance(instance) as store:
			assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0, \
				"the readiness waiter claimed the message"

	def test_blocking_readiness_times_out_like_wait(self, instance):
		with pytest.raises(b6.BatonError) as excinfo:
			b6.wait_for_readiness(instance, "acme.implementer",
			                      timeout_s=0.3, rescan_interval_s=0.1)
		assert excinfo.value.exit_code == b6.EXIT_NONE

	def test_readiness_returns_the_same_result_twice(self, instance):
		"""Idempotent BECAUSE it writes nothing. A consuming waiter cannot
		say this, and it is what makes an unattended readiness process
		harmless."""
		with b6.open_instance(instance) as store:
			send_one(store)
			first = store.readiness("acme.implementer")
			second = store.readiness("acme.implementer")
		assert first == second

	def test_a_damaged_head_is_ready_and_says_it_is_damaged(self, tmp_path):
		"""Ruled 2026-08-10, and it reverses what I built first.

		I had readiness skip damaged messages, because `claim` does. That
		hides the one state a human most needs to see: it would report the
		queue as healthy and shorter than it is, and the damaged message would
		sit at the head unmentioned. There IS something here and it IS next --
		what it needs is `quarantine` rather than `claim`, and the result says
		so."""
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		with b6.open_instance(config_path) as store:
			state = store.readiness("acme.implementer")
		assert state["ready"] is True
		assert state["message_id"] == damaged
		assert state["damaged"] is True

	def test_readiness_never_scans_past_the_head(self, tmp_path):
		"""The FIFO half of the same ruling. Reporting the healthy message
		behind a damaged one answers "what could be claimed", which is not
		what was asked -- and it is how the damaged head goes unnoticed."""
		config_path, root = _attach_instance(tmp_path)
		damaged, path = _send_attached(config_path, root, "EVIDENCE.md")
		path.write_bytes(b"edited after publication\n")
		# A REAL second apart, not a forged timestamp: `created_ts` has
		# second resolution, so two sends in the same second are ordered by a
		# random id and "the head" would not be well defined. The guard
		# refuses a bare UPDATE to fake it, which is the right answer -- the
		# ordering this test depends on has to be the ordering the store
		# actually produces.
		_time.sleep(1.1)
		with b6.open_instance(config_path) as store:
			healthy = send_one(store, body=b"fine")
			state = store.readiness("acme.implementer")
		assert state["message_id"] == damaged, "readiness looked past the head"
		assert state["message_id"] != healthy


class TestOrphanPublicationDoctor:
	"""`doctor` had four publication checks and every one of them validated
	rows that HAVE a publication. Nothing looked for a message without one,
	which is why the defect reached a live instance and was reported ok."""

	def test_a_healthy_instance_reports_no_orphans(self, instance):
		with b6.open_instance(instance) as store:
			store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			claim = store.claim("acme.implementer")
			store.reply(claim["claim_id"], participant="acme.implementer",
			            kind="a", body=b"y\n")
		report = b6.doctor(instance)
		assert report["ok"] is True, report["problems"]

	def test_the_schema_refuses_a_message_with_no_publication(self, instance):
		"""The invariant moved from "doctor notices" to "the database
		refuses", ruled 2026-08-10.

		This test REPLACED one that constructed an orphan and asserted doctor
		reported it. That test can no longer be written: with `NOT NULL` in
		place there is no way to produce the row, which is a better outcome
		than a diagnosis of it. The doctor check is kept as a backstop for
		authorities created by earlier protocol-10 builds -- the live one has
		28 such rows right now -- and it stops being reachable once that is
		archived and cut over."""
		with b6.open_instance(instance) as store:
			mid = store.send("hq.lead", "acme.implementer", kind="q", body=b"x\n")
			store.conn.execute(
				"UPDATE op_context SET op_id='t', participant='hq.lead', "
				"verb='gc', ts='2026-01-01T00:00:00Z' WHERE one_row=1")
			with pytest.raises(sqlite3.IntegrityError):
				store.conn.execute("UPDATE messages SET publication_id=NULL WHERE id=?", (mid,))
