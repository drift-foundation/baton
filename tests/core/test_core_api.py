"""Stage 2: the public core API the console needs.

These cover the capabilities that do not exist in the frozen oracle, so they
run against `baton_core` only. The oracle remains the parity reference for
everything it does implement; this file is where the two are ALLOWED to
diverge, deliberately and visibly.
"""

from __future__ import annotations

import json

import pytest

import baton_core as core


def make_config(tmp_path, name="inst"):
	home = tmp_path / name
	home.mkdir()
	root = home / "root"
	root.mkdir()
	(root / "EVIDENCE.md").write_bytes(b"pinned evidence\n")
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
			"mailbox": {"name": "console"},
			"participants": {"acme.reviewer": {}, "acme.implementer": {},
			                 "hq.lead": {"capabilities": ["recovery", "config"]}},
			"roots": {"src": str(root)}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path, root


FORBIDDEN_IN_PREVIEW = ("text", "base64", "body", "root_id", "path", "encoding",
                        "attachment", "manifest_sha256", "sha256")


def assert_no_delivery_content(value, where="preview"):
	"""A preview must never carry delivery content. Swept structurally rather
	than field by field, so a future key cannot quietly reintroduce the hole
	that this whole API split exists to close."""
	if isinstance(value, dict):
		for key, item in value.items():
			assert key not in FORBIDDEN_IN_PREVIEW, f"{where} exposes {key!r}"
			assert not isinstance(item, (bytes, bytearray)), f"{where}.{key} is bytes"
			assert_no_delivery_content(item, f"{where}.{key}")
	elif isinstance(value, list):
		for index, item in enumerate(value):
			assert_no_delivery_content(item, f"{where}[{index}]")


def _authority_counts(store):
	"""Every table an observation must not touch."""
	one = lambda name: store.conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
	return tuple(one(name) for name in
	             ("claims", "dispositions", "transitions", "notice_seen",
	              "messages", "notices"))


@pytest.fixture
def inst(tmp_path):
	path, root = make_config(tmp_path)
	return path, root


# -- observation never consumes -------------------------------------------

