"""Multipart authoring from the command line: order, stdin, vocabulary.

Deliberately spelling-independent. The `--part` value format is one escalated
decision; these pin the three properties that hold whichever way it is
written, and each is a property the obvious implementation gets wrong.
"""

from __future__ import annotations

import argparse

import pytest

from baton_core import BatonError, authoring


def _parser():
	"""A parser shaped like the real content options: three different flags,
	ONE ordered destination."""
	parser = argparse.ArgumentParser(exit_on_error=False)
	for flag, kind in (("--part", "part"), ("--attach", "attach"),
	                   ("--references", "references")):
		parser.add_argument(flag, dest="content", action=authoring.Collect,
		                    kind=kind, default=None)
	return parser


def _parse_part(value, *, where="--part"):
	"""A stand-in for the real descriptor. Deliberately trivial: the tests
	using it are about what happens AROUND the parse.

	It takes `where` because the seam does: the builder tells the parser which
	`--part` occurrence it is looking at, so a refusal can name it. A stand-in
	that did not accept it would be testing a different contract."""
	content_type, _, rest = value.partition("|")
	source, _, name = rest.partition("|")
	return content_type, source, "inline", (name or None)


# The authority's configured roots, as `store.list_roots()` returns them.
ROOTS = [{"root_id": "src", "path": "/anywhere"}]


def _build(namespace, files=None):
	files = files or {}
	return authoring.build(
		getattr(namespace, "content", None),
		roots=ROOTS,
		parse_part=_parse_part,
		read_bytes=lambda src: files.get(src, b"<" + src.encode() + b">"),
		read_text=lambda src: files.get(src, "src:a.md\n").decode()
		if isinstance(files.get(src, "src:a.md\n"), bytes) else files.get(src, "src:a.md\n"))


def _label(node):
	"""What a leaf IS, for order assertions.

	An earlier version of these assertions used `content_type or attach`,
	which read the attach node's ref only because that node happened to carry
	no content type. It now carries one, so the shorthand silently started
	labelling two different leaves the same way. Attach is checked FIRST here:
	an external leaf is identified by what it points at."""
	return node.get("attach") or node.get("content_type")


def test_occurrence_order_survives_across_different_options():
	"""The property argparse cannot express on its own.

	`--part a --attach b --part c` arrives from a normal parser as
	`parts=[a, c]`, `attach=[b]`, with the interleaving discarded. Leaf order
	is part of the manifest digest and the manifest is what retry compares, so
	losing it is not cosmetic."""
	ns = _parser().parse_args([
		"--part", "text/markdown; charset=utf-8|one.md",
		"--attach", "src:EVIDENCE.md",
		"--part", "text/plain; charset=utf-8|two.txt",
	])
	nodes = _build(ns)
	assert [_label(n) for n in nodes] == [
		"text/markdown; charset=utf-8", "src:EVIDENCE.md",
		"text/plain; charset=utf-8"]


def test_the_same_options_in_a_different_order_produce_a_different_message():
	"""Order is identity, so this must be observable rather than incidental."""
	first = _build(_parser().parse_args([
		"--part", "text/markdown; charset=utf-8|one.md", "--attach", "src:E.md"]))
	second = _build(_parser().parse_args([
		"--attach", "src:E.md", "--part", "text/markdown; charset=utf-8|one.md"]))
	assert [_label(n) for n in first] != [_label(n) for n in second]


def test_two_stdin_readers_are_refused_before_anything_is_read():
	"""A repeatable option makes `-` ambiguous in a way one `--body` never
	was: the second reader would silently get nothing.

	Refused BEFORE reading, which is what the injected reader proves — it
	fails the test if it is ever called."""
	def explode(_source):
		pytest.fail("input was read before the collision was refused")

	ns = _parser().parse_args([
		"--part", "text/markdown; charset=utf-8|-", "--part", "text/plain; charset=utf-8|-"])
	with pytest.raises(BatonError) as caught:
		authoring.build(ns.content, parse_part=_parse_part,
		                read_bytes=explode, read_text=explode)
	assert "only one part may read standard input" in str(caught.value)


