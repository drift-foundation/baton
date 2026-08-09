"""The curses loop: read a key, raise a model event, blit a rendered buffer.

Nothing decidable lives here. Key meaning is in `keys`, behaviour is in
`state`, layout is in `render`. What remains is terminal plumbing, which is
the part that cannot be unit-tested -- so it is kept small enough to read.
"""

from __future__ import annotations

import locale
import sys

from . import keys as K
from .safe_text import pad, split_cells
from .render import (STYLE_PART_HEADER, STYLE_SELECTED, detail_line_count, divider_for, input_line_index,
                     detail_overflow, help_line_count,
                     part_header_line_index, selection_span,
                     markers_for,
                     layout_for, render, render_styled)
from .state import (SEV_WARNING, FOCUS_DETAIL, MODE_BROWSE, MODE_COMPOSE,
                    MODE_CONFIRM_SEND, MODE_HELP,
                    VIEW_INBOX, VIEW_SENT,
                    MODE_NOTICE, MODE_PICK_RECIPIENT, MODE_PICK_ROOT,
                    MODE_REPLY, InboxState)


# Which affordance each contextual event needs. The footer reads the same
# names from the same query, so "advertised" and "dispatchable" are one fact.
_AFFORDANCE = {
	K.OPEN: "open", K.REPLY: "reply", K.CLOSE: "close",
	# `R` is the same semantic act as `r`, so it answers to the same
	# affordance. Omitting it left the footer hiding both reply forms while
	# `R` stayed dispatchable and refused through a SECOND predicate inside
	# `begin_reply` -- which is precisely the drift one query exists to stop.
	K.EDIT_BODY: "reply",
	K.MATERIALIZE: "materialize", K.READ_PART: "read_part",
	K.PART_UP: "part_nav", K.PART_DOWN: "part_nav",
	K.HSCROLL_LEFT: "hscroll", K.HSCROLL_RIGHT: "hscroll",
}

def _go_to_end(state, store, columns: int, lines: int, *, first: bool) -> None:
	"""`gg`/`G`, PER FOCUS: the ends of the focused list, or the top and
	bottom of the rendered detail. Same keys; the active label says which."""
	if state.focus == FOCUS_DETAIL:
		total = detail_line_count(state, columns, lines)
		state.scroll_detail(-total if first else total, total)
		return
	# The ACTIVE view's rows. `state.rows` is the inbox, so in SENT with a
	# different row count `G` stopped short of the last row -- or ran past it
	# into a clamp.
	state.jump_to(0 if first else len(state.view_rows) - 1, store)


# Controls INSIDE a modal mode that promise a change, and so must not fire
# when there is no other state to reach. `Tab` in a one-field notice and in a
# one-page picker are exactly that: mapped, but with nothing to move to.
_MODAL_AFFORDANCE = {
	K.PICK_PAGE: "picker_paging",
	K.NEXT_FIELD: "more_fields",
	K.PREV_FIELD: "more_fields",
}


def _allowed(state, event) -> bool:
	"""Whether a contextual key may fire, from the ONE affordance query.

	Modal controls are gated by the SAME query that described them, rather
	than only by what was drawn: a control that cannot change anything must
	not dispatch a meaningless transition either. This is a dispatch property,
	not a footer feature -- which is why it outlives the footer that used to
	be the only thing consulting it.

	Deliberately NOT extended to movement at a boundary: `j` on the last row
	still means something, because the list can move."""
	modal = _MODAL_AFFORDANCE.get(event)
	if modal is not None:
		return bool(state.modal_affordances().get(modal, True))
	if state.mode != MODE_BROWSE:
		# Ctrl-E reaches EDIT_BODY from the typing modes, where the browse
		# affordances say nothing about it.
		return True
	return bool(state.affordances().get(_AFFORDANCE[event], True))