def test_listing_notices_commits_no_receipt(inst):
	"""THE reason this API exists. `see` returns bytes and commits the receipt
	in one transaction, so a polling inbox would destroy every broadcast by
	rendering it, and a crash a frame later would lose it permanently."""
	path, _ = inst
	with core.open_instance(path) as store:
		store.send_notice("hq.lead", kind="announcement",
		                  subject="All hands", body=b"details\n")
		# Poll the way an inbox refresh loop would.
		for _ in range(25):
			listed = store.list_notices("acme.implementer")
			assert len(listed) == 1
			assert listed[0]["subject"] == "All hands"
			assert listed[0]["seen_ts"] is None
		assert store.conn.execute(
			"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
		# METADATA ONLY. Listing must not become a second delivery path that
		# hands out broadcast bytes with no receipt behind it -- then the
		# at-most-once guarantee would depend on which API a caller chose.
		assert_no_delivery_content(listed)
		assert listed[0]["parts"][0]["content_type"] == "text/markdown; charset=utf-8"
		assert listed[0]["parts"][0]["size"] == 8
		# And `see` still works afterwards -- nothing was consumed.
		assert len(store.see("acme.implementer")) == 1


def test_marking_seen_is_explicit_and_idempotent(inst):
	path, _ = inst
	with core.open_instance(path) as store:
		nid = store.send_notice("hq.lead", kind="announcement", body=b"x\n")
		first = store.mark_notice_seen("acme.implementer", nid)
		assert first["seen_ts"] is not None
		assert first["already_seen"] is False
		# Content arrives through this door once, with the receipt.
		assert first["parts"][0]["body"] == b"x\n"
		# A repeat is harmless -- a console redraws -- but must NOT redeliver.
		# Returning content again would make broadcast repeatable for anyone
		# who kept asking, which is exactly what the receipt exists to prevent.
		again = store.mark_notice_seen("acme.implementer", nid)
		assert again["seen_ts"] == first["seen_ts"]
		assert again["already_seen"] is True
		assert_no_delivery_content(again, "already-seen result")
		assert store.conn.execute(
			"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 1
		assert store.list_notices("acme.implementer") == []
		# Per participant, not global: the other participant still sees it.
		assert len(store.list_notices("acme.reviewer")) == 1


def test_marking_seen_refuses_unknown_and_expired(inst, monkeypatch):
	path, _ = inst
	with core.open_instance(path) as store:
		with pytest.raises(core.BatonError) as excinfo:
			store.mark_notice_seen("acme.implementer", "0" * 32)
		assert excinfo.value.exit_code == core.EXIT_NONE
		nid = store.send_notice("hq.lead", kind="a", body=b"x\n", ttl_seconds=1)
		# Advance the clock rather than rewriting the row: notices are
		# immutable, which is the guard doing its job.
		monkeypatch.setattr(core._impl, "_utc_now_iso", lambda: "2099-01-01T00:00:00Z")
		with pytest.raises(core.BatonError, match="expired"):
			store.mark_notice_seen("acme.implementer", nid)
		# An expired notice also drops out of the read-only listing.
		assert store.list_notices("acme.implementer") == []


def test_scanning_the_inbox_creates_no_claim(inst):
	"""The cursor-never-claims rule, at the API level."""
	path, _ = inst
	with core.open_instance(path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
				subject="Choose me", body=b"body\n")
		for _ in range(25):
			scan = store.scan("acme.implementer")
			assert len(scan["pending"]) == 1
			assert scan["pending"][0]["subject"] == "Choose me"
		assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0


# -- reopen ----------------------------------------------------------------

def test_reopen_returns_the_delivery_without_a_second_claim(inst):
	"""A console cannot hold the only readable copy in process memory."""
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Needs an answer", body=b"# Ask\n")
		claim = store.claim("acme.implementer", message_id=mid)
		before = store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
		ledger = store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
	# Fresh process, nothing in memory.
	with core.open_instance(path) as store:
		again = store.reopen_claim(claim["claim_id"], "acme.implementer")
		assert again["damaged"] is None
		assert again["message"]["subject"] == "Needs an answer"
		assert again["message"]["content"]["parts"][0]["text"] == "# Ask\n"
		assert again["claim"]["claim_id"] == claim["claim_id"]
		assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == before
		assert store.conn.execute(
			"SELECT COUNT(*) FROM transitions").fetchone()[0] == ledger
		# And the claim can still be finished normally.
		assert store.reply(claim["claim_id"], participant="acme.implementer",
		                   kind="a", body=b"done\n")["already_committed"] is False


def test_reopen_enforces_ownership(inst):
	"""`get_claim` has no ownership check, because every disposition path
	re-validates before acting. Reopen returns CONTENT, so it is the first
	read path where the check has to exist."""
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"secret\n")
		claim = store.claim("acme.implementer", message_id=mid)
		with pytest.raises(core.BatonError, match="belongs to"):
			store.reopen_claim(claim["claim_id"], "acme.reviewer")
		# The rightful owner still succeeds, so the refusal is a permission
		# check and not a broken lookup.
		assert store.reopen_claim(claim["claim_id"], "acme.implementer")["damaged"] is None


def test_reopen_revalidates_external_pins_and_leaves_a_way_out(inst):
	"""Re-reading stored parts does not re-verify a pinned file. Without this,
	a pin broken since the claim is handed back as though still good."""
	path, root = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="ev",
		                 subject="Evidence attached", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"see attached\n"},
			{"content_type": "text/markdown; charset=utf-8", "disposition": "attachment",
			 "attach": "src:EVIDENCE.md"},
		])
		claim = store.claim("acme.implementer", message_id=mid)
	(root / "EVIDENCE.md").write_bytes(b"MUTATED AFTER THE CLAIM\n")
	with core.open_instance(path) as store:
		result = store.reopen_claim(claim["claim_id"], "acme.implementer")
		# Fails closed on CONTENT...
		assert result["content"] is None
		assert "pinned hash" in result["damaged"]
		# ...but the holder can still see what they hold, and how to get out.
		assert result["message"]["subject"] == "Evidence attached"
		assert "close" in result["disposition_path"]
		# The stated exit actually works: quarantine is refused while claimed,
		# close is not.
		with pytest.raises(core.BatonError) as excinfo:
			store.quarantine_attachment(mid, participant="hq.lead", reason="stale")
		assert excinfo.value.exit_code == core.EXIT_RACE
		store.close_claim(claim["claim_id"], participant="acme.implementer")
		assert store.quarantine_attachment(
			mid, participant="hq.lead", reason="stale")["state"] == "closed"