def test_the_stdin_collision_is_counted_across_different_options_too():
	"""`--part -` beside `--references -` is the same collision. A per-option
	check would miss exactly the case a repeatable surface introduces."""
	ns = _parser().parse_args(["--part", "text/markdown; charset=utf-8|-", "--references", "-"])
	with pytest.raises(BatonError):
		authoring.build(ns.content, parse_part=_parse_part,
		                read_bytes=lambda s: b"", read_text=lambda s: "src:a.md\n")


def test_one_stdin_reader_is_fine():
	ns = _parser().parse_args(["--part", "text/markdown; charset=utf-8|-", "--part", "text/plain; charset=utf-8|b.txt"])
	nodes = _build(ns)
	assert len(nodes) == 2


def test_the_surface_says_name_and_the_storage_says_part_name():
	"""The rename has landed, and this surface did not move.

	It said `name` while protocol 9 stored `filename`, precisely so the
	protocol-10 rename would be a storage change rather than a user-visible
	one. The assertion below is the proof that it worked: the descriptor is
	unchanged and only the stored key moved."""
	ns = _parser().parse_args(["--part", "application/pdf|r.pdf|Q3 report.pdf"])
	node = _build(ns)[0]
	assert node["part_name"] == "Q3 report.pdf"
	assert "name" not in node, "the surface word leaked into the stored node"


def test_a_part_without_a_name_carries_no_filename_key_at_all():
	"""Absent is not the same as empty: the store defaults only when the key
	is missing."""
	ns = _parser().parse_args(["--part", "text/markdown; charset=utf-8|one.md"])
	assert "part_name" not in _build(ns)[0]


def test_a_references_option_produces_the_ruled_leaf():
	from baton_core import references
	ns = _parser().parse_args(["--references", "refs.txt"])
	node = _build(ns, files={"refs.txt": "src:a.md\nsrc:b.md\n"})[0]
	assert node["content_type"] == references.CONTENT_TYPE
	assert node["body"] == b"src:a.md\nsrc:b.md\n"


def test_an_invalid_reference_refuses_the_whole_command():
	"""Partial authoring is worse than none: a message that went without its
	references is a message that quietly says less than it meant to."""
	ns = _parser().parse_args([
		"--part", "text/markdown; charset=utf-8|one.md", "--references", "refs.txt"])
	with pytest.raises(BatonError) as caught:
		_build(ns, files={"refs.txt": "src:/etc/passwd\n"})
	assert "drop the leading '/'" in str(caught.value)


def test_no_content_options_means_no_parts_rather_than_an_empty_list():
	"""`None` and `[]` mean different things to `content_spec`: one is "the
	caller said nothing", the other is "the caller asked for zero parts"."""
	assert _build(_parser().parse_args([])) is None


def test_the_built_nodes_are_accepted_by_the_store_normalizer():
	"""The whole point of building this shape: it drops into the existing
	`content_spec` rather than becoming a second authoring path."""
	from baton_core import content_spec
	ns = _parser().parse_args([
		"--part", "text/markdown; charset=utf-8|one.md",
		"--part", "text/plain; charset=utf-8|two.txt|notes.txt"])
	container, nodes = content_spec(None, _build(ns))
	assert [n["content_type"] for n in nodes] == \
		["text/markdown; charset=utf-8", "text/plain; charset=utf-8"]
	assert nodes[1]["part_name"] == "notes.txt"
	assert container is not None, "several leaves need a container type"


# -- the ruled descriptor: URL-query named fields, RFC 3986 ---------------

from baton_core.authoring import parse_part  # noqa: E402


def test_the_ruled_example_parses():
	assert parse_part(
		"source=report.pdf&type=application/pdf"
		"&disposition=attachment&name=Q3-report.pdf") == (
		"application/pdf", "report.pdf", "attachment", "Q3-report.pdf")


def test_a_media_type_survives_without_encoding_its_own_equals():
	"""Pairs split at the FIRST `=`, which is what lets `charset=utf-8` travel
	unencoded. Without that rule every media type would need percent-escaping
	and the surface would be unreadable by hand."""
	assert parse_part("source=n.md&type=text/markdown;%20charset=utf-8")[0] == \
		"text/markdown; charset=utf-8"


def test_percent_encoding_is_accepted_for_the_same_type():
	"""Both spellings must mean the same thing, or the encoded form is a
	second dialect."""
	plain = parse_part("source=n.md&type=text/markdown;%20charset=utf-8")
	encoded = parse_part("source=n.md&type=text/markdown%3B%20charset%3Dutf-8")
	assert plain == encoded


