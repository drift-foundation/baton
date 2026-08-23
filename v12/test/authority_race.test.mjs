// W2928: competing claims across REAL processes.
//
// Every other suite here drives one process, which can show that a
// second claim is refused but cannot show that two claims arriving at
// once are serialized rather than interleaved. The contract's central
// promise — "the claim is atomic and rechecked inside the write
// transaction, so an earlier readiness observation is advisory and a
// competing claim fails closed" — is a promise about concurrency, so
// this suite spends real processes on it.
//
// The racers are separate `node` processes over ONE durable store. They
// synchronize on a shared wall-clock instant so their claims land in the
// same few milliseconds, and each reports only what the authority told
// it. Nothing coordinates them beyond the store itself.

import { test, after } from "node:test";
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { promisify } from "node:util";

import { CLAUDE, GEMINI, WORK, cleanup, deployment, refusalMessage,
         scratch } from "./authority_fixture.mjs";
import { V12Authority, V12 } from "../src/authority/index.mjs";

after(cleanup);

const run = promisify(execFile);

// How long the racers wait before contending. Long enough that four
// processes have finished importing and opening the store, so the barrier
// releases them into the SAME instant rather than staggering them.
const BARRIER_MS = 750;

// The racer takes the module to load as its FIRST operand rather than
// naming it in a static import. Two reasons, and the second is the one
// that matters: this file is written outside the subtree, so a relative
// specifier could not resolve — and `placement.test.mjs` scans every
// `from "..."` in `v12/` for exactly the kind of unresolvable specifier a
// templated one would look like. Passing the location as an operand keeps
// that gate honest instead of teaching it an exception.
const RACER = `
import { writeFileSync } from "node:fs";

const [module, path, workId, participant, operationId, startAt, out] =
	process.argv.slice(2);

// The result goes to a FILE, synchronously, not to stdout.
//
// Review 2026-08-22 [P2]: the racers used to report through stdout, and
// the parent intermittently parsed an empty string. A pipe is an async
// channel whose flush races process exit, and four children under a
// spin-wait barrier are exactly the load that loses it. A synchronous
// write to a file the parent names is either there or it is not, and
// "not there" is then a diagnosable outcome rather than a JSON parse
// error. stdout stays available for diagnostics.
const report = (result) => writeFileSync(out, JSON.stringify(result));

try {
	const { V12Authority } = await import(module);
	const authority = V12Authority.open(path);
	// The racer holds the RUNTIME face, bound to its participant, which is
	// what a Worker Manager holds. It opens the store because it is a test
	// harness standing in for a deployment; a manager is handed its session.
	const session = authority.session(participant);
	// A shared start instant, so the claims contend instead of queueing.
	while (Date.now() < Number(startAt)) { /* spin to the barrier */ }
	try {
		const assignment = session.claim({ workId, operationId });
		report({ ok: true, participant, assignment });
	} catch (error) {
		report({ ok: false, participant, message: error.message,
		         name: error.name });
	}
	authority.dispose();
} catch (error) {
	// Anything that is NOT the authority refusing — a failed import, a
	// store that would not open, a bug in this probe — is reported as
	// what it is instead of vanishing into an empty channel.
	report({ ok: false, participant, harness: true,
	         message: String(error && error.stack || error) });
}
`;

const MODULE = new URL("../src/authority/index.mjs", import.meta.url).href;

function racerScript(dir) {
	const file = join(dir, "racer.mjs");
	writeFileSync(file, RACER);
	return file;
}

// Run one racer and describe its outcome COMPLETELY.
//
// Review 2026-08-22 [P2]: the old harness parsed the child's stdout and
// threw a JSON syntax error when it was empty, discarding the exit
// status, the signal and stderr — so a failure said nothing about
// whether the authority, the child launch or the transport had failed.
// Every one of those is now a named outcome.
async function racer({ script, module, path, workId, participant, operationId,
                       startAt, out }) {
	const context = { participant, operationId };
	let proc;
	try {
		proc = await run(process.execPath,
			[script, module, path, workId, participant, operationId,
			 String(startAt), out]);
		context.status = 0;
	} catch (error) {
		// `execFile` rejects on a non-zero exit, and the error carries the
		// child's streams. A racer that DIED is a different fact from one
		// that was refused, and the harness must not conflate them.
		if (error.code === "ENOENT") {
			return { ...context, outcome: "spawn-failed", detail: String(error) };
		}
		context.status = error.code;
		context.signal = error.signal ?? null;
		context.stdout = String(error.stdout ?? "");
		context.stderr = String(error.stderr ?? "");
	}
	if (proc) {
		context.stdout = proc.stdout;
		context.stderr = proc.stderr;
	}
	if (!existsSync(out)) {
		return { ...context, outcome: "no-report",
			detail: `the racer wrote no result file; exit=${context.status} `
				+ `signal=${context.signal ?? "none"} stderr=${context.stderr.slice(0, 400)}` };
	}
	const text = readFileSync(out, "utf8");
	let report;
	try {
		report = JSON.parse(text);
	} catch (error) {
		return { ...context, outcome: "malformed-report",
			detail: `${error.message}; raw=${JSON.stringify(text.slice(0, 400))}` };
	}
	if (report.harness) {
		return { ...context, outcome: "harness-failure", detail: report.message };
	}
	return { ...context, outcome: report.ok ? "claimed" : "refused",
	         assignment: report.assignment, message: report.message };
}

