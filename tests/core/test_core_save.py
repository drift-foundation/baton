# Whole-message save: the core operation and the `save` subcommand.
#
# `materialize` answers "give me this leaf's bytes as a file". This answers the
# other question a human actually asks — "keep this message" — and the two are
# different enough that most of what is worth testing here is what the saved
# file DOES NOT contain, and what the operation refuses.

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import pytest

import baton_core as core

from test_core_api import make_config


@pytest.fixture
def inst(tmp_path):
	path, root = make_config(tmp_path)
	return path, root


def read_saved(path):
	with open(path, "rb") as handle:
		return handle.read()


def load_saved(path):
	return json.loads(read_saved(path).decode("utf-8"))


# -- the document shape ----------------------------------------------------

def test_a_saved_message_is_the_immutable_envelope_and_nothing_else(inst, tmp_path):
	"""The whole point of the export: it describes the MESSAGE, not the
	reader's relationship to it."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Needs an answer", body=b"# Ask\n")
		store.claim("acme.implementer", message_id=mid)
	assert core.save_message(path, mid, out, participant="acme.implementer") == out

	document = load_saved(out)
	assert document["format"] == "baton.whole-message"
	assert document["version"] == 1
	assert "notice" not in document
	message = document["message"]
	assert set(message) == {
		"id", "from_participant", "to_participant", "kind", "subject",
		"thread_id", "retention", "outcome", "created_ts", "responds_to",
		"audience", "possible_duplicate", "content"}
	assert message["id"] == mid
	assert message["subject"] == "Needs an answer"
	assert message["audience"] == ["acme.implementer"]
	assert message["possible_duplicate"] is False
	assert message["content"]["parts"][0]["text"] == "# Ask\n"


def test_the_saved_document_carries_no_reader_or_process_state(inst, tmp_path):
	"""Everything absent here is absent ON PURPOSE. A saved message that
	recorded who saved it and when would differ on every save, and the
	no-clobber publication would then report a second save as corruption."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")
	message = load_saved(out)["message"]
	for absent in ("state", "claim", "claim_id", "seen_ts", "completed_ts",
	               "saved_by", "saved_ts", "output_path", "participant",
	               "publication_id"):
		assert absent not in message, f"{absent} leaked into the export"


def test_the_same_message_saves_identically_across_a_lifecycle_change(inst, tmp_path):
	"""Determinism is what makes the second save a RESUME rather than a
	conflict. If any mutable field were exported, answering the message
	between two saves would make the second one fail."""
	path, _ = inst
	first = str(tmp_path / "first.baton.json")
	second = str(tmp_path / "second.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		claim = store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, first, participant="acme.implementer")
	with core.open_instance(path) as store:
		store.reply(claim["claim_id"], participant="acme.implementer",
		            kind="a", body=b"done\n")
	core.save_message(path, mid, second, participant="acme.implementer")
	assert read_saved(first) == read_saved(second)
	# And re-saving over the first file is accepted as the same bytes.
	core.save_message(path, mid, first, participant="acme.implementer")
	assert read_saved(first) == read_saved(second)


def test_the_serialization_is_canonical(inst, tmp_path):
	"""Sorted keys, two-space indent, UTF-8, one final newline — stated in
	the contract because two saves must agree byte for byte."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Ünïcøde", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")
	data = read_saved(out)
	assert data.endswith(b"\n") and not data.endswith(b"\n\n")
	text = data.decode("utf-8")
	assert "Ünïcøde" in text, "non-ASCII was escaped rather than written"
	assert text == json.dumps(json.loads(text), ensure_ascii=False,
	                          sort_keys=True, indent=2) + "\n"


def test_a_subject_only_message_saves_with_null_content(inst, tmp_path):
	"""`materialize` refuses a contentless owner because there is no leaf to
	project. An EXPORT of the same message is meaningful — its subject IS the
	message — so it records the absence instead of refusing.

	`null`, not the empty `multipart/mixed` container storage keeps: that
	container is Baton's internal sentinel for "no content" (`content_type`
	is NOT NULL on both owner tables, so there is nowhere else for the absence
	to live), and the v1 export says it in JSON's own vocabulary. The
	narrowness matters — see the delivery-comparison test next door, which
	pins that an owner WITH parts is emitted untranslated."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="No body at all")
		claim = store.claim("acme.implementer", message_id=mid)
		# The sentinel this exists to translate: storage does hold a
		# container, and the export deliberately does not carry it.
		delivered = core.delivery_for(store, claim)["message"]["content"]
		assert delivered["parts"] == [] and delivered["content_type"]
	core.save_message(path, mid, out, participant="acme.implementer")
	message = load_saved(out)["message"]
	assert message["subject"] == "No body at all"
	assert message["content"] is None


