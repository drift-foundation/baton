"""Composing a multipart message from command-line options.

Everything here is independent of how a part is SPELLED on the command line.
That spelling is one escalated decision; this module owns the three properties
that hold whichever spelling wins, and each of them is a property the obvious
implementation gets wrong.

ORDER IS IDENTITY. Leaf order is part of the manifest digest, and the manifest
is what retry compares. So the order the human wrote their options in has to
survive into the message. `argparse` cannot express that on its own: each
option gets its own list, and `--part a --attach b --part c` arrives as
`parts=[a, c]`, `attach=[b]` with the interleaving discarded. `Collect` is one
shared ordered list that every content option appends to, so occurrence order
IS the answer rather than something reconstructed afterwards.

ONE STDIN. A repeatable option makes `-` ambiguous in a way a single `--body`
never was: two parts both reading standard input would silently give the
second one nothing. That is refused BEFORE anything is read, because a
diagnostic after half a message has been consumed is a diagnostic about a
message that no longer exists.

`--body` STILL COUNTS. An earlier version of this module entered "part mode"
whenever `--part` or `--references` appeared and passed `body=None` from there
on -- so `send --body notes.md --references refs.txt` exited zero having
published only the references leaf. A command that succeeds while dropping
content the caller named is worse than one that fails, and it was found by
review rather than by any test here. `--body` is now folded into the plan as
the first leaf, carrying its own legacy metadata, and it is refused outright
beside `--part`, whose leaves carry their own type, name and position.

`name` ON THE SURFACE, `part_name` INSIDE. The descriptor field stayed `name`
while protocol 9 storage said `filename`, precisely so the rename would land
as a storage change rather than a user-visible one. Protocol 10 landed it and
the CLI surface did not move at all. New surface uses the new word now and translates
inward, so this CLI does not have to teach a vocabulary it is about to
retire — and so the rename, when it lands, is a storage change rather than a
user-visible one.
"""

from __future__ import annotations

import argparse
import re
from urllib.parse import unquote

from ._impl import DEFAULT_ATTACHMENT_TYPE, BatonError

STDIN = "-"

# The ruled descriptor: URL-query named fields, RFC 3986 percent encoding.
PART_KEYS = ("source", "type", "disposition", "name")
REQUIRED_KEYS = ("source", "type")
# The public surface has exactly two. Refused HERE rather than left to the
# store's normalizer, which would diagnose it out of context -- the human
# typed a `--part` field and should be told which field, in a message about
# the command they ran.
DISPOSITIONS = ("inline", "attachment")

# `unquote` does NOT raise on a malformed escape -- `%zz` and `%2` come back
# unchanged -- so a truncated or non-hex escape would reach the store as
# literal text and be stored as a media type or a path nobody typed. Validated
# here instead.
_BAD_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")

# RFC 3986 `query`: pchar / "/" / "?", where pchar is unreserved / pct-encoded
# / sub-delims / ":" / "@". Written out rather than computed so the surface the
# CLI accepts is readable in one place.
#
# This keeps everything a descriptor actually wants unencoded -- `/` and `+`
# for media types, `;` and `=` for their parameters, `:` and `@`, `.` `-` `_`
# `~` for filenames. What it excludes is the raw SPACE, control characters, and
# non-ASCII bytes: a descriptor is a URL query, so `%20` is the space and
# non-ASCII travels percent-encoded as UTF-8. Accepting the raw forms would
# make the same descriptor mean different things depending on the shell,
# locale and terminal encoding it passed through.
_QUERY_CHARS = frozenset(
	"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
	"-._~"          # unreserved
	"!$&\'()*+,;="   # sub-delims
	":@/?"          # pchar extras, plus query's own additions
	"%")            # percent-encoding introducer, validated separately


def _check_query_charset(value: str, where: str) -> None:
	"""Refuse a descriptor that is not a URL query.

	Diagnostics name the CATEGORY and the position, never the character or the
	surrounding text: the descriptor can carry a path or a media type from
	anywhere, and echoing it puts unreviewed bytes on the terminal. A position
	is enough to find it and gives nothing away.
	"""
	for index, char in enumerate(value, start=1):
		if char in _QUERY_CHARS:
			continue
		if char in " \t":
			why = "raw whitespace (a space is %20 in a query)"
		elif ord(char) < 0x20 or ord(char) == 0x7F:
			why = "a control character"
		elif ord(char) > 0x7F:
			why = "a non-ASCII character (percent-encode it as UTF-8)"
		else:
			why = "a character not permitted in a URL query"
		raise BatonError(
			f"{where}: {why} at position {index}; the descriptor is an RFC 3986 "
			f"query")