def test_reopen_refuses_a_finished_claim(inst):
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		claim = store.claim("acme.implementer", message_id=mid)
		store.close_claim(claim["claim_id"], participant="acme.implementer")
		with pytest.raises(core.BatonError, match="not active"):
			store.reopen_claim(claim["claim_id"], "acme.implementer")


def test_core_declares_its_api_contract():
	versions = core.core_versions()
	# EXACTLY 3. `>= 1` encoded the superseded compatibility rule: protocol 10
	# removed `filename` from every delivery and every Store signature, so
	# "at least" is the wrong shape for a contract that can break by removal.
	#
	# 3 as of 1.1: `save_message` is new public surface, and the ruled rule is
	# that ADDITIVE growth bumps it too -- `check_core_compatibility` demands
	# equality, so a console asking for 2 must not silently accept a core that
	# is no longer the one it was tested against.
	#
	# 4 as of 1.2, by the same rule and for a sharper reason: `mailbox_identity`
	# and `check_mailbox_identity` are surface the applications CALL at
	# startup, so a 1.2 console against an API-3 core would not fail a version
	# check -- it would raise `AttributeError` before drawing anything.
	assert versions["core_api_version"] == 4
	assert versions["protocol_version"] == 10
	# The core's own package version travels with the contract now. There is no
	# `tool_version`: it answered for a shared release version that no longer
	# exists, and "which of the three did you mean" is worse than its absence.
	assert versions["core_version"] == core.CORE_VERSION
	assert "tool_version" not in versions


def test_message_preview_is_read_only_and_contentless(inst):
	"""Directed preview: the cursor lands on a row and the detail pane shows
	what it IS, not what it says. Reading the text is the separate explicit
	claim-and-open action that starts the reply/close obligation."""
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Decide on rollout", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"# Secret\n"},
			{"content_type": "text/markdown; charset=utf-8", "disposition": "attachment",
			 "part_name": "EVIDENCE.md", "attach": "src:EVIDENCE.md"},
		])
		for _ in range(25):
			preview = store.preview_message(mid, "acme.implementer")
		assert preview["subject"] == "Decide on rollout"
		assert preview["state"] == "pending"
		# Shape is visible: two parts, one an external attachment.
		assert [p["storage"] for p in preview["parts"]] == ["inline", "external"]
		assert preview["parts"][1]["disposition"] == "attachment"
		assert preview["parts"][1]["part_name"] == "EVIDENCE.md"
		# Content, hashes and the on-disk location of evidence are not.
		assert_no_delivery_content(preview)
		assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0


def test_message_preview_refuses_another_participants_mail(inst):
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		with pytest.raises(core.BatonError, match="addressed to"):
			store.preview_message(mid, "acme.reviewer")


