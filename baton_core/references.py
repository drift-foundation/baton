"""The references part: navigational metadata, validated.

When a message refers to repository files it carries a separate leaf listing
them, one ROOT-QUALIFIED POSIX path per line, ordered by first material
mention:

    content type   text/vnd.baton.references; charset=utf-8
    disposition    inline
    content        ROOT_ID:RELATIVE/POSIX/PATH per line

    source:baton_core/_impl.py
    source:README.md

THE ROOT IDENTIFIER IS REQUIRED. One Baton authority may coordinate several
repositories, so a bare `README.md` does not say whose README it is -- and the
convention's whole claim is that a reference resolves on the reader's machine
as well as the sender's. Root IDs are validated against the authority's own
configured roots, so a reference cannot name a repository the participants do
not share.

SAME ADDRESS, DIFFERENT PROMISE. An external attachment uses this same
`ROOT_ID:PATH` shape, and the alignment is deliberate -- one address vocabulary
rather than two. What the two do with it could not be more different:

    external part   resolves the root, READS the file, pins its bytes and
                    metadata, and may later fail verification
    reference       says where to look, and nothing else

Nothing here reads, stats, hashes or pins anything, and the path is not
required to exist. A path listed today may not exist yet, or may live in a
checkout the reader has and the sender does not. Checking would turn
navigational metadata into a weak pin, which is worse than either.

The convention itself is OPTIONAL, and is described as such in the mailbox
protocol document that ships beside this package: whether to send a references
part at all is the sender's business and nothing breaks if they do not.

What this module provides is the STRICT convenience. Reaching for it is a
request to be checked; a sender who deliberately wants an unvalidated
references-typed leaf can author one through the general part surface and get
no checking at all. That is the difference between a convenience and an alias.

Deliberately outside `_impl.py`. That file is the byte-copy the differential
oracle is measured against, and every line added to it makes the measurement
mean slightly less. This is a convention over the protocol rather than part of
it, so it lives beside it.

It also carries no reference to any host project's working documents: this
module ships inside the executable, and a shipped file pointing at a
particular repository's notes is not reusable by anyone else.
"""

from __future__ import annotations

from ._impl import ROOT_ID_RE, BatonError

CONTENT_TYPE = "text/vnd.baton.references; charset=utf-8"


def _refuse(line_number: int, line: str, why: str) -> BatonError:
	"""Name the line AND quote it. A validator that says only "invalid path"
	makes the human find it themselves, and they are looking at a list."""
	return BatonError(f"references line {line_number}: {why}: {line!r}")


def _check_relative(number: int, line: str, rel: str) -> None:
	"""The portability rules, applied to the part AFTER the root.

	Unchanged from when a reference was a bare path: the root says which
	repository, and these say the rest of the address means the same thing on
	both machines.
	"""
	if not rel:
		raise _refuse(number, line, "no path after the root identifier")
	if rel.strip() != rel:
		raise _refuse(number, line,
		              "leading or trailing whitespace: it may be part of the "
		              "filename or a mistake, and neither reading justifies "
		              "changing what you wrote")
	if "\\" in rel:
		raise _refuse(number, line, "use POSIX '/' separators")
	if rel.startswith("/"):
		raise _refuse(number, line,
		              "the path is relative to its root; drop the leading '/'")
	if rel.startswith("~"):
		raise _refuse(number, line, "home expansion is host-specific")
	components = rel.split("/")
	if any(part == ".." for part in components):
		raise _refuse(number, line, "'..' escapes the root")
	if any(part == "" for part in components):
		raise _refuse(number, line, "empty path component")


def normalize(text: str, *, roots=None) -> bytes:
	"""The validated bytes of a references leaf, or `BatonError`.

	`roots` is the authority's configured root IDs. When given, a reference
	naming a root the instance does not have is refused -- which is the point
	of requiring the root at all, since an address nobody can resolve is the
	thing this convention exists to prevent. When it is None the shape is still
	checked but membership is not, so the validator stays usable without an
	open instance.

	NOTHING IS REWRITTEN. Whitespace around a path is REFUSED rather than
	stripped: it is either part of a legal POSIX filename or an authoring
	mistake, and nothing here can tell which. Guessing between two readings and
	storing the guess is the one thing a validator must not do.

	Order is PRESERVED. "Ordered by first material mention" is the author's
	judgement about their own message; sorting would quietly discard it. A
	repeated address keeps its FIRST mention and the later one is dropped --
	refusing a whole message over a duplicate would be worse.
	"""
	if text is None:
		raise BatonError("references: no content")
	known = None if roots is None else {
		root["root_id"] if isinstance(root, dict) else root for root in roots}
	out: list[str] = []
	seen: set[str] = set()
	for number, line in enumerate(text.splitlines(), start=1):
		if not line:
			raise _refuse(number, line, "blank line")
		if not line.strip():
			# BEFORE the edge-whitespace check, which would otherwise catch
			# this first and describe it wrongly: a line of nothing but spaces
			# is not an address with untidy edges.
			raise _refuse(number, line, "whitespace-only line")
		if line.strip() != line:
			raise _refuse(number, line,
			              "leading or trailing whitespace: it may be part of "
			              "the filename or a mistake, and neither reading "
			              "justifies changing what you wrote")
		if line.startswith("#"):
			# A comment is not an address, and silently storing one would put
			# it in front of a reader as though it were.
			raise _refuse(number, line, "comments are not references")
		root_id, separator, rel = line.partition(":")
		if not separator:
			raise _refuse(number, line,
			              "a reference is ROOT_ID:RELATIVE/PATH; one authority "
			              "may coordinate several repositories, so a bare path "
			              "does not say which one owns it")
		if not ROOT_ID_RE.match(root_id) or len(root_id) > 64:
			# Also what refuses `C:/repo/file.md`: the grammar is lowercase, so
			# a Windows drive letter cannot be a root ID and needs no rule of
			# its own.
			raise _refuse(number, line, f"{root_id!r} is not a root identifier")
		if known is not None and root_id not in known:
			raise _refuse(
				number, line,
				f"no root {root_id!r} is configured on this instance; known "
				f"roots are {', '.join(sorted(known)) or '(none)'}")
		_check_relative(number, line, rel)
		if line in seen:
			continue
		seen.add(line)
		out.append(line)
	if not out:
		raise BatonError("references: no paths")
	return ("\n".join(out) + "\n").encode("utf-8")


def part(text: str, *, roots=None) -> dict:
	"""A references leaf, ready for `content_spec`'s `parts` list."""
	return {"content_type": CONTENT_TYPE,
	        "disposition": "inline",
	        "body": normalize(text, roots=roots)}
