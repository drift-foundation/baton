#!/usr/bin/env python3
"""Publish the migration guide: one notice, one durable delivery per person.

SEPARATE FROM GENERATING IT, and behind its own human gate. This module exists,
is tested, and is not run by anything: publication is one of the five acts only
Slawomir authorizes, and a publisher that only appears at the moment it is
needed is a publisher nobody has ever seen work.

WHAT IT GUARANTEES, exactly:

- THE SAME BYTES to everyone. The generated body is read once and sent as the
  inline part of the broadcast notice and of every directed delivery. Two
  renderings of "the same" document is how half a team ends up following
  instructions the other half never saw.

- THE AUDIENCE IS THE ACCEPTED ONE, frozen and re-proved. The guide records the
  config digest its audience came from; this refuses unless the authority still
  accepts exactly that config, because a `regen` in between means the frozen
  audience is no longer the audience.

- ONE PUBLICATION, N MESSAGES. The core's `send` takes the whole audience and
  makes one publication of ordinary directed messages, each with its own
  claim and lifecycle. That is the shape the ruling asks for, and it is also
  what makes the durable half either done or not done.

- AT LEAST ONCE, WITHOUT SILENT DUPLICATES. The notice and the publication are
  each recorded the moment they are confirmed, so a retry after a crash sends
  only the half that is missing. You cannot unsend a message, so the honest
  model is resume, never undo.

- A REVIEWABLE RECEIPT. Who was addressed, which message id each delivery got,
  the notice id, the body digest and the config digest, written as the run
  proceeds rather than at the end.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

import migration_guide                                 # noqa: E402  (sibling)


_EXPECTED: tuple = (OSError, UnicodeError)


class PublishError(Exception):
	"""A refusal a human should read, rather than a traceback."""


RECEIPT_FORMAT = "baton.guide-publication"
RECEIPT_FORMAT_VERSION = 2

# What a receipt must agree with before any completed step in it is believed.
# R14: it validated its own format and nothing else, so a receipt from ONE
# publication could mark the notice done for a DIFFERENT body -- half the team
# reading the old bytes and half the new, which is precisely the failure the
# one-body ruling exists to prevent.
IDENTITY = ("guide", "body_sha256", "config_digest", "config_generation",
            "audience", "sender")
FIELDS = IDENTITY + ("format", "format_version", "notice", "publication",
                     "attempting")


class Uncertain(PublishError):
	"""A Baton call may have committed before this process died. Sending again
	is allowed; sending again SILENTLY is not."""


def _read_once(guide_path: str) -> bytes:
	"""The guide's bytes, read ONCE.

	R21: the body was read for hashing and again for sending, so an edit
	between the two left the receipt recording one document while both
	channels carried another. Everything downstream derives from this value.
	"""
	fd = os.open(guide_path, os.O_RDONLY | os.O_NOFOLLOW)
	try:
		chunks = []
		while True:
			chunk = os.read(fd, 1 << 20)
			if not chunk:
				return b"".join(chunks)
			chunks.append(chunk)
	finally:
		os.close(fd)


def _identity(config_path: str, guide_path: str, sender: str,
              body: bytes | None = None) -> dict:
	raw = _read_once(guide_path) if body is None else body
	body_text = raw.decode("utf-8")
	if not body_text.strip():
		raise PublishError(f"{guide_path} is empty")
	try:
		audience, digest, generation = migration_guide._accepted(config_path)
	except migration_guide.GuideError:
		raise
	if digest not in body_text:
		raise PublishError(
			f"{guide_path} does not record the config digest it was generated "
			f"from ({digest[:12]}…). Regenerate it: an audience frozen against "
			f"one config and a body describing another are not one handoff.")
	return {"guide": os.path.abspath(guide_path),
	        "body_sha256": hashlib.sha256(raw).hexdigest(),
	        "config_digest": digest, "config_generation": generation,
	        "audience": audience, "sender": sender}


def _receipt(path: str, identity: dict, home: int | None = None) -> dict:
	"""The receipt for THIS publication, or a refusal.

	A receipt that describes a different body, a different accepted config, a
	different audience or a different sender is not this publication's, and
	inheriting its completed steps would publish two documents under one name.
	"""
	fresh = {"format": RECEIPT_FORMAT, "format_version": RECEIPT_FORMAT_VERSION,
	         "notice": None, "publication": None, "attempting": None, **identity}
	name = os.path.basename(path)
	try:
		fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW,
		             dir_fd=home) if home is not None else os.open(
			path, os.O_RDONLY | os.O_NOFOLLOW)
	except FileNotFoundError:
		return fresh
	except OSError as exc:
		raise PublishError(f"{path} is not a readable receipt "
		                   f"({exc.strerror}); a receipt is a regular file, "
		                   f"never a link") from None
	try:
		with os.fdopen(fd, "r", encoding="utf-8") as handle:
			raw = handle.read()
	except UnicodeDecodeError:
		raise PublishError(f"{path} is not valid UTF-8") from None
	try:
		document = json.loads(raw, object_pairs_hook=_unique_keys)
	except ValueError as broken:
		raise PublishError(f"{path} is not a usable receipt ({broken})") from None
	if not isinstance(document, dict):
		raise PublishError(f"{path} is not a JSON object")
	if document.get("format") != RECEIPT_FORMAT or \
			document.get("format_version") != RECEIPT_FORMAT_VERSION:
		raise PublishError(f"{path} is not a publication receipt this tool "
		                   f"wrote; refusing to resume from it")
	unknown = set(document) - set(FIELDS)
	if unknown:
		raise PublishError(f"{path} carries fields this tool does not write: "
		                   f"{sorted(unknown)}")
	missing = set(FIELDS) - set(document)
	if missing:
		raise PublishError(f"{path} is missing {sorted(missing)}; a receipt "
		                   f"this tool wrote carries all of them")
	# EVERY FIELD'S SHAPE. R21: the loader refused duplicates and unknowns and
	# then believed whatever the known keys held, so `"publication": 123` was
	# accepted as completed work and a missing key became a `KeyError`. A
	# trust document may produce neither.
	_expect(path, document, "guide", str, lambda v: os.path.isabs(v))
	_expect(path, document, "body_sha256", str, _is_sha)
	_expect(path, document, "config_digest", str, _is_sha)
	_expect(path, document, "config_generation", int, lambda v: v >= 1)
	_expect(path, document, "sender", str, lambda v: bool(v))
	_expect(path, document, "audience", list,
	        lambda v: all(isinstance(x, str) for x in v)
	        and sorted(set(v)) == v and bool(v))
	for field in ("notice", "publication"):
		value = document[field]
		# THE ACTUAL GRAMMAR. R25: "non-empty string" accepted `"made-up"` as
		# completed work, so a receipt could claim a publication that never
		# existed. Baton ids are `secrets.token_hex(16)`.
		if value is not None and not _is_identifier(value):
			raise PublishError(f"{path}: {field} is {value!r}, which is not an "
			                   f"identifier Baton issues")
	if document["attempting"] not in (None, "notice", "directed"):
		raise PublishError(f"{path}: attempting is {document['attempting']!r}, "
		                   f"which is not a step this tool takes")
	for field in IDENTITY:
		if document.get(field) != identity[field]:
			raise PublishError(
				f"{path} was written for a different publication: its "
				f"{field} is not the one being published now. A changed input "
				f"begins a new publication with a new receipt; it never "
				f"inherits completion from the old one.")
	return document


def _is_identifier(value) -> bool:
	"""A Baton message or notice id: 32 lowercase hex characters."""
	return (isinstance(value, str) and len(value) == 32
	        and all(c in "0123456789abcdef" for c in value))


def _is_sha(value: str) -> bool:
	return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _expect(path: str, document: dict, field: str, kind, ok) -> None:
	value = document[field]
	if isinstance(value, bool) or not isinstance(value, kind) or not ok(value):
		raise PublishError(f"{path}: {field} is {value!r}, which is not the "
		                   f"{kind.__name__} this tool records")


def _unique_keys(pairs):
	seen = {}
	for key, value in pairs:
		if key in seen:
			raise ValueError(f"duplicate key {key!r}")
		seen[key] = value
	return seen


def _write_receipt(home: int, path: str, document: dict) -> bool:
	"""Written after every confirmed step, and durable before the next one.

	Returns whether durability was confirmed. A receipt that is only written
	when everything succeeds is exactly no use in the case it exists for.
	"""
	through = f"/proc/self/fd/{home}"
	handle, staging = tempfile.mkstemp(prefix=".receipt-", dir=through)
	try:
		with os.fdopen(handle, "w", encoding="utf-8") as writer:
			json.dump(document, writer, indent=2, sort_keys=True)
			writer.write("\n")
			writer.flush()
			os.fsync(writer.fileno())
		os.replace(os.path.basename(staging), os.path.basename(path),
		           src_dir_fd=home, dst_dir_fd=home)
	except BaseException:
		if os.path.lexists(staging):
			os.unlink(staging)
		raise
	try:
		os.fsync(home)
	except OSError:
		return False
	return True


def _receipt_home(receipt_path: str) -> int:
	"""The receipt's parent directory, opened and HELD without following it.

	R25: the lock, the staging file, the replace and the directory fsync were
	all built from lexical paths, so a symlinked parent was followed and the
	real receipt was published outside the path that was named.

	The same limit applies here as to the deployment root: this refuses links
	and non-directories, and it cannot stop a same-UID process from moving the
	directory it holds. That is the cooperative single-operator boundary
	Slawomir approved on 2026-08-13, stated in `deploy.py`; nothing here
	claims more than it.
	"""
	directory = os.path.dirname(os.path.abspath(receipt_path)) or "/"
	# EVERY ANCESTOR, from the root down. R27: `O_NOFOLLOW` applies to the
	# FINAL component only, and `islink` was asked about that same final
	# component -- so `ROOT/linked/nested/receipt.json`, where `nested` is a
	# real directory inside a symlinked `linked`, resolved happily and
	# published the receipt outside the path that was named.
	#
	# A receipt path is user-supplied and has no separate trusted anchor, so
	# there is nothing to descend FROM except `/`, and every existing
	# component has to be checked on the way down.
	import deploy

	fd = os.open("/", os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
	walked = [fd]
	try:
		for name in [part for part in directory.split("/") if part]:
			try:
				nxt = deploy._openat2_beneath(name, fd)
				if nxt is None:
					nxt = os.open(name,
					              os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
					              dir_fd=fd)
			except OSError as exc:
				raise PublishError(
					f"{directory}: {name!r} is a symlink or not a directory "
					f"({exc.strerror}). A receipt is written inside the path "
					f"that was named, and following a link would put it "
					f"somewhere else.") from None
			walked.append(nxt)
			fd = nxt
		# The last descriptor is the receipt's home; the rest were only the
		# way there.
		for descriptor in walked[:-1]:
			os.close(descriptor)
		return fd
	except BaseException:
		for descriptor in walked:
			os.close(descriptor)
		raise


@contextlib.contextmanager
def _only_one(home: int, receipt_path: str):
	"""One publisher at a time for one receipt, locked inside its directory."""
	name = os.path.basename(receipt_path) + ".lock"
	try:
		fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644,
		             dir_fd=home)
	except FileExistsError:
		raise PublishError(
			f"{receipt_path}.lock exists, so another publication holds this "
			f"receipt. If nothing is running, remove it deliberately.") from None
	try:
		os.write(fd, f"{os.getpid()}\n".encode())
		os.close(fd)
		yield
	finally:
		try:
			os.unlink(name, dir_fd=home)
		except OSError:
			pass


def plan(config_path: str, guide_path: str, receipt_path: str, *,
         sender: str = "") -> dict:
	"""What publishing WOULD do, computed without sending anything."""
	identity = _identity(config_path, guide_path, sender)
	if sender:
		home = _receipt_home(receipt_path)
		try:
			receipt = _receipt(receipt_path, identity, home)
		finally:
			os.close(home)
	else:
		receipt = None
	remaining = ["notice", "directed"]
	if receipt is not None:
		remaining = [step for step, done in (("notice", receipt["notice"]),
		                                     ("directed", receipt["publication"]))
		             if not done]
	return {"audience": identity["audience"],
	        "notice": receipt["notice"] if receipt else None,
	        "publication": receipt["publication"] if receipt else None,
	        "attempting": receipt["attempting"] if receipt else None,
	        "remaining": remaining,
	        "body_sha256": identity["body_sha256"],
	        "config_digest": identity["config_digest"],
	        "config_generation": identity["config_generation"]}


class Unrecorded(PublishError):
	"""A receipt step committed and could not be confirmed durable. Nothing
	further is sent: the next step's safety depends on this one surviving a
	power loss."""


def _gate(home: int, receipt_path: str, receipt: dict, what: str) -> None:
	"""Write a receipt step and REFUSE TO CONTINUE unless it is durable."""
	if not _write_receipt(home, receipt_path, receipt):
		raise Unrecorded(
			f"{what} committed but could not be confirmed durable, so nothing "
			f"further was sent. Re-run: the receipt on disk is what the retry "
			f"reasons from, and a step that might not survive a power loss "
			f"cannot be the basis for the next one.")


def publish(config_path: str, guide_path: str, receipt_path: str, *,
            sender: str, resend_uncertain: bool = False) -> dict:
	"""Send the notice and the directed publication, resumably.

	AT LEAST ONCE, SAID OUT LOUD. Baton commits before this process learns it
	did, so a crash between the send and the receipt leaves a step that may or
	may not have landed. The receipt records `attempting` BEFORE each call, so
	a retry cannot pretend the earlier attempt did not commit: it refuses, and
	`--resend-uncertain` sends again with `possible_duplicate=True`, which is
	what the protocol requires of a sender who cannot know.
	"""
	import baton_core

	# ONE READ. Identity and both sends come from these exact bytes.
	body = _read_once(guide_path)
	identity = _identity(config_path, guide_path, sender, body=body)
	subject = "Baton is moving: new paths, same versions"
	durable = True

	home = _receipt_home(receipt_path)
	try:
		with _only_one(home, receipt_path):
			receipt = _receipt(receipt_path, identity, home)
			pending = receipt.get("attempting")
			if pending and not resend_uncertain:
				raise Uncertain(
					f"a previous run was in the middle of publishing the "
					f"{pending!r} step and did not record its outcome. It may have "
					f"committed. Re-run with --resend-uncertain to send it again "
					f"as a possible duplicate, which is what a sender who cannot "
					f"know is required to say.")
			with baton_core.open_instance(config_path) as store:
				# THE FROZEN CONFIG, re-proved against the OPEN authority rather
				# than against a second read: a `regen` that changed the accepted
				# digest without changing the participant list would otherwise
				# publish the old guide under the new config.
				if store.config_digest != identity["config_digest"] or \
						store.config["generation"] != identity["config_generation"]:
					raise PublishError(
						"the accepted config changed between generating this guide "
						"and publishing it; regenerate before sending")
				accepted = sorted(entry["address"]
				                  for entry in store.list_participants())
				if accepted != identity["audience"]:
					raise PublishError(
						"the accepted participants changed between generating this "
						"guide and publishing it; regenerate before sending")

				if receipt["notice"] is None:
					duplicate = pending == "notice"
					receipt["attempting"] = "notice"
					# A GATE, not a field: an `attempting` record whose durability
					# could not be confirmed was folded into the exit code and the
					# send happened anyway, so a power loss could revert the
					# receipt while the notice had already committed.
					_gate(home, receipt_path, receipt,
					      "recording that the notice was about to be sent")
					# NO SCOPE PARAMETER. It was accepted and never bound into the
					# receipt, so a receipt from a scoped notice could mark an
					# unscoped one done. The guide goes to everybody who holds an
					# address here; a scoped variant would need its scope in the
					# identity above.
					receipt["notice"] = store.send_notice(
						sender, kind="migration", subject=subject, body=body,
						possible_duplicate=duplicate)
					receipt["attempting"] = None
					# And the SAME gate before the next external mutation: if the
					# confirmed notice is not durably recorded, advancing to the
					# directed publication risks a receipt that says `attempting:
					# notice` while both channels have committed.
					_gate(home, receipt_path, receipt, "recording the notice that was "
					                             "sent")
				if receipt["publication"] is None:
					duplicate = pending == "directed"
					receipt["attempting"] = "directed"
					_gate(home, receipt_path, receipt, "recording that the directed "
					                             "publication was about to be sent")
					# EVERY REGISTERED PARTICIPANT, the sender included: the ruling
					# says one durable delivery per registered participant, and a
					# sender who is also a participant is one.
					receipt["publication"] = store.send(
						sender, identity["audience"], kind="migration",
						subject=subject, body=body,
						possible_duplicate=duplicate)
					receipt["attempting"] = None
					durable = _write_receipt(home, receipt_path, receipt)
	finally:
		os.close(home)
	return {**receipt, "durable": bool(durable)}


def _expected_failures():
	"""The classes that mean the outside world refused, not that this code is
	wrong: Baton's own refusals, filesystem errors, and decoding errors."""
	import baton_core

	return (baton_core.BatonError, OSError, UnicodeError)