class _ContentsReadWatch:
	"""Fails if the connection READS the `contents` table.

	Output-key exclusion cannot catch read amplification: stripping bytes
	after loading them still loads them. A SQLite authorizer sees the actual
	access, so this asserts the cheap path rather than the tidy result."""

	def __init__(self, conn):
		self.conn = conn
		self.reads = []

	def __enter__(self):
		def authorizer(action, arg1, arg2, dbname, source):
			if action == 20 and arg1 == "contents":   # SQLITE_READ
				self.reads.append(arg2)
			return 0                                   # SQLITE_OK
		self.conn.set_authorizer(authorizer)
		return self

	def __exit__(self, *exc):
		self.conn.set_authorizer(None)
		return False


def test_preview_never_reads_the_contents_table(inst):
	"""A 10 MB part must cost a preview nothing. Building metadata from the
	`parts` rows and stripping content after a full read look identical in the
	output and are not remotely the same operation."""
	path, _ = inst
	big = b"x" * (10 * 1024 * 1024)
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Large", parts=[
			{"content_type": "text/plain; charset=utf-8", "body": b"small\n"},
			{"content_type": "multipart/alternative", "parts": [
				{"content_type": "application/octet-stream", "body": big},
			]},
		])
		nid = store.send_notice("hq.lead", kind="a", subject="Broadcast", body=b"n\n")
		with _ContentsReadWatch(store.conn) as watch:
			for _ in range(10):
				preview = store.preview_message(mid, "acme.implementer")
				listed = store.list_notices("acme.implementer")
			assert watch.reads == [], f"preview read contents: {sorted(set(watch.reads))}"
		# Nesting, order and sizes survive the cheap path.
		assert [p["address"] for p in preview["parts"]] == ["0", "1"]
		assert preview["parts"][1]["parts"][0]["address"] == "1.0"
		assert preview["parts"][1]["parts"][0]["size"] == len(big)
		assert listed[0]["subject"] == "Broadcast"
		assert_no_delivery_content(preview)
		assert_no_delivery_content(listed)
		assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
		assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
		# The real open still reads content -- proving the watch works at all.
		with _ContentsReadWatch(store.conn) as watch:
			store.mark_notice_seen("acme.implementer", nid)
			assert watch.reads, "the delivering path should read contents"