def test_plus_is_a_literal_plus_and_not_a_space():
	"""The trap this ruling names explicitly. `urllib.parse.parse_qsl` and
	`unquote_plus` turn `+` into a space, which silently converts
	`application/ld+json` into an invalid media type — and the error then
	points at media-type validation rather than at the decoder."""
	assert parse_part("source=a.json&type=application/ld+json")[0] == \
		"application/ld+json"


def test_field_order_inside_one_descriptor_carries_no_meaning():
	a = parse_part("source=a.md&type=text/plain;%20charset=utf-8&name=x")
	b = parse_part("name=x&type=text/plain;%20charset=utf-8&source=a.md")
	assert a == b


@pytest.mark.parametrize("descriptor,fragment", [
	("type=a/b", "missing required field(s) source"),
	("source=a.md", "missing required field(s) type"),
	("source=a.md&type=a/b&type=c/d", "duplicate field 'type'"),
	("source=a.md&type=a/b&nope=1", "unknown field 'nope'"),
	("source=a.md&type=a/b&name=", "field 'name' is empty"),
	("source=&type=a/b", "field 'source' is empty"),
	("source=a.md&type=a/b&", "empty field"),
	("source&type=a/b", "has no value"),
	("source=%zz&type=a/b", "malformed percent escape"),
	("source=a%2&type=a/b", "malformed percent escape"),
])
def test_every_ruled_refusal_names_the_field(descriptor, fragment):
	with pytest.raises(BatonError) as caught:
		parse_part(descriptor)
	assert fragment in str(caught.value), str(caught.value)


def test_a_refusal_never_echoes_the_value():
	"""Ruled: diagnostics identify the occurrence and field without echoing
	arbitrary payload bytes. A descriptor can carry a path or media type from
	anywhere, and quoting it back puts unreviewed bytes in front of whoever is
	reading the terminal."""
	secret = "s3cret-looking-value-nobody-should-see"
	with pytest.raises(BatonError) as caught:
		parse_part(f"source={secret}&type=a/b&unknown={secret}")
	assert secret not in str(caught.value), str(caught.value)


def test_disposition_defaults_to_inline_and_name_to_absent():
	content_type, source, disposition, name = parse_part("source=a.md&type=a/b")
	assert disposition == "inline"
	assert name is None


def test_the_ruled_parser_drops_into_the_builder_unchanged():
	"""The seam closing: `parse_part` is what `build` was written against, so
	wiring it should require nothing but passing it."""
	ns = _parser().parse_args([
		"--part", "source=one.md&type=text/markdown;%20charset=utf-8",
		"--attach", "src:E.md",
		"--part", "source=two.pdf&type=application/pdf"
		          "&disposition=attachment&name=Report.pdf",
	])
	nodes = authoring.build(ns.content, parse_part=parse_part,
	                        read_bytes=lambda s: b"<bytes>",
	                        read_text=lambda s: "src:a.md\n")
	assert [_label(n) for n in nodes] == [
		"text/markdown; charset=utf-8", "src:E.md", "application/pdf"]
	assert nodes[2]["part_name"] == "Report.pdf"
	assert nodes[2]["disposition"] == "attachment"


def test_an_encoded_key_is_the_same_key_and_cannot_evade_the_duplicate_check():
	"""Keys are decoded BEFORE duplicates are detected. Otherwise `%74ype` is
	a stranger to `type` and slips past as an unknown field — the same mistake
	reported as a different error, and only by luck a refusal at all."""
	assert parse_part("%73ource=a.md&type=a/b")[1] == "a.md"
	with pytest.raises(BatonError) as caught:
		parse_part("source=a.md&type=a/b&%74ype=c/d")
	assert "duplicate field 'type'" in str(caught.value)


def test_percent_bytes_that_are_not_utf8_are_refused_not_replaced():
	"""`unquote` defaults to `errors="replace"`, so `%FF` silently becomes
	U+FFFD and a path or media type quietly turns into a different string.
	Decoded strictly instead."""
	with pytest.raises(BatonError) as caught:
		parse_part("source=%FF&type=a/b")
	message = str(caught.value)
	assert "not valid UTF-8" in message, message
	assert "�" not in message, "the replacement character reached the message"


