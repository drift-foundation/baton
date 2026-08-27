"""W24755: the portable Graphviz DOT renderer for the Work graph.

PURE. This module holds no authority handle, opens no file, imports no
Graphviz, and starts no subprocess. It turns one already-built envelope into
one UTF-8 string. Baton emits DOT; it never renders an image and never needs
the Graphviz runtime to be installed.

SEPARATE FROM THE PROJECTION ON PURPOSE. `projection.work_graph` is structured
data suitable for graph analysis or another textual renderer later; DOT is an
export format and not protocol state. Because they are two boundaries, this one
VALIDATES ITS INPUT rather than trusting that the projection built it -- a
renderer that assumed a well-formed envelope would be a renderer that emits
malformed DOT the moment anything else calls it.

Review [P1] found that sentence was a CLAIM this module did not keep: it owned
container shapes and the relation enum, and nothing else, so a structured
caller could obtain a complete-looking document carrying a duplicate edge, a
dangling endpoint or a forged predicate. It now runs
`projection.validate_work_graph` -- the same function the projection runs, not
a second statement of the same rules -- over its whole input before composing
any statement. One enforcement on every renderer input.

NON-`strict`, ALWAYS. Graphviz's `strict` merges parallel edges sharing a tail
and head, and two Works may simultaneously hold dependency, containment,
follow-up and duplicate relations. A `strict` digraph would silently collapse
four true relationships into one and apply the last one's attributes to it,
which is the export losing exactly the information it exists to carry.

SEMANTICS IN TEXT, NEVER IN STYLE. No colour, rank, cluster, shape or line
style carries Baton meaning. Every relation spells itself in `label` and in
`baton_*` attributes, so the export is readable by a person, by a graph tool
that ignores unknown attributes, and by a parser -- none of which agree about
how to interpret a colour.
"""

from __future__ import annotations

import base64
import unicodedata

from baton_work.authority import WorkError
from baton_work.projection import (GRAPH_NODE_MEMBERS, GRAPH_RELATIONS,
                                   validate_work_graph)

# The format's own version, independent of the projection version. A consumer
# reads this to know the shape of the document rather than the shape of the
# JSON that produced it.
DOT_VERSION = "1"

# `*` is the value that means "no filter", chosen because a configured team
# handle can never be `*` and an absent attribute would be indistinguishable
# from a renderer that forgot to emit it.
UNFILTERED = "*"


def _visible(text: str) -> str:
	"""Make control and format code points VISIBLE rather than active.

	A raw newline, carriage return, NUL, tab or bidirectional override inside a
	title is the difference between one node statement and a DOT document whose
	structure the title decided. Each becomes `<U+XXXX>`, which is ordinary
	text inside a quoted string -- this is never an HTML-like label, so `<` and
	`>` carry no syntax here.

	Zl and Zp are included with Cc/Cf because U+2028 and U+2029 ARE line
	breaks to a good many consumers even though Unicode files them under
	separators, and a label that can be split is a label that can be escaped
	from. Cs and Co are included because a lone surrogate or a private-use code
	point has no agreed rendering and should not be passed through silently.

	A title that already contains the literal text `<U+0009>` is emitted
	unchanged and is therefore indistinguishable HERE from a real tab. That is
	deliberate and harmless: `baton_title_b64` carries the exact bytes, so the
	label is the readable approximation and the base64 is the truth.
	"""
	out = []
	for char in text:
		if unicodedata.category(char) in ("Cc", "Cf", "Cs", "Co", "Zl", "Zp"):
			out.append(f"<U+{ord(char):04X}>")
		else:
			# PRINTABLE UNICODE PASSES THROUGH UNCHANGED. The document
			# declares `charset="UTF-8"`, which is also DOT's default, so a
			# CJK or accented title is emitted as itself rather than escaped
			# into unreadability.
			out.append(char)
	return "".join(out)


