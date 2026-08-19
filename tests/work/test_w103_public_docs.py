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
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from baton_work import cli as _cli                             # noqa: E402

# The documents that give CURRENT guidance. Release notes, dossiers, and
# review journals are history and are deliberately absent.
ACTIVE_DOCS = (
	"README.md",
	"docs/BATON-WORK.md",
	"docs/BATON-SETUP.md",
	"docs/AGENTS-MAILBOX-PROTO.md",
	"docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md",
	"tools/codex-event-bridge/README.md",
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


def _prose(body):
	"""The document with markdown link and image TARGETS removed.

	W29 note: this guard forbids retired launch paths, and it was
	matching bare substrings — so a screenshot named
	`assets/images/baton-tui.png` read as an instruction to run the
	retired `baton-tui` binary. A file may be named after the product
	it depicts; what must not survive is prose telling somebody to RUN
	the retired thing. Link targets are therefore not prose."""
	return re.sub(r"\]\([^)]*\)", "]()", body)


def test_active_documents_prescribe_no_retired_launch_path():
	for relative in ACTIVE_DOCS:
		body = _prose(_text(relative))
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


def test_the_readme_positions_baton_across_repositories():
	opening = " ".join(_text("README.md").split("![Baton TUI", 1)[0].split())
	assert "engineering work across repositories" in opening
	assert "teams of humans and agents" in opening
	assert "same repository" not in opening


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


def test_the_agent_policy_names_every_actionable_kind_wait_returns():
	"""The R3 defect, generalized. A policy that lists all but one of the
	kinds `wait` returns leaves an agent meeting an entry it was never
	told about — which is how the claimant-continuation half was missed
	in round one. The kinds are asked of the PROJECTION rather than
	restated here, so a fifth kind fails this test on the day it ships
	instead of on the day somebody notices the prose is short."""
	body = _text("docs/AGENTS-MAILBOX-PROTO.md")
	source = (REPO / "src" / "baton_work" / "projection.py").read_text()
	start = source.index("def participant_actions")
	# the NEXT top-level def ends the window: later projections build on
	# this one and their own row kinds are not wake kinds.
	window = source[start:start + source[start + 1:].index("\ndef ")]
	kinds = set(re.findall(r'\["kind"\] = "(\w+)"', window))
	kinds |= set(re.findall(r'"kind": "(\w+)"', window))
	# The phrase each kind is taught under. Natural prose does not have
	# to spell an internal identifier, but the MAP has to cover exactly
	# the kinds the projection emits — so a fifth kind fails here until
	# somebody writes both the phrase and the paragraph behind it.
	taught = {"work": "UNCLAIMED Work",
	          "obligation": "obligations your endpoint owes",
	          "due_trial": "due verification trials",
	          "poke": "pokes** addressed to your exact participant",
	          "runtime_refresh": "refresh request is for your adapter"}
	assert kinds == set(taught), (kinds, set(taught))
	for kind, phrase in taught.items():
		assert phrase in body, \
			f"the shipped agent policy never teaches {kind!r}"


def test_the_agent_policy_states_the_blocking_default():
	"""W103 R4 parked this while W159 was in review: documentation
	describes the CERTIFIED release. The behaviour is accepted now — the
	grammar itself says the default — so the wording returns, and this
	check ties it to the grammar rather than to a memory of the ruling."""
	spec = {key["name"]: key
	        for key in _cli.GRAMMAR["say"]["keys"]}
	assert "default true with request=" in spec["wait"]["help"], \
		"the grammar no longer defaults a directed request to blocking"
	body = _text("docs/AGENTS-MAILBOX-PROTO.md")
	assert "blocks by default" in body.lower(), \
		"the agent policy does not state the certified blocking default"
	assert "wait=false" in body, \
		"the policy states the default without its explicit override"


def test_the_agent_policy_names_protocol_eleven_and_the_stable_path():
	body = _text("docs/AGENTS-MAILBOX-PROTO.md")
	assert "protocol 11" in body
	assert "stable on purpose" in body, \
		"the policy does not explain why the v10 filename is kept"


def test_the_codex_bridge_example_matches_the_runtime_validator():
	"""W6: the documented post-v10 target/identity shape is executable,
	not a hand-maintained approximation of the JavaScript schema."""
	script = r'''
import { readFileSync } from "node:fs";
import { validateConfig } from "./tools/codex-event-bridge/src/config.mjs";

const raw = JSON.parse(readFileSync(
  "./tools/codex-event-bridge/config.example.json", "utf8"));
const config = validateConfig(raw);
if (!config.roleInstructions || !config.targets.driftquery.identity) {
  throw new Error("post-v10 role instruction identity was not validated");
}
'''
	done = subprocess.run(
		["node", "--input-type=module", "--eval", script], cwd=REPO,
		capture_output=True, text=True, timeout=30)
	assert done.returncode == 0, done.stderr