def step(state, store, key: int, columns: int, lines: int,
         edit_fn=None) -> bool:
	"""Apply ONE keypress. Returns False to quit.

	Separated from the curses loop so the entire interaction is testable with
	plain integers -- the loop below only supplies keys and draws."""
	event, payload = K.map_key(key, state.mode)

	# Multi-key chords. `g` alone is inert; `gg` jumps to the first row. Any
	# other key clears the prefix, so an abandoned `g` can never combine with
	# a later keystroke into an action the human did not type.
	if state.mode == MODE_BROWSE:
		if event == K.PREFIX_G:
			if state.pending_prefix == "g":
				state.pending_prefix = ""
				# Through the SAME routing `G` uses, or `gg` would jump the
				# list while `G` scrolled the detail -- one chord obeying
				# focus and its partner ignoring it.
				_go_to_end(state, store, columns, lines, first=True)
			else:
				state.pending_prefix = "g"
			return True
		state.pending_prefix = ""
	if event == K.LAST:
		_go_to_end(state, store, columns, lines, first=False)
		return True
	if event == K.FIRST:
		_go_to_end(state, store, columns, lines, first=True)
		return True
	if event == K.TOGGLE_FOCUS:
		state.toggle_focus()
		return True
	if event == K.QUIT:
		# `step` returns False to EXIT; `request_quit` returns True when it is
		# safe to. Inverting these is a one-character mistake that makes `q`
		# either never quit or quit past the confirmation, so the polarity is
		# pinned in both directions by the tests below.
		return not state.request_quit()
	if event == K.CONFIRM_SEND:
		state.confirm_send(store, True)
		return True
	if event == K.DECLINE_SEND:
		state.confirm_send(store, False)
		return True
	if event == K.CONFIRM:
		return not state.confirm_quit(True)
	if event == K.DECLINE:
		state.confirm_quit(False)
		return True
	if event in (K.UP, K.DOWN, K.PAGE_UP, K.PAGE_DOWN):
		# ONE navigation model, routed by focus. DETAIL navigation never moves
		# the list cursor and list navigation never moves the detail offset --
		# they are separate panes and the keys only choose which one.
		down = event in (K.DOWN, K.PAGE_DOWN)
		page = event in (K.PAGE_UP, K.PAGE_DOWN)
		if state.focus == FOCUS_DETAIL:
			step_size = max(1, state.detail_height) if page else 1
			state.scroll_detail(step_size if down else -step_size,
			                    detail_line_count(state, columns, lines))
		else:
			step_size = max(1, state.inbox_height - 1) if page else 1
			state.move(step_size if down else -step_size, store)
	elif event == K.SCROLL_UP:
		# The help owns its own scroll, so the reader's detail position is
		# exactly where they left it when they close it.
		if state.mode == MODE_HELP:
			state.scroll_help(-1, help_line_count(state, columns, lines))
		else:
			state.scroll_detail(-1, detail_line_count(state, columns, lines))
	elif event == K.SCROLL_DOWN:
		if state.mode == MODE_HELP:
			state.scroll_help(1, help_line_count(state, columns, lines))
		else:
			state.scroll_detail(1, detail_line_count(state, columns, lines))
	elif (event in _AFFORDANCE or event in _MODAL_AFFORDANCE) \
			and not _allowed(state, event):
		# Refused by the SAME query that describes the control, so `?` help
		# cannot document a key that would refuse and dispatch cannot run one
		# help calls meaningless. Two predicates would drift.
		name = _MODAL_AFFORDANCE.get(event) or _AFFORDANCE.get(event)
		state.set_status(state.unavailable_reason(name), SEV_WARNING)
	elif event == K.OPEN:
		state.open_selected(store)
	elif event == K.REPLY:
		state.begin_reply()
	elif event == K.CLOSE:
		state.close_selected(store, outcome="closed")
	elif event == K.REFRESH:
		state.refresh(store)
		# Re-preview only when a PREVIEW is what is showing, exactly as the
		# poll path does. An explicit refresh used to replace an opened
		# delivery with its metadata preview -- so `^R` closed the message the
		# human was reading, and took the sideways offset with it because a
		# preview has nothing to scroll.
		if state.detail is None or "preview" in (state.detail or {}):
			state.preview(store)
	elif event == K.SEND:
		# ARMS the send. Publishing happens on the `y` that follows.
		# Enter on an EMPTY attach path opens the ROOT PICKER instead of
		# reviewing the send. Without this the picker is unreachable behind
		# the "Enter from any field reviews" shorthand -- a control that
		# exists and cannot be got to.
		if state.mode in (MODE_COMPOSE,) and state.compose_field_name == "attach_path" \
				and not (state.compose.get("attach_path") or "").strip() \
				and not (state.compose.get("attach_root") or "").strip():
			if state.begin_pick_root(store):
				apply_layout(state, columns, lines)
				return True
		state.arm_send()
	elif event == K.CANCEL:
		if state.mode == MODE_PICK_ROOT:
			state.cancel_root_picker()
		elif state.mode == MODE_PICK_RECIPIENT:
			state.cancel_picker()
		elif state.mode in (MODE_COMPOSE, MODE_NOTICE):
			state.cancel_compose()
		else:
			state.cancel_reply()
	elif event == K.TYPE and payload:
		# Insert AT THE CARET, whichever buffer is being edited.
		state.type_char(payload)
	elif event == K.CARET_LEFT:
		state.move_caret(-1)
	elif event == K.CARET_RIGHT:
		state.move_caret(1)
	elif event == K.CARET_HOME:
		state.caret_home()
	elif event == K.CARET_END:
		state.caret_end()
	elif event == K.DELETE_FORWARD:
		state.delete_forward()
	elif event == K.KILL_TO_START:
		state.kill_to_start()
	elif event == K.OPEN_HELP:
		state.open_help()
	elif event == K.CLOSE_HELP:
		state.close_help()
	elif event == K.BACKSPACE:
		state.backspace()
	elif event == K.MATERIALIZE:
		state.materialize_selected_part(store)
	elif event == K.READ_PART:
		state.read_selected_external_part(store)
	elif event in (K.HSCROLL_LEFT, K.HSCROLL_RIGHT):
		# Sideways, one display cell. Observation only: nothing is read from
		# the authority and nothing is written.
		width = max(1, columns)
		state.scroll_detail_sideways(
			1 if event == K.HSCROLL_RIGHT else -1,
			width + detail_overflow(state, columns, lines), width)
	elif event == K.PART_UP:
		state.move_part(-1)
	elif event == K.PART_DOWN:
		state.move_part(1)
	elif event == K.PICK and payload:
		if state.mode == MODE_PICK_ROOT:
			state.pick_root(payload)
		else:
			state.pick_recipient(payload)
	elif event == K.PICK_PAGE:
		state.picker_next_page()
	elif event == K.COMPOSE:
		state.begin_pick_recipient(store)
	elif event == K.EDIT_BODY:
		# The editor callable is INJECTED: suspending curses needs a real
		# terminal, and everything else about this path is testable without
		# one. A driver with no editor available says so rather than
		# pretending the keystroke did nothing.
		if edit_fn is None:
			state.set_status("no external editor available here", SEV_WARNING)
		else:
			if state.mode == MODE_BROWSE:
				# `R` from browse is the FULL version of `r`: it starts the
				# reply -- or the follow-up, on a row whose claim is already
				# resolved -- and goes straight to the editor. One action,
				# which is what a person wants when the answer is not one
				# line; splitting it into "press r, then Ctrl-E" would be the
				# hybrid model that was rejected.
				if not state.begin_reply():
					return True
				if not state.edit_body_externally(edit_fn):
					# The one action did nothing, so put the human back where
					# it started: reading the message they were reading. The
					# editor's own explanation stays in the status bar.
					state.abandon_fresh_reply()
			else:
				# Ctrl-E inside an existing composition: the draft is theirs
				# and survives whatever the editor did.
				state.edit_body_externally(edit_fn)
	elif event in (K.VIEW_INBOX_KEY, K.VIEW_SENT_KEY):
		# A view switch ESTABLISHES the destination view's highlighted row,
		# exactly as startup does -- so it goes through the same semantic
		# selection path. Routing it through `preview` preserved the old
		# "switching writes nothing" rule and left a hole: arrive in an empty
		# MESSAGES, let a pending message land, press `i`, and the row was
		# highlighted but unclaimed -- the extra-Enter ceremony the ruling
		# removed, reachable again by a different door.
		#
		# Polling itself stays write-free; this is a human act, like any other
		# selection. A notice stays explicit and sent/handled/outbound rows
		# open observationally, because `select_row` decides that per row
		# rather than per view.
		state.select_view(VIEW_INBOX if event == K.VIEW_INBOX_KEY else VIEW_SENT)
		state.select_row(store)
	elif event == K.COMPOSE_NOTICE:
		state.begin_compose(notice=True)
	elif event == K.NEXT_FIELD:
		state.compose_next_field(1)
	elif event == K.PREV_FIELD:
		state.compose_next_field(-1)
	# AFTER the whole dispatch, so it sees the state the keystroke actually
	# produced -- and through the same helper the redraw path uses, so a
	# resize cannot follow a different rule than a keystroke.
	apply_layout(state, columns, lines)
	# The renderer is the only thing that knows how the content laid out, so
	# the model is told each frame and the affordance reads one number.
	state.detail_overflow = detail_overflow(state, columns, lines)
	state.scroll_detail_sideways(0, columns + state.detail_overflow, columns)
	if event in (K.PART_UP, K.PART_DOWN):
		# Bring the newly marked part header into view. Only on the keystroke
		# that MOVED it: doing this on every redraw would take the reader's
		# `J`/`K` scroll position away from them. The stacked detail pane is
		# 60% of the body, so the later parts of a multipart message start
		# below the fold -- and a mark nobody can see is not a cursor.
		header = part_header_line_index(state, columns, lines)
		if header >= 0:
			total = detail_line_count(state, columns, lines)
			# The header itself, THEN the line after it. Two calls, because the
			# two directions need different things: moving up, the header must
			# become visible; moving down, it must not come to rest on the row
			# the pane spends on its "... N more lines" indicator, which is not
			# a header and so drops the mark. Following only the line after it
			# fixed the second and broke the first.
			state.follow_line(header, total)
			state.follow_line(header + 1, total)
	return True


