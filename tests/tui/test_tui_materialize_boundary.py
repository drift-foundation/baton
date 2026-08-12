"""`m` refuses unread content and nothing else.

Slawomir hit "materialize needs a message you hold the claim for" while looking
at a part he had every right to read. The rule was not wrong, it was
over-applied: it required an ACTIVE claim, which ends the moment you reply or
close, and which never exists for a message you sent or a notice you have seen.
The agent CLI could save all three; the human console could not.

What survives is the preview boundary, and only it — an unclaimed pending
message must not become bytes on disk, because writing them is reading them in
the most durable form there is.
"""

from __future__ import annotations

import json
import pathlib

import pytest

import baton_core as core
from baton_tui.render import layout_for
from baton_tui.state import InboxState, VIEW_SENT


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	proj = home / "proj"
	proj.mkdir()
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
			"mailbox": {"name": "mat"},
			"participants": {"acme.reviewer": {}, "acme.outsider": {},
			                 "acme.implementer": {"projection_dir": str(proj)}},
			"roots": {}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path, proj


@pytest.fixture
def env(tmp_path):
	path, proj = _instance(tmp_path)
	with core.open_instance(path) as store:
		yield store, proj


def _ready(store, participant="acme.implementer"):
	state = InboxState(participant)
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	# What the console does on selection. Previewing reads headers only and
	# claims nothing; without it there is no selected row for `m` to act on.
	state.preview(store)
	return state


def _select(state, subject):
	for index, row in enumerate(state.view_rows):
		if row.get("subject") == subject:
			state.cursor = index if state.view != VIEW_SENT else state.cursor
			if state.view == VIEW_SENT:
				state.sent_cursor = index
			return row
	raise AssertionError(f"no row titled {subject!r}")


def test_an_unclaimed_pending_message_is_still_refused(env):
	"""The preview boundary, which is the whole point of the rule. It must
	survive the fix that relaxed everything around it."""
	store, proj = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Unopened", body=b"secret bytes\n")
	state = _ready(store)
	assert state.materialize_selected_part(store, target_dir=str(proj)) is None
	assert list(proj.iterdir()) == [], "content reached disk without a claim"
	assert "unopened" in state.status.lower()
	# And the message it gives names the action that helps, rather than a rule
	# about claims the human cannot act on.
	assert "Enter" in state.status


def test_an_answered_message_can_be_saved(env):
	"""The defect Slawomir hit: answering a message ended the claim, and with
	it the ability to save what he had just read."""
	store, proj = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Answered", body=b"the body he wanted\n")
	state = _ready(store)
	state.open_selected(store)
	claim_id = state.opened["claim_id"]
	store.close_claim(claim_id, participant="acme.implementer", outcome="done")
	state.refresh(store)          # the action target is dropped here
	assert state.opened is None, "this fixture did not reach the reported state"

	# Enter on the answered row, which is what a human does to read it back.
	# This loads the content through the authorized path and claims nothing.
	state.open_selected(store)
	assert "received" in state.detail
	written = state.materialize_selected_part(store, target_dir=str(proj))
	assert written is not None, state.status
	assert pathlib.Path(written).read_bytes() == b"the body he wanted\n"
	assert mid in written


def test_a_sent_message_can_be_saved(env):
	"""No claim exists and none ever will: the participant wrote it."""
	store, proj = env
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="Mine to keep", body=b"what I sent\n")
	state = _ready(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	_select(state, "Mine to keep")
	state.open_selected(store)

	written = state.materialize_selected_part(store, target_dir=str(proj))
	assert written is not None, state.status
	assert pathlib.Path(written).read_bytes() == b"what I sent\n"


def test_a_seen_notice_can_be_saved_and_an_unseen_one_cannot(env):
	"""Ruled: anything viewable in full must be saveable, seen notices
	included.

	`see` remains the only way to RECEIVE a notice, so an unseen one has no
	readable body — and that refusal comes from the core's own authorization,
	not from a second rule invented in the console."""
	store, proj = env
	store.send_notice("acme.reviewer", kind="ann", subject="Broadcast",
	                  body=b"the announcement\n")
	state = _ready(store)
	_select(state, "Broadcast")

	notice_id = next(n["id"] for n in store.list_notice_activity("acme.implementer")
	                 if n.get("subject") == "Broadcast")
	with pytest.raises(core.BatonError):
		store.authorize_read("notice", notice_id, "acme.implementer")

	state.open_selected(store)          # Enter marks it seen
	state.refresh(store)
	written = state.materialize_selected_part(store, target_dir=str(proj))
	assert written is not None, state.status
	assert pathlib.Path(written).read_bytes() == b"the announcement\n"
	assert notice_id in written, "the projection names the notice it came from"


def test_a_transient_message_is_still_refused(env, tmp_path):
	"""Retention survives the widening. The sender chose transient; a durable
	copy of it would defeat that choice, and a save feature reached by a
	keystroke is the worst place for a contract to be quietly undone."""
	store, proj = env
	# SENT by this participant, so the authorized path is what runs: an
	# answered transient message has no content left to select by the time the
	# claim resolves, which would test nothing.
	mid = store.send("acme.implementer", "acme.reviewer", kind="q",
	                 subject="Fleeting", body=b"do not keep me\n",
	                 retention="transient")
	state = _ready(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	_select(state, "Fleeting")
	state.open_selected(store)
	assert state.selected_part is not None, "this fixture has nothing to save"

	assert state.materialize_selected_part(store, target_dir=str(proj)) is None
	assert "transient" in state.status, state.status
	assert list(proj.iterdir()) == [], str(mid)


def test_authorization_is_the_cores_not_the_consoles(env, tmp_path):
	"""The console decides which id to ask about; the core decides whether the
	participant may read it. A front end that answered this itself would be a
	boundary one refactor from not existing."""
	store, _proj = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Not for the reviewer", body=b"private\n")

	mid = next(r["id"] for r in store.list_messages("acme.implementer")
	           if r.get("subject") == "Not for the reviewer")

	# NEITHER sender nor audience. The reviewer does not qualify — it SENT this
	# message, so the core authorizes it, and my first version of this test
	# used it as the intruder and proved nothing.
	with pytest.raises(core.BatonError):
		store.authorize_read("message", mid, "acme.outsider")
	# The sender and the recipient are both authorized, which is what makes the
	# refusal above a boundary rather than a blanket denial.
	assert store.authorize_read("message", mid, "acme.reviewer") is not None
	assert store.authorize_read("message", mid, "acme.implementer") is not None


def test_saving_writes_nothing_to_the_authority(env, tmp_path):
	"""Reading back is not an event: no claim, no receipt, no transition."""
	store, _proj = env
	path = None
	for candidate in tmp_path.rglob("baton.json"):
		path = str(candidate)
	assert path, "the fixture moved; this test cannot find the config"

	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Answered", body=b"body\n")
	state = _ready(store)
	state.open_selected(store)
	store.close_claim(state.opened["claim_id"], participant="acme.implementer",
	                  outcome="done")
	state.refresh(store)
	state.open_selected(store)

	before = core.dump(path)
	assert state.materialize_selected_part(store, target_dir=str(tmp_path)) is not None
	assert core.dump(path) == before
