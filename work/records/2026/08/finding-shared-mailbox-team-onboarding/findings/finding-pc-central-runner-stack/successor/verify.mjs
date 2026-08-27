#!/usr/bin/env node
// Read-only config and exact execution-policy preflight for W10198.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { validateConfig as validateDispatcher } from "/home/sl/src/baton/tools/codex-event-bridge/src/config.mjs";
import { assertInspectionProvisioned, assertPolicyProvisioned } from "/home/sl/src/baton/tools/codex-event-bridge/src/exec_policy.mjs";
import { validateConfig as validateAcp } from "/home/sl/src/baton/tools/acp-baton-bridge/src/config.mjs";

const root = dirname(fileURLToPath(import.meta.url));
const parse = (name) => JSON.parse(readFileSync(join(root, name), "utf8"));
const policy = join(root, "baton.rules");
const dispatcher = parse("codex-event-bridge.template.json");
dispatcher.roleInstructions.execPolicyFile = policy;
const validatedDispatcher = validateDispatcher(dispatcher);

for (const target of Object.values(validatedDispatcher.targets)) {
	assertPolicyProvisioned(policy, {
		binary: validatedDispatcher.roleInstructions.binary,
		config: validatedDispatcher.roleInstructions.config,
		participant: target.identity.participant,
	});
}
assertInspectionProvisioned(policy);

const acp = parse("acp-pc-code.template.json");
const stagedPolicy = join(root, "pc-code-policy");
acp.agent.command = join(stagedPolicy, "launch-agent-sandboxed.sh");
acp.agent.env.PROTECTED_PATHS_FILE = join(stagedPolicy, "protected-paths.txt");
acp.policyResources = [
	join(stagedPolicy, "claude/settings.json"),
	join(stagedPolicy, "block-git-commit.sh"),
	join(stagedPolicy, "git_guard.py"),
	join(stagedPolicy, "launch-agent-sandboxed.sh"),
	join(stagedPolicy, "protected-paths.txt"),
];
const validatedAcp = validateAcp(acp);
if (validatedAcp.baton.participant !== "pc.code" || validatedAcp.baton.role !== "impl") {
	throw new Error("pc.code ACP identity/role mismatch");
}
if (validatedAcp.agent.env.BATON_BIN !== validatedAcp.baton.binary
		|| validatedAcp.agent.env.BATON_CONFIG !== validatedAcp.baton.config
		|| validatedAcp.agent.env.BATON_PARTICIPANT !== validatedAcp.baton.participant
		|| validatedAcp.agent.env.BATON_ROLE !== validatedAcp.baton.role) {
	throw new Error("pc.code ACP launcher environment does not match its Baton identity");
}

console.log(`dispatcher preflight: ${Object.keys(validatedDispatcher.targets).length} unique targets`);
console.log("execution policy: 6 exact participant profiles + Docker inspection profile");
console.log("ACP preflight: pc.code/impl policy resources readable from staged set");
console.log("ACP locator preflight: exact binary/config/participant/role exported");