def test_a_valid_multibyte_path_still_travels():
	"""Strictness is about invalid bytes, not about non-ASCII."""
	assert parse_part("source=notes-%C3%A9.md&type=a/b")[1] == "notes-é.md"


def test_a_field_name_with_surrounding_whitespace_is_refused_not_repaired():
	"""An earlier version `strip()`ped the key, which silently accepted
	` type=` and made a field name the author did not write. Same reasoning as
	reference paths: repairing input is deciding what someone meant.

	Only the ENCODED case reaches this check now. A raw space anywhere in a
	descriptor is refused earlier and more strictly, by the query-charset gate,
	because a descriptor is an RFC 3986 query and a raw space is not query-legal
	wherever it appears. Both raw spellings are still pinned as refused — what
	changed is which rule catches them, and being caught sooner by a broader
	rule is not a weaker guarantee.
	"""
	with pytest.raises(BatonError) as caught:
		parse_part("%20type=a/b&source=a.md")
	assert "field name has surrounding whitespace" in str(caught.value)
	for raw in (" type=a/b&source=a.md", "type =a/b&source=a.md"):
		with pytest.raises(BatonError) as caught:
			parse_part(raw)
		assert "RFC 3986 query" in str(caught.value)


@pytest.mark.parametrize("value", ["inline", "attachment"])
def test_both_allowed_dispositions_pass(value):
	assert parse_part(f"source=a.md&type=a/b&disposition={value}")[2] == value


def test_any_other_disposition_is_refused_at_the_parser():
	"""Refused here rather than by the store's normalizer, which would
	diagnose it out of context — the human typed a `--part` field and should
	be told which field, in a message about the command they ran."""
	with pytest.raises(BatonError) as caught:
		parse_part("source=a.md&type=a/b&disposition=sideways")
	message = str(caught.value)
	assert "disposition must be one of inline, attachment" in message
	assert "sideways" not in message, "the value was echoed"


@pytest.mark.parametrize("descriptor", [
	"source=%FF&type=a/b",            # invalid lead byte
	"source=%C3%28&type=a/b",         # invalid continuation
	"source=%C3&type=a/b",            # truncated multibyte
])
def test_every_shape_of_invalid_utf8_is_refused(descriptor):
	"""Three distinct decoder failures, not one. `errors="strict"` catches
	all three; `errors="replace"` — the default — catches none."""
	with pytest.raises(BatonError) as caught:
		parse_part(descriptor)
	assert "not valid UTF-8" in str(caught.value)


def test_the_diagnostic_names_WHICH_part_when_several_are_given():
	"""With a repeatable option, "unknown field" on a command carrying four
	parts tells the human almost nothing — and the value must not be echoed,
	so the occurrence count is the only thing left to distinguish them."""
	ns = _parser().parse_args([
		"--part", "source=one.md&type=text/plain;%20charset=utf-8",
		"--part", "source=two.md&type=text/plain;%20charset=utf-8",
		"--part", "source=three.md&type=text/plain;%20charset=utf-8&nope=1",
	])
	with pytest.raises(BatonError) as caught:
		authoring.build(ns.content, parse_part=parse_part,
		                read_bytes=lambda s: b"", read_text=lambda s: "src:a.md\n")
	message = str(caught.value)
	assert "--part #3" in message, message
	assert "unknown field 'nope'" in message, message
	assert "three.md" not in message, "the value was echoed"


def test_invalid_utf8_in_a_KEY_is_refused_too():
	"""Keys go through the same decoder as values. Pinned separately because
	a key is validated on a different code path from a value, and "it uses the
	same function" is an implementation claim rather than a behavioural one."""
	with pytest.raises(BatonError) as caught:
		parse_part("%FFkey=a&source=b.md&type=a/b")
	message = str(caught.value)
	assert "field name" in message, message
	assert "not valid UTF-8" in message, message


def test_a_malformed_escape_in_a_KEY_is_refused_too():
	with pytest.raises(BatonError) as caught:
		parse_part("%zzkey=a&source=b.md&type=a/b")
	assert "malformed percent escape" in str(caught.value)


