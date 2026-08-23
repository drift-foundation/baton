"""W4996: the dependency neighbourhood, as plain ASCII rows.

`work/records/2026/08/finding-ascii-dependency-neighborhood/`, contract
approved 2026-08-22 without amendment.

PURE ON PURPOSE. Nothing here touches curses, the store or console state:
it takes one `projection.dependency_neighborhood` response and a width and
returns rows. That is what lets the layout be tested at every width without
a terminal, and it is why the console cannot accidentally invent graph
state — it has none to invent.

WIDTH CHOOSES THE RENDERER, NEVER THE GRAPH. The layered form, the
adjacency fallback and the stacked fallback all draw the SAME nodes and the
same edges. A narrow terminal loses layout, never a relationship — an
operator who widened the window and saw a new edge appear would have been
looking at a lie.

NO UNICODE, NO COLOUR, NO INFORMATION IN STYLING. Every edge spells
`--blocks-->` with the arrowhead at the consumer, so direction survives a
pipe, a log paste and a screen reader.
"""

from __future__ import annotations

ARROW = "--blocks-->"

# A row the console can select. `kind` says what Enter means: a `work` row
# recenters, an `overflow` row admits one more page of that exact branch,
# and a `deeper` row is expanded with `+` rather than Enter — the two
# reasons for omission never share an ambiguous token.
ROW_WORK = "work"
ROW_OVERFLOW = "overflow"
ROW_DEEPER = "deeper"
ROW_TEXT = "text"


class GraphTooNarrow(ValueError):
	"""The terminal cannot hold one complete selector.

	Refusing is the only honest answer: a clipped identity is a different
	Work as far as the operator's eyes are concerned, and this view exists
	to be acted on."""


def token(node: dict) -> str:
	"""`[W2929 open]` — the stable local selector and the status.

	The local selector rather than the full id because the console's other
	surfaces select that way too, and an operator who has to translate
	between two spellings will eventually translate one wrong."""
	state = node["status"] if node["status"] != "open" else (
		node.get("phase") or "open")
	return f"[{node['local_id']} {state}]"


def rows(view: dict, width: int) -> list[dict]:
	"""The rendered rows, widest form that fits.

	Order is ONE deterministic unique-node traversal and it is the same in
	every renderer: upstream outermost-to-center, the center, then
	downstream center-to-outermost, stable inside a layer by edge order,
	with each branch's overflow token immediately after its visible
	siblings. `j`/`k` therefore mean the same thing at every width."""
	widest = max((len(token(node)) for node in view["nodes"].values()),
	             default=0)
	if width < widest + 2:
		raise GraphTooNarrow(
			f"a dependency graph needs {widest + 2} columns to draw one "
			f"complete selector; this terminal has {width}. Widen it rather "
			f"than reading a clipped identity")
	layered = _layered(view, width)
	if layered is not None:
		return layered
	adjacency = _adjacency(view, width)
	if adjacency is not None:
		return adjacency
	return _stacked(view)


# ---------------------------------------------------------------------------
# the ordered node/token walk every renderer shares
# ---------------------------------------------------------------------------

def _layers(view: dict) -> tuple[list[list[str]], list[list[str]]]:
	"""Upstream and downstream layers by hop distance from the center.

	Distance is measured along the direction being expanded, so a node
	reached at two depths sits at the SHORTEST one — drawing it twice in
	one column would say there are two of it."""
	center = view["center"]
	up_edges = [edge for edge in view["edges"] if edge["side"] == "upstream"]
	down_edges = [edge for edge in view["edges"] if edge["side"] == "downstream"]
	return (_walk(center, up_edges, "blocker", "work"),
	        _walk(center, down_edges, "work", "blocker"))


def _walk(center: str, edges, far_key: str, near_key: str) -> list[list[str]]:
	layers: list[list[str]] = []
	frontier = [center]
	placed = {center}
	while frontier:
		layer: list[str] = []
		for edge in edges:
			if edge[near_key] in frontier and edge[far_key] not in placed:
				layer.append(edge[far_key])
				placed.add(edge[far_key])
		if not layer:
			break
		layers.append(layer)
		frontier = layer
	return layers


