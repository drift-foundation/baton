"""The references CONVENIENCE, and what it checks.

The convention itself is not enforced and these tests do not claim it is:
nothing requires a sender to carry a references leaf, and `--part` will
publish a references-typed leaf with no checking at all. What is pinned here
is the behaviour of the optional convenience — reaching for it is a request to
be checked, which is the difference between a convenience and an alias.

`docs/AGENTS-MAILBOX-PROTO.md`, section "File references travel as their own
part", says a reference that resolves on only one machine is not a reference.
These pin that sentence where the convenience applies it: what travels, what
is refused, and — the part that is easy to get wrong — what is deliberately
NOT checked.

(That sentence used to be cited from the ephemeral finding folder where it was
first written, which has since been removed. A permanent test citing a path
designed to disappear is the same mistake as a permanent test READING one, one
step less severe: the rule's durable owner is the protocol document, and that
is what this now names.)

(This header previously said the convention was "enforced rather than
described", which contradicted the implemented split and the module it tests.
If Slawomir's pending convention ruling goes the other way, this moves with
`references.py` rather than being corrected separately.)
"""

from __future__ import annotations

import pytest

from baton_core import BatonError
from baton_core import references

# The authority's configured roots, as `store.list_roots()` returns them.
ROOTS = [{"root_id": "src", "path": "/anywhere"}]


def test_a_plain_list_travels_unchanged_and_keeps_its_order():
	"""The finding says "ordered by first material mention". That is the
	author's judgement about their own message; sorting would discard it."""
	text = "src:baton_core/_impl.py\nsrc:README.md\nsrc:notes/NOTE.md\n"
	assert references.normalize(text, roots=ROOTS) == text.encode()


def test_the_usual_terminal_newline_is_accepted():
	"""And needs no special handling at all: `splitlines()` does not return
	an empty record for it. `"a.md\n"` is `["a.md"]`."""
	assert references.normalize("src:a.md\n", roots=ROOTS) == b"src:a.md\n"
	assert references.normalize("src:a.md", roots=ROOTS) == b"src:a.md\n"


def test_an_internal_blank_line_is_refused_by_number():
	"""SUPERSEDED: this file first DROPPED blank lines, reasoning that a
	trailing newline is how text files end. That conflated two things —
	the terminal newline produces no empty record, so accepting it never
	required dropping anything, and an internal blank is a real one."""
	with pytest.raises(BatonError) as caught:
		references.normalize("src:a.md\n\nsrc:b.md\n", roots=ROOTS)
	assert "blank line" in str(caught.value)
	assert "line 2" in str(caught.value)


@pytest.mark.parametrize("line", [" src:a.md", "src:a.md ", "\tsrc:a.md", "src:a.md\t"])
def test_surrounding_whitespace_is_refused_rather_than_stripped(line):
	"""Stripping produces a DIFFERENT reference. Edge whitespace may be part
	of a legal POSIX filename or an authoring mistake, and nothing here can
	tell which — so it is REFUSED rather than guessed at. Interior whitespace
	is a separate case and travels; see below."""
	with pytest.raises(BatonError) as caught:
		references.normalize("src:first.md\n" + line + "\n", roots=ROOTS)
	message = str(caught.value)
	assert "whitespace" in message, message
	assert "line 2" in message, message


def test_a_path_that_legitimately_contains_a_space_travels():
	"""The rule is about the EDGES, where the ambiguity is. Interior
	whitespace is unambiguous and is left alone."""
	assert references.normalize("src:dir/my notes.md\n", roots=ROOTS) == b"src:dir/my notes.md\n"


@pytest.mark.parametrize("line", ["   ", "\t", " \t "])
def test_a_whitespace_only_line_gets_its_own_diagnostic(line):
	"""It is not a path with untidy edges, and calling it one would send the
	author looking for a filename that is not there. Ordered before the
	edge-whitespace check, which would otherwise catch it first."""
	with pytest.raises(BatonError) as caught:
		references.normalize("src:first.md\n" + line + "\n", roots=ROOTS)
	assert "whitespace-only line" in str(caught.value)
	assert "line 2" in str(caught.value)


def test_a_repeated_path_keeps_only_its_first_mention():
	"""Not an error: refusing a whole message over a duplicate is worse than
	dropping it, and the ordering rule is about FIRST mention."""
	assert references.normalize("src:a.md\nsrc:b.md\nsrc:a.md\n", roots=ROOTS) == b"src:a.md\nsrc:b.md\n"