def test_the_authoring_layer_no_longer_declares_the_attachment_type():
	"""REPLACED the stopgap test, which said out loud that it should be.

	The old test pinned `authoring` declaring `application/octet-stream`
	itself, because `normalize_parts` defaulted EVERY untyped node to markdown
	and only this one caller was patched around it. Its docstring said: "If
	that lands and this line is removed, this test is what says so out loud."
	It landed, and this is that.

	Now the authoring layer declares NOTHING, and the type arrives from the
	store's general rule. Asserting the absence is the point: if a future edit
	re-adds an explicit type here, it would mask a regression in that rule
	from every test that goes through the CLI."""
	nodes = _build(_parser().parse_args(
		["--attach", "src:report.pdf", "--part", "text/plain; charset=utf-8|a.txt"]))
	assert "content_type" not in nodes[0], \
		"the authoring layer is declaring a type the store should choose"
	assert nodes[0]["disposition"] == "attachment"


def test_the_store_defaults_an_untyped_attachment_to_binary():
	"""The correction itself, at the layer that owns it.

	Reached through the general parts surface -- the one every multipart
	caller must use -- rather than the `send(attach=...)` convenience path
	that always had the right default."""
	from baton_core._impl import DEFAULT_ATTACHMENT_TYPE, content_spec
	_container, nodes = content_spec(
		None, [{"attach": "r:report.pdf", "disposition": "attachment"}])
	assert nodes[0]["content_type"] == DEFAULT_ATTACHMENT_TYPE


def test_an_explicit_type_still_wins_over_the_attachment_default():
	"""The default is a default. A caller who names `application/pdf` gets it,
	which is what makes the rule a fallback rather than a coercion."""
	from baton_core._impl import content_spec
	_container, nodes = content_spec(
		None, [{"attach": "r:report.pdf", "disposition": "attachment",
		        "content_type": "application/pdf"}])
	assert nodes[0]["content_type"] == "application/pdf"


def test_an_inline_leaf_still_defaults_to_markdown():
	"""The other half: the fix chooses per node, so it must not have moved the
	INLINE default with it."""
	from baton_core._impl import DEFAULT_CONTENT_TYPE, content_spec
	_container, nodes = content_spec(b"hello\n", None)
	assert nodes[0]["content_type"] == DEFAULT_CONTENT_TYPE


def test_the_two_cli_attachment_surfaces_agree_on_the_default_type():
	"""One file, two spellings, one declared type -- measured AFTER
	normalization, which is where the type is now decided.

	This assertion used to read the authoring layer's output, because that
	layer declared the type itself. It no longer does, so checking it there
	would only confirm that the workaround is gone. Both spellings are now put
	through `content_spec`, which is what the store actually stores, and the
	expected value is read from the module rather than repeated."""
	from baton_core._impl import DEFAULT_ATTACHMENT_TYPE, content_spec
	authored = _build(_parser().parse_args(
		["--attach", "src:report.pdf", "--references", "refs.txt"]))
	_c, parts_path = content_spec(None, authored)
	# The convenience spelling: one attachment, no parts list.
	_c2, convenience_path = content_spec(
		None, [{"attach": "src:report.pdf", "disposition": "attachment"}])
	assert parts_path[0]["content_type"] == DEFAULT_ATTACHMENT_TYPE
	assert convenience_path[0]["content_type"] == DEFAULT_ATTACHMENT_TYPE


# -- `--body` in part mode: the data-loss regression -----------------------

def _build_with_body(namespace, body, files=None):
	files = files or {}
	return authoring.build(
		getattr(namespace, "content", None), body=body, roots=ROOTS,
		parse_part=_parse_part,
		read_bytes=lambda src: files.get(src, b"<" + src.encode() + b">"),
		read_text=lambda src: files.get(src, "src:a.md\n"))


def test_a_body_beside_references_is_the_first_leaf_rather_than_dropped():
	"""THE REGRESSION. An earlier version entered part mode on `--part` or
	`--references` and passed `body=None` from there, so

	    send --body notes.md --references refs.txt

	exited zero having published only the references leaf. A command that
	succeeds while discarding content the caller named is worse than one that
	fails, and no test here caught it -- review did."""
	ns = _parser().parse_args(["--references", "refs.txt"])
	nodes = _build_with_body(ns, ("notes.md", None, None, None),
	                         files={"notes.md": b"BODY MUST SURVIVE"})
	assert nodes[0]["body"] == b"BODY MUST SURVIVE"
	assert len(nodes) == 2