def test_the_participant_registry_is_read_only_and_deterministic(inst):
	"""Added for the console's recipient picker: choosing an address beats
	typing one, because a typo is only caught at send time and costs the human
	their composed message."""
	path, _ = inst
	with core.open_instance(path) as store:
		first = store.list_participants()
		assert [entry["address"] for entry in first] == sorted(
			entry["address"] for entry in first)
		assert {entry["address"] for entry in first} == {
			"acme.reviewer", "acme.implementer", "hq.lead"}
		# Capabilities are exposed so a console can label them; the registry
		# itself grants nothing.
		lead = [e for e in first if e["address"] == "hq.lead"][0]
		assert "recovery" in lead["capabilities"]
		# Read-only: repeated calls change nothing anywhere.
		for _ in range(20):
			assert store.list_participants() == first
		for table in ("claims", "notice_seen", "dispositions", "messages"):
			assert store.conn.execute(
				f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


# -- SENT: a read-only outbound view, owner-checked and pin-revalidated ----

def test_list_sent_takes_no_write_lock(inst):
	"""It must be callable while holding a claim, and must never be able to
	move anything. A view that needs the write lock is a view that can block
	the queue."""
	path, _ = inst
	with core.open_instance(path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q", subject="in",
		           body=b"x\n")
		assert store.claim("acme.implementer") is not None
		assert store.list_sent("acme.reviewer") is not None      # still held


def test_open_sent_refuses_a_message_this_participant_did_not_send(inst):
	path, _ = inst
	with core.open_instance(path) as store:
		other = store.send("acme.reviewer", "acme.implementer", kind="q",
		                   subject="theirs", body=b"x\n")
		with pytest.raises(core.BatonError):
			store.open_sent(other, "acme.implementer")
		with pytest.raises(core.BatonError):
			store.open_sent(other, "hq.lead")


def test_open_sent_fails_closed_on_a_stale_external_pin(inst):
	"""The SENDER is the last person who should be shown bytes that no longer
	match what the recipient will get. A pin that has gone stale fails closed
	rather than handing back whatever is at that path now."""
	path, root = inst
	with core.open_instance(path) as store:
		message = store.send("acme.reviewer", "acme.implementer", kind="q",
		                     subject="pinned", parts=[
			{"content_type": "text/plain; charset=utf-8", "body": b"note\n"},
			{"disposition": "attachment", "attach": "src:EVIDENCE.md"},
		])
		assert store.open_sent(message, "acme.reviewer")["sent"]["content"]
		(root / "EVIDENCE.md").write_bytes(b"tampered\n")
		with pytest.raises(core.BatonError):
			store.open_sent(message, "acme.reviewer")


def test_open_sent_notice_commits_no_receipt(inst):
	"""A receipt records that a RECIPIENT read a broadcast. The author reading
	their own is not that, and writing one would corrupt the delivery count
	they are looking at."""
	path, _ = inst
	with core.open_instance(path) as store:
		notice = store.send_notice("acme.reviewer", kind="announcement",
		                           subject="bcast", body=b"x\n")
		before = store.conn.execute(
			"SELECT COUNT(*) FROM notice_seen").fetchone()[0]
		store.open_sent_notice(notice, "acme.reviewer")
		assert store.conn.execute(
			"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == before


def test_list_sent_is_newest_first_by_a_total_order(inst):
	"""Newest-first, with the id as the tiebreak so the order is TOTAL.

	Deliberately not asserted against `scan`'s pending order: that orders by
	`created_ts` alone, so two messages sent inside the same second come back
	in whatever order SQLite happens to produce. Comparing against it would
	make this test pass or fail on timing. The property worth pinning is that
	`list_sent` itself is deterministic and descending."""
	path, _ = inst
	with core.open_instance(path) as store:
		ids = [store.send("acme.reviewer", "acme.implementer", kind="q",
		                  subject=f"m{index}", body=b"x\n") for index in range(5)]
		rows = [row for row in store.list_sent("acme.reviewer")
		        if row["row_kind"] == "message"]
		keys = [(row["created_ts"], row["id"]) for row in rows]
		assert keys == sorted(keys, reverse=True)
		assert {row["id"] for row in rows} == set(ids)


def test_naming_the_message_defeats_the_same_second_ordering_limit(inst):
	"""Why the same-second ordering limit is not a delivery defect, pinned.

	`(created_ts, id)` is deterministic but not chronological inside one
	second, and protocol 10 keeps that rule (protocol 11 replaces it with a
	persisted publication sequence). The reason it is safe to keep is the
	standing pattern: `wait` then `claim --message-id`. So the property that
	must hold is that NAMING a message always yields that message, whatever
	the tie-break did to the listing -- and that every item is claimable
	exactly once, so nothing is lost or duplicated by the ambiguity.
	"""
	path, _ = inst
	with core.open_instance(path) as store:
		ids = [store.send("acme.reviewer", "acme.implementer", kind="q",
		                  subject=f"same-second {index}", body=b"x\n")
		       for index in range(5)]
		stamps = {row["created_ts"] for row in store.list_sent("acme.reviewer")
		          if row["row_kind"] == "message"}
		assert len(stamps) == 1, \
			f"this test needs one timestamp second to be meaningful: {stamps}"

		# Named, in an order deliberately unrelated to any listing.
		for wanted in reversed(ids):
			claimed = store.claim("acme.implementer", message_id=wanted)
			assert claimed["message_id"] == wanted, claimed
			store.close_claim(claimed["claim_id"],
			                  participant="acme.implementer",
			                  outcome="acknowledged")

		# Exactly once each, and nothing left behind.
		assert store.scan("acme.implementer") == {"claimed": [], "damaged": [],
		                                          "pending": []}


# -- notice ACTIVITY: history, with the same content discipline ------------

def test_notice_activity_never_exposes_delivery_content(inst):
	"""The strongest thing this API claims, pinned AT THE CORE BOUNDARY.

	The console's tests consume it and would still pass if a future
	implementation leaked `body`, `text`, `base64`, an attachment path or
	manifest data -- they never look. Swept structurally, over BOTH an unseen
	row and a seen one, because the seen path is the one that has a receipt
	to be tempted by."""
	path, _ = inst
	with core.open_instance(path) as store:
		first = store.send_notice("hq.lead", kind="announcement",
		                          subject="All hands", body=b"the details\n")
		store.send_notice("hq.lead", kind="announcement",
		                  subject="Second", body=b"more details\n")
		unseen = store.list_notice_activity("acme.implementer")
		assert_no_delivery_content(unseen, "list_notice_activity(unseen)")
		store.mark_notice_seen("acme.implementer", first)
		mixed = store.list_notice_activity("acme.implementer")
		assert_no_delivery_content(mixed, "list_notice_activity(seen)")
		# Belt as well as braces: the bytes themselves are not in there.
		assert b"the details" not in json.dumps(mixed, default=str).encode()


def test_notice_activity_keeps_both_rows_after_one_is_seen(inst):
	"""The whole reason it exists. `list_notices` drops a notice the moment it
	is seen, which made a human watch an announcement disappear while they
	were reading it."""
	path, _ = inst
	with core.open_instance(path) as store:
		first = store.send_notice("hq.lead", kind="announcement",
		                          subject="One", body=b"a\n")
		second = store.send_notice("hq.lead", kind="announcement",
		                           subject="Two", body=b"b\n")
		store.mark_notice_seen("acme.implementer", first)
		rows = {row["id"]: row for row in
		        store.list_notice_activity("acme.implementer")}
		assert set(rows) == {first, second}
		assert rows[first]["seen_ts"] is not None
		assert rows[second]["seen_ts"] is None
		# ...and `list_notices` is UNCHANGED: still unseen-only, for its
		# existing at-most-once consumers.
		assert [row["id"] for row in store.list_notices("acme.implementer")] == [second]


def test_notice_activity_is_per_participant(inst):
	"""One receipt per participant, and neither can see the other's. Reading
	the wrong side of the join would report someone else's state as yours."""
	path, _ = inst
	with core.open_instance(path) as store:
		notice_id = store.send_notice("hq.lead", kind="announcement",
		                              subject="Shared", body=b"x\n")
		store.mark_notice_seen("acme.implementer", notice_id)
		mine = store.list_notice_activity("acme.implementer")[0]
		theirs = store.list_notice_activity("acme.reviewer")[0]
		assert mine["seen_ts"] is not None
		assert theirs["seen_ts"] is None
		assert mine["id"] == theirs["id"]


def test_listing_notice_activity_writes_nothing(inst):
	"""Read-only, repeatedly. A LEFT JOIN that took a write lock would turn
	the console's two-second poll into a contention source."""
	path, _ = inst
	with core.open_instance(path) as store:
		store.send_notice("hq.lead", kind="announcement", subject="S", body=b"x\n")
		before = _authority_counts(store)
		for _ in range(5):
			store.list_notice_activity("acme.implementer")
		assert _authority_counts(store) == before


def test_notice_activity_omits_expired_notices(inst):
	"""TTL, `expire` and gc remain the ONLY reasons a history row goes away."""
	path, _ = inst
	with core.open_instance(path) as store:
		notice_id = store.send_notice("hq.lead", kind="announcement",
		                              subject="Brief", body=b"x\n", ttl_seconds=1)
		assert [row["id"] for row in
		        store.list_notice_activity("acme.implementer")] == [notice_id]
		store.expire("hq.lead", notice_id=notice_id)
		assert store.list_notice_activity("acme.implementer") == []


class TestAuthorizedMaterialize:
	"""`Store.materialize_authorized_part` — the reread path, shared.

	Extracted from the module-level entry point so the agent CLI and the human
	console resolve, authorize and name a projection identically. They had
	drifted: the console could only reach messages it held an ACTIVE claim on,
	so a human could not save their own answered mail while the CLI could.
	"""

	def test_it_reaches_messages_and_seen_notices(self, inst, tmp_path):
		path, _root = inst
		with core.open_instance(path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 subject="Answered", body=b"message bytes\n")
			nid = store.send_notice("acme.reviewer", kind="ann",
			                        subject="Broadcast", body=b"notice bytes\n")
			# A notice is unreadable until SEEN: `see` remains the only way to
			# receive one, and this is only the way back to one.
			with pytest.raises(core.BatonError):
				store.materialize_authorized_part(nid, "acme.implementer",
				                                  str(tmp_path))
			store.see("acme.implementer")

			out = store.materialize_authorized_part(mid, "acme.implementer",
			                                        str(tmp_path))
			assert __import__('pathlib').Path(out).read_bytes() == b"message bytes\n"
			out = store.materialize_authorized_part(nid, "acme.implementer",
			                                        str(tmp_path))
			assert __import__('pathlib').Path(out).read_bytes() == b"notice bytes\n"

	def test_no_claim_is_required_and_none_is_created(self, inst, tmp_path):
		"""The defect this closes: answering a message ended the claim and with
		it the ability to save what had just been read."""
		path, _root = inst
		with core.open_instance(path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 subject="Answered", body=b"body\n")
			claim = store.claim("acme.implementer", message_id=mid)
			store.close_claim(claim["claim_id"], participant="acme.implementer",
			                  outcome="done")
		before = core.dump(path)
		path, _root = inst
		with core.open_instance(path) as store:
			assert store.materialize_authorized_part(
				mid, "acme.implementer", str(tmp_path))
		assert core.dump(path) == before, "reading back wrote to the authority"

	def test_authorization_is_unchanged(self, inst, tmp_path):
		"""Sender or frozen audience, and nobody else. The refusal must not
		distinguish 'not yours' from 'no such id', or the surface becomes an
		enumeration oracle."""
		path, _root = inst
		with core.open_instance(path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 subject="Private", body=b"body\n")
			assert store.materialize_authorized_part(mid, "acme.reviewer",
			                                         str(tmp_path))       # sender
			with pytest.raises(core.BatonError) as refused:
				store.materialize_authorized_part(mid, "hq.lead", str(tmp_path))
			with pytest.raises(core.BatonError) as absent:
				store.materialize_authorized_part("0" * 32, "hq.lead", str(tmp_path))
			# Identical APART FROM THE ID each one names, which is the property:
			# a non-party learns nothing about whether the id exists or which
			# kind it is.
			assert str(refused.value).replace(mid, "ID") == \
				str(absent.value).replace("0" * 32, "ID")

	def test_retention_is_unchanged(self, inst, tmp_path):
		"""The sender chose transient; a durable copy would defeat that choice,
		and widening WHO may save must not widen WHAT may be saved."""
		path, _root = inst
		with core.open_instance(path) as store:
			mid = store.send("acme.reviewer", "acme.implementer", kind="q",
			                 subject="Fleeting", body=b"gone soon\n",
			                 retention="transient")
			# A dedicated directory: `tmp_path` already holds the instance the
			# fixture built, so asserting IT is empty would assert nothing.
			target = tmp_path / "projection"
			target.mkdir()
			with pytest.raises(core.BatonError) as excinfo:
				store.materialize_authorized_part(mid, "acme.reviewer", str(target))
			assert "transient" in str(excinfo.value)
			assert list(target.iterdir()) == []