def _quoted(value: str) -> str:
	"""One DOT double-quoted string, safe for identifiers and values alike.

	EVERY QUOTED VALUE IN THE DOCUMENT PASSES THROUGH HERE, and that is why
	the visibility substitution is applied HERE rather than at the label. My
	first version guarded `label` alone, so a title carrying a raw tab, NUL or
	newline reached `baton_title` unaltered -- one attribute of one statement
	still able to put a control character into the document, which is the
	whole class of defect the label guard existed to close. A rule that has to
	be remembered at each call site is a rule that will be forgotten at one of
	them, so there is one owner and every value goes through it.

	It is idempotent, so a caller that has already made text visible is not
	punished for it: `<U+0009>` contains no control characters of its own.

	THE BACKSLASH IS PROTECTED FIRST, and that ordering is the whole point.
	Graphviz label values are `escString`s: `\\N`, `\\G`, `\\E`, `\\T`, `\\H`,
	`\\L`, `\\n`, `\\l` and `\\r` are SUBSTITUTIONS, not literals. A title
	containing `\\N` would otherwise be replaced by the node's name at render
	time -- so every user backslash is doubled before anything else, which
	makes each of those sequences render as the two characters the author
	typed.

	Escaping `"` afterwards cannot re-introduce the problem, because the
	backslash it adds is one this function put there.
	"""
	if not isinstance(value, str):
		raise WorkError(f"a DOT value is text; this is {value!r}")
	value = _visible(value)
	return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _assignments(pairs: dict) -> list[str]:
	"""`name="value"` for each pair, LEXICOGRAPHIC BY NAME.

	Sorted rather than emitted in insertion order so the bytes cannot depend
	on how the mapping was built -- which is the kind of accidental ordering
	that makes two runs of an unchanged snapshot differ.

	ONE OWNER FOR BOTH KINDS OF LIST, and the mutation pass is why. The graph
	attribute block used to call `sorted` separately, and because that dict's
	literal happened to be written in sorted order already, removing the call
	changed no byte and no case could see it -- a guard nothing observes. It is
	the same rule in both places, so it is now the same code in both places,
	and the cases that hold the bracketed lists hold the graph block too.
	"""
	return [f"{name}={_quoted(value)}" for name, value in sorted(pairs.items())]


def _attributes(pairs: dict) -> str:
	"""One bracketed attribute list, for a node or an edge statement."""
	return "[" + ", ".join(_assignments(pairs)) + "]"


def _text(value) -> str:
	"""One structured member as the string DOT carries.

	`None` becomes the literal `null` rather than an empty string or an absent
	attribute: an absent attribute is indistinguishable from a renderer that
	dropped it, and `""` is indistinguishable from a genuinely empty value.
	`True`/`False` become `true`/`false` rather than Python's capitalized
	spelling, because this document is read by tools that are not Python.
	"""
	if value is None:
		return "null"
	if value is True:
		return "true"
	if value is False:
		return "false"
	return str(value)


def _envelope(envelope) -> tuple[dict, dict]:
	"""Own the input at this boundary, before a single byte is composed."""
	if not isinstance(envelope, dict):
		raise WorkError(f"a DOT export renders one envelope; this is "
		                f"{envelope!r}")
	missing = [name for name in ("authority_uuid", "projection_version",
	                             "protocol_version", "snapshot_seq", "result")
	           if name not in envelope]
	if missing:
		raise WorkError(f"the envelope to render needs "
		                f"{', '.join(missing)}")
	result = envelope["result"]
	if not isinstance(result, dict):
		raise WorkError(f"a Work-graph result is a document; this is "
		                f"{result!r}")
	for name in ("scope", "counts", "nodes", "edges"):
		if name not in result:
			raise WorkError(f"a Work-graph result needs {name}")
	for name, kind in (("nodes", list), ("edges", list), ("scope", dict)):
		if not isinstance(result[name], kind):
			raise WorkError(f"a Work-graph {name} is a {kind.__name__}; this "
			                f"is {result[name]!r}")
	return envelope, result


def _node_statement(node: dict) -> str:
	# BOTH SPELLINGS OF `selected`, and review [P1] is why. I read
	# `scope=selected|context` and "a baton_* per structured node member" as
	# competing instructions and picked the more specific one -- but they are
	# COMPLEMENTARY: one is the readable role a person and a graph tool see,
	# the other is the projection's exact boolean a consumer round-trips.
	# Emitting both costs one attribute and removes a format-specific reverse
	# mapping from every reader.
	scope = "selected" if node["selected"] else "context"
	# The readable line, single by construction: every code point that could
	# break it is already `<U+XXXX>` above.
	standing = _text(node["phase"] if node["status"] == "open"
	                 else node["outcome"])
	label = (f"{node['local_id']} | {node['team']} | "
	         f"{node['status']}/{standing} | {scope} | {node['title']}")
	attributes = {
		"label": label,
		"baton_scope": scope,
		# THE EXACT TITLE, INDEPENDENT OF EVERY OTHER SPELLING OF IT. Both
		# `label` and `baton_title` are readable approximations and both are
		# lossy on purpose, because both go through the visibility rule. This
		# is the byte-for-byte original, so a consumer that needs the true
		# title never has to reverse a substitution -- and base64 is chosen
		# precisely because its alphabet cannot itself need escaping.
		"baton_title_b64": base64.b64encode(
			node["title"].encode("utf-8")).decode("ascii"),
		"baton_title_encoding": "base64-utf8",
	}
	for name in GRAPH_NODE_MEMBERS:
		attributes[f"baton_{name}"] = _text(node[name])
	return f"\t{_quoted(node['id'])} {_attributes(attributes)}"