def _ordered(view: dict) -> list[dict]:
	"""Every selectable row, in the one traversal order, before layout.

	ONE ENTRY PER CANONICAL EDGE, plus the center itself.

	W4996 review [P1]: this emitted one entry per unique NODE and every
	renderer then paired that node with the center. At depth two the chain
	`A --blocks--> B --blocks--> C` therefore drew `A --blocks--> C` — a
	relationship the authority never held — and dropped the `B --blocks--> C`
	it did. That contradicts the one guarantee this view is built on: every
	rendered relationship comes from the canonical projection.

	The rows now carry their REAL endpoints. `work` remains the far node, so
	selection identity is unchanged and a Work appearing on several edges is
	still one selection.

	W4996 re-review [P2]: an overflow token is placed by its BRANCH, not by
	the node that owns the branch. It used to be emitted beside that node,
	which put the center's `[+N blockers]` after the center — between the
	center and the blockers it belongs to — and the center's
	`[+N dependents]` before any dependent had been drawn. A token that does
	not sit in its branch's traversal slot makes Enter expansion jump.
	"""
	rows = _edge_rows(view)
	# Anchor each token to its own branch and rebuild once, rather than
	# inserting into a list whose indices keep moving.
	after: dict[int, list[dict]] = {}
	for work, side, token_row in _tokens(view):
		at = _branch_anchor(rows, work, side)
		# Same anchor, deterministic order: the DENSE page first, then the
		# depth frontier. They answer different questions and a reader who
		# sees both should always see them in the same sequence.
		rank = 0 if token_row["kind"] == ROW_OVERFLOW else 1
		after.setdefault(at, []).append((side, rank, token_row))
	entries: list[dict] = []
	entries.extend(row for _side, _rank, row in sorted(after.pop(-1, [])))
	for index, row in enumerate(rows):
		entries.append(row)
		entries.extend(item for _side, _rank, item
		               in sorted(after.pop(index, [])))
	return entries


def _edge_rows(view: dict) -> list[dict]:
	"""The ROW_WORK entries alone, in traversal order."""
	upstream, downstream = _layers(view)
	upstream_edges = [edge for edge in view["edges"]
	                  if edge["side"] == "upstream"]
	downstream_edges = [edge for edge in view["edges"]
	                    if edge["side"] == "downstream"]
	rows: list[dict] = []
	# Upstream reads outermost-to-center, so the layer holding a node's
	# blockers comes before the layer holding the node.
	for layer in reversed(upstream):
		for work in layer:
			for edge in upstream_edges:
				if edge["blocker"] != work:
					continue
				rows.append({"kind": ROW_WORK, "work": edge["blocker"],
				             "blocker": edge["blocker"],
				             "consumer": edge["work"],
				             "side": "upstream"})
	rows.append({"kind": ROW_WORK, "work": view["center"], "side": "center"})
	for layer in downstream:
		for work in layer:
			for edge in downstream_edges:
				if edge["work"] != work:
					continue
				rows.append({"kind": ROW_WORK, "work": edge["work"],
				             "blocker": edge["blocker"],
				             "consumer": edge["work"],
				             "side": "downstream"})
	return rows


def _tokens(view: dict):
	"""The two kinds of omission, never sharing one token.

	A DENSE branch has more direct neighbours than the page admits and is
	opened with Enter. A DEPTH FRONTIER has neighbours the current depth
	does not reach and is opened with `+`. Collapsing them into one token
	would make the key that opens it a guess."""
	for key, omitted in view["omitted"].items():
		if not omitted:
			continue
		work, _, side = key.rpartition("|")
		noun = "blockers" if side == "upstream" else "dependents"
		yield work, side, {"kind": ROW_OVERFLOW, "work": work, "side": side,
		                   "count": omitted,
		                   "label": f"[+{omitted} {noun}]"}
	# The DEPTH frontier, and it says `deeper` because that is the whole
	# difference: this branch is not paged, it is beyond the depth bound,
	# and `+` opens it rather than Enter. A token that did not say which
	# would make the key a guess.
	for key, beyond in view.get("frontier", {}).items():
		if not beyond:
			continue
		work, _, side = key.rpartition("|")
		noun = "deeper blockers" if side == "upstream" \
			else "deeper dependents"
		yield work, side, {"kind": ROW_DEEPER, "work": work, "side": side,
		                   "count": beyond,
		                   "label": f"[+{beyond} {noun}]"}


