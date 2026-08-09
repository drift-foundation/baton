"""Key mapping and the step function, driven with plain integers.

The curses loop itself needs a terminal and is excluded from coverage on
purpose -- which is only defensible because everything decidable was moved out
of it. These tests are what make that claim true.
"""

from __future__ import annotations

import json

import pytest

import baton_core as core
from baton_tui import keys as K
from baton_tui.driver import step
from baton_tui.render import DIVIDER, layout_for, render
from baton_tui.state import (EDITOR_UNCHANGED, MODE_BROWSE, MODE_COMPOSE,
                             MODE_CONFIRM_QUIT, MODE_CONFIRM_SEND,
                             MODE_PICK_RECIPIENT, MODE_REPLY, InboxState)


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	(home / "root").mkdir()
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 9, "generation": 1,
			"mailbox": {"name": "console"},
			"participants": {"acme.reviewer": {}, "acme.implementer": {},
			                 "hq.lead": {"capabilities": ["recovery", "config"]}},
			"roots": {"src": str(home / "root")}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path


@pytest.fixture
def env(tmp_path):
	with core.open_instance(_instance(tmp_path)) as store:
		yield store


def _ready(store, participant="acme.implementer"):
	state = InboxState(participant)
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	state.preview(store)
	return state


def _pick(state, address):
	"""The key that selects `address` in the open picker."""
	for label, entry in state.picker_entries():
		if entry["address"] == address:
			return ord(label)
	raise AssertionError(f"{address} is not on this picker page")


def _send(state, store):
	"""Enter ARMS the send; `y` publishes it.

	Sending is two strokes now, so every test that used to press one Enter
	presses this instead. It asserts the confirmation was actually armed, so
	a regression that publishes on the first Enter fails here rather than
	being absorbed by a helper that just presses both keys."""
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_CONFIRM_SEND, (
		f"Enter did not arm a confirmation; mode is {state.mode}")
	return _press(state, store, ord("y"))


def _press(state, store, *keys):
	alive = True
	for key in keys:
		alive = step(state, store, key, 100, 24)
	return alive


# -- typing must not trigger commands --------------------------------------

@pytest.mark.parametrize("key", [ord("q"), ord("c"), ord("R"), ord("j"), ord("m")])
def test_command_letters_are_plain_text_while_typing(env, key):
	"""Reply mode is a separate table, not the browse table with guards. A
	shared table is how a draft quits the application or closes a claim
	mid-sentence."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)             # claim and open
	_press(state, store, ord("R"))               # enter reply mode
	assert state.mode == MODE_REPLY
	seeded = state.draft                          # the quick-reply line
	alive = _press(state, store, key)
	assert alive is True                          # 'q' did not quit
	assert state.draft == seeded + chr(key)
	assert state.mode == MODE_REPLY
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0


def test_a_draft_types_sends_and_resolves(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Needs an ack", body=b"?\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	seeded = state.draft
	for char in "on it":
		_press(state, store, ord(char))
	assert state.draft == seeded + "on it"
	_press(state, store, K.BACKSPACE_KEY)
	assert state.draft == seeded + "on i"
	_send(state, store)                          # Enter, then y
	assert state.mode == MODE_BROWSE
	response = store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0]
	assert response == 1
	assert state.unresolved_count() == 0


def test_escape_cancels_and_leaves_the_claim_owed(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"), ord("h"), ord("i"), K.ESC)
	assert state.mode == MODE_BROWSE and state.draft == ""
	assert state.unresolved_count() == 1
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0


def test_control_characters_are_refused_at_the_keyboard(env):
	"""A control character in a draft would be sent to another participant and
	rendered on THEIR terminal. Refused at the keyboard as well as in the
	renderer -- neither layer relies on the other."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	seeded = state.draft
	for key in (0, 1, 7, 9, 11, 27 + 0, 31, 155):
		if key == K.ESC:
			continue
		step(state, store, key, 100, 24)
	assert state.draft == seeded


# -- navigation never disposes ---------------------------------------------

@pytest.mark.parametrize("key", [
	K.KEY_UP, K.KEY_DOWN, ord("j"), ord("k"), K.KEY_NPAGE, K.KEY_PPAGE,
	ord("J"), ord("K"), ord("g"), K.KEY_RESIZE, ord("z"), ord("?"),
])
def test_navigation_never_consumes_a_broadcast_or_disposes_anything(env, key):
	"""SUPERSEDED IN PART. This asserted that NO navigation key changed the
	authority at all -- zero claims included. Slawomir reversed that for
	directed messages: highlighting one claims and opens it.

	The half that survives is the half that was never on the table. Browsing
	consumes no BROADCAST -- zero notice receipts -- and disposes of nothing:
	no reply, no close, no auto-resolution of the claims that accumulate. Those
	are the irreversible acts; a claim is recoverable and is now deliberate."""
	store = env
	for i in range(5):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	store.send_notice("hq.lead", kind="announcement", subject="N", body=b"n\n")
	state = _ready(store)
	for _ in range(12):
		assert step(state, store, key, 100, 24) is True
	assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
	assert store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	# Never more claims than there are directed rows: a row already claimed by
	# us is reopened, not claimed again.
	claims = store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
	assert claims <= 5, f"navigation claimed {claims} times over 5 rows"


def test_only_three_events_are_destructive():
	"""Keeps the mapping honest. If a new key is wired to something that takes
	ownership, it has to be added here deliberately."""
	destructive = {event for event in vars(K).values()
	               if isinstance(event, str) and K.is_destructive(event)}
	assert destructive == {K.OPEN, K.SEND, K.CLOSE, K.MATERIALIZE}


@pytest.mark.parametrize("key", sorted(set(range(0, 300)) - {ord("q")}))
def test_no_key_quits_except_q(env, key):
	"""Swept rather than assumed: a stray mapping that exits the console while
	a claim is held is exactly the abandonment this tool exists to prevent."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert step(state, store, key, 100, 24) is True


def test_q_quits_from_browse_only(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert step(state, store, ord("q"), 100, 24) is False
	_press(state, store, K.ENTER_LF, ord("R"))
	assert step(state, store, ord("q"), 100, 24) is True     # typing, not quitting


# -- the loop's own contract ----------------------------------------------

def test_paging_moves_by_a_screen_and_stays_visible(env):
	store = env
	for i in range(60):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i:02d}", body=b"x\n")
	state = _ready(store)
	for _ in range(6):
		_press(state, store, K.KEY_NPAGE)
		assert any(line.startswith(">") for line in render(state, 100, 24))
	for _ in range(6):
		_press(state, store, K.KEY_PPAGE)
		assert any(line.startswith(">") for line in render(state, 100, 24))
	assert state.cursor == 0


def test_detail_focus_scrolls_the_detail_and_never_the_list(env):
	"""Detail navigation never moves the list cursor. (This pressed `J`/`K`,
	which Slawomir superseded: the focused-pane model is the sole navigation
	model and those bindings are gone, not aliased.)"""
	store = env
	body = "\n".join(f"line {i}" for i in range(80)).encode()
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Long", body=body)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	cursor = state.cursor
	_press(state, store, K.TAB)                       # focus DETAIL
	for _ in range(10):
		_press(state, store, ord("j"))
	assert state.detail_offset > 0
	assert state.cursor == cursor, "detail navigation moved the list cursor"
	for _ in range(30):
		_press(state, store, ord("k"))
	assert state.detail_offset == 0
	assert state.cursor == cursor


def test_open_on_a_notice_marks_seen_once(env):
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="N", body=b"n\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 1
	_press(state, store, K.ENTER_LF)
	assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 1


def test_close_resolves_the_opened_claim(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	assert state.unresolved_count() == 1
	_press(state, store, ord("c"))
	assert state.unresolved_count() == 0


# -- gap 1: materialize is a first-class action ---------------------------

def test_materialize_writes_the_selected_part(env, tmp_path):
	"""Not an instruction to go and use the CLI: the console writes it."""
	store = env
	target = tmp_path / "proj"
	target.mkdir()
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Rich", parts=[
		{"content_type": "text/markdown; charset=utf-8", "body": b"# first\n"},
		{"content_type": "text/plain; charset=utf-8", "body": b"second part\n"},
	])
	state = _ready(store)
	state.projection_dir = str(target)
	_press(state, store, K.ENTER_LF)                  # claim and open
	_press(state, store, ord("m"))
	assert "wrote" in state.status
	first = sorted(target.iterdir())
	assert len(first) == 1 and first[0].read_bytes() == b"# first\n"
	# `]` selects the next part; materialize follows the selection.
	_press(state, store, ord("]"), ord("m"))
	written = sorted(p.name for p in target.iterdir())
	assert len(written) == 2
	assert any(p.read_bytes() == b"second part\n" for p in target.iterdir())


def test_materialize_reports_failure_without_dying(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="T",
	           retention="transient", body=b"ephemeral\n")
	state = _ready(store)
	state.projection_dir = str(tmp_path / "does-not-exist")
	_press(state, store, K.ENTER_LF)
	assert _press(state, store, ord("m")) is True     # still running
	assert "failed" in state.status
	assert state.unresolved_count() == 1              # claim state intact


# -- gap 2: composing new traffic -----------------------------------------

def test_a_new_directed_message_can_be_sent_from_the_console(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "Need a decision":
		_press(state, store, ord(char))
	_send(state, store)
	assert state.mode == MODE_BROWSE
	sent = store.scan("acme.reviewer")["pending"]
	assert len(sent) == 1
	assert sent[0]["subject"] == "Need a decision"


def test_a_notice_can_be_published_from_the_console(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("N"))
	for char in "Maintenance":
		_press(state, store, ord(char))
	_send(state, store)
	# The persistent confirmation names what went where and how to look at it.
	assert "Sent:" in state.status and "Maintenance" in state.status
	assert "o to view" in state.status
	listed = store.list_notices("acme.reviewer")
	assert listed and listed[0]["subject"] == "Maintenance"


def test_a_message_can_carry_an_attachment_beside_its_body(env, tmp_path):
	"""Protocol 9's whole point, reachable from the console: the explanation
	and its evidence in ONE message."""
	store = env
	root = tmp_path / "inst" / "root"
	(root / "EVIDENCE.md").write_bytes(b"the evidence\n")
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "With evidence":
		_press(state, store, ord(char))
	_press(state, store, K.TAB)
	# SUPERSEDED INPUT: this used to type `src:EVIDENCE.md` -- Baton's own
	# locator -- straight into the field. Slawomir ruled that form out of the
	# UI entirely: Enter on the empty path opens a picker of configured roots,
	# and the path is typed relative to the one chosen.
	_press(state, store, K.ENTER_LF)
	assert state.mode == "pick_root", state.mode
	_press(state, store, _pick_root(state, "src"))
	for char in "EVIDENCE.md":
		_press(state, store, ord(char))
	step(state, store, 5, 100, 24, edit_fn=lambda seed: ("see attached", "imported"))
	_send(state, store)
	assert state.mode == MODE_BROWSE, state.status
	mid = store.scan("acme.reviewer")["pending"][0]["id"]
	parts = store.get_message(mid)["parts"]
	assert [p["storage"] for p in parts] == ["inline", "external"]
	assert parts[1]["attach"]["path"] == "EVIDENCE.md"


def test_compose_keeps_the_buffer_when_sending_fails(env):
	"""The human typed it. Losing their words because the recipient was
	misspelled would be the console destroying work the protocol did not."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	step(state, store, 5, 100, 24, edit_fn=lambda seed: ("careful text", "imported"))
	# The recipient is valid, so break the SEND instead -- the point is that
	# a failure keeps the human's words, not how the failure was caused.
	store = _Broken(store, {"send"})
	assert _send(state, store) is True
	assert "failed" in state.status
	assert state.compose["body"] == "careful text"     # not discarded
	assert state.mode != MODE_BROWSE


def test_escape_discards_a_composition(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"), ord("x"), K.ESC)
	assert state.mode == MODE_BROWSE and state.compose == {}


@pytest.mark.parametrize("key", [ord("q"), ord("c"), ord("R"), ord("N")])
def test_command_letters_are_text_while_composing(env, key):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	assert _press(state, store, key) is True
	assert state.compose["subject"] == chr(key)


# -- gap 3: quitting with work outstanding --------------------------------

def test_q_requires_confirmation_when_a_claim_is_unresolved(env):
	"""Policy is that a claim is disposed immediately. Reopen making an
	abandoned claim recoverable is not a reason to let a stray keystroke
	abandon it quietly."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                  # claim it
	assert step(state, store, ord("q"), 100, 24) is True     # did NOT quit
	assert state.mode == MODE_CONFIRM_QUIT
	assert "still owe" in state.status
	# Anything other than Y stays -- including Enter, hit reflexively.
	assert step(state, store, K.ENTER_LF, 100, 24) is True
	assert state.mode == MODE_BROWSE
	assert state.unresolved_count() == 1
	# Y quits deliberately.
	step(state, store, ord("q"), 100, 24)
	assert step(state, store, ord("Y"), 100, 24) is False


def test_q_quits_immediately_when_nothing_is_owed(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert step(state, store, ord("q"), 100, 24) is False
	# And after resolving a claim, it quits again without asking.
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("c"))
	assert state.unresolved_count() == 0
	assert step(state, store, ord("q"), 100, 24) is False


# -- gap 4: failures are visible status, not a teardown -------------------

def test_losing_a_claim_race_is_reported_not_fatal(env):
	"""Another consumer took the exact message between the refresh and the
	keystroke. Ordinary, and the console must survive it with honest state."""
	store = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Contested", body=b"x\n")
	state = _ready(store)
	# Someone else claims it first, behind our back.
	other = store.claim("acme.implementer", message_id=mid)
	assert step(state, store, K.ENTER_LF, 100, 24) is True    # still alive
	assert "failed" in state.status
	assert state.opened is None                              # no false target
	# The model re-read reality: the row is now shown as claimed.
	assert state.rows[0]["state"] == "claimed"
	store.close_claim(other["claim_id"], participant="acme.implementer")


def test_losing_the_claim_underneath_a_draft_discards_it_honestly(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	for char in "my answer":
		_press(state, store, ord(char))
	# Recover the claim underneath, so the reply cannot land.
	store.recover_claim(state.opened["claim_id"], participant="hq.lead", reason="taken")
	assert _send(state, store) is True
	# Definite, not "either way": the reply did not commit, the console is
	# alive, the bar says why, and the model no longer claims an actionable
	# target it does not have.
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	assert state.status_severity in ("error", "warning")
	assert state.opened is None or state.opened.get("claim_id") is None
	assert state.unresolved_count() == 0        # the claim really is gone


def test_a_failed_close_leaves_the_model_honest(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	store.recover_claim(state.opened["claim_id"], participant="hq.lead", reason="taken")
	assert _press(state, store, ord("c")) is True
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	# The console tells the human the truth about what they now hold.
	state.refresh(store)
	assert state.unresolved_count() == 0


# -- materialize must not bypass the claim boundary -----------------------

def test_m_on_a_pending_preview_writes_nothing(env, tmp_path):
	"""Reported by baton.reviewer, reproduced before fixing.

	Writing bytes to disk is reading them in the most durable form there is.
	Allowing `m` from a preview let the console put message content on the
	filesystem without the human ever claiming it -- the preview boundary
	bypassed by the one action that makes the bypass permanent."""
	store = env
	target = tmp_path / "proj"
	target.mkdir()
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Unclaimed", body=b"# SECRET CONTENT\n")
	state = _ready(store)
	state.projection_dir = str(target)
	assert _press(state, store, ord("m")) is True       # still running
	assert list(target.iterdir()) == []                  # no file
	assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
	# The refusal names what is missing, not a keystroke: "press Enter to
	# claim" stopped being the normal path when selection began claiming, and
	# it cannot help on a row that is not claimable at all.
	assert "hold the claim for" in state.status
	# And after an explicit claim it works.
	_press(state, store, K.ENTER_LF, ord("m"))
	written = list(target.iterdir())
	assert len(written) == 1 and written[0].read_bytes() == b"# SECRET CONTENT\n"


def test_the_core_enforces_materialize_ownership_not_just_the_ui(env, tmp_path):
	"""A rule that lives only in the front end is one refactor from not
	existing, so the core refuses too."""
	store = env
	target = tmp_path / "proj"
	target.mkdir()
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Owned", body=b"content\n")
	claim = store.claim("acme.implementer", message_id=mid)
	with pytest.raises(core.BatonError, match="belongs to"):
		store.materialize_claimed_part(claim["claim_id"], "acme.reviewer", str(target))
	assert list(target.iterdir()) == []
	# The rightful owner succeeds, so the refusal is permission, not breakage.
	assert store.materialize_claimed_part(
		claim["claim_id"], "acme.implementer", str(target))
	store.close_claim(claim["claim_id"], participant="acme.implementer")
	with pytest.raises(core.BatonError, match="not active"):
		store.materialize_claimed_part(claim["claim_id"], "acme.implementer", str(target))


def test_materialize_refuses_without_a_projection_directory(env):
	"""Never the process working directory: the console may be launched from
	anywhere, and writing message content into whatever repository the human
	happened to be in is not a default anyone would choose."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert state.projection_dir == ""
	_press(state, store, K.ENTER_LF)
	assert _press(state, store, ord("m")) is True
	assert "no projection directory" in state.status


# -- every core call is guarded -------------------------------------------

class _Broken:
	"""A store whose chosen operation always fails, to prove the console
	survives an async failure rather than taking the human's context down."""

	def __init__(self, real, failing):
		self._real = real
		self._failing = failing

	def __getattr__(self, name):
		if name in self._failing:
			def boom(*args, **kwargs):
				raise core.BatonError("simulated authority failure", core.EXIT_RACE)
			return boom
		return getattr(self._real, name)


def test_a_failed_poll_keeps_the_previous_rows(env):
	store = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	state = _ready(store)
	before = [r["id"] for r in state.rows]
	state.refresh(_Broken(store, {"scan"}))
	assert [r["id"] for r in state.rows] == before        # stale, but coherent
	assert "failed" in state.status and state.status_severity == "error"
	assert len(render(state, 100, 24)) == 24              # still renders


def test_a_failed_notice_listing_keeps_the_previous_rows(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="M", body=b"x\n")
	state = _ready(store)
	before = [r["id"] for r in state.rows]
	# The METHOD the console actually calls: MESSAGES lists notice ACTIVITY,
	# seen and unseen, since a seen notice stopped disappearing.
	state.refresh(_Broken(store, {"list_notice_activity"}))
	assert [r["id"] for r in state.rows] == before
	assert "failed" in state.status


def test_a_failed_preview_keeps_what_was_displayed(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="M", body=b"x\n")
	state = _ready(store)
	shown = state.detail
	state.preview(_Broken(store, {"preview_message"}))
	assert state.detail is shown
	assert "failed" in state.status


def test_a_claim_that_cannot_be_read_back_stays_visibly_owed(env):
	"""The claim COMMITTED. If reading it back fails, the obligation is real
	and must stay on screen -- a claim behind a blank pane is still a claim,
	and hiding it is how one gets abandoned."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="M", body=b"x\n")
	state = _ready(store)
	broken = _Broken(store, {"reopen_claim"})
	assert step(state, broken, K.ENTER_LF, 100, 24) is True
	assert store.conn.execute(
		"SELECT COUNT(*) FROM claims WHERE state='active'").fetchone()[0] == 1
	assert state.opened is not None and state.opened["claim_id"]
	assert "still owes" in state.status
	assert state.unresolved_count() == 1
	assert "1 awaiting" in "\n".join(render(state, 100, 24))


def test_a_reply_that_fails_while_the_claim_is_still_ours_keeps_everything(env):
	"""The case the previous test did NOT cover, and the one that matters:
	the claim is still active, the authority merely refused the reply.

	The human's words must survive, the obligation must stay visible, and
	nothing may commit. Previously the implementation looked designed to do
	this and no tripwire proved it."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Still mine", body=b"?\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	for char in "a careful answer":
		_press(state, store, ord(char))
	claim_id = state.opened["claim_id"]

	broken = _Broken(store, {"reply"})
	assert _send(state, broken) is True                         # console alive
	assert state.draft.endswith("a careful answer")             # words kept, exactly
	assert state.mode == MODE_REPLY                             # still composing
	assert state.status_severity == "error" and "failed" in state.status
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	# The claim is untouched and still owed.
	assert store.conn.execute(
		"SELECT state FROM claims WHERE claim_id=?", (claim_id,)).fetchone()[0] == "active"
	assert state.unresolved_count() == 1
	assert "1 awaiting" in "\n".join(render(state, 100, 24))
	# And retrying against the healthy store sends the same words.
	assert _send(state, store) is True
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 1
	assert state.unresolved_count() == 0


def test_a_failed_preview_never_describes_another_row(env):
	"""Reported by baton.reviewer. Keeping the old detail on a preview failure
	could leave message A's headers beside a selection on message B -- and the
	human would reasonably believe the pane describes what the cursor is on,
	then press Enter and claim something else. An error in the bar does not
	make that safe."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="AAA", body=b"a\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="BBB", body=b"b\n")
	state = _ready(store)
	state.preview(store)
	first = state.selected["id"]
	assert state.detail["preview"]["id"] == first

	# The failure mode MOVED with claim-on-highlight: selecting a row now
	# claims it, so the way a move can fail is a lost race on the claim rather
	# than a failed preview. The property is the ruling's fail-closed rule and
	# is unchanged -- keep the intended row selected, show the error, and
	# never show another row's content.
	broken = _Broken(store, {"claim", "preview_message"})
	state.move(1, broken)                       # cursor moves to the other row
	intended = state.selected["id"]
	assert intended != first
	assert state.status_severity == "error"
	assert state.opened is None, "a failed claim left a target armed"
	shown = state.detail or {}
	for key in ("delivery", "received", "sent", "notice"):
		assert key not in shown, "content was shown after a failed claim"
	assert state.detail_row in (None, ("message", intended)), (
		"the pane describes a row the cursor is not on")
	assert state.selected["id"] == intended, "the selection moved on failure"


def test_a_failed_preview_of_the_same_row_keeps_its_own_detail(env):
	"""The other side: a transient failure re-previewing the SAME row may keep
	what is displayed, because it still describes that row."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="AAA", body=b"a\n")
	state = _ready(store)
	state.preview(store)
	shown = state.detail
	state.preview(_Broken(store, {"preview_message"}))
	assert state.detail is shown
	assert state.detail_row == ("message", state.selected["id"])


# -- arrow keys must not depend on terminfo -------------------------------

@pytest.mark.parametrize("tail,expected", [
	("[A", K.KEY_UP), ("OA", K.KEY_UP),
	("[B", K.KEY_DOWN), ("OB", K.KEY_DOWN),
	("[5~", K.KEY_PPAGE), ("[6~", K.KEY_NPAGE),
	("[Z", K.SHIFT_TAB),
])
def test_escape_sequences_decode_without_curses(tail, expected):
	"""Trial defect: on the deployment terminal `getch` returned raw 27, 91,
	66 for Down, so arrows did nothing at all. These sequences are fixed by
	ANSI, so decoding them removes a dependency on the terminal database."""
	assert K.decode_escape(tail) == expected


def test_a_bare_escape_is_not_swallowed_by_the_decoder():
	"""ESC cancels a draft. A decoder that consumed it would take away the
	only way out of reply mode."""
	assert K.decode_escape("") is None
	assert K.decode_escape("x") is None


def test_both_arrows_and_letters_move_the_cursor(env):
	store = env
	for i in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	state = _ready(store)
	for down, up in ((K.KEY_DOWN, K.KEY_UP), (ord("j"), ord("k"))):
		start = state.cursor
		_press(state, store, down, down)
		assert state.cursor == start + 2
		_press(state, store, up, up)
		assert state.cursor == start


# -- Vim browse bindings ---------------------------------------------------

def test_gg_and_G_jump_to_the_ends(env):
	store = env
	for i in range(12):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i:02d}", body=b"x\n")
	state = _ready(store)
	_press(state, store, ord("G"))
	assert state.cursor == len(state.rows) - 1
	_press(state, store, ord("g"), ord("g"))
	assert state.cursor == 0


def test_a_lone_g_does_nothing_at_all(env):
	"""`g` is a PREFIX. A prefix that also acted would make every abandoned
	`gg` a side effect -- which is why manual refresh is `Ctrl+r`."""
	store = env
	for i in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	store.send_notice("hq.lead", kind="announcement", subject="N", body=b"n\n")
	state = _ready(store)
	state.cursor = 2
	state.preview(store)
	# ONE `g`. (Ten would be five `gg` jumps, which is the binding working.)
	assert _press(state, store, ord("g")) is True
	assert state.cursor == 2                       # did not move
	assert state.pending_prefix == "g"
	assert state.detail is not None                # nothing was opened or cleared
	assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
	assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
	assert store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0


def test_an_abandoned_g_prefix_cannot_combine_with_a_later_key(env):
	"""`g` then `j` must be a plain `j`, not a chord fired late."""
	store = env
	for i in range(6):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	state = _ready(store)
	state.cursor = 3
	state.preview(store)
	_press(state, store, ord("g"), ord("j"))
	assert state.cursor == 4                       # moved down by one
	assert state.pending_prefix == ""
	# A later `g` does not complete the abandoned one.
	_press(state, store, ord("g"))
	assert state.cursor == 4


def test_ctrl_r_refreshes_and_g_no_longer_does(env):
	"""Manual refresh is `Ctrl+r` (Slawomir's ruling): both plain-letter `r`
	spellings are reply keys, and `g` cannot take refresh back -- a prefix key
	that refreshed would make every abandoned `gg` a side effect.

	(HISTORICAL: this asserted plain `R` refreshes, from when it did, and the
	ruling that moved it said `R` had become the full editor reply. `R` is the
	QUICK reply now; the reason refresh is not on a plain letter is
	unchanged.)"""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="First", body=b"x\n")
	state = _ready(store)
	assert len(state.rows) == 1
	store.send("hq.lead", "acme.implementer", kind="q", subject="Second", body=b"y\n")
	_press(state, store, ord("g"))
	assert len(state.rows) == 1                    # `g` did not refresh
	_press(state, store, K.CTRL_R)
	assert len(state.rows) == 2