def _edge_statement(edge: dict) -> str:
	attributes = {
		# The relation is readable WITHOUT colour, style or layout: a person
		# looking at a rendered graph and a parser reading the source get the
		# same two words.
		"label": f"{edge['relation']}: {edge['predicate']}",
		"baton_relation": _text(edge["relation"]),
		"baton_predicate": _text(edge["predicate"]),
		"baton_relation_seq": _text(edge["relation_seq"]),
		"baton_via_obligation": _text(edge["via_obligation"]),
	}
	return (f"\t{_quoted(edge['source'])} -> {_quoted(edge['target'])} "
	        f"{_attributes(attributes)}")


def render_work_graph_dot(envelope) -> str:
	"""One complete DOT document, composed and validated entirely in memory.

	THE WHOLE TEXT IS BUILT BEFORE THE CALLER CAN WRITE ANY OF IT. An
	application refusal therefore cannot leave a syntactically plausible
	partial graph on the operator's terminal or in their redirect target -- a
	half-written digraph that happens to parse is worse than no file, because
	it is a complete-looking answer to a question that was never answered.

	NOTHING IN THE OUTPUT DEPENDS ON WHO ASKED OR WHEN. No generated-at
	instant, participant, config path, working directory or random value. One
	authority, one snapshot and one scope therefore yield byte-identical DOT
	for every authorized participant, which is what makes the export
	diffable and checksummable.
	"""
	envelope, result = _envelope(envelope)
	scope = result["scope"]
	for name in ("team", "status", "changed_from", "changed_until"):
		if name not in scope:
			raise WorkError(f"a Work-graph scope needs {name}")
	graph = {
		"baton_authority_uuid": _text(envelope["authority_uuid"]),
		"baton_dot_version": DOT_VERSION,
		"baton_projection_version": _text(envelope["projection_version"]),
		"baton_protocol_version": _text(envelope["protocol_version"]),
		# THE WHOLE SCOPE, INCLUDING THE INTERVAL. The determinism promise is
		# that one authority, snapshot and SCOPE give one document -- so a
		# scope operand the document did not spell would let two different
		# questions produce identical bytes, and a reader could not tell which
		# one they were holding.
		"baton_scope_changed_from": scope["changed_from"] or UNFILTERED,
		"baton_scope_changed_until": scope["changed_until"] or UNFILTERED,
		"baton_scope_closure": _text(scope.get("closure")),
		"baton_scope_status": _text(scope["status"]),
		"baton_scope_team": scope["team"] or UNFILTERED,
		"baton_snapshot_seq": _text(envelope["snapshot_seq"]),
		"charset": "UTF-8",
	}
	# THE WHOLE RESULT VALIDATED, THEN BYTES -- and by ONE function. What it
	# owns, named exactly rather than summarized, because every finding against
	# this Work has been a sentence like this one being wider than the code:
	#
	#   the scope document       fixed members, closed values, the interval
	#   the derived counts       all four proved from the arrays beside them
	#   member presence          every fixed node and edge member
	#   member type              exact Python type and nullable domain
	#   a closed vocabulary      the six members whose values are enumerated
	#   the coupled node state   status with phase and outcome, as one state
	#   edge provenance          via_obligation only on a dependency
	#   graph topology           duplicate nodes, duplicate typed edges,
	#                            missing endpoints, forged predicates
	#
	# `test_the_renderer_refuses_one_input_per_category_it_claims_to_own`
	# drives one malformed input per line AND checks that this list and its
	# table name the same categories, so a category added to the prose without
	# a refusal behind it fails rather than reads well.
	#
	# Second review [P1]: this module proved presence and left types to
	# whatever read the value next. Fourth review [P1]: it proved nodes and
	# edges while `scope` and `counts` -- both required, both reaching the
	# graph attributes below -- were merely present, so a forged closure or a
	# count contradicting its own array rendered as an authoritative-looking
	# document.
	#
	# Nothing is checked here beside the call. Two boundaries checking the
	# same thing is how they come to disagree, which is the correction the
	# first review made and the reason the projection now validates its own
	# output through this same function.
	validate_work_graph(result)
	nodes = result["nodes"]
	edges = result["edges"]
	lines = ['digraph "baton_work" {']
	lines += [f"\t{one}" for one in _assignments(graph)]
	# Statement order is graph metadata, then nodes, then edges. The arrays
	# arrive already in the projection's canonical order and are NOT re-sorted
	# here: two orderings of one export would be two answers to "what is
	# canonical", and the projection owns that question.
	lines += [_node_statement(node) for node in nodes]
	lines += [_edge_statement(edge) for edge in edges]
	lines.append("}")
	# LF endings and EXACTLY ONE final LF -- a POSIX text file, so `diff`,
	# `sha256sum` and a shell redirect all behave.
	return "\n".join(lines) + "\n"
