"""Curses rendering of the canonical projection — B1.

THE PINNED MODEL, exactly: open on a borderless fixed-column table of the
viewer's top-level Work; Enter drills into a table of immediate children, the
same interaction at every depth; a persistent breadcrumb names the drilled
path; `o` opens the focused Work view (facts, rounds, and the selectable
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
import shlex
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
COLUMNS = (("ST", 6), ("PHASE", 5), ("CLS", 5), ("MSG/MY", 7),
           ("READY", 5), ("CURRENT", 13), ("NEXT", 13), ("NEW", 4))

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
DROP_ORDER = ("CLS", "PHASE", "MSG/MY", "READY", "NEXT")
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
	"""W84 (ruled hot zone): open Work someone is EXECUTING (a non-null
	active claimant, any operational phase) or runnable review Work
	someone needs to CLAIM (phase=review with ready=true, including the
	interval before the reviewer claims). Blocked (ready=false) review,
	waiting, parked, and terminal Work are cold. Derived from canonical
	row state alone — no recency clock, no timestamp inference, no
	authority read of its own."""
	return row["status"] == "open" and (
		row["active"] is not None
		or (row["phase"] == "review" and row["ready"]))


def visible_columns(width: int):
	"""The column set that fits `width`, dropping DROP_ORDER members until
	the title keeps MIN_TITLE cells. Shared with the parity suite so the
	two surfaces can never disagree about the layout."""
	columns = list(COLUMNS)
	for name in DROP_ORDER:
		fixed = sum(w for _n, w in columns) + len(columns)
		if width - fixed - 1 >= MIN_TITLE:
			break
		columns = [entry for entry in columns if entry[0] != name]
	return tuple(columns)


def layout_fits(width: int) -> bool:
	columns = visible_columns(width)
	fixed = sum(w for _n, w in columns) + len(columns)
	return width - fixed - 1 >= MIN_TITLE


# WS-1 approved compact vocabulary — PRESENTATION ONLY, capped at five
# display cells, never a protocol identity and never a mutation value. Both
# maps are CLOSED (R5 ruling): an unmapped canonical value fails visibly —
# a client must never invent a label by truncation.
PHASE_COMPACT = {"queued": "queue", "research": "rsrch", "waiting": "wait",
                 "active": "actve", "review": "rview", "parked": "park"}
# W6 (ruled): confirmed-defect reads `defct` — cnfrm did not express
# the classification. Presentation only; canonical values unchanged.
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


def paint_messages(screen, top: int, budget: int, width: int,
                   messages, skip: int = 0) -> dict:
	"""Paint formatted blocks into `budget` lines. Whole blocks only —
	EXCEPT the first message, which may continue across pages via
	`skip` (R1: a message taller than the viewport stays readable).
	Returns the honest seen bound: `painted_last` names a message only
	once its FINAL line has actually been painted — a clipped block or
	an unfinished continuation never counts.

	  painted_last  seq eligible for the explicit seen mark, or None
	  next_skip     None, or the skip cursor for the next `n` page of
	                the still-unfinished first message"""
	row = top
	painted_last = None
	more_below = False
	for index, message in enumerate(messages):
		block = format_message(message, width)
		attribute = curses.A_BOLD if message.get("new") else 0
		if index == 0 and (skip or len(block) > budget):
			# The continuation path: paint what fits from the skip
			# cursor; a compact header that survives narrow panes tags
			# the same message.
			visible = block[skip:]
			if skip:
				visible = [f"#{message['seq']} (cont.)"] + visible
			take = min(len(visible), top + budget - row)
			if take <= 0:
				return {"painted_last": None, "next_skip": skip}
			for offset, text in enumerate(visible[:take]):
				screen.addnstr(row + offset, 0, text, width - 1,
				               attribute if offset == 0 else 0)
			row += take
			consumed = take - (1 if skip else 0)
			if skip + consumed < len(block):
				return {"painted_last": None,
				        "next_skip": skip + consumed,
				        "more_below": True}
			painted_last = message["seq"]
			continue
		if row + len(block) > top + budget:
			# R1 (W71 review): a LATER fetched block did not fit — the
			# page is not "everything"; the more-state and `n` must
			# both know, and the clipped block is never counted seen.
			more_below = True
			break
		screen.addnstr(row, 0, block[0], width - 1, attribute)
		for offset, text in enumerate(block[1:], start=1):
			screen.addnstr(row + offset, 0, text, width - 1)
		row += len(block)
		painted_last = message["seq"]
	return {"painted_last": painted_last, "next_skip": None,
	        "more_below": more_below}


class Console:
	def __init__(self, store: Authority, viewer_team: str,
	             viewer_member: str, config_path: str | None = None):
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
		self.viewed_last_seq: int | None = None
		self.thread_after = 0
		# R1: intra-message continuation cursors — lines of the current
		# first block already shown on earlier pages.
		self.thread_skip = 0

		# R4: a skip is a LINE index into the block wrapped at one
		# specific width — each cursor remembers that width and resets
		# to zero when the terminal changes, so a resize can repeat
		# content but can never omit it or fake a full paint.
		self.thread_skip_width: int | None = None

		self.command: str | None = None  # the `:` command-bar buffer
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
		no cursor decision lives here."""
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
		window = self._cached(("tree", root_id),
		                      lambda: projection.tree(
			self.store, root_id, viewer_team=self.team,
			viewer_member=self.member))
		return list(window["rows"]), window["summary"]

	def rows(self) -> list[dict]:
		return self.view()[0]

	def visible_rows(self, rows: list[dict]) -> tuple[list[dict], int]:
		"""(rows to draw, hidden closed count) — the collapse is pure
		presentation over the projection's own status values."""
		if self.show_closed:
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
		# Actionable state on the same line, FROM the projection: the count
		# a member acts on is never derived here (parity holds it equal to
		# the JSON obligations list).
		pending = len(self._cached(
			("obligations",), lambda: projection.obligations(
				self.store, viewer_team=self.team)))
		# The parked count is ALWAYS visible (WS-1 ruling): parked work has
		# no wake condition, so it stays in the operators' faces.
		suffix = (f"  [oblig:{pending}] [park:{summary['parked']}]"
		          f" [due:{summary['due']}]")
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
		rows, summary = (self.view() if self.mode == "table"
		                 else ([], self._cached(
		                     ("summary",),
		                     lambda: projection.team_summary(
			self.store, viewer_team=self.team))))
		screen.addnstr(0, 0, self.breadcrumb_text(summary), width - 1,
		               curses.A_BOLD)
		if self.mode == "detail":
			# W71 (ruled, superseding the main-screen split): the Work
			# detail view — Threads above, the selected Thread's
			# Messages below, Ctrl-W pane navigation.
			self._render_detail(screen, height, width)
		elif self.mode == "links":
			self._render_links(screen, height, width)
		else:
			self._render_table(screen, height, width, rows)
		caret = None
		if self.confirm_exit:
			# One row, drawn whole at any width the console accepts.
			screen.addnstr(height - 1, 0, "Exit? y/N", width - 1)
		elif self.batch is not None:
			caret = self._render_batch(screen, height, width)
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
			"PHASE": phase_cell(row["status"], row["phase"]),
			"CLS": compact_classification(row["classification"]),
			# W36: conversation volume and MY directed load, combined
			# compactly here only — the canonical fields stay separate.
			"MSG/MY": f"{row['message_count']}"
			          f"/{row['my_pending_obligations']}",
			"READY": "yes" if row["ready"] else "no",
			"CURRENT": row["current"]["endpoint"] if row["current"]
			else "-",
			"NEXT": row["next"]["endpoint"] if row["next"] else "-",
			"NEW": str(row["new"]),
		}

	def _render_table(self, screen, height, width, rows) -> None:
		if not layout_fits(width):
			columns = visible_columns(width)
			need = sum(w for _n, w in columns) + len(columns) + \
				MIN_TITLE + 1
			# The explicit too-narrow REFUSAL (ruled): identities are
			# never truncated into ambiguity to fake a fit.
			screen.addnstr(1, 0,
			               f"(terminal too narrow: need {need} cells)",
			               width - 1)
			return
		columns = visible_columns(width)
		fixed = sum(w for _n, w in columns) + len(columns)
		title_width = max(MIN_TITLE, width - fixed - 1)
		# Trial finding 26de18dd-W2: headers draw initial-capital LABELS
		# (Title, St, Phase, ...); the canonical projection fields and
		# the internal responsive-column identifiers stay unchanged.
		header = "Title".ljust(title_width)
		for name, col_width in columns:
			label = HEADER_LABELS.get(name, name.capitalize())
			header += " " + label.ljust(col_width)
		screen.addnstr(1, 0, header, width - 1, curses.A_UNDERLINE)
		visible, hidden = self.visible_rows(rows)
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
		budget = max(1, (height - 4) if hidden else (height - 3))
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
			line = title[:title_width].ljust(title_width)
			cells = self._row_cells(row)
			for name, col_width in columns:
				line += " " + cells[name][:col_width].ljust(col_width)
			attribute = curses.A_REVERSE \
				if start + offset == self.cursor else 0
			screen.addnstr(2 + offset, 0, line, width - 1, attribute)
			if hot_work(row):
				# W84: the slow blink marks ONLY the phase/status cell
				# of a hot row — title, identifiers, counters, routing
				# and selection stay steady, and the ordinary textual
				# state remains when a terminal ignores blink. At
				# widths where the PHASE column is dropped there is
				# simply no cell to animate.
				x = title_width
				for name, col_width in columns:
					x += 1
					if name == "PHASE":
						if x < width - 1:
							screen.addnstr(
								2 + offset, x,
								cells["PHASE"][:col_width]
								.ljust(col_width),
								min(col_width, width - 1 - x),
								attribute | curses.A_BLINK)
						break
					x += col_width
		footer_row = 2 + min(len(visible) - start, budget)
		if hidden and footer_row <= height - 2:
			screen.addnstr(footer_row, 0,
			               f"({hidden} closed hidden — z shows)",
			               width - 1)
		if not visible and not hidden:
			screen.addnstr(2, 0, "(no work here)", width - 1)
		if height - 2 > footer_row:
			screen.addnstr(
				height - 2, 0,
				"Enter details · u unfold · Esc back · z closed · "
				"b links · : command · q quit", width - 1)

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
			endpoint = (entry["current"]["endpoint"]
			            if entry["current"] else "-")
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
		duplicate/follow-up identity, and the transitions the projection
		DECLARES for this viewer — a human never discovers authority by
		attempting invisible operations."""
		facts = []
		if detail["status"] == "closed":
			facts.append(f"closed {detail['outcome']} — "
			             f"{detail['rationale']}")
		# finding-active-work-claim: WHO is executing is a canonical
		# authority value, never inferred from route membership.
		if detail.get("active") is not None:
			facts.append(f"active: {detail['active']['team']}."
			             f"{detail['active']['member']}")
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
		if detail["available_transitions"]:
			facts.append("can: " +
			             " ".join(detail["available_transitions"]))
		return facts

	def _detail_header(self, detail: dict) -> str:
		current = detail["current"]["endpoint"] if detail["current"] \
			else "-"
		planned = detail["next"]["endpoint"] if detail["next"] else "-"
		# W12 (ruled): the EXACT canonical Work id leads the header —
		# first on the line so no narrow width ever clips it, straight
		# from the selected Work's canonical detail (never a title
		# inference). Every command-bar operation can be typed from it.
		line = (f"{detail['id']} [{detail['status']}"
		        f"/{phase_cell(detail['status'], detail['phase'])}"
		        f"/{compact_classification(detail['classification'])}] "
		        f"current {current}  next {planned}  new {detail['new']}")
		waiting = detail.get("waiting_on")
		if waiting is not None:
			line += f"  wait:{waiting['type']}"
			if waiting["obligation"] is not None:
				line += f"#{waiting['obligation']}"
		return line

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
		if detail["rounds"]:
			latest = detail["rounds"][-1]
			flags = "due" if latest["due"] else latest["status"]
			line = (f"R{latest['round']} {latest['candidate']} "
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

		rows = self.thread_rows()
		if self.disc_cursor is None:
			self._thread_autoselect()
			rows = self.thread_rows()
		if not rows:
			screen.addnstr(offset_row, 0, "(no threads)", width - 1)
			self.viewed_thread = None
			self.viewed_last_seq = None
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
			screen.addnstr(offset_row + 1 + offset, 0,
			               f"  T{row['ordinal']} {row['subject']} "
			               f"new:{row['new']} {row['id']}",
			               width - 1, attribute)
		msgs_top = offset_row + 1 + min(len(rows) - start, list_budget)

		# The Messages pane for the selected thread only.
		budget = max(1, height - 3 - msgs_top)
		snapshot = self._cached(
			("thread", selected["id"], self.thread_after,
			 max(1, budget)),
			lambda: projection.thread(
				self.store, selected["id"], viewer_team=self.team,
				viewer_member=self.member, after=self.thread_after,
				limit=max(1, budget)))
		messages = snapshot["messages"]
		if self.thread_skip and self.thread_skip_width != width:
			self.thread_skip = 0
		self.thread_skip_width = width
		marker = "»" if self.focus == "msgs" else " "
		screen.addnstr(msgs_top, 0,
		               f"{marker}Msgs — {snapshot['subject']}",
		               width - 1,
		               curses.A_BOLD if self.focus == "msgs" else 0)
		page = paint_messages(screen, msgs_top + 1, budget - 1, width,
		                      messages, skip=self.thread_skip)
		self.viewed_last_seq = page["painted_last"]
		self.viewed_next_skip = page["next_skip"]
		# W71: n acts only while MORE exists — the disclosed more-state
		# and the control agree; the last page never pages into an
		# empty screen.
		self.viewed_has_more = (page["next_skip"] is not None or
		                        page["more_below"] or
		                        snapshot["next_after"] is not None or
		                        len(messages) == max(1, budget))
		if not messages:
			screen.addnstr(msgs_top + 1, 0,
			               "(no messages on this page)", width - 1)
		# Operator-facing more/page state + the advertised controls
		# (ruled: paged surfaces disclose their controls; Ctrl-W is the
		# pane convention; the seen action stays discoverable).
		more_state = ""
		if page["next_skip"] is not None or page["more_below"] or \
				(messages and len(messages) == max(1, budget)):
			more_state = "more below — n next · p first · "
		elif self.thread_after:
			more_state = "earlier pages — p first · "
		screen.addnstr(
			height - 2, 0,
			f"{more_state}Ctrl-W panes · j/k select · "
			f"s mark shown seen · Esc back", width - 1)

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
			# R1 (round 2): every buffer MUTATION makes the previous
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

	def _command_key(self, key: int) -> None:
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
			self.execute(line)
		elif key == 27:
			self.command = None
		elif key in (8, 127, curses.KEY_BACKSPACE):
			self.command = self.command[:-1]
		elif 32 <= key <= 126:
			self.command += chr(key)

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
			self.thread_after = 0
			self.thread_skip = 0
			self.focus = "threads"
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
		"""The detail view's keys. Ctrl-W (23) is the pane-navigation
		prefix (ruled, the Vim split convention): h/k/up focus Threads,
		j/l/down focus Msgs, w or a second Ctrl-W cycles."""
		if self.ctrl_w_pending:
			self.ctrl_w_pending = False
			if key in (ord("h"), ord("k"), curses.KEY_UP,
			           curses.KEY_LEFT):
				self.focus = "threads"
			elif key in (ord("j"), ord("l"), curses.KEY_DOWN,
			             curses.KEY_RIGHT):
				self.focus = "msgs"
			elif key in (ord("w"), 23):
				self.focus = "msgs" if self.focus == "threads" \
					else "threads"
			return True
		if key == 23:
			self.ctrl_w_pending = True
			return True
		if key in (27, curses.KEY_LEFT):
			self.mode = "table"
			return True
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
				self.thread_after = 0
				self.thread_skip = 0
			elif key in (curses.KEY_UP, ord("k")):
				if self.disc_cursor > 0:
					self.disc_cursor -= 1
				self.thread_after = 0
				self.thread_skip = 0
			elif key == ord("n") and self.disc_next is not None:
				self.disc_after = self.disc_next
				self.disc_cursor = 0
				self.thread_after = 0
				self.thread_skip = 0
			elif key == ord("p"):
				self.disc_after = 0
				self.disc_cursor = 0
				self.thread_after = 0
				self.thread_skip = 0
			elif key == ord("s"):
				self._mark_shown_seen()
			return True
		# -- the Msgs pane -------------------------------------------------
		if key == ord("n"):
			# R1: an unfinished oversized block continues first; only a
			# finished page with MORE below advances the message cursor.
			if getattr(self, "viewed_next_skip", None) is not None:
				self.thread_skip = self.viewed_next_skip
			elif self.viewed_last_seq is not None and \
					getattr(self, "viewed_has_more", False):
				self.thread_after = self.viewed_last_seq
				self.thread_skip = 0
		elif key == ord("p"):
			self.thread_after = 0
			self.thread_skip = 0
		elif key == ord("s"):
			self._mark_shown_seen()
		return True

	def _mark_shown_seen(self) -> None:
		"""The EXPLICIT seen transition — the one writer, by ruling —
		scoped to the DISPLAYED thread, bounded by the PAINTED page
		(R70): a message committed after paint stays New; an
		already-seen no-op schedules nothing (R7)."""
		if self.viewed_thread is None or self.viewed_last_seq is None:
			return
		result = transitions.seen_thread(
			self.store, self.viewed_thread, team=self.team,
			member=self.member, up_to_seq=self.viewed_last_seq)
		if result["advanced"]:
			self.schedule_refresh()
		self.status = (f"seen up to #{result['cursor']}"
		               if result["advanced"] else "already seen")


def run(screen, store: Authority, viewer_team: str, viewer_member: str,
        config_path: str | None = None, refresh: float = 2.0) -> None:
	"""W5: `refresh` seconds (default 2, positive, configurable via
	`tui refresh=`) is the ONE background trigger for fresh canonical
	reads — getch times out, the cache drops, the screen repaints.
	Ordinary keystrokes operate on the cached projection."""
	import time
	curses.curs_set(0)
	console = Console(store, viewer_team, viewer_member,
	                  config_path=config_path)
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
		if not console.handle(key):
			return
		console.render(screen)


# SUPERSEDED (C3): the module-level entry that opened a raw authority path is
# gone. The ONLY launch is `baton --config ... --participant ... tui`,
# which opens through the bound lifecycle and validates the participant
# before curses claims the screen — the v10 console's refuse-first lesson,
# now enforced by the configuration boundary rather than by this module.
