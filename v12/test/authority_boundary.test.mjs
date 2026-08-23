// W2928: the self-containment boundary, enforced rather than asserted in
// prose.
//
// The assignment is explicit: the v12 authority "may reuse or copy v11
// concepts but must not import, open, mutate, package or depend at
// runtime on `src/baton_work/` or a v11 authority". That is exactly the
// kind of boundary that holds until somebody adds one convenient import,
// so it is a regression rather than a paragraph in a README.

import { test, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { Refusal, V12Authority, V12, normalizeAssignment, snapshot }
	from "../src/authority/index.mjs";
import { CLAUDE, CLOSER, GEMINI, OTHER, UUID, WORK, claimedV12, cleanup,
         deployment, refusalMessage, scratch } from "./authority_fixture.mjs";

after(cleanup);

const SOURCE = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "authority");

function modules() {
	return readdirSync(SOURCE).filter((name) => name.endsWith(".mjs"))
		.map((name) => [name, readFileSync(join(SOURCE, name), "utf8")]);
}

test("W2928: every import is a Node builtin or a sibling in this subtree", () => {
	const files = modules();
	assert.ok(files.length >= 6, "the authority modules were not found");
	for (const [name, text] of files) {
		for (const match of text.matchAll(/^\s*(?:import|export)[^\n]*?from\s+"([^"]+)"/gm)) {
			const specifier = match[1];
			const ok = specifier.startsWith("node:") || /^\.\/[\w.-]+\.mjs$/.test(specifier);
			assert.ok(ok,
				`${name} imports ${specifier}; the v12 authority depends on Node `
				+ `builtins and its own siblings only`);
		}
		// A dynamic import would slip past the static check above, and an
		// npm dependency would make this subtree unbuildable on its own.
		assert.equal(/\bimport\s*\(/.test(text), false,
			`${name} uses a dynamic import, which the static boundary check cannot see`);
		assert.equal(/\brequire\s*\(/.test(text), false, `${name} uses require()`);
	}
});

test("W2928: nothing here names the v11 product tree, store or executable", () => {
	// The negative form matters as much as the positive one: reaching the
	// v11 authority through a path string, a spawned executable or its
	// database file would be exactly the coupling the boundary forbids,
	// and none of those is an `import`.
	const forbidden = [
		[/baton_work/, "the v11 product package"],
		[/work\.sqlite3/, "a v11 authority database"],
		[/child_process/, "a spawned process"],
		[/\bexecFile|\bspawn\b/, "a spawned process"],
		[/\.\.\/\.\.\//, "a path escaping this subtree"],
	];
	for (const [name, text] of modules()) {
		// Comments explain the boundary and legitimately mention what is on
		// the far side of it; the check is about CODE.
		const code = text.replace(/^\s*\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "");
		for (const [pattern, what] of forbidden) {
			assert.equal(pattern.test(code), false,
				`${name} references ${what}`);
		}
	}
});

test("W2928: the authority creates exactly the one file it was given", () => {
	// A disposable authority that quietly wrote beside its own path would
	// be state the operator cannot find or remove.
	const dir = scratch();
	const authority = V12Authority.create(join(dir, "authority.sqlite3"),
		{ authorityUuid: "boundary-uuid" });
	authority.addRouteHandler("impl", CLAUDE);
	authority.createWork({ workId: WORK, route: "impl" });
	authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:1" });
	authority.dispose();
	// WAL and its shared-memory index are SQLite's own sidecars of the
	// nominated file, and both are gone once it is closed cleanly.
	assert.deepEqual(readdirSync(dir).sort(), ["authority.sqlite3"]);
});

test("W2928: the authority exposes no store, database or SQL runner", () => {
	// Review 2026-08-22 [P1]. A `store` getter used to be on this object,
	// and through it a consumer of the advertised boundary set
	// `generation_counter` to 41 and then claimed normally, receiving
	// generation 42 — choosing the supposedly authority-minted generation.
	//
	// The check is on the OBJECT rather than on the source, because that is
	// what a consumer holds. Own properties, prototype methods and getters
	// are all walked: a getter added later would be a new door, and the
	// point of this case is that there is none.
	const { as, authority } = deployment();
	const names = new Set();
	for (let object = authority; object && object !== Object.prototype;
	     object = Object.getPrototypeOf(object)) {
		for (const name of Object.getOwnPropertyNames(object)) names.add(name);
	}
	const forbidden = [/store/i, /^db$/i, /database/i, /sqlite/i, /^run$/,
	                   /^exec$/, /^prepare$/, /^query$/, /^sql$/i, /transact/i];
	for (const name of names) {
		for (const pattern of forbidden) {
			assert.equal(pattern.test(name), false,
				`${name} is reachable on the public authority and matches ${pattern}`);
		}
	}
	// And nothing REACHABLE from it is one either: every readable value is a
	// function or plain data, never an object carrying a SQL surface.
	for (const name of names) {
		if (name === "constructor") continue;
		let value;
		try { value = authority[name]; } catch { continue; }
		if (value === null || typeof value !== "object") continue;
		for (const inner of ["run", "exec", "prepare", "close"]) {
			assert.notEqual(typeof value[inner], "function",
				`authority.${name} exposes a ${inner}() — that is a store handle`);
		}
	}
});

test("W2928: a consumer cannot choose the generation the authority mints", () => {
	// The reviewer's reproduction, as a regression. The only route to a
	// generation is `claim`, and the counter it advances is not reachable.
	const { as, authority } = deployment({ contract: V12 });
	assert.equal(authority.store, undefined);
	assert.equal(authority.db, undefined);
	const first = as(CLAUDE).claim({ workId: WORK, operationId: "claim:1" });
	assert.equal(first.generation, 1, "the authority allocates from its own counter");
	as(first.participant).end({ expect: first, operationId: "end:1", reason: "handed back" });
	assert.equal(as(CLAUDE).claim({ workId: WORK, operationId: "claim:2" }).generation, 2,
		"the successor generation follows the authority's counter, not a caller");
});

test("W2928: the runtime face carries the transitions and no configuration", () => {
	// Re-review 2026-08-22 [P1]. One object carried both the trusted
	// bootstrap and the runtime surface, and W2929 was directed to consume
	// it — so a consumer could grant itself `close`, close a live Work as
	// that actor, and replace the canonical target with zero proposals and
	// zero receipts. The two are now different objects, and this walks both.
	const { authority } = deployment();
	const session = authority.session(CLAUDE);

	// Every transition is reachable on the SESSION.
	for (const name of ["claim", "end", "pass", "cancel", "rejectPlan",
	                    "installGate", "satisfyGate", "advanceContract", "close",
	                    "publish", "verify", "review", "approve", "integrate",
	                    "activity", "settleOperation"]) {
		assert.equal(typeof session[name], "function", `${name} is not on the session`);
	}
	// And NONE of the configuration is. This is the list the reproduction
	// used: `grantCapability` to self-grant, `setPolicy` to move the
	// canonical target.
	for (const name of ["grantCapability", "revokeCapability", "setPolicy",
	                    "certifyContract", "withdrawCertification",
	                    "permitContractTransition", "createWork", "addRouteHandler",
	                    "session", "dispose", "setLookupAvailable",
	                    "store", "db"]) {
		assert.equal(session[name], undefined,
			`${name} is reachable on the runtime face`);
	}
	// The session exposes no route back to the authority or the store.
	const names = new Set();
	for (let object = session; object && object !== Object.prototype;
	     object = Object.getPrototypeOf(object)) {
		for (const name of Object.getOwnPropertyNames(object)) names.add(name);
	}
	for (const name of names) {
		if (name === "constructor") continue;
		let value;
		try { value = session[name]; } catch { continue; }
		if (value === null || typeof value !== "object") continue;
		for (const inner of ["session", "grantCapability", "setPolicy", "run", "exec"]) {
			assert.notEqual(typeof value[inner], "function",
				`session.${name} exposes ${inner}()`);
		}
	}
});

test("W2928: a session holder cannot self-grant, impersonate or move the target",
	() => {
		// The reviewer's two reproductions, as regressions.
		const { authority } = claimedV12();
		const publisher = authority.session(CLAUDE);
		const before = authority.canonicalTarget();

		// 1. Self-grant is unreachable.
		assert.equal(publisher.grantCapability, undefined);
		assert.deepEqual(authority.capabilitiesOf(CLAUDE), []);
		// 2. Closing as itself refuses on the capability.
		assert.match(
			refusalMessage(() => publisher.close({ workId: WORK,
				outcome: "satisfying", rationale: "mine", operationId: "c1",
				expect: authority.assignmentOf(WORK) })),
			/does not hold the close capability/);
		// 3. Impersonating a configured closer refuses on the binding.
		assert.match(
			refusalMessage(() => publisher.close({ workId: WORK,
				outcome: "satisfying", rationale: "mine", actor: CLOSER,
				operationId: "c2", expect: authority.assignmentOf(WORK) })),
			/takes its actor from the session it is called on/);
		// 4. The canonical target cannot be written directly.
		assert.equal(publisher.setPolicy, undefined);
		assert.equal(authority.canonicalTarget(), before);
		assert.equal(authority.projectWork(WORK).status, "open");
		// And a session cannot mint another for a different participant.
		assert.equal(publisher.session, undefined);
		assert.throws(
			() => new (Object.getPrototypeOf(publisher).constructor)(
				Symbol("forged"), null, "poc.evil"),
			/minted by the trusted authority/);
	});

test("W2928: the trusted face configures and vends, and still holds no store", () => {
	const { authority } = deployment();
	for (const name of ["certifyContract", "permitContractTransition", "setPolicy",
	                    "grantCapability", "revokeCapability", "createWork",
	                    "addRouteHandler", "session", "dispose", "projectWork"]) {
		assert.equal(typeof authority[name], "function", `${name} is not on the authority`);
	}
	// The transitions are NOT on it: there is one way to perform one, and it
	// is a session bound to a participant.
	for (const name of ["claim", "publish", "verify", "review", "approve",
	                    "integrate", "close", "cancel", "end"]) {
		assert.equal(authority[name], undefined,
			`${name} is reachable on the trusted face without a participant binding`);
	}
	assert.equal(authority.store, undefined);
	assert.equal(authority.db, undefined);
	assert.equal(typeof V12Authority.claimSignature, "function");
});

test("W2928: an identity that changes its answer cannot cross the boundary", () => {
	// Re-review 2026-08-22 [P1]. The session read
	// `operands.expect.participant` for its binding check and then handed
	// the SAME caller-owned object to the core, which read it again. A
	// getter answering `poc.claude` for the first two reads and
	// `poc.gemini` afterwards passed the check and then ended Gemini's live
	// assignment: the Work became unclaimed and the event named Gemini.
	//
	// Validating one view and executing another is the whole defect. The
	// boundary now takes ONE snapshot into plain frozen data and never
	// reads the caller's object again, so there is no second view to
	// present.
	const { authority } = deployment({
		contract: V12, works: [[WORK, "impl"], [OTHER, "impl"]] });
	const claude = authority.session(CLAUDE);
	const gemini = authority.session(GEMINI);
	claude.claim({ workId: WORK, operationId: "c1" });
	const foreign = gemini.claim({ workId: OTHER, operationId: "c2" });

	const shifting = (first, later) => {
		let reads = 0;
		return {
			authorityUuid: foreign.authorityUuid, workId: foreign.workId,
			generation: foreign.generation,
			get participant() { reads += 1; return reads <= 2 ? first : later; },
		};
	};

	// The reviewer's exact shape, on `end`.
	const trap = shifting(CLAUDE, GEMINI);
	assert.throws(() => claude.end({ expect: trap, operationId: "toctou" }),
		/stale assignment/,
		"a shifting identity crossed the session boundary");
	// Whatever the ONE read returned is the identity for the whole
	// operation, so this refuses on the compare-and-swap rather than the
	// binding — and either way it refuses.
	assert.deepEqual({ ...authority.assignmentOf(OTHER) }, { ...foreign },
		"Gemini's assignment was ended by Claude's session");
	assert.equal(authority.projectWork(OTHER).phase, "active");
	assert.deepEqual(authority.assignmentEvents(OTHER), [],
		"the foreign Work's journal was written");
	assert.equal(authority.operationRecord("toctou"), null);

	// The other direction: if the single read names the foreign
	// participant, the BINDING refuses it first.
	assert.throws(
		() => claude.end({ expect: shifting(GEMINI, CLAUDE), operationId: "toctou2" }),
		/this session acts for poc\.claude/);
	assert.equal(authority.operationRecord("toctou2"), null);

	// A Proxy is the same story: the snapshot reads own enumerable
	// properties once, so a `get` trap gets one chance to answer.
	let trapped = 0;
	const proxied = new Proxy({ ...foreign }, {
		get(target, key) {
			if (key === "participant") {
				trapped += 1;
				return trapped <= 2 ? CLAUDE : GEMINI;
			}
			return target[key];
		},
	});
	assert.throws(() => claude.end({ expect: proxied, operationId: "toctou3" }),
		/stale assignment|this session acts for/);
	assert.deepEqual({ ...authority.assignmentOf(OTHER) }, { ...foreign });
	assert.equal(authority.operationRecord("toctou3"), null);
	// A function-valued operand is refused outright: the snapshot takes
	// plain data, and something that can be CALLED is not an operand this
	// authority accepts.
	assert.throws(
		() => claude.end({ expect: { ...foreign, participant: CLAUDE },
			operationId: "fn", reason: () => "later" }),
		/an operand may not be a function/);
	authority.assertInvariants(OTHER);
});

test("W2928: every assignment-owned transition takes the same snapshot", () => {
	// The review named eight transitions that shared the wrapper. Each is
	// driven with a shifting identity and must leave the foreign Work and
	// its journal untouched.
	const { authority } = deployment({
		contract: V12, works: [[WORK, "impl"], [OTHER, "impl"]] });
	const claude = authority.session(CLAUDE);
	const gemini = authority.session(GEMINI);
	claude.claim({ workId: WORK, operationId: "c1" });
	const foreign = gemini.claim({ workId: OTHER, operationId: "c2" });

	// One operand bag wide enough for every transition; each takes what it
	// needs and the identity is what is under test.
	const operandsFor = (name, expect) => ({
		expect, key: "k", operationId: `t-${name}`, toRoute: "rview",
		reason: "r", comment: "r", planDigest: "p", gate: "runtime-quiescence:1",
		workId: OTHER, expectContract: V12, targetContract: V12, rationale: "r",
		proposalId: "p", resultId: "r", resultDigest: "d", candidateDigest: "c",
		inputDigest: "i", policyDigest: "po",
	});
	for (const name of ["activity", "advanceContract", "cancel", "end",
	                    "installGate", "pass", "publish", "rejectPlan"]) {
		let reads = 0;
		const expect = {
			authorityUuid: foreign.authorityUuid, workId: foreign.workId,
			generation: foreign.generation,
			get participant() { reads += 1; return reads <= 2 ? CLAUDE : GEMINI; },
		};
		assert.throws(() => claude[name](operandsFor(name, expect)),
			(error) => error instanceof Refusal, `${name} accepted a shifting identity`);
		assert.equal(authority.operationRecord(`t-${name}`), null, name);
	}
	// Nothing moved.
	assert.deepEqual({ ...authority.assignmentOf(OTHER) }, { ...foreign });
	assert.equal(authority.projectWork(OTHER).phase, "active");
	assert.deepEqual(authority.assignmentEvents(OTHER), []);
	assert.deepEqual(authority.activities(OTHER), []);
	assert.deepEqual(authority.contractEvents(OTHER), []);
	authority.assertInvariants(OTHER);
});

test("W2928: claim refuses a supplied identity operand rather than ignoring it", () => {
	// Re-review 2026-08-22 [P2]. `claim` destructured only `workId` and
	// `operationId`, so a supplied `participant` was silently dropped and a
	// caller could believe it had been honoured — which contradicts the
	// same correction's rule everywhere else.
	const { authority } = deployment({ contract: V12 });
	const claude = authority.session(CLAUDE);
	for (const name of ["participant", "actor"]) {
		assert.throws(
			() => claude.claim({ workId: WORK, [name]: GEMINI,
				operationId: `claim:${name}` }),
			new RegExp(`supplying ${name} would let a caller choose an identity`),
			name);
		assert.equal(authority.operationRecord(`claim:${name}`), null, name);
	}
	assert.equal(authority.projectWork(WORK).handler, null);
	// And the ordinary form still works.
	assert.equal(claude.claim({ workId: WORK, operationId: "claim:ok" }).participant,
		CLAUDE);
});

test("W2928: the snapshot reads each operand exactly once", () => {
	// The primitive both layers rest on, tested at its own level. The
	// session's wrapper and the core's `normalizeAssignment` are two calls
	// to this; without it neither is more than a hopeful comparison.
	let reads = 0;
	const shifting = {
		authorityUuid: UUID, workId: WORK, generation: 1,
		get participant() { reads += 1; return reads === 1 ? CLAUDE : GEMINI; },
	};
	const taken = snapshot(shifting);
	assert.equal(reads, 1, "the snapshot read a property more than once");
	assert.equal(taken.participant, CLAUDE);
	assert.equal(taken.participant, CLAUDE, "the snapshot is not stable");
	assert.equal(reads, 1, "reading the snapshot reached back to the original");
	assert.ok(Object.isFrozen(taken));
	// Nested values are taken too, so a nested getter cannot shift either.
	let nested = 0;
	const deep = snapshot({ evidence: { get kind() { nested += 1; return "a"; } } });
	assert.equal(nested, 1);
	assert.ok(Object.isFrozen(deep.evidence));
	// And a value that can be CALLED is not an operand.
	assert.throws(() => snapshot({ reason: () => "later" }),
		/an operand may not be a function/);
	assert.throws(() => snapshot({ key: Symbol("s") }), /may not be a symbol/);

	// `normalizeAssignment` is the snapshot plus the four-part validation.
	assert.deepEqual({ ...normalizeAssignment(shifting) },
		{ authorityUuid: UUID, workId: WORK, participant: GEMINI, generation: 1 });
	assert.throws(() => normalizeAssignment({ participant: CLAUDE }),
		/must be the full four-part identity/);
	// Absent stays absent: an unclaimed close is not forced to invent one.
	assert.equal(normalizeAssignment(undefined), undefined);
	assert.equal(normalizeAssignment(null), null);
});