def apply_layout(state, columns: int, lines: int) -> None:
	"""Fit the model to this terminal, then bring the caret back into view.

	One helper for both callers on purpose. Following the caret used to happen
	only at the end of `step`, so a RESIZE moved the viewport without moving
	the offset: after narrowing, a draft's tail and caret were off-screen and
	stayed there until the human typed one more character, which is the moment
	they most need to see what they already wrote.

	Order matters. The new pane height has to be in the model before the caret
	position is computed against it, or the follow corrects toward the old
	window."""
	layout = layout_for(columns, lines, state.recipients, state.participant)
	if layout is not None:
		state.set_viewport(**layout)
	if state.mode in (MODE_REPLY, MODE_COMPOSE, MODE_NOTICE):
		# Typing modes have no scroll keys -- every printable key is text --
		# so the model follows the caret instead of the human chasing it.
		state.follow_line(input_line_index(state, columns, lines),
		                  detail_line_count(state, columns, lines))


def curses_editor(stdscr, argv, poll_seconds: float = 2.0):  # pragma: no cover
	"""An `edit_fn` that suspends curses, runs the editor on the REAL
	terminal, and puts the screen back.

	`endwin` then `doupdate` is the documented suspend/resume pair. Skipping
	it leaves the editor drawing into a screen curses believes it owns, and
	the result is unusable in a way that looks like the editor's fault."""
	import curses

	from .editor import edit_text

	def edit(seed: str):
		curses.endwin()
		try:
			return edit_text(seed, argv=argv)
		finally:
			# Re-measure and repaint from scratch: the editor may have been
			# resized, and curses' idea of the screen is now stale.
			stdscr.clear()
			curses.doupdate()
			stdscr.refresh()
	return edit