def test_the_body_leads_even_when_its_option_came_last():
	"""`--body` is not one of the ordered options -- it cannot repeat and has
	no position of its own -- so the only stable place for it is the front,
	which is also where it sat in the legacy body-plus-attachment shape."""
	ns = _parser().parse_args(["--attach", "src:E.md", "--references", "refs.txt"])
	nodes = _build_with_body(ns, ("notes.md", None, None, None))
	assert nodes[0].get("body") is not None
	assert [_label(n) for n in nodes[1:]] == [
		"src:E.md", "text/vnd.baton.references; charset=utf-8"]


def test_the_legacy_body_keeps_its_legacy_metadata():
	"""`--content-type`/`--disposition`/`--part-name` have always described the
	body. They keep describing it, rather than being silently ignored because
	another option happened to appear."""
	ns = _parser().parse_args(["--references", "refs.txt"])
	nodes = _build_with_body(
		ns, ("notes.txt", "text/plain; charset=utf-8", "attachment", "notes.txt"))
	assert nodes[0]["content_type"] == "text/plain; charset=utf-8"
	assert nodes[0]["disposition"] == "attachment"
	assert nodes[0]["part_name"] == "notes.txt"


def test_an_undescribed_body_passes_none_so_the_store_still_defaults():
	"""The legacy node passed all three keys as None and let the store default
	on them. Reproduced exactly rather than approximated, or a body authored
	beside a references leaf would get a different type from the same command
	without one."""
	ns = _parser().parse_args(["--references", "refs.txt"])
	node = _build_with_body(ns, ("notes.md", None, None, None))[0]
	assert node["content_type"] is None
	assert node["disposition"] is None
	assert node["part_name"] is None


def test_a_body_reading_stdin_collides_with_a_part_reading_stdin():
	"""The body joins the plan BEFORE the collision check, so `--body -` is
	counted like any other source. It would otherwise be the one reader the
	check could not see."""
	def explode(_source):
		pytest.fail("input was read before the collision was refused")

	ns = _parser().parse_args(["--references", "-"])
	with pytest.raises(BatonError) as caught:
		authoring.build(ns.content, body=("-", None, None, None),
		                parse_part=_parse_part, read_bytes=explode, read_text=explode)
	assert "only one part may read standard input" in str(caught.value)


# -- the descriptor is an RFC 3986 query -----------------------------------

def test_a_percent_encoded_space_is_how_a_media_type_parameter_travels():
	assert parse_part("source=a.md&type=text/markdown;%20charset=utf-8")[0] == \
		"text/markdown; charset=utf-8"


def test_percent_encoded_utf8_travels_and_decodes():
	assert parse_part("source=notes-%C3%A9.md&type=text/plain")[1] == "notes-\u00e9.md"


@pytest.mark.parametrize("value,why", [
	("source=a.md&type=text/markdown; charset=utf-8", "raw whitespace"),
	("source=notes-\u00e9.md&type=text/plain", "non-ASCII"),
	("source=a\tb.md&type=text/plain", "raw whitespace"),
	("source=a\x01b.md&type=text/plain", "control character"),
	("source=a<b>.md&type=text/plain", "not permitted in a URL query"),
])
def test_a_descriptor_that_is_not_a_query_is_refused(value, why):
	"""Accepting the raw forms would make one descriptor mean different things
	depending on the shell, locale and terminal encoding it travelled
	through."""
	with pytest.raises(BatonError) as caught:
		parse_part(value)
	assert why in str(caught.value)


def test_the_charset_refusal_names_a_position_and_not_the_text():
	"""A descriptor can carry a path from anywhere. The position is enough to
	find the character; echoing the value would put unreviewed bytes on the
	terminal."""
	with pytest.raises(BatonError) as caught:
		parse_part("source=secret path.md&type=text/plain", where="--part #2")
	message = str(caught.value)
	assert "--part #2" in message
	assert "position" in message
	assert "secret" not in message


@pytest.mark.parametrize("value", [
	"source=a.md&type=application/ld+json",       # literal + survives
	"source=dir/sub/a.md&type=text/plain",        # / travels
	"source=a.md&type=text/plain;%20charset=utf-8",
	"source=a:b.md&type=text/plain",              # : is legal in a query
])
def test_what_the_charset_gate_must_not_break(value):
	assert parse_part(value)[1]