// Every outcome that is not a claim or a refusal is a harness fault, and
// it is reported with everything known about it rather than as an
// assertion on a parsed value.
function assertDecided(results) {
	const broken = results.filter((result) =>
		result.outcome !== "claimed" && result.outcome !== "refused");
	assert.deepEqual(broken, [],
		"a racer did not reach an authority decision:\n"
		+ broken.map((result) =>
			`  ${result.participant} ${result.outcome}: ${result.detail}`).join("\n"));
}

async function race({ participants, operationId, contract = V12 }) {
	const dir = scratch();
	const built = deployment({
		dir, contract,
		handlers: participants.map((participant) => ["impl", participant]),
	});
	built.authority.dispose();
	const script = racerScript(dir);
	const startAt = Date.now() + BARRIER_MS;
	const results = await Promise.all(participants.map((participant, index) =>
		racer({ script, module: MODULE, path: built.path, workId: WORK,
		        participant, operationId: operationId ?? `claim:racer-${index}`,
		        startAt, out: join(dir, `result-${index}.json`) })));
	assertDecided(results);
	return { results, path: built.path };
}

test("W2928: concurrent processes claiming one Work — exactly one wins", async () => {
	const { results, path } = await race({
		participants: [CLAUDE, GEMINI, "poc.third", "poc.fourth"] });

	const winners = results.filter((result) => result.outcome === "claimed");
	assert.equal(winners.length, 1,
		`expected exactly one winner, got ${JSON.stringify(results, null, 1)}`);
	for (const loser of results.filter((result) => result.outcome === "refused")) {
		assert.match(loser.message, /Work is already claimed/,
			`${loser.participant} failed for a reason other than losing the race`);
	}
	// The decisive assertion: the counter moved EXACTLY once. Three losers
	// that each minted a generation on the way to being refused would show
	// up here and nowhere else.
	const authority = V12Authority.open(path);
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	assert.equal(winners[0].assignment.generation, 1);
	assert.equal(authority.projectWork(WORK).handler, winners[0].participant);
	// And every loser's slot is untaken: a refused claim takes no capacity.
	for (const loser of results.filter((result) => result.outcome === "refused")) {
		assert.equal(authority.slotHolder(loser.participant), null);
	}
	authority.assertInvariants(WORK);
	authority.dispose();
});

test("W2928: concurrent processes replaying ONE fixed claim mint once", async () => {
	// The other half of the race, and the one the restart table depends
	// on: several managers recovering the SAME accepted offer submit the
	// SAME fixed operation. They must all get one assignment back, not one
	// each.
	const { results, path } = await race({
		participants: [CLAUDE, CLAUDE, CLAUDE, CLAUDE],
		operationId: "claim:offer-1" });

	assert.equal(results.filter((result) => result.outcome === "claimed").length,
		results.length,
		`every submitter of a committed fixed claim should get its result: `
		+ JSON.stringify(results, null, 1));
	const generations = new Set(results.map((result) => result.assignment.generation));
	assert.deepEqual([...generations], [1], "the fixed claim minted more than once");
	const authority = V12Authority.open(path);
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	authority.assertInvariants(WORK);
	authority.dispose();
});

test("W2928: cancellation refuses an assignment that has no generation", () => {
	// Under `v11` there is nothing to fence, so "fence the exact
	// generation AND end the assignment in one transaction" would fence
	// nothing and install a gate naming no generation. Half a guarantee
	// spelled like a whole one is worse than a refusal.
	const { as, authority } = deployment();
	const v11 = as(CLAUDE).claim({ workId: WORK, operationId: "claim:v11" });
	assert.equal(v11.generation, null);
	assert.match(
		refusalMessage(() => as(CLAUDE).cancel({
			expect: v11, operationId: "cancel:v11", reason: "runtime lost" })),
		/only a v12 assignment contract can be cancelled/);
	// Nothing moved: the refusal wrote neither a fence nor an ending.
	const work = authority.projectWork(WORK);
	assert.equal(work.handler, CLAUDE);
	assert.equal(work.phase, "active");
	assert.equal(work.gate, null);
	assert.deepEqual(work.fencedGenerations, []);
	assert.deepEqual(authority.assignmentEvents(WORK), []);
	authority.assertInvariants(WORK);
});