@pytest.mark.parametrize("key", [K.CTRL_U, K.CTRL_D])
def test_ctrl_u_and_ctrl_d_page_the_inbox(env, key):
	store = env
	for i in range(40):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i:02d}", body=b"x\n")
	state = _ready(store)
	if key == K.CTRL_U:
		_press(state, store, K.CTRL_D, K.CTRL_D)
	start = state.cursor
	_press(state, store, key)
	assert state.cursor != start
	assert any(line.startswith(">") for line in render(state, 100, 24))


def test_brackets_move_between_multipart_leaves(env):
	"""`[`/`]` are the only part navigation. (This also pressed `H`/`L`, which
	were aliases until `h`/`l` became sideways scrolling and the aliases were
	removed rather than left as a spelling nobody is told about.)"""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Rich", parts=[
		{"content_type": "text/markdown; charset=utf-8", "body": b"one\n"},
		{"content_type": "text/plain; charset=utf-8", "body": b"two\n"},
		{"content_type": "text/plain; charset=utf-8", "body": b"three\n"},
	])
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	assert state.part_cursor == 0
	_press(state, store, ord("]"), ord("]"))
	assert state.part_cursor == 2
	_press(state, store, ord("["))
	assert state.part_cursor == 1
	_press(state, store, ord("["))
	assert state.part_cursor == 0
	# ...and the removed aliases do nothing to the part cursor.
	_press(state, store, ord("L"), ord("H"))
	assert state.part_cursor == 0


@pytest.mark.parametrize("key", [ord("g"), ord("G"), ord("h"), ord("l"),
                                 ord("r"), K.CTRL_U, K.CTRL_D])
def test_no_browse_chord_fires_while_typing(env, key):
	"""Every Vim binding is a letter someone will type. In reply and compose
	modes they must be literal text, and the `gg` prefix must not accumulate
	behind a draft."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	before = state.cursor
	seeded = state.draft                       # `Re: S`, the quick-reply line
	assert _press(state, store, key) is True
	assert state.mode == MODE_REPLY
	assert state.cursor == before
	assert state.pending_prefix == ""
	if 32 <= key < 127:
		assert state.draft == seeded + chr(key)
	elif key == K.CTRL_U:
		# Ctrl+u is an EDITING key in the text modes by Slawomir's ruling --
		# kill to the start of the line. What this test is about is that its
		# BROWSE meaning (page up) did not fire, which the cursor assertion
		# above covers; it is not that the chord is inert.
		assert state.draft == ""
	else:
		assert state.draft == seeded           # other control keys are not text
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0


def test_vim_keys_are_literal_while_composing(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "gGhlR":
		_press(state, store, ord(char))
	assert state.compose["subject"] == "gGhlR"
	assert state.pending_prefix == ""


def test_a_jump_claims_only_its_destination(env):
	"""`gg`/`G` obey the same rule as every other move -- which is now
	claim-on-arrival. The constraint that matters is that a JUMP claims only
	the row it lands on, never the ones it passed over.

	(This asserted a jump claimed nothing and abandoned the target, from when
	selection was observational.)"""
	store = env
	for i in range(5):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)               # claim the first
	assert state.opened is not None
	first = state.opened["id"]
	_press(state, store, ord("G"))
	landed = state.selected["id"]
	assert landed != first
	assert state.opened["id"] == landed, "the target is not the row landed on"
	# EXACTLY the two rows visited, not the three skipped over.
	claimed = {r[0] for r in store.conn.execute(
		"SELECT message_id FROM claims").fetchall()}
	assert claimed == {first, landed}, f"a jump claimed skipped rows: {claimed}"
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0


# -- item 3: no typo path to a recipient ---------------------------------

def test_every_participant_is_addressable_exactly_once(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	labels = [label for label, _ in state.picker_entries()]
	addresses = [entry["address"] for _, entry in state.picker_entries()]
	configured = [p["address"] for p in store.list_participants()]
	assert addresses == sorted(configured)
	assert len(labels) == len(set(labels)) == len(addresses)
	assert len(addresses) == len(set(addresses))


def test_a_letter_selects_and_the_address_is_exact(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	target = "acme.reviewer"
	_press(state, store, _pick(state, target))
	assert state.mode == MODE_COMPOSE
	assert state.compose["to"] == target
	# And `to` is no longer editable, so there is no path back to a typo.
	assert "to" not in state.compose_fields
	for char in "zzz":
		_press(state, store, ord(char))
	assert state.compose["to"] == target


def test_the_picker_creates_nothing(env):
	"""Opening, paging and cancelling are observation."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	store.send_notice("hq.lead", kind="announcement", subject="N", body=b"n\n")
	state = _ready(store)
	for _ in range(5):
		_press(state, store, ord("n"))
		_press(state, store, K.TAB, K.TAB)
		_press(state, store, K.ESC)
	assert state.mode == MODE_BROWSE
	assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
	assert store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
	assert store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	assert store.conn.execute(
		"SELECT COUNT(*) FROM messages WHERE from_participant='acme.implementer'"
	).fetchone()[0] == 0


@pytest.mark.parametrize("key", [ord("q"), ord("c"), ord("R"), ord("j"), ord("g"),
                                 ord("m"), ord("r"), ord("G")])
def test_letters_cannot_trigger_commands_in_the_picker(env, key):
	"""The human is choosing who receives a message. A stray `c` or `q`
	reaching its browse meaning would act on the inbox behind the dialogue."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, ord("n"))
	alive = _press(state, store, key)
	assert alive is True                            # `q` did not quit
	assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
	assert store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	# A letter that names a participant selects; one that does not is ignored.
	if state.mode == MODE_COMPOSE:
		assert state.compose["to"] in [e["address"] for e in store.list_participants()]
	else:
		assert state.mode == MODE_PICK_RECIPIENT


def test_a_send_goes_only_to_the_selected_address(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "hq.lead"))
	for char in "for the lead":
		_press(state, store, ord(char))
	_send(state, store)
	assert state.mode == MODE_BROWSE, state.status
	rows = store.conn.execute(
		"SELECT to_participant, subject FROM messages "
		"WHERE from_participant='acme.implementer'").fetchall()
	assert [(r[0], r[1]) for r in rows] == [("hq.lead", "for the lead")]


def test_a_recipient_removed_before_send_fails_visibly_and_keeps_the_draft(env):
	"""Config can change under a composition. The error must be the expected
	one and the human's work must survive it."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "important":
		_press(state, store, ord(char))
	step(state, store, 5, 100, 24, edit_fn=lambda seed: ("careful body", "imported"))
	# The recipient disappears from the config between choosing and sending.
	del store.config["participants"]["acme.reviewer"]
	assert _send(state, store) is True
	assert "not declared in the config" in state.status
	assert state.status_severity == "error"
	assert state.mode == MODE_COMPOSE
	assert state.compose["subject"] == "important"
	assert state.compose["body"] == "careful body"


def test_the_picker_pages_when_there_are_more_than_twenty_six(tmp_path):
	"""Every configured participant must be reachable. A picker that silently
	truncated would hide addresses that exist."""
	home = tmp_path / "many"
	home.mkdir()
	path = str(home / "baton.json")
	participants = {f"team{i:02d}.member": {} for i in range(40)}
	participants["acme.implementer"] = {}
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 9, "generation": 1,
			"mailbox": {"name": "many"}, "participants": participants,
			"roots": {}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	with core.open_instance(path) as store:
		state = InboxState("acme.implementer")
		state.refresh(store)
		state.set_viewport(**layout_for(100, 24))
		state.begin_pick_recipient(store)
		# Pages are sized by what FITS, not by the 26 available letters.
		assert state.picker_page_size < len(state.recipients)
		assert state.picker_pages > 1
		reachable = set()
		for _ in range(state.picker_pages):
			reachable.update(entry["address"] for _, entry in state.picker_entries())
			state.picker_next_page()
		assert reachable == set(participants)


def test_the_picker_marks_the_operator_themselves(env):
	from baton_tui.render import render
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	screen = "\n".join(render(state, 100, 24))
	assert "acme.implementer" in screen and "(you)" in screen


def test_the_picker_never_labels_a_recipient_it_does_not_draw(env):
	"""Reported by baton.reviewer against the live 21-participant config at
	100x24: labels a-r drew, s-u were labelled and selectable but hidden
	behind the overflow marker. A shortcut the human cannot see is worse than
	one that does not exist -- it is a hidden control on a screen that claims
	to list everything."""
	from baton_tui.render import render
	store = env
	state = _ready(store)
	for columns, lines in ((100, 24), (80, 12), (40, 8), (133, 40)):
		layout = layout_for(columns, lines)
		if layout is None:
			continue
		state.set_viewport(**layout)
		state.begin_pick_recipient(store)
		screen = "\n".join(render(state, columns, lines))
		for label, entry in state.picker_entries():
			assert f"{label})" in screen, (
				f"{columns}x{lines}: label {label} is selectable but not drawn")
		state.cancel_picker()


def test_every_participant_is_reachable_by_paging_at_any_size(tmp_path):
	store_path = tmp_path / "many"
	store_path.mkdir()
	path = str(store_path / "baton.json")
	participants = {f"team{i:02d}.member": {} for i in range(30)}
	participants["acme.implementer"] = {}
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 9, "generation": 1,
			"mailbox": {"name": "many"}, "participants": participants,
			"roots": {}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	with core.open_instance(path) as store:
		for columns, lines in ((100, 24), (80, 10), (40, 8), (120, 50)):
			layout = layout_for(columns, lines)
			if layout is None:
				continue
			state = InboxState("acme.implementer")
			state.refresh(store)
			state.set_viewport(**layout)
			state.begin_pick_recipient(store)
			reachable = set()
			for _ in range(state.picker_pages):
				reachable.update(e["address"] for _, e in state.picker_entries())
				state.picker_next_page()
			assert reachable == set(participants), f"unreachable at {columns}x{lines}"


# -- round 3 item 3: a growing draft cannot scroll its own caret away -------

def _type(state, store, text, columns=100, lines=24):
	"""Feed characters through the real dispatch, so viewport-following is
	exercised the way a keystroke exercises it -- not by calling the model
	directly, which would prove only that the model works when driven
	correctly."""
	from baton_tui.driver import step
	for char in text:
		step(state, store, ord(char), columns, lines)


@pytest.mark.parametrize("columns,lines", [(100, 24), (80, 24), (61, 20), (40, 10)])
def test_a_long_reply_keeps_its_caret_on_screen(env, columns, lines):
	"""Reply mode has no scroll keys -- every printable key is text -- so a
	draft that outgrows the pane would scroll the line being typed out of
	sight and the human would be typing blind."""
	from baton_tui.render import detail_line_count, input_line_index
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=("context " * 300).encode())
	state = _ready(store)
	state.open_selected(store)
	state.begin_reply()
	state.set_viewport(**layout_for(columns, lines))
	_type(state, store, "the quick brown fox jumps over the lazy dog " * 6,
	      columns, lines)
	index = input_line_index(state, columns, lines)
	assert index >= 0, "no draft line was produced"
	# The caret's line is INSIDE the visible window, not merely produced.
	assert state.detail_offset <= index < state.detail_offset + state.detail_height
	# And the offset is a real position in the document, not past its end.
	total = detail_line_count(state, columns, lines)
	assert 0 <= state.detail_offset <= max(0, total - state.detail_height)


def test_a_long_compose_body_keeps_its_caret_on_screen(env):
	"""Same guarantee on the other typing path. Compose has more fields above
	the body, so it runs out of pane sooner than reply does."""
	from baton_tui.render import input_line_index
	store = env
	state = _ready(store)
	state.begin_compose(recipient="acme.reviewer")
	state.set_viewport(**layout_for(100, 24))
	state.compose_next_field(1)
	state.compose_next_field(1)          # onto the body field
	_type(state, store, "sentence after sentence with no newline anywhere " * 40)
	index = input_line_index(state, 100, 24)
	assert index >= 0
	assert state.detail_offset <= index < state.detail_offset + state.detail_height


def test_the_tail_of_a_long_draft_is_actually_drawn(env):
	"""The strongest form: the characters most recently typed appear on the
	SCREEN. Following the caret is the mechanism; seeing what you typed is
	the requirement."""
	from baton_tui.render import render
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=("context " * 300).encode())
	state = _ready(store)
	state.open_selected(store)
	state.begin_reply()
	state.set_viewport(**layout_for(100, 24))
	_type(state, store, "padding padding padding " * 20 + "ENDMARKER")
	screen = "\n".join(render(state, 100, 24))
	assert "ENDMARKER" in screen, "the end of the draft scrolled out of sight"


def test_following_the_caret_does_not_disturb_browse_scrolling(env):
	"""Browse mode has real scroll keys, and taking them over would be a
	regression dressed as a fix."""
	from baton_tui.driver import step
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=("line\n" * 200).encode())
	state = _ready(store)
	state.open_selected(store)
	state.set_viewport(**layout_for(100, 24))
	# Tab to DETAIL focus, then `j`. `J`/`K` are gone -- Slawomir ruled the
	# focused-pane model is the sole navigation model, with no hidden alias.
	step(state, store, K.TAB, 100, 24)
	for _ in range(5):
		step(state, store, ord("j"), 100, 24)
	assert state.detail_offset > 0, "j stopped scrolling the focused detail pane"


# -- re-review R2: a resize follows the caret with no keystroke ------------

@pytest.mark.parametrize("first,second", [
	((100, 24), (40, 10)),        # narrowing: the reported reproduction
	((100, 24), (60, 10)),
	((40, 10), (100, 24)),        # widening, which reflows just as much
	((80, 24), (200, 40)),
])
def test_resizing_brings_the_draft_tail_back_without_typing(env, first, second):
	"""Reported: compose at 100x24, resize to 40x10, and the tail and caret
	are gone until you type one more character -- the moment you most need to
	see what you already wrote.

	Following used to happen only at the end of `step`, so a resize moved the
	viewport without moving the offset. This drives the RESIZE path only: no
	key is pressed between the two layouts."""
	from baton_tui.driver import apply_layout
	from baton_tui.render import input_line_index, render
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"y\n")
	state = _ready(store)
	state.open_selected(store)
	state.begin_reply()
	apply_layout(state, *first)
	_type(state, store, "padding padding padding " * 20 + "ENDMARKER",
	      *first)

	apply_layout(state, *second)          # the resize, and nothing else
	columns, lines = second
	index = input_line_index(state, columns, lines)
	assert index >= 0
	assert state.detail_offset <= index < state.detail_offset + state.detail_height, (
		f"{first} -> {second}: the caret line is outside the window after resize")
	assert "ENDMARKER" in "\n".join(render(state, columns, lines)), (
		f"{first} -> {second}: the draft tail is invisible after resize")


def test_resizing_while_browsing_does_not_move_the_detail_offset(env):
	"""Following applies to typing modes only. Taking over the reader's
	scroll position on every resize would be a regression dressed as a fix."""
	from baton_tui.driver import apply_layout
	from baton_tui.render import detail_line_count
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=("line\n" * 200).encode())
	state = _ready(store)
	state.open_selected(store)
	apply_layout(state, 100, 24)
	state.scroll_detail(30, detail_line_count(state, 100, 24))
	before = state.detail_offset
	apply_layout(state, 80, 20)
	assert state.detail_offset == before


def test_the_picker_capacity_is_remeasured_on_resize(env):
	"""Capacity depends on width through the wrapped entries, so a resize has
	to recompute it or the picker offers letters the new size cannot draw."""
	from baton_tui.driver import apply_layout
	store = env
	state = _ready(store)
	state.recipients = [{"address": f"team{i:02d}.member"} for i in range(21)]
	apply_layout(state, 100, 24)
	wide = state.picker_page_size
	apply_layout(state, 40, 10)
	assert state.picker_page_size < wide
	apply_layout(state, 100, 24)
	assert state.picker_page_size == wide


# -- addendum: Enter arms a send, only y publishes -------------------------

def _drafted(store, mode="reply"):
	"""A state parked in one of the three typing modes with a draft in it."""
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"x\n")
	state = _ready(store)
	if mode == "reply":
		_press(state, store, K.ENTER_LF, ord("R"))
		# The quick-reply line IS the draft. Replace the seeded subject so
		# the assertions below read clearly.
		state.draft = "my answer"
	elif mode == "compose":
		_press(state, store, ord("n"))
		_press(state, store, _pick(state, "acme.reviewer"))
		for char in "a subject":
			_press(state, store, ord(char))
	else:
		_press(state, store, ord("N"))
		for char in "an announcement":
			_press(state, store, ord(char))
	return state


def _sent_count(store):
	return (store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
	        + store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
	        + store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0])


@pytest.mark.parametrize("mode", ["reply", "compose", "notice"])
def test_enter_arms_a_confirmation_instead_of_publishing(env, mode):
	"""Compose opens on the subject and a subject alone is enough, so Enter
	had become a ONE-keystroke publish reachable from a field a newcomer is
	still filling in -- and Enter is the key people press to mean "next
	field"."""
	store = env
	state = _drafted(store, mode)
	before = _sent_count(store)
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_CONFIRM_SEND
	assert _sent_count(store) == before, "Enter published without confirmation"
	assert "Send?" in state.status


_PUBLISHED_TABLE = {"reply": "dispositions", "compose": "messages",
                    "notice": "notices"}


@pytest.mark.parametrize("mode", ["reply", "compose", "notice"])
def test_y_publishes_and_keeps_the_quick_path_at_two_strokes(env, mode):
	store = env
	state = _drafted(store, mode)
	# Count the table this mode WRITES, not a total: a reply commits both a
	# disposition and its response message, so a total moves by two and an
	# assertion on "+1" would be pinning the wrong thing.
	table = _PUBLISHED_TABLE[mode]
	before = store.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
	_press(state, store, K.ENTER_LF, ord("y"))
	after = store.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
	assert after == before + 1
	assert state.mode == MODE_BROWSE


@pytest.mark.parametrize("mode", ["reply", "compose", "notice"])
@pytest.mark.parametrize("key", [ord("n"), ord("N"), K.ESC])
def test_declining_returns_the_same_draft_and_field(env, mode, key):
	"""A cancelled send that cost the human their message would be worse than
	no confirmation at all."""
	store = env
	state = _drafted(store, mode)
	draft, compose, field = state.draft, dict(state.compose), state.compose_field
	before = _sent_count(store)
	_press(state, store, K.ENTER_LF, key)
	assert _sent_count(store) == before
	assert state.mode != MODE_CONFIRM_SEND
	assert state.draft == draft
	assert state.compose == compose
	assert state.compose_field == field, "the caret moved to another field"


@pytest.mark.parametrize("mode", ["reply", "compose", "notice"])
def test_a_second_enter_confirms(env, mode):
	"""`Send? Y/n` -- conventional shell semantics, yes as the default, so
	Enter answers it. The fast path is Enter, Enter.

	(An earlier rule made a second Enter inert, to keep a reflex keystroke
	from publishing. Slawomir superseded it: the first Enter still cannot
	publish, so the reflex now lands on a question that names what is about to
	happen with the draft still on screen behind it.)"""
	store = env
	state = _drafted(store, mode)
	table = _PUBLISHED_TABLE[mode]
	before = store.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
	_press(state, store, K.ENTER_LF, K.ENTER_LF)
	after = store.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
	assert after == before + 1, "Enter, Enter did not send"
	assert state.mode == MODE_BROWSE


@pytest.mark.parametrize("mode", ["reply", "compose", "notice"])
def test_the_first_enter_still_cannot_publish(env, mode):
	"""The property that survives the correction, and the reason the
	confirmation exists: compose opens on the subject and a subject alone is
	enough, so a single Enter must never be a publish."""
	store = env
	state = _drafted(store, mode)
	before = _sent_count(store)
	_press(state, store, K.ENTER_LF)
	assert _sent_count(store) == before, "the first Enter published"
	assert state.mode == MODE_CONFIRM_SEND


@pytest.mark.parametrize("mode", ["reply", "compose", "notice"])
def test_printable_keys_do_not_leak_into_the_draft_while_confirming(env, mode):
	"""The human is answering a question, not editing. A stray letter must
	neither reach the draft nor fire its browse meaning."""
	store = env
	state = _drafted(store, mode)
	draft, compose = state.draft, dict(state.compose)
	before = _sent_count(store)
	_press(state, store, K.ENTER_LF)               # arm it first
	assert state.mode == MODE_CONFIRM_SEND
	# `q` would quit, `c` would close a claim, `r` would start a reply.
	for key in (ord("q"), ord("c"), ord("R"), ord("z"), ord("1"), K.TAB):
		assert _press(state, store, key) is True, f"{chr(key) if key < 256 else key} exited"
	assert state.mode == MODE_CONFIRM_SEND
	assert state.draft == draft
	assert state.compose == compose
	assert _sent_count(store) == before


def test_the_draft_is_still_visible_while_confirming(env):
	"""A confirmation over a blank pane asks the human to approve something
	they can no longer see."""
	store = env
	state = _drafted(store, "reply")
	_press(state, store, K.ENTER_LF)
	from baton_tui.render import CONFIRM_SEND_FOOTER
	screen = render(state, 100, 24)
	assert "my answer" in "\n".join(screen)
	# EXACTLY ONE row asks, and it is the last row. The question must not be
	# duplicated into the detail pane, and there is no second footer row.
	asking = [line for line in screen if "Send now?" in line]
	assert len(asking) == 1, f"the question appears {len(asking)} times: {asking}"
	assert screen[-1].strip() == CONFIRM_SEND_FOOTER
	assert asking[0] is screen[-1]


def test_the_confirmation_footer_replaces_the_browse_keys(env):
	"""Advertising keys that are deliberately swallowed would teach the wrong
	thing at exactly the wrong moment."""
	store = env
	state = _drafted(store, "compose")
	_press(state, store, K.ENTER_LF)
	from baton_tui.render import CONFIRM_SEND_FOOTER
	screen = render(state, 100, 24)
	assert screen[-1].strip() == CONFIRM_SEND_FOOTER
	# The row ABOVE it is pane content, not a second footer row: no status
	# line, no severity marker, no "acting on" context.
	assert "Send" not in screen[-2]
	assert "acting on" not in screen[-2]
	assert "[!]" not in screen[-2]
	# And no browse key list anywhere: those keys are swallowed here.
	assert "gg/G first/last" not in "\n".join(screen[-1:])


def test_a_failed_confirmed_send_returns_to_the_draft(env):
	"""Declining is not the only way back: if the authority refuses, the
	human must land in their draft rather than in a dead confirmation."""
	store = env
	state = _drafted(store, "reply")
	broken = _Broken(store, {"reply"})
	assert _send(state, broken) is True
	assert state.mode == MODE_REPLY
	assert state.draft == "my answer"


def test_the_confirmation_footer_is_exactly_one_row_of_exact_text(env):
	"""Slawomir gave a literal target. Pinned literally, and pinned as a ROW
	COUNT: the screen must still be exactly `lines` rows, so the row the
	second footer line used to occupy goes to the panes rather than
	disappearing."""
	from baton_tui.render import CONFIRM_SEND_FOOTER, DIVIDER
	store = env
	for mode in ("reply", "compose", "notice"):
		state = _drafted(store, mode)
		for lines in (8, 12, 24, 40):
			ordinary = render(state, 100, lines)
			_press(state, store, K.ENTER_LF)
			confirming = render(state, 100, lines)
			assert len(confirming) == lines == len(ordinary)
			assert confirming[-1].strip() == CONFIRM_SEND_FOOTER
			assert "Send now?" not in ordinary[-1]
			# One MORE body row than the ordinary footer leaves: the panes grew
			# into the space instead of a row going missing. Counted as the rows
			# between the header and the footer, because STACKED gives the rule
			# a row of its own rather than a cell on every body row.
			assert len(confirming[1:-1]) == len(ordinary[1:-2]) + 1
			# And the rule is still exactly one row of the screen, in both.
			# It carries the `DETAIL` focus label now.
			for screen in (ordinary, confirming):
				assert sum(1 for line in screen
				           if line.lstrip().startswith("DETAIL ")
				           and DIVIDER in line) == 1
			_press(state, store, ord("n"))         # back to the draft


@pytest.mark.parametrize("columns", [40, 50, 60, 80, 100, 133])
def test_the_confirmation_footer_clips_safely_when_narrow(env, columns):
	"""The only permitted deviation from the literal text is right-edge
	clipping, and it must never overflow the terminal."""
	from baton_tui.render import CONFIRM_SEND_FOOTER
	from baton_tui.safe_text import display_width
	store = env
	state = _drafted(store, "compose")
	_press(state, store, K.ENTER_LF)
	row = render(state, columns, 24)[-1]
	assert display_width(row) <= columns
	if display_width(f"  {CONFIRM_SEND_FOOTER}") <= columns:
		assert row.strip() == CONFIRM_SEND_FOOTER
	else:
		# Clipped, but it still begins with the question -- the part that
		# cannot be allowed to fall off.
		assert row.strip().startswith("Send now? [Y/n]")


# The literal target, written out HERE rather than imported. Every other pin
# compares the rendered row against `CONFIRM_SEND_FOOTER`, which means editing
# that constant moves both sides of the assertion and the text can drift
# freely -- dropping the brackets passed every one of them. This is the copy
# that has to be changed deliberately.
LITERAL_CONFIRM_FOOTER = "Send now? [Y/n]   Enter or y = send   n or Esc = keep editing"


def test_the_confirmation_footer_matches_the_literal_target(env):
	"""Slawomir supplied this string exactly. Pinned by value, at a width
	where the whole legend fits."""
	store = env
	for mode in ("reply", "compose", "notice"):
		state = _drafted(store, mode)
		_press(state, store, K.ENTER_LF)
		screen = render(state, 120, 24)
		assert screen[-1].strip() == LITERAL_CONFIRM_FOOTER, (
			f"{mode}: {screen[-1].strip()!r}")
		_press(state, store, ord("n"))


