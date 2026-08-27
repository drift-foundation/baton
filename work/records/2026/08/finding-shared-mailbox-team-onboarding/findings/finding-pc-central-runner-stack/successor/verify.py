#!/usr/bin/env python3
"""Read-only structural preflight for the W10198 staged successor set."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
LIVE = Path("/home/sl/baton-v11.14aecfb")
BATON_REPO = Path("/home/sl/src/baton")
sys.path.insert(0, str(BATON_REPO / "tools"))
import infra  # noqa: E402


def load(path: Path):
	with path.open(encoding="utf-8") as handle:
		return json.load(handle, object_pairs_hook=infra._strict_object)


candidate = load(ROOT / "infra.json")
current = load(LIVE / "infra.json")
dispatcher = load(ROOT / "codex-event-bridge.template.json")
acp = load(ROOT / "acp-pc-code.template.json")
pushcoin_policy = (ROOT / "pushcoin-AGENTS.md").read_text(encoding="utf-8")

assert candidate["version"] == current["version"] == 2
assert candidate["control"] == current["control"]
assert candidate["contexts"][:len(current["contexts"])] == current["contexts"]
current_services = {entry["name"]: entry for entry in current["services"]}
candidate_services = {entry["name"]: entry for entry in candidate["services"]}
assert len(candidate_services) == len(candidate["services"])
for name, entry in current_services.items():
	assert candidate_services[name] == entry, f"existing service changed: {name}"

expected_contexts = {
	"pc-prompt": ("pc.prompt", "prompt"),
	"pc-plan": ("pc.plan", "rview"),
	"pc-tuner": ("pc.tuner", "tuner"),
}
for name, (participant, role) in expected_contexts.items():
	context = next(entry for entry in candidate["contexts"] if entry["name"] == name)
	assert context["participant"] == participant
	assert context["command"][context["command"].index("--participant") + 1] == participant
	assert context["command"][context["command"].index("--role") + 1] == role
	assert context["command"][context["command"].index("--cwd") + 1] == "/home/sl/src/pushcoin"

for participant, service_name, target in (
	("pc.plan", "pc-plan-readiness", "pc-plan"),
	("pc.tuner", "pc-tuner-readiness", "pc-tuner"),
):
	matching = [entry for entry in candidate["services"] if entry.get("participant") == participant]
	assert len(matching) == 1 and matching[0]["name"] == service_name
	command = matching[0]["command"]
	assert command[command.index("--participant") + 1] == participant
	assert command[command.index("--target") + 1] == target
assert not any(entry.get("participant") == "pc.prompt" for entry in candidate["services"])

pc_code = candidate_services["pc-code-acp"]
assert pc_code["participant"] == "pc.code"
assert pc_code["renders"][0]["name"] == "pc-code-acp"
assert acp["baton"]["participant"] == "pc.code" and acp["baton"]["role"] == "impl"
assert acp["agent"]["cwd"] == acp["session"]["cwd"] == "/home/sl/src/pushcoin"
assert acp["stateDir"].endswith("/{{start.id}}/pc.code")
assert acp["agent"]["env"]["BATON_BIN"] == acp["baton"]["binary"]
assert acp["agent"]["env"]["BATON_CONFIG"] == acp["baton"]["config"]
assert acp["agent"]["env"]["BATON_PARTICIPANT"] == acp["baton"]["participant"]
assert acp["agent"]["env"]["BATON_ROLE"] == acp["baton"]["role"]

expected_targets = {
	"pc-prompt": ("pc.prompt", "prompt", "pc.slaw", "{{context.pc-prompt.threadId}}"),
	"pc-plan": ("pc.plan", "rview", "pc.slaw", "{{context.pc-plan.threadId}}"),
	"pc-tuner": ("pc.tuner", "tuner", "pc.slaw", "{{context.pc-tuner.threadId}}"),
}
assert len({entry["identity"]["participant"] for entry in dispatcher["targets"].values()}) == len(dispatcher["targets"])
assert len({entry["threadId"] for entry in dispatcher["targets"].values()}) == len(dispatcher["targets"])
for name, expected in expected_targets.items():
	entry = dispatcher["targets"][name]
	actual = (entry["identity"]["participant"], entry["identity"]["role"], entry["identity"]["actionOwner"], entry["threadId"])
	assert actual == expected

assert "gemini" not in json.dumps(candidate).lower()
assert "gemini" not in json.dumps(dispatcher).lower()
assert "gemini" not in json.dumps(acp).lower()
assert Path("/home/sl/src/pushcoin").is_dir()
assert Path("/home/sl/src/pushcoin/.git").exists()

for required in (
	"protocol-11", "pc.prompt", "pc.plan", "pc.code", "pc.slaw",
	"pc.tuner", "work/records/YYYY/MM/finding-stable-name",
	"claim work=W", "--participant pc.plan", "BATON_BIN", "BATON_CONFIG",
	"BATON_PARTICIPANT=pc.code", "BATON_ROLE=impl",
):
	assert required in pushcoin_policy, f"Pushcoin policy omits {required!r}"
for retired in (
	"pushcoin.reviewer", "pushcoin.implementer", "work/finding-<slug>",
):
	assert retired not in pushcoin_policy, f"Pushcoin policy retains {retired!r}"
assert pushcoin_policy.count("claim --message-id") == 1
assert "claim --message-id`, and `see` are retired" in pushcoin_policy

# Exercise the lifecycle loader against the staged templates without
# rewriting the literal-install manifest committed for the operator.
preflight = copy.deepcopy(candidate)
replacements = {
	str(LIVE / "codex-event-bridge.template.json"): str(ROOT / "codex-event-bridge.template.json"),
	str(LIVE / "acp-pc-code.template.json"): str(ROOT / "acp-pc-code.template.json"),
}
for service in preflight["services"]:
	service["requires"] = [replacements.get(path, path) for path in service.get("requires", [])]
	for render in service.get("renders", []):
		render["template"] = replacements.get(render["template"], render["template"])
with tempfile.TemporaryDirectory(prefix="w10198-infra-preflight-") as directory:
	mailbox = Path(directory)
	(mailbox / "infra.json").write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")
	loaded = infra.load_manifest(str(mailbox))
	assert len(loaded["contexts"]) == 6
	assert len(loaded["services"]) == 8

print("infra preflight: 6 contexts, 8 services, existing Baton entries unchanged")
print("pc topology: 3 Codex targets, 2 readiness consumers, 1 Claude ACP service")
print("pc.code launch contract: exact Baton locators and identity exported")
print("working directory: /home/sl/src/pushcoin; Gemini references: 0")
print("Pushcoin policy: protocol 11, five pc.* identities, permanent dossiers")
