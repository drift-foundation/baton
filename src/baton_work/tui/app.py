"""Curses rendering of the canonical projection — B1.

THE PINNED MODEL, exactly: open on a borderless fixed-column table of the
viewer's top-level Work; Enter drills into a table of immediate children, the
same interaction at every depth; a persistent breadcrumb names the drilled
path; `o` opens the focused Work view (facts, trials, and the selectable
thread set); Enter there opens one thread's paged thread — never
several merged into a false timeline. `b` shows blocking/dependent neighbors
with stable ids and drills through on Enter. Column priorities, sorting and
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
import time as _time
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
COLUMNS = (("ST", 6), ("PR", 2), ("PHASE", 6), ("CLS", 5),
           ("MSG/MY", 7), ("ROUTE", 13), ("HANDLER", 13), ("NEXT", 13),
           ("NEW", 4), ("HELD", 6))

# Header LABELS where plain capitalize() would miscase a compound name —
# plus the ruled `Cat` display label for the classification column
# (finding-tui-category-header): presentation only, the canonical value,
# JSON field, and compact vocabulary stay `classification`/`defct`-style.
HEADER_LABELS = {"MSG/MY": "Msg/My", "CLS": "Cat"}

# Responsive omission (prototype-grade presentation under the ruling): at
# narrow widths whole low-priority columns are OMITTED, never squeezed into
# ambiguity — identities and counters are drawn whole or not at all. The
# title keeps a minimum working width; below the minimum the table REFUSES
# with an explicit too-narrow line instead of truncating identities.
# W3 (ruled): Pr is the FIRST whole column omitted under width
# pressure, preserving every previously existing narrow layout.
# W245: NEXT then ROUTE go before CURRENT — under width pressure the
# question that survives longest is who is actually executing.
DROP_ORDER = ("PR", "CLS", "PHASE", "MSG/MY", "HELD", "NEXT", "ROUTE")
MIN_TITLE = 10

# One bounded page of a Work's thread SET (prototype size): `n` pages
# forward through the canonical continuation cursor, `p` returns to the
# start — every thread is reachable, none is silently truncated.
DISC_PAGE = 10

# W7 split-pane (ruled): below this terminal height the console stays
# single-pane — the split never squeezes the Work table into
# uselessness on a short terminal.
MIN_SPLIT_HEIGHT = 14


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
	  enforces them (accept's two forms, parked/waiting, say's
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
	- the Work is open, ready, unclaimed, not waiting/parked, and its
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
	        and row.get("phase") not in ("waiting", "parked")
	        and route is not None
	        and route["endpoint"].split(".", 1)[0] == viewer_team
	        and viewer_member in (route.get("handlers") or ()))


def visible_columns(width: int, id_width: int = 0):
	"""The column set that fits `width`, dropping DROP_ORDER members until
	the title keeps MIN_TITLE cells. Shared with the parity suite so the
	two surfaces can never disagree about the layout. `id_width` is the
	W4 leading Id column (plus its separator) the budget must carry —
	the Id itself is identity and is never dropped or truncated."""
	lead = id_width + 1 if id_width else 0
	columns = list(COLUMNS)
	for name in DROP_ORDER:
		fixed = sum(w for _n, w in columns) + len(columns)
		if width - fixed - lead - 1 >= MIN_TITLE:
			break
		columns = [entry for entry in columns if entry[0] != name]
	return tuple(columns)


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

	CLAIMED: `MM:SS` since canonical claimed_at (the visible reset at
	pickup preserves when the recipient actually took the Work).
	UNCLAIMED OPEN: `MM:SS` since the committed handoff, or `-` when
	there is no handoff to time. CLOSED: `-`. Which of the first two a
	row is reading is answered by `Handler`, not by a glyph here.
	Readiness, wait and park remain separate table and JSON facts."""
	claimed_at = row.get("claimed_at")
	if claimed_at is not None:
		return held_cell(claimed_at, now)
	if row.get("status") == "closed":
		return "-"
	return held_cell(row.get("handoff_at"), now)


def blocker_cue(row: dict) -> str:
	"""W39/W187: the inline dependency cue under the `Wait` heading —
	`Wn` names the deterministic first OPEN blocker (canonical
	projection data, the reviewed W4 selector identity), `+N` counts
	the remaining open blockers: `W171+2` waits on W171 and two more.
	Empty when nothing open blocks the row. NO arrow (W187 ruling: it
	competed with the containment marker and `Blk` read ambiguously);
	a dependency is a graph edge, never a containment child — the `↳`
	marker is a different fact and stays untouched."""
	first = row.get("first_open_blocker")
	if not first:
		return ""
	more = row["open_blockers"] - 1
	return f"{first}" + (f"+{more}" if more > 0 else "")


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


