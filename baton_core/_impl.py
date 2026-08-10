"""Protocol-8 Baton: one logical transactional coordination authority.

All protocol state lives in a single SQLite database (`mailbox.sqlite3`
beside the explicitly passed config); there are no filename-state
transitions. This module is semantically independent of any host project:
it knows nothing about repositories, work trees, review workflows, or any
particular participant names. See PLAN (the consolidated v6 design) for
the contract this implements.

Exit-code table (documented contract):
  0 success
  2 environment floor (Python / sqlite3 module / SQLite library)
  3 nothing eligible
  4 protocol / validation error
  5 race / busy / locked
  6 integrity damage (fail closed)
  7 gated (maintenance / moved instance)
"""

from __future__ import annotations

import datetime as dt
import errno
import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import sys
from typing import Any

EXIT_FLOOR = 2
EXIT_NONE = 3
EXIT_PROTOCOL = 4
EXIT_RACE = 5
EXIT_DAMAGE = 6
EXIT_GATED = 7

PROTOCOL_VERSION = 10
TOOL_VERSION = "6.0.0"
SQLITE_MIN = (3, 37, 0)  # STRICT tables
BUSY_TIMEOUT_MS = 10_000
TRANSIENT_BODY_MAX_BYTES = 64 * 1024
DEFAULT_RETENTION_DAYS = 90
DEFAULT_NOTICE_TTL_SECONDS = 86_400

RETENTION_DURABLE = "durable"
RETENTION_TRANSIENT = "transient"
RETENTIONS = frozenset((RETENTION_DURABLE, RETENTION_TRANSIENT))

ADDRESS_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
HEX32_RE = re.compile(r"^[a-f0-9]{32}$")
KIND_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
THREAD_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
ROOT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")

# -- content envelope -------------------------------------------------------
#
# Baton TRANSPORTS content and never renders it. These constants describe
# bytes; nothing here interprets them. A transport that renders is a transport
# with an injection surface.

# RFC 2045 token, restricted to the RFC 7230 character set. Deliberately
# stricter than RFC 2045's grammar: fail closed on anything exotic rather than
# store a media type this build cannot round-trip byte-for-byte.
MEDIA_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")

# The default for a body published without a declared type. Every message this
# project has ever carried is Markdown, `materialize` has always emitted `.md`,
# and the protocol document names Markdown as the review-document format.
# RFC 7763 makes the charset parameter REQUIRED for text/markdown, so the
# default states it rather than leaving it to be assumed downstream.
DEFAULT_CONTENT_TYPE = "text/markdown; charset=utf-8"
DEFAULT_CONTAINER_TYPE = "multipart/mixed"

DISPOSITION_INLINE = "inline"
DISPOSITION_ATTACHMENT = "attachment"
# Media type for an external part whose type the caller did not declare.
# Deliberately the RFC 2046 "unknown bytes" type rather than a guess from the
# file extension: sniffing a type is exactly the interpretation Baton does not do.
DEFAULT_ATTACHMENT_TYPE = "application/octet-stream"

# HOW A CONTENTLESS MESSAGE IS STORED, pinned rather than left implicit.
#
# `messages.content_type` and `manifest_sha256` are NOT NULL, so "no content"
# still needs a representation. It is an EMPTY CONTAINER: a `multipart/mixed`
# whose part list is empty, whose manifest is the digest of exactly that, and
# which owns no part rows. Nothing is invented -- an empty ordered list of
# parts is what a message with no parts has -- and the retry manifest stays
# meaningful, because two contentless publications of the same subject hash
# identically while any content at all hashes differently.
#
# The alternative was nullable columns, which is a schema change, and a schema
# change is a protocol bump and another cutover for a quick-message shorthand.
CONTENTLESS_CONTAINER = "multipart/mixed"
DISPOSITIONS = frozenset((DISPOSITION_INLINE, DISPOSITION_ATTACHMENT))  # RFC 2183

# Delivery representation names. Exactly one is ever present on a leaf part,
# and `encoding` names which -- so a consumer dispatches on one key instead of
# probing for two that must never both appear.
ENCODING_TEXT = "text"
ENCODING_BASE64 = "base64"

# Where a leaf's bytes live. Protocol 9 made external storage a PART
# representation rather than a second content model bolted onto `messages`.
STORAGE_NONE = "none"          # a multipart container owns no bytes
STORAGE_INLINE = "inline"      # bytes in `contents`, owned by this instance
STORAGE_EXTERNAL = "external"  # bytes in a configured root, hash-pinned

# Projection suffixes by media type. Naming only: nothing here parses, renders,
# or transforms the bytes.
_PROJECTION_SUFFIXES = {
	"text/markdown": ".md",
	"text/plain": ".txt",
	"text/html": ".html",
	"text/csv": ".csv",
	"application/json": ".json",
	"application/pdf": ".pdf",
	"image/png": ".png",
	"image/jpeg": ".jpg",
	"image/svg+xml": ".svg",
}
_PROJECTION_SUFFIX_DEFAULT = ".bin"
_KNOWN_PROJECTION_SUFFIXES = frozenset(_PROJECTION_SUFFIXES.values()) | {_PROJECTION_SUFFIX_DEFAULT}

# A human-facing one-line summary -- what an inbox shows before anything is
# opened. Optional at the protocol level so status traffic can fall back to
# `kind`, but lossless and immutable when supplied.
SUBJECT_MAX_BYTES = 255

DB_NAME = "mailbox.sqlite3"

# Deleting verbs authorized to remove content rows (retention deletion is
# not mutation): the consuming reply/close transaction scrubs the incoming
# transient body; gc removes aged terminal metadata.
CONTENT_DELETE_VERBS = ("reply", "close", "gc")

# statfs f_type allowlist: known-good local filesystems (fail closed).
LOCAL_FS_MAGICS = {
	0xEF53,        # ext2/3/4
	0x9123683E,    # btrfs
	0x58465342,    # xfs
	0x01021994,    # tmpfs
	0xF2F52010,    # f2fs
}


# Test-only fault-injection seam (PLAN: injected storage-layer hooks, no
# ambient production switch). Production leaves this None.
_FAULT_HOOK = None


def _fault(point: str) -> None:
	if _FAULT_HOOK is not None:
		_FAULT_HOOK(point)


class BatonError(RuntimeError):
	def __init__(self, message: str, exit_code: int = EXIT_PROTOCOL) -> None:
		super().__init__(message)
		self.exit_code = exit_code


def _utc_now_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id() -> str:
	return secrets.token_hex(16)


# ---------------------------------------------------------------------------
# Content envelope: media types, parts, and the manifest digest
# ---------------------------------------------------------------------------

def parse_media_type(raw: str) -> tuple[str, str, dict[str, str]]:
	"""Parse an RFC 2045 media type with parameters into
	`(type, subtype, params)`, canonicalized: type, subtype and parameter
	NAMES lowercased (they are case-insensitive), parameter values preserved
	except `charset`, which RFC 2046 also defines as case-insensitive.

	Strict on purpose. An unparseable or ambiguous type is refused at
	publication rather than stored and delivered as something a consumer must
	guess at -- a mislabelled part is worse than an unlabelled one, because a
	consumer acts on the label."""
	if type(raw) is not str:
		raise BatonError("content_type must be a string")
	text = raw.strip()
	if not text:
		raise BatonError("content_type must not be empty")
	head, sep, tail = text.partition(";")
	main, slash, sub = head.strip().partition("/")
	if not slash:
		raise BatonError(
			f"content_type {raw!r} is not TYPE/SUBTYPE (e.g. 'text/markdown; charset=utf-8')")
	main = main.strip().lower()
	sub = sub.strip().lower()
	if not MEDIA_TOKEN_RE.match(main) or not MEDIA_TOKEN_RE.match(sub):
		raise BatonError(f"content_type {raw!r} has an invalid type or subtype token")
	params: dict[str, str] = {}
	rest = tail if sep else ""
	while rest.strip():
		name, eq, remainder = rest.partition("=")
		name = name.strip().lower()
		if not eq or not MEDIA_TOKEN_RE.match(name):
			raise BatonError(f"content_type {raw!r} has a malformed parameter")
		if name in params:
			raise BatonError(f"content_type {raw!r} repeats the {name!r} parameter")
		remainder = remainder.lstrip()
		if remainder.startswith('"'):
			value, rest = _scan_quoted(remainder, raw)
		else:
			value, _, rest = remainder.partition(";")
			value = value.strip()
			if not MEDIA_TOKEN_RE.match(value):
				raise BatonError(
					f"content_type {raw!r} parameter {name!r} is neither a token nor a quoted string")
		if name == "charset":
			value = value.lower()
		params[name] = value
	# RFC 7763 makes charset REQUIRED for text/markdown. Requiring it for every
	# text/* subtype costs a caller nine characters and removes the only
	# question a consumer would otherwise have to answer by sniffing.
	if main == "text" and "charset" not in params:
		raise BatonError(
			f"content_type {raw!r} must declare a charset parameter (RFC 7763 requires it for "
			f"text/markdown, and delivery encoding depends on it) -- e.g. '{text}; charset=utf-8'")
	if main == "multipart" and params:
		raise BatonError(
			"a multipart container type takes no parameters here; part order is structural, "
			"not a boundary string")
	return main, sub, params


def _scan_quoted(text: str, raw: str) -> tuple[str, str]:
	"""Consume one RFC 2045 quoted-string from the head of `text`, returning
	`(value, remainder-after-the-next-semicolon)`."""
	out = []
	index = 1
	while index < len(text):
		char = text[index]
		if char == "\\" and index + 1 < len(text):
			out.append(text[index + 1])
			index += 2
			continue
		if char == '"':
			trailing = text[index + 1:].lstrip()
			if trailing.startswith(";"):
				return "".join(out), trailing[1:]
			if trailing:
				raise BatonError(f"content_type {raw!r} has trailing junk after a quoted parameter")
			return "".join(out), ""
		if ord(char) < 0x20 or ord(char) == 0x7F:
			raise BatonError(f"content_type {raw!r} has a control character in a quoted parameter")
		out.append(char)
		index += 1
	raise BatonError(f"content_type {raw!r} has an unterminated quoted parameter")


def canonical_media_type(raw: str) -> str:
	"""Round-trip a media type through `parse_media_type` into ONE canonical
	spelling. The manifest digest hashes this string, so `text/markdown;
	charset=UTF-8` and `text/markdown;charset=utf-8` must not be two different
	contents -- and equally must not collide with a genuinely different type."""
	main, sub, params = parse_media_type(raw)
	out = f"{main}/{sub}"
	for name in sorted(params):
		value = params[name]
		if MEDIA_TOKEN_RE.match(value):
			out += f"; {name}={value}"
		else:
			escaped = value.replace("\\", "\\\\").replace('"', '\\"')
			out += f'; {name}="{escaped}"'
	return out


def is_container_type(content_type: str) -> bool:
	return content_type.split("/", 1)[0].lower() == "multipart"


def validate_subject(subject: str | None, *, where: str = "subject") -> str | None:
	"""A subject is a single line of bounded plain text.

	Rejected rather than sanitized: a newline or a control character in a
	subject is a display-injection hazard for every consumer that lists an
	inbox, and quietly stripping it would leave the sender believing they sent
	something they did not. Bounded in BYTES for the same reason `part_name` is
	-- a character count is not what any downstream store enforces."""
	if subject is None:
		return None
	if type(subject) is not str:
		raise BatonError(f"{where} must be a string")
	if subject != subject.strip():
		raise BatonError(f"{where} must not have leading or trailing whitespace")
	if not subject:
		raise BatonError(f"{where} must not be empty; omit it entirely instead")
	if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in subject):
		raise BatonError(
			f"{where} must be a single line of plain text: no newlines, tabs, or other "
			f"control characters")
	encoded = subject.encode("utf-8")
	if len(encoded) > SUBJECT_MAX_BYTES:
		raise BatonError(
			f"{where} must be at most {SUBJECT_MAX_BYTES} bytes as UTF-8 (got {len(encoded)})")
	return subject


# A team scope: dotted segments, then a literal `.*`. The segment grammar is
# `ADDRESS_RE`'s, because a scope selects ADDRESSES and a selector that could
# not possibly match one is a typo rather than an empty audience.
SCOPE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*\.\*$")


def _is_address(address) -> bool:
	"""The participant-address grammar AND its bound, in one place.

	The bound lives beside the pattern rather than inside it, so anything that
	calls `ADDRESS_RE.match` alone is quietly laxer than publication. Doctor
	was; that is why this exists.
	"""
	return (type(address) is str and bool(ADDRESS_RE.match(address))
	        and len(address) <= 64)


def validate_scope(selector: str) -> tuple:
	"""A scope selector -> its literal segment prefix, or `BatonError`.

	Returns the segments BEFORE the `*`, which is what matching compares.
	Returning segments rather than a string is the point: matching on the
	string `"baton."` would also match `baton.x` AND `baton_extra.reviewer` is
	only excluded by luck of the dot. Comparing whole segments cannot make
	that mistake.
	"""
	if type(selector) is not str:
		raise BatonError("scope must be a string")
	if not SCOPE_RE.match(selector) or len(selector) > 64:
		raise BatonError(
			f"scope {selector!r} must be dotted lowercase segments ending in "
			f"'.*', for example 'baton.*'")
	return tuple(selector.split(".")[:-1])


def scope_matches(selector_segments: tuple, address: str) -> bool:
	"""Whole-segment prefix match.

	`baton.*` matches `baton.reviewer` and `baton.implementer`. It does NOT
	match `baton_extra.reviewer` -- the selector's segment is `baton`, the
	address's first segment is `baton_extra`, and those are different segments.
	A string-prefix test would have got this right by accident and `baton.*`
	against `baton.a.b` wrong.

	A scope also never matches its own prefix as a whole address: `baton.*`
	requires something AFTER `baton`, because a scope addresses members of a
	group rather than the group itself.
	"""
	segments = address.split(".")
	return (len(segments) > len(selector_segments)
	        and tuple(segments[:len(selector_segments)]) == selector_segments)


def expand_scope(selector: str, participants) -> list:
	"""Every configured participant the selector matches, sorted.

	SORTED because this expansion is stored and compared: an audience that
	depends on dict ordering would make retry identity depend on how the
	config happened to be written.

	An EMPTY expansion is refused. A notice addressed to nobody is a
	publication that silently does nothing, and the likeliest cause is a typo
	in the selector -- which is exactly when the author most wants to be told.
	"""
	segments = validate_scope(selector)
	matched = sorted(address for address in participants
	                 if scope_matches(segments, address))
	if not matched:
		raise BatonError(
			f"scope {selector!r} matches no configured participant")
	return matched


def validate_part_name(name: str | None) -> str | None:
	"""A part name is an UNINTERPRETED LABEL. It is not a path, and protocol 10
	stopped pretending otherwise.

	Until the rename this was `validate_filename` and it enforced filesystem
	rules -- no `/`, no `\\`, not `.` or `..`, no leading `-` -- on the theory
	that a careless consumer might use the label as a path. Protocol 10 rejects
	the premise: the SENDER names a part, the RECIPIENT decides whether it ever
	becomes a file and under what name, and `materialize` derives its output
	from the caller's own `--prefix` and `--dir` and never from this field.

	Renaming the key while keeping those rules would have been the old concept
	wearing the new word, which is exactly what the finding exists to prevent.
	So `../diagram` is a legal part name now: it is a strange one, it means
	nothing to Baton, and it arrives at the recipient exactly as the sender
	wrote it. Refusing it would be Baton deciding what a label means to
	somebody else's software.

	WHAT IS STILL REFUSED, and why each one is about Baton rather than about a
	filesystem:

	  empty            a present-but-empty label is not a name, and absent
	                   already means "no name"
	  control chars    this string is displayed in an inbox by every consumer;
	                   a `\x1b[2J` in it is a display-injection hazard, which is
	                   the same reason `subject` refuses them
	  NUL              cannot survive the boundaries this string crosses
	  over 255 bytes   a BATON bound: it is stored in every manifest, compared
	                   on every retry, and drawn in a one-line list. Unbounded
	                   metadata is a denial-of-service surface and an unreadable
	                   row. Measured in BYTES because that is what the store and
	                   the digest count.
	"""
	if name is None:
		return None
	if type(name) is not str:
		raise BatonError("part_name must be a string")
	encoded = name.encode("utf-8")
	if not name or len(encoded) > 255:
		raise BatonError(
			f"part_name must be 1..255 bytes as UTF-8 (got {len(encoded)}); the bound "
			f"is Baton's -- the label is stored in every manifest, compared on every "
			f"retry, and drawn on one line -- and it is bytes because that is what "
			f"the store and the digest count")
	if "\x00" in name:
		raise BatonError(f"part_name contains a NUL byte")
	if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in name):
		# NOT echoed: the offending character is by definition a control
		# character, and putting it on a terminal is the hazard being refused.
		raise BatonError("part_name contains a control character")
	return name


def normalize_parts(spec: Any, *, where: str = "content") -> list[dict]:
	"""Normalize a caller's part specification into the canonical tree the
	store writes and the manifest digest hashes.

	A leaf carries `content_type`, `disposition`, optional `part_name`, and
	`body` bytes. A container carries a `multipart/*` `content_type` and a
	non-empty `parts` list, and carries no bytes of its own. Nesting is
	arbitrary depth, so `multipart/alternative` inside `multipart/mixed` is a
	row layout that already exists rather than a schema change."""
	if not isinstance(spec, (list, tuple)) or not spec:
		raise BatonError(f"{where}: parts must be a non-empty list")
	out = []
	for index, raw in enumerate(spec):
		if not isinstance(raw, dict):
			raise BatonError(f"{where}[{index}]: each part must be an object")
		unknown = set(raw) - {"content_type", "disposition", "part_name", "body", "parts", "attach"}
		if unknown:
			raise BatonError(f"{where}[{index}]: unknown part field(s) {sorted(unknown)}")
		# Default only when a field is ABSENT. `raw.get(k) or DEFAULT` cannot
		# tell "not supplied" from "supplied empty", so an explicit "" used to
		# become a valid default instead of reaching its validator -- a caller
		# asking for something meaningless got silence and a media type it
		# never named.
		declared_type = raw.get("content_type")
		# THE DEFAULT COMES FROM THE NODE, not from the surface that built it.
		# A node carrying `attach` is a pinned file of unknown type; an inline
		# node is authored text. Defaulting both to markdown declared binaries
		# to be text -- an assertion the store made on the sender's behalf that
		# the sender never made, recorded in the manifest digest and therefore
		# not correctable without republishing.
		#
		# The failure was silent in the direction that matters: calling binary
		# content text invites a reader to decode it, while the reverse is
		# merely unhelpful.
		#
		# This also makes `send(attach=...)`'s behaviour a CONSEQUENCE of the
		# general rule rather than a second rule that only one caller reached.
		default_type = (DEFAULT_ATTACHMENT_TYPE if raw.get("attach") is not None
		                else DEFAULT_CONTENT_TYPE)
		content_type = canonical_media_type(
			default_type if declared_type is None else declared_type)
		disposition = raw.get("disposition")
		if disposition is None:
			disposition = DISPOSITION_INLINE
		elif disposition not in DISPOSITIONS:
			raise BatonError(
				f"{where}[{index}]: disposition must be one of {sorted(DISPOSITIONS)} "
				f"(RFC 2183), not {disposition!r}")
		body = raw.get("body")
		attach = raw.get("attach")
		children = raw.get("parts")
		node = {"content_type": content_type, "disposition": disposition,
		        "part_name": None, "storage": STORAGE_NONE, "body": None, "attach": None,
		        "sha256": None, "size": None, "parts": None}
		if is_container_type(content_type):
			if body is not None or attach is not None:
				raise BatonError(
					f"{where}[{index}]: a {content_type} container holds parts, not bytes")
			if raw.get("part_name") is not None:
				raise BatonError(f"{where}[{index}]: a container part has no part_name")
			node["parts"] = normalize_parts(children, where=f"{where}[{index}].parts")
		else:
			if children is not None:
				raise BatonError(
					f"{where}[{index}]: only a multipart/* part may hold nested parts")
			if (body is None) == (attach is None):
				raise BatonError(
					f"{where}[{index}]: a leaf part requires exactly one of body (inline) "
					f"or attach (external)")
			node["part_name"] = validate_part_name(raw.get("part_name"))
			if attach is not None:
				# External bytes are pinned, not copied. Hash and size are
				# filled in by the store, which is what can resolve the root.
				node["storage"] = STORAGE_EXTERNAL
				node["attach"] = _normalize_attach_ref(attach, f"{where}[{index}]")
				out.append(node)
				continue
			if not isinstance(body, (bytes, bytearray)):
				raise BatonError(f"{where}[{index}]: a leaf part requires a bytes body")
			body = bytes(body)
			node["storage"] = STORAGE_INLINE
			node["body"] = body
			node["sha256"] = hashlib.sha256(body).hexdigest()
			node["size"] = len(body)
			# A part declaring charset=utf-8 whose bytes are not valid UTF-8 is
			# a lie about its own content, and it is cheaper to refuse it here
			# than to hand every consumer a decode error later.
			if _delivery_encoding(content_type) == ENCODING_TEXT:
				try:
					body.decode("utf-8")
				except UnicodeDecodeError as exc:
					raise BatonError(
						f"{where}[{index}]: content_type declares charset=utf-8 but the bytes are "
						f"not valid UTF-8 ({exc})") from exc
		out.append(node)
	return out


def _normalize_attach_ref(attach: Any, where: str) -> dict:
	"""An external part names a configured root and a path within it. The
	hash, size and binding generation are pinned by the STORE at publication;
	a caller cannot assert them."""
	if isinstance(attach, str):
		root_id, sep, rel = attach.partition(":")
		if not sep:
			raise BatonError(f"{where}: attach expects ROOT_ID:RELATIVE/PATH")
		attach = {"root_id": root_id, "path": rel}
	if not isinstance(attach, dict):
		raise BatonError(f"{where}: attach must be ROOT_ID:PATH or an object")
	unknown = set(attach) - {"root_id", "path"}
	if unknown:
		raise BatonError(f"{where}: unknown attach field(s) {sorted(unknown)}")
	root_id, path = attach.get("root_id"), attach.get("path")
	if not root_id or type(root_id) is not str:
		raise BatonError(f"{where}: attach requires a root_id")
	if not path or type(path) is not str:
		raise BatonError(f"{where}: attach requires a path")
	return {"root_id": root_id, "path": path}


def _delivery_encoding(content_type: str) -> str:
	"""Which of the two delivery representations a part uses -- decided by the
	DECLARED media type, never by whether the bytes happen to decode.

	This is the whole point of the typed envelope. The old representation
	emitted a `utf8` field only when the bytes decoded, so the same field
	appeared and disappeared based on content and a consumer could not dispatch
	on it. Now `text/...; charset=utf-8` always delivers `text`, everything else
	always delivers `base64`, and exactly one of them is ever present."""
	main, _, params = parse_media_type(content_type)
	if main == "text" and params.get("charset") == "utf-8":
		return ENCODING_TEXT
	return ENCODING_BASE64


def refuse_empty_bodies(nodes, where: str) -> None:
	"""Refuse a leaf that says "here is content" and carries none.

	A zero-byte part is the store asserting, on the sender's behalf, that
	content exists and happens to be empty. Nobody means that. What people
	DO mean -- "the subject is the whole message" -- is a contentless
	publication, which is a different shape and is permitted separately where
	a subject carries it.

	NOT called from `content_spec`, deliberately. `reply` and `close` build
	their nodes before consulting the committed disposition, so refusing
	during normalization would make an exact retry of a legacy zero-byte
	disposition impossible to complete -- turning a defect fix into a
	permanent inability to finish an operation that already committed. This
	runs at FIRST publication instead, which is the only place new content is
	created.
	"""
	for index, node in enumerate(nodes or []):
		if node.get("parts"):
			refuse_empty_bodies(node["parts"], f"{where}[{index}].parts")
		elif node.get("attach") is None and node.get("body") == b"":
			# The DEFAULT exit class, which is what every other validation
			# refusal in this module uses. The finding named an
			# `EXIT_VALIDATION` that does not exist here; inventing one for a
			# single refusal would split the exit vocabulary rather than
			# describe it.
			raise BatonError(
				f"{where}[{index}]: an explicitly supplied body must contain at least "
				f"one byte (omit it entirely for a subject-only message)")


def content_spec(body: bytes | None, parts: Any, *, content_type: str | None = None,
                 disposition: str | None = None, part_name: str | None = None,
                 container_type: str | None = None,
                 where: str = "content") -> tuple[str | None, list[dict] | None]:
	"""Normalize the two authoring surfaces into ONE manifest.

	`body` is the single-leaf convenience the CLI exposes; `parts` is the
	general form the store has always been able to write. Both produce the same
	shape, so a single-part message is not a special case anywhere below this
	function -- which is the difference between multipart readiness and an
	array with one element in it."""
	if parts is not None:
		if body is not None:
			raise BatonError(f"{where}: pass either body or parts, never both")
		if content_type is not None or disposition is not None or part_name is not None:
			raise BatonError(
				f"{where}: per-part metadata belongs on each part, not beside the parts list")
		nodes = normalize_parts(parts, where=where)
	elif body is not None:
		nodes = normalize_parts(
			[{"content_type": content_type, "disposition": disposition,
			  "part_name": part_name, "body": body}], where=where)
	else:
		# Metadata describing content that does not exist is refused rather
		# than dropped: an attachment-only send or a bodyless close that names
		# a content type is asking for something this operation cannot do, and
		# silently discarding it tells the caller it worked.
		orphaned = [name for name, value in (
			("content_type", content_type), ("disposition", disposition),
			("part_name", part_name), ("container_type", container_type))
			if value is not None]
		if orphaned:
			raise BatonError(
				f"{where}: {', '.join(orphaned)} supplied but there is no content to "
				f"describe; content metadata requires a body or parts")
		return None, None
	container = canonical_media_type(
		DEFAULT_CONTAINER_TYPE if container_type is None else container_type)
	if not is_container_type(container):
		raise BatonError(
			f"{where}: the envelope content_type must be multipart/* (got {container!r})")
	return container, nodes


def total_content_size(nodes: list[dict]) -> int:
	return sum((node["size"] or 0) if node["parts"] is None else total_content_size(node["parts"])
	           for node in nodes)


def reject_external_parts(nodes: list[dict], owner: str) -> None:
	"""External storage is permitted ONLY on directed messages, because that
	is the only owner with a damage lifecycle.

	A pinned file can go stale after publication, so every owner that accepts
	one needs a way to notice and a way to resolve it. A message has the whole
	chain: claim-time verification outside the write lock, skip-and-continue so
	one damaged message cannot block the queue, the audited quarantine
	ceremony, and `doctor`.

	A notice has none of it. There is no per-recipient claim, so nothing to
	skip and nothing to quarantine; the seen receipt commits inside `see`'s
	write transaction, where file IO does not belong, and it would have to run
	once per recipient for one file. Accepting a pin there means committing an
	at-most-once receipt for content that may already be gone -- silent data
	loss for that participant.

	A close disposition is a terminal audit record that is never delivered.
	A pin there is a promise nothing ever checks.

	Refusing at publication is the honest option. Publishing a pin that nothing
	verifies is not."""
	for node in nodes:
		if node["parts"] is not None:
			reject_external_parts(node["parts"], owner)
		elif node["storage"] == STORAGE_EXTERNAL:
			raise BatonError(
				f"{owner} cannot carry an externally stored part: a pinned file can go "
				f"stale, and only a directed message has claim-time verification, "
				f"skip-and-continue, and the quarantine ceremony to resolve it. Send the "
				f"bytes inline, or send a directed message with the attachment")


def _check_transient_size(nodes: list[dict]) -> None:
	"""The transient ceiling bounds the MESSAGE, summed across its parts.
	Bounding each part instead would let a caller carry an unbounded transient
	payload by splitting it, which is the same row growing by another name."""
	total = total_content_size(nodes)
	if total > TRANSIENT_BODY_MAX_BYTES:
		raise BatonError(
			f"transient content exceeds {TRANSIENT_BODY_MAX_BYTES} bytes "
			f"across all parts ({total})")


def manifest_digest(container_type: str, nodes: list[dict]) -> str:
	"""The identity of a message's COMPLETE ordered part manifest, metadata
	included -- not merely of its bytes.

	`_verify_retry` compares this. Two retries that differ in part order,
	`content_type`, `disposition` or `part_name` are different operations even
	when every byte matches, and hashing the manifest rather than the payload
	is what makes them fail closed instead of silently reporting
	`already_committed` for an operation that was never committed."""
	def canon(items):
		return [{
			"content_type": node["content_type"],
			"disposition": node["disposition"],
			"part_name": node["part_name"],
			# Storage location is part of what a message IS: the same bytes
			# carried inline versus pinned externally are different messages,
			# because only one of them can go stale under your feet.
			"storage": node["storage"],
			"root_id": (node["attach"] or {}).get("root_id"),
			"path": (node["attach"] or {}).get("path"),
			"sha256": node["sha256"],
			"size": node["size"],
			"parts": canon(node["parts"]) if node["parts"] is not None else None,
		} for node in items]
	document = {"content_type": canonical_media_type(container_type), "parts": canon(nodes)}
	encoded = json.dumps(document, sort_keys=True, separators=(",", ":"),
	                     ensure_ascii=True).encode("utf-8")
	return hashlib.sha256(encoded).hexdigest()


_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _parse_ts(ts: str) -> dt.datetime:
	return dt.datetime.strptime(ts, _TS_FMT).replace(tzinfo=dt.timezone.utc)


def _notice_expired(created_ts: str, ttl_seconds: int | None, now_ts: str) -> bool:
	if ttl_seconds is None:
		return False
	return _parse_ts(created_ts) + dt.timedelta(seconds=ttl_seconds) <= _parse_ts(now_ts)


def _iso_minus_days(now_ts: str, days: int) -> str:
	return (_parse_ts(now_ts) - dt.timedelta(days=days)).strftime(_TS_FMT)


# ---------------------------------------------------------------------------
# Strict JSON
# ---------------------------------------------------------------------------

def _reject_dup_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
	obj: dict[str, Any] = {}
	for key, value in pairs:
		if key in obj:
			raise BatonError(f"strict JSON: duplicate object key {key!r}")
		obj[key] = value
	return obj


def _reject_constant(name: str) -> Any:
	raise BatonError(f"strict JSON: non-finite constant {name!r} rejected")


def loads_strict(text: str) -> Any:
	try:
		return json.loads(text, object_pairs_hook=_reject_dup_pairs, parse_constant=_reject_constant)
	except BatonError:
		raise
	except json.JSONDecodeError as exc:
		raise BatonError(f"strict JSON: parse error: {exc}") from exc


def canonical_dumps(obj: Any) -> str:
	return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def canonical_sha256(obj: Any) -> str:
	return hashlib.sha256(canonical_dumps(obj).encode("utf-8")).hexdigest()


def _expect_str(obj: dict, key: str, where: str, pattern: re.Pattern | None = None, maxlen: int | None = None) -> str:
	value = obj.get(key)
	if type(value) is not str:
		raise BatonError(f"{where}: {key!r} must be a string")
	if maxlen is not None and len(value) > maxlen:
		raise BatonError(f"{where}: {key!r} exceeds maximum length {maxlen}")
	if pattern is not None and not pattern.match(value):
		raise BatonError(f"{where}: {key!r} value {value!r} violates grammar")
	return value


def _expect_int(obj: dict, key: str, where: str, minimum: int | None = None) -> int:
	value = obj.get(key)
	if type(value) is not int:  # bool is not int here, by exact-type check
		raise BatonError(f"{where}: {key!r} must be an integer")
	if minimum is not None and value < minimum:
		raise BatonError(f"{where}: {key!r} must be >= {minimum}")
	return value


def _reject_unknown(obj: dict, allowed: frozenset[str], where: str) -> None:
	unknown = set(obj) - allowed
	if unknown:
		raise BatonError(f"{where}: unknown field(s) {sorted(unknown)!r} rejected")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_CONFIG_FIELDS = frozenset(("config_version", "protocol_version", "generation", "mailbox", "participants", "roots", "retention_days"))
_MAILBOX_FIELDS = frozenset(("name",))
_PARTICIPANT_FIELDS = frozenset(("projection_prefix", "projection_dir", "capabilities"))
# Removed at protocol 8: a participant address is the complete logical
# identity, so there is no actor to bind and no per-process credential.
_REMOVED_PARTICIPANT_FIELDS = ("identity", "singleton_actor", "actor", "seed")
_CAPABILITIES = frozenset(("recovery", "config"))


def validate_config(obj: Any) -> dict:
	if type(obj) is not dict:
		raise BatonError("config: top level must be an object")
	_reject_unknown(obj, _CONFIG_FIELDS, "config")
	if _expect_int(obj, "config_version", "config") != 1:
		raise BatonError("config: unsupported config_version")
	if _expect_int(obj, "protocol_version", "config") != PROTOCOL_VERSION:
		raise BatonError(f"config: protocol_version must be {PROTOCOL_VERSION}")
	_expect_int(obj, "generation", "config", minimum=1)
	mailbox = obj.get("mailbox")
	if type(mailbox) is not dict:
		raise BatonError("config: 'mailbox' must be an object")
	_reject_unknown(mailbox, _MAILBOX_FIELDS, "config.mailbox")
	_expect_str(mailbox, "name", "config.mailbox", pattern=re.compile(r"^[a-z0-9][a-z0-9_-]*$"), maxlen=64)
	participants = obj.get("participants")
	if type(participants) is not dict or not participants:
		raise BatonError("config: 'participants' must be a non-empty object")
	for address, spec in participants.items():
		where = f"config.participants[{address!r}]"
		if not ADDRESS_RE.match(address) or len(address) > 64:
			raise BatonError(f"{where}: invalid participant address")
		if type(spec) is not dict:
			raise BatonError(f"{where}: must be an object")
		# A pre-8 config is REJECTED with the reason, never silently accepted
		# with its identity fields ignored — a config that still describes
		# actors would otherwise read as enforced when nothing enforces it.
		stale = [f for f in _REMOVED_PARTICIPANT_FIELDS if f in spec]
		if stale:
			raise BatonError(
				f"{where}: {', '.join(stale)} removed at protocol {PROTOCOL_VERSION}; the "
				f"participant address is the complete identity, so there is no actor to "
				f"declare or bind")
		_reject_unknown(spec, _PARTICIPANT_FIELDS, where)
		if "capabilities" in spec:
			caps = spec["capabilities"]
			if type(caps) is not list or any(type(c) is not str for c in caps):
				raise BatonError(f"{where}: capabilities must be a list of strings")
			unknown_caps = set(caps) - _CAPABILITIES
			if unknown_caps:
				raise BatonError(f"{where}: unknown capabilities {sorted(unknown_caps)!r}")
			if len(set(caps)) != len(caps):
				raise BatonError(f"{where}: duplicate capabilities")
		if "projection_prefix" in spec:
			_expect_str(spec, "projection_prefix", where, pattern=KIND_RE, maxlen=64)
		if "projection_dir" in spec:
			_expect_str(spec, "projection_dir", where, maxlen=4096)
	roots = obj.get("roots", {})
	if type(roots) is not dict:
		raise BatonError("config: 'roots' must be an object")
	for root_id, path in roots.items():
		if not ROOT_ID_RE.match(root_id) or len(root_id) > 64:
			raise BatonError(f"config.roots: invalid root id {root_id!r}")
		if type(path) is not str or not path.startswith("/"):
			raise BatonError(f"config.roots[{root_id!r}]: must be an absolute path string")
	if "retention_days" in obj:
		_expect_int(obj, "retention_days", "config", minimum=1)
	return obj


def _read_config_at(dirfd: int, name: str) -> tuple[dict, str]:
	"""Open the config existing-only/no-follow RELATIVE to the held instance
	dirfd and read through the fd — no re-resolution window exists between
	validation and read, and the config binds to the same directory identity
	the DB is opened under."""
	try:
		fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=dirfd)
	except FileNotFoundError:
		raise BatonError(f"config not found: {name}") from None
	except OSError as exc:
		if exc.errno == errno.ELOOP:
			raise BatonError("config must not be a symlink") from exc
		raise BatonError(f"config unreadable: {exc}") from exc
	try:
		st = os.fstat(fd)
		if not stat.S_ISREG(st.st_mode):
			raise BatonError("config must be a regular file")
		with os.fdopen(fd, "rb", closefd=False) as handle:
			raw = handle.read()
	finally:
		os.close(fd)
	try:
		text = raw.decode("utf-8")
	except UnicodeDecodeError as exc:
		raise BatonError(f"config is not valid UTF-8: {exc}") from exc
	config = validate_config(loads_strict(text))
	return config, canonical_sha256(config)


def load_config(config_path: str) -> tuple[dict, str]:
	"""Validate and load the explicit config; returns (config, canonical digest)."""
	if not os.path.isabs(config_path):
		raise BatonError("config path must be absolute")
	dirfd = open_instance_dir(config_path)
	try:
		return _read_config_at(dirfd, os.path.basename(config_path))
	finally:
		os.close(dirfd)


# ---------------------------------------------------------------------------
# Filesystem anchoring
# ---------------------------------------------------------------------------

def _statfs_ftype(fd: int) -> int:
	import ctypes
	class StatFS(ctypes.Structure):
		_fields_ = [
			("f_type", ctypes.c_long), ("f_bsize", ctypes.c_long),
			("f_blocks", ctypes.c_ulong), ("f_bfree", ctypes.c_ulong),
			("f_bavail", ctypes.c_ulong), ("f_files", ctypes.c_ulong),
			("f_ffree", ctypes.c_ulong), ("f_fsid", ctypes.c_long * 2),
			("f_namelen", ctypes.c_long), ("f_frsize", ctypes.c_long),
			("f_flags", ctypes.c_long), ("f_spare", ctypes.c_long * 4),
		]
	libc = ctypes.CDLL(None, use_errno=True)
	buf = StatFS()
	if libc.fstatfs(fd, ctypes.byref(buf)) != 0:
		raise BatonError("fstatfs failed; cannot verify filesystem", EXIT_DAMAGE)
	return buf.f_type & 0xFFFFFFFF