def test_the_shipped_constant_is_the_literal_target():
	"""And the constant the rest of the suite compares against is that same
	string, so the other pins are anchored to something real."""
	from baton_tui.render import CONFIRM_SEND_FOOTER
	assert CONFIRM_SEND_FOOTER == LITERAL_CONFIRM_FOOTER


# -- SENT view: authority-backed outbound history --------------------------

def _writes(store):
	"""Every table a delivery would touch. The SENT view must move none of
	them: reading your own outbox is not a delivery, and if it were, a sender
	could consume the message their recipient is waiting for."""
	return tuple(store.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
	             for t in ("claims", "notice_seen", "dispositions", "messages",
	                       "notices", "quarantines"))


def _sent(store, state):
	return {row["subject"]: row for row in state.sent_rows}


def _sent_glyph(row):
	"""What the SENT view draws for one outbound row, through the same
	function the messages pane uses."""
	from baton_tui.render import ROW_MESSAGE, ROW_NOTICE, _status_glyph
	return _status_glyph({**row,
	                      "row_type": (ROW_NOTICE if row.get("row_kind") == "notice"
	                                   else ROW_MESSAGE),
	                      "direction": "out"})


def test_every_directed_state_gets_its_own_badge(env):
	"""The badge is the only thing distinguishing a message waiting for pickup
	from one already answered, so every state the authority can report needs
	one -- `?` on screen means the console met a state it does not
	understand.

	(Brackets SUPERSEDED by the one-cell status column. The letters, the
	coverage of every schema state, and the unknown fallback are unchanged.)"""
	from baton_tui.render import SENT_BADGES
	store = env
	# Reachable states, driven through the real authority.
	# Sent FIRST and claimed, so `queued` can be sent afterwards and stay
	# pending -- claim() is FIFO, so sending it first would have picked it up.
	pick = store.send("acme.implementer", "acme.reviewer", kind="q",
	                  subject="picked", body=b"b\n")
	answered = store.send("acme.implementer", "acme.reviewer", kind="q",
	                      subject="answered", body=b"c\n")
	shut = store.send("acme.implementer", "acme.reviewer", kind="q",
	                  subject="shut", body=b"d\n")
	claims = {}
	for _ in range(3):
		claim = store.claim("acme.reviewer")
		claims[claim["message_id"]] = claim["claim_id"]
	store.reply(claims[answered], participant="acme.reviewer", kind="response",
	            body=b"ok\n")
	store.close_claim(claims[shut], participant="acme.reviewer", outcome="done")
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="queued", body=b"a\n")

	state = _ready(store)
	rows = _sent(store, state)
	# SUPERSEDED: the old badge helper no longer answers the four states a human has
	# an obligation about. `_status_glyph` does, for BOTH views, which is what
	# stopped SENT and MESSAGES disagreeing about one row. What is asserted
	# now is that every schema state still gets an answer from SOMEWHERE.
	from baton_tui.render import COMPLETED, PICKED_UP, QUEUED
	glyphs = {name: _sent_glyph(row) for name, row in rows.items()}
	assert glyphs["queued"] == QUEUED
	assert glyphs["picked"] == PICKED_UP
	assert glyphs["answered"] == COMPLETED
	assert glyphs["shut"] == COMPLETED, "closed and replied read the same now"
	schema_states = {"pending", "claimed", "completed", "closed", "expired",
	                 "quarantined"}
	answered_somewhere = set(SENT_BADGES) | {"pending", "claimed", "completed",
	                                         "closed"}
	assert schema_states <= answered_somewhere, \
		"a state the authority can produce has no glyph at all"


def test_a_notice_is_visibly_distinct_and_shows_receipts(env):
	"""A notice has no claim, so `pending` and `claimed` would both be lies.
	It reports what it actually has: receipts and a lifetime."""
	store = env
	store.send_notice("acme.implementer", kind="announcement",
	                  subject="broadcast", body=b"x\n")
	state = _ready(store)
	row = _sent(store, state)["broadcast"]
	from baton_tui.state import VIEW_SENT
	from baton_tui.render import NOTICE_BADGE
	state.select_view(VIEW_SENT)
	state.refresh(store)
	listed = [l for l in render(state, 120, 24) if "broadcast" in l][0]
	assert NOTICE_BADGE in listed, "an authored notice lost its own mark"
	state.select_view("inbox")
	state.refresh(store)
	assert row["row_kind"] == "notice"
	assert row["to_participant"] is None
	assert row["seen_count"] == 0
	assert row["expires_ts"]
	store.mark_notice_seen("acme.reviewer", row["id"])
	state.refresh(store)
	assert _sent(store, state)["broadcast"]["seen_count"] == 1


def test_sent_is_newest_first_and_mirrors_the_queue_order(env):
	"""Newest-first is defined as the exact reverse of the order the
	authority itself claims in, so the two can never disagree about which
	message is older."""
	store = env
	for index in range(6):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"m{index}", body=b"x\n")
	state = _ready(store)
	keys = [(row["created_ts"], row["id"]) for row in state.sent_rows]
	assert keys == sorted(keys, reverse=True)


def test_a_sent_message_and_a_reply_response_both_appear(env):
	"""A reply creates a response MESSAGE authored by the replier. It is
	outbound traffic and belongs in their sent view."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="asked",
	           body=b"?\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	for char in "my answer":
		_press(state, store, ord(char))
	_send(state, store)
	state.refresh(store)
	assert state.sent_rows, "the reply response is not in the sender's sent view"
	assert any(row["row_kind"] == "message" for row in state.sent_rows)


def test_a_pending_message_becomes_claimed_on_refresh(env):
	"""The point of the view: a sender watches pickup happen. An in-memory
	recently-sent list could never show this."""
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="watch",
	           body=b"x\n")
	state = _ready(store)
	assert _sent(store, state)["watch"]["state"] == "pending"
	store.claim("acme.reviewer")            # someone else picks it up
	state.refresh(store)
	assert _sent(store, state)["watch"]["state"] == "claimed"


def test_switching_to_sent_shows_one_list_and_writes_nothing(env):
	"""One key each, no split. Switching TO SENT still writes nothing --
	sent rows are read-only whichever door you arrive by.

	(This also asserted that switching BACK to MESSAGES wrote nothing. A view
	switch establishes the destination's highlighted row like startup does, so
	arriving on a pending inbound row claims it; the case is pinned separately
	below.)"""
	from baton_tui.state import VIEW_SENT
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="in",
	           body=b"x\n")
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="out",
	           body=b"y\n")
	state = _ready(store)
	state.select_row(store)                           # settle the inbox first
	before = _writes(store)
	_press(state, store, ord("o"))
	assert state.view == VIEW_SENT
	screen = render(state, 100, 24)
	assert "SENT" in screen[0]
	# The SAME list pane, showing one list at a time: the outbound subject is
	# drawn and no inbox row is.
	body = "\n".join(screen)
	assert "out" in body and "in " not in body
	assert _writes(store) == before, "switching to SENT wrote to the authority"


def test_each_view_keeps_its_own_selection(env):
	store = env
	for index in range(5):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"in{index}", body=b"x\n")
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"out{index}", body=b"y\n")
	state = _ready(store)
	_press(state, store, ord("j"), ord("j"), ord("j"))
	inbox_at = state.cursor
	assert inbox_at == 3
	_press(state, store, ord("o"))
	assert state.sent_cursor == 0, "the sent view inherited the inbox cursor"
	_press(state, store, ord("j"))
	_press(state, store, ord("i"))
	assert state.cursor == inbox_at, "the inbox lost its place"
	_press(state, store, ord("o"))
	assert state.sent_cursor == 1, "the sent view lost its place"


def test_opening_a_sent_item_creates_nothing(env):
	"""Read-only in the strongest sense: no claim, no receipt, no transition,
	no audit row."""
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="mine",
	           body=b"the body\n")
	store.send_notice("acme.implementer", kind="announcement", subject="bcast",
	                  body=b"n\n")
	state = _ready(store)
	_press(state, store, ord("o"))
	before = _writes(store)
	for _ in range(len(state.sent_rows)):
		_press(state, store, K.ENTER_LF)
		_press(state, store, ord("j"))
	assert _writes(store) == before, "opening a sent item wrote to the authority"
	assert state.opened is None, "a sent item became an action target"


def test_opening_a_sent_message_shows_its_content(env):
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="mine",
	           body=b"the exact body\n")
	state = _ready(store)
	_press(state, store, ord("o"), K.ENTER_LF)
	screen = "\n".join(render(state, 100, 24))
	assert "the exact body" in screen
	assert "read only" in screen.lower()


def test_a_sent_message_belonging_to_someone_else_is_refused(env):
	"""Owner-checked in the CORE, not merely hidden by the view."""
	import baton_core as core
	store = env
	other = store.send("acme.reviewer", "acme.implementer", kind="q",
	                   subject="theirs", body=b"x\n")
	with pytest.raises(core.BatonError):
		store.open_sent(other, "acme.implementer")


def test_sent_survives_a_restart(env, tmp_path):
	"""Authority-backed, not process memory. A recently-sent list would be
	empty here, and would have looked correct until the first restart."""
	import baton_core as core
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="durable",
	           body=b"x\n")
	fresh = InboxState("acme.implementer")
	fresh.refresh(store)
	assert "durable" in _sent(store, fresh)


def test_gc_removes_a_row_from_sent(env):
	"""Retention stays authoritative: this is a view, not an archive, and it
	must not keep a copy the protocol has collected."""
	store = env
	store.send_notice("acme.implementer", kind="announcement", subject="fleeting",
	                  body=b"x\n", ttl_seconds=1)
	state = _ready(store)
	assert "fleeting" in _sent(store, state)
	store.expire("acme.implementer", notice_id=_sent(store, state)["fleeting"]["id"])
	state.refresh(store)
	assert "fleeting" not in _sent(store, state), "a collected notice lingered"


# -- reply to a notice: a new directed message, never a claim --------------

def _opened_notice(store, subject="All hands", body=b"meeting at 3\n"):
	store.send_notice("acme.reviewer", kind="announcement", subject=subject,
	                  body=body)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)             # open, committing the receipt
	return state


def test_replying_to_a_notice_addresses_its_author_with_no_picker(env):
	"""The human said "reply to this", which answers both who and about what.
	Making them pick the author from a list they did not need would be asking
	a question whose answer is already on screen."""
	from baton_tui.state import MODE_COMPOSE, MODE_PICK_RECIPIENT
	store = env
	state = _opened_notice(store)
	assert _press(state, store, ord("R")) is True
	assert state.mode == MODE_COMPOSE
	assert state.mode != MODE_PICK_RECIPIENT, "a picker appeared"
	assert state.compose["to"] == "acme.reviewer"


def test_a_notice_reply_copies_the_subject_exactly(env):
	"""Exactly: not prefixed, not summarised. The author identifies their
	broadcast by that line."""
	store = env
	state = _opened_notice(store, subject="Quarterly maintenance window")
	_press(state, store, ord("R"))
	assert state.compose["subject"] == "Quarterly maintenance window"


def test_a_notice_reply_starts_in_the_subject(env):
	"""The caret is where the words go -- and for a quick reply the words go
	in the subject line, which becomes the content through the shorthand.

	SUPERSEDED: this used to assert the caret started in an inline BODY
	field. There is no inline body editor any more."""
	store = env
	state = _opened_notice(store)
	_press(state, store, ord("R"))
	assert state.compose_fields[state.compose_field] == "subject"
	for char in " — on my way":
		_press(state, store, ord(char))
	assert state.compose["subject"] == "All hands — on my way"


def test_beginning_and_cancelling_a_notice_reply_changes_no_receipts(env):
	"""Only the explicit open commits a receipt. Deciding to answer, and then
	deciding not to, must leave the broadcast exactly as it was."""
	store = env
	state = _opened_notice(store)
	before = (store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0],
	          store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0])
	_press(state, store, ord("R"))
	for char in "half a thought":
		_press(state, store, ord(char))
	_press(state, store, K.ESC)
	after = (store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0],
	         store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0])
	assert after == before


def test_a_notice_reply_creates_one_directed_message_and_no_claim(env):
	"""A broadcast has no claim to complete, and `responds_to` references a
	message -- so this is a new directed message, not a disposition wearing
	one."""
	store = env
	state = _opened_notice(store)
	claims_before = store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
	_press(state, store, ord("R"))
	_send(state, store)
	pending = store.scan("acme.reviewer")["pending"]
	assert len(pending) == 1
	assert pending[0]["subject"] == "All hands"
	assert store.conn.execute(
		"SELECT COUNT(*) FROM claims").fetchone()[0] == claims_before
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	# And it does not pretend to answer the notice structurally.
	assert store.conn.execute(
		"SELECT responds_to FROM messages WHERE id=?",
		(pending[0]["id"],)).fetchone()[0] is None


def test_the_notice_stays_readable_while_the_reply_is_typed(env):
	"""The draft must not replace what is being answered -- and the notice
	BODY has to be there, not just its headers."""
	store = env
	state = _opened_notice(store, body=b"the exact announcement\n")
	_press(state, store, ord("R"))
	for char in "understood":
		_press(state, store, ord(char))
	screen = "\n".join(render(state, 100, 24))
	assert "the exact announcement" in screen, "the original vanished"
	assert "All hands" in screen
	assert "understood" in screen


def test_declining_the_send_restores_the_notice_reply_draft(env):
	store = env
	state = _opened_notice(store)
	_press(state, store, ord("R"))
	for char in " keep this":
		_press(state, store, ord(char))
	_press(state, store, K.ENTER_LF, ord("n"))
	assert state.compose["subject"] == "All hands keep this"
	assert state.compose["to"] == "acme.reviewer"
	screen = "\n".join(render(state, 100, 24))
	assert "meeting at 3" in screen, "the original context was lost"


def test_a_notice_reply_appears_in_sent_and_tracks_state(env):
	store = env
	state = _opened_notice(store)
	_press(state, store, ord("R"))
	_send(state, store)
	state.refresh(store)
	rows = {row["subject"]: row for row in state.sent_rows}
	assert "All hands" in rows
	assert rows["All hands"]["row_kind"] == "message"
	assert rows["All hands"]["state"] == "pending"
	store.claim("acme.reviewer")
	state.refresh(store)
	assert {r["subject"]: r for r in state.sent_rows}["All hands"]["state"] == "claimed"


def test_a_directed_reply_keeps_the_original_visible_and_inherits_the_subject(env):
	"""The same UI rule as the notice path, and the subject arrives unchanged
	-- no stacked `Re:` chain."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Deploy plan", body=b"the original question\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	assert state.draft == "Deploy plan"
	for char in " — answering now":
		_press(state, store, ord(char))
	screen = "\n".join(render(state, 100, 24))
	assert "the original question" in screen, "the draft replaced the original"
	assert "answering now" in screen
	_send(state, store)
	response = store.scan("acme.reviewer")["pending"]
	assert len(response) == 1
	# Single prefix, and the edited line is what went out.
	assert response[0]["subject"] == "Deploy plan — answering now"


# -- Ctrl+e: an external editor for the body -------------------------------

def _editor(returns=None, message="draft imported", record=None):
	"""A fake `edit_fn`. `returns` may be a callable taking the seed."""
	def edit(seed):
		if record is not None:
			record.append(seed)
		if callable(returns):
			value = returns(seed)
		else:
			value = returns
		if value is None:
			return None, message
		return value, message
	return edit


def test_ctrl_e_edits_the_reply_body_and_publishes_nothing(env):
	"""Importing is not publishing. "Save and quit" is muscle memory; "send
	this to another person" is a decision."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"the question\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	before = store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0]
	step(state, store, 5, 100, 24, edit_fn=_editor("written elsewhere"))
	# The BODY, not the subject line: there is no inline body buffer to merge
	# with, which is the whole point of the model.
	assert state.reply_body == "written elsewhere"
	assert state.draft == "S", "the editor overwrote the subject line"
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == before
	assert state.mode == MODE_REPLY, "the editor left the typing mode"
	# The ordinary confirmation still stands.
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_CONFIRM_SEND


def test_a_printable_key_is_never_the_editor_shortcut(env):
	"""Every printable character in these modes is text. Stealing one would
	make a letter unusable in a message."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "eEx":
		_press(state, store, ord(char))
	assert state.compose["subject"] == "eEx"


def test_an_empty_reply_draft_is_seeded_with_a_quote(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"the original words\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	seeds = []
	step(state, store, 5, 100, 24, edit_fn=_editor("x", record=seeds))
	assert "acme.reviewer wrote:" in seeds[0]
	assert "> the original words" in seeds[0]


def test_an_existing_draft_is_opened_exactly_and_never_re_seeded(env):
	"""Silently re-seeding over words someone already wrote would destroy
	them, and they would not find out until the editor opened."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"the original words\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	step(state, store, 5, 100, 24, edit_fn=_editor("already imported"))
	seeds = []
	step(state, store, 5, 100, 24, edit_fn=_editor("kept", record=seeds))
	# Reopening gets EXACTLY the last imported body. No re-seed, no merge,
	# nothing lost.
	assert seeds[0] == "already imported"
	assert "wrote:" not in seeds[0]


def test_a_binary_original_is_not_quoted_into_the_draft(env):
	"""Quoting base64 into someone's reply helps nobody, and the original
	stays on screen for context either way."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           parts=[{"content_type": "image/png", "body": b"\x89PNG\r\n\x1a\n",
	                   "disposition": "attachment", "filename": "d.png"}])
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	seeds = []
	step(state, store, 5, 100, 24, edit_fn=_editor("typed", record=seeds))
	assert seeds[0] == ""
	assert "PNG" not in seeds[0]


def test_an_editor_failure_leaves_the_draft_untouched(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"q\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	step(state, store, 5, 100, 24, edit_fn=_editor("my words"))
	step(state, store, 5, 100, 24,
	     edit_fn=_editor(None, message="editor exited 1; draft unchanged"))
	assert state.reply_body == "my words"
	assert "draft unchanged" in state.status
	assert state.mode == MODE_REPLY


def test_the_original_stays_visible_after_returning_from_the_editor(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Deploy",
	           body=b"the original question\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	step(state, store, 5, 100, 24, edit_fn=_editor("imported body"))
	screen = "\n".join(render(state, 100, 24))
	assert "the original question" in screen
	# The body is summarised, not typed here -- a truncated preview would
	# invite editing the preview.
	# The body STATE stays; "(Ctrl-E to edit)" is a footer duplicate and is
	# gone. `^E` is still advertised, by the mode legend that owns it.
	assert "body:" in screen
	# Neither spelling. `Ctrl-E` was a hint in the work area and `^E` was the
	# footer's copy of it -- and there is no ordinary footer any more. `?`
	# help is where the editor key is documented.
	assert "Ctrl-E" not in screen
	assert "^E" not in screen
	assert "Ctrl+e" in _legend(state), "the affordance itself was lost"


def test_ctrl_e_edits_the_body_field_of_a_compose(env):
	"""Whatever field the caret is in: it is the only field an editor is worth
	launching for, and silently editing `attach` would be a surprise."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "a subject":
		_press(state, store, ord(char))
	step(state, store, 5, 100, 24, edit_fn=_editor("the long body"))
	assert state.compose["body"] == "the long body"
	assert state.compose["subject"] == "a subject", "the subject was overwritten"
	# `body` is not an inline field at all, so the caret never moves to it.
	assert "body" not in state.compose_fields


def test_a_notice_reply_seeds_the_quote_from_the_notice(env):
	store = env
	state = _opened_notice(store, body=b"the announcement text\n")
	_press(state, store, ord("R"))
	seeds = []
	step(state, store, 5, 100, 24, edit_fn=_editor("ack", record=seeds))
	assert "> the announcement text" in seeds[0]
	assert "acme.reviewer wrote:" in seeds[0]


def test_the_editor_never_sees_an_authority_path(env, tmp_path):
	"""Never pass storage paths to an editor: it is an arbitrary program, and
	the mailbox is the one file that must not be edited by hand."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"q\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	seen = {}

	def edit(seed):
		seen["seed"] = seed
		return "ok", "imported"

	step(state, store, 5, 100, 24, edit_fn=edit)
	assert "mailbox.sqlite3" not in seen["seed"]
	assert ".json" not in seen["seed"]


def test_no_editor_available_says_so_and_changes_nothing(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"q\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	step(state, store, 5, 100, 24)            # no edit_fn injected
	assert state.reply_body == ""
	assert "editor" in state.status


# -- the no-inline-body model ---------------------------------------------

def test_there_is_no_inline_body_field_anywhere(env):
	"""The superseding rule. Printable text never accumulates in a body
	buffer, so there is no inline-versus-editor merge boundary to get wrong --
	which is exactly why the hybrid was rejected."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	assert "body" not in state.compose_fields
	# Tabbing forever never reaches one.
	for _ in range(8):
		_press(state, store, K.TAB)
		assert state.compose_fields[state.compose_field] != "body"


def test_typing_in_compose_can_never_reach_the_body(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for _ in range(4):
		for char in "xyz":
			_press(state, store, ord(char))
		_press(state, store, K.TAB)
	assert state.compose.get("body", "") == ""


def test_the_editor_key_opens_the_editor_from_browse(env):
	"""A distinct action from the quick subject reply. One key meaning both is
	the hybrid that was rejected.

	Lowercase `r`, by Slawomir's trial ruling: the reply people actually write
	is a body in the editor, so the easier key serves it. (It was `e`, then
	`R`; both of those bindings are REMOVED for this act rather than kept as
	undiscoverable aliases.)"""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"the original\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)              # claim and open, still browsing
	seeds = []
	step(state, store, ord("r"), 100, 24, edit_fn=_editor("full body", record=seeds))
	# One action: the reply started AND the editor opened, seeded with the
	# quoted original.
	assert state.mode == MODE_REPLY
	assert state.draft == "S", "the subject was not inherited"
	assert state.reply_body == "full body"
	assert "> the original" in seeds[0]


def test_a_browse_letter_is_ordinary_text_inside_the_quick_reply_subject(env):
	"""The text modes are a separate key table, so every browse letter is just
	a letter while typing. Checked with `r`, which is the EDITOR reply key --
	stealing it in the subject editor would make a lowercase r untypeable.

	(It checked `e` when `e` was the full-reply key, then `R`; `r` is the
	editor key now, and inside the subject line it is a letter like any
	other.)"""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))    # the QUICK reply
	seeded = state.draft
	_press(state, store, ord("r"))                # ...and `r` is just text
	assert state.draft == seeded + "r"


def test_a_quick_reply_sends_the_subject_line_as_the_content(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Deploy plan", body=b"?\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	for char in " — shipping now":
		_press(state, store, ord(char))
	_send(state, store)
	response = store.scan("acme.reviewer")["pending"][0]
	full = store.get_message(response["id"])
	assert full["subject"] == "Deploy plan — shipping now"
	assert full["parts"][0]["body"] == "Deploy plan — shipping now".encode()
	# The claim is RESOLVED: a quick reply is still a disposition, so the
	# obligation does not silently persist.
	assert state.unresolved_count() == 0


def test_an_edited_body_wins_over_the_subject_line(env):
	"""When a body exists it IS the message; the subject line stays the
	subject."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Deploy plan", body=b"?\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	step(state, store, 5, 100, 24, edit_fn=_editor("the considered answer"))
	_send(state, store)
	response = store.get_message(
		store.scan("acme.reviewer")["pending"][0]["id"])
	assert response["subject"] == "Deploy plan"
	assert response["parts"][0]["body"] == b"the considered answer"


def test_the_body_state_is_shown_rather_than_typed(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	# The EMPTY row names the action, by Slawomir's trial ruling -- it has no
	# body state of its own to report. `(none)` was what it said between the
	# noise sweep and that ruling.
	from baton_tui.render import EMPTY_BODY
	empty = "\n".join(render(state, 100, 24))
	assert EMPTY_BODY in empty
	assert "none" not in empty
	step(state, store, 5, 100, 24, edit_fn=_editor("one\ntwo\nthree"))
	screen = "\n".join(render(state, 100, 24))
	# ...and once there IS a body, the row goes back to reporting its size and
	# says nothing about keys.
	assert "3 lines" in screen
	assert EMPTY_BODY not in screen, "the empty-state label outlived the body"
	assert "Ctrl-E" not in screen, "the key hint is back in the work area"
	assert "Ctrl+e" not in screen, "the removed footer is back"
	assert "Ctrl+e" in _legend(state), "the affordance itself was lost"
	# The body TEXT is not drawn as an editable field.
	assert "the considered answer" not in screen


# -- the distinction that must never blur ---------------------------------

def _counts(store):
	"""Claims, dispositions, and messages. A directed reply must move the
	first two; a notice reply must move only the third."""
	return {name: store.conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
	        for name in ("claims", "dispositions", "messages", "notices")}


@pytest.mark.parametrize("path", ["quick", "editor"])
def test_a_directed_reply_completes_the_claim_by_either_path(env, path):
	"""`r` and `e` are UI differences over one protocol act. Neither may
	become an ordinary send: that would leave the claim active and the human
	still owing a reply or close, while the screen said the reply went."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Deploy plan", body=b"the question\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                 # claim and open
	before = _counts(store)
	claim_id = state.opened["claim_id"]

	if path == "quick":
		_press(state, store, ord("R"))
		for char in " — done":
			_press(state, store, ord(char))
	else:
		step(state, store, ord("r"), 100, 24,
		     edit_fn=_editor("the considered answer"))
	_send(state, store)

	after = _counts(store)
	# A DISPOSITION was written, and the response message rides with it.
	assert after["dispositions"] == before["dispositions"] + 1
	assert after["messages"] == before["messages"] + 1
	assert after["claims"] == before["claims"], "a second claim appeared"
	# The claim is COMPLETED, not merely left alone.
	assert store.conn.execute(
		"SELECT state FROM claims WHERE claim_id=?", (claim_id,)
	).fetchone()[0] == "completed"
	assert state.unresolved_count() == 0


@pytest.mark.parametrize("path", ["quick", "editor"])
def test_a_notice_reply_is_a_new_message_and_never_a_disposition(env, path):
	"""A notice has NO claim, so there is nothing to complete. Producing a
	disposition here would mean inventing a claim the protocol never made."""
	store = env
	state = _opened_notice(store)
	before = _counts(store)

	if path == "quick":
		_press(state, store, ord("R"))
	else:
		step(state, store, ord("r"), 100, 24, edit_fn=_editor("a full answer"))
	_send(state, store)

	after = _counts(store)
	assert after["messages"] == before["messages"] + 1
	assert after["dispositions"] == before["dispositions"], "a disposition appeared"
	assert after["claims"] == before["claims"], "a claim appeared"
	assert after["notices"] == before["notices"]


def test_the_two_reply_paths_are_told_apart_by_what_is_open(env):
	"""One key, two protocol acts, chosen by the OPENED item -- never by the
	cursor, which is the bug this console was built after."""
	store = env
	store.send_notice("acme.reviewer", kind="announcement", subject="Broadcast",
	                  body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Directed",
	           body=b"d\n")
	state = _ready(store)

	# Open the DIRECTED message; `r` must be a disposition even though a
	# notice is also in the list.
	for index, row in enumerate(state.rows):
		if row["row_type"] == "message":
			state.cursor = index
			break
	state.preview(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	assert state.mode == MODE_REPLY, "a directed reply became a compose"
	_press(state, store, K.ESC)

	# Open the NOTICE; `r` must be a new directed message.
	state.refresh(store)
	for index, row in enumerate(state.rows):
		if row["row_type"] == "notice":
			state.cursor = index
			break
	state.preview(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	assert state.mode == MODE_COMPOSE, "a notice reply became a disposition"
	assert state.compose["to"] == "acme.reviewer"


# -- R2: four functional defects found in review ---------------------------

def test_a_notice_has_no_inline_body_field_either(env):
	"""R2.1. The no-inline-body rule is "anywhere", and notices were still
	exposing one. The existing pin only exercised directed compose, which is
	why this survived."""
	store = env
	state = _ready(store)
	_press(state, store, ord("N"))
	assert "body" not in state.compose_fields
	for _ in range(6):
		_press(state, store, K.TAB)
		assert state.compose_fields[state.compose_field] != "body"
	for char in "typed":
		_press(state, store, ord(char))
	assert state.compose.get("body", "") == ""


@pytest.mark.parametrize("key", [ord("n"), ord("N")])
def test_a_new_composition_never_quotes_whatever_was_open(env, key):
	"""R2.2. `begin_compose` leaves the previously opened item in `detail`, so
	the editor seed fell back to quoting it. Open something, start an
	UNRELATED new message, and another participant's words appeared in it."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Theirs",
	           body=b"words that belong to someone else\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                 # open the unrelated item
	_press(state, store, key)                        # start a NEW composition
	if key == ord("n"):
		_press(state, store, _pick(state, "acme.reviewer"))
	seeds = []
	step(state, store, 5, 100, 24, edit_fn=_editor("mine", record=seeds))
	assert seeds[0] == "", f"a new composition was seeded with: {seeds[0]!r}"
	assert "someone else" not in seeds[0]
	assert "wrote:" not in seeds[0]


def test_a_notice_reply_still_quotes_its_own_notice(env):
	"""The fix for R2.2 must not remove quoting where it belongs."""
	store = env
	state = _opened_notice(store, body=b"the announcement\n")
	_press(state, store, ord("R"))
	seeds = []
	step(state, store, 5, 100, 24, edit_fn=_editor("ack", record=seeds))
	assert "> the announcement" in seeds[0]


@pytest.mark.parametrize("key", [ord("R"), ord("r"), ord("c"), ord("m")])
def test_switching_to_sent_disarms_every_effectful_inbox_action(env, key):
	"""R2.3. `select_view` left `opened` armed, so after opening an inbox
	message and pressing `o`, an effectful key could reach the hidden claim
	while a sent row was on screen. That is the wrong-target bug wearing a
	different hat."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Inbox one",
	           body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                 # claim and open
	claim_id = state.opened["claim_id"]
	before = (store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0],
	          store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0])

	_press(state, store, ord("o"))                   # switch to SENT
	assert state.opened is None, "the inbox target survived the view switch"
	step(state, store, key, 100, 24, edit_fn=_editor("body"))

	after = (store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0],
	         store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
	assert after == before, f"{chr(key)!r} acted on the hidden inbox claim"
	# And the claim itself is untouched -- viewing must not mutate the
	# authority in either direction.
	assert store.conn.execute(
		"SELECT state FROM claims WHERE claim_id=?", (claim_id,)
	).fetchone()[0] == "active"


def test_switching_back_to_the_inbox_finds_the_claim_still_owed(env):
	"""Disarming the UI target must not lose the obligation."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Owed",
	           body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("o"), ord("i"))
	assert state.unresolved_count() == 1
	_press(state, store, K.ENTER_LF)                 # reopen it deliberately
	assert state.opened is not None


def test_G_reaches_the_last_row_of_the_active_view(env):
	"""R2.4. `G` used the INBOX row count in both views, so with differing
	counts it stopped short of the last sent row."""
	store = env
	for index in range(2):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"in{index}", body=b"x\n")
	for index in range(7):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"out{index}", body=b"y\n")
	state = _ready(store)
	assert len(state.rows) != len(state.sent_rows), "counts must differ to test this"

	_press(state, store, ord("G"))
	assert state.cursor == len(state.rows) - 1

	_press(state, store, ord("o"), ord("G"))
	assert state.sent_cursor == len(state.sent_rows) - 1
	_press(state, store, ord("g"), ord("g"))
	assert state.sent_cursor == 0


# -- R3: remaining correctness findings ------------------------------------

def test_the_selection_stripe_follows_the_active_view(env):
	"""R3.1. The style row came from inbox state while the pane drew sent
	rows, so in SENT the stripe landed on the wrong row -- or on none when the
	inbox was empty and the sent list was not."""
	from baton_tui.render import STYLE_SELECTED, render_styled
	store = env
	# Deliberately UNEQUAL counts between the two views.
	for index in range(6):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"out{index}", body=b"y\n")
	# One INBOUND message, which MESSAGES carries and SENT does not.
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="in0",
	           body=b"x\n")
	state = _ready(store)
	assert len(state.rows) != len(state.sent_rows), (
		f"{len(state.rows)} vs {len(state.sent_rows)}")

	_press(state, store, ord("o"))
	rows = render_styled(state, 100, 24)
	styled = [text for text, style in rows if STYLE_SELECTED in style]
	assert len(styled) == 1, "no row is highlighted in SENT"
	# It is the row the model says is selected.
	assert state.sent_rows[state.sent_cursor]["subject"] in styled[0]

	_press(state, store, ord("j"), ord("j"))
	rows = render_styled(state, 100, 24)
	styled = [text for text, style in rows if STYLE_SELECTED in style]
	assert state.sent_rows[state.sent_cursor]["subject"] in styled[0]


