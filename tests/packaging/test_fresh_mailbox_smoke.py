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


# -- the REVIEWED proposal, not a fixture that resembles it -------------------

PROPOSAL = pathlib.Path(__file__).resolve().parents[2] / "work" \
	/ "finding-product-version-manifest" / "findings" \
	/ "finding-generation-layout-rollout" / "proposed-baton.json"


def test_the_reviewed_config_proposal_is_internally_coherent():
	"""R38. The file a human will copy into place, checked as the artifact it
	is rather than as prose in a runbook.

	The defect this exists for was real: the proposal carried a
	`projection_dir` under `mailbox/legacy/`, the retired authority's path,
	while the successor mailbox is `mailbox/v10/`. A config is not reviewed by
	being read — every absolute path in it has to agree with the cutover it
	belongs to."""
	document = json.loads(PROPOSAL.read_text())
	assert document["protocol_version"] == PROTOCOL
	# A FRESH authority: generation 1, because a fresh mailbox has accepted
	# exactly one config.
	assert document["generation"] == 1
	home = f"/home/sl/baton/mailbox/v{PROTOCOL}"
	for address, entry in document["participants"].items():
		projection = entry.get("projection_dir")
		if projection is None:
			continue
		assert projection.startswith(home + "/"), \
			f"{address} projects into {projection}, not the successor mailbox"
		assert "legacy" not in projection, \
			f"{address} still projects into the retired authority: {projection}"
	# A distinguishing name, so a stray process pointed at the retired file
	# cannot be confused about which authority it is on.
	assert document["mailbox"]["name"] != "drift-suite-local"


def test_the_reviewed_proposal_initializes_and_carries_traffic(tmp_path):
	"""R38, the half that reading cannot establish: the EXACT proposal is
	initialized by the candidate CLI, stamped, and then used.

	Only the absolute paths that must move with the mailbox are rewritten —
	`projection_dir`, which is per-machine — and the test asserts it rewrote
	exactly one thing, so a proposal that silently depended on some other
	absolute path could not pass here by being quietly patched."""
	cli = candidate.require().cli
	document = json.loads(PROPOSAL.read_text())
	home = tmp_path / "mailbox" / f"v{PROTOCOL}"
	(home / "projections" / "human.slawomir").mkdir(parents=True)

	rewritten = 0
	for entry in document["participants"].values():
		if "projection_dir" in entry:
			entry["projection_dir"] = str(home / "projections" / "human.slawomir")
			rewritten += 1
	assert rewritten == 1, f"{rewritten} projection dirs, not one"
	# Roots are repository paths this machine may not have; the proposal keeps
	# them for production and they are not what this test is about.
	document["roots"] = {}
	config = home / "baton.json"
	config.write_text(json.dumps(document, indent=2) + "\n")

	assert _json(_run(cli, config, "init"))["initialized"] is True
	deploy.mailbox_identity(str(home), protocol=PROTOCOL)
	assert json.loads((home / "MAILBOX.json").read_text())["namespace"] == \
		f"v{PROTOCOL}"

	report = _json(_run(cli, config, "doctor"))
	assert report["problems"] == [], report

	# The two participants this coordination actually runs on, end to end.
	sent = _json(_run(cli, config, "send", "--participant", "baton.reviewer",
	                  "--to", "baton.implementer", "--kind", "review",
	                  "--tweet", "proposal smoke"))
	pending = _json(_run(cli, config, "scan",
	                     "--participant", "baton.implementer"))["pending"]
	assert [row["id"] for row in pending] == [sent["message_id"]]

	# ...and a scoped broadcast over the real participant list.
	notice = _json(_run(cli, config, "send-notice",
	                    "--participant", "human.slawomir",
	                    "--kind", "announcement", "--scope", "baton.*",
	                    "--subject", "proposal broadcast",
	                    "--part", "source=" + str(config)
	                              + "&type=application/json"))
	audience = {row["participant"] for row
	            in json.loads(_run(cli, config, "dump").stdout)["notice_audience"]
	            if row["notice_id"] == notice["notice_id"]}
	assert audience == {"baton.reviewer", "baton.implementer"}, audience
