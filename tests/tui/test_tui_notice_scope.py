"""`N` asks who a notice is for.

Slawomir: "right now it's impossible to address the team (`lang.*`) when
creating a notice." The authority and the agent CLI had scoped notices all
along; the console never offered the choice, so every console-authored
broadcast went to everyone — not because anyone chose that, but because nobody
was asked.

Ruled shape: an editable, filtering combobox over `*` plus the configured team
scopes. Typing filters; Tab completes; Enter submits whatever is typed, so a
complete `web.*` works with no suggestion chosen. The console never expands or
authorizes an audience — the core does that in the publication transaction, and
a refusal keeps the draft rather than quietly falling back to everyone.

DRIVEN THROUGH THE KEYS. A model that can hold a scope while the key that
reaches it refuses is a model that changed nothing, which is a mistake this
console has already shipped twice.
"""

from __future__ import annotations

import json

import pytest

import baton_core as core
from baton_tui import keys as K
from baton_tui.driver import step
from baton_tui.render import layout_for, render
from baton_tui.state import (MODE_BROWSE, MODE_NOTICE, MODE_PICK_SCOPE,
                             SCOPE_GLOBAL, InboxState, team_scopes)


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
			"mailbox": {"name": "scope"},
			"participants": {
				"web.lead": {}, "web.dev": {},
				"lang.lead": {}, "lang.deep.owner": {},
				"acme.implementer": {}, "hq.lead": {},
			},
			"roots": {}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path


@pytest.fixture
def env(tmp_path):
	path = _instance(tmp_path)
	with core.open_instance(path) as store:
		yield store, path


def _ready(store, participant="acme.implementer"):
	state = InboxState(participant)
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	state.preview(store)
	return state


def _press(state, store, *keys):
	for key in keys:
		step(state, store, key, 100, 24)
	return state


def _type(state, store, text):
	for char in text:
		_press(state, store, ord(char))


def _screen(state, columns=100, lines=24):
	return "\n".join(render(state, columns, lines))


# -- the suggestion rule, without a screen ---------------------------------

def test_team_scopes_are_proper_prefixes_only():
	"""Every team an address implies, and never the address itself: `a.b.c.*`
	would be an exact participant wearing a wildcard, and the ruling is that
	notices are team-oriented."""
	assert team_scopes(["web.lead", "web.dev", "lang.deep.owner"]) == [
		"lang.*", "lang.deep.*", "web.*"]
	# Deduplicated, sorted, and deterministic across orderings.
	assert team_scopes(["b.x", "a.y", "b.z"]) == team_scopes(["b.z", "a.y", "b.x"])
	# A single-segment address implies no team at all.
	assert team_scopes(["solo"]) == []
	assert team_scopes([None, 3]) == []


# -- the control ------------------------------------------------------------

