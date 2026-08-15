"""Curses rendering of the canonical projection — B1.

THE PINNED MODEL, exactly: open on a borderless fixed-column table of the
viewer's top-level Work; Enter drills into a table of immediate children, the
same interaction at every depth; a persistent breadcrumb names the drilled
path; `o` opens the focused Work view (facts, rounds, and the selectable
discussion set); Enter there opens one discussion's paged thread — never
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

from baton_work.authority import Authority, WorkError
from baton_work import projection
from baton_work import transitions

# Fixed column budget (borderless; alignment is the separator). The title
# column absorbs the remainder and is the ONLY thing ever truncated — an
# identity is never abbreviated (6/6 rule makes them fit by construction).
# Gate B: the set is exactly the canonical projection's row fields — the
# renderer formats them and never aggregates or invents a value.
COLUMNS = (("ST", 6), ("PHASE", 5), ("CLS", 5), ("PROG", 5), ("DEP", 3),
           ("READY", 5), ("CURRENT", 13), ("NEXT", 13), ("NEW", 4))

# Responsive omission (prototype-grade presentation under the ruling): at
# narrow widths whole low-priority columns are OMITTED, never squeezed into
# ambiguity — identities and counters are drawn whole or not at all. The
# title keeps a minimum working width; below the minimum the table REFUSES
# with an explicit too-narrow line instead of truncating identities.
DROP_ORDER = ("CLS", "DEP", "PROG", "PHASE", "READY", "NEXT")
MIN_TITLE = 10

# One bounded page of a Work's discussion SET (prototype size): `n` pages
# forward through the canonical continuation cursor, `p` returns to the
# start — every discussion is reachable, none is silently truncated.
DISC_PAGE = 10


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
CLASSIFICATION_COMPACT = {"unknown": "unkwn", "suspected-defect": "suspt",
                          "confirmed-defect": "cnfrm",
                          "limitation": "limit", "duplicate": "dupe",
                          "design-choice": "desgn", "rejection": "rejct"}


def compact_phase(value: str) -> str:
	if value not in PHASE_COMPACT:
		raise ValueError(f"phase {value!r} has no ruled compact rendering")
	return PHASE_COMPACT[value]


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


def progress_cell(row: dict) -> str:
	progress = row["progress"]
	if not progress["children"]:
		return "-"
	return f"{progress['closed']}/{progress['children']}"


class Console:
	def __init__(self, store: Authority, viewer_team: str,
	             viewer_member: str, config_path: str | None = None):
		self.store = store
		self.team = viewer_team
		self.member = viewer_member
		self.config_path = config_path
		self.path: list[str] = []        # drilled Work ids, root-first
		self.cursor = 0
		self.mode = "table"       # table / links / discussion / thread
		self.status = ""
		# Resolved branches are COLLAPSED by default (ruled): closed rows
		# leave the table, an explicit count names what is hidden, and a
		# key reveals them — nothing is ever silently absent.
		self.show_closed = False
		self.links_work: str | None = None
		self.links_cursor = 0
		self.disc_cursor = 0
		self.disc_after = 0
		self.disc_next: int | None = None
		self.viewed_discussion: str | None = None
		self.viewed_last_seq: int | None = None
		self.thread_after = 0
		self.command: str | None = None  # the `:` command-bar buffer

	# -- data, one projection call per need -----------------------------------

	def view(self) -> tuple[list[dict], dict]:
		"""(rows, summary) — at top level BOTH come from the ONE `home`
		projection, so the always-visible parked count and the table are
		the same snapshot (WS-1 review R3: never two calls that can sample
		different sequences)."""
		if not self.path:
			top = projection.home(self.store, viewer_team=self.team,
			                      viewer_member=self.member)
			return top["rows"], top["summary"]
		return (projection.children(self.store, self.path[-1],
		                            viewer_team=self.team,
		                            viewer_member=self.member),
		        projection.team_summary(self.store, viewer_team=self.team))

	def rows(self) -> list[dict]:
		return self.view()[0]

	def visible_rows(self, rows: list[dict]) -> tuple[list[dict], int]:
		"""(rows to draw, hidden closed count) — the collapse is pure
		presentation over the projection's own status values."""
		if self.show_closed:
			return rows, 0
		visible = [row for row in rows if row["status"] == "open"]
		return visible, len(rows) - len(visible)

	def discussion_rows(self) -> list[dict]:
		"""ONE bounded page of the focused Work's discussion SET from the
		paged canonical read — never merged, each row selectable, the
		continuation cursor kept so `n` reaches every later page."""
		page = projection.work_discussions(
			self.store, self.path[-1], viewer_team=self.team,
			viewer_member=self.member, after=self.disc_after,
			limit=DISC_PAGE)
		self.disc_next = page["next_after"]
		return page["rows"]

	def breadcrumb_text(self, summary: dict) -> str:
		# Actionable state on the same line, FROM the projection: the count
		# a member acts on is never derived here (parity holds it equal to
		# the JSON obligations list).
		pending = len(projection.obligations(self.store,
		                                     viewer_team=self.team))
		# The parked count is ALWAYS visible (WS-1 ruling): parked work has
		# no wake condition, so it stays in the operators' faces.
		suffix = (f"  [oblig:{pending}] [park:{summary['parked']}]"
		          f" [due:{summary['due']}]")
		if not self.path:
			return f"{self.team}.{self.member} — top-level work{suffix}"
		trail = projection.breadcrumb(self.store, self.path[-1])
		return " > ".join(entry["title"] for entry in trail) + suffix

	# -- rendering ------------------------------------------------------------

	def render(self, screen) -> None:
		screen.erase()
		height, width = screen.getmaxyx()
		rows, summary = (self.view() if self.mode == "table"
		                 else ([], projection.team_summary(
		                     self.store, viewer_team=self.team)))
		screen.addnstr(0, 0, self.breadcrumb_text(summary), width - 1,
		               curses.A_BOLD)
		if self.mode == "discussion":
			self._render_discussion(screen, height, width)
		elif self.mode == "thread":
			self._render_thread(screen, height, width)
		elif self.mode == "links":
			self._render_links(screen, height, width)
		else:
			self._render_table(screen, height, width, rows)
		if self.command is not None:
			screen.addnstr(height - 1, 0, ":" + self.command, width - 1)
		elif self.status:
			screen.addnstr(height - 1, 0, self.status, width - 1)
		screen.refresh()

	def _row_cells(self, row: dict) -> dict:
		"""Every drawable cell for one projection row — canonical values
		through the closed compact maps, nothing computed here."""
		return {
			"ST": status_cell(row),
			"PHASE": compact_phase(row["phase"]),
			"CLS": compact_classification(row["classification"]),
			"PROG": progress_cell(row),
			"DEP": str(row["dep"]),
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
		header = "TITLE".ljust(title_width)
		for name, col_width in columns:
			header += " " + name.ljust(col_width)
		screen.addnstr(1, 0, header, width - 1, curses.A_UNDERLINE)
		visible, hidden = self.visible_rows(rows)
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
			line = row["title"][:title_width].ljust(title_width)
			cells = self._row_cells(row)
			for name, col_width in columns:
				line += " " + cells[name][:col_width].ljust(col_width)
			attribute = curses.A_REVERSE \
				if start + offset == self.cursor else 0
			screen.addnstr(2 + offset, 0, line, width - 1, attribute)
		footer_row = 2 + min(len(visible) - start, budget)
		if hidden and footer_row <= height - 2:
			screen.addnstr(footer_row, 0,
			               f"({hidden} closed hidden — z shows)",
			               width - 1)
		if not visible and not hidden:
			screen.addnstr(2, 0, "(no work here)", width - 1)

	def _links_rows(self) -> list[tuple[str, str]]:
		"""(work id, drawn line) pairs — every fact the `links`
		projection's far-row summary, with the STABLE id shown so the
		deliberate cross-team drill-through has a visible anchor."""
		view = projection.links(self.store, self.links_work)
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
		line = (f"[{detail['status']}/{compact_phase(detail['phase'])}"
		        f"/{compact_classification(detail['classification'])}] "
		        f"current {current}  next {planned}  new {detail['new']}")
		waiting = detail.get("waiting_on")
		if waiting is not None:
			line += f"  wait:{waiting['type']}"
			if waiting["obligation"] is not None:
				line += f"#{waiting['obligation']}"
		return line

	def _render_discussion(self, screen, height, width) -> None:
		"""The FOCUSED Work view: header, facts, the latest round, and
		the selectable discussion set — Enter opens one discussion's
		thread; nothing is merged into a false timeline."""
		work_id = self.path[-1]
		detail = projection.detail(self.store, work_id,
		                           viewer_team=self.team,
		                           viewer_member=self.member)
		screen.addnstr(1, 0, self._detail_header(detail), width - 1)
		facts = self._facts(detail)
		for offset, text in enumerate(facts):
			screen.addnstr(2 + offset, 0, text, width - 1)
		offset_row = 2 + len(facts)
		# Bounded WS-2 parity: the latest round, both axes from the same
		# canonical projection — due/pending/reported/withdrawn are
		# distinguished, and the raw observation is shown separately from
		# the reviewer's assessment (e.g. "failed/rejected").
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
		rows = self.discussion_rows()
		if not rows:
			screen.addnstr(offset_row, 0, "(no discussions)", width - 1)
			return
		paging = f" after #{self.disc_after}" if self.disc_after else ""
		more = "  (n: more)" if self.disc_next is not None else ""
		screen.addnstr(offset_row, 0,
		               f"discussions ({detail['discussion_count']})"
		               f"{paging}:{more}",
		               width - 1)
		budget = max(1, height - 2 - (offset_row + 1))
		start = max(0, min(self.disc_cursor - budget + 1,
		                   len(rows) - budget))
		for offset, row in enumerate(rows[start:start + budget]):
			attribute = curses.A_REVERSE \
				if start + offset == self.disc_cursor else 0
			screen.addnstr(offset_row + 1 + offset, 0,
			               f"  {row['id']} new:{row['new']} "
			               f"last:#{row['last_seq'] or 0}",
			               width - 1, attribute)

	def _render_thread(self, screen, height, width) -> None:
		"""ONE discussion's messages, PAGED through the canonical thread
		read — `n` pages forward from the last painted message, `p`
		returns to the start, `s` marks seen bounded by the painted page
		(R70/R72)."""
		snapshot = projection.thread(
			self.store, self.viewed_discussion, viewer_team=self.team,
			viewer_member=self.member, after=self.thread_after,
			limit=max(1, height - 4))
		messages = snapshot["messages"]
		screen.addnstr(1, 0,
		               f"discussion {self.viewed_discussion} "
		               f"after #{self.thread_after} "
		               f"({len(messages)} shown)", width - 1)
		self.viewed_last_seq = messages[-1]["seq"] if messages else None
		for offset, message in enumerate(messages):
			text = (f"#{message['seq']} {message['author_team']}."
			        f"{message['author']}: {message['body']}")
			# R90: ordered references render as the same portable
			# root:path facts the projection carries.
			for reference in message.get("references", []):
				text += f" [{reference['root']}:{reference['path']}]"
			screen.addnstr(2 + offset, 0, text, width - 1)
		if not messages:
			screen.addnstr(2, 0, "(no messages on this page)", width - 1)

	# -- the command bar: the ONE public surface, in place ---------------------

	def execute(self, line: str) -> None:
		"""Feed the typed command to the SAME public CLI entry the JSON
		agent uses — same config, same participant, same grammar, same
		refusals. The console adds nothing and hides nothing."""
		import contextlib
		import io
		import json as _json

		from baton_work import cli as _cli
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
		# The console carries ONE validated participant and ONE bound
		# configuration (C3). Re-entering either global in the command
		# bar would be identity by assertion — refused, with the
		# reason, INCLUDING every argparse long-option abbreviation the
		# parser would accept for them.
		for token in argv:
			flag = token.split("=", 1)[0]
			guarded = any(
				len(flag) > 2 and fixed.startswith(flag)
				for fixed in ("--participant", "--config"))
			if guarded and flag.startswith("--"):
				self.status = (
					f"{flag} names the session's fixed global "
					f"participant/configuration; the command bar "
					f"never re-enters them")
				return
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
		if code == 0:
			brief = "ok"
			try:
				result = _json.loads(out.getvalue())["result"]
			except (ValueError, KeyError):
				result = None
			if isinstance(result, dict):
				for key in ("work_id", "seq", "revision", "generation"):
					if key in result:
						brief += f" {key}={result[key]}"
			self.status = brief
		else:
			try:
				self.status = _json.loads(err.getvalue())["error"][:200]
			except ValueError:
				self.status = (err.getvalue() or
				               "refused").strip()[:200]

	def _command_key(self, key: int) -> None:
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
		self.status = ""
		if key == ord(":"):
			self.command = ""
			return True
		rows, _hidden = (self.visible_rows(self.rows())
		                 if self.mode == "table" else ([], 0))
		if key in (ord("q"),):
			return False
		if self.mode == "links":
			entries = self._links_rows()
			if key in (curses.KEY_DOWN, ord("j")):
				self.links_cursor = min(self.links_cursor + 1,
				                        max(0, len(entries) - 1))
			elif key in (curses.KEY_UP, ord("k")):
				self.links_cursor = max(0, self.links_cursor - 1)
			elif key in (curses.KEY_ENTER, 10, 13) and entries:
				# The deliberate cross-team drill-through (ruled): the
				# far Work becomes the drilled position; the breadcrumb
				# reconstructs its real ancestry.
				self.path = [entries[self.links_cursor][0]]
				self.cursor = 0
				self.mode = "table"
				self.links_work = None
			elif key in (27, curses.KEY_LEFT, ord("i")):
				self.mode = "table"
				self.links_work = None
			return True
		if self.mode == "thread":
			if key in (27, curses.KEY_LEFT, ord("i")):
				self.mode = "discussion"
			elif key == ord("n") and self.viewed_last_seq is not None:
				self.thread_after = self.viewed_last_seq
			elif key == ord("p"):
				self.thread_after = 0
			elif key == ord("s") and \
					self.viewed_discussion is not None and \
					self.viewed_last_seq is not None:
				# The EXPLICIT seen transition — the one writer, by
				# ruling — scoped to the DISPLAYED discussion and
				# bounded by the PAINTED page (R70): a message
				# committed after paint stays New.
				result = transitions.seen_discussion(
					self.store, self.viewed_discussion, team=self.team,
					member=self.member,
					up_to_seq=self.viewed_last_seq)
				self.status = (f"seen up to #{result['cursor']}"
				               if result["advanced"] else "already seen")
			return True
		if self.mode == "discussion":
			entries = self.discussion_rows()
			if key == ord("n") and self.disc_next is not None:
				self.disc_after = self.disc_next
				self.disc_cursor = 0
				return True
			if key == ord("p"):
				self.disc_after = 0
				self.disc_cursor = 0
				return True
			if key in (curses.KEY_DOWN, ord("j")):
				self.disc_cursor = min(self.disc_cursor + 1,
				                       max(0, len(entries) - 1))
			elif key in (curses.KEY_UP, ord("k")):
				self.disc_cursor = max(0, self.disc_cursor - 1)
			elif key in (curses.KEY_ENTER, 10, 13) and entries:
				self.viewed_discussion = \
					entries[self.disc_cursor]["id"]
				self.thread_after = 0
				self.viewed_last_seq = None
				self.mode = "thread"
			elif key in (27, curses.KEY_LEFT, ord("i")):
				self.mode = "table"
			return True
		if key in (curses.KEY_DOWN, ord("j")):
			self.cursor = min(self.cursor + 1, max(0, len(rows) - 1))
		elif key in (curses.KEY_UP, ord("k")):
			self.cursor = max(0, self.cursor - 1)
		elif key in (curses.KEY_ENTER, 10, 13) and rows:
			self.path.append(rows[self.cursor]["id"])
			self.cursor = 0
		elif key == ord("o") and self.path:
			self.mode = "discussion"
			self.disc_cursor = 0
			self.disc_after = 0
		elif key == ord("b") and rows:
			# Blocking/dependent neighbors on demand for the row under
			# the cursor — selectable, drill-through on Enter.
			self.links_work = rows[self.cursor]["id"]
			self.links_cursor = 0
			self.mode = "links"
		elif key == ord("z"):
			# Reveal/collapse resolved rows; the cursor stays inside the
			# newly visible list.
			self.show_closed = not self.show_closed
			shown, _hidden = self.visible_rows(self.rows())
			self.cursor = min(self.cursor, max(0, len(shown) - 1))
		elif key in (27, curses.KEY_LEFT) and self.path:
			self.path.pop()
			self.cursor = 0
		return True


def run(screen, store: Authority, viewer_team: str, viewer_member: str,
        config_path: str | None = None) -> None:
	curses.curs_set(0)
	console = Console(store, viewer_team, viewer_member,
	                  config_path=config_path)
	console.render(screen)
	while True:
		key = screen.getch()
		if not console.handle(key):
			return
		console.render(screen)


# SUPERSEDED (C3): the module-level entry that opened a raw authority path is
# gone. The ONLY launch is `baton-work --config ... --participant ... tui`,
# which opens through the bound lifecycle and validates the participant
# before curses claims the screen — the v10 console's refuse-first lesson,
# now enforced by the configuration boundary rather than by this module.
