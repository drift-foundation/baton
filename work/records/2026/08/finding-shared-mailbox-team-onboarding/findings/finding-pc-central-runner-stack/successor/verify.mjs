#!/usr/bin/env node
// Read-only config and exact execution-policy preflight for W10198.

import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync,
	writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
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
	join(stagedPolicy, "preflight-process-domain.sh"),
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

// W28681: THE CONFIGURED LAUNCHER MUST OWN ITS DESCENDANTS.
//
// The bridge cannot check this. It is deliberately ACP-generic and does not
// parse the configured command -- so the one place that can hold a deployment
// to "the outer owner is a process domain" is the verifier of that
// deployment's own staged set, which is here.
//
// The incident this closes: a mount-only bubblewrap launch contained every
// WRITE the agent could make and owned none of its PROCESSES, so five tool
// groups outlived it by a day and a half. A setsid call escapes a process
// group and a session; it does not escape a PID namespace.
//
// REVIEW [P0]: THE FIRST VERSION OF THIS CHECK SEARCHED FREE TEXT, and the
// paragraph you are reading is why that failed. Both flag names appear in the
// launcher's own explanatory comments, so removing them from the executable
// ARGS line left `includes()` answering true for both -- a gate that admitted
// exactly the mount-only launcher it exists to refuse.
//
// So this RUNS the launcher against a recording stand-in for bwrap and reads
// the argv that was actually composed. Prose cannot satisfy it.
function launcherVector(script) {
	const probe = mkdtempSync(join(tmpdir(), "w28681-launcher-"));
	try {
		const recorder = join(probe, "bwrap");
		const record = join(probe, "argv.json");
		// COMMONJS ON PURPOSE: a file named `bwrap` has no `.mjs` suffix, so
		// Node reads it as a script and an `import` would not parse.
		writeFileSync(recorder,
			"#!/usr/bin/env node\n"
			+ `require("node:fs").writeFileSync(${JSON.stringify(record)}, `
			+ "JSON.stringify(process.argv.slice(2)));\n",
			{ mode: 0o755 });
		const agent = join(probe, "agent-real");
		writeFileSync(agent, "#!/bin/sh\nexit 0\n", { mode: 0o755 });
		// RUN THROUGH `bash` rather than executed: the staged copy carries the
		// mode the checkout gave it, and INSTALL.md is what makes the
		// installed one executable. What is under test is the launch this
		// script COMPOSES, not the bit the filesystem happens to have.
		const answer = spawnSync("bash", [script], {
			env: { ...process.env, PATH: `${probe}:${process.env.PATH}`,
				AGENT_REAL: agent,
				PROTECTED_PATHS_FILE: join(stagedPolicy,
					"protected-paths.txt") },
			encoding: "utf8",
		});
		if (answer.status !== 0) {
			throw new Error("the staged ACP launcher refused to run under a "
				+ `recording bwrap: ${answer.error?.message ?? ""}`
				+ `${answer.stderr ?? ""}${answer.stdout ?? ""}`);
		}
		return { argv: JSON.parse(readFileSync(record, "utf8")), agent };
	} finally {
		rmSync(probe, { recursive: true, force: true });
	}
}

function launcherOwnsItsDescendants(script) {
	const { argv, agent } = launcherVector(script);
	const executable = argv.indexOf(agent);
	if (executable < 0) return "the launcher never execs the configured agent";
	for (const flag of ["--unshare-pid", "--die-with-parent"]) {
		const at = argv.indexOf(flag);
		// PRESENT AS AN ARGUMENT, and BEFORE the executable -- a bubblewrap
		// option after the command is an argument to the command.
		if (at < 0) return `the composed launch does not pass ${flag}`;
		if (at > executable) return `${flag} is passed to the agent rather `
			+ "than to bubblewrap";
	}
	// AND THE MOUNT BOUNDARY IS STILL THERE. The process domain is a second
	// duty, not a replacement for the first.
	if (!argv.includes("--ro-bind")) {
		return "the composed launch binds no protected path read-only";
	}
	return null;
}

const launcherScript = join(stagedPolicy, "launch-agent-sandboxed.sh");
const verdict = launcherOwnsItsDescendants(launcherScript);
if (verdict) {
	throw new Error(`${verdict}; a mount-only sandbox contains the agent's `
		+ "writes and does not own its descendants, which is not an accepted "
		+ "managed configuration");
}

