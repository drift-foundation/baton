"""Console state model: a pure state machine over the core API.

Kept separate from rendering and from curses so the whole interaction is
testable without a terminal. Every transition here is a function of the
previous state plus one keystroke, which is also what makes the safety
properties checkable: "the poll creates no claim" is a statement about this
module, and a test can hold it to that without drawing anything.

The load-bearing distinction, pinned by the contract:

    OBSERVE   the POLL: refresh, and re-previewing the same row
              -> read-only. No claims. No seen receipts. No content.

    COMMIT    selecting an inbound directed row (claim and open),
              Enter on a notice (mark seen and open), reply, close
              -> the actions that take ownership or consume a broadcast.

**Selection is a COMMIT for directed messages** -- Slawomir's ruling, recorded
in FINDING §16. Highlighting one claims and opens it, because scrolling to a
row and then pressing Enter was one ceremony too many. What must never blur is
the other line: the POLL observes and never commits, so mail cannot be claimed
by arriving, and a BROADCAST is never consumed by being looked at.

SUPERSEDED, recorded so it is not restored by someone finding it reasonable:
cursor movement and selection used to be pure observation, and Enter used to
be the only act that took ownership.
"""

from __future__ import annotations

import time

from baton_core import BatonError, notice_delivery

from .drafts import DraftError
from . import drafts as draft_store

MODE_BROWSE = "browse"
MODE_REPLY = "reply"
MODE_COMPOSE = "compose"          # new directed message
MODE_NOTICE = "notice"            # publish a broadcast
MODE_CONFIRM_QUIT = "confirm_quit"
# ONE LINE, and the capital names the safe default. `q` is next to nothing on
# a keyboard and is pressed by reflex; the answer that loses nothing is the
# one a stray Enter should give.
CONFIRM_QUIT_PROMPT = "Exit? y/N"
MODE_PICK_RECIPIENT = "pick_recipient"
# Choosing the TRUST ANCHOR an attachment is named against. Its own mode,
# not a flag on the recipient picker: the two choose different things and
# cancelling one must not look like cancelling the other.
MODE_PICK_ROOT = "pick_root"
# Enter ARMS a send; only `y` publishes. Reached from reply, compose and
# notice alike, and it remembers which one so declining returns to exactly the
# draft and field the human left.
MODE_CONFIRM_SEND = "confirm_send"
# `Discard draft? y/N` -- one status line, default NO. Its own mode rather
# than a flag, so every screen-splitting calculation sees it the way it sees
# the other confirmations.
MODE_CONFIRM_DISCARD = "confirm_discard"
# The modal shortcut list. A VIEW, not status-bar prose: the whole map does not
# fit on one row, and a console whose keys are only discoverable by reading its
# source is a console with one user.
MODE_HELP = "help"

# Which pane the navigation keys drive. PURE UI STATE: focusing writes nothing
# and is not an action target -- the selected/opened item remains the target
# model, and focus deciding what `c` acts on would be the wrong-target bug in
# a third costume.
FOCUS_LIST = "list"
FOCUS_DETAIL = "detail"

# The list pane shows ONE of these at a time. Not a split: the pane is 40% of
# the body already, and halving it would make both lists unreadable to save a
# keystroke.
VIEW_INBOX = "inbox"
VIEW_SENT = "sent"
# There is NO History view. Splitting active from handled made a message vanish
# the moment it was answered; the fix was the unified MESSAGES list, where a
# handled row keeps its place and changes its badge. A second view would put
# that decision back on the screen it was taken off.

# One-letter selection labels. 26 per page, then paged explicitly -- a picker
# that silently truncated would hide participants that exist.
PICKER_LABELS = "abcdefghijklmnopqrstuvwxyz"

# Status severity, shown in the persistent bottom bar. An expected Baton
# failure is an ERROR the human must see, not an exception that takes their
# context down with it; an arrival is INFO that must not steal focus.
SEV_INFO = "info"
SEV_SUCCESS = "success"
SEV_WARNING = "warning"
SEV_ERROR = "error"

# Compose fields, in the order the human fills them.
#
# The attachment is TWO values, not one. `attach_root` is chosen from a picker
# and `attach_path` is typed relative to it, and they stay separate all the way
# to the core call -- collapsing them into `root:path` would put Baton's
# serialization in front of the human, which is the thing the ruling removes.
COMPOSE_FIELDS = ("to", "subject", "attach_path", "body")
# `body` is NOT here. There is no inline body editor: printable text never
# accumulates in a body buffer, so there is no inline-versus-editor merge
# question to get wrong. The body is written externally or not at all.
#
# `attach_root` is not here either, for a different reason: it is CHOSEN, never
# typed, exactly like `to`.
COMPOSE_EDITABLE = ("subject", "attach_path")
# `body` is absent here for the same reason it is absent from COMPOSE_EDITABLE:
# there is no inline body editor ANYWHERE. A notice body is written externally
# or the subject-only shorthand carries the message.
NOTICE_FIELDS = ("subject",)

# The row-type discriminator is `row_type`, NOT `kind`: a message carries its
# own protocol `kind` ("question", "review", ...), and reusing that key meant
# the spread overwrote the discriminator with the sender's value. A row would
# then be whatever kind the sender happened to name.
# HOW LONG A ROW MUST STAY SELECTED before highlighting it takes ownership.
# Ruled at two seconds: long enough to scroll past work you mean to ignore,
# short enough that settling on a message still opens it without a keystroke.
DWELL_SECONDS = 2.0

ROW_MESSAGE = "message"
ROW_NOTICE = "notice"
# A retained draft. NOT authority state: it has no message id, no claim, no
# transitions, and it exists only in this participant's own local file. It
# appears in the same list because that is where the human looks for work they
# owe, and an unfinished message is work they owe themselves.
ROW_DRAFT = "draft"

# The one-line guidance for a row whose claim is resolved. An answered
# conversation is NOT a dead end -- Slawomir's ruling -- so the console says
# what can still be done rather than "read only".
FOLLOW_UP_ANSWERED = "Answered"
FOLLOW_UP_SENT = "Sent"
# What the console says when the editor came back with the same bytes it was
# given. It names the OBSERVATION, not a diagnosis: a successful `:q!` and a
# save with no changes are indistinguishable from here, and both mean the same
# thing to the human.
EDITOR_UNCHANGED = "editor returned no changes; nothing imported"
# What a quick reply IS, said once. Not a key list: the footer owns those.
REPLY_STARTED = "quick reply — the subject line is the message"
# Human-facing name for `responds_to`. The wire field is unchanged; the
# relation is broader than the one claim-resolving reply, so the prose is not.
IN_REFERENCE_TO = "In reference to:"
# What an already-seen notice says. The absence of a write is not enough on
# its own: a reader has to be told the bytes are not coming back, or the row
# looks like one keystroke away from the announcement.
NOTICE_SEEN_STATUS = ("seen — the content is not redelivered (at most once); "
                      "r replies to the author")
# Descriptive kind for a conversational follow-up. NEVER the safety authority:
# claim and disposition records are, and threading derives from `responds_to`.
KIND_FOLLOW_UP = "follow_up"


def _is_displayable_text(part: dict | None) -> bool:
	"""Whether a leaf's DECLARED type is text this terminal can render.

	The same rule `read_selected_external_part` applies to what comes back, so
	the offer and the action cannot disagree -- and it is decided from the
	manifest, which the console already holds, rather than by opening the
	file and finding out."""
	return str((part or {}).get("content_type", "")).startswith("text/")


def _row_order(row: dict) -> tuple:
	"""The TOTAL order a row sorts by: `(created_ts, id)`.

	A total order, not a timestamp: Baton stamps to the second, so two
	messages sent in the same second tie and would come back in whatever order
	SQLite produced. Anything that compares "which came first" -- the sort and
	the same-sender warning -- has to use this one, or the two can disagree
	about the same pair of rows."""
	return (row["created_ts"], row["id"])


def thread_rows(rows: list[dict]) -> list[dict]:
	"""The list in THREAD order, each row carrying its `depth`.

	Slawomir's ruling: a reply is an indented child of the message it answers,
	not a flat sibling. Newest-first put a reply immediately ABOVE its own
	parent, which reads as two unrelated messages that happen to share a
	subject -- and the one place a human looks to see whether something was
	answered is the row of the thing they answered.

	Two orders, and they are deliberately different:

	- THREADS are ordered newest-first by their most recent member, so
	  answering an old message brings the conversation back to the top. By the
	  ROOT's own timestamp instead, a reply you just sent would appear near
	  the bottom of the list -- which is the "I sent it and it vanished"
	  failure that unified MESSAGES exists to fix, wearing a new hat.
	- WITHIN a thread, oldest-first under the parent, because that is the
	  order the conversation happened in and an indented child that precedes
	  its parent is not a child.

	`responds_to` is followed only WITHIN the visible set. A reply whose
	parent has been collected is a root: pretending otherwise would indent it
	under nothing.
	"""
	by_id = {row["id"]: row for row in rows}
	children: dict = {}
	roots: list[dict] = []
	for row in rows:
		parent = row.get("responds_to")
		if parent is not None and parent in by_id and parent != row["id"]:
			children.setdefault(parent, []).append(row)
		else:
			roots.append(row)

	def descendants(row) -> list:
		out = []
		for child in sorted(children.get(row["id"], []), key=_row_order):
			out.append(child)
			out.extend(descendants(child))
		return out

	groups = []
	for root in roots:
		members = [root] + descendants(root)
		# The whole thread sorts by its NEWEST member.
		groups.append((max(_row_order(member) for member in members), root, members))
	groups.sort(key=lambda group: (group[0], group[1]["id"]), reverse=True)

	out: list[dict] = []
	for _, root, members in groups:
		depths = {root["id"]: 0}
		for member in members:
			if member["id"] not in depths:
				parent = member.get("responds_to")
				depths[member["id"]] = depths.get(parent, 0) + 1
			out.append({**member, "depth": depths[member["id"]]})
	return out


def list_capacity(row_count: int, pane_lines: int) -> int:
	"""How many list rows a pane this tall actually DRAWS.

	THE single viewport authority for the list, shared by the model's
	scrolling and by the renderer that draws it. An overflowing list spends
	its last row on the "... N more" indicator; a list that FITS does not, and
	reserving that row unconditionally is what hid a message.

	The exact-fit case is where it went wrong: the model scrolled against
	`pane_lines - 1` while the pane, seeing no overflow, drew against
	`pane_lines`. With exactly as many messages as rows, moving to the last
	one scrolled the top to 1 -- so row 0 left the screen with no `... above`
	marker to say it had, which is the one thing an overflow indicator exists
	to prevent. Two heights for one pane is the same class of fault as the
	four copies of the old pane-width arithmetic."""
	if pane_lines <= 0:
		return 0
	return pane_lines - 1 if row_count > pane_lines else pane_lines


def list_top(row_count: int, pane_lines: int, top: int) -> int:
	"""The first row a pane this tall may honestly start at.

	The other half of the same authority. Clamping only to `row_count - 1`
	let the top stay wherever a smaller pane had pushed it: widen the terminal
	so the list fits again and it still started at row 7, drawing one message
	and silently omitting the seven above it. You can never scroll past the
	point where the last row sits at the bottom of the pane."""
	return max(0, min(top, max(0, row_count - list_capacity(row_count, pane_lines))))


def _trimmed_subject(text: str | None) -> str | None:
	"""The subject as the authority will accept it: edge whitespace removed.

	Ruled, and ruled narrowly. The SHARED CORE and the agent CLI keep refusing
	edge whitespace -- an agent sending `"  S  "` has a bug worth hearing
	about, and silently accepting it would hide the bug and change retry
	identity. The TUI is different: a human typing into a field trails a space
	the way they trail a space in every other text box on their machine, and
	answering that with a refusal at send time is the console failing to be a
	console.

	So this is a TUI-only courtesy applied at SEND, and it is the only place
	that trims. Interior whitespace is untouched, because it is not ambiguous.
	A subject that is nothing but whitespace becomes None -- the same as no
	subject -- rather than an empty string the core would refuse.
	"""
	if text is None:
		return None
	trimmed = text.strip()
	return trimmed or None


