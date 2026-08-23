// The INSTALLED execution-policy generator
// (`work/records/2026/08/finding-deployed-exec-policy-helper/`).
//
// Release d46ab1e shipped a dispatcher template that told the operator
// to generate the exact W415 rules with a path existing only in the
// source checkout, and shipped no equivalent command. These cases pin
// the direct invocation that closes that gap: strict operands, stdout
// only, and no side effect on import — the dispatcher imports this same
// module during startup preflight.
//
// The DEPLOYED artifact is covered separately, by the actual v11
// deployer lane in `tests/work/test_deploy_v11.py`. Passing here says
// the source module behaves; passing there says the release carries it.

import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { rulesFor, identityFromOperands, generate, inspectionRules,
         requestFromOperands, USAGE, INSPECTION_PROFILE, POLICY_PROFILE,
         RULED_VERBS, ExecPolicyError } from "../src/exec_policy.mjs";

const MODULE = join(dirname(fileURLToPath(import.meta.url)),
                    "..", "src", "exec_policy.mjs");
const IDENTITY = { binary: "/opt/baton/bin/baton",
	config: "/srv/baton/baton.json", participant: "baton.codex" };
const OPERANDS = [`binary=${IDENTITY.binary}`, `config=${IDENTITY.config}`,
                  `participant=${IDENTITY.participant}`];

function run(argv, options = {}) {
	return spawnSync(process.execPath, [MODULE, ...argv],
		{ encoding: "utf8", ...options });
}

test("W415 packaging: direct invocation prints exactly the approved rules",
	() => {
		const proc = run(OPERANDS);
		assert.equal(proc.status, 0, proc.stderr);
		// Byte-for-byte the reviewed generator's own output. The CLI is a
		// front door onto `rulesFor`, never a second implementation of it.
		assert.equal(proc.stdout, `${rulesFor(IDENTITY).join("\n")}\n`);
		assert.equal(proc.stderr, "");
		// One rule per verb in the ruled profile, and nothing else on
		// stdout. W220 widened that profile from four verbs to the
		// managed Work workflow; the count still comes from the profile
		// rather than from a number written here twice.
		assert.equal(proc.stdout.trimEnd().split("\n").length, RULED_VERBS.length);
		assert.ok(RULED_VERBS.length > 1);
		// Operand ORDER is not part of the identity; the rule order is
		// the approved verb order either way.
		const shuffled = run([OPERANDS[2], OPERANDS[0], OPERANDS[1]]);
		assert.equal(shuffled.stdout, proc.stdout);
	});

test("W415 packaging: the generator prints and installs nothing", () => {
	// The deployment-owned boundary this whole mechanism rests on: a
	// process that could grant itself authority has no boundary, so
	// installing the output stays the operator's deliberate act.
	const dir = mkdtempSync("/tmp/exec-policy-cli-inert-");
	const proc = run(OPERANDS, { cwd: dir });
	assert.equal(proc.status, 0, proc.stderr);
	assert.deepEqual(readdirSync(dir), [],
		"the generator created a file; it must only print");
	// It does not overwrite an existing policy file either. The BYTES
	// are what this asserts: an implementation that rewrote the file in
	// place would leave the name exactly where it was.
	const existing = join(dir, "baton.rules");
	writeFileSync(existing, "untouched\n");
	assert.equal(run(OPERANDS, { cwd: dir }).status, 0);
	assert.deepEqual(readdirSync(dir), ["baton.rules"]);
	assert.equal(readFileSync(existing, "utf8"), "untouched\n",
		"the generator rewrote an existing policy file in place");
});

test("W415 packaging: importing the module emits nothing", () => {
	// The dispatcher imports this module for its startup preflight. A
	// module that wrote policy text on import would corrupt every
	// consumer of that stream, and the existing bridge fixtures would
	// have to tolerate it.
	const proc = spawnSync(process.execPath,
		["--input-type=module", "-e",
		 `await import(${JSON.stringify(MODULE)});`],
		{ encoding: "utf8" });
	assert.equal(proc.status, 0, proc.stderr);
	assert.equal(proc.stdout, "");
	assert.equal(proc.stderr, "");
});

test("W415 packaging: every malformed operand set is refused", () => {
	// A generator that guessed would emit rules authorizing a command
	// nobody asked for, so nothing is defaulted or ignored.
	const refusals = [
		[[], /missing operand\(s\): binary, config, participant/],
		[[OPERANDS[0]], /missing operand\(s\): config, participant/],
		[[...OPERANDS, "verbs=claim"], /unknown operand "verbs=claim"/],
		[[...OPERANDS, "--help"], /unknown operand "--help"/],
		[[...OPERANDS, OPERANDS[0]], /operand binary was given more than once/],
		[["binary", ...OPERANDS.slice(1)], /operand binary needs a value/],
		[[`binary=baton`, OPERANDS[1], OPERANDS[2]],
		 /ABSOLUTE installed executable/],
		[[OPERANDS[0], "config=baton.json", OPERANDS[2]],
		 /ABSOLUTE installed executable/],
		[[OPERANDS[0], OPERANDS[1], "participant="],
		 /non-empty participant/],
		[["binary=", OPERANDS[1], OPERANDS[2]], /non-empty binary/],
	];
	for (const [argv, expected] of refusals) {
		const proc = run(argv);
		assert.equal(proc.status, 1, `${argv.join(" ")} was not refused`);
		assert.match(proc.stderr, expected);
		// The refusal names the invocation, and emits NO partial policy:
		// a truncated rules file is a broken boundary, not a warning.
		assert.ok(proc.stderr.includes(USAGE.split("\n")[0]),
			"the refusal does not show the usage");
		assert.equal(proc.stdout, "",
			"a refused invocation still wrote policy text to stdout");
	}
});