def test_sent_history_is_not_silently_truncated(env):
	"""R3.2. A default cap meant older durable subjects sat in the authority,
	unreachable, while the view called itself history -- and nothing on screen
	said so."""
	store = env
	for index in range(210):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"m{index:03d}", body=b"x\n")
	for index in range(5):
		store.send_notice("acme.implementer", kind="announcement",
		                  subject=f"n{index}", body=b"b\n")
	state = _ready(store)
	assert len(state.sent_rows) == 215, f"history stopped at {len(state.sent_rows)}"
	subjects = {row["subject"] for row in state.sent_rows}
	assert "m000" in subjects, "the OLDEST message is unreachable"
	assert "n0" in subjects
	# And it survives a restart, because it is authority-backed.
	fresh = InboxState("acme.implementer")
	fresh.refresh(store)
	assert len(fresh.sent_rows) == 215


def test_the_console_never_rewrites_a_subject_on_the_way_past(env):
	"""R3.3. The core rejects leading and trailing whitespace deliberately --
	silent sanitization misrepresents what the sender wrote. The console was
	stripping first, which hid the refusal AND sent something the human did
	not type."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "  padded  ":
		_press(state, store, ord(char))
	assert _send(state, store) is True
	# Refused by the AUTHORITY, surfaced, and the draft is intact.
	assert state.mode == MODE_COMPOSE
	assert "whitespace" in state.status.lower()
	assert state.compose["subject"] == "  padded  "
	assert store.conn.execute(
		"SELECT COUNT(*) FROM messages").fetchone()[0] == 0


def test_an_empty_body_from_the_editor_refuses_rather_than_sending_the_subject(env):
	"""R3.6. The quick path is valid, but choosing the FULL path and getting
	an empty body back must not silently send a different message."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Deploy",
	           body=b"q\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	step(state, store, ord("r"), 100, 24, edit_fn=_editor(""))   # editor emptied it
	before = store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0]
	_press(state, store, K.ENTER_LF, K.ENTER_LF)
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == before
	assert "empty body" in state.status
	assert state.draft == "Deploy", "the draft was lost"
	assert state.unresolved_count() == 1


def test_the_quick_path_still_sends_when_no_editor_was_opened(env):
	"""The R3.6 refusal must not leak into the quick path."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Deploy",
	           body=b"q\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	_send(state, store)
	assert state.unresolved_count() == 0


# -- R4: received history ---------------------------------------------------

def _answered(store, subject="Answered", body=b"the question\n", how="reply"):
	"""Send in, claim, and dispose of it -- the shape that used to vanish."""
	store.send("acme.reviewer", "acme.implementer", kind="q", subject=subject,
	           body=body)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	if how == "reply":
		_press(state, store, ord("R"))
		_send(state, store)
	else:
		_press(state, store, ord("c"))
	return state


def test_an_answered_message_stays_in_place_with_a_changed_badge(env):
	"""R4, exactly as Slawomir hit it: he received a message, replied, and the
	original disappeared.

	SUPERSEDED SHAPE: this first asserted the row LEFT the list and appeared
	in a separate `h` history view. Slawomir corrected that -- one MESSAGES
	list across the whole lifecycle, where answering changes the badge and
	the row keeps its place. Where a message sits is part of its story."""
	store = env
	state = _answered(store, subject="Answered one")
	# The INBOUND one: replying also creates an outbound response message,
	# which inherits the subject and now appears in the same list.
	row = next((r for r in state.rows
	            if r["subject"] == "Answered one"
	            and r.get("direction") == "in"), None)
	assert row is not None, "the answered message vanished from MESSAGES"
	assert row["state"] == "completed"
	from baton_tui.render import COMPLETED
	assert _sent_glyph(row) == COMPLETED
	assert "Answered one" in "\n".join(render(state, 120, 24))
	assert state.unresolved_count() == 0


def test_a_handled_message_opens_read_only_and_is_owner_checked(env):
	"""Opening a message you already answered must not claim, receipt or
	transition anything -- it is terminal, and the point of keeping the row is
	that you can look at what you answered. Owner-checked in the CORE on the
	recipient."""
	import baton_core as core
	store = env
	state = _answered(store, subject="Mine", body=b"what they asked\n")
	row = next(r for r in state.rows
	           if r["subject"] == "Mine" and r.get("direction") == "in")
	before = _writes(store)
	state.cursor = state.rows.index(row)
	state.preview(store)
	_press(state, store, K.ENTER_LF)
	assert _writes(store) == before, "reopening a handled message wrote"
	# It is NOT a dead end -- Slawomir's ruling -- so `r`/`R` are offered as a
	# FOLLOW-UP. What must stay gone is the DISPOSITION: no claim to complete,
	# so `_held_claim_id` is None and `c` and reply-as-disposition refuse.
	# (This asserted `opened is None`, when a handled row offered nothing.)
	assert state.opened is not None
	assert state.opened["claim_id"] is None, "a resolved row offered a disposition"
	assert state.follow_up_context["to"] == "acme.reviewer"
	assert "what they asked" in "\n".join(render(state, 100, 24))
	with pytest.raises(core.BatonError):
		store.open_received(row["id"], "acme.reviewer")      # the SENDER


# -- R5: a real caret in every editable field -------------------------------

def _replying(store, subject="Deploy plan"):
	store.send("acme.reviewer", "acme.implementer", kind="q", subject=subject,
	           body=b"q\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	return state


def test_a_seeded_subject_starts_with_the_caret_at_the_end(env):
	"""The human is continuing a subject, not inserting before it."""
	store = env
	state = _replying(store)
	assert state.draft == "Deploy plan"
	assert state.caret == len(state.draft)


def test_the_arrows_move_the_caret_and_typing_inserts_there(env):
	"""Reported by Slawomir: text could only be changed by backspacing from
	the end, because there was no caret to insert at."""
	store = env
	state = _replying(store)
	for _ in range(4):
		_press(state, store, K.KEY_LEFT)
	assert state.caret == len("Deploy ")
	for char in "new ":
		_press(state, store, ord(char))
	assert state.draft == "Deploy new plan"
	_press(state, store, K.KEY_RIGHT, K.KEY_RIGHT)
	assert state.caret == len("Deploy new pl")


def test_home_and_end_reach_both_ends(env):
	store = env
	state = _replying(store)
	_press(state, store, K.KEY_HOME)
	assert state.caret == 0
	for char in "RE ":
		_press(state, store, ord(char))
	assert state.draft == "RE Deploy plan"
	_press(state, store, K.KEY_END)
	assert state.caret == len(state.draft)


def test_backspace_and_delete_are_different_keys(env):
	"""At the start of a line one does nothing and the other still deletes."""
	store = env
	state = _replying(store)
	_press(state, store, K.KEY_HOME)
	_press(state, store, K.BACKSPACE_KEY)
	assert state.draft == "Deploy plan", "backspace at the start deleted something"
	_press(state, store, K.KEY_DC)
	assert state.draft == "eploy plan"
	_press(state, store, K.KEY_END, K.BACKSPACE_KEY)
	assert state.draft == "eploy pla"
	_press(state, store, K.KEY_DC)
	assert state.draft == "eploy pla", "delete past the end removed something"


def test_the_caret_never_leaves_the_buffer(env):
	store = env
	state = _replying(store)
	for _ in range(40):
		_press(state, store, K.KEY_LEFT)
	assert state.caret == 0
	for _ in range(40):
		_press(state, store, K.KEY_RIGHT)
	assert state.caret == len(state.draft)


def test_each_compose_field_keeps_its_own_caret(env):
	"""Switching away and back must not silently jump to the end of what you
	were writing."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "a subject":
		_press(state, store, ord(char))
	_press(state, store, K.KEY_HOME)
	assert state.caret == 0
	_press(state, store, K.TAB)                       # to attach
	for char in "src:E.md":
		_press(state, store, ord(char))
	assert state.caret == len("src:E.md")
	_press(state, store, K.TAB)                       # back round to subject
	while state.compose_fields[state.compose_field] != "subject":
		_press(state, store, K.TAB)
	assert state.caret == 0, "the subject caret was not preserved"
	for char in "RE ":
		_press(state, store, ord(char))
	assert state.compose["subject"] == "RE a subject"


def test_wide_characters_move_one_caret_step_each(env):
	"""The caret counts CHARACTERS; the renderer converts to display cells.
	Conflating the two puts the terminal cursor in the wrong column."""
	store = env
	state = _replying(store, subject="広い文字")
	assert state.caret == 4
	_press(state, store, K.KEY_LEFT, K.KEY_LEFT)
	assert state.caret == 2
	_press(state, store, ord("x"))
	assert state.draft == "広いx文字"


def test_the_terminal_cursor_follows_the_model_caret(env):
	"""Parking the cursor at the end of the line would show the human one
	position while their next keystroke landed at another."""
	from baton_tui.render import input_caret
	store = env
	state = _replying(store)
	_, at_end = input_caret(state, 100, 24)
	_press(state, store, K.KEY_HOME)
	_, at_home = input_caret(state, 100, 24)
	assert at_home < at_end, "the cursor did not move with the caret"
	_press(state, store, K.KEY_END)
	assert input_caret(state, 100, 24)[1] == at_end


def test_editing_keys_do_not_disturb_the_other_bindings(env):
	"""Esc still cancels, Enter still arms, `Ctrl+e` still opens the editor."""
	store = env
	state = _replying(store)
	_press(state, store, K.KEY_LEFT, K.KEY_LEFT)
	step(state, store, 5, 100, 24, edit_fn=_editor("full body"))
	assert state.reply_body == "full body"
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_CONFIRM_SEND
	_press(state, store, ord("n"))
	assert state.mode == MODE_REPLY
	_press(state, store, K.ESC)
	assert state.mode == MODE_BROWSE


# -- unified MESSAGES: both directions in one retained list ----------------

def test_a_sent_message_appears_in_messages_immediately(env):
	"""Slawomir's live trial: he composed, sent, and the message vanished
	from the primary list. Outbound lived only behind `o`."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "just sent this":
		_press(state, store, ord(char))
	_send(state, store)
	row = next((r for r in state.rows if r["subject"] == "just sent this"), None)
	assert row is not None, "the message vanished from MESSAGES after sending"
	assert row["direction"] == "out"
	assert "just sent this" in "\n".join(render(state, 120, 24))


def test_direction_is_visible_not_inferred(env):
	"""Delegated outbound work must never be mistaken for inbound work owed."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="owed to me",
	           body=b"x\n")
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="I delegated",
	           body=b"y\n")
	state = _ready(store)
	screen = render(state, 120, 24)
	# The party column is width-limited, so assert the DIRECTION MARKER rather
	# than the full address: `to …` is what distinguishes the two at a glance.
	outbound = [l for l in screen if "I delegated" in l]
	inbound = [l for l in screen if "owed to me" in l]
	assert outbound and "to acme.rev" in outbound[0], outbound
	assert inbound and "to acme.rev" not in inbound[0], inbound


def test_outbound_rows_carry_no_disposition(env):
	"""Its lifecycle is someone else's obligation, so no disposition key may
	reach it: `c` and reply-as-disposition would be actions that must fail.

	`r`/`R` DO work now -- they start a follow-up, which is a new message and
	never a second disposition. (This test asserted an outbound row offered
	nothing at all, from when it did; the property that survives is the one
	about dispositions, asserted here by counting authority writes.)"""
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="delegated",
	           body=b"y\n")
	state = _ready(store)
	assert state.unresolved_count() == 0, "an outbound row counted as owed"
	before = _writes(store)
	_press(state, store, K.ENTER_LF)                 # open it
	assert state.opened["claim_id"] is None, "an outbound row offered a claim"
	for key in (ord("c"), ord("m")):
		step(state, store, key, 120, 24, edit_fn=_editor("x"))
	assert _writes(store) == before, "an outbound row was dispositioned"
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0


def test_opening_an_outbound_row_shows_the_sent_copy_with_guidance(env):
	"""It shows your own sent bytes, and says what can still be done with the
	conversation rather than calling it read only.

	(This asserted the screen said "read only". Slawomir ruled that an
	answered or sent conversation is never presented as a dead end; the body
	is still immutable and no disposition key is offered, which is asserted in
	`test_outbound_rows_carry_no_disposition`.)"""
	from baton_tui.state import FOLLOW_UP_SENT
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="delegated",
	           parts=[{"content_type": "text/markdown; charset=utf-8",
	                   "body": b"what I asked them\n"}])
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	screen = "\n".join(render(state, 120, 24))
	assert "what I asked them" in screen
	assert FOLLOW_UP_SENT in screen
	assert "read only" not in screen.lower()


def test_the_header_count_is_inbound_obligations_only(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="owed",
	           body=b"x\n")
	for index in range(3):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"delegated{index}", body=b"y\n")
	state = _ready(store)
	# Select the INBOUND row explicitly; outbound sorts alongside it now.
	state.cursor = next(i for i, r in enumerate(state.rows)
	                    if r.get("direction") == "in")
	state.preview(store)
	_press(state, store, K.ENTER_LF)                 # claim the inbound one
	assert state.unresolved_count() == 1
	assert "1 awaiting" in render(state, 120, 24)[0]


# -- R7: part selection has to follow the shorter detail pane --------------

def _many_parts(store, count=8):
	return store.send("acme.reviewer", "acme.implementer", kind="q",
	                  subject="Many parts", parts=[
		{"content_type": "text/plain; charset=utf-8",
		 "body": f"leaf {index}\n".encode()} for index in range(count)])


def test_selecting_a_later_part_brings_its_header_into_view(env):
	"""Stacked, the detail pane is 60% of the body instead of all of it, so
	the later parts of a multipart message start below the fold. `[`/`]` that
	moved a mark nobody can see would be a cursor that does not exist -- the
	same fault as a picker offering a letter it never drew."""
	from baton_tui.render import STYLE_PART_HEADER, render_styled
	store = env
	_many_parts(store)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                  # claim and open
	seen = []
	for index in range(8):
		if index:
			_press(state, store, ord("]"))
		assert state.part_cursor == index
		marked = [text for text, style in render_styled(state, 100, 24)
		          if STYLE_PART_HEADER in style]
		assert marked, f"part {index} is selected but its header is off screen"
		seen.append(marked[0])
	assert len(set(seen)) == 8, "the mark did not move with the selection"


def test_moving_back_up_the_parts_follows_too(env):
	"""Both directions, or `[` walks off the top of the pane instead."""
	from baton_tui.render import STYLE_PART_HEADER, render_styled
	store = env
	_many_parts(store)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	for _ in range(7):
		_press(state, store, ord("]"))
	bottom = state.detail_offset
	assert bottom > 0, "the pane never scrolled; the fixture is too small"
	for _ in range(7):
		_press(state, store, ord("["))
		assert any(STYLE_PART_HEADER in style
		           for _, style in render_styled(state, 100, 24))
	assert state.part_cursor == 0
	# Back up the document, not merely marking a header nobody can see.
	assert state.detail_offset < bottom


def test_reading_scroll_is_not_taken_over_by_part_following(env):
	"""Following happens on the keystroke that MOVES the part, never on a
	redraw -- otherwise every repaint would yank a reader's `J`/`K` position
	back to the marked header."""
	from baton_tui.driver import apply_layout
	store = env
	_many_parts(store)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	_press(state, store, K.TAB)                       # focus the detail pane
	for _ in range(6):
		_press(state, store, ord("j"))
	scrolled = state.detail_offset
	assert scrolled > 0
	apply_layout(state, 100, 24)
	assert state.detail_offset == scrolled
	_press(state, store, K.CTRL_R)                    # a refresh is not a move
	assert state.detail_offset == scrolled


# -- RULED: r editor reply, R quick subject reply, Ctrl+r refresh ----------

def test_the_editor_key_does_not_go_through_the_quick_reply_first(env):
	"""Slawomir's ruling, and the property that makes it one action rather
	than two: the editor key from BROWSE starts the reply and opens the
	editor. It must not require, or leave behind, a trip through the
	quick-reply subject.

	(That key was `R` when this was written and is `r` now — the trial
	reversed the pair. The property is the same one.)"""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"the original\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                   # claim and open
	assert state.mode == MODE_BROWSE, "the fixture is not in browse mode"
	seeds = []
	step(state, store, ord("r"), 100, 24,
	     edit_fn=_editor("a full answer", record=seeds))
	assert seeds, "the editor never opened"
	assert state.reply_body == "a full answer"
	assert state.draft == "S", "the subject was not inherited"


def test_the_quick_key_is_still_the_subject_only_path(env):
	"""The pair only works if the small one stays small: the quick key edits
	the inherited subject and opens no editor. (`r` when written, `R` now.)"""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Subject line",
	           body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	seeds = []
	step(state, store, ord("R"), 100, 24,
	     edit_fn=_editor("must not be used", record=seeds))
	assert not seeds, "the quick path opened the editor"
	assert state.mode == MODE_REPLY
	assert state.draft == "Subject line"
	assert state.reply_body == ""


def test_ctrl_r_refreshes_without_acting_on_a_message(env):
	"""Refresh is observation. Moving it onto a control key must not have made
	it touch the message under the cursor."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Untouched",
	           body=b"x\n")
	state = _ready(store)
	before = _writes(store)
	_press(state, store, K.CTRL_R)
	assert _writes(store) == before, "refresh wrote to the authority"
	assert state.mode == MODE_BROWSE
	assert state.opened is None


def test_the_browse_e_shortcut_is_gone(env):
	"""Removed rather than kept as an alias: a second spelling nobody is told
	about is a key only its author can press."""
	from baton_tui.state import MODE_BROWSE as BROWSE
	assert K.map_key(ord("e"), BROWSE) == (K.IGNORE, None)


def test_the_key_legend_advertises_the_ruled_bindings(env):
	"""A binding nobody can see is a binding nobody has.

	SUPERSEDED IN LOCATION, twice over. It was a fixed footer string; then it
	became the contextual footer; now there is no ordinary footer at all and
	`?` help is where the console says what it can do. The property survives
	in two halves: the affordance query still turns `reply` on only once
	there is something to reply to, and HELP documents every ruled binding."""
	from baton_tui.keys import HELP_SECTIONS
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert state.affordances()["reply"] is False, "reply offered with nothing open"
	_press(state, store, K.ENTER_LF)                  # claim and open
	assert state.affordances()["reply"] is True

	documented = {key for _title, rows in HELP_SECTIONS for key, *_ in rows}
	for binding in ("r", "R", "Ctrl+r", "n", "N", "c", "[ / ]", "Tab"):
		assert binding in documented, f"help does not document {binding!r}"


# -- RULED: Ctrl+u kills subject text left of the caret --------------------

@pytest.mark.parametrize("caret,expected", [
	(0, "a subject line"),        # nothing to the left: nothing is lost
	(2, "subject line"),          # middle: only the left of the caret goes
	(14, ""),                     # at the end: the whole line clears
])
def test_ctrl_u_kills_to_the_start_of_the_subject(env, caret, expected):
	"""Slawomir's ruling, at the three caret positions that behave
	differently. Everything AT and after the caret survives."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	state.draft, state.draft_caret = "a subject line", caret
	_press(state, store, K.CTRL_U)
	assert state.draft == expected
	assert state.caret == 0, "the caret must land where the text now starts"