def run(stdscr, config_path: str, participant: str, poll_seconds: float = 2.0,
        editor_argv=None) -> None:  # pragma: no cover
	"""The loop. Excluded from coverage deliberately: it is the only part that
	needs a real terminal, which is exactly why everything else was moved out
	of it."""
	import curses

	import baton_core as core

	curses.curs_set(0)
	stdscr.keypad(True)                 # belt: ask for translation...
	try:
		curses.set_escdelay(25)          # ...and do not wait a second for ESC
	except (AttributeError, curses.error):
		pass
	arm_poll(stdscr, poll_seconds)
	# Decided ONCE at startup from the terminal's encoding: a box-drawing
	# divider on a non-UTF-8 terminal is worse than the ASCII bar it replaces.
	encoding = (getattr(sys.stdout, "encoding", None)
	            or locale.getpreferredencoding(False))
	divider = divider_for(encoding)
	marks = markers_for(encoding)
	state = InboxState(participant)
	with core.open_instance(config_path) as store:
		# The participant's CONFIGURED projection directory, never the
		# process working directory. Absent one, materialize refuses rather
		# than writing message content into whatever directory launched the
		# console.
		spec = store.config.get("participants", {}).get(participant, {})
		state.projection_dir = spec.get("projection_dir", "")
		state.refresh(store)
		first_selection(store=store, state=state)
		while True:
			lines, columns = stdscr.getmaxyx()
			apply_layout(state, columns, lines)
			stdscr.erase()
			for row, (text, style) in enumerate(
					render_styled(state, columns, lines, divider=divider,
					              thread=marks["thread"], deep=marks["deep"],
					              notice_seen=marks["notice_seen"],
					              status=marks["status"])):
				try:
					if STYLE_PART_HEADER in style and STYLE_SELECTED not in style:
						# Distinct from the inbox selection ON PURPOSE: the
						# two cursors mean different things -- which message
						# Enter opens, and which part `m` writes out -- and a
						# human who cannot tell them apart has two cursors
						# that look like one. Bold+underline, not reverse.
						stdscr.addnstr(row, 0, text, max(0, columns - 1),
						               curses.A_BOLD | curses.A_UNDERLINE)
					elif STYLE_SELECTED in style:
						# The WHOLE ROW reversed. Stacked, a list row IS the
						# full width, so the stripe no longer has to stop at a
						# column -- but it still says exactly what it always
						# said: this row, in this list. The rule below it and
						# the detail pane are separate ROWS and are drawn
						# plainly. Padded by display cell so the stripe is not
						# ragged, and split by cell so a wide character cannot
						# push it one cell past the terminal.
						budget = max(0, columns - 1)
						_, end = selection_span(columns)
						end = min(end, budget)
						head, _ = split_cells(text, end)
						stdscr.addnstr(row, 0, pad(head, end), end,
						               curses.A_REVERSE)
					else:
						stdscr.addnstr(row, 0, text, max(0, columns - 1))
				except curses.error:
					pass          # a terminal shrinking mid-draw is not an error
			# Cursor visible only while typing, and placed AT the input so the
			# human can see where their next character lands.
			if state.mode in (MODE_REPLY, MODE_COMPOSE, MODE_NOTICE):
				curses.curs_set(1)
				try:
					stdscr.move(*_input_position(state, columns, lines))
				except curses.error:
					pass
			else:
				curses.curs_set(0)
			stdscr.refresh()
			# Re-armed before EVERY blocking read, so no earlier operation can
			# leave the console waiting forever with mail pending.
			arm_poll(stdscr, poll_seconds)
			key = _read_key(stdscr, poll_seconds)
			if key == -1:                     # poll timeout: refresh the queue
				state.refresh(store)
				if state.detail is None or "preview" in (state.detail or {}):
					state.preview(store)
				continue
			if not step(state, store, key, columns, lines,
			            edit_fn=curses_editor(stdscr, editor_argv or ["vim"],
			                                  poll_seconds)):
				return


