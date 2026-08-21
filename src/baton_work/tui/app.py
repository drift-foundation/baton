"""Curses rendering of the canonical projection — B1.

THE PINNED MODEL, exactly: open on a borderless fixed-column table showing
three containment levels — the viewer's top-level Work, its children, and
theirs (W155, superseding W71's two-level cap). `u` re-roots the window at the
selected Work and a persistent breadcrumb names that path; Enter opens the
focused Work's detail rather than drilling a level; `o` opens the focused Work view (facts, trials, and the selectable
thread set); Enter there opens one thread's paged thread — never
several merged into a false timeline. `b` shows blocking/dependent neighbors
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


def _fit(value: str, size: int) -> str:
	"""One value in one column, abbreviated VISIBLY when it cannot fit.

	W137: an identifier that is silently cut reads as a different,
	shorter identifier. The ellipsis is what makes a prefix say it is a
	prefix."""
	if len(value) <= size:
		return value.ljust(size)
	return (value[:size - 1] + "…") if size > 1 else value[:size]


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
	         f"{message['author']} {message.get('ts', '')}{marker}"]
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
		self.cursor = 0
		self.mode = "table"       # table / links / thread / thread
		self.status = ""
		# Resolved branches are COLLAPSED by default (ruled): closed rows
		# leave the table, an explicit count names what is hidden, and a
		# key reveals them — nothing is ever silently absent.
		self.show_closed = False
		self.links_work: str | None = None
		self.links_cursor = 0
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


	def view(self) -> tuple[list[dict], dict]:
		"""(tree rows, summary) — W155 (superseding W71's two-level
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
		window = self._cached(("tree", root_id, filter_key),
		                      lambda: projection.tree(
			self.store, root_id, viewer_team=self.team,
			viewer_member=self.member,
			work_filter=self.work_filter))
		return list(window["rows"]), window["summary"]

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
		containment tree the operator is."""
		if self.mode == "detail" and self.detail_work is not None:
			trail = self._cached(("breadcrumb", self.detail_work),
			                     lambda: projection.breadcrumb(
				self.store, self.detail_work))
			return " > ".join(entry["title"] for entry in trail)
		if not self.path:
			# W74: the root view has no breadcrumb — the tab bar already
			# says where the operator is, so prose here would be noise.
			return ""
		trail = self._cached(("breadcrumb", self.path[-1]),
		                     lambda: projection.breadcrumb(
			self.store, self.path[-1]))
		return " > ".join(entry["title"] for entry in trail)

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
		"""Row 0: tabs first, then the Jobs trail, with the participant
		identity right-aligned. Identity is drawn LAST and overdraws, so
		no width can clip away who the operator is signed in as."""
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
		if self.work_filter and self.tab == "jobs":
			# W5 (ruled): active filtering is ALWAYS disclosed. It now
			# shares the right edge with the identity, so it sits just
			# left of it rather than under it.
			tag = f"Filter:{len(self.work_filter)}"
			at = width - 2 - len(tag) - len(self.participant)
			screen.addnstr(0, max(0, at), tag, width - 1, curses.A_BOLD)
		screen.addnstr(0, max(0, width - 1 - len(self.participant)),
		               self.participant, width - 1, curses.A_BOLD)

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
		elif self.mode == "search":
			rows = self.search_rows()
			summary = self._cached(
				("summary",),
				lambda: projection.team_summary(
					self.store, viewer_team=self.team))
		else:
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
			self._render_links(screen, height, width)
		elif self.mode == "pokes":
			# W17: the conversational pokes this participant is part of
			# — the ones owed an answer, and the ones they asked.
			self._render_pokes(screen, height, width)
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
			table_top = 1
			if self.work_filter:
				# The dedicated normalized-clause line; horizontally
				# viewported at narrow widths, never silently dropped.
				clauses = "filter: " + self._filter_clauses()
				if len(clauses) > width - 1:
					clauses = clauses[:max(0, width - 2)] + "…"
				screen.addnstr(1, 0, clauses, width - 1, curses.A_DIM)
				table_top = 2
			self._render_table(screen, height, width, rows,
			                   top=table_top)
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
		         ("Since", (pickup.get("since") or "-")[:19])]
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
		         ("Since", (runtime.get("since") or "-")[:19]),
		         ("Last contact",
		          (runtime.get("last_contact") or "-")[:19]),
		         ("Lease expires",
		          (runtime.get("expires_at") or "-")[:19]),
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
			              f"{runtime['refresh_requested'][:19]} — "
			              f"awaiting the adapter's next poll"))
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
		         ("At", answer["at"][:16].replace("T", " ")),
		         ("Explanation", answer["explanation"]),
		         ("Provider", runner["provider"]),
		         ("Model", runner["model"]),
		         ("Session state", runner["session_state"]),
		         ("Auth state", runner["auth_state"]),
		         ("Limit state", runner["limit_state"])]
		if runner["retry_at"]:
			pairs.append(("Retry at", runner["retry_at"]))
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
	                  top: int = 1) -> None:
		# W4 R1: the Id width comes from the rows ACTUALLY painted in
		# this view — a collapsed closed row must not consume Title
		# space or drop columns until `z` exposes it. The W39
		# dependency cue is scoped the same way, and is ONE whole
		# optional responsive field: when it alone breaks the fit it is
		# omitted entirely (never clipped); `[b] deps` stays available.
		visible, hidden = self.visible_rows(rows)
		id_width = id_column_width(visible)
		cue_width = cue_column_width(visible)
		# W73: the Out column is part of the budget exactly when the
		# view can hold terminal Work, so every fit judgment below
		# carries the same answer.
		terminal = self.terminal_visible()
		if cue_width and not layout_fits(
				width, id_width + 1 + cue_width, terminal):
			cue_width = 0
		lead = id_width + ((1 + cue_width) if cue_width else 0)
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
		claimed = any(row.get("handler") for row in rows)
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
		for name, col_width in columns:
			label = HEADER_LABELS.get(name, name.capitalize())
			header += " " + label.ljust(col_width)
		screen.addnstr(top, 0, header, width - 1, curses.A_UNDERLINE)
		# W5: the selection anchors to the WORK ID, not the index — a
		# background refresh that inserts or removes rows never moves
		# the cursor to a different Work.
		if self.selected_id is not None:
			for index, row in enumerate(visible):
				if row["id"] == self.selected_id:
					self.cursor = index
					break
			else:
				self.cursor = min(self.cursor,
				                  max(0, len(visible) - 1))
		if visible:
			self.selected_id = \
				visible[min(self.cursor, len(visible) - 1)]["id"]
		# The hidden-count footer is part of the collapse CONTRACT: when
		# closed rows are hidden, one line is RESERVED for naming them —
		# a full page of open rows may never make the collapse silent.
		budget = max(1, (height - 3 - top) if hidden
		             else (height - 2 - top))
		# The selected row must be PAINTED: Enter acts on it, and an
		# off-screen aim would be an invisible destructive action. Long
		# tables scroll so the cursor stays inside the drawn slice.
		start = max(0, min(self.cursor - budget + 1,
		                   len(visible) - budget))
		for offset, row in enumerate(visible[start:start + budget]):
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
			cells = self._row_cells(row)
			for name, col_width in columns:
				line += " " + cells[name][:col_width].ljust(col_width)
			attribute = curses.A_REVERSE \
				if start + offset == self.cursor else 0
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
		footer_row = top + 1 + min(len(visible) - start, budget)
		if hidden and footer_row <= height - 2:
			screen.addnstr(footer_row, 0,
			               f"({hidden} closed hidden — z shows)",
			               width - 1)
		if not visible and not hidden:
			screen.addnstr(top + 1, 0, "(no work here)", width - 1)
		if height - 2 > footer_row:
			screen.addnstr(
				height - 2, 0,
				"Enter details · u unfold · c claim · z closed · "
				"[b] deps · Esc back · : command · q quit", width - 1)

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

	def _links_rows(self) -> list[tuple[str, str]]:
		"""(work id, drawn line) pairs — every fact the `links`
		projection's far-row summary, with the STABLE id shown so the
		deliberate cross-team drill-through has a visible anchor."""
		view = self._cached(("links", self.links_work),
		                    lambda: projection.links(
			self.store, self.links_work))
		rows = []

		def far_text(prefix, entry):
			endpoint = (entry["route"]["endpoint"]
			            if entry["route"] else "-")
			extra = "" if entry["outcome"] is None \
				else f" {compact_outcome(entry['outcome'])}"
			rows.append((entry["id"],
			             f"{prefix} {entry['id']} {entry['team']} "
			             f"{entry['status']}{extra} {endpoint} "
			             f"{entry['title']}"))

		for entry in view["blocked_by"]:
			far_text("blocked-by", entry)
		for entry in view["blocks"]:
			far_text("blocks", entry)
		if view["duplicate_of"] is not None:
			far_text("duplicate-of", view["duplicate_of"])
		for entry in view["duplicates"]:
			far_text("duplicate", entry)
		return rows

	def _render_links(self, screen, height, width) -> None:
		rows = self._links_rows()
		if not rows:
			screen.addnstr(2, 0, "(no blocking or dependent neighbors)",
			               width - 1)
			return
		budget = max(1, height - 3)
		start = max(0, min(self.links_cursor - budget + 1,
		                   len(rows) - budget))
		for offset, (_work, text) in enumerate(
				rows[start:start + budget]):
			attribute = curses.A_REVERSE \
				if start + offset == self.links_cursor else 0
			screen.addnstr(2 + offset, 0, text, width - 1, attribute)

	# -- W17: the poke view ----------------------------------------------

	@staticmethod
	def _poke_stamp(value) -> str:
		"""One canonical instant as the console shows instants: date and
		minute, with the `T` and the zone marker spent on nothing a
		reader of a live console needs. The canonical value stays in
		JSON — this is the row's timestamp cell, not the record."""
		text = (value or "").replace("T", " ")
		return text[:16]

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

	DETAIL_TABS = ("messages", "events")

	def detail_tab_segments(self) -> list[tuple[str, str]]:
		"""`(tab name, drawn label)`, every label bracketed.

		W110: the same grammar the top level uses. The brackets say
		"this is a tab"; the active one is highlighted by the painter."""
		return [(name, f"[{name.title()}]")
		        for name in self.DETAIL_TABS]

	def _tab_bar(self) -> str:
		"""W123: `[Messages]  [Events]`. The bar is presentation; the
		tab itself is client state and touches no authority."""
		return TAB_GAP.join(label for _name, label
		                    in self.detail_tab_segments())

	def _switch_tab(self, step: int) -> None:
		"""`]` next, `[` previous. Each tab's own focus, selection, page
		cursor and reader scroll live in separate fields, so switching
		preserves both sides by construction rather than by saving and
		restoring a shared slot."""
		here = self.DETAIL_TABS.index(self.detail_tab)
		self.detail_tab = self.DETAIL_TABS[
			(here + step) % len(self.DETAIL_TABS)]

	def _detail_footer(self, screen, height, width, bits) -> None:
		"""The advertised controls. `[/] tabs` is ALWAYS present: the
		ruling is that tab navigation must not be discoverable only by
		prior knowledge.

		W1151 puts both pane gestures in ONE cell — `Tab/Ctrl-W panes`
		— rather than spending a second row or a second bit on the
		alternative. An operator who does not use Vim window commands
		needs to see that Tab works; one who does needs nothing new."""
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
		index_width = self.EVENT_INDEX_WIDTH
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
		bits.extend(["Tab/Ctrl-W panes", "j/k select", "Esc back"])
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

	def _event_columns(self, cell_width):
		"""The widest column set that fits, dropping from the right."""
		columns = list(self.EVENT_COLUMNS)
		while columns and sum(w for _n, w in columns) + len(columns) - 1 \
				> cell_width:
			columns.pop()
		return columns

	def _event_row(self, entry, columns) -> str:
		interval = entry.get("phase_interval")
		values = {
			"EVENT": f"E{entry['seq']}",
			"KIND": entry["kind"],
			"ACTOR": entry["actor"] or "",
			"TIME": (entry.get("ts") or "")[11:16],
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
		columns = self._event_columns(cell_width)
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
		         f"{entry['ts']}"]
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
			             f"{interval['started_at']}")
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
		column = 0
		# W110 review R2: the SAME narrow-layout rule the top level
		# uses. This loop used to stop at the first label too wide,
		# which left the inactive `[Messages]` alone on a 13-column bar
		# while the operator was in Events — advertising a tab the
		# screen did not show, and losing the one it did.
		for name, label in fitted_tabs(self.detail_tab_segments(),
		                               self.detail_tab,
		                               max(0, width - 1)):
			screen.addnstr(offset_row, column, label, width - 1 - column,
			               curses.A_BOLD | (curses.A_REVERSE
			                                if name == self.detail_tab
			                                else 0))
			column += len(label) + len(TAB_GAP)
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

	@classmethod
	def message_columns(cls, cell_width: int, id_width: int,
	                    cue_width: int | None = None):
		"""The columns that fit, dropping whole fields in reverse
		priority. `Id` and the selection cue always survive: a row whose
		selector is gone cannot be acted on, so there is nothing left to
		render.

		`cue_width` is the page's own `Do` allocation; the declared
		width is the minimum, never a cap."""
		widths = {name: width for name, width in cls.MESSAGE_COLUMNS}
		if cue_width is not None and "Do" in widths:
			widths["Do"] = max(widths["Do"], cue_width)
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
			"Time": (message.get("ts") or "")[11:16],
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
		columns = self.message_columns(cell_width, id_width,
		                               self.message_cue_width(messages))
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
		bits.extend(["Tab/Ctrl-W panes", "j/k select",
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
				# Esc restoration
				self.search_saved = (list(self.path), self.cursor,
				                     self.selected_id,
				                     self.show_closed)
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

	def _open_pokes(self) -> None:
		"""Enter the poke view on the row that wants an answer — owed
		pokes sort first, so that is simply the first row."""
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
		elif key == 27:
			# the exact prior table state returns — path, cursor,
			# selection, AND closed visibility (R2); the filter was
			# never search's to change
			path, cursor, selected, shown = \
				self.search_saved or ([], 0, None, self.show_closed)
			self.path = path
			self.cursor = cursor
			self.selected_id = selected
			self.show_closed = shown
			self.search_query = None
			self.search_saved = None
			self.mode = "table"
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
		if key in (ord("["), ord("]")) and self.mode != "detail":
			step = -1 if key == ord("[") else 1
			self.tab = TABS[(TABS.index(self.tab) + step) % len(TABS)]
			return True
		if self.tab == "inbox":
			return self._handle_inbox(key)
		if self.tab == "teams":
			return self._handle_teams(key)
		if key == ord("/") and self.mode in ("table", "search"):
			# W6: open (or replace) the search query bar.
			self.search_input = ""
			return True
		if self.mode == "search":
			return self._search_mode_key(key)
		if self.mode == "pokes":
			return self._handle_pokes(key)
		rows, _hidden = (self.visible_rows(self.rows())
		                 if self.mode == "table" else ([], 0))

		if self.mode == "links":
			entries = self._links_rows()
			if key in (curses.KEY_DOWN, ord("j")):
				self.links_cursor = min(self.links_cursor + 1,
				                        max(0, len(entries) - 1))
			elif key in (curses.KEY_UP, ord("k")):
				self.links_cursor = max(0, self.links_cursor - 1)
			elif key in (curses.KEY_ENTER, 10, 13) and entries:
				# The deliberate cross-team drill-through (ruled): the
				# far Work re-roots the tree; the breadcrumb
				# reconstructs its real ancestry.
				self.path = [entries[self.links_cursor][0]]
				self.cursor = 0
				self.selected_id = None
				self.mode = "table"
				self.links_work = None
			elif key in (27, curses.KEY_LEFT, ord("i")):
				self.mode = "table"
				self.links_work = None
			return True
		if self.mode == "detail":
			return self._handle_detail(key)
		# -- the Work tree ------------------------------------------------
		if key in (curses.KEY_DOWN, ord("j")):
			self.cursor = min(self.cursor + 1, max(0, len(rows) - 1))
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_UP, ord("k")):
			self.cursor = max(0, self.cursor - 1)
			self.selected_id = rows[self.cursor]["id"] if rows else None
		elif key in (curses.KEY_ENTER, 10, 13) and rows:
			# W71: Enter has ONE meaning — open the selected Work's
			# detail view. It never drills into children.
			self._enter_detail(rows[self.cursor]["id"],
			                   came_from="table")
		elif key == ord("u") and rows:
			# W71/W155: the visible unfold — re-root the three-level
			# window at the selected Work; breadcrumbs identify the
			# position and Esc returns upward. Re-rooting at the current root is
			# idempotent: one logical unfold, one Back (R2).
			target = rows[self.cursor]["id"]
			if not (self.path and self.path[-1] == target):
				self.path.append(target)
				self.cursor = 0
				self.selected_id = None
		elif key == ord("b") and rows:
			self.links_work = rows[self.cursor]["id"]
			self.links_cursor = 0
			self.mode = "links"
		elif key == ord("c") and rows:
			self._claim_selected(rows)
		elif key == ord("p"):
			# W17: the poke view opens with no Work selected and none
			# needed — a poke is addressed to a participant, not to
			# Work, so it is reachable from an empty table too.
			self._open_pokes()
		elif key == ord("z"):
			self.show_closed = not self.show_closed
			shown, _hidden = self.visible_rows(self.rows())
			self.cursor = min(self.cursor, max(0, len(shown) - 1))
			self.selected_id = shown[self.cursor]["id"] if shown \
				else None
		elif key in (27, curses.KEY_LEFT) and self.path:
			self.path.pop()
			self.cursor = 0
			self.selected_id = None
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
				order = ("index", "reader")
				here = self.event_focus if self.event_focus in order \
					else "index"
				self.event_focus = order[(order.index(here) + step)
				                         % len(order)]
			else:
				here = self.focus if self.focus in regions else "index"
				self.focus = regions[(regions.index(here) + step)
				                     % len(regions)]
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
			# W6: leaving detail returns to the view that opened it —
			# the search results when the result row was entered.
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
		untouched; it was never meant to follow the operator to a
		different Work."""
		self.detail_work = work_id
		self.detail_tab = "messages"
		self.disc_cursor = None      # the New-first default
		self.disc_after = 0
		self.focus = DETAIL_ENTRY_FOCUS
		self._reset_message_selection()
		self.event_cursor = None
		self.event_before = None
		self.event_focus = "index"
		self.event_skip = 0
		self.detail_return = came_from
		self.mode = "detail"

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
