"""W71459: integration keeps custody modes out of the checkout."""

from __future__ import annotations

import copy
import hashlib
import json
import os


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECORD = os.path.join(
	REPO, "work", "records", "2026", "09",
	"finding-integrator-test-change-preapproval")
GENERATION_SIX = os.path.join(RECORD, "evidence", "generation-6")
GENERATION_SEVEN = os.path.join(RECORD, "evidence", "generation-7")


def _json(path):
	with open(path, encoding="utf-8") as handle:
		return json.load(handle)


def _text(*parts):
	with open(os.path.join(REPO, *parts), encoding="utf-8") as handle:
		return handle.read()


def _normalized(text):
	return " ".join(text.replace("> ", "").replace("`", "").split())


def test_policy_guide_and_generation_seven_carry_the_confirmed_boundary():
	policy = _normalized(_text("AGENTS.md"))
	guide = _normalized(_text("docs", "PROPOSAL-INTEGRATOR.md"))
	candidate = _json(os.path.join(GENERATION_SEVEN, "baton.json"))
	role = _normalized(
		candidate["teams"]["baton"]["roles"]["integ"]["instructions"])

	for boundary in (
		"accepted Work description or plan",
		"adding, editing, or removing tests",
		"newest independent review",
		"non-symlink regular file",
		"reviewed base bytes",
		"already owner-writable",
		"without preserving custody modes",
		"verify final bytes and modes",
		"never work around a read-only target with install, chmod",
		"ordinary non-executable repository mode",
		"executable mode requires explicit accepted scope",
		"never request interactive approval from a managed turn",
	):
		assert boundary in policy
		assert boundary in guide
		assert boundary in role


def test_generation_seven_changes_only_generation_and_integrator_instructions():
	previous = _json(os.path.join(GENERATION_SIX, "baton.json"))
	candidate = _json(os.path.join(GENERATION_SEVEN, "baton.json"))
	assert previous["generation"] == 6
	assert candidate["generation"] == 7

	expected = copy.deepcopy(previous)
	expected["generation"] = 7
	expected["teams"]["baton"]["roles"]["integ"]["instructions"] = \
		candidate["teams"]["baton"]["roles"]["integ"]["instructions"]
	assert candidate == expected


def test_generation_seven_evidence_is_digest_bound_and_uses_fresh_gates():
	assert set(os.listdir(GENERATION_SEVEN)) == {"README.md", "baton.json"}
	with open(os.path.join(GENERATION_SEVEN, "baton.json"), "rb") as handle:
		digest = hashlib.sha256(handle.read()).hexdigest()
	with open(os.path.join(GENERATION_SEVEN, "README.md"), encoding="utf-8") as handle:
		raw_readme = handle.read()
	assert f"{digest}  baton.json" in raw_readme
	readme = " ".join(raw_readme.split())
	for boundary in (
		"accepted generation 6",
		"No participant, kind, route, root, capability",
		"no privileged `install`, `chmod`",
		"separately accountable Work or controlled immutable proposals",
		"never the closed W33937 history",
		"one positive and one negative managed gate",
		"before any content or mode mutation",
		"Exact checkout repair remains an operator action",
	):
		assert boundary in readme
