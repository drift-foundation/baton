"""The cutover, rehearsed as a test: a fresh mailbox, initialized exactly the
way the successor cutover will initialize one, driven through the CANDIDATE
executables.

Plan step 23 requires fresh-mailbox smoke coverage before cutover. Everything
else in the packaging suite examines the candidate as an artifact — what it
contains, what it hashes to, where it installs. This asks the only question a
human actually cares about on cutover morning: after `init` and the identity
stamp, does the thing WORK.

It runs `build/bin/baton` as a subprocess rather than importing the core, so
what is exercised is the packaged executable a deployment installs — the same
bytes, entered the same way.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"tools"))

import candidate                                              # noqa: E402
import deploy                                                 # noqa: E402

PROTOCOL = 10


def _run(cli, config, *argv, expect=0):
	"""One CLI call, refusing to guess what a non-zero exit meant."""
	proc = subprocess.run([sys.executable, str(cli), "--config", str(config),
	                       *argv],
	                      capture_output=True, text=True, timeout=120)
	assert proc.returncode == expect, \
		f"{argv} exited {proc.returncode}: {proc.stdout}{proc.stderr}"
	return proc


def _json(proc):
	return json.loads(proc.stdout)


@pytest.fixture
def fresh(tmp_path):
	"""A mailbox created by the CUTOVER SEQUENCE, not by a test helper.

	Config placed, `init` run by the packaged CLI, identity stamped by
	`deploy mailbox-identity`. If the documented sequence stops working, this
	fixture stops working, which is the point of building it this way.
	"""
	cli = candidate.require().cli
	home = tmp_path / "mailbox" / f"v{PROTOCOL}"
	(home / "projections" / "human.operator").mkdir(parents=True)
	config = home / "baton.json"
	config.write_text(json.dumps({
		"config_version": 1, "protocol_version": PROTOCOL, "generation": 1,
		"mailbox": {"name": "fresh-smoke"},
		"participants": {
			"team.reviewer": {}, "team.implementer": {},
			"other.reviewer": {},
			"human.operator": {"capabilities": ["recovery", "config"],
			                   "projection_dir": str(home / "projections"
			                                         / "human.operator")},
		},
		"roots": {}, "retention_days": 90,
	}, indent=2) + "\n")

	assert _json(_run(cli, config, "init"))["initialized"] is True
	deploy.mailbox_identity(str(home), protocol=PROTOCOL)
	return cli, config, home


def test_the_cutover_sequence_produces_a_usable_mailbox(fresh):
	"""Step 0. The identity is what the sequence claims it is, and the
	authority answers for itself."""
	cli, config, home = fresh

	identity = json.loads((home / "MAILBOX.json").read_text())
	assert identity == {"format": "baton.mailbox", "format_version": 1,
	                    "namespace": f"v{PROTOCOL}",
	                    "protocol_version": PROTOCOL}
	# Written read-only: a compatibility claim anybody can edit in place is
	# not a claim.
	assert not os.access(home / "MAILBOX.json", os.W_OK)

	report = _json(_run(cli, config, "doctor"))
	assert report["problems"] == [], report
	assert _json(_run(cli, config, "scan",
	                  "--participant", "team.implementer")) == \
		{"claimed": [], "damaged": [], "pending": []}


def test_a_directed_message_completes_its_whole_lifecycle(fresh):
	"""Primary workflow one: send, scan, claim, reply, and the sender sees the
	answer. A mailbox that accepts a message and cannot finish it is worse
	than one that refuses."""
	cli, config, _home = fresh

	sent = _json(_run(cli, config, "send",
	                  "--participant", "team.reviewer",
	                  "--to", "team.implementer", "--kind", "review",
	                  "--tweet", "smoke: please look at this"))
	pending = _json(_run(cli, config, "scan",
	                     "--participant", "team.implementer"))["pending"]
	assert [row["id"] for row in pending] == [sent["message_id"]]
	assert pending[0]["subject"] == "smoke: please look at this"

	claimed = _json(_run(cli, config, "claim",
	                     "--participant", "team.implementer",
	                     "--message-id", sent["message_id"]))
	assert claimed["message"]["state"] == "claimed"

	answered = _json(_run(cli, config, "reply",
	                      "--participant", "team.implementer",
	                      "--kind", "result", "--outcome", "completed",
	                      "--tweet", "smoke: done",
	                      claimed["claim"]["claim_id"]))
	assert answered["outcome"] == "completed"

	# The obligation is discharged on one side and delivered on the other.
	assert _json(_run(cli, config, "scan",
	                  "--participant", "team.implementer"))["claimed"] == []
	back = _json(_run(cli, config, "scan",
	                  "--participant", "team.reviewer"))["pending"]
	assert [row["id"] for row in back] == [answered["response_message_id"]]


def test_a_scoped_broadcast_reaches_its_team_and_nobody_else(fresh):
	"""Primary workflow two, and the scenario `finding-tui-sent-broadcast-
	missing` was opened about: publish to a scope, the right people receive
	it, the receipt is recorded, and the SENDER can see what they sent."""
	cli, config, home = fresh

	published = _json(_run(cli, config, "send-notice",
	                       "--participant", "human.operator",
	                       "--kind", "announcement",
	                       "--scope", "team.*",
	                       "--subject", "smoke: scoped broadcast",
	                       "--part", "source=" + str(home / "baton.json")
	                                 + "&type=application/json"))
	notice_id = published["notice_id"]

	dumped = json.loads(_run(cli, config, "dump").stdout)
	audience = {row["participant"] for row in dumped["notice_audience"]
	            if row["notice_id"] == notice_id}
	assert audience == {"team.reviewer", "team.implementer"}, audience
	assert "other.reviewer" not in audience
	# The author is not in a scope they do not belong to, and the notice is
	# not silently addressed to everyone.
	assert "human.operator" not in audience

	seen = _json(_run(cli, config, "see", "--participant", "team.reviewer"))
	assert [row["id"] for row in seen["notices"]] == [notice_id]
	assert seen["notices"][0]["selector"] == "team.*"

	# THE RECEIPT IS RECORDED against the notice, which is what the sender's
	# Sent view counts. The Sent VIEW itself is the console's, and is covered
	# against a fresh mailbox by
	# `tests/tui/test_tui_pty.py::test_the_packaged_console_publishes_and_sees_it_on_a_fresh_mailbox`
	# — this file drives the CLI, which has no such view to assert about.
	receipts = [row for row in json.loads(_run(cli, config, "dump").stdout)
	            ["notice_seen"] if row["notice_id"] == notice_id]
	assert [row["participant"] for row in receipts] == ["team.reviewer"]
	rows = json.loads(_run(cli, config, "dump").stdout)["notices"]
	assert [row["subject"] for row in rows] == ["smoke: scoped broadcast"]
	assert rows[0]["from_participant"] == "human.operator"


def test_the_identity_refuses_a_client_that_cannot_speak_this_mailbox(fresh):
	"""The reason the stamp exists. A wrong-generation client must refuse
	BEFORE it touches the authority, not discover it half-way through."""
	cli, config, home = fresh

	identity = home / "MAILBOX.json"
	identity.chmod(0o644)
	identity.write_text(json.dumps({"format": "baton.mailbox",
	                                "format_version": 1,
	                                "protocol_version": PROTOCOL + 1,
	                                "namespace": f"v{PROTOCOL + 1}"}))
	proc = _run(cli, config, "scan", "--participant", "team.reviewer",
	            expect=4)
	assert f"protocol {PROTOCOL + 1}" in proc.stderr, proc.stderr

	# ...and nothing was written while refusing.
	identity.write_text(json.dumps({"format": "baton.mailbox",
	                                "format_version": 1,
	                                "protocol_version": PROTOCOL,
	                                "namespace": f"v{PROTOCOL}"}))
	assert _json(_run(cli, config, "scan",
	                  "--participant", "team.reviewer")) == \
		{"claimed": [], "damaged": [], "pending": []}


def test_a_malformed_identity_is_refused_rather_than_ignored(fresh):
	"""Absence is accepted; a broken claim is not. The failure mode this
	guards is a corrupted document quietly becoming 'no document'."""
	cli, config, home = fresh

	identity = home / "MAILBOX.json"
	identity.chmod(0o644)
	identity.write_text('{"format": "baton.mailbox", "format_version": 1, '
	                    '"protocol_version": 10, "protocol_version": 10, '
	                    '"namespace": "v10"}')
	# EXIT 6, not 4, and the difference is the point: 4 says "I cannot speak
	# this mailbox's generation", 6 says "this document is not usable". A
	# duplicate key is the second — the values agree here, and it is still
	# refused, because a document that says a thing twice is not a document
	# whose meaning anyone should be resolving by position.
	proc = _run(cli, config, "scan", "--participant", "team.reviewer",
	            expect=6)
	assert "duplicate object key" in proc.stderr, proc.stderr

	identity.unlink()
	assert _json(_run(cli, config, "scan",
	                  "--participant", "team.reviewer")) == \
		{"claimed": [], "damaged": [], "pending": []}, \
		"a mailbox with no identity must still open"


# -- the reviewed proposal (R38) — RETIRED 2026-08-14 -------------------------
#
# Two tests here exercised the exact `proposed-baton.json` awaiting the v10
# cutover: internal coherence, and an end-to-end init/traffic run of the very
# file a human would copy into place. The cutover happened on 2026-08-14 —
# that file WAS copied to /home/sl/baton/mailbox/v10/baton.json, initialized
# by the 10.2.0 binary, and proven with directed and broadcast round trips on
# the live authority — and commit fb9420a then dropped the work folder that
# held the proposal. The tests' subject no longer exists because it was
# consumed by the act they guarded. Retired rather than repointed: a test
# suite must not read live production configuration, and a copied fixture
# would be exactly the "resembles it" lookalike R38 forbade.