class InboxState:
	"""What the two panes show, and nothing about how they look."""

	def __init__(self, participant: str):
		self.participant = participant
		# THE CLAIM-ON-HIGHLIGHT DWELL. `None` when nothing is pending
		# commitment; otherwise the message identity being dwelt on and its
		# monotonic deadline.
		self.dwell: dict | None = None
		# Injectable so the dwell is testable without sleeping. Production
		# passes nothing and gets `time.monotonic`; a test substitutes a
		# counter and drives the deadline exactly, which is the difference
		# between asserting the rule and asserting that two seconds elapsed.
		self.clock = time.monotonic
		self.rows: list[dict] = []
		self.cursor = 0
		self.mode = MODE_BROWSE
		self.draft = ""
		self.detail: dict | None = None      # preview (no content) or opened delivery
		# Which row the detail pane is DESCRIBING. Without this, a failed
		# preview could leave message A's headers beside a selection on
		# message B, and the human would reasonably believe the pane describes
		# what the cursor is on -- then press Enter and claim something else.
		# An error in the status bar does not make that safe.
		self._detail_row: tuple | None = None
		# What a state-changing action acts on. Set ONLY by an explicit open,
		# cleared by any navigation. It is deliberately NOT the cursor: rows
		# are removed and reordered by refresh (opening a notice removes it),
		# so the cursor can land on a different message between what the human
		# is LOOKING AT and what they then act on. Binding `r` to the cursor
		# meant a reply typed while reading a notice could be sent to an
		# unrelated claim -- the human's own words delivered to the wrong
		# recipient. The displayed item and the action target must be
		# incapable of diverging.
		self.opened: dict | None = None
		self.status = ""
		self.status_severity = SEV_INFO
		self.warning = ""
		self.last_error = ""
		# Viewports live in the MODEL, not in the curses loop. Scrolling
		# decides which rows and which lines are visible, and that is
		# behaviour worth testing without a terminal -- a cursor that scrolls
		# off the pane is invisible to the human but still the thing their
		# next keystroke acts on.
		self.inbox_top = 0
		self.detail_offset = 0
		self.inbox_height = 10
		self.detail_height = 10
		# Which leaf the human has selected inside the detail pane, as a
		# manifest address. Materializing acts on THIS, not on the whole
		# message -- a multipart message has no single "the" body.
		self.part_cursor = 0
		# A pending multi-key chord (`g` awaiting a second `g`). Held in the
		# model so the sequence is testable, and so an abandoned prefix is
		# visible state rather than something hidden in the terminal loop.
		self.pending_prefix = ""
		self.send_return_mode = None
		# CARET POSITIONS, one per editable buffer. The editor was append-only
		# -- text could only be removed by backspacing from the end, and the
		# arrow keys did nothing at all -- because there was no position to
		# insert at. Everything below is expressed as (text, caret).
		self.draft_caret = 0
		self.compose_carets: dict = {}
		# SENT is a second VIEW of the same pane, with its own cursor and
		# scroll: switching back must land where you were, or the switch costs
		# more than it saves.
		self.view = VIEW_INBOX
		self.compose_recipient = ""
		# True only while composing a REPLY to something. A fresh `n`/`N`
		# leaves the previously opened item in `detail`, so without this a new
		# message would open the editor seeded with an unrelated message the
		# human happened to be reading.
		self.compose_is_reply = False
		# Body imported from the external editor. Never typed into.
		self.reply_body = ""
		# True once the human has explicitly opened the editor for a reply.
		# Then an empty body is a REFUSAL rather than a silent fall back to
		# sending the subject line: they asked for a full reply and got an
		# empty one, and quietly sending something else is not that message.
		self.reply_body_requested = False
		# Retained drafts, participant-local and never protocol state. Loaded
		# by the driver at startup, because reading them needs the configured
		# projection directory the driver supplies.
		self.drafts: list[dict] = []
		self.draft_id: str | None = None
		self.discard_target: str | None = None
		# Set when a committed draft could not be removed from disk. The send
		# succeeded; the cleanup did not, and the human has to be told.
		self.draft_cleanup_warning: str | None = None
		# Set when a reopened reply has no claim left to answer. It is not an
		# error state -- the draft is intact and reopened -- but sending is
		# impossible and the console must say why rather than blame the draft.
		self.reply_blocked: str | None = None
		self.draft_serial = 0
		self.sent_rows: list[dict] = []
		# True only when the most recent poll actually listed outbound rows.
		self.sent_rows_fresh = False
		self.sent_cursor = 0
		self.sent_top = 0
		# Recipient picker state. Capacity comes from the renderer, which is
		# the only thing that knows how many rows the prompt took after
		# wrapping at the current width.
		self.recipients: list[dict] = []
		# The picker's live list, emptied when it closes -- and the roots this
		# session has seen, kept so a refusal can still name the base
		# directory after the picker is gone.
		self.roots: list[dict] = []
		self.known_roots: list[dict] = []
		self.picker_page = 0
		self.picker_capacity = 18
		# Which composing mode the root picker interrupted, so cancelling
		# returns to the draft the human was actually in.
		self.compose_return_mode: str | None = None
		# Compose buffers. Kept in the model so a half-written message
		# survives a redraw and is testable without a terminal.
		self.compose: dict = {}
		self.compose_field = 0
		# External part bytes fetched for display, keyed by manifest address.
		# Populated only by an explicit `v`, and dropped whenever the detail
		# pane changes: a file read for one message must never be drawn under
		# another.
		self.external_text: dict = {}
		# The modal help view's own scroll. Nothing else about the console
		# moves while it is open.
		self.help_offset = 0
		# The message a composed follow-up is IN REFERENCE TO, and the thread
		# it inherits. Set only by `_begin_follow_up`, cleared by every fresh
		# composition, so an ordinary `n` can never acquire a linkage.
		self.follow_up_to: str | None = None
		self.follow_up_thread: str | None = None
		# Navigation focus. The LIST by default: it is where a console opens
		# and what a new arrival is about.
		self.focus = FOCUS_LIST
		# Horizontal scroll of the DETAIL pane, in display cells. It belongs
		# to the CONTENT being read, so it resets when the message, the view
		# or the selected part changes -- and survives everything else.
		self.detail_hscroll = 0
		# No default. Resolved from the participant's configured
		# `projection_dir` at startup; absent that, materialize refuses rather
		# than writing into whatever directory launched the console.
		self.projection_dir = ""

	@property
	def detail_row(self) -> tuple | None:
		"""Which row the detail pane is DESCRIBING."""
		return self._detail_row

	@detail_row.setter
	def detail_row(self, value) -> None:
		"""Setting it to a DIFFERENT row resets the sideways offset.

		Here rather than in `preview`, because the offset must survive a
		preview of the SAME row -- which the two-second poll and `Ctrl-R` both
		are -- and every path that changes what the pane describes goes
		through this one assignment. Resetting in `preview` snapped the pane
		back to column zero every couple of seconds while someone was
		reading."""
		if value != self._detail_row:
			self.detail_hscroll = 0
		self._detail_row = value

	# -- OBSERVE ----------------------------------------------------------

	def refresh(self, store) -> None:
		"""Rebuild the queue. Read-only by construction: `scan` and
		`list_notices` create nothing.

		Deliberately NOT `wait`: a blocking wait claims the oldest message
		before the human has chosen it, which would make merely running the
		console take ownership of work."""
		# A poll runs unattended, forever. An unguarded scan means one busy
		# moment takes the console down and the human's context with it, so
		# the previous rows are KEPT and the bar says the refresh failed --
		# stale-but-labelled beats gone.
		# EVERY retained message addressed here, whatever its state. One list
		# across the lifecycle: splitting active from handled made a message
		# vanish the moment it was answered, and the human who answered it
		# watched their own evidence disappear.
		messages = self._guard("refresh",
		                       lambda: store.list_messages(self.participant))
		if messages is None:
			return
		scan = self._guard("scan", lambda: store.scan(self.participant))
		if scan is None:
			return
		rows: list[dict] = [{**entry, "row_type": ROW_MESSAGE} for entry in messages]
		damaged = {d["id"] for d in scan["damaged"]}
		for row in rows:
			row["damaged"] = row["id"] in damaged
		# ACTIVITY, not the unseen queue. Opening a notice used to remove its
		# row, so a human watched an announcement disappear while they were
		# reading it. TTL and gc are now the only reasons it leaves.
		notices = self._guard("list notices",
		                      lambda: store.list_notice_activity(self.participant))
		if notices is None:
			return                       # keep the previous coherent rows
		for entry in notices:
			rows.append({**entry, "row_type": ROW_NOTICE,
			             "state": "unseen" if entry.get("seen_ts") is None
			             else "seen"})
		# NEWEST FIRST, by the TOTAL order `(created_ts, id)` descending --
		# Slawomir's ruling, and the same ordering discipline the Sent filter
		# already uses. MESSAGES is retained activity: with oldest-first,
		# reaching new work meant scrolling past the entire history, and that
		# cost grows forever.
		#
		# This is PRESENTATION ONLY. Authority delivery is unchanged: `claim`
		# and `wait` still take the oldest pending message, and the console
		# still never uses them to populate the list. Handled rows keep their
		# place in this order rather than being sorted away, because where a
		# message sits is part of its story.
		#
		# THREADED: a reply is an indented child under the message it answers,
		# and a thread sorts by its newest member. `thread_rows` owns both
		# orders and stamps each row's `depth`.
		rows = thread_rows(rows)
		# DRAFTS FIRST, above everything the authority knows about.
		#
		# They have no authority timestamp to sort by -- they were never
		# published -- so any position among the dated rows would be invented.
		# The top is also where they are useful: an unfinished message is the
		# one row whose next action nobody else can take.
		rows = [{"row_type": ROW_DRAFT, "id": draft["id"], "state": "draft",
		         "subject": draft.get("subject") or "",
		         "to_participant": draft.get("to") or "",
		         "from_participant": self.participant,
		         "created_ts": None, "depth": 0, "damaged": False,
		         "draft": draft}
		        for draft in self.drafts] + rows
		# NOTHING is said about arrivals. The `N new: senders` line that used
		# to be set here was mailbox state the header counts and the
		# newest-first list already show -- a third copy, written by a timer,
		# over whatever the human's last action had put in the status bar. An
		# error or an editor outcome being replaced two seconds later by a
		# count is the specific harm; the arrival itself is not news the
		# status bar has to carry, because the row is already at the top.
		#
		# The cursor is still never moved: a poll that jumped to new mail
		# would yank the human off what they were reading, and the next
		# keystroke would act on something they did not choose.
		#
		# By IDENTITY, not by index. Newest-first inserts arrivals at the TOP,
		# so every existing row shifts down by one and a numeric cursor would
		# quietly point at a different message -- the next Enter would claim
		# something the human never selected. That is the wrong-target bug
		# again, arriving through the poll instead of through a keystroke.
		selected = self.selected
		self.rows = rows
		self._restore_cursor(selected)
		self._refresh_sent(store)
		# Refresh OWNS the invariant, because refresh is what breaks it: the
		# polling loop calls this, rows reorder and disappear underneath, and
		# an action target left pointing at a moved or vanished row is exactly
		# how a reply reaches the wrong recipient.
		self._revalidate_action_target()
		self._sync_detail_metadata()
		self._scroll_cursor_into_view()

	# Lifecycle metadata the LIST already knows and the detail pane displays.
	# Deliberately a short, explicit list rather than "everything in the row":
	# copying wholesale would eventually drag a content-shaped field into an
	# envelope the human is reading, which is the one thing this must not do.
	_SYNCED_FIELDS = ("state", "outcome", "completed_ts", "responds_to",
	                  "thread_id", "seen_count", "expires_ts", "damaged")

	def _sync_detail_metadata(self) -> None:
		"""Bring an OPENED detail's lifecycle metadata up to the poll.

		The list and the detail were rendering two different authority
		snapshots of the same row: `refresh` rebuilt the rows, the glyph moved,
		and the envelope captured at open time kept saying `State: claimed`
		until the human navigated away and back. Two panes contradicting each
		other about the same message is worse than either being stale, because
		neither one tells you which to believe.

		METADATA ONLY. No content is re-read, re-requested or replaced: a
		notice delivered at-most-once must not be asked for a second time, and
		an external or damaged part must not cross an authorization boundary
		because a poll ran. Nothing here calls the store at all -- it copies
		from rows `refresh` has already fetched.

		BY IDENTITY, never by index. If the opened row is gone from the list it
		is LEFT ALONE: the existing unavailable behaviour is the honest answer,
		and attaching the detail to whatever now occupies that position is the
		wrong-target bug in its quietest form.
		"""
		if self.detail is None or self.detail_row is None:
			return
		envelope = self._opened_envelope()
		if envelope is None:
			return
		kind, identity = self.detail_row
		# BOTH LISTS. The reported case is an OUTBOUND row: the recipient
		# claims it, the Sent list's glyph moves, and the opened copy keeps
		# saying the old state. Sent rows live in `sent_rows`, which `refresh`
		# rebuilds separately -- searching only `rows` would have fixed the
		# case nobody reported and left the one Slawomir hit.
		# EVERY matching row, not the first. A notice this participant
		# AUTHORED appears twice: once in the inbox list, which carries no
		# `seen_count`, and once in the Sent list, which does. Returning on
		# the first match copied nothing useful and left `Seen by:` stale --
		# the exact symptom, reached by a different route than the one that
		# caused it.
		#
		# Sent rows are applied LAST so the author's own richer copy wins --
		# and ONLY when this poll actually refreshed them. Applying a retained
		# cache last would let a stale value overwrite a state the primary
		# list just got right, which is worse than the staleness this fixes:
		# stale-but-labelled is the console's rule, silently wrong is not.
		outbound = list(self.sent_rows) if self.sent_rows_fresh else []
		for row in list(self.rows) + outbound:
			if row.get("id") != identity:
				continue
			if row.get("row_type") is not None and row["row_type"] != kind:
				continue
			for field in self._SYNCED_FIELDS:
				if field in row:
					envelope[field] = row[field]

	def _opened_envelope(self) -> dict | None:
		"""The dict whose fields the detail pane renders, or None for a
		preview.

		A PREVIEW is deliberately excluded: it is built from the row on every
		draw, so it is never stale and has nothing to synchronize. Only an
		opened envelope holds a snapshot that can fall behind.
		"""
		detail = self.detail or {}
		delivery = detail.get("delivery")
		if isinstance(delivery, dict):
			message = delivery.get("message")
			return message if isinstance(message, dict) else None
		# EVERY opened envelope key, enumerated from the renderer rather than
		# from memory. `sent_notice` was missing from the first version and
		# nothing failed: an authored broadcast kept showing a stale
		# `Seen by:` while the Sent list counted correctly, which is the same
		# contradiction this exists to remove, one envelope shape along.
		for key in ("sent", "sent_notice", "received", "notice"):
			envelope = detail.get(key)
			if isinstance(envelope, dict):
				return envelope
		return None

	def _restore_cursor(self, previous: dict | None) -> None:
		"""Put the cursor back on the SAME ROW after the list is rebuilt."""
		if previous is not None:
			identity = (previous["row_type"], previous["id"])
			for index, row in enumerate(self.rows):
				if (row["row_type"], row["id"]) == identity:
					self.cursor = index
					return
		# It is gone -- collected, expired, or a notice that was opened. Fall
		# back to a position, clamped.
		self.cursor = min(self.cursor, max(0, len(self.rows) - 1))

	def _refresh_sent(self, store) -> None:
		"""Outbound history, from the AUTHORITY, on the same poll as the
		inbox.

		On the poll on purpose: the point of a sent view is watching pending
		become claimed, and a list that only refreshes when you ask cannot
		show you that. Failure keeps the previous rows and says so, like the
		inbox does -- stale-but-labelled beats gone."""
		# Whether THIS poll actually got outbound rows. `_sync_detail_metadata`
		# applies sent rows last, so a retained-but-stale cache would overwrite
		# a state the primary list just refreshed correctly -- turning a
		# partial failure into a WRONG screen rather than a stale one.
		self.sent_rows_fresh = False
		sent = self._guard("list sent", lambda: store.list_sent(self.participant))
		if sent is None:
			return
		self.sent_rows_fresh = True
		# Newest-first here too, so a send you just made appears at the top and
		# shifts every other row down. Same identity rule, same reason.
		# Read directly rather than through `selected_sent`, which answers only
		# while the Sent filter is the active view -- the poll runs in both.
		previous = (self.sent_rows[min(self.sent_cursor, len(self.sent_rows) - 1)]
		            if self.sent_rows else None)
		self.sent_rows = sent
		if previous is not None:
			for index, row in enumerate(sent):
				if row["id"] == previous["id"]:
					self.sent_cursor = index
					break
			else:
				self.sent_cursor = min(self.sent_cursor, max(0, len(sent) - 1))
		else:
			self.sent_cursor = min(self.sent_cursor, max(0, len(sent) - 1))
		self.sent_top = min(self.sent_top, max(0, len(sent) - 1))

	# How far the rendered detail overflows the pane, in display cells. The
	# driver sets it from the renderer each frame -- only the renderer knows
	# how the content laid out at this width.
	detail_overflow = 0

	def toggle_focus(self) -> None:
		"""`Tab`: swap which pane the navigation keys drive.

		BROWSE only -- Tab means "next field" while composing and "next page"
		in the picker, and stealing it there would cost a working key to gain
		a new one. Two panes means two stops: Shift-Tab is the same toggle
		rather than a third.

		Writes NOTHING and disturbs nothing: not the selection, the action
		target, either offset, the selected part, a draft or the status bar.
		The only thing that moves is which keys go where."""
		if self.mode != MODE_BROWSE:
			return
		self.focus = FOCUS_DETAIL if self.focus == FOCUS_LIST else FOCUS_LIST

	def leave_detail(self) -> None:
		"""Esc in BROWSE: leave DETAIL for LIST. The way out, mirroring Enter.

		PURE UI STATE. No store call, no claim, no receipt, no refresh, no
		disposition, nothing written anywhere -- the selection, the opened
		item, both offsets, the selected part, any draft and the status bar
		all stay exactly as they were. The only thing that moves is which pane
		the keys go to.

		A no-op with LIST already focused, deliberately: Esc is the most
		reflexive key on a keyboard, and in browse mode it must never be the
		one that undoes something. Its modal meanings -- cancel a draft,
		decline a confirmation, close help, dismiss a picker -- are untouched
		and live in their own modes.
		"""
		if self.mode != MODE_BROWSE:
			return
		self.focus = FOCUS_LIST

	def affordances(self) -> dict:
		"""What is legal RIGHT NOW -- THE one source, read by both the footer
		and key dispatch.

		A footer that guessed separately would be a second opinion about what
		is legal and would drift from dispatch within weeks: the same shape as
		the two pane heights that hid a message, and the four copies of the
		pane width before them. With one predicate, "nothing advertised
		refuses just because the state makes it unavailable" is a property a
		test can hold; with two it is a hope.

		The defect that prompted it: an opened notice advertised `c close`,
		and a notice has no claim for close to consume. It had said so since
		the footer was written, because the footer was a fixed string."""
		claim = self._held_claim_id()
		opened = self.opened or {}
		part = self.selected_part
		external = (part or {}).get("storage") == "external"
		# The declared type is already on the part, so whether `v` could show
		# anything is decidable WITHOUT touching the file. Advertising it for
		# an external PNG meant reading and hashing a file only to report that
		# it is not text -- an offered action refusing for a reason the
		# console already knew.
		displayable = external and _is_displayable_text(part)
		return {
			# Enter: any row of the ACTIVE VIEW can be opened; what that MEANS
			# differs by row. `self.selected` is the MESSAGES selection, so
			# reading it here hid Enter in SENT whenever MESSAGES happened to
			# be empty -- a selectable row on screen that the console refused
			# to open, because the gate was asking about a different list.
			# THIS AFFORDANCE IS ABOUT THE KEY, NOT THE VERB, and getting that
			# wrong shipped a defect to a human trial: once the two-second
			# dwell had opened a row, `_already_open` made this false, dispatch
			# refused `K.OPEN` before `enter_selected` could run, and the most
			# ordinary sequence there is -- pause on a row until it opens, then
			# press Enter to read it -- left focus in LIST.
			#
			# "Opening again is redundant" is true. "Enter has nothing to do"
			# does not follow: while LIST has focus, Enter still performs the
			# separately ruled focus move into DETAIL. I called that swallowing
			# correct in a progress note; the finding's already-open clause
			# said otherwise in writing, and it was right.
			#
			# So the key is offered when EITHER opening is available or a pure
			# focus transfer is. An UNSEEN NOTICE still advertises it, because
			# there it is the explicit mark-seen action and nothing has
			# consumed it yet.
			"open": self.selected_in_view is not None and (
				not self._already_open or self._can_enter_detail),
			# Close consumes a claim, so it needs one. Never a notice, never
			# an outbound row, never a handled row, never the Sent view.
			"close": claim is not None,
			# Reply/follow-up: a live claim, an opened notice, or a resolved
			# row that can still be followed up.
			"reply": bool(claim or opened.get("row_type") == ROW_NOTICE
			              or self.follow_up_context),
			# Only when moving actually changes which part is selected.
			"part_nav": len(self.visible_parts()) > 1,
			# `h`/`l` sideways: only where the detail is FOCUSED and something
			# is actually off the right edge. Advertising it on a pane with
			# nothing to reveal is the same fault as `Tab` in a one-field
			# notice -- a promise the key cannot keep.
			"hscroll": self.focus == FOCUS_DETAIL and self.detail_overflow > 0,
			# `v` reads an EXTERNAL part, only from an active claim, and only
			# when its declared type is text this terminal can show.
			"read_part": bool(claim and displayable),
			# `m` refuses on an external part -- it is already a file -- and
			# needs somewhere to write.
			"materialize": bool(claim and part and not external
			                    and self.projection_dir),
		}

	def modal_affordances(self) -> dict:
		"""State-dependent controls inside a modal mode.

		The modal legends are mostly static -- typing is typing -- but a
		couple of them promise a CHANGE, and a key that cannot reach another
		state is not meaningful even though it is mapped. `Tab` in a one-field
		notice and in a one-page picker are exactly that.

		Deliberately NOT extended to movement at a boundary: `j` at the last
		row still means something, because the list can move. This is only for
		controls with no other state to reach at all."""
		return {
			"picker_paging": self.picker_pages > 1,
			"more_fields": len(self.compose_fields) > 1,
		}

	def unavailable_reason(self, action: str) -> str:
		"""WHY an unavailable action is unavailable, in the words the human
		needs.

		The affordance query answers yes or no, which is what the footer and
		dispatch need; a refusal also has to say what would make it work. The
		two must not disagree, so both are computed from the same conditions
		here rather than a generic "not available" that tells nobody
		anything."""
		claim = self._held_claim_id()
		part = self.selected_part
		# The two modal controls that can run out of anywhere to go.
		if action == "picker_paging":
			return "every recipient fits on this page"
		if action == "more_fields":
			return "this draft has one field"
		if action == "close":
			return "close needs a claim you hold; nothing here owes a disposition"
		if action == "reply":
			return "nothing to reply to: open a message or a notice first"
		if action == "open":
			return "nothing to open"
		if action == "part_nav":
			return "this message has one part"
		if action == "read_part":
			if claim is None:
				return ("reading a part needs a message you hold the claim for; "
				        "this row has none")
			if part is None:
				return "no part selected"
			if part.get("storage") != "external":
				return "v reads an EXTERNAL part; this one's bytes are on screen"
			pin = part.get("attachment") or {}
			return (f"{part.get('content_type', 'that type')} is not displayable "
			        f"in the terminal; the file remains at "
			        f"{pin.get('root_id', '?')}:{pin.get('path', '?')}")
		if action == "materialize":
			if claim is None:
				return ("materialize needs a message you hold the claim for; "
				        "this row has none")
			if part is None:
				return "no part selected"
			if part.get("storage") == "external":
				return ("that part is an external file at "
				        f"{(part.get('attachment') or {}).get('root_id', '?')}:"
				        f"{(part.get('attachment') or {}).get('path', '?')}; it is "
				        "not copied into a projection")
			return ("no projection directory: set projection_dir for this "
			        "participant in the config")
		return "not available here"

	def select_view(self, view: str) -> None:
		"""One key, no writes, and each view keeps its own place."""
		if view not in (VIEW_INBOX, VIEW_SENT):
			return
		if view == self.view:
			return
		self.view = view
		self.detail_hscroll = 0
		# Back to the LIST: the human just said which list they are
		# navigating, so the navigation keys should be pointed at it.
		self.focus = FOCUS_LIST
		# Horizontal scroll of the DETAIL pane, in display cells. It belongs
		# to the CONTENT being read, so it resets when the message, the view
		# or the selected part changes -- and survives everything else.
		self.detail_hscroll = 0
		# Drop the UI target. The CLAIM is untouched -- viewing must never
		# mutate the authority -- but an action target left armed behind a
		# different list is exactly the bug this console was built after: the
		# human sees a sent row and `r`, `e`, `c` or `m` reaches an inbox
		# claim they can no longer see.
		self._clear_action_target()
		self.detail_offset = 0
		self.set_status({VIEW_SENT: "sent — newest first, read only",
		                 VIEW_INBOX: "messages"}[view], SEV_INFO)

	@property
	def view_rows(self) -> list[dict]:
		return self.sent_rows if self.view == VIEW_SENT else self.rows

	# Each view keeps its own place. `_CURSORS` and `_TOPS` name the attribute
	# per view so a third view could not be added while quietly sharing the
	# inbox cursor -- which is exactly how the styling bug in R3 happened.
	_CURSORS = {VIEW_SENT: "sent_cursor", VIEW_INBOX: "cursor"}
	_TOPS = {VIEW_SENT: "sent_top", VIEW_INBOX: "inbox_top"}

	@property
	def view_cursor(self) -> int:
		return getattr(self, self._CURSORS[self.view])

	@view_cursor.setter
	def view_cursor(self, value: int) -> None:
		setattr(self, self._CURSORS[self.view], value)

	@property
	def view_top(self) -> int:
		return getattr(self, self._TOPS[self.view])

	@view_top.setter
	def view_top(self, value: int) -> None:
		setattr(self, self._TOPS[self.view], value)

	@property
	def _can_enter_detail(self) -> bool:
		"""Whether Enter still has its PURE FOCUS action here.

		Nothing to open, but somewhere to go: browse mode, LIST focus, and a
		detail pane already showing this row's content. No store call, no
		claim, no receipt -- the transfer is UI state and nothing else."""
		return (self.mode == MODE_BROWSE and self.focus == FOCUS_LIST
		        and self.detail is not None)

	@property
	def _already_open(self) -> bool:
		"""Whether the highlighted row's CONTENT is what the pane is showing.

		A preview does not count: metadata is not the message, and for an
		unseen notice the preview is exactly the state `Enter` acts on."""
		row = self.selected_in_view
		if row is None or self.detail is None:
			return False
		# CONTENT keys only. `preview`, `sent_row` and `history_row` are row
		# SUMMARIES built from the list call -- metadata, not the message --
		# so a row showing one has not been opened, and `Enter` still has
		# something to do.
		if not ({"delivery", "notice", "sent", "received"} & set(self.detail)):
			return False
		return self.detail_row == (row.get("row_type"), row.get("id"))

	@property
	def selected_in_view(self) -> dict | None:
		"""The selected row of the ACTIVE view.

		`selected` is deliberately the MESSAGES row and stays that way -- the
		actionable list is what most of the model is about. Anything asking
		"what is under the cursor RIGHT NOW", across whichever list is on
		screen, has to ask this instead."""
		rows = self.view_rows
		if not rows:
			return None
		return rows[min(self.view_cursor, len(rows) - 1)]

	@property
	def selected_sent(self) -> dict | None:
		if self.view != VIEW_SENT or not self.sent_rows:
			return None
		return self.sent_rows[min(self.sent_cursor, len(self.sent_rows) - 1)]

	def open_sent_selected(self, store) -> bool:
		"""Read your own outbound message. Creates NOTHING. Returns whether it
		opened.

		Not a delivery: no claim, no receipt, no transition, no audit write.
		Reading your own outbox must never consume the message the recipient
		is waiting for -- which is exactly what would happen if this reused
		the claim path because both end in "show me the content".

		THE RESULT IS REPORTED for the same reason `open_selected` reports
		one: `Enter` focuses DETAIL only on a successful open, and a refused
		read here leaves the lightweight sent-row preview behind. Without
		this, `open_selected` returned True for the whole SENT branch
		unconditionally and Enter focused a pane showing nothing it had been
		asked for. I converted the other twelve return paths and classified
		this delegation as success without checking whether the delegate could
		fail; it can."""
		row = self.selected_sent
		if row is None:
			self.set_status("nothing to open", SEV_INFO)
			return False
		if row.get("row_kind") == "notice":
			result = self._guard("open sent notice",
			                     lambda: store.open_sent_notice(row["id"], self.participant))
			if result is None:
				return False
			self.detail = {"sent_notice": result["sent_notice"]}
		else:
			result = self._guard("open sent",
			                     lambda: store.open_sent(row["id"], self.participant))
			if result is None:
				return False             # damaged pins fail closed, and say so
			self.detail = {"sent": result["sent"]}
		self.detail_offset = 0
		self.set_status("read only — this is your own sent copy", SEV_INFO)
		return True

	def _revalidate_action_target(self) -> None:
		"""Keep the opened item, the cursor and the actionable claim in
		agreement, or drop the target loudly.

		A target that quietly survives its claim is worse than no target: the
		human keeps seeing an actionable item and their next keystroke goes
		somewhere unexpected."""
		if self.opened is None:
			return
		for index, row in enumerate(self.rows):
			if (row["row_type"] == self.opened["row_type"]
					and row["id"] == self.opened["id"]):
				if (self.opened["row_type"] == ROW_MESSAGE
						and self.opened["claim_id"] is not None
						and (row["state"] != "claimed"
						     or row.get("claim_id") != self.opened["claim_id"])):
					break                      # claim resolved or replaced
				self.cursor = index
				return
		if (self.opened["row_type"] == ROW_NOTICE
				and (self.detail or {}).get("notice", {}).get("id") == self.opened["id"]):
			# An opened notice keeps its row now -- MESSAGES lists notice
			# ACTIVITY, so seeing one changes its state rather than removing
			# it. This branch is the DEFENSIVE case that remains: TTL,
			# `expire` or gc can still take the row away underneath a human
			# who is reading it. Nothing is owed and nothing can be
			# abandoned, so dropping the target here would discard content
			# they are still reading and make `r` on an open notice
			# impossible.
			#
			# (It used to say a notice normally LEAVES the list, which was
			# true of the unseen-only listing and is not true now.)
			return
		# Gone, or no longer the claim we opened. Say so rather than leaving
		# stale actionable state armed behind the current view.
		was = self.opened
		self.opened = None
		self.detail = None
		self.detail_row = None
		if self.mode == MODE_REPLY:
			self.mode = MODE_BROWSE
			self.draft = ""
			self.set_status("the message you were replying to is no longer "
			                "yours to answer; draft discarded", SEV_ERROR)
		else:
			self.set_status(f"the {was['row_type']} you had open is no longer "
			                f"available; nothing is actionable", SEV_WARNING)

	def set_viewport(self, inbox_height: int, detail_height: int,
	                 picker_capacity: int | None = None) -> None:
		"""The PUBLIC resize event. The driver calls it on start and on every
		terminal resize, before rendering.

		Deliberately not done inside `render`: drawing the same model at a
		different size would then be a hidden state transition, and a function
		documented as observation would be moving the cursor."""
		self.inbox_height = max(1, inbox_height)
		self.detail_height = max(1, detail_height)
		if picker_capacity is not None:
			self.picker_capacity = max(1, picker_capacity)
		self._scroll_cursor_into_view()
		self.detail_offset = max(0, self.detail_offset)

	def _scroll_cursor_into_view(self) -> None:
		"""Keep the selected row visible. A selection scrolled off the pane is
		the same class of problem as the action-target bug: the human cannot
		see what they are about to act on.

		Against `list_capacity`, not against the pane height: how many rows are
		drawn depends on whether the list overflows, and the model has to reach
		that conclusion the same way the renderer does."""
		rows = len(self.view_rows)
		window = max(1, list_capacity(rows, self.inbox_height))
		cursor, top = self.view_cursor, self.view_top
		if cursor < top:
			top = cursor
		elif cursor >= top + window:
			top = cursor - window + 1
		self.view_top = list_top(rows, self.inbox_height, top)

	def scroll_detail_sideways(self, delta: int, widest: int, pane: int) -> None:
		"""`h`/`l` under DETAIL focus: one display cell at a time.

		PURE OBSERVATION -- no core call, no claim, no receipt, no write. The
		maximum is computed from the RENDERED detail at the current width and
		clamped here, so a resize cannot leave the view past the end of its
		own content."""
		# One cell of the pane goes to the left-hand indicator once scrolled,
		# so the far end is `widest - (pane - 1)`. Clamping to `widest - pane`
		# left the last cell permanently unreachable -- a scroll that cannot
		# reach the end of its content is not much better than truncation.
		limit = max(0, widest - max(1, pane) + 1) if widest > max(1, pane) else 0
		self.detail_hscroll = max(0, min(limit, self.detail_hscroll + delta))

	def scroll_detail(self, delta: int, total_lines: int) -> None:
		"""Scroll the detail pane. `total_lines` comes from the renderer,
		which is the only thing that knows how the content laid out at the
		current width."""
		limit = max(0, total_lines - self.detail_height)
		self.detail_offset = max(0, min(limit, self.detail_offset + delta))

	def jump_to(self, index: int, store) -> None:
		"""Absolute row move -- `gg` and `G` under LIST focus.

		Like every other selection change it now COMMITS on the destination
		(Slawomir's ruling); only the row actually landed on, never the ones
		skipped over."""
		rows = self.view_rows
		if not rows:
			return
		self.view_cursor = max(0, min(len(rows) - 1, index))
		self.detail_offset = 0
		self._scroll_cursor_into_view()
		self._clear_action_target()
		self.select_row(store)

	def move(self, delta: int, store) -> None:
		"""Move the cursor and COMMIT on the row landed on.

		Creates no receipt -- a broadcast is still never consumed by looking
		at it -- but an inbound directed row IS claimed and opened. See
		`select_row`. (This said "creates NO claim", from before the ruling.)"""
		rows = self.view_rows
		if not rows:
			return
		previous = self.view_cursor
		self.view_cursor = max(0, min(len(rows) - 1, self.view_cursor + delta))
		self.detail_offset = 0
		self._scroll_cursor_into_view()
		if self.view_cursor != previous:
			# Navigating away abandons the opened item. The claim itself is
			# untouched and still owed -- only this console's notion of "the
			# thing I am acting on" is dropped, because the human is now
			# looking at something else.
			self._clear_action_target()
		self.select_row(store)

	# -- failures are status, never a teardown ----------------------------

	def set_status(self, text: str, severity: str = SEV_INFO) -> None:
		"""The one way status is written, so severity can never be forgotten
		by a caller that used a bare assignment."""
		self.status = text
		self.status_severity = severity

	def _guard(self, description: str, action):
		"""Run a core action, turning an expected Baton failure into visible
		status instead of an exception.

		A console that dies on a lost race takes the human's context with it,
		and a console that swallows the error silently leaves them believing
		something happened. Neither is acceptable: the model stays coherent
		and SAYS what went wrong. Unexpected exceptions are not caught --
		those are bugs and should surface."""
		try:
			return action()
		except BatonError as exc:
			self.set_status(f"{description} failed: {exc}", SEV_ERROR)
			self.last_error = str(exc)
			return None

	def _clear_action_target(self) -> None:
		self.opened = None
		if self.mode == MODE_REPLY:
			# A half-typed draft belonged to the item being abandoned.
			self.mode = MODE_BROWSE
			self.draft = ""

	# -- part selection inside the detail pane ----------------------------

	def visible_parts(self) -> list[dict]:
		"""Flat list of LEAF parts of whatever is displayed, in manifest
		order. Containers are structure, not something to materialize."""
		detail = self.detail or {}
		if "preview" in detail:
			tree = detail["preview"].get("parts") or []
		elif "delivery" in detail:
			content = (detail["delivery"].get("message") or {}).get("content") or {}
			tree = content.get("parts") or []
		elif "notice" in detail:
			notice = detail["notice"]
			tree = (((notice.get("content") or {}).get("parts")
			         if notice.get("content") else notice.get("parts")) or [])
		elif "sent" in detail:
			tree = ((detail["sent"].get("content") or {}).get("parts")) or []
		elif "sent_notice" in detail:
			tree = ((detail["sent_notice"].get("content") or {}).get("parts")) or []
		elif "received" in detail:
			tree = ((detail["received"].get("content") or {}).get("parts")) or []
		else:
			return []
		out: list[dict] = []

		def walk(nodes):
			for node in nodes:
				children = node.get("parts")
				if children:
					walk(children)
				elif not node.get("is_container"):
					out.append(node)
		walk(tree)
		return out

	def move_part(self, delta: int) -> None:
		parts = self.visible_parts()
		if not parts:
			self.part_cursor = 0
			return
		before = self.part_cursor
		self.part_cursor = max(0, min(len(parts) - 1, self.part_cursor + delta))
		if self.part_cursor != before:
			# A different part is different content; the sideways position
			# belonged to the old one.
			self.detail_hscroll = 0

	@property
	def selected_part(self) -> dict | None:
		parts = self.visible_parts()
		if not parts:
			return None
		return parts[min(self.part_cursor, len(parts) - 1)]

	def read_selected_external_part(self, store) -> str | None:
		"""`v`: read an EXTERNAL part's bytes and show them in the detail pane.

		The trial failure this exists for: an external leaf carries a pin
		instead of bytes, so the pane drew its header and nothing else, and
		the human reported "I can only view part 0". Materializing is not the
		answer -- the part is already a file and the core refuses to copy it
		into a projection, which is the right rule and leaves reading it
		unsolved.

		Read-only, owner-checked and pin-revalidated in the CORE, from an
		explicitly opened active claim -- the same boundary materialize has,
		for the same reason: this returns delivered content, and content is
		not readable until the human has claimed."""
		part = self.selected_part
		if self.opened is None or self.opened.get("row_type") != ROW_MESSAGE:
			self.set_status("reading a part needs a message you hold the claim "
			                "for; this row has none", SEV_WARNING)
			return None
		claim_id = self.opened.get("claim_id")
		if claim_id is None:
			self.set_status("reading a part needs an active claim", SEV_WARNING)
			return None
		if part is None:
			self.set_status("no part selected", SEV_WARNING)
			return None
		if part.get("storage") != "external":
			self.set_status("this part's bytes are already on screen; v is for "
			                "external files", SEV_INFO)
			return None
		result = self._guard("read part", lambda: store.read_claimed_external_part(
			claim_id, self.participant, part=part["address"]))
		if result is None:
			return None
		if not _is_displayable_text(result):
			# Binary is summarized and hidden by default, exactly as it is for
			# an inline base64 leaf. Wrapping a PNG into a terminal is how a
			# console teaches people not to press keys.
			self.set_status(
				f"{result['content_type']} is not text; it is at "
				f"{result['root_id']}:{result['path']}", SEV_WARNING)
			return None
		try:
			text = result["body"].decode("utf-8")
		except UnicodeDecodeError:
			self.set_status(
				f"{result['root_id']}:{result['path']} is not valid UTF-8; "
				f"nothing shown", SEV_WARNING)
			return None
		if result["truncated"]:
			text += "\n… (truncated for display; the whole file is at "
			text += f"{result['root_id']}:{result['path']})"
		self.external_text[str(part["address"])] = text
		self.set_status(f"showing {result['root_id']}:{result['path']} — "
		                f"pin verified", SEV_SUCCESS)
		return text

	def materialize_selected_part(self, store, target_dir: str | None = None,
	                              prefix: str = "message"):
		"""Write the selected part to a file, through the core, from an
		EXPLICITLY OPENED active claim.

		Not from a preview. Writing bytes to disk is reading them in the most
		durable form there is, so allowing it from a pending row would have
		let `m` bypass the whole preview boundary -- content on disk without
		the human ever claiming the message. The core enforces the same rule,
		because a boundary that exists only in the front end is one refactor
		from not existing."""
		part = self.selected_part
		if self.opened is None or self.opened.get("row_type") != ROW_MESSAGE:
			self.set_status("materialize needs a message you hold the claim for; "
			                "this row has none", SEV_WARNING)
			return None
		claim_id = self.opened.get("claim_id")
		if claim_id is None:
			self.set_status("materialize needs an active claim", SEV_WARNING)
			return None
		if part is None:
			self.set_status("no part selected", SEV_WARNING)
			return None
		destination = target_dir or self.projection_dir
		if not destination:
			# Never the process working directory: the console may have been
			# launched from anywhere, and silently writing message content
			# into whatever repository the human happened to be in is not a
			# default anyone would choose.
			self.set_status(
				"no projection directory: set projection_dir for this participant "
				"in the config, or pass a destination", SEV_WARNING)
			return None
		path = self._guard("materialize", lambda: store.materialize_claimed_part(
			claim_id, self.participant, destination,
			prefix=prefix, part=part["address"]))
		if path is not None:
			self.set_status(f"wrote {path}", SEV_SUCCESS)
		return path

	def _would_claim(self, row) -> bool:
		"""Whether opening THIS row would take ownership.

		The single place that answers it, because the dwell and the commit
		must agree exactly: a dwell armed on a row that would not claim would
		delay an ordinary read for two seconds, and a commit that claims a row
		the dwell did not cover would be the ungated claim this exists to
		prevent."""
		if row is None or self.view == VIEW_SENT:
			return False
		return (row.get("row_type") == ROW_MESSAGE
		        and row.get("direction") != "out"
		        and row.get("state") == "pending")

	def _arm_dwell(self, message_id: str) -> None:
		"""Start, or CONTINUE, the dwell on one message identity.

		Keyed by message id rather than row index, which is what makes the
		three cases fall out of one rule: an identity change resets the clock;
		a keystroke that does not move the selection (holding a direction key
		at the end of the list) does not restart it; and leaving a row and
		returning to it later is an identity change in both directions, so it
		gets a fresh two seconds rather than resuming the old ones.

		A monotonic clock, never wall-clock: a NTP correction or a DST jump
		must not make a message claim itself early or hang unclaimed."""
		if self.dwell is not None and self.dwell["message_id"] == message_id:
			return
		self.dwell = {"message_id": message_id,
		              "deadline": self.clock() + DWELL_SECONDS}

	def tick(self, store) -> bool:
		"""Commit a dwell that has come due. Returns whether anything changed.

		Called from the driver loop rather than from a keystroke, because the
		whole point is that the human stopped pressing keys.

		Re-checks the identity every time, which is what makes a POLL safe:
		an arrival or a reordering can move the selection under the cursor,
		and the claim must never be redirected to whatever ended up there.
		The dwell is cancelled rather than transferred."""
		if self.dwell is None:
			return False
		row = self.selected_in_view
		if row is None or row.get("id") != self.dwell["message_id"] \
				or not self._would_claim(row):
			# The row moved, went away, or was claimed by someone else while
			# we waited. Cancel; do not claim a neighbour.
			self.dwell = None
			return False
		if self.clock() < self.dwell["deadline"]:
			return False
		self.dwell = None
		self.open_selected(store)
		self.warning = self._fifo_warning()
		return True

	def dwell_remaining(self) -> float | None:
		"""Seconds until the armed dwell commits, or None. The driver uses it
		to shorten its input timeout so the claim lands near the deadline
		instead of at the next poll."""
		if self.dwell is None:
			return None
		return max(0.0, self.dwell["deadline"] - self.clock())

	def select_row(self, store) -> None:
		"""HIGHLIGHTING a row commits on it, AFTER A TWO-SECOND DWELL.

		Slawomir's ruling, with the dwell added by a later one.

		**This supersedes the OBSERVE/COMMIT split for LIST navigation.** The
		old rule was that selection is always observational and `Enter` is the
		only thing that takes ownership; scrolling to a row and then pressing
		Enter was judged one ceremony too many for a human console, and the
		ownership tradeoff was accepted explicitly.

		What the tradeoff IS, stated rather than discovered: moving across
		several pending directed rows may leave several unresolved claims.
		None is ever auto-closed or auto-replied. The unresolved count, the
		badges and the quit confirmation are what protect them.

		What did NOT change, and is the boundary that keeps this bounded:

		- **Polling never commits.** A poll calls `preview`, never this, so an
		  arrival is not claimed because it arrived and restoring the same
		  selection does not re-claim.
		- **Notices are still explicit.** Highlighting an unseen broadcast
		  shows metadata and records no receipt; `Enter` remains the atomic
		  mark-seen-and-return. Slawomir authorised claim-on-highlight for
		  directed messages, not implicit consumption of broadcasts.
		- **DETAIL-focused navigation is still pure UI**, because it does not
		  move the selection at all.
		- The claim is by the HIGHLIGHTED message id, never the oldest and
		  never a neighbour."""
		row = self.selected_in_view
		if self._would_claim(row):
			# HIGHLIGHT AND PREVIEW IMMEDIATELY; ownership waits. Scrolling
			# through a queue must not accumulate claims on every row passed
			# over, and only the row the human settles on may commit.
			self.preview(store)
			self._arm_dwell(row["id"])
			return
		self.dwell = None
		if row is None or row.get("row_type") in (ROW_NOTICE, ROW_DRAFT):
			# A broadcast stays explicit; so does an empty list.
			#
			# A DRAFT stays explicit for a different reason. Highlighting one
			# used to reopen it straight into the editor, which meant a human
			# could not select a draft in order to DISCARD it: `D` landed in
			# the subject field they had just been dropped into. Claim-on-
			# highlight is about taking ownership of someone else's work, and
			# a draft is already yours -- there is nothing to take. `Enter`
			# reopens it.
			self.preview(store)
			return
		self.open_selected(store)
		# FIFO guidance stays INFORMATIONAL, as ruled: selecting a later
		# message from the same sender still warns, and the claim still goes
		# to the highlighted row rather than being redirected to the earlier
		# one. `preview` used to be where this was computed, and the commit
		# path does not go through it.
		self.warning = self._fifo_warning()

	def preview(self, store) -> None:
		"""Headers and part shape for the selected row -- never content.

		Preview never sets an action target. Looking is not choosing."""
		self.part_cursor = 0
		# Bytes read for one message must never be drawn under another.
		self.external_text = {}
		if self.view == VIEW_SENT:
			# The row itself is the preview. No core call at all: everything
			# shown here came back with `list_sent`, so navigating the Sent
			# filter cannot touch the authority even to read.
			row = self.selected_sent
			self.detail = {"sent_row": row} if row else None
			self.detail_row = ("sent_row", row["id"]) if row else None
			self.warning = ""
			return
		row = self.selected
		if row is None:
			self.detail = None
			self.detail_row = None
			return
		identity = (row["row_type"], row["id"])
		if row["row_type"] == ROW_MESSAGE and row.get("direction") == "out":
			# MY OWN outbound copy. `preview_message` is owner-checked on the
			# RECIPIENT -- correctly, it is the delivery preview -- so routing
			# an outbound row through it made merely SELECTING one an error:
			# "addressed to X, not you". Live-trial report, reproduced: send a
			# reply, land on the child, and the pane goes blank with an error.
			#
			# The row IS the preview here, exactly as it is in the Sent
			# filter: everything shown came back with `list_messages`, so no
			# core call is made and selecting cannot fail. `Enter` still opens
			# the real copy through `open_sent`, which is owner-checked on the
			# SENDER.
			self.detail = {"sent_row": row}
			self.detail_row = identity
			self.warning = ""
			return
		if row["row_type"] == ROW_MESSAGE:
			preview = self._guard(
				"preview", lambda: store.preview_message(row["id"], self.participant))
			if preview is None:
				# Only keep what is displayed if it describes THIS row.
				# Otherwise the pane would be about something the cursor is
				# not on, which is worse than an empty pane.
				if self.detail_row != identity:
					self.detail = None
					self.detail_row = None
					self.set_status(
						f"{self.last_error} — nothing shown for this row", SEV_ERROR)
				return
			self.detail = {"preview": preview}
		else:
			self.detail = {"preview": {k: row[k] for k in row if k != "row_type"}}
		self.detail_row = identity
		self.warning = self._fifo_warning()

	def _fifo_warning(self) -> str:
		"""Choosing a later message is allowed across teams; choosing one while
		an earlier message from the same sender is waiting warns rather than
		forbids -- the human may have a reason, and a console that refuses
		teaches people to work around it.

		Compared by the TOTAL ORDER `(created_ts, id)`, never by position in
		the list. Position meant "older" only while the list was oldest-first;
		under the newest-first ruling `self.rows[:self.cursor]` is the rows
		NEWER than the selection, so the warning would have inverted itself --
		silent, and in the direction that never warns when it should."""
		row = self.selected
		if (row is None or row["row_type"] != ROW_MESSAGE
				or row["state"] != "pending"
				or row.get("direction", "in") != "in"):
			return ""
		here = _row_order(row)
		earlier = [r for r in self.rows
		           if r["row_type"] == ROW_MESSAGE and r["state"] == "pending"
		           and r.get("direction", "in") == "in"
		           and r.get("from_participant") == row.get("from_participant")
		           and _row_order(r) < here]
		if not earlier:
			return ""
		return (f"{len(earlier)} earlier message(s) from "
		        f"{row['from_participant']} are still pending")

	@property
	def selected(self) -> dict | None:
		if not self.rows or self.cursor >= len(self.rows):
			return None
		return self.rows[self.cursor]

	# -- COMMIT -----------------------------------------------------------

	def enter_selected(self, store) -> None:
		"""`Enter` from LIST: open the row and FOCUS the detail.

		Ruled by Slawomir, recorded late -- see
		`work/finding-human-console/FINDING.md` § "Enter from LIST enters
		DETAIL". From LIST focus this is analogous to a forward `Tab`.

		It also COMMITS a dwell that has not yet elapsed, on that exact
		message. The dwell exists so PASSIVE highlighting does not take
		ownership while someone scrolls past; a deliberate keystroke is not
		passive, and making the human wait two more seconds after pressing
		Enter would be ceremony for its own sake -- the thing this console's
		rulings keep removing.

		Focus moves only when the open SUCCEEDED. An empty list, a refused
		read or a lost claim race leaves focus in LIST rather than moving into
		a pane that cannot show what was asked for.
		"""
		if self.mode != MODE_BROWSE:
			return
		self.dwell = None
		# ALREADY OPEN: move focus and touch the store not at all. Reopening
		# would be a second read of content already on screen, and the ruled
		# contract says this transfer happens "without another claim".
		if self._already_open:
			self.focus = FOCUS_DETAIL
			return
		# THE OPEN REPORTS ITS OWN SUCCESS. Testing `self.detail is not None`
		# was wrong in exactly one case, and it is the case that matters: on a
		# LOST CLAIM RACE the open refreshes and PREVIEWS the row it could not
		# take, so `detail` becomes non-None while `opened` stays None -- and
		# Enter moved focus into a pane that cannot show the body the human
		# asked to enter, contradicting this method's own rule.
		#
		# A preview is not an open. Only the open can say whether it opened.
		if self.open_selected(store):
			self.focus = FOCUS_DETAIL

	def open_selected(self, store) -> bool:
		"""Open the selected row, taking ownership where that is what opening
		means.

		Reached BOTH by `Enter` and by `select_row`, which is what selection
		now calls. (It used to be the only action that took ownership; that is
		superseded for directed messages.) For a NOTICE it remains the only
		path, and Enter remains the only way to reach it.

		On a pending message it claims THAT exact row -- not the oldest, which
		is what `wait` would have done -- and only then loads content. On an
		already-claimed row it reopens without a second claim. On a notice it
		marks seen and returns content in one transaction.

		In the SENT view it takes ownership of nothing: that is your own
		outbound copy, and consuming it would take the message the recipient
		is waiting for."""
		if self.view == VIEW_SENT:
			return self.open_sent_selected(store)
		row = self.selected
		if row is None:
			return False
		self.external_text = {}
		if row["row_type"] == ROW_DRAFT:
			self.reopen_draft(row)
			return True
		if row["row_type"] == ROW_NOTICE and row.get("state") == "seen":
			# Already seen. NOT a content path: no write, no second receipt,
			# and no redelivery -- that is what at-most-once means, and the
			# screen has to SAY it rather than leave a reader thinking the
			# body is one keystroke away.
			#
			# The body loaded EARLIER in this session is kept if it is this
			# notice's: it is already in memory, and blanking it because the
			# poll ran would take away something the human is reading.
			if (self.detail or {}).get("notice", {}).get("id") != row["id"]:
				self.detail = {"notice": {**row, "already_seen": True,
				                          "content": None}}
			self.detail_row = (ROW_NOTICE, row["id"])
			self.detail_offset = 0
			self.opened = {"row_type": ROW_NOTICE, "id": row["id"], "claim_id": None}
			self.set_status(NOTICE_SEEN_STATUS, SEV_INFO)
			return True
		if row["row_type"] == ROW_NOTICE:
			result = self._guard(
				"open notice", lambda: store.mark_notice_seen(self.participant, row["id"]))
			if result is None:
				self.refresh(store)
				return False
			# Through the SAME envelope builder delivery uses. The raw rows
			# carry `body` bytes; the renderer speaks the typed envelope's
			# `text`/`encoding`, so handing it the raw shape drew every
			# notice as "(no retained bytes)" -- headers and no announcement.
			# It looked like a rendering nicety and was actually the content
			# never arriving.
			envelope = notice_delivery(result)["notice"]
			envelope["already_seen"] = result.get("already_seen", False)
			self.detail = {"notice": envelope}
			self.detail_row = (ROW_NOTICE, row["id"])
			# A notice has no claim, so nothing is actionable while it is open.
			self.opened = {"row_type": ROW_NOTICE, "id": row["id"], "claim_id": None}
			self.set_status(
				"already seen; not redelivered" if result["already_seen"]
				else "notice opened and marked seen",
				SEV_WARNING if result["already_seen"] else SEV_SUCCESS)
		elif row.get("direction") == "out":
			# MY OWN outbound copy: read-only, owner-checked on the SENDER.
			# It cannot be replied to or closed here -- that is the
			# recipient's obligation, and offering the keys would be offering
			# an action that must fail.
			result = self._guard(
				"open sent", lambda: store.open_sent(row["id"], self.participant))
			if result is None:
				return False
			self.detail = {"sent": result["sent"]}
			self.detail_row = (ROW_MESSAGE, row["id"])
			self.detail_offset = 0
			self.opened = self._follow_up_target(row, row.get("to_participant"))
			self.set_status(FOLLOW_UP_SENT, SEV_INFO)
			return True
		elif row["state"] not in ("pending", "claimed"):
			# Already dealt with. Reading it back must not claim, receipt or
			# transition anything -- it is terminal, and the whole point of
			# keeping the row is that the human can look at what they
			# answered.
			result = self._guard(
				"open", lambda: store.open_received(row["id"], self.participant))
			if result is None:
				return False
			self.detail = {"received": result["received"]}
			self.detail_row = (ROW_MESSAGE, row["id"])
			self.detail_offset = 0
			# NOT a dead end. Nothing is OWED -- the claim is resolved and `c`
			# and the disposition paths stay unavailable -- but the
			# conversation is still open, so `r`/`R` start a follow-up.
			self.opened = self._follow_up_target(row, row.get("from_participant"))
			self.set_status(FOLLOW_UP_ANSWERED, SEV_INFO)
			return True
		elif row["state"] == "pending":
			# Losing this race is ordinary -- another consumer took the exact
			# message between the refresh and the keystroke. Say so and
			# re-read; do not tear the console down over it.
			claim = self._guard(
				"claim", lambda: store.claim(self.participant, message_id=row["id"]))
			if claim is None:
				self.refresh(store)
				self.preview(store)
				return False
			# The claim COMMITTED. Even if reading it back fails, the human now
			# owes a reply or close, so the target is recorded first and the
			# obligation stays visible -- a claim behind a blank pane is still
			# a claim, and hiding it is how one gets abandoned.
			self.opened = {"row_type": ROW_MESSAGE, "id": row["id"],
			               "claim_id": claim["claim_id"]}
			delivery = self._guard(
				"open", lambda: store.reopen_claim(claim["claim_id"], self.participant))
			if delivery is None:
				self.detail = None
				self.detail_row = None
				self.set_status(
					f"claimed, but could not read it back: {self.last_error} — "
					f"it is yours and still owes a reply or close", SEV_ERROR)
				self.refresh(store)
				return False
			self.detail = {"delivery": delivery}
			self.detail_row = (ROW_MESSAGE, row["id"])
			self.set_status("claimed — reply or close is now owed", SEV_WARNING)
		else:
			self.opened = {"row_type": ROW_MESSAGE, "id": row["id"],
			               "claim_id": row["claim_id"]}
			delivery = self._guard(
				"reopen", lambda: store.reopen_claim(row["claim_id"], self.participant))
			if delivery is None:
				self.detail = None
				self.detail_row = None
				self.refresh(store)
				return False
			self.detail = {"delivery": delivery}
			self.detail_row = (ROW_MESSAGE, row["id"])
			self.set_status("reopened — reply or close is still owed", SEV_WARNING)
		detail = self.detail
		self.detail_offset = 0
		self.refresh(store)     # preserves and re-centres the target itself
		self.detail = detail
		return True

	def _follow_up_target(self, row: dict, other: str | None) -> dict | None:
		"""What `r`/`R` act on for a row whose claim is resolved, or which was
		never ours to claim.

		`claim_id` is None ON PURPOSE, and every disposition path keys off
		that: `_held_claim_id` returns None, so `c`, reply-as-disposition and
		materialize all refuse exactly as before. A follow-up is a NEW
		message, never a second disposition, and the safety authority stays
		the claim record rather than this dict or the message `kind`."""
		if not other:
			return None
		return {"row_type": ROW_MESSAGE, "id": row["id"], "claim_id": None,
		        "follow_up": {"to": other, "subject": row.get("subject"),
		                      "thread_id": row.get("thread_id")}}

	@property
	def follow_up_context(self) -> dict | None:
		"""The follow-up this console would author, or None."""
		return (self.opened or {}).get("follow_up")

	@staticmethod
	def reply_subject(subject: str | None) -> str:
		"""The original subject, EXACTLY. No `Re:` is ever added.

		Slawomir's ruling. `[R]` in SENT already exposes replied state and
		`responds_to`/`thread_id` carry the actual relationship, so a prefix
		would be decorative redundancy -- and subject churn in a long thread,
		where the same words drift by one prefix per hop.

		The human may still edit or replace the copied line in quick-reply
		mode; that is a deliberate act, which is exactly the difference.

		Returned EXACTLY, including any surrounding whitespace. The core
		rejects leading or trailing whitespace deliberately -- silently
		sanitizing misrepresents what the sender wrote -- so trimming here
		would hide a refusal the human is entitled to see, and would send
		something they did not type.

		SUPERSEDED: an earlier rule seeded `Re: ` exactly once,
		case-insensitively. It was implemented and pinned before this ruling."""
		return subject or ""

	def begin_reply(self) -> bool:
		"""`r`: reply to what is OPEN. `R` is the same intent, straight into
		the external editor.

		Three things wear the key, because they are one intent. On a live
		claim it is a DISPOSITION that resolves it. On a notice it cannot be:
		a broadcast has no claim to complete and `responds_to` references a
		message, so pretending otherwise would mean lying to the schema -- it
		becomes a new directed message to the author, and the receipt is left
		exactly as the open set it. On a row whose claim is already resolved,
		or one that was never ours to claim, it is a FOLLOW-UP: also a new
		message, also never a second disposition.

		This opens the QUICK path: the subject line, seeded with a copy of the
		original subject, is edited in place and becomes the content."""
		if self.opened is not None and self.opened.get("row_type") == ROW_NOTICE:
			return self._begin_notice_reply()
		if self.follow_up_context and not self._held_claim_id():
			return self._begin_follow_up()
		if not self._held_claim_id():
			self.set_status("nothing to reply to: claim the message first", SEV_WARNING)
			return False
		self.mode = MODE_REPLY
		# THE DRAFT IS THE SUBJECT. A quick reply is a one-line answer, and
		# the subject line is where that line goes -- it becomes the content
		# part through the subject-only shorthand. `R` opens the editor for
		# anything longer.
		envelope = ((self.detail or {}).get("delivery") or {}).get("message") or {}
		self.reply_blocked = None
		self.draft = self.reply_subject(envelope.get("subject"))
		# At the END of the seeded line: the human is continuing a subject,
		# not inserting before it.
		self.draft_caret = len(self.draft)
		self.reply_body = ""
		self.reply_body_requested = False
		# WHAT STARTED, not which keys work. The mode legend already lists
		# the controls, and status restating them was the same instruction in
		# two layers -- Slawomir's ruling names the footer as its owner.
		self.set_status(REPLY_STARTED, SEV_INFO)
		return True

	def _begin_follow_up(self) -> bool:
		"""A fresh directed message IN REFERENCE TO the opened one.

		Never a second disposition: the original claim is already resolved (or
		was never ours), and `messages.responds_to` is the relation -- which is
		exactly what "in reference to" names. The recipient is the OTHER
		party, taken from the row rather than from a picker, because the human
		said "follow up on this" and that answers who."""
		context = self.follow_up_context
		if not context:
			return False
		self.begin_compose(recipient=context["to"])
		self.compose_is_reply = True
		self.compose["subject"] = self.reply_subject(context.get("subject"))
		self.compose_carets["subject"] = len(self.compose["subject"])
		self.follow_up_to = self.opened["id"]
		self.follow_up_thread = context.get("thread_id")
		self.set_status(
			f"follow-up to {context['to']} — in reference to "
			f"\"{self.compose['subject']}\" — Enter reviews the send", SEV_INFO)
		return True

	def _begin_notice_reply(self) -> bool:
		"""A directed message to the notice's author, pre-addressed and
		pre-titled, with the caret in the SUBJECT.

		No picker and no subject traversal: the human said "reply to this",
		which answers both questions. Making them pick the author from a list
		they did not need would be asking a question whose answer is on
		screen.

		The caret starts in the SUBJECT -- there is no inline body field to
		put it in, and the subject line is what a quick reply says."""
		notice = (self.detail or {}).get("notice") or {}
		author = notice.get("from_participant")
		if not author:
			self.set_status("cannot reply: this notice has no author on record",
			                SEV_WARNING)
			return False
		self.begin_compose(recipient=author)
		self.compose_is_reply = True
		# EXACTLY the notice's subject. Not prefixed, not summarised: the
		# author identifies their broadcast by that line.
		self.compose["subject"] = self.reply_subject(notice.get("subject"))
		self.compose_carets["subject"] = len(self.compose["subject"])
		fields = self.compose_fields
		self.compose_field = fields.index("body") if "body" in fields else 0
		self.set_status(
			f"replying to {author} about \"{self.compose['subject']}\" — "
			f"Enter reviews the send", SEV_INFO)
		return True

	def abandon_fresh_reply(self) -> None:
		"""Undo a reply/follow-up that `R` had only just started.

		`R` from browse is ONE action: start the reply and open the editor. If
		the editor gives nothing back -- cancelled, unchanged, missing,
		non-zero, killed -- then that one action did nothing, and the human
		should be looking at the message they were reading. Leaving them in a
		quick-subject editor they never asked for is a DIFFERENT action from
		the one they took.

		This is the fresh case only. Ctrl-E from a draft that already exists
		keeps that draft, because there the editor is a step inside a
		composition the human deliberately started.

		The status is deliberately NOT touched: the editor's own explanation
		of what went wrong is the thing worth showing, and a cheerful
		"composition discarded" over the top of it would replace the reason
		with a summary."""
		if self.mode == MODE_REPLY:
			self.mode = MODE_BROWSE
			self.draft = ""
			self.draft_caret = 0
		elif self.mode in (MODE_COMPOSE, MODE_NOTICE):
			self.mode = MODE_BROWSE
			self.compose = {}
			self.compose_carets = {}
			self.compose_field = 0
			self.compose_is_reply = False
			self.follow_up_to = None
			self.follow_up_thread = None
		self.reply_body = ""
		self.reply_body_requested = False

	def cancel_reply(self) -> None:
		"""`Esc` RETAINS here too, and a reply draft keeps what it answers.

		Without the link a retained reply is a subject line with no context:
		reopening it would compose a NEW message rather than continue the
		answer, and the claim it was owed against would be unrelated to it.
		"""
		self._retain_draft()          # capture first; see `cancel_compose`
		self.mode = MODE_BROWSE
		self.draft = ""

	# `action_target_description` stood here and is REMOVED. It composed the
	# footer's `acting on ...` clause, and there is no such clause any more:
	# Slawomir ruled the ordinary bottom hints off the screen. What it
	# encoded is not lost -- whether a disposition is owed is
	# `affordances()["close"]`, why it is refused is `unavailable_reason`,
	# and what a follow-up would answer is `follow_up_context`. Those are the
	# facts; the sentence was one rendering of them.

	def send_reply(self, store, kind: str = "response") -> dict | None:
		"""Send the reply, resolve the claim, and advance.

		The body is the externally edited draft when there is one, otherwise
		the quick-reply subject line itself through the subject-only
		shorthand. The subject is the copied original, unchanged unless the
		human edited that line deliberately.

		Always a DISPOSITION through `store.reply`: this completes the claim.
		A directed reply that became an ordinary send would leave the
		obligation open while the screen said the reply had gone."""
		if self.reply_blocked:
			# BEFORE anything else, and before the emptiness checks. A
			# reopened reply whose claim went terminal has no claim to
			# resolve; falling through reported an EMPTY reply for a draft
			# that was not empty, which blamed the draft for a condition it
			# had nothing to do with and replaced the one useful warning.
			self.set_status(self.reply_blocked, SEV_WARNING)
			return None
		claim_id = self._held_claim_id()
		# EXACT. Empty means omitted; anything else goes to the core as typed,
		# so its validation is what the human sees rather than a quiet rewrite
		# on the way past.
		subject = _trimmed_subject(self.draft)
		# The externally edited body when there is one, otherwise the subject
		# line itself -- the same shorthand directed compose uses. Never a
		# zero-byte part.
		body = self.reply_body or self.draft
		if self.reply_body_requested and not self.reply_body:
			# They chose the full-body path and the editor came back empty.
			# Falling through to the subject line would send a different
			# message than the one they set out to write.
			self.set_status("the editor returned an empty body — nothing sent, "
			                "and the draft is unchanged", SEV_WARNING)
			return None
		if claim_id is None or not body:
			self.set_status("empty reply not sent", SEV_WARNING)
			return None
		result = self._guard("reply", lambda: store.reply(
			claim_id, participant=self.participant, kind=kind, subject=subject,
			body=body.encode("utf-8")))
		if result is None:
			# The draft is KEPT: the human typed it, the send failed, and
			# discarding their words because the authority was busy would be
			# the console losing work the protocol did not.
			self.refresh(store)
			return None
		recipient = ((self.detail or {}).get("delivery", {})
		             .get("message", {}).get("from_participant"))
		self.mode = MODE_BROWSE
		self._clear_committed_draft()
		self.draft = ""
		self.reply_body = ""
		self.reply_body_requested = False
		self._report_send(
			f"Sent: reply to {recipient} — claim resolved — o to view"
			if recipient else "replied — claim resolved")
		# Same ruling: the claim is resolved, so focus returns to the list.
		self._after_disposition(store)
		return result

	def close_selected(self, store, outcome: str | None = None) -> dict | None:
		claim_id = self._held_claim_id()
		if claim_id is None:
			self.set_status("nothing to close", SEV_WARNING)
			return None
		result = self._guard("close", lambda: store.close_claim(
			claim_id, participant=self.participant, outcome=outcome))
		if result is None:
			self.refresh(store)
			return None
		self.set_status("closed — claim resolved", SEV_SUCCESS)
		self._after_disposition(store)
		return result

	def _after_disposition(self, store) -> None:
		"""Shared tail of a SUCCESSFUL reply or close.

		The claim is resolved, so nothing in the detail pane is owed anything
		and keyboard focus belongs back on the queue -- otherwise the human
		presses `Tab` before every single next message, which is what Slawomir
		hit in packaged testing.

		Only ever called after the authority has committed. A refused or
		cancelled disposition must leave focus exactly where it was: moving it
		as though the action succeeded is a console telling the human something
		the store did not.

		THE CURSOR IS NOT MOVED. A correction asked for the next actionable row
		to be selected here; a standing trial ruling, pinned by
		`test_a_successful_reply_returns_focus_to_the_list`, says the row that
		was selected before the send is still selected after it. Both cannot
		hold, so this does the part they agree on -- focus returns to the list,
		and `refresh` restores the selection by identity onto the answered row,
		which is retained and is a sensible place to be. Advancing to the next
		obligation is deferred to whoever reconciles the two rulings, rather
		than shipped unused behind a flag nothing sets.
		"""
		self.focus = FOCUS_LIST
		self.opened = None
		self.refresh(store)
		self.preview(store)

	def _held_claim_id(self) -> str | None:
		"""The claim a state-changing action applies to: the OPENED one.

		Never the cursor. That was the bug."""
		if self.opened is None or self.opened["row_type"] != ROW_MESSAGE:
			return None
		claim_id = self.opened["claim_id"]
		if claim_id is None:
			return None
		# Still held, and still by us -- the row list is the console's own view
		# and may be stale.
		for row in self.rows:
			if row.get("claim_id") == claim_id and row["state"] == "claimed":
				return claim_id
		return None

	# -- choosing a recipient ---------------------------------------------

	def begin_pick_recipient(self, store) -> None:
		"""`n` opens the picker, not a free-text field.

		Typing an address is a typo waiting to happen: the mistake is only
		caught at send time, by which point the human has written the whole
		message. Selection cannot produce an address that does not exist."""
		everyone = self._guard("list participants", store.list_participants)
		if everyone is None:
			return
		self.recipients = [entry for entry in everyone]
		self.picker_page = 0
		self.mode = MODE_PICK_RECIPIENT
		# WHAT is happening. The keys were a second copy of the picker's own
		# legend, and there is no legend on screen any more -- `?` help owns
		# them, and status is for what the console did.
		self.set_status("choosing a recipient", SEV_INFO)

	@property
	def picker_page_size(self) -> int:
		"""How many recipients actually FIT the picker pane right now.

		Paging by the 26 available letters was wrong: at 100x24 with the live
		21-participant config only 18 rows fit, so `s`, `t` and `u` were
		labelled and selectable but never drawn. A shortcut the human cannot
		see is worse than one that does not exist -- it is a hidden control on
		a screen that claims to list everything.

		The capacity comes from the renderer through `set_viewport`, because
		only it knows how many rows the prompt occupied after wrapping at this
		width -- a fixed reserve under-counts on a narrow pane."""
		return max(1, min(len(PICKER_LABELS), self.picker_capacity))

	@property
	def picker_pages(self) -> int:
		return max(1, -(-len(self.recipients) // self.picker_page_size))

	def picker_entries(self) -> list[tuple[str, dict]]:
		"""(label, participant) for the current page. Every configured
		participant is reachable on exactly one page, and every entry returned
		here is one the renderer will actually draw."""
		size = self.picker_page_size
		page_index = min(self.picker_page, self.picker_pages - 1)
		start = page_index * size
		return list(zip(PICKER_LABELS, self.recipients[start:start + size]))

	def picker_next_page(self, delta: int = 1) -> None:
		self.picker_page = (self.picker_page + delta) % self.picker_pages

	def follow_line(self, line_index: int, total_lines: int) -> None:
		"""Keep one detail line on screen.

		Two callers, one rule. Compose and reply modes cannot have scroll keys
		-- every printable key is text -- so a draft that grows past the pane
		would scroll its own caret out of sight, leaving the human typing into
		a line they cannot see. Part selection has the same shape: `[`/`]`
		move a mark, and a mark below the fold is a cursor the human cannot
		find. The driver reports where the line landed and this brings it back
		into the window.

		Named for the LINE rather than for input since the stacked layout gave
		it a second caller: a helper that says "input" while scrolling to a
		part header is a comment that lies at the call site."""
		if line_index < 0:
			return
		window = max(1, self.detail_height)
		if line_index < self.detail_offset:
			self.detail_offset = line_index
		elif line_index >= self.detail_offset + window:
			self.detail_offset = line_index - window + 1
		self.detail_offset = max(0, min(self.detail_offset,
		                                max(0, total_lines - window)))

	def pick_recipient(self, label: str):
		"""A letter selects immediately. Returns the chosen address, or None
		if that letter is not on this page."""
		for entry_label, entry in self.picker_entries():
			if entry_label == label:
				self.begin_compose(recipient=entry["address"])
				return entry["address"]
		return None

	def cancel_picker(self) -> None:
		self.mode = MODE_BROWSE
		self.recipients = []
		self.set_status("recipient selection cancelled", SEV_INFO)

	# -- the attachment: two values, checked before they become one -------

	def attachment_locator(self) -> str | None:
		"""`root_id:relative/path` for the core call, or None when there is
		no attachment. The ONLY place this form is constructed, and it is
		never displayed.

		The path is passed EXACTLY as typed. It used to be `.strip()`ed, which
		meant a draft displaying ` report.md ` could publish `report.md` -- a
		different file from the one on screen. The root id is picker-owned, so
		normalising THAT is safe; a typed path is the human's."""
		root = (self.compose.get("attach_root") or "").strip()
		path = self.compose.get("attach_path") or ""
		if not root or not path:
			return None
		return f"{root}:{path}"

	def attachment_error(self) -> str | None:
		"""Why this attachment cannot be sent, in the words the human needs,
		or None when it can.

		PREFLIGHT, NOT AUTHORITY. Core verifies and hash-pins the file at
		publication, and it must keep doing so: the file can change or vanish
		between this check and the send, and a console that treated its own
		earlier look as proof would report a message sent that the authority
		refused. What this buys is a refusal the human can act on BEFORE they
		have composed the rest of a message.

		So it MIRRORS core's rules rather than inventing gentler ones. Core
		requires a clean relative path -- no empty, `.` or `..` component --
		and walks every component with `O_NOFOLLOW`, refusing any symlink even
		when it points somewhere legal. A `join` + `realpath` check accepts
		`sub/../file`, `./file`, doubled separators and an in-root symlink,
		all of which core then refuses: a preflight that predicts a different
		answer is worse than none, because it teaches the human that a path is
		fine and lets the refusal arrive after they have written the message.

		Every refusal leaves the chosen root, the typed path and the focus
		exactly as they are."""
		import os
		import stat as stat_module
		root = (self.compose.get("attach_root") or "").strip()
		path = self.compose.get("attach_path") or ""
		if not root and not path:
			return None                     # no attachment is not an error
		if not root:
			return "choose an attachment root first — Enter on the path field"
		if not path:
			return f"root {root} is chosen; the path within it is empty"
		if path != path.strip():
			# NOT trimmed silently: trimming would attach a different file
			# from the one displayed. Named so the human can see what is
			# there, because whitespace is invisible.
			return "the path has leading or trailing whitespace; remove it"
		if os.path.isabs(path):
			return ("the path is relative to the chosen root — "
			        f"drop the leading {os.sep!r}")
		head = path.split("/")[0]
		if ":" in head and head.split(":")[0] in self._root_ids():
			# Baton's own locator typed into the field. Diagnosed ONLY when
			# the prefix names a configured root: `notes:2026.md` is a legal
			# filename and core accepts it, so treating every colon as
			# serialization would refuse a file the authority allows.
			return "this field takes a path INSIDE the chosen root, not root:path"
		components = path.split("/")
		if any(component in ("", ".", "..") for component in components):
			return (f"{path!r} must be a clean relative path: no empty, '.' or "
			        f"'..' components")
		base = self._root_path(root)
		if base is None:
			return f"{root} is not a configured attachment root"
		# Component-wise, no-follow, exactly as core walks it. A symlink
		# anywhere on the way -- including one that lands on a regular file
		# inside the same root -- is refused, because core refuses it.
		try:
			fd = os.open(base, os.O_DIRECTORY | os.O_CLOEXEC)
		except OSError as exc:
			return f"{root} cannot be opened: {exc.strerror or exc}"
		try:
			for component in components[:-1]:
				try:
					nxt = os.open(component, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
					              dir_fd=fd)
				except OSError as exc:
					# WHAT IT IS, not which errno the open produced. A
					# symlink-to-directory refused by O_NOFOLLOW reports
					# ENOTDIR on Linux and ELOOP elsewhere, and either way
					# "not a directory" is useless to someone looking at what
					# is plainly a folder. `lstat` on the same descriptor,
					# which does not follow, answers it portably -- and
					# without importing `errno`, which the packaging guard
					# would rightly ask about for a message string.
					link = False
					try:
						link = stat_module.S_ISLNK(
							os.lstat(component, dir_fd=fd).st_mode)
					except OSError:
						pass
					os.close(fd)
					if link:
						return f"{component} is a symlink; core refuses those"
					if isinstance(exc, FileNotFoundError):
						return f"no such file inside {root}: {path}"
					if isinstance(exc, NotADirectoryError):
						return f"{component} is not a directory"
					return f"{path} cannot be read: {exc.strerror or exc}"
				os.close(fd)
				fd = nxt
			try:
				leaf = os.open(components[-1],
				               os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
				               dir_fd=fd)
			except OSError as exc:
				link = False
				try:
					link = stat_module.S_ISLNK(
						os.lstat(components[-1], dir_fd=fd).st_mode)
				except OSError:
					pass
				if link:
					return f"{path} is a symlink; core refuses those"
				if isinstance(exc, FileNotFoundError):
					return f"no such file inside {root}: {path}"
				return f"{path} cannot be read: {exc.strerror or exc}"
			try:
				info = os.fstat(leaf)
				if not stat_module.S_ISREG(info.st_mode):
					return f"{path} is not a regular file"
				try:
					os.read(leaf, 1)
				except OSError as exc:
					return f"{path} cannot be read: {exc.strerror or exc}"
			finally:
				os.close(leaf)
		finally:
			try:
				os.close(fd)
			except OSError:
				pass
		return None

	def _root_ids(self) -> set:
		"""Every root id this session has been told about."""
		return {entry.get("root_id") for entry in
		        (self.roots or []) + (self.known_roots or [])}

	def _root_path(self, root_id: str) -> str | None:
		"""The absolute base of a configured root, from whatever the picker
		last listed. Kept so a refusal can be computed without a store."""
		for entry in (self.roots or []) + (self.known_roots or []):
			if entry.get("root_id") == root_id:
				return entry.get("path")
		return None

	# -- choosing the root an attachment is named against ------------------

	def begin_pick_root(self, store) -> bool:
		"""Enter on an EMPTY `attach` field opens this instead of reviewing
		the send.

		The human never types Baton's `root_id:relative/path` locator -- that
		is a serialization, and asking someone to learn it is asking them to
		do the adapter's job. They choose a configured ROOT, seeing its name
		and where it points, and then say where inside it the file is. The
		boundary is visible at the moment it is being relied on.

		Returns False when there is nothing to choose from, so the caller can
		fall through rather than opening an empty picker."""
		roots = self._guard("list roots", store.list_roots)
		if roots is None:
			return False
		if not roots:
			self.set_status("no attachment roots are configured for this "
			                "instance", SEV_WARNING)
			return False
		self.roots = list(roots)
		self.known_roots = list(roots)
		self.picker_page = 0
		self.compose_return_mode = self.mode
		self.mode = MODE_PICK_ROOT
		self.set_status("choosing an attachment root", SEV_INFO)
		return True

	@property
	def root_pages(self) -> int:
		return max(1, -(-len(self.roots) // self.picker_page_size))

	def root_entries(self) -> list[tuple[str, dict]]:
		"""(label, root) for the current page, drawn by the same rules the
		recipient picker uses -- letters select, Tab pages, Esc cancels."""
		size = self.picker_page_size
		page_index = min(self.picker_page, self.root_pages - 1)
		start = page_index * size
		return list(zip(PICKER_LABELS, self.roots[start:start + size]))

	def pick_root(self, label: str):
		"""A letter selects immediately. Returns the chosen root id, or None
		if that letter is not on this page.

		Changing the root KEEPS the path only while it is still valid there.
		A path that no longer resolves stays visible and editable rather than
		being silently dropped -- the human typed it, and it may be one
		character from correct."""
		for entry_label, entry in self.root_entries():
			if entry_label != label:
				continue
			self.compose["attach_root"] = entry["root_id"]
			self.mode = self.compose_return_mode or MODE_COMPOSE
			self.roots = []
			path = self.compose.get("attach_path", "")
			if path and self.attachment_error():
				self.set_status(
					f"root is {entry['root_id']} — the path no longer resolves "
					f"there; correct it before sending", SEV_WARNING)
			else:
				self.set_status(f"root is {entry['root_id']} ({entry['path']})",
				                SEV_INFO)
			return entry["root_id"]
		return None

	def cancel_root_picker(self) -> None:
		"""Back to the draft, which is untouched -- including any root and
		path already chosen."""
		self.mode = self.compose_return_mode or MODE_COMPOSE
		self.roots = []
		self.set_status("root selection cancelled", SEV_INFO)

	# -- composing new traffic --------------------------------------------

	def begin_compose(self, notice: bool = False, recipient: str | None = None) -> None:
		"""`n` for a new directed message, `N` to publish a notice. Both are
		first-class here rather than "go and use the CLI": a console that
		sends you elsewhere for half the protocol is not a console."""
		self.mode = MODE_NOTICE if notice else MODE_COMPOSE
		self.compose = {field: "" for field in
		                (NOTICE_FIELDS if notice else COMPOSE_FIELDS)}
		# Each field remembers its own caret, so switching away and back does
		# not silently jump to the end of what you were writing.
		self.compose_carets = {field: 0 for field in self.compose}
		# A new composition is NOT a reply until something says so, and it is
		# in reference to nothing until `_begin_follow_up` says otherwise.
		self.compose_is_reply = False
		self.follow_up_to = None
		self.follow_up_thread = None
		if recipient is not None:
			# Chosen, not typed. Held outside the editable fields so there is
			# no free-form path back to a typo.
			self.compose["to"] = recipient
		self.compose_field = 0
		# WHAT started, and to whom. The send shorthand is a key workflow and
		# belongs to `?` help and the README, not to a second copy of the
		# footer that competes with the actual event this bar reports.
		self.set_status("composing a notice" if notice else
		                f"composing a message to {self.compose.get('to', '')}".rstrip(),
		                SEV_INFO)

	@property
	def compose_field_name(self) -> str:
		"""Which field the caret is in, by NAME. The driver needs it to route
		Enter on the empty attach path to the root picker, and an index into
		a tuple that differs between compose and notice is not something a
		call site should be reconstructing."""
		fields = self.compose_fields
		if not fields:
			return ""
		return fields[min(self.compose_field, len(fields) - 1)]

	@property
	def compose_fields(self) -> tuple:
		"""Editable fields. `to` is NOT among them for a directed message: it
		was selected from the registry and is displayed read-only."""
		return NOTICE_FIELDS if self.mode == MODE_NOTICE else COMPOSE_EDITABLE

	def compose_next_field(self, delta: int = 1) -> None:
		fields = self.compose_fields
		self.compose_field = (self.compose_field + delta) % len(fields)

	# -- one caret model, shared by every editable buffer -----------------

	@property
	def _active_field(self) -> str | None:
		"""Which compose field the caret is in, or None while replying."""
		if self.mode == MODE_REPLY:
			return None
		fields = self.compose_fields
		return fields[self.compose_field] if fields else None

	def _read_buffer(self) -> tuple:
		field = self._active_field
		if field is None:
			return self.draft, self.draft_caret
		return self.compose.get(field, ""), self.compose_carets.get(field, 0)

	def _write_buffer(self, text: str, caret: int) -> None:
		caret = max(0, min(len(text), caret))
		field = self._active_field
		if field is None:
			self.draft, self.draft_caret = text, caret
		else:
			self.compose[field] = text
			self.compose_carets[field] = caret

	def type_char(self, char: str) -> None:
		"""Insert AT THE CARET, not at the end."""
		text, caret = self._read_buffer()
		caret = max(0, min(len(text), caret))
		self._write_buffer(text[:caret] + char + text[caret:], caret + len(char))

	def backspace(self) -> None:
		"""Delete the character BEFORE the caret."""
		text, caret = self._read_buffer()
		caret = max(0, min(len(text), caret))
		if caret == 0:
			return
		self._write_buffer(text[:caret - 1] + text[caret:], caret - 1)

	def delete_forward(self) -> None:
		"""Delete the character UNDER the caret. Distinct from backspace: at
		the start of a line one does nothing and the other still deletes."""
		text, caret = self._read_buffer()
		caret = max(0, min(len(text), caret))
		if caret >= len(text):
			return
		self._write_buffer(text[:caret] + text[caret + 1:], caret)

	def kill_to_start(self) -> None:
		"""`Ctrl-U`: delete from the caret back to the start of the buffer.

		The readline spelling, and Slawomir's ruling. Everything AT and after
		the caret survives -- with the caret at the end that is nothing, so it
		clears the line, which is what people press Ctrl-U for. In BROWSE the
		same key still pages the list: the text modes are a separate key
		table, which is what lets one chord mean two things without a guard."""
		text, caret = self._read_buffer()
		caret = max(0, min(len(text), caret))
		self._write_buffer(text[caret:], 0)

	def move_caret(self, delta: int) -> None:
		text, caret = self._read_buffer()
		self._write_buffer(text, caret + delta)

	def caret_home(self) -> None:
		text, _ = self._read_buffer()
		self._write_buffer(text, 0)

	def caret_end(self) -> None:
		text, _ = self._read_buffer()
		self._write_buffer(text, len(text))

	@property
	def caret(self) -> int:
		"""Where the caret is in the buffer being edited."""
		return self._read_buffer()[1]

	# The names the driver already used.
	def compose_type(self, char: str) -> None:
		self.type_char(char)

	def compose_backspace(self) -> None:
		self.backspace()

	def cancel_compose(self) -> None:
		"""`Esc` RETAINS. It used to discard the whole composition.

		Escape is the key people press to back out of anything, so making it
		also the most destructive key on the console meant a reflex could cost
		someone a message they had been writing for ten minutes. Discarding is
		now `D`, and it asks.
		"""
		# CAPTURE FIRST. An earlier version set the mode to browse and then
		# retained, so the snapshot looked at a state that was no longer
		# composing anything and concluded there was nothing to keep -- the
		# retention silently did nothing, which is the exact bug it exists to
		# prevent, wearing a different hat.
		self._retain_draft()
		self.mode = MODE_BROWSE
		self.compose = {}
		self.compose_field = 0

	def _report_send(self, success: str) -> None:
		"""Say what happened, INCLUDING a cleanup that did not.

		A send whose draft could not be removed is still a send -- reporting
		it as a failure would invite a retry that publishes a second copy --
		but it is not an ordinary success either, and the human has to know
		the draft may come back.
		"""
		warning = self.draft_cleanup_warning
		self.draft_cleanup_warning = None
		if warning:
			self.set_status(warning, SEV_WARNING)
			return
		self.set_status(success, SEV_SUCCESS)

	def _clear_committed_draft(self) -> None:
		"""Remove the draft that was just published, and only that one.

		Called ONLY after the authority has committed. A refused send leaves
		every draft exactly as it was -- which is the whole point of retaining
		them, and is why this is not in a `finally`.
		"""
		target = self.draft_id
		self.draft_id = None
		if not target:
			return
		remaining = [d for d in self.drafts if d.get("id") != target]
		if len(remaining) == len(self.drafts):
			return
		self.drafts = remaining
		try:
			self._persist_drafts()
		except DraftError as error:
			# THE MESSAGE WENT. Reporting a failed send would be false and
			# would invite a retry that publishes a second copy -- so the send
			# is still a success and is still reported as one.
			#
			# But a clean success is also false: the draft is still on disk,
			# and a restart would show it as unsent and let the human publish
			# it again. So the outcome is recorded and the caller appends it
			# to the status, and the in-memory list no longer contains it, so
			# nothing in THIS session can resend it.
			self.draft_cleanup_warning = (
				f"sent, but the draft could not be cleared ({error}) — "
				f"it may reappear on restart; discard it with D")

	def _draft_from_state(self) -> dict | None:
		"""The complete authoring state, as a plain dict.

		Plain data, not a live reference into `self.compose`: a retained draft
		must be a SNAPSHOT, or clearing the compose buffers afterwards would
		empty the draft that was just kept.

		Returns None when there is nothing worth keeping. "Worth keeping" is
		any authored TEXT -- a recipient alone is a picker selection, not a
		message, and retaining it would leave a row that says nothing.
		"""
		if self.mode == MODE_REPLY:
			subject, body = self.draft, self.reply_body
			answering = (self.opened or {}).get("id")
			kind = "reply"
			recipient = ""
			attach = ""
		elif self.mode in (MODE_COMPOSE, MODE_NOTICE):
			subject = self.compose.get("subject", "")
			body = self.compose.get("body", "")
			recipient = self.compose.get("to", "")
			attach = self.compose.get("attach_path", "")
			answering = self.follow_up_to
			kind = "notice" if self.mode == MODE_NOTICE else "compose"
		else:
			return None
		if not (subject.strip() or body.strip() or attach.strip()):
			return None
		return {"id": self._draft_id(answering, kind),
		        "kind": kind, "subject": subject, "body": body,
		        "to": recipient, "attach_path": attach, "answering": answering,
		        "is_reply": bool(self.compose_is_reply or kind == "reply")}

	def _draft_id(self, answering, kind: str) -> str:
		"""One draft per thing being answered; new messages get their own.

		A reply draft is identified by WHAT IT ANSWERS, so re-opening the same
		message and backing out again updates the one draft rather than
		growing a pile of near-identical rows. A fresh composition answers
		nothing, so it keeps whichever id it was already carrying and only
		takes a new one when it is genuinely new.
		"""
		if answering:
			return f"{kind}:{answering}"
		existing = getattr(self, "draft_id", None)
		if existing:
			return existing
		# SKIP ANYTHING ALREADY TAKEN. `draft_serial` starts at zero in every
		# new state, so after a restart the first fresh composition would
		# otherwise be handed `compose:new:1` again -- and `_replace_draft`
		# would treat it as the loaded draft of that name and overwrite it.
		# Silent data loss, and it is what this loop exists to prevent.
		#
		# Checked against the LIST rather than by reserving serials at load
		# time. Both work for a file this console wrote; only this one works
		# for a file whose serials are sparse or hand-edited, and having two
		# mechanisms meant neither could be tested -- removing either left the
		# regression passing.
		taken = {draft.get("id") for draft in self.drafts}
		while True:
			self.draft_serial = getattr(self, "draft_serial", 0) + 1
			candidate = f"{kind}:new:{self.draft_serial}"
			if candidate not in taken:
				return candidate

	def _replace_draft(self, draft: dict) -> None:
		"""Insert or update by id, preserving position.

		Updating in place rather than moving the row to the end: a draft that
		jumped down the list every time it was touched would be somewhere new
		each time the human came back to it.
		"""
		for index, existing in enumerate(self.drafts):
			if existing.get("id") == draft["id"]:
				self.drafts[index] = draft
				return
		self.drafts.append(draft)

	def _persist_drafts(self) -> None:
		"""Write the list, or raise `DraftError`. No authority contact."""
		draft_store.save(self.projection_dir, self.participant, self.drafts)

	def reopen_draft(self, row: dict) -> None:
		"""Continue a retained draft, in the mode it was written in.

		The COMPLETE authoring state comes back -- subject, body, recipient,
		attachment and what it answers -- because a draft that reopens missing
		its recipient or its reply link is not the message that was kept, and
		the human would have to notice what is missing before sending it.

		Opening a draft takes no ownership of anything. It is local text; the
		claim a reply draft was written against is not re-claimed, and if that
		claim is gone the send will say so at send time rather than here.
		"""
		draft = row.get("draft") or {}
		# FIRST, so a warning raised while reattaching survives. Set at the
		# end it overwrote "that claim is no longer held", which is the one
		# thing the human most needs to read here.
		self.set_status("draft reopened", SEV_INFO)
		self.draft_id = draft.get("id")
		self.follow_up_to = draft.get("answering")
		self.compose_is_reply = bool(draft.get("is_reply"))
		if draft.get("kind") == "reply":
			self.mode = MODE_REPLY
			self.draft = draft.get("subject", "")
			self.draft_caret = len(self.draft)
			self.reply_body = draft.get("body", "")
			self.reply_body_requested = bool(self.reply_body)
			# RESTORE WHAT IT ANSWERS. `send_reply` resolves its target
			# through `_held_claim_id`, which reads `opened` -- so after a
			# restart a reopened reply had a subject, a body and no way to be
			# sent: the claim was still active in the authority and the
			# console could not see it.
			#
			# By the ANSWERED MESSAGE ID, never by the cursor. The human may
			# be anywhere in the list; aiming a reply at the highlighted row
			# is the wrong-target bug this console has already had once.
			self._reattach_reply(draft.get("answering"))
		else:
			self.mode = MODE_NOTICE if draft.get("kind") == "notice" \
				else MODE_COMPOSE
			self.compose = {"subject": draft.get("subject", ""),
			                "body": draft.get("body", ""),
			                "to": draft.get("to", ""),
			                "attach_path": draft.get("attach_path", "")}
			self.compose_carets = {name: len(value)
			                       for name, value in self.compose.items()}
			self.compose_field = 0

	def _reattach_reply(self, answering) -> None:
		"""Point `opened` back at the message a reply draft answers.

		Only when THIS participant still holds an active claim on it.

		BOTH other outcomes REFUSE, identically and out loud: a claim that went
		terminal while the console was away, and a message that is no longer
		listed at all. The draft keeps its `answering` link and is retained and
		reopened so the words can be copied out or the row discarded
		deliberately -- what it cannot do is send, and the console says so
		rather than promising a follow-up it will not perform.

		(An earlier version of this sentence said a terminal draft stayed
		available for the ruled follow-up path. It did not: the state had no
		claim, `send_reply` could not follow up from there, and the send
		reported an EMPTY reply for a draft that was not empty.)

		What must never happen in any branch is the reply quietly becoming an
		unrelated new message aimed at whatever is under the cursor.
		"""
		self.opened = None
		self.reply_blocked = None
		if not answering:
			return
		for row in self.rows:
			if row.get("row_type") != ROW_MESSAGE or row.get("id") != answering:
				continue
			if row.get("state") == "claimed" and row.get("claim_id"):
				self.opened = {"row_type": ROW_MESSAGE, "id": row["id"],
				               "claim_id": row["claim_id"]}
			else:
				# A TRUTHFUL REFUSAL, not a promise. An earlier version said
				# "this will go as a follow-up" and then left the state in
				# reply mode with no claim, where `send_reply` cannot follow
				# up at all: pressing send returned nothing and reported an
				# EMPTY reply for a draft that was not empty. Two false
				# statements in a row about the same draft.
				#
				# The draft is kept and reopened so the words can be copied
				# out or the row discarded deliberately; what it cannot do is
				# send, and it says so.
				self.reply_blocked = (
					"that claim is no longer held — this draft cannot be "
					"sent as a reply; it is kept, and D discards it")
				self.set_status(self.reply_blocked, SEV_WARNING)
			return
		# THE SAME TRUTHFUL REFUSAL. This branch was left setting only a
		# status, so a send still fell through to the emptiness tests and
		# called a non-empty draft empty -- the identical fault as the
		# terminal-claim branch, one `return` away from it, and fixed there
		# alone the first time.
		self.reply_blocked = (
			"the message this answers is no longer listed — this draft cannot "
			"be sent as a reply; it is kept, and D discards it")
		self.set_status(self.reply_blocked, SEV_WARNING)


	def discard_draft(self, confirmed: bool) -> bool:
		"""`D` then `y`. Returns True when a draft was discarded.

		Default NO, and `Enter` counts as no. `Enter` is the affirmative key
		everywhere else on this console, which is exactly why it must not be
		here: a confirmation whose default is destructive is a slower way of
		not asking.
		"""
		self.mode = MODE_BROWSE
		target = getattr(self, "discard_target", None)
		self.discard_target = None
		if not confirmed or target is None:
			self.set_status("kept", SEV_INFO)
			return False
		before = len(self.drafts)
		self.drafts = [d for d in self.drafts if d.get("id") != target]
		if len(self.drafts) == before:
			self.set_status("that draft is already gone", SEV_WARNING)
			return False
		if self.draft_id == target:
			self.draft_id = None
		try:
			self._persist_drafts()
		except DraftError as error:
			self.set_status(f"discarded here, not on disk: {error}", SEV_WARNING)
			return True
		self.set_status("draft discarded", SEV_SUCCESS)
		return True

	def begin_discard_draft(self) -> bool:
		"""Arm the confirmation, but ONLY on a draft row.

		`D` on a message, a notice or a sent row does nothing at all -- not a
		different destructive act, and not a confirmation the human has to
		decline. A key that is destructive on one row type and silently
		harmless on another is only safe if the harmless case is genuinely
		silent about destruction.
		"""
		row = self.selected
		if row is None or row.get("row_type") != ROW_DRAFT:
			self.set_status("no draft selected", SEV_INFO)
			return False
		self.discard_target = row["id"]
		self.mode = MODE_CONFIRM_DISCARD
		return True

	def load_drafts(self) -> None:
		"""Read retained drafts at startup.

		Every failure is NON-FATAL and reported. A console that refused to
		start because a draft file was unreadable would deny the human their
		mailbox over their own unsent notes -- and an unconfigured
		`projection_dir` is not an error at all until they try to keep
		something.
		"""
		self.drafts = []
		try:
			self.drafts = draft_store.load(self.projection_dir, self.participant)
		except DraftError as error:
			if self.projection_dir:
				self.set_status(f"drafts unavailable: {error}", SEV_WARNING)

	def _retain_draft(self) -> None:
		"""Keep what is being composed, and say where it went.

		An EMPTY composition is not retained: a draft row for a message with
		no subject, no body and no recipient is a row that says nothing and
		has to be discarded by hand. Backing straight out of a compose the
		human opened by mistake should leave no trace.

		Persistence failure is REPORTED and the draft is still kept in memory
		for this session. Losing the words because the disk was full would be
		the same harm the retention exists to prevent, and a console that says
		"discarded" when it meant "could not save" is lying about which.
		"""
		draft = self._draft_from_state()
		if draft is None:
			self.set_status("nothing to keep", SEV_INFO)
			return
		self._replace_draft(draft)
		try:
			self._persist_drafts()
		except DraftError as error:
			self.set_status(f"draft kept for this session only: {error}",
			                SEV_WARNING)
			return
		self.set_status("draft kept — D discards it", SEV_INFO)

	def send_compose(self, store, kind: str = "message"):
		"""Publish what was composed. An `attach` of `ROOT:path` rides as an
		external part beside the body, which is what protocol 9 made possible
		-- the explanation and its evidence in one message.

		WHAT COUNTS AS CONTENT. Protocol 9 requires a message to have content,
		and an external attachment IS a content leaf. So an attachment with no
		body is a valid message and sends the external leaf ALONE -- adding an
		empty inline text leaf to satisfy a check would put a part on the wire
		that the sender did not write.

		Emptiness is tested WITHOUT `strip()`. A whitespace-only body is
		non-empty protocol content: the store accepts those bytes, and a
		console that silently refuses them disagrees with the authority it is
		a front end for. Indentation and blank lines are content in Markdown,
		which is what this body is declared as."""
		notice = self.mode == MODE_NOTICE
		body = self.compose.get("body", "")
		subject = _trimmed_subject(self.compose.get("subject", ""))
		recipient = self.compose.get("to", "").strip()
		self.compose_recipient = recipient
		if notice:
			# Notices expose no attachment field, so a body is the only
			# content they can carry -- but the one-line shorthand applies
			# here too, approved for consistency with directed compose: a
			# subject alone becomes the content part as well as the subject.
			# A zero-byte part is still never published.
			if not body:
				if not subject:
					self.set_status("nothing to send: no subject or body",
					                SEV_WARNING)
					return None
				body = subject
			result = self._guard("publish notice", lambda: store.send_notice(
				self.participant, kind="announcement", subject=subject,
				body=body.encode("utf-8")))
		else:
			if not recipient:
				self.set_status("nothing sent: no recipient", SEV_WARNING)
				return None
			# The serialization is built HERE, at the boundary, from the two
			# values the human actually chose and typed. It is the only place
			# `root:path` exists, and it never reaches the screen.
			refusal = self.attachment_error()
			if refusal:
				self.set_status(refusal, SEV_WARNING)
				return None
			attach = self.attachment_locator()
			if not body and not attach:
				if not subject:
					# Nothing at all. A message needs SOMETHING to say.
					self.set_status("nothing to send: no subject, body or "
					                "attachment", SEV_WARNING)
					return None
				# ONE-LINE SHORTHAND. A quick message should not cost a Tab
				# and a retype: the subject line becomes the content part as
				# well as the subject. It is the same words either way, and
				# the alternative -- a zero-byte placeholder part -- would put
				# an empty leaf on the wire and make the message unreadable to
				# anything that renders content rather than headers.
				body = subject
			parts = []
			if body:
				parts.append({"content_type": "text/markdown; charset=utf-8",
				              "body": body.encode("utf-8")})
			if attach:
				parts.append({"disposition": "attachment", "attach": attach})
			self.compose_recipient = recipient
			# A FOLLOW-UP carries the relation and inherits the thread, and
			# says so in `kind`. `kind` is DESCRIPTIVE: the claim and
			# disposition records remain the safety authority, and list
			# threading derives from `responds_to`, never from this word.
			if self.follow_up_to:
				kind = KIND_FOLLOW_UP
			result = self._guard("send", lambda: store.send(
				self.participant, recipient, kind=kind, subject=subject,
				parts=parts, responds_to=self.follow_up_to,
				thread_id=self.follow_up_thread))
		if result is None:
			# Buffers kept so nothing is retyped -- and the retained draft is
			# untouched. A refused send must leave every draft exactly as it
			# was; that is the whole reason they are retained.
			return None
		followed = self.follow_up_to
		self.follow_up_to = None
		self.follow_up_thread = None
		self.mode = MODE_BROWSE
		self._clear_committed_draft()
		self.compose = {}
		self.compose_field = 0
		# Stay in the INBOX -- the human's next action is almost never about
		# the thing they just sent -- but say where it went and how to look.
		# A confirmation that vanishes on the next repaint is a confirmation
		# nobody sees.
		if notice:
			said = f"Sent: {subject or '(no subject)'} to everyone (notice) — o to view"
		elif followed:
			# Says what did NOT happen as well as what did: a follow-up leaves
			# the original's badge and disposition exactly where they were,
			# and that is the property most worth stating out loud.
			said = (f"Sent: follow-up to {self.compose_recipient or recipient} — "
			        f"the original is unchanged")
		else:
			said = (f"Sent: {subject or '(no subject)'} to "
			        f"{self.compose_recipient or recipient} — o to view")
		# The send SUCCEEDED, so that piece of work is finished and the
		# natural next action is another message -- Slawomir's trial ruling.
		# Focus goes back to the LIST; the selected row, the visible detail
		# and this status all stay exactly as they are, and nothing is read
		# or written to say so. A FAILED send never reaches here, which is
		# the point: it leaves the human where they were, with their draft.
		self.focus = FOCUS_LIST
		self._report_send(said)
		self.refresh(store)
		self.preview(store)
		return result

	# -- quitting with work outstanding -----------------------------------

	def arm_send(self) -> bool:
		"""Enter no longer publishes. It asks.

		Compose opens focused on the subject and a subject alone is now
		enough, so Enter became a one-keystroke publish reachable from a field
		a newcomer is still filling in -- and Enter is the key people press to
		mean "next field". The quick path is still two strokes -- Enter,
		Enter -- but the second one lands on a question that names what is
		about to happen, with the draft still on screen behind it.

		`Send? Y/n` follows the conventional shell default: yes. Slawomir's
		call, and it is the reading most people already have.

		Returns False when there is nothing to arm, so the caller can leave
		the draft alone."""
		if self.mode not in (MODE_REPLY, MODE_COMPOSE, MODE_NOTICE):
			return False
		# PREFLIGHT BEFORE THE QUESTION. A bad attachment path used to reach
		# the confirmation, so the human read `Send? Y/n`, answered it, and
		# only then learned the path was wrong -- a refusal that costs a
		# keystroke and a moment of believing the message went. Refusing here
		# leaves them on the path field with everything they typed.
		#
		# `send_compose` checks AGAIN, and that is not redundant: the file can
		# change between the review and the confirmation, and core checks a
		# third time because core is the authority.
		refusal = self.attachment_error()
		if refusal:
			self.set_status(refusal, SEV_WARNING)
			self._focus_field("attach_path")
			return False
		self.send_return_mode = self.mode
		self.mode = MODE_CONFIRM_SEND
		self.set_status("Send? Y/n", SEV_WARNING)
		return True

	def _focus_field(self, name: str) -> None:
		"""Put the caret on the field a refusal is about, if it exists here."""
		fields = self.compose_fields
		if name in fields:
			self.compose_field = fields.index(name)

	def confirm_send(self, store, confirmed: bool):
		"""`y`, `Y` or Enter publishes; `n`, `N` or Esc returns to the SAME
		draft and the SAME field with the buffers untouched. A cancelled send
		that cost the human their message would be worse than no
		confirmation."""
		mode = getattr(self, "send_return_mode", None) or MODE_COMPOSE
		self.mode = mode
		if not confirmed:
			self.set_status("not sent — the draft is unchanged", SEV_INFO)
			return None
		if mode in (MODE_COMPOSE, MODE_NOTICE):
			return self.send_compose(store)
		return self.send_reply(store)

	def edit_body_externally(self, edit_fn) -> bool:
		"""Ctrl-E: hand the body to a real editor, import what comes back.

		Importing is NOT publishing. The ordinary Enter and `Send now? [Y/n]`
		still stand -- an editor that saves and exits must not be able to put
		a message on the wire, because "save and quit" is muscle memory and
		"send this to another person" is a decision.

		Any failure leaves the draft exactly as it was: a half-imported body
		is worse than no import."""
		if self.mode not in (MODE_REPLY, MODE_COMPOSE, MODE_NOTICE):
			return False
		if self.mode == MODE_REPLY:
			# The BODY, not the subject line the human is editing inline.
			# Reopening always gets exactly the last imported body: no
			# re-seed, no merge, nothing lost.
			seed = self.reply_body or self._reply_quote()
		else:
			# `body` is not an inline field at all, so there is nothing to
			# switch to and nothing to merge: the editor owns it outright.
			# A quote ONLY when this composition is answering something. A
			# fresh compose or notice starts from its own draft, which is
			# usually empty -- seeding it with whatever was last open would
			# put another participant's words in an unrelated message.
			seed = self.compose.get("body", "")
			if not seed and self.compose_is_reply:
				seed = self._reply_quote()
		result, message = edit_fn(seed)
		if result is None:
			self.set_status(message, SEV_WARNING)
			return False
		if result == seed:
			# `:q!` in Vim EXITS SUCCESSFULLY and leaves the file untouched,
			# so the editor hands back exactly what it was given. Reporting
			# that as an import is how a cancelled full reply left the human
			# stranded in a provisional draft they never wrote: nothing failed,
			# so nothing was undone. Identical bytes are no edit, whatever the
			# exit status said.
			#
			# It follows that saving a seeded quote verbatim is also no edit.
			# That is intended: an unmodified quote is not an answer.
			self.set_status(EDITOR_UNCHANGED, SEV_WARNING)
			return False
		if self.mode == MODE_REPLY:
			self.reply_body = result
			self.reply_body_requested = True
		else:
			self.compose["body"] = result
		self.set_status(message, SEV_SUCCESS)
		return True

	def _reply_quote(self) -> str:
		"""A conventional quote of the original, ONLY when the draft is empty.

		A draft with content is opened exactly as it stands: silently
		re-seeding over words someone already wrote would destroy them, and
		they would not find out until the editor opened."""
		from .editor import quote
		detail = self.detail or {}
		if "delivery" in detail:
			envelope = detail["delivery"].get("message") or {}
		elif "notice" in detail:
			envelope = detail["notice"]
		else:
			return ""
		text = self._first_text_leaf(envelope)
		if text is None:
			# Binary and withheld parts are NOT copied into a draft. Quoting
			# base64 into someone's reply helps nobody, and the original stays
			# on screen for context either way.
			return ""
		return quote(text, envelope.get("from_participant"),
		             envelope.get("created_ts"))

	@staticmethod
	def _first_text_leaf(envelope: dict) -> str | None:
		content = envelope.get("content") or {}
		nodes = content.get("parts") or envelope.get("parts") or []

		def walk(items):
			for node in items or []:
				if node.get("parts"):
					found = walk(node["parts"])
					if found is not None:
						return found
				elif node.get("encoding") == "text":
					return node.get("text") or ""
			return None
		return walk(nodes)

	# -- the modal shortcut list ------------------------------------------

	def open_help(self) -> None:
		"""`?`: show the shortcut map. OBSERVATION, in the strongest sense.

		It claims nothing, marks nothing seen, refreshes nothing and publishes
		nothing -- and it must not disturb the console either. The selection,
		both scroll positions, the selected part, the opened claim, any draft
		and the status bar are all left exactly as they were, so closing it
		puts the human back where they were reading. Its own scroll is the
		only state it owns."""
		if self.mode != MODE_BROWSE:
			return
		self.mode = MODE_HELP
		self.help_offset = 0

	def close_help(self) -> None:
		"""`?`, `q` or Esc. `q` does NOT quit from here: it is the key people
		press to dismiss a full-screen thing, and quitting the console from a
		help screen would be a very poor joke."""
		if self.mode != MODE_HELP:
			return
		self.mode = MODE_BROWSE
		self.help_offset = 0

	def scroll_help(self, delta: int, total_lines: int) -> None:
		"""The help scrolls itself, so a small terminal reaches every shortcut
		rather than silently clipping the ones that did not fit."""
		limit = max(0, total_lines - max(1, self.detail_height))
		self.help_offset = max(0, min(limit, self.help_offset + delta))

	def request_quit(self) -> bool:
		"""ALWAYS ask, exactly once. Never True on the first press.

		It used to quit immediately when nothing was owed, and confirm only
		with claims outstanding. Two behaviours behind one key means the human
		cannot know what `q` will do until after it has done it -- and the
		cheap case is the one where they are reading, not the one where they
		are finishing work.

		One prompt regardless of how many claims are outstanding. Their count
		is already on the header and in the list; a confirmation that
		restates it is a second row saying what the first said.

		No store call on request, decline or confirm: quitting is a decision
		about this process, not about the mailbox."""
		self.mode = MODE_CONFIRM_QUIT
		self.set_status(CONFIRM_QUIT_PROMPT, SEV_WARNING)
		return False

	def confirm_quit(self, confirmed: bool) -> bool:
		self.mode = MODE_BROWSE
		if not confirmed:
			# GENERIC on purpose. The old wording told the human to "finish or
			# close the open claim", which is an instruction to do something
			# that may not exist: with nothing owed it named a claim the
			# reader did not have.
			self.set_status("staying", SEV_INFO)
		return confirmed

	# -- what the renderer needs to know ----------------------------------

	def unresolved_count(self) -> int:
		"""Claims this participant holds that still owe a reply or close. A
		console must keep this visible: the whole failure mode it exists to
		prevent is a human walking away from a claim nobody else can take."""
		# INBOUND only. An outbound message someone else has claimed is their
		# obligation, not a reply this participant owes.
		return sum(1 for r in self.rows
		           if r["row_type"] == ROW_MESSAGE and r["state"] == "claimed"
		           and r.get("claim_id") and r.get("direction", "in") == "in")
