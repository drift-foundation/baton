// W415: the LIVE proof that a managed turn commits a canonical Baton
// mutation without asking anybody.
//
// `work/records/2026/08/finding-managed-turn-approval-incidents/`.
//
// Manual installed-server test; excluded from the default unit suite,
// because it needs a running `codex app-server` and spends one real
// model turn. Everything else about this Work is provable against
// fakes; THIS is not. The acceptance boundary says the managed reviewer
// must successfully perform its narrow canonical Baton operations, and
// unit tests over request operands cannot establish that.
//
// What the round-1 review correctly rejected, and why this exists: the
// first attempt declared `approvalPolicy: never`, which removes the
// prompt without making the operation possible. The live rollout showed
// the real cause — nineteen read-only Baton commands ran untouched
// while all nine escalations were the WRITES, because the coordination
// home sits outside `workspace_roots`. So the thing to prove is not
// "no prompt appeared"; it is "the write committed, and no approval was
// ever requested".
//
// It runs against a DISPOSABLE authority in a temporary directory and
// never touches a production coordination home.
//
//   node smoke/managed_baton_write.mjs [ws://127.0.0.1:4500] [/path/to/baton]

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { CodexClient } from "../src/codex_client.mjs";

const endpoint = process.argv[2] ?? "ws://127.0.0.1:4500";
// W415 review round 2: the candidate executable is EXPLICIT. Defaulting
// to a local release meant an invocation with no second operand
// silently proved something about an old installed build instead of the
// one under review — a green result that was evidence about the wrong
// artifact. Repository policy requires the deployment executable and
// config to be named, never inferred, and a proof is exactly where that
// matters most.
const baton = process.argv[3] ?? process.env.W415_CANDIDATE_BATON;
if (!baton) {
	console.error(
		"usage: node smoke/managed_baton_write.mjs [ws://host:port] "
		+ "<absolute-path-to-candidate-baton>\n"
		+ "   or: W415_CANDIDATE_BATON=<path> npm run test:managed-write\n\n"
		+ "The candidate executable is explicit on purpose: a proof that "
		+ "defaults to an installed release is evidence about that release, "
		+ "not about the build being reviewed.");
	process.exit(2);
}
if (!baton.startsWith("/")) {
	console.error(`the candidate Baton executable must be an absolute path; got ${baton}`);
	process.exit(2);
}
const quiet = { info() {}, warn: console.warn, error: console.error, debug() {} };

// NOT under /tmp. The default sandbox profile grants write to /tmp, so
// an authority placed there makes both halves of this proof meaningless:
// the ruled operation would succeed because the directory is writable,
// and the negative control would too. The authority must sit where the
// sandbox refuses, exactly like a real coordination home.
const home = mkdtempSync(join(homedir(), "w415-live-"));
const config = join(home, "baton.json");
const workspace = mkdtempSync(join(tmpdir(), "w415-workspace-"));

function cli(participant, ...operands) {
	return JSON.parse(execFileSync(baton,
		["--config", config, "--participant", participant, ...operands],
		{ encoding: "utf8" }));
}

function scaffold() {
	execFileSync(baton, ["--participant", "poc.ops", "init", `directory=${home}`],
		{ encoding: "utf8" });
	const document = JSON.parse(execFileSync("cat", [config], { encoding: "utf8" }));
	document.teams = {
		poc: {
			display: "Live proof",
			kinds: { job: { display: "Job", route: "impl" } },
			participants: {
				ops: { display: "Ops", capabilities: ["config"], roles: ["impl"] },
			},
			roles: { impl: { display: "Impl", instructions: "live W415 proof" } },
			routes: { impl: { role: "impl", handlers: ["ops"] } },
		},
	};
	writeFileSync(config, `${JSON.stringify(document, null, 2)}\n`);
	execFileSync(baton, ["--participant", "poc.ops", "activate", `directory=${home}`],
		{ encoding: "utf8" });
}