def _branch_anchor(rows: list[dict], work: str, side: str) -> int:
	"""The index after which this branch's token belongs.

	A branch's VISIBLE members are the drawn edges of that branch: for
	downstream, the rows whose blocker is `work`; for upstream, the rows
	whose consumer is it. The token follows the last of them — that is the
	next slot a further page would fill.

	With nothing visible the branch has no members to follow, so the token
	takes the slot the branch itself would occupy: after the node's own row
	going downstream, before it going upstream, which is the direction each
	side reads."""
	members = [index for index, row in enumerate(rows)
	           if row["side"] == side
	           and row.get("blocker" if side == "downstream"
	                       else "consumer") == work]
	if members:
		return max(members)
	own = next((index for index, row in enumerate(rows)
	            if row["work"] == work
	            and (row["side"] == "center"
	                 or row["side"] == ("upstream" if side == "upstream"
	                                    else "downstream"))), None)
	if own is None:
		# A branch on a node no drawn edge reaches. It cannot be placed
		# beside anything, so it goes last rather than silently vanishing.
		return len(rows) - 1
	return own - 1 if side == "upstream" else own


# ---------------------------------------------------------------------------
# the three renderers
# ---------------------------------------------------------------------------

def _row(entry: dict, text: str, indent: int = 0) -> dict:
	return {**entry, "text": (" " * indent) + text}


def _layered(view: dict, width: int) -> list[dict] | None:
	"""The wide form: the center in ONE column, upstream reaching it from
	the left and downstream leaving it to the right.

	One row per RELATIONSHIP, drawn with that relationship's own endpoints.
	What makes it layered rather than a list is the COLUMN: every appearance
	of a Work starts at the offset of its shortest-path layer, so the eye
	follows one vertical line per layer and sees which side of the center a
	Work is on.

	W4996 re-review [P2]: this indented every downstream edge to the center
	column and right-justified every upstream edge to end there, whatever
	the depth. In `A --blocks--> B --blocks--> C` centered on A, B was the
	first row's target at the center's right edge and then the second row's
	source at column zero — one node in two columns, which is an adjacency
	list with indentation rather than a layered graph. The offsets are
	derived from `_layers` now, so a node's column is a property of the node
	and not of the row it happens to appear on.
	"""
	nodes = view["nodes"]
	upstream, downstream = _layers(view)
	column = _columns(view, upstream, downstream)
	out: list[dict] = []
	for entry in _ordered(view):
		if entry["kind"] != ROW_WORK:
			out.append(_row(entry, entry["label"],
			                indent=_token_column(view, column, entry)))
			continue
		if entry["side"] == "center":
			out.append(_row(entry, token(nodes[view["center"]]),
			                indent=column[view["center"]]))
			continue
		source = nodes[entry["blocker"]]
		target = nodes[entry["consumer"]]
		# Draw from the SOURCE's column and let the arrow reach the target's.
		lead = f"{token(source)} {ARROW}"
		gap = (column[entry["consumer"]] - column[entry["blocker"]]
		       - len(lead))
		if gap < 1:
			# W4996 re-review [P2]: THIS FORM DECLINES rather than moving an
			# endpoint.
			#
			# A legal DAG can reach a Work directly AND by a longer path —
			# `shortcut` at layer one, also the target of an edge from
			# layer two. Shortest-path layering puts it left of that source,
			# so the row cannot run left to right without either painting
			# the target in a second, farther column or overlapping the
			# arrow. The previous version clamped the gap to one space and
			# took the first of those, which contradicts the rule this
			# renderer exists to keep: a column is a property of the WORK,
			# not of the row it appears on.
			#
			# Declining hands the graph to the adjacency form, which draws
			# the same edges with the same endpoints and no columns at all.
			# Losing the layout is honest; moving a selector is not.
			#
			# The alternative — LONGEST-path layering, which makes every DAG
			# edge monotonic — is left to the reviewer: the approved contract
			# says shortest-path layers, and changing that is a contract
			# question rather than a rendering fix.
			return None
		out.append(_row(entry, lead + " " * gap + token(target),
		                indent=column[entry["blocker"]]))
	return out if all(len(row["text"]) <= width for row in out) else None


def _token_column(view: dict, column: dict[str, int], entry: dict) -> int:
	"""A branch token lines up with the SIBLINGS it offers more of.

	They are one layer out from the branch's owner — the center's blockers
	are the column to its left — so aligning the token with the owner would
	put `[+2 blockers]` in the center's own column, reading as something
	about the center rather than one more of the rows above it.

	With nothing visible on the branch there is no sibling column to join,
	and the token is that branch's only representative, so it takes the
	owner's."""
	owner, side = entry["work"], entry["side"]
	near, far = ("work", "blocker") if side == "upstream" \
		else ("blocker", "work")
	siblings = [edge[far] for edge in view["edges"]
	            if edge["side"] == side and edge[near] == owner
	            and edge[far] in column]
	if siblings:
		return min(column[work] for work in siblings)
	return column[owner]