test("W415 packaging: the operand parser is the CLI's only interface",
	async () => {
		assert.deepEqual(identityFromOperands(OPERANDS), IDENTITY);
		assert.throws(() => identityFromOperands(["nonsense"]), ExecPolicyError);
		assert.equal(generate(OPERANDS), `${rulesFor(IDENTITY).join("\n")}\n`);
		// The generated text is what `assertPolicyProvisioned` accepts.
		// Here that is the same module doing both, which is the point of
		// putting the CLI in the reviewed module; the release's copy is
		// held to it by the deployer's byte-parity regression.
		const dir = mkdtempSync("/tmp/exec-policy-cli-roundtrip-");
		const file = join(dir, "baton.rules");
		writeFileSync(file, execFileSync(process.execPath, [MODULE, ...OPERANDS],
			{ encoding: "utf8" }));
		const { assertPolicyProvisioned } = await import("../src/exec_policy.mjs");
		assert.equal(assertPolicyProvisioned(file, IDENTITY).satisfied, true);
	});

// -- W2845: the second profile ---------------------------------------------
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/
// finding-managed-docker-inspection-policy/`. The four read-only Docker
// inspection prefixes go into the SAME nominated policy file, so the
// generator has to be able to print them — the operator installed them
// by hand on 2026-08-22 because it could not.

const INSPECTION = ["profile=managed-docker-inspection"];

test("W2845: the inspection profile prints exactly the four ruled prefixes",
	() => {
		const proc = run(INSPECTION);
		assert.equal(proc.status, 0, proc.stderr);
		assert.equal(proc.stderr, "");
		// The approved set, in the ruled order, written out here rather
		// than read from the module the case is testing.
		assert.equal(proc.stdout,
			'prefix_rule(pattern=["docker", "version"], decision="allow")\n'
			+ 'prefix_rule(pattern=["docker", "info"], decision="allow")\n'
			+ 'prefix_rule(pattern=["docker", "inspect"], decision="allow")\n'
			+ 'prefix_rule(pattern=["docker", "image", "inspect"], decision="allow")\n');
		// Byte-for-byte the reviewed generator's own output: the CLI is a
		// front door onto `inspectionRules`, never a second copy of it.
		assert.equal(proc.stdout, `${inspectionRules().join("\n")}\n`);
		// It names no participant and no config, so it is run ONCE for
		// the deployment rather than once per identity.
		assert.ok(!proc.stdout.includes("--participant"));
		// And it installs nothing, like the workflow profile.
		const dir = mkdtempSync("/tmp/exec-policy-cli-inspection-");
		assert.equal(run(INSPECTION, { cwd: dir }).status, 0);
		assert.deepEqual(readdirSync(dir), []);
	});

test("W2845: the workflow profile is the default and may be named", () => {
	// Every invocation the release already documents keeps working, and
	// naming the profile explicitly prints the same bytes.
	const implicit = run(OPERANDS);
	const explicit = run([`profile=${POLICY_PROFILE}`, ...OPERANDS]);
	assert.equal(explicit.status, 0, explicit.stderr);
	assert.equal(explicit.stdout, implicit.stdout);
	assert.equal(explicit.stdout, `${rulesFor(IDENTITY).join("\n")}\n`);
	// The two profiles are different sets, and neither leaks into the
	// other: the Docker rules carry no Baton identity, and the Baton
	// rules authorize no Docker command.
	assert.ok(!implicit.stdout.includes("docker"));
	assert.ok(!run(INSPECTION).stdout.includes(IDENTITY.binary));
});

test("W2845: an ambiguous or misapplied profile operand is refused", () => {
	// A generator that guessed here would print one profile's rules to
	// an operator who asked for the other's, and the output is a
	// security boundary somebody then installs.
	const refusals = [
		[["profile=nonsense"], /unknown profile "nonsense"/],
		[["profile="], /unknown profile ""/],
		[["profile"], /operand profile needs a value/],
		[[...INSPECTION, ...OPERANDS],
		 /takes no other operand; drop binary=/],
		[[...INSPECTION, "participant=baton.codex"],
		 /takes no other operand; drop participant=baton\.codex/],
		[[...INSPECTION, `profile=${POLICY_PROFILE}`],
		 /operand profile was given more than once/],
		// The workflow profile still needs its identity, named or not.
		[[`profile=${POLICY_PROFILE}`],
		 /missing operand\(s\): binary, config, participant/],
		[[`profile=${POLICY_PROFILE}`, "binary=baton", OPERANDS[1], OPERANDS[2]],
		 /ABSOLUTE installed executable/],
	];
	for (const [argv, expected] of refusals) {
		const proc = run(argv);
		assert.equal(proc.status, 1, `${argv.join(" ")} was not refused`);
		assert.match(proc.stderr, expected);
		assert.equal(proc.stdout, "",
			`${argv.join(" ")} still wrote policy text to stdout`);
	}
	// The usage names BOTH forms, so an operator who guessed wrong is
	// told what the other one is.
	assert.ok(USAGE.includes(`profile=${INSPECTION_PROFILE}`));
	assert.match(run(["profile=nonsense"]).stderr,
		new RegExp(`profile=${INSPECTION_PROFILE}`));
});

test("W2845: the operand parser is the CLI's only interface here too", () => {
	assert.deepEqual(requestFromOperands(INSPECTION),
		{ profile: INSPECTION_PROFILE, identity: null });
	assert.deepEqual(requestFromOperands(OPERANDS),
		{ profile: POLICY_PROFILE, identity: IDENTITY });
	assert.throws(() => requestFromOperands(["profile=nonsense"]), ExecPolicyError);
	assert.equal(generate(INSPECTION), `${inspectionRules().join("\n")}\n`);
});