// AND THE CHECK CAN ACTUALLY FAIL. Review [P0] found the previous one could
// not, so this gate now proves its own reachability the same way: a copy with
// the functional flags removed from the ARGS line and EVERY explanatory
// comment retained must be refused. If this ever stops refusing, the check
// above has gone back to reading prose.
const gutted = mkdtempSync(join(tmpdir(), "w28681-gutted-"));
try {
	const copy = join(gutted, "launch-agent-sandboxed.sh");
	const source = readFileSync(launcherScript, "utf8");
	const stripped = source.replace(
		"ARGS=(--unshare-pid --die-with-parent --dev-bind / /)",
		"ARGS=(--dev-bind / /)");
	if (stripped === source) {
		throw new Error("the staged launcher no longer composes its ARGS the "
			+ "way this reachability probe removes them; re-point the probe "
			+ "rather than leaving it unable to fail");
	}
	for (const flag of ["--unshare-pid", "--die-with-parent"]) {
		if (!stripped.includes(flag)) {
			throw new Error(`removing the functional ${flag} also removed `
				+ "every mention of it, so this probe would pass a free-text "
				+ "check too and proves nothing");
		}
	}
	writeFileSync(copy, stripped, { mode: 0o755 });
	if (!launcherOwnsItsDescendants(copy)) {
		throw new Error("the launcher gate accepted a mount-only launcher "
			+ "whose comments still name both flags; it is reading prose "
			+ "rather than the composed launch");
	}
} finally {
	rmSync(gutted, { recursive: true, force: true });
}

// REVIEW [P0]: EVERY REQUIRED POLICY RESOURCE MUST BE STAGED *AND* INSTALLED.
//
// The template named `preflight-process-domain.sh` as a required policy
// resource and INSTALL.md never installed it, so following the documented
// cutover produced a configuration the ACP bridge refuses to start — a
// missing-resource failure at launch, discovered by an operator mid-cutover
// rather than by this gate.
//
// The bridge already refuses an unreadable resource; what nothing checked is
// that the OPERATOR PROCEDURE puts one there. So each entry is mapped back to
// its staged counterpart and required to exist, and INSTALL.md is required to
// name its installed path. This is a documentation check on purpose: the
// defect was in the procedure, not in the code.
const installDoc = readFileSync(join(root, "INSTALL.md"), "utf8");
const stagedNames = new Set(readdirSync(stagedPolicy));
for (const resource of parse("acp-pc-code.template.json").policyResources) {
	const name = resource.slice(resource.lastIndexOf("/") + 1);
	const staged = resource.includes("/policy/claude/")
		? join(stagedPolicy, "claude", name)
		: join(stagedPolicy, name);
	if (!existsSync(staged)) {
		throw new Error(`the template requires policy resource ${resource} `
			+ `and this staged set does not carry ${staged}; the bridge would `
			+ "refuse to start on a missing resource");
	}
	if (!resource.includes("/policy/claude/") && !stagedNames.has(name)) {
		throw new Error(`${name} is not in the staged policy directory`);
	}
	// AN INSTALL LINE, NOT A MENTION. Searching free text is the mistake the
	// launcher gate above was just corrected for: a byte-comparison, a
	// rollback removal or a paragraph naming the path would all satisfy
	// `includes()` while nothing ever put the file there.
	const installs = installDoc.split("\n").some((line) => {
		const words = line.trim().split(/\s+/);
		return words[0] === "install" && words[words.length - 1] === resource;
	});
	if (!installs) {
		throw new Error(`INSTALL.md has no install command whose destination `
			+ `is ${resource}, which the template requires; an operator `
			+ "following the documented cutover would install a "
			+ "configuration that refuses to start");
	}
}

// REVIEW [P1]: EVERY BACKUP A ROLLBACK RESTORES IS PRODUCED ON THAT SAME PATH.
//
// Section 6's fresh-cutover rollback restored a launcher backup that only the
// section 7 reconciliation created, so a failed mandatory preflight on the
// documented fresh path reached a rollback command that fails before anything
// is restored. Finding an install command SOMEWHERE in the document is not
// enough -- that is the free-text mistake again, one level up.
//
// The document is split at its top-level headings and the fresh path (1-6) is
// held apart from the reconciliation (7). A restore whose SOURCE is a `.pre-`
// backup must have that backup produced in its own group, guarded or not.
function installGroups(text) {
	const fresh = [];
	const reconcile = [];
	let target = fresh;
	for (const line of text.split("\n")) {
		const heading = /^##\s+(\d+)\./.exec(line);
		if (heading) target = Number(heading[1]) >= 7 ? reconcile : fresh;
		target.push(line);
	}
	return { fresh, reconcile };
}

// The path operands of one install command, whether it stands alone or sits
// inside a shell guard. A conditional backup is still a backup, and a fresh
// install legitimately has none to take -- so the guard must not hide it from
// this check, and a trailing `;` is punctuation rather than part of a path.
function installOperands(line) {
	const words = line.trim().split(/\s+/)
		.map((one) => one.replace(/;+$/, ""))
		.filter(Boolean);
	const at = words.indexOf("install");
	if (at < 0) return [];
	// EXACTLY THE SOURCE AND THE DESTINATION. A guarded line carries shell
	// keywords and sometimes a second command after them, so the operands are
	// the first two ABSOLUTE PATHS following `install` rather than everything
	// that is not a flag.
	return words.slice(at + 1)
		.filter((one) => one.startsWith("/"))
		.slice(0, 2);
}