def layout_fits(width: int, id_width: int = 0) -> bool:
	"""W4 R2: the fit judgment carries the VISIBLE Id column — identity
	is never truncated, and its growth may never silently clip the
	mandatory tail either; past the budget the table refuses whole."""
	lead = id_width + 1 if id_width else 0
	columns = visible_columns(width, id_width)
	fixed = sum(w for _n, w in columns) + len(columns)
	return width - fixed - lead - 1 >= MIN_TITLE


# WS-1 approved compact vocabulary — PRESENTATION ONLY, capped at five
# display cells, never a protocol identity and never a mutation value. Both
# maps are CLOSED (R5 ruling): an unmapped canonical value fails visibly —
# a client must never invent a label by truncation.
PHASE_COMPACT = {"queued": "queue", "waiting": "wait",
                 "active": "actve", "parked": "park"}
# W6 (ruled): confirmed-defect reads `defct` — cnfrm did not express
# the classification. Presentation only; canonical values unchanged.
# W3 (ruled): the two-cell compact priority — presentation only; the
# canonical values and every mutation input stay the full strings.
PRIORITY_COMPACT = {"high": "Hi", "normal": "No", "low": "Lo"}


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
OUTCOME_COMPACT = {"satisfying": "c/sat", "non-satisfying": "c/nsat",
                   "rejected": "c/rej", "cancelled": "c/canc"}


def compact_outcome(value: str) -> str:
	if value not in OUTCOME_COMPACT:
		raise ValueError(f"outcome {value!r} has no ruled compact rendering")
	return OUTCOME_COMPACT[value]


