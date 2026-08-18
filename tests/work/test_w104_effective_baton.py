"""W104: EFFECTIVE-BATON is the v11 operating guide, and stays one.

The finding requires every command example to be executed against the
release candidate that ships the rewrite. Executing them once proves the
document was right the day it was written; these checks are what keep it
right — a later edit cannot quietly reintroduce a retired verb, invent a
verb the CLI does not have, or teach a phase the authority refuses.

The guide is deliberately NOT a second specification, so nothing here
asserts prose completeness. The checks are mechanical: the vocabulary it
uses must exist, and the vocabulary it retired must stay retired.
"""

from __future__ import annotations

import pathlib
import re

from baton_work import cli as _cli
from baton_work import transitions as _tr

REPO = pathlib.Path(__file__).resolve().parents[2]
GUIDE = REPO / "docs" / "EFFECTIVE-BATON.md"


def _text():
	return GUIDE.read_text(encoding="utf-8")


def _referenced_verbs(body):
	"""Verbs the guide actually tells a reader to run."""
	return set(re.findall(r"(?:\$BATON|baton --participant [a-z.]+) "
	                      r"([a-z][a-z-]*)", body))


def test_every_verb_the_guide_teaches_exists_in_the_cli():
	"""The failure this catches is a guide that drifts ahead of, or
	behind, the shipped grammar — the reader runs it and it refuses."""
	known = set(_cli.GRAMMAR)
	used = _referenced_verbs(_text())
	assert used, "no commands found; the extraction pattern has drifted"
	assert used <= known, \
		f"the guide teaches verbs the CLI does not have: {sorted(used - known)}"


def test_the_guide_teaches_the_retired_runtime_nowhere():
	body = _text()
	for token in ("baton-tui", "baton-codex-monitor", "codex-baton-stack",
	              "send-notice", "just codex-baton"):
		assert token not in body, \
			f"the operating guide still prescribes the retired {token!r}"


def test_retired_mailbox_verbs_appear_only_as_retired():
	"""Naming what was retired is the point; teaching it is the defect.
	The distinction is the sentence that says so, and prose wraps, so
	the disclaimer is looked for in a window rather than one line."""
	lines = _text().splitlines()
	for number, line in enumerate(lines, 1):
		if not re.search(r"`(send|reply)`", line):
			continue
		window = " ".join(lines[max(0, number - 3):number + 2])
		assert re.search(r"retired|not a fallback|[Pp]rotocol 10", window), \
			f"EFFECTIVE-BATON:{number} teaches retired verbs: {line!r}"


def test_the_guide_teaches_only_real_phases_and_outcomes():
	"""A guide naming a phase or outcome the authority refuses sends a
	reader into a guaranteed refusal."""
	body = _text()
	for token in re.findall(r"`(?:phase )?(?:work=\S+ )?to=([a-z]+)`", body):
		assert token in _tr.PHASES, f"unknown phase taught: {token}"
	for token in re.findall(r"outcome=([a-z-]+)", body):
		assert token in _tr.OUTCOMES, f"unknown outcome taught: {token}"


def test_the_guide_pins_the_claim_before_execute_rule():
	"""The one rule whose absence produces the operational races v11
	exists to prevent."""
	body = _text()
	assert "Claim before you execute" in body
	assert "fail closed" in body or "fails closed" in body


def test_the_guide_states_both_halves_of_the_readiness_contract():
	"""Same defect W103 R3 found in the agent policy: a runner that only
	looks for unclaimed Work walks past its own restarted assignment."""
	body = _text()
	assert "already claimed" in body.lower()
	assert "restart" in body.lower()
	assert "claims nothing" in body


def test_the_guide_keeps_the_blocking_request_precondition():
	"""W159's ruled grammar: the blocking form suspends the Work its own
	executor is doing, so it refuses on unclaimed Work. A guide that
	omits this teaches an example that cannot run."""
	body = _text()
	assert "wait=false" in body, "the asynchronous override is undocumented"
	assert "unclaimed" in body


def test_the_guide_separates_route_stability_from_claim_release():
	"""W245 + W159 together. The previous version of this check accepted
	"Current does not move", which W245 made FALSE: the route is what
	stays put, while entering the blocking wait releases the claim and
	therefore clears current. A regression that accepts the superseded
	sentence protects the wrong model, so both halves are asserted
	separately."""
	# Prose WRAPS, so every phrase check here collapses whitespace
	# first — matching line-by-line is how a true statement gets
	# reported as missing.
	flat = " ".join(_text().split())
	assert "**The route does not move**" in flat, \
		"the guide does not say the ROUTE stays put across a request"
	assert "**Current does clear**" in flat, \
		"the guide does not say a blocking request CLEARS current"
	assert "Current does not move" not in flat, \
		"the guide still teaches the superseded W245 invariant"


def test_the_guide_names_claimant_authority_for_scope_revision():
	"""W288: `revise` requires the EXACT current claimant, who must also
	still be route-eligible. The guide previously taught route-handler
	authority, which was true of the implementation and wrong as a
	contract — an eligible peer could rewrite scope underneath the
	person executing it. Both halves are pinned."""
	flat = " ".join(_text().split())
	revision = flat[flat.index("## Changing the contract"):]
	assert "**exact current claimant**" in revision, revision[:500]
	assert "still be eligible through the live route" in revision
	assert "Unclaimed Work refuses" in revision
	assert "never rewrites assigned scope underneath its executor" in revision


def test_the_guide_does_not_supply_a_destination_phase_by_hand():
	"""W73: the destination route decides the phase. An example passing
	phase= would be refused as unknown."""
	assert not re.search(r"pass work=\S+[^\n]*\bphase=", _text()), \
		"the guide shows a pass supplying its own destination phase"


def test_the_guide_is_subordinate_to_the_contract_documents():
	"""The documentation boundary: this explains how to work safely and
	links for depth, rather than duplicating the verb surface."""
	body = _text()
	assert "BATON-WORK.md" in body and "BATON-SETUP.md" in body
	assert "they are the authority" in body
