"""Curses rendering of the canonical projection — B1.

THE PINNED MODEL, exactly: open on a borderless fixed-column table showing
three containment levels — the viewer's top-level Work, its children, and
theirs (W155, superseding W71's two-level cap). Work CLAIMED below that
window is still shown: a `⋮` elision line (W6814) stands for the omitted
levels and the exact active Work is drawn under it, so a roll-up never looks
idle while somebody is executing beneath it. `u` re-roots the window at the
selected Work and a persistent breadcrumb names that containment path; Enter
ACTIVATES the focused Work — W6814 supersedes W71's single meaning, and the
row's own canonical child count decides: a Work that contains Work becomes
the contextual root, one that contains none opens its detail (facts, trials,
and the selectable thread set). Enter there opens one thread's paged thread —
never several merged into a false timeline. `d` shows blocking/dependent neighbors
with stable ids and drills through on Enter. `p` shows the conversational
pokes this participant is part of, which are addressed to a PARTICIPANT and
not to Work — so that view hangs off the identity in the header rather than
off any row (W17). Column priorities, sorting and
keys are prototype-grade by ruling and carry no semantics of their own.

EVERY VALUE ON SCREEN comes from the projection. The renderer never computes
`New`, never sums children, never decides readiness — it formats. ACTIONS go
through the ONE public surface: the `:` command bar feeds the typed command
to the same `baton_work.cli` entry the JSON agent uses (same config, same
participant), so every transition the projection declares is available with
exactly the public grammar and exactly the public refusals. The parity suite
(B2) holds the two surfaces together by driving the same fixture through
both.
"""

from __future__ import annotations

import curses
import locale
import os
import shlex
import subprocess
import tempfile
import time as _time
import unicodedata
import uuid

from baton_work.authority import Authority, WorkError
from baton_work import cli as _cli
from baton_work import projection
from baton_work.tui import graph
from baton_work import transitions

# Fixed column budget (borderless; alignment is the separator). The title
# column absorbs the remainder and is the ONLY thing ever truncated — an
# identity is never abbreviated (6/6 rule makes them fit by construction).
# Gate B: the set is exactly the canonical projection's row fields — the
# renderer formats them and never aggregates or invents a value.
# W245/W38: ROUTE and HANDLER are separate columns because they answer
# separate questions — who MAY claim, and who IS executing. The single
# old Current column showed the endpoint, so a routed handoff nobody had
# picked up looked staffed. W38 renamed the claimant to HANDLER.
# W35 (finding-tui-endpoint-via-columns): that eligibility half is TWO
# facts, and one column labelled `Route` was showing the wrong one. The
# cell rendered the ENDPOINT — the stable `team.kind` address — while
# the label promised the route. Before W230 that was terminology; with
# alternates it is operationally misleading, because `baton.impl` is the
# same address whether the Work is offered through `impl` to Claude or
# `impl2` to Gemini. Endpoint and Via are now separate columns, and Via
# carries the selected route that actually decides claim eligibility.
# W73 (finding-hide-redundant-work-state): `St` is GONE from the default
# table. The normal list hides terminal Work, so every visible row read
# `open` — six cells repeating an invariant of the view instead of
# telling two rows apart. In its place `Out` appears ONLY where terminal
# Work can be seen, and carries the outcome rather than the word the
# view already implies.
# W2938 (finding-claim-overdue-cue) removes `New` from THIS list for
# horizontal-space priority: personal unseen state is unchanged
# everywhere it drives an action — Inbox, Threads, Message indexes, Work
# detail and `new` reads all still carry it, and the JSON field never
# moved.
#
# It adds NO replacement. The ownership supersession in that record is
# explicit: a Job is queued and unclaimed, and is not the entity that
# owes a claim — the AGENT with free capacity owes pickup. A per-Job cue
# would turn one idle participant into N duplicate overdue rows and
# attach a member-level failure to Work records. The cue lives on Teams;
# the persistent signal here is the `[Teams*]` tab.
COLUMNS = (("OUT", 5), ("PR", 2), ("PHASE", 6), ("CLS", 5),
           ("MSG/MY", 7), ("ENDPOINT", 13), ("VIA", 6), ("HANDLER", 13),
           ("RUN", 5), ("NEXT", 13), ("HELD", 6))

# Header LABELS where plain capitalize() would miscase a compound name —
# plus the ruled `Cat` display label for the classification column
# (finding-tui-category-header): presentation only, the canonical value,
# JSON field, and compact vocabulary stay `classification`/`defct`-style.
HEADER_LABELS = {"MSG/MY": "Msg/My", "CLS": "Cat", "OUT": "Out"}

# Responsive omission (prototype-grade presentation under the ruling): at
# narrow widths whole low-priority columns are OMITTED, never squeezed into
# ambiguity — identities and counters are drawn whole or not at all. The
# title keeps a minimum working width; below the minimum the table REFUSES
# with an explicit too-narrow line instead of truncating identities.
# W3 (ruled): Pr is the FIRST whole column omitted under width
# pressure, preserving every previously existing narrow layout.
# W245: NEXT then the eligibility columns go before HANDLER — under
# width pressure the question that survives longest is who is actually
# executing. W35: VIA drops before ENDPOINT, because a bare route handle
# without its address is the more ambiguous of the two halves.
# W73: `Out` is last, so it survives longest. It is present only
# because the operator asked to see terminal Work, and dropping the one
# column that answers that question would leave the reveal pointless —
# whereas Route and Next are least interesting on a closed row.
# W93 slice 5: the runtime-state column sits beside HANDLER by value and
# drops just before it. The two answer adjacent questions — who is
# executing, and what their runner is doing — and the second is
# worthless without the first.
# W137 (finding-responsive-teams-runtime-table) renamed it `Run`. It
# never held an agent: `Handler` names the participant and these cells
# say what that participant's RUNNER is doing (`work`, `input`,
# `retry`, `off`). A header naming the wrong thing costs an operator a
# lookup every time. Presentation only — the projection field is still
# `agent` and Teams still has its own `Agent` column, which really does
# name the adapter family.
# W2938: the removed `New` was in no drop order at all, so the narrowest
# layout is four cells and a separator cheaper than it was.
DROP_ORDER = ("PR", "CLS", "PHASE", "MSG/MY", "HELD", "NEXT", "VIA",
              "ENDPOINT", "RUN", "OUT")
# W93 slice 5 measured this and deliberately LEFT IT ALONE. Three Works
# have now added identity columns here — W35's Endpoint and Via, and
# this slice's Agent — and the Title is the one column the layout may
# truncate, so it has absorbed all of it: at the common 110 columns a
# title is about fourteen cells, where it was roughly twenty-four
# before W35.
#
# Raising this floor is the lever the layout already provides, and it
# does not work, because the same constant also sets the width below
# which the table REFUSES to draw. At 20 the 110-column title is healthy
# again and a 40-column terminal loses its table entirely ("need 43
# cells"); at 14 the narrow terminal survives and the wide one is back
# where it started. The two ends are in direct tension and no value
# satisfies both.
#
# That makes it a presentation ruling rather than an implementer's
# choice, and it is written up in the dossier with the measurements.
# Until it is ruled, the constant stays where W3 put it and row-location
# assertions anchor on the Id, which is identity and is never truncated.
MIN_TITLE = 10

# W26: the command-history bound. Session-local presentation state, so
# this is a memory courtesy rather than a protocol limit.
HISTORY_LIMIT = 500

# One bounded page of a Work's thread SET (prototype size): `n` pages
# forward through the canonical continuation cursor, `p` returns to the
# start — every thread is reachable, none is silently truncated.
DISC_PAGE = 10

# W2597 (finding-default-message-pane-focus): where the cursor lands
# when Work detail opens FRESH. The Threads pane is where it used to
# land, and most Work has exactly one thread — so the operator paid a
# `Tab` before every reading session to reach the Messages the thread
# was already selecting for them. Named once because three entry paths
# (Jobs, search, Inbox) share it and must not drift apart.
DETAIL_ENTRY_FOCUS = "index"

# W7 split-pane (ruled): below this terminal height the console stays
# single-pane — the split never squeezes the Work table into
# uselessness on a short terminal.
MIN_SPLIT_HEIGHT = 14

# W17 (finding-tui-poke-visibility): the bounded window of poke HISTORY
# the view keeps, and the page size it reads to reach it.
#
# W17 review 2026-08-19 (R1): `pokes` pages in canonical ASCENDING
# sequence, so reading one page from `after=0` returns the OLDEST rows.
# Sorting that page backwards is not the newest window — it hid the most
# recent answers and then said the oldest had been omitted, which was the
# opposite of what happened. The console now reads FORWARD to the end and
# keeps the tail, which is the newest window in fact rather than by
# assumption. `POKE_FETCH` is deliberately larger than the kept window:
# the walk's cost is the number of PAGES, and only while this view is
# open — the rest of the console never reads this projection at all.
#
# The OWED set never comes from this window either way. It is the
# participant projection's complete pending set, the same one the header
# counts and `wait` consumes, so no bound here can hide an unanswered
# question. The view states exactly how many older rows it left out.
POKE_PAGE = 100
POKE_FETCH = 500

# W25 (finding-tui-jobs-teams-inbox): the three top-level tabs, in the
# ruled order. Jobs is the Work tree and everything that hangs off it,
# Teams is the operational roster, Inbox is what this participant owes
# and has not seen. The order is the header's order and the `[`/`]`
# cycle's order, from one list, so they cannot disagree.
TABS = ("jobs", "teams", "inbox")

# W2938: the compact Teams-cell vocabulary for the participant pickup
# obligation. `late` rather than `overdue` because the column is four
# cells wide and this is a table; member detail spells out the full
# word beside the elapsed interval.
PICKUP_LABELS = {"pending": "pend", "overdue": "late"}


# The gap between painted tab labels. One constant because the header is
# drawn label by label — only Inbox carries the urgency weight — while
# `top_tabs()` joins the same labels into one string; two spellings of
# this spacing would put the text and the paint out of step.
TAB_GAP = "  "


# W137 (finding-responsive-teams-runtime-table): the Members table's
# column rules, in one place, because the layout is the whole finding.
#
# `floor` is the narrowest a column may be drawn; `cap` bounds the
# categorical fields so a long role list cannot eat the row. `Session`
# has NO cap: it is the diagnostic identifier an operator came for, and
# surplus width belongs to it rather than to padding around fields whose
# vocabulary is four characters wide.
# W2938 (finding-claim-overdue-cue): `Pickup` is the participant's ONE
# claim obligation — `-`, `pend`, or `late`. It sits beside `Work`,
# because the two answer the adjacent questions: what this member is
# executing, and whether they owe a pickup they have not made. Four
# cells, the width of its longest value.
TEAM_COLUMNS = (("Role", 4, 14), ("Agent", 5, 8), ("State", 5, 6),
                ("Work", 4, 8), ("Pickup", 6, 6), ("Session", 7, None),
                ("Since", 5, 6))

# Deterministic omission, narrowest first. `Session` goes first because
# the member detail block below the table carries it in full, so it is
# the one column whose loss costs nothing an operator cannot recover in
# one keystroke — and it is by far the widest. `State` and the
# participant identity are never dropped: who this is and what their
# runner is doing is the entire reason the table exists.
# W2938: `Pickup` outlives every column except `State` and the identity
# — a member who owes a pickup nobody has made is the reason an operator
# opened Teams at all.
TEAM_DROP_ORDER = ("Session", "Role", "Since", "Work", "Agent", "Pickup")


# W292: the fields that describe "where the operator is and what they
# were looking at" — captured whole on every drill-in and restored whole
# on every Back.
NAV_STATE_FIELDS = (
	"mode", "path", "cursor", "selected_id", "show_closed",
	# W26331: displayed structural location is separate from browser
	# history. A direct ancestor jump keeps the deeper page in `nav` for
	# one-step Back while resetting only this list.
	"location", "crumb_focus", "crumb_key", "crumb_return_focus",
	"search_query", "search_after", "search_page", "search_next",
	# W26328: the `Awaiting me` page and its cursor. `cursor` and
	# `selected_id` are already in this list, which is what makes
	# Enter-then-Back land on the same ROW of the same page rather
	# than at the top of page one.
	"mine_after", "mine_page", "mine_next",
	"detail_work", "detail_tab", "focus", "disc_cursor", "disc_after",
	"viewed_thread", "thread_before", "msg_cursor", "reader_skip",
	"event_cursor", "event_before", "event_focus", "event_skip",
	"links_work", "links_cursor", "poke_cursor", "poke_seq",
	# W4996: the dependency graph's whole position. A row cursor alone
	# would repeat the selection drift the Jobs table already forbids —
	# the same row index means a different Work after a depth change, a
	# branch expansion or a refresh, so the ANCHOR is the Work id (or the
	# branch key of a token) and the row is derived from it.
	"graph_center", "graph_depth", "graph_anchor", "graph_expanded",
)
# The separator between breadcrumb segments. One spelling, so the painter
# and every test read the same trail.
NAV_SEPARATOR = " > "
# What a NON-Jobs page of a Work is called in the breadcrumb's last
# segment. The Work's own three tabs need no suffix — they are tabs of the
# page the trail already names, not places of their own (W6814).
PAGE_NAMES = {"links": "deps"}
PAGE_COMPACT = {"search": "search", "links": "deps", "pokes": "pokes",
	            "mine": "awaiting"}

# W6814 (finding-tui-active-descendant-trail): the bound on ORDINARY session
# navigation history. Browser-shaped: one entry per explicit page transition,
# oldest evicted at the bound. The original caller is kept beside the stack
# and is never evicted, so a 64-deep walk can still be left in one Back —
# eviction may cost the middle of a path, never the way out of it.
NAV_HISTORY_LIMIT = 64

# W26328 (finding-actionable-work-discovery): the `Awaiting me` page size.
# One number, shared with the projection call, so the footer's page label and
# the rows it describes can never come from two different bounds.
MINE_LIMIT = 100

# W6814: the local tabs of one contextual Work page. All three are scoped to
# that page's ROOT Work: `Jobs` renders it as the tree root, and Messages and
# Events are its own. A merely highlighted descendant never moves them.
ROOT_TABS = ("jobs", "messages", "events")


def _nav_copy(value):
	"""One captured field, owned by the frame that captured it.

	W4996: lists were already copied and dicts were not, which was
	harmless while no navigation state was a dict. Branch expansions are
	one, and a shared dict would let expanding a branch after Back
	silently rewrite the frame the operator came from — a restore that is
	subtly not the state they left, which is exactly what this mechanism
	exists to prevent."""
	if isinstance(value, list):
		return [dict(one) if isinstance(one, dict) else one for one in value]
	if isinstance(value, dict):
		return dict(value)
	return value


def _fit(value: str, size: int) -> str:
	"""One value in one column, abbreviated VISIBLY when it cannot fit.

	W137: an identifier that is silently cut reads as a different,
	shorter identifier. The ellipsis is what makes a prefix say it is a
	prefix."""
	if len(value) <= size:
		return value.ljust(size)
	return (value[:size - 1] + "…") if size > 1 else value[:size]


def breadcrumb_window(items: list[dict], selected_key: str,
	                  room: int) -> list[dict]:
	"""The maximal whole-token window containing the selected crumb.

	Every candidate reserves standalone omission markers before it is
	accepted. The compact pass uses exact selectors, never sliced prose;
	if even that cannot fit, an empty answer asks the painter for the
	explicit narrow refusal.
	"""
	if not items or room <= 0:
		return []
	keys = [item["key"] for item in items]
	selected = keys.index(selected_key) if selected_key in keys \
		else len(items) - 1
	best = None
	for compact in (False, True):
		labels = [item["compact"] if compact else item["label"]
		          for item in items]
		for left in range(selected + 1):
			for right in range(selected, len(items)):
				pieces = (["…"] if left else []) + labels[left:right + 1] \
					+ (["…"] if right + 1 < len(items) else [])
				cells = sum(len(piece) for piece in pieces) \
					+ len(NAV_SEPARATOR) * max(0, len(pieces) - 1)
				if cells > room:
					continue
				count = right - left + 1
				rank = (count, not compact, cells)
				if best is None or rank > best[0]:
					best = (rank, left, right, labels)
	if best is None:
		return []
	_rank, left, right, labels = best
	out = []
	if left:
		out.append({"text": "…", "key": None})
	for index in range(left, right + 1):
		out.append({"text": labels[index], "key": items[index]["key"]})
	if right + 1 < len(items):
		out.append({"text": "…", "key": None})
	return out


# The narrowest a participant identity may be drawn before the table
# stops being about anybody. Below this the LAST column goes instead:
# a row that cannot say who it describes says nothing.
TEAM_ID_FLOOR = 3


def team_layout(width: int, id_natural: int, natural: dict):
	"""`(id_width, [(name, size)])` for one Members table.

	Pure, and separate from the painting, because every acceptance case
	in W137 is a statement about widths: a wide terminal shows the whole
	session locator, an exact fit shows everything and nothing more, a
	narrow one drops WHOLE columns in a fixed order, and a resize is
	just this function called again with a new number.

	`natural` is what each column's content actually needs, measured
	AFTER the cells exist and never before — the defect this replaces
	decided `Session` was twelve characters wide before the layout knew
	whether it had eighty columns or two hundred.

	Three passes, in this order and for this reason:

	1. FIT AT FLOORS. Dropping is decided against the narrowest each
	   column may be drawn, not against what it would like — otherwise
	   one over-long session locator deletes the whole Session column
	   from a terminal that could have shown a usable prefix.
	2. KEEP SOMEBODY. If even the floors do not fit, the identity
	   shrinks, and when it reaches `TEAM_ID_FLOOR` the remaining
	   columns go rather than the name of the member.
	3. SPEND THE SURPLUS. Categorical columns grow to their content up
	   to their cap; everything left goes to `Session`, which is the
	   only column with more to say when it is given room."""
	budget = max(0, width - 1)
	floors = {name: floor for name, floor, _cap in TEAM_COLUMNS}
	caps = {name: cap for name, _floor, cap in TEAM_COLUMNS}
	sizes = dict(floors)
	present = [name for name, _floor, _cap in TEAM_COLUMNS]
	id_width = max(len("Participant"), id_natural)

	def spent(identity):
		return identity + sum(sizes[name] + 1 for name in present)

	for name in TEAM_DROP_ORDER:
		if spent(id_width) <= budget:
			break
		present = [entry for entry in present if entry != name]
	if spent(id_width) > budget:
		id_width = budget - sum(sizes[name] + 1 for name in present)
	while present and id_width < TEAM_ID_FLOOR:
		present = present[:-1]
		id_width = budget - sum(sizes[name] + 1 for name in present)
	id_width = max(0, min(id_width, budget))

	surplus = budget - spent(id_width)
	for name in present:
		if name == "Session" or surplus <= 0:
			continue
		want = min(natural.get(name, floors[name]), caps[name] or 0) \
			- sizes[name]
		grew = max(0, min(want, surplus))
		sizes[name] += grew
		surplus -= grew
	if "Session" in present and surplus > 0:
		sizes["Session"] += min(
			surplus, max(0, natural.get("Session", 0) - sizes["Session"]))
	return id_width, [(name, sizes[name]) for name in present]


def fitted_tabs(segments, active, budget: int):
	"""The labels that fit WHOLE in `budget`, always keeping `active`.

	W110's narrow-layout contract, in one place because it is the same
	contract at both view levels. Labels are dropped ENTIRE, from
	whichever end is not the active tab, and if not even the active one
	fits the bar is empty rather than a truncated `[Inbo` — a half
	label reads as a different, shorter label.

	Review R2: the detail bar had its own left-to-right loop that
	stopped at the first label too wide, which at width 13 left the
	INACTIVE `[Messages]` on screen while the operator was in Events.
	Two copies of one rule is how the second copy ends up not being the
	rule."""
	visible = list(segments)

	def fits(seq):
		return sum(len(label) for _name, label in seq) \
			+ len(TAB_GAP) * (len(seq) - 1) <= budget

	while len(visible) > 1 and not fits(visible):
		visible = visible[1:] if visible[-1][0] == active \
			else visible[:-1]
	return visible if fits(visible) else []


# W184 (finding-teams-member-detail-table): Member detail is a
# two-column table, not prose. The keys are stable and the value column
# is aligned across the WHOLE block — including across sections, so an
# operator's eye lands in one place and stays there.
KEY_INDENT = "    "
SECTION_INDENT = "  "
KEY_GAP = 2