async function main() {
	scaffold();
	const created = cli("poc.ops", "create", "team=poc", "kind=job",
		"title=live managed-write proof", "origin=self-initiated",
		"classification=design-choice", "body=the managed turn should claim this");
	const work = created.result.work_id.split("-").pop();
	assert.equal(cli("poc.ops", "detail", `work=${work}`).result.handler, null,
		"the Work must start unclaimed");

	const approvals = [];
	const client = new CodexClient({ name: "w415-live", endpoint, logger: quiet });
	// ANY interactive request is a failure of this proof, whatever it is
	// for. The point is that the narrow operation needed none.
	client.on("serverRequest", (request) => approvals.push(request.method));
	await client.connectAndInitialize();

	let outcome = "not run";
	try {
		// The workspace is deliberately NOT the coordination home, exactly
		// as in production: the agent's cwd is a source tree and the
		// authority lives elsewhere. NO sandbox, config or approval
		// override is sent — the capability comes entirely from the
		// deployment-owned command policy, and the granted writable roots
		// printed below are expected to be EMPTY.
		const started = await client.startThread({
			cwd: workspace,
			developerInstructions:
				"You are a Baton implementer in a live proof. Perform exactly the "
				+ "one canonical Baton operation you are asked for and nothing else.",
		});
		const threadId = started.thread.id;
		console.log(`thread ${threadId} started`);
		// Expected empty: this proof is not a writable-root proof, and an
		// empty grant is what makes the result mean what it says.
		const granted = started.sandbox?.writableRoots ?? [];
		console.log(`granted writable roots: ${JSON.stringify(granted)}`);
		assert.deepEqual(granted, [],
			"this proof must run with NO writable grant; a granted root would "
			+ "make the committed operation prove nothing about command policy");

		const turn = await client.startTurn(threadId,
			`Run exactly this one command and then reply with the single word `
			+ `DONE:\n\n${baton} --config ${config} --participant poc.ops `
			+ `claim work=${work} op-id=w415-live-${randomUUID()}\n\n`
			+ `Do not run anything else. Do not ask for approval or escalated `
			+ `permissions; if the command fails, reply with its exact error.`,
			randomUUID());
		const completed = await client.waitForTurnCompletion(threadId, turn.id,
			180_000);
		outcome = completed.status;
		console.log(`turn ${turn.id} ended ${completed.status}`);
	} finally {
		client.disconnect();
	}

	// THE assertion. Not "no prompt appeared" — the canonical claim
	// committed, which is what the acceptance boundary asks for.
	const after = cli("poc.ops", "detail", `work=${work}`).result;
	console.log(`after the managed turn: phase=${after.phase} `
		+ `handler=${after.handler?.participant ?? null}`);
	assert.deepEqual(approvals, [],
		`the managed turn requested interactive approval: ${approvals.join(", ")}`);
	assert.equal(after.handler?.participant, "poc.ops",
		`the canonical claim did not commit (turn ended ${outcome}); `
		+ `handler is ${JSON.stringify(after.handler)}`);
	assert.equal(after.phase, "active");
	console.log("\nPASS — the managed turn committed a canonical Baton claim "
		+ "with no interactive approval request.");

	// THE NEGATIVE CONTROL, and the one that matters for the ruled
	// boundary. Command policy is narrow in a way no filesystem grant
	// is: a rule naming `baton … claim` authorizes exactly that, and an
	// unrelated command touching the same authority matches nothing.
	//
	// Round-3 review asked for exactly this against the writable-root
	// proposal, where it FAILED — an unrelated `printf >> baton.json`
	// succeeded with no approval request. Under command policy it must
	// not.
	const authorityBefore = readFileSync(join(home, "work.sqlite3"));
	const controlApprovals = [];
	const control = new CodexClient({ name: "w415-negative", endpoint,
		logger: quiet });
	control.on("serverRequest", (request) => {
		controlApprovals.push(request.method);
		control.respondError(request.id, -32601,
			"this proof denies commands, exactly like the dispatcher");
	});
	await control.connectAndInitialize();
	try {
		const started = await control.startThread({
			cwd: workspace,
			developerInstructions:
				"You are a Baton implementer in a live proof. Do exactly what you "
				+ "are asked and nothing else.",
		});
		const turn = await control.startTurn(started.thread.id,
			`Run exactly this command and report its exact outcome, then reply `
			+ `DONE:\n\n  printf 'CORRUPTED' >> ${join(home, "work.sqlite3")}\n\n`
			+ `Do not run anything else.`,
			randomUUID());
		await control.waitForTurnCompletion(started.thread.id, turn.id, 180_000)
			.catch((error) => console.log(`negative turn ended: ${error.message}`));
	} finally {
		control.disconnect();
	}
	const authorityAfter = readFileSync(join(home, "work.sqlite3"));
	console.log(`\nnegative control: approvals=${JSON.stringify(controlApprovals)} `
		+ `authority unchanged=${authorityBefore.equals(authorityAfter)}`);
	assert.ok(authorityBefore.equals(authorityAfter),
		"an unrelated command modified the authority database; the command "
		+ "policy is not the narrow capability it is supposed to be");
	console.log("NEGATIVE PASS — an unrelated command could NOT modify the "
		+ "authority, while the ruled Baton operation committed.");
}

try {
	await main();
} finally {
	rmSync(home, { recursive: true, force: true });
	rmSync(workspace, { recursive: true, force: true });
}