def _open_dir_no_follow(path: str, what: str) -> int:
	"""Open a canonical absolute directory by walking EVERY component from an
	opened "/" dirfd with O_DIRECTORY|O_NOFOLLOW — no ancestor may be a
	symlink (final-component-only no-follow is not the approved boundary)."""
	if not os.path.isabs(path) or path != os.path.normpath(path):
		raise BatonError(f"{what} path {path!r} must be a canonical absolute path")
	flags = os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
	fd = os.open("/", flags)
	try:
		for component in [c for c in path.split("/") if c]:
			try:
				next_fd = os.open(component, flags, dir_fd=fd)
			except OSError as exc:
				if exc.errno in (errno.ELOOP, errno.ENOTDIR):
					raise BatonError(
						f"{what} {path!r}: component {component!r} is a symlink or not a "
						"directory; refusing", EXIT_DAMAGE) from exc
				raise BatonError(f"{what} {path!r} is not an openable directory: {exc}") from exc
			os.close(fd)
			fd = next_fd
		result, fd = fd, -1
		return result
	finally:
		if fd >= 0:
			os.close(fd)


def _open_root_dir(path: str) -> int:
	"""Configured roots are trust anchors opened via the component-walk
	no-follow authority."""
	return _open_dir_no_follow(path, "root")


def _validate_roots(config: dict) -> None:
	for root_id, path in config.get("roots", {}).items():
		os.close(_open_root_dir(path))


def open_instance_dir(config_path: str) -> int:
	if not os.path.isabs(config_path):
		raise BatonError("config path must be absolute")
	instance_dir = os.path.dirname(config_path) or "/"
	dirfd = _open_dir_no_follow(os.path.normpath(instance_dir), "instance directory")
	ftype = _statfs_ftype(dirfd)
	if ftype not in LOCAL_FS_MAGICS:
		os.close(dirfd)
		raise BatonError(f"instance directory filesystem (statfs f_type 0x{ftype:X}) is not a supported local filesystem", EXIT_DAMAGE)
	return dirfd


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_TABLES: dict[str, str] = {
	"instance_meta": (
		"CREATE TABLE instance_meta(one_row INTEGER PRIMARY KEY CHECK(one_row=1), "
		"uuid TEXT NOT NULL, protocol INTEGER NOT NULL, "
		"accepted_generation INTEGER NOT NULL CHECK(accepted_generation>=1), "
		"config_sha256 TEXT NOT NULL, "
		"maintenance INTEGER NOT NULL DEFAULT 0 CHECK(maintenance IN (0,1)), "
		"maintainer_participant TEXT, maintainer_reason TEXT, "
		"move_status TEXT NOT NULL DEFAULT 'none' CHECK(move_status IN ('none','moving','moved')), "
		"move_token TEXT, move_role TEXT CHECK(move_role IN ('source','destination')), "
		"move_peer TEXT, move_source TEXT, moved_to TEXT, created_ts TEXT NOT NULL, "
		"CHECK(NOT (move_status IN ('moving','moved') AND maintenance = 0)), "
		"CHECK((move_status = 'none') = (move_token IS NULL)), "
		"CHECK((move_status = 'none') = (move_role IS NULL)), "
		"CHECK((move_status = 'none') = (move_peer IS NULL)), "
		"CHECK((move_status = 'none') = (move_source IS NULL)), "
		"CHECK(NOT (move_status = 'moving' AND moved_to IS NOT NULL)), "
		"CHECK((move_status = 'moved') = (moved_to IS NOT NULL))) STRICT"
	),
	"op_context": (
		"CREATE TABLE op_context(one_row INTEGER PRIMARY KEY CHECK(one_row=1), "
		"op_id TEXT, participant TEXT, verb TEXT, ts TEXT) STRICT"
	),
	"contents": (
		"CREATE TABLE contents(content_id TEXT PRIMARY KEY, body BLOB NOT NULL, "
		"sha256 TEXT NOT NULL, size INTEGER NOT NULL, created_ts TEXT NOT NULL) STRICT"
	),
	# Every body is an ordered tree of parts, owned by a message, a notice, or a
	# close disposition. Part order and metadata live HERE, never as columns on
	# the owner and never as a serialized blob, so a second part -- or a nested
	# multipart/alternative -- is an insert rather than a protocol bump.
	#
	# A container part (content_type multipart/*) has children and no bytes; a
	# leaf part has bytes and no children.
	#
	# A leaf's bytes are stored INLINE (`content_id` into `contents`) or
	# EXTERNALLY (`storage='external'`, pinned by root binding, path, hash and
	# size). Protocol 9 collapsed those into one representation: an attachment
	# had always been a typed, external, hash-pinned part, but lived in five
	# columns on `messages`, was limited to one per message, was mutually
	# exclusive with content, and carried no media type. Every property the
	# parts tree provides -- ordering, typing, disposition, count, and coverage
	# by the retry manifest -- had to be built twice or not at all.
	#
	# `content_id` may go NULL on an inline leaf when a transient body is
	# scrubbed: the identity (sha256, size) survives the bytes, which is
	# exactly the transient contract.
	"parts": (
		"CREATE TABLE parts(part_id TEXT PRIMARY KEY, "
		"owner_kind TEXT NOT NULL CHECK(owner_kind IN ('message','notice','disposition')), "
		"owner_id TEXT NOT NULL, parent_part_id TEXT REFERENCES parts(part_id), "
		"ordinal INTEGER NOT NULL CHECK(ordinal >= 0), "
		"content_type TEXT NOT NULL, "
		"disposition TEXT NOT NULL CHECK(disposition IN ('inline','attachment')), "
		"part_name TEXT, "
		"storage TEXT NOT NULL CHECK(storage IN ('none','inline','external')), "
		"content_id TEXT REFERENCES contents(content_id), "
		"root_id TEXT, path TEXT, generation INTEGER, "
		"sha256 TEXT, size INTEGER, created_ts TEXT NOT NULL, "
		"CHECK(parent_part_id IS NOT part_id), "
		"CHECK((sha256 IS NULL) = (size IS NULL)), "
		"CHECK((content_type LIKE 'multipart/%') = (sha256 IS NULL)), "
		"CHECK((content_type LIKE 'multipart/%') = (storage = 'none')), "
		"CHECK(NOT (content_type LIKE 'multipart/%' "
		"AND (content_id IS NOT NULL OR part_name IS NOT NULL))), "
		"CHECK((storage = 'external') = (root_id IS NOT NULL)), "
		"CHECK((root_id IS NULL) = (path IS NULL) "
		"AND (root_id IS NULL) = (generation IS NULL)), "
		"CHECK(NOT (storage = 'external' AND content_id IS NOT NULL))) STRICT"
	),
	"messages": (
		"CREATE TABLE messages(id TEXT PRIMARY KEY, "
		"from_participant TEXT NOT NULL, to_participant TEXT NOT NULL, "
		"kind TEXT NOT NULL, subject TEXT, thread_id TEXT, "
		"retention TEXT NOT NULL CHECK(retention IN ('durable','transient')), "
		"content_type TEXT NOT NULL, manifest_sha256 TEXT NOT NULL, "
		"outcome TEXT, created_ts TEXT NOT NULL, "
		"state TEXT NOT NULL CHECK(state IN ('pending','claimed','completed','closed','expired','quarantined')), "
		"responds_to TEXT REFERENCES messages(id), completed_ts TEXT, "
		# NOT NULL, ruled 2026-08-10. Every directed message belongs to a
		# publication, and for a while that was true only because two code
		# paths both remembered to do it -- one of them did not, and `doctor`
		# could not see it. An invariant the schema states is one no future
		# author can forget. Fresh authorities only: the historical orphans
		# are archived intact rather than repaired, so nothing has to be
		# reconstructed to satisfy this.
		"publication_id TEXT NOT NULL REFERENCES publications(publication_id), "
		"CHECK((state IN ('pending','claimed')) = (completed_ts IS NULL))) STRICT"
	),
	"claims": (
		"CREATE TABLE claims(claim_id TEXT PRIMARY KEY, "
		"message_id TEXT NOT NULL REFERENCES messages(id), "
		"participant TEXT NOT NULL, claimed_ts TEXT NOT NULL, "
		"state TEXT NOT NULL CHECK(state IN ('active','completed','recovered')), "
		"terminal_ts TEXT, "
		"CHECK((state = 'active') = (terminal_ts IS NULL))) STRICT"
	),
	"dispositions": (
		"CREATE TABLE dispositions(claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id), "
		"kind TEXT NOT NULL CHECK(kind IN ('reply','close')), outcome TEXT, "
		"retention TEXT NOT NULL CHECK(retention IN ('durable','transient')), "
		"content_type TEXT, manifest_sha256 TEXT, "
		"response_message_id TEXT REFERENCES messages(id), created_ts TEXT NOT NULL, "
		"CHECK((content_type IS NULL) = (manifest_sha256 IS NULL))) STRICT"
	),
	"notices": (
		"CREATE TABLE notices(id TEXT PRIMARY KEY, from_participant TEXT NOT NULL, "
		"kind TEXT NOT NULL, subject TEXT, content_type TEXT NOT NULL, "
		"manifest_sha256 TEXT NOT NULL, created_ts TEXT NOT NULL, "
		"ttl_seconds INTEGER NOT NULL CHECK(ttl_seconds >= 1), "
		# HOW it was addressed, kept beside WHO it reached. The audience table
		# alone cannot distinguish `--scope baton.*` from a global notice that
		# happened to match the same people, and retry identity and the detail
		# header both need to tell them apart.
		"audience_kind TEXT NOT NULL CHECK(audience_kind IN ('global','scope')), "
		"selector TEXT, "
		# A broadcast can be republished after an ambiguous result just as a
		# directed message can, and the sender's warning belongs on both.
		"possible_duplicate INTEGER NOT NULL DEFAULT 0 "
		"CHECK(possible_duplicate IN (0,1)), "
		"CHECK((audience_kind = 'scope') = (selector IS NOT NULL))) STRICT"
	),
	"publications": (
		# ONE directed publication, however many recipients it addresses --
		# including one. There is no private special case: decision
		# obligations and participant-authorized reread both need a single
		# publication-time audience model, and a shape that exists only for
		# multi-recipient traffic is a shape they would have to work around.
		#
		# IDENTITY AND AUDIENCE ONLY. No delivery state lives here: claims and
		# dispositions stay on the ordinary messages, which is what keeps each
		# recipient's lifecycle independent by construction rather than by
		# care. Deriving the audience from surviving message rows would shrink
		# it as GC removes terminal deliveries, so it is recorded once.
		"CREATE TABLE publications(publication_id TEXT PRIMARY KEY, "
		"from_participant TEXT NOT NULL, kind TEXT NOT NULL, subject TEXT, "
		"thread_id TEXT, retention TEXT NOT NULL, outcome TEXT, "
		"content_type TEXT NOT NULL, manifest_sha256 TEXT NOT NULL, "
		"created_ts TEXT NOT NULL, "
		# The SENDER's assertion that they could not tell whether an earlier
		# attempt committed. Publication is at-least-once by ruling: Baton does
		# NOT claim to have identified or correlated the original, and the
		# recipient decides what to do about it.
		"possible_duplicate INTEGER NOT NULL DEFAULT 0 "
		"CHECK(possible_duplicate IN (0,1))) STRICT"
	),
	"publication_audience": (
		"CREATE TABLE publication_audience(publication_id TEXT NOT NULL "
		"REFERENCES publications(publication_id) ON DELETE CASCADE, "
		"participant TEXT NOT NULL, "
		"PRIMARY KEY (publication_id, participant)) STRICT, WITHOUT ROWID"
	),
	"notice_audience": (
		# The audience FROZEN at publication. Ruled: a broadcast is to the
		# participants who existed when it was sent, global and scoped alike,
		# so a config addition cannot grant a new identity access to historic
		# broadcast content.
		#
		# One immutable mechanism rather than a global special case that
		# re-evaluates live config -- which is also the difference between an
		# audience you can audit and one you have to reconstruct.
		"CREATE TABLE notice_audience(notice_id TEXT NOT NULL "
		"REFERENCES notices(id) ON DELETE CASCADE, "
		"participant TEXT NOT NULL, "
		"PRIMARY KEY (notice_id, participant)) STRICT, WITHOUT ROWID"
	),
	"notice_seen": (
		# The composite reference is the point: a receipt may only exist for a
		# participant who is IN that notice's frozen audience. Authorization
		# lives in the schema as well as in the code path, so a future reader
		# cannot recreate the bypass by adding another query.
		"CREATE TABLE notice_seen(notice_id TEXT NOT NULL REFERENCES notices(id) ON DELETE CASCADE, "
		"participant TEXT NOT NULL, seen_ts TEXT NOT NULL, "
		"PRIMARY KEY(notice_id, participant), "
		"FOREIGN KEY(notice_id, participant) "
		"REFERENCES notice_audience(notice_id, participant) ON DELETE CASCADE) STRICT"
	),
	"quarantines": (
		"CREATE TABLE quarantines(quarantine_id TEXT PRIMARY KEY, "
		"message_id TEXT NOT NULL UNIQUE REFERENCES messages(id), "
		"participant TEXT NOT NULL, reason TEXT NOT NULL, prior_state TEXT NOT NULL, "
		"part_id TEXT NOT NULL, part_ordinal TEXT NOT NULL, "
		"content_type TEXT NOT NULL, "
		"root_id TEXT NOT NULL, path TEXT NOT NULL, "
		"sha256 TEXT NOT NULL, size INTEGER NOT NULL, generation INTEGER NOT NULL, "
		"failure TEXT NOT NULL, created_ts TEXT NOT NULL) STRICT"
	),
	"recoveries": (
		"CREATE TABLE recoveries(recovery_id TEXT PRIMARY KEY, "
		"claim_id TEXT NOT NULL REFERENCES claims(claim_id), "
		"participant TEXT NOT NULL, reason TEXT NOT NULL, created_ts TEXT NOT NULL) STRICT"
	),
	"ceremonies": (
		"CREATE TABLE ceremonies(ceremony_id TEXT PRIMARY KEY, "
		"kind TEXT NOT NULL CHECK(kind IN ('maintenance_enter','maintenance_exit',"
		"'move_bind_destination','move_activate','move_decommission','abort_move','migrate')), "
		"participant TEXT NOT NULL, reason TEXT, token TEXT, peer TEXT, "
		"created_ts TEXT NOT NULL) STRICT"
	),
	"moves": (
		"CREATE TABLE moves(token TEXT PRIMARY KEY, instance_uuid TEXT NOT NULL, "
		"source_config TEXT NOT NULL, source_dev INTEGER NOT NULL, source_ino INTEGER NOT NULL, "
		"destination_config TEXT NOT NULL, destination_dev INTEGER NOT NULL, "
		"destination_ino INTEGER NOT NULL, created_ts TEXT NOT NULL) STRICT"
	),
	"accepted_roots": (
		"CREATE TABLE accepted_roots(root_id TEXT PRIMARY KEY, path TEXT NOT NULL, "
		"binding_generation INTEGER NOT NULL CHECK(binding_generation>=1)) STRICT"
	),
	"transitions": (
		"CREATE TABLE transitions(seq INTEGER PRIMARY KEY AUTOINCREMENT, "
		"entity TEXT NOT NULL CHECK(entity IN ('message','claim')), "
		"entity_id TEXT NOT NULL, from_state TEXT, to_state TEXT NOT NULL, "
		"op_id TEXT NOT NULL, participant TEXT, "
		"verb TEXT NOT NULL, at_ts TEXT NOT NULL) STRICT"
	),
}

_INDEXES: dict[str, str] = {
	"contents_sha_idx": "CREATE INDEX contents_sha_idx ON contents(sha256)",
	"messages_dest_idx": "CREATE INDEX messages_dest_idx ON messages(to_participant, state)",
	"messages_thread_idx": "CREATE INDEX messages_thread_idx ON messages(thread_id)",
	"claims_one_active_idx": "CREATE UNIQUE INDEX claims_one_active_idx ON claims(message_id) WHERE state='active'",
	"claims_message_idx": "CREATE INDEX claims_message_idx ON claims(message_id)",
	# Two PARTIAL unique indexes rather than one composite: SQLite treats NULLs
	# as distinct in a UNIQUE constraint, so a single index over
	# (owner, parent_part_id, ordinal) would leave top-level ordinals -- the
	# ones with a NULL parent -- entirely unconstrained. Order is enforced at
	# both levels or it is enforced nowhere.
	"parts_root_order_idx": (
		"CREATE UNIQUE INDEX parts_root_order_idx ON parts(owner_kind, owner_id, ordinal) "
		"WHERE parent_part_id IS NULL"),
	"parts_child_order_idx": (
		"CREATE UNIQUE INDEX parts_child_order_idx ON parts(parent_part_id, ordinal) "
		"WHERE parent_part_id IS NOT NULL"),
	"parts_owner_idx": "CREATE INDEX parts_owner_idx ON parts(owner_kind, owner_id)",
}

_CTX = "(SELECT op_id FROM op_context WHERE one_row=1)"
_CTX_PART = "(SELECT participant FROM op_context WHERE one_row=1)"
_CTX_VERB = "(SELECT verb FROM op_context WHERE one_row=1)"
_CTX_TS = "(SELECT ts FROM op_context WHERE one_row=1)"

_TRIGGERS: dict[str, str] = {
	"trg_msg_insert_guard": (
		f"CREATE TRIGGER trg_msg_insert_guard BEFORE INSERT ON messages "
		f"WHEN {_CTX} IS NULL OR new.state <> 'pending' "
		f"BEGIN SELECT RAISE(ABORT, 'message insert requires operation context and pending birth'); END"
	),
	"trg_msg_birth": (
		f"CREATE TRIGGER trg_msg_birth AFTER INSERT ON messages "
		f"BEGIN INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, participant, verb, at_ts) "
		f"VALUES('message', new.id, NULL, new.state, {_CTX}, {_CTX_PART}, {_CTX_VERB}, {_CTX_TS}); END"
	),
	"trg_msg_update_guard": (
		f"CREATE TRIGGER trg_msg_update_guard BEFORE UPDATE OF state ON messages "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'uncontextual message state mutation'); END"
	),
	"trg_msg_edge": (
		# The quarantined edge carries its authorizing verb IN the guard: a
		# transaction running any other verb cannot manufacture a quarantined
		# message, so "explicit audited recovery" holds at the schema
		# boundary rather than only in the Python that normally calls it.
		f"CREATE TRIGGER trg_msg_edge BEFORE UPDATE OF state ON messages "
		f"WHEN NOT ((old.state='pending' AND new.state='claimed') "
		f"OR (old.state='claimed' AND new.state IN ('completed','closed','pending')) "
		f"OR (old.state='pending' AND new.state='quarantined' "
		f"AND {_CTX_VERB} IS 'quarantine')) "
		f"BEGIN SELECT RAISE(ABORT, 'illegal message state edge (quarantine requires its own verb)'); END"
	),
	"trg_msg_transition": (
		f"CREATE TRIGGER trg_msg_transition AFTER UPDATE OF state ON messages "
		f"BEGIN INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, participant, verb, at_ts) "
		f"VALUES('message', new.id, old.state, new.state, {_CTX}, {_CTX_PART}, {_CTX_VERB}, {_CTX_TS}); END"
	),
	"trg_msg_frozen_cols": (
		"CREATE TRIGGER trg_msg_frozen_cols BEFORE UPDATE OF id, from_participant, to_participant, kind, "
		"subject, thread_id, retention, content_type, manifest_sha256, "
		"outcome, created_ts, responds_to ON messages "
		"BEGIN SELECT RAISE(ABORT, 'immutable message column'); END"
	),
	"trg_msg_completed_ts_guard": (
		"CREATE TRIGGER trg_msg_completed_ts_guard BEFORE UPDATE OF completed_ts ON messages "
		"WHEN NOT ((old.state='claimed' AND new.state IN ('completed','closed') AND new.completed_ts IS NOT NULL) "
		"OR (old.state='claimed' AND new.state='pending' AND new.completed_ts IS NULL) "
		"OR (old.state='pending' AND new.state='quarantined' AND new.completed_ts IS NOT NULL)) "
		"BEGIN SELECT RAISE(ABORT, 'completed_ts changes only with its own terminal transition'); END"
	),
	"trg_claim_terminal_ts_guard": (
		"CREATE TRIGGER trg_claim_terminal_ts_guard BEFORE UPDATE OF terminal_ts ON claims "
		"WHEN NOT (old.state='active' AND new.state IN ('completed','recovered') AND new.terminal_ts IS NOT NULL) "
		"BEGIN SELECT RAISE(ABORT, 'terminal_ts changes only with its own terminal transition'); END"
	),
	"trg_claim_insert_guard": (
		f"CREATE TRIGGER trg_claim_insert_guard BEFORE INSERT ON claims "
		f"WHEN {_CTX} IS NULL OR new.state <> 'active' "
		f"BEGIN SELECT RAISE(ABORT, 'claim insert requires operation context and active birth'); END"
	),
	"trg_claim_birth": (
		f"CREATE TRIGGER trg_claim_birth AFTER INSERT ON claims "
		f"BEGIN INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, participant, verb, at_ts) "
		f"VALUES('claim', new.claim_id, NULL, new.state, {_CTX}, {_CTX_PART}, {_CTX_VERB}, {_CTX_TS}); END"
	),
	"trg_claim_update_guard": (
		f"CREATE TRIGGER trg_claim_update_guard BEFORE UPDATE OF state ON claims "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'uncontextual claim state mutation'); END"
	),
	"trg_claim_edge": (
		"CREATE TRIGGER trg_claim_edge BEFORE UPDATE OF state ON claims "
		"WHEN NOT (old.state='active' AND new.state IN ('completed','recovered')) "
		"BEGIN SELECT RAISE(ABORT, 'illegal claim state edge'); END"
	),
	"trg_claim_transition": (
		f"CREATE TRIGGER trg_claim_transition AFTER UPDATE OF state ON claims "
		f"BEGIN INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, participant, verb, at_ts) "
		f"VALUES('claim', new.claim_id, old.state, new.state, {_CTX}, {_CTX_PART}, {_CTX_VERB}, {_CTX_TS}); END"
	),
	"trg_claim_frozen_cols": (
		"CREATE TRIGGER trg_claim_frozen_cols BEFORE UPDATE OF claim_id, message_id, participant, claimed_ts ON claims "
		"BEGIN SELECT RAISE(ABORT, 'immutable claim column'); END"
	),
	"trg_disp_insert_guard": (
		f"CREATE TRIGGER trg_disp_insert_guard BEFORE INSERT ON dispositions "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'disposition insert requires operation context'); END"
	),
	# A reply's disposition and its response message describe the SAME content,
	# so the manifest digests must agree. Under multipart this covers part
	# order, media types, dispositions and part names -- not only the bytes.
	"trg_disp_reply_hash": (
		"CREATE TRIGGER trg_disp_reply_hash BEFORE INSERT ON dispositions "
		"WHEN new.kind='reply' AND (new.response_message_id IS NULL "
		"OR new.manifest_sha256 IS NOT (SELECT manifest_sha256 FROM messages WHERE id=new.response_message_id) "
		"OR new.content_type IS NOT (SELECT content_type FROM messages WHERE id=new.response_message_id)) "
		"BEGIN SELECT RAISE(ABORT, 'reply disposition content manifest mismatch'); END"
	),
	"trg_parts_insert_guard": (
		f"CREATE TRIGGER trg_parts_insert_guard BEFORE INSERT ON parts "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'part insert requires operation context'); END"
	),
	"trg_parts_frozen_cols": (
		"CREATE TRIGGER trg_parts_frozen_cols BEFORE UPDATE OF part_id, owner_kind, owner_id, "
		"parent_part_id, ordinal, content_type, disposition, part_name, storage, "
		"root_id, path, generation, sha256, size, created_ts ON parts "
		"BEGIN SELECT RAISE(ABORT, 'immutable part column'); END"
	),
	# The part-level successor to the message content scrub guard: dropping the
	# bytes of a terminal transient message is the ONLY permitted content_id
	# mutation, and the owning message must actually be transient and terminal.
	"trg_parts_scrub_only": (
		f"CREATE TRIGGER trg_parts_scrub_only BEFORE UPDATE OF content_id ON parts "
		f"WHEN new.content_id IS NOT NULL OR old.content_id IS NULL "
		f"OR old.storage IS NOT 'inline' "
		f"OR old.owner_kind IS NOT 'message' "
		f"OR NOT EXISTS(SELECT 1 FROM messages m WHERE m.id = old.owner_id "
		f"AND m.retention='transient' AND m.state IN ('completed','closed')) "
		f"OR {_CTX} IS NULL OR {_CTX_VERB} NOT IN ('reply','close','gc') "
		f"BEGIN SELECT RAISE(ABORT, 'scrub is restricted to a terminal transient message part in a consuming operation'); END"
	),
	"trg_parts_delete_guard": (
		f"CREATE TRIGGER trg_parts_delete_guard BEFORE DELETE ON parts "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('gc','expire') "
		f"BEGIN SELECT RAISE(ABORT, 'parts are removable only by gc or expire'); END"
	),
	"trg_disp_update": (
		"CREATE TRIGGER trg_disp_update BEFORE UPDATE ON dispositions "
		"BEGIN SELECT RAISE(ABORT, 'dispositions are immutable'); END"
	),
	"trg_disp_delete": (
		f"CREATE TRIGGER trg_disp_delete BEFORE DELETE ON dispositions "
		f"WHEN {_CTX_VERB} IS NOT 'gc' "
		f"BEGIN SELECT RAISE(ABORT, 'dispositions are removable only by gc'); END"
	),
	"trg_content_update": (
		"CREATE TRIGGER trg_content_update BEFORE UPDATE ON contents "
		"BEGIN SELECT RAISE(ABORT, 'contents are immutable'); END"
	),
	"trg_content_delete": (
		f"CREATE TRIGGER trg_content_delete BEFORE DELETE ON contents "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('reply','close','gc','expire') "
		f"BEGIN SELECT RAISE(ABORT, 'content deletion restricted to retention operations'); END"
	),
	"trg_msg_delete_guard": (
		f"CREATE TRIGGER trg_msg_delete_guard BEFORE DELETE ON messages "
		f"WHEN {_CTX_VERB} IS NOT 'gc' "
		f"BEGIN SELECT RAISE(ABORT, 'messages are removable only by gc'); END"
	),
	"trg_msg_gc_ledger": (
		f"CREATE TRIGGER trg_msg_gc_ledger AFTER DELETE ON messages "
		f"BEGIN INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, participant, verb, at_ts) "
		f"VALUES('message', old.id, old.state, 'gc', {_CTX}, {_CTX_PART}, {_CTX_VERB}, {_CTX_TS}); END"
	),
	"trg_claim_delete_guard": (
		f"CREATE TRIGGER trg_claim_delete_guard BEFORE DELETE ON claims "
		f"WHEN {_CTX_VERB} IS NOT 'gc' "
		f"BEGIN SELECT RAISE(ABORT, 'claims are removable only by gc'); END"
	),
	"trg_claim_gc_ledger": (
		f"CREATE TRIGGER trg_claim_gc_ledger AFTER DELETE ON claims "
		f"BEGIN INSERT INTO transitions(entity, entity_id, from_state, to_state, op_id, participant, verb, at_ts) "
		f"VALUES('claim', old.claim_id, old.state, 'gc', {_CTX}, {_CTX_PART}, {_CTX_VERB}, {_CTX_TS}); END"
	),
	"trg_notice_insert_guard": (
		f"CREATE TRIGGER trg_notice_insert_guard BEFORE INSERT ON notices "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'notice insert requires operation context'); END"
	),
	"trg_notice_frozen": (
		"CREATE TRIGGER trg_notice_frozen BEFORE UPDATE ON notices "
		"BEGIN SELECT RAISE(ABORT, 'notices are immutable'); END"
	),
	"trg_notice_seen_guard": (
		f"CREATE TRIGGER trg_notice_seen_guard BEFORE INSERT ON notice_seen "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'notice_seen insert requires operation context'); END"
	),
	"trg_notice_seen_update": (
		"CREATE TRIGGER trg_notice_seen_update BEFORE UPDATE ON notice_seen "
		"BEGIN SELECT RAISE(ABORT, 'notice_seen receipts are immutable'); END"
	),
	"trg_notice_seen_delete": (
		f"CREATE TRIGGER trg_notice_seen_delete BEFORE DELETE ON notice_seen "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('expire','gc') "
		f"BEGIN SELECT RAISE(ABORT, 'notice_seen receipts are removable only by expire or gc'); END"
	),
	"trg_publication_guard": (
		f"CREATE TRIGGER trg_publication_guard BEFORE INSERT ON publications "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'publication insert requires operation context'); END"
	),
	"trg_publication_frozen": (
		# Immutable, including `possible_duplicate`: it is the sender's
		# assertion at publication time, and one that can be set or cleared
		# afterwards is a rumour rather than a record.
		"CREATE TRIGGER trg_publication_frozen BEFORE UPDATE ON publications "
		"BEGIN SELECT RAISE(ABORT, 'publications are immutable'); END"
	),
	"trg_publication_delete": (
		f"CREATE TRIGGER trg_publication_delete BEFORE DELETE ON publications "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('gc') "
		f"BEGIN SELECT RAISE(ABORT, 'publications are removable only by gc'); END"
	),
	"trg_publication_audience_guard": (
		f"CREATE TRIGGER trg_publication_audience_guard BEFORE INSERT ON publication_audience "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'publication audience insert requires operation context'); END"
	),
	"trg_publication_audience_update": (
		"CREATE TRIGGER trg_publication_audience_update BEFORE UPDATE ON publication_audience "
		"BEGIN SELECT RAISE(ABORT, 'publication audiences are immutable'); END"
	),
	"trg_publication_audience_delete": (
		f"CREATE TRIGGER trg_publication_audience_delete BEFORE DELETE ON publication_audience "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('gc') "
		f"BEGIN SELECT RAISE(ABORT, 'publication audiences are removable only by gc'); END"
	),
	"trg_notice_audience_guard": (
		f"CREATE TRIGGER trg_notice_audience_guard BEFORE INSERT ON notice_audience "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'notice_audience insert requires operation context'); END"
	),
	"trg_notice_audience_update": (
		# IMMUTABLE. The audience is the record of who a broadcast was
		# addressed to; a row that can be edited afterwards is not that
		# record. Nothing legitimate ever needs to change one -- membership is
		# decided once, inside the publishing transaction.
		"CREATE TRIGGER trg_notice_audience_update BEFORE UPDATE ON notice_audience "
		"BEGIN SELECT RAISE(ABORT, 'notice audiences are immutable'); END"
	),
	"trg_notice_audience_delete": (
		# Removable only with the notice itself, by the two ceremonies that may
		# remove notices. Deleting a membership row on its own would silently
		# shrink history and make a delivered notice look like it had never
		# been addressed to that participant.
		f"CREATE TRIGGER trg_notice_audience_delete BEFORE DELETE ON notice_audience "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('expire','gc') "
		f"BEGIN SELECT RAISE(ABORT, 'notice audiences are removable only by expire or gc'); END"
	),
	"trg_quarantine_insert_guard": (
		f"CREATE TRIGGER trg_quarantine_insert_guard BEFORE INSERT ON quarantines "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} IS NOT 'quarantine' "
		f"BEGIN SELECT RAISE(ABORT, 'quarantine records are written only by the quarantine ceremony'); END"
	),
	"trg_quarantine_frozen": (
		"CREATE TRIGGER trg_quarantine_frozen BEFORE UPDATE ON quarantines "
		"BEGIN SELECT RAISE(ABORT, 'quarantine records are immutable'); END"
	),
	"trg_quarantine_delete_guard": (
		"CREATE TRIGGER trg_quarantine_delete_guard BEFORE DELETE ON quarantines "
		"BEGIN SELECT RAISE(ABORT, 'quarantine records are permanent audit'); END"
	),
	"trg_recoveries_insert_guard": (
		f"CREATE TRIGGER trg_recoveries_insert_guard BEFORE INSERT ON recoveries "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'recovery insert requires operation context'); END"
	),
	"trg_notice_delete_guard": (
		f"CREATE TRIGGER trg_notice_delete_guard BEFORE DELETE ON notices "
		f"WHEN {_CTX_VERB} IS NULL OR {_CTX_VERB} NOT IN ('expire','gc') "
		f"BEGIN SELECT RAISE(ABORT, 'notices are removable only by expire or gc'); END"
	),
	"trg_transitions_update": (
		"CREATE TRIGGER trg_transitions_update BEFORE UPDATE ON transitions "
		"BEGIN SELECT RAISE(ABORT, 'transition ledger is append-only'); END"
	),
	"trg_transitions_delete": (
		"CREATE TRIGGER trg_transitions_delete BEFORE DELETE ON transitions "
		"BEGIN SELECT RAISE(ABORT, 'transition ledger is append-only'); END"
	),
	"trg_accepted_roots_guard_ins": (
		f"CREATE TRIGGER trg_accepted_roots_guard_ins BEFORE INSERT ON accepted_roots "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} IS NOT 'regen' "
		f"BEGIN SELECT RAISE(ABORT, 'accepted roots change only under regen'); END"
	),
	"trg_accepted_roots_guard_upd": (
		f"CREATE TRIGGER trg_accepted_roots_guard_upd BEFORE UPDATE ON accepted_roots "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} IS NOT 'regen' "
		f"BEGIN SELECT RAISE(ABORT, 'accepted roots change only under regen'); END"
	),
	"trg_accepted_roots_guard_del": (
		f"CREATE TRIGGER trg_accepted_roots_guard_del BEFORE DELETE ON accepted_roots "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} IS NOT 'regen' "
		f"BEGIN SELECT RAISE(ABORT, 'accepted roots change only under regen'); END"
	),
	"trg_moves_insert_guard": (
		f"CREATE TRIGGER trg_moves_insert_guard BEFORE INSERT ON moves "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} IS NOT 'move_enter' "
		f"BEGIN SELECT RAISE(ABORT, 'move bindings are created only by move entry'); END"
	),
	"trg_moves_update": (
		"CREATE TRIGGER trg_moves_update BEFORE UPDATE ON moves "
		"BEGIN SELECT RAISE(ABORT, 'move bindings are immutable'); END"
	),
	"trg_moves_delete": (
		"CREATE TRIGGER trg_moves_delete BEFORE DELETE ON moves "
		"BEGIN SELECT RAISE(ABORT, 'move bindings are immutable'); END"
	),
	"trg_meta_frozen": (
		"CREATE TRIGGER trg_meta_frozen BEFORE UPDATE OF one_row, uuid, created_ts "
		"ON instance_meta BEGIN SELECT RAISE(ABORT, 'instance identity is immutable'); END"
	),
	"trg_meta_protocol_guard": (
		# The protocol field was previously immutable, which made an in-place
		# schema migration impossible without dropping a guard. It now changes
		# under exactly one verb, so migration is expressible without ever
		# disarming the schema's own protection.
		# Constrained to a SINGLE forward step as well as to the verb: a
		# migration that skipped versions, or ran backwards, would be a
		# different operation than the one this tool knows how to perform.
		f"CREATE TRIGGER trg_meta_protocol_guard BEFORE UPDATE OF protocol ON instance_meta "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} IS NOT 'migrate' "
		f"OR new.protocol IS NOT old.protocol + 1 "
		f"BEGIN SELECT RAISE(ABORT, 'protocol advances one step, only under an audited migration'); END"
	),
	"trg_meta_config_guard": (
		f"CREATE TRIGGER trg_meta_config_guard BEFORE UPDATE OF accepted_generation, config_sha256 "
		f"ON instance_meta WHEN {_CTX} IS NULL OR {_CTX_VERB} NOT IN ('regen','migrate') "
		f"BEGIN SELECT RAISE(ABORT, 'config acceptance changes only under regen/migrate'); END"
	),
	"trg_meta_gate_guard": (
		f"CREATE TRIGGER trg_meta_gate_guard BEFORE UPDATE OF maintenance, move_status, move_token, "
		f"move_role, move_peer, move_source, moved_to, maintainer_participant, maintainer_reason ON instance_meta "
		f"WHEN {_CTX} IS NULL OR {_CTX_VERB} NOT IN ('maintenance','move','move_enter') "
		f"BEGIN SELECT RAISE(ABORT, 'gate/move state changes only under an authorized ceremony'); END"
	),
	"trg_meta_move_edge": (
		"CREATE TRIGGER trg_meta_move_edge BEFORE UPDATE OF move_status ON instance_meta "
		"WHEN old.move_status IS NOT new.move_status AND NOT ("
		"(old.move_status='none' AND new.move_status='moving') "
		"OR (old.move_status='moving' AND new.move_status IN ('none','moved'))) "
		"BEGIN SELECT RAISE(ABORT, 'illegal move_status edge'); END"
	),
	"trg_ceremonies_insert_guard": (
		f"CREATE TRIGGER trg_ceremonies_insert_guard BEFORE INSERT ON ceremonies "
		f"WHEN {_CTX} IS NULL "
		f"BEGIN SELECT RAISE(ABORT, 'ceremony insert requires operation context'); END"
	),
	"trg_ceremonies_update": (
		"CREATE TRIGGER trg_ceremonies_update BEFORE UPDATE ON ceremonies "
		"BEGIN SELECT RAISE(ABORT, 'ceremony records are immutable'); END"
	),
	"trg_ceremonies_delete": (
		"CREATE TRIGGER trg_ceremonies_delete BEFORE DELETE ON ceremonies "
		"BEGIN SELECT RAISE(ABORT, 'ceremony records are immutable'); END"
	),
	"trg_recoveries_update": (
		"CREATE TRIGGER trg_recoveries_update BEFORE UPDATE ON recoveries "
		"BEGIN SELECT RAISE(ABORT, 'recovery records are immutable'); END"
	),
	"trg_recoveries_delete": (
		"CREATE TRIGGER trg_recoveries_delete BEFORE DELETE ON recoveries "
		"BEGIN SELECT RAISE(ABORT, 'recovery records are immutable'); END"
	),
}