function producedIn(group, backup) {
	// The LAST operand of an install command, guarded or not -- a conditional
	// backup is still a backup, and a fresh install legitimately has none to
	// take.
	return group.some((line) => {
		const operands = installOperands(line);
		return operands.length > 0
			&& operands[operands.length - 1] === backup;
	});
}

for (const [name, group] of Object.entries(installGroups(installDoc))) {
	for (const line of group) {
		const source = installOperands(line)[0];
		if (!source || !source.includes(".pre-")) continue;
		if (!producedIn(group, source)) {
			throw new Error(`the ${name} path restores ${source} and never `
				+ "produces it; a rollback that reaches for a backup only "
				+ "another path creates fails before anything is restored");
		}
	}
}

// REVIEW [P0]: AND THE MANDATORY PREFLIGHT MUST NOT PASS A LAUNCHER THAT
// STARTS NOTHING.
//
// The first descendant-reaping preflight identified its own descendants with
// `pgrep -f` tokens, and those tokens sit inside the shell program passed as
// an ARGUMENT to bubblewrap -- so the owner's own argv satisfied both "the
// descendant started" checks, and their disappearance when it exited was
// counted as reaping. A stand-in whose entire body is a sleep passed the gate.
//
// This runs the staged preflight against exactly that stand-in and requires a
// refusal. It needs no namespace, so it runs everywhere this verifier does.
function preflightAgainst(name, body) {
	const home = mkdtempSync(join(tmpdir(), `w28681-${name}-`));
	try {
		writeFileSync(join(home, "bwrap"), body, { mode: 0o755 });
		return spawnSync("bash",
			[join(stagedPolicy, "preflight-process-domain.sh")], {
				env: { ...process.env,
					PATH: `${home}:${process.env.PATH}` },
				encoding: "utf8", timeout: 240000,
			});
	} finally {
		rmSync(home, { recursive: true, force: true });
	}
}

// A launcher that creates no namespace and starts nothing. THE EXACT REASON is
// required rather than any nonzero status: a probe satisfied by "it failed
// somehow" would be satisfied by a preflight that failed for a missing tool,
// and would stop saying anything the day the script grows a new early exit.
const empty = preflightAgainst("vacuous",
	"#!/bin/sh\nwhile :; do sleep 1; done\n");
if (empty.status !== 4) {
	throw new Error("the process-domain preflight answered "
		+ `${empty.status} against a launcher that starts no descendants; `
		+ "exit 4 is the reason that means \"nothing ever ran inside the "
		+ `domain\". Output: ${(empty.stderr || empty.stdout || "").trim()}`);
}

// AND THE POSITIVE CASE, which is the half a negative probe cannot give.
// Review [P1]: the preflight took its "have they stopped writing" baseline
// BEFORE signalling the owner, so a final heartbeat written during teardown
// read as survival and a launcher that reaped its complete tree was REFUSED.
// A gate with only a negative probe cannot see that; this stand-in runs both
// descendants and reaps the whole recorded tree on SIGTERM, exactly as a PID
// namespace does, and the preflight must accept it.
const reaper = preflightAgainst("reaper", `#!/usr/bin/env bash
set -u
while [[ $# -gt 0 && "$1" != "/bin/sh" ]]; do shift; done
[[ $# -gt 0 ]] || exit 2
"$@" &
domain=$!
descendants() {
	local parent="$1" child
	for child in $(pgrep -P "$parent" 2>/dev/null || true); do
		descendants "$child"
		printf '%s\\n' "$child"
	done
}
reap() {
	local seen
	seen="$(descendants "$domain" | tr '\\n' ' ')"
	[[ -z "$seen" ]] || kill -KILL $seen 2>/dev/null || true
	kill -KILL "$domain" 2>/dev/null || true
	wait "$domain" 2>/dev/null || true
	exit 0
}
trap reap TERM
wait "$domain"
`);
if (reaper.status !== 0) {
	throw new Error("the process-domain preflight REFUSED a launcher that "
		+ "runs both descendants and reaps its complete tree; it is rejecting "
		+ `the behaviour it exists to require. Output: `
		+ `${(reaper.stderr || reaper.stdout || "").trim()}`);
}

// AND THE PREFLIGHT SHIPS WITH IT. Whether this HOST can create the namespace
// and reap a detached descendant is not a repository fact and cannot be
// established from a nested sandbox; what is checkable here is that the
// operator has the exact probe to run in the service launch context before
// installing.
readFileSync(join(stagedPolicy, "preflight-process-domain.sh"), "utf8");

console.log(`dispatcher preflight: ${Object.keys(validatedDispatcher.targets).length} unique targets`);
console.log("execution policy: 6 exact participant profiles + Docker inspection profile");
console.log("ACP preflight: pc.code/impl policy resources readable from staged set");
console.log("ACP locator preflight: exact binary/config/participant/role exported");
console.log(`ACP process domain: launcher unshares PID and dies with parent; `
	+ `turn deadline ${validatedAcp.turnTimeoutMs}ms; run `
	+ `pc-code-policy/preflight-process-domain.sh in the SERVICE context`);
