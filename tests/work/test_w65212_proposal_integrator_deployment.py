"""W65212: the dedicated proposal integrator is one exact managed identity."""

from __future__ import annotations

import json
import os
import subprocess


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _json(*parts):
	with open(os.path.join(REPO, *parts), encoding="utf-8") as handle:
		return json.load(handle)


def _text(*parts):
	with open(os.path.join(REPO, *parts), encoding="utf-8") as handle:
		return handle.read()


def test_integrator_has_one_context_target_and_readiness_consumer():
	infra = _json("conf", "infra.example.json")
	dispatcher = _json("conf", "codex-event-bridge.template.json")

	contexts = [entry for entry in infra["contexts"]
	            if entry.get("participant") == "baton.merge"]
	assert len(contexts) == 1
	context = contexts[0]
	assert context["name"] == "integrator"
	assert context["command"][-4:] == [
		"--participant", "baton.merge", "--role", "integ"]

	targets = [entry for entry in dispatcher["targets"].values()
	           if entry["identity"]["participant"] == "baton.merge"]
	assert len(targets) == 1
	assert targets[0] == {
		"server": "local",
		"threadId": "{{context.integrator.threadId}}",
		"identity": {
			"participant": "baton.merge",
			"role": "integ",
			"actionOwner": "baton.slaw",
		},
	}

	readiness = [entry for entry in infra["services"]
	             if entry.get("participant") == "baton.merge"]
	assert len(readiness) == 1
	assert readiness[0]["name"] == "codex-integrator-readiness"
	command = readiness[0]["command"]
	assert command[command.index("--participant") + 1] == "baton.merge"
	assert command[command.index("--target") + 1] == "baton-integrator"


def test_integrator_policy_is_exact_and_git_nonmutating():
	dispatcher = _json("conf", "codex-event-bridge.template.json")
	comments = "\n".join(value for key, value in dispatcher.items()
	                     if key.startswith("//"))
	assert "baton.merge" in comments
	assert "participant=\"$who\"" in comments

	contract = _text("docs", "PROPOSAL-INTEGRATOR.md")
	for boundary in (
			"review-bound digest", "declared base", "current target",
			"exact path set", "overlapping divergence", "broaden its paths",
			"Never stage or unstage", "commit", "merge or rebase Git history",
			"pass it to the approver"):
		assert boundary in contract

	policy = _text("AGENTS.md")
	assert "`baton.merge` for proposal integration (`integ`)" in policy
	assert "It never stages files or mutates Git history" in policy


def test_generation_five_candidate_is_complete_and_generator_exact():
	base = os.path.join(
		REPO, "work", "records", "2026", "09",
		"finding-dedicated-proposal-integrator", "evidence", "generation-5")
	with open(os.path.join(base, "baton.json"), encoding="utf-8") as handle:
		candidate = json.load(handle)
	team = candidate["teams"]["baton"]
	assert candidate["generation"] == 5
	assert team["kinds"]["merge"] == {
		"display": "Integration", "route": "integ"}
	assert team["participants"]["merge"] == {
		"display": "Integrator", "roles": ["integ"]}
	assert team["routes"]["integ"] == {
		"handlers": ["merge"], "role": "integ"}
	for boundary in ("review-bound digest", "base or target drift",
	                 "Never stage or unstage", "--participant baton.merge"):
		assert boundary in team["roles"]["integ"]["instructions"]

	with open(os.path.join(base, "codex-event-bridge.template.json"),
	          encoding="utf-8") as handle:
		dispatcher = json.load(handle)
	identity = dispatcher["roleInstructions"]
	generated = subprocess.run([
		"node", os.path.join(
			REPO, "tools", "codex-event-bridge", "src", "exec_policy.mjs"),
		f"binary={identity['binary']}", f"config={identity['config']}",
		"participant=baton.merge"], capture_output=True, text=True,
		check=True).stdout.splitlines()
	with open(os.path.join(base, "baton.rules"), encoding="utf-8") as handle:
		installed = [line.rstrip("\n") for line in handle
		             if '"--participant", "baton.merge"' in line]
	assert installed == generated
	assert all("git" not in line.lower() for line in installed)