def main(argv=None) -> int:
	import argparse

	global _EXPECTED
	_EXPECTED = _expected_failures()

	parser = argparse.ArgumentParser(
		prog="publish_guide",
		description="Publish the migration guide as a notice and directed deliveries")
	parser.add_argument("guide")
	parser.add_argument("--config", required=True)
	parser.add_argument("--receipt", required=True)
	parser.add_argument("--participant", help="the sender; required to send")
	parser.add_argument("--resend-uncertain", action="store_true",
	                    help="a previous run may have committed a step it did "
	                         "not record; send it again as a possible "
	                         "duplicate")
	parser.add_argument("--send", action="store_true",
	                    help="actually publish. Without it, this prints the "
	                         "plan and sends nothing.")
	args = parser.parse_args(argv)
	try:
		if not args.send:
			print(json.dumps(plan(args.config, args.guide, args.receipt,
			                      sender=args.participant or ""),
			                 indent=2, sort_keys=True))
			return 0
		if not args.participant:
			raise PublishError("--participant names the sender; publishing "
			                   "without one is not something to guess at")
		written = publish(args.config, args.guide, args.receipt,
		                  sender=args.participant,
		                  resend_uncertain=args.resend_uncertain)
		print(json.dumps(written, indent=2, sort_keys=True))
		return 0 if written["durable"] else 3
	except (PublishError, migration_guide.GuideError) as refusal:
		print(f"publish_guide: {refusal}", file=sys.stderr)
		return 1
	except _EXPECTED as failure:
		# NAMED, NOT A TRACEBACK -- and only for the classes that mean the
		# OUTSIDE WORLD said no. R28: catching every `Exception` swallowed
		# `AssertionError` and `TypeError` too, printing "re-run to continue"
		# over a programming defect and hiding the traceback that would have
		# shown where it was. A defect is not an uncertain external outcome
		# and must not be dressed as one.
		name = type(failure).__module__.split(".")[0]
		print(f"publish_guide: the publication stopped: {failure} "
		      f"[{name}.{type(failure).__name__}]. Anything already recorded "
		      f"in the receipt stands; re-run to continue.", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
