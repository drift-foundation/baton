"""W103: the active public documentation stays v11-only.

The cutover's acceptance items were verified once by hand, which does
not protect a release from regression — a later edit can quietly
reintroduce a retired launch path or a link to a document that is not
v11 yet. These are the standing checks.

Explicitly historical evidence is excluded by design: release records
and permanent dossiers describe the release or decision they were
written for and are never rewritten to satisfy a scan.
"""

from __future__ import annotations

import os
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]

# The documents that give CURRENT guidance. Release notes, dossiers, and
# review journals are history and are deliberately absent.
ACTIVE_DOCS = (
	"README.md",
	"docs/BATON-WORK.md",
	"docs/BATON-SETUP.md",
	"docs/AGENTS-MAILBOX-PROTO.md",
)

# Retired protocol-10 launch surfaces. A hit means active guidance is
# telling somebody to run the retired product.
RETIRED = (
	"baton-tui",
	"baton-codex-monitor",
	"codex-baton-stack",
	"send-notice",
	"just codex-baton",
)


def _text(relative):
	return (REPO / relative).read_text(encoding="utf-8")


def test_active_documents_prescribe_no_retired_launch_path():
	for relative in ACTIVE_DOCS:
		body = _text(relative)
		for token in RETIRED:
			assert token not in body, \
				f"{relative} still prescribes the retired {token!r}"


def test_active_documents_do_not_teach_the_retired_mailbox():
	"""`send`/`reply`/notice vocabulary may be NAMED as retired; it may
	not be taught. The distinction is the sentence that says so."""
	for relative in ACTIVE_DOCS:
		lines = _text(relative).splitlines()
		for number, line in enumerate(lines, 1):
			if not re.search(r"`(send|reply)`", line):
				continue
			# the disclaimer is a SENTENCE, and prose wraps: look at the
			# surrounding window rather than the one line the match
			# happened to land on
			window = " ".join(lines[max(0, number - 3):number + 2])
			assert re.search(r"retired|not a fallback|[Pp]rotocol 10",
			                 window), \
				f"{relative}:{number} teaches retired mailbox verbs: {line!r}"


def test_every_repository_link_in_the_readme_resolves():
	body = _text("README.md")
	for link in re.findall(r"\]\(([^)]+)\)", body):
		if link.startswith(("http://", "https://", "#", "mailto:")):
			continue
		target = REPO / link
		assert target.exists(), f"README links a missing path: {link}"


def test_the_readme_does_not_send_readers_into_a_non_v11_guide():
	"""EFFECTIVE-BATON still teaches the protocol-10 operating model
	until its own Work lands. The public entry point must not route a
	reader there while that is true — and this check RETIRES ITSELF as
	soon as it is rewritten, rather than forbidding the link forever."""
	guide = REPO / "docs" / "EFFECTIVE-BATON.md"
	if not guide.exists():
		return
	body = guide.read_text(encoding="utf-8")
	still_v10 = any(token in body for token in
	                ("send-notice", "baton-tui", "mailbox"))
	if still_v10:
		assert "docs/EFFECTIVE-BATON.md)" not in _text("README.md"), \
			"the README links EFFECTIVE-BATON while it is still v10"


def test_the_agent_policy_states_both_halves_of_the_wait_contract():
	"""W103 R3: an agent following the shipped policy must not walk past
	Work it has already claimed — the exact failure a restart produces."""
	body = _text("docs/AGENTS-MAILBOX-PROTO.md")
	assert "UNCLAIMED Work" in body
	assert "ALREADY CLAIMED" in body, \
		"the policy omits the claimant-continuation half of `wait`"
	assert "restart" in body


def test_the_agent_policy_names_protocol_eleven_and_the_stable_path():
	body = _text("docs/AGENTS-MAILBOX-PROTO.md")
	assert "protocol 11" in body
	assert "stable on purpose" in body, \
		"the policy does not explain why the v10 filename is kept"
