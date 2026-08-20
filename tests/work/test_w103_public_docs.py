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
from baton_work import transitions as _tr                      # noqa: E402

# The documents that give CURRENT guidance. Release notes, dossiers, and
# review journals are history and are deliberately absent.
ACTIVE_DOCS = (
	"README.md",
	"docs/BATON-WORK.md",
	# W2780 R4: the current OPERATING guide was missing, so both
	# documentation guards passed around a live W38 contradiction in it.
	"docs/EFFECTIVE-BATON.md",
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


# W2693: the scheduler phase axis is a CLOSED set, and every active
# document that names it must name the current one. `waiting` was
# renamed to `block`; the constant moved and the prose did not, so
# `docs/BATON-WORK.md` taught a phase the CLI refuses.
#
# `waiting` is a legitimate word elsewhere and the checks below must not
# sweep it: it is a poke-answer state (`idle|working|waiting|needs-help`),
# it is half of the runtime state `waiting-input`, and it is ordinary
# English. What distinguishes a PHASE-sense use is the company it keeps —
# the axis is enumerated, so a stale member appears beside a live one.
PHASE_COMPANIONS = ("queued", "active", "parked", "phase")
RETIRED_PHASES = ("waiting",)


def _phase_sense_uses(body, token):
	"""Occurrences of `token` standing beside a real phase name.

	A window rather than a line, because these enumerations wrap. The
	companions deliberately exclude `block` itself: the document also
	uses `block` as a VERB (`block work=W on=…`) and as the adjective
	`blocked`, so it cannot distinguish an axis enumeration from an
	ordinary sentence — while `queued`, `active` and `parked` have no
	other meaning here."""
	hits = []
	# CASE-INSENSITIVE: W2780 R4 found `honest WAITING` in a workflow
	# story that this scan walked straight past.
	for match in re.finditer(rf"\b{token}\b(?!-)", body, re.IGNORECASE):
		window = body[max(0, match.start() - 60):match.end() + 60]
		if any(companion in window for companion in PHASE_COMPANIONS):
			hits.append(window.replace("\n", " "))
	return hits


def test_no_active_document_names_a_retired_scheduler_phase():
	"""The drift this exists to catch, in every document that could
	repeat it — not only the one where it was found."""
	for relative in ACTIVE_DOCS:
		body = _text(relative)
		for token in RETIRED_PHASES:
			hits = _phase_sense_uses(body, token)
			assert not hits, (
				f"{relative} names the retired phase {token!r} beside a "
				f"live one; the axis is {_tr.PHASES}: " + " | ".join(hits))


# W2780 R3: the guards above protect ACTIVE_DOCS, and the review was
# right that a repository sweep was CLAIMED and not encoded — the same
# retired vocabulary was still published from the CLI grammar and from
# live source and executable-spec prose.
#
# These two sets are what a sweep may read. Source and tests are not
# prose documents, so the scan is deliberately narrow: it looks at
# comments and docstrings, and it allows any window that says the
# retired name IS retired, because history has to remain writable.
def swept_sources():
	"""Every live Python source and executable spec, DERIVED.

	W2780 R4: this was a hand-picked five-file tuple, and the review was
	right that a repository sweep cannot be claimed after checking an
	arbitrary subset — current-sense uses of the retired name were
	sitting just outside it. The scope is now the glob, so a new file
	is covered the day it is written and nobody has to remember a list.

	`src/` and `tests/` only: `work/records` is permanent evidence and
	is deliberately never rewritten to satisfy a scan."""
	roots = (REPO / "src" / "baton_work", REPO / "tests")
	mine = pathlib.Path(__file__).resolve().relative_to(REPO)
	return sorted(
		str(path.relative_to(REPO))
		for root in roots for path in root.rglob("*.py")
		if "__pycache__" not in path.parts
		# This file DEFINES the vocabulary it forbids; it has to be
		# able to name the token to guard it.
		and path.relative_to(REPO) != mine)

# Saying a retired name is retired is not teaching it. Any of these in
# the window makes the mention historical rather than current guidance.
HISTORICAL = ("renamed", "retired", "superseded", "supersedes",
              "pre-W78", "no longer", "used to", "was the name")


# A phase NAME is enumerated or quoted; the ordinary English participle
# is followed by a word. `waiting on budget` inside a park reason is not
# the scheduler axis, and a guard that cannot tell them apart would push
# people into contorting prose to satisfy it.
_CONNECTORS = ("and", "or", "queued", "active", "block", "parked",
               "waiting")


def _reads_as_a_phase_name(body, match):
	tail = body[match.end():match.end() + 24].lstrip("`'\"")
	if not tail or not tail[:1].isspace():
		return True                       # a delimiter follows: enumerated
	following = tail.split()
	if not following:
		return True
	word = following[0].strip(",|/`'\"")
	if not word:
		return True                       # a bare delimiter: enumerated
	return word.lower() in _CONNECTORS


def _current_retired_phase(body, token="waiting"):
	"""Retired-phase mentions that read as CURRENT guidance.

	Three filters, each for a use that must stay legal. The companion
	rule from the ACTIVE_DOCS guard, widened to the word `phase` itself
	— a stale member stands beside a live one, or beside the axis it
	belongs to. The historical exemption, without which this repository
	could not record its own supersessions. And the English one, because
	`waiting on budget` is not a phase.

	THE LIMIT, stated plainly because W2780 R4 was right to press on it.
	This is a REGRESSION guard, not a proof of absence. It catches the
	retired name where it is enumerated or delimiter-adjacent — which is
	the shape it kept coming back in — and it CANNOT catch a prose-shaped
	use like "lands `queued` when runnable, `waiting` when a gate is
	unsatisfied": at that distance a phase name and an English participle
	are the same string. The repository was therefore swept by READING,
	file by file over the same derived scope, and the corrections are
	recorded in the Work's discussion. The guard's job is to stop the
	catchable shapes returning; a reviewer is still what catches the
	rest."""
	hits = []
	for match in re.finditer(rf"\b{token}\b(?!-)", body):
		window = body[max(0, match.start() - 90):match.end() + 90]
		if not any(name in window for name in PHASE_COMPANIONS):
			continue
		if any(word in window for word in HISTORICAL):
			continue
		if not _reads_as_a_phase_name(body, match):
			continue
		hits.append(" ".join(window.split()))
	return hits


def test_the_generated_cli_help_states_the_claim_phase_invariant():
	"""P1: `--help` and command assistance are a PUBLIC contract emitted
	from `_SPEC`, so a documentation sweep cannot protect them. The
	`claim` help said "(phase untouched)" while the protocol document
	said the claim IS the phase.

	Derived from the live grammar, not from a fixed string: the phase
	the CLI does not offer as a `phase to=` value is the one claiming
	must be documented as reaching."""
	unsettable = tuple(phase for phase in _tr.PHASES
	                   if phase not in _cli._SETTABLE_PHASES)
	assert unsettable == ("active",), unsettable
	claimed = unsettable[0]
	help_text = _cli.GRAMMAR["claim"]["help"]
	assert claimed in help_text, \
		f"the claim help never mentions `{claimed}`: {help_text!r}"
	assert not _retired_claim_phase(help_text), \
		f"the claim help still separates the claim from the phase: " \
		f"{help_text!r}"
	assert "untouched" not in help_text, \
		f"the claim help still says the phase is untouched: {help_text!r}"


def test_no_verb_help_teaches_a_retired_scheduler_phase():
	"""The whole generated grammar, not only `claim` — every verb's help
	and every key's help, since both reach an operator through
	`--help`."""
	for verb, spec in _cli.GRAMMAR.items():
		texts = [spec.get("help", "")]
		texts += [key.get("help", "") for key in spec.get("keys", ())]
		for text in texts:
			for retired in RETIRED_PHASES:
				assert not _current_retired_phase(text, retired), \
					f"{verb} help teaches the retired phase " \
					f"{retired!r}: {text!r}"


def test_live_source_and_spec_prose_teach_only_live_phases():
	"""P1/P2: the same rule over a DERIVED scope — every live source and
	spec file, not a hand-picked list. History stays writable, since a
	window that says the name is retired is exempt, so this forbids
	teaching the old axis rather than remembering it.

	See `_current_retired_phase` for what this can and cannot see."""
	found = []
	for relative in swept_sources():
		body = _text(relative)
		for retired in RETIRED_PHASES:
			for hit in _current_retired_phase(body, retired):
				found.append(f"{relative}: {retired!r} in …{hit}…")
	# Every file at once. Reporting the first and stopping made a sweep
	# feel like whack-a-mole and hid how much was left.
	assert not found, "retired phases taught as current:\n" + \
		"\n".join(found)


def test_the_exemptions_are_not_holes():
	"""Each filter has to be narrow enough to still catch the real
	thing, so both directions are pinned together."""
	# caught: the stale axis, taught as current, in the shapes it
	# actually appeared in
	for stale in ("the axis is queued, active, waiting, parked",
	              "phase is queued | active | waiting | parked",
	              "the declared forms — phase parked/waiting",
	              "a gate on unclaimed queued Work commits waiting/gates",
	              "the phase episodes are queued/active/waiting/parked",
	              "scheduler axis — queued | active | waiting | parked"):
		assert _current_retired_phase(stale), stale
	# allowed: history, and ordinary English near a parked row
	for legal in ("the axis was queued, active, waiting, parked before "
	              "`waiting` was renamed `block`",
	              'phase="parked", reason="waiting on budget"',
	              "a root's child sat waiting while the parked leaf "
	              "stayed put",
	              "answered with state=waiting while the queued row "
	              "stood still",
	              "CHECK (state IN ('idle', 'working', 'waiting', "
	              "'needs-help'))"):
		assert not _current_retired_phase(legal), legal


def test_the_protocol_document_enumerates_exactly_the_live_phase_axis():
	"""The sentence that DEFINES the closed set is the one that lied, so
	it is checked directly: the phases it names, in backticks, must be
	the authority's set exactly — no member missing, none invented."""
	body = _text("docs/BATON-WORK.md")
	axis = re.search(r"phase is a closed SCHEDULER axis — (.+?)absent once",
	                 body, re.S)
	assert axis, 		"the phase-axis sentence has moved; this check must move with it"
	named = set(re.findall(r"`([a-z]+)`", axis.group(1)))
	assert named == set(_tr.PHASES), 		f"the document enumerates {sorted(named)}, the axis is " \
		f"{sorted(_tr.PHASES)}"


# W2780: the wordings W38 retired. Every one of them names the CLAIM and
# the PHASE TOGETHER — as patterns rather than fragments, because Baton
# has real independent axes and documenting one of those must stay
# possible.
#
# Review R2 was right that the fragment list was still too much: bare
# "orthogonal to phase" does not name a claim, so it would have rejected
# "the route is orthogonal to phase". The first pattern therefore
# requires the claim WITHIN one sentence of the orthogonality — `[^.]`
# bounds the window to a sentence, and the prose is space-normalized
# before matching, so a wrapped line reads as one string.
RETIRED_CLAIM_PHASE = (
	r"claim[^.]{0,80}orthogonal[^.]{0,40}phase",
	r"phase-orthogonal\s+claim",
	r"claiming never rewrites phase",
	r"claim[^.]{0,80}without touching[^.]{0,60}stage",
	r"keeps its honest stage phase",
)


def _retired_claim_phase(prose):
	"""Every retired claim/phase wording this prose still uses."""
	return [pattern for pattern in RETIRED_CLAIM_PHASE
	        if re.search(pattern, prose, re.IGNORECASE)]


def test_the_narrowed_guard_still_lets_a_real_independent_axis_be_written():
	"""The other half of R1, pinned so the guard cannot be re-widened by
	accident: a document must remain able to say that Baton's genuinely
	independent axes are independent. Only the claim-and-phase pairing
	is retired."""
	for legitimate in (
			"the route is orthogonal to phase",
			"the route's role is orthogonal to the scheduler phase: one "
			"says what KIND of work this is, the other whether it can run",
			"phase and role are orthogonal axes"):
		assert not _retired_claim_phase(legitimate), \
			f"the guard forbids a genuinely separate axis: {legitimate!r}"
	for retired in (
			"the active claim is its own authority state, orthogonal to "
			"phase",
			"claim work=WORK records WHO is executing without touching "
			"WHAT stage the phase names",
			"finding-active-work-claim: the atomic phase-orthogonal claim",
			"blocked Work keeps its honest stage phase but cannot be "
			"claimed"):
		assert _retired_claim_phase(retired), \
			f"the guard no longer catches: {retired!r}"


def test_the_protocol_document_states_the_claim_phase_invariant():
	"""W2780: the guide said the claim was "orthogonal to phase" and
	recorded WHO "without touching" the phase. W38 superseded exactly
	that: the claim and `active` are one fact, and only `claim` reaches
	it. A reader following the retired sentence would look for a way to
	set `active` and find a refusal.

	The check derives the phase from the LIVE contract rather than
	naming it: `active` is precisely the member of `PHASES` that the CLI
	does not offer as a `phase to=` value. If that ever stops being
	true, the first assertion fails and says so — because the prose this
	guards would then be describing a different rule."""
	unsettable = tuple(phase for phase in _tr.PHASES
	                   if phase not in _cli._SETTABLE_PHASES)
	assert unsettable == ("active",), (
		f"the settable-phase contract moved: {sorted(_tr.PHASES)} minus "
		f"{sorted(_cli._SETTABLE_PHASES)} is {list(unsettable)}; the "
		f"documentation guard below must move with it")
	claimed = unsettable[0]
	prose = " ".join(_text("docs/BATON-WORK.md").split())
	assert f"only `claim` reaches `{claimed}`" in prose, \
		f"the document does not say that only claiming reaches " \
		f"`{claimed}`"
	assert f"`phase to={claimed}` is refused" in prose, \
		f"the document does not say `phase to={claimed}` refuses"
	still = _retired_claim_phase(prose)
	assert not still, \
		f"the document still teaches the superseded rule: {still}"


def test_no_active_document_separates_the_claim_from_the_phase():
	"""The same supersession, swept across every document that gives
	current guidance — the contradiction was pre-existing and found in
	one file, which is not evidence it lived in only one.

	W2780 review R1: this used to ban the bare word "orthogonal", which
	is too much. Baton HAS independent axes and says so — the route's
	role is genuinely orthogonal to the scheduler phase, and the
	corrected paragraph in this very document relies on being able to
	say that. What W38 retired is one specific pairing, so the phrases
	below name the CLAIM and the PHASE together and nothing else."""
	for relative in ACTIVE_DOCS:
		still = _retired_claim_phase(" ".join(_text(relative).split()))
		assert not still, \
			f"{relative} still separates the claim from the phase: {still}"


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