def first_selection(state, store) -> None:
	"""The startup selection, which COMMITS like any other (point 1).

	Its own function rather than a line in `run`, because `run` is the only
	part excluded from coverage -- and "launching the console claims the
	message it lands on" is far too consequential to live only there."""
	state.select_row(store)


def arm_poll(stdscr, poll_seconds: float) -> None:
	"""Re-apply the finite input timeout.

	A LOOP INVARIANT, not startup configuration. `nodelay(False)` -- which the
	escape decoder calls to restore itself -- sets BLOCKING mode, which is not
	the same as the finite delay that was there before; and the editor's
	suspend/resume never restored it at all. Either path left `getch` blocking
	forever, so the two-second poll stopped and mail only appeared when the
	human pressed a key. Reported from the live trial after writing a body in
	Vim."""
	stdscr.timeout(int(poll_seconds * 1000))


def _read_key(stdscr, poll_seconds: float = 2.0):  # pragma: no cover - needs a live terminal
	"""One key, with escape sequences decoded here rather than by terminfo.

	If keypad translation works, arrows arrive already decoded and this is a
	pass-through. If it does not -- as on the trial terminal, where Down
	arrived as raw 27, 91, 66 and did nothing -- we assemble the sequence
	ourselves. A bare ESC still returns ESC, because it cancels a draft."""
	key = stdscr.getch()
	if key != K.ESC:
		return key
	stdscr.nodelay(True)
	tail = ""
	try:
		for _ in range(4):
			following = stdscr.getch()
			if following == -1:
				break
			tail += chr(following)
			decoded = K.decode_escape(tail)
			if decoded is not None:
				return decoded
			if following in (ord("~"), ord("A"), ord("B"), ord("Z"),
			                 ord("H"), ord("F")):
				break                       # a terminated sequence we do not map
	finally:
		# NOT `nodelay(False)`: that is blocking mode, and the poll timeout it
		# replaces is what makes new mail appear on its own.
		arm_poll(stdscr, poll_seconds)
	return K.ESC if not tail else -1         # unknown sequence: ignore, do not act


def _input_position(state, columns: int, lines: int) -> tuple[int, int]:
	"""Row and column of the draft caret, in the detail pane."""
	from .render import input_caret
	return input_caret(state, columns, lines)


def main(argv=None) -> int:  # pragma: no cover
	import argparse
	import curses

	import baton_core as core
	from . import TUI_VERSION, check_core_compatibility

	parser = argparse.ArgumentParser(prog="baton-tui",
	                                 description="Human console for a Baton instance")
	parser.add_argument("--config", required=True, help="absolute path to baton.json")
	parser.add_argument("--participant", required=True)
	parser.add_argument("--version", action="version", version=f"baton-tui {TUI_VERSION}")
	parser.add_argument(
		"--editor",
		help="editor for Ctrl-E, as a command line (no shell). Precedence: "
		     "--editor, BATON_EDITOR, VISUAL, EDITOR, then vim.")
	args = parser.parse_args(argv)
	check_core_compatibility(core)
	from .editor import resolve_editor
	curses.wrapper(run, args.config, args.participant, 2.0,
	               resolve_editor(args.editor))
	return 0