def _decode(field: str, raw: str, where: str) -> str:
	"""Percent-decode one key or value, RFC 3986, strictly.

	Three stdlib defaults are wrong for this and each fails silently:

	`unquote_plus` and `parse_qsl` apply HTML FORM semantics and turn a literal
	`+` into a space, which corrupts `application/ld+json` into an invalid
	media type -- and the failure then surfaces as a media-type error pointing
	at the wrong thing.

	`unquote` does not raise on a MALFORMED escape: `%zz` and `%2` come back
	unchanged, so a truncated escape would be stored as literal text nobody
	typed. Validated before decoding.

	`unquote` defaults to `errors="replace"`, so invalid UTF-8 becomes U+FFFD
	and a path or media type quietly becomes a different string. Decoded
	strictly, so it is refused instead.
	"""
	if _BAD_ESCAPE.search(raw):
		raise BatonError(f"{where}: {field}: malformed percent escape")
	try:
		return unquote(raw, errors="strict")
	except UnicodeDecodeError:
		# The value is NOT echoed: it is by definition not valid UTF-8, and
		# putting undecodable bytes on a terminal is its own problem.
		raise BatonError(f"{where}: {field}: percent bytes are not valid UTF-8") from None


def parse_part(value: str, *, where: str = "--part") -> tuple:
	"""One `--part` descriptor -> `(type, source, disposition, name)`.

	    source=report.pdf&type=application/pdf&disposition=attachment&name=Q3.pdf

	The whole descriptor must be a valid RFC 3986 query: `%20` for a space,
	percent-encoded UTF-8 for anything non-ASCII. `/`, `;`, `=`, `+`, `:` and
	`@` travel unencoded, which is what keeps a media type and its parameters
	readable -- `type=text/markdown;%20charset=utf-8`.

	Fields split at `&`, each pair at its FIRST `=` -- which is what lets
	`type=text/markdown; charset=utf-8` travel without encoding its own `=`.
	Field order inside one descriptor carries no meaning; the order of the
	`--part` OPTIONS carries all of it.

	Diagnostics name the occurrence and the field and never echo the value.
	A descriptor can carry a path or a media type from anywhere, and a message
	that quotes it back has put unreviewed bytes in front of whoever is reading
	the terminal.
	"""
	_check_query_charset(value, where)
	seen: dict[str, str] = {}
	for pair in value.split("&"):
		if not pair:
			raise BatonError(f"{where}: empty field")
		raw_key, sep, raw = pair.partition("=")
		if not sep:
			raise BatonError(f"{where}: a field has no value")
		# Keys are decoded TOO, and duplicates are detected afterwards --
		# otherwise `%74ype` is a stranger to `type` and slips past the
		# duplicate check as an unknown field, which is a different error for
		# the same mistake.
		#
		# NOT stripped. An earlier version did, which silently accepted
		# ` type=` and made a key the author did not write. Surrounding
		# whitespace in a field name is a typo, and saying so is more useful
		# than repairing it.
		key = _decode("field name", raw_key, where)
		if key != key.strip():
			raise BatonError(
				f"{where}: field name has surrounding whitespace")
		if key not in PART_KEYS:
			raise BatonError(
				f"{where}: unknown field {key!r}; known fields are "
				f"{', '.join(PART_KEYS)}")
		if key in seen:
			raise BatonError(f"{where}: duplicate field {key!r}")
		decoded = _decode(key, raw, where)
		if not decoded:
			# `name=` is not "no name". Absent and empty are different, and the
			# store defaults only on absent.
			raise BatonError(f"{where}: field {key!r} is empty")
		seen[key] = decoded
	missing = [key for key in REQUIRED_KEYS if key not in seen]
	if missing:
		raise BatonError(f"{where}: missing required field(s) {', '.join(missing)}")
	disposition = seen.get("disposition", "inline")
	if disposition not in DISPOSITIONS:
		raise BatonError(
			f"{where}: disposition must be one of {', '.join(DISPOSITIONS)}")
	return seen["type"], seen["source"], disposition, seen.get("name")