@pytest.mark.parametrize("mode", ["compose", "notice"])
def test_ctrl_u_works_in_every_subject_editor(env, mode):
	""""Every subject editor" means every one: a rule that holds in one flow
	and not another is how the no-inline-body model came apart in R2."""
	store = env
	state = _drafted(store, mode)
	field = state.compose_fields[state.compose_field]
	state.compose[field] = "throw this away"
	state.compose_carets[field] = len("throw this away")
	_press(state, store, K.CTRL_U)
	assert state.compose[field] == ""


def test_browse_ctrl_u_still_pages_the_list(env):
	"""The same chord means two things because the tables are separate. Taking
	the browse meaning would cost a navigation key to gain an editing one."""
	store = env
	for index in range(40):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"m{index:02d}", body=b"x\n")
	state = _ready(store)
	_press(state, store, ord("G"))                    # to the last row
	bottom = state.cursor
	_press(state, store, K.CTRL_U)
	assert state.cursor < bottom, "Ctrl+u stopped paging in browse mode"
	assert state.mode == MODE_BROWSE


# -- RULED: `?` opens a modal shortcut list --------------------------------

def _helped(store):
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Context",
	           body=("line\n" * 80).encode())
	store.send("hq.lead", "acme.implementer", kind="q", subject="Second", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                 # claim and open something
	for _ in range(4):
		_press(state, store, ord("J"))               # and scroll it
	return state


@pytest.mark.parametrize("key", [ord("?"), ord("q"), K.ESC])
def test_help_opens_and_closes_restoring_everything(env, key):
	"""It must put the human back exactly where they were reading. `q` closes
	the help and does NOT quit -- it is the key people press to dismiss a
	full-screen thing."""
	from baton_tui.state import MODE_HELP
	store = env
	state = _helped(store)
	before = (state.cursor, state.inbox_top, state.detail_offset,
	          state.part_cursor, state.status, state.status_severity,
	          state.draft, dict(state.compose),
	          None if state.opened is None else dict(state.opened))
	assert _press(state, store, ord("?")) is True
	assert state.mode == MODE_HELP
	assert _press(state, store, key) is True, "the console exited from help"
	assert state.mode == MODE_BROWSE
	assert (state.cursor, state.inbox_top, state.detail_offset,
	        state.part_cursor, state.status, state.status_severity,
	        state.draft, dict(state.compose),
	        None if state.opened is None else dict(state.opened)) == before


def test_help_writes_nothing_to_the_authority(env):
	"""Observation in the strongest sense: no claim, no receipt, no
	transition, no disposition, and no refresh of authority state."""
	store = env
	state = _helped(store)
	before = _writes(store)
	_press(state, store, ord("?"))
	for _ in range(6):
		_press(state, store, ord("j"))
	_press(state, store, ord("?"))
	assert _writes(store) == before


def test_question_mark_is_literal_text_while_typing(env):
	"""A key that opened a full-screen view mid-sentence would be the browse
	table leaking into the text one."""
	from baton_tui.state import MODE_HELP
	store = env
	state = _drafted(store, "reply")
	state.draft_caret = len(state.draft)          # type at the end of the line
	seeded = state.draft
	_press(state, store, ord("?"))
	assert state.mode != MODE_HELP
	assert state.draft == seeded + "?"


def test_the_help_lists_every_active_browse_binding(env):
	"""Built from the table beside the key map so the two cannot drift. Help
	that is wrong is worse than none, because it is believed."""
	from baton_tui import keys as K2
	documented = {event for _, entries in K2.HELP_SECTIONS
	              for _, _, events in entries for event in events}
	live = set(K2._BROWSE.values()) - {K2.IGNORE}
	missing = live - documented
	assert not missing, f"browse bindings the help does not mention: {missing}"


@pytest.mark.parametrize("columns,lines", [(40, 8), (40, 24), (80, 12), (100, 24)])
def test_every_shortcut_is_reachable_on_a_small_terminal(env, columns, lines):
	"""It PAGES rather than clipping. A shortcut the terminal was too small to
	draw is a shortcut that does not exist -- the fault the recipient picker
	taught, in a different view."""
	from baton_tui.render import help_line_count, help_lines, render
	from baton_tui.driver import apply_layout, step
	store = env
	state = _ready(store)
	# At the SIZE under test, not at the helper's default: the scroll clamp is
	# computed against the pane height, so driving it at one size and drawing
	# at another would prove nothing about either.
	apply_layout(state, columns, lines)
	step(state, store, ord("?"), columns, lines)
	total = help_line_count(state, columns, lines)
	expected = [line.rstrip() for line in help_lines(state, columns) if line.strip()]
	seen = ""
	for _ in range(total + 2):
		seen += "\n".join(render(state, columns, lines)) + "\n"
		step(state, store, ord("j"), columns, lines)
	for line in expected:
		assert line in seen, f"{columns}x{lines}: never drawn: {line!r}"


def test_the_status_bar_is_not_replaced_by_help(env):
	"""Help is a modal VIEW, not status-bar prose. The bar is where async
	events land and it must keep saying what it was saying."""
	from baton_tui.render import render
	store = env
	state = _helped(store)
	said = state.status
	_press(state, store, ord("?"))
	screen = render(state, 100, 24)
	assert state.status == said
	assert said[:20] in screen[-1]


# -- BLOCKING trial: an outbound row must not preview as a delivery ---------

def _full_reply(state, store, body="a full answer"):
	"""Claim, open, full-editor reply, review, send -- the trial's path."""
	_press(state, store, K.ENTER_LF)
	step(state, store, ord("r"), 100, 24, edit_fn=_editor(body))
	_press(state, store, K.ENTER_LF, ord("y"))


def test_selecting_an_outbound_row_never_errors(env):
	"""Live-trial failure, reproduced: `preview_message` is owner-checked on
	the RECIPIENT -- correctly, it is the delivery preview -- so routing an
	outbound row through it made merely SELECTING one report "addressed to
	them, not you" and blank the pane.

	The owner check is right and is NOT weakened; the console stopped asking
	it the wrong question."""
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Delegated",
	           body=b"x\n")
	state = _ready(store)
	state.cursor = next(index for index, row in enumerate(state.rows)
	                    if row.get("direction") == "out")
	state.preview(store)
	assert state.status_severity != "error", state.status
	assert state.detail is not None, "the pane went blank on an outbound row"
	assert "sent_row" in state.detail, "an outbound row previewed as a delivery"


def test_a_full_reply_publishes_once_and_leaves_no_error(env):
	"""The whole reported sequence, end to end: publication succeeds exactly
	once and the console does not then report an error about its own child."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Original",
	           body=b"?\n")
	state = _ready(store)
	before = store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
	_full_reply(state, store)
	after = store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
	assert after == before + 1, "the reply did not publish exactly once"
	assert state.status_severity != "error", state.status
	assert state.mode == MODE_BROWSE
	# The claim really was resolved: exactly one disposition, no second claim.
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 1
	assert state.unresolved_count() == 0


def test_the_new_child_is_selectable_and_renders_through_the_outbound_path(env):
	"""After the send, moving onto the child must show the sent content
	rather than an error -- and through `open_sent`, which is owner-checked on
	the SENDER."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Original",
	           body=b"?\n")
	state = _ready(store)
	_full_reply(state, store, "the body I typed")
	child = next(index for index, row in enumerate(state.rows)
	             if row.get("direction") == "out")
	state.cursor = child
	state.preview(store)
	assert state.status_severity != "error", state.status
	_press(state, store, K.ENTER_LF)               # open it
	assert state.status_severity != "error", state.status
	assert "sent" in (state.detail or {}), "the child did not open as sent"
	screen = "\n".join(render(state, 100, 40))
	assert "the body I typed" in screen, "the sent content is not visible"
	# Opening your own copy consumes nothing: no second claim, no disposition.
	assert store.conn.execute(
		"SELECT COUNT(*) FROM claims").fetchone()[0] == 1
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 1


def test_the_quick_reply_path_has_the_same_guarantee(env):
	"""Both reply paths reach the same place, so both are pinned: fixing one
	and assuming the other is how the notice body stayed broken for a release."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Original",
	           body=b"?\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	state.draft = "a quick answer"
	_press(state, store, K.ENTER_LF, ord("y"))
	assert state.status_severity != "error", state.status
	child = next(index for index, row in enumerate(state.rows)
	             if row.get("direction") == "out")
	state.cursor = child
	state.preview(store)
	assert state.status_severity != "error", state.status
	assert "sent_row" in (state.detail or {})


def test_the_selection_after_a_send_is_a_row_that_can_be_shown(env):
	"""Whatever the console selects after publishing, it must be able to draw
	it. The trial's screen was an error where a message should have been."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Original",
	           body=b"?\n")
	state = _ready(store)
	_full_reply(state, store)
	assert state.selected is not None
	assert state.detail is not None
	assert state.status_severity != "error", state.status
	screen = render(state, 100, 24)
	assert not any("nothing shown for this row" in line for line in screen)


# -- review: the editor follow-up, and the guidance must name a live key ---

def test_the_quick_reply_guidance_names_the_key_that_exists(env):
	"""It said "e for the editor" after `e` was unbound and `R` took the
	action. A stale comment is untidy; stale ON-SCREEN instructions send
	someone pressing a key that does nothing.

	SUPERSEDED IN LOCATION, not in force. Status no longer lists the reply
	keys at all -- the footer owns them, by Slawomir's one-owner ruling -- so
	the property moved to where the instruction now lives. Removing the
	duplicate must not lose the check that the surviving copy is accurate."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("R"))
	# Status says WHAT started and stops there.
	assert "quick reply" in state.status, state.status
	assert "Esc" not in state.status and "Enter" not in state.status, \
		"status is restating the footer again"
	# The footer is the owner, and it names the key that works HERE. Inside a
	# quick reply that is `Ctrl+e`, not `r` -- `r` is a browse key, and typing
	# it in this mode inserts the letter. The old status line said "R for the
	# editor" while the reply was open, which was inaccurate even then.
	legend = _legend(state, 100, 24)
	assert "Ctrl+e" in legend, legend
	assert " e " not in legend and "e for the editor" not in legend
	assert K.map_key(ord("e"), MODE_BROWSE) == (K.IGNORE, None)
	assert K.map_key(ord("r"), MODE_BROWSE) == (K.EDIT_BODY, None)
	# And from browse, where the reply keys ARE actions, the footer says so.
	_press(state, store, K.ESC)
	assert "R" in _legend(state, 100, 24)


def _handled_inbound(store):
	"""A received message, claimed and answered: nothing owed, still open."""
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Answered thing", body=b"?\n")
	claim = store.claim("acme.implementer", message_id=mid)
	store.reply(claim["claim_id"], participant="acme.implementer",
	            kind="response", subject="Answered thing", body=b"a\n")
	state = _ready(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == mid)
	state.preview(store)
	return state, mid


def _handled_outbound(store):
	mid = store.send("acme.implementer", "acme.reviewer", kind="q",
	                 subject="Delegated thing", body=b"x\n")
	state = _ready(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == mid)
	state.preview(store)
	return state, mid


@pytest.mark.parametrize("fixture,other", [
	(_handled_inbound, "acme.reviewer"),
	(_handled_outbound, "acme.reviewer"),
])
def test_r_publishes_a_full_body_follow_up_from_a_handled_row(env, fixture, other):
	"""The gap review found: the quick path was pinned and the EDITOR path was
	not, on either kind of handled row. One keystroke opens the editor, the
	edited body is imported, and the confirmation publishes exactly one
	`follow_up` linked to the row — and no disposition."""
	from baton_tui.state import KIND_FOLLOW_UP
	store = env
	state, mid = fixture(store)
	_press(state, store, K.ENTER_LF)                  # open the handled row
	assert state.mode == MODE_BROWSE
	messages = store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
	dispositions = store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0]
	seeds = []
	step(state, store, ord("r"), 100, 24,
	     edit_fn=_editor("the long version", record=seeds))
	assert seeds, "R did not open the editor"
	assert state.compose.get("body") == "the long version", "the body was not imported"
	_press(state, store, K.ENTER_LF, ord("y"))        # review, then send
	assert state.status_severity != "error", state.status
	assert store.conn.execute(
		"SELECT COUNT(*) FROM messages").fetchone()[0] == messages + 1
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == dispositions
	child = store.conn.execute(
		"SELECT id, kind, responds_to, to_participant FROM messages "
		"WHERE responds_to = ? AND kind = ?", (mid, KIND_FOLLOW_UP)).fetchall()
	assert len(child) == 1, "expected exactly one linked follow-up"
	assert child[0]["to_participant"] == other
	body = store.get_message(child[0]["id"])["parts"][0]["body"]
	assert b"the long version" in body, "the editor's body did not reach the wire"


@pytest.mark.parametrize("fixture,other", [
	(_handled_inbound, "acme.reviewer"),
	(_handled_outbound, "acme.reviewer"),
])
def test_a_cancelled_editor_publishes_nothing_and_keeps_the_follow_up(env, fixture, other):
	"""The other half of the `r` follow-up path: the editor comes back with
	nothing.

	**SUPERSEDED IN ONE RESPECT, and it was mine.** This asserted the
	follow-up context SURVIVED a cancelled fresh editor reply so the human
	could retry through `Ctrl+e`. Review then ruled that a cancelled fresh
	editor reply must restore the original opened message instead, and that is
	the better rule: `r` from browse is ONE action, so if the editor gives
	nothing back the action did nothing, and there is no human-authored draft
	to lose -- the "draft" was only the subject the console seeded. Retry is
	pressing `r` again.

	What survives unchanged, and is what the test was really for: nothing is
	published, nothing is written to any table, and the failure is VISIBLE
	rather than a keystroke that silently did nothing."""
	from baton_tui.state import KIND_FOLLOW_UP
	store = env
	state, mid = fixture(store)
	_press(state, store, K.ENTER_LF)                  # open the handled row
	before = _writes(store)
	messages = store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

	def refuses(seed):
		return None, "the editor exited without saving"

	step(state, store, ord("r"), 100, 24, edit_fn=refuses)
	# Nothing reached the authority: no message, claim, disposition, receipt
	# or transition.
	assert store.conn.execute(
		"SELECT COUNT(*) FROM messages").fetchone()[0] == messages
	assert _writes(store) == before
	# The failure is VISIBLE rather than a keystroke that did nothing, and the
	# editor's own explanation is what is shown -- not a summary over the top.
	assert state.status_severity in ("warning", "error"), state.status
	assert "editor" in state.status.lower()
	# The human is back where they started: reading the message, not parked in
	# a quick-subject editor they never asked for.
	assert state.mode == MODE_BROWSE, "left in an editor the human did not ask for"
	assert state.follow_up_to is None, "a half-started follow-up survived"
	assert not state.compose, "a half-started composition survived"
	assert state.opened is not None, "the original was closed"
	assert state.opened["id"] == mid, "a different message is open"
	# Retry is pressing `r` again, and it publishes exactly ONE linked
	# follow-up.
	#
	# Counted as `kind=follow_up AND responds_to=mid`, not as `responds_to`
	# alone: on the handled-inbound fixture the original REPLY is itself
	# linked to `mid`, so a bare `>= 1` was already true before the retry and
	# would have passed if the retry published nothing at all. Review caught
	# it; the assertion now brackets the retry.
	def follow_ups():
		return store.conn.execute(
			"SELECT COUNT(*) FROM messages WHERE responds_to = ? AND kind = ?",
			(mid, KIND_FOLLOW_UP)).fetchone()[0]

	assert follow_ups() == 0, "the cancelled edit published something"
	step(state, store, ord("r"), 100, 24, edit_fn=_editor("second attempt"))
	_press(state, store, K.ENTER_LF, ord("y"))
	assert follow_ups() == 1, "the retry did not publish exactly one follow-up"
	row = store.conn.execute(
		"SELECT id, to_participant FROM messages "
		"WHERE responds_to = ? AND kind = ?", (mid, KIND_FOLLOW_UP)).fetchone()
	assert row["to_participant"] == other
	body = store.get_message(row["id"])["parts"][0]["body"]
	assert b"second attempt" in body, "the retried body did not reach the wire"


# -- RULED: Tab pane focus, and Vim navigation routed through it -----------

def _long_message(store, subject="Long"):
	store.send("acme.reviewer", "acme.implementer", kind="q", subject=subject,
	           body="\n".join(f"line {i:03d}" for i in range(200)).encode())


def test_tab_toggles_exactly_two_focus_stops(env):
	"""Two panes, two stops. Shift-Tab is the same toggle rather than a third
	place to be."""
	from baton_tui.state import FOCUS_DETAIL, FOCUS_LIST
	store = env
	_long_message(store)
	state = _ready(store)
	assert state.focus == FOCUS_LIST, "focus does not start on the list"
	_press(state, store, K.TAB)
	assert state.focus == FOCUS_DETAIL
	_press(state, store, K.TAB)
	assert state.focus == FOCUS_LIST
	_press(state, store, K.SHIFT_TAB)
	assert state.focus == FOCUS_DETAIL
	_press(state, store, K.SHIFT_TAB)
	assert state.focus == FOCUS_LIST


def test_focusing_writes_nothing_and_disturbs_nothing(env):
	"""Pure UI state. It must not claim, receipt, dispose, publish or
	transition, and it must not move anything the human set."""
	store = env
	_long_message(store)
	store.send("hq.lead", "acme.implementer", kind="q", subject="Other", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                  # claim and open
	_press(state, store, K.TAB)
	for _ in range(3):
		_press(state, store, ord("j"))                # scroll the detail
	before = (_writes(store), state.cursor, state.inbox_top, state.detail_offset,
	          state.part_cursor, state.status, state.status_severity,
	          state.draft, dict(state.opened))
	for _ in range(6):
		_press(state, store, K.TAB)                   # back and forth
	assert (_writes(store), state.cursor, state.inbox_top, state.detail_offset,
	        state.part_cursor, state.status, state.status_severity,
	        state.draft, dict(state.opened)) == before


def test_list_focus_moves_the_row_and_never_the_detail(env):
	"""The other direction of the separation."""
	from baton_tui.state import FOCUS_LIST
	store = env
	_long_message(store)
	for index in range(5):
		store.send("hq.lead", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=b"x\n")
	state = _ready(store)
	# The LONG one: newest-first puts the short rows above it, and scrolling a
	# one-line body proves nothing.
	state.cursor = next(i for i, r in enumerate(state.rows) if r["subject"] == "Long")
	state.preview(store)
	_press(state, store, K.ENTER_LF)
	_press(state, store, K.TAB)
	for _ in range(4):
		_press(state, store, ord("j"))
	scrolled = state.detail_offset
	assert scrolled > 0
	_press(state, store, K.TAB)
	assert state.focus == FOCUS_LIST
	start = state.cursor
	# Whichever direction has somewhere to go. Same-second sends tie and order
	# by id, so the long message can land on either end of the list -- pressing
	# `j` unconditionally made this test pass or fail on a hash. A flaky test
	# is worse than no test: it trains people to rerun until green.
	_press(state, store, ord("k") if start == len(state.rows) - 1 else ord("j"))
	assert state.cursor != start, "list focus did not move the row"
	# It did not SCROLL the detail. The offset resets to 0 because the pane
	# now shows a different message, which is the older rule that a scroll
	# position belongs to the thing being read -- see
	# `test_scrolling_resets_when_the_selection_changes`. Reported to review
	# as a conflict with the ruling's literal wording rather than silently
	# resolved.
	assert state.detail_offset == 0


@pytest.mark.parametrize("key", [ord("j"), K.KEY_DOWN, K.CTRL_D, K.KEY_NPAGE])
def test_every_forward_navigation_key_follows_focus(env, key):
	"""Arrows and page keys route the same way as j/k -- one model, not a
	special case per key."""
	store = env
	_long_message(store)
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	_press(state, store, K.TAB)
	cursor = state.cursor
	_press(state, store, key)
	assert state.detail_offset > 0, "the key did not scroll the focused detail"
	assert state.cursor == cursor, "the key moved the list while detail was focused"


def test_gg_and_G_act_on_the_focused_pane(env):
	"""Confirmed by Slawomir: same keys, per-focus meaning."""
	store = env
	_long_message(store)
	for index in range(6):
		store.send("hq.lead", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=b"x\n")
	state = _ready(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["subject"] == "Long")
	state.preview(store)
	_press(state, store, K.ENTER_LF)
	_press(state, store, K.TAB)                       # DETAIL focus
	row = state.cursor
	_press(state, store, ord("G"))
	assert state.detail_offset > 0, "G did not reach the bottom of the detail"
	assert state.cursor == row, "G moved the list while detail was focused"
	_press(state, store, ord("g"), ord("g"))
	assert state.detail_offset == 0, "gg did not reach the top of the detail"
	assert state.cursor == row
	_press(state, store, K.TAB)                       # LIST focus
	_press(state, store, ord("G"))
	assert state.cursor == len(state.rows) - 1


def test_focus_survives_refresh_and_resize(env):
	"""Polling, redraw, resize and `Ctrl+r` all preserve it."""
	from baton_tui.driver import apply_layout
	from baton_tui.state import FOCUS_DETAIL
	store = env
	_long_message(store)
	state = _ready(store)
	_press(state, store, K.TAB)
	state.refresh(store)
	assert state.focus == FOCUS_DETAIL
	apply_layout(state, 60, 16)
	assert state.focus == FOCUS_DETAIL
	_press(state, store, K.CTRL_R)
	assert state.focus == FOCUS_DETAIL


def test_switching_lists_returns_focus_to_the_list(env):
	"""`i`/`o` say which list is being navigated, so the keys should point at
	it."""
	from baton_tui.state import FOCUS_LIST, VIEW_SENT
	store = env
	_long_message(store)
	state = _ready(store)
	_press(state, store, K.TAB)
	_press(state, store, ord("o"))
	assert state.view == VIEW_SENT
	assert state.focus == FOCUS_LIST


def test_tab_keeps_its_meaning_in_every_other_mode(env):
	"""Compose next field, picker next page. Taking Tab there would cost a
	working key to gain a new one."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))                    # the recipient picker
	pages = state.picker_page
	_press(state, store, K.TAB)
	assert state.picker_page != pages or state.picker_pages == 1
	_press(state, store, _pick(state, "acme.reviewer"))
	field = state.compose_field
	_press(state, store, K.TAB)
	assert state.compose_field != field, "Tab stopped moving the compose field"


def test_uppercase_J_and_K_are_unbound(env):
	"""Removed, not aliased. Two competing navigation models is one more than
	a console should have."""
	assert K.map_key(ord("J"), MODE_BROWSE) == (K.IGNORE, None)
	assert K.map_key(ord("K"), MODE_BROWSE) == (K.IGNORE, None)
	help_text = "\n".join(f"{c} {d}" for _, entries in K.HELP_SECTIONS
	                      for c, d, _ in entries)
	assert "J / K" not in help_text


def test_both_pane_labels_are_always_drawn_with_exactly_one_marker(env):
	"""An indication that exists only as bold or colour is no indication on
	half the terminals this runs on."""
	store = env
	_long_message(store)
	state = _ready(store)
	for columns, lines in ((40, 8), (80, 24), (133, 40)):
		for _ in range(2):
			screen = render(state, columns, lines)
			body = "\n".join(screen)
			assert "MESSAGES" in body and "DETAIL" in body
			marked = [line for line in screen
			          if "> MESSAGES" in line or "> DETAIL" in line
			          or "> SENT" in line]
			assert len(marked) == 1, f"{columns}x{lines}: {len(marked)} marked"
			_press(state, store, K.TAB)


def test_the_focus_marker_does_not_move_anything(env):
	"""`> ` and two spaces are the same two cells, so toggling focus cannot
	shift a column or change the screen height."""
	from baton_tui.safe_text import display_width
	store = env
	_long_message(store)
	state = _ready(store)
	for columns, lines in ((40, 8), (100, 24)):
		first = render(state, columns, lines)
		_press(state, store, K.TAB)
		second = render(state, columns, lines)
		assert len(first) == len(second) == lines
		assert [display_width(l) for l in first] == [display_width(l) for l in second]
		_press(state, store, K.TAB)


# -- RULED: the footer advertises only what presently works ----------------

# What the console WOULD offer, in the wording the footer used before it was
# removed. SUPERSEDED AS PRESENTATION, kept as vocabulary: Slawomir ruled the
# ordinary shortcut catalogue off the screen entirely, but the query behind it
# is the single authority dispatch consults, and every property these pins
# protect -- close only while a claim is held, no part navigation for a
# one-part message, an opened notice offering nothing to close -- is a
# property of THAT, not of a row of text.
#
# So this reads the affordance query directly. The labels exist only so the
# assertions below still read as English; the product renders none of them,
# which `test_no_shortcut_catalogue_reaches_the_screen` is what pins.
_LABELS = (
	("open", "Enter open"),
	("reply", "r reply  R editor"),
	("close", "c close"),
	("part_nav", "[/] part"),
	("hscroll", "h/l sideways"),
	("read_part", "v read"),
	("materialize", "m save"),
)
_ALWAYS = ("n new", "N notice", "i/o view", "Ctrl+r refresh", "? help", "q quit")


def _legend(state, columns=200, lines=24):
	"""The affordances in force right now, rendered for reading."""
	from baton_tui.state import FOCUS_DETAIL
	modal = K.MODE_LEGENDS.get(state.mode)
	if modal is not None:
		enabled = state.modal_affordances()
		return "  ".join(label for label, _keys, condition in modal
		                 if condition is None or enabled.get(condition))
	available = state.affordances()
	moves = ("j/k scroll  gg/G top/bottom" if state.focus == FOCUS_DETAIL
	         else "j/k move  gg/G first/last")
	parts = [moves, "Tab focus"]
	parts.extend(label for name, label in _LABELS if available.get(name))
	parts.extend(_ALWAYS)
	return "  ".join(parts)