def test_the_saved_content_is_the_delivered_content_exactly(inst, tmp_path):
	"""The whole representation, byte for byte against the delivery path —
	nested containers, dispositions, part names and all. One representation,
	so a tool that reads a delivery reads an export."""
	path, root = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="ev",
		                 subject="Nested", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"lead\n",
			 "part_name": "summary"},
			{"content_type": "multipart/mixed", "parts": [
				{"content_type": "text/plain; charset=utf-8", "body": b"nested one\n",
				 "part_name": "detail"},
				{"content_type": "application/octet-stream", "body": b"\x00\x01\x02",
				 "disposition": "attachment", "part_name": "blob.bin"},
			]},
			{"content_type": "text/markdown; charset=utf-8",
			 "disposition": "attachment", "attach": "src:EVIDENCE.md"},
		])
		claim = store.claim("acme.implementer", message_id=mid)
		delivered = core.delivery_for(store, claim)["message"]["content"]
	core.save_message(path, mid, out, participant="acme.implementer")
	saved = load_saved(out)["message"]["content"]
	assert saved == delivered

	# And spelled out, so a silent change to BOTH sides cannot pass.
	assert [part["part_name"] for part in saved["parts"]] == \
		["summary", None, None]
	inner = saved["parts"][1]["parts"]
	assert [part["part_name"] for part in inner] == ["detail", "blob.bin"]
	assert [part["disposition"] for part in inner] == ["inline", "attachment"]
	assert [part["address"] for part in inner] == ["1.0", "1.1"]
	assert saved["parts"][2]["disposition"] == "attachment"