def _expected_schema() -> dict[tuple[str, str], str]:
	expected: dict[tuple[str, str], str] = {}
	for name, sql in _TABLES.items():
		expected[("table", name)] = sql
	for name, sql in _INDEXES.items():
		expected[("index", name)] = sql
	for name, sql in _TRIGGERS.items():
		expected[("trigger", name)] = sql
	return expected


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def _sql_limit(limit: int | None) -> int:
	"""SQLite has no "no limit" literal; -1 is the documented way to say it."""
	return -1 if limit is None else int(limit)


class Store:
	"""One open handle on an instance at the supported protocol. Not
	thread-safe."""

	def __init__(self, config_path: str, config: dict, config_digest: str,
	             dirfd: int, dbfd: int, conn: sqlite3.Connection, readonly: bool) -> None:
		self.config_path = config_path
		self.config = config
		self.config_digest = config_digest
		self.dirfd = dirfd
		self.dbfd = dbfd
		self.conn = conn
		self.readonly = readonly

	def close(self) -> None:
		try:
			self.conn.close()
		finally:
			for fd in (self.dbfd, self.dirfd):
				try:
					os.close(fd)
				except OSError:
					pass

	def __enter__(self) -> "Store":
		return self

	def __exit__(self, *exc: Any) -> None:
		self.close()

	# -- transaction discipline --------------------------------------------

	def _txn_begin(self, verb: str, *, participant: str | None = None,
	               ceremony: str | None = None) -> str:
		"""Open a write transaction: BEGIN IMMEDIATE, then re-read and enforce
		the instance gates against THIS handle's config (open-time checks are
		not sufficient — another process may have set maintenance, moved the
		instance, or accepted a new config since open), then set the operation
		context. Any failure after BEGIN rolls back — a Store never strands an
		open transaction."""
		if self.readonly:
			raise BatonError("read-only store cannot execute write operations")
		op_id = new_id()
		try:
			self.conn.execute("BEGIN IMMEDIATE")
		except sqlite3.OperationalError as exc:
			raise BatonError(f"store is busy: {exc}", EXIT_RACE) from exc
		try:
			self._enforce_gates_in_txn(ceremony)
			self.conn.execute(
				"UPDATE op_context SET op_id=?, participant=?, verb=?, ts=? WHERE one_row=1",
				(op_id, participant, verb, _utc_now_iso()))
			return op_id
		except BaseException as exc:
			self._txn_rollback()
			if isinstance(exc, BatonError):
				raise
			if isinstance(exc, sqlite3.OperationalError):
				raise BatonError(f"store is busy: {exc}", EXIT_RACE) from exc
			if isinstance(exc, sqlite3.Error):
				raise BatonError(f"transaction begin failed: {exc}", EXIT_DAMAGE) from exc
			raise

	def _enforce_gates_in_txn(self, ceremony: str | None) -> None:
		row = self.conn.execute(
			"SELECT protocol, accepted_generation, config_sha256, maintenance, move_status, moved_to "
			"FROM instance_meta WHERE one_row=1").fetchone()
		if row is None:
			raise BatonError("instance_meta row is missing", EXIT_DAMAGE)
		if row["protocol"] != PROTOCOL_VERSION:
			raise BatonError(f"instance protocol {row['protocol']} unsupported", EXIT_PROTOCOL)
		if row["move_status"] == "moved" and ceremony != "move":
			raise BatonError(f"instance has moved to {row['moved_to']!r}; refusing", EXIT_GATED)
		# Quarantine is authorized DURING a plain maintenance gate — the whole
		# point is to repair instance health in the same quiet window as a
		# migration, before reopening to participants. It is emphatically not
		# authorized during a move: a half-copied instance must not acquire
		# dispositions its peer will never see.
		if ceremony == "quarantine" and row["move_status"] != "none":
			raise BatonError(
				f"instance move is {row['move_status']!r}; quarantine is refused during a move",
				EXIT_GATED)
		if row["maintenance"] == 1 and ceremony not in (
				"move", "migrate", "maintenance", "quarantine"):
			raise BatonError("instance is under maintenance; write operations are gated", EXIT_GATED)
		if ceremony == "regen":
			if row["accepted_generation"] != self.config["generation"] - 1:
				raise BatonError(
					f"regen race: accepted generation is now {row['accepted_generation']}, "
					f"offered {self.config['generation']}", EXIT_RACE)
		elif (row["accepted_generation"] != self.config["generation"]
				or row["config_sha256"] != self.config_digest):
			raise BatonError(
				"this handle's config is stale (the instance accepted a newer config); reopen",
				EXIT_GATED)

	def _txn_commit(self) -> None:
		self.conn.execute(
			"UPDATE op_context SET op_id=NULL, participant=NULL, verb=NULL, ts=NULL WHERE one_row=1")
		self.conn.execute("COMMIT")

	def _txn_rollback(self) -> None:
		try:
			self.conn.execute("ROLLBACK")
		except sqlite3.OperationalError:
			pass

	# -- participant identity ----------------------------------------------

	def _check_participant(self, address: str, where: str) -> dict:
		spec = self.config["participants"].get(address)
		if spec is None:
			raise BatonError(f"{where}: participant {address!r} is not declared in the config")
		return spec

	def _validate_route_identity(self, route_config: str, bound_dev: int, bound_ino: int,
	                             what: str) -> None:
		"""The ONLY residence predicate: a route passes when (a) it is the
		canonical committed path, (b) opening its parent via the component
		walk (never following a symlink) yields exactly the directory
		identity bound at maintenance_enter, (c) THIS Store's held dirfd has
		that same identity, and (d) the config basename matches. Pathname
		stats that follow symlinks are banned from this class of check."""
		if not os.path.isabs(route_config) or route_config != os.path.normpath(route_config):
			raise BatonError(f"{what}: committed route is not canonical", EXIT_DAMAGE)
		if self.config_path != route_config:
			raise BatonError(
				f"{what}: this handle's config path {self.config_path!r} is not the exact "
				f"committed route {route_config!r}; alternate spellings are refused, never "
				"normalized", EXIT_DAMAGE)
		fd = _open_dir_no_follow(os.path.dirname(route_config), what)
		try:
			opened = os.fstat(fd)
		finally:
			os.close(fd)
		if (opened.st_dev, opened.st_ino) != (bound_dev, bound_ino):
			raise BatonError(
				f"{what}: the route's directory identity does not match the identity bound "
				"at maintenance_enter (replaced, renamed, or symlinked)", EXIT_DAMAGE)
		own = os.fstat(self.dirfd)
		if (own.st_dev, own.st_ino) != (bound_dev, bound_ino):
			raise BatonError(
				f"{what}: this instance does not physically reside at the bound directory",
				EXIT_DAMAGE)
		if os.path.basename(route_config) != os.path.basename(self.config_path):
			raise BatonError(f"{what}: config basename does not match the bound route", EXIT_DAMAGE)

	def _move_binding(self, token: str) -> sqlite3.Row:
		row = self.conn.execute("SELECT * FROM moves WHERE token=?", (token,)).fetchone()
		if row is None:
			raise BatonError("no immutable move binding exists for this token", EXIT_DAMAGE)
		uuid = self.conn.execute("SELECT uuid FROM instance_meta WHERE one_row=1").fetchone()[0]
		if row["instance_uuid"] != uuid:
			raise BatonError(
				"move binding names a different instance uuid; refusing (corruption)", EXIT_DAMAGE)
		return row

	def _require_capability(self, address: str, capability: str, what: str) -> None:
		"""Administrative authority is an EXPLICIT config declaration, never
		inferred from endpoint cardinality: the participant must carry the
		named capability in addition to ordinary identity validation. The
		host deployment decides which endpoint holds it."""
		self._check_identity(address)
		caps = self.config["participants"][address].get("capabilities", [])
		if capability not in caps:
			raise BatonError(
				f"{what} requires the {capability!r} capability, which {address!r} does not hold")

	def _check_identity(self, address: str) -> dict:
		"""The participant address IS the identity. There is no second factor
		to validate: a caller either names a configured participant or does
		not. Trust that the caller is who it says is the deployment's, not
		Baton's — filesystem access to the instance is the boundary."""
		return self._check_participant(address, "identity check")

	# -- operations ---------------------------------------------------------

	def _resolve_attachment(self, attach: Any) -> tuple[str, str, str, int]:
		"""Resolve and hash-pin a separately authored evidence file under a
		configured root with component-wise no-follow containment. Returns
		(root_id, rel_path, sha256, size)."""
		if type(attach) is not dict or set(attach) != {"root_id", "path"}:
			raise BatonError("attachment must be {'root_id': ..., 'path': ...}")
		root_id = attach["root_id"]
		rel_path = attach["path"]
		if type(root_id) is not str or type(rel_path) is not str:
			raise BatonError("attachment root_id and path must be strings")
		root = self.config.get("roots", {}).get(root_id)
		if root is None:
			raise BatonError(f"attachment root {root_id!r} is not declared in the config")
		parts = rel_path.split("/")
		if rel_path.startswith("/") or any(p in ("", ".", "..") for p in parts):
			raise BatonError(f"attachment path {rel_path!r} must be a clean relative path")
		fd = _open_root_dir(root)
		try:
			for component in parts[:-1]:
				next_fd = os.open(component, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
				os.close(fd)
				fd = next_fd
			try:
				leaf = os.open(parts[-1],
				               os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=fd)
			except OSError as exc:
				if exc.errno == errno.ELOOP:
					raise BatonError(f"attachment {rel_path!r} is a symlink; refusing", EXIT_DAMAGE) from exc
				raise BatonError(f"attachment {rel_path!r} unreadable: {exc}") from exc
			try:
				st_before = os.fstat(leaf)
				if not stat.S_ISREG(st_before.st_mode):
					raise BatonError(f"attachment {rel_path!r} is not a regular file")
				hasher = hashlib.sha256()
				with os.fdopen(leaf, "rb", closefd=False) as handle:
					for chunk in iter(lambda: handle.read(1 << 20), b""):
						hasher.update(chunk)
				_fault("attach:post-hash")
				st_after = os.fstat(leaf)
				before_id = (st_before.st_dev, st_before.st_ino, st_before.st_mode,
				             st_before.st_size, st_before.st_mtime_ns, st_before.st_ctime_ns)
				after_id = (st_after.st_dev, st_after.st_ino, st_after.st_mode,
				            st_after.st_size, st_after.st_mtime_ns, st_after.st_ctime_ns)
				if before_id != after_id:
					raise BatonError(
						f"attachment {rel_path!r} changed while being hashed; refusing the "
						"ambiguous snapshot", EXIT_DAMAGE)
				return root_id, rel_path, hasher.hexdigest(), st_before.st_size
			finally:
				os.close(leaf)
		except OSError as exc:
			if exc.errno == errno.ELOOP:
				raise BatonError(f"attachment path {rel_path!r} crosses a symlink; refusing", EXIT_DAMAGE) from exc
			raise BatonError(f"attachment path {rel_path!r} unresolvable: {exc}") from exc
		finally:
			try:
				os.close(fd)
			except OSError:
				pass

	def _pin_external_parts(self, nodes: list[dict]) -> None:
		"""Resolve every external leaf against its root and PIN hash, size and
		binding generation. Done at publication, before the write transaction,
		exactly where the single attachment was resolved before."""
		for node in nodes:
			if node["parts"] is not None:
				self._pin_external_parts(node["parts"])
				continue
			if node["storage"] != STORAGE_EXTERNAL:
				continue
			ref = node["attach"]
			root_id, _, sha, size = self._resolve_attachment(
				{"root_id": ref["root_id"], "path": ref["path"]})
			binding = self.conn.execute(
				"SELECT binding_generation FROM accepted_roots WHERE root_id=?",
				(root_id,)).fetchone()
			if binding is None:
				raise BatonError(f"root {root_id!r} has no accepted binding", EXIT_DAMAGE)
			ref["generation"] = binding["binding_generation"]
			node["sha256"] = sha
			node["size"] = size

	def _verify_external_part(self, part: dict) -> None:
		"""Re-resolve ONE external leaf; mutation fails closed. The binding
		generation identifies the ROOT BINDING it was pinned under (not the
		global config generation), so unrelated config edits never invalidate
		a part while remap or removal of a referenced binding stays refused by
		regen."""
		ref = part["attach"]
		accepted = self.conn.execute(
			"SELECT path, binding_generation FROM accepted_roots WHERE root_id=?",
			(ref["root_id"],)).fetchone()
		if accepted is None or accepted["path"] != self.config.get("roots", {}).get(ref["root_id"]):
			raise BatonError(
				f"attachment root {ref['root_id']!r} is no longer the accepted mapping", EXIT_DAMAGE)
		if accepted["binding_generation"] != ref["generation"]:
			raise BatonError(
				f"attachment root {ref['root_id']!r} binding generation "
				f"{accepted['binding_generation']} does not match the pinned "
				f"{ref['generation']}", EXIT_DAMAGE)
		try:
			_, _, sha, size = self._resolve_attachment(
				{"root_id": ref["root_id"], "path": ref["path"]})
		except BatonError as exc:
			# It resolved cleanly at publication, so ANY failure to re-resolve
			# now is post-publication damage, not a usage error: a deleted,
			# replaced, or newly unreadable file is the same class of problem
			# as a changed hash and must be skippable and reportable the same
			# way. Re-raise unchanged if it was already damage.
			if exc.exit_code == EXIT_DAMAGE:
				raise
			raise BatonError(
				f"attachment {ref['path']!r} can no longer be resolved: {exc}",
				EXIT_DAMAGE) from exc
		if sha != part["sha256"] or size != part["size"]:
			raise BatonError(
				f"attachment {ref['path']!r} no longer matches its pinned hash; refusing",
				EXIT_DAMAGE)

	def _external_leaves(self, nodes: list[dict]) -> list[dict]:
		out = []
		for node in nodes:
			if node["parts"] is not None:
				out.extend(self._external_leaves(node["parts"]))
			elif node["storage"] == STORAGE_EXTERNAL:
				out.append(node)
		return out

	def verify_attachment(self, message_id: str) -> None:
		"""Re-resolve EVERY external part of a message; any mutation fails
		closed. A message may now carry several, so one damaged part damages
		the message -- which is what keeps skip-and-continue honest."""
		row = self.conn.execute(
			"SELECT id FROM messages WHERE id=?", (message_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown message {message_id!r}", EXIT_NONE)
		for part in self._external_leaves(self._read_parts("message", message_id)):
			self._verify_external_part(part)

	def send(self, sender: str, recipient, *, kind: str, subject: str | None = None,
	         body: bytes | None = None, parts: Any = None,
	         content_type: str | None = None, disposition: str | None = None,
	         part_name: str | None = None, container_type: str | None = None,
	         thread_id: str | None = None,
	         retention: str = RETENTION_DURABLE, outcome: str | None = None,
	         responds_to: str | None = None, attach: Any = None,
	         possible_duplicate: bool = False) -> str:
		"""Publish to ONE recipient or several.

		`recipient` takes an address or a sequence of them. Several recipients
		make ONE publication and N ORDINARY MESSAGES -- each with its own
		claim, retry, disposition, damage and GC lifecycle, because they are
		ordinary messages and were never joined. Resolving one recipient's copy
		cannot touch another's, and that is true by construction rather than by
		every future change remembering it.

		The publication record exists for single recipients too. Deriving the
		audience from surviving message rows would shrink it as GC removes
		terminal deliveries, and a shape that exists only for multi-recipient
		traffic is one that decision obligations and authorized reread would
		have to work around.

		`possible_duplicate` is the SENDER's assertion that they could not tell
		whether an earlier attempt committed. Publication is at-least-once by
		ruling: Baton does not identify or correlate the original, and the
		recipient decides what to do with the warning. It is immutable.

		Returns the message id for a single recipient -- unchanged -- and the
		publication id when several are addressed, because there is no single
		message to name.
		"""
		# `attach` is sugar for a single external part, so the historical
		# attachment-only send still works -- but it is now ONE leaf in the
		# ordinary manifest, and it may sit beside inline parts.
		if attach is not None:
			if parts is not None:
				raise BatonError(
					"pass attach inside parts when composing a multipart message")
			if body is not None:
				parts = [{"content_type": content_type, "disposition": disposition,
				          "part_name": part_name, "body": body},
				         {"content_type": DEFAULT_ATTACHMENT_TYPE,
				          "disposition": DISPOSITION_ATTACHMENT, "attach": attach}]
				body = content_type = disposition = part_name = None
			else:
				parts = [{"content_type": (DEFAULT_ATTACHMENT_TYPE
				                           if content_type is None else content_type),
				          "disposition": (DISPOSITION_ATTACHMENT
				                          if disposition is None else disposition),
				          "part_name": part_name, "attach": attach}]
				content_type = disposition = part_name = None
		container, nodes = content_spec(
			body, parts, content_type=content_type, disposition=disposition,
			part_name=part_name, container_type=container_type, where="send content")
		if nodes is None:
			# THE SUBJECT IS THE MESSAGE. Ruled 2026-08-10 as a first-class
			# affordance, after measurement showed every subject-only message
			# on the live channel was reaching its recipient through the
			# zero-byte body defect rather than through anything deliberate.
			#
			# A subject is required because otherwise nothing at all is
			# published: a recipient would get a row with no content and no
			# summary, which is not a quick message but an empty one.
			if not subject:
				raise BatonError(
					"a message requires content, or a subject to carry it")
			container, nodes = CONTENTLESS_CONTAINER, []
		else:
			refuse_empty_bodies(nodes, "send content")
			self._pin_external_parts(nodes)
		self._check_identity(sender)
		recipients = [recipient] if isinstance(recipient, str) else list(recipient)
		if not recipients:
			raise BatonError("a message requires at least one recipient")
		# REFUSED, not deduplicated. `--to a --to a` means something the caller
		# did not write, and silently collapsing it would publish a different
		# request than the one they made.
		duplicates = sorted({a for a in recipients if recipients.count(a) > 1})
		if duplicates:
			raise BatonError(f"duplicate recipient(s) {', '.join(duplicates)}")
		for address in recipients:
			# A wildcard is a SCOPE, and a scope addresses a broadcast. Letting
			# one through here would turn "assign this work to a team" into
			# something with no per-recipient claim, which is the opposite of
			# what a directed message is for.
			if address.endswith(".*"):
				raise BatonError(
					f"{address!r} is a scope; --to takes exact participants, and a "
					f"scope addresses a notice rather than claimable work")
			self._check_participant(address, "send")
		if not KIND_RE.match(kind):
			raise BatonError(f"invalid kind {kind!r}")
		subject = validate_subject(subject)
		if thread_id is not None and not THREAD_RE.match(thread_id):
			raise BatonError(f"invalid thread id {thread_id!r}")
		if retention not in RETENTIONS:
			raise BatonError(f"invalid retention {retention!r}")
		if retention == RETENTION_TRANSIENT:
			_check_transient_size(nodes)
		self._txn_begin("send", participant=sender)
		try:
			now = _utc_now_iso()
			publication_id = self._publish(
				sender, recipients, kind=kind, subject=subject, thread_id=thread_id,
				retention=retention, outcome=outcome, container_type=container,
				nodes=nodes, now=now, possible_duplicate=possible_duplicate)
			# ATOMIC: every delivery or none. A partial audience would leave
			# some recipients holding work the others were never told about,
			# with nothing in the store able to say which.
			ids = [self._insert_message(
				sender, address, kind=kind, subject=subject, container_type=container,
				nodes=nodes, thread_id=thread_id, retention=retention, outcome=outcome,
				responds_to=responds_to, publication_id=publication_id)
				for address in recipients]
			self._txn_commit()
			return ids[0] if isinstance(recipient, str) else publication_id
		except BaseException:
			self._txn_rollback()
			raise

	def _publish(self, sender: str, recipients, *, kind: str, subject: str | None,
	             thread_id: str | None, retention: str, outcome: str | None,
	             container_type: str, nodes: list[dict] | None, now: str,
	             possible_duplicate: bool = False) -> str:
		"""The publication record and its frozen audience. Returns its id.

		ONE path for every directed message, which is the whole point of
		extracting it. `reply` used to insert its response message directly
		and skipped this, so every reply carried a NULL publication link and
		delivered `audience: []` -- a contract violation that lived for as
		long as there were two ways to create a directed message.

		Callers must already be inside the transaction that creates the
		deliveries: a publication without its messages is exactly the partial
		state the audience record exists to make impossible.
		"""
		publication_id = new_id()
		self.conn.execute(
			"INSERT INTO publications(publication_id, from_participant, kind, "
			"subject, thread_id, retention, outcome, content_type, "
			"manifest_sha256, created_ts, possible_duplicate) "
			"VALUES(?,?,?,?,?,?,?,?,?,?,?)",
			(publication_id, sender, kind, subject, thread_id, retention,
			 outcome, container_type, manifest_digest(container_type, nodes), now,
			 1 if possible_duplicate else 0))
		self.conn.executemany(
			"INSERT INTO publication_audience(publication_id, participant) VALUES(?,?)",
			[(publication_id, address) for address in sorted(recipients)])
		return publication_id

	def _insert_message(self, sender: str, recipient: str, *, kind: str,
	                    subject: str | None, container_type: str, nodes: list[dict],
	                    thread_id: str | None, retention: str, outcome: str | None,
	                    responds_to: str | None,
	                    publication_id: str | None = None) -> str:
		now = _utc_now_iso()
		message_id = new_id()
		manifest = manifest_digest(container_type, nodes)
		self.conn.execute(
			"INSERT INTO messages(id, from_participant, to_participant, kind, subject, thread_id, "
			"retention, content_type, manifest_sha256, outcome, created_ts, state, "
			"responds_to, publication_id) "
			"VALUES(?,?,?,?,?,?,?,?,?,?,?, 'pending', ?,?)",
			(message_id, sender, recipient, kind, subject, thread_id, retention, container_type,
			 manifest, outcome, now, responds_to, publication_id))
		self._write_parts("message", message_id, nodes, now)
		return message_id

	# -- parts --------------------------------------------------------------

	def _write_parts(self, owner_kind: str, owner_id: str, nodes: list[dict],
	                 now: str, *, retain: bool = True) -> None:
		"""Persist a normalized part tree. `retain=False` records the manifest
		(types, order, hashes, sizes) without keeping the bytes -- the transient
		contract, which has always been "identity survives, payload does not"."""
		def write(items: list[dict], parent_id: str | None) -> None:
			for ordinal, node in enumerate(items):
				part_id = new_id()
				content_id = root_id = path = generation = None
				storage = node["storage"]
				if storage == STORAGE_EXTERNAL:
					root_id = node["attach"]["root_id"]
					path = node["attach"]["path"]
					generation = node["attach"]["generation"]
				elif storage == STORAGE_INLINE and retain:
					content_id = new_id()
					self.conn.execute(
						"INSERT INTO contents(content_id, body, sha256, size, created_ts) "
						"VALUES(?,?,?,?,?)",
						(content_id, node["body"], node["sha256"], node["size"], now))
				self.conn.execute(
					"INSERT INTO parts(part_id, owner_kind, owner_id, parent_part_id, ordinal, "
					"content_type, disposition, part_name, storage, content_id, root_id, path, "
					"generation, sha256, size, created_ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
					(part_id, owner_kind, owner_id, parent_id, ordinal, node["content_type"],
					 node["disposition"], node["part_name"], storage, content_id,
					 root_id, path, generation, node["sha256"], node["size"], now))
				if node["parts"] is not None:
					write(node["parts"], part_id)
		write(nodes, None)

	def _read_parts(self, owner_kind: str, owner_id: str) -> list[dict]:
		"""Rebuild the stored part tree in document order, with the bytes of
		every retained leaf. A row that is unreachable from the roots, or a
		parent cycle, is DAMAGE: the manifest digest would no longer describe
		what is stored, and delivering it would be delivering a lie."""
		rows = self.conn.execute(
			"SELECT p.part_id, p.parent_part_id, p.ordinal, p.content_type, p.disposition, "
			"p.part_name, p.storage, p.root_id, p.path, p.generation, p.sha256, p.size, c.body "
			"FROM parts p LEFT JOIN contents c ON c.content_id = p.content_id "
			"WHERE p.owner_kind=? AND p.owner_id=? ORDER BY p.ordinal",
			(owner_kind, owner_id)).fetchall()
		if not rows:
			return []
		by_parent: dict = {}
		for row in rows:
			by_parent.setdefault(row["parent_part_id"], []).append(row)
		seen: set[str] = set()

		def build(parent_id: str | None, prefix: str = "") -> list[dict]:
			out = []
			for row in sorted(by_parent.get(parent_id, []), key=lambda r: r["ordinal"]):
				address = f"{prefix}{row['ordinal']}"
				if row["part_id"] in seen:
					raise BatonError(
						f"part tree for {owner_kind} {owner_id!r} contains a cycle", EXIT_DAMAGE)
				seen.add(row["part_id"])
				container = is_container_type(row["content_type"])
				out.append({
					"part_id": row["part_id"],
					# Dotted position in the ordered manifest -- the same
					# address `materialize --part` takes, so anything that
					# reports a part reports something a human can act on.
					"address": address,
					"content_type": row["content_type"],
					"disposition": row["disposition"],
					"part_name": row["part_name"],
					"storage": row["storage"],
					"attach": ({"root_id": row["root_id"], "path": row["path"],
					            "generation": row["generation"]}
					           if row["storage"] == STORAGE_EXTERNAL else None),
					"sha256": row["sha256"],
					"size": row["size"],
					"body": row["body"],
					"parts": build(row["part_id"], address + ".") if container else None,
				})
			return out
		tree = build(None)
		if len(seen) != len(rows):
			raise BatonError(
				f"part tree for {owner_kind} {owner_id!r} has {len(rows) - len(seen)} unreachable "
				f"row(s); the stored manifest is incomplete", EXIT_DAMAGE)
		return tree

	def _parts_depth_first(self, owner_kind: str, owner_id: str) -> list[sqlite3.Row]:
		"""Owner's part rows deepest-first, so deletes never orphan a child
		behind its parent's foreign key."""
		rows = self.conn.execute(
			"SELECT part_id, parent_part_id, content_id FROM parts "
			"WHERE owner_kind=? AND owner_id=?", (owner_kind, owner_id)).fetchall()
		parents = {row["part_id"]: row["parent_part_id"] for row in rows}
		depths = {}
		for part_id in parents:
			depth, cursor, walked = 0, part_id, set()
			while parents.get(cursor) is not None:
				if cursor in walked:
					raise BatonError(
						f"part tree for {owner_kind} {owner_id!r} contains a cycle", EXIT_DAMAGE)
				walked.add(cursor)
				cursor = parents[cursor]
				depth += 1
			depths[part_id] = depth
		return sorted(rows, key=lambda r: -depths[r["part_id"]])

	def _delete_parts(self, owner_kind: str, owner_id: str) -> None:
		for row in self._parts_depth_first(owner_kind, owner_id):
			self.conn.execute("DELETE FROM parts WHERE part_id=?", (row["part_id"],))
			if row["content_id"] is not None:
				self.conn.execute(
					"DELETE FROM contents WHERE content_id=?", (row["content_id"],))

	def _scrub_parts(self, owner_kind: str, owner_id: str) -> None:
		"""Drop the BYTES of every retained leaf while leaving the manifest --
		order, media types, dispositions, part names, sizes and hashes -- intact.
		A consumed transient message can still prove what it carried."""
		for row in self.conn.execute(
				"SELECT part_id, content_id FROM parts WHERE owner_kind=? AND owner_id=? "
				"AND content_id IS NOT NULL", (owner_kind, owner_id)).fetchall():
			self.conn.execute(
				"UPDATE parts SET content_id=NULL WHERE part_id=?", (row["part_id"],))
			self.conn.execute(
				"DELETE FROM contents WHERE content_id=?", (row["content_id"],))

	def _first_deliverable(self, participant: str) -> tuple[str | None, int]:
		"""Oldest pending message whose attachment still verifies, in
		deterministic (created_ts, id) order, plus how many were skipped as
		damaged. SKIP AND CONTINUE: a message whose pinned file changed after
		publication must not block the healthy messages behind it — before
		this existed, one such message made every claim for that recipient
		fail with EXIT_DAMAGE forever, and it could not be claimed, closed, or
		collected in order to clear it. Skipping never mutates the damaged
		message; it stays pending and surfaces through `scan` and `doctor`."""
		ids = [row[0] for row in self.conn.execute(
			"SELECT id FROM messages WHERE to_participant=? AND state='pending' "
			"ORDER BY created_ts, id", (participant,))]
		skipped = 0
		for candidate in ids:
			try:
				self.verify_attachment(candidate)
			except BatonError as exc:
				if exc.exit_code != EXIT_DAMAGE:
					raise
				skipped += 1
				continue
			return candidate, skipped
		return None, skipped

	def readiness(self, participant: str) -> dict:
		"""What is at the HEAD of this participant's queue, taking none of it.

		Strict FIFO, ruled 2026-08-10: the first pending directed message in
		(created_ts, id) order, healthy or DAMAGED, and never a look past it.

		I first built this on `claim`'s eligibility, which skips damaged
		messages to find one it can take. That was wrong for an observation.
		Scanning ahead makes readiness answer a different question from the
		one asked -- "what could be claimed" instead of "what is next" -- and
		it HIDES a damaged head: the one state a human most needs to see,
		reported as though the queue were healthy and shorter than it is.

		`damaged` therefore rides on the result. A damaged head is still
		ready in the sense that matters: there is something here, it is next,
		and it needs attention. What it needs may be `quarantine` rather than
		`claim`, and saying so is the point.

		ALWAYS returns a dict. `ready` false means the queue is empty, which
		is different from a queue whose head cannot be claimed.

		Metadata only: no parts, no body, no subject -- the caller is told
		work exists, not handed it. Observation writes nothing: no claim, no
		notice receipt, no ledger event, no write lock at all.
		"""
		self._check_identity(participant)
		row = self.conn.execute(
			"SELECT id, from_participant, kind, created_ts FROM messages "
			"WHERE to_participant=? AND state='pending' "
			"ORDER BY created_ts, id LIMIT 1", (participant,)).fetchone()
		if row is not None:
			try:
				self.verify_attachment(row["id"])
			except BatonError as exc:
				if exc.exit_code != EXIT_DAMAGE:
					raise
				damaged = True
			else:
				damaged = False
			return {"ready": True, "channel": "message", "message_id": row["id"],
			        "from_participant": row["from_participant"], "kind": row["kind"],
			        "created_ts": row["created_ts"], "damaged": damaged}
		if self.has_unseen_notice(participant):
			# The notice is NOT named. A readiness result that named one would
			# invite the caller to consume that specific notice, while `see`
			# drains oldest-first -- so a notice arriving in between would be
			# consumed under another one's name. Readiness says the channel is
			# non-empty; `see` decides what that means.
			return {"ready": True, "channel": "notice"}
		return {"ready": False, "channel": None}

	def claim(self, participant: str, *, message_id: str | None = None) -> dict:
		self._check_identity(participant)
		if message_id is None:
			# Attachment pins are enforced at selection: post-publication
			# mutation fails closed before the claim transaction begins (file
			# IO stays outside the write lock).
			message_id, skipped = self._first_deliverable(participant)
			if message_id is None:
				# EXIT_NONE, never EXIT_DAMAGE — "nothing eligible" is what
				# keeps a waiter alive and able to receive a later healthy
				# publication instead of standing it down permanently.
				if skipped:
					raise BatonError(
						f"no deliverable message for {participant!r}: {skipped} pending "
						f"message(s) have damaged attachments (see scan/doctor)", EXIT_NONE)
				raise BatonError(f"no message addressed to {participant!r} is pending", EXIT_NONE)
		else:
			# An EXPLICITLY named target still fails closed on damage: the
			# caller asked for this message, so quietly substituting another
			# would be a lie about what was delivered.
			self.verify_attachment(message_id)
		self._txn_begin("claim", participant=participant)
		try:
			claim_id = new_id()
			now = _utc_now_iso()
			self.conn.execute(
				"INSERT INTO claims(claim_id, message_id, participant, claimed_ts, state) "
				"VALUES(?,?,?,?, 'active')", (claim_id, message_id, participant, now))
			cur = self.conn.execute(
				"UPDATE messages SET state='claimed' WHERE id=? AND state='pending' AND to_participant=?",
				(message_id, participant))
			if cur.rowcount != 1:
				raise BatonError(f"message {message_id!r} is not pending for {participant!r}", EXIT_NONE)
			self._txn_commit()
			return self.get_claim(claim_id)
		except sqlite3.IntegrityError as exc:
			self._txn_rollback()
			raise BatonError(f"claim lost a race: {exc}", EXIT_RACE) from exc
		except BaseException:
			self._txn_rollback()
			raise

	def _load_active_claim(self, claim_id: str, participant: str) -> sqlite3.Row:
		row = self.conn.execute(
			"SELECT c.claim_id, c.message_id, c.participant, c.state AS claim_state, "
			"m.from_participant, m.to_participant, m.kind, m.subject, m.thread_id, m.retention, "
			"m.content_type, m.manifest_sha256, m.state AS message_state "
			"FROM claims c JOIN messages m ON m.id = c.message_id WHERE c.claim_id=?",
			(claim_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown claim {claim_id!r}")
		# Ownership is the claiming participant, which the schema records and
		# which must equal the message recipient. A caller that is not that
		# participant cannot dispose of the claim, and there is no credential
		# to present in place of being it.
		if row["participant"] != participant:
			raise BatonError(
				f"claim {claim_id!r} belongs to {row['participant']!r}, not {participant!r}")
		if row["to_participant"] != participant:
			raise BatonError(
				f"claim {claim_id!r} is on a message addressed to {row['to_participant']!r}; "
				f"only the recipient may dispose of it", EXIT_PROTOCOL)
		return row

	def _existing_disposition(self, claim_id: str) -> sqlite3.Row | None:
		return self.conn.execute(
			"SELECT d.claim_id, d.kind, d.outcome, d.retention, d.content_type, d.manifest_sha256, "
			"d.response_message_id, d.created_ts FROM dispositions d WHERE d.claim_id=?",
			(claim_id,)).fetchone()

	def _verify_retry(self, existing: sqlite3.Row, *, op: str, message_kind: str | None,
	                  outcome: str | None, container_type: str | None,
	                  nodes: list[dict] | None, recipient: str | None,
	                  subject: str | None = None,
	                  thread_id: str | None = None, retention: str | None = None) -> dict:
		"""Retry idempotence: validate the retried operation against the
		committed disposition; matching retries redeliver, mismatches fail
		closed.

		Identity is the COMPLETE ORDERED PART MANIFEST, metadata included --
		not the body bytes. Two retries whose parts differ in order, media
		type, disposition or part_name are different operations even when every
		byte matches, and comparing manifest digests is what makes them fail
		closed rather than report `already_committed` for something that was
		never committed. Bytes may already be scrubbed; the manifest survives
		scrubbing, which is the other reason to compare it."""
		if existing["kind"] != op:
			raise BatonError(
				f"claim already has a committed {existing['kind']} disposition; retried {op} mismatches", EXIT_PROTOCOL)
		if existing["outcome"] != outcome:
			raise BatonError("retried outcome differs from the committed disposition", EXIT_PROTOCOL)
		if retention is not None and existing["retention"] != retention:
			raise BatonError("retried retention differs from the committed disposition", EXIT_PROTOCOL)
		committed_manifest = existing["manifest_sha256"]
		retry_manifest = manifest_digest(container_type, nodes) if nodes is not None else None
		if existing["content_type"] != container_type or committed_manifest != retry_manifest:
			raise BatonError(
				"retried content manifest differs from the committed disposition", EXIT_PROTOCOL)
		response_id = existing["response_message_id"]
		if response_id is not None:
			row = self.conn.execute(
				"SELECT to_participant, kind, subject, thread_id FROM messages WHERE id=?",
				(response_id,)).fetchone()
			if row is None:
				raise BatonError(
					"committed disposition references a missing response message", EXIT_DAMAGE)
			if row["to_participant"] != recipient:
				raise BatonError("retried recipient differs from the committed disposition", EXIT_PROTOCOL)
			if message_kind is not None and row["kind"] != message_kind:
				raise BatonError("retried message kind differs from the committed disposition", EXIT_PROTOCOL)
			if row["thread_id"] != thread_id:
				raise BatonError("retried thread differs from the committed disposition", EXIT_PROTOCOL)
			# The EFFECTIVE subject, so an inherited retry still matches an
			# inherited commit and an explicit change fails closed.
			if row["subject"] != subject:
				raise BatonError("retried subject differs from the committed disposition", EXIT_PROTOCOL)
		return {
			"already_committed": True,
			"claim_id": existing["claim_id"],
			"kind": existing["kind"],
			"outcome": existing["outcome"],
			"content_type": existing["content_type"],
			"manifest_sha256": committed_manifest,
			"retention": existing["retention"],
			"response_message_id": response_id,
			"created_ts": existing["created_ts"],
		}

	def _scrub_transient_incoming(self, row: sqlite3.Row) -> None:
		if row["retention"] == RETENTION_TRANSIENT and row["manifest_sha256"] is not None:
			self._scrub_parts("message", row["message_id"])

	def reply(self, claim_id: str, *, participant: str, kind: str, subject: str | None = None,
	          body: bytes | None = None, parts: Any = None,
	          content_type: str | None = None, disposition: str | None = None,
	          part_name: str | None = None, container_type: str | None = None,
	          outcome: str | None = None,
	          recipient: str | None = None, thread_id: str | None = None,
	          retention: str | None = None) -> dict:
		if not KIND_RE.match(kind):
			raise BatonError(f"invalid kind {kind!r}")
		subject = validate_subject(subject)
		container, nodes = content_spec(
			body, parts, content_type=content_type, disposition=disposition,
			part_name=part_name, container_type=container_type, where="reply content")
		if nodes is None:
			# `close` remains the contentless DISPOSITION; this is the
			# contentless MESSAGE, which still says something.
			#
			# A reply INHERITS the subject it answers, so the effective
			# subject is what must be non-empty -- resolved below, against the
			# claim, because it is not known here.
			if subject is not None and not subject.strip():
				raise BatonError(
					"reply requires content, or a subject to carry it "
					"(a close is the contentless disposition)")
			container, nodes = CONTENTLESS_CONTAINER, []
		if retention is not None and retention not in RETENTIONS:
			raise BatonError(f"invalid retention {retention!r}")
		# Pinning happens BEFORE the write transaction, as it always has:
		# resolving an external part is file IO and stays outside the lock.
		# It must also happen before the retry comparison, because the pinned
		# hash and size are part of the manifest a retry is compared against.
		self._pin_external_parts(nodes)
		self._txn_begin("reply")
		try:
			row = self._load_active_claim(claim_id, participant)
			self.conn.execute("UPDATE op_context SET participant=? WHERE one_row=1", (row["to_participant"],))
			effective_retention = retention if retention is not None else row["retention"]
			# None means INHERIT on both first publication and retry — the
			# effective route is normalized before disposition lookup so a
			# retry can never wildcard-match a differently routed commit.
			effective_recipient = recipient if recipient is not None else row["from_participant"]
			effective_thread = thread_id if thread_id is not None else row["thread_id"]
			# A reply inherits the subject it is answering, so a thread reads
			# as one conversation in an inbox rather than as unrelated lines.
			effective_subject = subject if subject is not None else row["subject"]
			# THE INHERITED SUBJECT IS THE ONE THAT MUST CARRY IT. A
			# contentless reply is "the subject is the message", and a reply
			# inherits the subject it answers -- so answering a SUBJECTLESS
			# message with no body would publish a row with neither content
			# nor summary. Checked here because the effective subject is not
			# known until the claim is loaded, and before anything is written.
			if not nodes and not (effective_subject or "").strip():
				raise BatonError(
					"reply requires content, or a subject to carry it; the message "
					"being answered has no subject to inherit "
					"(a close is the contentless disposition)")
			existing = self._existing_disposition(claim_id)
			if existing is not None:
				result = self._verify_retry(existing, op='reply', message_kind=kind, outcome=outcome,
				                            container_type=container, nodes=nodes,
				                            recipient=effective_recipient, subject=effective_subject,
				                            thread_id=effective_thread, retention=effective_retention)
				self._txn_rollback()
				return result
			if row["claim_state"] != "active":
				raise BatonError(f"claim {claim_id!r} is {row['claim_state']}, not active", EXIT_PROTOCOL)
			# See `close`: after the retry short-circuit, so a committed
			# legacy zero-byte reply stays retryable.
			refuse_empty_bodies(nodes, "reply content")
			to = effective_recipient
			self._check_participant(to, "reply")
			thread = effective_thread
			# v5-preserved surface: explicit override permitted, default inherit
			# (v5 respond(): response_retention = retention or envelope retention).
			if effective_retention == RETENTION_TRANSIENT:
				_check_transient_size(nodes)
			now = _utc_now_iso()
			# A RESPONSE IS A DIRECTED MESSAGE, so it gets its own
			# single-recipient publication like any other. Reached only on the
			# FIRST commit: the retry path above returns the committed
			# disposition before here, so a retried reply cannot mint a second
			# publication for the same response.
			publication_id = self._publish(
				row["to_participant"], [to], kind=kind, subject=effective_subject,
				thread_id=thread, retention=effective_retention, outcome=outcome,
				container_type=container, nodes=nodes, now=now)
			response_id = self._insert_message(
				row["to_participant"], to, kind=kind, subject=effective_subject,
				container_type=container, nodes=nodes,
				thread_id=thread, retention=effective_retention, outcome=outcome,
				responds_to=row["message_id"], publication_id=publication_id)
			manifest = manifest_digest(container, nodes)
			self.conn.execute(
				"INSERT INTO dispositions(claim_id, kind, outcome, retention, content_type, "
				"manifest_sha256, response_message_id, created_ts) VALUES(?, 'reply', ?, ?, ?, ?, ?, ?)",
				(claim_id, outcome, effective_retention, container, manifest, response_id, now))
			self.conn.execute(
				"UPDATE claims SET state='completed', terminal_ts=? WHERE claim_id=?", (now, claim_id))
			self.conn.execute(
				"UPDATE messages SET state='completed', completed_ts=? WHERE id=?", (now, row["message_id"]))
			self._scrub_transient_incoming(row)
			self._txn_commit()
			return {
				"already_committed": False,
				"claim_id": claim_id,
				"kind": kind,
				"outcome": outcome,
				"content_type": container,
				"manifest_sha256": manifest,
				"retention": effective_retention,
				"response_message_id": response_id,
				"created_ts": now,
			}
		except BaseException:
			self._txn_rollback()
			raise

	def close_claim(self, claim_id: str, *, participant: str,
	                body: bytes | None = None, parts: Any = None,
	                content_type: str | None = None, disposition: str | None = None,
	                part_name: str | None = None, container_type: str | None = None,
	                outcome: str | None = None,
	                retention: str | None = None) -> dict:
		if retention is not None and retention not in RETENTIONS:
			raise BatonError(f"invalid retention {retention!r}")
		container, nodes = content_spec(
			body, parts, content_type=content_type, disposition=disposition,
			part_name=part_name, container_type=container_type, where="close content")
		if nodes is not None:
			reject_external_parts(nodes, "a close disposition")
		self._txn_begin("close")
		try:
			row = self._load_active_claim(claim_id, participant)
			self.conn.execute("UPDATE op_context SET participant=? WHERE one_row=1", (row["to_participant"],))
			effective_retention = retention if retention is not None else row["retention"]
			existing = self._existing_disposition(claim_id)
			if existing is not None:
				result = self._verify_retry(existing, op='close', message_kind=None, outcome=outcome,
				                            container_type=container, nodes=nodes,
				                            recipient=None, retention=effective_retention)
				self._txn_rollback()
				return result
			if row["claim_state"] != "active":
				raise BatonError(f"claim {claim_id!r} is {row['claim_state']}, not active", EXIT_PROTOCOL)
			# AFTER the retry short-circuit, deliberately. A legacy zero-byte
			# disposition that already committed must still be retryable to
			# `already_committed`; refusing it here would make an operation
			# that succeeded impossible to complete. This gate is for NEW
			# content only.
			refuse_empty_bodies(nodes, "close content")
			now = _utc_now_iso()
			manifest = None
			if nodes is not None:
				# The EFFECTIVE disposition retention (override or inherit)
				# decides retained bytes vs manifest-only identity (T16). The
				# manifest is recorded either way, so a transient close can
				# still prove exactly what it carried.
				manifest = manifest_digest(container, nodes)
				retain = effective_retention != RETENTION_TRANSIENT
				if not retain:
					_check_transient_size(nodes)
				self._write_parts("disposition", claim_id, nodes, now, retain=retain)
			self.conn.execute(
				"INSERT INTO dispositions(claim_id, kind, outcome, retention, content_type, "
				"manifest_sha256, response_message_id, created_ts) VALUES(?, 'close', ?, ?, ?, ?, NULL, ?)",
				(claim_id, outcome, effective_retention, container, manifest, now))
			self.conn.execute(
				"UPDATE claims SET state='completed', terminal_ts=? WHERE claim_id=?", (now, claim_id))
			self.conn.execute(
				"UPDATE messages SET state='closed', completed_ts=? WHERE id=?", (now, row["message_id"]))
			self._scrub_transient_incoming(row)
			self._txn_commit()
			return {
				"already_committed": False,
				"claim_id": claim_id,
				"kind": "close",
				"outcome": outcome,
				"content_type": container,
				"manifest_sha256": manifest,
				"retention": effective_retention,
				"response_message_id": None,
				"created_ts": now,
			}
		except BaseException:
			self._txn_rollback()
			raise

	# -- notices ------------------------------------------------------------

	def send_notice(self, sender: str, *, kind: str, subject: str | None = None,
	                body: bytes | None = None, parts: Any = None,
	                content_type: str | None = None, disposition: str | None = None,
	                part_name: str | None = None, container_type: str | None = None,
	                ttl_seconds: int | None = None, scope: str | None = None,
	                possible_duplicate: bool = False) -> str:
		"""Broadcast a notice with a FINITE lifetime (default 86400s, the v5
		protocol TTL). Immortal notices are not constructible. The exact
		authoring participant is recorded immutably and
		is the only identity permitted to expire the notice early.

		Notices use the SAME content representation as directed messages --
		same parts table, same manifest digest, same envelope. The two inbound
		channels diverged once before, and a consumer had to special-case which
		one it was reading; that is why there is one code path here.

		THE AUDIENCE IS FROZEN HERE, global and scoped alike. `scope` selects a
		team -- `baton.*` -- and its absence means every configured
		participant; either way the expansion happens inside this transaction
		and the resulting explicit list is stored.

		Ruled, and it changes global behaviour: a participant added later can
		no longer see an older broadcast. A broadcast is to the participants
		who existed when it was sent, and a config addition should not grant a
		new identity access to historic content. One immutable mechanism is
		also auditable in a way that re-evaluating live config at read time is
		not -- with the old shape, "who was this sent to" had no answer except
		"whoever the config says today"."""
		self._check_identity(sender)
		if not KIND_RE.match(kind):
			raise BatonError(f"invalid kind {kind!r}")
		subject = validate_subject(subject)
		if ttl_seconds is None:
			ttl_seconds = DEFAULT_NOTICE_TTL_SECONDS
		if type(ttl_seconds) is not int or ttl_seconds < 1:
			raise BatonError("ttl_seconds must be a positive integer")
		# EXPANDED BEFORE THE TRANSACTION OPENS, so a malformed selector or one
		# that matches nobody costs no authority write at all.
		configured = sorted(self.config.get("participants", {}))
		if scope is None:
			audience_kind, audience = "global", configured
		else:
			audience_kind, audience = "scope", expand_scope(scope, configured)
		if not audience:
			raise BatonError("a notice requires at least one addressee")
		container, nodes = content_spec(
			body, parts, content_type=content_type, disposition=disposition,
			part_name=part_name, container_type=container_type, where="notice content")
		if nodes is None:
			# NOT extended to broadcast, ruled. A notice has no recipient
			# obligation to carry its meaning forward, and a TTL'd
			# announcement whose whole content is a summary line is the case
			# that most needs a body.
			raise BatonError("a notice requires content")
		refuse_empty_bodies(nodes, "notice content")
		reject_external_parts(nodes, "a notice")
		_check_transient_size(nodes)
		self._txn_begin("send", participant=sender)
		try:
			now = _utc_now_iso()
			notice_id = new_id()
			manifest = manifest_digest(container, nodes)
			self.conn.execute(
				"INSERT INTO notices(id, from_participant, kind, subject, "
				"content_type, manifest_sha256, created_ts, ttl_seconds, "
				"audience_kind, selector, possible_duplicate) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
				(notice_id, sender, kind, subject, container, manifest, now,
				 ttl_seconds, audience_kind, scope,
				 1 if possible_duplicate else 0))
			self.conn.executemany(
				"INSERT INTO notice_audience(notice_id, participant) VALUES(?,?)",
				[(notice_id, address) for address in audience])
			self._write_parts("notice", notice_id, nodes, now)
			self._txn_commit()
			return notice_id
		except BaseException:
			self._txn_rollback()
			raise

	def see(self, participant: str, *,
	        limit: int | None = None) -> list[dict]:
		"""Mark not-yet-seen live notices seen for a participant and
		return them oldest-first. One transaction; broadcast, never claimable.
		Selection and receipt commit together, so a crash before the commit
		leaves the notice deliverable and a crash after it does not redeliver
		— broadcast is at-most-once per participant by construction,
		because a claimless read has no acknowledgement to wait for.

		`limit` bounds how many notices this call consumes: `see` drains
		everything, while `wait` takes exactly one delivery at a time. The
		ordering tiebreak is the notice id, matching `claim`'s total order —
		timestamps are second-resolution, so created_ts alone is not a total
		order."""
		self._check_identity(participant)
		if limit is not None and (type(limit) is not int or limit < 1):
			raise BatonError("limit must be a positive integer or None")
		self._txn_begin("see", participant=participant)
		try:
			now = _utc_now_iso()
			rows = self.conn.execute(
				"SELECT n.id, n.from_participant, n.kind, n.subject, n.content_type, n.manifest_sha256, "
				"n.created_ts, n.ttl_seconds, n.audience_kind, n.selector, n.possible_duplicate FROM notices n "
				"WHERE NOT EXISTS (SELECT 1 FROM notice_seen s "
				"WHERE s.notice_id=n.id AND s.participant=?) "
				# MEMBERSHIP, not "every notice". A broadcast now reaches the
				# audience frozen at publication and nobody else.
				"AND EXISTS (SELECT 1 FROM notice_audience a "
				"WHERE a.notice_id=n.id AND a.participant=?) "
				"ORDER BY n.created_ts, n.id",
				(participant, participant)).fetchall()
			unseen = []
			for row in rows:
				if limit is not None and len(unseen) >= limit:
					break
				if _notice_expired(row["created_ts"], row["ttl_seconds"], now):
					continue
				self.conn.execute(
					"INSERT INTO notice_seen(notice_id, participant, seen_ts) "
					"VALUES(?,?,?)", (row["id"], participant, now))
				entry = dict(row)
				entry["seen_ts"] = now
				entry["parts"] = self._read_parts("notice", row["id"])
				unseen.append(entry)
			_fault("see:selected")
			self._txn_commit()
			return unseen
		except BaseException:
			self._txn_rollback()
			raise

	def _part_metadata(self, owner_kind: str, owner_id: str) -> list[dict]:
		"""Non-content description of a part tree, for PREVIEW.

		Structure, types and sizes -- enough for a human to see that a message
		has three parts, that one is a PDF and one is an attachment, and to
		decide whether to open it. Deliberately excludes every content key
		(`text`, `base64`, `body`) and the external `root_id`/`path`, so a
		preview can never become an unreceipted delivery path or leak where
		evidence lives on disk.

		One helper for both preview surfaces, so the exclusion cannot drift
		apart between messages and notices.

		Reads the `parts` rows DIRECTLY and never joins `contents`. Stripping
		content after loading it would still have read it: a quick preview of
		a 10 MB part would pull 10 MB off disk to return a size and a media
		type. Excluding a key from the output is not the same as not reading
		the bytes, and only the second one is cheap."""
		rows = self.conn.execute(
			"SELECT part_id, parent_part_id, ordinal, content_type, disposition, "
			"part_name, storage, size FROM parts WHERE owner_kind=? AND owner_id=? "
			"ORDER BY ordinal", (owner_kind, owner_id)).fetchall()
		by_parent: dict = {}
		for row in rows:
			by_parent.setdefault(row["parent_part_id"], []).append(row)
		seen: set = set()

		def build(parent_id, prefix=""):
			out = []
			for row in sorted(by_parent.get(parent_id, []), key=lambda r: r["ordinal"]):
				if row["part_id"] in seen:
					raise BatonError(
						f"part tree for {owner_kind} {owner_id!r} contains a cycle", EXIT_DAMAGE)
				seen.add(row["part_id"])
				address = f"{prefix}{row['ordinal']}"
				container = is_container_type(row["content_type"])
				entry = {
					"address": address,
					"content_type": row["content_type"],
					"disposition": row["disposition"],
					"part_name": row["part_name"],
					"size": row["size"],
					"storage": row["storage"],
					"is_container": container,
				}
				if container:
					entry["parts"] = build(row["part_id"], address + ".")
				out.append(entry)
			return out
		tree = build(None)
		if len(seen) != len(rows):
			raise BatonError(
				f"part tree for {owner_kind} {owner_id!r} has unreachable row(s)", EXIT_DAMAGE)
		return tree

	def preview_message(self, message_id: str, participant: str) -> dict:
		"""Read-only preview of a message addressed to this participant.

		What the inbox detail pane shows BEFORE the human commits to anything:
		headers, state, and the shape of the content. It creates no claim and
		returns no delivery content -- reading the full text is the separate,
		explicit `claim and open` action, which is the only thing that takes
		ownership and starts the reply/close obligation."""
		self._check_identity(participant)
		# Headers only. `get_message` would load the whole part tree with its
		# inline bodies just to hand back a subject line.
		msg = self.conn.execute(
			"SELECT id, from_participant, to_participant, kind, subject, thread_id, "
			"retention, content_type, outcome, created_ts, state, responds_to "
			"FROM messages WHERE id=?", (message_id,)).fetchone()
		if msg is None:
			raise BatonError(f"unknown message {message_id!r}", EXIT_NONE)
		if msg["to_participant"] != participant:
			raise BatonError(
				f"message {message_id!r} is addressed to {msg['to_participant']!r}, "
				f"not {participant!r}")
		out = dict(msg)
		out["parts"] = self._part_metadata("message", message_id)
		return out

	def list_notices(self, participant: str) -> list[dict]:
		"""Live notices this participant has not seen, WITHOUT committing a
		receipt. Read-only: no transaction, no write lock.

		`see` is the consuming read -- it commits the receipt in the same
		transaction that returns the bytes, which is what makes broadcast
		at-most-once. That is correct for an agent draining its queue and
		fatal for a console: an inbox that polls would consume every broadcast
		the instant it rendered one, and a crash a frame later would lose it
		with nothing recording that it existed.

		So observation is separated from acknowledgement. A console lists with
		this, renders the SUBJECTS, and commits the receipt through
		`mark_notice_seen` when the human actually opens one.

		**Metadata only: this returns no content bytes, ever.** That is the
		whole discipline. If listing returned content it would become a second
		delivery path that hands out broadcast bytes with no receipt behind
		it, and the at-most-once guarantee would then depend on which API a
		caller happened to use. Content has exactly one door, and that door
		commits the receipt in the same transaction."""
		self._check_identity(participant)
		now = _utc_now_iso()
		out = []
		for row in self.conn.execute(
				"SELECT n.id, n.from_participant, n.kind, n.subject, n.content_type, "
				"n.created_ts, n.ttl_seconds, n.audience_kind, n.selector, n.possible_duplicate FROM notices n "
				"WHERE NOT EXISTS (SELECT 1 FROM notice_seen s "
				"WHERE s.notice_id=n.id AND s.participant=?) "
				"AND EXISTS (SELECT 1 FROM notice_audience a "
				"WHERE a.notice_id=n.id AND a.participant=?) "
				"ORDER BY n.created_ts, n.id", (participant, participant)):
			if _notice_expired(row["created_ts"], row["ttl_seconds"], now):
				continue
			entry = dict(row)
			entry["seen_ts"] = None
			# Enough to LIST: who, what kind, what subject, when, and how many
			# parts there are. Never what they say.
			entry["parts"] = self._part_metadata("notice", row["id"])
			out.append(entry)
		return out

	def list_notice_activity(self, participant: str) -> list[dict]:
		"""EVERY unexpired notice, with this participant's receipt if there is
		one. READ ONLY: no transaction, no write lock, no receipt.

		`list_notices` is deliberately unseen-only and is left exactly as it
		is, for its existing at-most-once consumers. This is the HISTORY view
		of the same rows, added because a console that dropped a notice the
		instant it was opened made a human watch an announcement disappear
		while they were reading it.

		`seen_ts` is None when this participant has no receipt, and the
		timestamp of their receipt otherwise. It is a LEFT JOIN, per
		participant: two participants have independent seen states over the
		same notice, and neither can see the other's.

		**Metadata only: this returns no content bytes, ever** -- the same
		discipline `list_notices` states, and for the same reason. Content has
		exactly one door and that door commits the receipt in the same
		transaction. A history row is a record that something was said, not a
		second copy of it: after a restart the row is still here and the bytes
		are not, which is what at-most-once MEANS."""
		self._check_identity(participant)
		now = _utc_now_iso()
		out = []
		for row in self.conn.execute(
				"SELECT n.id, n.from_participant, n.kind, n.subject, n.content_type, "
				"n.created_ts, n.ttl_seconds, n.audience_kind, n.selector, n.possible_duplicate, s.seen_ts AS seen_ts FROM notices n "
				"LEFT JOIN notice_seen s "
				"ON s.notice_id = n.id AND s.participant = ? "
				"WHERE EXISTS (SELECT 1 FROM notice_audience a "
				"WHERE a.notice_id=n.id AND a.participant=?) "
				"ORDER BY n.created_ts, n.id", (participant, participant)):
			if _notice_expired(row["created_ts"], row["ttl_seconds"], now):
				# TTL and gc remain the ONLY reason a row leaves this list.
				continue
			entry = dict(row)
			entry["parts"] = self._part_metadata("notice", row["id"])
			out.append(entry)
		return out

	def mark_notice_seen(self, participant: str, notice_id: str) -> dict:
		"""Commit the seen receipt for ONE notice, explicitly.

		The acknowledgement half of `list_notices`, and the ONLY path that
		returns notice content besides `see`. Receipt and content commit in
		one transaction, so the at-most-once window is exactly where it has
		always been: a crash after the commit loses the notice, and a crash
		before it leaves the notice deliverable.

		Repeating it is harmless but is NOT a second delivery: a notice this
		participant has already seen returns the existing receipt and listing
		metadata, with `already_seen` true and no content. A console that
		redraws must not turn a repeat keystroke into an error, and it must
		not be able to re-read a broadcast by asking twice -- the receipt is
		the record that delivery already happened.

		`see` is unchanged and remains the agent-facing drain."""
		self._check_identity(participant)
		self._txn_begin("see", participant=participant)
		try:
			now = _utc_now_iso()
			row = self.conn.execute(
				"SELECT id, from_participant, kind, subject, content_type, manifest_sha256, "
				"created_ts, ttl_seconds, audience_kind, selector "
				"FROM notices WHERE id=?", (notice_id,)).fetchone()
			if row is None:
				raise BatonError(f"unknown notice {notice_id!r}", EXIT_NONE)
			# AUTHORIZED AGAINST THE FROZEN AUDIENCE, in this transaction.
			#
			# `see`, `list_notices` and `list_notice_activity` all select BY
			# membership, so scope holds there by construction. This path
			# selects by ID, which is a different question -- and without this
			# check any configured participant who learned a scoped notice's id
			# could read team-only content and record a receipt for it.
			#
			# The refusal is deliberately identical to "unknown notice": a
			# distinguishable one would confirm the id exists, which is itself
			# information the non-member is not entitled to.
			member = self.conn.execute(
				"SELECT 1 FROM notice_audience WHERE notice_id=? AND participant=?",
				(notice_id, participant)).fetchone()
			if member is None:
				raise BatonError(f"unknown notice {notice_id!r}", EXIT_NONE)
			if _notice_expired(row["created_ts"], row["ttl_seconds"], now):
				raise BatonError(f"notice {notice_id!r} has expired", EXIT_NONE)
			existing = self.conn.execute(
				"SELECT seen_ts FROM notice_seen WHERE notice_id=? AND participant=?",
				(notice_id, participant)).fetchone()
			entry = dict(row)
			if existing is not None:
				# Already seen: harmless to repeat, but NOT delivered again.
				# Returning the content on a second open would make broadcast
				# repeatable for anyone who kept asking, which is precisely the
				# at-most-once guarantee the receipt exists to create. The
				# receipt is the record that delivery already happened.
				entry["seen_ts"] = existing["seen_ts"]
				entry["already_seen"] = True
				# Same shape as a listing entry, integrity digest included:
				# the caller is being told "already delivered", not handed a
				# second delivery, so it gets exactly what a preview gets.
				entry.pop("manifest_sha256", None)
				entry["parts"] = self._part_metadata("notice", notice_id)
				self._txn_commit()
				return entry
			self.conn.execute(
				"INSERT INTO notice_seen(notice_id, participant, seen_ts) VALUES(?,?,?)",
				(notice_id, participant, now))
			entry["seen_ts"] = now
			entry["already_seen"] = False
			entry["parts"] = self._read_parts("notice", notice_id)
			self._txn_commit()
			return entry
		except BaseException:
			self._txn_rollback()
			raise

	def reopen_claim(self, claim_id: str, participant: str) -> dict:
		"""Re-read the delivery of an ACTIVE claim this participant already
		holds. Creates no claim and writes no ledger row.

		A console cannot keep the only readable copy of a delivery in process
		memory: restart it and the human holds a claim they can no longer see,
		with `reply` and `close` still owed. `claim` cannot be used to recover
		it -- the message is no longer pending, and claiming again would be a
		second claim.

		Two properties this needs that a bare row read does not have:

		- **Ownership is enforced.** `get_claim` deliberately has none, because
		  every disposition path re-validates before it acts. This is the
		  first read path that returns CONTENT, so it is the first place the
		  check has to exist.
		- **External pins are revalidated.** Re-reading stored parts does not
		  re-verify a pinned file, so a pin broken since the claim would
		  otherwise be handed back as though still good.

		On damage it fails closed WITHOUT content, but still returns the
		envelope metadata and the failure -- the holder must be able to see
		what they are holding in order to dispose of it. Note the exit: a
		damaged pin cannot be quarantined while the claim is active, so the
		path out is `close`, then quarantine."""
		row = self._load_active_claim(claim_id, participant)
		if row["claim_state"] != "active":
			raise BatonError(
				f"claim {claim_id!r} is {row['claim_state']}, not active", EXIT_PROTOCOL)
		message_id = row["message_id"]
		try:
			self.verify_attachment(message_id)
		except BatonError as exc:
			if exc.exit_code != EXIT_DAMAGE:
				raise
			msg = self.get_message(message_id)
			return {
				"claim": self.get_claim(claim_id),
				"message": {k: msg[k] for k in (
					"id", "from_participant", "to_participant", "kind", "subject",
					"thread_id", "retention", "outcome", "created_ts", "state",
					"responds_to")},
				"content": None,
				"damaged": str(exc),
				"disposition_path": "close this claim, then quarantine the message",
			}
		return {**_delivery(self, self.get_claim(claim_id)), "damaged": None}

	def has_unseen_notice(self, participant: str) -> bool:
		"""READ-ONLY probe: does a live notice exist that this participant
		has not seen? `see` opens a write transaction, and a waiter polls
		indefinitely — without this probe an idle waiter would BEGIN IMMEDIATE
		on every poll, contending with real writers and letting an unrelated
		transient busy (EXIT_RACE) stand it down. `claim` already reads for a
		candidate before transacting; this is the notice-side equivalent.
		Racing is harmless: `see` re-filters under the write lock and simply
		returns nothing if the notice expired or was consumed meanwhile."""
		now = _utc_now_iso()
		for row in self.conn.execute(
				"SELECT n.created_ts, n.ttl_seconds FROM notices n "
				"WHERE NOT EXISTS (SELECT 1 FROM notice_seen s "
				"WHERE s.notice_id=n.id AND s.participant=?) "
				# THE SAME PREDICATE `see` USES. Without it the probe reports
				# work for a scoped notice addressed to another team, and the
				# waiter takes a write transaction to `see` that returns
				# nothing -- reintroducing exactly the idle contention this
				# probe exists to avoid, and doing it across teams.
				"AND EXISTS (SELECT 1 FROM notice_audience a "
				"WHERE a.notice_id=n.id AND a.participant=?)",
				(participant, participant)):
			if not _notice_expired(row["created_ts"], row["ttl_seconds"], now):
				return True
		return False

	def expire(self, participant: str, *,
	           notice_id: str | None = None) -> list[str]:
		"""Delete expired notices (and, via CASCADE, their seen rows) plus
		their content rows in ONE transaction. An explicit id may also be
		expired early by its author."""
		self._check_identity(participant)
		self._txn_begin("expire", participant=participant)
		try:
			now = _utc_now_iso()
			if notice_id is not None:
				rows = self.conn.execute(
					"SELECT id, from_participant, created_ts, "
					"ttl_seconds FROM notices WHERE id=?", (notice_id,)).fetchall()
				if not rows:
					raise BatonError(f"unknown notice {notice_id!r}", EXIT_NONE)
			else:
				rows = self.conn.execute(
					"SELECT id, from_participant, created_ts, "
					"ttl_seconds FROM notices").fetchall()
			removed = []
			for row in rows:
				elapsed = _notice_expired(row["created_ts"], row["ttl_seconds"], now)
				exact_author = row["from_participant"] == participant
				if not elapsed and not (notice_id is not None and exact_author):
					if notice_id is not None:
						raise BatonError(
							f"notice {notice_id!r} is not expired and the caller is not its exact "
							f"authoring participant; a dead author's notice is "
							f"swept when its TTL elapses")
					continue
				self._delete_parts("notice", row["id"])
				self.conn.execute("DELETE FROM notices WHERE id=?", (row["id"],))
				removed.append(row["id"])
			self._txn_commit()
			return removed
		except BaseException:
			self._txn_rollback()
			raise

	# -- recovery -----------------------------------------------------------

	def recover_claim(self, claim_id: str, *, participant: str,
	                  reason: str) -> dict:
		"""Capability-authorized recovery of an abandoned claim: the recovering identity
		must hold the config-declared 'recovery' capability. Closes the exact
		immutable claim attempt as recovered, records the audit row with the
		recovering participant, and re-pends the message — one
		transaction; history is never rewritten."""
		if type(reason) is not str or not reason.strip():
			raise BatonError("recovery requires a non-empty --reason")
		self._require_capability(participant, "recovery", "claim recovery")
		self._txn_begin("recover", participant=participant)
		try:
			row = self.conn.execute(
				"SELECT c.state, c.message_id, m.state AS message_state FROM claims c "
				"JOIN messages m ON m.id=c.message_id WHERE c.claim_id=?", (claim_id,)).fetchone()
			if row is None:
				raise BatonError(f"unknown claim {claim_id!r}", EXIT_NONE)
			if row["state"] != "active":
				raise BatonError(f"claim {claim_id!r} is {row['state']}, not active; nothing to recover")
			now = _utc_now_iso()
			recovery_id = new_id()
			self.conn.execute(
				"UPDATE claims SET state='recovered', terminal_ts=? WHERE claim_id=?", (now, claim_id))
			self.conn.execute(
				"INSERT INTO recoveries(recovery_id, claim_id, participant, reason, created_ts) "
				"VALUES(?,?,?,?,?)", (recovery_id, claim_id, participant, reason, now))
			cur = self.conn.execute(
				"UPDATE messages SET state='pending', completed_ts=NULL WHERE id=? AND state='claimed'",
				(row["message_id"],))
			if cur.rowcount != 1:
				raise BatonError(
					f"message for claim {claim_id!r} is {row['message_state']!r}, not claimed", EXIT_DAMAGE)
			self._txn_commit()
			return {"recovery_id": recovery_id, "claim_id": claim_id, "message_id": row["message_id"]}
		except BaseException:
			self._txn_rollback()
			raise

	def _committed_quarantine(self, message_id: str, participant: str, reason: str) -> dict | None:
		"""Read-only retry resolution. Returns the committed disposition for an
		EXACT retry, None when no record exists, and fails closed when the
		record exists under a different identity or reason — the full
		(participant, reason) pair is the retry identity, so a
		second operator cannot silently inherit someone else's audit row."""
		row = self.conn.execute(
			"SELECT * FROM quarantines WHERE message_id=?", (message_id,)).fetchone()
		if row is None:
			return None
		mismatch = [name for name, offered in (
			("participant", participant), ("reason", reason))
			if row[name] != offered]
		if mismatch:
			raise BatonError(
				f"message {message_id!r} already has a committed quarantine; retried "
				f"{', '.join(mismatch)} differs from the committed record — refusing to "
				f"re-label an audit record", EXIT_PROTOCOL)
		state = self.conn.execute(
			"SELECT state FROM messages WHERE id=?", (message_id,)).fetchone()["state"]
		return {"already_committed": True, "quarantine_id": row["quarantine_id"],
		        "message_id": message_id, "prior_state": row["prior_state"],
		        "state": state, "failure": row["failure"], "created_ts": row["created_ts"]}

	def quarantine_attachment(self, message_id: str, *, participant: str,
	                          reason: str) -> dict:
		"""Capability-authorized disposition for a message whose pinned
		attachment can no longer be verified. `claim` already SKIPS such a
		message so it cannot block the queue; this is how it stops being
		unresolved.

		It is deliberately NOT a claim. A claim asserts that Baton verified
		the message well enough to deliver it, and damaged content was never
		delivered — recording it as claimed-and-closed would put a lie in the
		ledger. Instead the message reaches a terminal `quarantined` state and
		an immutable `quarantines` row records the ORIGINAL pin alongside the
		observed failure, so the evidence of what was published survives the
		disposition. The message's own attach_* columns are never touched.

		An already-terminal message keeps its state: its content really was
		delivered, and only the retained attachment later went stale, so the
		quarantine row is an acknowledgement rather than a state change. That
		is the case that restores instance health without rewriting history.

		One transaction. Exact retry is idempotent; a retry with a different
		reason fails closed rather than silently re-labelling the record."""
		if type(reason) is not str or not reason.strip():
			raise BatonError("quarantine requires a non-empty --reason")
		self._require_capability(participant, "recovery", "attachment quarantine")
		self.get_message(message_id)
		external = self._external_leaves(self._read_parts("message", message_id))
		if not external:
			raise BatonError(
				f"message {message_id!r} has no externally stored part; quarantine applies "
				"only to messages with pinned external content")
		# Committed retry identity is settled BEFORE any external file is
		# consulted. The attachment is mutable and outside our control — if
		# someone restores the original bytes after a committed quarantine, an
		# exact retry must still redeliver the committed record rather than
		# fail as "verifies cleanly". Effectively-once cannot depend on the
		# world holding still.
		committed = self._committed_quarantine(message_id, participant, reason)
		if committed is not None:
			return committed
		# Only now the read-only file IO, and outside the write lock, exactly
		# as claim's own pin check is.
		damaged_part = None
		for part in external:
			try:
				self._verify_external_part(part)
			except BatonError as exc:
				if exc.exit_code != EXIT_DAMAGE:
					raise
				# The FIRST damaged part in manifest order is what the audit
				# row records. A message with several damaged parts is still
				# one quarantine: the disposition is of the message, and the
				# recorded part is the evidence that justified it.
				damaged_part, failure = part, str(exc)
				break
		if damaged_part is None:
			raise BatonError(
				f"message {message_id!r} verifies cleanly; refusing to quarantine an "
				"undamaged message")
		self._txn_begin("quarantine", participant=participant,
		                ceremony="quarantine")
		try:
			row = self.conn.execute(
				"SELECT state FROM messages WHERE id=?", (message_id,)).fetchone()
			if row is None:
				raise BatonError(f"unknown message {message_id!r}", EXIT_NONE)
			state = row["state"]
			# Repeat under the write lock: another writer may have committed
			# the same quarantine between the pre-check and the lock.
			existing = self.conn.execute(
				"SELECT * FROM quarantines WHERE message_id=?", (message_id,)).fetchone()
			if existing is not None:
				self._txn_rollback()
				result = self._committed_quarantine(message_id, participant, reason)
				if result is None:  # raced with a DIFFERENT identity/reason
					raise BatonError(
						f"message {message_id!r} was quarantined concurrently by another "
						"identity or reason", EXIT_RACE)
				return result
			if state == "claimed":
				raise BatonError(
					f"message {message_id!r} is claimed; resolve or recover the claim before "
					"quarantining", EXIT_RACE)
			now = _utc_now_iso()
			quarantine_id = new_id()
			ref = damaged_part["attach"]
			self.conn.execute(
				"INSERT INTO quarantines(quarantine_id, message_id, participant, "
				"reason, prior_state, part_id, part_ordinal, content_type, root_id, path, "
				"sha256, size, generation, failure, created_ts) "
				"VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
				(quarantine_id, message_id, participant, reason, state,
				 damaged_part["part_id"], damaged_part["address"],
				 damaged_part["content_type"], ref["root_id"], ref["path"],
				 damaged_part["sha256"], damaged_part["size"], ref["generation"],
				 failure, now))
			if state == "pending":
				cur = self.conn.execute(
					"UPDATE messages SET state='quarantined', completed_ts=? "
					"WHERE id=? AND state='pending'", (now, message_id))
				if cur.rowcount != 1:
					# Another writer claimed it between the read and the lock.
					raise BatonError(
						f"message {message_id!r} changed state during quarantine", EXIT_RACE)
				final_state = "quarantined"
			else:
				final_state = state  # already terminal: acknowledge, never rewrite
			self._txn_commit()
			return {"already_committed": False, "quarantine_id": quarantine_id,
			        "message_id": message_id, "prior_state": state, "state": final_state,
			        "failure": failure, "created_ts": now}
		except sqlite3.IntegrityError as exc:
			self._txn_rollback()
			raise BatonError(f"quarantine lost a race: {exc}", EXIT_RACE) from exc
		except BaseException:
			self._txn_rollback()
			raise

	def quarantined_message_ids(self) -> set[str]:
		"""Message ids with a committed quarantine acknowledgement."""
		return {row[0] for row in self.conn.execute("SELECT message_id FROM quarantines")}

	# -- gc ------------------------------------------------------------------

	def gc(self, *, participant: str, now: str | None = None) -> dict:
		"""Bounded deletion of TRANSIENT terminal message metadata older than
		retention_days, plus expired-notice sweep. Durable messages and the
		transitions/recoveries audit trail are permanent. Every deletion
		emits a final ledger event via the gc triggers."""
		self._check_identity(participant)
		retention_days = self.config.get("retention_days", DEFAULT_RETENTION_DAYS)
		now_ts = now if now is not None else _utc_now_iso()
		cutoff = _iso_minus_days(now_ts, retention_days)
		self._txn_begin("gc", participant=participant)
		try:
			# Retention-graph fixpoint (reply links form deletion dependencies
			# in BOTH directions): start from aged transient terminal messages
			# with no recovery-referenced claim, then iteratively remove any
			# candidate anchored by retained protocol state —
			#   (a) a responds_to child OUTSIDE the candidate set (the child
			#       row references its parent), or
			#   (b) a disposition belonging to a claim on a message OUTSIDE
			#       the set whose response_message_id names the candidate
			#       (a RETAINED disposition is the immutable retry-identity
			#       authority, so its transient response stays retained as
			#       metadata — the pinned contract), or
			#   (c) one of the candidate's OWN dispositions is durable — a
			#       durable close on a transient envelope is a retained
			#       record; the delivery envelope's retention never deletes
			#       a durable disposition body.
			# The surviving component deletes cleanly: dispositions → claims →
			# messages children-first in an order derived from the actual
			# responds_to graph → contents. One call always makes its bounded
			# progress or returns empty; it can never abort on a valid graph
			# (a corrupted/self-referential graph fails closed instead).
			# A quarantine row is permanent audit that references the message,
			# so a quarantined subject is a RETAINED ANCHOR exactly as a
			# recovery-referenced one is. Without this the message stays a
			# candidate, its disposition and claim get deleted, and the
			# message delete then fails the foreign key — rolling the whole
			# transaction back, so one valid audit record would make bounded
			# GC fail forever.
			candidates = {row[0] for row in self.conn.execute(
				"SELECT m.id FROM messages m WHERE m.retention='transient' "
				"AND m.state IN ('completed','closed') AND m.completed_ts < ? "
				"AND NOT EXISTS (SELECT 1 FROM claims c JOIN recoveries rec ON rec.claim_id=c.claim_id "
				"WHERE c.message_id = m.id) "
				"AND NOT EXISTS (SELECT 1 FROM quarantines q WHERE q.message_id = m.id)",
				(cutoff,))}
			while True:
				anchored = set()
				for mid in candidates:
					children = [r[0] for r in self.conn.execute(
						"SELECT id FROM messages WHERE responds_to=?", (mid,))]
					if any(child not in candidates for child in children):
						anchored.add(mid)
						continue
					holders = [r[0] for r in self.conn.execute(
						"SELECT c.message_id FROM dispositions d JOIN claims c ON c.claim_id=d.claim_id "
						"WHERE d.response_message_id=?", (mid,))]
					if any(holder not in candidates for holder in holders):
						anchored.add(mid)
						continue
					durable_own = self.conn.execute(
						"SELECT 1 FROM dispositions d JOIN claims c ON c.claim_id=d.claim_id "
						"WHERE c.message_id=? AND d.retention='durable' LIMIT 1", (mid,)).fetchone()
					if durable_own is not None:
						anchored.add(mid)
				if not anchored:
					break
				candidates -= anchored
			removed_messages = []
			if candidates:
				# Children-first order derived from the responds_to references
				# themselves (timestamps can tie within one second): a message
				# is deletable once no REMAINING component member references
				# it as a parent.
				parents = {mid: self.conn.execute(
					"SELECT responds_to FROM messages WHERE id=?", (mid,)).fetchone()[0]
					for mid in candidates}
				remaining = set(candidates)
				ordered = []
				while remaining:
					referenced = {parents[m] for m in remaining if parents[m] in remaining}
					leaves = sorted(remaining - referenced)
					if not leaves:
						raise BatonError("gc: responds_to cycle in candidate component", EXIT_DAMAGE)
					ordered.extend(leaves)
					remaining -= set(leaves)
				for mid in ordered:
					for (cid,) in self.conn.execute(
							"SELECT claim_id FROM claims WHERE message_id=?", (mid,)).fetchall():
						disp = self.conn.execute(
							"SELECT claim_id FROM dispositions WHERE claim_id=?", (cid,)).fetchone()
						if disp is not None:
							self._delete_parts("disposition", cid)
							self.conn.execute("DELETE FROM dispositions WHERE claim_id=?", (cid,))
						self.conn.execute("DELETE FROM claims WHERE claim_id=?", (cid,))
				for mid in ordered:
					self._delete_parts("message", mid)
					self.conn.execute("DELETE FROM messages WHERE id=?", (mid,))
					removed_messages.append(mid)
			expired = []
			for row in self.conn.execute(
					"SELECT id, created_ts, ttl_seconds FROM notices").fetchall():
				if _notice_expired(row["created_ts"], row["ttl_seconds"], now_ts):
					self._delete_parts("notice", row["id"])
					self.conn.execute("DELETE FROM notices WHERE id=?", (row["id"],))
					expired.append(row["id"])
			self._txn_commit()
			return {"messages": removed_messages, "notices": expired, "cutoff": cutoff}
		except BaseException:
			self._txn_rollback()
			raise

	# -- reads --------------------------------------------------------------

	def get_message(self, message_id: str) -> dict:
		row = self.conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown message {message_id!r}", EXIT_NONE)
		out = dict(row)
		out["parts"] = self._read_parts("message", message_id) if row["manifest_sha256"] else []
		return out

	def materialize_part(self, message_id: str, target_dir: str, *,
	                     prefix: str = "message", part: str = "0") -> str:
		"""Project ONE part to a file, from an already-open instance.

		The console holds a store; reopening the instance to write a
		projection would be a second connection to the same authority for no
		reason. Same naming and same refusals as the CLI entry point, because
		both call one function.

		NOTE: like the CLI entry point, this does not require a claim. A
		console must use `materialize_claimed_part` instead -- writing content
		the human has not claimed would defeat the preview boundary."""
		return _project_part(self.get_message(message_id), message_id,
		                     target_dir, prefix, part)

	def read_claimed_external_part(self, claim_id: str, participant: str, *,
	                               part: str, max_bytes: int = 1 << 20) -> dict:
		"""The BYTES of an EXTERNAL part of a message this participant has
		actively claimed, for display. READ ONLY: no claim, no receipt, no
		transition, no audit row, and nothing is written to disk.

		Why this exists. An external leaf carries a pin instead of bytes, so
		the delivered envelope has nothing for a console to render -- and the
		console showed the header and then said nothing else, which a human
		reading a licence file quite reasonably reported as "I can only view
		part 0". Materializing is not the answer either: the part is already a
		file and the core refuses to copy it into a projection, which is the
		right rule and leaves reading it unsolved.

		Ownership is enforced HERE, like every other path that returns
		content, and the pin is REVALIDATED before a byte is read -- the same
		reason `reopen_claim` and `materialize_claimed_part` do it. Showing
		bytes that no longer match the pin would be showing the human
		something the sender did not send.

		Bounded: a caller asking to display a file gets at most `max_bytes`,
		and is told when it was truncated. A console that tried to wrap a
		gigabyte would take the terminal down, and the pane can show a few
		hundred lines at most anyway.

		The path is never taken from the advisory `part_name`: it is the pinned
		root id and relative path, resolved by the same component-wise
		no-follow walk that pinned it."""
		row = self._load_active_claim(claim_id, participant)
		if row["claim_state"] != "active":
			raise BatonError(
				f"claim {claim_id!r} is {row['claim_state']}, not active", EXIT_PROTOCOL)
		message_id = row["message_id"]
		node = resolve_part(self._read_parts("message", message_id), part)
		if node["parts"] is not None:
			raise BatonError(
				f"part {part!r} of message {message_id!r} is a "
				f"{node['content_type']} container; address one of its leaves")
		if node["storage"] != STORAGE_EXTERNAL:
			raise BatonError(
				f"part {part!r} of message {message_id!r} is not externally "
				f"stored; its bytes travel in the delivery envelope")
		# Fails closed on a broken pin, exactly as delivery does.
		self._verify_external_part(node)
		ref = node["attach"]
		root = self.config.get("roots", {})[ref["root_id"]]
		fd = _open_root_dir(root)
		try:
			components = ref["path"].split("/")
			for component in components[:-1]:
				nxt = os.open(component, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
				              dir_fd=fd)
				os.close(fd)
				fd = nxt
			leaf = os.open(components[-1],
			               os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
			               dir_fd=fd)
			try:
				with os.fdopen(leaf, "rb", closefd=False) as handle:
					body = handle.read(max_bytes + 1)
			finally:
				os.close(leaf)
		finally:
			try:
				os.close(fd)
			except OSError:
				pass
		truncated = len(body) > max_bytes
		return {"address": part, "content_type": node["content_type"],
		        "size": node["size"], "sha256": node["sha256"],
		        "root_id": ref["root_id"], "path": ref["path"],
		        "body": body[:max_bytes], "truncated": truncated}

	def materialize_claimed_part(self, claim_id: str, participant: str,
	                             target_dir: str, *, prefix: str = "message",
	                             part: str = "0") -> str:
		"""Project a part of a message this participant has ACTIVELY CLAIMED.

		The console's materialize path. Ownership is enforced HERE rather than
		in the UI, because a rule that lives only in the front end is one
		refactor away from not existing: the preview boundary says content is
		not readable until the human explicitly claims, and writing bytes to
		disk is reading them in the most durable possible way.

		External pins are revalidated first, for the same reason `reopen_claim`
		does it: a projection of content whose pin broke would put stale bytes
		on disk under a name implying they are the delivered ones."""
		row = self._load_active_claim(claim_id, participant)
		if row["claim_state"] != "active":
			raise BatonError(
				f"claim {claim_id!r} is {row['claim_state']}, not active", EXIT_PROTOCOL)
		message_id = row["message_id"]
		self.verify_attachment(message_id)
		return _project_part(self.get_message(message_id), message_id,
		                     target_dir, prefix, part)

	def list_sent(self, participant: str, limit: int | None = None) -> list[dict]:
		"""Outbound history for this participant, newest first. READ ONLY.

		Authority-backed on purpose. A console could remember what it sent
		this session, but that list lies the moment the process restarts and
		lies again the moment someone else claims the message -- and the whole
		value of a sent view is watching pending become claimed. So the state
		comes from the same rows that decide it.

		Directed messages authored here, including the response messages that
		replies create, and authored notices while they remain retained.
		Retention and gc stay authoritative: a row that has been collected is
		gone from here too, because this is a view, not an archive.

		No transaction and no write lock: this must never be able to move
		anything, and a caller holding a claim must be able to run it.

		`limit` defaults to NO LIMIT. A default cap would mean older durable
		subjects sat in the authority, unreachable, while the view called
		itself history -- and nothing on screen would say so. Retention and gc
		already bound how much there is; a second, silent bound here would
		only hide what they kept. A caller that genuinely wants a page may
		still pass one."""
		self._check_identity(participant)
		out: list[dict] = []
		for row in self.conn.execute(
				"SELECT id, to_participant, kind, subject, retention, outcome, "
				"created_ts, state, responds_to, completed_ts "
				"FROM messages WHERE from_participant=? "
				"ORDER BY created_ts DESC, id DESC LIMIT ?",
				(participant, _sql_limit(limit))).fetchall():
			item = dict(row)
			item["row_kind"] = "message"
			# `state` already distinguishes completed-by-reply from closed,
			# expired and quarantined, so the view needs no second source of
			# truth for what happened to a message.
			out.append(item)
		for row in self.conn.execute(
				"SELECT id, kind, subject, created_ts, ttl_seconds "
				"FROM notices WHERE from_participant=? "
				"ORDER BY created_ts DESC, id DESC LIMIT ?",
				(participant, _sql_limit(limit))).fetchall():
			item = dict(row)
			item["row_kind"] = "notice"
			item["to_participant"] = None
			# A notice has no claim and therefore no directed state. What it
			# HAS is receipts and a lifetime, and reporting those is honest
			# where borrowing `pending`/`claimed` would not be.
			item["seen_count"] = self.conn.execute(
				"SELECT COUNT(*) FROM notice_seen WHERE notice_id=?",
				(row["id"],)).fetchone()[0]
			item["expires_ts"] = (_parse_ts(row["created_ts"])
			                      + dt.timedelta(seconds=row["ttl_seconds"])
			                      ).strftime(_TS_FMT)
			out.append(item)
		out.sort(key=lambda item: (item["created_ts"], item["id"]), reverse=True)
		return out if limit is None else out[:limit]

	def list_messages(self, participant: str, limit: int | None = None) -> list[dict]:
		"""EVERY retained message this participant SENT OR RECEIVED, whatever
		its state. READ ONLY.

		One list across the whole lifecycle AND both directions. Two failures
		drove this, both found by using it: answering a message made the
		original vanish, and sending one made the new message vanish, because
		outbound lived only behind another key. Here the row stays put and its
		BADGE changes, which is what "I dealt with that" looks like.

		Each row carries `direction`, `in` or `out`. Only inbound rows are
		ever actionable; outbound rows are someone else's obligation and must
		not be mistakable for work owed.

		Returned in the total order `(created_ts, id)` ASCENDING, matching the
		order `claim` itself would choose. That is a stable base, not a
		presentation decision: which end a consumer puts at the top is the
		consumer's, and the console presents this list newest-first. Handled
		rows keep their place in the order rather than being sorted away,
		because their position is part of the story.

		Each row carries `responds_to` -- the message it is in reference to --
		and `thread_id`, so a consumer can render a thread, and author a
		follow-up that inherits the thread, without a second query per row.
		Both are the schema's own columns, reported rather than derived.

		No cap: retention and gc already bound this, and a second silent bound
		would only hide what they kept."""
		self._check_identity(participant)
		out = []
		for row in self.conn.execute(
				"SELECT m.id, m.from_participant, m.to_participant, m.kind, "
				"m.subject, m.retention, m.outcome, m.created_ts, m.state, "
				"m.completed_ts, m.responds_to, m.thread_id, "
				"d.kind AS disposition_kind, d.outcome AS disposition_outcome, "
				"c.claim_id AS claim_id, c.state AS claim_state "
				"FROM messages m "
				"LEFT JOIN claims c ON c.message_id = m.id AND c.participant = ? "
				"AND c.state = 'active' "
				"LEFT JOIN dispositions d ON d.claim_id = ("
				"  SELECT claim_id FROM claims WHERE message_id = m.id "
				"  AND participant = ? ORDER BY claimed_ts DESC LIMIT 1) "
				"WHERE m.to_participant = ? OR m.from_participant = ? "
				"ORDER BY m.created_ts, m.id LIMIT ?",
				(participant, participant, participant, participant,
				 _sql_limit(limit))).fetchall():
			item = dict(row)
			item["row_kind"] = "message"
			# DIRECTION, stated rather than inferred at each call site.
			# Delegated outbound work must never be mistaken for inbound work
			# owed, and a caller deriving it from `to_participant` every time
			# is a caller that will get it wrong once.
			item["direction"] = ("in" if row["to_participant"] == participant
			                     else "out")
			out.append(item)
		return out

	def authorize_read(self, kind: str, owner_id: str, participant: str) -> sqlite3.Row:
		"""May this participant read this message or notice back? Returns the
		row, or refuses INDISTINGUISHABLY from "it does not exist".

		Authority is the immutable publication-time audience, plus the sender:

		- a message: its `from_participant`, or a member of its publication
		  audience;
		- a notice: its author, or a member of its frozen audience WHO HAS
		  ALREADY SEEN IT.

		The receipt requirement on notices is what keeps at-most-once intact.
		Reread is not redelivery -- the recipient already had these bytes --
		but reading one they have NOT been delivered would be a first delivery
		through a door that records nothing. `see` remains the only way to
		receive a notice; this is only the way back to one.

		Recovery does not appear here. It is a capability for repairing
		claims, and the ruling keeps it separate: it does not grant universal
		authority to read other participants' content.

		REFUSALS ARE IDENTICAL for "no such thing" and "not yours", so the
		read surface is not an enumeration oracle -- a non-party learns
		nothing from it, including whether an id exists.
		"""
		self._check_identity(participant)
		absent = BatonError(f"unknown {kind} {owner_id!r}", EXIT_NONE)
		if kind == "message":
			row = self.conn.execute(
				"SELECT * FROM messages WHERE id=?", (owner_id,)).fetchone()
			if row is None:
				raise absent
			if row["from_participant"] == participant:
				return row
			member = self.conn.execute(
				"SELECT 1 FROM publication_audience WHERE publication_id=? AND participant=?",
				(row["publication_id"], participant)).fetchone()
			if member is None:
				raise absent
			return row
		row = self.conn.execute(
			"SELECT * FROM notices WHERE id=?", (owner_id,)).fetchone()
		if row is None:
			raise absent
		if row["from_participant"] == participant:
			return row
		member = self.conn.execute(
			"SELECT 1 FROM notice_audience WHERE notice_id=? AND participant=?",
			(owner_id, participant)).fetchone()
		seen = self.conn.execute(
			"SELECT 1 FROM notice_seen WHERE notice_id=? AND participant=?",
			(owner_id, participant)).fetchone()
		if member is None or seen is None:
			raise absent
		return row

	def open_received(self, message_id: str, participant: str) -> dict:
		"""The retained content of something this participant RECEIVED and has
		already finished with. Read-only.

		Owner-checked on the RECIPIENT, which is the opposite end from
		`open_sent` and deliberately a separate method: one function taking
		"either end" would be one edit away from letting anyone read anything.

		Creates no claim and no receipt. The message is already terminal;
		reading it back cannot and must not move it."""
		self._check_identity(participant)
		row = self.conn.execute(
			"SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown message {message_id!r}", EXIT_NONE)
		if row["to_participant"] != participant:
			raise BatonError(
				f"message {message_id!r} was addressed to "
				f"{row['to_participant']!r}, not {participant!r}")
		msg = dict(row)
		msg["parts"] = self._read_parts("message", message_id) if row["manifest_sha256"] else []

		def verify(nodes):
			for node in nodes or []:
				if node.get("parts") is not None:
					verify(node["parts"])
				elif node.get("attach"):
					self._verify_external_part(node)
		verify(msg["parts"])

		envelope = {k: msg[k] for k in (
			"id", "from_participant", "to_participant", "kind", "subject",
			"thread_id", "retention", "outcome", "created_ts", "state", "responds_to")}
		envelope["content"] = _content_repr(
			msg["content_type"], msg.get("parts"), msg["manifest_sha256"])
		return {"received": envelope}

	def open_sent(self, message_id: str, participant: str) -> dict:
		"""The retained content of something this participant SENT, read-only.

		Never creates a claim, never commits a receipt, never transitions
		anything: reading your own outbox is not a delivery, and treating it
		as one would let a sender consume the message they are waiting on.

		Owner-checked, and external pins are revalidated exactly as delivery
		revalidates them. A stale pin fails closed with EXIT_DAMAGE rather
		than handing back whatever is at that path now -- the sender is the
		last person who should be shown bytes that no longer match what the
		recipient will get."""
		self._check_identity(participant)
		row = self.conn.execute(
			"SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown message {message_id!r}", EXIT_NONE)
		if row["from_participant"] != participant:
			raise BatonError(
				f"message {message_id!r} was sent by {row['from_participant']!r}, "
				f"not {participant!r}")
		msg = dict(row)
		msg["parts"] = self._read_parts("message", message_id) if row["manifest_sha256"] else []

		def verify(nodes):
			for node in nodes or []:
				if node.get("parts") is not None:
					verify(node["parts"])
				elif node.get("attach"):
					self._verify_external_part(node)
		verify(msg["parts"])

		envelope = {k: msg[k] for k in (
			"id", "from_participant", "to_participant", "kind", "subject",
			"thread_id", "retention", "outcome", "created_ts", "state", "responds_to")}
		envelope["content"] = _content_repr(
			msg["content_type"], msg.get("parts"), msg["manifest_sha256"])
		return {"sent": envelope}

	def open_sent_notice(self, notice_id: str, participant: str) -> dict:
		"""The same for a notice this participant authored. No receipt is
		committed: a receipt records that a RECIPIENT read a broadcast, and
		the author reading their own is not that."""
		self._check_identity(participant)
		row = self.conn.execute(
			"SELECT * FROM notices WHERE id=?", (notice_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown notice {notice_id!r}", EXIT_NONE)
		if row["from_participant"] != participant:
			raise BatonError(
				f"notice {notice_id!r} was published by {row['from_participant']!r}, "
				f"not {participant!r}")
		notice = dict(row)
		notice["parts"] = self._read_parts("notice", notice_id)
		envelope = {k: notice[k] for k in (
			"id", "from_participant", "kind", "subject", "created_ts", "ttl_seconds",
			# The AUTHOR's copy needs these as much as the recipient's. Without
			# them the renderer sees the legacy shape and draws "everyone", so
			# the one person who knows the notice was scoped is told it was
			# not.
			"audience_kind", "selector")}
		envelope["content"] = _content_repr(
			notice["content_type"], notice.get("parts"), notice["manifest_sha256"])
		return {"sent_notice": envelope}

	def list_participants(self) -> list[dict]:
		"""Every participant this instance accepts, from the VALIDATED config.

		Read-only and side-effect free. A console offers these for selection
		so an address is chosen rather than typed: a mistyped recipient is
		rejected at send time, which costs the human their composed message
		and teaches nothing about which addresses exist.

		Deterministic order, so a one-letter selection means the same thing
		every time the picker opens."""
		participants = self.config.get("participants", {})
		return [{"address": address,
		         "capabilities": tuple(spec.get("capabilities", ())),
		         "has_projection_dir": bool(spec.get("projection_dir"))}
		        for address, spec in sorted(participants.items())]

	def list_roots(self) -> list[dict]:
		"""Every attachment root this instance accepts, from the VALIDATED
		config: `{"root_id", "path"}`, path absolute.

		Read-only and side-effect free, and the same shape of answer as
		`list_participants` for the same reason. A console that asked a human
		to type Baton's `root_id:relative/path` locator would be asking them
		to learn a serialization; offering the roots lets them CHOOSE the
		trust anchor and see where it points, so the security boundary is
		visible at the moment it matters.

		The config roots are what publication validates against, so this is
		the set an attachment can actually name. Deterministic order, so a
		one-letter selection means the same thing every time."""
		roots = self.config.get("roots", {})
		return [{"root_id": root_id, "path": path}
		        for root_id, path in sorted(roots.items())]

	def publication_of(self, publication_id: str | None) -> tuple[list[str], bool]:
		"""The frozen audience and duplicate warning behind one delivery.

		Returns the canonical audience from `publication_audience`, NOT the
		surviving `messages` rows. GC or transient retention can remove one
		recipient's terminal delivery while another has not opened theirs, and
		an audience derived from survivors would silently shrink -- telling the
		remaining reader the work was more private than it was.

		A NULL publication predates the record and reads as a private message
		with no warning, which is what such a row always was.
		"""
		if publication_id is None:
			return [], False
		row = self.conn.execute(
			"SELECT possible_duplicate FROM publications WHERE publication_id=?",
			(publication_id,)).fetchone()
		if row is None:
			return [], False
		members = [r["participant"] for r in self.conn.execute(
			"SELECT participant FROM publication_audience WHERE publication_id=? "
			"ORDER BY participant", (publication_id,))]
		return members, bool(row["possible_duplicate"])

	def publication_deliveries(self, publication_id: str) -> dict:
		"""Which message each recipient of one publication received.

		The mapping the stage plan pinned and the return value never carried.
		A caller that addressed three participants got one publication id and
		no way to say "and THIS is the delivery I made to the reviewer" -- so
		following up on one recipient's copy meant querying the store for
		something the publishing call already knew.

		Read from `messages`, deliberately, unlike `publication_of` which
		reads the canonical audience. The question here is "what delivery
		exists for whom", and a collected delivery genuinely has no message to
		name. An audience member missing from this mapping is information, not
		an error -- `doctor` is what decides whether it is a problem.
		"""
		return {row["to_participant"]: row["id"] for row in self.conn.execute(
			"SELECT to_participant, id FROM messages WHERE publication_id=? "
			"ORDER BY to_participant", (publication_id,))}

	def get_claim(self, claim_id: str) -> dict:
		row = self.conn.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
		if row is None:
			raise BatonError(f"unknown claim {claim_id!r}", EXIT_NONE)
		return dict(row)

	def scan(self, participant: str | None = None) -> dict:
		where = "WHERE to_participant=?" if participant else ""
		args = (participant,) if participant else ()
		pending = [dict(r) for r in self.conn.execute(
			f"SELECT id, from_participant, to_participant, kind, subject, thread_id, created_ts "
			f"FROM messages {where} {'AND' if where else 'WHERE'} state='pending' ORDER BY created_ts", args)]
		claimed = [dict(r) for r in self.conn.execute(
			f"SELECT m.id, m.from_participant, m.to_participant, m.kind, m.subject, m.thread_id, "
			f"m.created_ts, c.claim_id, c.participant AS claimed_by, c.claimed_ts "
			f"FROM messages m JOIN claims c ON c.message_id=m.id AND c.state='active' "
			f"{where.replace('to_participant', 'm.to_participant')} {'AND' if where else 'WHERE'} m.state='claimed' "
			f"ORDER BY c.claimed_ts", args)]
		# The machine-readable view of what `claim` skips. Damaged entries stay
		# in `pending` as well, because they ARE pending — this is an extra
		# lens on the same rows, not a separate queue. `doctor` remains the
		# whole-instance view and also covers already-terminal messages whose
		# retained attachment later went stale.
		damaged = []
		for entry in pending:
			try:
				self.verify_attachment(entry["id"])
			except BatonError as exc:
				if exc.exit_code != EXIT_DAMAGE:
					raise
				damaged.append({**entry, "failure": str(exc),
				                "parts": [
					{"part": p["address"], "content_type": p["content_type"],
					 "root_id": p["attach"]["root_id"], "path": p["attach"]["path"],
					 "sha256": p["sha256"], "size": p["size"],
					 "generation": p["attach"]["generation"]}
					for p in self._external_leaves(self._read_parts("message", entry["id"]))]})
		return {"pending": pending, "claimed": claimed, "damaged": damaged}


# ---------------------------------------------------------------------------
# init / open
# ---------------------------------------------------------------------------

def _connect_fd(dbfd: int, readonly: bool) -> sqlite3.Connection:
	mode = "ro" if readonly else "rw"
	conn = sqlite3.connect(f"file:/proc/self/fd/{dbfd}?mode={mode}", uri=True,
	                       isolation_level=None, timeout=BUSY_TIMEOUT_MS / 1000.0)
	conn.row_factory = sqlite3.Row
	return conn


def _verify_db_identity(conn: sqlite3.Connection, dbfd: int, dirfd: int) -> None:
	rows = conn.execute("PRAGMA database_list").fetchall()
	main = [r for r in rows if r[1] == "main"]
	if len(main) != 1 or not main[0][2]:
		raise BatonError("cannot resolve the opened database path", EXIT_DAMAGE)
	canonical = main[0][2]
	try:
		st_path = os.stat(canonical)
	except OSError as exc:
		raise BatonError(f"opened database path vanished: {exc}", EXIT_DAMAGE) from exc
	st_fd = os.fstat(dbfd)
	if (st_path.st_dev, st_path.st_ino) != (st_fd.st_dev, st_fd.st_ino):
		raise BatonError("database identity mismatch (dev/inode)", EXIT_DAMAGE)
	st_parent = os.stat(os.path.dirname(canonical))
	st_dir = os.fstat(dirfd)
	if (st_parent.st_dev, st_parent.st_ino) != (st_dir.st_dev, st_dir.st_ino):
		raise BatonError("database parent directory mismatch", EXIT_DAMAGE)


def _apply_connection_contract(conn: sqlite3.Connection, readonly: bool) -> None:
	if sqlite3.sqlite_version_info < SQLITE_MIN:
		raise BatonError(
			f"SQLite library {sqlite3.sqlite_version} is below the required "
			f"{'.'.join(map(str, SQLITE_MIN))} (STRICT tables)", EXIT_FLOOR)
	mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
	if mode != "wal":
		raise BatonError(f"database journal_mode is {mode!r}, not WAL; refusing", EXIT_DAMAGE)
	conn.execute("PRAGMA trusted_schema=OFF")
	conn.execute("PRAGMA foreign_keys=ON")
	conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
	if not readonly:
		conn.execute("PRAGMA synchronous=FULL")


def _validate_schema(conn: sqlite3.Connection) -> None:
	"""Exact schema identity."""
	user_version = conn.execute("PRAGMA user_version").fetchone()[0]
	if user_version != PROTOCOL_VERSION:
		raise BatonError(
			f"database protocol {user_version} does not match supported protocol {PROTOCOL_VERSION}", EXIT_PROTOCOL)
	actual: dict[tuple[str, str], str] = {}
	for typ, name, sql in conn.execute(
			"SELECT type, name, sql FROM sqlite_master "
			"WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"):
		actual[(typ, name)] = sql
	expected = _expected_schema()
	if actual != expected:
		missing = sorted(set(expected) - set(actual))
		extra = sorted(set(actual) - set(expected))
		changed = sorted(k for k in set(actual) & set(expected) if actual[k] != expected[k])
		raise BatonError(
			f"schema validation failed (missing={missing!r} extra={extra!r} changed={changed!r})", EXIT_DAMAGE)
	fk = conn.execute("PRAGMA foreign_key_check").fetchall()
	if fk:
		raise BatonError(f"foreign_key_check reported {len(fk)} violation(s)", EXIT_DAMAGE)
	quick = [r[0] for r in conn.execute("PRAGMA quick_check")]
	if quick != ["ok"]:
		raise BatonError(f"quick_check failed: {quick!r}", EXIT_DAMAGE)


def _check_meta(conn: sqlite3.Connection, config: dict, config_digest: str, readonly: bool,
                for_regen: bool = False, for_ceremony: bool = False) -> None:
	row = conn.execute("SELECT * FROM instance_meta WHERE one_row=1").fetchone()
	if row is None:
		raise BatonError("instance_meta row is missing", EXIT_DAMAGE)
	if row["protocol"] != PROTOCOL_VERSION:
		raise BatonError(f"instance protocol {row['protocol']} unsupported", EXIT_PROTOCOL)
	if for_regen:
		if config["generation"] != row["accepted_generation"] + 1:
			raise BatonError(
				f"regen requires config generation {row['accepted_generation'] + 1} "
				f"(accepted {row['accepted_generation']}, offered {config['generation']})")
	elif row["accepted_generation"] != config["generation"] or row["config_sha256"] != config_digest:
		raise BatonError(
			"config digest/generation does not match the accepted instance state "
			f"(accepted generation {row['accepted_generation']}; run regen for config changes)", EXIT_PROTOCOL)
	if row["move_status"] == "moved" and not for_ceremony:
		raise BatonError(f"instance has moved to {row['moved_to']!r}; refusing", EXIT_GATED)
	if not readonly and not for_ceremony and row["maintenance"] == 1:
		raise BatonError("instance is under maintenance; write operations are gated", EXIT_GATED)


def init_instance(config_path: str) -> None:
	"""Crash-atomic initialization: build a uniquely named scratch DB, create
	the schema transactionally, checkpoint/validate/fsync it, then no-clobber
	publish (hardlink) to the final name and fsync the directory. A crash can
	leave recognizable `.init-*` scratch, never a partial final authority."""
	dirfd = open_instance_dir(config_path)
	scratch = None
	sfd = -1
	try:
		config, digest = _read_config_at(dirfd, os.path.basename(config_path))
		_validate_roots(config)
		scratch = f".init-{new_id()}.sqlite3"
		sfd = os.open(scratch, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
		              0o600, dir_fd=dirfd)
		conn = _connect_fd(sfd, readonly=False)
		try:
			if sqlite3.sqlite_version_info < SQLITE_MIN:
				raise BatonError(
					f"SQLite library {sqlite3.sqlite_version} is below the required "
					f"{'.'.join(map(str, SQLITE_MIN))}", EXIT_FLOOR)
			conn.execute("PRAGMA journal_mode=WAL")
			conn.execute("PRAGMA synchronous=FULL")
			conn.execute("PRAGMA trusted_schema=OFF")
			conn.execute("PRAGMA foreign_keys=ON")
			conn.execute("BEGIN IMMEDIATE")
			conn.execute(f"PRAGMA user_version={PROTOCOL_VERSION}")
			for sql in _TABLES.values():
				conn.execute(sql)
			for sql in _INDEXES.values():
				conn.execute(sql)
			# Seed rows BEFORE the guard triggers exist: bootstrap inserts are
			# part of instance creation, not protocol operations.
			conn.execute("INSERT INTO op_context(one_row) VALUES(1)")
			conn.execute(
				"INSERT INTO instance_meta(one_row, uuid, protocol, accepted_generation, "
				"config_sha256, created_ts) VALUES(1, ?, ?, ?, ?, ?)",
				(new_id(), PROTOCOL_VERSION, config["generation"], digest, _utc_now_iso()))
			for root_id, path in config.get("roots", {}).items():
				conn.execute(
					"INSERT INTO accepted_roots(root_id, path, binding_generation) VALUES(?, ?, ?)",
					(root_id, path, config["generation"]))
			for sql in _TRIGGERS.values():
				conn.execute(sql)
			conn.execute("COMMIT")
			_fault("init:post-commit")
			busy, log, ckpt = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
			if busy != 0 or log != ckpt:
				raise BatonError(
					f"init checkpoint incomplete (busy={busy}, log={log}, checkpointed={ckpt})", EXIT_DAMAGE)
			_fault("init:post-checkpoint")
			_validate_schema(conn)
		finally:
			conn.close()
		os.fsync(sfd)
		_fault("init:pre-link")
		try:
			os.link(scratch, DB_NAME, src_dir_fd=dirfd, dst_dir_fd=dirfd)
		except FileExistsError:
			raise BatonError(f"refusing to initialize over existing {DB_NAME}") from None
		_fault("init:post-link")
		os.unlink(scratch, dir_fd=dirfd)
		scratch = None
		_fault("init:post-unlink")
		os.fsync(dirfd)
	except BaseException:
		if scratch is not None:
			try:
				os.unlink(scratch, dir_fd=dirfd)
			except OSError:
				pass
		raise
	finally:
		if sfd >= 0:
			os.close(sfd)
		os.close(dirfd)


def open_instance(config_path: str, *, readonly: bool = False, _for_regen: bool = False,
                  _for_ceremony: bool = False) -> Store:
	dirfd = open_instance_dir(config_path)
	dbfd = -1
	conn = None
	try:
		config, digest = _read_config_at(dirfd, os.path.basename(config_path))
		flags = (os.O_RDONLY if readonly else os.O_RDWR) | os.O_NOFOLLOW | os.O_CLOEXEC
		try:
			dbfd = os.open(DB_NAME, flags, dir_fd=dirfd)
		except FileNotFoundError:
			raise BatonError(f"no {DB_NAME} beside the config (run init)", EXIT_PROTOCOL) from None
		except OSError as exc:
			if exc.errno == errno.ELOOP:
				raise BatonError(f"{DB_NAME} is a symlink; refusing", EXIT_DAMAGE) from exc
			raise
		_validate_roots(config)
		conn = _connect_fd(dbfd, readonly)
		try:
			_verify_db_identity(conn, dbfd, dirfd)
			_apply_connection_contract(conn, readonly)
			_validate_schema(conn)
			_check_meta(conn, config, digest, readonly, for_regen=_for_regen,
			            for_ceremony=_for_ceremony)
		except sqlite3.DatabaseError as exc:
			raise BatonError(f"database failed open validation: {exc}", EXIT_DAMAGE) from exc
		return Store(config_path, config, digest, dirfd, dbfd, conn, readonly)
	except BaseException:
		if conn is not None:
			conn.close()
		if dbfd >= 0:
			os.close(dbfd)
		os.close(dirfd)
		raise


def regen_instance(config_path: str, *, participant: str) -> dict:
	"""Accept a new config in ONE transaction. Requirements enforced inside
	the transaction: capability authority; offered generation exactly
	accepted+1; NO participant named by a live (pending/claimed) message or
	live notice may be removed; NO root referenced by any retained attachment
	may be removed or remapped (referenced mappings are preserved immutably —
	the accepted_roots table is the publication-time authority). Additive
	changes are always safe."""
	with open_instance(config_path, _for_regen=True) as store:
		store._require_capability(participant, "config", "regen")
		store._txn_begin("regen", participant=participant, ceremony="regen")
		try:
			new_participants = set(store.config["participants"])
			live = store.conn.execute(
				"SELECT DISTINCT from_participant AS p FROM messages WHERE state IN ('pending','claimed') "
				"UNION SELECT DISTINCT to_participant FROM messages WHERE state IN ('pending','claimed') "
				"UNION SELECT DISTINCT from_participant FROM notices "
				# THE FROZEN AUDIENCE TOO. Protecting only notice AUTHORS left
				# a removal able to strand an addressee: the audience is
				# immutable, so the participant stays in it forever while
				# becoming undeclared and unable to consume what it names.
				#
				# Only where the notice is still deliverable to them -- a
				# receipt already recorded means delivery happened, and a
				# notice everyone has seen holds nobody hostage. Expiry and gc
				# remove the audience with the notice, so a removal that is
				# refused today becomes possible later without ever rewriting
				# retained history.
				"UNION SELECT DISTINCT a.participant FROM notice_audience a "
				"WHERE NOT EXISTS (SELECT 1 FROM notice_seen s "
				"WHERE s.notice_id=a.notice_id AND s.participant=a.participant)"
				).fetchall()
			missing = sorted({r["p"] for r in live} - new_participants)
			if missing:
				raise BatonError(
					f"regen refused: participant(s) {missing!r} are named by live messages/notices "
					"and absent from the offered config")
			new_roots = store.config.get("roots", {})
			for row in store.conn.execute(
					"SELECT DISTINCT p.root_id AS root_id, a.path FROM parts p "
					"JOIN accepted_roots a ON a.root_id = p.root_id "
					"WHERE p.storage='external'").fetchall():
				if new_roots.get(row["root_id"]) != row["path"]:
					raise BatonError(
						f"regen refused: root {row['root_id']!r} is referenced by retained "
						f"attachments and must keep its accepted mapping {row['path']!r}")
			previous = {row["root_id"]: (row["path"], row["binding_generation"])
			            for row in store.conn.execute(
			                "SELECT root_id, path, binding_generation FROM accepted_roots")}
			store.conn.execute("DELETE FROM accepted_roots")
			for root_id, path in new_roots.items():
				prior = previous.get(root_id)
				binding_gen = prior[1] if prior is not None and prior[0] == path else store.config["generation"]
				store.conn.execute(
					"INSERT INTO accepted_roots(root_id, path, binding_generation) VALUES(?, ?, ?)",
					(root_id, path, binding_gen))
			store.conn.execute(
				"UPDATE instance_meta SET accepted_generation=?, config_sha256=? WHERE one_row=1",
				(store.config["generation"], store.config_digest))
			store._txn_commit()
			return {"accepted_generation": store.config["generation"], "config_sha256": store.config_digest}
		except BaseException:
			store._txn_rollback()
			raise


# ---------------------------------------------------------------------------
# Maintenance / move / migrate ceremonies
# ---------------------------------------------------------------------------

CHECKPOINT_DRAIN_ATTEMPTS = 50
CHECKPOINT_DRAIN_SLEEP_S = 0.1


def _audit_ceremony(store: Store, kind: str, participant: str,
                    reason: str | None, token: str | None, peer: str | None = None) -> str:
	ceremony_id = new_id()
	store.conn.execute(
		"INSERT INTO ceremonies(ceremony_id, kind, participant, reason, token, peer, created_ts) "
		"VALUES(?,?,?,?,?,?,?)",
		(ceremony_id, kind, participant, reason, token, peer, _utc_now_iso()))
	return ceremony_id


def _committed_ceremony(store: Store, kind: str, token: str) -> sqlite3.Row | None:
	return store.conn.execute(
		"SELECT * FROM ceremonies WHERE kind=? AND token=?", (kind, token)).fetchone()


def _meta(store: Store) -> sqlite3.Row:
	return store.conn.execute("SELECT * FROM instance_meta WHERE one_row=1").fetchone()


def maintenance_enter(config_path: str, *, participant: str,
                      reason: str, move: bool = False, destination: str | None = None) -> dict:
	"""Set the maintenance gate. For a move, the ONE canonical destination
	directory is bound atomically with the token BEFORE any copy exists, and
	this instance becomes the move SOURCE; a copied database inherits that
	role and therefore can never activate itself."""
	if type(move) is not bool:
		raise BatonError("move must be a boolean")
	if type(reason) is not str or not reason.strip():
		raise BatonError("maintenance requires a non-empty --reason")
	if move:
		if type(destination) is not str or not os.path.isabs(destination) \
				or destination != os.path.normpath(destination) or destination.endswith("/"):
			raise BatonError(
				"a move requires an explicit canonical absolute DESTINATION CONFIG PATH")
		dest_dirfd = _open_dir_no_follow(os.path.dirname(destination), "move destination")
		try:
			ftype = _statfs_ftype(dest_dirfd)
			if ftype not in LOCAL_FS_MAGICS:
				raise BatonError(
					f"move destination filesystem (statfs f_type 0x{ftype:X}) is not a "
					"supported local filesystem", EXIT_DAMAGE)
			dest_identity = os.fstat(dest_dirfd)
			try:
				probe = os.open(os.path.basename(destination),
				                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
				                dir_fd=dest_dirfd)
				try:
					if not stat.S_ISREG(os.fstat(probe).st_mode):
						raise BatonError(
							"destination config path exists and is not a regular file; refusing")
				finally:
					os.close(probe)
			except FileNotFoundError:
				pass
			except OSError as exc:
				if exc.errno == errno.ELOOP:
					raise BatonError("destination config path is a symlink; refusing", EXIT_DAMAGE) from exc
				raise
		finally:
			os.close(dest_dirfd)
	elif destination is not None:
		raise BatonError("destination is only valid with move=True")
	with open_instance(config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "maintenance")
		verb = "move_enter" if move else "maintenance"
		store._txn_begin(verb, participant=participant,
		                 ceremony="move" if move else "maintenance")
		try:
			row = _meta(store)
			if row["maintenance"] == 1:
				raise BatonError("instance is already under maintenance")
			# The no-active-claims invariant belongs to the operation that
			# CLOSES the gate, checked in the same transaction. `reply` and
			# `close` are themselves gated, so a claim that survives into
			# maintenance has lost its normal route to resolution: the holder
			# cannot drain it, and the operator must exit the gate (undoing
			# any staged config) before anyone can. Refusing here leaves the
			# instance ungated, so the holder simply finishes their work.
			active = store.conn.execute(
				"SELECT claim_id, participant FROM claims WHERE state='active' "
				"ORDER BY claimed_ts, claim_id").fetchall()
			if active:
				raise BatonError(
					f"{len(active)} active claim(s) held (first {active[0]['claim_id']!r} held by "
					f"{active[0]['participant']!r}); resolve or recover them before gating — "
					f"reply and close are gated, so a claim cannot be drained once the gate "
					f"is set", EXIT_RACE)
			token = new_id() if move else None
			if move:
				source_route = config_path
				if source_route != os.path.normpath(source_route):
					raise BatonError("source config path must be canonical for a move binding")
				source_identity = os.fstat(store.dirfd)
				if os.path.basename(source_route) != os.path.basename(store.config_path):
					raise BatonError("move must be entered at the source's own config path")
				if (source_identity.st_dev, source_identity.st_ino) == \
						(dest_identity.st_dev, dest_identity.st_ino):
					raise BatonError(
						"move source and destination are the same directory; a move must "
						"change the instance's directory identity")
				store.conn.execute(
					"UPDATE instance_meta SET maintenance=1, maintainer_participant=?, maintainer_reason=?, "
					"move_status='moving', move_token=?, move_role='source', move_peer=?, "
					"move_source=? WHERE one_row=1",
					(participant, reason, token, destination, source_route))
				store.conn.execute(
					"INSERT INTO moves(token, instance_uuid, source_config, source_dev, source_ino, "
					"destination_config, destination_dev, destination_ino, created_ts) "
					"VALUES(?,?,?,?,?,?,?,?,?)",
					(token, row["uuid"], source_route, source_identity.st_dev, source_identity.st_ino,
					 destination, dest_identity.st_dev, dest_identity.st_ino, _utc_now_iso()))
			else:
				store.conn.execute(
					"UPDATE instance_meta SET maintenance=1, maintainer_participant=?, maintainer_reason=? "
					"WHERE one_row=1", (participant, reason))
			_audit_ceremony(store, "maintenance_enter", participant, reason, token,
			                peer=destination)
			store._txn_commit()
			_fault("enter:committed")
			return {"maintenance": True, "move_token": token, "destination": destination}
		except BaseException:
			store._txn_rollback()
			raise


def maintenance_exit(config_path: str, *, participant: str,
                     reason: str) -> dict:
	"""Clear a plain maintenance gate. Any instance that is part of a move
	(source OR copied destination) DEFAULT-REFUSES this generic clear —
	completing or aborting the move are the only exits, so a same-UUID copy
	can never be forked back to active by a routine stale-flag clear."""
	if type(reason) is not str or not reason.strip():
		raise BatonError("maintenance exit requires a non-empty --reason")
	with open_instance(config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "maintenance")
		store._txn_begin("maintenance", participant=participant, ceremony="maintenance")
		try:
			row = _meta(store)
			if row["maintenance"] == 0:
				raise BatonError("instance is not under maintenance")
			if row["move_status"] != "none":
				raise BatonError(
					"instance is part of a move; the generic maintenance clear is refused — "
					"complete the move (bind/activate/decommission) or, on the SOURCE only, "
					"use abort-move with the exact token and a destination-destroyed "
					"attestation", EXIT_GATED)
			store.conn.execute(
				"UPDATE instance_meta SET maintenance=0, maintainer_participant=NULL, "
				"maintainer_reason=NULL WHERE one_row=1")
			_audit_ceremony(store, "maintenance_exit", participant, reason, None)
			store._txn_commit()
			return {"maintenance": False}
		except BaseException:
			store._txn_rollback()
			raise


def checkpoint_drain(store: Store) -> tuple[int, int]:
	"""Run wal_checkpoint(TRUNCATE) with NO open transaction until it reports
	busy==0 AND log==checkpointed, with bounded backoff. Returns the final
	(log, checkpointed) tuple; raises on timeout with the flag left set."""
	import time
	for _ in range(CHECKPOINT_DRAIN_ATTEMPTS):
		busy, log, ckpt = store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
		if busy == 0 and log == ckpt:
			return (log, ckpt)
		time.sleep(CHECKPOINT_DRAIN_SLEEP_S)
	raise BatonError(
		"checkpoint drain did not converge (readers/writers still active); the maintenance "
		"flag remains set — retry after the instance quiesces", EXIT_RACE)


def _write_all(dfd: int, data: bytes) -> None:
	view = memoryview(data)
	while view:
		written = os.write(dfd, view)
		if written == 0:
			raise BatonError("zero-byte write while publishing; refusing", EXIT_DAMAGE)
		view = view[written:]


COPY_CHUNK = 1 << 20


def _sha256_fd_pread(fd: int) -> str:
	hasher = hashlib.sha256()
	offset = 0
	while True:
		chunk = os.pread(fd, COPY_CHUNK, offset)
		if not chunk:
			return hasher.hexdigest()
		hasher.update(chunk)
		offset += len(chunk)


def _hash_existing_regular(dst_dirfd: int, name: str) -> str | None:
	"""Stream-hash an existing destination artifact; absent returns None. The
	artifact must be a regular file (nonblocking/no-follow open) so a FIFO or
	device can neither hang the resume nor impersonate a copied file."""
	try:
		fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
		             dir_fd=dst_dirfd)
	except FileNotFoundError:
		return None
	except OSError as exc:
		if exc.errno == errno.ELOOP:
			raise BatonError(f"destination {name!r} is a symlink; refusing", EXIT_DAMAGE) from exc
		raise
	try:
		if not stat.S_ISREG(os.fstat(fd).st_mode):
			raise BatonError(f"destination {name!r} is not a regular file; refusing", EXIT_DAMAGE)
		return _sha256_fd_pread(fd)
	finally:
		os.close(fd)


def _stream_publish_from_fd(src_fd: int, expected_size: int, dst_dirfd: int, dst_name: str,
                            mode: int) -> str:
	"""Stream the held source fd into a scratch destination in bounded chunks
	while hashing, fsync, then no-clobber publish. An EXISTING regular
	artifact is accepted only when its streamed hash equals the source's
	streamed hash (resume); mismatch fails closed. Bounded memory by
	construction; premature EOF and zero-byte writes fail closed. Returns the
	source hash."""
	source_sha = _sha256_fd_pread(src_fd)
	existing_sha = _hash_existing_regular(dst_dirfd, dst_name)
	if existing_sha is not None:
		if existing_sha != source_sha:
			raise BatonError(
				f"destination already contains a MISMATCHING {dst_name!r}; refusing", EXIT_DAMAGE)
		return source_sha
	scratch = f".copy-{new_id()}"
	dfd = os.open(scratch, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
	              mode, dir_fd=dst_dirfd)
	try:
		verify = hashlib.sha256()
		offset = 0
		while offset < expected_size:
			chunk = os.pread(src_fd, min(COPY_CHUNK, expected_size - offset), offset)
			if not chunk:
				raise BatonError(
					f"premature EOF streaming {dst_name!r} at offset {offset}; refusing", EXIT_DAMAGE)
			verify.update(chunk)
			view = memoryview(chunk)
			while view:
				written = os.write(dfd, view)
				if written == 0:
					raise BatonError(
						f"zero-byte write streaming {dst_name!r}; refusing", EXIT_DAMAGE)
				view = view[written:]
			offset += len(chunk)
		if verify.hexdigest() != source_sha:
			raise BatonError(
				f"source changed while streaming {dst_name!r}; refusing the ambiguous copy",
				EXIT_DAMAGE)
		os.fsync(dfd)
	except BaseException:
		os.close(dfd)
		try:
			os.unlink(scratch, dir_fd=dst_dirfd)
		except OSError:
			pass
		raise
	os.close(dfd)
	try:
		os.link(scratch, dst_name, src_dir_fd=dst_dirfd, dst_dir_fd=dst_dirfd)
	except FileExistsError:
		os.unlink(scratch, dir_fd=dst_dirfd)
		raise BatonError(f"destination race on {dst_name!r}; rerun to verify/resume", EXIT_RACE) from None
	os.unlink(scratch, dir_fd=dst_dirfd)
	os.fsync(dst_dirfd)
	return source_sha


def _publish_bytes_at(dst_dirfd: int, dst_name: str, data: bytes, mode: int,
                      expect_sha: str) -> None:
	"""Publish exact bytes at dst_name (scratch → fsync → no-clobber hardlink
	→ dirfsync). An EXISTING artifact is accepted only if its bytes hash to
	expect_sha (resume); a mismatch fails closed."""
	try:
		existing = os.open(dst_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
		                   dir_fd=dst_dirfd)
	except FileNotFoundError:
		existing = -1
	except OSError as exc:
		if exc.errno == errno.ELOOP:
			raise BatonError(f"destination {dst_name!r} is a symlink; refusing", EXIT_DAMAGE) from exc
		raise BatonError(f"destination {dst_name!r} unreadable: {exc}", EXIT_DAMAGE) from exc
	if existing >= 0:
		try:
			if not stat.S_ISREG(os.fstat(existing).st_mode):
				raise BatonError(f"destination {dst_name!r} is not a regular file; refusing", EXIT_DAMAGE)
			if _sha256_fd_pread(existing) != expect_sha:
				raise BatonError(
					f"destination already contains a MISMATCHING {dst_name!r}; refusing", EXIT_DAMAGE)
			return  # exact artifact already published — resume
		finally:
			os.close(existing)
	scratch = f".copy-{new_id()}"
	dfd = os.open(scratch, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
	              mode, dir_fd=dst_dirfd)
	try:
		_write_all(dfd, data)
		os.fsync(dfd)
	finally:
		os.close(dfd)
	try:
		os.link(scratch, dst_name, src_dir_fd=dst_dirfd, dst_dir_fd=dst_dirfd)
	except FileExistsError:
		os.unlink(scratch, dir_fd=dst_dirfd)
		raise BatonError(f"destination race on {dst_name!r}; rerun to verify/resume", EXIT_RACE) from None
	os.unlink(scratch, dir_fd=dst_dirfd)
	os.fsync(dst_dirfd)


def move_copy(config_path: str, *, participant: str) -> dict:
	"""Copy the drained, move-gated SOURCE to its BOUND destination config
	path (set at maintenance_enter — never a call-site argument). The DB
	bytes are read from the HELD, identity-verified descriptor after drain;
	the config bytes are re-read through the held instance dirfd and must
	still hash to the accepted canonical digest. Publication is per-file
	resumable BEFORE destination binding (byte/digest equality required);
	after the bind/activate ceremonies the destination legitimately differs,
	so a retry discovers the committed stage from the destination's immutable
	ceremony/token/UUID history and reports it instead of demanding byte
	equality. Unexplained artifacts fail closed."""
	with open_instance(config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "move copy")
		row = _meta(store)
		if row["move_status"] != "moving" or row["move_role"] != "source":
			raise BatonError("move copy requires the move-gated SOURCE (maintenance_enter(move=True))")
		token = row["move_token"]
		source_uuid = row["uuid"]
		binding = store._move_binding(token)
		store._validate_route_identity(binding["source_config"], binding["source_dev"],
		                               binding["source_ino"], "move_copy SOURCE route")
		dest_config = binding["destination_config"]
		if row["move_peer"] != dest_config or row["move_source"] != binding["source_config"]:
			raise BatonError(
				"live move fields disagree with the immutable binding; refusing (corruption)",
				EXIT_DAMAGE)
		dest_dir = os.path.dirname(dest_config)
		dest_name = os.path.basename(dest_config)
		# Stage discovery: a valid destination pair means a committed stage.
		try:
			with open_instance(dest_config, readonly=True, _for_ceremony=True) as peer:
				pm = peer.conn.execute(
					"SELECT uuid, move_status, move_token, move_role FROM instance_meta "
					"WHERE one_row=1").fetchone()
				if pm["uuid"] != source_uuid:
					raise BatonError(
						"destination holds a DIFFERENT instance uuid; refusing", EXIT_DAMAGE)
				# NO stage may be reported for a peer that is not physically at
				# the bound destination identity.
				peer._validate_route_identity(binding["destination_config"],
				                              binding["destination_dev"],
				                              binding["destination_ino"],
				                              "stage discovery DESTINATION route")
				if pm["move_token"] == token and pm["move_role"] == "source":
					return {"move_token": token, "destination": dest_config, "stage": "copied",
					        "already_committed": True}
				if pm["move_token"] == token and pm["move_role"] == "destination":
					return {"move_token": token, "destination": dest_config, "stage": "bound",
					        "already_committed": True}
				activated = _committed_ceremony(peer, "move_activate", token)
				if activated is not None:
					if activated["peer"] != dest_config:
						raise BatonError(
							"activation history names a different route than the bound "
							"destination; refusing", EXIT_DAMAGE)
					return {"move_token": token, "destination": dest_config, "stage": "activated",
					        "already_committed": True}
				raise BatonError(
					"destination pair exists but its move history does not explain this token; "
					"refusing", EXIT_DAMAGE)
		except BatonError as exc:
			# Recovery classification is NARROW: only the two expected absence
			# shapes mean "publish/resume below"; anything else from an
			# existing pair keeps its own reason.
			message = str(exc)
			if not ("run init" in message or "config not found" in message):
				raise
		dest_dirfd = _open_dir_no_follow(dest_dir, "move destination")
		try:
			ftype = _statfs_ftype(dest_dirfd)
			if ftype not in LOCAL_FS_MAGICS:
				raise BatonError(
					f"move destination filesystem (statfs f_type 0x{ftype:X}) is not a "
					"supported local filesystem", EXIT_DAMAGE)
			dest_now = os.fstat(dest_dirfd)
			if (dest_now.st_dev, dest_now.st_ino) != (binding["destination_dev"], binding["destination_ino"]):
				raise BatonError(
					"destination directory identity does not match the identity bound at "
					"maintenance_enter; refusing to publish", EXIT_DAMAGE)
			_fault("move:pre-drain")
			log, ckpt = checkpoint_drain(store)
			_fault("move:post-drain")
			config_name = os.path.basename(store.config_path)
			cfd = os.open(config_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
			              dir_fd=store.dirfd)
			try:
				if not stat.S_ISREG(os.fstat(cfd).st_mode):
					raise BatonError(
						f"source config {config_name!r} is no longer a regular file; refusing",
						EXIT_DAMAGE)
				config_bytes = b""
				while True:
					chunk = os.read(cfd, 1 << 20)
					if not chunk:
						break
					config_bytes += chunk
			finally:
				os.close(cfd)
			try:
				config_text = config_bytes.decode("utf-8")
			except UnicodeDecodeError as exc:
				raise BatonError(f"source config is not valid UTF-8: {exc}", EXIT_DAMAGE) from exc
			reparsed = validate_config(loads_strict(config_text))
			if canonical_sha256(reparsed) != store.config_digest:
				raise BatonError(
					"config bytes no longer match the accepted canonical digest; refusing to copy",
					EXIT_DAMAGE)
			config_sha = hashlib.sha256(config_bytes).hexdigest()
			_publish_bytes_at(dest_dirfd, dest_name, config_bytes, 0o644, config_sha)
			_fault("move:config-copied")
			db_size = os.fstat(store.dbfd).st_size
			_stream_publish_from_fd(store.dbfd, db_size, dest_dirfd, DB_NAME, 0o600)
			_fault("move:db-copied")
		finally:
			os.close(dest_dirfd)
	# Full validation of the gated destination pair before reporting success —
	# including the bound directory identity: a substitution between
	# publication and this open must fail, not report 'copied'.
	with open_instance(dest_config, readonly=True, _for_ceremony=True) as check:
		check._validate_route_identity(binding["destination_config"],
		                               binding["destination_dev"], binding["destination_ino"],
		                               "post-publication DESTINATION route")
		peer_meta = check.conn.execute(
			"SELECT uuid, move_token, move_role, move_peer, move_source FROM instance_meta "
			"WHERE one_row=1").fetchone()
		if peer_meta["uuid"] != source_uuid or peer_meta["move_token"] != token:
			raise BatonError("copied destination failed identity validation; refusing", EXIT_DAMAGE)
		if (peer_meta["move_role"] != "source"
				or peer_meta["move_peer"] != binding["destination_config"]
				or peer_meta["move_source"] != binding["source_config"]):
			raise BatonError(
				"copied destination's live move mirrors disagree with the binding; refusing",
				EXIT_DAMAGE)
	return {"move_token": token, "destination": dest_config, "stage": "copied",
	        "already_committed": False, "checkpoint": (log, ckpt)}


def move_bind_destination(dest_config_path: str, *, participant: str,
                          token: str) -> dict:
	"""After both files are durably present and the copy validates, flip ONLY
	the copy to role='destination' (audited, exact token). The ceremony
	verifies the copy physically resides at the destination directory bound
	by the source — a copy placed anywhere else refuses — and records its
	peer. Idempotent by committed ceremony."""
	with open_instance(dest_config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "move destination binding")
		store._txn_begin("move", participant=participant, ceremony="move")
		try:
			row = _meta(store)
			committed = _committed_ceremony(store, "move_bind_destination", token)
			if committed is not None and row["move_role"] == "destination":
				binding = store._move_binding(token)
				store._validate_route_identity(binding["destination_config"],
				                               binding["destination_dev"], binding["destination_ino"],
				                               "bind retry DESTINATION route")
				store._txn_rollback()
				return {"already_committed": True, "bound": True}
			if row["move_status"] != "moving" or row["move_role"] != "source":
				raise BatonError(
					f"destination binding requires a moving source-role copy "
					f"(status {row['move_status']!r}, role {row['move_role']!r})")
			if row["move_token"] != token:
				raise BatonError("move token does not match; refusing destination binding")
			binding = store._move_binding(token)
			store._validate_route_identity(binding["destination_config"],
			                               binding["destination_dev"], binding["destination_ino"],
			                               "bind DESTINATION route")
			bound_config = binding["destination_config"]
			store.conn.execute(
				"UPDATE instance_meta SET move_role='destination' WHERE one_row=1")
			_audit_ceremony(store, "move_bind_destination", participant, None, token,
			                peer=bound_config)
			store._txn_commit()
			_fault("bind:committed")
			return {"already_committed": False, "bound": True}
		except BaseException:
			store._txn_rollback()
			raise


def move_activate(dest_config_path: str, *, participant: str,
                  token: str) -> dict:
	"""Activate the BOUND destination: requires moving + role='destination'
	+ exact token. Retries discover the committed ceremony and return
	already_committed after validating the token."""
	with open_instance(dest_config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "move activation")
		store._txn_begin("move", participant=participant, ceremony="move")
		try:
			row = _meta(store)
			committed = _committed_ceremony(store, "move_activate", token)
			if committed is not None and row["move_status"] == "none":
				binding = store._move_binding(token)
				store._validate_route_identity(binding["destination_config"],
				                               binding["destination_dev"], binding["destination_ino"],
				                               "activation retry DESTINATION route")
				store._txn_rollback()
				return {"already_committed": True, "activated": True}
			if row["move_status"] != "moving":
				raise BatonError(f"destination is not part of a move (status {row['move_status']!r})")
			if row["move_role"] != "destination":
				raise BatonError(
					"activation requires the BOUND destination role; a source (or unbound copy) "
					"can never activate", EXIT_GATED)
			if row["move_token"] != token:
				raise BatonError("move token does not match; refusing activation")
			# A post-bind clone carries the destination role in its BYTES;
			# only the bound directory identity may activate.
			binding = store._move_binding(token)
			store._validate_route_identity(binding["destination_config"],
			                               binding["destination_dev"], binding["destination_ino"],
			                               "activation DESTINATION route")
			bound_route = binding["destination_config"]
			store.conn.execute(
				"UPDATE instance_meta SET maintenance=0, maintainer_participant=NULL, maintainer_reason=NULL, "
				"move_status='none', move_token=NULL, move_role=NULL, move_peer=NULL, "
				"move_source=NULL WHERE one_row=1")
			_audit_ceremony(store, "move_activate", participant, None, token,
			                peer=bound_route)
			store._txn_commit()
			_fault("activate:committed")
			return {"already_committed": False, "activated": True}
		except BaseException:
			store._txn_rollback()
			raise


def move_decommission(source_config_path: str, *, participant: str,
                      token: str, moved_to: str) -> dict:
	"""Mark the SOURCE 'moved' forever: requires moving + role='source' +
	exact token, and moved_to must equal the bound destination. Retries
	discover the committed ceremony and return already_committed."""
	if type(moved_to) is not str or not os.path.isabs(moved_to) or moved_to != os.path.normpath(moved_to):
		raise BatonError("moved_to must be a canonical absolute path")
	with open_instance(source_config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "move decommission")
		store._txn_begin("move", participant=participant, ceremony="move")
		try:
			row = _meta(store)
			committed = _committed_ceremony(store, "move_decommission", token)
			if committed is not None and row["move_status"] == "moved":
				if committed["peer"] != moved_to:
					raise BatonError(
						f"retried moved_to {moved_to!r} differs from the committed route "
						f"{committed['peer']!r}; refusing", EXIT_PROTOCOL)
				binding = store._move_binding(token)
				store._validate_route_identity(binding["source_config"], binding["source_dev"],
				                               binding["source_ino"], "decommission retry SOURCE route")
				store._txn_rollback()
				return {"already_committed": True, "moved_to": row["moved_to"]}
			if row["move_status"] != "moving":
				raise BatonError(f"source is not part of a move (status {row['move_status']!r})")
			if row["move_role"] != "source":
				raise BatonError("decommission requires the SOURCE role", EXIT_DAMAGE)
			if row["move_token"] != token:
				raise BatonError("move token does not match; refusing decommission")
			binding = store._move_binding(token)
			store._validate_route_identity(binding["source_config"], binding["source_dev"],
			                               binding["source_ino"], "decommission SOURCE route")
			if binding["destination_config"] != moved_to:
				raise BatonError(
					f"moved_to {moved_to!r} does not match the bound destination "
					f"{binding['destination_config']!r}; refusing")
			# PLAN sequence: destination activation precedes source
			# decommission — the bound destination must exist, carry the same
			# immutable UUID, hold the committed activation for this token and
			# route, and be active (ungated) at the exact destination route.
			try:
				with open_instance(moved_to, readonly=True) as dest:
					dest._validate_route_identity(binding["destination_config"],
					                              binding["destination_dev"],
					                              binding["destination_ino"],
					                              "decommission DESTINATION route")
					dest_meta = dest.conn.execute(
						"SELECT uuid, maintenance, move_status FROM instance_meta "
						"WHERE one_row=1").fetchone()
					if dest_meta["uuid"] != row["uuid"]:
						raise BatonError(
							"bound destination carries a different instance uuid; refusing "
							"decommission", EXIT_DAMAGE)
					if dest_meta["maintenance"] != 0 or dest_meta["move_status"] != "none":
						raise BatonError(
							"bound destination is not active; activate it before source "
							"decommission")
					activated = _committed_ceremony(dest, "move_activate", token)
					if activated is None or activated["peer"] != moved_to:
						raise BatonError(
							"bound destination has no committed activation for this token and "
							"route; activate it before source decommission")
			except BatonError as exc:
				if "run init" in str(exc) or "config not found" in str(exc):
					raise BatonError(
						"bound destination does not exist yet; copy/bind/activate before "
						"source decommission") from exc
				raise
			store.conn.execute(
				"UPDATE instance_meta SET move_status='moved', moved_to=? WHERE one_row=1",
				(moved_to,))
			_audit_ceremony(store, "move_decommission", participant, None, token,
			                peer=moved_to)
			store._txn_commit()
			_fault("decommission:committed")
			return {"already_committed": False, "moved_to": moved_to}
		except BaseException:
			store._txn_rollback()
			raise


def abort_move(config_path: str, *, participant: str, token: str,
               destination_destroyed: bool, reason: str) -> dict:
	"""Abort an in-flight move — SOURCE ONLY. Requires the exact token plus
	an explicit attestation that the destination copy is destroyed (or was
	never created). A destination copy REFUSES abort outright: destroying it
	is the only disposal; it can never interpret the attestation as
	permission to ungate itself."""
	if type(destination_destroyed) is not bool:
		raise BatonError("destination_destroyed must be a boolean")
	if not destination_destroyed:
		raise BatonError(
			"abort-move requires the destination-destroyed attestation; without it the same "
			"mailbox UUID could fork into two active authorities")
	if type(reason) is not str or not reason.strip():
		raise BatonError("abort-move requires a non-empty --reason")
	with open_instance(config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "abort-move")
		store._txn_begin("move", participant=participant, ceremony="move")
		try:
			row = _meta(store)
			if row["move_status"] != "moving":
				raise BatonError(f"instance is not part of a move (status {row['move_status']!r})")
			if row["move_role"] != "source":
				raise BatonError(
					"abort-move requires the SOURCE role; any copy must be destroyed, never "
					"ungated", EXIT_GATED)
			if row["move_token"] != token:
				raise BatonError("move token does not match; refusing abort")
			binding = store._move_binding(token)
			store._validate_route_identity(binding["source_config"], binding["source_dev"],
			                               binding["source_ino"], "abort SOURCE route")
			store.conn.execute(
				"UPDATE instance_meta SET maintenance=0, maintainer_participant=NULL, maintainer_reason=NULL, "
				"move_status='none', move_token=NULL, move_role=NULL, move_peer=NULL, "
				"move_source=NULL WHERE one_row=1")
			_audit_ceremony(store, "abort_move", participant, reason, token)
			store._txn_commit()
			return {"aborted": True}
		except BaseException:
			store._txn_rollback()
			raise


def _read_config_bytes_at(dirfd: int, config_name: str) -> bytes:
	"""Read the config through the HELD instance dirfd, no-follow, refusing a
	non-regular file — the same discipline the move ceremony uses."""
	cfd = os.open(config_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=dirfd)
	try:
		if not stat.S_ISREG(os.fstat(cfd).st_mode):
			raise BatonError(f"config {config_name!r} is not a regular file; refusing",
			                 EXIT_DAMAGE)
		data = b""
		while True:
			chunk = os.read(cfd, 1 << 20)
			if not chunk:
				break
			data += chunk
		return data
	finally:
		os.close(cfd)


def quarantine_attachment_instance(config_path: str, message_id: str, *, participant: str,
                                   reason: str) -> dict:
	"""Ceremony entry point for the quarantine disposition. Opens as a
	ceremony so it can run while the instance is under a PLAIN maintenance
	gate — repairing instance health belongs in the same quiet window as any
	other administrative work, before participants are let back in. Move-gated
	instances are still refused, inside the transaction where the check cannot
	be raced."""
	with open_instance(config_path, _for_ceremony=True) as store:
		return store.quarantine_attachment(message_id, participant=participant,
		                                   reason=reason)


def migrate_instance(config_path: str, *, participant: str) -> dict:
	"""Schema migration gate. Protocol 8 is the only schema this tool knows.
	The authorized ATTEMPT is durably audited before the unsupported result is
	reported, so the gate's audit claim is true today. A migration path is
	added only alongside a protocol bump, together with the frozen definition
	of the protocol it migrates from."""
	with open_instance(config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "migrate")
		row = store.conn.execute(
			"SELECT maintenance FROM instance_meta WHERE one_row=1").fetchone()
		if row["maintenance"] != 1:
			raise BatonError("migrate requires the maintenance gate to be set first")
		store._txn_begin("migrate", participant=participant, ceremony="migrate")
		try:
			_audit_ceremony(store, "migrate", participant,
			                f"attempted migration; no path from protocol {PROTOCOL_VERSION}", None)
			store._txn_commit()
		except BaseException:
			store._txn_rollback()
			raise
		raise BatonError(
			f"no migration path exists from protocol {PROTOCOL_VERSION}; this tool only "
			"gains one alongside a protocol bump", EXIT_PROTOCOL)


def snapshot_instance(config_path: str, dest_dir: str, *, participant: str) -> dict:
	"""Take a validated, restorable copy of a QUIESCED instance.

	Rationale: a bare `cp` of a WAL-mode database is not a backup contract —
	the committed state may live partly in `-wal`, so the copy can be torn or
	stale. This drains the WAL with the same `checkpoint_drain` the move
	ceremony uses (TRUNCATE until it reports converged, which also proves no
	other reader/writer is active), then publishes the database and config
	through the same hash-verified, fsynced, no-clobber streaming copy that
	publishes a move. Finally it OPENS the copy and validates it, so the
	snapshot is known-good before it is ever needed.

	Requires the maintenance gate: a snapshot of a live instance would be a
	snapshot of a moving target."""
	with open_instance(config_path, _for_ceremony=True) as store:
		store._require_capability(participant, "config", "snapshot")
		row = _meta(store)
		if row["maintenance"] != 1:
			raise BatonError(
				"snapshot requires the maintenance gate to be set first (a snapshot of a "
				"live instance is a snapshot of a moving target)")
		if row["move_status"] != "none":
			raise BatonError(
				f"instance move is {row['move_status']!r}; snapshot is refused during a move",
				EXIT_GATED)
		return _take_snapshot(store, config_path, dest_dir, row)


def _take_snapshot(store: Store, config_path: str, dest_dir: str,
                   meta_row: sqlite3.Row) -> dict:
	"""Validated copy of a quiesced instance: drain the WAL, publish the
	database and config through the hash-verified fsynced no-clobber path,
	then open the copy and check it."""
	active = store.conn.execute(
		"SELECT COUNT(*) FROM claims WHERE state='active'").fetchone()[0]
	checkpoint_drain(store)  # fold the WAL in; proves the instance is quiet
	dest = os.path.abspath(dest_dir)
	# Creating the directory is not enough: the publication helpers fsync the
	# copied files and `dest` itself, which persists the entries INSIDE dest,
	# but not dest's own entry in its parent. A crash after the migration
	# commits could then lose the rollback directory's NAME even though every
	# byte inside it was synced. Persist the parent link too.
	created = not os.path.isdir(dest)
	os.makedirs(dest, exist_ok=True)
	if created:
		parent_fd = _open_dir_no_follow(os.path.dirname(dest) or "/", "snapshot parent directory")
		try:
			os.fsync(parent_fd)
		finally:
			os.close(parent_fd)
	config_bytes = _read_config_bytes_at(store.dirfd, os.path.basename(config_path))
	config_sha = hashlib.sha256(config_bytes).hexdigest()
	dst_dirfd = _open_dir_no_follow(dest, "snapshot directory")
	try:
		_publish_bytes_at(dst_dirfd, "baton.json", config_bytes, 0o600, config_sha)
		db_sha = _stream_publish_from_fd(
			store.dbfd, os.fstat(store.dbfd).st_size, dst_dirfd, DB_NAME, 0o600)
	finally:
		os.close(dst_dirfd)
	# Prove the snapshot is a usable instance NOW, not when it is needed.
	with open_instance(os.path.join(dest, "baton.json"), readonly=True,
	                   _for_ceremony=True) as copy:
		meta = copy.conn.execute(
			"SELECT uuid, protocol, accepted_generation FROM instance_meta "
			"WHERE one_row=1").fetchone()
		messages = copy.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
		if meta["uuid"] != meta_row["uuid"]:
			raise BatonError("snapshot holds a different instance uuid; refusing", EXIT_DAMAGE)
	return {"snapshot_dir": dest, "database_sha256": db_sha, "config_sha256": config_sha,
	        "protocol": meta["protocol"], "accepted_generation": meta["accepted_generation"],
	        "messages": messages, "active_claims": active}


def move_status_inspect(config_path: str) -> dict:
	"""Read-only inspection of the move/maintenance state — the discovery
	path for a lost maintenance_enter(move=True) response: the committed
	token, role, and bound route are all durably readable."""
	with open_instance(config_path, readonly=True, _for_ceremony=True) as store:
		row = _meta(store)
		binding = None
		if row["move_token"] is not None:
			b = store.conn.execute(
				"SELECT * FROM moves WHERE token=?", (row["move_token"],)).fetchone()
			if b is not None:
				binding = dict(b)
		return {
			"maintenance": bool(row["maintenance"]),
			"maintainer_participant": row["maintainer_participant"],
			"maintainer_reason": row["maintainer_reason"],
			"move_status": row["move_status"],
			"move_token": row["move_token"],
			"move_role": row["move_role"],
			"move_peer": row["move_peer"],
			"move_source": row["move_source"],
			"moved_to": row["moved_to"],
			"binding": binding,
		}


# ---------------------------------------------------------------------------
# wait / eventing (notification is never authority)
# ---------------------------------------------------------------------------

WAIT_RESCAN_INTERVAL_S = 60.0

_IN_CREATE = 0x00000100
_IN_DELETE = 0x00000200
_IN_MODIFY = 0x00000002
_IN_MOVED_TO = 0x00000080
_IN_MOVE_SELF = 0x00000800
_IN_DELETE_SELF = 0x00000400
_IN_Q_OVERFLOW = 0x00004000
_IN_IGNORED = 0x00008000
_IN_UNMOUNT = 0x00002000
_IN_NONBLOCK = 0x00000800
_IN_CLOEXEC = 0x00080000


_WATCH_MASK = (_IN_CREATE | _IN_DELETE | _IN_MODIFY | _IN_MOVED_TO
               | _IN_MOVE_SELF | _IN_DELETE_SELF | _IN_UNMOUNT)


def _decode_inotify(data: bytes) -> dict:
	"""Decode a raw inotify buffer into the waiter's decision flags:
	`revalidate` (overflow / watch invalidation / directory replaced or
	unmounted → full re-open validation before rearm) and `relevant`
	(a mailbox.sqlite3* name changed)."""
	revalidate = False
	relevant = False
	offset = 0
	while offset + 16 <= len(data):
		_wd, mask, _cookie, name_len = _struct_unpack_from(data, offset)
		name = data[offset + 16: offset + 16 + name_len].split(b"\x00", 1)[0].decode(
			"utf-8", "replace")
		offset += 16 + name_len
		if mask & (_IN_Q_OVERFLOW | _IN_IGNORED | _IN_MOVE_SELF
		           | _IN_DELETE_SELF | _IN_UNMOUNT):
			revalidate = True
		if name.startswith(DB_NAME):
			relevant = True
	return {"revalidate": revalidate, "relevant": relevant}


class _InotifyWatch:
	"""Best-effort inotify watch on the instance DIRECTORY (never a single
	WAL inode — checkpoints create/delete/reset it). Every event is only a
	prompt to requery; failure to arm degrades to pure polling."""

	def __init__(self, instance_dir: str) -> None:
		import ctypes
		self._libc = ctypes.CDLL(None, use_errno=True)
		self.fd = self._libc.inotify_init1(_IN_NONBLOCK | _IN_CLOEXEC)
		if self.fd < 0:
			raise OSError("inotify_init1 failed")
		wd = self._libc.inotify_add_watch(self.fd, instance_dir.encode(), _WATCH_MASK)
		if wd < 0:
			os.close(self.fd)
			raise OSError("inotify_add_watch failed")

	def close(self) -> None:
		try:
			os.close(self.fd)
		except OSError:
			pass

	def poll(self, timeout_s: float) -> dict:
		"""Block up to timeout_s; drain events. Returns flags describing what
		must happen next: {'revalidate': bool} — dir replaced/unmounted/
		overflowed watches require full re-open validation before rearming."""
		import select
		readable, _, _ = select.select([self.fd], [], [], max(timeout_s, 0.0))
		if not readable:
			return {"revalidate": False, "relevant": False}
		try:
			data = os.read(self.fd, 65536)
		except BlockingIOError:
			data = b""
		# The waiter requeries after EVERY poll return (events are hints,
		# never authority), so the decoder's verdict is returned untouched —
		# `relevant` is informational; only `revalidate` alters control flow.
		return _decode_inotify(data)


def _struct_unpack_from(data: bytes, offset: int) -> tuple:
	import struct
	return struct.unpack_from("iIII", data, offset)


def wait_for_readiness(config_path: str, participant: str, *,
                       timeout_s: float | None = None,
                       rescan_interval_s: float = WAIT_RESCAN_INTERVAL_S) -> dict:
	"""Block until work EXISTS, and take none of it.

	Same arming, requery and gate behaviour as `wait_for_message` -- literally
	the same loop -- with a read-only probe in place of the consuming one.
	Sharing the loop is the point: the query-to-arm race close and the safety
	rescan are subtle, and a second copy of them would slowly diverge.

	Safe to leave in a background terminal that may never wake its agent. That
	is the whole reason it exists: a consuming waiter in that position creates
	an active claim with no model turn available to answer it, and the work
	sits held. A missed wake here delays work instead of holding it.

	Several consumers may wake for the same message. `claim` remains the
	transaction that decides who owns it, exactly as before.
	"""
	def probe(store):
		state = store.readiness(participant)
		return state if state["ready"] else None
	return _blocking_wait(config_path, participant, probe=probe, timeout_s=timeout_s,
	                      rescan_interval_s=rescan_interval_s)


def wait_for_message(config_path: str, participant: str, *,
                     timeout_s: float | None = None,
                     rescan_interval_s: float = WAIT_RESCAN_INTERVAL_S) -> dict:
	"""Query → arm directory watch → REQUERY → block; every event is only a
	prompt to requery the transactional store. The 60s safety rescan always
	applies; without inotify this degrades to pure interval polling. A gated
	(maintenance/moved) instance makes the waiter stand down with the gate's
	own diagnostic rather than spinning.

	The requery covers BOTH inbound channels — a claimable directed message,
	or failing that an unseen live broadcast notice. A notice commit wakes the
	directory watch like any other write, so requerying only `messages` would
	wake the waiter and then send it back to sleep with the notice
	undelivered."""
	import math
	import time
	if timeout_s is not None and (type(timeout_s) not in (int, float)
			or not math.isfinite(timeout_s) or timeout_s < 0):
		raise BatonError("timeout must be a finite nonnegative number")
	if (type(rescan_interval_s) not in (int, float)
			or not math.isfinite(rescan_interval_s) or rescan_interval_s <= 0):
		raise BatonError("rescan interval must be a finite positive number")
	def probe(store):
		"""Directed messages win: claimable work must never be delayed behind
		advisory broadcast, which also keeps the directed path's timing and
		delivery shape unchanged for consumers that never receive notices."""
		try:
			claim = store.claim(participant)
		except BatonError as exc:
			if exc.exit_code != EXIT_NONE:
				raise
		else:
			# Deterministic seam BETWEEN claim commit and content fetch: an
			# instance transition here must not strand the claim -- the
			# delivery below reads through this SAME open, validated Store,
			# never a second open.
			_fault("wait:claimed")
			return _delivery(store, claim)
		if not store.has_unseen_notice(participant):
			return None  # idle poll stays read-only; no write lock taken
		notices = store.see(participant, limit=1)
		return _notice_delivery(notices[0]) if notices else None
	return _blocking_wait(config_path, participant, probe=probe, timeout_s=timeout_s,
	                      rescan_interval_s=rescan_interval_s)


def _blocking_wait(config_path: str, participant: str, *, probe,
                   timeout_s: float | None, rescan_interval_s: float) -> dict:
	"""The arm/requery/block loop, with WHAT to look for left to the caller.

	`probe` receives one open, validated Store and returns a result or None.
	It runs inside that single open so a gate stands the whole waiter down and
	the post-arm requery closes the query-to-arm race identically for every
	probe."""
	import math
	import time
	if timeout_s is not None and (type(timeout_s) not in (int, float)
			or not math.isfinite(timeout_s) or timeout_s < 0):
		raise BatonError("timeout must be a finite nonnegative number")
	if (type(rescan_interval_s) not in (int, float)
			or not math.isfinite(rescan_interval_s) or rescan_interval_s <= 0):
		raise BatonError("rescan interval must be a finite positive number")
	deadline = (time.monotonic() + timeout_s) if timeout_s is not None else None

	def try_deliver() -> dict | None:
		"""One requery of both channels through ONE open, validated Store, so
		a gate stands the whole waiter down and the post-arm requery closes
		the query→arm race for notices exactly as it does for messages.
		Directed messages win: claimable work must never be delayed behind
		advisory broadcast, which also keeps the directed path's timing and
		delivery shape unchanged for consumers that never receive notices."""
		try:
			with open_instance(config_path) as store:
				return probe(store)
		except BatonError as exc:
			if exc.exit_code == EXIT_NONE:
				return None
			raise  # gates (EXIT_GATED) and real errors stand the waiter down

	delivery = try_deliver()
	if delivery is not None:
		return delivery
	instance_dir = os.path.dirname(config_path)
	while True:
		watch = None
		try:
			try:
				watch = _InotifyWatch(instance_dir)
			except OSError:
				watch = None  # degraded: pure polling
			_fault("wait:armed")
			delivery = try_deliver()  # requery closes the query→arm race
			if delivery is not None:
				return delivery
			remaining = None if deadline is None else deadline - time.monotonic()
			if remaining is not None and remaining <= 0:
				raise BatonError(
					f"no message or notice for {participant!r} arrived within the timeout",
					EXIT_NONE)
			slice_s = rescan_interval_s if remaining is None else min(rescan_interval_s, remaining)
			if watch is not None:
				flags = watch.poll(slice_s)
				if flags["revalidate"]:
					watch.close()
					watch = None  # full re-open validation happens in try_deliver
			else:
				time.sleep(slice_s)  # degraded polling honors the configured interval
			delivery = try_deliver()
			if delivery is not None:
				return delivery
		finally:
			if watch is not None:
				watch.close()


def _part_repr(node: dict, *, bytes_required: bool) -> dict:
	"""One part of a delivered content envelope.

	A container carries its nested `parts` and no bytes. A leaf carries
	`size`, `sha256`, and EXACTLY ONE delivery representation, named by
	`encoding`: `text` for `text/...; charset=utf-8`, `base64` for everything
	else. Never both -- the same bytes were previously emitted twice, as `utf8`
	AND `base64`, and the `utf8` field came and went depending on whether the
	content happened to decode, which left a consumer nothing stable to
	dispatch on.

	`encoding` is null, with neither content key present, when a transient body
	has been scrubbed: the manifest outlives the payload, so a consumed
	transient part still states what it was and what it hashed to.

	`bytes_required` is TRUE on every delivery path: a message is delivered
	only while pending or claimed, and a notice is never scrubbed, so absent
	bytes always mean something removed them. The manifest cannot notice --
	it deliberately excludes byte presence so that it survives scrubbing.
	Manifest-only leaves are legitimate only in STORAGE, after a lawful scrub,
	and `doctor` is what validates that against owner semantics."""
	out = {
		# Manifest address, so a delivered envelope is SELF-ADDRESSING: a
		# consumer reading it can name the part it wants to materialize
		# without recomputing positions from the tree. `materialize --part`
		# takes exactly this string.
		"address": node.get("address"),
		"content_type": node["content_type"],
		"disposition": node["disposition"],
		"part_name": node["part_name"],
	}
	if node["parts"] is None:
		out["attachment"] = None
	if node["parts"] is not None:
		out["parts"] = [_part_repr(child, bytes_required=bytes_required)
		                for child in node["parts"]]
		return out
	out["size"] = node["size"]
	out["sha256"] = node["sha256"]
	out["storage"] = node["storage"]
	if node["storage"] == STORAGE_EXTERNAL:
		# Externally stored bytes are POINTED AT, never inlined: the pin was
		# verified before delivery, and copying the file into the envelope
		# would defeat the point of storing it outside.
		ref = node["attach"]
		out["attachment"] = {"root_id": ref["root_id"], "path": ref["path"],
		                     "generation": ref["generation"]}
		out["encoding"] = None
		return out
	body = node["body"]
	if body is None:
		if bytes_required:
			raise BatonError(
				"part has no stored bytes but its owner is not a terminal transient; "
				"content was removed outside the retention path", EXIT_DAMAGE)
		out["encoding"] = None
		return out
	# Metadata is RECOMPUTED from the bytes: a stored-metadata disagreement is
	# damage, and damage is never delivered.
	actual_sha = hashlib.sha256(body).hexdigest()
	if node["sha256"] is not None and actual_sha != node["sha256"]:
		raise BatonError(
			"part bytes do not match their recorded sha256; refusing to deliver "
			"contradictory metadata", EXIT_DAMAGE)
	if node["size"] is not None and len(body) != node["size"]:
		raise BatonError(
			"part bytes do not match their recorded size; refusing to deliver", EXIT_DAMAGE)
	encoding = _delivery_encoding(node["content_type"])
	out["encoding"] = encoding
	if encoding == ENCODING_TEXT:
		try:
			out[ENCODING_TEXT] = body.decode("utf-8")
		except UnicodeDecodeError as exc:
			raise BatonError(
				f"part declares charset=utf-8 but its stored bytes do not decode ({exc}); "
				f"refusing to deliver", EXIT_DAMAGE) from exc
	else:
		import base64
		out[ENCODING_BASE64] = base64.b64encode(body).decode("ascii")
	return out


def _content_repr(container_type: str | None, nodes: list[dict] | None,
                  expected_manifest: str | None, *,
                  bytes_required: bool = True) -> dict | None:
	"""The typed content envelope: a container type plus an ORDERED part list,
	always -- a single-part message is not a different shape.

	The manifest digest is recomputed from what is actually stored and checked
	against what the owner row recorded, so a part that was added, dropped,
	reordered or retyped behind the API is damage rather than a quiet
	redefinition of the message."""
	if not container_type:
		return None
	nodes = nodes or []
	actual = manifest_digest(container_type, nodes)
	if expected_manifest is not None and actual != expected_manifest:
		raise BatonError(
			"stored parts do not match the recorded content manifest; refusing to deliver "
			"contradictory metadata", EXIT_DAMAGE)
	return {
		"content_type": container_type,
		"manifest_sha256": actual,
		"parts": [_part_repr(node, bytes_required=bytes_required) for node in nodes],
	}


def _delivery(store: Store, claim: dict) -> dict:
	"""The ONE lossless delivery shape shared by claim and wait: claim
	metadata plus the immutable message envelope with its typed content
	envelope, whose leaves may be inline or externally pinned."""
	msg = store.get_message(claim["message_id"])
	envelope = {k: msg[k] for k in (
		"id", "from_participant", "to_participant", "kind", "subject", "thread_id",
		"retention", "outcome", "created_ts", "state", "responds_to")}
	# Bytes are ALWAYS required on the delivery path. A message is delivered
	# only while pending or claimed, and scrubbing happens at reply/close --
	# so a leaf without bytes here was emptied by something else, whatever the
	# retention says. Deciding this from retention alone would have let a
	# damaged transient deliver as a lawful scrub.
	# There is no message-level attachment any more: an external part is a
	# leaf in `content.parts`, carrying its own type, disposition, order and
	# pin. One model, one place to look.
	envelope["content"] = _content_repr(
		msg["content_type"], msg.get("parts"), msg["manifest_sha256"])
	# WHO ELSE GOT THIS. Required by the finding: a recipient must be able to
	# tell a private message from work deliberately assigned to several
	# participants, and `to_participant` alone says only "me" either way.
	#
	# The EXPANDED LIST, not a selector -- unlike a notice, `--to` never
	# accepts a wildcard, so there is no selector to show and the addresses are
	# what the sender actually wrote.
	#
	# This discloses the audience; it does NOT make replies a group
	# conversation. A reply still goes to the original sender and no other
	# recipient's disposition is visible here.
	audience, duplicate = store.publication_of(msg.get("publication_id"))
	envelope["audience"] = audience
	envelope["possible_duplicate"] = duplicate
	return {"claim": claim, "message": envelope}


def _notice_delivery(notice: dict) -> dict:
	"""The broadcast delivery shape `wait` returns for a notice, distinguished
	from a directed delivery by key: `{'notice': ...}` versus
	`{'claim': ..., 'message': ...}`. The directed shape gains and loses
	nothing, so a consumer that only ever receives directed traffic sees no
	change at all.

	There is no claim here, and none is constructible: a `claims` row
	references `messages(id)`, and a notice is one row read by every
	participant with no per-recipient message to own. The `notice_seen`
	receipt written with the read is the whole disposition — nothing to reply
	to, nothing to close."""
	envelope = {k: notice[k] for k in (
		"id", "from_participant", "kind", "subject", "created_ts", "ttl_seconds", "seen_ts")}
	# WHO IT WAS ADDRESSED TO. A recipient reading a broadcast cannot otherwise
	# tell "everyone" from "my team", and those are different things to act on:
	# an announcement to twenty people and one to two read the same without it.
	envelope["audience_kind"] = notice.get("audience_kind")
	envelope["selector"] = notice.get("selector")
	envelope["possible_duplicate"] = bool(notice.get("possible_duplicate"))
	# A notice is never scrubbed -- it is deleted whole by expire or gc -- so a
	# notice part without bytes is always damage.
	envelope["content"] = _content_repr(
		notice["content_type"], notice.get("parts"), notice["manifest_sha256"])
	return {"notice": envelope}


# ---------------------------------------------------------------------------
# Observability: doctor / dump / materialize
# ---------------------------------------------------------------------------

_KNOWN_INSTANCE_FILES = ("baton.json", DB_NAME, DB_NAME + "-wal", DB_NAME + "-shm")


def doctor(config_path: str) -> dict:
	"""Read-only diagnosis. `problems` are integrity/logical violations and
	drive ok/exit status; `warnings` are recoverable residue (stale scratch,
	unrecognized files) that never fail the instance."""
	report: dict = {"ok": True, "problems": [], "warnings": []}
	with open_instance(config_path, readonly=True, _for_ceremony=True) as store:
		integrity = [r[0] for r in store.conn.execute("PRAGMA integrity_check")]
		if integrity != ["ok"]:
			report["problems"].append(f"integrity_check: {integrity!r}")
		fk = store.conn.execute("PRAGMA foreign_key_check").fetchall()
		if fk:
			report["problems"].append(f"foreign_key_check: {len(fk)} violation(s)")
		meta = store.conn.execute("SELECT * FROM instance_meta WHERE one_row=1").fetchone()
		report["instance"] = {
			"uuid": meta["uuid"], "protocol": meta["protocol"],
			"accepted_generation": meta["accepted_generation"],
			"maintenance": bool(meta["maintenance"]), "move_status": meta["move_status"],
		}
		report["messages_by_state"] = {
			r[0]: r[1] for r in store.conn.execute(
				"SELECT state, COUNT(*) FROM messages GROUP BY state")}
		report["active_claims"] = [dict(r) for r in store.conn.execute(
			"SELECT claim_id, message_id, participant, claimed_ts FROM claims WHERE state='active'")]
		report["notices"] = store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
		# THE FROZEN AUDIENCE. Every one of these is an invariant the schema
		# cannot express on its own, and each has a distinct failure: a notice
		# nobody can read, a receipt from outside the audience, an address or
		# selector that no longer parses, and an audience row whose notice is
		# gone.
		# DIRECTED PUBLICATIONS. Same shape of question as the notice audience,
		# and the same reason: the audience is the record of who work was
		# assigned to, and it must not be derivable from whichever deliveries
		# happen to survive.
		for row in store.conn.execute(
				"SELECT publication_id FROM publications p WHERE NOT EXISTS "
				"(SELECT 1 FROM publication_audience a "
				"WHERE a.publication_id=p.publication_id)"):
			report["problems"].append(
				f"publication {row['publication_id']} has an empty audience")
		# THE ORPHAN LINK. `messages.publication_id` is nullable, and for as
		# long as `reply` inserted its response directly it produced a
		# directed message with no publication record -- delivered as
		# `audience: []`, which reads as "nobody" where the truth is
		# "unrecorded". Both creation paths now publish, so a new orphan means
		# a THIRD path appeared; the existing ones are pre-fix rows that a
		# backfill has not reached yet.
		#
		# A PROBLEM rather than a warning: the audience is what later
		# participant-authorized reread will check, and an unrecorded one
		# cannot be checked. The message is still claimable and closable, so
		# nothing is stuck -- but nothing will notice this on its own either,
		# which is how it survived to reach a live instance.
		orphans = [row["id"] for row in store.conn.execute(
			"SELECT id FROM messages WHERE publication_id IS NULL ORDER BY created_ts, id")]
		if orphans:
			shown = ", ".join(orphans[:5]) + (" ..." if len(orphans) > 5 else "")
			report["problems"].append(
				f"{len(orphans)} directed message(s) have no publication record "
				f"and deliver an empty audience: {shown}")
		for row in store.conn.execute(
				"SELECT m.id, m.to_participant, m.publication_id FROM messages m "
				"WHERE m.publication_id IS NOT NULL AND NOT EXISTS "
				"(SELECT 1 FROM publication_audience a "
				"WHERE a.publication_id=m.publication_id "
				"AND a.participant=m.to_participant)"):
			report["problems"].append(
				f"message {row['id']} is delivered to {row['to_participant']}, "
				f"who is not in publication {row['publication_id']}'s audience")
		for row in store.conn.execute(
				"SELECT m.id, m.publication_id FROM messages m "
				"JOIN publications p ON p.publication_id = m.publication_id "
				"WHERE m.from_participant <> p.from_participant "
				"OR m.kind <> p.kind OR m.retention <> p.retention "
				"OR m.manifest_sha256 <> p.manifest_sha256 "
				"OR m.content_type <> p.content_type "
				"OR m.subject IS NOT p.subject OR m.thread_id IS NOT p.thread_id "
				"OR m.outcome IS NOT p.outcome"):
			report["problems"].append(
				f"message {row['id']} disagrees with publication "
				f"{row['publication_id']} about its envelope")
		orphaned = store.conn.execute(
			"SELECT COUNT(*) FROM publication_audience a WHERE NOT EXISTS "
			"(SELECT 1 FROM publications p "
			"WHERE p.publication_id=a.publication_id)").fetchone()[0]
		if orphaned:
			report["problems"].append(
				f"{orphaned} publication audience row(s) outlived their publication")
		for row in store.conn.execute(
				"SELECT id FROM notices n WHERE NOT EXISTS "
				"(SELECT 1 FROM notice_audience a WHERE a.notice_id=n.id)"):
			report["problems"].append(
				f"notice {row['id']} has an empty frozen audience and can reach nobody")
		for row in store.conn.execute(
				"SELECT s.notice_id, s.participant FROM notice_seen s WHERE NOT EXISTS "
				"(SELECT 1 FROM notice_audience a "
				"WHERE a.notice_id=s.notice_id AND a.participant=s.participant)"):
			report["problems"].append(
				f"notice {row['notice_id']} has a seen receipt from "
				f"{row['participant']}, who is not in its audience")
		# THE PROTOCOL'S OWN CHECKS, not a bare regex. Both grammars carry a
		# 64-character bound that lives beside the pattern rather than in it,
		# so calling `.match` alone accepts an overlong address or selector
		# that publication would have refused -- a doctor that is laxer than
		# the writer cannot detect what the writer prevents.
		for row in store.conn.execute(
				"SELECT DISTINCT participant FROM notice_audience"):
			if not _is_address(row["participant"]):
				report["problems"].append(
					f"notice audience holds {row['participant']!r}, "
					f"which is not a participant address")
		for row in store.conn.execute(
				"SELECT id, selector FROM notices WHERE selector IS NOT NULL"):
			try:
				validate_scope(row["selector"])
			except BatonError:
				report["problems"].append(
					f"notice {row['id']} records selector {row['selector']!r}, "
					f"which is not a scope")
		orphans = store.conn.execute(
			"SELECT COUNT(*) FROM notice_audience a WHERE NOT EXISTS "
			"(SELECT 1 FROM notices n WHERE n.id=a.notice_id)").fetchone()[0]
		if orphans:
			report["problems"].append(
				f"{orphans} notice audience row(s) outlived their notice")
		ctx = store.conn.execute("SELECT op_id FROM op_context WHERE one_row=1").fetchone()
		if ctx["op_id"] is not None:
			report["problems"].append("op_context is non-NULL outside any transaction")
		# Full audit-chain validation per entity: exactly one birth,
		# contiguous from->to order by seq, legal edges, tail equal to the
		# live row; ledger groups WITHOUT a live row must close in 'gc'
		# (GC'd subjects keep their permanent history).
		_MSG_EDGES = {(None, "pending"), ("pending", "claimed"), ("claimed", "completed"),
		              ("claimed", "closed"), ("claimed", "pending"),
		              ("pending", "quarantined"),
		              ("completed", "gc"), ("closed", "gc")}
		_CLAIM_EDGES = {(None, "active"), ("active", "completed"), ("active", "recovered"),
		                ("completed", "gc"), ("recovered", "gc"), ("active", "gc")}
		_KNOWN_VERBS = {"send", "claim", "reply", "close", "see", "expire", "recover",
		                "regen", "gc", "maintenance", "move", "move_enter", "migrate",
		                "quarantine"}
		# The finite edge -> producing-verb table: an edge outside its verb
		# set is an unexplained audit record even with valid syntax.
		_EDGE_VERBS = {
			("message", None, "pending"): {"send", "reply"},
			("message", "pending", "claimed"): {"claim"},
			("message", "claimed", "completed"): {"reply"},
			("message", "claimed", "closed"): {"close"},
			("message", "claimed", "pending"): {"recover"},
			("message", "pending", "quarantined"): {"quarantine"},
			("message", "completed", "gc"): {"gc"},
			("message", "closed", "gc"): {"gc"},
			("claim", None, "active"): {"claim"},
			("claim", "active", "completed"): {"reply", "close"},
			("claim", "active", "recovered"): {"recover"},
			("claim", "completed", "gc"): {"gc"},
			("claim", "recovered", "gc"): {"gc"},
			("claim", "active", "gc"): {"gc"},
		}
		live_state = {}
		for r in store.conn.execute("SELECT id, state FROM messages"):
			live_state[("message", r["id"])] = r["state"]
		for r in store.conn.execute("SELECT claim_id, state FROM claims"):
			live_state[("claim", r["claim_id"])] = r["state"]
		chains: dict = {}
		op_groups: dict = {}
		for r in store.conn.execute(
				"SELECT seq, entity, entity_id, from_state, to_state, op_id, participant, "
				"verb, at_ts FROM transitions ORDER BY seq"):
			chains.setdefault((r["entity"], r["entity_id"]), []).append(
				(r["from_state"], r["to_state"]))
			if r["verb"] not in _KNOWN_VERBS:
				report["problems"].append(
					f"transition {r['seq']} has unknown verb {r['verb']!r}")
			if not HEX32_RE.match(r["op_id"] or ""):
				report["problems"].append(f"transition {r['seq']} has malformed op_id")
			if r["participant"] is not None and (not ADDRESS_RE.match(r["participant"])
					or len(r["participant"]) > 64):
				report["problems"].append(f"transition {r['seq']} has malformed participant")
			try:
				_parse_ts(r["at_ts"])
			except (ValueError, TypeError):
				report["problems"].append(f"transition {r['seq']} has malformed timestamp")
			allowed_verbs = _EDGE_VERBS.get((r["entity"], r["from_state"], r["to_state"]))
			if allowed_verbs is not None and r["verb"] not in allowed_verbs:
				report["problems"].append(
					f"transition {r['seq']}: edge {r['from_state']!r}->{r['to_state']!r} "
					f"cannot be produced by verb {r['verb']!r}")
			op_groups.setdefault(r["op_id"], set()).add(
				(r["participant"], r["verb"], r["at_ts"]))
		for key, chain in chains.items():
			entity, entity_id = key
			edges = _MSG_EDGES if entity == "message" else _CLAIM_EDGES
			births = sum(1 for f, _t in chain if f is None)
			if births != 1 or chain[0][0] is not None:
				report["problems"].append(
					f"{entity} {entity_id}: {births} birth event(s) or birth not first")
				continue
			broken = False
			for i in range(1, len(chain)):
				if chain[i][0] != chain[i - 1][1]:
					report["problems"].append(
						f"{entity} {entity_id}: transition chain breaks at step {i}")
					broken = True
					break
			if broken:
				continue
			for edge in chain:
				if edge not in edges:
					report["problems"].append(f"{entity} {entity_id}: illegal edge {edge!r}")
					broken = True
					break
			if broken:
				continue
			tail = chain[-1][1]
			live = live_state.get(key)
			if live is None:
				if tail != "gc":
					report["problems"].append(
						f"{entity} {entity_id}: ledger has no live row and does not close in gc")
			elif tail != live:
				report["problems"].append(
					f"{entity} {entity_id}: ledger tail {tail!r} disagrees with live state {live!r}")
		for key in live_state:
			if key not in chains:
				report["problems"].append(f"{key[0]} {key[1]} has no ledger history at all")
		# Every row sharing an op_id was emitted by ONE transaction and must
		# carry one coherent attribution tuple.
		for op_id, tuples in op_groups.items():
			if len(tuples) > 1:
				report["problems"].append(
					f"op {op_id} has {len(tuples)} distinct attribution tuples "
					"(one transaction, one identity)")
		# Content bytes: recorded size/sha must describe the stored bytes,
		# and every content row must be owned by EXACTLY ONE part.
		for r in store.conn.execute("SELECT content_id, body, sha256, size FROM contents"):
			if len(r["body"]) != r["size"] or hashlib.sha256(r["body"]).hexdigest() != r["sha256"]:
				report["problems"].append(
					f"content {r['content_id']} bytes disagree with recorded size/sha256")
			owners = store.conn.execute(
				"SELECT COUNT(*) FROM parts WHERE content_id=?", (r["content_id"],)).fetchone()[0]
			if owners != 1:
				report["problems"].append(
					f"content {r['content_id']} has {owners} owning part(s) (exactly one required)")
		# Parts: a leaf's stored bytes must match the part's own hash and size,
		# and every owner's stored tree must still hash to the manifest digest
		# recorded on the owner row. A part added, dropped, reordered or
		# retyped behind the API changes what the message MEANS while leaving
		# every individual byte intact, so the manifest is the only check that
		# catches it.
		for r in store.conn.execute(
				"SELECT p.part_id, p.owner_kind, p.owner_id, p.sha256, p.size, c.body "
				"FROM parts p JOIN contents c ON c.content_id = p.content_id"):
			if len(r["body"]) != r["size"] or hashlib.sha256(r["body"]).hexdigest() != r["sha256"]:
				report["problems"].append(
					f"part {r['part_id']} bytes disagree with its recorded size/sha256")
		# Bytes may be absent from an INLINE leaf ONLY where the retention
		# contract removed them: a terminal transient message, or a transient
		# close disposition that never stored them. The manifest digest cannot
		# catch this -- it deliberately excludes byte presence so that it
		# survives scrubbing -- so a durable message whose content rows were
		# deleted would otherwise read as healthy and deliver like a scrubbed
		# one. External leaves are exempt by construction: their bytes live in
		# a configured root and are checked by pin verification instead.
		for r in store.conn.execute(
				"SELECT p.part_id, p.owner_kind, p.owner_id FROM parts p "
				"WHERE p.storage='inline' AND p.content_id IS NULL "
				"AND p.sha256 IS NOT NULL AND NOT ("
				"(p.owner_kind='message' AND EXISTS(SELECT 1 FROM messages m WHERE m.id=p.owner_id "
				"AND m.retention='transient' AND m.state IN ('completed','closed'))) "
				"OR (p.owner_kind='disposition' AND EXISTS(SELECT 1 FROM dispositions d "
				"WHERE d.claim_id=p.owner_id AND d.retention='transient')))"):
			report["problems"].append(
				f"part {r['part_id']} of {r['owner_kind']} {r['owner_id']} has no stored bytes "
				f"but its owner is not a terminal transient")
		owner_manifests = [
			("message", "SELECT id, content_type, manifest_sha256 FROM messages "
			            "WHERE manifest_sha256 IS NOT NULL"),
			("notice", "SELECT id, content_type, manifest_sha256 FROM notices"),
			("disposition", "SELECT claim_id AS id, content_type, manifest_sha256 FROM dispositions "
			                "WHERE manifest_sha256 IS NOT NULL AND response_message_id IS NULL"),
		]
		for owner_kind, query in owner_manifests:
			for r in store.conn.execute(query):
				try:
					nodes = store._read_parts(owner_kind, r["id"])
					if not nodes:
						# A CONTENTLESS PUBLICATION IS NOT DAMAGE, and the
						# manifest proves which one this is: the pinned
						# representation hashes to the digest of an empty
						# container, so a row that matches it stores no parts
						# BY CONSTRUCTION. Anything else with a manifest and
						# no parts had parts once, which is the case this
						# check exists for.
						if (r["content_type"] == CONTENTLESS_CONTAINER
								and r["manifest_sha256"] == manifest_digest(
									CONTENTLESS_CONTAINER, [])):
							continue
						report["problems"].append(
							f"{owner_kind} {r['id']} records a content manifest but stores no parts")
						continue
					if manifest_digest(r["content_type"], nodes) != r["manifest_sha256"]:
						report["problems"].append(
							f"{owner_kind} {r['id']} stored parts do not hash to its recorded "
							f"content manifest")
				except BatonError as exc:
					report["problems"].append(f"{owner_kind} {r['id']}: {exc}")
		# A REPLY disposition stores no parts of its own -- its content is the
		# response message -- so the manifest pass above skips it. That left it
		# unchecked entirely: a corrupted reply manifest read as healthy while
		# breaking effectively-once, refusing a correct retry. The insert-time
		# trigger asserts this equality; doctor must confirm it still holds.
		for r in store.conn.execute(
				"SELECT d.claim_id, d.content_type, d.manifest_sha256, d.retention, "
				"d.response_message_id, m.content_type AS msg_content_type, "
				"m.manifest_sha256 AS msg_manifest, m.retention AS msg_retention "
				"FROM dispositions d LEFT JOIN messages m ON m.id = d.response_message_id "
				"WHERE d.kind='reply'"):
			if r["response_message_id"] is None:
				report["problems"].append(
					f"reply disposition {r['claim_id']} references no response message")
			elif r["msg_manifest"] is None and r["msg_content_type"] is None:
				report["problems"].append(
					f"reply disposition {r['claim_id']} references missing response message "
					f"{r['response_message_id']}")
			elif (r["manifest_sha256"] != r["msg_manifest"]
			      or r["content_type"] != r["msg_content_type"]):
				report["problems"].append(
					f"reply disposition {r['claim_id']} content manifest disagrees with its "
					f"response message {r['response_message_id']}")
			elif r["retention"] != r["msg_retention"]:
				report["problems"].append(
					f"reply disposition {r['claim_id']} retention disagrees with its "
					f"response message {r['response_message_id']}")
		for r in store.conn.execute(
				"SELECT part_id, owner_kind, owner_id FROM parts "
				"WHERE storage='external' AND owner_kind <> 'message'"):
			report["problems"].append(
				f"part {r['part_id']} is externally stored on {r['owner_kind']} "
				f"{r['owner_id']}, which has no damage lifecycle to verify or resolve it")
		orphans = store.conn.execute(
			"SELECT COUNT(*) FROM parts p WHERE NOT EXISTS("
			"SELECT 1 FROM messages m WHERE p.owner_kind='message' AND m.id=p.owner_id) "
			"AND NOT EXISTS(SELECT 1 FROM notices n WHERE p.owner_kind='notice' AND n.id=p.owner_id) "
			"AND NOT EXISTS(SELECT 1 FROM dispositions d WHERE p.owner_kind='disposition' "
			"AND d.claim_id=p.owner_id)").fetchone()[0]
		if orphans:
			report["problems"].append(f"{orphans} part row(s) reference no surviving owner")
		# Retained attachments: verify pinned path/size/hash through the
		# existing no-follow authority — a mutated or unreadable attachment
		# is a problem, not a healthy report.
		# Damage that has been explicitly dispositioned through the quarantine
		# ceremony is a WARNING, not a problem: it is acknowledged, audited,
		# and no longer blocking anything. Only unresolved damage keeps the
		# instance unhealthy — otherwise there would be no way to reach a
		# healthy instance after a pin legitimately went stale.
		acknowledged = store.quarantined_message_ids()
		for r in store.conn.execute(
				"SELECT DISTINCT owner_id AS id FROM parts "
				"WHERE owner_kind='message' AND storage='external'"):
			try:
				store.verify_attachment(r["id"])
			except BatonError as exc:
				if r["id"] in acknowledged:
					report["warnings"].append(
						f"attachment of message {r['id']} is damaged but quarantined: {exc}")
				else:
					report["problems"].append(f"attachment of message {r['id']}: {exc}")
		report["quarantined"] = sorted(acknowledged)
		# Quarantine coherence: the state and its audit row must agree, in
		# both directions. A quarantined message with no row, or a row whose
		# recorded pin disagrees with the message's immutable columns, means
		# something produced the state outside the ceremony.
		for row in store.conn.execute(
				"SELECT id FROM messages WHERE state='quarantined'"):
			if row["id"] not in acknowledged:
				report["problems"].append(
					f"message {row['id']} is quarantined with no quarantine record")
		for q in store.conn.execute("SELECT * FROM quarantines"):
			msg = store.conn.execute(
				"SELECT state FROM messages WHERE id=?", (q["message_id"],)).fetchone()
			if msg is None:
				report["problems"].append(
					f"quarantine {q['quarantine_id']} references missing message {q['message_id']}")
				continue
			# The audit row records the pin of ONE part; that part must still
			# exist on the message and still carry the pin that was recorded.
			part = store.conn.execute(
				"SELECT owner_id, content_type, root_id, path, sha256, size, generation "
				"FROM parts WHERE part_id=?", (q["part_id"],)).fetchone()
			if part is None or part["owner_id"] != q["message_id"]:
				report["problems"].append(
					f"quarantine {q['quarantine_id']} references part {q['part_id']} that is "
					f"not a part of message {q['message_id']}")
			elif any(part[col] != q[col] for col in
			         ("content_type", "root_id", "path", "sha256", "size", "generation")):
				report["problems"].append(
					f"quarantine {q['quarantine_id']} records a different pin than part "
					f"{q['part_id']} still carries")
			if q["prior_state"] == "pending":
				if msg["state"] != "quarantined":
					report["problems"].append(
						f"quarantine {q['quarantine_id']} recorded prior_state 'pending' but "
						f"message {q['message_id']} is {msg['state']!r}, not quarantined")
				edge = store.conn.execute(
					"SELECT verb FROM transitions WHERE entity='message' AND entity_id=? "
					"AND from_state='pending' AND to_state='quarantined'",
					(q["message_id"],)).fetchall()
				if [e["verb"] for e in edge] != ["quarantine"]:
					report["problems"].append(
						f"message {q['message_id']} lacks exactly one 'quarantine' ledger edge "
						f"for its pending->quarantined transition")
			elif msg["state"] != q["prior_state"]:
				report["problems"].append(
					f"quarantine {q['quarantine_id']} acknowledged message {q['message_id']} in "
					f"state {q['prior_state']!r} but it is now {msg['state']!r}")
		# Attachment pins: pinned root must be the accepted binding at the
		# pinned generation and match the live config mapping.
		config_roots = store.config.get("roots", {})
		for row in store.conn.execute(
				"SELECT part_id, owner_kind, owner_id, root_id, generation FROM parts "
				"WHERE storage='external'"):
			accepted = store.conn.execute(
				"SELECT path, binding_generation FROM accepted_roots WHERE root_id=?",
				(row["root_id"],)).fetchone()
			if accepted is None:
				report["problems"].append(
					f"part {row['part_id']} pins root {row['root_id']!r} with no "
					"accepted binding")
			elif accepted["binding_generation"] != row["generation"]:
				report["problems"].append(
					f"part {row['part_id']} pins binding generation {row['generation']} "
					f"but the accepted binding is {accepted['binding_generation']}")
			elif config_roots.get(row["root_id"]) != accepted["path"]:
				report["problems"].append(
					f"root {row['root_id']!r} accepted path disagrees with the config")
		# accepted_roots / config coherence.
		accepted_map = {r["root_id"]: r["path"] for r in store.conn.execute(
			"SELECT root_id, path FROM accepted_roots")}
		if accepted_map != dict(config_roots):
			report["problems"].append("accepted_roots does not match the config roots mapping")
		# Instance-dir inventory via the HELD dirfd (never a re-resolved path).
		unrecognized = []
		scratch = []
		for name in sorted(os.listdir(store.dirfd)):
			if name in _KNOWN_INSTANCE_FILES or name == os.path.basename(config_path):
				continue
			if name.startswith(".init-") or name.startswith(".copy-"):
				scratch.append(name)
			else:
				unrecognized.append(name)
		report["stale_scratch"] = scratch
		report["unrecognized_files"] = unrecognized
		if scratch:
			report["warnings"].append(
				f"{len(scratch)} stale scratch file(s) (crash residue; removable)")
		if unrecognized:
			report["warnings"].append(
				f"{len(unrecognized)} unrecognized file(s) in the instance directory")
		# Projection inventory: reconcile configured projection directories
		# against durable messages — projections are caches, so orphans are
		# warnings, but the PLAN requires them inventoried, never ignored.
		projections = {"orphans": [], "checked": 0}
		durable_ids = {r[0] for r in store.conn.execute(
			"SELECT id FROM messages WHERE retention='durable'")}
		# Shared directories accumulate every declaring participant's
		# configured prefix (default "message").
		dir_prefixes: dict = {}
		for spec in store.config["participants"].values():
			proj_dir = spec.get("projection_dir")
			if proj_dir is not None:
				dir_prefixes.setdefault(proj_dir, set()).add(
					spec.get("projection_prefix", "message"))
		for proj_dir, prefixes in dir_prefixes.items():
			try:
				dfd = _open_dir_no_follow(proj_dir, "projection directory")
			except BatonError as exc:
				report["warnings"].append(f"projection directory {proj_dir!r}: {exc}")
				continue
			try:
				for name in sorted(os.listdir(dfd)):
					stem, _, ext = name.rpartition(".")
					if not stem or ("." + ext) not in _KNOWN_PROJECTION_SUFFIXES or not any(
							name.startswith(prefix + "-") for prefix in prefixes):
						continue
					projections["checked"] += 1
					# A non-zero part appends "-part<address>"; the message id is
					# the field before it.
					head, sep, tail = stem.rpartition("-part")
					if sep and all(c.isdigit() or c == "-" for c in tail) and tail:
						stem = head
					mid = stem.rsplit("-", 1)[-1]
					if mid not in durable_ids:
						projections["orphans"].append(os.path.join(proj_dir, name))
			finally:
				os.close(dfd)
		report["projections"] = projections
		if projections["orphans"]:
			report["warnings"].append(
				f"{len(projections['orphans'])} projection file(s) reference no durable message")
	report["ok"] = not report["problems"]
	return report


def dump(config_path: str) -> dict:
	"""Human-inspection snapshot of every protocol table (read-only)."""
	out: dict = {}
	with open_instance(config_path, readonly=True, _for_ceremony=True) as store:
		for table in ("instance_meta", "op_context", "messages", "parts", "claims",
		              "dispositions", "publications", "publication_audience",
		              "contents", "notices", "notice_audience",
		              "notice_seen", "quarantines",
		              "recoveries", "ceremonies", "moves", "accepted_roots"):
			rows = []
			for r in store.conn.execute(f"SELECT * FROM {table}"):
				row = dict(r)
				for key, value in row.items():
					if isinstance(value, bytes):
						row[key] = f"<{len(value)} bytes>"
				rows.append(row)
			out[table] = rows
		out["transitions_tail"] = [dict(r) for r in store.conn.execute(
			"SELECT * FROM transitions ORDER BY seq DESC LIMIT 50")]
		out["transitions_tail_truncated_to"] = 50
		out["transitions_total"] = store.conn.execute(
			"SELECT COUNT(*) FROM transitions").fetchone()[0]
	return out


def resolve_part(nodes: list[dict], path: str) -> dict:
	"""Address ONE part by its position in the ordered manifest.

	`0` is the first top-level part; `1.2` is the third child of the second.
	Dotted addressing exists now rather than later so that nesting a
	`multipart/alternative` inside a message needs no new command surface --
	the addressing scheme already reaches it."""
	if not path:
		raise BatonError("part address must not be empty")
	cursor = nodes
	node = None
	for index, element in enumerate(path.split(".")):
		if not element.isdigit():
			raise BatonError(
				f"part address {path!r} must be dot-separated non-negative integers (e.g. '0' or '1.2')")
		ordinal = int(element)
		if cursor is None:
			raise BatonError(
				f"part {'.'.join(path.split('.')[:index])} is not a container; "
				f"{path!r} addresses nothing", EXIT_NONE)
		if ordinal >= len(cursor):
			raise BatonError(
				f"part address {path!r} is out of range: only {len(cursor)} part(s) at that level",
				EXIT_NONE)
		node = cursor[ordinal]
		cursor = node["parts"]
	return node


def projection_suffix(content_type: str) -> str:
	"""Filename suffix for a projection, by media type. NAMING only -- nothing
	here parses, renders, or transforms the bytes. An unmapped type gets
	`.bin`, which is honest rather than a guess."""
	main, sub, _ = parse_media_type(content_type)
	return _PROJECTION_SUFFIXES.get(f"{main}/{sub}", _PROJECTION_SUFFIX_DEFAULT)


def _project_part(msg: dict, message_id: str, target_dir: str, prefix: str,
                  part: str) -> str:
	"""Shared by the module entry point and `Store.materialize_part`, so the
	CLI and the console cannot drift on where a projection lands or what it is
	called."""
	# A NOTICE HAS NO RETENTION. It is retained until its TTL elapses or `gc`
	# collects it, and while it exists its bytes are as durable as a durable
	# message's -- so the transient guard below simply does not apply to one.
	# `.get` rather than `[...]`: the absence of the column is the signal, and
	# defaulting it to "durable" would quietly re-run a check that has no
	# meaning here.
	if msg.get("retention", RETENTION_DURABLE) != RETENTION_DURABLE:
		raise BatonError(
			f"message {message_id!r} is transient; materializing it would create a "
			"durable copy that defeats the retention contract")
	if not msg["manifest_sha256"]:
		raise BatonError(
			f"message {message_id!r} has no retained content (attachment-only); nothing "
			"to materialize")
	node = resolve_part(msg["parts"], part)
	if node["parts"] is not None:
		raise BatonError(
			f"part {part!r} of message {message_id!r} is a {node['content_type']} container; "
			f"address one of its {len(node['parts'])} leaf part(s) instead")
	if node["body"] is None:
		if node["storage"] == STORAGE_EXTERNAL:
			raise BatonError(
				f"part {part!r} of message {message_id!r} is externally stored at "
				f"{node['attach']['root_id']}:{node['attach']['path']}; it is already a "
				f"file and is not copied into a projection")
		raise BatonError(
			f"part {part!r} of message {message_id!r} has no retained bytes; nothing "
			"to materialize")
	body = node["body"]
	suffix = projection_suffix(node["content_type"])
	dirfd = _open_dir_no_follow(target_dir, "projection directory")
	try:
		if not KIND_RE.match(prefix):
			raise BatonError(f"invalid projection prefix {prefix!r}")
		part_tag = "" if part == "0" else "-part" + part.replace(".", "-")
		name = f"{prefix}-{msg['created_ts'].replace(':', '-')}-{message_id}{part_tag}{suffix}"
		_publish_bytes_at(dirfd, name, body, 0o644, hashlib.sha256(body).hexdigest())
		return os.path.join(target_dir, name)
	finally:
		os.close(dirfd)


def materialize(config_path: str, owner_id: str, target_dir: str,
                prefix: str = "message", part: str = "0", *,
                participant: str) -> str:
	"""Re-emit ONE durable part as a byte-exact projection file in target_dir
	(idempotent: an existing exact file is accepted). Projections are caches,
	never protocol state.

	`participant` IS REQUIRED, ruled 2026-08-10. This verb used to take a bare
	id and ask nobody who they were: in a mailbox holding ten teams' agents,
	any of them could project any other's message content, and with no
	participant on the command there was nothing to write anywhere that a
	boundary had been crossed. Every other content-bearing verb is
	participant-scoped; this one was not, and it was the one that wrote bytes
	to disk.

	Addresses a NOTICE as well as a message, which is the other half of the
	same finding: a notice's bytes were reachable only at delivery, so a
	participant whose terminal truncated the text had no way back to it and
	the tempting alternative was reading the database by hand.

	Reading back writes NOTHING: no claim, no receipt, no transition, and --
	ruled explicitly -- no audit record either.

	Part `0` keeps the historical unsuffixed filename, so the single-part case
	that every existing projection directory holds does not churn; any other
	part appends `-part<address>`. The suffix follows the part's declared media
	type, so a Markdown part is still `.md`."""
	with open_instance(config_path, readonly=True) as store:
		# ONE REFUSAL FOR EVERY FAILURE, and it must not depend on which table
		# the id was found in. An earlier version picked the kind by looking
		# the id up first, so an unauthorized MESSAGE said "unknown message"
		# while a nonexistent id said "unknown notice" -- which tells a
		# non-party that the id exists and is a message. That is the
		# enumeration oracle this surface is supposed not to be, and a test
		# comparing the two refusal strings is what caught it.
		owner = kind = None
		for candidate, table in (("message", "messages"), ("notice", "notices")):
			try:
				row = store.authorize_read(candidate, owner_id, participant)
			except BatonError:
				continue
			owner, kind = dict(row), candidate
			break
		if owner is None:
			raise BatonError(f"unknown id {owner_id!r}", EXIT_NONE)
		owner["parts"] = store._read_parts(kind, owner_id)
	return _project_part(owner, owner_id, target_dir, prefix, part)


# ---------------------------------------------------------------------------
# CLI (thin layer over the transaction APIs; exit codes per module table)
# ---------------------------------------------------------------------------

def _to_jsonable(value):
	"""Explicit fail-closed protocol encoding: only JSON-native types pass;
	anything unexpected is a bug surfaced as damage, never silently
	stringified."""
	if type(value) is float:
		import math
		if not math.isfinite(value):
			raise BatonError("non-finite float in protocol output", EXIT_DAMAGE)
		return value
	if value is None or type(value) in (str, int, bool):
		return value
	if isinstance(value, dict):
		out = {}
		for k, v in value.items():
			if type(k) is not str:
				raise BatonError(
					f"non-string dict key {k!r} in protocol output", EXIT_DAMAGE)
			out[k] = _to_jsonable(v)
		return out
	if isinstance(value, (list, tuple)):
		return [_to_jsonable(v) for v in value]
	raise BatonError(f"unexpected type {type(value).__name__} in protocol output", EXIT_DAMAGE)


def _print_result(obj) -> None:
	print(json.dumps(_to_jsonable(obj), indent=2, sort_keys=True))





def _authored_parts(ns, *, roots=None, legacy_attach: bool = False):
	"""The `parts` list for a verb, or None when the caller used the legacy
	single-body surface.

	`--attach` is collected with the parts so it can take its place in
	occurrence order. When no `--part` and no `--references` were given, this
	returns None and the caller falls back to the ORIGINAL `--body` plus
	`attach=` path, byte for byte -- so every existing command keeps its
	existing meaning and its existing leaf order.

	`--body` IS NOT DISCARDED HERE. An earlier version entered part mode on
	`--part` or `--references` and passed `body=None` from there on, so
	`send --body notes.md --references refs.txt` exited zero having published
	only the references leaf. It now becomes the first leaf and keeps its
	legacy `--content-type`/`--disposition`/`--part-name`, which is where that
	metadata has always applied.

	Beside `--part` it is REFUSED instead. A general part carries its own type,
	disposition, name and position; `--body` carries a type and no position, so
	the two describe the same leaf in two vocabularies and there is no reading
	of the combination that is obviously right. Refusing beats picking one.
	"""
	from .authoring import build, parse_part
	items = getattr(ns, "content", None) or []
	kinds = {kind for kind, _ in items}
	if not (kinds & {"part", "references"}):
		# `--attach` ALONE is enough on a verb with no legacy attach path.
		#
		# `send` has always had a store-level `attach=` parameter, so a lone
		# `--attach` there keeps taking the original route, byte for byte.
		# `reply` never had one. Falling back to the legacy route there meant
		# the attachment reached nothing at all: the command succeeded and
		# published a response without it. Whether a verb HAS a legacy route
		# is the whole distinction, so the caller states it rather than this
		# function guessing from the option names.
		if not ("attach" in kinds and not legacy_attach):
			return None
	body_spec = getattr(ns, "body", None)
	legacy = (("--content-type", getattr(ns, "content_type", None)),
	          ("--disposition", getattr(ns, "disposition", None)),
	          ("--part-name", getattr(ns, "part_name", None)))
	body = None
	if body_spec is not None:
		if any(kind == "part" for kind, _ in items):
			raise BatonError(
				"--body cannot be combined with --part: a general part already "
				"carries its own type, disposition, name and position. Author "
				"the body as another --part")
		body = (body_spec, ns.content_type, ns.disposition, ns.part_name)
	else:
		# Never silently ignored. Metadata describing a body that was not
		# supplied is a request this command cannot honour, and dropping it
		# tells the caller it worked.
		orphaned = [name for name, value in legacy if value is not None]
		if orphaned:
			raise BatonError(
				f"{', '.join(orphaned)} describes --body, which was not supplied; "
				f"per-part metadata belongs on each --part")
	return build(items, body=body, roots=roots, parse_part=parse_part,
	             read_bytes=_read_body, read_text=_read_references)


def _or_stdin(spec: str | None) -> str:
	"""The legacy stdin default for the verbs that had one.

	`send-notice` and `reply` used `default="-"` on `--body`. That default now
	lives here instead, so the namespace can still say "no body was supplied"
	-- which is what part mode needs in order to know whether to build a body
	leaf, and what the argparse default was silently erasing.
	"""
	return "-" if spec is None else spec


def _read_references(spec: str) -> str:
	"""A references file as text, refusing invalid UTF-8 as a BatonError.

	A bare `.decode("utf-8")` raises `UnicodeDecodeError`, which `main` does not
	catch -- so a mis-encoded references file printed a traceback rather than a
	diagnostic. The bytes are NOT echoed: they are by definition not valid
	UTF-8, and putting them on a terminal is its own problem.
	"""
	try:
		return (_read_body(spec) or b"").decode("utf-8")
	except UnicodeDecodeError:
		where = "standard input" if spec == "-" else repr(spec)
		raise BatonError(
			f"--references {where}: not valid UTF-8; a references list is text, "
			f"one repository-relative path per line") from None


def _legacy_attach(ns):
	"""The single `--attach` value the old surface passed to the store.

	Last one wins, which is what a non-repeatable argparse option did before
	it joined the shared list. Only consulted on the legacy path.
	"""
	items = getattr(ns, "content", None) or []
	values = [value for kind, value in items if kind == "attach"]
	return values[-1] if values else None


def _read_body(spec: str | None) -> bytes | None:
	if spec is None:
		return None
	if spec == "-":
		return sys.stdin.buffer.read()
	try:
		with open(spec, "rb") as handle:
			return handle.read()
	except OSError as exc:
		raise BatonError(f"body file unreadable: {exc}") from exc


# Every option that supplies CONTENT or names how content is shaped, as its
# NAMESPACE attribute. `--part`, `--references` and `--attach` are deliberately
# absent: they do not have namespace attributes at all. `authoring_opts` sends
# all three into one shared ordered `ns.content` list, so leaf order is the
# order the human typed -- and `getattr(ns, "part", None)` was therefore
# permanently None, which made three of the eight exclusivity checks dead code
# that always passed.
_TWEET_EXCLUSIVE = ("subject", "body", "content_type", "disposition", "part_name")


def _tweet_conflicts(ns) -> list[str]:
	"""Which content options were supplied beside `--tweet`, named as flags.

	Reads BOTH shapes, because the surface has two: ordinary attributes, and
	the shared ordered list that `--part`/`--references`/`--attach` collect
	into. Checking only the first is how `--tweet x --attach root:file`
	exited zero and published a contentless message, silently discarding an
	attachment the sender explicitly asked for.
	"""
	found = {f"--{name.replace('_', '-')}" for name in _TWEET_EXCLUSIVE
	         if getattr(ns, name, None) not in (None, [], ())}
	for kind, _value in getattr(ns, "content", None) or []:
		found.add(f"--{kind.replace('_', '-')}")
	return sorted(found)


def _tweet_subject(ns) -> str | None:
	"""Resolve `--tweet`, or None when it was not used.

	The value BECOMES THE SUBJECT and the message publishes with no content.
	An explicit option rather than an inferred one: every alternative infers
	"I meant to send nothing" from an ABSENCE -- no `--body`, or empty stdin
	-- and an absence is also what a broken pipe, a truncated heredoc, or a
	missing input file looks like. Every subject-only message on this
	deployment was already being produced by accident, through the zero-byte
	body defect, which is the failure this whole rule exists to end.

	`--tweet -` reads stdin as UTF-8 and removes EXACTLY ONE terminal LF or
	CRLF, because `printf 'ship it\n' | ...` is what a human writing one line
	actually types. Only the line terminator is forgiven: a leading space or a
	second trailing newline still reaches the subject validator and is
	refused.

	Nothing is silently ignored. `--tweet` beside any content option is a
	refusal in both directions -- dropping the body would lose content, and
	dropping the flag would make it decorative.
	"""
	tweet = getattr(ns, "tweet", None)
	if tweet is None:
		return None
	conflicts = _tweet_conflicts(ns)
	if conflicts:
		raise BatonError(
			f"--tweet is the whole message, so it cannot be combined with "
			f"{', '.join(sorted(conflicts))}")
	if tweet == "-":
		raw = sys.stdin.buffer.read()
		try:
			text = raw.decode("utf-8")
		except UnicodeDecodeError:
			raise BatonError("--tweet - expects UTF-8 text") from None
		# EXACTLY ONE terminator, and CRLF before LF so the CR is not left
		# behind to fail validation as a control character.
		for terminator in ("\r\n", "\n"):
			if text.endswith(terminator):
				text = text[:-len(terminator)]
				break
	else:
		text = tweet
	if not text:
		raise BatonError("--tweet requires text; there is nothing to send")
	# NOT validated here. A tweet IS a subject, and `send`/`reply` already run
	# `validate_subject` on whatever they are given -- one line, no controls,
	# no edge whitespace, at most 255 bytes as UTF-8.
	#
	# An earlier version called the validator here too. It was redundant, and
	# the break check proved it: removing the call failed nothing, because
	# every refusal still arrived from the store. A second gate checking the
	# same property is not extra safety -- it is a second thing to keep in
	# agreement, and the one that drifts is the one nobody tests.
	return text


def _parse_attach(spec: str | None):
	if spec is None:
		return None
	root_id, sep, rel = spec.partition(":")
	if not sep or not root_id or not rel:
		raise BatonError("--attach expects ROOT_ID:RELATIVE/PATH")
	return {"root_id": root_id, "path": rel}


def _build_parser():
	import argparse
	parser = argparse.ArgumentParser(
		prog="baton", description="Portable coordination over one transactional authority")
	parser.add_argument("--config", help="absolute path to the instance baton.json")
	parser.add_argument("--version", action="version",
	                    version=f"baton {TOOL_VERSION} (protocol {PROTOCOL_VERSION})")
	sub = parser.add_subparsers(dest="command", required=True)

	def cmd(name, **kwargs):
		c = sub.add_parser(name, **kwargs)
		return c

	def ident(c):
		c.add_argument("--participant", required=True)

	def authoring_opts(c, *, attach=True):
		"""The repeatable multipart surface, identical on every verb that
		authors content.

		One shared ordered destination, so `--part`, `--attach` and
		`--references` interleave in the order the human typed them -- leaf
		order is manifest identity, and argparse gives each option its own
		list unless told otherwise.

		`--attach` joins that list rather than keeping a private one, which is
		what lets it take its place among the parts. Its LEGACY behaviour is
		unchanged: with no `--part` and no `--references`, the single value is
		handed to the store exactly as before.
		"""
		from .authoring import Collect
		c.add_argument("--part", dest="content", action=Collect, kind="part",
		               default=None, metavar="DESCRIPTOR",
		               # `%%`, not `%`. argparse formats help through
		               # `help % params`, so a literal percent -- which this
		               # example needs, the descriptor being a URL query --
		               # raises `TypeError: %c requires int or char` and takes
		               # `--help` down on every verb that carries this option.
		               help="repeatable inline part, e.g. "
		                    "'source=notes.md&type=text/markdown;%%20charset=utf-8' "
		                    "— fields: source, type, disposition, name")
		c.add_argument("--references", dest="content", action=Collect,
		               kind="references", default=None, metavar="FILE",
		               # No literal `--attach` in this text: `close` does not
		               # offer that option, and a test asserts its help does
		               # not mention it. Naming the option here put it back on
		               # the screen of the one verb that cannot use it.
		               help="file of ROOT_ID:RELATIVE/POSIX/PATH references, "
		                    "one per line, using the instance's configured "
		                    "roots; - for stdin")
		if attach:
			c.add_argument("--attach", dest="content", action=Collect,
			               kind="attach", default=None,
			               help="ROOT_ID:REL/PATH — pinned external part; may "
			                    "accompany --body rather than replace it")

	def content_opts(c):
		"""Type the one part this command publishes. The CLI writes a
		single-leaf manifest; the storage layer and the delivery envelope are
		multipart throughout, so a repeatable per-part flag is a capability
		extension rather than another protocol redesign."""
		# Defaults are applied in the store, NOT here: argparse defaults would
		# make an omitted flag indistinguishable from an explicit one, and the
		# store must be able to refuse content metadata on an operation that
		# carries no content.
		c.add_argument("--content-type", default=None,
		               help=f"IANA media type of the body (default: {DEFAULT_CONTENT_TYPE})")
		c.add_argument("--disposition", choices=sorted(DISPOSITIONS), default=None,
		               help=f"RFC 2183 content disposition (default: {DISPOSITION_INLINE})")
		c.add_argument("--part-name",
		               help="advisory name for the part; it is a LABEL, not a "
		                    "path, and never selects where anything is written")


	cmd("init", help="create a new instance beside --config")
	c = cmd("regen", help="accept a generation+1 config")
	ident(c)
	c = cmd("send", help="send a directed message")
	ident(c)
	c.add_argument("--tweet", metavar="TEXT",
	               help="the whole message is this one line, which becomes its "
	                    "subject; no body is published. Use `-` to read the line "
	                    "from stdin. Cannot be combined with --subject or any "
	                    "content option.")
	c.add_argument("--possible-duplicate", action="store_true",
	               help="you could not tell whether an earlier attempt was "
	                    "published; marks this one, immutably, for the "
	                    "recipient to judge")
	c.add_argument("--to", required=True, action="append", metavar="PARTICIPANT",
	               help="exact participant; repeat for several, each of whom "
	                    "gets their own claim and disposition")
	c.add_argument("--kind", required=True)
	c.add_argument("--subject", help="one-line human summary shown in an inbox")
	c.add_argument("--thread")
	c.add_argument("--retention", choices=sorted(RETENTIONS), default=RETENTION_DURABLE)
	c.add_argument("--outcome")
	c.add_argument("--body", help="body file or - for stdin (default: stdin)")
	authoring_opts(c)
	content_opts(c)
	c = cmd("send-notice", help="broadcast a notice (finite TTL)")
	ident(c)
	c.add_argument("--kind", required=True)
	c.add_argument("--subject", help="one-line human summary shown in an inbox")
	c.add_argument("--ttl-seconds", type=int)
	# QUOTE IT in documentation: an unquoted `baton.*` is expanded by the
	# shell against the current directory, which usually matches nothing and
	# silently passes the literal through -- but not always.
	c.add_argument("--possible-duplicate", action="store_true",
	               help="you could not tell whether an earlier attempt was "
	                    "published; marks this one, immutably")
	c.add_argument("--scope", metavar="TEAM.*",
	               help="address a team instead of everyone, e.g. 'baton.*'; "
	                    "the audience is expanded and frozen at publication")
	# Default None, NOT "-". This verb and `reply` defaulted to stdin, which
	# made a body that was never supplied indistinguishable from one explicitly
	# read from stdin -- and part mode has to tell them apart to know whether
	# the caller asked for a body leaf at all. The stdin fallback moves to the
	# legacy dispatch, where it applies exactly as before.
	c.add_argument("--body")
	authoring_opts(c, attach=False)
	content_opts(c)
	c = cmd("claim", help="claim one pending message")
	ident(c)
	c.add_argument("--message-id")
	c = cmd("wait", help="block until work exists; READ-ONLY, claims nothing "
	                     "(then use claim or see to consume it)")
	ident(c)
	c.add_argument("--timeout", type=float)
	c.add_argument("--interval", type=float, default=WAIT_RESCAN_INTERVAL_S)
	c = cmd("see", help="mark unseen notices seen and print them")
	ident(c)
	c = cmd("expire", help="expire notices (author-early or TTL-elapsed)")
	ident(c)
	c.add_argument("--notice-id")
	c = cmd("reply", help="reply to a held claim (effectively-once)")
	ident(c)
	c.add_argument("claim_id")
	c.add_argument("--tweet", metavar="TEXT",
	               help="the whole message is this one line, which becomes its "
	                    "subject; no body is published. Use `-` to read the line "
	                    "from stdin. Cannot be combined with --subject or any "
	                    "content option.")
	c.add_argument("--kind", required=True)
	c.add_argument("--subject",
	               help="one-line human summary (default: inherit the message's subject)")
	c.add_argument("--to")
	c.add_argument("--thread")
	c.add_argument("--retention", choices=sorted(RETENTIONS))
	c.add_argument("--outcome")
	c.add_argument("--body")  # default None; see send-notice above
	authoring_opts(c)
	content_opts(c)
	c = cmd("close", help="close a held claim (terminal disposition)")
	ident(c)
	c.add_argument("claim_id")
	c.add_argument("--outcome")
	c.add_argument("--retention", choices=sorted(RETENTIONS))
	c.add_argument("--body")
	# No `--attach`. External storage is refused on a disposition anyway --
	# `reject_external_parts` says so, because a close is a terminal audit
	# record with no delivery and so no way to notice or resolve a stale pin --
	# and offering an option whose every use is refused is a worse surface than
	# not offering it. Inline `--part ...&disposition=attachment` still works;
	# what is unavailable here is EXTERNAL storage.
	authoring_opts(c, attach=False)
	content_opts(c)
	c = cmd("recover-claim", help="capability-authorized recovery of an abandoned claim")
	ident(c)
	c.add_argument("claim_id")
	c.add_argument("--reason", required=True)
	c = cmd("quarantine-attachment",
	        help="capability-authorized disposition for a damaged attachment")
	ident(c)
	c.add_argument("message_id")
	c.add_argument("--reason", required=True)
	c = cmd("snapshot", help="validated copy of a maintenance-gated instance")
	ident(c)
	c.add_argument("--dir", required=True)
	c = cmd("gc", help="bounded retention garbage collection")
	ident(c)
	c = cmd("scan", help="pending/claimed inventory")
	c.add_argument("--participant")
	cmd("doctor", help="read-only diagnosis")
	cmd("dump", help="read-only table snapshot")
	cmd("inspect", help="move/maintenance state (read-only)")
	c = cmd("materialize",
	        help="re-emit one durable content part as a projection file "
	             "(message or notice; requires --participant)")
	ident(c)
	c.add_argument("message_id", metavar="ID",
	               help="a message id, or a notice id you have already seen")
	c.add_argument("--dir", required=True)
	c.add_argument("--prefix", default="message")
	c.add_argument("--part", default="0",
	               help="part address in the ordered manifest, e.g. 0 or 1.2 (default: 0)")
	c = cmd("maintenance-enter", help="set the maintenance gate")
	ident(c)
	c.add_argument("--reason", required=True)
	c.add_argument("--move", action="store_true")
	c.add_argument("--destination", help="destination CONFIG path (with --move)")
	c = cmd("maintenance-exit", help="clear a plain maintenance gate")
	ident(c)
	c.add_argument("--reason", required=True)
	c = cmd("move-copy", help="copy the drained source to its bound destination")
	ident(c)
	c = cmd("move-bind", help="flip the copied pair to the destination role")
	ident(c)
	c.add_argument("--token", required=True)
	c = cmd("move-activate", help="activate the bound destination")
	ident(c)
	c.add_argument("--token", required=True)
	c = cmd("move-decommission", help="mark the source moved forever")
	ident(c)
	c.add_argument("--token", required=True)
	c.add_argument("--moved-to", required=True)
	c = cmd("abort-move", help="source-only move abort (attestation required)")
	ident(c)
	c.add_argument("--token", required=True)
	c.add_argument("--destination-destroyed", action="store_true")
	c.add_argument("--reason", required=True)
	c = cmd("migrate", help="audited migration gate")
	ident(c)
	return parser


def main(argv: list[str] | None = None) -> int:
	parser = _build_parser()
	try:
		ns = parser.parse_args(argv)
	except SystemExit as exc:
		# Usage/parse failures are VALIDATION errors (4); --help/--version exit
		# 0. Exit 2 is reserved for the environment-floor bootstrap.
		code = exc.code if isinstance(exc.code, int) else EXIT_PROTOCOL
		return 0 if code == 0 else EXIT_PROTOCOL
	try:
		if ns.command != "init" and ns.config is None:
			raise BatonError("--config is required")
		if ns.command == "init":
			if ns.config is None:
				raise BatonError("--config is required")
			init_instance(ns.config)
			_print_result({"initialized": True, "config": ns.config})
		elif ns.command == "regen":
			_print_result(regen_instance(ns.config, participant=ns.participant,))
		elif ns.command == "send":
			# An explicit --body, or stdin when nothing external was named. With
			# --attach alone, stdin is NOT consumed: the caller asked to send a
			# file, not to be blocked on a terminal.
			# ONE instance, opened before the content is built: a reference
			# names a ROOT, and which roots exist is the authority's answer
			# rather than this process's.
			tweet = _tweet_subject(ns)
			with open_instance(ns.config) as store:
				parts = None if tweet is not None else _authored_parts(
					ns, roots=store.list_roots(), legacy_attach=True)
				attach = None if tweet is not None else _legacy_attach(ns)
				if tweet is not None:
					# The subject IS the message: no body, no parts, no
					# implicit stdin read.
					body = None
				elif parts is not None:
					# Part mode: every leaf is in `parts`, including any
					# `--attach`, in the order the options appeared.
					body = None
					attach = None
				elif ns.body is not None:
					body = _read_body(ns.body)
				elif attach is None:
					body = _read_body("-")
				else:
					body = None
				# ONE address stays a string so the historical single-recipient
				# return shape is unchanged; several become a list.
				addressees = ns.to if len(ns.to) > 1 else ns.to[0]
				message_id = store.send(
					ns.participant, addressees, kind=ns.kind,
					subject=tweet if tweet is not None else ns.subject,
					possible_duplicate=ns.possible_duplicate,
					body=body, parts=parts,
					content_type=ns.content_type if parts is None else None,
					disposition=ns.disposition if parts is None else None,
					part_name=ns.part_name if parts is None else None,
					thread_id=ns.thread, retention=ns.retention,
					outcome=ns.outcome, attach=attach)
			# BOTH IDENTITIES, always. The plan pinned `publication_id` on the
			# single-recipient result and the recipient-to-message mapping on
			# the multi-recipient one; the result carried one bare string
			# either way, so a caller could not follow up on an individual
			# delivery without going back to the store for what the call it
			# just made already knew.
			with open_instance(ns.config) as store:
				if isinstance(ns.to, list) and len(ns.to) > 1:
					_print_result({"publication_id": message_id,
					               "recipients": store.publication_deliveries(message_id)})
				else:
					_print_result({
						"message_id": message_id,
						"publication_id": store.get_message(message_id)["publication_id"]})
		elif ns.command == "send-notice":
			with open_instance(ns.config) as store:
				parts = _authored_parts(ns, roots=store.list_roots())
				notice_id = store.send_notice(
					ns.participant, kind=ns.kind, subject=ns.subject, scope=ns.scope,
					possible_duplicate=ns.possible_duplicate,
					body=None if parts is not None else (_read_body(_or_stdin(ns.body)) or b""),
					parts=parts,
					content_type=ns.content_type if parts is None else None,
					disposition=ns.disposition if parts is None else None,
					part_name=ns.part_name if parts is None else None,
					ttl_seconds=ns.ttl_seconds)
			_print_result({"notice_id": notice_id})
		elif ns.command == "claim":
			with open_instance(ns.config) as store:
				claim = store.claim(ns.participant,
				                    message_id=ns.message_id)
				result = _delivery(store, claim)
			_print_result(result)
		elif ns.command == "wait":
			# READ-ONLY, ruled 2026-08-10. `wait` used to claim the message it
			# returned, which made the most obvious command the one that is
			# unsafe to leave running: an agent host can yield a terminal into
			# the background and never wake the agent, and the claim sits held
			# with nobody able to answer it.
			#
			# Now a missed wake delays work instead of holding it. Consumption
			# is explicit -- `claim` for directed work, `see` for a notice --
			# and there is deliberately no second spelling of this verb.
			result = wait_for_readiness(ns.config, ns.participant, timeout_s=ns.timeout,
			                            rescan_interval_s=ns.interval)
			_print_result(result)
		elif ns.command == "see":
			with open_instance(ns.config) as store:
				seen = store.see(ns.participant)
			# One representation for both inbound channels: `see` prints the
			# same content envelope `wait` delivers under {"notice": ...}.
			_print_result({"notices": [_notice_delivery(n)["notice"] for n in seen]})
		elif ns.command == "expire":
			with open_instance(ns.config) as store:
				removed = store.expire(ns.participant,
				                       notice_id=ns.notice_id)
			_print_result({"expired": removed})
		elif ns.command == "reply":
			tweet = _tweet_subject(ns)
			with open_instance(ns.config) as store:
				parts = None if tweet is not None else _authored_parts(
					ns, roots=store.list_roots())
				result = store.reply(ns.claim_id, participant=ns.participant,
				                     kind=ns.kind,
				                     subject=tweet if tweet is not None else ns.subject,
				                     # `--tweet` publishes no content and reads
				                     # no stdin; without it the implicit-stdin
				                     # behaviour is exactly as before.
				                     body=None if (tweet is not None or parts is not None)
				                     else _read_body(_or_stdin(ns.body)),
				                     parts=parts,
				                     content_type=ns.content_type if parts is None else None,
				                     disposition=ns.disposition if parts is None else None,
				                     part_name=ns.part_name if parts is None else None,
				                     outcome=ns.outcome, recipient=ns.to,
				                     thread_id=ns.thread, retention=ns.retention)
			_print_result(result)
		elif ns.command == "close":
			with open_instance(ns.config) as store:
				parts = _authored_parts(ns, roots=store.list_roots())
				result = store.close_claim(
					ns.claim_id, participant=ns.participant,
					body=None if parts is not None else _read_body(ns.body),
					parts=parts,
					content_type=ns.content_type if parts is None else None,
					disposition=ns.disposition if parts is None else None,
					part_name=ns.part_name if parts is None else None,
					outcome=ns.outcome, retention=ns.retention)
			_print_result(result)
		elif ns.command == "recover-claim":
			with open_instance(ns.config) as store:
				result = store.recover_claim(ns.claim_id, participant=ns.participant, reason=ns.reason)
			_print_result(result)
		elif ns.command == "snapshot":
			_print_result(snapshot_instance(ns.config, ns.dir, participant=ns.participant,))
		elif ns.command == "quarantine-attachment":
			_print_result(quarantine_attachment_instance(
				ns.config, ns.message_id, participant=ns.participant, reason=ns.reason))
		elif ns.command == "gc":
			with open_instance(ns.config) as store:
				result = store.gc(participant=ns.participant)
			_print_result(result)
		elif ns.command == "scan":
			with open_instance(ns.config, readonly=True, _for_ceremony=True) as store:
				_print_result(store.scan(ns.participant))
		elif ns.command == "doctor":
			report = doctor(ns.config)
			_print_result(report)
			return 0 if report["ok"] else EXIT_DAMAGE
		elif ns.command == "dump":
			_print_result(dump(ns.config))
		elif ns.command == "inspect":
			_print_result(move_status_inspect(ns.config))
		elif ns.command == "materialize":
			path = materialize(ns.config, ns.message_id, ns.dir, prefix=ns.prefix,
			                   part=ns.part, participant=ns.participant)
			_print_result({"projection": path})
		elif ns.command == "maintenance-enter":
			_print_result(maintenance_enter(
				ns.config, participant=ns.participant,
				reason=ns.reason, move=ns.move, destination=ns.destination))
		elif ns.command == "maintenance-exit":
			_print_result(maintenance_exit(
				ns.config, participant=ns.participant, reason=ns.reason))
		elif ns.command == "move-copy":
			_print_result(move_copy(ns.config, participant=ns.participant,))
		elif ns.command == "move-bind":
			_print_result(move_bind_destination(
				ns.config, participant=ns.participant,
				token=ns.token))
		elif ns.command == "move-activate":
			_print_result(move_activate(
				ns.config, participant=ns.participant,
				token=ns.token))
		elif ns.command == "move-decommission":
			_print_result(move_decommission(
				ns.config, participant=ns.participant,
				token=ns.token, moved_to=ns.moved_to))
		elif ns.command == "abort-move":
			_print_result(abort_move(
				ns.config, participant=ns.participant,
				token=ns.token, destination_destroyed=ns.destination_destroyed,
				reason=ns.reason))
		elif ns.command == "migrate":
			_print_result(migrate_instance(ns.config, participant=ns.participant,))
		else:  # pragma: no cover
			raise BatonError(f"unknown command {ns.command!r}")
		return 0
	except BatonError as exc:
		print(f"baton: {exc}", file=sys.stderr)
		return exc.exit_code


if __name__ == "__main__":  # pragma: no cover
	raise SystemExit(main())