def test_an_opened_notice_does_not_advertise_close(env):
	"""The reported defect. A notice has no claim for `close` to consume, and
	the footer said `c close` anyway -- it had, since the footer was written,
	because the footer was a fixed string."""
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast", body=b"n\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                  # mark seen and open
	legend = _legend(state)
	assert "c close" not in legend, legend
	# ...and what IS offered is offered because it works: `r` replies to the
	# notice's author.
	assert "r reply" in legend


def test_close_appears_exactly_while_a_claim_is_held(env):
	"""Before, during, after — the whole lifecycle of the one action the
	defect was about."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Owed", body=b"x\n")
	state = _ready(store)
	assert "c close" not in _legend(state), "close advertised before opening"
	_press(state, store, K.ENTER_LF)                  # claim
	assert "c close" in _legend(state), "close not advertised while owed"
	_press(state, store, ord("c"))                    # resolve it
	assert state.unresolved_count() == 0
	assert "c close" not in _legend(state), "close still advertised after closing"


@pytest.mark.parametrize("build,expect_close", [
	(_handled_inbound, False),
	(_handled_outbound, False),
])
def test_handled_and_outbound_rows_never_advertise_close(env, build, expect_close):
	store = env
	state, _ = build(store)
	_press(state, store, K.ENTER_LF)
	legend = _legend(state)
	assert ("c close" in legend) is expect_close, legend
	# They CAN be followed up, and the legend says so.
	assert "r reply" in legend


def test_the_sent_view_advertises_no_claim_fiction(env):
	"""Read-only in the strongest sense, including in what it offers."""
	from baton_tui.state import VIEW_SENT
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Out", body=b"x\n")
	state = _ready(store)
	_press(state, store, ord("o"))
	assert state.view == VIEW_SENT
	legend = _legend(state)
	assert "c close" not in legend
	assert "Ctrl+r refresh" in legend and "q quit" in legend


def test_an_empty_list_advertises_globals_only(env):
	store = env
	state = _ready(store)
	assert not state.rows
	legend = _legend(state)
	for contextual in ("Enter open", "c close", "r reply", "[/] part",
	                   "v read", "m save"):
		assert contextual not in legend, f"{contextual!r} offered with nothing selected"
	assert "n new" in legend and "? help" in legend


def test_part_navigation_is_offered_only_when_there_is_more_than_one_part(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="One",
	           body=b"single\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	assert "[/] part" not in _legend(state), "part navigation offered for one part"
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Two", parts=[
		{"content_type": "text/plain; charset=utf-8", "body": b"a\n"},
		{"content_type": "text/plain; charset=utf-8", "body": b"b\n"}])
	state.refresh(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["subject"] == "Two")
	state.preview(store)
	_press(state, store, K.ENTER_LF)
	assert "[/] part" in _legend(state)


def test_nothing_advertised_refuses_for_want_of_state(env):
	"""The matrix property, and the reason there is ONE affordance query: with
	two predicates this is a hope; with one it is checkable.

	Walks a range of states and asserts every contextual key the footer offers
	is one dispatch would accept, and every key it withholds is one dispatch
	would refuse."""
	from baton_tui.driver import _AFFORDANCE, _allowed
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="In", parts=[
		{"content_type": "text/plain; charset=utf-8", "body": b"a\n"},
		{"content_type": "text/plain; charset=utf-8", "body": b"b\n"}])
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Out", body=b"x\n")
	state = _ready(store)
	seen = 0
	for index in range(len(state.rows)):
		state.cursor = index
		state.preview(store)
		for opened in (False, True):
			if opened:
				_press(state, store, K.ENTER_LF)
			legend = _legend(state)
			available = state.affordances()
			for event, name in _AFFORDANCE.items():
				offered = {
					"open": "Enter open", "reply": "r reply", "close": "c close",
					"part_nav": "[/] part", "read_part": "v read",
					"materialize": "m save", "hscroll": "h/l sideways",
				}[name] in legend
				assert offered == bool(available[name]), (
					f"row {index} opened={opened}: {name} offered={offered} "
					f"but available={available[name]}")
				assert _allowed(state, event) == bool(available[name]), (
					f"row {index}: dispatch and the footer disagree about {name}")
			seen += 1
	assert seen >= 6, "the sweep did not cover enough states"


def test_the_legend_follows_focus(env):
	"""LIST focus advertises list movement; DETAIL focus advertises
	scrolling. The wording is what the keys actually do."""
	store = env
	_long_message(store)
	state = _ready(store)
	assert "j/k move" in _legend(state)
	assert "Tab focus" in _legend(state)
	_press(state, store, K.TAB)
	assert "j/k scroll" in _legend(state)
	assert "gg/G top/bottom" in _legend(state)


def test_the_legend_recomputes_after_every_transition(env):
	"""It is composed per frame from the model, so there is no cache to go
	stale — asserted across open, reply, close and a view switch."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Owed", body=b"x\n")
	state = _ready(store)
	seen = [_legend(state)]
	_press(state, store, K.ENTER_LF)
	seen.append(_legend(state))
	_press(state, store, K.TAB)
	seen.append(_legend(state))
	_press(state, store, K.TAB)
	_press(state, store, ord("c"))
	seen.append(_legend(state))
	_press(state, store, ord("o"))
	seen.append(_legend(state))
	assert len(set(seen)) >= 4, "the legend did not change with the state"


# -- review: three affordance gaps ------------------------------------------

def test_sent_can_be_opened_when_the_message_list_is_empty(env):
	"""R1, reproduced exactly as reported: `open` read the MESSAGES selection
	while SENT was on screen, so an empty inbox hid Enter from a sent row that
	was selectable and read-only to open."""
	from baton_tui.state import VIEW_SENT
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Out",
	           body=b"x\n")
	state = _ready(store)
	# Nothing INBOUND at all: every row is outbound, so the Sent filter has a
	# row and the actionable list has none of its own to offer.
	state.rows = []
	state.select_view(VIEW_SENT)
	state.preview(store)
	assert state.sent_rows and not state.rows
	assert state.affordances()["open"] is True
	assert "Enter open" in _legend(state)
	_press(state, store, K.ENTER_LF)
	assert state.status_severity != "error", state.status
	assert "sent" in (state.detail or {}), "the sent row did not open"


def test_the_inverse_asymmetry_still_refuses(env):
	"""The other half, so the fix cannot invert: rows in MESSAGES and none in
	SENT, while SENT is the active view."""
	from baton_tui.state import VIEW_SENT
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="In", body=b"x\n")
	state = _ready(store)
	assert state.rows and not state.sent_rows
	state.select_view(VIEW_SENT)
	state.preview(store)
	assert state.affordances()["open"] is False
	assert "Enter open" not in _legend(state)
	before = _writes(store)
	_press(state, store, K.ENTER_LF)
	assert _writes(store) == before, "Enter acted with nothing selected"


def test_both_reply_keys_answer_to_the_same_affordance(env):
	"""R2: the footer grouped `r reply  R editor` under one affordance while
	only `r` was gated, so `R` stayed dispatchable and refused through a
	SECOND predicate inside `begin_reply` -- the drift one query exists to
	stop."""
	from baton_tui.driver import _AFFORDANCE, _allowed
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert _AFFORDANCE[K.EDIT_BODY] == "reply"
	# Nothing opened: both forms are hidden AND both are inert.
	assert not state.affordances()["reply"]
	assert not _allowed(state, K.REPLY)
	assert not _allowed(state, K.EDIT_BODY)
	legend = _legend(state)
	assert "r reply" not in legend and "R editor" not in legend
	seeds = []
	step(state, store, ord("r"), 100, 24, edit_fn=_editor("x", record=seeds))
	assert not seeds, "R opened the editor with nothing to reply to"
	assert state.mode == MODE_BROWSE
	# Claim it: both become offered and both dispatch.
	_press(state, store, K.ENTER_LF)
	assert _allowed(state, K.REPLY) and _allowed(state, K.EDIT_BODY)
	assert "r reply" in _legend(state) and "R editor" in _legend(state)
	step(state, store, ord("r"), 100, 24, edit_fn=_editor("a body", record=seeds))
	assert seeds, "R did not reach the editor once a claim was held"


@pytest.mark.parametrize("build", [_handled_inbound, _handled_outbound])
def test_both_reply_forms_move_together_for_follow_ups(env, build):
	"""And for a follow-up target, which is the third way `reply` becomes
	available."""
	from baton_tui.driver import _allowed
	store = env
	state, _ = build(store)
	assert not _allowed(state, K.REPLY) and not _allowed(state, K.EDIT_BODY)
	_press(state, store, K.ENTER_LF)
	assert _allowed(state, K.REPLY) and _allowed(state, K.EDIT_BODY)


def test_both_reply_forms_move_together_for_a_notice(env):
	from baton_tui.driver import _allowed
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	assert not _allowed(state, K.EDIT_BODY)
	_press(state, store, K.ENTER_LF)
	assert _allowed(state, K.REPLY) and _allowed(state, K.EDIT_BODY)
	assert "R editor" in _legend(state)


# R3: a modal footer describes only that mode.

_BROWSE_ONLY = ("n new", "N notice", "i/o view", "Ctrl+r refresh", "? help",
                "q quit", "Tab focus", "c close", "Enter open", "m save")


def _pick_root(state, root_id):
	"""The letter that selects this root on the page now showing."""
	for label, entry in state.root_entries():
		if entry["root_id"] == root_id:
			return ord(label)
	raise AssertionError(f"{root_id} is not on this page: {state.root_entries()}")


def _enter_mode(state, store, mode):
	from baton_tui.state import (MODE_COMPOSE, MODE_HELP, MODE_NOTICE,
	                             MODE_PICK_RECIPIENT, MODE_PICK_ROOT,
	                             MODE_REPLY)
	if mode == MODE_HELP:
		_press(state, store, ord("?"))
	elif mode == MODE_PICK_ROOT:
		# Through the real route: compose, Tab to the empty attach path,
		# Enter. If that route ever stops reaching the picker this fails here
		# as well as in its own pin.
		_press(state, store, ord("n"))
		_press(state, store, _pick(state, "acme.reviewer"))
		_press(state, store, K.TAB)
		_press(state, store, K.ENTER_LF)
	elif mode == MODE_PICK_RECIPIENT:
		_press(state, store, ord("n"))
	elif mode == MODE_NOTICE:
		_press(state, store, ord("N"))
	elif mode == MODE_COMPOSE:
		_press(state, store, ord("n"))
		_press(state, store, _pick(state, "acme.reviewer"))
	elif mode == MODE_REPLY:
		_press(state, store, K.ENTER_LF, ord("R"))
	assert state.mode == mode, f"did not reach {mode}: {state.mode}"


@pytest.mark.parametrize("mode", list(K.MODE_LEGENDS))
def test_a_modal_footer_advertises_only_that_modes_controls(env, mode):
	"""R3. The browse footer was drawn in every mode, so HELP offered `n new`
	and `^R refresh`, and the recipient picker offered open/reply/close from
	the row hidden behind it -- all keys the mode tables deliberately
	swallow."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_enter_mode(state, store, mode)
	legend = _legend(state)
	for browse in _BROWSE_ONLY:
		assert browse not in legend, f"{mode} advertises {browse!r}"
	enabled = state.modal_affordances()
	for label, _, condition in K.MODE_LEGENDS[mode]:
		expected = condition is None or enabled.get(condition)
		assert (label in legend) is bool(expected), (
			f"{mode}: {label!r} advertised={label in legend} "
			f"but meaningful={bool(expected)}")


@pytest.mark.parametrize("mode", list(K.MODE_LEGENDS))
def test_every_advertised_modal_control_dispatches_in_that_mode(env, mode):
	"""Advertised from the SAME table that decides the mode's keys, so the
	footer cannot describe a key the mode swallows."""
	for label, codes, _ in K.MODE_LEGENDS[mode]:
		for code in codes:
			event, _ = K.map_key(code, mode)
			assert event != K.IGNORE, (
				f"{mode} advertises {label!r} but {code!r} is inert there")


def test_the_confirmation_footers_keep_their_exact_one_line_form(env):
	"""The two confirmations already had their own single-line legends, and
	the modal work must not have disturbed them."""
	from baton_tui.render import CONFIRM_SEND_FOOTER
	store = env
	state = _drafted(store, "compose")
	_press(state, store, K.ENTER_LF)
	screen = render(state, 100, 24)
	assert screen[-1].strip() == CONFIRM_SEND_FOOTER
	assert len(screen) == 24
	_press(state, store, ord("n"))
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Owed", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)                  # a claim is now owed
	_press(state, store, ord("q"))                    # quit asks
	screen = render(state, 100, 24)
	assert "QUIT WITH UNRESOLVED CLAIMS?" in screen[-2]
	assert len(screen) == 24


# -- review R4: the context line must not invent an obligation -------------

@pytest.mark.parametrize("build", [_handled_inbound, _handled_outbound])
def test_a_follow_up_row_never_says_close_is_owed(env, build):
	"""R4. The old `action_target_description` keyed off `row_type`, and a
	follow-up target is message-shaped with no claim -- so it said
	`owed: reply or close` while the affordance query correctly refused close.
	Two statements about one row, and the false one named an obligation that
	does not exist.

	SUPERSEDED IN LOCATION: the clause it produced is off the screen, along
	with the whole ordinary footer. The DISAGREEMENT is what mattered, so this
	now asserts the facts that survived -- nothing owed, and a follow-up is
	what the keys would do."""
	store = env
	state, mid = build(store)
	_press(state, store, K.ENTER_LF)
	assert state.affordances()["close"] is False, "an obligation was invented"
	assert state.follow_up_context, "the row offers no follow-up either"
	assert state.opened["id"] == mid
	assert "needs a claim you hold" in state.unavailable_reason("close")


def test_an_active_claim_still_says_what_is_owed(env):
	"""The other side: where an obligation DOES exist, it is still reported.
	Removing the false case must not remove the true one."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Owed", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	assert state.affordances()["close"] is True
	assert state.unresolved_count() == 1, "the header no longer counts it"
	_press(state, store, ord("c"))
	assert state.affordances()["close"] is False
	assert state.unresolved_count() == 0


def test_an_opened_notice_says_nothing_is_owed(env):
	"""A notice keeps its explicit wording; it has no claim to complete."""
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF)
	assert state.affordances()["close"] is False
	assert state.unresolved_count() == 0, "a broadcast was counted as owed"


def test_the_context_line_and_the_legend_never_disagree_about_close(env):
	"""One row, one story. Swept across every row kind, opened and not.

	SUPERSEDED IN LOCATION: there is no context line and no legend to
	disagree. The surviving pair is the affordance query and the refusal it
	produces -- if `close` is unavailable, pressing `c` must be refused with a
	reason, and if it is available, pressing `c` must work."""
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="In", body=b"x\n")
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Out", body=b"x\n")
	state = _ready(store)
	for index in range(len(state.rows)):
		state.cursor = index
		state.preview(store)
		for _ in range(2):
			available = bool(state.affordances()["close"])
			reason = state.unavailable_reason("close")
			assert reason, "an unavailable close has no explanation to give"
			before = state.unresolved_count()
			_press(state, store, ord("c"))
			if available:
				assert state.unresolved_count() == before - 1, (
					f"row {index}: close was offered and did nothing")
			else:
				assert state.status == reason, (
					f"row {index}: close was refused without saying why")
				assert state.unresolved_count() == before
			_press(state, store, K.ENTER_LF)


# -- review R5: a mapped key that changes nothing is not an affordance ------

def test_a_one_field_notice_does_not_advertise_tab(env):
	"""R5. `NOTICE_FIELDS` is exactly `("subject",)`, so `Tab` is live and
	moves modulo one — the same field. The footer promised a change the key
	cannot make."""
	store = env
	state = _ready(store)
	_press(state, store, ord("N"))
	assert len(state.compose_fields) == 1
	legend = _legend(state)
	assert "Tab" not in legend, legend
	# Everything else the mode does offer is still there.
	assert "Ctrl+e editor" in legend and "Esc cancel" in legend


def test_directed_compose_keeps_tab_because_it_has_fields_to_move_between(env):
	"""The other side, so the fix does not overreach into hiding a control
	that works."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	assert len(state.compose_fields) > 1
	assert "Tab next field" in _legend(state)
	field = state.compose_field
	_press(state, store, K.TAB)
	assert state.compose_field != field, "the advertised Tab did nothing"


def test_a_one_page_picker_does_not_advertise_paging(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	assert state.picker_pages == 1
	legend = _legend(state)
	assert "Tab next page" not in legend, legend
	assert "a-z choose a recipient" in legend


def test_a_multi_page_picker_advertises_paging_and_it_works(tmp_path):
	"""Enough participants to need a second page, so `Tab` reaches one."""
	store_path = tmp_path / "many"
	store_path.mkdir()
	path = str(store_path / "baton.json")
	participants = {f"team{index:02d}.member": {} for index in range(40)}
	participants["acme.implementer"] = {}
	with open(path, "w") as handle:
		json.dump({"config_version": 1, "protocol_version": 9, "generation": 1,
		           "mailbox": {"name": "many"}, "participants": participants,
		           "roots": {}, "retention_days": 90}, handle)
	core.init_instance(path)
	with core.open_instance(path) as store:
		state = InboxState("acme.implementer")
		state.refresh(store)
		state.set_viewport(**layout_for(100, 24))
		_press(state, store, ord("n"))
		assert state.picker_pages > 1
		assert "Tab next page" in _legend(state)
		page = state.picker_page
		_press(state, store, K.TAB)
		assert state.picker_page != page, "the advertised paging did nothing"


def test_movement_is_not_hidden_merely_at_a_boundary(env):
	"""The limit of the rule, stated so it is not broadened later: `j` at the
	last row still means something, because the list can move. R5 is only for
	controls with no other state to reach at all."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Only", body=b"x\n")
	state = _ready(store)
	_press(state, store, ord("G"))                    # at the last row
	assert "j/k move" in _legend(state)
	_press(state, store, K.TAB)                       # detail at the top
	assert "j/k scroll" in _legend(state)


# -- RULED: h/l scroll the DETAIL pane sideways ---------------------------

def _unwrappable(store, subject="Long token", tail="ENDMARKER"):
	store.send("acme.reviewer", "acme.implementer", kind="q", subject=subject,
	           body=("see " + "ABCDEFGHIJ" * 15 + tail + " after\n").encode())


def _focused_detail(store, columns=60, lines=20):
	state = _ready(store)
	step(state, store, K.ENTER_LF, columns, lines)
	step(state, store, K.TAB, columns, lines)
	return state


def _content_rows(state, columns=60, lines=20):
	"""Rows below the rule and above the footer.

	Matched on `DETAIL ` plus the divider glyph rather than on the start of
	the line: the FOCUSED form is `> DETAIL`, so a `lstrip().startswith` test
	misses exactly the case these tests are about."""
	screen = render(state, columns, lines)
	rule = next(i for i, l in enumerate(screen)
	            if "DETAIL " in l and DIVIDER in l)
	return screen[rule + 1:-1]


def test_detail_focus_reveals_the_tail_of_an_unwrappable_token(env):
	"""The reason horizontal movement exists: ordinary prose wraps, and a
	token longer than the pane cannot. Nothing is discarded -- the tail is
	REACHABLE, and returning to column zero is exact."""
	store = env
	_unwrappable(store)
	state = _focused_detail(store)
	assert state.affordances()["hscroll"] is True
	assert "ENDMARKER" not in "\n".join(_content_rows(state))
	for _ in range(400):
		step(state, store, ord("l"), 60, 20)
	assert "ENDMARKER" in "\n".join(_content_rows(state)), "the tail is unreachable"
	for _ in range(600):
		step(state, store, ord("h"), 60, 20)
	assert state.detail_hscroll == 0, "did not return exactly to column zero"


@pytest.mark.parametrize("key", [K.KEY_LEFT, K.KEY_RIGHT])
def test_the_arrows_do_the_same_as_h_and_l(env, key):
	store = env
	_unwrappable(store)
	state = _focused_detail(store)
	before = state.detail_hscroll
	step(state, store, key, 60, 20)
	if key == K.KEY_RIGHT:
		assert state.detail_hscroll == before + 1
	else:
		assert state.detail_hscroll == before


def test_the_hidden_side_is_always_indicated(env):
	"""Leading, trailing and both. Nothing is silently off screen."""
	from baton_tui.safe_text import ELLIPSIS
	store = env
	_unwrappable(store)
	state = _focused_detail(store)

	def content():
		return [l for l in _content_rows(state) if "ABCDEFGHIJ" in l][0]

	at_zero = content()
	assert not at_zero.lstrip().startswith(ELLIPSIS)
	assert at_zero.endswith(ELLIPSIS), "nothing said the right side was hidden"
	for _ in range(30):
		step(state, store, ord("l"), 60, 20)
	middle = content()
	assert middle.startswith(ELLIPSIS) and middle.endswith(ELLIPSIS)
	for _ in range(400):
		step(state, store, ord("l"), 60, 20)
	end = content()
	assert end.startswith(ELLIPSIS) and not end.endswith(ELLIPSIS)


@pytest.mark.parametrize("columns", [40, 60, 100])
def test_horizontal_scrolling_never_exceeds_the_terminal(env, columns):
	"""Including with wide cells, which must never be split in half."""
	from baton_tui.safe_text import display_width
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Wide",
	           body=("広い" * 60 + "\n").encode())
	state = _ready(store)
	step(state, store, K.ENTER_LF, columns, 20)
	step(state, store, K.TAB, columns, 20)
	for _ in range(80):
		screen = render(state, columns, 20)
		assert len(screen) == 20
		for line in screen:
			assert display_width(line) <= columns, repr(line)
		step(state, store, ord("l"), columns, 20)


def test_ordinary_prose_gains_no_sideways_overflow(env):
	"""It still wraps at whitespace, so there is nothing to scroll to and the
	affordance is not offered."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Prose",
	           body=("ordinary words that wrap perfectly well " * 12).encode())
	state = _focused_detail(store)
	assert state.detail_overflow == 0
	assert state.affordances()["hscroll"] is False
	assert "h/l sideways" not in _legend(state, 200, 20)


def test_list_focus_leaves_everything_alone_on_h_and_l(env):
	"""Unbound there for now. No list action was invented."""
	store = env
	_unwrappable(store)
	state = _ready(store)
	step(state, store, K.ENTER_LF, 60, 20)
	before = (_writes(store), state.cursor, state.detail_offset,
	          state.detail_hscroll, dict(state.opened))
	for key in (ord("h"), ord("l"), K.KEY_LEFT, K.KEY_RIGHT):
		step(state, store, key, 60, 20)
	assert (_writes(store), state.cursor, state.detail_offset,
	        state.detail_hscroll, dict(state.opened)) == before
	assert "h/l sideways" not in _legend(state, 200, 20)


def test_horizontal_movement_writes_nothing(env):
	store = env
	_unwrappable(store)
	state = _focused_detail(store)
	before = _writes(store)
	for _ in range(50):
		step(state, store, ord("l"), 60, 20)
	assert _writes(store) == before


def test_the_offset_survives_what_it_should_and_resets_when_it_must(env):
	"""It belongs to the content being read."""
	from baton_tui.driver import apply_layout
	store = env
	_unwrappable(store)
	store.send("hq.lead", "acme.implementer", kind="q", subject="Other", body=b"x\n")
	state = _ready(store)
	state.cursor = next(i for i, r in enumerate(state.rows)
	                    if r["subject"] == "Long token")
	state.preview(store)
	step(state, store, K.ENTER_LF, 60, 20)
	step(state, store, K.TAB, 60, 20)
	for _ in range(20):
		step(state, store, ord("l"), 60, 20)
	held = state.detail_hscroll
	assert held > 0
	# Survives: focus toggles, vertical scrolling, refresh, redraw, resize.
	step(state, store, K.TAB, 60, 20)
	step(state, store, K.TAB, 60, 20)
	assert state.detail_hscroll == held
	step(state, store, ord("j"), 60, 20)
	assert state.detail_hscroll == held
	step(state, store, K.CTRL_R, 60, 20)
	assert state.detail_hscroll == held
	apply_layout(state, 60, 20)
	assert state.detail_hscroll == held
	# Resets: a different message. In whichever direction there is one --
	# same-second sends tie and order by id, so "the row below" may not exist
	# and `move` would then be a no-op that resets nothing. Same flake shape
	# as the list-focus test; caught by the full run, not in isolation.
	step(state, store, K.TAB, 60, 20)
	start = state.cursor
	state.move(1 if start < len(state.rows) - 1 else -1, store)
	assert state.cursor != start, "the fixture has only one row"
	assert state.detail_hscroll == 0


def test_the_offset_is_clamped_after_a_narrowing_resize(env):
	"""A resize must not leave the view past the end of its own content."""
	store = env
	_unwrappable(store)
	state = _focused_detail(store, 120, 20)
	for _ in range(400):
		step(state, store, ord("l"), 120, 20)
	wide = state.detail_hscroll
	step(state, store, K.IGNORE if False else ord("l"), 40, 20)
	assert state.detail_hscroll <= wide + 1
	from baton_tui.render import detail_overflow
	assert state.detail_hscroll <= 40 + detail_overflow(state, 40, 20)


# -- live trial: the poll timeout is a LOOP INVARIANT ----------------------

class _FakeWindow:
	"""Enough curses to record input-mode changes.

	The real defect is invisible to the model tests and expensive to catch
	over a PTY, because it is about which mode `getch` is left in -- so it is
	pinned on the mode transitions themselves."""

	def __init__(self):
		self.timeouts = []
		self.blocking = None
		self.keys = []

	def timeout(self, milliseconds):
		self.timeouts.append(milliseconds)
		self.blocking = milliseconds < 0

	def nodelay(self, flag):
		# What curses actually does: True = never block, False = block
		# FOREVER. Neither is the finite delay the poll needs.
		self.blocking = not flag
		self.timeouts.append(-1 if not flag else 0)

	def getch(self):
		return self.keys.pop(0) if self.keys else -1


def test_arming_the_poll_sets_a_finite_timeout(env):
	from baton_tui.driver import arm_poll
	window = _FakeWindow()
	arm_poll(window, 2.0)
	assert window.timeouts == [2000]
	assert window.blocking is False


def test_the_escape_decoder_restores_the_poll_not_blocking_mode(env):
	"""`nodelay(False)` is BLOCKING mode, not the finite delay it replaced.
	Every bare Esc left the console waiting forever with mail pending."""
	from baton_tui.driver import _read_key
	window = _FakeWindow()
	window.keys = [K.ESC]
	assert _read_key(window, 2.0) == K.ESC
	assert window.timeouts[-1] == 2000, window.timeouts
	assert window.blocking is False, "the console was left blocking after Esc"


def test_a_decoded_escape_sequence_also_restores_the_poll(env):
	"""The arrow path takes the same detour through nodelay."""
	from baton_tui.driver import _read_key
	window = _FakeWindow()
	window.keys = [K.ESC, ord("["), ord("B")]
	assert _read_key(window, 2.0) == K.KEY_DOWN
	assert window.timeouts[-1] == 2000
	assert window.blocking is False


def test_an_unknown_escape_sequence_also_restores_the_poll(env):
	from baton_tui.driver import _read_key
	window = _FakeWindow()
	window.keys = [K.ESC, ord("["), ord("~")]
	_read_key(window, 2.0)
	assert window.timeouts[-1] == 2000
	assert window.blocking is False


def test_the_poll_interval_is_preserved_not_busy_looped(env):
	"""Re-arming must not turn into a spin: the configured interval is what
	is re-applied, whatever it is."""
	from baton_tui.driver import _read_key, arm_poll
	for seconds in (0.5, 2.0, 5.0):
		window = _FakeWindow()
		arm_poll(window, seconds)
		window.keys = [K.ESC]
		_read_key(window, seconds)
		assert window.timeouts[-1] == int(seconds * 1000)
		assert all(t != 0 for t in window.timeouts[-1:]), "polling became a spin"


# -- RULED (major supersession): highlighting a directed row claims it -----

def test_startup_selection_claims_and_opens_the_highlighted_row(env):
	"""Point 1: the initial selected row follows the ruling too, so launching
	the console on a pending directed message claims it."""
	from baton_tui.driver import first_selection
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Waiting",
	           body=b"the body\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
	first_selection(state, store)
	assert state.opened is not None
	assert state.opened["claim_id"] is not None
	assert "delivery" in state.detail
	assert "the body" in "\n".join(render(state, 100, 24))


def test_a_poll_never_claims_sees_or_steals_the_selection(env):
	"""The boundary that keeps the tradeoff bounded. An arrival must not be
	claimed because it ARRIVED, and restoring the same identity must not
	re-claim."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="First", body=b"a\n")
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	state.select_row(store)                           # one deliberate selection
	claims = store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
	chosen = state.selected["id"]
	store.send("hq.lead", "acme.implementer", kind="q", subject="Arrival", body=b"b\n")
	for _ in range(5):
		state.refresh(store)
	assert store.conn.execute(
		"SELECT COUNT(*) FROM claims").fetchone()[0] == claims, "a poll claimed"
	assert store.conn.execute(
		"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0, "a poll consumed a notice"
	assert state.selected["id"] == chosen, "a poll stole the selection"


def test_a_reordering_poll_cannot_redirect_a_claim(env):
	"""Identity, not index. This console has produced the wrong-target bug
	twice; claim-on-highlight makes its consequence a CLAIM rather than a
	misdirected keystroke."""
	import time
	store = env
	for index in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=b"x\n")
	state = _ready(store)
	state.move(1, store)
	chosen = state.selected["id"]
	claimed = {r[0] for r in store.conn.execute(
		"SELECT message_id FROM claims").fetchall()}
	time.sleep(1.1)
	store.send("hq.lead", "acme.implementer", kind="q", subject="Newer", body=b"x\n")
	state.refresh(store)
	assert state.rows[0]["subject"] == "Newer", "the arrival is not at the top"
	assert state.selected["id"] == chosen, "the selection followed the index"
	assert {r[0] for r in store.conn.execute(
		"SELECT message_id FROM claims").fetchall()} == claimed


