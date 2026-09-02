"""W71459: managed integration preflights existing-test change authority."""

from __future__ import annotations

import copy
import hashlib
import json
import os


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECORD = os.path.join(
	REPO, "work", "records", "2026", "09",
	"finding-integrator-test-change-preapproval")
GENERATION_FIVE = os.path.join(
	REPO, "work", "records", "2026", "09",
	"finding-dedicated-proposal-integrator", "evidence", "generation-5")
GENERATION_SIX = os.path.join(RECORD, "evidence", "generation-6")


def _json(path):
	with open(path, encoding="utf-8") as handle:
		return json.load(handle)


def _text(*parts):
	with open(os.path.join(REPO, *parts), encoding="utf-8") as handle:
		return handle.read()


def _normalized(text):
	return " ".join(text.replace("> ", "").split())


def test_policy_guide_and_candidate_carry_the_complete_preflight_boundary():
	policy = _normalized(_text("AGENTS.md"))
	guide = _normalized(_text("docs", "PROPOSAL-INTEGRATOR.md"))
	candidate = _json(os.path.join(GENERATION_SIX, "baton.json"))
	role = _normalized(
		candidate["teams"]["baton"]["roles"]["integ"]["instructions"])

	for boundary in (
		"whole proposed path set",
		"existing test path",
		"immutable proposal digest",
		"assertion or expected-behaviour changes",
		"Generic sign-off",
		"candidate-byte enumeration",
		"proposal-wide approval",
		"before changing any path",
		"missing, ambiguous, stale, digest-mismatched, or incomplete",
		"never request interactive approval from a managed turn",
		"reviewed candidate bytes at the named paths",
		"another test change, weakening, redesign, conflict correction",
	):
		assert boundary in policy
		assert boundary in guide
		assert boundary in role


def test_generation_six_changes_only_generation_and_integrator_instructions():
	previous = _json(os.path.join(GENERATION_FIVE, "baton.json"))
	candidate = _json(os.path.join(GENERATION_SIX, "baton.json"))
	assert previous["generation"] == 5
	assert candidate["generation"] == 6

	expected = copy.deepcopy(previous)
	expected["generation"] = 6
	expected["teams"]["baton"]["roles"]["integ"]["instructions"] = \
		candidate["teams"]["baton"]["roles"]["integ"]["instructions"]
	assert candidate == expected


def test_generation_six_evidence_is_digest_bound_and_rollout_gated():
	assert set(os.listdir(GENERATION_SIX)) == {"README.md", "baton.json"}
	with open(os.path.join(GENERATION_SIX, "baton.json"), "rb") as handle:
		digest = hashlib.sha256(handle.read()).hexdigest()
	with open(os.path.join(GENERATION_SIX, "README.md"), encoding="utf-8") as handle:
		readme = handle.read()
	assert f"{digest}  baton.json" in readme
	for boundary in (
		"accepted generation 5",
		"independent review",
		"drain",
		"paused",
		"regen",
		"fresh `integrator` context",
		"W33937",
		"without an interactive approval request",
	):
		assert boundary in readme


def test_rollout_fences_recovery_before_pause_and_stop():
	with open(os.path.join(GENERATION_SIX, "README.md"), encoding="utf-8") as handle:
		readme = handle.read()
	approval = readme.index("1. place in W33937's handoff")
	drain = readme.index("begin the deployment drain")
	recovery = readme.index("release the exact `baton.merge` assignment")
	paused = readme.index("moves dispatch to `paused`")
	stop = readme.index("stop through the drained lifecycle gate")
	restart = readme.index("start the managed stack")
	claim = readme.index("allow queued W33937 to be claimed")
	assert approval < drain < recovery < paused < stop < restart < claim

	plan = _normalized(_text(
		"work", "records", "2026", "09",
		"finding-integrator-test-change-preapproval", "PLAN.md"))
	approval = plan.index("Place W33937's digest-bound four-test-path approval")
	drain = plan.index("begin the deployment drain")
	recovery = plan.index("recover the exact W33937 claim under that drain fence")
	paused = plan.index("dispatch reaches `paused`")
	stop = plan.index("Then stop")
	restart = plan.index("restart into a fresh integrator context")
	assert approval < drain < recovery < paused < stop < restart