def _columns(view: dict, upstream, downstream) -> dict[str, int]:
	"""One start offset per Work, from its shortest-path layer.

	Upstream layers are laid out RIGHT to left — the outermost blockers
	start at column zero and each layer inwards begins where the previous
	one's widest edge ends — so the center lands in one column with every
	blocker reaching it from the left. Downstream continues outwards from
	the center for the same reason in the other direction."""
	nodes = view["nodes"]

	def widest(layer) -> int:
		return max((len(token(nodes[work])) for work in layer), default=0)

	column: dict[str, int] = {}
	# Upstream, outermost first: layer i sits one arrow-span right of i+1.
	offset = 0
	for layer in reversed(upstream):
		for work in layer:
			column[work] = offset
		offset += widest(layer) + len(ARROW) + 2
	column[view["center"]] = offset
	offset += len(token(nodes[view["center"]])) + len(ARROW) + 2
	for layer in downstream:
		for work in layer:
			column[work] = offset
		offset += widest(layer) + len(ARROW) + 2
	return column


def _adjacency(view: dict, width: int) -> list[dict] | None:
	"""One edge per row, still spelling the whole relationship with its own
	endpoints. Narrower than the layered form because it drops LAYER
	columns — a Work's distance from the center is not drawn here.

	What it does keep is ONE ARROW COLUMN. W4996 re-review [P2]: this is the
	form a non-monotonic DAG falls back to, and it was ragged — the source
	field was as wide as whatever token it held, so `[W19 block]` landed at
	offset 24 after a short source and 25 after a long one. That is the same
	defect the layered correction was about, arriving through the fallback:
	one Work drawn at two offsets for a reason that has nothing to do with
	the graph. Padding the source field costs a few columns and moves no
	relationship.

	It promises less than the layered form and says so: every occurrence of
	a Work AS A TARGET shares one offset, and every occurrence AS A SOURCE
	shares another. It does not claim a single offset per Work, because an
	adjacency list has no layer to derive one from."""
	nodes = view["nodes"]
	widest = max((len(token(node)) for node in nodes.values()), default=0)
	out: list[dict] = []
	for entry in _ordered(view):
		if entry["kind"] != ROW_WORK:
			out.append(_row(entry, entry["label"]))
			continue
		if entry["side"] == "center":
			out.append(_row(entry, token(nodes[view["center"]])))
			continue
		out.append(_row(entry,
		                f"{token(nodes[entry['blocker']]).ljust(widest)} "
		                f"{ARROW} {token(nodes[entry['consumer']])}"))
	return out if all(len(row["text"]) <= width for row in out) else None


def _stacked(view: dict) -> list[dict]:
	"""The last fallback: source, label and target on their own rows.

	W4996 review [P1]: the selectable row used to paint the CENTER token for
	a downstream edge while carrying the consumer's `work`, so a console
	would highlight one Work and Enter would recenter on another. Every
	selectable row now DISPLAYS the selector for its own `work`; the other
	endpoint and the arrow are presentation rows, which is why they carry no
	identity at all.

	The relationship still reads in its true direction — for a downstream
	edge the source is shown first and the selectable target last; for an
	upstream edge the selectable source comes first."""
	nodes = view["nodes"]
	out: list[dict] = []
	for entry in _ordered(view):
		if entry["kind"] != ROW_WORK:
			out.append(_row(entry, entry["label"]))
			continue
		if entry["side"] == "center":
			out.append(_row(entry, token(nodes[view["center"]])))
			continue
		source = token(nodes[entry["blocker"]])
		target = token(nodes[entry["consumer"]])
		if entry["side"] == "upstream":
			out.append(_row(entry, source))
			out.append({"kind": ROW_TEXT, "text": f"  {ARROW}"})
			out.append({"kind": ROW_TEXT, "text": target})
		else:
			out.append({"kind": ROW_TEXT, "text": source})
			out.append({"kind": ROW_TEXT, "text": f"  {ARROW}"})
			out.append(_row(entry, target))
	return out


def footer(view: dict) -> str:
	"""What the operator can do here, and what the view is not showing.

	The cap and the depth are stated rather than implied: a graph that has
	stopped expanding looks exactly like one that had nothing more to
	show."""
	parts = [f"depth {view['depth']}/{view['depth_max']}",
	         "[Enter] recenter", "[+/-] depth", "[Esc] back"]
	if view.get("capped"):
		parts.append(f"view cap {view['occurrence_cap']} reached")
	return "  ".join(parts)