def test_highlighting_an_unseen_notice_records_no_receipt(env):
	"""Slawomir authorised claim-on-highlight for DIRECTED messages, not
	implicit consumption of broadcasts. Enter remains the atomic action."""
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"body\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Directed", body=b"x\n")
	state = _ready(store)
	for _ in range(6):
		_press(state, store, ord("j"))
		_press(state, store, ord("k"))
	assert store.conn.execute(
		"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0
	# ...and Enter is still advertised on it, because it has not been consumed.
	state.cursor = next(i for i, r in enumerate(state.rows)
	                    if r["row_type"] == "notice")
	state.select_row(store)
	assert "Enter open" in _legend(state)
	_press(state, store, K.ENTER_LF)
	assert store.conn.execute(
		"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 1


def test_enter_stops_being_advertised_once_the_row_is_open(env):
	"""Point 8: it would be a no-op, so the footer moves straight to what
	works now."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	legend = _legend(state)
	assert "Enter open" not in legend, legend
	assert "c close" in legend and "r reply" in legend


def test_detail_focus_navigation_still_claims_nothing(env):
	"""Point 4: DETAIL navigation does not move the selection, so it cannot
	commit anything."""
	store = env
	for index in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=("line\n" * 60).encode())
	state = _ready(store)
	state.select_row(store)
	before = _writes(store)
	chosen = state.selected["id"]
	_press(state, store, K.TAB)
	for key in (ord("j"), ord("k"), ord("h"), ord("l"), ord("G"), K.CTRL_D):
		_press(state, store, key)
	assert _writes(store) == before, "detail navigation touched the authority"
	assert state.selected["id"] == chosen


def test_moving_across_pending_rows_accumulates_claims_and_closes_none(env):
	"""The accepted consequence, pinned so it is a decision rather than a
	surprise -- and so the promise that nothing is auto-resolved is checked."""
	store = env
	for index in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	for _ in range(3):
		_press(state, store, ord("j"))
	assert state.unresolved_count() == 4
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0, "a claim was auto-resolved"
	# The quit confirmation is what protects them.
	assert state.request_quit() is False


def test_handled_and_outbound_rows_stay_observational_on_highlight(env):
	"""They have no claim to take; highlighting opens the retained copy and
	arms a follow-up, exactly as before."""
	store = env
	for build in (_handled_inbound, _handled_outbound):
		state, mid = build(store)
		before = _writes(store)
		state.select_row(store)
		assert _writes(store) == before, "highlighting a handled row wrote"
		assert state.opened is not None
		assert state.opened["claim_id"] is None
		assert state.follow_up_context is not None


# -- batch 1 review R1: a view switch establishes its destination ----------

def test_switching_back_to_messages_claims_the_highlighted_pending_row(env):
	"""The reported hole, in its reported shape: MESSAGES empty while the
	human is in SENT, a pending message arrives, press `i` — and the row was
	highlighted but unclaimed, which is the extra-Enter ceremony the ruling
	removed, reachable by a different door."""
	from baton_tui.state import VIEW_INBOX, VIEW_SENT
	store = env
	state = _ready(store)
	_press(state, store, ord("o"))
	assert state.view == VIEW_SENT
	# MESSAGES genuinely empty, which is the reported shape: there is no prior
	# selection for identity restoration to hold onto, so the arrival becomes
	# the highlighted row.
	assert not state.rows
	# It arrives while the human is elsewhere; the POLL must not claim it.
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Arrived",
	           body=b"the body\n")
	state.refresh(store)
	assert store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0, \
		"the poll claimed"
	_press(state, store, ord("i"))
	assert state.view == VIEW_INBOX
	assert state.selected["subject"] == "Arrived", "it is not the highlighted row"
	assert state.opened is not None and state.opened["claim_id"] is not None, \
		"switching back left the row highlighted but unclaimed"
	assert "the body" in "\n".join(render(state, 100, 24))


def test_switching_to_a_notice_row_still_records_no_receipt(env):
	"""A view switch decides per ROW, not per view: a broadcast stays
	explicit however you arrive at it."""
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	_press(state, store, ord("o"))
	_press(state, store, ord("i"))
	assert state.selected["row_type"] == "notice"
	assert store.conn.execute(
		"SELECT COUNT(*) FROM notice_seen").fetchone()[0] == 0


@pytest.mark.parametrize("build", [_handled_inbound, _handled_outbound])
def test_switching_onto_a_handled_or_outbound_row_writes_nothing(env, build):
	"""They have no claim to take, so arriving at them is observational."""
	store = env
	state, _ = build(store)
	before = _writes(store)
	_press(state, store, ord("o"))
	_press(state, store, ord("i"))
	assert _writes(store) == before, "arriving at a handled row wrote"


# -- BATCH 2: chrome stays fixed while content pans -----------------------

def test_metadata_and_part_headers_do_not_pan(env):
	"""Panning the chrome off the left edge would make the pane unreadable in
	order to fix a line: the human loses which message they are in and which
	part they are on, to reveal the tail of one body row."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Chrome stays put",
	           body=("see " + "ABCDEFGHIJ" * 12 + "ENDMARK\n").encode())
	state = _focused_detail(store)
	before = [line for line in _content_rows(state)
	          if line.lstrip().startswith(("From:", "Subject:", "Kind:", "Date:",
	                                       "State:", "[0]")) or "[0]" in line]
	assert before, "no chrome rows in the fixture"
	for _ in range(40):
		step(state, store, ord("l"), 60, 20)
	assert state.detail_hscroll > 0
	after = [line for line in _content_rows(state)
	         if line.lstrip().startswith(("From:", "Subject:", "Kind:", "Date:",
	                                      "State:", "[0]")) or "[0]" in line]
	assert after == before, "the chrome moved with the content"


def test_the_content_line_does_pan_while_chrome_holds(env):
	"""Both halves in one assertion, so a fix that froze everything would not
	pass."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Subj",
	           body=("see " + "ABCDEFGHIJ" * 12 + "ENDMARK\n").encode())
	state = _focused_detail(store)

	def rows():
		return _content_rows(state)

	assert any("Subject: Subj" in line for line in rows())
	assert "ENDMARK" not in "\n".join(rows())
	for _ in range(400):
		step(state, store, ord("l"), 60, 20)
	panned = rows()
	assert "ENDMARK" in "\n".join(panned), "the content did not pan"
	assert any("Subject: Subj" in line for line in panned), \
		"the subject header moved with it"


def test_no_chrome_line_is_ever_wider_than_the_pane(env):
	"""The reason chrome can be frozen safely.

	A frozen line that ran past the edge would be permanently unreadable --
	no key could reach its tail. So every chrome line must arrive already
	fitted to the width, elided if need be. This is what makes `detail_overflow`
	measuring content only correct rather than merely convenient.

	Written after the pin that stood here first turned out to be VACUOUS: it
	asserted a long subject offers no sideways movement, which passed even with
	the measurement deliberately broken, because the subject was elided long
	before it could be measured. This asserts the eliding instead."""
	from baton_tui.render import _detail_lines
	from baton_tui.safe_text import display_width
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="S" * 250, body=b"short\n", filename="X" * 200)
	state = _focused_detail(store)
	pannable: list[int] = []
	produced = _detail_lines(state, 60, pannable=pannable)
	movable = set(pannable)
	chrome = [line for index, line in enumerate(produced) if index not in movable]
	assert len(chrome) > 5, "the fixture produced no chrome to speak of"
	assert any(display_width(line) == 60 for line in chrome), \
		"nothing in this fixture was long enough to test the eliding"
	for line in chrome:
		assert display_width(line) <= 60, \
			f"a frozen line runs past the pane and can never be read: {line!r}"


# -- BATCH 2: a cancelled fresh editor reply restores the original ------------------

# `UNCHANGED` asks the fake editor to hand the seed straight back, which is
# what a real `:q!` does: exit zero, file untouched. It is NOT a failure, and
# the first version of these tests missed it entirely -- every case supplied
# `None`, so the parametrize ids claimed a coverage the bodies did not have.
UNCHANGED = object()


@pytest.mark.parametrize("outcome,message", [
	(None, "the editor exited without saving"),
	(None, "editor not found"),
	(None, "editor exited 1; draft unchanged"),
	(None, "the editor was killed"),
	(UNCHANGED, EDITOR_UNCHANGED),
])
def test_a_fresh_editor_reply_that_gives_nothing_back_restores_the_original(env, outcome, message):
	"""Cancel, missing, non-zero, killed, and SAVED-WITHOUT-CHANGES -- all the
	same shape: the one action did nothing, so the human is left reading the
	message they were reading.

	The last case is the one that was live. `:q!` exits successfully, so
	nothing in the failure path fires; the console imported the seed it had
	just written and left the human in a provisional reply they never typed."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Original",
	           body=b"the original body\n")
	state = _ready(store)
	state.select_row(store)
	opened = dict(state.opened)
	shown = "\n".join(render(state, 100, 24))
	assert "the original body" in shown

	step(state, store, ord("r"), 100, 24, edit_fn=_gives_back(outcome, message))
	assert state.mode == MODE_BROWSE, "left in an editor the human did not ask for"
	assert state.draft == "", "a seeded subject survived"
	assert not state.compose
	assert state.reply_body == "", "an unwritten body was imported"
	assert not state.reply_body_requested
	assert dict(state.opened) == opened, "the opened message changed"
	after = "\n".join(render(state, 100, 24))
	assert "the original body" in after, "the original is no longer displayed"
	# The editor's own explanation survives; it is not replaced by a summary.
	assert message in state.status


def _gives_back(outcome, message):
	"""An editor that returns nothing usable, one way or the other.

	The UNCHANGED case deliberately reports the SUCCESS message a real editor
	would: the console must decide from the bytes, not from what it was told."""
	def edit_fn(seed):
		if outcome is UNCHANGED:
			return seed, "draft imported — Enter reviews the send"
		return outcome, message
	return edit_fn


def test_ctrl_e_from_an_existing_draft_still_preserves_it(env):
	"""The distinction that must NOT be lost: inside a composition the human
	deliberately started, the editor is a step and the draft is theirs."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	_press(state, store, ord("R"))                    # a quick reply, by hand
	state.draft = "my own words"
	step(state, store, K.CTRL_E, 100, 24,
	     edit_fn=lambda seed: (None, "the editor exited without saving"))
	assert state.mode == MODE_REPLY, "a deliberate composition was abandoned"
	assert state.draft == "my own words", "the human's draft was discarded"


def test_a_fresh_editor_reply_that_succeeds_is_unaffected(env):
	"""The happy path must not have been narrowed by the restore."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	seeds = []
	step(state, store, ord("r"), 100, 24,
	     edit_fn=_editor("a full answer", record=seeds))
	assert seeds, "the editor never opened"
	assert state.mode == MODE_REPLY
	assert state.reply_body == "a full answer"
	assert state.draft == "Ask", "the subject was not inherited"


def test_a_fresh_editor_reply_over_a_handled_row_restores_that_view(env):
	"""A follow-up synthesizes a whole composition -- recipient, subject,
	thread -- before the editor is launched. If the editor gives nothing back,
	none of that provisional state may survive, and the handled copy the human
	was reading has to still be on screen."""
	store = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Handled", body=b"the answered body\n")
	claim = store.claim("acme.implementer", message_id=mid)
	store.close_claim(claim["claim_id"], participant="acme.implementer",
	                  outcome="done")
	state = _ready(store)
	state.select_row(store)
	opened = dict(state.opened)
	assert "the answered body" in "\n".join(render(state, 100, 24))

	step(state, store, ord("r"), 100, 24, edit_fn=_gives_back(UNCHANGED, ""))
	assert state.mode == MODE_BROWSE
	assert not state.compose, "a half-started follow-up survived"
	assert state.follow_up_to is None
	assert state.follow_up_thread is None
	assert dict(state.opened) == opened
	assert "the answered body" in "\n".join(render(state, 100, 24)), \
		"the handled copy is no longer displayed"
	assert EDITOR_UNCHANGED in state.status


def test_a_fresh_editor_reply_over_a_notice_restores_that_view(env):
	"""Third origin, same rule. A notice has no claim, so the console has even
	less to fall back on if the provisional composition is left behind."""
	store = env
	store.send_notice("acme.reviewer", kind="announcement", subject="Broadcast",
	                  body=b"the announced body\n")
	state = _ready(store)
	state.select_row(store)
	_press(state, store, K.ENTER_LF)               # notices open explicitly
	opened = dict(state.opened)
	assert "the announced body" in "\n".join(render(state, 100, 24))

	step(state, store, ord("r"), 100, 24, edit_fn=_gives_back(UNCHANGED, ""))
	assert state.mode == MODE_BROWSE
	assert not state.compose, "a half-started follow-up survived"
	assert dict(state.opened) == opened
	assert "the announced body" in "\n".join(render(state, 100, 24)), \
		"the notice is no longer displayed"


def test_ctrl_e_that_changes_nothing_keeps_the_draft_and_the_mode(env):
	"""The other half of the rule. Inside a composition the human started,
	an editor that saved nothing must not throw away what they already wrote --
	and must not claim to have imported it either."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	_press(state, store, ord("R"))
	state.draft = "my own words"
	state.reply_body = "a body I already wrote"
	step(state, store, K.CTRL_E, 100, 24, edit_fn=_gives_back(UNCHANGED, ""))
	assert state.mode == MODE_REPLY, "a deliberate composition was abandoned"
	assert state.draft == "my own words"
	assert state.reply_body == "a body I already wrote", "the body was disturbed"
	assert EDITOR_UNCHANGED in state.status


# -- BATCH 3 R1: no ordinary shortcut catalogue reaches the screen ---------

_CATALOGUE = ("n new", "N notice", "i/o view", "Ctrl+r refresh", "? help", "q quit",
              "Tab focus", "j/k move", "j/k scroll", "gg/G first/last",
              "gg/G top/bottom", "c close", "r reply", "R editor", "[/] part",
              "h/l sideways", "v read", "m save", "Enter open",
              "Tab next field", "Tab next page", "Ctrl+e editor", "Esc cancel",
              "a-z choose a recipient", "acting on", "owed:")
# NOT swept: `in reference to`. It reads like the removed target clause, and
# it was part of one -- but it is also how the STATUS reports what a follow-up
# just started, which is exactly what the bottom row is for. Listing it here
# failed intermittently, only when a preceding test had left that status
# showing, which is the sweep objecting to the console doing its job.


def _bottom(state, columns=200, lines=24):
	"""The footer, which is now exactly ONE row.

	Deliberately not the last two: the row above belongs to a pane, and the
	help screen legitimately ends `... 32 more (j/k scrolls)` there -- that is
	overflow state on the one surface whose job IS teaching keys, not a
	shortcut catalogue under the panes."""
	return render(state, columns, lines)[-1]


@pytest.mark.parametrize("phrase", _CATALOGUE)
def test_no_shortcut_catalogue_reaches_the_screen(env, phrase):
	"""Slawomir's ruling: ordinary bottom hints go away altogether. `?` help
	and the README own shortcuts; the bottom is ONE status line for what the
	console did.

	Swept across every mode and both focus states, because the catalogue used
	to be composed per mode -- fixing browse alone would leave it in the
	picker."""
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="In",
	           parts=[{"content_type": "text/markdown; charset=utf-8", "body": b"a\n"},
	                  {"content_type": "text/markdown; charset=utf-8", "body": b"b\n"}])
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Out", body=b"x\n")
	state = _ready(store)

	seen = [_bottom(state)]
	_press(state, store, K.TAB)                        # detail focus
	seen.append(_bottom(state))
	_press(state, store, K.TAB)
	for key in (ord("o"), ord("i"), ord("?")):         # sent, messages, help
		_press(state, store, key)
		seen.append(_bottom(state))
	_press(state, store, ord("q"))                     # leave help
	for start in (ord("R"), ord("n"), ord("N")):       # reply, picker, notice
		_press(state, store, start)
		seen.append(_bottom(state))
		_press(state, store, K.ESC)
	for bottom in seen:
		assert phrase not in bottom, f"{phrase!r} is still on the bottom rows"


def test_the_ordinary_footer_is_one_row_and_the_pane_took_the_other(env):
	"""The reclaimed row is the point: it goes to the panes, not to a blank."""
	from baton_tui.render import _body_lines
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	for lines in (12, 20, 24, 40):
		assert _body_lines(state, lines) == lines - 2, \
			"the footer is not one row"
		screen = render(state, 100, lines)
		assert len(screen) == lines
		# The last row is the status bar; the one above it belongs to a pane.
		assert screen[-1].strip() in ("", f"[i] {state.status}".strip()) \
			or state.status in screen[-1]


def test_an_empty_status_is_a_blank_row_not_a_reworded_hint(env):
	"""Explicitly ruled: do not replace the removed hints with reworded ones.
	The empty state is a blank row."""
	store = env
	state = _ready(store)
	state.set_status("", "info")
	assert render(state, 100, 24)[-1].strip() == ""


def test_the_send_confirmation_keeps_its_exact_literal(env):
	"""The one line that is still allowed to be an instruction, unchanged."""
	from baton_tui.render import CONFIRM_SEND_FOOTER
	store = env
	state = _drafted(store, "compose")
	_press(state, store, K.ENTER_LF)
	assert render(state, 100, 24)[-1].strip() == CONFIRM_SEND_FOOTER


# -- BATCH 3 R3: modal affordances gate DISPATCH, not only display ---------

def test_a_one_page_picker_refuses_to_page(env):
	"""A mapped key that cannot reach another state is not an affordance, and
	dispatching it anyway is a transition the human did not get anything
	from. R5, finished: the gate is on dispatch, where it always belonged."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	assert state.picker_pages == 1, "this fixture has more than one page"
	assert state.modal_affordances()["picker_paging"] is False
	before = state.picker_page
	_press(state, store, K.TAB)
	assert state.picker_page == before, "a one-page picker paged anyway"
	assert "every recipient fits" in state.status


def test_a_multi_page_picker_still_pages(env):
	"""The other direction, so the gate cannot be a blanket refusal."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	state.picker_rows = 1                     # force more than one page
	if state.picker_pages > 1:
		before = state.picker_page
		_press(state, store, K.TAB)
		assert state.picker_page != before, "a multi-page picker refused to page"


def test_a_one_field_notice_refuses_to_move_between_fields(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("N"))
	assert len(state.compose_fields) == 1, "this fixture has more than one field"
	assert state.modal_affordances()["more_fields"] is False
	before = state.compose_field
	_press(state, store, K.TAB)
	assert state.compose_field == before, "a one-field draft moved fields"
	assert "one field" in state.status


def test_a_directed_compose_still_moves_between_its_fields(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	state.pick_recipient("a")
	if len(state.compose_fields) > 1:
		before = state.compose_field
		_press(state, store, K.TAB)
		assert state.compose_field != before, "a multi-field draft refused to move"


# -- TRIAL: a successful send returns focus to the list --------------------

def _in_detail(state, store):
	"""Focus DETAIL first, or the assertion afterwards proves nothing."""
	_press(state, store, K.TAB)
	from baton_tui.state import FOCUS_DETAIL
	assert state.focus == FOCUS_DETAIL, "the fixture never left the list"


def _navigates_the_list(state, store):
	"""FUNCTIONAL focus, not the marker: a list key must move the selection
	and leave the detail offset alone.

	Review's point, and it was right -- the first version of these pins
	asserted `> MESSAGES` was on the header, which a cosmetic marker would
	satisfy while the keys still scrolled the detail pane."""
	assert len(state.rows) >= 2, "one row cannot show that navigation moved"
	before_row = state.selected["id"]
	before_offset = state.detail_offset
	_press(state, store, ord("j"))
	assert state.selected["id"] != before_row, \
		"a list key did not move the selection: the focus is cosmetic"
	assert state.detail_offset == before_offset, \
		"a list key scrolled the detail pane instead"


def test_a_successful_reply_returns_focus_to_the_list(env):
	"""Slawomir's trial ruling: the send finished that piece of work, and the
	natural next action is another message."""
	from baton_tui.state import FOCUS_LIST
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Other", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	selected = state.selected["id"]
	_in_detail(state, store)
	_press(state, store, ord("R"))
	state.draft = "an answer"
	_press(state, store, K.ENTER_LF, ord("y"))          # arm, then send
	assert state.focus == FOCUS_LIST, "focus stayed in the detail pane"
	assert "Sent" in state.status or "replied" in state.status
	assert state.selected is not None, "the selection was dropped"
	assert state.selected["id"] == selected, \
		"the selected row is not the one that was selected before the send"
	assert "> MESSAGES" in render(state, 100, 24)[0]
	_navigates_the_list(state, store)


def test_a_successful_compose_returns_focus_to_the_list(env):
	from baton_tui.state import FOCUS_LIST
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ctx", body=b"x\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ctx2", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	selected = state.selected["id"]
	_in_detail(state, store)
	state.begin_compose(recipient="acme.reviewer")
	state.compose["subject"] = "A new message"
	_press(state, store, K.ENTER_LF, ord("y"))
	assert state.focus == FOCUS_LIST, "focus stayed in the detail pane"
	assert "Sent" in state.status
	assert state.selected is not None and state.selected["id"] == selected, \
		"the selected row identity did not survive the send"
	_navigates_the_list(state, store)


def test_a_successful_notice_returns_focus_to_the_list(env):
	from baton_tui.state import FOCUS_LIST
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ctx", body=b"x\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ctx2", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	selected = state.selected["id"]
	_in_detail(state, store)
	state.begin_compose(notice=True)
	state.compose["subject"] = "A broadcast"
	_press(state, store, K.ENTER_LF, ord("y"))
	assert state.focus == FOCUS_LIST
	assert "Sent" in state.status
	assert state.selected is not None and state.selected["id"] == selected, \
		"the selected row identity did not survive the send"
	_navigates_the_list(state, store)


def test_a_successful_follow_up_returns_focus_to_the_list(env):
	from baton_tui.state import FOCUS_LIST
	store = env
	state, _mid = _handled_inbound(store)
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Other", body=b"x\n")
	state.refresh(store)
	state.select_row(store)
	selected = state.selected["id"]
	_in_detail(state, store)
	assert state.begin_reply(), "this fixture did not reach a follow-up"
	state.compose["subject"] = "A follow-up"
	_press(state, store, K.ENTER_LF, ord("y"))
	assert state.focus == FOCUS_LIST
	assert "Sent" in state.status
	assert state.selected is not None and state.selected["id"] == selected, \
		"the selected row identity did not survive the send"
	_navigates_the_list(state, store)


def test_a_declined_confirmation_leaves_focus_where_it_was(env):
	"""The negative side, and the reason the positive pins are not vacuous:
	nothing about arming or declining a send may move the human."""
	from baton_tui.state import FOCUS_DETAIL
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	_in_detail(state, store)
	_press(state, store, ord("R"))
	state.draft = "an answer"
	_press(state, store, K.ENTER_LF)                    # arm
	assert state.focus == FOCUS_DETAIL, "arming moved the focus"
	_press(state, store, ord("n"))                      # decline
	assert state.focus == FOCUS_DETAIL, "declining moved the focus"
	assert state.draft == "an answer", "the draft was lost"


def test_a_cancelled_draft_leaves_focus_where_it_was(env):
	from baton_tui.state import FOCUS_DETAIL
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	_in_detail(state, store)
	_press(state, store, ord("R"))
	_press(state, store, K.ESC)
	assert state.focus == FOCUS_DETAIL, "cancelling a draft moved the focus"


def test_a_failed_send_leaves_focus_and_draft_alone(env):
	"""The authority refusing must not be indistinguishable from success."""
	from baton_tui.state import FOCUS_DETAIL
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	_in_detail(state, store)
	_press(state, store, ord("R"))
	state.draft = "an answer"

	class Refuses:
		def __getattr__(self, name):
			return getattr(store, name)

		def reply(self, *args, **kwargs):
			raise core.BatonError("the authority is busy")

	_press(state, Refuses(), K.ENTER_LF, ord("y"))
	assert state.focus == FOCUS_DETAIL, "a failed send moved the focus"
	assert state.draft == "an answer", "a failed send discarded the draft"


# -- TRIAL: attachments are a chosen root plus a relative path -------------

def _message_count(store):
	return store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]


def _composing_with_attachment(env, path="EVIDENCE.md"):
	"""Through the real keystrokes: compose, Tab to the path, Enter, choose."""
	import os
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "Subject":
		_press(state, store, ord(char))
	_press(state, store, K.TAB)
	_press(state, store, K.ENTER_LF)
	assert state.mode == "pick_root", f"Enter did not open the root picker: {state.mode}"
	root = state.root_entries()[0][1]
	with open(os.path.join(root["path"], path), "wb") as handle:
		handle.write(b"the evidence\n")
	_press(state, store, _pick_root(state, root["root_id"]))
	for char in path:
		_press(state, store, ord(char))
	return state, store, root


def test_enter_on_the_empty_attach_path_opens_the_root_picker(env):
	"""Otherwise the picker is unreachable behind "Enter from any field
	reviews the send" -- a control that exists and cannot be got to."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	_press(state, store, K.TAB)
	assert state.compose_field_name == "attach_path"
	_press(state, store, K.ENTER_LF)
	assert state.mode == "pick_root"
	# ...and every configured root is offered with WHERE it points, because
	# the choice is a security boundary.
	screen = "\n".join(render(state, 100, 24))
	for entry in state.root_entries():
		assert entry[1]["root_id"] in screen
		assert entry[1]["path"] in screen