def status_cell(row: dict) -> str:
	"""ST formats the projection's status plus, when closed, its outcome —
	both canonical values, never a client-side judgement."""
	if row["status"] == "open":
		return "open"
	return compact_outcome(row["outcome"])


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
		self.focus = "threads"
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
		# W81: the contextual `say` seed. `seeded_say` is the exact
		# operand text this client inserted, so an explicit one arriving
		# later can displace precisely that and nothing else.
		self.seeded_say: str | None = None
		# W9: the one-row exit confirmation — q asks, y answers.
		self.confirm_exit = False
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
		"""(tree rows, summary) — W71: the main screen is a bounded
		TWO-LEVEL containment window. At the top it shows every root
		plus each root's immediate children (depth 1, `↳`); re-rooted
		(`u`) it shows the selected Work plus its immediate children.
		Indentation is the single-parent containment tree ONLY — graph
		edges never masquerade as children. Each row dict carries a
		presentation `depth`."""
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

	def visible_rows(self, rows: list[dict]) -> tuple[list[dict], int]:
		"""(rows to draw, hidden closed count) — the collapse is pure
		presentation over the projection's own status values. W5 R1: an
		EXPLICIT status=closed filter reveals the rows it selected —
		the default collapse would erase the filter's whole answer (and
		its open context parents); the ordinary collapse applies
		whenever no status filter requests closed Work."""
		if self.show_closed or \
				(self.work_filter or {}).get("status") == "closed":
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

	def breadcrumb_text(self, summary: dict) -> str:
		# W136: the header's oblig/due are the VIEWER'S actionable
		# counts — from the same participant projection wait consumes,
		# never the whole team's load (parity holds them equal to the
		# JSON facts). The parked count stays deliberately TEAM-wide
		# and always visible (WS-1 ruling): parked work has no wake
		# condition, so it stays in the operators' faces.
		mine = self._cached(
			("participant_actions",),
			lambda: projection.participant_actions(
				self.store, viewer_team=self.team,
				viewer_member=self.member))["actions"]
		pending = sum(1 for action in mine
		              if action["kind"] == "obligation")
		due = sum(1 for action in mine
		          if action["kind"] == "due_trial")
		suffix = (f"  [oblig:{pending}] [park:{summary['parked']}]"
		          f" [due:{due}]")
		# W71: the DETAIL view identifies its Work with the real
		# containment breadcrumb.
		if self.mode == "detail" and self.detail_work is not None:
			trail = self._cached(("breadcrumb", self.detail_work),
			                     lambda: projection.breadcrumb(
				self.store, self.detail_work))
			return " > ".join(entry["title"]
			                  for entry in trail) + suffix
		if not self.path:
			# W74: the root view has no breadcrumb, so the location is
			# already unambiguous — identity plus the live summary only,
			# no redundant prose.
			return f"{self.team}.{self.member}{suffix}"
		trail = self._cached(("breadcrumb", self.path[-1]),
		                     lambda: projection.breadcrumb(
			self.store, self.path[-1]))
		return " > ".join(entry["title"] for entry in trail) + suffix

	# -- rendering ------------------------------------------------------------

	def render(self, screen) -> None:
		screen.erase()
		height, width = screen.getmaxyx()
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
		screen.addnstr(0, 0, self.breadcrumb_text(summary), width - 1,
		               curses.A_BOLD)
		if self.work_filter:
			# W5 (ruled): active filtering is ALWAYS disclosed — the
			# clause count overdraws RIGHT-aligned so no narrow width
			# can clip it away.
			tag = f"Filter:{len(self.work_filter)}"
			screen.addnstr(0, max(0, width - 1 - len(tag)), tag,
			               width - 1, curses.A_BOLD)
		if self.mode == "detail":
			# W71 (ruled, superseding the main-screen split): the Work
			# detail view — Threads above, the selected Thread's
			# Messages below, Ctrl-W pane navigation.
			self._render_detail(screen, height, width)
		elif self.mode == "links":
			self._render_links(screen, height, width)
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
		caret = None
		if self.confirm_exit:
			# One row, drawn whole at any width the console accepts.
			screen.addnstr(height - 1, 0, "Exit? y/N", width - 1)
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
			typed = ":" + self.command
			avail = width - 1
			if len(typed) < avail:
				screen.addnstr(height - 1, 0, typed, avail)
				room = avail - len(typed) - 2
				if room >= 8:
					if self.command.strip() == "filter" and \
							self.work_filter:
						# W5 (ruled): command entry exposes the
						# current clauses — SPACE seeds them into the
						# buffer for editing; bare Enter clears.
						hint = ("current: " + self._filter_clauses()
						        + " · space edits · Enter clears")
					else:
						hint = assist_text(self.command)
					screen.addnstr(height - 1, len(typed) + 2,
					               hint[:room], room, curses.A_DIM)
				caret = (height - 1, len(typed))
			else:
				tail = typed[len(typed) - (avail - 2):]
				screen.addnstr(height - 1, 0, "<" + tail, avail)
				caret = (height - 1, 1 + len(tail))
		elif self.status:
			screen.addnstr(height - 1, 0, self.status, width - 1)
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
			"ST": status_cell(row),
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
			"ROUTE": row["route"]["endpoint"] if row["route"] else "-",
			# W245/W38: the exact claimant, or `-` when NOBODY holds
			# it. Phase says whether the Work is running; this says who
			# is running it.
			"HANDLER": (f"{row['handler']['team']}."
			            f"{row['handler']['member']}")
			if row["handler"] else "-",
			"NEXT": row["next"]["endpoint"] if row["next"] else "-",
			"NEW": str(row["new"]),
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
		if cue_width and not layout_fits(
				width, id_width + 1 + cue_width):
			cue_width = 0
		lead = id_width + ((1 + cue_width) if cue_width else 0)
		if not layout_fits(width, lead):
			columns = visible_columns(width, lead)
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
		columns = visible_columns(width, lead)
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
			title = row["title"]
			if row.get("depth"):
				title = "↳ " + title
			if row.get("depth") and row["progress"]["children"]:
				title += f" ▸{row['progress']['children']}"
			line = (row["local_id"].ljust(id_width) + " "
			        + title[:title_width].ljust(title_width))
			if cue_width:
				line += " " + blocker_cue(row).ljust(cue_width)
			cells = self._row_cells(row)
			for name, col_width in columns:
				line += " " + cells[name][:col_width].ljust(col_width)
			attribute = curses.A_REVERSE \
				if start + offset == self.cursor else 0
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
					top + 1 + offset, id_width + 1,
					title[:title_width].ljust(title_width),
					min(title_width, max(0, width - 1 - id_width - 1)),
					attribute | curses.A_BOLD)
			if self.phase_blink.get(row["id"], 0) > 0:
				# W33: the ephemeral phase-CHANGE cue — the phase cell
				# blinks for three scheduled refresh ticks after an
				# OBSERVED genuine Phase change, then the steady bold
				# Title + Age remain. At widths where the PHASE column
				# is dropped there is simply no cell to animate.
				x = id_width + 1 + title_width \
					+ ((1 + cue_width) if cue_width else 0)
				for name, col_width in columns:
					x += 1
					if name == "PHASE":
						if x < width - 1:
							screen.addnstr(
								top + 1 + offset, x,
								cells["PHASE"][:col_width]
								.ljust(col_width),
								min(col_width, width - 1 - x),
								attribute | curses.A_BLINK)
						break
					x += col_width
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
		waiting = detail.get("waiting_on")
		if waiting is not None:
			line += f"  wait:{waiting['type']}"
			if waiting["obligation"] is not None:
				line += f"#{waiting['obligation']}"
		return line

	DETAIL_TABS = ("messages", "events")

	def _tab_bar(self) -> str:
		"""W123: `Messages  Events` with the active tab distinguished.
		The bar is presentation; the tab itself is client state and
		touches no authority."""
		return "  ".join(
			f"[{name.title()}]" if name == self.detail_tab
			else f" {name.title()} "
			for name in self.DETAIL_TABS)

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
		prior knowledge."""
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
		wide = width - 1 - self.INDEX_WIDTH - 2 >= self.MIN_READER
		if wide:
			reader_x = self.INDEX_WIDTH + 2
			reader_width = width - 1 - reader_x
			screen.addnstr(top, 0, index_label, self.INDEX_WIDTH,
			               index_bold)
			screen.addnstr(top, reader_x, reader_label, reader_width,
			               reader_bold)
			self._paint_event_index(screen, top + 1, region - 1, 0,
			                        self.INDEX_WIDTH, events)
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
		bits.extend(["Ctrl-W panes", "j/k select", "Esc back"])
		self._detail_footer(screen, height, width, bits)

	def _paint_event_index(self, screen, top, rows, x, cell_width,
	                       events):
		"""`E<seq>` is the visible stable event identifier — the
		authoritative sequence, nothing invented. Newest first, matching
		the Message index."""
		if not events:
			screen.addnstr(top, x, "(no events on this page)",
			               cell_width)
			return
		ordered = list(reversed(events))
		seqs = [entry["seq"] for entry in ordered]
		chosen = seqs.index(self.event_cursor) \
			if self.event_cursor in seqs else 0
		start = max(0, min(chosen - rows + 1, len(ordered) - rows))
		for offset, entry in enumerate(ordered[start:start + rows]):
			stamp = (entry.get("ts") or "")[11:16]
			text = (f"E{entry['seq']} {entry['kind']} {stamp} "
			        f"{entry['actor']}")
			attribute = curses.A_REVERSE \
				if entry["seq"] == self.event_cursor else 0
			screen.addnstr(top + offset, x,
			               text[:cell_width].ljust(cell_width),
			               cell_width, attribute)

	def _event_lines(self, entry) -> list[str]:
		"""Human labels for the common typed fields, then the COMPLETE
		payload. Routine events read compactly, but nothing is hidden:
		the ruling is that folding must be explicit, never silent
		omission."""
		payload = entry.get("payload") or {}
		lines = [f"#{entry['seq']} {entry['kind']} {entry['actor']} "
		         f"{entry['ts']}",
		         f"  roles: {', '.join(entry['roles'])}"]
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
		for label in ("rationale", "reason", "comment", "outcome",
		              "from", "to", "destination_phase", "title",
		              "classification", "priority", "claimant",
		              "released_claimant", "blocker", "provider"):
			if payload.get(label) is not None:
				lines.append(f"  {label}: {payload[label]}")
		for reference in entry.get("references") or ():
			lines.append(f"  ref: {reference.get('root')}:"
			             f"{reference.get('path')}")
		import json as _payload_json
		lines.append("  payload: "
		             + _payload_json.dumps(payload, sort_keys=True))
		return lines

	def _paint_event_reader(self, screen, top, rows, x, cell_width,
	                        entry) -> None:
		if entry is None:
			screen.addnstr(top, x, "(no event selected)", cell_width)
			self.event_clipped = False
			return
		import textwrap
		wrapped = []
		for line in self._event_lines(entry):
			indent = "    " if line.startswith("  ") else "  "
			wrapped.extend(textwrap.wrap(line, max(8, cell_width),
			                             subsequent_indent=indent)
			               or [""])
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
		# distinguished rather than merely remembered.
		screen.addnstr(offset_row, 0, self._tab_bar(), width - 1,
		               curses.A_BOLD)
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

	def _paint_index(self, screen, top, rows, x, cell_width, messages):
		"""The compact Message index: `M<seq>` (the existing stable
		sequence — nothing invented), author, time, and the personal
		new/seen state. W76: the NEWEST Message paints at the top; the
		page itself stays canonical ascending everywhere else, so only
		this display order is reversed. The selected row is reversed;
		personal-new rows are bold; the window scrolls to keep the
		selection painted."""
		if not messages:
			screen.addnstr(top, x, "(no messages on this page)",
			               cell_width)
			return
		messages = list(reversed(messages))
		seqs = [message["seq"] for message in messages]
		chosen = seqs.index(self.msg_cursor) \
			if self.msg_cursor in seqs else 0
		start = max(0, min(chosen - rows + 1, len(messages) - rows))
		for offset, message in enumerate(messages[start:start + rows]):
			stamp = (message.get("ts") or "")[11:16]
			state = "new" if message.get("new") else "seen"
			text = (f"M{message['seq']} {message['author_team']}."
			        f"{message['author']} {stamp} {state}")
			attribute = 0
			if message["seq"] == self.msg_cursor:
				attribute = curses.A_REVERSE
			elif message.get("new"):
				attribute = curses.A_BOLD
			screen.addnstr(top + offset, x,
			               text[:cell_width].ljust(cell_width),
			               cell_width, attribute)

	def _paint_reader(self, screen, top, rows, x, cell_width, selected):
		"""The reader: exactly ONE selected Message as its canonical
		formatted block — metadata header, wrapped body, Refs visually
		separate — scrolled by `reader_skip` with an honest `(cont.)`
		tag; a clipped tail is disclosed, never silently dropped."""
		if selected is None:
			screen.addnstr(top, x, "(no message selected)", cell_width)
			self.reader_clipped = False
			return
		block = format_message(selected, cell_width)
		skip = min(self.reader_skip, max(0, len(block) - 1))
		self.reader_skip = skip
		visible = block[skip:]
		if skip:
			visible = [f"M{selected['seq']} (cont.)"] + visible
		take = max(0, min(len(visible), rows))
		for offset, text in enumerate(visible[:take]):
			attribute = curses.A_BOLD if offset == 0 and \
				(skip or selected.get("new")) else 0
			screen.addnstr(top + offset, x, text, cell_width,
			               attribute)
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
		reader_bold = curses.A_BOLD if self.focus == "reader" else 0
		imarker = "»" if self.focus == "index" else " "
		rmarker = "»" if self.focus == "reader" else " "
		# W76: the index reads newest-first, so "more" is honestly OLDER.
		more = "  (n: older)" if snapshot["next_before"] is not None \
			else ""
		# W176 (finding-message-pane-header-redundancy): the split-area
		# headings identify PANE ROLES, never content already visible in
		# the selected Thread and Message rows. The Thread row owns the
		# subject; the reversed index row owns selection; the reader
		# heading names the selected message exactly once.
		index_label = f"{imarker}Messages ({len(messages)}){more}"
		reader_label = f"{rmarker}Message M{selected['seq']}" \
			if selected else f"{rmarker}Message"
		wide = width - 1 - self.INDEX_WIDTH - 2 >= self.MIN_READER
		if wide:
			reader_x = self.INDEX_WIDTH + 2
			reader_width = width - 1 - reader_x
			screen.addnstr(top, 0, index_label, self.INDEX_WIDTH,
			               index_bold)
			screen.addnstr(top, reader_x, reader_label, reader_width,
			               reader_bold)
			self._paint_index(screen, top + 1, region - 1, 0,
			                  self.INDEX_WIDTH, messages)
			self._paint_reader(screen, top + 1, region - 1, reader_x,
			                   reader_width, selected)
		else:
			index_rows = max(1, min(len(messages) or 1,
			                        max(2, region // 3),
			                        region - 3))
			screen.addnstr(top, 0, index_label, width - 1,
			               index_bold)
			self._paint_index(screen, top + 1, index_rows, 0,
			                  width - 1, messages)
			reader_top = top + 1 + index_rows
			screen.addnstr(reader_top, 0, reader_label, width - 1,
			               reader_bold)
			self._paint_reader(screen, reader_top + 1,
			                   top + region - reader_top - 1, 0,
			                   width - 1, selected)
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
		bits.extend(["Ctrl-W panes", "j/k select",
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

	def execute(self, line: str) -> None:
		"""The one-line `:` bar: feed the typed command through
		`_run_line` and surface the brief or the refusal."""
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
			self.detail_work = rows[min(self.cursor,
			                            len(rows) - 1)]["id"]
			self.disc_cursor = None
			self.disc_after = 0
			self.focus = "threads"
			self._reset_message_selection()
			self.detail_return = "search"
			self.mode = "detail"
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
				self.command = head + rest
				self.seeded_say = None
			return
		if self.command != "say":
			return
		selector = self._selected_thread_selector()
		if selector is None:
			return
		self.seeded_say = f"thread={selector} "
		self.command = f"say {self.seeded_say}"

	def _command_key(self, key: int) -> None:
		if key == ord(" ") and self.command == "filter" and \
				self.work_filter:
			# W5 R2: the first space after exact `filter` SEEDS the
			# buffer with the normalized current clauses — the
			# operator edits one clause without retyping the rest,
			# and Enter replaces atomically through the same parser.
			# Bare `filter` + Enter still clears.
			self.command = "filter " + self._filter_clauses()
			return
		if key == ord(":") and self.command == "":
			# W19: `::` — a second colon on the EMPTY bar converts it
			# into the multiline batch buffer. The one-line `:`
			# interaction is otherwise untouched.
			self.command = None
			self.batch = [self._batch_line("")]
			self.batch_cursor = 0
			self.batch_confirm = False
			self.batch_status = ""
			return
		if key in (10, 13, curses.KEY_ENTER):
			line, self.command = self.command, None
			self.seeded_say = None
			self.execute(line)
		elif key == 27:
			self.command = None
			self.seeded_say = None
		elif key in (8, 127, curses.KEY_BACKSPACE):
			self.command = self.command[:-1]
			self._reconcile_say_seed()
		elif 32 <= key <= 126:
			self.command += chr(key)
			self._reconcile_say_seed()

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
		if key == ord("q"):
			self.confirm_exit = True
			return True
		self.status = ""
		if key == ord(":"):
			self.command = ""
			return True
		if key == ord("/") and self.mode in ("table", "search"):
			# W6: open (or replace) the search query bar.
			self.search_input = ""
			return True
		if self.mode == "search":
			return self._search_mode_key(key)
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
			self.detail_work = rows[self.cursor]["id"]
			self.disc_cursor = None      # the New-first default
			self.disc_after = 0
			self.focus = "threads"
			self._reset_message_selection()
			self.detail_return = "table"
			self.mode = "detail"
		elif key == ord("u") and rows:
			# W71: the visible unfold — re-root the two-level window at
			# the selected Work; breadcrumbs identify the position and
			# Esc returns upward. Re-rooting at the current root is
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


# W25: the normal-mode (DECCKM off) cursor spellings, which `smkx` asks
# terminals not to use and some send anyway. The application-mode forms
# (`ESC O A`…) are already translated by keypad, and `ESC [ A`… are what
# reaches the loop as a bare escape.
ESCAPE_PEEK_MS = 25
_CURSOR_FINALS = {ord("A"): curses.KEY_UP, ord("B"): curses.KEY_DOWN,
                  ord("C"): curses.KEY_RIGHT, ord("D"): curses.KEY_LEFT}


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
	if final != -1:
		curses.ungetch(final)
	curses.ungetch(introducer)
	return 27


def run(screen, store: Authority, viewer_team: str, viewer_member: str,
        config_path: str | None = None, refresh: float = 2.0,
        work_filter: dict | None = None) -> None:
	"""W5: `refresh` seconds (default 2, positive, configurable via
	`tui refresh=`) is the ONE background trigger for fresh canonical
	reads — getch times out, the cache drops, the screen repaints.
	Ordinary keystrokes operate on the cached projection."""
	import time
	curses.curs_set(0)
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
		key = screen.getch()
		if key == -1:
			continue
		if key == 27:
			key = _decode_normal_mode_cursor(screen)
		if not console.handle(key):
			return
		console.render(screen)


# SUPERSEDED (C3): the module-level entry that opened a raw authority path is
# gone. The ONLY launch is `baton --config ... --participant ... tui`,
# which opens through the bound lifecycle and validates the participant
# before curses claims the screen — the v10 console's refuse-first lesson,
# now enforced by the configuration boundary rather than by this module.
