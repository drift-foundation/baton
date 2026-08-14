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

from baton_work.authority import Authority, WorkError
from baton_work import projection
from baton_work import transitions

# Fixed column budget (borderless; alignment is the separator). The title
# column absorbs the remainder and is the ONLY thing ever truncated — an
# identity is never abbreviated (6/6 rule makes them fit by construction).
COLUMNS = (("ST", 6), ("READY", 5), ("CURRENT", 13), ("NEXT", 13), ("NEW", 4))


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

	def rows(self) -> list[dict]:
		if not self.path:
			return projection.home(self.store, viewer_team=self.team,
			                       viewer_member=self.member)
		return projection.children(self.store, self.path[-1],
		                           viewer_team=self.team,
		                           viewer_member=self.member)

	def breadcrumb_text(self) -> str:
		# Actionable state on the same line, FROM the projection: the count
		# a member acts on is never derived here (parity holds it equal to
		# the JSON obligations list).
		pending = len(projection.obligations(self.store,
		                                     viewer_team=self.team))
		suffix = f"  [oblig:{pending}]"
		if not self.path:
			return f"{self.team}.{self.member} — top-level work{suffix}"
		trail = projection.breadcrumb(self.store, self.path[-1])
		return " > ".join(entry["title"] for entry in trail) + suffix

	# -- rendering ------------------------------------------------------------

	def render(self, screen) -> None:
		screen.erase()
		height, width = screen.getmaxyx()
		screen.addnstr(0, 0, self.breadcrumb_text(), width - 1,
		               curses.A_BOLD)
		if self.mode == "discussion":
			self._render_discussion(screen, height, width)
		else:
			self._render_table(screen, height, width)
		if self.status:
			screen.addnstr(height - 1, 0, self.status, width - 1)
		screen.refresh()

	def _render_table(self, screen, height, width) -> None:
		fixed = sum(w for _n, w in COLUMNS) + len(COLUMNS)
		title_width = max(10, width - fixed - 1)
		header = "TITLE".ljust(title_width)
		for name, col_width in COLUMNS:
			header += " " + name.ljust(col_width)
		screen.addnstr(1, 0, header, width - 1, curses.A_UNDERLINE)
		rows = self.rows()
		for index, row in enumerate(rows[:height - 3]):
			line = row["title"][:title_width].ljust(title_width)
			values = (row["status"][:6],
			          "yes" if row["ready"] else "no",
			          (row["current"] or "-"),
			          (row["next"] or "-"),
			          str(row["new"]))
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
		line = (f"[{detail['status']}] current {detail['current'] or '-'}"
		        f"  next {detail['next'] or '-'}  new {detail['new']}")
		screen.addnstr(1, 0, line, width - 1)
		messages = projection.discussion(self.store, work_id)
		start = max(0, len(messages) - (height - 4))
		for offset, message in enumerate(messages[start:]):
			text = (f"#{message['seq']} {message['author_team']}."
			        f"{message['author']}: {message['body']}")
			screen.addnstr(2 + offset, 0, text, width - 1)

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
			elif key == ord("s"):
				# The EXPLICIT seen transition — the one writer, by ruling.
				result = transitions.mark_seen(
					self.store, self.path[-1], team=self.team,
					member=self.member, up_to_seq=self.store.last_seq())
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


def main(authority_path: str, viewer: str) -> int:
	team, dot, member = viewer.partition(".")
	if not dot:
		raise WorkError(f"viewer {viewer!r} is not team.member shaped")
	with Authority(authority_path) as store:
		# Refuse before curses takes the screen: a refusal through a claimed
		# drawing surface is a corrupted screen (the v10 console's lesson).
		projection.home(store, viewer_team=team, viewer_member=member)
		curses.wrapper(run, store, team, member)
	return 0