def test_N_asks_who_before_composing(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	assert state.mode == MODE_PICK_SCOPE, "N entered the composer without asking"
	screen = _screen(state)
	assert "Who is this notice for?" in screen
	assert SCOPE_GLOBAL in screen


def test_the_options_are_global_and_teams_never_participants(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	options = state.scope_matches_query()
	assert options[0] == SCOPE_GLOBAL
	assert set(options[1:]) == {"acme.*", "hq.*", "lang.*", "lang.deep.*", "web.*"}
	# EXACT PARTICIPANTS NEVER APPEAR. Ruled, and the reason the control is not
	# the recipient picker with a flag.
	screen = _screen(state)
	for address in ("web.lead", "web.dev", "lang.lead", "hq.lead"):
		assert address not in screen, address


def test_typing_filters_the_suggestions(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "lang")
	assert state.scope_matches_query() == ["lang.*", "lang.deep.*"]
	screen = _screen(state)
	assert "lang.*" in screen and "web.*" not in screen
	# Backspacing widens it again.
	_press(state, store, K.BACKSPACE_KEY)
	assert "lang.*" in state.scope_matches_query()
	assert "lan" == state.scope_query


def test_tab_completes_through_the_matches(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "lang")
	_press(state, store, K.TAB)
	assert state.scope_query == "lang.*"
	_press(state, store, K.TAB)
	assert state.scope_query == "lang.deep.*", "Tab must reach the second match"
	_press(state, store, K.TAB)
	assert state.scope_query == "lang.*", "and cycle rather than stop"


def test_a_typed_scope_submits_without_choosing_a_suggestion(env):
	"""The ruling's sharpest clause: a complete valid scope works even when no
	suggestion was precomputed for it."""
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "brandnew.*")
	assert state.scope_matches_query() == [], "this fixture had a suggestion after all"
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_NOTICE
	assert state.notice_scope == "brandnew.*"


def test_an_incomplete_scope_is_refused_and_keeps_the_typed_text(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "lang")
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_PICK_SCOPE, "an incomplete scope opened the composer"
	assert state.scope_query == "lang", "the refusal discarded what was typed"
	assert "lang" in state.status


def test_enter_on_an_empty_query_means_everyone(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"), K.ENTER_LF)
	assert state.mode == MODE_NOTICE
	assert state.notice_scope == SCOPE_GLOBAL


def test_escape_cancels_and_composes_nothing(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "web")
	_press(state, store, K.ESC)
	assert state.mode == MODE_BROWSE
	assert state.notice_scope is None
	assert state.compose.get("subject", "") == ""


# -- what actually gets published ------------------------------------------

def _publish(state, store, subject):
	_type(state, store, subject)
	_press(state, store, K.ENTER_LF, ord("y"))


def test_a_scoped_notice_reaches_only_that_team(env):
	"""Acceptance 2, measured at the authority: the audience is the core's
	expansion of the scope, and an unrelated team is not in it."""
	store, path = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_publish(state, store, "for the web team")

	notices = core.dump(path)["notices"]
	assert len(notices) == 1, state.status
	assert notices[0]["subject"] == "for the web team"
	audience = {row["participant"] for row in core.dump(path)["notice_audience"]
	            if row["notice_id"] == notices[0]["id"]}
	assert audience == {"web.lead", "web.dev"}, audience


def test_a_global_notice_still_reaches_everyone(env):
	store, path = env
	state = _ready(store)
	_press(state, store, ord("N"), K.ENTER_LF)
	_publish(state, store, "for all of us")

	notices = core.dump(path)["notices"]
	assert len(notices) == 1, state.status
	audience = {row["participant"] for row in core.dump(path)["notice_audience"]
	            if row["notice_id"] == notices[0]["id"]}
	assert audience == {"web.lead", "web.dev", "lang.lead", "lang.deep.owner",
	                    "acme.implementer", "hq.lead"}


def test_a_deep_scope_includes_only_its_own_subtree(env):
	store, path = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "lang.deep.*")
	_press(state, store, K.ENTER_LF)
	_publish(state, store, "deep only")

	notices = core.dump(path)["notices"]
	audience = {row["participant"] for row in core.dump(path)["notice_audience"]
	            if row["notice_id"] == notices[0]["id"]}
	assert audience == {"lang.deep.owner"}, audience


# -- the audience is visible, and it survives ------------------------------

def test_the_audience_is_on_screen_while_composing_and_confirming(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_type(state, store, "a subject")
	assert "web.*" in _screen(state), "the audience vanished during composition"

	_press(state, store, K.ENTER_LF)            # arm the confirmation
	assert "Send? Y/n" in state.status
	assert "web.*" in _screen(state), "the audience vanished at confirmation"


def test_global_shows_itself_at_confirmation(env):
	"""Acceptance 3: current behaviour, but `*` must be visible before it
	publishes to everyone."""
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"), K.ENTER_LF)
	_type(state, store, "everybody")
	_press(state, store, K.ENTER_LF)
	screen = _screen(state)
	assert SCOPE_GLOBAL in screen and "everyone" in screen


def test_the_audience_survives_a_declined_confirmation(env):
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_type(state, store, "a subject")
	_press(state, store, K.ENTER_LF, ord("n"))   # arm, then decline

	assert state.mode == MODE_NOTICE
	assert state.notice_scope == "web.*"
	assert state.compose["subject"] == "a subject"
	assert "web.*" in _screen(state)


# -- nothing is written until the human says so ----------------------------

def test_opening_filtering_and_cancelling_write_nothing(env):
	"""Acceptance 5, compared against a full dump: choosing an audience is a
	local act."""
	store, path = env
	state = _ready(store)
	before = core.dump(path)

	_press(state, store, ord("N"))
	_type(state, store, "lang")
	_press(state, store, K.TAB)
	_press(state, store, K.CTRL_U)
	_press(state, store, K.ESC)
	assert core.dump(path) == before

	# And a declined confirmation publishes nothing either.
	_press(state, store, ord("N"), K.ENTER_LF)
	_type(state, store, "nearly")
	_press(state, store, K.ENTER_LF, ord("n"))
	assert core.dump(path) == before


def test_a_core_refusal_keeps_the_draft_and_never_falls_back_global(env):
	"""Acceptance 7. A scope that no longer matches anyone is the core's to
	refuse; the console must not rescue it by broadcasting to everyone."""
	store, path = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "nobody.*")
	_press(state, store, K.ENTER_LF)
	_type(state, store, "goes nowhere")
	_press(state, store, K.ENTER_LF, ord("y"))

	assert core.dump(path)["notices"] == [], "a refused scope published anyway"
	assert state.notice_scope == "nobody.*", "the audience was discarded"
	assert state.compose["subject"] == "goes nowhere", "the draft was lost"
	assert state.status, "the refusal was silent"


# -- narrow terminals -------------------------------------------------------

@pytest.mark.parametrize("columns,lines", [(100, 24), (60, 12), (44, 10)])
def test_the_picker_draws_safely_at_every_size(env, columns, lines):
	from baton_tui.safe_text import display_width
	store, _ = env
	state = _ready(store)
	layout = layout_for(columns, lines)
	if layout:
		state.set_viewport(**layout)
	_press(state, store, ord("N"))
	_type(state, store, "l")
	screen = render(state, columns, lines)
	assert len(screen) == lines
	assert all(display_width(line) <= columns for line in screen)
	# Every option offered is one the pane actually drew.
	drawn = "\n".join(screen)
	for option in state.scope_entries():
		assert option in drawn, f"{option!r} was offered but not drawn"


# -- the audience must survive being put down and picked up ----------------
#
# R1 from review, and the sharpest defect in this item: a retained `web.*`
# notice reopened with no audience at all, and `send_compose` reads no audience
# as global. Continuing yesterday's team draft would have broadcast it to the
# whole mailbox — silently, at the moment of sending, which is the worst place
# to learn it.

def _restart(state, store, projection):
	"""A NEW console over the same projection directory, as a restart is."""
	fresh = InboxState(state.participant)
	fresh.projection_dir = projection
	fresh.load_drafts()
	fresh.refresh(store)
	fresh.set_viewport(**layout_for(100, 24))
	fresh.preview(store)
	return fresh


def _draft_row(state, subject):
	for row in state.rows:
		draft = row.get("draft") or {}
		if draft.get("subject") == subject:
			return row
	raise AssertionError(f"no retained draft titled {subject!r}")


def test_a_retained_scoped_draft_survives_restart_and_sends_to_its_team(env, tmp_path):
	"""The whole point, end to end: retain, restart, reopen, SEND, and check
	the audience at the authority. A test that stopped at 'the field came back'
	would have passed with the bug three lines later."""
	store, path = env
	projection = str(tmp_path / "proj")
	(tmp_path / "proj").mkdir()

	state = _ready(store)
	state.projection_dir = projection
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_type(state, store, "kept overnight")
	_press(state, store, K.ESC)                  # Esc RETAINS
	assert state.notice_scope is None, "the audience stayed armed after Esc"

	fresh = _restart(state, store, projection)
	fresh.reopen_draft(_draft_row(fresh, "kept overnight"))
	assert fresh.notice_scope == "web.*", "the audience did not survive the restart"
	assert "web.*" in _screen(fresh), "the restored audience is not on screen"

	_press(fresh, store, K.ENTER_LF, ord("y"))
	notices = core.dump(path)["notices"]
	assert len(notices) == 1, fresh.status
	audience = {row["participant"] for row in core.dump(path)["notice_audience"]
	            if row["notice_id"] == notices[0]["id"]}
	assert audience == {"web.lead", "web.dev"}, audience


def test_a_draft_written_before_scopes_existed_reopens_as_global(env, tmp_path):
	"""Version-1 drafts predate the audience field. They were global by
	construction, so they restore as an explicit `*` — restored and shown,
	never guessed at send time."""
	store, path = env
	projection = tmp_path / "proj"
	(projection / ".baton-tui").mkdir(parents=True, mode=0o700)
	# A GENUINE version-1 file, written raw: `save` now writes version 2 and
	# refuses a notice with no audience, which is the point — this is what an
	# older console left behind, not something this one would produce.
	(projection / ".baton-tui" / "acme.implementer.json").write_text(json.dumps({
		"version": 1, "drafts": [
			{"id": "notice:old", "kind": "notice", "subject": "from before",
			 "body": "", "to": "", "attach_path": "", "answering": None,
			 "is_reply": False}]}))
	(projection / ".baton-tui" / "acme.implementer.json").chmod(0o600)
	projection = str(projection)

	fresh = _restart(_ready(store), store, projection)
	assert fresh.drafts, "the legacy draft was rejected instead of loaded"
	fresh.reopen_draft(_draft_row(fresh, "from before"))
	assert fresh.notice_scope == SCOPE_GLOBAL
	assert SCOPE_GLOBAL in _screen(fresh)

	_press(fresh, store, K.ENTER_LF, ord("y"))
	notices = core.dump(path)["notices"]
	audience = {row["participant"] for row in core.dump(path)["notice_audience"]
	            if row["notice_id"] == notices[0]["id"]}
	assert len(audience) == 6, audience


def test_a_stored_audience_that_no_longer_parses_is_not_downgraded(env, tmp_path):
	"""It reopens with the audience it claimed and the reason it is unusable.
	Silently rewriting it to `*` would turn a corrupt team notice into a
	mailbox-wide broadcast."""
	from baton_tui import drafts as draft_store
	store, _ = env
	projection = str(tmp_path / "proj")
	(tmp_path / "proj").mkdir()
	bad = {"id": "notice:bad", "kind": "notice", "subject": "broken audience",
	       "body": "", "to": "", "attach_path": "", "answering": None,
	       "is_reply": False, "notice_scope": "Not A Scope",
	       "body_requested": False}
	draft_store.save(projection, "acme.implementer", [bad])

	fresh = _restart(_ready(store), store, projection)
	fresh.reopen_draft(_draft_row(fresh, "broken audience"))
	assert fresh.notice_scope == "Not A Scope"
	assert "unusable" in fresh.status, fresh.status


def test_an_empty_stored_audience_is_refused_as_damage(tmp_path):
	"""An empty string is not "global" — it is a field that lost its value,
	and guessing which audience it meant is the guess that broadcasts a team
	message to everyone."""
	from baton_tui import drafts as draft_store
	from baton_tui.drafts import DraftError
	projection = tmp_path / "proj"
	(projection / ".baton-tui").mkdir(parents=True, mode=0o700)
	# Written RAW, because `save` validates too — the case being pinned is a
	# file that reached the disk damaged, not one this console would produce.
	(projection / ".baton-tui" / "acme.implementer.json").write_text(json.dumps({
		"version": 1, "drafts": [
			{"id": "notice:x", "kind": "notice", "subject": "s", "body": "",
			 "to": "", "attach_path": "", "answering": None,
			 "is_reply": False, "notice_scope": ""}]}))
	(projection / ".baton-tui" / "acme.implementer.json").chmod(0o600)
	with pytest.raises(DraftError) as refused:
		draft_store.load(str(projection), "acme.implementer")
	# WHICH refusal. Without this the test passed on the directory-permission
	# check instead of the audience rule, which is a green test asserting
	# nothing about the thing it is named for.
	assert "notice_scope" in str(refused.value), refused.value


def test_the_audience_survives_the_external_editor(env, tmp_path):
	"""Ruled survival case: writing the body in `$EDITOR` must not lose who
	the notice is for."""
	store, _ = env
	state = _ready(store)
	state.projection_dir = str(tmp_path)
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_type(state, store, "edited elsewhere")

	step(state, store, 5, 100, 24,               # Ctrl-E
	     edit_fn=lambda seed: ("a body written in the editor\n", ""))
	assert state.notice_scope == "web.*", "the editor round trip lost the audience"
	assert "web.*" in _screen(state)


def test_the_success_status_names_the_real_audience(env):
	"""It said "to everyone" unconditionally, which was true of every notice
	until the audience became a choice."""
	store, _ = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_publish(state, store, "scoped")
	assert "web.*" in state.status, state.status
	assert "everyone" not in state.status, state.status

	state2 = _ready(store)
	_press(state2, store, ord("N"), K.ENTER_LF)
	_publish(state2, store, "global")
	assert "everyone" in state2.status, state2.status


def test_a_sent_audience_is_not_inherited_by_the_next_notice(env):
	"""Lifecycle cleanup. An audience left armed belongs to a message that is
	already gone, and the next `N` would quietly inherit who it reached."""
	store, path = env
	state = _ready(store)
	_press(state, store, ord("N"))
	_type(state, store, "web.*")
	_press(state, store, K.ENTER_LF)
	_publish(state, store, "first")
	assert state.notice_scope is None

	_press(state, store, ord("N"))
	assert state.scope_query == "", "the picker reopened pre-filled"
	_press(state, store, K.ENTER_LF)
	_publish(state, store, "second")

	dump = core.dump(path)
	second = [n for n in dump["notices"] if n["subject"] == "second"][0]
	audience = {row["participant"] for row in dump["notice_audience"]
	            if row["notice_id"] == second["id"]}
	assert len(audience) == 6, f"the second notice inherited an audience: {audience}"


# -- cross-version safety ---------------------------------------------------
#
# R2 from review, and the reason the format version had to move: a version-1
# file carrying an extra field is still version 1 to every reader that already
# exists. The FROZEN 1.0 console reads exactly those, ignores the audience it
# has never heard of, and publishes the notice to everyone — the same
# wrong-audience outcome as the first defect, reached from the other side.

def _frozen_drafts_module():
	"""`baton_tui.drafts` exactly as it shipped in the released 1.0.0 console.

	FROM FROZEN EVIDENCE, not from the checked-in artifact. It used to be read
	out of `bin/baton-tui`, whose comment called that "the released 1.0.0
	console" -- true until the 1.1 release build replaced it, after which this
	test loaded the NEW console, found draft format 3 and asserted that 3 == 1.
	Compatibility evidence cannot live in the thing being released.

	Nor is it fetched from Git at test time: the suite has to run in an
	exported tree, a shallow clone, or a distribution with no history at all.

	`tests/tui/frozen/PROVENANCE.json` records where these bytes came from and
	their digest, and the digest is CHECKED here -- evidence nobody verifies is
	just a file somebody once copied."""
	import hashlib
	import importlib.util
	import json as _json
	import pathlib as _pathlib

	frozen = _pathlib.Path(__file__).resolve().parent / "frozen"
	record = _json.loads((frozen / "PROVENANCE.json").read_text())
	evidence = frozen / record["file"]
	source = evidence.read_bytes()
	actual = hashlib.sha256(source).hexdigest()
	assert actual == record["member_sha256"], (
		f"{evidence.name} is not the evidence PROVENANCE.json describes: "
		f"{actual} != {record['member_sha256']}")

	spec = importlib.util.spec_from_loader("frozen_drafts", loader=None)
	module = importlib.util.module_from_spec(spec)
	module.__dict__["__file__"] = "frozen:baton_tui/drafts.py"
	exec(compile(source, "frozen:baton_tui/drafts.py", "exec"), module.__dict__)
	assert module.VERSION == record["draft_format_version"], (
		"the frozen evidence does not carry the draft format it claims")
	return module


def test_the_frozen_console_refuses_a_file_this_one_writes(tmp_path):
	"""The compatibility guarantee: an older console must REFUSE the newer
	file rather than misread it. Refusing costs the human a reopen; misreading
	costs them a broadcast to everyone."""
	from baton_tui import drafts as current
	projection = str(tmp_path / "proj")
	(tmp_path / "proj").mkdir()
	current.save(projection, "acme.implementer", [
		{"id": "notice:new", "kind": "notice", "subject": "team only",
		 "body": "", "to": "", "attach_path": "", "answering": None,
		 "is_reply": False, "notice_scope": "web.*", "body_requested": False}])

	frozen = _frozen_drafts_module()
	# The 1.0 reader, still 1 however far the current console has moved.
	assert frozen.VERSION == 1, "this test is measuring the wrong console"
	with pytest.raises(frozen.DraftError) as refused:
		frozen.load(projection, "acme.implementer")
	assert "version" in str(refused.value)

	# And the current console still reads its own file, with the audience.
	kept = current.load(projection, "acme.implementer")
	assert kept[0]["notice_scope"] == "web.*"


def test_the_writer_advanced_and_still_reads_the_old_format():
	from baton_tui import drafts as current
	assert current.VERSION == 3
	assert current.READABLE == (1, 2, 3)
	# The storage layer's spelling of "everyone" must match the screen model's,
	# since the two are deliberately not imported into each other.
	assert current.GLOBAL_SCOPE == SCOPE_GLOBAL


def test_a_version_one_notice_carrying_an_audience_is_preserved(tmp_path):
	"""This console briefly wrote experimental version-1 files with an
	audience. Those keep it — preserved and validated, never downgraded."""
	from baton_tui import drafts as current
	projection = tmp_path / "proj"
	(projection / ".baton-tui").mkdir(parents=True, mode=0o700)
	target = projection / ".baton-tui" / "acme.implementer.json"
	target.write_text(json.dumps({
		"version": 1, "drafts": [
			{"id": "notice:exp", "kind": "notice", "subject": "experimental",
			 "body": "", "to": "", "attach_path": "", "answering": None,
			 "is_reply": False, "notice_scope": "lang.*"}]}))
	target.chmod(0o600)

	kept = current.load(str(projection), "acme.implementer")
	assert kept[0]["notice_scope"] == "lang.*", "an experimental audience was lost"