def test_a_saved_notice_records_how_it_was_addressed_not_who_it_reached(inst, tmp_path):
	"""The ruled v1 envelope: `audience_kind` and `selector`, no expanded
	list.

	NOT because the list is unstable — `notice_audience` is expanded and
	frozen transactionally at publication, exactly as a directed message's
	`publications` audience is, so a saved list would be accurate. The ruling
	is that the selector is what the sender wrote and what identifies the
	broadcast, and the v1 export carries what was authored."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		nid = store.send_notice("hq.lead", kind="ann", subject="Downtime",
		                        body=b"tonight\n", ttl_seconds=3600,
		                        scope="acme.*")
		store.mark_notice_seen("acme.implementer", nid)
	core.save_message(path, nid, out, participant="acme.implementer")

	document = load_saved(out)
	assert "message" not in document
	notice = document["notice"]
	assert set(notice) == {
		"id", "from_participant", "kind", "subject", "created_ts",
		"ttl_seconds", "audience_kind", "selector", "possible_duplicate",
		"content"}
	assert notice["audience_kind"] == "scope"
	assert notice["selector"] == "acme.*"
	assert notice["content"]["parts"][0]["text"] == "tonight\n"
	assert "seen_ts" not in notice
	# The frozen list EXISTS in the authority; the export deliberately omits
	# it, which is a ruling and not a limitation.
	frozen = [row for row in core.dump(path)["notice_audience"]
	          if row["notice_id"] == nid]
	assert frozen, "the authority did freeze an audience at publication"
	assert "audience" not in notice


def test_a_multipart_message_saves_its_parts_in_order(inst, tmp_path):
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"first\n"},
			{"content_type": "text/markdown; charset=utf-8", "body": b"second\n"},
		])
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")
	parts = load_saved(out)["message"]["content"]["parts"]
	assert [part["text"] for part in parts] == ["first\n", "second\n"]


# -- external parts --------------------------------------------------------

def test_an_external_part_is_saved_as_a_reference_not_a_copy(inst, tmp_path):
	"""The export names the pinned file; it never inlines its bytes. A pinned
	root is the sender's evidence, and copying it into an export would make a
	second uncontrolled copy of something deliberately kept out of the store."""
	path, root = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="ev", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"see attached\n"},
			{"content_type": "text/markdown; charset=utf-8",
			 "disposition": "attachment", "attach": "src:EVIDENCE.md"},
		])
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")

	external = load_saved(out)["message"]["content"]["parts"][1]
	assert external["storage"] == "external"
	# EVERY field of the pin, not just the ones that are easy to assert: a
	# reference missing its binding generation names a file without saying
	# which acceptance of the root it was pinned under.
	pinned = (root / "EVIDENCE.md").read_bytes()
	assert external["attachment"] == {
		"root_id": "src", "path": "EVIDENCE.md",
		"generation": external["attachment"]["generation"]}
	assert isinstance(external["attachment"]["generation"], int)
	assert external["size"] == len(pinned)
	assert external["sha256"] == hashlib.sha256(pinned).hexdigest()
	assert external["encoding"] is None
	assert "text" not in external and "base64" not in external
	assert b"pinned evidence" not in read_saved(out)
	# The pin agrees with the delivery path's, field for field. The claim
	# already exists, so this REOPENS it rather than taking a second.
	with core.open_instance(path) as store:
		claim_id = store.conn.execute(
			"SELECT claim_id FROM claims WHERE message_id=?", (mid,)).fetchone()[0]
		delivered = store.reopen_claim(claim_id, "acme.implementer")["message"]
	assert external == delivered["content"]["parts"][1]


def test_saving_refuses_a_message_whose_pin_has_moved_and_writes_nothing(inst, tmp_path):
	"""Fails CLOSED. An export presenting itself as an intact message while
	one of its references no longer resolves is the export lying about
	itself."""
	path, root = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="ev", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"see attached\n"},
			{"content_type": "text/markdown; charset=utf-8",
			 "disposition": "attachment", "attach": "src:EVIDENCE.md"},
		])
		store.claim("acme.implementer", message_id=mid)
	(root / "EVIDENCE.md").write_bytes(b"tampered\n")
	with pytest.raises(core.BatonError):
		core.save_message(path, mid, out, participant="acme.implementer")
	assert not os.path.exists(out), "a refusal left a file behind"


# -- authorization and retention -------------------------------------------

def test_saving_refuses_a_non_party_indistinguishably_from_an_unknown_id(inst, tmp_path):
	"""One refusal for every failure. Two different messages would tell a
	non-party that an id exists, and which kind it is."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"secret\n")
	with pytest.raises(core.BatonError) as denied:
		core.save_message(path, mid, out, participant="hq.lead")
	with pytest.raises(core.BatonError) as missing:
		core.save_message(path, "no-such-id", out, participant="hq.lead")
	assert str(denied.value).replace(mid, "ID") == \
		str(missing.value).replace("no-such-id", "ID")
	assert not os.path.exists(out)


def test_an_unseen_notice_refuses_exactly_as_an_unknown_id_does(inst, tmp_path):
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		nid = store.send_notice("hq.lead", kind="ann", body=b"x\n",
		                        ttl_seconds=3600)
	with pytest.raises(core.BatonError, match="unknown id"):
		core.save_message(path, nid, out, participant="acme.implementer")
	assert not os.path.exists(out)
	# And it saves once seen, so the refusal was the boundary and not a
	# broken lookup.
	with core.open_instance(path) as store:
		store.mark_notice_seen("acme.implementer", nid)
	core.save_message(path, nid, out, participant="acme.implementer")
	assert load_saved(out)["notice"]["id"] == nid