class Collect(argparse.Action):
	"""Append `(kind, value)` to ONE shared list across several options.

	`kind` is the option's role -- `part`, `attach`, `references` -- so the
	consumer can tell what each entry was without re-parsing it, and the list
	preserves the order the human typed.
	"""

	def __init__(self, option_strings, dest, kind=None, **kwargs):
		if kind is None:
			raise ValueError("Collect requires a kind")
		self._kind = kind
		super().__init__(option_strings, dest, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		items = getattr(namespace, self.dest, None)
		if items is None:
			items = []
			setattr(namespace, self.dest, items)
		items.append((self._kind, values))


def one_stdin(sources) -> None:
	"""Refuse more than one `-` across every content option, before reading.

	Takes PARSED sources, not raw option strings. An earlier version looked
	for a trailing `-` inside the unparsed value, which meant this function
	knew about the spelling -- the one thing this module exists not to know --
	and it missed a source that did not happen to end the string.

	Counted across ALL kinds together, not per option: `--part -` beside
	`--references -` is the same collision as two parts, and a per-option
	check would miss exactly the case a repeatable surface introduces.
	"""
	readers = [f"{kind} {source!r}" for kind, source in sources
	           if source == STDIN]
	if len(readers) > 1:
		raise BatonError(
			"only one part may read standard input; got " + ", ".join(readers))


def build(items, *, parse_part, read_bytes, read_text, body=None,
          roots=None) -> list[dict] | None:
	"""The `parts` list for `content_spec`, in the order the options appeared.

	`parse_part` is the SEAM. It turns one `--part` value into
	`(content_type, source, disposition, name)` and is the only thing here
	that knows the spelling, so freezing that decision later changes one
	function rather than this contract.

	`read_bytes` and `read_text` are injected for the same reason the editor
	is injected elsewhere: this stays testable without a filesystem, and the
	CLI's existing reader keeps being the single place that knows what `-`
	means.
	"""
	from . import references as references_module

	if not items:
		return None

	# PARSE EVERYTHING FIRST, then check, then read. Three passes rather than
	# one, deliberately: a stdin collision has to be refused before any input
	# is consumed, and a diagnostic delivered after half a message has been
	# read is a diagnostic about a message that no longer exists.
	plan = []
	if body is not None:
		# FIRST, always. `--body` is not one of the ordered options -- it
		# cannot be repeated and has no position of its own -- so the only
		# stable place for it is the front, which is also where it sat in the
		# legacy body-plus-attachment shape. It joins the plan HERE, before the
		# stdin check, so `--body -` collides with `--references -` exactly the
		# way two parts do.
		source, content_type, disposition, part_name = body
		plan.append(("body", source, (content_type, disposition, part_name)))
	occurrence = 0
	for kind, value in items:
		if kind == "part":
			occurrence += 1
			# WHICH `--part`. With a repeatable option, "unknown field 'nope'"
			# on a command carrying four of them tells the human almost
			# nothing; the count is the only thing that distinguishes them,
			# since the value must not be echoed.
			content_type, source, disposition, name = parse_part(
				value, where=f"--part #{occurrence}")
			plan.append((kind, source, (content_type, disposition, name)))
		elif kind == "references":
			plan.append((kind, value, None))
		elif kind == "attach":
			plan.append((kind, None, value))
		else:
			raise BatonError(f"unknown content option {kind!r}")

	one_stdin([(kind, source) for kind, source, _ in plan if source is not None])

	out: list[dict] = []
	for kind, source, extra in plan:
		if kind == "body":
			content_type, disposition, part_name = extra
			# All three keys are passed even when None: the store defaults on
			# a None exactly as it does on an absent key, so this reproduces
			# the legacy single-leaf node rather than approximating it.
			out.append({"content_type": content_type, "disposition": disposition,
			            "part_name": part_name, "body": read_bytes(source)})
		elif kind == "part":
			content_type, disposition, name = extra
			node = {"content_type": content_type,
			        "disposition": disposition,
			        "body": read_bytes(source)}
			if name is not None:
				# Translated INWARD, and the translation is why the
				# protocol-10 rename cost this surface nothing.
				node["part_name"] = name
			out.append(node)
		elif kind == "references":
			out.append(references_module.part(read_text(source), roots=roots))
		else:
			# STOPGAP, not the fix. `normalize_parts` defaults an absent
			# content type to `text/markdown; charset=utf-8` for EVERY node,
			# including one carrying `attach` -- so the same file published
			# through the parts surface is declared text while the same file
			# through `send(attach=...)` is declared `application/octet-stream`.
			# Declaring it here makes the two CLI surfaces agree today.
			#
			# It fixes nothing: every other caller of the library's parts
			# surface still reaches the bug, and the real correction is for
			# `normalize_parts` to pick its default from the node. That is
			# recorded as a finding, which is where the correction lives.
			out.append({"attach": extra, "disposition": "attachment",
			            "content_type": DEFAULT_ATTACHMENT_TYPE})
	return out