@pytest.mark.parametrize("line,fragment", [
	("src:/etc/passwd", "drop the leading '/'"),
	("src:~/notes.md", "home expansion is host-specific"),
	("src:../outside/x.md", "'..' escapes the root"),
	("src:a/../../x.md", "'..' escapes the root"),
	("src:a//b.md", "empty path component"),
	("src:dir\\file.md", "use POSIX '/' separators"),
	("# a comment", "comments are not references"),
	("README.md", "ROOT_ID:RELATIVE/PATH"),
	("C:/repo/f.md", "is not a root identifier"),
	("nope:a.md", "no root 'nope' is configured"),
	("src:", "no path after the root identifier"),
])
def test_what_cannot_travel_is_refused_and_the_line_is_named(line, fragment):
	"""Each refusal names the line NUMBER and quotes it: a validator that says
	only "invalid path" makes the human search a list they are already
	looking at."""
	with pytest.raises(BatonError) as caught:
		references.normalize("src:first.md\n" + line + "\nsrc:last.md\n", roots=ROOTS)
	message = str(caught.value)
	assert fragment in message, message
	assert "line 2" in message, message
	assert repr(line) in message or line in message, message


def test_an_empty_list_is_an_error_rather_than_an_empty_part():
	"""An empty references leaf says "here are the files" and then names
	none, which is worse than not sending one."""
	for text in ("", "\n\n\n", "   \n"):
		with pytest.raises(BatonError):
			references.normalize(text, roots=ROOTS)


def test_nothing_touches_the_filesystem(tmp_path, monkeypatch):
	"""The property that keeps a reference a reference.

	A path listed today may not exist yet, or may live in a repository the
	reader has and the sender does not. Checking would turn navigational
	metadata into a weak pin — worse than both the pin and the reference,
	because it fails on the sender's machine for the reader's reasons.

	Asserted by making every filesystem entry point explode."""
	import os
	for name in ("stat", "lstat", "open", "listdir", "access", "readlink"):
		monkeypatch.setattr(os, name, lambda *a, **k: pytest.fail(
			f"references touched the filesystem via os.{name}"))
	monkeypatch.setattr("os.path.exists",
	                    lambda *a, **k: pytest.fail("references called os.path.exists"))
	assert references.normalize("src:does/not/exist.md\n", roots=ROOTS) == b"src:does/not/exist.md\n"


def test_the_part_carries_the_ruled_type_and_disposition():
	node = references.part("src:a.md\n", roots=ROOTS)
	assert node["content_type"] == "text/vnd.baton.references; charset=utf-8"
	assert node["disposition"] == "inline"
	assert node["body"] == b"src:a.md\n"


def test_the_part_is_shaped_for_the_general_parts_list():
	"""It has to drop straight into `content_spec`'s `parts`, or the CLI ends
	up with a second authoring path for one leaf."""
	from baton_core import content_spec
	container, nodes = content_spec(None, [references.part("src:a.md\n", roots=ROOTS)])
	assert len(nodes) == 1
	assert nodes[0]["content_type"] == references.CONTENT_TYPE
	assert nodes[0]["body"] == b"src:a.md\n"


def test_without_the_authority_the_shape_is_still_checked():
	"""`roots=None` means "no instance to ask", not "anything goes".

	The membership check needs the authority; the grammar does not. Keeping
	them separable is what lets the validator be used and tested without an
	open instance — and stops a missing argument from silently disabling the
	whole check."""
	assert references.normalize("anything:a.md\n") == b"anything:a.md\n"
	for bad in ("README.md\n", "src:../x.md\n", "C:/repo/f.md\n"):
		with pytest.raises(BatonError):
			references.normalize(bad)


def test_the_reference_address_is_the_attachment_address():
	"""Deliberate: one address vocabulary, not two. `--attach src:q3/led.csv`
	and a reference to `src:q3/led.csv` name the same file the same way.

	What differs is the promise, and that is asserted next door — an external
	part reads and pins those bytes, a reference touches nothing and does not
	require them to exist."""
	from baton_core._impl import _normalize_attach_ref
	address = "src:q3/ledger.csv"
	pinned = _normalize_attach_ref(address, "content[0]")
	assert (pinned["root_id"], pinned["path"]) == ("src", "q3/ledger.csv")
	assert references.normalize(address + "\n", roots=ROOTS) == \
		(address + "\n").encode()