def test_the_sender_may_save_their_own_message(inst, tmp_path):
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
	core.save_message(path, mid, out, participant="acme.reviewer")
	assert load_saved(out)["message"]["from_participant"] == "acme.reviewer"


def test_saving_refuses_a_transient_message_before_touching_the_destination(inst, tmp_path):
	"""A durable copy of a transient message defeats the contract its sender
	chose — and the refusal must land before the output directory is even
	opened, so a refusal never leaves scratch behind."""
	path, _ = inst
	out = str(tmp_path / "nonexistent-dir" / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 body=b"ephemeral\n", retention="transient")
		store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError, match="transient"):
		core.save_message(path, mid, out, participant="acme.implementer")


def test_a_transient_message_is_refused_at_every_lifecycle_shape(inst, tmp_path):
	"""Pending, claimed, answered and scrubbed alike. Retention is a property
	of the MESSAGE, not of where it has got to, and a refusal that held only
	while the bytes were still there would let the empty husk save."""
	path, _ = inst
	with core.open_instance(path) as store:
		shapes = {}
		for name in ("pending", "claimed", "answered"):
			shapes[name] = store.send(
				"acme.reviewer", "acme.implementer", kind="q",
				subject=f"transient {name}", body=b"ephemeral\n",
				retention="transient")
		claim = store.claim("acme.implementer", message_id=shapes["claimed"])
		answered = store.claim("acme.implementer", message_id=shapes["answered"])
		store.reply(answered["claim_id"], participant="acme.implementer",
		            kind="a", body=b"done\n")
	# The answered one has been scrubbed by the reply, which is exactly the
	# husk a retention-blind check would have exported.
	assert claim is not None
	for name, mid in shapes.items():
		out = str(tmp_path / f"{name}.baton.json")
		with pytest.raises(core.BatonError, match="transient"):
			core.save_message(path, mid, out, participant="acme.implementer")
		assert not os.path.exists(out), name
		# And the sender is refused too: retention is the sender's own
		# contract, not a permission the recipient lacks.
		with pytest.raises(core.BatonError, match="transient"):
			core.save_message(path, mid, out, participant="acme.reviewer")
		assert not os.path.exists(out), name


def test_a_durable_message_saves_at_every_lifecycle_shape(inst, tmp_path):
	"""The other half, so the refusal above is about RETENTION and not about
	the states it happened to be measured in."""
	path, _ = inst
	saved = {}
	with core.open_instance(path) as store:
		shapes = {}
		for name in ("pending", "claimed", "answered", "closed"):
			shapes[name] = store.send("acme.reviewer", "acme.implementer",
			                          kind="q", subject=f"durable {name}",
			                          body=b"kept\n")
		store.claim("acme.implementer", message_id=shapes["claimed"])
		answered = store.claim("acme.implementer", message_id=shapes["answered"])
		store.reply(answered["claim_id"], participant="acme.implementer",
		            kind="a", body=b"done\n")
		closed = store.claim("acme.implementer", message_id=shapes["closed"])
		store.close_claim(closed["claim_id"], participant="acme.implementer",
		                  outcome="done")
	for name, mid in shapes.items():
		out = str(tmp_path / f"{name}.baton.json")
		core.save_message(path, mid, out, participant="acme.implementer")
		document = load_saved(out)["message"]
		assert document["subject"] == f"durable {name}"
		assert document["content"]["parts"][0]["text"] == "kept\n", name
		saved[name] = read_saved(out)
	# Lifecycle leaves no trace in the export. Each document names its own
	# subject and id; with those removed the four are IDENTICAL, which is only
	# true because no state, claim or receipt reached the file.
	def anonymize(name: str, data: bytes) -> bytes:
		document = json.loads(data.decode("utf-8"))["message"]
		for field in ("id", "subject", "created_ts"):
			document.pop(field)
		return json.dumps(document, sort_keys=True).encode("utf-8")
	assert len({anonymize(name, data) for name, data in saved.items()}) == 1


