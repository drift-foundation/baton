"""Curses rendering of the canonical projection — B1.

THE PINNED MODEL, exactly: open on a borderless fixed-column table of the
viewer's top-level Work; Enter drills into a table of immediate children, the
same interaction at every depth; a persistent breadcrumb names the drilled
path; opening a row's discussion is a view within the current Work, not a new
navigation model. Column priorities, sorting and keys are prototype-grade by
ruling and carry no semantics of their own.

EVERY VALUE ON SCREEN comes from one `projection` call per repaint. The
renderer never computes `New`, never sums children, never decides readiness —
it formats. The parity suite (B2) holds the two surfaces together by driving
the same fixture through both.
"""

from __future__ import annotations

import curses

from baton_work.authority import Authority
from baton_work import projection
from baton_work import transitions

# Fixed column budget (borderless; alignment is the separator). The title
# column absorbs the remainder and is the ONLY thing ever truncated — an
# identity is never abbreviated (6/6 rule makes them fit by construction).
COLUMNS = (("ST", 6), ("PHASE", 5), ("CLS", 5), ("READY", 5),
           ("CURRENT", 13), ("NEXT", 13), ("NEW", 4))

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


class Console:
	def __init__(self, store: Authority, viewer_team: str, viewer_member: str):
		self.store = store
		self.team = viewer_team
		self.member = viewer_member
		self.path: list[str] = []        # drilled Work ids, root-first
		self.cursor = 0
		self.mode = "table"              # or "discussion"
		self.status = ""

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
		else:
			self._render_table(screen, height, width, rows)
		if self.status:
			screen.addnstr(height - 1, 0, self.status, width - 1)
		screen.refresh()

	def _render_table(self, screen, height, width, rows) -> None:
		fixed = sum(w for _n, w in COLUMNS) + len(COLUMNS)
		title_width = max(10, width - fixed - 1)
		header = "TITLE".ljust(title_width)
		for name, col_width in COLUMNS:
			header += " " + name.ljust(col_width)
		screen.addnstr(1, 0, header, width - 1, curses.A_UNDERLINE)
		for index, row in enumerate(rows[:height - 3]):
			line = row["title"][:title_width].ljust(title_width)
			current = row["current"]["endpoint"] if row["current"] else "-"
			planned = row["next"]["endpoint"] if row["next"] else "-"
			values = (row["status"][:6],
			          compact_phase(row["phase"]),
			          compact_classification(row["classification"]),
			          "yes" if row["ready"] else "no",
			          current, planned, str(row["new"]))
			for (name, col_width), value in zip(COLUMNS, values):
				line += " " + str(value)[:col_width].ljust(col_width)
			attribute = curses.A_REVERSE if index == self.cursor else 0
			screen.addnstr(2 + index, 0, line, width - 1, attribute)
		if not rows:
			screen.addnstr(2, 0, "(no work here)", width - 1)

	def _render_discussion(self, screen, height, width) -> None:
		work_id = self.path[-1]
		detail = projection.detail(self.store, work_id,
		                           viewer_team=self.team,
		                           viewer_member=self.member)
		current = detail["current"]["endpoint"] if detail["current"] else "-"
		planned = detail["next"]["endpoint"] if detail["next"] else "-"
		line = (f"[{detail['status']}/{compact_phase(detail['phase'])}"
		        f"/{compact_classification(detail['classification'])}] "
		        f"current {current}  next {planned}  new {detail['new']}")
		screen.addnstr(1, 0, line, width - 1)
		# WS-6 R90: the human sees the SAME portable facts the JSON
		# client sees — the effective binding as root:path plus its
		# revision, straight from the canonical projection; no resolver,
		# no filesystem, no probe.
		binding = detail.get("binding")
		if binding is not None:
			screen.addnstr(
				2, 0,
				f"binding {binding['root']}:{binding['path']} "
				f"r{binding['revision']}", width - 1)
		# Bounded WS-2 parity: the latest round, both axes from the same
		# canonical projection — due/pending/reported/withdrawn are
		# distinguished, and the raw observation is shown separately from
		# the reviewer's assessment (e.g. "failed/rejected").
		offset_row = 2 if detail.get("binding") is None else 3
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
		# Slice B: the Work has a discussion SET (R54); the bounded view
		# renders the FIRST related discussion's thread — one
		# conversation, never several merged into a false timeline.
		related = projection.work_discussions(
			self.store, work_id, viewer_team=self.team,
			viewer_member=self.member, limit=1)["rows"]
		self.viewed_discussion = related[0]["id"] if related else None
		messages = []
		self.viewed_last_seq = None
		if self.viewed_discussion is not None:
			snapshot = projection.thread(
				self.store, self.viewed_discussion,
				viewer_team=self.team,
				viewer_member=self.member)
			messages = snapshot["messages"]
			# R70/R72: the mark the user can make is bounded by what
			# was PAINTED — the last message actually returned by this
			# page, never the discussion-wide last_seq and never a
			# later global sequence read at keypress time. An empty
			# page leaves nothing markable.
			self.viewed_last_seq = messages[-1]["seq"] \
				if messages else None
		start = max(0, len(messages) - (height - 2 - offset_row))
		for offset, message in enumerate(messages[start:]):
			text = (f"#{message['seq']} {message['author_team']}."
			        f"{message['author']}: {message['body']}")
			# R90: ordered references render as the same portable
			# root:path facts the projection carries.
			for reference in message.get("references", []):
				text += f" [{reference['root']}:{reference['path']}]"
			screen.addnstr(offset_row + offset, 0, text, width - 1)

	# -- interaction ----------------------------------------------------------

	def handle(self, key: int) -> bool:
		"""One key. Returns False to exit."""
		self.status = ""
		rows = self.rows() if self.mode == "table" else []
		if key in (ord("q"),):
			return False
		if self.mode == "discussion":
			if key in (27, curses.KEY_LEFT, ord("i")):
				self.mode = "table"
			elif key == ord("s") and \
					getattr(self, "viewed_discussion", None) is not None \
					and getattr(self, "viewed_last_seq", None) is not None:
				# The EXPLICIT seen transition — the one writer, by
				# ruling — scoped to the DISPLAYED discussion and
				# bounded by the PAINTED snapshot (R70): a message
				# committed after paint stays New.
				result = transitions.seen_discussion(
					self.store, self.viewed_discussion, team=self.team,
					member=self.member,
					up_to_seq=self.viewed_last_seq)
				self.status = (f"seen up to #{result['cursor']}"
				               if result["advanced"] else "already seen")
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
		elif key in (27, curses.KEY_LEFT) and self.path:
			self.path.pop()
			self.cursor = 0
		return True


def run(screen, store: Authority, viewer_team: str, viewer_member: str) -> None:
	curses.curs_set(0)
	console = Console(store, viewer_team, viewer_member)
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