def test_once_a_root_is_chosen_enter_reviews_the_send(env):
	"""The other half of the same rule: the picker must not swallow Enter
	forever, or the message can never be sent from that field."""
	state, store, _root = _composing_with_attachment(env)
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_CONFIRM_SEND, state.mode


def test_the_locator_never_reaches_the_screen(env):
	"""`root_id:relative/path` is a serialization. Compose and send review
	show Root and Path separately."""
	state, store, root = _composing_with_attachment(env)
	composing = "\n".join(render(state, 100, 24))
	_press(state, store, K.ENTER_LF)                    # send review
	assert state.mode == MODE_CONFIRM_SEND, state.mode
	reviewing = "\n".join(render(state, 100, 24))
	for text in (composing, reviewing):
		assert f"{root['root_id']}:EVIDENCE.md" not in text, "the locator leaked"
		assert root["root_id"] in text, "the chosen root is not shown"
		assert "EVIDENCE.md" in text, "the path is not shown"
		assert "root:" in text and "path:" in text, "they were collapsed"


def test_the_locator_is_still_what_core_receives(env):
	"""The form is removed from the UI, not from the wire."""
	state, _store, root = _composing_with_attachment(env)
	assert state.attachment_locator() == f"{root['root_id']}:EVIDENCE.md"


@pytest.mark.parametrize("path,expected", [
	("", "the path within it is empty"),
	("/etc/passwd", "the path is relative to the chosen root"),
	("../outside.md", "clean relative path"),
	("./here.md", "clean relative path"),
	("sub//file.md", "clean relative path"),
	("sub/../file.md", "clean relative path"),
	(" report.md", "leading or trailing whitespace"),
	("report.md ", "leading or trailing whitespace"),
	("missing.md", "no such file inside"),
	("subdir", "is not a regular file"),
])
def test_every_refusal_is_actionable_and_keeps_the_draft(env, path, expected):
	"""Each refusal names what is wrong, and none of them costs the human the
	root they chose, the path they typed, or where they were."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	_press(state, store, K.TAB)
	_press(state, store, K.ENTER_LF)
	root = state.root_entries()[0][1]
	import os
	os.makedirs(os.path.join(root["path"], "subdir"), exist_ok=True)
	_press(state, store, _pick_root(state, root["root_id"]))
	state.compose["attach_path"] = path
	refusal = state.attachment_error()
	assert refusal, f"{path!r} was accepted"
	assert expected in refusal, refusal
	# Enter must NOT reach the confirmation. The refusal used to arrive after
	# `Send? Y/n` had been asked and answered, which spends a keystroke and a
	# moment of believing the message had gone.
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_COMPOSE, f"a bad path reached {state.mode}"
	assert state.compose.get("attach_root") == root["root_id"], "the root was lost"
	assert state.compose.get("attach_path") == path, "the typed path was lost"
	assert state.compose_field_name == "attach_path", \
		"the caret is not on the field the refusal is about"
	assert expected in state.status


def test_a_readable_regular_file_inside_the_root_is_accepted(env):
	"""The positive case, so the refusals are not just a blanket no."""
	state, _store, _root = _composing_with_attachment(env)
	assert state.attachment_error() is None, state.attachment_error()


def test_a_file_that_vanishes_after_review_is_not_published(env):
	"""Preflight passing is not proof. The file can go between the review and
	the confirmation, and the console must not publish on the strength of its
	own earlier look."""
	import os
	state, store, root = _composing_with_attachment(env)
	assert state.attachment_error() is None
	_press(state, store, K.ENTER_LF)                    # review; preflight passed
	assert state.mode == MODE_CONFIRM_SEND
	os.remove(os.path.join(root["path"], "EVIDENCE.md"))
	before = _message_count(store)
	_press(state, store, ord("y"))
	assert _message_count(store) == before, "a message was published anyway"
	assert state.compose.get("attach_path") == "EVIDENCE.md", "the draft was lost"
	assert state.compose.get("attach_root") == root["root_id"], "the root was lost"


def test_the_authority_still_decides_and_its_refusal_is_survivable(env):
	"""The boundary itself: preflight passing does NOT skip the store call,
	and whatever the authority says is what happens.

	Staged with a store that refuses, because preflight now mirrors core's
	rules closely enough that a path passing one and failing the other is
	hard to construct on purpose -- which is the point of mirroring them, and
	is exactly why this has to be pinned some other way."""
	state, store, _root = _composing_with_attachment(env)
	assert state.attachment_error() is None
	calls = []

	class Refuses:
		def __getattr__(self, name):
			return getattr(store, name)

		def send(self, *args, **kwargs):
			calls.append(kwargs.get("parts"))
			raise core.BatonError("the authority refused this attachment")

	_press(state, Refuses(), K.ENTER_LF, ord("y"))
	assert calls, "the console published on its own say-so without asking core"
	assert _message_count(store) == 0, "a message reached the store anyway"
	assert state.compose.get("attach_path") == "EVIDENCE.md", "the draft was lost"


def test_cancelling_the_root_picker_keeps_the_draft(env):
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	for char in "Keep me":
		_press(state, store, ord(char))
	_press(state, store, K.TAB)
	_press(state, store, K.ENTER_LF)
	assert state.mode == "pick_root"
	_press(state, store, K.ESC)
	assert state.mode == MODE_COMPOSE, "cancelling left the draft behind"
	assert state.compose["subject"] == "Keep me", "the draft was discarded"


def test_changing_the_root_keeps_a_path_that_still_resolves(env):
	"""And says so when it does not, instead of silently dropping it."""
	state, store, root = _composing_with_attachment(env)
	assert state.attachment_error() is None
	state.begin_pick_root(store)
	_press(state, store, _pick_root(state, root["root_id"]))
	assert state.compose["attach_path"] == "EVIDENCE.md", "the path was dropped"
	assert state.attachment_error() is None


# -- R3/R4: the cases the first handoff CLAIMED and did not have ----------

def _at_the_path_field(env):
	"""Composing, root chosen, caret on the path — the fixture the refusal
	cases share."""
	store = env
	state = _ready(store)
	_press(state, store, ord("n"))
	_press(state, store, _pick(state, "acme.reviewer"))
	_press(state, store, K.TAB)
	_press(state, store, K.ENTER_LF)
	root = state.root_entries()[0][1]
	_press(state, store, _pick_root(state, root["root_id"]))
	return state, store, root


def _refuses(state, store, path, fragment):
	state.compose["attach_path"] = path
	refusal = state.attachment_error()
	assert refusal, f"{path!r} was accepted; core would refuse it"
	assert fragment in refusal, refusal
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_COMPOSE, f"{path!r} reached {state.mode}"
	assert state.compose["attach_path"] == path, "the typed path was lost"


def test_a_leaf_symlink_is_refused_even_inside_the_root(env):
	"""The differentiator the review named. A `realpath` check accepts this:
	the link IS inside the root and DOES point at a regular file. Core opens
	every component with `O_NOFOLLOW` and refuses it, so preflight must too,
	or it teaches the human that a path is fine and lets core contradict it
	after the message is written."""
	import os
	state, store, root = _at_the_path_field(env)
	target = os.path.join(root["path"], "real.md")
	with open(target, "wb") as handle:
		handle.write(b"real\n")
	os.symlink(target, os.path.join(root["path"], "link.md"))
	assert os.path.realpath(os.path.join(root["path"], "link.md")) == target, \
		"this fixture is not the in-root case the pin is about"
	_refuses(state, store, "link.md", "symlink")


def test_an_intermediate_symlink_is_refused_too(env):
	"""Same rule one component up: core walks directories with `O_NOFOLLOW`."""
	import os
	state, store, root = _at_the_path_field(env)
	real_dir = os.path.join(root["path"], "realdir")
	os.makedirs(real_dir, exist_ok=True)
	with open(os.path.join(real_dir, "file.md"), "wb") as handle:
		handle.write(b"real\n")
	os.symlink(real_dir, os.path.join(root["path"], "linkdir"))
	_refuses(state, store, "linkdir/file.md", "symlink")


def test_an_unreadable_regular_file_is_refused(env):
	"""Named in the contract and absent from the first handoff, which claimed
	it. It exists, it is regular, and it still cannot be attached."""
	import os
	state, store, root = _at_the_path_field(env)
	target = os.path.join(root["path"], "secret.md")
	with open(target, "wb") as handle:
		handle.write(b"secret\n")
	os.chmod(target, 0)
	if os.access(target, os.R_OK):
		pytest.skip("running as a user that ignores file modes")
	try:
		_refuses(state, store, "secret.md", "cannot be read")
	finally:
		os.chmod(target, 0o600)


def test_a_special_file_is_refused(env):
	"""The contract names directories AND special files; only the directory
	case was pinned."""
	import os
	state, store, root = _at_the_path_field(env)
	fifo = os.path.join(root["path"], "pipe")
	try:
		os.mkfifo(fifo)
	except (AttributeError, OSError):
		pytest.skip("this platform cannot create a fifo here")
	_refuses(state, store, "pipe", "not a regular file")


def test_a_colon_in_a_filename_is_a_filename(env):
	"""R4. `notes:2026.md` is a legal name and core accepts it. Treating every
	colon as Baton serialization refused a file the authority allows -- and
	the old check asked the filesystem about the process CWD, so whether it
	refused depended on where the console happened to be started."""
	import os
	state, store, root = _at_the_path_field(env)
	with open(os.path.join(root["path"], "notes:2026.md"), "wb") as handle:
		handle.write(b"notes\n")
	state.compose["attach_path"] = "notes:2026.md"
	assert state.attachment_error() is None, state.attachment_error()
	assert state.attachment_locator() == f"{root['root_id']}:notes:2026.md"


def test_the_locator_form_is_still_diagnosed_when_it_names_a_real_root(env):
	"""The other side of R4: someone typing what they saw in a CLI command
	should be told what the field is for."""
	state, store, root = _at_the_path_field(env)
	_refuses(state, store, f"{root['root_id']}:EVIDENCE.md", "not root:path")


def test_a_path_is_attached_exactly_as_typed(env):
	"""R5. `.strip()` meant a draft displaying ` report.md ` could publish
	`report.md` -- a DIFFERENT file from the one on screen. The path is the
	human's; only the picker-owned root id is normalised."""
	import os
	state, store, root = _at_the_path_field(env)
	with open(os.path.join(root["path"], "report.md"), "wb") as handle:
		handle.write(b"report\n")
	state.compose["attach_path"] = " report.md"
	assert state.attachment_error(), "whitespace was silently accepted"
	assert "whitespace" in state.attachment_error()
	assert state.compose["attach_path"] == " report.md", "the path was rewritten"
	state.compose["attach_path"] = "report.md"
	assert state.attachment_error() is None
	assert state.attachment_locator() == f"{root['root_id']}:report.md"


# -- TRIAL: the status column answers what the READER owes ----------------

def _row_for(state, subject, columns=100, lines=24):
	from baton_tui.render import DIVIDER
	screen = render(state, columns, lines)
	rule = [i for i, line in enumerate(screen)
	        if "DETAIL " in line and DIVIDER in line][0]
	rows = [line for line in screen[1:rule] if subject in line]
	assert rows, f"{subject!r} is not on the list: {screen[1:rule]}"
	return rows[0]


def _glyph_of(state, subject):
	"""The one status cell, taken from the DRAWN row.

	Read off the screen rather than from `_status_glyph`, because the ruling
	is about what the human sees and a helper agreeing with itself proves
	nothing about which branch the row actually took."""
	row = _row_for(state, subject)
	return row[1]                            # marker, then the status column


def test_an_unopened_message_says_someone_is_waiting(env):
	from baton_tui.render import UNOPENED
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Fresh", body=b"x\n")
	state = _ready(store)
	assert _glyph_of(state, "Fresh") == UNOPENED
	assert state.unresolved_count() == 0, "nothing is owed until it is claimed"


def test_opening_it_says_it_is_mine_and_still_owed(env):
	from baton_tui.render import OPENED
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Mine", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	assert _glyph_of(state, "Mine") == OPENED
	assert state.unresolved_count() == 1, "the obligation is not counted"


def test_replying_says_i_answered_and_clears_the_obligation(env):
	from baton_tui.render import COMPLETED
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Asked", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	state.draft = "answered"
	state.send_reply(store)
	state.refresh(store)
	assert _glyph_of(state, "Asked") == COMPLETED
	assert state.unresolved_count() == 0, "the obligation outlived the reply"


def test_closing_reads_the_same_as_replying_and_the_detail_still_distinguishes(env):
	"""SUPERSEDED: this required `C`, a DIFFERENT mark, on the grounds that
	replying and closing are not the same act. They are not — but the question
	the LIST answers is whether anything is still owed, and the answer is the
	same either way. Ruled: one terminal mark.

	Which act it was must still be recoverable, and it is: the detail pane
	carries the exact state and outcome. That half is asserted here too,
	because collapsing the glyph is only safe while the fact survives
	somewhere."""
	from baton_tui.render import COMPLETED
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Shut", body=b"x\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Answered", body=b"?\n")
	state = _ready(store)
	# The row by NAME, not whichever is newest: a second message was added so
	# the detail assertion below has something to be about, and it would
	# otherwise be the one that got closed.
	state.cursor = [i for i, r in enumerate(state.rows)
	                if r.get("subject") == "Shut"][0]
	state.select_row(store)
	state.close_selected(store, outcome="noted")
	state.refresh(store)
	assert _glyph_of(state, "Shut") == COMPLETED, "a closed row is not marked done"
	assert state.unresolved_count() == 0

	# The distinction lives in the DETAIL, where someone who needs it looks.
	state.cursor = [i for i, r in enumerate(state.rows)
	                if r.get("subject") == "Shut"][0]
	state.select_row(store)
	detail = "\n".join(render(state, 100, 24))
	assert "closed" in detail, detail


def test_a_notice_goes_unseen_to_seen_without_a_claim(env):
	from baton_tui.render import NOTICE_SEEN_MARK
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	assert _glyph_of(state, "Cast") == "!"
	before = len(store.scan("acme.implementer")["claimed"])
	_press(state, store, K.ENTER_LF)
	state.refresh(store)
	assert _glyph_of(state, "Cast") == NOTICE_SEEN_MARK
	assert len(store.scan("acme.implementer")["claimed"]) == before, \
		"seeing a broadcast created a claim"


def test_outbound_rows_still_say_what_the_other_side_did(env):
	"""The two notations answer different questions and must not converge:
	on an outbound row the human is waiting, not owing."""
	from baton_tui.render import OPENED, PICKED_UP, QUEUED, UNOPENED
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Sent out", body=b"x\n")
	state = _ready(store)
	assert _glyph_of(state, "Sent out") == QUEUED
	store.claim("acme.reviewer")
	state.refresh(store)
	assert _glyph_of(state, "Sent out") == PICKED_UP
	assert _glyph_of(state, "Sent out") not in (UNOPENED, OPENED)


def test_inbound_and_outbound_with_the_same_store_state_read_differently(env):
	"""The direction-correctness case: `pending` means "waiting for me" one
	way and "not picked up yet" the other, and one glyph for both would
	report the wrong person's obligation."""
	from baton_tui.render import COMPLETED, QUEUED, UNOPENED
	store = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q", subject="Inbound", body=b"x\n")
	out = store.send("acme.implementer", "acme.reviewer", kind="q", subject="Outbound", body=b"x\n")
	state = _ready(store)
	assert _glyph_of(state, "Inbound") == UNOPENED
	assert _glyph_of(state, "Outbound") == QUEUED

	# ...and once BOTH are answered they read the SAME glyph, because who
	# answered is the party column's job. Ruled: the terminal mark must not
	# duplicate direction.
	claim = store.claim("acme.implementer", message_id=mid)
	store.reply(claim["claim_id"], participant="acme.implementer", kind="response",
	            body=b"mine\n")
	claim = store.claim("acme.reviewer", message_id=out)
	store.reply(claim["claim_id"], participant="acme.reviewer", kind="response",
	            body=b"theirs\n")
	state.refresh(store)
	assert _glyph_of(state, "Inbound") == COMPLETED
	assert _glyph_of(state, "Outbound") == COMPLETED


def test_the_exact_protocol_state_is_still_in_the_detail(env):
	"""Simplifying the glyph must not hide the state a diagnosis needs."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Diag", body=b"x\n")
	state = _ready(store)
	state.select_row(store)
	detail = "\n".join(render(state, 100, 24))
	assert "State:" in detail and "claimed" in detail, detail


def test_every_glyph_is_one_cell_and_the_column_holds(env):
	"""Including the new ones, which are the widest characters here."""
	from baton_tui.render import (COMPLETED, DAMAGED, OPENED, PICKED_UP,
	                              QUEUED, UNOPENED)
	from baton_tui.safe_text import display_width
	for glyph in (UNOPENED, OPENED, QUEUED, PICKED_UP, COMPLETED, DAMAGED):
		assert display_width(glyph) == 1, f"{glyph!r} is not one cell"
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Aa", body=b"x\n")
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Bb", body=b"x\n")
	store.send_notice("hq.lead", kind="announcement", subject="Cc", body=b"n\n")
	state = _ready(store)
	for columns in (40, 60, 100, 200):
		rows = [_row_for(state, subject, columns) for subject in ("Aa", "Bb", "Cc")]
		starts = {row.index(subject) for row, subject in zip(rows, ("Aa", "Bb", "Cc"))}
		assert len(starts) == 1, f"{columns} columns: the subject column moved: {rows}"


def test_help_no_longer_calls_an_inbound_row_R(env):
	"""The old inbound legend must be absent, not merely joined by the new."""
	from baton_tui.keys import HELP_SECTIONS
	text = " ".join(f"{key} {label}" for _title, rows in HELP_SECTIONS
	                for key, label, *_ in rows)
	assert "claimed by you" not in text
	assert "still owed" in text and "not yet opened" in text
	# `answered by a reply` IS in help now, and is the point: it is the
	# DIRECTION-INDEPENDENT completion entry that replaced both the inbound
	# tick and the outbound `R`. What must be absent is the `R` legend.
	assert "nothing is owed" in text
	assert "R replied" not in text and "they answered it" not in text
	assert "C closed" not in text, "the C legend survives"


# -- TRIAL: `r` opens the editor, `R` is the quick subject line ------------

def test_lowercase_r_goes_straight_to_the_editor(env):
	"""Slawomir's trial finding: the reply people actually write is a body in
	their editor, and the subject-only one is rare. The easier key serves the
	common action. This REVERSES the earlier pairing."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	seeds = []
	step(state, store, ord("r"), 100, 24, edit_fn=_editor("a full answer", record=seeds))
	assert seeds, "`r` did not open the editor"
	assert state.reply_body == "a full answer"
	assert state.mode == MODE_REPLY, "the editor did not return to a draft"


def test_uppercase_R_is_the_quick_subject_line_and_opens_nothing(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	seeds = []
	step(state, store, ord("R"), 100, 24, edit_fn=_editor("never", record=seeds))
	assert not seeds, "`R` opened the editor"
	assert state.mode == MODE_REPLY
	assert state.draft == "Ask", "the subject was not seeded for editing"


def test_lowercase_r_on_a_handled_row_is_a_follow_up_in_the_editor(env):
	"""It must not reopen or alter the original disposition."""
	store = env
	state, mid = _handled_inbound(store)
	state.select_row(store)
	before = store.get_message(mid)["state"]
	seeds = []
	step(state, store, ord("r"), 100, 24, edit_fn=_editor("a follow-up", record=seeds))
	assert seeds, "`r` did not open the editor on a handled row"
	assert state.follow_up_to == mid, "the follow-up relation was lost"
	assert store.get_message(mid)["state"] == before, "the original moved"


def test_ctrl_e_still_promotes_a_quick_draft_without_losing_the_subject(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Ask", body=b"?\n")
	state = _ready(store)
	state.select_row(store)
	_press(state, store, ord("R"))
	for char in " more":
		_press(state, store, ord(char))
	typed = state.draft
	step(state, store, K.CTRL_E, 100, 24, edit_fn=_editor("the body"))
	assert state.draft == typed, "the typed subject was lost"
	assert state.reply_body == "the body"


def test_help_and_readme_carry_the_new_mapping_once(env):
	from pathlib import Path
	from baton_tui.keys import HELP_SECTIONS
	rows = [(key, label) for _title, section in HELP_SECTIONS
	        for key, label, *_ in section]
	reply_rows = [(key, label) for key, label in rows if key in ("r", "R")]
	assert len(reply_rows) == 2, reply_rows
	mapping = dict(reply_rows)
	assert "editor" in mapping["r"], mapping["r"]
	assert "subject line IS the message" in mapping["R"], mapping["R"]
	readme = Path(__file__).resolve().parent.joinpath("README.md").read_text()
	assert "`r` replies — straight into your external editor" in readme
	assert "`R` is the quick one" in readme
	# The old mapping must be ABSENT, not merely joined by the new one.
	assert "quick reply, or quick follow-up" not in " ".join(
		label for _key, label in rows)


def test_the_two_views_never_disagree_about_one_row(env):
	"""The defect this closes: SENT had its own badge table, so ONE message
	read `✓` in MESSAGES and `R` in SENT — two answers to one question, which
	is the thing the whole obligation vocabulary exists to prevent.

	Swept across every state an outbound row can be in, comparing what each
	view actually DRAWS rather than what a helper returns."""
	from baton_tui.state import VIEW_SENT
	store = env
	pick = store.send("acme.implementer", "acme.reviewer", kind="q",
	                  subject="Picked", body=b"b\n")
	done = store.send("acme.implementer", "acme.reviewer", kind="q",
	                  subject="Done", body=b"c\n")
	shut = store.send("acme.implementer", "acme.reviewer", kind="q",
	                  subject="Shut", body=b"d\n")
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="Queued", body=b"a\n")
	claim = store.claim("acme.reviewer", message_id=done)
	store.reply(claim["claim_id"], participant="acme.reviewer", kind="response", body=b"x\n")
	claim = store.claim("acme.reviewer", message_id=shut)
	store.close_claim(claim["claim_id"], participant="acme.reviewer", outcome="done")
	store.claim("acme.reviewer", message_id=pick)

	state = _ready(store)
	in_messages = {}
	for subject in ("Queued", "Picked", "Done", "Shut"):
		in_messages[subject] = _glyph_of(state, subject)
	state.select_view(VIEW_SENT)
	state.refresh(store)
	for subject, expected in in_messages.items():
		row = _row_for(state, subject)
		assert row[1] == expected, (
			f"{subject}: MESSAGES draws {expected!r}, SENT draws {row[1]!r}")