def test_saving_writes_nothing_to_the_authority(inst, tmp_path):
	"""Reading back is not a disposition: no claim, no receipt, no
	transition, no audit record."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	# THE WHOLE DUMP, not selected tables. A read path that wrote to a table
	# nobody thought to count is exactly the thing a count of three tables
	# cannot see.
	before = core.dump(path)
	core.save_message(path, mid, out, participant="acme.implementer")
	assert core.dump(path) == before


def test_the_saved_envelope_agrees_with_the_authority(inst, tmp_path):
	"""Field for field against `dump()`. An export that quietly diverged from
	the store would be worse than no export: it would look authoritative."""
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Compared", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")

	stored = next(row for row in core.dump(path)["messages"] if row["id"] == mid)
	saved = load_saved(out)["message"]
	for field in ("id", "from_participant", "to_participant", "kind", "subject",
	              "thread_id", "retention", "outcome", "created_ts",
	              "responds_to"):
		assert saved[field] == stored[field], field


# -- path safety -----------------------------------------------------------

def test_the_output_path_must_be_absolute_and_canonical(inst, tmp_path):
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	for bad in ("relative/saved.baton.json",
	            f"{tmp_path}/./saved.baton.json",
	            f"{tmp_path}/sub/../saved.baton.json",
	            f"{tmp_path}//saved.baton.json"):
		with pytest.raises(core.BatonError, match="canonical absolute"):
			core.save_message(path, mid, bad, participant="acme.implementer")


def test_a_doubled_ROOT_slash_is_refused_and_writes_nothing(inst, tmp_path):
	"""`//x` SURVIVES `normpath`: POSIX reserves exactly two leading slashes
	as implementation-defined, so the stdlib preserves that spelling and a
	normpath-only check called it canonical. Two canonical names for one
	directory gives a no-clobber destination two places to be written."""
	path, _ = inst
	target = tmp_path / "doubled.baton.json"
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	doubled = "/" + str(target)
	assert doubled == os.path.normpath(doubled), "normpath already collapsed it"
	with pytest.raises(core.BatonError, match="canonical absolute"):
		core.save_message(path, mid, doubled, participant="acme.implementer")
	assert not target.exists()
	# The single-slash spelling of the same path still works, so the refusal
	# is about the doubling and not about the directory.
	core.save_message(path, mid, str(target), participant="acme.implementer")
	assert target.exists()


def test_a_file_appearing_at_the_destination_mid_save_is_not_replaced(inst, tmp_path):
	"""The publication race. `_publish_bytes_at` links no-clobber, so a file
	that appears between the decision and the link is refused rather than
	overwritten — and an EXACT one is accepted as a resume."""
	path, _ = inst
	out = tmp_path / "raced.baton.json"
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="Raced", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)

	real_link = os.link
	def racing_link(src, dst, **kwargs):
		# Someone else wins the pathname while this save is in flight.
		if not os.path.exists(out):
			out.write_bytes(b"another process got here first\n")
		return real_link(src, dst, **kwargs)

	import unittest.mock
	with unittest.mock.patch("os.link", racing_link):
		with pytest.raises(core.BatonError):
			core.save_message(path, mid, str(out), participant="acme.implementer")
	assert out.read_bytes() == b"another process got here first\n"

	# Losing the race is a REFUSAL even when the winner wrote identical bytes:
	# the resume check happens before the scratch file exists, so a file that
	# appears at the link is never inspected. The refusal says "rerun to
	# verify/resume", and rerunning is what resolves it — which is the honest
	# contract, and cheaper than reading back inside the race window.
	out.unlink()
	core.save_message(path, mid, str(out), participant="acme.implementer")
	winner = out.read_bytes()
	out.unlink()
	with unittest.mock.patch("os.link", racing_link_with(winner, real_link, out)):
		with pytest.raises(core.BatonError, match="race"):
			core.save_message(path, mid, str(out), participant="acme.implementer")
	assert out.read_bytes() == winner
	# The rerun the refusal names: no race this time, exact bytes, resume.
	core.save_message(path, mid, str(out), participant="acme.implementer")
	assert out.read_bytes() == winner


def racing_link_with(payload, real_link, target):
	"""A winner that publishes `payload` at `target` inside the race window."""
	def link(src, dst, **kwargs):
		if not os.path.exists(target):
			target.write_bytes(payload)
		return real_link(src, dst, **kwargs)
	return link


def test_the_output_path_must_name_a_file_not_a_directory(inst, tmp_path):
	"""`--output` names the FILE. Naming a directory and having the operation
	pick a filename inside it is exactly the guessing this contract forbids."""
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	# A trailing slash is not canonical, and says "directory" besides.
	with pytest.raises(core.BatonError, match="canonical absolute"):
		core.save_message(path, mid, str(tmp_path) + "/",
		                  participant="acme.implementer")
	# The same path without one is syntactically a filename, and is still
	# refused rather than filled in.
	with pytest.raises(core.BatonError):
		core.save_message(path, mid, str(tmp_path),
		                  participant="acme.implementer")
	assert not any(entry.name.endswith(".baton.json")
	               for entry in tmp_path.iterdir())
	# And the degenerate case that has no filename at all.
	with pytest.raises(core.BatonError, match="must name a file"):
		core.save_message(path, mid, "/", participant="acme.implementer")


def test_a_missing_parent_directory_is_refused_never_created(inst, tmp_path):
	path, _ = inst
	out = str(tmp_path / "absent" / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError):
		core.save_message(path, mid, out, participant="acme.implementer")
	assert not (tmp_path / "absent").exists()


def test_a_symlinked_parent_directory_is_refused(inst, tmp_path):
	"""No ancestor may be a symlink. Following one would write the export
	somewhere the human did not name."""
	path, _ = inst
	real = tmp_path / "real"
	real.mkdir()
	(tmp_path / "link").symlink_to(real, target_is_directory=True)
	out = str(tmp_path / "link" / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError):
		core.save_message(path, mid, out, participant="acme.implementer")
	assert not (real / "saved.baton.json").exists()


def test_a_symlinked_destination_is_refused_rather_than_followed(inst, tmp_path):
	path, _ = inst
	elsewhere = tmp_path / "elsewhere.json"
	out = tmp_path / "saved.baton.json"
	out.symlink_to(elsewhere)
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError, match="symlink"):
		core.save_message(path, mid, str(out), participant="acme.implementer")
	assert not elsewhere.exists()


def test_a_different_existing_file_is_never_overwritten(inst, tmp_path):
	"""No-clobber, with exact-resume as the only exception. Overwriting is
	how a mistyped path destroys something the human cared about."""
	path, _ = inst
	out = tmp_path / "saved.baton.json"
	out.write_bytes(b"something else entirely\n")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError):
		core.save_message(path, mid, str(out), participant="acme.implementer")
	assert out.read_bytes() == b"something else entirely\n"


def test_a_non_regular_destination_is_refused(inst, tmp_path):
	path, _ = inst
	fifo = tmp_path / "saved.baton.json"
	os.mkfifo(fifo)
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError):
		core.save_message(path, mid, str(fifo), participant="acme.implementer")


def test_no_scratch_file_survives_a_successful_save(inst, tmp_path):
	path, _ = inst
	out = tmp_path / "saved.baton.json"
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, str(out), participant="acme.implementer")
	assert sorted(entry.name for entry in tmp_path.iterdir()
	              if entry.is_file()) == ["saved.baton.json"]


# -- large content ---------------------------------------------------------

def test_a_large_body_survives_the_round_trip_intact(inst, tmp_path):
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	body = ("line of text\n" * 40000).encode("utf-8")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=body)
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")
	assert load_saved(out)["message"]["content"]["parts"][0]["text"] == \
		body.decode("utf-8")


def test_binary_content_saves_base64_and_round_trips(inst, tmp_path):
	import base64
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	blob = bytes(range(256)) * 8
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 parts=[{"content_type": "application/octet-stream",
		                         "body": blob}])
		store.claim("acme.implementer", message_id=mid)
	core.save_message(path, mid, out, participant="acme.implementer")
	part = load_saved(out)["message"]["content"]["parts"][0]
	assert "text" not in part
	assert base64.b64decode(part["base64"]) == blob


# -- the CLI ---------------------------------------------------------------

def run_cli(config, *args):
	return subprocess.run(
		[sys.executable, "-c",
		 "import sys, baton_core.cli; sys.exit(baton_core.cli.main(sys.argv[1:]))",
		 "--config", config, *args],
		capture_output=True, text=True,
		env={**os.environ, "PYTHONPATH": os.path.join(os.getcwd(), "src")})


def test_the_cli_saves_and_reports_the_exact_path(inst, tmp_path):
	path, _ = inst
	out = str(tmp_path / "saved.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="From the CLI", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	done = run_cli(path, "save", mid, "--participant", "acme.implementer",
	               "--output", out)
	assert done.returncode == 0, done.stderr
	assert json.loads(done.stdout)["saved"] == out
	assert load_saved(out)["message"]["subject"] == "From the CLI"


def test_the_cli_requires_output(inst):
	path, _ = inst
	done = run_cli(path, "save", "some-id", "--participant", "acme.implementer")
	assert done.returncode != 0
	assert "--output" in done.stderr


def test_the_cli_refuses_a_relative_output_path(inst, tmp_path):
	path, _ = inst
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q", body=b"x\n")
		store.claim("acme.implementer", message_id=mid)
	done = run_cli(path, "save", mid, "--participant", "acme.implementer",
	               "--output", "saved.baton.json")
	assert done.returncode != 0
	assert not os.path.exists("saved.baton.json")


def test_a_candidate_packaged_cli_saves(inst, tmp_path):
	"""The packaged half. A feature that works in the source tree and is not
	in the artifact is a feature that does not exist — the lesson the console
	work paid for twice.

	Built into a THROWAWAY root: the released `bin/baton` is 1.0.0 and is not
	rebuilt by next-generation work.
	"""
	import importlib.util
	repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	spec = importlib.util.spec_from_file_location(
		"build_zipapp", os.path.join(repo, "tools", "build_zipapp.py"))
	builder = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(builder)
	root = tmp_path / "candidate"
	builder.build(str(root))
	artifact = root / "bin" / "baton"
	assert artifact.exists()

	path, _ = inst
	out = str(tmp_path / "packaged.baton.json")
	with core.open_instance(path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="q",
		                 subject="From the artifact", body=b"packaged\n")
		store.claim("acme.implementer", message_id=mid)
	# No PYTHONPATH and no repository on the path: the artifact must carry
	# everything it needs.
	env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
	done = subprocess.run(
		[sys.executable, str(artifact), "--config", path, "save", mid,
		 "--participant", "acme.implementer", "--output", out],
		capture_output=True, text=True, cwd=str(tmp_path), env=env)
	assert done.returncode == 0, done.stderr
	assert json.loads(done.stdout)["saved"] == out
	document = load_saved(out)
	assert document["format"] == "baton.whole-message"
	assert document["message"]["subject"] == "From the artifact"
	assert document["message"]["content"]["parts"][0]["text"] == "packaged\n"