def kv_lines(sections, width: int) -> list[str]:
	"""Grouped key/value rows, one aligned value column.

	`sections` is `[(title, [(key, value), ...]), ...]`; a section with
	no rows is omitted entirely rather than left as a heading over
	nothing.

	Two rules the finding states and this enforces:

	- a wrapped value continues AT the value column, never under its
	  key, so a long locator still reads as one field's content;
	- a long key may not eat the value column. The key column is capped
	  at a third of the usable width, and a key past the cap keeps its
	  whole text on its own line with the value beginning on the next —
	  which is honest about both, rather than truncating a label into
	  something that reads like a different one."""
	rows = [pair for _title, pairs in sections for pair in pairs]
	if not rows:
		return []
	usable = max(4, width)
	cap = max(4, (usable - len(KEY_INDENT) - KEY_GAP) // 3)
	key_width = min(cap, max(len(key) for key, _value in rows))
	value_at = len(KEY_INDENT) + key_width + KEY_GAP
	room = usable - value_at
	# Below this the two columns stop being two columns: a value with
	# four cells is not a value. The block STACKS instead — key on its
	# own line, value indented under it — which is still every fact,
	# still in order, and still inside the screen.
	stacked = room < 8
	out: list[str] = []
	for title, pairs in sections:
		if not pairs:
			continue
		# The heading obeys the same rule as everything else: it is
		# wrapped, never painted past the edge.
		out.extend(SECTION_INDENT + piece for piece in _wrap_value(
			title, max(1, usable - len(SECTION_INDENT))))
		for key, value in pairs:
			text = "-" if value is None or value == "" else str(value)
			if stacked:
				out.extend(KEY_INDENT + piece for piece in _wrap_value(
					key, max(1, usable - len(KEY_INDENT))))
				out.extend(
					KEY_INDENT + "  " + piece for piece in _wrap_value(
						text, max(1, usable - len(KEY_INDENT) - 2)))
				continue
			pieces = _wrap_value(text, room)
			if len(key) > key_width:
				out.extend(KEY_INDENT + piece for piece in _wrap_value(
					key, max(1, usable - len(KEY_INDENT))))
				out.extend(" " * value_at + piece for piece in pieces)
				continue
			out.append(KEY_INDENT + key.ljust(key_width)
			           + " " * KEY_GAP + pieces[0])
			out.extend(" " * value_at + piece for piece in pieces[1:])
	return out


def _wrap_value(text: str, room: int) -> list[str]:
	"""One value across as many visual lines as it needs.

	Breaks on spaces where it can and mid-token only when a single
	token is wider than the column — a session locator has no spaces
	and must still be recoverable, so it wraps rather than being cut."""
	out: list[str] = []
	rest = text
	while len(rest) > room:
		cut = rest.rfind(" ", 0, room + 1)
		if cut <= 0:
			cut = room
		out.append(rest[:cut].rstrip())
		rest = rest[cut:].lstrip() if rest[cut:cut + 1] == " " \
			else rest[cut:]
	out.append(rest)
	return out or [""]


def mine_stream(rows, width: int) -> list[dict]:
	"""W26328: the PHYSICAL lines of one `Awaiting me` page.

	An entry is its Id and its COMPLETE breadcrumb — the whole
	containment path, root-first, ending in the Work's own title. The
	path is the point of this page: the tree cannot show these rows at
	all (they are deeper than its window, or under a root the operator
	is not on), so an entry that named only the Work would say what to
	claim and never where it lives, and two similarly titled Works
	under different roots would be indistinguishable.

	So the crumb WRAPS rather than truncating. Every other bounded cell
	in this console clips, because a clipped Title is still a Title and
	the row beside it carries the identity; a clipped path is a
	DIFFERENT path, and the operator has no second copy of it on the
	line. Continuation lines are blank in the Id column, which is what
	makes one entry read as one entry.

	`first` marks the line the cursor and the selection weight anchor
	to, exactly as `tree_stream`'s `kind` does: the keys see entries,
	the viewport sees lines, and the two counts are not the same
	number."""
	id_width = id_column_width(rows)
	room = max(1, width - 1 - id_width - 1)
	out: list[dict] = []
	for row in rows:
		crumb = " > ".join(entry["title"]
		                   for entry in row.get("breadcrumb") or ())
		for index, text in enumerate(_wrap_value(crumb, room)):
			out.append({"row": row, "first": index == 0,
			            "id": row["local_id"] if index == 0 else "",
			            "text": text})
	return out


def assist_text(buffer: str) -> str:
	"""W14: the command-bar assistance line — a pure FORMATTER over
	`cli.analyze_partial`, the partial-command analyzer owned beside
	the one declarative grammar the parser executes. Nothing here
	re-tokenizes or re-reads GRAMMAR: the analyzer speaks the same
	shell-quoting and first-`=` rules as execution, so the assistance
	can never drift from the parser, open an authority transaction, or
	mark anything seen.

	- typing the verb: matching command names;
	- after a complete verb: the EFFECTIVE remaining required and
	  optional keys — form conditions applied exactly as the parser
	  enforces them (accept's two forms, parked/block, say's
	  exclusive carriers, close's duplicate outcome), narrowed by a
	  live key prefix;
	- typing `key=` on a closed vocabulary: the accepted values,
	  narrowed by the typed prefix;
	- malformed, unknown, or duplicated input: the diagnostic, never a
	  plausible-looking ordinary hint.
	"""
	state = _cli.analyze_partial(buffer)
	kind = state["state"]
	if kind == "commands":
		return "command: " + ", ".join(state["matches"])
	if kind == "verbs":
		return ", ".join(state["matches"])
	if kind == "diagnostic":
		return state["diagnostic"]
	if kind == "values":
		return f"{state['key']}=: " + ", ".join(state["values"])
	parts = []
	if state["heading"]:
		parts.append(state["heading"])
	required, optional = state["required"], state["optional"]
	if state["key_matches"] is not None:
		required = [name for name in required
		            if name in state["key_matches"]]
		optional = [name for name in optional
		            if name in state["key_matches"]]
	if required:
		parts.append("required: " + ", ".join(required))
	if optional:
		parts.append("optional: " + ", ".join(optional))
	parts.extend(state["notes"])
	return "  ".join(parts) if parts else "ready"


def hot_work(row: dict) -> bool:
	"""W84 (ruled hot zone): open Work someone is EXECUTING.

	W84's second clause was "runnable REVIEW Work someone needs to
	claim", which W38 makes inexpressible here: there is no review
	phase any more, and the review-ness of Work is its Route's role, not
	a scheduler state. Reintroducing it would mean this presentation
	helper matching on role names — exactly the role-shaped reasoning
	W38 removed from the phase axis.

	So the zone reduces to its first clause, which is also the one W38
	sharpened: hot means somebody is executing it, which is now the same
	statement as `phase == "active"`. Runnable unclaimed Work of every
	role reads the same, because it IS the same situation — nobody has
	picked it up. FLAGGED for the reviewer: this narrows a ruled cue,
	and the narrowing is a consequence of W38 rather than a decision
	this Work was asked to make.

	Derived from canonical row state alone — no recency clock, no
	timestamp inference, no authority read of its own."""
	return row["status"] == "open" and row["handler"] is not None


def actionable_work(row: dict, viewer_team: str,
                    viewer_member: str) -> bool:
	"""W81 (superseding the global hot-zone bold): bold Title is
	PERSONAL actionability — "what am I supposed to handle?" — true
	exactly when:
	- this viewer IS the row's Handler; or
	- the Work is open, ready, unclaimed, not blocked/parked, and its
	  Route endpoint resolves to this viewer (every eligible handler of
	  a multi-handler Route sees it until one claims; after the claim
	  only the winner keeps the cue); or
	- this viewer has an unresolved directed @ obligation on the Work
	  (independently actionable even while blocked).
	Everyone else's activity stays visible through Phase, Handler, and
	claim Age. Pure row facts in, presentation out — no authority
	read, no authorization change.

	W245: the two clauses now read as the two different questions they
	always were — Handler answers WHO IS EXECUTING, Route answers WHO
	MAY CLAIM."""
	handler = row.get("handler")
	if handler and handler.get("team") == viewer_team and \
			handler.get("member") == viewer_member:
		return True
	if row.get("my_pending_obligations"):
		return True
	route = row.get("route")
	return (row.get("status") == "open"
	        and bool(row.get("ready"))
	        and handler is None
	        and row.get("phase") not in ("block", "parked")
	        and route is not None
	        and route["endpoint"].split(".", 1)[0] == viewer_team
	        and viewer_member in (route.get("handlers") or ()))


def visible_columns(width: int, id_width: int = 0,
                    terminal: bool = False, claimed: bool = False):
	"""The column set that fits `width`, dropping DROP_ORDER members until
	the title keeps MIN_TITLE cells. Shared with the parity suite so the
	two surfaces can never disagree about the layout. `id_width` is the
	W4 leading Id column (plus its separator) the budget must carry —
	the Id itself is identity and is never dropped or truncated.

	W73: `terminal` says whether this view CAN contain terminal Work —
	closed rows revealed with `z`, or a closed-status filter. It is the
	VIEW's question, not "does a closed row happen to be on screen right
	now": deriving it from the rows would make the column appear and
	vanish as ordinary work closed underneath the operator, and a table
	whose columns move on their own is harder to read than one dash.

	W93 applies the same rule to `Run` (W137's name for it), for the
	reason W73 removed `St`: a column that reads `-` on every row is
	cells repeating a property of the VIEW rather than telling two rows
	apart. `Run` describes the HANDLER's runner, so a window in which
	nothing is claimed has no runner to describe — and the cells it would cost come
	straight out of the Title, which is the only column the layout may
	truncate. `claimed` is the view's question, exactly as `terminal`
	is: does this window contain claimed Work at all."""
	lead = id_width + 1 if id_width else 0
	columns = [entry for entry in COLUMNS
	           if (terminal or entry[0] != "OUT")
	           and (claimed or entry[0] != "RUN")]
	for name in DROP_ORDER:
		fixed = sum(w for _n, w in columns) + len(columns)
		if width - fixed - lead - 1 >= MIN_TITLE:
			break
		columns = [entry for entry in columns if entry[0] != name]
	return tuple(columns)


def local_stamp(value, compact: bool = False) -> str:
	"""W8160: ONE conversion from a canonical UTC instant to the wall
	clock the operator is actually reading, with the zone that decided
	it.

	The defect this exists for: the console painted stored UTC fields
	verbatim, so `2026-08-25 00:36:19` appeared on a Denver terminal
	whose own clock said `2026-08-24 18:36` — a FUTURE local time, with
	nothing on screen to say it was not local. An unlabelled wall clock
	is not merely inconvenient; it is read as local, because that is
	what a wall clock means.

	Storage, the JSON API and every protocol value stay UTC and are
	untouched. This is the rendering boundary and nothing else.

	TWO INPUT FORMS, and the difference between them is the trap. The
	projection emits explicit instants like `2026-08-25T05:17:35.151Z`,
	and Baton's canonical Message spelling is `2026-08-25 05:11:03` —
	UTC fields with no offset, which `fromisoformat` returns NAIVE.
	Calling `astimezone()` on that would assume the fields are ALREADY
	local, silently keep the wrong number and add a zone label swearing
	to it. So UTC is attached explicitly first, and the conversion runs
	on an aware instant either way.

	THE ZONE IS NOT CACHED. `astimezone()` with no argument asks the C
	library for the offset in force AT THIS INSTANT, so the historical
	daylight rule decides — a January instant reads `MST` and a July one
	`MDT` on the same host, and the two local `01:30`s of a fall-back
	hour stay distinguishable by their labels. A timezone object built
	once at import would answer for the wrong half of the year and would
	not notice `TZ` changing under the process.

	`tzname()` is preferred over the numeric offset because an
	abbreviation is what an operator's other windows say; a platform
	that has no name for the zone falls back to `%z` rather than
	dropping the context, which would restore exactly the ambiguity
	this ruling removes.

	Full renders `2026-08-24 18:36:19 MDT`; `compact` renders
	`18:36 MDT` for the index tables, whose columns MEASURE the
	formatted value and drop whole rather than clipping the suffix off
	— a five-cell slice would leave an unlabelled wall clock again.

	Absent is `""`, so each caller keeps its own absent spelling. A
	value that will not parse is returned VERBATIM: the console is not
	the place to discover a malformed projection instant, and text that
	is visibly not a local stamp is a better report than a crash."""
	import datetime as _dt
	text = str(value or "").strip()
	if not text:
		return ""
	try:
		stamp = _dt.datetime.fromisoformat(
			text.replace("Z", "+00:00").replace(" ", "T"))
	except ValueError:
		return text
	if stamp.tzinfo is None:
		stamp = stamp.replace(tzinfo=_dt.timezone.utc)
	here = stamp.astimezone()
	zone = here.tzname() or here.strftime("%z")
	if compact:
		return f"{here:%H:%M} {zone}"
	return f"{here:%Y-%m-%d %H:%M:%S} {zone}"


def duration_cell(seconds) -> str:
	"""W47: the same MM:SS scale as `held_cell`, from a count of whole
	seconds the PROJECTION computed rather than a client clock.

	Kept beside `held_cell` and sharing its overflow so the two cells
	read identically; the difference is only where the number comes
	from. `-` when there is no interval at all."""
	if seconds is None:
		return "-"
	seconds = max(0, int(seconds))
	minutes = seconds // 60
	if minutes < 100:
		return f"{minutes:02d}:{seconds % 60:02d}"
	return "∞"


def held_cell(since, now) -> str:
	"""W55 (superseding only W226's timer scale and overflow spelling):
	ONE minutes:seconds interpretation for every ordinary value —
	elapsed whole seconds, `00:00` through `99:59` as MM:SS, `∞` at 100
	minutes and beyond, `-` with no reference instant. The overflow is
	`∞` rather than a saturated `99:59` (which would read as a live
	value) or a unit-bearing cap (whose units the eye cannot infer from
	the ordinary cells beside it). Clock corrections clamp to zero;
	derived client-side from a canonical instant and the local clock —
	never a second scheduler, never an extra authority read."""
	if since is None:
		return "-"
	import datetime as _dt
	stamp = _dt.datetime.fromisoformat(
		since.replace("Z", "+00:00").replace(" ", "T")).timestamp()
	seconds = max(0, int(now - stamp))
	minutes = seconds // 60
	if minutes <= 99:
		return f"{minutes:02d}:{seconds % 60:02d}"
	return "∞"


# W47's presentation threshold is GONE (W65): six minutes of protocol
# silence no longer renders an alert, because a claimed agent can be
# alive and busy inside a single model turn with no opportunity to call
# `heartbeat`. The two-minute cadence and the heartbeat instants remain
# real, audited, structured JSON facts — they simply do not drive a
# glyph. `PICKUP_OVERDUE_SECONDS` in the projection still describes a
# genuine unclaimed-pickup obligation.


def held_field(row, now) -> str:
	"""The Held field: an elapsed timer and nothing else (W15).

	W65 made `>` the primary unclaimed cue here and in Phase. Projection
	8 superseded that: `Handler` is the exact claimant and is BLANK
	when nobody holds the Work, so the row already says it. Repeating
	the same fact in two more cells was noise that made the operational
	stage harder to scan, and the marker is gone from both.

	W65's other conclusions stand. Both six-minute `!` switches stay
	removed: pending pickup does not escalate, and the claimant
	heartbeat suffix is gone because a claimed agent can be alive and
	busy inside one model turn with no opportunity to call `heartbeat` —
	treating silence as execution failure manufactured false alarms.
	Heartbeat instants remain structured JSON diagnostics.

	W78 replaced the unclaimed-handoff origin with two clocks: the
	current claim, and the displayed gate's episode. **W12 supersedes the
	second of those.** Held is the HANDLER-duration column and nothing
	else:

	ACTIVE: `MM:SS` since canonical `claimed_at` — time the current
	Handler has actually held the Work, and `Handler` names them.
	EVERYTHING ELSE — queued, block, parked, terminal: `-`.

	A blocked row has no Handler; the gate released the claim to make it.
	Running a clock there said a recipient was working, or late, on Work
	that no participant could progress — the row read as somebody's
	overdue task when it was nobody's. Blocked duration is not lost with
	the cell: the gate keeps its typed identity and episode start, `Wait`
	names it, and Events carry how long it lasted. It simply is not
	Handler time and does not belong in the Handler column.

	W78's other conclusion stands. An unclaimed handoff still starts no
	clock: two unclaimed rows in the same phase once ran different clocks
	because one carried a historical `handoff_at` and nothing on either
	row explained the difference. `handoff_at` and `pickup` remain
	structured history; they do not drive this cell.

	The instant is always the authority's. The TUI never substitutes
	`last_changed_at`, an edge's creation time, or its own observation
	time for a start the authority did not commit."""
	# Stated as the ruling states it — no Handler, no Held. The
	# projection already nulls `claimed_at` exactly when `handler` is
	# null, so this reads as a second guard on one fact; it is written
	# this way because the RULE is about the Handler, and a future change
	# to that projection coupling should not silently start a clock here.
	if row.get("handler") is None:
		return "-"
	return held_cell(row.get("claimed_at"), now)


# W48: the sentinel that distinguishes an ABSENT Event payload from a
# present falsy one. `None` cannot do this job — `null` is itself a
# payload the ledger can hold.
_ABSENT_PAYLOAD = object()


def soft_wrap(line: str, cell_width: int) -> list[str]:
	"""Break one logical line to the pane, preserving its structure.

	W48: continuations keep the line's OWN leading spaces and add
	exactly two more cells. The previous wrapper gave every indented
	line one fixed four-space continuation, so a deeply nested JSON
	scalar lost its structural depth the moment it wrapped — the reader
	showed a value at a nesting level it does not occupy.

	This preserves every displayed character. It never reserializes,
	summarizes, folds or clips; a line too long for the pane comes back
	as more visual lines, not as less content. An empty logical line
	stays one empty visual line rather than vanishing.

	The rule generalizes what the old wrapper did for the human label
	lines rather than replacing it: a top-level line indents its
	continuations by two, and a two-space fact line by four, which is
	exactly what it produced before.
	"""
	width = max(8, cell_width)
	indent = len(line) - len(line.lstrip(" "))
	continuation = " " * min(indent + 2, max(0, width - 1))
	if len(line) <= width:
		return [line]
	out, rest, prefix = [], line, ""
	while True:
		# At least one character per pass, so the loop cannot spin. The
		# clamp above normally keeps `room` positive on its own; making
		# progress STRUCTURAL means a future mistake in that arithmetic
		# shows up as a fragment too wide for the cell — which every
		# caller and test already checks — instead of as a hang, which
		# nothing can check.
		room = max(1, width - len(prefix))
		if len(rest) <= room:
			out.append(prefix + rest)
			return out
		# Break AFTER the last space inside the budget, so words survive
		# and the space itself stays on the line it ended. A space
		# inside a JSON string is DATA — consuming it at the break would
		# silently rewrite the value, and `"alpha   beta"` would come
		# back as `"alphabeta"`. Only the continuation indent this
		# function adds is presentation; every original character stays,
		# in order, so stripping that indent reassembles the line
		# exactly.
		#
		# With no space in the budget the break is hard, because an
		# unbroken JSON token must still be shown whole across lines
		# rather than truncated.
		found = rest.rfind(" ", 0, room)
		cut = found + 1 if found > 0 else room
		out.append(prefix + rest[:cut])
		rest = rest[cut:]
		prefix = continuation
		if not rest:
			return out


def _title_cell(row: dict, title_width: int) -> str:
	"""The Title column: reserved structure, then the truncatable title.

	W154. The containment marker and the deeper-Work disclosure are
	STRUCTURAL — they say where this row sits and whether anything is
	hidden beneath it — so they are laid out first and the title takes
	whatever room is left. Appending the disclosure to the title and
	cutting the result, as this used to, made the cue the first thing a
	long title removed: the one row that most needed to say "there is
	more under here" was the one that stopped saying it.

	The disclosure is the child's own canonical progress count. It is
	deliberately NOT a claimant: a parent's Handler stays blank unless
	that parent is itself claimed, because the cue says deeper Work
	exists, not that this row is being worked on.
	"""
	# W155: three containment levels, so the indent is per LEVEL — two
	# cells each, then the `↳` that marks containment. Fixed and
	# unambiguous at every depth, and still containment only: a
	# dependency is a graph edge and wears the separate `Wait` cue.
	depth = row.get("depth") or 0
	prefix = ("  " * (depth - 1) + "↳ ") if depth else ""
	# W154/W155: the more-levels icon. It says this row contains Work
	# this window does not show — at the cap that is the fourth level,
	# and it is equally true of children a filter removed. The count is
	# the row's own canonical progress total; it aggregates no Handler,
	# Phase or message state from below.
	if row.get("deeper"):
		children = (row.get("progress") or {}).get("children") or 0
		prefix += f"▸{children} " if children else "▸ "
	room = max(0, title_width - len(prefix))
	return (prefix + row["title"][:room])[:title_width].ljust(title_width)


# W6814 (finding-tui-active-descendant-trail): the omitted-levels marker.
# It says that one or more containment levels were skipped between the row
# above it and the active Work below it, and it is deliberately NOT a Work
# row — no Id, no columns, no selection. A marker an operator can put the
# cursor on is a Work as far as their hands are concerned, and Enter on one
# would have to mean nothing, which is the worst answer a key can give.
ELISION_MARK = "⋮"
ELISION_FALLBACK = "..."


def elision_mark(encoding: str | None = None) -> str:
	"""`⋮` when the terminal's locale can ENCODE it, `...` otherwise.

	Encodability is the only thing that can be ASKED. Whether the font
	actually HAS the glyph is invisible to curses, so the finding rules
	out guessing it from `TERM` or a terminal name — a guess wearing a
	fact's clothes is worse than the ASCII fallback, because the operator
	cannot tell it happened. Both spellings say the same thing and the
	structure around them is identical, so a fallback screen loses a
	glyph and no meaning."""
	if encoding is None:
		encoding = locale.getpreferredencoding(False)
	try:
		ELISION_MARK.encode(encoding)
	except (LookupError, UnicodeEncodeError, TypeError):
		return ELISION_FALLBACK
	return ELISION_MARK


def _elision_cell(depth: int, title_width: int, mark: str) -> str:
	"""The elision line's Title cell: the containment indent the hidden
	levels would have occupied, then the marker.

	It sits at the depth of the Work BELOW it, so the marker lines up
	with that row's `↳` and the pair reads as one structure rather
	than as two unrelated lines."""
	prefix = "  " * max(0, depth - 1)
	return (prefix + mark)[:title_width].ljust(title_width)


def tree_stream(rows: list[dict], trails) -> list[dict]:
	"""The PHYSICAL display order of the Jobs table — W6814.

	Ordinary Work rows in the canonical window order, and after each
	anchor's ordinary SUBTREE one elision line followed by the active
	Work rows the bounded window hides beneath it. Entries are
	`{"kind": "work", "row": ..., "trail": bool}` or
	`{"kind": "elision", "depth": ...}`; only Work entries are
	selectable, which is what keeps the cursor, the viewport anchor and
	every key on exact Work ids.

	Insertion is after the anchor's WHOLE ordinary subtree rather than
	immediately after the anchor row, because a group painted between a
	parent and its own visible children would read as another child of
	that parent. A group flushes when a row arrives that is not a
	descendant of its anchor, so nested anchors flush deepest-first and
	each group stays inside the branch it belongs to.

	One elision per anchor GROUP, not per trail: the marker says levels
	were omitted, and repeating it above every concurrent claim would
	spend a line per worker saying the same thing."""
	groups: dict[str, list[dict]] = {}
	for trail in trails or ():
		groups.setdefault(trail["anchor"], []).append(trail)
	stream: list[dict] = []
	pending: list[tuple[int, list[dict]]] = []

	def emit(depth: int, group: list[dict]) -> None:
		stream.append({"kind": "elision", "depth": depth + 1})
		for trail in group:
			# The trail's own canonical row, re-depthed for the indent
			# it is DRAWN at. Nothing else about it is touched: its
			# Handler, Phase, Run state and claim facts are the
			# projection's, and the ancestor above keeps its own.
			stream.append({"kind": "work", "trail": True,
			               "row": dict(trail["work"], depth=depth + 1)})

	def flush(down_to: int) -> None:
		while pending and pending[-1][0] >= down_to:
			depth, group = pending.pop()
			emit(depth, group)

	for row in rows:
		flush(row.get("depth") or 0)
		stream.append({"kind": "work", "trail": False, "row": row})
		if row["id"] in groups:
			pending.append((row.get("depth") or 0, groups.pop(row["id"])))
	flush(0)
	# Anchors the projection returned that this view then hid. Containment
	# forbids the only way it could happen — a parent cannot close while an
	# open child remains, so a collapsed closed row can hold no active
	# descendant — but a trail is never DROPPED to keep that assumption
	# tidy. It flushes at the end of the table, where it is visibly out of
	# place rather than invisibly absent.
	for anchor in list(groups):
		emit(0, groups.pop(anchor))
	return stream


def blocker_cue(row: dict) -> str:
	"""The inline cue under the `Wait` heading: WHAT is holding this row.

	W39/W187 established `Wn` for the deterministic first open blocker
	with `+N` counting the rest — `W171+2` waits on W171 and two more.
	NO arrow (W187: it competed with the containment marker and `Blk`
	read ambiguously); a dependency is a graph edge, never a containment
	child, and the `↳` marker is a different fact.

	W78 makes the cue name the projected GATE rather than the blocker
	list, because those are not the same question. A directed Message
	obligation blocks a Work with no blocker edge at all, and used to
	leave this cell empty beside a running clock — the row showed a
	timer and nothing that explained it. `M66` now names the source
	Message, which is the locator an operator can actually open; the
	internal obligation number is a JSON fact and is deliberately not in
	the compact row.

	`+N` still counts additional open WORK blockers, and only for a Work
	gate: the timer belongs to the displayed gate alone, so a count
	beside a Message gate would suggest the two were commensurable."""
	gate = row.get("gate")
	if not gate:
		return ""
	if gate["kind"] == "message":
		return gate["selector"] or ""
	more = (row.get("open_blockers") or 0) - 1
	return f"{gate['selector']}" + (f"+{more}" if more > 0 else "")


def cue_column_width(rows) -> int:
	"""W39/W187 R1: the dependency-cue column width — the longest
	visible cue OR the `Wait` heading, whichever is wider, so a lone
	short cue (W2) can never let the four-cell heading spill into the
	next column; still 0 when no row carries a cue (the field is
	omitted whole, heading included)."""
	longest = max((len(blocker_cue(row)) for row in rows), default=0)
	return max(longest, len("Wait")) if longest else 0


def mine_cell(row: dict) -> str:
	"""W26328: what THIS viewer can act on at this row — blank, `me`,
	`+N`, or `me+N`.

	Two facts, one cell, and they are genuinely different questions:
	`me` says this row is claimable by you right now, and `+N` says how
	many claimable rows are hidden somewhere BELOW it. A row that is
	both is `me+N`. Blank means neither, which is the common case and
	must read as nothing rather than as a zero — a column of `0`s is
	noise an operator has to look past to find the rows that matter.

	Both members come from the canonical projection row. Nothing is
	derived here: `viewer_actionable` is the same predicate `claim`
	authorizes against, and `actionable_descendants` counts the same
	set through containment.
	"""
	here = "me" if row.get("viewer_actionable") else ""
	below = row.get("actionable_descendants") or 0
	return here + (f"+{below}" if below else "")


def mine_column_width(rows) -> int:
	"""The `Mine` allocation for one painted page — the longest cell or
	the heading, whichever is wider.

	It is computed like the Id column and for the same reason: the
	column is MANDATORY and never truncated, so `me+12` widens it
	rather than being clipped to `me+1`, which would be a smaller
	number rather than a visibly cut one. Unlike the `Wait` cue it is
	never omitted when every cell is blank — an empty column still
	answers "nothing here is yours", and a column that vanished would
	be indistinguishable from a build that never had it."""
	longest = max((len(mine_cell(row)) for row in rows), default=0)
	return max(len("Mine"), longest)


def id_column_width(rows) -> int:
	"""W4: the exact leading Id column width — grown to the longest
	visible local selector (W100, W1000, ...), NEVER truncating
	identity. Shared with the parity suite so the two surfaces cannot
	disagree about the layout."""
	longest = max((len(row.get("local_id") or "") for row in rows),
	              default=0)
	return max(2, longest)


def layout_fits(width: int, id_width: int = 0,
                terminal: bool = False) -> bool:
	"""W4 R2: the fit judgment carries the VISIBLE Id column — identity
	is never truncated, and its growth may never silently clip the
	mandatory tail either; past the budget the table refuses whole."""
	lead = id_width + 1 if id_width else 0
	columns = visible_columns(width, id_width, terminal)
	fixed = sum(w for _n, w in columns) + len(columns)
	return width - fixed - lead - 1 >= MIN_TITLE


# WS-1 approved compact vocabulary — PRESENTATION ONLY, capped at five
# display cells, never a protocol identity and never a mutation value. Both
# maps are CLOSED (R5 ruling): an unmapped canonical value fails visibly —
# a client must never invent a label by truncation.
# W78: `block` renders as itself — five cells, the column width, and
# the same word the authority uses. `wait` was the compact spelling of
# `waiting`, and keeping it would have left the TUI naming a phase the
# protocol no longer has.
PHASE_COMPACT = {"queued": "queue", "block": "block",
                 "active": "actve", "parked": "park"}
# W6 (ruled): confirmed-defect reads `defct` — cnfrm did not express
# the classification. Presentation only; canonical values unchanged.
# W3 (ruled): the two-cell compact priority — presentation only; the
# canonical values and every mutation input stay the full strings.
PRIORITY_COMPACT = {"high": "Hi", "normal": "No", "low": "Lo"}


# W93 slice 5: the compact runtime labels. Five cells, because the
# canonical vocabulary is longer than any Work column can carry and an
# operator scanning a table needs the distinction, not the spelling.
# `unkn` is a DERIVED state and reads differently from `-`, which means
# nobody holds the Work at all.
AGENT_LABELS = {"idle": "idle", "working": "work",
                "waiting-input": "input", "retrying": "retry",
                "failed": "fail", "offline": "off", "unknown": "unkn"}


def agent_cell(agent) -> str:
	"""The `Run` cell for one Work row — what the handler's runner is
	doing. (W137 renamed the COLUMN; the projection field it reads is
	still `agent`, and this function is named for that field.)

	`-` when the Work is UNCLAIMED: there is no runner to describe,
	which is a different fact from a runner nobody can see. A claimed
	Work whose handler has published nothing reads `off` or `unkn`,
	exactly as the authority derived it."""
	if not agent:
		return "-"
	return AGENT_LABELS.get(agent.get("state"), str(agent.get("state")))


def compact_priority(value: str) -> str:
	if value not in PRIORITY_COMPACT:
		raise ValueError(f"priority {value!r} has no ruled compact "
		                 f"rendering")
	return PRIORITY_COMPACT[value]


CLASSIFICATION_COMPACT = {"unknown": "unkwn", "suspected-defect": "suspt",
                          "confirmed-defect": "defct",
                          "limitation": "limit", "duplicate": "dupe",
                          "design-choice": "desgn", "rejection": "rejct"}


def compact_phase(value: str) -> str:
	if value not in PHASE_COMPACT:
		raise ValueError(f"phase {value!r} has no ruled compact rendering")
	return PHASE_COMPACT[value]


def phase_cell(status: str, phase) -> str:
	"""W77 (lifecycle-aware, fail-closed both ways): a CLOSED row's
	canonical phase is null and renders the bare dash; an OPEN row must
	carry one known canonical phase — null or an unruled value refuses
	visibly rather than masquerading as a valid closed rendering."""
	if status == "open":
		if phase is None:
			raise ValueError(
				"an open work projects one canonical phase; got None — "
				"refusing to render a malformed open row as closed")
		return compact_phase(phase)
	if phase is not None:
		raise ValueError(
			f"a closed work projects phase null; got {phase!r} — "
			f"refusing to render a malformed terminal row")
	return "-"


def compact_classification(value: str) -> str:
	if value not in CLASSIFICATION_COMPACT:
		raise ValueError(f"classification {value!r} has no ruled compact "
		                 f"rendering; labels are never invented by "
		                 f"truncation")
	return CLASSIFICATION_COMPACT[value]


# Terminal outcomes, compact — a CLOSED map like the others: the four ruled
# outcomes and nothing else; an unmapped value fails visibly.
# W73 (ruled): the `c/` prefix is gone with the St column that needed
# it. It encoded "closed", which the Out column's own presence already
# says — and the operator only sees this column because they asked for
# terminal Work.
OUTCOME_COMPACT = {"satisfying": "sat", "non-satisfying": "nsat",
                   "rejected": "rej", "cancelled": "cancl"}


def compact_outcome(value: str) -> str:
	if value not in OUTCOME_COMPACT:
		raise ValueError(f"outcome {value!r} has no ruled compact rendering")
	return OUTCOME_COMPACT[value]


def outcome_cell(row: dict) -> str:
	"""OUT formats the projection's canonical outcome, and `-` while the
	Work is open.

	W73 replaces `status_cell`, which formatted `open` for every row in
	a view that could only contain open Work. The dash is not a
	placeholder for a missing value: an open Work HAS no outcome, and
	saying so beside a closed row's `rej` is what makes a mixed view
	readable. Both values are canonical; nothing is judged here."""
	if row["status"] == "open":
		return "-"
	return compact_outcome(row["outcome"])


def _completion_command(verb: str, owed: dict) -> str:
	"""One ready-to-edit command for a terminal verb.

	W228 asks for "enough command context to act without consulting
	JSON", and a bare `verb obligation=N` is not that — `respond` needs
	a body, `dispose` a disposition, `accept` a provider. Each verb's
	required operands come from the CLI's OWN grammar rather than a
	second copy here, so a grammar change cannot leave this line quietly
	advertising a command that refuses."""
	from baton_work.cli import GRAMMAR
	spec = GRAMMAR.get(verb)
	if spec is None:
		return f"{verb} obligation={owed['seq']}"
	parts = [verb]
	for key in spec["keys"]:
		if not key.get("required"):
			continue
		if key["name"] == "obligation":
			parts.append(f"obligation={owed['seq']}")
		else:
			parts.append(f"{key['name']}=…")
	if verb == "accept":
		# accept's provider is an exactly-one-of rule rather than a
		# required key, so the grammar's `required` flags cannot express
		# it; the verb refuses without one.
		parts.append("into=W… | create=true kind=… title=… classification=…")
	return " ".join(parts)


def _local_selector(identity) -> str:
	"""The local half of a canonical id — `W3`, `T12` — which is what an
	operator types and what every other column already shows. The full
	id stays in JSON; abbreviating it on screen is presentation, and
	presentation is the only thing that ever does it."""
	return "-" if not identity else str(identity).rsplit("-", 1)[-1]


def poke_answer_states() -> tuple[str, ...]:
	"""W17: the accepted `poke-answer state=` vocabulary, asked of the
	ONE declarative grammar rather than restated here.

	The console offers these as a chooser because `state=` is closed and
	an operator cannot be expected to guess a closed vocabulary. A second
	copy of it in this module would drift, and a drifted copy either
	offers a state the authority refuses or hides one it accepts —
	both worse than not offering the chooser at all."""
	from baton_work.cli import GRAMMAR
	for entry in GRAMMAR["poke-answer"]["keys"]:
		if entry["name"] == "state":
			return tuple(entry["values"] or ())
	return ()


def format_message(message: dict, width: int) -> list[str]:
	"""W8: one message as a compact borderless BLOCK — a bold metadata
	header (#seq author ts, with the viewer's personal new marker), the
	body wrapped to the pane width under a two-space indent, and the
	references under an explicit Refs section (W71): visually separate,
	one readable canonical reference per line. Presentation only."""
	import textwrap
	marker = " • new" if message.get("new") else ""
	lines = [f"#{message['seq']} {message['author_team']}."
	         f"{message['author']} "
	         f"{local_stamp(message.get('ts'))}{marker}"]
	# W228: the selected Message states the action it owes and how to
	# satisfy it. The index cue says WHICH Message; this says what to
	# type, so an ordinary directed decision stops requiring a trip to
	# `obligations` to correlate a sequence with a Message by hand. The
	# verbs are the authority's own declared completion set — never a
	# guess, and never discovered by trying them.
	owed = message.get("owed")
	if owed:
		lines.append(f"  @ you owe obligation {owed['seq']}"
		             f" ({owed['owed_by']['endpoint']})")
		for verb in owed["completes_by"]:
			lines.append(f"  complete: {_completion_command(verb, owed)}")
	body_width = max(10, width - 3)
	for paragraph in message["body"].splitlines() or [""]:
		# break_on_hyphens=False: identifiers, paths and hyphenated
		# words stay whole across wraps — a broken token reads worse
		# than a ragged margin.
		wrapped = textwrap.wrap(paragraph, body_width,
		                        break_on_hyphens=False) or [""]
		lines.extend("  " + text for text in wrapped)
	if message.get("references"):
		lines.append("  Refs:")
		for reference in message["references"]:
			text = f"[{reference['root']}:{reference['path']}]"
			wrapped = textwrap.wrap(text, body_width - 2,
			                        subsequent_indent="  ",
			                        break_on_hyphens=False) or [text]
			lines.extend("    " + piece for piece in wrapped)
	return lines


class Console:
	def __init__(self, store: Authority, viewer_team: str,
	             viewer_member: str, config_path: str | None = None,
	             work_filter: dict | None = None):
		self.store = store
		self.team = viewer_team
		self.member = viewer_member
		self.participant = f"{viewer_team}.{viewer_member}"
		self.config_path = config_path
		self.path: list[str] = []        # drilled Work ids, root-first
		# W6814: the encoding the `⋮`/`...` fallback is decided
		# against. None asks the process locale, which is what a real
		# terminal session runs under; a test pins either spelling by
		# naming an encoding, without needing a terminal to do it.
		self.encoding: str | None = None
		# W292 (finding-work-detail-breadcrumb-navigation): the ONE
		# universal navigation stack. Empty means the operator is on a
		# top-level page, which is the only place the global
		# `[Jobs] [Teams] [Inbox]` row is painted. Every drill-in — a
		# table re-root, a search, a Work detail, a links view, the
		# poke view — pushes exactly one frame, the header shows the
		# breadcrumb for the whole path instead of the global tabs, and
		# Back/Esc pops exactly one frame and restores the level it
		# reveals.
		#
		# It is deliberately NOT a Work-only mechanism: the frame kind
		# is a label, and every drillable surface uses the same push,
		# the same pop and the same captured view state. A later
		# drillable page joins by pushing a frame, not by growing a
		# special case here.
		self.nav: list[dict] = []
		# W26331: the breadcrumb's structural location. It normally grows
		# beside `nav`, but a direct crumb jump resets it without discarding
		# the history entry that one Esc must restore.
		self.location: list[dict] = []
		self.crumb_focus = False
		self.crumb_key: str | None = None
		self.crumb_return_focus: str | None = None
		# W6814: the page the FIRST drill of this walk left. It is kept
		# beside the stack rather than inside it, because the bound
		# above evicts the oldest ordinary entry and the way out is the
		# one entry that may never be the casualty.
		self.nav_caller: dict | None = None
		self.cursor = 0
		self.mode = "table"       # table / links / thread / thread
		self.status = ""
		# Resolved branches are COLLAPSED by default (ruled): closed rows
		# leave the table, an explicit count names what is hidden, and a
		# key reveals them — nothing is ever silently absent.
		self.show_closed = False
		self.links_work: str | None = None
		self.links_cursor = 0
		# W4996: the dependency neighbourhood graph. `graph_anchor` is a
		# Work id for a selectable Work row and a branch key for an
		# overflow or depth-frontier token; `graph_expanded` maps a branch
		# key to the number of direct neighbours that branch may draw.
		self.graph_center: str | None = None
		self.graph_depth = projection.DEPENDENCY_DEPTH_MIN
		self.graph_anchor: str | None = None
		self.graph_expanded: dict[str, int] = {}
		# The width the graph was last painted at. Rows are DERIVED from
		# the projection, never stored: the row order and every row's
		# identity are the same at every width — a regression asserts
		# exactly that — so a key press does not depend on having painted
		# first, and only the narrow REFUSAL is width-dependent.
		self._graph_width = 120
		self.disc_cursor: int | None = None
		self.disc_after = 0
		self.disc_next: int | None = None
		self.viewed_thread: str | None = None
		self.viewed_ordinal = 0
		self.thread_total = 0
		# W71: the detail view's pane focus (threads/msgs, moved with
		# the Ctrl-W convention), its Work, and a pending Ctrl-W prefix.
		self.focus = DETAIL_ENTRY_FOCUS
		self.detail_work: str | None = None
		self.ctrl_w_pending = False
		# W76: the Message index reads NEWEST-FIRST, so its cursor pages
		# toward older messages. None means "the newest page".
		self.thread_before = None
		# W123: Work detail has two tabs. Messages is the default —
		# opening a Work is usually about the conversation — and Events
		# is the operational play-by-play. Each tab keeps its OWN focused
		# pane, selection, page cursor and reader scroll, so switching
		# away and back returns to where the operator was rather than
		# resetting them.
		self.detail_tab = "messages"
		self.event_cursor = None
		self.event_before = None
		self.event_focus = "index"
		self.event_skip = 0
		self.viewed_event_seqs: list[int] = []
		self.viewed_events_next_before = None
		# W14: the Message-index cursor — the chosen message's
		# existing stable seq (never an invented identifier), preserved
		# across refresh, paging, and resize while the message remains
		# on the page; None asks for the new-first autoselect.
		self.msg_cursor: int | None = None
		# W14: the reader's scroll cursor — a LINE index into the
		# selected block wrapped at one specific width; it remembers
		# that width and resets when the terminal changes, so a resize
		# can repeat content but never omit it or fake a full paint.
		self.reader_skip = 0
		self.reader_skip_width: int | None = None
		self.reader_clipped = False
		self.viewed_seqs: list[int] = []
		self.viewed_next_before: int | None = None
		# W33: the ephemeral phase-CHANGE attention state — client-
		# local only, never persisted; reconnect starts cold. The
		# baseline is the first loaded snapshot (blinks nothing);
		# a later genuine Phase change arms that row's cell for THREE
		# scheduled refresh ticks. Only tick() consumes.
		self.phase_baseline: dict | None = None
		self.phase_blink: dict[str, int] = {}
		# W5: the client-local view filter — normalized {field: value}
		# in the canonical order, or None. Startup operands and the
		# interactive :filter command share ONE grammar and land here;
		# it never mutates authority state or another session's view,
		# and it does not survive restart unless supplied on launch.
		self.work_filter: dict | None = work_filter
		# W6: the slash search — typing is PURE client state (no
		# authority read per keystroke); Enter submits one canonical
		# search; Esc restores the exact prior table state. The result
		# mode reuses the ordinary refresh/cache path and anchors
		# selection by Work id.
		self.search_input: str | None = None
		self.search_query: str | None = None
		self.search_after = 0
		self.search_next: int | None = None
		self.search_page = 1
		# W26328: the flattened all-team `Awaiting me` page.
		self.mine_after = 0
		self.mine_next: int | None = None
		self.mine_page = 1
		self.mine_total = 0
		self.search_limit = 100
		self.search_saved: tuple | None = None
		self.detail_return = "table"
		# W33 R1: a timer tick only OWES a consumption — the cycle is
		# spent by the SUCCESSFUL scheduled canonical read that
		# follows, never by the tick alone (a failed read spends
		# nothing the operator never saw).
		self.tick_owed = False

		self.command: str | None = None  # the `:` command-bar buffer
		# W35: where the next insertion or deletion lands — an index
		# into `command`'s CHARACTERS, 0..len, and the only thing that
		# makes the bar an editable line rather than an append-only
		# one. Every assignment to `command` goes through
		# `_set_command`, so the two can never disagree about a buffer
		# one of them has not seen.
		self.command_caret: int = 0
		# W36: a one-shot line shown where the assistance hint goes,
		# for the case the ordinary status row cannot serve: the bar is
		# REOPENED holding the intact draft, and the status row is
		# hidden behind it. Cleared by the next keystroke.
		self.command_note: str | None = None
		# W26: bounded, session-local command history. Presentation
		# state, not protocol state — it is never read from or written
		# to the authority, and a second Console has its own.
		self.history: list[str] = []
		# Where Up/Down currently sits: an index into `history`, or
		# None meaning "on the live draft, past the newest entry".
		self.history_cursor: int | None = None
		# The buffer as it was before history navigation began, so
		# Down past the newest entry restores it BYTE-EXACTLY rather
		# than approximately. W35: `(text, caret)` — restoring the
		# characters but dropping the caret would be a different draft
		# from the one the operator left, and carrying the pair means
		# the existing `= None` resets cannot leave a stale caret
		# behind a live draft.
		self.history_draft: tuple[str, int] | None = None
		# W26 reverse search: {"query", "match", "draft"} while active.
		# `match` is an index into `history` or None when nothing
		# matches; `draft` is the pre-search buffer Esc restores.
		self.reverse: dict | None = None
		# W81: the contextual `say` seed. `seeded_say` is the exact
		# operand text this client inserted, so an explicit one arriving
		# later can displace precisely that and nothing else.
		self.seeded_say: str | None = None
		# W9: the one-row exit confirmation — q asks, y answers.
		self.confirm_exit = False
		# W17: the poke view's own selection, anchored on the poke's
		# stable sequence so a background refresh cannot move the
		# operator onto a different question. `poke_choice` holds the
		# poke seq whose answer is waiting for its one state key, and
		# is the only modal state this view keeps.
		self.poke_cursor = 0
		self.poke_seq: int | None = None
		self.poke_choice: int | None = None
		# W25: the three top-level tabs and each one's own selection.
		# Every anchor is a CANONICAL identity — an action key, a
		# selector, a participant address — never a row index, so a
		# background refresh cannot move the operator onto a different
		# row merely because the list changed underneath them.
		self.tab = "jobs"
		self.inbox_cursor = 0
		self.inbox_key: str | None = None
		self.team_cursor = 0
		self.team_member: str | None = None
		# Ruled default: the viewer's own team, with deliberate
		# navigation into every configured team behind one key.
		self.teams_own_only = True
		# W19: the `::` batch buffer — a list of staged line entries
		# ({text, state, note, op_id}), or None when closed. Pure view
		# state until Ctrl-G; states are None (staged), "completed",
		# "failed", "unrun".
		self.batch: list[dict] | None = None
		self.batch_cursor = 0
		self.batch_confirm = False
		self.batch_status = ""
		# W5: the projection CACHE. Ordinary keystrokes operate on
		# cached data and never query the authority; the configured
		# timer tick (and an explicit mutation's own refresh) are the
		# only invalidations. Navigation to a NEW context fetches on
		# miss — displaying a view the cache has never held is not a
		# poll.
		self._cache: dict = {}
		# The ONE refresh scheduler (pinned): timer expiry and a
		# successful local mutation are two PRODUCERS of the same
		# refresh request; the cache accessor consumes it, and pending
		# requests coalesce — a due flag, not two behaviors.
		self.refresh_due = False
		# W5: the id-stable selection anchor — a background refresh
		# must never move the cursor to a different Work merely
		# because rows changed.
		self.selected_id: str | None = None

	# -- W292: the universal navigation stack ----------------------------

	def _nav_capture(self) -> dict:
		"""Everything that makes the CURRENT level look the way it does.

		One fixed field list rather than a per-mode capture: a
		mode-specific snapshot is one forgotten attribute away from
		restoring a frame that is subtly not the one the operator left,
		and the forgotten attribute is invisible until somebody
		navigates the exact path that used it."""
		state = {}
		for name in NAV_STATE_FIELDS:
			state[name] = _nav_copy(getattr(self, name))
		return state

	def _nav_restore(self, state: dict) -> None:
		for name, value in state.items():
			setattr(self, name, _nav_copy(value))

	def _nav_push(self, kind: str, label: str, *,
	              restore: dict | None = None,
	              work: str | None = None) -> None:
		"""Record ONE explicit navigation. `restore` is the state of the
		page being LEFT, captured before the caller changed anything;
		omitting it captures the live state, which is right whenever the
		push happens first.

		A Work frame carries the Work's ID, not only its title. Two
		siblings may share a title, and deciding what is already on the
		stack by comparing prose would put the operator in a scope they
		did not open.

		W6814 supersedes W292's frame-per-ancestor seeding. This stack is
		INTERACTION history in the browser's model: one entry per
		explicit navigation act, whatever containment distance that act
		crossed. Structure is now the breadcrumb's separate job
		(`nav_segments`), and the two answer genuinely different
		questions — how did I get here, and where am I. Under W292 they
		were one list, so opening a VISIBLE grandchild with one Enter
		cost three Backs to leave, through two pages the operator had
		never asked to see."""
		state = self._nav_capture() if restore is None else restore
		if self.nav and (kind, work, label) == \
				(self.nav[-1]["kind"], self.nav[-1]["work"],
				 self.nav[-1]["label"]):
			# Consecutive duplicates coalesce. The page you are already
			# on is not somewhere Back can take you, and recording it
			# would spend a Back doing nothing visible — which reads as
			# a dropped keystroke.
			return
		if not self.nav:
			self.nav_caller = state
		self.nav.append({"kind": kind, "label": label, "work": work,
		                 "restore": state})
		self.location.append({"kind": kind, "label": label, "work": work})
		self.crumb_focus = False
		self.crumb_key = None
		if len(self.nav) > NAV_HISTORY_LIMIT:
			# The OLDEST ordinary entry goes. `nav_caller` already holds
			# the escape target, so the walk shortens from the far end
			# and never loses its exit.
			del self.nav[0]
			if len(self.location) > NAV_HISTORY_LIMIT:
				del self.location[0]

	def _nav_pop(self) -> bool:
		"""Back/Esc: pop EXACTLY one entry and restore the page it
		reveals. False when there is nothing to pop, which is how a
		top-level page keeps its own Esc semantics.

		W6814: the LAST Back always lands on the original caller.
		Normally that is exactly the popped entry's own restore; after an
		eviction it is the only surviving record of it, which is what
		stops a long walk from stranding the operator inside a Work
		view."""
		if not self.nav:
			return False
		frame = self.nav.pop()
		state = frame["restore"] if self.nav \
			else (self.nav_caller or frame["restore"])
		self._nav_restore(state)
		if not self.nav:
			self.nav_caller = None
		return True

	def nav_segments(self) -> list[str]:
		"""The complete location path, root-first, or empty at the top
		level. The first segment is the top-level PAGE the walk started
		from.

		W6814 splits this from the Back stack. A Work page contributes
		its canonical containment ANCESTRY — every level, whether or not
		the operator opened each one explicitly — because the breadcrumb
		answers where this is, and containment is what that means. `nav`
		answers the different question of how many Backs it took to get
		here, and one Enter is one Back however many levels it crossed.

		A drill DEEPER inside a path already painted contributes only its
		missing descendants (W292 R1: `root > root > child` duplicated a
		segment that is not a containment level); a page of a Work the
		segment above already names contributes that page's name instead;
		and a page that is not a Work's names itself."""
		return [item["label"] for item in self.breadcrumb_items()]

	def breadcrumb_items(self) -> list[dict]:
		"""Structured breadcrumb targets for the displayed location.

		`nav` is browser history; `location` is the structural path it
		currently displays. Keeping this structured is what lets focus move
		without parsing titles and lets an ancestor jump reset the latter
		without popping the former.
		"""
		if not self.location:
			return []
		items = [{"key": "top:jobs", "label": "Jobs", "compact": "Jobs",
		          "kind": "top", "work": None, "location": []}]
		covered: list[str] = []
		for index, frame in enumerate(self.location):
			prefix = _nav_copy(self.location[:index + 1])
			if not frame["work"]:
				kind = frame["kind"]
				items.append({"key": f"page:{index}:{kind}",
				              "label": frame["label"],
				              "compact": PAGE_COMPACT.get(kind, kind),
				              "kind": kind, "work": None,
				              "location": prefix})
				covered = []
				continue
			trail = self._work_ancestry(frame["work"])
			ids = [entry["id"] for entry in trail]
			already = len(covered) \
				if covered and ids[:len(covered)] == covered else 0
			for entry in trail[already:]:
				target = _nav_copy(self.location[:index])
				target.append({"kind": "work", "label": entry["title"],
				               "work": entry["id"]})
				items.append({"key": f"work:{entry['id']}",
				              "label": entry["title"],
				              "compact": entry["id"].rsplit("-", 1)[-1],
				              "kind": "work", "work": entry["id"],
				              "location": target})
			covered = ids
			if frame["kind"] in PAGE_NAMES:
				kind = frame["kind"]
				items.append({"key": f"page:{index}:{kind}",
				              "label": PAGE_NAMES[kind],
				              "compact": PAGE_COMPACT[kind],
				              "kind": kind, "work": frame["work"],
				              "location": prefix})
		return items

	def _state_for_location(self, location: list[dict]) -> dict | None:
		"""The exact captured page state for one displayed prefix."""
		if not location:
			return _nav_copy(self.nav_caller) if self.nav_caller else None
		for frame in reversed(self.nav):
			state = frame["restore"]
			if state.get("location") == location:
				return {name: _nav_copy(value)
				        for name, value in state.items()}
		return None

	def _work_jump_state(self, work_id: str) -> dict:
		"""A Work crumb target, preserving a contextual Work local tab."""
		tab = self.context_tab() if self.context_work() else "jobs"
		if tab == "jobs":
			return self._rooted_state(work_id)
		state = self._fresh_detail_state(work_id)
		state["detail_tab"] = tab
		return state

	def _jump_to_crumb(self, item: dict) -> None:
		items = self.breadcrumb_items()
		if not items or item["key"] == items[-1]["key"]:
			return
		if item["kind"] == "top":
			target = self._state_for_location([])
		elif item["kind"] == "work":
			target = self._work_jump_state(item["work"])
		else:
			target = self._state_for_location(item["location"])
		if target is None:
			return
		# One direct jump is one browser-history action. `_nav_push`
		# captures the complete deeper page, including its breadcrumb
		# selection, before only the displayed location is reset.
		self._nav_push(item["kind"], item["label"], work=item["work"])
		self._nav_restore(target)
		self.location = _nav_copy(item["location"])
		self.crumb_focus = bool(self.location)
		self.crumb_key = item["key"] if self.location else None

	def _enter_breadcrumb(self, return_focus: str | None = None) -> bool:
		items = self.breadcrumb_items()
		if not items:
			return False
		self.crumb_focus = True
		self.crumb_return_focus = return_focus
		if self.crumb_key not in {item["key"] for item in items}:
			self.crumb_key = items[-1]["key"]
		return True

	def _leave_breadcrumb(self) -> None:
		self.crumb_focus = False
		if self.detail_tab == "events" and self.crumb_return_focus:
			self.event_focus = self.crumb_return_focus
		elif self.crumb_return_focus:
			self.focus = self.crumb_return_focus

	def _handle_breadcrumb_key(self, key: int) -> bool:
		if not self.crumb_focus:
			return False
		items = self.breadcrumb_items()
		if not items:
			self.crumb_focus = False
			return False
		keys = [item["key"] for item in items]
		at = keys.index(self.crumb_key) if self.crumb_key in keys \
			else len(keys) - 1
		if key in (ord("h"), curses.KEY_LEFT):
			self.crumb_key = keys[max(0, at - 1)]
		elif key in (ord("l"), curses.KEY_RIGHT):
			self.crumb_key = keys[min(len(keys) - 1, at + 1)]
		elif key in (curses.KEY_ENTER, 10, 13):
			self._jump_to_crumb(items[at])
		elif key in (curses.KEY_DOWN, ord("j")):
			self._leave_breadcrumb()
		else:
			return False
		return True

	def context_work(self) -> str | None:
		"""The Work whose CONTEXTUAL PAGE the operator is on, or None at
		a top-level page or a page that is not a Work's.

		This is what the local `[Jobs] [Messages] [Events]` row is scoped
		to. It comes from the navigation entry rather than from the
		cursor, which is the ruling: moving the highlight through the
		tree must never change which Work owns Messages or Events."""
		if self.location:
			here = self.location[-1]
			return here["work"] if here["kind"] == "work" else None
		# A view constructed STRAIGHT into a Work page has no recorded
		# path — the parity and unit harnesses build one — and its tabs
		# must still be that Work's. The re-rooted table says so through
		# `path`, and the detail view through the Work it is showing.
		if self.mode == "detail":
			return self.detail_work
		return self.path[-1] if self.path else None

	def context_tab(self) -> str:
		"""Which of the contextual page's three tabs is showing."""
		return "jobs" if self.mode != "detail" else self.detail_tab

	def nav_text(self) -> str:
		return NAV_SEPARATOR.join(self.nav_segments())

	def _work_ancestry(self, work_id: str) -> list[dict]:
		"""The canonical root-first containment trail, ending at
		`work_id`. One cached read, shared by every drill that seeds
		Work frames."""
		trail = self._cached(("breadcrumb", work_id),
		                     lambda: projection.breadcrumb(self.store, work_id))
		return list(trail) or [{"id": work_id, "title": work_id}]

	def _open_root(self, work_id: str) -> None:
		"""Make one Job the CONTEXTUAL ROOT of the Work view — W6814.

		The three-level window and its active-descendant elisions are
		recomputed relative to the new root, which is the whole point:
		once the operator has opened a Job, spending vertical space on
		its former ancestors buys them nothing they cannot read in the
		breadcrumb.

		Re-rooting where you already are is idempotent and records no
		history, so `u` on the current root and Enter on the root row are
		both no-ops rather than Backs that go nowhere."""
		if self.mode == "table" and self.path and self.path[-1] == work_id:
			return
		self._nav_push("work", self._work_title(work_id), work=work_id)
		self._nav_restore(self._rooted_state(work_id))

	def _activate(self, row: dict) -> None:
		"""Enter on a Job — W6814, deliberately superseding W71's rule
		that Enter always opened detail and only `u` re-rooted.

		The row's OWN canonical child count decides. A Job that contains
		Work becomes the contextual root and the tree is recomputed
		beneath it; a Job that contains none opens its own detail,
		because there is no subtree left to present. One canonical fact
		(`progress.children`, the same number the `▸N` disclosure already
		draws), so the two branches cannot drift from what the screen
		says.

		`u` survives as the EXPLICIT re-root — it is the way to root at a
		childless Job, which activation deliberately does not do — and it
		is no longer the only way to reach a subtree.

		Either branch is ONE explicit navigation and therefore exactly
		one Back, whatever containment distance Enter crossed."""
		children = (row.get("progress") or {}).get("children") or 0
		if children:
			self._open_root(row["id"])
		else:
			self._enter_detail(row["id"], came_from="table")

	def _work_title(self, work_id: str) -> str:
		"""A Work's own title from the cached breadcrumb — the same read
		the trail uses, so a segment and the path it sits in can never
		name the Work differently."""
		trail = self._cached(("breadcrumb", work_id),
		                     lambda: projection.breadcrumb(self.store, work_id))
		if trail:
			return trail[-1]["title"]
		return work_id.rsplit("-", 1)[-1]

	# -- data: cached canonical reads (W5) --------------------------------

	def schedule_refresh(self) -> None:
		"""Producer side of the ONE refresh path — timer expiry and
		successful local mutations both land here; requests coalesce."""
		self.refresh_due = True

	def _cached(self, key, loader):
		# Consumer side: a due refresh drops the whole cache exactly
		# once before the next canonical read.
		if self.refresh_due:
			self._cache.clear()
			self.refresh_due = False
		if key not in self._cache:
			self._cache[key] = loader()
		return self._cache[key]

	def tick(self) -> None:
		"""The timer tick — a PRODUCER on the one refresh path: the
		next paint re-reads. Read-only; no seen mark, no transition,
		no cursor decision lives here. W33 R1: the tick only marks a
		consumption as OWED — the phase-change countdown is spent by
		the successful scheduled canonical read that follows, so a
		failed read spends nothing, keystrokes/redraws/resize/mutation
		refreshes spend nothing, and a coalesced timer+mutation
		refresh spends exactly one."""
		self.tick_owed = True
		self.schedule_refresh()


	def _window(self) -> dict:
		"""THE canonical tree window — W155 (superseding W71's two-level
		cap): the main screen is a bounded THREE-LEVEL containment
		window. At the top it shows every root, each root's immediate
		children (depth 1, `↳`) and their children in turn (depth 2);
		re-rooted (`u`) it shows the selected Work and the next three
		levels beneath it. Indentation is the single-parent containment
		tree ONLY — graph edges never masquerade as children. Each row
		dict carries a presentation `depth` and a `deeper` flag saying
		whether it holds Work this window does not show."""
		# W71 R3: ONE canonical projection call — rows (with depth),
		# summary and token all come from one read snapshot; the screen
		# can never mix two authority states, and JSON `tree` returns
		# the identical result.
		root_id = self.path[-1] if self.path else None
		# W5: the filter is part of the canonical query — the cache key
		# carries it, and the projection returns the filtered window
		# plus its normalized disclosure.
		filter_key = tuple(sorted((self.work_filter or {}).items()))
		return self._cached(("tree", root_id, filter_key),
		                    lambda: projection.tree(
			self.store, root_id, viewer_team=self.team,
			viewer_member=self.member,
			work_filter=self.work_filter))

	def view(self) -> tuple[list[dict], dict]:
		"""(tree rows, summary) — the two halves of `_window()` every
		caller that does not need the trails already asked for."""
		window = self._window()
		return list(window["rows"]), window["summary"]

	def trails(self) -> list[dict]:
		"""W6814: the actively claimed Work the bounded window HIDES,
		each with the returned ancestor it belongs under.

		Served from the SAME cached window as the rows and the summary,
		so an elision group and the ancestor it hangs from are one
		authority state — the whole reason the field is derived inside
		the canonical tree read rather than joined here."""
		return list(self._window().get("active_trails") or ())

	def elision_mark(self) -> str:
		"""The omitted-levels marker this terminal can actually
		encode."""
		return elision_mark(self.encoding)

	def table_rows(self) -> tuple[list[dict], int]:
		"""(selectable Jobs rows, hidden closed count) — W6814.

		The ordinary window and the active-descendant trails in ONE
		display order, which is what every key acts on: a trail Work is
		reachable by j/k, Enter, `c`, `d` and `u` exactly as an
		ordinary row is, because from the operator's hands it is an
		ordinary row. The elision lines are not here at all — the keys
		never see a line that is not a Work."""
		visible, hidden = self.visible_rows(self.rows())
		stream = tree_stream(visible, self.trails())
		return ([entry["row"] for entry in stream
		         if entry["kind"] == "work"], hidden)

	def search_rows(self) -> list[dict]:
		"""W336: the search window flows through the SAME countdown and
		observation boundary as the main table — the accepted search
		through the SAME cache/refresh path the table uses — the timer tick invalidates, keystrokes serve from
		cache, and the id anchor keeps selection stable. W6 R1: paging
		operates on the console's EFFECTIVE visible universe — while
		closed Work is hidden and no explicit status filter overrides
		it, the search itself constrains to status=open, so hidden
		closed matches can never consume a page or distort its counts;
		exposing closed rows (z) or filtering status=closed lifts the
		constraint. JSON's canonical all-status result is untouched."""
		owed = self.refresh_due and self.tick_owed
		effective = dict(self.work_filter or {})
		if not self.show_closed and "status" not in effective:
			effective["status"] = "open"
		effective = effective or None
		filter_key = tuple(sorted((effective or {}).items()))
		window = self._cached(
			("search", self.search_query, self.search_after,
			 filter_key),
			lambda: projection.search(
				self.store, self.search_query,
				viewer_team=self.team, viewer_member=self.member,
				work_filter=effective,
				after=self.search_after, limit=self.search_limit))
		self.search_next = window["next_after"]
		rows = list(window["rows"])
		self._spend_owed_cycle(owed)
		self._observe_phases(rows)
		return rows

	def mine_rows(self) -> list[dict]:
		"""W26328: ONE page of the flattened `Awaiting me` window,
		through the same cache, countdown and observation boundary
		every other table-shaped window uses.

		It is deliberately NOT the tree filtered down. The tree is a
		bounded three-level containment window, so a claimable Work
		four levels under a root it never returns is invisible there
		however carefully the operator looks — which is the finding.
		This asks the authority the flat question directly, across the
		whole team's Work and independently of the current root, and
		the projection answers with the same claimability the `claim`
		operation authorizes against.

		`show_closed` and the work filter are NOT applied. A closed
		Work is never claimable and a filtered-out one is still
		awaiting you, so honouring either would let a view state the
		operator set for a different question silently hide Work this
		page exists to surface."""
		owed = self.refresh_due and self.tick_owed
		window = self._cached(
			("mine", self.mine_after),
			lambda: projection.actionable_work(
				self.store, viewer_team=self.team,
				viewer_member=self.member,
				after=self.mine_after, limit=MINE_LIMIT))
		self.mine_next = window["next_after"]
		self.mine_total = window["actionable_for_viewer"]
		rows = list(window["rows"])
		self._spend_owed_cycle(owed)
		self._observe_phases(rows)
		return rows

	def _spend_owed_cycle(self, owed: bool) -> None:
		"""W336: the ONE countdown boundary. Every table-shaped window
		— the main/re-rooted tree AND search, through the full render()
		path and key paths alike — spends the phase-blink cycle here,
		and only for the successful scheduled read that `owed`
		witnessed. Failed reads never reach this call; mutation-only
		refreshes and keystroke repaints arrive with owed False."""
		if not owed:
			return
		self.phase_blink = {work_id: remaining - 1
		                    for work_id, remaining
		                    in self.phase_blink.items()
		                    if remaining > 1}
		self.tick_owed = False

	def rows(self) -> list[dict]:
		# W33 R1: consumption is bound to the SUCCESSFUL scheduled
		# canonical read. A pending tick (tick_owed) plus a due
		# refresh means THIS fetch is that read — if it raises,
		# nothing below runs and no cycle is spent; a coalesced
		# timer+mutation refresh spends exactly one; a mutation-only
		# refresh (no owed tick) spends none.
		owed = self.refresh_due and self.tick_owed
		rows = self.view()[0]
		self._spend_owed_cycle(owed)
		self._observe_phases(rows)
		return rows

	def _observe_phases(self, rows) -> None:
		"""W33: compare the freshly painted window against the last
		observed baseline. The FIRST snapshot only establishes the
		baseline (initial load and reconnect are cold). A genuine
		Phase change arms (or re-arms) that row's three-tick blink;
		an unchanged window arms nothing, so cached repaints and
		no-op refreshes are naturally inert."""
		seen = {row["id"]: row["phase"] for row in rows}
		if self.phase_baseline is None:
			self.phase_baseline = seen
			return
		for work_id, phase in seen.items():
			if work_id in self.phase_baseline and \
					self.phase_baseline[work_id] != phase:
				self.phase_blink[work_id] = 3
		self.phase_baseline.update(seen)

	def terminal_visible(self) -> bool:
		"""W73: can this view contain terminal Work?

		The two triggers the ruling names — closed rows revealed with
		`z`, or a closed-status filter — and it is deliberately the
		same question `visible_rows` asks, factored so the column set
		and the row set can never disagree about which view this is."""
		return bool(self.show_closed or
		            (self.work_filter or {}).get("status") == "closed")

	def visible_rows(self, rows: list[dict]) -> tuple[list[dict], int]:
		"""(rows to draw, hidden closed count) — the collapse is pure
		presentation over the projection's own status values. W5 R1: an
		EXPLICIT status=closed filter reveals the rows it selected —
		the default collapse would erase the filter's whole answer (and
		its open context parents); the ordinary collapse applies
		whenever no status filter requests closed Work."""
		if self.terminal_visible():
			return rows, 0
		visible = [row for row in rows if row["status"] == "open"]
		return visible, len(rows) - len(visible)

	def thread_rows(self) -> list[dict]:
		"""ONE bounded page of the focused Work's thread SET from the
		paged canonical read — never merged, each row selectable, the
		continuation cursor kept so `n` reaches every later page."""
		page = self._cached(
			("work_threads", self.detail_work, self.disc_after),
			lambda: projection.work_threads(
				self.store, self.detail_work, viewer_team=self.team,
				viewer_member=self.member, after=self.disc_after,
				limit=DISC_PAGE))
		self.disc_next = page["next_after"]
		return page["rows"]

	def owed_pokes(self) -> list[dict]:
		"""The pokes THIS participant owes an answer — the canonical
		pending set, taken from the same participant projection the
		header counts and `wait` consumes rather than from a second
		derivation of "still owed". Answered, cancelled, superseded and
		timed-out pokes are absent here by construction: the projection
		stops offering them, so presentation never has to decide it."""
		mine = self._cached(
			("participant_actions",),
			lambda: projection.participant_actions(
				self.store, viewer_team=self.team,
				viewer_member=self.member))["actions"]
		return [action for action in mine if action["kind"] == "poke"]

	def _poke_window(self, side: str) -> dict:
		"""The NEWEST bounded window of one poke narrowing, with the
		counts needed to say honestly what it left out.

		`pokes` pages ascending from a sequence cursor, so the newest
		window is reached by walking FORWARD to the end and keeping the
		tail — there is no backwards operand to ask for, and inventing
		the answer by reversing the first page is exactly the defect
		this replaces. Only the tail is retained, so the walk's memory
		is the window and not the history.

		`self` counts the pokes this participant sent to itself, which
		are the only rows appearing in BOTH narrowings — the correction
		that makes a merged total a count of distinct pokes rather than
		a double count."""
		me = f"{self.team}.{self.member}"
		narrow = {"target": me} if side == "target" else {"asker": me}
		rows: list[dict] = []
		total = mutual = after = 0
		while True:
			page = projection.pokes(
				self.store, viewer_team=self.team,
				viewer_member=self.member, after=after,
				limit=POKE_FETCH, **narrow)["pokes"]
			total += len(page)
			mutual += sum(1 for entry in page
			              if entry["asker"] == entry["target"] == me)
			rows = (rows + list(page))[-POKE_PAGE:]
			if len(page) < POKE_FETCH:
				break
			after = page[-1]["poke"]
		return {"rows": rows, "total": total, "mutual": mutual}

	def poke_rows(self) -> tuple[list[dict], int]:
		"""(rows, older not shown) — every poke this participant is part
		of: the ones asked OF them, which they answer, and the ones they
		asked, which they may withdraw.

		Owed pokes sort first and the rest follow newest-first, so the
		question waiting on the operator is the one under the cursor
		when the view opens. `owed` is the canonical pending set above,
		which is complete and separately derived; everything else is the
		newest bounded history window, and the count returned beside it
		is exactly how many distinct older pokes it omitted."""
		me = f"{self.team}.{self.member}"
		asked_of_me = self._cached(("pokes", "target"),
		                           lambda: self._poke_window("target"))
		asked_by_me = self._cached(("pokes", "asker"),
		                           lambda: self._poke_window("asker"))
		merged: dict = {}
		for entry in asked_of_me["rows"] + asked_by_me["rows"]:
			merged[entry["poke"]] = dict(entry)
		for action in self.owed_pokes():
			# A poke older than the history window is still owed, and
			# owed is the fact this view exists for — so the action
			# supplies the row rather than it being dropped for falling
			# off a page.
			row = merged.setdefault(action["poke"], {
				"poke": action["poke"], "asker": action["asker"],
				"target": me, "request": action["request"],
				"asked_at": action["asked_at"],
				"expires_at": action["expires_at"],
				"state": "pending", "answer": None})
			row["owed"] = True
		rows = []
		for entry in sorted(merged.values(), key=lambda row: -row["poke"]):
			entry.setdefault("owed", False)
			entry["mine"] = entry["asker"] == me
			rows.append(entry)
		rows.sort(key=lambda row: not row["owed"])
		distinct = (asked_of_me["total"] + asked_by_me["total"]
		            - asked_of_me["mutual"])
		return rows, max(0, distinct - len(rows))

	def _poke_selected(self) -> dict | None:
		rows, _older = self.poke_rows()
		if not rows:
			return None
		for index, row in enumerate(rows):
			if row["poke"] == self.poke_seq:
				self.poke_cursor = index
				return row
		self.poke_cursor = min(self.poke_cursor, len(rows) - 1)
		chosen = rows[self.poke_cursor]
		self.poke_seq = chosen["poke"]
		return chosen

	def inbox_view(self) -> dict:
		"""The participant's Inbox, through the ONE cached read path —
		the tab label, the bold rule and the rows are all the same
		canonical answer, so the count can never advertise a row the
		list does not hold."""
		return self._cached(("inbox",), lambda: projection.inbox(
			self.store, viewer_team=self.team,
			viewer_member=self.member))

	def breadcrumb_text(self, summary: dict) -> str:
		"""The Jobs location trail. W25 moved the identity and the
		counters out of this string: identity is right-aligned by the
		header painter and the old `[oblig] [park] [due]` counters are
		gone, because Inbox owns owed action and Jobs owns parked Work.
		What is left is what the name always promised — where in the
		containment tree the operator is.

		W292 supersedes the ancestry re-read this used to do. The
		location is now the NAVIGATION path the operator actually walked
		— it starts at the top-level page and names one segment per
		drill-in — because a trail and a Back that describe different
		things is the ambiguity this Work exists to remove. The
		canonical Work ancestry still decides the SEGMENTS, at entry:
		`_enter_detail` seeds one Work frame per ancestor, so the two
		can never disagree.

		Empty at the top level: W74's rule that the root view has no
		breadcrumb is unchanged, and there the tab bar says where the
		operator is."""
		return self.nav_text()

	def top_tab_segments(self) -> list[tuple[str, str]]:
		"""`(tab name, drawn label)` in order, every label bracketed.

		The painter needs the PIECES, not the joined line: the Inbox
		label carries the urgency weight and the active label carries
		the selection weight, so a single string would force both onto
		all three tabs or none. `top_tabs()` joins exactly these
		pieces, so the text and the paint cannot disagree about where a
		label starts.

		W110 (finding-consistent-tui-tab-grammar) supersedes W25's
		rule that the brackets marked the ACTIVE tab. They now mark
		what is a TAB — the same grammar Work detail uses for
		Messages/Events — and the active one is highlighted instead. A
		bracket that means "selected" here and "this is a tab" one
		level down is a grammar an operator has to learn twice."""
		box = self.inbox_view()
		out = []
		for name in TABS:
			label = name.title()
			if name == "jobs":
				# W26328: the participant-actionable total, ALWAYS spelled
				# including zero. `[Jobs 0]` is an answer -- "nothing is
				# waiting for you" -- and omitting it when the count is zero
				# would leave an operator unable to tell that from a tab that
				# never says. It carries a COUNT rather than the `*` marker
				# Inbox and Teams use, because the question here is how much
				# and theirs is whether.
				#
				# From the SAME cached window the rows come from, so the
				# header and the table cannot describe two authority states.
				label += f" {self._window()['actionable_for_viewer']}"
			if name == "inbox" and box["owed_action"]:
				# W167 (finding-inbox-owed-marker) supersedes W25's
				# `total/unseen` here. Those are genuinely independent
				# projection fields, but most live row kinds are unseen
				# for their whole life or vanish when resolved, so the
				# label spent six cells reading `0/0` or `1/1` and
				# emphasised UNREADNESS — while the question an
				# operator has at a glance is whether they owe
				# anything. One ASCII marker answers exactly that. It
				# encodes no count, no severity and no unseen state,
				# and it comes from canonical `owed_action` rather than
				# from either counter: the numbers still exist, inside
				# Inbox and in the JSON, where their meaning is visible
				# beside the rows they describe.
				label += " *"
			if name == "teams" and self.teams_need_attention():
				# W2938 (finding-claim-overdue-cue): the persistent cue
				# while the operator is looking at Jobs. It uses the
				# SAME `*` vocabulary W167 chose for Inbox rather than
				# inventing a second alarm glyph, and it carries no
				# count: one star means Teams needs attention, and it
				# does not multiply with participants or Jobs. Pending
				# alone never stars — a grace period nobody has missed
				# yet is not attention.
				label += " *"
			out.append((name, f"[{label}]"))
		return out

	def teams_need_attention(self) -> bool:
		"""W2938: is ANY participant claim-overdue?

		Read through the same cached roster the Teams tab is drawn
		from, so the star and the rows it sends the operator to can
		never disagree — and so looking at Jobs costs no extra
		authority read."""
		roster = self._cached(("teams",), lambda: projection.teams(
			self.store, viewer_team=self.team,
			viewer_member=self.member))["teams"]
		return any(
			(member.get("pickup") or {}).get("state") == "overdue"
			for team in roster for member in team["members"])

	def top_tabs(self) -> str:
		"""`[Jobs]  [Teams]  [Inbox *]` — every tab, bracketed.

		Which one is ACTIVE is the paint's job (W110); this is the text
		of the bar. W167: Inbox carries one `*` when this participant
		OWES something, and nothing when they do not — the counts live
		inside the view and in the JSON."""
		return TAB_GAP.join(label for _name, label
		                    in self.top_tab_segments())

	def visible_tab_segments(self, width: int) -> list[tuple[str, str]]:
		"""The top-level segments that fit WHOLE, active one kept.

		W110 review R1: the budget is the room the labels ACTUALLY
		have, not `width - 1`. The participant identity is painted last
		and deliberately overdraws — that is its own guarantee, that no
		width can clip away who the operator is signed in as — so a
		label this function accepted could still be half-erased by the
		time the row was composed, leaving `[lang.ada` on screen. The
		identity region is therefore reserved HERE, where the decision
		is made, and the identity's own promise is untouched."""
		return fitted_tabs(self.top_tab_segments(), self.tab,
		                   self._tab_budget(width))

	def _tab_budget(self, width: int) -> int:
		"""The columns the tab bar may use before the right-aligned
		identity begins. One space separates them, so a label and a
		name never abut."""
		return max(0, width - 1 - len(self.participant) - 1)

	def _render_header(self, screen, width: int, summary) -> None:
		"""Row 0: the location, with the participant identity
		right-aligned. Identity is drawn LAST and overdraws, so no width
		can clip away who the operator is signed in as.

		W292: WHICH location depends on the one thing that decides it —
		whether the operator has drilled in. At a top-level page this is
		the global tab row, exactly as W25/W74/W110 built it. Inside any
		drilled page it is the breadcrumb for the whole path and the
		global row is ABSENT, because two tab rows on one screen imply
		two peer navigation surfaces when one of them is a drill-down
		inside the other. The local tabs of the drilled page are painted
		by that page, beneath this row."""
		if self.location:
			self._render_breadcrumb(screen, width)
			return
		box = self.inbox_view()
		tabs = self.top_tabs()
		# W25 review R1: the urgency weight belongs to the INBOX label
		# alone. Bolding the whole bar told the operator that something
		# was owed and then hid which tab held it — the one question the
		# cue exists to answer. Each label is painted at its own column
		# so exactly one of them can carry it; the joined string is the
		# same pieces, so the selected-tab brackets and the widths are
		# unchanged. Seen state still cannot quiet this: it follows
		# `owed_action`, not `unseen`.
		column = 0
		for name, label in self.visible_tab_segments(width):
			urgent = name == "inbox" and box["owed_action"]
			# W110: the two weights are independent facts and they
			# compose. REVERSE says which tab the keys act in; BOLD
			# still says only that Inbox is owed something, so an
			# operator sitting in Teams can see both at once and a
			# quiet Inbox never looks urgent for being selected.
			attr = (curses.A_REVERSE if name == self.tab else 0) \
				| (curses.A_BOLD if urgent else 0)
			screen.addnstr(0, column, label, width - 1 - column, attr)
			column += len(label) + len(TAB_GAP)
		trail = self.breadcrumb_text(summary) if self.tab == "jobs" \
			else ""
		if trail:
			screen.addnstr(0, min(len(tabs) + 2, max(0, width - 1)),
			               trail, max(0, width - 1 - len(tabs) - 2),
			               curses.A_BOLD)
		self._render_right_edge(screen, width)

	def _render_right_edge(self, screen, width: int) -> None:
		"""The right edge of row 0, painted the same way in BOTH header
		paths: dispatch state, then filter disclosure, then identity.

		W4615: the dispatch label goes here rather than in the top-level
		tab row alone, because a deployment-global state that disappears
		when the operator drills into a Work is exactly the fact they
		would then act without. Identity is still drawn LAST and still
		overdraws — the one promise no width may break — and the
		dispatch label sits furthest left of the three, so a narrow
		terminal loses it before it loses who the operator is."""
		dispatch = self._dispatch_tag()
		tag = self._filter_tag()
		# W5 (ruled): active filtering is ALWAYS disclosed. It shares the
		# right edge with the identity, so it sits just left of it
		# rather than under it. W292: the drilled header paints the same
		# tag from the same definition.
		if tag:
			at = width - 2 - len(tag) - len(self.participant)
			screen.addnstr(0, max(0, at), tag, width - 1, curses.A_BOLD)
		if dispatch:
			at = (width - 2 - len(dispatch) - len(self.participant)
			      - (len(tag) + 1 if tag else 0))
			if at > 0:
				screen.addnstr(0, at, dispatch, width - 1, curses.A_BOLD)
		screen.addnstr(0, max(0, width - 1 - len(self.participant)),
		               self.participant, width - 1, curses.A_BOLD)

	def dispatch_view(self) -> dict:
		"""The deployment-global dispatch state, through the ONE cached
		read path the rest of the console uses."""
		return self._cached(("dispatch",),
		                    lambda: projection.dispatch_view(self.store))

	def _dispatch_tag(self) -> str:
		"""W4615's header disclosure. ONE definition, like the filter
		tag's and for the same reason: the top-level header and every
		drilled header owe the operator the same fact.

		Empty while `running`. A label that is always present would
		train the eye to ignore it, and RUNNING is the state an operator
		already assumes — but DRAINING and PAUSED change what the
		console's own keys will do, so they are always said. The active
		count is on the DRAINING label because "how much longer" is the
		next question an operator asks."""
		state = self.dispatch_view()
		if state["mode"] == "running":
			return ""
		if state["mode"] == "paused":
			return "Dispatch:PAUSED"
		return f"Dispatch:DRAINING ({state['blocking_claims']} active)"

	def _filter_tag(self) -> str:
		"""W5's header disclosure, or empty. ONE definition, because the
		top-level header and every drilled header owe the operator the
		same fact and must not be able to disagree about when."""
		return f"Filter:{len(self.work_filter)}" \
			if self.work_filter and self.tab == "jobs" else ""

	def _render_breadcrumb(self, screen, width: int) -> None:
		"""The drilled location row: the complete path, then the right
		edge — an active filter's disclosure, then identity.

		Narrow terminals lose the OLDEST segments rather than the
		newest: where the operator is now is the fact they cannot
		afford to lose, and an elided head is announced with a leading
		`…` so a shortened trail never reads as a complete one. The
		identity keeps its own promise and overdraws last.

		W292 round-2 review: this used to paint the trail and identity
		and return, so `Filter:N` was reachable only at the top level.
		W292 supersedes the global TAB ROW inside a drill; it does not
		supersede W5's ruling that an active filter is ALWAYS disclosed
		in the header — and search results are themselves narrowed by
		that filter, so a drilled page with no disclosure showed a
		reduced result set with nothing saying why. Both right-edge
		units are reserved here, where the trail's room is decided, so
		neither can be half-erased by the other."""
		tag = self._filter_tag()
		dispatch = self._dispatch_tag()
		room = max(0, self._tab_budget(width)
		           - (len(tag) + 1 if tag else 0)
		           - (len(dispatch) + 1 if dispatch else 0))
		items = self.breadcrumb_items()
		selected = self.crumb_key if self.crumb_focus else items[-1]["key"]
		window = breadcrumb_window(items, selected, room)
		if not window:
			refusal = "(breadcrumb too narrow)"
			if len(refusal) <= room:
				screen.addnstr(0, 0, refusal, room, curses.A_BOLD)
		else:
			column = 0
			for index, piece in enumerate(window):
				if index:
					screen.addnstr(0, column, NAV_SEPARATOR,
					               room - column, curses.A_BOLD)
					column += len(NAV_SEPARATOR)
				attr = curses.A_BOLD
				if self.crumb_focus and piece["key"] == selected:
					attr |= curses.A_REVERSE
				screen.addnstr(0, column, piece["text"],
				               room - column, attr)
				column += len(piece["text"])
		self._render_right_edge(screen, width)

	# -- rendering ------------------------------------------------------------

	def render(self, screen) -> None:
		screen.erase()
		height, width = screen.getmaxyx()
		if self.tab != "jobs":
			# W25: Teams and Inbox are whole tabs, not modes inside the
			# Work tree. They share the header, the command bar and the
			# status row — everything an operator's hands already know —
			# and nothing else: neither reads a Work window, so neither
			# pays for one.
			self._render_header(screen, width, None)
			if self.tab == "teams":
				self._render_teams(screen, height, width)
			else:
				self._render_inbox(screen, height, width)
			self._render_bar(screen, height, width)
			return
		if self.mode == "table":
			# W336: the LIVE render path drains the countdown too — the
			# window comes through rows() (the countdown/observation
			# boundary); the summary re-read is served from the same
			# cached snapshot, never a second authority read.
			rows = self.rows()
			summary = self.view()[1]
			# W6814: from the SAME cached window as the rows above, so
			# an elision group and the ancestor it hangs from can never
			# come from two authority states.
			trails = self.trails()
		elif self.mode == "search":
			rows, trails = self.search_rows(), ()
			summary = self._cached(
				("summary",),
				lambda: projection.team_summary(
					self.store, viewer_team=self.team))
		else:
			trails = ()
			rows, summary = [], self._cached(
				("summary",),
				lambda: projection.team_summary(
					self.store, viewer_team=self.team))
		self._render_header(screen, width, summary)
		if self.mode == "detail":
			# W71 (ruled, superseding the main-screen split): the Work
			# detail view — Threads above, the selected Thread's
			# Messages below, Ctrl-W pane navigation.
			self._render_detail(screen, height, width)
		elif self.mode == "links":
			# W4996: `[b]` is the dependency NEIGHBOURHOOD now. The flat
			# blocked-by/blocks list it replaced showed the same edges
			# without ever showing the shape they make.
			self._render_graph(screen, height, width)
		elif self.mode == "pokes":
			# W17: the conversational pokes this participant is part of
			# — the ones owed an answer, and the ones they asked.
			self._render_pokes(screen, height, width)
		elif self.mode == "mine":
			# W26328: every Work awaiting THIS participant, flat, with
			# the complete path to each.
			self._render_mine(screen, height, width)
		elif self.mode == "search":
			# W6: the flat result table — ordinary row facts, the
			# closed-visibility rule, and a footer naming the result
			# page and controls.
			visible, _hidden = self.visible_rows(rows)
			more = "  (n: more)" if self.search_next is not None \
				else ""
			# R3: the bounded truth — a page label and the SHOWN
			# count, never a page count masquerading as a total.
			screen.addnstr(1, 0,
			               f"search: {self.search_query} — page "
			               f"{self.search_page} · {len(visible)} "
			               f"shown{more}",
			               width - 1, curses.A_DIM)
			if visible:
				self._render_table(screen, height, width, rows,
				                   top=2)
			else:
				screen.addnstr(3, 0,
				               f"(no matches for "
				               f"{self.search_query!r})", width - 1)
			screen.addnstr(
				height - 2, 0,
				"j/k select · Enter details · / new query · "
				"n/p page · Esc back", width - 1)
		else:
			# EVERY ROW ABOVE THE TABLE IS ALLOCATED FROM ONE RUNNING
			# CURSOR. W6814 review [P1]: the filter branch painted at a
			# LITERAL row 1 and then reset the cursor to a literal 2, so
			# on a re-rooted page whose filter survived the re-root the
			# clause text overpainted the contextual tab row — leaving
			# `filter: status=open [Events]`, which is one disclosure
			# destroyed and the other made misleading.
			#
			# Both rows are required and neither is optional to the
			# other: W5 rules that an active filter is ALWAYS disclosed,
			# and W6814 rules that a contextual Work page always shows
			# which of its three tabs it is on. Two independent rules
			# writing to one hard-coded row is how one of them silently
			# wins.
			table_top = 1
			if self.context_work():
				# W6814: the contextual Work page's own tabs sit
				# directly under the breadcrumb, above the tree the
				# `Jobs` tab is showing.
				self._paint_tab_row(screen, table_top, width, "jobs")
				table_top += 1
			if self.work_filter:
				# The dedicated normalized-clause line; horizontally
				# viewported at narrow widths, never silently dropped.
				clauses = "filter: " + self._filter_clauses()
				if len(clauses) > width - 1:
					clauses = clauses[:max(0, width - 2)] + "…"
				screen.addnstr(table_top, 0, clauses, width - 1,
				               curses.A_DIM)
				table_top += 1
			self._render_table(screen, height, width, rows,
			                   top=table_top, trails=trails, mine=True)
		self._render_bar(screen, height, width)

	# -- W25: the Inbox tab ----------------------------------------------

	def inbox_rows(self) -> list[dict]:
		"""Owed rows first, then attention — the Inbox is read top-down
		by somebody deciding what to do next, and the things they are
		the blocker for are what that decision is about."""
		rows = list(self.inbox_view()["rows"])
		rows.sort(key=lambda row: not row["owed"])
		return rows

	def _inbox_selected(self) -> dict | None:
		rows = self.inbox_rows()
		if not rows:
			return None
		# The `is not None` guard is load-bearing: an attention row has
		# no action key, so a null ANCHOR would match the first such row
		# and silently move the operator's selection onto it.
		if self.inbox_key is not None:
			for index, row in enumerate(rows):
				if self.inbox_key in (row["action_key"],
				                      row["selector"]):
					self.inbox_cursor = index
					return row
		self.inbox_cursor = min(self.inbox_cursor, len(rows) - 1)
		chosen = rows[self.inbox_cursor]
		self.inbox_key = chosen["action_key"] or chosen["selector"]
		return chosen

	@staticmethod
	def _inbox_cells(row: dict) -> dict:
		"""One Inbox row's cells. `Do` is the action in WORDS and `Type`
		is what the row IS — W228's ruling that an actionable row must
		be legible without colour or weight, applied to a surface whose
		whole job is telling those two apart."""
		return {
			# W93 slice 5: a runtime row is `attend` — the runner is
			# waiting on a HUMAN in its own session and Baton has no
			# verb that answers it. Saying `read` would advertise an
			# action the operator cannot take here.
			# W415: an incident is DISMISSED, and deliberately never
			# `approve`. The corrective action is to repair the
			# deployment/rule mismatch or reroute the Work; an approve
			# here would rebuild the interactive path one console away
			# from the dispatcher that refuses it.
			"Do": ("answer" if row["kind"] == "poke" else
			       "respond" if row["kind"] == "obligation" else
			       "assess" if row["kind"] == "due_trial" else
			       "attend" if row["kind"] == "runtime" else
			       "dismiss" if row["kind"] == "incident" else "read"),
			"Type": row["kind"].replace("_", " "),
			"Seen": "seen" if row["seen"] else "new",
			"Context": (_local_selector(row["work"]) if row["work"]
			            else "-"),
			"What": " ".join(str(row["summary"] or "").split()),
		}

	def _render_inbox(self, screen, height, width) -> None:
		"""What this participant owes and has not seen.

		Every value is the canonical projection's. Opening the tab
		neither answers anything nor marks anything seen: `s` is the
		only thing that moves a seen cursor, and it runs the public
		verb."""
		box = self.inbox_view()
		rows = self.inbox_rows()
		note = (f"inbox — {box['owed']} owed · {box['unseen']} unseen "
		        f"· {box['total']} total")
		screen.addnstr(1, 0, note, width - 1, curses.A_DIM)
		footer = height - 2
		if not rows:
			screen.addnstr(3, 0, "(nothing owed and nothing unseen)",
			               width - 1)
			screen.addnstr(footer, 0, "[/] tabs", width - 1)
			return
		selected = self._inbox_selected()
		cells = {row["selector"]: self._inbox_cells(row)
		         for row in rows}
		id_width = max(len(row["selector"]) for row in rows)
		columns = []
		for name, floor in (("Do", 2), ("Type", 4), ("Seen", 4),
		                    ("Context", 7)):
			columns.append((name, max(floor, max(
				len(cells[row["selector"]][name]) for row in rows))))
		used = id_width + sum(size + 1 for _name, size in columns)
		columns.append(("What", max(8, width - 2 - used)))
		header = "Id".ljust(id_width)
		for name, size in columns:
			header += " " + name.ljust(size)
		screen.addnstr(2, 0, header[:width - 1], width - 1,
		               curses.A_UNDERLINE)
		listing = max(1, footer - 5)
		start = max(0, min(self.inbox_cursor - listing + 1,
		                   len(rows) - listing))
		start = max(0, start)
		shown = rows[start:start + listing]
		for offset, row in enumerate(shown):
			text = row["selector"].ljust(id_width)
			for name, size in columns:
				text += " " + cells[row["selector"]][name][:size] \
					.ljust(size)
			attribute = 0
			if start + offset == self.inbox_cursor:
				attribute = curses.A_REVERSE
			elif row["owed"]:
				attribute = curses.A_BOLD
			screen.addnstr(3 + offset, 0, text[:width - 1], width - 1,
			               attribute)
		if selected:
			top = 3 + len(shown) + 1
			for offset, line in enumerate(
					self._inbox_detail(selected, width)):
				if top + offset >= footer:
					break
				screen.addnstr(top + offset, 0, line, width - 1)
		bits = ["j/k select"]
		if selected and selected["kind"] == "poke":
			bits.append("a answer")
		elif selected and selected["kind"] == "obligation":
			bits.append("a respond")
		if selected and selected["work"]:
			bits.append("Enter open in Jobs")
		if selected and selected["thread"]:
			bits.append("s mark seen")
		bits.append("[/] tabs")
		screen.addnstr(footer, 0, " · ".join(bits), width - 1)

	def _inbox_detail(self, row: dict, width: int) -> list[str]:
		"""The chosen row in full, including the verbs that satisfy it —
		an operator reads what would discharge this without going to the
		grammar for it."""
		lines = [f"{row['selector']} — {row['kind'].replace('_', ' ')}"
		         + ("  (you owe this)" if row["owed"]
		            else "  (attention only)")
		         + ("" if row["seen"] else "  · unseen")]
		for part in str(row["summary"] or "").splitlines():
			lines.append(f"  {part}")
		if row["unseen_count"]:
			lines.append(f"  {row['unseen_count']} unseen message(s) "
			             f"in {_local_selector(row['thread'])}")
		if row["kind"] == "runtime":
			lines.append("  the runner is waiting on a person in its own "
			             "session; Baton has no verb that answers it, "
			             "and the row clears when the adapter reports "
			             "what happened next")
		if row["kind"] == "incident":
			lines.append(f"  {row['participant']} · {row['category']} · "
			             f"{row['cause']}"
			             + (f" · episode {row['episode']}"
			                if row["episode"] is not None else ""))
			if row["occurrences"] > 1:
				lines.append(f"  this has happened {row['occurrences']} "
				             f"times; the first repair did not hold")
			if row["work"]:
				lines.append(f"  {_local_selector(row['work'])} was NOT "
				             f"claimed and is still waiting; dismissing "
				             f"this incident does not pick it up")
			lines.append("  the fix is to repair the deployment/rule "
			             "mismatch or reroute the Work — there is no "
			             "approve, because a managed turn is "
			             "non-interactive by ruling")
			lines.append("  it stays here through idle transitions, "
			             "refreshes and restarts until you dismiss it")
		if row["completes_by"]:
			lines.append("  satisfied by: "
			             + ", ".join(row["completes_by"]))
		out: list[str] = []
		for line in lines:
			out.extend(soft_wrap(line, max(8, width - 1)))
		return out

	# -- W25: the Teams tab ----------------------------------------------

	def team_rows(self) -> list[dict]:
		"""The roster, own team first (ruled default) and every other
		configured team after it — deliberate navigation, not a wall of
		strangers on open."""
		roster = self._cached(("teams",), lambda: projection.teams(
			self.store, viewer_team=self.team,
			viewer_member=self.member))["teams"]
		rows = []
		for entry in sorted(roster, key=lambda team: not team["mine"]):
			if self.teams_own_only and not entry["mine"]:
				continue
			for member in entry["members"]:
				rows.append(member)
		return rows

	def _team_selected(self) -> dict | None:
		rows = self.team_rows()
		if not rows:
			return None
		for index, row in enumerate(rows):
			if row["participant"] == self.team_member:
				self.team_cursor = index
				return row
		self.team_cursor = min(self.team_cursor, len(rows) - 1)
		chosen = rows[self.team_cursor]
		self.team_member = chosen["participant"]
		return chosen

	@staticmethod
	def _team_cells(row: dict) -> dict:
		"""Workflow facts and RUNNER facts, side by side and never
		merged.

		W93 slice 5: `Agent` is the runner FAMILY and `State` is what
		that runner is doing — both from the canonical runtime lease,
		neither inferred from the participant's name or from the Work
		it holds. `Work` is the authority's answer about what this
		member is executing; `Session` is the exact locator, in FULL —
		W137: fitting it is the layout's job, and pre-truncating here
		decided the width before the layout knew what it had; `Since`
		is when the runner's state last changed. `-` throughout means
		the authority holds no such fact, which is never the same as a
		reassuring one."""
		runtime = row.get("runtime") or {}
		held = row["handled_work"]
		return {
			"Role": ",".join(row["roles"]) or "-",
			"Agent": runtime.get("adapter") or "-",
			"State": AGENT_LABELS.get(runtime.get("state"),
			                          runtime.get("state") or "-"),
			"Work": (_local_selector(held[0]["work"]) if held
			         else "-"),
			# W137: the WHOLE locator. Pre-truncating here decided
			# the width before the layout knew what it had, so a wide
			# terminal could not recover a value the record held all
			# along. Fitting is the layout's job and happens once.
			"Session": runtime.get("session") or "-",
			# W93 review R15: ELAPSED time in the current state, in the
			# one MM:SS/∞ vocabulary every other duration cell uses —
			# not an absolute instant, which spent sixteen cells saying
			# something the operator has to subtract. The absolute
			# instants stay in the member detail block below.
			"Since": held_cell(runtime.get("since"), _time.time()),
			# W2938: `-` owes nothing (busy, no actionable Work, or not
			# eligible), `pend` is inside the accepted threshold, `late`
			# is at or beyond it. Compact because this is a table cell
			# and the member detail below spells it out; the STATE is
			# canonical and the wording is presentation, which is why
			# JSON clients read `pickup.state` and never this.
			"Pickup": PICKUP_LABELS.get(
				(row.get("pickup") or {}).get("state"), "-"),
		}

	def _render_teams(self, screen, height, width) -> None:
		rows = self.team_rows()
		scope = "own team" if self.teams_own_only else "every team"
		screen.addnstr(1, 0, f"teams — {len(rows)} member(s), {scope}",
		               width - 1, curses.A_DIM)
		footer = height - 2
		if not rows:
			screen.addnstr(3, 0, "(no configured members)", width - 1)
			screen.addnstr(footer, 0, "t all teams · [/] tabs",
			               width - 1)
			return
		selected = self._team_selected()
		cells = {row["participant"]: self._team_cells(row)
		         for row in rows}
		# W137: the natural widths are measured from the cells that
		# EXIST, and the fitting happens once, in one place. The old
		# shape measured content, computed a `used` total, and then
		# threw it away — so the table stayed as narrow as its floors
		# no matter how much terminal it had been given.
		natural = {name: max([len(name)] + [
			len(cells[row["participant"]][name]) for row in rows])
			for name, _floor, _cap in TEAM_COLUMNS}
		id_width, columns = team_layout(
			width, max(len(row["participant"]) for row in rows), natural)
		header = "Participant".ljust(id_width)
		for name, size in columns:
			header += " " + _fit(name, size)
		screen.addnstr(2, 0, header[:width - 1], width - 1,
		               curses.A_UNDERLINE)
		# W184: the detail block is a table now and needs real room, so
		# the LIST gives it a fair share instead of taking everything
		# up to the old floor. The selected member is always visible
		# because the window follows the cursor below.
		listing = max(1, min(len(rows),
		                     (footer - 4) // 2 if selected
		                     else footer - 4))
		start = max(0, min(self.team_cursor - listing + 1,
		                   len(rows) - listing))
		start = max(0, start)
		shown = rows[start:start + listing]
		for offset, row in enumerate(shown):
			text = _fit(row["participant"], id_width)
			for name, size in columns:
				text += " " + _fit(cells[row["participant"]][name],
				                   size)
			attribute = curses.A_REVERSE \
				if start + offset == self.team_cursor else 0
			# W2938: an OVERDUE member's row is bold — the reason the
			# `[Teams*]` star sent the operator here, so it has to be
			# findable without reading every Pickup cell. It composes
			# with the selection highlight rather than replacing it, so
			# an overdue row the cursor is on stays visibly both.
			if (row.get("pickup") or {}).get("state") == "overdue":
				attribute |= curses.A_BOLD
			elif row["participant"] == self.participant and not attribute:
				attribute = curses.A_BOLD
			screen.addnstr(3 + offset, 0, text[:width - 1], width - 1,
			               attribute)
		if selected:
			top = 3 + len(shown) + 1
			detail = self._team_detail(selected, width)
			budget = max(0, footer - top)
			if len(detail) > budget:
				# The pokes view's ruled shape: say how much is not on
				# screen and name where the whole record is, rather
				# than stopping mid-table and looking complete. W184
				# made this block taller by giving every fact its own
				# row, which is the point — so a short terminal has to
				# be honest about what it cut.
				hidden = len(detail) - max(0, budget - 1)
				detail = detail[:max(0, budget - 1)] + [
					f"  … {hidden} more row(s) — `teams` has the whole "
					f"record"]
			for offset, line in enumerate(detail):
				if top + offset >= footer:
					break
				screen.addnstr(top + offset, 0, line, width - 1)
		bits = ["j/k select", "p poke"]
		if self._pending_poke_to(selected) is not None:
			bits.append("x withdraw")
		bits.append("t own/all teams")
		bits.append("[/] tabs")
		screen.addnstr(footer, 0, " · ".join(bits), width - 1)

	def _team_detail(self, row: dict, width: int) -> list[str]:
		"""One member in full, as a two-column table.

		W184 (finding-teams-member-detail-table) supersedes the prose
		form. The authority already exposes these as typed fields, and
		flattening them into sentences threw away the one thing
		structure gives an operator: somewhere to look. Labels started
		at different columns and several facts shared a line, so
		finding one field meant rereading the block.

		Every fact keeps its OWN key — provider, model, session,
		incarnation, state, cause, transition time, last contact and
		each operational fact — because combining unrelated facts to
		save a row is what made the old block unscannable. `unknown`,
		`-` and "never published" stay visibly different from each
		other: a renderer that tidies an absent fact into a reassuring
		one is lying about what the authority holds."""
		runtime = row.get("runtime") or {}
		sections = [
			("Identity and routing", self._detail_identity(row)),
			("Workflow", self._detail_workflow(row)),
			("Claim pickup", self._detail_pickup(row)),
			("Runner state", self._detail_runner(runtime)),
			("Operational diagnostics", self._detail_facts(runtime)),
			("Last poke answer", self._detail_answer(row)),
		]
		head = f"{row['participant']} — {row['display']}"
		return soft_wrap(head, max(8, width - 1)) \
			+ kv_lines(sections, max(8, width - 1))

	@staticmethod
	def _detail_identity(row: dict) -> list[tuple[str, str]]:
		pairs = [("Participant", row["participant"]),
		         ("Display", row["display"]),
		         ("Roles", ", ".join(row["roles"]) or "none")]
		for entry in row["routes"]:
			pairs.append(("Route", f"{entry['route']} ({entry['role']}): "
			              + (", ".join(entry["endpoints"])
			                 or "no live endpoint")))
		if not row["routes"]:
			pairs.append(("Route", "none — no Work can be routed here"))
		return pairs

	@staticmethod
	def _detail_workflow(row: dict) -> list[tuple[str, str]]:
		if not row["handled_work"]:
			return [("Holding", "nothing")]
		return [("Holding", f"{_local_selector(held['work'])} "
		         f"[{held['phase']}] {held['title']}")
		        for held in row["handled_work"]]

	@staticmethod
	def _detail_pickup(row: dict) -> list[tuple[str, str]]:
		"""W2938: the participant's ONE claim obligation, spelled out.

		The table cell is four characters; here there is room for the
		word, how long it has been owed, and what to do about it. The
		suggested Work is DIAGNOSTIC — the obligation belongs to the
		participant, and claiming ANY eligible Work discharges it, so
		the row says `suggested next claim` rather than naming an owner.

		Absent entirely when nothing is owed: a member who is busy, has
		no actionable Work, or is not eligible has no pickup to report,
		and a permanent `Pickup -` row would be a cell repeating that
		the section does not apply."""
		pickup = row.get("pickup") or {}
		state = pickup.get("state")
		if state is None:
			return []
		pairs = [("Pickup", state),
		         ("Waiting", duration_cell(pickup.get("elapsed_seconds"))),
		         ("Since", local_stamp(pickup.get("since")) or "-")]
		suggested = pickup.get("next_work")
		if suggested:
			pairs.append(("Suggested next claim",
			              f"{suggested['local_id']} {suggested['title']}"))
		return pairs

	@staticmethod
	def _detail_runner(runtime: dict) -> list[tuple[str, str]]:
		"""The runtime lease, one fact per row.

		A participant whose adapter has never opened a lease gets ONE
		row saying exactly that, rather than a dozen rows of `-` that
		would read as a runner reporting nothing."""
		state = runtime.get("state")
		if state in (None, "offline") and not runtime.get("incarnation"):
			return [("Lease", "none — this participant's adapter has "
			         "never published runtime state")]
		pairs = [("State", f"{state} ({runtime.get('provenance')})"),
		         ("Cause", runtime.get("cause") or "-"),
		         ("Detail", runtime.get("detail") or "-"),
		         ("Adapter", runtime.get("adapter") or "-"),
		         ("Provider", runtime.get("provider") or "-"),
		         ("Model", runtime.get("model") or "-"),
		         ("Session", runtime.get("session") or "-"),
		         ("Incarnation", runtime.get("incarnation") or "-"),
		         ("Since", local_stamp(runtime.get("since")) or "-"),
		         ("Last contact",
		          local_stamp(runtime.get("last_contact")) or "-"),
		         ("Lease expires",
		          local_stamp(runtime.get("expires_at")) or "-"),
		         # Its own row: the deadline and whether it has passed
		         # are different facts, and a reader should not have to
		         # subtract one from the clock to learn the other.
		         ("Stale", "yes" if runtime.get("stale") else "no")]
		if runtime.get("action_owner"):
			pairs.append(("Action owner",
			              f"interactive answers owed by "
			              f"{runtime['action_owner']}"))
		if runtime.get("refresh_requested"):
			pairs.append(("Refresh",
			              f"asked at "
			              f"{local_stamp(runtime['refresh_requested'])}"
			              f" — awaiting the adapter's next poll"))
		if runtime.get("note"):
			pairs.append(("Note", runtime["note"]))
		return pairs

	@staticmethod
	def _detail_facts(runtime: dict) -> list[tuple[str, str]]:
		"""The safe operational inventory, each fact with its own
		source and age — they age SEPARATELY from the state above, so
		showing them together would make the older look as live as the
		newer.

		This is an inventory of what an adapter ACTUALLY published, so
		it holds exactly those facts and invents no row for one that is
		absent — `log` included.

		W1578 (finding-omit-unpublished-member-log, 2026-08-20)
		supersedes W184's rule that a missing `log` must render a
		`not published` row. W184's reasoning was that an operator
		hunting for the log should be told it was never published
		rather than left to guess a path — but in the live deployment
		EVERY member said it, so the sentence disclosed nothing while
		costing a wide row per participant. An absent key in an
		inventory already means the adapter did not publish it, which
		is the same fact the row was spelling out. W184's published-log
		rule is unchanged: a locator that exists still appears verbatim
		with its source and age."""
		held = {fact["key"]: fact for fact in runtime.get("facts") or []}
		return [(key.replace("-", " ").capitalize(),
		         f"{fact['value']}  [{fact['source']} · "
		         f"{held_cell(fact['observed_at'], _time.time())} ago]")
		        for key, fact in held.items()]

	@staticmethod
	def _detail_answer(row: dict) -> list[tuple[str, str]]:
		"""What the AGENT said when it was last asked, which is a
		different kind of evidence from what its adapter observed."""
		answer = row["last_answer"]
		if answer is None:
			return [("Said", "never asked — no poke has been answered "
			         "by this participant")]
		runner = answer["runner"]
		pairs = [("Said", answer["state"]),
		         ("At", local_stamp(answer["at"])),
		         ("Explanation", answer["explanation"]),
		         ("Provider", runner["provider"]),
		         ("Model", runner["model"]),
		         ("Session state", runner["session_state"]),
		         ("Auth state", runner["auth_state"]),
		         ("Limit state", runner["limit_state"])]
		if runner["retry_at"]:
			pairs.append(("Retry at", local_stamp(runner["retry_at"])))
		telemetry = answer["telemetry"]
		if any(value is not None for value in telemetry.values()):
			# W184 review R1: the three counters are supplied
			# INDEPENDENTLY, so a partial answer is ordinary rather
			# than exceptional. Handing the raw value to `kv_lines`
			# renders an absent one as this table's `-`; `str()` here
			# printed Python's `None`, which is an implementation
			# word and not Baton's absent-value vocabulary. The keys
			# stay whatever arrives, so what the agent reported and
			# what it left out remain separate facts.
			pairs.append(("Context used", telemetry["context_used"]))
			pairs.append(("Context limit", telemetry["context_limit"]))
			pairs.append(("Context remaining",
			              telemetry["context_remaining"]))
		return pairs

	def _pending_poke_to(self, member) -> int | None:
		"""The poke THIS participant has outstanding to that member, if
		any — the one a withdrawal would act on."""
		if member is None:
			return None
		rows, _older = self.poke_rows()
		for row in rows:
			if row["mine"] and row["target"] == member["participant"] \
					and row["state"] == "pending":
				return row["poke"]
		return None

	def _render_bar(self, screen, height: int, width: int) -> None:
		"""The bottom row and the caret — the command bar, the batch
		buffer, the search entry, the modal prompts, the status line
		and the poke cue, in their ruled precedence.

		W25 gave this its own painter because all three tabs end in
		the same row: an operator's hands do not change tab, and a
		second copy of this precedence would be a second set of
		rules to keep in step."""
		if self.crumb_focus and self.location:
			self._render_breadcrumb_footer(screen, height, width)
		caret = None
		if self.confirm_exit:
			# One row, drawn whole at any width the console accepts.
			screen.addnstr(height - 1, 0, "Exit? y/N", width - 1)
		elif self.poke_choice is not None:
			# W17: the one operand a human cannot be asked to guess.
			# `state=` is a closed vocabulary and the grammar owns it,
			# so the prompt enumerates whatever the grammar accepts and
			# a later state appears here without a second list to edit.
			offer = " · ".join(
				f"{index + 1} {state}" for index, state
				in enumerate(poke_answer_states()))
			screen.addnstr(height - 1, 0,
			               f"Answer poke {self.poke_choice} — state? "
			               f"{offer} · Esc cancel", width - 1)
		elif self.batch is not None:
			caret = self._render_batch(screen, height, width)
		elif self.search_input is not None:
			typed = "/" + self.search_input
			avail = width - 1
			if len(typed) < avail:
				screen.addnstr(height - 1, 0, typed, avail)
				caret = (height - 1, len(typed))
			else:
				tail = typed[len(typed) - (avail - 2):]
				screen.addnstr(height - 1, 0, "<" + tail, avail)
				caret = (height - 1, 1 + len(tail))
		elif self.command is not None:
			# W14: the input owns the row, with a VISIBLE caret at the
			# insertion point. When it fits, the assistance renders DIM
			# on the right of the remaining space, yielding entirely
			# below 8 free cells. When the input outgrows the row, a
			# horizontal viewport keeps the caret and the live tail
			# visible — `<` marks the clipped left; the BUFFER itself
			# is never cut, so a wider resize (recomputing this
			# viewport from the same buffer) shows it whole again.
			# W26: while reverse search is open the row shows the
			# query and its match instead of the ordinary buffer, so
			# the operator can always see WHICH command Enter would
			# submit. The caret sits in the query, which is what is
			# being edited.
			if self.reverse is not None:
				found = self.reverse["match"]
				shown = "" if found is None else self.history[found]
				avail = width - 1
				# W26 R2: reverse search obeys the SAME viewport rule as
				# ordinary entry, because it is ordinary entry — typing
				# appends to the query, so the insertion point is the
				# query's end. Painting `row[:avail]` showed the OLDEST
				# prefix and then parked the caret on the last cell: the
				# caret sat on unrelated text while every character
				# being typed was off-screen.
				#
				# Three things compete for the row, and they are ranked.
				# The identity comes first — an operator who cannot see
				# `(reverse-i-search)` does not know which mode Enter
				# will act in. The live query tail comes second. The
				# match comes last: it is the RESULT, and a result that
				# crowds out the input it came from is backwards.
				head = "(reverse-i-search)`"
				# the space after the closing quote SEPARATES the query
				# from the match; with no match there is nothing to
				# separate, and on a narrow row that cell is better
				# spent on the query the operator is typing.
				joint = "': " if found is not None else "':"
				room = avail - len(head) - len(joint)
				if room < 1:
					# Degenerate width: keep the identity and put the
					# caret at its end. Nothing else fits, and inventing
					# a second, shorter spelling of the prompt would
					# make the mode unrecognizable exactly when the
					# operator most needs to recognize it.
					screen.addnstr(height - 1, 0, head[:avail], avail,
					               curses.A_DIM if found is None else
					               curses.A_NORMAL)
					caret = (height - 1, max(0, min(len(head),
					                                avail - 1)))
				else:
					query = self.reverse["query"]
					# `<` marks the clipped left, exactly as ordinary
					# entry marks it. The stored query is NEVER cut —
					# a wider resize recomputes this viewport from the
					# intact value and shows it whole again.
					clipped = query if len(query) <= room \
						else "<" + query[-(room - 1):]
					# The ranking is enforced ABOVE, by computing
					# `room` from the fixed parts alone: the query gets
					# its space before the match is considered at all.
					# Appending the whole match here needs no bookkeeping
					# — the paint below clips the row to the cell, which
					# is the same thing said once instead of twice.
					row = head + clipped + joint + shown
					# DIM when nothing matches, so a query that has
					# narrowed to nothing is visibly distinct from one
					# that found something.
					screen.addnstr(height - 1, 0, row[:avail], avail,
					               curses.A_DIM if found is None else
					               curses.A_NORMAL)
					# the caret sits at the END of the query, which is
					# where typing lands — the match beside it is the
					# result, not input
					caret = (height - 1,
					         min(len(head) + len(clipped),
					             max(0, avail - 1)))
			else:
				typed = ":" + self.command
				avail = width - 1
				# W35: ONE caret-aware window serves both the fitting
				# and the scrolled case. The old code had two branches
				# and put the caret at the end of the buffer in each,
				# which is the whole defect: the bar could only ever
				# append.
				visible, column = command_window(
					typed, 1 + self.command_caret, avail)
				screen.addnstr(height - 1, 0, visible, avail)
				caret = (height - 1, min(column, max(0, width - 1)))
				if visible == typed:
					room = avail - _cells(typed) - 2
					if room >= 8:
						if self.command_note:
							# W36: an editor that refused or cancelled
							# has to say so BESIDE the draft it just
							# handed back, because the status row is
							# behind the reopened bar.
							hint = self.command_note
						elif self.command.strip() == "filter" and \
								self.work_filter:
							# W5 (ruled): command entry exposes the
							# current clauses — SPACE seeds them into
							# the buffer for editing; bare Enter
							# clears.
							hint = ("current: "
							        + self._filter_clauses()
							        + " · space edits · Enter clears")
						else:
							hint = assist_text(self.command)
						screen.addnstr(height - 1, _cells(typed) + 2,
						               hint[:room], room, curses.A_DIM)
		elif self.status:
			screen.addnstr(height - 1, 0, self.status, width - 1)
		elif self.tab == "jobs" and self.mode != "pokes" \
				and self.owed_pokes():
			# W17: the counter says a poke is waiting; this says what to
			# press. It is derived from the same cached pending set at
			# paint time — nothing stores it — so answering the last
			# poke removes it on the next refresh, and it never displaces
			# the operator's own command feedback above.
			owed = len(self.owed_pokes())
			screen.addnstr(height - 1, 0,
			               f"{owed} poke{'' if owed == 1 else 's'} "
			               f"waiting for you — Tab to Inbox, or p for "
			               f"the poke record", width - 1,
			               curses.A_BOLD)
		# The caret exists exactly while the bar is open: shown at the
		# insertion point during entry, hidden again the moment the
		# bar closes. (A terminal refusing cursor-visibility control
		# keeps its own default — the row still renders identically.)
		try:
			curses.curs_set(1 if caret else 0)
		except curses.error:
			pass
		if caret:
			screen.move(*caret)
		screen.refresh()

	def _render_breadcrumb_footer(self, screen, height: int,
	                              width: int) -> None:
		items = self.breadcrumb_items()
		keys = [item["key"] for item in items]
		at = keys.index(self.crumb_key) if self.crumb_key in keys \
			else len(items) - 1
		prefix = (f"breadcrumb {at + 1}/{len(items)}: "
		          f"{items[at]['compact']}")
		available = max(0, width - 1)
		if len(prefix) > available:
			text = "(breadcrumb too narrow)"
		else:
			clauses = [prefix, "h/l select", "Enter open", "Down page",
			           "Esc back"]
			text = clauses[0]
			for clause in clauses[1:]:
				candidate = text + " · " + clause
				if len(candidate) > available:
					break
				text = candidate
		# Replace the page-specific help row completely; command/status
		# input remains on its independent bottom row.
		screen.addnstr(height - 2, 0, " " * available, available)
		screen.addnstr(height - 2, 0, text, available, curses.A_DIM)

	def _row_cells(self, row: dict) -> dict:
		"""Every drawable cell for one projection row — canonical values
		through the closed compact maps, nothing computed here."""
		return {
			"OUT": outcome_cell(row),
			"PR": compact_priority(row["priority"]),
			# W15: Phase is the operational stage alone. The claimant
			# cue lives in Handler, which is blank when unclaimed.
			"PHASE": phase_cell(row["status"], row["phase"]),
			"CLS": compact_classification(row["classification"]),
			# W36: conversation volume and MY directed load, combined
			# compactly here only — the canonical fields stay separate.
			"MSG/MY": f"{row['message_count']}"
			          f"/{row['my_pending_obligations']}",
			# W33: presentation-derived from the canonical claimed_at
			# and the local clock at paint time — advanced by the ONE
			# existing refresh cadence, no second scheduler.
			"HELD": held_field(row, _time.time()),
			# W35: two facts, two cells. ENDPOINT is the stable address
			# a reader types; VIA is the selected route that decides who
			# may claim it — and it comes from the SAME resolved route
			# object the authorization uses, so the table can never show
			# a route the claim would refuse.
			"ENDPOINT": row["route"]["endpoint"] if row["route"] else "-",
			"VIA": (row["route"]["route"] or "-") if row["route"]
			       else "-",
			# W245/W38: the exact claimant, or `-` when NOBODY holds
			# it. Phase says whether the Work is running; this says who
			# is running it.
			"HANDLER": (f"{row['handler']['team']}."
			            f"{row['handler']['member']}")
			if row["handler"] else "-",
			# W93 slice 5: what the HANDLER's runner is doing, never
			# inferred from Phase or Handler — the canonical projection
			# answers it, and `-` means nobody holds this Work rather
			# than anything about a runner.
			"RUN": agent_cell(row.get("agent")),
			"NEXT": row["next"]["endpoint"] if row["next"] else "-",
		}

	def _render_table(self, screen, height, width, rows,
	                  top: int = 1, trails=(), mine: bool = False) -> None:
		# W26328: `mine` is the VIEW's question, exactly as `terminal`
		# and `claimed` are — the ordinary containment tree carries the
		# `Mine` column and nothing else does. Deriving it from whether
		# the rows happen to have the members would make the column
		# appear and vanish with the data, and would silently paint it
		# on the flattened `Awaiting me` page, where every row is
		# actionable and a column saying so of all of them says
		# nothing.
		# W4 R1: the Id width comes from the rows ACTUALLY painted in
		# this view — a collapsed closed row must not consume Title
		# space or drop columns until `z` exposes it. The W39
		# dependency cue is scoped the same way, and is ONE whole
		# optional responsive field: when it alone breaks the fit it is
		# omitted entirely (never clipped); `[d] deps` stays available.
		visible, hidden = self.visible_rows(rows)
		# W6814: the physical display stream — the ordinary rows plus,
		# under each anchor, one non-selectable elision line and the
		# active Work this window hides beneath it. `selectable` is what
		# the cursor, the Id/cue budgets and every key see, so a trail
		# Work is an ordinary row to all of them and the elision is
		# invisible to all of them.
		stream = tree_stream(visible, trails)
		selectable = [entry["row"] for entry in stream
		              if entry["kind"] == "work"]
		id_width = id_column_width(selectable)
		cue_width = cue_column_width(selectable)
		# W26328: `Mine` is MANDATORY on this surface, so it joins the
		# identity allocation rather than the responsive column set.
		# Being in `COLUMNS` would put it in some drop position, and a
		# column that answers "is any of this mine" is worth less than
		# nothing if the widths at which an operator most needs a
		# summary are exactly the widths that drop it.
		mine_width = mine_column_width(selectable) if mine else 0
		mandatory = id_width + ((1 + mine_width) if mine_width else 0)
		# W73: the Out column is part of the budget exactly when the
		# view can hold terminal Work, so every fit judgment below
		# carries the same answer.
		terminal = self.terminal_visible()
		if cue_width and not layout_fits(
				width, mandatory + 1 + cue_width, terminal):
			cue_width = 0
		lead = mandatory + ((1 + cue_width) if cue_width else 0)
		if not layout_fits(width, lead, terminal):
			columns = visible_columns(width, lead, terminal)
			need = sum(w for _n, w in columns) + len(columns) + \
				MIN_TITLE + id_width + 2
			# The explicit too-narrow REFUSAL (ruled): identities are
			# never truncated into ambiguity to fake a fit — and (W4
			# R2) an over-wide identity refuses the table rather than
			# clipping the mandatory tail.
			screen.addnstr(top, 0,
			               f"(terminal too narrow: need {need} cells)",
			               width - 1)
			return
		# W4: the exact Id column LEADS the table and never truncates —
		# it grows to the longest visible selector; the responsive drop
		# budget carries it, and the title absorbs the remainder.
		claimed = any(row.get("handler") for row in selectable)
		columns = visible_columns(width, lead, terminal, claimed)
		fixed = sum(w for _n, w in columns) + len(columns)
		title_width = max(MIN_TITLE, width - fixed - lead - 2)
		# Trial finding 26de18dd-W2: headers draw initial-capital LABELS
		# (Title, St, Phase, ...); the canonical projection fields and
		# the internal responsive-column identifiers stay unchanged.
		header = "Id".ljust(id_width) + " " + "Title".ljust(title_width)
		if cue_width:
			# W187: `Wait` — what this row waits on; `Blk` read
			# ambiguously between blocks and blocked-by.
			header += " " + "Wait".ljust(cue_width)
		if mine_width:
			header += " " + "Mine".ljust(mine_width)
		for name, col_width in columns:
			label = HEADER_LABELS.get(name, name.capitalize())
			header += " " + label.ljust(col_width)
		screen.addnstr(top, 0, header, width - 1, curses.A_UNDERLINE)
		# W5: the selection anchors to the WORK ID, not the index — a
		# background refresh that inserts or removes rows never moves
		# the cursor to a different Work.
		if self.selected_id is not None:
			for index, row in enumerate(selectable):
				if row["id"] == self.selected_id:
					self.cursor = index
					break
			else:
				self.cursor = min(self.cursor,
				                  max(0, len(selectable) - 1))
		if selectable:
			self.selected_id = \
				selectable[min(self.cursor, len(selectable) - 1)]["id"]
		# The hidden-count footer is part of the collapse CONTRACT: when
		# closed rows are hidden, one line is RESERVED for naming them —
		# a full page of open rows may never make the collapse silent.
		budget = max(1, (height - 3 - top) if hidden
		             else (height - 2 - top))
		# The selected row must be PAINTED: Enter acts on it, and an
		# off-screen aim would be an invisible destructive action. Long
		# tables scroll so the cursor stays inside the drawn slice.
		# W6814: the viewport scrolls over PHYSICAL lines and still
		# anchors on the selected WORK. An elision spends a line like
		# anything else, so a group under the cursor's ancestor can
		# never quietly push the selected row off the drawn slice —
		# which is the failure the id anchor exists to prevent.
		at_line = [index for index, entry in enumerate(stream)
		           if entry["kind"] == "work"]
		cursor_line = at_line[self.cursor] if self.cursor < len(at_line) \
			else 0
		start = max(0, min(cursor_line - budget + 1,
		                   len(stream) - budget))
		for offset, entry in enumerate(stream[start:start + budget]):
			if entry["kind"] == "elision":
				# The Id column stays EMPTY and no data column is
				# drawn: the line says "levels omitted" and nothing
				# that could be mistaken for a Work's own facts. Dim,
				# because it is structure rather than content.
				cell = _elision_cell(entry["depth"], title_width,
				                     self.elision_mark())
				screen.addnstr(top + 1 + offset, id_width + 1, cell,
				               max(0, width - 1 - id_width - 1),
				               curses.A_DIM)
				continue
			row = entry["row"]
			# W71: depth-1 rows are `↳`-indented containment children; a
			# child that itself contains children carries a visible
			# disclosure count (its canonical progress total) reachable
			# through `u`.
			#
			# W154: both symbols are STRUCTURE and are reserved BEFORE
			# the truncatable title. They used to be a prefix and a
			# suffix around the whole title, which was then cut to the
			# column — so a long enough title deleted the very cue that
			# said more Work was hidden beneath it. That is how W5 came
			# to look like a leaf while W6 was open and claimed under
			# it. Title length, terminal width, selection, filters and
			# the other columns can now shorten the TITLE, and never the
			# fact that something is down there.
			title_cell = _title_cell(row, title_width)
			line = (row["local_id"].ljust(id_width) + " " + title_cell)
			if cue_width:
				line += " " + blocker_cue(row).ljust(cue_width)
			if mine_width:
				line += " " + mine_cell(row).ljust(mine_width)
			cells = self._row_cells(row)
			for name, col_width in columns:
				line += " " + cells[name][:col_width].ljust(col_width)
			# W6814: selection is decided by IDENTITY, not by the
			# physical line — the elision lines mean the two counts
			# are no longer the same number.
			attribute = curses.A_REVERSE \
				if row["id"] == self.selected_id else 0
			if self.phase_blink.get(row["id"], 0) > 0:
				# W105: the ephemeral phase-CHANGE cue covers the whole
				# visible row, not just the Phase cell. It was easy to
				# miss while scanning Titles, and it vanished entirely
				# at widths where the responsive layout drops PHASE —
				# so the cue was absent exactly where the row is
				# hardest to read.
				#
				# Composed into the BASE attribute rather than
				# overpainted, which is what makes it survive column
				# omission and compose with selection and the
				# actionable-Title bold instead of replacing either.
				# The scope is the CLIPPED visible row: what is painted
				# blinks, and off-screen columns have nothing to
				# animate.
				attribute |= curses.A_BLINK
			screen.addnstr(top + 1 + offset, 0, line, width - 1,
			               attribute)
			if actionable_work(row, self.team, self.member):
				# W81 (superseding the global hot bold): the Title
				# cell renders BOLD exactly for the VIEWER'S
				# actionable Work; the Age column carries the claim
				# timer. Only the Title cell — Id, counters, routing,
				# and the Blk cue stay steady — and the selection
				# attribute COMPOSES with the bold rather than
				# erasing it.
				screen.addnstr(
					top + 1 + offset, id_width + 1, title_cell,
					min(title_width, max(0, width - 1 - id_width - 1)),
					attribute | curses.A_BOLD)
		footer_row = top + 1 + min(len(stream) - start, budget)
		if hidden and footer_row <= height - 2:
			screen.addnstr(footer_row, 0,
			               f"({hidden} closed hidden — z shows)",
			               width - 1)
		if not stream and not hidden:
			screen.addnstr(top + 1, 0, "(no work here)", width - 1)
		if height - 2 > footer_row:
			# W6814 supersedes W71's `Enter details` here: Enter is now
			# ordinary ACTIVATION and what it opens depends on the row —
			# a Job with children becomes the contextual root, a Job
			# without them opens its own detail.
			screen.addnstr(
				height - 2, 0,
				# W26328 appends `m mine` AFTER `[d] deps` rather than
				# beside the other selection keys. W17 rules that the
				# deps label survives whole at 60 columns, and this
				# line clips at the terminal width — so a hint
				# inserted ahead of it would have pushed a ruled one
				# off the screen at exactly the width where it was
				# ruled to be present.
				"Enter drill · u unfold · c claim · z closed · "
				"[d] deps · m mine · Esc back · : command · q quit",
				width - 1)

	def _thread_autoselect(self) -> None:
		"""The ruled default across EVERY bounded page of the detail
		Work's thread set: select the first thread carrying personal New
		wherever it lives; else the first. Selection marks nothing."""
		after = 0
		while True:
			page = self._cached(
				("work_threads", self.detail_work, after),
				lambda a=after: projection.work_threads(
					self.store, self.detail_work,
					viewer_team=self.team,
					viewer_member=self.member, after=a,
					limit=DISC_PAGE))
			index = next((offset for offset, row
			              in enumerate(page["rows"]) if row["new"]),
			             None)
			if index is not None:
				self.disc_after = after
				self.disc_cursor = index
				return
			if page["next_after"] is None:
				self.disc_after = 0
				self.disc_cursor = 0
				return
			after = page["next_after"]

	# -- W4996: the dependency neighbourhood graph -------------------------

	def _graph_view(self) -> dict:
		"""One bounded, snapshotted neighbourhood for the current center.

		Cached on every input that decides it, so paging a branch or
		changing depth is a new read and a repaint is not."""
		key = ("graph", self.graph_center, self.graph_depth,
		       tuple(sorted(self.graph_expanded.items())))
		return self._cached(key, lambda: projection.dependency_neighborhood(
			self.store, self.graph_center, depth=self.graph_depth,
			expanded=dict(self.graph_expanded)))

	def _graph_anchor_index(self, rows: list[dict]) -> int:
		"""The selected ROW, derived from the anchor rather than stored.

		Anchoring by identity is the whole point: a row index means a
		different Work after a depth change, a branch expansion or a
		refresh. A Work appearing on several edges has several rows and
		the FIRST is the one keys act on, while every one of them is
		drawn selected."""
		for index, row in enumerate(rows):
			if self._graph_row_key(row) == self.graph_anchor:
				return index
		return 0

	def _graph_keys(self, rows: list[dict]) -> list[str]:
		"""The traversal order: every DISTINCT selectable key, once, in the
		order it first appears. A Work drawn on three edges is one stop."""
		seen: list[str] = []
		for row in rows:
			key = self._graph_row_key(row)
			if key is not None and key not in seen:
				seen.append(key)
		return seen

	@staticmethod
	def _graph_row_key(row: dict) -> str | None:
		"""What a row is selected BY. A Work row is its Work; a token is
		its exact branch, because two branches of one Work are two
		different things to open."""
		# A PRESENTATION ROW HAS NO IDENTITY, and that is the stacked
		# renderer's own rule: when a terminal cannot fit one edge on a
		# line it draws source, arrow and target on three rows, and only
		# the row that displays its own Work is selectable.
		#
		# W4996 PTY matrix: this assumed every row carried `work` and
		# raised `KeyError` the moment the stacked fallback was reached —
		# the console DIED on a 30-column terminal. The focused suite
		# could not see it: it drives the console at widths where the
		# layered form fits, and the narrow REFUSAL it does assert is a
		# different boundary from the narrow FALLBACK.
		if row.get("work") is None:
			return None
		if row["kind"] == graph.ROW_WORK:
			return row["work"]
		return f"{row['work']}|{row['side']}|{row['kind']}"

	def _graph_reanchor(self, rows: list[dict]) -> None:
		"""Selection follows the Work when it can and the center when it
		cannot. Ruled: a depth reduction or a refresh that removes the
		selected Work returns selection to the center; nothing else moves
		it, so a resize can never move an action to another Work."""
		if any(self._graph_row_key(row) == self.graph_anchor
		       for row in rows):
			return
		self.graph_anchor = self.graph_center

	def _graph_row_set(self) -> list[dict]:
		"""The selectable rows, derived on demand.

		Keys act on the graph, not on the last paint: a handler that read
		a cached row list would do nothing at all before the first render
		and something stale after a resize. Width is passed only because
		the renderer needs one — the row ORDER and each row's identity are
		width-independent by contract."""
		try:
			return graph.rows(self._graph_view(),
			                  max(1, self._graph_width - 1))
		except (projection.GraphInvalid, graph.GraphTooNarrow):
			# Both refuse VISIBLY when painted. A key press has nothing to
			# act on either way.
			return []

	def _render_graph(self, screen, height, width) -> None:
		self._graph_width = width
		try:
			view = self._graph_view()
		except projection.GraphInvalid as refusal:
			# Damaged data. The view refuses VISIBLY rather than drawing a
			# smaller graph that looks complete.
			screen.addnstr(2, 0, f"graph refused: {refusal}", width - 1)
			return
		try:
			rows = graph.rows(view, max(1, width - 1))
		except graph.GraphTooNarrow as refusal:
			screen.addnstr(2, 0, str(refusal), width - 1)
			return
		if not view["edges"]:
			# W17's empty state, kept verbatim. A lone token with nothing
			# beside it reads as a view that failed to load; saying there
			# are no neighbours is the answer, and it is a real one.
			screen.addnstr(height - 4, 0,
			               "(no blocking or dependent neighbors)", width - 1)
		self._graph_reanchor(rows)
		selected = self._graph_anchor_index(rows)
		# EVERY appearance of the selected Work is drawn selected, because
		# one Work on three edges is one Work.
		chosen = self._graph_row_key(rows[selected]) if rows else None
		budget = max(1, height - 4)
		start = max(0, min(selected - budget + 1, len(rows) - budget))
		for offset, row in enumerate(rows[start:start + budget]):
			attribute = curses.A_REVERSE \
				if self._graph_row_key(row) == chosen else 0
			screen.addnstr(2 + offset, 0, row["text"], width - 1, attribute)
		if height - 3 > 2 + min(len(rows) - start, budget):
			screen.addnstr(height - 3, 0, graph.footer(view), width - 1)

	def _open_graph(self, target: str) -> None:
		"""Open the graph centered on one Work, from wherever."""
		self._nav_push("links", f"{self._work_title(target)} · deps",
		               work=target)
		self.graph_center = target
		self.graph_depth = projection.DEPENDENCY_DEPTH_MIN
		self.graph_anchor = target
		self.graph_expanded = {}
		self.links_work = target
		self.links_cursor = 0
		self.mode = "links"

	def _handle_graph(self, key: int) -> bool:
		rows = self._graph_row_set()
		self._graph_reanchor(rows)
		keys = self._graph_keys(rows)
		at_top = not keys or self.graph_anchor == keys[0]
		if key in (curses.KEY_UP, ord("k")) and at_top:
			self._enter_breadcrumb()
			return True
		if key in (curses.KEY_DOWN, ord("j"), curses.KEY_UP, ord("k")):
			# ONE UNIQUE-NODE ORDER, which is what the contract says and
			# what a row order cannot give.
			#
			# W4996 console review [P1]: the renderer keeps one row per
			# canonical EDGE, so a shared DAG Work occupies consecutive
			# rows — and stepping by row from such a Work landed on
			# another row carrying the same id. The anchor did not change,
			# the next key started from the first appearance again, and
			# selection was trapped there for good.
			#
			# Movement is over DISTINCT selectable keys; painting is over
			# every appearance. Those are the two halves of the same rule
			# and they were being served by one list.
			keys = self._graph_keys(rows)
			if keys:
				step = 1 if key in (curses.KEY_DOWN, ord("j")) else -1
				try:
					at = keys.index(self.graph_anchor)
				except ValueError:
					at = 0
				self.graph_anchor = keys[
					max(0, min(at + step, len(keys) - 1))]
		elif key in (ord("+"), ord("=")):
			# `=` because `+` is shifted on most layouts and an operator
			# who presses the unshifted key means the same thing.
			self.graph_depth = min(projection.DEPENDENCY_DEPTH_MAX,
			                       self.graph_depth + 1)
		elif key == ord("-"):
			self.graph_depth = max(projection.DEPENDENCY_DEPTH_MIN,
			                       self.graph_depth - 1)
		elif key in (curses.KEY_ENTER, 10, 13) and rows:
			row = rows[self._graph_anchor_index(rows)]
			if row["kind"] == graph.ROW_OVERFLOW:
				# Enter widens ONE branch page. It is not a depth change
				# and it does not touch any other branch.
				branch = projection.branch_key(row["work"], row["side"])
				self.graph_expanded[branch] = (
					self.graph_expanded.get(
						branch, projection.DEPENDENCY_BRANCH_PAGE)
					+ projection.DEPENDENCY_BRANCH_PAGE)
			elif row["kind"] == graph.ROW_DEEPER:
				# The depth frontier is opened by `+`, and the token says
				# so. Enter here would silently mean two different things
				# on two token kinds.
				self.status = "deeper neighbours: press + to raise depth"
			elif row["work"] != self.graph_center:
				# RECENTER, in the graph. It does not jump to the Jobs
				# table: the operator asked to look at a neighbour's
				# neighbourhood, not to leave the view.
				self._nav_push("links",
				               f"{self._work_title(row['work'])} · deps",
				               work=row["work"])
				self.graph_center = row["work"]
				self.graph_anchor = row["work"]
				# Branch pages belong to the graph they were opened in.
				self.graph_expanded = {}
				self.links_work = row["work"]
		elif key in (27, curses.KEY_LEFT, ord("i")):
			# Esc restores the EXACT prior graph — center, depth, anchor
			# and branch expansions all ride the navigation frame — and
			# the last one returns to the caller's table state.
			if not self._nav_pop():
				self.mode = "table"
				self.graph_center = None
				self.links_work = None
		if self.mode == "links":
			# Re-anchor AFTER the act, not only before it. A depth
			# REDUCTION can remove the selected Work, and the ruling says
			# selection returns to the center when it does — waiting for
			# the next key or the next paint to notice would leave the
			# console briefly pointing at a Work it is not showing.
			self._graph_reanchor(self._graph_row_set())
		return True

	# -- W17: the poke view ----------------------------------------------

	@staticmethod
	def _poke_stamp(value) -> str:
		"""One canonical instant as the console shows instants.

		W8160 supersedes the truncation this used to be. The old cell
		dropped the `T` and cut at the minute, on the reasoning that a
		zone marker was spent on nothing a live reader needs — which was
		true only while the marker was `Z` on a value nobody could act
		on. It is FALSE for a local instant: the zone is what says the
		number is the operator's own clock rather than the store's, and
		the poke table already measures this cell and drops it whole, so
		the width is not bought by removing the one field that makes the
		rest legible.

		The canonical value stays in JSON — this is the row's timestamp
		cell, not the record."""
		return local_stamp(value)

	def _poke_cells(self, row: dict) -> dict:
		"""Every drawable cell for one poke — canonical values only.

		`Do` is the W228 cue restated for this view: the action is TEXT,
		because the ruling there is that an actionable row must be
		legible without relying on colour, blink or bold alone. `State`
		stays the canonical vocabulary beside it and never borrows a
		word of its own — `pending` and `answer` are two different
		facts, and the row shows both.

		`With` names the OTHER participant and the direction, because a
		poke has exactly two ends and which end this participant is on
		decides what they can do about it: answer the ones asked of
		them, withdraw the ones they asked."""
		other = row["target"] if row["mine"] else row["asker"]
		return {
			"Do": ("answer" if row["owed"] else
			       "withdraw" if row["mine"]
			       and row["state"] == "pending" else ""),
			"State": row["state"],
			"With": ("to " if row["mine"] else "from ") + str(other),
			"Asked": self._poke_stamp(row.get("asked_at")),
			"Request": " ".join(str(row["request"] or "").split()),
		}

	def _poke_detail_lines(self, row: dict, width: int) -> list[str]:
		"""The selected poke in full: the friendly question as asked,
		its deadline when it has one, and the one terminal answer when
		it has been given — the agent's own words, beside the state it
		reported. Nothing here is summarized away, which is the whole
		point of a detail block under a truncating table."""
		lines = [f"Poke {row['poke']} — {row['state']}"
		         + ("  (owed by you)" if row["owed"] else "")]
		lines.append(f"  asked by {row['asker']} → {row['target']}"
		             f" at {self._poke_stamp(row.get('asked_at'))}")
		if row.get("expires_at"):
			lines.append(f"  times out at "
			             f"{self._poke_stamp(row['expires_at'])}")
		for part in str(row["request"] or "").splitlines() or [""]:
			lines.append(f"  {part}")
		answer = row.get("answer")
		if answer:
			lines.append(f"  answered {answer['state']} at "
			             f"{self._poke_stamp(answer.get('at'))}")
			for part in str(answer.get("explanation")
			                or "").splitlines():
				lines.append(f"    {part}")
		out: list[str] = []
		for line in lines:
			out.extend(soft_wrap(line, max(8, width - 1)))
		return out

	def _render_mine(self, screen, height, width) -> None:
		"""W26328: the flattened `Awaiting me` page.

		NO `Mine` column. Every row here is claimable by this viewer —
		that is the page's whole definition — so a column repeating it
		on every line would be cells spent telling no two rows apart,
		which is exactly the rule W73 and W93 apply to `Out` and `Run`.
		The COUNT still appears, once, in the page label."""
		rows = self.mine_rows()
		more = "  (n: more)" if self.mine_next is not None else ""
		screen.addnstr(1, 0,
		               f"awaiting me: {self.mine_total} total · page "
		               f"{self.mine_page} · {len(rows)} shown{more}",
		               width - 1, curses.A_DIM)
		# The empty page is an ANSWER and says so in words. A blank
		# body would read as a view that failed to load.
		if not rows:
			screen.addnstr(3, 0, "(no work awaiting you)", width - 1)
		else:
			# W5's id anchor, on this page too: a background refresh
			# that adds or removes actionable Work must not slide the
			# cursor onto a different Work.
			if self.selected_id is not None:
				for index, row in enumerate(rows):
					if row["id"] == self.selected_id:
						self.cursor = index
						break
				else:
					self.cursor = min(self.cursor, len(rows) - 1)
			self.cursor = max(0, min(self.cursor, len(rows) - 1))
			self.selected_id = rows[self.cursor]["id"]
			stream = mine_stream(rows, width)
			id_width = id_column_width(rows)
			budget = max(1, height - 4)
			at_line = [index for index, entry in enumerate(stream)
			           if entry["first"]]
			cursor_line = at_line[self.cursor]
			start = max(0, min(cursor_line - budget + 1,
			                   len(stream) - budget))
			for offset, entry in enumerate(stream[start:start + budget]):
				# The whole entry carries the selection weight, every
				# wrapped line of it: half a highlighted path would
				# read as two entries.
				attribute = curses.A_REVERSE \
					if entry["row"]["id"] == self.selected_id else 0
				line = entry["id"].ljust(id_width) + " " + entry["text"]
				screen.addnstr(2 + offset, 0, line, width - 1, attribute)
		screen.addnstr(height - 2, 0,
		               "j/k select · Enter details · c claim · "
		               "n/p page · Esc back", width - 1)

	def _open_mine(self) -> None:
		"""W26328: enter the flattened page. It is a drill like any
		other — one frame, one Back, and the frame carries the table
		state being left, so Esc returns to the exact row of the exact
		tree the operator pressed `m` on."""
		self._nav_push("mine", "awaiting me")
		self.mode = "mine"
		self.mine_after = 0
		self.mine_page = 1
		self.cursor = 0
		self.selected_id = None

	def _handle_mine(self, key: int) -> bool:
		"""W26328: the `Awaiting me` keys — the same vocabulary the
		table and search already teach, and nothing new to learn."""
		rows = self.mine_rows()
		if key in (curses.KEY_DOWN, ord("j")):
			self.cursor = min(self.cursor + 1, max(0, len(rows) - 1))
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_UP, ord("k")) and self.cursor == 0:
			self._enter_breadcrumb()
		elif key in (curses.KEY_UP, ord("k")):
			self.cursor = max(0, self.cursor - 1)
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_ENTER, 10, 13) and rows:
			self._enter_detail(rows[min(self.cursor,
			                            len(rows) - 1)]["id"],
			                   came_from="mine")
		elif key == ord("n") and self.mine_next is not None:
			self.mine_after = self.mine_next
			self.mine_page += 1
			self.cursor = 0
			self.selected_id = None
		elif key == ord("p"):
			self.mine_after = 0
			self.mine_page = 1
			self.cursor = 0
			self.selected_id = None
		elif key == ord("c") and rows:
			# The SAME shared claim path the table and search use. This
			# is the page an operator opens to claim from, so anything
			# else here would be a second claim path to keep honest.
			self._claim_selected(rows)
		elif key in (27, curses.KEY_LEFT) and self.nav:
			self._nav_pop()
		return True

	def _render_pokes(self, screen, height, width) -> None:
		"""The pokes this participant is part of, owed ones first.

		Presentation only: every value is the canonical projection's,
		the actions run the public verbs, and opening this view neither
		answers, cancels nor marks anything seen."""
		rows, older = self.poke_rows()
		owed = sum(1 for row in rows if row["owed"])
		mine = sum(1 for row in rows if row["mine"])
		# W17 review R1: the disclosure names the rows ACTUALLY omitted
		# — older history, counted — and says nothing at all when the
		# window holds everything. A line describing the wrong end is
		# worse than no line, because it is believed.
		note = (f"pokes — {owed} owed you · {mine} you asked"
		        + (f" · {older} older not shown" if older else ""))
		screen.addnstr(1, 0, note, width - 1, curses.A_DIM)
		footer = height - 2
		if not rows:
			screen.addnstr(3, 0,
			               "(no pokes — nobody has asked you anything, "
			               "and you have asked nobody)", width - 1)
			screen.addnstr(footer, 0, "Esc back", width - 1)
			return
		selected = self._poke_selected()
		detail = self._poke_detail_lines(selected, width) \
			if selected else []
		# The list keeps at least three rows whatever the detail block
		# wants: a view showing one selectable row cannot be navigated,
		# and the block below it is the part that can be scrolled off
		# honestly — every fact in it is already in the record.
		reserved = min(len(detail), max(3, (footer - 4) // 2))
		listing = max(3, footer - 4 - reserved)
		id_width = max(len(f"P{row['poke']}") for row in rows)
		cells = {row["poke"]: self._poke_cells(row) for row in rows}
		columns = []
		for name, floor in (("Do", 2), ("State", 6), ("With", 12),
		                    ("Asked", 16)):
			columns.append((name, max(floor, max(
				len(cells[row["poke"]][name]) for row in rows))))
		# Whole columns are OMITTED under width pressure, never squeezed
		# — the main table's rule, applied to the two facts whose loss
		# costs least here. `Asked` goes first (a poke's age is context,
		# not the question), then `State`, and the detail block below
		# still carries both in full. `Do`, `With` and the question
		# itself always survive: they are what the row is FOR.
		for droppable in ("Asked", "State"):
			used = id_width + sum(size + 1 for _name, size in columns)
			if width - 2 - used >= 24:
				break
			columns = [entry for entry in columns
			           if entry[0] != droppable]
		used = id_width + sum(size + 1 for _name, size in columns)
		columns.append(("Request", max(8, width - 2 - used)))
		header = "Id".ljust(id_width)
		for name, size in columns:
			header += " " + name.ljust(size)
		screen.addnstr(2, 0, header[:width - 1], width - 1,
		               curses.A_UNDERLINE)
		start = max(0, min(self.poke_cursor - listing + 1,
		                   len(rows) - listing))
		start = max(0, start)
		shown = rows[start:start + listing]
		for offset, row in enumerate(shown):
			text = f"P{row['poke']}".ljust(id_width)
			for name, size in columns:
				text += " " + cells[row["poke"]][name][:size].ljust(size)
			attribute = 0
			if start + offset == self.poke_cursor:
				attribute = curses.A_REVERSE
			elif row["owed"]:
				attribute = curses.A_BOLD
			screen.addnstr(3 + offset, 0, text[:width - 1], width - 1,
			               attribute)
		# One blank separator row, then the chosen poke in full — the
		# block sits UNDER the list it explains rather than floating at
		# the bottom of a tall terminal.
		detail_top = 3 + len(shown) + 1
		budget = max(0, footer - detail_top)
		if len(detail) > budget > 0:
			# A short terminal clips the block; it never pretends to
			# have shown the whole question. The canonical record is
			# named, so the operator knows where the rest is.
			hidden = len(detail) - (budget - 1)
			detail = detail[:budget - 1] + [
				f"  … {hidden} more line(s) — `pokes` has the record"]
		for offset, line in enumerate(detail[:budget]):
			screen.addnstr(detail_top + offset, 0, line, width - 1)
		# The footer offers only what the chosen poke actually admits:
		# a state key on somebody else's answered poke would be an
		# invitation to a refusal.
		bits = ["j/k select"]
		if selected and selected["owed"]:
			bits.append("a answer")
		if selected and selected["mine"] \
				and selected["state"] == "pending":
			bits.append("x withdraw")
		bits.append("Esc back")
		screen.addnstr(footer, 0, " · ".join(bits), width - 1)

	def _facts(self, detail: dict) -> list[str]:
		"""The focused facts, EVERY one a canonical projection value: the
		terminal outcome with its durable rationale, the effective binding
		(WS-6 R90 portable root:path), the effective contract revision,
		and duplicate/follow-up identity.

		W90: the `can:` line is GONE from here. It rendered the Work's
		`available_transitions` directly above the Threads list, where
		`can: prioritize` reads as something you might do to the message
		you are looking at. It is a capability of the Work — open to any
		configured member of its owning team — and repeating it on a
		reading surface invited exactly that misreading.

		Nothing about the capability itself changed: `available_transitions`
		remains in the canonical JSON detail for every client, and the
		command grammar is untouched. What was removed is the claim that
		it belongs beside a conversation. A genuine Work-actions or help
		surface is where it should reappear."""
		facts = []
		if detail["status"] == "closed":
			facts.append(f"closed {detail['outcome']} — "
			             f"{detail['rationale']}")
		# finding-active-work-claim: WHO is executing is a canonical
		# authority value, never inferred from route membership.
		# W245/W38: it is spelled `handler`, and its absence is the fact.
		if detail.get("handler") is not None:
			facts.append(f"handler: {detail['handler']['team']}."
			             f"{detail['handler']['member']}")
		binding = detail.get("binding")
		if binding is not None:
			facts.append(f"binding {binding['root']}:{binding['path']} "
			             f"r{binding['revision']}")
		revision = detail.get("revision")
		if revision is not None:
			facts.append(f"contract rev r{revision['revision']} "
			             f"(message #{revision['message_seq']})")
		if detail["duplicate_of"] is not None:
			facts.append(f"duplicate-of {detail['duplicate_of']}")
		if detail["follow_up_of"] is not None:
			facts.append(f"follow-up-of {detail['follow_up_of']}")
		return facts

	def _detail_header(self, detail: dict) -> str:
		route = detail["route"]["endpoint"] if detail["route"] else "-"
		handler = (f"{detail['handler']['team']}."
		           f"{detail['handler']['member']}") \
			if detail["handler"] else "-"
		planned = detail["next"]["endpoint"] if detail["next"] else "-"
		# W12 (ruled): the EXACT canonical Work id leads the header —
		# first on the line so no narrow width ever clips it, straight
		# from the selected Work's canonical detail (never a title
		# inference). Every command-bar operation can be typed from it.
		line = (f"{detail['id']} ({detail['local_id']}) "
		        f"[{detail['status']}"
		        f"/{phase_cell(detail['status'], detail['phase'])}"
		        f"/{compact_classification(detail['classification'])}] "
		        # W245: both facts, in the order they are asked —
		        # who may claim, then who actually holds it.
		        f"route {route}  handler {handler}  "
		        f"next {planned}  new {detail['new']}")
		# W78: the focused row states WHAT is holding the Work, not the
		# kind of condition it is waiting on. `wait:gates` named a
		# category; `wait W4` and `wait M66` name the thing an operator
		# can go and look at. The detail pane below adds the gate's
		# full facts — obligation state and resolved endpoint — which
		# the compact row deliberately leaves out.
		gate = detail.get("gate")
		if gate is not None:
			line += f"  wait {gate['selector']}"
		return line

	# W6814 supersedes the two-tab detail row. The tabs belong to the
	# contextual Work PAGE, not to its detail view, and `Jobs` is that
	# Work rendered as the tree root — the third thing an operator can
	# want to see about the Work they opened.
	DETAIL_TABS = ROOT_TABS

	def detail_tab_segments(self) -> list[tuple[str, str]]:
		"""`(tab name, drawn label)`, every label bracketed.

		W110: the same grammar the top level uses. The brackets say
		"this is a tab"; the active one is highlighted by the painter."""
		return [(name, f"[{name.title()}]")
		        for name in self.DETAIL_TABS]

	def _paint_tab_row(self, screen, row: int, width: int,
	                   active: str) -> None:
		"""The contextual Work page's local tab row, painted label by
		label — W110: the active one carries REVERSE and a single string
		could only weight both or neither.

		W110 review R2: the SAME narrow-layout rule the top level uses.
		This loop used to stop at the first label too wide, which left
		the inactive `[Messages]` alone on a 13-column bar while the
		operator was in Events — advertising a tab the screen did not
		show, and losing the one it did.

		W6814 gives it a second caller. The Jobs tab of a contextual
		Work page is the same row above a table instead of above a
		reader, and two paintings of one row would be two chances for
		them to disagree about which tab is active."""
		column = 0
		for name, label in fitted_tabs(self.detail_tab_segments(), active,
		                               max(0, width - 1)):
			screen.addnstr(row, column, label, width - 1 - column,
			               curses.A_BOLD | (curses.A_REVERSE
			                                if name == active else 0))
			column += len(label) + len(TAB_GAP)

	def _tab_bar(self) -> str:
		"""W123: `[Messages]  [Events]`. The bar is presentation; the
		tab itself is client state and touches no authority."""
		return TAB_GAP.join(label for _name, label
		                    in self.detail_tab_segments())

	def _switch_tab(self, step: int) -> None:
		"""`]` next, `[` previous, across the contextual Work page's own
		`[Jobs] [Messages] [Events]` — W6814.

		Each tab's own focus, selection, page cursor and reader scroll
		live in separate fields, so switching preserves every side by
		construction rather than by saving and restoring a shared slot.
		A tab change is a LOCAL interaction: it records no history and
		does not touch the breadcrumb, because the operator has not
		changed which Work they are looking at."""
		here = self.DETAIL_TABS.index(self.context_tab())
		self._show_tab(self.DETAIL_TABS[
			(here + step) % len(self.DETAIL_TABS)])

	def _show_tab(self, name: str) -> None:
		"""Show one of the contextual page's tabs, scoped to the page's
		ROOT Work rather than to whatever row is highlighted.

		`Jobs` re-enters the tree already rooted there — preserving the
		row and cursor if it is already the root, so a round trip out to
		Messages and back returns to the row the operator left."""
		root = self.context_work() or self.detail_work \
			or (self.path[-1] if self.path else None)
		if root is None:
			return
		if name == "jobs":
			self.mode = "table"
			if not (self.path and self.path[-1] == root):
				self.path = self._work_ids(root)
				self.cursor = 0
				self.selected_id = None
			return
		self.mode = "detail"
		self.detail_work = root
		self.detail_tab = name

	def _detail_footer(self, screen, height, width, bits) -> None:
		"""The advertised controls. `[/] tabs` is ALWAYS present: the
		ruling is that tab navigation must not be discoverable only by
		prior knowledge.

		W26331 extends W1151's pane cycle through the breadcrumb. The
		footer now names Tab as the generic focus gesture and keeps Ctrl-W
		explicitly pane-shaped; the focused breadcrumb replaces this line
		with its exact ordinal and selector instructions."""
		screen.addnstr(height - 2, 0,
		               " · ".join(["[/] tabs", *bits]), width - 1)

	def _render_events(self, screen, top, height, width) -> None:
		"""The Events tab: a bounded index of `E<seq>` beside a reader
		showing one selected event's complete typed detail.

		Layout mirrors Messages deliberately — wide splits index|reader,
		narrow stacks them — because the two tabs are the same shape of
		thing and an operator should not have to learn two geometries.
		Like Messages (W76) it opens NEWEST-FIRST on one bounded page;
		`n` reaches older events, `p` returns to the newest."""
		region = height - 2 - top
		if region < 2:
			return
		page_limit = max(1, region - 2)
		snapshot = self._cached(
			("work-events", self.detail_work, self.event_before,
			 page_limit),
			lambda: projection.work_events(
				self.store, self.detail_work,
				before=self.event_before,
				newest=self.event_before is None, limit=page_limit))
		events = snapshot["events"]
		self.viewed_events_next_before = snapshot["next_before"]
		seqs = [entry["seq"] for entry in events]
		self.viewed_event_seqs = seqs
		if self.event_cursor not in seqs:
			self.event_cursor = seqs[-1] if seqs else None
			self.event_skip = 0
		selected = next((entry for entry in events
		                 if entry["seq"] == self.event_cursor), None)
		index_bold = curses.A_BOLD if self.event_focus == "index" else 0
		reader_bold = curses.A_BOLD if self.event_focus == "reader" else 0
		imarker = "»" if self.event_focus == "index" else " "
		rmarker = "»" if self.event_focus == "reader" else " "
		more = "  (n: older)" if snapshot["next_before"] is not None \
			else ""
		index_label = f"{imarker}Events ({len(events)}){more}"
		reader_label = f"{rmarker}Event E{selected['seq']}" \
			if selected else f"{rmarker}Event"
		index_width = self.event_index_width(events)
		wide = width - 1 - index_width - 2 >= self.MIN_READER
		if wide:
			reader_x = index_width + 2
			reader_width = width - 1 - reader_x
			screen.addnstr(top, 0, index_label, index_width,
			               index_bold)
			screen.addnstr(top, reader_x, reader_label, reader_width,
			               reader_bold)
			self._paint_event_index(screen, top + 1, region - 1, 0,
			                        index_width, events)
			self._paint_event_reader(screen, top + 1, region - 1,
			                         reader_x, reader_width, selected)
		else:
			index_rows = max(1, min(len(events) or 1,
			                        max(2, region // 3), region - 3))
			screen.addnstr(top, 0, index_label, width - 1, index_bold)
			self._paint_event_index(screen, top + 1, index_rows, 0,
			                        width - 1, events)
			reader_top = top + 1 + index_rows
			screen.addnstr(reader_top, 0, reader_label, width - 1,
			               reader_bold)
			self._paint_event_reader(screen, reader_top + 1,
			                         top + region - reader_top - 1, 0,
			                         width - 1, selected)
		bits = []
		if snapshot["next_before"] is not None:
			bits.append("older events — n older · p newest")
		elif self.event_before is not None:
			bits.append("newer events — p newest")
		bits.extend(["Tab focus", "Ctrl-W panes", "j/k select", "Esc back"])
		self._detail_footer(screen, height, width, bits)

	# W47: the Event index is a fixed-column table. Concatenating the
	# fields put every later one at a different cell, so nothing lined
	# up and the eye could not scan a column. Widths are FIXED and an
	# entire lower-priority column is dropped whole when the pane is
	# too narrow — truncating one would move every column after it,
	# which is the defect in a subtler form.
	#
	# Priority order, highest first: the stable id, the typed kind, the
	# actor, the time, the scheduler phase, its duration.
	EVENT_COLUMNS = (("EVENT", 6), ("KIND", 12), ("ACTOR", 10),
	                 ("TIME", 5), ("PHASE", 5), ("FOR", 5))
	# The Events index carries six columns where the Messages index
	# carries a line of prose, so it gets its own width. Sharing the
	# narrower Messages budget would have dropped PHASE and FOR at
	# every terminal size, which is the whole point of the table.
	EVENT_INDEX_WIDTH = sum(w for _n, w in EVENT_COLUMNS) + 5

	@staticmethod
	def event_time_width(events) -> int:
		"""The `TIME` allocation for ONE painted page.

		W8160: the declared five cells were exactly `HH:MM`, and a local
		instant carries its zone. Sized from the page for the reason
		`Do` and `Id` are — the declared width is a FLOOR, never a cap —
		because clipping `18:36 MDT` back to five cells restores the
		unlabelled wall clock this ruling removed, whereas dropping the
		whole column costs a fact the reader can still get from the
		Event pane beside it."""
		widest = max((len(local_stamp(entry.get("ts"), compact=True))
		              for entry in events or ()), default=0)
		return max(len("TIME"), widest)

	def _event_columns(self, cell_width, time_width: int | None = None):
		"""The widest column set that fits, dropping from the right."""
		columns = [(name, max(width, time_width)
		            if name == "TIME" and time_width is not None
		            else width)
		           for name, width in self.EVENT_COLUMNS]
		while columns and sum(w for _n, w in columns) + len(columns) - 1 \
				> cell_width:
			columns.pop()
		return columns

	def event_index_width(self, events) -> int:
		"""The Events index PANE, sized for the page it is about to
		paint.

		W8160: `EVENT_INDEX_WIDTH` is a constant computed from the
		declared widths, so a measured `TIME` would have been dropped by
		`_event_columns` at every terminal size — the pane would never
		have offered it the cells. It stays as the floor and the page
		raises it."""
		return max(self.EVENT_INDEX_WIDTH,
		           self.EVENT_INDEX_WIDTH
		           - dict(self.EVENT_COLUMNS)["TIME"]
		           + self.event_time_width(events))

	def _event_row(self, entry, columns) -> str:
		interval = entry.get("phase_interval")
		values = {
			"EVENT": f"E{entry['seq']}",
			"KIND": entry["kind"],
			"ACTOR": entry["actor"] or "",
			"TIME": local_stamp(entry.get("ts"), compact=True),
			# The phase-ENTRY event owns these two cells; every other
			# row reads `-`, so one episode appears exactly once.
			"PHASE": compact_phase(interval["phase"])
			if interval else "-",
			"FOR": duration_cell(interval["elapsed_seconds"])
			if interval else "-",
		}
		return " ".join(values[name][:width].ljust(width)
		                for name, width in columns)

	def _paint_event_index(self, screen, top, rows, x, cell_width,
	                       events):
		"""`E<seq>` is the visible stable event identifier — the
		authoritative sequence, nothing invented. Newest first, matching
		the Message index."""
		if not events:
			screen.addnstr(top, x, "(no events on this page)",
			               cell_width)
			return
		columns = self._event_columns(cell_width,
		                              self.event_time_width(events))
		header = " ".join(name[:width].ljust(width)
		                  for name, width in columns)
		screen.addnstr(top, x, header[:cell_width].ljust(cell_width),
		               cell_width, curses.A_DIM)
		rows = max(0, rows - 1)
		ordered = list(reversed(events))
		seqs = [entry["seq"] for entry in ordered]
		chosen = seqs.index(self.event_cursor) \
			if self.event_cursor in seqs else 0
		start = max(0, min(chosen - rows + 1, len(ordered) - rows))
		for offset, entry in enumerate(ordered[start:start + rows]):
			text = self._event_row(entry, columns)
			attribute = curses.A_REVERSE \
				if entry["seq"] == self.event_cursor else 0
			screen.addnstr(top + 1 + offset, x,
			               text[:cell_width].ljust(cell_width),
			               cell_width, attribute)

	def _event_lines(self, entry) -> list[str]:
		"""Human labels for the common typed fields, then the COMPLETE
		payload. Routine events read compactly, but nothing is hidden:
		the ruling is that folding must be explicit, never silent
		omission."""
		# W48: an ABSENT payload and a present falsy one are different
		# facts. `entry.get("payload") or {}` turned `null`, `false`,
		# `0`, `""` and `[]` into `{}` — the reader claimed an empty
		# object where the ledger holds a JSON value with its own type
		# and spelling. Only a genuinely missing key falls back.
		payload = entry.get("payload", _ABSENT_PAYLOAD)
		if payload is _ABSENT_PAYLOAD:
			payload = {}
		lines = [f"#{entry['seq']} {entry['kind']} {entry['actor']} "
		         f"{local_stamp(entry['ts'])}"]
		# W1217 (finding-event-relation-display): `subject` is why this
		# Event is on the screen at all — every row in this Work's
		# Events tab is here because it relates to this Work — so a row
		# saying so restated the view and spent a line doing it, in
		# vocabulary that reads like a member role.
		#
		# A MEANINGFUL relationship is different: `consumer`,
		# `blocker`, `parent`, `provider` explain why an Event that
		# primarily concerns another Work appears here, and that an
		# operator cannot infer. Those are named, and `subject` is
		# never shown beside them — it is the implicit baseline, not an
		# extra fact. The canonical `roles` array is untouched; this is
		# the reader deciding what to say, not the projection deciding
		# what to hold.
		meaningful = [role for role in entry["roles"] if role != "subject"]
		if len(meaningful) == 1:
			lines.append(f"  relation: {meaningful[0]}")
		elif meaningful:
			lines.append(f"  relations: {', '.join(meaningful)}")
		for other in entry.get("related") or ():
			lines.append(f"  related: {other['work']} "
			             f"({other['role']})")
		interval = entry.get("claim_interval")
		if interval:
			held = interval["elapsed_seconds"]
			lines.append(f"  claim: {interval['claimant']} from "
			             f"E{interval['claim_seq']} "
			             f"{local_stamp(interval['started_at'])}")
			if interval["end_seq"] is None:
				# W123 R3: an open claim shows how long it has been
				# held, not merely that it is open.
				lines.append(f"  claim: still open, held {held}s")
			else:
				lines.append(f"  claim: ended E{interval['end_seq']} "
				             f"({interval['end_kind']}) after {held}s")
		# The typed labels read the payload's own fields, so they apply
		# only when it IS an object. A list or scalar payload has no
		# fields to label and goes straight to the JSON block below.
		if isinstance(payload, dict):
			for label in ("rationale", "reason", "comment", "outcome",
			              "from", "to", "destination_phase", "title",
			              "classification", "priority", "claimant",
			              "released_claimant", "blocker", "provider"):
				if payload.get(label) is not None:
					lines.append(f"  {label}: {payload[label]}")
		for reference in entry.get("references") or ():
			lines.append(f"  ref: {reference.get('root')}:"
			             f"{reference.get('path')}")
		# W48: `payload:` is a SECTION LABEL on its own line and the
		# JSON begins beneath it, two spaces per nesting level. One
		# `json.dumps(..., sort_keys=True)` line put nested objects and
		# arrays on a single wrapped line, where the reader's generic
		# wrapping obscured the structure the operator is reading the
		# payload to see.
		#
		# Each JSON logical line is supplied SEPARATELY, before any
		# terminal-width handling — wrapping is the painter's job and
		# is presentation only. `ensure_ascii=False` keeps Unicode
		# readable; `sort_keys=True` keeps the order deterministic.
		import json as _payload_json
		# W1207 (finding-event-payload-visual-separation): ONE blank
		# row between the typed metadata and the audit record. The
		# `payload:` label was already there, but with no vertical gap
		# the JSON read as one more metadata field and the eye had to
		# re-parse the block to find where the human summary ended.
		#
		# Spacing rather than a rule: a horizontal line would spend
		# width the reader needs and would depend on glyphs some
		# terminals draw badly. `soft_wrap` keeps an empty logical line
		# as exactly one empty visual line, so a narrow pane neither
		# multiplies nor erases the separator.
		lines.append("")
		lines.append("  payload:")
		lines.extend(
			"  " + text for text in
			_payload_json.dumps(payload, indent=2, sort_keys=True,
			                    ensure_ascii=False).splitlines())
		return lines

	def _paint_event_reader(self, screen, top, rows, x, cell_width,
	                        entry) -> None:
		if entry is None:
			screen.addnstr(top, x, "(no event selected)", cell_width)
			self.event_clipped = False
			return
		wrapped = []
		for line in self._event_lines(entry):
			wrapped.extend(soft_wrap(line, cell_width))
		skip = min(self.event_skip, max(0, len(wrapped) - 1))
		self.event_skip = skip
		visible = wrapped[skip:]
		if skip:
			visible = [f"E{entry['seq']} (cont.)"] + visible
		take = max(0, min(len(visible), rows))
		for offset, line in enumerate(visible[:take]):
			screen.addnstr(top + offset, x, line, cell_width)
		shown = take - (1 if skip else 0)
		self.event_clipped = skip + shown < len(wrapped)

	def _render_detail(self, screen, height, width) -> None:
		"""W71: the Work DETAIL view — header and facts, then the
		distinct Threads (subjects, selectable, bounded pages) above the
		selected Thread's formatted Messages. Ctrl-W moves between the
		panes; selection marks nothing; only the explicit `s` writes,
		bounded by the painted page. No internal cursor is shown —
		continuation is operator-facing more/page state."""
		work_id = self.detail_work
		detail = self._cached(("detail", work_id),
		                      lambda: projection.detail(
			self.store, work_id, viewer_team=self.team,
			viewer_member=self.member))
		screen.addnstr(1, 0, self._detail_header(detail), width - 1)
		facts = self._facts(detail)
		for offset, text in enumerate(facts):
			screen.addnstr(2 + offset, 0, text, width - 1)
		offset_row = 2 + len(facts)
		if detail["trials"]:
			latest = detail["trials"][-1]
			flags = "due" if latest["due"] else latest["status"]
			line = (f"Trial {latest['trial']} {latest['candidate']} "
			        f"{latest['progress']} {flags} "
			        f"wthdr:{latest['withdrawn']}")
			screen.addnstr(offset_row, 0, line, width - 1)
			for index, entry in enumerate(latest["assignments"]):
				verdict = entry["effective_assessment"]
				axis = ((entry["observation"] or entry["state"]) + "/" +
				        (verdict["assessment"] if verdict else "-"))
				screen.addnstr(offset_row + 1 + index, 0,
				               f"  {entry['endpoint']} {axis}",
				               width - 1)
			offset_row = offset_row + 1 + len(latest["assignments"])

		# W123: the tab bar is ALWAYS painted, so both views are
		# discoverable without prior knowledge, and the active one is
		# distinguished rather than merely remembered. W110: painted
		# label by label, because the active one carries REVERSE and a
		# single string could only weight both or neither — the same
		# reason the top-level header is painted in pieces.
		self._paint_tab_row(screen, offset_row, width, self.detail_tab)
		offset_row += 1
		if self.detail_tab == "events":
			self._render_events(screen, offset_row, height, width)
			return

		rows = self.thread_rows()
		if self.disc_cursor is None:
			self._thread_autoselect()
			rows = self.thread_rows()
		if not rows:
			screen.addnstr(offset_row, 0, "(no threads)", width - 1)
			self.viewed_thread = None
			self.msg_cursor = None
			self._detail_footer(screen, height, width, [])
			return
		chosen = min(self.disc_cursor, len(rows) - 1)
		selected = rows[chosen]
		self.viewed_thread = selected["id"]
		self.viewed_ordinal = selected["ordinal"]

		# The Threads pane: a bounded selectable list, more-state in
		# operator terms (never an internal cursor).
		more = "  (n: more threads)" if self.disc_next is not None \
			else ""
		marker = "»" if self.focus == "threads" else " "
		screen.addnstr(offset_row, 0,
		               f"{marker}Threads ({detail['thread_count']})"
		               f"{more}:", width - 1,
		               curses.A_BOLD if self.focus == "threads" else 0)
		list_budget = max(1, min(len(rows), (height - offset_row) // 3))
		start = max(0, min(chosen - list_budget + 1,
		                   len(rows) - list_budget))
		for offset, row in enumerate(rows[start:start + list_budget]):
			attribute = curses.A_REVERSE \
				if start + offset == chosen else 0
			# W7: the label is the ACCEPTED local selector (the
			# canonical id's sequence), never the Work-scoped label
			# ordinal — what the pane shows is what `say thread=`
			# takes.
			screen.addnstr(offset_row + 1 + offset, 0,
			               f"  {row['local_id']} {row['subject']} "
			               f"new:{row['new']} {row['id']}",
			               width - 1, attribute)
		# W176: exactly ONE blank separator row between the Thread list
		# and the lower Messages/Message panes — spacing, not a border
		# or a repeated label, separates the two navigation levels.
		msgs_top = offset_row + 1 + min(len(rows) - start,
		                                list_budget) + 1

		# W14: the lower region — Message index + selected reader.
		self._render_message_region(screen, msgs_top, height, width,
		                            selected)

	# W14 layout: the index column at usable width; the reader must keep
	# at least MIN_READER cells or the two regions stack instead.
	INDEX_WIDTH = 34
	MIN_READER = 40

	def _autoselect_seq(self, messages):
		"""W76: entry selects the NEWEST Message on the page.

		This replaces W14's walk to the first personal-new Message, and
		it is not a weakening: the seen cursor is a MONOTONIC sequence,
		so whenever anything is unseen the newest Message is itself
		unseen. Selecting it therefore lands on new mail when there is
		new mail, and on the end of the conversation when there is not
		— without loading every page to find out. Selection marks
		nothing."""
		return messages[-1]["seq"] if messages else None

	# W49: the Message index is a fixed-column table, declared here as
	# data. Concatenating the fields made every row's time and state
	# start wherever the author's name happened to end, so nothing could
	# be scanned down a column.
	#
	# Visual order is `Id From Time St`. PRIORITY is different and
	# deliberate — Id, From, St, then Time — so width pressure drops the
	# clock before it drops the viewer's own new/seen fact. Id is not in
	# this table because its width is computed per page from the longest
	# visible selector.
	#
	# `From` is 13 cells because a configured handle is at most six
	# display cells and the address is `team.member`; the compact
	# vocabulary is the authority for that, not this renderer.
	#
	# W228 used the seam W49 left: `Do` is the viewer-relative action
	# cue, and adding it was one entry here plus one drop-order
	# position. It sits second in the VISUAL order, beside the selector,
	# because an owed action is the reason to act on the row at all —
	# and it drops LAST of the optional fields for the same reason. The
	# aggregate `oblig:1` in the header and the bold Work row say
	# something is owed somewhere; only this says which Message, and it
	# is the fact W228 found undiscoverable without leaving the TUI.
	MESSAGE_COLUMNS = (("Do", 4), ("From", 13), ("Time", 5), ("St", 4))
	MESSAGE_DROP_ORDER = ("Time", "St", "From", "Do")

	@staticmethod
	def message_id_width(messages) -> int:
		"""The `Id` allocation for ONE painted page: the longest visible
		`M<seq>`, never narrower than its own heading.

		Computed from the page rather than from a constant, so a
		sequence crossing a decimal boundary widens the column instead
		of clipping the one field every other operation is typed from.
		All rows in a paint share it."""
		widest = max((len(f"M{message['seq']}") for message in messages),
		             default=0)
		return max(len("Id"), widest)

	@staticmethod
	def message_cue_width(messages) -> int:
		"""The `Do` allocation for ONE painted page: the longest visible
		`@<seq>`, never narrower than its own heading.

		W228 R1: obligation sequences are monotonic and unbounded, so a
		FIXED four cells turns `@1000` into `@100` — not a hidden cue but
		a different obligation, and the operator would type the verb at
		whichever one that names. Sized from the page for exactly the
		reason `Id` is: a selector is the thing every command is typed
		from, so it widens the column rather than losing a digit."""
		widest = max((len(f"@{message['owed']['seq']}")
		              for message in messages if message.get("owed")),
		             default=0)
		return max(len("Do"), widest)

	@staticmethod
	def message_time_width(messages) -> int:
		"""The `Time` allocation for ONE painted page.

		W8160, and the same rule `message_cue_width` states: the
		declared width is a floor. Five cells were exactly `HH:MM`, and
		a local instant carries the zone that makes it readable as
		local. `Time` is first in `MESSAGE_DROP_ORDER` and still drops
		WHOLE under pressure — losing the column is honest, losing its
		suffix is the original defect."""
		widest = max((len(local_stamp(message.get("ts"), compact=True))
		              for message in messages or ()), default=0)
		return max(len("Time"), widest)

	@classmethod
	def message_columns(cls, cell_width: int, id_width: int,
	                    cue_width: int | None = None,
	                    time_width: int | None = None):
		"""The columns that fit, dropping whole fields in reverse
		priority. `Id` and the selection cue always survive: a row whose
		selector is gone cannot be acted on, so there is nothing left to
		render.

		`cue_width` is the page's own `Do` allocation and `time_width`
		its own `Time` allocation; each declared width is the minimum,
		never a cap."""
		widths = {name: width for name, width in cls.MESSAGE_COLUMNS}
		if cue_width is not None and "Do" in widths:
			widths["Do"] = max(widths["Do"], cue_width)
		if time_width is not None and "Time" in widths:
			widths["Time"] = max(widths["Time"], time_width)
		kept = [name for name, _width in cls.MESSAGE_COLUMNS]

		def used(names):
			total = id_width
			for name, _declared in cls.MESSAGE_COLUMNS:
				if name in names:
					total += 1 + widths[name]
			return total

		for candidate in cls.MESSAGE_DROP_ORDER:
			if used(kept) <= cell_width:
				break
			kept.remove(candidate)
		return [(name, widths[name]) for name, _declared
		        in cls.MESSAGE_COLUMNS if name in kept]

	def _message_cells(self, message) -> dict:
		# W228: `@<seq>` names the obligation this viewer owes on this
		# exact Message. A glyph alone would not identify WHICH
		# obligation, and the ruling requires legibility without relying
		# on colour, blink or bold — so the cue is text carrying the
		# local sequence the terminal verbs are typed with.
		owed = message.get("owed")
		return {
			"Do": f"@{owed['seq']}" if owed else "",
			"From": f"{message['author_team']}.{message['author']}",
			"Time": local_stamp(message.get("ts"), compact=True),
			"St": "new" if message.get("new") else "seen",
		}

	def _paint_index(self, screen, top, rows, x, cell_width, messages):
		"""The Message index as a fixed-column table: `M<seq>` (the
		existing stable sequence — nothing invented), author, event
		time, and the personal new/seen state, each clipped inside its
		own allocation so no field's overflow can move a later one.

		W76: the NEWEST Message paints at the top; the page itself stays
		canonical ascending everywhere else, so only this display order
		is reversed. The selected row is reversed; personal-new rows are
		bold; the window scrolls to keep the selection painted."""
		if not messages:
			screen.addnstr(top, x, "(no messages on this page)",
			               cell_width)
			return
		id_width = self.message_id_width(messages)
		columns = self.message_columns(
			cell_width, id_width, self.message_cue_width(messages),
			self.message_time_width(messages))
		header = "Id".ljust(id_width)
		for name, width in columns:
			header += " " + name.ljust(width)
		screen.addnstr(top, x, header[:cell_width].ljust(cell_width),
		               cell_width, curses.A_UNDERLINE)
		listing = max(0, rows - 1)
		if not listing:
			return
		messages = list(reversed(messages))
		seqs = [message["seq"] for message in messages]
		chosen = seqs.index(self.msg_cursor) \
			if self.msg_cursor in seqs else 0
		start = max(0, min(chosen - listing + 1, len(messages) - listing))
		start = max(0, start)
		for offset, message in enumerate(messages[start:start + listing]):
			cells = self._message_cells(message)
			text = f"M{message['seq']}".ljust(id_width)
			for name, width in columns:
				text += " " + cells[name][:width].ljust(width)
			attribute = 0
			if message["seq"] == self.msg_cursor:
				attribute = curses.A_REVERSE
			elif message.get("new"):
				attribute = curses.A_BOLD
			screen.addnstr(top + 1 + offset, x,
			               text[:cell_width].ljust(cell_width),
			               cell_width, attribute)

	def _paint_reader(self, screen, top, rows, x, cell_width, selected,
	                  focused=False):
		"""The reader: exactly ONE selected Message as its canonical
		formatted block — metadata header, wrapped body, Refs visually
		separate — scrolled by `reader_skip` with an honest `(cont.)`
		tag; a clipped tail is disclosed, never silently dropped.

		W30: there is no reader HEADING any more. It spent a whole row
		saying `Message M20` while the reversed index row already
		showed the selection and the metadata beneath already said
		`#20` — the same fact three times, one of them costing a body
		line. Focus therefore rides the first reader row, marked in the
		same `»` column the index heading uses; bold alone would not do,
		because unseen metadata is already bold."""
		marker = "»" if focused else " "
		if selected is None:
			screen.addnstr(top, x, marker + "(no message selected)",
			               cell_width)
			self.reader_clipped = False
			return
		# The marker owns column 0 of the cell, so the block wraps one
		# cell narrower. `format_message` happens to reserve a column of
		# its own, which would make this look redundant — it is not: the
		# reservation is stated HERE because the marker is painted here,
		# and it must not depend on another function's internal margin.
		block = format_message(selected, max(1, cell_width - 1))
		skip = min(self.reader_skip, max(0, len(block) - 1))
		self.reader_skip = skip
		visible = block[skip:]
		if skip:
			visible = [f"M{selected['seq']} (cont.)"] + visible
		take = max(0, min(len(visible), rows))
		for offset, text in enumerate(visible[:take]):
			attribute = curses.A_BOLD if offset == 0 and \
				(skip or selected.get("new")) else 0
			screen.addnstr(top + offset, x,
			               (marker if offset == 0 else " ") + text,
			               cell_width, attribute)
		shown = take - (1 if skip else 0)
		self.reader_clipped = skip + shown < len(block)

	def _render_message_region(self, screen, top, height, width,
	                           selected_thread) -> None:
		"""W14 (superseding W71's flat stream inside Work details): the
		lower region is a compact Message INDEX and a selected-message
		READER. At usable width the index sits left of the reader; at
		narrow width the same two regions stack, index above reader —
		never merged back into a flat body stream. Viewing and
		selection are read-only; only the explicit `s` writes, bounded
		by the chosen Message and no later one."""
		region = height - 2 - top
		if region < 2:
			return
		page_limit = max(1, region - 2)
		snapshot = self._cached(
			("thread", selected_thread["id"], self.thread_before,
			 page_limit),
			lambda: projection.thread(
				self.store, selected_thread["id"],
				viewer_team=self.team, viewer_member=self.member,
				before=self.thread_before,
				newest=self.thread_before is None, limit=page_limit))
		messages = snapshot["messages"]
		self.viewed_next_before = snapshot["next_before"]
		seqs = [message["seq"] for message in messages]
		self.viewed_seqs = seqs
		if self.msg_cursor not in seqs:
			# W76: ONE bounded read. The old entry path walked forward
			# through every page hunting the first personal-new Message,
			# which could load an entire Thread just to reach its tail.
			# Entering at the newest page makes that walk unnecessary —
			# see _autoselect_seq for why newest is also newest-unseen.
			# The selection is keyed by the STABLE seq: refresh, paging
			# and resize keep it while the Message remains present.
			self.msg_cursor = self._autoselect_seq(messages)
			self.reader_skip = 0
		if self.reader_skip_width != width:
			self.reader_skip = 0
			self.reader_skip_width = width
		selected = next((message for message in messages
		                 if message["seq"] == self.msg_cursor), None)
		index_bold = curses.A_BOLD if self.focus == "index" else 0
		imarker = "»" if self.focus == "index" else " "
		# W76: the index reads newest-first, so "more" is honestly OLDER.
		more = "  (n: older)" if snapshot["next_before"] is not None \
			else ""
		# W176 (finding-message-pane-header-redundancy): the split-area
		# headings identify PANE ROLES, never content already visible in
		# the selected Thread and Message rows. The Thread row owns the
		# subject; the reversed index row owns selection. W30 carried
		# that rule to its conclusion: the reader's own heading said
		# nothing the index row and the metadata beneath it did not
		# already say, so the reader has no heading and this is the
		# only pane label the region paints.
		# W29: `(total/unseen)` for the WHOLE Thread, both from the
		# canonical snapshot. `len(messages)` is the painted page, so
		# it reported ten rows as if the conversation held ten — the
		# heading an operator cannot reconcile with what they are
		# reading. The `(n: older)` continuation beside it still
		# describes paging, which is a different question.
		index_label = (f"{imarker}Messages "
		               f"({snapshot['total']}/{snapshot['new']}){more}")
		wide = width - 1 - self.INDEX_WIDTH - 2 >= self.MIN_READER
		if wide:
			reader_x = self.INDEX_WIDTH + 2
			reader_width = width - 1 - reader_x
			screen.addnstr(top, 0, index_label, self.INDEX_WIDTH,
			               index_bold)
			self._paint_index(screen, top + 1, region - 1, 0,
			                  self.INDEX_WIDTH, messages)
			# W30: the reader begins on the SAME row as the Message
			# index heading and keeps every row it had, so the body
			# viewport gains one line instead of spending it on a
			# label.
			self._paint_reader(screen, top, region, reader_x,
			                   reader_width, selected,
			                   focused=self.focus == "reader")
		else:
			# W49: +1 for the index's own column header. It is part of
			# the index, so the header's row comes out of the index's
			# allocation rather than out of its LISTING — otherwise
			# adding the header would silently drop the last visible
			# Message from a narrow page.
			index_rows = max(1, min(len(messages) or 1,
			                        max(2, region // 3),
			                        region - 2)) + 1
			screen.addnstr(top, 0, index_label, width - 1,
			               index_bold)
			self._paint_index(screen, top + 1, index_rows, 0,
			                  width - 1, messages)
			# Stacked: the reader starts immediately after the index
			# region, with no intervening label row.
			reader_top = top + 1 + index_rows
			self._paint_reader(screen, reader_top,
			                   top + region - reader_top, 0,
			                   width - 1, selected,
			                   focused=self.focus == "reader")
		# Operator-facing more/page state + the advertised controls
		# (ruled: paged surfaces disclose their controls; Ctrl-W is the
		# region convention; the seen action names its exact bound).
		bits = []
		if snapshot["next_before"] is not None:
			bits.append("older msgs — n older · p newest")
		elif self.thread_before is not None:
			bits.append("newer msgs — p newest")
		if self.reader_clipped:
			bits.append("reader: j scrolls")
		seen_label = f"M{self.msg_cursor}" if self.msg_cursor \
			else "selected"
		bits.extend(["Tab focus", "Ctrl-W panes", "j/k select",
		             f"s seen through {seen_label}", "Esc back"])
		self._detail_footer(screen, height, width, bits)

	# -- the command bar: the ONE public surface, in place ---------------------

	@staticmethod
	def _fixed_global_guard(argv) -> str | None:
		"""The console carries ONE validated participant and ONE bound
		configuration (C3). Re-entering either global in the command
		bar (or a batch line) would be identity by assertion — refused,
		with the reason. The W13 parser accepts full launcher
		spellings only (no abbreviation exists anywhere in the
		grammar), and this guard refuses the session-fixed globals up
		front so neither surface can ever retarget the console's
		validated identity or instance."""
		for token in argv:
			flag = token.split("=", 1)[0]
			guarded = any(
				len(flag) > 2 and fixed.startswith(flag)
				for fixed in ("--participant", "--config"))
			if guarded and flag.startswith("--"):
				return (f"{flag} names the session's fixed global "
				        f"participant/configuration; the command bar "
				        f"never re-enters them")
		return None

	def _run_line(self, argv):
		"""One command through the SAME public CLI entry the JSON agent
		uses — same config, same participant, same grammar, same
		refusals. Returns (code, brief, error, committed): the success
		brief or public refusal text, and whether a storage change
		ACTUALLY committed (R7: an effectively-once replay and a
		successful no-op change nothing)."""
		import contextlib
		import io
		import json as _json

		from baton_work.cli import MUTATIONS as _mutations
		out, err = io.StringIO(), io.StringIO()
		code = 1
		with contextlib.redirect_stdout(out), \
				contextlib.redirect_stderr(err):
			try:
				code = _cli.main(["--config", self.config_path,
				                  "--participant",
				                  f"{self.team}.{self.member}"] + argv)
			except SystemExit as stop:
				code = stop.code if isinstance(stop.code, int) else 1
			except WorkError as refusal:
				err.write(_json.dumps({"error": str(refusal)}))
		# R2/R4: the VERB is the first token after any operation
		# operand before it (op-id=V, ref=V, ... — the same public
		# grammar the JSON interface takes), never the first raw token.
		verb = None
		position = 0
		while position < len(argv):
			token = argv[position]
			if token.startswith("--"):
				position += 1 if "=" in token else 2
				continue
			verb = token
			break
		if code == 0:
			brief = "ok"
			try:
				result = _json.loads(out.getvalue())["result"]
			except (ValueError, KeyError):
				result = None
			committed = verb in _mutations
			if committed and isinstance(result, dict):
				operation = result.get("operation")
				if isinstance(operation, dict) and \
						operation.get("state") == "replayed":
					committed = False
				if result.get("advanced") is False:
					committed = False
			if isinstance(result, dict):
				for key in ("work_id", "seq", "revision", "generation"):
					if key in result:
						brief += f" {key}={result[key]}"
			return 0, brief, "", committed
		try:
			error = _json.loads(err.getvalue())["error"][:200]
		except ValueError:
			error = (err.getvalue() or "refused").strip()[:200]
		return code, "", error, False

	def _prose_context(self, argv) -> list:
		"""Whatever context the command and the current view supply —
		the Work or Thread being acted on, with its title when the
		cached window happens to know it. Never a read the operator did
		not already cause: this uses the SAME cached projection the
		screen is drawn from, so opening an editor cannot touch the
		authority."""
		context = []
		operands = {}
		for token in argv[1:]:
			key, equals, value = token.partition("=")
			if equals and key not in operands:
				operands[key] = value
		named = operands.get("work")
		if named is None and self.detail_work is not None:
			named = self.detail_work
		if named is not None:
			title = None
			for row in self.rows():
				if named in (row["id"], row["local_id"]):
					title = row["title"]
					break
			context.append(f"Work {named}"
			               + (f" — {title}" if title else ""))
		if "thread" in operands:
			context.append(f"Thread {operands['thread']}")
		context.append(f"Participant {self.team}.{self.member}")
		return context

	def _prose_refused(self, line: str, note: str) -> None:
		"""Hand the draft back INTACT and say why.

		Every failure of the round trip lands here — no editor
		configured, an unlaunchable one, a nonzero exit, an empty or
		unchanged document. The operator gets the exact command they
		pressed Enter on, in the bar, with the caret at its end, and
		nothing was submitted."""
		self._set_command(line)
		self.command_note = note

	def _author_prose(self, line: str, argv, key: str):
		"""One external-editor round trip for one missing prose operand.

		Returns the authored text, or None when it refused or cancelled
		— in which case the draft is already back in the bar.

		`EDITOR` ONLY, and split into an argument vector WITHOUT a
		shell. Resolving `VISUAL` too, or falling back to a guess, would
		mean Baton sometimes choosing an editor the operator did not
		configure; passing the value to a shell would make the
		environment a command-injection surface for a feature whose
		whole job is to open a text file."""
		spec = os.environ.get("EDITOR")
		if not spec or not spec.strip():
			self._prose_refused(
				line, f"{key}= needs prose: set EDITOR to author it")
			return None
		try:
			command = shlex.split(spec)
		except ValueError:
			command = []
		if not command:
			self._prose_refused(
				line, "EDITOR is not a usable command; draft kept")
			return None
		document = prose_template(argv[0], key, self._prose_context(argv))
		handle, path = tempfile.mkstemp(prefix="baton-prose-",
		                                suffix=".txt")
		try:
			with os.fdopen(handle, "w", encoding="utf-8") as draft:
				# Explicitly, not by relying on the default: the draft
				# holds whatever the operator is about to say. Inside
				# the `with`, so no path through here can leak the
				# descriptor.
				os.fchmod(draft.fileno(), 0o600)
				draft.write(document)
			try:
				# Give the terminal back before the editor draws on it;
				# the render that follows this key restores curses.
				curses.endwin()
			except curses.error:
				pass
			try:
				done = subprocess.run(command + [path], check=False)
			except OSError as broken:
				self._prose_refused(
					line, f"EDITOR could not run: {broken.strerror}")
				return None
			if done.returncode != 0:
				self._prose_refused(
					line, f"editor exited {done.returncode}; "
					f"nothing submitted")
				return None
			with open(path, encoding="utf-8") as saved:
				text = saved.read()
		except KeyboardInterrupt:
			# W36 review 2026-08-19: a terminal SIGINT reaches the whole
			# FOREGROUND GROUP, so Baton receives it alongside the editor
			# it is waiting on. Every other way this round trip can fail
			# is already a safe cancellation, and an interrupt has to be
			# one too — `_command_key` closed the bar before calling
			# `execute`, so letting this propagate tears the console down
			# and takes the operator's draft with it.
			#
			# The whole interaction is covered, not only the wait: an
			# interrupt landing a moment later, while the authored text
			# is being read back, would escape exactly the same way.
			# `BaseException` does not reach the ordinary handlers, so
			# it is named here or it is not caught at all.
			self._prose_refused(
				line, f"{key}= editing interrupted; nothing submitted")
			return None
		finally:
			try:
				os.unlink(path)
			except OSError:
				pass
		value = strip_prose_template(text)
		if not value.strip():
			self._prose_refused(line, f"{key}= left empty; nothing submitted")
			return None
		return value

	def execute(self, line: str) -> None:
		"""The one-line `:` bar: feed the typed command through
		`_run_line` and surface the brief or the refusal."""
		# W26: the submission is recorded HERE, before any refusal
		# path, and never from a success status or an authority event.
		# Every one-line submission passes through this method — local
		# `filter` included — so this is the single point where "the
		# operator submitted this text" is true.
		self._remember(line)
		if self.config_path is None:
			self.status = "no config path; the command bar is unavailable"
			return
		try:
			argv = shlex.split(line)
		except ValueError as broken:
			self.status = f"unparseable command: {broken}"
			return
		if not argv:
			return
		if argv[0] == "filter":
			# W5: client-local view state — handled HERE, never sent
			# to the authority surface.
			self._set_filter(argv[1:])
			return
		if argv[0] == "tui":
			self.status = "already here"
			return
		guard = self._fixed_global_guard(argv)
		if guard:
			self.status = guard
			return
		# W36: a REQUIRED prose operand the line does not carry opens
		# the editor instead of returning a bare missing-operand
		# refusal. The grammar decides which operand that is; a supplied
		# one never gets here, and a missing non-prose operand still
		# refuses normally through `_run_line` below.
		#
		# The authored value is APPENDED AS AN ARGV TOKEN rather than
		# spliced into the command string. There is no second round of
		# shell quoting to survive, so a body with quotes, newlines or
		# Unicode reaches the canonical path exactly as it was written.
		prose_key = _cli.missing_prose_operand(line)
		if prose_key is not None:
			authored = self._author_prose(line, argv, prose_key)
			if authored is None:
				return
			argv = argv + [f"{prose_key}={authored}"]
		code, brief, error, committed = self._run_line(argv)
		# R7: only an ACTUAL storage change schedules a refresh.
		if committed:
			self.schedule_refresh()
		self.status = brief if code == 0 else error

	# -- the `::` batch buffer (W19) -------------------------------------------

	@staticmethod
	def _batch_line(text: str) -> dict:
		return {"text": text, "state": None, "note": "", "op_id": None}

	@staticmethod
	def _batch_edited(entry: dict) -> None:
		"""Any edit returns the line to staged AND discards its
		generated identity: WS-5 fingerprints the typed input, so an
		edited line is a NEW command — reusing the old identity would
		refuse as an identity conflict."""
		entry["state"] = None
		entry["note"] = ""
		entry["op_id"] = None

	def _batch_close(self) -> None:
		if self.batch_status:
			self.status = self.batch_status
		self.batch = None
		self.batch_cursor = 0
		self.batch_confirm = False
		self.batch_status = ""

	def _batch_key(self, key: int) -> bool:
		"""Keys while the batch buffer is open. Enter is ONLY ever a
		newline (a pasted newline can never execute); Ctrl-G is Go;
		Esc cancels behind a one-row confirmation whenever the buffer
		still holds unexecuted text."""
		if self.batch_confirm:
			if key in (ord("y"), ord("Y")):
				self.batch_status = ""
				self._batch_close()
			elif key in (ord("n"), ord("N"), 27):
				self.batch_confirm = False
			return True
		entry = self.batch[self.batch_cursor]
		if key == 27:
			if any(line["text"].strip() and
			       line["state"] != "completed"
			       for line in self.batch):
				self.batch_confirm = True
			else:
				self._batch_close()
			return True
		if key == 7:  # Ctrl-G: Go
			self._batch_go()
			return True
		if key in (10, 13, curses.KEY_ENTER):
			# R1 (trial 2): every buffer MUTATION makes the previous
			# run summary stale — invalidate it so the legend's
			# Go/cancel controls return. Cursor-only movement (below)
			# keeps a still-applicable summary.
			self.batch_status = ""
			self.batch.insert(self.batch_cursor + 1,
			                  self._batch_line(""))
			self.batch_cursor += 1
			return True
		if key == curses.KEY_UP:
			self.batch_cursor = max(0, self.batch_cursor - 1)
			return True
		if key == curses.KEY_DOWN:
			self.batch_cursor = min(len(self.batch) - 1,
			                        self.batch_cursor + 1)
			return True
		if key in (8, 127, curses.KEY_BACKSPACE):
			if entry["text"]:
				self.batch_status = ""
				entry["text"] = entry["text"][:-1]
				self._batch_edited(entry)
			elif len(self.batch) > 1:
				self.batch_status = ""
				del self.batch[self.batch_cursor]
				self.batch_cursor = max(0, self.batch_cursor - 1)
			return True
		if 32 <= key <= 126:
			self.batch_status = ""
			entry["text"] += chr(key)
			self._batch_edited(entry)
			return True
		return True

	def _batch_go(self) -> None:
		"""Go (pinned): preflight EVERY pending line statically — the
		fixed-global guard and THE shared parser, before any authority
		access; any refusal marks its line failed and NOTHING executes.
		Then assign per-slot operation identity to mutating lines
		without an explicit op-id=, and execute sequentially in written
		order through the same public entry as the one-line bar,
		stopping at the first refusal: earlier lines are completed
		(committed — never rolled back), the rest unrun. Completed
		lines are skipped by later Gos; an unedited retry keeps its
		identity, so WS-5 replays any committed result instead of
		duplicating it."""
		if self.config_path is None:
			self.batch_status = ("no config path; the command bar is "
			                     "unavailable")
			return
		pending = []
		preflight_error = None
		for entry in self.batch:
			if not entry["text"].strip() or \
					entry["state"] == "completed":
				continue
			entry["state"] = None
			entry["note"] = ""
			try:
				argv = shlex.split(entry["text"])
			except ValueError as broken:
				entry["state"] = "failed"
				entry["note"] = f"unparseable command: {broken}"
				preflight_error = preflight_error or entry["note"]
				continue
			guard = self._fixed_global_guard(argv)
			if guard:
				entry["state"] = "failed"
				entry["note"] = guard
				preflight_error = preflight_error or guard
				continue
			try:
				args = _cli._parse_invocation(
					["--config", self.config_path, "--participant",
					 f"{self.team}.{self.member}"] + argv)
			except WorkError as refusal:
				entry["state"] = "failed"
				entry["note"] = str(refusal)
				preflight_error = preflight_error or str(refusal)
				continue
			if args.command == "tui":
				entry["state"] = "failed"
				entry["note"] = "already here"
				preflight_error = preflight_error or "already here"
				continue
			pending.append((entry, argv, args))
		if preflight_error:
			self.batch_status = ("nothing ran — "
			                     + preflight_error)[:200]
			return
		if not pending:
			self.batch_status = "nothing to run"
			return
		# Per-slot identity (pinned): generated for MUTATING lines
		# without an explicit op-id=, retained while the text is
		# unchanged, never touching an explicit one. Two identical
		# lines are two commands — a batch is a list, never a set.
		for entry, _argv, args in pending:
			if args.command in _cli.MUTATIONS and \
					args.op_id is None and entry["op_id"] is None:
				entry["op_id"] = "batch-" + uuid.uuid4().hex
		completed = 0
		stopped = None
		refresh = False
		for entry, argv, args in pending:
			if stopped is not None:
				entry["state"] = "unrun"
				continue
			run_argv = list(argv)
			if entry["op_id"] is not None and args.op_id is None:
				run_argv.append("op-id=" + entry["op_id"])
			code, brief, error, committed = self._run_line(run_argv)
			if code == 0:
				entry["state"] = "completed"
				entry["note"] = brief
				completed += 1
				refresh = refresh or committed
			else:
				entry["state"] = "failed"
				entry["note"] = error
				stopped = error
		if refresh:
			self.schedule_refresh()
		if stopped is not None:
			self.batch_status = (f"{completed} completed; stopped: "
			                     + stopped)[:200]
		else:
			self.batch_status = f"batch: {completed} completed"

	def _render_batch(self, screen, height: int, width: int):
		"""W19: the staged batch — a bottom pane of state-marked lines
		over one legend row naming Go and cancellation. The cursor line
		renders with the W14 caret/viewport contract and the shared
		read-only assistance; other lines truncate on screen only (the
		buffer is never cut). Returns the caret position or None."""
		rows = min(len(self.batch), max(3, height // 3))
		first = min(self.batch_cursor,
		            max(0, len(self.batch) - rows))
		if self.batch_cursor >= first + rows:
			first = self.batch_cursor - rows + 1
		top = height - 1 - rows
		marks = {None: "   ", "completed": "ok ", "failed": "!! ",
		         "unrun": "-- "}
		caret = None
		for offset in range(rows):
			index = first + offset
			if index >= len(self.batch):
				break
			entry = self.batch[index]
			y = top + offset
			screen.addnstr(y, 0, " " * (width - 1), width - 1)
			attr = {"completed": curses.A_DIM,
			        "failed": curses.A_BOLD}.get(entry["state"], 0)
			screen.addnstr(y, 0, marks[entry["state"]], 3, attr)
			text = entry["text"]
			avail = width - 1 - 3
			if index == self.batch_cursor and avail > 2:
				if len(text) < avail:
					screen.addnstr(y, 3, text, avail)
					room = avail - len(text) - 2
					if room >= 8:
						hint = assist_text(text)
						screen.addnstr(y, 3 + len(text) + 2,
						               hint[:room], room,
						               curses.A_DIM)
					caret = (y, 3 + len(text))
				else:
					tail = text[len(text) - (avail - 2):]
					screen.addnstr(y, 3, "<" + tail, avail)
					caret = (y, 3 + 1 + len(tail))
			else:
				screen.addnstr(y, 3, text[:avail], avail, attr)
		legend_row = height - 1
		screen.addnstr(legend_row, 0, " " * (width - 1), width - 1)
		if self.batch_confirm:
			screen.addnstr(legend_row, 0, "Discard batch? y/N",
			               width - 1)
			return None
		if self.batch_status:
			screen.addnstr(legend_row, 0, self.batch_status,
			               width - 1)
		else:
			screen.addnstr(legend_row, 0,
			               "batch · Enter newline · Ctrl-G go · "
			               "Esc cancel", width - 1, curses.A_DIM)
		return caret

	def _search_entry_key(self, key: int) -> None:
		"""The one-line query bar: typing is pure client state; Enter
		submits ONE canonical search; Esc cancels without touching the
		current view; an empty query refuses locally."""
		if key in (10, 13, curses.KEY_ENTER):
			query = self.search_input.strip()
			if not query:
				self.status = "search needs a non-empty query"
				self.search_input = None
				return
			if self.mode != "search":
				# entering search: remember the EXACT prior table
				# state — including closed visibility (R2) — for the
				# Esc restoration.
				#
				# W292: results are a page the operator drilled INTO,
				# so the same navigation frame carries that state and
				# the breadcrumb names the query. `search_saved` stays
				# as the frame's payload rather than a second mechanism
				# beside it.
				self.search_saved = (list(self.path), self.cursor,
				                     self.selected_id,
				                     self.show_closed)
				self._nav_push("search", f"search: {query}")
			elif self.nav and self.nav[-1]["kind"] == "search":
				# A replacement query is the SAME level, relabelled —
				# `/` from results does not nest a second search inside
				# the first, and one Esc still reaches the table.
				self.nav[-1]["label"] = f"search: {query}"
				if self.location and self.location[-1]["kind"] == "search":
					self.location[-1]["label"] = f"search: {query}"
			self.search_query = query
			self.search_after = 0
			self.search_page = 1
			self.search_input = None
			self.cursor = 0
			self.selected_id = None
			self.mode = "search"
		elif key == 27:
			self.search_input = None
		elif key in (8, 127, curses.KEY_BACKSPACE):
			self.search_input = self.search_input[:-1]
		elif 32 <= key <= 126:
			self.search_input += chr(key)

	def _claim_selected(self, rows) -> None:
		"""W235 (+R1): claim the chosen Work through the ONE canonical
		command path — the same atomic claim operation and the same
		committed-only refresh the typed bar uses — shared by the root
		table and the search-result mode. The authority stays final: a
		refusal surfaces its diagnostic untouched and no local state
		pretends otherwise; the id-anchored selection survives the
		refresh. Search-entry text and the detail panes never reach
		this helper."""
		target = rows[min(self.cursor, len(rows) - 1)]["id"]
		self.selected_id = target
		self.execute(f"claim work={target}")

	# -- W17: the poke view's actions -------------------------------------

	def _run_authored(self, line: str, key: str) -> None:
		"""Run one CONSOLE-COMPOSED command whose durable prose the
		operator authors in the editor.

		Nothing composed here is guessed: the selector comes from the
		selected row and any closed operand from the grammar's own
		vocabulary, so the only thing left for a human is the prose. It
		is the same public CLI entry, the same refusals and the same
		committed-only refresh the typed bar uses — including the
		refusal path, which hands the intact command back to the bar
		rather than dropping it when there is no editor to author in.

		W36's `missing_prose_operand` route is deliberately not reused:
		that one answers "which REQUIRED prose operand is this typed
		line still missing", and here the console already knows which
		operand it is composing around."""
		if self.config_path is None:
			self.status = "no config path; the command bar is unavailable"
			return
		argv = shlex.split(line)
		authored = self._author_prose(line, argv, key)
		if authored is None:
			return
		self._remember(line)
		code, brief, error, committed = self._run_line(
			argv + [f"{key}={authored}"])
		if committed:
			self.schedule_refresh()
		self.status = brief if code == 0 else error

	def _open_pokes_nav(self) -> None:
		"""W292: the poke view is reached from Jobs and returns to it,
		so it is a drilled page and takes a breadcrumb segment. It has
		no local tabs, which is a property of this page rather than an
		exception to the model."""
		self._nav_push("pokes", "pokes")

	def _open_pokes(self) -> None:
		"""Enter the poke view on the row that wants an answer — owed
		pokes sort first, so that is simply the first row."""
		self._open_pokes_nav()
		self.mode = "pokes"
		self.poke_cursor = 0
		self.poke_seq = None
		rows, _older = self.poke_rows()
		if rows:
			self.poke_seq = rows[0]["poke"]

	def _poke_choice_key(self, key: int) -> bool:
		"""The one state key that turns the chosen poke into an answer.

		Digits rather than initials: the vocabulary is the grammar's, so
		two states sharing a first letter must not decide which one an
		operator can reach — and a positional key stays correct when the
		vocabulary grows. Esc cancels; every other key neither answers
		nor cancels, exactly as the exit prompt behaves."""
		states = poke_answer_states()
		if key == 27:
			self.poke_choice = None
			return True
		if ord("1") <= key <= ord("9"):
			index = key - ord("1")
			if index < len(states):
				poke, self.poke_choice = self.poke_choice, None
				self._run_authored(f"poke-answer poke={poke} "
				                   f"state={states[index]}",
				                   "explanation")
		return True

	def _handle_inbox(self, key: int) -> bool:
		"""The Inbox tab's keys. Selection is view state; every action
		runs a public verb and none of them infers authority."""
		rows = self.inbox_rows()
		selected = self._inbox_selected()
		if key in (curses.KEY_DOWN, ord("j")):
			self.inbox_cursor = min(self.inbox_cursor + 1,
			                        max(0, len(rows) - 1))
			self._inbox_anchor(rows)
		elif key in (curses.KEY_UP, ord("k")):
			self.inbox_cursor = max(0, self.inbox_cursor - 1)
			self._inbox_anchor(rows)
		elif key in (curses.KEY_ENTER, 10, 13) and selected:
			if not selected["work"]:
				self.status = (f"{selected['selector']} has no Work "
				               f"context; a poke names a participant, "
				               f"not Work")
			else:
				# The row LINKS to its context rather than reproducing
				# it: Jobs owns Work, and this hands the operator over
				# to it with the right row already open.
				self.tab = "jobs"
				self._enter_detail(selected["work"], came_from="table")
		elif key == ord("a") and selected:
			if selected["kind"] == "incident":
				# W415: authored, because a dismissal that records why
				# is what the next reader needs when it recurs.
				self._run_authored(
					f"dismiss incident={selected['incident']}", "note")
			elif selected["kind"] == "poke":
				self.poke_choice = selected["poke"]
			elif selected["kind"] == "obligation":
				self._run_authored(
					f"respond obligation={selected['obligation']}",
					"body")
			else:
				self.status = (f"{selected['selector']} is answered "
				               f"through {', '.join(selected['completes_by']) or 'no console action'}"
				               f"; open it in Jobs")
		elif key == ord("s") and selected:
			if selected["kind"] == "incident":
				# The ruled point, said out loud: marking discussion
				# seen is not how an operational incident is answered.
				self.status = (f"{selected['selector']} is an incident, "
				               f"not a message; it stays until you "
				               f"dismiss it with `a`")
			elif not selected["thread"]:
				self.status = (f"{selected['selector']} has no thread; "
				               f"there is no seen cursor to move")
			else:
				self.execute(f"mark-seen thread={selected['thread']} "
				             f"up-to={selected['message']}")
		return True

	def _inbox_anchor(self, rows) -> None:
		if rows:
			chosen = rows[min(self.inbox_cursor, len(rows) - 1)]
			self.inbox_key = chosen["action_key"] or chosen["selector"]

	def _handle_teams(self, key: int) -> bool:
		"""The Teams tab's keys. `p` asks a member what is going on —
		the one wake that names a participant instead of resolving a
		route — and `x` withdraws the one this participant has
		outstanding to them."""
		rows = self.team_rows()
		selected = self._team_selected()
		if key in (curses.KEY_DOWN, ord("j")):
			self.team_cursor = min(self.team_cursor + 1,
			                       max(0, len(rows) - 1))
			if rows:
				self.team_member = rows[self.team_cursor]["participant"]
		elif key in (curses.KEY_UP, ord("k")):
			self.team_cursor = max(0, self.team_cursor - 1)
			if rows:
				self.team_member = rows[self.team_cursor]["participant"]
		elif key == ord("t"):
			self.teams_own_only = not self.teams_own_only
			self.team_cursor = 0
		elif key == ord("p") and selected:
			self._run_authored(
				f"poke target={selected['participant']}", "request")
		elif key == ord("x") and selected:
			outstanding = self._pending_poke_to(selected)
			if outstanding is None:
				self.status = (f"you have no pending poke to "
				               f"{selected['participant']}")
			else:
				self._run_authored(f"poke-cancel poke={outstanding}",
				                   "reason")
		return True

	def _handle_pokes(self, key: int) -> bool:
		"""The poke view's keys. Selection is view state; both actions
		run public verbs and neither infers authority."""
		rows, _older = self.poke_rows()
		selected = self._poke_selected()
		if key in (curses.KEY_DOWN, ord("j")):
			self.poke_cursor = min(self.poke_cursor + 1,
			                       max(0, len(rows) - 1))
			self.poke_seq = rows[self.poke_cursor]["poke"] if rows \
				else None
		elif key in (curses.KEY_UP, ord("k")) and self.poke_cursor == 0:
			self._enter_breadcrumb()
		elif key in (curses.KEY_UP, ord("k")):
			self.poke_cursor = max(0, self.poke_cursor - 1)
			self.poke_seq = rows[self.poke_cursor]["poke"] if rows \
				else None
		elif key == ord("a") and selected is not None:
			if selected["owed"]:
				self.poke_choice = selected["poke"]
			else:
				# Locally certain and cheap to say: a poke names ONE
				# participant, and this one is not it — or it is already
				# terminal. Spending an editor round trip to reach the
				# authority's refusal would ask for prose that could
				# never be submitted.
				self.status = (f"poke {selected['poke']} is "
				               f"{selected['state']} and owed by "
				               f"{selected['target']}; only the exact "
				               f"participant a poke names answers it")
		elif key == ord("x") and selected is not None:
			if selected["state"] == "pending":
				# Pending is the only part of eligibility presentation
				# may decide — WHO may withdraw (the asker, or a
				# config-capability holder) is the authority's answer,
				# so the verb runs and its refusal speaks for itself.
				self._run_authored(f"poke-cancel poke={selected['poke']}",
				                   "reason")
			else:
				self.status = (f"poke {selected['poke']} is already "
				               f"{selected['state']}; a terminal poke "
				               f"cannot be withdrawn")
		elif key in (27, curses.KEY_LEFT, ord("p")):
			# W292: one segment out, restoring the table the poke view
			# was opened from.
			if not self._nav_pop():
				self.mode = "table"
		return True

	def _search_mode_key(self, key: int) -> bool:
		"""The flat result mode: ordinary selection, ordinary detail
		entry, replacement queries, bounded paging, and the exact Esc
		restoration of the prior Work window."""
		rows, _hidden = self.visible_rows(self.search_rows())
		if key in (curses.KEY_DOWN, ord("j")):
			self.cursor = min(self.cursor + 1, max(0, len(rows) - 1))
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_UP, ord("k")) and self.cursor == 0:
			self._enter_breadcrumb()
		elif key in (curses.KEY_UP, ord("k")):
			self.cursor = max(0, self.cursor - 1)
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_ENTER, 10, 13) and rows:
			self._enter_detail(rows[min(self.cursor,
			                            len(rows) - 1)]["id"],
			                   came_from="search")
		elif key == ord("n") and self.search_next is not None:
			self.search_after = self.search_next
			self.search_page += 1
			self.cursor = 0
			self.selected_id = None
		elif key == ord("p"):
			self.search_after = 0
			self.search_page = 1
			self.cursor = 0
			self.selected_id = None
		elif key == ord("z"):
			# toggling visibility changes the effective paging
			# universe — restart at page one of the new universe
			self.show_closed = not self.show_closed
			self.search_after = 0
			self.search_page = 1
			self.cursor = 0
			self.selected_id = None
		elif key == ord("c") and rows:
			# W235 R1: search results are selectable Work — the SAME
			# shared claim path as the root table.
			self._claim_selected(rows)
		elif key == ord("d") and rows:
			# W4996: and so is the dependency neighbourhood. The approved
			# entry boundary names the table AND search, and search mode
			# is dispatched before the table's own `d` case ever runs —
			# so without this branch the key was simply a no-op here.
			#
			# W96: the key is `d` for deps. It was `b`, inherited from the
			# earlier blocker/link presentation, and this view has shown
			# both prerequisites and dependents since W4996 — so `b` named
			# half of what it opened. Removed outright, with no alias: a
			# hidden compatibility binding is a second contract nobody
			# advertises and nobody tests.
			# A search result is a Work like any other, and an operator
			# who found one by searching is exactly the operator who
			# wants to see what it waits on.
			self._open_graph(rows[min(self.cursor, len(rows) - 1)]["id"])
		elif key == 27:
			# the exact prior table state returns — path, cursor,
			# selection, AND closed visibility (R2); the filter was
			# never search's to change.
			#
			# W292: one Back pops the search segment. The frame carries
			# the same state `search_saved` did, so the restoration is
			# unchanged; what changed is that it is now the SAME
			# mechanism every other drilled page uses.
			if not self._nav_pop():
				path, cursor, selected, shown = \
					self.search_saved or ([], 0, None, self.show_closed)
				self.path = path
				self.cursor = cursor
				self.selected_id = selected
				self.show_closed = shown
				self.mode = "table"
			self.search_query = None
			self.search_saved = None
		return True

	def _set_filter(self, tokens) -> None:
		"""W5: replace the client-local filter atomically through the
		SAME shared grammar and validation the launch operands use.
		Bare `filter` clears. A refusal changes neither the filter nor
		anything else — no plausible partial view."""
		try:
			args = _cli._parse_invocation(
				["--config", self.config_path or "-",
				 "--participant", f"{self.team}.{self.member}",
				 "filter"] + list(tokens))
			pairs = _cli._filter_operands(args)
			normalized = projection.normalize_filter(
				self.store, pairs, self.team)
		except WorkError as refusal:
			self.status = str(refusal)[:200]
			return
		self.work_filter = normalized
		self.status = ("filter cleared" if normalized is None
		               else "filter: " + self._filter_clauses())

	def _filter_clauses(self) -> str:
		return " ".join(f"{field}={value}" for field, value
		                in (self.work_filter or {}).items())

	@staticmethod
	def _explicit_operands(buffer: str, key: str) -> int | None:
		"""W81 R3: how many REAL `key=` operands the buffer carries,
		read through the command grammar's OWN partial tokenizer.

		The first attempt at this was a second, approximate lexer, and
		it disagreed with execution in both directions — first counting
		`thread=` inside a quoted value (R1), then counting it after an
		ESCAPED space that `shlex` does not treat as a token boundary
		at all (R3). Extending an approximation one escape case at a
		time is how the two interpretations keep drifting; the fix is to
		have only one. `cli._partial_tokens` is the same partial-`shlex`
		reading the assistance and the parser already share, so
		detection and execution cannot disagree about quotes,
		backslashes, or escaped whitespace — and an escaped spelling
		that `shlex` resolves INTO a genuine operand is counted,
		because by then it genuinely is one.

		Returns None when the line cannot be tokenized even under the
		quote rules (a trailing escape). Callers treat that as "do not
		touch the seed": the safe direction, since the failure this
		guards against is silently deleting a destination."""
		parsed = _cli._partial_tokens(buffer)
		if parsed is None:
			return None
		completed, live, _open_quote = parsed
		tokens = list(completed)
		if live is not None:
			tokens.append(live)
		# token 0 is the verb; operands follow it
		return sum(1 for token in tokens[1:] if token.startswith(key))

	def _selected_thread_selector(self) -> str | None:
		"""The ONE unambiguous selected Thread's visible local selector,
		or None. Root/list views and empty Thread views have no
		selection and must not invent a destination.

		The selector is the row's `local_id` — what the Threads pane
		actually shows and what `say thread=` actually accepts. Never
		the Work-scoped label ordinal (W7 showed those diverge) and
		never a canonical id the client reassembled for itself."""
		# W81 R2: the seed means "reply where I am READING". While the
		# Events tab is active there is no visible selected Thread, so
		# seeding from the retained Messages cursor would invent a
		# destination the operator cannot see.
		if self.mode != "detail" or self.detail_work is None:
			return None
		if self.detail_tab != "messages":
			return None
		rows = self.thread_rows()
		if not rows or self.disc_cursor is None:
			return None
		chosen = rows[min(self.disc_cursor, len(rows) - 1)]
		return chosen.get("local_id")

	def _reconcile_say_seed(self) -> None:
		"""W81: seed `thread=` from where the operator is reading.

		Seeding happens ONCE, at the moment the buffer becomes exactly
		`say`, and only in a detail view with one selected Thread. The
		seeded value is a SNAPSHOT of context: later focus or selection
		movement never retargets a command the operator is already
		composing.

		An explicit `thread=` — typed or pasted — always wins. Paste in
		a curses bar is indistinguishable from fast typing, so a pasted
		`say thread=T5 ...` necessarily passes through the exact-`say`
		moment and picks up the seed; when its own operand then arrives,
		the seed is removed rather than left to duplicate. That is the
		ruled "never duplicates or overwrites an explicit thread=",
		enforced by construction instead of by hoping paste looks
		different from typing."""
		if self.command is None:
			self.seeded_say = None
			return
		if self.seeded_say is not None:
			if self.seeded_say not in self.command:
				# edited away by hand; it is no longer ours to manage
				self.seeded_say = None
			elif (self._explicit_operands(self.command, "thread=")
			      or 0) > 1:
				at = self.command.index(self.seeded_say)
				rest = self.command[at + len(self.seeded_say):]
				head = self.command[:at]
				# the seed carries its own trailing space; dropping it
				# next to the space that preceded it would leave a gap
				if head.endswith(" ") and rest.startswith(" "):
					rest = rest[1:]
				# W35: the caret rides the splice. Text before the
				# removed seed is untouched; a caret after it shifts
				# left by exactly what vanished, and one that was
				# INSIDE the seed lands where the seed was — the
				# operator keeps editing the place they were looking
				# at rather than being thrown to the end.
				removed = len(self.command) - len(head + rest)
				caret = self.command_caret
				if caret > at:
					caret = max(at, caret - removed)
				self._set_command(head + rest, caret)
				self.seeded_say = None
			return
		if self.command != "say":
			return
		selector = self._selected_thread_selector()
		if selector is None:
			return
		self.seeded_say = f"thread={selector} "
		self._set_command(f"say {self.seeded_say}")

	def _remember(self, line: str) -> None:
		"""W26: record one SUBMITTED command.

		Every non-empty submission enters history, including one the
		parser or the authority refuses — correcting a refused command
		is the primary reason the feature exists, so deriving history
		from success would omit exactly the entries most worth
		recalling. Adjacent identical submissions collapse, and the
		bound evicts oldest-first."""
		text = line.strip()
		if not text or (self.history and self.history[-1] == text):
			return
		self.history.append(text)
		if len(self.history) > HISTORY_LIMIT:
			del self.history[:len(self.history) - HISTORY_LIMIT]

	def _history_step(self, older: bool) -> None:
		"""Up walks toward older entries, Down toward newer. Down past
		the newest restores the scratch draft the operator had before
		navigating."""
		if not self.history:
			return
		if self.history_cursor is None:
			if not older:
				return
			self.history_draft = (self.command, self.command_caret)
			self.history_cursor = len(self.history) - 1
		elif older:
			self.history_cursor = max(0, self.history_cursor - 1)
		else:
			self.history_cursor += 1
			if self.history_cursor >= len(self.history):
				# past the newest: the draft, exactly as it was
				self.history_cursor = None
				draft, caret = self.history_draft or ("", 0)
				self._set_command(draft, caret)
				self.history_draft = None
				self._reconcile_say_seed()
				return
		# W35: a recalled entry arrives with the caret at its end. It is
		# an independent DRAFT from that moment — editing it never
		# reaches back into `history`, which stays immutable.
		self._set_command(self.history[self.history_cursor])
		self._reconcile_say_seed()

	def _reverse_match(self, query: str, before: int | None) -> int | None:
		"""The newest entry at or before `before` containing `query`.
		Case-sensitive, as ruled."""
		start = len(self.history) - 1 if before is None else before
		for index in range(start, -1, -1):
			if query in self.history[index]:
				return index
		return None

	def _reverse_adopt(self) -> None:
		"""Take the displayed match into the ordinary buffer and leave
		search. Nothing executes: this is the `recall, tweak, rerun`
		path, and the tweak happens in the normal editor."""
		if self.reverse is not None and self.reverse["match"] is not None:
			self._set_command(self.history[self.reverse["match"]])
		self.reverse = None
		self._reconcile_say_seed()

	def _reverse_key(self, key: int) -> None:
		"""Incremental reverse search. Shell-familiar by ruling:
		typing NARROWS, repeated Ctrl-R steps to the next older match,
		Right or Tab accepts, Enter submits, Esc restores the draft."""
		state = self.reverse
		if key in (10, 13, curses.KEY_ENTER):
			if state["match"] is None:
				# Enter submits the chosen match. With nothing
				# chosen there is nothing to submit — and the buffer
				# behind the prompt is the pre-search draft, which the
				# operator can no longer see. Running it would execute
				# invisible text. Staying in search is the safe
				# reading: Esc still restores that draft deliberately.
				return
			self._reverse_adopt()
			line = self.command
			self._set_command(None)
			self.seeded_say = None
			self.history_cursor = self.history_draft = None
			self.execute(line)
			return
		if key == 27:
			# cancel: the pre-search draft, byte for byte — and W35
			# adds "caret for caret", because a draft restored with the
			# caret moved is not the draft that was left
			self._set_command(state["draft"], state["caret"])
			self.reverse = None
			self._reconcile_say_seed()
			return
		if key == 18:                      # Ctrl-R: next OLDER match
			nxt = None if state["match"] is None else state["match"] - 1
			if nxt is not None and nxt >= 0:
				found = self._reverse_match(state["query"], nxt)
				if found is not None:
					state["match"] = found
			# no wrap past the oldest match, deliberately: wrapping
			# hides that the search has run out
			return
		if key in (curses.KEY_RIGHT, 9):   # Right / Tab accept
			# Both leave search with the match in the ordinary buffer
			# and the caret at its end. W26 reserved this branch for
			# W27: once the match is adopted it IS an ordinary buffer,
			# so Tab adopts and then completes it in the same gesture —
			# which is what the ruling asks for, and why W26 stopped
			# here rather than calling a verb that did not exist.
			self._reverse_adopt()
			if key == 9:
				self._complete_command()
			return
		if key in (8, 127, curses.KEY_BACKSPACE):
			state["query"] = state["query"][:-1]
		elif 32 <= key <= 126:
			state["query"] += chr(key)
		else:
			return
		state["match"] = self._reverse_match(state["query"], None)

	def _command_key(self, key: int) -> None:
		# W36: the note describes what the LAST key did, so the next one
		# retires it — the same lifetime the status row has in
		# navigation.
		self.command_note = None
		if self.reverse is not None:
			self._reverse_key(key)
			return
		if key == 18 and self.history:      # Ctrl-R opens the search
			self.reverse = {"query": "", "draft": self.command,
			                "caret": self.command_caret,
			                "match": len(self.history) - 1}
			return
		if key in (curses.KEY_UP, curses.KEY_DOWN):
			self._history_step(older=key == curses.KEY_UP)
			return
		if key == 9:                        # Tab completes
			self._complete_command()
			return
		if key == ord(" ") and self.command == "filter" and \
				self.work_filter:
			# W5 R2: the first space after exact `filter` SEEDS the
			# buffer with the normalized current clauses — the
			# operator edits one clause without retyping the rest,
			# and Enter replaces atomically through the same parser.
			# Bare `filter` + Enter still clears.
			self._set_command("filter " + self._filter_clauses())
			return
		if key == ord(":") and self.command == "":
			# W19: `::` — a second colon on the EMPTY bar converts it
			# into the multiline batch buffer. The one-line `:`
			# interaction is otherwise untouched.
			self._set_command(None)
			self.batch = [self._batch_line("")]
			self.batch_cursor = 0
			self.batch_confirm = False
			self.batch_status = ""
			return
		if key in (10, 13, curses.KEY_ENTER):
			line = self.command
			self._set_command(None)
			self.seeded_say = None
			self.history_cursor = self.history_draft = None
			self.execute(line)
			return
		if key == 27:
			self._set_command(None)
			self.seeded_say = None
			self.history_cursor = self.history_draft = None
			return
		# W35 (ruled 2026-08-18, non-modal): movement and deletion at an
		# explicit caret. Printable `h`, `l`, `i` and `a` stay literal
		# command text — there is no hidden normal mode and no second
		# cursor grammar — and Esc keeps the visible meaning it already
		# had, which is why it is handled above rather than repurposed.
		# Ctrl-A/Ctrl-E are the readline spellings of Home/End and are
		# the terminal-proof ones: they are plain control bytes, where
		# Home/End arrive as escape sequences a terminal may spell two
		# ways (W25).
		if key == curses.KEY_LEFT:
			self.command_caret = max(0, self.command_caret - 1)
			return
		if key == curses.KEY_RIGHT:
			self.command_caret = min(len(self.command),
			                         self.command_caret + 1)
			return
		if key in (curses.KEY_HOME, 1):
			self.command_caret = 0
			return
		if key in (curses.KEY_END, 5):
			self.command_caret = len(self.command)
			return
		if key in (8, 127, curses.KEY_BACKSPACE):
			at = self.command_caret
			if at == 0:
				# nothing before the caret: deleting the last character
				# instead is exactly the append-only behaviour this Work
				# exists to remove
				return
			self._set_command(self.command[:at - 1] + self.command[at:],
			                  at - 1)
			self._reconcile_say_seed()
			return
		if key == curses.KEY_DC:
			at = self.command_caret
			if at >= len(self.command):
				return
			self._set_command(self.command[:at] + self.command[at + 1:], at)
			self._reconcile_say_seed()
			return
		if 32 <= key <= 126:
			self._command_type(chr(key))

	def _set_command(self, text: str | None, caret: int | None = None) -> None:
		"""THE assignment to the command buffer.

		W35: the caret is state that only means anything relative to a
		particular buffer, so nothing sets one without the other.
		`caret=None` means the end, which is what every whole-buffer
		replacement wants — a recalled entry, an adopted search match, a
		seeded draft — because the operator's next keystroke continues
		the line before it edits inside it."""
		self.command = text
		if text is None:
			self.command_caret = 0
		else:
			self.command_caret = len(text) if caret is None \
				else max(0, min(caret, len(text)))

	def _command_type(self, character: str) -> None:
		"""One printable character into the bar AT THE CARET, through
		the one path that owns the buffer's side effects."""
		at = self.command_caret
		self._set_command(self.command[:at] + character
		                  + self.command[at:], at + 1)
		self._reconcile_say_seed()

	def _complete_command(self) -> None:
		"""W27: Tab turns the existing analysis into conservative
		editing.

		The completion is applied by TYPING the remaining characters
		rather than assigning the finished buffer, and that is the whole
		trick. Two command-bar behaviours are triggered by reaching an
		exact verb, not by parsing a submitted line — `say` seeds the
		selected `thread=`, and the first space after `filter` seeds the
		editable current clauses. Assigning `say ` wholesale would
		produce an unseeded buffer that ordinary typing could never
		reach, so completion goes through the same keys the operator
		would have pressed.

		A transition that rewrites the buffer ends the feed: its result
		is the authoritative buffer, and appending the rest of a
		completion on top of it would duplicate what the transition
		already supplied.

		No candidate, no progress, an open quote or a diagnostic all
		leave the buffer untouched — the assist line is already the
		candidate display, and a repeated Tab never chooses for the
		operator."""
		if self.command is None:
			return
		if self.command_caret != len(self.command):
			# W35: `complete_partial` analyses the buffer's LAST token,
			# which is not the token an interior caret is in. Typing
			# its result at the caret would splice characters into a
			# place the operator is not looking and rewrite a different
			# operand — so Tab declines instead, exactly as it already
			# declines an ambiguous candidate or an open quote. A
			# repeated Tab never chooses for the operator, and that
			# includes never choosing WHERE.
			return
		result = _cli.complete_partial(self.command)
		if not result["progressed"]:
			return
		completed = result["buffer"]
		if not completed.startswith(self.command):
			# completion only ever extends the live token; anything else
			# would be a rewrite this must not perform
			return
		for character in completed[len(self.command):]:
			expected = self.command + character
			if character == " ":
				# the space that seeds `filter` is a real key, and it is
				# handled where that transition lives
				self._command_key(ord(" "))
			else:
				self._command_type(character)
			if self.command != expected:
				# a seed or other transition owns the buffer now
				return

	# -- interaction ----------------------------------------------------------

	def handle(self, key: int) -> bool:
		"""One key. Returns False to exit."""
		if self.command is not None:
			self._command_key(key)
			return True
		if self.batch is not None:
			# W19: every key belongs to the batch buffer while it is
			# open — q and : stay literal text, exactly like the bar.
			return self._batch_key(key)
		if self.search_input is not None:
			self._search_entry_key(key)
			return True
		# W9 (ruled): in normal navigation q opens ONE bottom-row
		# Exit? y/N prompt. y/Y exits; n/N/Esc cancels to the UNCHANGED
		# view — including any visible status, so this whole branch
		# runs BEFORE the per-key status reset; every other key neither
		# confirms nor cancels. Nothing here touches the authority or
		# seen state — pure view state. Text entry in the command bar
		# keeps q literal (handled above, before this branch).
		if self.confirm_exit:
			if key in (ord("y"), ord("Y")):
				return False
			if key in (ord("n"), ord("N"), 27):
				self.confirm_exit = False
			return True
		# W17: the state chooser is modal for the same reason the exit
		# prompt is — it owns the bottom row and the next key answers
		# it. It sits above `q` so a state key cannot double as an exit
		# and an exit cannot double as an answer.
		if self.poke_choice is not None:
			self.status = ""
			return self._poke_choice_key(key)
		if key == ord("q"):
			self.confirm_exit = True
			return True
		self.status = ""
		if key == ord(":"):
			# W26: one scratch draft per opening, positioned AFTER the
			# newest entry — the first Up recalls the newest submission.
			self._set_command("")
			self.history_cursor = None
			self.history_draft = None
			self.reverse = None
			return True
		# W110 (finding-consistent-tui-tab-grammar) supersedes W25's
		# reasoning here. W25 kept `[`/`]` away from the top level
		# because Work detail already used them for Messages/Events —
		# but the keys perform the SAME operation at two levels, and
		# "previous/next tab at the level you are in" is one rule, not
		# two. What an operator would otherwise learn twice is which
		# gesture each level wants.
		#
		# The guard is the whole of the context separation: inside Work
		# detail this branch declines and `_handle_detail` takes the
		# keys, so `]` there never escapes to the top level. Text entry
		# — the command bar, the batch buffer, the search input — has
		# already claimed every key above, so `[` and `]` stay literal
		# where somebody is typing them.
		#
		# W1151 (finding-immediate-pane-focus-navigation) retires the
		# `Tab`/`Shift-Tab` aliases W110 kept here. `[` and `]` are the
		# EXCLUSIVE tab-switching keys now, because Tab has a better
		# job: cycling pane focus for operators who do not reach for
		# Vim window commands. One key cannot mean "next tab" and "next
		# pane" without meaning neither.
		# W292 generalizes the guard from "not in Work detail" to "not
		# drilled in at all". `[`/`]` move among the tabs at the CURRENT
		# level, and the global tabs are only the current level at the
		# top — so inside any drilled page these keys belong to that
		# page and can never move the operator to Teams or Inbox behind
		# their back. A drilled page with no local tabs simply ignores
		# them.
		#
		# BOTH conditions, deliberately. `nav` is the recorded path and
		# is what the breadcrumb paints; the mode is what the operator
		# is actually looking at. A view constructed straight into a
		# detail mode has no recorded path, and its brackets must still
		# not reach the global row.
		if key in (ord("["), ord("]")) \
				and not self.location and self.mode == "table" \
				and not self.context_work():
			step = -1 if key == ord("[") else 1
			self.tab = TABS[(TABS.index(self.tab) + step) % len(TABS)]
			return True
		if self.tab == "inbox":
			return self._handle_inbox(key)
		if self.tab == "teams":
			return self._handle_teams(key)
		# W26331: every breadcrumb-bearing single-body page has a
		# two-stop region cycle. Work detail owns its larger cycle below.
		if self.location and self.mode != "detail":
			if self.crumb_focus:
				if key in (9, curses.KEY_BTAB):
					self._leave_breadcrumb()
					return True
				if self._handle_breadcrumb_key(key):
					return True
			elif key in (9, curses.KEY_BTAB):
				self._enter_breadcrumb()
				return True
		if key == ord("/") and self.mode in ("table", "search"):
			# W6: open (or replace) the search query bar.
			self.search_input = ""
			return True
		if self.mode == "search":
			return self._search_mode_key(key)
		if self.mode == "pokes":
			return self._handle_pokes(key)
		if self.mode == "mine":
			return self._handle_mine(key)
		rows, _hidden = (self.table_rows()
		                 if self.mode == "table" else ([], 0))

		if self.mode == "links":
			return self._handle_graph(key)
		if self.mode == "detail":
			return self._handle_detail(key)
		# -- the Work tree ------------------------------------------------
		if key in (curses.KEY_DOWN, ord("j")):
			self.cursor = min(self.cursor + 1, max(0, len(rows) - 1))
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_UP, ord("k")) and self.cursor == 0 \
				and self.location:
			self._enter_breadcrumb()
		elif key in (curses.KEY_UP, ord("k")):
			self.cursor = max(0, self.cursor - 1)
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (ord("["), ord("]")) and self.context_work():
			# W6814: inside a contextual Work page the bracket keys move
			# among ITS tabs. The global guard above already declined
			# them, which is the whole separation: `]` never escapes a
			# drilled page to reach Teams.
			self._switch_tab(1 if key == ord("]") else -1)
		elif key in (curses.KEY_ENTER, 10, 13) and rows:
			# W6814 supersedes W71's single meaning: activation opens
			# what the row HAS — a subtree, or the Job's own detail.
			self._activate(rows[self.cursor])
		elif key == ord("u") and rows:
			# W71/W155/W6814: the EXPLICIT unfold. Activation covers the
			# ordinary case; this is what roots at a Job with no children
			# and what an operator with the key in their hands still
			# expects. Re-rooting at the current root is idempotent: one
			# logical unfold, one Back (R2).
			self._open_root(rows[self.cursor]["id"])
		elif key == ord("d") and rows:
			# W292: the dependency page is a drill into the chosen Work,
			# so it is a breadcrumb segment like any other.
			#
			# W96: `d` for deps, and `b` is gone rather than aliased.
			self._open_graph(rows[self.cursor]["id"])
		elif key == ord("c") and rows:
			self._claim_selected(rows)
		elif key == ord("p"):
			# W17: the poke view opens with no Work selected and none
			# needed — a poke is addressed to a participant, not to
			# Work, so it is reachable from an empty table too.
			self._open_pokes()
		elif key == ord("m"):
			# W26328: `m` for mine. Like `p`, it needs no selected row
			# and opens from an empty table — the whole point is the
			# Work this window is NOT showing.
			self._open_mine()
		elif key == ord("z"):
			self.show_closed = not self.show_closed
			shown, _hidden = self.table_rows()
			self.cursor = min(self.cursor, max(0, len(shown) - 1))
			self.selected_id = shown[self.cursor]["id"] if shown \
				else None
		elif key in (27, curses.KEY_LEFT) and self.nav:
			# W292: one segment per Back, and the revealed level comes
			# back as it was.
			self._nav_pop()
		return True

	def _handle_detail(self, key: int) -> bool:
		"""The detail view's keys. Ctrl-W (23) is the region-navigation
		prefix (ruled, the Vim split convention).

		W76: the three regions are GEOMETRIC, not a linear tuple. The
		Threads list sits above both Message panes, and the index and
		reader sit beside each other (stacked when narrow, but with the
		same logical neighbours). So one upward move from the READER
		reaches Threads directly — the Message index is not a mandatory
		intermediate stop, which is what made the panes feel like a list
		rather than three panels. Unmapped edge directions stay put; a
		second Ctrl-W (or `w`) keeps the deterministic three-pane
		cycle."""
		regions = ("threads", "index", "reader")
		# direction -> {from: to}. Absent entries are edges: stay.
		neighbours = {
			"up": {"index": "threads", "reader": "threads"},
			"down": {"threads": "index", "index": "reader"},
			"left": {"reader": "index"},
			"right": {"index": "reader"},
		}
		if self.crumb_focus:
			if self.ctrl_w_pending:
				self.ctrl_w_pending = False
				if key in (ord("j"), curses.KEY_DOWN, ord("w"), 23):
					self.crumb_return_focus = "index" \
						if self.detail_tab == "events" else "threads"
					self._leave_breadcrumb()
				return True
			if key == 23:
				self.ctrl_w_pending = True
				return True
			if key in (9, curses.KEY_BTAB):
				if self.detail_tab == "events":
					self.crumb_return_focus = "reader" \
						if key == curses.KEY_BTAB else "index"
				else:
					self.crumb_return_focus = "reader" \
						if key == curses.KEY_BTAB else "threads"
				self._leave_breadcrumb()
				return True
			if self._handle_breadcrumb_key(key):
				return True
		# W1151: the discoverable alternative to the Vim chord. Tab
		# cycles the VISIBLE regions forward and Shift-Tab backward,
		# wrapping, over exactly the panes this tab paints — three in
		# Messages, two in Events. It is a view move like the chord it
		# sits beside: read-only, no selection, no seen state, no
		# authority read.
		if key in (9, curses.KEY_BTAB):
			# W1151 review: a pane gesture CONSUMES a pending chord.
			# The two are alternatives, so using one cannot leave the
			# other half-entered — otherwise `Ctrl-W`, Tab, `j` makes
			# that later `j` finish the OLD chord instead of acting in
			# the pane Tab just selected. Vim answers `Ctrl-W Tab` by
			# cycling, which is what this does either way.
			self.ctrl_w_pending = False
			step = -1 if key == curses.KEY_BTAB else 1
			if self.detail_tab == "events":
				order = ("breadcrumb", "index", "reader")
				here = self.event_focus if self.event_focus in order \
					else "index"
				target = order[(order.index(here) + step) % len(order)]
				if target == "breadcrumb":
					self._enter_breadcrumb(here)
				else:
					self.event_focus = target
			else:
				order = ("breadcrumb",) + regions
				here = self.focus if self.focus in order else "index"
				target = order[(order.index(here) + step) % len(order)]
				if target == "breadcrumb":
					self._enter_breadcrumb(here)
				else:
					self.focus = target
			return True
		if self.ctrl_w_pending:
			self.ctrl_w_pending = False
			# W123: Ctrl-W stays PANE-LOCAL to the active tab. Events
			# has two panes; the map degenerates to the index/reader
			# pair without a Threads list above them.
			if self.detail_tab == "events":
				if key in (ord("j"), curses.KEY_DOWN, ord("l"),
				           curses.KEY_RIGHT):
					self.event_focus = "reader"
				elif key in (ord("k"), curses.KEY_UP) \
						and self.event_focus == "index":
					self._enter_breadcrumb("index")
				elif key in (ord("k"), curses.KEY_UP, ord("h"),
				             curses.KEY_LEFT):
					self.event_focus = "index"
				elif key in (ord("w"), 23):
					self.event_focus = "reader" \
						if self.event_focus == "index" else "index"
				return True
			here = self.focus if self.focus in regions else "index"
			if key in (ord("k"), curses.KEY_UP):
				direction = "up"
			elif key in (ord("j"), curses.KEY_DOWN):
				direction = "down"
			elif key in (ord("h"), curses.KEY_LEFT):
				direction = "left"
			elif key in (ord("l"), curses.KEY_RIGHT):
				direction = "right"
			elif key in (ord("w"), 23):
				self.focus = regions[(regions.index(here) + 1)
				                     % len(regions)]
				return True
			else:
				return True
			if direction == "up" and here == "threads":
				self._enter_breadcrumb("threads")
			else:
				self.focus = neighbours[direction].get(here, here)
			return True
		if key == 23:
			self.ctrl_w_pending = True
			return True
		# W123: tab switching works from ANYWHERE in Work detail, not
		# only from a particular pane — it is a view-level move, not a
		# pane-level one.
		if key == ord("]"):
			self._switch_tab(1)
			return True
		if key == ord("["):
			self._switch_tab(-1)
			return True
		if key in (27, curses.KEY_LEFT):
			# W292: Back pops exactly ONE breadcrumb segment. Inside a
			# nested Work that is the parent Work scope, not the caller
			# — the trail names those scopes, so a Back that skipped
			# them would be describing a path nobody can walk. The last
			# pop restores the view that opened the drill, which is
			# what W6's search restoration always promised.
			if self._nav_pop():
				return True
			self.mode = self.detail_return
			self.detail_return = "table"
			return True
		if self.detail_tab == "events":
			return self._handle_events_keys(key)
		if self.focus == "threads":
			rows = self.thread_rows()
			if self.disc_cursor is None:
				self._thread_autoselect()
			if key in (curses.KEY_DOWN, ord("j")):
				if self.disc_cursor + 1 < len(rows):
					self.disc_cursor += 1
				elif self.disc_next is not None:
					self.disc_after = self.disc_next
					self.disc_cursor = 0
				self._reset_message_selection()
			elif key in (curses.KEY_UP, ord("k")) \
					and (self.disc_cursor or 0) == 0:
				self._enter_breadcrumb("threads")
			elif key in (curses.KEY_UP, ord("k")):
				if self.disc_cursor > 0:
					self.disc_cursor -= 1
				self._reset_message_selection()
			elif key == ord("n") and self.disc_next is not None:
				self.disc_after = self.disc_next
				self.disc_cursor = 0
				self._reset_message_selection()
			elif key == ord("p"):
				self.disc_after = 0
				self.disc_cursor = 0
				self._reset_message_selection()
			elif key == ord("s"):
				self._mark_selected_seen()
			return True
		if self.focus == "reader":
			# -- the reader: scroll the ONE selected block ---------------
			if key in (curses.KEY_DOWN, ord("j")):
				if self.reader_clipped:
					self.reader_skip += 1
			elif key in (curses.KEY_UP, ord("k")):
				self.reader_skip = max(0, self.reader_skip - 1)
			elif key == ord("p"):
				self.reader_skip = 0
			elif key == ord("s"):
				self._mark_selected_seen()
			return True
		# -- the Message index (also any legacy focus spelling) ------------
		# W76: the index reads NEWEST-FIRST, so screen-down selects an
		# OLDER Message — one step back along the canonical ascending
		# page — and screen-up selects a newer one. Paging follows the
		# same direction: `n` reaches the older page, `p` returns to the
		# newest one (never a previous-page step).
		if key in (curses.KEY_DOWN, ord("j")):
			if self.msg_cursor in self.viewed_seqs:
				here = self.viewed_seqs.index(self.msg_cursor)
				if here > 0:
					self.msg_cursor = self.viewed_seqs[here - 1]
					self.reader_skip = 0
				elif self.viewed_next_before is not None:
					self.thread_before = self.viewed_next_before
					self._reset_message_selection(keep_thread=True)
		elif key in (curses.KEY_UP, ord("k")):
			if self.msg_cursor in self.viewed_seqs:
				here = self.viewed_seqs.index(self.msg_cursor)
				if here + 1 < len(self.viewed_seqs):
					self.msg_cursor = self.viewed_seqs[here + 1]
					self.reader_skip = 0
		elif key == ord("n"):
			if self.viewed_next_before is not None:
				self.thread_before = self.viewed_next_before
				self._reset_message_selection(keep_thread=True)
		elif key == ord("p"):
			self.thread_before = None
			self._reset_message_selection(keep_thread=True)
		elif key == ord("s"):
			self._mark_selected_seen()
		return True

	def _handle_events_keys(self, key: int) -> bool:
		"""The Events tab's own keys, mirroring Messages so the two
		tabs behave alike: j/k select (newest-first, so down is older),
		n reaches the older page, p returns to the newest, and in the
		reader j/k scroll one long event. Nothing here writes: Events
		is a read of the immutable journal, and there is no seen cursor
		to advance."""
		if self.event_focus == "reader":
			if key in (curses.KEY_DOWN, ord("j")):
				if getattr(self, "event_clipped", False):
					self.event_skip += 1
			elif key in (curses.KEY_UP, ord("k")):
				self.event_skip = max(0, self.event_skip - 1)
			elif key == ord("p"):
				self.event_skip = 0
			return True
		if key in (curses.KEY_DOWN, ord("j")):
			if self.event_cursor in self.viewed_event_seqs:
				here = self.viewed_event_seqs.index(self.event_cursor)
				if here > 0:
					self.event_cursor = self.viewed_event_seqs[here - 1]
					self.event_skip = 0
				elif self.viewed_events_next_before is not None:
					self.event_before = self.viewed_events_next_before
					self.event_cursor = None
					self.event_skip = 0
		elif key in (curses.KEY_UP, ord("k")) \
				and (not self.viewed_event_seqs or
				     self.event_cursor == self.viewed_event_seqs[-1]):
			self._enter_breadcrumb("index")
		elif key in (curses.KEY_UP, ord("k")):
			if self.event_cursor in self.viewed_event_seqs:
				here = self.viewed_event_seqs.index(self.event_cursor)
				if here + 1 < len(self.viewed_event_seqs):
					self.event_cursor = self.viewed_event_seqs[here + 1]
					self.event_skip = 0
		elif key == ord("n"):
			if self.viewed_events_next_before is not None:
				self.event_before = self.viewed_events_next_before
				self.event_cursor = None
				self.event_skip = 0
		elif key == ord("p"):
			self.event_before = None
			self.event_cursor = None
			self.event_skip = 0
		return True

	def _enter_detail(self, work_id: str, *, came_from: str) -> None:
		"""Open Work detail FRESH on one Work — the one place the three
		entry paths (Jobs, search, Inbox) agree about what a fresh entry
		means.

		W2597 (finding-default-message-pane-focus): focus lands in the
		MESSAGE INDEX, not the Threads pane. Most Work has one thread,
		which the autoselect below picks anyway, so opening in Threads
		charged every operator a `Tab` before they could move through
		the Messages they came to read.

		The Threads pane keeps its job and its selection: the visible
		thread still decides which Messages are shown, `Shift-Tab` and
		`Ctrl-W k` still reach it, and the autoselect rule is untouched.
		Only where the cursor STARTS changed.

		Nothing here reads the authority or writes it. The thread and
		Message selections are both deferred — `disc_cursor=None` lets
		the New-first thread rule run at render, and
		`_reset_message_selection` lets the newest-first Message rule
		run — so entry cannot mark anything seen or invent a Message
		that does not exist.

		W2597 R1: a fresh entry also clears the view state that belonged
		to the WORK BEFORE IT. `detail_tab` and the Events tab's cursor,
		page and pane focus all survived `Esc`, so opening Work A,
		switching to Events, leaving, and opening Work B put B on the
		Events tab — against the ruling and the documentation — showing
		A's event page. Per-tab state is preserved for a tab ROUND TRIP
		inside one open detail view, which is `_switch_tab`'s job and is
		it was never meant to follow the operator to a different Work.

		W292 recorded the navigation path here, one frame per Work in
		the canonical ancestry. W6814 SUPERSEDES that: entry records
		exactly ONE history entry, because the operator performed one
		navigation. The breadcrumb still names the whole containment
		ancestry — it is derived structurally now (`nav_segments`) rather
		than assembled from Back steps — so nothing is lost from the
		trail and two intermediate Works the operator never opened no
		longer become two Backs they have to spend."""
		self._nav_push("work", self._work_title(work_id), work=work_id)
		self._nav_restore(self._fresh_detail_state(work_id))
		self.detail_return = came_from

	def _work_ids(self, work_id: str) -> list[str]:
		"""The re-rooted window's path: the ancestry as Work ids."""
		return [entry["id"] for entry in self._work_ancestry(work_id)]

	def _rooted_state(self, work_id: str) -> dict:
		"""What a FRESH contextual Work page looks like on its `Jobs`
		tab: the Work as the tree root, the cursor at the top, and the
		Messages/Events tabs already aimed at that same Work so `]`
		reaches them without a second decision about which Work they
		belong to."""
		state = self._fresh_detail_state(work_id)
		state.update({"mode": "table", "path": self._work_ids(work_id),
		              "cursor": 0, "selected_id": None})
		return state

	def _fresh_detail_state(self, work_id: str) -> dict:
		"""What a FRESH Work-detail entry looks like — the one
		definition, so a synthesized ancestor frame and a real entry
		cannot drift apart."""
		return {"mode": "detail", "detail_work": work_id,
		        "detail_tab": "messages", "disc_cursor": None,
		        "disc_after": 0, "focus": DETAIL_ENTRY_FOCUS,
		        "thread_before": None, "msg_cursor": None,
		        "reader_skip": 0, "event_cursor": None,
		        "event_before": None, "event_focus": "index",
		        "event_skip": 0}

	def _reset_message_selection(self, keep_thread: bool = False) -> None:
		"""Moving to another Thread (or another page) drops the message
		selection so the newest-first default reapplies; the reader
		restarts at the top. W76 retired the `seek` flag with the
		forward walk it armed: entry is now one bounded newest-page
		read, so there is no thread-wide hunt for a page command to
		override."""
		if not keep_thread:
			self.thread_before = None
		self.msg_cursor = None
		self.reader_skip = 0

	def _mark_selected_seen(self) -> None:
		"""The EXPLICIT seen transition — the one writer, by ruling —
		scoped to the DISPLAYED thread and bounded by the chosen
		Message: the cursor advances through it and through NO later
		Message (W14); an already-seen no-op schedules nothing (R7)."""
		if self.viewed_thread is None or self.msg_cursor is None:
			return
		result = transitions.seen_thread(
			self.store, self.viewed_thread, team=self.team,
			member=self.member, up_to_seq=self.msg_cursor)
		if result["advanced"]:
			self.schedule_refresh()
		self.status = (f"seen through M{result['cursor']}"
		               if result["advanced"] else "already seen")


# W36 (finding-editor-backed-command-text): authoring durable prose in
# the one-row `:` bar means quoting paragraphs into a single line, which
# is exactly what an external editor is for. The two functions below are
# the whole client-local contract, kept PURE and module level so the
# byte-preservation rules can be asserted without a terminal, an editor,
# or a store.
PROSE_COMMENT = "#"


def prose_template(verb: str, key: str, context) -> str:
	"""The Git-commit-style document an operator opens.

	It is never an unexplained empty file: it names the operation and
	the field being authored, whatever Work or Thread context supplies,
	and how to save and cancel — including the one rule a reader
	otherwise has to guess, which is WHICH `#` lines disappear."""
	lines = [f"{PROSE_COMMENT} Baton {verb} — authoring {key}="]
	for note in context:
		lines.append(f"{PROSE_COMMENT} {note}")
	lines += [
		PROSE_COMMENT,
		f"{PROSE_COMMENT} Everything below the blank line becomes the "
		f"value of {key}=.",
		f"{PROSE_COMMENT} These leading '{PROSE_COMMENT}' lines are "
		f"removed; a '{PROSE_COMMENT}' line further down is kept.",
		f"{PROSE_COMMENT} Save and exit to run the command. Exit "
		f"leaving this empty to cancel;",
		f"{PROSE_COMMENT} the command draft stays intact either way.",
	]
	return "\n".join(lines) + "\n\n"


def strip_prose_template(text: str) -> str:
	"""The authored value, and NOTHING Baton wrote.

	The rule is the leading contiguous run of comment lines, plus one
	blank separator if it survived, plus one trailing newline. It is
	deliberately positional rather than a match against the block that
	was generated: a rule that only removed lines it still recognised
	would leak instructional text the moment an operator edited one of
	them, and `instructional text can never leak into the submitted
	body` is the acceptance boundary that outranks every other
	consideration here.

	The cost is stated in the template itself — a `#` line the operator
	puts at the very TOP goes with the block. Anywhere else it is
	content, which is the ruling's own distinction.

	Everything after that is preserved byte for byte: quotes, blank
	lines inside the body, Unicode, and comment characters."""
	lines = text.split("\n")
	index = 0
	while index < len(lines) and \
			lines[index].lstrip().startswith(PROSE_COMMENT):
		index += 1
	if index < len(lines) and lines[index] == "":
		index += 1
	body = "\n".join(lines[index:])
	# Editors append a final newline; one is the terminator, not content.
	return body[:-1] if body.endswith("\n") else body


# W35 (finding-command-buffer-cursor-editing): the caret is an index
# into the buffer's CHARACTERS, but a terminal draws CELLS, so the two
# have to be converted wherever they meet or a wide character silently
# puts the visible caret somewhere the next keystroke will not land.
#
# These are the same wcwidth rules `authority.cell_width` applies to a
# canonical handle. They are not that function: it answers a VALIDATION
# question and returns -1 to refuse a control character, while rendering
# has to produce a number for whatever is in the buffer. One of those
# contracts cannot serve the other, so the rules are shared and the
# answers are not.
def _cell_width(character: str) -> int:
	if unicodedata.combining(character) or \
			unicodedata.category(character) in ("Mn", "Me", "Cf"):
		return 0
	return 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1


def _cells(text: str) -> int:
	return sum(_cell_width(character) for character in text)


def command_window(typed: str, caret: int, avail: int) -> tuple[str, int]:
	"""The visible slice of the one-line `:` bar and the screen COLUMN
	its caret lands on.

	A PURE function of the buffer, the caret and the width — there is no
	remembered scroll offset — so the same three inputs always produce
	the same window, a narrow terminal is testable without a terminal,
	and a resize cannot leave the caret stranded off screen: the next
	render simply recomputes it.

	`<` and `>` name text scrolled off each side and cost a cell each,
	so a marker never covers the character it stands in for. One further
	cell is always left free to the right of the caret when the line
	scrolls: the caret sits AFTER the last visible character, where the
	next typed one will land, and parking it in the terminal's final
	column is the one place curses and auto-wrap disagree about what
	happens next."""
	if avail <= 0:
		return "", 0
	if _cells(typed) < avail:
		return typed, _cells(typed[:caret])
	# The caret is still inside the first screenful: stay anchored at the
	# start — scrolling a buffer whose beginning the operator is editing
	# would move text for no reason — and name the hidden tail.
	end, used = 0, 0
	while end < len(typed) and used + _cell_width(typed[end]) <= avail - 1:
		used += _cell_width(typed[end])
		end += 1
	if caret <= end:
		return typed[:end] + ">", _cells(typed[:caret])
	# Otherwise the caret anchors the RIGHT edge: `<` names the hidden
	# head, as much preceding context as fits follows, and any room left
	# over shows what comes after the caret.
	# Reserve before measuring: `<` always, one cell for the caret
	# itself, and `>` too when text remains after it. Taking those cells
	# afterwards is what a first cut did, and the `>` then landed
	# exactly on the caret's own column — a marker covering the very
	# character it was standing in for, which is the one thing the
	# markers must not do.
	reserved = 2 if caret >= len(typed) else 3
	start, used = caret, 0
	while start > 0 and \
			used + _cell_width(typed[start - 1]) <= avail - reserved:
		used += _cell_width(typed[start - 1])
		start -= 1
	text = "<" + typed[start:caret]
	column = 1 + used
	room = avail - column
	tail = caret
	while tail < len(typed) and _cell_width(typed[tail]) <= room - 1:
		room -= _cell_width(typed[tail])
		tail += 1
	text += typed[caret:tail]
	if tail < len(typed):
		text += ">"
	return text, column


# W25: the normal-mode (DECCKM off) cursor spellings, which `smkx` asks
# terminals not to use and some send anyway. The application-mode forms
# (`ESC O A`…) are already translated by keypad, and `ESC [ A`… are what
# reaches the loop as a bare escape.
ESCAPE_PEEK_MS = 25
_CURSOR_FINALS = {ord("A"): curses.KEY_UP, ord("B"): curses.KEY_DOWN,
                  ord("C"): curses.KEY_RIGHT, ord("D"): curses.KEY_LEFT,
                  # W35: Home and End carry EXACTLY the skew W25
                  # measured — `ESC O H`/`ESC O F` in application mode,
                  # `ESC [ H`/`ESC [ F` in normal mode. Shipping the
                  # ruled contract without them would leave two of its
                  # keys reachable from one kind of terminal and
                  # invisible from the other, which is the defect W25
                  # exists to have found once.
                  ord("H"): curses.KEY_HOME, ord("F"): curses.KEY_END}
# W35: the tilde-terminated spellings. Delete has no control-byte
# alternate the way Home and End have Ctrl-A and Ctrl-E, so `ESC [ 3 ~`
# is the only way it arrives from a terminal whose terminfo the running
# ncurses did not match.
_TILDE_FINALS = {ord("1"): curses.KEY_HOME, ord("3"): curses.KEY_DC,
                 ord("4"): curses.KEY_END, ord("7"): curses.KEY_HOME,
                 ord("8"): curses.KEY_END}


def _decode_normal_mode_cursor(screen) -> int:
	"""Translate `ESC [ A/B/C/D` (and the `ESC O` variant) into the
	cursor constants, or return 27 for a genuine bare Esc.

	Anything that is not a cursor sequence is pushed back, so an escape
	introducing some other sequence is not silently eaten — the reader
	sees exactly what it would have seen before."""
	screen.timeout(ESCAPE_PEEK_MS)
	introducer = screen.getch()
	if introducer == -1:
		return 27
	if introducer not in (ord("["), ord("O")):
		curses.ungetch(introducer)
		return 27
	final = screen.getch()
	if final in _CURSOR_FINALS:
		return _CURSOR_FINALS[final]
	if final in _TILDE_FINALS:
		# One more byte, and only for a sequence that genuinely takes
		# one: anything that is not the terminator is pushed back with
		# everything before it, so a `ESC [ 3` introducing something
		# else is still handed on exactly as it was.
		terminator = screen.getch()
		if terminator == ord("~"):
			return _TILDE_FINALS[final]
		if terminator != -1:
			curses.ungetch(terminator)
	if final != -1:
		curses.ungetch(final)
	curses.ungetch(introducer)
	return 27


def _absorb_paired_linefeed(screen) -> None:
	"""Swallow the `LF` that completes a `CR LF` Return.

	W1568: a terminal in NEW LINE mode (LNM) transmits `CR LF` for ONE
	Return. Under ncurses' default `nl()` the `CR` is translated to `LF`
	before the console reads it, so the pair arrives as two identical
	Enter keys — byte-identical to two deliberate Returns, and no
	handler can tell them apart. `run()` selects `nonl()` so the `CR`
	survives, and this collapses the pair back into the one keystroke
	the operator made.

	It is a DECODE, not a debounce: only an `LF` arriving directly
	behind a `CR` is absorbed. Two deliberate Returns arrive as `13 13`,
	the peek sees a `13`, pushes it back, and both are delivered —
	nothing is suppressed on the basis of how recently anything ran.
	Anything else that follows is pushed back untouched, exactly as
	`_decode_normal_mode_cursor` pushes back a non-cursor escape."""
	screen.timeout(ESCAPE_PEEK_MS)
	following = screen.getch()
	if following not in (-1, 10):
		curses.ungetch(following)


def _read_key(screen) -> int:
	"""One LOGICAL keystroke, or -1 when the read expired.

	The whole terminal-spelling boundary lives here, so what the console
	handles is what the operator DID rather than which bytes their
	terminal chose to say it with. Both corrections it applies were
	invisible to tests that call `Console.handle` with an already-decoded
	key, which is why they shipped: W25's normal-mode cursor sequences,
	and W1568's `CR LF` Return."""
	key = screen.getch()
	if key == 27:
		return _decode_normal_mode_cursor(screen)
	if key == 13:
		_absorb_paired_linefeed(screen)
	return key


def run(screen, store: Authority, viewer_team: str, viewer_member: str,
        config_path: str | None = None, refresh: float = 2.0,
        work_filter: dict | None = None) -> None:
	"""W5: `refresh` seconds (default 2, positive, configurable via
	`tui refresh=`) is the ONE background trigger for fresh canonical
	reads — getch times out, the cache drops, the screen repaints.
	Ordinary keystrokes operate on the cached projection."""
	import time
	curses.curs_set(0)
	# W1568: `nonl()` keeps `CR` and `LF` distinct at the reader. The
	# default `nl()` sets the tty's ICRNL, which folds the `CR LF` a
	# NEW LINE mode terminal sends for one Return into two identical
	# Enter keys — the second of them landing in Jobs navigation and
	# opening Work detail nobody asked for. Every Enter branch in the
	# console already accepts 10, 13 and `KEY_ENTER`, so keeping the
	# `CR` costs no handler a change; `_absorb_paired_linefeed` below
	# collapses the pair.
	curses.nonl()
	# W25: keypad translation is already on — `curses.wrapper` calls
	# `keypad(1)` before this function runs — so the cursor keys are
	# decoded, but only in ONE of the two spellings a terminal may send.
	#
	# `keypad(1)` emits `smkx`, which asks the terminal for APPLICATION
	# cursor mode, and xterm's terminfo then expects `ESC O B` for Down.
	# A terminal that stays in NORMAL cursor mode sends `ESC [ B`
	# instead — and ncurses, having asked for the other mode, hands that
	# through as a bare 27 followed by two ordinary characters. The
	# aliases in the handlers were therefore reachable from one kind of
	# terminal and invisible from the other, which is why vi keys kept
	# working and the tests, injecting `curses.KEY_*` directly, could
	# not see the gap at all. `curses.define_key` would be the tidy fix
	# but is absent from this build, so the normal-mode forms are
	# decoded here.
	#
	# The peek costs nothing when a bare Esc is pressed: nothing
	# follows, the short read expires, and 27 is returned unchanged.
	if not os.environ.get("ESCDELAY"):
		curses.set_escdelay(ESCAPE_PEEK_MS)
	console = Console(store, viewer_team, viewer_member,
	                  config_path=config_path, work_filter=work_filter)
	console.render(screen)
	# R1: the refresh is WALL-CLOCK driven — a monotonic deadline that
	# input can neither postpone nor accelerate. Keys before the
	# deadline serve from the cache; reaching the deadline refreshes
	# even while input keeps arriving.
	deadline = time.monotonic() + refresh
	while True:
		remaining = deadline - time.monotonic()
		if remaining <= 0:
			console.tick()
			console.render(screen)
			deadline = time.monotonic() + refresh
			continue
		screen.timeout(max(1, int(remaining * 1000)))
		key = _read_key(screen)
		if key == -1:
			continue
		if not console.handle(key):
			return
		console.render(screen)


# SUPERSEDED (C3): the module-level entry that opened a raw authority path is
# gone. The ONLY launch is `baton --config ... --participant ... tui`,
# which opens through the bound lifecycle and validates the participant
# before curses claims the screen — the v10 console's refuse-first lesson,
# now enforced by the configuration boundary rather than by this module.
